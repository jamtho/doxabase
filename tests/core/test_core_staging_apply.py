"""Split from test_doxabase_core.py (distillation Phase 2); tests verbatim."""

from tests.core.support_core import *  # noqa: F401,F403


def test_apply_staged_revision_mutates_graph_and_records_history(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    addition = """
    @prefix ex: <https://example.test/project#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:Messages a rc:Dataset, rc:Table ;
        rdfs:label "Messages" .
    """
    staged = db.stage_graph_revision(
        summary="Stage messages table",
        rationale="Messages should become durable map context after review.",
        additions=[{"graph": "map", "content": addition}],
        revision_anchors=["https://example.test/project#Messages"],
        validation_scope="all",
    )

    check = db.check_staged_revision_apply(staged.revision_iri)
    assert check.revision_iri == staged.revision_iri
    assert check.staged_revision_iri == staged.revision_iri
    assert check.can_apply is True
    assert check.status == "ready"
    assert check.decision == "review_then_apply"
    assert check.review_recommended is True
    assert check.blocking_reasons == []
    assert check.recommended_resolution is not None
    assert "apply only if the proposal is still desired" in (
        check.recommended_resolution
    )
    assert check.summary == (
        "Ready to apply 1 patch(es) across map: +3 triple(s), -0 triple(s)."
    )
    assert check.conflicts == []
    assert check.validation_conforms is True
    assert check.validation_skipped_reason is None
    assert check.patches_checked == 1
    assert check.triples_to_add == 3
    assert check.triples_to_remove == 0
    assert check.patch_checks[0].current_triple_count == 0
    assert check.patch_checks[0].preview_triple_count == 3
    assert check.suggested_next_actions[0].tool == "doxabase.describe_staged_revision"
    assert check.suggested_next_actions[0].tool == (
        "doxabase.describe_staged_revision"
    )
    assert check.suggested_next_actions[0].args == {"iri": staged.revision_iri}
    assert check.suggested_next_actions[-1].tool == "doxabase.apply_staged_revision"
    assert check.next_action is not None
    assert check.next_action.action_type == "apply_after_review"
    assert check.next_action.queue == "apply_after_review"
    assert check.next_action.tool_name == "apply_staged_revision"
    assert check.next_action.arguments == {"iri": staged.revision_iri}
    ready_description = db.describe_staged_revision(staged.revision_iri)
    assert ready_description.current_apply_check is None
    assert ready_description.stored_review_context is None
    ready_description_with_check = db.describe_staged_revision(
        staged.revision_iri,
        include_current_apply_check=True,
    )
    assert ready_description_with_check.stored_review_context is None
    assert ready_description_with_check.current_apply_check is not None
    ready_summary = ready_description_with_check.current_apply_check
    assert ready_summary.status == "ready"
    assert ready_summary.decision == "review_then_apply"
    assert ready_summary.can_apply is True
    assert ready_summary.validation_conforms is True
    assert ready_summary.patches_checked == 1
    assert ready_summary.triples_to_add == 3
    assert ready_summary.triples_to_remove == 0
    assert ready_summary.next_action is not None
    assert ready_summary.next_action.action_type == "apply_after_review"
    assert ready_summary.next_action.queue == "apply_after_review"
    assert ready_summary.next_action.arguments == {"iri": staged.revision_iri}
    assert ready_summary.error is None

    result = db.apply_staged_revision(staged.revision_iri)

    assert result.staged_revision_iri == staged.revision_iri
    assert result.changed_graphs == ["map"]
    assert result.post_apply_recheck_revisions == []
    assert result.post_apply_recheck_revision_iris == []
    assert result.post_apply_recheck_is_partial_queue is True
    assert [action.tool.removeprefix("doxabase.") for action in result.suggested_next_actions] == [
        "plan_staged_revision_recovery"
    ]
    assert result.suggested_next_actions[0].args == {
        "current_staged_work_only": True
    }
    assert result.patches_applied == 1
    assert result.triples_added == 3
    assert result.triples_removed == 0
    assert result.validation_conforms is True
    assert db.triple_count("map") == 3
    messages = db.describe_dataset("https://example.test/project#Messages")
    assert messages.label == "Messages"

    applied = db.describe_graph_revision(result.applied_revision_iri)
    assert applied.record_kind == "applied_event"
    assert applied.revision_type == RC + "AppliedStagedRevision"
    assert applied.snapshot_evidence.status == "history_plus_snapshot_rows"
    assert applied.snapshot_evidence.exact_snapshot_graph_roles == ["map"]
    assert applied.revision_type_label == "applied staged revision"
    assert applied.applies_staged_revision == staged.revision_iri
    assert applied.applied_source is not None
    assert applied.applied_source.iri == staged.revision_iri
    assert applied.applied_source.summary == "Stage messages table"
    assert applied.applied_source.revision_stance_label == "candidate revision"
    assert applied.applied_source.patch_count == 1
    assert applied.applied_source.patches[0].target_graph == "map"
    assert applied.applied_source.patches[0].count_basis == "target_graph_only"
    assert applied.applied_source.patches[0].before_triple_count == 0
    assert applied.applied_source.patches[0].after_triple_count == 3
    assert applied.applied_source.graph_snapshots[0].graph_role == "map"
    applied_payload = to_dict(applied)
    assert "content" not in applied_payload["applied_source"]["patches"][0]
    assert applied.changed_graphs == ["map"]
    assert applied.validation_conforms is True
    assert applied.graph_snapshots[0].graph_role == "map"
    assert applied.graph_snapshots[0].triple_count == 3
    assert applied.graph_snapshots[0].content_digest is not None
    assert applied.graph_snapshots[0].content_digest.startswith("sha256:")
    assert [action.tool.removeprefix("doxabase.") for action in applied.suggested_next_actions] == [
        "describe_graph_revision",
        "describe_applied_revision_diff",
    ]
    assert applied.suggested_next_actions[1].args == {
        "iri": result.applied_revision_iri
    }
    diff = db.describe_applied_revision_diff(result.applied_revision_iri)
    assert diff.applied_revision_iri == result.applied_revision_iri
    assert diff.staged_revision_iri == staged.revision_iri
    assert diff.snapshot_evidence.status == "history_plus_snapshot_rows"
    assert diff.snapshot_evidence.exact_snapshot_graph_roles == ["map"]
    assert diff.source_snapshot_evidence.status == "history_plus_snapshot_rows"
    assert diff.source_snapshot_evidence.exact_snapshot_graph_roles == ["map"]
    assert diff.changed_graphs == ["map"]
    assert len(diff.graph_diffs) == 1
    map_diff = diff.graph_diffs[0]
    assert map_diff.graph_role == "map"
    assert map_diff.count_basis == "target_graph_only"
    assert map_diff.before_revision_iri == staged.revision_iri
    assert map_diff.after_revision_iri == result.applied_revision_iri
    assert map_diff.before_triple_count == 0
    assert map_diff.after_triple_count == 3
    assert map_diff.before_content_digest is not None
    assert map_diff.after_content_digest == applied.graph_snapshots[0].content_digest
    assert map_diff.exact_changed_triples_available is True
    assert map_diff.exact_changed_triples_included is False
    assert map_diff.triples_added_count == 3
    assert map_diff.triples_removed_count == 0
    assert map_diff.triples_added_truncated is True
    assert map_diff.triples_removed_truncated is False
    assert map_diff.max_triples == 500
    assert map_diff.triples_added == []
    assert map_diff.triples_removed == []
    exact_diff = db.describe_applied_revision_diff(
        result.applied_revision_iri,
        include_triples=True,
    )
    exact_map_diff = exact_diff.graph_diffs[0]
    assert exact_diff.include_triples is True
    assert exact_map_diff.count_basis == "target_graph_only"
    assert exact_map_diff.exact_changed_triples_included is True
    assert exact_map_diff.triples_added_truncated is False
    assert {triple.subject for triple in exact_map_diff.triples_added} == {
        "https://example.test/project#Messages"
    }
    before_snapshot = db.describe_revision_graph_snapshot(
        staged.revision_iri,
        "map",
        include_triples=True,
    )
    assert before_snapshot.snapshot_evidence.status == "history_plus_snapshot_rows"
    assert before_snapshot.triple_count == 0
    assert before_snapshot.content_digest == map_diff.before_content_digest
    assert before_snapshot.count_basis == "stored_snapshot_rows"
    assert before_snapshot.exact_snapshot_available is True
    assert before_snapshot.triples_included is True
    assert before_snapshot.triples_truncated is False
    assert before_snapshot.triples == []
    after_snapshot = db.describe_revision_graph_snapshot(
        result.applied_revision_iri,
        "map",
        include_triples=True,
        max_triples=2,
    )
    assert after_snapshot.snapshot_evidence.status == "history_plus_snapshot_rows"
    assert after_snapshot.triple_count == 3
    assert after_snapshot.content_digest == applied.graph_snapshots[0].content_digest
    assert after_snapshot.count_basis == "stored_snapshot_rows"
    assert after_snapshot.stored_at is not None
    assert after_snapshot.exact_snapshot_available is True
    assert after_snapshot.triples_included is True
    assert after_snapshot.triples_truncated is True
    assert after_snapshot.max_triples == 2
    assert len(after_snapshot.triples) == 2
    assert {triple.subject for triple in after_snapshot.triples} == {
        "https://example.test/project#Messages"
    }
    with pytest.raises(DoxaBaseError, match="Unknown graph role"):
        db.describe_revision_graph_snapshot(
            result.applied_revision_iri,
            "not_a_graph_role",
        )
    with pytest.raises(DoxaBaseError, match="max_triples must be at least 1"):
        db.describe_revision_graph_snapshot(
            result.applied_revision_iri,
            "map",
            max_triples=0,
        )
    with pytest.raises(DoxaBaseError) as wrong_resource_excinfo:
        db.describe_resource_revision_lineage(
            "https://example.test/project#UnrelatedResource",
            result.applied_revision_iri,
        )
    wrong_resource_message = str(wrong_resource_excinfo.value)
    assert "was not found in resource lineage" in wrong_resource_message
    assert "Revision exists in history" in wrong_resource_message
    assert "Snapshot rows exist for this revision IRI" not in wrong_resource_message
    assert "Import the project/history RDF bundle" not in wrong_resource_message
    project_path = tmp_path / "project.trig"
    snapshot_path = tmp_path / "revision-snapshots.json"
    db.export_trig(project_path, graphs="project")
    snapshot_export = db.export_revision_snapshots(
        snapshot_path,
        revision_iris=[result.applied_revision_iri],
    )
    assert snapshot_export.snapshot_count == 2
    assert snapshot_export.quad_count == 3
    assert snapshot_export.revision_iris == [
        result.applied_revision_iri,
        staged.revision_iri,
    ]

    round_trip = DoxaBase.create(tmp_path / "round-trip.sqlite")
    round_trip.import_trig(project_path)
    imported_resource_list_before_snapshots = round_trip.list_resource_revisions(
        "https://example.test/project#Messages",
        include_patch_mentions=True,
        include_apply_checks=True,
        drift_detail="summary",
    )
    assert imported_resource_list_before_snapshots.count == 2
    assert imported_resource_list_before_snapshots.patch_mention_scan.status == (
        "complete"
    )
    assert {
        iri
        for iri in imported_resource_list_before_snapshots.next_action_queue[
            "complete_handoff_import"
        ]
    } == {result.applied_revision_iri, staged.revision_iri}
    assert imported_resource_list_before_snapshots.next_action_queue_item_counts == {
        "complete_handoff_import": 2,
    }
    assert {
        item.revision.iri: item.match_types
        for item in imported_resource_list_before_snapshots.revisions
    } == {
        result.applied_revision_iri: [
            "revision_anchor",
            "applied_source_patch_subject",
            "applied_source_revision_anchor",
        ],
        staged.revision_iri: ["revision_anchor", "patch_subject"],
    }
    assert (
        '"content"'
        not in json.dumps(to_dict(imported_resource_list_before_snapshots))
    )
    imported_lineage_before_snapshots = (
        round_trip.describe_resource_revision_lineage(
            "https://example.test/project#Messages",
            result.applied_revision_iri,
            include_triples=True,
        )
    )
    assert imported_lineage_before_snapshots.selected_role == "applied_event"
    assert imported_lineage_before_snapshots.next_action is not None
    assert imported_lineage_before_snapshots.next_action.queue == (
        "complete_handoff_import"
    )
    assert imported_lineage_before_snapshots.suggested_next_actions[
        0
    ].tool == "doxabase.import_revision_snapshots"
    assert imported_lineage_before_snapshots.paired_revision is not None
    assert (
        imported_lineage_before_snapshots.paired_revision.revision.iri
        == staged.revision_iri
    )
    assert imported_lineage_before_snapshots.paired_role == "applied_source"
    assert imported_lineage_before_snapshots.applied_diff_status == "unavailable"
    assert imported_lineage_before_snapshots.applied_diff is not None
    assert (
        imported_lineage_before_snapshots.applied_diff.graph_diffs[
            0
        ].exact_changed_triples_available
        is False
    )
    imported_status_before_snapshots = round_trip.describe_revision_snapshot_evidence(
        result.applied_revision_iri
    )
    assert imported_status_before_snapshots.status == "history_only_count_digest"
    assert imported_status_before_snapshots.rdf_snapshot_graph_roles == ["map"]
    assert imported_status_before_snapshots.stored_snapshot_graph_roles == []
    assert [
        action.tool.removeprefix("doxabase.")
        for action in imported_status_before_snapshots.suggested_next_actions
    ] == ["import_revision_snapshots"]
    snapshot_action = imported_status_before_snapshots.suggested_next_actions[0]
    assert snapshot_action.args == {
        "path": "/tmp/revision-snapshots.json",
        "path_is_placeholder": True,
    }
    assert "real handoff path" in snapshot_action.reason
    imported_graph_detail_before_snapshots = round_trip.describe_graph_revision(
        result.applied_revision_iri
    )
    assert [
        action.tool.removeprefix("doxabase.")
        for action in imported_graph_detail_before_snapshots.suggested_next_actions[
            :2
        ]
    ] == ["import_revision_snapshots", "describe_graph_revision"]
    imported_revision_list_before_snapshots = round_trip.list_graph_revisions(
        record_kind="applied_event"
    )
    assert imported_revision_list_before_snapshots.next_action_queue == {
        "complete_handoff_import": [result.applied_revision_iri]
    }
    assert imported_revision_list_before_snapshots.revisions[0].next_action is not None
    assert imported_revision_list_before_snapshots.revisions[0].next_action.queue == (
        "complete_handoff_import"
    )
    imported_graph_lineage_before_snapshots = round_trip.describe_revision_lineage(
        result.applied_revision_iri
    )
    assert imported_graph_lineage_before_snapshots.selected_role == "applied_event"
    assert imported_graph_lineage_before_snapshots.next_action is not None
    assert imported_graph_lineage_before_snapshots.next_action.queue == (
        "complete_handoff_import"
    )
    assert imported_graph_lineage_before_snapshots.suggested_next_actions[
        0
    ].tool == "doxabase.import_revision_snapshots"
    assert [
        item.snapshot_evidence.status
        for item in [
            imported_graph_lineage_before_snapshots.selected_revision,
            imported_graph_lineage_before_snapshots.paired_revision,
        ]
        if item is not None
    ] == ["history_only_count_digest", "history_only_count_digest"]
    assert len(imported_graph_lineage_before_snapshots.warnings) == 2
    assert all(
        "import a companion revision snapshot JSON bundle" in warning
        for warning in imported_graph_lineage_before_snapshots.warnings
    )
    imported_diff_before_snapshots = round_trip.describe_applied_revision_diff(
        result.applied_revision_iri,
        include_triples=True,
    )
    assert (
        imported_diff_before_snapshots.snapshot_evidence.status
        == "history_only_count_digest"
    )
    assert (
        imported_diff_before_snapshots.source_snapshot_evidence.status
        == "history_only_count_digest"
    )
    assert [
        action.tool.removeprefix("doxabase.")
        for action in (
            imported_diff_before_snapshots.snapshot_evidence.suggested_next_actions
        )
    ] == ["import_revision_snapshots"]
    assert [
        action.tool.removeprefix("doxabase.")
        for action in imported_diff_before_snapshots.suggested_next_actions
    ] == ["import_revision_snapshots"]
    assert (
        imported_diff_before_snapshots.graph_diffs[0].exact_changed_triples_available
        is False
    )
    assert "import_revision_snapshots" in (
        imported_diff_before_snapshots.graph_diffs[0].note
    )
    rdf_only_snapshot = round_trip.describe_revision_graph_snapshot(
        result.applied_revision_iri,
        "map",
        include_triples=True,
    )
    assert rdf_only_snapshot.snapshot_evidence.status == "history_only_count_digest"
    assert rdf_only_snapshot.triple_count == 3
    assert rdf_only_snapshot.content_digest == applied.graph_snapshots[0].content_digest
    assert rdf_only_snapshot.count_basis == "rdf_history_graph_snapshot"
    assert rdf_only_snapshot.exact_snapshot_available is False
    assert rdf_only_snapshot.triples_included is False
    assert rdf_only_snapshot.triples == []
    assert [
        action.tool.removeprefix("doxabase.") for action in rdf_only_snapshot.suggested_next_actions
    ] == ["import_revision_snapshots"]
    assert "Import a companion revision snapshot JSON bundle" in (
        rdf_only_snapshot.note
    )
    rdf_only_version_diff = round_trip.describe_graph_version_diff(
        "map",
        staged.revision_iri,
        after_revision_iri=result.applied_revision_iri,
    )
    assert rdf_only_version_diff.exact_changed_triples_available is False
    assert [
        action.tool.removeprefix("doxabase.") for action in rdf_only_version_diff.suggested_next_actions
    ][:1] == ["import_revision_snapshots"]

    snapshot_import = round_trip.import_revision_snapshots(snapshot_path)
    assert snapshot_import.imported_snapshot_count == 2
    assert snapshot_import.skipped_snapshot_count == 0
    assert snapshot_import.imported_quad_count == 3
    assert {
        item.revision_iri: item.status
        for item in snapshot_import.post_import_snapshot_evidence
    } == {
        result.applied_revision_iri: "history_plus_snapshot_rows",
        staged.revision_iri: "history_plus_snapshot_rows",
    }
    imported_status_after_snapshots = round_trip.describe_revision_snapshot_evidence(
        result.applied_revision_iri
    )
    assert imported_status_after_snapshots.status == "history_plus_snapshot_rows"
    assert imported_status_after_snapshots.exact_snapshot_graph_roles == ["map"]
    imported_graph_lineage_after_snapshots = round_trip.describe_revision_lineage(
        result.applied_revision_iri
    )
    assert imported_graph_lineage_after_snapshots.warnings == []
    imported_resource_list_after_snapshots = round_trip.list_resource_revisions(
        "https://example.test/project#Messages",
        include_patch_mentions=True,
        include_apply_checks=True,
        drift_detail="summary",
    )
    assert imported_resource_list_after_snapshots.count == 2
    assert {
        iri
        for iri in imported_resource_list_after_snapshots.next_action_queue[
            "inspect_already_applied"
        ]
    } == {result.applied_revision_iri, staged.revision_iri}
    assert imported_resource_list_after_snapshots.next_action_queue_item_counts == {
        "inspect_already_applied": 2,
    }
    assert {
        item.row_iri: item.resolved_target_iri
        for item in imported_resource_list_after_snapshots.next_action_queue_items
    } == {
        result.applied_revision_iri: result.applied_revision_iri,
        staged.revision_iri: result.applied_revision_iri,
    }
    assert (
        '"content"'
        not in json.dumps(to_dict(imported_resource_list_after_snapshots))
    )
    imported_exact_diff = round_trip.describe_applied_revision_diff(
        result.applied_revision_iri,
        include_triples=True,
    )
    assert imported_exact_diff.graph_diffs[0].exact_changed_triples_available is True
    assert {
        triple.subject
        for triple in imported_exact_diff.graph_diffs[0].triples_added
    } == {"https://example.test/project#Messages"}
    imported_after_snapshot = round_trip.describe_revision_graph_snapshot(
        result.applied_revision_iri,
        "map",
        include_triples=True,
        max_triples=1,
    )
    assert imported_after_snapshot.snapshot_evidence.status == (
        "history_plus_snapshot_rows"
    )
    assert imported_after_snapshot.exact_snapshot_available is True
    assert imported_after_snapshot.triples_included is True
    assert imported_after_snapshot.triples_truncated is True
    assert len(imported_after_snapshot.triples) == 1
    imported_lineage_after_snapshots = round_trip.describe_resource_revision_lineage(
        "https://example.test/project#Messages",
        result.applied_revision_iri,
        include_triples=True,
    )
    assert imported_lineage_after_snapshots.applied_diff_status == "available"
    assert imported_lineage_after_snapshots.applied_diff is not None
    imported_resource_diff = imported_lineage_after_snapshots.applied_diff.graph_diffs[
        0
    ]
    assert imported_resource_diff.exact_changed_triples_available is True
    assert imported_resource_diff.exact_changed_triples_included is True
    assert imported_resource_diff.resource_triples_added_count == 3
    assert imported_resource_diff.resource_triples_removed_count == 0
    assert {
        triple.subject for triple in imported_resource_diff.resource_triples_added
    } == {"https://example.test/project#Messages"}
    skipped_import = round_trip.import_revision_snapshots(snapshot_path)
    assert skipped_import.imported_snapshot_count == 0
    assert skipped_import.skipped_snapshot_count == 2
    assert [
        item.status for item in skipped_import.post_import_snapshot_evidence
    ] == [
        "history_plus_snapshot_rows",
        "history_plus_snapshot_rows",
    ]
    workflow_path = tmp_path / "workflow.trig"
    db.export_trig(workflow_path, graphs="workflow")
    workflow_round_trip = DoxaBase.create(tmp_path / "workflow-round-trip.sqlite")
    workflow_round_trip.import_trig(workflow_path)
    workflow_status = workflow_round_trip.describe_revision_snapshot_evidence(
        result.applied_revision_iri
    )
    assert workflow_status.status == "history_missing"
    assert workflow_status.rdf_snapshot_graph_roles == []
    assert workflow_status.stored_snapshot_graph_roles == []
    with pytest.raises(DoxaBaseError, match="was not found in history"):
        workflow_round_trip.describe_graph_revision(result.applied_revision_iri)
    orphan_import = workflow_round_trip.import_revision_snapshots(snapshot_path)
    assert {
        item.revision_iri: item.status
        for item in orphan_import.post_import_snapshot_evidence
    } == {
        result.applied_revision_iri: "snapshot_rows_without_history",
        staged.revision_iri: "snapshot_rows_without_history",
    }
    assert [
        action.tool.removeprefix("doxabase.")
        for action in orphan_import.post_import_snapshot_evidence[
            0
        ].suggested_next_actions
    ] == ["import_trig"]
    orphan_status = workflow_round_trip.describe_revision_snapshot_evidence(
        result.applied_revision_iri
    )
    assert orphan_status.status == "snapshot_rows_without_history"
    assert orphan_status.orphan_snapshot_row_graph_roles == ["map"]
    assert [action.tool.removeprefix("doxabase.") for action in orphan_status.suggested_next_actions] == [
        "import_trig"
    ]
    assert orphan_status.suggested_next_actions[0].args == {
        "path": "/tmp/project.trig",
        "path_is_placeholder": True,
    }
    assert "real handoff path" in orphan_status.suggested_next_actions[0].reason
    with pytest.raises(DoxaBaseError, match="Snapshot rows exist"):
        workflow_round_trip.describe_applied_revision_diff(
            result.applied_revision_iri
        )
    assert exact_map_diff.triples_removed == []
    with pytest.raises(DoxaBaseError, match="max_triples must be at least 1"):
        db.describe_applied_revision_diff(
            result.applied_revision_iri,
            include_triples=True,
            max_triples=0,
        )
    with pytest.raises(DoxaBaseError, match="not an applied staged revision"):
        db.describe_applied_revision_diff(staged.revision_iri)
    context = db.describe_resource(result.applied_revision_iri, graph="history")
    assert any(
        triple.predicate == RC + "appliesStagedRevision"
        and triple.object == staged.revision_iri
        for triple in context.outgoing
    )
    assert db.validate_graph(scope="all").conforms

    with pytest.raises(DoxaBaseError, match="already been applied"):
        db.apply_staged_revision(staged.revision_iri)
    applied_check = db.check_staged_revision_apply(staged.revision_iri)
    assert applied_check.can_apply is False
    assert applied_check.status == "already_applied"
    assert applied_check.decision == "inspect_applied_revision"
    assert applied_check.review_recommended is False
    assert applied_check.blocking_reasons == ["already_applied"]
    assert applied_check.validation_skipped_reason == "already_applied"
    assert applied_check.recommended_resolution is not None
    assert "do not apply" in applied_check.recommended_resolution
    assert applied_check.summary == (
        f"Already applied by {result.applied_revision_iri}."
    )
    assert applied_check.already_applied_by == result.applied_revision_iri
    assert applied_check.suggested_next_actions[0].tool == (
        "doxabase.describe_graph_revision"
    )
    assert applied_check.suggested_next_actions[1].tool == (
        "doxabase.describe_applied_revision_diff"
    )
    assert applied_check.suggested_next_actions[1].args == {
        "iri": result.applied_revision_iri
    }
    applied_description = db.describe_staged_revision(staged.revision_iri)
    assert applied_description.application_status == "already_applied"
    assert applied_description.applied_by is not None
    assert applied_description.applied_by.iri == result.applied_revision_iri
    applied_description_with_check = db.describe_staged_revision(
        staged.revision_iri,
        include_current_apply_check=True,
    )
    assert applied_description_with_check.current_apply_check is not None
    applied_summary = applied_description_with_check.current_apply_check
    assert applied_summary.status == "already_applied"
    assert applied_summary.decision == "inspect_applied_revision"
    assert applied_summary.already_applied_by == result.applied_revision_iri
    assert applied_summary.validation_skipped_reason == "already_applied"
    applied_export = db.export_staged_revisions(
        [staged.revision_iri],
        tmp_path / "applied-staged-review.md",
    )
    assert applied_export.revision_summaries[0].stale_resolution_state == (
        "already_applied"
    )
    assert applied_export.bundle_summary.recommended_review_iris == [
        staged.revision_iri
    ]
    assert applied_export.bundle_summary.post_apply_recheck_revision_iris == []
    assert applied_export.bundle_summary.recommended_mutation_review_iris == []
    assert applied_export.bundle_summary.recommended_apply_or_restage_review_iris == []
    assert applied_export.bundle_summary.recommended_repair_review_iris == []

    applied_export_path = tmp_path / "applied-single-review.md"
    db.export_staged_revision(staged.revision_iri, applied_export_path)
    applied_export_text = applied_export_path.read_text(encoding="utf-8")
    assert "**doxabase.describe_applied_revision_diff**" in applied_export_text
    assert applied_export.bundle_summary.recommended_applied_inspection_iris == [
        staged.revision_iri
    ]

    with pytest.raises(DoxaBaseError) as mixed_export_exc:
        db.export_staged_revisions(
            [staged.revision_iri, result.applied_revision_iri],
            tmp_path / "mixed-applied-event-review.md",
        )

    mixed_export_message = str(mixed_export_exc.value)
    assert "export_staged_revisions only accepts staged patch revisions" in (
        mixed_export_message
    )
    assert "applied revision event" in mixed_export_message
    assert result.applied_revision_iri in mixed_export_message
    assert staged.revision_iri in mixed_export_message

    recovery_event_plan = db.plan_staged_revision_recovery(
        [result.applied_revision_iri]
    )
    assert recovery_event_plan.returned_count == 1
    assert recovery_event_plan.lane_counts == {"inspect_already_applied": 1}
    assert recovery_event_plan.next_action_queue_item_counts == {
        "inspect_already_applied": 1
    }
    assert recovery_event_plan.not_restageable_revision_iris_by_reason == {
        "applied_event_record": [result.applied_revision_iri]
    }
    assert recovery_event_plan.recommended_applied_inspection_iris == [
        result.applied_revision_iri
    ]
    assert recovery_event_plan.review_revision_iris == [result.applied_revision_iri]
    applied_event_lane = recovery_event_plan.lanes[0]
    assert applied_event_lane.source_revision_iri == result.applied_revision_iri
    assert applied_event_lane.current_revision_iri == result.applied_revision_iri
    assert applied_event_lane.lane == "inspect_already_applied"
    assert applied_event_lane.batch_action == "skipped_applied_event"
    assert applied_event_lane.not_restageable_reason == "applied_event_record"
    assert applied_event_lane.next_action is not None
    assert applied_event_lane.next_action.tool_name == "describe_graph_revision"
    assert applied_event_lane.next_action.arguments == {
        "iri": result.applied_revision_iri
    }
    assert applied_event_lane.next_action_queue_item is not None
    assert applied_event_lane.next_action_queue_item.record_kind == "applied_event"
    assert applied_event_lane.next_action_queue_item.row_is_target is True
    assert applied_event_lane.next_action_queue_item.resolved_target_iri == (
        result.applied_revision_iri
    )
    assert [
        action.tool.removeprefix("doxabase.") for action in applied_event_lane.suggested_next_actions
    ] == ["describe_graph_revision", "describe_applied_revision_diff"]
    assert any(
        action.tool == "doxabase.describe_applied_revision_diff"
        and action.args == {"iri": result.applied_revision_iri}
        for action in recovery_event_plan.suggested_next_actions
    )

    with pytest.raises(DoxaBaseError) as restage_event_exc:
        db.restage_staged_revisions(
            [result.applied_revision_iri],
            dry_run=True,
        )

    restage_event_message = str(restage_event_exc.value)
    assert "is an applied revision event, not a staged patch revision" in (
        restage_event_message
    )
    assert staged.revision_iri in restage_event_message


def test_apply_staged_revision_removes_existing_triples(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    messages = """
    @prefix ex: <https://example.test/project#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:Messages a rc:Dataset, rc:Table ;
        rdfs:label "Messages" .
    """
    staged_addition = db.stage_graph_revision(
        summary="Stage messages table",
        rationale="Create a removable map resource for the apply test.",
        additions=[{"graph": "map", "content": messages}],
    )
    db.apply_staged_revision(staged_addition.revision_iri)
    assert db.triple_count("map") == 3

    staged_removal = db.stage_graph_revision(
        summary="Remove messages table",
        rationale="The messages resource was staged only as temporary context.",
        removals=[{"graph": "map", "content": messages}],
    )
    result = db.apply_staged_revision(staged_removal.revision_iri)

    assert result.changed_graphs == ["map"]
    assert result.triples_added == 0
    assert result.triples_removed == 3
    diff = db.describe_applied_revision_diff(
        result.applied_revision_iri,
        include_triples=True,
        max_triples=2,
    )
    assert diff.changed_graphs == ["map"]
    assert diff.graph_diffs[0].triples_added == []
    assert diff.graph_diffs[0].triples_added_count == 0
    assert diff.graph_diffs[0].triples_removed_count == 3
    assert diff.graph_diffs[0].exact_changed_triples_included is True
    assert diff.graph_diffs[0].triples_removed_truncated is True
    assert len(diff.graph_diffs[0].triples_removed) == 2
    assert {triple.subject for triple in diff.graph_diffs[0].triples_removed} == {
        "https://example.test/project#Messages"
    }
    assert db.triple_count("map") == 0
    with pytest.raises(DoxaBaseError, match="Messages"):
        db.describe_dataset("https://example.test/project#Messages")


def test_apply_staged_revision_rejects_count_conflicts(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = db.stage_graph_revision(
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

    check = db.check_staged_revision_apply(staged.revision_iri)
    assert check.can_apply is False
    assert check.status == "conflict"
    assert check.decision == "restage_against_current_graph"
    assert check.review_recommended is True
    assert check.blocking_reasons == ["target_count_drift"]
    assert check.recommended_resolution is not None
    assert "Restage the proposal" in check.recommended_resolution
    assert check.summary.startswith("Blocked by 1 conflict(s); first conflict:")
    assert check.effective_delta_summary.replayable_triples_to_add == 0
    assert check.effective_delta_summary.replayable_triples_to_remove == 0
    assert check.effective_delta_summary.blocked_patch_triples_to_add == 1
    assert check.effective_delta_summary.blocked_patch_triples_to_remove == 0
    assert check.effective_delta_summary.total_effective_triples_to_add == 1
    assert check.effective_delta_summary.total_effective_triples_to_remove == 0
    assert check.effective_delta_summary.already_effective is False
    assert check.effective_delta_summary.has_conflicted_patches is True
    assert check.effective_delta_summary.patch_triple_status_counts == {
        "all_patch_triples_absent": 1,
    }
    assert check.effective_delta_summary.basis == "conflicted_patches_excluded"
    assert check.validation_conforms is None
    assert check.validation_skipped_reason == "conflicts_present"
    assert len(check.conflicts) == 1
    assert len(check.count_drifts) == 1
    assert check.count_drifts[0].target_graph == "map"
    assert check.count_drifts[0].count_basis == "target_graph_only"
    assert check.count_drifts[0].patch_sequence_index == 1
    assert check.count_drifts[0].expected_before_triple_count == 0
    assert check.count_drifts[0].expected_before_basis == (
        "expected_before_triple_count is the original staged graph snapshot "
        "before patch 1"
    )
    assert check.count_drifts[0].current_triple_count == db.triple_count("map")
    assert check.count_drifts[0].delta == db.triple_count("map")
    assert check.count_drifts[0].exact_changed_triples_available is True
    assert check.count_drifts[0].patch_operation == RC + "AdditionPatch"
    assert check.count_drifts[0].patch_triples_checked == 1
    assert check.count_drifts[0].patch_triples_currently_present == 0
    assert check.count_drifts[0].patch_triples_currently_absent == 1
    assert check.count_drifts[0].patch_triple_status == "all_patch_triples_absent"
    assert "available in snapshot_drifts" in check.count_drifts[0].note
    assert len(check.snapshot_drifts) == 1
    assert check.snapshot_drifts[0].exact_changed_triples_available is True
    assert check.snapshot_drifts[0].triples_added_since_snapshot_count == len(
        check.snapshot_drifts[0].triples_added_since_snapshot
    )
    assert check.snapshot_drifts[0].triples_removed_since_snapshot_count == 0
    assert check.snapshot_drifts[0].triples_added_since_snapshot
    assert check.snapshot_drifts[0].triples_removed_since_snapshot == []
    assert (
        check.snapshot_drifts[0].drift_relevance
        == "broad_patch_object_overlap"
    )
    assert check.snapshot_drifts[0].patch_overlap_subjects == []
    assert str(RDF.type) in check.snapshot_drifts[0].patch_overlap_predicates
    assert check.snapshot_drifts[0].patch_overlap_objects == [RC + "Dataset"]
    assert check.snapshot_drifts[0].revision_anchor_overlap == []
    assert "does not touch staged patch subjects" in (
        check.snapshot_drifts[0].note
    )
    assert "weak relevance hint" in check.snapshot_drifts[0].note
    stale_description = db.describe_staged_revision(
        staged.revision_iri,
        include_current_apply_check=True,
    )
    assert stale_description.current_apply_check is not None
    stale_summary = stale_description.current_apply_check
    assert stale_summary.status == "conflict"
    assert stale_summary.decision == "restage_against_current_graph"
    assert stale_summary.blocking_reasons == ["target_count_drift"]
    assert stale_summary.validation_skipped_reason == "conflicts_present"
    assert stale_summary.effective_delta_summary is not None
    assert stale_summary.effective_delta_summary.blocked_patch_triples_to_add == 1
    assert stale_summary.effective_delta_summary.basis == (
        "conflicted_patches_excluded"
    )
    assert stale_summary.next_action is not None
    assert stale_summary.next_action.action_type == "restage_after_review"
    assert stale_summary.next_action.queue == "restage_after_review"
    assert stale_summary.next_action.arguments == {
        "revision_iris": staged.revision_iri
    }
    assert stale_summary.count_drifts[0].target_graph == "map"
    assert stale_summary.count_drifts[0].count_basis == "target_graph_only"
    assert stale_summary.snapshot_drifts[0].exact_changed_triples_available is True
    assert stale_summary.snapshot_drifts[0].exact_changed_triples_included is False
    assert stale_summary.snapshot_drifts[0].triples_added_since_snapshot == []

    export_path = tmp_path / "stale-staged-review.md"
    db.export_staged_revision(staged.revision_iri, export_path)
    export_text = export_path.read_text(encoding="utf-8")

    assert "## Current Apply Check" in export_text
    assert "- Status: conflict" in export_text
    assert "- Decision: restage_against_current_graph" in export_text
    assert "- Mechanically can apply: False" in export_text
    assert "- Replayable triple delta: +0, -0 (conflicted patches excluded)" in (
        export_text
    )
    assert (
        "- Patch replay note: conflicted patch triples are shown in Patch Replay; "
        "replayable delta excludes them."
    ) in export_text
    assert "- Blocking reasons: target_count_drift" in export_text
    assert "- Validation skipped: conflicts_present" in export_text
    assert "### Count Drift" in export_text
    assert (
        "| Patch | Sequence | Graph | Expected before | Count basis | "
        "Expected basis | Current | Delta |"
    ) in export_text
    assert "target_graph_only" in export_text
    assert "original staged graph snapshot before patch 1" in export_text
    assert "### Snapshot Drift" in export_text
    assert "#### Snapshot Drift Triples: map" in export_text
    assert "Added since snapshot" in export_text
    assert (
        "| Patch | Graph | Operation | Recorded preview before | "
        "Count basis | Current preview before | Recorded preview after | "
        "Current preview | Effective + | Effective - | Already present | "
        "Already absent | Mechanically can apply | Conflict |"
    ) in export_text
    assert "| map | 0 |" in export_text
    assert f"| 0 | {db.triple_count('map')} |" in export_text
    assert "all_patch_triples_absent" in export_text
    assert "### Suggested Next Actions" in export_text
    assert "**doxabase.restage_staged_revision**" in export_text
    assert "Create a refreshed staged revision" in export_text
    assert "expected 0 triples before patch" in check.conflicts[0]
    assert check.patch_checks[0].can_apply is False
    assert check.suggested_next_actions[0].tool == "doxabase.describe_staged_revision"
    assert check.suggested_next_actions[0].args == {
        "iri": staged.revision_iri,
        "include_current_apply_check": True,
    }
    assert check.suggested_next_actions[-1].tool == "doxabase.restage_staged_revision"
    assert check.next_action is not None
    assert check.next_action.action_type == "restage_after_review"
    assert check.next_action.queue == "restage_after_review"
    assert check.next_action.tool_name == "restage_staged_revision"
    assert check.next_action.arguments == {
        "revision_iris": staged.revision_iri
    }

    with pytest.raises(DoxaBaseError, match="Staged revision cannot be applied"):
        db.apply_staged_revision(staged.revision_iri)

    with pytest.raises(DoxaBaseError, match="Messages"):
        db.describe_dataset("https://example.test/project#Messages")


def test_staged_review_decision_refuses_ready_mutation_target_by_default(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = db.stage_graph_revision(
        summary="Stage messages dataset",
        rationale="Exercise explicit review resolution override.",
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

    with pytest.raises(DoxaBaseError, match="current mutation-target row"):
        db.record_staged_revision_review_decision(
            staged.revision_iri,
            decision="discarded",
            rationale="Reviewer decided not to keep this ready proposal.",
        )

    resolution = db.record_staged_revision_review_decision(
        staged.revision_iri,
        decision="discarded",
        rationale="Reviewer explicitly decided not to keep this ready proposal.",
        allow_mutation_target=True,
    )

    assert resolution.current_application_status == "ready"
    assert resolution.closes_current_staged_work is True
    current_work = db.list_graph_revisions(
        revision_type="rc:StagedRevision",
        current_staged_work_only=True,
    )
    assert current_work.count == 0

    with pytest.raises(DoxaBaseError, match="recorded review resolution"):
        db.apply_staged_revision(staged.revision_iri)

    with pytest.raises(DoxaBaseError, match="recorded review resolution"):
        db.stage_graph_revision(
            summary="Try repaired messages dataset",
            rationale="Should not restage a review-resolved source.",
            additions=[
                {
                    "graph": "map",
                    "content": """
                        @prefix ex: <https://example.test/project#> .
                        @prefix rc: <https://richcanopy.org/ns/rc#> .

                        ex:Messages a rc:Table .
                    """,
                }
            ],
            restages_revision=staged.revision_iri,
        )


def test_noop_successor_post_apply_recheck_reports_live_decision(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    source = db.stage_graph_revision(
        summary="Stage messages dataset",
        rationale="Exercise no-op successor after a sibling apply.",
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
        "https://example.test/project#Messages",
        label="Messages",
    )
    db.record_map_dataset(
        "https://example.test/project#OtherDataset",
        label="Other dataset",
    )
    noop_successor = db.stage_graph_revision(
        summary="Authored no-op successor",
        rationale=(
            "Preserve the old already-realized framing as an authored successor "
            "without using mechanical restage."
        ),
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
        restages_revision=source.revision_iri,
    )
    noop_check = db.check_staged_revision_apply(noop_successor.revision_iri)
    assert noop_check.status == "noop"
    assert noop_check.decision == "inspect_no_effective_change"
    assert noop_check.routing_decision == "inspect_no_effective_change"
    assert noop_check.blocking_reasons == ["no_effective_patch_triples"]

    sibling = db.stage_graph_revision(
        summary="Stage shipments dataset",
        rationale="Applying this sibling should make the no-op successor stale.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Shipments a rc:Dataset .
                """,
            }
        ],
    )

    applied = db.apply_staged_revision(sibling.revision_iri)

    assert noop_successor.revision_iri in applied.post_apply_recheck_revision_iris
    recheck = next(
        item
        for item in applied.post_apply_recheck_revisions
        if item.iri == noop_successor.revision_iri
    )
    assert recheck.application_status == "conflict"
    assert recheck.decision == "restage_against_current_graph"
    assert recheck.routing_decision == "inspect_no_effective_change"
    assert "target_count_drift" in recheck.blocking_reasons
    assert recheck.next_action is not None
    assert recheck.next_action.action_type == "inspect_no_effective_change"
    assert recheck.next_action.queue == "informational"
    assert recheck.next_action.tool_name == "describe_staged_revision"
    assert recheck.next_action.arguments == {
        "iri": noop_successor.revision_iri,
        "include_current_apply_check": True,
    }

    with pytest.raises(DoxaBaseError, match="already-effective stale source"):
        db.restage_staged_revision(noop_successor.revision_iri)


def test_post_apply_recheck_preserves_staged_validation_repair_signal(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    invalid = db.stage_graph_revision(
        summary="Invalid row semantics",
        rationale="Staged-time validation failure should survive later drift.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders a rc:Dataset, rc:Table ;
                        rc:rowSemantics rc:EventRow, rc:SnapshotRow .
                """,
            }
        ],
        validation_scope="all",
    )
    ready = db.stage_graph_revision(
        summary="Ready sibling",
        rationale="Applying this sibling will make the invalid row stale.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Shipments a rc:Dataset .
                """,
            }
        ],
        validation_scope="all",
    )

    invalid_check = db.check_staged_revision_apply(invalid.revision_iri)

    assert invalid_check.status == "validation_failed"
    assert invalid_check.next_action is not None
    assert invalid_check.next_action.queue == "repair_or_replace"

    applied = db.apply_staged_revision(ready.revision_iri)
    recheck = next(
        item
        for item in applied.post_apply_recheck_revisions
        if item.iri == invalid.revision_iri
    )

    assert recheck.application_status == "conflict"
    assert recheck.decision == "restage_against_current_graph"
    assert recheck.recheck_reasons == ["shared_changed_graph:map"]
    assert recheck.next_action is not None
    assert recheck.next_action.action_type == "repair_or_replace"
    assert recheck.next_action.queue == "repair_or_replace"
    assert recheck.next_action.tool_name == "restage_staged_revision"
    assert recheck.next_action.arguments.get("dry_run") is True


def test_post_apply_recheck_includes_validation_dependency_drift(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    map_revision = db.stage_graph_revision(
        summary="Stage unlabeled dataset",
        rationale="This candidate is ready before the project shape tightens.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders a rc:Dataset .
                """,
            }
        ],
        validation_scope="all",
    )
    shape_revision = db.stage_graph_revision(
        summary="Require dataset labels",
        rationale="Project validation should force map candidates back to review.",
        additions=[
            {
                "graph": "shapes",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
                    @prefix sh: <http://www.w3.org/ns/shacl#> .

                    ex:DatasetLabelShape a sh:NodeShape ;
                        sh:targetClass rc:Dataset ;
                        sh:property [
                            sh:path rdfs:label ;
                            sh:minCount 1 ;
                            sh:message "Datasets need labels."
                        ] .
                """,
            }
        ],
        validation_scope="all",
    )

    assert db.check_staged_revision_apply(map_revision.revision_iri).status == "ready"
    assert db.check_staged_revision_apply(shape_revision.revision_iri).status == "ready"

    applied = db.apply_staged_revision(shape_revision.revision_iri)
    recheck = next(
        item
        for item in applied.post_apply_recheck_revisions
        if item.iri == map_revision.revision_iri
    )

    assert map_revision.revision_iri in applied.post_apply_recheck_revision_iris
    assert recheck.shared_changed_graphs == []
    assert recheck.recheck_reasons == ["validation_dependency_graph:shapes"]
    assert recheck.application_status == "validation_failed"
    assert recheck.decision == "inspect_validation_results"
    assert recheck.blocking_reasons == ["validation_failed"]
    assert recheck.next_action is not None
    assert recheck.next_action.queue == "repair_or_replace"


def test_batch_restage_preserves_order_and_exports_review_bundle(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    first = db.stage_graph_revision(
        summary="Stage order events table",
        rationale="Keep the raw order event framing available for review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:OrderEvents a rc:Dataset .
                """,
            }
        ],
    )
    second = db.stage_graph_revision(
        summary="Stage order lifecycle table",
        rationale="Keep the lifecycle framing available for review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:OrderLifecycle a rc:Dataset .
                """,
            }
        ],
    )
    db.record_map_dataset(
        "https://example.test/project#DriftDataset",
        label="Drift dataset",
    )
    already_restaged = db.restage_staged_revision(first.revision_iri)
    ready = db.stage_graph_revision(
        summary="Stage current shipment table",
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

    export_path = tmp_path / "batch-restage-review.md"
    batch = db.restage_staged_revisions(
        [first.revision_iri, second.revision_iri, ready.revision_iri],
        path=export_path,
        title="Batch restage review",
    )
    restaged_second = batch.restaged_revision_iris[0]

    assert batch.dry_run is False
    assert batch.would_restage_revision_iris == []
    assert [item.action for item in batch.items] == [
        "skipped_already_handled",
        "restaged",
        "skipped_not_restageable",
    ]
    assert batch.restaged_revision_by_source == {
        second.revision_iri: restaged_second
    }
    assert batch.current_revision_by_source == {
        first.revision_iri: already_restaged.revision_iri,
        second.revision_iri: restaged_second,
        ready.revision_iri: ready.revision_iri,
    }
    assert batch.skipped_revision_iris == [first.revision_iri, ready.revision_iri]
    assert batch.already_handled_revision_iris == [first.revision_iri]
    assert batch.not_restageable_revision_iris == [ready.revision_iri]
    assert batch.not_restageable_revision_iris_by_reason == {
        "ready": [ready.revision_iri],
    }
    assert batch.items[1].status_after == "ready"
    assert batch.items[1].decision_after == "review_then_apply"
    assert batch.items[1].stale_resolution_state_after == "restaged_successor_ready"
    assert batch.items[1].blocking_reasons_after == []
    assert batch.items[1].source_snapshot_evidence.status == (
        "history_plus_snapshot_rows"
    )
    assert batch.items[1].source_snapshot_evidence_completeness == "complete"
    assert batch.items[1].current_snapshot_evidence.revision_iri == restaged_second
    assert batch.items[1].current_snapshot_evidence.status == (
        "history_plus_snapshot_rows"
    )
    assert batch.items[1].current_snapshot_evidence_completeness == "complete"
    assert batch.items[1].triples_to_add_after > 0
    assert batch.items[1].triples_to_remove_after == 0
    assert batch.items[0].next_action_after is not None
    assert batch.items[0].next_action_after.action_type == "apply_after_review"
    assert batch.items[0].next_action_after.arguments == {
        "iri": already_restaged.revision_iri
    }
    assert batch.items[0].next_action_queue_item_after is not None
    assert batch.items[0].next_action_queue_item_after.row_iri == (
        already_restaged.revision_iri
    )
    assert batch.items[0].next_action_queue_item_after.resolved_target_iri == (
        already_restaged.revision_iri
    )
    assert batch.items[0].next_action_queue_item_after.row_is_target is True
    assert batch.items[0].next_action_queue_item_after.record_kind == "staged_patch"
    assert (
        batch.items[0].next_action_queue_item_after.resolved_target_record_kind
        == "staged_patch"
    )
    assert batch.items[1].next_action_after is not None
    assert batch.items[1].next_action_after.action_type == "apply_after_review"
    assert batch.items[1].next_action_after.arguments == {"iri": restaged_second}
    assert batch.items[1].next_action_queue_item_after is not None
    assert batch.items[1].next_action_queue_item_after.row_iri == restaged_second
    assert batch.items[1].next_action_queue_item_after.resolved_target_iri == (
        restaged_second
    )
    assert batch.items[1].suggested_next_actions_after[-1].tool == (
        "doxabase.apply_staged_revision"
    )
    assert batch.items[2].not_restageable_reason == "ready"
    assert batch.items[2].next_action_after is not None
    assert batch.items[2].next_action_after.action_type == "apply_after_review"
    assert batch.items[2].next_action_after.arguments == {"iri": ready.revision_iri}
    assert batch.items[2].next_action_queue_item_after is not None
    assert batch.items[2].next_action_queue_item_after.row_iri == ready.revision_iri
    assert batch.review_revision_iris == [
        first.revision_iri,
        already_restaged.revision_iri,
        second.revision_iri,
        restaged_second,
        ready.revision_iri,
    ]
    assert batch.export_record is not None
    assert batch.export_record.path == str(export_path)
    assert batch.export_record.revision_iris == batch.review_revision_iris
    assert batch.bundle_summary.apply_status_counts == {
        "conflict": 2,
        "ready": 3,
    }
    assert batch.bundle_summary.stale_resolution_state_counts == {
        "stale_handled_by_restage": 2,
        "restaged_successor_ready": 2,
        "ready": 1,
    }
    assert batch.bundle_summary.unresolved_stale_revision_iris == []
    assert batch.bundle_summary.ready_restage_successor_revision_iris == [
        already_restaged.revision_iri,
        restaged_second,
    ]
    assert batch.bundle_summary.post_apply_recheck_revision_iris == [
        already_restaged.revision_iri,
        restaged_second,
        ready.revision_iri,
    ]
    assert batch.requires_recheck_after_each_apply is True
    assert batch.sequential_apply_recheck_candidate_iris == [
        already_restaged.revision_iri,
        restaged_second,
        ready.revision_iri,
    ]
    assert len(batch.bundle_summary.warnings) == 1
    assert batch.bundle_summary.recommended_mutation_review_iris == [
        already_restaged.revision_iri,
        restaged_second,
        ready.revision_iri,
    ]
    assert batch.bundle_summary.recommended_apply_or_restage_review_iris == [
        already_restaged.revision_iri,
        restaged_second,
        ready.revision_iri,
    ]
    assert batch.bundle_summary.recommended_repair_review_iris == []
    exported = export_path.read_text(encoding="utf-8")
    assert exported.startswith("# Batch restage review\n")
    assert "## Bundle Warnings" in exported
    assert "## Review Queues" in exported
    assert "- Apply/restage review: " in exported
    assert "- Repair review: (none)" in exported
    assert "- Sequential apply recheck candidates: " in exported
    assert "## Restage Context" in exported
    assert exported.index("## Review Queues") < exported.index("## Restage Context")
    assert "Stage order lifecycle table" in exported
    assert db.check_staged_revision_apply(restaged_second).status == "ready"

    db.apply_staged_revision(already_restaged.revision_iri)
    ready_after_apply = db.check_staged_revision_apply(ready.revision_iri)
    assert ready_after_apply.status == "conflict"
    assert "target_count_drift" in ready_after_apply.blocking_reasons


def test_post_apply_recheck_subset_does_not_replace_current_work_plan(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    first_map = db.stage_graph_revision(
        summary="Stage alpha dataset",
        rationale="First map sibling for post-apply recheck routing.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Alpha a rc:Dataset ;
                        rdfs:label "Alpha" .
                """,
            }
        ],
    )
    second_map = db.stage_graph_revision(
        summary="Stage beta dataset",
        rationale="Second map sibling that should be rechecked after alpha.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Beta a rc:Dataset ;
                        rdfs:label "Beta" .
                """,
            }
        ],
    )
    ontology_revision = db.stage_graph_revision(
        summary="Stage project ticket concept",
        rationale="Independent ontology sibling in the same staged frontier.",
        additions=[
            {
                "graph": "ontology",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:ProjectTicketConcept a rdfs:Class ;
                        rdfs:subClassOf rc:Concept ;
                        rdfs:label "Project ticket concept" .
                """,
            }
        ],
        validation_scope="ontology",
    )

    initial_plan = db.plan_staged_revision_recovery()

    assert initial_plan.requires_recheck_after_each_apply is True
    assert set(initial_plan.mutation_frontier_iris) == {
        first_map.revision_iri,
        second_map.revision_iri,
        ontology_revision.revision_iri,
    }
    assert set(initial_plan.sequential_apply_recheck_candidate_iris) == {
        first_map.revision_iri,
        second_map.revision_iri,
    }

    applied = db.apply_staged_revision(first_map.revision_iri)

    assert applied.post_apply_recheck_revision_iris == [second_map.revision_iri]
    assert ontology_revision.revision_iri not in (
        applied.post_apply_recheck_revision_iris
    )
    assert applied.post_apply_recheck_is_partial_queue is True
    assert applied.suggested_next_actions[0].tool == (
        "doxabase.plan_staged_revision_recovery"
    )
    assert applied.suggested_next_actions[0].args == {
        "current_staged_work_only": True
    }
    assert applied.suggested_next_actions[0].reason.startswith(
        "Post-apply recheck rows are only the affected sibling subset."
    )
    assert any(
        action.tool == "doxabase.restage_staged_revision"
        and action.args == {"revision_iris": second_map.revision_iri}
        for action in applied.suggested_next_actions
    )

    followup_plan = db.plan_staged_revision_recovery()

    assert followup_plan.total_count == 2
    assert followup_plan.next_action_queue == {
        "apply_after_review": [ontology_revision.revision_iri],
        "restage_after_review": [second_map.revision_iri],
    }
    assert set(followup_plan.mutation_frontier_iris) == {
        second_map.revision_iri,
        ontology_revision.revision_iri,
    }
    assert followup_plan.requires_recheck_after_each_apply is False


def test_export_profile_insight_review_bundle_discovers_related_staged_revisions(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/profile-review#SupportEvents"
    status_column = "https://example.test/profile-review#SupportEventsState"
    evidence = "https://example.test/profile-review#SupportEventsProfileEvidence"
    metric = "https://example.test/profile-review#WorkflowFlipRate"
    caveat = "https://example.test/profile-review#WorkflowFlipRateCaveat"
    fake_secret = "FAKE_SECRET_DO_NOT_USE_PROFILE"
    secret_text = f"Bearer {fake_secret}"

    db.record_map_dataset(
        dataset,
        label="Support Events",
        is_table=True,
        row_count_snapshot=8,
        path_templates=["support/events/*.parquet"],
    )
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="workflow_state",
        nullable=False,
    )
    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Support Events were profiled with a full-table scan.",
        evidence_summary="Synthetic profile run for profile insight review.",
        evidence_sources=["test://support-events-profile"],
        shared_evidence_iri=evidence,
        sample_size=10,
        sample_scope="All rows in the Support Events table.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=10,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": metric,
                "target": dataset,
                "value": "0.217",
                "datatype": "xsd:decimal",
            }
        ],
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "workflow_state",
                "summary": "Workflow state had nulls in the full scan.",
                "null_count": 1,
                "distinct_count": 4,
                "physical_type": "rc:Varchar",
            }
        ],
    )
    related_pattern = db.record_pattern(
        summary="Workflow flip rate needs scoped review.",
        pattern_text=(
            "Workflow flip rate is useful only when replay and backfill rows "
            "are scoped out of the denominator."
        ),
        rationale=(
            "The same profile evidence supports map drift review, metric "
            "vocabulary review, and a caveat alternative."
        ),
        pattern_targets=[dataset, metric],
        supporting_observations=bundle.handoff_entrypoints.profile_observation_iris,
        evidence_iri=evidence,
        map_implications=[metric, caveat],
    )
    unrelated_pattern = db.record_pattern(
        summary="Unrelated same-evidence note.",
        pattern_text="This note intentionally shares evidence but targets refunds.",
        rationale="It should not make unrelated staged work part of the bundle.",
        pattern_targets=["https://example.test/profile-review#Refunds"],
        evidence_iri=evidence,
        map_implications=["https://example.test/profile-review#RefundReason"],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)
    query_context_action = draft.suggested_next_action_groups[
        "query_context_review"
    ][0]
    query_route_key = next(
        source["route_group_key"]
        for source in db._profile_insight_route_sources(draft)
        if source["review_lane"] == "query_context_review"
    )
    profile_map_route_key = next(
        source["route_group_key"]
        for source in db._profile_insight_route_sources(draft)
        if source["review_lane"] == "profile_map_updates"
    )
    staged_map = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[0, 1],
        supporting_patterns=[related_pattern.pattern_iri],
    )
    promotion_action = next(
        action
        for action in draft.suggested_next_action_groups["metric_vocabulary_review"]
        if (action.tool, action.args.get("kind")) == ("doxabase.stage_revision", "pattern_promotion")
    )
    metric_route_key = promotion_action.args["spec"][
        "profile_route_sources"
    ][0]["route_group_key"]
    metric_promotion = db.stage_pattern_promotion(
        **promotion_action.args["spec"]
    )
    assert metric_promotion.profile_route_source_count == 1
    storage_access = "https://example.test/profile-review#SupportEventsStorage"
    query_repair_draft = db.stage_systematisation(
        summary="Review Support Events storage access",
        intent="Keep the query-context blocker repair reviewable beside profile-derived map updates.",
        rationale=(
            "The profile draft routed agents through query_context_review before "
            "using profile-derived map updates as query-planning context."
        ),
        anchors=[dataset, storage_access],
        profile_route_sources=[
            next(
                source
                for source in db._profile_insight_route_sources(draft)
                if source["review_lane"] == "query_context_review"
            )
        ],
        framings=[
            {
                "label": "Map storage access",
                "graph": "map",
                "content": f"""
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    <{dataset}> rc:hasStorageAccess <{storage_access}> .

                    <{storage_access}> a rc:StorageAccess ;
                        rc:storageProtocol rc:LocalFilesystemStorage ;
                        rc:storageRoot "/tmp/support-events.parquet" .
                """,
            }
        ],
        validation_scope="all",
    )
    assert query_repair_draft.profile_route_source_count == 1
    caveat_draft = db.stage_systematisation(
        summary="Review workflow flip caveat",
        intent="Keep the denominator caveat reviewable beside profile map updates.",
        rationale=(
            "The caveat is profile-derived but should remain a staged semantic "
            "choice rather than being hidden in the row-count update."
        ),
        anchors=[dataset, metric, caveat],
        supporting_observations=bundle.handoff_entrypoints.profile_observation_iris,
        supporting_patterns=[related_pattern.pattern_iri],
        evidence=[evidence],
        framings=[
            {
                "label": "Map caveat",
                "graph": "map",
                "content": f"""
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    <{caveat}> a rc:KnownCaveat ;
                        rdfs:label "Workflow flip denominator caveat" ;
                        rc:caveatDescription "Workflow flip rate excludes replay and backfill rows. Scratch credential paste: {secret_text}" .

                    <{dataset}> rc:hasKnownCaveat <{caveat}> .
                """,
            }
        ],
        validation_scope="all",
    )
    unrelated_draft = db.stage_systematisation(
        summary="Unrelated refunds review",
        intent="Provide an unrelated same-evidence staged row.",
        rationale="This row shares no profile-derived anchors or related pattern.",
        supporting_patterns=[unrelated_pattern.pattern_iri],
        framings=[
            {
                "label": "Refund note",
                "graph": "patterns",
                "content": """
                    @prefix ex: <https://example.test/profile-review#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:RefundReviewPattern a rc:Pattern ;
                        rc:summary "Refunds need separate review." ;
                        rc:patternText "Refunds are not part of the support event profile insight." ;
                        rc:rationale "Synthetic unrelated row." ;
                        rc:patternTarget ex:Refunds .
                """,
            }
        ],
        validation_scope="all",
    )

    export_path = tmp_path / "profile-insight-review.md"
    result = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        export_path,
    )

    expected_revision_iris = {
        staged_map.staged_revision.revision_iri,
        metric_promotion.staged_revisions[0].revision_iri,
        query_repair_draft.staged_revisions[0].revision_iri,
        caveat_draft.staged_revisions[0].revision_iri,
    }
    assert set(result.candidate_revision_iris) == expected_revision_iris
    assert unrelated_draft.staged_revisions[0].revision_iri not in (
        result.candidate_revision_iris
    )
    assert result.candidate_count == 4
    assert result.export is not None
    assert set(result.export.revision_iris) == expected_revision_iris
    candidates_by_iri = {
        candidate.revision_iri: candidate for candidate in result.candidates
    }
    assert profile_map_route_key in candidates_by_iri[
        staged_map.staged_revision.revision_iri
    ].profile_route_keys
    map_route_groups = {
        group["review_lane"]: group
        for group in candidates_by_iri[
            staged_map.staged_revision.revision_iri
        ].profile_route_groups
    }
    assert map_route_groups["profile_map_updates"]["match_strength"] == (
        "direct_action"
    )
    assert map_route_groups["metric_vocabulary_review"]["match_strength"] == (
        "strong_support"
    )
    assert metric_route_key in candidates_by_iri[
        metric_promotion.staged_revisions[0].revision_iri
    ].profile_route_keys
    metric_route_groups = {
        group["review_lane"]: group
        for group in candidates_by_iri[
            metric_promotion.staged_revisions[0].revision_iri
        ].profile_route_groups
    }
    assert metric_route_groups["metric_vocabulary_review"]["match_strength"] == (
        "direct_action"
    )
    assert metric_route_groups["profile_map_updates"]["match_strength"] == (
        "strong_support"
    )
    assert query_route_key in candidates_by_iri[
        query_repair_draft.staged_revisions[0].revision_iri
    ].profile_route_keys
    query_route_groups = {
        group["review_lane"]: group
        for group in candidates_by_iri[
            query_repair_draft.staged_revisions[0].revision_iri
        ].profile_route_groups
    }
    assert query_route_groups["query_context_review"]["match_strength"] == (
        "direct_action"
    )
    assert all(
        group["route_step_keys"]
        for candidate in result.candidates
        for group in candidate.profile_route_groups
    )
    assert result.artifact_kind == "profile_insight_review_bundle"
    assert result.importable is False
    assert result.recommended_import_tool is None
    assert result.recovery_complete is False
    assert result.export is not None
    assert result.export.artifact_kind == "staged_revisions_review_markdown"
    assert result.export.importable is False
    assert result.export.recommended_import_tool is None
    assert result.export.recovery_complete is False
    assert result.export.sensitive_literal_count == 1
    assert result.export.shareability_review_required is True
    assert result.export.shareability_review_status == "required_not_completed"
    assert result.export.privacy_warnings
    assert fake_secret not in " ".join(result.export.privacy_warnings)
    assert related_pattern.pattern_iri in result.related_pattern_iris
    assert unrelated_pattern.pattern_iri not in result.related_pattern_iris
    assert all(candidate.relation_reasons for candidate in result.candidates)
    assert any(
        "supporting_profile_observation" in candidate.relation_reasons
        for candidate in result.candidates
    )
    assert export_path.exists()
    exported = export_path.read_text(encoding="utf-8")
    assert "Profile insight review: Support Events" in exported
    assert "## Privacy Warning" in exported
    assert "## Reviewer Decision Matrix" in exported
    assert "### Profile Route Bridge" in exported
    assert (
        "| Row | Candidate | Revision | Profile route keys | Review lanes | Matched by |"
        in exported
    )
    for row_number, candidate in enumerate(result.candidates, start=1):
        if not candidate.profile_route_groups:
            continue
        assert f"| {row_number} | {candidate.summary} |" in exported
        assert f"## Revision {row_number}: {candidate.summary}" in exported
    assert profile_map_route_key in exported
    assert metric_route_key in exported
    assert query_route_key in exported
    assert "profile_map_updates (direct_action)" in exported
    assert "metric_vocabulary_review (direct_action)" in exported
    assert "profile_map_updates (strong_support)" in exported
    assert "metric_vocabulary_review (strong_support)" in exported
    secret_line = _line_number_containing(exported, secret_text)
    assert f"line {secret_line} " in " ".join(result.export.privacy_warnings)
    assert "Workflow flip denominator caveat" in exported
    assert secret_text in exported
    assert "WorkflowFlipRate" in exported

    blocked_profile_path = tmp_path / "blocked-profile-insight-review.md"
    with pytest.raises(DoxaBaseError, match="fail_on_sensitive=True"):
        db.export_profile_insight_review_bundle(
            dataset,
            evidence,
            blocked_profile_path,
            fail_on_sensitive=True,
        )
    assert not blocked_profile_path.exists()


def test_profile_insight_review_bundle_reuses_apply_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/profile-cache#Orders"
    evidence = "https://example.test/profile-cache#OrdersProfileEvidence"
    staged_note = "https://example.test/profile-cache#OrdersReviewNote"

    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=10,
    )
    db.record_dataset_profile(
        dataset,
        summary="Orders profile pass.",
        evidence_summary="Synthetic profile output.",
        evidence_sources=["test://orders-profile"],
        evidence_iri=evidence,
        sample_size=10,
        sample_scope="All rows in the local Orders table.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=10,
        update_map_snapshot=False,
    )
    staged = db.stage_graph_revision(
        summary="Add Orders profile review note",
        rationale="Keep a profile-derived review note near the evidence.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    <{staged_note}> rdfs:comment "Profile-derived review note." .
                """,
            }
        ],
        evidence=[evidence],
    )

    validate_preview_call_count = 0
    original_validate_graph_preview = db._validate_graph_preview

    def counted_validate_graph_preview(*args: object, **kwargs: object) -> object:
        nonlocal validate_preview_call_count
        validate_preview_call_count += 1
        return original_validate_graph_preview(*args, **kwargs)

    monkeypatch.setattr(db, "_validate_graph_preview", counted_validate_graph_preview)

    result = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        tmp_path / "profile-insight-review.md",
    )

    assert result.candidate_revision_iris == [staged.revision_iri]
    assert validate_preview_call_count == 1


def test_profile_insight_review_bundle_marks_plain_map_update_safe_single(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/profile-gate#Orders"
    evidence = "https://example.test/profile-gate#OrdersProfileEvidence"

    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=10,
    )
    db.record_dataset_profile(
        dataset,
        summary="Orders profile found a row-count drift.",
        evidence_summary="Synthetic full-table profile output.",
        evidence_sources=["test://orders-profile"],
        evidence_iri=evidence,
        sample_size=12,
        sample_scope="All rows in the local Orders table.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=12,
        update_map_snapshot=False,
    )
    staged = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[0],
    )

    result = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        tmp_path / "profile-insight-map-only-review.md",
    )

    assert result.bulk_apply_allowed is True
    assert result.safe_single_apply_candidate_revision_iris == [
        staged.staged_revision.revision_iri
    ]
    assert result.semantic_apply_gate_counts["safe_single_apply_candidates"] == 1
    assert result.semantic_apply_gate_blocking_reasons == []
    assert result.executor_decision_summary["decision"] == (
        "bulk_apply_after_review"
    )
    assert result.executor_decision_summary["mutation_policy"] == (
        "bulk_apply_allowed_after_review"
    )
    assert result.executor_decision_summary[
        "safe_single_apply_candidate_revision_iris"
    ] == [staged.staged_revision.revision_iri]
    assert result.executor_decision_summary["open_review_lanes"] == []
    assert result.executor_decision_summary["candidate_roles"] == {
        "ordinary_profile_map_update": 1
    }
    candidate = result.candidates[0]
    assert candidate.semantic_apply_role == "ordinary_profile_map_update"
    assert candidate.apply_cardinality == "single_after_review"
    assert candidate.safe_single_apply_candidate is True
    assert candidate.bulk_apply_allowed is True
    exported = (tmp_path / "profile-insight-map-only-review.md").read_text(
        encoding="utf-8"
    )
    assert "### Semantic Apply Gate" in exported
    assert "Bulk application is mechanically allowed" in exported
    assert "Generic staged review queues below are mechanical" in exported
    assert "bulk_allowed_after_review" in exported
    assert "generic queues may be followed after profile review" in exported


def test_export_profile_insight_review_bundle_recovers_applied_profile_sources(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/profile-postapply#Payments"
    evidence = "https://example.test/profile-postapply#PaymentsProfileEvidence"
    caveat = "https://example.test/profile-postapply#PaymentsProfileCaveat"

    db.record_map_dataset(
        dataset,
        label="Payments",
        is_table=True,
        row_count_snapshot=8,
    )
    profile_bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Payments were profiled with a full-table scan.",
        evidence_summary="Synthetic profile run for post-apply recovery.",
        evidence_sources=["test://payments-profile"],
        shared_evidence_iri=evidence,
        sample_size=10,
        sample_scope="All rows in the Payments table.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=10,
        update_map_snapshot=False,
    )
    draft = db.draft_profile_map_updates(dataset, evidence)
    profile_map_route_key = next(
        source["route_group_key"]
        for source in db._profile_insight_route_sources(draft)
        if source["review_lane"] == "profile_map_updates"
    )
    staged_map = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[0],
    )
    applied_source_iri = staged_map.staged_revision.revision_iri

    db.apply_staged_revision(applied_source_iri)
    caveat_draft = db.stage_systematisation(
        summary="Review payments profile caveat",
        intent="Keep a post-apply profile caveat reviewable beside the applied map update.",
        rationale=(
            "The applied row-count update and the caveat both come from the same "
            "profile evidence."
        ),
        anchors=[dataset, caveat],
        supporting_observations=(
            profile_bundle.handoff_entrypoints.profile_observation_iris
        ),
        evidence=[evidence],
        framings=[
            {
                "label": "Map profile caveat",
                "graph": "map",
                "content": f"""
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    <{caveat}> a rc:KnownCaveat ;
                        rdfs:label "Payments profile caveat" ;
                        rc:caveatDescription "Payment profile row count needs settlement-lag review." .

                    <{dataset}> rc:hasKnownCaveat <{caveat}> .
                """,
            }
        ],
        validation_scope="all",
    )
    caveat_revision_iri = caveat_draft.staged_revisions[0].revision_iri

    export_path = tmp_path / "profile-postapply-review.md"
    result = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        export_path,
    )

    assert result.candidate_revision_iris == [
        caveat_revision_iri,
        applied_source_iri,
    ]
    applied_candidate = next(
        candidate
        for candidate in result.candidates
        if candidate.revision_iri == applied_source_iri
    )
    assert applied_candidate.explicit is False
    assert "shared_profile_evidence" in applied_candidate.relation_reasons
    assert "profile_derived_anchor" in applied_candidate.relation_reasons
    assert profile_map_route_key in applied_candidate.profile_route_keys
    route_groups_by_lane = {
        group["review_lane"]: group for group in applied_candidate.profile_route_groups
    }
    assert route_groups_by_lane["profile_map_updates"]["match_strength"] == (
        "direct_action"
    )
    assert applied_candidate.safe_single_apply_candidate is False
    assert applied_source_iri not in result.safe_single_apply_candidate_revision_iris
    assert result.export is not None
    assert result.export.revision_iris == result.candidate_revision_iris
    assert result.export.bundle_summary.recommended_applied_inspection_iris == [
        applied_source_iri
    ]
    exported = export_path.read_text(encoding="utf-8")
    applied_row_number = result.candidates.index(applied_candidate) + 1
    assert (
        "| Row | Candidate | Revision | Profile route keys | Review lanes | Matched by |"
        in exported
    )
    assert (
        f"| {applied_row_number} | {applied_candidate.summary} |"
        in exported
    )
    assert (
        f"## Revision {applied_row_number}: {applied_candidate.summary}"
        in exported
    )

    current_only = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        tmp_path / "profile-current-only-review.md",
        include_applied_staged_sources=False,
    )

    assert current_only.candidate_revision_iris == [caveat_revision_iri]


def test_profile_review_bundle_keeps_live_followup_routes_supportive(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/profile-followup#Payments"
    status_column = "https://example.test/profile-followup#PaymentsStatus"
    evidence = "https://example.test/profile-followup#PaymentsProfileEvidence"

    db.record_map_dataset(
        dataset,
        label="Payments",
        is_table=True,
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Payments were profiled with a full-table scan.",
        evidence_summary="Synthetic profile run with an unmapped nullable column.",
        evidence_sources=["test://payments-profile"],
        shared_evidence_iri=evidence,
        sample_size=10,
        sample_scope="All rows in the Payments table.",
        sample_method="DuckDB full-table aggregate profile.",
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status was profiled before being mapped.",
                "null_count": 2,
                "physical_type": "rc:Varchar",
            }
        ],
    )
    initial_draft = db.draft_profile_map_updates(dataset, evidence)
    initial_route_key = next(
        source["route_group_key"]
        for source in db._profile_insight_route_sources(initial_draft)
        if source["review_lane"] == "profile_map_updates"
    )
    staged = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[0],
    )
    assert staged.staged_revision is not None
    applied_source_iri = staged.staged_revision.revision_iri
    db.apply_staged_revision(applied_source_iri)

    followup_draft = db.draft_profile_map_updates(dataset, evidence)
    followup_route_key = next(
        source["route_group_key"]
        for source in db._profile_insight_route_sources(followup_draft)
        if source["review_lane"] == "profile_map_updates"
    )
    assert followup_route_key != initial_route_key
    assert followup_draft.recommendations[0].kind == "column_nullable"

    export_path = tmp_path / "profile-followup-review.md"
    result = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        export_path,
    )

    assert result.candidate_revision_iris == [applied_source_iri]
    applied_candidate = result.candidates[0]
    route_groups_by_key = {
        group["route_group_key"]: group
        for group in applied_candidate.profile_route_groups
    }
    assert route_groups_by_key[initial_route_key]["match_strength"] == (
        "direct_action"
    )
    assert route_groups_by_key[followup_route_key]["match_strength"] == (
        "strong_support"
    )
    exported = export_path.read_text(encoding="utf-8")
    assert initial_route_key in exported
    assert followup_route_key in exported
    assert "profile_map_updates (direct_action)" in exported
    assert "profile_map_updates (strong_support)" in exported


def test_export_profile_insight_review_bundle_recovers_applied_query_repair_route(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/profile-query-postapply#Messages"
    evidence = "https://example.test/profile-query-postapply#MessagesProfileEvidence"
    storage_iri = "https://example.test/profile-query-postapply#MessagesStorage"
    layout_iri = "https://example.test/profile-query-postapply#MessagesLayout"

    db.record_map_dataset(
        dataset,
        label="Messages",
        is_table=True,
        path_templates=["messages/*.parquet"],
    )
    db.record_map_physical_layout(
        layout_iri,
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByListingLayout",
        datasets=[dataset],
    )
    storage = db.record_map_storage_access(
        storage_iri,
        label="Messages storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(tmp_path / "warehouse"),
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Messages were profiled with a full-table scan.",
        evidence_summary="Synthetic profile run for applied query-repair recovery.",
        evidence_sources=["test://messages-profile"],
        shared_evidence_iri=evidence,
        sample_size=10,
        sample_scope="All rows in the Messages table.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=10,
        update_map_snapshot=False,
    )

    draft = db.draft_profile_map_updates(dataset, evidence)
    query_route_key = next(
        source["route_group_key"]
        for source in db._profile_insight_route_sources(draft)
        if source["review_lane"] == "query_context_review"
    )
    assert query_route_key.startswith("query_context_review:")
    context = db.describe_query_context(dataset)
    missing_storage = next(
        issue for issue in context.issues if issue.code == "missing_storage_access"
    )
    link_action = next(
        action
        for action in missing_storage.details["repair_hint"]["actions"]
        if action["action_type"] == "stage_existing_storage_access_link"
    )
    arguments = dict(link_action["arguments_template"]["spec"])
    arguments["object"] = storage.iri
    arguments["rationale"] = "Reviewed the Messages storage access for this profile."
    query_repair = db.stage_map_assertion_change(**arguments)

    db.apply_staged_revision(query_repair.revision_iri)

    post_apply_draft = db.draft_profile_map_updates(dataset, evidence)
    assert "query_context_review" not in post_apply_draft.suggested_next_action_groups

    result = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        tmp_path / "profile-query-postapply-review.md",
        include_current_staged_work=False,
        include_applied_staged_sources=True,
    )

    assert result.candidate_revision_iris == [query_repair.revision_iri]
    candidate = result.candidates[0]
    assert candidate.explicit is False
    assert "profile_derived_anchor" in candidate.relation_reasons
    route_groups_by_lane = {
        group["review_lane"]: group for group in candidate.profile_route_groups
    }
    assert route_groups_by_lane["query_context_review"]["match_strength"] == (
        "direct_action"
    )
    exported = (tmp_path / "profile-query-postapply-review.md").read_text(
        encoding="utf-8"
    )
    assert (
        "| Row | Candidate | Revision | Profile route keys | Review lanes | Matched by |"
        in exported
    )
    assert f"| 1 | {candidate.summary} |" in exported
    assert f"## Revision 1: {candidate.summary}" in exported
    assert "query_context_review (direct_action)" in exported

