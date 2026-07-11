"""Split from test_doxabase_core.py (distillation Phase 2); tests verbatim."""

from tests.core.support_core import *  # noqa: F401,F403


def test_capsule_creation_seeds_base_graphs(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    overview = db.graph_overview()

    graphs = {graph.name: graph for graph in overview.named_graphs}
    assert graphs["base_ontology"].triple_count == 1530
    assert graphs["base_ontology"].mutable is False
    assert graphs["base_shapes"].triple_count == 1540
    assert graphs["base_shapes"].mutable is False
    assert graphs["map"].mutable is True
    assert graphs["patterns"].mutable is True


def test_open_readonly_inspects_existing_capsule_without_writes(
    tmp_path: Path,
) -> None:
    capsule = tmp_path / "capsule.sqlite"
    db = DoxaBase.create(capsule)
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.close()
    before_mtime = capsule.stat().st_mtime_ns

    with DoxaBase.open_readonly(capsule) as readonly:
        assert readonly.read_only is True
        overview = readonly.graph_overview()
        assert overview.key_counts["datasets"] == 1
        assert readonly.describe_dataset(dataset).iri == dataset
        assert readonly.search("Orders", graph="map").matches[0].iri == dataset

        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            readonly.record_map_dataset(
                "https://example.test/project#Customers",
                label="Customers",
                is_table=True,
            )

    assert capsule.stat().st_mtime_ns == before_mtime


def test_reopening_readonly_capsule_suggests_open_readonly(
    tmp_path: Path,
) -> None:
    capsule = tmp_path / "capsule.sqlite"
    db = DoxaBase.create(capsule)
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.close()

    os.chmod(capsule, 0o444)
    try:
        with pytest.raises(DoxaBaseError, match="DoxaBase.open_readonly"):
            DoxaBase(capsule)
        with DoxaBase.open_readonly(capsule) as readonly:
            assert readonly.describe_dataset(dataset).iri == dataset
    finally:
        os.chmod(capsule, 0o644)


def test_to_dict_serializes_api_dataclasses(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(POLYMARKET_FIXTURE)

    pattern = db.describe_pattern(
        "https://richcanopy.org/example/manifest/polymarket#"
        "pattern_price_payload_boundary"
    )
    pattern_payload = to_dict(pattern)
    assert "targets" not in pattern_payload
    assert pattern_payload["pattern_targets"][0]["iri"] == (
        "https://richcanopy.org/example/manifest/polymarket#PriceSnapshots"
    )
    assert pattern_payload["supporting_claims"][0]["claim_text"]

    entity_rows = db.list_entities(type="rc:Table", graph="map", limit=1).entities
    entity_payload = to_jsonable(entity_rows)
    assert entity_payload == [
        {
            "iri": entity_rows[0].iri,
            "label": entity_rows[0].label,
            "types": entity_rows[0].types,
            "graph": "map",
        }
    ]


def test_replace_graph_triples_can_create_same_count_digest_drift(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:Orders a rc:Dataset ;
            rdfs:label "Orders scratch table" .

        ex:Customers a rc:Dataset ;
            rdfs:label "Customers scratch table" .

        ex:OrderCustomerLink a rc:Relationship ;
            rc:sourceDataset ex:Orders .
        """,
        graph="map",
    )
    staged = db.stage_graph_revision(
        summary="Stage an Orders review comment",
        rationale="The staged patch should become stale after unrelated map drift.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Orders rdfs:comment "Staged comment." .
                """,
            }
        ],
    )

    result = db.replace_graph_triples(
        "map",
        removals="""
            @prefix ex: <https://example.test/project#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            ex:Customers rdfs:label "Customers scratch table" .
        """,
        additions="""
            @prefix ex: <https://example.test/project#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            ex:Customers rdfs:label "Customers scratch table, drifted after staging" .
        """,
        expected_count=6,
    )

    assert result.graph == "map"
    assert result.before_count == 6
    assert result.after_count == 6
    assert result.count_delta == 0
    assert result.same_count is True
    assert result.digest_changed is True
    assert result.removal_triples == 1
    assert result.addition_triples == 1
    assert result.triples_removed == 1
    assert result.triples_added == 1
    assert result.before_digest.startswith("sha256:")
    assert result.after_digest.startswith("sha256:")
    assert result.before_digest != result.after_digest

    check = db.check_staged_revision_apply(staged.revision_iri)
    assert check.status == "conflict"
    assert check.blocking_reasons == ["target_digest_drift"]
    assert check.count_drifts == []
    drift = check.snapshot_drifts[0]
    assert drift.graph_role == "map"
    assert drift.snapshot_triple_count == 6
    assert drift.current_triple_count == 6
    assert drift.snapshot_content_digest == result.before_digest
    assert drift.current_content_digest == result.after_digest
    assert [triple.object for triple in drift.triples_added_since_snapshot] == [
        "Customers scratch table, drifted after staging"
    ]
    assert [triple.object for triple in drift.triples_removed_since_snapshot] == [
        "Customers scratch table"
    ]


def test_replace_graph_triples_rejects_count_change_before_mutating(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:Orders a rc:Dataset .
        """,
        graph="map",
    )
    before_digest = db._graph_content_digest("map")

    with pytest.raises(DoxaBaseError, match="would change graph 'map' count"):
        db.replace_graph_triples(
            "map",
            additions="""
                @prefix ex: <https://example.test/project#> .
                @prefix rc: <https://richcanopy.org/ns/rc#> .

                ex:Customers a rc:Dataset .
            """,
        )

    assert db.triple_count("map") == 1
    assert db._graph_content_digest("map") == before_digest
    assert db.search("Customers", graph="map").matches == []


def test_apply_check_resolution_mentions_count_and_digest_drift(
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
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:SeedPattern rdfs:label "Seed pattern" .
        """,
        graph="patterns",
    )
    staged = db.stage_graph_revision(
        summary="Stage map and pattern additions",
        rationale="Exercise mixed count and digest drift messaging.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:CandidateDataset a rc:Dataset .
                """,
            },
            {
                "graph": "patterns",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:CandidatePattern rdfs:label "Candidate pattern" .
                """,
            },
        ],
        validation_scope="map",
    )
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:MapCountDrift a rc:Dataset .
        """,
        graph="map",
    )
    pattern_drift = db.stage_graph_revision(
        summary="Rename seed pattern without changing count",
        rationale="Exercise digest drift on a second changed graph.",
        additions=[
            {
                "graph": "patterns",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:SeedPattern rdfs:label "Seed pattern renamed" .
                """,
            }
        ],
        removals=[
            {
                "graph": "patterns",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:SeedPattern rdfs:label "Seed pattern" .
                """,
            }
        ],
        validation_scope="map",
    )
    db.apply_staged_revision(pattern_drift.revision_iri, validation_scope="map")

    check = db.check_staged_revision_apply(
        staged.revision_iri,
        validation_scope="map",
    )

    assert check.status == "conflict"
    assert check.blocking_reasons == ["target_count_drift", "target_digest_drift"]
    assert len(check.count_drifts) == 1
    assert {drift.graph_role for drift in check.snapshot_drifts} == {
        "map",
        "patterns",
    }
    assert all(
        drift.exact_changed_triples_available for drift in check.snapshot_drifts
    )
    assert check.recommended_resolution == (
        "Restage the proposal against the current graph state; at least one "
        "target graph count and at least one target graph content digest changed "
        "since staging."
    )


def test_stale_row_semantics_add_suggests_same_slot_replacement(
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

    check = db.check_staged_revision_apply(source.revision_iri)

    assert check.status == "conflict"
    assert check.decision == "restage_against_current_graph"
    assert check.routing_decision == "stage_same_slot_replacement"
    assert check.recommended_resolution is not None
    assert "stage_revision map_assertion replacement" in (
        check.recommended_resolution
    )
    assert "mechanically restaging" in check.recommended_resolution
    assert check.next_action is not None
    assert check.next_action.action_type == "repair_or_replace"
    assert check.next_action.queue == "repair_or_replace"
    assert check.next_action.tool_name == "stage_revision"
    assert check.next_action.arguments.get("kind") == "map_assertion"
    action_tools = [action.tool.removeprefix("doxabase.") for action in check.suggested_next_actions]
    assert "stage_revision" in action_tools
    assert "restage_staged_revision" not in action_tools
    action = next(
        action
        for action in check.suggested_next_actions
        if (action.tool, action.args.get("kind")) == ("doxabase.stage_revision", "map_assertion")
    )
    assert action.args["spec"]["subject"] == orders
    assert action.args["spec"]["predicate"] == RC + "rowSemantics"
    assert action.args["spec"]["object"] == RC + "SnapshotRow"
    assert action.args["spec"]["object_kind"] == "iri"
    assert action.args["spec"]["change_kind"] == "replace"
    assert action.args["spec"]["graph"] == "map"
    assert action.args["spec"]["restages_revision"] == source.revision_iri
    assert action.args["spec"]["validation_scope"] == "all"
    draft = db.draft_staged_revision_rebase(source.revision_iri)
    assert draft.result_kind == "staged_revision_rebase_draft"
    assert draft.mode == "non_executed_review_draft"
    assert draft.source_revision_iri == source.revision_iri
    assert draft.current_revision_iri == source.revision_iri
    assert draft.draft_status == "drafted"
    assert draft.draft_kind == "same_slot_replacement"
    assert draft.reason_codes == ["same_slot_replacement"]
    assert draft.apply_check.routing_decision == "stage_same_slot_replacement"
    assert draft.preferred_action is not None
    assert draft.preferred_action.args == action.args
    assert draft.next_action is not None
    assert draft.next_action.queue == "repair_or_replace"
    assert draft.next_action.tool_name == "stage_revision"
    assert draft.next_action.arguments.get("kind") == "map_assertion"
    assert [
        (action.tool.removeprefix("doxabase."), action.args.get("kind"))
        for action in draft.suggested_next_actions
    ] == [
        ("stage_revision", "map_assertion"),
        ("describe_revision", None),
        ("export_bundle", "staged_revisions"),
    ]
    assert draft.next_action_queue_item is not None
    assert draft.next_action_queue_item.row_iri == source.revision_iri
    assert draft.next_action_queue_item.row_is_target is False
    assert draft.repair_candidates[0].current_same_subject_predicate_triples[0].object == (
        RC + "EventRow"
    )
    assert draft.repair_candidates[0].proposed_triples[0].object == (
        RC + "SnapshotRow"
    )
    described = db.describe_staged_revision(
        source.revision_iri,
        include_current_apply_check=True,
    )
    assert described.current_apply_check is not None
    assert described.current_apply_check.decision == "restage_against_current_graph"
    assert described.current_apply_check.routing_decision == (
        "stage_same_slot_replacement"
    )

    with pytest.raises(DoxaBaseError, match="same-slot replacement conflict"):
        db.restage_staged_revision(source.revision_iri)

    repair = db.stage_map_assertion_change(**action.args["spec"])
    assert repair.staged_revision.restaged_from == source.revision_iri
    assert [value.object for value in repair.current_values_before] == [
        RC + "EventRow"
    ]
    repair_check = db.check_staged_revision_apply(
        repair.staged_revision.revision_iri
    )
    assert repair_check.status == "ready"


def test_same_slot_replacement_preserves_applied_alternative_gate(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    applied_source = db.stage_graph_revision(
        summary="Model Orders as event rows",
        rationale="One row-grain framing under review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders rc:rowSemantics rc:EventRow .
                """,
            }
        ],
        revision_anchors=[orders],
    )
    stale_alternative = db.stage_graph_revision(
        summary="Model Orders as snapshot rows",
        rationale="Competing row-grain framing under review.",
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
        alternative_to=applied_source.revision_iri,
    )
    applied = db.apply_staged_revision(applied_source.revision_iri)

    check = db.check_staged_revision_apply(stale_alternative.revision_iri)

    assert check.status == "conflict"
    assert check.routing_decision == "stage_same_slot_replacement"
    assert check.alternative_gate.status == "alternative_to_applied_source"
    action = next(
        action
        for action in check.suggested_next_actions
        if (action.tool, action.args.get("kind")) == ("doxabase.stage_revision", "map_assertion")
    )
    assert action.args["spec"]["restages_revision"] == stale_alternative.revision_iri
    assert action.args["spec"]["alternative_to"] == applied_source.revision_iri

    repair_arguments = dict(action.args["spec"])
    assert repair_arguments.pop("alternative_to") == applied_source.revision_iri
    repair = db.stage_map_assertion_change(**repair_arguments)
    assert repair.staged_revision.restaged_from == stale_alternative.revision_iri
    assert repair.staged_revision.alternative_to == applied_source.revision_iri
    repair_check = db.check_staged_revision_apply(
        repair.staged_revision.revision_iri
    )
    assert repair_check.status == "ready"
    assert repair_check.alternative_gate.status == "alternative_to_applied_source"
    assert repair_check.alternative_gate.semantic_review_required is True
    assert repair_check.alternative_gate.applied_source_iri == (
        applied_source.revision_iri
    )
    assert repair_check.next_action is not None
    assert repair_check.next_action.action_label == (
        "Apply only after semantic review"
    )

    repair_iri = repair.staged_revision.revision_iri
    graph_versions = db.list_graph_versions(
        "map",
        exact_only=True,
        record_kind="staged_patch",
    )
    repair_version = next(
        item for item in graph_versions.versions if item.revision_iri == repair_iri
    )
    assert repair_version.alternative_gate_status == (
        "alternative_to_applied_source"
    )
    assert repair_version.alternative_semantic_review_required is True
    assert repair_version.alternative_applied_source_iri == (
        applied_source.revision_iri
    )
    assert repair_version.alternative_applied_revision_iri == (
        applied.applied_revision_iri
    )

    version_diff = db.describe_graph_version_diff("map", repair_iri)
    assert version_diff.count_delta == 0
    assert version_diff.digest_changed is False
    assert version_diff.before_revision_context is not None
    assert version_diff.before_revision_context.application_status == "ready"
    assert version_diff.before_revision_context.alternative_gate_status == (
        "alternative_to_applied_source"
    )
    assert (
        version_diff.before_revision_context.alternative_semantic_review_required
        is True
    )
    assert version_diff.before_revision_context.alternative_applied_source_iri == (
        applied_source.revision_iri
    )
    assert version_diff.before_revision_context.alternative_applied_revision_iri == (
        applied.applied_revision_iri
    )


def test_stale_authored_replacement_with_target_already_current_routes_to_inspection(
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
        rationale="Original replacement before another route made it current.",
    )
    db.record_map_dataset(orders, row_semantics="rc:SnapshotRow")

    check = db.check_staged_revision_apply(source.staged_revision.revision_iri)

    assert check.status == "conflict"
    assert check.decision == "restage_against_current_graph"
    assert check.routing_decision == "inspect_no_effective_change"
    assert check.summary.startswith("Already-effective stale source")
    assert check.effective_delta_summary.replayable_triples_to_add == 0
    assert check.effective_delta_summary.replayable_triples_to_remove == 0
    assert check.effective_delta_summary.blocked_patch_triples_to_add == 0
    assert check.effective_delta_summary.blocked_patch_triples_to_remove == 0
    assert check.effective_delta_summary.total_effective_triples_to_add == 0
    assert check.effective_delta_summary.total_effective_triples_to_remove == 0
    assert check.effective_delta_summary.already_effective is True
    assert check.effective_delta_summary.has_conflicted_patches is True
    assert check.effective_delta_summary.patch_triple_status_counts == {
        "all_patch_triples_absent": 1,
        "all_patch_triples_present": 1,
    }
    assert check.effective_delta_summary.basis == "conflicted_patches_excluded"
    assert check.already_applied_by is None
    assert check.next_action is not None
    assert check.next_action.action_type == "inspect_no_effective_change"
    assert check.next_action.queue == "informational"
    assert check.next_action.tool_name == "describe_revision"
    assert not any(
        (action.tool, action.args.get("kind")) == ("doxabase.stage_revision", "map_assertion")
        for action in check.suggested_next_actions
    )
    assert not any(
        action.tool == "doxabase.restage_staged_revision"
        for action in check.suggested_next_actions
    )
    by_operation = {patch.operation: patch for patch in check.patch_checks}
    addition_patch = by_operation[db.expand_iri("rc:AdditionPatch")]
    removal_patch = by_operation[db.expand_iri("rc:RemovalPatch")]
    assert addition_patch.already_present_triples == 1
    assert addition_patch.effective_triples_to_add == 0
    assert removal_patch.already_absent_triples == 1
    assert removal_patch.effective_triples_to_remove == 0

    dry_run = db.restage_staged_revisions(
        [source.staged_revision.revision_iri],
        dry_run=True,
    )
    assert dry_run.not_restageable_revision_iris_by_reason == {
        "already_effective": [source.staged_revision.revision_iri]
    }
    dry_item = dry_run.items[0]
    assert dry_item.decision_before == "restage_against_current_graph"
    assert dry_item.routing_decision_before == "inspect_no_effective_change"
    assert dry_item.decision_after == "restage_against_current_graph"
    assert dry_item.routing_decision_after == "inspect_no_effective_change"
    assert dry_run.bundle_summary.next_action_queue == {
        "informational": [source.staged_revision.revision_iri]
    }
    assert dry_run.bundle_summary.recommended_mutation_review_iris == []


def test_schema_stability_same_slot_drift_suggests_replacement(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    source = db.stage_graph_revision(
        summary="Model Orders as fixed schema",
        rationale="Original schema-stability proposal before an intervening edit.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders rc:schemaStability rc:FixedSchema .
                """,
            }
        ],
        revision_anchors=[orders],
    )
    db.record_map_dataset(orders, schema_stability="rc:VariableSchema")

    check = db.check_staged_revision_apply(source.revision_iri)

    assert check.status == "conflict"
    assert check.next_action is not None
    assert check.next_action.queue == "repair_or_replace"
    action = next(
        action
        for action in check.suggested_next_actions
        if (action.tool, action.args.get("kind")) == ("doxabase.stage_revision", "map_assertion")
    )
    assert action.args["spec"]["subject"] == orders
    assert action.args["spec"]["predicate"] == RC + "schemaStability"
    assert action.args["spec"]["object"] == RC + "FixedSchema"
    assert action.args["spec"]["object_kind"] == "iri"
    assert "schema stability" in action.reason

    dry_run = db.restage_staged_revisions([source.revision_iri], dry_run=True)
    assert dry_run.not_restageable_revision_iris_by_reason == {
        "same_slot_replacement": [source.revision_iri]
    }


def test_stale_removal_with_target_already_absent_routes_to_inspection(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    source = db.stage_map_assertion_change(
        subject=orders,
        predicate="rdfs:label",
        object="Orders",
        object_kind="literal",
        change_kind="remove",
        rationale="Remove redundant label after review.",
    )
    db.replace_graph_triples(
        "map",
        removals="""
            @prefix ex: <https://example.test/project#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            ex:Orders rdfs:label "Orders" .
        """,
        allow_count_change=True,
    )

    check = db.check_staged_revision_apply(source.staged_revision.revision_iri)

    assert check.status == "conflict"
    assert check.decision == "restage_against_current_graph"
    assert check.next_action is not None
    assert check.next_action.action_type == "inspect_no_effective_change"
    assert check.next_action.queue == "informational"
    assert not any(
        action.tool == "doxabase.restage_staged_revision"
        for action in check.suggested_next_actions
    )
    patch_check = check.patch_checks[0]
    assert patch_check.already_present_triples == 0
    assert patch_check.already_absent_triples == 1
    assert patch_check.effective_triples_to_remove == 0

    dry_run = db.restage_staged_revisions(
        [source.staged_revision.revision_iri],
        dry_run=True,
    )
    assert dry_run.not_restageable_revision_iris_by_reason == {
        "already_effective": [source.staged_revision.revision_iri]
    }
    with pytest.raises(DoxaBaseError, match="already-effective stale source"):
        db.restage_staged_revision(source.staged_revision.revision_iri)


def test_apply_check_reports_validation_failed_status(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = db.stage_graph_revision(
        summary="Stage invalid value type",
        rationale="Exercise apply-check status for a clean patch with SHACL errors.",
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

    check = db.check_staged_revision_apply(staged.revision_iri)
    assert check.can_apply is False
    assert check.status == "validation_failed"
    assert check.decision == "inspect_validation_results"
    assert check.review_recommended is False
    assert check.blocking_reasons == ["validation_failed"]
    assert check.recommended_resolution is not None
    assert "validation_results" in check.recommended_resolution
    assert check.conflicts == []
    assert check.validation_conforms is False
    assert check.validation_skipped_reason is None
    assert check.validation_results
    assert check.summary == (
        "Patch counts replay cleanly, but preview validation failed with "
        f"{check.validation_result_count} result(s)."
    )
    assert check.next_action is not None
    assert check.next_action.queue == "repair_or_replace"
    assert check.next_action.tool_name == "restage_staged_revision"
    assert check.next_action.arguments.get("dry_run") is True
    assert [action.tool.removeprefix("doxabase.") for action in check.suggested_next_actions] == [
        "restage_staged_revision",
        "describe_revision",
        "export_bundle",
    ]
    assert check.suggested_next_actions[0].args.get("dry_run") is True
    assert "read-only repair/rebase plan" in check.suggested_next_actions[0].reason
    assert "stage a repaired" in check.suggested_next_actions[1].reason
    assert "validation-failed" in (
        check.suggested_next_actions[2].args["spec"]["path"]
    )
    description = db.describe_staged_revision(
        staged.revision_iri,
        include_current_apply_check=True,
    )
    assert description.current_apply_check is not None
    validation_summary = description.current_apply_check
    assert validation_summary.status == "validation_failed"
    assert validation_summary.decision == "inspect_validation_results"
    assert validation_summary.validation_conforms is False
    assert validation_summary.validation_result_count == check.validation_result_count
    assert validation_summary.next_action is not None
    assert validation_summary.next_action.action_type == "repair_or_replace"
    assert validation_summary.next_action.queue == "repair_or_replace"
    assert validation_summary.next_action.arguments == {
        "revision_iris": staged.revision_iri,
        "dry_run": True,
        "validation_scope": "all",
    }
    assert validation_summary.suggested_next_actions[0].tool == (
        "doxabase.restage_staged_revision"
    )
    assert validation_summary.suggested_next_actions[0].args.get(
        "dry_run"
    ) is True
    assert validation_summary.error is None

    export = db.export_staged_revisions(
        [staged.revision_iri],
        tmp_path / "validation-failed-review.md",
    )
    assert export.bundle_summary.validation_failed_revision_iris == [
        staged.revision_iri
    ]
    assert export.bundle_summary.staged_validation_failed_revision_iris == [
        staged.revision_iri
    ]
    assert export.bundle_summary.post_apply_recheck_revision_iris == []
    assert export.bundle_summary.recommended_mutation_review_iris == [
        staged.revision_iri
    ]
    assert export.bundle_summary.recommended_apply_or_restage_review_iris == []
    assert export.bundle_summary.recommended_repair_review_iris == [
        staged.revision_iri
    ]
    assert export.bundle_summary.recommended_applied_inspection_iris == []
    assert export.revision_summaries[0].apply_recommended_resolution is not None
    assert (
        export.revision_summaries[0].apply_recommendation_scope
        == "current_apply_check"
    )
    assert "validation_results" in (
        export.revision_summaries[0].apply_recommended_resolution
    )
    assert export.revision_summaries[0].summary_recommendation == (
        export.revision_summaries[0].apply_recommended_resolution
    )
    assert (
        export.revision_summaries[0].summary_recommendation_source
        == "apply_recommended_resolution"
    )
    exported = (tmp_path / "validation-failed-review.md").read_text(
        encoding="utf-8"
    )
    assert "Inspect validation_results" in exported

    with pytest.raises(
        DoxaBaseError,
        match="Applying staged revision would fail",
    ) as excinfo:
        db.apply_staged_revision(staged.revision_iri)
    error = str(excinfo.value)
    assert staged.revision_iri in error
    assert "describe_revision(" in error
    assert "include_current_apply_check=True" in error


def test_external_intentionally_unrecorded_credential_reference_is_non_secret_marker(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_s3_storage",
        label="Orders S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        location_kind="prefix",
        bucket_name="orders",
        key_prefix="current",
        path_templates=["dt={date}.parquet"],
        credential_reference="external:intentionally-unrecorded",
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

    context = db.describe_query_context(dataset)
    assert context.storage_accesses[0].credential_reference == (
        "external:intentionally-unrecorded"
    )
    assert "s3_access_resolution_unrecorded" not in {
        issue.code for issue in context.issues
    }
    plan = db.draft_query_plan(dataset)
    assert plan.storage_environment.credential_reference == (
        "external:intentionally-unrecorded"
    )
    scan = db.scan_sensitive_literals(graphs=["map"])
    assert scan.match_count == 0
    preflight = db.export_preflight(export_kind="graph", graphs=["map"])
    assert preflight.scanner_clean is True


def test_non_tabular_file_formats_have_core_labels(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/non-tabular-formats#"
    assets = {
        "raw_images": ("Raw image tiles", "rc:JPEG", "JPEG"),
        "mask_tiles": ("Mask tiles", "rc:PNG", "PNG"),
        "orthomosaic": ("Orthomosaic", "rc:GeoTIFF", "GeoTIFF"),
        "scan_pages": ("Scanned pages", "rc:TIFF", "TIFF"),
        "report": ("Review report", "rc:PDF", "PDF"),
    }

    for local_name, (label, file_format, expected_label) in assets.items():
        dataset = f"{base}{local_name}"
        db.record_map_dataset(dataset, label=label, is_table=False)
        db.record_map_physical_layout(
            f"{base}{local_name}_layout",
            label=f"{label} layout",
            file_format=file_format,
            layout_verification_status="rc:GeneratedFromManifestLayout",
            datasets=[dataset],
        )

        description = db.describe_dataset(dataset)
        assert RC + "Dataset" in description.types
        assert RC + "Table" not in description.types
        assert description.physical_layouts[0].file_format is not None
        assert description.physical_layouts[0].file_format.iri == (
            db.expand_iri(file_format)
        )
        assert description.physical_layouts[0].file_format.label == expected_label

    assert db.validate_graph(scope="all").conforms


@pytest.mark.parametrize(
    ("call", "match"),
    [
        pytest.param(
            lambda db: db.record_map_dataset(
                "https://example.test/project#messages",
                label="Messages",
                row_semantics="rc:PingRow",
            ),
            "row_semantics must be one of: .*rc:DimensionRow",
            id="dataset-row-semantics",
        ),
        pytest.param(
            lambda db: db.record_map_dataset(
                "https://example.test/project#messages",
                label="Messages",
                schema_stability="rc:EvolvingSchema",
            ),
            "schema_stability must be one of: .*rc:VariableSchema",
            id="dataset-schema-stability",
        ),
        pytest.param(
            lambda db: db.record_map_dataset(
                "https://example.test/project#messages",
                label="Messages",
                layout_verification_status="rc:VerifiedLayout",
            ),
            "layout_verification_status must be one of: .*rc:ContradictedLayout",
            id="dataset-layout-status",
        ),
        pytest.param(
            lambda db: db.record_map_storage_access(
                "https://example.test/project#local_access",
                layout_verification_status="rc:VerifiedLayout",
            ),
            "layout_verification_status must be one of: .*rc:ContradictedLayout",
            id="storage-layout-status",
        ),
        pytest.param(
            lambda db: db.record_map_physical_layout(
                "https://example.test/project#messages_layout",
                layout_verification_status="rc:VerifiedLayout",
            ),
            "layout_verification_status must be one of: .*rc:ContradictedLayout",
            id="physical-layout-status",
        ),
        pytest.param(
            lambda db: db.record_map_partition_scheme(
                "https://example.test/project#messages_partitioning",
                granularity="rc:FiscalQuarter",
            ),
            "granularity must be one of: .*rc:ByValue",
            id="partition-granularity",
        ),
        pytest.param(
            lambda db: db.record_map_partition_scheme(
                "https://example.test/project#messages_partitioning",
                layout_verification_status="rc:VerifiedLayout",
            ),
            "layout_verification_status must be one of: .*rc:ContradictedLayout",
            id="partition-layout-status",
        ),
        pytest.param(
            lambda db: db.record_map_caveat(
                "https://example.test/project#body_caveat",
                description="Body text is cleaned text, not raw source text.",
                severity="rc:High",
            ),
            "severity must be one of: .*rc:Minor.*rc:Moderate.*rc:Severe",
            id="caveat-severity",
        ),
    ],
)
def test_map_helpers_reject_unknown_controlled_values_before_write(
    tmp_path: Path,
    call: Callable[[DoxaBase], object],
    match: str,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_map_count = db.triple_count("map")

    with pytest.raises(DoxaBaseError, match=match):
        call(db)

    assert db.triple_count("map") == before_map_count


def test_map_helper_plain_name_error_suggests_curie(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError) as excinfo:
        db.record_map_caveat(
            "https://example.test/project#body_caveat",
            description="Body text is cleaned text, not raw source text.",
            severity="warning",
        )

    message = str(excinfo.value)
    assert "severity values must be IRIs or CURIEs" in message
    assert "not plain names: 'warning'" in message
    assert "rc:Moderate" in message


def test_graph_overview_counts_imported_fixtures(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    db.import_trig(POLYMARKET_FIXTURE)

    overview = db.graph_overview()

    assert overview.key_counts["tables"] >= 7
    assert overview.key_counts["columns"] >= 40
    assert overview.key_counts["storage_accesses"] == 2
    assert any(
        predicate == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
        for predicate, _ in overview.predicate_counts
    )


def test_validate_graph_uses_base_and_project_shapes(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    db.import_trig(POLYMARKET_FIXTURE)

    result = db.validate_graph(scope="all")

    assert result.conforms, result.report_text
    assert result.result_count == 0


def test_validate_graph_wraps_malformed_project_shapes(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .

        ex:BadDatasetShape a sh:NodeShape ;
            sh:targetClass rc:Dataset ;
            sh:property [
                sh:path rc:label, rc:summary ;
                sh:minCount 1
            ] .
        """,
        graph="shapes",
    )

    with pytest.raises(DoxaBaseError) as exc_info:
        db.validate_graph(scope="all")

    message = str(exc_info.value)
    assert "Could not run SHACL validation for scope 'all'" in message
    assert "ShapeLoadError" in message or "ConstraintLoadError" in message

