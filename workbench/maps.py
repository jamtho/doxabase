"""The map is a second renderer for frame-query results, not a geospatial
subsystem (owner design note, 2026-07-21): any SELECT whose returned
columns happen to carry a recognizable coordinate pair gets a map view
alongside the results table, in any domain -- "set a hollow_frac threshold
and see what it implies; plot a vessel's stops." See doc 13 section 2 item
4 (the L2 map panel) and doc 11's rendering discipline (state exactly
what's shown; the projection never invents structure the query didn't
return).

Two things live here:

- ``build_map_payload``: turn one query's (columns, rows) into the
  JSON-safe structure ``static/map.js`` renders with Leaflet -- points,
  per-column color-by metadata (categorical top-N + "other", or a 5-step
  numeric gradient with visible breakpoints), and path-join eligibility.
- ``example_queries``: 2-3 canned one-click SQL examples for a dataset
  page, built from its described schema so the map affordance is
  discoverable without writing SQL first.
"""
from __future__ import annotations

import datetime
import decimal
import os
from collections import Counter
from typing import Any

# OSM's standard raster tile servers -- see doc's basemap ask. Set
# WORKBENCH_TILES=off to skip live tile requests entirely and render a
# plain grid background instead (offline use, or avoiding an external
# request the analyst didn't expect); the dataset template's own
# attribution line says which mode is active.
OSM_TILE_URL = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
OSM_ATTRIBUTION = (
    '&copy; <a href="https://www.openstreetmap.org/copyright">'
    "OpenStreetMap</a> contributors"
)

ESRI_IMAGERY_TILE_URL = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/"
    "MapServer/tile/{z}/{y}/{x}"
)
ESRI_IMAGERY_ATTRIBUTION = (
    "Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics, "
    "and the GIS User Community"
)


def tiles_enabled() -> bool:
    return os.environ.get("WORKBENCH_TILES", "on").strip().lower() != "off"

# First match wins -- doc-specified accepted coordinate pairs. Matched
# case-insensitively against returned column names so `SELECT LATITUDE,
# LONGITUDE` or an uppercase alias still renders.
COORDINATE_PAIRS: list[tuple[str, str]] = [
    ("latitude", "longitude"),
    ("lat", "lon"),
    ("centroid_lat", "centroid_lon"),
    ("start_lat", "start_lon"),
    ("end_lat", "end_lon"),
]

# Recognizable ordering columns for the "join points as path" affordance
# (round-5 KML lesson: the eye reads joined motion instantly). First match
# wins, same convention as the coordinate pairs.
ORDER_COLUMNS = ["base_date_time", "start_ts", "ts", "timestamp"]

# Columns that identify "one thing" across rows -- generic `identity` for
# non-AIS domains, `mmsi` for this one. A path is only offered when a
# result is already scoped to a single identity value: joining points from
# several different vessels/entities into one line would draw a fiction.
IDENTITY_COLUMNS = ["mmsi", "identity"]

# Categorical legend cap (doc ask: "up to ~10, then other").
MAX_CATEGORIES = 10


def detect_coordinate_pair(columns: list[str]) -> tuple[str, str] | None:
    """First accepted (lat_col, lon_col) name pair present in `columns`,
    preserving the caller's original casing; None if no pair matches."""
    lowered = {c.lower(): c for c in columns}
    for lat_name, lon_name in COORDINATE_PAIRS:
        if lat_name in lowered and lon_name in lowered:
            return lowered[lat_name], lowered[lon_name]
    return None


def _detect_first(columns: list[str], candidates: list[str]) -> str | None:
    lowered = {c.lower(): c for c in columns}
    for name in candidates:
        if name in lowered:
            return lowered[name]
    return None


def _jsonable(value: Any) -> Any:
    """Mirror the results table's own display convention (Jinja's default
    str() of whatever DuckDB's fetchall() hands back) but as JSON-safe
    types, so a popup shows the same values the table row would."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    return str(value)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float, decimal.Decimal)) and not isinstance(value, bool)


def _color_column_meta(name: str, values: list[Any]) -> dict:
    """Color-by metadata for one non-coordinate column: a numeric 5-step
    gradient (equal-interval breakpoints, visible in the legend) or a
    categorical palette slot list ranked by frequency, capped at
    MAX_CATEGORIES with the rest folded into "other"."""
    non_null = [v for v in values if v is not None]
    if non_null and all(_is_number(v) for v in non_null):
        nums = [float(v) for v in non_null]
        lo, hi = min(nums), max(nums)
        step = (hi - lo) / 5 if hi > lo else 0.0
        breaks = [lo + i * step for i in range(6)] if step else [lo] * 6
        return {"name": name, "kind": "numeric", "min": lo, "max": hi, "breaks": breaks}
    counts = Counter(str(v) for v in non_null)
    ranked = [value for value, _ in counts.most_common()]
    return {
        "name": name,
        "kind": "categorical",
        "categories": ranked[:MAX_CATEGORIES],
        "total_categories": len(ranked),
        "has_other": len(ranked) > MAX_CATEGORIES,
    }


def _pick_default_color(
    color_columns: list[dict], order_col: str | None, constant_identity_col: str | None
) -> str | None:
    """Auto-select a color-by column so a query that already computes a
    classification (the owner's hollow_frac/CASE example) renders classed
    colors with zero dropdown interaction. Prefers, in order: a "true"
    classification (categorical, more than one distinct value, no
    overflow into "other"); else a numeric column (a gradient is
    informative even when we can't tell in advance whether it varies);
    else the first remaining column, so something is always chosen
    rather than defaulting to a constant-valued or id-like column just
    because it happens to come first in the SELECT list. Excluded
    throughout: the ordering column (raw timestamps make a poor legend)
    and an identity column that turned out constant across every
    returned row (e.g. a single-vessel query's own mmsi column) -- both
    still selectable by hand from the dropdown, just not auto-picked."""
    candidates = [
        c for c in color_columns if c["name"] not in (order_col, constant_identity_col)
    ]
    for c in candidates:
        if c["kind"] == "categorical" and 1 < c["total_categories"] <= MAX_CATEGORIES:
            return c["name"]
    for c in candidates:
        if c["kind"] == "numeric":
            return c["name"]
    return candidates[0]["name"] if candidates else None


def build_map_payload(columns: list[str], rows: list[tuple]) -> dict | None:
    """None if `columns` carries no recognizable coordinate pair. Else a
    JSON-safe dict for static/map.js: points (lat/lon + every other
    column, popup-ready), color-by metadata per non-coordinate column, a
    default color-by choice, and whether "join as path" applies."""
    pair = detect_coordinate_pair(columns)
    if pair is None:
        return None
    lat_col, lon_col = pair
    order_col = _detect_first(columns, ORDER_COLUMNS)
    identity_col = _detect_first(columns, IDENTITY_COLUMNS)
    other_cols = [c for c in columns if c not in (lat_col, lon_col)]
    idx = {c: i for i, c in enumerate(columns)}

    points: list[dict] = []
    identity_values: set[Any] = set()
    raw_by_column: dict[str, list[Any]] = {c: [] for c in other_cols}
    for row in rows:
        lat, lon = row[idx[lat_col]], row[idx[lon_col]]
        if lat is None or lon is None:
            continue
        points.append({
            "lat": float(lat),
            "lon": float(lon),
            "fields": {c: _jsonable(row[idx[c]]) for c in other_cols},
        })
        if identity_col:
            identity_values.add(row[idx[identity_col]])
        for c in other_cols:
            raw_by_column[c].append(row[idx[c]])

    color_columns = [
        _color_column_meta(c, raw_by_column[c])
        for c in other_cols
        if any(v is not None for v in raw_by_column[c])
    ]

    identity_constant = len(identity_values) == 1
    path_available = bool(order_col and identity_col and identity_constant and len(points) > 1)

    return {
        "lat_col": lat_col,
        "lon_col": lon_col,
        "order_col": order_col,
        "identity_col": identity_col,
        "path_available": path_available,
        "color_columns": color_columns,
        "default_color": _pick_default_color(
            color_columns, order_col, identity_col if identity_constant else None
        ),
        "point_count": len(points),
        "points": points,
    }


# ---------------------------------------------------------------------
# Canned example queries (doc ask, item 3): 2-3 one-click SQL examples on
# any dataset page whose described frame schema has a recognizable
# coordinate pair, so the map affordance is discoverable before anyone
# writes SQL. {mmsi} is a template placeholder the dataset page's own
# small JS fills from an adjacent input before running the query --
# nothing server-side parameterizes it.

_STOPS_SERIES_MMSI_DEFAULT = 338617000  # PENNSYLVANIA -- the story_kml.py demo vessel


def _stops_series_examples(lat_col: str, lon_col: str) -> list[dict]:
    return [
        {
            "label": "One vessel's stops, classed by hollow_frac",
            "sql": (
                f"SELECT {lat_col}, {lon_col}, start_ts, mmsi, hollow_frac,\n"
                "  CASE WHEN hollow_frac > 0.85 THEN 'tight'\n"
                "       WHEN hollow_frac < 0.7 THEN 'hollow'\n"
                "       ELSE 'mid' END AS class\n"
                "FROM frame WHERE mmsi = {mmsi}\n"
                "ORDER BY start_ts LIMIT 500"
            ),
            "param": "mmsi",
            "param_default": _STOPS_SERIES_MMSI_DEFAULT,
        },
        {
            "label": "All multi-day stops in a bounding box",
            "sql": (
                f"SELECT {lat_col}, {lon_col}, duration_bucket, hollow_frac, mmsi\n"
                "FROM frame\n"
                "WHERE duration_bucket = 'multi-day'\n"
                f"  AND {lat_col} BETWEEN 25 AND 45\n"
                f"  AND {lon_col} BETWEEN -95 AND -70\n"
                "ORDER BY duration_s DESC LIMIT 500"
            ),
        },
        {
            "label": "Stop density sample",
            "sql": (
                f"SELECT {lat_col}, {lon_col}, duration_bucket\n"
                "FROM frame\nUSING SAMPLE 500 ROWS"
            ),
        },
    ]


def _generic_examples(lat_col: str, lon_col: str, columns: list[str]) -> list[dict]:
    """Fallback for any other dataset whose schema has a coordinate pair:
    a plain sample, plus a per-identity track when the schema also has an
    identity + ordering column (the general form of the stops-series
    "one vessel" example)."""
    examples = [
        {
            "label": "Sample of points",
            "sql": f"SELECT {lat_col}, {lon_col}\nFROM frame\nUSING SAMPLE 200 ROWS",
        }
    ]
    order_col = _detect_first(columns, ORDER_COLUMNS)
    identity_col = _detect_first(columns, IDENTITY_COLUMNS)
    if order_col and identity_col:
        # identity_col is in the SELECT list, not just the WHERE clause --
        # the path-join checkbox only appears when the result's own
        # columns carry a single-valued identity column (build_map_payload
        # checks the returned rows, not the query text).
        examples.insert(0, {
            "label": f"One {identity_col}'s track",
            "sql": (
                f"SELECT {lat_col}, {lon_col}, {order_col}, {identity_col}\n"
                f"FROM frame WHERE {identity_col} = {{{identity_col}}}\n"
                f"ORDER BY {order_col} LIMIT 500"
            ),
            "param": identity_col,
            "param_default": _STOPS_SERIES_MMSI_DEFAULT if identity_col == "mmsi" else "",
        })
    return examples


def example_queries(dataset_iri: str, columns: list[str]) -> list[dict]:
    """2-3 canned queries for a dataset page, or [] if its schema has no
    recognizable coordinate pair. Each entry: label, sql (may contain one
    `{param}` placeholder), and if so `param`/`param_default`."""
    pair = detect_coordinate_pair(columns)
    if pair is None:
        return []
    lat_col, lon_col = pair
    if dataset_iri == "https://ais.study/dataset/stops-series-full":
        return _stops_series_examples(lat_col, lon_col)
    return _generic_examples(lat_col, lon_col, columns)
