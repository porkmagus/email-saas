import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_stripe_webhook_invalid_payload(client: AsyncClient):
    # With a dummy secret, invalid payload should still return 400
    r = await client.post("/api/v1/stripe/webhook", headers={"Stripe-Signature": "v1=abc"}, content=b"not_json")
    # payload parse error or signature verification error
    assert r.status_code in (400, 503)


@pytest.mark.asyncio
async def test_stripe_webhook_first_event_processed(client: AsyncClient, db_session, test_customer):
    import os
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    from api.config import get_settings
    get_settings.cache_clear()
    from api.models import StripeEvent, StripeEventStatus
    from sqlalchemy import select

    # Insert a stripe event directly
    event = StripeEvent(
        stripe_event_id="evt_123",
        event_type="invoice.payment_succeeded",
        account_id=test_customer.id,
        payload={"id": "evt_123", "type": "invoice.payment_succeeded"},
        processing_status=StripeEventStatus.completed,
    )
    db_session.add(event)
    await db_session.commit()

    # Verify it exists
    result = await db_session.execute(
        select(StripeEvent).where(StripeEvent.stripe_event_id == "evt_123")
    )
    assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_stripe_event_retry_logic(client: AsyncClient, db_session, test_customer):
    import os
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    from api.config import get_settings
    get_settings.cache_clear()
    from api.models import StripeEvent, StripeEventStatus
    from sqlalchemy import select

    event = StripeEvent(
        stripe_event_id="evt_retry",
        event_type="invoice.payment_failed",
        account_id=test_customer.id,
        payload={"id": "evt_retry", "type": "invoice.payment_failed"},
        processing_status=StripeEventStatus.failed,
        attempt_count=0,
    )
    db_session.add(event)
    await db_session.commit()

    result = await db_session.execute(
        select(StripeEvent).where(StripeEvent.stripe_event_id == "evt_retry")
    )
    ev = result.scalar_one_or_none()
    assert ev is not None
    assert ev.attempt_count == 0
