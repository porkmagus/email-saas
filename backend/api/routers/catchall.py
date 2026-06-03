import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, Domain, Mailbox
from api.schemas import CatchAllCreate, DomainOut, MessageOut
from api.services.audit import audit_from_request

router = APIRouter()


@router.post("/domains/{domain_id}/catch-all", response_model=DomainOut)
async def set_catch_all(
    request: Request,
    domain_id: uuid.UUID,
    data: CatchAllCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(select(Domain).where(Domain.id == domain_id, Domain.account_id == account.id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    # Verify target mailbox ownership
    mailbox_result = await db.execute(select(Mailbox).where(Mailbox.id == data.target_mailbox_id, Mailbox.account_id == account.id))
    if not mailbox_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Target mailbox not found")

    domain.catch_all_target_mailbox_id = data.target_mailbox_id
    await db.commit()
    await db.refresh(domain)

    await audit_from_request(
        request, "set_catch_all", "domain", str(domain_id), account.id, account.id,
        metadata={"target_mailbox_id": str(data.target_mailbox_id)}
    )

    return domain


@router.delete("/domains/{domain_id}/catch-all", response_model=DomainOut)
async def clear_catch_all(
    request: Request,
    domain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(select(Domain).where(Domain.id == domain_id, Domain.account_id == account.id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    domain.catch_all_target_mailbox_id = None
    await db.commit()
    await db.refresh(domain)

    await audit_from_request(
        request, "clear_catch_all", "domain", str(domain_id), account.id, account.id
    )

    return domain
