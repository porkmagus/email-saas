#!/bin/bash
set -euo pipefail

# setup.sh
# Pushbutton setup for Email SaaS
# Detects OS, installs Docker, runs the stack, seeds admin
# Usage: ./setup.sh

LOG_FILE="/var/log/email-saas-setup.log"
exec > >(tee -a "$LOG_FILE") 2>&1

REPO_URL="https://github.com/your-org/email-saas.git"
PROJECT_DIR="/opt/email-saas"
ROLE="${ROLE:-app}"   # app or mail

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

# Detect if running in Docker (local dev)
if [[ -f /.dockerenv ]] || grep -q docker /proc/1/cgroup 2>/dev/null; then
    echo "Docker environment detected. Skipping system-level setup."
    IN_DOCKER=true
else
    IN_DOCKER=false
fi

echo "=== Email SaaS Setup ==="
echo "OS: $OS $VER"
echo "Role: $ROLE"
echo "Docker: $IN_DOCKER"
echo "Date: $(date -Iseconds)"

# Install Docker & Docker Compose if not present
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

if ! command -v docker-compose &>/dev/null && ! docker compose version &>/dev/null; then
    echo "Installing Docker Compose..."
    apt-get install -y docker-compose-plugin
fi

# Clone or use existing repo
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
FRONTEND_URL=https://localhost
FIRST_ADMIN_EMAIL=admin@example.com
FIRST_ADMIN_PASSWORD=changeme-strong-password
EOF
    fi
fi

# Run docker-compose (local dev or Docker-only server)
if [[ "$IN_DOCKER" == true || "$ROLE" == "app" ]]; then
    echo "Starting Docker Compose stack..."
    cd "$PROJECT_DIR"
    docker compose up -d --build

    echo "Waiting for services to start..."
    sleep 15

    # Run migrations
    docker compose exec -T backend alembic upgrade head || echo "Migration failed (may need manual intervention)"

    # Seed admin
    docker compose exec -T backend python scripts/seed_admin.py || echo "Admin seed failed (may already exist)"
fi

# If not in Docker, run full VPS setup
if [[ "$IN_DOCKER" == false ]]; then
    echo "Running full VPS hardening and provisioning..."
    bash "$PROJECT_DIR/infra/scripts/setup_vps.sh"
fi

# Print summary
echo ""
echo "=========================================="
echo "   Email SaaS Setup Complete"
echo "=========================================="
echo ""
echo "Project directory: $PROJECT_DIR"
echo "Logs:             $LOG_FILE"
echo ""
if [[ "$IN_DOCKER" == true || "$ROLE" == "app" ]]; then
    echo "URLs:"
    echo "  Frontend: http://localhost"
    echo "  API:      http://localhost/api/v1"
    echo "  Health:   http://localhost/api/v1/health"
    echo ""
fi
if [[ "$IN_DOCKER" == false ]]; then
    echo "Production VPS Setup Complete"
    echo "Next steps:"
    echo "1. Edit $PROJECT_DIR/.env with real values"
    echo "2. Configure WireGuard between VPS-1 and VPS-2"
    echo "3. Run certbot for SSL certificates"
    echo "4. Deploy application code to /opt/email-saas"
    echo "5. Seed admin account"
    echo ""
fi
echo "Documentation:"
echo "  - $PROJECT_DIR/docs/SETUP.md"
echo "  - $PROJECT_DIR/docs/OPS.md"
echo "  - $PROJECT_DIR/docs/SECURITY.md"
echo ""
