import pytest
from httpx import AsyncClient

from api.models import Account, AccountRole
from api.deps import verify_password


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    r = await client.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "password": "Password123!",
        "display_name": "New User",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "customer"


@pytest.mark.asyncio
async def test_login(client: AsyncClient, test_customer):
    r = await client.post("/api/v1/auth/login", json={
        "email": "customer@example.com",
        "password": "Password123!",
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_customer):
    r = await client.post("/api/v1/auth/login", json={
        "email": "customer@example.com",
        "password": "wrongpassword",
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me(client: AsyncClient, customer_token):
    r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {customer_token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "customer@example.com"


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient, test_customer, customer_token):
    r = await client.post("/api/v1/auth/change-password", headers={
        "Authorization": f"Bearer {customer_token}"
    }, json={
        "old_password": "Password123!",
        "new_password": "NewPassword123!",
    })
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, customer_token):
    r = await client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {customer_token}"})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_totp_flow(client: AsyncClient, customer_token):
    # Setup
    r = await client.post("/api/v1/auth/totp/setup", headers={"Authorization": f"Bearer {customer_token}"})
    assert r.status_code == 200
    secret = r.json()["secret"]

    import pyotp
    code = pyotp.TOTP(secret).now()

    r = await client.post("/api/v1/auth/totp/verify", headers={
        "Authorization": f"Bearer {customer_token}"
    }, json={"code": code})
    assert r.status_code == 200

    # Disable
    r = await client.post("/api/v1/auth/totp/disable", headers={
        "Authorization": f"Bearer {customer_token}"
    }, json={"code": code})
    assert r.status_code == 200
