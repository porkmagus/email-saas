import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.db import engine, get_db
from api.deps import get_redis
from api.routers import (
    auth, stripe, domains, mailboxes, admin, tickets, api_keys, send,
    aliases, blocked_senders, catchall, contacts, email_rules, vacation_response,
    app_passwords, files, login_logs, notes, outbox, passkeys, sessions, snooze,
    calendar, search, import_jobs, export_jobs,
)
from api.services.audit import audit_from_request
from api.models import AuditLog, ActorType

settings = get_settings()

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(lambda conn: None)
    
    # Production config validation
    if settings.environment == "production":
        if not settings.api_key_secret:
            raise RuntimeError("API_KEY_SECRET is required in production")
        if not settings.secret_key or len(settings.secret_key) < 32:
            raise RuntimeError("SECRET_KEY must be at least 32 characters in production")
        if not settings.stripe_secret_key or settings.stripe_secret_key.startswith("sk_test"):
            raise RuntimeError("STRIPE_SECRET_KEY must be a live key in production")
        if not settings.stalwart_api_token:
            raise RuntimeError("STALWART_API_TOKEN is required in production")
        if not settings.vps2_public_ip or settings.vps2_public_ip == "1.2.3.4":
            raise RuntimeError("VPS2_PUBLIC_IP must be set to a real IP in production")
        if settings.docs_enabled is not False:
            raise RuntimeError("DOCS_ENABLED must be false in production")
        if settings.stripe_webhook_secret == "whsec_test":
            raise RuntimeError("STRIPE_WEBHOOK_SECRET must be a real secret in production")
    
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="Email SaaS API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    # Only audit mutating methods
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        try:
            account_id_str = getattr(request.state, "account_id", None)
            actor_id_str = getattr(request.state, "actor_id", None)
            account_id = uuid.UUID(account_id_str) if account_id_str else None
            actor_id = uuid.UUID(actor_id_str) if actor_id_str else None
            await audit_from_request(
                request=request,
                action=f"{request.method} {request.url.path}",
                resource_type="http_request",
                resource_id=None,
                account_id=account_id,
                actor_id=actor_id,
                actor_type=ActorType.user,
                metadata={"duration_ms": round(duration * 1000, 2), "status_code": response.status_code},
            )
        except Exception:
            pass
    return response


# Apply rate limits to specific routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(stripe.router, prefix="/api/v1/stripe", tags=["stripe"])
app.include_router(domains.router, prefix="/api/v1/domains", tags=["domains"])
app.include_router(mailboxes.router, prefix="/api/v1/mailboxes", tags=["mailboxes"])
app.include_router(send.router, prefix="/api/v1/send", tags=["send"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(tickets.router, prefix="/api/v1/tickets", tags=["tickets"])
app.include_router(api_keys.router, prefix="/api/v1/api-keys", tags=["api_keys"])
app.include_router(aliases.router, prefix="/api/v1/aliases", tags=["aliases"])
app.include_router(blocked_senders.router, prefix="/api/v1/blocked-senders", tags=["blocked_senders"])
app.include_router(catchall.router, prefix="/api/v1/catch-all", tags=["catch_all"])
app.include_router(contacts.router, prefix="/api/v1/contacts", tags=["contacts"])
app.include_router(email_rules.router, prefix="/api/v1/email-rules", tags=["email_rules"])
app.include_router(vacation_response.router, prefix="/api/v1/vacation-response", tags=["vacation_response"])
app.include_router(app_passwords.router, prefix="/api/v1/app-passwords", tags=["app_passwords"])
app.include_router(files.router, prefix="/api/v1/files", tags=["files"])
app.include_router(login_logs.router, prefix="/api/v1/login-logs", tags=["login_logs"])
app.include_router(notes.router, prefix="/api/v1/notes", tags=["notes"])
app.include_router(outbox.router, prefix="/api/v1/outbox", tags=["outbox"])
app.include_router(snooze.router, prefix="/api/v1/snooze", tags=["snooze"])
app.include_router(passkeys.router, prefix="/api/v1/passkeys", tags=["passkeys"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(calendar.router, prefix="/api/v1/calendar", tags=["calendar"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(import_jobs.router, prefix="/api/v1/import", tags=["import"])
app.include_router(export_jobs.router, prefix="/api/v1/export", tags=["export"])


@app.get("/api/v1/health", response_model=dict)
async def health_check():
    db_ok = "ok"
    redis_ok = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = "error"
    try:
        redis = await get_redis()
        await redis.ping()
    except Exception:
        redis_ok = "error"
    status_code = 200 if db_ok == "ok" and redis_ok == "ok" else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ok" if status_code == 200 else "degraded", "database": db_ok, "redis": redis_ok},
    )


@app.get("/")
async def root():
    payload = {"message": "Email SaaS API", "version": "1.0.0"}
    if settings.docs_enabled:
        payload["docs"] = "/docs"
    return payload
