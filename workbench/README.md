# DoxaBase Capsule Workbench

A local-first, read-only web UI over one DoxaBase capsule: project brief,
resource pages, search, a datasets overview, and per-dataset pages with a
capped SQL query box over the frames the capsule describes.

**Status (2026-07-20): lives in this repo now**, at the owner's direction
("humans can't really interface with the capsules without it") — it
started as a separate repo (`jamtho/doxabase-workbench`) while the wheel
API it depends on was still moving; that repo's `README.md` now just
points here. It stays a sibling top-level `workbench/` package, not part
of the `doxabase/` package the distillation-program scoreboard measures
(`tools/scoreboard.py` only walks `doxabase/`), and its runtime
dependencies (fastapi, uvicorn, duckdb, jinja2, ...) are an optional
extra so the core install stays lean.

This is the **first implementation cut** of
[design doc 13](../doxabase_design_docs/13-capsule-workbench.md) ("The
Capsule Workbench"), scoped to doc 13 §5's first cut: L1 (a thin FastAPI
facade over the installed `doxabase` wheel's read calls, plus one DuckDB
frame-query endpoint) and the generic resource/search/dataset views from
L2. Doc 11 ("The Capsule Observatory") is its static, public-facing
sibling — not built here.

## What this is not (yet)

Honest status against doc 13 §2's L2 list — built vs. not:

- Built: resource pages (types/literals/links, claim+evidence+caveat one-hop
  inline expansion), search, the project brief as landing page, the frame
  query box (one dataset at a time, SELECT-only, capped at 500 rows), and
  `list_entities`/`validate_graph` wrapped at L1 (`/api/entities` JSON, a
  conforms/issue-count line on the landing page, and `list_entities` itself
  now has an HTML page via `/types/entities`, see below).
- Built (doc 13 §5 session outcome, "direct eyes on the living capsule"):
  the version-flow view — a `/revisions` timeline (newest first, paginated,
  wrapping `list_graph_revisions`) with each row linking to
  `/revisions/<iri>` (`describe_graph_revision`, full lineage/validation/
  graph-snapshot/revision-anchor detail); a **History** section on every
  resource page (`list_resource_revisions`: revision-anchor links plus a
  scan of stored patch payloads mentioning the resource, oldest first); and
  a claim-reconsideration supersession chain (old claim &rarr; superseding
  claim, dated) rendered inline in the existing Claim section. Per-resource
  history is real but partial by construction — see the caveat printed on
  every History section for exactly what it can and cannot find.
- Built (doc 14 §4.4, decided into v1): an **Anchored derivation** panel on
  any resource page carrying `aisv:` provenance properties
  (`derivedFromRun`/`representsDetectorRows`/`assessedAt`/
  `assessmentDataWindow`), with an explicitly-labelled "match-back status:
  not yet computed" placeholder (the match-back method doesn't exist yet).
- Built (maintainer ask, "another route in" alongside /revisions): a
  `/types` overview -- every `rdf:type` present in every named graph, in
  the capsule's own role order (map, ontology, observations, patterns,
  evidence, shapes, history, base_ontology, base_shapes), with instance
  counts and each graph's total entity count in its header; types are
  shown in full (no cutoff for huge or singleton types), sorted by count.
  Type labels are resolved via a batched `rdfs:label` lookup where the
  ontology has them, falling back to the same compacted-IRI display the
  rest of the app already uses. Each type links to
  `/types/entities?graph=&type=` -- `list_entities(type=, graph=)` reused
  as-is, paginated. The landing page gets a compact "what's in this
  capsule" per-graph entity-count strip linking into `/types`, without
  displacing the project brief as the lead. This is a direct SQL rollup
  over the capsule's `quads` table (`workbench/graph_types.py`), not a
  wheel-wrapped call -- the wheel has no dedicated graph/type rollup, and
  doc 13 is explicit that a single GROUP BY here is fine and fast.
- Built (owner ask, 2026-07-20 — "row counts making datasets tractable is
  the point"): a `/datasets` overview -- every described `rc:Table`/
  `rc:Dataset` entity in one table, led with its recorded row-count
  snapshot (never a live frame `COUNT(*)` paid for on page load), plus
  kind, column/caveat counts, storage kind (S3/local/logical) with a
  reachability badge, and a referenced-by count (distinct `map`/
  `observations` entities citing the dataset or one of its columns, a
  direct `quads` query cached per process — see `workbench/dataset_index.py`).
  Linked from the nav and from the landing page's own dataset table.
- **Not built**: the frame browser's saved/recorded views and export; the
  map panel (MapLibre, KML/KMZ export, geo layers); method pages (recorded
  methods as contracts, with evidenced-parameter plots inline); the caveat
  catalog as its own cross-dataset view; queue *review* (queue *viewing*
  exists via the landing page only); a live match-back status computation
  (doc 14's match-back method itself is unbuilt); L3 domain configuration
  (vessel-page templates, saved views, layer styling); the observatory
  static-build target from doc 11; auth (doc 13 open question 1 — don't
  expose this beyond localhost, use an observatory build instead).

## Run it

Runtime deps are an optional extra so a plain `doxabase` install stays
lean:

```bash
pip install "doxabase[workbench]"
# or, from a checkout:
uv sync --extra workbench
```

Then point it at a capsule (opened `mode=ro`; the workbench never writes to
it) and start the server:

```bash
doxabase-workbench /home/codex/ais-study/capsule.sqlite
# -> http://127.0.0.1:8000
```

Or run uvicorn directly:

```bash
WORKBENCH_CAPSULE_PATH=/home/codex/ais-study/capsule.sqlite \
    uvicorn workbench.app:app --port 8000
```

`doxabase-workbench` is always registered by the core wheel (pip entry
points can't be conditioned on an extra), but `workbench/cli.py` guards
its own `fastapi`/`uvicorn` imports — running it without the `workbench`
extra installed fails with one clear line, not a raw traceback.

The frame query box on a dataset page only appears if the dataset has a
reachable physical layout — S3-backed (a cheap `glob()` probe at render
time against `MINIO_ENDPOINT`/`MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY`,
mirroring the AIS study's own `query.py` convention) or a local frame
under `WORKBENCH_DATA_ROOT` (default: the capsule's own directory; see
`workbench/frames.py`). The workbench never records or displays
credential values.

## Smoke test

```bash
tools/workbench_smoke.sh [capsule-path]
```

(Not part of `tools/gate.sh` — it needs the optional extra installed and
a real capsule file, neither of which the core gate's clean-venv smoke
should pay for. Point `WORKBENCH_SMOKE_PYTHON` at a venv with
`doxabase[workbench]` installed if the repo's own `.venv` doesn't have
it; `SMOKE_PORT` overrides the default port.)

Starts the server against a capsule (default: the AIS study capsule) and
curls: the landing page; a search results page and a resource page (IRI
discovered via search); the dataset page; `/datasets` (row counts, storage
reachability, reference counts); the `/revisions` list and a
`/revisions/<iri>` detail page (IRI discovered via `list_graph_revisions`);
the `/types` overview and a `/types/entities` drilldown (graph + type IRI
discovered live via the same `graph_types.type_overview` GROUP BY the page
itself runs); and a resource page whose History section is non-empty (IRI
discovered via a revision's `revision_anchors`) — asserting HTTP 200 +
expected substrings on each.

## Layout

```
workbench/
  capsule.py       L1: open the capsule read-only (one connection per request)
  frames.py        the one DuckDB frame-query endpoint: glob + SELECT-only guard + 500-row cap
  graph_types.py   the /types rollup: direct SQL over quads, no wheel call wraps this
  dataset_index.py the /datasets rollup: row-count/storage/reachability/referenced-by per dataset
  app.py           FastAPI routes (the facade) + Jinja rendering glue
  cli.py           `doxabase-workbench capsule.sqlite` entry point (extras-guarded)
  templates/       server-rendered HTML, no JS framework
    datasets.html       /datasets -- every described dataset, row counts led first
    revisions.html      /revisions -- the history-graph timeline, newest first
    revision.html       /revisions/<iri> -- one revision's full description
    types.html          /types -- rdf:type instances and counts, one section per graph
    type_entities.html  /types/entities -- list_entities(type=, graph=) reused, paginated
    resource.html       (extended) History section, supersession chain, anchored-derivation panel
  static/          one plain CSS file
tools/workbench_smoke.sh
```

## What's next (per doc 13 §5's own ordering)

Resource pages + search first (done here, they exercise L1 completely);
frame browser next — this cut has one query box per dataset page but not
the saved/recorded-view affordance or export; then the map panel by porting
`story_kml.py`'s DuckDB queries to GeoJSON for a MapLibre layer, per doc 11.
