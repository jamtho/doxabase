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


def describe_graph_revision_tool(
    db: DoxaBase,
    iri: str,
    graph: str | None = "history",
) -> dict[str, Any]:
    return asdict(db.describe_graph_revision(iri=iri, graph=graph))


def describe_staged_revision_tool(
    db: DoxaBase,
    iri: str,
    graph: str | None = "history",
) -> dict[str, Any]:
    return asdict(db.describe_staged_revision(iri=iri, graph=graph))


def describe_pattern_tool(
    db: DoxaBase,
    iri: str,
    graph: str | None = "patterns",
) -> dict[str, Any]:
    return asdict(db.describe_pattern(iri=iri, graph=graph))


def describe_dataset_tool(
    db: DoxaBase,
    iri: str,
    graph: str | None = "map",
) -> dict[str, Any]:
    return asdict(db.describe_dataset(iri=iri, graph=graph))


def describe_context_slice_tool(
    db: DoxaBase,
    seed_iris: list[str],
    profile: str = "dataset_brief",
    max_triples: int = 500,
    include_trig: bool = False,
) -> dict[str, Any]:
    return asdict(
        db.describe_context_slice(
            seed_iris,
            profile=profile,  # type: ignore[arg-type]
            max_triples=max_triples,
            include_trig=include_trig,
        )
    )


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


def record_pattern_tool(
    db: DoxaBase,
    summary: str,
    pattern_text: str,
    rationale: str,
    pattern_targets: list[str],
    supporting_observations: list[str] | None = None,
    supporting_claims: list[str] | None = None,
    synthesized_at: str | None = None,
    synthesized_by: str | None = None,
    evidence_summary: str | None = None,
    evidence_sources: list[str] | None = None,
    source_path: str | None = None,
    source_section: str | None = None,
    start_line: int | None = None,
    end_line: int | None = None,
    source_kind: str | None = None,
    confidence: str | None = "rc:MediumConfidence",
    pattern_status: str | None = "rc:Tentative",
    pattern_stability: str | None = "rc:EmergingPattern",
    map_implications: list[str] | None = None,
) -> dict[str, Any]:
    result = db.record_pattern(
        summary=summary,
        pattern_text=pattern_text,
        rationale=rationale,
        pattern_targets=pattern_targets,
        supporting_observations=supporting_observations,
        supporting_claims=supporting_claims,
        synthesized_at=synthesized_at,
        synthesized_by=synthesized_by,
        evidence_summary=evidence_summary,
        evidence_sources=evidence_sources,
        source_path=source_path,
        source_section=source_section,
        start_line=start_line,
        end_line=end_line,
        source_kind=source_kind,
        confidence=confidence,
        pattern_status=pattern_status,
        pattern_stability=pattern_stability,
        map_implications=map_implications,
    )
    return asdict(result)


def record_map_dataset_tool(
    db: DoxaBase,
    iri: str,
    label: str | None = None,
    description: str | None = None,
    is_table: bool | None = None,
    columns: list[str] | None = None,
    path_templates: list[str] | None = None,
    row_count_snapshot: int | None = None,
    row_semantics: str | None = None,
    entity_key: str | None = None,
    schema_stability: str | None = None,
    caveats: list[str] | None = None,
    storage_accesses: list[str] | None = None,
    physical_layouts: list[str] | None = None,
    companion_datasets: list[str] | None = None,
    extra_types: list[str] | None = None,
) -> dict[str, Any]:
    result = db.record_map_dataset(
        iri=iri,
        label=label,
        description=description,
        is_table=is_table,
        columns=columns,
        path_templates=path_templates,
        row_count_snapshot=row_count_snapshot,
        row_semantics=row_semantics,
        entity_key=entity_key,
        schema_stability=schema_stability,
        caveats=caveats,
        storage_accesses=storage_accesses,
        physical_layouts=physical_layouts,
        companion_datasets=companion_datasets,
        extra_types=extra_types,
    )
    return asdict(result)


def record_map_column_tool(
    db: DoxaBase,
    iri: str,
    column_name: str,
    table_iri: str | None = None,
    label: str | None = None,
    description: str | None = None,
    physical_type: str | None = None,
    value_type: str | None = None,
    nullable: bool | None = None,
) -> dict[str, Any]:
    result = db.record_map_column(
        iri=iri,
        column_name=column_name,
        table_iri=table_iri,
        label=label,
        description=description,
        physical_type=physical_type,
        value_type=value_type,
        nullable=nullable,
    )
    return asdict(result)


def record_map_caveat_tool(
    db: DoxaBase,
    iri: str,
    description: str,
    label: str | None = None,
    impact: str | None = None,
    severity: str | None = None,
    targets: list[str] | None = None,
) -> dict[str, Any]:
    result = db.record_map_caveat(
        iri=iri,
        description=description,
        label=label,
        impact=impact,
        severity=severity,
        targets=targets,
    )
    return asdict(result)


def record_map_storage_access_tool(
    db: DoxaBase,
    iri: str,
    label: str | None = None,
    description: str | None = None,
    storage_protocol: str | None = None,
    access_mode: str | None = None,
    storage_root: str | None = None,
    endpoint_profile: str | None = None,
    bucket_name: str | None = None,
    key_prefix: str | None = None,
    region: str | None = None,
    path_style_access: bool | None = None,
    credential_reference: str | None = None,
    path_templates: list[str] | None = None,
    datasets: list[str] | None = None,
) -> dict[str, Any]:
    result = db.record_map_storage_access(
        iri=iri,
        label=label,
        description=description,
        storage_protocol=storage_protocol,
        access_mode=access_mode,
        storage_root=storage_root,
        endpoint_profile=endpoint_profile,
        bucket_name=bucket_name,
        key_prefix=key_prefix,
        region=region,
        path_style_access=path_style_access,
        credential_reference=credential_reference,
        path_templates=path_templates,
        datasets=datasets,
    )
    return asdict(result)


def record_map_relationship_tool(
    db: DoxaBase,
    iri: str,
    relationship_type: str,
    label: str | None = None,
    description: str | None = None,
    source_dataset: str | None = None,
    target_dataset: str | None = None,
    from_column: str | None = None,
    to_column: str | None = None,
    identifying_columns: list[str] | None = None,
    source_columns: list[str] | None = None,
    derived_columns: list[str] | None = None,
    declared: bool | None = None,
    referential_integrity: str | None = None,
    derivation_function: str | None = None,
    derivation_properties: list[str] | None = None,
) -> dict[str, Any]:
    result = db.record_map_relationship(
        iri=iri,
        relationship_type=relationship_type,  # type: ignore[arg-type]
        label=label,
        description=description,
        source_dataset=source_dataset,
        target_dataset=target_dataset,
        from_column=from_column,
        to_column=to_column,
        identifying_columns=identifying_columns,
        source_columns=source_columns,
        derived_columns=derived_columns,
        declared=declared,
        referential_integrity=referential_integrity,
        derivation_function=derivation_function,
        derivation_properties=derivation_properties,
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


def export_graph_tool(
    db: DoxaBase,
    path: str,
    graphs: list[str] | None = None,
    format: str = "turtle",
    overwrite: bool = False,
) -> dict[str, Any]:
    resolved_path = _resolve_path(path)
    result = db.export_graph(
        resolved_path,
        graphs=graphs if graphs is not None else ["map"],
        format=format,
        overwrite=overwrite,
    )
    return asdict(result)


def export_trig_tool(
    db: DoxaBase,
    path: str,
    graphs: list[str] | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    resolved_path = _resolve_path(path)
    result = db.export_trig(
        resolved_path,
        graphs=graphs,
        overwrite=overwrite,
    )
    return asdict(result)


def record_graph_revision_tool(
    db: DoxaBase,
    summary: str,
    rationale: str,
    changed_graphs: list[str],
    revision_type: str = "rc:ManualRevision",
    included_graphs: list[str] | None = None,
    revision_iri: str | None = None,
    created_at: str | None = None,
    created_by: str | None = None,
    supporting_observations: list[str] | None = None,
    supporting_claims: list[str] | None = None,
    supporting_patterns: list[str] | None = None,
    evidence: list[str] | None = None,
    export_path: str | None = None,
    graph_counts: dict[str, int] | None = None,
    validation_scope: str | None = None,
    validation_conforms: bool | None = None,
    validation_result_count: int | None = None,
) -> dict[str, Any]:
    result = db.record_graph_revision(
        summary=summary,
        rationale=rationale,
        changed_graphs=changed_graphs,
        revision_type=revision_type,
        included_graphs=included_graphs,
        revision_iri=revision_iri,
        created_at=created_at,
        created_by=created_by,
        supporting_observations=supporting_observations,
        supporting_claims=supporting_claims,
        supporting_patterns=supporting_patterns,
        evidence=evidence,
        export_path=export_path,
        graph_counts=graph_counts,
        validation_scope=validation_scope,
        validation_conforms=validation_conforms,
        validation_result_count=validation_result_count,
    )
    return asdict(result)


def stage_graph_revision_tool(
    db: DoxaBase,
    summary: str,
    rationale: str,
    additions: list[dict[str, str]] | None = None,
    removals: list[dict[str, str]] | None = None,
    stance: str = "rc:CandidateRevision",
    revision_type: str = "rc:StagedRevision",
    included_graphs: list[str] | None = None,
    revision_iri: str | None = None,
    created_at: str | None = None,
    created_by: str | None = None,
    supporting_observations: list[str] | None = None,
    supporting_claims: list[str] | None = None,
    supporting_patterns: list[str] | None = None,
    evidence: list[str] | None = None,
    alternative_to: str | None = None,
    validation_scope: str = "all",
) -> dict[str, Any]:
    result = db.stage_graph_revision(
        summary=summary,
        rationale=rationale,
        additions=additions,
        removals=removals,
        stance=stance,
        revision_type=revision_type,
        included_graphs=included_graphs,
        revision_iri=revision_iri,
        created_at=created_at,
        created_by=created_by,
        supporting_observations=supporting_observations,
        supporting_claims=supporting_claims,
        supporting_patterns=supporting_patterns,
        evidence=evidence,
        alternative_to=alternative_to,
        validation_scope=validation_scope,  # type: ignore[arg-type]
    )
    return asdict(result)


def stage_systematisation_tool(
    db: DoxaBase,
    summary: str,
    intent: str,
    framings: list[dict[str, Any]],
    anchors: list[str] | None = None,
    rationale: str | None = None,
    default_stance: str = "rc:ExploratoryHunch",
    revision_type: str = "rc:StagedRevision",
    included_graphs: list[str] | None = None,
    created_at: str | None = None,
    created_by: str | None = None,
    supporting_observations: list[str] | None = None,
    supporting_claims: list[str] | None = None,
    supporting_patterns: list[str] | None = None,
    evidence: list[str] | None = None,
    alternative_to: str | None = None,
    link_alternatives: bool = True,
    validation_scope: str = "all",
) -> dict[str, Any]:
    result = db.stage_systematisation(
        summary=summary,
        intent=intent,
        framings=framings,
        anchors=anchors,
        rationale=rationale,
        default_stance=default_stance,
        revision_type=revision_type,
        included_graphs=included_graphs,
        created_at=created_at,
        created_by=created_by,
        supporting_observations=supporting_observations,
        supporting_claims=supporting_claims,
        supporting_patterns=supporting_patterns,
        evidence=evidence,
        alternative_to=alternative_to,
        link_alternatives=link_alternatives,
        validation_scope=validation_scope,  # type: ignore[arg-type]
    )
    return asdict(result)


def export_staged_revision_tool(
    db: DoxaBase,
    iri: str,
    path: str,
    format: str = "markdown",
    overwrite: bool = False,
) -> dict[str, Any]:
    resolved_path = _resolve_path(path)
    result = db.export_staged_revision(
        iri=iri,
        path=resolved_path,
        format=format,  # type: ignore[arg-type]
        overwrite=overwrite,
    )
    return asdict(result)


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
