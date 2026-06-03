# Runbooks

## Queue Stuck (Outbound)

**Symptoms:** Outbound queue depth > 500 or oldest message > 15 minutes.

**Steps:**

```bash
# Check Stalwart queue status
curl -s -H "Authorization: Bearer $STALWART_API_TOKEN" \
  http://10.0.0.2:8080/api/server/queue | jq

# Check if specific domain is stuck
journalctl -u stalwart -n 200 | grep "timeout\|deferred\|refused"

# If stuck on a specific destination, check DNS
nslookup -type=mx problematic-domain.com

# Restart Stalwart (last resort)
systemctl restart stalwart
```

**Escalation:** If restart does not help, check disk space and network connectivity.

---

## Blacklist Listing

**Symptoms:** `blacklist_check.sh` reports IP listed on Spamhaus, Barracuda, etc.

**Steps:**

```bash
# Verify listing
dig -x <vps2-public-ip>
# Check each blacklist manually
for bl in zen.spamhaus.org b.barracudacentral.org multi.surbl.org; do
  dig +short "$(echo <vps2-public-ip> | awk -F. '{print $4"."$3"."$2"."$1}').$bl" A
done

# Immediately suspend outbound
systemctl stop stalwart
# OR via API:
curl -s -X PATCH -H "Authorization: Bearer $STALWART_API_TOKEN" \
  -d '{"outbound": {"enabled": false}}' \
  http://10.0.0.2:8080/api/server/queue

# Identify offending account
journalctl -u stalwart -n 5000 | grep -i "spam\|bulk\|volume" | tail -20

# Suspend customer account in admin dashboard
# POST /api/v1/admin/accounts/{id}/suspend

# Request delisting
# Spamhaus: https://www.spamhaus.org/removal/
# Barracuda: https://www.barracudacentral.org/rbl/removal
# SURBL: contact via provider

# After delisting confirmed, re-enable outbound
systemctl start stalwart
```

**Escalation:** If IP is repeatedly listed, consider migrating to a dedicated IP or suspend high-volume accounts.

---

## SSL Certificate Failure

**Symptoms:** Browser shows certificate error, or `certbot renew` fails.

**Steps:**

```bash
# Check cert status
certbot certificates

# Test renewal
certbot renew --dry-run

# Check nginx config is valid
nginx -t

# If cert expired, force renew
certbot renew --force-renewal --nginx

# If DNS challenge fails, verify A records
dig example.com A

# Restart nginx after renewal
systemctl restart nginx

# Check auto-renewal cron
systemctl status certbot.timer
```

**Escalation:** If DNS issues persist, check domain registrar and NS records.

---

## Disk Full

**Symptoms:** `df -h` shows > 80% on VPS-2 or > 85% on VPS-1.

**Steps:**

```bash
# Find largest directories
du -sh /var/lib/stalwart/* | sort -rh | head -20
du -sh /var/lib/postgresql/* | sort -rh | head -20
du -sh /var/log/* | sort -rh | head -20

# Rotate logs manually
logrotate -f /etc/logrotate.d/stalwart
logrotate -f /etc/logrotate.d/nginx

# Clean old PostgreSQL dumps
find /backups/postgresql -name "*.sql.gz" -mtime +7 -delete

# Clean old Restic local cache
restic cache --cleanup

# If maildir is the issue, check for large mailboxes
# Use Stalwart API to list accounts by quota usage

# Emergency: expand disk or add secondary storage
```

**Escalation:** Contact hosting provider for disk expansion if cleanup is insufficient.

---

## Account Suspension (Billing)

**Symptoms:** Stripe webhook `invoice.payment_failed` received.

**Steps:**

```bash
# Check Stripe dashboard for failed invoices
# Verify account status in API
# GET /api/v1/admin/accounts/{id}

# Suspend account
# POST /api/v1/admin/accounts/{id}/suspend
# Body: { "reason": "billing_failure" }

# Queue cleanup jobs
# POST /api/v1/admin/accounts/{id}/suspend
# This automatically enqueues:
# - suspend_account in Stalwart
# - disable API keys
# - notify customer

# Customer can reactivate by updating payment in Stripe Portal
# On `invoice.paid` webhook, unsuspend:
# POST /api/v1/admin/accounts/{id}/unsuspend
```

**Escalation:** If customer disputes charge, follow Stripe dispute resolution process.

---

## API Service Down

**Symptoms:** `curl /api/v1/health` returns 503 or connection refused.

**Steps:**

```bash
# Check systemd status
systemctl status email-saas-api

# Check recent logs
journalctl -u email-saas-api -n 100

# Check if database is up
pg_isready -h localhost -p 5432

# Check if redis is up
redis-cli ping

# Check socket file exists
ls -la /run/email-saas/api.sock

# Restart API
systemctl restart email-saas-api

# Check for port conflicts
ss -tlnp | grep 8000
```

**Escalation:** If database is down, see PostgreSQL recovery procedures.

---

## PostgreSQL Recovery

**Symptoms:** Database connection failures, corruption errors.

**Steps:**

```bash
# Check PostgreSQL status
systemctl status postgresql

# Check logs
journalctl -u postgresql -n 200

# If minor issue, restart
systemctl restart postgresql

# If corrupted, restore from backup:
# 1. Stop API
systemctl stop email-saas-api

# 2. Drop and recreate database
sudo -u postgres psql -c "DROP DATABASE email_saas;"
sudo -u postgres psql -c "CREATE DATABASE email_saas OWNER email_saas;"

# 3. Restore from latest dump
gunzip -c /backups/postgresql/email_saas_YYYYMMDD_HHMMSS.sql.gz | \
  sudo -u postgres psql -d email_saas

# 4. Restart API
systemctl start email-saas-api

# 5. Run migrations if needed
# cd /opt/email-saas/backend && alembic upgrade head
```

**Escalation:** If backup is also corrupted, use Restic point-in-time recovery.

---

## Data Breach / Compromise

**Symptoms:** Unauthorized access, suspicious API activity, leaked credentials.

**Steps:**

1. Immediately rotate `SECRET_KEY` in `.env` and restart API
2. Revoke all active sessions in Redis
3. Force password reset for all admin accounts
4. Rotate `STALWART_API_TOKEN`
5. Review `audit_log` table for suspicious actions
6. Check fail2ban for recent blocks
7. If Stripe keys compromised, rotate in Stripe Dashboard
8. Notify affected customers per GDPR / breach notification laws

**Escalation:** Engage security team and legal counsel. Document all actions.
