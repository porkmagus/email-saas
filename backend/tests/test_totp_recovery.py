import pytest
from httpx import AsyncClient

from api.deps import create_access_token


@pytest.mark.asyncio
async def test_totp_recovery_login(client: AsyncClient, test_customer, customer_token):
    # Enable TOTP first
    r = await client.post("/api/v1/auth/totp/setup", headers={
        "Authorization": f"Bearer {customer_token}"
    })
    assert r.status_code == 200
    secret = r.json()["secret"]

    import pyotp
    code = pyotp.TOTP(secret).now()
    r = await client.post("/api/v1/auth/totp/verify", headers={
        "Authorization": f"Bearer {customer_token}"
    }, json={"code": code})
    assert r.status_code == 200
    recovery_codes = r.json()["recovery_codes"]
    assert len(recovery_codes) == 10

    # Use recovery code
    r = await client.post("/api/v1/auth/totp/recovery", json={
        "email": "customer@example.com",
        "password": "Password123!",
        "recovery_code": recovery_codes[0],
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["account"]["email"] == "customer@example.com"

    # Token should work on /me
    r = await client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {data['access_token']}"
    })
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_totp_recovery_reused_code_fails(client: AsyncClient, test_customer, customer_token):
    # Enable TOTP
    r = await client.post("/api/v1/auth/totp/setup", headers={
        "Authorization": f"Bearer {customer_token}"
    })
    assert r.status_code == 200
    secret = r.json()["secret"]

    import pyotp
    code = pyotp.TOTP(secret).now()
    r = await client.post("/api/v1/auth/totp/verify", headers={
        "Authorization": f"Bearer {customer_token}"
    }, json={"code": code})
    assert r.status_code == 200
    recovery_codes = r.json()["recovery_codes"]

    # Use recovery code
    r = await client.post("/api/v1/auth/totp/recovery", json={
        "email": "customer@example.com",
        "password": "Password123!",
        "recovery_code": recovery_codes[0],
    })
    assert r.status_code == 200

    # Reuse same code
    r = await client.post("/api/v1/auth/totp/recovery", json={
        "email": "customer@example.com",
        "password": "Password123!",
        "recovery_code": recovery_codes[0],
    })
    assert r.status_code == 400
    assert "invalid" in r.json()["detail"].lower()
