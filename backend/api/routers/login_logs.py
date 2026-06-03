"""Login logs router.

Read-only login history for the current account.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, LoginLog
from api.schemas import LoginLogOut

router = APIRouter()


@router.get("", response_model=list[LoginLogOut])
async def list_login_logs(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(LoginLog)
        .where(LoginLog.account_id == account.id)
        .order_by(desc(LoginLog.created_at))
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()
