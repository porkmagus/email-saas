import pytest
from httpx import AsyncClient

from api.models import Account, AccountRole, AccountStatus, Domain, Mailbox
import uuid


@pytest.mark.asyncio
async def test_customer_cannot_access_other_domains(client: AsyncClient, db_session, customer_token):
    # Create another account with a domain
    other = Account(
        id=uuid.uuid4(),
        email="other@example.com",
        password_hash="hash",
        role=AccountRole.customer,
        status=AccountStatus.active,
    )
    db_session.add(other)
    await db_session.commit()
    domain = Domain(
        id=uuid.uuid4(),
        account_id=other.id,
        domain="other-domain.com",
    )
    db_session.add(domain)
    await db_session.commit()

    r = await client.get(f"/api/v1/domains/{domain.id}", headers={
        "Authorization": f"Bearer {customer_token}"
    })
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_customer_cannot_access_other_mailboxes(client: AsyncClient, db_session, customer_token):
    other = Account(
        id=uuid.uuid4(),
        email="other2@example.com",
        password_hash="hash",
        role=AccountRole.customer,
        status=AccountStatus.active,
    )
    db_session.add(other)
    await db_session.commit()
    domain = Domain(
        id=uuid.uuid4(),
        account_id=other.id,
        domain="other2-domain.com",
    )
    db_session.add(domain)
    await db_session.commit()
    mailbox = Mailbox(
        id=uuid.uuid4(),
        account_id=other.id,
        domain_id=domain.id,
        local_part="test",
        password_hash="hash",
        status=AccountStatus.active,
    )
    db_session.add(mailbox)
    await db_session.commit()

    r = await client.get(f"/api/v1/mailboxes/{mailbox.id}", headers={
        "Authorization": f"Bearer {customer_token}"
    })
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_customer_cannot_access_other_tickets(client: AsyncClient, db_session, customer_token):
    from api.models import Ticket, TicketStatus, TicketPriority, TicketCategory
    other = Account(
        id=uuid.uuid4(),
        email="other3@example.com",
        password_hash="hash",
        role=AccountRole.customer,
        status=AccountStatus.active,
    )
    db_session.add(other)
    await db_session.commit()
    ticket = Ticket(
        id=uuid.uuid4(),
        account_id=other.id,
        title="Other ticket",
        status=TicketStatus.open,
        priority=TicketPriority.normal,
        category=TicketCategory.billing,
    )
    db_session.add(ticket)
    await db_session.commit()

    r = await client.get(f"/api/v1/tickets/{ticket.id}", headers={
        "Authorization": f"Bearer {customer_token}"
    })
    assert r.status_code == 403
