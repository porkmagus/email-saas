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
