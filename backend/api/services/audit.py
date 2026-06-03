import uuid
from datetime import datetime, timezone

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert

from api.models import AuditLog, ActorType
from api.db import async_session_maker


async def log_audit(
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    account_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
    actor_type: ActorType = ActorType.user,
    metadata: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    try:
        async with async_session_maker() as db:
            await db.execute(
                insert(AuditLog).values(
                    id=uuid.uuid4(),
                    account_id=account_id,
                    actor_id=actor_id,
                    actor_type=actor_type,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    meta_data=metadata,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    created_at=datetime.now(timezone.utc),
                )
            )
            await db.commit()
    except Exception:
        # Audit logging is best-effort; don't block main request
        pass


async def audit_from_request(
    request: Request,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    account_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
    actor_type: ActorType = ActorType.user,
    metadata: dict | None = None,
) -> None:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    await log_audit(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        account_id=account_id,
        actor_id=actor_id,
        actor_type=actor_type,
        metadata=metadata,
        ip_address=ip,
        user_agent=ua,
    )
