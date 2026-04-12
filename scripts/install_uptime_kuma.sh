#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/deploy/monitoring/uptime-kuma.compose.yml"
TARGET_DIR="${UPTIME_KUMA_INSTALL_DIR:-/opt/uptime-kuma}"
ENV_FILE="${TARGET_DIR}/.env"
DATA_DIR="${UPTIME_KUMA_DATA_DIR:-${TARGET_DIR}/data}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to install Uptime Kuma."
  exit 1
fi

mkdir -p "${TARGET_DIR}" "${DATA_DIR}"

if [[ ! -f "${ENV_FILE}" ]]; then
  cp "${ROOT_DIR}/deploy/monitoring/uptime-kuma.env.example" "${ENV_FILE}"
  echo "Created ${ENV_FILE} from template."
fi

echo "Starting Uptime Kuma..."
docker compose \
  --env-file "${ENV_FILE}" \
  -f "${COMPOSE_FILE}" \
  up -d

echo
echo "Uptime Kuma is starting."
echo "UI will be available on http://127.0.0.1:3001 by default."
echo
echo "Recommended first monitors:"
echo "  - API Health: https://api.wobbly.site/health"
echo "  - Main Site:  https://wobbly.site"
echo "  - API Ready:  https://api.wobbly.site/ready (add after the first rollout)"

