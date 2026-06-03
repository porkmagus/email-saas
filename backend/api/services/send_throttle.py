import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from api.config import get_settings
from api.models import Account, OutboundLimit, OutboundLimitPeriod, AccountStatus
from api.db import get_db

settings = get_settings()

# Contabo limit: ~25 emails per minute
# New account: 25/day, warmed: 500/day
NEW_ACCOUNT_DAILY_LIMIT = 25
WARMED_ACCOUNT_DAILY_LIMIT = 500
PROBATION_DAYS = 30
HOURLY_LIMIT_RATIO = 0.1


async def get_or_create_limit(
    db: AsyncSession,
    account_id: uuid.UUID,
    period: OutboundLimitPeriod,
    period_start: datetime,
    period_end: datetime,
    emails_allowed: int,
    domain_id: Optional[uuid.UUID] = None,
    mailbox_id: Optional[uuid.UUID] = None,
) -> OutboundLimit:
    result = await db.execute(
        select(OutboundLimit).where(
            OutboundLimit.account_id == account_id,
            OutboundLimit.period == period,
            OutboundLimit.period_start == period_start,
            OutboundLimit.domain_id == domain_id,
            OutboundLimit.mailbox_id == mailbox_id,
        )
    )
    limit = result.scalar_one_or_none()
    if not limit:
        limit = OutboundLimit(
            id=uuid.uuid4(),
            account_id=account_id,
            domain_id=domain_id,
            mailbox_id=mailbox_id,
            period=period,
            period_start=period_start,
            period_end=period_end,
            emails_allowed=emails_allowed,
            emails_sent=0,
        )
        db.add(limit)
        await db.commit()
        await db.refresh(limit)
    return limit


async def check_send_allowed(
    db: AsyncSession,
    account_id: uuid.UUID,
    domain_id: Optional[uuid.UUID] = None,
    mailbox_id: Optional[uuid.UUID] = None,
) -> tuple[bool, str]:
    """Check if sending is allowed. Returns (allowed, reason)."""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        return False, "Account not found"

    if account.status == AccountStatus.suspended:
        return False, "Account suspended"
    if account.status == AccountStatus.cancelled:
        return False, "Account cancelled"

    # Determine account age and limit
    account_age = datetime.now(timezone.utc) - account.created_at
    is_new = account_age < timedelta(days=PROBATION_DAYS)
    daily_limit = NEW_ACCOUNT_DAILY_LIMIT if is_new else WARMED_ACCOUNT_DAILY_LIMIT
    hourly_limit = int(daily_limit * HOURLY_LIMIT_RATIO)

    # Check daily limit
    now = datetime.now(timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    daily = await get_or_create_limit(
        db, account_id, OutboundLimitPeriod.daily, day_start, day_end, daily_limit,
        domain_id=domain_id, mailbox_id=mailbox_id,
    )
    if daily.emails_sent >= daily.emails_allowed:
        return False, f"Daily send limit reached ({daily_limit} emails/day)"

    # Check hourly limit
    hour_start = now.replace(minute=0, second=0, microsecond=0)
    hour_end = hour_start + timedelta(hours=1)
    hourly = await get_or_create_limit(
        db, account_id, OutboundLimitPeriod.hourly, hour_start, hour_end, hourly_limit,
        domain_id=domain_id, mailbox_id=mailbox_id,
    )
    if hourly.emails_sent >= hourly.emails_allowed:
        return False, f"Hourly send limit reached ({hourly_limit} emails/hour)"

    # Check Contabo per-minute limit via Redis
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    minute_key = f"send_count:{account_id}:{now.strftime('%Y%m%d%H%M')}"
    current_minute = await redis.get(minute_key)
    if current_minute and int(current_minute) >= 25:
        await redis.close()
        return False, "Per-minute send limit reached (25 emails/min)"

    await redis.close()
    return True, ""


async def record_send(
    db: AsyncSession,
    account_id: uuid.UUID,
    domain_id: Optional[uuid.UUID] = None,
    mailbox_id: Optional[uuid.UUID] = None,
) -> None:
    """Record a successful send, incrementing counters."""
    now = datetime.now(timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    hour_start = now.replace(minute=0, second=0, microsecond=0)
    hour_end = hour_start + timedelta(hours=1)

    # Determine limit
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    is_new = (now - account.created_at) < timedelta(days=PROBATION_DAYS) if account else True
    daily_limit = NEW_ACCOUNT_DAILY_LIMIT if is_new else WARMED_ACCOUNT_DAILY_LIMIT
    hourly_limit = int(daily_limit * HOURLY_LIMIT_RATIO)

    daily = await get_or_create_limit(
        db, account_id, OutboundLimitPeriod.daily, day_start, day_end, daily_limit,
        domain_id=domain_id, mailbox_id=mailbox_id,
    )
    hourly = await get_or_create_limit(
        db, account_id, OutboundLimitPeriod.hourly, hour_start, hour_end, hourly_limit,
        domain_id=domain_id, mailbox_id=mailbox_id,
    )

    daily.emails_sent += 1
    hourly.emails_sent += 1
    await db.commit()

    # Increment Redis per-minute counter
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    minute_key = f"send_count:{account_id}:{now.strftime('%Y%m%d%H%M')}"
    await redis.incr(minute_key)
    await redis.expire(minute_key, 120)  # 2-minute expiry
    await redis.close()
