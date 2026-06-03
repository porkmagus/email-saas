import hashlib
import hmac
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.models import Account, OutboundLimit, OutboundLimitPeriod, AccountStatus, SendEvent, SendEventStatus

settings = get_settings()

# Provider per-minute send limit (default 25; adjust for your VPS provider)
NEW_ACCOUNT_DAILY_LIMIT = 25
WARMED_ACCOUNT_DAILY_LIMIT = 500
PROBATION_DAYS = 30
HOURLY_LIMIT_RATIO = 0.1


def _redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def _minute_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M")


def _hour_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H")


def _day_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


async def reserve_send_slot(
    account_id: uuid.UUID,
    domain_id: Optional[uuid.UUID] = None,
    mailbox_id: Optional[uuid.UUID] = None,
) -> tuple[bool, str]:
    """Atomically reserve send capacity using Redis. Returns (allowed, reason)."""
    redis = _redis()
    try:
        minute = _minute_key()
        hour = _hour_key()
        day = _day_key()

        # Keys
        global_min_key = f"send:global:min:{minute}"
        acct_hour_key = f"send:acct:{account_id}:hour:{hour}"
        acct_day_key = f"send:acct:{account_id}:day:{day}"
        domain_hour_key = f"send:domain:{domain_id}:hour:{hour}" if domain_id else None
        domain_day_key = f"send:domain:{domain_id}:day:{day}" if domain_id else None
        mailbox_hour_key = f"send:mailbox:{mailbox_id}:hour:{hour}" if mailbox_id else None
        mailbox_day_key = f"send:mailbox:{mailbox_id}:day:{day}" if mailbox_id else None

        all_keys = [
            global_min_key,
            acct_hour_key,
            acct_day_key,
        ]
        if domain_hour_key:
            all_keys.append(domain_hour_key)
        if domain_day_key:
            all_keys.append(domain_day_key)
        if mailbox_hour_key:
            all_keys.append(mailbox_hour_key)
        if mailbox_day_key:
            all_keys.append(mailbox_day_key)

        # Determine account limits
        # We can't easily query DB here without a session; use fixed limits for now
        daily_limit = WARMED_ACCOUNT_DAILY_LIMIT
        hourly_limit = int(daily_limit * HOURLY_LIMIT_RATIO)
        global_minute_limit = settings.provider_max_per_minute

        # Use pipeline to increment all counters atomically (best-effort)
        pipe = redis.pipeline()
        for key in all_keys:
            pipe.incr(key)
        results = await pipe.execute()

        # Set TTLs on first increment (when result == 1)
        ttl_pipe = redis.pipeline()
        for key, count in zip(all_keys, results):
            if count == 1:
                ttl_pipe.expire(key, 120 if "min" in key else 3600 if "hour" in key else 86400)
        await ttl_pipe.execute()

        # Check limits
        key_result = dict(zip(all_keys, results))
        if key_result[global_min_key] > global_minute_limit:
            return False, f"Global per-minute send limit reached ({global_minute_limit} emails/min)"
        if key_result[acct_hour_key] > hourly_limit:
            return False, f"Hourly send limit reached ({hourly_limit} emails/hour)"
        if key_result[acct_day_key] > daily_limit:
            return False, f"Daily send limit reached ({daily_limit} emails/day)"
        if domain_hour_key and key_result[domain_hour_key] > hourly_limit:
            return False, f"Domain hourly send limit reached ({hourly_limit} emails/hour)"
        if domain_day_key and key_result[domain_day_key] > daily_limit:
            return False, f"Domain daily send limit reached ({daily_limit} emails/day)"
        if mailbox_hour_key and key_result[mailbox_hour_key] > hourly_limit:
            return False, f"Mailbox hourly send limit reached ({hourly_limit} emails/hour)"
        if mailbox_day_key and key_result[mailbox_day_key] > daily_limit:
            return False, f"Mailbox daily send limit reached ({daily_limit} emails/day)"

        return True, ""
    finally:
        await redis.aclose()


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
    hourly = await get_or_create_limit(
        db, account_id, OutboundLimitPeriod.hourly, day_start, day_end, hourly_limit,
        domain_id=domain_id, mailbox_id=mailbox_id,
    )
    if hourly.emails_sent >= hourly.emails_allowed:
        return False, f"Hourly send limit reached ({hourly_limit} emails/hour)"

    # Check provider per-minute limit via Redis
    redis = _redis()
    try:
        minute_key = f"send_count:{account_id}:{now.strftime('%Y%m%d%H%M')}"
        current_minute = await redis.get(minute_key)
        if current_minute and int(current_minute) >= 25:
            return False, "Per-minute send limit reached (25 emails/min)"
    finally:
        await redis.aclose()

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
    redis = _redis()
    try:
        minute_key = f"send_count:{account_id}:{now.strftime('%Y%m%d%H%M')}"
        await redis.incr(minute_key)
        await redis.expire(minute_key, 120)  # 2-minute expiry
    finally:
        await redis.aclose()


def hash_recipient(email: str) -> str:
    settings = get_settings()
    secret = settings.api_key_secret or settings.secret_key
    return hmac.new(secret.encode(), email.lower().encode(), hashlib.sha256).hexdigest()


def recipient_domain(email: str) -> str | None:
    if "@" not in email:
        return None
    return email.rsplit("@", 1)[1].lower()


async def record_send_event(
    db: AsyncSession,
    account_id: uuid.UUID,
    recipients: list[str],
    domain_id: uuid.UUID | None = None,
    mailbox_id: uuid.UUID | None = None,
    status: SendEventStatus = SendEventStatus.sent,
    message_size: int | None = None,
    has_attachments: bool = False,
) -> None:
    """Create SendEvent rows for each recipient. Stores hashed recipient, not raw email."""
    for email in recipients:
        event = SendEvent(
            id=uuid.uuid4(),
            account_id=account_id,
            domain_id=domain_id,
            mailbox_id=mailbox_id,
            recipient_domain=recipient_domain(email),
            recipient_hash=hash_recipient(email),
            status=status,
            message_size=message_size,
            has_attachments=has_attachments,
        )
        db.add(event)
    await db.commit()
