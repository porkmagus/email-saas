import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.db import get_db
from api.deps import get_current_active_account, get_redis
from api.models import Account, AccountStatus, Subscription, SubscriptionStatus, ProvisioningJob, JobType, StripeEvent, StripeEventStatus
from api.schemas import StripeCheckoutOut, StripePortalOut, MessageOut
from api.services.audit import audit_from_request

import stripe
from redis.asyncio import Redis

router = APIRouter()
settings = get_settings()
limiter = Limiter(key_func=get_remote_address)

if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key

STALE_PROCESSING_THRESHOLD = timedelta(minutes=5)
MAX_RETRY_ATTEMPTS = 3


@router.post("/checkout", response_model=StripeCheckoutOut)
@limiter.limit("10/minute")
async def create_checkout(
    request: Request,
    account: Account = Depends(get_current_active_account),
):
    if not settings.stripe_secret_key or not settings.stripe_price_id:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    try:
        session = stripe.checkout.Session.create(
            customer=account.stripe_customer_id or None,
            customer_email=None if account.stripe_customer_id else account.email,
            payment_method_types=["card"],
            line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{settings.frontend_url}/billing?success=1",
            cancel_url=f"{settings.frontend_url}/billing?canceled=1",
            metadata={"account_id": str(account.id)},
        )
        if not account.stripe_customer_id and session.customer:
            account.stripe_customer_id = session.customer
            # commit handled later or via webhook
        return {"url": session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/portal", response_model=StripePortalOut)
@limiter.limit("10/minute")
async def create_portal(
    request: Request,
    account: Account = Depends(get_current_active_account),
):
    if not settings.stripe_secret_key or not account.stripe_customer_id:
        raise HTTPException(status_code=503, detail="Stripe not configured or no customer")
    try:
        session = stripe.billing_portal.Session.create(
            customer=account.stripe_customer_id,
            return_url=f"{settings.frontend_url}/billing",
        )
        return {"url": session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook", response_model=MessageOut)
@limiter.limit("100/minute")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
):
    payload = await request.body()
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook secret not configured")
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    stripe_event_id = event["id"]
    event_type = event["type"]
    data_object = event["data"]["object"]

    # Idempotency check with state-aware handling
    existing_result = await db.execute(
        select(StripeEvent).where(StripeEvent.stripe_event_id == stripe_event_id)
    )
    existing_event = existing_result.scalar_one_or_none()

    if existing_event:
        now = datetime.now(timezone.utc)
        
        if existing_event.processing_status == StripeEventStatus.completed:
            return {"message": "Event already processed"}
        
        elif existing_event.processing_status == StripeEventStatus.processing:
            # Check if stale
            stale_threshold = now - STALE_PROCESSING_THRESHOLD
            if existing_event.received_at < stale_threshold:
                existing_event.processing_status = StripeEventStatus.retrying
                existing_event.attempt_count += 1
                existing_event.last_attempt_at = now
                await db.commit()
            else:
                return {"message": "Event processing in progress"}
        
        elif existing_event.processing_status == StripeEventStatus.failed:
            if existing_event.attempt_count >= MAX_RETRY_ATTEMPTS:
                return {"message": "Event failed after max retries"}
            existing_event.processing_status = StripeEventStatus.retrying
            existing_event.attempt_count += 1
            existing_event.last_attempt_at = now
            await db.commit()
        
        elif existing_event.processing_status in (StripeEventStatus.retrying, StripeEventStatus.received):
            existing_event.processing_status = StripeEventStatus.processing
            existing_event.attempt_count += 1
            existing_event.last_attempt_at = now
            await db.commit()
        
        else:
            return {"message": "Event processing in progress"}
        
        stripe_event = existing_event
    else:
        # Insert with race protection
        try:
            stripe_event = StripeEvent(
                id=uuid.uuid4(),
                stripe_event_id=stripe_event_id,
                event_type=event_type,
                payload=dict(event),
                processing_status=StripeEventStatus.processing,
                attempt_count=1,
                last_attempt_at=datetime.now(timezone.utc),
            )
            db.add(stripe_event)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            return {"message": "Event processing in progress"}

    try:
        if event_type == "checkout.session.completed":
            account_id = data_object.get("metadata", {}).get("account_id")
            if account_id:
                result = await db.execute(select(Account).where(Account.id == uuid.UUID(account_id)))
                account = result.scalar_one_or_none()
                if account:
                    account.status = AccountStatus.active
                    if not account.stripe_customer_id and data_object.get("customer"):
                        account.stripe_customer_id = data_object["customer"]
                    sub_id = data_object.get("subscription")
                    if sub_id:
                        existing_sub = await db.execute(
                            select(Subscription).where(Subscription.stripe_subscription_id == sub_id)
                        )
                        if not existing_sub.scalar_one_or_none():
                            sub = Subscription(
                                id=uuid.uuid4(),
                                account_id=account.id,
                                stripe_subscription_id=sub_id,
                                status=SubscriptionStatus.active,
                                plan=account.plan,
                            )
                            db.add(sub)
                    job = ProvisioningJob(
                        id=uuid.uuid4(),
                        account_id=account.id,
                        type=JobType.provision_account,
                        payload={"stripe_event_id": stripe_event_id},
                        status="pending",
                    )
                    db.add(job)
                    await db.commit()

        elif event_type == "invoice.paid":
            sub_id = data_object.get("subscription")
            if sub_id:
                result = await db.execute(
                    select(Subscription).where(Subscription.stripe_subscription_id == sub_id)
                )
                sub = result.scalar_one_or_none()
                if sub:
                    sub.status = SubscriptionStatus.active
                    sub.current_period_end = datetime.fromtimestamp(
                        data_object.get("period_end", 0), tz=timezone.utc
                    )
                    await db.commit()

        elif event_type == "invoice.payment_failed":
            sub_id = data_object.get("subscription")
            if sub_id:
                result = await db.execute(
                    select(Subscription).where(Subscription.stripe_subscription_id == sub_id)
                )
                sub = result.scalar_one_or_none()
                if sub:
                    sub.status = SubscriptionStatus.past_due
                    await db.commit()
            customer_id = data_object.get("customer")
            if customer_id:
                result = await db.execute(
                    select(Account).where(Account.stripe_customer_id == customer_id)
                )
                account = result.scalar_one_or_none()
                if account:
                    account.status = AccountStatus.suspended
                    job = ProvisioningJob(
                        id=uuid.uuid4(),
                        account_id=account.id,
                        type=JobType.suspend_account,
                        payload={"reason": "invoice.payment_failed", "stripe_event_id": stripe_event_id},
                        status="pending",
                    )
                    db.add(job)
                    await db.commit()

        elif event_type == "customer.subscription.deleted":
            sub_id = data_object.get("id")
            result = await db.execute(
                select(Subscription).where(Subscription.stripe_subscription_id == sub_id)
            )
            sub = result.scalar_one_or_none()
            if sub:
                sub.status = SubscriptionStatus.cancelled
                sub.cancel_at_period_end = True
                result = await db.execute(select(Account).where(Account.id == sub.account_id))
                account = result.scalar_one_or_none()
                if account:
                    account.status = AccountStatus.cancelled
                    job = ProvisioningJob(
                        id=uuid.uuid4(),
                        account_id=account.id,
                        type=JobType.delete_account,
                        payload={"reason": "subscription.cancelled", "grace_days": 30},
                        status="pending",
                    )
                    db.add(job)
                await db.commit()

        # Mark as completed
        stripe_event.processing_status = StripeEventStatus.completed
        stripe_event.processed_at = datetime.now(timezone.utc)
        await db.commit()

    except Exception as e:
        stripe_event.processing_status = StripeEventStatus.failed
        stripe_event.error_message = str(e)
        stripe_event.attempt_count += 1
        stripe_event.last_attempt_at = datetime.now(timezone.utc)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {e}")

    await audit_from_request(
        request,
        f"stripe_webhook:{event_type}",
        "stripe_event",
        data_object.get("id"),
        actor_type="system",
        metadata={"event_type": event_type, "stripe_event_id": stripe_event_id, "attempt": stripe_event.attempt_count},
    )
    return {"message": "Webhook processed"}
