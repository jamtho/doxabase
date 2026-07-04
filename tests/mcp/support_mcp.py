"""Shared imports, constants, and helpers for the split test_mcp_tools.py suite."""

import json

import inspect

from pathlib import Path

import pytest

from rdflib.namespace import XSD

import doxabase.mcp_tools as mcp_tools

from doxabase import DoxaBase, DoxaBaseError, to_dict

from doxabase.mcp_server import build_server

from doxabase.mcp_tools import (
    apply_staged_revision_tool,
    check_staged_revision_apply_tool,
    describe_applied_revision_diff_tool,
    get_context_graph_tool,
    describe_dataset_tool,
    describe_graph_revision_tool,
    describe_graph_version_diff_tool,
    describe_query_context_tool,
    describe_revision_graph_snapshot_tool,
    describe_revision_lineage_tool,
    describe_resource_revision_lineage_tool,
    describe_resource_tool,
    describe_revision_snapshot_evidence_tool,
    describe_revision_tool,
    describe_staged_revision_recovery_session_tool,
    describe_staged_revision_tool,
    draft_map_assertion_change_tool,
    draft_query_evidence_storage_overlay_tool,
    draft_profile_map_updates_tool,
    draft_staged_revision_rebase_tool,
    draft_systematisation_shared_context_rerun_tool,
    export_bundle_tool,
    export_context_slice_tool,
    export_graph_tool,
    export_handoff_bundle_tool,
    export_preflight_tool,
    export_profile_insight_review_bundle_tool,
    export_revision_snapshots_tool,
    export_staged_revision_tool,
    export_staged_revisions_tool,
    export_trig_tool,
    get_doc_tool,
    graph_overview_tool,
    import_bundle_tool,
    import_handoff_bundle_tool,
    import_revision_snapshots_tool,
    import_trig_tool,
    list_entities_tool,
    list_graph_revisions_tool,
    list_graph_versions_tool,
    list_resource_revisions_tool,
    list_revisions_tool,
    load_example_fixtures_tool,
    plan_profile_followthrough_tool,
    plan_staged_revision_recovery_tool,
    preflight_context_slice_export_tool,
    project_brief_tool,
    record_analysis_packet_tool,
    record_claim_observation_tool,
    record_claim_reconsideration_tool,
    record_column_profile_tool,
    record_dataset_profile_tool,
    record_domain_network_profile_tool,
    record_map_analysis_view_bundle_tool,
    record_map_analysis_view_tool,
    record_map_asset_transform_tool,
    record_map_caveat_tool,
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
    record_staged_revision_review_decision_tool,
    record_observation_tool,
    record_profile_tool,
    record_map_fact_tool,
    record_pattern_tool,
    record_query_result_tool,
    record_profile_bundle_tool,
    restage_staged_revision_tool,
    restage_staged_revisions_tool,
    scan_sensitive_literals_tool,
    search_tool,
    stage_graph_revision_tool,
    stage_revision_tool,
    stage_query_physical_layout_repair_tool,
    stage_query_storage_access_repair_tool,
    stage_map_assertion_change_tool,
    stage_pattern_promotion_tool,
    stage_profile_map_updates_tool,
    stage_systematisation_tool,
    start_staged_revision_recovery_session_tool,
    validate_graph_tool,
)

RC = "https://richcanopy.org/ns/rc#"

def _delete_base_ontology_seed_terms(db: DoxaBase, terms: list[str]) -> None:
    for term in terms:
        iri = db.expand_iri(term)
        db._conn.execute(
            """
            DELETE FROM quads
            WHERE graph = 'base_ontology'
              AND (subject = ? OR object = ?)
            """,
            (iri, iri),
        )
    db._conn.commit()

def _line_number_containing(text: str, needle: str) -> int:
    for line_number, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return line_number
    raise AssertionError(f"Expected text to contain {needle!r}")

def _assert_repair_action_option(
    option: dict[str, object],
    *,
    action_index: int,
    action_type: str,
    tool: str,
    required_extra_arguments: list[str],
    placeholder_fields: list[str],
    reviewed_value_fields: list[str],
    action_status: str = "pending_review",
) -> None:
    assert option["action_index"] == action_index
    assert option["action_type"] == action_type
    assert option["tool"] == tool
    assert option["action_status"] == action_status
    assert option.get("required_extra_arguments", []) == required_extra_arguments
    assert option.get("placeholder_fields", []) == placeholder_fields
    assert option.get("reviewed_value_fields", []) == reviewed_value_fields


__all__ = [
    "json",
    "inspect",
    "Path",
    "pytest",
    "XSD",
    "mcp_tools",
    "DoxaBase",
    "DoxaBaseError",
    "to_dict",
    "build_server",
    "apply_staged_revision_tool",
    "check_staged_revision_apply_tool",
    "describe_applied_revision_diff_tool",
    "get_context_graph_tool",
    "describe_dataset_tool",
    "describe_graph_revision_tool",
    "describe_graph_version_diff_tool",
    "describe_query_context_tool",
    "describe_revision_graph_snapshot_tool",
    "describe_revision_lineage_tool",
    "describe_resource_revision_lineage_tool",
    "describe_resource_tool",
    "describe_revision_snapshot_evidence_tool",
    "describe_revision_tool",
    "describe_staged_revision_recovery_session_tool",
    "describe_staged_revision_tool",
    "draft_map_assertion_change_tool",
    "draft_query_evidence_storage_overlay_tool",
    "draft_profile_map_updates_tool",
    "draft_staged_revision_rebase_tool",
    "draft_systematisation_shared_context_rerun_tool",
    "export_bundle_tool",
    "export_context_slice_tool",
    "export_graph_tool",
    "export_handoff_bundle_tool",
    "export_preflight_tool",
    "export_profile_insight_review_bundle_tool",
    "export_revision_snapshots_tool",
    "export_staged_revision_tool",
    "export_staged_revisions_tool",
    "export_trig_tool",
    "get_doc_tool",
    "graph_overview_tool",
    "import_bundle_tool",
    "import_handoff_bundle_tool",
    "import_revision_snapshots_tool",
    "import_trig_tool",
    "list_entities_tool",
    "list_graph_revisions_tool",
    "list_graph_versions_tool",
    "list_resource_revisions_tool",
    "list_revisions_tool",
    "load_example_fixtures_tool",
    "plan_profile_followthrough_tool",
    "plan_staged_revision_recovery_tool",
    "preflight_context_slice_export_tool",
    "project_brief_tool",
    "record_analysis_packet_tool",
    "record_claim_observation_tool",
    "record_claim_reconsideration_tool",
    "record_column_profile_tool",
    "record_dataset_profile_tool",
    "record_domain_network_profile_tool",
    "record_map_analysis_view_bundle_tool",
    "record_map_analysis_view_tool",
    "record_map_asset_transform_tool",
    "record_map_caveat_tool",
    "record_map_column_tool",
    "record_map_dataset_tool",
    "record_map_table_bundle_tool",
    "record_map_partition_scheme_tool",
    "record_map_physical_layout_tool",
    "record_map_relationship_tool",
    "record_map_storage_access_tool",
    "record_profiled_parquet_table_tool",
    "record_profile_to_capsule_manifest_tool",
    "record_graph_revision_tool",
    "record_staged_revision_review_decision_tool",
    "record_observation_tool",
    "record_profile_tool",
    "record_map_fact_tool",
    "record_pattern_tool",
    "record_query_result_tool",
    "record_profile_bundle_tool",
    "restage_staged_revision_tool",
    "restage_staged_revisions_tool",
    "scan_sensitive_literals_tool",
    "search_tool",
    "stage_graph_revision_tool",
    "stage_revision_tool",
    "stage_query_physical_layout_repair_tool",
    "stage_query_storage_access_repair_tool",
    "stage_map_assertion_change_tool",
    "stage_pattern_promotion_tool",
    "stage_profile_map_updates_tool",
    "stage_systematisation_tool",
    "start_staged_revision_recovery_session_tool",
    "validate_graph_tool",
    "RC",
    "_delete_base_ontology_seed_terms",
    "_line_number_containing",
    "_assert_repair_action_option",
]
