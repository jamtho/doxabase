"""Split from test_mcp_tools.py (distillation Phase 2); tests verbatim."""

from tests.mcp.support_mcp import *  # noqa: F401,F403


def test_draft_query_evidence_storage_overlay_tool_returns_stage_payload(
    tmp_path: Path,
) -> None:
    warehouse = tmp_path / "warehouse"
    warehouse.mkdir()
    csv_path = warehouse / "orders.csv"
    csv_path.write_text(
        "order_id,status,amount\n1,paid,12.00\n2,pending,8.00\n",
        encoding="utf-8",
    )
    query_path = tmp_path / "orders_status.sql"
    query_path.write_text("select status, count(*) from orders;\n", encoding="utf-8")
    result_path = tmp_path / "orders_status.json"
    result_path.write_text('{"paid": 1, "pending": 1}\n', encoding="utf-8")

    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    result = record_query_result_tool(
        db,
        summary="Orders status aggregate scanned the reviewed local CSV.",
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path=str(query_path),
        query_hash="sha256:mcp-orders-status",
        result_sources=[str(result_path)],
        scanned_source_paths=[str(csv_path)],
        sample_size=2,
        sample_scope="All rows in the reviewed Orders CSV.",
        sample_method="External read-only aggregate query.",
        row_count=2,
    )

    before_context = describe_query_context_tool(db, iri=dataset)
    assert before_context["readiness"] == "insufficient_metadata"
    assert before_context.get("query_target_candidates", []) == []
    assert [
        action["tool"].removeprefix("doxabase.") for action in before_context["suggested_next_actions"]
    ] == [
        "describe_resource",
        "stage_revision",
    ]
    assert before_context["safe_inspection_action_indexes"] == [0]
    assert before_context["first_safe_inspection_action_index"] == 0
    overlay_action = before_context["suggested_next_actions"][1]
    assert overlay_action["args"]["spec"]["dataset_iri"] == dataset
    assert overlay_action["args"]["spec"]["evidence_iri"] == result["evidence_iri"]
    assert "reviewed values" in overlay_action["reason"]
    route_candidate = next(
        candidate
        for issue in before_context["issues"]
        if isinstance(issue.get("details"), dict)
        and isinstance(issue["details"].get("repair_hint"), dict)
        for candidate in (
            issue["details"]["repair_hint"].get(
                "evidence_storage_route_candidates"
            )
            or []
        )
    )
    assert route_candidate["candidate_kind"] == "local_path_from_query_evidence"
    assert route_candidate[
        "query_evidence_overlay_candidate_spec"
    ] == {
        "storage_protocol": "rc:LocalFilesystemStorage",
        "storage_root": str(warehouse),
        "location_kind": "directory",
        "path_templates": ["orders.csv"],
        "file_format": "rc:CSV",
    }

    draft = stage_revision_tool(
        db,
        kind="query_evidence_overlay",
        dry_run=True,
        spec={
            "dataset_iri": dataset,
            "evidence_iri": result["evidence_iri"],
            "storage_protocol": "rc:LocalFilesystemStorage",
            "storage_root": str(warehouse),
            "location_kind": "directory",
            "route_roles": ["rc:CurrentRoute"],
            "path_templates": ["orders.csv"],
            "file_format": "rc:CSV",
            "layout_verification_note": (
                "Reviewed query evidence scanned orders.csv."
            ),
        },
    )

    assert draft["result_kind"] == "query_evidence_storage_overlay_draft"
    assert draft["mode"] == "non_mutating_stage_arguments"
    assert draft["source_query_context_readiness"] == "insufficient_metadata"
    assert draft["source_profile_evidence"]["query_hash"] == (
        "sha256:mcp-orders-status"
    )
    assert draft["source_profile_evidence"]["query_source_paths"] == [
        str(query_path)
    ]
    assert draft["source_profile_evidence"]["scanned_source_paths"] == [
        str(csv_path)
    ]
    assert draft["source_profile_evidence"]["scanned_source_handles"] == [
        str(csv_path)
    ]
    assert draft["source_profile_evidence"]["result_sources"] == [str(result_path)]
    assert draft["source_query_evidence"] == draft["source_profile_evidence"]
    assert draft["reviewed_overlay"]["storage_root"] == str(warehouse)
    assert draft["reviewed_overlay"]["route_roles"] == [RC + "CurrentRoute"]
    assert draft["reviewed_overlay"]["path_templates"] == ["orders.csv"]
    assert draft["reviewed_overlay"]["file_format"] == RC + "CSV"
    assert draft["validation_conforms"] is True
    assert draft["changed_graphs"] == ["map"]
    assert draft["stage_arguments"]["supporting_observations"] == [
        result["observation_iri"]
    ]
    assert draft["suggested_next_actions"][0]["tool"] == (
        "doxabase.stage_revision"
    )
    assert draft["suggested_next_actions"][0]["args"]["kind"] == "graph"

    still_before_apply = describe_query_context_tool(db, iri=dataset)
    assert still_before_apply["readiness"] == "insufficient_metadata"
    assert still_before_apply.get("query_target_candidates", []) == []

    staged = stage_graph_revision_tool(db, **draft["stage_arguments"])
    assert staged["validation_conforms"] is True
    check = apply_staged_revision_tool(
        db, iri=staged["revision_iri"], dry_run=True
    )
    with pytest.raises(DoxaBaseError, match="read-only apply check"):
        apply_staged_revision_tool(
            db,
            iri=staged["revision_iri"],
            dry_run=True,
            created_by="agent",
        )
    assert check["status"] == "ready"
    applied = apply_staged_revision_tool(db, staged["revision_iri"])
    assert applied["patches_applied"] == 1

    repaired_context = describe_query_context_tool(db, iri=dataset)
    assert repaired_context["readiness"] == "ready_for_query_planning"
    plan = draft_query_plan_tool(db, iri=dataset)
    assert plan["handoff_kind"] == "execution_attempt_ready"
    assert plan["scan"]["uri_template"] == str(csv_path)


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

    result = stage_revision_tool(
        db,
        kind="graph",
        spec={
            "summary": "Try messages table framing",
            "rationale": (
                "Exploratory hunch: this map shape may generalise better once "
                "more message-like datasets arrive."
            ),
            "additions": [{"graph": "map", "content": content}],
            "stance": "rc:ExploratoryHunch",
            "validation_scope": "all",
        },
    )
    with pytest.raises(DoxaBaseError, match="kind must be one of"):
        stage_revision_tool(db, kind="bogus", spec={})
    with pytest.raises(DoxaBaseError, match="has no dry-run planner"):
        stage_revision_tool(db, kind="graph", spec={}, dry_run=True)
    with pytest.raises(DoxaBaseError, match="missing required spec field"):
        stage_revision_tool(db, kind="graph", spec={"summary": "x"})
    with pytest.raises(DoxaBaseError, match="dry_run-only"):
        stage_revision_tool(db, kind="query_evidence_overlay", spec={})

    assert result["revision_iri"].startswith(
        "https://richcanopy.org/doxabase/generated/staged-revision/"
    )
    assert result["revision_type"] == "https://richcanopy.org/ns/rc#StagedRevision"
    assert result["revision_stance"] == "https://richcanopy.org/ns/rc#ExploratoryHunch"
    assert result["summary"] == "Try messages table framing"
    assert result["rationale"].startswith("Exploratory hunch")
    assert result.get("review_note") is None
    assert result.get("review_recommendation") is None
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

    with pytest.raises(DoxaBaseError, match="current mutation-target row"):
        record_staged_revision_review_decision_tool(
            db,
            iri=result["revision_iri"],
            decision="discarded",
            rationale="Reviewer decided not to keep this ready proposal.",
        )

    resolution = stage_revision_tool(
        db,
        kind="review_decision",
        spec={
            "iri": result["revision_iri"],
            "decision": "discarded",
            "rationale": (
                "Reviewer explicitly decided not to keep this ready proposal."
            ),
            "allow_mutation_target": True,
        },
    )

    assert resolution["staged_revision_iri"] == result["revision_iri"]
    assert resolution["decision"] == "discarded"
    assert resolution["decision_iri"] == RC + "DiscardedDecision"
    assert resolution["current_application_status"] == "ready"
    assert resolution["current_next_action"]["queue"] == "apply_after_review"
    assert resolution["closes_current_staged_work"] is True
    assert [
        action["tool"].removeprefix("doxabase.") for action in resolution["suggested_next_actions"]
    ] == [
        "describe_revision",
        "describe_revision",
        "plan_staged_revision_recovery",
    ]

    resolved_description = describe_staged_revision_tool(db, result["revision_iri"])
    assert resolved_description["review_resolution"]["decision"] == "discarded"
    assert (
        resolved_description["review_resolution"]["resolution_revision_iri"]
        == resolution["resolution_revision_iri"]
    )

    decision_event = describe_graph_revision_tool(
        db,
        resolution["resolution_revision_iri"],
    )
    assert decision_event["record_kind"] == "staged_review_resolution"
    assert decision_event["resolves_staged_revision"] == result["revision_iri"]
    assert decision_event["staged_review_decision"] == RC + "DiscardedDecision"


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
    assert single["shareability_review_required"] is True
    assert single["shareability_review_status"] == "required_not_completed"
    assert grouped["shareability_review_required"] is True
    assert grouped["shareability_review_status"] == "required_not_completed"
    assert single["artifact_kind"] == "staged_revision_review_markdown"
    assert grouped["artifact_kind"] == "staged_revisions_review_markdown"
    assert single["importable"] is False
    assert grouped["importable"] is False
    assert single.get("recommended_import_tool") is None
    assert grouped.get("recommended_import_tool") is None
    assert single["recovery_complete"] is False
    assert grouped["recovery_complete"] is False
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


def test_export_staged_revisions_tool_resolves_relative_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
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
    assert export["bundle_summary"]["decision_headline"] == (
        "Review 1 staged revision row(s); queues: apply_after_review: 1; "
        "changed graphs: map: 1; snapshot evidence complete for 1 row(s)."
    )
    assert export["bundle_summary"]["changed_graph_counts"] == {"map": 1}
    assert export["bundle_summary"].get("choose_one_groups", []) == []
    assert export["bundle_summary"]["stale_resolution_state_counts"] == {"ready": 1}
    assert export["bundle_summary"].get("post_apply_recheck_revision_iris", []) == []
    snapshot_evidence = export["bundle_summary"]["snapshot_evidence"]
    assert snapshot_evidence["complete"] is True
    assert snapshot_evidence["total_revision_count"] == 1
    assert snapshot_evidence["status_counts"] == {"history_plus_snapshot_rows": 1}
    assert snapshot_evidence["rows"][0]["revision_iri"] == staged["revision_iri"]
    assert snapshot_evidence["rows"][0]["completeness"] == "complete"
    assert snapshot_evidence["rows"][0].get("suggested_next_actions", []) == []
    exported = expected_path.read_text(encoding="utf-8")
    assert "## At A Glance" in exported
    assert "- Rows: 1" in exported
    assert "- Changed graphs: map: 1" in exported
    assert "- Choose-one groups: none" in exported
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
    assert export["bundle_summary"].get("external_recommended_review_iris", []) == []
    assert export["bundle_summary"]["recommended_mutation_review_iris"] == [
        staged["revision_iri"]
    ]
    assert export["bundle_summary"]["recommended_apply_or_restage_review_iris"] == [
        staged["revision_iri"]
    ]
    assert export["bundle_summary"].get("recommended_repair_review_iris", []) == []
    assert export["bundle_summary"].get("warnings", []) == []
    assert export["bundle_summary"].get("validation_failed_revision_iris", []) == []
    assert export["bundle_summary"].get("recommended_applied_inspection_iris", []) == []
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
    assert export["bundle_summary"].get("semantic_review_required_queue_counts", {}) == {}
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
    assert export["revision_summaries"][0].get("alternative_to") is None
    assert export["revision_summaries"][0].get("current_alternative_to") is None
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
        "tool"
    ] == "doxabase.apply_staged_revision"
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


def test_list_graph_versions_tool_can_include_staged_apply_checks(
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
    record_map_dataset_tool(
        db,
        iri="https://example.test/project#UnrelatedDrift",
        label="Unrelated drift dataset",
        is_table=True,
    )

    result = list_graph_versions_tool(
        db,
        graph_role="map",
        exact_only=True,
        include_apply_checks=True,
        drift_detail="exact",
    )

    assert result["include_apply_checks"] is True
    assert result["drift_detail"] == "exact"
    assert [row["revision_iri"] for row in result["versions"]] == [
        staged["revision_iri"]
    ]
    row = result["versions"][0]
    assert row["application_status"] == "conflict"
    assert row["application_decision"] == "restage_against_current_graph"
    assert row["application_can_apply"] is False
    assert row["application_blocking_reasons"] == ["target_count_drift"]
    assert row["stale_resolution_state"] == "stale_unresolved"
    assert row["next_action"]["queue"] == "restage_after_review"
    assert row["next_action"]["arguments"] == {
        "revision_iris": staged["revision_iri"]
    }
    assert row["next_action_queue_item"]["queue"] == "restage_after_review"
    assert row["next_action_queue_item"]["resolved_target_iri"] == (
        staged["revision_iri"]
    )


def test_graph_version_tools_surface_review_resolved_staged_rows(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    messages = "https://example.test/project#Messages"
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
    db.record_map_dataset(messages)
    resolution = record_staged_revision_review_decision_tool(
        db,
        staged["revision_iri"],
        decision="no_effective_change",
        rationale=(
            "Reviewed the stale source and confirmed the same fact already "
            "exists in the current map."
        ),
        created_at="2026-06-01T10:01:00Z",
    )

    versions = list_graph_versions_tool(
        db,
        graph_role="map",
        record_kind="staged_patch",
        include_current=False,
    )

    assert [item["revision_iri"] for item in versions["versions"]] == [
        staged["revision_iri"]
    ]
    version = versions["versions"][0]
    assert version["is_current_staged_work"] is False
    assert version["not_current_staged_work_reason"] == "review_resolved"
    assert version["review_resolution"]["decision"] == "no_effective_change"
    assert (
        version["review_resolution"]["resolution_revision_iri"]
        == resolution["resolution_revision_iri"]
    )

    diff = describe_graph_version_diff_tool(
        db,
        graph_role="map",
        before_revision_iri=staged["revision_iri"],
    )

    context = diff["before_revision_context"]
    assert context["application_status"] == "conflict"
    assert context["application_decision"] == "restage_against_current_graph"
    assert context["is_current_staged_work"] is False
    assert context["not_current_staged_work_reason"] == "review_resolved"
    assert context["review_resolution"]["decision"] == "no_effective_change"
    assert (
        context["review_resolution"]["resolution_revision_iri"]
        == resolution["resolution_revision_iri"]
    )


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

    result = stage_revision_tool(
        db,
        kind="pattern_promotion",
        spec=dict(
        patterns=[pattern.pattern_iri],
        summary="Promote body_top caveat",
        profile_route_sources=[
            {
                "review_lane": "metric_vocabulary_review",
                "route_group_key": "metric_vocabulary_review:test",
                "route_step_key": "profile-route-step:test",
            }
        ],
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
        ),
    )

    assert result["result_kind"] == "systematisation_draft"
    assert result["summary"] == "Promote body_top caveat"
    assert result["intent"] == (
        "Stage one or more graph changes supported by selected patterns."
    )
    assert result["profile_route_source_count"] == 1
    assert result["anchors"] == [pattern.pattern_iri, target, implication]
    revision_iri = result["staged_revisions"][0]["revision_iri"]
    assert result["next_action_queue"] == {"apply_after_review": [revision_iri]}
    assert result["suggested_next_actions"][0]["tool"] == (
        "doxabase.export_bundle"
    )
    assert result["suggested_next_actions"][0]["args"]["spec"][
        "path"
    ].startswith("/tmp/systematisation-review-")
    assert [
        action["args"]
        for action in result["suggested_next_actions"]
        if (action["tool"], action["args"].get("dry_run")) == ("doxabase.apply_staged_revision", True)
    ] == [{"iri": revision_iri, "dry_run": True}]
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


def test_stage_query_storage_access_repair_tool_stages_new_storage_link(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Messages"
    storage_access = "https://example.test/project#messages_storage"
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Messages",
        is_table=True,
        path_templates=["messages/current/*.jsonl"],
    )

    staged = stage_revision_tool(
        db,
        kind="query_storage_access_repair",
        spec={
            "dataset_iri": dataset,
            "storage_access_iri": storage_access,
            "storage_protocol": "rc:LocalFilesystemStorage",
            "storage_root": str(tmp_path / "warehouse"),
            "rationale": "Reviewed the local warehouse route for Messages.",
            "route_roles": ["rc:CurrentRoute"],
            "location_kind": "directory",
            "path_templates": ["messages/current/*.jsonl"],
            "layout_verification_status": "rc:VerifiedByListingLayout",
            "layout_verification_note": (
                "Reviewed from local warehouse listing."
            ),
        },
    )

    assert staged["validation_conforms"] is True
    assert check_staged_revision_apply_tool(db, staged["revision_iri"])["status"] == (
        "ready"
    )
    apply_staged_revision_tool(db, staged["revision_iri"])
    repaired = describe_query_context_tool(db, iri=dataset)
    assert "missing_storage_access" not in {
        issue["code"] for issue in repaired["issues"]
    }
    assert repaired["storage_accesses"][0]["iri"] == storage_access
    assert [role["iri"] for role in repaired["storage_accesses"][0]["route_roles"]] == [
        RC + "CurrentRoute"
    ]
    assert repaired["storage_accesses"][0]["storage_root"] == str(
        tmp_path / "warehouse"
    )


def test_search_staged_patch_payloads_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    term = "https://example.test/project#CohortCompletenessLens"
    staged = stage_graph_revision_tool(
        db,
        summary="Define cohort completeness lens",
        rationale="The term should remain reviewable before it becomes ontology.",
        additions=[
            {
                "graph": "ontology",
                "content": f"""
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    <{term}> a rdfs:Class ;
                        rdfs:label "Cohort completeness lens" ;
                        rdfs:comment "A staged-only modelling lens." .
                """,
            }
        ],
        validation_scope="all",
    )

    result = search_tool(
        db,
        scope="staged_patches",
        query="cohort completeness",
    )

    assert result["query"] == "cohort completeness"
    assert result["current_staged_work_only"] is True
    assert result["count"] == 1
    match = result["matches"][0]
    assert match["revision_iri"] == staged["revision_iri"]
    assert match["revision_summary"] == "Define cohort completeness lens"
    assert match["target_graph"] == "ontology"
    assert match["patch_subject_iris"] == [term]
    assert "literal" in match["matched_term_roles"]
    assert match["suggested_next_actions"][0]["tool"] == (
        "doxabase.describe_revision"
    )
    assert match["suggested_next_actions"][1]["tool"] == (
        "doxabase.export_bundle"
    )
    assert (
        match["suggested_next_actions"][1]["args"]["spec"]["fail_on_sensitive"]
        is True
    )
    assert result["suggested_next_actions"][0] == match["suggested_next_actions"][0]

