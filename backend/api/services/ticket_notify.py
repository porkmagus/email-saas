import asyncio
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.models import Ticket, TicketComment, Account

if TYPE_CHECKING:
    pass

settings = get_settings()


async def notify_ticket_change(ticket: Ticket, comment: TicketComment, db: AsyncSession) -> None:
    """
    Send notifications on ticket changes.
    In production this integrates with SMTP, Slack webhooks, etc.
    """
    # Get account email
    result = await db.execute(select(Account).where(Account.id == ticket.account_id))
    account = result.scalar_one_or_none()
    if not account:
        return

    subject = f"[Ticket #{str(ticket.id)[:8]}] {ticket.title}"
    body = f"New comment on ticket '{ticket.title}':\n\n{comment.body}\n\n"

    # Staff notification
    if not comment.is_internal and ticket.assigned_to:
        # Send to assigned staff
        pass

    # Customer notification
    if comment.is_internal:
        # Don't notify customer on internal notes
        return
    else:
        # Notify customer
        pass

    # Slack webhook placeholder
    if settings.slack_webhook_url:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(
                    settings.slack_webhook_url,
                    json={
                        "text": f"{subject}\nFrom: {comment.author_email}\nStatus: {ticket.status.value}\n{comment.body[:500]}"
                    },
                    timeout=10.0,
                )
        except Exception:
            pass
