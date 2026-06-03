#!/bin/bash
set -euo pipefail

# daily_backups.sh
# PostgreSQL dump + Restic backup to S3-compatible storage
# Runs on VPS-1 (App)

# Required env vars (from .env or systemd EnvironmentFile):
#   BACKUP_S3_ENDPOINT      e.g., s3.wasabisys.com
#   BACKUP_S3_BUCKET        e.g., email-saas-backups
#   BACKUP_S3_ACCESS_KEY
#   BACKUP_S3_SECRET_KEY
#   BACKUP_RESTIC_PASSWORD  (encryption key)
#   DATABASE_URL            (for pg_dump)
#   BACKUP_RETENTION_DAYS   (default: 30)

BACKUP_DIR="/backups/postgresql"
RETENTION="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DUMP_FILE="${BACKUP_DIR}/email_saas_${TIMESTAMP}.sql.gz"

# Parse database credentials from DATABASE_URL
DB_URL="${DATABASE_URL:-}"
if [[ -z "$DB_URL" ]]; then
    echo "Error: DATABASE_URL not set"
    exit 1
fi

# Extract host, port, user, pass, db using simple regex
DB_HOST=$(echo "$DB_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo "$DB_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_USER=$(echo "$DB_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_PASS=$(echo "$DB_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
DB_NAME=$(echo "$DB_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

mkdir -p "$BACKUP_DIR"

# Dump PostgreSQL
export PGPASSWORD="$DB_PASS"
echo "Dumping PostgreSQL database: $DB_NAME"
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --no-owner --no-privileges | gzip > "$DUMP_FILE"
unset PGPASSWORD

echo "Dump complete: $DUMP_FILE"

# Restic backup to S3
if [[ -n "${BACKUP_S3_ENDPOINT:-}" && -n "${BACKUP_RESTIC_PASSWORD:-}" ]]; then
    export AWS_ACCESS_KEY_ID="${BACKUP_S3_ACCESS_KEY:-}"
    export AWS_SECRET_ACCESS_KEY="${BACKUP_S3_SECRET_KEY:-}"
    export RESTIC_PASSWORD="${BACKUP_RESTIC_PASSWORD}"

    RESTIC_REPO="s3:${BACKUP_S3_ENDPOINT}/${BACKUP_S3_BUCKET:-email-saas-backups}"

    # Initialize repo if not exists
    if ! restic -r "$RESTIC_REPO" snapshots >/dev/null 2>&1; then
        echo "Initializing Restic repository..."
        restic -r "$RESTIC_REPO" init
    fi

    echo "Running Restic backup..."
    restic -r "$RESTIC_REPO" backup \
        --tag "daily,postgres" \
        "$BACKUP_DIR" \
        /opt/email-saas/.env \
        /etc/nginx/sites-available \
        /etc/stalwart

    echo "Forgetting old snapshots..."
    restic -r "$RESTIC_REPO" forget \
        --tag "daily,postgres" \
        --keep-daily 7 \
        --keep-weekly 4 \
        --keep-monthly 3 \
        --prune

    echo "Restic backup complete."
fi

# Cleanup local dumps older than retention
find "$BACKUP_DIR" -name "email_saas_*.sql.gz" -mtime +$RETENTION -delete

echo "Backup finished at $(date -Iseconds)"
