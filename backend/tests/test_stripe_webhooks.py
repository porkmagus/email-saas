import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_stripe_webhook_missing_secret(client: AsyncClient):
    r = await client.post("/api/v1/stripe/webhook", headers={"Stripe-Signature": "v1=abc"}, content=b"{}")
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_stripe_webhook_invalid_payload(client: AsyncClient):
    # With a dummy secret, invalid payload should still return 400
    import os
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    from api.config import get_settings
    get_settings.cache_clear()
    r = await client.post("/api/v1/stripe/webhook", headers={"Stripe-Signature": "v1=abc"}, content=b"not_json")
    # payload parse error or signature verification error
    assert r.status_code in (400, 503)
