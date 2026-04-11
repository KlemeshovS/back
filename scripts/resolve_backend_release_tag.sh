#!/usr/bin/env bash

set -euo pipefail

TARGET_SHA="${1:-HEAD}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

VERSION="$(./scripts/read_backend_version.sh)"
BASE_TAG="backend/v${VERSION}"

resolve_tag() {
  local candidate="$1"

  if git rev-parse "$candidate" >/dev/null 2>&1; then
    local existing_sha
    existing_sha="$(git rev-list -n 1 "$candidate")"
    if [[ "$existing_sha" == "$TARGET_SHA" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
    return 1
  fi

  printf '%s\n' "$candidate"
  return 0
}

if resolve_tag "$BASE_TAG" >/dev/null; then
  resolve_tag "$BASE_TAG"
  exit 0
fi

index=1
while true; do
  candidate="${BASE_TAG}-r${index}"
  if resolve_tag "$candidate" >/dev/null; then
    resolve_tag "$candidate"
    exit 0
  fi
  index=$((index + 1))
done
