#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="${BACKEND_VERSION_FILE:-${ROOT_DIR}/backend/VERSION}"

if [[ ! -f "$VERSION_FILE" ]]; then
  echo "Backend version file not found: $VERSION_FILE" >&2
  exit 1
fi

BACKEND_VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"

if [[ -z "$BACKEND_VERSION" ]]; then
  echo "Backend version file is empty: $VERSION_FILE" >&2
  exit 1
fi

if [[ ! "$BACKEND_VERSION" =~ ^[0-9]+(\.[0-9]+){2}([.-][0-9A-Za-z]+)*$ ]]; then
  echo "Backend version must look like semver (for example 1.2.3 or 1.2.3-rc1). Current value: $BACKEND_VERSION" >&2
  exit 1
fi

printf '%s\n' "$BACKEND_VERSION"
