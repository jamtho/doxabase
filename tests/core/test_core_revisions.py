"""Split from test_doxabase_core.py (distillation Phase 2); tests verbatim."""

from tests.core.support_core import *  # noqa: F401,F403


def test_record_graph_revision_writes_history_metadata(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    observation = db.record_observation(
        summary="AIS map export was reviewed during a revision test.",
        observed_asset="https://richcanopy.org/example/manifest/ais#DailyIndex",
        evidence_summary="Revision helper unit test evidence.",
        evidence_sources=["tests/test_doxabase_core.py"],
    )
    graph_counts = {
        "map": db.triple_count("map"),
        "observations": db.triple_count("observations"),
    }
    assert observation.evidence_iri is not None

    revision = db.record_graph_revision(
        summary="AIS map review bundle recorded",
        rationale="The exported bundle captures the current AIS map plus one review observation.",
        changed_graphs=["observations"],
        included_graphs=["map", "observations"],
        revision_type="rc:ExportRevision",
        created_at="2026-06-02T00:00:00Z",
        created_by="urn:doxabase:test-agent",
        supporting_observations=[observation.observation_iri],
        revision_anchors=[
            "https://richcanopy.org/example/manifest/ais#DailyIndex",
            "https://richcanopy.org/example/manifest/ais#ix_mmsi",
        ],
        evidence=[observation.evidence_iri],
        export_path="/tmp/ais-review-bundle.trig",
        graph_counts=graph_counts,
        validation_scope="all",
        validation_conforms=True,
        validation_result_count=0,
    )

    assert revision.revision_type == RC + "ExportRevision"
    assert revision.graph == "history"
    assert revision.triples > 0
    assert db.validate_graph(scope="all").conforms

    revisions = db.list_entities(type="rc:GraphRevision", graph="history")
    assert revisions.entities[0].iri == revision.revision_iri
    overview = db.graph_overview()
    assert overview.key_counts["graph_revisions"] == 1
    assert overview.key_counts["graph_snapshots"] == 2

    context = db.describe_resource(revision.revision_iri, graph="history")
    outgoing = {(triple.predicate, triple.object) for triple in context.outgoing}
    assert (RC + "changedGraph", "map") not in outgoing
    assert (RC + "changedGraph", "observations") in outgoing
    assert (RC + "includedGraph", "map") in outgoing
    assert (RC + "includedGraph", "observations") in outgoing
    assert (
        RC + "revisionAnchor",
        "https://richcanopy.org/example/manifest/ais#DailyIndex",
    ) in outgoing
    assert (RC + "exportPath", "/tmp/ais-review-bundle.trig") in outgoing
    assert any(triple.predicate == RC + "hasGraphSnapshot" for triple in context.outgoing)

    description = db.describe_graph_revision(revision.revision_iri)
    assert description.summary == "AIS map review bundle recorded"
    assert description.record_kind == "export_record"
    assert description.revision_type == RC + "ExportRevision"
    assert description.revision_type_label == "export revision"
    assert description.changed_graphs == ["observations"]
    assert description.included_graphs == ["map", "observations"]
    assert description.export_path == "/tmp/ais-review-bundle.trig"
    assert description.validation_conforms is True
    assert description.validation_result_count == 0
    snapshots = {
        snapshot.graph_role: snapshot for snapshot in description.graph_snapshots
    }
    assert {
        graph_role: snapshot.triple_count
        for graph_role, snapshot in snapshots.items()
    } == graph_counts
    for snapshot in snapshots.values():
        assert snapshot.content_digest is not None
        assert snapshot.content_digest.startswith("sha256:")
        assert len(snapshot.content_digest) == len("sha256:") + 64
    assert [support.iri for support in description.supporting_observations] == [
        observation.observation_iri
    ]
    assert [anchor.iri for anchor in description.revision_anchors] == [
        "https://richcanopy.org/example/manifest/ais#DailyIndex",
        "https://richcanopy.org/example/manifest/ais#ix_mmsi",
    ]
    assert description.revision_anchors[0].label == "AIS Daily Vessel Index"
    assert description.revision_anchors[1].label == "mmsi"
    assert description.supporting_observations[0].label == (
        "AIS map export was reviewed during a revision test."
    )


def test_record_graph_revision_rejects_immutable_seed_targets(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(ImmutableGraphError, match="base_ontology"):
        db.record_graph_revision(
            summary="Invalid seed revision",
            rationale="Ordinary project revisions should not target shipped seeds.",
            changed_graphs=["base_ontology"],
        )


def test_table_type_overlap_is_broad_snapshot_drift_relevance(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = db.stage_graph_revision(
        summary="Stage messages table shell",
        rationale="Messages should become durable table context after review.",
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
    )
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:OtherMessages a rc:Table .
        """,
        graph="map",
    )

    check = db.check_staged_revision_apply(staged.revision_iri)

    assert check.status == "conflict"
    assert len(check.snapshot_drifts) == 1
    drift = check.snapshot_drifts[0]
    assert drift.drift_relevance == "broad_patch_object_overlap"
    assert drift.patch_overlap_subjects == []
    assert str(RDF.type) in drift.patch_overlap_predicates
    assert drift.patch_overlap_objects == [RC + "Table"]
    assert "only staged patch object overlap is broad vocabulary" in drift.note


def test_apply_check_reports_same_count_snapshot_digest_drift(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:SeedDataset a rc:Dataset ;
            rdfs:label "Seed dataset" .
        """,
        graph="map",
    )
    staged = db.stage_graph_revision(
        summary="Stage candidate dataset",
        rationale="This candidate should detect same-count graph drift.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:CandidateDataset a rc:Dataset .
                """,
            }
        ],
    )
    label_swap = db.stage_graph_revision(
        summary="Rename seed dataset without changing count",
        rationale=(
            "Exercise digest drift: the map content changes but triple count "
            "returns to the staged baseline."
        ),
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:SeedDataset rdfs:label "Seed dataset renamed" .
                """,
            }
        ],
        removals=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:SeedDataset rdfs:label "Seed dataset" .
                """,
            }
        ],
    )
    db.apply_staged_revision(label_swap.revision_iri)

    check = db.check_staged_revision_apply(staged.revision_iri)

    assert check.can_apply is False
    assert check.status == "conflict"
    assert check.decision == "restage_against_current_graph"
    assert check.blocking_reasons == ["target_digest_drift"]
    assert check.count_drifts == []
    assert len(check.snapshot_drifts) == 1
    drift = check.snapshot_drifts[0]
    assert drift.graph_role == "map"
    assert drift.snapshot_triple_count == 2
    assert drift.current_triple_count == 2
    assert drift.snapshot_content_digest.startswith("sha256:")
    assert drift.current_content_digest.startswith("sha256:")
    assert drift.snapshot_content_digest != drift.current_content_digest
    assert drift.exact_changed_triples_available is True
    assert drift.exact_changed_triples_included is True
    assert drift.triples_added_since_snapshot_count == 1
    assert drift.triples_removed_since_snapshot_count == 1
    assert drift.drift_relevance == "no_patch_subject_overlap"
    assert drift.patch_overlap_subjects == []
    assert drift.patch_overlap_predicates == []
    assert drift.patch_overlap_objects == []
    assert drift.revision_anchor_overlap == []
    assert drift.changed_resource_count == 1
    assert drift.changed_resources_returned_count == 1
    assert drift.changed_resources_omitted_count == 0
    assert drift.changed_resources[0].resource.iri == (
        "https://example.test/project#SeedDataset"
    )
    assert drift.changed_resources[0].changed_triple_count == 2
    assert drift.changed_resources[0].added_triple_count == 1
    assert drift.changed_resources[0].removed_triple_count == 1
    assert drift.changed_resources[0].matched_by == ["changed_subject"]
    assert drift.changed_resources[0].predicate_displays == ["rdfs:label"]
    assert drift.changed_resource_suggested_next_actions[0].tool_name == (
        "list_resource_revisions"
    )
    assert "Predicate overlap is reported separately, even when empty" in drift.note
    assert [triple.object for triple in drift.triples_added_since_snapshot] == [
        "Seed dataset renamed"
    ]
    assert [triple.object for triple in drift.triples_removed_since_snapshot] == [
        "Seed dataset"
    ]
    assert drift.triples_added_since_snapshot[0].subject_display == "SeedDataset"
    assert drift.triples_added_since_snapshot[0].predicate_curie == "rdfs:label"
    assert drift.triples_added_since_snapshot[0].predicate_display == "rdfs:label"
    assert drift.triples_added_since_snapshot[0].object_display == (
        "Seed dataset renamed"
    )
    assert "Exact triples" in drift.note
    assert check.patch_checks[0].can_apply is False
    assert "content digest changed since staging" in (
        check.patch_checks[0].conflict or ""
    )

    export_path = tmp_path / "same-count-drift-review.md"
    db.export_staged_revision(staged.revision_iri, export_path)
    export_text = export_path.read_text(encoding="utf-8")
    assert "- Blocking reasons: target_digest_drift" in export_text
    assert "### Snapshot Drift" in export_text
    assert (
        "| Graph | Snapshot stored count | Current count | "
        "Snapshot digest | Current digest | Exact changed triples | "
        "Added since snapshot | Removed since snapshot | Drift relevance | "
        "Patch subject overlap | Patch predicate overlap | Patch object overlap | "
        "Revision anchor overlap | Note |"
    ) in export_text
    assert "| map | 2 | 2 |" in export_text
    assert "| True | 1 | 1 |" in export_text
    assert "#### Snapshot Drift Changed Resources: map" in export_text
    assert "| Seed dataset renamed | 2 | 1 | 1 | changed_subject | rdfs:label |" in (
        export_text
    )
    assert "list_resource_revisions(resource_iri=" in export_text
    assert "#### Snapshot Drift Triples: map" in export_text
    assert "exact raw RDF terms remain available" in export_text
    assert "SeedDataset" in export_text
    assert "rdfs:label" in export_text
    assert "Seed dataset renamed" in export_text
    assert "sha256:" in export_text

    listing = db.list_graph_revisions(
        revision_type="rc:StagedRevision",
        include_apply_checks=True,
    )
    assert listing.drift_detail == "summary"
    listed = {item.iri: item for item in listing.revisions}[staged.revision_iri]
    assert listed.application_status == "conflict"
    assert listed.application_blocking_reasons == ["target_digest_drift"]
    summary_drift = listed.application_snapshot_drifts[0]
    assert summary_drift.graph_role == "map"
    assert summary_drift.exact_changed_triples_available is True
    assert summary_drift.exact_changed_triples_included is False
    assert summary_drift.triples_added_since_snapshot_count == 1
    assert summary_drift.triples_removed_since_snapshot_count == 1
    assert summary_drift.triples_added_since_snapshot == []
    assert summary_drift.triples_removed_since_snapshot == []
    assert (
        summary_drift.drift_relevance
        == "no_patch_subject_overlap"
    )
    assert summary_drift.patch_overlap_objects == []
    assert summary_drift.revision_anchor_overlap == []
    assert summary_drift.changed_resource_count == 1
    assert summary_drift.changed_resources[0].resource.iri == (
        "https://example.test/project#SeedDataset"
    )
    assert summary_drift.changed_resource_suggested_next_actions[0].tool_name == (
        "list_resource_revisions"
    )
    assert "omitted from this summary response" in summary_drift.note
    assert "are included" not in summary_drift.note

    exact_listing = db.list_graph_revisions(
        revision_type="rc:StagedRevision",
        include_apply_checks=True,
        drift_detail="exact",
    )
    assert exact_listing.drift_detail == "exact"
    exact_listed = {
        item.iri: item for item in exact_listing.revisions
    }[staged.revision_iri]
    exact_drift = exact_listed.application_snapshot_drifts[0]
    assert exact_drift.exact_changed_triples_available is True
    assert exact_drift.exact_changed_triples_included is True
    assert exact_drift.triples_added_since_snapshot_count == 1
    assert exact_drift.triples_removed_since_snapshot_count == 1
    assert [triple.object for triple in exact_drift.triples_added_since_snapshot] == [
        "Seed dataset renamed"
    ]

    recovery = db.plan_staged_revision_recovery([staged.revision_iri])
    assert len(recovery.lanes) == 1
    lane_drift_summary = recovery.lanes[0].exact_drift_summary
    assert len(lane_drift_summary) == 1
    assert lane_drift_summary[0].graph_role == "map"
    assert lane_drift_summary[0].blocking_reasons == ["target_digest_drift"]
    assert lane_drift_summary[0].has_count_drift is False
    assert lane_drift_summary[0].has_snapshot_digest_drift is True
    assert lane_drift_summary[0].count_drift_count == 0
    assert lane_drift_summary[0].count_drift_deltas == []
    assert lane_drift_summary[0].patch_triple_status_counts == {}
    assert lane_drift_summary[0].snapshot_triple_count == 2
    assert lane_drift_summary[0].current_triple_count == 2
    assert lane_drift_summary[0].triples_added_since_snapshot_count == 1
    assert lane_drift_summary[0].triples_removed_since_snapshot_count == 1
    assert lane_drift_summary[0].exact_changed_triples_available is True
    assert lane_drift_summary[0].exact_changed_triples_included is False
    assert lane_drift_summary[0].drift_relevance == "no_patch_subject_overlap"
    assert lane_drift_summary[0].changed_resource_count == 1
    assert lane_drift_summary[0].changed_resources[0].resource.iri == (
        "https://example.test/project#SeedDataset"
    )
    assert "raw changed triples are intentionally omitted" in (
        lane_drift_summary[0].note
    )


def test_apply_check_reports_object_and_anchor_snapshot_drift_overlap(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:OperationalIdentifier a rdfs:Class ;
            rdfs:label "Operational identifier" ;
            rdfs:comment "Identifier assignments are operational." .
        """,
        graph="ontology",
    )
    staged = db.stage_graph_revision(
        summary="Stage provisional radio identity class",
        rationale=(
            "The staged class uses OperationalIdentifier as a superclass and "
            "anchor, so same-count drift on that term should be visible."
        ),
        additions=[
            {
                "graph": "ontology",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:ProvisionalRadioIdentity a rdfs:Class ;
                        rdfs:subClassOf ex:OperationalIdentifier .
                """,
            }
        ],
        revision_anchors=["https://example.test/project#OperationalIdentifier"],
    )
    same_count_drift = db.stage_graph_revision(
        summary="Refresh operational identifier comment",
        rationale="Replace one ontology comment without changing graph count.",
        additions=[
            {
                "graph": "ontology",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:OperationalIdentifier
                        rdfs:comment "Identifier assignments are operational, not durable identity proof." .
                """,
            }
        ],
        removals=[
            {
                "graph": "ontology",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:OperationalIdentifier
                        rdfs:comment "Identifier assignments are operational." .
                """,
            }
        ],
    )
    db.apply_staged_revision(same_count_drift.revision_iri)

    check = db.check_staged_revision_apply(staged.revision_iri)

    assert check.status == "conflict"
    assert check.blocking_reasons == ["target_digest_drift"]
    assert check.count_drifts == []
    drift = check.snapshot_drifts[0]
    assert drift.snapshot_triple_count == drift.current_triple_count
    assert drift.drift_relevance == "patch_object_and_anchor_overlap"
    assert drift.patch_overlap_subjects == []
    assert drift.patch_overlap_predicates == []
    assert drift.patch_overlap_objects == [
        "https://example.test/project#OperationalIdentifier"
    ]
    assert drift.revision_anchor_overlap == [
        "https://example.test/project#OperationalIdentifier"
    ]
    assert drift.changed_resource_count == 1
    assert drift.changed_resources[0].resource.iri == (
        "https://example.test/project#OperationalIdentifier"
    )
    assert drift.changed_resources[0].matched_by == [
        "revision_anchor",
        "patch_object",
        "changed_subject",
    ]
    assert drift.changed_resource_suggested_next_actions[0].tool_name == (
        "describe_resource_revision_lineage"
    )
    assert "patch objects and revision anchors" in drift.note


def test_list_graph_revisions_routes_handled_stale_to_applied_successor(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    source = db.stage_graph_revision(
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
    db.record_map_dataset(
        "https://example.test/project#DriftMaker",
        label="Drift maker",
    )
    successor = db.restage_staged_revision(
        source.revision_iri,
        created_at="2026-06-01T10:01:00Z",
    )
    applied = db.apply_staged_revision(
        successor.revision_iri,
        created_at="2026-06-01T10:02:00Z",
    )

    listing = db.list_graph_revisions(include_apply_checks=True)
    by_iri = {item.iri: item for item in listing.revisions}
    source_row = by_iri[source.revision_iri]

    assert source_row.application_status == "conflict"
    assert source_row.restaged_by == successor.revision_iri
    assert source_row.current_restaged_by == successor.revision_iri
    assert source_row.stale_resolution_state == "stale_handled_by_restage"
    assert source_row.is_current_staged_work is False
    assert source_row.next_action is not None
    assert source_row.next_action.action_type == "inspect_already_applied"
    assert source_row.next_action.queue == "inspect_already_applied"
    assert source_row.next_action.tool_name == "describe_graph_revision"
    assert source_row.next_action.arguments == {"iri": applied.applied_revision_iri}
    assert source_row.suggested_next_actions[0].tool_name == (
        "describe_graph_revision"
    )
    assert source_row.suggested_next_actions[0].arguments == {
        "iri": applied.applied_revision_iri
    }
    assert listing.next_action_queue["inspect_already_applied"].count(
        source.revision_iri
    ) == 1
    source_queue_item = next(
        item
        for item in listing.next_action_queue_items
        if item.row_iri == source.revision_iri
    )
    assert source_queue_item.queue == "inspect_already_applied"
    assert source_queue_item.action_type == "inspect_already_applied"
    assert source_queue_item.resolved_target_iri == applied.applied_revision_iri
    assert source_queue_item.resolved_target_record_kind == "applied_event"
    assert source_queue_item.resolved_target_iri_source == (
        "next_action.arguments.iri"
    )
    assert source_queue_item.row_is_target is False
    assert source_queue_item.application_status == "conflict"
    assert source_queue_item.stale_resolution_state == "stale_handled_by_restage"
    assert source_queue_item.alternative_semantic_review_required is False
    assert listing.next_action_queue_item_counts["inspect_already_applied"] >= 1
    assert listing.semantic_review_required_queue_counts == {}

    resource_listing = db.list_resource_revisions(
        "https://example.test/project#Messages",
        include_apply_checks=True,
    )
    assert "returned page" in resource_listing.timeline_note
    assert [
        event.revision_iri for event in resource_listing.timeline
    ] == [
        source.revision_iri,
        successor.revision_iri,
        applied.applied_revision_iri,
    ]
    assert [
        event.timeline_role for event in resource_listing.timeline
    ] == [
        "restaged_source",
        "applied_source",
        "applied_event",
    ]
    timeline_by_iri = {
        event.revision_iri: event for event in resource_listing.timeline
    }
    source_event = timeline_by_iri[source.revision_iri]
    assert source_event.next_action_call == (
        "describe_graph_revision("
        f"iri='{applied.applied_revision_iri}'"
        ")"
    )
    assert source_event.resolved_target_iri == applied.applied_revision_iri
    assert source_event.resolved_target_record_kind == "applied_event"
    assert source_event.row_is_target is False
    assert timeline_by_iri[successor.revision_iri].applied_revision_iri == (
        applied.applied_revision_iri
    )
    assert timeline_by_iri[applied.applied_revision_iri].staged_revision_iri == (
        successor.revision_iri
    )


def test_list_graph_revisions_summarizes_history_and_apply_status(
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
        created_at="2026-06-01T10:00:00Z",
    )

    staged_listing = db.list_graph_revisions(
        revision_type="rc:StagedRevision",
        include_apply_checks=True,
    )
    assert staged_listing.count == 1
    assert staged_listing.returned_count == 1
    assert staged_listing.total_count == 1
    assert staged_listing.drift_detail == "summary"
    assert staged_listing.record_kind is None
    assert staged_listing.application_status is None
    assert staged_listing.staged_validation_status is None
    assert staged_listing.stale_resolution_state is None
    assert staged_listing.current_staged_work_only is False
    assert staged_listing.returned_current_staged_work_application_status_counts == {
        "ready": 1
    }
    assert staged_listing.revisions[0].iri == staged.revision_iri
    assert staged_listing.revisions[0].record_kind == "staged_patch"
    assert staged_listing.revisions[0].is_current_staged_work is True
    assert staged_listing.revisions[0].not_current_staged_work_reason is None
    assert staged_listing.revisions[0].revision_type == RC + "StagedRevision"
    assert staged_listing.revisions[0].revision_type_label == "staged revision"
    assert staged_listing.revisions[0].has_patch_payload is True
    assert staged_listing.revisions[0].patch_count == 1
    assert staged_listing.revisions[0].snapshot_evidence.status == (
        "history_plus_snapshot_rows"
    )
    assert staged_listing.revisions[0].snapshot_evidence.exact_snapshot_graph_roles == [
        "map"
    ]
    assert staged_listing.revisions[0].application_status == "ready"
    assert staged_listing.revisions[0].staged_validation_status == "conforms"
    assert staged_listing.revisions[0].application_can_apply is True
    assert staged_listing.revisions[0].stale_resolution_state == "ready"
    assert staged_listing.revisions[0].application_summary is not None
    assert staged_listing.revisions[0].application_summary.startswith("Ready to apply")
    assert staged_listing.revisions[0].application_recommended_resolution is not None
    assert staged_listing.revisions[0].application_validation_skipped_reason is None
    assert staged_listing.revisions[0].suggested_next_actions

    applied = db.apply_staged_revision(
        staged.revision_iri,
        created_at="2026-06-01T10:01:00Z",
    )
    listing = db.list_graph_revisions(include_apply_checks=True)

    assert listing.count == 2
    assert listing.returned_count == 2
    assert listing.total_count == 2
    by_iri = {item.iri: item for item in listing.revisions}
    assert by_iri[staged.revision_iri].applied_by == applied.applied_revision_iri
    assert by_iri[staged.revision_iri].application_status == "already_applied"
    assert by_iri[staged.revision_iri].stale_resolution_state == "already_applied"
    assert by_iri[staged.revision_iri].is_current_staged_work is False
    assert (
        by_iri[staged.revision_iri].not_current_staged_work_reason
        == "already_applied_source"
    )
    assert by_iri[staged.revision_iri].application_summary == (
        f"Already applied by {applied.applied_revision_iri}."
    )
    assert by_iri[staged.revision_iri].application_validation_skipped_reason == (
        "already_applied"
    )
    assert by_iri[applied.applied_revision_iri].applies_staged_revision == (
        staged.revision_iri
    )
    assert by_iri[applied.applied_revision_iri].record_kind == "applied_event"
    assert by_iri[applied.applied_revision_iri].has_patch_payload is False
    assert by_iri[applied.applied_revision_iri].patch_count == 0
    assert by_iri[applied.applied_revision_iri].application_status == "applied_event"
    assert by_iri[applied.applied_revision_iri].stale_resolution_state is None
    assert by_iri[applied.applied_revision_iri].is_current_staged_work is False
    assert (
        by_iri[applied.applied_revision_iri].not_current_staged_work_reason
        == "applied_event_record"
    )
    assert listing.revisions[0].iri == applied.applied_revision_iri

    stale = db.stage_graph_revision(
        summary="Stage other table",
        rationale="Exercise list status for count drift.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:OtherMessages a rc:Dataset .
                """,
            }
        ],
        created_at="2026-06-01T10:02:00Z",
    )
    db.record_map_dataset(
        "https://example.test/project#DriftMaker",
        label="Drift maker",
    )
    restaged = db.restage_staged_revision(
        stale.revision_iri,
        created_at="2026-06-01T10:03:00Z",
    )
    manual = db.record_graph_revision(
        summary="Record manual review note",
        rationale="Exercise current staged work reason for non-staged history.",
        changed_graphs=["map"],
        created_at="2026-06-01T10:04:00Z",
    )

    drift_listing = db.list_graph_revisions(include_apply_checks=True)
    assert drift_listing.drift_detail == "summary"
    assert "conflict" in drift_listing.returned_application_status_counts
    assert drift_listing.returned_current_staged_work_application_status_counts == {
        "ready": 1
    }
    drift_by_iri = {item.iri: item for item in drift_listing.revisions}
    stale_item = drift_by_iri[stale.revision_iri]
    assert stale_item.application_status == "conflict"
    assert stale_item.application_summary is not None
    assert stale_item.application_summary.startswith(
        "Handled by restage; inspect successor"
    )
    assert restaged.revision_iri in stale_item.application_summary
    assert stale_item.application_recommended_resolution is not None
    assert "already has a refreshed successor" in (
        stale_item.application_recommended_resolution
    )
    assert restaged.revision_iri in stale_item.application_recommended_resolution
    assert stale_item.application_validation_skipped_reason == "conflicts_present"
    assert stale_item.application_blocking_reasons == ["target_count_drift"]
    assert stale_item.application_count_drifts[0].target_graph == "map"
    assert stale_item.restaged_by == restaged.revision_iri
    assert stale_item.stale_resolution_state == "stale_handled_by_restage"
    assert stale_item.is_current_staged_work is False
    assert stale_item.not_current_staged_work_reason == "superseded_by_restage"
    assert stale_item.suggested_next_actions[-1].tool_name == "describe_staged_revision"
    assert stale_item.suggested_next_actions[-1].arguments == {
        "iri": restaged.revision_iri
    }
    assert drift_by_iri[restaged.revision_iri].restaged_from == stale.revision_iri
    assert (
        drift_by_iri[restaged.revision_iri].stale_resolution_state
        == "restaged_successor_ready"
    )
    assert drift_by_iri[restaged.revision_iri].is_current_staged_work is True
    assert (
        drift_by_iri[restaged.revision_iri].not_current_staged_work_reason is None
    )
    assert drift_by_iri[manual.revision_iri].record_kind == "history_record"
    assert drift_by_iri[manual.revision_iri].is_current_staged_work is False
    assert (
        drift_by_iri[manual.revision_iri].not_current_staged_work_reason
        == "history_record"
    )

    current_work_listing = db.list_graph_revisions(
        revision_type="rc:StagedRevision",
        current_staged_work_only=True,
    )
    assert current_work_listing.current_staged_work_only is True
    assert current_work_listing.include_apply_checks is True
    assert current_work_listing.returned_count == 1
    assert current_work_listing.total_count == 1
    assert [item.iri for item in current_work_listing.revisions] == [
        restaged.revision_iri
    ]

    ready_listing = db.list_graph_revisions(
        revision_type="rc:StagedRevision",
        application_status="ready",
        current_staged_work_only=True,
    )
    assert ready_listing.include_apply_checks is True
    assert ready_listing.application_status == "ready"
    assert ready_listing.current_staged_work_only is True
    assert [item.iri for item in ready_listing.revisions] == [restaged.revision_iri]

    stored_conforms_listing = db.list_graph_revisions(
        revision_type="rc:StagedRevision",
        staged_validation_status="conforms",
    )
    assert stored_conforms_listing.include_apply_checks is False
    assert stored_conforms_listing.staged_validation_status == "conforms"
    assert restaged.revision_iri in {
        item.iri for item in stored_conforms_listing.revisions
    }

    handled_listing = db.list_graph_revisions(
        revision_type="rc:StagedRevision",
        stale_resolution_state="stale_handled_by_restage",
    )
    assert handled_listing.include_apply_checks is True
    assert handled_listing.stale_resolution_state == "stale_handled_by_restage"
    assert [item.iri for item in handled_listing.revisions] == [stale.revision_iri]

    applied_events = db.list_graph_revisions(record_kind="applied_event")
    assert applied_events.record_kind == "applied_event"
    assert [item.iri for item in applied_events.revisions] == [
        applied.applied_revision_iri
    ]

    def page_counts(field_name: str, page) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in page.revisions:
            value = getattr(item, field_name)
            if value is None:
                continue
            counts[value] = counts.get(value, 0) + 1
        return counts

    def current_work_page_counts(field_name: str, page) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in page.revisions:
            if not item.is_current_staged_work:
                continue
            value = getattr(item, field_name)
            if value is None:
                continue
            counts[value] = counts.get(value, 0) + 1
        return counts

    def page_queue(page) -> dict[str, list[str]]:
        queues: dict[str, list[str]] = {}
        for item in page.revisions:
            if item.next_action is None:
                continue
            queues.setdefault(item.next_action.queue, []).append(item.iri)
        return queues

    def page_queue_item_counts(page) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in page.next_action_queue_items:
            counts[item.queue] = counts.get(item.queue, 0) + 1
        return counts

    def page_semantic_gate_counts(page) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in page.next_action_queue_items:
            if not item.alternative_semantic_review_required:
                continue
            counts[item.queue] = counts.get(item.queue, 0) + 1
        return counts

    full_page = db.list_graph_revisions(include_apply_checks=True)
    first_page = db.list_graph_revisions(
        include_apply_checks=True,
        limit=2,
        offset=0,
    )
    second_page = db.list_graph_revisions(
        include_apply_checks=True,
        limit=2,
        offset=2,
    )
    assert first_page.count == full_page.count
    assert second_page.count == full_page.count
    assert full_page.returned_count == len(full_page.revisions)
    assert full_page.total_count == full_page.count
    assert first_page.returned_count == 2
    assert first_page.total_count == full_page.count
    assert second_page.returned_count == 2
    assert second_page.total_count == full_page.count
    assert len(first_page.revisions) == 2
    assert len(second_page.revisions) == 2
    assert first_page.returned_application_status_counts == page_counts(
        "application_status",
        first_page,
    )
    assert first_page.returned_current_staged_work_application_status_counts == (
        current_work_page_counts(
            "application_status",
            first_page,
        )
    )
    assert first_page.returned_stale_resolution_state_counts == page_counts(
        "stale_resolution_state",
        first_page,
    )
    assert first_page.returned_staged_validation_status_counts == page_counts(
        "staged_validation_status",
        first_page,
    )
    assert first_page.next_action_queue == page_queue(first_page)
    assert first_page.next_action_queue_item_counts == page_queue_item_counts(
        first_page
    )
    assert first_page.semantic_review_required_queue_counts == (
        page_semantic_gate_counts(first_page)
    )
    assert second_page.returned_application_status_counts == page_counts(
        "application_status",
        second_page,
    )
    assert second_page.returned_current_staged_work_application_status_counts == (
        current_work_page_counts(
            "application_status",
            second_page,
        )
    )
    assert second_page.next_action_queue == page_queue(second_page)
    assert second_page.next_action_queue_item_counts == page_queue_item_counts(
        second_page
    )
    assert second_page.semantic_review_required_queue_counts == (
        page_semantic_gate_counts(second_page)
    )
    assert first_page.returned_application_status_counts != (
        full_page.returned_application_status_counts
    )
    assert first_page.next_action_queue != full_page.next_action_queue


def test_list_graph_revisions_filters_current_work_before_apply_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    applied_source = db.stage_graph_revision(
        summary="Add applied messages table",
        rationale="Creates a staged source that should be skipped by live filters.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:AppliedMessages a rc:Dataset .
                """,
            }
        ],
        created_at="2026-06-01T10:00:00Z",
    )
    db.apply_staged_revision(
        applied_source.revision_iri,
        created_at="2026-06-01T10:01:00Z",
    )
    stale = db.stage_graph_revision(
        summary="Add other messages table",
        rationale="Creates a stale staged source with a current restaged successor.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:OtherMessages a rc:Dataset .
                """,
            }
        ],
        created_at="2026-06-01T10:02:00Z",
    )
    db.record_map_dataset(
        "https://example.test/project#DriftMaker",
        label="Drift maker",
    )
    restaged = db.restage_staged_revision(
        stale.revision_iri,
        created_at="2026-06-01T10:03:00Z",
    )
    db.record_graph_revision(
        summary="Manual history note",
        rationale="Non-staged history should not need apply preview validation.",
        changed_graphs=["map"],
        created_at="2026-06-01T10:04:00Z",
    )

    checked_revision_iris: list[str] = []
    original_check = db.check_staged_revision_apply

    def counted_check(revision_iri: str):
        checked_revision_iris.append(revision_iri)
        return original_check(revision_iri)

    monkeypatch.setattr(db, "check_staged_revision_apply", counted_check)

    current_work = db.list_graph_revisions(
        current_staged_work_only=True,
        include_apply_checks=True,
    )

    assert [item.iri for item in current_work.revisions] == [restaged.revision_iri]
    assert checked_revision_iris == [restaged.revision_iri]
    assert current_work.count == 1
    assert current_work.returned_count == 1
    assert current_work.revisions[0].application_status == "ready"


def test_list_graph_versions_lists_stored_graph_timeline(
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
        created_at="2026-06-01T10:00:00Z",
    )
    applied = db.apply_staged_revision(
        staged.revision_iri,
        created_at="2026-06-01T10:01:00Z",
    )

    versions = db.list_graph_versions("map")

    assert versions.graph_role == "map"
    assert versions.graph == "history"
    assert versions.exact_only is False
    assert versions.include_current is True
    assert versions.count == 2
    assert versions.total_count == 2
    assert versions.returned_count == 2
    assert versions.current_graph is not None
    assert versions.current_graph.graph_role == "map"
    assert versions.current_graph.triple_count == db.triple_count("map")
    assert versions.current_graph.content_digest == db._graph_content_digest("map")
    assert versions.snapshot_evidence_status_counts == {
        "history_plus_snapshot_rows": 2
    }
    assert versions.exact_snapshot_available_count == 2
    assert "not a temporal checkout engine" in versions.note

    rows_by_iri = {item.revision_iri: item for item in versions.versions}
    staged_row = rows_by_iri[staged.revision_iri]
    applied_row = rows_by_iri[applied.applied_revision_iri]

    assert staged_row.record_kind == "staged_patch"
    assert staged_row.snapshot_semantics == "staged_before_graph"
    assert staged_row.summary == "Stage messages table"
    assert staged_row.created_at == "2026-06-01T10:00:00+00:00"
    assert staged_row.changed_graphs == ["map"]
    assert staged_row.included_graphs == ["map"]
    assert staged_row.is_current_staged_work is False
    assert staged_row.not_current_staged_work_reason == "already_applied_source"
    assert staged_row.review_resolution is None
    assert staged_row.triple_count == 0
    assert staged_row.count_basis == "stored_snapshot_rows"
    assert staged_row.exact_snapshot_available is True
    assert staged_row.snapshot_evidence_status == "history_plus_snapshot_rows"
    assert staged_row.suggested_next_actions[0].tool_name == (
        "describe_revision_graph_snapshot"
    )
    assert staged_row.suggested_next_actions[1].tool_name == (
        "describe_revision_lineage"
    )
    assert staged_row.suggested_next_actions[1].arguments == {
        "iri": staged.revision_iri
    }
    assert staged_row.suggested_next_actions[2].tool_name == (
        "describe_graph_version_diff"
    )
    assert staged_row.suggested_next_actions[2].arguments == {
        "graph_role": "map",
        "before_revision_iri": staged.revision_iri,
        "compare_to_current": True,
    }

    assert applied_row.record_kind == "applied_event"
    assert applied_row.snapshot_semantics == "applied_after_graph"
    assert applied_row.created_at == "2026-06-01T10:01:00+00:00"
    assert applied_row.applies_staged_revision == staged.revision_iri
    assert applied_row.is_current_staged_work is False
    assert applied_row.not_current_staged_work_reason == "applied_event_record"
    assert applied_row.review_resolution is None
    assert applied_row.triple_count == db.triple_count("map")
    assert applied_row.exact_snapshot_available is True
    assert [
        action.tool_name for action in applied_row.suggested_next_actions
    ] == [
        "describe_revision_graph_snapshot",
        "describe_revision_lineage",
        "describe_graph_version_diff",
    ]
    assert applied_row.suggested_next_actions[1].arguments == {
        "iri": applied.applied_revision_iri
    }

    exact_staged = db.list_graph_versions(
        "map",
        exact_only=True,
        include_current=False,
        record_kind="staged_patch",
    )
    assert exact_staged.exact_only is True
    assert exact_staged.include_current is False
    assert exact_staged.record_kind == "staged_patch"
    assert exact_staged.current_graph is None
    assert [item.revision_iri for item in exact_staged.versions] == [
        staged.revision_iri
    ]

    first_page = db.list_graph_versions("map", limit=1, offset=0)
    second_page = db.list_graph_versions("map", limit=1, offset=1)
    assert first_page.count == 2
    assert first_page.returned_count == 1
    assert first_page.versions[0].revision_iri == applied.applied_revision_iri
    assert second_page.count == 2
    assert second_page.returned_count == 1
    assert second_page.versions[0].revision_iri == staged.revision_iri


def test_describe_graph_version_diff_compares_versions_and_current(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    first_staged = db.stage_graph_revision(
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
    first_applied = db.apply_staged_revision(
        first_staged.revision_iri,
        created_at="2026-06-01T10:01:00Z",
    )
    second_staged = db.stage_graph_revision(
        summary="Stage messages label and orders table",
        rationale="A later revision extends the map after the first snapshot.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Messages rdfs:label "Messages" .
                    ex:Orders a rc:Dataset .
                """,
            }
        ],
        created_at="2026-06-01T10:02:00Z",
    )
    second_applied = db.apply_staged_revision(
        second_staged.revision_iri,
        created_at="2026-06-01T10:03:00Z",
    )

    stored_diff = db.describe_graph_version_diff(
        "map",
        first_staged.revision_iri,
        after_revision_iri=first_applied.applied_revision_iri,
    )

    assert stored_diff.graph_role == "map"
    assert stored_diff.graph == "history"
    assert stored_diff.before_revision_iri == first_staged.revision_iri
    assert stored_diff.after_revision_iri == first_applied.applied_revision_iri
    assert stored_diff.compare_to_current is False
    assert stored_diff.after_target_kind == "stored_revision_snapshot"
    assert stored_diff.before_revision_context is not None
    assert stored_diff.before_revision_context.record_kind == "staged_patch"
    assert stored_diff.before_revision_context.snapshot_semantics == (
        "staged_before_graph"
    )
    assert stored_diff.before_revision_context.applied_by == (
        first_applied.applied_revision_iri
    )
    assert stored_diff.after_revision_context is not None
    assert stored_diff.after_revision_context.record_kind == "applied_event"
    assert stored_diff.after_revision_context.snapshot_semantics == (
        "applied_after_graph"
    )
    assert stored_diff.after_revision_context.applies_staged_revision == (
        first_staged.revision_iri
    )
    assert stored_diff.related_revision_iris == [
        first_applied.applied_revision_iri,
        first_staged.revision_iri,
    ]
    assert stored_diff.before_snapshot.triple_count == 0
    assert stored_diff.after_snapshot is not None
    assert stored_diff.after_snapshot.triple_count == 1
    assert stored_diff.current_graph is None
    assert stored_diff.count_basis == "target_graph_only"
    assert stored_diff.before_triple_count == 0
    assert stored_diff.after_triple_count == 1
    assert stored_diff.count_delta == 1
    assert stored_diff.digest_changed is True
    assert stored_diff.exact_changed_triples_available is True
    assert stored_diff.exact_changed_triples_included is False
    assert stored_diff.triples_added_count == 1
    assert stored_diff.triples_removed_count == 0
    assert stored_diff.triples_added_truncated is True
    assert stored_diff.triples_removed_truncated is False
    assert stored_diff.changed_resource_count == 2
    assert stored_diff.changed_resources_returned_count == 2
    assert stored_diff.changed_resources_omitted_count == 0
    assert [item.resource.iri for item in stored_diff.changed_resources] == [
        "https://example.test/project#Messages",
        "https://richcanopy.org/ns/rc#Dataset",
    ]
    assert stored_diff.changed_resources[0].matched_by == [
        "patch_subject",
        "changed_subject",
    ]
    assert stored_diff.changed_resources[1].matched_by == [
        "patch_object",
        "changed_object",
    ]
    assert [
        action.tool_name
        for action in stored_diff.changed_resource_suggested_next_actions
    ] == [
        "describe_resource_revision_lineage",
        "describe_resource_revision_lineage",
    ]
    assert [
        action.arguments
        for action in stored_diff.changed_resource_suggested_next_actions
    ] == [
        {
            "resource_iri": "https://example.test/project#Messages",
            "revision_iri": first_staged.revision_iri,
        },
        {
            "resource_iri": "https://richcanopy.org/ns/rc#Dataset",
            "revision_iri": first_staged.revision_iri,
        },
    ]
    assert [action.tool_name for action in stored_diff.suggested_next_actions] == [
        "describe_revision_graph_snapshot",
        "describe_revision_graph_snapshot",
        "describe_revision_lineage",
        "describe_revision_lineage",
        "describe_applied_revision_diff",
        "describe_graph_version_diff",
    ]
    assert stored_diff.suggested_next_actions[2].arguments == {
        "iri": first_staged.revision_iri,
    }
    assert stored_diff.suggested_next_actions[4].arguments == {
        "iri": first_applied.applied_revision_iri,
    }

    current_diff = db.describe_graph_version_diff(
        "map",
        first_applied.applied_revision_iri,
        include_triples=True,
        max_triples=1,
    )

    assert current_diff.after_revision_iri is None
    assert current_diff.compare_to_current is True
    assert current_diff.after_target_kind == "current_graph"
    assert current_diff.before_snapshot.triple_count == 1
    assert current_diff.after_snapshot is None
    assert current_diff.current_graph is not None
    assert current_diff.current_graph.triple_count == db.triple_count("map")
    assert current_diff.after_triple_count == db.triple_count("map")
    assert current_diff.count_delta == 2
    assert current_diff.digest_changed is True
    assert current_diff.exact_changed_triples_available is True
    assert current_diff.exact_changed_triples_included is True
    assert current_diff.triples_added_count == 2
    assert current_diff.triples_removed_count == 0
    assert current_diff.triples_added_truncated is True
    assert current_diff.triples_removed_truncated is False
    assert current_diff.max_triples == 1
    assert len(current_diff.triples_added) == 1
    assert current_diff.triples_removed == []
    assert current_diff.changed_resource_count == 3
    assert [item.resource.iri for item in current_diff.changed_resources] == [
        "https://example.test/project#Messages",
        "https://example.test/project#Orders",
        "https://richcanopy.org/ns/rc#Dataset",
    ]
    assert current_diff.changed_resources[0].matched_by == ["changed_subject"]
    assert current_diff.changed_resources[1].matched_by == ["changed_subject"]
    assert current_diff.changed_resources[2].matched_by == ["changed_object"]
    assert [
        action.tool_name
        for action in current_diff.changed_resource_suggested_next_actions
    ] == [
        "list_resource_revisions",
        "list_resource_revisions",
        "list_resource_revisions",
    ]
    assert {triple.subject for triple in current_diff.triples_added} <= {
        "https://example.test/project#Messages",
        "https://example.test/project#Orders",
    }
    assert "Exact graph-version changed triples" in current_diff.note

    same_current_diff = db.describe_graph_version_diff(
        "map",
        second_applied.applied_revision_iri,
    )
    assert same_current_diff.count_delta == 0
    assert same_current_diff.digest_changed is False
    assert same_current_diff.triples_added_count == 0
    assert same_current_diff.triples_removed_count == 0
    assert [
        action.tool_name for action in same_current_diff.suggested_next_actions
    ] == [
        "describe_revision_graph_snapshot",
        "describe_revision_lineage",
        "describe_applied_revision_diff",
    ]

    third_staged = db.stage_graph_revision(
        summary="Stage tickets table",
        rationale=(
            "A staged row can need recovery inspection even when its before "
            "snapshot is identical to the current graph."
        ),
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Tickets a rc:Dataset .
                """,
            }
        ],
        created_at="2026-06-01T10:04:00Z",
    )
    staged_to_current = db.describe_graph_version_diff(
        "map",
        third_staged.revision_iri,
    )
    assert staged_to_current.count_delta == 0
    assert staged_to_current.digest_changed is False
    assert staged_to_current.before_revision_context is not None
    assert staged_to_current.before_revision_context.record_kind == "staged_patch"
    assert staged_to_current.before_revision_context.application_status == "ready"
    assert staged_to_current.before_revision_context.is_current_staged_work is True
    assert staged_to_current.before_revision_context.related_revision_iris == []
    assert [
        action.tool_name for action in staged_to_current.suggested_next_actions
    ] == [
        "describe_revision_graph_snapshot",
        "describe_revision_lineage",
    ]

    with pytest.raises(DoxaBaseError, match="after_revision_iri is required"):
        db.describe_graph_version_diff(
            "map",
            first_applied.applied_revision_iri,
            compare_to_current=False,
        )
    with pytest.raises(DoxaBaseError, match="max_triples must be at least 1"):
        db.describe_graph_version_diff(
            "map",
            first_applied.applied_revision_iri,
            max_triples=0,
        )


def test_lineage_queue_items_carry_alternative_set_membership(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    source = db.stage_graph_revision(
        summary="Model Orders as events",
        rationale="Source framing for choose-one review.",
        revision_anchors=[orders],
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
    alternative = db.stage_graph_revision(
        summary="Model Orders as snapshots",
        rationale="Alternative framing for choose-one review.",
        revision_anchors=[orders],
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
        created_at="2026-06-01T10:01:00Z",
    )
    expected_set = {source.revision_iri, alternative.revision_iri}

    def assert_queue_item_membership(
        item: RevisionNextActionQueueItem | None,
        *,
        row_iri: str,
        role: str,
    ) -> None:
        assert item is not None
        assert item.row_iri == row_iri
        assert set(item.alternative_set_iris) == expected_set
        assert item.alternative_set_source_iri == source.revision_iri
        assert item.alternative_set_role == role

    graph_source = db.describe_revision_lineage(source.revision_iri)
    graph_alternative = db.describe_revision_lineage(alternative.revision_iri)
    resource_source = db.describe_resource_revision_lineage(
        orders,
        source.revision_iri,
    )
    resource_alternative = db.describe_resource_revision_lineage(
        orders,
        alternative.revision_iri,
    )

    assert_queue_item_membership(
        graph_source.next_action_queue_item,
        row_iri=source.revision_iri,
        role="source",
    )
    assert_queue_item_membership(
        graph_alternative.next_action_queue_item,
        row_iri=alternative.revision_iri,
        role="alternative",
    )
    assert_queue_item_membership(
        resource_source.next_action_queue_item,
        row_iri=source.revision_iri,
        role="source",
    )
    assert_queue_item_membership(
        resource_alternative.next_action_queue_item,
        row_iri=alternative.revision_iri,
        role="alternative",
    )


def test_describe_revision_lineage_warns_about_imported_odd_history(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    source_iri = "https://example.test/project#ambiguous-source"
    successor_a_iri = "https://example.test/project#ambiguous-a-successor"
    successor_z_iri = "https://example.test/project#ambiguous-z-successor"
    manual_iri = "https://example.test/project#manual-restage-note"
    parallel_applied_iri = "https://example.test/project#parallel-applied-event"
    missing_source_iri = "https://example.test/project#missing-applied-source"
    applied_iri = "https://example.test/project#applied-event-missing-source"
    source_dataset_iri = "https://example.test/project#SourceDataset"

    source = db.stage_graph_revision(
        summary="Source proposal",
        rationale="Keep an imported-lineage source available.",
        revision_iri=source_iri,
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:SourceDataset a rc:Dataset .
                """,
            }
        ],
        created_at="2026-06-01T10:00:00Z",
    )
    successor_a = db.stage_graph_revision(
        summary="First successor",
        rationale="Caller-authored restage successor A.",
        revision_iri=successor_a_iri,
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:SuccessorA a rc:Dataset .
                """,
            }
        ],
        restages_revision=source.revision_iri,
        created_at="2026-06-01T10:01:00Z",
    )
    db.import_turtle(
        f"""
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        <{successor_z_iri}> a rc:GraphRevision ;
            rc:summary "Imported parallel successor" ;
            rc:revisionType rc:StagedRevision ;
            rc:hasGraphPatch ex:ambiguousZPatch ;
            rc:restagesRevision <{source.revision_iri}> ;
            rc:createdAt "2026-06-01T10:02:00Z" .

        ex:ambiguousZPatch a rc:GraphPatch .

        <{manual_iri}> a rc:GraphRevision ;
            rc:summary "Manual restage note" ;
            rc:revisionType rc:ManualRevision ;
            rc:restagesRevision <{successor_a.revision_iri}> ;
            rc:createdAt "2026-06-01T10:03:00Z" .

        <{parallel_applied_iri}> a rc:GraphRevision ;
            rc:summary "Applied parallel successor" ;
            rc:revisionType rc:AppliedStagedRevision ;
            rc:appliesStagedRevision <{successor_z_iri}> ;
            rc:createdAt "2026-06-01T10:03:30Z" .

        <{applied_iri}> a rc:GraphRevision ;
            rc:summary "Applied event missing source" ;
            rc:revisionType rc:AppliedStagedRevision ;
            rc:appliesStagedRevision <{missing_source_iri}> ;
            rc:createdAt "2026-06-01T10:04:00Z" .
        """,
        graph="history",
    )

    source_lineage = db.describe_revision_lineage(source.revision_iri)

    assert source_lineage.restage_chain_iris == [
        source.revision_iri,
        successor_a.revision_iri,
        manual_iri,
    ]
    assert {
        successor_a.revision_iri,
        successor_z_iri,
        manual_iri,
        parallel_applied_iri,
    }.issubset(set(source_lineage.related_revision_iris))
    assert any(
        "multiple visible successors" in warning
        and successor_a.revision_iri in warning
        and successor_z_iri in warning
        for warning in source_lineage.warnings
    )
    assert any(
        "non-staged revision" in warning
        and manual_iri in warning
        and "history_record" in warning
        for warning in source_lineage.warnings
    )
    resource_lineage = db.describe_resource_revision_lineage(
        source_dataset_iri,
        source.revision_iri,
    )
    assert {
        successor_a.revision_iri,
        successor_z_iri,
        manual_iri,
        parallel_applied_iri,
    }.issubset(set(resource_lineage.related_revision_iris))
    assert any(
        "multiple visible successors" in warning
        and successor_a.revision_iri in warning
        and successor_z_iri in warning
        for warning in resource_lineage.warnings
    )
    export = db.export_staged_revisions(
        [source.revision_iri],
        tmp_path / "parallel-successor-review.md",
    )
    assert parallel_applied_iri in (
        export.bundle_summary.recommended_applied_inspection_iris
    )
    assert any(
        "Parallel restage successor" in warning
        and successor_z_iri in warning
        and parallel_applied_iri in warning
        for warning in export.bundle_summary.warnings
    )

    missing_source_lineage = db.describe_revision_lineage(applied_iri)

    assert missing_source_lineage.selected_role == "applied_event"
    assert missing_source_lineage.applied_revision_iri == applied_iri
    assert missing_source_lineage.staged_revision_iri is None
    assert missing_source_lineage.restage_chain_iris == []
    assert any(
        "points to missing staged source" in warning
        and missing_source_iri in warning
        for warning in missing_source_lineage.warnings
    )


def test_list_resource_revisions_finds_anchors_patches_and_applied_sources(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    other = "https://example.test/project#OtherOrders"
    db.record_map_dataset(orders, label="Orders", is_table=True)

    anchored = db.stage_graph_revision(
        summary="Classify Orders as current table",
        rationale="Anchor and patch should both mention Orders.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders a rc:Table .
                """,
            }
        ],
        revision_anchors=[orders],
        created_at="2026-06-01T10:00:00Z",
    )
    unanchored = db.stage_graph_revision(
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
        created_at="2026-06-01T10:01:00Z",
    )
    applied = db.apply_staged_revision(
        unanchored.revision_iri,
        created_at="2026-06-01T10:02:00Z",
    )
    unrelated = db.stage_graph_revision(
        summary="Add unrelated table",
        rationale="This proposal should not appear in the Orders resource list.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:OtherOrders a rc:Dataset .
                """,
            }
        ],
        revision_anchors=[other],
        created_at="2026-06-01T10:03:00Z",
    )

    listing = db.list_resource_revisions(orders)

    assert listing.resource.iri == orders
    assert listing.include_patch_mentions is True
    assert listing.patch_mention_scan.status == "complete"
    assert listing.patch_mention_scan.unreadable_patch_count == 0
    assert listing.patch_mention_scan.unreadable_revision_count == 0
    assert listing.patch_mention_scan.omitted_match_risk is False
    assert listing.include_apply_checks is True
    assert listing.count == 3
    by_iri = {item.revision.iri: item for item in listing.revisions}
    assert {item.revision_iri for item in listing.revisions} == set(by_iri)
    assert set(by_iri) == {
        anchored.revision_iri,
        unanchored.revision_iri,
        applied.applied_revision_iri,
    }
    assert unrelated.revision_iri not in by_iri

    anchored_item = by_iri[anchored.revision_iri]
    assert anchored_item.revision_anchor_match is True
    assert anchored_item.patch_mention_match is True
    assert anchored_item.match_types == ["revision_anchor", "patch_subject"]
    assert anchored_item.patch_mentions[0].matched_term_roles == ["subject"]
    assert anchored_item.patch_mentions[0].matched_triples == 1
    assert anchored_item.patch_mentions[0].triple_count == 1
    assert anchored_item.patch_mentions_incomplete is False
    assert anchored_item.patch_mentions_unreadable_count == 0
    assert anchored_item.revision.application_status == "conflict"
    assert anchored_item.revision.stale_resolution_state == "stale_unresolved"

    unanchored_item = by_iri[unanchored.revision_iri]
    assert unanchored_item.revision_anchor_match is False
    assert unanchored_item.patch_mention_match is True
    assert unanchored_item.match_types == ["patch_subject"]
    assert unanchored_item.revision.application_status == "already_applied"

    applied_item = by_iri[applied.applied_revision_iri]
    assert applied_item.revision.record_kind == "applied_event"
    assert applied_item.applied_source_match is True
    assert applied_item.applied_source_revision_iri == unanchored.revision_iri
    assert applied_item.match_types == ["applied_source_patch_subject"]
    assert applied_item.applied_source_patch_mentions[0].target_graph == "map"
    assert applied_item.applied_source_patch_mentions[0].matched_triples == 1
    assert applied_item.applied_source_patch_mentions_incomplete is False
    assert applied_item.applied_source_patch_mentions_unreadable_count == 0
    lineage = db.describe_resource_revision_lineage(
        orders,
        applied.applied_revision_iri,
        include_triples=True,
    )
    assert lineage.resource.iri == orders
    assert lineage.selected_revision.revision.iri == applied.applied_revision_iri
    assert lineage.selected_revision_iri == applied.applied_revision_iri
    assert lineage.selected_role == "applied_event"
    assert lineage.paired_revision is not None
    assert lineage.paired_revision.revision.iri == unanchored.revision_iri
    assert lineage.paired_revision_iri == unanchored.revision_iri
    assert lineage.paired_role == "applied_source"
    assert lineage.applied_revision_iri == applied.applied_revision_iri
    assert lineage.staged_revision_iri == unanchored.revision_iri
    assert lineage.current_staged_revision_iri is None
    assert lineage.current_revision_iri is None
    assert lineage.latest_revision_iri == applied.applied_revision_iri
    assert lineage.latest_role == "applied_event"
    assert lineage.restage_chain_iris == [unanchored.revision_iri]
    assert lineage.alternative_revision_iris == []
    assert lineage.related_revision_iris == [
        applied.applied_revision_iri,
        unanchored.revision_iri,
    ]
    assert lineage.patch_mention_scan.status == "complete"
    assert lineage.applied_diff_status == "available"
    assert lineage.applied_diff is not None
    assert lineage.applied_diff.changed_graphs == ["map"]
    assert lineage.applied_diff.include_triples is True
    map_diff = lineage.applied_diff.graph_diffs[0]
    assert map_diff.graph_role == "map"
    assert map_diff.count_basis == "target_graph_only"
    assert map_diff.exact_changed_triples_available is True
    assert map_diff.exact_changed_triples_included is True
    assert map_diff.resource_triples_added_count == 1
    assert map_diff.resource_triples_removed_count == 0
    assert map_diff.resource_triples_added[0].subject == orders
    assert map_diff.resource_triples_added_truncated is False

    source_lineage = db.describe_resource_revision_lineage(
        orders,
        unanchored.revision_iri,
        include_applied_diff=False,
    )
    assert source_lineage.selected_role == "applied_source"
    assert source_lineage.selected_revision_iri == unanchored.revision_iri
    assert source_lineage.paired_revision is not None
    assert source_lineage.paired_revision.revision.iri == applied.applied_revision_iri
    assert source_lineage.paired_revision_iri == applied.applied_revision_iri
    assert source_lineage.latest_revision_iri == applied.applied_revision_iri
    assert source_lineage.latest_role == "applied_event"
    assert source_lineage.next_action_queue_item is not None
    assert source_lineage.next_action_queue_item.row_iri == unanchored.revision_iri
    assert (
        source_lineage.next_action_queue_item.resolved_target_iri
        == applied.applied_revision_iri
    )
    assert source_lineage.next_action_queue_item.row_is_target is False
    assert (
        source_lineage.next_action_queue_item.resolved_target_record_kind
        == "applied_event"
    )
    assert source_lineage.applied_diff_status == "omitted"
    assert source_lineage.applied_diff is None

    anchor_only = db.list_resource_revisions(orders, include_patch_mentions=False)
    assert anchor_only.patch_mention_scan.status == "not_requested"
    assert anchor_only.patch_mention_scan.unreadable_patch_count == 0
    assert anchor_only.patch_mention_scan.omitted_match_risk is False
    assert anchor_only.count == 1
    assert anchor_only.revisions[0].revision.iri == anchored.revision_iri
    assert anchor_only.revisions[0].match_types == ["revision_anchor"]


def test_list_resource_revisions_recovers_imported_applied_source_anchors(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    source_iri = "https://example.test/project#ImportedStagedSource"
    applied_iri = "https://example.test/project#ImportedAppliedEvent"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    db.record_graph_revision(
        summary="Imported staged source with anchors only",
        rationale="Imported handoff preserved anchors but omitted patch payloads.",
        changed_graphs=["map"],
        revision_type="rc:StagedRevision",
        revision_iri=source_iri,
        revision_anchors=[orders],
        created_at="2026-06-01T10:00:00Z",
    )
    db.import_trig(
        f"""
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        GRAPH <https://richcanopy.org/graph/history> {{
            ex:ImportedAppliedEvent a rc:GraphRevision ;
                rc:revisionType rc:AppliedStagedRevision ;
                rc:summary "Imported applied event" ;
                rc:revisionRationale "Applied an imported staged source." ;
                rc:changedGraph "map" ;
                rc:createdAt "2026-06-01T10:01:00Z"^^xsd:dateTime ;
                rc:appliesStagedRevision <{source_iri}> .
        }}
        """
    )

    listing = db.list_resource_revisions(orders)

    assert listing.patch_mention_scan.status == "complete"
    assert listing.patch_mention_scan.omitted_match_risk is False
    by_iri = {item.revision.iri: item for item in listing.revisions}
    assert set(by_iri) == {source_iri, applied_iri}
    source_item = by_iri[source_iri]
    assert source_item.revision_anchor_match is True
    assert source_item.match_types == ["revision_anchor"]
    applied_item = by_iri[applied_iri]
    assert applied_item.revision.record_kind == "applied_event"
    assert applied_item.applied_source_match is True
    assert applied_item.applied_source_revision_iri == source_iri
    assert applied_item.match_types == ["applied_source_revision_anchor"]
    assert applied_item.applied_source_patch_mentions == []
    assert applied_item.applied_source_patch_mentions_incomplete is False
    assert applied_item.applied_source_patch_mentions_unreadable_count == 0
    lineage = db.describe_resource_revision_lineage(orders, applied_iri)
    assert lineage.selected_revision.revision.iri == applied_iri
    assert lineage.selected_role == "applied_event"
    assert lineage.paired_revision is not None
    assert lineage.paired_revision.revision.iri == source_iri
    assert lineage.paired_role == "applied_source"
    assert lineage.applied_revision_iri == applied_iri
    assert lineage.staged_revision_iri == source_iri
    assert lineage.applied_source_revision_iri == source_iri
    assert lineage.applied_diff_status == "unavailable"
    assert lineage.applied_diff is not None
    assert lineage.applied_diff.graph_diffs[0].exact_changed_triples_available is False

    without_patch_mentions = db.list_resource_revisions(
        orders,
        include_patch_mentions=False,
    )
    assert {
        item.revision.iri: item.match_types
        for item in without_patch_mentions.revisions
    } == {
        source_iri: ["revision_anchor"],
        applied_iri: ["applied_source_revision_anchor"],
    }
    patch_only = db.stage_graph_revision(
        summary="Unanchored Orders patch",
        rationale="Patch payload mentions Orders without anchoring it.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders rc:hasKnownCaveat ex:OrdersPatchOnlyCaveat .
                """,
            }
        ],
    )
    with_patch_mentions = db.describe_resource_revision_lineage(
        orders,
        patch_only.revision_iri,
    )
    assert (
        with_patch_mentions.selected_revision.revision.iri
        == patch_only.revision_iri
    )
    assert with_patch_mentions.selected_revision.match_types == ["patch_subject"]
    with pytest.raises(DoxaBaseError) as disabled_scan_excinfo:
        db.describe_resource_revision_lineage(
            orders,
            patch_only.revision_iri,
            include_patch_mentions=False,
        )
    disabled_scan_message = str(disabled_scan_excinfo.value)
    assert "patch payload scanning was disabled" in disabled_scan_message
    assert "include_patch_mentions=True" in disabled_scan_message
    assert "Revision exists in history" in disabled_scan_message


def test_list_resource_revisions_defers_apply_checks_until_after_resource_page(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    old_relevant = db.stage_graph_revision(
        summary="Add old Orders note",
        rationale="Relevant but outside the first returned resource page.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Orders rdfs:comment "Old Orders note." .
                """,
            }
        ],
        created_at="2026-06-01T10:00:00Z",
    )
    new_relevant = db.stage_graph_revision(
        summary="Add new Orders note",
        rationale="Relevant and inside the first returned resource page.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Orders rdfs:comment "New Orders note." .
                """,
            }
        ],
        created_at="2026-06-01T10:01:00Z",
    )
    for index in range(4):
        db.stage_graph_revision(
            summary=f"Add unrelated table {index}",
            rationale="Unrelated staged noise should not require apply checks.",
            additions=[
                {
                    "graph": "map",
                    "content": f"""
                        @prefix ex: <https://example.test/project#> .
                        @prefix rc: <https://richcanopy.org/ns/rc#> .

                        ex:Unrelated{index} a rc:Dataset .
                    """,
                }
            ],
            created_at=f"2026-06-01T10:0{index + 2}:00Z",
        )

    checked_revision_iris: list[str] = []
    original_check = db.check_staged_revision_apply

    def counted_check(revision_iri: str):
        checked_revision_iris.append(revision_iri)
        return original_check(revision_iri)

    monkeypatch.setattr(db, "check_staged_revision_apply", counted_check)

    listing = db.list_resource_revisions(
        orders,
        include_apply_checks=True,
        limit=1,
        offset=0,
    )

    assert listing.count == 2
    assert listing.returned_count == 1
    assert [item.revision.iri for item in listing.revisions] == [
        new_relevant.revision_iri
    ]
    assert old_relevant.revision_iri not in checked_revision_iris
    assert checked_revision_iris == [new_relevant.revision_iri]
    assert listing.revisions[0].revision.application_status == "ready"
    assert listing.next_action_queue == {
        "apply_after_review": [new_relevant.revision_iri]
    }


def test_list_resource_revisions_filters_noisy_patch_only_current_work(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    applied_source = db.stage_graph_revision(
        summary="Add applied Orders note",
        rationale="Creates historical patch-only rows for the resource family.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Orders rdfs:comment "Historical applied note." .
                """,
            }
        ],
        created_at="2026-06-01T10:00:00Z",
    )
    applied_source_event = db.apply_staged_revision(
        applied_source.revision_iri,
        created_at="2026-06-01T10:01:00Z",
    )
    stale_simple = db.stage_graph_revision(
        summary="Add current Orders note",
        rationale="Patch-only current work should survive live-work filtering.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Orders rdfs:comment "Current operations note." .
                """,
            }
        ],
        created_at="2026-06-01T10:02:00Z",
    )
    applied_alternative = db.stage_graph_revision(
        summary="Model Orders as event rows",
        rationale="First semantic alternative for review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Orders rdfs:comment "Event-row interpretation." .
                """,
            }
        ],
        created_at="2026-06-01T10:03:00Z",
    )
    stale_alternative = db.stage_graph_revision(
        summary="Model Orders as snapshot rows",
        rationale="Competing semantic alternative for review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Orders rdfs:comment "Snapshot-row interpretation." .
                """,
            }
        ],
        alternative_to=applied_alternative.revision_iri,
        created_at="2026-06-01T10:04:00Z",
    )
    applied_alternative_event = db.apply_staged_revision(
        applied_alternative.revision_iri,
        created_at="2026-06-01T10:05:00Z",
    )
    simple_current = db.restage_staged_revision(
        stale_simple.revision_iri,
        created_at="2026-06-01T10:06:00Z",
    )
    semantic_current = db.restage_staged_revision(
        stale_alternative.revision_iri,
        created_at="2026-06-01T10:07:00Z",
    )
    manual_history = db.record_graph_revision(
        summary="Manual Orders review note",
        rationale="Newest anchored non-staged history should not enter live work.",
        changed_graphs=["map"],
        revision_anchors=[orders],
        created_at="2026-06-01T10:08:00Z",
    )

    full_page = db.list_resource_revisions(
        orders,
        include_apply_checks=True,
        limit=1,
        offset=0,
    )
    assert full_page.count == 9
    assert full_page.returned_count == 1
    assert full_page.total_count == 9
    assert full_page.revisions[0].revision.iri == manual_history.revision_iri
    full_listing = db.list_resource_revisions(
        orders,
        include_apply_checks=True,
    )
    by_iri = {item.revision.iri: item for item in full_listing.revisions}
    assert by_iri[manual_history.revision_iri].revision.record_kind == (
        "history_record"
    )
    assert by_iri[applied_source.revision_iri].revision.application_status == (
        "already_applied"
    )
    assert by_iri[applied_source_event.applied_revision_iri].revision.record_kind == (
        "applied_event"
    )
    assert by_iri[stale_simple.revision_iri].revision.stale_resolution_state == (
        "stale_handled_by_restage"
    )
    assert by_iri[stale_alternative.revision_iri].revision.stale_resolution_state == (
        "stale_handled_by_restage"
    )

    live_listing = db.list_resource_revisions(
        orders,
        include_apply_checks=False,
        current_staged_work_only=True,
    )
    assert live_listing.current_staged_work_only is True
    assert live_listing.include_apply_checks is True
    assert live_listing.count == 2
    assert live_listing.returned_count == 2
    assert live_listing.total_count == 2
    assert [item.revision.iri for item in live_listing.revisions] == [
        semantic_current.revision_iri,
        simple_current.revision_iri,
    ]
    assert [item.match_types for item in live_listing.revisions] == [
        ["patch_subject"],
        ["patch_subject"],
    ]
    assert all(
        item.revision.is_current_staged_work for item in live_listing.revisions
    )
    assert live_listing.next_action_queue == {
        "apply_after_review": [
            semantic_current.revision_iri,
            simple_current.revision_iri,
        ]
    }
    semantic_queue_item = next(
        item
        for item in live_listing.next_action_queue_items
        if item.row_iri == semantic_current.revision_iri
    )
    assert semantic_queue_item.row_is_target is True
    assert semantic_queue_item.resolved_target_iri == semantic_current.revision_iri
    assert semantic_queue_item.alternative_semantic_review_required is True
    assert semantic_queue_item.alternative_applied_source_iri == (
        applied_alternative.revision_iri
    )
    assert semantic_queue_item.alternative_applied_revision_iri == (
        applied_alternative_event.applied_revision_iri
    )

    first_live_page = db.list_resource_revisions(
        orders,
        current_staged_work_only=True,
        limit=1,
        offset=0,
    )
    second_live_page = db.list_resource_revisions(
        orders,
        current_staged_work_only=True,
        limit=1,
        offset=1,
    )
    assert first_live_page.count == 2
    assert second_live_page.count == 2
    assert first_live_page.returned_count == 1
    assert first_live_page.total_count == 2
    assert second_live_page.returned_count == 1
    assert second_live_page.total_count == 2
    assert first_live_page.revisions[0].revision.iri == semantic_current.revision_iri
    assert second_live_page.revisions[0].revision.iri == simple_current.revision_iri

    hidden_patch_only_live_work = db.list_resource_revisions(
        orders,
        include_patch_mentions=False,
        current_staged_work_only=True,
    )
    assert hidden_patch_only_live_work.count == 0
    assert hidden_patch_only_live_work.patch_mention_scan.status == "not_requested"


def test_list_resource_revisions_marks_unreadable_patch_mentions_incomplete(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    staged = db.stage_graph_revision(
        summary="Malformed anchored patch for Orders",
        rationale="Anchor keeps the revision discoverable despite bad patch RDF.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders a rc:Table .
                """,
            }
        ],
        revision_anchors=[orders],
    )
    _corrupt_staged_patch_content(
        db,
        staged.patches[0].patch_iri,
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:Orders a rc:Table
        ex:Other a rc:Dataset .
        """,
    )
    unanchored = db.stage_graph_revision(
        summary="Malformed unanchored patch for Orders",
        rationale="Only patch parsing could reveal whether this mentions Orders.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders rc:hasColumn ex:OrdersStatus .
                """,
            }
        ],
    )
    _corrupt_staged_patch_content(
        db,
        unanchored.patches[0].patch_iri,
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:Orders rc:hasColumn ex:OrdersStatus
        ex:Other a rc:Dataset .
        """,
    )

    listing = db.list_resource_revisions(orders)

    assert listing.patch_mention_scan.status == "incomplete"
    assert listing.patch_mention_scan.unreadable_patch_count == 2
    assert listing.patch_mention_scan.unreadable_revision_count == 2
    assert listing.patch_mention_scan.omitted_match_risk is True
    assert listing.count == 1
    item = listing.revisions[0]
    assert item.revision.iri == staged.revision_iri
    assert item.match_types == ["revision_anchor"]
    assert item.patch_mentions == []
    assert item.patch_mentions_incomplete is True
    assert item.patch_mentions_unreadable_count == 1
    with pytest.raises(DoxaBaseError) as excinfo:
        db.describe_resource_revision_lineage(orders, unanchored.revision_iri)
    message = str(excinfo.value)
    assert "was not found in resource lineage" in message
    assert "Resource patch mention scan was incomplete" in message
    assert "unreadable_patch_count=2" in message
    assert "unreadable_revision_count=2" in message
    assert "omitted_match_risk=True" in message


def test_draft_query_plan_scan_surfaces_inherited_path_lineage(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    plan = db.draft_query_plan(
        "https://richcanopy.org/example/manifest/ais#DailyIndex"
    )

    assert plan.dataset.label == "AIS Daily Vessel Index"
    assert plan.scan.uri_template == (
        "s3://ais-noaa/broadcasts/{year}/ais-{date}.parquet"
    )
    assert plan.scan.template_source == "partition_scheme"
    assert plan.scan.template_source_resource is not None
    assert plan.scan.template_source_resource.iri == (
        "https://richcanopy.org/example/manifest/ais#daily_date_partition"
    )
    assert plan.scan.template_lineage is not None
    assert "daily_date_partition" in plan.scan.template_lineage
    assert plan.scan.dataset_verification_status is not None
    assert plan.scan.dataset_verification_status.iri == RC + "UnverifiedLayout"
    assert plan.scan.dataset_verification_note is not None
    assert "inherits the broadcast partition template" in (
        plan.scan.dataset_verification_note
    )
    assert "index/{year}/ais-{date}.parquet" in plan.scan.dataset_verification_note
    assert plan.review_gate.blocking_reason_codes == ["layout_needs_verification"]
    assert plan.selected_candidate is not None
    direct_reason_text = " ".join(
        reason.message for reason in plan.selected_candidate.direct_review_reasons
    )
    assert "inherits the broadcast partition template" in direct_reason_text
    assert "index/{year}/ais-{date}.parquet" in direct_reason_text


def test_deep_lore_context_slice_finds_revision_anchor_matches(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_storage",
        label="Orders storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="directory",
        storage_root=str(tmp_path / "warehouse"),
        path_templates=["orders/*.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#orders_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    partition = db.record_map_partition_scheme(
        "https://example.test/project#orders_daily_partition",
        path_template="orders/dt={date}/*.parquet",
        granularity="rc:Daily",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    staged = db.stage_graph_revision(
        summary="Link orders physical query metadata",
        rationale=(
            "Reviewed storage, physical layout, and partition metadata for "
            "Orders query planning."
        ),
        revision_anchors=[dataset, storage.iri, layout.iri, partition.iri],
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    <{dataset}> rc:hasStorageAccess <{storage.iri}> ;
                        rc:hasPhysicalLayout <{layout.iri}> ;
                        rc:partitionedBy <{partition.iri}> .
                """,
            }
        ],
        validation_scope="all",
    )
    applied = db.apply_staged_revision(staged.revision_iri)

    context_slice = db.describe_context_slice([dataset], profile="deep_lore")

    assert not any("found no claims" in warning for warning in context_slice.warnings)
    resources = {resource.iri: resource for resource in context_slice.resources}
    assert staged.revision_iri in resources
    assert applied.applied_revision_iri in resources
    assert storage.iri in resources
    assert layout.iri in resources
    assert partition.iri in resources
    routes = {
        iri: {route.route for route in resource.routes}
        for iri, resource in resources.items()
    }
    assert "revision_anchor_match" in routes[staged.revision_iri]
    assert "revision_anchor_match" in routes[applied.applied_revision_iri]
    assert "applied_revision" in routes[applied.applied_revision_iri]
    assert "applies_staged_revision" in routes[staged.revision_iri]
    assert context_slice.route_counts["revision_anchor_match"] >= 2
    assert context_slice.route_counts["storage_access"] == 1
    assert context_slice.route_counts["physical_layout"] == 1
    assert context_slice.route_counts["partition_scheme"] == 1
    route_legend = {row.route: row for row in context_slice.route_legend}
    assert route_legend["revision_anchor_match"].meaning == (
        "A revision reached because a selected resource is one of its anchors."
    )


def test_deep_lore_context_slice_expands_revision_seeds(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#orders"
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
    )
    claim = db.record_claim_observation(
        summary="Orders need a freshness caveat.",
        claim_text="Orders include late-arriving events and need freshness caveats.",
        claim_kind="rc:CaveatClaim",
        claim_targets=[dataset],
        evidence_sources=["test://orders-freshness-profile"],
    )
    assert claim.evidence_iri is not None
    pattern = db.record_pattern(
        summary="Orders freshness should travel with handoffs.",
        pattern_text="Late-arriving orders make freshness caveats part of the durable map.",
        rationale="The caveat claim targets the dataset.",
        pattern_targets=[dataset],
        supporting_claims=[claim.claim_iri],
        evidence_iri=claim.evidence_iri,
    )
    staged = db.stage_graph_revision(
        summary="Add orders freshness caveat",
        rationale="Promote the checked freshness lore into map caveat context.",
        supporting_claims=[claim.claim_iri],
        supporting_patterns=[pattern.pattern_iri],
        revision_anchors=[dataset],
        evidence=[claim.evidence_iri],
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:orders_freshness_caveat a rc:KnownCaveat ;
                        rdfs:label "Orders freshness caveat" ;
                        rc:caveatDescription "Orders include late-arriving events." ;
                        rc:severity rc:Moderate .

                    <{dataset}> rc:hasKnownCaveat ex:orders_freshness_caveat .
                """,
            }
        ],
        validation_scope="all",
    )
    applied = db.apply_staged_revision(staged.revision_iri)

    staged_slice = db.describe_context_slice(
        [staged.revision_iri],
        profile="deep_lore",
        include_trig=True,
    )

    assert staged_slice.trig is not None
    assert not staged_slice.warnings
    staged_routes = {
        resource.iri: {route.route for route in resource.routes}
        for resource in staged_slice.resources
    }
    assert "seed_revision" in staged_routes[staged.revision_iri]
    assert "applied_revision" in staged_routes[applied.applied_revision_iri]
    assert "revision_anchor" in staged_routes[dataset]
    assert staged_slice.dataset_contexts[0].iri == dataset
    assert [context.iri for context in staged_slice.pattern_contexts] == [
        pattern.pattern_iri
    ]
    assert staged_slice.route_counts["seed_revision"] == 1
    assert staged_slice.route_counts["revision_anchor"] >= 1
    assert staged_slice.route_counts["linked_pattern"] >= 1
    assert staged_slice.route_counts["supporting_claim"] >= 1
    assert staged_slice.route_counts["revision_evidence"] >= 1
    assert staged_slice.route_counts["applied_revision"] == 1

    applied_slice = db.describe_context_slice(
        [applied.applied_revision_iri],
        profile="deep_lore",
    )

    assert not applied_slice.warnings
    applied_routes = {
        resource.iri: {route.route for route in resource.routes}
        for resource in applied_slice.resources
    }
    assert "seed_revision" in applied_routes[applied.applied_revision_iri]
    assert "applies_staged_revision" in applied_routes[staged.revision_iri]
    assert "revision_anchor" in applied_routes[dataset]
    assert applied_slice.route_counts["applies_staged_revision"] == 1
    assert applied_slice.route_counts["applied_revision"] == 1

