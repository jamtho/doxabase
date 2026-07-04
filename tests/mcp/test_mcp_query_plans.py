"""Split from test_mcp_tools.py (distillation Phase 2); tests verbatim."""

from tests.mcp.support_mcp import *  # noqa: F401,F403


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


def test_draft_query_evidence_storage_overlay_tool_returns_stale_seed_blocker(
    tmp_path: Path,
) -> None:
    warehouse = tmp_path / "warehouse"
    warehouse.mkdir()
    csv_path = warehouse / "orders.csv"
    csv_path.write_text("order_id,status\n1,paid\n", encoding="utf-8")

    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    record_map_dataset_tool(db, iri=dataset, label="Orders", is_table=True)
    result = record_query_result_tool(
        db,
        summary="Orders query scanned the reviewed local CSV.",
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path=str(tmp_path / "orders_status.sql"),
        query_hash="sha256:mcp-stale-seed-overlay",
        scanned_source_paths=[str(csv_path)],
        row_count=1,
    )
    _delete_base_ontology_seed_terms(
        db,
        ["rc:GraphPatchRole", "rc:FramingPatch", "rc:SharedContextPatch"],
    )

    result_payload = draft_query_evidence_storage_overlay_tool(
        db,
        dataset_iri=dataset,
        evidence_iri=result["evidence_iri"],
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(warehouse),
        location_kind="directory",
        path_templates=["orders.csv"],
        file_format="rc:CSV",
    )

    assert result_payload["result_kind"] == (
        "query_evidence_storage_overlay_blocker"
    )
    assert result_payload["helper"] == "draft_query_evidence_storage_overlay"
    assert result_payload["mode"] == "blocked_stale_seed_recovery_required"
    assert result_payload["missing_seed_terms"] == [
        "rc:GraphPatchRole",
        "rc:FramingPatch",
        "rc:SharedContextPatch",
    ]
    assert result_payload["mutation_allowed_after"] == (
        "stale_seed_recovery_required_before_staging"
    )
    assert "stage_arguments" not in result_payload
    assert result_payload["suggested_next_actions"][0]["tool"] == (
        "doxabase.export_preflight"
    )
    assert result_payload["suggested_next_actions"][0]["args"] == {
        "export_kind": "handoff_bundle",
        "graphs": ["project"],
        "limit": 20,
        "validation_scope": "map",
    }


def test_draft_query_evidence_storage_overlay_tool_accepts_blocked_query_evidence(
    tmp_path: Path,
) -> None:
    warehouse = tmp_path / "warehouse"
    warehouse.mkdir()
    csv_path = warehouse / "orders.csv"
    csv_path.write_text("order_id,status\n1,blocked\n", encoding="utf-8")

    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    result = record_query_result_tool(
        db,
        summary="Orders query was blocked after reviewing the intended CSV route.",
        observed_asset=dataset,
        execution_status="blocked",
        engine="python-csv",
        query_hash="sha256:mcp-orders-blocked",
        failure_summary="Runtime access was not available in this container.",
        scanned_source_paths=[str(csv_path)],
    )
    assert result["failure_summary"] == (
        "Runtime access was not available in this container."
    )

    draft = draft_query_evidence_storage_overlay_tool(
        db,
        dataset_iri=dataset,
        evidence_iri=result["evidence_iri"],
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(warehouse),
        location_kind="directory",
        path_templates=["orders.csv"],
        file_format="rc:CSV",
        layout_verification_status="rc:CandidateLayout",
        layout_verification_note=(
            "Reviewed blocked-query evidence named the intended orders.csv route."
        ),
    )

    assert draft["validation_conforms"] is True
    assert draft.get("profile_observation_iris", []) == []
    assert draft["source_query_evidence"]["execution_status"] == "blocked"
    assert draft["source_query_evidence"]["query_hash"] == (
        "sha256:mcp-orders-blocked"
    )
    assert draft["source_query_evidence"]["scanned_source_paths"] == [str(csv_path)]
    assert draft["source_profile_evidence"] == draft["source_query_evidence"]
    assert draft["reviewed_overlay"]["layout_verification_status"] == (
        RC + "CandidateLayout"
    )
    assert draft["stage_arguments"].get("supporting_observations", []) == []
    assert draft["stage_arguments"]["evidence"] == [result["evidence_iri"]]


def test_draft_query_evidence_storage_overlay_tool_replaces_status(
    tmp_path: Path,
) -> None:
    warehouse = tmp_path / "warehouse"
    warehouse.mkdir()
    csv_path = warehouse / "orders.csv"
    csv_path.write_text("order_id,status\n1,paid\n", encoding="utf-8")
    query_path = tmp_path / "orders_status.sql"
    query_path.write_text("select count(*) from orders;\n", encoding="utf-8")
    result_path = tmp_path / "orders_status.json"
    result_path.write_text('{"row_count": 1}\n', encoding="utf-8")

    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Orders",
        is_table=True,
        layout_verification_status="rc:CandidateLayout",
        layout_verification_note="Candidate note before query review.",
    )
    result = record_query_result_tool(
        db,
        summary="Orders aggregate scanned the reviewed local CSV.",
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path=str(query_path),
        query_hash="sha256:mcp-orders-status-replace",
        result_sources=[str(result_path)],
        sample_size=1,
        sample_scope="All rows in the reviewed Orders CSV.",
        sample_method="External read-only aggregate query.",
        row_count=1,
    )

    draft = draft_query_evidence_storage_overlay_tool(
        db,
        dataset_iri=dataset,
        evidence_iri=result["evidence_iri"],
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(warehouse),
        location_kind="directory",
        path_templates=["orders.csv"],
        file_format="rc:CSV",
        layout_verification_note="Reviewed query evidence scanned orders.csv.",
    )

    assert draft["validation_conforms"] is True
    assert draft["reviewed_overlay"][
        "replaced_dataset_layout_verification_statuses"
    ] == [RC + "CandidateLayout"]
    assert draft["reviewed_overlay"]["replaced_dataset_layout_verification_notes"] == [
        "Candidate note before query review."
    ]
    assert "removals" in draft["stage_arguments"]
    assert "CandidateLayout" in draft["stage_arguments"]["removals"][0]["content"]

    staged = stage_graph_revision_tool(db, **draft["stage_arguments"])
    assert staged["validation_conforms"] is True
    applied = apply_staged_revision_tool(db, staged["revision_iri"])
    assert applied["patches_applied"] == 2
    plan = draft_query_plan_tool(db, iri=dataset)
    assert plan["handoff_kind"] == "execution_attempt_ready"
    assert plan["scan"]["uri_template"] == str(csv_path)


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
    assert result["source_context"].get("ready_candidate_indexes", []) == []
    assert result["source_context"].get("unselected_ready_candidate_indexes", []) == []
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
    assert result["scan"].get("dataset_verification_status") is None
    assert result["scan"].get("dataset_verification_note") is None
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
    assert result["binding_requirements"][0].get("partition_column") is None
    assert result["binding_requirements"][0]["partition_granularity"]["iri"] == (
        "https://richcanopy.org/ns/rc#Daily"
    )
    assert result["binding_requirements"][0].get("candidate_column_matches", []) == []
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
    assert result["binding_requirements"][1].get("candidate_column_matches", []) == []
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
    assert context.get("ready_candidate_indexes", []) == []
    assert context.get("unselected_ready_candidate_indexes", []) == []
    assert context["direct_clean_candidate_indexes"] == [
        context["query_target_decision"]["candidate_index"]
    ]
    assert context.get("unselected_direct_clean_candidate_indexes", []) == []
    query_action = context["suggested_next_actions"][0]
    selected_selector = context["query_target_candidates"][
        context["query_target_decision"]["candidate_index"]
    ]["candidate_selector"]
    assert query_action["tool"] == "doxabase.draft_query_plan"
    assert query_action["args"] == {
        "iri": dataset,
        "candidate_selector": selected_selector,
        "allow_context_blocked_candidate": True,
    }

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
    assert result["source_context"].get("ready_candidate_indexes", []) == []
    assert result["source_context"].get("unselected_ready_candidate_indexes", []) == []
    assert result["source_context"]["direct_clean_candidate_indexes"] == [
        result["source_context"]["selected_candidate_index"]
    ]
    assert result["source_context"].get("unselected_direct_clean_candidate_indexes", []) == []
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
    assert result["review_gate"].get("blocking_reason_codes", []) == []
    assert result["review_gate"]["primary_execution_attempt_blocking_reason_code"] == (
        "binding_values_required"
    )
    assert result["review_gate"]["execution_attempt_blocking_reason_codes"] == [
        "binding_values_required"
    ]
    assert result["handoff_summary"]["context_blocked_candidate_allowed"] is True
    assert result["handoff_summary"]["context_blocked_candidate_used"] is True
    assert result["handoff_summary"].get("direct_blocking_reason_codes", []) == []
    assert result["handoff_summary"]["context_blocking_reason_codes"] == [
        "query_context_has_other_blockers"
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
        if candidate.get("relation_identifier") == "mart.orders"
    )
    archive_candidate_index = next(
        index
        for index, candidate in enumerate(context["query_target_candidates"])
        if candidate.get("relation_identifier") == "mart.orders_archive"
    )
    relation_candidate_selector = context["query_target_candidates"][
        relation_candidate_index
    ]["candidate_selector"]
    archive_candidate_selector = context["query_target_candidates"][
        archive_candidate_index
    ]["candidate_selector"]

    assert context["query_target_decision"]["status"] == "context_blocked"
    assert context.get("ready_candidate_indexes", []) == []
    assert relation_candidate_index in context["direct_clean_candidate_indexes"]
    assert archive_candidate_index in context["unselected_direct_clean_candidate_indexes"]
    assert [
        action["args"]
        for action in context["suggested_next_actions"]
        if action["tool"] == "doxabase.draft_query_plan"
    ] == [
        {
            "iri": dataset,
            "candidate_selector": relation_candidate_selector,
            "allow_context_blocked_candidate": True,
        },
        {
            "iri": dataset,
            "candidate_selector": archive_candidate_selector,
            "allow_context_blocked_candidate": True,
        },
    ]

    result = draft_query_plan_tool(
        db,
        iri=dataset,
        candidate_selector=relation_candidate_selector,
        allow_context_blocked_candidate=True,
    )

    assert result["source_context"]["selection_mode"] == "candidate_selector"
    assert result["source_context"]["selected_candidate_index"] == (
        relation_candidate_index
    )
    assert result["source_context"]["selected_candidate_selector"] == (
        relation_candidate_selector
    )
    assert result["source_context"]["requested_candidate_selector"] == (
        relation_candidate_selector
    )
    assert result["source_context"].get("requested_candidate_index") is None
    assert result["source_context"].get("requested_storage_access_iri") is None
    assert result["source_context"]["allow_context_blocked_candidate"] is True
    assert result["selected_candidate"]["storage_access"]["iri"] == (
        relation_storage.iri
    )
    assert result["selected_candidate"]["relation_identifier"] == "mart.orders"
    assert result["selected_candidate"]["candidate_path_status"] == "ready"
    assert result["selected_candidate"]["review_required"] is False
    assert result["selected_candidate"]["direct_review_required"] is False
    assert result["scan"].get("uri_template") is None
    assert result["scan"]["relation_identifier"] == "mart.orders"
    assert result["scan"]["connection_reference"] == "warehouse-prod"
    assert result["scan"]["composition"] == "database_connection_and_relation"
    assert result["review_gate"]["status"] == "ready"
    assert result["review_gate"]["context_blocked_candidate_used"] is True
    assert result["review_gate"]["context_blocking_reason_codes"] == [
        "query_context_has_other_blockers"
    ]
    assert result["review_gate"].get("blocking_reason_codes", []) == []
    assert result["review_gate"]["execution_attempt_blocking_reason_codes"] == [
        "runtime_resolution_required"
    ]
    assert result["review_gate"]["primary_execution_attempt_blocking_reason_code"] == (
        "runtime_resolution_required"
    )
    assert result["review_gate"]["all_issue_codes"] == [
        "database_relation_template_missing"
    ]
    assert result["handoff_kind"] == "database_relation_handoff"
    assert result["handoff_summary"]["selected_candidate_selector"] == (
        relation_candidate_selector
    )

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
    assert "Pass candidate_selector for a stable selection" in error_message
    assert f"candidate_selector='{relation_candidate_selector}'" in error_message
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
    target = context["query_target_candidates"][0]
    assert target.get("candidate_path") is None
    assert target.get("relation_identifier") is None
    assert target["connection_reference"] == "warehouse-prod"
    assert target["candidate_path_status"] == "unresolved"
    assert target["direct_review_reasons"][0]["code"] == (
        "database_relation_template_source_mismatch"
    )
    assert [action["tool"].removeprefix("doxabase.") for action in context["suggested_next_actions"]] == [
        "draft_query_plan",
    ]
    assert plan["selected_candidate"]["template_source"] == "dataset"
    assert plan["scan"].get("uri_template") is None
    assert plan["scan"].get("relation_identifier") is None
    assert plan["scan"]["connection_reference"] == "warehouse-prod"
    assert plan["review_gate"]["blocking_reason_codes"] == [
        "database_relation_template_source_mismatch"
    ]
    assert plan["handoff_kind"] == "metadata_review_required"
    assert plan["handoff_summary"]["primary_repair_issue_index"] == 0
    assert plan["handoff_summary"]["primary_repair_issue_code"] == (
        "database_relation_template_source_mismatch"
    )
    assert plan["handoff_summary"]["primary_repair_group_action_type"] == (
        "move_database_relation_template_to_storage_access"
    )
    assert plan["handoff_summary"]["primary_repair_action_index"] == 0
    assert plan["handoff_summary"]["primary_repair_action_type"] == (
        "add_reviewed_relation_template"
    )
    assert plan["handoff_summary"]["primary_repair_tool"] == (
        "doxabase.stage_map_assertion_change"
    )
    assert plan["handoff_summary"]["primary_repair_required_extra_arguments"] == [
        "object",
        "rationale",
    ]


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
        assert tool_payload.get("ready_candidate_indexes", []) == python_payload.get(
            "ready_candidate_indexes", []
        )
        assert tool_payload.get(
            "unselected_ready_candidate_indexes", []
        ) == python_payload.get("unselected_ready_candidate_indexes", [])


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
    assert repair_group["action_status_counts"] == {"pending_review": 3}
    assert repair_group["pending_action_count"] == 3
    assert repair_group["skippable_action_count"] == 0
    assert repair_group["already_satisfied_action_count"] == 0
    optional_storage_fields = [
        "endpoint_profile",
        "bucket_name",
        "key_prefix",
        "region",
        "path_style_access",
        "credential_reference",
    ]
    assert repair_group["pending_required_extra_arguments"] == [
        "storage_access_iri",
        "storage_protocol",
        "storage_root",
        "rationale",
        "iri",
        "object",
    ]
    assert len(repair_group["pending_action_options"]) == 3
    staged_storage_option = repair_group["pending_action_options"][0]
    _assert_repair_action_option(
        staged_storage_option,
        action_index=0,
        action_type="stage_reviewed_storage_access",
        tool="doxabase.stage_query_storage_access_repair",
        required_extra_arguments=[
            "storage_access_iri",
            "storage_protocol",
            "storage_root",
            "rationale",
        ],
        placeholder_fields=[
            "storage_access_iri",
            "storage_protocol",
            "storage_root",
            *optional_storage_fields,
            "rationale",
            "location_kind",
            "path_templates",
            "layout_verification_status",
            "layout_verification_note",
        ],
        reviewed_value_fields=[
            "storage_access_iri",
            "storage_protocol",
            "storage_root",
            *optional_storage_fields,
            "rationale",
            "location_kind",
            "path_templates",
            "layout_verification_status",
            "layout_verification_note",
        ],
    )
    assert "staged-revision rationale" in staged_storage_option["reason"]
    storage_option = repair_group["pending_action_options"][1]
    _assert_repair_action_option(
        storage_option,
        action_index=1,
        action_type="record_reviewed_storage_access",
        tool="doxabase.record_map_storage_access",
        required_extra_arguments=[
            "iri",
            "storage_protocol",
            "storage_root",
        ],
        placeholder_fields=[*optional_storage_fields, "path_templates"],
        reviewed_value_fields=[*optional_storage_fields, "path_templates"],
    )
    assert "non-secret storage protocol" in storage_option["reason"]
    assert "Database relation identifiers" in storage_option["condition"]
    assert "record_map_storage_access writes current-best map facts directly" in (
        storage_option["review_rationale_guidance"]
    )
    link_option = repair_group["pending_action_options"][2]
    _assert_repair_action_option(
        link_option,
        action_index=2,
        action_type="stage_existing_storage_access_link",
        tool="doxabase.stage_map_assertion_change",
        required_extra_arguments=["object", "rationale"],
        placeholder_fields=["object"],
        reviewed_value_fields=["object"],
    )
    assert "suitable storage access resource already exists" in link_option["reason"]
    action_by_type = {
        action["action_type"]: action for action in repair_group["actions"]
    }
    assert set(action_by_type) == {
        "stage_reviewed_storage_access",
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
    assert candidate.get("generic_dataset_token_matches", []) == []
    assert candidate.get("dataset_partial_token_matches", []) == []
    assert candidate.get("generic_dataset_partial_token_matches", []) == []
    assert candidate.get("linked_dataset_iris", []) == []
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
    staged_record_action = action_by_type["stage_reviewed_storage_access"]
    assert staged_record_action["arguments_template"]["dataset_iri"] == dataset
    assert staged_record_action["arguments_template"]["storage_access_iri"] == (
        "<reviewed storage access IRI>"
    )
    assert "stage_query_storage_access_repair records a reviewable" in (
        staged_record_action["review_rationale_guidance"]
    )
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

