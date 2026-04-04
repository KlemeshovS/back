#!/usr/bin/env bash

set -euo pipefail

DEPLOY_HOST="${DEPLOY_HOST:?DEPLOY_HOST is required}"
DEPLOY_USER="${DEPLOY_USER:?DEPLOY_USER is required}"
DEPLOY_PATH="${DEPLOY_PATH:?DEPLOY_PATH is required}"
DEPLOY_SERVICE="${DEPLOY_SERVICE:?DEPLOY_SERVICE is required}"
DEPLOY_OWNER="${DEPLOY_OWNER:?DEPLOY_OWNER is required}"
SSH_KEY_PATH="${SSH_KEY_PATH:?SSH_KEY_PATH is required}"
DEPLOY_VENV_PATH="${DEPLOY_VENV_PATH:-${DEPLOY_PATH}/.venv}"
DEPLOY_HEALTHCHECK_URL="${DEPLOY_HEALTHCHECK_URL:-http://127.0.0.1:8000/ready}"
BACKEND_VERSION_FILE="${BACKEND_VERSION_FILE:-backend/VERSION}"

DATE_TAG="$(date +%Y%m%d-%H%M%S)"
BACKEND_VERSION="$(BACKEND_VERSION_FILE="$BACKEND_VERSION_FILE" ./scripts/read_backend_version.sh)"
GIT_REF="$(git rev-parse --short=12 HEAD)"
ARCHIVE_NAME="backend-v${BACKEND_VERSION}-${GIT_REF}.tar.gz"
TMP_ARCHIVE="/tmp/${ARCHIVE_NAME}"
REMOTE_TMP_ARCHIVE="/tmp/${ARCHIVE_NAME}"
REMOTE_BACKUP_DIR="${DEPLOY_PATH}/.deploy-backups/${DATE_TAG}-v${BACKEND_VERSION}"
REMOTE_RELEASE_DIR="${DEPLOY_PATH}/.releases"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

if [[ -f "${ROOT_DIR}/frontend/package.json" ]]; then
  npm --prefix "${ROOT_DIR}/frontend" ci
  npm --prefix "${ROOT_DIR}/frontend" run build
fi

export COPYFILE_DISABLE=1

tar \
  --exclude-vcs \
  --exclude=".github" \
  --exclude=".gitignore" \
  --exclude="deploy_key" \
  --exclude="deploy_key.pub" \
  --exclude="__pycache__" \
  --exclude=".DS_Store" \
  --exclude="._*" \
  --exclude=".venv" \
  --exclude=".pytest_cache" \
  --exclude=".ruff_cache" \
  --exclude="frontend/node_modules" \
  --exclude="frontend/dist" \
  -czf "$TMP_ARCHIVE" .

ssh -o BatchMode=yes -i "$SSH_KEY_PATH" "${DEPLOY_USER}@${DEPLOY_HOST}" "mkdir -p '${REMOTE_BACKUP_DIR}' '${REMOTE_RELEASE_DIR}'"
scp -i "$SSH_KEY_PATH" "$TMP_ARCHIVE" "${DEPLOY_USER}@${DEPLOY_HOST}:${REMOTE_TMP_ARCHIVE}"

ssh -o BatchMode=yes -i "$SSH_KEY_PATH" "${DEPLOY_USER}@${DEPLOY_HOST}" "\
  if [ -f '${DEPLOY_PATH}/backend/app/main.py' ]; then \
    cp '${DEPLOY_PATH}/backend/app/main.py' '${REMOTE_BACKUP_DIR}/main.py'; \
  elif [ -f '${DEPLOY_PATH}/app/main.py' ]; then \
    cp '${DEPLOY_PATH}/app/main.py' '${REMOTE_BACKUP_DIR}/main.py'; \
  fi && \
  if [ -f '${DEPLOY_PATH}/backend/app/static/index.html' ]; then \
    cp '${DEPLOY_PATH}/backend/app/static/index.html' '${REMOTE_BACKUP_DIR}/index.html'; \
  elif [ -f '${DEPLOY_PATH}/app/static/pages/landing.html' ]; then \
    cp '${DEPLOY_PATH}/app/static/pages/landing.html' '${REMOTE_BACKUP_DIR}/landing.html'; \
  fi && \
  cp '${REMOTE_TMP_ARCHIVE}' '${REMOTE_RELEASE_DIR}/${ARCHIVE_NAME}' && \
  tar -xzf '${REMOTE_TMP_ARCHIVE}' -C '${DEPLOY_PATH}' && \
  find '${DEPLOY_PATH}' -name '._*' -delete && \
  '${DEPLOY_VENV_PATH}/bin/python' -m pip install -r '${DEPLOY_PATH}/backend/requirements.txt' && \
  printf '%s\n' '${BACKEND_VERSION}' > '${DEPLOY_PATH}/.backend-release-version' && \
  printf '%s\n' '${GIT_REF}' > '${DEPLOY_PATH}/.backend-release-ref' && \
  printf '%s\n' 'backend/v${BACKEND_VERSION}' > '${DEPLOY_PATH}/.backend-release-tag' && \
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
