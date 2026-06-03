# Email SaaS: Next Tasks & Agent Guardrails

**Document version:** 2025-06-03
**Status:** All 11 coding-plan features (catch-all, dark mode, calendar, keyboard shortcuts, search, desktop notifications, VIP contacts, import, export, sieve editor, Roundcube SSO) have been implemented. Remaining work below are **cleanup, stabilization, and production-readiness** tasks.

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
| Config | Pydantic Settings, .env | pydantic-settings==2.14.1 |
| Frontend | React 19 + Vite 6 + TypeScript 5.8 + Tailwind 4 | react==19.2.6, vite==6.4.3, tailwindcss==4.1.4 |
| HTTP Client | axios | axios==1.17.0 |
| Icons | lucide-react | lucide-react==0.487.0 |

---

## 2. CRITICAL PATHS

```
backend/api/main.py        # FastAPI app, router registration, lifespan, middleware
backend/api/config.py      # Settings class (env-based, Pydantic)
backend/api/db.py          # Async engine, session, Base
backend/api/models.py      # All SQLAlchemy models (~22 tables)
backend/api/schemas.py     # All Pydantic schemas
backend/api/deps.py        # Auth dependencies, JWT, Redis, bcrypt
backend/api/routers/       # All feature routers
backend/api/services/      # stalwart_api.py, provision.py, send_throttle.py, audit.py, crypto.py, api_key_crypto.py
frontend/src/api/client.ts # Axios instance with interceptors
frontend/src/context/      # AuthContext.tsx, ToastContext.tsx, ThemeContext.tsx
frontend/src/App.tsx       # Routes, RequireAuth, GuestRoute
frontend/src/index.css     # Tailwind CSS + CSS variables (light + dark mode)
```

---

## 3. REMAINING TASKS (Production Readiness)

### Task 1: Apply All Pending Database Migrations
**Priority:** P0 (must run before app boots)
**Backend:**
- Migrations 005 through 009 are ready but unapplied.
- Run: `cd /home/sean/repos/email-saas/backend && alembic upgrade head`
- Verify all tables exist: `calendar_events`, `import_jobs`, `export_jobs`, `webmail_tokens`, `contacts.is_vip` (via migration 006), `accounts.sieve_script` (via migration 008).
- If any migration fails, fix the revision chain. Downgrade to a known-good revision and re-apply.

**Guardrails:**
- Never skip migrations.
- Always back up the database before running migrations in production.
- Never add/remove columns without a migration.

---

### Task 2: Fix Frontend Build / Verify TypeScript
**Priority:** P0 (must pass before deployment)
**Frontend:**
- `node_modules` is missing in the environment. Run: `cd /home/sean/repos/email-saas/frontend && npm install`
- Run: `cd /home/sean/repos/email-saas/frontend && npm run build` (runs `tsc && vite build`)
- Fix any TypeScript errors.
- Fix any Tailwind class warnings.
- Verify all new routes in `App.tsx` resolve correctly.
- Verify all new `Sidebar` nav icons exist in `lucide-react`.
- Verify `ThemeContext.tsx` is imported and used correctly in `main.tsx` and `Sidebar.tsx`.
- Verify `KeyboardShortcuts.tsx` is mounted in `Layout.tsx` and does not conflict with existing key listeners.
- Verify `SearchBar.tsx` is mounted in `Layout.tsx` and does not break mobile layout.

**Guardrails:**
- Never use raw `fetch`. Use `api` from `../api/client`.
- Never use inline styles. Use Tailwind classes.
- Never add new dependencies unless approved. Use `lucide-react` for icons.
- All new pages must use `useAuth`, `useToast`, `Loading` pattern.
- All new pages must have a `try/catch` around API calls.

---

### Task 3: Verify Backend Router Registration & Imports
**Priority:** P0
**Backend:**
- Verify `backend/api/main.py` correctly imports all new routers:
  - `calendar`, `search`, `import_jobs`, `export_jobs`, `email_rules` (renamed from `rules`), `passkeys`, `sessions`
- Verify each router is included with the correct prefix and tags.
- Ensure `email_rules.py` (not `rules.py`) is the file used in `main.py` imports.
- Verify `backend/api/config.py` has `roundcube_base_url` set (or defaults to `"https://webmail.example.com"`). Update `.env` to the real URL.
- Run the backend: `cd /home/sean/repos/email-saas/backend && python -m uvicorn api.main:app --reload` (or the project run command).
- Verify all new endpoints are reachable via Swagger UI (`/docs`).
- Test each new endpoint with a valid auth token.

**Guardrails:**
- Always use `response_model` on router decorators.
- Always use `get_current_active_account` for customer endpoints.
- Always add audit logging on POST/PUT/PATCH/DELETE.
- Always handle Stalwart API errors with `try/except httpx.HTTPStatusError`.
- Never use `print()`. Use `logging.getLogger(__name__)`.
- Never hardcode secrets. Use `settings.xxx`.

---

### Task 4: Search Backend - Replace ILIKE with PostgreSQL Full-Text Search
**Priority:** P1
**Backend:**
- Current `search.py` uses simple `ILIKE` pattern matching. This is fine for small datasets but will degrade at scale.
- Add a `tsvector` column to the `messages` table (or create a search index) using PostgreSQL `to_tsvector`.
- Update `search.py` to use `func.to_tsvector('english', ...)` + `plainto_tsquery`.
- Add a GIN index on the tsvector column for performance.
- Add `tsvector` columns for `contacts` (name + email) and `notes` (title + content) as well.
- Create an Alembic migration for the new indexes and columns.
- Ensure search results are still filtered by `account_id`.
- Keep the `scope` param working (emails, contacts, files, notes, all).

**Guardrails:**
- Always add indexes on query columns.
- Always use `ondelete="CASCADE"` or `SET NULL` on FKs.
- Always add a migration for schema changes.
- Never expose other accounts' data in search results.

---

### Task 5: Import/Export - Implement Real Background Workers
**Priority:** P1
**Backend:**
- Current `import_jobs.py` and `export_jobs.py` use `background_tasks.add_task` as a stub. Replace with a real task queue.
- Add a `background_worker.py` module using `celery` or `arq` (or a simple Redis-backed worker).
- For import: connect via `imaplib` or `aiosmtplib`, fetch messages in batches, save to Stalwart via JMAP.
- For export: generate MBOX/ICS/vCard files, write to a temp directory, upload to S3 or serve as a streaming download.
- Update `import_jobs.py` to kick off the worker instead of `background_tasks`.
- Update `export_jobs.py` to kick off the worker.
- Add progress tracking (poll `GET /api/v1/import/{id}` or `GET /api/v1/export/{id}` for status).
- Add a `retry` mechanism for failed import jobs.

**Guardrails:**
- Never store plaintext passwords in the database. Encrypt the `password` field in `ImportJob` using `api.services.crypto`.
- Never expose IMAP credentials in logs or API responses.
- Always validate the IMAP server hostname before connecting.
- Always add audit logging when import/export starts.
- Use `settings` for any S3 bucket names or file paths.

---

### Task 6: Roundcube SSO - Configure Production URL & Plugin
**Priority:** P1
**Backend:**
- Update `backend/api/config.py`: `roundcube_base_url` must point to the real Roundcube instance.
- Create a Roundcube plugin (PHP) that:
  1. Reads the `token` query parameter on the Roundcube login page.
  2. Calls `POST /api/v1/auth/webmail-sso` with the token.
  3. Uses the returned `email` and `password_hash` to authenticate the user.
  4. Redirects to the Roundcube inbox.
- Ensure the token is single-use and expires after 5 minutes.
- Ensure the token is invalidated after use.
- Add rate limiting to `POST /api/v1/auth/webmail-sso` (e.g., 5 requests per minute per IP).

**Guardrails:**
- Never return the plaintext password in the SSO response.
- Always validate the token against the `WebmailToken` table (unused + not expired).
- Always mark the token as used immediately after validation.
- Never log the token value.

---

### Task 7: Dark Mode - Verify CSS Coverage & Accessibility
**Priority:** P2
**Frontend:**
- Audit all existing pages for missing `dark:` class coverage.
- Check that `index.css` dark mode variables apply correctly to all custom components.
- Verify `html.dark` class is toggled on `<html>` (not `<body>`) by `ThemeContext`.
- Add `prefers-color-scheme: dark` fallback if `localStorage` key is missing.
- Ensure focus rings and active states are visible in dark mode.
- Verify the theme toggle is accessible (aria-label, keyboard focus).
- Add `theme-color` meta tag to `index.html` to match current theme.

**Guardrails:**
- Never use inline styles for colors.
- Always use CSS variables (`--color-background`, `--color-surface`, etc.) or Tailwind dark mode.
- Never hardcode color hex values in component code.

---

### Task 8: Keyboard Shortcuts - Resolve Conflicts & Add Missing Shortcuts
**Priority:** P2
**Frontend:**
- Ensure `KeyboardShortcuts.tsx` does not intercept `Escape` when a modal is already open (e.g., Calendar event modal, Sieve editor).
- Ensure `KeyboardShortcuts.tsx` does not intercept `/` when the user is inside a text input.
- Ensure `g` sequences do not interfere with the browser's native `Ctrl+G` or `Cmd+G`.
- Add missing shortcuts for new pages:
  - `g i` -> Import
  - `g e` -> Export
  - `g f` -> Files
  - `g n` -> Notes
  - `g p` -> Passkeys
  - `g l` -> Login Logs
  - `g u` -> Outbox
  - `g z` -> Snooze
  - `g v` -> Vacation Response
  - `g r` -> Email Rules
- Add a shortcut for "Toggle notifications" (`n t`).
- Add a shortcut for "Search" (`/` - already implemented, verify it focuses the SearchBar).
- Verify the `?` help overlay lists all current shortcuts and has no stale entries.

**Guardrails:**
- Never block native browser shortcuts (Ctrl+C, Ctrl+V, Ctrl+S, Ctrl+Z, Ctrl+F).
- Always check `event.target` is not an input/textarea before intercepting key presses.
- Always use `useEffect` with cleanup for global listeners.

---

### Task 9: Search Frontend - Add Mobile Layout & Keyboard Navigation
**Priority:** P2
**Frontend:**
- Ensure `SearchBar.tsx` collapses to a small icon on mobile and expands on tap.
- Add keyboard navigation inside the search results dropdown (Up/Down arrows, Enter to select, Escape to close).
- Add a "No results" state.
- Add loading state inside the search dropdown.
- Ensure the search overlay does not block the sidebar on mobile.
- Add a `debounce` of 300ms (already implemented, verify it works correctly).
- Ensure the `scope` tabs are scrollable on mobile.

**Guardrails:**
- Always use `useEffect` for cleanup.
- Always use the `api` client, not raw `fetch`.
- Always handle `Escape` to close the dropdown.

---

### Task 10: Calendar - Sync with Stalwart CalDAV
**Priority:** P2
**Backend:**
- Current `CalendarEvent` is stored only in PostgreSQL. Sync events to Stalwart via CalDAV.
- On create/update/delete of a `CalendarEvent`, push the change to Stalwart via CalDAV (or JMAP for Calendars if available).
- On read, prefer Stalwart as the source of truth and cache in PostgreSQL.
- Add a background sync job that periodically pulls events from Stalwart and updates the local cache.
- Handle recurrence rules (`recurrence_rule` field) correctly when syncing.
- Handle ICS invitations (e.g., `METHOD:REQUEST`) by parsing the ICS and creating/updating events.

**Guardrails:**
- Always handle CalDAV errors gracefully.
- Always use `settings` for CalDAV server URL.
- Never expose Stalwart admin credentials.
- Always add audit logging for calendar mutations.

---

### Task 11: VIP Notifications - Wire to Desktop Notifications
**Priority:** P2
**Backend + Frontend:**
- Backend: when a new message arrives from a `Contact` with `is_vip=True`, include a `vip: true` flag in the notification payload.
- Frontend: when `DesktopNotifications` is enabled, check if the incoming notification is VIP. If the user has "VIP only" mode enabled in Settings, only show VIP notifications.
- Add a "VIP only" toggle in `SettingsPage.tsx` under the Notifications section.
- Persist the "VIP only" setting in `localStorage` as `vip_notifications_only`.
- Add a Web Push subscription endpoint that filters by VIP status.

**Guardrails:**
- Always respect the user's notification preference.
- Never spam notifications.
- Always check `Notification.permission === "granted"` before showing.

---

### Task 12: Sieve Editor - Add Syntax Highlighting
**Priority:** P3
**Frontend:**
- Replace the plain `<textarea>` in `EmailRulesPage.tsx` with a lightweight code editor (e.g., `react-simple-code-editor` or `prismjs` for syntax highlighting).
- Use `prismjs` with a Sieve grammar (or a custom grammar for basic Sieve keywords: `require`, `if`, `elsif`, `else`, `fileinto`, `reject`, `discard`, `keep`, `stop`, `redirect`, `vacation`, `allof`, `anyof`, `not`, `header`, `address`, `envelope`, `size`, `body`).
- The editor should be at least 20 rows tall.
- Keep the existing validate/save/reset buttons.
- Ensure the editor works in dark mode.
- Ensure the editor is accessible (tab navigation, focus visible).

**Guardrails:**
- Do not add heavy dependencies (e.g., Monaco Editor) unless necessary.
- Keep the bundle size small.
- Use existing `lucide-react` icons.

---

### Task 13: Custom Webmail (Inbox) - Planning Only
**Priority:** P3 (do not implement yet)
**Notes:**
- This is a 6-12 month project to replace Roundcube.
- Do not write any code for this yet. Only gather requirements.
- Plan: JMAP API client, thread view, compose UI, attachment handling, drag-and-drop, search, filters.
- Keep this as a separate PRD document when ready.

---

## 4. BACKEND PATTERNS (Copy these exactly)

### 4.1 Model
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

### 4.2 Schema
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

### 4.3 Router
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

### 4.4 Auth Dependencies (chain)
```
# No auth -> get_current_account -> get_current_active_account -> require_admin -> require_superadmin
# Use get_current_active_account for customer endpoints.
# Use require_admin for admin endpoints (requires 2FA if admin_2fa_required).
# Use require_superadmin for superadmin endpoints.
```

### 4.5 Audit Log (mandatory for POST/PUT/PATCH/DELETE)
```python
from api.services.audit import audit_from_request
await audit_from_request(request, "action_name", "resource_type", str(resource.id), account.id, account.id, metadata={"key": "value"})
```

### 4.6 Stalwart API Call
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

## 5. FRONTEND PATTERNS (Copy these exactly)

### 5.1 API Call
```typescript
import { api } from "../api/client";
const res = await api.get<MyType[]>("/endpoint");
const data = res.data;
```
**Never use raw `fetch`.**

### 5.2 Page Component
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

### 5.3 Tailwind Classes (existing theme)
- Cards: `card p-6`
- Buttons: `btn-primary`, `btn-secondary`, `btn-danger`, `btn-success`, `btn-accent`
- Inputs: `input`
- Labels: `label`
- Layout: `space-y-6`, `grid sm:grid-cols-2 gap-4`
- Colors: `text-accent`, `text-success`, `text-danger`, `text-warning`, `text-muted`, `bg-surface-alt`, `bg-accent/10`
- Loading: `<Loader2 size={16} className="animate-spin" />`
- Dark mode: `html.dark` class toggles all CSS variables automatically.

---

## 6. GUARDRAILS (Non-negotiable)

### 6.1 Code Generation
1. Never invent new patterns - use exact patterns from this doc.
2. Never change existing code style.
3. Never skip migrations.
4. Never skip audit logging on mutating endpoints.
5. Never skip auth checks.
6. Never use `print()` - use logger.
7. Never hardcode secrets - use `settings.xxx`.
8. Never skip error handling on Stalwart calls.
9. Never use `eval()` or `exec()`.
10. Never store plaintext in logs.

### 6.2 Database
- Always add indexes on foreign keys and query columns.
- Always use `ondelete="CASCADE"` or `SET NULL` on FKs.
- Always use `nullable=False` unless truly optional.
- Always use `default=now_utc` for timestamps.
- Always use `uuid.uuid4()` for IDs.
- Never add/remove columns without a migration.

### 6.3 API
- Always use Pydantic schemas for request/response.
- Always use `response_model` on router decorators.
- Always validate ownership before returning data.
- Always return `MessageOut` for simple messages.
- Always use `429` for rate limits, `401` for auth, `403` for forbidden, `404` for not found, `422` for validation.

### 6.4 Frontend
- Always use the `api` client (never raw `fetch`).
- Always use `useToast` for errors.
- Always use `Loading` for loading states.
- Always use `lucide-react` for icons.
- Always use Tailwind classes (never inline styles).
- Always add `try/catch` around API calls.
- Always clean up `useEffect` listeners.
- Never add new dependencies without approval.
- Never block native browser shortcuts in `KeyboardShortcuts`.

### 6.5 Security
- Never return plaintext passwords in API responses.
- Never log tokens, secrets, or credentials.
- Always encrypt sensitive fields at rest (use `api.services.crypto`).
- Always validate tokens before use and mark them as used immediately.
- Always rate-limit public endpoints (SSO, login, password reset).
- Always validate input with Pydantic schemas.
- Never allow open redirects.
- Never allow SQL injection (use SQLAlchemy ORM, never raw SQL).

### 6.6 Testing
- Add a test for every new backend endpoint.
- Add a test for every new frontend page component.
- Run `pytest` in `backend/` before committing.
- Run `npm run build` in `frontend/` before committing.
- Never commit without running the test suite.

---

*Document compiled from the previous agent session's "Remaining Notes" and the existing codebase patterns. All tasks are specific, actionable, and have clear guardrails.*
