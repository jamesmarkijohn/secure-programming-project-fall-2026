#!/bin/sh
# Takes an encrypted database backup on a schedule
# The dump is piped into age, unencrypted data never touches disk
set -eu
set -o pipefail

: "${BACKUP_PUBLIC_KEY:?Set BACKUP_PUBLIC_KEY in .env}"
INTERVAL="${BACKUP_INTERVAL_SECONDS:-86400}"
KEEP_DAYS="${BACKUP_KEEP_DAYS:-7}"

export PGPASSWORD="$POSTGRES_PASSWORD"

while true; do
    stamp=$(date -u +%Y%m%dT%H%M%SZ)
    final="/backups/gallery-$stamp.sql.age"
    partial="/backups/.gallery-$stamp.partial"

    # Write to a temporary name first, so a failed or half-written backup is never mistaken for a good one
    if pg_dump -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner \
        | age -r "$BACKUP_PUBLIC_KEY" -o "$partial"; then
        mv "$partial" "$final"
        echo "Backup written: $final"
    else
        rm -f "$partial"
        echo "Backup FAILED at $stamp" >&2
    fi

    # Delete backups older than the retention period
    find /backups -name 'gallery-*.sql.age' -mtime +"$KEEP_DAYS" -delete

    sleep "$INTERVAL"
done