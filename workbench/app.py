"""L1 facade: FastAPI routes over the installed doxabase wheel's read calls,
plus the one DuckDB frame-query endpoint (doc 13 §5's first cut).

Every route opens its own capsule connection, calls exactly one doxabase
read method, converts the result with `to_dict`/`to_jsonable`, and hands a
plain dict to a Jinja template. No route writes to the capsule. Kept close
to the doc's ~200 line target for the facade; templates carry the
presentation.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from doxabase import DoxaBaseError, to_dict

from . import dataset_index, frames, graph_types, maps
from .capsule import capsule_path, open_capsule

_APP_DIR = Path(__file__).parent

# project_brief() walks queues/gates/dataset status and measured ~2s against
# the AIS capsule -- fine once, not on every landing-page hit. Doc 13's
# <100ms floor is scoped to resource pages; for this one expensive call we
# cache with a short TTL so the landing page stays fast within a browsing
# session but still notices capsule writes an agent made a few seconds ago
# (this is the human-checks-after-agent-writes loop the workbench is for).
_BRIEF_CACHE_TTL_SECONDS = 20
_brief_cache: dict[str, tuple[float, dict, dict]] = {}


def _cached_landing_data(capsule_key: str) -> tuple[dict, dict]:
    cached = _brief_cache.get(capsule_key)
    if cached is not None and time.monotonic() - cached[0] < _BRIEF_CACHE_TTL_SECONDS:
        return cached[1], cached[2]
    with open_capsule() as db:
        brief = to_dict(db.project_brief(limit=10))
        validation = to_dict(db.validate_graph("map", limit_results=1))
    _brief_cache[capsule_key] = (time.monotonic(), brief, validation)
    return brief, validation

app = FastAPI(title="DoxaBase Capsule Workbench")
app.mount("/static", StaticFiles(directory=str(_APP_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(_APP_DIR / "templates"))
templates.env.globals["resource_url"] = lambda iri: f"/resource?iri={quote(iri, safe='')}"
templates.env.globals["dataset_url"] = lambda iri: f"/dataset?iri={quote(iri, safe='')}"
# A path segment, not a query param (task ask: "/revisions/<iri>"), so the
# IRI's own '/' and ':' stay unescaped -- Starlette hands routes the
# ASGI-decoded path, so a fully quote(safe='')-escaped IRI would arrive
# already un-escaped back into literal slashes and fail to match a single
# {iri} segment. Escaping only the characters that would otherwise be
# mis-parsed as path/query/fragment separators (?, #, %, space, ...) keeps
# the round trip lossless with a {iri:path} route.
templates.env.globals["revision_url"] = lambda iri: f"/revisions/{quote(iri, safe='/:')}"
# Single source of truth for the OSM tile URL/attribution -- both the
# human-readable line under the map and map.js's Leaflet attribution
# control read the same constants (workbench/maps.py) rather than each
# hardcoding their own copy.
templates.env.globals["osm_tile_url"] = maps.OSM_TILE_URL
templates.env.globals["osm_attribution"] = maps.OSM_ATTRIBUTION


def _type_entities_url(graph: str, type_iri: str, offset: int = 0) -> str:
    url = (
        f"/types/entities?graph={quote(graph, safe='')}"
        f"&type={quote(type_iri, safe='')}"
    )
    if offset:
        url += f"&offset={offset}"
    return url


templates.env.globals["type_entities_url"] = _type_entities_url
# /datasets leads with row counts (owner ask) -- large recorded snapshots
# (M12's full run is 30M+ rows) need thousands separators to read at a glance.
templates.env.filters["thousands"] = (
    lambda n: f"{n:,}" if isinstance(n, int) else n
)


def _tojson(value) -> str:
    """The map payload embedded as `<script type="application/json">`
    text -- Jinja has no built-in `tojson` (that's a Flask addition), and
    the escaping matters: a row value containing a literal "</script>"
    must not close the tag early."""
    return (
        json.dumps(value)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


templates.env.filters["tojson"] = _tojson

# record_kind is the wheel's internal vocabulary for a history-graph row;
# the maintainer asked for the plainer staged/applied/resolution framing
# (doc 13 §5 session outcome) on the version-flow views.
_REVISION_KIND_LABELS = {
    "staged_patch": "staged",
    "applied_event": "applied",
    "staged_review_resolution": "resolution",
    "export_record": "export",
    "import_record": "import",
    "history_record": "history",
}
templates.env.globals["revision_kind_label"] = (
    lambda kind: _REVISION_KIND_LABELS.get(kind, kind)
)

# Resource types worth showing one hop inline rather than requiring a
# click-through -- doc 13 L2.1's "claim chains expanded inline", extended
# to evidence and caveats (data never appears without its semantics).
# Triples' own object_types/subject_types are graph-scoped (populated only
# from the triple's own named graph) and miss cross-graph links -- claims
# and evidence commonly live in a different graph than what cites them --
# so we check the real type via a cheap one-hop describe_resource() instead
# of trusting that field. Measured ~1ms/call against the AIS capsule, so a
# capped number of attempts stays well inside the doc's <100ms floor.
_INLINE_TYPES = {
    "https://richcanopy.org/ns/rc#Claim",
    "https://richcanopy.org/ns/rc#Evidence",
    "https://richcanopy.org/ns/rc#KnownCaveat",
}
_INLINE_EXPANSION_CAP = 12
_INLINE_ATTEMPT_CAP = 40

# Doc 14 §4.4's anchored-derivation panel: the wheel has no dedicated call
# for these -- they are project-vocabulary (aisv:) properties, not shared
# rc: terms, so this is a plain scan of a resource's already-fetched
# outgoing triples for four full predicate IRIs. Literal-valued in every
# example seen in the AIS capsule; rendered as text either way.
_ANCHORED_DERIVATION_PREDICATES = {
    "https://ais.study/ns#derivedFromRun": "derived_from_run",
    "https://ais.study/ns#representsDetectorRows": "represents_detector_rows",
    "https://ais.study/ns#assessedAt": "assessed_at",
    "https://ais.study/ns#assessmentDataWindow": "assessment_data_window",
}


def _anchored_derivation(outgoing: list[dict]) -> dict[str, list[dict]] | None:
    fields: dict[str, list[dict]] = {}
    for triple in outgoing:
        key = _ANCHORED_DERIVATION_PREDICATES.get(triple.get("predicate"))
        if key is None:
            continue
        fields.setdefault(key, []).append(
            {"value": triple.get("object"), "kind": triple.get("object_kind")}
        )
    return fields or None


def _render(request: Request, template: str, **context) -> HTMLResponse:
    return templates.TemplateResponse(request, template, context)


def _expand_inline(db, triples: list[dict], iri_key: str, kind_key: str,
                    expansions: dict[str, dict], attempts: list[int]) -> None:
    """Fetch a compact one-hop description for claim/evidence/caveat
    link targets so the resource page can render them inline."""
    for triple in triples:
        if len(expansions) >= _INLINE_EXPANSION_CAP or attempts[0] >= _INLINE_ATTEMPT_CAP:
            return
        target = triple.get(iri_key)
        if not target or triple.get(kind_key) != "uri" or target in expansions:
            continue
        attempts[0] += 1
        try:
            described = to_dict(
                db.describe_resource(target, include_incoming=False, limit=20)
            )
        except DoxaBaseError:
            continue
        if _INLINE_TYPES & set(described.get("types", [])):
            expansions[target] = described


@app.exception_handler(DoxaBaseError)
def _doxabase_error(request: Request, exc: DoxaBaseError) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "error.html", {"message": str(exc)}, status_code=404,
    )


@app.get("/", response_class=HTMLResponse)
def landing(request: Request) -> HTMLResponse:
    brief, validation = _cached_landing_data(str(capsule_path()))
    graph_totals = graph_types.graph_entity_totals(capsule_path())
    return _render(
        request, "landing.html", brief=brief, validation=validation,
        graph_totals=graph_totals,
    )


@app.get("/datasets", response_class=HTMLResponse)
def datasets_overview(request: Request) -> HTMLResponse:
    """Every described dataset in one table, row counts led first (owner
    ask, 2026-07-20: "row counts making datasets tractable is the point").
    Linked from the nav and from the project-brief landing page's own
    dataset table."""
    with open_capsule() as db:
        rows = dataset_index.dataset_overview(capsule_path(), db)
    return _render(request, "datasets.html", rows=rows)


@app.get("/search", response_class=HTMLResponse)
def search(request: Request, q: str = "", graph: str | None = None,
           offset: int = 0) -> HTMLResponse:
    results = None
    if q.strip():
        with open_capsule() as db:
            results = to_dict(db.search(q, graph=graph, limit=25, offset=offset))
    return _render(request, "search.html", query=q, graph=graph, results=results)


@app.get("/api/entities")
def api_entities(type: str | None = None, graph: str | None = "map",
                  text: str | None = None, limit: int = 25,
                  offset: int = 0) -> JSONResponse:
    """Thin JSON wrapper over list_entities -- no HTML browser built on top
    of it yet (README's honest-status list), but it is part of L1."""
    with open_capsule() as db:
        entities = to_dict(db.list_entities(
            type=type, graph=graph, text=text, limit=limit, offset=offset,
        ))
    return JSONResponse(entities)


@app.get("/types", response_class=HTMLResponse)
def types_overview(request: Request) -> HTMLResponse:
    """Landing page for the graph, a bit like /revisions: every rdf:type
    present in every graph, with instance counts, sorted by count within
    the graph -- doc 13's L2 entity listing had no page of its own yet;
    this is the overview that leads into it."""
    overview = graph_types.type_overview(capsule_path())
    return _render(request, "types.html", overview=overview)


_TYPE_ENTITIES_LIMIT = 25


@app.get("/types/entities", response_class=HTMLResponse)
def type_entities(request: Request, graph: str, type: str,
                   offset: int = 0) -> HTMLResponse:
    """Instances of one rdf:type in one graph -- list_entities(type=,
    graph=) reused as-is. `type` must already be a full IRI (the /types
    page hands the exact quads.object value straight through); list_entities
    raises on an unregistered-prefix CURIE rather than silently matching
    nothing, so there is nothing to expand here."""
    with open_capsule() as db:
        entities = to_dict(
            db.list_entities(
                type=type, graph=graph, limit=_TYPE_ENTITIES_LIMIT, offset=offset,
            )
        )
    type_label = graph_types.label_for_type(capsule_path(), type)
    return _render(
        request, "type_entities.html", entities=entities, graph=graph,
        type_iri=type, type_label=type_label,
    )


_RESOURCE_HISTORY_LIMIT = 25


@app.get("/resource", response_class=HTMLResponse)
def resource(request: Request, iri: str) -> HTMLResponse:
    with open_capsule() as db:
        ctx = to_dict(db.describe_resource(iri, limit=200))
        inline: dict[str, dict] = {}
        attempts = [0]
        _expand_inline(db, ctx.get("outgoing", []), "object", "object_kind", inline, attempts)
        _expand_inline(db, ctx.get("incoming", []), "subject", "subject_kind", inline, attempts)
        # list_resource_revisions is the "cheapest honest query" doc 13 §5
        # asks for: it matches this resource against history-graph rows via
        # rc:revisionAnchor plus a scan of stored patch payloads (subject/
        # predicate/object), including the staged source behind an applied
        # event. include_apply_checks=False skips the (here ~50ms extra)
        # apply-check recomputation, which the history section doesn't need.
        # Measured ~90ms against the AIS capsule's 18-revision history graph
        # -- above doc 13's <100ms resource-page floor on its own, so this
        # section is the one part of the page allowed to push past it.
        history = to_dict(
            db.list_resource_revisions(
                iri,
                include_patch_mentions=True,
                include_apply_checks=False,
                limit=_RESOURCE_HISTORY_LIMIT,
            )
        )
    found = bool(ctx.get("types") or ctx.get("outgoing") or ctx.get("incoming"))
    derivation = _anchored_derivation(ctx.get("outgoing", []))
    return _render(request, "resource.html", resource=ctx, iri=iri,
                   inline=inline, found=found, history=history,
                   derivation=derivation)


_REVISIONS_LIST_LIMIT = 20


@app.get("/revisions", response_class=HTMLResponse)
def revisions(request: Request, offset: int = 0, limit: int = _REVISIONS_LIST_LIMIT) -> HTMLResponse:
    with open_capsule() as db:
        listing = to_dict(db.list_graph_revisions(limit=limit, offset=offset))
    return _render(request, "revisions.html", listing=listing)


@app.get("/revisions/{iri:path}", response_class=HTMLResponse)
def revision_detail(request: Request, iri: str) -> HTMLResponse:
    with open_capsule() as db:
        rev = to_dict(db.describe_graph_revision(iri))
    return _render(request, "revision.html", revision=rev, iri=iri)


def _schema_columns(ds: dict) -> list[str]:
    return [c["column_name"] for c in ds.get("columns", []) if c.get("column_name")]


@app.get("/dataset", response_class=HTMLResponse)
def dataset(request: Request, iri: str) -> HTMLResponse:
    with open_capsule() as db:
        ds = to_dict(db.describe_dataset(iri))
    glob = frames.frame_glob(ds.get("path_templates", []))
    reachable = bool(glob) and frames.is_reachable(glob)
    # Canned example queries (doc ask, item 3) only make sense once we
    # know the frame is actually queryable -- same condition the query
    # box itself uses to decide whether to render at all.
    examples = maps.example_queries(iri, _schema_columns(ds)) if reachable else []
    return _render(
        request, "dataset.html", dataset=ds, iri=iri, glob=glob,
        reachable=reachable, sql=None, columns=None, rows=None, query_error=None,
        examples=examples, map_payload=None, tiles_enabled=maps.tiles_enabled(),
    )


@app.post("/dataset/query", response_class=HTMLResponse)
def dataset_query(request: Request, iri: str = Form(...),
                   sql: str = Form(...)) -> HTMLResponse:
    with open_capsule() as db:
        ds = to_dict(db.describe_dataset(iri))
    glob = frames.frame_glob(ds.get("path_templates", []))
    reachable = bool(glob) and frames.is_reachable(glob)
    columns = rows = None
    query_error = None
    map_payload = None
    if not reachable:
        query_error = "This dataset's storage is not reachable right now."
    else:
        try:
            columns, rows = frames.run_query(glob, sql)
            # The map is a second renderer for this same result set (owner
            # design note) -- not a separate query, not a separate cap.
            # None when the returned columns carry no recognizable
            # coordinate pair; the template falls back to table-only.
            map_payload = maps.build_map_payload(columns, rows)
        except frames.FrameQueryError as exc:
            query_error = str(exc)
    examples = maps.example_queries(iri, _schema_columns(ds)) if reachable else []
    return _render(
        request, "dataset.html", dataset=ds, iri=iri, glob=glob,
        reachable=reachable, sql=sql, columns=columns, rows=rows,
        query_error=query_error, examples=examples, map_payload=map_payload,
        tiles_enabled=maps.tiles_enabled(),
    )
