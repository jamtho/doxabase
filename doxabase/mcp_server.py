from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from doxabase import DoxaBase
from doxabase.mcp_tools import (
    apply_staged_revision_tool,
    check_staged_revision_apply_tool,
    describe_dataset_tool,
    describe_context_slice_tool,
    describe_graph_revision_tool,
    describe_pattern_tool,
    describe_resource_tool,
    describe_staged_revision_tool,
    export_graph_tool,
    export_staged_revision_tool,
    export_staged_revisions_tool,
    export_trig_tool,
    get_doc_tool,
    graph_overview_tool,
    import_trig_tool,
    list_docs_tool,
    list_entities_tool,
    load_example_fixtures_tool,
    record_claim_observation_tool,
    record_claim_reconsideration_tool,
    record_column_profile_tool,
    record_dataset_profile_tool,
    record_map_caveat_tool,
    record_map_column_tool,
    record_map_dataset_tool,
    record_map_partition_scheme_tool,
    record_map_physical_layout_tool,
    record_map_relationship_tool,
    record_map_storage_access_tool,
    record_graph_revision_tool,
    record_observation_tool,
    record_pattern_tool,
    search_tool,
    stage_graph_revision_tool,
    stage_pattern_promotion_tool,
    stage_systematisation_tool,
    validate_graph_tool,
)

SERVER_INSTRUCTIONS = """DoxaBase is a local RDF memory capsule for data projects.
Start with doxabase.list_docs, then read overview, graph_roles, and agent_workflow.
Use graph_overview, search, list_entities, describe_dataset, describe_context_slice, and describe_pattern before asking for broader graph context.
Current V1 tools support inspection, context slicing, type-aware resource/pattern/revision retrieval, lexical search, bounded dataset/storage description, map authoring, observation/profile/claim/pattern/claim-reconsideration/history recording, systematisation and pattern-promotion staging, staged graph revision apply checks/apply/review, import/export, fixture loading, and validation."""


def build_server(capsule_path: str | Path = ".doxabase.sqlite") -> FastMCP:
    db = DoxaBase.create(capsule_path, overwrite=False)
    server = FastMCP("doxabase", instructions=SERVER_INSTRUCTIONS)

    @server.tool(name="doxabase.list_docs")
    def list_docs() -> dict[str, Any]:
        """List short agent-facing DoxaBase docs available through MCP."""

        return list_docs_tool()

    @server.tool(name="doxabase.get_doc")
    def get_doc(doc_id: str, max_chars: int = 12000) -> dict[str, Any]:
        """Return one agent-facing markdown doc by ID."""

        return get_doc_tool(doc_id, max_chars=max_chars)

    @server.tool(name="doxabase.graph_overview")
    def graph_overview(limit: int = 100) -> dict[str, Any]:
        """Return named graph counts, common classes, predicates, and key counts."""

        return graph_overview_tool(db, limit=limit)

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

    @server.tool(name="doxabase.describe_context_slice")
    def describe_context_slice(
        seed_iris: list[str],
        profile: str = "dataset_brief",
        max_triples: int = 500,
        include_trig: bool = False,
    ) -> dict[str, Any]:
        """Return a route-explained graph slice around datasets, patterns, or lore."""

        return describe_context_slice_tool(
            db,
            seed_iris=seed_iris,
            profile=profile,
            max_triples=max_triples,
            include_trig=include_trig,
        )

    @server.tool(name="doxabase.describe_resource")
    def describe_resource(
        iri: str,
        graph: str | None = None,
        include_incoming: bool = True,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Return outgoing and incoming RDF triples for one resource."""

        return describe_resource_tool(
            db,
            iri=iri,
            graph=graph,
            include_incoming=include_incoming,
            limit=limit,
        )

    @server.tool(name="doxabase.describe_graph_revision")
    def describe_graph_revision(
        iri: str,
        graph: str | None = "history",
    ) -> dict[str, Any]:
        """Return compact revision metadata, snapshots, and support links."""

        return describe_graph_revision_tool(db, iri=iri, graph=graph)

    @server.tool(name="doxabase.describe_staged_revision")
    def describe_staged_revision(
        iri: str,
        graph: str | None = "history",
    ) -> dict[str, Any]:
        """Return staged revision metadata and patch payloads for review."""

        return describe_staged_revision_tool(db, iri=iri, graph=graph)

    @server.tool(name="doxabase.check_staged_revision_apply")
    def check_staged_revision_apply(
        iri: str,
        validation_scope: str | None = None,
    ) -> dict[str, Any]:
        """Preview whether a staged graph revision can apply cleanly."""

        return check_staged_revision_apply_tool(
            db,
            iri=iri,
            validation_scope=validation_scope,
        )

    @server.tool(name="doxabase.describe_pattern")
    def describe_pattern(
        iri: str,
        graph: str | None = "patterns",
    ) -> dict[str, Any]:
        """Return compact pattern context, support links, and evidence spans."""

        return describe_pattern_tool(db, iri=iri, graph=graph)

    @server.tool(name="doxabase.record_observation")
    def record_observation(
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
        """Record a structured observation, optionally linked to evidence."""

        return record_observation_tool(
            db,
            summary=summary,
            observation_type=observation_type,
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

    @server.tool(name="doxabase.record_claim_observation")
    def record_claim_observation(
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
        """Record an observation with one structured claim, evidence, and optional source span."""

        return record_claim_observation_tool(
            db,
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
        )

    @server.tool(name="doxabase.record_dataset_profile")
    def record_dataset_profile(
        dataset_iri: str,
        summary: str,
        observed_at: str | None = None,
        observed_by: str | None = None,
        evidence_summary: str | None = None,
        evidence_sources: list[str] | None = None,
        sample_size: int | None = None,
        row_count: int | None = None,
        null_count: int | None = None,
        distinct_count: int | None = None,
        update_map_snapshot: bool = True,
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
        """Record a dataset profile observation, optional map snapshot, and pattern."""

        return record_dataset_profile_tool(
            db,
            dataset_iri=dataset_iri,
            summary=summary,
            observed_at=observed_at,
            observed_by=observed_by,
            evidence_summary=evidence_summary,
            evidence_sources=evidence_sources,
            sample_size=sample_size,
            row_count=row_count,
            null_count=null_count,
            distinct_count=distinct_count,
            update_map_snapshot=update_map_snapshot,
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

    @server.tool(name="doxabase.record_column_profile")
    def record_column_profile(
        column_iri: str,
        column_name: str,
        summary: str,
        table_iri: str | None = None,
        observed_at: str | None = None,
        observed_by: str | None = None,
        evidence_summary: str | None = None,
        evidence_sources: list[str] | None = None,
        sample_size: int | None = None,
        row_count: int | None = None,
        null_count: int | None = None,
        distinct_count: int | None = None,
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
        """Record a column profile observation, optional map column, and pattern."""

        return record_column_profile_tool(
            db,
            column_iri=column_iri,
            column_name=column_name,
            summary=summary,
            table_iri=table_iri,
            observed_at=observed_at,
            observed_by=observed_by,
            evidence_summary=evidence_summary,
            evidence_sources=evidence_sources,
            sample_size=sample_size,
            row_count=row_count,
            null_count=null_count,
            distinct_count=distinct_count,
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

    @server.tool(name="doxabase.record_map_dataset")
    def record_map_dataset(
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
        """Record or update a dataset/table resource in the map graph."""

        return record_map_dataset_tool(
            db,
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

    @server.tool(name="doxabase.record_map_column")
    def record_map_column(
        iri: str,
        column_name: str,
        table_iri: str | None = None,
        label: str | None = None,
        description: str | None = None,
        physical_type: str | None = None,
        value_type: str | None = None,
        nullable: bool | None = None,
    ) -> dict[str, Any]:
        """Record or update a column resource in the map graph."""

        return record_map_column_tool(
            db,
            iri=iri,
            column_name=column_name,
            table_iri=table_iri,
            label=label,
            description=description,
            physical_type=physical_type,
            value_type=value_type,
            nullable=nullable,
        )

    @server.tool(name="doxabase.record_map_caveat")
    def record_map_caveat(
        iri: str,
        description: str,
        label: str | None = None,
        impact: str | None = None,
        severity: str | None = None,
        targets: list[str] | None = None,
    ) -> dict[str, Any]:
        """Record or update a known caveat in the map graph."""

        return record_map_caveat_tool(
            db,
            iri=iri,
            description=description,
            label=label,
            impact=impact,
            severity=severity,
            targets=targets,
        )

    @server.tool(name="doxabase.record_map_storage_access")
    def record_map_storage_access(
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
        layout_verification_status: str | None = None,
        layout_verification_note: str | None = None,
        datasets: list[str] | None = None,
    ) -> dict[str, Any]:
        """Record or update non-secret storage access metadata in the map graph."""

        return record_map_storage_access_tool(
            db,
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
            layout_verification_status=layout_verification_status,
            layout_verification_note=layout_verification_note,
            datasets=datasets,
        )

    @server.tool(name="doxabase.record_map_physical_layout")
    def record_map_physical_layout(
        iri: str,
        label: str | None = None,
        description: str | None = None,
        file_format: str | None = None,
        compression_codec: str | None = None,
        layout_verification_status: str | None = None,
        layout_verification_note: str | None = None,
        datasets: list[str] | None = None,
    ) -> dict[str, Any]:
        """Record or update physical layout metadata in the map graph."""

        return record_map_physical_layout_tool(
            db,
            iri=iri,
            label=label,
            description=description,
            file_format=file_format,
            compression_codec=compression_codec,
            layout_verification_status=layout_verification_status,
            layout_verification_note=layout_verification_note,
            datasets=datasets,
        )

    @server.tool(name="doxabase.record_map_partition_scheme")
    def record_map_partition_scheme(
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
        """Record or update partition scheme metadata in the map graph."""

        return record_map_partition_scheme_tool(
            db,
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

    @server.tool(name="doxabase.record_map_relationship")
    def record_map_relationship(
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
        """Record or update a relationship resource in the map graph."""

        return record_map_relationship_tool(
            db,
            iri=iri,
            relationship_type=relationship_type,
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

    @server.tool(name="doxabase.search")
    def search(
        query: str,
        graph: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Lexically search literal RDF claims and return matched resources."""

        return search_tool(
            db,
            query=query,
            graph=graph,
            limit=limit,
            offset=offset,
        )

    @server.tool(name="doxabase.import_trig")
    def import_trig(path: str, replace: bool = False) -> dict[str, Any]:
        """Import a TriG file into DoxaBase graph roles."""

        return import_trig_tool(db, path=path, replace=replace)

    @server.tool(name="doxabase.export_graph")
    def export_graph(
        path: str,
        graphs: list[str] | None = None,
        format: str = "turtle",
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Export one or more graph roles as a flattened RDF graph file."""

        return export_graph_tool(
            db,
            path=path,
            graphs=graphs,
            format=format,
            overwrite=overwrite,
        )

    @server.tool(name="doxabase.export_trig")
    def export_trig(
        path: str,
        graphs: list[str] | None = None,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Export graph roles as a named-graph TriG bundle."""

        return export_trig_tool(
            db,
            path=path,
            graphs=graphs,
            overwrite=overwrite,
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

    @server.tool(name="doxabase.stage_graph_revision")
    def stage_graph_revision(
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
        review_note: str | None = None,
        review_recommendation: str | None = None,
        validation_scope: str = "all",
    ) -> dict[str, Any]:
        """Record a reviewable staged graph revision without applying it."""

        return stage_graph_revision_tool(
            db,
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
            review_note=review_note,
            review_recommendation=review_recommendation,
            validation_scope=validation_scope,
        )

    @server.tool(name="doxabase.stage_systematisation")
    def stage_systematisation(
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
        """Stage one or more caller-authored RDF framings for a systematisation."""

        return stage_systematisation_tool(
            db,
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
            validation_scope=validation_scope,
        )

    @server.tool(name="doxabase.stage_pattern_promotion")
    def stage_pattern_promotion(
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
        """Stage graph changes supported by existing patterns."""

        return stage_pattern_promotion_tool(
            db,
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
            validation_scope=validation_scope,
        )

    @server.tool(name="doxabase.export_staged_revision")
    def export_staged_revision(
        iri: str,
        path: str,
        format: str = "markdown",
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Export a staged revision review bundle."""

        return export_staged_revision_tool(
            db,
            iri=iri,
            path=path,
            format=format,
            overwrite=overwrite,
        )

    @server.tool(name="doxabase.apply_staged_revision")
    def apply_staged_revision(
        iri: str,
        applied_revision_iri: str | None = None,
        created_at: str | None = None,
        created_by: str | None = None,
        allow_validation_failure: bool = False,
        validation_scope: str | None = None,
    ) -> dict[str, Any]:
        """Apply a staged graph revision after conflict and validation checks."""

        return apply_staged_revision_tool(
            db,
            iri=iri,
            applied_revision_iri=applied_revision_iri,
            created_at=created_at,
            created_by=created_by,
            allow_validation_failure=allow_validation_failure,
            validation_scope=validation_scope,
        )

    @server.tool(name="doxabase.export_staged_revisions")
    def export_staged_revisions(
        revision_iris: list[str],
        path: str,
        title: str | None = None,
        executive_summary: str | None = None,
        format: str = "markdown",
        overwrite: bool = False,
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
