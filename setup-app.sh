#!/bin/bash
set -euo pipefail

# setup-app.sh
# Pushbutton setup for VPS-1 (App Server)
# Architecture: Docker Compose for backend + postgres + redis
# Host nginx serves frontend static files and proxies /api/ to backend container
# Usage: ./setup-app.sh
# Must be run as root on Ubuntu 24.04

LOG_FILE="/var/log/email-saas-setup.log"
exec > >(tee -a "$LOG_FILE") 2>&1

REPO_URL="https://github.com/your-org/email-saas.git"
PROJECT_DIR="/opt/email-saas"
HOSTNAME="${HOSTNAME:-vps1-app}"
DOMAIN="${DOMAIN:-example.com}"

# Detect OS
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    echo "Cannot detect OS. Exiting."
    exit 1
fi

if [[ "$OS" != "Ubuntu" ]] || [[ ! "$VER" =~ ^24\.04 ]]; then
    echo "WARNING: This script is designed for Ubuntu 24.04. Detected: $OS $VER"
    read -rp "Continue anyway? [y/N] " ans
    if [[ "$ans" != "y" && "$ans" != "Y" ]]; then
        exit 1
    fi
fi

echo "=== Email SaaS App Server Setup (VPS-1) ==="
echo "OS: $OS $VER"
echo "Hostname: $HOSTNAME"
echo "Domain: $DOMAIN"
echo "Date: $(date -Iseconds)"

# Set hostname
hostnamectl set-hostname "$HOSTNAME"

# Run base VPS hardening (common to both VPSs)
# This installs: nginx, ufw, fail2ban, logrotate, certbot, ssh hardening
# It does NOT install PostgreSQL, Redis, or Node.js (those run in Docker)
ROLE=app DOMAIN="$DOMAIN" bash "$PROJECT_DIR/infra/scripts/setup_vps.sh" || {
    echo "ERROR: VPS hardening failed"
    exit 1
}

# Clone or update repo
if [[ -d "$PROJECT_DIR/.git" ]]; then
    echo "Using existing repo at $PROJECT_DIR"
    cd "$PROJECT_DIR"
    git pull origin main || true
elif [[ -d "$PROJECT_DIR" ]]; then
    echo "Using existing directory at $PROJECT_DIR (no git)"
else
    echo "Cloning repository..."
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# Install Docker & Docker Compose
if ! command -v docker &>/dev/null; then
    echo "Installing Docker..."
    apt-get update
    apt-get install -y --no-install-recommends ca-certificates curl gnupg lsb-release
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable docker
    systemctl start docker
fi

if ! docker compose version &>/dev/null; then
    echo "Installing Docker Compose..."
    apt-get install -y docker-compose-plugin
fi

# Create .env if missing
if [[ ! -f "$PROJECT_DIR/.env" ]]; then
    if [[ -f "$PROJECT_DIR/.env.example" ]]; then
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        echo "Created .env from .env.example. Please review and edit it."
    else
        echo "WARNING: .env.example not found. Creating minimal .env."
        cat > "$PROJECT_DIR/.env" <<EOF
DATABASE_URL=postgresql+asyncpg://email_saas:email_saas_dev@postgres:5432/email_saas
REDIS_URL=redis://redis:6379/0
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
IMPERSONATE_TOKEN_EXPIRE_MINUTES=15
ADMIN_2FA_REQUIRED=true
ENVIRONMENT=production
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_ID=
STALWART_BASE_URL=http://10.0.0.2:8080
STALWART_API_TOKEN=
FRONTEND_URL=https://$DOMAIN
FIRST_ADMIN_EMAIL=admin@$DOMAIN
FIRST_ADMIN_PASSWORD=$(openssl rand -base64 24)
EOF
    fi
fi

# Build frontend on host (nginx will serve static files)
echo "Building frontend..."
cd "$PROJECT_DIR/frontend"

# Install Node.js if not present
if ! command -v node &>/dev/null; then
    echo "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
    apt-get install -y nodejs
fi

npm ci
npm run build

# Copy built frontend to nginx web root
mkdir -p /var/www/app/dist
cp -r "$PROJECT_DIR/frontend/dist/"* /var/www/app/dist/
chown -R www-data:www-data /var/www/app/dist
echo "Frontend copied to /var/www/app/dist"

# Start Docker Compose stack (backend + postgres + redis only)
echo "Starting Docker Compose stack..."
cd "$PROJECT_DIR"
docker compose up -d --build

echo "Waiting for services to start..."
sleep 15

# Run migrations
docker compose exec -T backend alembic upgrade head || echo "Migration failed (may need manual intervention)"

# Seed admin
docker compose exec -T backend python scripts/seed_admin.py || echo "Admin seed failed (may already exist)"

# Restart nginx to pick up new config
systemctl restart nginx

# Print summary
echo ""
echo "=========================================="
echo "   Email SaaS App Server (VPS-1) Setup Complete"
echo "=========================================="
echo ""
echo "Project directory: $PROJECT_DIR"
echo "Logs:             $LOG_FILE"
echo ""
echo "URLs:"
echo "  Frontend: https://$DOMAIN"
echo "  API:      https://$DOMAIN/api/v1"
echo "  Health:   https://$DOMAIN/api/v1/health"
echo ""
echo "Next steps:"
echo "1. Edit $PROJECT_DIR/.env with real values (Stripe keys, Stalwart token)"
echo "2. Configure WireGuard to VPS-2"
echo "3. Run certbot for SSL certificates: certbot --nginx -d $DOMAIN -d www.$DOMAIN -d status.$DOMAIN"
echo "4. Set up Stripe webhooks"
echo ""
echo "Documentation:"
echo "  - $PROJECT_DIR/docs/SETUP.md"
echo "  - $PROJECT_DIR/docs/OPS.md"
echo ""
