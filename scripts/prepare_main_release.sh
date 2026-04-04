#!/usr/bin/env bash

set -euo pipefail

EXPECTED_SOURCE_BRANCH="${EXPECTED_SOURCE_BRANCH:-develop}"
RELEASE_BRANCH="${1:-codex/release-main}"
BACKEND_VERSION="${2:-}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CURRENT_BRANCH="$(git branch --show-current)"

if [[ "$CURRENT_BRANCH" != "$EXPECTED_SOURCE_BRANCH" ]]; then
  echo "This script must be run from ${EXPECTED_SOURCE_BRANCH}. Current branch: ${CURRENT_BRANCH}" >&2
  exit 1
fi

if [[ -n "$(git status --short)" ]]; then
  echo "Working tree must be clean before preparing a production release branch." >&2
  exit 1
fi

git checkout -b "$RELEASE_BRANCH"

if [[ -n "$BACKEND_VERSION" ]]; then
  if [[ ! "$BACKEND_VERSION" =~ ^[0-9]+(\.[0-9]+){2}([.-][0-9A-Za-z]+)*$ ]]; then
    echo "Backend version must look like semver (for example 1.2.3 or 1.2.3-rc1). Current value: $BACKEND_VERSION" >&2
    exit 1
  fi

  printf '%s\n' "$BACKEND_VERSION" > backend/VERSION
fi

STAGING_ONLY_PATHS=(
  ".github/workflows/staging.yml"
  "deploy/nginx/staging-api.wobbly.site.conf"
  "deploy/systemd/rating-service-staging.service"
  "docs/STAGING.md"
)

for path in "${STAGING_ONLY_PATHS[@]}"; do
  if [[ -e "$path" ]]; then
    git rm -f "$path"
  fi
done

cat <<EOF
Release branch prepared: ${RELEASE_BRANCH}

Next steps:
1. Review production-facing docs and surfaces.
2. Commit the staging cleanup$(if [[ -n "$BACKEND_VERSION" ]]; then printf ' and backend version bump (%s)' "$BACKEND_VERSION"; fi) on ${RELEASE_BRANCH}.
3. Merge ${RELEASE_BRANCH} into main instead of merging develop directly.
4. Push main and let the production pipeline create tag backend/v$(if [[ -n "$BACKEND_VERSION" ]]; then printf '%s' "$BACKEND_VERSION"; else ./scripts/read_backend_version.sh; fi).
EOF
