#!/bin/bash
set -euo pipefail

# install_stalwart.sh
# Download and install Stalwart Mail Server 0.16.5 on Ubuntu 24.04
# Idempotent: will skip if exact version already installed
# Creates systemd service and pins version

VERSION="0.16.5"
INSTALL_DIR="/opt/stalwart"
DATA_DIR="/var/lib/stalwart"
CONFIG_DIR="/etc/stalwart"
SERVICE_FILE="/etc/systemd/system/stalwart.service"
USER="stalwart"
ARCH="$(uname -m)"

# Map architecture
if [[ "$ARCH" == "x86_64" ]]; then
    ARCH_TAG="x86_64"
elif [[ "$ARCH" == "aarch64" ]]; then
    ARCH_TAG="aarch64"
else
    echo "Unsupported architecture: $ARCH"
    exit 1
fi

# Check if already installed and at correct version
if [[ -x "$INSTALL_DIR/stalwart" ]]; then
    CURRENT_VERSION=$("$INSTALL_DIR/stalwart" --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' || true)
    if [[ "$CURRENT_VERSION" == "$VERSION" ]]; then
        echo "Stalwart $VERSION already installed. Skipping."
        exit 0
    fi
fi

# Create user and directories
id -u "$USER" &>/dev/null || useradd -r -s /bin/false -d "$DATA_DIR" "$USER"
mkdir -p "$INSTALL_DIR" "$DATA_DIR" "$CONFIG_DIR" /var/log/stalwart
chown -R "$USER:$USER" "$DATA_DIR" /var/log/stalwart

# Download binary
URL="https://github.com/stalwartlabs/mail-server/releases/download/v${VERSION}/stalwart-mail-${ARCH_TAG}-unknown-linux-gnu.tar.gz"
echo "Downloading Stalwart $VERSION from $URL"
curl -fsSL -o /tmp/stalwart.tar.gz "$URL"

# Backup existing binary before overwrite
if [[ -f "$INSTALL_DIR/stalwart" ]]; then
    cp "$INSTALL_DIR/stalwart" "$INSTALL_DIR/stalwart.backup"
    echo "Existing binary backed up to $INSTALL_DIR/stalwart.backup"
fi

# Extract
tar -xzf /tmp/stalwart.tar.gz -C "$INSTALL_DIR" --strip-components=1
chmod +x "$INSTALL_DIR/stalwart"
rm -f /tmp/stalwart.tar.gz

# Ensure config directory has a minimal config (admin should replace with real config)
if [[ ! -f "$CONFIG_DIR/stalwart.toml" ]]; then
    cat > "$CONFIG_DIR/stalwart.toml" <<'EOF'
# Stalwart Mail Server Configuration
# Replace with your full configuration or provision via API
[server]
hostname = "mail.example.com"

[storage]
store = "rocksdb"
path = "/var/lib/stalwart"

[directory]
type = "internal"
EOF
    chown "$USER:$USER" "$CONFIG_DIR/stalwart.toml"
fi

# Create systemd service
if [[ ! -f "$SERVICE_FILE" ]] || ! grep -q "$VERSION" "$SERVICE_FILE" 2>/dev/null; then
    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Stalwart Mail Server v${VERSION}
After=network.target

[Service]
Type=simple
User=${USER}
Group=${USER}
WorkingDirectory=${DATA_DIR}
ExecStart=${INSTALL_DIR}/stalwart --config ${CONFIG_DIR}/stalwart.toml
ExecReload=/bin/kill -HUP \$MAINPID
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=stalwart

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${DATA_DIR} /var/log/stalwart
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    echo "Systemd service installed at $SERVICE_FILE"
fi

# Enable and start
systemctl enable stalwart
if systemctl is-active --quiet stalwart; then
    systemctl restart stalwart
    echo "Stalwart restarted."
else
    systemctl start stalwart
    echo "Stalwart started."
fi

echo "Stalwart $VERSION installed successfully."
echo "Binary: $INSTALL_DIR/stalwart"
echo "Config: $CONFIG_DIR/stalwart.toml"
echo "Data:   $DATA_DIR"
echo "Logs:   journalctl -u stalwart -f"
