"""Split from test_doxabase_core.py (distillation Phase 2); tests verbatim."""

from tests.core.support_core import *  # noqa: F401,F403


def test_revision_lineage_warns_when_restage_ancestor_lacks_snapshots(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = db.stage_graph_revision(
        summary="Stage daily orders snapshot",
        rationale="Initial candidate before unrelated map drift.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:OrdersDailySnapshot a rc:Dataset .
                """,
            }
        ],
    )
    db.record_map_dataset(
        "https://example.test/project#UnrelatedAuditLog",
        label="Unrelated audit log",
        is_table=True,
    )
    restaged = db.restage_staged_revision(staged.revision_iri)
    applied = db.apply_staged_revision(restaged.revision_iri)
    project_path = tmp_path / "project.trig"
    applied_only_snapshot_path = tmp_path / "applied-only-snapshots.json"
    db.export_trig(project_path, graphs="project")
    applied_only_export = db.export_revision_snapshots(
        applied_only_snapshot_path,
        revision_iris=[applied.applied_revision_iri],
    )

    assert applied_only_export.revision_iris == [
        applied.applied_revision_iri,
        restaged.revision_iri,
    ]

    partial = DoxaBase.create(tmp_path / "partial.sqlite")
    partial.import_trig(project_path)
    partial.import_revision_snapshots(applied_only_snapshot_path)
    partial_lineage = partial.describe_revision_lineage(
        applied.applied_revision_iri,
    )

    assert partial_lineage.restage_chain_iris == [
        staged.revision_iri,
        restaged.revision_iri,
    ]
    assert partial_lineage.selected_revision.snapshot_evidence.status == (
        "history_plus_snapshot_rows"
    )
    assert partial_lineage.paired_revision is not None
    assert partial_lineage.paired_revision.snapshot_evidence.status == (
        "history_plus_snapshot_rows"
    )
    assert any(
        "restage-chain ancestor 1 revision" in warning
        and staged.revision_iri in warning
        and "import a companion revision snapshot JSON bundle" in warning
        for warning in partial_lineage.warnings
    )
    assert not any(
        restaged.revision_iri in warning for warning in partial_lineage.warnings
    )
    grouped_export_path = tmp_path / "partial-snapshot-grouped-review.md"
    partial.export_staged_revisions(
        [staged.revision_iri, restaged.revision_iri],
        grouped_export_path,
        title="Partial snapshot grouped review",
    )
    grouped_export_text = grouped_export_path.read_text(encoding="utf-8")
    assert "## Snapshot Evidence" in grouped_export_text
    assert "history_plus_snapshot_rows: 1" in grouped_export_text
    assert "history_only_count_digest: 1" in grouped_export_text
    assert staged.revision_iri in grouped_export_text
    assert restaged.revision_iri in grouped_export_text
    assert '"kind": "revision_snapshots"' in grouped_export_text
    assert grouped_export_text.index("## Snapshot Evidence") < grouped_export_text.index(
        "## Review Queues"
    )

    full_snapshot_path = tmp_path / "full-chain-snapshots.json"
    full_export = db.export_revision_snapshots(
        full_snapshot_path,
        revision_iris=[applied.applied_revision_iri, staged.revision_iri],
    )
    assert set(full_export.revision_iris) == {
        applied.applied_revision_iri,
        restaged.revision_iri,
        staged.revision_iri,
    }

    recovered = DoxaBase.create(tmp_path / "recovered.sqlite")
    recovered.import_trig(project_path)
    recovered.import_revision_snapshots(full_snapshot_path)
    recovered_lineage = recovered.describe_revision_lineage(
        applied.applied_revision_iri,
    )

    assert recovered_lineage.restage_chain_iris == [
        staged.revision_iri,
        restaged.revision_iri,
    ]
    assert recovered_lineage.warnings == []


def test_restage_staged_revision_refreshes_counts_after_conflict(
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
        review_note="Original note should travel with the refreshed proposal.",
    )
    db.record_map_dataset(
        "https://example.test/project#OtherDataset",
        label="Other dataset",
    )
    stale_check = db.check_staged_revision_apply(staged.revision_iri)
    assert stale_check.status == "conflict"

    restaged = db.restage_staged_revision(staged.revision_iri)

    assert restaged.revision_iri != staged.revision_iri
    assert restaged.patches[0].before_triple_count == db.triple_count("map")
    assert restaged.patches[0].after_triple_count == db.triple_count("map") + 1
    assert restaged.alternative_to is None
    assert restaged.restaged_from == staged.revision_iri
    assert restaged.restage_reason is not None
    assert "prior status conflict" in restaged.restage_reason
    assert restaged.current_restaged_by is None
    assert restaged.status_after == "ready"
    assert restaged.decision_after == "review_then_apply"
    assert restaged.routing_decision_after == "apply_after_review"
    assert restaged.stale_resolution_state_after == "restaged_successor_ready"
    assert restaged.blocking_reasons_after == []
    assert restaged.current_staged_validation_status == "conforms"
    assert restaged.next_action_after is not None
    assert restaged.next_action_after.action_type == "apply_after_review"
    assert restaged.next_action_after.tool_name == "apply_staged_revision"
    assert restaged.next_action_after.arguments == {"iri": restaged.revision_iri}
    assert restaged.next_action_queue_item_after is not None
    assert restaged.next_action_queue_item_after.queue == "apply_after_review"
    assert restaged.next_action_queue_item_after.resolved_target_iri == (
        restaged.revision_iri
    )
    assert restaged.suggested_next_actions_after
    assert restaged.suggested_next_actions_after[-1].tool == (
        "doxabase.apply_staged_revision"
    )
    restaged_description = db.describe_staged_revision(restaged.revision_iri)
    assert restaged_description.restaged_from is not None
    assert restaged_description.restaged_from.iri == staged.revision_iri
    assert restaged_description.restage_reason is not None
    assert "prior status conflict" in restaged_description.restage_reason
    assert "blockers target_count_drift" in restaged_description.restage_reason
    assert restaged_description.review_note == (
        "Original note should travel with the refreshed proposal."
    )
    assert "Restaged stale revision" in (restaged_description.rationale or "")
    assert "Count drift details:" in (restaged_description.rationale or "")
    assert "Snapshot drift details:" in (restaged_description.rationale or "")
    assert "Added since snapshot:" in (restaged_description.rationale or "")
    assert "OtherDataset" in (restaged_description.rationale or "")
    assert "Original staged rationale:" in (restaged_description.rationale or "")
    stale_description = db.describe_staged_revision(staged.revision_iri)
    assert stale_description.restaged_by is not None
    assert stale_description.restaged_by.iri == restaged.revision_iri
    staged_count_after_restage = db.list_graph_revisions(
        revision_type="rc:StagedRevision"
    ).count
    with pytest.raises(DoxaBaseError, match="already has a refreshed"):
        db.restage_staged_revision(staged.revision_iri)
    assert (
        db.list_graph_revisions(revision_type="rc:StagedRevision").count
        == staged_count_after_restage
    )
    stale_export_path = tmp_path / "stale-original-review.md"
    db.export_staged_revision(staged.revision_iri, stale_export_path)
    stale_export_text = stale_export_path.read_text(encoding="utf-8")
    assert "- Restaged by: " in stale_export_text
    assert stale_export_text.index("- Restaged by: ") < stale_export_text.index(
        "## Current Apply Check"
    )
    assert "already has a refreshed successor" in stale_export_text
    assert "instead of restaging the source again" in stale_export_text
    export_path = tmp_path / "restaged-review.md"
    db.export_staged_revision(restaged.revision_iri, export_path)
    export_text = export_path.read_text(encoding="utf-8")
    assert "- Restage headline: " in export_text
    assert export_text.index("- Restage headline: ") < export_text.index(
        "## Current Apply Check"
    )
    assert "- Reason: " in export_text

    grouped_export_path = tmp_path / "restaged-comparison.md"
    grouped_export_record = db.export_staged_revisions(
        [staged.revision_iri, restaged.revision_iri],
        grouped_export_path,
        title="Restaged comparison",
    )
    grouped_export = grouped_export_path.read_text(encoding="utf-8")
    assert [item.revision_iri for item in grouped_export_record.revision_summaries] == [
        staged.revision_iri,
        restaged.revision_iri,
    ]
    stale_summary = grouped_export_record.revision_summaries[0]
    assert stale_summary.apply_status == "conflict"
    assert stale_summary.apply_decision == "restage_against_current_graph"
    assert stale_summary.apply_can_apply is False
    assert stale_summary.apply_blocking_reasons == ["target_count_drift"]
    assert stale_summary.apply_validation_skipped_reason == "conflicts_present"
    assert stale_summary.current_validation == "skipped: conflicts_present"
    assert stale_summary.staged_validation == "True (0 result(s))"
    assert stale_summary.stale_resolution_state == "stale_handled_by_restage"
    assert stale_summary.apply_recommended_resolution is not None
    assert (
        stale_summary.apply_recommendation_scope
        == "prior_source_apply_check_context"
    )
    assert "already has a refreshed successor" in (
        stale_summary.apply_recommended_resolution
    )
    assert restaged.revision_iri in stale_summary.apply_recommended_resolution
    assert "Handled by refreshed successor" in stale_summary.summary_recommendation
    assert (
        stale_summary.summary_recommendation_source
        == "stale_resolution_redirect"
    )
    assert stale_summary.active_recommendation_field == "summary_recommendation"
    assert stale_summary.restaged_by == restaged.revision_iri
    assert stale_summary.suggested_next_actions[-1].tool == (
        "doxabase.describe_revision"
    )
    assert stale_summary.suggested_next_actions[-1].args == {
        "iri": restaged.revision_iri
    }
    restaged_summary = grouped_export_record.revision_summaries[1]
    assert restaged_summary.apply_status == "ready"
    assert restaged_summary.apply_decision == "review_then_apply"
    assert restaged_summary.apply_can_apply is True
    assert restaged_summary.apply_recommendation_scope == "current_apply_check"
    assert restaged_summary.restaged_from == staged.revision_iri
    assert restaged_summary.stale_resolution_state == "restaged_successor_ready"
    assert grouped_export_record.bundle_summary.apply_status_counts == {
        "conflict": 1,
        "ready": 1,
    }
    assert grouped_export_record.bundle_summary.stale_resolution_state_counts == {
        "stale_handled_by_restage": 1,
        "restaged_successor_ready": 1,
    }
    assert grouped_export_record.bundle_summary.unresolved_stale_revision_iris == []
    assert grouped_export_record.bundle_summary.stale_handled_by_restage_revision_iris == [
        staged.revision_iri
    ]
    assert grouped_export_record.bundle_summary.ready_restage_successor_revision_iris == [
        restaged.revision_iri
    ]
    assert grouped_export_record.bundle_summary.post_apply_recheck_revision_iris == []
    assert grouped_export_record.bundle_summary.warnings == []
    assert grouped_export_record.bundle_summary.recommended_review_iris == [
        restaged.revision_iri
    ]
    assert grouped_export_record.bundle_summary.recommended_mutation_review_iris == [
        restaged.revision_iri
    ]
    assert (
        grouped_export_record.bundle_summary.recommended_apply_or_restage_review_iris
        == [restaged.revision_iri]
    )
    assert grouped_export_record.bundle_summary.recommended_repair_review_iris == []
    assert (
        grouped_export_record.bundle_summary.recommended_applied_inspection_iris == []
    )
    assert "## Review Queues" in grouped_export
    assert "## Resolved Targets" in grouped_export
    assert grouped_export.index("## Review Queues") < grouped_export.index(
        "## Resolved Targets"
    )
    assert grouped_export.index("## Resolved Targets") < grouped_export.index(
        "## Restage Context"
    )
    assert (
        "| Queue | Row | Action | Resolved target | Target kind | Row is target | "
        "Semantic risk | Alternative gate |"
    ) in grouped_export
    assert f"`{staged.revision_iri}`" in grouped_export
    assert f"`{restaged.revision_iri}`" in grouped_export
    assert "Inspect current refreshed successor" in grouped_export
    assert "staged_patch | False | none | not_applicable |" in grouped_export
    assert "staged_patch | True | none | not_applicable |" in grouped_export
    assert "## Restage Context" in grouped_export
    assert grouped_export.index("## Restage Context") < grouped_export.index(
        "## Revisions"
    )
    assert "- Recommended review: " in grouped_export
    assert "Handled by refreshed successor; follow Review Queues" in grouped_export
    assert restaged.revision_iri in grouped_export
    assert "prior/source apply-check context:" in grouped_export
    assert "after prior status conflict" in grouped_export
    assert "prior status conflict" in grouped_export

    fresh_check = db.check_staged_revision_apply(restaged.revision_iri)
    assert fresh_check.can_apply is True
    assert fresh_check.status == "ready"
    assert fresh_check.blocking_reasons == []

    stale_check_after = db.check_staged_revision_apply(staged.revision_iri)
    assert stale_check_after.status == "conflict"
    assert stale_check_after.restaged_by == restaged.revision_iri
    assert stale_check_after.current_restaged_by == restaged.revision_iri
    assert stale_check_after.stale_resolution_state == "stale_handled_by_restage"
    assert stale_check_after.summary.startswith(
        "Handled by restage; inspect successor"
    )
    assert restaged.revision_iri in stale_check_after.summary
    assert stale_check_after.next_action is not None
    assert stale_check_after.next_action.arguments == {"iri": restaged.revision_iri}
    assert not any(
        action.tool == "doxabase.restage_staged_revision"
        for action in stale_check_after.suggested_next_actions
    )
    assert stale_check_after.suggested_next_actions[-1].args == {
        "iri": restaged.revision_iri
    }

    result = db.apply_staged_revision(restaged.revision_iri)
    assert result.triples_added == 1
    applied = db.describe_graph_revision(result.applied_revision_iri)
    assert applied.applied_source is not None
    assert applied.applied_source.iri == restaged.revision_iri
    assert applied.applied_source.restaged_from == staged.revision_iri
    assert applied.applied_source.restage_reason is not None
    assert "prior status conflict" in applied.applied_source.restage_reason
    assert applied.applied_source.patch_count == 1
    stale_check_after_apply = db.check_staged_revision_apply(staged.revision_iri)
    assert stale_check_after_apply.status == "conflict"
    assert stale_check_after_apply.restaged_by == restaged.revision_iri
    assert stale_check_after_apply.current_restaged_by == restaged.revision_iri
    assert (
        stale_check_after_apply.stale_resolution_state
        == "stale_handled_by_restage"
    )
    assert result.applied_revision_iri in stale_check_after_apply.summary
    assert stale_check_after_apply.recommended_resolution is not None
    assert result.applied_revision_iri in (
        stale_check_after_apply.recommended_resolution
    )
    assert stale_check_after_apply.next_action is not None
    assert stale_check_after_apply.next_action.action_type == (
        "inspect_already_applied"
    )
    assert stale_check_after_apply.next_action.queue == "inspect_already_applied"
    assert stale_check_after_apply.next_action.tool_name == "describe_revision"
    assert stale_check_after_apply.next_action.arguments == {
        "iri": result.applied_revision_iri
    }
    assert stale_check_after_apply.suggested_next_actions[0].tool == (
        "doxabase.describe_revision"
    )
    assert stale_check_after_apply.suggested_next_actions[0].args == {
        "iri": result.applied_revision_iri
    }
    assert stale_check_after_apply.suggested_next_actions[1].tool == (
        "doxabase.describe_revision"
    )
    assert stale_check_after_apply.suggested_next_actions[1].args == {
        "iri": result.applied_revision_iri,
        "aspect": "applied_diff",
    }
    applied_grouped_export = db.export_staged_revisions(
        [staged.revision_iri, restaged.revision_iri],
        tmp_path / "applied-restaged-comparison.md",
    )
    applied_stale_summary = applied_grouped_export.revision_summaries[0]
    assert applied_stale_summary.next_action is not None
    assert applied_stale_summary.next_action.action_type == (
        "inspect_already_applied"
    )
    assert applied_stale_summary.next_action.arguments == {
        "iri": result.applied_revision_iri
    }
    assert applied_stale_summary.suggested_next_actions[0].tool == (
        "doxabase.describe_revision"
    )
    assert applied_stale_summary.suggested_next_actions[0].args == {
        "iri": result.applied_revision_iri
    }
    assert applied_grouped_export.revision_summaries[1].stale_resolution_state == (
        "restaged_successor_already_applied"
    )
    applied_source_queue_item = next(
        item
        for item in applied_grouped_export.bundle_summary.next_action_queue_items
        if item.row_iri == staged.revision_iri
    )
    assert applied_source_queue_item.queue == "inspect_already_applied"
    assert (
        applied_source_queue_item.resolved_target_iri
        == result.applied_revision_iri
    )
    assert (
        applied_source_queue_item.resolved_target_record_kind
        == "applied_event"
    )
    assert applied_source_queue_item.row_is_target is False
    assert applied_source_queue_item.stale_resolution_state == (
        "stale_handled_by_restage"
    )
    assert applied_grouped_export.bundle_summary.next_action_queue_item_counts == {
        "inspect_already_applied": 2
    }
    assert (
        applied_grouped_export.bundle_summary.semantic_review_required_queue_counts
        == {}
    )
    assert applied_grouped_export.bundle_summary.recommended_mutation_review_iris == []
    assert applied_grouped_export.bundle_summary.recommended_applied_inspection_iris == [
        restaged.revision_iri
    ]
    assert db.describe_dataset("https://example.test/project#Messages").iri == (
        "https://example.test/project#Messages"
    )


def test_restage_staged_revision_preserves_patch_sequence(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    addition_operation = db.expand_iri("rc:AdditionPatch")
    removal_operation = db.expand_iri("rc:RemovalPatch")
    patch_role = db.expand_iri("rc:FramingPatch")

    def ordered_patch(operation: str, content: str) -> dict:
        patch_graph = Graph()
        patch_graph.parse(data=content, format="turtle")
        return {
            "patch_iri": db._mint_iri("graph-patch"),
            "operation": operation,
            "target_graph": "map",
            "format": "turtle",
            "patch_role": patch_role,
            "content": content,
            "graph": patch_graph,
        }

    source = db.stage_graph_revision(
        summary="Replace Orders label",
        rationale="Exercise restage replay of a removal-first patch sequence.",
        validation_scope="all",
        _ordered_patch_specs=[
            ordered_patch(
                removal_operation,
                """
                @prefix ex: <https://example.test/project#> .
                @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                ex:Orders rdfs:label "Orders" .
                """,
            ),
            ordered_patch(
                addition_operation,
                """
                @prefix ex: <https://example.test/project#> .
                @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                ex:Orders rdfs:label "Preferred orders" .
                """,
            ),
        ],
    )

    assert [patch.operation for patch in source.patches] == [
        removal_operation,
        addition_operation,
    ]
    assert db.check_staged_revision_apply(source.revision_iri).status == "ready"
    db.record_map_dataset(
        "https://example.test/project#InterveningDataset",
        label="Intervening dataset",
    )

    restaged = db.restage_staged_revision(source.revision_iri)

    assert [patch.operation for patch in restaged.patches] == [
        removal_operation,
        addition_operation,
    ]
    assert [patch.sequence_index for patch in restaged.patches] == [1, 2]
    assert restaged.patches[0].before_triple_count == db.triple_count("map")
    assert restaged.patches[0].after_triple_count == db.triple_count("map") - 1
    assert restaged.patches[1].before_triple_count == db.triple_count("map") - 1
    assert restaged.patches[1].after_triple_count == db.triple_count("map")
    assert db.check_staged_revision_apply(restaged.revision_iri).status == "ready"


def test_stage_graph_revision_can_record_repaired_restage_successor(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    source = db.stage_graph_revision(
        summary="Stage old orders label",
        rationale="Original stale candidate used a label that later proved wrong.",
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
    db.record_map_dataset(orders, label="Current orders", is_table=True)
    assert db.check_staged_revision_apply(source.revision_iri).status == "conflict"

    repair = db.stage_graph_revision(
        summary="Repair stale orders label",
        rationale=(
            "Caller-authored repair for the stale label candidate; replaces "
            "the current label instead of replaying the old add-only patch."
        ),
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
        restages_revision=source.revision_iri,
        review_recommendation="Review repaired successor before applying.",
    )

    assert repair.restaged_from == source.revision_iri
    assert repair.restage_reason is not None
    assert "Caller-authored repair" in repair.restage_reason
    source_description = db.describe_staged_revision(source.revision_iri)
    assert source_description.restaged_by is not None
    assert source_description.restaged_by.iri == repair.revision_iri
    repair_description = db.describe_staged_revision(repair.revision_iri)
    assert repair_description.restaged_from is not None
    assert repair_description.restaged_from.iri == source.revision_iri
    current_work = db.list_graph_revisions(
        current_staged_work_only=True,
        include_apply_checks=True,
    )
    current_work_iris = {item.iri for item in current_work.revisions}
    assert source.revision_iri not in current_work_iris
    assert repair.revision_iri in current_work_iris
    with pytest.raises(DoxaBaseError, match="already has a refreshed successor"):
        db.stage_graph_revision(
            summary="Parallel repaired successor",
            rationale="This would create an ambiguous successor chain.",
            additions=[
                {
                    "graph": "map",
                    "content": """
                        @prefix ex: <https://example.test/project#> .
                        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                        ex:Orders rdfs:comment "Parallel repair." .
                    """,
                }
            ],
            restages_revision=source.revision_iri,
        )


def test_ready_restage_source_apply_check_redirects_to_successor(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    source = db.stage_graph_revision(
        summary="Stage old orders label",
        rationale="Original candidate is still mechanically ready.",
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
    repair = db.stage_graph_revision(
        summary="Supersede ready source",
        rationale="Caller-authored successor should become the active candidate.",
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
        restages_revision=source.revision_iri,
    )

    source_check = db.check_staged_revision_apply(source.revision_iri)

    assert source_check.can_apply is False
    assert source_check.status == "superseded_by_restage"
    assert source_check.decision == "inspect_current_successor"
    assert source_check.blocking_reasons == ["superseded_by_restage"]
    assert source_check.validation_conforms is True
    assert source_check.suggested_next_actions[0].tool == (
        "doxabase.describe_revision"
    )
    assert source_check.suggested_next_actions[0].args == {
        "iri": repair.revision_iri
    }
    with pytest.raises(DoxaBaseError, match="refreshed successor"):
        db.apply_staged_revision(source.revision_iri)

    described_source = db.describe_staged_revision(
        source.revision_iri,
        include_current_apply_check=True,
    )
    assert described_source.current_apply_check is not None
    assert described_source.current_apply_check.status == "superseded_by_restage"
    assert described_source.current_apply_check.next_action is not None
    assert described_source.current_apply_check.next_action.action_type == (
        "inspect_current_successor"
    )
    assert described_source.current_apply_check.next_action.queue == "informational"
    assert described_source.current_apply_check.next_action.arguments == {
        "iri": repair.revision_iri
    }
    listing = db.list_graph_revisions(
        current_staged_work_only=True,
        include_apply_checks=True,
    )
    assert [item.iri for item in listing.revisions] == [repair.revision_iri]
    export_path = tmp_path / "ready-superseded-review.md"
    export = db.export_staged_revisions(
        [source.revision_iri, repair.revision_iri],
        export_path,
    )
    summaries = {item.revision_iri: item for item in export.revision_summaries}
    assert summaries[source.revision_iri].apply_status == "superseded_by_restage"
    assert summaries[source.revision_iri].suggested_next_actions[0].tool == (
        "doxabase.describe_revision"
    )
    assert summaries[source.revision_iri].suggested_next_actions[0].args == {
        "iri": repair.revision_iri
    }
    assert not any(
        action.tool == "doxabase.apply_staged_revision"
        for action in summaries[source.revision_iri].suggested_next_actions
    )
    assert summaries[repair.revision_iri].apply_status == "ready"
    assert any(
        action.tool == "doxabase.apply_staged_revision"
        for action in summaries[repair.revision_iri].suggested_next_actions
    )
    exported = export_path.read_text(encoding="utf-8")
    source_section = exported.split("## Revision 1: Stage old orders label", 1)[
        1
    ].split(
        "## Revision 2:",
        1,
    )[0]
    assert "**doxabase.describe_revision**" in source_section
    assert "apply_staged_revision" not in source_section
    assert repair.revision_iri in source_section


def test_restage_alternative_gate_detects_applied_sibling_set_member(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    source = db.stage_graph_revision(
        summary="Model order rows as raw events",
        rationale="Keep the first framing as an unapplied comparison anchor.",
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
    lifecycle = db.stage_graph_revision(
        summary="Model order rows as lifecycle entities",
        rationale="A sibling alternative that will be chosen first.",
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
        alternative_to=source.revision_iri,
    )
    snapshot = db.stage_graph_revision(
        summary="Model order rows as snapshot entities",
        rationale="A second sibling alternative staged before the first choice.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:OrderSnapshots a rc:Dataset .
                """,
            }
        ],
        alternative_to=source.revision_iri,
    )

    applied_lifecycle = db.apply_staged_revision(lifecycle.revision_iri)
    stale_snapshot_check = db.check_staged_revision_apply(snapshot.revision_iri)

    assert stale_snapshot_check.status == "conflict"
    assert stale_snapshot_check.alternative_gate.status == (
        "alternative_set_member_applied"
    )
    assert stale_snapshot_check.alternative_gate.applied_source_iri == (
        lifecycle.revision_iri
    )

    restaged_snapshot = db.restage_staged_revision(snapshot.revision_iri)
    restaged_snapshot_check = db.check_staged_revision_apply(
        restaged_snapshot.revision_iri
    )

    assert restaged_snapshot_check.status == "ready"
    assert restaged_snapshot_check.decision == "review_then_apply"
    assert restaged_snapshot_check.alternative_gate.status == (
        "alternative_set_member_applied"
    )
    assert (
        restaged_snapshot_check.alternative_gate.current_alternative_to
        == source.revision_iri
    )
    assert restaged_snapshot_check.alternative_gate.semantic_review_required is True
    assert restaged_snapshot_check.alternative_gate.applied_source_iri == (
        lifecycle.revision_iri
    )
    assert restaged_snapshot_check.alternative_gate.applied_revision_iri == (
        applied_lifecycle.applied_revision_iri
    )
    assert restaged_snapshot_check.next_action is not None
    assert restaged_snapshot_check.next_action.queue == "apply_after_review"
    assert restaged_snapshot_check.next_action.action_label == (
        "Apply only after semantic review"
    )
    assert lifecycle.revision_iri in restaged_snapshot_check.next_action.reason
    assert (
        applied_lifecycle.applied_revision_iri
        in restaged_snapshot_check.next_action.reason
    )

    current_work = db.list_graph_revisions(
        current_staged_work_only=True,
        include_apply_checks=True,
    )
    restaged_item = next(
        item
        for item in current_work.revisions
        if item.iri == restaged_snapshot.revision_iri
    )
    assert restaged_item.alternative_gate.status == "alternative_set_member_applied"
    assert restaged_item.alternative_gate.semantic_review_required is True
    assert restaged_item.alternative_gate.applied_source_iri == (
        lifecycle.revision_iri
    )
    assert current_work.semantic_review_required_queue_counts == {
        "apply_after_review": 1
    }


def test_stale_column_same_slot_drift_keeps_restage_route(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    source = db.stage_graph_revision(
        summary="Add staged orders column",
        rationale="A multi-valued column link should not be inferred as replacement.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders rc:hasColumn ex:StagedColumn .
                """,
            }
        ],
        revision_anchors=[orders],
    )
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:Orders rc:hasColumn ex:CurrentColumn .
        """,
        graph="map",
    )

    check = db.check_staged_revision_apply(source.revision_iri)

    assert check.status == "conflict"
    assert check.decision == "restage_against_current_graph"
    assert check.routing_decision == "restage_after_review"
    assert check.next_action is not None
    assert check.next_action.action_type == "restage_after_review"
    assert check.next_action.tool_name == "restage_staged_revision"
    assert not any(
        (action.tool, action.args.get("kind")) == ("doxabase.stage_revision", "map_assertion")
        for action in check.suggested_next_actions
    )


def test_batch_restage_skips_row_semantics_same_slot_replacement(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    source = db.stage_graph_revision(
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

    dry_run = db.restage_staged_revisions([source.revision_iri], dry_run=True)

    assert dry_run.would_restage_revision_iris == []
    assert dry_run.restaged_revision_iris == []
    assert dry_run.skipped_revision_iris == [source.revision_iri]
    assert dry_run.not_restageable_revision_iris == [source.revision_iri]
    assert dry_run.not_restageable_revision_iris_by_reason == {
        "same_slot_replacement": [source.revision_iri]
    }
    dry_item = dry_run.items[0]
    assert dry_item.action == "skipped_not_restageable"
    assert dry_item.not_restageable_reason == "same_slot_replacement"
    assert dry_item.status_before == "conflict"
    assert dry_item.decision_before == "restage_against_current_graph"
    assert dry_item.routing_decision_before == "stage_same_slot_replacement"
    assert dry_item.status_after == "conflict"
    assert dry_item.decision_after == "restage_against_current_graph"
    assert dry_item.routing_decision_after == "stage_same_slot_replacement"
    assert dry_item.current_revision_iri == source.revision_iri
    assert dry_item.restaged_revision_iri is None
    assert dry_item.next_action_after is not None
    assert dry_item.next_action_after.queue == "repair_or_replace"
    assert dry_item.next_action_after.tool_name == "stage_revision"
    assert dry_item.next_action_after.arguments.get("kind") == "map_assertion"
    assert "repair or replacement" in dry_item.note
    assert any(
        (action.tool, action.args.get("kind")) == ("doxabase.stage_revision", "map_assertion")
        for action in dry_item.suggested_next_actions_after
    )

    batch = db.restage_staged_revisions([source.revision_iri])

    assert batch.would_restage_revision_iris == []
    assert batch.restaged_revision_iris == []
    assert batch.skipped_revision_iris == [source.revision_iri]
    assert batch.not_restageable_revision_iris_by_reason == {
        "same_slot_replacement": [source.revision_iri]
    }
    assert batch.current_revision_by_source == {
        source.revision_iri: source.revision_iri
    }
    description = db.describe_staged_revision(source.revision_iri)
    assert description.restaged_by is None
    assert batch.bundle_summary.next_action_queue == {
        "repair_or_replace": [source.revision_iri]
    }
    assert batch.bundle_summary.recommended_repair_review_iris == [
        source.revision_iri
    ]
    assert (
        "stage_revision map_assertion replacement"
        in batch.revision_summaries[0].apply_recommended_resolution
    )


def test_stale_authored_replacement_keeps_restage_route_when_removal_still_matters(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(
        orders,
        label="Orders",
        is_table=True,
        row_semantics="rc:EventRow",
    )
    source = db.stage_map_assertion_change(
        subject=orders,
        predicate="rc:rowSemantics",
        object="rc:SnapshotRow",
        change_kind="replace",
        rationale="Original replacement before another route added the target.",
    )
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:Orders rc:rowSemantics rc:SnapshotRow .
        """,
        graph="map",
    )

    check = db.check_staged_revision_apply(source.staged_revision.revision_iri)

    assert check.status == "conflict"
    assert check.next_action is not None
    assert check.next_action.action_type == "restage_after_review"
    assert check.next_action.tool_name == "restage_staged_revision"
    assert not any(
        (action.tool, action.args.get("kind")) == ("doxabase.stage_revision", "map_assertion")
        for action in check.suggested_next_actions
    )
    by_operation = {patch.operation: patch for patch in check.patch_checks}
    addition_patch = by_operation[db.expand_iri("rc:AdditionPatch")]
    removal_patch = by_operation[db.expand_iri("rc:RemovalPatch")]
    assert addition_patch.already_present_triples == 1
    assert addition_patch.effective_triples_to_add == 0
    assert removal_patch.already_present_triples == 1
    assert removal_patch.effective_triples_to_remove == 1


@pytest.mark.parametrize(
    ("setup", "subject", "predicate", "staged_object", "current_object"),
    [
        (
            "dataset",
            "https://example.test/project#Orders",
            "rc:rowCountSnapshot",
            "10",
            "12",
        ),
        (
            "dataset",
            "https://example.test/project#Orders",
            "rdfs:label",
            '"Staged orders"',
            '"Current orders"',
        ),
        (
            "column",
            "https://example.test/project#orders__status",
            "rdfs:label",
            '"Staged status"',
            '"Current status"',
        ),
        (
            "column",
            "https://example.test/project#orders__status",
            "rc:schemaStability",
            "rc:FixedSchema",
            "rc:VariableSchema",
        ),
        (
            "dataset",
            "https://example.test/project#Orders",
            "rc:physicalType",
            "rc:Double",
            "rc:Varchar",
        ),
        (
            "dataset",
            "https://example.test/project#Orders",
            "rc:nullable",
            "true",
            "false",
        ),
        (
            "untyped",
            "https://example.test/project#Untyped",
            "rc:physicalType",
            "rc:Double",
            "rc:Varchar",
        ),
    ],
)
def test_same_slot_replacement_guarded_negatives_keep_restage_route(
    tmp_path: Path,
    setup: str,
    subject: str,
    predicate: str,
    staged_object: str,
    current_object: str,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    if setup == "dataset":
        db.record_map_dataset(subject, is_table=True)
    elif setup == "column":
        db.record_map_column(subject, column_name="status")
    source = db.stage_graph_revision(
        summary="Stage guarded negative assertion",
        rationale="This same-slot shape should stay on the restage route.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    <{subject}> {predicate} {staged_object} .
                """,
            }
        ],
        revision_anchors=[subject],
    )
    db.import_turtle(
        f"""
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        <{subject}> {predicate} {current_object} .
        """,
        graph="map",
    )

    check = db.check_staged_revision_apply(source.revision_iri)

    assert check.status == "conflict"
    assert check.next_action is not None
    assert check.next_action.queue == "restage_after_review"
    assert not any(
        (action.tool, action.args.get("kind")) == ("doxabase.stage_revision", "map_assertion")
        for action in check.suggested_next_actions
    )


def test_restaged_revision_with_realized_addition_reports_noop(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = db.stage_graph_revision(
        summary="Stage messages dataset",
        rationale="Exercise restage when another route already added the fact.",
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

    stale_check = db.check_staged_revision_apply(staged.revision_iri)
    assert stale_check.status == "conflict"
    assert stale_check.decision == "restage_against_current_graph"
    assert stale_check.summary.startswith("Already-effective stale source")
    assert stale_check.effective_delta_summary.already_effective is True
    assert stale_check.effective_delta_summary.total_effective_triples_to_add == 0
    assert stale_check.effective_delta_summary.blocked_patch_triples_to_add == 0
    assert stale_check.effective_delta_summary.patch_triple_status_counts == {
        "all_patch_triples_present": 1,
    }
    assert stale_check.already_applied_by is None
    assert stale_check.next_action is not None
    assert stale_check.next_action.action_type == "inspect_no_effective_change"
    assert stale_check.next_action.queue == "informational"
    assert stale_check.next_action.tool_name == "describe_revision"
    assert stale_check.next_action.arguments == {
        "iri": staged.revision_iri,
        "include_current_apply_check": True,
    }
    assert stale_check.recommended_resolution is not None
    assert "no effective delta" in stale_check.recommended_resolution
    assert not any(
        action.tool == "doxabase.restage_staged_revision"
        for action in stale_check.suggested_next_actions
    )
    assert stale_check.count_drifts[0].patch_triple_status == (
        "all_patch_triples_present"
    )
    dry_run = db.restage_staged_revisions([staged.revision_iri], dry_run=True)
    assert dry_run.would_restage_revision_iris == []
    assert dry_run.restaged_revision_iris == []
    assert dry_run.not_restageable_revision_iris_by_reason == {
        "already_effective": [staged.revision_iri]
    }
    dry_item = dry_run.items[0]
    assert dry_item.action == "skipped_not_restageable"
    assert dry_item.not_restageable_reason == "already_effective"
    assert dry_item.status_before == "conflict"
    assert dry_item.status_after == "conflict"
    assert dry_item.next_action_after is not None
    assert dry_item.next_action_after.action_type == "inspect_no_effective_change"
    assert dry_item.next_action_after.queue == "informational"
    assert dry_run.bundle_summary.next_action_queue == {
        "informational": [staged.revision_iri]
    }
    assert dry_run.bundle_summary.recommended_mutation_review_iris == []

    with pytest.raises(DoxaBaseError, match="already-effective stale source"):
        db.restage_staged_revision(staged.revision_iri)

    export = db.export_staged_revisions(
        [staged.revision_iri],
        tmp_path / "already-effective-stale-review.md",
    )
    summary = export.revision_summaries[0]
    assert summary.apply_status == "conflict"
    assert summary.next_action is not None
    assert summary.next_action.action_type == "inspect_no_effective_change"
    assert export.bundle_summary.post_apply_recheck_revision_iris == []
    assert export.bundle_summary.recommended_mutation_review_iris == []
    assert export.bundle_summary.recommended_apply_or_restage_review_iris == []
    assert export.bundle_summary.recommended_repair_review_iris == []
    exported_text = (tmp_path / "already-effective-stale-review.md").read_text(
        encoding="utf-8"
    )
    assert "Effective +" in exported_text
    assert "Inspect already-effective stale source" in exported_text
    assert (
        "| 1 | Stage messages dataset | Inspect already-effective stale source |"
        in exported_text
    )

    resolution = db.record_staged_revision_review_decision(
        staged.revision_iri,
        decision="no_effective_change",
        rationale=(
            "Reviewed the stale source and confirmed the same fact already "
            "exists in the current map, so there is no useful staged mutation "
            "left to perform."
        ),
        created_at="2026-06-01T10:05:00Z",
        review_note="Closed after comparing patch-triple presence.",
    )

    assert resolution.staged_revision_iri == staged.revision_iri
    assert resolution.decision == "no_effective_change"
    assert resolution.decision_iri == RC + "NoEffectiveChangeDecision"
    assert resolution.current_application_status == "conflict"
    assert resolution.current_next_action is not None
    assert resolution.current_next_action.action_type == "inspect_no_effective_change"
    assert resolution.closes_current_staged_work is True
    assert [
        action.tool.removeprefix("doxabase.") for action in resolution.suggested_next_actions
    ] == [
        "describe_revision",
        "describe_revision",
        "plan_staged_revision_recovery",
    ]

    decision_event = db.describe_graph_revision(resolution.resolution_revision_iri)
    assert decision_event.record_kind == "staged_review_resolution"
    assert decision_event.revision_type == RC + "StagedRevisionReviewResolution"
    assert decision_event.resolves_staged_revision == staged.revision_iri
    assert decision_event.staged_review_decision == RC + "NoEffectiveChangeDecision"
    assert decision_event.staged_review_decision_label == "no effective change"

    resolved_description = db.describe_staged_revision(staged.revision_iri)
    assert resolved_description.review_resolution is not None
    assert resolved_description.review_resolution.decision == "no_effective_change"
    assert (
        resolved_description.review_resolution.resolution_revision_iri
        == resolution.resolution_revision_iri
    )

    full_listing = db.list_graph_revisions(
        revision_type="rc:StagedRevision",
        include_apply_checks=True,
    )
    resolved_item = next(
        item for item in full_listing.revisions if item.iri == staged.revision_iri
    )
    assert resolved_item.is_current_staged_work is False
    assert resolved_item.not_current_staged_work_reason == "review_resolved"
    assert resolved_item.review_resolution is not None
    assert resolved_item.review_resolution.decision == "no_effective_change"
    assert resolved_item.application_status == "conflict"

    current_work = db.list_graph_revisions(
        revision_type="rc:StagedRevision",
        current_staged_work_only=True,
    )
    assert staged.revision_iri not in [item.iri for item in current_work.revisions]

    current_plan = db.plan_staged_revision_recovery(current_staged_work_only=True)
    assert staged.revision_iri not in current_plan.processed_revision_iris


def test_restaged_revision_reports_effective_delta_for_mixed_addition(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = db.stage_graph_revision(
        summary="Stage messages and threads datasets",
        rationale="Exercise restage when part of the patch already exists.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Messages a rc:Dataset .
                    ex:Threads a rc:Dataset .
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

    stale_check = db.check_staged_revision_apply(staged.revision_iri)
    assert stale_check.status == "conflict"
    assert stale_check.count_drifts[0].patch_triple_status == (
        "mixed_patch_triples_present"
    )

    restaged = db.restage_staged_revision(staged.revision_iri)
    check = db.check_staged_revision_apply(restaged.revision_iri)

    assert check.status == "ready"
    assert check.can_apply is True
    assert check.triples_to_add == 1
    assert check.triples_to_remove == 0
    assert check.summary == (
        "Ready to apply 1 patch(es) across map: +1 triple(s), -0 triple(s)."
    )
    patch_check = check.patch_checks[0]
    assert patch_check.effective_triples_to_add == 1
    assert patch_check.effective_triples_to_remove == 0
    assert patch_check.already_present_triples == 1
    assert patch_check.already_absent_triples == 1

    result = db.apply_staged_revision(restaged.revision_iri)

    assert result.triples_added == 1
    assert db.describe_dataset("https://example.test/project#Threads").iri == (
        "https://example.test/project#Threads"
    )


def test_batch_restage_preserves_source_patch_sequences(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    shipments = "https://example.test/project#Shipments"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    db.record_map_dataset(shipments, label="Shipments", is_table=True)
    addition_operation = db.expand_iri("rc:AdditionPatch")
    removal_operation = db.expand_iri("rc:RemovalPatch")
    patch_role = db.expand_iri("rc:FramingPatch")

    def ordered_patch(operation: str, content: str) -> dict:
        patch_graph = Graph()
        patch_graph.parse(data=content, format="turtle")
        return {
            "patch_iri": db._mint_iri("graph-patch"),
            "operation": operation,
            "target_graph": "map",
            "format": "turtle",
            "patch_role": patch_role,
            "content": content,
            "graph": patch_graph,
        }

    removal_first = db.stage_graph_revision(
        summary="Replace Orders label",
        rationale="Removal-first source should remain removal-first after batch restage.",
        validation_scope="all",
        _ordered_patch_specs=[
            ordered_patch(
                removal_operation,
                """
                @prefix ex: <https://example.test/project#> .
                @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                ex:Orders rdfs:label "Orders" .
                """,
            ),
            ordered_patch(
                addition_operation,
                """
                @prefix ex: <https://example.test/project#> .
                @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                ex:Orders rdfs:label "Preferred orders" .
                """,
            ),
        ],
    )
    interleaved = db.stage_graph_revision(
        summary="Change Shipments label and type",
        rationale="Interleaved source should preserve all patch positions.",
        validation_scope="all",
        _ordered_patch_specs=[
            ordered_patch(
                addition_operation,
                """
                @prefix ex: <https://example.test/project#> .
                @prefix rc: <https://richcanopy.org/ns/rc#> .

                ex:Shipments a rc:SnapshotDataset .
                """,
            ),
            ordered_patch(
                removal_operation,
                """
                @prefix ex: <https://example.test/project#> .
                @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                ex:Shipments rdfs:label "Shipments" .
                """,
            ),
            ordered_patch(
                addition_operation,
                """
                @prefix ex: <https://example.test/project#> .
                @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                ex:Shipments rdfs:label "Daily shipments" .
                """,
            ),
        ],
    )
    db.record_map_dataset(
        "https://example.test/project#InterveningDataset",
        label="Intervening dataset",
    )

    batch = db.restage_staged_revisions(
        [removal_first.revision_iri, interleaved.revision_iri]
    )
    by_source = batch.restaged_revision_by_source
    restaged_removal_first = db.describe_staged_revision(
        by_source[removal_first.revision_iri]
    )
    restaged_interleaved = db.describe_staged_revision(
        by_source[interleaved.revision_iri]
    )

    assert [item.action for item in batch.items] == ["restaged", "restaged"]
    assert [patch.operation for patch in restaged_removal_first.patches] == [
        removal_operation,
        addition_operation,
    ]
    assert [patch.sequence_index for patch in restaged_removal_first.patches] == [
        1,
        2,
    ]
    assert [patch.operation for patch in restaged_interleaved.patches] == [
        addition_operation,
        removal_operation,
        addition_operation,
    ]
    assert [patch.sequence_index for patch in restaged_interleaved.patches] == [
        1,
        2,
        3,
    ]
    assert all(item.status_after == "ready" for item in batch.items)
    assert batch.bundle_summary.next_action_queue == {
        "apply_after_review": [
            by_source[removal_first.revision_iri],
            by_source[interleaved.revision_iri],
        ],
        "informational": [
            removal_first.revision_iri,
            interleaved.revision_iri,
        ],
    }
    assert {
        action.args["iri"]
        for action in batch.suggested_next_actions
        if action.tool == "doxabase.apply_staged_revision"
    } == {
        by_source[removal_first.revision_iri],
        by_source[interleaved.revision_iri],
    }


def test_batch_restage_dry_run_reports_plan_without_creating_successors(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    applied_staged = db.stage_graph_revision(
        summary="Stage applied table",
        rationale="Exercise already-applied dry-run classification.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:AlreadyApplied a rc:Dataset .
                """,
            }
        ],
    )
    db.apply_staged_revision(applied_staged.revision_iri)
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
    validation_failed = db.stage_graph_revision(
        summary="Stage invalid value type",
        rationale="Exercise validation-failed dry-run classification.",
        additions=[
            {
                "graph": "ontology",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:BadValueType a rc:ValueType ;
                        rc:requiredPhysicalType "VARCHAR" .
                """,
            }
        ],
        validation_scope="all",
    )
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
    staged_count_before = db.list_graph_revisions(
        revision_type="rc:StagedRevision"
    ).count
    total_revision_count_before = db.list_graph_revisions().count
    history_triples_before = db.triple_count("history")
    export_path = tmp_path / "dry-run-batch-review.md"

    batch = db.restage_staged_revisions(
        [
            first.revision_iri,
            second.revision_iri,
            validation_failed.revision_iri,
            applied_staged.revision_iri,
            ready.revision_iri,
        ],
        path=export_path,
        title="Dry-run batch review",
        dry_run=True,
    )

    assert batch.dry_run is True
    assert [item.action for item in batch.items] == [
        "skipped_already_handled",
        "would_restage",
        "skipped_not_restageable",
        "skipped_not_restageable",
        "skipped_not_restageable",
    ]
    assert batch.would_restage_revision_iris == [second.revision_iri]
    assert batch.restaged_revision_iris == []
    assert batch.restaged_revision_by_source == {}
    assert batch.current_revision_by_source == {
        first.revision_iri: already_restaged.revision_iri,
        second.revision_iri: second.revision_iri,
        validation_failed.revision_iri: validation_failed.revision_iri,
        applied_staged.revision_iri: applied_staged.revision_iri,
        ready.revision_iri: ready.revision_iri,
    }
    assert batch.skipped_revision_iris == [
        first.revision_iri,
        validation_failed.revision_iri,
        applied_staged.revision_iri,
        ready.revision_iri,
    ]
    assert batch.already_handled_revision_iris == [first.revision_iri]
    assert batch.not_restageable_revision_iris == [
        validation_failed.revision_iri,
        applied_staged.revision_iri,
        ready.revision_iri,
    ]
    assert batch.not_restageable_revision_iris_by_reason == {
        "validation_failed": [validation_failed.revision_iri],
        "already_applied": [applied_staged.revision_iri],
        "ready": [ready.revision_iri],
    }
    assert [item.not_restageable_reason for item in batch.items] == [
        None,
        None,
        "validation_failed",
        "already_applied",
        "ready",
    ]
    assert batch.review_revision_iris == [
        first.revision_iri,
        already_restaged.revision_iri,
        second.revision_iri,
        validation_failed.revision_iri,
        applied_staged.revision_iri,
        ready.revision_iri,
    ]
    assert batch.bundle_summary.unresolved_stale_revision_iris == [
        second.revision_iri
    ]
    assert batch.bundle_summary.validation_failed_revision_iris == [
        validation_failed.revision_iri
    ]
    assert [action.tool.removeprefix("doxabase.") for action in batch.suggested_next_actions] == [
        "restage_staged_revision"
    ]
    assert batch.suggested_next_actions[0].args == {
        "revision_iris": [second.revision_iri],
        "dry_run": False,
    }
    assert batch.export_record is not None
    assert batch.export_record.path == str(export_path)
    assert export_path.read_text(encoding="utf-8").startswith(
        "# Dry-run batch review\n"
    )
    assert "Dry run" in batch.items[1].note
    assert db.describe_staged_revision(second.revision_iri).restaged_by is None
    assert (
        db.list_graph_revisions(revision_type="rc:StagedRevision").count
        == staged_count_before
    )
    assert db.list_graph_revisions().count == total_revision_count_before
    assert db.triple_count("history") == history_triples_before


def test_batch_restage_items_report_validation_failed_successor_status(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    stale = db.stage_graph_revision(
        summary="Stage invalid value type",
        rationale="Exercise restaged successor status for invalid proposals.",
        additions=[
            {
                "graph": "ontology",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:BadValueType a rc:ValueType ;
                        rc:requiredPhysicalType "VARCHAR" .
                """,
            }
        ],
        validation_scope="all",
    )
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:OntologyDrift a rdfs:Class .
        """,
        graph="ontology",
    )

    batch = db.restage_staged_revisions([stale.revision_iri])

    successor_iri = batch.restaged_revision_iris[0]
    item = batch.items[0]
    assert item.action == "restaged"
    assert item.restaged_revision_iri == successor_iri
    assert item.current_revision_iri == successor_iri
    assert item.status_before == "conflict"
    assert item.source_staged_validation_status == "failed"
    assert item.source_validation_result_count == 1
    assert item.status_after == "validation_failed"
    assert item.decision_after == "inspect_validation_results"
    assert item.stale_resolution_state_after == "restaged_successor_not_ready"
    assert item.blocking_reasons_after == ["validation_failed"]
    assert item.current_staged_validation_status == "failed"
    assert item.current_validation_result_count == 1
    assert item.triples_to_add_after > 0
    assert item.triples_to_remove_after == 0
    assert "current revision fails validation" in item.note
    assert "stage a repaired or alternative candidate" in item.note
    assert "stage_revision map_assertion replacement" in item.note
    assert item.repair_first_warning is not None
    assert "Repair-first warning" in item.repair_first_warning
    assert "same-payload mechanical restage" in item.repair_first_warning
    assert item.repair_first_warning in item.note
    assert item.next_action_after is not None
    assert item.next_action_after.action_type == "repair_or_replace"
    assert item.next_action_after.queue == "repair_or_replace"
    assert item.next_action_after.tool_name == "restage_staged_revision"
    assert item.next_action_after.arguments.get("dry_run") is True
    assert item.next_action_after.arguments == {
        "revision_iris": successor_iri,
        "dry_run": True,
        "validation_scope": "all",
    }
    assert item.suggested_next_actions_after[0].tool == (
        "doxabase.restage_staged_revision"
    )
    assert item.suggested_next_actions_after[0].args.get("dry_run") is True
    successor_check = db.check_staged_revision_apply(successor_iri)
    assert successor_check.recommended_resolution is not None
    assert "removal+addition" in successor_check.recommended_resolution
    assert "stage_revision map_assertion replacement" in (
        successor_check.recommended_resolution
    )
    assert batch.bundle_summary.apply_status_counts == {
        "conflict": 1,
        "validation_failed": 1,
    }
    assert batch.bundle_summary.ready_restage_successor_revision_iris == []
    assert batch.bundle_summary.post_apply_recheck_revision_iris == []
    assert batch.bundle_summary.validation_failed_revision_iris == [successor_iri]
    assert batch.bundle_summary.recommended_mutation_review_iris == [successor_iri]
    assert batch.bundle_summary.recommended_apply_or_restage_review_iris == []
    assert batch.bundle_summary.recommended_repair_review_iris == [successor_iri]


def test_restage_from_staged_validation_failure_routes_to_repair_when_current_state_fills_gap(
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

        ft:TemporalInterpretationScope a rdfs:Class ;
            rdfs:label "Temporal interpretation scope" .

        ft:clockColumn a rdf:Property ;
            rdfs:label "clock column" .

        ft:timezoneEvidenceColumn a rdf:Property ;
            rdfs:label "timezone evidence column" .
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
                sh:nodeKind sh:IRI ;
                sh:message "Temporal scopes must name timezone evidence."
            ] .
        """,
        graph="shapes",
    )
    source = db.stage_graph_revision(
        summary="Stage incomplete temporal scope",
        rationale=(
            "Regression test: this source failed staged-time validation because "
            "the framing omitted timezone evidence."
        ),
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
    assert source.validation_conforms is False
    db.import_turtle(
        f"""
        @prefix ft: <https://example.test/project/systematisation#> .

        <{scope}> ft:timezoneEvidenceColumn <{timezone}> .
        """,
        graph="map",
    )
    stale_check = db.check_staged_revision_apply(source.revision_iri)
    assert stale_check.status == "conflict"
    assert stale_check.blocking_reasons == ["target_count_drift"]

    dry_run = db.restage_staged_revisions([source.revision_iri], dry_run=True)
    dry_item = dry_run.items[0]
    assert dry_item.action == "would_restage"
    assert dry_run.would_restage_revision_iris == []
    assert dry_run.repair_first_revision_iris == [source.revision_iri]
    assert dry_run.repair_or_replace_source_revision_iris == [source.revision_iri]
    assert dry_item.source_staged_validation_status == "failed"
    assert dry_item.routing_decision_after == "repair_or_replace"
    assert dry_item.next_action_after is not None
    assert dry_item.next_action_after.queue == "repair_or_replace"
    assert any(
        (action.tool, action.args.get("dry_run")) == ("doxabase.restage_staged_revision", True)
        for action in dry_item.suggested_next_actions_after
    )
    assert not any(
        action.tool == "doxabase.restage_staged_revision"
        and action.args.get("dry_run") is not True
        for action in dry_item.suggested_next_actions_after
    )
    assert dry_item.repair_first_warning is not None
    assert "Repair-first warning" in dry_item.repair_first_warning
    assert "same-payload mechanical restage" in dry_item.repair_first_warning
    assert dry_item.repair_first_warning in dry_item.note

    conflict_export = db.export_staged_revisions(
        [source.revision_iri],
        tmp_path / "staged-validation-conflict-review.md",
    )
    conflict_summary = conflict_export.revision_summaries[0]
    assert conflict_summary.apply_status == "conflict"
    assert conflict_summary.apply_decision == "restage_against_current_graph"
    assert conflict_summary.next_action is not None
    assert conflict_summary.next_action.queue == "repair_or_replace"
    assert conflict_summary.summary_recommendation == (
        "Stored staged-time validation failed; inspect validation diagnostics "
        "and stage a repaired or alternative proposal before restaging or "
        "applying this row."
    )
    assert (
        conflict_summary.summary_recommendation_source
        == "staged_validation_repair_route"
    )
    conflict_markdown = (
        tmp_path / "staged-validation-conflict-review.md"
    ).read_text(encoding="utf-8")
    assert "Repair or discard" in conflict_markdown
    assert "Stored staged-time validation failed" in conflict_markdown

    restaged = db.restage_staged_revision(source.revision_iri)
    check = db.check_staged_revision_apply(restaged.revision_iri)

    assert restaged.validation_conforms is True
    assert check.status == "ready"
    assert check.can_apply is True
    assert check.validation_conforms is True
    assert check.decision == "inspect_restaged_source_validation_failure"
    assert check.next_action is not None
    assert check.next_action.action_type == "repair_or_replace"
    assert check.next_action.queue == "repair_or_replace"
    assert check.next_action.tool_name == "describe_revision"
    assert not any(
        action.tool == "doxabase.apply_staged_revision"
        for action in check.suggested_next_actions
    )
    warning = (
        "The restaged source failed staged-time validation with 1 result(s)"
    )
    assert any(warning in reason for reason in check.semantic_risk_reasons)
    assert check.recommended_resolution is not None
    assert warning in check.recommended_resolution

    batch = db.restage_staged_revisions([restaged.revision_iri], dry_run=True)
    assert batch.items[0].action == "skipped_not_restageable"
    assert batch.items[0].not_restageable_reason == (
        "inspect_restaged_source_validation_failure"
    )
    assert batch.items[0].next_action_after is not None
    assert batch.items[0].next_action_after.queue == "repair_or_replace"
    assert "source failed staged-time validation" in batch.items[0].note
    assert batch.items[0].repair_first_warning is None

    export = db.export_staged_revisions(
        [source.revision_iri, restaged.revision_iri],
        tmp_path / "restaged-source-validation-review.md",
    )
    restaged_summary = export.revision_summaries[1]
    assert restaged_summary.apply_status == "ready"
    assert restaged_summary.apply_decision == (
        "inspect_restaged_source_validation_failure"
    )
    assert restaged_summary.next_action is not None
    assert restaged_summary.next_action.queue == "repair_or_replace"
    assert export.bundle_summary.next_action_queue == {
        "informational": [source.revision_iri],
        "repair_or_replace": [restaged.revision_iri],
    }
    assert export.bundle_summary.recommended_apply_or_restage_review_iris == []
    assert export.bundle_summary.recommended_repair_review_iris == [
        restaged.revision_iri
    ]
    listing = db.list_graph_revisions(
        revision_type="rc:StagedRevision",
        include_apply_checks=True,
    )
    assert listing.returned_application_status_counts == {
        "conflict": 1,
        "ready": 1,
    }
    assert listing.returned_stale_resolution_state_counts == {
        "stale_handled_by_restage": 1,
        "restaged_successor_ready": 1,
    }
    assert listing.returned_staged_validation_status_counts == {
        "failed": 1,
        "conforms": 1,
    }
    assert listing.next_action_queue == {
        "informational": [source.revision_iri],
        "repair_or_replace": [restaged.revision_iri],
    }


def test_batch_restage_marks_stale_current_successor_as_unresolved(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    original = db.stage_graph_revision(
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
        "https://example.test/project#InterveningA",
        label="Intervening A",
    )
    successor = db.restage_staged_revision(original.revision_iri)
    db.record_map_dataset(
        "https://example.test/project#InterveningB",
        label="Intervening B",
    )

    batch = db.restage_staged_revisions([original.revision_iri])

    item = batch.items[0]
    assert item.action == "skipped_already_handled"
    assert item.current_revision_iri == successor.revision_iri
    assert item.status_after == "conflict"
    assert item.stale_resolution_state_after == (
        "restaged_successor_stale_unresolved"
    )
    assert "current successor is itself stale" in item.note
    assert item.next_action_after is not None
    assert item.next_action_after.action_type == "restage_after_review"
    assert item.next_action_after.queue == "restage_after_review"
    assert item.next_action_after.tool_name == "restage_staged_revision"
    assert item.next_action_after.arguments == {
        "revision_iris": successor.revision_iri
    }
    assert item.suggested_next_actions_after[-1].tool == (
        "doxabase.restage_staged_revision"
    )
    assert batch.bundle_summary.stale_resolution_state_counts == {
        "stale_handled_by_restage": 1,
        "restaged_successor_stale_unresolved": 1,
    }
    assert batch.bundle_summary.unresolved_stale_revision_iris == [
        successor.revision_iri
    ]
    assert batch.bundle_summary.stale_handled_by_restage_revision_iris == [
        original.revision_iri
    ]
    assert batch.bundle_summary.ready_restage_successor_revision_iris == []
    assert batch.bundle_summary.post_apply_recheck_revision_iris == []
    assert batch.bundle_summary.recommended_mutation_review_iris == [
        successor.revision_iri
    ]
    assert batch.bundle_summary.recommended_apply_or_restage_review_iris == [
        successor.revision_iri
    ]
    assert batch.bundle_summary.recommended_repair_review_iris == []


def test_batch_restage_finalizes_current_revision_chain_mapping(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    original = db.stage_graph_revision(
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
        "https://example.test/project#InterveningA",
        label="Intervening A",
    )
    first_successor = db.restage_staged_revision(original.revision_iri)
    db.record_map_dataset(
        "https://example.test/project#InterveningB",
        label="Intervening B",
    )

    batch = db.restage_staged_revisions(
        [original.revision_iri, first_successor.revision_iri],
    )
    final_successor = batch.restaged_revision_iris[0]

    assert [item.action for item in batch.items] == [
        "skipped_already_handled",
        "restaged",
    ]
    assert batch.items[0].current_revision_iri == first_successor.revision_iri
    assert batch.items[0].next_action_after is not None
    assert batch.items[0].next_action_after.arguments == {
        "revision_iris": first_successor.revision_iri
    }
    assert batch.items[1].current_revision_iri == final_successor
    assert batch.current_revision_by_source == {
        original.revision_iri: final_successor,
        first_successor.revision_iri: final_successor,
    }
    assert batch.review_revision_iris == [
        original.revision_iri,
        first_successor.revision_iri,
        final_successor,
    ]
    assert batch.bundle_summary.ready_restage_successor_revision_iris == [
        final_successor
    ]
    final_check = db.check_staged_revision_apply(final_successor)
    assert final_check.status == "ready"


def test_restage_chain_routes_to_current_successor(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    original = db.stage_graph_revision(
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
        "https://example.test/project#InterveningA",
        label="Intervening A",
    )
    first_successor = db.restage_staged_revision(original.revision_iri)
    db.record_map_dataset(
        "https://example.test/project#InterveningB",
        label="Intervening B",
    )
    current_successor = db.restage_staged_revision(first_successor.revision_iri)
    current_successor_description = db.describe_staged_revision(
        current_successor.revision_iri
    )
    assert current_successor_description.summary == (
        "Restage stale revision: Stage messages table"
    )
    assert "Restage stale revision: Restage stale revision" not in (
        current_successor_description.summary or ""
    )

    original_description = db.describe_staged_revision(original.revision_iri)
    assert original_description.restaged_by is not None
    assert original_description.restaged_by.iri == first_successor.revision_iri
    assert original_description.current_restaged_by is not None
    assert (
        original_description.current_restaged_by.iri
        == current_successor.revision_iri
    )

    original_check = db.check_staged_revision_apply(original.revision_iri)
    assert original_check.status == "conflict"
    assert original_check.restaged_by == first_successor.revision_iri
    assert original_check.current_restaged_by == current_successor.revision_iri
    assert original_check.stale_resolution_state == "stale_handled_by_restage"
    assert original_check.summary.startswith(
        "Handled by restage; inspect successor"
    )
    assert current_successor.revision_iri in original_check.summary
    assert original_check.suggested_next_actions[-1].args == {
        "iri": current_successor.revision_iri
    }
    assert original_check.next_action is not None
    assert original_check.next_action.action_type == "inspect_current_successor"
    assert original_check.next_action.arguments == {
        "iri": current_successor.revision_iri
    }
    assert not any(
        action.tool == "doxabase.restage_staged_revision"
        for action in original_check.suggested_next_actions
    )

    listing = db.list_graph_revisions(include_apply_checks=True)
    by_iri = {item.iri: item for item in listing.revisions}
    assert by_iri[original.revision_iri].restaged_by == first_successor.revision_iri
    assert (
        by_iri[original.revision_iri].current_restaged_by
        == current_successor.revision_iri
    )
    assert by_iri[original.revision_iri].suggested_next_actions[-1].args == {
        "iri": current_successor.revision_iri
    }

    export_path = tmp_path / "original-chain-review.md"
    export = db.export_staged_revisions(
        [original.revision_iri],
        export_path,
    )
    assert export.revision_summaries[0].restaged_by == first_successor.revision_iri
    assert (
        export.revision_summaries[0].current_restaged_by
        == current_successor.revision_iri
    )
    assert export.bundle_summary.recommended_review_iris == [
        current_successor.revision_iri
    ]
    assert export.bundle_summary.external_recommended_review_iris == [
        current_successor.revision_iri
    ]
    assert export.bundle_summary.mutation_frontier_iris == []
    assert len(export.bundle_summary.warnings) == 1
    assert "outside this bundle" in export.bundle_summary.warnings[0]
    assert current_successor.revision_iri in export.bundle_summary.warnings[0]
    exported = export_path.read_text(encoding="utf-8")
    assert "## Bundle Warnings" in exported
    assert exported.index("## Bundle Warnings") < exported.index(
        "## Reviewer Decision Matrix"
    )
    assert "- Restaged by: " in exported
    assert "- Current restaged by: " in exported
    assert "**doxabase.describe_revision**" in exported
    assert "- Recommended review: " in exported
    assert current_successor.revision_iri in exported

    current_export = db.export_staged_revisions(
        [original.revision_iri, current_successor.revision_iri],
        tmp_path / "current-chain-review.md",
    )
    assert current_export.bundle_summary.recommended_review_iris == [
        current_successor.revision_iri
    ]
    assert current_export.bundle_summary.external_recommended_review_iris == []
    assert current_export.bundle_summary.mutation_frontier_iris == [
        current_successor.revision_iri
    ]

    batch = db.restage_staged_revisions(
        [original.revision_iri],
        path=tmp_path / "batch-chain-review.md",
    )
    assert batch.items[0].action == "skipped_already_handled"
    assert batch.items[0].restaged_from is None
    assert batch.items[0].current_restaged_by == current_successor.revision_iri
    assert batch.current_revision_by_source == {
        original.revision_iri: current_successor.revision_iri
    }
    assert batch.review_revision_iris == [
        original.revision_iri,
        current_successor.revision_iri,
    ]
    assert batch.bundle_summary.ready_restage_successor_revision_iris == [
        current_successor.revision_iri
    ]
    assert batch.bundle_summary.post_apply_recheck_revision_iris == []
    assert batch.bundle_summary.warnings == []

    successor_batch = db.restage_staged_revisions(
        [first_successor.revision_iri],
        dry_run=True,
    )
    assert successor_batch.items[0].action == "skipped_already_handled"
    assert successor_batch.items[0].restaged_from == original.revision_iri
    assert (
        successor_batch.items[0].current_restaged_by
        == current_successor.revision_iri
    )


def test_same_subject_alternative_restage_routes_max_count_repair(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    event_framing = db.stage_graph_revision(
        summary="Model Orders as event rows",
        rationale="First alternative for row-grain review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders a rc:Dataset, rc:Table ;
                        rc:rowSemantics rc:EventRow .
                """,
            }
        ],
        revision_anchors=[orders],
        validation_scope="all",
    )
    snapshot_framing = db.stage_graph_revision(
        summary="Model Orders as snapshot rows",
        rationale="Competing same-subject row-grain alternative.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders a rc:Dataset, rc:Table ;
                        rc:rowSemantics rc:SnapshotRow .
                """,
            }
        ],
        alternative_to=event_framing.revision_iri,
        revision_anchors=[orders],
        validation_scope="all",
    )
    db.record_map_dataset(
        "https://example.test/project#DriftDataset",
        label="Drift dataset",
    )

    event_successor = db.restage_staged_revision(event_framing.revision_iri)
    db.apply_staged_revision(event_successor.revision_iri)
    snapshot_successor = db.restage_staged_revision(snapshot_framing.revision_iri)

    snapshot_check = db.check_staged_revision_apply(
        snapshot_successor.revision_iri
    )
    assert snapshot_check.status == "validation_failed"
    assert snapshot_check.decision == "inspect_validation_results"
    assert snapshot_check.can_apply is False
    assert snapshot_check.blocking_reasons == ["validation_failed"]
    assert snapshot_check.next_action is not None
    assert snapshot_check.next_action.action_type == "repair_or_replace"
    assert snapshot_check.next_action.queue == "repair_or_replace"
    assert snapshot_check.next_action.tool_name == "restage_staged_revision"
    assert snapshot_check.next_action.arguments.get("dry_run") is True
    assert snapshot_check.next_action.arguments == {
        "revision_iris": snapshot_successor.revision_iri,
        "dry_run": True,
        "validation_scope": "all",
    }
    assert snapshot_check.suggested_next_actions[0].tool == (
        "doxabase.restage_staged_revision"
    )
    assert snapshot_check.suggested_next_actions[0].args.get(
        "dry_run"
    ) is True
    assert "removal+addition" in (snapshot_check.recommended_resolution or "")
    row_semantics_diagnostic = next(
        result
        for result in snapshot_check.validation_results
        if result.result_path == RC + "rowSemantics"
    )
    assert row_semantics_diagnostic.source_constraint_component == (
        "http://www.w3.org/ns/shacl#MaxCountConstraintComponent"
    )
    assert row_semantics_diagnostic.hint is not None
    assert "rc:EventRow" in row_semantics_diagnostic.hint
    assert "rc:SnapshotRow" in row_semantics_diagnostic.hint
    assert "removal+addition" in row_semantics_diagnostic.hint
    draft = db.draft_staged_revision_rebase(snapshot_successor.revision_iri)
    assert draft.source_revision_iri == snapshot_successor.revision_iri
    assert draft.current_revision_iri == snapshot_successor.revision_iri
    assert draft.draft_status == "drafted"
    assert draft.draft_kind == "same_slot_replacement"
    assert draft.apply_check.status == "validation_failed"
    assert draft.apply_check.decision == "inspect_validation_results"
    assert draft.lineage.alternative_gate_status == (
        "alternative_to_applied_source"
    )
    assert draft.lineage.alternative_semantic_review_required is True
    assert draft.lineage.alternative_applied_source_iri == (
        event_successor.revision_iri
    )
    assert (
        draft.repair_actions[0].tool,
        draft.repair_actions[0].args.get("kind"),
    ) == ("doxabase.stage_revision", "map_assertion")
    assert draft.repair_actions[0].args["spec"]["subject"] == orders
    assert draft.repair_actions[0].args["spec"]["predicate"] == RC + "rowSemantics"
    assert draft.repair_actions[0].args["spec"]["object"] == RC + "SnapshotRow"
    assert draft.repair_actions[0].args["spec"]["change_kind"] == "replace"
    assert draft.repair_actions[0].args["spec"]["restages_revision"] == (
        snapshot_successor.revision_iri
    )
    assert draft.repair_actions[0].args["spec"]["alternative_to"] == (
        event_framing.revision_iri
    )
    repair_candidate = draft.repair_candidates[0]
    assert repair_candidate.candidate_status == "ready_to_stage"
    assert repair_candidate.current_same_subject_predicate_triples[0].object == (
        RC + "EventRow"
    )
    assert repair_candidate.proposed_triples[0].object == RC + "SnapshotRow"
    assert repair_candidate.validation_results[0].result_path == (
        RC + "rowSemantics"
    )
    assert draft.next_action is not None
    assert draft.next_action.source == "draft_staged_revision_rebase"
    assert draft.next_action.tool_name == "stage_revision"
    assert draft.next_action.arguments.get("kind") == "map_assertion"
    assert draft.suggested_next_actions[0].tool == "doxabase.stage_revision"
    assert draft.suggested_next_actions[0].args.get("kind") == (
        "map_assertion"
    )
    snapshot_description = db.describe_staged_revision(
        snapshot_successor.revision_iri
    )
    stored_diagnostic = next(
        result
        for result in snapshot_description.validation_results
        if result.result_path == RC + "rowSemantics"
    )
    assert stored_diagnostic.hint == row_semantics_diagnostic.hint

    current_work = db.list_graph_revisions(
        current_staged_work_only=True,
        include_apply_checks=True,
    )

    assert current_work.count == 1
    assert current_work.revisions[0].iri == snapshot_successor.revision_iri
    assert current_work.next_action_queue == {
        "repair_or_replace": [snapshot_successor.revision_iri]
    }
    assert current_work.returned_application_status_counts == {
        "validation_failed": 1
    }


def test_restage_staged_revision_rejects_non_conflicted_revision(
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

    with pytest.raises(DoxaBaseError, match="current status is 'ready'"):
        db.restage_staged_revision(staged.revision_iri)


def test_describe_revision_lineage_summarizes_restage_and_apply_chain(
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
        created_at="2026-06-01T10:00:00Z",
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
        created_at="2026-06-01T10:01:00Z",
    )
    db.record_map_dataset(
        "https://example.test/project#DriftDataset",
        label="Drift dataset",
    )
    first_restaged = db.restage_staged_revision(first.revision_iri)
    second_restaged = db.restage_staged_revision(second.revision_iri)
    applied = db.apply_staged_revision(first_restaged.revision_iri)

    source_lineage = db.describe_revision_lineage(first.revision_iri)

    assert source_lineage.selected_role == "restaged_source"
    assert source_lineage.selected_revision_iri == first.revision_iri
    assert source_lineage.paired_revision is None
    assert source_lineage.paired_revision_iri is None
    assert source_lineage.applied_revision_iri == applied.applied_revision_iri
    assert source_lineage.staged_revision_iri == first.revision_iri
    assert source_lineage.applied_source_revision_iri == first_restaged.revision_iri
    assert source_lineage.current_staged_revision_iri is None
    assert source_lineage.current_revision_iri is None
    assert source_lineage.latest_revision_iri == applied.applied_revision_iri
    assert source_lineage.latest_role == "applied_event"
    assert source_lineage.restage_chain_iris == [
        first.revision_iri,
        first_restaged.revision_iri,
    ]
    assert second_restaged.revision_iri in source_lineage.alternative_revision_iris
    assert source_lineage.next_action is not None
    assert source_lineage.next_action.queue == "inspect_already_applied"
    assert source_lineage.next_action_queue_item is not None
    assert source_lineage.next_action_queue_item.row_iri == first.revision_iri
    assert (
        source_lineage.next_action_queue_item.resolved_target_iri
        == applied.applied_revision_iri
    )
    assert source_lineage.next_action_queue_item.row_is_target is False
    assert (
        source_lineage.next_action_queue_item.resolved_target_record_kind
        == "applied_event"
    )
    assert source_lineage.warnings == []

    staged_lineage = db.describe_revision_lineage(first_restaged.revision_iri)

    assert staged_lineage.selected_role == "applied_source"
    assert staged_lineage.selected_revision_iri == first_restaged.revision_iri
    assert staged_lineage.paired_revision is not None
    assert staged_lineage.paired_revision.iri == applied.applied_revision_iri
    assert staged_lineage.paired_revision_iri == applied.applied_revision_iri
    assert staged_lineage.paired_role == "applied_event"
    assert staged_lineage.staged_revision_iri == first_restaged.revision_iri
    assert staged_lineage.applied_source_revision_iri == first_restaged.revision_iri
    assert staged_lineage.applied_revision_iri == applied.applied_revision_iri

    applied_lineage = db.describe_revision_lineage(applied.applied_revision_iri)

    assert applied_lineage.selected_role == "applied_event"
    assert applied_lineage.selected_revision_iri == applied.applied_revision_iri
    assert applied_lineage.paired_revision is not None
    assert applied_lineage.paired_revision.iri == first_restaged.revision_iri
    assert applied_lineage.paired_revision_iri == first_restaged.revision_iri
    assert applied_lineage.paired_role == "applied_source"
    assert applied_lineage.applied_source_revision_iri == first_restaged.revision_iri
    assert applied_lineage.restage_chain_iris == [
        first.revision_iri,
        first_restaged.revision_iri,
    ]

    active_lineage = db.describe_revision_lineage(second_restaged.revision_iri)

    assert active_lineage.selected_role == "current_staged_revision"
    assert active_lineage.current_staged_revision_iri == second_restaged.revision_iri
    assert active_lineage.current_revision_iri == second_restaged.revision_iri
    assert active_lineage.applied_revision_iri is None
    assert active_lineage.applied_source_revision_iri is None
    assert active_lineage.latest_revision_iri == second_restaged.revision_iri
    assert active_lineage.next_action is not None
    assert active_lineage.next_action.queue == "restage_after_review"
    assert active_lineage.restage_chain_iris == [
        second.revision_iri,
        second_restaged.revision_iri,
    ]
    assert applied.applied_revision_iri in active_lineage.related_revision_iris


def test_resource_revision_lineage_tracks_current_restage_successor(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    original = db.stage_graph_revision(
        summary="Classify Orders as dataset",
        rationale="Exercise resource lineage across restage and apply.",
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
        revision_anchors=[orders],
        created_at="2026-06-01T10:00:00Z",
    )
    db.record_map_dataset(
        "https://example.test/project#DriftMaker",
        label="Drift maker",
    )
    restaged = db.restage_staged_revision(
        original.revision_iri,
        created_at="2026-06-01T10:01:00Z",
    )

    stale_lineage = db.describe_resource_revision_lineage(
        orders,
        original.revision_iri,
    )
    assert stale_lineage.selected_role == "restaged_source"
    assert stale_lineage.applied_revision_iri is None
    assert stale_lineage.applied_source_revision_iri is None
    assert stale_lineage.current_staged_revision_iri == restaged.revision_iri
    assert stale_lineage.current_revision_iri == restaged.revision_iri
    assert stale_lineage.latest_revision_iri == restaged.revision_iri
    assert stale_lineage.latest_role == "current_staged_revision"
    assert stale_lineage.restage_chain_iris == [
        original.revision_iri,
        restaged.revision_iri,
    ]
    assert stale_lineage.alternative_revision_iris == []
    assert stale_lineage.related_revision_iris == [
        original.revision_iri,
        restaged.revision_iri,
    ]
    current_resource_lineage = db.describe_resource_revision_lineage(
        orders,
        restaged.revision_iri,
    )
    assert current_resource_lineage.selected_role == "current_staged_revision"
    assert current_resource_lineage.applied_revision_iri is None
    assert current_resource_lineage.applied_source_revision_iri is None
    current_graph_lineage = db.describe_revision_lineage(restaged.revision_iri)
    assert current_graph_lineage.applied_revision_iri is None
    assert current_graph_lineage.applied_source_revision_iri is None

    applied = db.apply_staged_revision(
        restaged.revision_iri,
        created_at="2026-06-01T10:02:00Z",
    )
    applied_source_lineage = db.describe_resource_revision_lineage(
        orders,
        original.revision_iri,
    )
    assert applied_source_lineage.selected_role == "restaged_source"
    assert applied_source_lineage.current_staged_revision_iri is None
    assert applied_source_lineage.current_revision_iri is None
    assert applied_source_lineage.latest_revision_iri == applied.applied_revision_iri
    assert applied_source_lineage.latest_role == "applied_event"
    assert applied_source_lineage.applied_revision_iri == applied.applied_revision_iri
    assert applied_source_lineage.staged_revision_iri == restaged.revision_iri
    assert applied_source_lineage.applied_source_revision_iri == (
        restaged.revision_iri
    )
    assert applied_source_lineage.restage_chain_iris == [
        original.revision_iri,
        restaged.revision_iri,
    ]
    assert applied_source_lineage.related_revision_iris == [
        original.revision_iri,
        applied.applied_revision_iri,
        restaged.revision_iri,
    ]
    assert applied_source_lineage.next_action is not None
    assert applied_source_lineage.next_action.action_type == (
        "inspect_applied_event"
    )
    assert applied_source_lineage.next_action_queue_item is not None
    assert (
        applied_source_lineage.next_action_queue_item.row_iri
        == original.revision_iri
    )
    assert (
        applied_source_lineage.next_action_queue_item.resolved_target_iri
        == applied.applied_revision_iri
    )
    assert applied_source_lineage.next_action_queue_item.row_is_target is False
    assert applied_source_lineage.next_action.arguments == {
        "iri": applied.applied_revision_iri,
    }
    assert [
        action.tool.removeprefix("doxabase.") for action in applied_source_lineage.suggested_next_actions
    ][:3] == [
        "describe_revision",
        "describe_revision",
        "describe_revision",
    ]
    assert [
        action.args.get("aspect")
        for action in applied_source_lineage.suggested_next_actions
    ][:3] == [None, "applied_diff", None]
    assert applied_source_lineage.applied_diff_status == "available"
    assert applied_source_lineage.applied_diff is not None
    assert applied_source_lineage.applied_diff.applied_revision_iri == (
        applied.applied_revision_iri
    )
    assert applied_source_lineage.applied_diff.staged_revision_iri == (
        restaged.revision_iri
    )
    assert applied_source_lineage.applied_diff.changed_graphs == ["map"]
    assert (
        applied_source_lineage.applied_diff.graph_diffs[0].resource_triples_added_count
        == 1
    )
    applied_event_lineage = db.describe_resource_revision_lineage(
        orders,
        applied.applied_revision_iri,
    )
    assert applied_event_lineage.restage_chain_iris == [
        original.revision_iri,
        restaged.revision_iri,
    ]
    assert applied_event_lineage.latest_revision_iri == applied.applied_revision_iri
    assert applied_event_lineage.latest_role == "applied_event"
    assert applied_event_lineage.related_revision_iris == [
        applied.applied_revision_iri,
        restaged.revision_iri,
        original.revision_iri,
    ]


def test_handoff_import_preserves_mixed_semantic_gate_and_stale_restage(
    tmp_path: Path,
) -> None:
    source = DoxaBase.create(tmp_path / "source.sqlite")
    orders = "https://example.test/project#Orders"
    fulfillment = "https://example.test/project#FulfillmentEvents"
    source.record_map_dataset(orders, label="Orders", is_table=True)
    event_source = source.stage_graph_revision(
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
    stale_mechanical = source.stage_graph_revision(
        summary="Add fulfillment events dataset",
        rationale=(
            "Independent map addition staged before the Orders event framing "
            "is applied."
        ),
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    <{fulfillment}> a rc:Dataset .
                """,
            }
        ],
        revision_anchors=[fulfillment],
        validation_scope="all",
    )
    applied = source.apply_staged_revision(event_source.revision_iri)
    semantic_alternative = source.stage_systematisation(
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
    revision_iris = [semantic_iri, stale_mechanical.revision_iri]

    semantic_check = source.check_staged_revision_apply(semantic_iri)
    assert semantic_check.status == "ready"
    assert semantic_check.can_apply is True
    assert semantic_check.next_action is not None
    assert semantic_check.next_action.action_label == (
        "Apply only after semantic review"
    )
    assert semantic_check.first_safe_next_action is not None
    assert semantic_check.first_safe_next_action.tool_name == (
        "describe_revision"
    )
    assert source.check_staged_revision_apply(
        stale_mechanical.revision_iri
    ).next_action.tool_name == "restage_staged_revision"

    source_plan = source.plan_staged_revision_recovery(
        revision_iris,
        current_staged_work_only=False,
        drift_detail="exact",
    )
    assert source_plan.lane_counts == {
        "apply_after_review": 1,
        "restage_after_review": 1,
    }
    assert source_plan.mutation_allowed_after == (
        "semantic_review_required_before_mutation"
    )
    assert source_plan.first_mutation_action is None
    assert any(
        action_tool_name(item.action) == "restage_staged_revision"
        and dict(action_arguments(item.action))
        == {"revision_iris": stale_mechanical.revision_iri}
        and item.requires_semantic_review_before_mutation is False
        for item in source_plan.mutation_frontier_items
    )
    assert source_plan.first_safe_review_or_mutation_action is not None
    assert action_tool_name(
        source_plan.first_safe_review_or_mutation_action
    ) == "restage_staged_revision"
    source_lanes = {lane.row_iri: lane for lane in source_plan.lanes}
    assert source_lanes[semantic_iri].alternative_gate is not None
    assert source_lanes[semantic_iri].alternative_gate.status == (
        "alternative_to_applied_source"
    )
    assert (
        source_lanes[semantic_iri].alternative_gate.semantic_review_required
        is True
    )
    assert source_lanes[stale_mechanical.revision_iri].next_action is not None
    assert source_lanes[
        stale_mechanical.revision_iri
    ].next_action.tool_name == "restage_staged_revision"

    manifest_path = tmp_path / "handoff-manifest.json"
    trig_path = tmp_path / "project-handoff.trig"
    snapshot_path = tmp_path / "revision-snapshots.json"
    session = source.start_staged_revision_recovery_session(
        revision_iris,
        summary="Mixed staged handoff recovery session",
        handoff_manifest_path=str(manifest_path),
        current_staged_work_only=False,
        drift_detail="exact",
    )
    exported = source.export_handoff_bundle(
        trig_path,
        snapshot_path,
        manifest_path=manifest_path,
        revision_iris=revision_iris,
    )
    assert exported.manifest["recovery_session_iris"] == [session.session_iri]
    assert exported.manifest["recovery_session_count"] == 1
    manifest_session = exported.manifest["recovery_sessions"][0]
    assert manifest_session["session_iri"] == session.session_iri
    assert manifest_session["summary"] == "Mixed staged handoff recovery session"
    assert manifest_session["source_revision_iris"] == revision_iris
    assert manifest_session["drift_detail"] == "exact"
    assert manifest_session["resume_action"]["tool"] == (
        "doxabase.plan_staged_revision_recovery"
    )
    assert manifest_session["resume_action"]["args"]["session_iri"] == (
        session.session_iri
    )

    trig_only_receiver = DoxaBase.create(tmp_path / "trig-only.sqlite")
    trig_only_receiver.import_trig(trig_path)
    trig_only_plan = trig_only_receiver.plan_staged_revision_recovery(
        revision_iris,
        current_staged_work_only=False,
    )
    assert trig_only_plan.lane_counts == {"complete_handoff_import": 2}
    assert trig_only_plan.mutation_allowed_after == (
        "handoff_preflight_required_before_mutation"
    )
    assert trig_only_plan.first_mutation_action is None
    assert trig_only_plan.first_safe_review_or_mutation_action is not None
    assert trig_only_plan.first_safe_review_or_mutation_action.tool == (
        "doxabase.import_bundle"
    )

    receiver = DoxaBase.create(tmp_path / "receiver.sqlite")
    imported = receiver.import_handoff_bundle(
        manifest_path,
        drift_detail="exact",
    )
    assert imported.manifest["recovery_session_iris"] == [session.session_iri]
    assert imported.matching_recovery_session_iris == [session.session_iri]
    assert imported.recovery_summary.imported_recovery_session_iris == [
        session.session_iri
    ]
    assert imported.recovery_summary.matching_recovery_session_iris == [
        session.session_iri
    ]
    assert imported.recovery_summary.resume_recovery_session_iri == (
        session.session_iri
    )
    assert imported.recovery_summary.recommended_next_step == (
        "continue_imported_recovery_session"
    )
    assert imported.suggested_next_actions[0].tool == (
        "doxabase.plan_staged_revision_recovery"
    )
    manifest_resume_iri = imported.manifest["recovery_sessions"][0]["session_iri"]
    receiver_brief = receiver.project_brief(limit=10)
    frontier_queue = next(
        queue
        for queue in receiver_brief.queues
        if queue.name == "staged_frontier_review"
    )
    assert frontier_queue.count == 1
    assert frontier_queue.example_iri == session.session_iri
    recovery_gate = next(
        gate
        for gate in receiver_brief.gates
        if gate.gate == "staged_revision_recovery"
    )
    assert recovery_gate.blocks == "mutation"
    recovery_action = receiver_brief.suggested_next_actions[0]
    assert recovery_action.tool == (
        "doxabase.plan_staged_revision_recovery"
    )
    assert recovery_action.args == {
        "session_iri": session.session_iri,
        "drift_detail": "exact",
    }
    described_session = receiver.describe_staged_revision_recovery_session(
        manifest_resume_iri,
        drift_detail="exact",
    )
    receiver_plan = described_session.current_plan
    assert receiver_plan.lane_counts == {
        "apply_after_review": 1,
        "restage_after_review": 1,
    }
    assert receiver_plan.first_mutation_action is None
    assert any(
        action_tool_name(item.action) == "restage_staged_revision"
        and dict(action_arguments(item.action))
        == {"revision_iris": stale_mechanical.revision_iri}
        and item.requires_semantic_review_before_mutation is False
        for item in receiver_plan.mutation_frontier_items
    )
    assert receiver_plan.first_safe_review_or_mutation_action is not None
    assert receiver_plan.first_safe_review_or_mutation_action.tool == (
        "doxabase.restage_staged_revision"
    )
    receiver_lanes = {lane.row_iri: lane for lane in receiver_plan.lanes}
    receiver_semantic_lane = receiver_lanes[semantic_iri]
    assert receiver_semantic_lane.next_action is not None
    assert receiver_semantic_lane.next_action.action_label == (
        "Apply only after semantic review"
    )
    assert receiver_semantic_lane.alternative_gate is not None
    assert receiver_semantic_lane.alternative_gate.applied_source_iri == (
        event_source.revision_iri
    )
    assert receiver_semantic_lane.alternative_gate.applied_revision_iri == (
        applied.applied_revision_iri
    )
    assert receiver_lanes[stale_mechanical.revision_iri].next_action is not None
    assert receiver_lanes[
        stale_mechanical.revision_iri
    ].next_action.tool_name == "restage_staged_revision"

    receiver_semantic_check = receiver.check_staged_revision_apply(semantic_iri)
    assert receiver_semantic_check.status == "ready"
    assert receiver_semantic_check.can_apply is True
    assert receiver_semantic_check.first_safe_next_action is not None
    assert receiver_semantic_check.first_safe_next_action.tool_name == (
        "describe_revision"
    )
    assert receiver_semantic_check.next_action is not None
    assert receiver_semantic_check.next_action.action_label == (
        "Apply only after semantic review"
    )
    semantic_lineage = receiver.describe_revision_lineage(semantic_iri)
    assert semantic_lineage.selected_role == "current_staged_revision"
    assert event_source.revision_iri in semantic_lineage.related_revision_iris
    versions = receiver.list_graph_versions("map", exact_only=True)
    assert versions.exact_snapshot_available_count >= 2
    diff = receiver.describe_graph_version_diff(
        "map",
        before_revision_iri=stale_mechanical.revision_iri,
        include_triples=True,
    )
    assert diff.exact_changed_triples_available is True
    assert diff.digest_changed is True


def test_plan_profile_followthrough_rechecks_and_restages_stale_sibling(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled for follow-through routing.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        update_map_snapshot=False,
        column_profiles=[],
    )
    first = db.stage_graph_revision(
        summary="Define first profile value type",
        rationale="Synthetic sibling revision for profile follow-through.",
        additions=[
            {
                "graph": "ontology",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:FirstProfileValueType a rc:ValueType ;
                        rdfs:label "First profile value type" .
                """,
            }
        ],
        revision_anchors=[dataset],
        validation_scope="all",
    )
    second = db.stage_graph_revision(
        summary="Define second profile value type",
        rationale="Synthetic sibling revision for profile follow-through.",
        additions=[
            {
                "graph": "ontology",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:SecondProfileValueType a rc:ValueType ;
                        rdfs:label "Second profile value type" .
                """,
            }
        ],
        revision_anchors=[dataset],
        validation_scope="all",
    )

    assert db.check_staged_revision_apply(second.revision_iri).status == "ready"
    db.apply_staged_revision(first.revision_iri)
    stale_check = db.check_staged_revision_apply(second.revision_iri)
    assert stale_check.status == "conflict"
    assert stale_check.next_action is not None
    assert stale_check.next_action.tool_name == "restage_staged_revision"

    dry_plan = db.plan_profile_followthrough(
        dataset,
        evidence,
        staged_revision_iris=[second.revision_iri],
    )

    assert dry_plan.revision_check_count == 1
    assert dry_plan.revision_checks[0].status_before == "conflict"
    assert dry_plan.revision_checks[0].restage_performed is False
    assert dry_plan.revision_checks[0].suggested_next_actions[-1].tool == (
        "doxabase.restage_staged_revision"
    )
    assert dry_plan.suggested_next_action_groups[
        "staged_revision_recheck"
    ][-1].tool == "doxabase.restage_staged_revision"

    restage_plan = db.plan_profile_followthrough(
        dataset,
        evidence,
        staged_revision_iris=[second.revision_iri],
        restage_stale_revisions=True,
    )

    assert restage_plan.revision_check_count == 1
    recheck = restage_plan.revision_checks[0]
    assert recheck.status_before == "conflict"
    assert recheck.restage_performed is True
    assert recheck.restaged_revision_iri is not None
    assert recheck.status_after == "ready"
    assert recheck.next_action_after is not None
    assert recheck.next_action_after.tool_name == "apply_staged_revision"
    assert restage_plan.restaged_revision_iris == [recheck.restaged_revision_iri]
    assert restage_plan.suggested_next_actions[-1].tool == (
        "doxabase.apply_staged_revision"
    )
    assert restage_plan.suggested_next_action_groups[
        "staged_revision_recheck"
    ][-1].tool == "doxabase.apply_staged_revision"
    assert db.validate_graph(scope="all").conforms

