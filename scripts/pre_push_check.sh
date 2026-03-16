#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

if ! python3 -m pytest --version >/dev/null 2>&1; then
  echo "pytest is required for pre-push checks."
  echo "Install project test dependencies first."
  echo "Example: python3 -m pip install -r requirements.txt pytest httpx"
  exit 1
fi

echo "Running pytest"
python3 -m pytest

echo "Pre-push checks completed"
