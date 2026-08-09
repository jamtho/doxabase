#!/usr/bin/env bash
# Starts the workbench (now in-repo, doc 13 status note 2026-07-20) against
# a capsule and exercises: the landing page; search and a resource page
# (IRI discovered via search); the dataset page; /datasets (row counts,
# storage reachability, reference counts -- owner ask 2026-07-20); /revisions
# and a /revisions/<iri> detail page (IRI discovered via
# list_graph_revisions); /types and a /types/entities drilldown (graph+type
# discovered live via graph_types.type_overview, the same GROUP BY the page
# itself runs); a resource page whose History section is non-empty (IRI
# discovered via a revision's revision_anchors); a coordinate-bearing frame
# query against stops-series-full (the owner's hollow_frac/CASE worked
# example) rendering the map-view markup; and the method pages
# (/methods, /method?iri=, /evidence/plot) added per the knowhow-ab design-B
# trial win -- the design's own five acceptance checks (plots render as real
# images, M12 structural completeness with severity coloring, M13's
# cross-contract constrainedBy resolution, the M12->M11 dependsOnMethod edge
# rendered honestly, M13's output section not fabricating a link the graph
# doesn't assert) plus design A's shared-failure-mode cross-link check
# (stolen into the build per the judge report). Sub-IRIs (invariant/
# parameter/dependency targets) are discovered live via workbench.methods
# calls against the real capsule; only the three known contract IRIs named
# in the design docs themselves are hardcoded -- asserting HTTP 200 +
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

echo "12) coordinate-bearing frame query renders the map view (stops-series-full)"
# The map is a second renderer for query results, not a separate feature
# (owner design note, 2026-07-21): this is the owner's own worked example
# -- set a hollow_frac threshold in SQL, get classed colored points, zero
# extra UI. mmsi 338617000 is the story_kml.py demo vessel (PENNSYLVANIA).
MAP_SQL="SELECT centroid_lat, centroid_lon, start_ts, hollow_frac,
  CASE WHEN hollow_frac > 0.85 THEN 'tight'
       WHEN hollow_frac < 0.7 THEN 'hollow'
       ELSE 'mid' END AS class
FROM frame WHERE mmsi = 338617000
ORDER BY start_ts LIMIT 500"
MAP_STATUS="$(curl -s -o /tmp/smoke-body.html -w '%{http_code}' \
  "${BASE}/dataset/query" \
  --data-urlencode "iri=https://ais.study/dataset/stops-series-full" \
  --data-urlencode "sql=${MAP_SQL}")"
if [ "$MAP_STATUS" != "200" ]; then
  fail "POST ${BASE}/dataset/query (map query) -> ${MAP_STATUS}, expected 200"
fi
assert_contains 'id="results-map-view"'
assert_contains 'id="map-canvas"'
assert_contains 'id="map-payload"'
assert_contains '"lat_col": "centroid_lat"'
assert_contains '"default_color": "class"'

echo "13) methods index page"
assert_status "${BASE}/methods" 200
assert_contains "M12"
assert_contains "M13"

M11_IRI="https://ais.study/contract/m11-berth-anchor-discriminator"
M12_IRI="https://ais.study/contract/m12-stops-series"
M13_IRI="https://ais.study/contract/m13-feed-outage-attribution"
ENCODED_M11="$(python3 -c "import sys, urllib.parse as u; print(u.quote(sys.argv[1], safe=''))" "$M11_IRI")"
ENCODED_M12="$(python3 -c "import sys, urllib.parse as u; print(u.quote(sys.argv[1], safe=''))" "$M12_IRI")"
ENCODED_M13="$(python3 -c "import sys, urllib.parse as u; print(u.quote(sys.argv[1], safe=''))" "$M13_IRI")"

echo "14) M11 plot renders as an actual image, not a text citation (design-B check 1)"
assert_status "${BASE}/method?iri=${ENCODED_M11}" 200
assert_contains '<img class="evidence-plot"'
assert_contains '/evidence/plot?path=work%2Fplots%2Fm11_'
PLOT_HEADERS="$(curl -s -o /dev/null -D - "${BASE}/evidence/plot?path=work%2Fplots%2Fm11_a_radius_mean_hist.png" | tr -d '\r')"
echo "${PLOT_HEADERS}" | grep -q "^HTTP/1.1 200" || fail "GET /evidence/plot?path=work/plots/m11_a_radius_mean_hist.png did not return 200"
echo "${PLOT_HEADERS}" | grep -qi "^content-type: image/png" || fail "GET /evidence/plot did not return Content-Type: image/png"

echo "15) M12 structural completeness + severity coloring (design-B check 2)"
assert_status "${BASE}/method?iri=${ENCODED_M12}" 200
assert_contains "5 invariants"
assert_contains "7 parameters"
assert_contains "1 realization"
assert_contains "5 failure modes"
assert_contains 'class="caveat severe"'
assert_contains 'class="caveat moderate"'

echo "16) M13 cross-contract parameter reuse is visible, not hidden (design-B check 3, judge fix b)"
assert_status "${BASE}/method?iri=${ENCODED_M13}" 200
assert_contains "defined in the M12 contract, reused here by reference"
assert_contains "href=\"/method?iri=https%3A%2F%2Fais.study%2Fcontract%2Fm12-stops-series\""

echo "17) M12->M11 dependsOnMethod renders honestly, unmodified (design-B check 4, judge fix c)"
assert_status "${BASE}/method?iri=${ENCODED_M12}" 200
# method_url() percent-encodes the whole IRI (including '/'), so the link
# target appears in the rendered href as ".../pattern%2F2fb8d9b7-..." --
# check for that encoded form, not the raw IRI, which never appears as
# page text (only the M11 title text does).
assert_contains "pattern%2F2fb8d9b7-80e9-44e7-b5f9-181b2f271008"
assert_contains "<strong>Depends on:</strong>"

echo "18) M13's output section reports the real graph shape, not a prose-name-matched fabrication (design-B check 5)"
"$PYTHON" - "$CAPSULE" <<'EOF'
import sys
from pathlib import Path

from doxabase import DoxaBase

from workbench import methods

path = Path(sys.argv[1])
db = DoxaBase.open_readonly(path)
page = methods.build_method_page(path, db, "https://ais.study/contract/m13-feed-outage-attribution")

# The honest mc:-seeAlso-only panel ("datasets that cite this contract")
# must not include M13's own two output frames -- no mc: edge connects
# them to the contract today, only a name-check in free prose.
cited = {d["iri"] for d in page["output"]["cited_by"]}
assert cited == {"https://ais.study/dataset/stops-series-full"}, f"cited_by unexpected: {cited}"

# The separate, additional panel stolen from design A (pattern-level
# patternTarget/mapImplication resolution) is exactly what recovers the
# edge the mc:-only panel above cannot show -- both must be true at once.
related = {d["iri"] for d in page["output"]["related_datasets"]}
expected = {"https://ais.study/dataset/feed-outages", "https://ais.study/dataset/stop-boundary-reasons"}
assert expected <= related, f"related_datasets missing pattern-level output edges: {related}"

grain_or_meaning = (page["output"]["grain"] or "") + (page["output"]["meaning"] or "")
assert "feed_outages" in grain_or_meaning, "outputGrain/outputMeaning prose does not name feed_outages"

print("M13 output section: OK")
EOF

echo "19) shared failure modes are cross-linked across methods, not silently duplicated (design-A check 4, stolen per judge report)"
assert_status "${BASE}/method?iri=${ENCODED_M12}" 200
assert_contains "ais-sentinel-values"
# The cross-link line is HTML-adjacent but not on the same physical line as
# "Also affects:", so a single-line grep can't see it -- verify through the
# same data build_method_page() feeds the template (proves the shared-
# caveat computation actually ran, not just that both pages independently
# list their own hasFailureMode targets).
"$PYTHON" - "$CAPSULE" <<'EOF'
import sys
from pathlib import Path

from doxabase import DoxaBase

from workbench import methods

path = Path(sys.argv[1])
db = DoxaBase.open_readonly(path)

m12 = methods.build_method_page(path, db, "https://ais.study/contract/m12-stops-series")
shared = next(fm for fm in m12["failure_modes"] if fm["iri"].endswith("ais-sentinel-values"))
also = {a["short"] for a in shared["also_affects"]}
assert "M11" in also, f"M12's ais-sentinel-values card does not cross-link to M11: {also}"

m11 = methods.build_method_page(path, db, "https://ais.study/contract/m11-berth-anchor-discriminator")
assert any(fm["iri"].endswith("ais-sentinel-values") for fm in m11["failure_modes"]), \
    "M11 does not independently list ais-sentinel-values as its own failure mode"

print("Shared failure mode cross-link: OK")
EOF
assert_status "${BASE}/method?iri=${ENCODED_M11}" 200
assert_contains "ais-sentinel-values"

echo "ALL SMOKE CHECKS PASSED"
