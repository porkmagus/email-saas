import pytest
from httpx import AsyncClient

from api.models import Account, AccountRole, AccountStatus


@pytest.mark.asyncio
async def test_admin_list_accounts(client: AsyncClient, admin_token, test_customer):
    r = await client.get("/api/v1/admin/accounts", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_admin_get_account(client: AsyncClient, admin_token, test_customer):
    r = await client.get(f"/api/v1/admin/accounts/{test_customer.id}", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == test_customer.email


@pytest.mark.asyncio
async def test_admin_impersonate(client: AsyncClient, superadmin_token, test_customer):
    r = await client.post(f"/api/v1/admin/accounts/{test_customer.id}/impersonate", json={
        "reason": "Testing impersonation for customer support"
    }, headers={
        "Authorization": f"Bearer {superadmin_token}"
    })
    assert r.status_code == 200
    data = r.json()
    assert "token" in data
    assert "expires_in" in data


@pytest.mark.asyncio
async def test_admin_impersonate_requires_reason(client: AsyncClient, superadmin_token, test_customer):
    r = await client.post(f"/api/v1/admin/accounts/{test_customer.id}/impersonate", json={
        "reason": ""
    }, headers={
        "Authorization": f"Bearer {superadmin_token}"
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_admin_suspend_unsuspend(client: AsyncClient, admin_token, test_customer):
    r = await client.post(f"/api/v1/admin/accounts/{test_customer.id}/suspend", headers={
        "Authorization": f"Bearer {admin_token}"
    }, json={"reason": "Test suspension"})
    assert r.status_code == 200

    r = await client.post(f"/api/v1/admin/accounts/{test_customer.id}/unsuspend", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_admin_stats(client: AsyncClient, admin_token):
    r = await client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    data = r.json()
    assert "total_accounts" in data


@pytest.mark.asyncio
async def test_customer_cannot_access_admin(client: AsyncClient, customer_token):
    r = await client.get("/api/v1/admin/accounts", headers={"Authorization": f"Bearer {customer_token}"})
    assert r.status_code == 403
