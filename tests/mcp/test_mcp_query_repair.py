"""Split from test_mcp_tools.py (distillation Phase 2); tests verbatim."""

from tests.mcp.support_mcp import *  # noqa: F401,F403


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


def test_describe_query_context_tool_suggests_dataset_layout_status_repair(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    warehouse = tmp_path / "warehouse"
    warehouse.mkdir()
    dataset = "https://example.test/project#Orders"
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#orders_local_storage",
        label="Orders local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(warehouse),
        location_kind="directory",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#orders_csv_layout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Orders",
        is_table=True,
        path_templates=["orders/current.csv"],
        storage_accesses=[storage["iri"]],
        physical_layouts=[layout["iri"]],
        layout_verification_status="rc:CandidateLayout",
        layout_verification_note=(
            "Dataset-level status was copied from a manifest candidate before "
            "storage and physical layout were reviewed."
        ),
    )

    result = describe_query_context_tool(db, iri=dataset)

    assert result["query_target_decision"]["status"] == "candidate_needs_review"
    assert result["suggested_repair_action_group_count"] == 1
    repair_group = result["suggested_repair_action_groups"][0]
    assert repair_group["issue_code"] == "layout_needs_verification"
    assert repair_group["issue_resource"]["iri"] == dataset
    assert repair_group["repair_action_type"] == (
        "replace_dataset_layout_verification_status"
    )
    assert repair_group["choice_mode"] == "choose_one"
    assert repair_group["pending_required_extra_arguments"] == ["rationale"]
    assert repair_group["repair_context"][
        "current_layout_verification_status_iri"
    ] == (RC + "CandidateLayout")
    assert repair_group["repair_context"]["verified_storage_access_iris"] == [
        storage["iri"]
    ]
    assert repair_group["repair_context"]["verified_physical_layout_iris"] == [
        layout["iri"]
    ]
    assert len(repair_group["pending_action_options"]) == 2
    listing_option = repair_group["pending_action_options"][0]
    _assert_repair_action_option(
        listing_option,
        action_index=0,
        action_type="replace_dataset_layout_verification_status",
        tool_name="stage_map_assertion_change",
        mcp_tool_name="doxabase.stage_map_assertion_change",
        action_label="Stage dataset layout verified by listing",
        required_extra_arguments=["rationale"],
        placeholder_fields=[],
        reviewed_value_fields=[],
    )
    action = repair_group["actions"][0]
    assert action["arguments"]["subject"] == dataset
    assert action["arguments"]["predicate"] == "rc:layoutVerificationStatus"
    assert action["arguments"]["object"] == "rc:VerifiedByListingLayout"
    assert action["arguments"]["object_kind"] == "iri"
    assert action["arguments"]["change_kind"] == "replace"
    assert action["arguments"]["validation_scope"] == "all"
    assert result["suggested_next_actions"]
    draft_action = result["suggested_next_actions"][0]
    assert draft_action["tool_name"] == "draft_query_plan"
    assert draft_action["unattended_recommended"] is False
    assert "query_repair_groups_present" in (
        draft_action["unattended_review_reason_codes"]
    )
    assert "suggested_repair_action_groups" in draft_action["unattended_caution"]
    assert result.get("unattended_recommended_action_indexes", []) == []
    assert result.get("first_unattended_action_index") is None

    arguments = dict(action["arguments"])
    arguments["rationale"] = "Reviewed the dataset-owned path template by listing."
    staged = stage_map_assertion_change_tool(db, **arguments)
    assert staged["staged_revision"]["validation_conforms"] is True
    applied = apply_staged_revision_tool(db, staged["revision_iri"])
    assert applied["patches_applied"] == 2
    repaired = describe_query_context_tool(db, iri=dataset)
    assert repaired["readiness"] == "ready_for_query_planning"
    assert repaired.get("suggested_repair_action_groups", []) == []


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
    assert repair_group["repair_action_type"] == "record_or_stage_physical_layout"
    assert repair_group["choice_mode"] == "choose_one"
    assert repair_group["repair_context"]["database_storage_present"] is True
    assert repair_group["repair_context"]["storage_protocol_iris"] == [
        RC + "DatabaseStorage"
    ]
    assert "rc:PostgreSQLTable" in repair_group["repair_context"][
        "file_format_guidance"
    ]["rc:DatabaseStorage"]
    assert len(repair_group["pending_action_options"]) == 2
    staged_option = repair_group["pending_action_options"][0]
    _assert_repair_action_option(
        staged_option,
        action_index=0,
        action_type="stage_reviewed_physical_layout",
        tool_name="stage_query_physical_layout_repair",
        mcp_tool_name="doxabase.stage_query_physical_layout_repair",
        action_label="Stage physical layout repair",
        required_extra_arguments=[
            "layout_iri",
            "file_format",
            "rationale",
        ],
        placeholder_fields=[
            "layout_iri",
            "file_format",
            "rationale",
            "layout_verification_status",
            "layout_verification_note",
        ],
        reviewed_value_fields=[
            "layout_iri",
            "file_format",
            "rationale",
            "layout_verification_status",
            "layout_verification_note",
        ],
    )
    assert "staged-revision rationale" in staged_option["reason"]
    layout_option = repair_group["pending_action_options"][1]
    _assert_repair_action_option(
        layout_option,
        action_index=1,
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
    assert result["suggested_next_actions"]
    draft_action = result["suggested_next_actions"][0]
    assert draft_action["tool_name"] == "draft_query_plan"
    assert draft_action["unattended_recommended"] is False
    assert "query_repair_groups_present" in (
        draft_action["unattended_review_reason_codes"]
    )
    assert "suggested_repair_action_groups" in draft_action["unattended_caution"]
    assert result.get("unattended_recommended_action_indexes", []) == []
    assert result.get("first_unattended_action_index") is None
    action = repair_group["actions"][0]
    assert action["tool_name"] == "stage_query_physical_layout_repair"
    assert action["arguments_template"]["dataset_iri"] == dataset
    assert action["arguments_template"]["layout_iri"] == (
        "<reviewed physical layout IRI>"
    )
    assert action["arguments_template"]["file_format"] == (
        "<reviewed rc:FileFormat IRI>"
    )
    direct_action = repair_group["actions"][1]
    assert direct_action["tool_name"] == "record_map_physical_layout"
    assert direct_action["arguments_template"]["datasets"] == [dataset]
    staged = stage_query_physical_layout_repair_tool(
        db,
        dataset_iri=dataset,
        layout_iri="https://example.test/project#warehouse_orders_table_layout",
        file_format="rc:PostgreSQLTable",
        rationale="Reviewed the warehouse relation as a PostgreSQL table layout.",
        layout_verification_status="rc:VerifiedByQueryLayout",
        layout_verification_note="Reviewed from warehouse source metadata.",
    )
    assert staged["validation_conforms"] is True
    assert check_staged_revision_apply_tool(db, staged["revision_iri"])["status"] == (
        "ready"
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
    candidate_selector = context["query_target_candidates"][0]["candidate_selector"]
    assert [action["arguments"] for action in selection_actions] == [
        {
            "iri": dataset,
            "candidate_selector": candidate_selector,
            "physical_layout_iri": parquet_layout["iri"],
        },
    ]
    route_card = selection_actions[0]["route_card"]
    assert route_card["candidate_selector"] == candidate_selector
    assert route_card["physical_layout_iri"] == parquet_layout["iri"]
    assert "ambiguous_physical_layout" in route_card["direct_issue_codes"]
    assert selection_actions[0]["call"].startswith("draft_query_plan(")
    assert automatic["scan"].get("function") is None
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
    assert "ambiguous_physical_layout" not in selected["review_gate"].get(
        "blocking_reason_codes", []
    )
    assert selected["review_gate"]["ready_for_execution_attempt"] is True
    assert selected["handoff_kind"] == "execution_attempt_ready"


def test_query_plan_tool_blocks_cross_route_physical_layout_selection(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    local_storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#events_local_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="directory",
        storage_root=str(tmp_path / "lake"),
        path_templates=["events/current/*.csv"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    database_storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#events_database_storage",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="analytics-prod",
        path_templates=["mart.events"],
        endpoint_profile="warehouse-prod",
        credential_reference="profile:warehouse-readonly",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    csv_layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#events_csv_layout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    table_layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#events_table_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Events",
        is_table=True,
        storage_accesses=[local_storage["iri"], database_storage["iri"]],
        physical_layouts=[csv_layout["iri"], table_layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = describe_query_context_tool(db, iri=dataset)
    local_index = next(
        index
        for index, target in enumerate(context["query_target_candidates"])
        if target["storage_access"]["iri"] == local_storage["iri"]
    )
    database_index = next(
        index
        for index, target in enumerate(context["query_target_candidates"])
        if target["storage_access"]["iri"] == database_storage["iri"]
    )
    local_selector = context["query_target_candidates"][local_index][
        "candidate_selector"
    ]
    database_selector = context["query_target_candidates"][database_index][
        "candidate_selector"
    ]
    selection_actions = [
        action
        for action in context["suggested_next_actions"]
        if action["action_label"] == "Select physical layout for draft"
    ]

    assert {
        (
            action["arguments"]["candidate_selector"],
            action["arguments"]["physical_layout_iri"],
        )
        for action in selection_actions
    } == {
        (local_selector, csv_layout["iri"]),
        (database_selector, table_layout["iri"]),
    }

    database_csv_plan = draft_query_plan_tool(
        db,
        iri=dataset,
        candidate_index=database_index,
        physical_layout_iri=csv_layout["iri"],
    )

    assert database_csv_plan["handoff_kind"] == "metadata_review_required"
    assert database_csv_plan["review_gate"]["blocking_reason_codes"] == [
        "physical_layout_storage_protocol_mismatch"
    ]
    assert database_csv_plan["issues"][-1]["code"] == (
        "physical_layout_storage_protocol_mismatch"
    )
    assert database_csv_plan["issues"][-1]["details"][
        "candidate_storage_route_kind"
    ] == "database"
    assert database_csv_plan["issues"][-1]["details"][
        "physical_layout_route_kind"
    ] == "file"


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
    assert repair_group["action_status_counts"] == {"pending_review": 4}
    assert repair_group["pending_action_count"] == 4
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
    assert "set_reviewed_bucket_name" not in action_by_type
    assert "set_reviewed_key_prefix" not in action_by_type
    assert action_by_type["remove_conflicting_bucket_name"]["arguments"][
        "object"
    ] == "public"

