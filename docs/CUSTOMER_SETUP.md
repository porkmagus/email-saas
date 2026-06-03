# Customer Setup Guide

## What Customers See

After Stripe Checkout, customers land in the portal and complete onboarding:

1. **Verify Domain** — Add a custom domain or use a subdomain
2. **Add Mailbox** — Create email addresses
3. **Configure DNS** — Copy MX, SPF, DKIM records from the portal
4. **Launch Webmail** — Access Roundcube with SSO

## Adding a Domain

1. Go to **Domains** → **Add Domain**
2. Enter domain name (e.g., `customer.com`)
3. The portal generates DNS records:

| Record | Type | Value |
|--------|------|-------|
| `customer.com` | MX | `mail.your-saas.com` (priority 10) |
| `customer.com` | TXT | `v=spf1 mx ~all` |
| `dkim._domainkey.customer.com` | TXT | `<DKIM public key from Stalwart>` |
| `_dmarc.customer.com` | TXT | `v=DMARC1; p=quarantine; rua=mailto:dmarc@your-saas.com` |

4. Add these records at the customer's registrar
5. Click **Verify DNS** in the portal
6. The backend checks MX, SPF, and DKIM via DNS lookups
7. Once verified, the domain is active for mailbox creation

## Adding a Mailbox

1. Go to **Mailboxes** → **Create Mailbox**
2. Select the verified domain
3. Enter local part (e.g., `john`) and password
4. Set quota (default from plan, or custom)
5. The backend provisions the mailbox via Stalwart API
6. The customer receives a welcome email with setup instructions

## Webmail Access

Customers click **Open Webmail** in the portal. This:

1. Generates a short-lived SSO JWT (valid 60 seconds)
2. Redirects to `webmail.your-saas.com` with the token
3. Roundcube validates the token and auto-logs the user
4. No separate password needed for webmail

## API Keys

For SMTP/IMAP/programmatic access:

1. Go to **Settings** → **API Keys**
2. Click **Create Key**
3. Name the key and select scopes:
   - `smtp` — Send email
   - `imap` — Read email
   - `api_read` — Read account data
   - `api_write` — Modify domains/mailboxes
4. The key is displayed **once** — copy it immediately
5. Use the key as the SMTP/IMAP password in any email client

## DNS Troubleshooting

If verification fails:

- **MX not found**: Ensure the MX record points to `mail.your-saas.com` and TTL has expired
- **SPF mismatch**: Only one SPF record should exist. Combine with existing records if needed
- **DKIM not found**: Wait for DNS propagation (up to 24 hours), then re-verify
- Use the portal's **DNS Lookup** tool to check records from our servers

## Plan Limits & Quota

The dashboard shows:

- Mailboxes used / mailboxes included
- Storage used / storage included
- Emails sent this month / monthly limit
- Overage warnings at 80% and 100%

At 100% quota, sends are blocked with an upgrade prompt.

## Data Migration

Customers can migrate from external providers:

1. Go to **Settings** → **Import Mail**
2. Enter source IMAP server, username, password
3. Select folders to import
4. Background job syncs mail to the new mailbox
5. Progress shown in the portal

## Cancellation & Data Export

1. Go to **Billing** → **Cancel Subscription**
2. Account enters grace period (30 days)
3. During grace period, customer can export data:
   - Mailboxes as `.eml` or `.mbox`
   - Domain settings as JSON
   - Billing history as CSV
4. After grace period, all data is permanently deleted
