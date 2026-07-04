#!/usr/bin/env bash
# Full DoxaBase gate (program Phase 1.4): tests, RDF validation, budget
# scoreboard, working-tree hygiene, then a wheel build + install smoke in a
# clean venv outside the repo. CI runs exactly this script.
set -euo pipefail
cd "$(dirname "$0")/.."

uv sync --quiet
uv run pytest -q -n 16
uv run python tools/validate_rdf.py
uv run python tools/scoreboard.py --check
git diff --check

uv build --quiet
WHEEL="$(ls -t dist/doxabase-*.whl | head -1)"

SMOKE_DIR="$(mktemp -d -t doxabase-gate-XXXXXX)"
trap 'rm -rf "$SMOKE_DIR"' EXIT
uv venv --quiet "$SMOKE_DIR/venv"
VIRTUAL_ENV="$SMOKE_DIR/venv" uv pip install --quiet "$WHEEL"
cp tools/install_smoke.py "$SMOKE_DIR/"
(cd "$SMOKE_DIR" && ./venv/bin/python install_smoke.py)
(cd "$SMOKE_DIR" && ./venv/bin/doxabase-mcp --help > /dev/null)

echo "gate: all checks passed"
