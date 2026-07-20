"""Types overview: which rdf:type instances exist in which named graph.

The wheel wraps entity listing (`list_entities`) and resource description,
but has no dedicated "types per graph" rollup -- and doesn't need one, since
this is exactly the kind of query the capsule's own SQLite storage answers
directly and fast: a single GROUP BY over the `quads` table keyed on
(graph, object) where predicate = rdf:type. Measured a couple of
milliseconds against the AIS capsule regardless of which query below is
run, so no caching layer here (contrast `_brief_cache` in app.py, which
exists for one genuinely slow call).

Each function opens its own short-lived read-only connection -- the same
`mode=ro` URI convention the wheel's own StorageMixin uses (see
`doxabase.core.storage`) -- rather than reaching into a `DoxaBase`
instance's private `_conn` from another package.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"

# The task's own graph role order: current working state (map) through
# project-owned extensions and the revision history, down to the immutable
# shipped seeds -- not alphabetical, and deliberately fixed rather than
# derived from `named_graphs` insertion order.
GRAPH_ROLE_ORDER = [
    "map",
    "ontology",
    "observations",
    "patterns",
    "evidence",
    "shapes",
    "history",
    "base_ontology",
    "base_shapes",
]


def _connect(path: Path) -> sqlite3.Connection:
    uri = f"{Path(path).resolve().as_uri()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _local_name(iri: str) -> str:
    """The same 'compacted' display the rest of the app already uses in
    place of a full IRI (resource.html, search.html): the fragment or last
    path segment. Most type IRIs in a project capsule (rc:, ais-study
    project vocab) aren't under a registered CURIE prefix anyway, so a real
    CURIE compaction would leave most of them unchanged -- this is the
    house style, not a lesser substitute for it."""
    return iri.split("#")[-1].split("/")[-1]


def _graph_order(conn: sqlite3.Connection) -> list[str]:
    present = {row["name"] for row in conn.execute("SELECT name FROM named_graphs")}
    ordered = [g for g in GRAPH_ROLE_ORDER if g in present]
    ordered += sorted(present - set(ordered))
    return ordered


def _labels_for(conn: sqlite3.Connection, iris: list[str]) -> dict[str, str]:
    if not iris:
        return {}
    placeholders = ",".join("?" for _ in iris)
    rows = conn.execute(
        f"""
        SELECT subject, object
        FROM quads
        WHERE predicate = ? AND object_kind = 'literal'
          AND subject IN ({placeholders})
        ORDER BY subject
        """,
        (RDFS_LABEL, *iris),
    ).fetchall()
    labels: dict[str, str] = {}
    for row in rows:
        labels.setdefault(row["subject"], row["object"])
    return labels


def type_overview(path: Path) -> list[dict]:
    """Per graph (role order), the total entity count and every rdf:type
    present with its instance count, sorted by count within the graph --
    the huge types and the singleton types both stay in, no cutoff. One
    grouped query over `quads` for the type/count rollup, one more for
    per-graph entity totals, and one batched rdfs:label lookup for the
    distinct type IRIs found (only the ontology graphs carry labels in
    practice)."""
    conn = _connect(path)
    try:
        graphs = _graph_order(conn)

        type_rows = conn.execute(
            """
            SELECT graph, object AS type_iri, COUNT(*) AS instance_count
            FROM quads
            WHERE predicate = ?
            GROUP BY graph, object
            ORDER BY graph, instance_count DESC, object
            """,
            (RDF_TYPE,),
        ).fetchall()

        entity_rows = conn.execute(
            """
            SELECT graph, COUNT(DISTINCT subject) AS n
            FROM quads
            WHERE subject_kind IN ('uri', 'bnode')
            GROUP BY graph
            """
        ).fetchall()
        entity_totals = {row["graph"]: int(row["n"]) for row in entity_rows}

        type_iris = sorted({row["type_iri"] for row in type_rows})
        labels = _labels_for(conn, type_iris)

        by_graph: dict[str, list[dict]] = {g: [] for g in graphs}
        for row in type_rows:
            iri = row["type_iri"]
            label = labels.get(iri)
            by_graph.setdefault(row["graph"], []).append(
                {
                    "type_iri": iri,
                    "instance_count": int(row["instance_count"]),
                    "label": label,
                    "display": label or _local_name(iri),
                }
            )

        return [
            {
                "graph": g,
                "entity_count": entity_totals.get(g, 0),
                "types": by_graph.get(g, []),
                "type_count": len(by_graph.get(g, [])),
            }
            for g in graphs
        ]
    finally:
        conn.close()


def graph_entity_totals(path: Path) -> list[tuple[str, int]]:
    """Per-graph entity totals only, in role order -- the landing page's
    compact strip doesn't need the full type breakdown, just enough to
    link into it."""
    conn = _connect(path)
    try:
        graphs = _graph_order(conn)
        rows = conn.execute(
            """
            SELECT graph, COUNT(DISTINCT subject) AS n
            FROM quads
            WHERE subject_kind IN ('uri', 'bnode')
            GROUP BY graph
            """
        ).fetchall()
        totals = {row["graph"]: int(row["n"]) for row in rows}
        return [(g, totals.get(g, 0)) for g in graphs]
    finally:
        conn.close()


def label_for_type(path: Path, type_iri: str) -> str | None:
    """Single-IRI rdfs:label lookup for the entity-list page's header."""
    conn = _connect(path)
    try:
        return _labels_for(conn, [type_iri]).get(type_iri)
    finally:
        conn.close()
