import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.db import get_db
from api.deps import (
    create_access_token,
    decode_token,
    get_current_active_account,
    get_current_account,
    get_redis,
    hash_password,
    verify_password,
    maybe_account,
)
from api.models import Account, AccountRole, AccountStatus, PlanTier, LoginLog, Session, WebmailToken
from api.schemas import (
    ErrorOut,
    MessageOut,
    PasswordChange,
    PasswordResetConfirm,
    PasswordResetRequest,
    TOTPDisable,
    TOTPRecoveryRequest,
    TOTPSetup,
    TOTPVerify,
    UserCreate,
    UserLogin,
    UserOut,
    UserProfileUpdate,
    WebmailSSOIn,
    WebmailSSOOut,
    WebmailTokenOut,
)
from api.services.audit import audit_from_request

import pyotp
from redis.asyncio import Redis

router = APIRouter()
settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserOut)
@limiter.limit("5/minute")
async def register(
    request: Request,
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Account).where(Account.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    account = Account(
        id=uuid.uuid4(),
        email=data.email,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
        status=AccountStatus.active,
        role=AccountRole.customer,
        plan=PlanTier.starter,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    await audit_from_request(
        request, "register", "account", str(account.id), account.id, account.id, metadata={"email": account.email}
    )
    return account


@router.post("/login")
@limiter.limit("10/minute")
async def login(
    request: Request,
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    result = await db.execute(select(Account).where(Account.email == data.email))
    account = result.scalar_one_or_none()
    if not account or not verify_password(data.password, account.password_hash):
        # Log failed login attempt
        log = LoginLog(
            id=uuid.uuid4(),
            account_id=account.id if account else None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            success=False,
        )
        db.add(log)
        await db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if account.totp_enabled:
        # Return a temp token requiring TOTP
        temp_token = create_access_token(
            {"sub": str(account.id), "totp_required": True},
            expires_delta_minutes=5,
            token_type="totp_challenge",
        )
        return {"temp_token": temp_token, "totp_required": True}

    token = create_access_token({"sub": str(account.id)})
    # Decode to get jti for session tracking
    token_payload = decode_token(token)
    jti = token_payload.get("jti", str(uuid.uuid4()))
    session = Session(
        id=uuid.uuid4(),
        account_id=account.id,
        token_jti=jti,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes),
    )
    db.add(session)
    # Log successful login
    log = LoginLog(
        id=uuid.uuid4(),
        account_id=account.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        success=True,
    )
    db.add(log)
    await db.commit()
    await redis.setex(f"session:{account.id}:access", settings.access_token_expire_minutes * 60, "active")
    await audit_from_request(
        request, "login", "account", str(account.id), account.id, account.id, metadata={"email": account.email}
    )
    return {"access_token": token, "token_type": "bearer", "account": UserOut.model_validate(account)}


@router.post("/login/totp")
async def login_totp(
    request: Request,
    temp_token: str,
    code: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    try:
        payload = decode_token(temp_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired temp token")
    if payload.get("type") != "totp_challenge":
        raise HTTPException(status_code=401, detail="Invalid token type")
    account_id = payload.get("sub")
    result = await db.execute(select(Account).where(Account.id == uuid.UUID(account_id)))
    account = result.scalar_one_or_none()
    if not account or not account.totp_enabled:
        raise HTTPException(status_code=401, detail="TOTP not enabled")
    totp = pyotp.TOTP(account.totp_secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Invalid TOTP code")
    token = create_access_token({"sub": str(account.id)})
    token_payload = decode_token(token)
    jti = token_payload.get("jti", str(uuid.uuid4()))
    session = Session(
        id=uuid.uuid4(),
        account_id=account.id,
        token_jti=jti,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes),
    )
    db.add(session)
    # Log successful TOTP login
    log = LoginLog(
        id=uuid.uuid4(),
        account_id=account.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        success=True,
    )
    db.add(log)
    await db.commit()
    await redis.setex(f"session:{account.id}:access", settings.access_token_expire_minutes * 60, "active")
    await audit_from_request(
        request, "login_totp", "account", str(account.id), account.id, account.id, metadata={"email": account.email}
    )
    return {"access_token": token, "token_type": "bearer", "account": UserOut.model_validate(account)}


@router.get("/me", response_model=UserOut)
async def me(account: Account = Depends(get_current_active_account)):
    return account


@router.patch("/me", response_model=UserOut)
async def update_me(
    request: Request,
    data: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    if data.display_name is not None:
        account.display_name = data.display_name
    await db.commit()
    await db.refresh(account)
    await audit_from_request(request, "update_profile", "account", str(account.id), account.id, account.id)
    return account


@router.post("/change-password", response_model=MessageOut)
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    if not verify_password(data.old_password, account.password_hash):
        raise HTTPException(status_code=400, detail="Old password incorrect")
    account.password_hash = hash_password(data.new_password)
    await db.commit()
    await audit_from_request(
        request, "change_password", "account", str(account.id), account.id, account.id
    )
    return {"message": "Password updated"}


@router.post("/logout")
async def logout(
    request: Request,
    account: Account = Depends(get_current_account),
    redis: Redis = Depends(get_redis),
):
    await redis.setex(f"session:{account.id}:access", settings.access_token_expire_minutes * 60, "revoked")
    await audit_from_request(request, "logout", "account", str(account.id), account.id, account.id)
    return {"message": "Logged out"}


@router.post("/totp/setup", response_model=TOTPSetup)
async def totp_setup(
    request: Request,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    if account.totp_enabled:
        raise HTTPException(status_code=400, detail="TOTP already enabled")
    secret = pyotp.random_base32()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=account.email, issuer_name="Email SaaS"
    )
    # Store secret temporarily? We store in DB but don't enable until verify.
    account.totp_secret = secret
    await db.commit()
    return {"secret": secret, "uri": uri}


class TOTPVerifyOut(BaseModel):
    message: str
    recovery_codes: list[str]


@router.post("/totp/verify", response_model=TOTPVerifyOut)
async def totp_verify(
    request: Request,
    data: TOTPVerify,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    if not account.totp_secret:
        raise HTTPException(status_code=400, detail="TOTP not set up")
    totp = pyotp.TOTP(account.totp_secret)
    if not totp.verify(data.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid code")
    account.totp_enabled = True
    # Generate 10 recovery codes with strong entropy
    import secrets
    import hashlib
    import hmac
    raw_codes = [secrets.token_urlsafe(12) for _ in range(10)]  # 96 bits each
    secret_key = settings.api_key_secret or settings.secret_key
    account.recovery_codes = [
        hmac.new(secret_key.encode(), c.encode(), hashlib.sha256).hexdigest()
        for c in raw_codes
    ]
    await db.commit()
    await audit_from_request(request, "enable_totp", "account", str(account.id), account.id, account.id)
    return {"message": "TOTP enabled", "recovery_codes": raw_codes}  # Displayed once


@router.post("/totp/recovery")
@limiter.limit("3/minute")
async def totp_recovery(
    request: Request,
    data: TOTPRecoveryRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    result = await db.execute(select(Account).where(Account.email == data.email))
    account = result.scalar_one_or_none()
    if not account or not verify_password(data.password, account.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not account.totp_enabled or not account.recovery_codes:
        raise HTTPException(status_code=400, detail="TOTP not enabled or no recovery codes")
    import hashlib
    import hmac
    secret_key = settings.api_key_secret or settings.secret_key
    provided_hash = hmac.new(secret_key.encode(), data.recovery_code.encode(), hashlib.sha256).hexdigest()
    if provided_hash not in account.recovery_codes:
        raise HTTPException(status_code=400, detail="Invalid recovery code")
    # Remove used recovery code
    account.recovery_codes = [c for c in account.recovery_codes if c != provided_hash]
    await db.commit()
    token = create_access_token({"sub": str(account.id)})
    token_payload = decode_token(token)
    jti = token_payload.get("jti", str(uuid.uuid4()))
    session = Session(
        id=uuid.uuid4(),
        account_id=account.id,
        token_jti=jti,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes),
    )
    db.add(session)
    # Log successful TOTP recovery login
    log = LoginLog(
        id=uuid.uuid4(),
        account_id=account.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        success=True,
    )
    db.add(log)
    await db.commit()
    await redis.setex(
        f"session:{account.id}:access",
        settings.access_token_expire_minutes * 60,
        "active",
    )
    await audit_from_request(request, "totp_recovery", "account", str(account.id), account.id, account.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "account": UserOut.model_validate(account),
    }


@router.post("/totp/regenerate-codes", response_model=MessageOut)
async def totp_regenerate_codes(
    request: Request,
    data: TOTPDisable,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    """Regenerate recovery codes after TOTP verification."""
    if not account.totp_enabled or not account.totp_secret:
        raise HTTPException(status_code=400, detail="TOTP not enabled")
    totp = pyotp.TOTP(account.totp_secret)
    if not totp.verify(data.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid code")
    import secrets
    import hashlib
    import hmac
    raw_codes = [secrets.token_urlsafe(12) for _ in range(10)]
    secret_key = settings.api_key_secret or settings.secret_key
    account.recovery_codes = [
        hmac.new(secret_key.encode(), c.encode(), hashlib.sha256).hexdigest()
        for c in raw_codes
    ]
    await db.commit()
    await audit_from_request(request, "regenerate_recovery_codes", "account", str(account.id), account.id, account.id)
    return {"message": "Recovery codes regenerated", "recovery_codes": raw_codes}


@router.post("/totp/disable", response_model=MessageOut)
async def totp_disable(
    request: Request,
    data: TOTPDisable,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    if not account.totp_enabled or not account.totp_secret:
        raise HTTPException(status_code=400, detail="TOTP not enabled")
    totp = pyotp.TOTP(account.totp_secret)
    if not totp.verify(data.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid code")
    account.totp_enabled = False
    account.totp_secret = None
    account.recovery_codes = None
    await db.commit()
    await audit_from_request(request, "disable_totp", "account", str(account.id), account.id, account.id)
    return {"message": "TOTP disabled"}


@router.post("/reset-password/request", response_model=MessageOut)
@limiter.limit("3/minute")
async def reset_password_request(request: Request, data: PasswordResetRequest):
    # In production, send email with reset link containing token.
    return {"message": "If that email exists, a reset link was sent"}


@router.post("/reset-password/confirm", response_model=MessageOut)
@limiter.limit("3/minute")
async def reset_password_confirm(
    request: Request,
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = decode_token(data.token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    account_id = payload.get("sub")
    result = await db.execute(select(Account).where(Account.id == uuid.UUID(account_id)))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=400, detail="Invalid token")
    account.password_hash = hash_password(data.new_password)
    await db.commit()
    await audit_from_request(request, "reset_password", "account", str(account.id), account.id, account.id)
    return {"message": "Password reset successfully"}


@router.get("/webmail-token", response_model=WebmailTokenOut)
async def webmail_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    import secrets
    token_value = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    webmail_token = WebmailToken(
        id=uuid.uuid4(),
        account_id=account.id,
        token=token_value,
        expires_at=expires_at,
        used=False,
    )
    db.add(webmail_token)
    await db.commit()
    await audit_from_request(
        request, "webmail_token_created", "webmail_token", str(webmail_token.id), account.id, account.id
    )
    sso_url = f"{settings.roundcube_base_url}/sso?token={token_value}"
    return {"token": token_value, "url": sso_url}


@router.post("/webmail-sso", response_model=WebmailSSOOut)
async def webmail_sso(
    data: WebmailSSOIn,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WebmailToken)
        .where(
            WebmailToken.token == data.token,
            WebmailToken.used == False,
            WebmailToken.expires_at > datetime.now(timezone.utc),
        )
    )
    webmail_token = result.scalar_one_or_none()
    if not webmail_token:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    webmail_token.used = True
    await db.commit()
    result = await db.execute(select(Account).where(Account.id == webmail_token.account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=400, detail="Account not found")
    return {"email": account.email, "password_hash": account.password_hash}
