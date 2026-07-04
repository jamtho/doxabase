"""Split from test_mcp_tools.py (distillation Phase 2); tests verbatim."""

from tests.mcp.support_mcp import *  # noqa: F401,F403


def test_stage_profile_map_updates_tool_handles_all_skipped_recommendations(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#SampledOrders"
    evidence = "https://example.test/project#SampledOrdersProfileEvidence"
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Sampled orders",
        is_table=True,
        row_count_snapshot=100,
    )
    record_profile_bundle_tool(
        db,
        dataset_iri=dataset,
        dataset_summary="Sampled orders were profiled from one partition.",
        evidence_summary="Sampled orders profile evidence.",
        evidence_sources=["test://sampled-orders-profile"],
        shared_evidence_iri=evidence,
        sample_size=40,
        sample_scope="Sampled partition rows; not the full Sampled orders table.",
        sample_method="DuckDB sampled partition profile.",
        row_count=40,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
    )
    draft = draft_profile_map_updates_tool(db, dataset, evidence)
    assert draft["recommendations"][0]["kind"] == "dataset_row_count_snapshot"
    assert draft["recommendations"][0]["default_stageable"] is False

    result = stage_profile_map_updates_tool(
        db,
        dataset,
        evidence,
        accepted_recommendation_indexes=[0],
    )

    assert result["result_kind"] == "profile_map_update_staging"
    assert result.get("staged_revision") is None
    assert result.get("revision_iri") is None
    assert result.get("staged_recommendation_indexes", []) == []
    assert result["skipped_recommendation_indexes"] == [0]
    assert result["status_counts"] == {
        "staged": 0,
        "skipped": 1,
        "not_selected": 0,
    }
    assert result.get("suggested_next_actions", []) == []
    assert "Sampled or unknown-scope row-count recommendations" in (
        result["items"][0]["reason"]
    )


def test_describe_query_context_tool_surfaces_fixture_staleness_group_advisory(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="AIS Daily Broadcast Positions",
        is_table=True,
    )

    result = describe_query_context_tool(db, iri=dataset)

    repair_group = result["suggested_repair_action_groups"][0]
    assert repair_group["issue_code"] == "missing_storage_access"
    assert len(repair_group["group_advisories"]) == 1
    advisory = repair_group["group_advisories"][0]
    assert advisory["code"] == "query_fixture_staleness_review"
    assert advisory["recommended_handling"] == (
        "review_fixture_staleness_before_staging"
    )
    assert advisory["suppression_policy"] == "review_group_before_member_mutation"
    assert advisory["fixture_names"] == ["AIS"]
    assert advisory["storage_access_count"] == 0
    assert advisory["dataset_matches_known_fixture"] is True
    assert dataset in advisory["known_fixture_table_iris"]
    assert advisory["suggested_next_action"]["tool"] == "doxabase.project_brief"


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
    assert result["status"] == "pending map recommendations"
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
    assert result["suggested_next_actions"][0]["tool"] == (
        "doxabase.stage_profile_map_updates"
    )
    assert result["suggested_next_actions"][0]["args"] == {
        "dataset_iri": table,
        "evidence_iri": shared_evidence,
        "accepted_recommendation_indexes": [0, 1],
    }
    assert list(result["suggested_next_action_groups"]) == [
        "profile_map_updates",
        "metric_vocabulary_review",
        "profile_type_review",
    ]
    assert [
        action["tool"].removeprefix("doxabase.")
        for action in result["suggested_next_action_groups"]["profile_map_updates"]
    ] == ["stage_profile_map_updates"]

    assert [
        action["tool"].removeprefix("doxabase.")
        for action in result["suggested_next_action_groups"][
            "metric_vocabulary_review"
        ]
    ] == ["get_context_graph", "list_entities", "stage_systematisation"]
    metric_action_sources = [
        source
        for action in result["suggested_next_action_groups"][
            "metric_vocabulary_review"
        ]
        for source in action["args"].get("profile_route_sources") or []
    ]
    assert metric_action_sources
    assert metric_action_sources[0]["advisory_kind"] == "metric_vocabulary_review"
    assert metric_action_sources[0]["advisory_indexes"] == [0]
    assert metric_action_sources[0]["route_group_key"].startswith(
        "metric_vocabulary_review:"
    )
    assert metric_action_sources[0]["route_step_key"].startswith(
        "profile-route-step:"
    )
    assert metric_action_sources[0]["observed_metric_iris"] == [
        result["metric_advisories"][0]["observed_metric_iri"]
    ]
    assert [
        action["tool"].removeprefix("doxabase.")
        for action in result["suggested_next_action_groups"]["profile_type_review"]
    ] == [
        "get_context_graph",
        "record_pattern",
        "stage_systematisation",
        "stage_map_assertion_change",
    ]
    type_action = result["suggested_next_action_groups"]["profile_type_review"][3]
    assert type_action["tool"] == "doxabase.stage_map_assertion_change"
    type_action_source = type_action["args"]["profile_route_sources"][0]
    assert type_action_source["advisory_kind"] == "profile_type_review"
    assert type_action_source["index_field"] == "type_advisory_index"
    assert type_action_source["advisory_indexes"] == [0]
    assert type_action_source["duplicate_advisory_indexes"] == [0]
    assert type_action_source["route_group_key"].startswith("profile_type_review:")
    assert type_action_source["route_step_key"].startswith("profile-route-step:")
    assert type_action_source["consumes_result_bindings"][0]["source_tool_name"] == (
        "record_pattern"
    )
    assert type_action_source["consumes_result_bindings"][0]["argument"] == (
        "supporting_patterns"
    )
    binding_key = type_action_source["consumes_result_bindings"][0][
        "binding_key"
    ]
    pattern_action = result["suggested_next_action_groups"][
        "profile_type_review"
    ][1]
    assert pattern_action["tool"] == "doxabase.record_pattern"
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
    assert result["recommendations"][0].get("default_skip_reason") is None
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
    assert result["recommendations"][1].get("default_skip_reason") is None
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
        "tool"
    ] == "doxabase.get_context_graph"
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
    assert result["type_advisories"][0].get("current_physical_type") is None
    assert result["type_advisories"][0].get("related_recommendation_indexes", []) == []
    assert result["type_advisories"][0].get("related_recommendation_kinds", []) == []
    assert result["type_advisories"][0]["routing_note"].startswith(
        "Inspect current map context"
    )
    assert result["type_advisories"][0]["suggested_next_actions"][0][
        "tool"
    ] == "doxabase.get_context_graph"


def test_draft_profile_map_updates_tool_rejects_missing_evidence(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(
        DoxaBaseError,
        match="evidence_iri must be a non-empty IRI or CURIE string",
    ):
        draft_profile_map_updates_tool(
            db,
            dataset_iri="https://example.test/project#Orders",
            evidence_iri=None,  # type: ignore[arg-type]
        )


def test_plan_profile_followthrough_tool_resolves_bindings_json_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/profile-followthrough#Orders"
    status_column = f"{table}Status"
    status_value_type = "https://example.test/profile-followthrough#StatusCode"
    shared_evidence = f"{table}ProfileEvidence"

    db.record_map_dataset(table, label="Orders", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=table,
        column_name="status",
        physical_type="rc:Varchar",
    )
    record_profile_bundle_tool(
        db,
        dataset_iri=table,
        dataset_summary="Orders were profiled for follow-through routing.",
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
                "value_type": status_value_type,
            }
        ],
    )

    draft = draft_profile_map_updates_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
    )
    pattern_action = draft["suggested_next_action_groups"][
        "profile_type_review"
    ][1]
    binding_key = next(
        binding["binding_key"]
        for action in draft["suggested_next_action_groups"][
            "profile_type_review"
        ]
        if action["tool"] == "doxabase.stage_map_assertion_change"
        for source in action["args"].get("profile_route_sources") or []
        for binding in source.get("consumes_result_bindings") or []
    )
    pattern = record_pattern_tool(db, **pattern_action["args"])

    missing_result = plan_profile_followthrough_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
    )
    assert missing_result["missing_binding_keys"] == [binding_key]
    assert missing_result["missing_binding_action_count"] >= 1
    assert "missing_binding_prerequisites" in missing_result[
        "action_resolution_groups"
    ]
    assert "missing_binding_prerequisites" not in missing_result[
        "suggested_next_action_groups"
    ]

    result = plan_profile_followthrough_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
        result_bindings={binding_key: pattern["pattern_iri"]},
    )

    assert result["result_kind"] == "profile_followthrough_plan"
    assert result["result_binding_keys"] == [binding_key]
    assert result.get("missing_binding_keys", []) == []
    assert result["draft"]["type_advisory_count"] == 1
    assert result["draft"]["type_advisories"][0]["promotion_pattern_count"] == 1
    assert result["binding_resolution_count"] == 1
    assert result["resolved_action_count"] == 1
    assert [
        resolution["tool"].removeprefix("doxabase.")
        for resolution in result["action_resolution_groups"][
            "ready_resolved_mutations"
        ]
    ] == ["stage_map_assertion_change"]
    assert [
        action["tool"].removeprefix("doxabase.")
        for action in result["suggested_next_action_groups"][
            "ready_resolved_mutations"
        ]
    ] == ["stage_map_assertion_change"]
    batch_plan = result["profile_type_assertion_batch_plan"]
    assert batch_plan["result_kind"] == "profile_type_assertion_batch_plan"
    assert batch_plan["policy"] == "safe_missing_physical_type"
    assert batch_plan["eligible_action_count"] == 0
    assert batch_plan["skipped_reason_counts"] == {
        "unsupported_advisory_status": 2,
    }
    value_type_resolution = [
        resolution
        for resolution in result["action_resolutions"]
        if resolution["tool"] == "doxabase.stage_map_assertion_change"
        and resolution["action"]["args"]["predicate"] == "rc:valueType"
    ][0]
    assert value_type_resolution["binding_status"] == "not_applicable"
    assert value_type_resolution.get("applied_binding_keys", []) == []
    assert value_type_resolution["action"]["args"]["supporting_patterns"] == [
        pattern["pattern_iri"]
    ]
    assert "resolved_result_bindings" not in (
        value_type_resolution["action"]["args"]["profile_route_sources"][0]
    )


def test_plan_profile_followthrough_tool_serializes_eligible_type_batch(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/profile-batch#Orders"
    status_column = f"{table}Status"
    priority_column = f"{table}Priority"
    shared_evidence = f"{table}ProfileEvidence"

    db.record_map_dataset(table, label="Orders", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=table,
        column_name="status",
    )
    db.record_map_column(
        priority_column,
        table_iri=table,
        column_name="priority",
    )
    record_profile_bundle_tool(
        db,
        dataset_iri=table,
        dataset_summary="Orders were profiled for missing map types.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=shared_evidence,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status looked varchar in the profile.",
                "physical_type": "rc:Varchar",
            },
            {
                "column_iri": priority_column,
                "column_name": "priority",
                "summary": "Priority looked integer-coded in the profile.",
                "physical_type": "rc:Integer",
            },
        ],
    )

    draft = draft_profile_map_updates_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
    )
    result_bindings: dict[str, str] = {}
    type_actions = draft["suggested_next_action_groups"]["profile_type_review"]
    for stage_action in type_actions:
        if stage_action["tool"] != "doxabase.stage_map_assertion_change":
            continue
        consumed = next(
            (
                binding
                for source in (
                    stage_action["args"].get("profile_route_sources") or []
                )
                for binding in source.get("consumes_result_bindings") or []
            ),
            None,
        )
        if consumed is None:
            continue
        pattern_action = next(
            action
            for action in type_actions
            if action["tool"] == "doxabase.record_pattern"
            and stage_action["args"]["subject"]
            in (action["args"].get("pattern_targets") or [])
        )
        pattern = record_pattern_tool(db, **pattern_action["args"])
        result_bindings[consumed["binding_key"]] = pattern["pattern_iri"]

    result = plan_profile_followthrough_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
        result_bindings=result_bindings,
    )
    json.dumps(result)
    batch_plan = result["profile_type_assertion_batch_plan"]
    assert batch_plan["eligible_action_count"] == 2
    assert batch_plan["batch_count"] == 2
    assert batch_plan.get("skipped_reason_counts", {}) == {}
    items = [
        item for batch in batch_plan["batches"] for item in batch["items"]
    ]
    assert {item["subject"] for item in items} == {
        priority_column,
        status_column,
    }
    assert all(isinstance(item["action"], dict) for item in items)
    assert {
        item["action"]["tool"].removeprefix("doxabase.") for item in items
    } == {"stage_map_assertion_change"}
    assert all(
        item["action"]["args"]["supporting_patterns"] for item in items
    )


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

    assert result.get("suggested_next_actions", []) == []
    assert list(result["suggested_next_action_groups"]) == [
        "profile_scalar_conflict_review"
    ]
    conflict_actions = result["suggested_next_action_groups"][
        "profile_scalar_conflict_review"
    ]
    assert [action["tool"].removeprefix("doxabase.") for action in conflict_actions] == [
        "stage_profile_map_updates",
        "stage_profile_map_updates",
    ]
    accepted_indexes = {
        tuple(action["args"]["accepted_recommendation_indexes"])
        for action in conflict_actions
    }
    assert len(accepted_indexes) == 2
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
    assert query_action["tool"] == "doxabase.describe_query_context"
    assert query_action["args"] == {"iri": table}
    assert query_action == result["suggested_next_actions"][0]
    assert result["suggested_next_actions"][1]["tool"] == (
        "doxabase.stage_profile_map_updates"
    )
    assert result["suggested_next_actions"][1]["args"][
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
        if action["tool"] == "doxabase.stage_map_assertion_change"
        and action["args"]["predicate"] == "rc:valueType"
    ][0]

    assert context_action["tool"] == "doxabase.get_context_graph"
    assert value_type not in context_action["args"]["seed_iris"]
    assert context_action["args"]["seed_iris"] == [
        advisory["profile_observation_iri"],
        status_column,
        RC + "Integer",
    ]
    context = get_context_graph_tool(db, **context_action["args"])
    assert status_column in {resource["iri"] for resource in context["resources"]}
    assert value_type_action["args"]["object"] == value_type


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
    assert result["status"] == "pending profile advisory review"
    advisory = result["metric_advisories"][0]
    assert advisory["promotion_pattern_count"] == 1
    assert [item["iri"] for item in advisory["promotion_patterns"]] == [
        pattern["pattern_iri"]
    ]
    assert advisory["context_pattern_count"] == 0
    assert advisory.get("context_patterns", []) == []
    assert [action["tool"].removeprefix("doxabase.") for action in advisory["suggested_next_actions"]] == [
        "get_context_graph",
        "list_entities",
        "stage_systematisation",
        "describe_pattern",
        "stage_pattern_promotion",
    ]
    fallback_action = advisory["suggested_next_actions"][2]
    assert fallback_action["args"]["framings"][0]["graph"] == "patterns"
    promotion_action = advisory["suggested_next_actions"][4]
    promotion_args = promotion_action["args"]
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
        action["tool"].removeprefix("doxabase.") for action in rerun_advisory["suggested_next_actions"]
    ] == [
        "get_context_graph",
        "list_entities",
        "stage_systematisation",
        "describe_pattern",
        "describe_staged_revision",
        "export_staged_revisions",
    ]
    assert not any(
        action["tool"] == "doxabase.stage_pattern_promotion"
        for action in rerun_advisory["suggested_next_actions"]
    )
    export_action = next(
        action
        for action in rerun["suggested_next_action_groups"][
            "metric_vocabulary_review"
        ]
        if action["tool"] == "doxabase.export_staged_revisions"
    )


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
        pattern_summary="Status profile needs metric and value type vocabulary.",
        pattern_text=(
            "StatusCompletenessScore measures populated status values, while "
            "StatusCodeValue names the reviewed status domain."
        ),
        pattern_rationale="The same profile evidence supports both review lanes.",
        pattern_support_scope="all_profiles",
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
    pattern_iri = bundle["dataset_profile"]["pattern"]["pattern_iri"]
    pattern = describe_pattern_tool(db, pattern_iri)
    assert {item["iri"] for item in pattern["map_implications"]} == {
        table,
        project_metric,
        value_type,
    }

    result = draft_profile_map_updates_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
    )

    metric_advisory = result["metric_advisories"][0]
    type_advisory = result["type_advisories"][0]
    assert [item["iri"] for item in metric_advisory["promotion_patterns"]] == [
        pattern_iri
    ]
    assert [item["iri"] for item in type_advisory["promotion_patterns"]] == [
        pattern_iri
    ]
    assert [item["iri"] for item in metric_advisory["mixed_support_patterns"]] == [
        pattern_iri
    ]
    assert [item["iri"] for item in type_advisory["mixed_support_patterns"]] == [
        pattern_iri
    ]
    assert metric_advisory["mixed_support_pattern_count"] == 1
    assert type_advisory["mixed_support_pattern_count"] == 1
    grouped_metric_action = [
        action
        for action in result["suggested_next_action_groups"][
            "metric_vocabulary_review"
        ]
        if action["tool"] == "doxabase.stage_pattern_promotion"
    ][0]
    grouped_type_action = [
        action
        for action in result["suggested_next_action_groups"]["profile_type_review"]
        if action["tool"] == "doxabase.stage_map_assertion_change"
        and action["args"]["predicate"] == "rc:valueType"
    ][0]
    assert grouped_type_action["args"]["supporting_patterns"] == [
        pattern_iri
    ]
    assert "Mixed support" in grouped_metric_action["reason"]
    assert "Mixed support" in grouped_type_action["args"]["review_note"]
    followthrough = plan_profile_followthrough_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
    )
    assert followthrough.get("missing_binding_keys", []) == []
    assert "missing_binding_prerequisites" not in (
        followthrough["suggested_next_action_groups"]
    )
    value_type_resolution = [
        resolution
        for resolution in followthrough["action_resolutions"]
        if resolution["tool"] == "doxabase.stage_map_assertion_change"
        and resolution["action"]["args"]["predicate"] == "rc:valueType"
    ][0]
    assert value_type_resolution["binding_status"] == "not_applicable"
    assert value_type_resolution["action"]["args"]["supporting_patterns"] == [
        pattern_iri
    ]


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
    assert result.get("skipped_recommendation_indexes", []) == []
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
    assert result["revision_iri"] == result["staged_revision"]["revision_iri"]
    assert result["staged_revision"]["changed_graphs"] == ["map"]
    assert result["staged_revision"]["validation_conforms"] is True
    assert result["metric_advisory_count"] == 0
    assert result.get("metric_advisory_status_counts", {}) == {}
    assert result.get("metric_advisories", []) == []
    assert result["metric_vocabulary_review_required"] is False
    assert result.get("metric_advisory_suggested_next_actions", []) == []
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
        action["tool"].removeprefix("doxabase.")
        for action in result["type_advisory_suggested_next_actions"]
    ] == [
        "get_context_graph",
        "record_pattern",
        "stage_systematisation",
        "stage_map_assertion_change",
    ]
    fallback_action = result["type_advisory_suggested_next_actions"][2]
    assert fallback_action["args"]["framings"][0]["graph"] == "patterns"
    assert result["suggested_next_actions"][0]["tool"] == (
        "doxabase.check_staged_revision_apply"
    )
    assert result["suggested_next_actions"][0]["tool"] == (
        "doxabase.check_staged_revision_apply"
    )
    assert result["suggested_next_actions"][0]["args"] == {
        "iri": result["staged_revision"]["revision_iri"]
    }
    assert result["suggested_next_actions"][1]["tool"] == (
        "doxabase.export_profile_insight_review_bundle"
    )
    assert result["suggested_next_actions"][1]["tool"] == (
        "doxabase.export_profile_insight_review_bundle"
    )
    assert result["suggested_next_actions"][1]["args"]["dataset_iri"] == (
        table
    )
    assert result["suggested_next_actions"][1]["args"]["evidence_iri"] == (
        shared_evidence
    )
    assert result["suggested_next_actions"][1]["args"]["revision_iris"] == [
        result["staged_revision"]["revision_iri"]
    ]
    assert result["suggested_next_actions"][1]["args"]["overwrite"] is True
    assert result["suggested_next_actions"][1]["args"]["path"].startswith(
        "/tmp/profile-insight-review-"
    )
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
    assert described["profile_route_sources"]
    assert described["profile_route_keys"] == list(
        dict.fromkeys(
            source["route_group_key"]
            for source in described["profile_route_sources"]
        )
    )
    route_group_lanes = {
        group["review_lane"] for group in described["profile_route_groups"]
    }
    assert "profile_map_updates" in route_group_lanes

    generic_export_path = tmp_path / "generic-profile-staged-review.md"
    generic_export = export_staged_revisions_tool(
        db,
        revision_iris=[result["staged_revision"]["revision_iri"]],
        path=str(generic_export_path),
    )
    generic_summary = generic_export["revision_summaries"][0]
    assert generic_summary["profile_route_keys"] == described["profile_route_keys"]
    assert generic_summary["profile_route_groups"] == (
        described["profile_route_groups"]
    )
    generic_markdown = generic_export_path.read_text(encoding="utf-8")
    assert "## Profile Route Bridge" in generic_markdown
    assert "profile_map_updates" in generic_markdown
    assert described["profile_route_keys"][0] in generic_markdown
    assert db.describe_dataset(table).row_count_snapshot == 8


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

    assert [action["tool"].removeprefix("doxabase.") for action in result["suggested_next_actions"]] == [
        "check_staged_revision_apply",
        "export_profile_insight_review_bundle",
        "draft_profile_map_updates",
    ]
    rerun_action = result["suggested_next_actions"][2]
    assert "reviewing and applying" in rerun_action["reason"]

