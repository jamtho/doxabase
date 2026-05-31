from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from rdflib import Dataset

from doxybase.agent_docs import get_agent_doc, list_agent_docs
from doxybase.core import DoxyBase, RCG_PREFIX, ROOT

EXAMPLE_FIXTURES = (
    ROOT / "examples" / "manifest-prototype-rc" / "ais.trig",
    ROOT / "examples" / "manifest-prototype-rc" / "polymarket.trig",
)


def list_docs_tool() -> dict[str, Any]:
    return {"docs": list_agent_docs()}


def get_doc_tool(doc_id: str, max_chars: int = 12000) -> dict[str, Any]:
    return get_agent_doc(doc_id, max_chars=max_chars)


def graph_overview_tool(db: DoxyBase, limit: int = 100) -> dict[str, Any]:
    overview = db.graph_overview(limit=limit)
    return {
        "named_graphs": [asdict(graph) for graph in overview.named_graphs],
        "class_counts": _pairs_to_dicts(overview.class_counts, "class"),
        "predicate_counts": _pairs_to_dicts(overview.predicate_counts, "predicate"),
        "key_counts": overview.key_counts,
        "namespaces": overview.namespaces,
    }


def list_entities_tool(
    db: DoxyBase,
    type: str | None = None,
    graph: str | None = "map",
    text: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    result = db.list_entities(type=type, graph=graph, text=text, limit=limit, offset=offset)
    return {
        "entities": [asdict(entity) for entity in result.entities],
        "limit": result.limit,
        "offset": result.offset,
        "count": len(result.entities),
    }


def describe_dataset_tool(
    db: DoxyBase,
    iri: str,
    graph: str | None = "map",
) -> dict[str, Any]:
    return asdict(db.describe_dataset(iri=iri, graph=graph))


def record_observation_tool(
    db: DoxyBase,
    summary: str,
    observation_type: str = "observation",
    observed_asset: str | None = None,
    observed_column: str | None = None,
    observed_at: str | None = None,
    observed_by: str | None = None,
    evidence_summary: str | None = None,
    evidence_sources: list[str] | None = None,
    sample_size: int | None = None,
    row_count: int | None = None,
    null_count: int | None = None,
    distinct_count: int | None = None,
) -> dict[str, Any]:
    result = db.record_observation(
        summary=summary,
        observation_type=observation_type,  # type: ignore[arg-type]
        observed_asset=observed_asset,
        observed_column=observed_column,
        observed_at=observed_at,
        observed_by=observed_by,
        evidence_summary=evidence_summary,
        evidence_sources=evidence_sources,
        sample_size=sample_size,
        row_count=row_count,
        null_count=null_count,
        distinct_count=distinct_count,
    )
    return asdict(result)


def search_tool(
    db: DoxyBase,
    query: str,
    graph: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    result = db.search(query=query, graph=graph, limit=limit, offset=offset)
    return {
        "query": result.query,
        "graph": result.graph,
        "matches": [asdict(match) for match in result.matches],
        "limit": result.limit,
        "offset": result.offset,
        "count": len(result.matches),
    }


def import_trig_tool(
    db: DoxyBase,
    path: str,
    replace: bool = False,
) -> dict[str, Any]:
    resolved_path = _resolve_path(path)
    imported = db.import_trig(resolved_path, replace=replace)
    return {
        "path": str(resolved_path),
        "replace": replace,
        "imported": imported,
        "total_imported": sum(imported.values()),
    }


def load_example_fixtures_tool(db: DoxyBase, replace: bool = False) -> dict[str, Any]:
    results = []
    totals: dict[str, int] = {}
    if replace:
        for graph in _fixture_graph_roles(EXAMPLE_FIXTURES):
            db.clear_graph(graph)
    for fixture in EXAMPLE_FIXTURES:
        imported = db.import_trig(fixture, replace=False)
        for graph, count in imported.items():
            totals[graph] = totals.get(graph, 0) + count
        results.append(
            {
                "path": str(fixture),
                "imported": imported,
            }
        )
    return {
        "replace": replace,
        "fixtures": results,
        "totals": totals,
        "total_imported": sum(totals.values()),
    }


def validate_graph_tool(
    db: DoxyBase,
    scope: str = "map",
    limit_results: int = 100,
) -> dict[str, Any]:
    result = db.validate_graph(scope=scope, limit_results=limit_results)  # type: ignore[arg-type]
    return asdict(result)


def _pairs_to_dicts(pairs: list[tuple[str, int]], key_name: str) -> list[dict[str, Any]]:
    return [{key_name: key, "count": count} for key, count in pairs]


def _resolve_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return ROOT / candidate


def _fixture_graph_roles(fixtures: tuple[Path, ...]) -> list[str]:
    roles: list[str] = []
    for fixture in fixtures:
        dataset = Dataset()
        dataset.parse(fixture, format="trig")
        for context in dataset.graphs():
            if len(context) == 0:
                continue
            identifier = str(context.identifier)
            role = (
                identifier.removeprefix(RCG_PREFIX)
                if identifier.startswith(RCG_PREFIX)
                else identifier
            )
            roles.append(role)
    return list(dict.fromkeys(roles))
