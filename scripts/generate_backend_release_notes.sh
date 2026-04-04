#!/usr/bin/env bash

set -euo pipefail

CURRENT_TAG="${1:?Current backend tag is required}"
TARGET_SHA="${2:-HEAD}"

if [[ ! "$CURRENT_TAG" =~ ^backend/v ]]; then
  echo "Current tag must look like backend/v0.1.0" >&2
  exit 1
fi

CURRENT_VERSION="${CURRENT_TAG#backend/v}"
PREVIOUS_TAG=""

while IFS= read -r tag; do
  if [[ "$tag" == "$CURRENT_TAG" ]]; then
    continue
  fi
  PREVIOUS_TAG="$tag"
  break
done < <(git for-each-ref --sort=-taggerdate --format='%(refname:short)' refs/tags/backend/v*)

{
  echo "## Backend Release"
  echo
  echo "- Version: \`${CURRENT_VERSION}\`"
  echo "- Tag: \`${CURRENT_TAG}\`"
  echo "- Commit: \`$(git rev-parse --short=12 "$TARGET_SHA")\`"
  if [[ -n "$PREVIOUS_TAG" ]]; then
    echo "- Previous backend release: \`${PREVIOUS_TAG}\`"
  else
    echo "- Previous backend release: first recorded backend release"
  fi
  echo
  echo "### Production surfaces"
  echo "- https://api.wobbly.site/api/docs"
  echo "- https://api.wobbly.site/api/swagger"
  echo "- https://wobbly.site"
  echo "- https://admin.wobbly.site/production/"
  echo
  echo "### Changes"
  if [[ -n "$PREVIOUS_TAG" ]]; then
    git log --no-merges --pretty='- `%h` %s' "${PREVIOUS_TAG}..${TARGET_SHA}"
  else
    git log --no-merges --pretty='- `%h` %s' "$TARGET_SHA"
  fi
} 
