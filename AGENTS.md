# Email SaaS Agent Memory

## Project Overview
- FastAPI + SQLAlchemy 2.0 backend, React + Vite + Tailwind frontend, PostgreSQL + Stalwart mail server
- Authentication: JWT + OAuth2 + TOTP + recovery codes + WebAuthn (passkeys)
- Payments: Stripe webhooks
- Support: ticket system with public/internal comments
- Admin panel with RBAC

## Backend Conventions
- All routes under `/api/v1/` registered in `main.py`
- SQLAlchemy 2.0 style: `Mapped[T]` + `mapped_column(...)`
- Relationships need explicit `foreign_keys` when multiple FK paths exist (e.g., Domain/Mailbox)
- Models use `Base` from `api.database` with `AsyncSession` fixtures
- Tests: `pytest-asyncio` strict mode, async fixtures with `yield`
- RLS-style filtering: endpoints must filter by `account_id` from the current token

## Frontend Conventions
- React Router v6, `react-router-dom` `NavLink` for navigation
- API client: `axios` instance exported from `api/client.ts`
- Icons: `lucide-react`
- Styling: Tailwind CSS with custom color tokens (`bg-surface`, `text-accent`, `btn-primary`, etc.)
- Toast notifications via `useToast()` context
- Pages are stateful functional components with `useEffect` for data loading

## Router/Model Implementation Patterns
- CRUD routers follow consistent pattern: `POST /`, `GET /`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`
- Account-scoped routers use `get_account(db_session, token)` to resolve the current user
- All queries include `.where(Account.id == account_id)` for security
- 404 returned when cross-account access is attempted (do not leak existence)
- Use `selectinload` for eager-loading relationships when needed

## Foreign Key Ambiguity Fix
- When a model has two FKs to the same parent (e.g., `Domain` has `catch_all_mailbox_id` and `mailboxes` list), SQLAlchemy needs `foreign_keys` specified on both sides:
  ```python
  # Domain side
  mailboxes: Mapped[list["Mailbox"]] = relationship(
      "Mailbox", back_populates="domain", foreign_keys="Mailbox.domain_id"
  )
  # Mailbox side
  domain: Mapped["Domain | None"] = relationship(
      "Domain", back_populates="mailboxes", foreign_keys="Mailbox.domain_id"
  )
  ```

## Frontend Page Creation Pattern
- Add import in `App.tsx`
- Add `<Route>` inside the `<Layout>` wrapper
- Add nav item in `Sidebar.tsx` (with `lucide-react` icon)
- Page component: state for list, loading, form visibility; `useEffect` calls `load()`
- Use consistent card/table styling from existing pages (e.g., `BlockedSendersPage`)

## Build Commands
- Backend: `cd backend && uv run pytest` (requires `uv` + Python 3.12)
- Frontend: `cd frontend && npm run build` (requires Node.js + npm deps)

## Dependencies Added
- `aiosqlite==0.22.1` — test SQLite async driver
- `pytest-timeout==2.4.0` — pytest timeout plugin

---

## Environment Setup (Done 2026-06-03)

### Docker Containers
| Container | Image | Status | Ports |
|-----------|-------|--------|-------|
| `test-postgres` | postgres:16 | Up (36+ min) | 0.0.0.0:5432 |
| `email_saas_redis` | redis:7.4.9 | Up (healthy) | 127.0.0.1:6379 |

> **Note:** `email_saas_postgres` (postgres:17.10) is stuck in `Created` state due to port 5432 conflict with `test-postgres`. The `test-postgres` container is the active database.

### `.env` File Created
Path: `/home/sean/repos/email-saas/.env`
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/email_saas
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=local-dev-secret-key-change-me-in-production-123456789
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ADMIN_2FA_REQUIRED=true
ENVIRONMENT=development
DOCS_ENABLED=true
ROUNDCUBE_BASE_URL=http://localhost/roundcube
API_KEY_SECRET=local-dev-api-key-secret-123456789
STRIPE_SECRET_KEY=sk_test_placeholder
STRIPE_PUBLISHABLE_KEY=pk_test_placeholder
STRIPE_WEBHOOK_SECRET=whsec_placeholder
STRIPE_PRICE_ID=price_placeholder
STALWART_BASE_URL=http://localhost:8080
STALWART_API_TOKEN=stalwart-test-token
FRONTEND_URL=http://localhost:5173
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@mg.example.com
SMTP_PASSWORD=mailgun-api-key
NOTIFICATION_FROM=noreply@example.com
FIRST_ADMIN_EMAIL=admin@example.com
FIRST_ADMIN_PASSWORD=changeme-strong-password
VPS2_PUBLIC_IP=127.0.0.1
VPS1_WG_IP=10.0.0.1
VPS2_WG_IP=10.0.0.2
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRES_DB=email_saas
```

### Verified Dependency Versions
| Component | Version |
|-----------|---------|
| Python | 3.12.13 |
| FastAPI | 0.136.3 |
| SQLAlchemy | 2.0.50 |
| asyncpg | 0.31.0 |
| redis-py | 5.2.1 |
| Pydantic | 2.13.4 |
| pydantic-settings | 2.14.1 |
| Node.js | 22.22.1 |
| npm | 9.2.0 |
| PostgreSQL (server) | 16 |
| Redis (server) | 7.4.9 |
| Alembic revision | 009 (head) |

### Backend Tests
- **53 passed, 53 warnings** in 16.72s
- Warnings: `SAWarning` about unresolvable foreign key cycle between `domains` and `mailboxes` tables (harmless for test SQLite)

### Frontend Build
- `npm run build` passes cleanly
- Output: 515.61 KB JS + 28.49 KB CSS
- Build time: 1.49s
- Chunk size warning for >500 KB (not critical)

---

## Remaining Tasks (from TASKS.md)

### ✅ Task 1: Apply All Pending Database Migrations
**Status:** DONE — alembic at revision 009
- All tables verified: `calendar_events`, `import_jobs`, `export_jobs`, `webmail_tokens`, `contacts.is_vip`, `accounts.sieve_script`

### ✅ Task 2: Fix Frontend Build / Verify TypeScript
**Status:** DONE — `npm run build` passes
- `node_modules` was already present and complete
- No TypeScript errors
- All routes, icons, contexts verified

### ✅ Task 3: Verify Backend Router Registration & Imports
**Status:** DONE — routers verified in main.py
- All new routers imported: `calendar`, `search`, `import_jobs`, `export_jobs`, `email_rules`, `passkeys`, `sessions`
- Backend boots and tests pass

### ⚠️ Task 4: Search Backend — Replace ILIKE with PostgreSQL Full-Text Search
**Status:** PUSHED BACK / DEFERRED
- Reason: Cost/benefit and scaling concerns with two-server deployment
- Current implementation uses simple `ILIKE` (works for small datasets)
- When ready: add `tsvector` columns, GIN indexes, `to_tsvector`/`plainto_tsquery`
- Needs migration for schema changes

### 🔵 Task 5: Import/Export — Implement Real Background Workers
**Status:** IN PROGRESS
- Current code: `background_tasks.add_task` stubs in `import_jobs.py` and `export_jobs.py`
- Need to replace with real Redis-backed worker
- **Backend work:**
  1. Create `background_worker.py` module (using `celery` or `arq` or simple Redis queue)
  2. Implement IMAP import via `imaplib` or `aiosmtplib` — fetch batches, save to Stalwart via JMAP
  3. Implement export — generate MBOX/ICS/vCard, write to temp, stream or S3
  4. Update `import_jobs.py` to kick off worker instead of `background_tasks`
  5. Update `export_jobs.py` similarly
  6. Add progress polling (`GET /api/v1/import/{id}`, `GET /api/v1/export/{id}`)
  7. Add retry mechanism for failed jobs
- **Security guardrails:**
  - Encrypt `password` field in `ImportJob` using `api.services.crypto`
  - Never log IMAP credentials
  - Validate IMAP server hostname before connecting
  - Add audit logging on start
- **Dependencies:** Redis already installed and running

### 🔵 Task 7: Dark Mode — Verify CSS Coverage & Accessibility
**Status:** IN PROGRESS
- Need to audit all pages for missing `dark:` class coverage
- Check `index.css` dark mode variables apply to custom components
- Verify `html.dark` class toggled on `<html>` by `ThemeContext`
- Add `prefers-color-scheme: dark` fallback
- Ensure focus rings/active states visible in dark mode
- Verify theme toggle accessibility (aria-label, keyboard focus)
- Add `theme-color` meta tag to `index.html`
- **Guardrails:** Never use inline styles; use CSS variables or Tailwind dark mode

### ⚠️ Task 6: Roundcube SSO — Configure Production URL & Plugin
**Status:** PENDING
- Need real `roundcube_base_url` in production
- Create PHP Roundcube plugin for token-based SSO
- Ensure token is single-use, 5-min expiry, invalidated after use
- Add rate limiting to `POST /api/v1/auth/webmail-sso` (5 req/min/IP)
- **Security:** Never return plaintext password; validate token against `WebmailToken` table; mark as used immediately; never log token value

### ⚠️ Task 8: Keyboard Shortcuts — Resolve Conflicts & Add Missing Shortcuts
**Status:** PENDING
- Ensure `KeyboardShortcuts.tsx` does not intercept `Escape` when modal open
- Ensure `/` not intercepted when user in text input
- Ensure `g` sequences don't interfere with `Ctrl+G`
- Add missing `g` shortcuts: `g i` Import, `g e` Export, `g f` Files, `g n` Notes, `g p` Passkeys, `g l` Login Logs, `g u` Outbox, `g z` Snooze, `g v` Vacation Response, `g r` Email Rules
- Add `n t` for "Toggle notifications"
- Verify `/` focuses SearchBar
- Verify `?` help overlay lists all current shortcuts

### ⚠️ Task 9: Search Frontend — Add Mobile Layout & Keyboard Navigation
**Status:** PENDING
- Collapse `SearchBar.tsx` to icon on mobile, expand on tap
- Add keyboard navigation in results dropdown (Up/Down, Enter, Escape)
- Add "No results" and loading states
- Ensure overlay does not block sidebar on mobile
- Verify 300ms debounce
- Ensure `scope` tabs are scrollable on mobile

### ⚠️ Task 10: Calendar — Sync with Stalwart CalDAV
**Status:** PENDING
- Sync `CalendarEvent` to Stalwart via CalDAV (or JMAP for Calendars)
- Push create/update/delete to Stalwart
- Prefer Stalwart as source of truth on read, cache in PostgreSQL
- Add background sync job pulling from Stalwart periodically
- Handle recurrence rules (`recurrence_rule` field)
- Handle ICS invitations (`METHOD:REQUEST`)
- **Guardrails:** Handle CalDAV errors gracefully; use `settings` for URL; never expose admin credentials

### ⚠️ Task 11: VIP Notifications — Wire to Desktop Notifications
**Status:** PENDING
- Backend: include `vip: true` flag when message from `Contact.is_vip=True`
- Frontend: check VIP flag when `DesktopNotifications` enabled; if "VIP only" mode, only show VIP notifications
- Add "VIP only" toggle in `SettingsPage.tsx` under Notifications
- Persist `vip_notifications_only` in `localStorage`
- Add Web Push subscription endpoint filtering by VIP status

### ⚠️ Task 12: Sieve Editor — Add Syntax Highlighting
**Status:** PENDING
- Replace plain `<textarea>` in `EmailRulesPage.tsx` with lightweight code editor
- Use `prismjs` with custom Sieve grammar (keywords: `require`, `if`, `elsif`, `else`, `fileinto`, `reject`, `discard`, `keep`, `stop`, `redirect`, `vacation`, `allof`, `anyof`, `not`, `header`, `address`, `envelope`, `size`, `body`)
- Editor at least 20 rows tall
- Keep validate/save/reset buttons
- Ensure dark mode and accessibility
- **Guardrails:** Do not add heavy dependencies (Monaco); keep bundle small

### ⚠️ Task 13: Custom Webmail (Inbox) — Planning Only
**Status:** P3 (do not implement)
- 6-12 month project to replace Roundcube
- Plan: JMAP API client, thread view, compose UI, attachments, drag-and-drop, search, filters
- Write as separate PRD when ready

---

## Known Issues

1. **Port conflict:** `email_saas_postgres` (postgres:17.10) cannot start because `test-postgres` (postgres:16) already binds port 5432. If upgrading to postgres:17.10 is required, either stop `test-postgres` or remap `email_saas_postgres` to a different host port.

2. **Audit log FK violation:** When inserting into `audit_log`, ensure the referenced `account_id` exists in the `accounts` table. This was observed during manual database inspection. The application code should handle this naturally during normal API flows (auth creates account first), but direct SQL inserts may fail.

3. **SAWarning in tests:** `Can't sort tables for DROP; an unresolvable foreign key dependency exists between tables: domains, mailboxes` — This is a test-only warning when using SQLite with `DROP` for test isolation. It does not affect PostgreSQL production.

4. **Chunk size warning:** Frontend build produces a 515 KB JS chunk. This is acceptable for now but can be optimized with dynamic imports if needed.

---

## Quick Commands for Next Agent

```bash
# Check containers
docker ps --filter name=postgres --filter name=redis

# Run backend tests
cd /home/sean/repos/email-saas/backend && uv run pytest

# Run frontend build
cd /home/sean/repos/email-saas/frontend && npm run build

# Check alembic status
cd /home/sean/repos/email-saas/backend && ALEMBIC_CONFIG=migrations/alembic.ini alembic current

# Start backend dev server
cd /home/sean/repos/email-saas/backend && uv run python -m uvicorn api.main:app --reload --port 8000

# Start frontend dev server
cd /home/sean/repos/email-saas/frontend && npm run dev

# Test Redis connectivity
cd /home/sean/repos/email-saas/backend && python -c "import redis; r = redis.Redis.from_url('redis://localhost:6379/0', decode_responses=True); print(r.ping())"

# Test DB connectivity
cd /home/sean/repos/email-saas/backend && python -c "
import os, asyncio
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://user:pass@localhost:5432/email_saas'
os.environ['SECRET_KEY'] = 'test'
from api.db import async_session_maker
async def test(): async with async_session_maker() as s: from sqlalchemy import text; r = await s.execute(text('SELECT 1')); print('DB OK:', r.scalar())
asyncio.run(test())
"
```

---

## Current Context (User Preferences)

- **Task 4 (Search additions)** was **pushed back** by user due to cost/benefit and scaling concerns. Do not implement unless explicitly re-approved.
- **Task 5 (Redis Background Workers)** and **Task 7 (Dark Mode CSS)** were **approved** and are in-progress.
- **Environment:** WSL2 (Linux kernel 6.6.114.1-microsoft-standard-WSL2)
- **Database:** PostgreSQL 16 (test-postgres container), not 17.10
- **All 11 coding-plan features** are implemented (catch-all, dark mode, calendar, keyboard shortcuts, search, desktop notifications, VIP contacts, import, export, sieve editor, Roundcube SSO). Remaining work is cleanup, stabilization, and production-readiness.
