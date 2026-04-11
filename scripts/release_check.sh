#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

cd "$ROOT_DIR"

: "${TEST_DATABASE_URL:?TEST_DATABASE_URL is required for release checks}"

echo "Checking backend release prerequisites"
if ! "$PYTHON_BIN" -c "import alembic.command" >/dev/null 2>&1; then
  echo "Missing Python dependency: alembic"
  echo "Use the project virtualenv or install backend requirements before release."
  exit 1
fi

echo "Running standard backend CI checks"
./scripts/ci_check.sh

echo "Running real database integration tests"
TEST_DATABASE_URL="$TEST_DATABASE_URL" \
  "$PYTHON_BIN" -m pytest backend/tests/test_api_db_integration.py

echo "Release checks completed"
