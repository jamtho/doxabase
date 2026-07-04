from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from doxabase import DoxaBase
from doxabase.mcp_tools import (
    apply_staged_revision_tool,
    describe_applied_revision_diff_tool,
    describe_dataset_tool,
    get_context_graph_tool,
    describe_graph_revision_tool,
    describe_graph_version_diff_tool,
    describe_query_context_tool,
    describe_revision_graph_snapshot_tool,
    describe_revision_lineage_tool,
    describe_resource_revision_lineage_tool,
    describe_resource_tool,
    describe_revision_snapshot_evidence_tool,
    describe_staged_revision_tool,
    draft_query_plan_tool,
    export_context_slice_tool,
    export_graph_tool,
    export_handoff_bundle_tool,
    export_preflight_tool,
    export_profile_insight_review_bundle_tool,
    export_staged_revision_tool,
    export_staged_revisions_tool,
    export_trig_tool,
    export_revision_snapshots_tool,
    get_doc_tool,
    graph_overview_tool,
    import_handoff_bundle_tool,
    import_revision_snapshots_tool,
    import_trig_tool,
    list_entities_tool,
    list_graph_revisions_tool,
    list_graph_versions_tool,
    list_resource_revisions_tool,
    load_example_fixtures_tool,
    plan_staged_revision_recovery_tool,
    preflight_context_slice_export_tool,
    project_brief_tool,
    record_analysis_packet_tool,
    record_claim_observation_tool,
    record_claim_reconsideration_tool,
    record_column_profile_tool,
    record_dataset_profile_tool,
    record_domain_network_profile_tool,
    record_map_caveat_tool,
    record_map_analysis_view_bundle_tool,
    record_map_analysis_view_tool,
    record_map_asset_transform_tool,
    record_map_column_tool,
    record_map_dataset_tool,
    record_map_table_bundle_tool,
    record_map_partition_scheme_tool,
    record_map_physical_layout_tool,
    record_map_relationship_tool,
    record_map_storage_access_tool,
    record_profiled_parquet_table_tool,
    record_profile_to_capsule_manifest_tool,
    record_graph_revision_tool,
    record_observation_tool,
    record_profile_tool,
    record_map_fact_tool,
    record_pattern_tool,
    record_query_result_tool,
    record_profile_bundle_tool,
    replace_graph_triples_tool,
    restage_staged_revision_tool,
    scan_sensitive_literals_tool,
    search_tool,
    stage_revision_tool,
    validate_graph_tool,
)

SERVER_INSTRUCTIONS = """DoxaBase is a local RDF memory capsule for data projects.
Start with doxabase.get_doc (no arguments lists the docs), then read start_here. Use overview, graph_roles, and agent_workflow when you need fuller context.
Use doxabase.project_brief, doxabase.export_preflight, doxabase.graph_overview, doxabase.search, doxabase.list_entities, doxabase.describe_resource, doxabase.describe_dataset, doxabase.describe_query_context, and doxabase.get_context_graph before asking for broader graph context.
Current V1 tools support inspection, profile-to-map update drafting/staging and profile advisory follow-through planning, profile insight review bundle export, query-planning context, query-result capture, query-evidence storage overlay drafting, storage-access and physical-layout query repair staging, context slicing and context-slice export, type-aware resource/pattern/revision retrieval, revision listing, resource-centric revision discovery, staged patch-payload lexical discovery, revision snapshot evidence and graph-snapshot inspection, lexical search, privacy/export hygiene preflight and scanning, bounded dataset/storage description, map authoring, no-I/O profiled Parquet table recording, observation/profile/profile-bundle/claim/pattern/claim-reconsideration/history recording, staged review-decision recording, assertion-aware map-change drafting and staging, systematisation and pattern-promotion staging, shared-context systematisation rerun drafting, staged graph revision recovery planning/session/apply checks/restage/batch-restage/apply/review, controlled graph replacement, handoff-manifest import/export, fixture loading, and validation."""


class _LazyDoxaBase:
    def __init__(self, capsule_path: str | Path) -> None:
        self._capsule_path = capsule_path
        self._db: DoxaBase | None = None

    def _open(self) -> DoxaBase:
        if self._db is None:
            self._db = DoxaBase.create(self._capsule_path, overwrite=False)
        return self._db

    def __getattr__(self, name: str) -> Any:
        return getattr(self._open(), name)


def build_server(capsule_path: str | Path = ".doxabase.sqlite") -> FastMCP:
    db = _LazyDoxaBase(capsule_path)
    server = FastMCP("doxabase", instructions=SERVER_INSTRUCTIONS)

    @server.tool(name="doxabase.get_doc")
    def get_doc(
        doc_id: str | None = None,
        max_chars: int = 12000,
        start_char: int = 0,
        section: str | None = None,
    ) -> dict[str, Any]:
        """Return one agent doc by ID (with optional section/offset slicing),
        or the list of available docs when doc_id is omitted."""

        return get_doc_tool(
            doc_id,
            max_chars=max_chars,
            start_char=start_char,
            section=section,
        )

    @server.tool(name="doxabase.graph_overview")
    def graph_overview(limit: int = 100) -> dict[str, Any]:
        """Return named graph counts, common classes, predicates, and key counts."""

        return graph_overview_tool(db, limit=limit)

    @server.tool(name="doxabase.scan_sensitive_literals")
    def scan_sensitive_literals(
        graphs: list[str] | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Scan graph terms for suspicious credential-like values."""

        return scan_sensitive_literals_tool(db, graphs=graphs, limit=limit)

    @server.tool(name="doxabase.export_preflight")
    def export_preflight(
        export_kind: str = "handoff_bundle",
        graphs: list[str] | None = None,
        revision_iris: list[str] | None = None,
        snapshot_graph_roles: list[str] | None = None,
        validation_scope: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Dry-run export privacy scope and conservative shareability decision."""

        return export_preflight_tool(
            db,
            export_kind=export_kind,
            graphs=graphs,
            revision_iris=revision_iris,
            snapshot_graph_roles=snapshot_graph_roles,
            validation_scope=validation_scope,
            limit=limit,
        )

    @server.tool(name="doxabase.project_brief")
    def project_brief(
        limit: int = 20,
    ) -> dict[str, Any]:
        """Return read-only capsule state: counts, dataset one-liners, gates
        (what is blocked and the one call that inspects each blocker), queues
        of pending work, and up to five suggested next actions."""

        return project_brief_tool(db, limit=limit)

    @server.tool(name="doxabase.list_entities")
    def list_entities(
        type: str | None = None,
        graph: str | None = "map",
        text: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List graph entities by RDF type, graph role, and optional text filter."""

        return list_entities_tool(
            db,
            type=type,
            graph=graph,
            text=text,
            limit=limit,
            offset=offset,
        )

    @server.tool(name="doxabase.describe_dataset")
    def describe_dataset(iri: str, graph: str | None = "map") -> dict[str, Any]:
        """Return bounded schema, layout, storage access, caveat, and provenance context."""

        return describe_dataset_tool(db, iri=iri, graph=graph)

    @server.tool(name="doxabase.describe_query_context")
    def describe_query_context(
        iri: str,
        graph: str | None = "map",
    ) -> dict[str, Any]:
        """Return compact non-secret query-planning context for one dataset."""

        return describe_query_context_tool(db, iri=iri, graph=graph)

    @server.tool(name="doxabase.draft_query_plan")
    def draft_query_plan(
        iri: str,
        graph: str | None = "map",
        engine: str = "duckdb",
        candidate_index: int | None = None,
        candidate_selector: str | None = None,
        storage_access_iri: str | None = None,
        physical_layout_iri: str | None = None,
        allow_context_blocked_candidate: bool = False,
    ) -> dict[str, Any]:
        """Draft a non-executed, review-gated physical query plan."""

        return draft_query_plan_tool(
            db,
            iri=iri,
            graph=graph,
            engine=engine,
            candidate_index=candidate_index,
            candidate_selector=candidate_selector,
            storage_access_iri=storage_access_iri,
            physical_layout_iri=physical_layout_iri,
            allow_context_blocked_candidate=allow_context_blocked_candidate,
        )

    @server.tool(name="doxabase.get_context_graph")
    def get_context_graph(
        seed_iris: list[str],
        profile: str = "dataset_brief",
        max_triples: int = 500,
        include_trig: bool = True,
        privacy_scan_limit: int = 20,
    ) -> dict[str, Any]:
        """Return a route-explained graph slice around datasets, patterns, or lore."""

        return get_context_graph_tool(
            db,
            seed_iris=seed_iris,
            profile=profile,
            max_triples=max_triples,
            include_trig=include_trig,
            privacy_scan_limit=privacy_scan_limit,
        )

    @server.tool(name="doxabase.preflight_context_slice_export")
    def preflight_context_slice_export(
        seed_iris: list[str],
        profile: str = "dataset_brief",
        max_triples: int = 500,
        include_seed_graphs: bool = False,
        validation_scope: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Dry-run an importable context-slice TriG export with privacy and validation gates."""

        return preflight_context_slice_export_tool(
            db,
            seed_iris=seed_iris,
            profile=profile,
            max_triples=max_triples,
            include_seed_graphs=include_seed_graphs,
            validation_scope=validation_scope,
            limit=limit,
        )

    @server.tool(name="doxabase.export_context_slice")
    def export_context_slice(
        path: str,
        seed_iris: list[str],
        profile: str = "dataset_brief",
        max_triples: int = 500,
        include_seed_graphs: bool = False,
        overwrite: bool = False,
        fail_on_sensitive: bool = False,
        fail_on_invalid: bool = True,
        validation_scope: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Write an importable TriG bundle for selected context-slice triples.

        By default, fail_on_invalid=True blocks writes when the live graph
        validation scope implied by the selected graph roles fails. Pass
        fail_on_invalid=False only for a deliberately reviewed diagnostic
        artifact.
        """

        return export_context_slice_tool(
            db,
            path=path,
            seed_iris=seed_iris,
            profile=profile,
            max_triples=max_triples,
            include_seed_graphs=include_seed_graphs,
            overwrite=overwrite,
            fail_on_sensitive=fail_on_sensitive,
            fail_on_invalid=fail_on_invalid,
            validation_scope=validation_scope,
            limit=limit,
        )

    @server.tool(name="doxabase.describe_resource")
    def describe_resource(
        iri: str,
        graph: str | None = None,
        aspect: str = "auto",
        include_incoming: bool = True,
        limit: int = 100,
        outgoing_offset: int = 0,
        incoming_offset: int = 0,
        include_blank_node_closure: bool = False,
        blank_node_depth: int = 2,
        blank_node_limit: int = 100,
        evidence_iri: str | None = None,
        predicate: str | None = None,
        object: str | None = None,
        object_kind: str = "auto",
        object_datatype: str | None = None,
        object_lang: str | None = None,
    ) -> dict[str, Any]:
        """Describe one resource. aspect='auto' detects patterns and analysis
        views by rdf:type and otherwise returns the resource's triples;
        aspect='profile_run' needs evidence_iri (iri = profiled dataset);
        aspect='assertion_support' needs predicate (iri = subject; optional
        object/object_kind/object_datatype/object_lang)."""

        return describe_resource_tool(
            db,
            iri=iri,
            graph=graph,
            aspect=aspect,
            include_incoming=include_incoming,
            limit=limit,
            outgoing_offset=outgoing_offset,
            incoming_offset=incoming_offset,
            include_blank_node_closure=include_blank_node_closure,
            blank_node_depth=blank_node_depth,
            blank_node_limit=blank_node_limit,
            evidence_iri=evidence_iri,
            predicate=predicate,
            object=object,
            object_kind=object_kind,
            object_datatype=object_datatype,
            object_lang=object_lang,
        )

    @server.tool(name="doxabase.describe_graph_revision")
    def describe_graph_revision(
        iri: str,
        graph: str | None = "history",
    ) -> dict[str, Any]:
        """Return compact revision metadata, snapshots, and support links."""

        return describe_graph_revision_tool(db, iri=iri, graph=graph)

    @server.tool(name="doxabase.describe_revision_snapshot_evidence")
    def describe_revision_snapshot_evidence(
        iri: str,
        graph: str | None = "history",
    ) -> dict[str, Any]:
        """Classify RDF history and SQLite snapshot-row evidence for a revision."""

        return describe_revision_snapshot_evidence_tool(db, iri=iri, graph=graph)

    @server.tool(name="doxabase.describe_revision_graph_snapshot")
    def describe_revision_graph_snapshot(
        iri: str,
        graph_role: str,
        graph: str | None = "history",
        include_triples: bool = False,
        max_triples: int = 500,
    ) -> dict[str, Any]:
        """Return one stored revision graph snapshot, optionally with triples."""

        return describe_revision_graph_snapshot_tool(
            db,
            iri=iri,
            graph_role=graph_role,
            graph=graph,
            include_triples=include_triples,
            max_triples=max_triples,
        )

    @server.tool(name="doxabase.describe_applied_revision_diff")
    def describe_applied_revision_diff(
        iri: str,
        graph: str | None = "history",
        include_triples: bool = False,
        max_triples: int = 500,
    ) -> dict[str, Any]:
        """Return stored snapshot diffs for an applied staged revision."""

        return describe_applied_revision_diff_tool(
            db,
            iri=iri,
            graph=graph,
            include_triples=include_triples,
            max_triples=max_triples,
        )

    @server.tool(name="doxabase.describe_graph_version_diff")
    def describe_graph_version_diff(
        graph_role: str,
        before_revision_iri: str,
        after_revision_iri: str | None = None,
        compare_to_current: bool = True,
        graph: str | None = "history",
        include_triples: bool = False,
        max_triples: int = 500,
    ) -> dict[str, Any]:
        """Compare a stored graph version to another version or current graph."""

        return describe_graph_version_diff_tool(
            db,
            graph_role=graph_role,
            before_revision_iri=before_revision_iri,
            after_revision_iri=after_revision_iri,
            compare_to_current=compare_to_current,
            graph=graph,
            include_triples=include_triples,
            max_triples=max_triples,
        )

    @server.tool(name="doxabase.list_graph_revisions")
    def list_graph_revisions(
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
        """List graph revisions, optionally with staged apply-check status."""

        return list_graph_revisions_tool(
            db,
            revision_type=revision_type,
            graph=graph,
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,
            record_kind=record_kind,
            application_status=application_status,
            staged_validation_status=staged_validation_status,
            stale_resolution_state=stale_resolution_state,
            current_staged_work_only=current_staged_work_only,
            limit=limit,
            offset=offset,
        )

    @server.tool(name="doxabase.list_graph_versions")
    def list_graph_versions(
        graph_role: str,
        graph: str | None = "history",
        exact_only: bool = False,
        include_current: bool = True,
        include_apply_checks: bool = False,
        drift_detail: str = "summary",
        record_kind: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List stored graph-version snapshots for one graph role.

        Pass include_apply_checks=True for version-first staged review. Then
        staged patch rows also carry application_status, stale/restage blockers,
        next_action, and next_action_queue_item routing fields copied from the
        revision triage surface.
        """

        return list_graph_versions_tool(
            db,
            graph_role=graph_role,
            graph=graph,
            exact_only=exact_only,
            include_current=include_current,
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,
            record_kind=record_kind,
            limit=limit,
            offset=offset,
        )

    @server.tool(name="doxabase.describe_revision_lineage")
    def describe_revision_lineage(
        iri: str,
        graph: str | None = "history",
        include_apply_checks: bool = True,
        drift_detail: str = "summary",
    ) -> dict[str, Any]:
        """Describe one graph revision's restage/apply lineage."""

        return describe_revision_lineage_tool(
            db,
            iri=iri,
            graph=graph,
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,
        )

    @server.tool(name="doxabase.list_resource_revisions")
    def list_resource_revisions(
        resource_iri: str,
        graph: str | None = "history",
        include_patch_mentions: bool = True,
        include_apply_checks: bool = True,
        drift_detail: str = "summary",
        current_staged_work_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List revisions anchored to or patch-mentioning one resource."""

        return list_resource_revisions_tool(
            db,
            resource_iri=resource_iri,
            graph=graph,
            include_patch_mentions=include_patch_mentions,
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,
            current_staged_work_only=current_staged_work_only,
            limit=limit,
            offset=offset,
        )

    @server.tool(name="doxabase.describe_resource_revision_lineage")
    def describe_resource_revision_lineage(
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
        """Describe one resource/revision match and its immediate lineage."""

        return describe_resource_revision_lineage_tool(
            db,
            resource_iri=resource_iri,
            revision_iri=revision_iri,
            graph=graph,
            include_patch_mentions=include_patch_mentions,
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,
            include_applied_diff=include_applied_diff,
            include_triples=include_triples,
            max_triples=max_triples,
        )

    @server.tool(name="doxabase.describe_staged_revision")
    def describe_staged_revision(
        iri: str,
        graph: str | None = "history",
        include_current_apply_check: bool = False,
    ) -> dict[str, Any]:
        """Return staged revision metadata and patch payloads for review."""

        return describe_staged_revision_tool(
            db,
            iri=iri,
            graph=graph,
            include_current_apply_check=include_current_apply_check,
        )

    @server.tool(name="doxabase.plan_staged_revision_recovery")
    def plan_staged_revision_recovery(
        revision_iris: list[str] | None = None,
        start_session: bool = False,
        session_iri: str | None = None,
        summary: str | None = None,
        handoff_manifest_path: str | None = None,
        current_staged_work_only: bool | None = None,
        include_drafts: bool | None = None,
        repair_draft_limit: int | None = None,
        validation_scope: str | None = None,
        drift_detail: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        created_at: str | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """Plan read-only recovery routes for staged revision queues.
        start_session=True persists the plan as a durable recovery session
        (summary, handoff_manifest_path, created_* apply only then).
        session_iri= without start_session describes that persisted session
        with a live replan; include_drafts/repair_draft_limit/drift_detail
        then default to the stored session settings."""

        return plan_staged_revision_recovery_tool(
            db,
            revision_iris=revision_iris,
            start_session=start_session,
            session_iri=session_iri,
            summary=summary,
            handoff_manifest_path=handoff_manifest_path,
            current_staged_work_only=current_staged_work_only,
            include_drafts=include_drafts,
            repair_draft_limit=repair_draft_limit,
            validation_scope=validation_scope,
            drift_detail=drift_detail,
            limit=limit,
            offset=offset,
            created_at=created_at,
            created_by=created_by,
        )

    @server.tool(name="doxabase.record_observation")
    def record_observation(
        summary: str | None = None,
        kind: str | None = None,
        spec: dict[str, Any] | None = None,
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
        """Record a point-in-time finding into observations+evidence.
        kind='observation' (default) or 'profile' use the flat fields;
        kind='claim' or 'query_result' take their fields in spec (targeted
        errors name the valid/missing fields). Observations must cite
        evidence (evidence_summary requires evidence_sources or a source
        path)."""

        return record_observation_tool(
            db,
            summary=summary,
            kind=kind,
            spec=spec,
            observation_type=observation_type,
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

    @server.tool(name="doxabase.record_profile")
    def record_profile(
        kind: str,
        spec: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record profile evidence. kind: 'dataset', 'column', 'bundle', or
        'domain_network'; spec carries that kind's fields (validation errors
        name the valid and missing fields; see get_doc('profiling'))."""

        return record_profile_tool(db, kind=kind, spec=spec)

    @server.tool(name="doxabase.record_map_fact")
    def record_map_fact(
        kind: str,
        spec: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record a current-best map fact. kind: 'dataset', 'column',
        'caveat', 'relationship', 'storage_access', 'physical_layout',
        'partition_scheme', 'asset_transform', 'analysis_view',
        'analysis_view_bundle', 'table_bundle', 'analysis_packet',
        'profile_manifest', or 'profiled_parquet_table'; spec carries that
        kind's fields (targeted errors name valid/missing fields; see
        get_doc('map_authoring'))."""

        return record_map_fact_tool(db, kind=kind, spec=spec)

    @server.tool(name="doxabase.record_pattern")
    def record_pattern(
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
        """Record a synthesis pattern linking observations or evidence to map targets."""

        return record_pattern_tool(
            db,
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

    @server.tool(name="doxabase.record_claim_reconsideration")
    def record_claim_reconsideration(
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
        """Record that one claim weakens, contradicts, supersedes, or refines another."""

        return record_claim_reconsideration_tool(
            db,
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

    @server.tool(name="doxabase.search")
    def search(
        query: str,
        graph: str | None = None,
        scope: str = "graphs",
        current_staged_work_only: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Lexical search. scope='graphs' searches literal RDF claims across
        named graphs; scope='staged_patches' searches staged revision patch
        payloads (graph defaults to history there)."""

        return search_tool(
            db,
            query=query,
            graph=graph,
            scope=scope,
            current_staged_work_only=current_staged_work_only,
            limit=limit,
            offset=offset,
        )

    @server.tool(name="doxabase.import_trig")
    def import_trig(path: str, replace: bool = False) -> dict[str, Any]:
        """Import a TriG file into DoxaBase graph roles."""

        return import_trig_tool(db, path=path, replace=replace)

    @server.tool(name="doxabase.import_revision_snapshots")
    def import_revision_snapshots(
        path: str,
        replace: bool = False,
    ) -> dict[str, Any]:
        """Import a JSON bundle of stored revision snapshot rows."""

        return import_revision_snapshots_tool(db, path=path, replace=replace)

    @server.tool(name="doxabase.import_handoff_bundle")
    def import_handoff_bundle(
        manifest_path: str,
        dry_run: bool = False,
        replace: bool = False,
        include_drafts: bool = True,
        validation_scope: str | None = None,
        drift_detail: str = "summary",
    ) -> dict[str, Any]:
        """Import a recovery-complete handoff manifest and return recovery state."""

        return import_handoff_bundle_tool(
            db,
            manifest_path=manifest_path,
            dry_run=dry_run,
            replace=replace,
            include_drafts=include_drafts,
            validation_scope=validation_scope,
            drift_detail=drift_detail,
        )

    @server.tool(name="doxabase.export_graph")
    def export_graph(
        path: str,
        graphs: list[str] | None = None,
        format: str = "turtle",
        overwrite: bool = False,
        fail_on_sensitive: bool = False,
        fail_on_invalid: bool = True,
        validation_scope: str | None = None,
    ) -> dict[str, Any]:
        """Export one or more graph roles as a flattened RDF graph file."""

        return export_graph_tool(
            db,
            path=path,
            graphs=graphs,
            format=format,
            overwrite=overwrite,
            fail_on_sensitive=fail_on_sensitive,
            fail_on_invalid=fail_on_invalid,
            validation_scope=validation_scope,
        )

    @server.tool(name="doxabase.replace_graph_triples")
    def replace_graph_triples(
        graph: str,
        removals: str | None = None,
        additions: str | None = None,
        format: str = "turtle",
        expected_count: int | None = None,
        allow_count_change: bool = False,
    ) -> dict[str, Any]:
        """Replace caller-authored triples in one graph with count/digest metadata."""

        return replace_graph_triples_tool(
            db,
            graph=graph,
            removals=removals,
            additions=additions,
            format=format,
            expected_count=expected_count,
            allow_count_change=allow_count_change,
        )

    @server.tool(name="doxabase.export_trig")
    def export_trig(
        path: str,
        graphs: list[str] | None = None,
        overwrite: bool = False,
        fail_on_sensitive: bool = False,
        fail_on_invalid: bool = True,
        validation_scope: str | None = None,
    ) -> dict[str, Any]:
        """Export graph roles as a named-graph TriG bundle."""

        return export_trig_tool(
            db,
            path=path,
            graphs=graphs,
            overwrite=overwrite,
            fail_on_sensitive=fail_on_sensitive,
            fail_on_invalid=fail_on_invalid,
            validation_scope=validation_scope,
        )

    @server.tool(name="doxabase.export_revision_snapshots")
    def export_revision_snapshots(
        path: str,
        revision_iris: list[str] | None = None,
        graph_roles: list[str] | None = None,
        overwrite: bool = False,
        fail_on_sensitive: bool = False,
    ) -> dict[str, Any]:
        """Export stored revision snapshot rows as a JSON handoff bundle."""

        return export_revision_snapshots_tool(
            db,
            path=path,
            revision_iris=revision_iris,
            graph_roles=graph_roles,
            overwrite=overwrite,
            fail_on_sensitive=fail_on_sensitive,
        )

    @server.tool(name="doxabase.export_handoff_bundle")
    def export_handoff_bundle(
        trig_path: str,
        revision_snapshot_path: str,
        manifest_path: str | None = None,
        graphs: list[str] | None = None,
        revision_iris: list[str] | None = None,
        snapshot_graph_roles: list[str] | None = None,
        overwrite: bool = False,
        fail_on_sensitive: bool = False,
        fail_on_invalid: bool = True,
        validation_scope: str | None = None,
    ) -> dict[str, Any]:
        """Export project TriG plus revision snapshot JSON as one handoff."""

        return export_handoff_bundle_tool(
            db,
            trig_path=trig_path,
            revision_snapshot_path=revision_snapshot_path,
            manifest_path=manifest_path,
            graphs=graphs,
            revision_iris=revision_iris,
            snapshot_graph_roles=snapshot_graph_roles,
            overwrite=overwrite,
            fail_on_sensitive=fail_on_sensitive,
            fail_on_invalid=fail_on_invalid,
            validation_scope=validation_scope,
        )

    @server.tool(name="doxabase.record_graph_revision")
    def record_graph_revision(
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
        """Record graph revision metadata in the history graph."""

        return record_graph_revision_tool(
            db,
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

    @server.tool(name="doxabase.stage_revision")
    def stage_revision(
        kind: str,
        spec: dict[str, Any] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Stage a reviewable revision without applying it. kind: 'graph',
        'map_assertion', 'systematisation', 'pattern_promotion',
        'profile_map_updates', 'query_storage_access_repair',
        'query_physical_layout_repair', or 'review_decision' (closes a
        staged row); spec carries that kind's fields (targeted errors name
        them). dry_run=True writes nothing, keeping the draft shapes:
        'map_assertion', 'profile_map_updates' (followthrough spec fields
        switch to the followthrough plan), 'systematisation' (rerun),
        'query_evidence_overlay' (dry-run only)."""

        return stage_revision_tool(db, kind=kind, spec=spec, dry_run=dry_run)

    @server.tool(name="doxabase.restage_staged_revision")
    def restage_staged_revision(
        revision_iris: list[str] | str,
        summary: str | None = None,
        rationale: str | None = None,
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
        """Restage conflicted staged revisions against current graph state.
        revision_iris: one IRI string restages that revision
        (summary/rationale override provenance); a list runs the batch path
        (path/title/executive_summary export one comparison review bundle).
        dry_run=True writes nothing: with a string it returns the read-only
        rebase-draft plan; with a list, the batch would-restage preview."""

        return restage_staged_revision_tool(
            db,
            revision_iris=revision_iris,
            summary=summary,
            rationale=rationale,
            path=path,
            title=title,
            executive_summary=executive_summary,
            format=format,
            overwrite=overwrite,
            created_at=created_at,
            created_by=created_by,
            validation_scope=validation_scope,
            dry_run=dry_run,
        )

    @server.tool(name="doxabase.export_staged_revision")
    def export_staged_revision(
        iri: str,
        path: str,
        format: str = "markdown",
        overwrite: bool = False,
        fail_on_sensitive: bool = False,
    ) -> dict[str, Any]:
        """Export a staged revision review bundle."""

        return export_staged_revision_tool(
            db,
            iri=iri,
            path=path,
            format=format,
            overwrite=overwrite,
            fail_on_sensitive=fail_on_sensitive,
        )

    @server.tool(name="doxabase.apply_staged_revision")
    def apply_staged_revision(
        iri: str,
        applied_revision_iri: str | None = None,
        created_at: str | None = None,
        created_by: str | None = None,
        allow_validation_failure: bool = False,
        validation_scope: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Apply a staged graph revision after conflict and validation checks.
        dry_run=True runs the read-only apply check instead (iri and
        validation_scope only) and returns the check response shape."""

        return apply_staged_revision_tool(
            db,
            iri=iri,
            applied_revision_iri=applied_revision_iri,
            created_at=created_at,
            created_by=created_by,
            allow_validation_failure=allow_validation_failure,
            validation_scope=validation_scope,
            dry_run=dry_run,
        )

    @server.tool(name="doxabase.export_staged_revisions")
    def export_staged_revisions(
        revision_iris: list[str],
        path: str,
        title: str | None = None,
        executive_summary: str | None = None,
        format: str = "markdown",
        overwrite: bool = False,
        fail_on_sensitive: bool = False,
    ) -> dict[str, Any]:
        """Export multiple staged revisions into one comparison review bundle."""

        return export_staged_revisions_tool(
            db,
            revision_iris=revision_iris,
            path=path,
            title=title,
            executive_summary=executive_summary,
            format=format,
            overwrite=overwrite,
            fail_on_sensitive=fail_on_sensitive,
        )

    @server.tool(name="doxabase.export_profile_insight_review_bundle")
    def export_profile_insight_review_bundle(
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
        """Export staged revisions connected to one profile evidence run."""

        return export_profile_insight_review_bundle_tool(
            db,
            dataset_iri=dataset_iri,
            evidence_iri=evidence_iri,
            path=path,
            revision_iris=revision_iris,
            include_current_staged_work=include_current_staged_work,
            current_staged_work_limit=current_staged_work_limit,
            include_applied_staged_sources=include_applied_staged_sources,
            applied_staged_source_limit=applied_staged_source_limit,
            title=title,
            executive_summary=executive_summary,
            format=format,
            overwrite=overwrite,
            fail_on_sensitive=fail_on_sensitive,
        )

    @server.tool(name="doxabase.load_example_fixtures")
    def load_example_fixtures(replace: bool = False) -> dict[str, Any]:
        """Import the bundled AIS and Polymarket RC fixture graphs."""

        return load_example_fixtures_tool(db, replace=replace)

    @server.tool(name="doxabase.validate_graph")
    def validate_graph(scope: str = "map", limit_results: int = 100) -> dict[str, Any]:
        """Run SHACL validation for map, ontology, patterns, shapes, or all graph scope."""

        return validate_graph_tool(db, scope=scope, limit_results=limit_results)

    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the DoxaBase MCP server.")
    parser.add_argument(
        "--capsule",
        default=".doxabase.sqlite",
        help="SQLite capsule path. Defaults to .doxabase.sqlite in the current directory.",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport. Defaults to stdio.",
    )
    args = parser.parse_args()
    build_server(args.capsule).run(args.transport)


if __name__ == "__main__":
    main()
