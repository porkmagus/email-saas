import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_api_key(client: AsyncClient, customer_token):
    r = await client.post("/api/v1/api-keys", headers={
        "Authorization": f"Bearer {customer_token}"
    }, json={
        "name": "My App",
        "permissions": ["smtp", "api_read"],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "My App"
    assert "secret" in data
    assert data["prefix"].startswith("esk_")


@pytest.mark.asyncio
async def test_list_api_keys(client: AsyncClient, customer_token):
    r = await client.get("/api/v1/api-keys", headers={
        "Authorization": f"Bearer {customer_token}"
    })
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_revoke_api_key(client: AsyncClient, customer_token):
    r = await client.post("/api/v1/api-keys", headers={
        "Authorization": f"Bearer {customer_token}"
    }, json={"name": "To Revoke", "permissions": ["smtp"]})
    assert r.status_code == 200
    key_id = r.json()["id"]

    r = await client.delete(f"/api/v1/api-keys/{key_id}", headers={
        "Authorization": f"Bearer {customer_token}"
    })
    assert r.status_code == 200

    r = await client.get("/api/v1/api-keys", headers={
        "Authorization": f"Bearer {customer_token}"
    })
    assert r.status_code == 200
    for k in r.json():
        assert k["id"] != key_id or k["revoked_at"] is not None


@pytest.mark.asyncio
async def test_api_key_authentication(client: AsyncClient, customer_token):
    # Create a key
    r = await client.post("/api/v1/api-keys", headers={
        "Authorization": f"Bearer {customer_token}"
    }, json={"name": "Auth Test", "permissions": ["api_read"]})
    assert r.status_code == 200
    key_data = r.json()
    secret = key_data["secret"]
    key_id = key_data["id"]

    # Use it to access /me
    r = await client.get("/api/v1/auth/me", headers={"X-API-Key": secret})
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "customer@example.com"

    # Revoke it
    r = await client.delete(f"/api/v1/api-keys/{key_id}", headers={
        "Authorization": f"Bearer {customer_token}"
    })
    assert r.status_code == 200

    # Should fail after revoke
    r = await client.get("/api/v1/auth/me", headers={"X-API-Key": secret})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_malformed_api_key_fails(client: AsyncClient):
    r = await client.get("/api/v1/auth/me", headers={"X-API-Key": "not_a_valid_key"})
    assert r.status_code == 401
