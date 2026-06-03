import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from api.models import SendEvent


@pytest.mark.asyncio
async def test_send_with_valid_mailbox(client: AsyncClient, customer_token, test_mailbox):
    with patch("api.services.stalwart_api.queue_message") as mock_queue:
        mock_queue.return_value = {"id": "fake-msg-id"}
        r = await client.post("/api/v1/send/send", headers={
            "Authorization": f"Bearer {customer_token}"
        }, json={
            "to": ["recipient@example.com"],
            "subject": "Hello",
            "body": "World",
            "from_mailbox_id": str(test_mailbox.id),
        })
        assert r.status_code == 200
        data = r.json()
        assert "queued" in data["message"].lower()
        mock_queue.assert_called_once()


@pytest.mark.asyncio
async def test_send_without_mailbox_fails(client: AsyncClient, customer_token):
    r = await client.post("/api/v1/send/send", headers={
        "Authorization": f"Bearer {customer_token}"
    }, json={
        "to": ["recipient@example.com"],
        "subject": "Hello",
        "body": "World",
    })
    assert r.status_code == 400
    assert "mailbox" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_send_with_other_account_mailbox_fails(
    client: AsyncClient, customer_token, db_session, test_admin
):
    from api.models import Domain, Mailbox, AccountStatus
    from api.deps import hash_password
    # Create a domain and mailbox for another account
    domain = Domain(
        id=uuid.uuid4(),
        account_id=test_admin.id,
        domain="other.com",
    )
    db_session.add(domain)
    await db_session.commit()
    await db_session.refresh(domain)
    mailbox = Mailbox(
        id=uuid.uuid4(),
        account_id=test_admin.id,
        domain_id=domain.id,
        local_part="test",
        password_hash=hash_password("Password123!"),
        status=AccountStatus.active,
    )
    db_session.add(mailbox)
    await db_session.commit()
    await db_session.refresh(mailbox)

    r = await client.post("/api/v1/send/send", headers={
        "Authorization": f"Bearer {customer_token}"
    }, json={
        "to": ["recipient@example.com"],
        "subject": "Hello",
        "body": "World",
        "from_mailbox_id": str(mailbox.id),
    })
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_send_event_rows_created(client: AsyncClient, customer_token, test_mailbox, db_session):
    with patch("api.services.stalwart_api.queue_message") as mock_queue:
        mock_queue.return_value = {"id": "fake-msg-id"}
        r = await client.post("/api/v1/send/send", headers={
            "Authorization": f"Bearer {customer_token}"
        }, json={
            "to": ["recipient@example.com", "another@example.org"],
            "subject": "Hello",
            "body": "World",
            "from_mailbox_id": str(test_mailbox.id),
        })
        assert r.status_code == 200

    from sqlalchemy import select
    result = await db_session.execute(
        select(SendEvent).where(SendEvent.account_id == test_mailbox.account_id)
    )
    events = result.scalars().all()
    assert len(events) == 2
    for ev in events:
        assert ev.recipient_hash is not None
        assert ev.recipient_hash != "recipient@example.com"
        assert ev.recipient_domain in ("example.com", "example.org")


@pytest.mark.asyncio
async def test_send_limit_blocks(client: AsyncClient, customer_token, test_mailbox):
    with patch("api.services.stalwart_api.queue_message") as mock_queue, \
         patch("api.routers.send.calculate_abuse_score") as mock_score, \
         patch("api.routers.send.enforce_abuse_action") as mock_enforce:
        mock_score.return_value = None
        mock_enforce.return_value = None
        mock_queue.return_value = {"id": "fake-msg-id"}
        # Exhaust per-minute limit (25)
        for i in range(26):
            r = await client.post("/api/v1/send/send", headers={
                "Authorization": f"Bearer {customer_token}"
            }, json={
                "to": [f"recipient{i}@example.com"],
                "subject": "Hello",
                "body": "World",
                "from_mailbox_id": str(test_mailbox.id),
            })
        # The last one should be blocked by per-minute limit
        assert r.status_code == 429
        assert "limit" in r.json()["detail"].lower()
