"""Split from test_mcp_tools.py (distillation Phase 2); tests verbatim."""

from tests.mcp.support_mcp import *  # noqa: F401,F403


def test_restage_staged_revision_tool_returns_json_like_payload(
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
    )
    db.record_map_dataset(
        "https://example.test/project#OtherDataset",
        label="Other dataset",
    )
    stale_check = check_staged_revision_apply_tool(db, iri=staged["revision_iri"])
    assert stale_check["status"] == "conflict"
    assert stale_check["validation_skipped_reason"] == "conflicts_present"
    assert stale_check["count_drifts"][0]["target_graph"] == "map"
    assert stale_check["count_drifts"][0]["delta"] == db.triple_count("map")
    assert stale_check["count_drifts"][0]["exact_changed_triples_available"] is True
    assert stale_check["count_drifts"][0]["patch_triples_checked"] == 1
    assert stale_check["count_drifts"][0]["patch_triples_currently_present"] == 0
    assert stale_check["count_drifts"][0]["patch_triples_currently_absent"] == 1
    assert stale_check["count_drifts"][0]["patch_triple_status"] == (
        "all_patch_triples_absent"
    )
    assert stale_check["snapshot_drifts"][0]["graph_role"] == "map"
    assert stale_check["snapshot_drifts"][0]["snapshot_content_digest"].startswith(
        "sha256:"
    )
    assert stale_check["snapshot_drifts"][0]["current_content_digest"].startswith(
        "sha256:"
    )
    snapshot_drift = stale_check["snapshot_drifts"][0]
    assert snapshot_drift["exact_changed_triples_available"] is True
    assert snapshot_drift["triples_added_since_snapshot_count"] == len(
        snapshot_drift["triples_added_since_snapshot"]
    )
    assert snapshot_drift["triples_removed_since_snapshot_count"] == 0
    assert snapshot_drift["triples_added_since_snapshot"]
    assert snapshot_drift.get("triples_removed_since_snapshot", []) == []
    added_drift_triple = snapshot_drift["triples_added_since_snapshot"][0]
    assert "subject_display" in added_drift_triple
    assert "predicate_display" in added_drift_triple
    assert "object_display" in added_drift_triple
    assert stale_check["suggested_next_actions"][0]["tool"] == (
        "doxabase.describe_revision"
    )
    assert stale_check["suggested_next_actions"][-1]["tool"] == (
        "doxabase.restage_staged_revision"
    )
    assert stale_check["next_action"]["action_type"] == "restage_after_review"
    assert stale_check["routing_decision"] == "restage_after_review"
    assert stale_check["next_action"]["queue"] == "restage_after_review"
    assert stale_check["next_action"]["tool_name"] == "restage_staged_revision"
    assert stale_check["next_action"]["arguments"] == {
        "revision_iris": staged["revision_iri"]
    }

    restaged = restage_staged_revision_tool(
        db, revision_iris=staged["revision_iri"]
    )

    assert restaged["revision_iri"] != staged["revision_iri"]
    assert restaged["patches"][0]["before_triple_count"] == db.triple_count("map")
    assert restaged.get("alternative_to") is None
    assert restaged["restaged_from"] == staged["revision_iri"]
    assert "prior status conflict" in restaged["restage_reason"]
    assert "blockers target_count_drift" in restaged["restage_reason"]
    assert restaged.get("current_restaged_by") is None
    assert restaged["status_after"] == "ready"
    assert restaged["decision_after"] == "review_then_apply"
    assert restaged["routing_decision_after"] == "apply_after_review"
    assert restaged["stale_resolution_state_after"] == "restaged_successor_ready"
    assert restaged.get("blocking_reasons_after", []) == []
    assert restaged["current_staged_validation_status"] == "conforms"
    assert restaged["next_action_after"]["action_type"] == "apply_after_review"
    assert restaged["next_action_after"]["tool_name"] == "apply_staged_revision"
    assert restaged["next_action_after"]["arguments"] == {
        "iri": restaged["revision_iri"]
    }
    assert restaged["next_action_queue_item_after"]["queue"] == "apply_after_review"
    assert restaged["next_action_queue_item_after"]["resolved_target_iri"] == (
        restaged["revision_iri"]
    )
    assert restaged["suggested_next_actions_after"][-1]["tool"] == (
        "doxabase.apply_staged_revision"
    )
    with pytest.raises(DoxaBaseError, match=restaged["revision_iri"]):
        restage_staged_revision_tool(
            db, revision_iris=staged["revision_iri"]
        )
    stale_description = describe_staged_revision_tool(db, staged["revision_iri"])
    assert stale_description["restaged_by"]["iri"] == restaged["revision_iri"]
    stale_check_after = check_staged_revision_apply_tool(
        db,
        iri=staged["revision_iri"],
    )
    assert stale_check_after["restaged_by"] == restaged["revision_iri"]
    assert stale_check_after["current_restaged_by"] == restaged["revision_iri"]
    assert stale_check_after["stale_resolution_state"] == "stale_handled_by_restage"
    assert stale_check_after["next_action"]["action_type"] == (
        "inspect_current_successor"
    )
    assert stale_check_after["next_action"]["arguments"] == {
        "iri": restaged["revision_iri"]
    }
    assert not any(
        action["tool"] == "doxabase.restage_staged_revision"
        for action in stale_check_after["suggested_next_actions"]
    )
    description = describe_staged_revision_tool(db, restaged["revision_iri"])
    assert description["restaged_from"]["iri"] == staged["revision_iri"]
    assert "prior status conflict" in description["restage_reason"]
    assert "blockers target_count_drift" in description["restage_reason"]
    assert check_staged_revision_apply_tool(
        db,
        iri=restaged["revision_iri"],
    )["status"] == "ready"
    applied = apply_staged_revision_tool(db, iri=restaged["revision_iri"])
    stale_check_after_apply = check_staged_revision_apply_tool(
        db,
        iri=staged["revision_iri"],
    )
    assert stale_check_after_apply["restaged_by"] == restaged["revision_iri"]
    assert (
        stale_check_after_apply["current_restaged_by"]
        == restaged["revision_iri"]
    )
    assert (
        stale_check_after_apply["stale_resolution_state"]
        == "stale_handled_by_restage"
    )
    assert stale_check_after_apply["next_action"]["action_type"] == (
        "inspect_already_applied"
    )
    assert stale_check_after_apply["next_action"]["queue"] == (
        "inspect_already_applied"
    )
    assert stale_check_after_apply["next_action"]["tool_name"] == (
        "describe_revision"
    )
    assert stale_check_after_apply["next_action"]["arguments"] == {
        "iri": applied["applied_revision_iri"]
    }
    assert stale_check_after_apply["suggested_next_actions"][0][
        "tool"
    ] == "doxabase.describe_revision"
    assert stale_check_after_apply["suggested_next_actions"][0]["args"] == {
        "iri": applied["applied_revision_iri"]
    }


def test_stage_graph_revision_tool_records_repaired_restage_successor(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    source = stage_graph_revision_tool(
        db,
        summary="Stage old orders label",
        rationale="Original candidate needs a repaired successor.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Orders rdfs:label "Old orders" .
                """,
            }
        ],
        revision_anchors=[orders],
    )
    record_map_dataset_tool(db, iri=orders, label="Current orders", is_table=True)

    repair = stage_graph_revision_tool(
        db,
        summary="Repair orders label",
        rationale="Caller-authored repaired successor.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Orders rdfs:label "Preferred orders" .
                """,
            }
        ],
        removals=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Orders rdfs:label "Current orders" .
                """,
            }
        ],
        restages_revision=source["revision_iri"],
    )

    assert repair["restaged_from"] == source["revision_iri"]
    stale_description = describe_staged_revision_tool(db, source["revision_iri"])
    assert stale_description["restaged_by"]["iri"] == repair["revision_iri"]
    current_work = list_graph_revisions_tool(
        db,
        current_staged_work_only=True,
        include_apply_checks=True,
    )
    current_work_iris = {item["iri"] for item in current_work["revisions"]}
    assert source["revision_iri"] not in current_work_iris
    assert repair["revision_iri"] in current_work_iris


def test_restage_staged_revisions_tool_exports_grouped_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    first = stage_graph_revision_tool(
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
    second = stage_graph_revision_tool(
        db,
        summary="Stage threads table",
        rationale="Threads should become durable map context after review.",
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
    db.record_map_dataset(
        "https://example.test/project#OtherDataset",
        label="Other dataset",
    )
    already_restaged = restage_staged_revision_tool(
        db,
        revision_iris=first["revision_iri"],
    )

    result = restage_staged_revisions_tool(
        db,
        revision_iris=[first["revision_iri"], second["revision_iri"]],
        path="nested/../batch-review.md",
        title="Batch review",
    )

    expected_path = (tmp_path / "batch-review.md").resolve()
    restaged_second = result["restaged_revision_iris"][0]
    assert result["export_record"]["path"] == str(expected_path)
    assert result["items"][0]["action"] == "skipped_already_handled"
    assert result["items"][1]["action"] == "restaged"
    assert result["items"][1]["source_snapshot_evidence"]["status"] == (
        "history_plus_snapshot_rows"
    )
    assert result["items"][1]["source_snapshot_evidence_completeness"] == "complete"
    assert result["items"][1]["current_snapshot_evidence"]["revision_iri"] == (
        restaged_second
    )
    assert result["items"][1]["current_snapshot_evidence"]["status"] == (
        "history_plus_snapshot_rows"
    )
    assert result["items"][1]["current_snapshot_evidence_completeness"] == "complete"
    assert result["items"][0]["next_action_after"]["action_type"] == (
        "apply_after_review"
    )
    assert result["items"][0]["next_action_after"]["arguments"] == {
        "iri": already_restaged["revision_iri"]
    }
    assert result["items"][0]["next_action_queue_item_after"]["row_iri"] == (
        already_restaged["revision_iri"]
    )
    assert result["items"][0]["next_action_queue_item_after"][
        "resolved_target_iri"
    ] == already_restaged["revision_iri"]
    assert result["items"][0]["next_action_queue_item_after"][
        "resolved_target_record_kind"
    ] == "staged_patch"
    assert result["items"][0]["next_action_queue_item_after"]["row_is_target"] is True
    assert result["items"][1]["next_action_after"]["action_type"] == (
        "apply_after_review"
    )
    assert result["items"][1]["next_action_after"]["arguments"] == {
        "iri": restaged_second
    }
    assert result["items"][1]["next_action_queue_item_after"]["row_iri"] == (
        restaged_second
    )
    assert result["items"][1]["next_action_queue_item_after"][
        "resolved_target_iri"
    ] == restaged_second
    assert result["items"][1]["suggested_next_actions_after"][-1]["tool"] == (
        "doxabase.apply_staged_revision"
    )
    assert result["current_revision_by_source"] == {
        first["revision_iri"]: already_restaged["revision_iri"],
        second["revision_iri"]: restaged_second,
    }
    assert result["review_revision_iris"] == [
        first["revision_iri"],
        already_restaged["revision_iri"],
        second["revision_iri"],
        restaged_second,
    ]
    assert result["bundle_summary"].get("unresolved_stale_revision_iris", []) == []
    assert result["bundle_summary"]["ready_restage_successor_revision_iris"] == [
        already_restaged["revision_iri"],
        restaged_second,
    ]
    assert result["bundle_summary"]["post_apply_recheck_revision_iris"] == [
        already_restaged["revision_iri"],
        restaged_second,
    ]
    assert result["bundle_summary"]["sequential_apply_recheck_candidate_iris"] == [
        already_restaged["revision_iri"],
        restaged_second,
    ]
    assert len(result["bundle_summary"]["warnings"]) == 1
    assert result["bundle_summary"]["recommended_apply_or_restage_review_iris"] == [
        already_restaged["revision_iri"],
        restaged_second,
    ]
    assert result["bundle_summary"]["next_action_queue"]["apply_after_review"] == [
        already_restaged["revision_iri"],
        restaged_second,
    ]
    assert result["bundle_summary"]["next_action_queue"]["informational"] == [
        first["revision_iri"],
        second["revision_iri"],
    ]
    assert result["bundle_summary"].get("recommended_repair_review_iris", []) == []
    stale_summary = result["revision_summaries"][0]
    assert stale_summary["next_action"]["action_type"] == "inspect_current_successor"
    assert stale_summary["next_action"]["queue"] == "informational"
    assert (
        stale_summary["apply_recommendation_scope"]
        == "prior_source_apply_check_context"
    )
    assert (
        stale_summary["summary_recommendation_source"]
        == "stale_resolution_redirect"
    )
    assert stale_summary["active_recommendation_field"] == "summary_recommendation"
    assert expected_path.exists()
    export_text = expected_path.read_text(encoding="utf-8")
    assert "## Bundle Warnings" in export_text
    assert "## Review Queues" in export_text
    assert "Queue values are returned row IRIs" in export_text
    assert "- Next action - apply after review: " in export_text
    assert "- Next action - informational: " in export_text
    assert "- Recommended review: " in export_text
    assert "- Recommended mutation review: " in export_text
    assert "- Apply/restage review: " in export_text
    assert "- Sequential apply recheck candidates: " in export_text
    assert "## Restage Context" in export_text
    assert "**doxabase.describe_revision**" in export_text


def test_restage_staged_revisions_tool_can_dry_run(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    first = stage_graph_revision_tool(
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
    )
    second = stage_graph_revision_tool(
        db,
        summary="Stage threads table",
        rationale="Threads should become durable map context after review.",
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
    db.record_map_dataset(
        "https://example.test/project#OtherDataset",
        label="Other dataset",
    )
    ready = stage_graph_revision_tool(
        db,
        summary="Stage current shipments table",
        rationale="This proposal was staged after the drift.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:CurrentShipments a rc:Dataset .
                """,
            }
        ],
    )
    staged_count_before = list_graph_revisions_tool(
        db,
        revision_type="rc:StagedRevision",
    )["count"]

    result = restage_staged_revisions_tool(
        db,
        revision_iris=[
            first["revision_iri"],
            second["revision_iri"],
            ready["revision_iri"],
        ],
        dry_run=True,
    )

    assert result["dry_run"] is True
    assert result["would_restage_revision_iris"] == [
        first["revision_iri"],
        second["revision_iri"],
    ]
    assert result.get("repair_or_replace_source_revision_iris", []) == []
    assert result.get("restaged_revision_iris", []) == []
    assert result["not_restageable_revision_iris"] == [ready["revision_iri"]]
    assert result["not_restageable_revision_iris_by_reason"] == {
        "ready": [ready["revision_iri"]],
    }
    assert [item["action"] for item in result["items"]] == [
        "would_restage",
        "would_restage",
        "skipped_not_restageable",
    ]
    assert [item.get("not_restageable_reason") for item in result["items"]] == [
        None,
        None,
        "ready",
    ]
    assert [action["tool"].removeprefix("doxabase.") for action in result["suggested_next_actions"]] == [
        "restage_staged_revision"
    ]
    assert result["suggested_next_actions"][0]["args"] == {
        "revision_iris": [
            first["revision_iri"],
            second["revision_iri"],
        ],
        "dry_run": False,
    }
    assert list_graph_revisions_tool(
        db,
        revision_type="rc:StagedRevision",
    )["count"] == staged_count_before


def test_restage_staged_revisions_tool_serializes_repair_first_warning(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    scope = "https://example.test/project#DispatchTemporalScope"
    clock = "https://example.test/project#dispatch_events__event_local_time"
    timezone = "https://example.test/project#dispatch_events__timezone_hint"
    db.import_turtle(
        """
        @prefix ft: <https://example.test/project/systematisation#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ft:TemporalInterpretationScope a rdfs:Class .

        ft:clockColumn a rdf:Property .

        ft:timezoneEvidenceColumn a rdf:Property .
        """,
        graph="ontology",
    )
    db.import_turtle(
        """
        @prefix ft: <https://example.test/project/systematisation#> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .

        ft:TemporalInterpretationScopeShape a sh:NodeShape ;
            sh:targetClass ft:TemporalInterpretationScope ;
            sh:property [
                sh:path ft:timezoneEvidenceColumn ;
                sh:minCount 1 ;
                sh:nodeKind sh:IRI
            ] .
        """,
        graph="shapes",
    )
    source = db.stage_graph_revision(
        summary="Stage incomplete temporal scope",
        rationale="The source intentionally fails staged validation.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix ft: <https://example.test/project/systematisation#> .

                    <{scope}> a ft:TemporalInterpretationScope ;
                        ft:clockColumn <{clock}> .
                """,
            }
        ],
        validation_scope="all",
    )
    db.import_turtle(
        f"""
        @prefix ft: <https://example.test/project/systematisation#> .

        <{scope}> ft:timezoneEvidenceColumn <{timezone}> .
        """,
        graph="map",
    )

    result = restage_staged_revisions_tool(
        db,
        revision_iris=[source.revision_iri],
        dry_run=True,
    )

    item = result["items"][0]
    assert item["action"] == "would_restage"
    assert result.get("would_restage_revision_iris", []) == []
    assert result["repair_first_revision_iris"] == [source.revision_iri]
    assert item["source_staged_validation_status"] == "failed"
    assert item["routing_decision_after"] == "repair_or_replace"
    assert any(
        (action["tool"], action["args"].get("dry_run")) == ("doxabase.restage_staged_revision", True)
        for action in item["suggested_next_actions_after"]
    )
    assert not any(
        action["tool"] == "doxabase.restage_staged_revision"
        and action["args"].get("dry_run") is not True
        for action in item["suggested_next_actions_after"]
    )
    assert item["repair_first_warning"] is not None
    assert "Repair-first warning" in item["repair_first_warning"]
    assert item["repair_first_warning"] in item["note"]

