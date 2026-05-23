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
RELEASE_TAG="${RELEASE_TAG:-}"

DATE_TAG="$(date +%Y%m%d-%H%M%S)"
BACKEND_VERSION="$(BACKEND_VERSION_FILE="$BACKEND_VERSION_FILE" ./scripts/read_backend_version.sh)"
if [[ -z "$RELEASE_TAG" ]]; then
  RELEASE_TAG="backend/v${BACKEND_VERSION}"
fi
GIT_REF="$(git rev-parse --short=12 HEAD)"
ARCHIVE_NAME="backend-v${BACKEND_VERSION}-${GIT_REF}.tar.gz"
TMP_ARCHIVE="/tmp/${ARCHIVE_NAME}"
REMOTE_TMP_ARCHIVE="/tmp/${ARCHIVE_NAME}"
REMOTE_BACKUP_DIR="${DEPLOY_PATH}/.deploy-backups/${DATE_TAG}-v${BACKEND_VERSION}"
REMOTE_RELEASE_DIR="${DEPLOY_PATH}/.releases"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

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
  --exclude="frontend" \
  -czf "$TMP_ARCHIVE" .

ssh -o BatchMode=yes -i "$SSH_KEY_PATH" "${DEPLOY_USER}@${DEPLOY_HOST}" "mkdir -p '${REMOTE_BACKUP_DIR}' '${REMOTE_RELEASE_DIR}'"
scp -i "$SSH_KEY_PATH" "$TMP_ARCHIVE" "${DEPLOY_USER}@${DEPLOY_HOST}:${REMOTE_TMP_ARCHIVE}"

ssh -o BatchMode=yes -i "$SSH_KEY_PATH" "${DEPLOY_USER}@${DEPLOY_HOST}" \
  bash -s -- \
  "$DEPLOY_PATH" \
  "$REMOTE_BACKUP_DIR" \
  "$REMOTE_TMP_ARCHIVE" \
  "$REMOTE_RELEASE_DIR" \
  "$ARCHIVE_NAME" \
  "$DEPLOY_VENV_PATH" \
  "$BACKEND_VERSION" \
  "$GIT_REF" \
  "$RELEASE_TAG" \
  "$DEPLOY_OWNER" \
  "$DEPLOY_SERVICE" \
  "$DEPLOY_HEALTHCHECK_URL" <<'REMOTE'
set -euo pipefail

deploy_path="$1"
remote_backup_dir="$2"
remote_tmp_archive="$3"
remote_release_dir="$4"
archive_name="$5"
configured_venv_path="$6"
backend_version="$7"
git_ref="$8"
release_tag="$9"
deploy_owner="${10}"
deploy_service="${11}"
deploy_healthcheck_url="${12}"

if [ -f "${deploy_path}/backend/app/main.py" ]; then
  cp "${deploy_path}/backend/app/main.py" "${remote_backup_dir}/main.py"
elif [ -f "${deploy_path}/app/main.py" ]; then
  cp "${deploy_path}/app/main.py" "${remote_backup_dir}/main.py"
fi

cp "${remote_tmp_archive}" "${remote_release_dir}/${archive_name}"
tar -xzf "${remote_tmp_archive}" -C "${deploy_path}"
find "${deploy_path}" -name '._*' -delete

service_execstart="$(systemctl cat "${deploy_service}" 2>/dev/null | sed -n 's/^ExecStart=//p' | head -n 1)"
service_venv_path="$(printf '%s\n' "${service_execstart}" | sed -n 's#^\([^ ]*/\.venv\)/bin/uvicorn.*#\1#p')"

if [[ -n "${service_venv_path}" ]]; then
  effective_venv_path="${service_venv_path}"
elif [[ -n "${configured_venv_path}" ]]; then
  effective_venv_path="${configured_venv_path}"
else
  effective_venv_path="${deploy_path}/.venv"
fi

echo "Using deploy venv: ${effective_venv_path}"

if [[ ! -x "${effective_venv_path}/bin/python" ]]; then
  echo "Creating missing venv at ${effective_venv_path}"
  python3 -m venv "${effective_venv_path}"
fi

"${effective_venv_path}/bin/python" -m pip install --upgrade pip
"${effective_venv_path}/bin/python" -m pip install -r "${deploy_path}/backend/requirements.txt"

printf '%s\n' "${backend_version}" > "${deploy_path}/.backend-release-version"
printf '%s\n' "${git_ref}" > "${deploy_path}/.backend-release-ref"
printf '%s\n' "${release_tag}" > "${deploy_path}/.backend-release-tag"
chown -R "${deploy_owner}" "${deploy_path}"

cd "${deploy_path}/backend"
if [ -f "${deploy_path}/backend/.env" ]; then
  set -a; source "${deploy_path}/backend/.env"; set +a
elif [ -f "${deploy_path}/.env" ]; then
  set -a; source "${deploy_path}/.env"; set +a
fi
echo "=== Alembic current revision ==="
alembic_current="$("${effective_venv_path}/bin/python" -m alembic current 2>&1)"
echo "${alembic_current}"
if echo "${alembic_current}" | grep -qvE "^INFO|^WARNING|^$"; then
  echo "Alembic revision found, upgrading normally"
else
  echo "No alembic revision found, stamping baseline 20260512_000008"
  "${effective_venv_path}/bin/python" -m alembic stamp 20260512_000008
fi
echo "=== Running alembic upgrade head ==="
"${effective_venv_path}/bin/python" -m alembic upgrade head
echo "=== Alembic upgrade done ==="

systemctl restart "${deploy_service}"
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  if systemctl is-active --quiet "${deploy_service}"; then
    break
  fi
  sleep 2
done

systemctl is-active "${deploy_service}"

for attempt in 1 2 3 4 5 6 7 8 9 10; do
  if curl -fsS "${deploy_healthcheck_url}"; then
    exit 0
  fi
  sleep 2
done

journalctl -u "${deploy_service}" -n 50 --no-pager
exit 1
REMOTE

rm -f "$TMP_ARCHIVE"
