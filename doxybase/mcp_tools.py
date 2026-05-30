from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from doxybase.agent_docs import get_agent_doc, list_agent_docs
from doxybase.core import DoxyBase, ROOT

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
    for fixture in EXAMPLE_FIXTURES:
        imported = db.import_trig(fixture, replace=replace)
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
