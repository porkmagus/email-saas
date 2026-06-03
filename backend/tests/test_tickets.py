import pytest
from httpx import AsyncClient

from api.models import TicketStatus, TicketPriority


@pytest.mark.asyncio
async def test_customer_create_ticket(client: AsyncClient, customer_token):
    r = await client.post("/api/v1/tickets", headers={"Authorization": f"Bearer {customer_token}"}, json={
        "title": "Help me",
        "body": "I need help setting up my domain",
        "category": "setup",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Help me"
    assert data["status"] == "open"


@pytest.mark.asyncio
async def test_customer_list_own_tickets(client: AsyncClient, customer_token, test_ticket):
    r = await client.get("/api/v1/tickets", headers={"Authorization": f"Bearer {customer_token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_customer_get_ticket(client: AsyncClient, customer_token, test_ticket):
    r = await client.get(f"/api/v1/tickets/{test_ticket.id}", headers={"Authorization": f"Bearer {customer_token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == str(test_ticket.id)


@pytest.mark.asyncio
async def test_customer_add_comment(client: AsyncClient, customer_token, test_ticket):
    r = await client.post(f"/api/v1/tickets/{test_ticket.id}/comments", headers={
        "Authorization": f"Bearer {customer_token}"
    }, json={"body": "Follow-up question", "is_internal": False})
    assert r.status_code == 200
    data = r.json()
    assert data["body"] == "Follow-up question"


@pytest.mark.asyncio
async def test_customer_cannot_create_internal_comment(client: AsyncClient, customer_token, test_ticket):
    r = await client.post(f"/api/v1/tickets/{test_ticket.id}/comments", headers={
        "Authorization": f"Bearer {customer_token}"
    }, json={"body": "Internal", "is_internal": True})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_customer_cannot_see_internal_comments(client: AsyncClient, customer_token, test_ticket, db_session):
    from api.models import TicketComment
    import uuid
    comment = TicketComment(
        id=uuid.uuid4(),
        ticket_id=test_ticket.id,
        author_id=None,
        is_internal=True,
        body="Secret staff note",
    )
    db_session.add(comment)
    await db_session.commit()

    r = await client.get(f"/api/v1/tickets/{test_ticket.id}", headers={
        "Authorization": f"Bearer {customer_token}"
    })
    assert r.status_code == 200
    data = r.json()
    bodies = [c["body"] for c in data.get("comments", [])]
    assert "Secret staff note" not in bodies


@pytest.mark.asyncio
async def test_staff_sees_internal_comments(client: AsyncClient, admin_token, test_ticket, db_session):
    from api.models import TicketComment
    import uuid
    comment = TicketComment(
        id=uuid.uuid4(),
        ticket_id=test_ticket.id,
        author_id=None,
        is_internal=True,
        body="Secret staff note",
    )
    db_session.add(comment)
    await db_session.commit()

    r = await client.get(f"/api/v1/tickets/{test_ticket.id}", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert r.status_code == 200
    data = r.json()
    bodies = [c["body"] for c in data.get("comments", [])]
    assert "Secret staff note" in bodies


@pytest.mark.asyncio
async def test_admin_update_ticket(client: AsyncClient, admin_token, test_ticket):
    r = await client.patch(f"/api/v1/tickets/{test_ticket.id}", headers={
        "Authorization": f"Bearer {admin_token}"
    }, json={"status": "resolved", "priority": "high", "assigned_to": "admin@example.com"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "resolved"
    assert data["priority"] == "high"
    assert data["assigned_to"] == "admin@example.com"


@pytest.mark.asyncio
async def test_customer_can_close_ticket(client: AsyncClient, customer_token, test_ticket):
    r = await client.patch(f"/api/v1/tickets/{test_ticket.id}", headers={
        "Authorization": f"Bearer {customer_token}"
    }, json={"status": "closed"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "closed"


@pytest.mark.asyncio
async def test_customer_cannot_change_priority(client: AsyncClient, customer_token, test_ticket):
    r = await client.patch(f"/api/v1/tickets/{test_ticket.id}", headers={
        "Authorization": f"Bearer {customer_token}"
    }, json={"priority": "critical"})
    assert r.status_code == 403
