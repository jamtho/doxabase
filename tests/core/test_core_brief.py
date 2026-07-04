"""Split from test_doxabase_core.py (distillation Phase 2); tests verbatim."""

from tests.core.support_core import *  # noqa: F401,F403


def test_project_brief_summarizes_datasets_and_active_queues(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    db.import_trig(POLYMARKET_FIXTURE)

    brief = db.project_brief(limit=4, profile_candidate_limit=1)

    assert brief.key_counts["tables"] >= 7
    assert brief.dataset_count >= 7
    assert brief.returned_dataset_count == 4
    assert brief.limit == 4
    assert sum(brief.dataset_query_readiness_counts.values()) == brief.dataset_count
    assert sum(brief.returned_dataset_query_readiness_counts.values()) == 4
    assert len(brief.datasets) == 4
    assert brief.datasets[0].dataset.iri.startswith("https://")
    assert brief.datasets[0].query.readiness
    assert brief.datasets[0].profile.profile_run_candidate_count >= 0
    assert brief.staged_review.returned_count == 0
    assert isinstance(to_dict(brief)["recommended_next_tasks"], list)


def test_project_brief_surfaces_singleton_profile_draft(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersProfileEvidence"

    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=10,
    )
    db.record_dataset_profile(
        dataset,
        summary="Orders were profiled with one full-table aggregate.",
        evidence_summary="Synthetic singleton profile output.",
        evidence_sources=["test://orders-profile"],
        evidence_iri=evidence,
        sample_size=12,
        sample_scope="All rows in the local Orders table.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=12,
        update_map_snapshot=False,
    )

    brief = db.project_brief(limit=2, profile_candidate_limit=1)
    profile = brief.datasets[0].profile

    assert profile.total_profile_count == 1
    assert profile.profile_run_candidate_count == 0
    assert profile.profile_evidence_iris == [evidence]
    assert profile.draft_evidence_iris == [evidence]
    assert profile.draft_count == 1
    assert profile.review_draft_count == 1
    assert profile.completed_draft_count == 0
    assert profile.draft_status_counts == {"pending map recommendations": 1}
    assert profile.drafts[0].status == "pending map recommendations"
    assert profile.drafts[0].requires_review is True
    assert profile.drafts[0].recommendation_count == 1
    draft = db.draft_profile_map_updates(dataset, evidence)
    assert draft.status == "pending map recommendations"
    assert brief.profile_queue_counts["profile_observations"] == 1
    assert brief.profile_queue_counts["profile_drafts"] == 1
    assert brief.profile_queue_counts["profile_review_drafts"] == 1
    assert brief.profile_queue_counts["profile_completed_drafts"] == 0
    assert brief.profile_queue_counts["profile_draft_recommendations"] == 1
    assert "profile_review" in brief.queue_counts
    profile_task = next(
        task
        for task in brief.recommended_next_tasks
        if task.task_type == "profile_review"
    )
    assert profile_task.suggested_next_action is not None
    assert profile_task.suggested_next_action.tool == "doxabase.stage_profile_map_updates"
    assert profile_task.inspection_next_action is not None
    assert profile_task.inspection_next_action.tool == "doxabase.draft_profile_map_updates"
    assert profile_task.inspection_next_action.args == {
        "dataset_iri": dataset,
        "evidence_iri": evidence,
    }


def test_project_brief_marks_completed_profile_draft(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersProfileEvidence"

    db.record_map_dataset(
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

    brief = db.project_brief(limit=2, profile_candidate_limit=1)
    profile = brief.datasets[0].profile

    assert profile.draft_count == 1
    assert profile.review_draft_count == 0
    assert profile.completed_draft_count == 1
    assert profile.draft_status_counts == {
        "profile evidence captured; no pending map recommendations": 1
    }
    assert profile.drafts[0].status == (
        "profile evidence captured; no pending map recommendations"
    )
    assert profile.drafts[0].requires_review is False
    assert profile.drafts[0].recommendation_count == 0
    assert brief.profile_queue_counts["profile_drafts"] == 1
    assert brief.profile_queue_counts["profile_review_drafts"] == 0
    assert brief.profile_queue_counts["profile_completed_drafts"] == 1
    draft = db.draft_profile_map_updates(dataset, evidence)
    assert draft.status == (
        "profile evidence captured; no pending map recommendations"
    )
    assert "profile_review" not in brief.queue_counts


def test_project_brief_names_advisory_only_profile_review(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    amount_column = "https://example.test/project#OrdersAmount"
    money_value_type = "https://example.test/project#MoneyAmountValue"
    evidence = "https://example.test/project#OrdersProfileEvidence"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled and amount was mapped directly.",
        evidence_summary="Synthetic amount profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        update_map_snapshot=False,
        column_profiles=[
            {
                "column_iri": amount_column,
                "column_name": "amount",
                "summary": "Amount was observed as decimal money.",
                "physical_type": "rc:Decimal",
                "value_type": money_value_type,
                "update_map_column": True,
            }
        ],
    )

    brief = db.project_brief(limit=5, profile_candidate_limit=1)
    profile_task = next(
        task
        for task in brief.recommended_next_tasks
        if task.task_type == "profile_review"
    )

    assert brief.datasets[0].profile.drafts[0].recommendation_count == 0
    assert brief.datasets[0].profile.drafts[0].requires_review is True
    assert brief.datasets[0].profile.review_draft_count == 1
    assert brief.datasets[0].profile.completed_draft_count == 0
    assert brief.datasets[0].profile.drafts[0].status == (
        "pending profile advisory review"
    )
    assert brief.datasets[0].profile.draft_status_counts == {
        "pending profile advisory review": 1
    }
    assert brief.profile_queue_counts["profile_review_drafts"] == 1
    assert brief.profile_queue_counts["profile_completed_drafts"] == 0
    draft = db.draft_profile_map_updates(dataset, evidence)
    assert draft.status == "pending profile advisory review"
    assert brief.datasets[0].profile.drafts[0].type_advisory_status_counts == {
        "type_finding_current_map_undefined_value_type": 1,
    }
    assert "no pending map recommendations" in profile_task.reason
    assert "profile type advisory count=1" in profile_task.reason
    assert "type_finding_current_map_undefined_value_type=1" in (
        profile_task.reason
    )
    assert "map updates" not in profile_task.reason


def test_project_brief_uses_profile_inspection_for_unattended_route(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersProfileEvidence"
    storage = db.record_map_storage_access(
        "https://example.test/project#OrdersStorage",
        label="Orders local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="object",
        storage_root=str(tmp_path / "orders.parquet"),
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#OrdersParquetLayout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=10,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_dataset_profile(
        dataset,
        summary="Orders were profiled with one full-table aggregate.",
        evidence_summary="Synthetic singleton profile output.",
        evidence_sources=["test://orders-profile"],
        evidence_iri=evidence,
        sample_size=12,
        sample_scope="All rows in the local Orders table.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=12,
        update_map_snapshot=False,
    )

    brief = db.project_brief(limit=5, profile_candidate_limit=1)

    assert brief.datasets[0].query.readiness == "ready_for_query_planning"
    assert brief.queue_counts["profile_review"] == 1
    assert brief.queue_counts["query_plan_handoff"] == 1
    profile_task = next(
        task
        for task in brief.recommended_next_tasks
        if task.task_type == "profile_review"
    )
    assert profile_task.suggested_next_action is not None
    assert profile_task.suggested_next_action.tool == "doxabase.stage_profile_map_updates"
    assert profile_task.inspection_next_action is not None
    assert profile_task.inspection_next_action.tool == "doxabase.draft_profile_map_updates"
    assert (
        brief.frontier_first_source
        == "recommended_next_tasks:profile_review:inspection"
    )
    assert brief.frontier_first_action == profile_task.inspection_next_action
    assert brief.first_unattended_source == brief.frontier_first_source
    assert brief.first_unattended_action == profile_task.inspection_next_action
    assert (
        brief.frontier_status.mutation_allowed_after
        == "current_frontier_task_available"
    )


def test_project_brief_reports_profile_candidates_hidden_by_limit(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence_iris = [
        f"https://example.test/project#OrdersProfileEvidence{index}"
        for index in range(3)
    ]

    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=10,
    )
    for index, evidence_iri in enumerate(evidence_iris):
        db.record_dataset_profile(
            dataset,
            summary=f"Orders profile pass {index}.",
            evidence_summary=f"Synthetic profile output {index}.",
            evidence_sources=[f"test://orders-profile/{index}"],
            evidence_iri=evidence_iri,
            sample_size=12 + index,
            sample_scope="All rows in the local Orders table.",
            sample_method="DuckDB full-table aggregate profile.",
            row_count=12 + index,
            update_map_snapshot=False,
        )

    brief = db.project_brief(limit=5, profile_candidate_limit=1)
    profile = brief.datasets[0].profile

    assert profile.draft_candidate_count == 3
    assert profile.draft_count == 1
    assert profile.draft_evidence_iris == [evidence_iris[0]]
    assert profile.profile_candidate_omitted_count == 2
    assert profile.omitted_draft_evidence_iris == evidence_iris[1:]
    assert brief.profile_queue_counts["profile_draft_candidates"] == 3
    assert brief.profile_queue_counts["profile_candidate_omitted"] == 2
    assert brief.profile_queue_counts["profile_drafts"] == 1
    assert brief.queue_counts["profile_review"] == 1
    assert brief.omitted_queue_counts == {}

    health_task = next(
        task
        for task in brief.health_tasks
        if task.task_type == "expand_profile_candidate_limit"
    )
    assert health_task.profile_candidate_omitted_count == 2
    assert health_task.suggested_limit == brief.limit
    assert health_task.suggested_profile_candidate_limit == 3
    assert health_task.queue_types == ["profile_review"]
    assert health_task.suggested_next_action is not None
    assert health_task.suggested_next_action.tool == "doxabase.project_brief"
    assert health_task.suggested_next_action.args == {
        "limit": brief.limit,
        "profile_candidate_limit": 3,
    }
    assert brief.next_best_expansion == health_task


def test_project_brief_full_frontier_expansion_combines_limits(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=10,
    )
    for index in range(4):
        db.record_dataset_profile(
            dataset,
            summary=f"Orders profile pass {index}.",
            evidence_summary=f"Synthetic profile output {index}.",
            evidence_sources=[f"test://orders-profile/{index}"],
            evidence_iri=f"https://example.test/project#OrdersProfileEvidence{index}",
            sample_size=12 + index,
            sample_scope="All rows in the local Orders table.",
            sample_method="DuckDB full-table aggregate profile.",
            row_count=12 + index,
            update_map_snapshot=False,
        )
    for index in range(5):
        db.stage_graph_revision(
            summary=f"Stage unrelated review item {index}",
            rationale="Create staged review pressure.",
            additions=[
                {
                    "graph": "map",
                    "content": f"""
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:FrontierCaveat{index} a rc:KnownCaveat .
                    """,
                }
            ],
        )

    brief = db.project_brief(limit=2, profile_candidate_limit=1)

    assert brief.next_best_expansion is not None
    assert brief.next_best_expansion.task_type == "expand_project_brief"
    assert brief.next_best_expansion.suggested_next_action is not None
    assert brief.next_best_expansion.suggested_next_action.args == {
        "limit": 4,
        "profile_candidate_limit": 1,
    }
    full_expansion = brief.full_frontier_expansion
    assert full_expansion is not None
    assert full_expansion.task_type == "expand_full_project_brief"
    assert full_expansion.suggested_limit == 11
    assert full_expansion.exhaustive_suggested_limit == 11
    assert full_expansion.suggested_profile_candidate_limit == 4
    assert full_expansion.profile_candidate_omitted_count == 3
    assert full_expansion.suggested_next_action is not None
    assert full_expansion.suggested_next_action.args == {
        "limit": 11,
        "profile_candidate_limit": 4,
    }
    assert brief.frontier_first_source == "full_frontier_expansion"
    assert brief.frontier_first_action == full_expansion.suggested_next_action
    assert brief.first_unattended_source == "full_frontier_expansion"
    assert brief.first_unattended_action == brief.frontier_first_action
    assert brief.frontier_status.is_complete is False
    assert brief.frontier_status.hidden_task_count == sum(
        brief.omitted_queue_counts.values()
    )
    assert brief.frontier_status.hidden_profile_candidate_count == 3
    assert "profile_review" in brief.frontier_status.hidden_queue_types
    assert brief.frontier_status.first_unattended_source == "full_frontier_expansion"
    assert (
        brief.frontier_status.mutation_allowed_after
        == "frontier_expansion_required_before_mutation"
    )

    rerun = db.project_brief(**full_expansion.suggested_next_action.args)

    assert rerun.omitted_queue_counts == {}
    assert rerun.profile_queue_counts["profile_candidate_omitted"] == 0
    assert rerun.full_frontier_expansion is None
    assert rerun.frontier_status.is_complete is True
    assert rerun.frontier_status.hidden_task_count == 0
    assert rerun.frontier_status.hidden_profile_candidate_count == 0
    assert rerun.frontier_first_action is not None
    assert rerun.frontier_first_source is not None
    assert rerun.first_unattended_action == rerun.frontier_first_action


def test_project_brief_packet_review_participates_in_frontier_expansion(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/packet-frontier#"
    view = f"{base}message_like_rows"
    packet = f"{base}message_like_packet"

    db.record_analysis_packet(
        packet,
        summary="Reviewed packet with a logical view and cookbook recipe.",
        evidence_sources=["scratch://message-like-packet.md"],
        analysis_views=[
            {
                "iri": view,
                "label": "Message-like rows",
                "denominator_description": "Rows that behave like messages.",
                "query_snippets": [
                    {
                        "label": "View definition",
                        "query_text": "select * from messages where is_message",
                    }
                ],
            }
        ],
        query_recipes=[
            {
                "iri": f"{base}register_messages_recipe",
                "label": "Register messages",
                "query_text": "create view messages as select * from read_parquet(?)",
            }
        ],
    )

    tight = db.project_brief(limit=1, profile_candidate_limit=0)

    assert tight.queue_counts["analysis_view_review"] == 1
    assert tight.queue_counts["analysis_packet_review"] == 1
    assert tight.returned_queue_counts == {"analysis_view_review": 1}
    assert tight.omitted_queue_counts == {"analysis_packet_review": 1}
    assert tight.full_frontier_expansion is not None
    assert tight.full_frontier_expansion.suggested_next_action is not None
    assert tight.full_frontier_expansion.suggested_next_action.args == {
        "limit": 2,
        "profile_candidate_limit": 0,
    }
    assert tight.frontier_first_source == "full_frontier_expansion"

    expanded = db.project_brief(
        **tight.full_frontier_expansion.suggested_next_action.args
    )

    assert expanded.omitted_queue_counts == {}
    assert [
        task.task_type for task in expanded.recommended_next_tasks
    ] == [
        "analysis_view_review",
        "analysis_packet_review",
    ]
    packet_task = expanded.recommended_next_tasks[1]
    assert packet_task.resource is not None
    assert packet_task.resource.iri == packet
    assert packet_task.suggested_next_action is not None
    assert packet_task.suggested_next_action.tool == "doxabase.get_context_graph"
    assert packet_task.suggested_next_action.args == {
        "seed_iris": [packet],
        "profile": "resource_brief",
    }


def test_project_brief_expanded_mixed_frontier_routes_staged_recovery_first(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/mixed-frontier#"
    dataset = f"{base}Orders"
    evidence = f"{base}OrdersProfileEvidence"
    storage = db.record_map_storage_access(
        f"{base}OrdersStorage",
        label="Orders local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="object",
        storage_root=str(tmp_path / "orders.parquet"),
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        f"{base}OrdersParquetLayout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=10,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_dataset_profile(
        dataset,
        summary="Orders were profiled with one aggregate.",
        evidence_summary="Synthetic profile evidence.",
        evidence_sources=["test://orders-profile"],
        evidence_iri=evidence,
        sample_size=12,
        sample_scope="All rows in the local Orders table.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=12,
        update_map_snapshot=False,
    )
    db.stage_graph_revision(
        summary="Stage related Orders caveat",
        rationale="Create current staged frontier pressure.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    <{base}OrdersCaveat> a rc:KnownCaveat ;
                        rdfs:label "Orders caveat" .
                """,
            }
        ],
    )

    tight = db.project_brief(limit=1, profile_candidate_limit=0)

    assert tight.frontier_first_source == "full_frontier_expansion"
    assert tight.frontier_first_action is not None
    assert tight.frontier_first_action.tool == "doxabase.project_brief"
    assert tight.frontier_first_action.args == {
        "limit": 4,
        "profile_candidate_limit": 1,
    }
    assert tight.queue_counts == {
        "staged_frontier_review": 1,
        "staged_review": 1,
        "query_plan_handoff": 1,
    }
    assert tight.omitted_queue_counts == {
        "staged_review": 1,
        "query_plan_handoff": 1,
    }
    assert tight.profile_queue_counts["profile_candidate_omitted"] == 1
    assert (
        tight.frontier_status.mutation_allowed_after
        == "frontier_expansion_required_before_mutation"
    )

    expanded = db.project_brief(**tight.frontier_first_action.args)

    assert expanded.omitted_queue_counts == {}
    assert expanded.profile_queue_counts["profile_candidate_omitted"] == 0
    assert expanded.queue_counts == {
        "staged_frontier_review": 1,
        "staged_review": 1,
        "profile_review": 1,
        "query_plan_handoff": 1,
    }
    assert [
        (task.task_type, task.suggested_next_action.tool.removeprefix("doxabase."))
        for task in expanded.recommended_next_tasks
        if task.suggested_next_action is not None
    ] == [
        ("staged_frontier_review", "plan_staged_revision_recovery"),
        ("staged_review", "describe_staged_revision"),
        ("profile_review", "stage_profile_map_updates"),
        ("query_plan_handoff", "draft_query_plan"),
    ]
    assert (
        expanded.frontier_first_source
        == "recommended_next_tasks:staged_frontier_review"
    )
    assert expanded.frontier_first_action is not None
    assert expanded.frontier_first_action.tool == "doxabase.plan_staged_revision_recovery"
    assert expanded.first_unattended_source == expanded.frontier_first_source
    assert expanded.first_unattended_action == expanded.frontier_first_action


def test_project_brief_expanded_mixed_repair_frontier_routes_staged_first(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/mixed-repair-frontier#"
    dataset = f"{base}Tickets"
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
    db.record_dataset_profile(
        dataset,
        summary="Tickets physical profile pass.",
        evidence_summary="Tickets profile evidence.",
        evidence_sources=["test://tickets/full"],
        evidence_iri=evidence,
        sample_size=1200,
        sample_scope="All rows in the local Tickets table.",
        sample_method="DuckDB full-table profile.",
        row_count=1200,
        update_map_snapshot=False,
    )
    db.stage_graph_revision(
        summary="Stage Tickets caveat",
        rationale="Create current staged frontier pressure.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    <{base}TicketsCaveat> a rc:KnownCaveat ;
                        rdfs:label "Tickets caveat" .
                """,
            }
        ],
    )

    tight = db.project_brief(limit=1, profile_candidate_limit=0)

    assert tight.frontier_first_source == "full_frontier_expansion"
    assert tight.frontier_first_action is not None
    assert tight.frontier_first_action.tool == "doxabase.project_brief"
    assert tight.frontier_first_action.args == {
        "limit": 4,
        "profile_candidate_limit": 1,
    }
    assert tight.queue_counts == {
        "staged_frontier_review": 1,
        "staged_review": 1,
        "query_repair_review": 1,
    }
    assert tight.omitted_queue_counts == {
        "staged_review": 1,
        "query_repair_review": 1,
    }
    assert tight.profile_queue_counts["profile_candidate_omitted"] == 1

    expanded = db.project_brief(**tight.frontier_first_action.args)

    assert expanded.omitted_queue_counts == {}
    assert expanded.profile_queue_counts["profile_candidate_omitted"] == 0
    assert expanded.queue_counts == {
        "staged_frontier_review": 1,
        "staged_review": 1,
        "query_repair_review": 1,
        "profile_review": 1,
    }
    assert [
        (task.task_type, task.suggested_next_action.tool.removeprefix("doxabase."))
        for task in expanded.recommended_next_tasks
        if task.suggested_next_action is not None
    ] == [
        ("staged_frontier_review", "plan_staged_revision_recovery"),
        ("staged_review", "describe_staged_revision"),
        ("query_repair_review", "describe_query_context"),
        ("profile_review", "describe_query_context"),
    ]
    profile_task = next(
        task
        for task in expanded.recommended_next_tasks
        if task.task_type == "profile_review"
    )
    assert profile_task.inspection_next_action is not None
    assert profile_task.inspection_next_action.tool == (
        "doxabase.draft_profile_map_updates"
    )
    assert (
        expanded.frontier_first_source
        == "recommended_next_tasks:staged_frontier_review"
    )
    assert expanded.frontier_first_action is not None
    assert expanded.frontier_first_action.tool == "doxabase.plan_staged_revision_recovery"
    assert expanded.first_unattended_source == expanded.frontier_first_source
    assert expanded.first_unattended_action == expanded.frontier_first_action


def test_project_brief_reuses_staged_apply_checks_during_frontier_expansion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged_revision_iris = []
    for index in range(3):
        staged = db.stage_graph_revision(
            summary=f"Stage frontier cache item {index}",
            rationale="Create staged review pressure for low-limit brief expansion.",
            additions=[
                {
                    "graph": "map",
                    "content": f"""
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    <https://example.test/frontier-cache#ReviewNote{index}>
                        rdfs:comment "Review note {index}." .
                    """,
                }
            ],
        )
        staged_revision_iris.append(staged.revision_iri)

    validate_preview_call_count = 0
    original_validate_graph_preview = db._validate_graph_preview

    def counted_validate_graph_preview(*args: object, **kwargs: object) -> object:
        nonlocal validate_preview_call_count
        validate_preview_call_count += 1
        return original_validate_graph_preview(*args, **kwargs)

    monkeypatch.setattr(db, "_validate_graph_preview", counted_validate_graph_preview)

    brief = db.project_brief(limit=1, profile_candidate_limit=0)

    assert brief.staged_review.count == len(staged_revision_iris)
    assert brief.staged_review.returned_count == 1
    assert brief.staged_review.omitted_count == 2
    assert validate_preview_call_count == len(staged_revision_iris)


def test_project_brief_profile_tasks_carry_evidence_scope_for_blocker_actions(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/profile-query#"
    dataset = f"{base}Tickets"
    evidence_iris = [
        f"{base}TicketsProfileEvidenceA",
        f"{base}TicketsProfileEvidenceB",
    ]

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
    for index, evidence_iri in enumerate(evidence_iris):
        db.record_dataset_profile(
            dataset,
            summary=f"Tickets physical profile pass {index}.",
            evidence_summary="Tickets full-profile evidence.",
            evidence_sources=[f"test://tickets/full/{index}"],
            evidence_iri=evidence_iri,
            sample_size=1200 + index,
            sample_scope="All rows in the local Tickets table.",
            sample_method="DuckDB full-table profile.",
            row_count=1200 + index,
            update_map_snapshot=False,
        )

    brief = db.project_brief(limit=5, profile_candidate_limit=2)

    profile_tasks = [
        task
        for task in brief.recommended_next_tasks
        if task.task_type == "profile_review"
    ]
    assert len(profile_tasks) == 2
    assert {task.profile_evidence_iri for task in profile_tasks} == set(
        evidence_iris
    )
    assert all(
        task.suggested_next_action is not None
        and task.suggested_next_action.tool == "doxabase.describe_query_context"
        for task in profile_tasks
    )
    assert all(
        task.inspection_next_action is not None
        and task.inspection_next_action.tool == "doxabase.draft_profile_map_updates"
        for task in profile_tasks
    )
    for evidence_iri in evidence_iris:
        draft = db.draft_profile_map_updates(dataset, evidence_iri)
        query_action = draft.suggested_next_action_groups[
            "query_context_review"
        ][0]
        assert query_action.tool == "doxabase.describe_query_context"
        assert query_action.args == {"iri": dataset}
    query_tasks = [
        task
        for task in brief.recommended_next_tasks
        if task.task_type == "query_repair_review"
    ]
    assert query_tasks[0].profile_evidence_iri is None


def test_project_brief_reuses_staged_review_for_profile_pending_detection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence_a = "https://example.test/project#OrdersProfileEvidenceA"
    evidence_b = "https://example.test/project#OrdersProfileEvidenceB"

    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=10,
    )
    for index, evidence_iri in enumerate([evidence_a, evidence_b], start=1):
        db.record_dataset_profile(
            dataset,
            summary=f"Orders profile run {index}.",
            evidence_summary=f"Synthetic profile run {index}.",
            evidence_sources=[f"test://orders-profile/{index}"],
            evidence_iri=evidence_iri,
            sample_size=10 + index,
            sample_scope="All rows in the local Orders table.",
            sample_method="DuckDB full-table aggregate profile.",
            row_count=10 + index,
            update_map_snapshot=False,
        )

    draft = db.draft_profile_map_updates(dataset, evidence_a)
    staged = db.stage_profile_map_updates(
        **draft.suggested_next_actions[0].args
    )
    assert staged.staged_revision is not None

    apply_check_count = 0
    original_check = db.check_staged_revision_apply

    def counted_check(revision_iri: str):
        nonlocal apply_check_count
        apply_check_count += 1
        return original_check(revision_iri)

    monkeypatch.setattr(db, "check_staged_revision_apply", counted_check)

    brief = db.project_brief(limit=5, profile_candidate_limit=2)

    assert apply_check_count == 1
    profile_tasks = [
        task
        for task in brief.recommended_next_tasks
        if task.task_type == "profile_review"
    ]
    assert {task.profile_evidence_iri for task in profile_tasks} == {
        evidence_a,
        evidence_b,
    }
    pending_task = next(
        task for task in profile_tasks if task.profile_evidence_iri == evidence_a
    )
    assert pending_task.pending_staged_profile_update_iris == [
        staged.staged_revision.revision_iri
    ]


def test_project_brief_routes_blocked_context_tasks_to_context_review(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/project#"
    dataset = f"{base}LocationBlockedEvents"
    storage = db.record_map_storage_access(
        f"{base}LocationBlockedEventsStorage",
        label="Location-blocked local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        f"{base}LocationBlockedEventsLayout",
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

    context = db.describe_query_context(dataset)
    assert context.readiness == "insufficient_metadata"
    assert context.suggested_repair_action_group_count == 0
    assert context.suggested_next_actions[0].tool == "doxabase.draft_query_plan"

    brief = db.project_brief(limit=5)

    assert brief.queue_counts["query_context_review"] == 1
    query_task = next(
        task
        for task in brief.recommended_next_tasks
        if task.task_type == "query_context_review"
    )
    assert query_task.source == "describe_query_context"
    assert "insufficient_metadata" in query_task.reason
    assert query_task.suggested_next_action is not None
    assert query_task.suggested_next_action.tool == "doxabase.describe_query_context"
    assert query_task.suggested_next_action.args == {"iri": dataset}
    assert brief.datasets[0].query.suggested_next_actions[0].tool == (
        "doxabase.draft_query_plan"
    )


def test_project_brief_routes_ready_query_handoffs_to_draft_plan(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage_root = str(tmp_path / "orders.parquet")
    storage = db.record_map_storage_access(
        "https://example.test/project#OrdersLocalStorage",
        label="Orders local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="object",
        storage_root=storage_root,
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#OrdersParquetLayout",
        file_format="rc:Parquet",
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

    brief = db.project_brief(limit=5)

    assert brief.datasets[0].query.readiness == "ready_for_query_planning"
    assert brief.queue_counts == {"query_plan_handoff": 1}
    task = brief.recommended_next_tasks[0]
    assert task.priority == 60
    assert task.task_type == "query_plan_handoff"
    assert task.source == "draft_query_plan"
    assert task.suggested_next_action is not None
    assert task.suggested_next_action.tool == "doxabase.draft_query_plan"
    assert task.suggested_next_action.args["iri"] == dataset
    task_selector = task.suggested_next_action.args["candidate_selector"]
    assert isinstance(task_selector, str)
    assert task_selector.startswith("query-target:")
    assert task.query_plan_handoff_summary is not None
    assert task.query_plan_handoff_summary.handoff_kind == "execution_attempt_ready"
    assert task.query_plan_handoff_summary.selected_candidate_index == 0
    assert task.query_plan_handoff_summary.selected_candidate_selector == (
        task_selector
    )
    assert task.query_plan_handoff_summary.scan_function == "read_parquet"
    assert task.query_plan_handoff_summary.ready_for_execution_attempt is True
    assert (
        task.query_plan_handoff_summary.primary_execution_attempt_blocking_reason_code
        is None
    )


def test_project_brief_ready_query_handoff_uses_full_query_actions(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/project#"
    dataset = f"{base}CustomerChurn"
    status_column = f"{base}CustomerChurnStatus"
    storage = db.record_map_storage_access(
        f"{base}CustomerChurnLocalStorage",
        label="Customer churn local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="object",
        storage_root=str(tmp_path / "customer-churn.parquet"),
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        f"{base}CustomerChurnParquetLayout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Customer churn",
        is_table=True,
        row_count_snapshot=1000,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
    )
    for index, row_count in enumerate((1000, 900, 800)):
        db.record_profile_bundle(
            dataset,
            dataset_summary=f"Customer churn profile pass {index}.",
            evidence_summary="Customer churn profile evidence.",
            evidence_sources=[f"test://customer-churn-profile/{index}"],
            shared_evidence_iri=f"{base}CustomerChurnProfileEvidence{index}",
            row_count=row_count,
            update_map_snapshot=False,
            column_defaults={"update_map_column": False},
            column_profiles=[
                {
                    "column_iri": status_column,
                    "column_name": "status",
                    "summary": f"Status was profiled in pass {index}.",
                }
            ],
        )

    context = db.describe_query_context(dataset)

    assert context.readiness == "ready_for_query_planning"
    assert [
        action.tool.removeprefix("doxabase.") for action in context.suggested_next_actions[:4]
    ] == [
        "describe_profile_run",
        "describe_profile_run",
        "describe_profile_run",
        "draft_query_plan",
    ]

    tight_brief = db.project_brief(limit=1, profile_candidate_limit=3)

    assert tight_brief.queue_counts["query_plan_handoff"] == 1
    assert tight_brief.returned_queue_counts.get("query_plan_handoff", 0) == 0
    assert tight_brief.omitted_queue_counts["query_plan_handoff"] == 1
    assert tight_brief.next_best_expansion is not None
    assert "query_plan_handoff" in tight_brief.next_best_expansion.queue_types
    assert tight_brief.next_best_expansion.exhaustive_suggested_limit >= 2

    brief = db.project_brief(limit=20, profile_candidate_limit=3)

    assert [
        action.tool.removeprefix("doxabase.") for action in brief.datasets[0].query.suggested_next_actions
    ] == [
        "describe_profile_run",
        "describe_profile_run",
        "describe_profile_run",
    ]
    handoff_task = next(
        task
        for task in brief.recommended_next_tasks
        if task.task_type == "query_plan_handoff"
    )
    assert handoff_task.source == "draft_query_plan"
    assert handoff_task.suggested_next_action is not None
    assert handoff_task.suggested_next_action.tool == "doxabase.draft_query_plan"
    assert handoff_task.suggested_next_action.args["iri"] == dataset
    handoff_selector = handoff_task.suggested_next_action.args[
        "candidate_selector"
    ]
    assert isinstance(handoff_selector, str)
    assert handoff_selector.startswith("query-target:")
    assert handoff_task.query_plan_handoff_summary is not None
    assert handoff_task.query_plan_handoff_summary.ready_for_execution_attempt is True


def test_project_brief_query_handoff_summary_surfaces_relation_choice(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WarehouseOrders"
    storage = db.record_map_storage_access(
        "https://example.test/project#warehouse_orders_storage",
        label="Warehouse orders database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        path_templates=[
            "archive.orders_2025",
            "mart.orders",
        ],
        endpoint_profile="warehouse-prod",
        credential_reference="profile:analytics-warehouse-readonly",
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
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    brief = db.project_brief(limit=5)

    task = brief.recommended_next_tasks[0]
    assert task.task_type == "query_plan_handoff"
    assert task.suggested_next_action is not None
    assert task.suggested_next_action.args["iri"] == dataset
    task_selector = task.suggested_next_action.args["candidate_selector"]
    assert isinstance(task_selector, str)
    assert task_selector.startswith("query-target:")
    assert task.query_plan_handoff_summary is not None
    summary = task.query_plan_handoff_summary
    assert summary.handoff_kind == "database_relation_handoff"
    assert summary.selected_candidate_index == 0
    assert summary.selected_candidate_selector == task_selector
    assert summary.relation_identifier == "archive.orders_2025"
    assert summary.connection_reference == "warehouse-prod"
    assert (
        summary.primary_execution_attempt_blocking_reason_code
        == "runtime_resolution_required"
    )
    assert summary.execution_attempt_blocking_reason_codes == [
        "runtime_resolution_required",
    ]
    assert summary.unselected_ready_candidate_indexes == [1]
    assert summary.unselected_direct_clean_candidate_indexes == [1]


def test_project_brief_reserves_recommendation_slots_by_queue(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    for name in ("Alpha", "Beta", "Gamma"):
        db.record_map_dataset(
            f"https://example.test/project#{name}",
            label=name,
            is_table=True,
        )
    db.stage_graph_revision(
        summary="Stage a delta table shell",
        rationale="The project brief should keep staged work visible.",
        additions=[
            {
                "graph": "map",
                "content": """
                @prefix ex: <https://example.test/project#> .
                @prefix rc: <https://richcanopy.org/ns/rc#> .
                @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                ex:Delta a rc:Dataset, rc:Table ;
                    rdfs:label "Delta" .
                """,
            }
        ],
    )

    brief = db.project_brief(limit=2)

    assert brief.queue_counts["query_repair_review"] >= 3
    assert brief.queue_counts["staged_frontier_review"] == 1
    assert brief.queue_counts["staged_review"] == 1
    assert brief.returned_queue_counts["staged_frontier_review"] == 1
    assert brief.returned_queue_counts["staged_review"] == 1
    assert "query_repair_review" not in brief.returned_queue_counts
    assert brief.omitted_queue_counts["query_repair_review"] >= 3
    assert [
        task.task_type for task in brief.recommended_next_tasks
    ] == ["staged_frontier_review", "staged_review"]
    staged_task = brief.recommended_next_tasks[1]
    assert staged_task.priority == 8
    assert staged_task.suggested_next_action is not None
    assert staged_task.suggested_next_action.tool == (
        "doxabase.describe_staged_revision"
    )
    assert brief.active_queue_type_count == 3
    assert brief.returned_queue_type_count == 2
    assert brief.limit_crowded_queue_types == ["query_repair_review"]
    health_task = brief.health_tasks[0]
    assert health_task.task_type == "expand_project_brief"
    assert health_task.queue_types == ["query_repair_review"]
    assert health_task.omitted_queue_counts == brief.omitted_queue_counts
    assert health_task.suggested_limit is not None
    assert health_task.suggested_limit > brief.limit
    assert health_task.suggested_next_action is not None
    assert health_task.suggested_next_action.tool == "doxabase.project_brief"
    assert health_task.suggested_next_action.args == {
        "limit": health_task.suggested_limit,
        "profile_candidate_limit": brief.profile_candidate_limit,
    }
    assert brief.next_best_expansion == health_task


def test_project_brief_selects_pending_staged_representative_per_queue() -> None:
    def task(
        task_type: str,
        priority: int,
        label: str,
        *,
        pending_repair: bool = False,
        pending_profile: bool = False,
    ) -> ProjectBriefRecommendedTask:
        return ProjectBriefRecommendedTask(
            priority=priority,
            task_type=task_type,
            source=label,
            resource=None,
            reason=label,
            suggested_next_action=None,
            pending_staged_repair_iris=(
                [f"https://example.test/project#{label}Repair"]
                if pending_repair
                else []
            ),
            pending_staged_profile_update_iris=(
                [f"https://example.test/project#{label}Profile"]
                if pending_profile
                else []
            ),
        )

    selected = DoxaBase._project_brief_select_recommended_tasks(
        [
            task("query_repair_review", 10, "fresh_query"),
            task(
                "query_repair_review",
                45,
                "pending_query",
                pending_repair=True,
            ),
            task("query_context_review", 20, "blocked_context"),
            task("profile_review", 30, "fresh_profile"),
            task(
                "profile_review",
                55,
                "pending_profile",
                pending_profile=True,
            ),
        ],
        limit=3,
    )

    assert [task.source for task in selected] == [
        "pending_query",
        "blocked_context",
        "pending_profile",
    ]
    assert selected[0].pending_staged_repair_iris
    assert selected[2].pending_staged_profile_update_iris


def test_project_brief_counts_staged_review_rows_hidden_by_limit(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    for index in range(4):
        db.stage_graph_revision(
            summary=f"Stage caveat {index}",
            rationale="The project brief should count hidden staged work.",
            additions=[
                {
                    "graph": "map",
                    "content": f"""
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Caveat{index} a rc:KnownCaveat ;
                        rdfs:label "Caveat {index}" ;
                        rc:caveatDescription "Synthetic caveat {index}." .
                    """,
                }
            ],
        )

    brief = db.project_brief(limit=2)

    assert brief.staged_review.count == 4
    assert brief.staged_review.returned_count == 2
    assert brief.staged_review.omitted_count == 2
    assert len(brief.staged_review.items) == 2
    assert brief.queue_counts["staged_frontier_review"] == 1
    assert brief.queue_counts["staged_review"] == 4
    assert brief.returned_queue_counts["staged_frontier_review"] == 1
    assert brief.returned_queue_counts["staged_review"] == 1
    assert brief.omitted_queue_counts["staged_review"] == 3


def test_project_brief_detects_hidden_pending_query_repairs(
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
    remove_arguments = dict(repair_group.actions[0]["args"])
    remove_arguments["rationale"] = (
        "Reviewed dataset path template as misplaced database relation metadata."
    )
    hidden_staged = db.stage_map_assertion_change(**remove_arguments)
    for index in range(4):
        db.stage_graph_revision(
            summary=f"Stage later unrelated caveat {index}",
            rationale="Make the pending query repair fall outside the visible brief slice.",
            additions=[
                {
                    "graph": "map",
                    "content": f"""
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:LaterCaveat{index} a rc:KnownCaveat ;
                        rdfs:label "Later caveat {index}" ;
                        rc:caveatDescription "Later unrelated caveat {index}." .
                    """,
                }
            ],
        )

    brief = db.project_brief(limit=3)

    visible_staged_iris = {
        item.revision_iri for item in brief.staged_review.items
    }
    assert hidden_staged.revision_iri not in visible_staged_iris
    assert brief.staged_review.count == 5
    assert brief.staged_review.returned_count == 3
    repair_task = next(
        task
        for task in brief.recommended_next_tasks
        if task.task_type == "query_repair_review"
    )
    assert repair_task.pending_staged_repair_iris == [
        hidden_staged.revision_iri
    ]
    assert repair_task.priority == 45
    assert "Pending staged repair(s)" in repair_task.reason


def test_project_brief_detects_hidden_pending_profile_updates(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#SupportEvents"
    evidence = "https://example.test/project#SupportEventsProfileEvidence"
    storage = db.record_map_storage_access(
        "https://example.test/project#support_events_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="directory",
        storage_root=str(tmp_path / "warehouse"),
        path_templates=["support-events.csv"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#support_events_layout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Support events",
        is_table=True,
        row_count_snapshot=10,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Support events were profiled with a full scan.",
        evidence_summary="Support events profile evidence.",
        evidence_sources=["test://support-events-profile"],
        shared_evidence_iri=evidence,
        sample_size=12,
        sample_scope="All rows in the local Support events table.",
        sample_method="DuckDB full-table profile.",
        row_count=12,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
    )
    draft = db.draft_profile_map_updates(dataset, evidence)
    staged = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=draft.representative_recommendation_indexes,
    )
    assert staged.staged_revision is not None
    hidden_staged_iri = staged.staged_revision.revision_iri
    for index in range(4):
        db.stage_graph_revision(
            summary=f"Stage later profile-unrelated caveat {index}",
            rationale="Make the pending profile update fall outside the visible brief slice.",
            additions=[
                {
                    "graph": "map",
                    "content": f"""
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:LaterProfileCaveat{index} a rc:KnownCaveat ;
                        rdfs:label "Later profile caveat {index}" ;
                        rc:caveatDescription "Later unrelated profile caveat {index}." .
                    """,
                }
            ],
        )

    brief = db.project_brief(limit=4, profile_candidate_limit=1)

    visible_staged_iris = {
        item.revision_iri for item in brief.staged_review.items
    }
    assert hidden_staged_iri not in visible_staged_iris
    assert brief.staged_review.count == 5
    assert brief.staged_review.returned_count == 4
    profile_task = next(
        task
        for task in brief.recommended_next_tasks
        if task.task_type == "profile_review"
    )
    assert profile_task.pending_staged_profile_update_iris == [
        hidden_staged_iri
    ]
    assert profile_task.priority == 55
    assert "Pending staged profile update(s)" in profile_task.reason
    assert profile_task.suggested_next_action is not None
    assert profile_task.suggested_next_action.tool == (
        "doxabase.draft_profile_map_updates"
    )


def test_project_brief_reports_limit_crowded_queue_types(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.record_map_dataset(
        "https://example.test/project#RiskScores",
        label="Risk Scores",
        description="Synthetic fixture FAKE_SECRET_TOKEN_HEALTH_TASK.",
        is_table=True,
    )
    db.record_map_dataset(
        "https://example.test/project#WebhookAPI",
        label="Webhook API",
        is_table=False,
    )
    support_tickets = "https://example.test/project#SupportTickets"
    support_profile = "https://example.test/project#SupportTicketsProfileEvidence"
    db.record_map_dataset(
        support_tickets,
        label="Support Tickets",
        is_table=True,
        row_count_snapshot=10,
    )
    db.record_dataset_profile(
        support_tickets,
        summary="Support tickets profile drift.",
        evidence_summary="Synthetic profile output with row-count drift.",
        evidence_sources=["test://support-tickets-profile"],
        evidence_iri=support_profile,
        sample_size=12,
        sample_scope="All local support tickets.",
        sample_method="Synthetic aggregate profile.",
        row_count=12,
        update_map_snapshot=False,
    )
    db.stage_graph_revision(
        summary="Stage support ticket freshness caveat",
        rationale="The project brief should expose staged review as an active queue.",
        additions=[
            {
                "graph": "map",
                "content": """
                @prefix ex: <https://example.test/project#> .
                @prefix rc: <https://richcanopy.org/ns/rc#> .
                @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                ex:SupportTicketFreshnessCaveat a rc:KnownCaveat ;
                    rdfs:label "Support ticket freshness caveat" ;
                    rc:caveatDescription "Synthetic records may lag source intake." .
                """,
            }
        ],
    )

    brief = db.project_brief(limit=3, profile_candidate_limit=1)

    assert brief.active_queue_type_count == 5
    assert brief.returned_queue_type_count == 3
    assert brief.queue_counts["staged_frontier_review"] == 1
    assert brief.queue_counts["staged_review"] == 1
    assert "staged_review" not in brief.omitted_queue_counts
    assert brief.limit_crowded_queue_types == [
        "non_tabular_asset_review",
        "profile_review",
    ]
    assert [
        task.task_type for task in brief.recommended_next_tasks
    ] == [
        "staged_frontier_review",
        "staged_review",
        "query_repair_review",
    ]
    expand_task = next(
        task for task in brief.health_tasks if task.task_type == "expand_project_brief"
    )
    assert "non_tabular_asset_review" in expand_task.queue_types
    assert "profile_review" in expand_task.queue_types
    assert "staged_review" not in expand_task.queue_types
    assert expand_task.suggested_limit is not None
    assert expand_task.exhaustive_suggested_limit == sum(brief.queue_counts.values())
    assert expand_task.exhaustive_suggested_limit >= expand_task.suggested_limit
    assert expand_task.suggested_next_action is not None
    assert "exhaustive_suggested_limit" in expand_task.suggested_next_action.reason
    assert brief.next_best_expansion == expand_task
    privacy_task = next(
        task for task in brief.health_tasks if task.task_type == "privacy_export_review"
    )
    assert [
        task.task_type for task in brief.health_tasks
    ] == ["expand_project_brief", "privacy_export_review"]
    assert brief.safety_first_action is not None
    assert brief.safety_first_action == privacy_task.suggested_next_action
    assert brief.safety_first_source == "health_tasks:privacy_export_review"
    assert brief.first_unattended_action == privacy_task.suggested_next_action
    assert brief.first_unattended_source == "health_tasks:privacy_export_review"
    assert (
        brief.frontier_first_action
        == brief.full_frontier_expansion.suggested_next_action
    )
    assert brief.frontier_status.is_complete is False
    assert (
        brief.frontier_status.mutation_allowed_after
        == "safety_review_required_before_frontier_or_mutation"
    )
    expanded = db.project_brief(
        **brief.full_frontier_expansion.suggested_next_action.args
    )
    assert expanded.frontier_status.is_complete is True
    assert expanded.safety_first_action is not None
    assert expanded.safety_first_source == "health_tasks:privacy_export_review"
    assert expanded.first_unattended_action == expanded.safety_first_action
    assert expanded.first_unattended_source == "health_tasks:privacy_export_review"
    assert expanded.frontier_status.mutation_allowed_after == (
        "safety_review_required_before_frontier_or_mutation"
    )
    handoff_preflight = db.export_preflight(
        export_kind="handoff_bundle",
        graphs=["project"],
    )
    assert privacy_task.sensitive_literal_count == (
        handoff_preflight.sensitive_literal_count
    )
    assert privacy_task.suggested_next_action is not None
    assert privacy_task.suggested_next_action.tool == "doxabase.export_preflight"
    assert "FAKE_SECRET" not in json.dumps(to_jsonable(brief.health_tasks))


def test_project_brief_surfaces_sanitized_privacy_health_task(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_TOKEN_PROJECT_BRIEF"
    db.record_map_dataset(
        "https://example.test/project#CredentialNotes",
        label="Credential notes",
        description=f"Synthetic fixture {fake_secret}.",
    )

    brief = db.project_brief(limit=5)

    privacy_task = next(
        task for task in brief.health_tasks if task.task_type == "privacy_export_review"
    )
    assert privacy_task.sensitive_literal_count == 1
    assert "FAKE_SECRET" not in privacy_task.reason
    assert privacy_task.suggested_next_action is not None
    assert privacy_task.suggested_next_action.tool == "doxabase.export_preflight"
    assert privacy_task.suggested_next_action.args == {
        "export_kind": "handoff_bundle",
        "graphs": ["project"],
        "limit": 20,
    }
    assert brief.safety_first_action == privacy_task.suggested_next_action
    assert brief.safety_first_source == "health_tasks:privacy_export_review"
    assert brief.datasets[0].dataset.description == (
        "[REDACTED:fake_secret_marker]"
    )
    assert "FAKE_SECRET" not in json.dumps(to_dict(privacy_task))
    assert fake_secret not in json.dumps(to_dict(brief))


def test_project_brief_surfaces_invalid_export_health_task(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rcg: <https://richcanopy.org/graph/> .

        rcg:observations {
            ex:obs_without_evidence a rc:Observation ;
                rc:summary "Scanner-clean invalid observation." .
        }
        """
    )

    preflight = db.export_preflight(
        export_kind="handoff_bundle",
        graphs=["project"],
    )
    assert preflight.scanner_clean is True
    assert preflight.would_block_invalid_export is True
    assert preflight.suggested_next_actions[0].tool == "doxabase.validate_graph"

    brief = db.project_brief(limit=5)

    validation_task = next(
        task
        for task in brief.health_tasks
        if task.task_type == "export_validation_review"
    )
    assert validation_task.source == "export_preflight"
    assert validation_task.would_block_invalid_export is True
    assert validation_task.validation_scope == "all"
    assert validation_task.validation_conforms is False
    assert validation_task.validation_result_count == preflight.validation_result_count
    assert validation_task.suggested_next_action is not None
    assert validation_task.suggested_next_action.tool == "doxabase.validate_graph"
    assert validation_task.suggested_next_action.args == {
        "scope": "all",
        "limit_results": 20,
    }
    assert brief.safety_first_action == validation_task.suggested_next_action
    assert brief.safety_first_source == "health_tasks:export_validation_review"
    assert brief.first_unattended_action == validation_task.suggested_next_action
    assert brief.first_unattended_source == "health_tasks:export_validation_review"
    assert (
        brief.frontier_status.mutation_allowed_after
        == "safety_review_required_before_frontier_or_mutation"
    )


def test_project_brief_privacy_precedes_overlapping_export_validation_gate(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rcg: <https://richcanopy.org/graph/> .

        rcg:observations {
            ex:dirty_invalid_obs a rc:Observation ;
                rc:summary "Synthetic FAKE_SECRET_TOKEN_OVERLAP invalid observation." .
        }
        """
    )

    preflight = db.export_preflight(
        export_kind="handoff_bundle",
        graphs=["project"],
    )
    assert preflight.scanner_clean is False
    assert preflight.would_block_invalid_export is True

    brief = db.project_brief(limit=5)
    health_by_type = {task.task_type: task for task in brief.health_tasks}
    privacy_task = health_by_type["privacy_export_review"]
    validation_task = health_by_type["export_validation_review"]

    assert privacy_task.priority < validation_task.priority
    assert [
        task.task_type for task in brief.health_tasks
    ] == [
        "privacy_export_review",
        "export_validation_review",
    ]
    assert validation_task.suggested_next_action is not None
    assert validation_task.suggested_next_action.tool == "doxabase.validate_graph"
    assert "scanner-clean" not in validation_task.reason
    assert brief.safety_first_action == privacy_task.suggested_next_action
    assert brief.safety_first_source == "health_tasks:privacy_export_review"
    assert brief.first_unattended_action == privacy_task.suggested_next_action
    assert brief.first_unattended_source == "health_tasks:privacy_export_review"
    assert (
        brief.frontier_status.mutation_allowed_after
        == "safety_review_required_before_frontier_or_mutation"
    )


def test_project_brief_redacts_nested_query_and_staged_payloads(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_PROJECT_BRIEF_NESTED_PAYLOAD"
    base = "https://example.test/project#"
    dataset = f"{base}Orders"
    storage = db.record_map_storage_access(
        f"{base}OrdersLocalStorage",
        label=f"Orders local storage {fake_secret}",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="object",
        storage_root=str(tmp_path / fake_secret / "orders.parquet"),
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        f"{base}OrdersParquetLayout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label=f"Orders {fake_secret}",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.stage_graph_revision(
        summary=f"Stage {fake_secret} staged review summary",
        rationale="Exercise project_brief staged review redaction.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:OrdersBriefNestedProbe a rc:Dataset .
                """,
            }
        ],
    )

    brief = db.project_brief(limit=5)
    payload = json.dumps(to_jsonable(brief), sort_keys=True)

    assert fake_secret not in payload
    assert "FAKE_SECRET" not in payload
    assert "[REDACTED:fake_secret_marker]" in payload
    query_action = brief.datasets[0].query.suggested_next_actions[0]
    assert query_action.tool == "doxabase.draft_query_plan"
    assert fake_secret not in json.dumps(to_jsonable(query_action), sort_keys=True)
    assert brief.staged_review.items[0].summary == "[REDACTED:fake_secret_marker]"
    assert brief.recommended_next_tasks[1].resource is not None
    assert brief.recommended_next_tasks[1].resource.label == (
        "[REDACTED:fake_secret_marker]"
    )


def test_project_brief_privacy_health_uses_handoff_preflight_scope(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_PROJECT_BRIEF_HANDOFF"
    db.record_map_storage_access(
        "https://example.test/project#orders_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=f"/tmp/{fake_secret}/orders",
    )
    db.stage_graph_revision(
        summary="Stage project brief privacy probe",
        rationale="Create revision snapshots over the sensitive map graph.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:OrdersBriefProbe a rc:Dataset .
                """,
            }
        ],
    )

    handoff_preflight = db.export_preflight(
        export_kind="handoff_bundle",
        graphs=["project"],
    )
    graph_scan = db.scan_sensitive_literals(graphs="project")
    assert handoff_preflight.graph_sensitive_literal_count == graph_scan.match_count
    assert handoff_preflight.snapshot_sensitive_literal_count >= 1
    assert handoff_preflight.sensitive_literal_count > graph_scan.match_count

    brief = db.project_brief(limit=5)

    privacy_task = next(
        task for task in brief.health_tasks if task.task_type == "privacy_export_review"
    )
    assert privacy_task.sensitive_literal_count == (
        handoff_preflight.sensitive_literal_count
    )
    assert "revision-snapshot" in privacy_task.reason
    assert fake_secret not in json.dumps(to_dict(privacy_task))


def test_project_brief_surfaces_fixture_storage_health_task(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"
    db.record_map_dataset(
        dataset,
        label="AIS Daily Broadcast Positions",
        is_table=True,
    )

    brief = db.project_brief(limit=5)

    fixture_task = next(
        task
        for task in brief.health_tasks
        if task.task_type == "query_fixture_staleness_review"
    )
    assert fixture_task.source == "fixture_storage_access_check"
    assert fixture_task.priority == 15
    assert fixture_task.queue_types == ["query_repair_review"]
    assert fixture_task.fixture_names == ["AIS"]
    assert fixture_task.storage_access_count == 0
    assert dataset in fixture_task.known_fixture_table_iris
    assert fixture_task.suggested_next_action is not None
    assert fixture_task.suggested_next_action.tool == "doxabase.describe_query_context"
    assert fixture_task.suggested_next_action.args == {"iri": dataset}
    assert "zero rc:StorageAccess" in fixture_task.reason
    assert brief.safety_first_action is not fixture_task.suggested_next_action
    repair_task = next(
        task
        for task in brief.recommended_next_tasks
        if task.task_type == "query_repair_review"
    )
    assert repair_task.task_advisories
    assert repair_task.task_advisories[0]["code"] == (
        "query_fixture_staleness_review"
    )
    assert repair_task.task_advisories[0]["recommended_handling"] == (
        "review_health_task_before_staging"
    )
    assert repair_task.task_advisories[0]["storage_access_count"] == 0
    assert repair_task.task_group is not None
    assert repair_task.task_group["group_type"] == (
        "query_fixture_staleness_review"
    )
    assert repair_task.task_group["suppression_policy"] == (
        "review_group_before_member_mutation"
    )

    db.record_map_storage_access(
        "https://example.test/project#ais_storage",
        datasets=[dataset],
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/tmp/ais-fixture",
    )
    repaired_brief = db.project_brief(limit=5)
    assert "query_fixture_staleness_review" not in {
        task.task_type for task in repaired_brief.health_tasks
    }
    assert all(
        not task.task_advisories
        for task in repaired_brief.recommended_next_tasks
    )


def test_project_brief_flags_fixture_table_without_linked_storage(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"
    unrelated = "https://example.test/project#UnrelatedOrders"
    db.record_map_dataset(
        dataset,
        label="AIS Daily Broadcast Positions",
        is_table=True,
    )
    db.record_map_dataset(unrelated, label="Unrelated orders", is_table=True)
    db.record_map_storage_access(
        "https://example.test/project#unrelated_storage",
        datasets=[unrelated],
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/tmp/unrelated",
    )

    brief = db.project_brief(limit=5)

    fixture_task = next(
        task
        for task in brief.health_tasks
        if task.task_type == "query_fixture_staleness_review"
    )
    assert fixture_task.storage_access_count == 1
    assert fixture_task.known_fixture_table_iris == [dataset]
    assert "without linked rc:StorageAccess" in fixture_task.reason
    repair_task = next(
        task
        for task in brief.recommended_next_tasks
        if task.task_type == "query_repair_review"
        and task.resource is not None
        and task.resource.iri == dataset
    )
    assert repair_task.task_advisories[0]["storage_access_count"] == 1
    assert repair_task.task_group is not None
    assert repair_task.task_group["group_member_count"] == 1

    db.record_map_storage_access(
        "https://example.test/project#ais_storage",
        datasets=[dataset],
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/tmp/ais-fixture",
    )
    repaired_brief = db.project_brief(limit=5)
    assert "query_fixture_staleness_review" not in {
        task.task_type for task in repaired_brief.health_tasks
    }


def test_project_brief_groups_fixture_storage_query_task_advisories(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    datasets = [
        "https://richcanopy.org/example/manifest/ais#DailyBroadcasts",
        "https://richcanopy.org/example/manifest/ais#DailyIndex",
        "https://richcanopy.org/example/manifest/polymarket#Trades",
    ]
    for dataset in datasets:
        db.record_map_dataset(
            dataset,
            label=dataset.rsplit("#", 1)[-1],
            is_table=True,
        )

    brief = db.project_brief(limit=3)

    repair_tasks = [
        task
        for task in brief.recommended_next_tasks
        if task.task_type == "query_repair_review"
    ]
    assert len(repair_tasks) == 3
    assert brief.first_unattended_source == (
        "recommended_next_tasks:query_repair_review"
    )
    for task in repair_tasks:
        assert task.task_advisories[0]["code"] == (
            "query_fixture_staleness_review"
        )
        assert task.task_advisories[0]["fixture_names"] == ["AIS", "Polymarket"]
        assert task.task_group is not None
        assert task.task_group["group_key"] == (
            "query_fixture_staleness_review:"
            "known_fixture_tables_without_storage_accesses"
        )
        assert task.task_group["group_member_count"] == 3
        assert task.task_group["returned_group_member_count"] == 3
        assert task.task_group["representative_resource_iri"] == datasets[0]


def test_project_brief_surfaces_stale_seed_health_task(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    _delete_base_ontology_seed_terms(
        db,
        ["rc:GraphPatchRole", "rc:CandidateRevision"],
    )

    brief = db.project_brief(limit=5)

    seed_task = next(
        task for task in brief.health_tasks if task.task_type == "seed_recovery_review"
    )
    assert seed_task.missing_seed_terms == [
        "rc:GraphPatchRole",
        "rc:CandidateRevision",
    ]
    assert "immutable base_ontology is missing current staging vocabulary" in (
        seed_task.reason
    )
    assert seed_task.suggested_next_action is not None
    assert seed_task.suggested_next_action.tool == "doxabase.export_preflight"
    assert seed_task.suggested_next_action.args == {
        "export_kind": "handoff_bundle",
        "graphs": ["project"],
        "limit": 20,
        "validation_scope": "map",
    }
    assert seed_task.current_staged_revision_count == 0
    assert brief.safety_first_action == seed_task.suggested_next_action
    assert brief.safety_first_source == "health_tasks:seed_recovery_review"
    assert brief.first_unattended_action == seed_task.suggested_next_action
    assert brief.first_unattended_source == "health_tasks:seed_recovery_review"
    assert brief.frontier_status.first_unattended_source == (
        "health_tasks:seed_recovery_review"
    )
    assert brief.frontier_status.mutation_allowed_after == (
        "safety_review_required_before_frontier_or_mutation"
    )


def test_project_brief_stale_seed_health_task_routes_staged_work_to_handoff(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = db.stage_graph_revision(
        summary="Stage stale-seed recovery sample",
        rationale="Exercise staged-work recovery guidance for stale seeds.",
        additions=[
            {
                "graph": "map",
                "content": """
                @prefix ex: <https://example.test/project#> .
                ex:stagedSeedSubject ex:stagedSeedPredicate ex:stagedSeedObject .
                """,
            }
        ],
    )
    _delete_base_ontology_seed_terms(
        db,
        ["rc:GraphPatchRole", "rc:CandidateRevision"],
    )

    brief = db.project_brief(limit=5)

    assert brief.staged_review.count == 1
    assert brief.staged_review.items[0].revision_iri == staged.revision_iri
    seed_task = next(
        task for task in brief.health_tasks if task.task_type == "seed_recovery_review"
    )
    assert seed_task.current_staged_revision_count == 1
    assert seed_task.queue_types == ["staged_review"]
    assert "revision snapshot JSON" in seed_task.reason
    assert "import_handoff_bundle()" in seed_task.reason
    assert seed_task.suggested_next_action is not None
    assert seed_task.suggested_next_action.tool == "doxabase.export_preflight"
    assert seed_task.suggested_next_action.args == {
        "export_kind": "handoff_bundle",
        "graphs": ["project"],
        "limit": 20,
        "validation_scope": "map",
    }
    assert brief.safety_first_action == seed_task.suggested_next_action
    assert brief.safety_first_source == "health_tasks:seed_recovery_review"
    assert brief.first_unattended_action == seed_task.suggested_next_action
    assert brief.first_unattended_source == "health_tasks:seed_recovery_review"


def test_project_brief_routes_non_tabular_assets_to_context_review(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    api = "https://example.test/project#RiskSignalsAPI"
    docs = "https://example.test/project#RiskSignalsOpenAPI"
    storage = "https://example.test/project#RiskSignalsHTTPSAccess"
    caveat = "https://example.test/project#RiskSignalsCaveat"

    db.record_map_storage_access(
        storage,
        label="Risk signals HTTPS access",
        storage_protocol="rc:HTTPSStorage",
        access_mode="rc:ReadOnlyAccess",
        location_kind="object",
        storage_root="https://api.example.test/risk/signals",
        datasets=[api],
    )
    db.record_map_caveat(
        caveat,
        label="rate limited endpoint",
        description="The API is rate limited and should not be bulk queried.",
        targets=[api],
    )
    db.record_map_dataset(
        api,
        label="Risk signals API",
        is_table=False,
        extra_types=["https://example.test/project#APIEndpoint"],
        caveats=[caveat],
        storage_accesses=[storage],
    )
    db.record_map_dataset(
        docs,
        label="Risk signals OpenAPI document",
        is_table=False,
        extra_types=["https://example.test/project#APIDocument"],
    )
    claim = db.record_claim_observation(
        summary="Risk signals API has live-service semantics.",
        claim_text="The API endpoint should be inspected as a live service, not a table.",
        claim_kind="rc:CaveatClaim",
        claim_targets=[api],
        evidence_sources=["test://risk-signals-api-note"],
    )
    db.record_pattern(
        summary="Risk signals assets need service-oriented handoff.",
        pattern_text=(
            "Use the API endpoint and OpenAPI document as non-tabular context "
            "before planning any extraction."
        ),
        rationale="The endpoint and document describe a live API surface.",
        pattern_targets=[api, docs],
        supporting_claims=[claim.claim_iri],
        evidence_sources=["test://risk-signals-openapi"],
    )

    brief = db.project_brief(limit=5)

    datasets_by_label = {dataset.dataset.label: dataset for dataset in brief.datasets}
    assert datasets_by_label["Risk signals API"].is_table is False
    assert datasets_by_label["Risk signals OpenAPI document"].is_table is False
    assert {
        dataset.query.readiness for dataset in datasets_by_label.values()
    } == {"not_applicable_non_tabular_asset"}
    assert brief.dataset_query_readiness_counts == {
        "not_applicable_non_tabular_asset": 2,
    }
    assert brief.queue_counts == {"non_tabular_asset_review": 2}
    assert "query_repair_review" not in brief.queue_counts
    assert "query_context_review" not in brief.queue_counts

    tasks = {
        task.resource.iri: task
        for task in brief.recommended_next_tasks
        if task.resource is not None
    }
    api_task = tasks[api]
    assert api_task.task_type == "non_tabular_asset_review"
    assert api_task.suggested_next_action is not None
    assert api_task.suggested_next_action.tool == "doxabase.get_context_graph"
    assert api_task.suggested_next_action.args == {
        "seed_iris": [api],
        "profile": "deep_lore",
    }


def test_recovery_first_safe_action_prefers_semantic_frontier_over_informational(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    already_effective = "https://example.test/project#AlreadyEffective"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    event_source = db.stage_graph_revision(
        summary="Model Orders as event rows",
        rationale="Choose event-row framing for Orders.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix ex: <https://example.test/project#> .

                    <{orders}> a ex:EventRow .
                """,
            }
        ],
        revision_anchors=[orders],
        validation_scope="all",
    )
    db.apply_staged_revision(event_source.revision_iri)
    informational_source = db.stage_graph_revision(
        summary="Stage already-effective table",
        rationale="This staged source will already be current map state.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    <{already_effective}> a rc:Dataset .
                """,
            }
        ],
    )
    db.record_map_dataset(already_effective, label="Already effective")
    semantic_alternative = db.stage_systematisation(
        summary="Review aggregate row alternative",
        intent=(
            "Keep the aggregate-row alternative visible after the event-row "
            "source was applied."
        ),
        anchors=[orders],
        framings=[
            {
                "label": "Aggregate row alternative",
                "graph": "map",
                "content": f"""
                    @prefix ex: <https://example.test/project#> .

                    <{orders}> a ex:AggregateRow .
                """,
                "alternative_to": event_source.revision_iri,
            }
        ],
        validation_scope="all",
    )
    semantic_iri = semantic_alternative.staged_revisions[0].revision_iri
    revision_iris = [informational_source.revision_iri, semantic_iri]

    plan = db.plan_staged_revision_recovery(
        revision_iris,
        current_staged_work_only=False,
        drift_detail="exact",
    )

    assert plan.lane_counts == {"informational": 1, "apply_after_review": 1}
    assert plan.would_restage_revision_iris == []
    assert plan.mutation_allowed_after == (
        "semantic_review_required_before_mutation"
    )
    assert plan.first_mutation_action is None
    assert plan.first_safe_review_or_mutation_action is not None
    assert plan.first_safe_review_or_mutation_action.tool == (
        "doxabase.describe_staged_revision"
    )
    assert plan.first_safe_review_or_mutation_action.args == {
        "iri": semantic_iri
    }
    assert plan.first_safe_review_or_mutation_source == "semantic_frontier_review"

    session = db.start_staged_revision_recovery_session(
        revision_iris,
        summary="Semantic frontier with informational source first",
        current_staged_work_only=False,
        drift_detail="exact",
    )
    described = db.describe_staged_revision_recovery_session(
        session.session_iri,
        drift_detail="exact",
    )

    assert described.current_plan.first_safe_review_or_mutation_action == (
        plan.first_safe_review_or_mutation_action
    )
    assert described.current_plan.first_safe_review_or_mutation_source == (
        "semantic_frontier_review"
    )


def test_project_brief_prioritizes_pending_staged_query_repair(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    relation = "mart.orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_database_storage",
        label="Orders database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        path_templates=[relation],
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
        path_templates=[relation],
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    context = db.describe_query_context(dataset)
    repair_group = context.suggested_repair_action_groups[0]
    remove_action = repair_group.actions[0]
    remove_arguments = dict(remove_action["args"])
    remove_arguments["rationale"] = (
        "Reviewed dataset path template as misplaced database relation metadata."
    )
    staged = db.stage_map_assertion_change(**remove_arguments)

    brief = db.project_brief(limit=3)

    assert brief.queue_counts["query_repair_review"] == 1
    assert brief.queue_counts["staged_frontier_review"] == 1
    assert brief.queue_counts["staged_review"] == 1
    assert [task.task_type for task in brief.recommended_next_tasks] == [
        "staged_frontier_review",
        "staged_review",
        "query_repair_review",
    ]
    frontier_task, staged_task, query_task = brief.recommended_next_tasks
    assert frontier_task.suggested_next_action is not None
    assert frontier_task.suggested_next_action.tool == (
        "doxabase.plan_staged_revision_recovery"
    )
    assert staged_task.suggested_next_action is not None
    assert staged_task.suggested_next_action.tool == "doxabase.describe_staged_revision"
    assert staged_task.resource is not None
    assert staged_task.resource.iri == staged.revision_iri
    assert query_task.priority == 45
    assert query_task.pending_staged_repair_iris == [staged.revision_iri]
    assert "Pending staged repair(s)" in query_task.reason
    assert query_task.suggested_next_action is not None
    assert query_task.suggested_next_action.tool == "doxabase.describe_query_context"
    assert to_dict(query_task)["pending_staged_repair_iris"] == [staged.revision_iri]
    assert brief.staged_review.items[0].queue == "apply_after_review"
    assert brief.staged_review.items[0].revision_anchor_iris == [dataset]
    recovery = db.plan_staged_revision_recovery(
        current_staged_work_only=True,
        limit=3,
    )
    assert recovery.next_action_queue == {"apply_after_review": [staged.revision_iri]}

    db.apply_staged_revision(staged.revision_iri)
    repaired_context = db.describe_query_context(dataset)
    assert repaired_context.readiness == "ready_for_query_planning"
    assert repaired_context.issues == []
    assert repaired_context.suggested_repair_action_groups == []
    post_apply_brief = db.project_brief(limit=3)
    assert post_apply_brief.queue_counts == {"query_plan_handoff": 1}
    assert post_apply_brief.recommended_next_tasks[0].task_type == (
        "query_plan_handoff"
    )
    post_apply_slice = db.get_context_graph(dataset, profile="dataset_brief")
    assert post_apply_slice.suggested_next_actions == []
    assert post_apply_slice.warnings == []


def test_resource_brief_packet_outgoing_refs_prioritize_action_links_over_artifacts(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/analysis-packet-priority#"
    source = f"{base}messages"
    packet = f"{base}packet"
    view = f"{base}z_review_view"
    recipe = f"{base}z_query_recipe"
    task = f"{base}z_followup_task"
    artifacts = [
        {
            "iri": f"{base}a_artifact_{index:02d}",
            "label": f"Bulk artifact {index:02d}",
            "summary": "Bulk visualization or aggregate output.",
            "source_path": f"scratch://bulk-artifact-{index:02d}.json",
            "artifact_role": "bulk output",
            "media_type": "application/json",
            "supports": [view],
        }
        for index in range(40)
    ]

    db.record_map_dataset(source, label="Messages", is_table=True)
    result = db.record_analysis_packet(
        packet,
        summary="Packet with many artifacts and a few action links.",
        analysis_views=[
            {
                "iri": view,
                "label": "Reviewed message population",
                "source_datasets": [source],
                "denominator_description": "Reviewed message rows.",
            },
        ],
        artifacts=artifacts,
        query_recipes=[
            {
                "iri": recipe,
                "label": "Review query",
                "query_text": "select * from messages where reviewed",
                "query_language": "DuckDB SQL",
                "query_engine": "duckdb",
                "targets": [view],
            }
        ],
        followup_tasks=[
            {
                "iri": task,
                "label": "Inspect reviewed population",
                "task_text": "Read the packet view before bulk artifacts.",
                "targets": [view],
            }
        ],
    )

    context = to_dict(db.get_context_graph([packet], profile="resource_brief"))
    outgoing_iris = {
        resource["iri"]
        for resource in context["resources"]
        if any(
            route["route"] == "outgoing_reference"
            and route["source_iri"] == packet
            for route in resource["routes"]
        )
    }

    assert context["route_counts"]["outgoing_reference"] == 25
    assert result.artifact_iris[-1] not in outgoing_iris
    assert {view, recipe, task}.issubset(outgoing_iris)
    assert any(
        action["tool"] == "doxabase.describe_analysis_view"
        and action["args"]["iri"] == view
        for action in context["suggested_next_actions"]
    )
    assert any(
        "omitted" in warning and "outgoing reference" in warning
        for warning in context["warnings"]
    )


def test_get_context_graph_returns_route_explained_dataset_brief(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/enron#"
    messages = f"{base}eml_messages"
    doc_id = f"{base}eml_messages__doc_id"
    claim = f"{base}claim_doc_id_join"

    db.record_map_dataset(
        messages,
        label="EML messages",
        description="Parsed email message records.",
        is_table=True,
        path_templates=["data/messages.parquet"],
        layout_verification_status="rc:CandidateLayout",
        layout_verification_note="Path pattern is plausible but not verified.",
    )
    db.record_map_column(
        doc_id,
        table_iri=messages,
        column_name="doc_id",
        physical_type="rc:Varchar",
    )
    claim_result = db.record_claim_observation(
        summary="doc_id behaves as the message entity key.",
        claim_text="doc_id behaves as the message entity key.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=[doc_id],
        claim_iri=claim,
        evidence_summary="Unit test evidence.",
        source_path="tests/test_doxabase_core.py",
        source_kind="rc:DocumentationSource",
    )
    pattern_result = db.record_pattern(
        summary="doc_id is the stable message identity handle.",
        pattern_text="Use doc_id as the stable message identity handle.",
        rationale="A claim about the table column supports this reader protocol.",
        pattern_targets=[messages],
        supporting_claims=[claim_result.claim_iri],
    )

    context_slice = db.get_context_graph(
        [messages],
        profile="dataset_brief",
        include_trig=True,
        max_triples=200,
    )

    assert context_slice.profile == "dataset_brief"
    assert context_slice.seeds[0].iri == messages
    assert context_slice.dataset_contexts[0].iri == messages
    assert context_slice.pattern_contexts[0].iri == pattern_result.pattern_iri
    assert context_slice.truncated is False
    assert context_slice.truncation_scope == "triples_only"
    assert context_slice.resource_count == len(context_slice.resources)
    assert context_slice.triple_count <= 200
    assert context_slice.returned_triple_count == context_slice.triple_count
    assert context_slice.candidate_triple_count == context_slice.triple_count
    assert context_slice.omitted_triple_count == 0
    assert context_slice.graph_counts["map"] >= 1
    assert context_slice.graph_counts["patterns"] >= 1
    assert context_slice.graph_counts["observations"] >= 1
    assert context_slice.graph_counts["evidence"] >= 1
    assert context_slice.route_counts["dataset_column"] == 1
    assert context_slice.route_counts["layout_verification_status"] == 1
    assert context_slice.route_counts["linked_pattern"] == 1
    assert context_slice.route_counts["supporting_claim"] >= 1
    assert context_slice.reading_order[0].startswith("Start with seeds")
    route_legend = {row.route: row for row in context_slice.route_legend}
    assert route_legend["seed"].count == 1
    assert route_legend["seed"].priority == 0
    assert route_legend["seed"].meaning == (
        "The resource the caller asked about directly."
    )
    assert route_legend["dataset_column"].count == 1
    assert route_legend["layout_verification_status"].meaning == (
        "A verification-status term attached to dataset, layout, storage, or partition path metadata."
    )

    resources = {resource.iri: resource for resource in context_slice.resources}
    assert messages in resources
    assert doc_id in resources
    assert RC + "CandidateLayout" in resources
    assert pattern_result.pattern_iri in resources
    assert claim_result.claim_iri in resources
    assert claim_result.evidence_iri in resources
    assert resources[messages].referenced_only is False
    assert resources[messages].surface_role == "current_map_context"
    assert resources[messages].primary_route == resources[messages].routes[0]
    assert resources[messages].primary_route.route == "seed"
    assert any(route.route == "seed" for route in resources[messages].routes)
    assert resources[doc_id].surface_role == "current_map_context"
    assert resources[RC + "CandidateLayout"].surface_role == "vocabulary_context"
    assert resources[pattern_result.pattern_iri].surface_role == "pattern_synthesis"
    assert resources[claim_result.claim_iri].surface_role == "observation_context"
    assert resources[claim_result.evidence_iri].surface_role == "evidence_support"
    assert any(route.route == "dataset_column" for route in resources[doc_id].routes)
    assert any(
        route.route == "layout_verification_status"
        for route in resources[RC + "CandidateLayout"].routes
    )
    assert any(
        route.route == "linked_pattern"
        for route in resources[pattern_result.pattern_iri].routes
    )

    assert context_slice.trig is not None
    dataset = Dataset()
    dataset.parse(data=context_slice.trig, format="trig")
    graph_iris = {str(graph.identifier) for graph in dataset.graphs() if len(graph)}
    assert "https://richcanopy.org/graph/map" in graph_iris
    assert "https://richcanopy.org/graph/patterns" in graph_iris


def test_resource_brief_context_slice_expands_shape_and_predicate_routes(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    shape = "https://example.test/project#SignalShape"
    score = "https://example.test/project#score"
    reading = "https://example.test/project#Reading"
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        ex:score a rdf:Property ;
            rdfs:label "score" ;
            rdfs:range xsd:decimal .
        """,
        graph="ontology",
    )
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:SignalShape a sh:NodeShape ;
            rdfs:label "Signal shape" ;
            sh:targetClass ex:Signal ;
            sh:property [
                sh:path ex:score ;
                sh:datatype xsd:decimal
            ] .
        """,
        graph="shapes",
    )
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        ex:Reading ex:score "0.91"^^xsd:decimal .
        """,
        graph="map",
    )

    shape_slice = db.get_context_graph(
        shape,
        profile="resource_brief",
        max_triples=50,
    )

    assert shape_slice.profile == "resource_brief"
    assert shape_slice.dataset_contexts == []
    assert shape_slice.pattern_contexts == []
    assert shape_slice.route_counts["seed"] == 1
    assert shape_slice.route_counts["resource_type"] == 1
    assert shape_slice.route_counts["blank_node_reference"] >= 2
    resources = {resource.iri: resource for resource in shape_slice.resources}
    assert resources[shape].surface_role == "validation_shape_context"
    assert score in resources
    assert any(
        triple.graph == "shapes"
        and triple.subject_kind == "bnode"
        and triple.predicate == "http://www.w3.org/ns/shacl#path"
        and triple.object == score
        for triple in shape_slice.triples
    )

    score_slice = db.get_context_graph(
        score,
        profile="resource_brief",
        max_triples=50,
    )

    score_routes = {
        route.route
        for resource in score_slice.resources
        if resource.iri == shape
        for route in resource.routes
    }
    assert "incoming_blank_node_owner" in score_routes
    reading_routes = {
        route.route
        for resource in score_slice.resources
        if resource.iri == reading
        for route in resource.routes
    }
    assert "predicate_usage_subject" in reading_routes


def test_resource_brief_context_slice_suggests_route_cap_recovery(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    outgoing_triples = "\n".join(
        f"ex:Hub ex:linksTo ex:Outgoing{index:02d} ."
        for index in range(30)
    )
    predicate_usage_triples = "\n".join(
        f"ex:Use{index:02d} ex:stressPredicate ex:Value{index:02d} ."
        for index in range(30)
    )
    db.import_turtle(
        f"""
        @prefix ex: <https://example.test/project#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

        ex:stressPredicate a rdf:Property .
        {outgoing_triples}
        {predicate_usage_triples}
        """,
        graph="map",
    )

    hub = "https://example.test/project#Hub"
    hub_slice = db.get_context_graph(
        hub,
        profile="resource_brief",
        max_triples=1000,
    )

    assert hub_slice.truncated is False
    assert any(
        "omitted 5 outgoing reference(s)" in warning
        and "Raising max_triples does not recover route-capped resources" in warning
        for warning in hub_slice.warnings
    )
    outgoing_action = next(
        action
        for action in hub_slice.suggested_next_actions
        if action.tool == "doxabase.describe_resource"
        and action.args.get("include_incoming") is False
    )
    assert outgoing_action.tool == "doxabase.describe_resource"
    assert outgoing_action.args == {
        "iri": hub,
        "include_incoming": False,
        "limit": 25,
        "outgoing_offset": 25,
    }

    predicate = "https://example.test/project#stressPredicate"
    predicate_slice = db.get_context_graph(
        predicate,
        profile="resource_brief",
        max_triples=1000,
    )

    assert predicate_slice.truncated is False
    assert any(
        "omitted 5 predicate usage subject(s)" in warning
        and "no paged predicate-usage browser" in warning
        for warning in predicate_slice.warnings
    )
    predicate_action = next(
        action
        for action in predicate_slice.suggested_next_actions
        if action.tool == "doxabase.export_graph"
    )
    assert predicate_action.tool == "doxabase.export_graph"
    assert predicate_action.args["graphs"] == "project"
    assert "predicate-usage" in predicate_action.args["path"]


def test_resource_brief_incoming_cap_prioritizes_lore_rich_references(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    value_type = "https://example.test/project#ConfidenceBand"
    useful_column = "https://example.test/project#zz_confidence_code"
    auxiliary_columns = "\n".join(
        (
            f"ex:aux_confidence_{index:02d} a rc:Column ; "
            f'rdfs:label "Aux confidence {index:02d}" ; '
            "rc:valueType ex:ConfidenceBand ."
        )
        for index in range(30)
    )
    db.import_turtle(
        f"""
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:ConfidenceBand a rdfs:Class ;
            rdfs:label "Confidence band" .

        {auxiliary_columns}

        ex:zz_confidence_code a rc:Column ;
            rdfs:label "ZZ confidence code" ;
            rc:valueType ex:ConfidenceBand .
        """,
        graph="map",
    )
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:confidence_code_claim a rc:InterpretationClaim ;
            rc:claimText "Confidence code controls calibration decisions." ;
            rc:claimTarget ex:zz_confidence_code .
        """,
        graph="observations",
    )

    context_slice = db.get_context_graph(
        value_type,
        profile="resource_brief",
        max_triples=1000,
    )

    resource_iris = {resource.iri for resource in context_slice.resources}
    assert useful_column in resource_iris
    assert "https://example.test/project#aux_confidence_29" not in resource_iris
    assert context_slice.route_counts["incoming_reference"] == 25
    assert any(
        "omitted 6 incoming reference(s)" in warning
        for warning in context_slice.warnings
    )


def test_resource_brief_context_slice_suggests_blank_node_closure_on_route_cap(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    property_blocks = "\n".join(
        (
            "            sh:property [ "
            f"sh:path ex:path{index:02d}; "
            "sh:datatype xsd:string "
            "] ;"
        )
        for index in range(30)
    )
    db.import_turtle(
        f"""
        @prefix ex: <https://example.test/project#> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        ex:WideShape a sh:NodeShape ;
{property_blocks}
            sh:targetClass ex:WideThing .
        """,
        graph="shapes",
    )

    shape = "https://example.test/project#WideShape"
    context_slice = db.get_context_graph(
        shape,
        profile="resource_brief",
        max_triples=1000,
    )

    assert context_slice.truncated is False
    assert any(
        "blank-node reference(s)" in warning
        and "inspect blank-node closure" in warning
        for warning in context_slice.warnings
    )
    closure_action = next(
        action
        for action in context_slice.suggested_next_actions
        if action.tool == "doxabase.describe_resource"
        and action.args.get("include_blank_node_closure") is True
    )
    assert closure_action.tool == "doxabase.describe_resource"
    assert closure_action.args == {
        "iri": shape,
        "include_blank_node_closure": True,
        "blank_node_depth": 4,
        "blank_node_limit": 100,
    }


def test_resource_brief_context_slice_warns_for_pattern_seed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    pattern = db.record_pattern(
        summary="Messages preserve document identity.",
        pattern_text="Message exports carry document identifiers through joins.",
        rationale="Exercise resource-brief guidance for pattern seeds.",
        pattern_targets=["https://example.test/project#Messages"],
        evidence_sources=["test://pattern"],
    )

    context_slice = db.get_context_graph(
        pattern.pattern_iri,
        profile="resource_brief",
        max_triples=100,
    )

    assert any(
        "Seed is an rc:Pattern; resource_brief gives a generic resource card."
        in warning
        for warning in context_slice.warnings
    )
    pattern_action = next(
        action
        for action in context_slice.suggested_next_actions
        if action.tool == "doxabase.get_context_graph"
        and action.args.get("profile") == "pattern_brief"
    )
    assert pattern_action.tool == "doxabase.get_context_graph"
    assert pattern_action.args == {
        "seed_iris": [pattern.pattern_iri],
        "profile": "pattern_brief",
        "max_triples": 100,
    }


def test_resource_brief_context_slice_finds_owner_for_blank_node_seed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    shape = "https://example.test/project#NestedShape"
    inner_path = "https://example.test/project#innerPath"
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:NestedShape a sh:NodeShape ;
            rdfs:label "Nested shape" ;
            sh:property [
                sh:path ex:outerPath ;
                sh:qualifiedValueShape [
                    sh:path ex:innerPath ;
                    sh:datatype xsd:string ;
                    sh:message "Inner path is text."
                ]
            ] .
        """,
        graph="shapes",
    )
    matches = db.search("Inner path", graph="shapes")
    blank_node_seed = next(
        match.iri
        for match in matches.matches
        if match.types == []
    )

    context_slice = db.get_context_graph(
        blank_node_seed,
        profile="resource_brief",
        max_triples=50,
    )

    shape_resource = next(
        resource for resource in context_slice.resources if resource.iri == shape
    )
    assert any(
        route.route == "blank_node_seed_owner"
        for route in shape_resource.routes
    )
    assert inner_path in {resource.iri for resource in context_slice.resources}
    assert "blank_node_seed_owner" in context_slice.route_counts
    assert not any("owner lookup" in warning for warning in context_slice.warnings)


def test_resource_brief_context_slice_routes_storage_seed_to_query_context(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WarehouseOrders"
    storage = db.record_map_storage_access(
        "https://example.test/project#warehouse_orders_storage",
        label="Warehouse orders database",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        path_templates=["public.orders"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Warehouse orders",
        is_table=True,
        storage_accesses=[storage.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context_slice = db.get_context_graph(
        storage.iri,
        profile="resource_brief",
    )

    dataset_resource = next(
        resource for resource in context_slice.resources if resource.iri == dataset
    )
    assert any(
        route.route == "incoming_reference"
        for route in dataset_resource.routes
    )
    query_actions = [
        action
        for action in context_slice.suggested_next_actions
        if action.tool == "doxabase.describe_query_context"
    ]
    assert len(query_actions) == 1
    assert query_actions[0].args == {"iri": dataset}
    assert "missing_physical_layout" in query_actions[0].reason
    query_context = db.describe_query_context(**query_actions[0].args)
    assert query_context.suggested_repair_action_groups[0].issue_code == (
        "missing_physical_layout"
    )


def test_resource_brief_storage_seed_suggests_clean_owner_query_context(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_storage",
        label="Orders object storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="object",
        storage_root=str(tmp_path / "orders.parquet"),
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#orders_layout",
        file_format="rc:Parquet",
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

    context_slice = db.get_context_graph(
        storage.iri,
        profile="resource_brief",
    )

    dataset_resource = next(
        resource for resource in context_slice.resources if resource.iri == dataset
    )
    assert any(
        route.route == "incoming_reference"
        for route in dataset_resource.routes
    )
    query_actions = [
        action
        for action in context_slice.suggested_next_actions
        if action.tool == "doxabase.describe_query_context"
    ]
    assert len(query_actions) == 1
    assert query_actions[0].args == {"iri": dataset}
    assert "single queryable owner table" in query_actions[0].reason
    query_context = db.describe_query_context(**query_actions[0].args)
    assert query_context.readiness == "ready_for_query_planning"
    assert query_context.suggested_repair_action_groups == []


def test_resource_brief_storage_seed_suggests_multiple_clean_owner_query_contexts(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    storage = db.record_map_storage_access(
        "https://example.test/project#shared_local_storage",
        label="Shared local object storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="prefix",
        storage_root=str(tmp_path / "warehouse"),
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#warehouse_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    owners = [
        ("https://example.test/project#Orders", "orders"),
        ("https://example.test/project#Refunds", "refunds"),
    ]
    for dataset, relation in owners:
        db.record_map_dataset(
            dataset,
            label=relation.title(),
            is_table=True,
            path_templates=[f"{relation}/part-*.parquet"],
            storage_accesses=[storage.iri],
            physical_layouts=[layout.iri],
            layout_verification_status="rc:VerifiedByQueryLayout",
        )

    context_slice = db.get_context_graph(
        storage.iri,
        profile="resource_brief",
    )

    assert {
        resource.iri
        for resource in context_slice.resources
        if any(route.route == "incoming_reference" for route in resource.routes)
    } >= {dataset for dataset, _ in owners}
    query_actions = [
        action
        for action in context_slice.suggested_next_actions
        if action.tool == "doxabase.describe_query_context"
    ]
    assert [action.args for action in query_actions] == [
        {"iri": dataset} for dataset, _ in owners
    ]
    assert all(
        "multiple queryable owner tables" in action.reason
        for action in query_actions
    )
    assert [
        db.describe_query_context(**action.args).readiness
        for action in query_actions
    ] == [
        "ready_for_query_planning",
        "ready_for_query_planning",
    ]


def test_resource_brief_query_context_action_separates_repairs_from_warnings(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    layout = db.record_map_physical_layout(
        "https://example.test/project#orders_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:CandidateLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        physical_layouts=[layout.iri],
        layout_verification_status="rc:CandidateLayout",
    )

    context_slice = db.get_context_graph(
        layout.iri,
        profile="resource_brief",
    )

    query_actions = [
        action
        for action in context_slice.suggested_next_actions
        if action.tool == "doxabase.describe_query_context"
    ]
    assert len(query_actions) == 1
    reason = query_actions[0].reason
    assert "query-planning repair group(s): missing_storage_access" in reason
    assert (
        "operational query-planning warning(s): "
        "layout_needs_verification, missing_path_template"
    ) in reason
    assert "repair group(s): layout_needs_verification" not in reason
    query_context = db.describe_query_context(**query_actions[0].args)
    assert [group.issue_code for group in query_context.suggested_repair_action_groups] == [
        "missing_storage_access"
    ]


def test_deep_lore_storage_seed_suggests_resource_brief_retry(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WarehouseOrders"
    storage = db.record_map_storage_access(
        "https://example.test/project#warehouse_orders_storage",
        label="Warehouse orders database",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        path_templates=["public.orders"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Warehouse orders",
        is_table=True,
        storage_accesses=[storage.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    deep_slice = db.get_context_graph(
        storage.iri,
        profile="deep_lore",
        max_triples=75,
    )

    assert any(
        "Seed is an rc:StorageAccess; rerun with profile='resource_brief'"
        in warning
        for warning in deep_slice.warnings
    )
    retry_action = next(
        action
        for action in deep_slice.suggested_next_actions
        if action.tool == "doxabase.get_context_graph"
        and action.args.get("profile") == "resource_brief"
    )
    assert retry_action.tool == "doxabase.get_context_graph"
    assert retry_action.args == {
        "seed_iris": [storage.iri],
        "profile": "resource_brief",
        "max_triples": 75,
    }

    resource_slice = db.get_context_graph(**retry_action.args)
    assert any(resource.iri == dataset for resource in resource_slice.resources)
    query_action = next(
        action
        for action in resource_slice.suggested_next_actions
        if action.tool == "doxabase.describe_query_context"
    )
    assert query_action.args == {"iri": dataset}
    assert "missing_physical_layout" in query_action.reason


def test_resource_brief_context_slice_finds_owner_for_nested_predicate_seed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    shape = "https://example.test/project#NestedShape"
    inner_path = "https://example.test/project#innerPath"
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:NestedShape a sh:NodeShape ;
            rdfs:label "Nested shape" ;
            sh:property [
                sh:path ex:outerPath ;
                sh:qualifiedValueShape [
                    sh:path ex:innerPath ;
                    sh:datatype xsd:string ;
                    sh:message "Inner path is text."
                ]
            ] .
        """,
        graph="shapes",
    )

    context_slice = db.get_context_graph(
        inner_path,
        profile="resource_brief",
        max_triples=50,
    )

    shape_resource = next(
        resource for resource in context_slice.resources if resource.iri == shape
    )
    assert any(
        route.route == "incoming_blank_node_owner"
        for route in shape_resource.routes
    )
    assert context_slice.route_counts["incoming_blank_node_owner"] == 1


def test_resource_brief_context_slice_expands_evidence_handoff(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Messages"
    claim_record = db.record_claim_observation(
        summary="Messages need source-backed review.",
        claim_text="The message export should be checked against its source notes.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=[dataset],
        evidence_summary="Synthetic source note.",
        source_path="/tmp/messages-source-note.md",
        source_kind="rc:DocumentationSource",
    )

    context_slice = db.get_context_graph(
        claim_record.evidence_iri,
        profile="resource_brief",
    )

    assert context_slice.route_counts["seed"] == 1
    assert context_slice.route_counts["outgoing_reference"] >= 1
    assert context_slice.route_counts["incoming_reference"] >= 1
    assert claim_record.source_span_iri in {
        resource.iri for resource in context_slice.resources
    }
    assert claim_record.observation_iri in {
        resource.iri for resource in context_slice.resources
    }
    route_legend = {row.route: row for row in context_slice.route_legend}
    assert route_legend["incoming_reference"].meaning == (
        "A URI subject that directly references a resource-brief seed."
    )


def test_resource_brief_evidence_seed_routes_observed_asset_to_query_context(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WarehouseOrders"
    storage = db.record_map_storage_access(
        "https://example.test/project#warehouse_orders_storage",
        label="Warehouse orders database",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        path_templates=["public.orders"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Warehouse orders",
        is_table=True,
        storage_accesses=[storage.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    observation = db.record_observation(
        summary="Warehouse orders were checked from source docs.",
        observed_asset=dataset,
        evidence_summary="Synthetic warehouse source note.",
        evidence_sources=["test://warehouse-orders-source"],
    )

    context_slice = db.get_context_graph(
        observation.evidence_iri,
        profile="resource_brief",
    )

    resources = {resource.iri: resource for resource in context_slice.resources}
    assert observation.observation_iri in resources
    assert dataset in resources
    assert any(
        route.route == "observed_asset"
        and route.source_iri == observation.observation_iri
        for route in resources[dataset].routes
    )
    query_actions = [
        action
        for action in context_slice.suggested_next_actions
        if action.tool == "doxabase.describe_query_context"
    ]
    assert len(query_actions) == 1
    assert query_actions[0].args == {"iri": dataset}
    assert "missing_physical_layout" in query_actions[0].reason


def test_resource_brief_profile_evidence_seed_suggests_profile_run(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WarehouseOrders"
    db.record_map_dataset(dataset, label="Warehouse orders", is_table=True)
    profile = db.record_dataset_profile(
        dataset,
        summary="Warehouse orders were profiled.",
        evidence_summary="Warehouse orders profiler output.",
        evidence_sources=["test://warehouse-orders-profile"],
        row_count=42,
        update_map_snapshot=False,
    )

    context_slice = db.get_context_graph(
        profile.observation.evidence_iri,
        profile="resource_brief",
    )

    resources = {resource.iri: resource for resource in context_slice.resources}
    assert profile.observation.observation_iri in resources
    assert dataset in resources
    profile_run_actions = [
        action
        for action in context_slice.suggested_next_actions
        if action.tool == "doxabase.describe_profile_run"
    ]
    assert len(profile_run_actions) == 1
    assert profile_run_actions[0].args == {
        "dataset_iri": dataset,
        "evidence_iri": profile.observation.evidence_iri,
    }


def test_evidence_seed_wrong_profile_suggests_resource_brief_before_export(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WarehouseOrders"
    db.record_map_dataset(dataset, label="Warehouse orders", is_table=True)
    profile = db.record_dataset_profile(
        dataset,
        summary="Warehouse orders were profiled.",
        evidence_summary="Warehouse orders profiler output.",
        evidence_sources=["test://warehouse-orders-profile"],
        row_count=42,
        update_map_snapshot=False,
    )

    context_slice = db.get_context_graph(
        profile.observation.evidence_iri,
        profile="dataset_brief",
    )

    assert context_slice.route_counts == {"seed": 1}
    assert any(
        "Seed is an rc:Evidence; rerun with profile='resource_brief'"
        in warning
        for warning in context_slice.warnings
    )
    assert context_slice.suggested_next_actions[0].tool == (
        "doxabase.get_context_graph"
    )
    assert context_slice.suggested_next_actions[0].args == {
        "seed_iris": [profile.observation.evidence_iri],
        "profile": "resource_brief",
        "max_triples": 500,
    }

    preflight = db.preflight_context_slice_export(
        profile.observation.evidence_iri,
        profile="dataset_brief",
    )

    assert preflight.suggested_next_actions[0].tool == (
        "doxabase.preflight_context_slice_export"
    )
    assert preflight.suggested_next_actions[0].args == {
        "seed_iris": [profile.observation.evidence_iri],
        "profile": "resource_brief",
        "max_triples": 500,
        "include_seed_graphs": False,
        "limit": 20,
    }
    assert any(
        action.tool == "doxabase.export_context_slice"
        for action in preflight.suggested_next_actions[1:]
    )


def test_project_brief_suppresses_defined_metric_context_only_profile_review(
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

    brief = db.project_brief(limit=5, profile_candidate_limit=1)
    profile_draft = brief.datasets[0].profile.drafts[0]

    assert profile_draft.metric_advisory_count == 1
    assert profile_draft.status == (
        "profile evidence captured; metric context only"
    )
    assert profile_draft.metric_advisory_status_counts == {
        "project_metric_defined": 1,
    }
    assert [action.tool.removeprefix("doxabase.") for action in profile_draft.suggested_next_actions] == [
        "get_context_graph",
        "describe_resource",
    ]
    assert brief.profile_queue_counts["profile_metric_advisories"] == 1
    assert "profile_review" not in brief.queue_counts
    assert all(
        task.task_type != "profile_review"
        for task in brief.recommended_next_tasks
    )

