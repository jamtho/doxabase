#!/usr/bin/env bash
# Starts the workbench (now in-repo, doc 13 status note 2026-07-20) against
# a capsule and exercises: the landing page; search and a resource page
# (IRI discovered via search); the dataset page; /datasets (row counts,
# storage reachability, reference counts -- owner ask 2026-07-20); /revisions
# and a /revisions/<iri> detail page (IRI discovered via
# list_graph_revisions); /types and a /types/entities drilldown (graph+type
# discovered live via graph_types.type_overview, the same GROUP BY the page
# itself runs); and a resource page whose History section is non-empty (IRI
# discovered via a revision's revision_anchors) -- asserting HTTP 200 +
# expected substrings on each.
#
# Not part of `tools/gate.sh`: it needs the optional `workbench` extra
# installed (fastapi/uvicorn/duckdb/jinja2/...) and a real capsule file,
# neither of which the core gate's clean-venv smoke should pay for. Point
# WORKBENCH_SMOKE_PYTHON at a venv with `doxabase[workbench]` installed
# (defaults to the repo's own .venv, which only has it if you ran
# `uv sync --extra workbench` there).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CAPSULE="${1:-/home/codex/ais-study/capsule.sqlite}"
PORT="${SMOKE_PORT:-8199}"
HOST="127.0.0.1"
BASE="http://${HOST}:${PORT}"
PYTHON="${WORKBENCH_SMOKE_PYTHON:-${REPO_DIR}/.venv/bin/python}"

if [ ! -x "$PYTHON" ]; then
  echo "FAIL: ${PYTHON} not found. Set WORKBENCH_SMOKE_PYTHON to a venv with doxabase[workbench] installed." >&2
  exit 1
fi
if [ ! -f "$CAPSULE" ]; then
  echo "FAIL: capsule not found at ${CAPSULE}" >&2
  exit 1
fi

LOG="$(mktemp)"
WORKBENCH_CAPSULE_PATH="$CAPSULE" "$PYTHON" -m uvicorn workbench.app:app \
  --app-dir "$REPO_DIR" --host "$HOST" --port "$PORT" >"$LOG" 2>&1 &
SERVER_PID=$!

cleanup() {
  kill "$SERVER_PID" >/dev/null 2>&1 || true
  wait "$SERVER_PID" 2>/dev/null || true
  rm -f "$LOG"
}
trap cleanup EXIT

echo "Starting workbench (pid ${SERVER_PID}) against ${CAPSULE} on ${BASE} ..."
for _ in $(seq 1 50); do
  if curl -s -o /dev/null "${BASE}/"; then
    break
  fi
  sleep 0.2
done

fail() {
  echo "FAIL: $1" >&2
  echo "--- server log ---" >&2
  cat "$LOG" >&2
  exit 1
}

assert_status() {
  local url="$1" expected="$2"
  local got
  got="$(curl -s -o /tmp/smoke-body.html -w '%{http_code}' "$url")"
  if [ "$got" != "$expected" ]; then
    fail "GET ${url} -> ${got}, expected ${expected}"
  fi
}

assert_contains() {
  local needle="$1"
  if ! grep -qF "$needle" /tmp/smoke-body.html; then
    fail "response did not contain: ${needle}"
  fi
}

echo "1) landing page"
assert_status "${BASE}/" 200
assert_contains "Project brief"
assert_contains "Datasets ("

echo "2) search"
assert_status "${BASE}/search?q=vessel" 200
assert_contains "match(es) for"

echo "3) discover a resource IRI via search"
IRI="$("$PYTHON" - "$CAPSULE" <<'EOF'
import sys
from doxabase import DoxaBase, to_dict
db = DoxaBase.open_readonly(sys.argv[1])
results = to_dict(db.search("vessel", limit=1))
print(results["matches"][0]["iri"])
EOF
)"
if [ -z "$IRI" ]; then
  fail "search returned no IRI to probe a resource page with"
fi
echo "   using IRI: ${IRI}"

echo "4) resource page"
ENCODED_IRI="$(python3 -c "import sys, urllib.parse as u; print(u.quote(sys.argv[1], safe=''))" "$IRI")"
assert_status "${BASE}/resource?iri=${ENCODED_IRI}" 200
assert_contains "$IRI"
assert_contains "Outgoing ("

echo "5) dataset page (broadcasts)"
assert_status "${BASE}/dataset?iri=https%3A%2F%2Fais.study%2Fdataset%2Fbroadcasts" 200
assert_contains "Caveats"
assert_contains "Columns ("

echo "6) revisions list"
assert_status "${BASE}/revisions" 200
assert_contains "Revision history"
assert_contains "revision(s)."

echo "7) discover a revision IRI and its detail page"
REVISION_IRI="$("$PYTHON" - "$CAPSULE" <<'EOF'
import sys
from doxabase import DoxaBase, to_dict
db = DoxaBase.open_readonly(sys.argv[1])
revisions = to_dict(db.list_graph_revisions(limit=1))["revisions"]
print(revisions[0]["iri"] if revisions else "")
EOF
)"
if [ -z "$REVISION_IRI" ]; then
  fail "list_graph_revisions returned no revision to probe /revisions/<iri> with"
fi
echo "   using revision IRI: ${REVISION_IRI}"
ENCODED_REVISION_IRI="$(python3 -c "import sys, urllib.parse as u; print(u.quote(sys.argv[1], safe='/:'))" "$REVISION_IRI")"
assert_status "${BASE}/revisions/${ENCODED_REVISION_IRI}" 200
assert_contains "${REVISION_IRI}"

echo "8) types overview page"
assert_status "${BASE}/types" 200
assert_contains "Entity types"
assert_contains "id=\"g-map\""

echo "9) discover a graph+type via the same GROUP BY the page uses, and drill down"
TYPE_LINE="$("$PYTHON" - "$CAPSULE" <<'EOF'
import sys
from workbench import graph_types
overview = graph_types.type_overview(sys.argv[1])
for g in overview:
    if g["types"]:
        top = g["types"][0]
        print(f"{g['graph']}\t{top['type_iri']}\t{top['instance_count']}")
        break
EOF
)"
if [ -z "$TYPE_LINE" ]; then
  fail "type_overview returned no graph with any rdf:type instance to drill into"
fi
TYPE_GRAPH="$(printf '%s' "$TYPE_LINE" | cut -f1)"
TYPE_IRI="$(printf '%s' "$TYPE_LINE" | cut -f2)"
TYPE_COUNT="$(printf '%s' "$TYPE_LINE" | cut -f3)"
echo "   using graph=${TYPE_GRAPH} type=${TYPE_IRI} (${TYPE_COUNT} instances)"
ENCODED_TYPE_IRI="$(python3 -c "import sys, urllib.parse as u; print(u.quote(sys.argv[1], safe=''))" "$TYPE_IRI")"
assert_status "${BASE}/types/entities?graph=${TYPE_GRAPH}&type=${ENCODED_TYPE_IRI}" 200
assert_contains "${TYPE_IRI}"
assert_contains "instance(s)."

echo "10) resource page with a non-empty History section"
HISTORY_IRI="$("$PYTHON" - "$CAPSULE" <<'EOF'
import sys
from doxabase import DoxaBase, to_dict
db = DoxaBase.open_readonly(sys.argv[1])
revisions = to_dict(db.list_graph_revisions(limit=1000))["revisions"]
for row in revisions:
    anchors = to_dict(db.describe_graph_revision(row["iri"])).get("revision_anchors") or []
    if anchors:
        print(anchors[0]["iri"])
        break
EOF
)"
if [ -z "$HISTORY_IRI" ]; then
  fail "no revision in this capsule carries a revision_anchor to probe a resource History section with"
fi
echo "   using resource IRI: ${HISTORY_IRI}"
ENCODED_HISTORY_IRI="$(python3 -c "import sys, urllib.parse as u; print(u.quote(sys.argv[1], safe=''))" "$HISTORY_IRI")"
assert_status "${BASE}/resource?iri=${ENCODED_HISTORY_IRI}" 200
assert_contains "History ("
assert_contains "revision-anchor link"

echo "11) datasets overview page"
assert_status "${BASE}/datasets" 200
assert_contains "dataset(s)."
assert_contains "Referenced by"
assert_contains "Rows (recorded snapshot)"

echo "ALL SMOKE CHECKS PASSED"
