#!/usr/bin/env bash

set -euo pipefail

DEPLOY_HOST="${DEPLOY_HOST:?DEPLOY_HOST is required}"
DEPLOY_USER="${DEPLOY_USER:?DEPLOY_USER is required}"
DEPLOY_PATH="${DEPLOY_PATH:?DEPLOY_PATH is required}"
DEPLOY_SERVICE="${DEPLOY_SERVICE:?DEPLOY_SERVICE is required}"
DEPLOY_OWNER="${DEPLOY_OWNER:?DEPLOY_OWNER is required}"
SSH_KEY_PATH="${SSH_KEY_PATH:?SSH_KEY_PATH is required}"
DEPLOY_VENV_PATH="${DEPLOY_VENV_PATH:-${DEPLOY_PATH}/.venv}"
DEPLOY_HEALTHCHECK_URL="${DEPLOY_HEALTHCHECK_URL:-http://127.0.0.1:8000/health}"

DATE_TAG="$(date +%Y%m%d-%H%M%S)"
ARCHIVE_NAME="release-${DATE_TAG}.tar.gz"
TMP_ARCHIVE="/tmp/${ARCHIVE_NAME}"
REMOTE_TMP_ARCHIVE="/tmp/${ARCHIVE_NAME}"
REMOTE_BACKUP_DIR="${DEPLOY_PATH}/.deploy-backups/${DATE_TAG}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

if [[ -f "${ROOT_DIR}/frontend/package.json" ]]; then
  npm --prefix "${ROOT_DIR}/frontend" ci
  npm --prefix "${ROOT_DIR}/frontend" run build
fi

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
  cp '${DEPLOY_PATH}/backend/app/main.py' '${REMOTE_BACKUP_DIR}/main.py' && \
  cp '${DEPLOY_PATH}/backend/app/static/index.html' '${REMOTE_BACKUP_DIR}/index.html' && \
  tar -xzf '${REMOTE_TMP_ARCHIVE}' -C '${DEPLOY_PATH}' && \
  '${DEPLOY_VENV_PATH}/bin/python' -m pip install -r '${DEPLOY_PATH}/backend/requirements.txt' && \
  chown -R '${DEPLOY_OWNER}' '${DEPLOY_PATH}' && \
  systemctl restart '${DEPLOY_SERVICE}' && \
  for attempt in 1 2 3 4 5 6 7 8 9 10; do \
    if systemctl is-active --quiet '${DEPLOY_SERVICE}'; then \
      break; \
    fi; \
    sleep 2; \
  done && \
  systemctl is-active '${DEPLOY_SERVICE}' && \
  for attempt in 1 2 3 4 5 6 7 8 9 10; do \
    if curl -fsS '${DEPLOY_HEALTHCHECK_URL}'; then \
      exit 0; \
    fi; \
    sleep 2; \
  done; \
  journalctl -u '${DEPLOY_SERVICE}' -n 50 --no-pager; \
  exit 1"

rm -f "$TMP_ARCHIVE"
