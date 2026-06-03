#!/bin/bash
set -euo pipefail

# setup_vps.sh
# Pushbutton Ubuntu 24.04 hardening and setup
# Run as root. Idempotent where possible.
# NOTE: Does NOT install Stalwart or Docker (role-specific scripts handle those).

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
    # Use default PHP packages provided by Ubuntu 24.04 (not hardcoded 8.4)
    PACKAGES="$PACKAGES nginx php-fpm php-cli php-curl php-gd php-imap php-intl php-mbstring php-mysql php-xml php-zip php-pspell"
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

# Create application directories
mkdir -p /var/www/app/dist
mkdir -p /var/www/letsencrypt
mkdir -p /var/log/email-saas
mkdir -p /opt/email-saas
mkdir -p /backups/postgresql

# Create service user for API (used by Docker containers)
id -u email-saas &>/dev/null || useradd -r -s /bin/false -d /opt/email-saas email-saas

# Install temporary HTTP-only nginx bootstrap config for Certbot
DOMAIN="${DOMAIN:-example.com}"
if [[ "$ROLE" == "app" ]]; then
    cat > /etc/nginx/sites-available/email-saas <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN www.$DOMAIN;
    root /var/www/app/dist;
    location /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
    }
    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF
    ln -sf /etc/nginx/sites-available/email-saas /etc/nginx/sites-enabled/email-saas
    rm -f /etc/nginx/sites-enabled/default
elif [[ "$ROLE" == "mail" ]]; then
    cat > /etc/nginx/sites-available/email-saas <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name mail.$DOMAIN webmail.$DOMAIN;
    root /var/www/letsencrypt;
    location /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
    }
}
EOF
    ln -sf /etc/nginx/sites-available/email-saas /etc/nginx/sites-enabled/email-saas
    rm -f /etc/nginx/sites-enabled/default
fi

# Test and restart nginx with bootstrap config
nginx -t && systemctl restart nginx && systemctl enable nginx

# Install cron scripts
if [[ -d "$PROJECT_ROOT/infra/cron" ]]; then
    cp "$PROJECT_ROOT/infra/cron/"*.sh /usr/local/bin/
    chmod +x /usr/local/bin/*.sh
fi

# Daily backup cron (app VPS)
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
echo "1. Run certbot for SSL certificates"
echo "2. Install final nginx HTTPS config"
echo "3. Configure .env on VPS-1"
echo "4. Set up WireGuard between VPSs"
