#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/wobbly-postgres}"
LOCAL_RETENTION_DAYS="${LOCAL_RETENTION_DAYS:-7}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
HOST_TAG="${HOST_TAG:-$(hostname -s)}"
BACKUP_PREFIX="${BACKUP_PREFIX:-wobbly-postgres}"
BACKUP_BASENAME="${BACKUP_PREFIX}-${HOST_TAG}-${TIMESTAMP}"
TMP_DIR="$(mktemp -d)"
TMP_FILE="${TMP_DIR}/${BACKUP_BASENAME}.dump"
CHECKSUM_FILE="${TMP_DIR}/${BACKUP_BASENAME}.sha256"
FINAL_DIR="${BACKUP_ROOT}/daily"
FINAL_FILE="${FINAL_DIR}/${BACKUP_BASENAME}.dump"
FINAL_CHECKSUM_FILE="${FINAL_DIR}/${BACKUP_BASENAME}.sha256"
OFFSITE_ENABLED="${OFFSITE_ENABLED:-false}"
RCLONE_REMOTE="${RCLONE_REMOTE:-}"
RCLONE_DESTINATION="${RCLONE_DESTINATION:-}"

cleanup() {
  rm -rf "$TMP_DIR"
}

trap cleanup EXIT

mkdir -p "$FINAL_DIR"

if [[ -n "${DATABASE_URL:-}" ]]; then
  PG_DUMP_TARGET="$DATABASE_URL"
else
  : "${PGHOST:?PGHOST or DATABASE_URL is required}"
  : "${PGPORT:?PGPORT or DATABASE_URL is required}"
  : "${PGDATABASE:?PGDATABASE or DATABASE_URL is required}"
  : "${PGUSER:?PGUSER or DATABASE_URL is required}"
  PG_DUMP_TARGET=""
fi

if [[ -n "$PG_DUMP_TARGET" ]]; then
  pg_dump \
    --format=custom \
    --compress=9 \
    --file="$TMP_FILE" \
    "$PG_DUMP_TARGET"
else
  pg_dump \
    --format=custom \
    --compress=9 \
    --file="$TMP_FILE"
fi

shasum -a 256 "$TMP_FILE" > "$CHECKSUM_FILE"

mv "$TMP_FILE" "$FINAL_FILE"
mv "$CHECKSUM_FILE" "$FINAL_CHECKSUM_FILE"

ln -sfn "$FINAL_FILE" "${BACKUP_ROOT}/latest.dump"
ln -sfn "$FINAL_CHECKSUM_FILE" "${BACKUP_ROOT}/latest.sha256"

find "$FINAL_DIR" -type f -name '*.dump' -mtime "+${LOCAL_RETENTION_DAYS}" -delete
find "$FINAL_DIR" -type f -name '*.sha256' -mtime "+${LOCAL_RETENTION_DAYS}" -delete

if [[ "$OFFSITE_ENABLED" == "true" ]]; then
  : "${RCLONE_REMOTE:?RCLONE_REMOTE is required when OFFSITE_ENABLED=true}"
  : "${RCLONE_DESTINATION:?RCLONE_DESTINATION is required when OFFSITE_ENABLED=true}"

  rclone copyto "$FINAL_FILE" "${RCLONE_REMOTE}:${RCLONE_DESTINATION}/$(basename "$FINAL_FILE")"
  rclone copyto "$FINAL_CHECKSUM_FILE" "${RCLONE_REMOTE}:${RCLONE_DESTINATION}/$(basename "$FINAL_CHECKSUM_FILE")"
fi

printf 'Backup created: %s\n' "$FINAL_FILE"
