import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, VacationResponse
from api.schemas import MessageOut, VacationResponseCreate, VacationResponseOut
from api.services.audit import audit_from_request

router = APIRouter()


@router.get("", response_model=VacationResponseOut | None)
async def get_vacation_response(
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(VacationResponse).where(VacationResponse.account_id == account.id)
    )
    return result.scalar_one_or_none()


@router.put("", response_model=VacationResponseOut)
async def upsert_vacation_response(
    request: Request,
    data: VacationResponseCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(VacationResponse).where(VacationResponse.account_id == account.id)
    )
    vr = result.scalar_one_or_none()

    if vr is None:
        vr = VacationResponse(account_id=account.id)
        db.add(vr)

    vr.is_active = data.is_active
    vr.subject = data.subject
    vr.body = data.body
    vr.start_at = data.start_at
    vr.end_at = data.end_at
    vr.only_contacts = data.only_contacts
    vr.only_aliases = data.only_aliases

    await db.commit()
    await db.refresh(vr)

    await audit_from_request(
        request, "upsert_vacation_response", "vacation_response", str(vr.id), account.id, account.id,
        metadata={"is_active": vr.is_active}
    )

    return vr


@router.delete("", response_model=MessageOut)
async def delete_vacation_response(
    request: Request,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(VacationResponse).where(VacationResponse.account_id == account.id)
    )
    vr = result.scalar_one_or_none()
    if vr:
        await db.delete(vr)
        await db.commit()

    await audit_from_request(
        request, "delete_vacation_response", "vacation_response", None, account.id, account.id
    )

    return MessageOut(message="Vacation response deleted")
