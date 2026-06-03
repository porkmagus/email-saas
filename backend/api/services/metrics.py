import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import (
    SendEvent,
    SendEventStatus,
    AbuseScore,
    AbuseScoreStatus,
    ProvisioningJob,
    JobStatus,
    Ticket,
    TicketStatus,
)
from api.services.stalwart_api import get_queue_metrics as get_stalwart_queue_metrics

async def get_mail_metrics(db: AsyncSession) -> dict:
    """Get mail-specific metrics for monitoring dashboard."""
    now = datetime.now(timezone.utc)
    window_24h = now - timedelta(hours=24)
    window_7d = now - timedelta(days=7)

    # Queue depth (send events in last hour that are deferred)
    deferred_result = await db.execute(
        select(func.count()).select_from(SendEvent).where(
            SendEvent.status == SendEventStatus.deferred,
            SendEvent.created_at >= window_24h,
        )
    )
    deferred_count = deferred_result.scalar() or 0

    # Bounce rate (last 24h)
    total_sent_24h = await db.execute(
        select(func.count()).select_from(SendEvent).where(
            SendEvent.created_at >= window_24h,
        )
    )
    total_sent = total_sent_24h.scalar() or 0

    bounces_24h = await db.execute(
        select(func.count()).select_from(SendEvent).where(
            SendEvent.status == SendEventStatus.bounced,
            SendEvent.created_at >= window_24h,
        )
    )
    bounces = bounces_24h.scalar() or 0

    bounce_rate = (bounces / total_sent * 100) if total_sent > 0 else 0.0

    # Complaint rate
    complaints_24h = await db.execute(
        select(func.count()).select_from(SendEvent).where(
            SendEvent.status == SendEventStatus.complained,
            SendEvent.created_at >= window_24h,
        )
    )
    complaints = complaints_24h.scalar() or 0
    complaint_rate = (complaints / total_sent * 100) if total_sent > 0 else 0.0

    # Sends per hour (last 24h)
    sends_per_hour = await db.execute(
        select(func.count()).select_from(SendEvent).where(
            SendEvent.created_at >= window_24h,
        )
    )
    hourly_avg = (sends_per_hour.scalar() or 0) / 24.0

    # Abuse scores
    red_scores = await db.execute(
        select(func.count()).select_from(AbuseScore).where(AbuseScore.status == AbuseScoreStatus.red)
    )
    orange_scores = await db.execute(
        select(func.count()).select_from(AbuseScore).where(AbuseScore.status == AbuseScoreStatus.orange)
    )
    yellow_scores = await db.execute(
        select(func.count()).select_from(AbuseScore).where(AbuseScore.status == AbuseScoreStatus.yellow)
    )

    # Provisioning jobs
    pending_jobs = await db.execute(
        select(func.count()).select_from(ProvisioningJob).where(ProvisioningJob.status == JobStatus.pending)
    )
    failed_jobs = await db.execute(
        select(func.count()).select_from(ProvisioningJob).where(ProvisioningJob.status == JobStatus.failed)
    )

    # Open tickets
    open_tickets = await db.execute(
        select(func.count()).select_from(Ticket).where(Ticket.status == TicketStatus.open)
    )

    # Live Stalwart metrics
    stalwart_metrics = await get_stalwart_queue_metrics()

    return {
        "queue": {
            "deferred_count": deferred_count,
            "bounce_rate_24h": round(bounce_rate, 2),
            "complaint_rate_24h": round(complaint_rate, 2),
            "sends_per_hour": round(hourly_avg, 2),
        },
        "abuse": {
            "red_accounts": red_scores.scalar() or 0,
            "orange_accounts": orange_scores.scalar() or 0,
            "yellow_accounts": yellow_scores.scalar() or 0,
        },
        "operations": {
            "pending_jobs": pending_jobs.scalar() or 0,
            "failed_jobs": failed_jobs.scalar() or 0,
            "open_tickets": open_tickets.scalar() or 0,
        },
        "stalwart": stalwart_metrics,
    }
