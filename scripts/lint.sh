#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

cd "$ROOT_DIR"

echo "Running Python syntax checks"
"$PYTHON_BIN" -c "import ast, pathlib; ast.parse(pathlib.Path('backend/app/main.py').read_text())"
"$PYTHON_BIN" -c "import ast, pathlib; ast.parse(pathlib.Path('backend/app/core/auth.py').read_text())"
"$PYTHON_BIN" -c "import ast, pathlib; ast.parse(pathlib.Path('backend/app/core/config.py').read_text())"
"$PYTHON_BIN" -c "import ast, pathlib; ast.parse(pathlib.Path('backend/app/core/rate_limit.py').read_text())"
"$PYTHON_BIN" -c "import ast, pathlib; ast.parse(pathlib.Path('backend/app/db/database.py').read_text())"
"$PYTHON_BIN" -c "import ast, pathlib; ast.parse(pathlib.Path('backend/app/domain/schemas.py').read_text())"

echo "Running Ruff lint"
"$PYTHON_BIN" -m ruff check backend/app backend/tests scripts

echo "Validating Docker Compose config"
docker compose config >/dev/null

echo "Checking API docs sync"
./scripts/check_api_docs_sync.sh
