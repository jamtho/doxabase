"""Split from test_doxabase_core.py (distillation Phase 2); tests verbatim."""

from tests.core.support_core import *  # noqa: F401,F403


def test_draft_profile_map_updates_skips_row_count_for_non_table_asset(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    asset = "https://example.test/project#SalesReadme"
    evidence = "https://example.test/project#SalesReadmeProfileEvidence"
    db.record_map_dataset(asset, label="Sales README", is_table=False)
    db.record_dataset_profile(
        asset,
        summary="Sales README asset was profiled as a document.",
        evidence_summary="Synthetic document profile output.",
        evidence_sources=["test://sales-readme-profile"],
        evidence_iri=evidence,
        sample_scope="The single README asset, not table rows.",
        sample_method="Markdown heading scan.",
        row_count=1,
        update_map_snapshot=False,
    )

    draft = db.draft_profile_map_updates(asset, evidence)

    assert draft.map_dataset_found is True
    assert draft.recommendations == []
    assert draft.recommendation_count == 0
    assert draft.suggested_next_action_groups == {}
    assert db.describe_dataset(asset).row_count_snapshot is None


def test_draft_profile_map_updates_surfaces_review_candidates(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Payments"
    status_column = "https://example.test/project#PaymentsStatus"
    amount_column = "https://example.test/project#PaymentsAmount"
    settlement_column = "https://example.test/project#PaymentsSettlementMethod"
    evidence = "https://example.test/project#PaymentsProfileRunEvidence"
    project_metric = "https://example.test/project#CompletenessRatio"

    db.record_map_dataset(
        dataset,
        label="Payments",
        is_table=True,
        row_count_snapshot=10,
    )
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        nullable=False,
    )
    db.record_map_column(
        amount_column,
        table_iri=dataset,
        column_name="amount",
        nullable=False,
    )

    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Payments were profiled with a full-table scan.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://payments-profile"],
        shared_evidence_iri=evidence,
        sample_size=12,
        sample_scope="All rows in the test Payments table.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=12,
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
                "null_count": 2,
                "distinct_count": 3,
            },
            {
                "column_iri": amount_column,
                "column_name": "amount",
                "summary": "Amount had no nulls in the full scan.",
                "null_count": 0,
                "distinct_count": 12,
            },
            {
                "column_iri": settlement_column,
                "column_name": "settlement_method",
                "summary": "Settlement method was observed but is unmapped.",
                "null_count": 0,
                "distinct_count": 2,
            },
        ],
    )
    profile_pattern = db.record_pattern(
        summary="Payments profile run supports map updates.",
        pattern_text=(
            "The Payments profile run observed row-count and column-nullability "
            "findings that should travel with staged map updates."
        ),
        rationale=(
            "The profile map update lane should preserve same-evidence "
            "profile-pattern support instead of requiring a second lookup."
        ),
        pattern_targets=[dataset, status_column],
        supporting_observations=bundle.handoff_entrypoints.profile_observation_iris,
        evidence_iri=evidence,
        map_implications=[dataset, status_column, settlement_column],
    )
    metric_pattern = db.record_pattern(
        summary="Payments completeness ratio needs vocabulary.",
        pattern_text=(
            "The Payments profile run used a project-specific completeness ratio "
            "that should be reviewed in the metric vocabulary lane."
        ),
        rationale=(
            "Sharing profile observations should not automatically make a "
            "metric-vocabulary pattern supporting context for staged map facts."
        ),
        pattern_targets=[project_metric],
        supporting_observations=bundle.handoff_entrypoints.profile_observation_iris,
        evidence_iri=evidence,
        map_implications=[project_metric],
    )
    unrelated_same_evidence_pattern = db.record_pattern(
        summary="Refunds profile evidence should stay separate.",
        pattern_text=(
            "This pattern intentionally shares the Payments profile evidence "
            "but targets a different asset and map implication."
        ),
        rationale=(
            "Same evidence alone should not make a pattern supporting context "
            "for profile-derived Payments map updates."
        ),
        pattern_targets=["https://example.test/project#Refunds"],
        evidence_iri=evidence,
        map_implications=["https://example.test/project#RefundsReason"],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.map_dataset_found is True
    assert draft.evidence_iri == evidence
    assert draft.pending_staged_profile_update_iris == []
    assert draft.pending_staged_profile_update_count == 0
    assert len(draft.profile_observation_iris) == 4
    assert "read-only review context" in draft.review_note
    assert draft.recommendation_count == 3
    assert draft.representative_recommendation_indexes == [0, 1, 2]
    assert [
        (
            recommendation.recommendation_index,
            recommendation.kind,
            recommendation.resource.iri,
        )
        for recommendation in draft.recommendations
    ] == [
        (0, "dataset_row_count_snapshot", dataset),
        (1, "column_nullable", status_column),
        (2, "unmapped_profiled_column", settlement_column),
    ]
    assert draft.suggested_next_actions[0].tool_name == (
        "stage_profile_map_updates"
    )
    assert draft.suggested_next_actions[0].arguments == {
        "dataset_iri": dataset,
        "evidence_iri": evidence,
        "accepted_recommendation_indexes": [0, 1, 2],
        "supporting_patterns": [profile_pattern.pattern_iri],
    }
    assert unrelated_same_evidence_pattern.pattern_iri not in (
        draft.suggested_next_actions[0].arguments["supporting_patterns"]
    )
    assert metric_pattern.pattern_iri not in (
        draft.suggested_next_actions[0].arguments["supporting_patterns"]
    )
    assert draft.suggested_next_calls[0].startswith("stage_profile_map_updates(")
    assert list(draft.suggested_next_action_groups) == [
        "profile_map_updates",
        "metric_vocabulary_review",
    ]
    assert draft.suggested_next_actions == [
        *draft.suggested_next_action_groups["profile_map_updates"],
        *draft.suggested_next_action_groups["metric_vocabulary_review"],
    ]
    assert [
        action.tool_name
        for action in draft.suggested_next_action_groups["profile_map_updates"]
    ] == ["stage_profile_map_updates"]
    profile_map_action = draft.suggested_next_action_groups[
        "profile_map_updates"
    ][0]
    map_source = profile_map_action.source_profile_map_update
    assert map_source["review_lane"] == "profile_map_updates"
    assert map_source["route_group_key"].startswith("profile_map_updates:")
    assert map_source["route_step_key"].startswith("profile-route-step:")
    assert map_source["recommendation_indexes"] == [0, 1, 2]
    assert map_source["duplicate_group_keys"] == [
        draft.recommendations[index].duplicate_group_key for index in [0, 1, 2]
    ]
    assert map_source["route_anchor_iris"] == [
        dataset,
        status_column,
        settlement_column,
    ]
    assert [
        action.tool_name
        for action in draft.suggested_next_action_groups[
            "metric_vocabulary_review"
        ]
    ] == [
        "get_context_graph",
        "list_entities",
        "stage_systematisation",
        "describe_pattern",
        "stage_pattern_promotion",
    ]
    metric_fallback_action = draft.suggested_next_action_groups[
        "metric_vocabulary_review"
    ][2]
    assert metric_fallback_action.review_lane == "metric_vocabulary_review"
    assert metric_fallback_action.route_group_key == (
        metric_fallback_action.source_profile_advisory["route_group_key"]
    )
    assert metric_fallback_action.route_step_key == (
        metric_fallback_action.source_profile_advisory["route_step_key"]
    )
    assert metric_fallback_action.semantic_move == "caveat_fallback"
    assert metric_fallback_action.unattended_choice_role == "fallback"
    assert metric_fallback_action.unattended_recommended is False
    assert metric_fallback_action.arguments["profile_route_sources"] == [
        metric_fallback_action.source_profile_advisory
    ]
    assert metric_fallback_action.arguments["framings"][0]["graph"] == "patterns"
    metric_skeleton_action = draft.suggested_next_action_groups[
        "metric_vocabulary_review"
    ][4]
    assert metric_skeleton_action.semantic_move == "define_metric"
    assert metric_skeleton_action.unattended_choice_role == "primary"
    assert metric_skeleton_action.unattended_recommended is True
    metric_action_sources = [
        action.source_profile_advisory
        for action in draft.suggested_next_action_groups[
            "metric_vocabulary_review"
        ]
    ]
    assert {
        tuple(source["advisory_indexes"]) for source in metric_action_sources
    } == {(0,)}
    assert {
        source["advisory_kind"] for source in metric_action_sources
    } == {"metric_vocabulary_review"}
    assert {
        source["index_field"] for source in metric_action_sources
    } == {"metric_advisory_index"}
    assert {
        source["route_group_key"] for source in metric_action_sources
    } == {metric_action_sources[0]["route_group_key"]}
    assert all(
        source["route_group_key"].startswith("metric_vocabulary_review:")
        for source in metric_action_sources
    )
    assert all(
        source["route_step_key"].startswith("profile-route-step:")
        for source in metric_action_sources
    )
    assert {
        tuple(source["observed_metric_iris"]) for source in metric_action_sources
    } == {(draft.metric_advisories[0].observed_metric_iri,)}
    assert draft.suggested_next_call_groups["profile_map_updates"] == [
        draft.suggested_next_calls[0]
    ]
    staged_from_suggestion = db.stage_profile_map_updates(
        **draft.suggested_next_actions[0].arguments
    )
    assert staged_from_suggestion.staged_revision is not None
    described_staged = db.describe_staged_revision(
        staged_from_suggestion.staged_revision.revision_iri
    )
    assert {item.iri for item in described_staged.supporting_patterns} == {
        profile_pattern.pattern_iri
    }
    assert unrelated_same_evidence_pattern.pattern_iri not in {
        item.iri for item in described_staged.supporting_patterns
    }
    assert metric_pattern.pattern_iri not in {
        item.iri for item in described_staged.supporting_patterns
    }

    rerun_draft = db.draft_profile_map_updates(dataset, evidence)
    assert rerun_draft.pending_staged_profile_update_iris == [
        staged_from_suggestion.staged_revision.revision_iri
    ]
    assert rerun_draft.pending_staged_profile_update_count == 1
    assert rerun_draft.status == (
        "pending staged profile update; open review lanes remain"
    )
    assert "pending staged profile map update" in rerun_draft.review_note
    rerun_profile_map_actions = rerun_draft.suggested_next_action_groups[
        "profile_map_updates"
    ]
    assert [action.tool_name for action in rerun_profile_map_actions] == [
        "plan_staged_revision_recovery",
    ]
    pending_action = rerun_profile_map_actions[0]
    assert pending_action.arguments == {
        "revision_iris": [staged_from_suggestion.staged_revision.revision_iri]
    }
    pending_source = pending_action.source_profile_map_update
    assert pending_source["action_status"] == "already_pending"
    assert pending_source["pending_staged_profile_update_iris"] == [
        staged_from_suggestion.staged_revision.revision_iri
    ]
    assert pending_source["pending_staged_profile_update_count"] == 1
    assert pending_source["recommendation_indexes"] == [0, 1, 2]
    assert pending_source["duplicate_group_keys"] == [
        draft.recommendations[index].duplicate_group_key for index in [0, 1, 2]
    ]
    assert pending_source["route_pattern_iris"] == [profile_pattern.pattern_iri]
    assert rerun_draft.suggested_next_actions[0] == pending_action
    assert "stage_profile_map_updates" not in {
        action.tool_name for action in rerun_draft.suggested_next_actions
    }
    followthrough = db.plan_profile_followthrough(dataset, evidence)
    assert "pending_profile_map_update_review" not in (
        followthrough.action_resolution_groups
    )
    assert "pending_profile_map_update_review" not in (
        followthrough.suggested_next_action_groups
    )
    assert [
        action.tool_name for action in followthrough.suggested_next_actions
    ][:1] == ["plan_staged_revision_recovery"]
    assert "stage_profile_map_updates" not in {
        action.tool_name for action in followthrough.suggested_next_actions
    }
    duplicate_stage_arguments = {
        "dataset_iri": dataset,
        "evidence_iri": evidence,
        "accepted_recommendation_indexes": (
            draft.representative_recommendation_indexes
        ),
        "supporting_patterns": [profile_pattern.pattern_iri],
    }
    with pytest.raises(DoxaBaseError, match="pending staged profile map update"):
        db.stage_profile_map_updates(**duplicate_stage_arguments)
    forced_duplicate = db.stage_profile_map_updates(
        **duplicate_stage_arguments,
        allow_pending_profile_updates=True,
    )
    assert forced_duplicate.staged_revision is not None

    row_count = draft.recommendations[0]
    assert row_count.action == "replace_map_value"
    assert row_count.current_value == 10
    assert row_count.observed_value == 12
    assert row_count.sample_size == 12
    assert row_count.sample_scope == "All rows in the test Payments table."
    assert row_count.sample_method == "DuckDB full-table aggregate profile."
    assert row_count.profile_row_count == 12
    assert row_count.basis == "full_scan"
    assert row_count.confidence == "high"
    assert row_count.helper_name == "record_map_dataset"
    assert row_count.helper_arguments == {
        "iri": dataset,
        "row_count_snapshot": 12,
    }

    nullable = draft.recommendations[1]
    assert nullable.action == "replace_map_value"
    assert nullable.current_value is False
    assert nullable.observed_value is True
    assert nullable.observed_count == 2
    assert nullable.sample_size == 12
    assert nullable.helper_arguments == {
        "iri": status_column,
        "table_iri": dataset,
        "column_name": "status",
        "nullable": True,
    }

    unmapped = draft.recommendations[2]
    assert unmapped.action == "add_map_column_shell"
    assert unmapped.current_value is None
    assert unmapped.observed_value == "settlement_method"
    assert unmapped.helper_arguments == {
        "iri": settlement_column,
        "table_iri": dataset,
        "column_name": "settlement_method",
    }

    assert len(draft.metric_advisories) == 1
    assert draft.metric_advisory_count == 1
    assert draft.metric_advisory_status_counts == {
        "project_metric_undefined": 1,
    }
    metric_advisory = draft.metric_advisories[0]
    assert metric_advisory.metric.iri == project_metric
    assert metric_advisory.observed_metric_iri.startswith(
        "https://richcanopy.org/doxabase/generated/observed-profile-metric/"
    )
    assert metric_advisory.advisory_status == "project_metric_undefined"
    assert metric_advisory.definition_found is False
    assert metric_advisory.definition is None
    assert [action.tool_name for action in metric_advisory.suggested_next_actions] == [
        "get_context_graph",
        "list_entities",
        "stage_systematisation",
        "describe_pattern",
        "stage_pattern_promotion",
    ]
    metric_fallback_action = metric_advisory.suggested_next_actions[2]
    assert metric_fallback_action.arguments["profile_route_sources"] == [
        metric_fallback_action.source_profile_advisory
    ]
    assert metric_fallback_action.arguments["framings"][0]["graph"] == "patterns"
    assert [item.iri for item in metric_advisory.promotion_patterns] == [
        metric_pattern.pattern_iri
    ]
    assert metric_advisory.suggested_next_actions[0].arguments == {
        "seed_iris": [metric_advisory.observed_metric_iri],
        "profile": "dataset_brief",
    }
    assert metric_advisory.recommendation == (
        "review_metric_vocabulary_before_reuse"
    )

    description = db.describe_dataset(dataset)
    assert description.row_count_snapshot == 10
    assert {
        column.iri: column.nullable for column in description.columns
    } == {
        status_column: False,
        amount_column: False,
    }


def test_profile_insight_route_bridge_groups_repeated_lane_labels(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    candidate = ProfileInsightReviewCandidate(
        revision_iri="https://example.test/revision#metric-promotion",
        summary="Promote freshness metric vocabulary",
        changed_graphs=["ontology"],
        relation_reasons=["profile_derived_anchor"],
        profile_route_keys=["route:dataset", "route:column-a", "route:column-b"],
        profile_route_groups=[
            {
                "route_group_key": "route:dataset",
                "review_lane": "metric_vocabulary_review",
                "route_step_keys": ["step:dataset"],
                "matched_by": ["revision_anchor"],
                "match_strength": "direct_action",
            },
            {
                "route_group_key": "route:column-a",
                "review_lane": "metric_vocabulary_review",
                "route_step_keys": ["step:column-a"],
                "matched_by": ["revision_anchor"],
                "match_strength": "direct_action",
            },
            {
                "route_group_key": "route:column-b",
                "review_lane": "metric_vocabulary_review",
                "route_step_keys": ["step:column-b"],
                "matched_by": ["revision_anchor"],
                "match_strength": "direct_action",
            },
        ],
        matched_evidence_iris=[],
        matched_profile_observation_iris=[],
        matched_supporting_pattern_iris=[],
        matched_revision_anchor_iris=["https://example.test/project#FreshnessMetric"],
        explicit=False,
    )

    bridge = db._profile_insight_route_bridge_markdown([candidate])

    assert "route:dataset" in bridge
    assert "route:column-a" in bridge
    assert "route:column-b" in bridge
    assert (
        "metric_vocabulary_review (direct_action; 3 route groups)"
        in bridge
    )
    assert "metric_vocabulary_review (direct_action), " not in bridge


def test_profile_map_update_support_omits_type_review_patterns(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Payments"
    status_column = "https://example.test/project#PaymentsStatus"
    status_value_type = "https://example.test/project#StatusCodeValue"
    evidence = "https://example.test/project#PaymentsProfileRunEvidence"

    db.record_map_dataset(
        dataset,
        label="Payments",
        is_table=True,
        row_count_snapshot=10,
    )
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        nullable=False,
        physical_type="rc:Varchar",
    )

    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Payments were profiled with a full-table scan.",
        evidence_summary="Synthetic profile run with nullable and type findings.",
        evidence_sources=["test://payments-profile"],
        shared_evidence_iri=evidence,
        sample_size=12,
        sample_scope="All rows in the test Payments table.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=12,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status had nulls and looked integer-coded.",
                "null_count": 2,
                "physical_type": "rc:Integer",
                "value_type": status_value_type,
            }
        ],
    )
    profile = db.describe_profile_run(
        dataset,
        evidence,
    ).mapped_column_profile_observations[0]
    map_pattern = db.record_pattern(
        summary="Payments profile supports map updates.",
        pattern_text=(
            "The Payments profile run supports row-count and nullable map "
            "updates for the current table and status column."
        ),
        rationale=(
            "This same-evidence pattern is about helper-equivalent map facts, "
            "not semantic type assertions."
        ),
        pattern_targets=[dataset, status_column],
        supporting_observations=bundle.handoff_entrypoints.profile_observation_iris,
        evidence_iri=evidence,
        map_implications=[dataset, status_column],
    )
    type_pattern = db.record_pattern(
        summary="Payments status type finding needs review.",
        pattern_text=(
            "The Payments status profile suggests an integer-coded status "
            "value type that should stay in type review."
        ),
        rationale=(
            "Column-targeted type rationale should not become automatic support "
            "for unrelated nullable or row-count map patches."
        ),
        pattern_targets=[status_column],
        supporting_observations=[profile.iri],
        evidence_iri=evidence,
        map_implications=[status_column, f"{RC}Integer", status_value_type],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.recommendation_count == 2
    assert draft.type_advisory_count == 1
    profile_map_action = draft.suggested_next_action_groups[
        "profile_map_updates"
    ][0]
    assert profile_map_action.arguments["supporting_patterns"] == [
        map_pattern.pattern_iri
    ]
    type_advisory = draft.type_advisories[0]
    value_type_promotion_action = [
        action
        for action in type_advisory.suggested_next_actions
        if action.tool_name == "stage_pattern_promotion"
    ][0]
    assert value_type_promotion_action.arguments["patterns"] == [
        type_pattern.pattern_iri
    ]
    assert type_pattern.pattern_iri not in (
        profile_map_action.arguments["supporting_patterns"]
    )

    staged = db.stage_profile_map_updates(**profile_map_action.arguments)
    assert staged.staged_revision is not None
    staged_description = db.describe_staged_revision(
        staged.staged_revision.revision_iri
    )

    assert {item.iri for item in staged_description.supporting_patterns} == {
        map_pattern.pattern_iri
    }
    assert type_pattern.pattern_iri not in {
        item.iri for item in staged_description.supporting_patterns
    }
    nullable_impact = next(
        impact
        for impact in staged_description.impacts
        if impact.impact_type == "changed_nullable"
    )
    assert type_pattern.pattern_iri in {
        item.iri for item in nullable_impact.related_patterns
    }
    assert map_pattern.pattern_iri in {
        item.iri for item in nullable_impact.related_patterns
    }


def test_draft_profile_map_updates_surfaces_profile_type_advisories(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    status_value_type = "https://example.test/project#OrderStatusCode"
    profile_metric_kind = "https://example.test/project#OrdersStatusCompleteness"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"

    db.replace_graph_triples(
        "ontology",
        additions=f"""
            @prefix rc: <https://richcanopy.org/ns/rc#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            <{status_value_type}> a rc:ValueType ;
                rdfs:label "Order status code" .

            <{profile_metric_kind}> a rc:ProfileMetricKind ;
                rdfs:label "Orders status completeness" .
        """,
        allow_count_change=True,
    )
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        physical_type="rc:Varchar",
    )

    db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled without changing the map.",
        evidence_summary="Synthetic type-finding profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
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

    profile_run = db.describe_profile_run(dataset, evidence)
    profile = profile_run.mapped_column_profile_observations[0]
    assert profile.observed_physical_type is not None
    assert profile.observed_physical_type.iri == RC + "Integer"
    assert profile.observed_value_type is not None
    assert profile.observed_value_type.iri == status_value_type

    description = db.describe_dataset(dataset)
    column = description.columns[0]
    assert column.physical_type is not None
    assert column.physical_type.iri == RC + "Varchar"
    assert column.value_type is None

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.recommendation_count == 0
    assert draft.metric_advisory_count == 0
    assert draft.type_advisory_count == 1
    assert draft.type_advisory_status_counts == {
        "type_finding_conflicts_current_map": 1,
    }
    advisory = draft.type_advisories[0]
    assert advisory.profile_observation_iri == profile.iri
    assert advisory.observed_column.iri == status_column
    assert advisory.observed_physical_type is not None
    assert advisory.observed_physical_type.iri == RC + "Integer"
    assert advisory.observed_value_type is not None
    assert advisory.observed_value_type.iri == status_value_type
    assert advisory.map_column_found is True
    assert advisory.current_physical_type is not None
    assert advisory.current_physical_type.iri == RC + "Varchar"
    assert advisory.current_value_type is None
    assert advisory.recommendation == "review_profile_type_finding_before_map_update"
    assert advisory.related_recommendation_indexes == []
    assert advisory.related_recommendation_kinds == []
    assert advisory.routing_note.startswith("Inspect current map context")
    assert [action.tool_name for action in advisory.suggested_next_actions] == [
        "get_context_graph",
        "record_pattern",
        "stage_systematisation",
        "stage_map_assertion_change",
        "stage_map_assertion_change",
    ]
    assert [
        action.arguments["predicate"]
        for action in advisory.suggested_next_actions
        if action.tool_name == "stage_map_assertion_change"
    ] == ["rc:physicalType", "rc:valueType"]
    plan_by_move = {
        item.semantic_move: item for item in draft.advisory_followthrough_plan
    }
    assert set(plan_by_move) == {"assert_map_type", "caveat_fallback"}
    assert plan_by_move["assert_map_type"].review_lane == "profile_type_review"
    assert plan_by_move["assert_map_type"].primary_tool_name == (
        "stage_map_assertion_change"
    )
    assert plan_by_move["assert_map_type"].primary_action_kind == (
        "stage_reviewable_change"
    )
    assert plan_by_move["assert_map_type"].primary_action_writes_graph is True
    assert plan_by_move["assert_map_type"].type_advisory_indexes == [0]
    assert plan_by_move["assert_map_type"].advisory_status_counts == {
        "type_finding_conflicts_current_map": 1,
    }
    assert plan_by_move["caveat_fallback"].primary_tool_name == (
        "stage_systematisation"
    )
    assert plan_by_move["caveat_fallback"].primary_action_kind == (
        "stage_reviewable_change"
    )
    assert plan_by_move["caveat_fallback"].primary_action_writes_graph is True
    assert plan_by_move["caveat_fallback"].type_advisory_indexes == [0]
    fallback_action = [
        action
        for action in advisory.suggested_next_actions
        if action.tool_name == "stage_systematisation"
    ][0]
    assert fallback_action.arguments["profile_route_sources"] == [
        fallback_action.source_profile_advisory
    ]
    assert fallback_action.arguments["supporting_observations"] == [profile.iri]
    assert fallback_action.arguments["evidence"] == [evidence]
    assert fallback_action.arguments["framings"][0]["graph"] == "patterns"
    assert "rc:supportingObservation" in (
        fallback_action.arguments["framings"][0]["content"]
    )
    staged_fallback = db.stage_systematisation(**fallback_action.arguments)
    assert staged_fallback.profile_route_source_count == 1
    fallback_staged_iri = staged_fallback.staged_revisions[0].revision_iri
    rerun_after_fallback = db.draft_profile_map_updates(dataset, evidence)
    rerun_advisory = rerun_after_fallback.type_advisories[0]
    assert [
        action.tool_name for action in rerun_advisory.suggested_next_actions
    ] == [
        "get_context_graph",
        "describe_staged_revision",
        "export_staged_revisions",
        "stage_map_assertion_change",
        "stage_map_assertion_change",
    ]
    assert not any(
        action.tool_name == "stage_systematisation"
        for action in rerun_advisory.suggested_next_actions
    )
    pending_fallback_action = rerun_advisory.suggested_next_actions[1]
    assert pending_fallback_action.semantic_move == "caveat_fallback"
    assert pending_fallback_action.arguments == {
        "iri": fallback_staged_iri,
        "include_current_apply_check": True,
    }
    assert pending_fallback_action.source_profile_advisory[
        "pending_staged_fallback_iris"
    ] == [fallback_staged_iri]
    rerun_plan_by_move = {
        item.semantic_move: item
        for item in rerun_after_fallback.advisory_followthrough_plan
    }
    assert set(rerun_plan_by_move) == {"assert_map_type", "caveat_fallback"}
    assert (
        rerun_plan_by_move["caveat_fallback"].primary_action_writes_graph
        is False
    )
    followthrough_after_fallback = db.plan_profile_followthrough(
        dataset,
        evidence,
    )
    assert "stage_systematisation" not in {
        action.tool_name for action in followthrough_after_fallback.suggested_next_actions
    }
    staged_type_actions = [
        action
        for action in advisory.suggested_next_actions
        if action.tool_name == "stage_map_assertion_change"
    ]
    assert all(
        action.arguments["supporting_patterns"] == []
        for action in staged_type_actions
    )
    assert all(
        "returned pattern_iri" in action.reason
        for action in staged_type_actions
    )
    assert all(
        "supporting_patterns=[]" in action.call
        for action in staged_type_actions
    )
    assert all(
        "add its pattern_iri to supporting_patterns" in action.arguments["review_note"]
        for action in staged_type_actions
    )
    pattern_action = [
        action
        for action in advisory.suggested_next_actions
        if action.tool_name == "record_pattern"
    ][0]
    produced_bindings = pattern_action.source_profile_advisory[
        "produces_result_bindings"
    ]
    assert produced_bindings == [
        {
            "binding_key": (
                pattern_action.source_profile_advisory["route_group_key"]
                + ":profile-type-support-pattern"
            ),
            "result_field": "pattern_iri",
            "target_tool_name": "stage_map_assertion_change",
            "target_argument": "supporting_patterns",
            "append": True,
            "review_lane": "profile_type_review",
            "route_group_key": pattern_action.source_profile_advisory[
                "route_group_key"
            ],
            "target_semantic_move": "assert_map_type",
        }
    ]
    assert all(
        action.source_profile_advisory["consumes_result_bindings"][0][
            "binding_key"
        ]
        == produced_bindings[0]["binding_key"]
        for action in staged_type_actions
    )
    assert all(
        action.source_profile_advisory["consumes_result_bindings"][0][
            "source_result_field"
        ]
        == "pattern_iri"
        for action in staged_type_actions
    )
    assert all(
        action.source_profile_advisory["consumes_result_bindings"][0][
            "argument"
        ]
        == "supporting_patterns"
        for action in staged_type_actions
    )

    recorded_pattern = db.record_pattern(
        **pattern_action.arguments,
    )
    related_pattern = db.record_pattern(
        summary="Orders status type assertions already have nearby lore.",
        pattern_text=(
            "Prior map review notes say Orders.status type changes should carry "
            "nearby column lore into staged map assertions."
        ),
        rationale="The assertion-support scan should merge related column patterns.",
        pattern_targets=[status_column],
        evidence_iri=evidence,
    )
    metric_pattern = db.record_pattern(
        summary="Orders status profile metric needs vocabulary review.",
        pattern_text=(
            "The profile metric attached to Orders.status is useful review "
            "context but does not directly support a physical type assertion."
        ),
        rationale=(
            "Same-profile observation patterns should remain reachable as "
            "context without becoming direct staged assertion support."
        ),
        pattern_targets=[profile_metric_kind],
        supporting_observations=[profile.iri],
        evidence_iri=evidence,
    )
    physical_type_action = staged_type_actions[0]
    physical_type_arguments = dict(physical_type_action.arguments)
    physical_type_arguments["supporting_patterns"] = [recorded_pattern.pattern_iri]
    staged_type = db.stage_map_assertion_change(**physical_type_arguments)
    staged_type_description = db.describe_staged_revision(
        staged_type.staged_revision.revision_iri,
    )

    assert profile.iri in {
        item.iri for item in staged_type_description.supporting_observations
    }
    assert evidence in {item.iri for item in staged_type_description.evidence}
    assert {
        recorded_pattern.pattern_iri,
        related_pattern.pattern_iri,
    }.issubset(
        {item.iri for item in staged_type_description.supporting_patterns},
    )
    assert metric_pattern.pattern_iri not in {
        item.iri for item in staged_type_description.supporting_patterns
    }
    assert [action.tool_name for action in draft.suggested_next_actions] == [
        "get_context_graph",
        "record_pattern",
        "stage_systematisation",
        "stage_map_assertion_change",
        "stage_map_assertion_change",
    ]
    assert list(draft.suggested_next_action_groups) == [
        "profile_type_review",
    ]
    assert draft.suggested_next_actions == (
        draft.suggested_next_action_groups["profile_type_review"]
    )
    assert db.validate_graph(scope="all").conforms


def test_plan_profile_followthrough_resolves_pattern_binding_and_reruns(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    status_value_type = "https://example.test/project#OrderStatusCode"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        physical_type="rc:Varchar",
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled without changing the map.",
        evidence_summary="Synthetic type-finding profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
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
    initial_draft = db.draft_profile_map_updates(dataset, evidence)
    advisory = initial_draft.type_advisories[0]
    pattern_action = [
        action
        for action in advisory.suggested_next_actions
        if action.tool_name == "record_pattern"
    ][0]
    produced_binding = pattern_action.source_profile_advisory[
        "produces_result_bindings"
    ][0]

    recorded_pattern = db.record_pattern(**pattern_action.arguments)
    plan = db.plan_profile_followthrough(
        dataset,
        evidence,
        result_bindings={
            produced_binding["binding_key"]: recorded_pattern.pattern_iri,
        },
    )

    assert plan.result_kind == "profile_followthrough_plan"
    assert plan.result_binding_keys == [produced_binding["binding_key"]]
    assert plan.draft.type_advisory_count == 1
    rerun_advisory = plan.draft.type_advisories[0]
    assert rerun_advisory.promotion_pattern_count == 1
    assert rerun_advisory.promotion_patterns[0].iri == recorded_pattern.pattern_iri
    assert {
        item.semantic_move for item in plan.draft.advisory_followthrough_plan
    } == {"assert_map_type", "caveat_fallback", "define_value_type"}

    assert plan.produced_binding_count >= 1
    assert plan.binding_resolution_count == 1
    assert plan.resolved_action_count == 1
    assert plan.missing_binding_action_count == 0
    assert {
        resolution.status for resolution in plan.binding_resolutions
    } == {"resolved"}
    assert {
        resolution.target_tool_name for resolution in plan.binding_resolutions
    } == {"stage_map_assertion_change"}
    assert {
        resolution.target_argument for resolution in plan.binding_resolutions
    } == {"supporting_patterns"}
    assert [
        resolution.tool_name
        for resolution in plan.action_resolution_groups[
            "ready_resolved_mutations"
        ]
    ] == ["stage_map_assertion_change"]
    assert [
        action.tool_name
        for action in plan.suggested_next_action_groups[
            "ready_resolved_mutations"
        ]
    ] == ["stage_map_assertion_change"]
    independent_value_type_action = [
        resolution
        for resolution in plan.action_resolution_groups[
            "independent_mutation_reviews"
        ]
        if resolution.tool_name == "stage_map_assertion_change"
        and resolution.action.arguments["predicate"] == "rc:valueType"
    ][0]
    assert independent_value_type_action.binding_status == "not_applicable"
    assert independent_value_type_action.action.arguments["supporting_patterns"] == [
        recorded_pattern.pattern_iri
    ]
    assert "missing_binding_prerequisites" not in (
        plan.action_resolution_groups
    )
    assert "missing_binding_prerequisites" not in (
        plan.suggested_next_action_groups
    )
    assert plan.suggested_next_call_groups[
        "ready_resolved_mutations"
    ] == [
        action.call
        for action in plan.suggested_next_action_groups[
            "ready_resolved_mutations"
        ]
    ]
    value_type_action_resolution = [
        resolution
        for resolution in plan.action_resolutions
        if resolution.tool_name == "stage_map_assertion_change"
        and resolution.action.arguments["predicate"] == "rc:valueType"
    ][0]
    assert value_type_action_resolution.binding_status == "not_applicable"
    assert value_type_action_resolution.applied_binding_keys == []
    value_type_action = value_type_action_resolution.action
    assert value_type_action.arguments["supporting_patterns"] == [
        recorded_pattern.pattern_iri
    ]
    route_source = value_type_action.arguments["profile_route_sources"][0]
    assert "resolved_result_bindings" not in route_source
    assert f"'{recorded_pattern.pattern_iri}'" in value_type_action.call
    assert any(
        resolution.tool_name == "stage_pattern_promotion"
        and resolution.semantic_move == "define_value_type"
        for resolution in plan.action_resolutions
    )

    staged = db.stage_map_assertion_change(**value_type_action.arguments)
    staged_description = db.describe_staged_revision(
        staged.staged_revision.revision_iri,
    )

    assert recorded_pattern.pattern_iri in {
        item.iri for item in staged_description.supporting_patterns
    }
    assert db.validate_graph(scope="all").conforms


def test_plan_profile_followthrough_batches_safe_missing_physical_type_assertions(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    priority_column = "https://example.test/project#OrdersPriority"
    channel_column = "https://example.test/project#OrdersChannel"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
    )
    db.record_map_column(
        priority_column,
        table_iri=dataset,
        column_name="priority",
    )
    db.record_map_column(
        channel_column,
        table_iri=dataset,
        column_name="channel",
        physical_type="rc:Varchar",
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled for type follow-through.",
        evidence_summary="Synthetic profile run with mixed type findings.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
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
            {
                "column_iri": channel_column,
                "column_name": "channel",
                "summary": "Channel conflicted with the map type.",
                "physical_type": "rc:Integer",
            },
        ],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)
    assert draft.type_advisory_status_counts == {
        "type_finding_conflicts_current_map": 1,
        "type_finding_missing_map_type": 2,
    }

    missing_binding_plan = db.plan_profile_followthrough(dataset, evidence)
    missing_batch = missing_binding_plan.profile_type_assertion_batch_plan
    assert missing_batch["eligible_action_count"] == 0
    assert missing_batch["batch_count"] == 0
    assert missing_batch["skipped_reason_counts"] == {
        "requires_result_binding": 2,
        "unsupported_advisory_status": 1,
    }
    assert missing_batch["skipped_status_counts"] == {
        "type_finding_conflicts_current_map": 1,
        "type_finding_missing_map_type": 2,
    }

    result_bindings: dict[str, str] = {}
    for action in draft.suggested_next_action_groups["profile_type_review"]:
        source = getattr(action, "source_profile_advisory", {})
        if (
            action.tool_name != "record_pattern"
            or source.get("advisory_statuses")
            != ["type_finding_missing_map_type"]
        ):
            continue
        produced = source["produces_result_bindings"][0]
        pattern = db.record_pattern(**action.arguments)
        result_bindings[produced["binding_key"]] = pattern.pattern_iri

    ready_plan = db.plan_profile_followthrough(
        dataset,
        evidence,
        result_bindings=result_bindings,
    )
    ready_batch = ready_plan.profile_type_assertion_batch_plan

    assert ready_batch["result_kind"] == "profile_type_assertion_batch_plan"
    assert ready_batch["policy"] == "safe_missing_physical_type"
    assert ready_batch["eligible_action_count"] == 2
    assert ready_batch["skipped_reason_counts"] == {
        "unsupported_advisory_status": 1,
    }
    assert ready_batch["skipped_status_counts"] == {
        "type_finding_conflicts_current_map": 1,
    }
    assert {
        batch["object"] for batch in ready_batch["batches"]
    } == {
        RC + "Integer",
        RC + "Varchar",
    }
    assert {
        item["subject"]
        for batch in ready_batch["batches"]
        for item in batch["items"]
    } == {priority_column, status_column}
    assert {
        item["predicate"]
        for batch in ready_batch["batches"]
        for item in batch["items"]
    } == {"rc:physicalType"}
    assert all(
        item["action"].tool_name == "stage_map_assertion_change"
        and item["supporting_patterns"]
        for batch in ready_batch["batches"]
        for item in batch["items"]
    )


def test_profile_type_advisory_routes_value_type_promotion_skeleton(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    status_value_type = "https://example.test/project#StatusCodeValue"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        physical_type="rc:Varchar",
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Orders profile with an undefined project value type.",
        evidence_summary="Synthetic type-finding profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
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
    profile = db.describe_profile_run(
        dataset,
        evidence,
    ).mapped_column_profile_observations[0]
    target_pattern = db.record_pattern(
        summary="Status code value needs vocabulary.",
        pattern_text=(
            "Status code value means the reviewed order lifecycle domain, not "
            "only the integer storage representation."
        ),
        rationale="The pattern and profile run share the same evidence.",
        pattern_targets=[status_value_type],
        supporting_observations=[profile.iri],
        evidence_iri=evidence,
    )
    implication_pattern = db.record_pattern(
        summary="Orders status profile implies a value type.",
        pattern_text=(
            "The Orders status profile implies a reusable project value type "
            "before status codes are promoted into current map assertions."
        ),
        rationale="The pattern and profile run share the same evidence.",
        pattern_targets=[status_column],
        supporting_observations=[profile.iri],
        evidence_iri=evidence,
        map_implications=[status_value_type],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)
    advisory = draft.type_advisories[0]

    assert advisory.observed_value_type is not None
    assert advisory.observed_value_type.iri == status_value_type
    assert [action.tool_name for action in advisory.suggested_next_actions] == [
        "get_context_graph",
        "record_pattern",
        "stage_systematisation",
        "describe_pattern",
        "describe_pattern",
        "stage_pattern_promotion",
        "stage_map_assertion_change",
        "stage_map_assertion_change",
    ]
    value_type_plan = next(
        item
        for item in draft.advisory_followthrough_plan
        if item.semantic_move == "define_value_type"
    )
    assert value_type_plan.review_lane == "profile_type_review"
    assert value_type_plan.primary_tool_name == "stage_pattern_promotion"
    assert value_type_plan.type_advisory_indexes == [0]
    assert set(value_type_plan.route_pattern_iris) == {
        target_pattern.pattern_iri,
        implication_pattern.pattern_iri,
    }
    assert {
        item.semantic_move for item in draft.advisory_followthrough_plan
    } == {"assert_map_type", "caveat_fallback", "define_value_type"}
    promotion_action = [
        action
        for action in advisory.suggested_next_actions
        if action.tool_name == "stage_pattern_promotion"
    ][0]
    promotion_args = promotion_action.arguments
    assert promotion_action.action_label == "Stage value type vocabulary skeleton"
    assert set(promotion_args["patterns"]) == {
        target_pattern.pattern_iri,
        implication_pattern.pattern_iri,
    }
    assert promotion_args["anchors"] == [status_value_type]
    assert promotion_args["evidence"] == [evidence]
    framing_content = promotion_args["framings"][0]["content"]
    assert "rc:ValueType" in framing_content
    assert "rc:ProfileMetricKind" not in framing_content
    assert status_value_type in framing_content
    assert "reviewed order lifecycle domain" in framing_content
    value_type_route_source = promotion_args["profile_route_sources"][0]
    assert value_type_route_source["route_group_key"] == (
        value_type_plan.route_group_key
    )
    assert value_type_route_source["semantic_move"] == "define_value_type"
    assert value_type_route_source["route_step_key"] in (
        value_type_plan.route_step_keys
    )
    assert value_type_route_source["advisory_indexes"] == (
        value_type_plan.type_advisory_indexes
    )
    assert set(value_type_route_source["route_pattern_iris"]) == set(
        value_type_plan.route_pattern_iris
    )

    staged_promotion = db.stage_pattern_promotion(**promotion_args)

    assert staged_promotion.profile_route_source_count == len(
        promotion_args["profile_route_sources"]
    )
    assert len(staged_promotion.staged_revisions) == 1
    staged = db.describe_staged_revision(
        staged_promotion.staged_revisions[0].revision_iri
    )
    assert staged.validation_conforms is True
    assert {item.iri for item in staged.supporting_patterns} == {
        target_pattern.pattern_iri,
        implication_pattern.pattern_iri,
    }
    assert {item.iri for item in staged.supporting_observations} == {profile.iri}
    assert {item.iri for item in staged.evidence} == {evidence}
    assert status_value_type in {item.iri for item in staged.revision_anchors}

    rerun = db.draft_profile_map_updates(dataset, evidence)
    rerun_advisory = rerun.type_advisories[0]
    assert rerun_advisory.pending_staged_promotion_iris == [staged.iri]
    assert rerun_advisory.pending_staged_promotion_count == 1
    assert rerun_advisory.pending_staged_assertion_iris == []
    assert [
        action.tool_name for action in rerun_advisory.suggested_next_actions
    ] == [
        "get_context_graph",
        "record_pattern",
        "stage_systematisation",
        "describe_pattern",
        "describe_pattern",
        "describe_staged_revision",
        "export_staged_revisions",
        "stage_map_assertion_change",
        "stage_map_assertion_change",
    ]
    assert not any(
        action.tool_name == "stage_pattern_promotion"
        for action in rerun_advisory.suggested_next_actions
    )
    pending_promotion_export = next(
        action
        for action in rerun.suggested_next_action_groups["profile_type_review"]
        if action.tool_name == "export_staged_revisions"
        and action.semantic_move == "define_value_type"
    )
    assert pending_promotion_export.source_profile_advisory[
        "action_status"
    ] == "already_pending"
    assert pending_promotion_export.source_profile_advisory[
        "pending_staged_promotion_iris"
    ] == [staged.iri]

    review = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        tmp_path / "orders-profile-type-review.md",
    )
    candidate = next(
        candidate
        for candidate in review.candidates
        if candidate.revision_iri == staged.iri
    )
    route_groups = {
        group["review_lane"]: group for group in candidate.profile_route_groups
    }
    assert route_groups["profile_type_review"]["match_strength"] == (
        "direct_action"
    )
    assert route_groups["profile_type_review"]["direct_semantic_moves"] == [
        "define_value_type"
    ]
    assert route_groups["profile_type_review"]["closed_semantic_moves"] == [
        "define_value_type"
    ]
    assert "assert_map_type" in route_groups["profile_type_review"][
        "semantic_moves"
    ]
    assert "assert_map_type" in route_groups["profile_type_review"][
        "remaining_semantic_moves"
    ]
    open_lanes = {
        lane.review_lane: lane for lane in review.open_profile_review_lanes
    }
    assert set(open_lanes) == {"profile_type_review"}
    assert open_lanes["profile_type_review"].route_group_keys == [
        value_type_plan.route_group_key
    ]
    assert open_lanes["profile_type_review"].closed_semantic_moves == [
        "define_value_type"
    ]
    assert open_lanes["profile_type_review"].closed_route_step_keys == [
        value_type_route_source["route_step_key"]
    ]
    assert "assert_map_type" in open_lanes[
        "profile_type_review"
    ].remaining_semantic_moves
    assert open_lanes["profile_type_review"].matched_candidate_revision_iris == [
        staged.iri
    ]
    assert not set(open_lanes["profile_type_review"].route_step_keys) & set(
        value_type_plan.route_step_keys
    )
    assert open_lanes["profile_type_review"].action_count == 5
    assert len(open_lanes["profile_type_review"].remaining_actions) == 5
    assert {
        action.route_step_key
        for action in open_lanes["profile_type_review"].remaining_actions
    } == set(open_lanes["profile_type_review"].route_step_keys)
    remaining_type_assertions = [
        action
        for action in open_lanes["profile_type_review"].remaining_actions
        if action.tool_name == "stage_map_assertion_change"
        and action.semantic_move == "assert_map_type"
    ]
    assert {
        action.arguments["predicate"] for action in remaining_type_assertions
    } == {"rc:physicalType", "rc:valueType"}
    assert all(action.suggested_next_call for action in remaining_type_assertions)
    assert all(
        action.source_summary["advisory_kind"] == "profile_type_review"
        for action in remaining_type_assertions
    )
    assert review.closed_semantic_moves == ["define_value_type"]
    assert "assert_map_type" in review.remaining_semantic_moves
    assert review.closed_route_step_keys == [
        value_type_route_source["route_step_key"]
    ]
    assert set(review.remaining_route_step_keys) == set(
        open_lanes["profile_type_review"].route_step_keys
    )
    assert review.semantic_move_closure_summary.startswith(
        "Closed semantic moves: define_value_type."
    )
    assert review.executor_decision_summary["decision"] == (
        "review_or_stage_open_lanes"
    )
    assert review.executor_decision_summary["mutation_policy"] == (
        "do_not_bulk_apply"
    )
    assert review.executor_decision_summary["open_review_lane_count"] == 1
    assert review.executor_decision_summary["open_review_lanes"][0][
        "review_lane"
    ] == "profile_type_review"
    assert "assert_map_type" in review.executor_decision_summary[
        "open_review_lanes"
    ][0]["remaining_semantic_moves"]
    assert review.executor_decision_summary["open_review_lanes"][0][
        "closed_route_step_keys"
    ] == [value_type_route_source["route_step_key"]]
    executor_remaining_actions = review.executor_decision_summary[
        "open_review_lanes"
    ][0]["remaining_actions"]
    assert {
        action["arguments"]["predicate"]
        for action in executor_remaining_actions
        if action["tool_name"] == "stage_map_assertion_change"
    } == {"rc:physicalType", "rc:valueType"}
    assert set(
        review.executor_decision_summary["open_review_lanes"][0][
            "remaining_route_step_keys"
        ]
    ) == set(open_lanes["profile_type_review"].route_step_keys)
    assert review.executor_decision_summary["candidate_roles"] == {
        "profile_type_candidate": 1
    }
    candidate_guidance = review.executor_decision_summary[
        "candidate_apply_guidance"
    ][0]
    assert candidate_guidance["revision_iri"] == staged.iri
    assert candidate_guidance["apply_guidance"] == (
        "blocked_by_specific_open_lanes"
    )
    assert candidate_guidance["semantic_apply_role"] == "profile_type_candidate"
    assert candidate_guidance["blocking_open_review_lane_count"] == 1
    assert candidate_guidance["blocking_open_review_lanes"][0]["review_lane"] == (
        "profile_type_review"
    )
    assert "assert_map_type" in candidate_guidance[
        "blocking_open_review_lanes"
    ][0]["remaining_semantic_moves"]
    assert status_value_type in candidate_guidance["matched_revision_anchor_iris"]
    exported = (tmp_path / "orders-profile-type-review.md").read_text(
        encoding="utf-8"
    )
    assert "Closed route steps:" in exported
    assert value_type_route_source["route_step_key"] in exported
    assert "Remaining route steps:" in exported
    assert "### Semantic Move Closure" in exported
    assert "Closed semantic moves: define_value_type" in exported
    assert "Remaining semantic moves:" in exported
    assert "assert_map_type" in exported

    value_type_action = [
        action
        for action in advisory.suggested_next_actions
        if action.tool_name == "stage_map_assertion_change"
        and action.arguments["predicate"] == "rc:valueType"
    ][0]
    value_type_args = dict(value_type_action.arguments)
    value_type_args["supporting_patterns"] = [
        target_pattern.pattern_iri,
        implication_pattern.pattern_iri,
    ]
    staged_assertion = db.stage_map_assertion_change(**value_type_args)
    rerun_after_assertion = db.draft_profile_map_updates(dataset, evidence)
    rerun_assertion_advisory = rerun_after_assertion.type_advisories[0]
    assert rerun_assertion_advisory.pending_staged_promotion_iris == [staged.iri]
    assert rerun_assertion_advisory.pending_staged_assertion_iris == [
        staged_assertion.revision_iri
    ]
    assert rerun_assertion_advisory.pending_staged_assertion_count == 1
    assert not any(
        action.tool_name == "stage_pattern_promotion"
        for action in rerun_assertion_advisory.suggested_next_actions
    )
    assert not any(
        action.tool_name == "stage_map_assertion_change"
        for action in rerun_assertion_advisory.suggested_next_actions
    )
    pending_assertion_export = next(
        action
        for action in rerun_after_assertion.suggested_next_action_groups[
            "profile_type_review"
        ]
        if action.tool_name == "export_staged_revisions"
        and action.semantic_move == "assert_map_type"
    )
    assert pending_assertion_export.source_profile_advisory[
        "action_status"
    ] == "already_pending"
    assert pending_assertion_export.source_profile_advisory[
        "pending_staged_assertion_iris"
    ] == [staged_assertion.revision_iri]

    brief_after_assertion = db.project_brief(limit=10, profile_candidate_limit=1)
    profile_task = next(
        task
        for task in brief_after_assertion.recommended_next_tasks
        if task.task_type == "profile_review"
    )
    profile_draft = brief_after_assertion.datasets[0].profile.drafts[0]
    assert set(profile_draft.pending_staged_profile_advisory_iris) == {
        staged.iri,
        staged_assertion.revision_iri,
    }
    assert profile_draft.pending_staged_profile_advisory_count == 2
    assert profile_draft.pending_staged_profile_advisory_actions[0].tool_name == (
        "describe_staged_revision"
    )
    assert profile_task.priority == 55
    assert profile_task.suggested_next_action is not None
    assert profile_task.suggested_next_action.tool_name == "describe_staged_revision"
    assert set(profile_task.suggested_next_action.arguments.values()) & {
        staged.iri,
        staged_assertion.revision_iri,
    }
    assert "Pending staged profile advisory follow-through" in (
        profile_task.reason
    )
    assert {
        advisory["code"] for advisory in profile_task.task_advisories
    } == {"pending_staged_profile_advisory_review"}
    advisories_by_move = {
        advisory["semantic_move"]: advisory
        for advisory in profile_task.task_advisories
    }
    assert set(advisories_by_move) == {"assert_map_type", "define_value_type"}
    assert advisories_by_move["assert_map_type"][
        "pending_staged_assertion_iris"
    ] == [staged_assertion.revision_iri]
    assert advisories_by_move["define_value_type"][
        "pending_staged_promotion_iris"
    ] == [staged.iri]

    final_review = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        tmp_path / "orders-profile-type-review-final.md",
    )

    assert final_review.open_profile_review_lanes == []
    assert final_review.closed_semantic_moves == [
        "assert_map_type",
        "define_value_type",
    ]
    final_candidates = {
        candidate.revision_iri: candidate for candidate in final_review.candidates
    }
    assert staged.iri in final_candidates
    assert staged_assertion.revision_iri in final_candidates
    final_assertion_candidate = final_candidates[staged_assertion.revision_iri]
    final_route_groups = {
        group["review_lane"]: group
        for group in final_assertion_candidate.profile_route_groups
    }
    assert final_route_groups["profile_type_review"]["closed_semantic_moves"] == [
        "assert_map_type"
    ]
    assert "caveat_fallback" in final_route_groups["profile_type_review"][
        "semantic_moves"
    ]
    assert "caveat_fallback" not in final_review.remaining_semantic_moves


def test_profile_type_assertion_route_source_closes_only_selected_advisory(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    channel_column = "https://example.test/project#OrdersChannel"
    status_value_type = "https://example.test/project#StatusCodeValue"
    channel_value_type = "https://example.test/project#ChannelCodeValue"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        physical_type="rc:Varchar",
    )
    db.record_map_column(
        channel_column,
        table_iri=dataset,
        column_name="channel",
        physical_type="rc:Varchar",
    )
    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders profile with two project value types.",
        evidence_summary="Synthetic type-finding profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status carried a reviewed lifecycle code.",
                "physical_type": "rc:Varchar",
                "value_type": status_value_type,
            },
            {
                "column_iri": channel_column,
                "column_name": "channel",
                "summary": "Channel carried a reviewed acquisition code.",
                "physical_type": "rc:Varchar",
                "value_type": channel_value_type,
            },
        ],
    )
    broad_pattern = db.record_pattern(
        summary="Orders coded columns need value-type review.",
        pattern_text=(
            "Orders status and channel codes both need value-type review before "
            "profile findings become current map assertions."
        ),
        rationale="One profile review pattern intentionally supports two type lanes.",
        pattern_targets=[status_value_type, channel_value_type],
        supporting_observations=bundle.handoff_entrypoints.profile_observation_iris,
        evidence_iri=evidence,
        map_implications=[status_value_type, channel_value_type],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)
    type_actions = draft.suggested_next_action_groups["profile_type_review"]
    status_action = next(
        action
        for action in type_actions
        if action.tool_name == "stage_map_assertion_change"
        and action.arguments["subject"] == status_column
        and action.arguments["predicate"] == "rc:valueType"
    )
    channel_action = next(
        action
        for action in type_actions
        if action.tool_name == "stage_map_assertion_change"
        and action.arguments["subject"] == channel_column
        and action.arguments["predicate"] == "rc:valueType"
    )
    status_route_key = status_action.source_profile_advisory["route_group_key"]
    channel_route_key = channel_action.source_profile_advisory["route_group_key"]
    assert status_route_key != channel_route_key

    status_arguments = dict(status_action.arguments)
    status_arguments["supporting_patterns"] = [broad_pattern.pattern_iri]
    assert status_arguments["profile_route_sources"] == [
        status_action.source_profile_advisory
    ]
    staged_status = db.stage_map_assertion_change(**status_arguments)

    assert staged_status.profile_route_source_count == 1

    review = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        tmp_path / "orders-profile-type-routes.md",
    )
    candidate = next(
        candidate
        for candidate in review.candidates
        if candidate.revision_iri == staged_status.revision_iri
    )
    route_groups = {
        group["route_group_key"]: group for group in candidate.profile_route_groups
    }

    assert route_groups[status_route_key]["match_strength"] == "direct_action"
    assert route_groups[channel_route_key]["match_strength"] == "strong_support"

    open_route_keys = {
        route_group_key
        for lane in review.open_profile_review_lanes
        for route_group_key in lane.route_group_keys
    }
    assert status_route_key in open_route_keys
    assert channel_route_key in open_route_keys
    assert "assert_map_type" not in route_groups[status_route_key][
        "remaining_semantic_moves"
    ]
    assert "define_value_type" in route_groups[status_route_key][
        "remaining_semantic_moves"
    ]


def test_profile_advisories_flag_mixed_metric_and_type_promotion_support(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    status_value_type = "https://example.test/project#StatusCodeValue"
    project_metric = "https://example.test/project#StatusCompletenessScore"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        physical_type="rc:Varchar",
    )
    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders profile with shared metric and value-type evidence.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
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
                "summary": "Status used varchar storage and a project value type.",
                "physical_type": "rc:Varchar",
                "value_type": status_value_type,
            }
        ],
    )
    assert bundle.dataset_profile.pattern is not None
    pattern_iri = bundle.dataset_profile.pattern.pattern_iri
    pattern_description = db.describe_pattern(pattern_iri)
    assert {item.iri for item in pattern_description.map_implications} == {
        dataset,
        project_metric,
        status_value_type,
    }

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.metric_advisory_count == 1
    assert draft.type_advisory_count == 1
    metric_advisory = draft.metric_advisories[0]
    type_advisory = draft.type_advisories[0]
    assert [item.iri for item in metric_advisory.promotion_patterns] == [pattern_iri]
    assert [item.iri for item in type_advisory.promotion_patterns] == [pattern_iri]
    assert metric_advisory.mixed_support_pattern_count == 1
    assert type_advisory.mixed_support_pattern_count == 1
    assert [item.iri for item in metric_advisory.mixed_support_patterns] == [
        pattern_iri
    ]
    assert [item.iri for item in type_advisory.mixed_support_patterns] == [
        pattern_iri
    ]
    assert metric_advisory.mixed_support_note is not None
    assert "profile type review" in metric_advisory.mixed_support_note
    assert "Review or export" in metric_advisory.mixed_support_note
    assert type_advisory.mixed_support_note is not None
    assert "metric vocabulary review" in type_advisory.mixed_support_note
    assert "generated promotion or assertion drafts together" in (
        type_advisory.mixed_support_note
    )

    metric_promotion_action = [
        action
        for action in metric_advisory.suggested_next_actions
        if action.tool_name == "stage_pattern_promotion"
    ][0]
    type_promotion_action = [
        action
        for action in type_advisory.suggested_next_actions
        if action.tool_name == "stage_pattern_promotion"
    ][0]
    value_assertion_action = [
        action
        for action in type_advisory.suggested_next_actions
        if action.tool_name == "stage_map_assertion_change"
        and action.arguments["predicate"] == "rc:valueType"
    ][0]

    assert "Mixed support" in metric_promotion_action.reason
    assert "Mixed support" in type_promotion_action.reason
    assert "Mixed support" in value_assertion_action.reason
    assert "Mixed support" in metric_promotion_action.arguments["framings"][0][
        "review_note"
    ]
    assert "Mixed support" in type_promotion_action.arguments["framings"][0][
        "review_note"
    ]
    assert "Mixed support" in value_assertion_action.arguments["review_note"]
    assert value_assertion_action.arguments["supporting_patterns"] == [pattern_iri]
    assert "consumes_result_bindings" not in (
        value_assertion_action.source_profile_advisory
    )

    grouped_metric_action = [
        action
        for action in draft.suggested_next_action_groups[
            "metric_vocabulary_review"
        ]
        if action.tool_name == "stage_pattern_promotion"
    ][0]
    grouped_type_action = [
        action
        for action in draft.suggested_next_action_groups["profile_type_review"]
        if action.tool_name == "stage_map_assertion_change"
        and action.arguments["predicate"] == "rc:valueType"
    ][0]

    assert grouped_metric_action.source_profile_advisory["mixed_support"] == {
        "pattern_iris": [pattern_iri],
        "pattern_count": 1,
        "other_review_lanes": ["profile_type_review"],
        "note": metric_advisory.mixed_support_note,
    }
    assert grouped_type_action.source_profile_advisory["mixed_support"] == {
        "pattern_iris": [pattern_iri],
        "pattern_count": 1,
        "other_review_lanes": ["metric_vocabulary_review"],
        "note": type_advisory.mixed_support_note,
    }
    assert grouped_type_action.arguments["supporting_patterns"] == [pattern_iri]
    assert "consumes_result_bindings" not in (
        grouped_type_action.source_profile_advisory
    )
    assert draft.mixed_support_review_group_count == 1
    mixed_group = draft.mixed_support_review_groups[0]
    assert mixed_group.pattern_iris == [pattern_iri]
    assert mixed_group.pattern_count == 1
    assert mixed_group.review_lanes == [
        "metric_vocabulary_review",
        "profile_type_review",
    ]
    assert set(mixed_group.semantic_moves) == {
        "assert_map_type",
        "caveat_fallback",
        "define_metric",
        "define_value_type",
    }
    assert mixed_group.metric_advisory_indexes == [0]
    assert mixed_group.type_advisory_indexes == [0]
    assert mixed_group.action_count == len(mixed_group.route_step_keys)
    assert mixed_group.action_count == len(mixed_group.action_labels)
    assert "Compare the grouped actions" in mixed_group.note

    followthrough = db.plan_profile_followthrough(dataset, evidence)
    assert followthrough.missing_binding_keys == []
    assert "missing_binding_prerequisites" not in (
        followthrough.suggested_next_action_groups
    )
    value_type_resolution = [
        resolution
        for resolution in followthrough.action_resolutions
        if resolution.tool_name == "stage_map_assertion_change"
        and resolution.action.arguments["predicate"] == "rc:valueType"
    ][0]
    assert value_type_resolution.binding_status == "not_applicable"
    assert value_type_resolution.action.arguments["supporting_patterns"] == [
        pattern_iri
    ]
    assert value_type_resolution.action.unattended_choice_role == "primary"


def test_stage_profile_map_updates_keeps_mixed_advisory_vocabulary_out_of_map_patch(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    status_value_type = "https://example.test/project#StatusCodeValue"
    project_metric = "https://example.test/project#StatusCompletenessScore"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"

    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=10,
    )
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        physical_type="rc:Varchar",
    )
    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders profile with shared metric and value-type evidence.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        sample_size=12,
        sample_scope="All rows in the Orders table.",
        sample_method="DuckDB full-table profile.",
        row_count=12,
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
                "summary": "Status used varchar storage and a project value type.",
                "physical_type": "rc:Varchar",
                "value_type": status_value_type,
            }
        ],
    )
    pattern = db.record_pattern(
        summary="Status profile needs metric and value type vocabulary.",
        pattern_text=(
            "StatusCompletenessScore measures populated status values, while "
            "StatusCodeValue names the reviewed status domain."
        ),
        rationale="The same profile evidence supports both review lanes.",
        pattern_targets=[project_metric, status_value_type],
        supporting_observations=bundle.handoff_entrypoints.profile_observation_iris,
        evidence_iri=evidence,
        map_implications=[project_metric, status_value_type],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.metric_advisories[0].mixed_support_patterns[0].iri == (
        pattern.pattern_iri
    )
    assert draft.type_advisories[0].mixed_support_patterns[0].iri == (
        pattern.pattern_iri
    )
    row_count_recommendation = next(
        recommendation
        for recommendation in draft.recommendations
        if recommendation.kind == "dataset_row_count_snapshot"
    )

    staged = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[
            row_count_recommendation.recommendation_index
        ],
    )

    assert staged.staged_recommendation_indexes == [
        row_count_recommendation.recommendation_index
    ]
    assert staged.not_selected_recommendation_indexes == []
    assert staged.metric_advisory_count == 1
    assert staged.type_advisory_count == 1
    assert staged.staged_revision is not None
    description = db.describe_staged_revision(staged.staged_revision.revision_iri)
    patch_content = "\n".join(
        patch.content or "" for patch in description.patches
    )
    assert "rc:rowCountSnapshot 12" in patch_content
    assert project_metric not in patch_content
    assert status_value_type not in patch_content
    assert project_metric not in {anchor.iri for anchor in description.revision_anchors}
    assert status_value_type not in {
        anchor.iri for anchor in description.revision_anchors
    }

    review = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        tmp_path / "orders-mixed-support-map-review.md",
    )
    assert review.bulk_apply_allowed is False
    assert review.safe_single_apply_candidate_revision_iris == [
        staged.staged_revision.revision_iri
    ]
    assert review.semantic_apply_gate_counts["safe_single_apply_candidates"] == 1
    assert review.executor_decision_summary["decision"] == (
        "apply_one_safe_single_after_review"
    )
    assert review.executor_decision_summary["mutation_policy"] == (
        "apply_at_most_one_then_recheck"
    )
    assert review.executor_decision_summary["open_review_lane_count"] > 0
    candidate = review.candidates[0]
    assert candidate.semantic_apply_role == (
        "profile_map_update_with_semantic_context"
    )
    assert candidate.apply_cardinality == "single_after_review_then_recheck"
    assert candidate.safe_single_apply_candidate is True


def test_unmapped_profile_type_advisory_points_to_column_shell_recommendation(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    channel_column = "https://example.test/project#OrdersChannel"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"

    db.record_map_dataset(dataset, label="Orders", is_table=True)

    def record_unmapped_type_profile() -> None:
        db.record_profile_bundle(
            dataset,
            dataset_summary="Orders were profiled without changing the map.",
            evidence_summary="Synthetic type-finding profile run.",
            evidence_sources=["test://orders-profile"],
            shared_evidence_iri=evidence,
            update_map_snapshot=False,
            column_defaults={"update_map_column": False},
            column_profiles=[
                {
                    "column_iri": channel_column,
                    "column_name": "channel",
                    "summary": "Channel was observed as varchar.",
                    "physical_type": "rc:Varchar",
                }
            ],
        )

    record_unmapped_type_profile()
    record_unmapped_type_profile()

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.recommendation_count == 2
    assert [recommendation.kind for recommendation in draft.recommendations] == [
        "unmapped_profiled_column",
        "unmapped_profiled_column",
    ]
    assert draft.type_advisory_count == 2
    assert draft.type_advisory_status_counts == {
        "type_finding_unmapped_column": 2,
    }
    type_observations = {
        advisory.profile_observation_iri for advisory in draft.type_advisories
    }
    for advisory in draft.type_advisories:
        assert advisory.map_column_found is False
        assert advisory.duplicate_count == 2
        assert advisory.duplicate_advisory_indexes == [0, 1]
        assert set(advisory.duplicate_profile_observation_iris) == (
            type_observations
        )
        assert advisory.related_recommendation_indexes == [0, 1]
        assert advisory.related_recommendation_kinds == [
            "unmapped_profiled_column"
        ]
        assert "recommendation index(es) 0, 1 first" in advisory.routing_note
        assert "column shell" in advisory.routing_note
        assert "duplicate group" in advisory.routing_note
        assert "representative stage_profile_map_updates action" in (
            advisory.routing_note
        )
        assert [action.tool_name for action in advisory.suggested_next_actions] == [
            "get_context_graph",
            "record_pattern",
            "stage_systematisation",
        ]
    assert [action.tool_name for action in draft.suggested_next_actions] == [
        "stage_profile_map_updates",
        "get_context_graph",
        "record_pattern",
        "stage_systematisation",
    ]
    assert list(draft.suggested_next_action_groups) == [
        "profile_map_updates",
        "profile_type_review",
    ]
    assert [
        action.tool_name
        for action in draft.suggested_next_action_groups["profile_map_updates"]
    ] == ["stage_profile_map_updates"]
    assert [
        action.tool_name
        for action in draft.suggested_next_action_groups["profile_type_review"]
    ] == ["get_context_graph", "record_pattern", "stage_systematisation"]

    staged = db.stage_profile_map_updates(
        **draft.suggested_next_action_groups["profile_map_updates"][0].arguments
    )
    assert staged.staged_revision is not None
    followthrough_note = (
        "After applying staged unmapped column shells, rerun "
        "draft_profile_map_updates for the same dataset and evidence"
    )
    assert followthrough_note in staged.review_note
    described = db.describe_staged_revision(staged.staged_revision.revision_iri)
    assert described.review_note is not None
    assert followthrough_note in described.review_note

    db.apply_staged_revision(staged.staged_revision.revision_iri)
    rerun = db.draft_profile_map_updates(dataset, evidence)

    assert rerun.recommendation_count == 0
    assert rerun.type_advisory_status_counts == {
        "type_finding_missing_map_type": 2,
    }
    assert [
        action.tool_name
        for action in rerun.suggested_next_action_groups["profile_type_review"]
    ] == [
        "get_context_graph",
        "record_pattern",
        "stage_systematisation",
        "stage_map_assertion_change",
    ]


def test_profile_type_advisory_duplicate_actions_preserve_support(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
    )

    def record_repeated_type_profile() -> None:
        db.record_profile_bundle(
            dataset,
            dataset_summary="Orders were profiled without changing the map.",
            evidence_summary="Repeated type-finding profile run.",
            evidence_sources=["test://orders-profile"],
            shared_evidence_iri=evidence,
            update_map_snapshot=False,
            column_defaults={"update_map_column": False},
            column_profiles=[
                {
                    "column_iri": status_column,
                    "column_name": "status",
                    "summary": "Status looked varchar in the profile.",
                    "physical_type": "rc:Varchar",
                }
            ],
        )

    record_repeated_type_profile()
    record_repeated_type_profile()

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.type_advisory_count == 2
    assert draft.representative_type_advisory_indexes == [0]
    assert draft.type_advisory_status_counts == {
        "type_finding_missing_map_type": 2,
    }
    type_group_key = draft.type_advisories[0].duplicate_group_key
    type_observations = {
        advisory.profile_observation_iri for advisory in draft.type_advisories
    }
    for index, advisory in enumerate(draft.type_advisories):
        assert advisory.type_advisory_index == index
        assert advisory.duplicate_group_key == type_group_key
        assert advisory.duplicate_group_key.startswith("profile-type-advisory:")
        assert advisory.duplicate_count == 2
        assert advisory.duplicate_advisory_indexes == [0, 1]
        assert set(advisory.duplicate_profile_observation_iris) == type_observations
        stage_action = [
            action
            for action in advisory.suggested_next_actions
            if action.tool_name == "stage_map_assertion_change"
        ][0]
        assert set(stage_action.arguments["supporting_observations"]) == (
            type_observations
        )

    assert [action.tool_name for action in draft.suggested_next_actions] == [
        "get_context_graph",
        "record_pattern",
        "stage_systematisation",
        "stage_map_assertion_change",
    ]
    top_stage_action = draft.suggested_next_actions[3]
    assert set(top_stage_action.arguments["supporting_observations"]) == (
        type_observations
    )


def test_profile_map_update_duplicate_groups_preserve_representative_support(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Payments"
    status_column = "https://example.test/project#PaymentsStatus"
    settlement_column = "https://example.test/project#PaymentsSettlementMethod"
    evidence = "https://example.test/project#PaymentsProfileRunEvidence"
    project_metric = "https://example.test/project#CompletenessRatio"

    db.record_map_dataset(
        dataset,
        label="Payments",
        is_table=True,
        row_count_snapshot=10,
    )
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        nullable=False,
    )

    def record_repeated_profile(settlement_sample_scope: str) -> None:
        db.record_profile_bundle(
            dataset,
            dataset_summary="Payments were profiled with a full-table scan.",
            evidence_summary="Repeated profile run over Payments.",
            evidence_sources=["test://payments-profile"],
            shared_evidence_iri=evidence,
            sample_size=12,
            sample_scope="All rows in the test Payments table.",
            sample_method="DuckDB full-table aggregate profile.",
            row_count=12,
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
                    "null_count": 2,
                },
                {
                    "column_iri": settlement_column,
                    "column_name": "settlement_method",
                    "summary": "Settlement method was observed but is unmapped.",
                    "sample_scope": settlement_sample_scope,
                },
            ],
        )

    record_repeated_profile("All rows in the test Payments table.")
    record_repeated_profile("Repeated pass over the same Payments population.")

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.recommendation_count == 6
    recommendation_groups = {}
    for recommendation in draft.recommendations:
        recommendation_groups.setdefault(
            recommendation.duplicate_group_key,
            [],
        ).append(recommendation)
    assert sorted(len(group) for group in recommendation_groups.values()) == [
        2,
        2,
        2,
    ]
    assert {
        group[0].kind for group in recommendation_groups.values()
    } == {
        "dataset_row_count_snapshot",
        "column_nullable",
        "unmapped_profiled_column",
    }
    unmapped_group = [
        group
        for group in recommendation_groups.values()
        if group[0].kind == "unmapped_profiled_column"
    ][0]
    assert {item.sample_scope for item in unmapped_group} == {
        "All rows in the test Payments table.",
        "Repeated pass over the same Payments population.",
    }
    for group_key, group in recommendation_groups.items():
        indexes = [recommendation.recommendation_index for recommendation in group]
        observations = [
            recommendation.profile_observation_iri for recommendation in group
        ]
        assert group_key.startswith("profile-map-update:")
        for recommendation in group:
            assert recommendation.duplicate_group_key == group_key
            assert recommendation.duplicate_count == 2
            assert recommendation.duplicate_recommendation_indexes == indexes
            assert set(recommendation.duplicate_profile_observation_iris) == set(
                observations
            )

    assert draft.metric_advisory_count == 2
    metric_group_key = draft.metric_advisories[0].duplicate_group_key
    metric_observations = {
        advisory.profile_observation_iri for advisory in draft.metric_advisories
    }
    for index, advisory in enumerate(draft.metric_advisories):
        assert advisory.metric_advisory_index == index
        assert advisory.duplicate_group_key == metric_group_key
        assert advisory.duplicate_group_key.startswith("profile-metric-advisory:")
        assert advisory.duplicate_count == 2
        assert advisory.duplicate_advisory_indexes == [0, 1]
        assert set(advisory.duplicate_profile_observation_iris) == metric_observations

    representative_indexes = sorted(
        group[0].recommendation_index for group in recommendation_groups.values()
    )
    expected_support = {
        observation_iri
        for index in representative_indexes
        for observation_iri in draft.recommendations[
            index
        ].duplicate_profile_observation_iris
    }

    staged = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=representative_indexes,
    )

    assert staged.staged_recommendation_indexes == representative_indexes
    assert staged.status_counts == {"staged": 3, "skipped": 0, "not_selected": 3}
    for item in staged.items:
        assert set(item.supporting_profile_observation_iris) == set(
            draft.recommendations[
                item.recommendation_index
            ].duplicate_profile_observation_iris
        )
    assert staged.staged_revision is not None
    described = db.describe_staged_revision(staged.staged_revision.revision_iri)
    described_support = {item.iri for item in described.supporting_observations}
    assert described_support == expected_support
    assert len(described_support) == 6
    assert draft.representative_recommendation_indexes == representative_indexes
    assert draft.suggested_next_actions[0].arguments == {
        "dataset_iri": dataset,
        "evidence_iri": evidence,
        "accepted_recommendation_indexes": representative_indexes,
    }


def test_profile_map_update_scalar_conflicts_are_not_default_stageable(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/profile-conflict#"
    dataset = f"{base}Tickets"
    status_column = f"{base}TicketsStatus"
    risk_column = f"{base}TicketsRiskScore"
    evidence = f"{base}TicketsProfileEvidence"

    db.record_map_dataset(
        dataset,
        label="Tickets",
        is_table=True,
        row_count_snapshot=1000,
    )
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
    )

    for index, (row_count, status_null_count) in enumerate(
        (
            (1200, 0),
            (1210, 12),
        )
    ):
        if index == 0:
            sample_size = row_count
            sample_scope = "All rows in the local Tickets table."
            sample_method = "DuckDB full-table profile."
        else:
            sample_size = 100
            sample_scope = "Sampled rows from the local Tickets table."
            sample_method = "DuckDB sampled profile."
        column_profiles = [
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status nullability came from the profile.",
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
        db.record_profile_bundle(
            dataset,
            dataset_summary=f"Tickets full profile pass {index}.",
            evidence_summary="Tickets full profile evidence.",
            evidence_sources=[f"test://tickets/full/{index}"],
            shared_evidence_iri=evidence,
            sample_size=sample_size,
            sample_scope=sample_scope,
            sample_method=sample_method,
            row_count=row_count,
            update_map_snapshot=False,
            column_defaults={"update_map_column": False},
            column_profiles=column_profiles,
        )

    draft = db.draft_profile_map_updates(dataset, evidence)

    row_count_recommendations = [
        recommendation
        for recommendation in draft.recommendations
        if recommendation.kind == "dataset_row_count_snapshot"
    ]
    nullable_recommendations = [
        recommendation
        for recommendation in draft.recommendations
        if recommendation.kind == "column_nullable"
    ]
    unmapped_recommendations = [
        recommendation
        for recommendation in draft.recommendations
        if recommendation.kind == "unmapped_profiled_column"
    ]

    assert {item.observed_value for item in row_count_recommendations} == {
        1200,
        1210,
    }
    assert {item.observed_value for item in nullable_recommendations} == {
        False,
        True,
    }
    for recommendation in [
        *row_count_recommendations,
        *nullable_recommendations,
    ]:
        assert recommendation.default_stageable is False
        assert (
            "Same-evidence profile recommendations propose conflicting values"
            in (recommendation.default_skip_reason or "")
        )
    assert len(unmapped_recommendations) == 1
    assert unmapped_recommendations[0].default_stageable is True
    assert draft.scalar_conflict_group_count == 2
    assert [group.kind for group in draft.scalar_conflict_groups] == [
        "dataset_row_count_snapshot",
        "column_nullable",
    ]
    row_count_group = draft.scalar_conflict_groups[0]
    assert row_count_group.resource.iri == dataset
    assert row_count_group.predicate == "rc:rowCountSnapshot"
    assert row_count_group.current_value == 1000
    assert {option.observed_value for option in row_count_group.options} == {
        1200,
        1210,
    }
    row_count_options_by_value = {
        option.observed_value: option for option in row_count_group.options
    }
    row_count_recommendations_by_value = {
        recommendation.observed_value: recommendation
        for recommendation in row_count_recommendations
    }
    assert row_count_options_by_value[1200].recommendation_contexts == [
        ProfileScalarConflictRecommendationContext(
            recommendation_index=row_count_options_by_value[
                1200
            ].representative_recommendation_index,
            profile_observation_iri=(
                row_count_recommendations_by_value[1200].profile_observation_iri
            ),
            observed_count=1200,
            sample_size=1200,
            sample_scope="All rows in the local Tickets table.",
            sample_method="DuckDB full-table profile.",
            profile_row_count=1200,
            basis="full_scan",
            confidence="high",
        )
    ]
    assert row_count_options_by_value[1210].recommendation_contexts == [
        ProfileScalarConflictRecommendationContext(
            recommendation_index=row_count_options_by_value[
                1210
            ].representative_recommendation_index,
            profile_observation_iri=(
                row_count_recommendations_by_value[1210].profile_observation_iri
            ),
            observed_count=1210,
            sample_size=100,
            sample_scope="Sampled rows from the local Tickets table.",
            sample_method="DuckDB sampled profile.",
            profile_row_count=1210,
            basis="sample",
            confidence="medium",
        )
    ]
    for option in row_count_group.options:
        assert option.suggested_next_action.tool_name == "stage_profile_map_updates"
        assert option.suggested_next_action.arguments == {
            "dataset_iri": dataset,
            "evidence_iri": evidence,
            "accepted_recommendation_indexes": [
                option.representative_recommendation_index
            ],
        }
    nullable_group = draft.scalar_conflict_groups[1]
    assert nullable_group.resource.iri == status_column
    assert nullable_group.predicate == "rc:nullable"
    assert {option.observed_value for option in nullable_group.options} == {
        False,
        True,
    }

    default_action = draft.suggested_next_action_groups["profile_map_updates"][0]
    assert default_action.arguments == {
        "dataset_iri": dataset,
        "evidence_iri": evidence,
        "accepted_recommendation_indexes": [
            unmapped_recommendations[0].recommendation_index
        ],
    }
    scalar_conflict_actions = draft.suggested_next_action_groups[
        "profile_scalar_conflict_review"
    ]
    assert [
        action.source_scalar_conflict["kind"]
        for action in scalar_conflict_actions
    ] == [
        "dataset_row_count_snapshot",
        "dataset_row_count_snapshot",
        "column_nullable",
        "column_nullable",
    ]
    assert all(
        action.tool_name == "stage_profile_map_updates"
        for action in scalar_conflict_actions
    )
    assert all(
        action.source_scalar_conflict["selection_rule"]
        == "choose_at_most_one_option_per_conflict_group"
        for action in scalar_conflict_actions
    )
    assert all(
        action.source_scalar_conflict["route_group_key"].startswith(
            "profile_scalar_conflict_review:"
        )
        for action in scalar_conflict_actions
    )
    assert all(
        action.source_scalar_conflict["route_step_key"].startswith(
            "profile-route-step:"
        )
        for action in scalar_conflict_actions
    )
    assert len(
        {
            action.source_scalar_conflict["route_step_key"]
            for action in scalar_conflict_actions
        }
    ) == len(scalar_conflict_actions)
    row_count_action_sources = {
        action.source_scalar_conflict["observed_value"]: action.source_scalar_conflict
        for action in scalar_conflict_actions
        if action.source_scalar_conflict["kind"] == "dataset_row_count_snapshot"
    }
    assert row_count_action_sources[1210]["recommendation_contexts"] == [
        to_jsonable(row_count_options_by_value[1210].recommendation_contexts[0])
    ]

    conflicting_scalar_indexes = [
        recommendation.recommendation_index
        for recommendation in [
            *row_count_recommendations,
            *nullable_recommendations,
        ]
    ]
    conflicting_stage = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=conflicting_scalar_indexes,
    )
    assert conflicting_stage.staged_revision is None
    assert conflicting_stage.status_counts == {
        "staged": 0,
        "skipped": 4,
        "not_selected": 1,
    }
    assert conflicting_stage.skipped_recommendation_indexes == (
        conflicting_scalar_indexes
    )
    assert all(
        "Same-evidence profile recommendations propose conflicting values"
        in (item.reason or "")
        for item in conflicting_stage.items
        if item.status == "skipped"
    )

    chosen_row_count = next(
        recommendation
        for recommendation in row_count_recommendations
        if recommendation.observed_value == 1200
    )
    chosen_nullable = next(
        recommendation
        for recommendation in nullable_recommendations
        if recommendation.observed_value is True
    )
    chosen_stage = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[
            chosen_row_count.recommendation_index,
            chosen_nullable.recommendation_index,
        ],
    )

    assert chosen_stage.staged_recommendation_indexes == [
        chosen_row_count.recommendation_index,
        chosen_nullable.recommendation_index,
    ]
    assert chosen_stage.status_counts == {
        "staged": 2,
        "skipped": 0,
        "not_selected": 3,
    }
    assert chosen_stage.staged_revision is not None
    assert db.check_staged_revision_apply(
        chosen_stage.staged_revision.revision_iri
    ).status == "ready"
    db.apply_staged_revision(chosen_stage.staged_revision.revision_iri)

    post_apply_draft = db.draft_profile_map_updates(dataset, evidence)
    post_apply_scalar_recommendations = [
        recommendation
        for recommendation in post_apply_draft.recommendations
        if recommendation.kind
        in {"dataset_row_count_snapshot", "column_nullable"}
    ]
    sibling_row_count_values = {
        recommendation.observed_value
        for recommendation in row_count_recommendations
        if recommendation.observed_value != chosen_row_count.observed_value
    }
    assert {
        recommendation.observed_value
        for recommendation in post_apply_scalar_recommendations
    } == {*sibling_row_count_values, False}
    assert all(
        recommendation.default_stageable is False
        for recommendation in post_apply_scalar_recommendations
    )
    assert all(
        "One value already matches the current map"
        in (recommendation.default_skip_reason or "")
        for recommendation in post_apply_scalar_recommendations
    )
    assert post_apply_draft.scalar_conflict_group_count == 2
    post_apply_conflict_actions = post_apply_draft.suggested_next_action_groups[
        "profile_scalar_conflict_review"
    ]
    assert all(
        action.tool_name == "describe_profile_run"
        for action in post_apply_conflict_actions
    )
    assert {
        action.source_scalar_conflict["selection_rule"]
        for action in post_apply_conflict_actions
    } == {"current_value_already_chosen_review_before_replacing"}

    post_apply_blocked_stage = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[
            recommendation.recommendation_index
            for recommendation in post_apply_scalar_recommendations
        ],
    )
    assert post_apply_blocked_stage.staged_revision is None
    assert post_apply_blocked_stage.status_counts == {
        "staged": 0,
        "skipped": 2,
        "not_selected": 1,
    }
    assert all(
        "One value already matches the current map" in (item.reason or "")
        for item in post_apply_blocked_stage.items
        if item.status == "skipped"
    )

    row_count_flip = next(
        recommendation
        for recommendation in post_apply_scalar_recommendations
        if recommendation.kind == "dataset_row_count_snapshot"
    )
    nullable_flip = next(
        recommendation
        for recommendation in post_apply_scalar_recommendations
        if recommendation.kind == "column_nullable"
    )
    legacy_flip = db.stage_graph_revision(
        summary="Legacy post-apply scalar flip",
        rationale=(
            "Simulate a staged profile map update created before current-equal "
            "scalar conflict siblings were guarded."
        ),
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    <{dataset}> rc:rowCountSnapshot {row_count_flip.observed_value} .
                    <{status_column}> rc:nullable false .
                """,
            }
        ],
        removals=[
            {
                "graph": "map",
                "content": f"""
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    <{dataset}> rc:rowCountSnapshot {chosen_row_count.observed_value} .
                    <{status_column}> rc:nullable true .
                """,
            }
        ],
        evidence=[evidence],
        supporting_observations=[
            row_count_flip.profile_observation_iri,
            nullable_flip.profile_observation_iri,
        ],
        revision_anchors=[dataset, status_column],
        review_note=(
            "Generated by stage_profile_map_updates. Legacy fixture for a "
            "post-apply scalar conflict flip."
        ),
    )
    route_group_key = db._profile_route_group_key(
        "profile_map_updates",
        ["legacy-post-apply-scalar-flip", dataset, status_column],
    )
    db._record_profile_insight_route_sources(
        legacy_flip.revision_iri,
        [
            {
                "review_lane": "profile_map_updates",
                "direct_review_lane": "profile_map_updates",
                "route_group_key": route_group_key,
                "route_step_key": "profile-route-step:legacy-post-apply-flip",
                "evidence_iri": evidence,
                "profile_evidence_iri": evidence,
                "recommendation_indexes": [
                    row_count_flip.recommendation_index,
                    nullable_flip.recommendation_index,
                ],
                "duplicate_profile_observation_iris": [
                    row_count_flip.profile_observation_iri,
                    nullable_flip.profile_observation_iri,
                ],
                "route_anchor_iris": [dataset, status_column],
                "route_pattern_iris": [],
                "action_status": "available",
            }
        ],
    )

    review = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        tmp_path / "post-apply-scalar-flip-review.md",
        revision_iris=[legacy_flip.revision_iri],
    )

    assert review.bulk_apply_allowed is False
    assert review.safe_single_apply_candidate_revision_iris == []
    assert review.semantic_apply_gate_blocking_reasons == [
        "semantic_or_support_candidate_present",
        "open_profile_review_lanes_present",
    ]
    candidate = review.candidates[0]
    assert candidate.semantic_apply_role == (
        "profile_map_update_with_semantic_context"
    )
    assert candidate.safe_single_apply_candidate is False
    assert "profile_scalar_conflict_review" in {
        group["review_lane"] for group in candidate.profile_route_groups
    }


def test_profile_map_update_query_blocker_routes_before_default_stage_action(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/profile-query#"
    dataset = f"{base}Tickets"
    status_column = f"{base}TicketsStatus"
    risk_column = f"{base}TicketsRiskScore"
    evidence = f"{base}TicketsProfileEvidence"

    db.record_map_dataset(
        dataset,
        label="Tickets",
        is_table=True,
        row_count_snapshot=1000,
        path_templates=["tickets/date={date}/*.parquet"],
    )
    db.record_map_physical_layout(
        f"{base}TicketsParquetLayout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
        datasets=[dataset],
    )
    db.record_map_column(
        status_column,
        table_iri=dataset,
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
        db.record_profile_bundle(
            dataset,
            dataset_summary=f"Tickets full profile pass {index}.",
            evidence_summary="Tickets full profile evidence.",
            evidence_sources=[f"test://tickets/full/{index}"],
            shared_evidence_iri=evidence,
            sample_size=row_count,
            sample_scope="All rows in the local Tickets table.",
            sample_method="DuckDB full-table profile.",
            row_count=row_count,
            update_map_snapshot=False,
            column_defaults={"update_map_column": False},
            column_profiles=column_profiles,
        )

    query_context = db.describe_query_context(dataset)
    draft = db.draft_profile_map_updates(dataset, evidence)

    assert query_context.readiness == "insufficient_metadata"
    assert "missing_storage_access" in [
        issue.code for issue in query_context.issues
    ]
    assert [group for group in draft.suggested_next_action_groups] == [
        "query_context_review",
        "profile_map_updates",
        "profile_scalar_conflict_review",
    ]
    query_action = draft.suggested_next_action_groups["query_context_review"][0]
    assert query_action.tool_name == "describe_query_context"
    assert query_action.arguments == {"iri": dataset}
    assert query_action.source_query_context["readiness"] == (
        "insufficient_metadata"
    )
    assert query_action.source_query_context["blocking_issue_codes"] == [
        "missing_storage_access"
    ]
    assert query_action.source_query_context["evidence_iri"] == evidence
    assert query_action.source_query_context["profile_evidence_iri"] == evidence
    assert query_action.source_query_context["route_anchor_iris"] == [dataset]
    assert query_action.source_query_context["route_group_key"].startswith(
        "query_context_review:"
    )
    assert query_action.source_query_context["route_step_key"].startswith(
        "profile-route-step:"
    )
    assert query_action.source_query_context[
        "suggested_repair_action_group_count"
    ] == 1
    assert draft.suggested_next_actions[0] == query_action
    assert draft.suggested_next_actions[1].tool_name == "stage_profile_map_updates"
    assert draft.suggested_next_actions[1].arguments == {
        "dataset_iri": dataset,
        "evidence_iri": evidence,
        "accepted_recommendation_indexes": [4],
    }
    assert "query_context_review" in draft.review_note

    staged_map = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[4],
    )
    review = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        tmp_path / "tickets-query-review.md",
        revision_iris=[staged_map.staged_revision.revision_iri],
    )
    open_lanes = {
        lane.review_lane: lane for lane in review.open_profile_review_lanes
    }
    assert "query_context_review" in open_lanes
    query_lane = open_lanes["query_context_review"]
    assert "describe_query_context" in query_lane.next_step
    assert "query/storage repair" in query_lane.next_step
    summary_query_lane = next(
        lane
        for lane in review.executor_decision_summary["open_review_lanes"]
        if lane["review_lane"] == "query_context_review"
    )
    assert summary_query_lane["next_step"] == query_lane.next_step
    exported = (tmp_path / "tickets-query-review.md").read_text(
        encoding="utf-8"
    )
    assert "Next step" in exported
    assert "describe_query_context" in exported


def test_profile_map_update_logical_only_dataset_omits_query_context_lane(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/profile-logical#"
    dataset = f"{base}Customers"
    evidence = f"{base}CustomersProfileEvidence"

    db.record_map_dataset(
        dataset,
        label="Customers",
        is_table=True,
        row_count_snapshot=100,
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Customers logical profile pass.",
        evidence_summary="Customers full profile evidence.",
        evidence_sources=["test://customers/full"],
        shared_evidence_iri=evidence,
        sample_size=120,
        sample_scope="All rows in the logical Customers table.",
        sample_method="DuckDB full-table profile.",
        row_count=120,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
    )

    query_context = db.describe_query_context(dataset)
    draft = db.draft_profile_map_updates(dataset, evidence)

    assert query_context.readiness == "insufficient_metadata"
    assert "missing_storage_access" in [
        issue.code for issue in query_context.issues
    ]
    assert list(draft.suggested_next_action_groups) == [
        "profile_map_updates",
    ]
    assert draft.suggested_next_actions
    assert draft.suggested_next_actions[0].tool_name == "stage_profile_map_updates"
    assert "query_context_review" not in draft.suggested_next_action_groups
    assert "query_context_review" not in draft.review_note


def test_profile_map_update_scalar_only_conflict_exposes_choose_one_options(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/profile-conflict#"
    dataset = f"{base}Invoices"
    evidence = f"{base}InvoicesProfileEvidence"

    db.record_map_dataset(
        dataset,
        label="Invoices",
        is_table=True,
        row_count_snapshot=100,
    )
    for index, row_count in enumerate((120, 120, 121)):
        db.record_profile_bundle(
            dataset,
            dataset_summary=f"Invoices full profile pass {index}.",
            evidence_summary="Invoices full profile evidence.",
            evidence_sources=[f"test://invoices/full/{index}"],
            shared_evidence_iri=evidence,
            sample_size=row_count,
            sample_scope="All rows in the local Invoices table.",
            sample_method="DuckDB full-table profile.",
            row_count=row_count,
            update_map_snapshot=False,
            column_defaults={"update_map_column": False},
        )

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.recommendation_count == 3
    assert all(
        recommendation.default_stageable is False
        for recommendation in draft.recommendations
    )
    assert list(draft.suggested_next_action_groups) == [
        "profile_scalar_conflict_review"
    ]
    conflict_actions = draft.suggested_next_action_groups[
        "profile_scalar_conflict_review"
    ]
    assert len(conflict_actions) == 2
    assert draft.suggested_next_call_groups["profile_scalar_conflict_review"] == [
        action.call for action in conflict_actions
    ]
    assert draft.suggested_next_actions == []
    assert draft.scalar_conflict_group_count == 1
    conflict_group = draft.scalar_conflict_groups[0]
    assert conflict_group.kind == "dataset_row_count_snapshot"
    assert conflict_group.resource.iri == dataset
    assert conflict_group.current_value == 100
    assert conflict_group.option_count == 2
    options_by_value = {
        option.observed_value: option for option in conflict_group.options
    }
    assert set(options_by_value) == {120, 121}
    duplicate_option = options_by_value[120]
    duplicate_option_index = next(
        index
        for index, option in enumerate(conflict_group.options)
        if option.observed_value == duplicate_option.observed_value
    )
    assert len(duplicate_option.duplicate_recommendation_indexes) == 2
    assert len(duplicate_option.duplicate_profile_observation_iris) == 2
    assert duplicate_option.suggested_next_action.arguments == {
        "dataset_iri": dataset,
        "evidence_iri": evidence,
        "accepted_recommendation_indexes": [
            duplicate_option.representative_recommendation_index
        ],
    }
    conflict_review_action = next(
        action
        for action in conflict_actions
        if action.source_scalar_conflict["observed_value"]
        == duplicate_option.observed_value
    )
    assert conflict_review_action.arguments == (
        duplicate_option.suggested_next_action.arguments
    )
    conflict_source = dict(conflict_review_action.source_scalar_conflict)
    route_group_key = conflict_source.pop("route_group_key")
    route_step_key = conflict_source.pop("route_step_key")
    assert route_group_key.startswith("profile_scalar_conflict_review:")
    assert route_step_key.startswith("profile-route-step:")
    assert conflict_source == {
        "review_lane": "profile_scalar_conflict_review",
        "selection_rule": "choose_at_most_one_option_per_conflict_group",
        "conflict_group_index": 0,
        "evidence_iri": evidence,
        "resource_iri": dataset,
        "resource_label": "Invoices",
        "predicate": "rc:rowCountSnapshot",
        "kind": "dataset_row_count_snapshot",
        "current_value": 100,
        "option_index": duplicate_option_index,
        "option_count": 2,
        "observed_value": 120,
        "representative_recommendation_index": (
            duplicate_option.representative_recommendation_index
        ),
        "recommendation_indexes": duplicate_option.recommendation_indexes,
        "duplicate_recommendation_indexes": (
            duplicate_option.duplicate_recommendation_indexes
        ),
        "duplicate_profile_observation_iris": (
            duplicate_option.duplicate_profile_observation_iris
        ),
        "recommendation_contexts": to_jsonable(
            duplicate_option.recommendation_contexts
        ),
        "review_note": conflict_group.review_note,
    }

    staged = db.stage_profile_map_updates(
        **duplicate_option.suggested_next_action.arguments
    )

    assert staged.staged_recommendation_indexes == [
        duplicate_option.representative_recommendation_index
    ]
    assert staged.status_counts == {
        "staged": 1,
        "skipped": 0,
        "not_selected": 2,
    }
    assert staged.staged_revision is not None
    described = db.describe_staged_revision(staged.staged_revision.revision_iri)
    assert {
        item.iri for item in described.supporting_observations
    } == set(duplicate_option.duplicate_profile_observation_iris)
    assert db.check_staged_revision_apply(
        staged.staged_revision.revision_iri
    ).status == "ready"

    export_path = tmp_path / "scalar-profile-insight-review.md"
    review = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        export_path,
        revision_iris=[staged.staged_revision.revision_iri],
    )

    assert review.open_profile_review_lanes == []
    assert review.candidate_count == 1
    candidate = review.candidates[0]
    route_groups_by_lane = {
        group["review_lane"]: group for group in candidate.profile_route_groups
    }
    assert route_groups_by_lane["profile_scalar_conflict_review"][
        "match_strength"
    ] == "direct_action"
    assert "profile_scalar_conflict_review (direct_action)" in export_path.read_text(
        encoding="utf-8"
    )


def test_draft_profile_map_updates_reports_defined_project_metric_advisory(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"
    project_metric = "https://example.test/project#CompletenessScore"
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=100,
    )
    db.replace_graph_triples(
        "ontology",
        additions=f"""
            @prefix metric: <https://example.test/project#> .
            @prefix rc: <https://richcanopy.org/ns/rc#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            <{project_metric}> a rc:ProfileMetricKind ;
                rdfs:label "Completeness score" ;
                rdfs:comment "Share of records with complete required fields." .
        """,
        allow_count_change=True,
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Orders profile with a project metric.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        row_count=100,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": project_metric,
                "value": "0.99",
                "datatype": "xsd:decimal",
            }
        ],
        column_defaults={"update_map_column": False},
    )

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.recommendations == []
    assert draft.recommendation_count == 0
    assert draft.status == "profile evidence captured; metric context only"
    assert len(draft.metric_advisories) == 1
    assert draft.metric_advisory_count == 1
    assert draft.metric_advisory_status_counts == {
        "project_metric_defined": 1,
    }
    advisory = draft.metric_advisories[0]
    assert advisory.advisory_status == "project_metric_defined"
    assert advisory.definition_found is True
    assert advisory.definition is not None
    assert advisory.definition.iri == project_metric
    assert advisory.definition.label == "Completeness score"
    assert [action.tool_name for action in advisory.suggested_next_actions] == [
        "get_context_graph",
        "describe_resource",
    ]
    assert [action.tool_name for action in draft.suggested_next_actions] == [
        "get_context_graph",
        "describe_resource",
    ]
    assert draft.suggested_next_calls[0].startswith("get_context_graph(")
    assert advisory.suggested_next_actions[1].arguments == {
        "iri": project_metric,
        "graph": "ontology",
    }


def test_draft_profile_map_updates_routes_metric_promotion_pattern(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"
    project_metric = "https://example.test/project#CompletenessScore"
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=100,
    )
    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders profile with an undefined project metric.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        row_count=100,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": project_metric,
                "value": "0.99",
                "datatype": "xsd:decimal",
            }
        ],
        column_defaults={"update_map_column": False},
    )
    pattern = db.record_pattern(
        summary="Orders completeness score needs vocabulary.",
        pattern_text=(
            "The Orders profile uses a reusable completeness score that needs "
            "a project metric definition before comparison."
        ),
        rationale="The pattern and profile run share one evidence resource.",
        pattern_targets=[dataset],
        supporting_observations=(
            bundle.handoff_entrypoints.profile_observation_iris
        ),
        evidence_iri=evidence,
        map_implications=[project_metric],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.recommendation_count == 0
    advisory = draft.metric_advisories[0]
    assert advisory.advisory_status == "project_metric_undefined"
    assert advisory.promotion_pattern_count == 1
    assert [item.iri for item in advisory.promotion_patterns] == [
        pattern.pattern_iri
    ]
    assert [action.tool_name for action in advisory.suggested_next_actions] == [
        "get_context_graph",
        "list_entities",
        "stage_systematisation",
        "describe_pattern",
        "stage_pattern_promotion",
    ]
    fallback_action = advisory.suggested_next_actions[2]
    assert fallback_action.arguments["profile_route_sources"] == [
        fallback_action.source_profile_advisory
    ]
    assert fallback_action.arguments["supporting_observations"] == [
        advisory.profile_observation_iri
    ]
    assert fallback_action.arguments["evidence"] == [evidence]
    assert fallback_action.arguments["framings"][0]["graph"] == "patterns"
    assert "rc:supportingObservation" in (
        fallback_action.arguments["framings"][0]["content"]
    )
    staged_fallback = db.stage_systematisation(**fallback_action.arguments)
    assert staged_fallback.profile_route_source_count == 1
    fallback_staged_iri = staged_fallback.staged_revisions[0].revision_iri
    assert advisory.suggested_next_actions[3].arguments == {
        "iri": pattern.pattern_iri
    }
    promotion_action = advisory.suggested_next_actions[4]
    promotion_args = promotion_action.arguments
    assert promotion_action.mcp_tool_name == "doxabase.stage_pattern_promotion"
    assert promotion_args["patterns"] == [pattern.pattern_iri]
    assert promotion_args["anchors"] == [project_metric]
    assert promotion_args["evidence"] == [evidence]
    assert promotion_args["validation_scope"] == "all"
    framing_content = promotion_args["framings"][0]["content"]
    assert "rc:ProfileMetricKind" in framing_content
    assert project_metric in framing_content
    assert "reusable completeness score" in framing_content
    assert [action.tool_name for action in draft.suggested_next_actions] == [
        "get_context_graph",
        "list_entities",
        "stage_systematisation",
        "describe_pattern",
        "stage_pattern_promotion",
    ]
    plan_by_move = {
        item.semantic_move: item for item in draft.advisory_followthrough_plan
    }
    assert set(plan_by_move) == {"caveat_fallback", "define_metric"}
    metric_plan = plan_by_move["define_metric"]
    assert metric_plan.semantic_move == "define_metric"
    assert metric_plan.review_lane == "metric_vocabulary_review"
    assert metric_plan.primary_tool_name == "stage_pattern_promotion"
    assert metric_plan.primary_action_kind == "stage_reviewable_change"
    assert metric_plan.primary_action_writes_graph is True
    assert metric_plan.metric_advisory_indexes == [0]
    assert metric_plan.advisory_status_counts == {
        "project_metric_undefined": 1,
    }
    assert metric_plan.route_pattern_iris == [pattern.pattern_iri]
    assert metric_plan.source_profile_advisories[0]["route_group_key"].startswith(
        "metric_vocabulary_review:"
    )
    assert plan_by_move["caveat_fallback"].primary_tool_name == (
        "stage_systematisation"
    )
    assert plan_by_move["caveat_fallback"].primary_action_kind == (
        "stage_reviewable_change"
    )
    metric_route_source = promotion_args["profile_route_sources"][0]
    assert metric_route_source["route_group_key"] == metric_plan.route_group_key
    assert metric_route_source["route_step_key"] in (
        metric_plan.route_step_keys
    )
    assert metric_route_source["advisory_indexes"] == (
        metric_plan.metric_advisory_indexes
    )
    assert metric_route_source["duplicate_advisory_indexes"] == (
        metric_plan.duplicate_advisory_indexes
    )
    assert set(metric_route_source["route_pattern_iris"]) == set(
        metric_plan.route_pattern_iris
    )

    staged_promotion = db.stage_pattern_promotion(**promotion_args)

    assert staged_promotion.profile_route_source_count == len(
        promotion_args["profile_route_sources"]
    )
    assert len(staged_promotion.staged_revisions) == 1
    staged = db.describe_staged_revision(
        staged_promotion.staged_revisions[0].revision_iri
    )
    assert staged.validation_conforms is True
    assert {item.iri for item in staged.supporting_patterns} == {
        pattern.pattern_iri
    }
    assert {item.iri for item in staged.supporting_observations} == set(
        bundle.handoff_entrypoints.profile_observation_iris
    )
    assert {item.iri for item in staged.evidence} == {evidence}
    assert project_metric in {item.iri for item in staged.revision_anchors}
    rerun = db.draft_profile_map_updates(dataset, evidence)
    rerun_advisory = rerun.metric_advisories[0]
    assert rerun_advisory.pending_staged_promotion_iris == [staged.iri]
    assert rerun_advisory.pending_staged_promotion_count == 1
    assert [action.tool_name for action in rerun_advisory.suggested_next_actions] == [
        "get_context_graph",
        "list_entities",
        "describe_staged_revision",
        "export_staged_revisions",
        "describe_pattern",
        "describe_staged_revision",
        "export_staged_revisions",
    ]
    assert not any(
        action.tool_name == "stage_systematisation"
        for action in rerun_advisory.suggested_next_actions
    )
    assert not any(
        action.tool_name == "stage_pattern_promotion"
        for action in rerun_advisory.suggested_next_actions
    )
    fallback_inspect_action = rerun_advisory.suggested_next_actions[2]
    assert fallback_inspect_action.semantic_move == "caveat_fallback"
    assert fallback_inspect_action.arguments == {
        "iri": fallback_staged_iri,
        "include_current_apply_check": True,
    }
    assert fallback_inspect_action.source_profile_advisory[
        "action_status"
    ] == "already_pending"
    assert fallback_inspect_action.source_profile_advisory[
        "pending_staged_fallback_iris"
    ] == [fallback_staged_iri]
    fallback_export_action = rerun_advisory.suggested_next_actions[3]
    assert fallback_export_action.semantic_move == "caveat_fallback"
    assert fallback_export_action.arguments["revision_iris"] == [
        fallback_staged_iri
    ]
    inspect_action = rerun_advisory.suggested_next_actions[5]
    assert inspect_action.arguments == {
        "iri": staged.iri,
        "include_current_apply_check": True,
    }
    export_action = rerun_advisory.suggested_next_actions[6]
    assert export_action.arguments["revision_iris"] == [staged.iri]
    grouped_export_action = next(
        action
        for action in rerun.suggested_next_action_groups["metric_vocabulary_review"]
        if action.tool_name == "export_staged_revisions"
    )
    assert grouped_export_action.source_profile_advisory[
        "pending_staged_promotion_iris"
    ] == [staged.iri]
    assert (
        grouped_export_action.source_profile_advisory[
            "pending_staged_promotion_count"
        ]
        == 1
    )
    rerun_plan_by_move = {
        item.semantic_move: item for item in rerun.advisory_followthrough_plan
    }
    assert set(rerun_plan_by_move) == {"caveat_fallback", "define_metric"}
    assert rerun_plan_by_move["caveat_fallback"].primary_action_writes_graph is False
    assert rerun_plan_by_move["caveat_fallback"].source_profile_advisories[0][
        "pending_staged_fallback_iris"
    ] == [fallback_staged_iri]
    export_path = tmp_path / "metric-promotion-review.md"
    db.export_staged_revision(staged.iri, export_path)
    export_text = export_path.read_text()
    assert "## Linked Support" in export_text
    assert pattern.pattern_iri in export_text
    assert evidence in export_text
    assert bundle.handoff_entrypoints.profile_observation_iris[0] in export_text


def test_metric_advisory_context_action_stays_on_observed_metric(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    shipments = "https://example.test/project#Shipments"
    orders_evidence = "https://example.test/project#OrdersProfileRunEvidence"
    shipments_evidence = "https://example.test/project#ShipmentsProfileRunEvidence"
    project_metric = "https://example.test/project#CompletenessScore"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    db.record_map_dataset(shipments, label="Shipments", is_table=True)

    db.record_profile_bundle(
        orders,
        dataset_summary="Orders profile with completeness metric.",
        evidence_summary="Orders profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=orders_evidence,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": project_metric,
                "value": "0.98",
                "datatype": "xsd:decimal",
            }
        ],
        column_defaults={"update_map_column": False},
    )
    db.record_profile_bundle(
        shipments,
        dataset_summary="Shipments profile with the same metric kind.",
        evidence_summary="Shipments profile run.",
        evidence_sources=["test://shipments-profile"],
        shared_evidence_iri=shipments_evidence,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": project_metric,
                "value": "0.74",
                "datatype": "xsd:decimal",
            }
        ],
        column_defaults={"update_map_column": False},
    )

    draft = db.draft_profile_map_updates(orders, orders_evidence)
    advisory = draft.metric_advisories[0]
    context_action = advisory.suggested_next_actions[0]

    assert advisory.metric.iri == project_metric
    assert context_action.action_label == "Inspect observed metric context"
    assert context_action.arguments == {
        "seed_iris": [advisory.observed_metric_iri],
        "profile": "dataset_brief",
    }

    context_slice = db.get_context_graph(**context_action.arguments)
    context_dataset_iris = {dataset.iri for dataset in context_slice.dataset_contexts}

    assert orders in context_dataset_iris
    assert shipments not in context_dataset_iris

    broad_metric_slice = db.get_context_graph(
        project_metric,
        profile="dataset_brief",
        max_triples=200,
    )
    broad_dataset_iris = {
        dataset.iri for dataset in broad_metric_slice.dataset_contexts
    }
    assert {orders, shipments} <= broad_dataset_iris


def test_draft_profile_map_updates_routes_ambiguous_project_metric_advisory(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"
    project_metric = "https://example.test/project#CompletenessScore"
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=100,
    )
    db.replace_graph_triples(
        "ontology",
        additions=f"""
            @prefix metric: <https://example.test/project#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            <{project_metric}> a metric:Metric ;
                rdfs:label "Completeness score" ;
                rdfs:comment "Share of records with complete required fields." .
        """,
        allow_count_change=True,
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Orders profile with an ambiguously typed project metric.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        row_count=100,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": project_metric,
                "value": "0.99",
                "datatype": "xsd:decimal",
            }
        ],
        column_defaults={"update_map_column": False},
    )

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.metric_advisory_count == 1
    assert draft.metric_advisory_status_counts == {
        "project_metric_definition_ambiguous": 1,
    }
    advisory = draft.metric_advisories[0]
    assert advisory.advisory_status == "project_metric_definition_ambiguous"
    assert advisory.definition_found is True
    assert advisory.definition is not None
    assert advisory.definition.iri == project_metric
    assert [action.tool_name for action in advisory.suggested_next_actions] == [
        "get_context_graph",
        "describe_resource",
        "list_entities",
        "stage_systematisation",
    ]
    assert advisory.suggested_next_actions[1].arguments == {
        "iri": project_metric,
        "graph": "ontology",
    }


def test_draft_profile_map_updates_surfaces_prose_metric_context_pattern(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"
    project_metric = "https://example.test/project#CompletenessScore"
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=100,
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Orders profile with an undefined project metric.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        row_count=100,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": project_metric,
                "value": "0.99",
                "datatype": "xsd:decimal",
            }
        ],
        column_defaults={"update_map_column": False},
    )
    pattern = db.record_pattern(
        summary="CompletenessScore needs interpretation before reuse.",
        pattern_text=(
            "CompletenessScore appears to describe required-field coverage, but "
            "this prose pattern does not yet name the metric as a formal target "
            "or map implication."
        ),
        rationale="The pattern and profile run share one evidence resource.",
        pattern_targets=[dataset],
        evidence_iri=evidence,
    )

    draft = db.draft_profile_map_updates(dataset, evidence)

    advisory = draft.metric_advisories[0]
    assert advisory.advisory_status == "project_metric_undefined"
    assert advisory.promotion_pattern_count == 0
    assert advisory.promotion_patterns == []
    assert advisory.context_pattern_count == 1
    assert [item.iri for item in advisory.context_patterns] == [
        pattern.pattern_iri
    ]
    assert [action.tool_name for action in advisory.suggested_next_actions] == [
        "get_context_graph",
        "list_entities",
        "stage_systematisation",
        "describe_pattern",
    ]
    assert advisory.suggested_next_actions[-1].action_label == (
        "Inspect metric context pattern"
    )
    assert advisory.suggested_next_actions[-1].arguments == {
        "iri": pattern.pattern_iri,
    }
    assert "stage_pattern_promotion" not in {
        action.tool_name for action in draft.suggested_next_actions
    }


def test_draft_profile_map_updates_promotes_ambiguous_metric_with_pattern(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"
    project_metric = "https://example.test/project#CompletenessScore"
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=100,
    )
    db.replace_graph_triples(
        "ontology",
        additions=f"""
            @prefix metric: <https://example.test/project#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            <{project_metric}> a metric:Metric ;
                rdfs:label "Completeness score" ;
                rdfs:comment "Share of records with complete required fields." .
        """,
        allow_count_change=True,
    )
    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders profile with an ambiguously typed project metric.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        row_count=100,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": project_metric,
                "value": "0.99",
                "datatype": "xsd:decimal",
            }
        ],
        column_defaults={"update_map_column": False},
    )
    pattern = db.record_pattern(
        summary="Orders completeness score is reusable metric vocabulary.",
        pattern_text=(
            "CompletenessScore is the share of records with complete required "
            "fields and should be typed as reusable profile metric vocabulary."
        ),
        rationale="The pattern and profile run share one evidence resource.",
        pattern_targets=[project_metric],
        supporting_observations=(
            bundle.handoff_entrypoints.profile_observation_iris
        ),
        evidence_iri=evidence,
        map_implications=[project_metric],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)

    advisory = draft.metric_advisories[0]
    assert advisory.advisory_status == "project_metric_definition_ambiguous"
    assert advisory.definition_found is True
    assert advisory.promotion_pattern_count == 1
    assert [item.iri for item in advisory.promotion_patterns] == [
        pattern.pattern_iri
    ]
    assert [action.tool_name for action in advisory.suggested_next_actions] == [
        "get_context_graph",
        "describe_resource",
        "list_entities",
        "stage_systematisation",
        "describe_pattern",
        "stage_pattern_promotion",
    ]
    assert advisory.suggested_next_actions[1].arguments == {
        "iri": project_metric,
        "graph": "ontology",
    }
    promotion_action = advisory.suggested_next_actions[-1]
    promotion_args = promotion_action.arguments
    assert promotion_args["patterns"] == [pattern.pattern_iri]
    assert promotion_args["anchors"] == [project_metric]
    assert promotion_args["evidence"] == [evidence]
    assert "CompletenessScore is the share" in (
        promotion_args["framings"][0]["content"]
    )
    assert [action.tool_name for action in draft.suggested_next_actions] == [
        "get_context_graph",
        "describe_resource",
        "list_entities",
        "stage_systematisation",
        "describe_pattern",
        "stage_pattern_promotion",
    ]

    staged_promotion = db.stage_pattern_promotion(**promotion_args)

    staged = db.describe_staged_revision(
        staged_promotion.staged_revisions[0].revision_iri
    )
    assert staged.validation_conforms is True
    assert {item.iri for item in staged.supporting_patterns} == {
        pattern.pattern_iri
    }
    assert project_metric in {item.iri for item in staged.revision_anchors}


def test_stage_profile_map_updates_groups_accepted_reviewable_changes(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Payments"
    status_column = "https://example.test/project#PaymentsStatus"
    settlement_column = "https://example.test/project#PaymentsSettlementMethod"
    evidence = "https://example.test/project#PaymentsProfileRunEvidence"
    project_metric = "https://example.test/project#PaymentsFreshnessScore"

    db.record_map_dataset(
        dataset,
        label="Payments",
        is_table=True,
        row_count_snapshot=10,
    )
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        nullable=False,
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Payments were profiled with a full-table scan.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://payments-profile"],
        shared_evidence_iri=evidence,
        sample_size=12,
        sample_scope="All rows in the test Payments table.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=12,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": project_metric,
                "value": "0.93",
                "datatype": "xsd:decimal",
            }
        ],
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status had nulls in the full scan.",
                "null_count": 2,
                "physical_type": "rc:Varchar",
            },
            {
                "column_iri": settlement_column,
                "column_name": "settlement_method",
                "summary": "Settlement method was observed but is unmapped.",
            },
        ],
    )

    staged = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[0, 1, 2],
    )

    assert staged.result_kind == "profile_map_update_staging"
    assert staged.staged_recommendation_indexes == [0, 1, 2]
    assert staged.skipped_recommendation_indexes == []
    assert staged.not_selected_recommendation_indexes == []
    assert staged.status_counts == {"staged": 3, "skipped": 0, "not_selected": 0}
    assert [item.status for item in staged.items] == ["staged", "staged", "staged"]
    assert staged.metric_advisory_count == 1
    assert staged.metric_advisory_status_counts == {
        "project_metric_undefined": 1,
    }
    assert staged.metric_advisories[0].metric.iri == project_metric
    assert staged.metric_vocabulary_review_required is True
    assert [
        action.tool_name
        for action in staged.metric_advisory_suggested_next_actions
    ] == [
        "get_context_graph",
        "list_entities",
        "stage_systematisation",
    ]
    assert staged.metric_advisory_suggested_next_actions[0].arguments == {
        "seed_iris": [staged.metric_advisories[0].observed_metric_iri],
        "profile": "dataset_brief",
    }
    assert staged.metric_advisory_suggested_next_calls == [
        action.call for action in staged.metric_advisory_suggested_next_actions
    ]
    review_advisory_summary = (
        "Metric vocabulary advisories (review separately; not staged as map "
        "patches): 1 (project_metric_undefined=1)."
    )
    assert review_advisory_summary in staged.review_note
    assert staged.type_advisory_count == 1
    assert staged.type_advisory_status_counts == {
        "type_finding_missing_map_type": 1,
    }
    assert staged.type_advisories[0].observed_column.iri == status_column
    assert staged.type_advisories[0].observed_physical_type is not None
    assert staged.type_advisories[0].observed_physical_type.iri == f"{RC}Varchar"
    assert staged.type_review_required is True
    assert [
        action.tool_name for action in staged.type_advisory_suggested_next_actions
    ] == [
        "get_context_graph",
        "record_pattern",
        "stage_systematisation",
        "stage_map_assertion_change",
    ]
    assert staged.type_advisory_suggested_next_calls == [
        action.call for action in staged.type_advisory_suggested_next_actions
    ]
    type_review_advisory_summary = (
        "Profile type advisories (review separately; not staged as map "
        "patches): 1 (type_finding_missing_map_type=1)."
    )
    assert type_review_advisory_summary in staged.review_note
    assert staged.staged_revision is not None
    assert staged.staged_revision.validation_conforms is True
    assert staged.staged_revision.changed_graphs == ["map"]
    assert [action.tool_name for action in staged.suggested_next_actions] == [
        "check_staged_revision_apply",
        "export_profile_insight_review_bundle",
        "draft_profile_map_updates",
    ]
    assert staged.suggested_next_actions[0].arguments == {
        "iri": staged.staged_revision.revision_iri
    }
    assert staged.suggested_next_actions[0].mcp_tool_name == (
        "doxabase.check_staged_revision_apply"
    )
    assert staged.suggested_next_actions[1].arguments["dataset_iri"] == dataset
    assert staged.suggested_next_actions[1].arguments["evidence_iri"] == evidence
    assert staged.suggested_next_actions[1].arguments["revision_iris"] == [
        staged.staged_revision.revision_iri
    ]
    assert staged.suggested_next_actions[1].arguments["overwrite"] is True
    assert staged.suggested_next_actions[1].arguments["path"].startswith(
        "/tmp/profile-insight-review-"
    )
    assert staged.suggested_next_actions[1].mcp_tool_name == (
        "doxabase.export_profile_insight_review_bundle"
    )
    assert staged.suggested_next_actions[2].arguments == {
        "dataset_iri": dataset,
        "evidence_iri": evidence,
    }
    assert staged.suggested_next_actions[2].mcp_tool_name == (
        "doxabase.draft_profile_map_updates"
    )
    assert staged.suggested_next_actions[2].preconditions == {
        "staged_revision_applied": staged.staged_revision.revision_iri,
        "why": (
            "The rerun only reflects the newly mapped column after the staged "
            "profile map-update revision has been reviewed and applied."
        ),
    }
    assert staged.suggested_next_calls == [
        action.call for action in staged.suggested_next_actions
    ]
    staged_payload = to_jsonable(staged)
    assert staged_payload["suggested_next_actions"][2]["preconditions"][
        "staged_revision_applied"
    ] == staged.staged_revision.revision_iri
    assert [patch.target_graph for patch in staged.staged_revision.patches] == [
        "map",
        "map",
    ]
    assert {patch.triple_count for patch in staged.staged_revision.patches} == {
        2,
        5,
    }
    described = db.describe_staged_revision(staged.staged_revision.revision_iri)
    assert described.validation_conforms is True
    assert {anchor.iri for anchor in described.revision_anchors} == {
        dataset,
        status_column,
        settlement_column,
    }
    assert {item.iri for item in described.supporting_observations} == {
        item.profile_observation_iri for item in staged.items
    }
    assert [item.iri for item in described.evidence] == [evidence]
    assert review_advisory_summary in (described.review_note or "")

    description = db.describe_dataset(dataset)
    assert description.row_count_snapshot == 10
    assert {column.iri for column in description.columns} == {status_column}

    applied = db.apply_staged_revision(staged.staged_revision.revision_iri)
    assert applied.patches_applied == 2
    assert applied.triples_removed == 2
    assert applied.triples_added == 5
    assert applied.validation_conforms is True
    applied_description = db.describe_dataset(dataset)
    assert applied_description.row_count_snapshot == 12
    assert {
        column.iri: column.nullable for column in applied_description.columns
    } == {
        status_column: True,
        settlement_column: None,
    }


def test_profile_followthrough_mixes_duplicates_advisories_and_sampled_guardrail(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/profile-followthrough#"
    dataset = f"{base}Payments"
    status_column = f"{base}PaymentsStatus"
    settlement_column = f"{base}PaymentsSettlementMethod"
    referrer_column = f"{base}PaymentsReferrer"
    full_evidence = f"{base}FullProfileEvidence"
    sampled_evidence = f"{base}SampleProfileEvidence"
    project_metric = f"{base}PaymentsFreshnessScore"

    db.record_map_dataset(
        dataset,
        label="Payments",
        is_table=True,
        row_count_snapshot=10,
    )
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        nullable=False,
        physical_type="rc:Varchar",
    )
    db.record_map_column(
        referrer_column,
        table_iri=dataset,
        column_name="referrer",
        nullable=False,
    )

    full_profile_observations: list[str] = []
    for index in range(2):
        bundle = db.record_profile_bundle(
            dataset,
            dataset_summary="Payments were profiled with a full-table scan.",
            evidence_summary="Payments full profile.",
            evidence_sources=[f"test://payments/full/{index}"],
            shared_evidence_iri=full_evidence,
            sample_size=12,
            sample_scope="All rows in the local Payments table.",
            sample_method="DuckDB full-table profile.",
            row_count=12,
            update_map_snapshot=False,
            profile_metrics=[
                {
                    "metric": project_metric,
                    "value": "0.93",
                    "datatype": "xsd:decimal",
                }
            ],
            column_defaults={"update_map_column": False},
            column_profiles=[
                {
                    "column_iri": status_column,
                    "column_name": "status",
                    "summary": "Status had nulls and looked integer-coded.",
                    "null_count": 2,
                    "physical_type": "rc:Integer",
                },
                {
                    "column_iri": settlement_column,
                    "column_name": "settlement_method",
                    "summary": "Settlement method was observed but unmapped.",
                    "null_count": 0,
                    "physical_type": "rc:Varchar",
                },
            ],
        )
        full_profile_observations.extend(
            bundle.handoff_entrypoints.profile_observation_iris
        )

    metric_pattern = db.record_pattern(
        summary="Payments freshness score needs vocabulary.",
        pattern_text=(
            "The Payments profile uses a reusable freshness score that needs "
            "a project metric definition before comparison."
        ),
        rationale="The metric and pattern share the full-profile evidence.",
        pattern_targets=[dataset],
        supporting_observations=full_profile_observations,
        evidence_iri=full_evidence,
        map_implications=[project_metric],
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Payments sampled partition profile.",
        evidence_summary="Payments sampled profile.",
        evidence_sources=["test://payments/sample"],
        shared_evidence_iri=sampled_evidence,
        sample_size=40,
        sample_scope="Sampled partition rows; not the full Payments table.",
        sample_method="DuckDB sampled partition profile.",
        row_count=40,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": referrer_column,
                "column_name": "referrer",
                "summary": "Referrer had nulls in the sampled partition.",
                "null_count": 3,
            }
        ],
    )

    full_draft = db.draft_profile_map_updates(dataset, full_evidence)

    assert full_draft.recommendation_count == 6
    assert full_draft.representative_recommendation_indexes == [0, 2, 4]
    assert [
        recommendation.kind for recommendation in full_draft.recommendations
    ] == [
        "dataset_row_count_snapshot",
        "dataset_row_count_snapshot",
        "column_nullable",
        "column_nullable",
        "unmapped_profiled_column",
        "unmapped_profiled_column",
    ]
    assert full_draft.metric_advisory_status_counts == {
        "project_metric_undefined": 2,
    }
    assert full_draft.representative_metric_advisory_indexes == [0]
    assert full_draft.type_advisory_status_counts == {
        "type_finding_conflicts_current_map": 2,
        "type_finding_unmapped_column": 2,
    }
    assert full_draft.representative_type_advisory_indexes == [0, 2]
    assert all(
        advisory.metric_advisory_index == index
        and advisory.duplicate_advisory_indexes == [0, 1]
        and advisory.promotion_patterns[0].iri == metric_pattern.pattern_iri
        for index, advisory in enumerate(full_draft.metric_advisories)
    )
    assert [
        advisory.type_advisory_index for advisory in full_draft.type_advisories
    ] == [0, 1, 2, 3]

    staged_updates = db.stage_profile_map_updates(
        dataset,
        full_evidence,
        accepted_recommendation_indexes=(
            full_draft.representative_recommendation_indexes
        ),
    )
    assert staged_updates.status_counts == {
        "staged": 3,
        "skipped": 0,
        "not_selected": 3,
    }
    assert [
        action.tool_name for action in staged_updates.suggested_next_actions
    ] == [
        "check_staged_revision_apply",
        "export_profile_insight_review_bundle",
        "draft_profile_map_updates",
    ]
    assert staged_updates.suggested_next_actions[1].arguments["dataset_iri"] == (
        dataset
    )
    assert staged_updates.suggested_next_actions[1].arguments["evidence_iri"] == (
        full_evidence
    )
    assert staged_updates.suggested_next_actions[1].arguments[
        "revision_iris"
    ] == [staged_updates.staged_revision.revision_iri]
    assert staged_updates.suggested_next_actions[2].arguments == {
        "dataset_iri": dataset,
        "evidence_iri": full_evidence,
    }
    assert "After reviewing and applying" in (
        staged_updates.suggested_next_actions[2].reason
    )
    assert staged_updates.staged_revision is not None
    assert db.check_staged_revision_apply(
        staged_updates.staged_revision.revision_iri
    ).status == "ready"
    applied_updates = db.apply_staged_revision(
        staged_updates.staged_revision.revision_iri
    )
    assert applied_updates.patches_applied == 2
    updated_dataset = db.describe_dataset(dataset)
    assert updated_dataset.row_count_snapshot == 12
    assert {
        column.iri: column.nullable for column in updated_dataset.columns
    } == {
        status_column: True,
        settlement_column: None,
        referrer_column: False,
    }

    metric_promotion_action = next(
        action
        for action in full_draft.metric_advisories[0].suggested_next_actions
        if action.tool_name == "stage_pattern_promotion"
    )
    metric_promotion = db.stage_pattern_promotion(
        **metric_promotion_action.arguments
    )
    assert len(metric_promotion.staged_revisions) == 1
    promoted_revision = metric_promotion.staged_revisions[0]
    promoted_description = db.describe_staged_revision(
        promoted_revision.revision_iri
    )
    assert {item.iri for item in promoted_description.supporting_patterns} == {
        metric_pattern.pattern_iri
    }
    assert project_metric in {
        item.iri for item in promoted_description.revision_anchors
    }
    assert db.check_staged_revision_apply(promoted_revision.revision_iri).status == (
        "ready"
    )
    assert db.apply_staged_revision(promoted_revision.revision_iri).patches_applied == 1

    type_advisory = next(
        advisory
        for advisory in full_draft.type_advisories
        if advisory.observed_column.iri == status_column
    )
    type_pattern_action = next(
        action
        for action in type_advisory.suggested_next_actions
        if action.tool_name == "record_pattern"
    )
    type_pattern = db.record_pattern(**type_pattern_action.arguments)
    physical_type_action = next(
        action
        for action in type_advisory.suggested_next_actions
        if action.tool_name == "stage_map_assertion_change"
        and action.arguments["predicate"] == "rc:physicalType"
    )
    physical_type_arguments = dict(physical_type_action.arguments)
    physical_type_arguments["supporting_patterns"] = [type_pattern.pattern_iri]
    staged_type = db.stage_map_assertion_change(**physical_type_arguments)
    assert staged_type.judgement_panel.semantic_risk_level == "high"
    assert staged_type.staged_revision.validation_conforms is True
    described_type = db.describe_staged_revision(
        staged_type.staged_revision.revision_iri
    )
    assert type_pattern.pattern_iri in {
        item.iri for item in described_type.supporting_patterns
    }

    sampled_draft = db.draft_profile_map_updates(dataset, sampled_evidence)
    assert sampled_draft.recommendation_count == 2
    assert sampled_draft.representative_recommendation_indexes == [0, 1]
    assert [
        (recommendation.kind, recommendation.default_stageable)
        for recommendation in sampled_draft.recommendations
    ] == [
        ("dataset_row_count_snapshot", False),
        ("column_nullable", True),
    ]
    assert sampled_draft.profile_quality_summary["basis_counts"] == {"sample": 2}
    assert sampled_draft.profile_quality_summary[
        "default_stageable_basis_counts"
    ] == {"sample": 1}
    assert sampled_draft.profile_quality_summary[
        "sampled_default_stageable_recommendation_indexes"
    ] == [1]
    assert sampled_draft.profile_quality_summary["sample_scopes"] == [
        "Sampled partition rows; not the full Payments table."
    ]
    assert sampled_draft.sampled_evidence_caution is not None
    assert "Mechanical readiness is not full-scan evidence" in (
        sampled_draft.sampled_evidence_caution
    )
    assert sampled_draft.suggested_next_actions[0].arguments == {
        "dataset_iri": dataset,
        "evidence_iri": sampled_evidence,
        "accepted_recommendation_indexes": [1],
    }
    sampled_action_source = (
        sampled_draft.suggested_next_actions[0].source_profile_map_update
    )
    assert sampled_action_source["profile_quality_summary"][
        "sampled_default_stageable_recommendation_indexes"
    ] == [1]
    assert sampled_action_source["sampled_evidence_caution"] == (
        sampled_draft.sampled_evidence_caution
    )
    sampled_stage = db.stage_profile_map_updates(
        dataset,
        sampled_evidence,
        accepted_recommendation_indexes=[0, 1],
    )
    assert sampled_stage.status_counts == {
        "staged": 1,
        "skipped": 1,
        "not_selected": 0,
    }
    assert sampled_stage.staged_recommendation_indexes == [1]
    assert sampled_stage.skipped_recommendation_indexes == [0]
    sampled_review_path = tmp_path / "sampled-profile-review.md"
    sampled_review = db.export_profile_insight_review_bundle(
        dataset,
        sampled_evidence,
        sampled_review_path,
        revision_iris=[sampled_stage.staged_revision.revision_iri],
    )
    assert sampled_review.profile_quality_summary == (
        sampled_draft.profile_quality_summary
    )
    assert sampled_review.sampled_evidence_caution == (
        sampled_draft.sampled_evidence_caution
    )
    sampled_candidate = sampled_review.candidates[0]
    assert sampled_candidate.safe_single_apply_candidate is True
    assert sampled_candidate.profile_quality_summary[
        "sampled_default_stageable_recommendation_indexes"
    ] == [1]
    assert sampled_candidate.sampled_evidence_caution == (
        sampled_draft.sampled_evidence_caution
    )
    assert "Mechanical readiness is not full-scan evidence" in (
        sampled_candidate.semantic_apply_gate_reason
    )
    assert sampled_review.executor_decision_summary[
        "safe_single_apply_candidate_rationales"
    ][0]["sampled_evidence_caution"] == sampled_draft.sampled_evidence_caution
    sampled_review_text = sampled_review_path.read_text(encoding="utf-8")
    assert "Profile basis" in sampled_review_text
    assert "sample: 1" in sampled_review_text
    assert "Mechanical readiness is not full-scan evidence" in sampled_review_text
    generic_sampled_review_path = tmp_path / "sampled-generic-staged-review.md"
    generic_sampled_export = db.export_staged_revisions(
        [sampled_stage.staged_revision.revision_iri],
        generic_sampled_review_path,
    )
    generic_route_group = generic_sampled_export.revision_summaries[
        0
    ].profile_route_groups[0]
    assert generic_route_group["sampled_evidence_cautions"] == [
        sampled_draft.sampled_evidence_caution
    ]
    generic_sampled_review_text = generic_sampled_review_path.read_text(
        encoding="utf-8"
    )
    assert "## Profile Route Bridge" in generic_sampled_review_text
    assert "Evidence cautions" in generic_sampled_review_text
    assert "Mechanical readiness is not full-scan evidence" in (
        generic_sampled_review_text
    )
    assert db.validate_graph(scope="all").conforms


def test_stage_profile_map_updates_preserves_caller_support_metadata(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Payments"
    status_column = "https://example.test/project#PaymentsStatus"
    evidence = "https://example.test/project#PaymentsProfileRunEvidence"
    extra_anchor = "https://example.test/project#PaymentsQualityReview"

    db.record_map_dataset(
        dataset,
        label="Payments",
        is_table=True,
        row_count_snapshot=10,
    )
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        nullable=False,
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Payments were profiled with a full-table scan.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://payments-profile"],
        shared_evidence_iri=evidence,
        sample_size=12,
        sample_scope="All rows in the test Payments table.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=12,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status had nulls in the full scan.",
                "null_count": 2,
            }
        ],
    )
    claim = db.record_claim_observation(
        summary="Payments profile support claim.",
        claim_text="The full profile run should update current payment metadata.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=[dataset, status_column],
        evidence_sources=["test://profile-support-claim"],
    )
    pattern = db.record_pattern(
        summary="Payments profile support pattern.",
        pattern_text="Repeated full scans are treated as reliable map-update support.",
        rationale="The claim and profile evidence both point at the same table.",
        pattern_targets=[dataset],
        supporting_claims=[claim.claim_iri],
    )

    staged = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[0, 1],
        supporting_claims=[claim.claim_iri],
        supporting_patterns=[pattern.pattern_iri],
        revision_anchors=[extra_anchor, dataset],
    )

    assert staged.staged_revision is not None
    described = db.describe_staged_revision(staged.staged_revision.revision_iri)
    assert [item.iri for item in described.supporting_claims] == [claim.claim_iri]
    assert [item.iri for item in described.supporting_patterns] == [
        pattern.pattern_iri
    ]
    assert {item.iri for item in described.supporting_observations} == {
        item.profile_observation_iri for item in staged.items
    }
    assert [item.iri for item in described.evidence] == [evidence]
    assert {anchor.iri for anchor in described.revision_anchors} == {
        extra_anchor,
        dataset,
        status_column,
    }
    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_stage_profile_map_updates_stages_thin_shell_for_missing_dataset(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#ObservationOnlyOrders"
    status_column = "https://example.test/project#ObservationOnlyOrdersStatus"
    evidence = "https://example.test/project#ObservationOnlyProfileRunEvidence"

    db.record_profile_bundle(
        dataset,
        dataset_summary="Observation-only Orders profile.",
        evidence_summary="Observation-only profile pass.",
        evidence_sources=["test://observation-only-profile"],
        shared_evidence_iri=evidence,
        sample_size=20,
        sample_scope="All rows in the observation-only Orders table.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=20,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Observation-only status profile.",
            }
        ],
    )

    staged = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[0, 1],
    )

    assert staged.map_dataset_found is False
    assert staged.staged_recommendation_indexes == [0, 1]
    assert staged.status_counts == {"staged": 2, "skipped": 0, "not_selected": 0}
    assert staged.staged_revision is not None
    assert staged.staged_revision.validation_conforms is True
    assert len(staged.staged_revision.patches) == 1
    patch_content = db.describe_staged_revision(
        staged.staged_revision.revision_iri
    ).patches[0].content
    assert patch_content is not None
    assert "rc:Dataset" in patch_content
    assert "rc:Column" in patch_content
    assert "rc:rowCountSnapshot 20" in patch_content
    assert "status" in patch_content
    assert [
        anchor.iri
        for anchor in db.describe_staged_revision(
            staged.staged_revision.revision_iri
        ).revision_anchors
    ] == [
        dataset,
        status_column,
    ]

    with pytest.raises(DoxaBaseError, match="was not found"):
        db.describe_dataset(dataset)


def test_stage_profile_map_updates_skips_sampled_row_count_by_default(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    referrer_column = "https://example.test/project#OrdersReferrer"
    evidence = "https://example.test/project#OrdersPartitionSampleEvidence"

    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=100,
    )
    db.record_map_column(
        referrer_column,
        table_iri=dataset,
        column_name="referrer",
        nullable=False,
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled from one sampled partition.",
        evidence_summary="Synthetic partition sample profile.",
        evidence_sources=["test://orders-partition-sample-profile"],
        shared_evidence_iri=evidence,
        sample_size=40,
        sample_scope="Sampled partition rows; not the full Orders table.",
        sample_method="DuckDB sampled partition profile.",
        row_count=40,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": referrer_column,
                "column_name": "referrer",
                "summary": "Referrer had nulls in the sampled partition.",
                "null_count": 3,
            }
        ],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)
    assert draft.representative_recommendation_indexes == [0, 1]
    row_count_recommendation = draft.recommendations[0]
    nullable_recommendation = draft.recommendations[1]
    assert row_count_recommendation.kind == "dataset_row_count_snapshot"
    assert row_count_recommendation.default_stageable is False
    assert "Sampled or unknown-scope row-count recommendations" in (
        row_count_recommendation.default_skip_reason or ""
    )
    assert nullable_recommendation.kind == "column_nullable"
    assert nullable_recommendation.default_stageable is True
    assert nullable_recommendation.default_skip_reason is None
    assert draft.suggested_next_actions[0].tool_name == "stage_profile_map_updates"
    assert draft.suggested_next_actions[0].arguments == {
        "dataset_iri": dataset,
        "evidence_iri": evidence,
        "accepted_recommendation_indexes": [1],
    }

    staged = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[0],
    )

    assert staged.result_kind == "profile_map_update_staging"
    assert staged.staged_recommendation_indexes == []
    assert staged.skipped_recommendation_indexes == [0]
    assert staged.not_selected_recommendation_indexes == [1]
    assert staged.status_counts == {"staged": 0, "skipped": 1, "not_selected": 1}
    assert staged.staged_revision is None
    assert staged.revision_iri is None
    assert staged.suggested_next_actions == []
    assert staged.suggested_next_calls == []
    assert staged.items[0].status == "skipped"
    assert staged.items[1].status == "not_selected"
    assert "Sampled or unknown-scope row-count recommendations" in (
        staged.items[0].reason or ""
    )
    assert db.describe_dataset(dataset).row_count_snapshot == 100

    mixed = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[0, 1],
    )
    assert mixed.staged_recommendation_indexes == [1]
    assert mixed.skipped_recommendation_indexes == [0]
    assert mixed.not_selected_recommendation_indexes == []
    assert mixed.status_counts == {"staged": 1, "skipped": 1, "not_selected": 0}
    assert mixed.staged_revision is not None
    assert mixed.revision_iri == mixed.staged_revision.revision_iri
    assert mixed.suggested_next_actions[0].tool_name == (
        "check_staged_revision_apply"
    )

    override = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[0],
        allow_sampled_row_count_updates=True,
        allow_pending_profile_updates=True,
    )
    assert override.staged_recommendation_indexes == [0]
    assert override.status_counts == {"staged": 1, "skipped": 0, "not_selected": 1}
    assert override.staged_revision is not None
    assert override.revision_iri == override.staged_revision.revision_iri
    assert override.staged_revision.validation_conforms is True


def test_draft_profile_map_updates_omits_sampled_only_default_stage_action(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersPartitionSampleEvidence"

    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=100,
    )
    for index in range(2):
        db.record_profile_bundle(
            dataset,
            dataset_summary=f"Orders sampled profile {index}.",
            evidence_summary="Synthetic partition sample profile.",
            evidence_sources=[f"test://orders-partition-sample-profile/{index}"],
            shared_evidence_iri=evidence,
            sample_size=40,
            sample_scope="Sampled partition rows; not the full Orders table.",
            sample_method="DuckDB sampled partition profile.",
            row_count=40,
            update_map_snapshot=False,
            column_defaults={"update_map_column": False},
        )

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.recommendation_count == 2
    assert draft.representative_recommendation_indexes == [0]
    assert all(
        recommendation.default_stageable is False
        for recommendation in draft.recommendations
    )
    assert {
        recommendation.duplicate_count
        for recommendation in draft.recommendations
    } == {2}
    assert draft.suggested_next_actions == []
    assert draft.suggested_next_calls == []
    assert draft.suggested_next_action_groups == {}
    assert draft.suggested_next_call_groups == {}


def test_draft_profile_map_updates_skips_sampled_zero_null_promotion(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    promo_column = "https://example.test/project#OrdersPromoCode"
    evidence = "https://example.test/project#OrdersSampleProfileEvidence"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(
        promo_column,
        table_iri=dataset,
        column_name="promo_code",
        nullable=True,
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled from a sample.",
        evidence_summary="Synthetic sampled profile.",
        evidence_sources=["test://orders-sample-profile"],
        shared_evidence_iri=evidence,
        sample_size=25,
        sample_scope="Not a full population; 25 sampled Orders rows.",
        sample_method="DuckDB random sample profile.",
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": promo_column,
                "column_name": "promo_code",
                "summary": "Promo code had zero nulls in the sample.",
                "null_count": 0,
                "distinct_count": 8,
            }
        ],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.recommendations == []
    assert draft.metric_advisories == []
    assert draft.recommendation_count == 0
    assert draft.metric_advisory_count == 0
    assert draft.suggested_next_actions == []
    assert draft.suggested_next_calls == []
    description = db.describe_dataset(dataset)
    assert description.columns[0].nullable is True


def test_draft_profile_map_updates_treats_explicit_sample_text_as_sample(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    sample_only_column = "https://example.test/project#OrdersSampleOnlyFlag"
    evidence = "https://example.test/project#OrdersPartitionSampleEvidence"

    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=100,
    )
    db.record_map_column(
        sample_only_column,
        table_iri=dataset,
        column_name="sample_only_flag",
        nullable=True,
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled from one sampled partition.",
        evidence_summary="Synthetic partition sample profile.",
        evidence_sources=["test://orders-partition-sample-profile"],
        shared_evidence_iri=evidence,
        sample_size=40,
        sample_scope="Sampled partition rows; not the full Orders table.",
        sample_method="DuckDB sampled partition profile.",
        row_count=40,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": sample_only_column,
                "column_name": "sample_only_flag",
                "summary": "Sample-only flag had zero nulls in the partition sample.",
                "null_count": 0,
                "distinct_count": 2,
            }
        ],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert [(item.kind, item.basis) for item in draft.recommendations] == [
        ("dataset_row_count_snapshot", "sample")
    ]
    row_count = draft.recommendations[0]
    assert row_count.confidence == "medium"
    assert row_count.sample_size == 40
    assert row_count.profile_row_count == 40
    assert "sampled partition" in (row_count.sample_method or "").lower()
    description = db.describe_dataset(dataset)
    assert description.row_count_snapshot == 100
    assert description.columns[0].nullable is True


def test_draft_profile_map_updates_rejects_missing_identifiers(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(
        DoxaBaseError,
        match="dataset_iri must be a non-empty IRI or CURIE string",
    ):
        db.draft_profile_map_updates(
            None,  # type: ignore[arg-type]
            "https://example.test/project#ProfileEvidence",
        )
    with pytest.raises(
        DoxaBaseError,
        match="evidence_iri must be a non-empty IRI or CURIE string",
    ):
        db.draft_profile_map_updates(
            "https://example.test/project#Orders",
            None,  # type: ignore[arg-type]
        )

