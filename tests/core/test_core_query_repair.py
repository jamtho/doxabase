"""Split from test_doxabase_core.py (distillation Phase 2); tests verbatim."""

from tests.core.support_core import *  # noqa: F401,F403


def test_multipatch_same_slot_subpatch_routes_to_patch_repair_plan(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    source = db.stage_graph_revision(
        summary="Stage mixed Orders modelling update",
        rationale=(
            "A larger modelling update includes row grain, an already-realized "
            "column link, and an independent table addition."
        ),
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders rc:rowSemantics rc:SnapshotRow .
                """,
            },
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders rc:hasColumn ex:orders__ship_date .
                """,
            },
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:FulfillmentEvents a rc:Table ;
                        rdfs:label "Fulfillment events" .
                """,
            },
        ],
        revision_anchors=[orders],
    )
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:Orders rc:rowSemantics rc:EventRow ;
            rc:hasColumn ex:orders__ship_date .
        """,
        graph="map",
    )

    check = db.check_staged_revision_apply(source.revision_iri)

    assert check.status == "conflict"
    assert check.decision == "restage_against_current_graph"
    assert check.routing_decision == "repair_or_replace"
    assert check.next_action is not None
    assert check.next_action.tool_name == "draft_staged_revision_rebase"
    assert check.next_action.action_label == "Draft patch repair plan"
    assert check.recommended_resolution is not None
    assert "patch_repair_plan" in check.recommended_resolution
    assert not any(
        action.tool == "doxabase.restage_staged_revision"
        for action in check.suggested_next_actions
    )

    plan_by_sequence = {
        item.patch_sequence_index: item for item in check.patch_repair_plan
    }
    assert sorted(plan_by_sequence) == [1, 2, 3]
    same_slot_plan = plan_by_sequence[1]
    assert same_slot_plan.effect_class == "same_slot_replace"
    assert same_slot_plan.recommended_action_kind == "stage_map_assertion_change"
    assert same_slot_plan.action is not None
    assert same_slot_plan.action.tool == "doxabase.stage_map_assertion_change"
    assert same_slot_plan.action.args["subject"] == orders
    assert same_slot_plan.action.args["predicate"] == RC + "rowSemantics"
    assert same_slot_plan.action.args["object"] == RC + "SnapshotRow"
    assert same_slot_plan.action.args["restages_revision"] == source.revision_iri
    assert same_slot_plan.current_same_subject_predicate_triples[0].object == (
        RC + "EventRow"
    )
    assert same_slot_plan.proposed_triples[0].object == RC + "SnapshotRow"
    assert (
        plan_by_sequence[2].effect_class
        == "already_effective_drop_or_inspect"
    )
    assert plan_by_sequence[3].effect_class == "blocked_keep_or_repair"

    draft = db.draft_staged_revision_rebase(source.revision_iri)
    assert draft.draft_status == "not_drafted"
    assert draft.draft_kind == "patch_repair_plan"
    assert draft.reason_codes[0] == "patch_repair_plan"
    assert "target_count_drift" in draft.reason_codes
    assert draft.apply_check.patch_repair_plan[0].effect_class == (
        "same_slot_replace"
    )

    dry_run = db.restage_staged_revisions([source.revision_iri], dry_run=True)
    assert dry_run.would_restage_revision_iris == []
    assert dry_run.skipped_revision_iris == [source.revision_iri]
    assert dry_run.not_restageable_revision_iris_by_reason == {
        "patch_repair_plan": [source.revision_iri]
    }
    assert dry_run.items[0].next_action_after is not None
    assert dry_run.items[0].next_action_after.tool_name == (
        "draft_staged_revision_rebase"
    )

    with pytest.raises(DoxaBaseError, match="patch repair-plan conflict"):
        db.restage_staged_revision(source.revision_iri)


def test_stale_row_semantics_with_multiple_current_values_does_not_draft_repair(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    source = db.stage_graph_revision(
        summary="Model Orders as snapshot rows",
        rationale="Original row-grain proposal before an ambiguous map edit.",
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
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:Orders rc:rowSemantics rc:EventRow, rc:AggregateRow .
        """,
        graph="map",
    )

    check = db.check_staged_revision_apply(source.revision_iri)

    assert check.status == "conflict"
    assert check.routing_decision == "repair_or_replace"
    assert check.next_action is not None
    assert check.next_action.queue == "repair_or_replace"
    assert check.next_action.action_label == "Review ambiguous same-slot conflict"
    assert check.next_action.tool_name == "describe_resource"
    assert check.next_action.arguments["aspect"] == "assertion_support"
    assert check.next_action.arguments["iri"] == orders
    assert check.next_action.arguments["predicate"] == RC + "rowSemantics"
    assert check.next_action.arguments["object"] == RC + "SnapshotRow"
    assert check.next_action.arguments["object_kind"] == "iri"
    assert check.recommended_resolution is not None
    assert "multiple values" in check.recommended_resolution
    assert not any(
        action.tool == "doxabase.stage_map_assertion_change"
        for action in check.suggested_next_actions
    )
    assert not any(
        action.tool == "doxabase.restage_staged_revision"
        for action in check.suggested_next_actions
    )
    draft = db.draft_staged_revision_rebase(source.revision_iri)
    assert draft.draft_status == "not_drafted"
    assert draft.draft_kind == "ambiguous_same_slot"
    assert draft.reason_codes[0] == "ambiguous_same_slot"
    assert "target_count_drift" in draft.reason_codes
    assert draft.next_action is not None
    assert draft.next_action.action_label == "Review ambiguous same-slot conflict"
    assert draft.repair_actions == []
    assert draft.repair_candidates == []

    dry_run = db.restage_staged_revisions([source.revision_iri], dry_run=True)
    assert dry_run.would_restage_revision_iris == []
    assert dry_run.not_restageable_revision_iris_by_reason == {
        "ambiguous_same_slot": [source.revision_iri],
    }
    dry_item = dry_run.items[0]
    assert dry_item.action == "skipped_not_restageable"
    assert dry_item.not_restageable_reason == "ambiguous_same_slot"
    assert dry_item.next_action_after is not None
    assert dry_item.next_action_after.tool_name == "describe_resource"
    assert dry_item.next_action_after.arguments["aspect"] == "assertion_support"

    plan = db.plan_staged_revision_recovery([source.revision_iri])
    assert plan.lane_counts == {"repair_or_replace": 1}
    assert plan.not_restageable_revision_iris_by_reason == {
        "ambiguous_same_slot": [source.revision_iri],
    }
    assert plan.mutation_frontier_items == []
    assert plan.mutation_allowed_after == "repair_inspection_required_before_mutation"
    lane = plan.lanes[0]
    assert lane.not_restageable_reason == "ambiguous_same_slot"
    assert lane.next_action is not None
    assert lane.next_action.tool_name == "describe_resource"
    assert lane.next_action.arguments["aspect"] == "assertion_support"
    assert lane.repair_draft is not None
    assert lane.repair_draft.draft_kind == "ambiguous_same_slot"

    with pytest.raises(DoxaBaseError, match="ambiguous same-slot conflict"):
        db.restage_staged_revision(source.revision_iri)


def test_stale_authored_replacement_suggests_same_slot_repair(
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
        rationale="Original replacement before another map edit.",
    )
    db.record_map_dataset(orders, row_semantics="rc:AggregateRow")

    check = db.check_staged_revision_apply(source.staged_revision.revision_iri)

    assert check.status == "conflict"
    assert check.decision == "restage_against_current_graph"
    assert check.routing_decision == "stage_same_slot_replacement"
    assert check.next_action is not None
    assert check.next_action.queue == "repair_or_replace"
    assert check.next_action.tool_name == "stage_map_assertion_change"
    action = next(
        action
        for action in check.suggested_next_actions
        if action.tool == "doxabase.stage_map_assertion_change"
    )
    assert action.args["subject"] == orders
    assert action.args["predicate"] == RC + "rowSemantics"
    assert action.args["object"] == RC + "SnapshotRow"
    assert action.args["change_kind"] == "replace"
    assert action.args["restages_revision"] == (
        source.staged_revision.revision_iri
    )

    batch = db.restage_staged_revisions(
        [source.staged_revision.revision_iri],
        dry_run=True,
    )
    assert batch.not_restageable_revision_iris_by_reason == {
        "same_slot_replacement": [source.staged_revision.revision_iri]
    }
    repair = db.stage_map_assertion_change(**action.args)
    assert db.check_staged_revision_apply(
        repair.staged_revision.revision_iri
    ).status == "ready"


def test_polymarket_outcome_alignment_failure_and_repair_uses_diagnostics(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(POLYMARKET_FIXTURE)
    before_map_count = db.triple_count("map")
    before_ontology_count = db.triple_count("ontology")
    before_shapes_count = db.triple_count("shapes")
    ft = "https://richcanopy.org/example/field-trial/polymarket-diagnostics#"

    claim = db.record_claim_observation(
        summary="Outcome/token alignment is an embedded array bridge.",
        claim_text=(
            "Gamma market snapshots carry outcomes and clobTokenIds as JSON-array "
            "columns, while downstream CLOB tables use scalar token identifiers."
        ),
        claim_kind="rc:SchemaClaim",
        claim_targets=[
            "https://richcanopy.org/example/manifest/polymarket#MarketSnapshots",
            "https://richcanopy.org/example/manifest/polymarket#mkt_outcomes",
            "https://richcanopy.org/example/manifest/polymarket#mkt_clob_token_ids",
            "https://richcanopy.org/example/manifest/polymarket#same_entity_clob_token",
        ],
        confidence="rc:HighConfidence",
        observation_status="rc:Checked",
        evidence_summary=(
            "Fixture map records outcomes and clobTokenIds as JSON-array columns, "
            "and scalar token identity as a separate SharedIdentifier."
        ),
        source_path="examples/manifest-prototype-rc/polymarket.trig",
        start_line=163,
        end_line=494,
        source_kind="rc:DocumentationSource",
    )
    pattern = db.record_pattern(
        summary="Outcome/token alignment is a positional array bridge.",
        pattern_text=(
            "Polymarket market identity flows through conditionId plus parallel "
            "outcomes and clobTokenIds arrays before downstream tables expose "
            "scalar CLOB token ids."
        ),
        rationale=(
            "The existing fixture captures scalar token identity, but the "
            "market-side bridge is hidden inside array order rather than a "
            "plain column-to-column foreign key."
        ),
        pattern_targets=[
            "https://richcanopy.org/example/manifest/polymarket#mkt_outcomes",
            "https://richcanopy.org/example/manifest/polymarket#mkt_clob_token_ids",
            "https://richcanopy.org/example/manifest/polymarket#same_entity_clob_token",
        ],
        supporting_claims=[claim.claim_iri],
        map_implications=[
            f"{ft}outcome_token_alignment_v1",
            f"{ft}outcome_slot_latent_entity",
        ],
    )

    shared_ontology = f"""
    @prefix ft: <{ft}> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ft:OutcomeTokenAlignment a rdfs:Class ;
        rdfs:label "Outcome token alignment" .

    ft:OutcomeTokenAlignmentPattern a rdfs:Class ;
        rdfs:subClassOf rc:Pattern ;
        rdfs:label "Outcome token alignment pattern" .

    ft:OutcomeSlot a rdfs:Class ;
        rdfs:label "Outcome slot" .

    ft:alignmentMarketTable a rdf:Property ;
        rdfs:range rc:Table ;
        rdfs:label "alignment market table" .

    ft:conditionIdColumn a rdf:Property ;
        rdfs:range rc:Column ;
        rdfs:label "condition id column" .

    ft:outcomeLabelArrayColumn a rdf:Property ;
        rdfs:range rc:Column ;
        rdfs:label "outcome label array column" .

    ft:clobTokenIdArrayColumn a rdf:Property ;
        rdfs:range rc:Column ;
        rdfs:label "CLOB token id array column" .

    ft:downstreamTokenColumn a rdf:Property ;
        rdfs:range rc:Column ;
        rdfs:label "downstream token column" .

    ft:alignmentBasis a rdf:Property ;
        rdfs:label "alignment basis" .

    ft:requiresJsonArrayParsing a rdf:Property ;
        rdfs:label "requires JSON array parsing" .

    ft:impliedLatentEntity a rdf:Property ;
        rdfs:label "implied latent entity" .

    ft:keepsArrayOrderUnresolved a rdf:Property ;
        rdfs:label "keeps array order unresolved" .
    """
    shared_shapes = f"""
    @prefix ft: <{ft}> .
    @prefix sh: <http://www.w3.org/ns/shacl#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    ft:OutcomeTokenAlignmentShape a sh:NodeShape ;
        sh:targetClass ft:OutcomeTokenAlignment ;
        sh:property [
            sh:path ft:alignmentMarketTable ;
            sh:minCount 1 ;
            sh:maxCount 1 ;
            sh:nodeKind sh:IRI ;
            sh:message "Outcome token alignments must name the market snapshot table."
        ] ;
        sh:property [
            sh:path ft:conditionIdColumn ;
            sh:minCount 1 ;
            sh:maxCount 1 ;
            sh:nodeKind sh:IRI ;
            sh:message "Outcome token alignments must name the conditionId column."
        ] ;
        sh:property [
            sh:path ft:outcomeLabelArrayColumn ;
            sh:minCount 1 ;
            sh:maxCount 1 ;
            sh:nodeKind sh:IRI ;
            sh:message "Outcome token alignments must name the outcome-label array column."
        ] ;
        sh:property [
            sh:path ft:clobTokenIdArrayColumn ;
            sh:minCount 1 ;
            sh:maxCount 1 ;
            sh:nodeKind sh:IRI ;
            sh:message "Outcome token alignments must name the CLOB token-id array column."
        ] ;
        sh:property [
            sh:path ft:downstreamTokenColumn ;
            sh:minCount 1 ;
            sh:nodeKind sh:IRI ;
            sh:message "Outcome token alignments need a downstream scalar CLOB token column."
        ] ;
        sh:property [
            sh:path ft:alignmentBasis ;
            sh:minCount 1 ;
            sh:maxCount 1 ;
            sh:datatype xsd:string ;
            sh:message "Outcome token alignments must explain the alignment basis."
        ] ;
        sh:property [
            sh:path ft:requiresJsonArrayParsing ;
            sh:minCount 1 ;
            sh:maxCount 1 ;
            sh:datatype xsd:boolean ;
            sh:message "Outcome token alignments must say whether JSON array parsing is required."
        ] .

    ft:OutcomeTokenAlignmentPatternShape a sh:NodeShape ;
        sh:targetClass ft:OutcomeTokenAlignmentPattern ;
        sh:property [
            sh:path ft:impliedLatentEntity ;
            sh:minCount 1 ;
            sh:nodeKind sh:IRI ;
            sh:message "Pattern-first outcome token lore must name the latent entity it preserves."
        ] ;
        sh:property [
            sh:path ft:keepsArrayOrderUnresolved ;
            sh:maxCount 1 ;
            sh:datatype xsd:boolean ;
            sh:message "keepsArrayOrderUnresolved must be a boolean if supplied."
        ] .
    """
    flawed_map = f"""
    @prefix ft: <{ft}> .
    @prefix pm: <https://richcanopy.org/example/manifest/polymarket#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ft:outcome_token_alignment_v1 a ft:OutcomeTokenAlignment ;
        rdfs:label "Outcome token alignment across Gamma and CLOB tables" ;
        ft:alignmentMarketTable pm:MarketSnapshots ;
        ft:conditionIdColumn pm:mkt_condition_id ;
        ft:outcomeLabelArrayColumn pm:mkt_outcomes ;
        ft:downstreamTokenColumn pm:px_token_id, pm:ob_asset_id, pm:tr_asset, pm:hld_token ;
        ft:alignmentBasis "Outcome labels and token ids are expected to line up by array position before downstream tables expose scalar token ids." ;
        ft:requiresJsonArrayParsing true .
    """
    repaired_map = flawed_map.replace(
        "ft:outcomeLabelArrayColumn pm:mkt_outcomes ;",
        (
            "ft:outcomeLabelArrayColumn pm:mkt_outcomes ;\n"
            "        ft:clobTokenIdArrayColumn pm:mkt_clob_token_ids ;"
        ),
    )
    pattern_first = f"""
    @prefix ft: <{ft}> .
    @prefix pm: <https://richcanopy.org/example/manifest/polymarket#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ft:outcome_slot_latent_entity a ft:OutcomeSlot ;
        rdfs:label "Latent Polymarket outcome slot" .

    ft:outcome_token_alignment_pattern a ft:OutcomeTokenAlignmentPattern, rc:Pattern ;
        rdfs:label "Outcome token alignment pattern" ;
        rc:summary "Outcome/token alignment is a positional array bridge." ;
        rc:patternText "Gamma outcomes and clobTokenIds arrays imply a latent outcome slot before CLOB token ids appear as scalar columns." ;
        rc:rationale "This keeps the array-order hunch tentative instead of pretending the map already has a plain foreign key." ;
        rc:patternTarget pm:mkt_outcomes, pm:mkt_clob_token_ids, pm:same_entity_clob_token ;
        rc:supportingClaim <{claim.claim_iri}> ;
        rc:mapImplication ft:outcome_slot_latent_entity, ft:outcome_token_alignment_v1 ;
        rc:patternStability rc:EmergingPattern ;
        ft:impliedLatentEntity ft:outcome_slot_latent_entity ;
        ft:keepsArrayOrderUnresolved true .
    """
    shared_additions = [
        {"graph": "ontology", "content": shared_ontology},
        {"graph": "shapes", "content": shared_shapes},
    ]

    failed = db.stage_systematisation(
        summary="Model Polymarket outcome-token alignment",
        intent=(
            "Test whether provisional shapes catch a missing source array in "
            "a Polymarket outcome-token alignment hunch."
        ),
        anchors=[
            "https://richcanopy.org/example/manifest/polymarket#MarketSnapshots",
            "https://richcanopy.org/example/manifest/polymarket#mkt_outcomes",
            "https://richcanopy.org/example/manifest/polymarket#mkt_clob_token_ids",
            pattern.pattern_iri,
        ],
        supporting_claims=[claim.claim_iri],
        supporting_patterns=[pattern.pattern_iri],
        shared_context_summary=(
            "Define provisional outcome-token alignment vocabulary and shapes."
        ),
        shared_additions=shared_additions,
        framings=[
            {
                "label": "Flawed map candidate missing token array source",
                "graph": "map",
                "content": flawed_map,
                "stance": "rc:CandidateRevision",
            }
        ],
        validation_scope="all",
    )

    assert failed.framings[0].validation_conforms is False
    diagnostic = failed.framings[0].validation_results[0]
    assert diagnostic.focus_node == f"{ft}outcome_token_alignment_v1"
    assert diagnostic.result_path == f"{ft}clobTokenIdArrayColumn"
    assert diagnostic.source_constraint_component == (
        "http://www.w3.org/ns/shacl#MinCountConstraintComponent"
    )
    assert "CLOB token-id array column" in diagnostic.messages[0]

    failed_description = db.describe_staged_revision(
        failed.staged_revisions[0].revision_iri
    )
    failed_export_path = tmp_path / "failed-polymarket-alignment.md"
    db.export_staged_revision(failed_description.iri, failed_export_path)
    failed_export_text = failed_export_path.read_text()
    assert "## Validation Results" in failed_export_text
    assert "Result path: clobTokenIdArrayColumn" in failed_export_text
    assert "Outcome token alignments must name the CLOB token-id array column." in (
        failed_export_text
    )

    repaired = db.stage_systematisation(
        summary="Repair Polymarket outcome-token alignment",
        intent=(
            "Use the failed validation diagnostic to add the missing token "
            "array source, while preserving a pattern-first alternative."
        ),
        anchors=[
            "https://richcanopy.org/example/manifest/polymarket#MarketSnapshots",
            "https://richcanopy.org/example/manifest/polymarket#mkt_outcomes",
            "https://richcanopy.org/example/manifest/polymarket#mkt_clob_token_ids",
            pattern.pattern_iri,
        ],
        supporting_claims=[claim.claim_iri],
        supporting_patterns=[pattern.pattern_iri],
        shared_context_summary=(
            "Reuse the same provisional outcome-token alignment vocabulary and shapes."
        ),
        shared_additions=shared_additions,
        alternative_to=failed_description.iri,
        framings=[
            {
                "label": "Repaired map candidate with token array source",
                "graph": "map",
                "content": repaired_map,
                "stance": "rc:CandidateRevision",
            },
            {
                "label": "Pattern-first latent outcome slot",
                "graph": "patterns",
                "content": pattern_first,
                "stance": "rc:AlternativeSystematisation",
            },
        ],
        validation_scope="all",
    )

    assert [framing.validation_conforms for framing in repaired.framings] == [
        True,
        True,
    ]
    repaired_description = db.describe_staged_revision(
        repaired.staged_revisions[0].revision_iri
    )
    pattern_description = db.describe_staged_revision(
        repaired.staged_revisions[1].revision_iri
    )
    assert repaired_description.alternative_to is not None
    assert repaired_description.alternative_to.iri == failed_description.iri
    assert pattern_description.alternative_to is not None
    assert pattern_description.alternative_to.iri == repaired_description.iri
    assert db.triple_count("map") == before_map_count
    assert db.triple_count("ontology") == before_ontology_count
    assert db.triple_count("shapes") == before_shapes_count
    assert db.validate_graph(scope="all").conforms


def test_describe_query_context_suggests_dataset_layout_status_repair(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    warehouse = tmp_path / "warehouse"
    warehouse.mkdir()
    dataset = "https://example.test/project#Orders"
    storage = "https://example.test/project#orders_storage"
    layout = "https://example.test/project#orders_csv_layout"
    template = "orders/current.csv"
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        path_templates=[template],
        layout_verification_status="rc:CandidateLayout",
        layout_verification_note=(
            "Dataset-level status was copied from a manifest candidate before "
            "storage and physical layout were reviewed."
        ),
    )

    storage_repair = db.stage_query_storage_access_repair(
        dataset,
        storage,
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(warehouse),
        location_kind="directory",
        rationale="Reviewed the local warehouse storage route for Orders.",
        layout_verification_status="rc:VerifiedByListingLayout",
        layout_verification_note="Directory listing confirmed the Orders route.",
    )
    assert db.check_staged_revision_apply(storage_repair.revision_iri).status == (
        "ready"
    )
    db.apply_staged_revision(storage_repair.revision_iri)
    physical_repair = db.stage_query_physical_layout_repair(
        dataset,
        layout,
        file_format="rc:CSV",
        rationale="Reviewed Orders as CSV files.",
        layout_verification_status="rc:VerifiedByQueryLayout",
        layout_verification_note="A read-only query confirmed the CSV layout.",
    )
    assert db.check_staged_revision_apply(physical_repair.revision_iri).status == (
        "ready"
    )
    db.apply_staged_revision(physical_repair.revision_iri)

    context = db.describe_query_context(dataset)

    assert context.readiness == "needs_review"
    assert context.query_target_decision.status == "candidate_needs_review"
    assert context.query_target_decision.reason_codes == [
        "layout_needs_verification"
    ]
    assert context.suggested_repair_action_group_count == 1
    repair_group = context.suggested_repair_action_groups[0]
    assert repair_group.issue_code == "layout_needs_verification"
    assert repair_group.issue_resource is not None
    assert repair_group.issue_resource.iri == dataset
    assert repair_group.repair_action_type == (
        "replace_dataset_layout_verification_status"
    )
    assert repair_group.choice_mode == "choose_one"
    assert repair_group.pending_required_extra_arguments == ["rationale"]
    assert repair_group.repair_context["current_layout_verification_status_iri"] == (
        RC + "CandidateLayout"
    )
    assert repair_group.repair_context["verified_storage_access_iris"] == [storage]
    assert repair_group.repair_context["verified_physical_layout_iris"] == [layout]
    assert [action["args"]["object"] for action in repair_group.actions] == [
        "rc:VerifiedByListingLayout",
        "rc:VerifiedByQueryLayout",
    ]
    listing_action = repair_group.actions[0]
    assert listing_action["tool"] == "doxabase.stage_map_assertion_change"
    assert listing_action["args"]["subject"] == dataset
    assert listing_action["args"]["predicate"] == (
        "rc:layoutVerificationStatus"
    )
    assert listing_action["args"]["change_kind"] == "replace"
    assert context.suggested_next_actions
    draft_action = context.suggested_next_actions[0]
    assert draft_action.tool == "doxabase.draft_query_plan"

    arguments = dict(listing_action["args"])
    arguments["rationale"] = "Reviewed the dataset-owned path template by listing."
    status_repair = db.stage_map_assertion_change(**arguments)
    assert db.check_staged_revision_apply(status_repair.revision_iri).status == (
        "ready"
    )
    db.apply_staged_revision(status_repair.revision_iri)

    repaired_context = db.describe_query_context(dataset)

    assert repaired_context.readiness == "ready_for_query_planning"
    assert repaired_context.suggested_repair_action_groups == []
    assert repaired_context.layout_verification_status is not None
    assert repaired_context.layout_verification_status.iri == (
        RC + "VerifiedByListingLayout"
    )


def test_missing_storage_access_lifts_database_relation_candidate_from_query_evidence(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#SupportTicketDaily"
    relation_handle = "warehouse-prod:analytics.support_ticket_daily"
    db.record_map_dataset(dataset, label="Support ticket daily", is_table=True)
    db.record_query_result(
        summary=(
            "Support ticket daily aggregate ran through an external warehouse "
            "client before storage metadata was recorded."
        ),
        observed_asset=dataset,
        execution_status="succeeded",
        engine="external-sql-client",
        query_source_path="queries/support_ticket_daily.sql",
        result_sources=["artifacts/support_ticket_daily.json"],
        scanned_source_handles=[
            relation_handle,
            "s3://warehouse/support_ticket_daily.parquet",
            "warehouse/support_ticket_daily.csv",
        ],
    )

    context = db.describe_query_context(dataset)
    missing_storage = next(
        issue for issue in context.issues if issue.code == "missing_storage_access"
    )

    assert missing_storage.details is not None
    repair_hint = missing_storage.details["repair_hint"]
    assert repair_hint["database_relation_candidate_source"] == (
        "query_result_scanned_source_handles"
    )
    assert repair_hint["database_relation_candidate_count"] == 1
    assert repair_hint["database_relation_candidate_total_count"] == 1
    candidate = repair_hint["database_relation_candidates"][0]
    assert candidate["requires_review"] is True
    assert candidate["scanned_source_handle"] == relation_handle
    assert candidate["connection_reference"] == "warehouse-prod"
    assert candidate["relation_identifier"] == "analytics.support_ticket_daily"
    assert candidate["stage_query_storage_access_repair_candidate_arguments"] == {
        "storage_protocol": "rc:DatabaseStorage",
        "storage_root": "warehouse-prod",
        "location_kind": "connection",
        "path_templates": ["analytics.support_ticket_daily"],
    }
    route_candidates = repair_hint["evidence_storage_route_candidates"]
    assert [item["candidate_kind"] for item in route_candidates] == [
        "database_relation_from_query_evidence",
        "s3_path_from_query_evidence",
        "local_path_from_query_evidence",
    ]
    assert route_candidates[0][
        "stage_query_storage_access_repair_candidate_arguments"
    ] == {
        "storage_protocol": "rc:DatabaseStorage",
        "storage_root": "warehouse-prod",
        "location_kind": "connection",
        "path_templates": ["analytics.support_ticket_daily"],
    }
    assert route_candidates[0][
        "draft_query_evidence_storage_overlay_candidate_arguments"
    ] == {
        "storage_protocol": "rc:DatabaseStorage",
        "storage_root": "warehouse-prod",
        "location_kind": "connection",
        "path_templates": ["analytics.support_ticket_daily"],
        "file_format": "REVIEWED_DATABASE_TABLE_FILE_FORMAT",
    }
    assert route_candidates[1]["storage_protocol"] == "rc:S3CompatibleStorage"
    assert route_candidates[1]["storage_root"] == "s3://warehouse"
    assert route_candidates[1]["bucket_name"] == "warehouse"
    assert route_candidates[1]["path_templates"] == [
        "support_ticket_daily.parquet"
    ]
    assert route_candidates[1]["file_format"] == "rc:Parquet"
    assert route_candidates[2]["storage_protocol"] == "rc:LocalFilesystemStorage"
    assert route_candidates[2]["storage_root"] == "warehouse"
    assert route_candidates[2]["path_templates"] == ["support_ticket_daily.csv"]
    assert route_candidates[2]["file_format"] == "rc:CSV"

    repair_group = context.suggested_repair_action_groups[0]
    assert repair_group.issue_code == "missing_storage_access"
    assert repair_group.repair_context["database_relation_candidates"] == [
        candidate
    ]
    assert repair_group.repair_context[
        "database_relation_candidate_review_note"
    ].startswith("These candidates are parsed")
    assert db.validate_graph(scope="all").conforms


def test_describe_query_context_suggests_missing_physical_layout_repair(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WarehouseOrders"
    storage = db.record_map_storage_access(
        "https://example.test/project#warehouse_orders_storage",
        label="Warehouse orders database",
        storage_protocol="rc:DatabaseStorage",
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

    context = db.describe_query_context(dataset)

    missing_layout = next(
        issue for issue in context.issues if issue.code == "missing_physical_layout"
    )
    assert missing_layout.details is not None
    assert missing_layout.details["dataset_iri"] == dataset
    assert missing_layout.details["storage_protocol_iris"] == [RC + "DatabaseStorage"]
    assert missing_layout.details["database_storage_present"] is True
    repair_hint = missing_layout.details["repair_hint"]
    assert repair_hint["action_type"] == "record_or_stage_physical_layout"
    assert repair_hint["choice_mode"] == "choose_one"
    assert "rc:PostgreSQLTable" in repair_hint["file_format_guidance"][
        "rc:DatabaseStorage"
    ]
    repair_group = next(
        group
        for group in context.suggested_repair_action_groups
        if group.issue_code == "missing_physical_layout"
    )
    assert repair_group.repair_action_type == "record_or_stage_physical_layout"
    assert repair_group.issue_resource is not None
    assert repair_group.issue_resource.iri == dataset
    assert repair_group.choice_mode == "choose_one"
    assert repair_group.repair_context["database_storage_present"] is True
    assert repair_group.repair_context["storage_protocol_iris"] == [
        RC + "DatabaseStorage"
    ]
    assert repair_group.pending_required_extra_arguments == [
        "layout_iri",
        "file_format",
        "rationale",
        "iri",
    ]
    assert len(repair_group.pending_action_options) == 2
    staged_option = repair_group.pending_action_options[0]
    _assert_repair_action_option(
        staged_option,
        action_index=0,
        action_type="stage_reviewed_physical_layout",
        tool="doxabase.stage_query_physical_layout_repair",
        required_extra_arguments=[
            "layout_iri",
            "file_format",
            "rationale",
        ],
        placeholder_fields=[
            "layout_iri",
            "file_format",
            "rationale",
            "layout_verification_status",
            "layout_verification_note",
        ],
        reviewed_value_fields=[
            "layout_iri",
            "file_format",
            "rationale",
            "layout_verification_status",
            "layout_verification_note",
        ],
    )
    assert "staged-revision rationale" in staged_option["reason"]
    assert "rc:PostgreSQLTable" in staged_option["condition"]
    assert "stage_query_physical_layout_repair records a reviewable" in (
        staged_option["review_rationale_guidance"]
    )
    layout_option = repair_group.pending_action_options[1]
    _assert_repair_action_option(
        layout_option,
        action_index=1,
        action_type="record_reviewed_physical_layout",
        tool="doxabase.record_map_fact",
        required_extra_arguments=["iri", "file_format"],
        placeholder_fields=[
            "file_format",
            "layout_verification_status",
            "layout_verification_note",
        ],
        reviewed_value_fields=[
            "file_format",
            "layout_verification_status",
            "layout_verification_note",
        ],
    )
    assert "file format or database table layout" in layout_option["reason"]
    assert "rc:PostgreSQLTable" in layout_option["condition"]
    assert "record_map_physical_layout writes current-best map facts directly" in (
        layout_option["review_rationale_guidance"]
    )
    assert context.suggested_next_actions
    draft_action = context.suggested_next_actions[0]
    assert draft_action.tool == "doxabase.draft_query_plan"
    action = repair_group.actions[0]
    assert action["tool"] == "doxabase.stage_query_physical_layout_repair"
    assert action["arguments_template"]["dataset_iri"] == dataset
    assert action["arguments_template"]["layout_iri"] == (
        "<reviewed physical layout IRI>"
    )
    assert action["arguments_template"]["file_format"] == (
        "<reviewed rc:FileFormat IRI>"
    )
    assert "rc:PostgreSQLTable" in action["condition"]
    direct_action = repair_group.actions[1]
    assert direct_action["tool"] == "doxabase.record_map_fact"
    assert direct_action["arguments_template"]["kind"] == "physical_layout"
    assert direct_action["arguments_template"]["spec"]["datasets"] == [dataset]
    assert direct_action["arguments_template"]["spec"]["file_format"] == (
        "<reviewed rc:FileFormat IRI>"
    )

    layout_iri = "https://example.test/project#warehouse_orders_table_layout"
    staged = db.stage_query_physical_layout_repair(
        dataset_iri=dataset,
        layout_iri=layout_iri,
        file_format="rc:PostgreSQLTable",
        rationale="Reviewed the warehouse relation as a PostgreSQL table layout.",
        layout_verification_status="rc:VerifiedByQueryLayout",
        layout_verification_note="Reviewed from warehouse source metadata.",
    )
    assert staged.validation_conforms is True
    assert db.check_staged_revision_apply(staged.revision_iri).status == "ready"
    db.apply_staged_revision(staged.revision_iri)

    repaired_context = db.describe_query_context(dataset)
    assert "missing_physical_layout" not in {
        issue.code for issue in repaired_context.issues
    }
    plan = db.draft_query_plan(dataset)
    assert plan.handoff_kind == "database_relation_handoff"
    assert plan.scan.physical_layout is not None
    assert plan.scan.physical_layout.iri == layout_iri


def test_missing_storage_access_link_template_has_no_hidden_anchor_placeholder(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Messages"
    storage = db.record_map_storage_access(
        "https://example.test/project#messages_storage",
        label="Messages storage",
        storage_protocol="rc:LocalFilesystemStorage",
        route_roles=["rc:CurrentRoute"],
        storage_root=str(tmp_path / "warehouse"),
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    db.record_map_dataset(dataset, label="Messages", is_table=True)

    context = db.describe_query_context(dataset)
    missing_storage = next(
        issue for issue in context.issues if issue.code == "missing_storage_access"
    )
    assert missing_storage.details is not None
    repair_hint = missing_storage.details["repair_hint"]
    assert repair_hint["candidate_existing_storage_access_count"] == 1
    assert repair_hint["candidate_existing_storage_access_total_count"] == 1
    assert repair_hint["candidate_existing_storage_accesses_truncated"] is False
    candidate = repair_hint["candidate_existing_storage_accesses"][0]
    assert candidate["candidate_rank"] == 1
    assert candidate["storage_access_iri"] == storage.iri
    assert candidate["storage_access"]["iri"] == storage.iri
    assert [role["iri"] for role in candidate["route_roles"]] == [
        RC + "CurrentRoute"
    ]
    assert candidate["route_role_labels"] == ["current route"]
    assert candidate["storage_protocol"]["iri"] == RC + "LocalFilesystemStorage"
    assert candidate["storage_root"] == str(tmp_path / "warehouse")
    assert candidate["path_templates"] == []
    assert candidate["layout_verification_status"]["iri"] == (
        RC + "VerifiedByListingLayout"
    )
    assert candidate["match_reasons"] == [
        "declares_storage_protocol",
        "has_location_metadata",
        "has_layout_verification_status",
        "dataset_token_overlap",
    ]
    assert candidate["dataset_token_matches"] == ["messages"]
    assert candidate["dataset_partial_token_matches"] == []
    repair_group = context.suggested_repair_action_groups[0]
    assert repair_group.repair_context[
        "candidate_existing_storage_accesses"
    ][0]["storage_access_iri"] == storage.iri
    assert [
        role["iri"]
        for role in repair_group.repair_context[
            "candidate_existing_storage_accesses"
        ][0]["route_roles"]
    ] == [RC + "CurrentRoute"]
    link_action = repair_hint["actions"][2]

    assert link_action["action_type"] == "stage_existing_storage_access_link"
    assert link_action["required_extra_arguments"] == ["object", "rationale"]
    assert link_action["placeholder_fields"] == ["object"]
    assert link_action["reviewed_value_fields"] == ["object"]
    assert "revision_anchors" not in link_action["arguments_template"]

    arguments = dict(link_action["arguments_template"])
    arguments["object"] = storage.iri
    arguments["rationale"] = "Reviewed the existing storage access for Messages."

    staged = db.stage_map_assertion_change(**arguments)

    assert db.check_staged_revision_apply(staged.revision_iri).status == "ready"
    staged_payload = to_jsonable(staged)
    assert "<reviewed existing storage access IRI>" not in json.dumps(
        staged_payload,
        sort_keys=True,
    )

    pending_context = db.describe_query_context(dataset)
    pending_missing_storage = next(
        issue
        for issue in pending_context.issues
        if issue.code == "missing_storage_access"
    )
    assert pending_missing_storage.details is not None
    pending_repair_hint = pending_missing_storage.details["repair_hint"]
    pending_candidate = pending_repair_hint["candidate_existing_storage_accesses"][0]
    assert pending_candidate["storage_access_iri"] == storage.iri
    assert pending_candidate["candidate_status"] == "already_pending"
    assert pending_candidate["pending_staged_repair_iris"] == [staged.revision_iri]
    assert pending_repair_hint["already_pending_candidate_count"] == 1
    assert pending_repair_hint["already_pending_storage_access_iris"] == [
        storage.iri
    ]
    assert pending_repair_hint["pending_staged_repair_iris"] == [
        staged.revision_iri
    ]
    pending_repair_group = pending_context.suggested_repair_action_groups[0]
    assert pending_repair_group.choice_mode == "choose_one"
    assert pending_repair_group.repair_context[
        "already_pending_candidate_count"
    ] == 1
    assert pending_repair_group.repair_context[
        "already_pending_storage_access_iris"
    ] == [storage.iri]
    assert pending_repair_group.repair_context["pending_staged_repair_iris"] == [
        staged.revision_iri
    ]
    assert pending_repair_group.action_status_counts == {
        "pending_review": 2,
        "already_pending": 1,
    }
    assert pending_repair_group.pending_action_count == 2
    assert pending_repair_group.skippable_action_count == 1
    assert pending_repair_group.pending_required_extra_arguments == [
        "storage_access_iri",
        "storage_protocol",
        "storage_root",
        "rationale",
        "iri",
    ]
    pending_action_by_type = {
        action["action_type"]: action for action in pending_repair_group.actions
    }
    pending_link_action = pending_action_by_type["stage_existing_storage_access_link"]
    assert pending_link_action["action_status"] == "already_pending"
    assert pending_link_action["skip_when_already_pending"] is True
    assert pending_link_action["already_pending_candidate_count"] == 1
    assert pending_link_action["already_pending_storage_access_iris"] == [
        storage.iri
    ]
    assert pending_link_action["pending_staged_repair_iris"] == [
        staged.revision_iri
    ]
    assert len(pending_repair_group.pending_action_options) == 2
    optional_storage_fields = [
        "endpoint_profile",
        "bucket_name",
        "key_prefix",
        "region",
        "path_style_access",
        "credential_reference",
    ]
    pending_staged_storage_option = pending_repair_group.pending_action_options[0]
    _assert_repair_action_option(
        pending_staged_storage_option,
        action_index=0,
        action_type="stage_reviewed_storage_access",
        tool="doxabase.stage_query_storage_access_repair",
        required_extra_arguments=[
            "storage_access_iri",
            "storage_protocol",
            "storage_root",
            "rationale",
        ],
        placeholder_fields=[
            "storage_access_iri",
            "storage_protocol",
            "storage_root",
            *optional_storage_fields,
            "rationale",
            "location_kind",
            "path_templates",
            "layout_verification_status",
            "layout_verification_note",
        ],
        reviewed_value_fields=[
            "storage_access_iri",
            "storage_protocol",
            "storage_root",
            *optional_storage_fields,
            "rationale",
            "location_kind",
            "path_templates",
            "layout_verification_status",
            "layout_verification_note",
        ],
    )
    pending_storage_option = pending_repair_group.pending_action_options[1]
    _assert_repair_action_option(
        pending_storage_option,
        action_index=1,
        action_type="record_reviewed_storage_access",
        tool="doxabase.record_map_fact",
        required_extra_arguments=[
            "iri",
            "storage_protocol",
            "storage_root",
        ],
        placeholder_fields=[*optional_storage_fields, "path_templates"],
        reviewed_value_fields=[*optional_storage_fields, "path_templates"],
    )
    assert "non-secret storage protocol" in pending_storage_option["reason"]
    assert "Database relation identifiers" in pending_storage_option["condition"]
    assert "record_map_storage_access writes current-best map facts directly" in (
        pending_storage_option["review_rationale_guidance"]
    )


def test_missing_storage_access_ranks_dataset_specific_candidates_first(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    events_storage = db.record_map_storage_access(
        "https://example.test/project#events_local_storage",
        label="Events local directory",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(tmp_path / "warehouse"),
        path_templates=["events/current/*.parquet"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        "https://example.test/project#Events",
        label="Events",
        is_table=True,
        storage_accesses=[events_storage.iri],
    )
    generic_storage = db.record_map_storage_access(
        "https://example.test/project#generic_archive_storage",
        label="Generic archive directory",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(tmp_path / "archive"),
        layout_verification_status="rc:CandidateLayout",
    )
    orphan_storage = db.record_map_storage_access(
        "https://example.test/project#orphan_nearby_storage",
        label="Nearby orphan facts directory",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(tmp_path / "warehouse" / "orphan-facts"),
        path_templates=["facts/*.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    orphan = "https://example.test/project#OrphanFacts"
    db.record_map_dataset(orphan, label="Orphan facts", is_table=True)

    context = db.describe_query_context(orphan)
    missing_storage = next(
        issue for issue in context.issues if issue.code == "missing_storage_access"
    )
    assert missing_storage.details is not None
    candidates = missing_storage.details["repair_hint"][
        "candidate_existing_storage_accesses"
    ]

    assert [candidate["storage_access_iri"] for candidate in candidates[:3]] == [
        orphan_storage.iri,
        generic_storage.iri,
        events_storage.iri,
    ]
    assert candidates[0]["candidate_rank"] == 1
    assert candidates[0]["dataset_token_matches"] == ["facts", "orphan"]
    assert "dataset_token_overlap" in candidates[0]["match_reasons"]
    assert "linked_to_other_dataset" in candidates[2]["match_reasons"]
    assert context.suggested_repair_action_groups[0].repair_context[
        "candidate_existing_storage_accesses"
    ][0]["storage_access_iri"] == orphan_storage.iri


def test_missing_storage_access_downweights_generic_token_candidates(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    target = "https://example.test/project#AlphaTrialSnapshotData"
    intended_storage = db.record_map_storage_access(
        "https://example.test/project#alpha_storage",
        label="Alpha storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(tmp_path / "alpha"),
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    generic_storage = db.record_map_storage_access(
        "https://example.test/project#generic_data_trial_snapshot_parquet_storage",
        label="Generic data trial snapshot parquet storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(tmp_path / "data-trial-snapshot-parquet"),
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    linked_generic_storage = db.record_map_storage_access(
        "https://example.test/project#linked_data_trial_snapshot_parquet_storage",
        label="Linked data trial snapshot parquet storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(tmp_path / "linked-data-trial-snapshot-parquet"),
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    db.record_map_dataset(
        "https://example.test/project#GenericTrialSnapshotArchive",
        label="Generic trial snapshot archive",
        is_table=True,
        storage_accesses=[linked_generic_storage.iri],
    )
    database_generic_storage = db.record_map_storage_access(
        "https://example.test/project#analytics_trial_snapshot_data_relation",
        label="Analytics trial snapshot data relation",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="analytics-trial-snapshot",
        path_templates=["trial_snapshot_data"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        target,
        label="Alpha trial snapshot data",
        is_table=True,
        path_templates=["data/trial/snapshot/*.parquet"],
    )

    context = db.describe_query_context(target)
    missing_storage = next(
        issue for issue in context.issues if issue.code == "missing_storage_access"
    )
    assert missing_storage.details is not None
    candidates = missing_storage.details["repair_hint"][
        "candidate_existing_storage_accesses"
    ]

    assert [candidate["storage_access_iri"] for candidate in candidates[:4]] == [
        intended_storage.iri,
        generic_storage.iri,
        database_generic_storage.iri,
        linked_generic_storage.iri,
    ]
    intended_candidate = candidates[0]
    assert intended_candidate["dataset_token_matches"] == ["alpha"]
    assert intended_candidate["generic_dataset_token_matches"] == []
    assert "dataset_token_overlap" in intended_candidate["match_reasons"]

    generic_candidate = candidates[1]
    assert generic_candidate["dataset_token_matches"] == []
    assert generic_candidate["generic_dataset_token_matches"] == [
        "data",
        "parquet",
        "snapshot",
        "trial",
    ]
    assert "generic_dataset_token_overlap" in generic_candidate["match_reasons"]
    assert "dataset_token_overlap" not in generic_candidate["match_reasons"]

    linked_candidate = candidates[3]
    assert linked_candidate["storage_access_iri"] == linked_generic_storage.iri
    assert "linked_to_other_dataset" in linked_candidate["match_reasons"]
    assert linked_candidate["linked_dataset_iris"] == [
        "https://example.test/project#GenericTrialSnapshotArchive"
    ]

    link_action = next(
        action
        for action in missing_storage.details["repair_hint"]["actions"]
        if action["action_type"] == "stage_existing_storage_access_link"
    )
    arguments = dict(link_action["arguments_template"])
    arguments["object"] = intended_storage.iri
    arguments["rationale"] = "Reviewed the Alpha storage candidate."
    staged = db.stage_map_assertion_change(**arguments)

    pending_context = db.describe_query_context(target)
    pending_missing_storage = next(
        issue
        for issue in pending_context.issues
        if issue.code == "missing_storage_access"
    )
    assert pending_missing_storage.details is not None
    pending_repair_hint = pending_missing_storage.details["repair_hint"]
    assert pending_repair_hint["already_pending_candidate_count"] == 1
    assert pending_repair_hint["already_pending_storage_access_iris"] == [
        intended_storage.iri
    ]
    assert pending_repair_hint["pending_staged_repair_iris"] == [
        staged.revision_iri
    ]
    pending_repair_group = pending_context.suggested_repair_action_groups[0]
    assert pending_repair_group.action_status_counts == {"pending_review": 3}
    assert pending_repair_group.pending_action_count == 3
    assert pending_repair_group.skippable_action_count == 0
    assert pending_repair_group.repair_context[
        "already_pending_candidate_count"
    ] == 1
    assert pending_repair_group.repair_context[
        "already_pending_storage_access_iris"
    ] == [intended_storage.iri]
    assert pending_repair_group.repair_context["pending_staged_repair_iris"] == [
        staged.revision_iri
    ]
    pending_options_by_type = {
        option["action_type"]: option
        for option in pending_repair_group.pending_action_options
    }
    pending_link_option = pending_options_by_type[
        "stage_existing_storage_access_link"
    ]
    assert pending_link_option["action_status"] == "pending_review"
    assert pending_link_option["already_pending_candidate_count"] == 1
    assert pending_link_option["already_pending_storage_access_iris"] == [
        intended_storage.iri
    ]
    assert pending_link_option["pending_staged_repair_iris"] == [
        staged.revision_iri
    ]


def test_missing_storage_access_repair_omits_duplicate_path_template(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    template = "events/date={date}/*.parquet"
    layout = db.record_map_physical_layout(
        "https://example.test/project#events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Events",
        is_table=True,
        path_templates=[template],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    before = db.describe_query_context(dataset)
    missing_storage = next(
        issue for issue in before.issues if issue.code == "missing_storage_access"
    )
    assert missing_storage.details is not None
    repair_actions = {
        action["action_type"]: action
        for action in missing_storage.details["repair_hint"]["actions"]
    }
    staged_action = repair_actions["stage_reviewed_storage_access"]
    direct_action = repair_actions["record_reviewed_storage_access"]
    assert "Omit them when the dataset or partition already carries" in (
        staged_action["condition"]
    )
    assert "Omit this optional field" in direct_action["condition"]

    db.record_map_storage_access(
        "https://example.test/project#events_local_storage",
        label="Events local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(tmp_path / "warehouse"),
        datasets=[dataset],
        layout_verification_status="rc:VerifiedByListingLayout",
    )

    after = db.describe_query_context(dataset)

    assert after.readiness == "ready_for_query_planning"
    assert after.issues == []
    assert len(after.query_target_candidates) == 1
    candidate = after.query_target_candidates[0]
    assert candidate.template == template
    assert candidate.template_source == "dataset"
    assert candidate.composition == "storage_root_joined"
    assert candidate.candidate_path_status == "ready"
    draft_actions = [
        action
        for action in after.suggested_next_actions
        if action.tool == "doxabase.draft_query_plan"
    ]
    assert len(draft_actions) == 1


def test_describe_query_context_flags_known_fixture_without_storage_access(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"
    db.record_map_dataset(dataset, label="AIS Daily Broadcast Positions", is_table=True)

    context = db.describe_query_context(dataset)
    missing_storage = next(
        issue for issue in context.issues if issue.code == "missing_storage_access"
    )

    assert missing_storage.details is not None
    fixture_hint = missing_storage.details["fixture_staleness_hint"]
    assert fixture_hint["hint_type"] == (
        "known_fixture_tables_without_storage_accesses"
    )
    assert fixture_hint["fixture_names"] == ["AIS"]
    assert fixture_hint["global_storage_access_count"] == 0
    assert fixture_hint["dataset_matches_known_fixture"] is True
    assert dataset in fixture_hint["known_fixture_table_iris"]
    assert "stale or intentionally reduced" in fixture_hint["message"]

    repair_group = context.suggested_repair_action_groups[0]
    assert repair_group.issue_code == "missing_storage_access"
    assert repair_group.action_status_counts == {"pending_review": 3}
    assert len(repair_group.group_advisories) == 1
    advisory = repair_group.group_advisories[0]
    assert advisory["code"] == "query_fixture_staleness_review"
    assert advisory["recommended_handling"] == (
        "review_fixture_staleness_before_staging"
    )
    assert advisory["suppression_policy"] == "review_group_before_member_mutation"
    assert advisory["fixture_names"] == ["AIS"]
    assert advisory["storage_access_count"] == 0
    assert advisory["dataset_matches_known_fixture"] is True
    assert dataset in advisory["known_fixture_table_iris"]
    assert advisory["suggested_next_action"]["tool"] == "doxabase.project_brief"


def test_describe_query_context_reports_storage_access_owned_target_candidate(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_storage",
        label="Orders S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        bucket_name="example-bucket",
        key_prefix="warehouse",
        path_templates=["orders/dt={date}.parquet"],
        credential_reference="profile:orders-readonly",
        layout_verification_status="rc:VerifiedByListingLayout",
        layout_verification_note="Confirmed by listing the warehouse prefix.",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#orders_parquet_layout",
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

    assert context.readiness == "ready_for_query_planning"
    assert len(context.query_target_candidates) == 1
    target = context.query_target_candidates[0]
    assert target.template_source == "storage_access"
    assert target.source_resource.iri == storage.iri
    assert target.storage_access is not None
    assert target.storage_access.iri == storage.iri
    assert target.candidate_path == "s3://example-bucket/warehouse/orders/dt={date}.parquet"
    assert target.composition == "bucket_prefix_joined"
    assert target.candidate_path_status == "ready"
    assert target.credential_reference == "profile:orders-readonly"
    assert target.review_required is False
    assert target.review_reasons == []
    assert context.query_target_decision.status == "ready"
    assert context.query_target_decision.candidate_index == 0
    assert context.query_target_decision.candidate_path == target.candidate_path
    assert context.query_target_decision.candidate_path_status == "ready"
    assert context.query_target_decision.direct_review_required is False
    assert context.query_target_decision.selected_candidate_direct_clean is True
    assert context.query_target_decision.reason_codes == []

    plan = db.draft_query_plan(dataset)
    assert plan.scan.template_source == "storage_access"
    assert plan.scan.template_source_resource is not None
    assert plan.scan.template_source_resource.iri == storage.iri
    assert plan.scan.template_source_verification_status is not None
    assert (
        plan.scan.template_source_verification_status.iri
        == RC + "VerifiedByListingLayout"
    )
    assert plan.scan.template_source_verification_note == (
        "Confirmed by listing the warehouse prefix."
    )
    assert plan.scan.template_lineage is not None
    assert "storage_access Orders S3 access" in plan.scan.template_lineage
    assert "verified by listing" in plan.scan.template_lineage
    assert "Confirmed by listing the warehouse prefix" in plan.scan.template_lineage
    assert plan.storage_environment.runtime_resolution_required is True
    assert plan.review_gate.executable_without_review is True
    assert plan.review_gate.runtime_resolution_required is True
    assert plan.review_gate.ready_for_execution_attempt is False
    assert plan.review_gate.execution_attempt_blocking_reason_codes == [
        "runtime_resolution_required",
        "binding_values_required",
    ]


def test_query_context_suggests_stale_partition_link_repair(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#DailyIndex"
    date_column = db.record_map_column(
        "https://example.test/project#daily_index__date",
        table_iri=dataset,
        column_name="date",
    )
    index_storage = db.record_map_storage_access(
        "https://example.test/project#daily_index_object_store_access",
        label="Daily index object-store access",
        storage_protocol="rc:S3CompatibleStorage",
        storage_root="s3://ais-noaa/",
        endpoint_profile="local-minio",
        credential_reference="profile:ais-readonly",
        path_templates=["index/*/*.parquet"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    stale_partition = db.record_map_partition_scheme(
        "https://example.test/project#broadcast_date_partition",
        path_template="broadcasts/{year}/ais-{date}.parquet",
        partition_columns=[date_column.iri],
        granularity="rc:Daily",
        layout_verification_status="rc:CandidateLayout",
        datasets=[dataset],
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#daily_index_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Daily index",
        is_table=True,
        columns=[date_column.iri],
        storage_accesses=[index_storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.query_target_decision.status == "context_blocked"
    assert context.query_target_decision.selected_candidate_direct_clean is True
    assert context.suggested_repair_action_group_count == 1
    repair_group = context.suggested_repair_action_groups[0]
    assert repair_group.issue_code == "layout_needs_verification"
    assert repair_group.issue_resource is not None
    assert repair_group.issue_resource.iri == stale_partition.iri
    assert repair_group.repair_action_type == "remove_stale_partition_scheme_link"
    assert repair_group.choice_mode == "review_all_applicable"
    assert repair_group.action_status_counts == {"pending_review": 1}
    assert repair_group.pending_required_extra_arguments == ["rationale"]
    assert len(repair_group.pending_action_options) == 1
    stale_partition_option = repair_group.pending_action_options[0]
    _assert_repair_action_option(
        stale_partition_option,
        action_index=0,
        action_type="remove_stale_partition_scheme_link",
        tool="doxabase.stage_map_assertion_change",
        required_extra_arguments=["rationale"],
        placeholder_fields=[],
        reviewed_value_fields=[],
    )
    assert "selected direct-clean query target" in stale_partition_option["reason"]
    assert "stale blocker" in stale_partition_option["condition"]
    action = repair_group.actions[0]
    assert action["tool"] == "doxabase.stage_map_assertion_change"
    assert action["args"] == {
        "subject": dataset,
        "predicate": "rc:partitionedBy",
        "object": stale_partition.iri,
        "object_kind": "iri",
        "change_kind": "remove",
        "graph": "map",
        "validation_scope": "all",
    }
    staged = db.stage_map_assertion_change(
        **action["args"],
        rationale=(
            "Reviewed DailyIndex wildcard storage as the intended route; the "
            "broadcast partition link is stale."
        ),
    )
    db.apply_staged_revision(staged.staged_revision.revision_iri)

    repaired_context = db.describe_query_context(dataset)
    assert repaired_context.suggested_repair_action_group_count == 0
    plan = db.draft_query_plan(dataset)
    assert plan.scan.uri_template == "s3://ais-noaa/index/*/*.parquet"
    assert plan.required_bindings == []
    assert plan.review_gate.binding_values_required is False


def test_query_context_suggests_stale_physical_layout_link_repair(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    storage = db.record_map_storage_access(
        "https://example.test/project#events_local_storage",
        label="Events local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/warehouse",
        path_templates=["events/current/*.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    verified_layout = db.record_map_physical_layout(
        "https://example.test/project#events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    stale_layout = db.record_map_physical_layout(
        "https://example.test/project#events_old_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:CandidateLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Events",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[verified_layout.iri, stale_layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.query_target_decision.status == "context_blocked"
    assert context.query_target_decision.selected_candidate_direct_clean is True
    assert context.suggested_repair_action_group_count == 1
    repair_group = context.suggested_repair_action_groups[0]
    assert repair_group.issue_code == "layout_needs_verification"
    assert repair_group.issue_resource is not None
    assert repair_group.issue_resource.iri == stale_layout.iri
    assert repair_group.repair_action_type == "remove_stale_physical_layout_link"
    assert repair_group.choice_mode == "review_all_applicable"
    assert repair_group.action_status_counts == {"pending_review": 1}
    assert repair_group.pending_required_extra_arguments == ["rationale"]
    assert len(repair_group.pending_action_options) == 1
    stale_layout_option = repair_group.pending_action_options[0]
    _assert_repair_action_option(
        stale_layout_option,
        action_index=0,
        action_type="remove_stale_physical_layout_link",
        tool="doxabase.stage_map_assertion_change",
        required_extra_arguments=["rationale"],
        placeholder_fields=[],
        reviewed_value_fields=[],
    )
    assert "verified sibling layout" in stale_layout_option["reason"]
    assert "stale blocker" in stale_layout_option["condition"]
    action = repair_group.actions[0]
    assert action["tool"] == "doxabase.stage_map_assertion_change"
    assert action["args"] == {
        "subject": dataset,
        "predicate": "rc:hasPhysicalLayout",
        "object": stale_layout.iri,
        "object_kind": "iri",
        "change_kind": "remove",
        "graph": "map",
        "validation_scope": "all",
    }
    staged = db.stage_map_assertion_change(
        **action["args"],
        rationale=(
            "Reviewed Events local storage as the intended route; the older "
            "candidate physical-layout link is stale."
        ),
    )
    db.apply_staged_revision(staged.staged_revision.revision_iri)

    repaired_context = db.describe_query_context(dataset)
    assert repaired_context.suggested_repair_action_group_count == 0
    assert repaired_context.query_target_decision.status == "ready"
    plan = db.draft_query_plan(dataset)
    assert plan.scan.uri_template == "/warehouse/events/current/*.parquet"
    assert plan.scan.function == "read_parquet"
    assert plan.scan.physical_layout is not None
    assert plan.scan.physical_layout.iri == verified_layout.iri
    assert plan.review_gate.binding_values_required is False


def test_distinct_physical_layout_signatures_require_explicit_review(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    storage = db.record_map_storage_access(
        "https://example.test/project#events_local_storage",
        label="Events local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/warehouse",
        path_templates=["events/current/*.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    parquet_layout = db.record_map_physical_layout(
        "https://example.test/project#events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    csv_layout = db.record_map_physical_layout(
        "https://example.test/project#events_csv_layout",
        file_format="rc:CSV",
        layout_verification_status="rc:CandidateLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Events",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[parquet_layout.iri, csv_layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.query_target_decision.status == "candidate_needs_review"
    assert context.query_target_decision.selected_candidate_direct_clean is False
    assert context.suggested_repair_action_group_count == 0
    assert [issue.code for issue in context.issues] == [
        "ambiguous_physical_layout",
        "layout_needs_verification",
    ]
    assert context.issues[1].resource is not None
    assert context.issues[1].resource.iri == csv_layout.iri
    layout_selection_actions = [
        action for action in context.suggested_next_actions
        if action.args.get("physical_layout_iri") is not None
    ]
    assert {
        action.args["physical_layout_iri"] for action in layout_selection_actions
    } == {parquet_layout.iri}
    layout_action = layout_selection_actions[0]

    selected_layout_plan = db.draft_query_plan(
        dataset,
        physical_layout_iri=parquet_layout.iri,
    )
    assert selected_layout_plan.handoff_kind == "metadata_review_required"
    assert selected_layout_plan.scan.function == "read_parquet"
    assert selected_layout_plan.scan.physical_layout is not None
    assert selected_layout_plan.scan.physical_layout.iri == parquet_layout.iri
    assert selected_layout_plan.review_gate.blocking_reason_codes == [
        "layout_needs_verification"
    ]


def test_describe_query_context_requires_storage_access_owned_location(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    storage = db.record_map_storage_access(
        "https://example.test/project#events_local_storage",
        label="Events local access",
        storage_protocol="rc:LocalFilesystemStorage",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Events",
        is_table=True,
        path_templates=["relative/dt={date}.parquet"],
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "insufficient_metadata"
    assert any(
        issue.code == "missing_storage_location"
        and issue.resource is not None
        and issue.resource.iri == storage.iri
        for issue in context.issues
    )
    target = context.query_target_candidates[0]
    assert target.candidate_path == "relative/dt={date}.parquet"
    assert target.candidate_path_status == "unresolved"
    assert target.review_required is True
    assert any(
        reason.code == "missing_storage_location"
        for reason in target.review_reasons
    )


def test_storage_metadata_trial_repairs_cold_query_route_and_records_result(
    tmp_path: Path,
) -> None:
    warehouse = tmp_path / "warehouse"
    events_dir = warehouse / "events"
    events_dir.mkdir(parents=True)
    csv_path = events_dir / "current.csv"
    csv_path.write_text(
        "event_id,status,amount_cents\n"
        "1,paid,1200\n"
        "2,pending,800\n"
        "3,paid,3100\n"
        "4,refunded,700\n",
        encoding="utf-8",
    )
    query_path = tmp_path / "event_status_aggregate.sql"
    query_path.write_text(
        "-- storage metadata trial query\n"
        "select status, count(*) as row_count\n"
        "from read_csv_auto($events_path)\n"
        "group by status;\n",
        encoding="utf-8",
    )
    result_path = tmp_path / "event_status_aggregate.result.json"
    result_path.write_text(
        json.dumps(
            {
                "row_count": 4,
                "status_counts": {
                    "paid": 2,
                    "pending": 1,
                    "refunded": 1,
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    db.import_trig(POLYMARKET_FIXTURE)
    base = "https://example.test/project#"
    dataset = f"{base}EventStatus"
    columns = [
        db.record_map_column(
            f"{base}event_status__{name}",
            table_iri=dataset,
            column_name=name,
        )
        for name in ("event_id", "status", "amount_cents")
    ]
    db.record_map_dataset(
        dataset,
        label="Event status",
        is_table=True,
        columns=[column.iri for column in columns],
        path_templates=["events/current.csv"],
    )

    initial_context = db.describe_query_context(dataset)
    assert initial_context.readiness == "insufficient_metadata"
    assert {issue.code for issue in initial_context.issues} >= {
        "missing_storage_access",
        "missing_physical_layout",
    }
    assert [
        (group.group_name, group.issue_code)
        for group in initial_context.suggested_repair_action_groups
    ] == [("query_repair_review", "missing_storage_access")]

    brief = db.project_brief(limit=20)
    repair_queue = next(
        queue
        for queue in brief.queues
        if queue.name == "query_repair_review"
    )
    assert repair_queue.count >= 1
    repair_action = next(
        action
        for action in brief.suggested_next_actions
        if action.tool == "doxabase.describe_query_context"
        and action.args == {"iri": dataset}
    )

    storage = db.stage_query_storage_access_repair(
        dataset_iri=dataset,
        storage_access_iri=f"{base}event_status_local_storage",
        label="Event status local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        location_kind="directory",
        storage_root=str(warehouse),
        path_templates=["events/current.csv"],
        rationale="Reviewed the local warehouse route for Event status.",
        layout_verification_status="rc:VerifiedByListingLayout",
        layout_verification_note="Directory listing confirmed the CSV path.",
    )
    assert db.check_staged_revision_apply(storage.revision_iri).status == "ready"
    db.apply_staged_revision(storage.revision_iri)

    storage_context = db.describe_query_context(dataset)
    assert "missing_storage_access" not in {
        issue.code for issue in storage_context.issues
    }
    assert [
        (group.group_name, group.issue_code)
        for group in storage_context.suggested_repair_action_groups
    ] == [("query_repair_review", "missing_physical_layout")]

    layout = db.stage_query_physical_layout_repair(
        dataset_iri=dataset,
        layout_iri=f"{base}event_status_csv_layout",
        label="Event status CSV layout",
        file_format="rc:CSV",
        rationale="Reviewed the Event status file as CSV.",
        layout_verification_status="rc:VerifiedByQueryLayout",
        layout_verification_note="A read-only aggregate confirmed the CSV layout.",
    )
    assert db.check_staged_revision_apply(layout.revision_iri).status == "ready"
    db.apply_staged_revision(layout.revision_iri)

    repaired_context = db.describe_query_context(dataset)
    assert repaired_context.readiness == "ready_for_query_planning"
    assert repaired_context.suggested_repair_action_groups == []
    assert repaired_context.query_target_decision.status == "ready"
    assert (
        repaired_context.query_target_decision.selected_candidate_direct_clean
        is True
    )
    assert {
        issue.code for issue in repaired_context.issues
    } == {"verification_status_not_recorded"}

    plan = db.draft_query_plan(dataset)
    assert plan.handoff_kind == "execution_attempt_ready"
    assert plan.scan.function == "read_csv_auto"
    assert plan.scan.uri_template == str(csv_path)
    assert plan.scan.execution_attempt_ready is True
    assert plan.review_gate.ready_for_execution_attempt is True
    assert plan.review_gate.execution_attempt_blocking_reason_codes == []

    trades_plan = db.draft_query_plan(
        "https://richcanopy.org/example/manifest/polymarket#Trades"
    )
    assert trades_plan.handoff_kind == "binding_values_required"
    assert trades_plan.scan.function == "read_parquet"
    assert trades_plan.required_bindings == ["date", "hour"]
    assert trades_plan.review_gate.binding_values_required is True
    assert trades_plan.review_gate.execution_attempt_blocking_reason_codes == [
        "binding_values_required"
    ]
    assert trades_plan.review_gate.all_issue_codes == [
        "verification_status_not_recorded"
    ]

    result = db.record_query_result(
        summary=(
            "Event status aggregate ran with a Python CSV fallback after the "
            "storage metadata repair route reached a draft query handoff."
        ),
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path=str(query_path),
        query_source_section="status aggregate",
        start_line=2,
        end_line=4,
        query_hash="sha256:event-status-storage-route",
        result_sources=[str(result_path)],
        scanned_source_paths=[str(csv_path)],
        sample_size=4,
        sample_scope="All rows in the reviewed local Event status CSV.",
        sample_method="External read-only aggregate after draft_query_plan.",
        row_count=4,
    )

    assert result.observation_type == "profile"
    assert result.query_hash == "sha256:event-status-storage-route"
    assert result.source_span_iri is not None
    assert len(result.scanned_source_span_iris) == 1
    assert [action.tool.removeprefix("doxabase.") for action in result.suggested_next_actions] == [
        "describe_resource",
        "get_context_graph",
        "describe_query_context",
    ]

    evidence = db.describe_resource(result.evidence_iri, graph="evidence")
    evidence_outgoing = {
        (triple.predicate, triple.object) for triple in evidence.outgoing
    }
    assert (RC + "queryHash", "sha256:event-status-storage-route") in evidence_outgoing
    assert (RC + "sourceSpan", result.source_span_iri) in evidence_outgoing
    assert (
        RC + "sourceSpan",
        result.scanned_source_span_iris[0],
    ) in evidence_outgoing

    query_span = db.describe_resource(result.source_span_iri, graph="evidence")
    query_span_outgoing = {
        (triple.predicate, triple.object) for triple in query_span.outgoing
    }
    assert (RC + "sourcePath", str(query_path)) in query_span_outgoing
    assert (RC + "sourceSection", "status aggregate") in query_span_outgoing
    assert (RC + "startLine", "2") in query_span_outgoing
    assert (RC + "endLine", "4") in query_span_outgoing
    assert (RC + "sourceKind", RC + "QuerySource") in query_span_outgoing

    scanned_span = db.describe_resource(
        result.scanned_source_span_iris[0],
        graph="evidence",
    )
    scanned_span_outgoing = {
        (triple.predicate, triple.object) for triple in scanned_span.outgoing
    }
    assert (RC + "sourcePath", str(csv_path)) in scanned_span_outgoing
    assert (RC + "sourceKind", RC + "DataSampleSource") in scanned_span_outgoing

    evidence_slice = db.get_context_graph(
        **result.suggested_next_actions[1].args,
        max_triples=120,
    )
    assert result.evidence_iri in {
        resource.iri for resource in evidence_slice.resources
    }
    assert db.validate_graph(scope="all").conforms


def test_draft_query_plan_blocks_ambiguous_physical_layout_scan(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    storage = db.record_map_storage_access(
        "https://example.test/project#events_local_storage",
        label="Events local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="directory",
        storage_root=str(tmp_path / "warehouse"),
        path_templates=["events/current/*.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    csv_layout = db.record_map_physical_layout(
        "https://example.test/project#events_csv_layout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    parquet_layout = db.record_map_physical_layout(
        "https://example.test/project#events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Events",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[csv_layout.iri, parquet_layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "needs_review"
    issue = next(
        issue
        for issue in context.issues
        if issue.code == "ambiguous_physical_layout"
    )
    assert issue.severity == "warning"
    assert issue.resource is not None
    assert issue.resource.iri == dataset
    assert issue.details is not None
    assert issue.details["distinct_layout_signature_count"] == 2
    target = context.query_target_candidates[0]
    assert target.candidate_path_status == "orientation_only"
    assert target.direct_review_required is True
    assert [reason.code for reason in target.direct_review_reasons] == [
        "ambiguous_physical_layout"
    ]
    selection_actions = [
        action
        for action in context.suggested_next_actions
        if action.tool == "doxabase.draft_query_plan"
        and "physical_layout_iri" in action.args
    ]
    assert [action.args for action in selection_actions] == [
        {
            "iri": dataset,
            "candidate_selector": target.candidate_selector,
            "physical_layout_iri": parquet_layout.iri,
        },
    ]
    assert "file format rc:Parquet" in selection_actions[0].reason

    plan = db.draft_query_plan(dataset)

    assert plan.scan.file_format is None
    assert plan.scan.compression is None
    assert plan.scan.function is None
    assert plan.scan.physical_layout is None
    assert "No unambiguous physical layout" in (
        plan.scan.physical_layout_selection_note or ""
    )
    assert plan.review_gate.ready_for_execution_attempt is False
    assert plan.review_gate.blocking_reason_codes == ["ambiguous_physical_layout"]
    assert plan.handoff_kind == "metadata_review_required"

    selected_plan = db.draft_query_plan(
        dataset,
        physical_layout_iri=parquet_layout.iri,
    )

    assert selected_plan.source_context.requested_physical_layout_iri == (
        parquet_layout.iri
    )
    assert selected_plan.selected_candidate is not None
    assert selected_plan.selected_candidate.candidate_path_status == "ready"
    assert selected_plan.selected_candidate.direct_review_required is False
    assert selected_plan.scan.physical_layout is not None
    assert selected_plan.scan.physical_layout.iri == parquet_layout.iri
    assert selected_plan.scan.physical_layout_selection_note == (
        "Caller selected this physical layout for the draft query plan."
    )
    assert selected_plan.scan.file_format == "Parquet"
    assert selected_plan.scan.function == "read_parquet"
    assert "ambiguous_physical_layout" not in (
        selected_plan.review_gate.blocking_reason_codes
    )
    assert "ambiguous_physical_layout" not in selected_plan.review_gate.all_issue_codes
    assert selected_plan.review_gate.ready_for_execution_attempt is True
    assert selected_plan.handoff_kind == "execution_attempt_ready"
    assert selected_plan.issues == []

    with pytest.raises(DoxaBaseError, match="physical_layout_iri did not match"):
        db.draft_query_plan(
            dataset,
            physical_layout_iri="https://example.test/project#missing_layout",
        )


def test_database_relation_repair_hint_prioritizes_remove_when_relation_exists(
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
    issue = next(
        issue
        for issue in context.issues
        if issue.code == "database_relation_template_source_mismatch"
    )
    assert issue.details is not None
    repair_hint = issue.details["repair_hint"]

    assert repair_hint["candidate_relation_identifier"][
        "already_on_storage_access"
    ] is True
    assert [action["action_type"] for action in repair_hint["actions"]] == [
        "remove_misplaced_source_template",
        "add_reviewed_relation_template",
    ]
    assert repair_hint["actions"][0]["args"] == {
        "subject": dataset,
        "predicate": "rc:pathTemplate",
        "object": relation,
        "object_kind": "literal",
        "change_kind": "remove",
        "graph": "map",
    }
    assert repair_hint["actions"][1]["action_status"] == "already_satisfied"
    assert repair_hint["actions"][1]["skip_when_already_satisfied"] is True
    assert "remove_misplaced_source_template" in repair_hint["actions"][1][
        "condition"
    ]
    repair_group = context.suggested_repair_action_groups[0]
    assert repair_group.issue_code == "database_relation_template_source_mismatch"
    assert repair_group.action_status_counts == {
        "pending_review": 1,
        "already_satisfied": 1,
    }
    assert repair_group.pending_action_count == 1
    assert repair_group.skippable_action_count == 1
    assert repair_group.already_satisfied_action_count == 1
    assert repair_group.pending_required_extra_arguments == ["rationale"]


def test_describe_dataset_handles_blank_node_physical_layout(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    description = db.describe_dataset(
        "https://richcanopy.org/example/manifest/ais#DailyIndex"
    )

    assert len(description.physical_layouts) == 1
    layout = description.physical_layouts[0]
    assert layout.iri
    assert layout.file_format is not None
    assert layout.file_format.label == "Parquet"
    assert layout.compression_codec is not None
    assert layout.compression_codec.label == "zstd"


def test_context_slice_column_seed_suggests_query_context_for_owner_repairs(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    column = "https://example.test/project#events__event_type"
    dataset_template = "events/current/*.parquet"
    storage = db.record_map_storage_access(
        "https://example.test/project#events_database_storage",
        label="Events database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="analytics-prod",
        endpoint_profile="warehouse-prod",
        credential_reference="profile:warehouse-readonly",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#events_table_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Events",
        is_table=True,
        path_templates=[dataset_template],
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_column(
        column,
        table_iri=dataset,
        column_name="event_type",
        physical_type="rc:Varchar",
    )

    for profile in ("dataset_brief", "deep_lore"):
        context_slice = db.get_context_graph(column, profile=profile)

        assert context_slice.dataset_contexts[0].iri == dataset
        assert context_slice.route_counts["seed_column"] == 1
        assert context_slice.route_counts["related_dataset"] == 1
        query_actions = [
            action
            for action in context_slice.suggested_next_actions
            if action.tool == "doxabase.describe_query_context"
        ]
        assert len(query_actions) == 1
        action = query_actions[0]
        assert action.args == {"iri": dataset}
        assert "database_relation_template_source_mismatch" in action.reason
        assert "repair hints" in action.reason

        query_context = db.describe_query_context(**action.args)
        assert query_context.suggested_repair_action_groups[0].issue_code == (
            "database_relation_template_source_mismatch"
        )

