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
