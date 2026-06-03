"""Tests for snooze router."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _create_snooze(client: AsyncClient, customer_token: str, until: datetime, subject_contains: str | None = None):
    return await client.post(
        "/api/v1/snooze",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "subject_contains": subject_contains,
            "until": until.isoformat(),
        },
    )


async def test_snooze_crud(client: AsyncClient, test_customer, customer_token):
    until = datetime.now(timezone.utc) + timedelta(days=1)

    r = await _create_snooze(client, customer_token, until, subject_contains="vacation")
    assert r.status_code == 201
    data = r.json()
    assert data["subject_contains"] == "vacation"
    assert data["active"] is True
    assert data["sender_address"] is None
    snooze_id = data["id"]

    r = await client.get("/api/v1/snooze", headers={"Authorization": f"Bearer {customer_token}"})
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = await client.get(f"/api/v1/snooze/{snooze_id}", headers={"Authorization": f"Bearer {customer_token}"})
    assert r.status_code == 200
    assert r.json()["id"] == snooze_id

    r = await client.post(f"/api/v1/snooze/{snooze_id}/end", headers={"Authorization": f"Bearer {customer_token}"})
    assert r.status_code == 200
    assert r.json()["active"] is False

    r = await client.delete(f"/api/v1/snooze/{snooze_id}", headers={"Authorization": f"Bearer {customer_token}"})
    assert r.status_code == 200

    r = await client.get("/api/v1/snooze", headers={"Authorization": f"Bearer {customer_token}"})
    assert r.json() == []


async def test_snooze_active_filter(client: AsyncClient, customer_token):
    until = datetime.now(timezone.utc) + timedelta(days=1)
    await _create_snooze(client, customer_token, until, subject_contains="keep")
    ended = await _create_snooze(client, customer_token, until, subject_contains="end")
    ended_id = ended.json()["id"]
    await client.post(f"/api/v1/snooze/{ended_id}/end", headers={"Authorization": f"Bearer {customer_token}"})

    r = await client.get("/api/v1/snooze?active_only=true", headers={"Authorization": f"Bearer {customer_token}"})
    assert r.status_code == 200
    active = r.json()
    assert len(active) == 1
    assert active[0]["subject_contains"] == "keep"

    r = await client.get("/api/v1/snooze?active_only=false", headers={"Authorization": f"Bearer {customer_token}"})
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["subject_contains"] == "end"


async def test_snooze_cross_account_isolation(client: AsyncClient, customer_token, admin_token):
    until = datetime.now(timezone.utc) + timedelta(days=1)
    r = await _create_snooze(client, customer_token, until, subject_contains="mine")
    snooze_id = r.json()["id"]

    # Admin should not see customer's snooze
    r = await client.get("/api/v1/snooze", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.json() == []

    r = await client.get(f"/api/v1/snooze/{snooze_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 404

    r = await client.delete(f"/api/v1/snooze/{snooze_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 404

    r = await client.post(f"/api/v1/snooze/{snooze_id}/end", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 404

    # Ensure original still exists
    r = await client.get(f"/api/v1/snooze/{snooze_id}", headers={"Authorization": f"Bearer {customer_token}"})
    assert r.status_code == 200
