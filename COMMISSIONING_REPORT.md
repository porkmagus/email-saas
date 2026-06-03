# Pre-Ship Commissioning Report

**Project:** Email SaaS Provider
**Date:** 2026-06-03
**Reviewer:** Samantha (autonomous)
**Status:** ✅ PASSED

---

## 1. Executive Summary

The Email SaaS codebase has been subjected to a comprehensive pre-ship commissioning review. All critical issues identified during the code review phase have been resolved. The application is now ready for deployment with the following qualification:

- **Backend:** 31/31 tests passing, 0 known vulnerabilities
- **Frontend:** 0 build errors, 0 npm audit vulnerabilities
- **Docker:** Both images build cleanly
- **Security:** No hardcoded secrets, no SQL injection vectors, rate limiting active
- **Code Quality:** All TODOs/FIXMEs removed, strict type checking enforced

---

## 2. Review Scope

### Backend (25 Python files)
- `api/main.py` — FastAPI app, CORS, middleware, rate limiting
- `api/config.py` — Settings with `secrets.token_urlsafe(32)` default
- `api/deps.py` — Auth, Redis singleton pool, role guards
- `api/models.py` — 13 SQLAlchemy models with enums
- `api/schemas.py` — Pydantic v2 with generic `PaginatedResponse[T]`
- `api/routers/` — 7 routers (auth, stripe, domains, mailboxes, admin, tickets, api_keys)
- `api/services/` — 6 services (audit, dns_check, provision, stalwart_api, stripe_client, ticket_notify)
- `tests/` — 31 tests covering auth, RLS, admin, tickets, API keys, Stripe webhooks

### Frontend (36 TSX/TS files)
- React 19 + Vite + TailwindCSS + TypeScript strict mode
- 22 pages (landing, auth, portal, admin, tickets, legal, status)
- API client with `CustomEvent("unauthorized")` dispatch
- ESLint 9 + React Hooks + React Refresh rules

### Infrastructure (25 config/script files)
- Nginx configs (VPS-1, VPS-2, local)
- Stalwart install script
- WireGuard setup
- VPS hardening (UFW, Fail2ban, SSH, logrotate)
- Systemd services
- Backup scripts (Restic)
- Blacklist monitoring
- Docker Compose (PostgreSQL 17.10, Redis 7.4.9, backend, frontend)

### Documentation (7 markdown files)
- README.md, SETUP.md, OPS.md, RUNBOOKS.md, CUSTOMER_SETUP.md, SECURITY.md, VERIFICATION.md, CODE_REVIEW.md

---

## 3. Critical Issues Fixed (Post-Code-Review)

| # | Issue | Severity | Fix |
|---|-------|----------|-----|
| 1 | Provisioning job stored plaintext passwords | **CRITICAL** | Removed password from job payload; direct synchronous Stalwart creation in API endpoints |
| 2 | Redis connection leak in `get_redis()` | **CRITICAL** | Singleton `_redis_pool` + `FakeRedis` test double |
| 3 | Dead `passlib[bcrypt]` dependency | **CRITICAL** | Removed; direct `bcrypt` usage |
| 4 | Python version constraint too broad | **CRITICAL** | Tightened to `>=3.11.0,<3.14.0` |
| 5 | Audit middleware missing `account_id` | **WARNING** | `request.state.account_id` set in auth, read in middleware |
| 6 | Role string comparison in `tickets.py` | **WARNING** | `AccountRole` enum comparison |
| 7 | Mailbox delete lazy-load risk | **WARNING** | Domain lookup added before Stalwart delete call |
| 8 | Unused `zustand` dependency | **WARNING** | Removed from `package.json` |
| 9 | Missing ESLint config | **WARNING** | Created `eslint.config.js` with React hooks/refresh rules |
| 10 | 401 handler used full page reload | **WARNING** | `CustomEvent("unauthorized")` dispatch for React routing |
| 11 | Docker Compose frontend bound to all interfaces | **INFO** | Changed to `127.0.0.1:80:80` |
| 12 | Predictable default secret key | **INFO** | `secrets.token_urlsafe(32)` |
| 13 | `PaginatedResponse` too generic | **INFO** | `PaginatedResponse[T]` with type parameters |
| 14 | Vulnerable dependencies | **INFO** | Updated: vite 6.4.3, axios 1.17.0, react-router-dom 7.16.0, eslint 9.39.4, python-multipart 0.0.27, pytest 9.0.3 |

---

## 4. Pre-Ship Commissioning Fixes

| # | Issue | Severity | Fix |
|---|-------|----------|-----|
| 15 | `admin.py` `get_stats` used `Ticket.status == "open"` (string) | **WARNING** | Changed to `TicketStatus.open` enum |
| 16 | `admin.py` `list_accounts` missing ordering | **WARNING** | Added `order_by(Account.created_at.desc())` |
| 17 | `admin.py` `list_jobs` missing ordering | **WARNING** | Added `order_by(ProvisioningJob.created_at.desc())` |
| 18 | `admin.py` `get_stats` used `Subscription.status == "active"` (string) | **WARNING** | Changed to `SubscriptionStatus.active` enum |
| 19 | `domains.py` didn't create domain in Stalwart synchronously | **WARNING** | Added direct `stalwart_create_domain()` call with fallback job logging |
| 20 | `provision.py` worker referenced obsolete `payload["domain"]`/`payload["password"]` | **WARNING** | Updated to handle new payload format with DB lookups and clear error messages |

---

## 5. Verification Results

### Backend Tests
```
31 passed in 7.74s
- test_admin.py (6 tests)
- test_api_keys.py (3 tests)
- test_auth.py (7 tests)
- test_rls.py (3 tests)
- test_stripe_webhooks.py (2 tests)
- test_tickets.py (10 tests)
```

### Frontend Build
```
✓ built in 812ms
dist/assets/index-B5IyJPFC.js   394.32 kB │ gzip: 112.81 kB
dist/assets/index-B2xQQJwu.css   24.01 kB │ gzip:   5.27 kB
```

### Security Audit
```
pip-audit: 0 vulnerabilities
npm audit:  0 vulnerabilities
No hardcoded secrets found
No SQL injection vectors found
No TODOs/FIXMEs in application code
```

### Docker Builds
```
email-saas-backend:final  — OK
email-saas-frontend:final — OK
```

---

## 6. Architecture Verification

| Component | Status |
|-----------|--------|
| **VPS-1 (App)** | FastAPI + PostgreSQL + Redis + Stripe + Nginx + React SPA |
| **VPS-2 (Mail)** | Stalwart Mail Server + Roundcube + Nginx + PHP-FPM |
| **WireGuard** | Private tunnel between VPSs (10.0.0.0/24) |
| **SSL** | Certbot + Let's Encrypt (TLS 1.2/1.3) |
| **Rate Limiting** | Nginx limit_req + Slowapi (Redis-backed) |
| **Auth** | JWT + OAuth2 + TOTP 2FA + API Keys |
| **RBAC** | customer / admin / superadmin |
| **RLS** | Active on all customer queries |
| **Audit** | HTTP middleware + explicit service calls |
| **Backups** | Restic 0.18.1 + PostgreSQL PITR |

---

## 7. API Contract Alignment

| Backend Endpoint | Frontend Page | Status |
|------------------|---------------|--------|
| `POST /auth/register` | `/register` | ✅ |
| `POST /auth/login` | `/login` | ✅ |
| `POST /auth/totp/setup` | `/settings` | ✅ |
| `GET /auth/me` | All authenticated pages | ✅ |
| `GET /domains` | `/domains` | ✅ |
| `POST /domains` | `/domains` | ✅ |
| `POST /domains/{id}/verify` | `/domains` | ✅ |
| `GET /domains/{id}/onboarding` | `/domains` | ✅ |
| `GET /mailboxes` | `/mailboxes` | ✅ |
| `POST /mailboxes` | `/mailboxes` | ✅ |
| `PATCH /mailboxes/{id}` | `/mailboxes` | ✅ |
| `DELETE /mailboxes/{id}` | `/mailboxes` | ✅ |
| `POST /stripe/checkout` | `/billing` | ✅ |
| `POST /stripe/portal` | `/billing` | ✅ |
| `GET /tickets` | `/tickets` | ✅ |
| `POST /tickets` | `/tickets` | ✅ |
| `GET /tickets/{id}` | `/tickets/:id` | ✅ |
| `POST /tickets/{id}/comments` | `/tickets/:id` | ✅ |
| `GET /api-keys` | `/settings` | ✅ |
| `POST /api-keys` | `/settings` | ✅ |
| `DELETE /api-keys/{id}` | `/settings` | ✅ |
| `GET /admin/stats` | `/admin` | ✅ |
| `GET /admin/accounts` | `/admin/customers` | ✅ |
| `GET /admin/accounts/{id}` | `/admin/customers/:id` | ✅ |
| `GET /admin/accounts/{id}/impersonate` | Admin actions | ✅ |
| `POST /admin/accounts/{id}/suspend` | Admin actions | ✅ |
| `GET /admin/jobs` | `/admin/jobs` | ✅ |
| `GET /admin/audit-log` | `/admin/audit-log` | ✅ |
| `GET /api/v1/health` | `/status` | ✅ |

---

## 8. Known Limitations (Not Blockers)

1. **Stalwart provisioning retry jobs** — If synchronous mailbox/domain creation fails, a failed provisioning job is logged. The worker cannot retry mailbox creation without the plaintext password (by design). Manual intervention or a secure password vault integration would be needed for retries.

2. **Stripe webhooks** — Tested with mocked signatures. Real Stripe webhook signature verification requires live `STRIPE_WEBHOOK_SECRET`.

3. **DNS verification** — Uses `dns.resolver` (real DNS queries). In local dev, DNS propagation may cause verification delays.

4. **SMTP notifications** — `ticket_notify.py` is stubbed for Slack only. Email notifications require Mailgun/SendGrid/AWS SES config.

5. **Stalwart API** — HTTP client uses mocked responses in tests. Real Stalwart API requires VPS-2 installation.

---

## 9. Deployment Checklist

- [ ] Provision two Contabo VPS instances with Ubuntu 24.04 LTS
- [ ] Clone repo to `/opt/email-saas` on both VPSs
- [ ] Run `ROLE=app ./setup.sh` on VPS-1, `ROLE=mail ./setup.sh` on VPS-2
- [ ] Configure WireGuard between VPSs
- [ ] Run `certbot` on both VPSs for SSL certificates
- [ ] Create `.env` on VPS-1 with all required secrets
- [ ] Run `alembic upgrade head` on VPS-1
- [ ] Run `python scripts/seed_admin.py` on VPS-1
- [ ] Build frontend and copy `dist/` to `/var/www/app/`
- [ ] Configure Stalwart API token in `.env`
- [ ] Configure DNS records (A, MX, CNAME, TXT)
- [ ] Verify end-to-end: register → checkout → add domain → verify → create mailbox → send test email
- [ ] Configure backups (`restic init` with S3/Wasabi credentials)
- [ ] Enable monitoring (Uptime Kuma on port 3001)
- [ ] Run `fail2ban-client status` to verify active jails

---

## 10. Sign-Off

**Commissioned by:** Samantha
**Date:** 2026-06-03
**Result:** ✅ PASSED

The Email SaaS codebase meets strict high-quality standards. All critical and warning issues have been resolved. Tests pass. Builds are clean. No known vulnerabilities. The application is ready for deployment.

---

**Files Modified During Commissioning:**
- `backend/api/routers/mailboxes.py` — synchronous Stalwart create/delete
- `backend/api/routers/domains.py` — synchronous Stalwart create
- `backend/api/routers/admin.py` — enum comparisons, ordering
- `backend/api/routers/tickets.py` — enum role comparison
- `backend/api/deps.py` — Redis singleton, `request.state` for audit
- `backend/api/main.py` — audit middleware with `request.state`
- `backend/api/services/provision.py` — updated worker for new payloads
- `backend/api/schemas.py` — generic `PaginatedResponse[T]`
- `backend/api/config.py` — `secrets.token_urlsafe(32)`
- `backend/pyproject.toml` — version pinning, Python constraint
- `frontend/package.json` — updated deps, removed zustand
- `frontend/eslint.config.js` — new file
- `frontend/src/api/client.ts` — `CustomEvent` dispatch
- `docker-compose.yml` — `127.0.0.1` binding
- `infra/nginx/vps1.conf` — docs access note
