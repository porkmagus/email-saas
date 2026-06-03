#!/bin/bash
set -euo pipefail

# setup-mail.sh
# Pushbutton setup for VPS-2 (Mail Server)
# Installs: Stalwart Mail Server, Roundcube, PHP, Nginx, SSL
# Usage: ./setup-mail.sh
# Must be run as root on Ubuntu 24.04

LOG_FILE="/var/log/email-saas-mail-setup.log"
exec > >(tee -a "$LOG_FILE") 2>&1

REPO_URL="${REPO_URL:-https://github.com/porkmagus/email-saas.git}"
PROJECT_DIR="/opt/email-saas"
HOSTNAME="${HOSTNAME:-vps2-mail}"
DOMAIN="${DOMAIN:-example.com}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@$DOMAIN}"
ROUNDCUBE_VERSION="1.7.1"
ROUNDCUBE_DIR="/var/www/roundcube"

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

echo "=== Email SaaS Mail Server Setup (VPS-2) ==="
echo "OS: $OS $VER"
echo "Hostname: $HOSTNAME"
echo "Domain: $DOMAIN"
echo "Date: $(date -Iseconds)"

# Set hostname
hostnamectl set-hostname "$HOSTNAME"

# Install minimal prerequisites
apt-get update
apt-get install -y --no-install-recommends git curl ca-certificates jq

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
ROLE=mail DOMAIN="$DOMAIN" bash "$PROJECT_DIR/infra/scripts/setup_vps.sh" || {
    echo "ERROR: VPS hardening failed"
    exit 1
}

# Install Stalwart Mail Server
echo "=== Installing Stalwart Mail Server ==="
export DOMAIN="$DOMAIN"
export MAIL_HOSTNAME="mail.${DOMAIN}"
export STALWART_ADMIN_PASSWORD="${STALWART_ADMIN_PASSWORD:-$(openssl rand -base64 24)}"
export PROJECT_DIR="$PROJECT_DIR"
bash "$PROJECT_DIR/infra/scripts/install_stalwart.sh"

# Install Roundcube
echo "=== Installing Roundcube Webmail ==="

# Download Roundcube if not present
if [[ ! -d "$ROUNDCUBE_DIR" ]]; then
    echo "Downloading Roundcube $ROUNDCUBE_VERSION..."
    mkdir -p "$ROUNDCUBE_DIR"
    cd /tmp
    curl -fsSL "https://github.com/roundcube/roundcubemail/releases/download/$ROUNDCUBE_VERSION/roundcubemail-$ROUNDCUBE_VERSION-complete.tar.gz" -o roundcube.tar.gz
    tar -xzf roundcube.tar.gz -C "$ROUNDCUBE_DIR" --strip-components=1
    rm -f roundcube.tar.gz
    chown -R www-data:www-data "$ROUNDCUBE_DIR"
fi

# Ensure Roundcube writable directories exist
mkdir -p "$ROUNDCUBE_DIR/logs" "$ROUNDCUBE_DIR/temp" "$ROUNDCUBE_DIR/data"
chown -R www-data:www-data "$ROUNDCUBE_DIR/logs" "$ROUNDCUBE_DIR/temp" "$ROUNDCUBE_DIR/data"
chmod 750 "$ROUNDCUBE_DIR/logs" "$ROUNDCUBE_DIR/temp" "$ROUNDCUBE_DIR/data"

# Create Roundcube config from sample
if [[ ! -f "$ROUNDCUBE_DIR/config/config.inc.php" ]]; then
    echo "Creating Roundcube configuration..."
    cp "$ROUNDCUBE_DIR/config/config.inc.php.sample" "$ROUNDCUBE_DIR/config/config.inc.php"
    
    # Configure Roundcube for Stalwart
    cat >> "$ROUNDCUBE_DIR/config/config.inc.php" <<EOF

// Stalwart IMAP/SMTP configuration
\$config['default_host'] = 'tls://mail.$DOMAIN';
\$config['default_port'] = 993;
\$config['smtp_server'] = 'tls://mail.$DOMAIN';
\$config['smtp_port'] = 587;
\$config['smtp_user'] = '%u';
\$config['smtp_pass'] = '%p';
\$config['support_url'] = '';
\$config['product_name'] = 'Email SaaS Webmail';
\$config['skin'] = 'elastic';
\$config['plugins'] = ['archive', 'zipdownload', 'managesieve'];

// Security
\$config['login_autocomplete'] = 0;
\$config['password_charset'] = 'UTF-8';
\$config['sendmail_delay'] = 1;
\$config['max_recipients'] = 50;
\$config['max_group_members'] = 100;
EOF
    chown www-data:www-data "$ROUNDCUBE_DIR/config/config.inc.php"
fi

# Detect installed PHP-FPM service and socket
PHP_FPM_SERVICE="$(systemctl list-unit-files 'php*-fpm.service' --no-legend | awk '{print $1}' | head -n1)"
if [[ -z "$PHP_FPM_SERVICE" ]]; then
    echo "ERROR: PHP-FPM service not found."
    exit 1
fi
echo "Detected PHP-FPM service: $PHP_FPM_SERVICE"

PHP_FPM_SOCK="$(find /run/php -name 'php*-fpm.sock' 2>/dev/null | head -n1)"
if [[ -z "$PHP_FPM_SOCK" ]]; then
    echo "ERROR: PHP-FPM socket not found in /run/php."
    exit 1
fi
echo "Detected PHP-FPM socket: $PHP_FPM_SOCK"

systemctl enable "$PHP_FPM_SERVICE"
systemctl start "$PHP_FPM_SERVICE"

# Run certbot for SSL certificates
echo "=== Obtaining SSL certificates via Certbot ==="
if ! certbot certonly --webroot -w /var/www/letsencrypt -d "mail.$DOMAIN" -d "webmail.$DOMAIN" -d "admin-mail.$DOMAIN" --non-interactive --agree-tos -m "$ADMIN_EMAIL"; then
    echo "ERROR: Certbot failed. Check DNS and firewall."
    exit 1
fi

# Install final HTTPS nginx config
echo "=== Installing final HTTPS nginx config ==="
PHP_FPM_SOCK_NAME="${PHP_FPM_SOCK##*/}"
VPS1_WG_IP="${VPS1_WG_IP:-10.0.0.1}"
sed -e "s/{{DOMAIN}}/$DOMAIN/g" \
    -e "s/{{VPS1_WG_IP}}/$VPS1_WG_IP/g" \
    -e "s/{{PHP_FPM_SOCK}}/$PHP_FPM_SOCK_NAME/g" \
    "$PROJECT_DIR/infra/nginx/vps2.conf" > /etc/nginx/sites-available/email-saas
nginx -t && systemctl restart nginx

# Wait for Stalwart to be ready
for i in {1..12}; do
    if curl -fsS -u admin:"$STALWART_ADMIN_PASSWORD" http://localhost:8080/api/health >/dev/null 2>&1; then
        echo "Stalwart health check passed"
        break
    fi
    echo "Waiting for Stalwart... ($i/12)"
    sleep 5
    if [[ $i -eq 12 ]]; then
        echo "WARNING: Stalwart health check failed. Check: journalctl -u stalwart -f"
    fi
done

# Create required directories
mkdir -p /var/log/email-saas
mkdir -p /var/log/nginx

# Install cron scripts
if [[ -d "$PROJECT_DIR/infra/cron" ]]; then
    cp "$PROJECT_DIR/infra/cron/"*.sh /usr/local/bin/
    chmod +x /usr/local/bin/*.sh
fi

# Blacklist check cron
(crontab -l 2>/dev/null || true; echo "0 6 * * * /usr/local/bin/blacklist_check.sh >> /var/log/email-saas/blacklist.log 2>&1") | sort -u | crontab -

# Set up logrotate for Stalwart
cat > /etc/logrotate.d/stalwart <<'EOF'
/var/log/stalwart/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 stalwart adm
    sharedscripts
    postrotate
        systemctl reload nginx >/dev/null 2>&1 || true
    endscript
}
EOF

# Create a simple update script
cat > /usr/local/bin/update-email-saas-mail <<EOF
#!/bin/bash
set -euo pipefail
PROJECT_DIR="/opt/email-saas"
cd "$PROJECT_DIR"
git pull origin main

# Restart Stalwart
systemctl restart stalwart

# Restart nginx
systemctl restart nginx

# Restart PHP-FPM
PHP_FPM_SERVICE="\$(systemctl list-unit-files 'php*-fpm.service' --no-legend | awk '{print \$1}' | head -n1)"
if [[ -n "\$PHP_FPM_SERVICE" ]]; then
    systemctl restart "\$PHP_FPM_SERVICE"
fi

echo "Mail server update complete."
EOF
chmod +x /usr/local/bin/update-email-saas-mail

# Print summary
echo ""
echo "=========================================="
echo "   Email SaaS Mail Server (VPS-2) Setup Complete"
echo "=========================================="
echo ""
echo "Project directory: $PROJECT_DIR"
echo "Logs:             $LOG_FILE"
echo ""
echo "Installed services:"
echo "  Stalwart:   systemctl status stalwart"
echo "  Nginx:      systemctl status nginx"
echo "  PHP-FPM:    systemctl status $PHP_FPM_SERVICE"
echo ""
echo "Roundcube:    $ROUNDCUBE_DIR"
echo ""
echo "Next steps:"
echo "1. Review /etc/stalwart/stalwart.toml (auto-templated from domain)"
echo "2. Generate Stalwart API token: curl -u admin:<password> http://localhost:8080/api/auth/token"
echo "   (admin password is stored in /etc/stalwart/stalwart.toml)"
echo "3. Add API token to VPS-1 .env as STALWART_API_TOKEN"
echo "4. Configure WireGuard to VPS-1"
echo "5. Configure DNS MX records pointing to this server"
echo ""
echo "Quick update command:"
echo "  /usr/local/bin/update-email-saas-mail"
echo ""
echo "Documentation:"
echo "  - $PROJECT_DIR/docs/SETUP.md"
echo "  - $PROJECT_DIR/docs/OPS.md"
echo ""
