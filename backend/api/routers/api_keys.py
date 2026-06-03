import secrets
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, ApiKey
from api.schemas import ApiKeyCreate, ApiKeyOut, ApiKeyWithSecret, MessageOut
from api.services.audit import audit_from_request
from api.services.api_key_crypto import hash_api_key

router = APIRouter()


@router.post("", response_model=ApiKeyWithSecret)
async def create_api_key(
    request: Request,
    data: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    raw = "esk_" + secrets.token_urlsafe(32)
    prefix = raw[:11]
    key = ApiKey(
        id=uuid.uuid4(),
        account_id=account.id,
        name=data.name,
        prefix=prefix,
        hashed_secret=hash_api_key(raw),
        permissions=data.permissions,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)
    await audit_from_request(
        request, "create_api_key", "api_key", str(key.id), account.id, account.id
    )
    return {"id": key.id, "account_id": key.account_id, "name": key.name, "prefix": key.prefix,
            "permissions": key.permissions, "last_used_at": None, "created_at": key.created_at,
            "revoked_at": None, "secret": raw}


@router.get("", response_model=list[ApiKeyOut])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.account_id == account.id, ApiKey.revoked_at.is_(None))
    )
    return result.scalars().all()


@router.delete("/{key_id}", response_model=MessageOut)
async def revoke_api_key(
    request: Request,
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.account_id == account.id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    key.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    await audit_from_request(
        request, "revoke_api_key", "api_key", str(key_id), account.id, account.id
    )
    return {"message": "API key revoked"}
