import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.config import get_settings
from api.db import get_db
from api.models import Account, AccountRole, ApiKey
from api.services.api_key_crypto import verify_api_key

pwd_context = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

security_bearer = HTTPBearer(auto_error=False)

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(
    data: dict,
    expires_delta_minutes: int | None = None,
    token_type: str = "access",
) -> str:
    to_encode = data.copy()
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=(
            expires_delta_minutes
            if expires_delta_minutes is not None
            else settings.access_token_expire_minutes
        )
    )
    to_encode.update({"exp": expire, "type": token_type, "jti": jti})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


_redis_pool: Redis | None = None

async def get_redis() -> Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_pool


async def get_current_account(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    api_key: str | None = Depends(api_key_header),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> Account:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token:
        try:
            payload = decode_token(token)
        except JWTError:
            raise credentials_exception

        account_id = payload.get("sub")
        token_type = payload.get("type", "access")
        if account_id is None:
            raise credentials_exception

        try:
            account_id_uuid = uuid.UUID(account_id)
        except ValueError:
            raise credentials_exception

        # Check Redis session revocation
        session_key = f"session:{account_id}:{token_type}"
        revoked = await redis.get(session_key)
        if revoked == "revoked":
            raise credentials_exception

        result = await db.execute(select(Account).where(Account.id == account_id_uuid))
        account = result.scalar_one_or_none()
        if account is None:
            raise credentials_exception
        # Set on request state for audit middleware
        request.state.account_id = str(account.id)
        request.state.actor_id = str(account.id)
        return account

    if api_key:
        if not api_key.startswith("esk_"):
            raise credentials_exception
        prefix = api_key[:11]
        result = await db.execute(
            select(ApiKey).where(
                ApiKey.prefix == prefix,
                ApiKey.revoked_at.is_(None),
            )
        )
        key = result.scalar_one_or_none()
        if key is None:
            raise credentials_exception
        if not verify_api_key(api_key, key.hashed_secret):
            raise credentials_exception
        # Update last_used_at
        key.last_used_at = datetime.now(timezone.utc)
        await db.commit()
        result = await db.execute(select(Account).where(Account.id == key.account_id))
        account = result.scalar_one_or_none()
        if account is None:
            raise credentials_exception
        request.state.account_id = str(account.id)
        request.state.actor_id = str(key.id)
        return account

    raise credentials_exception


async def get_current_active_account(
    account: Account = Depends(get_current_account),
) -> Account:
    if account.status.value in ("suspended", "cancelled"):
        raise HTTPException(status_code=403, detail="Account suspended or cancelled")
    return account


async def require_admin(account: Account = Depends(get_current_active_account)) -> Account:
    if account.role not in (AccountRole.admin, AccountRole.superadmin):
        raise HTTPException(status_code=403, detail="Admin access required")
    if settings.admin_2fa_required and not account.totp_enabled:
        raise HTTPException(status_code=403, detail="2FA required for admin access")
    return account


async def require_superadmin(account: Account = Depends(get_current_active_account)) -> Account:
    if account.role != AccountRole.superadmin:
        raise HTTPException(status_code=403, detail="Superadmin access required")
    if settings.admin_2fa_required and not account.totp_enabled:
        raise HTTPException(status_code=403, detail="2FA required for admin access")
    return account


async def require_customer(account: Account = Depends(get_current_active_account)) -> Account:
    if account.role != AccountRole.customer:
        raise HTTPException(status_code=403, detail="Customer access required")
    return account


async def maybe_account(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Account | None:
    if not token:
        return None
    try:
        payload = decode_token(token)
    except JWTError:
        return None
    account_id = payload.get("sub")
    if not account_id:
        return None
    try:
        account_id_uuid = uuid.UUID(account_id)
    except ValueError:
        return None
    result = await db.execute(select(Account).where(Account.id == account_id_uuid))
    return result.scalar_one_or_none()
