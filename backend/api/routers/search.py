"""Search router.

Full-text search across emails, contacts, files, and notes.
"""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, Contact, File, Message, Note

router = APIRouter()

SearchScope = Literal["emails", "contacts", "files", "notes", "all"]


class SearchQuery(BaseModel):
    q: str = Field(min_length=1)
    scope: SearchScope | None = "all"
    limit: int = Field(default=20, ge=1, le=100)


class EmailSearchResult(BaseModel):
    id: uuid.UUID
    subject: str
    from_addr: str
    snippet: str | None
    received_at: str
    folder: str


class ContactSearchResult(BaseModel):
    id: uuid.UUID
    name: str | None
    email: str
    is_vip: bool


class FileSearchResult(BaseModel):
    id: uuid.UUID
    filename: str
    size: int
    created_at: str


class NoteSearchResult(BaseModel):
    id: uuid.UUID
    title: str
    content_preview: str | None
    created_at: str


class SearchOut(BaseModel):
    emails: list[EmailSearchResult]
    contacts: list[ContactSearchResult]
    files: list[FileSearchResult]
    notes: list[NoteSearchResult]
    total: int


async def search_emails(
    db: AsyncSession, account_id: uuid.UUID, q: str, limit: int
) -> list[EmailSearchResult]:
    pattern = f"%{q}%"
    stmt = (
        select(Message)
        .where(
            Message.account_id == account_id,
            or_(
                func.lower(Message.subject).like(func.lower(pattern)),
                func.lower(Message.from_addr).like(func.lower(pattern)),
                func.lower(Message.body_preview).like(func.lower(pattern)),
            ),
        )
        .order_by(Message.received_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        EmailSearchResult(
            id=r.id,
            subject=r.subject,
            from_addr=r.from_addr,
            snippet=r.body_preview[:200] if r.body_preview else None,
            received_at=r.received_at.isoformat(),
            folder=r.folder,
        )
        for r in rows
    ]


async def search_contacts(
    db: AsyncSession, account_id: uuid.UUID, q: str, limit: int
) -> list[ContactSearchResult]:
    pattern = f"%{q}%"
    stmt = (
        select(Contact)
        .where(
            Contact.account_id == account_id,
            or_(
                func.lower(Contact.email).like(func.lower(pattern)),
                func.lower(Contact.display_name).like(func.lower(pattern)),
                func.lower(Contact.first_name).like(func.lower(pattern)),
                func.lower(Contact.last_name).like(func.lower(pattern)),
            ),
        )
        .order_by(Contact.email)
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        ContactSearchResult(
            id=r.id,
            name=r.display_name or f"{r.first_name or ''} {r.last_name or ''}".strip() or None,
            email=r.email,
            is_vip=r.is_vip,
        )
        for r in rows
    ]


async def search_files(
    db: AsyncSession, account_id: uuid.UUID, q: str, limit: int
) -> list[FileSearchResult]:
    pattern = f"%{q}%"
    stmt = (
        select(File)
        .where(
            File.account_id == account_id,
            func.lower(File.name).like(func.lower(pattern)),
        )
        .order_by(File.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        FileSearchResult(
            id=r.id,
            filename=r.name,
            size=r.size_bytes,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


async def search_notes(
    db: AsyncSession, account_id: uuid.UUID, q: str, limit: int
) -> list[NoteSearchResult]:
    pattern = f"%{q}%"
    stmt = (
        select(Note)
        .where(
            Note.account_id == account_id,
            or_(
                func.lower(Note.title).like(func.lower(pattern)),
                func.lower(Note.content).like(func.lower(pattern)),
            ),
        )
        .order_by(Note.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        NoteSearchResult(
            id=r.id,
            title=r.title,
            content_preview=r.content[:200] if r.content else None,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.post("", response_model=SearchOut)
async def search(
    data: SearchQuery,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    scope = data.scope or "all"
    emails: list[EmailSearchResult] = []
    contacts: list[ContactSearchResult] = []
    files: list[FileSearchResult] = []
    notes: list[NoteSearchResult] = []

    if scope in ("all", "emails"):
        emails = await search_emails(db, account.id, data.q, data.limit)
    if scope in ("all", "contacts"):
        contacts = await search_contacts(db, account.id, data.q, data.limit)
    if scope in ("all", "files"):
        files = await search_files(db, account.id, data.q, data.limit)
    if scope in ("all", "notes"):
        notes = await search_notes(db, account.id, data.q, data.limit)

    total = len(emails) + len(contacts) + len(files) + len(notes)
    return SearchOut(emails=emails, contacts=contacts, files=files, notes=notes, total=total)
