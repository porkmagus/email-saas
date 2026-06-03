#!/bin/bash
set -euo pipefail

# provision_mailbox.sh
# Idempotent mailbox provisioning via Stalwart REST API
# Reads JSON from stdin:
#   { "domain": "example.com", "local_part": "user", "password": "secret", "quota": 1073741824 }
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
PASSWORD=$(echo "$PAYLOAD" | jq -r '.password // empty')
QUOTA=$(echo "$PAYLOAD" | jq -r '.quota // 1073741824')
DISPLAY_NAME=$(echo "$PAYLOAD" | jq -r '.display_name // ""')

if [[ -z "$DOMAIN" || -z "$LOCAL_PART" || -z "$PASSWORD" ]]; then
    echo "Error: domain, local_part, and password are required"
    exit 1
fi

EMAIL="${LOCAL_PART}@${DOMAIN}"

api_call() {
    local method="$1"
    local path="$2"
    local body="${3:-}"
    local opts=(-s -H "Authorization: Bearer $STALWART_API_TOKEN" -H "Content-Type: application/json")
    if [[ -n "$body" ]]; then
        opts+=(-d "$body")
    fi
    curl "${opts[@]}" -X "$method" "$STALWART_BASE_URL$path"
}

EXISTING=$(api_call GET "/api/account/$EMAIL" | jq -r '.type // empty')

if [[ "$EXISTING" == "account" ]]; then
    echo "Mailbox '$EMAIL' already exists. Updating password and quota."
    api_call PATCH "/api/account/$EMAIL" "$(jq -n \
        --arg pw "$PASSWORD" \
        --argjson q "$QUOTA" \
        '{password: $pw, quota: $q}')" > /dev/null
    echo "Mailbox '$EMAIL' updated."
else
    echo "Creating mailbox '$EMAIL' with quota ${QUOTA} bytes."
    api_call POST "/api/account" "$(jq -n \
        --arg email "$EMAIL" \
        --arg pw "$PASSWORD" \
        --argjson q "$QUOTA" \
        --arg name "$DISPLAY_NAME" \
        '{type: "account", id: $email, name: $name, password: $pw, quota: $q}')" > /dev/null
    echo "Mailbox '$EMAIL' created."
fi

api_call GET "/api/account/$EMAIL"
