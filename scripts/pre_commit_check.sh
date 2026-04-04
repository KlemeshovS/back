#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

cd "$ROOT_DIR"

if ! "$PYTHON_BIN" -m ruff --version >/dev/null 2>&1; then
  echo "ruff is required for pre-commit checks."
  echo "Install it first, for example: pip install ruff"
  exit 1
fi

if [[ -f "frontend/package.json" ]] && ! command -v node >/dev/null 2>&1; then
  echo "node is required for frontend checks."
  exit 1
fi

echo "Running Ruff autofix"
"$PYTHON_BIN" -m ruff check --fix backend/app backend/tests scripts

echo "Running Ruff validation"
"$PYTHON_BIN" -m ruff check backend/app backend/tests scripts

echo "Running Python syntax checks"
"$PYTHON_BIN" -c "import ast, pathlib; ast.parse(pathlib.Path('backend/app/main.py').read_text())"
"$PYTHON_BIN" -c "import ast, pathlib; ast.parse(pathlib.Path('backend/app/api/app.py').read_text())"
"$PYTHON_BIN" -c "import ast, pathlib; ast.parse(pathlib.Path('backend/app/domain/schemas.py').read_text())"
"$PYTHON_BIN" -c "import ast, pathlib; ast.parse(pathlib.Path('backend/app/services/user_service.py').read_text())"

if [[ -f "frontend/package.json" ]]; then
  echo "Running frontend lint"
  npm --prefix frontend run lint

  echo "Running frontend format check"
  npm --prefix frontend run format
else
  echo "Frontend source not present in this repository, skipping frontend pre-commit checks"
fi

echo "Pre-commit checks completed"
