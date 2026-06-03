"""Export jobs router."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, ExportJob
from api.schemas import ExportJobOut
from api.services.queue import enqueue

router = APIRouter()


class EmailExportRequest(BaseModel):
    mailbox_ids: list[uuid.UUID] | None = None
    since: datetime | None = None


class CalendarExportRequest(BaseModel):
    since: datetime | None = None


class ContactsExportRequest(BaseModel):
    group_id: uuid.UUID | None = None


@router.post("/emails", response_model=ExportJobOut)
async def export_emails(
    data: EmailExportRequest,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    job = ExportJob(
        account_id=account.id,
        type="emails",
        status="pending",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    await enqueue(
        job_type="export",
        job_id=job.id,
        account_id=account.id,
        payload={"subtype": "emails", "mailbox_ids": [str(m) for m in data.mailbox_ids] if data.mailbox_ids else None, "since": data.since.isoformat() if data.since else None},
    )
    return job


@router.post("/calendar", response_model=ExportJobOut)
async def export_calendar(
    data: CalendarExportRequest,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    job = ExportJob(
        account_id=account.id,
        type="calendar",
        status="pending",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    await enqueue(
        job_type="export",
        job_id=job.id,
        account_id=account.id,
        payload={"subtype": "calendar", "since": data.since.isoformat() if data.since else None},
    )
    return job


@router.post("/contacts", response_model=ExportJobOut)
async def export_contacts(
    data: ContactsExportRequest,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    job = ExportJob(
        account_id=account.id,
        type="contacts",
        status="pending",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    await enqueue(
        job_type="export",
        job_id=job.id,
        account_id=account.id,
        payload={"subtype": "contacts", "group_id": str(data.group_id) if data.group_id else None},
    )
    return job


@router.get("", response_model=list[ExportJobOut])
async def list_export_jobs(
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(ExportJob)
        .where(ExportJob.account_id == account.id)
        .order_by(ExportJob.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{job_id}", response_model=ExportJobOut)
async def get_export_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(ExportJob).where(ExportJob.id == job_id, ExportJob.account_id == account.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    return job
