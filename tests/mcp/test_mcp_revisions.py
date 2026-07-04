"""Split from test_mcp_tools.py (distillation Phase 2); tests verbatim."""

from tests.mcp.support_mcp import *  # noqa: F401,F403


def test_record_graph_revision_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)
    validation = validate_graph_tool(db, scope="all")
    export_path = tmp_path / "review.trig"
    export_result = export_trig_tool(db, path=str(export_path), graphs=["workflow"])

    result = record_graph_revision_tool(
        db,
        summary="Fixture review bundle exported",
        rationale="The MCP wrapper test records why this review bundle exists.",
        changed_graphs=["observations", "patterns", "evidence"],
        included_graphs=export_result["graphs"],
        revision_type="rc:ExportRevision",
        revision_anchors=[
            "https://richcanopy.org/example/manifest/ais#DailyIndex",
        ],
        export_path=export_result["path"],
        graph_counts=export_result["graph_counts"],
        validation_scope=validation["scope"],
        validation_conforms=validation["conforms"],
        validation_result_count=validation["result_count"],
    )

    assert result["revision_iri"].startswith(
        "https://richcanopy.org/doxabase/generated/graph-revision/"
    )
    assert result["revision_type"] == "https://richcanopy.org/ns/rc#ExportRevision"
    assert result["graph"] == "history"
    assert result["triples"] > 0
    context = db.describe_resource(result["revision_iri"], graph="history")
    outgoing = {(triple.predicate, triple.object) for triple in context.outgoing}
    assert ("https://richcanopy.org/ns/rc#changedGraph", "map") not in outgoing
    assert ("https://richcanopy.org/ns/rc#includedGraph", "map") in outgoing
    description = describe_graph_revision_tool(db, result["revision_iri"])
    assert description["summary"] == "Fixture review bundle exported"
    assert description["changed_graphs"] == ["evidence", "observations", "patterns"]
    assert description["included_graphs"] == [
        "evidence",
        "map",
        "observations",
        "patterns",
    ]
    assert description["revision_anchors"][0]["iri"] == (
        "https://richcanopy.org/example/manifest/ais#DailyIndex"
    )
    assert description["validation_conforms"] is True
    assert description["graph_snapshots"]
    assert description["graph_snapshots"][0]["content_digest"].startswith("sha256:")
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_list_graph_revisions_tool_returns_json_like_payload(
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
    result = list_graph_revisions_tool(
        db,
        revision_type="rc:StagedRevision",
        include_apply_checks=True,
    )

    assert result["count"] == 1
    assert result["returned_count"] == 1
    assert result["total_count"] == 1
    assert result["include_apply_checks"] is True
    assert result["drift_detail"] == "summary"
    assert result["revision_type"] == "https://richcanopy.org/ns/rc#StagedRevision"
    assert result.get("record_kind") is None
    assert result.get("application_status") is None
    assert result.get("staged_validation_status") is None
    assert result.get("stale_resolution_state") is None
    assert result["current_staged_work_only"] is False
    assert result["returned_application_status_counts"] == {"ready": 1}
    assert result["returned_current_staged_work_application_status_counts"] == {
        "ready": 1
    }
    assert result["returned_stale_resolution_state_counts"] == {"ready": 1}
    assert result["returned_staged_validation_status_counts"] == {"conforms": 1}
    assert result["next_action_queue"] == {
        "apply_after_review": [staged["revision_iri"]]
    }
    assert result["next_action_queue_item_counts"] == {"apply_after_review": 1}
    assert result.get("semantic_review_required_queue_counts", {}) == {}
    queue_item = result["next_action_queue_items"][0]
    assert queue_item["row_iri"] == staged["revision_iri"]
    assert queue_item["queue"] == "apply_after_review"
    assert queue_item["action_type"] == "apply_after_review"
    assert queue_item["resolved_target_iri"] == staged["revision_iri"]
    assert queue_item["resolved_target_iri_source"] == "next_action.arguments.iri"
    assert queue_item["resolved_target_record_kind"] == "staged_patch"
    assert queue_item["row_is_target"] is True
    assert queue_item["record_kind"] == "staged_patch"
    assert queue_item["application_status"] == "ready"
    assert queue_item["staged_validation_status"] == "conforms"
    assert queue_item["alternative_semantic_review_required"] is False
    assert result["revisions"][0]["iri"] == staged["revision_iri"]
    assert result["revisions"][0]["record_kind"] == "staged_patch"
    assert result["revisions"][0]["is_current_staged_work"] is True
    assert result["revisions"][0].get("not_current_staged_work_reason") is None
    assert result["revisions"][0]["has_patch_payload"] is True
    assert result["revisions"][0]["patch_count"] == 1
    assert result["revisions"][0]["snapshot_evidence"]["status"] == (
        "history_plus_snapshot_rows"
    )
    assert result["revisions"][0]["snapshot_evidence"]["exact_snapshot_graph_roles"] == [
        "map"
    ]
    assert result["revisions"][0]["application_status"] == "ready"
    assert result["revisions"][0]["staged_validation_status"] == "conforms"
    assert result["revisions"][0]["application_decision"] == "review_then_apply"
    assert result["revisions"][0]["application_can_apply"] is True
    assert result["revisions"][0]["next_action"]["action_type"] == (
        "apply_after_review"
    )
    assert result["revisions"][0]["next_action"]["tool_name"] == (
        "apply_staged_revision"
    )
    assert result["revisions"][0]["suggested_next_actions"]

    ready_result = list_graph_revisions_tool(
        db,
        revision_type="rc:StagedRevision",
        application_status="ready",
    )

    assert ready_result["include_apply_checks"] is True
    assert ready_result["application_status"] == "ready"
    assert ready_result["returned_application_status_counts"] == {"ready": 1}
    assert ready_result["count"] == 1
    assert ready_result["returned_count"] == 1
    assert ready_result["total_count"] == 1
    assert ready_result["revisions"][0]["iri"] == staged["revision_iri"]

    staged_patch_result = list_graph_revisions_tool(
        db,
        record_kind="staged_patch",
        current_staged_work_only=True,
    )

    assert staged_patch_result["record_kind"] == "staged_patch"
    assert staged_patch_result["current_staged_work_only"] is True
    assert staged_patch_result["include_apply_checks"] is True
    assert staged_patch_result["count"] == 1
    assert staged_patch_result["returned_count"] == 1
    assert staged_patch_result["total_count"] == 1
    assert staged_patch_result["revisions"][0]["iri"] == staged["revision_iri"]

    stored_conforms_result = list_graph_revisions_tool(
        db,
        revision_type="rc:StagedRevision",
        staged_validation_status="conforms",
    )

    assert stored_conforms_result["include_apply_checks"] is False
    assert stored_conforms_result["staged_validation_status"] == "conforms"
    assert stored_conforms_result["count"] == 1
    assert stored_conforms_result["returned_count"] == 1
    assert stored_conforms_result["total_count"] == 1
    assert stored_conforms_result["revisions"][0]["iri"] == staged["revision_iri"]
    assert (
        staged_patch_result["revisions"][0].get("not_current_staged_work_reason")
        is None
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
        created_at="2026-06-01T10:02:00Z",
    )
    applied = apply_staged_revision_tool(
        db,
        iri=staged["revision_iri"],
        created_at="2026-06-01T10:01:00Z",
    )
    mixed_page = list_graph_revisions_tool(
        db,
        include_apply_checks=True,
        limit=1,
        offset=0,
    )

    assert mixed_page["count"] == 3
    assert mixed_page["returned_count"] == 1
    assert mixed_page["total_count"] == 3
    assert len(mixed_page["revisions"]) == 1
    assert mixed_page["revisions"][0]["iri"] == sibling["revision_iri"]
    assert mixed_page["returned_application_status_counts"] == {"conflict": 1}
    assert mixed_page["returned_current_staged_work_application_status_counts"] == {
        "conflict": 1
    }
    assert mixed_page["returned_stale_resolution_state_counts"] == {
        "stale_unresolved": 1
    }
    assert mixed_page["returned_staged_validation_status_counts"] == {"conforms": 1}
    assert mixed_page["next_action_queue"] == {
        "restage_after_review": [sibling["revision_iri"]]
    }
    second_page = list_graph_revisions_tool(
        db,
        include_apply_checks=True,
        limit=1,
        offset=1,
    )
    assert second_page["count"] == 3
    assert second_page["returned_count"] == 1
    assert second_page["total_count"] == 3
    assert second_page["revisions"][0]["iri"] == applied["applied_revision_iri"]
    assert second_page["returned_application_status_counts"] == {
        "applied_event": 1
    }
    assert second_page.get("returned_current_staged_work_application_status_counts", {}) == {}
    assert second_page["next_action_queue"] == {
        "inspect_already_applied": [applied["applied_revision_iri"]]
    }
    assert second_page["next_action_queue_item_counts"] == {
        "inspect_already_applied": 1
    }
    second_queue_item = second_page["next_action_queue_items"][0]
    assert second_queue_item["row_iri"] == applied["applied_revision_iri"]
    assert second_queue_item["resolved_target_iri"] == applied["applied_revision_iri"]
    assert second_queue_item["resolved_target_record_kind"] == "applied_event"
    assert second_queue_item["row_is_target"] is True
    assert second_queue_item["record_kind"] == "applied_event"
    applied_row = second_page["revisions"][0]
    assert applied_row["next_action"]["tool_name"] == "describe_graph_revision"
    assert [
        action["tool"].removeprefix("doxabase.") for action in applied_row["suggested_next_actions"]
    ] == [
        "describe_graph_revision",
        "describe_applied_revision_diff",
    ]
    assert applied_row["suggested_next_actions"][1]["args"] == {
        "iri": applied["applied_revision_iri"]
    }


def test_list_graph_versions_tool_returns_timeline_payload(
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
    applied = apply_staged_revision_tool(
        db,
        staged["revision_iri"],
        created_at="2026-06-01T10:01:00Z",
    )

    result = list_graph_versions_tool(db, graph_role="map")

    assert result["graph_role"] == "map"
    assert result["graph"] == "history"
    assert result["exact_only"] is False
    assert result["include_current"] is True
    assert result["count"] == 2
    assert result["total_count"] == 2
    assert result["returned_count"] == 2
    assert result["current_graph"] == {
        "graph_role": "map",
        "triple_count": db.triple_count("map"),
        "content_digest": db._graph_content_digest("map"),
    }
    assert result["snapshot_evidence_status_counts"] == {
        "history_plus_snapshot_rows": 2
    }
    assert result["exact_snapshot_available_count"] == 2
    assert "not a temporal checkout engine" in result["note"]

    rows_by_iri = {row["revision_iri"]: row for row in result["versions"]}
    staged_row = rows_by_iri[staged["revision_iri"]]
    applied_row = rows_by_iri[applied["applied_revision_iri"]]

    assert staged_row["record_kind"] == "staged_patch"
    assert staged_row["snapshot_semantics"] == "staged_before_graph"
    assert staged_row["summary"] == "Stage messages table"
    assert staged_row["created_at"] == "2026-06-01T10:00:00+00:00"
    assert staged_row["changed_graphs"] == ["map"]
    assert staged_row["included_graphs"] == ["map"]
    assert staged_row["is_current_staged_work"] is False
    assert staged_row["not_current_staged_work_reason"] == "already_applied_source"
    assert staged_row.get("review_resolution") is None
    assert staged_row["triple_count"] == 0
    assert staged_row["count_basis"] == "stored_snapshot_rows"
    assert staged_row["exact_snapshot_available"] is True
    assert staged_row["snapshot_evidence_status"] == "history_plus_snapshot_rows"
    assert staged_row["suggested_next_actions"][0]["tool"] == (
        "doxabase.describe_revision_graph_snapshot"
    )
    assert staged_row["suggested_next_actions"][1]["tool"] == (
        "doxabase.describe_revision_lineage"
    )
    assert staged_row["suggested_next_actions"][1]["args"] == {
        "iri": staged["revision_iri"]
    }
    assert staged_row["suggested_next_actions"][2]["tool"] == (
        "doxabase.describe_graph_version_diff"
    )

    assert applied_row["record_kind"] == "applied_event"
    assert applied_row["snapshot_semantics"] == "applied_after_graph"
    assert applied_row["applies_staged_revision"] == staged["revision_iri"]
    assert applied_row["is_current_staged_work"] is False
    assert applied_row["not_current_staged_work_reason"] == "applied_event_record"
    assert applied_row.get("review_resolution") is None
    assert applied_row["triple_count"] == db.triple_count("map")
    assert applied_row["exact_snapshot_available"] is True
    assert [
        action["tool"].removeprefix("doxabase.") for action in applied_row["suggested_next_actions"]
    ] == [
        "describe_revision_graph_snapshot",
        "describe_revision_lineage",
        "describe_graph_version_diff",
    ]
    assert applied_row["suggested_next_actions"][1]["args"] == {
        "iri": applied["applied_revision_iri"]
    }

    exact_staged = list_graph_versions_tool(
        db,
        graph_role="map",
        exact_only=True,
        include_current=False,
        record_kind="staged_patch",
    )
    assert exact_staged["exact_only"] is True
    assert exact_staged["include_current"] is False
    assert exact_staged["record_kind"] == "staged_patch"
    assert exact_staged.get("current_graph") is None
    assert [row["revision_iri"] for row in exact_staged["versions"]] == [
        staged["revision_iri"]
    ]


def test_describe_graph_version_diff_tool_returns_json_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    first_staged = stage_graph_revision_tool(
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
    first_applied = apply_staged_revision_tool(
        db,
        first_staged["revision_iri"],
        created_at="2026-06-01T10:01:00Z",
    )
    second_staged = stage_graph_revision_tool(
        db,
        summary="Stage message label",
        rationale="A later revision extends the map after the first snapshot.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Messages rdfs:label "Messages" .
                """,
            }
        ],
        created_at="2026-06-01T10:02:00Z",
    )
    apply_staged_revision_tool(
        db,
        second_staged["revision_iri"],
        created_at="2026-06-01T10:03:00Z",
    )

    stored_diff = describe_graph_version_diff_tool(
        db,
        graph_role="map",
        before_revision_iri=first_staged["revision_iri"],
        after_revision_iri=first_applied["applied_revision_iri"],
    )

    assert stored_diff["after_target_kind"] == "stored_revision_snapshot"
    assert stored_diff["compare_to_current"] is False
    assert stored_diff["before_triple_count"] == 0
    assert stored_diff["after_triple_count"] == 1
    assert stored_diff["count_delta"] == 1
    assert stored_diff["exact_changed_triples_available"] is True
    assert stored_diff["exact_changed_triples_included"] is False
    assert stored_diff["triples_added_count"] == 1
    assert stored_diff.get("triples_added", []) == []
    assert stored_diff["after_snapshot"]["revision_iri"] == (
        first_applied["applied_revision_iri"]
    )
    assert [
        action["tool"].removeprefix("doxabase.")
        for action in stored_diff["changed_resource_suggested_next_actions"]
    ] == [
        "describe_resource_revision_lineage",
        "describe_resource_revision_lineage",
    ]
    assert stored_diff["changed_resource_suggested_next_actions"][0][
        "args"
    ] == {
        "resource_iri": "https://example.test/project#Messages",
        "revision_iri": first_staged["revision_iri"],
    }

    current_diff = describe_graph_version_diff_tool(
        db,
        graph_role="map",
        before_revision_iri=first_applied["applied_revision_iri"],
        include_triples=True,
    )

    assert current_diff.get("after_revision_iri") is None
    assert current_diff["compare_to_current"] is True
    assert current_diff["after_target_kind"] == "current_graph"
    assert current_diff["current_graph"]["triple_count"] == db.triple_count("map")
    assert current_diff.get("after_snapshot") is None
    assert current_diff["count_delta"] == 1
    assert current_diff["exact_changed_triples_included"] is True
    assert current_diff["triples_added_count"] == 1
    assert len(current_diff["triples_added"]) == 1
    assert current_diff["suggested_next_actions"][0]["tool"] == (
        "doxabase.describe_revision_graph_snapshot"
    )


def test_list_resource_revisions_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    staged = stage_graph_revision_tool(
        db,
        summary="Add Orders stewardship note",
        rationale="Patch touches Orders without an explicit revision anchor.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Orders rdfs:comment "Owned by the operations team." .
                """,
            }
        ],
        created_at="2026-06-01T10:00:00Z",
    )
    applied = apply_staged_revision_tool(
        db,
        staged["revision_iri"],
        created_at="2026-06-01T10:01:00Z",
    )

    result = list_resource_revisions_tool(db, resource_iri=orders)

    assert result["resource"]["iri"] == orders
    assert "items" not in result
    assert result["current_staged_work_only"] is False
    assert result["patch_mention_scan"] == {
        "status": "complete",
        "unreadable_patch_count": 0,
        "unreadable_revision_count": 0,
        "omitted_match_risk": False,
    }
    assert result["count"] == 2
    assert result["returned_count"] == 2
    assert result["total_count"] == 2
    assert len(result["revisions"]) == 2
    assert result["timeline_note"].startswith("Timeline events summarize")
    assert [
        event["revision_iri"] for event in result["timeline"]
    ] == [
        staged["revision_iri"],
        applied["applied_revision_iri"],
    ]
    assert [
        event["timeline_role"] for event in result["timeline"]
    ] == [
        "applied_source",
        "applied_event",
    ]
    assert result["timeline"][0]["resolved_target_iri"] == (
        applied["applied_revision_iri"]
    )
    assert result["timeline"][0]["row_is_target"] is False
    assert result["timeline"][1]["staged_revision_iri"] == staged["revision_iri"]
    by_iri = {item["revision"]["iri"]: item for item in result["revisions"]}
    assert {item["revision_iri"] for item in result["revisions"]} == set(by_iri)
    assert by_iri[staged["revision_iri"]]["match_types"] == ["patch_subject"]
    assert by_iri[staged["revision_iri"]]["patch_mentions_incomplete"] is False
    assert by_iri[staged["revision_iri"]]["patch_mentions_unreadable_count"] == 0
    assert by_iri[staged["revision_iri"]]["patch_mentions"][0][
        "matched_term_roles"
    ] == ["subject"]
    assert by_iri[staged["revision_iri"]]["patch_mentions"][0][
        "matched_triples"
    ] == 1
    assert by_iri[applied["applied_revision_iri"]]["match_types"] == [
        "applied_source_patch_subject"
    ]
    assert by_iri[applied["applied_revision_iri"]]["applied_source_revision_iri"] == (
        staged["revision_iri"]
    )
    assert by_iri[applied["applied_revision_iri"]][
        "applied_source_patch_mentions_incomplete"
    ] is False
    live_only = list_resource_revisions_tool(
        db,
        resource_iri=orders,
        current_staged_work_only=True,
        include_apply_checks=False,
    )
    assert live_only["current_staged_work_only"] is True
    assert live_only["include_apply_checks"] is True
    assert live_only["count"] == 0
    assert live_only["returned_count"] == 0
    assert live_only["total_count"] == 0
    lineage = describe_resource_revision_lineage_tool(
        db,
        resource_iri=orders,
        revision_iri=applied["applied_revision_iri"],
        include_triples=True,
    )
    assert lineage["selected_role"] == "applied_event"
    assert lineage["selected_revision_iri"] == applied["applied_revision_iri"]
    assert lineage["paired_revision"]["revision"]["iri"] == staged["revision_iri"]
    assert lineage["paired_revision_iri"] == staged["revision_iri"]
    assert lineage.get("current_staged_revision_iri") is None
    assert lineage.get("current_revision_iri") is None
    assert lineage["latest_revision_iri"] == applied["applied_revision_iri"]
    assert lineage["latest_role"] == "applied_event"
    assert lineage["restage_chain_iris"] == [staged["revision_iri"]]
    assert lineage.get("alternative_revision_iris", []) == []
    assert lineage["applied_source_revision_iri"] == staged["revision_iri"]
    assert lineage["next_action_queue_item"]["row_iri"] == (
        applied["applied_revision_iri"]
    )
    assert lineage["next_action_queue_item"]["resolved_target_iri"] == (
        applied["applied_revision_iri"]
    )
    assert lineage["next_action_queue_item"]["row_is_target"] is True
    assert lineage["applied_diff_status"] == "available"
    assert lineage["applied_diff"]["graph_diffs"][0][
        "resource_triples_added_count"
    ] == 1
    assert lineage["applied_diff"]["graph_diffs"][0]["resource_triples_added"][0][
        "subject"
    ] == orders
    generic_lineage = describe_revision_lineage_tool(
        db,
        iri=applied["applied_revision_iri"],
    )
    assert generic_lineage["selected_role"] == "applied_event"
    assert generic_lineage["selected_revision_iri"] == (
        applied["applied_revision_iri"]
    )
    assert generic_lineage["selected_revision"]["iri"] == (
        applied["applied_revision_iri"]
    )
    assert generic_lineage["paired_revision"]["iri"] == staged["revision_iri"]
    assert generic_lineage["paired_revision_iri"] == staged["revision_iri"]
    assert generic_lineage["paired_role"] == "applied_source"
    assert generic_lineage["applied_revision_iri"] == applied["applied_revision_iri"]
    assert generic_lineage["staged_revision_iri"] == staged["revision_iri"]
    assert generic_lineage["applied_source_revision_iri"] == staged["revision_iri"]
    assert generic_lineage["latest_revision_iri"] == applied["applied_revision_iri"]
    assert generic_lineage["latest_role"] == "applied_event"
    assert generic_lineage["restage_chain_iris"] == [staged["revision_iri"]]
    assert generic_lineage["next_action_queue_item"]["resolved_target_iri"] == (
        applied["applied_revision_iri"]
    )
    assert generic_lineage["next_action_queue_item"]["row_is_target"] is True
    assert generic_lineage["related_revision_iris"] == [
        applied["applied_revision_iri"],
        staged["revision_iri"],
    ]
    assert generic_lineage["next_action"]["queue"] == "inspect_already_applied"
    assert generic_lineage.get("warnings", []) == []

