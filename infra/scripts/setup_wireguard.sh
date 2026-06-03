#!/bin/bash
set -euo pipefail

# setup_wireguard.sh
# Set up WireGuard VPN between VPS-1 (App) and VPS-2 (Mail)
# Idempotent: will re-create config if it does not match expected values
#
# Usage on VPS-1:
#   ROLE=server WG_IP=10.0.0.1 PEER_IP=10.0.0.2 PEER_PUBLIC_IP=<vps2-public> ./setup_wireguard.sh
# Usage on VPS-2:
#   ROLE=client WG_IP=10.0.0.2 PEER_IP=10.0.0.1 PEER_PUBLIC_IP=<vps1-public> ./setup_wireguard.sh

ROLE="${ROLE:-server}"          # server or client
WG_IP="${WG_IP:-10.0.0.1}"
PEER_IP="${PEER_IP:-10.0.0.2}"
PEER_PUBLIC_IP="${PEER_PUBLIC_IP:-}"
WG_PORT="${WG_PORT:-51820}"
IFACE="${IFACE:-wg0}"

if [[ -z "$PEER_PUBLIC_IP" ]]; then
    echo "Error: PEER_PUBLIC_IP is required"
    exit 1
fi

if [[ "$ROLE" != "server" && "$ROLE" != "client" ]]; then
    echo "Error: ROLE must be 'server' or 'client'"
    exit 1
fi

# Install wireguard-tools
if ! command -v wg &>/dev/null; then
    apt-get update
    apt-get install -y --no-install-recommends wireguard-tools
fi

# Generate keys if missing
mkdir -p /etc/wireguard
chmod 700 /etc/wireguard

if [[ ! -f /etc/wireguard/privatekey ]]; then
    wg genkey | tee /etc/wireguard/privatekey | wg pubkey > /etc/wireguard/publickey
    chmod 600 /etc/wireguard/privatekey
fi

PRIVATE_KEY=$(cat /etc/wireguard/privatekey)
PUBLIC_KEY=$(cat /etc/wireguard/publickey)

# Generate peer key pair if missing (for pre-shared secret or manual exchange)
if [[ ! -f /etc/wireguard/peer_publickey ]]; then
    echo "NOTE: Please copy the peer public key to /etc/wireguard/peer_publickey after running this script on both sides."
fi

# Create / update config
CONFIG="/etc/wireguard/${IFACE}.conf"

if [[ "$ROLE" == "server" ]]; then
    cat > "$CONFIG" <<EOF
[Interface]
Address = ${WG_IP}/24
ListenPort = ${WG_PORT}
PrivateKey = ${PRIVATE_KEY}
PostUp = iptables -A FORWARD -i ${IFACE} -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i ${IFACE} -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
PublicKey = PLACEHOLDER_PEER_PUBLIC_KEY
AllowedIPs = ${PEER_IP}/32
PersistentKeepalive = 25
EOF
else
    cat > "$CONFIG" <<EOF
[Interface]
Address = ${WG_IP}/24
PrivateKey = ${PRIVATE_KEY}

[Peer]
PublicKey = PLACEHOLDER_PEER_PUBLIC_KEY
Endpoint = ${PEER_PUBLIC_IP}:${WG_PORT}
AllowedIPs = ${PEER_IP}/32, 10.0.0.0/24
PersistentKeepalive = 25
EOF
fi

chmod 600 "$CONFIG"

# Enable IP forwarding
sysctl -w net.ipv4.ip_forward=1
sed -i 's/#*net.ipv4.ip_forward=.*/net.ipv4.ip_forward=1/' /etc/sysctl.conf
sysctl -p

# Start / enable
systemctl enable wg-quick@${IFACE} || true
systemctl restart wg-quick@${IFACE} || wg-quick up ${IFACE}

echo "WireGuard ${IFACE} configured for ROLE=${ROLE}"
echo "This host WireGuard IP: ${WG_IP}"
echo "Peer WireGuard IP:      ${PEER_IP}"
echo "This host public key:"
cat /etc/wireguard/publickey
echo ""
echo "Next steps:"
echo "1. Exchange public keys."
echo "2. Update PLACEHOLDER_PEER_PUBLIC_KEY in ${CONFIG} with the peer's public key."
echo "3. Restart: systemctl restart wg-quick@${IFACE}"
echo "4. Test: ping ${PEER_IP}"
