#!/bin/bash
set -euo pipefail

# setup-mail.sh
# Pushbutton setup for VPS-2 (Mail Server)
# Installs: Stalwart Mail Server, Roundcube, PHP 8.4, Nginx, SSL
# Usage: ./setup-mail.sh
# Must be run as root on Ubuntu 24.04

LOG_FILE="/var/log/email-saas-mail-setup.log"
exec > >(tee -a "$LOG_FILE") 2>&1

REPO_URL="https://github.com/your-org/email-saas.git"
PROJECT_DIR="/opt/email-saas"
HOSTNAME="${HOSTNAME:-vps2-mail}"
DOMAIN="${DOMAIN:-example.com}"
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

# Run base VPS hardening (common to both VPSs)
# This installs: nginx, ufw, fail2ban, logrotate, certbot, ssh hardening
# For mail role: also PHP 8.4 FPM
ROLE=mail DOMAIN="$DOMAIN" bash "$PROJECT_DIR/infra/scripts/setup_vps.sh" || {
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

# Install Stalwart Mail Server
echo "=== Installing Stalwart Mail Server ==="
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

# Start PHP-FPM
systemctl enable php8.4-fpm
systemctl start php8.4-fpm

# Restart nginx to pick up new config
systemctl restart nginx

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
echo "  PHP-FPM:    systemctl status php8.4-fpm"
echo ""
echo "Roundcube:    $ROUNDCUBE_DIR"
echo ""
echo "Next steps:"
echo "1. Configure /etc/stalwart/stalwart.toml with your domain"
echo "2. Generate Stalwart API token: curl -u admin:password http://localhost:8080/api/auth/token"
echo "3. Add API token to VPS-1 .env as STALWART_API_TOKEN"
echo "4. Configure WireGuard to VPS-1"
echo "5. Run certbot for SSL: certbot --nginx -d webmail.$DOMAIN -d mail.$DOMAIN"
echo "6. Configure DNS MX records pointing to this server"
echo ""
echo "Documentation:"
echo "  - $PROJECT_DIR/docs/SETUP.md"
echo "  - $PROJECT_DIR/docs/OPS.md"
echo ""
