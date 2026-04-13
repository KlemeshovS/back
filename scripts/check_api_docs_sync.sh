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

if ! git cat-file -e "${BASE_REF}^{commit}" 2>/dev/null; then
  echo "API_DOCS_BASE_REF is not available in local git history, skipping docs sync check"
  exit 0
fi

CHANGED_FILES="$(git diff --name-only "$BASE_REF" "$HEAD_REF")"

if [[ -z "$CHANGED_FILES" ]]; then
  echo "No changed files detected for docs sync check"
  exit 0
fi

API_CHANGED=false
DOCS_CHANGED=false
FRONTEND_SOURCE_PRESENT=false

if [[ -f "frontend/package.json" ]]; then
  FRONTEND_SOURCE_PRESENT=true
fi

while IFS= read -r file; do
  # Only flag changes that affect the public API contract:
  # - route handlers (endpoints, request/response shape)
  # - API-level dependencies (auth guards, request parsing)
  # - domain schemas (request/response models visible to clients)
  # Internal helpers, services, and core utilities are excluded because
  # they do not change the public API surface.
  if [[ "$file" == backend/app/api/routes/* || "$file" == "backend/app/api/dependencies.py" || "$file" == "backend/app/domain/schemas.py" ]]; then
    API_CHANGED=true
  fi

  if [[ "$file" == "docs/MOBILE_API.md" || "$file" == "README.md" ]]; then
    DOCS_CHANGED=true
  fi

  if [[ "$FRONTEND_SOURCE_PRESENT" == "true" && ( "$file" == "frontend/src/features/docs/content.ts" || "$file" == "frontend/src/pages/ApiDocsPage.vue" ) ]]; then
    DOCS_CHANGED=true
  fi
done <<< "$CHANGED_FILES"

if [[ "$API_CHANGED" == "true" && "$DOCS_CHANGED" == "false" ]]; then
  echo "API files changed, but docs were not updated."
  echo "Update /api/docs and related API docs in the same change."
  exit 1
fi

echo "API docs sync check passed"
