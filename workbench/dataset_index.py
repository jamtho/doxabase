"""The /datasets landing page: every described dataset with recorded row
counts, storage reachability, and how much of the graph actually cites it.

Owner ask (2026-07-20, "row counts making datasets tractable is the
point -- lead with them"): the project-brief landing page already lists
datasets one at a time by column/caveat count, but an analyst has no
single place to see every described dataset's *scale* before opening it.
This module builds that one table.

``row_count_snapshot`` is whatever the capsule already holds as a
point-in-time snapshot (``DatasetDescription.row_count_snapshot``, backed
by ``rc:hasRowCountSnapshot`` triples an agent recorded) -- never a live
``COUNT(*)`` over a dataset's frame paid for on every page render. A
dataset's own query box (``/dataset?iri=...``) is where a live count
belongs, on request.
"""
from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path

from doxabase import DoxaBase

from . import frames

RC_TABLE = "rc:Table"
RC_DATASET = "rc:Dataset"

# rc:AnalysisView (doc 13/14): a named logical population whose denominator
# and query recipe are recorded for interpretation, never a direct physical
# route -- always "logical" storage regardless of any path_templates it
# happens to carry (see doxabase/core/datasets.py's is_table handling).
ANALYSIS_VIEW_TYPE = "https://richcanopy.org/ns/rc#AnalysisView"

# Most-specific-first rc: class local name worth surfacing as "kind",
# checked against a dataset's rdf:type set (see ontology/rc_core.ttl's
# DataAsset subclass tree). Friendly display labels alongside.
_KIND_PRECEDENCE = [
    ("AnalysisView", "analysis view"),
    ("DataFrame", "dataframe"),
    ("Table", "table"),
    ("Database", "database"),
    ("DataFile", "data file"),
    ("Dataset", "dataset"),
    ("DataAsset", "data asset"),
]


@dataclass(frozen=True)
class DatasetRow:
    iri: str
    label: str | None
    kind: str
    column_count: int
    caveat_count: int
    row_count_snapshot: int | None
    storage_kind: str
    reachable: bool | None  # None: not applicable (no physical layout to probe)
    referenced_by: int


def _dataset_kind(types: list[str]) -> str:
    local_names = {t.split("#")[-1].split("/")[-1] for t in types}
    for class_name, display in _KIND_PRECEDENCE:
        if class_name in local_names:
            return display
    return types[0].split("#")[-1].split("/")[-1] if types else "dataset"


def _storage_kind_and_reachability(description) -> tuple[str, bool | None]:
    """(storage kind label, reachability) for one dataset's description.

    Reuses frames.frame_glob/is_reachable -- the same S3-vs-local
    resolution and cheap glob() probe the dataset query box already runs
    before deciding whether to show itself -- so this badge and "can I
    query this" never disagree with each other.
    """
    if ANALYSIS_VIEW_TYPE in description.types or not description.path_templates:
        return "logical", None
    glob = frames.frame_glob(description.path_templates)
    if glob is None:
        return "logical", None
    kind = "S3" if glob.startswith("s3://") else "local"
    return kind, frames.is_reachable(glob)


def _connect(path: Path) -> sqlite3.Connection:
    uri = f"{Path(path).resolve().as_uri()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


_REFERENCED_BY_CACHE: dict[tuple[str, str], int] = {}
_REFERENCED_BY_LOCK = threading.Lock()


def _referenced_by_count(path: Path, dataset_iri: str, column_iris: list[str]) -> int:
    """How many map/observations entities cite this dataset or one of its
    columns -- the cheapest honest signal that a description is actually
    in use, not a full provenance trace.

    One COUNT(DISTINCT subject) over `quads` with an IN-list of the
    dataset IRI plus its column IRIs, restricted to the two graphs an
    agent's own findings live in (map, observations), excluding the
    dataset's own rc:hasColumn edges (subject == dataset_iri) -- without
    that exclusion every dataset's count would be inflated by at least
    its own column list, which is structure the dataset asserts about
    itself, not something else citing it.

    Cached per (capsule path, dataset iri) for the process lifetime, the
    same convention as frames.is_reachable's reachability cache: a
    capsule file does not change out from under a running read-only
    workbench process in practice, and the /datasets page would otherwise
    repeat this query on every render.
    """
    key = (str(path), dataset_iri)
    with _REFERENCED_BY_LOCK:
        cached = _REFERENCED_BY_CACHE.get(key)
    if cached is not None:
        return cached
    targets = [dataset_iri, *column_iris]
    conn = _connect(path)
    try:
        placeholders = ",".join("?" for _ in targets)
        row = conn.execute(
            f"""
            SELECT COUNT(DISTINCT subject) FROM quads
            WHERE graph IN ('map', 'observations')
              AND object IN ({placeholders})
              AND subject != ?
            """,
            (*targets, dataset_iri),
        ).fetchone()
    finally:
        conn.close()
    count = int(row[0]) if row else 0
    with _REFERENCED_BY_LOCK:
        _REFERENCED_BY_CACHE[key] = count
    return count


def _list_all(db: DoxaBase, type_iri: str):
    """Every entity of one type in the map graph -- list_entities with a
    second, exact-sized call only in the rare case a capsule has grown
    past the first page (the common case is one call)."""
    result = db.list_entities(type=type_iri, graph="map", limit=200)
    if result.has_more and result.total_count > len(result.entities):
        result = db.list_entities(type=type_iri, graph="map", limit=result.total_count)
    return result.entities


def _dataset_entities(db: DoxaBase) -> list:
    """Every rc:Table/rc:Dataset entity, deduplicated by IRI -- the same
    merge project_brief() does internally (doxabase/core/brief.py's
    private _project_brief_dataset_entities), reproduced here over the
    public list_entities call rather than reaching into that helper."""
    entities_by_iri: dict[str, object] = {}
    for type_iri in (RC_TABLE, RC_DATASET):
        for entity in _list_all(db, type_iri):
            entities_by_iri.setdefault(entity.iri, entity)
    return sorted(
        entities_by_iri.values(),
        key=lambda entity: (entity.label or entity.iri, entity.iri),
    )


def dataset_overview(path: Path, db: DoxaBase) -> list[DatasetRow]:
    """Every described dataset, row counts led first (owner ask): one row
    per rc:Table/rc:Dataset entity in the map graph with label, kind,
    column/caveat counts, recorded row-count snapshot, storage kind +
    reachability, and a referenced-by count."""
    rows: list[DatasetRow] = []
    for entity in _dataset_entities(db):
        description = db.describe_dataset(entity.iri)
        storage_kind, reachable = _storage_kind_and_reachability(description)
        column_iris = [column.iri for column in description.columns]
        rows.append(
            DatasetRow(
                iri=description.iri,
                label=description.label,
                kind=_dataset_kind(description.types),
                column_count=len(description.columns),
                caveat_count=len(description.caveats) + len(description.upstream_caveats),
                row_count_snapshot=description.row_count_snapshot,
                storage_kind=storage_kind,
                reachable=reachable,
                referenced_by=_referenced_by_count(path, description.iri, column_iris),
            )
        )
    return rows
