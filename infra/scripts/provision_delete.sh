#!/bin/bash
set -euo pipefail

# provision_delete.sh
# Cleanup provisioning: delete mailbox and/or domain from Stalwart
# Reads JSON from stdin:
#   { "domain": "example.com", "local_part": "user" }  # deletes mailbox
#   { "domain": "example.com" }                           # deletes domain
# Requires env vars: STALWART_BASE_URL, STALWART_API_TOKEN

STALWART_BASE_URL="${STALWART_BASE_URL:-http://localhost:8080}"
STALWART_API_TOKEN="${STALWART_API_TOKEN:-}"

if [[ -z "$STALWART_API_TOKEN" ]]; then
    echo "Error: STALWART_API_TOKEN is not set"
    exit 1
fi

PAYLOAD=$(cat)
DOMAIN=$(echo "$PAYLOAD" | jq -r '.domain // empty')
LOCAL_PART=$(echo "$PAYLOAD" | jq -r '.local_part // empty')

if [[ -z "$DOMAIN" ]]; then
    echo "Error: domain is required"
    exit 1
fi

api_call() {
    local method="$1"
    local path="$2"
    local opts=(-s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $STALWART_API_TOKEN")
    curl "${opts[@]}" -X "$method" "$STALWART_BASE_URL$path"
}

if [[ -n "$LOCAL_PART" ]]; then
    EMAIL="${LOCAL_PART}@${DOMAIN}"
    echo "Deleting mailbox: $EMAIL"
    CODE=$(api_call DELETE "/api/account/$EMAIL")
    if [[ "$CODE" == "204" || "$CODE" == "200" || "$CODE" == "404" ]]; then
        echo "Mailbox '$EMAIL' deleted (or did not exist)."
    else
        echo "Warning: unexpected HTTP $CODE deleting mailbox"
    fi
else
    echo "Deleting domain: $DOMAIN"
    # First list and delete accounts under this domain
    ACCOUNTS=$(curl -s -H "Authorization: Bearer $STALWART_API_TOKEN" \
        "$STALWART_BASE_URL/api/account?filter=endsWith(id, '@$DOMAIN')" | jq -r '.items[]?.id // empty')
    for acct in $ACCOUNTS; do
        echo "  Deleting account: $acct"
        api_call DELETE "/api/account/$acct" > /dev/null
    done
    CODE=$(api_call DELETE "/api/domain/$DOMAIN")
    if [[ "$CODE" == "204" || "$CODE" == "200" || "$CODE" == "404" ]]; then
        echo "Domain '$DOMAIN' deleted (or did not exist)."
    else
        echo "Warning: unexpected HTTP $CODE deleting domain"
    fi
fi
