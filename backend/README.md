# Email SaaS Backend API

FastAPI-based async backend for the email SaaS platform.

## Quick Start

1. Create a virtual environment:
   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Copy and configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your secrets
   ```

4. Run migrations:
   ```bash
   alembic -c migrations/alembic.ini upgrade head
   ```

5. Seed the first admin (optional):
   ```bash
   python scripts/seed_admin.py
   ```

6. Start the server:
   ```bash
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Running Tests

```bash
pytest tests/ -v
```

Tests use an in-memory SQLite database via `aiosqlite` for speed.

## API Structure

- `/api/v1/auth` — Register, login, logout, password change, TOTP
- `/api/v1/stripe` — Checkout, portal, webhooks
- `/api/v1/domains` — Domain management & DNS verification
- `/api/v1/mailboxes` — Mailbox CRUD
- `/api/v1/tickets` — Customer & staff ticket system
- `/api/v1/admin` — Dashboard, impersonation, stats, audit log
- `/api/v1/api-keys` — Scoped API key management
- `/api/v1/health` — Health check

## Key Design Decisions

- **Application-level tenant scoping:** Every repository query filters by `account_id` from the authenticated context. Cross-tenant access attempts are blocked by endpoint tests.
- **Audit**: Mutating HTTP requests are logged to `audit_log` via middleware.
- **Auth**: JWT + optional API keys. Admin endpoints require TOTP when `ADMIN_2FA_REQUIRED=true`.
- **Impersonation**: Short-lived JWTs (15 min) with Redis tracking and audit logging.
- **Stripe**: Webhooks idempotent via `stripe_event_id` in provisioning job payloads.
