#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

BASE_REF="${API_DOCS_BASE_REF:-}"
HEAD_REF="${API_DOCS_HEAD_REF:-HEAD}"

if [[ -z "$BASE_REF" ]]; then
  echo "API_DOCS_BASE_REF is not set, skipping docs sync check"
  exit 0
fi

CHANGED_FILES="$(git diff --name-only "$BASE_REF" "$HEAD_REF")"

if [[ -z "$CHANGED_FILES" ]]; then
  echo "No changed files detected for docs sync check"
  exit 0
fi

API_CHANGED=false
DOCS_CHANGED=false

while IFS= read -r file; do
  if [[ "$file" == app/api/routes/* || "$file" == "app/api/dependencies.py" || "$file" == "app/api/app.py" || "$file" == app/services/* || "$file" == app/domain/* || "$file" == app/core/* || "$file" == "app/main.py" || "$file" == "app/schemas.py" ]]; then
    API_CHANGED=true
  fi

  if [[ "$file" == "app/static/js/api-docs.js" || "$file" == "app/static/pages/api-docs.html" || "$file" == "MOBILE_API.md" || "$file" == "README.md" ]]; then
    DOCS_CHANGED=true
  fi
done <<< "$CHANGED_FILES"

if [[ "$API_CHANGED" == "true" && "$DOCS_CHANGED" == "false" ]]; then
  echo "API files changed, but docs were not updated."
  echo "Update /api/docs and related API docs in the same change."
  exit 1
fi

echo "API docs sync check passed"
