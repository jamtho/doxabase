from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from rdflib import Dataset

from doxabase.agent_docs import get_agent_doc, list_agent_docs
from doxabase.core import DoxaBase, RCG_PREFIX, ROOT

EXAMPLE_FIXTURES = (
    ROOT / "examples" / "manifest-prototype-rc" / "ais.trig",
    ROOT / "examples" / "manifest-prototype-rc" / "polymarket.trig",
)


def list_docs_tool() -> dict[str, Any]:
    return {"docs": list_agent_docs()}


def get_doc_tool(doc_id: str, max_chars: int = 12000) -> dict[str, Any]:
    return get_agent_doc(doc_id, max_chars=max_chars)


def graph_overview_tool(db: DoxaBase, limit: int = 100) -> dict[str, Any]:
    overview = db.graph_overview(limit=limit)
    return {
        "named_graphs": [asdict(graph) for graph in overview.named_graphs],
        "class_counts": _pairs_to_dicts(overview.class_counts, "class"),
        "predicate_counts": _pairs_to_dicts(overview.predicate_counts, "predicate"),
        "key_counts": overview.key_counts,
        "namespaces": overview.namespaces,
    }


def list_entities_tool(
    db: DoxaBase,
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


def describe_resource_tool(
    db: DoxaBase,
    iri: str,
    graph: str | None = None,
    include_incoming: bool = True,
    limit: int = 100,
) -> dict[str, Any]:
    result = db.describe_resource(
        iri=iri,
        graph=graph,
        include_incoming=include_incoming,
        limit=limit,
    )
    return asdict(result)


def describe_dataset_tool(
    db: DoxaBase,
    iri: str,
    graph: str | None = "map",
) -> dict[str, Any]:
    return asdict(db.describe_dataset(iri=iri, graph=graph))


def record_observation_tool(
    db: DoxaBase,
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


def record_claim_observation_tool(
    db: DoxaBase,
    summary: str,
    claim_text: str,
    claim_kind: str,
    claim_targets: list[str],
    observed_asset: str | None = None,
    observed_column: str | None = None,
    observed_at: str | None = None,
    observed_by: str | None = None,
    evidence_summary: str | None = None,
    evidence_sources: list[str] | None = None,
    source_path: str | None = None,
    source_section: str | None = None,
    start_line: int | None = None,
    end_line: int | None = None,
    source_kind: str | None = None,
    confidence: str | None = "rc:MediumConfidence",
    observation_status: str | None = "rc:Tentative",
    proposed_assertions: list[str] | None = None,
) -> dict[str, Any]:
    result = db.record_claim_observation(
        summary=summary,
        claim_text=claim_text,
        claim_kind=claim_kind,
        claim_targets=claim_targets,
        observed_asset=observed_asset,
        observed_column=observed_column,
        observed_at=observed_at,
        observed_by=observed_by,
        evidence_summary=evidence_summary,
        evidence_sources=evidence_sources,
        source_path=source_path,
        source_section=source_section,
        start_line=start_line,
        end_line=end_line,
        source_kind=source_kind,
        confidence=confidence,
        observation_status=observation_status,
        proposed_assertions=proposed_assertions,
    )
    return asdict(result)


def search_tool(
    db: DoxaBase,
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
    db: DoxaBase,
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


def load_example_fixtures_tool(db: DoxaBase, replace: bool = False) -> dict[str, Any]:
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
    db: DoxaBase,
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
