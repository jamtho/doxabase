"""``doxabase-observatory export <capsule> <outdir>`` -- doc 11's exporter,
the observatory's first deliverable per doc 11 section 7: "layers 1-2 from
the real AIS capsule, viewed locally in MapLibre [here: vendored Leaflet,
matching the workbench's own choice -- doc 13's 2026-07-21 status note],
before ANY hosting decisions." Console script guarded the same way
``workbench/cli.py`` guards ``doxabase-workbench``: always registered by
the core wheel, but its runtime dependency (duckdb, for the frame-derived
Layer 2 population) is the optional ``workbench`` extra.

Doc 13 section 2.4: "the observatory (doc 11) = a build that snapshots L2
views through the export-eligibility gate into static artifacts." This
module is that build. It is intentionally NOT a live server -- no
FastAPI, no request loop -- just a function that reads a capsule (+ the S3
frames it describes) once and writes a self-contained static bundle.

Bundle layout (doc 11 section 2's architecture diagram):
    manifest.json        layer registry, data window, generation provenance,
                          export-eligibility stamp
    layers/*.geojson      Layer 1 "story map", Layer 2 "shuttle census"
    provenance/*.json     per-feature claim/evidence chains, keyed by feature id
    index.html            the static viewer (workbench/observatory/index.html,
                           copied verbatim)
    observatory.js         viewer wiring (copied verbatim)
    observatory.css         viewer styling (copied verbatim)
    vendor/leaflet/        vendored Leaflet, copied from
                           workbench/static/vendor/leaflet (already in-repo
                           for the workbench's own map panel -- doc 13
                           section 2.4's "shared lower layers")

Two genuine data-model findings surfaced while building this (recorded here
per doc 11 section 3 -- "flow to the distiller ledger like any other
case-study finding"):

1. The capsule has no structured geo predicate. The promoted story
   resources (aisv:SilencePeriod/DwellPeriod/IdentityChange/
   DraftChangeEvent) carry coordinates only inside a free-text
   ``aisv:place`` literal ("30.68N -88.03W, Gulf of Mexico ..."), whose own
   predicate_label is candidly "place (position-inferred)". Round-4's
   directive was "natural language as display notes only, never the
   primary output" -- but for Layer 1 geometry, the note IS the only
   source. This exporter parses coordinates out of that literal with a
   regex (``COORD_PATTERN`` below); a future capsule that wants
   machine-checkable geometry would need a real ``geo:lat``/``geo:long``
   (or WKT) predicate on these event resources. There is also no cheap way
   to enumerate "all geo-typed resources with their claim chains" as a
   wheel call (doc 11 section 3's example gap, confirmed): this module
   finds them by a direct SQL scan for subjects carrying ``aisv:place``,
   the same "no wheel call wraps this, one SQL is fine" idiom
   ``workbench/graph_types.py`` already established.
2. M9's pattern text (the "two-point shuttle detector") records its
   layer-1 SQL verbatim but describes layer-2 (pole ranking, switch
   counting, thresholding) only in prose. This exporter re-implements
   layer 2 from that prose against the same described ``daily-index``
   dataset; spot checks against the pattern's own worked examples match
   exactly (SULPHUR ENTERPRISE 0.529 concentration, QUEEN OF SURREY 0.809
   concentration / 4 switches, the M2 multi_emitter exclusion at exactly
   12 MMSI) but the final population count lands a few percent above the
   capsule's recorded 820 (see ``build_shuttle_layer``'s docstring) --
   because the graph never recorded byte-exact tie-breaking for MMSIs with
   equal-dwell-day bins, only the definitions. Documented in the manifest,
   not silently rounded away.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any

from doxabase import DoxaBase, to_dict

_MODULE_DIR = Path(__file__).parent
_ASSETS_DIR = _MODULE_DIR / "observatory"
_VENDOR_LEAFLET_SRC = _MODULE_DIR / "static" / "vendor" / "leaflet"

RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
RDFS_COMMENT = "http://www.w3.org/2000/01/rdf-schema#comment"
RDFS_SEE_ALSO = "http://www.w3.org/2000/01/rdf-schema#seeAlso"
NS = "https://ais.study/ns#"
RC = "https://richcanopy.org/ns/rc#"
PLACE_PREDICATE = NS + "place"
HAS_CLAIM = RC + "hasClaim"
EVIDENCE_PRED = RC + "evidence"

# The promoted "story" resource types (doc 11 section 4, Layer 1): every
# instance of one of these that carries aisv:place is a candidate feature.
STORY_TYPES = {
    NS + "SilencePeriod",
    NS + "DwellPeriod",
    NS + "IdentityChange",
    NS + "DraftChangeEvent",
}

# "30.68N -88.03W", "16.13N -66.18W", etc. -- the numeric value already
# carries the correct sign for its hemisphere in this capsule's usage (a
# western longitude reads "-88.03W"), so only the number is used; N/S/E/W
# are read positionally to anchor the match, not to re-sign anything.
COORD_PATTERN = re.compile(r"(-?\d{1,3}\.\d+)\s*([NS])\s*,?\s+(-?\d{1,3}\.\d+)\s*([EW])")


def parse_coordinates(text: str | None) -> list[tuple[float, float]]:
    """Every (lat, lon) pair findable in a free-text aisv:place literal, in
    the order they appear (exit before return, etc. -- see module
    docstring finding 1)."""
    if not text:
        return []
    return [(float(lat), float(lon)) for lat, _, lon, _ in COORD_PATTERN.findall(text)]


def _local_name(iri: str) -> str:
    return iri.split("#")[-1].split("/")[-1]


def _connect_capsule(path: Path) -> sqlite3.Connection:
    """Read-only direct SQL over the capsule's own quads table -- the same
    mode=ro URI convention and "no wheel call wraps this" idiom
    ``workbench/graph_types.py``/``workbench/dataset_index.py`` already
    use, not a private DoxaBase._conn reach-in."""
    uri = f"{Path(path).resolve().as_uri()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _group_predicates(rows: list[sqlite3.Row]) -> dict[str, list[str]]:
    """{local predicate name: [object values in insertion order]} -- the
    generic shape both the story-feature builder and the claim-chain
    walker below use; doc 11 section 1's "RDF structure is the primary
    input" means we keep every predicate rather than hand-picking fields
    per rdf:type."""
    grouped: dict[str, list[str]] = {}
    for row in rows:
        grouped.setdefault(_local_name(row["predicate"]), []).append(row["object"])
    return grouped


def _labels_for(conn: sqlite3.Connection, iris: list[str]) -> dict[str, str]:
    if not iris:
        return {}
    placeholders = ",".join("?" for _ in iris)
    rows = conn.execute(
        f"SELECT subject, object FROM quads WHERE predicate=? AND subject IN ({placeholders})",
        (RDFS_LABEL, *iris),
    ).fetchall()
    labels: dict[str, str] = {}
    for row in rows:
        labels.setdefault(row["subject"], row["object"])
    return labels


# ---------------------------------------------------------------------
# Layer 1: the story map


@dataclass
class StoryFeature:
    id: str
    iri: str
    type_local: str
    label: str | None
    summary: str | None
    place_text: str | None
    coordinates: list[tuple[float, float]]
    vessel_iri: str | None
    vessel_label: str | None
    properties: dict[str, list[str]]
    claim_iris: list[str]


def _story_event_subjects(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT subject FROM quads WHERE graph='map' AND predicate=? ORDER BY subject",
        (PLACE_PREDICATE,),
    ).fetchall()
    return [row["subject"] for row in rows]


def _story_features(conn: sqlite3.Connection) -> list[StoryFeature]:
    subjects = _story_event_subjects(conn)
    features: list[StoryFeature] = []
    vessel_iris: set[str] = set()
    per_subject: dict[str, dict[str, list[str]]] = {}
    for subject in subjects:
        rows = conn.execute(
            "SELECT predicate, object FROM quads WHERE graph='map' AND subject=?",
            (subject,),
        ).fetchall()
        props = _group_predicates(rows)
        per_subject[subject] = props
        for vessel_iri in props.get("ofIdentity", []):
            vessel_iris.add(vessel_iri)
    vessel_labels = _labels_for(conn, sorted(vessel_iris))

    for subject in subjects:
        props = per_subject[subject]
        type_iris = [
            v
            for v in props.get("type", [])
            if v.startswith(NS)
        ]
        story_types = [t for t in type_iris if t in STORY_TYPES]
        if not story_types:
            continue  # not one of doc 11's promoted story types
        vessel_iri = props.get("ofIdentity", [None])[0]
        features.append(
            StoryFeature(
                id=_local_name(subject),
                iri=subject,
                type_local=_local_name(story_types[0]),
                label=props.get("label", [None])[0],
                summary=props.get("comment", [None])[0],
                place_text=props.get("place", [None])[0],
                coordinates=parse_coordinates(props.get("place", [None])[0]),
                vessel_iri=vessel_iri,
                vessel_label=vessel_labels.get(vessel_iri) if vessel_iri else None,
                properties=props,
                claim_iris=props.get("seeAlso", []),
            )
        )
    return features


# Properties every story feature already surfaces structurally (label,
# summary, place, ofIdentity, rdf:type, claim links) -- excluded from the
# generic "extra" bag in geojson properties so popups aren't duplicated.
_STORY_CORE_PREDICATES = {"type", "label", "comment", "place", "ofIdentity", "seeAlso"}


def _story_geojson_feature(feature: StoryFeature) -> dict[str, Any] | None:
    coords = feature.coordinates
    if not coords:
        return None  # nothing to render -- place text had no parseable coordinate
    if len(coords) == 1:
        lat, lon = coords[0]
        geometry = {"type": "Point", "coordinates": [lon, lat]}
    else:
        geometry = {"type": "LineString", "coordinates": [[lon, lat] for lat, lon in coords]}
    extra = {
        key: values[0] if len(values) == 1 else values
        for key, values in feature.properties.items()
        if key not in _STORY_CORE_PREDICATES
    }
    return {
        "type": "Feature",
        "id": feature.id,
        "geometry": geometry,
        "properties": {
            "layer": "story-map",
            "id": feature.id,
            "iri": feature.iri,
            "story_type": feature.type_local,
            "label": feature.label,
            "summary": feature.summary,
            "place_text": feature.place_text,
            "vessel_iri": feature.vessel_iri,
            "vessel_label": feature.vessel_label,
            "point_count": len(coords),
            "extra": extra,
            "provenance_ref": f"provenance/{feature.id}.json",
        },
    }


# ---------------------------------------------------------------------
# Claim/evidence chain (doc 11's "how this is known" panel data)


def _resource_props(conn: sqlite3.Connection, iri: str) -> dict[str, list[str]]:
    rows = conn.execute("SELECT predicate, object FROM quads WHERE subject=?", (iri,)).fetchall()
    return _group_predicates(rows)


def claim_chain(conn: sqlite3.Connection, claim_iris: list[str]) -> list[dict[str, Any]]:
    """event --rdfs:seeAlso--> claim --(reverse rc:hasClaim)-- observation
    --rc:evidence--> evidence. Walked once per feature via direct SQL
    (small, per-feature fan-out); this is the same chain a resource page's
    Claim section on the workbench shows, assembled here as a standalone
    JSON object rather than HTML."""
    chain: list[dict[str, Any]] = []
    for claim_iri in claim_iris:
        claim_props = _resource_props(conn, claim_iri)
        if not claim_props:
            continue
        obs_rows = conn.execute(
            "SELECT subject FROM quads WHERE predicate=? AND object=?",
            (HAS_CLAIM, claim_iri),
        ).fetchall()
        observations = []
        for obs_row in obs_rows:
            obs_iri = obs_row["subject"]
            obs_props = _resource_props(conn, obs_iri)
            evidence_entries = []
            for evidence_iri in obs_props.get("evidence", []):
                ev_props = _resource_props(conn, evidence_iri)
                evidence_entries.append(
                    {
                        "iri": evidence_iri,
                        "summary": ev_props.get("summary", [None])[0],
                        "source": ev_props.get("source", []),
                    }
                )
            observations.append(
                {
                    "iri": obs_iri,
                    "summary": obs_props.get("summary", [None])[0],
                    "observed_at": obs_props.get("observedAt", [None])[0],
                    "observation_status": (
                        _local_name(obs_props.get("observationStatus", [""])[0])
                        if obs_props.get("observationStatus")
                        else None
                    ),
                    "evidence": evidence_entries,
                }
            )
        chain.append(
            {
                "claim_iri": claim_iri,
                "claim_text": claim_props.get("claimText", claim_props.get("label", [None]))[0],
                "claim_kind": (
                    _local_name(claim_props.get("claimKind", [""])[0])
                    if claim_props.get("claimKind")
                    else None
                ),
                "confidence": (
                    _local_name(claim_props.get("confidence", [""])[0])
                    if claim_props.get("confidence")
                    else None
                ),
                "observation_status": (
                    _local_name(claim_props.get("observationStatus", [""])[0])
                    if claim_props.get("observationStatus")
                    else None
                ),
                "claim_targets": claim_props.get("claimTarget", []),
                "observations": observations,
            }
        )
    return chain


# ---------------------------------------------------------------------
# Layer 2: the shuttle census (M9 + M2, re-run against the described
# daily-index dataset -- see module docstring finding 2)

_M9_LAYER1_SQL = """
WITH flagged AS (
  SELECT mmsi, date, sog_mean, distance_m, centroid_lat, centroid_lon,
    (sog_mean<3.0 AND distance_m<50000) AS stationary_candidate,
    lag(date) OVER w AS prev_date2,
    lag(sog_mean<3.0 AND distance_m<50000) OVER w AS prev_stat2
  FROM read_parquet('{glob}') WINDOW w AS (PARTITION BY mmsi ORDER BY date)
), grouped AS (
  SELECT *, SUM(CASE WHEN prev_date2 IS NULL OR stationary_candidate<>prev_stat2
      OR (date_diff('day',prev_date2,date)>1 AND NOT (prev_date2=DATE '2024-08-25' AND date=DATE '2024-08-27'))
      THEN 1 ELSE 0 END) OVER (PARTITION BY mmsi ORDER BY date) AS grp_id
  FROM flagged
), ranked AS (
  SELECT *, row_number() OVER (PARTITION BY mmsi,grp_id ORDER BY date) AS rn,
    count(*) OVER (PARTITION BY mmsi,grp_id) AS cnt FROM grouped
)
SELECT mmsi, min(date) span_start, max(date) span_end, count(*) span_days,
  avg(CASE WHEN NOT (cnt>2 AND (rn=1 OR rn=cnt)) THEN centroid_lat END) AS core_lat,
  avg(CASE WHEN NOT (cnt>2 AND (rn=1 OR rn=cnt)) THEN centroid_lon END) AS core_lon
FROM ranked WHERE stationary_candidate GROUP BY mmsi, grp_id
"""

# M2's own recorded ExecutableQuerySnippet SQL (ais.study/query/m2-multi-
# emitter-detector), reused unmodified per M9's pattern text ("M2's own SQL
# unmodified").
_M2_SQL = """
WITH daily AS (
  SELECT mmsi, date, message_count, max_inter_msg_speed_ms,
         greatest(max_lat - min_lat,
                  (max_lon - min_lon) * cos(radians(centroid_lat))) AS span_deg
  FROM read_parquet('{glob}')
),
per AS (
  SELECT mmsi, count(*) AS active_days,
    count(*) FILTER (max_inter_msg_speed_ms > 100 AND message_count >= 20) AS conflict_days,
    quantile_cont(span_deg, 0.5)
      FILTER (max_inter_msg_speed_ms > 100 AND message_count >= 20) AS med_span_conflict
  FROM daily GROUP BY mmsi
)
SELECT mmsi,
  CASE
    WHEN conflict_days >= 10 AND conflict_days / active_days::DOUBLE >= 0.3
         AND med_span_conflict >= 1.0 THEN 'multi_emitter'
    WHEN conflict_days >= 10 AND med_span_conflict < 0.5 THEN 'position_jitter'
    WHEN conflict_days >= 10 THEN 'mixed_or_unclear'
    ELSE 'clean_or_sporadic'
  END AS emitter_class
FROM per
"""

# M9 thresholds, verbatim from the pattern text (richcanopy.org/.../pattern/
# 404f92f7-ba30-4e16-a8a5-8f6494680fbd): "METRICS (all thresholds tuned on
# this run, not discovered constants)".
M9_MIN_CONCENTRATION = 0.85
M9_MIN_POLE_SEP_DEG = 0.15
M9_MIN_SPANS_TOP2 = 8
M9_MIN_SWITCHES = 6
M9_MAX_DWELL_FRACTION = 0.5
M9_MIN_TOP2_WINDOW_DAYS = 300

M9_PATTERN_IRI = "https://richcanopy.org/doxabase/generated/pattern/404f92f7-ba30-4e16-a8a5-8f6494680fbd"
M9_EVIDENCE_IRI = "https://richcanopy.org/doxabase/generated/evidence/94c4bfa1-7de1-4ded-9b3a-6db0fe41c915"
M9_CENSUS_CLAIM_IRI = "https://richcanopy.org/doxabase/generated/claim/f770dc81-01c3-4729-8005-a0c5dfa784bb"
M2_VIEW_IRI = "https://ais.study/view/multi-emitter-mmsis"
M2_QUERY_IRI = "https://ais.study/query/m2-multi-emitter-detector"

# Session 9's per-vessel classification of the 17 M9-census members whose
# two-pole pattern last ran before 2025-06-01 (doc 11 section 4's
# "17-stopped population"), hand-extracted from claim
# richcanopy.org/.../claim/c10c1857-3556-4b02-bc82-ebf8d828a755 (evidence
# richcanopy.org/.../evidence/a2a0eedf-c815-4ace-a289-723ea6f9f497) -- the
# same "pull a small hardcoded table out of the graph, cite the source
# IRI" cheapness convention ``story_kml.py`` already uses for its own
# exemplar constants, not a fresh graph fact this exporter invents.
STOPPED_CLASSIFICATION_CLAIM_IRI = "https://richcanopy.org/doxabase/generated/claim/c10c1857-3556-4b02-bc82-ebf8d828a755"
STOPPED_CLASSIFICATION_EVIDENCE_IRI = "https://richcanopy.org/doxabase/generated/evidence/a2a0eedf-c815-4ace-a289-723ea6f9f497"

STOPPED_VESSELS: dict[int, dict[str, str]] = {
    244023610: {"name": "THAT'S LIFE", "stop_kind": "left_region",
                "note": "confirmed Pacific passage to Hawaii, physically plausible at ~3.2kn average"},
    303340000: {"name": "PRESIDENT CLEVELAND", "stop_kind": "left_region",
                "note": "confirmed offshore-accelerating departure track through the Golden Gate"},
    351249000: {"name": "NYK OCEANUS", "stop_kind": "left_region",
                "note": "probable, identical departure-track signature"},
    564561000: {"name": "SIRIUS LEADER", "stop_kind": "left_region",
                "note": "probable, low-duty foreign trader mostly outside coverage"},
    338436529: {"name": "VISTA", "stop_kind": "retasked_route",
                "note": "confirmed relocation track to a new operating area"},
    353746000: {"name": "EMILY G", "stop_kind": "retasked_route",
                "note": "confirmed relocation track to a new operating area"},
    477528400: {"name": "SEASPAN ADONIS", "stop_kind": "retasked_route",
                "note": "confirmed relocation track to a new operating area"},
    431710000: {"name": "ONE ALTAIR", "stop_kind": "retasked_route",
                "note": "confirmed relocation track to a new operating area"},
    338427574: {"name": "FIGHT ON", "stop_kind": "retasked_route",
                "note": "confirmed relocation track to a new operating area"},
    311000344: {"name": "COUGAR", "stop_kind": "retasked_route",
                "note": "confirmed relocation track to a new operating area"},
    338215013: {"name": "BARBARA ANN", "stop_kind": "apparent_layup",
                "note": "no relocation evidence found; endpoint stayed busy with other traffic"},
    338139747: {"name": "A-MACHAYA III", "stop_kind": "apparent_layup",
                "note": "no relocation evidence found; endpoint stayed busy with other traffic"},
    368078410: {"name": "HONDO", "stop_kind": "apparent_layup",
                "note": "no relocation evidence found; endpoint stayed busy with other traffic"},
    368065940: {"name": "PRIVATEER", "stop_kind": "apparent_layup",
                "note": "no relocation evidence found; endpoint stayed busy with other traffic"},
    368060840: {"name": "HARBOUR LIGHTS", "stop_kind": "apparent_layup",
                "note": "no relocation evidence found; endpoint stayed busy with other traffic"},
    368148950: {"name": "ENDEAVOUR", "stop_kind": "apparent_layup",
                "note": "no relocation evidence found; endpoint stayed busy with other traffic"},
    369494117: {"name": "CG33117", "stop_kind": "government_reassignment",
                "note": "USCG cutter, government reassignment"},
}

# AIS ship-type code -> a small "folders by classification" bucket (round-4
# expert directive). Standard ITU-R M.1371 ship-type ranges, folded to
# roughly MAX_CATEGORIES-sized buckets (workbench/maps.py's own cap) rather
# than one folder per exact code.
_AIS_TYPE_BUCKETS: list[tuple[range, str]] = [
    (range(30, 31), "fishing"),
    (range(31, 33), "towing"),
    (range(33, 34), "dredging"),
    (range(34, 36), "diving_military"),
    (range(36, 38), "pleasure_sailing"),
    (range(40, 50), "high_speed_craft"),
    (range(50, 60), "specialized_service"),
    (range(60, 70), "passenger"),
    (range(70, 80), "cargo"),
    (range(80, 90), "tanker"),
    (range(90, 100), "other"),
]


def classify_ais_type(code: int | None) -> str:
    if code is None:
        return "unknown"
    for code_range, bucket in _AIS_TYPE_BUCKETS:
        if code in code_range:
            return bucket
    return "unknown"


def _connect_s3(minio_endpoint: str, minio_access_key: str, minio_secret_key: str):
    """Same DuckDB httpfs + MinIO env-var convention as
    ``workbench/frames.py``/``docs/journal/ais-study/story_kml.py`` --
    reimplemented rather than imported because ``frames.run_query`` is
    deliberately restricted to one analyst-supplied SELECT against a
    ``frame`` view; this pipeline is a fixed, reviewed, multi-statement
    build step, not untrusted input."""
    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    endpoint = minio_endpoint.replace("http://", "").replace("https://", "")
    con.execute(f"SET s3_endpoint='{endpoint}'")
    con.execute("SET s3_url_style='path'; SET s3_use_ssl=false; SET s3_region='local';")
    con.execute(f"SET s3_access_key_id='{minio_access_key}'")
    con.execute(f"SET s3_secret_access_key='{minio_secret_key}'")
    return con


@dataclass
class ShuttleFeature:
    mmsi: int
    pole1: tuple[float, float]
    pole2: tuple[float, float]
    pole1_days: int
    pole2_days: int
    concentration: float
    pole_sep_deg: float
    n_spans_top2: int
    n_switches: int
    dwell_fraction: float
    top2_window_days: int
    emitter_class: str
    ais_type: int | None
    vessel_class: str
    stopped: bool
    stop_kind: str | None
    stop_note: str | None
    vessel_name: str | None


def _run_m9_census(con, index_glob: str) -> list[ShuttleFeature]:
    """Re-derive the M9 (+ M2 exclusion) shuttle population against the
    live described dataset -- see module docstring finding 2 for why the
    resulting count is close to, but not byte-identical with, the
    capsule's own recorded 820."""
    con.execute(f"CREATE TEMP TABLE dwell_spans AS {_M9_LAYER1_SQL.format(glob=index_glob)}")
    con.execute(
        """
        CREATE TEMP TABLE binned AS
        SELECT *, ROUND(core_lat,1) AS bin_lat, ROUND(core_lon,1) AS bin_lon
        FROM dwell_spans WHERE core_lat IS NOT NULL AND core_lon IS NOT NULL
        """
    )
    con.execute(
        """
        CREATE TEMP TABLE bin_totals AS
        SELECT mmsi, bin_lat, bin_lon, SUM(span_days) AS bin_days, COUNT(*) AS bin_spans,
               AVG(core_lat) AS pole_lat, AVG(core_lon) AS pole_lon
        FROM binned GROUP BY mmsi, bin_lat, bin_lon
        """
    )
    con.execute(
        """
        CREATE TEMP TABLE bin_ranked AS
        SELECT *, ROW_NUMBER() OVER (
            PARTITION BY mmsi ORDER BY bin_days DESC, bin_spans DESC, bin_lat, bin_lon
        ) AS bin_rank
        FROM bin_totals
        """
    )
    con.execute(
        """
        CREATE TEMP TABLE mmsi_all_days AS
        SELECT mmsi, SUM(bin_days) AS all_bin_days FROM bin_totals GROUP BY mmsi
        """
    )
    con.execute(
        """
        CREATE TEMP TABLE top2_pairs AS
        SELECT
          mmsi,
          MAX(CASE WHEN bin_rank=1 THEN bin_lat END) AS pole1_bin_lat,
          MAX(CASE WHEN bin_rank=1 THEN bin_lon END) AS pole1_bin_lon,
          MAX(CASE WHEN bin_rank=1 THEN pole_lat END) AS pole1_lat,
          MAX(CASE WHEN bin_rank=1 THEN pole_lon END) AS pole1_lon,
          MAX(CASE WHEN bin_rank=1 THEN bin_days END) AS pole1_days,
          MAX(CASE WHEN bin_rank=2 THEN bin_lat END) AS pole2_bin_lat,
          MAX(CASE WHEN bin_rank=2 THEN bin_lon END) AS pole2_bin_lon,
          MAX(CASE WHEN bin_rank=2 THEN pole_lat END) AS pole2_lat,
          MAX(CASE WHEN bin_rank=2 THEN pole_lon END) AS pole2_lon,
          MAX(CASE WHEN bin_rank=2 THEN bin_days END) AS pole2_days,
          COUNT(*) AS n_bins_present
        FROM bin_ranked WHERE bin_rank <= 2 GROUP BY mmsi HAVING COUNT(*) = 2
        """
    )
    con.execute(
        """
        CREATE TEMP TABLE top2_spans AS
        SELECT b.mmsi, b.span_start, b.span_end, b.span_days,
           CASE WHEN b.bin_lat=t.pole1_bin_lat AND b.bin_lon=t.pole1_bin_lon THEN 1 ELSE 2 END AS pole_no
        FROM binned b JOIN top2_pairs t ON b.mmsi=t.mmsi
        WHERE (b.bin_lat=t.pole1_bin_lat AND b.bin_lon=t.pole1_bin_lon)
           OR (b.bin_lat=t.pole2_bin_lat AND b.bin_lon=t.pole2_bin_lon)
        """
    )
    con.execute(
        """
        CREATE TEMP TABLE switches AS
        SELECT mmsi,
          SUM(CASE WHEN prev_pole IS NOT NULL AND prev_pole<>pole_no THEN 1 ELSE 0 END) AS n_switches,
          MIN(span_start) AS top2_window_start, MAX(span_end) AS top2_window_end,
          COUNT(*) AS n_spans_top2
        FROM (
          SELECT *, LAG(pole_no) OVER (PARTITION BY mmsi ORDER BY span_start) AS prev_pole
          FROM top2_spans
        ) GROUP BY mmsi
        """
    )
    con.execute(f"CREATE TEMP TABLE emitter_class AS {_M2_SQL.format(glob=index_glob)}")
    rows = con.execute(
        """
        SELECT p.mmsi, p.pole1_lat, p.pole1_lon, p.pole1_days, p.pole2_lat, p.pole2_lon, p.pole2_days,
           (p.pole1_days+p.pole2_days)::DOUBLE / a.all_bin_days AS concentration,
           GREATEST(ABS(p.pole1_lat-p.pole2_lat),
                    ABS(p.pole1_lon-p.pole2_lon)*COS(RADIANS((p.pole1_lat+p.pole2_lat)/2))) AS pole_sep_deg,
           s.n_spans_top2, s.n_switches,
           (p.pole1_days+p.pole2_days)::DOUBLE
             / NULLIF(date_diff('day', s.top2_window_start, s.top2_window_end),0) AS dwell_fraction,
           date_diff('day', s.top2_window_start, s.top2_window_end) AS top2_window_days,
           e.emitter_class
        FROM top2_pairs p
        JOIN mmsi_all_days a ON a.mmsi=p.mmsi
        JOIN switches s ON s.mmsi=p.mmsi
        LEFT JOIN emitter_class e ON e.mmsi=p.mmsi
        WHERE p.pole1_days+p.pole2_days > 0
          AND (p.pole1_days+p.pole2_days)::DOUBLE / a.all_bin_days >= ?
          AND GREATEST(ABS(p.pole1_lat-p.pole2_lat),
                       ABS(p.pole1_lon-p.pole2_lon)*COS(RADIANS((p.pole1_lat+p.pole2_lat)/2))) >= ?
          AND s.n_spans_top2 >= ? AND s.n_switches >= ?
          AND (p.pole1_days+p.pole2_days)::DOUBLE
              / NULLIF(date_diff('day', s.top2_window_start, s.top2_window_end),0) <= ?
          AND date_diff('day', s.top2_window_start, s.top2_window_end) >= ?
          AND (e.emitter_class IS NULL OR e.emitter_class != 'multi_emitter')
        """,
        [
            M9_MIN_CONCENTRATION, M9_MIN_POLE_SEP_DEG, M9_MIN_SPANS_TOP2,
            M9_MIN_SWITCHES, M9_MAX_DWELL_FRACTION, M9_MIN_TOP2_WINDOW_DAYS,
        ],
    ).fetchall()

    mmsi_list = [row[0] for row in rows]
    modal_type = _modal_vessel_types(con, index_glob, mmsi_list) if mmsi_list else {}

    features: list[ShuttleFeature] = []
    for row in rows:
        (mmsi, p1_lat, p1_lon, p1_days, p2_lat, p2_lon, p2_days, concentration,
         pole_sep, n_spans, n_switches, dwell_fraction, window_days, emitter_class) = row
        ais_type = modal_type.get(mmsi)
        stopped_info = STOPPED_VESSELS.get(mmsi)
        features.append(
            ShuttleFeature(
                mmsi=mmsi,
                pole1=(p1_lat, p1_lon),
                pole2=(p2_lat, p2_lon),
                pole1_days=int(p1_days),
                pole2_days=int(p2_days),
                concentration=float(concentration),
                pole_sep_deg=float(pole_sep),
                n_spans_top2=int(n_spans),
                n_switches=int(n_switches),
                dwell_fraction=float(dwell_fraction) if dwell_fraction is not None else 0.0,
                top2_window_days=int(window_days),
                emitter_class=emitter_class or "unclassified",
                ais_type=ais_type,
                vessel_class=classify_ais_type(ais_type),
                stopped=stopped_info is not None,
                stop_kind=stopped_info["stop_kind"] if stopped_info else None,
                stop_note=stopped_info["note"] if stopped_info else None,
                vessel_name=stopped_info["name"] if stopped_info else None,
            )
        )
    return features


def _modal_vessel_types(con, index_glob: str, mmsi_list: list[int]) -> dict[int, int]:
    """Most frequent AIS vessel_type code per candidate MMSI, scoped to the
    candidate list before unnesting to keep the second full-index pass
    cheap."""
    con.execute(
        "CREATE TEMP TABLE _census_mmsi(mmsi BIGINT)"
    )
    con.executemany("INSERT INTO _census_mmsi VALUES (?)", [(m,) for m in mmsi_list])
    rows = con.execute(
        f"""
        WITH exploded AS (
          SELECT idx.mmsi, unnest(idx.vessel_types) AS vtype
          FROM read_parquet('{index_glob}') idx
          JOIN _census_mmsi c ON c.mmsi = idx.mmsi
          WHERE idx.vessel_types IS NOT NULL
        ),
        counted AS (
          SELECT mmsi, vtype, count(*) AS n FROM exploded GROUP BY 1, 2
        )
        SELECT mmsi, vtype FROM (
          SELECT mmsi, vtype, row_number() OVER (PARTITION BY mmsi ORDER BY n DESC) AS rn
          FROM counted
        ) WHERE rn = 1
        """
    ).fetchall()
    return {mmsi: int(vtype) for mmsi, vtype in rows}


def _shuttle_geojson_feature(feature: ShuttleFeature) -> dict[str, Any]:
    lat1, lon1 = feature.pole1
    lat2, lon2 = feature.pole2
    feature_id = f"shuttle-{feature.mmsi}"
    return {
        "type": "Feature",
        "id": feature_id,
        "geometry": {"type": "LineString", "coordinates": [[lon1, lat1], [lon2, lat2]]},
        "properties": {
            "layer": "shuttle-census",
            "id": feature_id,
            "mmsi": feature.mmsi,
            "vessel_name": feature.vessel_name,
            "vessel_class": feature.vessel_class,
            "ais_type": feature.ais_type,
            "emitter_class": feature.emitter_class,
            "stopped": feature.stopped,
            "stop_kind": feature.stop_kind,
            "stop_note": feature.stop_note,
            "pole1_days": feature.pole1_days,
            "pole2_days": feature.pole2_days,
            "concentration": round(feature.concentration, 3),
            "n_spans_top2": feature.n_spans_top2,
            "n_switches": feature.n_switches,
            "dwell_fraction": round(feature.dwell_fraction, 3),
            "top2_window_days": feature.top2_window_days,
            "provenance_ref": f"provenance/{feature_id}.json",
        },
    }


def _shuttle_provenance(feature: ShuttleFeature) -> dict[str, Any]:
    """Population-scale features cite the method (M9 + M2), not a bespoke
    per-vessel claim -- honest given the graph doesn't record 820
    individual claims. The 17 stopped vessels additionally cite their own
    session-9 classification claim/evidence and carry their specific note."""
    chain: dict[str, Any] = {
        "feature_id": f"shuttle-{feature.mmsi}",
        "kind": "derived_population_member",
        "method_chain": [
            {
                "role": "detector",
                "iri": M9_PATTERN_IRI,
                "label": "M9 method: two-point shuttle detector",
                "evidence_iri": M9_EVIDENCE_IRI,
            },
            {
                "role": "shared-mmsi exclusion filter",
                "iri": M2_VIEW_IRI,
                "label": "M2: multi-emitter / shared-MMSI detector",
                "query_iri": M2_QUERY_IRI,
            },
            {
                "role": "recorded aggregate census",
                "iri": M9_CENSUS_CLAIM_IRI,
                "label": "Shuttle census (M9, strict thresholds): 820 MMSI pass ...",
            },
        ],
        "computed_metrics": {
            "concentration": round(feature.concentration, 4),
            "pole_sep_deg": round(feature.pole_sep_deg, 4),
            "n_spans_top2": feature.n_spans_top2,
            "n_switches": feature.n_switches,
            "dwell_fraction": round(feature.dwell_fraction, 4),
            "top2_window_days": feature.top2_window_days,
            "emitter_class": feature.emitter_class,
        },
        "computation_note": (
            "Recomputed live by the exporter from M9's own recorded threshold "
            "definitions (pattern " + M9_PATTERN_IRI + ") against the described "
            "daily-index dataset, because M9's layer-2 pole-ranking/switch-"
            "counting logic is recorded in the graph as prose, not literal SQL. "
            "This is an independently reproduced, auditable computation over a "
            "described dataset, not a graph-asserted fact about this specific "
            "MMSI."
        ),
    }
    if feature.stopped:
        chain["stop_classification"] = {
            "claim_iri": STOPPED_CLASSIFICATION_CLAIM_IRI,
            "evidence_iri": STOPPED_CLASSIFICATION_EVIDENCE_IRI,
            "stop_kind": feature.stop_kind,
            "note": feature.stop_note,
        }
    return chain


# ---------------------------------------------------------------------
# Export-eligibility posture (doc 11 section 2: "export_preflight + human
# review before any bundle goes public")


def _export_eligibility(db: DoxaBase) -> dict[str, Any]:
    try:
        record = db.export_preflight(export_kind="graph", graphs=["map"], limit=5)
        preflight = to_dict(record)
        preflight_summary = {
            "decision": preflight.get("decision"),
            "scanner_clean": preflight.get("scanner_clean"),
            "would_block_sensitive_export": preflight.get("would_block_sensitive_export"),
            "validation_conforms": preflight.get("validation_conforms"),
            "validation_result_count": preflight.get("validation_result_count"),
            "warnings": preflight.get("warnings", [])[:3],
        }
        error = None
    except Exception as exc:  # pragma: no cover - defensive; preflight is best-effort
        preflight_summary = None
        error = str(exc)
    return {
        "status": "local_only_pending_review",
        "note": (
            "Doc 11's public-mode gating (promoted/reviewed resources only, "
            "controlled wording by claim type/confidence) is future work -- "
            "this bundle is expert-mode output only and is NOT stamped for "
            "public sharing. export_preflight (scanner + validation) was run "
            "against the map graph as an informational check, not a publish "
            "gate; shareability_review_status stays required_not_completed "
            "regardless of its result. See README.md and doc 11 section 1."
        ),
        "export_preflight_summary": preflight_summary,
        "export_preflight_error": error,
    }


# ---------------------------------------------------------------------
# Manifest + bundle orchestration


def _data_window(db: DoxaBase) -> str | None:
    try:
        description = db.describe_dataset("https://ais.study/dataset/daily-index")
    except Exception:
        return None
    text = description.description or ""
    match = re.search(r"\d{4}-\d{2}-\d{2}\.\.\d{4}-\d{2}-\d{2}(?:, [^.]*missing)?", text)
    return match.group(0) if match else None


def _tool_version() -> str:
    try:
        return importlib_metadata.version("doxabase")
    except importlib_metadata.PackageNotFoundError:  # pragma: no cover
        return "unknown"


@dataclass
class LayerSummary:
    id: str
    title: str
    file: str
    kind: str
    feature_count: int
    description: str
    sampling: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportSummary:
    outdir: Path
    manifest: dict[str, Any]
    layers: list[LayerSummary]


def export_bundle(
    capsule_path: Path,
    outdir: Path,
    *,
    minio_endpoint: str | None,
    minio_access_key: str | None,
    minio_secret_key: str | None,
    tiles_enabled: bool = True,
    skip_shuttle_layer: bool = False,
) -> ExportSummary:
    """Build the full static bundle (doc 11 section 2). ``skip_shuttle_layer``
    exists only for fast offline smoke runs where MinIO isn't reachable;
    the default (real) export always includes both layers."""
    capsule_path = Path(capsule_path)
    outdir = Path(outdir)
    (outdir / "layers").mkdir(parents=True, exist_ok=True)
    (outdir / "provenance").mkdir(parents=True, exist_ok=True)

    with DoxaBase.open_readonly(capsule_path) as db:
        eligibility = _export_eligibility(db)
        data_window = _data_window(db)
        try:
            index_description = db.describe_dataset("https://ais.study/dataset/daily-index")
            index_templates = index_description.path_templates
        except Exception:
            index_templates = []

    conn = _connect_capsule(capsule_path)
    try:
        story_features = _story_features(conn)
        story_geojson_features = []
        provenance_written = 0
        for feature in story_features:
            geojson_feature = _story_geojson_feature(feature)
            if geojson_feature is None:
                continue
            story_geojson_features.append(geojson_feature)
            chain = claim_chain(conn, feature.claim_iris)
            provenance = {
                "feature_id": feature.id,
                "kind": "asserted_story_resource",
                "resource_iri": feature.iri,
                "place_text": feature.place_text,
                "claim_chain": chain,
            }
            (outdir / "provenance" / f"{feature.id}.json").write_text(
                json.dumps(provenance, indent=2, sort_keys=True) + "\n"
            )
            provenance_written += 1
        skipped_no_coords = len(story_features) - len(story_geojson_features)
    finally:
        conn.close()

    story_layer = LayerSummary(
        id="story-map",
        title="Story map",
        file="layers/story-map.geojson",
        kind="story",
        feature_count=len(story_geojson_features),
        description=(
            "Promoted vessel stories -- dwell poles, identity-change sites, "
            "and draft-change/silence events -- each opening its claim chain "
            "(doc 11 section 4, Layer 1). Coordinates parsed from each "
            "resource's aisv:place literal; see the exporter module "
            "docstring's finding 1 for the honest caveat on that."
        ),
    )
    _write_geojson(outdir / story_layer.file, story_geojson_features)

    layers = [story_layer]

    if not skip_shuttle_layer:
        if not (minio_endpoint and minio_access_key and minio_secret_key):
            raise RuntimeError(
                "MINIO_ENDPOINT / MINIO_ACCESS_KEY / MINIO_SECRET_KEY must all be set "
                "to build Layer 2 (the shuttle census reads the described daily-index "
                "dataset from S3). Pass --skip-shuttle-layer to export Layer 1 only."
            )
        if not index_templates:
            raise RuntimeError(
                "Could not resolve the daily-index dataset's path_templates from the "
                "capsule; cannot build Layer 2."
            )
        index_glob = re.sub(r"\{[^}]+\}", "*", index_templates[0])
        con = _connect_s3(minio_endpoint, minio_access_key, minio_secret_key)
        try:
            shuttle_features = _run_m9_census(con, index_glob)
        finally:
            con.close()

        shuttle_geojson_features = [_shuttle_geojson_feature(f) for f in shuttle_features]
        for feature, geojson_feature in zip(shuttle_features, shuttle_geojson_features):
            provenance = _shuttle_provenance(feature)
            (outdir / "provenance" / f"{geojson_feature['id']}.json").write_text(
                json.dumps(provenance, indent=2, sort_keys=True) + "\n"
            )
        stopped_found = sum(1 for f in shuttle_features if f.stopped)
        shuttle_layer = LayerSummary(
            id="shuttle-census",
            title="Shuttle census (M9)",
            file="layers/shuttle-census.geojson",
            kind="population",
            feature_count=len(shuttle_geojson_features),
            description=(
                "Vessels matching M9's two-point shuttle detector (concentration"
                f">={M9_MIN_CONCENTRATION}, pole separation>={M9_MIN_POLE_SEP_DEG} deg, "
                "regular chronological alternation between two dwell poles), "
                "M2 shared-MMSI (multi_emitter) candidates excluded, class-"
                "filterable by AIS vessel type. The 17-vessel 'stopped' "
                "sub-population (pattern last active before 2025-06-01) is "
                "flagged with its session-9 stop-kind classification (doc 11 "
                "section 4)."
            ),
            sampling={
                "sampled": False,
                "note": (
                    "Full recomputed population included (doc 11 section 6's open "
                    "question 1: at ~800-900 features GeoJSON is fine, no tiling/"
                    "sampling needed)."
                ),
                "recorded_census_count": 820,
                "recomputed_count": len(shuttle_geojson_features),
                "stopped_population_found": stopped_found,
                "stopped_population_expected": len(STOPPED_VESSELS),
                "count_discrepancy_note": (
                    "See exporter module docstring finding 2: M9's layer-2 pole-"
                    "ranking SQL isn't recorded verbatim, only its prose thresholds, "
                    "so this recomputation's count is close to but not byte-"
                    "identical with the capsule's own recorded 820."
                ),
            },
        )
        _write_geojson(outdir / shuttle_layer.file, shuttle_geojson_features)
        layers.append(shuttle_layer)

    manifest = {
        "format": "doxabase.observatory_bundle.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "generator": {"tool": "doxabase-observatory", "doxabase_version": _tool_version()},
        "capsule": {
            "path": str(capsule_path),
            "data_window": data_window,
        },
        "mode": "expert",
        "export_eligibility": eligibility,
        "tiles": (
            {
                "enabled": True,
                "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                "attribution": (
                    '&copy; <a href="https://www.openstreetmap.org/copyright">'
                    "OpenStreetMap</a> contributors"
                ),
            }
            if tiles_enabled
            else {"enabled": False, "note": "Plain-grid fallback: no external tile requests."}
        ),
        "layers": [
            {
                "id": layer.id,
                "title": layer.title,
                "file": layer.file,
                "kind": layer.kind,
                "feature_count": layer.feature_count,
                "description": layer.description,
                "sampling": layer.sampling,
            }
            for layer in layers
        ],
        "provenance_dir": "provenance/",
        "provenance_count": provenance_written + sum(
            layer.feature_count for layer in layers if layer.kind == "population"
        ),
        "story_features_skipped_no_coordinates": skipped_no_coords,
        "kml_export": {
            "built": False,
            "note": (
                "Post-MVP per doc 11 section 4 ('export what I'm looking at as "
                "KML/KMZ', expert round 6): deliberately out of scope for this "
                "layers-1-2 cut. docs/journal/ais-study/story_kml.py remains the "
                "cheap KML path/peer output a future session can wire to this "
                "exporter's own feature data."
            ),
        },
    }
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    _copy_viewer_assets(outdir)

    return ExportSummary(outdir=outdir, manifest=manifest, layers=layers)


def _write_geojson(path: Path, features: list[dict[str, Any]]) -> None:
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, indent=2, sort_keys=True)
        + "\n"
    )


def _copy_viewer_assets(outdir: Path) -> None:
    for name in ("index.html", "observatory.js", "observatory.css"):
        shutil.copyfile(_ASSETS_DIR / name, outdir / name)
    vendor_dest = outdir / "vendor" / "leaflet"
    if vendor_dest.exists():
        shutil.rmtree(vendor_dest)
    shutil.copytree(_VENDOR_LEAFLET_SRC, vendor_dest)


# ---------------------------------------------------------------------
# CLI


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="doxabase-observatory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser(
        "export", help="Export a static viewer bundle (layers 1-2) from a capsule."
    )
    export_parser.add_argument("capsule", help="Path to a capsule .sqlite file (opened read-only)")
    export_parser.add_argument("outdir", help="Directory to write the bundle into")
    export_parser.add_argument(
        "--tiles",
        choices=["on", "off"],
        default="on",
        help="OSM raster tiles (on) vs plain-grid fallback (off), stamped into manifest.json.",
    )
    export_parser.add_argument(
        "--skip-shuttle-layer",
        action="store_true",
        help="Export Layer 1 (story map) only; skip Layer 2 (needs S3/MinIO access).",
    )
    args = parser.parse_args(argv)

    if args.command == "export":
        try:
            import duckdb  # noqa: F401  (import-only: proves the workbench extra is present)
        except ImportError as exc:
            raise SystemExit(
                "doxabase-observatory needs its optional extra: "
                'pip install "doxabase[workbench]" (missing: '
                f"{exc.name or exc})"
            ) from None

        import os

        summary = export_bundle(
            Path(args.capsule),
            Path(args.outdir),
            minio_endpoint=os.environ.get("MINIO_ENDPOINT"),
            minio_access_key=os.environ.get("MINIO_ACCESS_KEY"),
            minio_secret_key=os.environ.get("MINIO_SECRET_KEY"),
            tiles_enabled=(args.tiles == "on"),
            skip_shuttle_layer=args.skip_shuttle_layer,
        )
        print(f"wrote bundle to {summary.outdir}")
        for layer in summary.layers:
            print(f"  {layer.id}: {layer.feature_count} feature(s) -> {layer.file}")
        print(f"  manifest.json, provenance/ ({summary.manifest['provenance_count']} file(s))")
        print(f"  open with a local static server, e.g.: python -m http.server -d {summary.outdir}")


if __name__ == "__main__":
    main()
