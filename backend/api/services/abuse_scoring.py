import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Account, SendEvent, SendEventStatus, AbuseScore, AbuseScoreStatus


async def calculate_abuse_score(
    db: AsyncSession,
    account_id: uuid.UUID,
) -> AbuseScore:
    """Calculate abuse score for an account based on recent sending activity."""
    result = await db.execute(
        select(AbuseScore).where(AbuseScore.account_id == account_id)
    )
    score = result.scalar_one_or_none()
    if not score:
        score = AbuseScore(
            id=uuid.uuid4(),
            account_id=account_id,
        )
        db.add(score)

    # Window: last 7 days
    window_start = datetime.now(timezone.utc) - timedelta(days=7)

    # Total sent
    total_sent_result = await db.execute(
        select(func.count()).select_from(SendEvent).where(
            SendEvent.account_id == account_id,
            SendEvent.created_at >= window_start,
        )
    )
    total_sent = total_sent_result.scalar() or 0

    # Bounces
    bounces_result = await db.execute(
        select(func.count()).select_from(SendEvent).where(
            SendEvent.account_id == account_id,
            SendEvent.status == SendEventStatus.bounced,
            SendEvent.created_at >= window_start,
        )
    )
    bounces = bounces_result.scalar() or 0

    # Complaints
    complaints_result = await db.execute(
        select(func.count()).select_from(SendEvent).where(
            SendEvent.account_id == account_id,
            SendEvent.status == SendEventStatus.complained,
            SendEvent.created_at >= window_start,
        )
    )
    complaints = complaints_result.scalar() or 0

    # Calculate rates
    bounce_rate = (bounces / total_sent * 100) if total_sent > 0 else 0.0
    complaint_rate = (complaints / total_sent * 100) if total_sent > 0 else 0.0

    # Send spike score: compare last 24h vs previous 6 days average
    last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    prev_6d = datetime.now(timezone.utc) - timedelta(days=7)

    recent_sent_result = await db.execute(
        select(func.count()).select_from(SendEvent).where(
            SendEvent.account_id == account_id,
            SendEvent.created_at >= last_24h,
        )
    )
    recent_sent = recent_sent_result.scalar() or 0

    prev_sent_result = await db.execute(
        select(func.count()).select_from(SendEvent).where(
            SendEvent.account_id == account_id,
            SendEvent.created_at >= prev_6d,
            SendEvent.created_at < last_24h,
        )
    )
    prev_sent = prev_sent_result.scalar() or 0
    prev_daily_avg = prev_sent / 6.0 if prev_sent > 0 else 1.0

    send_spike = (recent_sent / prev_daily_avg) if prev_daily_avg > 0 else 0.0

    # Suspicious recipient score: high percentage of different domains
    domains_result = await db.execute(
        select(func.count(func.distinct(SendEvent.recipient_domain))).select_from(SendEvent).where(
            SendEvent.account_id == account_id,
            SendEvent.created_at >= window_start,
        )
    )
    unique_domains = domains_result.scalar() or 0

    suspicious_recipient = (unique_domains / total_sent * 100) if total_sent > 0 else 0.0

    # Total score (weighted)
    total = (
        bounce_rate * 2.0 +
        complaint_rate * 10.0 +
        max(0, send_spike - 1.0) * 5.0 +
        max(0, suspicious_recipient - 50.0) * 0.5
    )

    # Determine status
    if total >= 50 or complaint_rate >= 0.3:
        status = AbuseScoreStatus.red
    elif total >= 25 or bounce_rate >= 5.0:
        status = AbuseScoreStatus.orange
    elif total >= 10 or bounce_rate >= 3.0:
        status = AbuseScoreStatus.yellow
    else:
        status = AbuseScoreStatus.green

    # Update score
    score.bounce_rate = round(bounce_rate, 2)
    score.complaint_rate = round(complaint_rate, 2)
    score.send_spike_score = round(send_spike, 2)
    score.suspicious_recipient_score = round(suspicious_recipient, 2)
    score.total_score = round(total, 2)
    score.status = status
    score.calculated_at = datetime.now(timezone.utc)
    score.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(score)
    return score


async def check_abuse_status(
    db: AsyncSession,
    account_id: uuid.UUID,
) -> tuple[bool, Optional[str]]:
    """Check if account is allowed to send based on abuse score.
    Returns (allowed, reason)."""
    result = await db.execute(
        select(AbuseScore).where(AbuseScore.account_id == account_id)
    )
    score = result.scalar_one_or_none()
    if not score:
        return True, None

    if score.status == AbuseScoreStatus.red:
        return False, "Account suspended due to abuse indicators. Contact support."
    if score.status == AbuseScoreStatus.orange:
        return False, "Sending paused due to elevated bounce/complaint rate. Contact support."
    return True, None


async def enforce_abuse_action(
    db: AsyncSession,
    account_id: uuid.UUID,
    score: AbuseScore,
) -> None:
    """Apply account enforcement based on abuse score.
    
    - Red: Auto-suspend account
    - Orange: Hold outbound mail, notify admin
    - Yellow: Reduce send limits (handled by check_send_allowed)
    """
    from api.models import Account, AccountStatus
    from api.services.audit import audit_log
    
    result = await db.execute(
        select(Account).where(Account.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        return
    
    if score.status == AbuseScoreStatus.red:
        if account.status != AccountStatus.suspended:
            account.status = AccountStatus.suspended
            await db.commit()
            await audit_log(
                "abuse_auto_suspend",
                "account",
                str(account_id),
                account_id=account_id,
                metadata={
                    "bounce_rate": score.bounce_rate,
                    "complaint_rate": score.complaint_rate,
                    "total_score": score.total_score,
                }
            )
            # Notify admin (fire-and-forget)
            await notify_admin(
                f"Account {account_id} auto-suspended due to abuse score: {score.total_score}"
            )
    
    elif score.status == AbuseScoreStatus.orange:
        # Hold outbound mail but don't suspend
        if account.status == AccountStatus.active:
            await audit_log(
                "abuse_hold",
                "account",
                str(account_id),
                account_id=account_id,
                metadata={
                    "bounce_rate": score.bounce_rate,
                    "complaint_rate": score.complaint_rate,
                    "total_score": score.total_score,
                }
            )
            await notify_admin(
                f"Account {account_id} sending paused due to abuse score: {score.total_score}"
            )


async def notify_admin(message: str) -> None:
    """Send admin notification via email or webhook.
    In production: integrate with SMTP, Slack, PagerDuty.
    """
    # Placeholder: log to console for now
    # Real implementation: send to admin email, Slack webhook
    print(f"[ADMIN ALERT] {message}")
