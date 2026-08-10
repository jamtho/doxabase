#!/usr/bin/env bash
# Exercises `doxabase-observatory export` (doc 11's exporter, workbench/
# observatory.py) against a real capsule: exports to a temp directory, then
# asserts the bundle's structure and content -- manifest fields, both
# layers' feature counts, the 17-vessel stopped sub-population, a known
# story feature's full claim/evidence chain, and that every viewer asset
# (index.html/observatory.js/observatory.css/vendored Leaflet) is present.
#
# Not part of `tools/gate.sh`: it needs the optional `workbench` extra
# installed (duckdb) and live access to the real capsule + its described
# S3 frames (MINIO_ENDPOINT/MINIO_ACCESS_KEY/MINIO_SECRET_KEY), neither of
# which the core gate's clean-venv smoke should pay for -- the same
# reasoning tools/workbench_smoke.sh already documents for itself. Point
# OBSERVATORY_SMOKE_PYTHON at a venv with `doxabase[workbench]` installed
# if the repo's own .venv doesn't have it.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CAPSULE="${1:-/home/codex/ais-study/capsule.sqlite}"
PYTHON="${OBSERVATORY_SMOKE_PYTHON:-${REPO_DIR}/.venv/bin/python}"

if [ ! -x "$PYTHON" ]; then
  echo "FAIL: ${PYTHON} not found. Set OBSERVATORY_SMOKE_PYTHON to a venv with doxabase[workbench] installed." >&2
  exit 1
fi
if [ ! -f "$CAPSULE" ]; then
  echo "FAIL: capsule not found at ${CAPSULE}" >&2
  exit 1
fi

OUTDIR="$(mktemp -d -t doxabase-observatory-smoke-XXXXXX)"
cleanup() { rm -rf "$OUTDIR"; }
trap cleanup EXIT

echo "Exporting ${CAPSULE} -> ${OUTDIR} ..."
(cd "$REPO_DIR" && "$PYTHON" -m workbench.observatory export "$CAPSULE" "$OUTDIR")

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

echo "1) bundle structure"
for f in manifest.json index.html observatory.js observatory.css \
         layers/story-map.geojson layers/shuttle-census.geojson \
         vendor/leaflet/leaflet.js vendor/leaflet/leaflet.css; do
  [ -f "${OUTDIR}/${f}" ] || fail "missing expected bundle file: ${f}"
done

echo "2) manifest.json: format, mode, export-eligibility stamp, both layers registered"
"$PYTHON" - "$OUTDIR" <<'EOF'
import json
import sys
from pathlib import Path

outdir = Path(sys.argv[1])
manifest = json.loads((outdir / "manifest.json").read_text())

assert manifest["format"] == "doxabase.observatory_bundle.v1", manifest["format"]
assert manifest["mode"] == "expert", manifest["mode"]
assert manifest["export_eligibility"]["status"] == "local_only_pending_review", (
    manifest["export_eligibility"]["status"]
)
layer_ids = {layer["id"] for layer in manifest["layers"]}
assert layer_ids == {"story-map", "shuttle-census"}, layer_ids
for layer in manifest["layers"]:
    assert layer["feature_count"] > 0, layer

print("manifest.json: OK")
EOF

echo "3) layers/story-map.geojson: 12 promoted story features, all with parsed coordinates"
"$PYTHON" - "$OUTDIR" <<'EOF'
import json
import sys
from pathlib import Path

outdir = Path(sys.argv[1])
geojson = json.loads((outdir / "layers" / "story-map.geojson").read_text())
features = geojson["features"]
assert len(features) == 12, f"expected 12 story features, got {len(features)}"
for feature in features:
    assert feature["geometry"]["type"] in ("Point", "LineString"), feature["geometry"]["type"]
    assert feature["properties"]["provenance_ref"].startswith("provenance/")

ids = {f["id"] for f in features}
assert "368817000-berth-stay-2025" in ids, "known story feature (Gulf-coast berth stay) missing"
print(f"story-map.geojson: OK ({len(features)} features)")
EOF

echo "4) provenance/368817000-berth-stay-2025.json: full claim -> observation -> evidence chain"
"$PYTHON" - "$OUTDIR" <<'EOF'
import json
import sys
from pathlib import Path

outdir = Path(sys.argv[1])
provenance = json.loads(
    (outdir / "provenance" / "368817000-berth-stay-2025.json").read_text()
)
chain = provenance["claim_chain"]
assert len(chain) >= 1, "expected at least one claim in the chain"
claim = chain[0]
assert claim["claim_iri"] == "https://ais.study/claim/368817000-gulf-berth-pattern", claim["claim_iri"]
assert claim["confidence"] == "HighConfidence", claim["confidence"]
observations = claim["observations"]
assert len(observations) >= 1, "expected at least one observation asserting the claim"
evidence = observations[0]["evidence"]
assert len(evidence) >= 1, "expected at least one evidence item on the observation"
assert "s3://ais-noaa/index" in evidence[0]["source"][0], evidence[0]["source"]
print("provenance chain: OK (claim -> observation -> evidence all present)")
EOF

echo "5) layers/shuttle-census.geojson: population sized close to the recorded 820, 17 stopped vessels flagged"
"$PYTHON" - "$OUTDIR" <<'EOF'
import json
import sys
from pathlib import Path

outdir = Path(sys.argv[1])
geojson = json.loads((outdir / "layers" / "shuttle-census.geojson").read_text())
features = geojson["features"]
# Recorded census is 820; the exporter's own recomputation (module docstring
# finding 2) lands close but not byte-identical -- assert it's in a sane
# band around that, not an exact match.
assert 700 <= len(features) <= 950, f"shuttle population out of expected band: {len(features)}"

stopped = [f for f in features if f["properties"]["stopped"]]
assert len(stopped) == 17, f"expected all 17 stopped vessels, found {len(stopped)}"
stopped_mmsis = {f["properties"]["mmsi"] for f in stopped}
assert 244023610 in stopped_mmsis, "THAT'S LIFE (244023610) missing from stopped population"

for feature in features:
    assert feature["geometry"]["type"] == "LineString", feature["geometry"]["type"]
    assert len(feature["geometry"]["coordinates"]) == 2, "expected a 2-pole path"
    assert feature["properties"]["vessel_class"], feature["properties"]

print(f"shuttle-census.geojson: OK ({len(features)} features, 17/17 stopped vessels found)")
EOF

echo "6) provenance/shuttle-244023610.json: method chain + stop classification"
"$PYTHON" - "$OUTDIR" <<'EOF'
import json
import sys
from pathlib import Path

outdir = Path(sys.argv[1])
provenance = json.loads((outdir / "provenance" / "shuttle-244023610.json").read_text())
assert provenance["kind"] == "derived_population_member"
roles = {step["role"] for step in provenance["method_chain"]}
assert "detector" in roles and "shared-mmsi exclusion filter" in roles
assert provenance["stop_classification"]["stop_kind"] == "left_region"
print("shuttle provenance: OK")
EOF

echo "7) bundle serves cleanly over plain HTTP (fetch()-based viewer needs a server, not file://)"
PORT="${OBSERVATORY_SMOKE_HTTP_PORT:-8898}"
# --directory instead of `(cd "$OUTDIR" && ...)`: a `cd &&` subshell makes
# `$!` the wrapper subshell's PID, not http.server's -- killing it later
# leaves the actual server (its child) running and leaking the port.
"$PYTHON" -m http.server "$PORT" --directory "$OUTDIR" >/tmp/observatory-smoke-http.log 2>&1 &
HTTP_PID=$!
cleanup_http() { kill "$HTTP_PID" >/dev/null 2>&1 || true; wait "$HTTP_PID" 2>/dev/null || true; }
trap 'cleanup_http; cleanup' EXIT
for _ in $(seq 1 50); do
  curl -s -o /dev/null "http://127.0.0.1:${PORT}/manifest.json" && break
  sleep 0.1
done
for path in index.html manifest.json layers/story-map.geojson layers/shuttle-census.geojson \
            provenance/368817000-berth-stay-2025.json vendor/leaflet/leaflet.js; do
  code="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PORT}/${path}")"
  [ "$code" = "200" ] || fail "GET /${path} -> ${code}, expected 200"
done
cleanup_http
echo "HTTP serve check: OK"

echo "ALL OBSERVATORY SMOKE CHECKS PASSED"
