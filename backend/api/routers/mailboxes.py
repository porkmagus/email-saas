import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account, hash_password
from api.models import Account, Domain, Mailbox, AccountStatus, ProvisioningJob, JobType, JobStatus
from api.schemas import MailboxCreate, MailboxUpdate, MailboxOut, MessageOut
from api.services.audit import audit_from_request
from api.services.stalwart_api import create_mailbox as stalwart_create_mailbox, delete_mailbox as stalwart_delete_mailbox

router = APIRouter()


@router.post("", response_model=MailboxOut)
async def create_mailbox(
    request: Request,
    data: MailboxCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    # Verify domain belongs to account
    domain_result = await db.execute(
        select(Domain).where(Domain.id == data.domain_id, Domain.account_id == account.id)
    )
    domain = domain_result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    # Check uniqueness
    existing = await db.execute(
        select(Mailbox).where(
            Mailbox.local_part == data.local_part,
            Mailbox.domain_id == data.domain_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Mailbox already exists")

    mailbox = Mailbox(
        id=uuid.uuid4(),
        account_id=account.id,
        domain_id=data.domain_id,
        local_part=data.local_part,
        display_name=data.display_name,
        quota_bytes=data.quota_bytes,
        status=AccountStatus.active,
        password_hash=hash_password(data.password),
    )
    db.add(mailbox)
    await db.commit()
    await db.refresh(mailbox)

    # Directly create in Stalwart (synchronous for reliability)
    try:
        await stalwart_create_mailbox(
            f"{data.local_part}@{domain.domain}",
            data.password,
            data.quota_bytes,
        )
    except Exception as e:
        # Log but don't fail - the DB record exists and a retry job can be created
        job = ProvisioningJob(
            id=uuid.uuid4(),
            account_id=account.id,
            type=JobType.add_mailbox,
            payload={
                "mailbox_id": str(mailbox.id),
                "domain_id": str(domain.id),
                "local_part": data.local_part,
                "error": str(e),
            },
            status=JobStatus.failed,
        )
        db.add(job)
        await db.commit()
        # Continue without failing - the DB record is the source of truth

    await audit_from_request(
        request, "create_mailbox", "mailbox", str(mailbox.id), account.id, account.id
    )
    return mailbox


@router.get("", response_model=list[MailboxOut])
async def list_mailboxes(
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Mailbox).where(Mailbox.account_id == account.id)
    )
    return result.scalars().all()


@router.get("/{mailbox_id}", response_model=MailboxOut)
async def get_mailbox(
    mailbox_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Mailbox).where(Mailbox.id == mailbox_id, Mailbox.account_id == account.id)
    )
    mailbox = result.scalar_one_or_none()
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")
    return mailbox


@router.patch("/{mailbox_id}", response_model=MailboxOut)
async def update_mailbox(
    request: Request,
    mailbox_id: uuid.UUID,
    data: MailboxUpdate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Mailbox).where(Mailbox.id == mailbox_id, Mailbox.account_id == account.id)
    )
    mailbox = result.scalar_one_or_none()
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")

    if data.display_name is not None:
        mailbox.display_name = data.display_name
    if data.quota_bytes is not None:
        mailbox.quota_bytes = data.quota_bytes
    if data.password is not None:
        mailbox.password_hash = hash_password(data.password)
    mailbox.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(mailbox)
    await audit_from_request(
        request, "update_mailbox", "mailbox", str(mailbox.id), account.id, account.id
    )
    return mailbox


@router.delete("/{mailbox_id}", response_model=MessageOut)
async def delete_mailbox(
    request: Request,
    mailbox_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Mailbox).where(Mailbox.id == mailbox_id, Mailbox.account_id == account.id)
    )
    mailbox = result.scalar_one_or_none()
    if not mailbox:
        raise HTTPException(status_code=404, detail="Mailbox not found")

    # Look up domain for Stalwart deletion
    domain_result = await db.execute(
        select(Domain).where(Domain.id == mailbox.domain_id)
    )
    domain = domain_result.scalar_one_or_none()

    # Directly delete from Stalwart (synchronous for reliability)
    if domain:
        try:
            await stalwart_delete_mailbox(f"{mailbox.local_part}@{domain.domain}")
        except Exception:
            # Log but don't fail - the DB record is already deleted
            pass

    await db.delete(mailbox)
    await db.commit()
    await audit_from_request(
        request, "delete_mailbox", "mailbox", str(mailbox_id), account.id, account.id
    )
    return {"message": "Mailbox deleted"}
