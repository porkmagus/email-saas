"""Import jobs router."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, ImportJob
from api.schemas import ImportJobCreate, ImportJobOut
from api.services.audit import audit_from_request
from api.services.queue import enqueue

router = APIRouter()


@router.post("", response_model=ImportJobOut)
async def create_import_job(
    data: ImportJobCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    job = ImportJob(
        account_id=account.id,
        server=data.server,
        port=data.port,
        username=data.username,
        password=data.password,
        tls=data.tls,
        status="pending",
        messages_imported=0,
        errors=0,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    await enqueue(
        job_type="import",
        job_id=job.id,
        account_id=account.id,
        payload={
            "server": data.server,
            "port": data.port,
            "username": data.username,
            "password": data.password,
            "tls": data.tls,
        },
    )

    return job


@router.get("", response_model=list[ImportJobOut])
async def list_import_jobs(
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(ImportJob)
        .where(ImportJob.account_id == account.id)
        .order_by(ImportJob.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{job_id}", response_model=ImportJobOut)
async def get_import_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(ImportJob).where(ImportJob.id == job_id, ImportJob.account_id == account.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    return job
