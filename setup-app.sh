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

REPO_URL="${REPO_URL:-https://github.com/porkmagus/email-saas.git}"
PROJECT_DIR="/opt/email-saas"
HOSTNAME="${HOSTNAME:-vps1-app}"
DOMAIN="${DOMAIN:-example.com}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@$DOMAIN}"

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

# Install minimal prerequisites
apt-get update
apt-get install -y --no-install-recommends git curl ca-certificates

# Clone or update repo
if [[ -d "$PROJECT_DIR/.git" ]]; then
    cd "$PROJECT_DIR"
    git pull origin main
elif [[ -d "$PROJECT_DIR" ]]; then
    echo "ERROR: $PROJECT_DIR exists but is not a git repo. Move it or clone manually."
    exit 1
else
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# Run base VPS hardening (common to both VPSs)
ROLE=app DOMAIN="$DOMAIN" bash "$PROJECT_DIR/infra/scripts/setup_vps.sh" || {
    echo "ERROR: VPS hardening failed"
    exit 1
}

# Install Docker & Docker Compose
if ! command -v docker &>/dev/null; then
    echo "Installing Docker..."
    apt-get install -y --no-install-recommends gnupg lsb-release
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
    echo "Creating $PROJECT_DIR/.env with production-required values..."
    cat > "$PROJECT_DIR/.env" <<EOF
DATABASE_URL=postgresql+asyncpg://email_saas:email_saas_dev@postgres:5432/email_saas
REDIS_URL=redis://redis:6379/0
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
IMPERSONATE_TOKEN_EXPIRE_MINUTES=15
ADMIN_2FA_REQUIRED=true
ENVIRONMENT=production
DOCS_ENABLED=false
API_KEY_SECRET=$(openssl rand -hex 32)
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_ID=
STALWART_BASE_URL=http://10.0.0.2:8080
STALWART_API_TOKEN=
FRONTEND_URL=https://$DOMAIN
VPS2_PUBLIC_IP=
FIRST_ADMIN_EMAIL=admin@$DOMAIN
FIRST_ADMIN_PASSWORD=$(openssl rand -base64 24)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
NOTIFICATION_FROM=noreply@$DOMAIN
SLACK_WEBHOOK_URL=
EOF
    echo "Created $PROJECT_DIR/.env. Edit required production values, then rerun setup."
    exit 1
fi

# Validate that critical production values are set
set -a
source "$PROJECT_DIR/.env"
set +a

MISSING=()
if [[ -z "${STRIPE_SECRET_KEY:-}" ]] || [[ "${STRIPE_SECRET_KEY:-}" == sk_test* ]]; then
    MISSING+=("STRIPE_SECRET_KEY (must be a live key, not test)")
fi
if [[ -z "${STRIPE_WEBHOOK_SECRET:-}" ]] || [[ "${STRIPE_WEBHOOK_SECRET:-}" == whsec_test* ]]; then
    MISSING+=("STRIPE_WEBHOOK_SECRET (must be a real secret, not whsec_test)")
fi
if [[ -z "${STALWART_API_TOKEN:-}" ]]; then
    MISSING+=("STALWART_API_TOKEN")
fi
if [[ -z "${VPS2_PUBLIC_IP:-}" ]] || [[ "${VPS2_PUBLIC_IP:-}" == "1.2.3.4" ]]; then
    MISSING+=("VPS2_PUBLIC_IP")
fi
if [[ -z "${SECRET_KEY:-}" ]] || [[ "${#SECRET_KEY}" -lt 32 ]]; then
    MISSING+=("SECRET_KEY (must be >= 32 chars)")
fi
if [[ -z "${API_KEY_SECRET:-}" ]]; then
    MISSING+=("API_KEY_SECRET")
fi

if [[ ${#MISSING[@]} -gt 0 ]]; then
    echo "ERROR: Missing or invalid required production values in .env:"
    for key in "${MISSING[@]}"; do
        echo "  - $key"
    done
    echo "Edit $PROJECT_DIR/.env and rerun setup."
    exit 1
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
if ! docker compose exec -T backend alembic upgrade head; then
    echo "ERROR: Database migration failed. Aborting setup."
    exit 1
fi

# Seed admin
docker compose exec -T backend python scripts/seed_admin.py || echo "Admin seed failed (may already exist)"

# Run certbot for SSL certificates
echo "=== Obtaining SSL certificates via Certbot ==="
if ! certbot certonly --webroot -w /var/www/letsencrypt -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos -m "$ADMIN_EMAIL"; then
    echo "ERROR: Certbot failed. Check DNS and firewall."
    exit 1
fi

# Install final HTTPS nginx config
echo "=== Installing final HTTPS nginx config ==="
sed -e "s/{{DOMAIN}}/$DOMAIN/g" "$PROJECT_DIR/infra/nginx/vps1.conf" > /etc/nginx/sites-available/email-saas
nginx -t && systemctl restart nginx

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
echo "1. Configure WireGuard to VPS-2"
echo "2. Set up Stripe webhooks"
echo "3. Add VPS-2 .env STALWART_API_TOKEN if not already done"
echo ""
echo "Documentation:"
echo "  - $PROJECT_DIR/docs/SETUP.md"
echo "  - $PROJECT_DIR/docs/OPS.md"
echo ""
