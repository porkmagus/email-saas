# Security Documentation

## Security Posture

### Authentication

- **JWT-based sessions** with `HS256` signing and configurable expiration
- **Password hashing** via bcrypt (Passlib)
- **2FA/TOTP** mandatory for admin and superadmin roles; optional for customers
- **API keys** with scoped permissions (`smtp`, `imap`, `api_read`, `api_write`)
- **Session tracking** in Redis with explicit revocation support
- **Admin impersonation** generates short-lived tokens (15 min) and logs all actions

### Authorization

- **Role-based access control (RBAC)**:
  - `customer` — own account only
  - `admin` — full customer directory, tickets, refunds
  - `superadmin` — staff management, destructive ops
- **Application-level tenant filtering** enforced through query filters and endpoint tests:
  - Every DB query auto-injected with `account_id` from authenticated context
  - Raw `account_id` never accepted from client body
  - Cross-tenant access attempts return 403
  - **Note:** This is application-level filtering, not PostgreSQL row-level security policies.
- **API key scope enforcement**:
  - Keys with `smtp` only cannot call `DELETE /mailboxes`
  - Scopes checked at route level

### Audit Logging

Every mutating request is logged to the `audit_log` table:

- `actor_id` / `actor_type` (user, admin, system, impersonation)
- `action` (e.g., `POST /api/v1/mailboxes`)
- `resource_type` and `resource_id`
- `ip_address` and `user_agent`
- `metadata` (JSON, includes duration and status code)

Admin impersonation actions are tagged with `actor_type=impersonation` and include the original admin ID.

### Infrastructure Security

- **Firewall (UFW)**:
  - VPS-1: 22, 80, 443 open
  - VPS-2: 22, 25, 80, 443, 465, 587, 993, 995 open; SSH restricted to WireGuard
- **Fail2ban**:
  - SSH brute-force protection
  - Nginx rate-limit abuse
  - Bad bot detection
- **WireGuard VPN** between VPS-1 and VPS-2:
  - Stalwart API accessible only via private network
  - Provisioning traffic never traverses public internet
- **SSH hardening**:
  - Password authentication disabled
  - Root login prohibited-password
  - MaxAuthTries 3
  - ClientAlive timeout
- **Nginx security headers**:
  - HSTS, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy
  - Rate limiting on login, API, and Stripe endpoints
- **Stalwart sandboxing**:
  - systemd `NoNewPrivileges`, `ProtectSystem=strict`, `ProtectHome=true`
  - `CAP_NET_BIND_SERVICE` only

### API Key Management

- Keys are **hashed** (SHA-256) in the database; only prefix is stored for identification
- Keys are displayed **only once** at creation
- Keys can be revoked instantly via portal or admin dashboard
- `last_used_at` tracked for audit

### Secrets Management

- **No secrets in code or repositories**
- All sensitive values in `.env` files (not committed)
- `.env` files restricted to `root` / `email-saas` user
- Backup encryption key stored only on VPS-1
- Stripe webhook secret verified via signature validation

### Stripe Security

- **Webhook signature verification** using `stripe-webhook-secret`
- Test mode keys never used in production
- Billing data encrypted at rest by Stripe

### Data Retention & GDPR

- **Tickets**: retained 90 days after closure
- **Audit logs**: retained 1 year
- **Metering events**: retained 2 years
- **Account deletion**: 30-day grace period with full export available
- **Self-service export**: `GET /account/export` returns JSON/CSV of all customer data
- **DPA**: available for enterprise customers

### Compliance

- **CAN-SPAM**: All outbound SMTP includes valid `List-Unsubscribe` if bulk
- **From domain alignment**: enforced to match registered domains
- **Opt-in verification**: required for high-volume senders
- **GDPR**: right to erasure, right to portability, data retention policies documented

## Security Checklist

- [ ] `SECRET_KEY` is 32+ random bytes and rotated annually
- [ ] `ADMIN_2FA_REQUIRED=true` in production
- [ ] `.env` files are not in git
- [ ] SSH keys only (no password auth)
- [ ] Fail2ban active and configured
- [ ] WireGuard tunnel operational
- [ ] Stalwart API not exposed to public internet
- [ ] SSL A+ rating on SSL Labs
- [ ] Backup encryption key stored securely (1Password / Vault)
- [ ] Restic backup tested monthly
- [ ] Cross-tenant access tests pass (pytest)
- [ ] API key scope tests pass (pytest)
- [ ] Admin impersonation audit logs verified
