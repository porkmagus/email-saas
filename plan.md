# Email SaaS Implementation Plan

## Current State (as of 2026-06-03)

### ✅ Completed
- **Backend**: All 16 Phase 1-4 routers + database tables + schemas + audit logging
- **Frontend**: All 12 Phase 1-4 customer pages + sidebar navigation
- **Auth**: JWT, OAuth, TOTP, recovery codes, WebAuthn/passkeys
- **Infrastructure**: Stalwart integration, Docker, tests, docs

### ⏳ Remaining: Phase 5 (Advanced)

#### P0: Critical (Builds on existing infrastructure)
1. **Outbox Router** - `OutboxMessage` table already exists in models
   - `POST /api/v1/outbox` — schedule/queue a message
   - `GET /api/v1/outbox` — list pending/sent/cancelled
   - `DELETE /api/v1/outbox/{id}` — cancel before send (undo send)
   - `POST /api/v1/outbox/{id}/send-now` — force immediate send
   - Background worker: cron job to send scheduled messages
   - Frontend: `OutboxPage` with schedule form, cancel button, status

2. **Snooze Router** — new `snooze` table needed
   - `POST /api/v1/snooze` — create a snooze rule
   - `GET /api/v1/snooze` — list active snoozes
   - `DELETE /api/v1/snooze/{id}` — end snooze
   - Frontend: `SnoozePage` with vacation-style snooze config

3. **Search Router** — leverage PostgreSQL `tsvector` or JMAP proxy
   - `GET /api/v1/search?query=&mailbox=All` — search across mail
   - Stalwart JMAP `SearchSnippet` or PostgreSQL `tsvector` on cached headers
   - Frontend: `SearchPage` with global search bar

#### P1: High Priority
4. **Export Router** — generate MBOX/EML/JSON exports
   - `POST /api/v1/export` — request export job
   - `GET /api/v1/export` — list exports
   - `GET /api/v1/export/{id}/download` — download file
   - Background worker: `aiosmtplib` + `mailbox` library
   - Frontend: `ExportPage`

5. **Import Router** — upload MBOX/EML/CSV
   - `POST /api/v1/import` — upload + queue
   - `GET /api/v1/import` — list imports
   - Frontend: `ImportPage`

6. **Desktop Notifications** — Web Push API
   - `POST /api/v1/push/subscribe` — store push subscription
   - `DELETE /api/v1/push/subscribe` — remove subscription
   - `POST /api/v1/push/test` — send test notification
   - Frontend: `NotificationsPage` with push toggle

7. **VIP Notifications** — extends Contact + Web Push
   - `PATCH /api/v1/contacts/{id}/vip` — toggle VIP
   - Push only when `is_vip` sender
   - Frontend: VIP toggle on Contacts page

#### P2: Medium Priority
8. **Attachment Search** — extends Files
   - `GET /api/v1/files?query=&type=image` — file search
   - Frontend: file search/filter

9. **Notes Search** — extends Notes
   - PostgreSQL `tsvector` on `title` + `body`
   - `GET /api/v1/notes?query=` — full-text search

10. **Email Templates** — new `templates` table
   - CRUD for reusable templates
   - `POST /api/v1/send` supports `template_id`

#### P3: Nice-to-Have
11. **Background Workers** — Celery/ARQ integration
   - Scheduled send, export, import as async tasks
   - `api/services/queue.py` with Redis

### ⏳ Remaining: Phase 6 (Scale & Enterprise)

#### P1: High Priority
1. **Shared Mailboxes** — Stalwart ACL + Groups
   - `SharedMailbox` table with `owner_account_id`, `members` (JSON)
   - `POST /api/v1/shared-mailboxes` — create
   - `GET /api/v1/shared-mailboxes` — list
   - Stalwart: `Principal` + `ACL` JMAP set
   - Frontend: `SharedMailboxesPage`

2. **Quota Add-ons** — Stripe metered billing
   - `POST /api/v1/billing/quota-addons` — list add-ons
   - `POST /api/v1/billing/quota-addons/{id}` — purchase
   - Update `Account.total_quota` on purchase
   - Frontend: `QuotaAddonsPage`

3. **Retention Policies** — new `retention_policies` table
   - `DELETE_AFTER_DAYS` for mail/folders
   - Cron job: `stalwart_api.py` delete old messages
   - Frontend: `RetentionPoliciesPage`

#### P2: Medium Priority
4. **Custom Webmail** — JMAP-based SPA
   - Massive scope (6-12 months); defer to Phase 6B
   - Alternatively: improve Roundcube SSO

5. **Mobile Apps** — React Native / Capacitor
   - Wrap existing SPA in Capacitor for iOS/Android
   - Push notifications via FCM/APNs

6. **DNS Hosting** — PowerDNS API proxy
   - `DnsZone` table with records
   - `POST /api/v1/dns` — create zone
   - Frontend: `DNSHostingPage`

7. **Website Hosting** — WebDAV static
   - `Website` table with WebDAV path
   - Nginx WebDAV location
   - Frontend: `WebsiteHostingPage`

## Implementation Order

### Round 1: Immediate (2-3 days)
- [ ] Outbox Router + frontend page
- [ ] Snooze Router + DB migration + frontend page
- [ ] Search Router + frontend page
- [ ] Update Sidebar with new nav items
- [ ] Update App.tsx with new routes
- [ ] Update tests

### Round 2: Near-term (1-2 weeks)
- [ ] Export Router + frontend
- [ ] Import Router + frontend
- [ ] Desktop Notifications (Web Push)
- [ ] VIP Notifications
- [ ] Notes Search (PostgreSQL tsvector)
- [ ] Attachment Search

### Round 3: Medium-term (1-2 months)
- [ ] Shared Mailboxes (Stalwart ACL)
- [ ] Quota Add-ons (Stripe metered)
- [ ] Retention Policies
- [ ] Background Worker queue (Celery/ARQ)
- [ ] Email Templates

### Round 4: Long-term (3+ months)
- [ ] Custom Webmail (JMAP SPA)
- [ ] Mobile Apps (Capacitor)
- [ ] DNS Hosting (PowerDNS)
- [ ] Website Hosting (WebDAV)

## Restrictions
- No Redis for frontend session cache
- No Redis Stream queue
- No DAP/DAP DP deployments
- All enterprise features only (no free tier)
- Native Mail.app/Outlook integration only (no client bridges)
- Only SMTP/IMAP/S3/Directory to OAuth migration (no WebAuthn migration)

## Database Migrations Needed
1. `snooze` table
2. `push_subscriptions` table
3. `exports` table
4. `imports` table
5. `templates` table
6. `shared_mailboxes` table
7. `retention_policies` table
8. `dns_zones` table
9. `websites` table
10. `tsvector` columns for search

## Frontend Dependencies
- No new packages needed (lucide-react, axios, react-router-dom already present)
- Web Push: use `navigator.serviceWorker` + `PushManager` (native APIs)
- Full-text search UI: use existing `Input` component
- Date scheduling: use `input[type="datetime-local"]`
