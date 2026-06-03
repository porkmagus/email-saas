"""Tests for the new routers (app_passwords, files, login_logs, notes, passkeys, sessions)."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_app_passwords_crud(client: AsyncClient, test_customer, customer_token):
    headers = {"Authorization": f"Bearer {customer_token}"}

    # Create
    res = await client.post(
        "/api/v1/app-passwords",
        headers=headers,
        json={"name": "Test App PW", "permissions": ["mail"]},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Test App PW"
    assert data["permissions"] == ["mail"]
    assert data["account_id"] == str(test_customer.id)
    ap_id = data["id"]

    # List
    res = await client.get("/api/v1/app-passwords", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1

    # Update
    res = await client.patch(
        f"/api/v1/app-passwords/{ap_id}",
        headers=headers,
        json={"name": "Renamed"},
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Renamed"

    # Delete
    res = await client.delete(f"/api/v1/app-passwords/{ap_id}", headers=headers)
    assert res.status_code == 200
    res = await client.get("/api/v1/app-passwords", headers=headers)
    assert len(res.json()) == 0


@pytest.mark.asyncio
async def test_files_crud(client: AsyncClient, test_customer, customer_token):
    headers = {"Authorization": f"Bearer {customer_token}"}

    res = await client.post(
        "/api/v1/files",
        headers=headers,
        json={
            "name": "doc.txt",
            "path": "/docs/doc.txt",
            "size_bytes": 42,
            "mime_type": "text/plain",
            "folder": "docs",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "doc.txt"
    assert data["folder"] == "docs"
    file_id = data["id"]

    # List
    res = await client.get("/api/v1/files", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1

    # Get by ID
    res = await client.get(f"/api/v1/files/{file_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == file_id

    # Update
    res = await client.patch(
        f"/api/v1/files/{file_id}",
        headers=headers,
        json={"name": "renamed.txt"},
    )
    assert res.status_code == 200
    assert res.json()["name"] == "renamed.txt"

    # Delete
    res = await client.delete(f"/api/v1/files/{file_id}", headers=headers)
    assert res.status_code == 200
    res = await client.get("/api/v1/files", headers=headers)
    assert len(res.json()) == 0


@pytest.mark.asyncio
async def test_notes_crud(client: AsyncClient, test_customer, customer_token):
    headers = {"Authorization": f"Bearer {customer_token}"}

    res = await client.post(
        "/api/v1/notes",
        headers=headers,
        json={"title": "My Note", "content": "Some content"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "My Note"
    note_id = data["id"]

    res = await client.get("/api/v1/notes", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1

    res = await client.get(f"/api/v1/notes/{note_id}", headers=headers)
    assert res.status_code == 200

    res = await client.patch(
        f"/api/v1/notes/{note_id}",
        headers=headers,
        json={"content": "Updated content"},
    )
    assert res.status_code == 200
    assert res.json()["content"] == "Updated content"

    res = await client.delete(f"/api/v1/notes/{note_id}", headers=headers)
    assert res.status_code == 200
    res = await client.get("/api/v1/notes", headers=headers)
    assert len(res.json()) == 0


@pytest.mark.asyncio
async def test_login_logs_list(client: AsyncClient, test_customer, customer_token, db_session):
    from api.models import LoginLog
    from datetime import datetime, timezone

    log = LoginLog(
        account_id=test_customer.id,
        ip_address="192.168.1.1",
        user_agent="pytest",
        success=True,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(log)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {customer_token}"}
    res = await client.get("/api/v1/login-logs", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["ip_address"] == "192.168.1.1"


@pytest.mark.asyncio
async def test_passkeys_crud(client: AsyncClient, test_customer, customer_token):
    headers = {"Authorization": f"Bearer {customer_token}"}

    res = await client.post(
        "/api/v1/passkeys",
        headers=headers,
        json={"name": "YubiKey"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "YubiKey"
    pk_id = data["id"]

    res = await client.get("/api/v1/passkeys", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1

    res = await client.patch(
        f"/api/v1/passkeys/{pk_id}",
        headers=headers,
        json={"name": "Renamed Key"},
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Renamed Key"

    res = await client.delete(f"/api/v1/passkeys/{pk_id}", headers=headers)
    assert res.status_code == 200
    res = await client.get("/api/v1/passkeys", headers=headers)
    assert len(res.json()) == 0


@pytest.mark.asyncio
async def test_sessions_list_and_delete(client: AsyncClient, test_customer, customer_token, db_session):
    from api.models import Session
    from datetime import datetime, timezone

    session = Session(
        account_id=test_customer.id,
        token_jti="deadbeef",
        ip_address="192.168.1.1",
        user_agent="pytest",
        created_at=datetime.now(timezone.utc),
        last_active_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc),
    )
    db_session.add(session)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {customer_token}"}
    res = await client.get("/api/v1/sessions", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    sess_id = data[0]["id"]

    res = await client.delete(f"/api/v1/sessions/{sess_id}", headers=headers)
    assert res.status_code == 200

    res = await client.get("/api/v1/sessions", headers=headers)
    assert len(res.json()) == 0


@pytest.mark.asyncio
async def test_sessions_delete_all(client: AsyncClient, test_customer, customer_token, db_session):
    from api.models import Session
    from datetime import datetime, timezone

    for i in range(3):
        session = Session(
            account_id=test_customer.id,
            token_jti=f"hash{i}",
            ip_address="192.168.1.1",
            user_agent="pytest",
            created_at=datetime.now(timezone.utc),
            last_active_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc),
        )
        db_session.add(session)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {customer_token}"}
    res = await client.delete("/api/v1/sessions", headers=headers)
    assert res.status_code == 200
    assert res.json()["message"] == "Revoked 3 sessions"

    res = await client.get("/api/v1/sessions", headers=headers)
    assert len(res.json()) == 0


@pytest.mark.asyncio
async def test_cross_account_isolation_app_passwords(client: AsyncClient, test_customer, test_admin, customer_token, admin_token):
    # Create app password as customer
    headers_c = {"Authorization": f"Bearer {customer_token}"}
    res = await client.post(
        "/api/v1/app-passwords",
        headers=headers_c,
        json={"name": "Customer PW", "permissions": []},
    )
    ap_id = res.json()["id"]

    # Admin should not see customer's app password
    headers_a = {"Authorization": f"Bearer {admin_token}"}
    res = await client.get("/api/v1/app-passwords", headers=headers_a)
    assert res.status_code == 200
    assert len(res.json()) == 0

    # Admin should not be able to delete customer's app password
    res = await client.delete(f"/api/v1/app-passwords/{ap_id}", headers=headers_a)
    assert res.status_code == 404
