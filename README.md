# Email SaaS

A production-ready email service provider SaaS built on two Ubuntu VPS instances:

- **VPS-1 (App)** — React frontend, FastAPI backend, PostgreSQL, Redis, Stripe
- **VPS-2 (Mail)** — Stalwart Mail Server, Roundcube webmail

## Quick Start

### Local Development (Docker)

```bash
cp .env.example .env
docker compose up -d
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/seed_admin.py
```

Visit http://localhost and log in with the admin credentials from `.env`.

### Production (VPS)

See [docs/SETUP.md](docs/SETUP.md) for full step-by-step provisioning.

The pushbutton setup script:

```bash
# VPS-1 (App)
HOSTNAME=vps1-app ./setup-app.sh

# VPS-2 (Mail)
HOSTNAME=vps2-mail ./setup-mail.sh
```

## Architecture

```
VPS-1 (App)                      VPS-2 (Mail)
+----------+                     +----------+
|  Nginx   | <---- WireGuard --->|  Nginx   |
|  React   |     10.0.0.0/24     | Roundcube|
|  FastAPI |                     | Stalwart |
| Postgres |                     |          |
|  Redis   |                     |          |
+----------+                     +----------+
```

## Documentation

- [docs/SETUP.md](docs/SETUP.md) — Step-by-step VPS setup
- [docs/OPS.md](docs/OPS.md) — Daily operations
- [docs/RUNBOOKS.md](docs/RUNBOOKS.md) — Incident response
- [docs/CUSTOMER_SETUP.md](docs/CUSTOMER_SETUP.md) — Customer onboarding
- [docs/SECURITY.md](docs/SECURITY.md) — Security posture

## Key Directories

```
.
├── backend/              FastAPI + SQLAlchemy + Alembic
├── frontend/             React + Vite + Tailwind
├── infra/                Infrastructure scripts & configs
│   ├── nginx/            Nginx configs (VPS-1 & VPS-2)
│   ├── scripts/          Provisioning & setup scripts
│   ├── systemd/          Service units
│   ├── cron/             Backup & monitoring scripts
│   └── logrotate/        Log rotation configs
├── docs/                 Documentation
├── docker-compose.yml    Local dev stack
├── .env.example          Environment variable template
├── setup-app.sh          Pushbutton VPS-1 app server setup
├── setup-mail.sh         Pushbutton VPS-2 mail server setup
```

## Tech Stack

| Component | Version |
|-----------|---------|
| Ubuntu | 24.04 LTS |
| Nginx | 1.31.1 |
| PostgreSQL | 17.10 |
| Redis | 7.4.9 |
| Python | 3.13.13 |
| FastAPI | 0.136.3 |
| Node.js | 24.15.0 LTS |
| React | 19.2.6 |
| Stalwart | 0.16.5 |
| PHP | 8.4.21 |
