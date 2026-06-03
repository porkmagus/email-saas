#!/bin/bash
set -euo pipefail

# provision_domain.sh
# Idempotent domain provisioning via Stalwart REST API
# Reads JSON from stdin: { "domain": "example.com", "dkim_selector": "dkim" }
# Requires env vars: STALWART_BASE_URL, STALWART_API_TOKEN

STALWART_BASE_URL="${STALWART_BASE_URL:-http://localhost:8080}"
STALWART_API_TOKEN="${STALWART_API_TOKEN:-}"

if [[ -z "$STALWART_API_TOKEN" ]]; then
    echo "Error: STALWART_API_TOKEN is not set"
    exit 1
fi

# Read stdin
PAYLOAD=$(cat)
DOMAIN=$(echo "$PAYLOAD" | jq -r '.domain // empty')
SELECTOR=$(echo "$PAYLOAD" | jq -r '.dkim_selector // "dkim"')

if [[ -z "$DOMAIN" ]]; then
    echo "Error: domain is required in JSON payload"
    exit 1
fi

# Helper function for API calls
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

# Check if domain already exists
EXISTING=$(api_call GET "/api/domain/$DOMAIN" | jq -r '.type // empty')

if [[ "$EXISTING" == "domain" ]]; then
    echo "Domain '$DOMAIN' already exists. Updating DKIM selector."
    # Update DKIM if needed
    api_call PATCH "/api/domain/$DOMAIN" "$(jq -n --arg s "$SELECTOR" '{dkim: {selector: $s}}')" > /dev/null
    echo "Domain '$DOMAIN' updated."
else
    echo "Creating domain '$DOMAIN' with DKIM selector '$SELECTOR'."
    api_call POST "/api/domain" "$(jq -n --arg d "$DOMAIN" --arg s "$SELECTOR" '{type: "domain", id: $d, dkim: {selector: $s}}')" > /dev/null
    echo "Domain '$DOMAIN' created."
fi

# Return domain details
api_call GET "/api/domain/$DOMAIN"
