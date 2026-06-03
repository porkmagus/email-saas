import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, Contact, ContactGroup
from api.schemas import (
    ContactCreate,
    ContactGroupCreate,
    ContactGroupOut,
    ContactOut,
    ContactUpdate,
    MessageOut,
)
from api.services.audit import audit_from_request

router = APIRouter()

# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------

@router.post("", response_model=ContactOut)
async def create_contact(
    request: Request,
    data: ContactCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    contact = Contact(
        account_id=account.id,
        email=data.email,
        display_name=data.display_name,
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        notes=data.notes,
        is_vip=data.is_vip,
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    await audit_from_request(
        request, "create_contact", "contact", str(contact.id), account.id, account.id,
        metadata={"email": contact.email}
    )

    return contact


@router.get("", response_model=list[ContactOut])
async def list_contacts(
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Contact).where(Contact.account_id == account.id).order_by(Contact.email)
    )
    return result.scalars().all()


@router.get("/{contact_id}", response_model=ContactOut)
async def get_contact(
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.account_id == account.id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.patch("/{contact_id}", response_model=ContactOut)
async def update_contact(
    request: Request,
    contact_id: uuid.UUID,
    data: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.account_id == account.id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    for field in ["email", "display_name", "first_name", "last_name", "phone", "notes", "is_vip"]:
        val = getattr(data, field)
        if val is not None:
            setattr(contact, field, val)

    await db.commit()
    await db.refresh(contact)

    await audit_from_request(
        request, "update_contact", "contact", str(contact.id), account.id, account.id
    )

    return contact


@router.delete("/{contact_id}", response_model=MessageOut)
async def delete_contact(
    request: Request,
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id, Contact.account_id == account.id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    await db.delete(contact)
    await db.commit()

    await audit_from_request(
        request, "delete_contact", "contact", str(contact_id), account.id, account.id
    )

    return MessageOut(message="Contact deleted")


# ---------------------------------------------------------------------------
# Contact groups
# ---------------------------------------------------------------------------

@router.post("/groups", response_model=ContactGroupOut)
async def create_contact_group(
    request: Request,
    data: ContactGroupCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    group = ContactGroup(account_id=account.id, name=data.name)
    db.add(group)
    await db.commit()
    await db.refresh(group)

    await audit_from_request(
        request, "create_contact_group", "contact_group", str(group.id), account.id, account.id,
        metadata={"name": group.name}
    )

    return group


@router.get("/groups", response_model=list[ContactGroupOut])
async def list_contact_groups(
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(ContactGroup).where(ContactGroup.account_id == account.id)
    )
    return result.scalars().all()


@router.delete("/groups/{group_id}", response_model=MessageOut)
async def delete_contact_group(
    request: Request,
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(ContactGroup).where(ContactGroup.id == group_id, ContactGroup.account_id == account.id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    await db.delete(group)
    await db.commit()

    await audit_from_request(
        request, "delete_contact_group", "contact_group", str(group_id), account.id, account.id
    )

    return MessageOut(message="Group deleted")
