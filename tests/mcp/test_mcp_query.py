"""Split from test_mcp_tools.py (distillation Phase 2); tests verbatim."""

from tests.mcp.support_mcp import *  # noqa: F401,F403


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
        scanned_source_handles=["warehouse/orders.csv"],
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
    assert result["scanned_source_paths"] == []
    assert result["scanned_source_handles"] == ["warehouse/orders.csv"]
    assert result["scanned_source_span_iris"] == []
    assert result["source_span_triples"] > 0
    assert [action["tool_name"] for action in result["suggested_next_actions"]] == [
        "describe_profile_run",
        "describe_context_slice",
        "describe_query_context",
    ]
    assert result["suggested_next_actions"][0]["arguments"] == {
        "dataset_iri": "https://example.test/project#Orders",
        "evidence_iri": result["evidence_iri"],
    }
    assert result["suggested_next_actions"][1]["arguments"] == {
        "seed_iris": [result["evidence_iri"]],
        "profile": "resource_brief",
    }
    assert result["suggested_next_actions"][2]["arguments"] == {
        "iri": "https://example.test/project#Orders"
    }
    assert result["suggested_next_calls"] == [
        (
            "describe_profile_run("
            "dataset_iri='https://example.test/project#Orders', "
            f"evidence_iri='{result['evidence_iri']}')"
        ),
        (
            "describe_context_slice("
            f"seed_iris=['{result['evidence_iri']}'], profile='resource_brief')"
        ),
        "describe_query_context(iri='https://example.test/project#Orders')",
    ]


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
        scanned_source_paths=[str(csv_path)],
        evidence_summary="Reviewed Python CSV aggregate over scratch Orders.",
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
    assert context["safe_inspection_action_indexes"] == [0]
    assert context["first_safe_inspection_action_index"] == 0
    assert context["unattended_recommended_action_indexes"] == [1]
    assert context["first_unattended_action_index"] == 1
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
    assert source_profile_evidence["scanned_source_paths"] == [str(csv_path)]
    assert source_profile_evidence["scanned_source_handles"] == [str(csv_path)]
    assert source_profile_evidence["result_sources"] == [str(result_path)]
    assert source_profile_evidence["profile_summaries"][0]["summary"] == (
        "Orders paid aggregate scanned the scratch CSV."
    )

    profile_run = describe_profile_run_tool(db, **profile_action["arguments"])
    assert profile_run["returned_profile_count"] == 1
    assert profile_run["evidence"]["summary"] == (
        "Reviewed Python CSV aggregate over scratch Orders."
    )
    assert profile_run["evidence"]["query_execution_status"] == "succeeded"
    assert profile_run["evidence"]["query_engine"] == "python-csv"
    assert profile_run["evidence"]["query_hash"] == "sha256:abc123"
    assert profile_run["evidence"]["sources"] == [str(result_path)]
    assert profile_run["evidence"]["source_spans"][0]["source_path"] == (
        "queries/orders_paid_aggregate.sql"
    )
    assert {
        (span["source_path"], span["source_kind"])
        for span in profile_run["evidence"]["source_spans"]
    } >= {
        (str(csv_path), RC + "DataSampleSource"),
    }


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
    assert result["query_target_candidates"][0]["access_mode"]["iri"] == (
        RC + "ReadOnlyAccess"
    )
    assert result["query_target_candidates"][0]["region"] == "local"
    assert result["query_target_candidates"][0]["required_bindings"] == [
        "year",
        "date",
    ]
    assert result["query_target_candidates"][0]["required_binding_details"][1][
        "partition_column"
    ]["iri"] == "https://richcanopy.org/example/manifest/ais#bc_date"
    assert result["query_target_candidates"][0]["binding_example"] == (
        "year='2026', date='2026-06-30' -> "
        "s3://ais-noaa/broadcasts/2026/ais-2026-06-30.parquet"
    )
    assert result["query_target_candidates"][0]["binding_examples"][1][
        "binding"
    ] == "date"
    assert result["query_target_candidates"][0]["review_required"] is True
    assert result["query_target_candidates"][0]["direct_review_required"] is True
    assert {
        reason["code"]
        for reason in result["query_target_candidates"][0]["direct_review_reasons"]
    } == {
        "layout_needs_verification",
        "verification_status_not_recorded",
    }
    draft_action = next(
        action
        for action in result["suggested_next_actions"]
        if action["tool_name"] == "draft_query_plan"
    )
    route_card = draft_action["route_card"]
    assert route_card["candidate_index"] == 0
    assert route_card["candidate_selector"] == (
        result["query_target_candidates"][0]["candidate_selector"]
    )
    assert route_card["storage_label"] == "AIS local object-store access profile"
    assert route_card["access_mode"]["iri"] == RC + "ReadOnlyAccess"
    assert route_card["storage_root"] == "s3://ais-noaa/"
    assert route_card["endpoint_profile"] == "local-minio"
    assert route_card["bucket_name"] == "ais-noaa"
    assert route_card["region"] == "local"
    assert route_card["credential_reference"] == "profile:ais-readonly"
    assert route_card["path_style_access"] is True
    assert route_card["requires_endpoint_profile"] is True
    assert route_card["required_bindings"] == ["year", "date"]
    assert route_card["binding_example"] == (
        "year='2026', date='2026-06-30' -> "
        "s3://ais-noaa/broadcasts/2026/ais-2026-06-30.parquet"
    )
    assert result["storage_accesses"][0]["endpoint_profile"] == "local-minio"
    assert result["storage_accesses"][0]["access_mode"]["iri"] == (
        RC + "ReadOnlyAccess"
    )
    assert result["storage_accesses"][0]["region"] == "local"
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


def test_describe_query_context_tool_blocks_s3_template_outside_storage_root(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#orders_s3_storage",
        label="Orders S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        storage_root="s3://orders-lake/warehouse",
        path_templates=["s3://other-bucket/orders.csv"],
        endpoint_profile="orders-prod",
        credential_reference="profile:orders-readonly",
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
        storage_accesses=[storage["iri"]],
        physical_layouts=[layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    result = describe_query_context_tool(db, iri=dataset)

    assert result["readiness"] == "needs_review"
    candidate = result["query_target_candidates"][0]
    assert candidate["candidate_path"] == "s3://other-bucket/orders.csv"
    assert candidate["composition"] == "template_as_returned"
    assert candidate["candidate_path_status"] == "orientation_only"
    assert candidate["direct_review_required"] is True
    assert candidate["review_reasons"][0]["code"] == (
        "storage_protocol_location_mismatch"
    )
    assert "outside recorded storage_root" in candidate["review_reasons"][0][
        "details"
    ]["mismatch_reasons"][0]
    action_types = {
        action["action_type"]
        for action in candidate["review_reasons"][0]["details"]["repair_hint"][
            "actions"
        ]
    }
    assert "set_reviewed_bucket_name" in action_types
    assert "set_reviewed_key_prefix" in action_types
    assert result["query_target_decision"]["status"] == "candidate_needs_review"
    assert result["query_target_decision"]["reason_codes"] == [
        "storage_protocol_location_mismatch"
    ]


def test_describe_query_context_tool_avoids_database_mismatch_for_clean_object_route(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#MixedEvents"
    object_storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#mixed_events_s3_storage",
        label="Mixed events S3 access",
        route_roles=["rc:ArchiveRoute"],
        storage_protocol="rc:S3CompatibleStorage",
        bucket_name="ops-data-lake",
        key_prefix="curated",
        endpoint_profile="ops-s3",
        credential_reference="profile:ops-s3-readonly",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    database_storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#mixed_events_database_storage",
        label="Mixed events warehouse relation",
        route_roles=["rc:ProductionRoute", "rc:CurrentRoute"],
        storage_protocol="rc:DatabaseStorage",
        storage_root="warehouse-prod",
        path_templates=["mart.events"],
        endpoint_profile="warehouse-prod",
        credential_reference="profile:warehouse-readonly",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#mixed_events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Mixed events",
        is_table=True,
        path_templates=["events/date={date}/*.parquet"],
        storage_accesses=[object_storage["iri"], database_storage["iri"]],
        physical_layouts=[layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    result = describe_query_context_tool(db, iri=dataset)

    assert "database_relation_template_source_mismatch" not in {
        issue["code"] for issue in result["issues"]
    }
    assert all(
        group["issue_code"] != "database_relation_template_source_mismatch"
        for group in result["suggested_repair_action_groups"]
    )
    object_candidate = next(
        candidate
        for candidate in result["query_target_candidates"]
        if candidate["storage_access"]["iri"] == object_storage["iri"]
        and candidate["template_source"] == "dataset"
    )
    assert object_candidate["candidate_path"] == (
        "s3://ops-data-lake/curated/events/date={date}/*.parquet"
    )
    assert [role["label"] for role in object_candidate["route_roles"]] == [
        "archive route"
    ]
    assert object_candidate["direct_review_required"] is False
    database_candidates = [
        candidate
        for candidate in result["query_target_candidates"]
        if candidate["storage_access"]["iri"] == database_storage["iri"]
    ]
    assert [candidate["template_source"] for candidate in database_candidates] == [
        "storage_access"
    ]
    assert database_candidates[0]["relation_identifier"] == "mart.events"
    assert [role["iri"] for role in database_candidates[0]["route_roles"]] == [
        RC + "CurrentRoute",
        RC + "ProductionRoute",
    ]
    serialized_database_storage = next(
        access
        for access in result["storage_accesses"]
        if access["iri"] == database_storage["iri"]
    )
    assert [role["label"] for role in serialized_database_storage["route_roles"]] == [
        "current route",
        "production route",
    ]
    assert set(result["ready_candidate_indexes"]) == {
        result["query_target_candidates"].index(object_candidate),
        result["query_target_candidates"].index(database_candidates[0]),
    }
    database_candidate_index = result["query_target_candidates"].index(
        database_candidates[0]
    )
    assert result["query_target_decision"][
        "route_intent_review_candidate_indexes"
    ] == []
    assert result["query_target_decision"]["candidate_index"] == database_candidate_index
    peer_actions = [
        action
        for action in result["suggested_next_actions"]
        if action["tool_name"] == "draft_query_plan"
        and action["arguments"].get("candidate_selector")
        == object_candidate["candidate_selector"]
    ]
    assert peer_actions


def test_describe_query_context_tool_flags_unselected_route_intent(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    sample_storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#aaa_orders_sample_storage",
        label="Orders sample relation",
        route_roles=["rc:SampleRoute"],
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-dev",
        path_templates=["scratch.orders_sample"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    production_storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#zzz_orders_production_storage",
        label="Orders production relation",
        route_roles=["rc:ProductionRoute", "rc:CurrentRoute"],
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        path_templates=["mart.orders_current"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    table_layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#orders_table_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Orders",
        is_table=True,
        storage_accesses=[sample_storage["iri"], production_storage["iri"]],
        physical_layouts=[table_layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    result = describe_query_context_tool(db, iri=dataset)

    production_candidate = next(
        candidate
        for candidate in result["query_target_candidates"]
        if candidate["storage_access"]["iri"] == production_storage["iri"]
    )
    production_index = result["query_target_candidates"].index(production_candidate)
    assert result["query_target_decision"]["candidate_index"] != production_index
    assert result["query_target_decision"][
        "route_intent_review_candidate_indexes"
    ] == [production_index]
    assert "production/current/canonical route role intent" in (
        result["query_target_decision"]["route_intent_caution"]
    )
    assert "route_intent_review_candidates_present" in (
        result["query_target_decision"]["selection_reason_codes"]
    )
    selected_index = result["query_target_decision"]["candidate_index"]
    selected_action = next(
        action
        for action in result["suggested_next_actions"]
        if action["tool_name"] == "draft_query_plan"
        and action["route_card"]["candidate_index"] == selected_index
    )
    production_action = next(
        action
        for action in result["suggested_next_actions"]
        if action["tool_name"] == "draft_query_plan"
        and action["route_card"]["candidate_index"] == production_index
    )
    assert selected_action["unattended_recommended"] is False
    assert selected_action["unattended_caution"] == (
        result["query_target_decision"]["route_intent_caution"]
    )
    assert selected_action["unattended_review_reason_codes"] == [
        "route_intent_review_candidates_present"
    ]
    assert production_action["unattended_recommended"] is True
    assert production_action["unattended_caution"] == (
        result["query_target_decision"]["route_intent_caution"]
    )
    assert production_action["unattended_review_reason_codes"] == [
        "route_intent_review_candidates_present"
    ]
    assert result["unattended_recommended_action_indexes"] == [1]
    assert result["first_unattended_action_index"] == 1


def test_describe_query_context_tool_flags_review_gated_route_intent(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    sample_storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#aaa_orders_sample_storage",
        label="Orders sample relation",
        route_roles=["rc:SampleRoute"],
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-dev",
        path_templates=["scratch.orders_sample"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    production_storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#zzz_orders_production_storage",
        label="Orders production relation",
        route_roles=["rc:ProductionRoute", "rc:CurrentRoute"],
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        path_templates=["mart.orders_current"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    postgres_layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#orders_postgres_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    sqlite_layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#orders_sqlite_layout",
        file_format="rc:SQLiteTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Orders",
        is_table=True,
        storage_accesses=[sample_storage["iri"], production_storage["iri"]],
        physical_layouts=[postgres_layout["iri"], sqlite_layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    result = describe_query_context_tool(db, iri=dataset)

    production_candidate = next(
        candidate
        for candidate in result["query_target_candidates"]
        if candidate["storage_access"]["iri"] == production_storage["iri"]
    )
    production_index = result["query_target_candidates"].index(production_candidate)
    selected_candidate = result["query_target_candidates"][
        result["query_target_decision"]["candidate_index"]
    ]
    assert selected_candidate["storage_access"]["iri"] == sample_storage["iri"]
    assert result["query_target_decision"]["status"] == "candidate_needs_review"
    assert result["query_target_decision"][
        "route_intent_review_candidate_indexes"
    ] == [production_index]
    assert "production/current/canonical route role intent" in (
        result["query_target_decision"]["route_intent_caution"]
    )
    assert result["query_target_decision"]["selection_caution"] == (
        result["query_target_decision"]["route_intent_caution"]
    )
    assert "route_intent_review_candidates_present" in (
        result["query_target_decision"]["selection_reason_codes"]
    )
    recommended_indexes = result["unattended_recommended_action_indexes"]
    assert recommended_indexes
    assert result["first_unattended_action_index"] == recommended_indexes[0]
    for action_index in recommended_indexes:
        action = result["suggested_next_actions"][action_index]
        assert action["tool_name"] == "draft_query_plan"
        assert action["route_card"]["candidate_index"] == production_index
        assert action["unattended_recommended"] is True
    assert all(
        action.get("unattended_recommended") is False
        for action in result["suggested_next_actions"]
        if action["tool_name"] == "draft_query_plan"
        and action["route_card"]["candidate_index"] != production_index
    )


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
    assert s3_target["review_required"] is False
    assert s3_target["direct_review_required"] is False
    assert [
        reason["code"] for reason in s3_target["review_reasons"]
    ] == ["s3_credential_reference_not_recorded"]
    assert [
        reason["code"] for reason in s3_target["direct_review_reasons"]
    ] == ["s3_credential_reference_not_recorded"]
    assert any(
        issue["code"] == "s3_credential_reference_not_recorded"
        and issue["severity"] == "info"
        and issue["resource"]["iri"] == s3_storage["iri"]
        for issue in s3_result["issues"]
    )
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
    assert repair_hint["actions"][0]["action_label"] == (
        "Add reviewed relation template"
    )
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
    repair_group = context["suggested_repair_action_groups"][0]
    assert repair_group["pending_action_options"][0]["action_label"] == (
        "Add reviewed relation template"
    )
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
    assert result["suggested_repair_action_group_count"] == 1
    repair_group = result["suggested_repair_action_groups"][0]
    assert repair_group["issue_code"] == "storage_location_kind_needs_path_template"
    assert repair_group["repair_action_type"] == (
        "record_file_object_path_template_or_exact_root"
    )
    assert repair_group["choice_mode"] == "choose_one"
    assert [
        action["action_label"] for action in repair_group["pending_action_options"]
    ] == [
        "Add reviewed path template",
        "Mark root as exact object location",
    ]
    details = result["issues"][0]["details"]
    repair_hint = details["repair_hint"]
    assert repair_hint["source"] == {
        "storage_access_iri": storage["iri"],
        "storage_root": storage_root,
        "location_kind": "directory",
    }
    assert repair_hint["target"] == {
        "storage_access_iri": storage["iri"],
        "predicate": "rc:pathTemplate",
        "required_template_source": "storage_access",
    }
    assert repair_hint["actions"][0]["arguments_template"] == {
        "subject": storage["iri"],
        "predicate": "rc:pathTemplate",
        "object": "<reviewed_relative_path_template>",
        "object_kind": "literal",
        "change_kind": "add",
        "graph": "map",
    }
    assert repair_hint["actions"][1]["arguments"] == {
        "subject": storage["iri"],
        "predicate": "rc:locationKind",
        "object": "object",
        "object_kind": "literal",
        "change_kind": "replace",
        "graph": "map",
    }
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


def test_describe_query_context_tool_blocks_dataset_absolute_template_outside_local_root(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#csv_layout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    dataset = "https://example.test/project#LocalOrders"
    storage_root = str(tmp_path / "lake")
    outside_template = str(tmp_path / "external" / "orders.csv")
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
        path_templates=[outside_template],
        storage_accesses=[storage["iri"]],
        physical_layouts=[layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    result = describe_query_context_tool(db, iri=dataset)

    assert result["readiness"] == "needs_review"
    target = result["query_target_candidates"][0]
    assert target["template_source"] == "dataset"
    assert target["composition"] == "template_as_returned"
    assert target["candidate_path"] == outside_template
    assert target["candidate_path_status"] == "orientation_only"
    assert target["direct_review_required"] is True
    assert target["review_reasons"][0]["code"] == (
        "storage_protocol_location_mismatch"
    )
    assert "outside recorded storage_root" in target["review_reasons"][0][
        "details"
    ]["mismatch_reasons"][0]
    action_types = {
        action["action_type"]
        for action in target["review_reasons"][0]["details"]["repair_hint"][
            "actions"
        ]
    }
    assert "set_reviewed_bucket_name" not in action_types
    assert "set_reviewed_key_prefix" not in action_types
    assert "add_reviewed_path_template" in action_types
    assert "remove_conflicting_path_template" in action_types
    assert result["query_target_decision"]["status"] == "candidate_needs_review"
    assert result["query_target_decision"]["reason_codes"] == [
        "storage_protocol_location_mismatch"
    ]


def test_describe_query_context_tool_blocks_storage_absolute_template_outside_local_root(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#csv_layout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    dataset = "https://example.test/project#LocalOrders"
    storage_root = str(tmp_path / "lake")
    outside_template = str(tmp_path / "external" / "orders.csv")
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#local_orders_storage",
        label="Local orders storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="directory",
        storage_root=storage_root,
        path_templates=[outside_template],
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
    target = result["query_target_candidates"][0]
    assert target["template_source"] == "storage_access"
    assert target["composition"] == "template_as_returned"
    assert target["candidate_path"] == outside_template
    assert target["candidate_path_status"] == "orientation_only"
    assert target["direct_review_required"] is True
    assert target["review_reasons"][0]["code"] == (
        "storage_protocol_location_mismatch"
    )
    assert "outside recorded storage_root" in target["review_reasons"][0][
        "details"
    ]["mismatch_reasons"][0]
    assert result["query_target_decision"]["status"] == "candidate_needs_review"
    assert result["query_target_decision"]["reason_codes"] == [
        "storage_protocol_location_mismatch"
    ]


def test_describe_query_context_tool_keeps_absolute_template_inside_local_root_ready(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    layout = record_map_physical_layout_tool(
        db,
        iri="https://example.test/project#csv_layout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    dataset = "https://example.test/project#LocalOrders"
    storage_root = str(tmp_path / "lake")
    inside_template = str(tmp_path / "lake" / "orders" / "current.csv")
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#local_orders_storage",
        label="Local orders storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="directory",
        storage_root=storage_root,
        path_templates=[inside_template],
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
    target = result["query_target_candidates"][0]
    assert target["template_source"] == "storage_access"
    assert target["composition"] == "template_as_returned"
    assert target["candidate_path"] == inside_template
    assert target["candidate_path_status"] == "ready"
    assert target["review_reasons"] == []
    assert result["query_target_decision"]["status"] == "ready"
    assert result["query_target_decision"]["reason_codes"] == []

