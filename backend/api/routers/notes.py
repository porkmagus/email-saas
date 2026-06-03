"""Notes router.

Simple text notes CRUD.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, Note
from api.schemas import MessageOut, NoteCreate, NoteOut, NoteUpdate
from api.services.audit import audit_from_request

router = APIRouter()


@router.post("", response_model=NoteOut)
async def create_note(
    request: Request,
    data: NoteCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    note = Note(
        account_id=account.id,
        title=data.title,
        content=data.content,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)

    await audit_from_request(
        request, "create_note", "note", str(note.id), account.id, account.id,
        metadata={"title": data.title}
    )

    return note


@router.get("", response_model=list[NoteOut])
async def list_notes(
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Note)
        .where(Note.account_id == account.id)
        .order_by(Note.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{note_id}", response_model=NoteOut)
async def get_note(
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Note).where(Note.id == note_id, Note.account_id == account.id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.patch("/{note_id}", response_model=NoteOut)
async def update_note(
    request: Request,
    note_id: uuid.UUID,
    data: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Note).where(Note.id == note_id, Note.account_id == account.id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(note, key, value)

    db.add(note)
    await db.commit()
    await db.refresh(note)

    await audit_from_request(
        request, "update_note", "note", str(note_id), account.id, account.id,
        metadata={"changes": list(data.model_dump(exclude_unset=True).keys())}
    )

    return note


@router.delete("/{note_id}", response_model=MessageOut)
async def delete_note(
    request: Request,
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Note).where(Note.id == note_id, Note.account_id == account.id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    await db.delete(note)
    await db.commit()

    await audit_from_request(
        request, "delete_note", "note", str(note_id), account.id, account.id
    )

    return MessageOut(message="Note deleted")
