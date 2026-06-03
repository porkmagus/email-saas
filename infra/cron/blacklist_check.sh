#!/bin/bash
set -euo pipefail

# blacklist_check.sh
# Check Spamhaus, Barracuda, SURBL for VPS-2 public IP
# Runs on VPS-2 (Mail). Alerts via webhook or email.

# Required env vars:
#   VPS2_PUBLIC_IP       (e.g., 1.2.3.4)
#   ALERT_WEBHOOK_URL    (optional, e.g., Slack/Discord)
#   ALERT_EMAIL          (optional)
#   STALWART_API_TOKEN   (to suspend outbound if blacklisted)
#   STALWART_BASE_URL    (e.g., http://localhost:8080)

IP="${VPS2_PUBLIC_IP:-}"
ALERT_WEBHOOK="${ALERT_WEBHOOK_URL:-}"
ALERT_EMAIL="${ALERT_EMAIL:-}"

if [[ -z "$IP" ]]; then
    echo "Error: VPS2_PUBLIC_IP not set"
    exit 1
fi

# Reverse IP for DNSBL lookups
REV_IP=$(echo "$IP" | awk -F. '{print $4"."$3"."$2"."$1}')

BLACKLISTS=(
    "zen.spamhaus.org"
    "b.barracudacentral.org"
    "multi.surbl.org"
    "bl.spamcop.net"
    "dnsbl.sorbs.net"
)

LISTED=""
for BL in "${BLACKLISTS[@]}"; do
    if dig +short "${REV_IP}.${BL}" A >/dev/null 2>&1; then
        LISTED="${LISTED}${BL} "
    fi
done

if [[ -n "$LISTED" ]]; then
    MSG="ALERT: IP ${IP} is listed on blacklists: ${LISTED}"
    echo "$(date -Iseconds) $MSG"

    # Webhook alert
    if [[ -n "$ALERT_WEBHOOK" ]]; then
        curl -s -X POST -H "Content-Type: application/json" \
            -d "{\"text\":\"${MSG}\"}" \
            "$ALERT_WEBHOOK" || true
    fi

    # Email alert (via local mail if available)
    if [[ -n "$ALERT_EMAIL" ]]; then
        echo "$MSG" | mail -s "[ALERT] Blacklist Check" "$ALERT_EMAIL" || true
    fi

    # Optionally suspend outbound via Stalwart API
    if [[ -n "${STALWART_API_TOKEN:-}" && -n "${STALWART_BASE_URL:-}" ]]; then
        echo "Attempting to suspend outbound mail via Stalwart API..."
        curl -s -X PATCH -H "Authorization: Bearer $STALWART_API_TOKEN" \
            -H "Content-Type: application/json" \
            -d '{"outbound": {"enabled": false}}' \
            "${STALWART_BASE_URL}/api/server/queue" || true
    fi

    exit 1
else
    echo "$(date -Iseconds) IP ${IP} is clean on all checked blacklists."
    exit 0
fi
