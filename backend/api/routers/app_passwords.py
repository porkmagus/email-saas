"""App passwords router.

Manages app-specific passwords for IMAP/SMTP access.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, AppPassword
from api.schemas import AppPasswordCreate, AppPasswordOut, AppPasswordUpdate, MessageOut
from api.services.audit import audit_from_request

router = APIRouter()


@router.post("", response_model=AppPasswordOut)
async def create_app_password(
    request: Request,
    data: AppPasswordCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    # Placeholder for password generation; in production this would generate a
    # secure random string and hash it.
    import secrets
    raw_password = secrets.token_urlsafe(32)
    hashed_password = f"__hashed__{raw_password}"  # Replace with real hashing

    app_pw = AppPassword(
        account_id=account.id,
        name=data.name,
        hashed_password=hashed_password,
        permissions=data.permissions,
    )
    db.add(app_pw)
    await db.commit()
    await db.refresh(app_pw)

    await audit_from_request(
        request, "create_app_password", "app_password", str(app_pw.id), account.id, account.id,
        metadata={"name": data.name, "permissions": data.permissions}
    )

    return app_pw


@router.get("", response_model=list[AppPasswordOut])
async def list_app_passwords(
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(AppPassword)
        .where(AppPassword.account_id == account.id)
        .order_by(AppPassword.created_at.desc())
    )
    return result.scalars().all()


@router.patch("/{app_password_id}", response_model=AppPasswordOut)
async def update_app_password(
    request: Request,
    app_password_id: uuid.UUID,
    data: AppPasswordUpdate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(AppPassword).where(
            AppPassword.id == app_password_id,
            AppPassword.account_id == account.id,
        )
    )
    app_pw = result.scalar_one_or_none()
    if not app_pw:
        raise HTTPException(status_code=404, detail="App password not found")

    if data.revoked is True:
        app_pw.revoked_at = datetime.now(timezone.utc)
    elif data.revoked is False:
        app_pw.revoked_at = None

    if data.name is not None:
        app_pw.name = data.name
    if data.permissions is not None:
        app_pw.permissions = data.permissions

    db.add(app_pw)
    await db.commit()
    await db.refresh(app_pw)

    await audit_from_request(
        request, "update_app_password", "app_password", str(app_password_id), account.id, account.id,
        metadata={"changes": list(data.model_dump(exclude_unset=True).keys())}
    )

    return app_pw


@router.delete("/{app_password_id}", response_model=MessageOut)
async def delete_app_password(
    request: Request,
    app_password_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(AppPassword).where(
            AppPassword.id == app_password_id,
            AppPassword.account_id == account.id,
        )
    )
    app_pw = result.scalar_one_or_none()
    if not app_pw:
        raise HTTPException(status_code=404, detail="App password not found")

    await db.delete(app_pw)
    await db.commit()

    await audit_from_request(
        request, "delete_app_password", "app_password", str(app_password_id), account.id, account.id
    )

    return MessageOut(message="App password deleted")
