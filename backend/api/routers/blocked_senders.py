import uuid
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, BlockedSender
from api.schemas import BlockedSenderCreate, BlockedSenderOut, MessageOut
from api.services.audit import audit_from_request

router = APIRouter()


def _is_domain(email_or_domain: str) -> bool:
    return "@" not in email_or_domain or email_or_domain.startswith("@")


@router.post("", response_model=BlockedSenderOut)
async def create_blocked_sender(
    request: Request,
    data: BlockedSenderCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    email_or_domain = data.email_or_domain.strip().lower()
    if not email_or_domain:
        raise HTTPException(status_code=400, detail="Invalid email or domain")

    existing = await db.execute(
        select(BlockedSender).where(
            BlockedSender.account_id == account.id,
            BlockedSender.email_or_domain == email_or_domain,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already blocked")

    blocked = BlockedSender(
        account_id=account.id,
        email_or_domain=email_or_domain,
        is_domain="@" in email_or_domain and email_or_domain.startswith("@"),
    )
    db.add(blocked)
    await db.commit()
    await db.refresh(blocked)

    await audit_from_request(
        request, "create_blocked_sender", "blocked_sender", str(blocked.id), account.id, account.id,
        metadata={"email_or_domain": email_or_domain}
    )

    return blocked


@router.get("", response_model=list[BlockedSenderOut])
async def list_blocked_senders(
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(BlockedSender).where(BlockedSender.account_id == account.id)
    )
    return result.scalars().all()


@router.delete("/{blocked_id}", response_model=MessageOut)
async def delete_blocked_sender(
    request: Request,
    blocked_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(BlockedSender).where(
            BlockedSender.id == blocked_id,
            BlockedSender.account_id == account.id,
        )
    )
    blocked = result.scalar_one_or_none()
    if not blocked:
        raise HTTPException(status_code=404, detail="Blocked sender not found")

    await db.delete(blocked)
    await db.commit()

    await audit_from_request(
        request, "delete_blocked_sender", "blocked_sender", str(blocked_id), account.id, account.id
    )

    return MessageOut(message="Blocked sender removed")
