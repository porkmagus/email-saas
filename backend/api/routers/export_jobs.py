"""Export jobs router."""

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, ExportJob
from api.schemas import ExportJobOut

router = APIRouter()


class EmailExportRequest(BaseModel):
    mailbox_ids: list[uuid.UUID] | None = None
    since: datetime | None = None


class CalendarExportRequest(BaseModel):
    since: datetime | None = None


class ContactsExportRequest(BaseModel):
    group_id: uuid.UUID | None = None


async def _run_export_job(db_factory, job_id: uuid.UUID) -> None:
    """Placeholder background task for export execution."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from api.db import get_db
    async for db in get_db():
        result = await db.execute(select(ExportJob).where(ExportJob.id == job_id))
        job = result.scalar_one_or_none()
        if job:
            job.status = "running"
            job.started_at = datetime.now(timezone.utc)
            await db.commit()
            # Placeholder: generate a dummy file path
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            job.file_path = f"/tmp/export_{job.id}_{job.type}.tmp"
            job.file_size = 0
            await db.commit()
        break


@router.post("/emails", response_model=ExportJobOut)
async def export_emails(
    data: EmailExportRequest,
    background_tasks: BackgroundTasks,
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
    background_tasks.add_task(_run_export_job, get_db, job.id)
    return job


@router.post("/calendar", response_model=ExportJobOut)
async def export_calendar(
    data: CalendarExportRequest,
    background_tasks: BackgroundTasks,
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
    background_tasks.add_task(_run_export_job, get_db, job.id)
    return job


@router.post("/contacts", response_model=ExportJobOut)
async def export_contacts(
    data: ContactsExportRequest,
    background_tasks: BackgroundTasks,
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
    background_tasks.add_task(_run_export_job, get_db, job.id)
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
