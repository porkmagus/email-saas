# Revised Critique Fixes — Implementation Plan

**Date:** 2026-06-03
**Source:** Second-party review of `CRITIQUE_REMEDIATION_REPORT.md`
**Status:** 13 verified concerns require fixes
**Estimated Duration:** 18-24 hours
**Files to Change:** 20+ backend files, 3 frontend files, 3 infra files

---

## Verified Concerns Summary

| # | Concern | Severity | Verified In Code |
|---|---------|----------|-------------------|
| 1 | Stripe webhook idempotency checks ANY existing row, not just `completed` | Critical | `stripe.py` line 100: `if existing.scalar_one_or_none(): return "already processed"` — blocks retries after crash |
| 2 | Send throttling exists but never called in mail path | Critical | `send_throttle.py` has `check_send_allowed()` but no router calls it |
| 3 | Abuse scoring auto-suspension is `pass` (no-op) | Critical | `abuse_scoring.py` line 415: `if status == red: pass` |
| 4 | DKIM private key generated but discarded — never stored or pushed to Stalwart | Critical | `domains.py` line 49: `private_key` variable never serialized or stored |
| 5 | API_KEY_SECRET runtime-generated default breaks existing keys on restart | Critical | `config.py` line 44: `default_factory=lambda: secrets.token_urlsafe(32)` |
| 6 | TOTP recovery endpoint uses `data.code` on `UserLogin` schema — has no `code` field | Critical | `auth.py` line 239: `data.code` — `UserLogin` only has `email` and `password` |
| 7 | Admin impersonation still `GET` — should be `POST` | Critical | `admin.py` line 161: `@router.get(".../impersonate")` |
| 8 | TOTP recovery codes too weak — `secrets.token_hex(4)` = 32 bits, plain SHA-256 | High | `auth.py` line 220: `secrets.token_hex(4)` |
| 9 | SPF too simplistic — no provider-level SPF, no IPv6, no startup validation | High | `domains.py` line 167: `v=spf1 ip4:{ip} -all` only |
| 10 | Metrics only count `SendEvent` rows, not live Stalwart queue | High | `metrics.py` only queries DB, no Stalwart API call |
| 11 | Restore drill doesn't restore into actual PostgreSQL | High | `restore_drill.py` only checks file existence |
| 12 | CSP too generic, may break Stripe/Roundcube | Medium | `vps1.conf` and `vps2.conf` share identical CSP |
| 13 | Enterprise plan says 5,000/day but config says 500/day | Medium | `LandingPage.tsx` vs `config.py` mismatch |

---

## Phase 1: Fix Critical Bugs (6-8 hours)

### 1.1 Fix Stripe Webhook Idempotency

**File:** `backend/api/routers/stripe.py`

**Current broken behavior:**
```python
existing = await db.execute(select(StripeEvent).where(StripeEvent.stripe_event_id == stripe_event_id))
if existing.scalar_one_or_none():
    return {"message": "Event already processed"}  # BUG: blocks retries after crash
```

**Fix:**
```python
existing = await db.execute(
    select(StripeEvent).where(StripeEvent.stripe_event_id == stripe_event_id)
)
existing_event = existing.scalar_one_or_none()

if existing_event:
    if existing_event.processing_status == StripeEventStatus.completed:
        return {"message": "Event already processed"}
    elif existing_event.processing_status == StripeEventStatus.processing:
        # Check if stale (older than 5 minutes)
        stale_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
        if existing_event.received_at < stale_threshold:
            existing_event.processing_status = StripeEventStatus.retrying
            await db.commit()
        else:
            return {"message": "Event processing in progress"}
    elif existing_event.processing_status == StripeEventStatus.failed:
        existing_event.processing_status = StripeEventStatus.retrying
        await db.commit()
    else:
        return {"message": "Event processing in progress"}
else:
    # Insert with race protection
    try:
        stripe_event = StripeEvent(..., processing_status=StripeEventStatus.processing)
        db.add(stripe_event)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return {"message": "Event processing in progress"}
```

**Also add:**
- `attempt_count` field to `StripeEvent` model
- `last_attempt_at` field to `StripeEvent` model
- `locked_until` field for worker coordination
- Increment `attempt_count` on each retry
- Update `last_attempt_at` on each attempt

**Migration:** Patch `002_abuse_limits_stripe_events.py` to add new columns.

---

### 1.2 Integrate Send Throttling into Mail Path

**File:** `backend/api/routers/mailboxes.py` (or new `send.py` router)

**Current state:** `check_send_allowed()` exists in `send_throttle.py` but is never called.

**Fix:** Add a `POST /api/v1/send` endpoint that:
1. Calls `check_send_allowed()` before accepting the message
2. Calls `record_send()` after successful queue insertion
3. Returns 429 if limits exceeded

```python
@router.post("/send", response_model=MessageOut)
async def send_email(
    request: Request,
    data: SendEmailRequest,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    # Check abuse score first
    allowed, reason = await check_abuse_status(db, account.id)
    if not allowed:
        raise HTTPException(status_code=429, detail=reason)
    
    # Check send limits
    allowed, reason = await check_send_allowed(db, account.id)
    if not allowed:
        raise HTTPException(status_code=429, detail=reason)
    
    # Queue to Stalwart (or local queue for retry)
    try:
        await queue_message_to_stalwart(data)
        await record_send(db, account.id)
        return {"message": "Message queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue: {e}")
```

**Also:** Add `send_limit_middleware` that checks limits on all mail-related endpoints.

**New Schema:**
```python
class SendEmailRequest(BaseModel):
    to: list[EmailStr]
    subject: str
    body: str
    from_mailbox_id: uuid.UUID | None = None
```

---

### 1.3 Complete Abuse Scoring Enforcement

**File:** `backend/api/services/abuse_scoring.py`

**Current broken code:**
```python
if status == AbuseScoreStatus.red:
    # Trigger suspension logic
    pass  # BUG: no-op
```

**Fix:**
```python
from api.models import Account, AccountStatus
from api.services.audit import audit_log

async def enforce_abuse_action(db: AsyncSession, account_id: uuid.UUID, score: AbuseScore) -> None:
    if score.status == AbuseScoreStatus.red:
        # Suspend account immediately
        result = await db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()
        if account and account.status != AccountStatus.suspended:
            account.status = AccountStatus.suspended
            await db.commit()
            await audit_log(
                "abuse_auto_suspend",
                "account",
                str(account_id),
                account_id=account_id,
                metadata={
                    "bounce_rate": score.bounce_rate,
                    "complaint_rate": score.complaint_rate,
                    "total_score": score.total_score,
                }
            )
            # Notify admin
            await notify_admin(f"Account {account_id} auto-suspended due to abuse score: {score.total_score}")
    
    elif score.status == AbuseScoreStatus.orange:
        # Hold outbound mail, notify admin
        await notify_admin(f"Account {account_id} abuse score orange: {score.total_score}")
    
    elif score.status == AbuseScoreStatus.yellow:
        # Reduce send limits
        pass  # Lower limits in next period
```

**Also add:**
- `Account.abuse_status` enum field (green, yellow, orange, red)
- `Account.abuse_hold_until` datetime field
- Admin endpoint to manually override abuse hold
- Customer-facing suspension notice (generic, not revealing abuse details)

---

### 1.4 Fix DKIM Private Key Storage

**File:** `backend/api/routers/domains.py`

**Current broken code:**
```python
private_key = rsa.generate_private_key(...)  # Generated but never used again
public_key = private_key.public_key()
# ... only public key is extracted
# Private key is discarded!
```

**Fix Option A (Stalwart owns DKIM):**
```python
# After creating domain in Stalwart:
# Let Stalwart generate the keypair
# Fetch the public key and selector from Stalwart API
# Store only the selector and DNS record in our DB
# Do NOT store the private key
```

**Fix Option B (App owns, pushes to Stalwart):**
```python
from cryptography.hazmat.primitives import serialization

# Generate keypair
private_key = rsa.generate_private_key(...)
public_key = private_key.public_key()

# Serialize private key
private_pem = private_key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption()  # In production, encrypt with app secret
)

# Store encrypted private key in DB
# Use unique selector with counter to avoid collisions
selector = f"saas{datetime.now(timezone.utc).strftime('%Y%m%d')}a"

# Push to Stalwart via API
await stalwart_configure_dkim(domain.domain, selector, private_pem.decode(), public_record)

# Store in DB
domain.dkim_selector = selector
domain.dkim_record = public_record
domain.dkim_private_key_encrypted = encrypt_with_app_secret(private_pem.decode())
```

**New model field:**
```python
# api/models.py
class Domain(Base):
    ...
    dkim_private_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
```

**New endpoint:**
```python
# Safe rotation with dual-selector
@router.post("/{domain_id}/rotate-dkim")
async def rotate_dkim(request, domain_id, db, account):
    # 1. Generate new keypair
    # 2. Store as "staging" selector
    # 3. Push to Stalwart as secondary
    # 4. Wait for DNS verification
    # 5. Promote to primary
    # 6. Schedule old selector retirement after TTL
```

---

### 1.5 Fix API_KEY_SECRET Runtime Generation

**File:** `backend/api/config.py`

**Current broken code:**
```python
api_key_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
```

**Fix:**
```python
api_key_secret: str = Field(default="")  # No default in production

# In main.py or startup validation:
@app.on_event("startup")
async def validate_production_config():
    if settings.environment == "production":
        if not settings.api_key_secret:
            raise RuntimeError("API_KEY_SECRET is required in production")
        if settings.api_key_secret.startswith("change-me"):
            raise RuntimeError("API_KEY_SECRET placeholder value is not allowed")
        if len(settings.api_key_secret) < 32:
            raise RuntimeError("API_KEY_SECRET must be at least 32 characters")
```

---

### 1.6 Fix TOTP Recovery Endpoint Crash

**File:** `backend/api/routers/auth.py`

**Current broken code:**
```python
@router.post("/totp/recovery", response_model=UserOut)
async def totp_recovery(request: Request, data: UserLogin, db: AsyncSession):
    # ...
    provided_hash = hashlib.sha256(data.code.encode()).hexdigest()  # BUG: UserLogin has no .code
```

**Fix:**
```python
class TOTPRecoveryRequest(BaseModel):
    email: EmailStr
    password: str
    recovery_code: str

@router.post("/totp/recovery", response_model=UserOut)
@limiter.limit("3/minute")
async def totp_recovery(
    request: Request,
    data: TOTPRecoveryRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Account).where(Account.email == data.email))
    account = result.scalar_one_or_none()
    if not account or not verify_password(data.password, account.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not account.totp_enabled or not account.recovery_codes:
        raise HTTPException(status_code=400, detail="TOTP not enabled or no recovery codes")
    
    # HMAC-SHA256 with server secret
    from api.config import get_settings
    settings = get_settings()
    secret = settings.api_key_secret or settings.secret_key
    provided_hash = hmac.new(secret.encode(), data.recovery_code.encode(), hashlib.sha256).hexdigest()
    
    if provided_hash not in account.recovery_codes:
        raise HTTPException(status_code=400, detail="Invalid recovery code")
    
    # Remove used code
    account.recovery_codes = [c for c in account.recovery_codes if c != provided_hash]
    await db.commit()
    
    token = create_access_token({"sub": str(account.id), "email": account.email})
    await audit_from_request(request, "totp_recovery", "account", str(account.id), account.id, account.id)
    return {"id": account.id, "email": account.email, "token": token, "role": account.role, "plan": account.plan, "status": account.status}
```

**Also fix recovery code generation:**
```python
# In totp_verify:
raw_codes = [secrets.token_urlsafe(12) for _ in range(10)]  # 96 bits, not 32
```

---

### 1.7 Change Admin Impersonation to POST

**File:** `backend/api/routers/admin.py`

**Current broken code:**
```python
@router.get("/accounts/{account_id}/impersonate", response_model=AdminImpersonateOut)
async def impersonate(request, account_id, reason: str = "", db, admin, redis):
    # ... reason in query string
```

**Fix:**
```python
class AdminImpersonateRequest(BaseModel):
    reason: str = Field(..., min_length=5)
    ticket_id: str | None = None  # Optional support ticket reference

@router.post("/accounts/{account_id}/impersonate", response_model=AdminImpersonateOut)
async def impersonate(
    request: Request,
    account_id: uuid.UUID,
    data: AdminImpersonateRequest,
    db: AsyncSession = Depends(get_db),
    admin: Account = Depends(require_superadmin),
    redis: Redis = Depends(get_redis),
):
    # Require fresh re-auth for impersonation
    # ...
    token = create_access_token({
        "sub": str(account.id),
        "impersonated_by": str(admin.id),
        "impersonated_by_email": admin.email,
        "reason": data.reason,
    }, ...)
    # ...
```

**Also add:**
- Frontend banner showing impersonation mode
- `POST /auth/reauth` endpoint for destructive actions
- Short session lifetime for impersonation tokens

---

## Phase 2: High-Priority Fixes (6-8 hours)

### 2.1 Fix SPF to Provider-Level Pattern

**File:** `backend/api/routers/domains.py`

**Fix:**
```python
# Provider SPF (set once on provider domain)
# _spf.yourprovider.com TXT "v=spf1 ip4:{vps2_ip} ip6:{vps2_ipv6} -all"

# Customer SPF recommendation
"spf_record": f"v=spf1 include:_spf.yourprovider.com -all",

# For customers with existing providers:
"spf_record": f"v=spf1 include:_spf.yourprovider.com include:_spf.customers_existing.com -all",
```

**Add validation:**
```python
# In startup or domain creation:
if settings.vps2_public_ip == "1.2.3.4" or not settings.vps2_public_ip:
    raise RuntimeError("VPS2_PUBLIC_IP must be set to a real IP")
```

---

### 2.2 Add Live Stalwart Metrics

**File:** `backend/api/services/metrics.py`

**Add:**
```python
async def get_stalwart_metrics() -> dict:
    """Fetch live queue metrics from Stalwart API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.stalwart_base_url}/api/queue",
                headers={"Authorization": f"Bearer {settings.stalwart_api_token}"}
            )
            return response.json()
    except Exception as e:
        return {"error": str(e), "queue_depth": -1}
```

**Update admin metrics endpoint:**
```python
@router.get("/metrics", response_model=dict)
async def get_metrics(db: AsyncSession, admin: Account):
    db_metrics = await get_mail_metrics(db)
    stalwart_metrics = await get_stalwart_metrics()
    return {
        **db_metrics,
        "stalwart": stalwart_metrics,
    }
```

---

### 2.3 Fix Restore Drill to Actually Restore

**File:** `backend/scripts/restore_drill.py`

**Fix:**
```python
# 1. Restore files
# 2. Create temp PostgreSQL database
# 3. Import dump
# 4. Run schema validation
# 5. Check row counts
# 6. Verify critical tables exist
# 7. Report pass/fail

# Create temp database
subprocess.run(["createdb", "-h", "localhost", "restore_drill_test"], ...)

# Import dump
subprocess.run(["psql", "-h", "localhost", "-d", "restore_drill_test", "-f", pg_dump], ...)

# Validate
result = subprocess.run(["psql", "-h", "localhost", "-d", "restore_drill_test", 
                        "-c", "SELECT count(*) FROM accounts"], ...)

# Check backup age
# Alert on failure
# Record result in ops table
```

---

### 2.4 Split CSP by Application Surface

**Files:** `infra/nginx/vps1.conf`, `infra/nginx/vps2.conf`

**Fix:**
```nginx
# VPS-1 (React app + API)
location / {
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' https://js.stripe.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' https://api.stripe.com; frame-src https://js.stripe.com https://hooks.stripe.com; frame-ancestors 'none'; base-uri 'none'; form-action 'self';" always;
}

# VPS-2 (Roundcube)
location / {
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self';" always;
}
```

**Also:** Generate TOTP QR codes locally instead of using `api.qrserver.com`.

---

### 2.5 Fix Plan Limit Mismatch

**File:** `frontend/src/pages/LandingPage.tsx`

**Fix:**
```tsx
features: ["20 Domains", "100 Mailboxes", "500GB Storage", "500 emails/day (after warm-up)", "Dedicated Support"],
```

**Or update config:**
```python
# backend/api/config.py
warmed_account_daily_limit: int = 5000  # Match Enterprise plan
```

**Recommendation:** Make limits plan-aware:
```python
PLAN_LIMITS = {
    "starter": {"domains": 1, "mailboxes": 5, "storage_gb": 10, "daily_send": 100},
    "pro": {"domains": 5, "mailboxes": 25, "storage_gb": 100, "daily_send": 1000},
    "enterprise": {"domains": 20, "mailboxes": 100, "storage_gb": 500, "daily_send": 5000},
}
```

---

## Phase 3: Testing & Verification (4-6 hours)

### 3.1 Update Tests

**Files:** `backend/tests/test_stripe_webhooks.py`, `backend/tests/test_admin.py`, `backend/tests/test_auth.py`

**Add:**
- Test Stripe webhook retry after `processing` state
- Test `POST /admin/accounts/{id}/impersonate` with JSON body
- Test `POST /auth/totp/recovery` with `TOTPRecoveryRequest`
- Test weak recovery code rejection
- Test `API_KEY_SECRET` startup validation

### 3.2 Run Full Test Suite
```bash
python -m pytest tests/ -v
```

### 3.3 Run pip-audit
```bash
pip-audit --local
```

### 3.4 Build Frontend
```bash
npm run build
npm audit
```

### 3.5 Build Docker
```bash
docker build -t email-saas-backend:verified .
docker build -t email-saas-frontend:verified .
```

---

## Phase 4: Documentation (2-3 hours)

### 4.1 Update `.env.example`
```bash
# Required in production
API_KEY_SECRET=replace-with-32-char-random-string
VPS2_PUBLIC_IP=your.actual.vps2.ip
```

### 4.2 Update `docs/SETUP.md`
- Add startup validation checklist
- Add required env vars section
- Add production secrets guidance

### 4.3 Update `docs/SECURITY.md`
- Add API key HMAC documentation
- Add TOTP recovery flow
- Add abuse scoring documentation

---

## Files Likely to Change

**Backend (15+ files):**
- `api/routers/stripe.py` — Fix idempotency logic
- `api/routers/admin.py` — Change impersonation to POST
- `api/routers/auth.py` — Fix TOTP recovery endpoint and codes
- `api/routers/domains.py` — Fix DKIM private key storage
- `api/routers/mailboxes.py` — Add send endpoint with throttling
- `api/routers/send.py` — New: outbound mail endpoint
- `api/config.py` — Fix API_KEY_SECRET default, add startup validation
- `api/models.py` — Add `dkim_private_key_encrypted`, `attempt_count`, `last_attempt_at`, `locked_until`
- `api/schemas.py` — Add `TOTPRecoveryRequest`, `SendEmailRequest`, `AdminImpersonateRequest`
- `api/services/abuse_scoring.py` — Add enforcement logic
- `api/services/send_throttle.py` — Add atomic Redis pipeline
- `api/services/metrics.py` — Add Stalwart live metrics
- `api/services/dkim.py` — New: DKIM key management
- `api/main.py` — Add startup validation
- `scripts/restore_drill.py` — Actually restore into PostgreSQL
- `migrations/versions/002_abuse_limits_stripe_events.py` — Add new columns

**Frontend (1 file):**
- `src/pages/LandingPage.tsx` — Fix plan limits

**Infrastructure (2 files):**
- `infra/nginx/vps1.conf` — Separate CSP for React app
- `infra/nginx/vps2.conf` — Separate CSP for Roundcube

**Documentation (2 files):**
- `.env.example` — Add required secrets
- `docs/SETUP.md` — Add production validation

---

## Risks and Trade-offs

| Risk | Mitigation |
|------|------------|
| Changing impersonation from GET to POST breaks existing frontend | Update frontend admin page simultaneously |
| Stalwart API for queue metrics may not exist | Add graceful fallback, document endpoint needed |
| DKIM key encryption adds complexity | Use simple AES-256-GCM with app secret, document key escrow |
| Stripe webhook retry logic adds complexity | Extensive tests, manual Stripe CLI webhook tests |
| Redis pipeline for atomic counters requires testing | Add load tests for race conditions |

---

## Open Questions

1. Should Stalwart own DKIM (Option A) or should app push keys to Stalwart (Option B)?
2. What is the actual Stalwart API endpoint for queue metrics?
3. Should we add a `send` router or integrate throttling into existing mailbox router?
4. Should Enterprise plan be 500 or 5000/day? (Currently 500 in config, 5000 in frontend)

---

## Launch Status After This Plan

| Category | Before | After This Plan |
|---|---|---|
| Billing correctness | Not proven | Stripe webhook idempotency fixed |
| Mail provisioning | Not proven | Send throttling integrated |
| Abuse prevention | Partial | Auto-suspension implemented |
| DKIM | Incomplete | Private key stored and pushed |
| SPF | Better | Provider-level pattern |
| API key security | Needs fix | Required persistent secret |
| TOTP recovery | Broken | Fixed endpoint, stronger codes |
| Admin impersonation | Unsafe | POST + MFA + audit |
| Monitoring | Partial | Live Stalwart metrics added |
| Backup/restore | Partial | Real PostgreSQL restore |
| Public paid launch | No | Still no — needs real infrastructure tests |
| Private beta | Yes | Yes, with strict limits |

---

**END OF PLAN**
