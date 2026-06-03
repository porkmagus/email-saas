import asyncio
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from api.main import app
from api.db import Base, get_db
from api.models import Account, AccountRole, AccountStatus, Domain, Mailbox, Ticket, TicketStatus, TicketPriority, TicketCategory
from api.deps import hash_password, create_access_token, get_redis
from api.services import send_throttle as _st

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Simple fake Redis for tests
class FakeRedis:
    def __init__(self):
        self._data = {}
    async def get(self, key):
        return self._data.get(key)
    async def setex(self, key, seconds, value):
        self._data[key] = value
    async def delete(self, key):
        self._data.pop(key, None)
    async def ping(self):
        return True
    async def incr(self, key):
        val = self._data.get(key, 0)
        if not isinstance(val, int):
            val = int(val)
        val += 1
        self._data[key] = val
        return val
    async def expire(self, key, seconds):
        return True
    def pipeline(self):
        return FakePipeline(self)
    async def aclose(self):
        pass
    def flushall(self):
        self._data.clear()

class FakePipeline:
    def __init__(self, redis):
        self._redis = redis
        self._commands = []
    def incr(self, key):
        self._commands.append(("incr", key))
        return self
    def expire(self, key, seconds):
        self._commands.append(("expire", key, seconds))
        return self
    async def execute(self):
        results = []
        for cmd in self._commands:
            if cmd[0] == "incr":
                results.append(await self._redis.incr(cmd[1]))
            elif cmd[0] == "expire":
                results.append(await self._redis.expire(cmd[1], cmd[2]))
        self._commands = []
        return results

async def override_get_redis():
    return FakeRedis()

# Patch send_throttle to use a shared FakeRedis instance in tests
_fake_redis_instance = FakeRedis()
def _fake_redis():
    return _fake_redis_instance
_st._redis = _fake_redis


engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
TestSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False, autocommit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_redis] = override_get_redis


@pytest_asyncio.fixture(scope="function")
async def _db_engine():
    _fake_redis_instance.flushall()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(_db_engine):
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(_db_engine):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_customer(db_session):
    account = Account(
        id=uuid.uuid4(),
        email="customer@example.com",
        password_hash=hash_password("Password123!"),
        role=AccountRole.customer,
        status=AccountStatus.active,
        display_name="Test Customer",
    )
    db_session.add(account)
    await db_session.commit()
    return account


@pytest_asyncio.fixture
async def test_admin(db_session):
    account = Account(
        id=uuid.uuid4(),
        email="admin@example.com",
        password_hash=hash_password("Password123!"),
        role=AccountRole.admin,
        status=AccountStatus.active,
        totp_enabled=True,
        totp_secret="BASE32SECRET3232",
        display_name="Test Admin",
    )
    db_session.add(account)
    await db_session.commit()
    return account


@pytest_asyncio.fixture
async def test_superadmin(db_session):
    account = Account(
        id=uuid.uuid4(),
        email="superadmin@example.com",
        password_hash=hash_password("Password123!"),
        role=AccountRole.superadmin,
        status=AccountStatus.active,
        totp_enabled=True,
        totp_secret="BASE32SECRET3232",
        display_name="Test Superadmin",
    )
    db_session.add(account)
    await db_session.commit()
    return account


@pytest_asyncio.fixture
async def customer_token(test_customer):
    return create_access_token({"sub": str(test_customer.id)})


@pytest_asyncio.fixture
async def admin_token(test_admin):
    return create_access_token({"sub": str(test_admin.id)})


@pytest_asyncio.fixture
async def superadmin_token(test_superadmin):
    return create_access_token({"sub": str(test_superadmin.id)})


@pytest_asyncio.fixture
async def test_domain(db_session, test_customer):
    domain = Domain(
        id=uuid.uuid4(),
        account_id=test_customer.id,
        domain="example.com",
    )
    db_session.add(domain)
    await db_session.commit()
    return domain


@pytest_asyncio.fixture
async def test_mailbox(db_session, test_customer, test_domain):
    mailbox = Mailbox(
        id=uuid.uuid4(),
        account_id=test_customer.id,
        domain_id=test_domain.id,
        local_part="test",
        password_hash=hash_password("Password123!"),
        status=AccountStatus.active,
    )
    db_session.add(mailbox)
    await db_session.commit()
    return mailbox


@pytest_asyncio.fixture
async def test_ticket(db_session, test_customer):
    ticket = Ticket(
        id=uuid.uuid4(),
        account_id=test_customer.id,
        title="Test Ticket",
        status=TicketStatus.open,
        priority=TicketPriority.normal,
        category=TicketCategory.billing,
    )
    db_session.add(ticket)
    await db_session.commit()
    return ticket
