"""Snooze router.

Manages snooze rules for pausing email from specific senders, domains, or subjects.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, Snooze
from api.schemas import MessageOut, SnoozeCreate, SnoozeOut
from api.services.audit import audit_from_request

router = APIRouter()


@router.post("", response_model=SnoozeOut, status_code=status.HTTP_201_CREATED)
async def create_snooze(
    request: Request,
    data: SnoozeCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    snooze = Snooze(
        account_id=account.id,
        subject_contains=data.subject_contains,
        sender_address=data.sender_address,
        domain_name=data.domain_name,
        until=data.until,
        active=True,
    )
    db.add(snooze)
    await db.commit()
    await db.refresh(snooze)

    await audit_from_request(
        request, "create_snooze", "snooze", str(snooze.id), account.id, account.id,
        metadata={
            "subject_contains": data.subject_contains,
            "sender_address": data.sender_address,
            "domain_name": data.domain_name,
            "until": data.until.isoformat(),
        }
    )

    return snooze


@router.get("", response_model=list[SnoozeOut])
async def list_snoozes(
    active_only: bool | None = None,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    stmt = select(Snooze).where(Snooze.account_id == account.id)
    if active_only is True:
        stmt = stmt.where(Snooze.active == True)
    elif active_only is False:
        stmt = stmt.where(Snooze.active == False)
    stmt = stmt.order_by(Snooze.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{snooze_id}", response_model=SnoozeOut)
async def get_snooze(
    snooze_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Snooze).where(
            Snooze.id == snooze_id,
            Snooze.account_id == account.id,
        )
    )
    snooze = result.scalar_one_or_none()
    if not snooze:
        raise HTTPException(status_code=404, detail="Snooze rule not found")
    return snooze


@router.delete("/{snooze_id}", response_model=MessageOut)
async def delete_snooze(
    request: Request,
    snooze_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Snooze).where(
            Snooze.id == snooze_id,
            Snooze.account_id == account.id,
        )
    )
    snooze = result.scalar_one_or_none()
    if not snooze:
        raise HTTPException(status_code=404, detail="Snooze rule not found")

    await db.delete(snooze)
    await db.commit()

    await audit_from_request(
        request, "delete_snooze", "snooze", str(snooze_id), account.id, account.id
    )

    return MessageOut(message="Snooze rule deleted")


@router.post("/{snooze_id}/end", response_model=SnoozeOut)
async def end_snooze(
    request: Request,
    snooze_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    """Mark a snooze as inactive (ended early)."""
    result = await db.execute(
        select(Snooze).where(
            Snooze.id == snooze_id,
            Snooze.account_id == account.id,
        )
    )
    snooze = result.scalar_one_or_none()
    if not snooze:
        raise HTTPException(status_code=404, detail="Snooze rule not found")

    snooze.active = False
    snooze.until = datetime.now(timezone.utc)
    db.add(snooze)
    await db.commit()
    await db.refresh(snooze)

    await audit_from_request(
        request, "end_snooze", "snooze", str(snooze_id), account.id, account.id
    )

    return snooze
