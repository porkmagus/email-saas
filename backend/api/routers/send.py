import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, Mailbox
from api.schemas import MessageOut
from api.services.send_throttle import check_send_allowed, record_send
from api.services.abuse_scoring import check_abuse_status
from api.services.audit import audit_from_request


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class SendEmailRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    to: list[EmailStr]
    subject: str
    body: str
    from_mailbox_id: uuid.UUID | None = None
    text_body: str | None = None
    html_body: str | None = None


@router.post("/send", response_model=MessageOut)
@limiter.limit("60/minute")
async def send_email(
    request: Request,
    data: SendEmailRequest,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    """Send an email through the service. Throttled and abuse-checked."""
    # Check abuse status first
    allowed, reason = await check_abuse_status(db, account.id)
    if not allowed:
        raise HTTPException(status_code=429, detail=reason)

    # Resolve sender mailbox
    domain_id = None
    mailbox_id = None
    if data.from_mailbox_id:
        result = await db.execute(
            select(Mailbox).where(
                Mailbox.id == data.from_mailbox_id,
                Mailbox.account_id == account.id,
            )
        )
        mailbox = result.scalar_one_or_none()
        if not mailbox:
            raise HTTPException(status_code=404, detail="Sender mailbox not found")
        mailbox_id = mailbox.id
        domain_id = mailbox.domain_id
    else:
        # Use default mailbox for account
        result = await db.execute(
            select(Mailbox).where(Mailbox.account_id == account.id).limit(1)
        )
        mailbox = result.scalar_one_or_none()
        if mailbox:
            mailbox_id = mailbox.id
            domain_id = mailbox.domain_id

    # Check send limits
    allowed, reason = await check_send_allowed(db, account.id, domain_id=domain_id, mailbox_id=mailbox_id)
    if not allowed:
        raise HTTPException(status_code=429, detail=reason)

    # Queue to Stalwart (or local queue for retry)
    try:
        from api.services.stalwart_api import queue_message
        await queue_message(
            from_address=f"{mailbox.local_part}@{mailbox.domain.domain}" if mailbox else account.email,
            to_addresses=[str(addr) for addr in data.to],
            subject=data.subject,
            text_body=data.text_body or data.body,
            html_body=data.html_body,
        )
        await record_send(db, account.id, domain_id=domain_id, mailbox_id=mailbox_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue message: {e}")

    await audit_from_request(
        request,
        "send_email",
        "send_event",
        None,
        account_id=account.id,
        actor_id=account.id,
        metadata={
            "to_count": len(data.to),
            "subject": data.subject,
            "mailbox_id": str(mailbox_id) if mailbox_id else None,
        },
    )
    return {"message": f"Message queued to {len(data.to)} recipient(s)"}
