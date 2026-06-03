"""File metadata router.

Handles CRUD for file metadata records. Actual file storage is handled via
separate upload endpoints.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, File
from api.schemas import FileCreate, FileOut, FileUpdate, MessageOut
from api.services.audit import audit_from_request

router = APIRouter()


@router.post("", response_model=FileOut)
async def create_file(
    request: Request,
    data: FileCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    existing = await db.execute(
        select(File).where(
            File.account_id == account.id,
            File.name == data.name,
            File.folder == data.folder,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="File already exists in this folder")

    file = File(
        account_id=account.id,
        name=data.name,
        path=data.path,
        size_bytes=data.size_bytes,
        mime_type=data.mime_type,
        folder=data.folder,
    )
    db.add(file)
    await db.commit()
    await db.refresh(file)

    await audit_from_request(
        request, "create_file", "file", str(file.id), account.id, account.id,
        metadata={"name": data.name, "folder": data.folder}
    )

    return file


@router.get("", response_model=list[FileOut])
async def list_files(
    folder: str | None = None,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    stmt = select(File).where(File.account_id == account.id)
    if folder is not None:
        stmt = stmt.where(File.folder == folder)
    stmt = stmt.order_by(File.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{file_id}", response_model=FileOut)
async def get_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(File).where(File.id == file_id, File.account_id == account.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.patch("/{file_id}", response_model=FileOut)
async def update_file(
    request: Request,
    file_id: uuid.UUID,
    data: FileUpdate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(File).where(File.id == file_id, File.account_id == account.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(file, key, value)

    db.add(file)
    await db.commit()
    await db.refresh(file)

    await audit_from_request(
        request, "update_file", "file", str(file_id), account.id, account.id,
        metadata={"changes": list(data.model_dump(exclude_unset=True).keys())}
    )

    return file


@router.delete("/{file_id}", response_model=MessageOut)
async def delete_file(
    request: Request,
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(File).where(File.id == file_id, File.account_id == account.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    await db.delete(file)
    await db.commit()

    await audit_from_request(
        request, "delete_file", "file", str(file_id), account.id, account.id
    )

    return MessageOut(message="File deleted")
