#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

if ! python3 -m ruff --version >/dev/null 2>&1; then
  echo "ruff is required for pre-commit checks."
  echo "Install it first, for example: pip install ruff"
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "node is required for JavaScript syntax checks."
  exit 1
fi

echo "Running Ruff autofix"
python3 -m ruff check --fix app tests scripts

echo "Running Ruff validation"
python3 -m ruff check app tests scripts

echo "Running Python syntax checks"
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('app/main.py').read_text())"
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('app/api/app.py').read_text())"
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('app/domain/schemas.py').read_text())"
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('app/services/user_service.py').read_text())"

echo "Running JavaScript syntax checks"
node --check app/static/js/landing.js
node --check app/static/js/api-docs.js

echo "Pre-commit checks completed"
