from __future__ import annotations

from pathlib import Path
from typing import Any

from rdflib import Dataset

from doxabase.agent_docs import get_agent_doc, list_agent_docs
from doxabase.core import DoxaBase, RCG_PREFIX, ROOT, to_dict

EXAMPLE_FIXTURES = (
    ROOT / "examples" / "manifest-prototype-rc" / "ais.trig",
    ROOT / "examples" / "manifest-prototype-rc" / "polymarket.trig",
)


def list_docs_tool() -> dict[str, Any]:
    return {"docs": list_agent_docs()}


def get_doc_tool(
    doc_id: str,
    max_chars: int = 12000,
    start_char: int = 0,
    section: str | None = None,
) -> dict[str, Any]:
    return get_agent_doc(
        doc_id,
        max_chars=max_chars,
        start_char=start_char,
        section=section,
    )


def graph_overview_tool(db: DoxaBase, limit: int = 100) -> dict[str, Any]:
    overview = db.graph_overview(limit=limit)
    return {
        "named_graphs": [to_dict(graph) for graph in overview.named_graphs],
        "class_counts": _pairs_to_dicts(overview.class_counts, "class"),
        "predicate_counts": _pairs_to_dicts(overview.predicate_counts, "predicate"),
        "key_counts": overview.key_counts,
        "namespaces": overview.namespaces,
    }


def scan_sensitive_literals_tool(
    db: DoxaBase,
    graphs: list[str] | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    result = db.scan_sensitive_literals(graphs=graphs, limit=limit)
    return to_dict(result)


def export_preflight_tool(
    db: DoxaBase,
    export_kind: str = "handoff_bundle",
    graphs: list[str] | str | None = None,
    revision_iris: list[str] | None = None,
    snapshot_graph_roles: list[str] | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    result = db.export_preflight(
        export_kind=export_kind,  # type: ignore[arg-type]
        graphs=graphs,
        revision_iris=revision_iris,
        snapshot_graph_roles=snapshot_graph_roles,
        limit=limit,
    )
    return to_dict(result)


def project_brief_tool(
    db: DoxaBase,
    limit: int = 20,
    profile_candidate_limit: int = 2,
) -> dict[str, Any]:
    """Return a read-only orientation brief over active project queues."""

    return to_dict(
        db.project_brief(
            limit=limit,
            profile_candidate_limit=profile_candidate_limit,
        )
    )


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
        "entities": [to_dict(entity) for entity in result.entities],
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
    outgoing_offset: int = 0,
    incoming_offset: int = 0,
    include_blank_node_closure: bool = False,
    blank_node_depth: int = 2,
    blank_node_limit: int = 100,
) -> dict[str, Any]:
    result = db.describe_resource(
        iri=iri,
        graph=graph,
        include_incoming=include_incoming,
        limit=limit,
        outgoing_offset=outgoing_offset,
        incoming_offset=incoming_offset,
        include_blank_node_closure=include_blank_node_closure,
        blank_node_depth=blank_node_depth,
        blank_node_limit=blank_node_limit,
    )
    return to_dict(result)


def describe_assertion_support_tool(
    db: DoxaBase,
    subject: str,
    predicate: str,
    object: str | None = None,
    graph: str | None = "map",
    object_kind: str = "auto",
    object_datatype: str | None = None,
    object_lang: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    result = db.describe_assertion_support(
        subject=subject,
        predicate=predicate,
        object=object,
        graph=graph,
        object_kind=object_kind,  # type: ignore[arg-type]
        object_datatype=object_datatype,
        object_lang=object_lang,
        limit=limit,
    )
    return to_dict(result)


def describe_graph_revision_tool(
    db: DoxaBase,
    iri: str,
    graph: str | None = "history",
) -> dict[str, Any]:
    return to_dict(db.describe_graph_revision(iri=iri, graph=graph))


def describe_revision_snapshot_evidence_tool(
    db: DoxaBase,
    iri: str,
    graph: str | None = "history",
) -> dict[str, Any]:
    return to_dict(db.describe_revision_snapshot_evidence(iri=iri, graph=graph))


def describe_revision_graph_snapshot_tool(
    db: DoxaBase,
    iri: str,
    graph_role: str,
    graph: str | None = "history",
    include_triples: bool = False,
    max_triples: int = 500,
) -> dict[str, Any]:
    return to_dict(
        db.describe_revision_graph_snapshot(
            iri=iri,
            graph_role=graph_role,
            graph=graph,
            include_triples=include_triples,
            max_triples=max_triples,
        )
    )


def describe_applied_revision_diff_tool(
    db: DoxaBase,
    iri: str,
    graph: str | None = "history",
    include_triples: bool = False,
    max_triples: int = 500,
) -> dict[str, Any]:
    return to_dict(
        db.describe_applied_revision_diff(
            iri=iri,
            graph=graph,
            include_triples=include_triples,
            max_triples=max_triples,
        )
    )


def list_graph_revisions_tool(
    db: DoxaBase,
    revision_type: str | None = None,
    graph: str | None = "history",
    include_apply_checks: bool = False,
    drift_detail: str = "summary",
    record_kind: str | None = None,
    application_status: str | None = None,
    staged_validation_status: str | None = None,
    stale_resolution_state: str | None = None,
    current_staged_work_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    return to_dict(
        db.list_graph_revisions(
            revision_type=revision_type,
            graph=graph,
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,  # type: ignore[arg-type]
            record_kind=record_kind,
            application_status=application_status,
            staged_validation_status=staged_validation_status,  # type: ignore[arg-type]
            stale_resolution_state=stale_resolution_state,
            current_staged_work_only=current_staged_work_only,
            limit=limit,
            offset=offset,
        )
    )


def describe_revision_lineage_tool(
    db: DoxaBase,
    iri: str,
    graph: str | None = "history",
    include_apply_checks: bool = True,
    drift_detail: str = "summary",
) -> dict[str, Any]:
    return to_dict(
        db.describe_revision_lineage(
            iri=iri,
            graph=graph,
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,  # type: ignore[arg-type]
        )
    )


def list_resource_revisions_tool(
    db: DoxaBase,
    resource_iri: str,
    graph: str | None = "history",
    include_patch_mentions: bool = True,
    include_apply_checks: bool = True,
    drift_detail: str = "summary",
    current_staged_work_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    return to_dict(
        db.list_resource_revisions(
            resource_iri=resource_iri,
            graph=graph,
            include_patch_mentions=include_patch_mentions,
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,  # type: ignore[arg-type]
            current_staged_work_only=current_staged_work_only,
            limit=limit,
            offset=offset,
        )
    )


def describe_resource_revision_lineage_tool(
    db: DoxaBase,
    resource_iri: str,
    revision_iri: str,
    graph: str | None = "history",
    include_patch_mentions: bool = True,
    include_apply_checks: bool = True,
    drift_detail: str = "summary",
    include_applied_diff: bool = True,
    include_triples: bool = False,
    max_triples: int = 100,
) -> dict[str, Any]:
    return to_dict(
        db.describe_resource_revision_lineage(
            resource_iri=resource_iri,
            revision_iri=revision_iri,
            graph=graph,
            include_patch_mentions=include_patch_mentions,
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,  # type: ignore[arg-type]
            include_applied_diff=include_applied_diff,
            include_triples=include_triples,
            max_triples=max_triples,
        )
    )


def describe_staged_revision_tool(
    db: DoxaBase,
    iri: str,
    graph: str | None = "history",
    include_current_apply_check: bool = False,
) -> dict[str, Any]:
    return to_dict(
        db.describe_staged_revision(
            iri=iri,
            graph=graph,
            include_current_apply_check=include_current_apply_check,
        )
    )


def check_staged_revision_apply_tool(
    db: DoxaBase,
    iri: str,
    validation_scope: str | None = None,
) -> dict[str, Any]:
    return to_dict(
        db.check_staged_revision_apply(
            iri=iri,
            validation_scope=validation_scope,  # type: ignore[arg-type]
        )
    )


def draft_staged_revision_rebase_tool(
    db: DoxaBase,
    iri: str,
    validation_scope: str | None = None,
) -> dict[str, Any]:
    return to_dict(
        db.draft_staged_revision_rebase(
            iri=iri,
            validation_scope=validation_scope,  # type: ignore[arg-type]
        )
    )


def plan_staged_revision_recovery_tool(
    db: DoxaBase,
    revision_iris: list[str] | None = None,
    current_staged_work_only: bool = True,
    include_drafts: bool = True,
    validation_scope: str | None = None,
    drift_detail: str = "summary",
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    return to_dict(
        db.plan_staged_revision_recovery(
            revision_iris=revision_iris,
            current_staged_work_only=current_staged_work_only,
            include_drafts=include_drafts,
            validation_scope=validation_scope,  # type: ignore[arg-type]
            drift_detail=drift_detail,  # type: ignore[arg-type]
            limit=limit,
            offset=offset,
        )
    )


def describe_pattern_tool(
    db: DoxaBase,
    iri: str,
    graph: str | None = "patterns",
) -> dict[str, Any]:
    return to_dict(db.describe_pattern(iri=iri, graph=graph))


def describe_dataset_tool(
    db: DoxaBase,
    iri: str,
    graph: str | None = "map",
) -> dict[str, Any]:
    return to_dict(db.describe_dataset(iri=iri, graph=graph))


def describe_profile_run_tool(
    db: DoxaBase,
    dataset_iri: str,
    evidence_iri: str,
    graph: str | None = "map",
    limit: int | None = None,
) -> dict[str, Any]:
    return to_dict(
        db.describe_profile_run(
            dataset_iri=dataset_iri,
            evidence_iri=evidence_iri,
            graph=graph,
            limit=limit,
        )
    )


def draft_profile_map_updates_tool(
    db: DoxaBase,
    dataset_iri: str,
    evidence_iri: str,
    graph: str | None = "map",
) -> dict[str, Any]:
    return to_dict(
        db.draft_profile_map_updates(
            dataset_iri=dataset_iri,
            evidence_iri=evidence_iri,
            graph=graph,
        )
    )


def stage_profile_map_updates_tool(
    db: DoxaBase,
    dataset_iri: str,
    evidence_iri: str,
    accepted_recommendation_indexes: list[int],
    graph: str = "map",
    allow_sampled_row_count_updates: bool = False,
    summary: str | None = None,
    rationale: str | None = None,
    created_at: str | None = None,
    created_by: str | None = None,
    supporting_claims: list[str] | None = None,
    supporting_patterns: list[str] | None = None,
    revision_anchors: list[str] | None = None,
    validation_scope: str = "all",
) -> dict[str, Any]:
    return to_dict(
        db.stage_profile_map_updates(
            dataset_iri=dataset_iri,
            evidence_iri=evidence_iri,
            accepted_recommendation_indexes=accepted_recommendation_indexes,
            graph=graph,  # type: ignore[arg-type]
            allow_sampled_row_count_updates=allow_sampled_row_count_updates,
            summary=summary,
            rationale=rationale,
            created_at=created_at,
            created_by=created_by,
            supporting_claims=supporting_claims,
            supporting_patterns=supporting_patterns,
            revision_anchors=revision_anchors,
            validation_scope=validation_scope,  # type: ignore[arg-type]
        )
    )


def describe_query_context_tool(
    db: DoxaBase,
    iri: str,
    graph: str | None = "map",
) -> dict[str, Any]:
    return to_dict(db.describe_query_context(iri=iri, graph=graph))


def draft_query_plan_tool(
    db: DoxaBase,
    iri: str,
    graph: str | None = "map",
    engine: str = "duckdb",
    candidate_index: int | None = None,
    storage_access_iri: str | None = None,
    physical_layout_iri: str | None = None,
    allow_context_blocked_candidate: bool = False,
) -> dict[str, Any]:
    return to_dict(
        db.draft_query_plan(
            iri=iri,
            graph=graph,
            engine=engine,
            candidate_index=candidate_index,
            storage_access_iri=storage_access_iri,
            physical_layout_iri=physical_layout_iri,
            allow_context_blocked_candidate=allow_context_blocked_candidate,
        )
    )


def describe_context_slice_tool(
    db: DoxaBase,
    seed_iris: list[str],
    profile: str = "dataset_brief",
    max_triples: int = 500,
    include_trig: bool = False,
) -> dict[str, Any]:
    return to_dict(
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
    observed_column_name: str | None = None,
    observed_at: str | None = None,
    observed_by: str | None = None,
    evidence_summary: str | None = None,
    evidence_sources: list[str] | None = None,
    sample_size: int | None = None,
    sample_scope: str | None = None,
    sample_method: str | None = None,
    row_count: int | None = None,
    null_count: int | None = None,
    distinct_count: int | None = None,
    value_frequencies: list[dict[str, Any]] | None = None,
    profile_metrics: list[dict[str, Any]] | None = None,
    observed_physical_type: str | None = None,
    observed_value_type: str | None = None,
) -> dict[str, Any]:
    result = db.record_observation(
        summary=summary,
        observation_type=observation_type,  # type: ignore[arg-type]
        observed_asset=observed_asset,
        observed_column=observed_column,
        observed_column_name=observed_column_name,
        observed_at=observed_at,
        observed_by=observed_by,
        evidence_summary=evidence_summary,
        evidence_sources=evidence_sources,
        sample_size=sample_size,
        sample_scope=sample_scope,
        sample_method=sample_method,
        row_count=row_count,
        null_count=null_count,
        distinct_count=distinct_count,
        value_frequencies=value_frequencies,
        profile_metrics=profile_metrics,
        observed_physical_type=observed_physical_type,
        observed_value_type=observed_value_type,
    )
    return to_dict(result)


def record_query_result_tool(
    db: DoxaBase,
    summary: str,
    observed_asset: str | None = None,
    observed_at: str | None = None,
    observed_by: str | None = None,
    execution_status: str = "succeeded",
    engine: str | None = None,
    query_source_path: str | None = None,
    query_source_section: str | None = None,
    start_line: int | None = None,
    end_line: int | None = None,
    query_hash: str | None = None,
    result_sources: list[str] | None = None,
    evidence_summary: str | None = None,
    failure_summary: str | None = None,
    sample_size: int | None = None,
    sample_scope: str | None = None,
    sample_method: str | None = None,
    row_count: int | None = None,
    null_count: int | None = None,
    distinct_count: int | None = None,
    value_frequencies: list[dict[str, Any]] | None = None,
    profile_metrics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    result = db.record_query_result(
        summary=summary,
        observed_asset=observed_asset,
        observed_at=observed_at,
        observed_by=observed_by,
        execution_status=execution_status,
        engine=engine,
        query_source_path=query_source_path,
        query_source_section=query_source_section,
        start_line=start_line,
        end_line=end_line,
        query_hash=query_hash,
        result_sources=result_sources,
        evidence_summary=evidence_summary,
        failure_summary=failure_summary,
        sample_size=sample_size,
        sample_scope=sample_scope,
        sample_method=sample_method,
        row_count=row_count,
        null_count=null_count,
        distinct_count=distinct_count,
        value_frequencies=value_frequencies,
        profile_metrics=profile_metrics,
    )
    return to_dict(result)


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
    return to_dict(result)


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
    evidence_iri: str | None = None,
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
        evidence_iri=evidence_iri,
    )
    return to_dict(result)


def record_dataset_profile_tool(
    db: DoxaBase,
    dataset_iri: str,
    summary: str,
    observed_at: str | None = None,
    observed_by: str | None = None,
    evidence_summary: str | None = None,
    evidence_sources: list[str] | None = None,
    sample_size: int | None = None,
    sample_scope: str | None = None,
    sample_method: str | None = None,
    row_count: int | None = None,
    null_count: int | None = None,
    distinct_count: int | None = None,
    value_frequencies: list[dict[str, Any]] | None = None,
    profile_metrics: list[dict[str, Any]] | None = None,
    update_map_snapshot: bool = True,
    allow_sampled_row_count_snapshot: bool = False,
    map_label: str | None = None,
    map_description: str | None = None,
    is_table: bool | None = None,
    pattern_summary: str | None = None,
    pattern_text: str | None = None,
    pattern_rationale: str | None = None,
    pattern_confidence: str | None = "rc:MediumConfidence",
    pattern_status: str | None = "rc:Tentative",
    pattern_stability: str | None = "rc:EmergingPattern",
    pattern_map_implications: list[str] | None = None,
) -> dict[str, Any]:
    result = db.record_dataset_profile(
        dataset_iri=dataset_iri,
        summary=summary,
        observed_at=observed_at,
        observed_by=observed_by,
        evidence_summary=evidence_summary,
        evidence_sources=evidence_sources,
        sample_size=sample_size,
        sample_scope=sample_scope,
        sample_method=sample_method,
        row_count=row_count,
        null_count=null_count,
        distinct_count=distinct_count,
        value_frequencies=value_frequencies,
        profile_metrics=profile_metrics,
        update_map_snapshot=update_map_snapshot,
        allow_sampled_row_count_snapshot=allow_sampled_row_count_snapshot,
        map_label=map_label,
        map_description=map_description,
        is_table=is_table,
        pattern_summary=pattern_summary,
        pattern_text=pattern_text,
        pattern_rationale=pattern_rationale,
        pattern_confidence=pattern_confidence,
        pattern_status=pattern_status,
        pattern_stability=pattern_stability,
        pattern_map_implications=pattern_map_implications,
    )
    return to_dict(result)


def record_profile_bundle_tool(
    db: DoxaBase,
    dataset_iri: str,
    dataset_summary: str,
    column_profiles: list[dict[str, Any]] | None = None,
    observed_at: str | None = None,
    observed_by: str | None = None,
    evidence_summary: str | None = None,
    evidence_sources: list[str] | None = None,
    sample_size: int | None = None,
    sample_scope: str | None = None,
    sample_method: str | None = None,
    row_count: int | None = None,
    null_count: int | None = None,
    distinct_count: int | None = None,
    value_frequencies: list[dict[str, Any]] | None = None,
    profile_metrics: list[dict[str, Any]] | None = None,
    update_map_snapshot: bool = True,
    allow_sampled_row_count_snapshot: bool = False,
    map_label: str | None = None,
    map_description: str | None = None,
    is_table: bool | None = None,
    pattern_summary: str | None = None,
    pattern_text: str | None = None,
    pattern_rationale: str | None = None,
    pattern_confidence: str | None = "rc:MediumConfidence",
    pattern_status: str | None = "rc:Tentative",
    pattern_stability: str | None = "rc:EmergingPattern",
    pattern_map_implications: list[str] | None = None,
    pattern_support_scope: str = "dataset_profile",
    shared_evidence_iri: str | None = None,
    column_defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = db.record_profile_bundle(
        dataset_iri=dataset_iri,
        dataset_summary=dataset_summary,
        column_profiles=column_profiles,
        observed_at=observed_at,
        observed_by=observed_by,
        evidence_summary=evidence_summary,
        evidence_sources=evidence_sources,
        sample_size=sample_size,
        sample_scope=sample_scope,
        sample_method=sample_method,
        row_count=row_count,
        null_count=null_count,
        distinct_count=distinct_count,
        value_frequencies=value_frequencies,
        profile_metrics=profile_metrics,
        update_map_snapshot=update_map_snapshot,
        allow_sampled_row_count_snapshot=allow_sampled_row_count_snapshot,
        map_label=map_label,
        map_description=map_description,
        is_table=is_table,
        pattern_summary=pattern_summary,
        pattern_text=pattern_text,
        pattern_rationale=pattern_rationale,
        pattern_confidence=pattern_confidence,
        pattern_status=pattern_status,
        pattern_stability=pattern_stability,
        pattern_map_implications=pattern_map_implications,
        pattern_support_scope=pattern_support_scope,
        shared_evidence_iri=shared_evidence_iri,
        column_defaults=column_defaults,
    )
    return to_dict(result)


def record_column_profile_tool(
    db: DoxaBase,
    column_iri: str,
    column_name: str,
    summary: str,
    table_iri: str | None = None,
    observed_at: str | None = None,
    observed_by: str | None = None,
    evidence_summary: str | None = None,
    evidence_sources: list[str] | None = None,
    sample_size: int | None = None,
    sample_scope: str | None = None,
    sample_method: str | None = None,
    row_count: int | None = None,
    null_count: int | None = None,
    distinct_count: int | None = None,
    value_frequencies: list[dict[str, Any]] | None = None,
    profile_metrics: list[dict[str, Any]] | None = None,
    update_map_column: bool = True,
    map_label: str | None = None,
    map_description: str | None = None,
    physical_type: str | None = None,
    value_type: str | None = None,
    nullable: bool | None = None,
    pattern_summary: str | None = None,
    pattern_text: str | None = None,
    pattern_rationale: str | None = None,
    pattern_confidence: str | None = "rc:MediumConfidence",
    pattern_status: str | None = "rc:Tentative",
    pattern_stability: str | None = "rc:EmergingPattern",
    pattern_map_implications: list[str] | None = None,
) -> dict[str, Any]:
    result = db.record_column_profile(
        column_iri=column_iri,
        column_name=column_name,
        summary=summary,
        table_iri=table_iri,
        observed_at=observed_at,
        observed_by=observed_by,
        evidence_summary=evidence_summary,
        evidence_sources=evidence_sources,
        sample_size=sample_size,
        sample_scope=sample_scope,
        sample_method=sample_method,
        row_count=row_count,
        null_count=null_count,
        distinct_count=distinct_count,
        value_frequencies=value_frequencies,
        profile_metrics=profile_metrics,
        update_map_column=update_map_column,
        map_label=map_label,
        map_description=map_description,
        physical_type=physical_type,
        value_type=value_type,
        nullable=nullable,
        pattern_summary=pattern_summary,
        pattern_text=pattern_text,
        pattern_rationale=pattern_rationale,
        pattern_confidence=pattern_confidence,
        pattern_status=pattern_status,
        pattern_stability=pattern_stability,
        pattern_map_implications=pattern_map_implications,
    )
    return to_dict(result)


def record_claim_reconsideration_tool(
    db: DoxaBase,
    newer_claim: str,
    older_claim: str,
    relation: str,
    rationale: str,
    summary: str | None = None,
    reconsidered_at: str | None = None,
    reconsidered_by: str | None = None,
    evidence_summary: str | None = None,
    evidence_sources: list[str] | None = None,
    source_path: str | None = None,
    source_section: str | None = None,
    start_line: int | None = None,
    end_line: int | None = None,
    source_kind: str | None = None,
    older_claim_status: str | None = None,
) -> dict[str, Any]:
    result = db.record_claim_reconsideration(
        newer_claim=newer_claim,
        older_claim=older_claim,
        relation=relation,
        rationale=rationale,
        summary=summary,
        reconsidered_at=reconsidered_at,
        reconsidered_by=reconsidered_by,
        evidence_summary=evidence_summary,
        evidence_sources=evidence_sources,
        source_path=source_path,
        source_section=source_section,
        start_line=start_line,
        end_line=end_line,
        source_kind=source_kind,
        older_claim_status=older_claim_status,
    )
    return to_dict(result)


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
    layout_verification_status: str | None = None,
    layout_verification_note: str | None = None,
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
        layout_verification_status=layout_verification_status,
        layout_verification_note=layout_verification_note,
        caveats=caveats,
        storage_accesses=storage_accesses,
        physical_layouts=physical_layouts,
        companion_datasets=companion_datasets,
        extra_types=extra_types,
    )
    return to_dict(result)


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
    return to_dict(result)


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
    return to_dict(result)


def record_map_storage_access_tool(
    db: DoxaBase,
    iri: str,
    label: str | None = None,
    description: str | None = None,
    storage_protocol: str | None = None,
    access_mode: str | None = None,
    location_kind: str | None = None,
    storage_root: str | None = None,
    endpoint_profile: str | None = None,
    bucket_name: str | None = None,
    key_prefix: str | None = None,
    region: str | None = None,
    path_style_access: bool | None = None,
    credential_reference: str | None = None,
    path_templates: list[str] | None = None,
    layout_verification_status: str | None = None,
    layout_verification_note: str | None = None,
    datasets: list[str] | None = None,
) -> dict[str, Any]:
    result = db.record_map_storage_access(
        iri=iri,
        label=label,
        description=description,
        storage_protocol=storage_protocol,
        access_mode=access_mode,
        location_kind=location_kind,
        storage_root=storage_root,
        endpoint_profile=endpoint_profile,
        bucket_name=bucket_name,
        key_prefix=key_prefix,
        region=region,
        path_style_access=path_style_access,
        credential_reference=credential_reference,
        path_templates=path_templates,
        layout_verification_status=layout_verification_status,
        layout_verification_note=layout_verification_note,
        datasets=datasets,
    )
    return to_dict(result)


def record_map_physical_layout_tool(
    db: DoxaBase,
    iri: str,
    label: str | None = None,
    description: str | None = None,
    file_format: str | None = None,
    compression_codec: str | None = None,
    layout_verification_status: str | None = None,
    layout_verification_note: str | None = None,
    datasets: list[str] | None = None,
) -> dict[str, Any]:
    result = db.record_map_physical_layout(
        iri=iri,
        label=label,
        description=description,
        file_format=file_format,
        compression_codec=compression_codec,
        layout_verification_status=layout_verification_status,
        layout_verification_note=layout_verification_note,
        datasets=datasets,
    )
    return to_dict(result)


def record_map_partition_scheme_tool(
    db: DoxaBase,
    iri: str,
    label: str | None = None,
    description: str | None = None,
    partition_columns: list[str] | None = None,
    granularity: str | None = None,
    path_template: str | None = None,
    redundant_partition_key: str | None = None,
    layout_verification_status: str | None = None,
    layout_verification_note: str | None = None,
    datasets: list[str] | None = None,
) -> dict[str, Any]:
    result = db.record_map_partition_scheme(
        iri=iri,
        label=label,
        description=description,
        partition_columns=partition_columns,
        granularity=granularity,
        path_template=path_template,
        redundant_partition_key=redundant_partition_key,
        layout_verification_status=layout_verification_status,
        layout_verification_note=layout_verification_note,
        datasets=datasets,
    )
    return to_dict(result)


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
    group_by_columns: list[str] | None = None,
    aggregated_columns: list[dict[str, Any]] | None = None,
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
        group_by_columns=group_by_columns,
        aggregated_columns=aggregated_columns,
        declared=declared,
        referential_integrity=referential_integrity,
        derivation_function=derivation_function,
        derivation_properties=derivation_properties,
    )
    return to_dict(result)


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
        "matches": [to_dict(match) for match in result.matches],
        "limit": result.limit,
        "offset": result.offset,
        "count": len(result.matches),
        "scope_hint": (
            to_dict(result.scope_hint) if result.scope_hint is not None else None
        ),
        "suggested_next_actions": [
            to_dict(action) for action in result.suggested_next_actions
        ],
        "suggested_next_calls": list(result.suggested_next_calls),
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


def export_revision_snapshots_tool(
    db: DoxaBase,
    path: str,
    revision_iris: list[str] | None = None,
    graph_roles: list[str] | None = None,
    overwrite: bool = False,
    fail_on_sensitive: bool = False,
) -> dict[str, Any]:
    resolved_path = _resolve_path(path)
    result = db.export_revision_snapshots(
        resolved_path,
        revision_iris=revision_iris,
        graph_roles=graph_roles,
        overwrite=overwrite,
        fail_on_sensitive=fail_on_sensitive,
    )
    return to_dict(result)


def export_handoff_bundle_tool(
    db: DoxaBase,
    trig_path: str,
    revision_snapshot_path: str,
    manifest_path: str | None = None,
    graphs: list[str] | None = None,
    revision_iris: list[str] | None = None,
    snapshot_graph_roles: list[str] | None = None,
    overwrite: bool = False,
    fail_on_sensitive: bool = False,
) -> dict[str, Any]:
    resolved_trig_path = _resolve_path(trig_path)
    resolved_snapshot_path = _resolve_path(revision_snapshot_path)
    resolved_manifest_path = (
        _resolve_path(manifest_path) if manifest_path is not None else None
    )
    result = db.export_handoff_bundle(
        trig_path=resolved_trig_path,
        revision_snapshot_path=resolved_snapshot_path,
        manifest_path=resolved_manifest_path,
        graphs=graphs,
        revision_iris=revision_iris,
        snapshot_graph_roles=snapshot_graph_roles,
        overwrite=overwrite,
        fail_on_sensitive=fail_on_sensitive,
    )
    return to_dict(result)


def import_revision_snapshots_tool(
    db: DoxaBase,
    path: str,
    replace: bool = False,
) -> dict[str, Any]:
    resolved_path = _resolve_path(path)
    result = db.import_revision_snapshots(resolved_path, replace=replace)
    return to_dict(result)


def export_graph_tool(
    db: DoxaBase,
    path: str,
    graphs: list[str] | None = None,
    format: str = "turtle",
    overwrite: bool = False,
    fail_on_sensitive: bool = False,
) -> dict[str, Any]:
    resolved_path = _resolve_path(path)
    result = db.export_graph(
        resolved_path,
        graphs=graphs if graphs is not None else ["map"],
        format=format,
        overwrite=overwrite,
        fail_on_sensitive=fail_on_sensitive,
    )
    return to_dict(result)


def replace_graph_triples_tool(
    db: DoxaBase,
    graph: str,
    removals: str | None = None,
    additions: str | None = None,
    format: str = "turtle",
    expected_count: int | None = None,
    allow_count_change: bool = False,
) -> dict[str, Any]:
    result = db.replace_graph_triples(
        graph,
        removals=removals,
        additions=additions,
        format=format,
        expected_count=expected_count,
        allow_count_change=allow_count_change,
    )
    return to_dict(result)


def export_trig_tool(
    db: DoxaBase,
    path: str,
    graphs: list[str] | None = None,
    overwrite: bool = False,
    fail_on_sensitive: bool = False,
) -> dict[str, Any]:
    resolved_path = _resolve_path(path)
    result = db.export_trig(
        resolved_path,
        graphs=graphs,
        overwrite=overwrite,
        fail_on_sensitive=fail_on_sensitive,
    )
    return to_dict(result)


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
    revision_anchors: list[str] | None = None,
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
        revision_anchors=revision_anchors,
        evidence=evidence,
        export_path=export_path,
        graph_counts=graph_counts,
        validation_scope=validation_scope,
        validation_conforms=validation_conforms,
        validation_result_count=validation_result_count,
    )
    return to_dict(result)


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
    revision_anchors: list[str] | None = None,
    evidence: list[str] | None = None,
    alternative_to: str | None = None,
    restages_revision: str | None = None,
    review_note: str | None = None,
    review_recommendation: str | None = None,
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
        revision_anchors=revision_anchors,
        evidence=evidence,
        alternative_to=alternative_to,
        restages_revision=restages_revision,
        review_note=review_note,
        review_recommendation=review_recommendation,
        validation_scope=validation_scope,  # type: ignore[arg-type]
    )
    return to_dict(result)


def restage_staged_revision_tool(
    db: DoxaBase,
    iri: str,
    summary: str | None = None,
    rationale: str | None = None,
    created_at: str | None = None,
    created_by: str | None = None,
    validation_scope: str | None = None,
) -> dict[str, Any]:
    result = db.restage_staged_revision(
        iri=iri,
        summary=summary,
        rationale=rationale,
        created_at=created_at,
        created_by=created_by,
        validation_scope=validation_scope,  # type: ignore[arg-type]
    )
    return to_dict(result)


def restage_staged_revisions_tool(
    db: DoxaBase,
    revision_iris: list[str],
    path: str | None = None,
    title: str | None = None,
    executive_summary: str | None = None,
    format: str = "markdown",
    overwrite: bool = False,
    created_at: str | None = None,
    created_by: str | None = None,
    validation_scope: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    resolved_path = _resolve_path(path) if path is not None else None
    result = db.restage_staged_revisions(
        revision_iris=revision_iris,
        path=resolved_path,
        title=title,
        executive_summary=executive_summary,
        format=format,  # type: ignore[arg-type]
        overwrite=overwrite,
        created_at=created_at,
        created_by=created_by,
        validation_scope=validation_scope,  # type: ignore[arg-type]
        dry_run=dry_run,
    )
    return to_dict(result)


def draft_map_assertion_change_tool(
    db: DoxaBase,
    subject: str,
    predicate: str,
    object: str | None,
    rationale: str,
    change_kind: str = "replace",
    graph: str = "map",
    object_kind: str = "auto",
    object_datatype: str | None = None,
    object_lang: str | None = None,
    summary: str | None = None,
    stance: str = "rc:CandidateRevision",
    revision_type: str = "rc:StagedRevision",
    included_graphs: list[str] | None = None,
    revision_iri: str | None = None,
    created_at: str | None = None,
    created_by: str | None = None,
    supporting_observations: list[str] | None = None,
    supporting_claims: list[str] | None = None,
    supporting_patterns: list[str] | None = None,
    revision_anchors: list[str] | None = None,
    evidence: list[str] | None = None,
    alternative_to: str | None = None,
    restages_revision: str | None = None,
    review_note: str | None = None,
    review_recommendation: str | None = None,
    validation_scope: str = "all",
    limit: int = 20,
) -> dict[str, Any]:
    result = db.draft_map_assertion_change(
        subject=subject,
        predicate=predicate,
        object=object,
        rationale=rationale,
        change_kind=change_kind,  # type: ignore[arg-type]
        graph=graph,  # type: ignore[arg-type]
        object_kind=object_kind,  # type: ignore[arg-type]
        object_datatype=object_datatype,
        object_lang=object_lang,
        summary=summary,
        stance=stance,
        revision_type=revision_type,
        included_graphs=included_graphs,
        revision_iri=revision_iri,
        created_at=created_at,
        created_by=created_by,
        supporting_observations=supporting_observations,
        supporting_claims=supporting_claims,
        supporting_patterns=supporting_patterns,
        revision_anchors=revision_anchors,
        evidence=evidence,
        alternative_to=alternative_to,
        restages_revision=restages_revision,
        review_note=review_note,
        review_recommendation=review_recommendation,
        validation_scope=validation_scope,  # type: ignore[arg-type]
        limit=limit,
    )
    return to_dict(result)


def stage_map_assertion_change_tool(
    db: DoxaBase,
    subject: str,
    predicate: str,
    object: str | None,
    rationale: str,
    change_kind: str = "replace",
    graph: str = "map",
    object_kind: str = "auto",
    object_datatype: str | None = None,
    object_lang: str | None = None,
    summary: str | None = None,
    stance: str = "rc:CandidateRevision",
    revision_type: str = "rc:StagedRevision",
    included_graphs: list[str] | None = None,
    revision_iri: str | None = None,
    created_at: str | None = None,
    created_by: str | None = None,
    supporting_observations: list[str] | None = None,
    supporting_claims: list[str] | None = None,
    supporting_patterns: list[str] | None = None,
    revision_anchors: list[str] | None = None,
    evidence: list[str] | None = None,
    alternative_to: str | None = None,
    restages_revision: str | None = None,
    review_note: str | None = None,
    review_recommendation: str | None = None,
    validation_scope: str = "all",
    limit: int = 20,
) -> dict[str, Any]:
    result = db.stage_map_assertion_change(
        subject=subject,
        predicate=predicate,
        object=object,
        rationale=rationale,
        change_kind=change_kind,  # type: ignore[arg-type]
        graph=graph,  # type: ignore[arg-type]
        object_kind=object_kind,  # type: ignore[arg-type]
        object_datatype=object_datatype,
        object_lang=object_lang,
        summary=summary,
        stance=stance,
        revision_type=revision_type,
        included_graphs=included_graphs,
        revision_iri=revision_iri,
        created_at=created_at,
        created_by=created_by,
        supporting_observations=supporting_observations,
        supporting_claims=supporting_claims,
        supporting_patterns=supporting_patterns,
        revision_anchors=revision_anchors,
        evidence=evidence,
        alternative_to=alternative_to,
        restages_revision=restages_revision,
        review_note=review_note,
        review_recommendation=review_recommendation,
        validation_scope=validation_scope,  # type: ignore[arg-type]
        limit=limit,
    )
    payload = to_dict(result)
    payload["revision_iri"] = payload["staged_revision"]["revision_iri"]
    return payload


def stage_systematisation_tool(
    db: DoxaBase,
    summary: str,
    intent: str,
    framings: list[dict[str, Any]],
    anchors: list[str] | None = None,
    rationale: str | None = None,
    shared_additions: list[dict[str, str]] | None = None,
    shared_removals: list[dict[str, str]] | None = None,
    shared_context_summary: str | None = None,
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
        shared_additions=shared_additions,
        shared_removals=shared_removals,
        shared_context_summary=shared_context_summary,
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
    return to_dict(result)


def stage_pattern_promotion_tool(
    db: DoxaBase,
    patterns: list[str],
    framings: list[dict[str, Any]],
    summary: str | None = None,
    intent: str | None = None,
    rationale: str | None = None,
    anchors: list[str] | None = None,
    shared_additions: list[dict[str, str]] | None = None,
    shared_removals: list[dict[str, str]] | None = None,
    shared_context_summary: str | None = None,
    default_stance: str = "rc:CandidateRevision",
    revision_type: str = "rc:StagedRevision",
    included_graphs: list[str] | None = None,
    created_at: str | None = None,
    created_by: str | None = None,
    supporting_observations: list[str] | None = None,
    supporting_claims: list[str] | None = None,
    evidence: list[str] | None = None,
    alternative_to: str | None = None,
    link_alternatives: bool = True,
    validation_scope: str = "all",
) -> dict[str, Any]:
    result = db.stage_pattern_promotion(
        patterns=patterns,
        framings=framings,
        summary=summary,
        intent=intent,
        rationale=rationale,
        anchors=anchors,
        shared_additions=shared_additions,
        shared_removals=shared_removals,
        shared_context_summary=shared_context_summary,
        default_stance=default_stance,
        revision_type=revision_type,
        included_graphs=included_graphs,
        created_at=created_at,
        created_by=created_by,
        supporting_observations=supporting_observations,
        supporting_claims=supporting_claims,
        evidence=evidence,
        alternative_to=alternative_to,
        link_alternatives=link_alternatives,
        validation_scope=validation_scope,  # type: ignore[arg-type]
    )
    return to_dict(result)


def apply_staged_revision_tool(
    db: DoxaBase,
    iri: str,
    applied_revision_iri: str | None = None,
    created_at: str | None = None,
    created_by: str | None = None,
    allow_validation_failure: bool = False,
    validation_scope: str | None = None,
) -> dict[str, Any]:
    result = db.apply_staged_revision(
        iri=iri,
        applied_revision_iri=applied_revision_iri,
        created_at=created_at,
        created_by=created_by,
        allow_validation_failure=allow_validation_failure,
        validation_scope=validation_scope,  # type: ignore[arg-type]
    )
    return to_dict(result)


def export_staged_revision_tool(
    db: DoxaBase,
    iri: str,
    path: str,
    format: str = "markdown",
    overwrite: bool = False,
    fail_on_sensitive: bool = False,
) -> dict[str, Any]:
    resolved_path = _resolve_path(path)
    result = db.export_staged_revision(
        iri=iri,
        path=resolved_path,
        format=format,  # type: ignore[arg-type]
        overwrite=overwrite,
        fail_on_sensitive=fail_on_sensitive,
    )
    return to_dict(result)


def export_staged_revisions_tool(
    db: DoxaBase,
    revision_iris: list[str],
    path: str,
    title: str | None = None,
    executive_summary: str | None = None,
    format: str = "markdown",
    overwrite: bool = False,
    fail_on_sensitive: bool = False,
) -> dict[str, Any]:
    resolved_path = _resolve_path(path)
    result = db.export_staged_revisions(
        revision_iris=revision_iris,
        path=resolved_path,
        title=title,
        executive_summary=executive_summary,
        format=format,  # type: ignore[arg-type]
        overwrite=overwrite,
        fail_on_sensitive=fail_on_sensitive,
    )
    return to_dict(result)


def export_profile_insight_review_bundle_tool(
    db: DoxaBase,
    dataset_iri: str,
    evidence_iri: str,
    path: str,
    revision_iris: list[str] | None = None,
    include_current_staged_work: bool = True,
    current_staged_work_limit: int = 100,
    include_applied_staged_sources: bool = True,
    applied_staged_source_limit: int = 100,
    title: str | None = None,
    executive_summary: str | None = None,
    format: str = "markdown",
    overwrite: bool = False,
    fail_on_sensitive: bool = False,
) -> dict[str, Any]:
    resolved_path = _resolve_path(path)
    result = db.export_profile_insight_review_bundle(
        dataset_iri=dataset_iri,
        evidence_iri=evidence_iri,
        path=resolved_path,
        revision_iris=revision_iris,
        include_current_staged_work=include_current_staged_work,
        current_staged_work_limit=current_staged_work_limit,
        include_applied_staged_sources=include_applied_staged_sources,
        applied_staged_source_limit=applied_staged_source_limit,
        title=title,
        executive_summary=executive_summary,
        format=format,  # type: ignore[arg-type]
        overwrite=overwrite,
        fail_on_sensitive=fail_on_sensitive,
    )
    return to_dict(result)


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
    return to_dict(result)


def _pairs_to_dicts(pairs: list[tuple[str, int]], key_name: str) -> list[dict[str, Any]]:
    return [{key_name: key, "count": count} for key, count in pairs]


def _resolve_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate.resolve(strict=False)
    return (ROOT / candidate).resolve(strict=False)


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
