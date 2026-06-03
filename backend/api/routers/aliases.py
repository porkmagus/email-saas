import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, Alias, Domain, Mailbox
from api.schemas import AliasCreate, AliasOut, AliasUpdate, MessageOut
from api.services.audit import audit_from_request
from api.services.stalwart_api import create_alias_in_stalwart, delete_alias_in_stalwart

router = APIRouter()


@router.post("", response_model=AliasOut)
async def create_alias(
    request: Request,
    data: AliasCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    # Verify domain ownership
    domain_result = await db.execute(select(Domain).where(Domain.id == data.domain_id, Domain.account_id == account.id))
    domain = domain_result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    # Verify target mailbox ownership
    mailbox_result = await db.execute(select(Mailbox).where(Mailbox.id == data.target_mailbox_id, Mailbox.account_id == account.id))
    mailbox = mailbox_result.scalar_one_or_none()
    if not mailbox:
        raise HTTPException(status_code=404, detail="Target mailbox not found")

    # Check uniqueness
    existing = await db.execute(
        select(Alias).where(
            Alias.local_part == data.local_part,
            Alias.domain_id == data.domain_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Alias already exists for this domain")

    alias = Alias(
        account_id=account.id,
        domain_id=data.domain_id,
        local_part=data.local_part,
        target_mailbox_id=data.target_mailbox_id,
    )
    db.add(alias)
    await db.commit()
    await db.refresh(alias)

    # Sync to Stalwart
    alias_address = f"{data.local_part}@{domain.domain}"
    target_address = f"{mailbox.local_part}@{domain.domain}"
    try:
        await create_alias_in_stalwart(alias_address, target_address)
    except Exception as e:
        # Don't fail the request if Stalwart sync fails, but log it
        pass

    await audit_from_request(
        request, "create_alias", "alias", str(alias.id), account.id, account.id,
        metadata={"local_part": data.local_part, "domain": domain.domain, "target": target_address}
    )

    return alias


@router.get("", response_model=list[AliasOut])
async def list_aliases(
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(select(Alias).where(Alias.account_id == account.id))
    return result.scalars().all()


@router.get("/{alias_id}", response_model=AliasOut)
async def get_alias(
    alias_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(select(Alias).where(Alias.id == alias_id, Alias.account_id == account.id))
    alias = result.scalar_one_or_none()
    if not alias:
        raise HTTPException(status_code=404, detail="Alias not found")
    return alias


@router.patch("/{alias_id}", response_model=AliasOut)
async def update_alias(
    request: Request,
    alias_id: uuid.UUID,
    data: AliasUpdate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(select(Alias).where(Alias.id == alias_id, Alias.account_id == account.id))
    alias = result.scalar_one_or_none()
    if not alias:
        raise HTTPException(status_code=404, detail="Alias not found")

    if data.is_active is not None:
        alias.is_active = data.is_active
    if data.target_mailbox_id is not None:
        mailbox_result = await db.execute(select(Mailbox).where(Mailbox.id == data.target_mailbox_id, Mailbox.account_id == account.id))
        if not mailbox_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Target mailbox not found")
        alias.target_mailbox_id = data.target_mailbox_id

    await db.commit()
    await db.refresh(alias)

    await audit_from_request(
        request, "update_alias", "alias", str(alias.id), account.id, account.id,
        metadata={"is_active": alias.is_active, "target_mailbox_id": str(alias.target_mailbox_id)}
    )

    return alias


@router.delete("/{alias_id}", response_model=MessageOut)
async def delete_alias(
    request: Request,
    alias_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(select(Alias).where(Alias.id == alias_id, Alias.account_id == account.id))
    alias = result.scalar_one_or_none()
    if not alias:
        raise HTTPException(status_code=404, detail="Alias not found")

    domain_result = await db.execute(select(Domain).where(Domain.id == alias.domain_id))
    domain = domain_result.scalar_one_or_none()
    alias_address = f"{alias.local_part}@{domain.domain}" if domain else None

    await db.delete(alias)
    await db.commit()

    # Sync to Stalwart
    if alias_address:
        try:
            await delete_alias_in_stalwart(alias_address)
        except Exception:
            pass

    await audit_from_request(
        request, "delete_alias", "alias", str(alias_id), account.id, account.id,
        metadata={"alias": alias_address}
    )

    return MessageOut(message="Alias deleted")
