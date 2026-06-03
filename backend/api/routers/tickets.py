import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account, require_admin
from api.models import (
    Account,
    AccountRole,
    Ticket,
    TicketComment,
    TicketStatus,
    TicketPriority,
    ActorType,
)
from api.schemas import (
    TicketCreate,
    TicketOut,
    TicketUpdate,
    TicketCommentCreate,
    TicketCommentOut,
    MessageOut,
    PaginatedResponse,
)
from api.services.audit import audit_from_request
from api.services.ticket_notify import notify_ticket_change

router = APIRouter()


@router.post("", response_model=TicketOut)
async def create_ticket(
    request: Request,
    data: TicketCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    ticket = Ticket(
        id=uuid.uuid4(),
        account_id=account.id,
        title=data.title,
        status=TicketStatus.open,
        priority=TicketPriority.normal,
        category=data.category,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)

    comment = TicketComment(
        id=uuid.uuid4(),
        ticket_id=ticket.id,
        author_id=account.id,
        author_email=account.email,
        is_internal=False,
        body=data.body,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(ticket)

    await notify_ticket_change(ticket, comment, db)
    await audit_from_request(
        request, "create_ticket", "ticket", str(ticket.id), account.id, account.id
    )
    return ticket


@router.get("", response_model=PaginatedResponse[TicketOut])
async def list_tickets(
    page: int = 1,
    per_page: int = 20,
    status: TicketStatus | None = None,
    priority: TicketPriority | None = None,
    assigned_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    is_staff = account.role in (AccountRole.admin, AccountRole.superadmin)
    if is_staff:
        query = select(Ticket)
        count_query = select(func.count()).select_from(Ticket)
        if status:
            query = query.where(Ticket.status == status)
            count_query = count_query.where(Ticket.status == status)
        if priority:
            query = query.where(Ticket.priority == priority)
            count_query = count_query.where(Ticket.priority == priority)
        if assigned_to:
            query = query.where(Ticket.assigned_to == assigned_to)
            count_query = count_query.where(Ticket.assigned_to == assigned_to)
    else:
        query = select(Ticket).where(Ticket.account_id == account.id)
        count_query = select(func.count()).select_from(Ticket).where(Ticket.account_id == account.id)
        if status:
            query = query.where(Ticket.status == status)
            count_query = count_query.where(Ticket.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    result = await db.execute(
        query.offset((page - 1) * per_page).limit(per_page).order_by(Ticket.updated_at.desc())
    )
    items = result.scalars().all()
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": items,
    }


@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    is_staff = account.role in (AccountRole.admin, AccountRole.superadmin)
    if not is_staff and ticket.account_id != account.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Filter comments
    if not is_staff:
        ticket.comments = [c for c in ticket.comments if not c.is_internal]

    return ticket


@router.post("/{ticket_id}/comments", response_model=TicketCommentOut)
async def add_comment(
    request: Request,
    ticket_id: uuid.UUID,
    data: TicketCommentCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    is_staff = account.role in (AccountRole.admin, AccountRole.superadmin)
    if not is_staff and ticket.account_id != account.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if not is_staff and data.is_internal:
        raise HTTPException(status_code=403, detail="Cannot create internal notes")

    comment = TicketComment(
        id=uuid.uuid4(),
        ticket_id=ticket.id,
        author_id=account.id,
        author_email=account.email,
        is_internal=data.is_internal if is_staff else False,
        body=data.body,
    )
    db.add(comment)

    # Update ticket status
    if is_staff:
        ticket.status = TicketStatus.waiting_customer
    else:
        ticket.status = TicketStatus.waiting_staff
    ticket.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(comment)
    await notify_ticket_change(ticket, comment, db)
    await audit_from_request(
        request, "add_comment", "ticket_comment", str(comment.id), ticket.account_id, account.id
    )
    return comment


@router.patch("/{ticket_id}", response_model=TicketOut)
async def update_ticket(
    request: Request,
    ticket_id: uuid.UUID,
    data: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    is_staff = account.role in (AccountRole.admin, AccountRole.superadmin)
    if not is_staff and ticket.account_id != account.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if data.status is not None:
        if not is_staff:
            # Customers can only close or resolve
            if data.status not in (TicketStatus.closed, TicketStatus.resolved):
                raise HTTPException(status_code=403, detail="Can only close or resolve")
        ticket.status = data.status
    if data.priority is not None:
        if not is_staff:
            raise HTTPException(status_code=403, detail="Cannot change priority")
        ticket.priority = data.priority
    if data.assigned_to is not None:
        if not is_staff:
            raise HTTPException(status_code=403, detail="Cannot assign")
        ticket.assigned_to = data.assigned_to

    ticket.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(ticket)
    await audit_from_request(
        request, "update_ticket", "ticket", str(ticket.id), ticket.account_id, account.id,
        metadata={"status": data.status.value if data.status else None}
    )
    return ticket


@router.delete("/{ticket_id}", response_model=MessageOut)
async def delete_ticket(
    request: Request,
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(require_admin),
):
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    await db.delete(ticket)
    await db.commit()
    await audit_from_request(
        request, "delete_ticket", "ticket", str(ticket_id), ticket.account_id, account.id,
        actor_type=ActorType.admin,
    )
    return {"message": "Ticket deleted"}
