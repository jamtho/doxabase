"""Split from test_mcp_tools.py (distillation Phase 2); tests verbatim."""

from tests.mcp.support_mcp import *  # noqa: F401,F403


def test_check_staged_revision_apply_tool_surfaces_snapshot_preflight(
    tmp_path: Path,
) -> None:
    source = DoxaBase.create(tmp_path / "source.sqlite")
    staged = stage_graph_revision_tool(
        source,
        summary="Stage live messages table",
        rationale="Exercise direct apply-check routing after RDF-only handoff.",
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
    source.export_trig(project_path, graphs="project")
    receiver = DoxaBase.create(tmp_path / "receiver.sqlite")
    receiver.import_trig(project_path)

    check = check_staged_revision_apply_tool(receiver, staged["revision_iri"])

    assert check["status"] == "ready"
    assert check["can_apply"] is True
    assert check["next_action"]["tool_name"] == "apply_staged_revision"
    assert check["next_action"]["mutation_scope"] == "project_graph_and_history"
    assert check["next_action"]["mutates_project_graph"] is True
    assert check["next_action"]["writes_history"] is True
    assert check["next_action"]["writes_files"] is False
    assert check["next_action"]["writes_storage"] is False
    assert check["snapshot_evidence"]["status"] == "history_only_count_digest"
    assert check["snapshot_evidence_completeness"] == "history-only"
    assert check["mutation_allowed_after"] == (
        "handoff_preflight_required_before_mutation"
    )
    assert [action["tool"].removeprefix("doxabase.") for action in check["blocking_preflight_actions"]] == [
        "import_revision_snapshots"
    ]
    assert check["suggested_next_actions"][0]["tool"] == (
        "doxabase.import_revision_snapshots"
    )
    assert any(
        action["tool"] == "doxabase.apply_staged_revision"
        for action in check["suggested_next_actions"][1:]
    )
    assert check["first_safe_next_action"]["tool_name"] == (
        "import_revision_snapshots"
    )
    assert check["first_safe_next_action"]["queue"] == "complete_handoff_import"
    assert check["first_safe_next_action"]["mutation_scope"] == "snapshot_storage"
    assert check["first_safe_next_action"]["writes_storage"] is True


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
    assert check.get("blocking_reasons", []) == []
    assert check.get("validation_skipped_reason") is None
    assert "proposal is still desired" in check["recommended_resolution"]
    assert check["summary"] == (
        "Ready to apply 1 patch(es) across map: +3 triple(s), -0 triple(s)."
    )
    assert check.get("conflicts", []) == []
    assert check["patch_checks"][0]["count_basis"] == "target_graph_only"
    assert check["patch_checks"][0]["preview_triple_count"] == 3
    assert check["patch_checks"][0]["effective_triples_to_add"] == 3
    assert check["patch_checks"][0]["effective_triples_to_remove"] == 0
    assert check["patch_checks"][0]["already_present_triples"] == 0
    assert check["patch_checks"][0]["already_absent_triples"] == 3
    assert check["suggested_next_actions"][0]["tool"] == (
        "doxabase.describe_staged_revision"
    )
    assert check["suggested_next_actions"][-1]["tool"] == (
        "doxabase.apply_staged_revision"
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
    assert result["warnings"] == [
        (
            "Applying this staged revision may have made sibling staged readiness "
            "stale. Recheck affected staged revisions before the next mutation: "
            f"{sibling['revision_iri']}. post_apply_recheck_revision_iris is the "
            "affected-sibling subset, not the full remaining staged queue; rerun "
            "plan_staged_revision_recovery(current_staged_work_only=True) before "
            "applying another row."
        )
    ]
    assert result["suggested_next_actions"][0]["tool"] == (
        "doxabase.plan_staged_revision_recovery"
    )
    assert result["suggested_next_actions"][0]["args"] == {
        "current_staged_work_only": True
    }
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
    assert recheck["suggested_next_actions"][-1]["tool"] == (
        "doxabase.restage_staged_revision"
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
    assert diff["graph_diffs"][0].get("triples_added", []) == []
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
    trig_import = import_trig_tool(round_trip, path=str(project_path))
    assert trig_import["imported_history_revision_count"] == 3
    assert trig_import["post_import_snapshot_evidence_complete"] is False
    assert trig_import["post_import_snapshot_evidence_truncated"] is False
    assert trig_import["post_import_snapshot_evidence_status_counts"] == {
        "history_only_count_digest": 3
    }
    assert set(trig_import["incomplete_snapshot_revision_iris"]) == {
        result["applied_revision_iri"],
        sibling["revision_iri"],
        staged["revision_iri"],
    }
    assert {
        item["revision_iri"]: item["status"]
        for item in trig_import["post_import_snapshot_evidence"]
    } == {
        result["applied_revision_iri"]: "history_only_count_digest",
        sibling["revision_iri"]: "history_only_count_digest",
        staged["revision_iri"]: "history_only_count_digest",
    }
    assert trig_import["suggested_next_actions"][0]["tool"] == (
        "doxabase.import_revision_snapshots"
    )
    snapshot_status_before_import = describe_revision_snapshot_evidence_tool(
        round_trip,
        result["applied_revision_iri"],
    )
    assert snapshot_status_before_import["status"] == "history_only_count_digest"
    assert snapshot_status_before_import["suggested_next_actions"][0][
        "tool"
    ] == "doxabase.import_revision_snapshots"
    assert snapshot_status_before_import["suggested_next_actions"][0][
        "args"
    ] == {
        "path": "/tmp/revision-snapshots.json",
        "path_is_placeholder": True,
    }
    assert "real handoff path" in snapshot_status_before_import[
        "suggested_next_actions"
    ][0]["reason"]
    assert "export_handoff_bundle" in snapshot_status_before_import[
        "suggested_next_actions"
    ][0]["reason"]
    imported_detail_before_snapshots = describe_graph_revision_tool(
        round_trip,
        result["applied_revision_iri"],
    )
    assert [
        action["tool"].removeprefix("doxabase.")
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
    ][0]["tool"] == "doxabase.import_revision_snapshots"
    assert imported_diff_before_snapshots["suggested_next_actions"][0][
        "tool"
    ] == "doxabase.import_revision_snapshots"
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
    assert rdf_only_snapshot.get("triples", []) == []
    assert rdf_only_snapshot["suggested_next_actions"][0]["tool"] == (
        "doxabase.import_revision_snapshots"
    )
    rdf_only_version_diff = describe_graph_version_diff_tool(
        round_trip,
        graph_role="map",
        before_revision_iri=staged["revision_iri"],
        after_revision_iri=result["applied_revision_iri"],
    )
    assert rdf_only_version_diff["exact_changed_triples_available"] is False
    assert rdf_only_version_diff["suggested_next_actions"][0]["tool"] == (
        "doxabase.import_revision_snapshots"
    )
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
    ][0]["tool"] == "doxabase.import_trig"
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
    assert staged_description.get("current_apply_check") is None
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
    direct_route_step_keys = result["candidates"][0]["profile_route_groups"][0][
        "direct_route_step_keys"
    ]
    assert result["closed_route_step_keys"] == direct_route_step_keys
    assert result.get("remaining_route_step_keys", []) == []
    assert result.get("open_profile_review_lanes", []) == []
    assert result["open_profile_review_lane_count"] == 0
    assert result["executor_decision_summary"]["decision"] == (
        "bulk_apply_after_review"
    )
    assert result["executor_decision_summary"][
        "safe_single_apply_candidate_revision_iris"
    ] == result["candidate_revision_iris"]
    assert result["executor_decision_summary"].get("open_review_lanes", []) == []
    assert result["executor_decision_summary"]["candidate_apply_guidance"][0][
        "revision_iri"
    ] == staged["staged_revision"]["revision_iri"]
    assert result["executor_decision_summary"]["candidate_apply_guidance"][0][
        "apply_guidance"
    ] == "safe_single_after_review"
    assert result["executor_decision_summary"]["candidate_apply_guidance"][0].get(
        "blocking_open_review_lanes", []
    ) == []
    assert result["export"]["path"] == str(export_path)
    assert result["export"]["revision_iris"] == result["candidate_revision_iris"]
    assert result["export"]["sensitive_literal_count"] == 0
    assert result["export"].get("privacy_warnings", []) == []
    assert result["export"]["shareability_review_required"] is True
    assert result["export"]["shareability_review_status"] == (
        "required_not_completed"
    )
    assert result["export"]["artifact_disposition"] == (
        "local_only_pending_shareability_review"
    )
    assert result["export"]["git_safe"] is False
    assert result["decision"] == result["export"]["decision"]
    assert result["scanner_clean"] == result["export"]["scanner_clean"]
    assert result["would_block_sensitive_export"] == (
        result["export"]["would_block_sensitive_export"]
    )
    assert result["sensitive_literal_count"] == (
        result["export"]["sensitive_literal_count"]
    )
    assert result.get("privacy_warnings", []) == result["export"].get(
        "privacy_warnings", []
    )
    assert result.get("shareability_hints", []) == result["export"].get(
        "shareability_hints", []
    )
    assert result["shareability_hint_count"] == (
        result["export"]["shareability_hint_count"]
    )
    assert result.get("shareability_hint_matches", []) == (
        result["export"].get("shareability_hint_matches", [])
    )
    assert result["artifact_disposition"] == result["export"]["artifact_disposition"]
    assert result["git_safe"] is False
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
    assert current_only.get("candidate_revision_iris", []) == []
    assert current_only.get("export") is None


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
    assert open_lanes["profile_scalar_conflict_review"].get(
        "matched_candidate_revision_iris", []
    ) == []
    assert open_lanes["metric_vocabulary_review"][
        "matched_candidate_revision_iris"
    ] == [staged_iri]
    assert open_lanes["profile_type_review"][
        "matched_candidate_revision_iris"
    ] == [staged_iri]
    assert all(lane["route_step_keys"] for lane in open_lanes.values())
    assert all(lane["remaining_actions"] for lane in open_lanes.values())
    assert {
        action["route_step_key"]
        for action in open_lanes["profile_type_review"]["remaining_actions"]
    } == set(open_lanes["profile_type_review"]["route_step_keys"])
    assert {
        action["args"]["predicate"]
        for action in open_lanes["profile_type_review"]["remaining_actions"]
        if action["tool"] == "doxabase.stage_map_assertion_change"
    } == {"rc:valueType"}
    type_action_details = [
        action["target_detail"]
        for action in open_lanes["profile_type_review"]["remaining_actions"]
        if action["target_detail"]
    ]
    assert any(
        "column status" in detail
        and "value type StatusCodeValue" in detail
        and "status type_finding_missing_map_type" in detail
        for detail in type_action_details
    )
    assert result["executor_decision_summary"]["decision"] == (
        "review_or_stage_open_lanes"
    )
    assert result["executor_decision_summary"]["open_review_lane_count"] == 3
    assert {
        lane["review_lane"]
        for lane in result["executor_decision_summary"]["open_review_lanes"]
    } == {
        "profile_scalar_conflict_review",
        "metric_vocabulary_review",
        "profile_type_review",
    }
    assert result["executor_decision_summary"]["mutation_policy"] == (
        "do_not_bulk_apply"
    )
    executor_lanes = {
        lane["review_lane"]: lane
        for lane in result["executor_decision_summary"]["open_review_lanes"]
    }
    assert {
        action["args"]["predicate"]
        for action in executor_lanes["profile_type_review"]["remaining_actions"]
        if action["tool"] == "doxabase.stage_map_assertion_change"
    } == {"rc:valueType"}

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
    assert "Generic staged review queues below are mechanical" in exported
    assert "blocked_by_profile_gate" in exported
    assert "do not follow generic apply_after_review" in exported
    assert "### Open Profile Review Lanes" in exported
    assert "### Profile Route Bridge" in exported
    open_section = exported.split("### Open Profile Review Lanes", 1)[1].split(
        "### Profile Route Bridge",
        1,
    )[0]
    assert "Target / detail" in open_section
    assert "| profile_scalar_conflict_review | 1 | 2 | none |" in open_section
    assert "metric_vocabulary_review" in open_section
    assert "profile_type_review" in open_section
    assert "column status" in open_section
    assert "value type StatusCodeValue" in open_section
    assert "status type_finding_missing_map_type" in open_section
    assert "\n| profile_map_updates |" not in open_section

