"""Split from test_doxabase_core.py (distillation Phase 2); tests verbatim."""

from tests.core.support_core import *  # noqa: F401,F403


def test_import_handoff_bundle_gates_dirty_manifest_recovery_actions(
    tmp_path: Path,
) -> None:
    source = DoxaBase.create(tmp_path / "source.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_DIRTY_HANDOFF_IMPORT"
    source.record_map_storage_access(
        "https://example.test/project#orders_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=f"/tmp/{fake_secret}/orders",
    )
    staged = source.stage_graph_revision(
        summary=f"Stage dirty handoff receiver probe {fake_secret}",
        rationale="Create a recoverable staged row in a privacy-dirty handoff.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:DirtyHandoffImportProbe a rc:Dataset .
                """,
            }
        ],
    )
    trig_path = tmp_path / "dirty-project-handoff.trig"
    snapshot_path = tmp_path / "dirty-revision-snapshots.json"
    manifest_path = tmp_path / "dirty-handoff-manifest.json"
    exported = source.export_handoff_bundle(
        trig_path,
        snapshot_path,
        manifest_path=manifest_path,
        revision_iris=[staged.revision_iri],
    )
    assert exported.sensitive_literal_count > 0

    receiver = DoxaBase.create(tmp_path / "receiver.sqlite")
    dry_run = receiver.import_handoff_bundle(manifest_path, dry_run=True)

    assert dry_run.dry_run is True
    assert dry_run.trig_imported == {}
    assert dry_run.trig_total_imported == 0
    assert dry_run.revision_snapshots is None
    assert dry_run.recovery_plan is None
    assert dry_run.recovery_summary.recommended_next_step == (
        "review_handoff_privacy_before_recovery"
    )
    assert dry_run.recovery_summary.first_mutation_action is None
    assert dry_run.recovery_summary.first_safe_review_or_mutation_action is None
    assert dry_run.recovery_summary.first_safe_review_or_mutation_source is None
    assert dry_run.recovery_summary.first_suggested_next_action is not None
    assert dry_run.recovery_summary.first_suggested_next_action.tool == (
        "doxabase.import_handoff_bundle"
    )
    assert "non-mutating manifest privacy gate" in (
        dry_run.recovery_summary.note
    )
    assert "export_preflight" in (
        dry_run.recovery_summary.first_suggested_next_action.reason
    )
    assert [action.tool.removeprefix("doxabase.") for action in dry_run.suggested_next_actions] == [
        "import_handoff_bundle"
    ]
    assert fake_secret not in json.dumps(to_dict(dry_run))

    imported = receiver.import_handoff_bundle(manifest_path)

    assert imported.recovery_plan is not None
    assert imported.recovery_plan.processed_revision_iris == [staged.revision_iri]
    assert imported.suggested_next_actions
    assert [action.tool.removeprefix("doxabase.") for action in imported.suggested_next_actions] == [
        "export_preflight"
    ]
    privacy_action = imported.suggested_next_actions[0]
    assert privacy_action.args == {
        "export_kind": "handoff_bundle",
        "graphs": exported.graph_roles,
        "limit": 20,
        "revision_iris": [staged.revision_iri],
        "snapshot_graph_roles": exported.snapshot_graph_roles,
    }
    followup = receiver.export_preflight(**privacy_action.args)
    assert followup.sensitive_literal_count == exported.sensitive_literal_count
    assert followup.graph_sensitive_literal_count == (
        exported.graph_sensitive_literal_count
    )
    assert followup.snapshot_sensitive_literal_count == (
        exported.snapshot_sensitive_literal_count
    )
    assert imported.recovery_summary.recommended_next_step == (
        "review_handoff_privacy_before_recovery"
    )
    assert imported.recovery_summary.first_suggested_next_action == privacy_action
    assert (
        imported.recovery_summary.first_safe_review_or_mutation_action
        == privacy_action
    )
    assert imported.recovery_summary.first_safe_review_or_mutation_source == (
        "handoff_import_privacy_review"
    )
    assert imported.recovery_summary.first_mutation_action is None
    assert imported.recovery_summary.first_mutation_frontier_item is None
    assert imported.recovery_plan.mutation_allowed_after == (
        "handoff_import_privacy_review_required_before_recovery"
    )
    assert imported.recovery_plan.suggested_next_actions == [privacy_action]
    assert imported.recovery_plan.blocking_preflight_actions == [privacy_action]
    assert [
        step.step_kind
        for step in imported.recovery_plan.recommended_unattended_steps
    ] == ["review_handoff_privacy"]
    privacy_step = imported.recovery_plan.recommended_unattended_steps[0]
    assert privacy_step.action == privacy_action
    assert privacy_step.can_run_now is True
    assert privacy_step.mutates is False
    assert privacy_step.requires_replan_after_completion is True
    assert privacy_step.stop_reason == "rerun_plan_after_handoff_privacy_review"
    assert imported.recovery_plan.first_mutation_action is None
    assert (
        imported.recovery_plan.first_safe_review_or_mutation_action
        == privacy_action
    )
    assert (
        imported.recovery_plan.first_safe_review_or_mutation_source
        == "handoff_import_privacy_review"
    )
    assert imported.recovery_plan.mutation_frontier_iris == []
    assert imported.recovery_plan.mutation_frontier_items == []
    assert imported.recovery_plan.next_action_queue_items == []
    assert all(
        lane.next_action is None
        and lane.next_action_queue_item is None
        and lane.suggested_next_actions == [privacy_action]
        for lane in imported.recovery_plan.lanes
    )
    assert all(
        summary.next_action is None
        and summary.suggested_next_actions == [privacy_action]
        for summary in imported.recovery_plan.revision_summaries
    )
    assert "start_staged_revision_recovery_session" not in [
        action.tool.removeprefix("doxabase.") for action in imported.suggested_next_actions
    ]
    assert "apply_staged_revision" not in [
        action.tool.removeprefix("doxabase.") for action in imported.suggested_next_actions
    ]
    assert any(
        "potential sensitive terms" in warning
        for warning in imported.warnings
    )
    assert "apply_staged_revision" not in json.dumps(
        to_jsonable(imported.recovery_plan),
        sort_keys=True,
    )
    assert fake_secret not in json.dumps(to_dict(imported))


def test_import_handoff_bundle_gates_invalid_manifest_recovery_actions(
    tmp_path: Path,
) -> None:
    source = DoxaBase.create(tmp_path / "source.sqlite")
    source.import_trig(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rcg: <https://richcanopy.org/graph/> .

        rcg:observations {
            ex:obs_without_evidence a rc:Observation ;
                rc:summary "This observation intentionally keeps the handoff invalid." .
        }
        """
    )
    staged = source.stage_graph_revision(
        summary="Stage invalid diagnostic handoff receiver probe",
        rationale="Create a recoverable staged row in an invalid diagnostic handoff.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:InvalidHandoffImportProbe a rc:Dataset .
                """,
            }
        ],
    )
    trig_path = tmp_path / "invalid-project-handoff.trig"
    snapshot_path = tmp_path / "invalid-revision-snapshots.json"
    manifest_path = tmp_path / "invalid-handoff-manifest.json"
    exported = source.export_handoff_bundle(
        trig_path,
        snapshot_path,
        manifest_path=manifest_path,
        revision_iris=[staged.revision_iri],
        fail_on_invalid=False,
    )
    assert exported.would_block_invalid_export is True
    assert exported.validation_conforms is False

    receiver = DoxaBase.create(tmp_path / "receiver.sqlite")
    imported = receiver.import_handoff_bundle(manifest_path)

    assert imported.recovery_plan is not None
    assert imported.recovery_plan.processed_revision_iris == [staged.revision_iri]
    assert [action.tool.removeprefix("doxabase.") for action in imported.suggested_next_actions] == [
        "validate_graph"
    ]
    validation_action = imported.suggested_next_actions[0]
    assert validation_action.args == {
        "scope": "all",
        "limit_results": min(max(exported.validation_result_count, 20), 100),
    }
    followup = receiver.validate_graph(**validation_action.args)
    assert followup.conforms is False
    assert followup.result_count == exported.validation_result_count
    assert imported.recovery_summary.recommended_next_step == (
        "review_handoff_validation_before_recovery"
    )
    assert imported.recovery_summary.first_suggested_next_action == (
        validation_action
    )
    assert (
        imported.recovery_summary.first_safe_review_or_mutation_action
        == validation_action
    )
    assert imported.recovery_summary.first_safe_review_or_mutation_source == (
        "handoff_import_validation_review"
    )
    assert imported.recovery_summary.first_mutation_action is None
    assert imported.recovery_summary.first_mutation_frontier_item is None
    assert imported.recovery_plan.mutation_allowed_after == (
        "handoff_import_validation_review_required_before_recovery"
    )
    assert imported.recovery_plan.suggested_next_actions == [validation_action]
    assert imported.recovery_plan.blocking_preflight_actions == [validation_action]
    assert [
        step.step_kind
        for step in imported.recovery_plan.recommended_unattended_steps
    ] == ["review_handoff_validation"]
    validation_step = imported.recovery_plan.recommended_unattended_steps[0]
    assert validation_step.action == validation_action
    assert validation_step.can_run_now is True
    assert validation_step.mutates is False
    assert validation_step.requires_replan_after_completion is True
    assert validation_step.stop_reason == (
        "rerun_plan_after_handoff_validation_review"
    )
    assert imported.recovery_plan.first_mutation_action is None
    assert (
        imported.recovery_plan.first_safe_review_or_mutation_action
        == validation_action
    )
    assert imported.recovery_plan.first_safe_review_or_mutation_source == (
        "handoff_import_validation_review"
    )
    assert imported.recovery_plan.mutation_frontier_iris == []
    assert imported.recovery_plan.mutation_frontier_items == []
    assert imported.recovery_plan.next_action_queue_items == []
    assert all(
        lane.next_action is None
        and lane.next_action_queue_item is None
        and lane.suggested_next_actions == [validation_action]
        for lane in imported.recovery_plan.lanes
    )
    assert all(
        summary.next_action is None
        and summary.suggested_next_actions == [validation_action]
        for summary in imported.recovery_plan.revision_summaries
    )
    assert "start_staged_revision_recovery_session" not in [
        action.tool.removeprefix("doxabase.") for action in imported.suggested_next_actions
    ]
    assert "apply_staged_revision" not in json.dumps(
        to_jsonable(imported.recovery_plan),
        sort_keys=True,
    )
    assert any(
        "failed export validation" in warning
        for warning in imported.warnings
    )


def test_context_slice_export_warns_history_is_not_recovery_handoff(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    staged = db.stage_graph_revision(
        summary="Stage Orders caveat",
        rationale="Create history-backed staged work for context-slice export.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:OrdersCaveat a rc:KnownCaveat ;
                        rdfs:label "Orders caveat" ;
                        rc:caveatDescription "Synthetic caveat for export routing." .
                """,
            }
        ],
        revision_anchors=[dataset],
        included_graphs=["map"],
    )

    preflight = db.preflight_context_slice_export(
        staged.revision_iri,
        profile="deep_lore",
        max_triples=400,
    )

    assert "history" in preflight.graphs
    assert preflight.handoff_fit == (
        "resource_scoped_review_context_not_recovery_complete"
    )
    assert preflight.recovery_complete is False
    assert any(
        "not a recovery-complete revision handoff" in warning
        for warning in preflight.warnings
    )
    assert [
        action.tool.removeprefix("doxabase.") for action in preflight.suggested_next_actions
    ] == [
        "export_context_slice",
        "export_handoff_bundle",
    ]
    handoff_action = preflight.suggested_next_actions[1]
    assert handoff_action.args["revision_iris"] == [staged.revision_iri]
    assert handoff_action.args["manifest_path"] == "<handoff-manifest.json>"
    assert handoff_action.args["graphs"] == ["project"]
    assert handoff_action.args["fail_on_sensitive"] is True

    export_path = tmp_path / "revision-context.trig"
    export = db.export_context_slice(
        export_path,
        staged.revision_iri,
        profile="deep_lore",
        max_triples=400,
        fail_on_sensitive=True,
    )

    assert export.path == str(export_path)
    assert "history" in export.graphs
    assert export.handoff_fit == (
        "resource_scoped_review_context_not_recovery_complete"
    )
    assert any(
        "not a recovery-complete revision handoff" in warning
        for warning in export.warnings
    )
    assert [
        action.tool.removeprefix("doxabase.") for action in export.suggested_next_actions
    ] == ["export_handoff_bundle"]
    assert export.suggested_next_actions[0].args["revision_iris"] == [
        staged.revision_iri
    ]
    export_text = export_path.read_text(encoding="utf-8")
    assert "patchContent" in export_text
    assert "graphRole" in export_text
    assert "tripleCount" in export_text

    receiver = DoxaBase.create(tmp_path / "receiver.sqlite")
    imported = receiver.import_trig(export_path)
    assert imported["history"] == export.graph_counts["history"]
    assert imported["map"] == export.graph_counts["map"]
    validation = receiver.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_recovery_plan_promotes_snapshot_import_for_rdf_only_staged_handoff(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "source.sqlite")
    staged = db.stage_graph_revision(
        summary="Stage live messages table",
        rationale="Exercise RDF-only handoff planning for live staged work.",
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
    db.export_trig(project_path, graphs="project")

    imported = DoxaBase.create(tmp_path / "rdf-only.sqlite")
    imported.import_trig(project_path)

    direct_check = imported.check_staged_revision_apply(staged.revision_iri)
    assert direct_check.status == "ready"
    assert direct_check.can_apply is True
    assert direct_check.next_action is not None
    assert direct_check.next_action.tool_name == "apply_staged_revision"
    assert direct_check.next_action.mutation_scope == "project_graph_and_history"
    assert direct_check.next_action.mutates_project_graph is True
    assert direct_check.next_action.writes_history is True
    assert direct_check.next_action.writes_files is False
    assert direct_check.next_action.writes_storage is False
    assert direct_check.snapshot_evidence is not None
    assert direct_check.snapshot_evidence.status == "history_only_count_digest"
    assert direct_check.snapshot_evidence_completeness == "history-only"
    assert (
        direct_check.mutation_allowed_after
        == "handoff_preflight_required_before_mutation"
    )
    assert [
        action.tool.removeprefix("doxabase.") for action in direct_check.blocking_preflight_actions
    ] == ["import_revision_snapshots"]
    assert direct_check.first_safe_next_action is not None
    assert direct_check.first_safe_next_action.tool_name == (
        "import_revision_snapshots"
    )
    assert direct_check.first_safe_next_action.queue == "complete_handoff_import"
    assert direct_check.first_safe_next_action.mutation_scope == "snapshot_storage"
    assert direct_check.first_safe_next_action.mutates_project_graph is False
    assert direct_check.first_safe_next_action.writes_history is False
    assert direct_check.first_safe_next_action.writes_files is False
    assert direct_check.first_safe_next_action.writes_storage is True

    plan = imported.plan_staged_revision_recovery([staged.revision_iri])

    assert plan.lane_counts == {"complete_handoff_import": 1}
    assert plan.next_action_queue == {
        "complete_handoff_import": [staged.revision_iri]
    }
    assert plan.bundle_summary is not None
    assert plan.bundle_summary.snapshot_evidence.complete is False
    assert plan.bundle_summary.snapshot_evidence.incomplete_revision_iris == [
        staged.revision_iri
    ]
    assert plan.bundle_summary.warnings == plan.warnings
    assert "Snapshot evidence is incomplete" in plan.warnings[0]
    assert "post-preflight mutation routes" in plan.warnings[0]
    lane = plan.lanes[0]
    assert lane.lane == "complete_handoff_import"
    assert lane.next_action is not None
    assert lane.next_action.tool_name == "import_revision_snapshots"
    assert lane.next_action.mutation_scope == "snapshot_storage"
    assert lane.next_action.writes_storage is True
    assert lane.current_snapshot_evidence.status == "history_only_count_digest"
    assert lane.current_snapshot_evidence_completeness == "history-only"
    assert lane.suggested_next_actions[0].tool == (
        "doxabase.import_revision_snapshots"
    )
    assert lane.suggested_next_actions[0].args == {
        "path": "/tmp/revision-snapshots.json",
        "path_is_placeholder": True,
    }
    assert any(
        action.tool == "doxabase.apply_staged_revision"
        for action in lane.suggested_next_actions[1:]
    )
    assert plan.suggested_next_actions[0].tool == "doxabase.import_revision_snapshots"
    assert (
        plan.mutation_allowed_after
        == "handoff_preflight_required_before_mutation"
    )
    assert [
        action.tool.removeprefix("doxabase.") for action in plan.blocking_preflight_actions
    ] == ["import_revision_snapshots"]

    grouped_export_path = tmp_path / "rdf-only-grouped-review.md"
    grouped_export = imported.export_staged_revisions(
        [staged.revision_iri],
        grouped_export_path,
    )
    grouped_text = grouped_export_path.read_text(encoding="utf-8")

    assert grouped_export.bundle_summary.warnings == plan.bundle_summary.warnings
    assert "## Bundle Warnings" in grouped_text
    assert "Snapshot evidence is incomplete" in grouped_text
    assert "Next action - apply after review" in grouped_text
    assert grouped_text.index("Snapshot evidence is incomplete") < grouped_text.index(
        "## Review Queues"
    )

    snapshot_path = tmp_path / "revision-snapshots.json"
    db.export_revision_snapshots(snapshot_path, revision_iris=[staged.revision_iri])
    imported.import_revision_snapshots(snapshot_path)
    direct_check_after_snapshots = imported.check_staged_revision_apply(
        staged.revision_iri
    )
    assert direct_check_after_snapshots.snapshot_evidence is not None
    assert direct_check_after_snapshots.snapshot_evidence.status == (
        "history_plus_snapshot_rows"
    )
    assert direct_check_after_snapshots.blocking_preflight_actions == []
    assert (
        direct_check_after_snapshots.mutation_allowed_after
        == "direct_check_no_preflight"
    )
    assert direct_check_after_snapshots.first_safe_next_action is not None
    assert direct_check_after_snapshots.first_safe_next_action.tool_name == (
        "apply_staged_revision"
    )
    assert (
        direct_check_after_snapshots.first_safe_next_action.mutation_scope
        == "project_graph_and_history"
    )
    assert (
        direct_check_after_snapshots.first_safe_next_action.mutates_project_graph
        is True
    )


def test_staged_revision_recovery_session_replans_live_state(
    tmp_path: Path,
) -> None:
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

    session = db.start_staged_revision_recovery_session(
        [staged.revision_iri],
        summary="Messages recovery session",
        handoff_manifest_path="/tmp/messages-handoff-manifest.json",
        drift_detail="exact",
        created_at="2026-01-02T03:04:05+00:00",
        created_by="https://example.test/agents#TrialAgent",
    )

    assert session.helper == "start_staged_revision_recovery_session"
    assert session.mode == "recorded_session"
    assert session.created_triples is not None
    assert session.created_triples > 0
    assert session.summary == "Messages recovery session"
    assert session.created_at == "2026-01-02T03:04:05+00:00"
    assert session.created_by == "https://example.test/agents#TrialAgent"
    assert session.handoff_manifest_path == "/tmp/messages-handoff-manifest.json"
    assert session.source_revision_iris == [staged.revision_iri]
    assert session.initial_lane_counts == {"restage_after_review": 1}
    assert session.session_status == "active"
    assert session.repair_draft_limit == 1
    assert session.current_plan.repair_draft_limit == 1
    assert session.current_plan.lane_counts == {"restage_after_review": 1}
    assert session.source_states[0].workflow_state == "active"
    assert session.source_states[0].lane == "restage_after_review"
    assert session.source_states[0].effective_recovery_action == (
        "restage_after_review"
    )
    assert session.source_states[0].next_action_tool_name == (
        "restage_staged_revision"
    )
    session_resource = db.describe_resource(session.session_iri, graph="history")
    assert any(
        triple.predicate == str(RDF.type)
        and triple.object == RC + "StagedRevisionRecoverySession"
        for triple in session_resource.outgoing
    )
    assert any(
        triple.predicate == RC + "recoverySessionRepairDraftLimit"
        and triple.object == "1"
        for triple in session_resource.outgoing
    )

    restaged = db.restage_staged_revision(staged.revision_iri)
    after_restage = db.describe_staged_revision_recovery_session(
        session.session_iri,
        drift_detail="exact",
    )

    assert after_restage.helper == "describe_staged_revision_recovery_session"
    assert after_restage.mode == "read_only_description"
    assert after_restage.session_status == "active"
    assert after_restage.repair_draft_limit == 1
    assert after_restage.current_plan.lane_counts == {"apply_after_review": 1}
    assert after_restage.source_states[0].current_revision_iri == (
        restaged.revision_iri
    )
    assert after_restage.source_states[0].effective_recovery_action == (
        "apply_after_review"
    )
    assert after_restage.source_states[0].next_action_tool_name == (
        "apply_staged_revision"
    )
    after_restage_brief = db.project_brief(limit=10)
    recovery_gate = next(
        gate
        for gate in after_restage_brief.gates
        if gate.gate == "staged_revision_recovery"
    )
    assert recovery_gate.blocks == "mutation"
    assert recovery_gate.details_call == (
        "doxabase.describe_staged_revision_recovery_session"
    )
    recovery_action = after_restage_brief.suggested_next_actions[0]
    assert recovery_action.tool == (
        "doxabase.describe_staged_revision_recovery_session"
    )
    assert recovery_action.args == {
        "session_iri": session.session_iri,
        "drift_detail": "exact",
    }

    applied = db.apply_staged_revision(restaged.revision_iri)
    after_apply = db.describe_staged_revision_recovery_session(
        session.session_iri,
        drift_detail="exact",
    )

    assert after_apply.session_status == "complete"
    assert after_apply.current_plan.lane_counts == {"inspect_already_applied": 1}
    assert after_apply.completed_source_revision_iris == [staged.revision_iri]
    assert after_apply.active_source_revision_iris == []
    assert after_apply.applied_event_iris == [applied.applied_revision_iri]
    source_state = after_apply.source_states[0]
    assert source_state.workflow_state == "applied"
    assert source_state.applied_revision_iri == applied.applied_revision_iri
    assert source_state.latest_role == "applied_event"
    assert source_state.next_action_tool_name == "describe_graph_revision"
    assert any(
        action.tool == "doxabase.describe_applied_revision_diff"
        for action in after_apply.suggested_next_actions
    )
    assert db.validate_graph(scope="all").conforms


def test_plan_staged_revision_recovery_routes_mixed_staged_queue(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    repair_source = db.stage_graph_revision(
        summary="Model Orders as snapshot rows",
        rationale="Original row-grain proposal before an intervening map edit.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders rc:rowSemantics rc:SnapshotRow .
                """,
            }
        ],
        revision_anchors=[orders],
    )
    db.record_map_dataset(orders, row_semantics="rc:EventRow")
    informational_source = db.stage_graph_revision(
        summary="Stage already-effective table",
        rationale="This staged source will already be current map state.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:AlreadyEffective a rc:Dataset .
                """,
            }
        ],
    )
    db.record_map_dataset(
        "https://example.test/project#AlreadyEffective",
        label="Already effective",
    )
    stale = db.stage_graph_revision(
        summary="Stage stale messages table",
        rationale="This proposal will need mechanical restage after map drift.",
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
    handled_source = db.stage_graph_revision(
        summary="Stage handled table",
        rationale="This stale source will already have a refreshed successor.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Handled a rc:Dataset .
                """,
            }
        ],
    )
    applied_source = db.stage_graph_revision(
        summary="Stage applied table",
        rationale="This staged source will already be durable.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Applied a rc:Dataset .
                """,
            }
        ],
    )
    applied_event = db.apply_staged_revision(applied_source.revision_iri)
    handled_successor = db.restage_staged_revision(handled_source.revision_iri)
    ready = db.stage_graph_revision(
        summary="Stage ready table",
        rationale="This proposal is staged against current map state.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Ready a rc:Dataset .
                """,
            }
        ],
    )
    counts_before = _mutable_graph_counts(db)

    plan = db.plan_staged_revision_recovery(
        [
            ready.revision_iri,
            stale.revision_iri,
            handled_source.revision_iri,
            repair_source.revision_iri,
            applied_source.revision_iri,
            informational_source.revision_iri,
        ]
    )

    assert _mutable_graph_counts(db) == counts_before
    assert plan.result_kind == "staged_revision_recovery_plan"
    assert plan.mode == "read_only_plan"
    assert plan.selection_mode == "explicit_revision_iris"
    assert plan.returned_count == 6
    assert plan.current_revision_by_source[handled_source.revision_iri] == (
        handled_successor.revision_iri
    )
    assert plan.would_restage_revision_iris == [stale.revision_iri]
    assert plan.repair_first_revision_iris == []
    assert plan.repair_or_replace_source_revision_iris == [
        repair_source.revision_iri
    ]
    lanes_by_source = {lane.source_revision_iri: lane for lane in plan.lanes}
    assert lanes_by_source[ready.revision_iri].lane == "apply_after_review"
    assert (
        lanes_by_source[ready.revision_iri].effective_recovery_action
        == "apply_after_review"
    )
    assert lanes_by_source[ready.revision_iri].batch_action == (
        "skipped_not_restageable"
    )
    assert lanes_by_source[ready.revision_iri].not_restageable_reason == "ready"
    assert lanes_by_source[ready.revision_iri].status_after == "ready"
    assert lanes_by_source[stale.revision_iri].lane == "restage_after_review"
    assert (
        lanes_by_source[stale.revision_iri].effective_recovery_action
        == "restage_after_review"
    )
    assert lanes_by_source[stale.revision_iri].batch_action == "would_restage"
    handled_lane = lanes_by_source[handled_source.revision_iri]
    assert handled_lane.current_revision_iri == handled_successor.revision_iri
    assert handled_lane.row_iri == handled_successor.revision_iri
    assert handled_lane.lane == "apply_after_review"
    assert handled_lane.batch_action == "skipped_already_handled"
    repair_lane = lanes_by_source[repair_source.revision_iri]
    assert repair_lane.lane == "repair_or_replace"
    assert repair_lane.not_restageable_reason == "same_slot_replacement"
    assert repair_lane.repair_draft is not None
    assert repair_lane.repair_draft.draft_kind == "same_slot_replacement"
    assert repair_lane.repair_draft.preferred_action is not None
    assert repair_lane.repair_draft.preferred_action.args["restages_revision"] == (
        repair_source.revision_iri
    )
    assert repair_lane.next_action is not None
    assert repair_lane.next_action.tool_name == "stage_map_assertion_change"
    assert any(
        action.tool == "doxabase.stage_map_assertion_change"
        for action in repair_lane.suggested_next_actions
    )
    applied_lane = lanes_by_source[applied_source.revision_iri]
    assert applied_lane.lane == "inspect_already_applied"
    assert applied_lane.resolved_target_iri == applied_event.applied_revision_iri
    assert applied_lane.resolved_target_record_kind == "applied_event"
    assert applied_lane.row_is_target is False
    informational_lane = lanes_by_source[informational_source.revision_iri]
    assert informational_lane.lane == "informational"
    assert informational_lane.not_restageable_reason == "already_effective"
    assert informational_lane.resolved_target_iri == informational_source.revision_iri
    assert plan.next_action_queue_item_counts == {
        "apply_after_review": 2,
        "restage_after_review": 1,
        "repair_or_replace": 1,
        "inspect_already_applied": 1,
        "informational": 1,
    }
    assert plan.mutation_frontier_iris == [
        ready.revision_iri,
        stale.revision_iri,
        handled_successor.revision_iri,
    ]
    assert [
        action.tool.removeprefix("doxabase.") for action in plan.helper_mutation_frontier_actions
    ] == ["stage_map_assertion_change"]
    assert plan.helper_mutation_frontier_actions[0].args[
        "restages_revision"
    ] == repair_source.revision_iri
    assert [
        item.item_kind for item in plan.mutation_frontier_items
    ] == [
        "revision_target",
        "revision_target",
        "revision_target",
        "helper_action",
    ]
    assert [
        item.target_iri
        for item in plan.mutation_frontier_items
        if item.item_kind == "revision_target"
    ] == plan.mutation_frontier_iris
    helper_item = plan.mutation_frontier_items[-1]
    assert helper_item.queue == "repair_or_replace"
    assert helper_item.target_iri is None
    assert helper_item.source_revision_iris == [repair_source.revision_iri]
    assert helper_item.action == plan.helper_mutation_frontier_actions[0]
    assert any(
        "helper_mutation_frontier_actions" in warning
        and "not represented by mutation_frontier_iris" in warning
        for warning in plan.warnings
    )
    assert plan.resolved_target_group_counts == plan.next_action_queue_item_counts
    assert plan.requires_recheck_after_each_apply is True
    assert set(plan.sequential_apply_recheck_candidate_iris) == {
        ready.revision_iri,
        handled_successor.revision_iri,
    }
    assert any(
        "apply at most one ready row" in warning for warning in plan.warnings
    )
    batch_dry_run_action = plan.suggested_next_actions[0]
    assert batch_dry_run_action.tool == "doxabase.restage_staged_revisions"
    assert batch_dry_run_action.args == {
        "revision_iris": [stale.revision_iri],
        "dry_run": True,
    }
    assert [
        step.step_kind for step in plan.recommended_unattended_steps[:3]
    ] == [
        "dry_run_mechanical_restage",
        "run_reviewed_mechanical_restage",
        "stage_repair_successor",
    ]
    dry_step = plan.recommended_unattended_steps[0]
    assert dry_step.action == batch_dry_run_action
    assert dry_step.can_run_now is True
    assert dry_step.mutates is False
    assert dry_step.requires_replan_after_completion is False
    assert dry_step.revision_iris == [stale.revision_iri]
    real_step = plan.recommended_unattended_steps[1]
    assert real_step.action is not None
    assert real_step.action.tool == "doxabase.restage_staged_revisions"
    assert real_step.action.args == {
        "revision_iris": [stale.revision_iri],
        "dry_run": False,
    }
    assert real_step.can_run_now is False
    assert real_step.prerequisite == "after_reviewing_matching_dry_run"
    assert real_step.mutates is True
    assert real_step.requires_replan_after_completion is True
    assert real_step.stop_reason == "rerun_plan_after_restage"
    helper_step = plan.recommended_unattended_steps[2]
    assert helper_step.action == plan.helper_mutation_frontier_actions[0]
    assert helper_step.source_revision_iris == [repair_source.revision_iri]
    assert helper_step.can_run_now is False
    assert (
        helper_step.prerequisite
        == "after_mechanical_restage_replan_if_still_current"
    )
    assert helper_step.stop_reason == "mechanical_restage_first"
    assert any(
        action.tool == "doxabase.restage_staged_revision"
        and action.args == {"iri": stale.revision_iri}
        for action in plan.suggested_next_actions
    )

    alias_plan = db.plan_staged_revision_recovery(
        [
            handled_source.revision_iri,
            handled_successor.revision_iri,
            applied_source.revision_iri,
        ]
    )
    assert alias_plan.lane_counts == {
        "apply_after_review": 2,
        "inspect_already_applied": 1,
    }
    assert alias_plan.next_action_queue_item_counts == {
        "apply_after_review": 2,
        "inspect_already_applied": 1,
    }
    assert alias_plan.next_action_queue["apply_after_review"] == [
        handled_successor.revision_iri
    ]
    assert alias_plan.mutation_frontier_iris == [handled_successor.revision_iri]
    assert alias_plan.resolved_target_group_counts == {
        "apply_after_review": 1,
        "inspect_already_applied": 1,
    }
    groups_by_target = {
        group.resolved_target_iri: group
        for group in alias_plan.resolved_target_groups
    }
    handled_group = groups_by_target[handled_successor.revision_iri]
    assert handled_group.queue == "apply_after_review"
    assert handled_group.lane_count == 2
    assert handled_group.row_iris == [handled_successor.revision_iri]
    assert handled_group.source_revision_iris == [
        handled_source.revision_iri,
        handled_successor.revision_iri,
    ]
    assert handled_group.requested_revision_iris == [
        handled_source.revision_iri,
        handled_successor.revision_iri,
    ]
    assert handled_group.current_revision_iris == [handled_successor.revision_iri]
    assert handled_group.latest_revision_iris == [handled_successor.revision_iri]
    assert set(handled_group.restage_chain_iris) == {
        handled_source.revision_iri,
        handled_successor.revision_iri,
    }
    assert handled_group.row_is_target_all is True
    assert handled_group.row_is_target_any is True
    applied_group = groups_by_target[applied_event.applied_revision_iri]
    assert applied_group.queue == "inspect_already_applied"
    assert applied_group.lane_count == 1
    assert applied_group.applied_event_iris == [applied_event.applied_revision_iri]
    assert applied_group.row_is_target_all is False
    assert applied_group.row_is_target_any is False

    dry_run = db.restage_staged_revisions(
        plan.would_restage_revision_iris,
        dry_run=True,
    )

    assert dry_run.would_restage_revision_iris == [stale.revision_iri]

    batch = db.restage_staged_revisions(dry_run.would_restage_revision_iris)
    restaged_stale_iri = batch.restaged_revision_iris[0]
    applied_ready = db.apply_staged_revision(ready.revision_iri)

    assert set(applied_ready.post_apply_recheck_revision_iris) == {
        restaged_stale_iri,
        handled_successor.revision_iri,
        informational_source.revision_iri,
        repair_source.revision_iri,
    }

    followup_plan = db.plan_staged_revision_recovery(
        current_staged_work_only=True
    )

    assert followup_plan.next_action_queue_item_counts == {
        "restage_after_review": 2,
        "repair_or_replace": 1,
        "informational": 1,
    }
    assert set(followup_plan.would_restage_revision_iris) == {
        restaged_stale_iri,
        handled_successor.revision_iri,
    }
    followup_batch_action = followup_plan.suggested_next_actions[0]
    assert followup_batch_action.tool == "doxabase.restage_staged_revisions"
    assert set(followup_batch_action.args["revision_iris"]) == {
        restaged_stale_iri,
        handled_successor.revision_iri,
    }
    assert followup_batch_action.args["dry_run"] is True
    assert set(followup_plan.mutation_frontier_iris) == {
        restaged_stale_iri,
        handled_successor.revision_iri,
    }
    assert followup_plan.repair_or_replace_source_revision_iris == [
        repair_source.revision_iri
    ]
    assert informational_source.revision_iri not in (
        followup_plan.mutation_frontier_iris
    )


def test_plan_staged_revision_recovery_accepts_empty_explicit_revision_list(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    plan = db.plan_staged_revision_recovery(
        revision_iris=[],
        current_staged_work_only=False,
        drift_detail="exact",
    )

    assert plan.selection_mode == "explicit_revision_iris"
    assert plan.requested_revision_iris == []
    assert plan.processed_revision_iris == []
    assert plan.current_staged_work_only is False
    assert plan.drift_detail == "exact"
    assert plan.count == 0
    assert plan.returned_count == 0
    assert plan.total_count == 0
    assert plan.lane_counts == {}
    assert plan.next_action_queue == {}
    assert plan.next_action_queue_items == []
    assert plan.mutation_frontier_iris == []
    assert plan.mutation_allowed_after == "no_mutation_frontier"
    assert plan.suggested_next_actions == []


def test_plan_staged_revision_recovery_reuses_apply_checks_for_current_work(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/recovery-performance#"
    revisions = [
        db.stage_graph_revision(
            summary=f"Stage ready table {index}",
            rationale="Independent ready staged row for recovery planning.",
            additions=[
                {
                    "graph": "map",
                    "content": f"""
                        @prefix rc: <{RC}> .

                        <{base}Table{index}> a rc:Dataset, rc:Table .
                    """,
                }
            ],
            revision_anchors=[f"{base}Table{index}"],
        )
        for index in range(2)
    ]

    apply_check_count = 0
    original_check = db.check_staged_revision_apply

    def counted_check(*args, **kwargs):
        nonlocal apply_check_count
        apply_check_count += 1
        return original_check(*args, **kwargs)

    monkeypatch.setattr(db, "check_staged_revision_apply", counted_check)

    plan = db.plan_staged_revision_recovery(
        current_staged_work_only=True,
        include_drafts=False,
    )

    assert apply_check_count == len(revisions)
    assert plan.selection_mode == "current_staged_work"
    assert plan.total_count == len(revisions)
    assert plan.lane_counts == {"apply_after_review": len(revisions)}
    assert set(plan.mutation_frontier_iris) == {
        revision.revision_iri for revision in revisions
    }


def test_plan_staged_revision_recovery_keeps_valid_rows_with_patchless_history(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    applied_source = db.stage_graph_revision(
        summary="Stage already applied mixed-order row",
        rationale="This staged source will become an applied event for ordering.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:AlreadyAppliedMixedOrder a rc:Dataset .
                """,
            }
        ],
    )
    applied_event = db.apply_staged_revision(applied_source.revision_iri)
    ready = db.stage_graph_revision(
        summary="Stage ready table",
        rationale="This staged source has a complete patch payload.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:ReadyMixedHandoff a rc:Dataset .
                """,
            }
        ],
    )
    patchless_iri = "https://example.test/project#PatchlessStagedMetadata"
    db.record_graph_revision(
        summary="Patchless staged metadata",
        rationale="This mimics an RDF-only handoff row without staged patch triples.",
        changed_graphs=["map"],
        revision_type="rc:StagedRevision",
        revision_iri=patchless_iri,
    )
    counts_before = _mutable_graph_counts(db)

    plan = db.plan_staged_revision_recovery([ready.revision_iri, patchless_iri])

    assert _mutable_graph_counts(db) == counts_before
    assert plan.returned_count == 2
    assert plan.processed_revision_iris == [ready.revision_iri, patchless_iri]
    assert plan.next_action_queue_item_counts == {
        "apply_after_review": 1,
        "informational": 1,
    }
    lanes_by_source = {lane.source_revision_iri: lane for lane in plan.lanes}
    assert lanes_by_source[ready.revision_iri].lane == "apply_after_review"
    patchless_lane = lanes_by_source[patchless_iri]
    assert patchless_lane.lane == "informational"
    assert patchless_lane.batch_action == "skipped_missing_patch_payload"
    assert patchless_lane.not_restageable_reason == "missing_patch_payload"
    assert patchless_lane.next_action is not None
    assert patchless_lane.next_action.tool_name == "describe_graph_revision"
    assert patchless_lane.next_action_queue_item is not None
    assert patchless_lane.next_action_queue_item.record_kind == "history_record"
    assert patchless_lane.next_action_queue_item.resolved_target_iri == patchless_iri
    assert plan.current_revision_by_source[patchless_iri] == patchless_iri
    assert plan.not_restageable_revision_iris_by_reason[
        "missing_patch_payload"
    ] == [patchless_iri]
    assert patchless_iri in plan.review_revision_iris
    assert patchless_iri in plan.recommended_review_iris
    assert any(
        action.tool == "doxabase.describe_graph_revision"
        and action.args["iri"] == patchless_iri
        for action in plan.suggested_next_actions
    )
    assert any("without patch payload" in warning for warning in plan.warnings)

    patchless_only = db.plan_staged_revision_recovery([patchless_iri])
    assert patchless_only.returned_count == 1
    assert patchless_only.lanes[0].lane == "informational"
    assert patchless_only.lanes[0].not_restageable_reason == "missing_patch_payload"
    assert patchless_only.next_action_queue_item_counts == {"informational": 1}

    all_staged_plan = db.plan_staged_revision_recovery(
        current_staged_work_only=False
    )
    assert all_staged_plan.returned_count == 3
    assert set(all_staged_plan.processed_revision_iris) == {
        applied_source.revision_iri,
        ready.revision_iri,
        patchless_iri,
    }
    assert all_staged_plan.next_action_queue_item_counts == {
        "apply_after_review": 1,
        "inspect_already_applied": 1,
        "informational": 1,
    }
    all_lanes_by_source = {
        lane.source_revision_iri: lane for lane in all_staged_plan.lanes
    }
    assert (
        all_lanes_by_source[applied_source.revision_iri].lane
        == "inspect_already_applied"
    )
    assert all_lanes_by_source[patchless_iri].lane == "informational"
    assert all_lanes_by_source[patchless_iri].not_restageable_reason == (
        "missing_patch_payload"
    )

    mixed_order_plan = db.plan_staged_revision_recovery(
        [
            patchless_iri,
            applied_event.applied_revision_iri,
            ready.revision_iri,
        ]
    )
    assert mixed_order_plan.processed_revision_iris == [
        patchless_iri,
        applied_event.applied_revision_iri,
        ready.revision_iri,
    ]
    assert [lane.source_revision_iri for lane in mixed_order_plan.lanes] == [
        patchless_iri,
        applied_event.applied_revision_iri,
        ready.revision_iri,
    ]
    assert [lane.lane for lane in mixed_order_plan.lanes] == [
        "informational",
        "inspect_already_applied",
        "apply_after_review",
    ]


def test_plan_staged_revision_recovery_routes_non_staged_history_records(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.record_map_dataset(
        "https://example.test/project#Orders",
        label="Orders",
        is_table=True,
    )
    manual = db.record_graph_revision(
        summary="Manual map review",
        rationale="Record durable map review history with snapshots.",
        changed_graphs=["map"],
        included_graphs=["map"],
    )
    ready = db.stage_graph_revision(
        summary="Stage ready table",
        rationale="This staged source has a complete patch payload.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:ReadyNonStagedHandoff a rc:Dataset .
                """,
            }
        ],
    )

    plan = db.plan_staged_revision_recovery(
        [manual.revision_iri, ready.revision_iri],
        current_staged_work_only=False,
    )

    assert plan.processed_revision_iris == [manual.revision_iri, ready.revision_iri]
    assert plan.next_action_queue_item_counts == {
        "apply_after_review": 1,
        "informational": 1,
    }
    lanes_by_source = {lane.source_revision_iri: lane for lane in plan.lanes}
    manual_lane = lanes_by_source[manual.revision_iri]
    assert manual_lane.lane == "informational"
    assert manual_lane.batch_action == "skipped_non_staged_history_record"
    assert manual_lane.not_restageable_reason == "non_staged_history_record"
    assert manual_lane.next_action is not None
    assert manual_lane.next_action.tool_name == "describe_graph_revision"
    assert manual_lane.next_action_queue_item is not None
    assert manual_lane.next_action_queue_item.record_kind == "history_record"
    assert plan.not_restageable_revision_iris_by_reason[
        "non_staged_history_record"
    ] == [manual.revision_iri]
    assert manual.revision_iri in plan.review_revision_iris
    assert any(
        "non-staged graph-revision history" in warning for warning in plan.warnings
    )


@pytest.mark.parametrize("staged_object", ['"snapshot"', "[]"])
def test_invalid_row_semantics_object_does_not_draft_rebase_repair(
    tmp_path: Path,
    staged_object: str,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    source = db.stage_graph_revision(
        summary="Model Orders with invalid row-semantics object",
        rationale="Probe that invalid singleton-slot objects are not repaired mechanically.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders rc:rowSemantics {staged_object} .
                """,
            }
        ],
        revision_anchors=[orders],
    )
    assert source.validation_conforms is False
    db.record_map_dataset(orders, row_semantics="rc:EventRow")

    check = db.check_staged_revision_apply(source.revision_iri)

    assert check.status == "conflict"
    assert check.next_action is not None
    assert check.next_action.queue == "repair_or_replace"
    assert not any(
        action.tool == "doxabase.stage_map_assertion_change"
        for action in check.suggested_next_actions
    )
    draft = db.draft_staged_revision_rebase(source.revision_iri)
    assert draft.draft_status == "not_drafted"
    assert draft.draft_kind == "validation_repair_needed"
    assert "staged_validation_failed" in draft.reason_codes
    assert draft.repair_actions == []
    assert draft.repair_candidates == []
    assert draft.next_action is not None
    assert draft.next_action.queue == "repair_or_replace"
    assert draft.next_action.tool_name != "draft_staged_revision_rebase"
    assert all(
        action.tool != "doxabase.draft_staged_revision_rebase"
        for action in draft.suggested_next_actions
    )
    plan = db.plan_staged_revision_recovery([source.revision_iri])
    assert plan.repair_first_revision_iris == [source.revision_iri]
    assert plan.next_action_queue == {
        "repair_or_replace": [source.revision_iri],
    }
    assert plan.mutation_frontier_iris == []
    assert plan.mutation_frontier_items == []
    assert (
        plan.mutation_allowed_after
        == "repair_inspection_required_before_mutation"
    )
    assert any(
        "diagnostic inspection" in warning
        and "not represented by mutation_frontier_iris" in warning
        for warning in plan.warnings
    )
    lane = plan.lanes[0]
    assert lane.repair_draft is not None
    assert lane.repair_draft.draft_kind == "validation_repair_needed"
    assert lane.next_action is not None
    assert lane.next_action.tool_name != "draft_staged_revision_rebase"
    assert lane.suggested_next_actions == lane.repair_draft.suggested_next_actions
    assert all(
        action.tool != "doxabase.draft_staged_revision_rebase"
        for action in lane.suggested_next_actions
    )
    assert all(
        action.tool != "doxabase.draft_staged_revision_rebase"
        for action in plan.suggested_next_actions
    )
    assert plan.helper_mutation_frontier_actions == []


def test_plan_staged_revision_recovery_bounds_embedded_repair_drafts(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    def stage_invalid_row_semantics(local_name: str) -> str:
        dataset = f"https://example.test/project#{local_name}"
        db.record_map_dataset(dataset, label=local_name, is_table=True)
        staged = db.stage_graph_revision(
            summary=f"Model {local_name} with invalid row semantics",
            rationale="The invalid object should require manual repair review.",
            additions=[
                {
                    "graph": "map",
                    "content": f"""
                        @prefix ex: <https://example.test/project#> .
                        @prefix rc: <https://richcanopy.org/ns/rc#> .

                        ex:{local_name} rc:rowSemantics "snapshot" .
                    """,
                }
            ],
            revision_anchors=[dataset],
        )
        db.record_map_dataset(dataset, row_semantics="rc:EventRow")
        return staged.revision_iri

    revision_iris = [
        stage_invalid_row_semantics("Orders"),
        stage_invalid_row_semantics("Invoices"),
        stage_invalid_row_semantics("Shipments"),
    ]

    default_plan = db.plan_staged_revision_recovery(revision_iris)

    assert default_plan.repair_draft_limit == 1
    assert default_plan.repair_draft_attempted_count == 1
    assert default_plan.repair_drafts_included_count == 1
    assert default_plan.repair_drafts_deferred_count == 2
    assert default_plan.repair_or_replace_source_revision_iris == revision_iris
    assert default_plan.lane_counts == {"repair_or_replace": 3}
    assert default_plan.lanes[0].repair_draft is not None
    assert default_plan.lanes[0].repair_draft_deferred_reason is None
    assert [
        lane.repair_draft_deferred_reason for lane in default_plan.lanes[1:]
    ] == ["repair_draft_limit_reached", "repair_draft_limit_reached"]
    assert all(lane.repair_draft is None for lane in default_plan.lanes[1:])
    assert any("repair_draft_limit=1" in warning for warning in default_plan.warnings)

    zero_plan = db.plan_staged_revision_recovery(
        revision_iris,
        repair_draft_limit=0,
    )

    assert zero_plan.repair_draft_limit == 0
    assert zero_plan.repair_draft_attempted_count == 0
    assert zero_plan.repair_drafts_included_count == 0
    assert zero_plan.repair_drafts_deferred_count == 3
    assert zero_plan.repair_or_replace_source_revision_iris == revision_iris
    assert all(lane.repair_draft is None for lane in zero_plan.lanes)
    assert all(
        lane.repair_draft_deferred_reason == "repair_draft_limit_reached"
        for lane in zero_plan.lanes
    )

    exhaustive_plan = db.plan_staged_revision_recovery(
        revision_iris,
        repair_draft_limit=None,
    )

    assert exhaustive_plan.repair_draft_limit is None
    assert exhaustive_plan.repair_draft_attempted_count == 3
    assert exhaustive_plan.repair_drafts_included_count == 3
    assert exhaustive_plan.repair_drafts_deferred_count == 0
    assert all(lane.repair_draft is not None for lane in exhaustive_plan.lanes)
    assert all(
        lane.repair_draft_deferred_reason is None for lane in exhaustive_plan.lanes
    )

    no_drafts_plan = db.plan_staged_revision_recovery(
        revision_iris,
        include_drafts=False,
    )

    assert no_drafts_plan.repair_draft_limit == 0
    assert no_drafts_plan.repair_draft_attempted_count == 0
    assert no_drafts_plan.repair_drafts_included_count == 0
    assert no_drafts_plan.repair_drafts_deferred_count == 0
    assert all(lane.repair_draft is None for lane in no_drafts_plan.lanes)
    assert all(
        lane.repair_draft_deferred_reason is None for lane in no_drafts_plan.lanes
    )


def test_semantic_rebase_loop_separates_restage_from_same_slot_repair(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/semantic-rebase#"
    orders = f"{base}Orders"
    fulfillment_events = f"{base}FulfillmentEvents"
    db.record_map_dataset(
        orders,
        label="Orders",
        is_table=True,
        row_semantics="rc:SnapshotRow",
    )
    independent = db.stage_graph_revision(
        summary="Add Fulfillment Events table",
        rationale="Independent table proposal staged before row-grain review.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix rc: <{RC}> .

                    <{fulfillment_events}> a rc:Dataset, rc:Table .
                """,
            }
        ],
        revision_anchors=[fulfillment_events],
    )
    alternatives = db.stage_systematisation(
        summary="Explore Orders row-grain alternatives",
        intent=(
            "Keep competing row-semantics framings reviewable while recovery "
            "distinguishes mechanical drift from semantic same-slot repair."
        ),
        anchors=[orders],
        framings=[
            {
                "label": "Event rows",
                "additions": [
                    {
                        "graph": "map",
                        "content": f"""
                            @prefix rc: <{RC}> .

                            <{orders}> rc:rowSemantics rc:EventRow .
                        """,
                    }
                ],
                "removals": [
                    {
                        "graph": "map",
                        "content": f"""
                            @prefix rc: <{RC}> .

                            <{orders}> rc:rowSemantics rc:SnapshotRow .
                        """,
                    }
                ],
                "review_recommendation": "Preferred for this trial.",
            },
            {
                "label": "Aggregate rows",
                "additions": [
                    {
                        "graph": "map",
                        "content": f"""
                            @prefix rc: <{RC}> .

                            <{orders}> rc:rowSemantics rc:AggregateRow .
                        """,
                    }
                ],
                "removals": [
                    {
                        "graph": "map",
                        "content": f"""
                            @prefix rc: <{RC}> .

                            <{orders}> rc:rowSemantics rc:SnapshotRow .
                        """,
                    }
                ],
                "review_recommendation": "Competing alternative.",
            },
        ],
        validation_scope="all",
    )
    event_rows = alternatives.staged_revisions[0]
    aggregate_rows = alternatives.staged_revisions[1]
    assert aggregate_rows.alternative_to == event_rows.revision_iri

    initial_plan = db.plan_staged_revision_recovery(
        current_staged_work_only=True,
    )
    assert set(initial_plan.mutation_frontier_iris) == {
        independent.revision_iri,
        event_rows.revision_iri,
        aggregate_rows.revision_iri,
    }
    assert initial_plan.requires_recheck_after_each_apply is True

    applied_event = db.apply_staged_revision(event_rows.revision_iri)
    assert set(applied_event.post_apply_recheck_revision_iris) == {
        independent.revision_iri,
        aggregate_rows.revision_iri,
    }

    stale_plan = db.plan_staged_revision_recovery(
        current_staged_work_only=True,
        drift_detail="exact",
    )
    assert stale_plan.next_action_queue == {
        "repair_or_replace": [aggregate_rows.revision_iri],
        "restage_after_review": [independent.revision_iri],
    }
    assert stale_plan.mutation_frontier_iris == [independent.revision_iri]
    assert stale_plan.not_restageable_revision_iris_by_reason == {
        "same_slot_replacement": [aggregate_rows.revision_iri],
    }
    assert stale_plan.semantic_review_required_queue_counts == {
        "repair_or_replace": 1,
    }
    assert [
        action.tool.removeprefix("doxabase.")
        for action in stale_plan.helper_mutation_frontier_actions
    ] == ["stage_map_assertion_change"]
    helper_action = stale_plan.helper_mutation_frontier_actions[0]
    assert helper_action.args["restages_revision"] == (
        aggregate_rows.revision_iri
    )
    assert helper_action.args["alternative_to"] == event_rows.revision_iri
    helper_item = stale_plan.mutation_frontier_items[-1]
    assert helper_item.item_kind == "helper_action"
    assert helper_item.action == helper_action
    assert helper_item.source_revision_iris == [aggregate_rows.revision_iri]
    assert helper_item.row_iris == [aggregate_rows.revision_iri]
    assert helper_item.alternative_set_iris == [
        event_rows.revision_iri,
        aggregate_rows.revision_iri,
    ]
    assert helper_item.alternative_set_source_iri == event_rows.revision_iri
    assert helper_item.alternative_set_roles == ["alternative"]
    assert helper_item.alternative_gate_statuses == [
        "alternative_to_applied_source"
    ]
    assert helper_item.alternative_applied_source_iris == [event_rows.revision_iri]
    assert helper_item.alternative_applied_revision_iris == [
        applied_event.applied_revision_iri
    ]
    assert helper_item.requires_semantic_review_before_mutation is True
    assert "semantic review is required before mutation" in helper_item.reason
    assert "do not mutate unattended" in helper_item.reason
    assert stale_plan.first_mutation_action is None
    assert any(
        action_tool_name(item.action) == "restage_staged_revision"
        and dict(action_arguments(item.action))
        == {"iri": independent.revision_iri}
        and item.requires_semantic_review_before_mutation is False
        for item in stale_plan.mutation_frontier_items
    )
    lanes_by_source = {
        lane.source_revision_iri: lane for lane in stale_plan.lanes
    }
    assert lanes_by_source[independent.revision_iri].lane == "restage_after_review"
    repair_lane = lanes_by_source[aggregate_rows.revision_iri]
    assert repair_lane.lane == "repair_or_replace"
    assert repair_lane.not_restageable_reason == "same_slot_replacement"
    assert repair_lane.repair_draft is not None
    assert repair_lane.repair_draft.draft_kind == "same_slot_replacement"
    assert repair_lane.next_action is not None
    assert repair_lane.next_action.tool_name == "stage_map_assertion_change"

    dry_run = db.restage_staged_revisions(
        [independent.revision_iri, aggregate_rows.revision_iri],
        dry_run=True,
    )
    assert dry_run.would_restage_revision_iris == [independent.revision_iri]
    assert dry_run.not_restageable_revision_iris_by_reason == {
        "same_slot_replacement": [aggregate_rows.revision_iri],
    }
    assert [
        (item.source_revision_iri, item.action, item.not_restageable_reason)
        for item in dry_run.items
    ] == [
        (independent.revision_iri, "would_restage", None),
        (
            aggregate_rows.revision_iri,
            "skipped_not_restageable",
            "same_slot_replacement",
        ),
    ]

    restaged_independent = db.restage_staged_revision(independent.revision_iri)
    restaged_independent_check = db.check_staged_revision_apply(
        restaged_independent.revision_iri,
    )
    assert restaged_independent_check.status == "ready"
    applied_independent = db.apply_staged_revision(
        restaged_independent.revision_iri,
    )
    assert applied_independent.patches_applied == 1

    repair_draft = db.draft_staged_revision_rebase(aggregate_rows.revision_iri)
    assert repair_draft.draft_status == "drafted"
    assert repair_draft.draft_kind == "same_slot_replacement"
    assert repair_draft.preferred_action is not None
    assert repair_draft.preferred_action.tool == "doxabase.stage_map_assertion_change"
    assert repair_draft.preferred_action.args["restages_revision"] == (
        aggregate_rows.revision_iri
    )
    assert repair_draft.preferred_action.args["alternative_to"] == (
        event_rows.revision_iri
    )

    repair = db.stage_map_assertion_change(
        **repair_draft.preferred_action.args,
    )
    assert repair.staged_revision.restaged_from == aggregate_rows.revision_iri
    assert repair.staged_revision.alternative_to == event_rows.revision_iri
    repair_check = db.check_staged_revision_apply(
        repair.staged_revision.revision_iri,
    )
    assert repair_check.status == "ready"
    assert repair_check.alternative_gate.status == "alternative_to_applied_source"
    assert repair_check.alternative_gate.semantic_review_required is True
    assert repair_check.alternative_gate.applied_source_iri == event_rows.revision_iri
    assert repair_check.alternative_gate.applied_revision_iri == (
        applied_event.applied_revision_iri
    )
    assert repair_check.next_action is not None
    assert repair_check.next_action.action_label == (
        "Apply only after semantic review"
    )
    assert repair_check.first_safe_next_action is not None
    assert repair_check.first_safe_next_action.tool_name == "describe_staged_revision"
    assert repair_check.first_safe_next_action.queue == "semantic_review_required"
    assert repair_check.first_safe_next_action.mutation_scope == "none"
    assert repair_check.first_safe_next_action.mutates_project_graph is False

    final_plan = db.plan_staged_revision_recovery(current_staged_work_only=True)
    assert final_plan.mutation_frontier_iris == [
        repair.staged_revision.revision_iri
    ]
    assert final_plan.semantic_review_required_queue_counts == {
        "apply_after_review": 1,
    }
    semantic_item = final_plan.next_action_queue_items[0]
    assert semantic_item.row_iri == repair.staged_revision.revision_iri
    assert semantic_item.alternative_gate_status == "alternative_to_applied_source"
    assert semantic_item.alternative_semantic_review_required is True
    assert semantic_item.requires_semantic_review_before_mutation is True
    frontier_item = final_plan.mutation_frontier_items[0]
    assert frontier_item.target_iri == repair.staged_revision.revision_iri
    assert frontier_item.semantic_risk_level == semantic_item.semantic_risk_level
    assert frontier_item.semantic_risk_reasons == semantic_item.semantic_risk_reasons
    assert frontier_item.alternative_set_iris == [
        event_rows.revision_iri,
        repair.staged_revision.revision_iri,
    ]
    assert frontier_item.alternative_set_source_iri == event_rows.revision_iri
    assert frontier_item.alternative_set_roles == ["alternative"]
    assert frontier_item.alternative_gate_statuses == [
        semantic_item.alternative_gate_status
    ]
    assert frontier_item.alternative_applied_source_iris == [
        event_rows.revision_iri
    ]
    assert frontier_item.alternative_applied_revision_iris == [
        applied_event.applied_revision_iri
    ]
    assert frontier_item.requires_semantic_review_before_mutation is True
    assert "semantic review is required before mutation" in frontier_item.reason
    assert "do not mutate unattended" in frontier_item.reason
    assert final_plan.first_mutation_action is None
    assert final_plan.first_safe_review_or_mutation_action is not None
    assert (
        action_tool_name(final_plan.first_safe_review_or_mutation_action)
        == "describe_staged_revision"
    )


def test_grouped_export_summarizes_stale_alternative_recovery(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    first = db.stage_graph_revision(
        summary="Model order rows as raw events",
        rationale="Keep the raw event framing available for review.",
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
        summary="Model order rows as lifecycle entities",
        rationale="Keep the lifecycle entity framing available for review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:OrderLifecycles a rc:Dataset .
                """,
            }
        ],
        alternative_to=first.revision_iri,
    )
    db.record_map_dataset(
        "https://example.test/project#DriftDataset",
        label="Drift dataset",
    )

    first_restaged = db.restage_staged_revision(first.revision_iri)
    second_restaged = db.restage_staged_revision(second.revision_iri)

    export = db.export_staged_revisions(
        [
            first.revision_iri,
            first_restaged.revision_iri,
            second.revision_iri,
            second_restaged.revision_iri,
        ],
        tmp_path / "stale-alternative-recovery.md",
        title="Stale alternative recovery",
    )
    exported = (tmp_path / "stale-alternative-recovery.md").read_text(
        encoding="utf-8"
    )
    summaries = {item.revision_iri: item for item in export.revision_summaries}

    assert summaries[first.revision_iri].stale_resolution_state == (
        "stale_handled_by_restage"
    )
    assert summaries[second.revision_iri].stale_resolution_state == (
        "stale_handled_by_restage"
    )
    assert summaries[first_restaged.revision_iri].stale_resolution_state == (
        "restaged_successor_ready"
    )
    assert summaries[second_restaged.revision_iri].stale_resolution_state == (
        "restaged_successor_ready"
    )
    assert summaries[second_restaged.revision_iri].alternative_to == first.revision_iri
    assert summaries[second_restaged.revision_iri].current_alternative_to == (
        first_restaged.revision_iri
    )
    assert export.bundle_summary.apply_status_counts == {
        "conflict": 2,
        "ready": 2,
    }
    assert export.bundle_summary.stale_resolution_state_counts == {
        "stale_handled_by_restage": 2,
        "restaged_successor_ready": 2,
    }
    assert export.bundle_summary.unresolved_stale_revision_iris == []
    assert export.bundle_summary.stale_handled_by_restage_revision_iris == [
        first.revision_iri,
        second.revision_iri,
    ]
    assert export.bundle_summary.ready_restage_successor_revision_iris == [
        first_restaged.revision_iri,
        second_restaged.revision_iri,
    ]
    assert export.bundle_summary.post_apply_recheck_revision_iris == [
        first_restaged.revision_iri,
        second_restaged.revision_iri,
    ]
    assert export.bundle_summary.sequential_apply_recheck_candidate_iris == [
        first_restaged.revision_iri,
        second_restaged.revision_iri,
    ]
    assert len(export.bundle_summary.warnings) == 1
    assert "Re-run check_staged_revision_apply" in export.bundle_summary.warnings[0]
    assert export.bundle_summary.recommended_review_iris == [
        first_restaged.revision_iri,
        second_restaged.revision_iri,
    ]
    assert export.bundle_summary.recommended_mutation_review_iris == [
        first_restaged.revision_iri,
        second_restaged.revision_iri,
    ]
    assert export.bundle_summary.recommended_apply_or_restage_review_iris == [
        first_restaged.revision_iri,
        second_restaged.revision_iri,
    ]
    assert export.bundle_summary.mutation_frontier_iris == [
        first_restaged.revision_iri,
        second_restaged.revision_iri,
    ]
    assert export.bundle_summary.requires_recheck_after_each_apply is True
    assert export.bundle_summary.recommended_repair_review_iris == []
    assert export.bundle_summary.recommended_applied_inspection_iris == []
    assert "## Bundle Warnings" in exported
    assert exported.index("## Bundle Warnings") < exported.index("## Restage Context")
    assert "## Review Queues" in exported
    assert exported.index("## Review Queues") < exported.index("## Restage Context")
    assert "Mutation frontier:" in exported
    assert "requires rechecking the remaining ready candidates" in exported
    assert "## Alternative Context" in exported
    assert (
        "Stored alternative to Revision 1: Model order rows as raw events"
        in exported
    )
    assert (
        "current alternative to Revision 2: Restage stale revision: "
        "Model order rows as raw events"
    ) in exported
    assert exported.index("## Alternative Context") < exported.index("## Revisions")

    result = db.apply_staged_revision(first_restaged.revision_iri)
    assert result.post_apply_recheck_revision_iris == [second_restaged.revision_iri]
    assert result.warnings == [
        (
            "Applying this staged revision may have made sibling staged readiness "
            "stale. Recheck affected staged revisions before the next mutation: "
            f"{second_restaged.revision_iri}. post_apply_recheck_revision_iris "
            "is the affected-sibling subset, not the full remaining staged queue; "
            "rerun plan_staged_revision_recovery(current_staged_work_only=True) "
            "before applying another row."
        )
    ]
    assert len(result.post_apply_recheck_revisions) == 1
    recheck = result.post_apply_recheck_revisions[0]
    assert recheck.iri == second_restaged.revision_iri
    assert recheck.changed_graphs == ["map"]
    assert recheck.shared_changed_graphs == ["map"]
    assert recheck.application_status == "conflict"
    assert recheck.decision == "restage_against_current_graph"
    assert "target_count_drift" in recheck.blocking_reasons
    assert recheck.next_action is not None
    assert recheck.next_action.action_type == "restage_after_review"
    assert recheck.next_action.tool_name == "restage_staged_revision"
    assert recheck.next_action.arguments == {"iri": second_restaged.revision_iri}
    assert recheck.suggested_next_actions[-1].tool == "doxabase.restage_staged_revision"
    recheck_export_path = tmp_path / "post-apply-recheck.md"
    recheck_export = db.export_staged_revisions(
        result.post_apply_recheck_revision_iris,
        recheck_export_path,
    )
    assert recheck_export.revision_iris == [
        second_restaged.revision_iri
    ]
    assert recheck_export.bundle_summary.total_revisions == 1
    assert recheck_export.bundle_summary.apply_status_counts == {
        "conflict": 1,
    }
    assert recheck_export.bundle_summary.next_action_queue == {
        "restage_after_review": [second_restaged.revision_iri],
    }
    assert recheck_export.bundle_summary.mutation_frontier_iris == [
        second_restaged.revision_iri
    ]
    assert recheck_export.bundle_summary.requires_recheck_after_each_apply is False
    assert recheck_export.revision_summaries[0].next_action is not None
    assert recheck_export.revision_summaries[0].next_action.arguments == (
        recheck.next_action.arguments
    )
    post_apply_dry_run = db.restage_staged_revisions(
        result.post_apply_recheck_revision_iris,
        dry_run=True,
    )
    assert post_apply_dry_run.dry_run is True
    assert [item.action for item in post_apply_dry_run.items] == [
        "would_restage"
    ]
    assert post_apply_dry_run.items[0].current_revision_iri == (
        second_restaged.revision_iri
    )
    assert post_apply_dry_run.items[0].next_action_after is not None
    assert post_apply_dry_run.items[0].next_action_after.action_type == (
        "restage_after_review"
    )
    assert post_apply_dry_run.items[0].next_action_after.arguments == {
        "iri": second_restaged.revision_iri,
    }
    second_check_after_apply = db.check_staged_revision_apply(
        second_restaged.revision_iri
    )
    assert second_check_after_apply.status == "conflict"
    assert "target_count_drift" in second_check_after_apply.blocking_reasons
    recovered_second = db.restage_staged_revision(
        recheck.next_action.arguments["iri"]
    )
    recovered_second_check = db.check_staged_revision_apply(
        recovered_second.revision_iri
    )
    assert recovered_second_check.status == "ready"
    assert recovered_second_check.decision == "review_then_apply"
    assert recovered_second_check.stale_resolution_state == (
        "restaged_successor_ready"
    )
    assert recovered_second_check.alternative_gate.status == (
        "alternative_to_applied_source"
    )
    assert recovered_second_check.alternative_gate.semantic_review_required is True
    assert recovered_second_check.alternative_gate.applied_source_iri == (
        first_restaged.revision_iri
    )
    assert recovered_second_check.alternative_gate.applied_revision_iri == (
        result.applied_revision_iri
    )
    assert recovered_second_check.semantic_risk_level == "none"
    assert recovered_second_check.next_action is not None
    assert recovered_second_check.next_action.action_type == "apply_after_review"
    assert recovered_second_check.next_action.queue == "apply_after_review"
    assert recovered_second_check.next_action.action_label == (
        "Apply only after semantic review"
    )
    assert first_restaged.revision_iri in recovered_second_check.next_action.reason
    assert result.applied_revision_iri in recovered_second_check.next_action.reason
    review_action = recovered_second_check.suggested_next_actions[0]
    assert review_action.tool == "doxabase.describe_staged_revision"
    assert first_restaged.revision_iri in review_action.reason
    assert result.applied_revision_iri in review_action.reason
    export_action = recovered_second_check.suggested_next_actions[1]
    assert export_action.tool == "doxabase.export_staged_revision"
    assert "semantic alternative gate" in export_action.reason
    assert "staged-revision-semantic-alternative-review" in (
        export_action.args["path"]
    )
    apply_action = recovered_second_check.suggested_next_actions[-1]
    assert apply_action.tool == "doxabase.apply_staged_revision"
    assert apply_action.reason == recovered_second_check.next_action.reason
    assert first_restaged.revision_iri in apply_action.reason
    assert result.applied_revision_iri in apply_action.reason
    recovered_description = db.describe_staged_revision(
        recovered_second.revision_iri,
        include_current_apply_check=True,
    )
    assert recovered_description.alternative_gate.status == (
        "alternative_to_applied_source"
    )
    assert recovered_description.current_apply_check is not None
    assert recovered_description.current_apply_check.stale_resolution_state == (
        "restaged_successor_ready"
    )
    assert recovered_description.current_apply_check.alternative_gate.status == (
        "alternative_to_applied_source"
    )
    current_work_before_second_apply = db.list_graph_revisions(
        current_staged_work_only=True,
        include_apply_checks=True,
    )
    assert current_work_before_second_apply.count == 1
    assert current_work_before_second_apply.revisions[0].iri == (
        recovered_second.revision_iri
    )
    assert current_work_before_second_apply.revisions[0].alternative_gate.status == (
        "alternative_to_applied_source"
    )
    single_export_path = tmp_path / "ready-successor-applied-alternative-single.md"
    db.export_staged_revision(recovered_second.revision_iri, single_export_path)
    single_export_text = single_export_path.read_text(encoding="utf-8")
    assert "Alternative gate: semantic review required" in single_export_text
    assert first_restaged.revision_iri in single_export_text
    assert result.applied_revision_iri in single_export_text
    applied_alternative_export = db.export_staged_revisions(
        [
            first_restaged.revision_iri,
            second_restaged.revision_iri,
            recovered_second.revision_iri,
        ],
        tmp_path / "ready-successor-applied-alternative.md",
        title="Ready successor with applied alternative",
    )
    applied_alternative_markdown = (
        tmp_path / "ready-successor-applied-alternative.md"
    ).read_text(encoding="utf-8")
    applied_alternative_summary = applied_alternative_export.bundle_summary
    semantic_gate_iris = (
        applied_alternative_summary.ready_restage_successor_alternative_to_applied_source_iris
    )
    assert semantic_gate_iris == [recovered_second.revision_iri]
    recovered_summary = {
        summary.revision_iri: summary
        for summary in applied_alternative_export.revision_summaries
    }[recovered_second.revision_iri]
    assert recovered_summary.alternative_gate.status == (
        "alternative_to_applied_source"
    )
    assert recovered_summary.alternative_gate.semantic_review_required is True
    assert recovered_summary.next_action is not None
    assert recovered_summary.next_action.action_label == (
        "Apply only after semantic review"
    )
    assert first_restaged.revision_iri in recovered_summary.next_action.reason
    assert result.applied_revision_iri in recovered_summary.next_action.reason
    assert applied_alternative_summary.next_action_queue == {
        "inspect_already_applied": [first_restaged.revision_iri],
        "informational": [second_restaged.revision_iri],
        "apply_after_review": [recovered_second.revision_iri],
    }
    assert applied_alternative_summary.next_action_queue_item_counts == {
        "inspect_already_applied": 1,
        "informational": 1,
        "apply_after_review": 1,
    }
    assert applied_alternative_summary.mutation_frontier_iris == [
        recovered_second.revision_iri
    ]
    assert applied_alternative_summary.requires_recheck_after_each_apply is False
    assert applied_alternative_summary.semantic_review_required_queue_counts == {
        "informational": 1,
        "apply_after_review": 1,
    }
    semantic_queue_item = next(
        item
        for item in applied_alternative_summary.next_action_queue_items
        if item.row_iri == recovered_second.revision_iri
    )
    assert semantic_queue_item.queue == "apply_after_review"
    assert semantic_queue_item.resolved_target_iri == recovered_second.revision_iri
    assert semantic_queue_item.row_is_target is True
    assert semantic_queue_item.alternative_gate_status == (
        "alternative_to_applied_source"
    )
    assert semantic_queue_item.alternative_semantic_review_required is True
    assert (
        semantic_queue_item.alternative_applied_source_iri
        == first_restaged.revision_iri
    )
    assert (
        semantic_queue_item.alternative_applied_revision_iri
        == result.applied_revision_iri
    )
    assert any(
        "mechanically apply-ready" in warning
        and "already-applied staged source" in warning
        and recovered_second.revision_iri in warning
        for warning in applied_alternative_summary.warnings
    )
    assert "## Bundle Warnings" in applied_alternative_markdown
    assert "semantic review targets before applying" in applied_alternative_markdown

    second_apply = db.apply_staged_revision(recovered_second.revision_iri)

    assert second_apply.triples_added == 1
    assert second_apply.post_apply_recheck_revision_iris == []
    current_work = db.list_graph_revisions(
        current_staged_work_only=True,
        include_apply_checks=True,
    )
    assert current_work.count == 0


def test_stage_systematisation_preserves_alternative_rdf_framings(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    observation = db.record_observation(
        "Message-like rows repeatedly require identity reasoning.",
        evidence_summary="Synthetic test note backing the staged systematisation.",
        evidence_sources=["test://identity-ladder"],
    )
    before_ontology_count = db.triple_count("ontology")
    before_patterns_count = db.triple_count("patterns")

    ontology_framing = """
    @prefix ex: <https://example.test/project#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:IdentityLadder a rdfs:Class ;
        rdfs:label "Identity ladder" ;
        rdfs:comment "A project-local way to model progressively stronger identity hints." .
    """
    pattern_framing = f"""
    @prefix ex: <https://example.test/project#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:IdentityLadderPattern a rc:Pattern ;
        rdfs:label "Identity ladder pattern" ;
        rc:summary "Identity hints become stronger as more columns agree." ;
        rc:patternText "Repeated message-like rows appear to form a ladder of identity hints rather than one fixed key." ;
        rc:rationale "This may generalise better than forcing every source into a single key model." ;
        rc:patternTarget ex:Messages ;
        rc:supportingObservation <{observation.observation_iri}> ;
        rc:patternStability rc:EmergingPattern .
    """

    draft = db.stage_systematisation(
        summary="Explore identity-ladder modelling",
        intent=(
            "Keep two RDF framings alive while deciding whether this belongs in "
            "project vocabulary or as a pattern first."
        ),
        rationale=(
            "The concept is deliberately awkward: it may need ontology surface "
            "before it can become a map fact."
        ),
        anchors=[observation.observation_iri, "https://example.test/project#Messages"],
        framings=[
            {
                "label": "Project vocabulary term",
                "graph": "ontology",
                "content": ontology_framing,
                "stance": "rc:AlternativeSystematisation",
                "review_note": "This names the concept directly, but it may be premature.",
                "review_recommendation": "Keep as an alternative while more cases accumulate.",
            },
            {
                "label": "Pattern first",
                "graph": "patterns",
                "content": pattern_framing,
                "rationale": (
                    "This keeps the insight tentative while preserving the "
                    "intuition that the map may need a new concept later."
                ),
                "review_note": "This keeps the bold hunch alive without forcing the map.",
                "review_recommendation": "Preferred for now.",
            },
        ],
        validation_scope="all",
    )

    assert draft.result_kind == "systematisation_draft"
    assert draft.summary == "Explore identity-ladder modelling"
    assert draft.profile_route_source_count == 0
    assert draft.anchors == [
        observation.observation_iri,
        "https://example.test/project#Messages",
    ]
    assert len(draft.staged_revisions) == 2
    assert draft.staged_revisions[0].summary == (
        "Explore identity-ladder modelling: Project vocabulary term"
    )
    assert draft.staged_revisions[0].review_note == (
        "This names the concept directly, but it may be premature."
    )
    assert draft.staged_revisions[0].review_recommendation == (
        "Keep as an alternative while more cases accumulate."
    )
    assert draft.staged_revisions[1].summary == (
        "Explore identity-ladder modelling: Pattern first"
    )
    assert draft.staged_revisions[1].review_note == (
        "This keeps the bold hunch alive without forcing the map."
    )
    assert draft.staged_revisions[1].review_recommendation == "Preferred for now."
    assert len(draft.framings) == 2
    assert draft.framings[0].target_graphs == ["ontology"]
    assert draft.framings[1].target_graphs == ["patterns"]
    assert all(framing.validation_conforms for framing in draft.framings)
    assert draft.framings[0].stance == RC + "AlternativeSystematisation"
    assert draft.framings[1].stance == RC + "ExploratoryHunch"
    assert draft.framings[1].review_note == (
        "This keeps the bold hunch alive without forcing the map."
    )
    assert draft.framings[1].review_recommendation == "Preferred for now."
    revision_iris = [revision.revision_iri for revision in draft.staged_revisions]
    assert draft.next_action_queue == {"apply_after_review": revision_iris}
    assert draft.next_action_queue_item_counts == {"apply_after_review": 2}
    assert draft.semantic_review_required_queue_counts == {}
    assert [item.row_iri for item in draft.next_action_queue_items] == revision_iris
    assert [
        item.resolved_target_iri for item in draft.next_action_queue_items
    ] == revision_iris
    assert all(item.row_is_target for item in draft.next_action_queue_items)
    assert [
        item.alternative_set_iris for item in draft.next_action_queue_items
    ] == [revision_iris, revision_iris]
    assert [
        item.alternative_set_source_iri for item in draft.next_action_queue_items
    ] == [revision_iris[0], revision_iris[0]]
    assert [
        item.alternative_set_role for item in draft.next_action_queue_items
    ] == ["source", "alternative"]
    assert draft.suggested_next_actions[0].tool == "doxabase.export_staged_revisions"
    assert draft.suggested_next_actions[0].args["revision_iris"] == revision_iris
    assert draft.suggested_next_actions[0].args["fail_on_sensitive"] is True
    draft_export_path = draft.suggested_next_actions[0].args["path"]
    assert draft_export_path.startswith("/tmp/systematisation-review-")
    assert draft_export_path.endswith(".md")
    assert [
        action.args
        for action in draft.suggested_next_actions
        if action.tool == "doxabase.check_staged_revision_apply"
    ] == [{"iri": revision_iri} for revision_iri in revision_iris]
    first_export_action = next(
        action
        for action in db.check_staged_revision_apply(
            revision_iris[0],
        ).suggested_next_actions
        if action.tool == "doxabase.export_staged_revision"
    )
    second_export_action = next(
        action
        for action in db.check_staged_revision_apply(
            revision_iris[1],
        ).suggested_next_actions
        if action.tool == "doxabase.export_staged_revision"
    )
    first_export_path = first_export_action.args["path"]
    second_export_path = second_export_action.args["path"]
    assert first_export_path.startswith("/tmp/staged-revision-review-")
    assert second_export_path.startswith("/tmp/staged-revision-review-")
    assert first_export_path.endswith(".md")
    assert second_export_path.endswith(".md")
    assert first_export_path != second_export_path
    assert first_export_action.args["fail_on_sensitive"] is True
    assert second_export_action.args["fail_on_sensitive"] is True
    assert db.triple_count("ontology") == before_ontology_count
    assert db.triple_count("patterns") == before_patterns_count

    first = db.describe_staged_revision(draft.staged_revisions[0].revision_iri)
    second = db.describe_staged_revision(draft.staged_revisions[1].revision_iri)
    assert {anchor.iri for anchor in first.revision_anchors} == {
        observation.observation_iri,
        "https://example.test/project#Messages",
    }
    assert {anchor.iri for anchor in second.revision_anchors} == {
        observation.observation_iri,
        "https://example.test/project#Messages",
    }
    assert first.alternative_to is None
    assert second.alternative_to is not None
    assert second.alternative_to.iri == first.iri
    assert "Systematisation intent:" in second.rationale
    assert first.review_recommendation == (
        "Keep as an alternative while more cases accumulate."
    )
    assert second.review_note == "This keeps the bold hunch alive without forcing the map."
    assert second.review_recommendation == "Preferred for now."
    assert "Identity ladder" in first.patches[0].content
    assert "IdentityLadderPattern" in second.patches[0].content
    assert db.validate_graph(scope="all").conforms

    export_path = tmp_path / "identity-ladder-review.md"
    export = db.export_staged_revisions(
        [revision.revision_iri for revision in draft.staged_revisions],
        export_path,
        title="Identity ladder alternatives",
        executive_summary=(
            "Prefer the pattern-first framing for now, while preserving the "
            "ontology alternative as useful pressure on the model."
        ),
    )
    exported = export_path.read_text(encoding="utf-8")

    assert export.revision_iris == [
        revision.revision_iri for revision in draft.staged_revisions
    ]
    assert [item.revision_iri for item in export.revision_summaries] == [
        revision.revision_iri for revision in draft.staged_revisions
    ]
    assert [item.alternative_to for item in export.revision_summaries] == [
        None,
        draft.staged_revisions[0].revision_iri,
    ]
    assert [item.current_alternative_to for item in export.revision_summaries] == [
        None,
        draft.staged_revisions[0].revision_iri,
    ]
    assert [
        item.alternative_set_iris
        for item in export.bundle_summary.next_action_queue_items
    ] == [revision_iris, revision_iris]
    assert [
        item.alternative_set_source_iri
        for item in export.bundle_summary.next_action_queue_items
    ] == [revision_iris[0], revision_iris[0]]
    assert [
        item.alternative_set_role
        for item in export.bundle_summary.next_action_queue_items
    ] == ["source", "alternative"]
    assert export.bundle_summary.changed_graph_counts == {
        "ontology": 1,
        "patterns": 1,
    }
    assert len(export.bundle_summary.choose_one_groups) == 1
    choose_one = export.bundle_summary.choose_one_groups[0]
    assert choose_one.row_indexes == [1, 2]
    assert choose_one.revision_iris == revision_iris
    assert choose_one.alternative_set_source_iri == revision_iris[0]
    assert choose_one.source_row_index == 1
    assert choose_one.alternative_set_roles == ["source", "alternative"]
    assert export.bundle_summary.modelling_choice_summary is not None
    assert "choose-one group" in export.bundle_summary.modelling_choice_summary
    assert [
        row.modelling_role
        for row in export.bundle_summary.modelling_choice_rows
    ] == [
        "vocabulary_or_shape_candidate",
        "pattern_first_alternative",
    ]
    assert [
        row.alternative_set_role
        for row in export.bundle_summary.modelling_choice_rows
    ] == ["source", "alternative"]
    assert [
        row.queue for row in export.bundle_summary.modelling_choice_rows
    ] == ["apply_after_review", "apply_after_review"]
    assert [
        row.support_counts["anchors"]
        for row in export.bundle_summary.modelling_choice_rows
    ] == [2, 2]
    assert "choose-one group" in export.bundle_summary.decision_headline
    assert [item.apply_status for item in export.revision_summaries] == [
        "ready",
        "ready",
    ]
    assert [item.apply_decision for item in export.revision_summaries] == [
        "review_then_apply",
        "review_then_apply",
    ]
    assert [item.current_validation for item in export.revision_summaries] == [
        "True (0 result(s))",
        "True (0 result(s))",
    ]
    assert export.revision_summaries[1].review_recommendation == "Preferred for now."
    assert (
        export.revision_summaries[1].summary_recommendation
        == export.revision_summaries[1].apply_recommended_resolution
    )
    assert (
        export.revision_summaries[1].summary_recommendation_source
        == "apply_recommended_resolution"
    )
    assert (
        export.revision_summaries[1].active_recommendation_field
        == "summary_recommendation"
    )
    assert export.revision_summaries[1].next_action is not None
    assert export.revision_summaries[1].next_action.queue == "apply_after_review"
    assert export.revision_summaries[1].next_action.tool_name == (
        "apply_staged_revision"
    )
    assert export.revision_summaries[1].suggested_next_actions[-1].tool == (
        "doxabase.apply_staged_revision"
    )
    assert export.bytes_written == len(exported.encode("utf-8"))
    assert exported.startswith("# Identity ladder alternatives\n")
    assert "## Review Summary" in exported
    assert "Prefer the pattern-first framing for now" in exported
    assert "## At A Glance" in exported
    assert "- Changed graphs: ontology: 1, patterns: 1" in exported
    assert "- Choose-one groups:" in exported
    assert "## Modelling Choice Summary" in exported
    assert "vocabulary_or_shape_candidate" in exported
    assert "pattern_first_alternative" in exported
    assert exported.index("## At A Glance") < exported.index(
        "## Modelling Choice Summary"
    )
    assert exported.index("## Modelling Choice Summary") < exported.index(
        "## Reviewer Decision Matrix"
    )
    assert "## Reviewer Decision Matrix" in exported
    assert (
        "Rows 1 and 2 are competing alternatives. Apply at most one before "
        "regenerating or rechecking the bundle."
    ) in exported
    assert (
        "| Row | Candidate | Suggested human action | Why | "
        "Authored recommendation |"
    ) in exported
    decision_matrix = exported.split(
        "## Reviewer Decision Matrix",
        1,
    )[1].split("## Summary", 1)[0]
    assert (
        decision_matrix.count("Choose only if this alternative is preferred")
        == 2
    )
    assert "Apply after semantic review" not in decision_matrix
    assert "## Summary" in exported
    assert "Apply status" in exported
    assert "Current validation" in exported
    assert "Staged validation" in exported
    assert "True (0 result(s))" in exported
    assert "review_then_apply" in exported
    assert "Recommendation" in exported
    assert "Preferred for now." in exported
    assert "## Review Notes" in exported
    assert "This keeps the bold hunch alive without forcing the map." in exported
    assert "| 1 | Explore identity-ladder modelling: Project vocabulary term" in exported
    assert "| 2 | Explore identity-ladder modelling: Pattern first" in exported
    assert "## Revision 1: Explore identity-ladder modelling: Project vocabulary term" in exported
    assert "## Revision 2: Explore identity-ladder modelling: Pattern first" in exported
    assert "\n# Explore identity-ladder modelling: Project vocabulary term" not in exported
    assert "\n# Explore identity-ladder modelling: Pattern first" not in exported
    assert "## Alternative To" in exported
    assert "IdentityLadderPattern" in exported

    recovery = db.plan_staged_revision_recovery(revision_iris)
    assert [
        item.alternative_set_iris for item in recovery.next_action_queue_items
    ] == [revision_iris, revision_iris]
    assert [
        item.alternative_set_iris for item in recovery.mutation_frontier_items
    ] == [revision_iris, revision_iris]
    assert [
        item.alternative_set_source_iri
        for item in recovery.mutation_frontier_items
    ] == [revision_iris[0], revision_iris[0]]
    assert [
        item.alternative_set_roles for item in recovery.mutation_frontier_items
    ] == [["source"], ["alternative"]]
    assert [
        lane.next_action_queue_item.alternative_set_role
        for lane in recovery.lanes
        if lane.next_action_queue_item is not None
    ] == ["source", "alternative"]


def test_stage_systematisation_links_relative_framing_alternative(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    first_framing = """
    @prefix ex: <https://example.test/relative-framing#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:CandidateOne rdfs:comment "First candidate framing." .
    """
    second_framing = """
    @prefix ex: <https://example.test/relative-framing#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:CandidateTwo rdfs:comment "Second candidate framing." .
    """

    draft = db.stage_systematisation(
        summary="Compare relative framing alternatives",
        intent="Keep two caller-authored framings grouped without default linking.",
        framings=[
            {
                "label": "First candidate",
                "graph": "map",
                "content": first_framing,
            },
            {
                "label": "Second candidate",
                "graph": "map",
                "content": second_framing,
                "alternative_to_framing_index": 1,
            },
        ],
        link_alternatives=False,
    )

    revision_iris = [revision.revision_iri for revision in draft.staged_revisions]
    assert draft.choose_one_group_count == 1
    assert draft.choose_one_groups[0].revision_iris == revision_iris
    assert [
        item.alternative_set_role for item in draft.next_action_queue_items
    ] == ["source", "alternative"]

    first = db.describe_staged_revision(revision_iris[0])
    second = db.describe_staged_revision(revision_iris[1])

    assert first.alternative_to is None
    assert second.alternative_to is not None
    assert second.alternative_to.iri == first.iri


def test_shared_context_rerun_preserves_reversed_alternative_group(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    shared_ontology = """
    @prefix ex: <https://example.test/reversed-rerun#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:ReviewScope a rdfs:Class ;
        rdfs:label "Review scope" .
    """
    map_framing = """
    @prefix ex: <https://example.test/reversed-rerun#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:MapCandidate rdfs:comment "Map candidate with shared vocabulary." .
    """
    fallback_framing = """
    @prefix ex: <https://example.test/reversed-rerun#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:FallbackCandidate rdfs:comment "Fallback candidate without shared vocabulary." .
    """

    draft = db.stage_systematisation(
        summary="Compare reversed shared-context alternatives",
        intent="Create linked alternatives that need a shared-context rerun.",
        shared_additions=[{"graph": "ontology", "content": shared_ontology}],
        framings=[
            {"label": "Map candidate", "graph": "map", "content": map_framing},
            {
                "label": "Fallback candidate",
                "graph": "map",
                "content": fallback_framing,
            },
        ],
        validation_scope="all",
    )
    revision_iris = [revision.revision_iri for revision in draft.staged_revisions]

    rerun_draft = db.draft_systematisation_shared_context_rerun(
        list(reversed(revision_iris)),
        shared_context_target_revision_iris=[revision_iris[0]],
    )
    rerun_args = rerun_draft.stage_systematisation_arguments

    assert [
        framing.source_revision_iri for framing in rerun_draft.framings
    ] == revision_iris
    assert [framing["label"] for framing in rerun_args["framings"]] == [
        "Map candidate",
        "Fallback candidate",
    ]
    assert rerun_args["link_alternatives"] is False
    assert rerun_args["framings"][1]["alternative_to_framing_index"] == 1

    rerun = db.stage_systematisation(**rerun_args)
    rerun_revision_iris = [
        revision.revision_iri for revision in rerun.staged_revisions
    ]

    assert rerun.choose_one_group_count == 1
    assert rerun.choose_one_groups[0].revision_iris == rerun_revision_iris
    assert rerun.choose_one_groups[0].alternative_set_roles == [
        "source",
        "alternative",
    ]

    export_path = tmp_path / "reversed-shared-context-rerun.md"
    export = db.export_staged_revisions(rerun_revision_iris, export_path)
    exported = export_path.read_text(encoding="utf-8")

    assert len(export.bundle_summary.choose_one_groups) == 1
    assert export.bundle_summary.choose_one_groups[0].revision_iris == (
        rerun_revision_iris
    )
    assert "- Choose-one groups:" in exported
    assert "- Choose-one groups: none" not in exported


def test_stage_systematisation_routes_profile_sources_per_framing(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    status_value_type = "https://example.test/project#OperationalStatusCode"
    evidence = "https://example.test/project#OrdersProfileEvidence"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
    )
    profile = db.record_dataset_profile(
        dataset,
        summary="Orders were profiled for status semantics.",
        evidence_summary="Synthetic profile run for status value-type review.",
        evidence_sources=["test://orders-profile"],
        evidence_iri=evidence,
        sample_size=12,
        sample_scope="All Orders rows.",
        sample_method="Synthetic full-table profile.",
        row_count=12,
        update_map_snapshot=False,
    )
    profile_iri = profile.observation.observation_iri
    route_group_key = "profile-route-group:orders-status-value-type"

    def route_source(step: str, semantic_move: str) -> dict[str, object]:
        return {
            "review_lane": "profile_type_review",
            "route_group_key": route_group_key,
            "route_step_key": f"profile-route-step:{step}",
            "semantic_move": semantic_move,
            "route_anchor_iris": [status_column, status_value_type],
            "duplicate_profile_observation_iris": [profile_iri],
            "type_advisory_indexes": [0],
        }

    define_source = route_source("define-value-type", "define_value_type")
    assert_source = route_source("assert-map-type", "assert_map_type")
    fallback_source = route_source("caveat-fallback", "caveat_fallback")

    draft = db.stage_systematisation(
        summary="Review status value-type alternatives",
        intent=(
            "Compare the direct ontology+map type framing with a pattern-only "
            "fallback for the same profile type finding."
        ),
        anchors=[dataset, status_column, status_value_type],
        supporting_observations=[profile_iri],
        evidence=[evidence],
        framings=[
            {
                "label": "Define and assert value type",
                "additions": [
                    {
                        "graph": "ontology",
                        "content": f"""
                            @prefix rc: <https://richcanopy.org/ns/rc#> .
                            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                            <{status_value_type}> a rc:ValueType ;
                                rdfs:label "Operational status code" .
                        """,
                    },
                    {
                        "graph": "map",
                        "content": f"""
                            @prefix rc: <https://richcanopy.org/ns/rc#> .

                            <{status_column}> rc:valueType <{status_value_type}> .
                        """,
                    },
                ],
                "profile_route_sources": [define_source, assert_source],
            },
            {
                "label": "Pattern-only fallback",
                "graph": "patterns",
                "content": f"""
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    <https://example.test/project#StatusTypeFallbackPattern>
                        a rc:Pattern ;
                        rc:summary "Status values need semantic review." ;
                        rc:patternText "Status codes look domain-specific, but the project value type is not durable yet." ;
                        rc:rationale "Keep the type finding tentative if ontology and map promotion are premature." ;
                        rc:patternTarget <{status_column}> ;
                        rc:supportingObservation <{profile_iri}> .
                """,
                "profileRouteSources": [fallback_source],
            },
        ],
        validation_scope="all",
    )

    assert draft.profile_route_source_count == 3
    review = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        tmp_path / "status-type-review.md",
    )
    candidates = {
        candidate.revision_iri: candidate for candidate in review.candidates
    }
    direct_candidate = candidates[draft.staged_revisions[0].revision_iri]
    fallback_candidate = candidates[draft.staged_revisions[1].revision_iri]
    direct_groups = {
        group["review_lane"]: group for group in direct_candidate.profile_route_groups
    }
    fallback_groups = {
        group["review_lane"]: group
        for group in fallback_candidate.profile_route_groups
    }

    assert direct_groups["profile_type_review"]["match_strength"] == (
        "direct_action"
    )
    assert set(direct_groups["profile_type_review"]["direct_semantic_moves"]) == {
        "define_value_type",
        "assert_map_type",
    }
    assert "caveat_fallback" not in direct_groups["profile_type_review"][
        "direct_semantic_moves"
    ]
    assert fallback_groups["profile_type_review"]["match_strength"] == (
        "direct_action"
    )
    assert fallback_groups["profile_type_review"]["direct_semantic_moves"] == [
        "caveat_fallback"
    ]
    assert "define_value_type" not in fallback_groups["profile_type_review"][
        "direct_semantic_moves"
    ]
    assert "assert_map_type" not in fallback_groups["profile_type_review"][
        "direct_semantic_moves"
    ]
    assert set(review.closed_semantic_moves) == {
        "define_value_type",
        "assert_map_type",
        "caveat_fallback",
    }
    assert review.bulk_apply_allowed is False
    assert review.safe_single_apply_candidate_revision_iris == []
    assert review.semantic_apply_gate_counts["blocked_candidates"] == 2
    assert "semantic_or_support_candidate_present" in (
        review.semantic_apply_gate_blocking_reasons
    )
    assert direct_candidate.semantic_apply_role == "profile_type_candidate"
    assert direct_candidate.semantic_choice_group_key == route_group_key
    assert direct_candidate.apply_cardinality == (
        "one_semantic_choice_then_recheck"
    )
    assert direct_candidate.safe_single_apply_candidate is False
    assert direct_candidate.bulk_apply_allowed is False
    assert fallback_candidate.semantic_apply_role == (
        "semantic_fallback_candidate"
    )
    assert fallback_candidate.semantic_choice_group_key == route_group_key
    assert fallback_candidate.apply_cardinality == (
        "one_semantic_choice_then_recheck"
    )
    exported = (tmp_path / "status-type-review.md").read_text(encoding="utf-8")
    assert "### Semantic Apply Gate" in exported
    assert "Do not bulk apply this profile insight bundle" in exported
    assert "profile_type_candidate" in exported
    assert "semantic_fallback_candidate" in exported


def test_stage_systematisation_warns_on_unusable_profile_route_sources(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    draft = db.stage_systematisation(
        summary="Review route source shape",
        intent="Exercise profile route source validation feedback.",
        profile_route_sources=[
            {
                "tool_name": "describe_query_context",
                "arguments": {"iri": "https://example.test/project#Messages"},
            }
        ],
        framings=[
            {
                "label": "Map dataset",
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Messages a rc:Dataset .
                """,
            }
        ],
    )

    assert draft.profile_route_source_count == 0
    assert any(
        "profile_route_sources was provided" in warning
        for warning in draft.warnings
    )


def test_stage_systematisation_queue_items_surface_applied_alternative_gate(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    source = db.stage_graph_revision(
        summary="Model message rows as raw events",
        rationale="Seed an applied framing for a later systematisation alternative.",
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
    applied = db.apply_staged_revision(source.revision_iri)

    draft = db.stage_systematisation(
        summary="Explore message row alternatives",
        intent="Stage a ready alternative after the event framing was applied.",
        framings=[
            {
                "label": "Conversation entities",
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:MessageThreads a rc:Dataset .
                """,
                "alternative_to": source.revision_iri,
            }
        ],
    )

    revision_iri = draft.staged_revisions[0].revision_iri
    assert draft.next_action_queue == {"apply_after_review": [revision_iri]}
    assert draft.next_action_queue_item_counts == {"apply_after_review": 1}
    assert draft.semantic_review_required_queue_counts == {
        "apply_after_review": 1
    }
    queue_item = draft.next_action_queue_items[0]
    assert queue_item.row_iri == revision_iri
    assert queue_item.resolved_target_iri == revision_iri
    assert queue_item.resolved_target_record_kind == "staged_patch"
    assert queue_item.alternative_gate_status == "alternative_to_applied_source"
    assert queue_item.alternative_semantic_review_required is True
    assert queue_item.alternative_applied_source_iri == source.revision_iri
    assert queue_item.alternative_applied_revision_iri == applied.applied_revision_iri


def test_stage_systematisation_shared_context_validates_each_framing(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_ontology_count = db.triple_count("ontology")
    before_map_count = db.triple_count("map")
    before_patterns_count = db.triple_count("patterns")
    shared_context = """
    @prefix ex: <https://example.test/project#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:OperationalIdentifierInteger a rc:PhysicalType ;
        rdfs:label "operational identifier integer" .
    """
    map_framing = """
    @prefix ex: <https://example.test/project#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:message_mmsi a rc:Column ;
        rdfs:label "Message MMSI" ;
        rc:columnName "mmsi" ;
        rc:physicalType ex:OperationalIdentifierInteger .
    """
    pattern_framing = """
    @prefix ex: <https://example.test/project#> .
    @prefix dcterms: <http://purl.org/dc/terms/> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:operational_identifier_pattern a rc:Pattern ;
        rdfs:label "Operational identifier pattern" ;
        rc:summary "Identifier columns may need scoped reliability semantics." ;
        rc:patternText "The proposed operational identifier type is useful as shared context for map and pattern framings." ;
        rc:rationale "The pattern records the stronger hunch while the map framing tries a concrete column model." ;
        rc:patternTarget ex:message_mmsi ;
        rc:evidence ex:shared_context_evidence ;
        rc:patternStability rc:EmergingPattern .

    ex:shared_context_evidence a rc:Evidence ;
        rc:summary "Synthetic shared-context test evidence." ;
        dcterms:source "tests/test_doxabase_core.py" .
    """

    draft = db.stage_systematisation(
        summary="Explore shared operational identifier context",
        intent=(
            "Use one provisional ontology patch as shared context for a map "
            "candidate and a pattern hunch."
        ),
        anchors=["https://example.test/project#message_mmsi"],
        shared_context_summary=(
            "Define a project-local physical type that the map framing needs "
            "for SHACL validation."
        ),
        shared_additions=[{"graph": "ontology", "content": shared_context}],
        framings=[
            {
                "label": "Concrete map candidate",
                "graph": "map",
                "content": map_framing,
                "stance": "rc:CandidateRevision",
            },
            {
                "label": "Pattern hunch",
                "graph": "patterns",
                "content": pattern_framing,
            },
        ],
        validation_scope="all",
    )

    assert len(draft.staged_revisions) == 2
    assert "Shared proposed context patches" in draft.warnings[0]
    assert [
        warning.warning_code for warning in draft.structured_warnings
    ] == ["shared_semantic_context_applies_to_all_framings"]
    shared_warning = draft.structured_warnings[0]
    assert shared_warning.message in draft.warnings
    assert shared_warning.affected_revision_iris == [
        revision.revision_iri for revision in draft.staged_revisions
    ]
    assert (
        shared_warning.suggested_action
        == "rerun_with_shared_semantic_context_moved_to_framings"
    )
    assert shared_warning.suggested_rerun_arguments == {
        "move_shared_patch_graphs_into_framing_patches": ["ontology"],
        "shared_patch_sources_to_move": [
            {
                "source_argument": "shared_additions",
                "source_index": 0,
                "operation": "addition",
                "graph": "ontology",
            }
        ],
        "target_framing_selection_required": True,
        "target_framing_selection_note": (
            "Choose which framings should receive the moved ontology/shapes "
            "patches. fallback_revision_iris_with_shared_semantic_context is "
            "an inspection subset of later framings currently carrying shared "
            "context, not an automatic drop list."
        ),
    }
    assert shared_warning.fallback_revision_iris_with_shared_semantic_context == [
        draft.staged_revisions[1].revision_iri
    ]
    assert [
        (summary.target_graph, summary.triple_count, summary.count_basis)
        for summary in shared_warning.shared_patch_summaries
    ] == [("ontology", 2, "target_graph_plus_base_ontology")]
    shared_patch_summary = shared_warning.shared_patch_summaries[0]
    assert shared_patch_summary.operation == RC + "AdditionPatch"
    assert shared_patch_summary.operation_label == "addition patch"
    assert shared_patch_summary.patch_role == RC + "SharedContextPatch"
    assert shared_patch_summary.patch_role_label == "shared context patch"
    assert shared_patch_summary.format == "turtle"
    assert db.triple_count("ontology") == before_ontology_count
    assert db.triple_count("map") == before_map_count
    assert db.triple_count("patterns") == before_patterns_count
    assert all(framing.validation_conforms for framing in draft.framings)

    first = db.describe_staged_revision(draft.staged_revisions[0].revision_iri)
    second = db.describe_staged_revision(draft.staged_revisions[1].revision_iri)
    assert set(first.changed_graphs) == {"ontology", "map"}
    assert set(second.changed_graphs) == {"ontology", "patterns"}
    assert [patch.patch_role_label for patch in first.patches] == [
        "shared context patch",
        "framing patch",
    ]
    assert [patch.patch_role_label for patch in second.patches] == [
        "shared context patch",
        "framing patch",
    ]
    assert "Shared proposed context (1 patch(es))" in first.rationale
    export_path = tmp_path / "shared-context-review.md"
    db.export_staged_revision(first.iri, export_path)
    export_text = export_path.read_text()
    assert "Role: shared context patch" in export_text
    assert "Role: framing patch" in export_text


def test_stage_systematisation_shared_shapes_validate_preview_framing(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_map_count = db.triple_count("map")
    before_shapes_count = db.triple_count("shapes")
    shared_ontology = """
    @prefix ex: <https://example.test/project#> .
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:SnapshotStateKey a rdfs:Class ;
        rdfs:label "Snapshot state key" .

    ex:stateTimestampColumn a rdf:Property ;
        rdfs:label "state timestamp column" .
    """
    shared_shape = """
    @prefix ex: <https://example.test/project#> .
    @prefix sh: <http://www.w3.org/ns/shacl#> .

    ex:SnapshotStateKeyShape a sh:NodeShape ;
        sh:targetClass ex:SnapshotStateKey ;
        sh:property [
            sh:path ex:stateTimestampColumn ;
            sh:minCount 1 ;
            sh:nodeKind sh:IRI ;
            sh:message "Snapshot state keys must name a timestamp column."
        ] .
    """
    incomplete_map_framing = """
    @prefix ex: <https://example.test/project#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:incomplete_snapshot_state_key a ex:SnapshotStateKey ;
        rdfs:label "Incomplete snapshot state key" .
    """

    draft = db.stage_systematisation(
        summary="Test staged shape validation",
        intent=(
            "Confirm shared shape patches are active while each framing is "
            "validated."
        ),
        shared_context_summary=(
            "Define provisional snapshot state-key vocabulary and the stricter "
            "shape that candidate map framings must satisfy."
        ),
        shared_additions=[
            {"graph": "ontology", "content": shared_ontology},
            {"graph": "shapes", "content": shared_shape},
        ],
        framings=[
            {
                "label": "Incomplete map candidate",
                "graph": "map",
                "content": incomplete_map_framing,
                "stance": "rc:CandidateRevision",
            }
        ],
        validation_scope="all",
    )

    assert len(draft.staged_revisions) == 1
    assert draft.framings[0].validation_conforms is False
    assert draft.framings[0].validation_result_count > 0
    assert draft.framings[0].validation_results
    framing_result = draft.framings[0].validation_results[0]
    assert framing_result.result_path == "https://example.test/project#stateTimestampColumn"
    assert framing_result.result_path_label == "stateTimestampColumn"
    assert framing_result.source_constraint_component == (
        "http://www.w3.org/ns/shacl#MinCountConstraintComponent"
    )
    assert "Snapshot state keys must name a timestamp column." in framing_result.messages
    assert db.triple_count("map") == before_map_count
    assert db.triple_count("shapes") == before_shapes_count

    description = db.describe_staged_revision(draft.staged_revisions[0].revision_iri)
    assert description.validation_conforms is False
    assert description.validation_result_count > 0
    assert description.validation_results
    result = description.validation_results[0]
    assert result.iri == f"{description.iri}/validation-result/1"
    assert result.focus_node == "https://example.test/project#incomplete_snapshot_state_key"
    assert result.focus_node_label == "incomplete_snapshot_state_key"
    assert result.result_path == "https://example.test/project#stateTimestampColumn"
    assert "Snapshot state keys must name a timestamp column." in result.messages
    assert [patch.patch_role_label for patch in description.patches] == [
        "shared context patch",
        "shared context patch",
        "framing patch",
    ]
    export_path = tmp_path / "failed-shape-review.md"
    db.export_staged_revision(description.iri, export_path)
    export_text = export_path.read_text()
    assert "## Validation Results" in export_text
    assert "Result path: stateTimestampColumn" in export_text
    assert "Snapshot state keys must name a timestamp column." in export_text


def test_shared_context_rerun_warns_when_shapes_leave_invalid_framing(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    shared_ontology = """
    @prefix ex: <https://example.test/project#> .
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:SnapshotStateKey a rdfs:Class ;
        rdfs:label "Snapshot state key" .

    ex:stateTimestampColumn a rdf:Property ;
        rdfs:label "state timestamp column" .
    """
    shared_shape = """
    @prefix ex: <https://example.test/project#> .
    @prefix sh: <http://www.w3.org/ns/shacl#> .

    ex:SnapshotStateKeyShape a sh:NodeShape ;
        sh:targetClass ex:SnapshotStateKey ;
        sh:property [
            sh:path ex:stateTimestampColumn ;
            sh:minCount 1 ;
            sh:nodeKind sh:IRI ;
            sh:message "Snapshot state keys must name a timestamp column."
        ] .
    """
    incomplete_map_framing = """
    @prefix ex: <https://example.test/project#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:incomplete_snapshot_state_key a ex:SnapshotStateKey ;
        rdfs:label "Incomplete snapshot state key" .
    """
    complete_map_framing = """
    @prefix ex: <https://example.test/project#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:complete_snapshot_state_key a ex:SnapshotStateKey ;
        rdfs:label "Complete snapshot state key" ;
        ex:stateTimestampColumn ex:orders_updated_at .
    """

    draft = db.stage_systematisation(
        summary="Compare diagnostic and policy-backed state key framings",
        intent=(
            "Keep a validation diagnostic beside a complete candidate before "
            "moving shared shape context to the selected framing."
        ),
        shared_context_summary=(
            "Define provisional snapshot state-key vocabulary and shape."
        ),
        shared_additions=[
            {"graph": "ontology", "content": shared_ontology},
            {"graph": "shapes", "content": shared_shape},
        ],
        framings=[
            {
                "label": "Diagnostic missing timestamp",
                "graph": "map",
                "content": incomplete_map_framing,
                "stance": "rc:CandidateRevision",
            },
            {
                "label": "Policy-backed candidate",
                "graph": "map",
                "content": complete_map_framing,
                "stance": "rc:CandidateRevision",
            },
        ],
        validation_scope="all",
    )
    revision_iris = [
        revision.revision_iri for revision in draft.staged_revisions
    ]
    assert draft.framings[0].validation_conforms is False
    assert draft.framings[1].validation_conforms is True

    rerun_draft = db.draft_systematisation_shared_context_rerun(
        revision_iris=revision_iris,
        shared_context_target_revision_iris=[revision_iris[1]],
    )

    assert len(rerun_draft.warnings) == 1
    warning = rerun_draft.warnings[0]
    assert revision_iris[0] in warning
    assert "staged validation failures" in warning
    assert "validation context was removed" in warning
    assert "discarded review decision" in warning
    assert [
        (framing.source_revision_iri, framing.receives_shared_context)
        for framing in rerun_draft.framings
    ] == [
        (revision_iris[0], False),
        (revision_iris[1], True),
    ]

