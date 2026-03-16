#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

echo "Running Python syntax checks"
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('app/main.py').read_text())"
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('app/core/auth.py').read_text())"
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('app/core/config.py').read_text())"
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('app/core/rate_limit.py').read_text())"
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('app/db/database.py').read_text())"
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('app/domain/schemas.py').read_text())"

echo "Running JavaScript syntax checks"
node --check app/static/js/landing.js
node --check app/static/js/api-docs.js

echo "Running Ruff"
ruff check app tests scripts

echo "Running pytest"
pytest

echo "Validating Docker Compose config"
docker compose config >/dev/null

echo "Checking API docs sync"
./scripts/check_api_docs_sync.sh

echo "CI checks completed"
