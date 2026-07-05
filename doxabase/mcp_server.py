from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from doxabase import DoxaBase
from doxabase.mcp_tools import (
    apply_staged_revision_tool,
    describe_dataset_tool,
    get_context_graph_tool,
    describe_query_context_tool,
    describe_resource_tool,
    describe_revision_tool,
    export_bundle_tool,
    export_preflight_tool,
    get_doc_tool,
    graph_overview_tool,
    import_bundle_tool,
    list_entities_tool,
    list_revisions_tool,
    plan_staged_revision_recovery_tool,
    project_brief_tool,
    record_claim_reconsideration_tool,
    record_graph_revision_tool,
    record_observation_tool,
    record_profile_tool,
    record_map_fact_tool,
    record_pattern_tool,
    restage_staged_revision_tool,
    search_tool,
    stage_revision_tool,
    validate_graph_tool,
)

SERVER_INSTRUCTIONS = """DoxaBase is a local RDF memory capsule for data projects: named graphs of current-best facts (map), dated findings (observations), syntheses (patterns), evidence, vocabulary, shapes, and change rationale (history). You supply semantic judgement; DoxaBase supplies storage, validation, staged change, and privacy scanning.
Start with doxabase.get_doc (no arguments lists the docs), then read start_here. doxabase.project_brief reports capsule state including gates that block mutation or export; respect gates, read-only inspection is always safe.
Orientation reads: doxabase.project_brief, doxabase.graph_overview, doxabase.search, doxabase.list_entities, doxabase.describe_resource, doxabase.describe_dataset, doxabase.describe_query_context, doxabase.get_context_graph. Kind-dispatched tools (record_*, stage_revision, export/import_bundle) validate spec fields per kind with targeted errors; the mcp_tools doc lists every kind's fields. Run doxabase.export_preflight before shareable artifacts."""


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
    def graph_overview(limit: int = 25) -> dict[str, Any]:
        """Return named graph counts, common classes, predicates, and key counts."""

        return graph_overview_tool(db, limit=limit)

    @server.tool(name="doxabase.export_preflight")
    def export_preflight(
        kind: str = "handoff_bundle",
        graphs: list[str] | None = None,
        revision_iris: list[str] | None = None,
        snapshot_graph_roles: list[str] | None = None,
        validation_scope: str | None = None,
        limit: int = 20,
        seed_iris: list[str] | None = None,
        profile: str | None = None,
        max_triples: int | None = None,
        include_seed_graphs: bool | None = None,
    ) -> dict[str, Any]:
        """Dry-run export privacy scope and conservative shareability
        decision. kind: 'handoff_bundle' (default), 'graph', 'trig', or
        'revision_snapshots' preflight the matching export_bundle write;
        kind='scan_only' just scans graph terms for credential-like values;
        kind='context_slice' preflights a context-slice export (requires
        seed_iris; optional profile/max_triples/include_seed_graphs).
        Kind-invalid params fail with targeted errors."""

        return export_preflight_tool(
            db,
            kind=kind,
            graphs=graphs,
            revision_iris=revision_iris,
            snapshot_graph_roles=snapshot_graph_roles,
            validation_scope=validation_scope,
            limit=limit,
            seed_iris=seed_iris,
            profile=profile,
            max_triples=max_triples,
            include_seed_graphs=include_seed_graphs,
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
        limit: int = 25,
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
        plan_candidate: str | int | None = None,
        engine: str = "duckdb",
        storage_access_iri: str | None = None,
        physical_layout_iri: str | None = None,
        allow_context_blocked_candidate: bool = False,
    ) -> dict[str, Any]:
        """Return compact non-secret query-planning context for one dataset.
        Pass plan_candidate ('auto', a candidate selector string, or a
        candidate index) to instead draft a non-executed, review-gated
        physical query plan for that candidate; the other planning params
        are only valid alongside plan_candidate."""

        return describe_query_context_tool(
            db,
            iri=iri,
            graph=graph,
            plan_candidate=plan_candidate,
            engine=engine,
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

    @server.tool(name="doxabase.list_revisions")
    def list_revisions(
        kind: str = "graph",
        graph: str | None = "history",
        revision_type: str | None = None,
        record_kind: str | None = None,
        application_status: str | None = None,
        staged_validation_status: str | None = None,
        stale_resolution_state: str | None = None,
        current_staged_work_only: bool | None = None,
        graph_role: str | None = None,
        exact_only: bool | None = None,
        include_current: bool | None = None,
        resource_iri: str | None = None,
        include_patch_mentions: bool | None = None,
        include_apply_checks: bool | None = None,
        drift_detail: str = "summary",
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List revision history. kind='graph' lists graph revisions
        (filters: revision_type, record_kind, application_status,
        staged_validation_status, stale_resolution_state,
        current_staged_work_only); kind='versions' lists graph-version
        snapshots for one required graph_role (exact_only,
        include_current); kind='resource' lists revisions anchored to or
        patch-mentioning a required resource_iri. include_apply_checks
        adds staged review routing (defaults True only for 'resource');
        kind-invalid params fail with targeted errors."""

        return list_revisions_tool(
            db,
            kind=kind,
            graph=graph,
            revision_type=revision_type,
            record_kind=record_kind,
            application_status=application_status,
            staged_validation_status=staged_validation_status,
            stale_resolution_state=stale_resolution_state,
            current_staged_work_only=current_staged_work_only,
            graph_role=graph_role,
            exact_only=exact_only,
            include_current=include_current,
            resource_iri=resource_iri,
            include_patch_mentions=include_patch_mentions,
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,
            limit=limit,
            offset=offset,
        )

    @server.tool(name="doxabase.describe_revision")
    def describe_revision(
        iri: str,
        aspect: str = "auto",
        graph: str | None = "history",
        include_current_apply_check: bool | None = None,
        include_triples: bool | None = None,
        max_triples: int | None = None,
        graph_role: str | None = None,
        after_revision_iri: str | None = None,
        compare_to_current: bool | None = None,
        resource_iri: str | None = None,
        include_patch_mentions: bool | None = None,
        include_apply_checks: bool | None = None,
        drift_detail: str | None = None,
        include_applied_diff: bool | None = None,
    ) -> dict[str, Any]:
        """Describe one revision. aspect='auto' returns revision metadata,
        auto-detecting staged patch rows (include_current_apply_check adds
        their live apply check). Other aspects: 'applied_diff' (stored
        before/after diff), 'version_diff' (iri = before version; requires
        graph_role; optional after_revision_iri/compare_to_current),
        'lineage', 'resource_lineage' (requires resource_iri),
        'snapshot_evidence', 'graph_snapshot' (requires graph_role).
        Aspect-invalid params fail with targeted errors."""

        return describe_revision_tool(
            db,
            iri=iri,
            aspect=aspect,
            graph=graph,
            include_current_apply_check=include_current_apply_check,
            include_triples=include_triples,
            max_triples=max_triples,
            graph_role=graph_role,
            after_revision_iri=after_revision_iri,
            compare_to_current=compare_to_current,
            resource_iri=resource_iri,
            include_patch_mentions=include_patch_mentions,
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,
            include_applied_diff=include_applied_diff,
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
        observed_asset: str | None = None,
        observed_column: str | None = None,
        observed_at: str | None = None,
        observed_by: str | None = None,
        evidence_summary: str | None = None,
        evidence_sources: list[str] | None = None,
    ) -> dict[str, Any]:
        """Record a point-in-time finding into observations+evidence.
        kind='observation' (default) or 'profile' use the flat fields with
        the long tail (sample/profile metrics, physical/value types, ...) in
        spec; kind='claim' or 'query_result' take their fields in spec.
        Targeted errors name the valid spec fields. Observations must cite
        evidence (evidence_summary requires evidence_sources or a source
        path)."""

        return record_observation_tool(
            db,
            summary=summary,
            kind=kind,
            spec=spec,
            observed_asset=observed_asset,
            observed_column=observed_column,
            observed_at=observed_at,
            observed_by=observed_by,
            evidence_summary=evidence_summary,
            evidence_sources=evidence_sources,
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
        evidence_summary: str | None = None,
        evidence_sources: list[str] | None = None,
        source_path: str | None = None,
        confidence: str | None = "rc:MediumConfidence",
        map_implications: list[str] | None = None,
        spec: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Synthesize related observations/claims into a pattern. The long
        tail (synthesis provenance, source spans, status/stability, IRIs)
        goes in spec; targeted errors name the valid fields. An
        evidence_summary requires evidence_sources or source_path."""

        return record_pattern_tool(
            db,
            summary=summary,
            pattern_text=pattern_text,
            rationale=rationale,
            pattern_targets=pattern_targets,
            supporting_observations=supporting_observations,
            supporting_claims=supporting_claims,
            evidence_summary=evidence_summary,
            evidence_sources=evidence_sources,
            source_path=source_path,
            confidence=confidence,
            map_implications=map_implications,
            spec=spec,
        )

    @server.tool(name="doxabase.record_claim_reconsideration")
    def record_claim_reconsideration(
        newer_claim: str,
        older_claim: str,
        relation: str,
        rationale: str,
        summary: str | None = None,
        evidence_summary: str | None = None,
        evidence_sources: list[str] | None = None,
        source_path: str | None = None,
        spec: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record that a newer claim weakens, contradicts, supersedes, or
        refines an older one - reconsider, never delete. The tail
        (reconsidered_at/by, source spans, older_claim_status) goes in
        spec; targeted errors name the valid fields."""

        return record_claim_reconsideration_tool(
            db,
            newer_claim=newer_claim,
            older_claim=older_claim,
            relation=relation,
            rationale=rationale,
            summary=summary,
            evidence_summary=evidence_summary,
            evidence_sources=evidence_sources,
            source_path=source_path,
            spec=spec,
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

    @server.tool(name="doxabase.import_bundle")
    def import_bundle(
        kind: str,
        spec: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Import an artifact into the capsule. kind: 'trig' (named-graph
        TriG file; spec: path, replace), 'revision_snapshots' (stored
        snapshot-row JSON; spec: path, replace), 'handoff'
        (recovery-complete manifest; spec: manifest_path, dry_run, replace,
        include_drafts, validation_scope, drift_detail), or
        'example_fixtures' (bundled AIS/Polymarket fixtures; spec: replace).
        Targeted errors name each kind's valid and missing spec fields."""

        return import_bundle_tool(db, kind=kind, spec=spec)

    @server.tool(name="doxabase.export_bundle")
    def export_bundle(
        kind: str,
        spec: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Write a reviewed export artifact. kind: 'trig' (named-graph
        bundle), 'graph' (flattened RDF file), 'context_slice' (importable
        slice TriG; spec: path, seed_iris, ...), 'staged_revisions'
        (review bundle; spec revision_iris is one IRI string or a list for
        the grouped comparison, plus path), 'profile_insight_review',
        'revision_snapshots' (snapshot-row JSON), or 'handoff' (spec:
        trig_path, revision_snapshot_path, manifest_path, ...). Run
        export_preflight first; targeted errors name each kind's
        valid/missing spec fields."""

        return export_bundle_tool(db, kind=kind, spec=spec)

    @server.tool(name="doxabase.record_graph_revision")
    def record_graph_revision(
        summary: str,
        rationale: str,
        changed_graphs: list[str],
        revision_type: str = "rc:ManualRevision",
        spec: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record revision metadata into history for a change that already
        happened (staged work records its own). The tail (supporting
        observations/claims/patterns, anchors, evidence, export path, graph
        counts, validation fields, identity) goes in spec; targeted errors
        name the valid fields."""

        return record_graph_revision_tool(
            db,
            summary=summary,
            rationale=rationale,
            changed_graphs=changed_graphs,
            revision_type=revision_type,
            spec=spec,
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
