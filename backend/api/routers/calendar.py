"""Calendar events router.

CRUD for calendar events scoped to the current account.
"""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, CalendarEvent
from api.schemas import CalendarEventCreate, CalendarEventOut, CalendarEventUpdate, MessageOut
from api.services.audit import audit_from_request

router = APIRouter()


@router.post("/events", response_model=CalendarEventOut)
async def create_event(
    request: Request,
    data: CalendarEventCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    event = CalendarEvent(
        account_id=account.id,
        title=data.title,
        description=data.description,
        start_at=data.start_at,
        end_at=data.end_at,
        all_day=data.all_day,
        location=data.location,
        recurrence_rule=data.recurrence_rule,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    await audit_from_request(
        request, "create_calendar_event", "calendar_event", str(event.id), account.id, account.id,
        metadata={"title": data.title}
    )

    return event


@router.get("/events", response_model=list[CalendarEventOut])
async def list_events(
    start: datetime | None = None,
    end: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    stmt = select(CalendarEvent).where(CalendarEvent.account_id == account.id)
    if start is not None:
        stmt = stmt.where(CalendarEvent.start_at >= start)
    if end is not None:
        stmt = stmt.where(CalendarEvent.start_at <= end)
    stmt = stmt.order_by(CalendarEvent.start_at.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/events/{event_id}", response_model=CalendarEventOut)
async def get_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(CalendarEvent).where(CalendarEvent.id == event_id, CalendarEvent.account_id == account.id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.patch("/events/{event_id}", response_model=CalendarEventOut)
async def update_event(
    request: Request,
    event_id: uuid.UUID,
    data: CalendarEventUpdate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(CalendarEvent).where(CalendarEvent.id == event_id, CalendarEvent.account_id == account.id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(event, key, value)

    db.add(event)
    await db.commit()
    await db.refresh(event)

    await audit_from_request(
        request, "update_calendar_event", "calendar_event", str(event_id), account.id, account.id,
        metadata={"changes": list(data.model_dump(exclude_unset=True).keys())}
    )

    return event


@router.delete("/events/{event_id}", response_model=MessageOut)
async def delete_event(
    request: Request,
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(CalendarEvent).where(CalendarEvent.id == event_id, CalendarEvent.account_id == account.id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await db.delete(event)
    await db.commit()

    await audit_from_request(
        request, "delete_calendar_event", "calendar_event", str(event_id), account.id, account.id
    )

    return MessageOut(message="Event deleted")
