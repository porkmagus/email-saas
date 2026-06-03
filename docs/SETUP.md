# Setup Guide

## Prerequisites

- Two VPS instances (e.g., Hetzner, DigitalOcean, AWS, etc.) with Ubuntu 24.04 LTS
- A domain name (e.g., `example.com`)
- Stripe account with API keys
- S3-compatible storage for backups (Wasabi / Backblaze / AWS S3 / etc.)

## Step-by-Step VPS Setup

### 1. Initial Server Access

```bash
# Add your SSH key to both servers
ssh-copy-id root@vps1-ip
ssh-copy-id root@vps2-ip
```

### 2. Run Pushbutton Setup

```bash
# On VPS-1 (App Server)
ssh root@vps1-ip
cd /opt
git clone https://github.com/porkmagus/email-saas.git
cd email-saas
HOSTNAME=vps1-app DOMAIN=example.com ./setup-app.sh

# On VPS-2 (Mail Server)
ssh root@vps2-ip
cd /opt
git clone https://github.com/porkmagus/email-saas.git
cd email-saas
HOSTNAME=vps2-mail DOMAIN=example.com ./setup-mail.sh
```

**What each script does:**

- `setup-app.sh` (VPS-1):
  - Hardens Ubuntu (UFW, fail2ban, SSH)
  - Installs Docker, Nginx (host reverse proxy)
  - Builds React frontend on host (served by Nginx)
  - Starts Docker Compose: backend + PostgreSQL + Redis
  - Host Nginx proxies `/api/` to Docker backend
  - Runs migrations and seeds admin

- `setup-mail.sh` (VPS-2):
  - Hardens Ubuntu (UFW, fail2ban, SSH)
  - Installs Nginx, PHP 8.4 FPM
  - Installs Stalwart Mail Server
  - Installs Roundcube webmail
  - Configures host Nginx for Roundcube + Stalwart admin proxy

### 3. Configure WireGuard VPN

```bash
# On VPS-1
ROLE=server WG_IP=10.0.0.1 PEER_IP=10.0.0.2 PEER_PUBLIC_IP=<vps2-public> ./infra/scripts/setup_wireguard.sh

# On VPS-2
ROLE=client WG_IP=10.0.0.2 PEER_IP=10.0.0.1 PEER_PUBLIC_IP=<vps1-public> ./infra/scripts/setup_wireguard.sh

# Exchange public keys and update /etc/wireguard/wg0.conf on both sides
# Then restart:
systemctl restart wg-quick@wg0
```

### 4. Obtain SSL Certificates

```bash
# On VPS-1
certbot --nginx -d example.com -d www.example.com -d status.example.com

# On VPS-2
certbot --nginx -d webmail.example.com -d mail.example.com
```

### 5. Configure Environment Variables

```bash
# On VPS-1
cp .env.example /opt/email-saas/.env
nano /opt/email-saas/.env
```

Set at minimum:
- `DATABASE_URL` (use local postgres)
- `REDIS_URL` (use local redis)
- `SECRET_KEY` (generate with `openssl rand -hex 32`)
- `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID`
- `STALWART_BASE_URL=http://10.0.0.2:8080`
- `STALWART_API_TOKEN` (generate in Stalwart admin)
- `FRONTEND_URL=https://example.com`
- `FIRST_ADMIN_EMAIL` and `FIRST_ADMIN_PASSWORD`
- `BACKUP_*` variables for Restic

### 6. Deploy Application Code

```bash
# On VPS-1
rsync -avz --exclude=node_modules --exclude=.venv ./ backend/ /opt/email-saas/

# Install backend
cd /opt/email-saas/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run migrations
alembic upgrade head

# Seed admin
python scripts/seed_admin.py

# Build frontend
cd /opt/email-saas/frontend
npm ci
npm run build

# Copy dist to nginx
cp -r dist /var/www/app/

# Restart services
systemctl restart email-saas-api
systemctl restart nginx
```

### 7. Configure Stalwart (VPS-2)

Edit `/etc/stalwart/stalwart.toml` with your hostname, TLS, and storage settings.

Generate an API token:
```bash
curl -u admin:password http://localhost:8080/api/auth/token
```

Add this token to VPS-1 `.env` as `STALWART_API_TOKEN`.

### 8. Configure DNS

Point your domain to the VPS IPs:

| Record | Type | Value |
|--------|------|-------|
| `example.com` | A | VPS-1 IP |
| `www.example.com` | CNAME | example.com |
| `webmail.example.com` | A | VPS-2 IP |
| `mail.example.com` | A | VPS-2 IP |
| `status.example.com` | A | VPS-1 IP |
| `example.com` | MX | mail.example.com (priority 10) |
| `_dmarc.example.com` | TXT | `v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com` |

### 9. Verify End-to-End

```bash
# API health
curl https://example.com/api/v1/health

# Stripe webhook test
stripe listen --forward-to https://example.com/api/v1/stripe/webhook

# Create test domain via API
# (after admin login)
```

## First-Run Checklist

- [ ] API health returns `{"status": "ok"}`
- [ ] Stripe webhook signature verification works
- [ ] Admin login with 2FA enabled
- [ ] First domain created and verified
- [ ] First mailbox created via Stalwart API
- [ ] Test email sent and received via Roundcube
- [ ] Backups configured and Restic repo initialized
- [ ] Blacklist check script runs without errors
- [ ] Fail2ban active (`fail2ban-client status`)
- [ ] Logrotate configured (`logrotate -d /etc/logrotate.d/nginx`)
