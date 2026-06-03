"""Outbox router.

Manages scheduled and undo-send messages using the OutboxMessage table.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, OutboxMessage, OutboxMessageStatus
from api.schemas import MessageOut, OutboxMessageCreate, OutboxMessageOut, OutboxMessageUpdate
from api.services.audit import audit_from_request

router = APIRouter()


@router.post("", response_model=OutboxMessageOut, status_code=status.HTTP_201_CREATED)
async def create_outbox_message(
    request: Request,
    data: OutboxMessageCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    msg = OutboxMessage(
        account_id=account.id,
        from_address=data.from_address,
        to_addresses=data.to_addresses,
        subject=data.subject,
        text_body=data.text_body,
        html_body=data.html_body,
        scheduled_at=data.scheduled_at,
        status=OutboxMessageStatus.pending,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    await audit_from_request(
        request, "create_outbox", "outbox", str(msg.id), account.id, account.id,
        metadata={
            "subject": data.subject,
            "to": data.to_addresses,
            "scheduled": data.scheduled_at.isoformat() if data.scheduled_at else None,
        }
    )

    return msg


@router.get("", response_model=list[OutboxMessageOut])
async def list_outbox_messages(
    status_filter: OutboxMessageStatus | None = None,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    stmt = select(OutboxMessage).where(OutboxMessage.account_id == account.id)
    if status_filter:
        stmt = stmt.where(OutboxMessage.status == status_filter)
    stmt = stmt.order_by(OutboxMessage.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{msg_id}", response_model=OutboxMessageOut)
async def get_outbox_message(
    msg_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(OutboxMessage).where(
            OutboxMessage.id == msg_id,
            OutboxMessage.account_id == account.id,
        )
    )
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Outbox message not found")
    return msg


@router.patch("/{msg_id}", response_model=OutboxMessageOut)
async def update_outbox_message(
    request: Request,
    msg_id: uuid.UUID,
    data: OutboxMessageUpdate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(OutboxMessage).where(
            OutboxMessage.id == msg_id,
            OutboxMessage.account_id == account.id,
        )
    )
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Outbox message not found")

    if msg.status != OutboxMessageStatus.pending:
        raise HTTPException(status_code=400, detail="Cannot modify a non-pending message")

    if data.subject is not None:
        msg.subject = data.subject
    if data.text_body is not None:
        msg.text_body = data.text_body
    if data.html_body is not None:
        msg.html_body = data.html_body
    if data.scheduled_at is not None:
        msg.scheduled_at = data.scheduled_at
    if data.to_addresses is not None:
        msg.to_addresses = data.to_addresses

    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    await audit_from_request(
        request, "update_outbox", "outbox", str(msg_id), account.id, account.id,
        metadata={"changes": list(data.model_dump(exclude_unset=True).keys())}
    )

    return msg


@router.delete("/{msg_id}", response_model=MessageOut)
async def cancel_outbox_message(
    request: Request,
    msg_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    """Cancel a pending outbox message (undo send)."""
    result = await db.execute(
        select(OutboxMessage).where(
            OutboxMessage.id == msg_id,
            OutboxMessage.account_id == account.id,
        )
    )
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Outbox message not found")

    if msg.status != OutboxMessageStatus.pending:
        raise HTTPException(status_code=400, detail="Cannot cancel a non-pending message")

    msg.status = OutboxMessageStatus.cancelled
    db.add(msg)
    await db.commit()

    await audit_from_request(
        request, "cancel_outbox", "outbox", str(msg_id), account.id, account.id,
        metadata={"subject": msg.subject}
    )

    return MessageOut(message="Message cancelled")


@router.post("/{msg_id}/send-now", response_model=MessageOut)
async def send_now_outbox_message(
    request: Request,
    msg_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    """Force an immediate send of a pending scheduled message."""
    result = await db.execute(
        select(OutboxMessage).where(
            OutboxMessage.id == msg_id,
            OutboxMessage.account_id == account.id,
        )
    )
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Outbox message not found")

    if msg.status != OutboxMessageStatus.pending:
        raise HTTPException(status_code=400, detail="Cannot send a non-pending message")

    msg.status = OutboxMessageStatus.sent
    msg.scheduled_at = None
    db.add(msg)
    await db.commit()

    await audit_from_request(
        request, "send_now_outbox", "outbox", str(msg_id), account.id, account.id,
        metadata={"subject": msg.subject}
    )

    return MessageOut(message="Message sent immediately")
