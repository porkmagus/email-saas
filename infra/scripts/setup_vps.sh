#!/bin/bash
set -euo pipefail

# setup_vps.sh
# Pushbutton Ubuntu 24.04 hardening and setup
# Run as root. Idempotent where possible.

LOG_FILE="/var/log/setup_vps.log"
exec > >(tee -a "$LOG_FILE") 2>&1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

ROLE="${ROLE:-app}"   # app (VPS-1) or mail (VPS-2)
HOSTNAME="${HOSTNAME:-email-saas}"
SSH_PORT="${SSH_PORT:-22}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"

# Ensure running as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

echo "=== VPS Setup Started ==="
echo "Role: $ROLE"
echo "Date: $(date -Iseconds)"

# Set hostname
hostnamectl set-hostname "$HOSTNAME"

# Update system
apt-get update
apt-get upgrade -y
apt-get autoremove -y

# Install base packages
PACKAGES="curl wget jq git nano htop ufw fail2ban logrotate restic certbot python3-certbot-nginx unzip"

if [[ "$ROLE" == "app" ]]; then
    # App server only needs nginx (reverse proxy) and Docker (installed separately)
    # PostgreSQL, Redis, and Node.js run inside Docker containers
    PACKAGES="$PACKAGES nginx"
elif [[ "$ROLE" == "mail" ]]; then
    PACKAGES="$PACKAGES nginx php8.4-fpm php8.4-cli php8.4-curl php8.4-gd php8.4-imap php8.4-intl php8.4-mbstring php8.4-mysql php8.4-xml php8.4-zip php8.4-pspell"
fi

apt-get install -y --no-install-recommends $PACKAGES

# UFW Firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow $SSH_PORT/tcp
ufw allow 80/tcp
ufw allow 443/tcp

if [[ "$ROLE" == "app" ]]; then
    # Allow Redis only from localhost / WireGuard
    ufw allow from 10.0.0.0/24 to any port 6379
fi

if [[ "$ROLE" == "mail" ]]; then
    ufw allow 25/tcp
    ufw allow 465/tcp
    ufw allow 587/tcp
    ufw allow 993/tcp
    ufw allow 995/tcp
    ufw allow 4190/tcp   # Sieve
    ufw allow 110/tcp    # POP3
    ufw allow 143/tcp    # IMAP (starttls)
    # Restrict SSH to WireGuard if VPS-1 IP is known
    if [[ -n "${VPS1_WG_IP:-}" ]]; then
        ufw delete allow $SSH_PORT/tcp || true
        ufw allow from $VPS1_WG_IP to any port $SSH_PORT
        echo "SSH restricted to WireGuard IP $VPS1_WG_IP"
    fi
fi

ufw --force enable

# Fail2ban
if [[ ! -f /etc/fail2ban/jail.local ]]; then
    cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5
backend = systemd

[sshd]
enabled = true
port = $SSH_PORT
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-badbots]
enabled = true
filter = nginx-badbots
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 2

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
EOF
    systemctl restart fail2ban
    systemctl enable fail2ban
fi

# Logrotate for nginx (ensure present)
if [[ ! -f /etc/logrotate.d/nginx ]]; then
    cat > /etc/logrotate.d/nginx <<'EOF'
/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 $(cat /var/run/nginx.pid)
    endscript
}
EOF
fi

# SSH hardening
if [[ -f /etc/ssh/sshd_config ]]; then
    sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
    sed -i 's/^#*PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
    sed -i 's/^#*MaxAuthTries.*/MaxAuthTries 3/' /etc/ssh/sshd_config
    sed -i 's/^#*ClientAliveInterval.*/ClientAliveInterval 300/' /etc/ssh/sshd_config
    sed -i 's/^#*ClientAliveCountMax.*/ClientAliveCountMax 2/' /etc/ssh/sshd_config
    systemctl restart sshd
fi

# Install Stalwart on mail VPS
if [[ "$ROLE" == "mail" ]]; then
    echo "=== Installing Stalwart Mail Server ==="
    bash "$SCRIPT_DIR/install_stalwart.sh"
fi

# Create application directories
mkdir -p /var/www/app/dist
mkdir -p /var/log/email-saas
mkdir -p /opt/email-saas
mkdir -p /backups/postgresql

# Create service user for API (used by Docker containers)
id -u email-saas &>/dev/null || useradd -r -s /bin/false -d /opt/email-saas email-saas

# Copy nginx config (with template substitution for app role)
if [[ "$ROLE" == "app" && -f "$PROJECT_ROOT/infra/nginx/vps1.conf" ]]; then
    # Substitute template variables
    DOMAIN="${DOMAIN:-example.com}"
    sed -e "s/{{DOMAIN}}/$DOMAIN/g" "$PROJECT_ROOT/infra/nginx/vps1.conf" > /etc/nginx/sites-available/email-saas
    ln -sf /etc/nginx/sites-available/email-saas /etc/nginx/sites-enabled/email-saas
    rm -f /etc/nginx/sites-enabled/default
fi

if [[ "$ROLE" == "mail" && -f "$PROJECT_ROOT/infra/nginx/vps2.conf" ]]; then
    # Substitute template variables
    DOMAIN="${DOMAIN:-example.com}"
    VPS1_WG_IP="${VPS1_WG_IP:-10.0.0.1}"
    sed -e "s/{{DOMAIN}}/$DOMAIN/g" -e "s/{{VPS1_WG_IP}}/$VPS1_WG_IP/g" "$PROJECT_ROOT/infra/nginx/vps2.conf" > /etc/nginx/sites-available/email-saas
    ln -sf /etc/nginx/sites-available/email-saas /etc/nginx/sites-enabled/email-saas
    rm -f /etc/nginx/sites-enabled/default
fi

# Test nginx
nginx -t && systemctl restart nginx && systemctl enable nginx

# Install cron scripts
if [[ -d "$PROJECT_ROOT/infra/cron" ]]; then
    cp "$PROJECT_ROOT/infra/cron/"*.sh /usr/local/bin/
    chmod +x /usr/local/bin/*.sh
fi

# Daily backup cron
if [[ "$ROLE" == "app" ]]; then
    (crontab -l 2>/dev/null || true; echo "0 3 * * * /usr/local/bin/daily_backups.sh >> /var/log/email-saas/backup.log 2>&1") | sort -u | crontab -
fi

# Blacklist check cron (mail VPS)
if [[ "$ROLE" == "mail" ]]; then
    (crontab -l 2>/dev/null || true; echo "0 6 * * * /usr/local/bin/blacklist_check.sh >> /var/log/email-saas/blacklist.log 2>&1") | sort -u | crontab -
fi

# Disable password-based root login if SSH keys are present
if [[ -s /root/.ssh/authorized_keys ]]; then
    echo "SSH keys detected. Disabling password authentication."
    sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
    systemctl restart sshd
fi

echo "=== VPS Setup Complete ==="
echo "Role: $ROLE"
echo "Review $LOG_FILE for details."
echo "Next steps:"
echo "1. Configure .env on VPS-1"
echo "2. Set up WireGuard between VPSs"
echo "3. Run certbot for SSL"
echo "4. Deploy application code"
echo "5. Seed admin account"
