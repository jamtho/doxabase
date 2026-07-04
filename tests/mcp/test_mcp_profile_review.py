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
    assert result["staged_revision"] is None
    assert result["revision_iri"] is None
    assert result["staged_recommendation_indexes"] == []
    assert result["skipped_recommendation_indexes"] == [0]
    assert result["status_counts"] == {
        "staged": 0,
        "skipped": 1,
        "not_selected": 0,
    }
    assert result["suggested_next_actions"] == []
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
    assert advisory["suggested_next_action"]["tool_name"] == "project_brief"


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
    map_route_summary = result["suggested_next_action_group_summaries"][
        "profile_map_updates"
    ][0]
    assert map_route_summary["tool_name"] == "stage_profile_map_updates"
    assert map_route_summary["action_group"] == "profile_map_updates"
    assert map_route_summary["action_index"] == 0
    assert map_route_summary["source_kind"] == "profile_map_update"
    assert map_route_summary["review_lane"] == "profile_map_updates"
    assert map_route_summary["recommendation_indexes"] == [0, 1]
    assert map_route_summary["has_arguments"] is True
    assert map_route_summary["has_call"] is True
    assert "arguments" not in map_route_summary
    assert "call" not in map_route_summary
    assert result["suggested_next_action_summaries"][0] == map_route_summary
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
    ] == ["describe_context_slice", "list_entities", "stage_systematisation"]
    metric_route_summaries = result["suggested_next_action_group_summaries"][
        "metric_vocabulary_review"
    ]
    assert [summary["tool_name"] for summary in metric_route_summaries] == [
        "describe_context_slice",
        "list_entities",
        "stage_systematisation",
    ]
    assert metric_route_summaries[0]["semantic_move"] == "define_metric"
    assert metric_route_summaries[0]["action_kind"] == "inspect_context"
    assert metric_route_summaries[0]["writes_graph"] is False
    assert metric_route_summaries[2]["semantic_move"] == "caveat_fallback"
    assert metric_route_summaries[2]["writes_graph"] is True
    assert metric_route_summaries[2]["unattended_choice_role"] == "fallback"
    metric_context_action = result["suggested_next_action_groups"][
        "metric_vocabulary_review"
    ][0]
    metric_action_source = result["suggested_next_action_groups"][
        "metric_vocabulary_review"
    ][0]["source_profile_advisory"]
    assert metric_context_action["review_lane"] == "metric_vocabulary_review"
    assert metric_context_action["route_group_key"] == (
        metric_action_source["route_group_key"]
    )
    assert metric_context_action["route_step_key"] == (
        metric_action_source["route_step_key"]
    )
    assert metric_context_action["semantic_move"] == "define_metric"
    assert metric_context_action["unattended_choice_role"] == "inspect"
    assert metric_context_action["unattended_recommended"] is False
    metric_fallback_action = result["suggested_next_action_groups"][
        "metric_vocabulary_review"
    ][2]
    assert metric_fallback_action["semantic_move"] == "caveat_fallback"
    assert metric_fallback_action["unattended_choice_role"] == "fallback"
    assert metric_fallback_action["unattended_recommended"] is False
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
    ] == [
        "describe_context_slice",
        "record_pattern",
        "stage_systematisation",
        "stage_map_assertion_change",
    ]
    type_action = result["suggested_next_action_groups"]["profile_type_review"][3]
    type_action_source = type_action["source_profile_advisory"]
    assert type_action["tool_name"] == "stage_map_assertion_change"
    assert type_action["review_lane"] == "profile_type_review"
    assert type_action["semantic_move"] == "assert_map_type"
    assert type_action["unattended_choice_role"] == "requires_binding"
    assert type_action["unattended_recommended"] is False
    assert type_action[
        "arguments"
    ]["profile_route_sources"] == [type_action_source]
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
    assert pattern_action["source_profile_advisory"]["produces_result_bindings"][0][
        "result_field"
    ] == "pattern_iri"
    assert (
        pattern_action["source_profile_advisory"]["produces_result_bindings"][0][
            "binding_key"
        ]
        == binding_key
    )
    type_route_summaries = result["suggested_next_action_group_summaries"][
        "profile_type_review"
    ]
    assert type_route_summaries[1]["tool_name"] == "record_pattern"
    assert type_route_summaries[1]["produces_binding_keys"] == [binding_key]
    assert type_route_summaries[3]["tool_name"] == "stage_map_assertion_change"
    assert type_route_summaries[3]["requires_result_bindings"] is True
    assert type_route_summaries[3]["consumes_binding_keys"] == [binding_key]
    assert type_route_summaries[3]["argument_keys"]
    plan_by_move = {
        item["semantic_move"]: item
        for item in result["advisory_followthrough_plan"]
    }
    assert set(plan_by_move) == {
        "assert_map_type",
        "caveat_fallback",
        "define_metric",
    }
    assert plan_by_move["define_metric"]["review_lane"] == (
        "metric_vocabulary_review"
    )
    assert plan_by_move["define_metric"]["primary_tool_name"] == "list_entities"
    assert plan_by_move["define_metric"]["primary_action_kind"] == "inspect_context"
    assert plan_by_move["define_metric"]["primary_action_writes_graph"] is False
    assert plan_by_move["define_metric"]["metric_advisory_indexes"] == [0]
    assert plan_by_move["assert_map_type"]["primary_tool_name"] == (
        "stage_map_assertion_change"
    )
    assert plan_by_move["assert_map_type"]["primary_action_kind"] == (
        "stage_reviewable_change"
    )
    assert plan_by_move["assert_map_type"]["primary_action_writes_graph"] is True
    assert plan_by_move["assert_map_type"]["type_advisory_indexes"] == [0]
    assert plan_by_move["caveat_fallback"]["primary_tool_name"] == (
        "stage_systematisation"
    )
    assert plan_by_move["caveat_fallback"]["primary_action_kind"] == (
        "stage_reviewable_change"
    )
    assert plan_by_move["caveat_fallback"]["source_profile_advisories"][0][
        "route_group_key"
    ].startswith("profile_type_review:")
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
    binding_key = pattern_action["source_profile_advisory"][
        "produces_result_bindings"
    ][0]["binding_key"]
    pattern = record_pattern_tool(db, **pattern_action["arguments"])

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
    assert result["missing_binding_keys"] == []
    assert result["draft"]["type_advisory_count"] == 1
    assert result["draft"]["type_advisories"][0]["promotion_pattern_count"] == 1
    assert result["produced_binding_count"] >= 1
    assert result["binding_resolution_count"] == 1
    assert result["resolved_action_count"] == 1
    assert [
        resolution["tool_name"]
        for resolution in result["action_resolution_groups"][
            "ready_resolved_mutations"
        ]
    ] == ["stage_map_assertion_change"]
    assert [
        action["tool_name"]
        for action in result["suggested_next_action_groups"][
            "ready_resolved_mutations"
        ]
    ] == ["stage_map_assertion_change"]
    assert result["suggested_next_call_groups"]["ready_resolved_mutations"] == [
        action["call"]
        for action in result["suggested_next_action_groups"][
            "ready_resolved_mutations"
        ]
    ]
    batch_plan = result["profile_type_assertion_batch_plan"]
    assert batch_plan["result_kind"] == "profile_type_assertion_batch_plan"
    assert batch_plan["policy"] == "safe_missing_physical_type"
    assert batch_plan["eligible_action_count"] == 0
    assert batch_plan["skipped_reason_counts"] == {
        "unsupported_advisory_status": 2,
    }
    ready_route_summary = result["suggested_next_action_group_summaries"][
        "ready_resolved_mutations"
    ][0]
    assert ready_route_summary["tool_name"] == "stage_map_assertion_change"
    assert ready_route_summary["source_kind"] == "profile_advisory"
    assert ready_route_summary["semantic_move"] == "assert_map_type"
    assert ready_route_summary["writes_graph"] is True
    assert ready_route_summary["consumes_binding_keys"] == [binding_key]
    assert ready_route_summary["requires_result_bindings"] is False
    assert "arguments" not in ready_route_summary
    assert "call" not in ready_route_summary
    value_type_resolution = [
        resolution
        for resolution in result["action_resolutions"]
        if resolution["tool_name"] == "stage_map_assertion_change"
        and resolution["action"]["arguments"]["predicate"] == "rc:valueType"
    ][0]
    assert value_type_resolution["binding_status"] == "not_applicable"
    assert value_type_resolution["applied_binding_keys"] == []
    assert value_type_resolution["action"]["arguments"]["supporting_patterns"] == [
        pattern["pattern_iri"]
    ]
    assert "resolved_result_bindings" not in (
        value_type_resolution["action"]["arguments"]["profile_route_sources"][0]
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
    for action in draft["suggested_next_action_groups"]["profile_type_review"]:
        source = action["source_profile_advisory"]
        if (
            action["tool_name"] != "record_pattern"
            or source.get("advisory_statuses")
            != ["type_finding_missing_map_type"]
        ):
            continue
        produced = source["produces_result_bindings"][0]
        pattern = record_pattern_tool(db, **action["arguments"])
        result_bindings[produced["binding_key"]] = pattern["pattern_iri"]

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
    assert batch_plan["skipped_reason_counts"] == {}
    items = [
        item for batch in batch_plan["batches"] for item in batch["items"]
    ]
    assert {item["subject"] for item in items} == {
        priority_column,
        status_column,
    }
    assert all(isinstance(item["action"], dict) for item in items)
    assert {
        item["action"]["tool_name"] for item in items
    } == {"stage_map_assertion_change"}
    assert all(
        item["action"]["arguments"]["supporting_patterns"] for item in items
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
    option_contexts_by_value = {
        option["observed_value"]: option["recommendation_contexts"]
        for option in result["scalar_conflict_groups"][0]["options"]
    }
    assert source["recommendation_contexts"] == option_contexts_by_value[120]
    assert source["recommendation_contexts"][0] == {
        "recommendation_index": source["representative_recommendation_index"],
        "profile_observation_iri": source["recommendation_contexts"][0][
            "profile_observation_iri"
        ],
        "observed_count": 120,
        "sample_size": 120,
        "sample_scope": "All rows in the Invoices table.",
        "sample_method": "DuckDB full-table profile.",
        "profile_row_count": 120,
        "basis": "full_scan",
        "confidence": "high",
    }
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
    assert result["status"] == "pending profile advisory review"
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
        "stage_systematisation",
        "describe_pattern",
        "stage_pattern_promotion",
    ]
    fallback_action = advisory["suggested_next_actions"][2]
    assert fallback_action["arguments"]["profile_route_sources"] == [
        fallback_action["source_profile_advisory"]
    ]
    assert fallback_action["arguments"]["framings"][0]["graph"] == "patterns"
    promotion_action = advisory["suggested_next_actions"][4]
    promotion_args = promotion_action["arguments"]
    assert promotion_args["patterns"] == [pattern["pattern_iri"]]
    assert promotion_args["evidence"] == [shared_evidence]
    assert promotion_args["anchors"] == [project_metric]
    assert promotion_args["profile_route_sources"] == [
        promotion_action["source_profile_advisory"]
    ]
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
        "stage_systematisation",
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
    ] == [pattern_iri]
    assert grouped_type_action["source_profile_advisory"]["mixed_support"][
        "pattern_iris"
    ] == [pattern_iri]
    assert grouped_type_action["arguments"]["supporting_patterns"] == [
        pattern_iri
    ]
    assert "consumes_result_bindings" not in (
        grouped_type_action["source_profile_advisory"]
    )
    assert grouped_metric_action["arguments"]["profile_route_sources"] == [
        grouped_metric_action["source_profile_advisory"]
    ]
    assert grouped_type_action["arguments"]["profile_route_sources"] == [
        grouped_type_action["source_profile_advisory"]
    ]
    assert "Mixed support" in grouped_metric_action["reason"]
    assert "Mixed support" in grouped_type_action["arguments"]["review_note"]
    assert result["mixed_support_review_group_count"] == 1
    mixed_group = result["mixed_support_review_groups"][0]
    assert mixed_group["pattern_iris"] == [pattern_iri]
    assert mixed_group["review_lanes"] == [
        "metric_vocabulary_review",
        "profile_type_review",
    ]
    assert set(mixed_group["semantic_moves"]) == {
        "assert_map_type",
        "caveat_fallback",
        "define_metric",
        "define_value_type",
    }
    assert mixed_group["metric_advisory_indexes"] == [0]
    assert mixed_group["type_advisory_indexes"] == [0]
    assert mixed_group["action_count"] == len(mixed_group["route_step_keys"])
    assert mixed_group["action_count"] == len(mixed_group["action_labels"])
    assert "Compare the grouped actions" in mixed_group["note"]

    followthrough = plan_profile_followthrough_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
    )
    assert followthrough["missing_binding_keys"] == []
    assert "missing_binding_prerequisites" not in (
        followthrough["suggested_next_action_groups"]
    )
    value_type_resolution = [
        resolution
        for resolution in followthrough["action_resolutions"]
        if resolution["tool_name"] == "stage_map_assertion_change"
        and resolution["action"]["arguments"]["predicate"] == "rc:valueType"
    ][0]
    assert value_type_resolution["binding_status"] == "not_applicable"
    assert value_type_resolution["action"]["arguments"]["supporting_patterns"] == [
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
    assert result["revision_iri"] == result["staged_revision"]["revision_iri"]
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
        "stage_systematisation",
        "stage_map_assertion_change",
    ]
    fallback_action = result["type_advisory_suggested_next_actions"][2]
    assert fallback_action["arguments"]["profile_route_sources"] == [
        fallback_action["source_profile_advisory"]
    ]
    assert fallback_action["arguments"]["framings"][0]["graph"] == "patterns"
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

