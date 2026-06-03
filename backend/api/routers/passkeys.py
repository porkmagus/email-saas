"""Passkeys (WebAuthn) router.

Manages passkey registration for passwordless authentication.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, Passkey
from api.schemas import MessageOut, PasskeyCreate, PasskeyOut, PasskeyUpdate
from api.services.audit import audit_from_request

router = APIRouter()


@router.post("", response_model=PasskeyOut)
async def create_passkey(
    request: Request,
    data: PasskeyCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    # In production, this would integrate with a WebAuthn library to
    # generate a challenge, verify the attestation, and store the credential.
    # Here we create a placeholder record.
    import secrets
    passkey = Passkey(
        account_id=account.id,
        credential_id=secrets.token_urlsafe(16),
        public_key="placeholder",
        name=data.name,
    )
    db.add(passkey)
    await db.commit()
    await db.refresh(passkey)

    await audit_from_request(
        request, "create_passkey", "passkey", str(passkey.id), account.id, account.id,
        metadata={"name": data.name}
    )

    return passkey


@router.get("", response_model=list[PasskeyOut])
async def list_passkeys(
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Passkey)
        .where(Passkey.account_id == account.id)
        .order_by(Passkey.created_at.desc())
    )
    return result.scalars().all()


@router.patch("/{passkey_id}", response_model=PasskeyOut)
async def update_passkey(
    request: Request,
    passkey_id: uuid.UUID,
    data: PasskeyUpdate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Passkey).where(
            Passkey.id == passkey_id,
            Passkey.account_id == account.id,
        )
    )
    passkey = result.scalar_one_or_none()
    if not passkey:
        raise HTTPException(status_code=404, detail="Passkey not found")

    if data.name is not None:
        passkey.name = data.name

    passkey.last_used_at = datetime.now(timezone.utc)
    db.add(passkey)
    await db.commit()
    await db.refresh(passkey)

    await audit_from_request(
        request, "update_passkey", "passkey", str(passkey_id), account.id, account.id,
        metadata={"changes": list(data.model_dump(exclude_unset=True).keys())}
    )

    return passkey


@router.delete("/{passkey_id}", response_model=MessageOut)
async def delete_passkey(
    request: Request,
    passkey_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Passkey).where(
            Passkey.id == passkey_id,
            Passkey.account_id == account.id,
        )
    )
    passkey = result.scalar_one_or_none()
    if not passkey:
        raise HTTPException(status_code=404, detail="Passkey not found")

    await db.delete(passkey)
    await db.commit()

    await audit_from_request(
        request, "delete_passkey", "passkey", str(passkey_id), account.id, account.id
    )

    return MessageOut(message="Passkey deleted")
