#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

cd "$ROOT_DIR"

if ! "$PYTHON_BIN" -m pytest --version >/dev/null 2>&1; then
  echo "pytest is required for pre-push checks."
  echo "Install project test dependencies first."
  echo "Example: python3 -m pip install -r backend/requirements.txt pytest httpx"
  exit 1
fi

echo "Running pytest"
"$PYTHON_BIN" -m pytest

if [[ -f "frontend/package.json" ]]; then
  echo "Running frontend build"
  npm --prefix frontend run build
else
  echo "Frontend source not present in this repository, skipping frontend build"
fi

echo "Pre-push checks completed"
