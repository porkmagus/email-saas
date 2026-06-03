"""Seed the first admin account from environment variables."""
import asyncio
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from api.config import get_settings
from api.db import Base
from api.models import Account, AccountRole, AccountStatus
from api.deps import hash_password

settings = get_settings()

async def main():
    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as db:
        email = os.getenv("FIRST_ADMIN_EMAIL", "admin@example.com")
        password = os.getenv("FIRST_ADMIN_PASSWORD", "changeme-strong-password")
        existing = await db.execute(select(Account).where(Account.email == email))
        if existing.scalar_one_or_none():
            print("Admin already exists.")
            return
        admin = Account(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password(password),
            role=AccountRole.superadmin,
            status=AccountStatus.active,
            display_name="First Admin",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(admin)
        await db.commit()
        print(f"Created admin: {email}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
