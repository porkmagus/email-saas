"""Sessions router.

Lists and revokes active sessions for the current account.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, Session
from api.schemas import MessageOut, SessionOut
from api.services.audit import audit_from_request

router = APIRouter()


@router.get("", response_model=list[SessionOut])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Session)
        .where(Session.account_id == account.id)
        .order_by(desc(Session.last_active_at))
    )
    return result.scalars().all()


@router.delete("/{session_id}", response_model=MessageOut)
async def delete_session(
    request: Request,
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.account_id == account.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    await db.commit()

    await audit_from_request(
        request, "delete_session", "session", str(session_id), account.id, account.id
    )

    return MessageOut(message="Session revoked")


@router.delete("", response_model=MessageOut)
async def delete_all_sessions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Session).where(Session.account_id == account.id)
    )
    sessions = result.scalars().all()
    for session in sessions:
        await db.delete(session)
    await db.commit()

    await audit_from_request(
        request, "delete_all_sessions", "session", "*", account.id, account.id,
        metadata={"count": len(sessions)}
    )

    return MessageOut(message=f"Revoked {len(sessions)} sessions")
