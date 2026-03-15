#!/usr/bin/env bash

set -euo pipefail

DEPLOY_HOST="${DEPLOY_HOST:?DEPLOY_HOST is required}"
DEPLOY_USER="${DEPLOY_USER:?DEPLOY_USER is required}"
DEPLOY_PATH="${DEPLOY_PATH:?DEPLOY_PATH is required}"
DEPLOY_SERVICE="${DEPLOY_SERVICE:?DEPLOY_SERVICE is required}"
DEPLOY_OWNER="${DEPLOY_OWNER:?DEPLOY_OWNER is required}"
SSH_KEY_PATH="${SSH_KEY_PATH:?SSH_KEY_PATH is required}"

DATE_TAG="$(date +%Y%m%d-%H%M%S)"
ARCHIVE_NAME="release-${DATE_TAG}.tar.gz"
TMP_ARCHIVE="/tmp/${ARCHIVE_NAME}"
REMOTE_TMP_ARCHIVE="/tmp/${ARCHIVE_NAME}"
REMOTE_BACKUP_DIR="${DEPLOY_PATH}/.deploy-backups/${DATE_TAG}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

tar \
  --exclude-vcs \
  --exclude=".github" \
  --exclude=".gitignore" \
  --exclude="deploy_key" \
  --exclude="deploy_key.pub" \
  --exclude="__pycache__" \
  --exclude=".DS_Store" \
  -czf "$TMP_ARCHIVE" .

ssh -o BatchMode=yes -i "$SSH_KEY_PATH" "${DEPLOY_USER}@${DEPLOY_HOST}" "mkdir -p '${REMOTE_BACKUP_DIR}'"
scp -i "$SSH_KEY_PATH" "$TMP_ARCHIVE" "${DEPLOY_USER}@${DEPLOY_HOST}:${REMOTE_TMP_ARCHIVE}"

ssh -o BatchMode=yes -i "$SSH_KEY_PATH" "${DEPLOY_USER}@${DEPLOY_HOST}" "\
  cp '${DEPLOY_PATH}/app/main.py' '${REMOTE_BACKUP_DIR}/main.py' && \
  cp '${DEPLOY_PATH}/app/static/pages/landing.html' '${REMOTE_BACKUP_DIR}/landing.html' && \
  cp '${DEPLOY_PATH}/app/static/js/landing.js' '${REMOTE_BACKUP_DIR}/landing.js' && \
  tar -xzf '${REMOTE_TMP_ARCHIVE}' -C '${DEPLOY_PATH}' && \
  chown -R '${DEPLOY_OWNER}' '${DEPLOY_PATH}' && \
  systemctl restart '${DEPLOY_SERVICE}' && \
  sleep 2 && \
  systemctl is-active '${DEPLOY_SERVICE}' && \
  curl -fsS http://127.0.0.1:8000/health"

rm -f "$TMP_ARCHIVE"
