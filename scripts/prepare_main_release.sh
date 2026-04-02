#!/usr/bin/env bash

set -euo pipefail

EXPECTED_SOURCE_BRANCH="${EXPECTED_SOURCE_BRANCH:-develop}"
RELEASE_BRANCH="${1:-codex/release-main}"

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
2. Commit the staging cleanup on ${RELEASE_BRANCH}.
3. Merge ${RELEASE_BRANCH} into main instead of merging develop directly.
EOF
