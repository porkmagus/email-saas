# Operations Guide

## Daily Operations

### Check Service Health

```bash
# API health
systemctl status email-saas-api
journalctl -u email-saas-api -n 50 -f

# Database
systemctl status postgresql
pg_isready

# Redis
systemctl status redis
redis-cli ping

# Nginx
systemctl status nginx
nginx -t

# Mail server (VPS-2)
systemctl status stalwart
journalctl -u stalwart -n 50 -f
```

### Check Mail Queues

```bash
# Stalwart queue status
curl -s -H "Authorization: Bearer $STALWART_API_TOKEN" \
  http://10.0.0.2:8080/api/server/queue | jq

# Queue depth alert thresholds
# Outbound > 500 or oldest > 15 min → alert
# Inbound > 1000 → alert
```

### Restarting Services

```bash
# API (zero-downtime with systemd)
systemctl reload email-saas-api

# Nginx
systemctl reload nginx

# Stalwart
systemctl reload stalwart
# Full restart (drain queue first)
systemctl stop stalwart
systemctl start stalwart
```

### Database Maintenance

```bash
# Vacuum and analyze
sudo -u postgres psql -d email_saas -c "VACUUM ANALYZE;"

# Check table sizes
sudo -u postgres psql -d email_saas -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables WHERE schemaname='public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Check connection count
sudo -u postgres psql -d email_saas -c "SELECT count(*) FROM pg_stat_activity;"
```

### Redis Maintenance

```bash
# Check memory usage
redis-cli info memory

# Check connected clients
redis-cli info clients

# Flush stale sessions (if needed)
redis-cli eval "return redis.call('del', unpack(redis.call('keys', 'session:*')))" 0
```

### Log Monitoring

```bash
# API logs
journalctl -u email-saas-api -n 100 -f

# Nginx logs
tail -f /var/log/nginx/vps1_access.log

# Stalwart logs
journalctl -u stalwart -n 100 -f

# Mail logs
tail -f /var/log/stalwart/*.log
```

### Backup Verification

```bash
# Check latest Restic snapshot
restic -r s3:s3.wasabisys.com/email-saas-backups snapshots --latest 1

# Test restore (to temp directory)
restic -r s3:s3.wasabisys.com/email-saas-backups restore latest --target /tmp/restore-test
```

### SSL Certificate Management

```bash
# Check expiry
certbot certificates

# Renew manually (usually auto)
certbot renew --nginx

# Force renew for testing
certbot renew --force-renewal
```

## Common Tasks

### Add a New Admin

```bash
cd /opt/email-saas/backend
source .venv/bin/activate
python -c "
import asyncio
from api.db import async_session
from api.services.auth import create_user
async def main():
    async with async_session() as db:
        await create_user(db, email='newadmin@example.com', password='changeme', role='admin')
asyncio.run(main())
"
```

### Rotate Stalwart API Token

1. Generate new token in Stalwart admin
2. Update `/opt/email-saas/.env`
3. Reload API: `systemctl reload email-saas-api`

### Update Application Code

```bash
cd /opt/email-saas
git pull origin main

# Backend
cd backend
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
systemctl reload email-saas-api

# Frontend
cd ../frontend
npm ci
npm run build
cp -r dist /var/www/app/
systemctl reload nginx
```

## Monitoring Checklist

Run these daily or automate via cron:

- [ ] Check API uptime (`/api/v1/health`)
- [ ] Check mail queue depth
- [ ] Check disk usage (`df -h`)
- [ ] Check SSL expiry (within 30 days)
- [ ] Check backup success (`restic snapshots`)
- [ ] Check fail2ban status (`fail2ban-client status`)
- [ ] Check blacklist status (`/usr/local/bin/blacklist_check.sh`)
- [ ] Review failed provisioning jobs in admin dashboard
