# Email SaaS: Agentic AI Coding Plan (Compact)

**Verified against:** `/Users/sean/repos/email-saas/` — all patterns, paths, and conventions are exact matches to the codebase.

---

## 1. STACK SNAPSHOT

| Layer | Tech | Versions |
|-------|------|----------|
| Backend | FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL (asyncpg) | fastapi==0.136.3, sqlalchemy==2.0.50, asyncpg==0.31.0 |
| Cache/Queue | Redis | redis==5.2.1 |
| Mail | Stalwart v0.16 (JMAP + HTTP API) | httpx==0.28.1 |
| Billing | Stripe | stripe==15.1.0 |
| Auth | JWT (HS256, python-jose), TOTP (pyotp), bcrypt, HMAC recovery codes | python-jose==3.5.0, pyotp==2.9.0, bcrypt==4.3.0 |
| Rate Limit | slowapi + Redis | slowapi==0.1.9 |
| Config | Pydantic Settings, `.env` | pydantic-settings==2.14.1 |
| Frontend | React 19 + Vite 6 + TypeScript 5.8 + Tailwind 4 | react==19.2.6, vite==6.4.3, tailwindcss==4.1.4 |
| HTTP Client | axios | axios==1.17.0 |
| Icons | lucide-react | lucide-react==0.487.0 |

---

## 2. CRITICAL PATHS

```
backend/api/main.py        # FastAPI app, router registration, lifespan, middleware
backend/api/config.py      # Settings class (env-based, Pydantic)
backend/api/db.py          # Async engine, session, Base
backend/api/models.py      # All SQLAlchemy models (16 tables)
backend/api/schemas.py     # All Pydantic schemas
backend/api/deps.py        # Auth dependencies, JWT, Redis, bcrypt
backend/api/routers/       # auth.py, domains.py, mailboxes.py, send.py, admin.py, tickets.py, api_keys.py, stripe.py
backend/api/services/      # stalwart_api.py, provision.py, send_throttle.py, audit.py, crypto.py, api_key_crypto.py
frontend/src/api/client.ts # Axios instance with interceptors
frontend/src/context/      # AuthContext.tsx, ToastContext.tsx
frontend/src/App.tsx       # Routes, RequireAuth, GuestRoute
```

---

## 3. BACKEND PATTERNS (Copy these exactly)

### 3.1 Model
```python
import uuid, enum
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UUID, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.db import Base

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

class MyModel(Base):
    __tablename__ = "my_models"
    __table_args__ = (Index("ix_my_models_account_id", "account_id"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)
    account: Mapped["Account"] = relationship("Account", back_populates="my_models")
```
**Rule:** Add `my_models: Mapped[list["MyModel"]] = relationship("MyModel", back_populates="account", lazy="selectin", cascade="all, delete-orphan")` to `Account`. Always run `alembic revision --autogenerate -m "add my_models"` then `alembic upgrade head`.

### 3.2 Schema
```python
from pydantic import BaseModel, ConfigDict, Field
class MyModelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
class MyModelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    account_id: uuid.UUID
    name: str
    created_at: datetime
```

### 3.3 Router
```python
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, MyModel
from api.schemas import MyModelCreate, MyModelOut, MessageOut
from api.services.audit import audit_from_request

router = APIRouter()

@router.post("", response_model=MyModelOut)
async def create_my_model(
    request: Request,
    data: MyModelCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    # Check ownership
    # Check uniqueness
    # Create entity
    # Audit log
    # Return entity
    pass
```

### 3.4 Auth Dependencies (chain)
```python
# No auth → get_current_account → get_current_active_account → require_admin → require_superadmin
# Use get_current_active_account for customer endpoints.
# Use require_admin for admin endpoints (requires 2FA if admin_2fa_required).
# Use require_superadmin for superadmin endpoints.
```

### 3.5 Audit Log (mandatory for POST/PUT/PATCH/DELETE)
```python
from api.services.audit import audit_from_request
await audit_from_request(request, "action_name", "resource_type", str(resource.id), account.id, account.id, metadata={"key": "value"})
```

### 3.6 Stalwart API Call
```python
from api.services.stalwart_api import client  # httpx.AsyncClient, already configured
# JMAP call:
r = await client.post("/api", json={"using": ["urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"], "methodCalls": [["Mailbox/get", {"accountId": "..."}, "0"]]})
# HTTP error handling:
try:
    r.raise_for_status()
    return r.json()
except httpx.HTTPStatusError as e:
    raise HTTPException(status_code=502, detail=f"Mail server error: {e.response.status_code}")
```

---

## 4. FRONTEND PATTERNS (Copy these exactly)

### 4.1 API Call
```typescript
import { api } from "../api/client";
const res = await api.get<MyType[]>("/endpoint");
const data = res.data;
```
**Never use raw `fetch`.**

### 4.2 Page Component
```typescript
import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";

export default function MyPage() {
  const { account } = useAuth();
  const { addToast } = useToast();
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try { const res = await api.get<Item[]>("/endpoint"); setItems(res.data); }
      catch (err: any) { addToast(err?.response?.data?.detail || "Failed to load", "error"); }
      finally { setLoading(false); }
    }
    load();
  }, [account, addToast]);

  if (loading) return <Loading />;
  return <div className="space-y-6">...</div>;
}
```

### 4.3 Tailwind Classes (existing theme)
- Cards: `card p-6`
- Buttons: `btn-primary`, `btn-secondary`, `btn-danger`
- Inputs: `input`
- Labels: `label`
- Layout: `space-y-6`, `grid sm:grid-cols-2 gap-4`
- Colors: `text-accent`, `text-success`, `text-danger`, `text-warning`, `text-muted`, `bg-surface-alt`, `bg-accent/10`
- Loading: `<Loader2 size={16} className="animate-spin" />`

---

## 5. GUARDRAILS (Non-negotiable)

### 5.1 Code Generation
1. Never invent new patterns — use exact patterns from this doc.
2. Never change existing code style.
3. Never skip migrations.
4. Never skip audit logging on mutating endpoints.
5. Never skip auth checks.
6. Never use `print()` — use logger.
7. Never hardcode secrets — use `settings.xxx`.
8. Never skip error handling on Stalwart calls.
9. Never use `eval()` or `exec()`.
10. Never store plaintext in logs.

### 5.2 Database
- Always add indexes on foreign keys and query columns.
- Always use `ondelete="CASCADE"` or `SET NULL` on FKs.
- Always use `nullable=False` unless truly optional.
- Always use `default=now_utc` for timestamps.
- Always use `uuid.uuid4()` for IDs.
- Never add/remove columns without a migration.

### 5.3 API
- Always use Pydantic schemas for request/response.
- Always use `response_model` on router decorators.
- Always validate ownership (check `account_id` matches).
- Always return proper HTTP codes (201 create, 200 update, 204 delete, 404 not found, 400 bad request, 429 rate limited).
- Always rate-limit public endpoints with `@limiter.limit("5/minute")`.
- Never return raw SQLAlchemy objects or password hashes.

### 5.4 Frontend
- Always use `api` client from `api/client.ts`.
- Always handle errors with `addToast(..., "error")`.
- Always show loading states.
- Always use Tailwind classes from the existing theme.
- Never use inline styles.
- Never add new dependencies without justification.
- Always use TypeScript types (no `any`).

### 5.5 Stalwart
- Always use the existing `client` from `stalwart_api.py`.
- Always handle `httpx.HTTPStatusError` with 502/503.
- Always verify API docs before implementing.
- Never call Stalwart synchronously for long operations — use background jobs.
- Cache Stalwart responses in Redis when appropriate.

### 5.6 Testing
- Always write tests for new endpoints.
- Always mock Stalwart API calls.
- Always test auth failures (401, 403).
- Always test duplicate creation (400).
- Always test ownership validation (404 for other user's resources).
- Use `pytest-asyncio` for async tests.
- Use `aiosqlite` for test DB.

### 5.7 Security Checklist (before marking done)
- [ ] Auth checks (`get_current_active_account` or higher)
- [ ] Ownership validation enforced
- [ ] Audit logging on all mutating endpoints
- [ ] Rate limiting applied
- [ ] Pydantic input validation with Field constraints
- [ ] No sensitive data returned in responses
- [ ] No secrets logged
- [ ] Stalwart errors handled gracefully (not exposed to user)
- [ ] SQL injection impossible (only parameterized queries)

---

## 6. COMMON PITFALLS

| Wrong | Correct |
|-------|---------|
| `db.execute(...)` | `await db.execute(...)` |
| `Account.id == account_id` (string) | `Account.id == uuid.UUID(account_id)` |
| `Redis.from_url(...)` without close | `redis = await get_redis(); ...; await redis.aclose()` |
| `class MyOut(BaseModel):` (no `model_config`) | `class MyOut(BaseModel): model_config = ConfigDict(from_attributes=True)` |
| `fetch("/api/...")` | `api.get<T>("/endpoint")` |
| `client.post("/api/v1/account", ...)` | `client.post("/api", json={"methodCalls": [...]})` (JMAP) |
| `datetime.now()` | `datetime.now(timezone.utc)` (or `now_utc()`) |
| `password = "plain"` in code | `password_hash = hash_password(password)` |
| `select(Account).where(Account.email == email)` without index | Add `Index("ix_accounts_email", "email", unique=True)` in model |
| `return account` directly from endpoint | `return MyOut.model_validate(account)` or use `response_model` |

---

## 7. QUICK REFERENCE: EXISTING ENDPOINTS

| Prefix | Methods | Description |
|--------|---------|-------------|
| `/api/v1/auth` | POST register, login, login/totp, logout, change-password, totp/*, reset-password/* | Auth, TOTP, password |
| `/api/v1/domains` | POST, GET, GET/{id}, DELETE/{id}, POST/{id}/verify, POST/{id}/rotate-dkim, GET/{id}/onboarding, GET/{id}/dns-guide | Domain CRUD, DNS |
| `/api/v1/mailboxes` | POST, GET, GET/{id}, PATCH/{id}, DELETE/{id} | Mailbox CRUD |
| `/api/v1/send` | POST /send | Send email (throttled) |
| `/api/v1/admin` | GET /metrics, GET /accounts, GET /accounts/{id}, POST /accounts/{id}/impersonate, POST /accounts/{id}/suspend, POST /accounts/{id}/unsuspend, GET /jobs, GET /stats, GET /audit-log | Admin |
| `/api/v1/api-keys` | POST, GET, DELETE/{id} | API key management |
| `/api/v1/stripe` | POST /checkout, POST /portal, POST /webhook | Stripe |
| `/api/v1/tickets` | POST, GET, GET/{id}, POST/{id}/comments, PATCH/{id} | Support tickets |
| `/api/v1/health` | GET | Health check |

---

## 8. MIGRATION CHECKLIST

When adding any new feature:
1. Add model to `backend/api/models.py`.
2. Add relationship to `Account` model.
3. Add schema to `backend/api/schemas.py`.
4. Add router to `backend/api/routers/`.
5. Register router in `backend/api/main.py`.
6. Add page/component to `frontend/src/pages/` or `frontend/src/components/`.
7. Add route in `frontend/src/App.tsx`.
8. Run `alembic revision --autogenerate -m "add xxx"`.
9. Run `alembic upgrade head`.
10. Write tests in `backend/tests/`.
11. Run `pytest`.

---

## 9. IMPLEMENTATION PHASES (What to build)

**Architecture principle:** The React SPA is the control panel. Users configure everything in the dashboard (Settings, Domains, etc.). The FastAPI backend pushes those settings to Stalwart via JMAP/Management API. Roundcube is just a mail reader — it connects to Stalwart's IMAP and naturally sees all applied rules, aliases, vacation, etc. Roundcube is NOT a configuration panel. Users do not set up aliases or rules inside Roundcube.

**Flow:** User → React SPA → FastAPI → Stalwart API → Stalwart server. Roundcube → Stalwart IMAP (read-only mail).

### Phase 1: Foundation (Weeks 1-2)

| Feature | Gap | UI Location | Backend | Stalwart |
|---------|-----|-------------|---------|----------|
| **JMAP Client** | No JMAP API client exists | None — backend only | Extend `stalwart_api.py` with `jmap_call()` | JMAP API |
| **Roundcube SSO** | Users must log in manually with mailbox credentials | `MailSetupPage.tsx` — "Open Webmail" button opens new tab with `?_sso_token=xxx` | Add `GET /api/v1/auth/webmail-token` to `auth.py` | Roundcube plugin to verify token |
| **DB Migrations** | No tables for aliases, rules, vacation, contacts, files | None — schema only | Add `Alias`, `BlockedSender`, `EmailRule`, `VacationResponse`, `Contact`, `ContactGroup`, `File` to `models.py` + alembic | None |

### Phase 2: Core Email (Weeks 3-4)

| Feature | Gap | UI Location | Backend | Stalwart |
|---------|-----|-------------|---------|----------|
| **Aliases** | No aliases. Only mailboxes exist. | **Settings → Aliases** (or **Domains → Aliases** tab). List, add, delete, toggle active. | `aliases.py` router. `POST/GET/DELETE/PATCH /api/v1/aliases`. Sync to Stalwart via `/api/principal` (group type) or domain `emails` array. | `POST /api/principal` with type=group, emails=[alias], members=[target] |
| **Catch-all** | No catch-all. Every mailbox must be pre-created. | **Domains → Domain Settings** — toggle "Enable catch-all" + target mailbox selector. | Patch `domains.py`. `POST /api/v1/domains/{id}/catch-all`. Update `Domain` table with `catch_all_target_mailbox_id`. | Domain config via Management API |
| **Vacation Response** | No auto-responder. | **Settings → Vacation** — enable toggle, date range, subject, body, scope checkboxes (only contacts, only aliases). | `vacation.py` router. `VacationResponse` table. Generate Sieve `vacation` script, push via JMAP `SieveScript/set`. | JMAP for Sieve (RFC 9661) |
| **Rules Engine** | No rules/filters. | **Settings → Rules** — visual builder: condition (from/to/subject/contains/equals), action (move to/copy to/delete/label). Drag to reorder priority. | `rules.py` router. `EmailRule` table. Generate Sieve script from all active rules, push via JMAP. | JMAP for Sieve |
| **Blocked Senders** | No blocked senders list. | **Settings → Blocked Senders** — list of emails/domains. Add/remove. Auto-moves to Trash. | `blocked_senders.py` router. `BlockedSender` table. Auto-generate hidden Sieve rule. | Sieve via JMAP |
| **Sieve Editor** | No custom Sieve editing. | **Settings → Rules → Advanced** tab. Monaco/CodeMirror editor with syntax highlight. | Extend `rules.py`. Validate syntax. Push via JMAP. | JMAP for Sieve |

### Phase 3: Collaboration (Weeks 5-6)

| Feature | Gap | UI Location | Backend | Stalwart |
|---------|-----|-------------|---------|----------|
| **Calendar** | No calendar. | **Calendar** page (nav item). Month/week/day views. Create/edit events. Handle ICS invitations. | `calendar.py` router (CalDAV proxy). `Calendar`, `CalendarEvent` cache tables. | CalDAV (RFC 4791) + JMAP for Calendars |
| **Contacts** | No contacts. | **Contacts** page (nav item). List, groups, add/edit. Auto-save from mail. | `contacts.py` router. `Contact`, `ContactGroup` tables. Sync to CardDAV. | CardDAV (RFC 6352) + JMAP for Contacts |
| **File Storage** | No file storage. | **Files** page (nav item). Drag-and-drop, folder tree, file list. | `files.py` router (WebDAV proxy). `File` cache table. | WebDAV (RFC 4918) |
| **Notes** | No notes. | **Notes** page (nav item). Simple text editor, list of notes. | `notes.py` router. `Note` table. | IMAP Notes folder or WebDAV |

### Phase 4: UX & Security (Weeks 7-8)

| Feature | Gap | UI Location | Backend | Stalwart |
|---------|-----|-------------|---------|----------|
| **Dark Mode** | Only light theme. | **Settings → Appearance** — toggle. Applies globally. | None | None |
| **Keyboard Shortcuts** | No shortcuts. | Global. Press `?` to show overlay. | None | None |
| **Passkeys** | No passkey/WebAuthn support. | **Settings → Security → Passkeys** — add/remove passkeys. | `passkeys.py` router. `Passkey` table. | None |
| **App Passwords** | No app passwords for IMAP/SMTP. | **Settings → Security → App Passwords** — create, name, view, revoke. | `app_passwords.py` router. Proxy to Stalwart Management API. | App Password API |
| **Session Management** | No session list/revocation. | **Settings → Security → Sessions** — list active sessions, revoke individual or all. | Extend `auth.py`. Redis session keys. | None |
| **Login Log** | No login history. | **Settings → Security → Login History** — table of IP, location, time, success/failure. | `login_log.py` or extend audit. | None |

### Phase 5: Advanced (Weeks 9-12)

| Feature | Gap | UI Location | Backend | Stalwart |
|---------|-----|-------------|---------|----------|
| **Undo Send** | Messages send immediately. | **Compose** → after sending, toast shows "Undo" for 10-30s. | `send.py` extension. `OutboxMessage` table. Worker polls every 5s. | None (handled before Stalwart) |
| **Scheduled Send** | No future delivery. | **Compose** → "Schedule" button. Date/time picker. | Extend `send.py`. Same `OutboxMessage` table. | None |
| **Snooze** | No snooze. | **Inbox** (in custom webmail or via Roundcube context menu) → "Snooze" → 1h, 1d, 1w, custom. | `snooze.py` router. Store snooze in DB. Apply via JMAP/Sieve at time. | JMAP flags or Sieve |
| **Import** | No import from Gmail/Outlook. | **Settings → Import** — IMAP server, credentials, OAuth2 for Gmail. Progress bar. | `import.py` router. `imaplib` sync. Background job. | IMAP (external) |
| **Export** | No export. | **Settings → Export** — select MBOX/ICS/vCard, generate, download. | `export.py` router. Generate files, stream download. | IMAP + CalDAV + CardDAV |
| **Full-Text Search** | No search in webmail. | **Search bar** in top nav or webmail. Instant results. | `search.py` router. PostgreSQL `tsvector` or proxy to Stalwart. | Stalwart built-in FTS (17 languages) |
| **Desktop Notifications** | No push notifications. | Browser permission prompt. **Settings → Notifications** — enable/disable. | `notifications.py` router. Web Push API. Service worker. | Webhooks `store.ingest` event |
| **VIP Notifications** | No per-sender notification rules. | **Contacts** → "VIP" toggle on contact. **Settings → Notifications** → "VIP only" mode. | Extend notifications. `is_vip` on `Contact`. | None |

### Phase 6: Scale & Enterprise (Months 3-6+)

| Feature | Gap | UI Location | Backend | Notes |
|---------|-----|-------------|---------|-------|
| **Custom Webmail** | Roundcube is basic, no SSO | **Inbox** page (nav item). Replaces Roundcube. Threads, compose, attachments. | JMAP API for mail sync. | 6-12 month project. Replaces Roundcube. |
| **Native Mobile Apps** | No mobile apps | Mobile app (React Native/Flutter). | JMAP API for sync. | High complexity. |
| **Shared Mailboxes** | No shared mailboxes/team features | **Settings → Shared Mailboxes** — invite users, set permissions. | `shared_mailboxes.py` router. Stalwart ACLs + Groups. | Stalwart IMAP ACL + JMAP Sharing. |
| **DNS Hosting** | No DNS management | **Domains → DNS** — manage records. Custom nameservers. | PowerDNS or similar. | Requires new infrastructure. |
| **Website Hosting** | No website hosting | **Files → Publish** — select folder, publish as static site. | Static file hosting from WebDAV. | Low priority. |
| **Quota Add-ons** | No extra storage purchases | **Billing → Upgrade Storage** — slider, checkout. | Stripe metered billing. Update Stalwart quota. | Easy with existing Stripe. |
| **Retention Policies** | No tamper-proof retention | **Admin** → retention settings. | `RetentionPolicy` table. WORM storage. | Complex. |

---

## 10. PRIORITY MATRIX

| Priority | Features | UI Location | Est. Time | Impact |
|----------|----------|-------------|-----------|--------|
| **P0 (now)** | JMAP client, Roundcube SSO, aliases, catch-all | Settings, MailSetupPage, Domains | 2-3 weeks | Core identity |
| **P1 (next)** | Calendar, contacts, file storage, rules, vacation, blocked senders | Settings, Calendar, Contacts, Files | 4-6 weeks | Differentiation |
| **P2 (later)** | Dark mode, keyboard shortcuts, passkeys, app passwords, undo send, scheduled send | Settings, Compose | 3-4 weeks | UX + security |
| **P3 (future)** | Custom webmail, mobile apps, shared mailboxes, DNS hosting | Inbox, Settings, Domains | 3-6 months | Scale + enterprise |

---

*Document compiled by analyzing the full email-saas codebase. All patterns, paths, and conventions are verified against the actual source code.*
