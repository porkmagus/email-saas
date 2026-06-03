# Email SaaS Critique Remediation Plan

**Date:** 2026-06-03
**Source:** Third-party technical critique (34KB, 1240 lines, 22 sections)
**Status:** All concerns verified legitimate
**Recommendation:** Implement in 5 phases before any public launch

---

## Verified Concerns Summary

| # | Concern | Severity | Verified In Code |
|---|---------|----------|-------------------|
| 1 | "RLS" is application-level filtering, not PostgreSQL RLS | Critical | `api/routers/*.py` uses `where(Domain.account_id == account.id)` — no DB policies |
| 2 | SPF record example is invalid (`include:mail.{domain}`) | Critical | `domains.py` line 167 |
| 3 | "Unlimited" plan language in frontend | Critical | `LandingPage.tsx` line 55 |
| 4 | API docs (`/docs`, `/openapi.json`) exposed in production | Critical | `main.py` line 114 references `/docs` |
| 5 | Missing CSP header | Critical | `vps1.conf` has no `Content-Security-Policy` |
| 6 | Dev dependencies installed in production (`pip install -e ".[dev]"`) | Critical | `docs/SETUP.md` line 90 |
| 7 | No Stripe webhook idempotency table | Critical | `models.py` has no `stripe_events` table |
| 8 | No abuse scoring / send throttling system | Critical | No `outbound_limits`, `abuse_scores` tables |
| 9 | API key storage uses bcrypt instead of HMAC-SHA256 | Warning | `api_keys.py` line 32: `hashed_secret=hash_password(raw)` |
| 10 | No TOTP backup recovery codes | Warning | `Account` model has no `recovery_codes` field |
| 11 | No admin impersonation reason field | Warning | `admin.py` impersonate endpoint has no `reason` parameter |
| 12 | Missing operational email addresses | Warning | `AUPPage.tsx` says `abuse@example.com` |
| 13 | No Contabo send limit awareness (25/min) | Warning | No send rate limiting per account/domain |
| 14 | No DKIM automation per domain | Warning | `domains.py` uses static `default` selector |
| 15 | No PTR/rDNS verification | Warning | Not mentioned in DNS check or onboarding |
| 16 | No IP warm-up limits | Warning | No probationary send limits for new accounts |
| 17 | No backup restore drill documented | Warning | `RUNBOOKS.md` has no restore timing test |
| 18 | No load testing performed | Warning | No k6/locust tests |
| 19 | No PostgreSQL PITR/WAL-G | Warning | `docker-compose.yml` has no WAL archiving |
| 20 | Roundcube SSO incomplete | Warning | `CUSTOMER_SETUP.md` says manual login |
| 21 | Missing mail-specific monitoring | Warning | No bounce rate, complaint rate, queue age alerts |
| 22 | Pricing doesn't reflect real costs | Info | Missing support labor, abuse response, deliverability tooling |
| 23 | Missing customer-facing DNS docs | Info | No provider-specific guides |
| 24 | HSTS preload too early | Info | `vps1.conf` has `preload` without full verification |
| 25 | JWT key rotation not planned | Info | No documented rotation procedure |

---

## Phase 1: Rename "RLS" Honestly (1 hour)

### Goal
Stop misrepresenting application-level filtering as PostgreSQL RLS.

### Tasks
1. Update all documentation:
   - `README.md`: Change "RLS" to "Application-level tenant scoping"
   - `SECURITY.md`: Change "Row-level security (RLS)" to "Application-level tenant filtering enforced through query filters and endpoint tests"
   - `TECHNICAL_REVIEW_DOCUMENT.md`: Fix section 6.4
   - `COMMISSIONING_REPORT.md`: Fix "RLS" references
   - `VERIFICATION.md`: Fix "RLS" references
2. Add code comments in routers:
   - `domains.py`, `mailboxes.py`, `tickets.py`: Change "# RLS:" to "# Tenant scope:"
3. Add `backend/README.md` note explaining the difference

### Files
- `backend/README.md`
- `docs/SECURITY.md`
- `TECHNICAL_REVIEW_DOCUMENT.md`
- `COMMISSIONING_REPORT.md`
- `VERIFICATION.md`
- `backend/api/routers/domains.py`
- `backend/api/routers/mailboxes.py`
- `backend/api/routers/tickets.py`

---

## Phase 2: Fix SPF, Remove "Unlimited", Disable API Docs (2 hours)

### Goal
Fix the three most visible launch-blockers.

### Tasks
1. Fix SPF record in `domains.py`:
   - Change from `v=spf1 include:mail.{domain} ~all` to `v=spf1 ip4:{vps2_ip} -all`
   - Add `VPS2_PUBLIC_IP` to onboarding response
   - Add `vps2_public_ip` to `.env.example`

2. Remove "Unlimited" from frontend:
   - Change `LandingPage.tsx` Enterprise features to concrete limits
   - Add explicit send/storage limits to all plans
   - Add `OUTBOUND_LIMITS` to backend config

3. Disable API docs in production:
   - Add `DOCS_ENABLED` env var to `config.py`
   - Only include `/docs` and `/openapi.json` when `DOCS_ENABLED=true`
   - Default to `false` in production
   - Add `DOCS_ENABLED=false` to `.env.example`

### Files
- `backend/api/routers/domains.py`
- `frontend/src/pages/LandingPage.tsx`
- `backend/api/config.py`
- `backend/api/main.py`
- `backend/.env.example`
- `.env.example`

---

## Phase 3: Add CSP, Fix Production Deploy, Add Stripe Idempotency (4 hours)

### Goal
Fix security and deployment gaps.

### Tasks
1. Add Content-Security-Policy header:
   - Add strict CSP to `vps1.conf` and `vps2.conf`
   - `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://api.qrserver.com; connect-src 'self' https://api.stripe.com; frame-ancestors 'none'; base-uri 'none'; form-action 'self';`

2. Fix production deployment:
   - Change `pip install -e ".[dev]"` to `pip install -e "."` in `SETUP.md`
   - Add `production-requirements.txt` or separate install script
   - Add `scripts/validate_production.py` preflight check
   - Add `scripts/health_check.py` post-deploy smoke test

3. Add Stripe webhook idempotency:
   - Add `StripeEvent` model to `models.py`
   - Add `stripe_events` table with `stripe_event_id` unique constraint
   - Update `stripe.py` router to check idempotency before processing
   - Add `processing_status` enum: received, processing, completed, failed, retrying
   - Log all webhook events to table
   - Add test: `test_stripe_webhook_idempotency.py`

### Files
- `infra/nginx/vps1.conf`
- `infra/nginx/vps2.conf`
- `docs/SETUP.md`
- `backend/api/models.py`
- `backend/api/routers/stripe.py`
- `backend/tests/test_stripe_webhooks.py`
- `backend/scripts/validate_production.py`
- `backend/scripts/health_check.py`

---

## Phase 4: Add Abuse Controls, Send Throttling, API Key HMAC (6 hours)

### Goal
Add the missing operational controls for an email provider.

### Tasks
1. Add `OutboundLimit` model:
   - `account_id`, `domain_id`, `mailbox_id` (nullable, cascade up)
   - `period_start`, `period_end`
   - `emails_sent`, `emails_allowed`
   - `last_reset_at`

2. Add `AbuseScore` model:
   - `account_id`
   - `bounce_rate`, `complaint_rate`, `failed_auth_rate`
   - `send_spike_score`, `suspicious_recipient_score`
   - `blacklist_count`, `total_score`
   - `calculated_at`, `status` (green, yellow, orange, red)

3. Add `SendEvent` model:
   - `account_id`, `domain_id`, `mailbox_id`
   - `recipient_domain`, `recipient_address` (hashed)
   - `status` (sent, bounced, complained, deferred, rejected)
   - `message_size`, `has_attachments`
   - `created_at`

4. Add `SendLimitConfig` to config.py:
   - `NEW_ACCOUNT_DAILY_LIMIT = 25`
   - `WARMED_ACCOUNT_DAILY_LIMIT = 500`
   - `PROBATION_DAYS = 30`
   - `HOURLY_LIMIT_RATIO = 0.1`
   - `CONTABO_MAX_PER_MINUTE = 25`

5. Add `stalwart_send.py` service:
   - Intercept all outgoing mail via Stalwart API
   - Check limits before sending
   - Update counters atomically via Redis
   - Log to `send_events` table

6. Add `abuse_check.py` service:
   - Calculate abuse scores periodically
   - Alert on thresholds
   - Auto-suspend on red scores

7. Fix API key storage:
   - Change `hash_password(raw)` to `hmac.new(settings.api_key_secret, raw.encode(), hashlib.sha256).hexdigest()`
   - Add `API_KEY_SECRET` to config.py
   - Add migration for existing keys (re-hash or require rotation)

8. Add `send_limits` to `Account` model:
   - `daily_send_limit`, `hourly_send_limit`, `current_send_count`
   - Update on each send attempt

### Files
- `backend/api/models.py`
- `backend/api/config.py`
- `backend/api/services/stalwart_send.py`
- `backend/api/services/abuse_check.py`
- `backend/api/routers/api_keys.py`
- `backend/migrations/versions/002_abuse_limits.py`
- `backend/tests/test_send_limits.py`
- `backend/tests/test_abuse_scoring.py`

---

## Phase 5: Add TOTP Recovery, Admin Impersonation Safeguards, Operational Emails (4 hours)

### Goal
Fix authentication and operational gaps.

### Tasks
1. Add TOTP recovery codes:
   - Add `recovery_codes` JSON field to `Account` model (array of 10 hashed codes)
   - Generate on TOTP setup
   - Display once, never again
   - Validate on login if TOTP lost
   - Use `bcrypt` to hash each code
   - Add `POST /auth/totp/recovery` endpoint

2. Add admin impersonation safeguards:
   - Add `reason` parameter to `AdminImpersonateIn` schema
   - Add `impersonation_reason` to `AuditLog` model
   - Add `impersonation_banner` to frontend (visible banner when impersonating)
   - Add `POST /auth/reauth` for destructive actions
   - Add `DESTRUCTIVE_ACTIONS_REAUTH=true` to config

3. Add operational email addresses:
   - Update `AUPPage.tsx` to use real domain
   - Add `OPERATIONAL_DOMAIN` to config
   - Add `abuse@`, `postmaster@`, `security@`, `support@`, `billing@` to DNS docs
   - Add `docs/OPERATIONAL_EMAILS.md`

4. Add DKIM automation per domain:
   - Generate RSA keypair on domain creation
   - Store private key in Stalwart (via API)
   - Store public key in `Domain.dkim_record`
   - Generate unique selector per domain (e.g., `saas2026a`)
   - Add `POST /domains/{id}/rotate-dkim` endpoint
   - Add `Domain.dkim_private_key` (encrypted storage)

5. Add PTR/rDNS check:
   - Add `check_ptr_rdns()` to `dns_check.py`
   - Verify reverse DNS matches `mail.{domain}`
   - Add to onboarding response
   - Alert if mismatch detected

### Files
- `backend/api/models.py`
- `backend/api/schemas.py`
- `backend/api/routers/auth.py`
- `backend/api/routers/admin.py`
- `backend/api/routers/domains.py`
- `backend/api/services/dns_check.py`
- `frontend/src/pages/AupPage.tsx`
- `frontend/src/pages/admin/AdminTicketDetailPage.tsx`
- `backend/migrations/versions/003_recovery_codes_dkim.py`

---

## Phase 6: Add Monitoring, Backup Drills, Load Testing (6 hours)

### Goal
Add operational readiness.

### Tasks
1. Add mail-specific monitoring endpoints:
   - `GET /admin/metrics/queue` — queue depth, age, by destination
   - `GET /admin/metrics/bounces` — bounce rate, complaint rate
   - `GET /admin/metrics/sends` — sends per account/domain/hour
   - `GET /admin/metrics/abuse` — abuse scores

2. Add Prometheus-compatible metrics:
   - `emails_sent_total`, `emails_bounced_total`, `emails_complained_total`
   - `queue_depth`, `queue_age_seconds`
   - `api_requests_total`, `api_errors_total`
   - `auth_failures_total`, `rate_limit_hits_total`

3. Add backup restore drill script:
   - `scripts/restore_drill.py` — restores from Restic to temp directory
   - Verifies PostgreSQL can start with restored data
   - Verifies Stalwart data integrity
   - Reports timing results
   - Runs monthly via cron

4. Add load testing:
   - `tests/load/k6/` directory with k6 scripts
   - `auth_login.js` — 1000 concurrent logins
   - `api_crud.js` — domain/mailbox CRUD under load
   - `webhook_flood.js` — 1000 concurrent webhooks
   - Document expected throughput

5. Add WAL-G configuration:
   - Add `wal-g` to `setup.sh` for VPS-1
   - Configure `postgresql.conf` for WAL archiving
   - Add `scripts/wal_g_backup.sh` hourly cron
   - Add restore documentation to `RUNBOOKS.md`

### Files
- `backend/api/routers/admin.py`
- `backend/api/services/metrics.py`
- `backend/scripts/restore_drill.py`
- `backend/tests/load/k6/*.js`
- `backend/scripts/wal_g_backup.sh`
- `docs/RUNBOOKS.md`
- `infra/cron/wal_g_backup.sh`

---

## Phase 7: Update Legal Docs, Pricing, Customer Guides (4 hours)

### Goal
Make the business defensible.

### Tasks
1. Update legal documents:
   - `TermsPage.tsx` — real terms, not placeholders
   - `PrivacyPage.tsx` — GDPR-compliant, data retention specifics
   - `AUPPage.tsx` — real abuse policy, clear enforcement
   - Add `DPA.md` for enterprise customers
   - Add `REFUND.md` refund policy

2. Update pricing:
   - Change Enterprise to concrete limits
   - Add `PRICING.md` with plan comparison table
   - Add `outbound sending limits` column to landing page
   - Add `storage limits` column to landing page
   - Add `warm-up period` explanation

3. Add customer-facing documentation:
   - `docs/CLIENT_SETUP.md` — IMAP/SMTP settings per client
   - `docs/DNS_SETUP.md` — per-provider DNS guides (Cloudflare, GoDaddy, Namecheap, etc.)
   - `docs/WEBMAIL.md` — Roundcube usage guide
   - `docs/DELIVERABILITY.md` — best practices for customers

4. Add status page:
   - Expand `StatusPage.tsx` to show incident history
   - Add `GET /api/v1/status/history` endpoint
   - Add `MaintenanceWindow` model
   - Add admin ability to schedule maintenance

### Files
- `frontend/src/pages/TermsPage.tsx`
- `frontend/src/pages/PrivacyPage.tsx`
- `frontend/src/pages/AupPage.tsx`
- `frontend/src/pages/LandingPage.tsx`
- `frontend/src/pages/StatusPage.tsx`
- `docs/PRICING.md`
- `docs/CLIENT_SETUP.md`
- `docs/DNS_SETUP.md`
- `docs/WEBMAIL.md`
- `docs/DELIVERABILITY.md`
- `docs/DPA.md`
- `docs/REFUND.md`
- `backend/api/models.py`
- `backend/api/routers/admin.py`

---

## Phase 8: Final Testing and Verification (4 hours)

### Goal
Prove everything works.

### Tasks
1. Run all backend tests
2. Build frontend
3. Run pip-audit and npm audit
4. Run load tests
5. Run backup restore drill
6. Verify DNS records (SPF, DKIM, DMARC, PTR)
7. Test mail send/receive to Gmail, Outlook, Yahoo
8. Test Stripe webhook idempotency
9. Test admin impersonation with reason
10. Test TOTP recovery codes
11. Test abuse scoring
12. Test send throttling
13. Update `TECHNICAL_REVIEW_DOCUMENT.md` with fixes
14. Update `COMMISSIONING_REPORT.md` with new verification

---

## Estimated Timeline

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 1: Rename RLS | 1 hour | 1 hour |
| Phase 2: SPF, Unlimited, API Docs | 2 hours | 3 hours |
| Phase 3: CSP, Deploy, Stripe | 4 hours | 7 hours |
| Phase 4: Abuse, Throttling, API Keys | 6 hours | 13 hours |
| Phase 5: TOTP, Admin, DKIM, PTR | 4 hours | 17 hours |
| Phase 6: Monitoring, Backup, Load | 6 hours | 23 hours |
| Phase 7: Legal, Pricing, Guides | 4 hours | 27 hours |
| Phase 8: Testing | 4 hours | 31 hours |
| **Total** | **31 hours** | |

---

## Files Likely to Change

**Backend (16+ files):**
- `api/models.py` — Add 5+ models (StripeEvent, OutboundLimit, AbuseScore, SendEvent, MaintenanceWindow)
- `api/schemas.py` — Add schemas for new models
- `api/config.py` — Add 10+ new config values
- `api/main.py` — Conditional docs, metrics endpoint
- `api/routers/domains.py` — Fix SPF, add DKIM automation
- `api/routers/stripe.py` — Add idempotency
- `api/routers/admin.py` — Add metrics, impersonation reason
- `api/routers/auth.py` — Add recovery codes
- `api/routers/api_keys.py` — Fix HMAC storage
- `api/routers/mailboxes.py` — Add send throttling
- `api/services/dns_check.py` — Add PTR check
- `api/services/stalwart_send.py` — New file
- `api/services/abuse_check.py` — New file
- `api/services/metrics.py` — New file
- `migrations/versions/002_abuse_limits.py` — New migration
- `migrations/versions/003_recovery_codes_dkim.py` — New migration
- `tests/test_send_limits.py` — New test
- `tests/test_abuse_scoring.py` — New test
- `tests/test_stripe_webhooks.py` — Add idempotency test
- `scripts/validate_production.py` — New script
- `scripts/health_check.py` — New script
- `scripts/restore_drill.py` — New script
- `scripts/wal_g_backup.sh` — New script

**Frontend (5+ files):**
- `src/pages/LandingPage.tsx` — Remove unlimited, add limits
- `src/pages/TermsPage.tsx` — Real terms
- `src/pages/PrivacyPage.tsx` — GDPR compliance
- `src/pages/AupPage.tsx` — Real AUP
- `src/pages/StatusPage.tsx` — Incident history
- `src/pages/admin/AdminTicketDetailPage.tsx` — Impersonation banner

**Infrastructure (3+ files):**
- `infra/nginx/vps1.conf` — Add CSP
- `infra/nginx/vps2.conf` — Add CSP
- `infra/cron/wal_g_backup.sh` — New cron
- `docs/SETUP.md` — Fix dev dependency install
- `docs/SECURITY.md` — Fix RLS wording
- `docs/RUNBOOKS.md` — Add restore drill
- `docs/PRICING.md` — New file
- `docs/CLIENT_SETUP.md` — New file
- `docs/DNS_SETUP.md` — New file
- `docs/WEBMAIL.md` — New file
- `docs/DELIVERABILITY.md` — New file
- `docs/DPA.md` — New file
- `docs/REFUND.md` — New file
- `docs/OPERATIONAL_EMAILS.md` — New file

**Documentation (5+ files):**
- `README.md` — Fix RLS wording
- `TECHNICAL_REVIEW_DOCUMENT.md` — Update with fixes
- `COMMISSIONING_REPORT.md` — Update with new verification
- `VERIFICATION.md` — Update with new tests
- `CODE_REVIEW.md` — Add remediation notes

---

## Risks and Trade-offs

| Risk | Mitigation |
|------|------------|
| Adding 5+ models may break existing tests | Run full test suite after each migration |
| API key HMAC migration breaks existing keys | Require rotation on first use after deploy |
| Send throttling may block legitimate bulk mail | Allow admin override, exempt warmed accounts |
| DKIM automation requires RSA key generation | Use Python `cryptography` library, async task |
| 31-hour estimate may be optimistic | Prioritize phases, defer Phase 7 if needed |
| Contabo 25/min limit may surprise customers | Document clearly in onboarding and pricing |

---

## Open Questions

1. Should we implement real PostgreSQL RLS (Phase 9) or keep application-level filtering?
2. Should we add Cloudflare for DDoS protection before launch?
3. Should we use a dedicated IP from day 1, or migrate later?
4. What's the budget for deliverability tooling (GlockApps, Mailgun, etc.)?
5. Should we support reseller/white-label in Phase 1 or defer?

---

## GO/NO-GO Decision

**Current state:** Private beta only. Public launch blocked.
**After Phase 1-3:** Staging deployment safe.
**After Phase 1-6:** Private beta with trusted users.
**After Phase 1-8:** Public paid launch possible.

---

**END OF PLAN**
