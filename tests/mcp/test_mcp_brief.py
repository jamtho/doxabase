"""Split from test_mcp_tools.py (distillation Phase 2); tests verbatim."""

from tests.mcp.support_mcp import *  # noqa: F401,F403


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
    assert "safety_first_action" in result
    assert "safety_first_call" in result
    assert "safety_first_source" in result
    assert "frontier_first_action" in result
    assert "frontier_first_call" in result
    assert "frontier_first_source" in result
    assert "first_unattended_action" in result
    assert "first_unattended_call" in result
    assert "first_unattended_source" in result
    assert "frontier_status" in result
    frontier_status = result["frontier_status"]
    assert isinstance(frontier_status["is_complete"], bool)
    assert isinstance(frontier_status["hidden_task_count"], int)
    assert isinstance(frontier_status["hidden_profile_candidate_count"], int)
    assert isinstance(frontier_status["hidden_queue_types"], list)
    assert isinstance(frontier_status["active_queue_types"], list)
    assert isinstance(frontier_status["returned_queue_types"], list)
    assert frontier_status["first_unattended_call"] == result[
        "first_unattended_call"
    ]
    assert frontier_status["first_unattended_source"] == result[
        "first_unattended_source"
    ]
    assert frontier_status["mutation_allowed_after"] in {
        "safety_review_required_before_frontier_or_mutation",
        "frontier_expansion_required_before_mutation",
        "current_frontier_task_available",
        "no_current_recommended_task",
    }
    if result["safety_first_action"] is not None:
        assert result["safety_first_call"] == result["safety_first_action"]["call"]
        assert result["safety_first_source"] in {
            "health_tasks:privacy_export_review",
            "health_tasks:seed_recovery_review",
        }
        assert result["first_unattended_action"] == result["safety_first_action"]
        assert result["first_unattended_call"] == result["safety_first_call"]
    if result["frontier_first_action"] is not None:
        assert result["frontier_first_call"] == result["frontier_first_action"][
            "call"
        ]
        if result["safety_first_action"] is None:
            assert result["first_unattended_action"] == result[
                "frontier_first_action"
            ]
            assert result["first_unattended_call"] == result[
                "frontier_first_call"
            ]
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
        assert "inspection_next_action" in task
        assert "inspection_next_call" in task
        assert "query_plan_handoff_summary" in task
    assert isinstance(result["recommended_next_tasks"], list)


def test_project_brief_tool_serializes_profile_draft_status(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersProfileEvidence"

    record_map_dataset_tool(
        db,
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=12,
    )
    db.record_dataset_profile(
        dataset,
        summary="Orders were profiled with matching row count evidence.",
        evidence_summary="Synthetic completed profile output.",
        evidence_sources=["test://orders-profile"],
        evidence_iri=evidence,
        sample_size=12,
        sample_scope="All rows in the local Orders table.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=12,
        update_map_snapshot=False,
    )

    result = project_brief_tool(db, limit=2, profile_candidate_limit=1)
    profile = result["datasets"][0]["profile"]
    draft = profile["drafts"][0]

    assert draft["status"] == (
        "profile evidence captured; no pending map recommendations"
    )
    assert draft["requires_review"] is False
    assert draft["recommendation_count"] == 0
    assert profile["review_draft_count"] == 0
    assert profile["completed_draft_count"] == 1
    assert profile["draft_status_counts"] == {
        "profile evidence captured; no pending map recommendations": 1
    }
    assert result["profile_queue_counts"]["profile_review_drafts"] == 0
    assert result["profile_queue_counts"]["profile_completed_drafts"] == 1


def test_project_brief_tool_serializes_fixture_storage_health_task(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"
    db.record_map_dataset(
        dataset,
        label="AIS Daily Broadcast Positions",
        is_table=True,
    )

    result = project_brief_tool(db, limit=5)

    fixture_task = next(
        task
        for task in result["health_tasks"]
        if task["task_type"] == "query_fixture_staleness_review"
    )
    assert fixture_task["source"] == "fixture_storage_access_check"
    assert fixture_task["queue_types"] == ["query_repair_review"]
    assert fixture_task["fixture_names"] == ["AIS"]
    assert fixture_task["known_fixture_table_iris"] == [dataset]
    assert fixture_task["storage_access_count"] == 0
    assert fixture_task["suggested_next_action"]["tool_name"] == (
        "describe_query_context"
    )
    assert fixture_task["suggested_next_action"]["arguments"] == {
        "iri": dataset
    }
    repair_task = next(
        task
        for task in result["recommended_next_tasks"]
        if task["task_type"] == "query_repair_review"
    )
    assert repair_task["task_advisories"][0]["code"] == (
        "query_fixture_staleness_review"
    )
    assert repair_task["task_advisories"][0]["storage_access_count"] == 0
    assert repair_task["task_advisories"][0]["suggested_next_action"][
        "tool_name"
    ] == "describe_query_context"
    assert repair_task["task_group"]["group_type"] == (
        "query_fixture_staleness_review"
    )
    assert repair_task["task_group"]["suppression_policy"] == (
        "review_group_before_member_mutation"
    )


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
    assert task["suggested_next_action"]["arguments"]["iri"] == dataset
    task_selector = task["suggested_next_action"]["arguments"]["candidate_selector"]
    assert isinstance(task_selector, str)
    assert task_selector.startswith("query-target:")


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
        route_roles=["rc:ArchiveRoute"],
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
    assert missing_storage_group["action_status_counts"] == {"pending_review": 3}
    assert {
        action["action_type"] for action in missing_storage_group["actions"]
    } == {
        "stage_reviewed_storage_access",
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
    archive_candidate = next(
        candidate
        for candidate in missing_storage_group["repair_context"][
            "candidate_existing_storage_accesses"
        ]
        if candidate["storage_access"]["iri"] == archive_storage["iri"]
    )
    assert [role["iri"] for role in archive_candidate["route_roles"]] == [
        RC + "ArchiveRoute"
    ]
    assert archive_candidate["route_role_labels"] == ["archive route"]

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

