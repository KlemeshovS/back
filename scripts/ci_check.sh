#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

echo "Running Python syntax checks"
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('app/main.py').read_text())"
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('app/auth.py').read_text())"
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('app/config.py').read_text())"
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('app/database.py').read_text())"
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('app/rate_limit.py').read_text())"
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('app/schemas.py').read_text())"

echo "Running JavaScript syntax checks"
node --check app/static/js/landing.js
node --check app/static/js/api-docs.js

echo "Validating Docker Compose config"
docker compose config >/dev/null

echo "CI checks completed"
