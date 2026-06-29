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
    describe_assertion_support_tool,
    describe_context_slice_tool,
    describe_dataset_tool,
    describe_profile_run_tool,
    describe_graph_revision_tool,
    describe_pattern_tool,
    describe_query_context_tool,
    describe_revision_graph_snapshot_tool,
    describe_revision_lineage_tool,
    describe_resource_revision_lineage_tool,
    describe_resource_tool,
    describe_revision_snapshot_evidence_tool,
    describe_staged_revision_tool,
    draft_map_assertion_change_tool,
    draft_profile_map_updates_tool,
    draft_query_plan_tool,
    draft_staged_revision_rebase_tool,
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
    import_revision_snapshots_tool,
    import_trig_tool,
    list_docs_tool,
    list_entities_tool,
    list_graph_revisions_tool,
    list_resource_revisions_tool,
    load_example_fixtures_tool,
    plan_staged_revision_recovery_tool,
    project_brief_tool,
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
    record_query_result_tool,
    record_profile_bundle_tool,
    replace_graph_triples_tool,
    restage_staged_revision_tool,
    restage_staged_revisions_tool,
    scan_sensitive_literals_tool,
    search_tool,
    stage_graph_revision_tool,
    stage_map_assertion_change_tool,
    stage_pattern_promotion_tool,
    stage_profile_map_updates_tool,
    stage_systematisation_tool,
    validate_graph_tool,
)

RC = "https://richcanopy.org/ns/rc#"


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
    tool_name: str,
    mcp_tool_name: str,
    action_label: str,
    required_extra_arguments: list[str],
    placeholder_fields: list[str],
    reviewed_value_fields: list[str],
    action_status: str = "pending_review",
) -> None:
    assert option["action_index"] == action_index
    assert option["action_type"] == action_type
    assert option["tool_name"] == tool_name
    assert option["mcp_tool_name"] == mcp_tool_name
    assert option["action_label"] == action_label
    assert option["action_status"] == action_status
    assert option["required_extra_arguments"] == required_extra_arguments
    assert option["placeholder_fields"] == placeholder_fields
    assert option["reviewed_value_fields"] == reviewed_value_fields


@pytest.mark.anyio
async def test_build_server_registers_expected_tools(tmp_path: Path) -> None:
    server = build_server(tmp_path / "mcp.sqlite")
    tools = await server.list_tools()
    tool_names = {tool.name for tool in tools}

    assert "doxabase.list_docs" in tool_names
    assert "doxabase.get_doc" in tool_names
    assert "doxabase.graph_overview" in tool_names
    assert "doxabase.scan_sensitive_literals" in tool_names
    assert "doxabase.export_preflight" in tool_names
    assert "doxabase.project_brief" in tool_names
    assert "doxabase.list_entities" in tool_names
    assert "doxabase.describe_dataset" in tool_names
    assert "doxabase.describe_profile_run" in tool_names
    assert "doxabase.draft_profile_map_updates" in tool_names
    assert "doxabase.stage_profile_map_updates" in tool_names
    assert "doxabase.describe_query_context" in tool_names
    assert "doxabase.draft_query_plan" in tool_names
    assert "doxabase.describe_context_slice" in tool_names
    assert "doxabase.describe_resource" in tool_names
    assert "doxabase.describe_graph_revision" in tool_names
    assert "doxabase.describe_revision_snapshot_evidence" in tool_names
    assert "doxabase.describe_revision_graph_snapshot" in tool_names
    assert "doxabase.describe_applied_revision_diff" in tool_names
    assert "doxabase.list_graph_revisions" in tool_names
    assert "doxabase.describe_revision_lineage" in tool_names
    assert "doxabase.list_resource_revisions" in tool_names
    assert "doxabase.describe_resource_revision_lineage" in tool_names
    assert "doxabase.describe_staged_revision" in tool_names
    assert "doxabase.check_staged_revision_apply" in tool_names
    assert "doxabase.draft_staged_revision_rebase" in tool_names
    assert "doxabase.plan_staged_revision_recovery" in tool_names
    assert "doxabase.describe_pattern" in tool_names
    assert "doxabase.record_observation" in tool_names
    assert "doxabase.record_query_result" in tool_names
    assert "doxabase.record_claim_observation" in tool_names
    assert "doxabase.record_claim_reconsideration" in tool_names
    assert "doxabase.record_column_profile" in tool_names
    assert "doxabase.record_dataset_profile" in tool_names
    assert "doxabase.record_profile_bundle" in tool_names
    assert "doxabase.record_pattern" in tool_names
    assert "doxabase.record_map_dataset" in tool_names
    assert "doxabase.record_map_column" in tool_names
    assert "doxabase.record_map_caveat" in tool_names
    assert "doxabase.record_map_storage_access" in tool_names
    assert "doxabase.record_map_physical_layout" in tool_names
    assert "doxabase.record_map_partition_scheme" in tool_names
    assert "doxabase.record_map_relationship" in tool_names
    assert "doxabase.search" in tool_names
    assert "doxabase.export_graph" in tool_names
    assert "doxabase.export_handoff_bundle" in tool_names
    assert "doxabase.export_profile_insight_review_bundle" in tool_names
    assert "doxabase.export_revision_snapshots" in tool_names
    assert "doxabase.import_revision_snapshots" in tool_names
    assert "doxabase.replace_graph_triples" in tool_names
    assert "doxabase.export_staged_revision" in tool_names
    assert "doxabase.export_staged_revisions" in tool_names
    assert "doxabase.export_trig" in tool_names
    assert "doxabase.record_graph_revision" in tool_names
    assert "doxabase.stage_graph_revision" in tool_names
    assert "doxabase.restage_staged_revision" in tool_names
    assert "doxabase.restage_staged_revisions" in tool_names
    assert "doxabase.draft_map_assertion_change" in tool_names
    assert "doxabase.stage_map_assertion_change" in tool_names
    assert "doxabase.stage_systematisation" in tool_names
    assert "doxabase.stage_pattern_promotion" in tool_names
    assert "doxabase.apply_staged_revision" in tool_names
    assert "doxabase.load_example_fixtures" in tool_names
    assert "doxabase.validate_graph" in tool_names

    tool_by_name = {tool.name: tool for tool in tools}
    storage_access_description = (
        tool_by_name["doxabase.record_map_storage_access"].description or ""
    )
    assert "rc:DatabaseStorage" in storage_access_description
    assert "database relation identifiers" in storage_access_description
    assert "storage_root" in storage_access_description


@pytest.mark.anyio
async def test_server_get_doc_serves_query_planning_doc(
    tmp_path: Path,
) -> None:
    server = build_server(tmp_path / "mcp.sqlite")

    _, result = await server.call_tool(
        "doxabase.get_doc",
        {"doc_id": "query_planning", "max_chars": 80},
    )

    assert result["id"] == "query_planning"
    assert result["title"] == "Query Planning"
    assert result["content"].startswith("# Query Planning")


@pytest.mark.anyio
async def test_profile_mcp_tools_expose_sampled_snapshot_gate(
    tmp_path: Path,
) -> None:
    server = build_server(tmp_path / "mcp.sqlite")
    tools = {tool.name: tool for tool in await server.list_tools()}

    for tool_name in (
        "doxabase.record_dataset_profile",
        "doxabase.record_profile_bundle",
    ):
        properties = tools[tool_name].inputSchema["properties"]

        assert "allow_sampled_row_count_snapshot" in properties
        assert properties["allow_sampled_row_count_snapshot"]["default"] is False
        assert properties["allow_sampled_row_count_snapshot"]["type"] == "boolean"


@pytest.mark.anyio
async def test_mcp_tool_schemas_match_tool_layer_signatures(
    tmp_path: Path,
) -> None:
    server = build_server(tmp_path / "mcp.sqlite")
    mismatches: dict[str, dict[str, list[str]]] = {}

    for tool in await server.list_tools():
        short_name = tool.name.removeprefix("doxabase.")
        tool_func = getattr(mcp_tools, f"{short_name}_tool", None)
        if tool_func is None:
            continue
        tool_parameters = [
            name
            for name in inspect.signature(tool_func).parameters
            if name != "db"
        ]
        schema_properties = list(tool.inputSchema.get("properties", {}))
        missing = [
            name for name in tool_parameters if name not in schema_properties
        ]
        extra = [
            name for name in schema_properties if name not in tool_parameters
        ]
        if missing or extra:
            mismatches[tool.name] = {"missing": missing, "extra": extra}

    assert mismatches == {}


def test_doc_tools_return_json_like_payloads() -> None:
    result = list_docs_tool()
    doc_ids = {doc["id"] for doc in result["docs"]}
    response_shapes_doc = next(
        doc for doc in result["docs"] if doc["id"] == "response_shapes"
    )

    assert result["docs"][0]["id"] == "start_here"
    assert "start_here" in doc_ids
    assert "overview" in doc_ids
    assert "graph_roles" in doc_ids
    assert "response_shapes" in doc_ids
    assert "profiling" in doc_ids
    assert "systematisation" in doc_ids
    assert response_shapes_doc["size_chars"] > 0
    assert {
        section["anchor"]
        for section in response_shapes_doc["sections"]
    } >= {
        "profile-helper-records",
        "dataset-storage-and-layout",
        "linked-pattern-reasons",
        "query-context",
        "draft-query-plan",
        "staged-detail-and-current-apply-summary",
        "apply-check-patch-checks-and-snapshot-drift",
        "validation-diagnostics",
        "staged-revisions",
    }

    section = get_doc_tool(
        "response_shapes",
        section="Profile Helper Records",
        max_chars=300,
    )
    assert section["selected_section"]["anchor"] == "profile-helper-records"
    assert section["start_char"] == section["selected_section"]["start_char"]
    assert section["content"].startswith("## Profile Helper Records")
    assert section["truncated"] is True

    offset = get_doc_tool(
        "response_shapes",
        start_char=section["end_char"],
        max_chars=120,
    )
    assert offset["start_char"] == section["end_char"]
    assert len(offset["content"]) <= 120
    assert offset["selected_section"]["anchor"] == "profile-helper-records"

    nested_section = get_doc_tool(
        "response_shapes",
        section="Apply Check, Patch Checks, And Snapshot Drift",
        max_chars=300,
    )
    assert nested_section["selected_section"]["anchor"] == (
        "apply-check-patch-checks-and-snapshot-drift"
    )
    assert nested_section["content"].startswith(
        "### Apply Check, Patch Checks, And Snapshot Drift"
    )


def test_fixture_loading_and_validation_tools(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    load_result = load_example_fixtures_tool(db)
    overview = graph_overview_tool(db)
    tables = list_entities_tool(db, type="rc:Table", graph="map")
    validation = validate_graph_tool(db, scope="all")

    assert load_result["total_imported"] == 805
    assert load_result["totals"]["patterns"] == 14
    assert overview["key_counts"]["tables"] >= 7
    assert overview["key_counts"]["patterns"] >= 1
    assert tables["count"] >= 7
    assert validation["conforms"] is True

    support = describe_assertion_support_tool(
        db,
        subject="https://richcanopy.org/example/manifest/polymarket#px_price",
        predicate="rc:physicalType",
        object="rc:Varchar",
    )

    assert support["related_observations"][0]["iri"] == (
        "https://richcanopy.org/example/manifest/polymarket#"
        "obs_price_payload_caveat_from_manifest"
    )
    assert support["related_claims"][0]["iri"] == (
        "https://richcanopy.org/example/manifest/polymarket#"
        "claim_price_payload_requires_filtering"
    )

    assert support["related_patterns"][0]["iri"] == (
        "https://richcanopy.org/example/manifest/polymarket#"
        "pattern_price_payload_boundary"
    )
    assert support["related_evidence"][0]["iri"] == (
        "https://richcanopy.org/example/manifest/polymarket#"
        "evidence_price_payload_caveat_manifest"
    )
    route_types = {route["route_type"] for route in support["related_routes"]}
    assert "observed_column" in route_types
    assert "claim_target" in route_types
    assert "pattern_target" in route_types
    assert "supporting_claim" in route_types
    summary_by_kind = {
        summary["resource_kind"]: summary
        for summary in support["related_route_summaries"]
    }
    assert summary_by_kind["claim"]["strongest_route_type"] == "claim_target"
    assert "claim target" in summary_by_kind["claim"]["route_labels"]
    assert summary_by_kind["pattern"]["route_count"] >= 2

    token_support = describe_assertion_support_tool(
        db,
        subject="https://richcanopy.org/example/manifest/polymarket#px_token_id",
        predicate="rc:physicalType",
        object="rc:Double",
    )

    assert token_support["assertion_present"] is False
    assert "Current same-subject/predicate value(s): VARCHAR" in (
        token_support["absence_note"]
    )
    assert token_support["related_route_summaries"] == []
    mixed_price_links = [
        link
        for link in token_support["nearby_caveat_links"]
        if link["caveat"]["iri"]
        == "https://richcanopy.org/example/manifest/polymarket#caveat_mixed_type_price"
    ]
    assert len(mixed_price_links) == 1
    assert mixed_price_links[0]["scope"] == "owner_dataset"
    assert mixed_price_links[0]["route_type"] == "owner_dataset_has_known_caveat"
    assert mixed_price_links[0]["via_resource"]["iri"] == (
        "https://richcanopy.org/example/manifest/polymarket#PriceSnapshots"
    )
    assert mixed_price_links[0]["matched_resource"]["iri"] == (
        "https://richcanopy.org/example/manifest/polymarket#px_token_id"
    )


def test_project_brief_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)

    result = project_brief_tool(db, limit=3, profile_candidate_limit=1)

    assert result["dataset_count"] >= 3
    assert result["returned_dataset_count"] == 3
    assert result["limit"] == 3
    assert result["profile_candidate_limit"] == 1
    assert result["key_counts"]["tables"] >= 7
    assert result["datasets"]
    assert result["datasets"][0]["dataset"]["iri"].startswith("https://")
    assert "readiness" in result["datasets"][0]["query"]
    assert "profile_run_candidate_count" in result["datasets"][0]["profile"]
    assert "draft_candidate_count" in result["datasets"][0]["profile"]
    assert "profile_candidate_omitted_count" in result["datasets"][0]["profile"]
    assert "omitted_draft_evidence_iris" in result["datasets"][0]["profile"]
    assert "returned_dataset_query_readiness_counts" in result
    assert "profile_queue_counts" in result
    assert "profile_draft_candidates" in result["profile_queue_counts"]
    assert "profile_candidate_omitted" in result["profile_queue_counts"]
    assert "queue_counts" in result
    assert "returned_queue_counts" in result
    assert "omitted_queue_counts" in result
    assert "active_queue_type_count" in result
    assert "returned_queue_type_count" in result
    assert "limit_crowded_queue_types" in result
    assert "health_tasks" in result
    assert isinstance(result["health_tasks"], list)
    assert "next_best_expansion" in result
    assert "full_frontier_expansion" in result
    if result["next_best_expansion"] is not None:
        assert result["next_best_expansion"]["task_type"] in {
            "expand_project_brief",
            "expand_profile_candidate_limit",
        }
    for task in result["health_tasks"]:
        assert "exhaustive_suggested_limit" in task
        assert "suggested_profile_candidate_limit" in task
        assert "profile_candidate_omitted_count" in task
    for task in result["recommended_next_tasks"]:
        assert "query_plan_handoff_summary" in task
    assert isinstance(result["recommended_next_tasks"], list)


def test_project_brief_tool_routes_query_repair_tasks_to_context(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(dataset, label="Orders", is_table=True)

    result = project_brief_tool(db, limit=1)

    repair_task = result["recommended_next_tasks"][0]
    assert repair_task["task_type"] == "query_repair_review"
    assert repair_task["source"] == "describe_query_context"
    assert repair_task["suggested_next_action"]["tool_name"] == (
        "describe_query_context"
    )
    assert repair_task["suggested_next_action"]["arguments"] == {"iri": dataset}
    assert repair_task["suggested_next_call"] == (
        "describe_query_context(iri='https://example.test/project#Orders')"
    )


def test_project_brief_tool_routes_blocked_context_tasks_to_context_review(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#LocationBlockedEvents"
    storage = db.record_map_storage_access(
        "https://example.test/project#LocationBlockedEventsStorage",
        label="Location-blocked local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#LocationBlockedEventsLayout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Location-blocked events",
        is_table=True,
        path_templates=["events/location-blocked/*.parquet"],
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    result = project_brief_tool(db, limit=5)

    context_action = result["datasets"][0]["query"]["suggested_next_actions"][0]
    assert context_action["tool_name"] == "draft_query_plan"
    context_task = result["recommended_next_tasks"][0]
    assert context_task["task_type"] == "query_context_review"
    assert context_task["source"] == "describe_query_context"
    assert context_task["suggested_next_action"]["tool_name"] == (
        "describe_query_context"
    )
    assert context_task["suggested_next_action"]["arguments"] == {"iri": dataset}
    assert context_task["suggested_next_call"] == (
        "describe_query_context("
        "iri='https://example.test/project#LocationBlockedEvents')"
    )


def test_project_brief_tool_routes_ready_query_handoffs_to_draft_plan(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#OrdersLocalStorage",
        label="Orders local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="object",
        storage_root=str(tmp_path / "orders.parquet"),
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#OrdersParquetLayout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Orders",
        is_table=True,
        storage_accesses=[storage["iri"]],
        physical_layouts=[layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    result = project_brief_tool(db, limit=5)

    assert result["queue_counts"] == {"query_plan_handoff": 1}
    task = result["recommended_next_tasks"][0]
    assert task["task_type"] == "query_plan_handoff"
    assert task["source"] == "draft_query_plan"
    assert task["suggested_next_action"]["tool_name"] == "draft_query_plan"
    assert task["suggested_next_action"]["arguments"] == {
        "iri": dataset,
        "candidate_index": 0,
    }


def test_project_brief_tool_marks_pending_staged_query_repairs(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    relation = "mart.orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_database_storage",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        path_templates=[relation],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#orders_table_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        path_templates=[relation],
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    repair_group = db.describe_query_context(
        dataset,
    ).suggested_repair_action_groups[0]
    remove_arguments = dict(repair_group.actions[0]["arguments"])
    remove_arguments["rationale"] = (
        "Reviewed dataset path template as misplaced database relation metadata."
    )
    staged = db.stage_map_assertion_change(**remove_arguments)

    result = project_brief_tool(db, limit=3)

    assert result["staged_review"]["items"][0]["revision_anchor_iris"] == [dataset]
    assert [
        task["task_type"] for task in result["recommended_next_tasks"]
    ] == ["staged_frontier_review", "staged_review", "query_repair_review"]
    frontier_task = result["recommended_next_tasks"][0]
    assert frontier_task["suggested_next_action"]["tool_name"] == (
        "plan_staged_revision_recovery"
    )
    repair_task = result["recommended_next_tasks"][2]
    assert repair_task["pending_staged_repair_iris"] == [staged.revision_iri]
    assert "Pending staged repair(s)" in repair_task["reason"]


def test_project_brief_tool_does_not_gate_query_repair_on_unrelated_staged_work(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Tickets"
    db.record_map_dataset(dataset, label="Tickets", is_table=True)
    staged = stage_graph_revision_tool(
        db,
        summary="Stage Tickets caveat wording",
        rationale="Unrelated caveat wording should not count as a query repair.",
        additions=[
            {
                "graph": "map",
                "content": """
                @prefix ex: <https://example.test/project#> .
                @prefix rc: <https://richcanopy.org/ns/rc#> .
                @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                ex:TicketsFreshnessCaveat a rc:KnownCaveat ;
                    rdfs:label "Tickets freshness caveat" ;
                    rc:caveatDescription "Tickets freshness needs review." .

                ex:Tickets rc:hasKnownCaveat ex:TicketsFreshnessCaveat .
                """,
            }
        ],
        revision_anchors=[dataset],
    )

    result = project_brief_tool(db, limit=3)

    assert [
        task["task_type"] for task in result["recommended_next_tasks"]
    ] == ["staged_frontier_review", "staged_review", "query_repair_review"]
    repair_task = result["recommended_next_tasks"][2]
    assert repair_task["priority"] == 10
    assert repair_task["pending_staged_repair_iris"] == []
    assert "Pending staged repair(s)" not in repair_task["reason"]
    assert repair_task["suggested_next_action"]["tool_name"] == (
        "describe_query_context"
    )
    assert staged["revision_iri"] in {
        item["revision_iri"] for item in result["staged_review"]["items"]
    }


def test_project_brief_tool_gates_duplicate_profile_staging(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersProfileEvidence"
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#orders_local_storage",
        label="Orders local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="directory",
        storage_root=str(tmp_path / "warehouse"),
        path_templates=["orders/current.csv"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#orders_csv_layout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=10,
        storage_accesses=[storage["iri"]],
        physical_layouts=[layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_profile_bundle_tool(
        db,
        dataset_iri=dataset,
        dataset_summary="Orders were profiled with a full scan.",
        evidence_summary="Orders full-profile evidence.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        sample_size=12,
        sample_scope="All rows in the local Orders table.",
        sample_method="DuckDB full-table profile.",
        row_count=12,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
    )
    draft = draft_profile_map_updates_tool(db, dataset, evidence)
    staged = stage_profile_map_updates_tool(
        db,
        dataset,
        evidence,
        accepted_recommendation_indexes=(
            draft["representative_recommendation_indexes"]
        ),
    )

    result = project_brief_tool(db, limit=3, profile_candidate_limit=1)

    assert [
        task["task_type"] for task in result["recommended_next_tasks"]
    ] == ["staged_frontier_review", "staged_review", "profile_review"]
    frontier_task, staged_task, profile_task = result["recommended_next_tasks"]
    assert frontier_task["suggested_next_action"]["tool_name"] == (
        "plan_staged_revision_recovery"
    )
    assert staged_task["resource"]["iri"] == staged["staged_revision"]["revision_iri"]
    assert profile_task["pending_staged_profile_update_iris"] == [
        staged["staged_revision"]["revision_iri"]
    ]
    assert profile_task["profile_evidence_iri"] == evidence
    assert "Pending staged profile update(s)" in profile_task["reason"]
    assert profile_task["suggested_next_action"]["tool_name"] == (
        "draft_profile_map_updates"
    )
    assert profile_task["suggested_next_action"]["arguments"] == {
        "dataset_iri": dataset,
        "evidence_iri": evidence,
    }


def test_project_brief_tool_keeps_profile_advisories_visible_with_pending_map_update(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#SupportEvents"
    evidence = "https://example.test/project#SupportEventsProfileEvidence"
    metric = "https://example.test/project#SupportCompletenessMetric"
    storage = record_map_storage_access_tool(
        db,
        "https://example.test/project#SupportEventsStorage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="directory",
        storage_root=str(tmp_path / "warehouse"),
        path_templates=["support-events.csv"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#SupportEventsLayout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        db,
        dataset,
        label="Support events",
        is_table=True,
        row_count_snapshot=10,
        storage_accesses=[storage["iri"]],
        physical_layouts=[layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_profile_bundle_tool(
        db,
        dataset_iri=dataset,
        dataset_summary="Support events were profiled with a full scan.",
        evidence_summary="Support events profile evidence.",
        evidence_sources=["test://support-events-profile"],
        shared_evidence_iri=evidence,
        sample_size=12,
        sample_scope="All rows in the local Support events table.",
        sample_method="DuckDB full-table profile.",
        row_count=12,
        profile_metrics=[
            {
                "metric": metric,
                "target": dataset,
                "value": "0.9",
                "datatype": "xsd:decimal",
            }
        ],
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
    )
    draft = draft_profile_map_updates_tool(db, dataset, evidence)
    staged = stage_profile_map_updates_tool(
        db,
        dataset,
        evidence,
        accepted_recommendation_indexes=(
            draft["representative_recommendation_indexes"]
        ),
    )

    result = project_brief_tool(db, limit=3, profile_candidate_limit=1)

    assert draft["recommendation_count"] >= 1
    assert draft["metric_advisory_count"] == 1
    assert [
        task["task_type"] for task in result["recommended_next_tasks"]
    ] == ["staged_frontier_review", "staged_review", "profile_review"]
    profile_task = result["recommended_next_tasks"][2]
    assert profile_task["pending_staged_profile_update_iris"] == [
        staged["staged_revision"]["revision_iri"]
    ]
    assert "profile advisory/conflict lanes remain open" in profile_task["reason"]
    assert profile_task["suggested_next_action"]["tool_name"] == (
        "draft_profile_map_updates"
    )


def test_project_brief_tool_does_not_gate_profile_on_unrelated_staged_work(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersProfileEvidence"
    metric = "https://example.test/project#OrdersQualityMetric"
    storage = record_map_storage_access_tool(
        db,
        "https://example.test/project#OrdersStorage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="object",
        storage_root="/tmp/orders.csv",
        path_templates=["orders.csv"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    record_map_dataset_tool(
        db,
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=10,
        path_templates=["orders.csv"],
        storage_accesses=[storage["iri"]],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    record_profile_bundle_tool(
        db,
        dataset_iri=dataset,
        dataset_summary="Orders were profiled with a full scan.",
        evidence_summary="Orders full-profile evidence.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        sample_size=10,
        sample_scope="All rows in the local Orders table.",
        sample_method="DuckDB full-table profile.",
        row_count=10,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": metric,
                "target": dataset,
                "value": "1",
                "datatype": "xsd:decimal",
            }
        ],
        column_defaults={"update_map_column": False},
    )
    staged = stage_graph_revision_tool(
        db,
        summary="Stage auxiliary Orders caveat",
        rationale=(
            "This revision shares the profile evidence but is not a "
            "profile-map-update revision."
        ),
        additions=[
            {
                "graph": "map",
                "content": """
                @prefix ex: <https://example.test/project#> .
                @prefix rc: <https://richcanopy.org/ns/rc#> .
                @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                ex:OrdersAuxCaveat a rc:KnownCaveat ;
                    rdfs:label "Orders auxiliary caveat" ;
                    rc:caveatDescription "Auxiliary staged work." .

                ex:Orders rc:hasKnownCaveat ex:OrdersAuxCaveat .
                """,
            }
        ],
        revision_anchors=[dataset],
        evidence=[evidence],
    )

    result = project_brief_tool(db, limit=4, profile_candidate_limit=1)

    assert [
        task["task_type"] for task in result["recommended_next_tasks"]
    ] == [
        "staged_frontier_review",
        "staged_review",
        "query_repair_review",
        "profile_review",
    ]
    profile_task = result["recommended_next_tasks"][3]
    assert profile_task["profile_evidence_iri"] == evidence
    assert profile_task["pending_staged_profile_update_iris"] == []
    assert "Pending staged profile update(s)" not in profile_task["reason"]
    assert profile_task["suggested_next_action"]["tool_name"] == (
        "describe_context_slice"
    )
    assert profile_task["suggested_next_action"]["source_profile_advisory"][
        "review_lane"
    ] == "metric_vocabulary_review"
    assert staged["revision_iri"] in {
        item["revision_iri"] for item in result["staged_review"]["items"]
    }


def test_query_storage_frontier_tool_route_regression(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/project#"
    non_table_asset = f"{base}DesignNotesArchive"
    orders = f"{base}Orders"
    orphan = f"{base}OrphanEvents"
    relation = "mart.orders"
    warehouse_storage = record_map_storage_access_tool(
        db,
        iri=f"{base}orders_database_storage",
        label="Orders database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        path_templates=[relation],
        endpoint_profile="warehouse-prod",
        credential_reference="profile:warehouse-readonly",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    archive_storage = record_map_storage_access_tool(
        db,
        iri=f"{base}orphan_archive_storage",
        label="Orphan archive storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(tmp_path / "warehouse"),
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = record_map_physical_layout_tool(
        db,
        iri=f"{base}orders_table_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        db,
        iri=non_table_asset,
        label="Design notes archive",
        is_table=False,
        extra_types=[f"{base}DocumentArchive"],
    )
    record_map_dataset_tool(
        db,
        iri=orders,
        label="Orders",
        is_table=True,
        path_templates=[relation],
        storage_accesses=[warehouse_storage["iri"]],
        physical_layouts=[layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(db, iri=orphan, label="Orphan events", is_table=True)

    non_table_brief = project_brief_tool(db, limit=5)
    non_table_task = next(
        task
        for task in non_table_brief["recommended_next_tasks"]
        if task["resource"] and task["resource"]["iri"] == non_table_asset
    )
    assert non_table_task["task_type"] == "non_tabular_asset_review"
    assert non_table_task["suggested_next_action"]["tool_name"] == (
        "describe_context_slice"
    )

    orphan_context = describe_query_context_tool(db, iri=orphan)
    missing_storage_group = next(
        group
        for group in orphan_context["suggested_repair_action_groups"]
        if group["issue_code"] == "missing_storage_access"
    )
    assert missing_storage_group["repair_action_type"] == (
        "record_or_link_storage_access"
    )
    assert missing_storage_group["action_status_counts"] == {"pending_review": 2}
    assert {
        action["action_type"] for action in missing_storage_group["actions"]
    } == {
        "record_reviewed_storage_access",
        "stage_existing_storage_access_link",
    }
    candidate_storage_iris = {
        candidate["storage_access"]["iri"]
        for candidate in missing_storage_group["repair_context"][
            "candidate_existing_storage_accesses"
        ]
    }
    assert archive_storage["iri"] in candidate_storage_iris

    context = describe_query_context_tool(db, iri=orders)
    relation_candidate_index = next(
        index
        for index, candidate in enumerate(context["query_target_candidates"])
        if candidate["relation_identifier"] == relation
    )
    mismatch_group = next(
        group
        for group in context["suggested_repair_action_groups"]
        if group["issue_code"] == "database_relation_template_source_mismatch"
    )
    action_by_type = {
        action["action_type"]: action for action in mismatch_group["actions"]
    }
    assert mismatch_group["action_status_counts"] == {
        "pending_review": 1,
        "already_satisfied": 1,
    }
    assert action_by_type["add_reviewed_relation_template"]["action_status"] == (
        "already_satisfied"
    )
    assert action_by_type["remove_misplaced_source_template"][
        "required_extra_arguments"
    ] == ["rationale"]
    remove_arguments = dict(
        action_by_type["remove_misplaced_source_template"]["arguments"]
    )
    remove_arguments["rationale"] = (
        "Reviewed dataset path template as misplaced database relation metadata."
    )
    staged = stage_map_assertion_change_tool(db, **remove_arguments)

    brief = project_brief_tool(db, limit=5)
    staged_task_index = next(
        index
        for index, task in enumerate(brief["recommended_next_tasks"])
        if task["task_type"] == "staged_review"
        and task["resource"]
        and task["resource"]["iri"] == staged["revision_iri"]
    )
    query_task_index, query_task = next(
        (index, task)
        for index, task in enumerate(brief["recommended_next_tasks"])
        if task["task_type"] == "query_repair_review"
        and task["pending_staged_repair_iris"] == [staged["revision_iri"]]
    )
    assert staged_task_index < query_task_index
    assert query_task["pending_staged_repair_iris"] == [staged["revision_iri"]]
    assert query_task["suggested_next_action"]["tool_name"] == (
        "describe_query_context"
    )

    allowed_plan = draft_query_plan_tool(
        db,
        iri=orders,
        candidate_index=relation_candidate_index,
        allow_context_blocked_candidate=True,
    )
    assert allowed_plan["scan"]["relation_identifier"] == relation
    assert allowed_plan["scan"]["connection_reference"] == "warehouse-prod"
    assert allowed_plan["scan"]["uri_template"] is None
    assert allowed_plan["handoff_kind"] == "database_relation_handoff"
    assert allowed_plan["review_gate"]["ready_for_execution_attempt"] is False


def test_project_brief_tool_serializes_hidden_staged_review_counts(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    for index in range(3):
        db.stage_graph_revision(
            summary=f"Stage review bundle item {index}",
            rationale="The MCP project brief should expose hidden staged work.",
            additions=[
                {
                    "graph": "map",
                    "content": f"""
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:McpCaveat{index} a rc:KnownCaveat ;
                        rdfs:label "MCP caveat {index}" ;
                        rc:caveatDescription "Synthetic caveat {index}." .
                    """,
                }
            ],
        )

    result = project_brief_tool(db, limit=1)

    assert result["staged_review"]["count"] == 3
    assert result["staged_review"]["returned_count"] == 1
    assert result["staged_review"]["omitted_count"] == 2
    assert result["queue_counts"]["staged_frontier_review"] == 1
    assert result["queue_counts"]["staged_review"] == 3
    assert result["returned_queue_counts"]["staged_frontier_review"] == 1
    assert result["omitted_queue_counts"]["staged_review"] == 3


def test_record_query_result_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    result = record_query_result_tool(
        db,
        summary="Scratch query result returned three rows.",
        observed_asset="https://example.test/project#Orders",
        execution_status="succeeded",
        engine="python-csv",
        query_source_path="queries/orders.sql",
        result_sources=["/tmp/orders-result.json"],
        sample_size=3,
        sample_scope="All rows in the scratch Orders CSV.",
        sample_method="External read-only query.",
        row_count=3,
    )

    assert result["observation_type"] == "profile"
    assert result["execution_status"] == "succeeded"
    assert result["engine"] == "python-csv"
    assert result["evidence_iri"].startswith(
        "https://richcanopy.org/doxabase/generated/evidence/"
    )
    assert result["source_span_iri"].startswith(
        "https://richcanopy.org/doxabase/generated/source-span/"
    )
    assert result["source_span_triples"] > 0


def test_describe_query_context_tool_routes_singleton_query_result_evidence(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    csv_path = tmp_path / "orders.csv"
    csv_path.write_text("order_id,status,amount\n1,paid,12.00\n", encoding="utf-8")
    result_path = tmp_path / "orders-paid-aggregate.json"
    result_path.write_text('{"paid_order_count": 1}\n', encoding="utf-8")
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_csv_storage",
        label="Orders CSV storage",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        location_kind="object",
        storage_root=str(csv_path),
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#orders_csv_layout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    result = record_query_result_tool(
        db,
        summary="Orders paid aggregate scanned the scratch CSV.",
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path="queries/orders_paid_aggregate.sql",
        query_hash="sha256:abc123",
        result_sources=[str(result_path)],
        sample_size=1,
        sample_scope="All rows in the scratch Orders CSV.",
        sample_method="External read-only aggregate query.",
        row_count=1,
    )

    context = describe_query_context_tool(db, iri=dataset)

    assert context["profile_summary"]["evidence_iris"] == [result["evidence_iri"]]
    assert context["profile_summary"]["profile_run_candidates"] == []
    assert [
        action["tool_name"] for action in context["suggested_next_actions"][:2]
    ] == [
        "describe_profile_run",
        "draft_query_plan",
    ]
    profile_action = context["suggested_next_actions"][0]
    assert profile_action["action_label"] == "Inspect singleton profile evidence"
    assert profile_action["arguments"] == {
        "dataset_iri": dataset,
        "evidence_iri": result["evidence_iri"],
    }
    source_profile_evidence = profile_action["source_profile_evidence"]
    assert source_profile_evidence["execution_status"] == "succeeded"
    assert source_profile_evidence["engine"] == "python-csv"
    assert source_profile_evidence["query_hash"] == "sha256:abc123"
    assert source_profile_evidence["query_source_paths"] == [
        "queries/orders_paid_aggregate.sql"
    ]
    assert source_profile_evidence["result_sources"] == [str(result_path)]
    assert source_profile_evidence["profile_summaries"][0]["summary"] == (
        "Orders paid aggregate scanned the scratch CSV."
    )

    profile_run = describe_profile_run_tool(db, **profile_action["arguments"])
    assert profile_run["returned_profile_count"] == 1
    assert profile_run["evidence"]["sources"] == [str(result_path)]
    assert profile_run["evidence"]["source_spans"][0]["source_path"] == (
        "queries/orders_paid_aggregate.sql"
    )


def test_export_tools_write_review_artifacts(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)
    graph_path = tmp_path / "map.ttl"
    trig_path = tmp_path / "bundle.trig"

    graph_result = export_graph_tool(db, path=str(graph_path), graphs=["map"])
    trig_result = export_trig_tool(
        db,
        path=str(trig_path),
    )

    assert graph_result["path"] == str(graph_path)
    assert graph_result["format"] == "turtle"
    assert graph_result["graphs"] == ["map"]
    assert graph_result["graph_counts"] == {"map": db.triple_count("map")}
    assert graph_result["triples"] == db.triple_count("map")
    assert graph_result["sensitive_literal_count"] == 0
    assert graph_result["privacy_warnings"] == []
    assert graph_path.exists()

    assert trig_result["path"] == str(trig_path)
    assert trig_result["format"] == "trig"
    assert trig_result["graphs"] == [
        "ontology",
        "map",
        "observations",
        "patterns",
        "evidence",
        "shapes",
        "history",
    ]
    assert "base_ontology" not in trig_result["graphs"]
    assert trig_result["sensitive_literal_count"] == 0
    assert trig_result["privacy_warnings"] == []
    assert trig_result["triples"] == sum(trig_result["graph_counts"].values())
    assert trig_path.exists()


def test_scan_sensitive_literals_tool_returns_redacted_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_123"
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#orders_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        storage_root=f"/tmp/{fake_secret}/orders",
        credential_reference=f"Bearer {fake_secret}",
    )
    record_map_dataset_tool(
        db,
        iri="https://example.test/project#Orders",
        label="Orders",
        is_table=True,
        storage_accesses=[storage["iri"]],
    )

    result = scan_sensitive_literals_tool(db, graphs=["map"], limit=5)

    assert result["graphs"] == ["map"]
    assert result["match_count"] >= 2
    assert result["returned_match_count"] >= 2
    assert result["warnings"]
    assert fake_secret not in str(result["matches"])
    assert all("redacted_snippet" in match for match in result["matches"])
    assert all("term_position" in match for match in result["matches"])
    assert all("term_kind" in match for match in result["matches"])


def test_export_preflight_tool_returns_conservative_redacted_decision(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_PREFLIGHT_MCP"
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#orders_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=f"/tmp/{fake_secret}/orders",
    )
    record_map_dataset_tool(
        db,
        iri="https://example.test/project#Orders",
        label="Orders",
        is_table=True,
        storage_accesses=[storage["iri"]],
    )

    result = export_preflight_tool(
        db,
        export_kind="graph",
        graphs=["map"],
        limit=1,
    )

    assert result["export_kind"] == "graph"
    assert result["decision"] == "block"
    assert result["scanner_clean"] is False
    assert result["shareability_review_required"] is True
    assert result["would_block_sensitive_export"] is True
    assert result["graphs"] == ["map"]
    assert result["graph_sensitive_literal_count"] >= 1
    assert result["sensitive_literal_count"] >= 1
    assert result["returned_match_count"] == 1
    assert result["omitted_match_count"] == (
        result["sensitive_literal_count"] - result["returned_match_count"]
    )
    assert result["matches"][0]["match_id"].startswith("redacted-sha256:")
    assert result["suggested_next_actions"][0]["tool_name"] == "scan_sensitive_literals"
    assert fake_secret not in json.dumps(result)


def test_mcp_export_tools_block_sensitive_predicate_iris(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_PREDICATE_MCP"
    predicate_iri = f"https://example.test/project#{fake_secret}"
    db.import_turtle(
        f"""
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:Orders a rc:Dataset ;
            <{predicate_iri}> "predicate-only MCP privacy probe" .
        """,
        graph="map",
    )
    revision = db.record_graph_revision(
        summary="Record predicate MCP privacy probe",
        rationale=(
            "Capture a map snapshot whose sensitive-looking term is only a "
            "predicate IRI."
        ),
        changed_graphs=["map"],
        included_graphs=["map"],
    )

    scan = scan_sensitive_literals_tool(db, graphs=["map"], limit=10)

    assert scan["match_count"] >= 1
    assert any(match["term_position"] == "predicate" for match in scan["matches"])
    assert fake_secret not in str(scan["matches"])

    graph_path = tmp_path / "blocked-predicate.ttl"
    with pytest.raises(DoxaBaseError) as graph_excinfo:
        export_graph_tool(
            db,
            path=str(graph_path),
            graphs=["map"],
            fail_on_sensitive=True,
        )
    assert "fail_on_sensitive=True" in str(graph_excinfo.value)
    assert fake_secret not in str(graph_excinfo.value)
    assert not graph_path.exists()

    snapshot_path = tmp_path / "blocked-predicate-snapshots.json"
    with pytest.raises(DoxaBaseError) as snapshot_excinfo:
        export_revision_snapshots_tool(
            db,
            path=str(snapshot_path),
            revision_iris=[revision.revision_iri],
            fail_on_sensitive=True,
        )
    assert "fail_on_sensitive=True" in str(snapshot_excinfo.value)
    assert fake_secret not in str(snapshot_excinfo.value)
    assert not snapshot_path.exists()


def test_export_tools_can_block_sensitive_literals_before_writing(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_MCP"
    record_map_storage_access_tool(
        db,
        iri="https://example.test/project#orders_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=f"/tmp/{fake_secret}/orders",
    )

    graph_path = tmp_path / "blocked.ttl"
    with pytest.raises(DoxaBaseError) as excinfo:
        export_graph_tool(
            db,
            path=str(graph_path),
            graphs=["map"],
            fail_on_sensitive=True,
        )
    assert "fail_on_sensitive=True" in str(excinfo.value)
    assert fake_secret not in str(excinfo.value)
    assert not graph_path.exists()

    trig_path = tmp_path / "blocked.trig"
    with pytest.raises(DoxaBaseError):
        export_trig_tool(
            db,
            path=str(trig_path),
            graphs=["map"],
            fail_on_sensitive=True,
        )
    assert not trig_path.exists()


def test_export_revision_snapshots_tool_reports_sensitive_literals(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_SNAPSHOT_MCP"
    record_map_storage_access_tool(
        db,
        iri="https://example.test/project#orders_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=f"/tmp/{fake_secret}/orders",
    )
    staged = stage_graph_revision_tool(
        db,
        summary="Stage snapshot probe",
        rationale="Create a revision snapshot over the map graph.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:OrdersSnapshotProbe a rc:Dataset .
                """,
            }
        ],
    )

    snapshot_path = tmp_path / "revision-snapshots.json"
    result = export_revision_snapshots_tool(
        db,
        path=str(snapshot_path),
        revision_iris=[staged["revision_iri"]],
    )

    assert result["sensitive_literal_count"] >= 1
    assert result["privacy_warnings"]
    assert fake_secret not in " ".join(result["privacy_warnings"])
    assert fake_secret in snapshot_path.read_text(encoding="utf-8")

    blocked_path = tmp_path / "blocked-revision-snapshots.json"
    with pytest.raises(DoxaBaseError) as excinfo:
        export_revision_snapshots_tool(
            db,
            path=str(blocked_path),
            revision_iris=[staged["revision_iri"]],
            fail_on_sensitive=True,
        )
    assert "fail_on_sensitive=True" in str(excinfo.value)
    assert fake_secret not in str(excinfo.value)
    assert not blocked_path.exists()


def test_export_handoff_bundle_tool_writes_importable_pair(tmp_path: Path) -> None:
    source = DoxaBase.create(tmp_path / "source.sqlite")
    receiver = DoxaBase.create(tmp_path / "receiver.sqlite")
    staged = stage_graph_revision_tool(
        source,
        summary="Stage handoff table",
        rationale="Create a project/history RDF and snapshot handoff pair.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:HandoffOrders a rc:Dataset, rc:Table .
                """,
            }
        ],
    )
    trig_path = tmp_path / "project-handoff.trig"
    snapshot_path = tmp_path / "revision-snapshots.json"
    manifest_path = tmp_path / "handoff-manifest.json"

    result = export_handoff_bundle_tool(
        source,
        trig_path=str(trig_path),
        revision_snapshot_path=str(snapshot_path),
        manifest_path=str(manifest_path),
        revision_iris=[staged["revision_iri"]],
    )

    assert result["paths"] == {
        "trig": str(trig_path),
        "revision_snapshots": str(snapshot_path),
        "manifest": str(manifest_path),
    }
    assert result["trig"]["path"] == str(trig_path)
    assert result["revision_snapshots"]["path"] == str(snapshot_path)
    assert result["manifest_path"] == str(manifest_path)
    assert result["manifest_bytes_written"] == len(
        manifest_path.read_text(encoding="utf-8").encode("utf-8")
    )
    assert result["graph_roles"] == [
        "ontology",
        "map",
        "observations",
        "patterns",
        "evidence",
        "shapes",
        "history",
    ]
    assert result["revision_iris"] == [staged["revision_iri"]]
    assert result["snapshot_graph_roles"] == ["map"]
    assert result["sensitive_literal_count"] == 0
    assert result["privacy_warnings"] == []
    assert trig_path.exists()
    assert snapshot_path.exists()
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest == result["manifest"]
    assert manifest["format"] == "doxabase.handoff_bundle.v1"
    assert manifest["artifacts"]["trig"]["path"] == str(trig_path)
    assert manifest["artifacts"]["revision_snapshots"]["path"] == str(snapshot_path)
    assert [
        step["tool_name"] for step in manifest["recommended_import_sequence"]
    ] == ["import_trig", "import_revision_snapshots"]
    assert [
        step["expected_snapshot_evidence_status"]
        for step in manifest["recommended_import_sequence"]
    ] == ["history_only_count_digest", "history_plus_snapshot_rows"]

    import_trig_tool(receiver, path=str(trig_path))
    before_snapshots = describe_revision_snapshot_evidence_tool(
        receiver,
        iri=staged["revision_iri"],
    )
    assert before_snapshots["status"] == "history_only_count_digest"

    import_revision_snapshots_tool(receiver, path=str(snapshot_path))
    after_snapshots = describe_revision_snapshot_evidence_tool(
        receiver,
        iri=staged["revision_iri"],
    )
    assert after_snapshots["status"] == "history_plus_snapshot_rows"
    assert after_snapshots["exact_snapshot_graph_roles"] == ["map"]


def test_replace_graph_triples_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:Customers a rc:Dataset ;
            rdfs:label "Customers scratch table" .
        """,
        graph="map",
    )

    result = replace_graph_triples_tool(
        db,
        graph="map",
        removals="""
            @prefix ex: <https://example.test/project#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            ex:Customers rdfs:label "Customers scratch table" .
        """,
        additions="""
            @prefix ex: <https://example.test/project#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            ex:Customers rdfs:label "Customers scratch table, drifted" .
        """,
        expected_count=2,
    )

    assert result["graph"] == "map"
    assert result["before_count"] == 2
    assert result["after_count"] == 2
    assert result["same_count"] is True
    assert result["digest_changed"] is True
    assert result["triples_removed"] == 1
    assert result["triples_added"] == 1
    assert result["expected_count"] == 2
    assert result["allow_count_change"] is False


def test_record_graph_revision_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)
    validation = validate_graph_tool(db, scope="all")
    export_path = tmp_path / "review.trig"
    export_result = export_trig_tool(db, path=str(export_path), graphs=["workflow"])

    result = record_graph_revision_tool(
        db,
        summary="Fixture review bundle exported",
        rationale="The MCP wrapper test records why this review bundle exists.",
        changed_graphs=["observations", "patterns", "evidence"],
        included_graphs=export_result["graphs"],
        revision_type="rc:ExportRevision",
        revision_anchors=[
            "https://richcanopy.org/example/manifest/ais#DailyIndex",
        ],
        export_path=export_result["path"],
        graph_counts=export_result["graph_counts"],
        validation_scope=validation["scope"],
        validation_conforms=validation["conforms"],
        validation_result_count=validation["result_count"],
    )

    assert result["revision_iri"].startswith(
        "https://richcanopy.org/doxabase/generated/graph-revision/"
    )
    assert result["revision_type"] == "https://richcanopy.org/ns/rc#ExportRevision"
    assert result["graph"] == "history"
    assert result["triples"] > 0
    context = db.describe_resource(result["revision_iri"], graph="history")
    outgoing = {(triple.predicate, triple.object) for triple in context.outgoing}
    assert ("https://richcanopy.org/ns/rc#changedGraph", "map") not in outgoing
    assert ("https://richcanopy.org/ns/rc#includedGraph", "map") in outgoing
    description = describe_graph_revision_tool(db, result["revision_iri"])
    assert description["summary"] == "Fixture review bundle exported"
    assert description["changed_graphs"] == ["evidence", "observations", "patterns"]
    assert description["included_graphs"] == [
        "evidence",
        "map",
        "observations",
        "patterns",
    ]
    assert description["revision_anchors"][0]["iri"] == (
        "https://richcanopy.org/example/manifest/ais#DailyIndex"
    )
    assert description["validation_conforms"] is True
    assert description["graph_snapshots"]
    assert description["graph_snapshots"][0]["content_digest"].startswith("sha256:")
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_staged_revision_tools_return_json_like_payloads(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_map_count = db.triple_count("map")
    content = """
    @prefix ex: <https://example.test/project#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:Messages a rc:Dataset, rc:Table ;
        rdfs:label "Messages" .
    """

    result = stage_graph_revision_tool(
        db,
        summary="Try messages table framing",
        rationale=(
            "Exploratory hunch: this map shape may generalise better once "
            "more message-like datasets arrive."
        ),
        additions=[{"graph": "map", "content": content}],
        stance="rc:ExploratoryHunch",
        validation_scope="all",
    )

    assert result["revision_iri"].startswith(
        "https://richcanopy.org/doxabase/generated/staged-revision/"
    )
    assert result["revision_type"] == "https://richcanopy.org/ns/rc#StagedRevision"
    assert result["revision_stance"] == "https://richcanopy.org/ns/rc#ExploratoryHunch"
    assert result["summary"] == "Try messages table framing"
    assert result["rationale"].startswith("Exploratory hunch")
    assert result["review_note"] is None
    assert result["review_recommendation"] is None
    assert result["changed_graphs"] == ["map"]
    assert result["validation_conforms"] is True
    assert result["validation_result_count"] == 0
    assert result["patches"][0]["operation"] == "https://richcanopy.org/ns/rc#AdditionPatch"
    assert result["patches"][0]["count_basis"] == "target_graph_only"
    assert result["patches"][0]["before_triple_count"] == before_map_count
    assert result["patches"][0]["after_triple_count"] == before_map_count + 3
    assert db.triple_count("map") == before_map_count

    description = describe_staged_revision_tool(db, result["revision_iri"])
    assert description["revision_stance_label"] == "exploratory hunch"
    assert description["patches"][0]["target_graph"] == "map"
    assert description["patches"][0]["count_basis"] == "target_graph_only"
    assert "ex:Messages" in description["patches"][0]["content"]
    assert validate_graph_tool(db, scope="all")["conforms"] is True

    export_path = tmp_path / "staged-review.md"
    export = export_staged_revision_tool(
        db,
        iri=result["revision_iri"],
        path=str(export_path),
    )
    assert export["format"] == "markdown"
    assert export_path.exists()
    assert "exploratory hunch" in export_path.read_text()


def test_staged_markdown_export_tools_return_privacy_warnings(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_789"
    secret_text = f"Bearer {fake_secret}"
    staged = stage_graph_revision_tool(
        db,
        summary="Stage risky review literal",
        rationale="Export tools should surface privacy warnings.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:RiskyLiteral a rc:KnownCaveat ;
                        rdfs:label "Risky literal" ;
                        rc:caveatDescription "{secret_text}" .
                """,
            }
        ],
    )

    single = export_staged_revision_tool(
        db,
        iri=staged["revision_iri"],
        path=str(tmp_path / "single.md"),
    )
    grouped = export_staged_revisions_tool(
        db,
        revision_iris=[staged["revision_iri"]],
        path=str(tmp_path / "grouped.md"),
    )

    assert single["sensitive_literal_count"] == 1
    assert grouped["sensitive_literal_count"] == 1
    assert single["privacy_warnings"]
    assert grouped["privacy_warnings"]
    assert fake_secret not in " ".join(single["privacy_warnings"])
    assert fake_secret not in " ".join(grouped["privacy_warnings"])
    single_text = Path(single["path"]).read_text(encoding="utf-8")
    grouped_text = Path(grouped["path"]).read_text(encoding="utf-8")
    assert "## Privacy Warning" in single_text
    assert "## Privacy Warning" in grouped_text
    assert f"line {_line_number_containing(single_text, secret_text)} " in " ".join(
        single["privacy_warnings"]
    )
    assert f"line {_line_number_containing(grouped_text, secret_text)} " in " ".join(
        grouped["privacy_warnings"]
    )

    blocked_single_path = tmp_path / "blocked-single.md"
    with pytest.raises(DoxaBaseError, match="fail_on_sensitive=True"):
        export_staged_revision_tool(
            db,
            iri=staged["revision_iri"],
            path=str(blocked_single_path),
            fail_on_sensitive=True,
        )
    assert not blocked_single_path.exists()

    blocked_grouped_path = tmp_path / "blocked-grouped.md"
    with pytest.raises(DoxaBaseError, match="fail_on_sensitive=True"):
        export_staged_revisions_tool(
            db,
            revision_iris=[staged["revision_iri"]],
            path=str(blocked_grouped_path),
            fail_on_sensitive=True,
        )
    assert not blocked_grouped_path.exists()


def test_draft_staged_revision_rebase_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    event_framing = db.stage_graph_revision(
        summary="Model Orders as event rows",
        rationale="First alternative for row-grain review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders a rc:Dataset, rc:Table ;
                        rc:rowSemantics rc:EventRow .
                """,
            }
        ],
        revision_anchors=[orders],
    )
    snapshot_framing = db.stage_graph_revision(
        summary="Model Orders as snapshot rows",
        rationale="Competing row-grain alternative.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders a rc:Dataset, rc:Table ;
                        rc:rowSemantics rc:SnapshotRow .
                """,
            }
        ],
        alternative_to=event_framing.revision_iri,
        revision_anchors=[orders],
    )
    db.record_map_dataset(
        "https://example.test/project#DriftDataset",
        label="Drift dataset",
    )
    event_successor = db.restage_staged_revision(event_framing.revision_iri)
    db.apply_staged_revision(event_successor.revision_iri)
    snapshot_successor = db.restage_staged_revision(snapshot_framing.revision_iri)

    result = draft_staged_revision_rebase_tool(
        db,
        iri=snapshot_successor.revision_iri,
    )

    assert result["helper"] == "draft_staged_revision_rebase"
    assert result["mode"] == "non_executed_review_draft"
    assert result["source_revision_iri"] == snapshot_successor.revision_iri
    assert result["draft_status"] == "drafted"
    assert result["draft_kind"] == "same_slot_replacement"
    assert result["apply_check"]["status"] == "validation_failed"
    assert result["lineage"]["alternative_gate_status"] == (
        "alternative_to_applied_source"
    )
    assert result["repair_actions"][0]["tool_name"] == (
        "stage_map_assertion_change"
    )
    assert result["repair_actions"][0]["arguments"]["restages_revision"] == (
        snapshot_successor.revision_iri
    )
    assert result["repair_candidates"][0]["proposed_triples"][0]["object"] == (
        RC + "SnapshotRow"
    )
    assert result["next_action"]["source"] == "draft_staged_revision_rebase"


def test_plan_staged_revision_recovery_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = stage_graph_revision_tool(
        db,
        summary="Stage messages table",
        rationale="Messages should become durable map context after review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Messages a rc:Dataset .
                """,
            }
        ],
    )

    result = plan_staged_revision_recovery_tool(db)

    assert result["result_kind"] == "staged_revision_recovery_plan"
    assert result["helper"] == "plan_staged_revision_recovery"
    assert result["mode"] == "read_only_plan"
    assert result["selection_mode"] == "current_staged_work"
    assert result["processed_revision_iris"] == [staged["revision_iri"]]
    assert result["lane_counts"] == {"apply_after_review": 1}
    assert result["repair_or_replace_source_revision_iris"] == []
    assert result["next_action_queue_item_counts"] == {
        "apply_after_review": 1
    }
    assert result["mutation_frontier_iris"] == [staged["revision_iri"]]
    assert result["requires_recheck_after_each_apply"] is False
    lane = result["lanes"][0]
    assert lane["source_revision_iri"] == staged["revision_iri"]
    assert lane["row_iri"] == staged["revision_iri"]
    assert lane["lane"] == "apply_after_review"
    assert lane["next_action"]["tool_name"] == "apply_staged_revision"
    assert lane["next_action_queue_item"]["resolved_target_iri"] == (
        staged["revision_iri"]
    )
    assert result["bundle_summary"]["next_action_queue"] == {
        "apply_after_review": [staged["revision_iri"]]
    }
    assert result["bundle_summary"]["mutation_frontier_iris"] == [
        staged["revision_iri"]
    ]
    assert result["bundle_summary"]["requires_recheck_after_each_apply"] is False
    assert result["note"].startswith("Read-only staged revision recovery plan")


def test_plan_staged_revision_recovery_tool_promotes_handoff_snapshot_import(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "source.sqlite")
    staged = stage_graph_revision_tool(
        db,
        summary="Stage live messages table",
        rationale="Exercise RDF-only handoff planning through the MCP wrapper.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:LiveMessages a rc:Dataset .
                """,
            }
        ],
    )
    project_path = tmp_path / "project.trig"
    export_trig_tool(db, path=str(project_path), graphs="project")
    imported = DoxaBase.create(tmp_path / "rdf-only.sqlite")
    imported.import_trig(project_path)

    result = plan_staged_revision_recovery_tool(
        imported,
        revision_iris=[staged["revision_iri"]],
    )

    assert result["lane_counts"] == {"apply_after_review": 1}
    assert result["next_action_queue"] == {
        "apply_after_review": [staged["revision_iri"]]
    }
    assert result["bundle_summary"]["snapshot_evidence"]["complete"] is False
    assert result["suggested_next_actions"][0]["tool_name"] == (
        "import_revision_snapshots"
    )
    assert result["lanes"][0]["suggested_next_actions"][0]["tool_name"] == (
        "import_revision_snapshots"
    )
    assert "Snapshot evidence is incomplete" in result["warnings"][0]


def test_plan_staged_revision_recovery_tool_suggests_batch_restage_dry_run(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = stage_graph_revision_tool(
        db,
        summary="Stage messages table",
        rationale="Messages should become durable map context after review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Messages a rc:Dataset .
                """,
            }
        ],
    )
    record_map_dataset_tool(
        db,
        iri="https://example.test/project#Drift",
        label="Drift",
    )

    result = plan_staged_revision_recovery_tool(
        db,
        revision_iris=[staged["revision_iri"]],
    )

    assert result["would_restage_revision_iris"] == [staged["revision_iri"]]
    batch_action = result["suggested_next_actions"][0]
    assert batch_action["tool_name"] == "restage_staged_revisions"
    assert batch_action["mcp_tool_name"] == "doxabase.restage_staged_revisions"
    assert batch_action["arguments"] == {
        "revision_iris": [staged["revision_iri"]],
        "dry_run": True,
    }
    assert any(
        action["tool_name"] == "restage_staged_revision"
        and action["arguments"] == {"iri": staged["revision_iri"]}
        for action in result["suggested_next_actions"]
    )


def test_plan_staged_revision_recovery_tool_uses_embedded_no_repair_draft_route(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    record_map_dataset_tool(db, iri=orders, label="Orders", is_table=True)
    staged = stage_graph_revision_tool(
        db,
        summary="Model Orders with invalid row-semantics object",
        rationale="The invalid object should require manual repair review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders rc:rowSemantics "snapshot" .
                """,
            }
        ],
        revision_anchors=[orders],
    )
    record_map_dataset_tool(db, iri=orders, row_semantics="rc:EventRow")

    result = plan_staged_revision_recovery_tool(
        db,
        revision_iris=[staged["revision_iri"]],
    )

    assert result["repair_first_revision_iris"] == [staged["revision_iri"]]
    assert result["repair_or_replace_source_revision_iris"] == [
        staged["revision_iri"]
    ]
    lane = result["lanes"][0]
    assert lane["repair_draft"]["draft_kind"] == "validation_repair_needed"
    assert lane["next_action"]["tool_name"] != "draft_staged_revision_rebase"
    assert all(
        action["tool_name"] != "draft_staged_revision_rebase"
        for action in lane["suggested_next_actions"]
    )
    assert all(
        action["tool_name"] != "draft_staged_revision_rebase"
        for action in result["suggested_next_actions"]
    )


def test_restage_staged_revision_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = stage_graph_revision_tool(
        db,
        summary="Stage messages table",
        rationale="Messages should become durable map context after review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Messages a rc:Dataset .
                """,
            }
        ],
    )
    db.record_map_dataset(
        "https://example.test/project#OtherDataset",
        label="Other dataset",
    )
    stale_check = check_staged_revision_apply_tool(db, iri=staged["revision_iri"])
    assert stale_check["status"] == "conflict"
    assert stale_check["validation_skipped_reason"] == "conflicts_present"
    assert stale_check["count_drifts"][0]["target_graph"] == "map"
    assert stale_check["count_drifts"][0]["delta"] == db.triple_count("map")
    assert stale_check["count_drifts"][0]["exact_changed_triples_available"] is True
    assert stale_check["count_drifts"][0]["patch_triples_checked"] == 1
    assert stale_check["count_drifts"][0]["patch_triples_currently_present"] == 0
    assert stale_check["count_drifts"][0]["patch_triples_currently_absent"] == 1
    assert stale_check["count_drifts"][0]["patch_triple_status"] == (
        "all_patch_triples_absent"
    )
    assert stale_check["snapshot_drifts"][0]["graph_role"] == "map"
    assert stale_check["snapshot_drifts"][0]["snapshot_content_digest"].startswith(
        "sha256:"
    )
    assert stale_check["snapshot_drifts"][0]["current_content_digest"].startswith(
        "sha256:"
    )
    snapshot_drift = stale_check["snapshot_drifts"][0]
    assert snapshot_drift["exact_changed_triples_available"] is True
    assert snapshot_drift["triples_added_since_snapshot_count"] == len(
        snapshot_drift["triples_added_since_snapshot"]
    )
    assert snapshot_drift["triples_removed_since_snapshot_count"] == 0
    assert snapshot_drift["triples_added_since_snapshot"]
    assert snapshot_drift["triples_removed_since_snapshot"] == []
    added_drift_triple = snapshot_drift["triples_added_since_snapshot"][0]
    assert "subject_display" in added_drift_triple
    assert "predicate_display" in added_drift_triple
    assert "object_display" in added_drift_triple
    assert stale_check["suggested_next_actions"][0]["tool_name"] == (
        "describe_staged_revision"
    )
    assert stale_check["suggested_next_actions"][-1]["tool_name"] == (
        "restage_staged_revision"
    )
    assert stale_check["next_action"]["action_type"] == "restage_after_review"
    assert stale_check["routing_decision"] == "restage_after_review"
    assert stale_check["next_action"]["queue"] == "restage_after_review"
    assert stale_check["next_action"]["tool_name"] == "restage_staged_revision"
    assert stale_check["next_action"]["arguments"] == {"iri": staged["revision_iri"]}

    restaged = restage_staged_revision_tool(db, iri=staged["revision_iri"])

    assert restaged["revision_iri"] != staged["revision_iri"]
    assert restaged["patches"][0]["before_triple_count"] == db.triple_count("map")
    assert restaged["alternative_to"] is None
    assert restaged["restaged_from"] == staged["revision_iri"]
    assert "prior status conflict" in restaged["restage_reason"]
    assert "blockers target_count_drift" in restaged["restage_reason"]
    assert restaged["current_restaged_by"] is None
    assert restaged["status_after"] == "ready"
    assert restaged["decision_after"] == "review_then_apply"
    assert restaged["routing_decision_after"] == "apply_after_review"
    assert restaged["stale_resolution_state_after"] == "restaged_successor_ready"
    assert restaged["blocking_reasons_after"] == []
    assert restaged["current_staged_validation_status"] == "conforms"
    assert restaged["next_action_after"]["action_type"] == "apply_after_review"
    assert restaged["next_action_after"]["tool_name"] == "apply_staged_revision"
    assert restaged["next_action_after"]["arguments"] == {
        "iri": restaged["revision_iri"]
    }
    assert restaged["next_action_queue_item_after"]["queue"] == "apply_after_review"
    assert restaged["next_action_queue_item_after"]["resolved_target_iri"] == (
        restaged["revision_iri"]
    )
    assert restaged["suggested_next_actions_after"][-1]["tool_name"] == (
        "apply_staged_revision"
    )
    with pytest.raises(DoxaBaseError, match=restaged["revision_iri"]):
        restage_staged_revision_tool(db, iri=staged["revision_iri"])
    stale_description = describe_staged_revision_tool(db, staged["revision_iri"])
    assert stale_description["restaged_by"]["iri"] == restaged["revision_iri"]
    stale_check_after = check_staged_revision_apply_tool(
        db,
        iri=staged["revision_iri"],
    )
    assert stale_check_after["restaged_by"] == restaged["revision_iri"]
    assert stale_check_after["current_restaged_by"] == restaged["revision_iri"]
    assert stale_check_after["stale_resolution_state"] == "stale_handled_by_restage"
    assert stale_check_after["next_action"]["action_type"] == (
        "inspect_current_successor"
    )
    assert stale_check_after["next_action"]["arguments"] == {
        "iri": restaged["revision_iri"]
    }
    assert not any(
        action["tool_name"] == "restage_staged_revision"
        for action in stale_check_after["suggested_next_actions"]
    )
    description = describe_staged_revision_tool(db, restaged["revision_iri"])
    assert description["restaged_from"]["iri"] == staged["revision_iri"]
    assert "prior status conflict" in description["restage_reason"]
    assert "blockers target_count_drift" in description["restage_reason"]
    assert check_staged_revision_apply_tool(
        db,
        iri=restaged["revision_iri"],
    )["status"] == "ready"
    applied = apply_staged_revision_tool(db, iri=restaged["revision_iri"])
    stale_check_after_apply = check_staged_revision_apply_tool(
        db,
        iri=staged["revision_iri"],
    )
    assert stale_check_after_apply["restaged_by"] == restaged["revision_iri"]
    assert (
        stale_check_after_apply["current_restaged_by"]
        == restaged["revision_iri"]
    )
    assert (
        stale_check_after_apply["stale_resolution_state"]
        == "stale_handled_by_restage"
    )
    assert stale_check_after_apply["next_action"]["action_type"] == (
        "inspect_already_applied"
    )
    assert stale_check_after_apply["next_action"]["queue"] == (
        "inspect_already_applied"
    )
    assert stale_check_after_apply["next_action"]["tool_name"] == (
        "describe_graph_revision"
    )
    assert stale_check_after_apply["next_action"]["arguments"] == {
        "iri": applied["applied_revision_iri"]
    }
    assert stale_check_after_apply["suggested_next_actions"][0][
        "tool_name"
    ] == "describe_graph_revision"
    assert stale_check_after_apply["suggested_next_actions"][0]["arguments"] == {
        "iri": applied["applied_revision_iri"]
    }


def test_stage_graph_revision_tool_records_repaired_restage_successor(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    source = stage_graph_revision_tool(
        db,
        summary="Stage old orders label",
        rationale="Original candidate needs a repaired successor.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Orders rdfs:label "Old orders" .
                """,
            }
        ],
        revision_anchors=[orders],
    )
    record_map_dataset_tool(db, iri=orders, label="Current orders", is_table=True)

    repair = stage_graph_revision_tool(
        db,
        summary="Repair orders label",
        rationale="Caller-authored repaired successor.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Orders rdfs:label "Preferred orders" .
                """,
            }
        ],
        removals=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Orders rdfs:label "Current orders" .
                """,
            }
        ],
        restages_revision=source["revision_iri"],
    )

    assert repair["restaged_from"] == source["revision_iri"]
    stale_description = describe_staged_revision_tool(db, source["revision_iri"])
    assert stale_description["restaged_by"]["iri"] == repair["revision_iri"]
    current_work = list_graph_revisions_tool(
        db,
        current_staged_work_only=True,
        include_apply_checks=True,
    )
    current_work_iris = {item["iri"] for item in current_work["revisions"]}
    assert source["revision_iri"] not in current_work_iris
    assert repair["revision_iri"] in current_work_iris


def test_restage_staged_revisions_tool_exports_grouped_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mcp_tools, "ROOT", tmp_path)
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    first = stage_graph_revision_tool(
        db,
        summary="Stage messages table",
        rationale="Messages should become durable map context after review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Messages a rc:Dataset .
                """,
            }
        ],
        review_recommendation="Old authored review guidance should not mask live status.",
    )
    second = stage_graph_revision_tool(
        db,
        summary="Stage threads table",
        rationale="Threads should become durable map context after review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Threads a rc:Dataset .
                """,
            }
        ],
    )
    db.record_map_dataset(
        "https://example.test/project#OtherDataset",
        label="Other dataset",
    )
    already_restaged = restage_staged_revision_tool(
        db,
        iri=first["revision_iri"],
    )

    result = restage_staged_revisions_tool(
        db,
        revision_iris=[first["revision_iri"], second["revision_iri"]],
        path="nested/../batch-review.md",
        title="Batch review",
    )

    expected_path = (tmp_path / "batch-review.md").resolve()
    restaged_second = result["restaged_revision_iris"][0]
    assert result["export_record"]["path"] == str(expected_path)
    assert result["items"][0]["action"] == "skipped_already_handled"
    assert result["items"][1]["action"] == "restaged"
    assert result["items"][1]["source_snapshot_evidence"]["status"] == (
        "history_plus_snapshot_rows"
    )
    assert result["items"][1]["source_snapshot_evidence_completeness"] == "complete"
    assert result["items"][1]["current_snapshot_evidence"]["revision_iri"] == (
        restaged_second
    )
    assert result["items"][1]["current_snapshot_evidence"]["status"] == (
        "history_plus_snapshot_rows"
    )
    assert result["items"][1]["current_snapshot_evidence_completeness"] == "complete"
    assert result["items"][0]["next_action_after"]["action_type"] == (
        "apply_after_review"
    )
    assert result["items"][0]["next_action_after"]["arguments"] == {
        "iri": already_restaged["revision_iri"]
    }
    assert result["items"][0]["next_action_queue_item_after"]["row_iri"] == (
        already_restaged["revision_iri"]
    )
    assert result["items"][0]["next_action_queue_item_after"][
        "resolved_target_iri"
    ] == already_restaged["revision_iri"]
    assert result["items"][0]["next_action_queue_item_after"][
        "resolved_target_record_kind"
    ] == "staged_patch"
    assert result["items"][0]["next_action_queue_item_after"]["row_is_target"] is True
    assert result["items"][1]["next_action_after"]["action_type"] == (
        "apply_after_review"
    )
    assert result["items"][1]["next_action_after"]["arguments"] == {
        "iri": restaged_second
    }
    assert result["items"][1]["next_action_queue_item_after"]["row_iri"] == (
        restaged_second
    )
    assert result["items"][1]["next_action_queue_item_after"][
        "resolved_target_iri"
    ] == restaged_second
    assert result["items"][1]["suggested_next_actions_after"][-1]["tool_name"] == (
        "apply_staged_revision"
    )
    assert result["current_revision_by_source"] == {
        first["revision_iri"]: already_restaged["revision_iri"],
        second["revision_iri"]: restaged_second,
    }
    assert result["review_revision_iris"] == [
        first["revision_iri"],
        already_restaged["revision_iri"],
        second["revision_iri"],
        restaged_second,
    ]
    assert result["bundle_summary"]["unresolved_stale_revision_iris"] == []
    assert result["bundle_summary"]["ready_restage_successor_revision_iris"] == [
        already_restaged["revision_iri"],
        restaged_second,
    ]
    assert result["bundle_summary"]["post_apply_recheck_revision_iris"] == [
        already_restaged["revision_iri"],
        restaged_second,
    ]
    assert result["bundle_summary"]["sequential_apply_recheck_candidate_iris"] == [
        already_restaged["revision_iri"],
        restaged_second,
    ]
    assert len(result["bundle_summary"]["warnings"]) == 1
    assert result["bundle_summary"]["recommended_apply_or_restage_review_iris"] == [
        already_restaged["revision_iri"],
        restaged_second,
    ]
    assert result["bundle_summary"]["next_action_queue"]["apply_after_review"] == [
        already_restaged["revision_iri"],
        restaged_second,
    ]
    assert result["bundle_summary"]["next_action_queue"]["informational"] == [
        first["revision_iri"],
        second["revision_iri"],
    ]
    assert result["bundle_summary"]["recommended_repair_review_iris"] == []
    stale_summary = result["revision_summaries"][0]
    assert stale_summary["next_action"]["action_type"] == "inspect_current_successor"
    assert stale_summary["next_action"]["queue"] == "informational"
    assert (
        stale_summary["apply_recommendation_scope"]
        == "prior_source_apply_check_context"
    )
    assert (
        stale_summary["summary_recommendation_source"]
        == "stale_resolution_redirect"
    )
    assert stale_summary["active_recommendation_field"] == "summary_recommendation"
    assert stale_summary["suggested_next_actions"][-1]["action_label"] == (
        "Inspect current refreshed successor"
    )
    assert expected_path.exists()
    export_text = expected_path.read_text(encoding="utf-8")
    assert "## Bundle Warnings" in export_text
    assert "## Review Queues" in export_text
    assert "Queue values are returned row IRIs" in export_text
    assert "- Next action - apply after review: " in export_text
    assert "- Next action - informational: " in export_text
    assert "- Recommended review: " in export_text
    assert "- Recommended mutation review: " in export_text
    assert "- Apply/restage review: " in export_text
    assert "- Sequential apply recheck candidates: " in export_text
    assert "## Restage Context" in export_text
    assert "**Inspect current refreshed successor:**" in export_text


def test_restage_staged_revisions_tool_can_dry_run(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    first = stage_graph_revision_tool(
        db,
        summary="Stage messages table",
        rationale="Messages should become durable map context after review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Messages a rc:Dataset .
                """,
            }
        ],
    )
    second = stage_graph_revision_tool(
        db,
        summary="Stage threads table",
        rationale="Threads should become durable map context after review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Threads a rc:Dataset .
                """,
            }
        ],
    )
    db.record_map_dataset(
        "https://example.test/project#OtherDataset",
        label="Other dataset",
    )
    ready = stage_graph_revision_tool(
        db,
        summary="Stage current shipments table",
        rationale="This proposal was staged after the drift.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:CurrentShipments a rc:Dataset .
                """,
            }
        ],
    )
    staged_count_before = list_graph_revisions_tool(
        db,
        revision_type="rc:StagedRevision",
    )["count"]

    result = restage_staged_revisions_tool(
        db,
        revision_iris=[
            first["revision_iri"],
            second["revision_iri"],
            ready["revision_iri"],
        ],
        dry_run=True,
    )

    assert result["dry_run"] is True
    assert result["would_restage_revision_iris"] == [
        first["revision_iri"],
        second["revision_iri"],
    ]
    assert result["restaged_revision_iris"] == []
    assert result["not_restageable_revision_iris"] == [ready["revision_iri"]]
    assert result["not_restageable_revision_iris_by_reason"] == {
        "ready": [ready["revision_iri"]],
    }
    assert [item["action"] for item in result["items"]] == [
        "would_restage",
        "would_restage",
        "skipped_not_restageable",
    ]
    assert [item["not_restageable_reason"] for item in result["items"]] == [
        None,
        None,
        "ready",
    ]
    assert list_graph_revisions_tool(
        db,
        revision_type="rc:StagedRevision",
    )["count"] == staged_count_before


def test_restage_staged_revisions_tool_serializes_repair_first_warning(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    scope = "https://example.test/project#DispatchTemporalScope"
    clock = "https://example.test/project#dispatch_events__event_local_time"
    timezone = "https://example.test/project#dispatch_events__timezone_hint"
    db.import_turtle(
        """
        @prefix ft: <https://example.test/project/systematisation#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ft:TemporalInterpretationScope a rdfs:Class .

        ft:clockColumn a rdf:Property .

        ft:timezoneEvidenceColumn a rdf:Property .
        """,
        graph="ontology",
    )
    db.import_turtle(
        """
        @prefix ft: <https://example.test/project/systematisation#> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .

        ft:TemporalInterpretationScopeShape a sh:NodeShape ;
            sh:targetClass ft:TemporalInterpretationScope ;
            sh:property [
                sh:path ft:timezoneEvidenceColumn ;
                sh:minCount 1 ;
                sh:nodeKind sh:IRI
            ] .
        """,
        graph="shapes",
    )
    source = db.stage_graph_revision(
        summary="Stage incomplete temporal scope",
        rationale="The source intentionally fails staged validation.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix ft: <https://example.test/project/systematisation#> .

                    <{scope}> a ft:TemporalInterpretationScope ;
                        ft:clockColumn <{clock}> .
                """,
            }
        ],
        validation_scope="all",
    )
    db.import_turtle(
        f"""
        @prefix ft: <https://example.test/project/systematisation#> .

        <{scope}> ft:timezoneEvidenceColumn <{timezone}> .
        """,
        graph="map",
    )

    result = restage_staged_revisions_tool(
        db,
        revision_iris=[source.revision_iri],
        dry_run=True,
    )

    item = result["items"][0]
    assert item["action"] == "would_restage"
    assert result["would_restage_revision_iris"] == []
    assert result["repair_first_revision_iris"] == [source.revision_iri]
    assert item["source_staged_validation_status"] == "failed"
    assert item["routing_decision_after"] == "repair_or_replace"
    assert any(
        action["tool_name"] == "draft_staged_revision_rebase"
        for action in item["suggested_next_actions_after"]
    )
    assert not any(
        action["tool_name"] == "restage_staged_revision"
        for action in item["suggested_next_actions_after"]
    )
    assert item["repair_first_warning"] is not None
    assert "Repair-first warning" in item["repair_first_warning"]
    assert item["repair_first_warning"] in item["note"]


def test_export_staged_revisions_tool_resolves_relative_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mcp_tools, "ROOT", tmp_path)
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = stage_graph_revision_tool(
        db,
        summary="Stage messages table",
        rationale="Messages should become durable map context after review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Messages a rc:Dataset .
                """,
            }
        ],
        review_recommendation="Old authored review guidance should not mask live status.",
    )

    export = export_staged_revisions_tool(
        db,
        revision_iris=[staged["revision_iri"], staged["revision_iri"]],
        path="nested/../bundle.md",
        title="Relative bundle",
    )

    expected_path = (tmp_path / "bundle.md").resolve()
    assert export["path"] == str(expected_path)
    assert export["revision_iris"] == [staged["revision_iri"]]
    assert len(export["revision_summaries"]) == 1
    assert export["bundle_summary"]["apply_status_counts"] == {"ready": 1}
    assert export["bundle_summary"]["stale_resolution_state_counts"] == {"ready": 1}
    assert export["bundle_summary"]["post_apply_recheck_revision_iris"] == []
    snapshot_evidence = export["bundle_summary"]["snapshot_evidence"]
    assert snapshot_evidence["complete"] is True
    assert snapshot_evidence["total_revision_count"] == 1
    assert snapshot_evidence["status_counts"] == {"history_plus_snapshot_rows": 1}
    assert snapshot_evidence["rows"][0]["revision_iri"] == staged["revision_iri"]
    assert snapshot_evidence["rows"][0]["completeness"] == "complete"
    assert snapshot_evidence["rows"][0]["suggested_next_actions"] == []
    exported = expected_path.read_text(encoding="utf-8")
    assert "## Snapshot Evidence" in exported
    assert "Snapshot evidence complete for 1/1 revision row(s)." in exported
    assert "Status counts: history_plus_snapshot_rows: 1" in exported
    assert "Exact rows available for graph role(s): map" in exported
    assert "## Review Sequence" in exported
    assert "| Phase | Row | Candidate | Queue | Resolved target | Tool | Why |" in (
        exported
    )
    assert "| Review/apply ready | 1 | Stage messages table | apply_after_review |" in (
        exported
    )
    assert export["bundle_summary"]["recommended_review_iris"] == [
        staged["revision_iri"]
    ]
    assert export["bundle_summary"]["external_recommended_review_iris"] == []
    assert export["bundle_summary"]["recommended_mutation_review_iris"] == [
        staged["revision_iri"]
    ]
    assert export["bundle_summary"]["recommended_apply_or_restage_review_iris"] == [
        staged["revision_iri"]
    ]
    assert export["bundle_summary"]["recommended_repair_review_iris"] == []
    assert export["bundle_summary"]["warnings"] == []
    assert export["bundle_summary"]["validation_failed_revision_iris"] == []
    assert export["bundle_summary"]["recommended_applied_inspection_iris"] == []
    assert export["bundle_summary"]["next_action_queue"] == {
        "apply_after_review": [staged["revision_iri"]]
    }
    assert export["bundle_summary"]["next_action_queue_item_counts"] == {
        "apply_after_review": 1
    }
    assert export["bundle_summary"]["mutation_frontier_iris"] == [
        staged["revision_iri"]
    ]
    assert export["bundle_summary"]["requires_recheck_after_each_apply"] is False
    assert export["bundle_summary"]["semantic_review_required_queue_counts"] == {}
    export_queue_item = export["bundle_summary"]["next_action_queue_items"][0]
    assert export_queue_item["row_iri"] == staged["revision_iri"]
    assert export_queue_item["queue"] == "apply_after_review"
    assert export_queue_item["resolved_target_iri"] == staged["revision_iri"]
    assert export_queue_item["resolved_target_record_kind"] == "staged_patch"
    assert export_queue_item["row_is_target"] is True
    assert export_queue_item["alternative_semantic_review_required"] is False
    review_sequence = export["bundle_summary"]["review_sequence"]
    assert [item["phase"] for item in review_sequence] == ["review_apply"]
    review_sequence_item = review_sequence[0]
    assert review_sequence_item["phase_label"] == "Review/apply ready"
    assert review_sequence_item["row_index"] == 1
    assert review_sequence_item["row_iri"] == staged["revision_iri"]
    assert review_sequence_item["summary"] == "Stage messages table"
    assert review_sequence_item["queue"] == "apply_after_review"
    assert review_sequence_item["resolved_target_iri"] == staged["revision_iri"]
    assert review_sequence_item["resolved_target_record_kind"] == "staged_patch"
    assert review_sequence_item["tool_name"] == "apply_staged_revision"
    assert (
        review_sequence_item["mcp_tool_name"] == "doxabase.apply_staged_revision"
    )
    assert "Review semantic context" in review_sequence_item["reason"]
    assert export["revision_summaries"][0]["revision_iri"] == staged["revision_iri"]
    assert export["revision_summaries"][0]["alternative_to"] is None
    assert export["revision_summaries"][0]["current_alternative_to"] is None
    assert export["revision_summaries"][0]["stale_resolution_state"] == "ready"
    assert export["revision_summaries"][0]["apply_status"] == "ready"
    assert export["revision_summaries"][0]["apply_decision"] == "review_then_apply"
    assert export["revision_summaries"][0]["review_recommendation"] == (
        "Old authored review guidance should not mask live status."
    )
    assert (
        export["revision_summaries"][0]["apply_recommendation_scope"]
        == "current_apply_check"
    )
    assert (
        export["revision_summaries"][0]["summary_recommendation_source"]
        == "apply_recommended_resolution"
    )
    assert export["revision_summaries"][0]["summary_recommendation"] != (
        "Old authored review guidance should not mask live status."
    )
    assert (
        export["revision_summaries"][0]["active_recommendation_field"]
        == "summary_recommendation"
    )
    assert export["revision_summaries"][0]["current_validation"] == (
        "True (0 result(s))"
    )
    assert export["revision_summaries"][0]["staged_validation"] == (
        "True (0 result(s))"
    )
    assert export["revision_summaries"][0]["suggested_next_actions"][-1][
        "tool_name"
    ] == "apply_staged_revision"
    assert export["revision_summaries"][0]["next_action"]["action_type"] == (
        "apply_after_review"
    )
    assert export["revision_summaries"][0]["next_action"]["queue"] == (
        "apply_after_review"
    )
    assert export["revision_summaries"][0]["next_action"]["tool_name"] == (
        "apply_staged_revision"
    )
    assert expected_path.exists()
    assert expected_path.read_text(encoding="utf-8").startswith("# Relative bundle\n")


def test_list_graph_revisions_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = stage_graph_revision_tool(
        db,
        summary="Stage messages table",
        rationale="Messages should become durable map context after review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Messages a rc:Dataset .
                """,
            }
        ],
        created_at="2026-06-01T10:00:00Z",
    )
    result = list_graph_revisions_tool(
        db,
        revision_type="rc:StagedRevision",
        include_apply_checks=True,
    )

    assert result["count"] == 1
    assert result["returned_count"] == 1
    assert result["total_count"] == 1
    assert result["include_apply_checks"] is True
    assert result["drift_detail"] == "summary"
    assert result["revision_type"] == "https://richcanopy.org/ns/rc#StagedRevision"
    assert result["record_kind"] is None
    assert result["application_status"] is None
    assert result["staged_validation_status"] is None
    assert result["stale_resolution_state"] is None
    assert result["current_staged_work_only"] is False
    assert result["returned_application_status_counts"] == {"ready": 1}
    assert result["returned_current_staged_work_application_status_counts"] == {
        "ready": 1
    }
    assert result["returned_stale_resolution_state_counts"] == {"ready": 1}
    assert result["returned_staged_validation_status_counts"] == {"conforms": 1}
    assert result["next_action_queue"] == {
        "apply_after_review": [staged["revision_iri"]]
    }
    assert result["next_action_queue_item_counts"] == {"apply_after_review": 1}
    assert result["semantic_review_required_queue_counts"] == {}
    queue_item = result["next_action_queue_items"][0]
    assert queue_item["row_iri"] == staged["revision_iri"]
    assert queue_item["queue"] == "apply_after_review"
    assert queue_item["action_type"] == "apply_after_review"
    assert queue_item["resolved_target_iri"] == staged["revision_iri"]
    assert queue_item["resolved_target_iri_source"] == "next_action.arguments.iri"
    assert queue_item["resolved_target_record_kind"] == "staged_patch"
    assert queue_item["row_is_target"] is True
    assert queue_item["record_kind"] == "staged_patch"
    assert queue_item["application_status"] == "ready"
    assert queue_item["staged_validation_status"] == "conforms"
    assert queue_item["alternative_semantic_review_required"] is False
    assert result["revisions"][0]["iri"] == staged["revision_iri"]
    assert result["revisions"][0]["record_kind"] == "staged_patch"
    assert result["revisions"][0]["is_current_staged_work"] is True
    assert result["revisions"][0]["not_current_staged_work_reason"] is None
    assert result["revisions"][0]["has_patch_payload"] is True
    assert result["revisions"][0]["patch_count"] == 1
    assert result["revisions"][0]["snapshot_evidence"]["status"] == (
        "history_plus_snapshot_rows"
    )
    assert result["revisions"][0]["snapshot_evidence"]["exact_snapshot_graph_roles"] == [
        "map"
    ]
    assert result["revisions"][0]["application_status"] == "ready"
    assert result["revisions"][0]["staged_validation_status"] == "conforms"
    assert result["revisions"][0]["application_decision"] == "review_then_apply"
    assert result["revisions"][0]["application_can_apply"] is True
    assert result["revisions"][0]["next_action"]["action_type"] == (
        "apply_after_review"
    )
    assert result["revisions"][0]["next_action"]["tool_name"] == (
        "apply_staged_revision"
    )
    assert result["revisions"][0]["suggested_next_actions"]

    ready_result = list_graph_revisions_tool(
        db,
        revision_type="rc:StagedRevision",
        application_status="ready",
    )

    assert ready_result["include_apply_checks"] is True
    assert ready_result["application_status"] == "ready"
    assert ready_result["returned_application_status_counts"] == {"ready": 1}
    assert ready_result["count"] == 1
    assert ready_result["returned_count"] == 1
    assert ready_result["total_count"] == 1
    assert ready_result["revisions"][0]["iri"] == staged["revision_iri"]

    staged_patch_result = list_graph_revisions_tool(
        db,
        record_kind="staged_patch",
        current_staged_work_only=True,
    )

    assert staged_patch_result["record_kind"] == "staged_patch"
    assert staged_patch_result["current_staged_work_only"] is True
    assert staged_patch_result["include_apply_checks"] is True
    assert staged_patch_result["count"] == 1
    assert staged_patch_result["returned_count"] == 1
    assert staged_patch_result["total_count"] == 1
    assert staged_patch_result["revisions"][0]["iri"] == staged["revision_iri"]

    stored_conforms_result = list_graph_revisions_tool(
        db,
        revision_type="rc:StagedRevision",
        staged_validation_status="conforms",
    )

    assert stored_conforms_result["include_apply_checks"] is False
    assert stored_conforms_result["staged_validation_status"] == "conforms"
    assert stored_conforms_result["count"] == 1
    assert stored_conforms_result["returned_count"] == 1
    assert stored_conforms_result["total_count"] == 1
    assert stored_conforms_result["revisions"][0]["iri"] == staged["revision_iri"]
    assert (
        staged_patch_result["revisions"][0]["not_current_staged_work_reason"]
        is None
    )

    sibling = stage_graph_revision_tool(
        db,
        summary="Stage threads table",
        rationale="Threads should be rechecked after sibling map applies.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Threads a rc:Dataset .
                """,
            }
        ],
        created_at="2026-06-01T10:02:00Z",
    )
    applied = apply_staged_revision_tool(
        db,
        iri=staged["revision_iri"],
        created_at="2026-06-01T10:01:00Z",
    )
    mixed_page = list_graph_revisions_tool(
        db,
        include_apply_checks=True,
        limit=1,
        offset=0,
    )

    assert mixed_page["count"] == 3
    assert mixed_page["returned_count"] == 1
    assert mixed_page["total_count"] == 3
    assert len(mixed_page["revisions"]) == 1
    assert mixed_page["revisions"][0]["iri"] == sibling["revision_iri"]
    assert mixed_page["returned_application_status_counts"] == {"conflict": 1}
    assert mixed_page["returned_current_staged_work_application_status_counts"] == {
        "conflict": 1
    }
    assert mixed_page["returned_stale_resolution_state_counts"] == {
        "stale_unresolved": 1
    }
    assert mixed_page["returned_staged_validation_status_counts"] == {"conforms": 1}
    assert mixed_page["next_action_queue"] == {
        "restage_after_review": [sibling["revision_iri"]]
    }
    second_page = list_graph_revisions_tool(
        db,
        include_apply_checks=True,
        limit=1,
        offset=1,
    )
    assert second_page["count"] == 3
    assert second_page["returned_count"] == 1
    assert second_page["total_count"] == 3
    assert second_page["revisions"][0]["iri"] == applied["applied_revision_iri"]
    assert second_page["returned_application_status_counts"] == {
        "applied_event": 1
    }
    assert second_page["returned_current_staged_work_application_status_counts"] == {}
    assert second_page["next_action_queue"] == {
        "inspect_already_applied": [applied["applied_revision_iri"]]
    }
    assert second_page["next_action_queue_item_counts"] == {
        "inspect_already_applied": 1
    }
    second_queue_item = second_page["next_action_queue_items"][0]
    assert second_queue_item["row_iri"] == applied["applied_revision_iri"]
    assert second_queue_item["resolved_target_iri"] == applied["applied_revision_iri"]
    assert second_queue_item["resolved_target_record_kind"] == "applied_event"
    assert second_queue_item["row_is_target"] is True
    assert second_queue_item["record_kind"] == "applied_event"
    applied_row = second_page["revisions"][0]
    assert applied_row["next_action"]["tool_name"] == "describe_graph_revision"
    assert [
        action["tool_name"] for action in applied_row["suggested_next_actions"]
    ] == [
        "describe_graph_revision",
        "describe_applied_revision_diff",
    ]
    assert applied_row["suggested_next_actions"][1]["arguments"] == {
        "iri": applied["applied_revision_iri"]
    }


def test_list_resource_revisions_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    staged = stage_graph_revision_tool(
        db,
        summary="Add Orders stewardship note",
        rationale="Patch touches Orders without an explicit revision anchor.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Orders rdfs:comment "Owned by the operations team." .
                """,
            }
        ],
        created_at="2026-06-01T10:00:00Z",
    )
    applied = apply_staged_revision_tool(
        db,
        staged["revision_iri"],
        created_at="2026-06-01T10:01:00Z",
    )

    result = list_resource_revisions_tool(db, resource_iri=orders)

    assert result["resource"]["iri"] == orders
    assert "items" not in result
    assert result["current_staged_work_only"] is False
    assert result["patch_mention_scan"] == {
        "status": "complete",
        "unreadable_patch_count": 0,
        "unreadable_revision_count": 0,
        "omitted_match_risk": False,
    }
    assert result["count"] == 2
    assert result["returned_count"] == 2
    assert result["total_count"] == 2
    assert len(result["revisions"]) == 2
    by_iri = {item["revision"]["iri"]: item for item in result["revisions"]}
    assert {item["revision_iri"] for item in result["revisions"]} == set(by_iri)
    assert by_iri[staged["revision_iri"]]["match_types"] == ["patch_subject"]
    assert by_iri[staged["revision_iri"]]["patch_mentions_incomplete"] is False
    assert by_iri[staged["revision_iri"]]["patch_mentions_unreadable_count"] == 0
    assert by_iri[staged["revision_iri"]]["patch_mentions"][0][
        "matched_term_roles"
    ] == ["subject"]
    assert by_iri[staged["revision_iri"]]["patch_mentions"][0][
        "matched_triples"
    ] == 1
    assert by_iri[applied["applied_revision_iri"]]["match_types"] == [
        "applied_source_patch_subject"
    ]
    assert by_iri[applied["applied_revision_iri"]]["applied_source_revision_iri"] == (
        staged["revision_iri"]
    )
    assert by_iri[applied["applied_revision_iri"]][
        "applied_source_patch_mentions_incomplete"
    ] is False
    live_only = list_resource_revisions_tool(
        db,
        resource_iri=orders,
        current_staged_work_only=True,
        include_apply_checks=False,
    )
    assert live_only["current_staged_work_only"] is True
    assert live_only["include_apply_checks"] is True
    assert live_only["count"] == 0
    assert live_only["returned_count"] == 0
    assert live_only["total_count"] == 0
    lineage = describe_resource_revision_lineage_tool(
        db,
        resource_iri=orders,
        revision_iri=applied["applied_revision_iri"],
        include_triples=True,
    )
    assert lineage["selected_role"] == "applied_event"
    assert lineage["selected_revision_iri"] == applied["applied_revision_iri"]
    assert lineage["paired_revision"]["revision"]["iri"] == staged["revision_iri"]
    assert lineage["paired_revision_iri"] == staged["revision_iri"]
    assert lineage["current_staged_revision_iri"] is None
    assert lineage["current_revision_iri"] is None
    assert lineage["latest_revision_iri"] == applied["applied_revision_iri"]
    assert lineage["latest_role"] == "applied_event"
    assert lineage["restage_chain_iris"] == [staged["revision_iri"]]
    assert lineage["alternative_revision_iris"] == []
    assert lineage["next_action_queue_item"]["row_iri"] == (
        applied["applied_revision_iri"]
    )
    assert lineage["next_action_queue_item"]["resolved_target_iri"] == (
        applied["applied_revision_iri"]
    )
    assert lineage["next_action_queue_item"]["row_is_target"] is True
    assert lineage["applied_diff_status"] == "available"
    assert lineage["applied_diff"]["graph_diffs"][0][
        "resource_triples_added_count"
    ] == 1
    assert lineage["applied_diff"]["graph_diffs"][0]["resource_triples_added"][0][
        "subject"
    ] == orders
    generic_lineage = describe_revision_lineage_tool(
        db,
        iri=applied["applied_revision_iri"],
    )
    assert generic_lineage["selected_role"] == "applied_event"
    assert generic_lineage["selected_revision_iri"] == (
        applied["applied_revision_iri"]
    )
    assert generic_lineage["selected_revision"]["iri"] == (
        applied["applied_revision_iri"]
    )
    assert generic_lineage["paired_revision"]["iri"] == staged["revision_iri"]
    assert generic_lineage["paired_revision_iri"] == staged["revision_iri"]
    assert generic_lineage["paired_role"] == "applied_source"
    assert generic_lineage["applied_revision_iri"] == applied["applied_revision_iri"]
    assert generic_lineage["staged_revision_iri"] == staged["revision_iri"]
    assert generic_lineage["applied_source_revision_iri"] == staged["revision_iri"]
    assert generic_lineage["latest_revision_iri"] == applied["applied_revision_iri"]
    assert generic_lineage["latest_role"] == "applied_event"
    assert generic_lineage["restage_chain_iris"] == [staged["revision_iri"]]
    assert generic_lineage["next_action_queue_item"]["resolved_target_iri"] == (
        applied["applied_revision_iri"]
    )
    assert generic_lineage["next_action_queue_item"]["row_is_target"] is True
    assert generic_lineage["related_revision_iris"] == [
        applied["applied_revision_iri"],
        staged["revision_iri"],
    ]
    assert generic_lineage["next_action"]["queue"] == "inspect_already_applied"
    assert generic_lineage["suggested_next_calls"] == [
        f"describe_graph_revision(iri='{applied['applied_revision_iri']}')",
        (
            "describe_applied_revision_diff("
            f"iri='{applied['applied_revision_iri']}')"
        ),
        f"describe_staged_revision(iri='{staged['revision_iri']}')",
    ]
    assert generic_lineage["warnings"] == []


def test_draft_map_assertion_change_tool_returns_json_like_payload_without_write(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)
    before_map_count = db.triple_count("map")
    before_history_count = db.triple_count("history")

    result = draft_map_assertion_change_tool(
        db,
        subject="https://richcanopy.org/example/manifest/polymarket#px_price",
        predicate="rc:physicalType",
        object="rc:Double",
        rationale=(
            "Preview a tempting but unsafe type change before deciding whether "
            "to stage it."
        ),
        change_kind="replace",
    )

    assert result["result_kind"] == "draft_map_assertion_change"
    assert result["change_kind"] == "replace"
    assert result["assertion_present_before"] is False
    assert result["changed_graphs"] == ["map"]
    assert result["validation_conforms"] is True
    assert result["validation_result_count"] == 0
    assert result["assertion_support"]["related_route_summaries"]
    assert result["judgement_panel"]["semantic_risk_level"] == "high"
    assert any(
        impact["impact_type"] == "changed_physical_type"
        for impact in result["impacts"]
    )
    assert [
        action["tool_name"] for action in result["suggested_next_actions"]
    ] == ["describe_assertion_support", "stage_map_assertion_change"]
    assert result["suggested_next_actions"][0]["mcp_tool_name"] == (
        "doxabase.describe_assertion_support"
    )
    assert "high-risk" in result["suggested_next_actions"][0]["reason"]
    assert result["suggested_next_actions"][1]["mcp_tool_name"] == (
        "doxabase.stage_map_assertion_change"
    )
    assert result["stage_arguments"]["summary"] == (
        "Replace map assertion: price physicalType DOUBLE"
    )
    assert db.triple_count("map") == before_map_count
    assert db.triple_count("history") == before_history_count


def test_stage_map_assertion_change_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)
    before_map_count = db.triple_count("map")

    result = stage_map_assertion_change_tool(
        db,
        subject="https://richcanopy.org/example/manifest/polymarket#px_price",
        predicate="rc:physicalType",
        object="rc:Double",
        rationale=(
            "Exercise a tempting but unsafe type change so assertion support "
            "travels with the staged revision."
        ),
        change_kind="replace",
    )

    assert result["change_kind"] == "replace"
    assert result["assertion_present_before"] is False
    assert result["assertion_support"]["absence_note"] is not None
    assert "Current same-subject/predicate value(s): VARCHAR" in (
        result["assertion_support"]["absence_note"]
    )
    assert result["assertion_support"]["related_route_summaries"]
    assert result["review_recommendation"].startswith("Review assertion support")
    panel = result["judgement_panel"]
    assert panel["proposed_value"]["label"] == "DOUBLE"
    assert [value["label"] for value in panel["current_values"]] == ["VARCHAR"]
    assert panel["semantic_risk_level"] == "high"
    assert panel["semantic_risk_reasons"]
    assert panel["value_type_context"][0]["value_type"]["label"] == (
        "Raw CLOB Price Payload"
    )
    assert panel["value_type_context"][0]["current_physical_type_matches"] is True
    assert panel["value_type_context"][0]["proposed_physical_type_matches"] is False
    assert panel["caveats"]
    assert any(
        impact["impact_type"] == "changed_physical_type"
        for impact in panel["impacts"]
    )
    assert len(result["additions"]) == 1
    assert len(result["removals"]) == 1
    assert result["staged_revision"]["summary"] == (
        "Replace map assertion: price physicalType DOUBLE"
    )
    assert result["staged_revision"]["rationale"].startswith(
        "Exercise a tempting but unsafe type change"
    )
    assert (
        "Staged map assertion change kind: replace."
        in result["staged_revision"]["review_note"]
    )
    assert (
        "Current same-subject/predicate value(s): VARCHAR"
        in result["staged_revision"]["review_note"]
    )
    assert result["staged_revision"]["review_recommendation"].startswith(
        "Review assertion support"
    )
    assert result["staged_revision"]["changed_graphs"] == ["map"]
    assert result["staged_revision"]["validation_conforms"] is True
    assert result["revision_iri"] == result["staged_revision"]["revision_iri"]
    assert db.triple_count("map") == before_map_count

    description = describe_staged_revision_tool(
        db,
        result["staged_revision"]["revision_iri"],
    )
    assert description["judgement_panel"]["proposed_value"]["label"] == "DOUBLE"
    assert description["stored_review_context"] is None
    assert description["judgement_panel"]["semantic_risk_level"] == "high"
    assert description["supporting_patterns"]
    assert "https://richcanopy.org/ns/rc#Varchar" not in {
        anchor["iri"] for anchor in description["revision_anchors"]
    }
    assert "https://richcanopy.org/ns/rc#Double" not in {
        anchor["iri"] for anchor in description["revision_anchors"]
    }
    assert any(
        impact["impact_type"] == "changed_physical_type"
        for impact in description["impacts"]
    )
    check = check_staged_revision_apply_tool(
        db,
        result["staged_revision"]["revision_iri"],
    )
    assert check["can_apply"] is True
    assert check["status"] == "ready"
    assert check["semantic_risk_level"] == "high"
    assert check["semantic_risk_reasons"]
    assert check["suggested_next_actions"][-1]["tool_name"] == (
        "apply_staged_revision"
    )
    assert check["suggested_next_actions"][-1]["action_label"] == (
        "Apply only after semantic review"
    )

    ais_result = stage_map_assertion_change_tool(
        db,
        subject="https://richcanopy.org/example/manifest/ais#bc_base_date_time",
        predicate="rc:physicalType",
        object="rc:TimestampTZ",
        rationale=(
            "Exercise a second tempting type cleanup after the Polymarket stage."
        ),
        change_kind="replace",
    )
    ais_panel = ais_result["judgement_panel"]
    assert ais_panel["value_type_context"]
    assert ais_panel["value_type_context"][0]["value_type"]["label"] == (
        "Raw AIS Timestamp String"
    )
    assert ais_panel["value_type_context"][0]["required_physical_type"]["label"] == (
        "VARCHAR"
    )
    assert ais_panel["value_type_context"][0]["current_physical_type_matches"] is True
    assert (
        ais_panel["value_type_context"][0]["proposed_physical_type_matches"] is False
    )
    assert any(
        "Raw AIS Timestamp String requires physical type VARCHAR" in note
        for note in ais_panel["why_current_value_may_be_intentional"]
    )
    assert result["staged_revision"]["revision_iri"] not in {
        route["resource_iri"] for route in ais_panel["strongest_routes"]
    }
    ais_description = describe_staged_revision_tool(
        db,
        ais_result["staged_revision"]["revision_iri"],
    )
    assert ais_description["judgement_panel"]["value_type_context"][0][
        "value_type"
    ]["label"] == "Raw AIS Timestamp String"
    assert ais_description["judgement_panel"]["strongest_routes"] == []
    ais_export_path = tmp_path / "ais-judgement-review.md"
    export_staged_revision_tool(
        db,
        iri=ais_result["staged_revision"]["revision_iri"],
        path=str(ais_export_path),
    )
    ais_export = ais_export_path.read_text()
    assert "## Judgement Panel" in ais_export
    assert "### Value Type Context" in ais_export
    assert "Raw AIS Timestamp String" in ais_export
    assert "TIMESTAMP WITH TIME ZONE" in ais_export
    assert "| Value type | Required physical type | Current matches |" in ais_export
    assert "No strong related-lore routes surfaced" in ais_export
    assert db.triple_count("map") == before_map_count

    record_map_dataset_tool(
        db,
        "https://richcanopy.org/example/manifest/polymarket#scratch_drift",
        label="Scratch drift",
        is_table=True,
    )
    stale_description = describe_staged_revision_tool(
        db,
        result["staged_revision"]["revision_iri"],
        include_current_apply_check=True,
    )
    assert stale_description["judgement_panel"] is None
    assert stale_description["stored_review_context"]["semantic_risk_level"] == "high"
    assert stale_description["stored_review_context"]["review_note_signals"][
        "has_value_type_context"
    ] is True
    assert stale_description["stored_review_context"]["linked_support_counts"][
        "patterns"
    ] >= 1
    assert stale_description["stored_review_context"]["attention_impacts"][0][
        "impact_type"
    ] == "changed_physical_type"


def test_assertion_literal_metadata_tools_return_json_like_payloads(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:Orders a rc:Dataset, rc:Table ;
            rdfs:label "Orders"@en ;
            rc:hasColumn ex:is_active .

        ex:is_active a rc:Column ;
            rc:columnName "is_active" ;
            rc:physicalType rc:Boolean ;
            rc:nullable false .
        """,
        graph="map",
    )

    support = describe_assertion_support_tool(
        db,
        subject="https://example.test/project#Orders",
        predicate="rdfs:label",
        object="Orders",
        object_kind="literal",
        object_lang="en",
    )
    assert support["requested_object"]["lang"] == "en"
    assert support["matching_triples"][0]["object_lang"] == "en"

    result = stage_map_assertion_change_tool(
        db,
        subject="https://example.test/project#is_active",
        predicate="rc:nullable",
        object="true",
        object_kind="literal",
        object_datatype="xsd:boolean",
        change_kind="replace",
        rationale="Exercise typed literal metadata through the MCP wrapper.",
    )

    assert result["object_datatype"] == str(XSD.boolean)
    assert result["object_lang"] is None
    assert result["judgement_panel"]["proposed_value"]["datatype"] == str(
        XSD.boolean
    )
    description = describe_staged_revision_tool(
        db,
        result["staged_revision"]["revision_iri"],
    )
    assert description["judgement_panel"]["proposed_value"]["datatype"] == str(
        XSD.boolean
    )


def test_apply_staged_revision_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = stage_graph_revision_tool(
        db,
        summary="Stage messages table",
        rationale="Messages should become durable map context after review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Messages a rc:Dataset, rc:Table ;
                        rdfs:label "Messages" .
                """,
            }
        ],
    )

    check = check_staged_revision_apply_tool(db, iri=staged["revision_iri"])
    assert check["revision_iri"] == staged["revision_iri"]
    assert check["staged_revision_iri"] == staged["revision_iri"]
    assert check["can_apply"] is True
    assert check["status"] == "ready"
    assert check["decision"] == "review_then_apply"
    assert check["routing_decision"] == "apply_after_review"
    assert check["review_recommended"] is True
    assert check["blocking_reasons"] == []
    assert check["validation_skipped_reason"] is None
    assert "proposal is still desired" in check["recommended_resolution"]
    assert check["summary"] == (
        "Ready to apply 1 patch(es) across map: +3 triple(s), -0 triple(s)."
    )
    assert check["conflicts"] == []
    assert check["patch_checks"][0]["count_basis"] == "target_graph_only"
    assert check["patch_checks"][0]["preview_triple_count"] == 3
    assert check["patch_checks"][0]["effective_triples_to_add"] == 3
    assert check["patch_checks"][0]["effective_triples_to_remove"] == 0
    assert check["patch_checks"][0]["already_present_triples"] == 0
    assert check["patch_checks"][0]["already_absent_triples"] == 3
    assert check["suggested_next_actions"][0]["tool_name"] == (
        "describe_staged_revision"
    )
    assert check["suggested_next_calls"][0].startswith("describe_staged_revision(")
    assert check["suggested_next_actions"][-1]["tool_name"] == (
        "apply_staged_revision"
    )

    sibling = stage_graph_revision_tool(
        db,
        summary="Stage threads table",
        rationale="Threads should be rechecked after sibling map applies.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Threads a rc:Dataset .
                """,
            }
        ],
    )
    result = apply_staged_revision_tool(db, iri=staged["revision_iri"])

    assert result["staged_revision_iri"] == staged["revision_iri"]
    assert result["changed_graphs"] == ["map"]
    assert result["post_apply_recheck_revision_iris"] == [sibling["revision_iri"]]
    assert result["post_apply_recheck_is_partial_queue"] is True
    assert result["suggested_next_actions"][0]["tool_name"] == (
        "plan_staged_revision_recovery"
    )
    assert result["suggested_next_actions"][0]["arguments"] == {
        "current_staged_work_only": True
    }
    assert result["suggested_next_calls"][0] == (
        "plan_staged_revision_recovery(current_staged_work_only=True)"
    )
    assert len(result["post_apply_recheck_revisions"]) == 1
    recheck = result["post_apply_recheck_revisions"][0]
    assert recheck["iri"] == sibling["revision_iri"]
    assert recheck["changed_graphs"] == ["map"]
    assert recheck["shared_changed_graphs"] == ["map"]
    assert recheck["recheck_reasons"] == ["shared_changed_graph:map"]
    assert recheck["application_status"] == "conflict"
    assert recheck["decision"] == "restage_against_current_graph"
    assert recheck["routing_decision"] == "restage_after_review"
    assert "target_count_drift" in recheck["blocking_reasons"]
    assert recheck["next_action"]["action_type"] == "restage_after_review"
    assert recheck["next_action"]["tool_name"] == "restage_staged_revision"
    assert recheck["next_action"]["arguments"] == {"iri": sibling["revision_iri"]}
    assert recheck["suggested_next_actions"][-1]["tool_name"] == (
        "restage_staged_revision"
    )
    assert recheck["suggested_next_calls"][-1].startswith(
        "restage_staged_revision("
    )
    assert result["patches_applied"] == 1
    assert result["triples_added"] == 3
    assert result["validation_conforms"] is True
    description = describe_graph_revision_tool(db, result["applied_revision_iri"])
    assert description["record_kind"] == "applied_event"
    assert description["revision_type_label"] == "applied staged revision"
    assert description["applies_staged_revision"] == staged["revision_iri"]
    assert description["snapshot_evidence"]["status"] == "history_plus_snapshot_rows"
    assert description["snapshot_evidence"]["exact_snapshot_graph_roles"] == ["map"]
    assert description["applied_source"]["iri"] == staged["revision_iri"]
    assert description["applied_source"]["summary"] == "Stage messages table"
    assert description["applied_source"]["patch_count"] == 1
    assert description["applied_source"]["patches"][0]["target_graph"] == "map"
    assert "content" not in description["applied_source"]["patches"][0]
    diff = describe_applied_revision_diff_tool(db, result["applied_revision_iri"])
    assert diff["applied_revision_iri"] == result["applied_revision_iri"]
    assert diff["staged_revision_iri"] == staged["revision_iri"]
    assert diff["snapshot_evidence"]["status"] == "history_plus_snapshot_rows"
    assert diff["source_snapshot_evidence"]["status"] == (
        "history_plus_snapshot_rows"
    )
    assert diff["changed_graphs"] == ["map"]
    assert diff["graph_diffs"][0]["graph_role"] == "map"
    assert diff["graph_diffs"][0]["before_triple_count"] == 0
    assert diff["graph_diffs"][0]["after_triple_count"] == 3
    assert diff["graph_diffs"][0]["exact_changed_triples_available"] is True
    assert diff["graph_diffs"][0]["exact_changed_triples_included"] is False
    assert diff["graph_diffs"][0]["triples_added_count"] == 3
    assert diff["graph_diffs"][0]["triples_removed_count"] == 0
    assert diff["graph_diffs"][0]["triples_added_truncated"] is True
    assert diff["graph_diffs"][0]["triples_added"] == []
    exact_diff = describe_applied_revision_diff_tool(
        db,
        result["applied_revision_iri"],
        include_triples=True,
    )
    assert exact_diff["include_triples"] is True
    assert exact_diff["graph_diffs"][0]["exact_changed_triples_included"] is True
    assert {
        triple["subject"]
        for triple in exact_diff["graph_diffs"][0]["triples_added"]
    } == {"https://example.test/project#Messages"}
    after_snapshot = describe_revision_graph_snapshot_tool(
        db,
        result["applied_revision_iri"],
        "map",
        include_triples=True,
        max_triples=2,
    )
    assert after_snapshot["snapshot_evidence"]["status"] == (
        "history_plus_snapshot_rows"
    )
    assert after_snapshot["triple_count"] == 3
    assert after_snapshot["content_digest"] == description["graph_snapshots"][0][
        "content_digest"
    ]
    assert after_snapshot["count_basis"] == "stored_snapshot_rows"
    assert after_snapshot["exact_snapshot_available"] is True
    assert after_snapshot["triples_included"] is True
    assert after_snapshot["triples_truncated"] is True
    assert len(after_snapshot["triples"]) == 2
    assert {triple["subject"] for triple in after_snapshot["triples"]} == {
        "https://example.test/project#Messages"
    }
    project_path = tmp_path / "project.trig"
    snapshot_path = tmp_path / "revision-snapshots.json"
    export_trig_tool(db, path=str(project_path), graphs=["project"])
    snapshot_export = export_revision_snapshots_tool(
        db,
        path=str(snapshot_path),
        revision_iris=[result["applied_revision_iri"]],
    )
    assert snapshot_export["snapshot_count"] == 2
    assert snapshot_export["quad_count"] == 3
    assert snapshot_export["revision_iris"] == [
        result["applied_revision_iri"],
        staged["revision_iri"],
    ]

    round_trip = DoxaBase.create(tmp_path / "round-trip.sqlite")
    round_trip.import_trig(project_path)
    snapshot_status_before_import = describe_revision_snapshot_evidence_tool(
        round_trip,
        result["applied_revision_iri"],
    )
    assert snapshot_status_before_import["status"] == "history_only_count_digest"
    assert snapshot_status_before_import["suggested_next_actions"][0][
        "tool_name"
    ] == "import_revision_snapshots"
    assert snapshot_status_before_import["suggested_next_actions"][0][
        "arguments"
    ] == {
        "path": "/tmp/revision-snapshots.json",
        "path_is_placeholder": True,
    }
    assert "real handoff path" in snapshot_status_before_import[
        "suggested_next_actions"
    ][0]["reason"]
    imported_detail_before_snapshots = describe_graph_revision_tool(
        round_trip,
        result["applied_revision_iri"],
    )
    assert [
        action["tool_name"]
        for action in imported_detail_before_snapshots["suggested_next_actions"][
            :2
        ]
    ] == ["import_revision_snapshots", "describe_graph_revision"]
    imported_list_before_snapshots = list_graph_revisions_tool(
        round_trip,
        record_kind="applied_event",
    )
    assert imported_list_before_snapshots["next_action_queue"] == {
        "complete_handoff_import": [result["applied_revision_iri"]]
    }
    assert imported_list_before_snapshots["revisions"][0]["next_action"][
        "queue"
    ] == "complete_handoff_import"
    imported_diff_before_snapshots = describe_applied_revision_diff_tool(
        round_trip,
        result["applied_revision_iri"],
        include_triples=True,
    )
    assert imported_diff_before_snapshots["snapshot_evidence"]["status"] == (
        "history_only_count_digest"
    )
    assert imported_diff_before_snapshots["snapshot_evidence"][
        "suggested_next_actions"
    ][0]["tool_name"] == "import_revision_snapshots"
    assert (
        imported_diff_before_snapshots["graph_diffs"][0][
            "exact_changed_triples_available"
        ]
        is False
    )
    rdf_only_snapshot = describe_revision_graph_snapshot_tool(
        round_trip,
        result["applied_revision_iri"],
        "map",
        include_triples=True,
    )
    assert rdf_only_snapshot["snapshot_evidence"]["status"] == (
        "history_only_count_digest"
    )
    assert rdf_only_snapshot["triple_count"] == 3
    assert rdf_only_snapshot["count_basis"] == "rdf_history_graph_snapshot"
    assert rdf_only_snapshot["exact_snapshot_available"] is False
    assert rdf_only_snapshot["triples_included"] is False
    assert rdf_only_snapshot["triples"] == []
    snapshot_import = import_revision_snapshots_tool(
        round_trip,
        path=str(snapshot_path),
    )
    assert snapshot_import["imported_snapshot_count"] == 2
    assert snapshot_import["skipped_snapshot_count"] == 0
    assert {
        item["revision_iri"]: item["status"]
        for item in snapshot_import["post_import_snapshot_evidence"]
    } == {
        result["applied_revision_iri"]: "history_plus_snapshot_rows",
        staged["revision_iri"]: "history_plus_snapshot_rows",
    }
    orphan_round_trip = DoxaBase.create(tmp_path / "orphan-round-trip.sqlite")
    orphan_import = import_revision_snapshots_tool(
        orphan_round_trip,
        path=str(snapshot_path),
    )
    assert {
        item["revision_iri"]: item["status"]
        for item in orphan_import["post_import_snapshot_evidence"]
    } == {
        result["applied_revision_iri"]: "snapshot_rows_without_history",
        staged["revision_iri"]: "snapshot_rows_without_history",
    }
    assert orphan_import["post_import_snapshot_evidence"][0][
        "suggested_next_actions"
    ][0]["tool_name"] == "import_trig"
    snapshot_status_after_import = describe_revision_snapshot_evidence_tool(
        round_trip,
        result["applied_revision_iri"],
    )
    assert snapshot_status_after_import["status"] == "history_plus_snapshot_rows"
    assert snapshot_status_after_import["exact_snapshot_graph_roles"] == ["map"]
    imported_exact_diff = describe_applied_revision_diff_tool(
        round_trip,
        result["applied_revision_iri"],
        include_triples=True,
    )
    assert (
        imported_exact_diff["graph_diffs"][0]["exact_changed_triples_available"]
        is True
    )
    assert {
        triple["subject"]
        for triple in imported_exact_diff["graph_diffs"][0]["triples_added"]
    } == {"https://example.test/project#Messages"}
    imported_after_snapshot = describe_revision_graph_snapshot_tool(
        round_trip,
        result["applied_revision_iri"],
        "map",
        include_triples=True,
        max_triples=1,
    )
    assert imported_after_snapshot["snapshot_evidence"]["status"] == (
        "history_plus_snapshot_rows"
    )
    assert imported_after_snapshot["exact_snapshot_available"] is True
    assert imported_after_snapshot["triples_included"] is True
    assert imported_after_snapshot["triples_truncated"] is True
    assert len(imported_after_snapshot["triples"]) == 1
    staged_description = describe_staged_revision_tool(db, staged["revision_iri"])
    assert staged_description["current_apply_check"] is None
    assert staged_description["application_status"] == "already_applied"
    assert staged_description["applied_by"]["iri"] == result["applied_revision_iri"]
    staged_description_with_check = describe_staged_revision_tool(
        db,
        staged["revision_iri"],
        include_current_apply_check=True,
    )
    assert staged_description_with_check["current_apply_check"]["status"] == (
        "already_applied"
    )
    assert staged_description_with_check["current_apply_check"]["decision"] == (
        "inspect_applied_revision"
    )
    assert staged_description_with_check["current_apply_check"][
        "already_applied_by"
    ] == result["applied_revision_iri"]
    assert staged_description_with_check["current_apply_check"]["next_action"][
        "action_type"
    ] == "inspect_already_applied"
    assert staged_description_with_check["current_apply_check"]["next_action"][
        "queue"
    ] == "inspect_already_applied"
    assert staged_description_with_check["current_apply_check"]["next_action"][
        "arguments"
    ] == {"iri": result["applied_revision_iri"]}
    forbidden_summary_keys = {"patch_checks", "conflicts", "validation_results"}
    assert forbidden_summary_keys.isdisjoint(
        staged_description_with_check["current_apply_check"]
    )
    assert describe_dataset_tool(
        db,
        "https://example.test/project#Messages",
    )["label"] == "Messages"
    sibling_check = check_staged_revision_apply_tool(
        db,
        iri=sibling["revision_iri"],
    )
    assert sibling_check["status"] == "conflict"
    assert "target_count_drift" in sibling_check["blocking_reasons"]
    with pytest.raises(DoxaBaseError) as export_exc:
        export_staged_revisions_tool(
            db,
            revision_iris=[staged["revision_iri"], result["applied_revision_iri"]],
            path=str(tmp_path / "mixed-applied-event-review.md"),
        )
    export_message = str(export_exc.value)
    assert "export_staged_revisions only accepts staged patch revisions" in (
        export_message
    )
    assert "applied revision event" in export_message
    assert staged["revision_iri"] in export_message


def test_stage_systematisation_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    observation = db.record_observation(
        "Message-like rows repeatedly require identity reasoning.",
        evidence_summary="Synthetic test note backing the staged systematisation.",
        evidence_sources=["test://identity-ladder"],
    )
    ontology_framing = """
    @prefix ex: <https://example.test/project#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:IdentityLadder a rdfs:Class ;
        rdfs:label "Identity ladder" .
    """
    pattern_framing = f"""
    @prefix ex: <https://example.test/project#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:IdentityLadderPattern a rc:Pattern ;
        rdfs:label "Identity ladder pattern" ;
        rc:summary "Identity hints become stronger as more columns agree." ;
        rc:patternText "Repeated message-like rows appear to form a ladder of identity hints." ;
        rc:rationale "This keeps the idea exploratory without forcing a single key model." ;
        rc:patternTarget ex:Messages ;
        rc:supportingObservation <{observation.observation_iri}> ;
        rc:patternStability rc:EmergingPattern .
    """
    map_framing = """
    @prefix ex: <https://example.test/project#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:Messages a rc:Dataset, rc:Table ;
        rdfs:label "Messages" .
    """

    result = stage_systematisation_tool(
        db,
        summary="Explore identity-ladder modelling",
        intent="Preserve two possible RDF shapes for the same modelling hunch.",
        anchors=[observation.observation_iri],
        shared_additions=[{"graph": "ontology", "content": ontology_framing}],
        shared_context_summary="Define provisional identity-ladder vocabulary once.",
        framings=[
            {
                "label": "Pattern first",
                "graph": "patterns",
                "content": pattern_framing,
                "review_note": "The pattern framing keeps the idea tentative.",
                "review_recommendation": "Preferred until the map vocabulary settles.",
            },
            {
                "label": "Map candidate",
                "graph": "map",
                "content": map_framing,
                "stance": "rc:CandidateRevision",
                "reviewNote": "This is reviewable but slightly too early.",
                "reviewRecommendation": "Keep as a concrete alternative.",
            },
        ],
    )

    assert result["result_kind"] == "systematisation_draft"
    assert result["summary"] == "Explore identity-ladder modelling"
    assert result["anchors"] == [observation.observation_iri]
    assert len(result["framings"]) == 2
    assert len(result["staged_revisions"]) == 2
    revision_iris = [
        revision["revision_iri"] for revision in result["staged_revisions"]
    ]
    assert result["next_action_queue"] == {"apply_after_review": revision_iris}
    assert result["next_action_queue_item_counts"] == {"apply_after_review": 2}
    assert result["semantic_review_required_queue_counts"] == {}
    assert len(result["structured_warnings"]) == 1
    shared_warning = result["structured_warnings"][0]
    assert shared_warning["warning_code"] == (
        "shared_semantic_context_applies_to_all_framings"
    )
    assert shared_warning["message"] == result["warnings"][-1]
    assert shared_warning["affected_revision_iris"] == revision_iris
    assert shared_warning["suggested_action"] == (
        "rerun_with_shared_semantic_context_moved_to_framings"
    )
    assert shared_warning["suggested_rerun_arguments"] == {
        "move_shared_patch_graphs_into_framing_patches": ["ontology"],
        "shared_patch_sources_to_move": [
            {
                "source_argument": "shared_additions",
                "source_index": 0,
                "operation": "addition",
                "graph": "ontology",
            }
        ],
    }
    assert shared_warning["fallback_revision_iris_with_shared_semantic_context"] == [
        revision_iris[1]
    ]
    assert shared_warning["shared_patch_summaries"] == [
        {
            "target_graph": "ontology",
            "operation": RC + "AdditionPatch",
            "operation_label": "addition patch",
            "patch_role": RC + "SharedContextPatch",
            "patch_role_label": "shared context patch",
            "sequence_index": 1,
            "triple_count": 2,
            "count_basis": "target_graph_plus_base_ontology",
            "format": "turtle",
        }
    ]
    assert [
        item["row_iri"] for item in result["next_action_queue_items"]
    ] == revision_iris
    assert [
        item["resolved_target_iri"] for item in result["next_action_queue_items"]
    ] == revision_iris
    assert all(item["row_is_target"] for item in result["next_action_queue_items"])
    assert [
        item["alternative_set_iris"] for item in result["next_action_queue_items"]
    ] == [revision_iris, revision_iris]
    assert [
        item["alternative_set_source_iri"]
        for item in result["next_action_queue_items"]
    ] == [revision_iris[0], revision_iris[0]]
    assert [
        item["alternative_set_role"] for item in result["next_action_queue_items"]
    ] == ["source", "alternative"]
    assert result["suggested_next_actions"][0]["tool_name"] == (
        "export_staged_revisions"
    )
    assert result["suggested_next_actions"][0]["arguments"]["revision_iris"] == (
        revision_iris
    )
    assert result["suggested_next_actions"][0]["arguments"]["path"].startswith(
        "/tmp/systematisation-review-"
    )
    assert result["suggested_next_actions"][0]["arguments"]["path"].endswith(".md")
    assert [
        action["arguments"]
        for action in result["suggested_next_actions"]
        if action["tool_name"] == "check_staged_revision_apply"
    ] == [{"iri": revision_iri} for revision_iri in revision_iris]
    assert result["staged_revisions"][0]["summary"] == (
        "Explore identity-ladder modelling: Pattern first"
    )
    assert result["staged_revisions"][0]["review_note"] == (
        "The pattern framing keeps the idea tentative."
    )
    assert result["staged_revisions"][0]["review_recommendation"] == (
        "Preferred until the map vocabulary settles."
    )
    assert result["staged_revisions"][1]["summary"] == (
        "Explore identity-ladder modelling: Map candidate"
    )
    assert result["staged_revisions"][1]["review_note"] == (
        "This is reviewable but slightly too early."
    )
    assert result["staged_revisions"][1]["review_recommendation"] == (
        "Keep as a concrete alternative."
    )
    assert result["framings"][0]["target_graphs"] == ["ontology", "patterns"]
    assert result["framings"][1]["target_graphs"] == ["ontology", "map"]
    assert result["framings"][0]["validation_conforms"] is True
    assert result["framings"][1]["validation_conforms"] is True
    assert result["framings"][0]["review_note"] == (
        "The pattern framing keeps the idea tentative."
    )
    assert result["framings"][1]["review_recommendation"] == (
        "Keep as a concrete alternative."
    )

    first_iri = result["staged_revisions"][0]["revision_iri"]
    second = describe_staged_revision_tool(
        db,
        result["staged_revisions"][1]["revision_iri"],
    )
    assert second["alternative_to"]["iri"] == first_iri
    assert second["revision_anchors"][0]["iri"] == observation.observation_iri
    assert second["patches"][0]["patch_role_label"] == "shared context patch"
    assert second["patches"][1]["patch_role_label"] == "framing patch"
    assert "Systematisation intent:" in second["rationale"]

    export_path = tmp_path / "identity-ladder-review.md"
    export = export_staged_revisions_tool(
        db,
        revision_iris=revision_iris,
        path=str(export_path),
        title="Identity ladder MCP bundle",
        executive_summary="Pattern-first is preferred, but both framings remain useful.",
    )
    exported = export_path.read_text(encoding="utf-8")
    assert export["revision_iris"] == [
        revision["revision_iri"] for revision in result["staged_revisions"]
    ]
    assert export["bundle_summary"]["shared_context_graphs"] == ["ontology"]
    assert export["bundle_summary"][
        "fallback_revision_iris_with_shared_semantic_context"
    ] == [revision_iris[1]]
    assert export["bundle_summary"]["shared_context_patch_summaries"] == [
        {
            "target_graph": "ontology",
            "operation": RC + "AdditionPatch",
            "operation_label": "addition patch",
            "patch_role": RC + "SharedContextPatch",
            "patch_role_label": "shared context patch",
            "sequence_index": 1,
            "triple_count": 2,
            "count_basis": "target_graph_plus_base_ontology",
            "format": "turtle",
        }
    ]
    assert len(export["bundle_summary"]["shared_semantic_context_warnings"]) == 1
    assert export["bundle_summary"]["shared_semantic_context_warnings"][0][
        "warning_code"
    ] == "shared_semantic_context_applies_to_all_framings"
    assert [
        summary["shared_context_patch_count"]
        for summary in export["revision_summaries"]
    ] == [1, 1]
    assert [
        summary["shared_context_graphs"] for summary in export["revision_summaries"]
    ] == [["ontology"], ["ontology"]]
    assert exported.startswith("# Identity ladder MCP bundle\n")
    assert "## Review Summary" in exported
    assert "Pattern-first is preferred" in exported
    assert "Shared ontology or shapes context patches are present" in exported
    assert "## Reviewer Decision Matrix" in exported
    assert "Rows 1 and 2 are competing alternatives" in exported
    assert "Authored recommendation" in exported
    assert "Preferred until the map vocabulary settles." in exported
    assert "The pattern framing keeps the idea tentative." in exported
    assert "## Summary" in exported
    assert "Pattern first" in exported
    assert "Map candidate" in exported


def test_stage_systematisation_tool_warns_when_first_anchor_fails(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    shared_shape = """
    @prefix ex: <https://example.test/project#> .
    @prefix sh: <http://www.w3.org/ns/shacl#> .

    ex:ThingShape a sh:NodeShape ;
        sh:targetClass ex:Thing ;
        sh:property [
            sh:path ex:required ;
            sh:minCount 1
        ] .
    """
    incomplete_map = """
    @prefix ex: <https://example.test/project#> .

    ex:Thing1 a ex:Thing .
    """
    complete_map = """
    @prefix ex: <https://example.test/project#> .

    ex:Thing1 a ex:Thing ;
        ex:required ex:Value .
    """
    complementary_map = """
    @prefix ex: <https://example.test/project#> .

    ex:Thing1 a ex:Thing ;
        ex:required ex:OtherValue .
    """

    result = stage_systematisation_tool(
        db,
        summary="Compare thing framings",
        intent="Keep a diagnostic invalid framing beside valid map framings.",
        shared_additions=[{"graph": "shapes", "content": shared_shape}],
        framings=[
            {
                "label": "Diagnostic incomplete thing",
                "graph": "map",
                "content": incomplete_map,
            },
            {
                "label": "Complete thing",
                "graph": "map",
                "content": complete_map,
            },
            {
                "label": "Complementary complete thing",
                "graph": "map",
                "content": complementary_map,
            },
        ],
    )

    revision_iris = [
        revision["revision_iri"] for revision in result["staged_revisions"]
    ]
    assert result["next_action_queue"] == {
        "repair_or_replace": [revision_iris[0]],
        "apply_after_review": [revision_iris[1], revision_iris[2]],
    }
    assert any(
        "First framing 'Diagnostic incomplete thing'" in warning
        and "failed staged validation" in warning
        and revision_iris[0] in warning
        and "link_alternatives=False" in warning
        for warning in result["warnings"]
    )
    assert len(result["structured_warnings"]) == 2
    shared_warning = result["structured_warnings"][0]
    assert shared_warning["warning_code"] == (
        "shared_semantic_context_applies_to_all_framings"
    )
    assert shared_warning["message"] == result["warnings"][-2]
    assert shared_warning["affected_revision_iris"] == revision_iris
    assert shared_warning["suggested_action"] == (
        "rerun_with_shared_semantic_context_moved_to_framings"
    )
    assert shared_warning["suggested_rerun_arguments"] == {
        "move_shared_patch_graphs_into_framing_patches": ["shapes"],
        "shared_patch_sources_to_move": [
            {
                "source_argument": "shared_additions",
                "source_index": 0,
                "operation": "addition",
                "graph": "shapes",
            }
        ],
    }
    assert shared_warning["fallback_revision_iris_with_shared_semantic_context"] == [
        revision_iris[1],
        revision_iris[2],
    ]
    assert shared_warning["shared_patch_summaries"] == [
        {
            "target_graph": "shapes",
            "operation": RC + "AdditionPatch",
            "operation_label": "addition patch",
            "patch_role": RC + "SharedContextPatch",
            "patch_role_label": "shared context patch",
            "sequence_index": 1,
            "triple_count": 5,
            "count_basis": "target_graph_plus_base_shapes",
            "format": "turtle",
        }
    ]
    anchor_warning = result["structured_warnings"][1]
    assert anchor_warning == {
        "warning_code": "first_alternative_anchor_not_ready",
        "message": result["warnings"][-1],
        "affected_revision_iris": revision_iris,
        "suggested_action": "rerun_with_explicit_alternative_routing",
        "suggested_rerun_arguments": {"link_alternatives": False},
        "shared_patch_summaries": [],
        "fallback_revision_iris_with_shared_semantic_context": [],
    }
    rerun_action = result["suggested_next_actions"][0]
    assert rerun_action["tool_name"] == "stage_systematisation"
    assert rerun_action["action_label"] == (
        "Rerun with explicit alternative routing"
    )
    assert rerun_action["arguments"]["summary"] == "Compare thing framings"
    assert rerun_action["arguments"]["link_alternatives"] is False
    assert rerun_action["arguments"]["shared_additions"] == [
        {"graph": "shapes", "content": shared_shape}
    ]
    assert [
        framing["label"] for framing in rerun_action["arguments"]["framings"]
    ] == [
        "Diagnostic incomplete thing",
        "Complete thing",
        "Complementary complete thing",
    ]
    assert "link_alternatives=False" in rerun_action["reason"]
    assert result["suggested_next_actions"][1]["tool_name"] == (
        "export_staged_revisions"
    )
    export_path = tmp_path / "invalid-first-review.md"
    export = export_staged_revisions_tool(
        db,
        revision_iris=revision_iris,
        path=str(export_path),
        title="Invalid first framing review",
    )
    assert export["bundle_summary"]["next_action_queue"] == {
        "repair_or_replace": [revision_iris[0]],
        "apply_after_review": [revision_iris[1], revision_iris[2]],
    }
    exported = export_path.read_text(encoding="utf-8")
    assert "## Review Queues" in exported
    assert "Diagnostic incomplete thing" in exported
    assert "Complementary complete thing" in exported


def test_stage_systematisation_tool_suppresses_anchor_warning_for_explicit_sibling_alternatives(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    explicit_target = db.stage_graph_revision(
        summary="Existing comparison anchor",
        rationale="A staged source revision that explicit alternatives can target.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .

                    ex:PreferredComparisonAnchor ex:note "Anchor revision." .
                """,
            }
        ],
    ).revision_iri
    shared_shape = """
    @prefix ex: <https://example.test/project#> .
    @prefix sh: <http://www.w3.org/ns/shacl#> .

    ex:ThingShape a sh:NodeShape ;
        sh:targetClass ex:Thing ;
        sh:property [
            sh:path ex:required ;
            sh:minCount 1
        ] .
    """
    incomplete_map = """
    @prefix ex: <https://example.test/project#> .

    ex:Thing1 a ex:Thing .
    """
    complete_map = """
    @prefix ex: <https://example.test/project#> .

    ex:Thing1 a ex:Thing ;
        ex:required ex:Value .
    """
    complementary_map = """
    @prefix ex: <https://example.test/project#> .

    ex:Thing1 a ex:Thing ;
        ex:required ex:OtherValue .
    """

    result = stage_systematisation_tool(
        db,
        summary="Compare explicitly routed thing framings",
        intent=(
            "Keep a diagnostic invalid framing beside valid framings that use "
            "their own comparison anchor."
        ),
        shared_additions=[{"graph": "shapes", "content": shared_shape}],
        framings=[
            {
                "label": "Diagnostic incomplete thing",
                "graph": "map",
                "content": incomplete_map,
            },
            {
                "label": "Complete thing",
                "graph": "map",
                "content": complete_map,
                "alternative_to": explicit_target,
            },
            {
                "label": "Complementary complete thing",
                "graph": "map",
                "content": complementary_map,
                "alternative_to": explicit_target,
            },
        ],
    )

    revision_iris = [
        revision["revision_iri"] for revision in result["staged_revisions"]
    ]
    assert result["next_action_queue"] == {
        "repair_or_replace": [revision_iris[0]],
        "apply_after_review": [revision_iris[1], revision_iris[2]],
    }
    assert len(result["structured_warnings"]) == 1
    shared_warning = result["structured_warnings"][0]
    assert shared_warning["warning_code"] == (
        "shared_semantic_context_applies_to_all_framings"
    )
    assert shared_warning["message"] == result["warnings"][-1]
    assert shared_warning["affected_revision_iris"] == revision_iris
    assert shared_warning["suggested_action"] == (
        "rerun_with_shared_semantic_context_moved_to_framings"
    )
    assert shared_warning["suggested_rerun_arguments"] == {
        "move_shared_patch_graphs_into_framing_patches": ["shapes"],
        "shared_patch_sources_to_move": [
            {
                "source_argument": "shared_additions",
                "source_index": 0,
                "operation": "addition",
                "graph": "shapes",
            }
        ],
    }
    assert shared_warning["fallback_revision_iris_with_shared_semantic_context"] == [
        revision_iris[1],
        revision_iris[2],
    ]
    assert shared_warning["shared_patch_summaries"] == [
        {
            "target_graph": "shapes",
            "operation": RC + "AdditionPatch",
            "operation_label": "addition patch",
            "patch_role": RC + "SharedContextPatch",
            "patch_role_label": "shared context patch",
            "sequence_index": 1,
            "triple_count": 5,
            "count_basis": "target_graph_plus_base_shapes",
            "format": "turtle",
        }
    ]
    assert not any(
        "First framing 'Diagnostic incomplete thing'" in warning
        for warning in result["warnings"]
    )
    assert not any(
        "linked as an alternative to the first" in warning
        or "linked as alternatives to the first" in warning
        for warning in result["warnings"]
    )
    assert result["staged_revisions"][0]["alternative_to"] is None
    assert result["staged_revisions"][1]["alternative_to"] == explicit_target
    assert result["staged_revisions"][2]["alternative_to"] == explicit_target


def test_stage_pattern_promotion_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    target = "https://example.test/project#messages__body_top"
    implication = "https://example.test/project#body_top_lossy_caveat"
    observation = db.record_observation(
        "body_top behaves like cleaned top-level message text.",
        observed_column=target,
        evidence_sources=["test://body-top-profile"],
    )
    pattern = db.record_pattern(
        summary="body_top is cleaned message text.",
        pattern_text="Source notes and checks support body_top as cleaned sender-new text.",
        rationale="The claim is durable enough to stage as a map caveat.",
        pattern_targets=[target],
        supporting_observations=[observation.observation_iri],
        evidence_sources=["test://body-top-pattern"],
        map_implications=[implication],
    )

    result = stage_pattern_promotion_tool(
        db,
        patterns=[pattern.pattern_iri],
        summary="Promote body_top caveat",
        framings=[
            {
                "label": "Map caveat",
                "graph": "map",
                "content": f"""
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:body_top_lossy_caveat a rc:KnownCaveat ;
                        rdfs:label "body_top lossy caveat" ;
                        rc:caveatDescription "body_top is cleaned text, not a byte-exact source body." .

                    <{target}> rc:hasKnownCaveat ex:body_top_lossy_caveat .
                """,
            }
        ],
    )

    assert result["result_kind"] == "systematisation_draft"
    assert result["summary"] == "Promote body_top caveat"
    assert result["intent"] == (
        "Stage one or more graph changes supported by selected patterns."
    )
    assert result["anchors"] == [pattern.pattern_iri, target, implication]
    revision_iri = result["staged_revisions"][0]["revision_iri"]
    assert result["next_action_queue"] == {"apply_after_review": [revision_iri]}
    assert result["suggested_next_actions"][0]["tool_name"] == (
        "export_staged_revisions"
    )
    assert result["suggested_next_actions"][0]["arguments"]["path"].startswith(
        "/tmp/systematisation-review-"
    )
    assert [
        action["arguments"]
        for action in result["suggested_next_actions"]
        if action["tool_name"] == "check_staged_revision_apply"
    ] == [{"iri": revision_iri}]
    assert result["framings"][0]["stance"] == (
        "https://richcanopy.org/ns/rc#CandidateRevision"
    )
    staged = describe_staged_revision_tool(
        db,
        revision_iri,
    )
    assert staged["supporting_patterns"][0]["iri"] == pattern.pattern_iri
    assert staged["supporting_observations"][0]["iri"] == observation.observation_iri
    assert {anchor["iri"] for anchor in staged["revision_anchors"]} == {
        pattern.pattern_iri,
        target,
        implication,
    }
    assert "Selected pattern support" in staged["rationale"]


def test_describe_dataset_tool_returns_json_like_context(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)

    result = describe_dataset_tool(
        db,
        iri="https://richcanopy.org/example/manifest/polymarket#MarketSnapshots",
    )

    assert result["label"] == "Gamma Market Snapshots"
    assert result["row_semantics"]["iri"] == "https://richcanopy.org/ns/rc#SnapshotRow"
    assert result["entity_key"]["iri"] == (
        "https://richcanopy.org/example/manifest/polymarket#mkt_id"
    )
    assert result["entity_key"]["column_name"] == "id"
    assert result["entity_key"]["owning_dataset_label"] == "Gamma Market Snapshots"
    assert result["snapshot_timestamp"]["iri"] == (
        "https://richcanopy.org/example/manifest/polymarket#mkt_fetched_at"
    )
    assert result["snapshot_timestamp"]["column_name"] == "_fetched_at"
    assert result["schema_stability"]["iri"] == (
        "https://richcanopy.org/ns/rc#InferredSchema"
    )
    assert "data/parquet/gamma/markets/dt={date}/hour={hour}.parquet" in result[
        "path_templates"
    ]
    assert {column["column_name"] for column in result["columns"]} >= {
        "id",
        "bestBid",
        "bestAsk",
    }
    assert result["physical_layouts"][0]["compression_codec"]["label"] == "zstd"
    assert result["storage_accesses"][0]["storage_protocol"]["label"] == "local filesystem"
    assert result["storage_accesses"][0]["storage_root"] == "data/parquet"
    assert result["storage_accesses"][0]["access_mode"]["label"] == "read-only"
    assert any(
        caveat["description"]
        and "Parquet schemas are inferred" in caveat["description"]
        for caveat in result["caveats"]
    )
    assert any(
        caveat["impact"]
        and "physical types may vary" in caveat["impact"]
        and caveat["severity"]["iri"] == "https://richcanopy.org/ns/rc#Moderate"
        for caveat in result["caveats"]
    )
    assert {transformation["transformation_type"] for transformation in result[
        "transformations"
    ]} == {"collection", "compaction"}
    assert any(
        relationship["relationship_kind"]
        == "https://richcanopy.org/ns/rc#SharedIdentifier"
        and relationship["relationship_kind_label"] == "SharedIdentifier"
        and relationship["label"]
        == "Condition ID identifies the same market across datasets"
        and any(
            column["column_name"] == "conditionId"
            and column["owning_dataset_label"] == "Gamma Market Snapshots"
            for column in relationship["identifying_columns"]
        )
        for relationship in result["relationships"]
    )
    assert any(
        related["relationship"] == "shares_identifier_with"
        and related["relationship_label"]
        == "Condition ID identifies the same market across datasets"
        and related["relationship_kind"]
        == "https://richcanopy.org/ns/rc#SharedIdentifier"
        and related["relationship_kind_label"] == "SharedIdentifier"
        and related["label"] == "Trade Events"
        for related in result["related_datasets"]
    )
    trade_group = next(
        group
        for group in result["related_dataset_groups"]
        if group["label"] == "Trade Events"
    )
    condition_id_reason = next(
        reason
        for reason in trade_group["reasons"]
        if {
            (column["owning_dataset_label"], column["column_name"])
            for column in reason["columns"]
        }
        == {
            ("Gamma Market Snapshots", "conditionId"),
            ("Trade Events", "conditionId"),
        }
    )
    assert condition_id_reason["relationship"] == "target_of"
    assert condition_id_reason["relationship_label"] == "Trades to Markets via conditionId"
    assert condition_id_reason["relationship_kind_label"] == "ForeignKey"
    assert condition_id_reason["declared"] is None
    assert condition_id_reason["referential_integrity"]["iri"] == (
        "https://richcanopy.org/ns/rc#PartialIntegrity"
    )
    assert {
        tag["relationship_kind_label"]
        for tag in condition_id_reason["relationship_tags"]
    } == {"ForeignKey", "SharedIdentifier"}
    assert [
        column["column_name"]
        for column in condition_id_reason["current_dataset_columns"]
    ] == ["conditionId"]
    assert [
        column["column_name"]
        for column in condition_id_reason["related_dataset_columns"]
    ] == ["conditionId"]


def test_describe_query_context_tool_returns_planning_projection(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)

    result = describe_query_context_tool(
        db,
        iri="https://richcanopy.org/example/manifest/ais#DailyBroadcasts",
    )

    assert result["dataset"]["label"] == "AIS Daily Broadcast Positions"
    assert result["readiness"] == "needs_review"
    assert "readiness_note" in result
    assert "analysis_warnings" in result
    assert "layout_verification_status" in result
    assert "layout_verification_note" in result
    assert "broadcasts/{year}/ais-{date}.parquet" in result["path_templates"]
    assert result["query_target_candidates"][0]["candidate_path"] == (
        "s3://ais-noaa/broadcasts/{year}/ais-{date}.parquet"
    )
    assert result["query_target_decision"]["status"] == "candidate_needs_review"
    assert result["query_target_decision"]["candidate_index"] == 0
    assert result["query_target_decision"]["candidate_path"] == (
        "s3://ais-noaa/broadcasts/{year}/ais-{date}.parquet"
    )
    assert result["query_target_decision"]["candidate_path_status"] == (
        "orientation_only"
    )
    assert result["query_target_decision"]["direct_review_required"] is True
    assert result["query_target_decision"]["reason_codes"] == [
        "layout_needs_verification"
    ]
    assert result["query_target_candidates"][0]["composition"] == "storage_root_joined"
    assert result["query_target_candidates"][0]["candidate_path_status"] == (
        "orientation_only"
    )
    assert result["query_target_candidates"][0]["template_source"] == "partition_scheme"
    assert result["query_target_candidates"][0]["requires_endpoint_profile"] is True
    assert result["query_target_candidates"][0]["review_required"] is True
    assert result["query_target_candidates"][0]["direct_review_required"] is True
    assert {
        reason["code"]
        for reason in result["query_target_candidates"][0]["direct_review_reasons"]
    } == {
        "layout_needs_verification",
        "verification_status_not_recorded",
    }
    assert result["storage_accesses"][0]["endpoint_profile"] == "local-minio"
    assert any(
        issue["code"] == "layout_needs_verification"
        and issue["domain"] == "query_planning"
        and issue["severity"] == "warning"
        for issue in result["issues"]
    )
    assert any(
        issue["code"] == "verification_status_not_recorded"
        and issue["domain"] == "query_planning"
        and issue["severity"] == "info"
        for issue in result["issues"]
    )
    assert "non-secret planning metadata" in result["planning_notes"][0]


def test_query_tools_mark_non_tabular_asset_not_applicable(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    asset = "https://example.test/project#SalesReadme"
    storage = db.record_map_storage_access(
        "https://example.test/project#sales_readme_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="object",
        storage_root=str(tmp_path / "sales-readme.md"),
    )
    db.record_map_dataset(
        asset,
        label="Sales README",
        is_table=False,
        storage_accesses=[storage.iri],
    )

    context = describe_query_context_tool(db, iri=asset)

    assert context["readiness"] == "not_applicable_non_tabular_asset"
    assert context["query_target_candidates"] == []
    assert context["issues"][0]["code"] == "non_tabular_asset_query_not_applicable"
    assert context["suggested_next_actions"][0]["tool_name"] == (
        "describe_context_slice"
    )

    plan = draft_query_plan_tool(db, iri=asset)

    assert plan["handoff_kind"] == "not_applicable_non_tabular_asset"
    assert plan["handoff_summary"]["handoff_kind"] == (
        "not_applicable_non_tabular_asset"
    )
    assert plan["handoff_summary"]["selected_candidate_index"] is None
    assert plan["handoff_summary"]["ready_for_execution_attempt"] is False
    assert plan["selected_candidate"] is None
    assert plan["scan"]["function"] is None
    assert plan["review_gate"]["status"] == "not_applicable_non_tabular_asset"


def test_draft_query_plan_tool_returns_review_draft(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)

    result = draft_query_plan_tool(
        db,
        iri="https://richcanopy.org/example/manifest/ais#DailyBroadcasts",
    )

    assert result["helper"] == "draft_query_plan"
    assert result["mode"] == "non_executed_review_draft"
    assert result["handoff_kind"] == "metadata_review_required"
    assert result["handoff_summary"]["handoff_kind"] == "metadata_review_required"
    assert result["engine"] == {
        "name": "duckdb",
        "source": "caller_requested_target_engine",
    }
    assert result["source_context"]["readiness"] == "needs_review"
    assert result["source_context"]["selected_candidate_index"] == 0
    assert result["source_context"]["candidate_count"] == 1
    assert result["source_context"]["ready_candidate_indexes"] == []
    assert result["source_context"]["unselected_ready_candidate_indexes"] == []
    assert result["selected_candidate"]["template_source"] == "partition_scheme"
    assert result["scan"]["function"] == "read_parquet"
    assert result["scan"]["uri_template"] == (
        "s3://ais-noaa/broadcasts/{year}/ais-{date}.parquet"
    )
    assert result["handoff_summary"]["scan_function"] == "read_parquet"
    assert result["handoff_summary"]["uri_template"] == (
        "s3://ais-noaa/broadcasts/{year}/ais-{date}.parquet"
    )
    assert result["handoff_summary"]["selected_candidate_index"] == 0
    assert result["scan"]["candidate_path_status"] == "orientation_only"
    assert result["scan"]["dataset_verification_status"] is None
    assert result["scan"]["dataset_verification_note"] is None
    assert result["scan"]["template_source"] == "partition_scheme"
    assert result["scan"]["template_source_resource"]["iri"] == (
        "https://richcanopy.org/example/manifest/ais#daily_date_partition"
    )
    assert result["scan"]["template_source_verification_status"]["iri"] == (
        "https://richcanopy.org/ns/rc#GeneratedFromManifestLayout"
    )
    assert "partition_scheme daily_date_partition" in (
        result["scan"]["template_lineage"]
    )
    assert result["required_bindings"] == ["year", "date"]
    assert [binding["name"] for binding in result["binding_requirements"]] == [
        "year",
        "date",
    ]
    assert result["binding_requirements"][0]["source"] == (
        "path_template_placeholder"
    )
    assert result["binding_requirements"][0]["source_text"] == (
        "s3://ais-noaa/broadcasts/{year}/ais-{date}.parquet"
    )
    assert result["binding_requirements"][0]["required"] is True
    assert result["binding_requirements"][0]["derivation_status"] == "not_inferred"
    assert result["binding_requirements"][0]["binding_kind"] == (
        "partition_template_placeholder"
    )
    assert result["binding_requirements"][0]["partition_scheme"]["iri"] == (
        "https://richcanopy.org/example/manifest/ais#daily_date_partition"
    )
    assert result["binding_requirements"][0]["partition_column"] is None
    assert result["binding_requirements"][0]["partition_granularity"]["iri"] == (
        "https://richcanopy.org/ns/rc#Daily"
    )
    assert result["binding_requirements"][0]["candidate_column_matches"] == []
    assert result["binding_requirements"][0]["candidate_column_match_status"] == "none"
    assert result["binding_requirements"][1]["binding_kind"] == (
        "partition_template_placeholder"
    )
    assert result["binding_requirements"][1]["partition_column"]["iri"] == (
        "https://richcanopy.org/example/manifest/ais#bc_date"
    )
    assert result["binding_requirements"][1]["partition_column"]["column_name"] == (
        "date"
    )
    assert result["binding_requirements"][1]["partition_granularity"]["iri"] == (
        "https://richcanopy.org/ns/rc#Daily"
    )
    assert result["binding_requirements"][1]["candidate_column_matches"] == []
    assert (
        result["binding_requirements"][1]["candidate_column_match_status"]
        == "not_applicable"
    )
    assert result["storage_environment"]["endpoint_profile"] == "local-minio"
    assert result["storage_environment"]["credential_reference"] == (
        "profile:ais-readonly"
    )
    assert result["storage_environment"]["duckdb_settings_from_context"] == [
        "s3_url_style=path",
        "s3_region=local",
    ]
    assert result["review_gate"]["executable_without_review"] is False
    assert result["review_gate"]["runtime_resolution_required"] is True
    assert result["review_gate"]["binding_values_required"] is True
    assert result["review_gate"]["ready_for_execution_attempt"] is False
    assert result["handoff_summary"]["ready_for_execution_attempt"] is False
    assert result["handoff_summary"]["runtime_resolution_required"] is True
    assert result["handoff_summary"]["binding_values_required"] is True
    assert result["handoff_summary"]["required_bindings"] == ["year", "date"]
    assert result["review_gate"]["blocking_reason_codes"] == [
        "layout_needs_verification"
    ]
    assert result["review_gate"]["all_issue_codes"] == [
        "layout_needs_verification",
        "verification_status_not_recorded",
    ]
    assert result["handoff_summary"]["all_issue_codes"] == [
        "layout_needs_verification",
        "verification_status_not_recorded",
    ]
    assert result["review_gate"]["reason_codes"] == ["layout_needs_verification"]
    assert any(
        issue["code"] == "layout_needs_verification" for issue in result["issues"]
    )
    assert result["caveats"]


def test_describe_query_context_tool_routes_profile_evidence_before_query_draft(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)
    dataset = "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"
    shared_evidence = "https://example.test/project#AISProfileRunEvidence"

    record_profile_bundle_tool(
        db,
        dataset_iri=dataset,
        dataset_summary=(
            "AIS daily broadcasts were profiled before drafting a query plan."
        ),
        evidence_summary="Synthetic profile run for query-planning route coverage.",
        evidence_sources=["test://ais-query-profile-routing"],
        shared_evidence_iri=shared_evidence,
        sample_size=42,
        sample_scope="Synthetic bounded fixture profile.",
        sample_method="Focused query-planning routing trial.",
        row_count=42,
        update_map_snapshot=True,
        map_label="AIS Daily Broadcast Positions",
        is_table=True,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": (
                    "https://richcanopy.org/example/manifest/ais#bc_date"
                ),
                "column_name": "date",
                "summary": "AIS broadcast date was profiled in the same run.",
                "row_count": 42,
            }
        ],
    )

    context = describe_query_context_tool(db, iri=dataset)

    assert context["row_count_snapshot"] == 42
    assert context["query_target_decision"]["candidate_index"] == 0
    assert len(context["query_target_candidates"]) == 1
    assert context["profile_summary"]["profile_run_candidates"][0][
        "evidence_iri"
    ] == shared_evidence
    assert context["profile_summary"]["profile_run_candidates"][0][
        "returned_profile_count"
    ] == 2
    assert context["profile_summary"]["profile_run_candidates"][0][
        "dataset_profile_row_count_bases"
    ] == {"42": ["full_scan"]}
    assert context["profile_summary"]["profile_run_candidates"][0][
        "row_count_snapshot_basis"
    ] == "full_scan"
    assert [
        action["tool_name"] for action in context["suggested_next_actions"]
    ] == [
        "describe_profile_run",
        "draft_query_plan",
    ]

    profile_action = context["suggested_next_actions"][0]
    assert profile_action["action_label"] == "Inspect profile run evidence"
    assert profile_action["arguments"] == {
        "dataset_iri": dataset,
        "evidence_iri": shared_evidence,
    }
    profile_run = describe_profile_run_tool(db, **profile_action["arguments"])
    assert profile_run["returned_profile_count"] == 2
    assert profile_run["returned_dataset_profile_count"] == 1
    assert profile_run["returned_mapped_column_profile_count"] == 1
    assert profile_run["row_count_snapshot"] == 42
    assert profile_run["dataset_profile_row_counts"] == [42]
    assert profile_run["dataset_profile_row_count_bases"] == {"42": ["full_scan"]}
    assert profile_run["row_count_snapshot_matches"] is True
    assert profile_run["row_count_snapshot_basis"] == "full_scan"

    draft_action = context["suggested_next_actions"][1]
    assert draft_action["action_label"] == "Draft review-gated query plan"
    assert draft_action["arguments"] == {"iri": dataset, "candidate_index": 0}
    draft = draft_query_plan_tool(db, **draft_action["arguments"])
    assert draft["handoff_kind"] == "metadata_review_required"
    assert draft["source_context"]["selection_mode"] == "candidate_index"
    assert draft["source_context"]["selected_candidate_index"] == 0
    assert draft["scan"]["uri_template"] == (
        "s3://ais-noaa/broadcasts/{year}/ais-{date}.parquet"
    )


def test_draft_query_plan_tool_accepts_explicit_storage_selection(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    local_storage = db.record_map_storage_access(
        "https://example.test/project#orders_z_local_storage",
        label="Orders local access",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/warehouse",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    stale_storage = db.record_map_storage_access(
        "https://example.test/project#orders_a_stale_s3_storage",
        label="Orders stale S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        bucket_name="old-orders",
        key_prefix="orders",
        credential_reference="profile:old-orders",
        layout_verification_status="rc:ContradictedLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#orders_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        path_templates=["orders/dt={date}.parquet"],
        storage_accesses=[local_storage.iri, stale_storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    date_column = "https://example.test/project#orders__event_date"
    db.record_map_column(
        date_column,
        table_iri=dataset,
        column_name="event_date",
        physical_type="rc:Date",
    )

    context = describe_query_context_tool(db, iri=dataset)
    assert context["query_target_decision"]["status"] == "context_blocked"
    assert (
        context["query_target_decision"]["selected_candidate_direct_clean"]
        is True
    )
    assert context["ready_candidate_indexes"] == []
    assert context["unselected_ready_candidate_indexes"] == []
    assert context["direct_clean_candidate_indexes"] == [
        context["query_target_decision"]["candidate_index"]
    ]
    assert context["unselected_direct_clean_candidate_indexes"] == []
    query_action = context["suggested_next_actions"][0]
    assert query_action["tool_name"] == "draft_query_plan"
    assert query_action["action_label"] == (
        "Draft direct-clean candidate with context allowance"
    )
    assert query_action["arguments"] == {
        "iri": dataset,
        "candidate_index": context["query_target_decision"]["candidate_index"],
        "allow_context_blocked_candidate": True,
    }
    assert context["suggested_next_calls"] == [query_action["call"]]

    result = draft_query_plan_tool(
        db,
        iri=dataset,
        storage_access_iri=local_storage.iri,
        allow_context_blocked_candidate=True,
    )

    assert result["source_context"]["query_target_decision"]["status"] == (
        "context_blocked"
    )
    assert result["source_context"]["selection_mode"] == "storage_access_iri"
    assert result["source_context"]["requested_storage_access_iri"] == (
        local_storage.iri
    )
    assert result["source_context"]["selection_status"] == "matched"
    assert result["source_context"]["allow_context_blocked_candidate"] is True
    assert "Selected candidate" in result["source_context"]["selected_candidate_note"]
    assert "direct-clean binding values required" in (
        result["source_context"]["selected_candidate_note"]
    )
    assert "contradicted_layout" in (
        result["source_context"]["selected_candidate_note"]
    )
    assert result["source_context"]["ready_candidate_indexes"] == []
    assert result["source_context"]["unselected_ready_candidate_indexes"] == []
    assert result["source_context"]["direct_clean_candidate_indexes"] == [
        result["source_context"]["selected_candidate_index"]
    ]
    assert result["source_context"]["unselected_direct_clean_candidate_indexes"] == []
    assert result["selected_candidate"]["storage_access"]["iri"] == local_storage.iri
    assert result["selected_candidate"]["candidate_path_status"] == "ready"
    assert result["scan"]["candidate_path_status"] == "ready"
    assert result["scan"]["execution_attempt_ready"] is False
    assert result["scan"]["primary_execution_attempt_blocking_reason_code"] == (
        "binding_values_required"
    )
    assert result["scan"]["execution_attempt_blocking_reason_codes"] == [
        "binding_values_required"
    ]
    assert result["review_gate"]["status"] == "ready"
    assert result["review_gate"]["context_blocked_candidate_used"] is True
    assert result["review_gate"]["context_blocking_reason_codes"] == [
        "query_context_has_other_blockers"
    ]
    assert result["review_gate"]["blocking_reason_codes"] == []
    assert result["review_gate"]["primary_execution_attempt_blocking_reason_code"] == (
        "binding_values_required"
    )
    assert result["review_gate"]["execution_attempt_blocking_reason_codes"] == [
        "binding_values_required"
    ]
    assert result["handoff_kind"] == "binding_values_required"
    date_binding = result["binding_requirements"][0]
    assert date_binding["name"] == "date"
    assert date_binding["candidate_column_matches"][0]["column"]["iri"] == (
        date_column
    )
    assert date_binding["candidate_column_matches"][0]["column"]["column_name"] == (
        "event_date"
    )
    assert date_binding["candidate_column_matches"][0]["match_kind"] == (
        "suffix_name"
    )
    assert date_binding["candidate_column_matches"][0]["confidence"] == "medium"
    assert date_binding["candidate_column_match_status"] == "single"


def test_describe_query_context_tool_suggests_stale_partition_link_repair(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#DailyIndex"
    date_column = record_map_column_tool(
        db,
        iri="https://example.test/project#daily_index__date",
        table_iri=dataset,
        column_name="date",
    )
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#daily_index_object_store_access",
        label="Daily index object-store access",
        storage_protocol="rc:S3CompatibleStorage",
        storage_root="s3://ais-noaa/",
        endpoint_profile="local-minio",
        credential_reference="profile:ais-readonly",
        path_templates=["index/*/*.parquet"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    stale_partition = record_map_partition_scheme_tool(
        db,
        iri="https://example.test/project#broadcast_date_partition",
        path_template="broadcasts/{year}/ais-{date}.parquet",
        partition_columns=[date_column["iri"]],
        granularity="rc:Daily",
        layout_verification_status="rc:CandidateLayout",
        datasets=[dataset],
    )
    layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#daily_index_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Daily index",
        is_table=True,
        columns=[date_column["iri"]],
        storage_accesses=[storage["iri"]],
        physical_layouts=[layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    result = describe_query_context_tool(db, iri=dataset)

    assert result["query_target_decision"]["status"] == "context_blocked"
    assert result["suggested_repair_action_group_count"] == 1
    repair_group = result["suggested_repair_action_groups"][0]
    assert repair_group["issue_code"] == "layout_needs_verification"
    assert repair_group["issue_resource"]["iri"] == stale_partition["iri"]
    assert repair_group["repair_action_type"] == (
        "remove_stale_partition_scheme_link"
    )
    assert repair_group["choice_mode"] == "review_all_applicable"
    assert repair_group["action_status_counts"] == {"pending_review": 1}
    assert repair_group["pending_required_extra_arguments"] == ["rationale"]
    action = repair_group["actions"][0]
    assert action["tool_name"] == "stage_map_assertion_change"
    assert action["arguments"] == {
        "subject": dataset,
        "predicate": "rc:partitionedBy",
        "object": stale_partition["iri"],
        "object_kind": "iri",
        "change_kind": "remove",
        "graph": "map",
        "validation_scope": "all",
    }


def test_describe_query_context_tool_suggests_stale_physical_layout_link_repair(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#events_local_storage",
        label="Events local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/warehouse",
        path_templates=["events/current/*.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    verified_layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    stale_layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#events_old_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:CandidateLayout",
    )
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Events",
        is_table=True,
        storage_accesses=[storage["iri"]],
        physical_layouts=[verified_layout["iri"], stale_layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    result = describe_query_context_tool(db, iri=dataset)

    assert result["query_target_decision"]["status"] == "context_blocked"
    assert result["query_target_decision"]["selected_candidate_direct_clean"] is True
    assert result["suggested_repair_action_group_count"] == 1
    repair_group = result["suggested_repair_action_groups"][0]
    assert repair_group["issue_code"] == "layout_needs_verification"
    assert repair_group["issue_resource"]["iri"] == stale_layout["iri"]
    assert repair_group["repair_action_type"] == "remove_stale_physical_layout_link"
    assert repair_group["choice_mode"] == "review_all_applicable"
    assert repair_group["action_status_counts"] == {"pending_review": 1}
    assert repair_group["pending_required_extra_arguments"] == ["rationale"]
    action = repair_group["actions"][0]
    assert action["tool_name"] == "stage_map_assertion_change"
    assert action["arguments"] == {
        "subject": dataset,
        "predicate": "rc:hasPhysicalLayout",
        "object": stale_layout["iri"],
        "object_kind": "iri",
        "change_kind": "remove",
        "graph": "map",
        "validation_scope": "all",
    }


def test_describe_query_context_tool_lifts_missing_physical_layout_repair(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WarehouseOrders"
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#warehouse_orders_storage",
        label="Warehouse orders database",
        storage_protocol="rc:DatabaseStorage",
        storage_root="warehouse-prod",
        path_templates=["public.orders"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Warehouse orders",
        is_table=True,
        storage_accesses=[storage["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    result = describe_query_context_tool(db, iri=dataset)

    repair_group = next(
        group
        for group in result["suggested_repair_action_groups"]
        if group["issue_code"] == "missing_physical_layout"
    )
    assert repair_group["repair_action_type"] == "record_physical_layout"
    assert repair_group["repair_context"]["database_storage_present"] is True
    assert repair_group["repair_context"]["storage_protocol_iris"] == [
        RC + "DatabaseStorage"
    ]
    assert "rc:PostgreSQLTable" in repair_group["repair_context"][
        "file_format_guidance"
    ]["rc:DatabaseStorage"]
    assert len(repair_group["pending_action_options"]) == 1
    layout_option = repair_group["pending_action_options"][0]
    _assert_repair_action_option(
        layout_option,
        action_index=0,
        action_type="record_reviewed_physical_layout",
        tool_name="record_map_physical_layout",
        mcp_tool_name="doxabase.record_map_physical_layout",
        action_label="Record physical layout and link dataset",
        required_extra_arguments=["iri", "file_format"],
        placeholder_fields=[
            "file_format",
            "layout_verification_status",
            "layout_verification_note",
        ],
        reviewed_value_fields=[
            "file_format",
            "layout_verification_status",
            "layout_verification_note",
        ],
    )
    assert "file format or database table layout" in layout_option["reason"]
    assert "rc:PostgreSQLTable" in layout_option["condition"]
    assert "record_map_physical_layout writes current-best map facts directly" in (
        layout_option["review_rationale_guidance"]
    )
    action = repair_group["actions"][0]
    assert action["tool_name"] == "record_map_physical_layout"
    assert action["arguments_template"]["datasets"] == [dataset]
    assert action["arguments_template"]["file_format"] == (
        "<reviewed rc:FileFormat IRI>"
    )


def test_draft_query_plan_tool_accepts_explicit_physical_layout_selection(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#events_local_storage",
        label="Events local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="directory",
        storage_root=str(tmp_path / "warehouse"),
        path_templates=["events/current/*.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    csv_layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#events_csv_layout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    parquet_layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Events",
        is_table=True,
        storage_accesses=[storage["iri"]],
        physical_layouts=[csv_layout["iri"], parquet_layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = describe_query_context_tool(db, iri=dataset)
    automatic = draft_query_plan_tool(db, iri=dataset)
    selected = draft_query_plan_tool(
        db,
        iri=dataset,
        physical_layout_iri=parquet_layout["iri"],
    )

    assert context["readiness"] == "needs_review"
    assert "ambiguous_physical_layout" in {
        issue["code"] for issue in context["issues"]
    }
    selection_actions = [
        action
        for action in context["suggested_next_actions"]
        if action["action_label"] == "Select physical layout for draft"
    ]
    assert [action["arguments"] for action in selection_actions] == [
        {
            "iri": dataset,
            "candidate_index": 0,
            "physical_layout_iri": csv_layout["iri"],
        },
        {
            "iri": dataset,
            "candidate_index": 0,
            "physical_layout_iri": parquet_layout["iri"],
        },
    ]
    assert selection_actions[1]["call"].startswith("draft_query_plan(")
    assert automatic["scan"]["function"] is None
    assert automatic["review_gate"]["blocking_reason_codes"] == [
        "ambiguous_physical_layout"
    ]
    assert selected["source_context"]["requested_physical_layout_iri"] == (
        parquet_layout["iri"]
    )
    assert selected["scan"]["physical_layout"]["iri"] == parquet_layout["iri"]
    assert selected["scan"]["file_format"] == "Parquet"
    assert selected["scan"]["function"] == "read_parquet"
    assert selected["scan"]["physical_layout_selection_note"] == (
        "Caller selected this physical layout for the draft query plan."
    )
    assert "ambiguous_physical_layout" not in selected["review_gate"][
        "blocking_reason_codes"
    ]
    assert selected["review_gate"]["ready_for_execution_attempt"] is True
    assert selected["handoff_kind"] == "execution_attempt_ready"


def test_draft_query_plan_tool_returns_database_relation_handoff(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_database_storage",
        label="Orders database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        path_templates=["mart.orders"],
        endpoint_profile="warehouse-prod",
        credential_reference="profile:warehouse-readonly",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#orders_table_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    result = draft_query_plan_tool(db, iri=dataset)

    assert result["selected_candidate"]["candidate_path"] == "mart.orders"
    assert result["selected_candidate"]["relation_identifier"] == "mart.orders"
    assert result["selected_candidate"]["connection_reference"] == "warehouse-prod"
    assert result["selected_candidate"]["composition"] == (
        "database_connection_and_relation"
    )
    assert result["scan"]["function"] is None
    assert result["scan"]["uri_template"] is None
    assert result["scan"]["relation_identifier"] == "mart.orders"
    assert result["scan"]["connection_reference"] == "warehouse-prod"
    assert result["handoff_summary"]["relation_identifier"] == "mart.orders"
    assert result["handoff_summary"]["connection_reference"] == "warehouse-prod"
    assert result["scan"]["composition"] == "database_connection_and_relation"
    assert result["scan"]["execution_attempt_ready"] is False
    assert result["scan"]["execution_attempt_blocking_reason_codes"] == [
        "scan_function_not_inferred",
        "runtime_resolution_required",
    ]
    assert result["review_gate"]["blocking_reason_codes"] == [
        "scan_function_not_inferred"
    ]
    assert result["review_gate"]["binding_values_required"] is False
    assert result["review_gate"]["ready_for_execution_attempt"] is False
    assert result["handoff_kind"] == "database_relation_handoff"


def test_draft_query_plan_tool_handles_explicit_context_allowed_database_relation(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WarehouseOrders"
    relation_storage = db.record_map_storage_access(
        "https://example.test/project#orders_database_storage",
        label="Orders database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        path_templates=["mart.orders", "mart.orders_archive"],
        endpoint_profile="warehouse-prod",
        credential_reference="profile:warehouse-readonly",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    blocked_storage = db.record_map_storage_access(
        "https://example.test/project#orders_broken_database_storage",
        label="Orders broken database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-stale",
        endpoint_profile="warehouse-stale",
        credential_reference="profile:warehouse-stale-readonly",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#orders_table_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Warehouse orders",
        is_table=True,
        storage_accesses=[relation_storage.iri, blocked_storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = describe_query_context_tool(db, iri=dataset)
    relation_candidate_index = next(
        index
        for index, candidate in enumerate(context["query_target_candidates"])
        if candidate["relation_identifier"] == "mart.orders"
    )
    archive_candidate_index = next(
        index
        for index, candidate in enumerate(context["query_target_candidates"])
        if candidate["relation_identifier"] == "mart.orders_archive"
    )

    assert context["query_target_decision"]["status"] == "context_blocked"
    assert context["ready_candidate_indexes"] == []
    assert relation_candidate_index in context["direct_clean_candidate_indexes"]
    assert archive_candidate_index in context["unselected_direct_clean_candidate_indexes"]
    assert [
        action["arguments"]
        for action in context["suggested_next_actions"]
        if action["tool_name"] == "draft_query_plan"
    ] == [
        {
            "iri": dataset,
            "candidate_index": relation_candidate_index,
            "allow_context_blocked_candidate": True,
        },
        {
            "iri": dataset,
            "candidate_index": archive_candidate_index,
            "allow_context_blocked_candidate": True,
        },
    ]
    assert [
        action["action_label"]
        for action in context["suggested_next_actions"]
        if action["tool_name"] == "draft_query_plan"
    ] == [
        "Draft direct-clean candidate with context allowance",
        "Draft peer direct-clean candidate with context allowance",
    ]

    result = draft_query_plan_tool(
        db,
        iri=dataset,
        candidate_index=relation_candidate_index,
        allow_context_blocked_candidate=True,
    )

    assert result["source_context"]["selection_mode"] == "candidate_index"
    assert result["source_context"]["selected_candidate_index"] == (
        relation_candidate_index
    )
    assert result["source_context"]["requested_candidate_index"] == (
        relation_candidate_index
    )
    assert result["source_context"]["requested_storage_access_iri"] is None
    assert result["source_context"]["allow_context_blocked_candidate"] is True
    assert result["selected_candidate"]["storage_access"]["iri"] == (
        relation_storage.iri
    )
    assert result["selected_candidate"]["relation_identifier"] == "mart.orders"
    assert result["selected_candidate"]["candidate_path_status"] == "ready"
    assert result["selected_candidate"]["review_required"] is False
    assert result["selected_candidate"]["direct_review_required"] is False
    assert result["scan"]["uri_template"] is None
    assert result["scan"]["relation_identifier"] == "mart.orders"
    assert result["scan"]["connection_reference"] == "warehouse-prod"
    assert result["scan"]["composition"] == "database_connection_and_relation"
    assert result["review_gate"]["status"] == "ready"
    assert result["review_gate"]["context_blocked_candidate_used"] is True
    assert result["review_gate"]["context_blocking_reason_codes"] == [
        "query_context_has_other_blockers"
    ]
    assert result["review_gate"]["blocking_reason_codes"] == [
        "scan_function_not_inferred"
    ]
    assert result["review_gate"]["all_issue_codes"] == [
        "database_relation_template_missing"
    ]
    assert result["handoff_kind"] == "database_relation_handoff"

    with pytest.raises(DoxaBaseError) as exc_info:
        draft_query_plan_tool(
            db,
            iri=dataset,
            storage_access_iri=relation_storage.iri,
        )

    error_message = str(exc_info.value)
    assert "storage_access_iri matched multiple query target candidates" in (
        error_message
    )
    assert "Pass candidate_index for an exact selection" in error_message
    assert "relation_identifier='mart.orders'" in error_message
    assert "relation_identifier='mart.orders_archive'" in error_message


def test_draft_query_plan_tool_serializes_database_template_source_mismatch(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    dataset_template = "orders/current/*.parquet"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_database_storage",
        label="Orders database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        endpoint_profile="warehouse-prod",
        credential_reference="profile:warehouse-readonly",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#orders_table_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        path_templates=[dataset_template],
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = describe_query_context_tool(db, iri=dataset)
    plan = draft_query_plan_tool(db, iri=dataset)

    issue = next(
        issue
        for issue in context["issues"]
        if issue["code"] == "database_relation_template_source_mismatch"
    )
    assert issue["details"] == {
        "template": dataset_template,
        "template_source": "dataset",
        "template_source_resource_iri": dataset,
        "storage_access_iri": storage.iri,
        "storage_protocol_iri": RC + "DatabaseStorage",
        "allowed_relation_template_sources": ["storage_access"],
        "repair_hint": {
            "action_type": "move_database_relation_template_to_storage_access",
            "requires_review": True,
            "source_subject_iri": dataset,
            "misplaced_template_subject_iri": dataset,
            "misplaced_template_source": "dataset",
            "misplaced_template": dataset_template,
            "source": {
                "subject_iri": dataset,
                "template_source": "dataset",
                "predicate": "rc:pathTemplate",
                "template": dataset_template,
            },
            "target": {
                "storage_access_iri": storage.iri,
                "predicate": "rc:pathTemplate",
                "required_template_source": "storage_access",
            },
            "candidate_relation_identifier": {
                "value": dataset_template,
                "requires_review": True,
                "already_on_storage_access": False,
                "review_note": (
                    "Dataset and partition path templates are not database "
                    "relation identifiers by default; replace this value with "
                    "the reviewed schema/table/relation before staging the add."
                ),
            },
            "actions": [
                {
                    "action_type": "add_reviewed_relation_template",
                    "tool_name": "stage_map_assertion_change",
                    "mcp_tool_name": "doxabase.stage_map_assertion_change",
                    "source_subject_iri": dataset,
                    "misplaced_template_subject_iri": dataset,
                    "misplaced_template_source": "dataset",
                    "misplaced_template": dataset_template,
                    "required_extra_arguments": ["object", "rationale"],
                    "rationale_template": (
                        "Reviewed database relation identifier for "
                        f"{storage.iri}."
                    ),
                    "arguments_template": {
                        "subject": storage.iri,
                        "predicate": "rc:pathTemplate",
                        "object": "<reviewed_database_relation_identifier>",
                        "object_kind": "literal",
                        "change_kind": "add",
                        "graph": "map",
                    },
                    "placeholder_fields": ["object"],
                    "reviewed_value_fields": ["object"],
                    "condition": (
                        "Replace the placeholder object with the reviewed "
                        "database relation identifier before staging."
                    ),
                },
                {
                    "action_type": "remove_misplaced_source_template",
                    "tool_name": "stage_map_assertion_change",
                    "mcp_tool_name": "doxabase.stage_map_assertion_change",
                    "source_subject_iri": dataset,
                    "misplaced_template_subject_iri": dataset,
                    "misplaced_template_source": "dataset",
                    "misplaced_template": dataset_template,
                    "required_extra_arguments": ["rationale"],
                    "rationale_template": (
                        "Reviewed source template as misplaced database "
                        "relation metadata."
                    ),
                    "arguments": {
                        "subject": dataset,
                        "predicate": "rc:pathTemplate",
                        "object": dataset_template,
                        "object_kind": "literal",
                        "change_kind": "remove",
                        "graph": "map",
                    },
                    "condition": (
                        "Only after review confirms the source template was "
                        "misplaced relation metadata rather than a real "
                        "file/object path."
                    ),
                },
            ],
        },
    }
    target = context["query_target_candidates"][0]
    assert target["candidate_path"] is None
    assert target["relation_identifier"] is None
    assert target["connection_reference"] == "warehouse-prod"
    assert target["candidate_path_status"] == "unresolved"
    assert target["direct_review_reasons"][0]["code"] == (
        "database_relation_template_source_mismatch"
    )
    assert [action["tool_name"] for action in context["suggested_next_actions"]] == [
        "draft_query_plan",
    ]
    assert plan["selected_candidate"]["template_source"] == "dataset"
    assert plan["scan"]["uri_template"] is None
    assert plan["scan"]["relation_identifier"] is None
    assert plan["scan"]["connection_reference"] == "warehouse-prod"
    assert plan["review_gate"]["blocking_reason_codes"] == [
        "database_relation_template_source_mismatch"
    ]
    assert plan["handoff_kind"] == "metadata_review_required"


def test_describe_query_context_tool_matches_python_target_candidates(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)
    tables = list_entities_tool(db, type="rc:Table", graph="map")

    for table in tables["entities"]:
        iri = table["iri"]
        python_payload = to_dict(db.describe_query_context(iri=iri))
        tool_payload = describe_query_context_tool(db, iri=iri)

        assert tool_payload["query_target_candidates"] == python_payload[
            "query_target_candidates"
        ]
        assert tool_payload["query_target_decision"] == python_payload[
            "query_target_decision"
        ]
        assert tool_payload["ready_candidate_indexes"] == python_payload[
            "ready_candidate_indexes"
        ]
        assert tool_payload["unselected_ready_candidate_indexes"] == python_payload[
            "unselected_ready_candidate_indexes"
        ]


def test_describe_query_context_tool_warns_on_complete_s3_template_without_resolution(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#orders_s3_storage",
        label="Orders S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        path_templates=["s3://orders-bucket/warehouse/orders/*.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#orders_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Orders",
        is_table=True,
        storage_accesses=[storage["iri"]],
        physical_layouts=[layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    result = describe_query_context_tool(db, iri=dataset)

    assert result["readiness"] == "needs_review"
    assert any(
        issue["code"] == "s3_access_resolution_unrecorded"
        and issue["resource"]["iri"] == storage["iri"]
        for issue in result["issues"]
    )
    candidate = result["query_target_candidates"][0]
    assert candidate["candidate_path"] == "s3://orders-bucket/warehouse/orders/*.parquet"
    assert candidate["composition"] == "template_as_returned"
    assert candidate["candidate_path_status"] == "orientation_only"
    assert candidate["review_required"] is True
    assert any(
        reason["code"] == "s3_access_resolution_unrecorded"
        for reason in candidate["review_reasons"]
    )


def test_describe_query_context_tool_lifts_repair_action_groups(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Snapshots"
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#snapshots_https_storage",
        label="Snapshots HTTPS access",
        storage_protocol="rc:HTTPSStorage",
        bucket_name="public",
        key_prefix="snapshots",
        path_templates=["dt={date}.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#snapshots_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Snapshots",
        is_table=True,
        storage_accesses=[storage["iri"]],
        physical_layouts=[layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    result = describe_query_context_tool(db, iri=dataset)

    assert result["suggested_repair_action_group_count"] == 1
    repair_group = result["suggested_repair_action_groups"][0]
    assert repair_group["group_name"] == "query_repair_review"
    assert repair_group["issue_code"] == "storage_protocol_location_mismatch"
    assert repair_group["issue_resource"]["iri"] == storage["iri"]
    assert repair_group["repair_hint_path"] == (
        f"issues[{repair_group['issue_index']}].details.repair_hint"
    )
    assert repair_group["repair_action_type"] == (
        "repair_storage_protocol_location_mismatch"
    )
    assert repair_group["requires_review"] is True
    assert repair_group["action_count"] == len(repair_group["actions"])
    assert repair_group["action_status_counts"] == {"pending_review": 6}
    assert repair_group["pending_action_count"] == 6
    assert repair_group["skippable_action_count"] == 0
    assert repair_group["already_satisfied_action_count"] == 0
    assert repair_group["pending_required_extra_arguments"] == ["rationale"]
    action_by_type = {
        action["action_type"]: action for action in repair_group["actions"]
    }
    assert action_by_type["set_reviewed_storage_protocol"][
        "required_extra_arguments"
    ] == ["rationale"]
    assert action_by_type["set_reviewed_storage_protocol"]["placeholder_fields"] == [
        "object"
    ]
    assert action_by_type["set_reviewed_storage_protocol"][
        "reviewed_value_fields"
    ] == ["object"]
    assert action_by_type["remove_conflicting_bucket_name"]["arguments"][
        "object"
    ] == "public"


def test_describe_query_context_tool_lists_missing_storage_candidates(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Messages"
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#messages_storage",
        label="Messages storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(tmp_path / "warehouse"),
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Messages",
        is_table=True,
    )

    result = describe_query_context_tool(db, iri=dataset)

    repair_group = result["suggested_repair_action_groups"][0]
    assert repair_group["issue_code"] == "missing_storage_access"
    assert repair_group["repair_action_type"] == "record_or_link_storage_access"
    assert repair_group["choice_mode"] == "choose_one"
    assert repair_group["action_status_counts"] == {"pending_review": 2}
    assert repair_group["pending_action_count"] == 2
    assert repair_group["skippable_action_count"] == 0
    assert repair_group["already_satisfied_action_count"] == 0
    assert repair_group["pending_required_extra_arguments"] == [
        "iri",
        "storage_protocol",
        "storage_root",
        "object",
        "rationale",
    ]
    assert len(repair_group["pending_action_options"]) == 2
    storage_option = repair_group["pending_action_options"][0]
    _assert_repair_action_option(
        storage_option,
        action_index=0,
        action_type="record_reviewed_storage_access",
        tool_name="record_map_storage_access",
        mcp_tool_name="doxabase.record_map_storage_access",
        action_label="Record storage access and link dataset",
        required_extra_arguments=[
            "iri",
            "storage_protocol",
            "storage_root",
        ],
        placeholder_fields=["path_templates"],
        reviewed_value_fields=["path_templates"],
    )
    assert "non-secret storage protocol" in storage_option["reason"]
    assert "Database relation identifiers" in storage_option["condition"]
    assert "record_map_storage_access writes current-best map facts directly" in (
        storage_option["review_rationale_guidance"]
    )
    link_option = repair_group["pending_action_options"][1]
    _assert_repair_action_option(
        link_option,
        action_index=1,
        action_type="stage_existing_storage_access_link",
        tool_name="stage_map_assertion_change",
        mcp_tool_name="doxabase.stage_map_assertion_change",
        action_label="Stage link to an existing storage access",
        required_extra_arguments=["object", "rationale"],
        placeholder_fields=["object"],
        reviewed_value_fields=["object"],
    )
    assert "suitable storage access resource already exists" in link_option["reason"]
    action_by_type = {
        action["action_type"]: action for action in repair_group["actions"]
    }
    assert set(action_by_type) == {
        "record_reviewed_storage_access",
        "stage_existing_storage_access_link",
    }
    candidates = repair_group["repair_context"][
        "candidate_existing_storage_accesses"
    ]
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate["candidate_rank"] == 1
    assert candidate["storage_access_iri"] == storage["iri"]
    assert candidate["storage_access"]["iri"] == storage["iri"]
    assert candidate["storage_protocol"]["iri"] == RC + "LocalFilesystemStorage"
    assert candidate["storage_root"] == str(tmp_path / "warehouse")
    assert candidate["match_reasons"] == [
        "declares_storage_protocol",
        "has_location_metadata",
        "has_layout_verification_status",
        "dataset_token_overlap",
    ]
    assert candidate["dataset_token_matches"] == ["messages"]
    assert candidate["generic_dataset_token_matches"] == []
    assert candidate["dataset_partial_token_matches"] == []
    assert candidate["generic_dataset_partial_token_matches"] == []
    assert candidate["linked_dataset_iris"] == []
    assert repair_group["repair_context"][
        "candidate_existing_storage_access_count"
    ] == 1
    assert repair_group["repair_context"][
        "candidate_existing_storage_access_total_count"
    ] == 1
    assert repair_group["repair_context"][
        "candidate_existing_storage_accesses_truncated"
    ] is False
    record_action = action_by_type["record_reviewed_storage_access"]
    assert "rc:DatabaseStorage" in record_action["protocol_guidance"]
    assert "database_relation_template_source_mismatch" in (
        record_action["condition"]
    )
    assert "does not record graph-revision rationale" in (
        record_action["review_rationale_guidance"]
    )
    link_action = action_by_type["stage_existing_storage_access_link"]
    assert link_action["placeholder_fields"] == ["object"]
    assert link_action["reviewed_value_fields"] == ["object"]
    assert link_action["arguments_template"]["object"] == (
        "<reviewed existing storage access IRI>"
    )

    link_arguments = dict(link_action["arguments_template"])
    link_arguments["object"] = storage["iri"]
    link_arguments["rationale"] = "Reviewed the existing Messages storage route."
    staged = stage_map_assertion_change_tool(db, **link_arguments)

    pending_result = describe_query_context_tool(db, iri=dataset)
    pending_group = pending_result["suggested_repair_action_groups"][0]
    assert pending_group["repair_context"]["already_pending_candidate_count"] == 1
    assert pending_group["repair_context"][
        "already_pending_storage_access_iris"
    ] == [storage["iri"]]
    assert pending_group["repair_context"]["pending_staged_repair_iris"] == [
        staged["revision_iri"]
    ]
    pending_action_by_type = {
        action["action_type"]: action for action in pending_group["actions"]
    }
    pending_link_action = pending_action_by_type[
        "stage_existing_storage_access_link"
    ]
    assert pending_link_action["already_pending_candidate_count"] == 1
    assert pending_link_action["already_pending_storage_access_iris"] == [
        storage["iri"]
    ]
    assert pending_link_action["pending_staged_repair_iris"] == [
        staged["revision_iri"]
    ]


def test_describe_query_context_tool_surfaces_root_only_targets(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    local_dataset = "https://example.test/project#LocalOrders"
    local_root = str(tmp_path / "orders.parquet")
    local_storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#local_orders_storage",
        label="Local orders storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="object",
        storage_root=local_root,
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    record_map_dataset_tool(
        db,
        iri=local_dataset,
        label="Local orders",
        is_table=True,
        storage_accesses=[local_storage["iri"]],
        physical_layouts=[layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    s3_dataset = "https://example.test/project#S3Orders"
    s3_root = "s3://orders-lake/exports/orders.parquet"
    s3_storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#s3_orders_storage",
        label="S3 orders storage",
        storage_protocol="rc:S3CompatibleStorage",
        location_kind="object",
        storage_root=s3_root,
        endpoint_profile="orders-prod",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    record_map_dataset_tool(
        db,
        iri=s3_dataset,
        label="S3 orders",
        is_table=True,
        storage_accesses=[s3_storage["iri"]],
        physical_layouts=[layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    local_result = describe_query_context_tool(db, iri=local_dataset)
    s3_result = describe_query_context_tool(db, iri=s3_dataset)

    assert local_result["readiness"] == "ready_for_query_planning"
    assert local_result["path_templates"] == []
    local_target = local_result["query_target_candidates"][0]
    assert local_target["template_source"] == "storage_access_location"
    assert local_target["composition"] == "storage_root_as_candidate"
    assert local_target["location_kind"] == "object"
    assert local_target["candidate_path"] == local_root
    assert local_target["candidate_path_status"] == "ready"
    assert local_result["query_target_decision"]["status"] == "ready"
    assert local_result["query_target_decision"]["candidate_index"] == 0
    assert local_result["query_target_decision"]["candidate_path"] == local_root
    assert local_result["query_target_decision"]["reason_codes"] == []

    assert s3_result["readiness"] == "ready_for_query_planning"
    assert s3_result["path_templates"] == []
    s3_target = s3_result["query_target_candidates"][0]
    assert s3_target["template_source"] == "storage_access_location"
    assert s3_target["composition"] == "storage_root_as_candidate"
    assert s3_target["location_kind"] == "object"
    assert s3_target["candidate_path"] == s3_root
    assert s3_target["bucket_name"] is None
    assert s3_target["key_prefix"] is None
    assert s3_target["requires_endpoint_profile"] is True
    assert s3_target["review_reasons"] == []
    assert s3_result["query_target_decision"]["status"] == "ready"
    assert s3_result["query_target_decision"]["candidate_index"] == 0
    assert s3_result["query_target_decision"]["candidate_path"] == s3_root
    assert s3_result["query_target_decision"]["reason_codes"] == []


def test_describe_query_context_tool_demotes_root_only_database_target(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WarehouseOrders"
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#warehouse_orders_storage",
        label="Warehouse orders connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="object",
        storage_root="warehouse-prod",
        endpoint_profile="warehouse-prod",
        credential_reference="profile:warehouse-readonly",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#warehouse_orders_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Warehouse orders",
        is_table=True,
        storage_accesses=[storage["iri"]],
        physical_layouts=[layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = describe_query_context_tool(db, iri=dataset)
    plan = draft_query_plan_tool(db, iri=dataset)

    assert context["readiness"] == "needs_review"
    assert context["issues"][0]["code"] == "database_relation_template_missing"
    details = context["issues"][0]["details"]
    assert {
        key: details[key]
        for key in [
            "storage_access_iri",
            "storage_protocol_iri",
            "storage_root",
            "location_kind",
            "allowed_relation_template_sources",
        ]
    } == {
        "storage_access_iri": storage["iri"],
        "storage_protocol_iri": RC + "DatabaseStorage",
        "storage_root": "warehouse-prod",
        "location_kind": "object",
        "allowed_relation_template_sources": ["storage_access"],
    }
    repair_hint = details["repair_hint"]
    assert repair_hint["action_type"] == "record_database_relation_template"
    assert repair_hint["requires_review"] is True
    assert repair_hint["source"] == {
        "storage_access_iri": storage["iri"],
        "storage_root": "warehouse-prod",
        "location_kind": "object",
    }
    assert repair_hint["target"] == {
        "storage_access_iri": storage["iri"],
        "predicate": "rc:pathTemplate",
        "required_template_source": "storage_access",
    }
    assert repair_hint["actions"][0]["arguments_template"] == {
        "subject": storage["iri"],
        "predicate": "rc:pathTemplate",
        "object": "<reviewed_database_relation_identifier>",
        "object_kind": "literal",
        "change_kind": "add",
        "graph": "map",
    }
    assert repair_hint["actions"][0]["required_extra_arguments"] == [
        "object",
        "rationale",
    ]
    assert repair_hint["actions"][0]["placeholder_fields"] == ["object"]
    assert repair_hint["actions"][0]["reviewed_value_fields"] == ["object"]
    target = context["query_target_candidates"][0]
    assert target["template_source"] == "storage_access_location"
    assert target["composition"] == "database_connection_as_candidate"
    assert target["location_kind"] == "object"
    assert target["candidate_path"] == "warehouse-prod"
    assert target["relation_identifier"] is None
    assert target["connection_reference"] == "warehouse-prod"
    assert target["candidate_path_status"] == "orientation_only"
    assert target["direct_review_reasons"][0]["code"] == (
        "database_relation_template_missing"
    )
    assert context["query_target_decision"]["status"] == "candidate_needs_review"
    assert context["query_target_decision"]["reason_codes"] == [
        "database_relation_template_missing"
    ]
    assert plan["scan"]["uri_template"] is None
    assert plan["scan"]["relation_identifier"] is None
    assert plan["scan"]["connection_reference"] == "warehouse-prod"
    assert plan["review_gate"]["blocking_reason_codes"] == [
        "database_relation_template_missing"
    ]
    assert plan["handoff_kind"] == "metadata_review_required"


def test_describe_query_context_tool_demotes_directory_root_only_target(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    dataset = "https://example.test/project#LocalOrders"
    storage_root = str(tmp_path / "orders")
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#local_orders_storage",
        label="Local orders storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="directory",
        storage_root=storage_root,
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Local orders",
        is_table=True,
        storage_accesses=[storage["iri"]],
        physical_layouts=[layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    result = describe_query_context_tool(db, iri=dataset)

    assert result["readiness"] == "needs_review"
    assert result["storage_accesses"][0]["location_kind"] == "directory"
    target = result["query_target_candidates"][0]
    assert target["template_source"] == "storage_access_location"
    assert target["location_kind"] == "directory"
    assert target["candidate_path_status"] == "orientation_only"
    assert target["direct_review_required"] is True
    assert target["review_reasons"][0]["code"] == (
        "storage_location_kind_needs_path_template"
    )
    assert target["direct_review_reasons"][0]["code"] == (
        "storage_location_kind_needs_path_template"
    )
    assert result["query_target_decision"]["status"] == "candidate_needs_review"
    assert result["query_target_decision"]["candidate_index"] == 0
    assert result["query_target_decision"]["candidate_path"] == storage_root
    assert result["query_target_decision"]["candidate_path_status"] == (
        "orientation_only"
    )
    assert result["query_target_decision"]["direct_review_required"] is True
    assert result["query_target_decision"]["reason_codes"] == [
        "storage_location_kind_needs_path_template"
    ]


def test_describe_query_context_tool_keeps_directory_root_with_template_ready(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    dataset = "https://example.test/project#LocalOrders"
    storage_root = str(tmp_path / "lake")
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#local_orders_storage",
        label="Local orders storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="directory",
        storage_root=storage_root,
        path_templates=["orders/*.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Local orders",
        is_table=True,
        storage_accesses=[storage["iri"]],
        physical_layouts=[layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    result = describe_query_context_tool(db, iri=dataset)

    assert result["readiness"] == "ready_for_query_planning"
    assert result["storage_accesses"][0]["location_kind"] == "directory"
    target = result["query_target_candidates"][0]
    assert target["template_source"] == "storage_access"
    assert target["location_kind"] == "directory"
    assert target["composition"] == "storage_root_joined"
    assert target["candidate_path"] == f"{storage_root}/orders/*.parquet"
    assert target["candidate_path_status"] == "ready"
    assert target["review_reasons"] == []
    assert target["direct_review_required"] is False
    assert target["direct_review_reasons"] == []
    assert result["query_target_decision"]["status"] == "ready"
    assert result["query_target_decision"]["candidate_index"] == 0
    assert result["query_target_decision"]["candidate_path"] == (
        f"{storage_root}/orders/*.parquet"
    )
    assert result["query_target_decision"]["reason_codes"] == []


def test_describe_dataset_tool_exposes_aggregation_context(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)

    result = describe_dataset_tool(
        db,
        iri="https://richcanopy.org/example/manifest/ais#DailyIndex",
    )

    aggregation = next(
        relationship
        for relationship in result["relationships"]
        if relationship["relationship_kind"] == "https://richcanopy.org/ns/rc#Aggregation"
    )
    assert aggregation["source_dataset"]["label"] == "AIS Daily Broadcast Positions"
    assert aggregation["group_by_columns"][0]["column_name"] == "mmsi"
    assert result["layout_verification_status"]["iri"] == (
        "https://richcanopy.org/ns/rc#UnverifiedLayout"
    )
    assert "index/{year}/ais-{date}.parquet" in result[
        "layout_verification_note"
    ]
    assert result["partition_schemes"][0]["layout_verification_status"]["iri"] == (
        "https://richcanopy.org/ns/rc#GeneratedFromManifestLayout"
    )
    assert any(
        warning["code"] == "layout_needs_verification"
        and warning["domain"] == "query_planning"
        and warning["resource"]["iri"]
        == "https://richcanopy.org/example/manifest/ais#DailyIndex"
        for warning in result["operational_warnings"]
    )
    assert result["caveats"] == []
    assert any(
        caveat["description"]
        and "MMSI does not reliably identify a single vessel" in caveat["description"]
        for caveat in result["upstream_caveats"]
    )
    message_count_mapping = next(
        mapping
        for mapping in aggregation["aggregated_columns"]
        if mapping["target_column"]["column_name"] == "message_count"
    )
    assert message_count_mapping["source_columns"][0]["column_name"] == "mmsi"
    assert message_count_mapping["aggregation_function"]["iri"] == (
        "https://richcanopy.org/ns/rc#Count"
    )

    wrong_predicate = describe_assertion_support_tool(
        db,
        subject="https://richcanopy.org/example/manifest/ais#DailyIndex",
        predicate="rc:hasPartitionScheme",
        object="https://richcanopy.org/example/manifest/ais#daily_date_partition",
        object_kind="iri",
    )
    assert wrong_predicate["assertion_present"] is False
    assert "the requested predicate is absent on this subject" in (
        wrong_predicate["absence_note"]
    )
    assert "Nearby predicates on the same subject include" in (
        wrong_predicate["absence_note"]
    )
    assert "rc:partitionedBy" in wrong_predicate["absence_note"]
    assert any(
        hint["predicate"] == "https://richcanopy.org/ns/rc#partitionedBy"
        and hint["predicate_curie"] == "rc:partitionedBy"
        and hint["sample_values"][0]["value"]
        == "https://richcanopy.org/example/manifest/ais#daily_date_partition"
        for hint in wrong_predicate["predicate_hints"]
    )
    assert any(
        caveat["description"]
        and "MMSI does not reliably identify a single vessel" in caveat["description"]
        for caveat in aggregation["source_caveats"]
    )
    assert any(
        related["relationship"] == "aggregated_from"
        and related["label"] == "AIS Daily Broadcast Positions"
        for related in result["related_datasets"]
    )
    broadcast_group = next(
        group
        for group in result["related_dataset_groups"]
        if group["label"] == "AIS Daily Broadcast Positions"
    )
    assert any(
        caveat["impact"] and "Grouping by MMSI may conflate" in caveat["impact"]
        for reason in broadcast_group["reasons"]
        for caveat in reason["source_caveats"]
    )


def test_describe_context_slice_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)
    seed_iri = "https://richcanopy.org/example/manifest/polymarket#MarketSnapshots"
    pattern = record_pattern_tool(
        db,
        summary="Market snapshots carry hourly Gamma market state.",
        pattern_text="Treat market snapshots as hourly Gamma state around condition IDs.",
        rationale="The fixture map describes snapshot rows, condition IDs, and hourly partitions together.",
        pattern_targets=[seed_iri],
        source_path="tests/test_mcp_tools.py",
        source_kind="rc:DocumentationSource",
    )

    result = describe_context_slice_tool(
        db,
        seed_iris=[seed_iri],
        profile="dataset_brief",
        max_triples=120,
    )

    assert result["profile"] == "dataset_brief"
    assert result["seeds"][0]["label"] == "Gamma Market Snapshots"
    assert result["dataset_contexts"][0]["iri"] == seed_iri
    assert result["pattern_contexts"]
    assert result["resource_count"] == len(result["resources"])
    assert result["route_counts"]["dataset_column"] >= 1
    assert result["route_counts"]["linked_pattern"] >= 1
    assert result["reading_order"][0].startswith("Start with seeds")
    assert any("route_summaries" in step for step in result["reading_order"])
    assert any(
        route["route"] == "seed"
        and route["count"] == 1
        and route["priority"] == 0
        and route["meaning"] == "The resource the caller asked about directly."
        for route in result["route_legend"]
    )
    assert result["triple_count"] <= 120
    assert result["returned_triple_count"] == result["triple_count"]
    assert result["candidate_triple_count"] >= result["returned_triple_count"]
    assert result["omitted_triple_count"] == (
        result["candidate_triple_count"] - result["returned_triple_count"]
    )
    assert result["truncation_scope"] == "triples_only"
    assert result["truncated"] is True
    assert result["omitted_triple_count"] > 0
    assert [
        action["action_label"] for action in result["suggested_next_actions"]
    ] == [
        "Narrow to pattern context",
        "Return full raw RDF for slice",
    ]
    assert result["suggested_next_actions"][0]["arguments"] == {
        "seed_iris": [pattern["pattern_iri"]],
        "profile": "pattern_brief",
        "max_triples": 120,
    }
    assert result["suggested_next_actions"][1]["arguments"] == {
        "seed_iris": [seed_iri],
        "profile": "dataset_brief",
        "max_triples": result["candidate_triple_count"],
    }
    assert result["suggested_next_calls"] == [
        action["call"] for action in result["suggested_next_actions"]
    ]
    assert result["triples"][0]["subject"] == seed_iri
    assert result["trig"] is None
    resources_by_iri = {resource["iri"]: resource for resource in result["resources"]}
    assert resources_by_iri[seed_iri]["surface_role"] == "current_map_context"
    assert resources_by_iri[pattern["pattern_iri"]]["surface_role"] == (
        "pattern_synthesis"
    )
    seed_resource = resources_by_iri[seed_iri]
    assert seed_resource["primary_route"] == seed_resource["routes"][0]
    assert set(seed_resource["primary_route"]) == {
        "depth",
        "route",
        "route_label",
        "source_iri",
        "source_label",
    }
    assert any(
        resource["iri"]
        == "https://richcanopy.org/example/manifest/polymarket#MarketSnapshots"
        and resource["referenced_only"] is False
        and resource["primary_route"]["route"] == "seed"
        and any(route["route"] == "seed" for route in resource["routes"])
        for resource in result["resources"]
    )

    warning_db = DoxaBase.create(tmp_path / "warning-capsule.sqlite")
    warning_dataset = "https://example.test/project#Events"
    warning_layout = record_map_physical_layout_tool(
        warning_db,
        iri="https://example.test/project#events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        warning_db,
        iri=warning_dataset,
        label="Events",
        is_table=True,
        path_templates=["events/date={date}/*.parquet"],
        physical_layouts=[warning_layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    warning_result = describe_context_slice_tool(
        warning_db,
        seed_iris=[warning_dataset],
        profile="dataset_brief",
    )
    assert warning_result["truncated"] is False
    assert warning_result["warnings"] == []
    assert warning_result["dataset_contexts"][0]["operational_warnings"][0][
        "code"
    ] == "missing_storage_access"
    assert [
        action["tool_name"] for action in warning_result["suggested_next_actions"]
    ] == ["describe_query_context"]
    warning_action = warning_result["suggested_next_actions"][0]
    assert warning_action["mcp_tool_name"] == "doxabase.describe_query_context"
    assert warning_action["arguments"] == {"iri": warning_dataset}
    assert "missing_storage_access" in warning_action["reason"]
    assert warning_result["suggested_next_calls"] == [warning_action["call"]]

    repair_db = DoxaBase.create(tmp_path / "repair-capsule.sqlite")
    repair_dataset = "https://example.test/project#WarehouseOrders"
    relation = "mart.orders"
    repair_storage = record_map_storage_access_tool(
        repair_db,
        iri="https://example.test/project#orders_database_storage",
        label="Orders database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    repair_layout = record_map_physical_layout_tool(
        repair_db,
        iri="https://example.test/project#orders_table_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        repair_db,
        iri=repair_dataset,
        label="Warehouse orders",
        is_table=True,
        path_templates=[relation],
        storage_accesses=[repair_storage["iri"]],
        physical_layouts=[repair_layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    repair_result = describe_context_slice_tool(
        repair_db,
        seed_iris=[repair_dataset],
        profile="dataset_brief",
    )
    assert repair_result["truncated"] is False
    assert repair_result["dataset_contexts"][0]["operational_warnings"] == []
    assert [
        action["tool_name"] for action in repair_result["suggested_next_actions"]
    ] == ["describe_query_context"]
    repair_action = repair_result["suggested_next_actions"][0]
    assert repair_action["arguments"] == {"iri": repair_dataset}
    assert (
        "database_relation_template_source_mismatch" in repair_action["reason"]
    )
    repair_context = describe_query_context_tool(repair_db, iri=repair_dataset)
    assert repair_context["suggested_repair_action_groups"][0]["issue_code"] == (
        "database_relation_template_source_mismatch"
    )
    assert repair_result["suggested_next_calls"] == [repair_action["call"]]

    mismatch = describe_context_slice_tool(
        db,
        seed_iris=[pattern["pattern_iri"]],
        profile="dataset_brief",
        max_triples=120,
    )
    assert mismatch["pattern_contexts"] == []
    assert any(
        "Seed is an rc:Pattern; rerun with profile='pattern_brief' or 'deep_lore'."
        in warning
        for warning in mismatch["warnings"]
    )
    claim = record_claim_observation_tool(
        db,
        summary="Market snapshots are hourly state.",
        claim_text="Market snapshots are hourly state.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=[seed_iri],
        evidence_summary="Context-slice wrapper claim evidence.",
        source_path="tests/test_mcp_tools.py",
        source_kind="rc:DocumentationSource",
    )
    claim_mismatch = describe_context_slice_tool(
        db,
        seed_iris=[claim["claim_iri"]],
        profile="dataset_brief",
        max_triples=120,
    )
    assert claim_mismatch["route_counts"] == {"seed": 1}
    assert any(
        "Seed is an rc:Claim; rerun with profile='pattern_brief' or 'deep_lore'."
        in warning
        for warning in claim_mismatch["warnings"]
    )


def test_describe_context_slice_tool_preserves_profile_routes(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    metric_kind = "https://example.test/project#CompletenessRatio"
    record_map_dataset_tool(db, dataset, label="Orders", is_table=True)
    profile = record_dataset_profile_tool(
        db,
        dataset_iri=dataset,
        summary="Orders were profiled for completeness.",
        evidence_summary="Dataset profile run.",
        evidence_sources=["test://orders-profile"],
        profile_metrics=[
            {"metric": metric_kind, "value": 0.98, "target": dataset},
        ],
        update_map_snapshot=False,
    )

    result = describe_context_slice_tool(
        db,
        seed_iris=[metric_kind],
        profile="dataset_brief",
        max_triples=200,
    )

    resource_iris = {resource["iri"] for resource in result["resources"]}
    assert metric_kind in resource_iris
    assert profile["observation"]["observation_iri"] in resource_iris
    assert dataset in resource_iris
    assert result["dataset_contexts"][0]["iri"] == dataset
    assert [
        profile_summary["iri"]
        for profile_summary in result["seed_profile_observations"]
    ] == [profile["observation"]["observation_iri"]]
    seed_profile = result["seed_profile_observations"][0]
    assert seed_profile["profile_metrics"][0]["iri"]
    assert seed_profile["profile_metrics"][0]["metric"]["iri"] == metric_kind
    assert seed_profile["profile_metrics"][0]["target"]["iri"] == dataset
    assert seed_profile["profile_metrics"][0]["value"] == "0.98"
    assert seed_profile["profile_metrics"][0]["value_datatype"].startswith(
        "http://www.w3.org/2001/XMLSchema#"
    )
    assert seed_profile["profile_metrics"][0]["value_lang"] is None
    assert result["route_counts"]["seed_profile_metric_kind"] == 1
    assert result["route_counts"]["profile_metric_observation"] == 1
    legend = {row["route"]: row for row in result["route_legend"]}
    assert legend["profile_metric_observation"]["meaning"].startswith(
        "A profile observation reached from a selected observed profile metric"
    )


def test_record_observation_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    result = record_observation_tool(
        db,
        summary="MCP helper wrote a structured observation.",
        observed_by="urn:doxabase:test-agent",
        evidence_summary="Evidence written by the MCP helper test.",
        evidence_sources=["tests/test_mcp_tools.py"],
    )

    assert result["observation_iri"].startswith(
        "https://richcanopy.org/doxabase/generated/observation/"
    )
    assert result["observation_type"] == "observation"
    assert result["evidence_iri"] is not None
    assert result["observation_triples"] > 0
    assert result["evidence_triples"] > 0
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_record_observation_tool_accepts_profile_type_findings(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    column = "https://example.test/project#OrdersStatus"
    value_type = "https://example.test/project#OrderStatusCode"
    record_map_dataset_tool(db, dataset, label="Orders", is_table=True)
    replace_graph_triples_tool(
        db,
        graph="ontology",
        additions=f"""
            @prefix rc: <https://richcanopy.org/ns/rc#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            <{value_type}> a rc:ValueType ;
                rdfs:label "Order status code" .
        """,
        allow_count_change=True,
    )

    result = record_observation_tool(
        db,
        summary="MCP helper wrote a profile type finding.",
        observation_type="profile",
        observed_asset=dataset,
        observed_column=column,
        observed_column_name="status",
        observed_physical_type="rc:Integer",
        observed_value_type=value_type,
        evidence_summary="Synthetic profile type evidence.",
        evidence_sources=["tests/test_mcp_tools.py"],
    )

    profile_run = describe_profile_run_tool(
        db,
        dataset_iri=dataset,
        evidence_iri=result["evidence_iri"],
    )
    profile = profile_run["unmapped_column_profile_observations"][0]
    assert profile["iri"] == result["observation_iri"]
    assert profile["observed_physical_type"]["iri"] == RC + "Integer"
    assert profile["observed_value_type"]["iri"] == value_type
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_record_dataset_profile_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Messages"

    result = record_dataset_profile_tool(
        db,
        dataset_iri=dataset,
        summary="MCP helper recorded a profile bundle.",
        evidence_summary="Synthetic profile evidence.",
        evidence_sources=["tests/test_mcp_tools.py"],
        sample_size=55,
        sample_scope="All rows in the synthetic Messages table.",
        sample_method="DuckDB full-table profile.",
        row_count=55,
        distinct_count=54,
        value_frequencies=[
            {"value": "open", "frequency": 40},
            {"value": "closed", "frequency": 15},
        ],
        profile_metrics=[
            {"metric": "rc:MinimumValue", "value": 3, "target": dataset},
            {"metric": "rc:MaximumValue", "value": 99},
        ],
        map_label="Messages",
        is_table=True,
        pattern_summary="Messages profile looks stable.",
        pattern_text="The profile row count and distinct count nearly match.",
        pattern_rationale=(
            "A linked profile pattern keeps the profile synthesis reviewable."
        ),
    )

    assert result["dataset_iri"] == dataset
    assert result["observation"]["observation_type"] == "profile"
    assert result["map_dataset"]["iri"] == dataset
    assert result["pattern"]["pattern_iri"].startswith(
        "https://richcanopy.org/doxabase/generated/pattern/"
    )
    assert describe_dataset_tool(db, dataset)["row_count_snapshot"] == 55
    profile = describe_dataset_tool(db, dataset)["profile_observations"][0]
    assert profile["sample_size"] == 55
    assert profile["sample_scope"] == "All rows in the synthetic Messages table."
    assert profile["sample_method"] == "DuckDB full-table profile."
    assert profile["row_count"] == 55
    assert profile["distinct_count"] == 54
    assert [
        (item["value"], item["frequency"]) for item in profile["value_frequencies"]
    ] == [("open", 40), ("closed", 15)]
    assert {
        (
            item["metric"]["iri"],
            item["target"]["iri"] if item["target"] is not None else None,
            item["value"],
            item["value_datatype"],
        )
        for item in profile["profile_metrics"]
    } == {
        (
            "https://richcanopy.org/ns/rc#MinimumValue",
            dataset,
            "3",
            str(XSD.integer),
        ),
        (
            "https://richcanopy.org/ns/rc#MaximumValue",
            None,
            "99",
            str(XSD.integer),
        ),
    }
    assert profile["evidence"][0]["iri"] == result["observation"]["evidence_iri"]
    assert profile["evidence"][0]["sources"] == ["tests/test_mcp_tools.py"]
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_record_column_profile_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Messages"
    column = "https://example.test/project#MessagesDocId"
    record_map_dataset_tool(db, table, label="Messages", is_table=True)

    result = record_column_profile_tool(
        db,
        column_iri=column,
        column_name="doc_id",
        table_iri=table,
        summary="MCP helper recorded a column profile bundle.",
        evidence_summary="Synthetic column profile evidence.",
        evidence_sources=["tests/test_mcp_tools.py"],
        sample_size=55,
        sample_scope="All doc_id values in the synthetic Messages table.",
        sample_method="DuckDB column aggregate query.",
        row_count=55,
        null_count=0,
        distinct_count=55,
        value_frequencies=[
            {"value": "doc-001", "frequency": 1},
            {"value": "doc-002", "frequency": 1},
        ],
        profile_metrics=[
            {"metric": "rc:MeanValue", "value": 12.5},
        ],
        map_label="Messages.doc_id",
        physical_type="rc:Varchar",
        nullable=False,
        pattern_summary="doc_id profile looks complete.",
        pattern_text="The profile found no null doc_id values and all values distinct.",
        pattern_rationale="The profile is a useful identity hunch for later review.",
    )

    assert result["column_iri"] == column
    assert result["table_iri"] == table
    assert result["observation"]["observation_type"] == "profile"
    assert result["map_column"]["iri"] == column
    assert result["pattern"]["pattern_iri"].startswith(
        "https://richcanopy.org/doxabase/generated/pattern/"
    )
    dataset = describe_dataset_tool(db, table)
    assert dataset["columns"][0]["iri"] == column
    assert dataset["columns"][0]["nullable"] is False
    profile = dataset["columns"][0]["profile_observations"][0]
    assert profile["sample_size"] == 55
    assert profile["sample_scope"] == (
        "All doc_id values in the synthetic Messages table."
    )
    assert profile["sample_method"] == "DuckDB column aggregate query."
    assert profile["row_count"] == 55
    assert profile["null_count"] == 0
    assert profile["distinct_count"] == 55
    assert [
        (item["value"], item["frequency"]) for item in profile["value_frequencies"]
    ] == [("doc-001", 1), ("doc-002", 1)]
    assert profile["profile_metrics"][0]["metric"]["iri"] == (
        "https://richcanopy.org/ns/rc#MeanValue"
    )
    assert profile["profile_metrics"][0]["value"] == "12.5"
    assert profile["observed_column"]["iri"] == column
    assert profile["evidence"][0]["sources"] == ["tests/test_mcp_tools.py"]
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_record_profile_bundle_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    shared_evidence = "https://example.test/project#OrdersProfileRunEvidence"

    result = record_profile_bundle_tool(
        db,
        dataset_iri=table,
        dataset_summary="MCP helper recorded a dataset and column profile pass.",
        evidence_summary="Synthetic profile bundle evidence.",
        evidence_sources=["tests/test_mcp_tools.py"],
        sample_size=25,
        sample_scope="Twenty-five sampled Orders rows.",
        sample_method="DuckDB sampled profile query.",
        row_count=1000,
        map_label="Orders",
        is_table=True,
        shared_evidence_iri=shared_evidence,
        pattern_summary="Orders profile bundle supports a run-level synthesis.",
        pattern_text=(
            "The dataset profile and status column profile came from the same "
            "sampled Orders profiling pass."
        ),
        pattern_rationale="Both returned profile observations link to shared evidence.",
        pattern_support_scope="all_profiles",
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Sampled status values were profiled.",
                "distinct_count": 3,
                "value_frequencies": [
                    {"value": "fulfilled", "frequency": 18},
                    {"value": "pending", "frequency": 4},
                ],
            }
        ],
    )

    assert result["dataset_iri"] == table
    assert result["shared_evidence_iri"] == shared_evidence
    assert result["dataset_profile"]["observation"]["observation_type"] == "profile"
    assert result["dataset_profile"]["map_dataset"]["iri"] == table
    assert result["dataset_profile"]["pattern"]["pattern_iri"].startswith(
        "https://richcanopy.org/doxabase/generated/pattern/"
    )
    assert len(result["column_profiles"]) == 1
    assert result["column_profiles"][0]["column_iri"] == status_column
    assert result["column_profiles"][0]["map_column"] is None
    assert result["dataset_profile"]["observation"]["evidence_iri"] == shared_evidence
    assert result["column_profiles"][0]["observation"]["evidence_iri"] == shared_evidence
    assert result["handoff_entrypoints"]["dataset_iri"] == table
    assert result["handoff_entrypoints"]["shared_evidence_iri"] == shared_evidence
    assert result["handoff_entrypoints"]["dataset_describe_available"] is True
    assert result["handoff_entrypoints"]["profile_run_available"] is True
    assert result["handoff_entrypoints"]["profile_observation_iris"] == [
        result["dataset_profile"]["observation"]["observation_iri"],
        result["column_profiles"][0]["observation"]["observation_iri"],
    ]
    assert result["handoff_entrypoints"]["suggested_next_calls"][:2] == [
        f"describe_dataset('{table}')",
        f"describe_profile_run('{table}', '{shared_evidence}')",
    ]
    assert result["handoff_entrypoints"]["suggested_next_calls"][2] == (
        f"draft_profile_map_updates('{table}', '{shared_evidence}')"
    )
    assert [
        action["tool_name"]
        for action in result["handoff_entrypoints"]["suggested_next_actions"]
    ] == [
        "describe_dataset",
        "describe_profile_run",
        "draft_profile_map_updates",
        "describe_context_slice",
        "describe_context_slice",
    ]
    assert result["handoff_entrypoints"]["suggested_next_actions"][1][
        "arguments"
    ] == {
        "dataset_iri": table,
        "evidence_iri": shared_evidence,
    }
    assert result["handoff_entrypoints"]["suggested_next_actions"][2][
        "arguments"
    ] == {
        "dataset_iri": table,
        "evidence_iri": shared_evidence,
    }
    assert result["handoff_entrypoints"]["suggested_next_actions"][-1][
        "arguments"
    ] == {
        "seed_iris": result["handoff_entrypoints"]["profile_observation_iris"],
        "profile": "dataset_brief",
    }
    assert result["handoff_entrypoints"]["suggested_next_calls"][-1] == (
        "describe_context_slice("
        f"{result['handoff_entrypoints']['profile_observation_iris']!r}, "
        "profile='dataset_brief')"
    )

    dataset = describe_dataset_tool(db, table)

    assert dataset["row_count_snapshot"] is None
    assert dataset["columns"] == []
    assert dataset["profile_summary"]["returned_dataset_profile_count"] == 1
    assert dataset["profile_summary"]["returned_mapped_column_profile_count"] == 0
    assert dataset["profile_summary"]["returned_unmapped_column_profile_count"] == 1
    assert dataset["profile_summary"]["returned_profile_count"] == 2
    assert dataset["profile_summary"]["total_profile_count"] == 2
    assert dataset["profile_summary"]["omitted_profile_count"] == 0
    assert dataset["profile_summary"]["mapped_profiled_column_count"] == 0
    assert dataset["profile_summary"]["evidence_iris"] == [shared_evidence]
    assert dataset["profile_summary"]["evidence_profile_counts"] == {
        shared_evidence: 2,
    }
    assert dataset["profile_summary"]["shared_evidence_iris"] == [shared_evidence]
    assert dataset["profile_summary"]["profile_run_candidates"] == [
        {
            "evidence_iri": shared_evidence,
            "returned_profile_count": 2,
            "profile_observation_iris": [
                result["dataset_profile"]["observation"]["observation_iri"],
                result["column_profiles"][0]["observation"]["observation_iri"],
            ],
            "dataset_profile_row_counts": [1000],
            "dataset_profile_row_count_bases": {"1000": ["sample"]},
            "row_count_snapshot_matches": False,
            "row_count_snapshot_basis": None,
            "shared_by_all_returned_profiles": True,
        }
    ]
    query_context = describe_query_context_tool(db, table)
    assert query_context["row_count_snapshot"] is None
    assert query_context["profile_summary"]["evidence_iris"] == [shared_evidence]
    assert query_context["profile_summary"]["profile_run_candidates"] == (
        dataset["profile_summary"]["profile_run_candidates"]
    )
    assert "Profile lore is observed evidence" in (
        query_context["profile_summary"]["handoff_note"]
    )
    assert [
        action["tool_name"] for action in query_context["suggested_next_actions"]
    ] == [
        "describe_profile_run",
    ]
    assert query_context["suggested_next_actions"][0]["arguments"] == {
        "dataset_iri": table,
        "evidence_iri": shared_evidence,
    }
    profile_run = describe_profile_run_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
    )
    assert profile_run["returned_profile_count"] == 2
    assert profile_run["total_profile_count"] == 2
    assert profile_run["omitted_profile_count"] == 0
    assert set(profile_run["profile_observation_iris"]) == {
        result["dataset_profile"]["observation"]["observation_iri"],
        result["column_profiles"][0]["observation"]["observation_iri"],
    }
    bundle_pattern = describe_pattern_tool(
        db,
        result["dataset_profile"]["pattern"]["pattern_iri"],
    )
    assert {item["iri"] for item in bundle_pattern["supporting_observations"]} == set(
        profile_run["profile_observation_iris"]
    )
    assert bundle_pattern["evidence"][0]["iri"] == shared_evidence
    pattern = record_pattern_tool(
        db,
        summary="Orders profile bundle supports a cross-profile synthesis.",
        pattern_text=(
            "The dataset profile and status column profile came from the same "
            "sampled Orders profiling pass."
        ),
        rationale="Both returned profile observations link to the same run evidence.",
        pattern_targets=[table, status_column],
        supporting_observations=profile_run["profile_observation_iris"],
        evidence_iri=shared_evidence,
    )
    assert pattern["evidence_iri"] == shared_evidence
    assert describe_pattern_tool(db, pattern["pattern_iri"])["evidence"][0]["iri"] == (
        shared_evidence
    )
    profile = dataset["unmapped_column_profile_observations"][0]
    assert profile["observed_column_name"] == "status"
    assert profile["observed_column"]["column_name"] == "status"
    assert profile["sample_scope"] == "Twenty-five sampled Orders rows."
    assert profile["sample_method"] == "DuckDB sampled profile query."
    assert profile["evidence"][0]["iri"] == shared_evidence
    assert profile["evidence"][0]["sources"] == ["tests/test_mcp_tools.py"]
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_draft_profile_map_updates_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    shared_evidence = "https://example.test/project#OrdersProfileRunEvidence"
    project_metric = "https://example.test/project#CompletenessRatio"

    db.record_map_dataset(table, label="Orders", is_table=True, row_count_snapshot=8)
    db.record_map_column(
        status_column,
        table_iri=table,
        column_name="status",
        nullable=False,
    )
    record_profile_bundle_tool(
        db,
        dataset_iri=table,
        dataset_summary="Orders were profiled with a full-table scan.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=shared_evidence,
        sample_size=10,
        sample_scope="All rows in the Orders table.",
        sample_method="DuckDB full-table profile.",
        row_count=10,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": project_metric,
                "value": "0.90",
                "datatype": "xsd:decimal",
            }
        ],
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status had nulls in the full scan.",
                "null_count": 1,
                "physical_type": "rc:Varchar",
            }
        ],
    )

    result = draft_profile_map_updates_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
    )

    assert result["dataset"]["iri"] == table
    assert result["evidence_iri"] == shared_evidence
    assert result["map_dataset_found"] is True
    assert result["recommendation_count"] == 2
    assert result["representative_recommendation_indexes"] == [0, 1]
    assert [
        (
            recommendation["recommendation_index"],
            recommendation["kind"],
            recommendation["resource"]["iri"],
        )
        for recommendation in result["recommendations"]
    ] == [
        (0, "dataset_row_count_snapshot", table),
        (1, "column_nullable", status_column),
    ]
    assert result["suggested_next_actions"][0]["tool_name"] == (
        "stage_profile_map_updates"
    )
    assert result["suggested_next_actions"][0]["arguments"] == {
        "dataset_iri": table,
        "evidence_iri": shared_evidence,
        "accepted_recommendation_indexes": [0, 1],
    }
    assert result["suggested_next_calls"][0].startswith(
        "stage_profile_map_updates("
    )
    assert list(result["suggested_next_action_groups"]) == [
        "profile_map_updates",
        "metric_vocabulary_review",
        "profile_type_review",
    ]
    assert [
        action["tool_name"]
        for action in result["suggested_next_action_groups"]["profile_map_updates"]
    ] == ["stage_profile_map_updates"]
    map_action_source = result["suggested_next_action_groups"][
        "profile_map_updates"
    ][0]["source_profile_map_update"]
    assert map_action_source["review_lane"] == "profile_map_updates"
    assert map_action_source["route_group_key"].startswith("profile_map_updates:")
    assert map_action_source["route_step_key"].startswith("profile-route-step:")
    assert map_action_source["recommendation_indexes"] == [0, 1]
    assert [
        action["tool_name"]
        for action in result["suggested_next_action_groups"][
            "metric_vocabulary_review"
        ]
    ] == ["describe_context_slice", "list_entities"]
    metric_action_source = result["suggested_next_action_groups"][
        "metric_vocabulary_review"
    ][0]["source_profile_advisory"]
    assert metric_action_source["advisory_kind"] == "metric_vocabulary_review"
    assert metric_action_source["index_field"] == "metric_advisory_index"
    assert metric_action_source["advisory_indexes"] == [0]
    assert metric_action_source["duplicate_advisory_indexes"] == [0]
    assert metric_action_source["route_group_key"].startswith(
        "metric_vocabulary_review:"
    )
    assert metric_action_source["route_step_key"].startswith("profile-route-step:")
    assert metric_action_source["observed_metric_iris"] == [
        result["metric_advisories"][0]["observed_metric_iri"]
    ]
    assert [
        action["tool_name"]
        for action in result["suggested_next_action_groups"]["profile_type_review"]
    ] == ["describe_context_slice", "record_pattern", "stage_map_assertion_change"]
    type_action_source = result["suggested_next_action_groups"][
        "profile_type_review"
    ][0]["source_profile_advisory"]
    assert type_action_source["advisory_kind"] == "profile_type_review"
    assert type_action_source["index_field"] == "type_advisory_index"
    assert type_action_source["advisory_indexes"] == [0]
    assert type_action_source["duplicate_advisory_indexes"] == [0]
    assert type_action_source["route_group_key"].startswith("profile_type_review:")
    assert type_action_source["route_step_key"].startswith("profile-route-step:")
    assert result["suggested_next_call_groups"]["profile_map_updates"] == [
        result["suggested_next_calls"][0]
    ]
    assert result["recommendations"][0]["helper_arguments"] == {
        "iri": table,
        "row_count_snapshot": 10,
    }
    assert result["recommendations"][0]["sample_size"] == 10
    assert result["recommendations"][0]["sample_scope"] == (
        "All rows in the Orders table."
    )
    assert result["recommendations"][0]["sample_method"] == (
        "DuckDB full-table profile."
    )
    assert result["recommendations"][0]["profile_row_count"] == 10
    assert result["recommendations"][0]["default_stageable"] is True
    assert result["recommendations"][0]["default_skip_reason"] is None
    assert result["recommendations"][0]["duplicate_group_key"].startswith(
        "profile-map-update:"
    )
    assert result["recommendations"][0]["duplicate_count"] == 1
    assert result["recommendations"][0]["duplicate_recommendation_indexes"] == [0]
    assert result["recommendations"][0]["duplicate_profile_observation_iris"] == [
        result["recommendations"][0]["profile_observation_iri"]
    ]
    assert result["recommendations"][1]["helper_arguments"]["nullable"] is True
    assert result["recommendations"][1]["default_stageable"] is True
    assert result["recommendations"][1]["default_skip_reason"] is None
    assert result["metric_advisory_count"] == 1
    assert result["representative_metric_advisory_indexes"] == [0]
    assert result["metric_advisory_status_counts"] == {
        "project_metric_undefined": 1,
    }
    assert result["metric_advisories"][0]["metric"]["iri"] == project_metric
    assert result["metric_advisories"][0]["metric_advisory_index"] == 0
    assert result["metric_advisories"][0]["advisory_status"] == (
        "project_metric_undefined"
    )
    assert result["metric_advisories"][0]["definition_found"] is False
    assert result["metric_advisories"][0]["duplicate_group_key"].startswith(
        "profile-metric-advisory:"
    )
    assert result["metric_advisories"][0]["duplicate_count"] == 1
    assert result["metric_advisories"][0]["duplicate_advisory_indexes"] == [0]
    assert result["metric_advisories"][0]["duplicate_profile_observation_iris"] == [
        result["metric_advisories"][0]["profile_observation_iri"]
    ]
    assert result["metric_advisories"][0]["suggested_next_actions"][0][
        "tool_name"
    ] == "describe_context_slice"
    assert result["type_advisory_count"] == 1
    assert result["representative_type_advisory_indexes"] == [0]
    assert result["type_advisory_status_counts"] == {
        "type_finding_missing_map_type": 1,
    }
    assert result["type_advisories"][0]["type_advisory_index"] == 0
    assert result["type_advisories"][0]["observed_column"]["iri"] == status_column
    assert result["type_advisories"][0]["observed_physical_type"]["iri"] == (
        RC + "Varchar"
    )
    assert result["type_advisories"][0]["current_physical_type"] is None
    assert result["type_advisories"][0]["related_recommendation_indexes"] == []
    assert result["type_advisories"][0]["related_recommendation_kinds"] == []
    assert result["type_advisories"][0]["routing_note"].startswith(
        "Inspect current map context"
    )
    assert result["type_advisories"][0]["suggested_next_actions"][0][
        "tool_name"
    ] == "describe_context_slice"


def test_draft_profile_map_updates_tool_surfaces_scalar_conflict_review_lane(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/profile-conflict#Invoices"
    shared_evidence = "https://example.test/profile-conflict#InvoicesProfileEvidence"

    db.record_map_dataset(
        table,
        label="Invoices",
        is_table=True,
        row_count_snapshot=100,
    )
    for index, row_count in enumerate((120, 121)):
        record_profile_bundle_tool(
            db,
            dataset_iri=table,
            dataset_summary=f"Invoices full profile pass {index}.",
            evidence_summary="Invoices full profile evidence.",
            evidence_sources=[f"test://invoices/full/{index}"],
            shared_evidence_iri=shared_evidence,
            sample_size=row_count,
            sample_scope="All rows in the Invoices table.",
            sample_method="DuckDB full-table profile.",
            row_count=row_count,
            update_map_snapshot=False,
            column_defaults={"update_map_column": False},
        )

    result = draft_profile_map_updates_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
    )

    assert result["suggested_next_actions"] == []
    assert list(result["suggested_next_action_groups"]) == [
        "profile_scalar_conflict_review"
    ]
    conflict_actions = result["suggested_next_action_groups"][
        "profile_scalar_conflict_review"
    ]
    assert [action["tool_name"] for action in conflict_actions] == [
        "stage_profile_map_updates",
        "stage_profile_map_updates",
    ]
    assert result["suggested_next_call_groups"]["profile_scalar_conflict_review"] == [
        action["call"] for action in conflict_actions
    ]
    assert len(
        {
            action["source_scalar_conflict"]["route_step_key"]
            for action in conflict_actions
        }
    ) == len(conflict_actions)
    actions_by_value = {
        action["source_scalar_conflict"]["observed_value"]: action
        for action in conflict_actions
    }
    assert set(actions_by_value) == {120, 121}
    source = actions_by_value[120]["source_scalar_conflict"]
    assert source["review_lane"] == "profile_scalar_conflict_review"
    assert source["route_group_key"].startswith("profile_scalar_conflict_review:")
    assert source["route_step_key"].startswith("profile-route-step:")
    assert (
        source["selection_rule"]
        == "choose_at_most_one_option_per_conflict_group"
    )
    assert source["conflict_group_index"] == 0
    assert source["kind"] == "dataset_row_count_snapshot"
    assert source["resource_iri"] == table
    assert source["current_value"] == 100
    assert source["recommendation_indexes"] == [
        source["representative_recommendation_index"]
    ]
    assert source["duplicate_recommendation_indexes"] == (
        source["recommendation_indexes"]
    )
    assert actions_by_value[120]["arguments"] == {
        "dataset_iri": table,
        "evidence_iri": shared_evidence,
        "accepted_recommendation_indexes": [
            source["representative_recommendation_index"]
        ],
    }
    assert result["scalar_conflict_group_count"] == 1
    assert result["scalar_conflict_groups"][0]["option_count"] == 2


def test_draft_profile_map_updates_tool_routes_query_blockers_first(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/profile-query#"
    table = f"{base}Tickets"
    status_column = f"{base}TicketsStatus"
    risk_column = f"{base}TicketsRiskScore"
    shared_evidence = f"{base}TicketsProfileEvidence"

    db.record_map_dataset(
        table,
        label="Tickets",
        is_table=True,
        row_count_snapshot=1000,
        path_templates=["tickets/date={date}/*.parquet"],
    )
    db.record_map_physical_layout(
        f"{base}TicketsParquetLayout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
        datasets=[table],
    )
    db.record_map_column(
        status_column,
        table_iri=table,
        column_name="status",
    )
    for index, (row_count, status_null_count) in enumerate(
        (
            (1200, 0),
            (1210, 12),
        )
    ):
        column_profiles = [
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status nullability came from the full profile.",
                "null_count": status_null_count,
            }
        ]
        if index == 0:
            column_profiles.append(
                {
                    "column_iri": risk_column,
                    "column_name": "risk_score",
                    "summary": "Risk score was observed but is unmapped.",
                    "null_count": 0,
                }
            )
        record_profile_bundle_tool(
            db,
            dataset_iri=table,
            dataset_summary=f"Tickets full profile pass {index}.",
            evidence_summary="Tickets full profile evidence.",
            evidence_sources=[f"test://tickets/full/{index}"],
            shared_evidence_iri=shared_evidence,
            sample_size=row_count,
            sample_scope="All rows in the Tickets table.",
            sample_method="DuckDB full-table profile.",
            row_count=row_count,
            update_map_snapshot=False,
            column_defaults={"update_map_column": False},
            column_profiles=column_profiles,
        )

    result = draft_profile_map_updates_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
    )

    assert list(result["suggested_next_action_groups"]) == [
        "query_context_review",
        "profile_map_updates",
        "profile_scalar_conflict_review",
    ]
    query_action = result["suggested_next_action_groups"][
        "query_context_review"
    ][0]
    assert query_action["tool_name"] == "describe_query_context"
    assert query_action["arguments"] == {"iri": table}
    assert query_action["source_query_context"]["readiness"] == (
        "insufficient_metadata"
    )
    assert query_action["source_query_context"]["blocking_issue_codes"] == [
        "missing_storage_access"
    ]
    assert query_action["source_query_context"]["evidence_iri"] == (
        shared_evidence
    )
    assert query_action["source_query_context"]["profile_evidence_iri"] == (
        shared_evidence
    )
    assert query_action["source_query_context"]["route_anchor_iris"] == [table]
    assert query_action["source_query_context"]["route_group_key"].startswith(
        "query_context_review:"
    )
    assert query_action["source_query_context"]["route_step_key"].startswith(
        "profile-route-step:"
    )
    assert query_action == result["suggested_next_actions"][0]
    assert result["suggested_next_actions"][1]["tool_name"] == (
        "stage_profile_map_updates"
    )
    assert result["suggested_next_actions"][1]["arguments"][
        "accepted_recommendation_indexes"
    ] == [4]
    assert "query_context_review" in result["review_note"]


def test_draft_profile_map_updates_tool_omits_undefined_value_type_seed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    value_type = "https://example.test/project#StatusCodeValue"
    shared_evidence = "https://example.test/project#OrdersProfileRunEvidence"

    record_map_dataset_tool(db, table, label="Orders", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=table,
        column_name="status",
        physical_type="rc:Varchar",
    )
    record_profile_bundle_tool(
        db,
        dataset_iri=table,
        dataset_summary="Orders were profiled with a project value type finding.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=shared_evidence,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status looked integer-coded in the profile.",
                "physical_type": "rc:Integer",
                "value_type": value_type,
            }
        ],
    )

    result = draft_profile_map_updates_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
    )
    advisory = result["type_advisories"][0]
    context_action = advisory["suggested_next_actions"][0]
    value_type_action = [
        action
        for action in advisory["suggested_next_actions"]
        if action["tool_name"] == "stage_map_assertion_change"
        and action["arguments"]["predicate"] == "rc:valueType"
    ][0]

    assert context_action["tool_name"] == "describe_context_slice"
    assert value_type not in context_action["arguments"]["seed_iris"]
    assert context_action["arguments"]["seed_iris"] == [
        advisory["profile_observation_iri"],
        status_column,
        RC + "Integer",
    ]
    context = describe_context_slice_tool(db, **context_action["arguments"])
    assert status_column in {resource["iri"] for resource in context["resources"]}
    assert value_type_action["arguments"]["object"] == value_type


def test_draft_profile_map_updates_tool_routes_metric_promotion_pattern(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Orders"
    shared_evidence = "https://example.test/project#OrdersProfileRunEvidence"
    project_metric = "https://example.test/project#CompletenessScore"
    record_map_dataset_tool(
        db,
        table,
        label="Orders",
        is_table=True,
        row_count_snapshot=10,
    )
    bundle = record_profile_bundle_tool(
        db,
        dataset_iri=table,
        dataset_summary="Orders were profiled with a full-table scan.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=shared_evidence,
        row_count=10,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": project_metric,
                "value": "0.90",
                "datatype": "xsd:decimal",
            }
        ],
        column_defaults={"update_map_column": False},
    )
    pattern = record_pattern_tool(
        db,
        summary="Orders completeness score needs vocabulary.",
        pattern_text=(
            "The Orders profile uses a reusable completeness score that needs "
            "a project metric definition before comparison."
        ),
        rationale="The pattern and profile run share one evidence resource.",
        pattern_targets=[table],
        supporting_observations=(
            bundle["handoff_entrypoints"]["profile_observation_iris"]
        ),
        evidence_iri=shared_evidence,
        map_implications=[project_metric],
    )

    result = draft_profile_map_updates_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
    )

    assert result["recommendation_count"] == 0
    advisory = result["metric_advisories"][0]
    assert advisory["promotion_pattern_count"] == 1
    assert [item["iri"] for item in advisory["promotion_patterns"]] == [
        pattern["pattern_iri"]
    ]
    assert advisory["context_pattern_count"] == 0
    assert advisory["context_patterns"] == []
    assert [action["tool_name"] for action in advisory["suggested_next_actions"]] == [
        "describe_context_slice",
        "list_entities",
        "describe_pattern",
        "stage_pattern_promotion",
    ]
    promotion_action = advisory["suggested_next_actions"][3]
    promotion_args = promotion_action["arguments"]
    assert promotion_args["patterns"] == [pattern["pattern_iri"]]
    assert promotion_args["evidence"] == [shared_evidence]
    assert promotion_args["anchors"] == [project_metric]
    framing_content = promotion_args["framings"][0]["content"]
    assert "rc:ProfileMetricKind" in framing_content
    assert "reusable completeness score" in framing_content

    promoted = stage_pattern_promotion_tool(db, **promotion_args)

    assert len(promoted["staged_revisions"]) == 1
    assert promoted["staged_revisions"][0]["validation_conforms"] is True
    rerun = draft_profile_map_updates_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
    )
    rerun_advisory = rerun["metric_advisories"][0]
    staged_iri = promoted["staged_revisions"][0]["revision_iri"]
    assert rerun_advisory["pending_staged_promotion_iris"] == [staged_iri]
    assert rerun_advisory["pending_staged_promotion_count"] == 1
    assert [
        action["tool_name"] for action in rerun_advisory["suggested_next_actions"]
    ] == [
        "describe_context_slice",
        "list_entities",
        "describe_pattern",
        "describe_staged_revision",
        "export_staged_revisions",
    ]
    assert not any(
        action["tool_name"] == "stage_pattern_promotion"
        for action in rerun_advisory["suggested_next_actions"]
    )
    export_action = next(
        action
        for action in rerun["suggested_next_action_groups"][
            "metric_vocabulary_review"
        ]
        if action["tool_name"] == "export_staged_revisions"
    )
    assert export_action["source_profile_advisory"][
        "pending_staged_promotion_iris"
    ] == [staged_iri]


def test_draft_profile_map_updates_tool_serializes_mixed_support_cue(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    value_type = "https://example.test/project#StatusCodeValue"
    project_metric = "https://example.test/project#StatusCompletenessScore"
    shared_evidence = "https://example.test/project#OrdersProfileRunEvidence"

    record_map_dataset_tool(db, table, label="Orders", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=table,
        column_name="status",
        physical_type="rc:Varchar",
    )
    bundle = record_profile_bundle_tool(
        db,
        dataset_iri=table,
        dataset_summary="Orders were profiled with shared review evidence.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=shared_evidence,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": project_metric,
                "value": "0.91",
                "datatype": "xsd:decimal",
            }
        ],
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status has a project value type.",
                "physical_type": "rc:Varchar",
                "value_type": value_type,
            }
        ],
    )
    pattern = record_pattern_tool(
        db,
        summary="Status profile needs metric and value type vocabulary.",
        pattern_text=(
            "StatusCompletenessScore measures populated status values, while "
            "StatusCodeValue names the reviewed status domain."
        ),
        rationale="The same profile evidence supports both review lanes.",
        pattern_targets=[project_metric, value_type],
        supporting_observations=(
            bundle["handoff_entrypoints"]["profile_observation_iris"]
        ),
        evidence_iri=shared_evidence,
        map_implications=[project_metric, value_type],
    )

    result = draft_profile_map_updates_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
    )

    metric_advisory = result["metric_advisories"][0]
    type_advisory = result["type_advisories"][0]
    assert [item["iri"] for item in metric_advisory["mixed_support_patterns"]] == [
        pattern["pattern_iri"]
    ]
    assert [item["iri"] for item in type_advisory["mixed_support_patterns"]] == [
        pattern["pattern_iri"]
    ]
    assert metric_advisory["mixed_support_pattern_count"] == 1
    assert type_advisory["mixed_support_pattern_count"] == 1
    grouped_metric_action = [
        action
        for action in result["suggested_next_action_groups"][
            "metric_vocabulary_review"
        ]
        if action["tool_name"] == "stage_pattern_promotion"
    ][0]
    grouped_type_action = [
        action
        for action in result["suggested_next_action_groups"]["profile_type_review"]
        if action["tool_name"] == "stage_map_assertion_change"
        and action["arguments"]["predicate"] == "rc:valueType"
    ][0]
    assert grouped_metric_action["source_profile_advisory"]["mixed_support"][
        "pattern_iris"
    ] == [pattern["pattern_iri"]]
    assert grouped_type_action["source_profile_advisory"]["mixed_support"][
        "pattern_iris"
    ] == [pattern["pattern_iri"]]
    assert "Mixed support" in grouped_metric_action["reason"]
    assert "Mixed support" in grouped_type_action["arguments"]["review_note"]


def test_stage_profile_map_updates_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    shared_evidence = "https://example.test/project#OrdersProfileRunEvidence"

    db.record_map_dataset(table, label="Orders", is_table=True, row_count_snapshot=8)
    db.record_map_column(
        status_column,
        table_iri=table,
        column_name="status",
        nullable=False,
    )
    record_profile_bundle_tool(
        db,
        dataset_iri=table,
        dataset_summary="Orders were profiled with a full-table scan.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=shared_evidence,
        sample_size=10,
        sample_scope="All rows in the Orders table.",
        sample_method="DuckDB full-table profile.",
        row_count=10,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status had nulls in the full scan.",
                "null_count": 1,
                "physical_type": "rc:Varchar",
            }
        ],
    )
    claim = record_claim_observation_tool(
        db,
        summary="Orders profile support claim.",
        claim_text="The profile run supports updating the Orders map facts.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=[table, status_column],
        evidence_sources=["test://orders-profile-support-claim"],
    )
    pattern = record_pattern_tool(
        db,
        summary="Orders profile support pattern.",
        pattern_text="Full profile runs can support grouped map update staging.",
        rationale="The claim and profile target the same Orders map resources.",
        pattern_targets=[table],
        supporting_claims=[claim["claim_iri"]],
    )
    extra_anchor = "https://example.test/project#OrdersProfileReview"

    result = stage_profile_map_updates_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
        accepted_recommendation_indexes=[0, 1],
        supporting_claims=[claim["claim_iri"]],
        supporting_patterns=[pattern["pattern_iri"]],
        revision_anchors=[extra_anchor, table],
    )

    assert result["dataset"]["iri"] == table
    assert result["result_kind"] == "profile_map_update_staging"
    assert result["accepted_recommendation_indexes"] == [0, 1]
    assert result["staged_recommendation_indexes"] == [0, 1]
    assert result["skipped_recommendation_indexes"] == []
    assert result["status_counts"] == {
        "staged": 2,
        "skipped": 0,
        "not_selected": 0,
    }
    assert [item["status"] for item in result["items"]] == ["staged", "staged"]
    assert [
        item["supporting_profile_observation_iris"]
        for item in result["items"]
    ] == [[item["profile_observation_iri"]] for item in result["items"]]
    assert result["staged_revision"]["changed_graphs"] == ["map"]
    assert result["staged_revision"]["validation_conforms"] is True
    assert result["metric_advisory_count"] == 0
    assert result["metric_advisory_status_counts"] == {}
    assert result["metric_advisories"] == []
    assert result["metric_vocabulary_review_required"] is False
    assert result["metric_advisory_suggested_next_actions"] == []
    assert result["metric_advisory_suggested_next_calls"] == []
    assert result["type_advisory_count"] == 1
    assert result["type_advisory_status_counts"] == {
        "type_finding_missing_map_type": 1,
    }
    assert result["type_advisories"][0]["observed_column"]["iri"] == (
        status_column
    )
    assert result["type_advisories"][0]["observed_physical_type"]["iri"] == (
        RC + "Varchar"
    )
    assert result["type_review_required"] is True
    assert [
        action["tool_name"]
        for action in result["type_advisory_suggested_next_actions"]
    ] == [
        "describe_context_slice",
        "record_pattern",
        "stage_map_assertion_change",
    ]
    assert result["type_advisory_suggested_next_calls"] == [
        action["call"] for action in result["type_advisory_suggested_next_actions"]
    ]
    assert result["suggested_next_actions"][0]["tool_name"] == (
        "check_staged_revision_apply"
    )
    assert result["suggested_next_actions"][0]["mcp_tool_name"] == (
        "doxabase.check_staged_revision_apply"
    )
    assert result["suggested_next_actions"][0]["arguments"] == {
        "iri": result["staged_revision"]["revision_iri"]
    }
    assert result["suggested_next_actions"][1]["tool_name"] == (
        "export_profile_insight_review_bundle"
    )
    assert result["suggested_next_actions"][1]["mcp_tool_name"] == (
        "doxabase.export_profile_insight_review_bundle"
    )
    assert result["suggested_next_actions"][1]["arguments"]["dataset_iri"] == (
        table
    )
    assert result["suggested_next_actions"][1]["arguments"]["evidence_iri"] == (
        shared_evidence
    )
    assert result["suggested_next_actions"][1]["arguments"]["revision_iris"] == [
        result["staged_revision"]["revision_iri"]
    ]
    assert result["suggested_next_actions"][1]["arguments"]["overwrite"] is True
    assert result["suggested_next_actions"][1]["arguments"]["path"].startswith(
        "/tmp/profile-insight-review-"
    )
    assert result["suggested_next_calls"] == [
        action["call"] for action in result["suggested_next_actions"]
    ]
    described = describe_staged_revision_tool(
        db,
        result["staged_revision"]["revision_iri"],
    )
    assert [item["iri"] for item in described["supporting_claims"]] == [
        claim["claim_iri"]
    ]
    assert [item["iri"] for item in described["supporting_patterns"]] == [
        pattern["pattern_iri"]
    ]
    assert {anchor["iri"] for anchor in described["revision_anchors"]} == {
        extra_anchor,
        table,
        status_column,
    }
    assert db.describe_dataset(table).row_count_snapshot == 8


def test_export_profile_insight_review_bundle_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Orders"
    shared_evidence = "https://example.test/project#OrdersProfileRunEvidence"

    record_map_dataset_tool(
        db,
        table,
        label="Orders",
        is_table=True,
        row_count_snapshot=8,
    )
    record_profile_bundle_tool(
        db,
        dataset_iri=table,
        dataset_summary="Orders were profiled with a full-table scan.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=shared_evidence,
        sample_size=10,
        sample_scope="All rows in the Orders table.",
        sample_method="DuckDB full-table profile.",
        row_count=10,
        update_map_snapshot=False,
    )
    staged = stage_profile_map_updates_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
        accepted_recommendation_indexes=[0],
    )

    export_path = tmp_path / "orders-profile-review.md"
    result = export_profile_insight_review_bundle_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
        path=str(export_path),
    )

    assert result["result_kind"] == "profile_insight_review_bundle"
    assert result["dataset"]["iri"] == table
    assert result["evidence_iri"] == shared_evidence
    assert result["candidate_revision_iris"] == [
        staged["staged_revision"]["revision_iri"]
    ]
    assert result["candidate_count"] == 1
    assert result["candidates"][0]["profile_route_keys"]
    assert result["candidates"][0]["profile_route_groups"][0][
        "review_lane"
    ] == "profile_map_updates"
    assert result["candidates"][0]["profile_route_groups"][0][
        "match_strength"
    ] == "direct_action"
    assert result["open_profile_review_lanes"] == []
    assert result["open_profile_review_lane_count"] == 0
    assert result["export"]["path"] == str(export_path)
    assert result["export"]["revision_iris"] == result["candidate_revision_iris"]
    assert result["candidates"][0]["relation_reasons"]
    assert export_path.exists()
    exported = export_path.read_text(encoding="utf-8")
    assert "Profile insight review: Orders" in exported
    assert "### Profile Route Bridge" in exported
    assert (
        "| Row | Candidate | Revision | Profile route keys | Review lanes | Matched by |"
        in exported
    )
    assert f"| 1 | {result['candidates'][0]['summary']} |" in exported
    assert f"## Revision 1: {result['candidates'][0]['summary']}" in exported
    assert "profile_map_updates (direct_action)" in exported
    profile_map_route_key = result["candidates"][0]["profile_route_keys"][0]
    assert profile_map_route_key in exported

    apply_staged_revision_tool(
        db,
        iri=staged["staged_revision"]["revision_iri"],
    )
    post_apply = export_profile_insight_review_bundle_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
        path=str(tmp_path / "orders-profile-post-apply-review.md"),
    )
    assert post_apply["candidate_revision_iris"] == [
        staged["staged_revision"]["revision_iri"]
    ]
    assert post_apply["export"]["bundle_summary"][
        "recommended_applied_inspection_iris"
    ] == [staged["staged_revision"]["revision_iri"]]
    applied_candidate = post_apply["candidates"][0]
    assert profile_map_route_key in applied_candidate["profile_route_keys"]
    route_groups_by_lane = {
        group["review_lane"]: group for group in applied_candidate["profile_route_groups"]
    }
    assert route_groups_by_lane["profile_map_updates"]["match_strength"] == (
        "direct_action"
    )
    current_only = export_profile_insight_review_bundle_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
        path=str(tmp_path / "orders-profile-current-only-review.md"),
        include_applied_staged_sources=False,
    )
    assert current_only["candidate_revision_iris"] == []
    assert current_only["export"] is None


def test_export_profile_insight_review_bundle_tool_lists_open_profile_lanes(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/profile-review-lanes#"
    table = f"{base}Orders"
    status_column = f"{base}OrdersStatus"
    shared_evidence = f"{base}ProfileEvidence"
    project_metric = f"{base}CompletenessScore"
    value_type = f"{base}StatusCodeValue"

    db.record_map_dataset(
        table,
        label="Orders",
        is_table=True,
        row_count_snapshot=100,
    )
    db.record_map_column(
        status_column,
        table_iri=table,
        column_name="status",
        nullable=False,
        physical_type="rc:Varchar",
    )
    latest_bundle = None
    for index, row_count in enumerate((120, 121)):
        latest_bundle = record_profile_bundle_tool(
            db,
            dataset_iri=table,
            dataset_summary=f"Orders profile pass {index}.",
            evidence_summary="Orders shared profile evidence.",
            evidence_sources=[f"test://orders-profile/{index}"],
            shared_evidence_iri=shared_evidence,
            sample_size=row_count,
            sample_scope="All rows in Orders.",
            sample_method="DuckDB full-table profile.",
            row_count=row_count,
            update_map_snapshot=False,
            profile_metrics=[
                {
                    "metric": project_metric,
                    "target": table,
                    "value": "0.91",
                    "datatype": "xsd:decimal",
                }
            ]
            if index == 0
            else None,
            column_defaults={"update_map_column": False},
            column_profiles=[
                {
                    "column_iri": status_column,
                    "column_name": "status",
                    "summary": "Status had nulls and a value type.",
                    "null_count": 1,
                    "physical_type": "rc:Varchar",
                    "value_type": value_type,
                }
            ]
            if index == 0
            else [],
        )
    assert latest_bundle is not None
    record_pattern_tool(
        db,
        summary="Orders profile needs metric and value type vocabulary.",
        pattern_text="CompletenessScore and StatusCodeValue need review.",
        rationale="The profile evidence supports both review lanes.",
        pattern_targets=[project_metric, value_type],
        supporting_observations=(
            latest_bundle["handoff_entrypoints"]["profile_observation_iris"]
        ),
        evidence_iri=shared_evidence,
        map_implications=[project_metric, value_type],
    )
    draft = draft_profile_map_updates_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
    )
    nullable_indexes = [
        recommendation["recommendation_index"]
        for recommendation in draft["recommendations"]
        if recommendation["kind"] == "column_nullable"
    ]
    assert nullable_indexes == [2]
    staged = stage_profile_map_updates_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
        accepted_recommendation_indexes=nullable_indexes,
    )

    export_path = tmp_path / "orders-profile-review-lanes.md"
    result = export_profile_insight_review_bundle_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
        path=str(export_path),
    )

    staged_iri = staged["staged_revision"]["revision_iri"]
    assert result["candidate_revision_iris"] == [staged_iri]
    assert result["open_profile_review_lane_count"] == 3
    open_lanes = {
        lane["review_lane"]: lane for lane in result["open_profile_review_lanes"]
    }
    assert set(open_lanes) == {
        "profile_scalar_conflict_review",
        "metric_vocabulary_review",
        "profile_type_review",
    }
    assert open_lanes["profile_scalar_conflict_review"][
        "route_group_count"
    ] == 1
    assert open_lanes["profile_scalar_conflict_review"]["action_count"] == 2
    assert open_lanes["profile_scalar_conflict_review"][
        "matched_candidate_revision_iris"
    ] == []
    assert open_lanes["metric_vocabulary_review"][
        "matched_candidate_revision_iris"
    ] == [staged_iri]
    assert open_lanes["profile_type_review"][
        "matched_candidate_revision_iris"
    ] == [staged_iri]
    assert all(lane["route_step_keys"] for lane in open_lanes.values())

    candidate_groups = {
        group["review_lane"]: group
        for group in result["candidates"][0]["profile_route_groups"]
    }
    assert candidate_groups["profile_map_updates"]["match_strength"] == (
        "direct_action"
    )
    assert candidate_groups["profile_type_review"]["match_strength"] == (
        "strong_support"
    )
    assert candidate_groups["metric_vocabulary_review"]["match_strength"] == (
        "related_support"
    )
    assert "expected scalar conflict" in result["review_note"]

    exported = export_path.read_text(encoding="utf-8")
    assert "### Open Profile Review Lanes" in exported
    assert "### Profile Route Bridge" in exported
    open_section = exported.split("### Open Profile Review Lanes", 1)[1].split(
        "### Profile Route Bridge",
        1,
    )[0]
    assert "| profile_scalar_conflict_review | 1 | 2 | none |" in open_section
    assert "metric_vocabulary_review" in open_section
    assert "profile_type_review" in open_section
    assert "profile_map_updates" not in open_section


def test_stage_profile_map_updates_tool_marks_rerun_precondition(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Orders"
    channel_column = "https://example.test/project#OrdersChannel"
    shared_evidence = "https://example.test/project#OrdersProfileRunEvidence"

    db.record_map_dataset(table, label="Orders", is_table=True)
    record_profile_bundle_tool(
        db,
        dataset_iri=table,
        dataset_summary="Orders were profiled without changing the map.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=shared_evidence,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": channel_column,
                "column_name": "channel",
                "summary": "Channel was observed before the map had a shell.",
            }
        ],
    )

    result = stage_profile_map_updates_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
        accepted_recommendation_indexes=[0],
    )

    assert [action["tool_name"] for action in result["suggested_next_actions"]] == [
        "check_staged_revision_apply",
        "export_profile_insight_review_bundle",
        "draft_profile_map_updates",
    ]
    rerun_action = result["suggested_next_actions"][2]
    assert rerun_action["preconditions"]["staged_revision_applied"] == (
        result["staged_revision"]["revision_iri"]
    )
    assert "reviewed and applied" in rerun_action["preconditions"]["why"]


def test_describe_dataset_tool_returns_unmapped_column_profiles(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Orders"
    column = "https://example.test/project#OrdersStatus"
    record_map_dataset_tool(db, table, label="Orders", is_table=True)

    result = record_column_profile_tool(
        db,
        column_iri=column,
        column_name="status",
        table_iri=table,
        summary="MCP helper recorded an unmapped sampled column profile.",
        evidence_summary="Synthetic sampled profile evidence.",
        evidence_sources=["tests/test_mcp_tools.py"],
        sample_size=25,
        sample_scope="Twenty-five sampled Orders rows.",
        sample_method="Top-N sampled value-frequency query.",
        null_count=0,
        distinct_count=3,
        value_frequencies=[
            {"value": "fulfilled", "frequency": 18},
            {"value": "pending", "frequency": 4},
        ],
        update_map_column=False,
    )

    dataset = describe_dataset_tool(db, table)

    assert dataset["columns"] == []
    assert dataset["profile_observations"] == []
    assert dataset["profile_summary"]["returned_unmapped_column_profile_count"] == 1
    assert dataset["profile_summary"]["returned_profile_count"] == 1
    profiles = dataset["unmapped_column_profile_observations"]
    assert len(profiles) == 1
    assert profiles[0]["iri"] == result["observation"]["observation_iri"]
    assert profiles[0]["observed_column"]["iri"] == column
    assert profiles[0]["observed_column_name"] == "status"
    assert profiles[0]["observed_column"]["column_name"] == "status"
    assert profiles[0]["sample_method"] == "Top-N sampled value-frequency query."
    assert [
        (item["value"], item["frequency"])
        for item in profiles[0]["value_frequencies"]
    ] == [("fulfilled", 18), ("pending", 4)]
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_record_claim_observation_tool_and_resource_context(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    result = record_claim_observation_tool(
        db,
        summary="MCP helper wrote a structured claim observation.",
        claim_text="The embeddings output joins to eml_messages by doc_id.",
        claim_kind="rc:JoinClaim",
        claim_targets=[
            "https://example.test/enron#eml_embeddings_body_top_doc_id",
            "https://example.test/enron#eml_messages_doc_id",
        ],
        evidence_summary="README embeddings section.",
        source_path="/home/james/github.com/jamtho/enron-emails/README.md",
        source_section="Embeddings",
        source_kind="rc:DocumentationSource",
        confidence="rc:HighConfidence",
        observation_status="rc:Checked",
    )
    claims = list_entities_tool(
        db,
        type="rc:Claim",
        graph="observations",
        text="doc_id",
    )
    context = describe_resource_tool(
        db,
        iri=result["claim_iri"],
        graph="observations",
    )

    assert result["claim_iri"] in {claim["iri"] for claim in claims["entities"]}
    assert context["label"] == "The embeddings output joins to eml_messages by doc_id."
    assert any(
        triple["predicate"] == "https://richcanopy.org/ns/rc#claimKind"
        for triple in context["outgoing"]
    )
    assert context["outgoing_total_count"] >= context["outgoing_returned_count"]
    assert context["incoming_total_count"] >= context["incoming_returned_count"]
    assert context["outgoing_offset"] == 0
    assert context["incoming_offset"] == 0
    assert context["blank_node_triples"] == []
    assert context["blank_node_depth_exhausted"] is False
    assert context["blank_node_unvisited_count"] == 0
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_describe_assertion_support_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:Messages a rc:Dataset ;
            rc:hasColumn ex:message_id .

        ex:message_id a rc:Column ;
            rc:columnName "message_id" .
        """,
        graph="map",
    )

    result = describe_assertion_support_tool(
        db,
        subject="https://example.test/project#Messages",
        predicate="rc:hasColumn",
        object="https://example.test/project#message_id",
    )

    assert result["assertion_present"] is True
    assert result["matching_triples"][0]["object"] == (
        "https://example.test/project#message_id"
    )
    assert result["same_subject_predicate_triples"][0]["object"] == (
        "https://example.test/project#message_id"
    )
    assert result["owner_dataset"] is None
    assert result["absence_note"] is None
    assert result["nearby_context_triples"] == []
    assert result["nearby_caveat_links"] == []
    assert result["related_routes"] == []
    assert result["related_route_summaries"] == []
    assert result["suggested_next_actions"][0]["tool_name"] == (
        "describe_context_slice"
    )
    assert result["suggested_next_actions"][0]["mcp_tool_name"] == (
        "doxabase.describe_context_slice"
    )
    assert result["suggested_next_actions"][0]["arguments"]["seed_iris"] == [
        "https://example.test/project#Messages",
        "https://example.test/project#message_id",
    ]
    assert result["requested_object"]["resource"]["column_name"] == "message_id"
    assert "retrieval aid" in result["context_note"]
    assert "same-subject predicate triples" in result["support_scope_note"]


def test_record_claim_reconsideration_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    older = record_claim_observation_tool(
        db,
        summary="Initial MMSI identity hunch.",
        claim_text="MMSI can be treated as the stable vessel identity key.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=["https://example.test/ais#mmsi"],
        evidence_sources=["trial setup"],
    )
    newer = record_claim_observation_tool(
        db,
        summary="MMSI caveat check.",
        claim_text="MMSI is an operational grouping key, not proof of vessel identity.",
        claim_kind="rc:CaveatClaim",
        claim_targets=["https://example.test/ais#mmsi"],
        evidence_sources=["retrieved caveat"],
        observation_status="rc:Checked",
    )

    result = record_claim_reconsideration_tool(
        db,
        newer_claim=newer["claim_iri"],
        older_claim=older["claim_iri"],
        relation="weakens",
        rationale="The retrieved caveat makes the first hunch too strong.",
        evidence_sources=["DoxaBase search(\"MMSI vessel\")"],
        source_path="/tmp/doxabase-search-mmsi-vessel.json",
        source_kind="rc:DoxaBaseAPISource",
    )

    assert result["relation"] == "https://richcanopy.org/ns/rc#Weakening"
    assert result["older_claim_status"] == "https://richcanopy.org/ns/rc#Weakened"
    assert result["evidence_iri"] is not None
    assert result["source_span_iri"] is not None
    context = describe_resource_tool(
        db,
        iri=older["claim_iri"],
        graph="observations",
    )
    assert context["claim"]["lifecycle_summary"] == (
        "Current status: weakened. Later claims reconsider this claim: 1 weakening."
    )
    nested_reconsideration = context["claim"]["incoming_reconsiderations"][0]
    assert nested_reconsideration["evidence"][0]["sources"] == [
        'DoxaBase search("MMSI vessel")'
    ]
    assert nested_reconsideration["evidence"][0]["source_spans"][0]["source_path"] == (
        "/tmp/doxabase-search-mmsi-vessel.json"
    )
    assert nested_reconsideration["evidence"][0]["source_spans"][0]["source_kind"] == (
        "https://richcanopy.org/ns/rc#DoxaBaseAPISource"
    )
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_record_pattern_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    claim = record_claim_observation_tool(
        db,
        summary="MCP helper wrote a claim for pattern support.",
        claim_text="The child table joins to the parent table by parent_doc_id.",
        claim_kind="rc:JoinClaim",
        claim_targets=[
            "https://example.test/enron#eml_attachments_parent_doc_id",
            "https://example.test/enron#eml_messages_doc_id",
        ],
        evidence_summary="README attachments section.",
        source_path="/home/james/github.com/jamtho/enron-emails/README.md",
        source_kind="rc:DocumentationSource",
        confidence="rc:HighConfidence",
        observation_status="rc:Checked",
    )

    result = record_pattern_tool(
        db,
        summary="parent_doc_id behaves as the attachment-to-message join.",
        pattern_text="The structured claim and source docs support parent_doc_id as the join from attachments to messages.",
        rationale="The claim names both join columns, and the source span records where the handoff describes the relationship.",
        pattern_targets=["https://example.test/enron#eml_attachments_parent_doc_id"],
        supporting_claims=[claim["claim_iri"]],
        source_path="/home/james/github.com/jamtho/enron-emails/README.md",
        source_section="Attachments",
        source_kind="rc:DocumentationSource",
        confidence="rc:HighConfidence",
        pattern_status="rc:Checked",
        pattern_stability="rc:RepeatedPattern",
    )
    patterns = list_entities_tool(
        db,
        type="rc:Pattern",
        graph="patterns",
        text="attachment-to-message",
    )
    context = describe_resource_tool(
        db,
        iri=result["pattern_iri"],
        graph="patterns",
    )
    pattern_description = describe_pattern_tool(db, result["pattern_iri"])

    assert result["pattern_iri"] in {pattern["iri"] for pattern in patterns["entities"]}
    assert patterns["entities"][0]["label"] == (
        "parent_doc_id behaves as the attachment-to-message join."
    )
    assert context["label"] == "parent_doc_id behaves as the attachment-to-message join."
    assert any(
        triple["predicate"] == "https://richcanopy.org/ns/rc#supportingClaim"
        for triple in context["outgoing"]
    )
    assert pattern_description["summary"] == (
        "parent_doc_id behaves as the attachment-to-message join."
    )
    assert pattern_description["supporting_claims"][0]["claim_text"] == (
        "The child table joins to the parent table by parent_doc_id."
    )
    assert pattern_description["evidence"][0]["source_spans"][0]["source_section"] == (
        "Attachments"
    )
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_map_authoring_tools_return_json_like_payloads(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/project#"
    table = f"{base}messages"
    column = f"{base}messages__doc_id"
    caveat = f"{base}messages_caveat"
    storage = f"{base}local_access"
    layout = f"{base}parquet_layout"
    partition = f"{base}daily_partition"

    table_result = record_map_dataset_tool(
        db,
        iri=table,
        label="Messages",
        is_table=True,
        path_templates=["data/messages.parquet"],
        layout_verification_status="rc:CandidateLayout",
        layout_verification_note="A plausible test path before query verification.",
    )
    column_result = record_map_column_tool(
        db,
        iri=column,
        table_iri=table,
        column_name="doc_id",
        physical_type="rc:Varchar",
        nullable=False,
    )
    caveat_result = record_map_caveat_tool(
        db,
        iri=caveat,
        description="Message identifiers are source-system identifiers.",
        severity="rc:Minor",
        targets=[table],
    )
    storage_result = record_map_storage_access_tool(
        db,
        iri=storage,
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        storage_root="/tmp/example",
        layout_verification_status="rc:VerifiedByListingLayout",
        layout_verification_note="Confirmed by a local directory listing.",
        datasets=[table],
    )
    layout_result = record_map_physical_layout_tool(
        db,
        iri=layout,
        file_format="rc:Parquet",
        compression_codec="rc:ZstdCompression",
        layout_verification_status="rc:VerifiedByQueryLayout",
        layout_verification_note="A representative read used this file format.",
        datasets=[table],
    )
    partition_result = record_map_partition_scheme_tool(
        db,
        iri=partition,
        partition_columns=[column],
        granularity="rc:Daily",
        path_template="data/messages/dt={date}.parquet",
        redundant_partition_key=column,
        layout_verification_status="rc:CandidateLayout",
        layout_verification_note="Partition path still needs a real object listing.",
        datasets=[table],
    )
    relationship_result = record_map_relationship_tool(
        db,
        iri=f"{base}messages_doc_id_shared",
        relationship_type="shared_identifier",
        identifying_columns=[column, f"{base}other_messages__doc_id"],
    )
    record_pattern_tool(
        db,
        summary="doc_id is the message identity handle.",
        pattern_text="Use doc_id as the message identity handle before joining.",
        rationale="The map marks doc_id as the table column that participates in message identity.",
        pattern_targets=[column, relationship_result["iri"]],
        source_path="tests/test_mcp_tools.py",
        source_kind="rc:DocumentationSource",
    )

    assert table_result["resource_type"] == "https://richcanopy.org/ns/rc#Table"
    assert column_result["resource_type"] == "https://richcanopy.org/ns/rc#Column"
    assert caveat_result["resource_type"] == "https://richcanopy.org/ns/rc#KnownCaveat"
    assert storage_result["resource_type"] == "https://richcanopy.org/ns/rc#StorageAccess"
    assert layout_result["resource_type"] == (
        "https://richcanopy.org/ns/rc#PhysicalLayout"
    )
    assert partition_result["resource_type"] == (
        "https://richcanopy.org/ns/rc#PartitionScheme"
    )
    assert relationship_result["resource_type"] == (
        "https://richcanopy.org/ns/rc#SharedIdentifier"
    )
    description = describe_dataset_tool(db, iri=table)
    assert description["label"] == "Messages"
    assert description["layout_verification_status"]["iri"] == (
        "https://richcanopy.org/ns/rc#CandidateLayout"
    )
    assert description["layout_verification_note"] == (
        "A plausible test path before query verification."
    )
    assert description["storage_accesses"][0]["layout_verification_status"]["iri"] == (
        "https://richcanopy.org/ns/rc#VerifiedByListingLayout"
    )
    assert description["storage_accesses"][0]["layout_verification_note"] == (
        "Confirmed by a local directory listing."
    )
    assert description["physical_layouts"][0]["file_format"]["iri"] == (
        "https://richcanopy.org/ns/rc#Parquet"
    )
    assert description["physical_layouts"][0]["layout_verification_status"]["iri"] == (
        "https://richcanopy.org/ns/rc#VerifiedByQueryLayout"
    )
    assert description["partition_schemes"][0]["path_template"] == (
        "data/messages/dt={date}.parquet"
    )
    assert description["partition_schemes"][0]["layout_verification_status"]["iri"] == (
        "https://richcanopy.org/ns/rc#CandidateLayout"
    )
    linked_pattern_reason = description["linked_pattern_reasons"][0]
    assert linked_pattern_reason["pattern_iri"] == linked_pattern_reason["iri"]
    assert linked_pattern_reason["pattern_text"] == (
        "Use doc_id as the message identity handle before joining."
    )
    assert linked_pattern_reason["match_group_count"] == 2
    assert linked_pattern_reason["raw_match_count"] == 2
    assert linked_pattern_reason["relevance_tier_counts"] == {"direct": 2}
    assert {
        match["matched_resource"]["iri"]: match["match_type"]
        for match in linked_pattern_reason["matches"]
    } == {
        column: "pattern_target",
        relationship_result["iri"]: "pattern_target",
    }
    groups_by_resource = {
        group["matched_resource"]["iri"]: group
        for group in linked_pattern_reason["match_groups"]
    }
    assert groups_by_resource[column]["matched_resource"]["column_name"] == "doc_id"
    assert groups_by_resource[column]["relevance_tier"] == "direct"
    assert groups_by_resource[column]["route_labels"] == ["direct pattern target"]
    relationship_group = groups_by_resource[relationship_result["iri"]]
    assert relationship_group["matched_resource_kind"] == "SharedIdentifier"
    assert relationship_group["matched_resource"]["description"] == (
        "Shared identifier across doc_id, other_messages__doc_id"
    )
    assert validate_graph_tool(db, scope="map")["conforms"] is True


def test_search_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)

    result = search_tool(db, query="Parquet schemas", graph="map", limit=5)

    assert result["query"] == "Parquet schemas"
    assert result["graph"] == "map"
    assert result["limit"] == 5
    assert result["count"] >= 1
    assert any(
        "Parquet schemas are inferred" in match["text"]
        for match in result["matches"]
    )


def test_search_tool_suggests_scoped_retries_for_seed_heavy_unscoped_results(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    record_map_storage_access_tool(
        db,
        iri="https://example.test/project#OnlyStorageAccess",
        label="Only project storage access",
        description="Project storage access fact that should be easy to find.",
        storage_protocol="rc:S3CompatibleStorage",
        location_kind="prefix",
        storage_root="s3://example-project",
    )

    result = search_tool(db, query="storage", limit=5)

    assert result["graph"] is None
    assert result["scope_hint"]["status"] == "seed_heavy_unscoped_results"
    assert result["scope_hint"]["seed_match_count"] > result["scope_hint"][
        "project_match_count"
    ]
    assert result["scope_hint"]["suggested_graphs"] == [
        "map",
        "observations",
        "patterns",
        "evidence",
    ]
    assert result["suggested_next_actions"] == result["scope_hint"][
        "suggested_next_actions"
    ]
    first_action = result["suggested_next_actions"][0]
    assert first_action["tool_name"] == "search"
    assert first_action["mcp_tool_name"] == "doxabase.search"
    assert first_action["arguments"] == {
        "query": "storage",
        "graph": "map",
        "limit": 5,
        "offset": 0,
    }
    assert result["suggested_next_calls"] == result["scope_hint"][
        "suggested_next_calls"
    ]

    scoped = search_tool(db, query="storage", graph="map", limit=5)
    assert scoped["scope_hint"] is None
    assert scoped["suggested_next_actions"] == []
    assert {match["graph"] for match in scoped["matches"]} == {"map"}


def test_fixture_loading_replace_keeps_all_fixtures(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    load_result = load_example_fixtures_tool(db, replace=True)
    tables = list_entities_tool(db, type="rc:Table", graph="map")
    labels = {entity["label"] for entity in tables["entities"]}

    assert load_result["replace"] is True
    assert "AIS Daily Broadcast Positions" in labels
    assert "AIS Daily Vessel Index" in labels
    assert "Gamma Market Snapshots" in labels
    assert "Trade Events" in labels
