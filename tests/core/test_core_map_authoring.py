"""Split from test_doxabase_core.py (distillation Phase 2); tests verbatim."""

from tests.core.support_core import *  # noqa: F401,F403


def test_import_handoff_bundle_resolves_moved_absolute_artifacts_next_to_manifest(
    tmp_path: Path,
) -> None:
    source = DoxaBase.create(tmp_path / "source.sqlite")
    staged = source.stage_graph_revision(
        summary="Stage shipment table",
        rationale="Create a portable handoff manifest regression fixture.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Shipments a rc:Dataset, rc:Table .
                """,
            }
        ],
    )
    trig_path = tmp_path / "project-handoff.trig"
    snapshot_path = tmp_path / "revision-snapshots.json"
    manifest_path = tmp_path / "handoff-manifest.json"
    source.export_handoff_bundle(
        trig_path,
        snapshot_path,
        manifest_path=manifest_path,
        revision_iris=[staged.revision_iri],
        fail_on_sensitive=True,
    )

    portable_dir = tmp_path / "portable"
    portable_dir.mkdir()
    portable_trig = portable_dir / trig_path.name
    portable_snapshot = portable_dir / snapshot_path.name
    portable_trig.write_bytes(trig_path.read_bytes())
    portable_snapshot.write_bytes(snapshot_path.read_bytes())
    portable_manifest = portable_dir / manifest_path.name
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    stale_root = Path("/source-machine/doxabase-run")
    manifest["artifacts"]["trig"]["path"] = str(stale_root / trig_path.name)
    manifest["artifacts"]["revision_snapshots"]["path"] = str(
        stale_root / snapshot_path.name
    )
    manifest["recommended_import_sequence"][0]["path"] = str(
        stale_root / trig_path.name
    )
    manifest["recommended_import_sequence"][1]["path"] = str(
        stale_root / snapshot_path.name
    )
    portable_manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    receiver = DoxaBase.create(tmp_path / "receiver.sqlite")
    imported = receiver.import_handoff_bundle(portable_manifest)

    assert imported.paths["trig"] == str(portable_trig)
    assert imported.paths["revision_snapshots"] == str(portable_snapshot)
    assert {
        row.revision_iri: row.status for row in imported.post_import_snapshot_evidence
    } == {staged.revision_iri: "history_plus_snapshot_rows"}


def test_staged_revision_impacts_surface_lore_for_caveat_and_type_changes(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(
        """
        @prefix dcterms: <http://purl.org/dc/terms/> .
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rcg: <https://richcanopy.org/graph/> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        rcg:map {
            ex:PriceSnapshots a rc:Dataset, rc:Table ;
                rdfs:label "Price snapshots" ;
                rc:hasColumn ex:px_price ;
                rc:hasKnownCaveat ex:mixed_price_payload_caveat .

            ex:px_price a rc:Column ;
                rc:columnName "price" ;
                rc:physicalType rc:Varchar ;
                rc:nullable true ;
                rdfs:comment "Raw payload column: usually numeric strings, sometimes API error objects." .

            ex:mixed_price_payload_caveat a rc:KnownCaveat ;
                rdfs:label "Mixed price payload caveat" ;
                rc:caveatDescription "price may contain numeric strings or API error objects." ;
                rc:impact "Probability analysis must parse and filter raw payloads first." ;
                rc:severity rc:Moderate .
        }

        rcg:observations {
            ex:obs_price_payloads a rc:Observation ;
                rc:summary "Sample price payloads include API error objects." ;
                rc:observedAt "2026-06-14T00:00:00Z"^^xsd:dateTime ;
                rc:observedAsset ex:PriceSnapshots ;
                rc:observedColumn ex:px_price ;
                rc:observationStatus rc:Checked ;
                rc:evidence ex:evidence_price_payloads ;
                rc:hasClaim ex:claim_price_payloads_are_mixed .

            ex:claim_price_payloads_are_mixed a rc:Claim ;
                rc:claimKind rc:CaveatClaim ;
                rc:claimText "The price column is a raw payload lane before probability coercion." ;
                rc:claimTarget ex:px_price, ex:mixed_price_payload_caveat ;
                rc:confidence rc:HighConfidence ;
                rc:observationStatus rc:Checked ;
                rc:evidence ex:evidence_price_payloads .
        }

        rcg:patterns {
            ex:pattern_price_payload_boundary a rc:Pattern ;
                rc:summary "Raw price payloads need a coercion boundary." ;
                rc:patternText "The price column should not be treated as clean probability until parsing filters API errors." ;
                rc:rationale "The observation and claim explain why the caveat exists." ;
                rc:patternTarget ex:px_price ;
                rc:supportingObservation ex:obs_price_payloads ;
                rc:supportingClaim ex:claim_price_payloads_are_mixed ;
                rc:evidence ex:evidence_price_payloads ;
                rc:confidence rc:HighConfidence ;
                rc:patternStability rc:RepeatedPattern ;
                rc:mapImplication ex:mixed_price_payload_caveat .
        }

        rcg:evidence {
            ex:evidence_price_payloads a rc:Evidence ;
                rc:summary "Profile sample of price payload variants." ;
                dcterms:source "test://price-payload-profile" .
        }
        """
    )

    staged = db.stage_graph_revision(
        summary="Try clean price probability shortcut",
        rationale=(
            "This is intentionally tempting: make price easy for analysis while "
            "checking whether the review bundle shows what would be lost."
        ),
        removals=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:PriceSnapshots rc:hasKnownCaveat ex:mixed_price_payload_caveat .
                    ex:px_price rc:physicalType rc:Varchar ;
                        rc:nullable true ;
                        rdfs:comment "Raw payload column: usually numeric strings, sometimes API error objects." .
                """,
            }
        ],
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:px_price rc:physicalType rc:Double ;
                        rc:valueType ex:Probability ;
                        rc:nullable false .
                """,
            }
        ],
        validation_scope="all",
    )

    description = db.describe_staged_revision(staged.revision_iri)
    impact_types = {impact.impact_type for impact in description.impacts}
    assert "removed_caveat" in impact_types
    assert "changed_physical_type" in impact_types
    assert "changed_value_type" in impact_types
    assert "changed_nullable" in impact_types
    assert "changed_documentation" in impact_types

    caveat_impact = next(
        impact
        for impact in description.impacts
        if impact.impact_type == "removed_caveat"
    )
    assert caveat_impact.subject is not None
    assert caveat_impact.subject.iri == "https://example.test/project#PriceSnapshots"
    removed_caveat = caveat_impact.removed_values[0]
    assert removed_caveat.value_label == "Mixed price payload caveat"
    assert removed_caveat.caveat is not None
    assert removed_caveat.caveat.description == (
        "price may contain numeric strings or API error objects."
    )
    assert removed_caveat.caveat.impact == (
        "Probability analysis must parse and filter raw payloads first."
    )
    assert removed_caveat.caveat.severity is not None
    assert removed_caveat.caveat.severity.iri == RC + "Moderate"
    assert {item.iri for item in caveat_impact.related_observations} == {
        "https://example.test/project#obs_price_payloads"
    }
    assert {item.iri for item in caveat_impact.related_claims} == {
        "https://example.test/project#claim_price_payloads_are_mixed"
    }
    assert {item.iri for item in caveat_impact.related_patterns} == {
        "https://example.test/project#pattern_price_payload_boundary"
    }
    assert {item.iri for item in caveat_impact.related_evidence} == {
        "https://example.test/project#evidence_price_payloads"
    }

    type_impact = next(
        impact
        for impact in description.impacts
        if impact.impact_type == "changed_physical_type"
    )
    assert type_impact.subject is not None
    assert type_impact.subject.label == "price"
    assert "Raw payload column" not in type_impact.message
    assert [value.value for value in type_impact.removed_values] == [RC + "Varchar"]
    assert [value.value for value in type_impact.added_values] == [RC + "Double"]
    assert type_impact.related_observations[0].iri == (
        "https://example.test/project#obs_price_payloads"
    )

    nullable_impact = next(
        impact
        for impact in description.impacts
        if impact.impact_type == "changed_nullable"
    )
    assert [value.value for value in nullable_impact.removed_values] == ["true"]
    assert [value.value for value in nullable_impact.added_values] == ["false"]

    documentation_impact = next(
        impact
        for impact in description.impacts
        if impact.impact_type == "changed_documentation"
    )
    assert documentation_impact.added_values == []
    assert "API error objects" in documentation_impact.removed_values[0].value

    export_path = tmp_path / "price-shortcut-review.md"
    db.export_staged_revision(staged.revision_iri, export_path)
    export_text = export_path.read_text()
    assert "## Impact Review" in export_text
    assert "Removes known caveat Mixed price payload caveat" in export_text
    assert "Probability analysis must parse and filter raw payloads first." in export_text
    assert "Raw price payloads need a coercion boundary" in export_text


def test_describe_assertion_support_explains_map_assertion_lore(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(
        """
        @prefix dcterms: <http://purl.org/dc/terms/> .
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rcg: <https://richcanopy.org/graph/> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        rcg:map {
            ex:PriceSnapshots a rc:Dataset, rc:Table ;
                rdfs:label "Price snapshots" ;
                rc:hasColumn ex:px_price ;
                rc:rowCountSnapshot 12 ;
                rc:hasKnownCaveat ex:mixed_price_payload_caveat .

            ex:px_price a rc:Column ;
                rc:columnName "price" ;
                rc:physicalType rc:Varchar ;
                rc:nullable true ;
                rdfs:comment "Raw payload column." .

            ex:mixed_price_payload_caveat a rc:KnownCaveat ;
                rdfs:label "Mixed price payload caveat" ;
                rc:caveatDescription "price may contain numeric strings or API error objects." ;
                rc:impact "Probability analysis must parse and filter raw payloads first." ;
                rc:severity rc:Moderate .

            ex:DailyIndex a rc:Dataset, rc:Table ;
                rdfs:label "Daily index" ;
                rc:partitionedBy ex:daily_date_partition ;
                rc:layoutVerificationStatus rc:UnverifiedLayout ;
                rc:layoutVerificationNote "Index layout has not been checked against storage." .

            ex:daily_date_partition a rc:PartitionScheme ;
                rc:pathTemplate "index/{year}/ais-{date}.parquet" ;
                rc:layoutVerificationStatus rc:GeneratedFromManifestLayout ;
                rc:layoutVerificationNote "Partition path was generated from manifest metadata." .
        }

        rcg:observations {
            ex:obs_price_payloads a rc:Observation ;
                rc:summary "Sample price payloads include API error objects." ;
                rc:observedAt "2026-06-14T00:00:00Z"^^xsd:dateTime ;
                rc:observedAsset ex:PriceSnapshots ;
                rc:observedColumn ex:px_price ;
                rc:observationStatus rc:Checked ;
                rc:evidence ex:evidence_price_payloads ;
                rc:hasClaim ex:claim_price_payloads_are_mixed .

            ex:claim_price_payloads_are_mixed a rc:Claim ;
                rc:claimKind rc:CaveatClaim ;
                rc:claimText "The price column is a raw payload lane before probability coercion." ;
                rc:claimTarget ex:px_price, ex:mixed_price_payload_caveat ;
                rc:confidence rc:HighConfidence ;
                rc:observationStatus rc:Checked ;
                rc:evidence ex:evidence_price_payloads .
        }

        rcg:patterns {
            ex:pattern_price_payload_boundary a rc:Pattern ;
                rc:summary "Raw price payloads need a coercion boundary." ;
                rc:patternText "The price column should not be treated as clean probability until parsing filters API errors." ;
                rc:patternTarget ex:px_price ;
                rc:supportingObservation ex:obs_price_payloads ;
                rc:supportingClaim ex:claim_price_payloads_are_mixed ;
                rc:evidence ex:evidence_price_payloads ;
                rc:mapImplication ex:mixed_price_payload_caveat .
        }

        rcg:evidence {
            ex:evidence_price_payloads a rc:Evidence ;
                rc:summary "Profile sample of price payload variants." ;
                dcterms:source "test://price-payload-profile" .
        }
        """
    )

    caveat_support = db.describe_assertion_support(
        "https://example.test/project#PriceSnapshots",
        "rc:hasKnownCaveat",
        "https://example.test/project#mixed_price_payload_caveat",
    )

    assert caveat_support.assertion_present is True
    assert caveat_support.matching_triples[0].object_label == "Mixed price payload caveat"
    assert caveat_support.requested_object is not None
    assert caveat_support.requested_object.caveat is not None
    assert caveat_support.requested_object.caveat.impact == (
        "Probability analysis must parse and filter raw payloads first."
    )
    assert {item.iri for item in caveat_support.related_observations} == {
        "https://example.test/project#obs_price_payloads"
    }
    assert {item.iri for item in caveat_support.related_claims} == {
        "https://example.test/project#claim_price_payloads_are_mixed"
    }
    assert {item.iri for item in caveat_support.related_patterns} == {
        "https://example.test/project#pattern_price_payload_boundary"
    }
    assert {item.iri for item in caveat_support.related_evidence} == {
        "https://example.test/project#evidence_price_payloads"
    }
    caveat_routes = {
        (route.resource.iri, route.resource_kind, route.route_type)
        for route in caveat_support.related_routes
    }
    assert (
        "https://example.test/project#obs_price_payloads",
        "observation",
        "observed_asset",
    ) in caveat_routes
    assert (
        "https://example.test/project#claim_price_payloads_are_mixed",
        "claim",
        "claim_target",
    ) in caveat_routes
    assert (
        "https://example.test/project#pattern_price_payload_boundary",
        "pattern",
        "supporting_observation",
    ) in caveat_routes
    assert (
        "https://example.test/project#pattern_price_payload_boundary",
        "pattern",
        "map_implication",
    ) in caveat_routes
    caveat_route_summaries = {
        summary.resource.iri: summary
        for summary in caveat_support.related_route_summaries
    }
    pattern_summary = caveat_route_summaries[
        "https://example.test/project#pattern_price_payload_boundary"
    ]
    assert pattern_summary.rank >= 1
    assert pattern_summary.resource_kind == "pattern"
    assert pattern_summary.route_count == 3
    assert pattern_summary.strongest_route_type == "map_implication"
    assert pattern_summary.route_types == [
        "map_implication",
        "supporting_observation",
        "supporting_claim",
    ]
    assert "pattern map implication" in pattern_summary.route_labels
    assert "Mixed price payload caveat" in pattern_summary.route_note
    assert [item.iri for item in caveat_support.nearby_caveats] == [
        "https://example.test/project#mixed_price_payload_caveat"
    ]
    caveat_link_routes = {
        (
            link.caveat.iri,
            link.scope,
            link.route_type,
            link.via_resource.iri,
            link.matched_resource.iri,
        )
        for link in caveat_support.nearby_caveat_links
    }
    assert (
        "https://example.test/project#mixed_price_payload_caveat",
        "target_resource",
        "caveat_target_resource",
        "https://example.test/project#mixed_price_payload_caveat",
        "https://example.test/project#mixed_price_payload_caveat",
    ) in caveat_link_routes
    assert (
        "https://example.test/project#mixed_price_payload_caveat",
        "direct_target",
        "target_has_known_caveat",
        "https://example.test/project#PriceSnapshots",
        "https://example.test/project#PriceSnapshots",
    ) in caveat_link_routes

    column_support = db.describe_assertion_support(
        "https://example.test/project#px_price",
        "rc:physicalType",
        "rc:Varchar",
    )

    assert column_support.assertion_present is True
    assert column_support.subject.label == "price"
    assert column_support.owner_dataset is not None
    assert column_support.owner_dataset.iri == "https://example.test/project#PriceSnapshots"
    assert column_support.absence_note is None
    assert column_support.requested_object is not None
    assert column_support.requested_object.value == RC + "Varchar"
    assert {item.iri for item in column_support.nearby_caveats} == {
        "https://example.test/project#mixed_price_payload_caveat"
    }
    column_caveat_link = column_support.nearby_caveat_links[0]
    assert column_caveat_link.scope == "owner_dataset"
    assert column_caveat_link.route_type == "owner_dataset_has_known_caveat"
    assert column_caveat_link.via_resource.iri == (
        "https://example.test/project#PriceSnapshots"
    )
    assert column_caveat_link.matched_resource.iri == (
        "https://example.test/project#px_price"
    )
    assert [triple.object for triple in column_support.same_subject_predicate_triples] == [
        RC + "Varchar"
    ]
    assert column_support.suggested_next_actions[0].tool == (
        "doxabase.get_context_graph"
    )
    assert column_support.suggested_next_actions[0].tool == (
        "doxabase.get_context_graph"
    )
    assert column_support.suggested_next_actions[0].args["seed_iris"][0] == (
        "https://example.test/project#PriceSnapshots"
    )
    assert any(
        action.tool == "doxabase.describe_dataset"
        and action.args["iri"] == "https://example.test/project#PriceSnapshots"
        for action in column_support.suggested_next_actions
    )

    absent_support = db.describe_assertion_support(
        "https://example.test/project#px_price",
        "rc:physicalType",
        "rc:Double",
    )

    assert absent_support.assertion_present is False
    assert absent_support.matching_triples == []
    assert [triple.object for triple in absent_support.same_subject_predicate_triples] == [
        RC + "Varchar"
    ]
    assert absent_support.owner_dataset is not None
    assert absent_support.owner_dataset.label == "Price snapshots"
    assert absent_support.absence_note is not None
    assert "Current same-subject/predicate value(s): VARCHAR" in (
        absent_support.absence_note
    )
    assert {item.iri for item in absent_support.nearby_caveats} == {
        "https://example.test/project#mixed_price_payload_caveat"
    }
    absent_routes = {
        (route.resource.iri, route.resource_kind, route.route_type)
        for route in absent_support.related_routes
    }
    assert (
        "https://example.test/project#claim_price_payloads_are_mixed",
        "claim",
        "claim_target",
    ) in absent_routes
    assert (
        "https://example.test/project#pattern_price_payload_boundary",
        "pattern",
        "pattern_target",
    ) in absent_routes
    assert "owning dataset" in absent_support.support_scope_note
    assert any(
        action.tool == "doxabase.describe_assertion_support"
        and action.args["object"] is None
        for action in absent_support.suggested_next_actions
    )

    partition_support = db.describe_assertion_support(
        "https://example.test/project#DailyIndex",
        "rc:partitionedBy",
        "https://example.test/project#daily_date_partition",
    )

    context_values = {
        triple.object_label or triple.object
        for triple in partition_support.nearby_context_triples
    }
    assert partition_support.assertion_present is True
    assert "unverified layout" in context_values
    assert "generated from manifest" in context_values
    assert "Index layout has not been checked against storage." in context_values
    assert "Partition path was generated from manifest metadata." in context_values
    assert "index/{year}/ais-{date}.parquet" in context_values
    assert "No linked lore" not in partition_support.context_note
    assert "No related observations, claims, patterns, evidence, or revisions" in (
        partition_support.context_note
    )

    row_count_support = db.describe_assertion_support(
        "https://example.test/project#PriceSnapshots",
        "rc:rowCountSnapshot",
        "12",
        object_kind="literal",
    )
    assert row_count_support.assertion_present is True
    assert row_count_support.matching_triples[0].object == "12"
    assert row_count_support.matching_triples[0].object_datatype == str(XSD.integer)

    nullable_support = db.describe_assertion_support(
        "https://example.test/project#px_price",
        "rc:nullable",
        "true",
        object_kind="literal",
    )
    assert nullable_support.assertion_present is True
    assert nullable_support.matching_triples[0].object == "true"
    assert nullable_support.matching_triples[0].object_datatype == str(XSD.boolean)


def test_stage_map_assertion_change_packages_support_context(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(
        """
        @prefix dcterms: <http://purl.org/dc/terms/> .
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rcg: <https://richcanopy.org/graph/> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        rcg:ontology {
            ex:RawPricePayload a rc:ValueType ;
                rdfs:label "Raw price payload" ;
                rdfs:comment "Raw API payload before parsing invalid rows." ;
                rc:requiredPhysicalType rc:Varchar .

            ex:CleanProbability a rc:ValueType ;
                rdfs:label "Clean probability" ;
                rdfs:comment "Parsed numeric probability value." ;
                rc:requiredPhysicalType rc:Double .
        }

        rcg:map {
            ex:PriceSnapshots a rc:Dataset, rc:Table ;
                rdfs:label "Price snapshots" ;
                rc:hasColumn ex:px_price ;
                rc:hasKnownCaveat ex:mixed_price_payload_caveat .

            ex:px_price a rc:Column ;
                rc:columnName "price" ;
                rc:physicalType rc:Varchar ;
                rc:valueType ex:RawPricePayload ;
                rc:nullable true ;
                rdfs:comment "Raw payload lane." .

            ex:mixed_price_payload_caveat a rc:KnownCaveat ;
                rdfs:label "Mixed price payload caveat" ;
                rc:caveatDescription "price may contain API error objects." ;
                rc:impact "Parse payloads before probability analysis." ;
                rc:severity rc:Moderate .
        }

        rcg:observations {
            ex:obs_price_payloads a rc:Observation ;
                rc:summary "Sample price payloads include API error objects." ;
                rc:observedAt "2026-06-14T00:00:00Z"^^xsd:dateTime ;
                rc:observedColumn ex:px_price ;
                rc:observationStatus rc:Checked ;
                rc:evidence ex:evidence_price_payloads ;
                rc:hasClaim ex:claim_price_payloads_are_mixed .

            ex:claim_price_payloads_are_mixed a rc:Claim ;
                rc:claimKind rc:CaveatClaim ;
                rc:claimText "The price column is a raw payload lane." ;
                rc:claimTarget ex:px_price, ex:mixed_price_payload_caveat ;
                rc:confidence rc:HighConfidence ;
                rc:observationStatus rc:Checked ;
                rc:evidence ex:evidence_price_payloads .
        }

        rcg:patterns {
            ex:pattern_price_payload_boundary a rc:Pattern ;
                rc:summary "Raw price payloads need a coercion boundary." ;
                rc:patternText "Do not treat price as clean probability before parsing." ;
                rc:rationale "The current raw lane caveat is supported by the sample observation and claim." ;
                rc:patternTarget ex:px_price ;
                rc:supportingObservation ex:obs_price_payloads ;
                rc:supportingClaim ex:claim_price_payloads_are_mixed ;
                rc:evidence ex:evidence_price_payloads .
        }

        rcg:evidence {
            ex:evidence_price_payloads a rc:Evidence ;
                rc:summary "Profile sample of price payload variants." ;
                dcterms:source "test://price-payload-profile" .
        }
        """
    )
    before_map_count = db.triple_count("map")
    before_history_count = db.triple_count("history")
    change_arguments = {
        "subject": "https://example.test/project#px_price",
        "predicate": "rc:physicalType",
        "object": "rc:Double",
        "change_kind": "replace",
        "rationale": (
            "Testing a tempting but risky coercion so the review bundle should "
            "make the existing VARCHAR and attached lore visible."
        ),
        "review_note": "This is deliberately staged for review, not applied.",
    }

    draft_change = db.draft_map_assertion_change(**change_arguments)

    assert draft_change.result_kind == "draft_map_assertion_change"
    assert draft_change.change_kind == "replace"
    assert draft_change.assertion_present_before is False
    assert [triple.object for triple in draft_change.current_values_before] == [
        RC + "Varchar"
    ]
    assert draft_change.changed_graphs == ["map"]
    assert [patch.operation for patch in draft_change.patches] == [
        RC + "AdditionPatch",
        RC + "RemovalPatch",
    ]
    assert len(draft_change.additions) == 1
    assert len(draft_change.removals) == 1
    assert draft_change.validation_conforms is True
    assert draft_change.validation_result_count == 0
    assert any(
        impact.impact_type == "changed_physical_type"
        for impact in draft_change.impacts
    )
    assert draft_change.judgement_panel.semantic_risk_level == "high"
    assert [action.tool.removeprefix("doxabase.") for action in draft_change.suggested_next_actions] == [
        "describe_assertion_support",
        "stage_map_assertion_change",
    ]
    assert "high-risk" in draft_change.suggested_next_actions[0].reason
    assert draft_change.stage_arguments["rationale"].startswith(
        "Testing a tempting but risky coercion"
    )
    assert db.triple_count("history") == before_history_count

    staged_change = db.stage_map_assertion_change(**change_arguments)

    assert staged_change.change_kind == "replace"
    assert staged_change.assertion_present_before is False
    assert [triple.object for triple in staged_change.current_values_before] == [
        RC + "Varchar"
    ]
    assert len(staged_change.additions) == 1
    assert len(staged_change.removals) == 1
    assert "Double" in staged_change.additions[0]["content"]
    assert "Varchar" in staged_change.removals[0]["content"]
    assert staged_change.assertion_support.absence_note is not None
    assert "Current same-subject/predicate value(s): VARCHAR" in (
        staged_change.assertion_support.absence_note
    )
    assert "Nearby caveats by scope" in staged_change.review_note
    assert "Related route summaries" in staged_change.review_note
    assert "Value-type context" in staged_change.review_note
    assert "Why current value may be intentional" in staged_change.review_note
    assert "This is deliberately staged for review" in staged_change.review_note
    panel = staged_change.judgement_panel
    assert panel.assertion_present_before is False
    assert "VARCHAR" in panel.headline
    assert "DOUBLE" in panel.headline
    assert [value.label for value in panel.current_values] == ["VARCHAR"]
    assert panel.proposed_value is not None
    assert panel.proposed_value.label == "DOUBLE"
    assert panel.absence_note is not None
    assert panel.semantic_risk_level == "high"
    assert any(
        "current value may be intentional" in reason
        for reason in panel.semantic_risk_reasons
    )
    assert "Current same-subject/predicate value(s): VARCHAR" in panel.absence_note
    assert len(panel.value_type_context) == 1
    value_type_context = panel.value_type_context[0]
    assert value_type_context.value_type.iri == (
        "https://example.test/project#RawPricePayload"
    )
    assert value_type_context.required_physical_type is not None
    assert value_type_context.required_physical_type.label == "VARCHAR"
    assert value_type_context.current_physical_type_matches is True
    assert value_type_context.proposed_physical_type_matches is False
    assert any(
        "Raw price payload requires physical type VARCHAR" in note
        for note in panel.why_current_value_may_be_intentional
    )
    assert {caveat.scope for caveat in panel.caveats} == {"owner_dataset"}
    assert panel.caveats[0].caveat_label == "Mixed price payload caveat"
    assert any(
        route.resource_iri
        == "https://example.test/project#pattern_price_payload_boundary"
        for route in panel.strongest_routes
    )
    assert any(
        impact.impact_type == "changed_physical_type" for impact in panel.impacts
    )
    assert any(
        "exact requested assertion was absent" in note
        for note in panel.safety_notes
    )
    assert any("owning dataset" in note for note in panel.safety_notes)
    assert staged_change.additions == draft_change.additions
    assert staged_change.removals == draft_change.removals
    assert db.triple_count("map") == before_map_count
    assert db.triple_count("history") > before_history_count

    description = db.describe_staged_revision(
        staged_change.staged_revision.revision_iri
    )
    assert description.judgement_panel is not None
    assert description.stored_review_context is None
    assert description.judgement_panel.proposed_value is not None
    assert description.judgement_panel.proposed_value.label == "DOUBLE"
    assert description.judgement_panel.value_type_context
    assert description.judgement_panel.value_type_context[0].note.startswith(
        "Value type Raw price payload requires physical type VARCHAR"
    )
    assert [patch.operation for patch in description.patches] == [
        RC + "AdditionPatch",
        RC + "RemovalPatch",
    ]
    assert {item.iri for item in description.supporting_observations} == {
        "https://example.test/project#obs_price_payloads"
    }
    assert {item.iri for item in description.supporting_claims} == {
        "https://example.test/project#claim_price_payloads_are_mixed"
    }
    assert {item.iri for item in description.supporting_patterns} == {
        "https://example.test/project#pattern_price_payload_boundary"
    }
    assert {item.iri for item in description.evidence} == {
        "https://example.test/project#evidence_price_payloads"
    }
    assert {
        "https://example.test/project#px_price",
        "https://example.test/project#mixed_price_payload_caveat",
    }.issubset({item.iri for item in description.revision_anchors})
    assert RC + "Varchar" not in {
        item.iri for item in description.revision_anchors
    }
    assert RC + "Double" not in {item.iri for item in description.revision_anchors}
    assert any(
        impact.impact_type == "changed_physical_type"
        for impact in description.impacts
    )
    check = db.check_staged_revision_apply(
        staged_change.staged_revision.revision_iri
    )
    assert check.can_apply is True
    assert check.status == "ready"
    assert check.semantic_risk_level == "high"
    assert check.semantic_risk_reasons == panel.semantic_risk_reasons
    assert check.suggested_next_actions[-1].tool == "doxabase.apply_staged_revision"
    assert "semantic review" in check.suggested_next_actions[-1].reason
    export_path = tmp_path / "price-change-review.md"
    db.export_staged_revision(staged_change.staged_revision.revision_iri, export_path)
    exported = export_path.read_text()
    assert exported.index("## Semantic Review Warning") < exported.index(
        "## Current Apply Check"
    )
    assert "- Semantic risk: high" in exported
    assert "## Judgement Panel" in exported
    assert "### Value Type Context" in exported
    assert "Raw price payload" in exported
    assert "Current matches" in exported
    assert "Proposed matches" in exported
    assert "Why Current Value May Be Intentional" in exported

    grouped_export = db.export_staged_revisions(
        [staged_change.staged_revision.revision_iri],
        tmp_path / "price-change-grouped-review.md",
    )
    assert grouped_export.bundle_summary.semantic_risk_queue_counts == {
        "apply_after_review": 1
    }
    assert grouped_export.bundle_summary.semantic_review_required_queue_counts == {}
    assert grouped_export.revision_summaries[0].semantic_risk_level == "high"
    grouped_queue_item = grouped_export.bundle_summary.next_action_queue_items[0]
    assert grouped_queue_item.semantic_risk_level == "high"
    assert grouped_queue_item.semantic_risk_reasons == panel.semantic_risk_reasons
    listed = db.list_graph_revisions(
        include_apply_checks=True,
        current_staged_work_only=True,
    )
    listed_row = next(
        row
        for row in listed.revisions
        if row.iri == staged_change.staged_revision.revision_iri
    )
    assert listed_row.application_semantic_risk_level == "high"
    assert listed_row.application_semantic_risk_reasons == panel.semantic_risk_reasons
    listed_queue_item = next(
        item
        for item in listed.next_action_queue_items
        if item.row_iri == staged_change.staged_revision.revision_iri
    )
    assert listed_queue_item.semantic_risk_level == "high"
    assert listed_queue_item.semantic_risk_reasons == panel.semantic_risk_reasons
    resource_revisions = db.list_resource_revisions(
        "https://example.test/project#px_price",
        include_apply_checks=True,
        current_staged_work_only=True,
    )
    resource_queue_item = next(
        item
        for item in resource_revisions.next_action_queue_items
        if item.row_iri == staged_change.staged_revision.revision_iri
    )
    assert resource_queue_item.semantic_risk_level == "high"
    recovery = db.plan_staged_revision_recovery(
        [staged_change.staged_revision.revision_iri]
    )
    recovery_queue_item = recovery.next_action_queue_items[0]
    assert recovery_queue_item.semantic_risk_level == "high"
    assert recovery_queue_item.semantic_risk_reasons == panel.semantic_risk_reasons

    value_type_change = db.stage_map_assertion_change(
        subject="https://example.test/project#px_price",
        predicate="rc:valueType",
        object="https://example.test/project#CleanProbability",
        change_kind="replace",
        rationale=(
            "Testing a tempting semantic cleanup so reviewers can compare the "
            "current raw value type with the proposed parsed value type."
        ),
    )
    value_type_panel = value_type_change.judgement_panel
    assert value_type_panel.proposed_value is not None
    assert value_type_panel.proposed_value.label == "Clean probability"
    value_type_context_by_label = {
        context.value_type.label: context
        for context in value_type_panel.value_type_context
    }
    assert set(value_type_context_by_label) == {
        "Raw price payload",
        "Clean probability",
    }
    raw_context = value_type_context_by_label["Raw price payload"]
    assert raw_context.required_physical_type is not None
    assert raw_context.required_physical_type.label == "VARCHAR"
    assert raw_context.current_physical_type_matches is True
    assert raw_context.proposed_physical_type_matches is None
    assert "Current value type Raw price payload" in raw_context.note
    clean_context = value_type_context_by_label["Clean probability"]
    assert clean_context.required_physical_type is not None
    assert clean_context.required_physical_type.label == "DOUBLE"
    assert clean_context.current_physical_type_matches is None
    assert clean_context.proposed_physical_type_matches is False
    assert "Proposed value type Clean probability" in clean_context.note
    assert "proposed physical type" not in clean_context.note
    assert any(
        impact.impact_type == "changed_value_type"
        for impact in value_type_panel.impacts
    )
    value_type_description = db.describe_staged_revision(
        value_type_change.staged_revision.revision_iri
    )
    assert value_type_description.judgement_panel is not None
    assert len(value_type_description.judgement_panel.value_type_context) == 2
    assert any(
        impact.impact_type == "changed_value_type"
        for impact in value_type_description.impacts
    )

    comment_change = db.stage_map_assertion_change(
        subject="https://example.test/project#px_price",
        predicate="rdfs:comment",
        object="Clean probability column.",
        object_kind="literal",
        change_kind="replace",
        rationale=(
            "This comment cleanup has no shape-level blocker, but it still needs "
            "semantic review because the same column has attached caveats and lore."
        ),
    )
    comment_check = db.check_staged_revision_apply(
        comment_change.staged_revision.revision_iri
    )
    assert comment_check.can_apply is True
    assert comment_check.semantic_risk_level == "high"
    assert comment_check.semantic_risk_reasons

    remove_change = db.stage_map_assertion_change(
        subject="https://example.test/project#PriceSnapshots",
        predicate="rc:hasKnownCaveat",
        object="https://example.test/project#mixed_price_payload_caveat",
        change_kind="remove",
        rationale="Check that caveat removals expose an explicit removed value.",
    )
    remove_panel = remove_change.judgement_panel
    assert remove_panel.proposed_value is not None
    assert remove_panel.proposed_value.label == "Mixed price payload caveat"
    assert remove_panel.target_value is not None
    assert remove_panel.target_value.label == "Mixed price payload caveat"
    assert remove_panel.removed_value is not None
    assert remove_panel.removed_value.label == "Mixed price payload caveat"
    remove_export_path = tmp_path / "price-caveat-removal-review.md"
    db.export_staged_revision(
        remove_change.staged_revision.revision_iri,
        remove_export_path,
    )
    remove_exported = remove_export_path.read_text()
    assert "| Removed | Mixed price payload caveat | iri |" in remove_exported
    assert "| Proposed | Mixed price payload caveat | iri |" not in remove_exported


def test_stage_map_assertion_change_targets_typed_and_lang_literals(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        ex:Orders a rc:Dataset, rc:Table ;
            rdfs:label "Orders" ;
            rdfs:comment "Orders table"@en, "Table commandes"@fr ;
            rc:rowCountSnapshot 12 ;
            rc:hasColumn ex:is_active ;
            ex:confidenceScore "0.875"^^xsd:decimal .

        ex:is_active a rc:Column ;
            rc:columnName "is_active" ;
            rc:physicalType rc:Boolean ;
            rc:nullable false .
        """,
        graph="map",
    )

    decimal_support = db.describe_assertion_support(
        "https://example.test/project#Orders",
        "https://example.test/project#confidenceScore",
        "0.875",
        object_kind="literal",
        object_datatype="xsd:decimal",
    )
    assert decimal_support.assertion_present is True
    assert decimal_support.requested_object is not None
    assert decimal_support.requested_object.datatype == str(XSD.decimal)
    assert decimal_support.matching_triples[0].object_datatype == str(XSD.decimal)

    boolean_change = db.stage_map_assertion_change(
        subject="https://example.test/project#is_active",
        predicate="rc:nullable",
        object="true",
        object_kind="literal",
        object_datatype="xsd:boolean",
        change_kind="replace",
        rationale="Stage a valid typed boolean replacement.",
    )
    assert boolean_change.object_datatype == str(XSD.boolean)
    assert boolean_change.judgement_panel.proposed_value is not None
    assert boolean_change.judgement_panel.proposed_value.datatype == str(XSD.boolean)
    boolean_addition = Graph()
    boolean_addition.parse(data=boolean_change.additions[0]["content"], format="turtle")
    assert (
        URIRef("https://example.test/project#is_active"),
        URIRef(RC + "nullable"),
        Literal("true", datatype=XSD.boolean),
    ) in boolean_addition
    boolean_description = db.describe_staged_revision(
        boolean_change.staged_revision.revision_iri
    )
    assert boolean_description.judgement_panel is not None
    assert boolean_description.judgement_panel.proposed_value is not None
    assert boolean_description.judgement_panel.proposed_value.datatype == str(
        XSD.boolean
    )
    assert boolean_description.validation_conforms is True

    row_count_remove = db.stage_map_assertion_change(
        subject="https://example.test/project#Orders",
        predicate="rc:rowCountSnapshot",
        object="12",
        object_kind="literal",
        change_kind="remove",
        rationale=(
            "Compatible untyped targeting should still show the typed graph value "
            "being removed."
        ),
    )
    assert row_count_remove.judgement_panel.target_value is not None
    assert row_count_remove.judgement_panel.target_value.datatype is None
    assert row_count_remove.judgement_panel.removed_value is not None
    assert row_count_remove.judgement_panel.removed_value.datatype == str(XSD.integer)

    decimal_remove = db.stage_map_assertion_change(
        subject="https://example.test/project#Orders",
        predicate="https://example.test/project#confidenceScore",
        object="0.875",
        object_kind="literal",
        object_datatype="xsd:decimal",
        change_kind="remove",
        rationale="Remove exactly the decimal confidence-score assertion.",
    )
    assert decimal_remove.judgement_panel.removed_value is not None
    assert decimal_remove.judgement_panel.removed_value.datatype == str(XSD.decimal)
    decimal_removal = Graph()
    decimal_removal.parse(data=decimal_remove.removals[0]["content"], format="turtle")
    assert (
        URIRef("https://example.test/project#Orders"),
        URIRef("https://example.test/project#confidenceScore"),
        Literal("0.875", datatype=XSD.decimal),
    ) in decimal_removal

    label_change = db.stage_map_assertion_change(
        subject="https://example.test/project#Orders",
        predicate="rdfs:comment",
        object="Orders table",
        object_kind="literal",
        object_lang="en",
        change_kind="remove",
        rationale="Remove only the English comment while leaving other comments alone.",
    )
    assert label_change.object_lang == "en"
    assert label_change.judgement_panel.removed_value is not None
    assert label_change.judgement_panel.removed_value.lang == "en"
    assert {triple.object_lang for triple in label_change.current_values_before} == {
        "en",
        "fr",
    }
    label_removal = Graph()
    label_removal.parse(data=label_change.removals[0]["content"], format="turtle")
    assert (
        URIRef("https://example.test/project#Orders"),
        URIRef("http://www.w3.org/2000/01/rdf-schema#comment"),
        Literal("Orders table", lang="en"),
    ) in label_removal


def test_stage_map_assertion_replace_existing_value_warns_about_removals(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:Orders a rc:Dataset, rc:Table ;
            rc:hasColumn ex:order_count .

        ex:order_count a rc:Column ;
            rc:columnName "order_count" ;
            rc:physicalType rc:Integer, rc:Varchar .
        """,
        graph="map",
    )

    staged_change = db.stage_map_assertion_change(
        subject="https://example.test/project#order_count",
        predicate="rc:physicalType",
        object="rc:Integer",
        change_kind="replace",
        rationale=(
            "Keep INTEGER and remove the competing VARCHAR physical type after "
            "review."
        ),
    )

    assert staged_change.assertion_present_before is True
    assert {value.label for value in staged_change.judgement_panel.current_values} == {
        "INTEGER",
        "VARCHAR",
    }
    assert staged_change.judgement_panel.proposed_value is not None
    assert staged_change.judgement_panel.proposed_value.label == "INTEGER"
    assert len(staged_change.removals) == 1
    assert "Varchar" in staged_change.removals[0]["content"]
    assert any(
        "replacement value is already present" in note
        for note in staged_change.judgement_panel.safety_notes
    )
    assert any(
        "would mainly remove other current values" in reason
        for reason in staged_change.judgement_panel.semantic_risk_reasons
    )
    check = db.check_staged_revision_apply(
        staged_change.staged_revision.revision_iri
    )
    assert check.status == "ready"
    assert any(
        "would mainly remove other current values" in reason
        for reason in check.semantic_risk_reasons
    )


def test_stale_map_assertion_apply_check_preserves_review_risk(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/adversarial#"
    event_log = f"{base}EventLog"
    event_id = f"{base}event_log__event_id"
    account_id = f"{base}event_log__account_id"

    db.record_map_dataset(
        event_log,
        label="Event log",
        description="Scratch event stream with event-row and account identifiers.",
        is_table=True,
        row_semantics="rc:EventRow",
        entity_key=event_id,
    )
    db.record_map_column(
        event_id,
        table_iri=event_log,
        column_name="event_id",
        label="event_id",
        physical_type="rc:Varchar",
        nullable=False,
    )
    db.record_map_column(
        account_id,
        table_iri=event_log,
        column_name="account_id",
        label="account_id",
        description="Operational account identifier.",
        physical_type="rc:Varchar",
        nullable=False,
    )
    claim = db.record_claim_observation(
        summary="Account ids may not be durable person identity.",
        claim_text=(
            "account_id appears useful for joining records, but may be an "
            "operational account key rather than a person-level entity key."
        ),
        claim_kind="rc:InterpretationClaim",
        claim_targets=[event_log, account_id],
        observed_asset=event_log,
        observed_column=account_id,
        confidence="rc:MediumConfidence",
        observation_status="rc:Tentative",
        evidence_summary="Synthetic field-test note for account identity.",
        evidence_sources=["test://account-identity"],
    )
    pattern = db.record_pattern(
        summary="Account identity should stay reviewable before map promotion.",
        pattern_text=(
            "The event log has a tempting account_id join surface, but the "
            "current map still treats event_id as the event-row key."
        ),
        rationale="Changing entity key changes row-grain interpretation.",
        pattern_targets=[event_log, account_id],
        supporting_claims=[claim.claim_iri],
        map_implications=[f"{base}account_id_as_entity_key_candidate"],
    )
    staged_change = db.stage_map_assertion_change(
        event_log,
        "rc:entityKey",
        account_id,
        "Candidate entity-key replacement staged for semantic review.",
        change_kind="replace",
        object_kind="iri",
        supporting_claims=[claim.claim_iri],
        supporting_patterns=[pattern.pattern_iri],
        review_note=(
            "This is risky because account_id may identify an account rather "
            "than the event row."
        ),
        review_recommendation=(
            "Do not apply without domain confirmation of row grain."
        ),
        validation_scope="all",
    )
    ready_check = db.check_staged_revision_apply(
        staged_change.staged_revision.revision_iri
    )
    assert ready_check.status == "ready"
    assert ready_check.semantic_risk_level == "high"

    db.record_map_dataset(
        f"{base}UnrelatedAuditLog",
        label="Unrelated audit log",
        is_table=True,
        row_semantics="rc:EventRow",
        entity_key=f"{base}unrelated_audit__id",
    )

    stale_description = db.describe_staged_revision(
        staged_change.staged_revision.revision_iri
    )
    assert stale_description.judgement_panel is None
    stored_context = stale_description.stored_review_context
    assert stored_context is not None
    assert "review_note" in stored_context.source_fields
    assert "review_recommendation" in stored_context.source_fields
    assert "supporting_claims" in stored_context.source_fields
    assert "supporting_patterns" in stored_context.source_fields
    assert "impacts" in stored_context.source_fields
    assert stored_context.semantic_risk_level == "high"
    assert stored_context.review_recommendation == (
        "Do not apply without domain confirmation of row grain."
    )
    assert stored_context.review_note_signals.has_related_routes is True
    assert stored_context.review_note_signals.has_user_review_note is True
    assert stored_context.linked_support_counts.claims == 1
    assert stored_context.linked_support_counts.patterns == 1
    assert stored_context.linked_support_counts.revision_anchors >= 1
    assert any(
        impact.impact_type == "changed_row_key"
        for impact in stored_context.attention_impacts
    )

    stale_check = db.check_staged_revision_apply(
        staged_change.staged_revision.revision_iri
    )
    assert stale_check.status == "conflict"
    assert stale_check.decision == "restage_against_current_graph"
    assert stale_check.review_recommended is True
    assert stale_check.validation_skipped_reason == "conflicts_present"
    assert stale_check.semantic_risk_level == "high"
    assert "attention-level impact entries" in " ".join(
        stale_check.semantic_risk_reasons
    )
    assert len(stale_check.snapshot_drifts) == 1
    drift = stale_check.snapshot_drifts[0]
    assert drift.drift_relevance == "no_patch_subject_overlap"
    assert drift.patch_overlap_subjects == []
    assert RC + "entityKey" in drift.patch_overlap_predicates

    export_path = tmp_path / "stale-entity-key-review.md"
    db.export_staged_revision(staged_change.staged_revision.revision_iri, export_path)
    exported = export_path.read_text(encoding="utf-8")
    assert exported.index("## Semantic Review Warning") < exported.index(
        "## Current Apply Check"
    )
    assert "reconstructed from stored review context" in exported
    assert "- Semantic risk: high" in exported
    assert "## Stored Review Context" in exported
    assert "user/agent review note" in exported
    assert "changed_row_key" in exported


def test_stage_map_assertion_change_can_repair_stale_assertion_successor(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Current orders", is_table=True)
    source = db.stage_graph_revision(
        summary="Stage old orders label",
        rationale="Original candidate should be repaired as a replacement.",
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
    db.record_map_dataset(orders, label="Intervening orders", is_table=True)

    repair = db.stage_map_assertion_change(
        subject=orders,
        predicate="http://www.w3.org/2000/01/rdf-schema#label",
        object="Preferred orders",
        object_kind="literal",
        change_kind="replace",
        rationale="Repair the stale label candidate by replacing the current label.",
        restages_revision=source.revision_iri,
    )

    assert repair.revision_iri == repair.staged_revision.revision_iri
    assert repair.staged_revision.restaged_from == source.revision_iri
    assert repair.staged_revision.restage_reason is not None
    assert "Repair the stale label candidate" in (
        repair.staged_revision.restage_reason
    )
    source_description = db.describe_staged_revision(source.revision_iri)
    assert source_description.restaged_by is not None
    assert (
        source_description.restaged_by.iri
        == repair.staged_revision.revision_iri
    )
    applied = db.apply_staged_revision(repair.staged_revision.revision_iri)
    assert applied.applied_revision_iri
    current_work = db.list_graph_revisions(
        current_staged_work_only=True,
        include_apply_checks=True,
    )
    current_work_iris = {item.iri for item in current_work.revisions}
    assert source.revision_iri not in current_work_iris
    assert repair.staged_revision.revision_iri not in current_work_iris


def test_stage_map_assertion_change_replaces_row_semantics_cleanly(
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

    change = db.stage_map_assertion_change(
        subject=orders,
        predicate="rc:rowSemantics",
        object="rc:SnapshotRow",
        change_kind="replace",
        rationale=(
            "Follow the validation diagnostic repair route by replacing the "
            "current row-grain framing."
        ),
    )

    assert change.assertion_present_before is False
    assert [value.object for value in change.current_values_before] == [
        RC + "EventRow"
    ]
    assert "rc:SnapshotRow" in change.additions[0]["content"]
    assert "rc:EventRow" in change.removals[0]["content"]
    staged_iri = change.staged_revision.revision_iri
    description = db.describe_staged_revision(staged_iri)
    impacts = [impact for impact in description.impacts if impact.impact_type]
    row_semantics_impacts = [
        impact
        for impact in impacts
        if impact.impact_type == "changed_row_semantics"
    ]
    assert len(row_semantics_impacts) == 1
    impact = row_semantics_impacts[0]
    assert impact.severity == "attention"
    assert impact.predicate_label == "row semantics"
    assert impact.message == (
        "Changes row semantics on Orders from event row to snapshot row. "
        "Review attached lore before assuming the new framing is merely tidier."
    )
    assert ".. Review" not in impact.message
    assert [value.value for value in impact.removed_values] == [
        RC + "EventRow"
    ]
    assert [value.value_label for value in impact.removed_values] == ["event row"]
    assert [value.value for value in impact.added_values] == [
        RC + "SnapshotRow"
    ]
    assert [value.value_label for value in impact.added_values] == ["snapshot row"]
    assert change.judgement_panel is not None
    assert change.judgement_panel.headline == (
        "Replace row semantics on Orders: event row -> snapshot row"
    )

    check = db.check_staged_revision_apply(staged_iri)
    assert check.status == "ready"
    assert check.can_apply is True
    assert check.validation_conforms is True
    assert check.validation_result_count == 0
    current_work = db.list_graph_revisions(
        current_staged_work_only=True,
        include_apply_checks=True,
    )
    assert current_work.next_action_queue == {"apply_after_review": [staged_iri]}

    applied = db.apply_staged_revision(staged_iri)

    assert applied.triples_added == 1
    assert applied.triples_removed == 1
    assert db._objects(["map"], orders, "rc:rowSemantics") == [RC + "SnapshotRow"]
    assert (
        db.list_graph_revisions(
            current_staged_work_only=True,
            include_apply_checks=True,
        ).count
        == 0
    )


def test_record_map_storage_access_rejects_unknown_location_kind(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(
        DoxaBaseError,
    ) as excinfo:
        db.record_map_storage_access(
            "https://example.test/project#orders_local_storage",
            location_kind="local_path",
        )
    error = str(excinfo.value)
    assert "location_kind must be one of" in error
    assert "Do not use 'local_path'" in error
    assert "storage_protocol='rc:LocalFilesystemStorage'" in error
    assert "Use 'object'" in error
    assert "'directory'" in error


def test_record_map_storage_access_normalizes_bucket_location_kind_to_prefix(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_s3_storage",
        label="Orders S3 bucket",
        storage_protocol="rc:S3CompatibleStorage",
        location_kind="bucket",
        bucket_name="orders",
        key_prefix="current",
        path_templates=["dt={date}.parquet"],
        credential_reference="env:ORDERS_READONLY",
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

    description = db.describe_dataset(dataset)
    assert description.storage_accesses[0].location_kind == "prefix"
    context = db.describe_query_context(dataset)
    assert context.query_target_candidates[0].location_kind == "prefix"
    assert context.query_target_candidates[0].candidate_path == (
        "s3://orders/current/dt={date}.parquet"
    )
    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_describe_query_context_separates_analysis_caveats(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(POLYMARKET_FIXTURE)

    context = db.describe_query_context(
        "https://richcanopy.org/example/manifest/polymarket#PriceSnapshots"
    )

    assert context.readiness == "ready_for_query_planning"
    assert "Enough non-secret physical metadata" in context.readiness_note
    assert "Informational physical metadata notes" in context.readiness_note
    assert "Analysis warnings are separate caveats" in context.readiness_note
    assert context.layout_verification_status is None
    assert context.layout_verification_note is None
    dataset_target = next(
        target
        for target in context.query_target_candidates
        if target.template_source == "dataset"
    )
    assert dataset_target.template == "data/parquet/clob/prices/dt={date}/hour={hour}.parquet"
    assert dataset_target.storage_root == "data/parquet"
    assert dataset_target.candidate_path == (
        "data/parquet/clob/prices/dt={date}/hour={hour}.parquet"
    )
    assert dataset_target.composition == "template_as_returned"
    assert dataset_target.review_required is False
    assert {reason.severity for reason in dataset_target.review_reasons} == {"info"}
    partition_target = next(
        target
        for target in context.query_target_candidates
        if target.template_source == "partition_scheme"
    )
    assert partition_target.template == "data/parquet/{stream}/dt={date}/hour={hour}.parquet"
    assert partition_target.composition == "template_as_returned"
    assert all(issue.severity == "info" for issue in context.issues)
    assert any(
        issue.code == "verification_status_not_recorded"
        and issue.domain == "query_planning"
        and issue.resource is not None
        and issue.resource.iri
        == "https://richcanopy.org/example/manifest/polymarket#PriceSnapshots"
        for issue in context.issues
    )
    mixed_price_caveat = (
        "https://richcanopy.org/example/manifest/polymarket#"
        "caveat_mixed_type_price"
    )
    assert any(
        warning.code == "direct_analysis_caveat"
        and warning.domain == "analysis"
        and warning.severity == "warning"
        and warning.resource is not None
        and warning.resource.iri == mixed_price_caveat
        and warning.details is not None
        and warning.details["caveat_severity_iri"] == RC + "Moderate"
        and warning.details["caveat_severity_label"] == "moderate"
        and warning.details["scope"] == "direct"
        and "Price analysis must filter" in warning.message
        and ".. Impact:" not in warning.message
        for warning in context.analysis_warnings
    )


def test_query_analysis_warnings_preserve_caveat_severity_details(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/query-caveats#"
    dataset = f"{base}Orders"
    storage = f"{base}OrdersStorage"
    layout = f"{base}OrdersParquetLayout"
    minor_caveat = f"{base}MinorCaveat"
    moderate_caveat = f"{base}ModerateCaveat"
    severe_caveat = f"{base}SevereCaveat"

    db.record_map_storage_access(
        storage,
        label="Orders local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="directory",
        storage_root=str(tmp_path / "warehouse"),
        path_templates=["orders/*.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
        datasets=[dataset],
    )
    db.record_map_physical_layout(
        layout,
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
        datasets=[dataset],
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        storage_accesses=[storage],
        physical_layouts=[layout],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_caveat(
        minor_caveat,
        label="Minor orders caveat",
        description="Minor caveat affects cosmetic query interpretation.",
        impact="Review only when comparing display strings.",
        severity="rc:Minor",
        targets=[dataset],
    )
    db.record_map_caveat(
        moderate_caveat,
        label="Moderate orders caveat",
        description="Moderate caveat affects aggregate interpretation.",
        impact="Review before publishing aggregate totals.",
        severity="rc:Moderate",
        targets=[dataset],
    )
    db.record_map_caveat(
        severe_caveat,
        label="Severe orders caveat",
        description="Severe caveat affects scoped execution.",
        impact="Pause unless the query scope explicitly excludes bad rows.",
        severity="rc:Severe",
        targets=[dataset],
    )

    context = db.describe_query_context(dataset)

    warnings_by_iri = {
        warning.resource.iri: warning
        for warning in context.analysis_warnings
        if warning.resource is not None
    }
    assert set(warnings_by_iri) == {
        minor_caveat,
        moderate_caveat,
        severe_caveat,
    }
    assert warnings_by_iri[minor_caveat].severity == "info"
    assert warnings_by_iri[moderate_caveat].severity == "warning"
    assert warnings_by_iri[severe_caveat].severity == "warning"
    assert warnings_by_iri[minor_caveat].details == {
        "scope": "direct",
        "caveat_iri": minor_caveat,
        "caveat_label": "Minor orders caveat",
        "caveat_description": (
            "Minor caveat affects cosmetic query interpretation."
        ),
        "caveat_impact": "Review only when comparing display strings.",
        "caveat_severity_iri": RC + "Minor",
        "caveat_severity_label": "minor",
    }
    assert warnings_by_iri[moderate_caveat].details is not None
    assert warnings_by_iri[moderate_caveat].details["caveat_severity_iri"] == (
        RC + "Moderate"
    )
    assert warnings_by_iri[moderate_caveat].details["caveat_severity_label"] == (
        "moderate"
    )
    assert warnings_by_iri[severe_caveat].details is not None
    assert warnings_by_iri[severe_caveat].details["caveat_severity_iri"] == (
        RC + "Severe"
    )
    assert warnings_by_iri[severe_caveat].details["caveat_severity_label"] == (
        "severe"
    )
    assert "Pause unless" in warnings_by_iri[severe_caveat].message


def test_record_map_helpers_write_describable_map_resources(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/enron#"
    messages = f"{base}eml_messages"
    attachments = f"{base}eml_attachments"
    attachment_counts = f"{base}eml_message_attachment_counts"
    doc_id = f"{base}eml_messages__doc_id"
    parent_doc_id = f"{base}eml_attachments__parent_doc_id"
    count_doc_id = f"{base}eml_message_attachment_counts__doc_id"
    attachment_count = f"{base}eml_message_attachment_counts__attachment_count"
    caveat = f"{base}caveat_body_processing_lossy"
    storage = f"{base}local_parquet_access"
    layout = f"{base}parquet_layout"
    partition = f"{base}daily_partition"

    storage_record = db.record_map_storage_access(
        storage,
        label="local parquet access",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        storage_root="/home/james/github.com/jamtho/enron-emails",
        path_templates=["data/parquet/*.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
        layout_verification_note="Matched by listing the local parquet directory.",
        datasets=[messages],
    )
    layout_record = db.record_map_physical_layout(
        layout,
        label="zstd parquet layout",
        file_format="rc:Parquet",
        compression_codec="rc:ZstdCompression",
        layout_verification_status="rc:VerifiedByQueryLayout",
        layout_verification_note="DuckDB read confirmed the physical format.",
        datasets=[messages],
    )
    partition_record = db.record_map_partition_scheme(
        partition,
        label="daily message partition",
        partition_columns=[doc_id],
        granularity="rc:Daily",
        path_template="data/parquet/dt={date}/eml_messages.parquet",
        redundant_partition_key=doc_id,
        layout_verification_status="rc:CandidateLayout",
        layout_verification_note="Path pattern is plausible but still needs listing.",
        datasets=[messages],
    )
    caveat_record = db.record_map_caveat(
        caveat,
        label="body processing lossy",
        description="body_top is cleaned sender-new text, not raw email text.",
        severity="rc:Moderate",
        targets=[messages],
    )
    table_record = db.record_map_dataset(
        messages,
        label="EML messages",
        description="One row per parsed raw .eml message.",
        is_table=True,
        path_templates=["data/parquet/eml_messages.parquet"],
        row_count_snapshot=123,
        row_semantics="rc:EventRow",
        entity_key=doc_id,
        schema_stability="rc:FixedSchema",
        layout_verification_status="rc:VerifiedByQueryLayout",
        layout_verification_note="A representative DuckDB read succeeded during setup.",
        caveats=[caveat],
        storage_accesses=[storage],
    )
    db.record_map_dataset(
        attachments,
        label="EML attachments",
        is_table=True,
        path_templates=["data/parquet/eml_attachments.parquet"],
    )
    db.record_map_dataset(
        attachment_counts,
        label="EML attachment counts",
        is_table=True,
        entity_key=count_doc_id,
        path_templates=["data/parquet/eml_attachment_counts.parquet"],
    )
    doc_column = db.record_map_column(
        doc_id,
        table_iri=messages,
        column_name="doc_id",
        label="EML messages.doc_id",
        physical_type="rc:Varchar",
        value_type=f"{base}DocId",
        nullable=False,
    )
    db.record_map_column(
        parent_doc_id,
        table_iri=attachments,
        column_name="parent_doc_id",
        physical_type="rc:Varchar",
        value_type=f"{base}DocId",
        nullable=True,
    )
    db.record_map_column(
        count_doc_id,
        table_iri=attachment_counts,
        column_name="doc_id",
        physical_type="rc:Varchar",
        value_type=f"{base}DocId",
        nullable=False,
    )
    db.record_map_column(
        attachment_count,
        table_iri=attachment_counts,
        column_name="attachment_count",
        physical_type="rc:Integer",
        nullable=False,
    )
    relationship = db.record_map_relationship(
        f"{base}eml_attachment_parent_doc_id_fk",
        relationship_type="foreign_key",
        label="attachment parent doc id fk",
        from_column=parent_doc_id,
        to_column=doc_id,
        declared=False,
        referential_integrity="rc:StrictIntegrity",
    )
    aggregation = db.record_map_relationship(
        f"{base}attachment_counts_by_message",
        relationship_type="aggregation",
        label="attachment counts by message",
        source_dataset=attachments,
        target_dataset=attachment_counts,
        group_by_columns=[parent_doc_id],
        aggregated_columns=[
            {
                "target_column": attachment_count,
                "source_columns": [parent_doc_id],
                "aggregation_function": "rc:Count",
            }
        ],
    )

    assert storage_record.resource_type == RC + "StorageAccess"
    assert layout_record.resource_type == RC + "PhysicalLayout"
    assert partition_record.resource_type == RC + "PartitionScheme"
    assert caveat_record.resource_type == RC + "KnownCaveat"
    assert table_record.resource_type == RC + "Table"
    assert doc_column.resource_type == RC + "Column"
    assert relationship.resource_type == RC + "ForeignKey"
    assert aggregation.resource_type == RC + "Aggregation"
    assert db.validate_graph(scope="map").conforms

    description = db.describe_dataset(messages)
    assert description.label == "EML messages"
    assert description.row_semantics is not None
    assert description.row_semantics.iri == RC + "EventRow"
    assert description.entity_key is not None
    assert description.entity_key.iri == doc_id
    assert description.entity_key.column_name == "doc_id"
    assert description.entity_key.owning_dataset_iri == messages
    assert description.entity_key.owning_dataset_label == "EML messages"
    assert description.schema_stability is not None
    assert description.schema_stability.iri == RC + "FixedSchema"
    assert description.row_count_snapshot == 123
    assert description.layout_verification_status is not None
    assert description.layout_verification_status.iri == RC + "VerifiedByQueryLayout"
    assert description.layout_verification_note == (
        "A representative DuckDB read succeeded during setup."
    )
    assert description.path_templates == [
        "data/parquet/eml_messages.parquet",
        "data/parquet/dt={date}/eml_messages.parquet",
        "data/parquet/*.parquet",
    ]
    assert description.columns[0].column_name == "doc_id"
    assert description.columns[0].nullable is False
    assert description.physical_layouts[0].file_format is not None
    assert description.physical_layouts[0].file_format.iri == RC + "Parquet"
    assert description.physical_layouts[0].compression_codec is not None
    assert description.physical_layouts[0].compression_codec.iri == (
        RC + "ZstdCompression"
    )
    assert description.physical_layouts[0].layout_verification_status is not None
    assert description.physical_layouts[0].layout_verification_status.iri == (
        RC + "VerifiedByQueryLayout"
    )
    partition_description = description.partition_schemes[0]
    assert partition_description.partition_column is not None
    assert partition_description.partition_column.iri == doc_id
    assert [column.iri for column in partition_description.partition_columns] == [doc_id]
    assert partition_description.granularity is not None
    assert partition_description.granularity.iri == RC + "Daily"
    assert partition_description.path_template == (
        "data/parquet/dt={date}/eml_messages.parquet"
    )
    assert partition_description.redundant_partition_key is not None
    assert partition_description.redundant_partition_key.iri == doc_id
    assert partition_description.layout_verification_status is not None
    assert partition_description.layout_verification_status.iri == (
        RC + "CandidateLayout"
    )
    assert description.storage_accesses[0].storage_root == (
        "/home/james/github.com/jamtho/enron-emails"
    )
    assert description.storage_accesses[0].layout_verification_status is not None
    assert description.storage_accesses[0].layout_verification_status.iri == (
        RC + "VerifiedByListingLayout"
    )
    assert description.storage_accesses[0].layout_verification_note == (
        "Matched by listing the local parquet directory."
    )
    assert description.caveats[0].description == (
        "body_top is cleaned sender-new text, not raw email text."
    )
    assert description.caveats[0].severity is not None
    assert description.caveats[0].severity.iri == RC + "Moderate"
    relationship_description = description.relationships[0]
    assert relationship_description.relationship_kind == RC + "ForeignKey"
    assert relationship_description.relationship_kind_label == "ForeignKey"
    assert relationship_description.relationship_type == "foreign_key"
    assert relationship_description.foreign_key_from is not None
    assert relationship_description.foreign_key_from.iri == parent_doc_id
    assert relationship_description.foreign_key_from.column_name == "parent_doc_id"
    assert relationship_description.foreign_key_from.owning_dataset_label == (
        "EML attachments"
    )
    assert relationship_description.foreign_key_to is not None
    assert relationship_description.foreign_key_to.iri == doc_id
    assert relationship_description.foreign_key_to.column_name == "doc_id"
    assert relationship_description.foreign_key_to.owning_dataset_label == "EML messages"
    assert relationship_description.declared is False
    assert relationship_description.referential_integrity is not None
    assert relationship_description.referential_integrity.iri == RC + "StrictIntegrity"
    assert any(
        related.iri == attachments and related.relationship == "target_of"
        and related.relationship_label == "attachment parent doc id fk"
        and related.relationship_kind == RC + "ForeignKey"
        and related.relationship_kind_label == "ForeignKey"
        for related in description.related_datasets
    )
    assert len(description.related_dataset_groups) == 1
    related_group = description.related_dataset_groups[0]
    assert related_group.iri == attachments
    assert related_group.label == "EML attachments"
    assert len(related_group.reasons) == 1
    related_reason = related_group.reasons[0]
    assert related_reason.relationship == "target_of"
    assert related_reason.relationship_label == "attachment parent doc id fk"
    assert related_reason.relationship_kind_label == "ForeignKey"
    assert related_reason.declared is False
    assert related_reason.referential_integrity is not None
    assert related_reason.referential_integrity.iri == RC + "StrictIntegrity"
    assert {column.column_name for column in related_reason.columns} == {
        "doc_id",
        "parent_doc_id",
    }
    assert [column.column_name for column in related_reason.current_dataset_columns] == [
        "doc_id"
    ]
    assert [column.column_name for column in related_reason.related_dataset_columns] == [
        "parent_doc_id"
    ]
    assert [tag.relationship_kind_label for tag in related_reason.relationship_tags] == [
        "ForeignKey"
    ]

    count_description = db.describe_dataset(attachment_counts)
    count_relationship = next(
        relationship
        for relationship in count_description.relationships
        if relationship.relationship_kind == RC + "Aggregation"
    )
    assert count_relationship.relationship_type == "aggregation"
    assert count_relationship.source_dataset is not None
    assert count_relationship.source_dataset.iri == attachments
    assert [column.column_name for column in count_relationship.group_by_columns] == [
        "parent_doc_id"
    ]
    assert len(count_relationship.aggregated_columns) == 1
    count_mapping = count_relationship.aggregated_columns[0]
    assert count_mapping.target_column is not None
    assert count_mapping.target_column.column_name == "attachment_count"
    assert [column.column_name for column in count_mapping.source_columns] == [
        "parent_doc_id"
    ]
    assert count_mapping.aggregation_function is not None
    assert count_mapping.aggregation_function.iri == RC + "Count"
    assert any(
        related.iri == attachments
        and related.relationship == "aggregated_from"
        and related.relationship_kind == RC + "Aggregation"
        for related in count_description.related_datasets
    )
    count_group = count_description.related_dataset_groups[0]
    count_reason = count_group.reasons[0]
    assert count_reason.relationship == "aggregated_from"
    assert {column.column_name for column in count_reason.columns} == {
        "attachment_count",
        "parent_doc_id",
    }


def test_record_map_dataset_partial_update_preserves_table_type(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#messages"

    db.record_map_dataset(
        table,
        label="Messages",
        is_table=True,
        path_templates=["data/messages.parquet"],
    )
    db.record_map_dataset(table, label="Updated messages")

    description = db.describe_dataset(table)
    assert description.label == "Updated messages"
    assert RC + "Table" in description.types


def test_record_map_analysis_view_captures_logical_query_context(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/analysis-view#"
    source = f"{base}messages"
    view = f"{base}sent_external_messages"
    caveat = f"{base}redacted_body_caveat"

    db.record_map_dataset(source, label="Messages", is_table=True)
    db.record_map_caveat(
        caveat,
        label="Redacted body caveat",
        description="Message bodies may be redacted in the source export.",
        severity="rc:Moderate",
    )
    result = db.record_map_analysis_view(
        view,
        label="Sent external messages",
        description="External sent-message denominator used for analysis.",
        source_datasets=[source],
        row_count_snapshot=42,
        caveats=[caveat],
        denominator_label="External sent message denominator",
        denominator_description="One row per sent message with an external recipient.",
        denominator_row_count_snapshot=42,
        denominator_basis="direction = sent and recipient domain is outside example.test",
        query_snippet_label="External sent message SQL",
        query_snippet_description="Reviewed DuckDB SQL recipe for reconstructing the view.",
        query_text=(
            "select * from messages "
            "where direction = 'sent' and recipient_domain <> 'example.test'"
        ),
        query_language="DuckDB SQL",
        query_engine="duckdb",
    )

    assert result.resource_type == RC + "AnalysisView"
    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text

    described = db.describe_analysis_view(view)
    assert described.label == "Sent external messages"
    assert set(described.types) == {RC + "Dataset", RC + "Table", RC + "AnalysisView"}
    assert [source_dataset.iri for source_dataset in described.source_datasets] == [
        source
    ]
    assert described.denominator is not None
    assert described.denominator.iri == f"{view}/denominator"
    assert described.denominator.description == (
        "One row per sent message with an external recipient."
    )
    assert described.denominator.row_count_snapshot == 42
    assert described.denominator.basis == (
        "direction = sent and recipient domain is outside example.test"
    )
    assert len(described.query_snippets) == 1
    snippet = described.query_snippets[0]
    assert snippet.iri == f"{view}/query-snippet/1"
    assert snippet.query_language == "DuckDB SQL"
    assert snippet.query_engine == "duckdb"
    assert snippet.query_text is not None
    assert "recipient_domain" in snippet.query_text
    assert [item.iri for item in described.caveats] == [caveat]
    assert described.source_caveats == []
    assert described.row_count_snapshot == 42

    dataset_description = db.describe_dataset(view)
    assert RC + "AnalysisView" in dataset_description.types
    assert dataset_description.operational_warnings == []

    context = db.describe_query_context(view)
    assert context.readiness == "logical_analysis_view"
    assert context.issues[0].code == "logical_analysis_view_not_physical_route"
    assert context.suggested_repair_action_group_count == 0
    assert context.query_target_candidates == []
    assert context.query_target_decision.status == "logical_analysis_view"
    assert context.suggested_next_actions[0].tool == "doxabase.describe_analysis_view"
    assert context.safe_inspection_action_indexes == [0, 1]

    brief = db.project_brief(limit=5)
    view_tasks = [
        task
        for task in brief.recommended_next_tasks
        if task.resource is not None and task.resource.iri == view
    ]
    assert len(view_tasks) == 1
    assert view_tasks[0].task_type == "analysis_view_review"
    assert view_tasks[0].source == "describe_analysis_view"
    assert view_tasks[0].suggested_next_action is not None
    assert view_tasks[0].suggested_next_action.tool == "doxabase.describe_analysis_view"
    assert "query_context_review" not in [
        task.task_type for task in view_tasks
    ]


def test_record_map_analysis_view_accepts_multiple_query_snippets(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/analysis-view#"
    source = f"{base}messages"
    view = f"{base}message_like_rows"

    db.record_map_dataset(source, label="Messages", is_table=True)
    db.record_map_analysis_view(
        view,
        label="Message-like rows",
        source_datasets=[source],
        denominator_description="Rows that behave like user-authored messages.",
        query_snippets=[
            {
                "label": "DuckDB view definition",
                "query_text": (
                    "create or replace view message_like_rows as "
                    "select * from messages where folder_family <> 'calendar'"
                ),
                "query_language": "DuckDB SQL",
                "query_engine": "duckdb",
            },
            {
                "iri": f"{view}/query-snippet/count-check",
                "label": "Count check",
                "query_text": "select count(*) from message_like_rows",
                "query_language": "DuckDB SQL",
                "query_engine": "duckdb",
            },
        ],
    )

    described = db.describe_analysis_view(view)
    assert [snippet.iri for snippet in described.query_snippets] == [
        f"{view}/query-snippet/1",
        f"{view}/query-snippet/count-check",
    ]
    assert [snippet.label for snippet in described.query_snippets] == [
        "DuckDB view definition",
        "Count check",
    ]
    assert "folder_family" in (described.query_snippets[0].query_text or "")
    assert db.describe_query_context(view).readiness == "logical_analysis_view"
    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text

    db.record_map_analysis_view(view, query_snippets=[])
    assert db.describe_analysis_view(view).query_snippets == []


def test_record_map_analysis_view_bundle_records_reviewed_sidecar_specs(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/analysis-view-bundle#"
    source = f"{base}messages"
    plausible_view = f"{base}plausible_messages"
    message_like_view = f"{base}message_like_rows"

    db.record_map_dataset(source, label="Messages", is_table=True)
    result = db.record_map_analysis_view_bundle(
        [
            {
                "view_iri": plausible_view,
                "label": "Plausible messages",
                "source_datasets": [source],
                "row_count_snapshot": 120,
                "denominator_description": "Messages dated inside the reviewed window.",
                "denominator_row_count_snapshot": 120,
                "denominator_basis": "date_sent between 1997-01-01 and 2004-12-31",
                "query_snippets": [
                    {
                        "label": "View definition",
                        "query_text": (
                            "create view plausible_messages as "
                            "select * from messages where date_sent between "
                            "'1997-01-01' and '2004-12-31'"
                        ),
                        "query_language": "DuckDB SQL",
                        "query_engine": "duckdb",
                    },
                    {
                        "label": "Count check",
                        "query_text": "select count(*) from plausible_messages",
                        "query_language": "DuckDB SQL",
                        "query_engine": "duckdb",
                    },
                ],
            },
            {
                "iri": message_like_view,
                "label": "Message-like rows",
                "source_datasets": [source],
                "row_count_snapshot": 98,
                "denominator_description": (
                    "Plausible messages excluding calendar and contact rows."
                ),
                "query_snippets": [
                    {
                        "label": "View definition",
                        "query_text": (
                            "create view message_like_rows as "
                            "select * from plausible_messages "
                            "where folder_family not in ('calendar', 'contacts')"
                        ),
                        "query_language": "DuckDB SQL",
                        "query_engine": "duckdb",
                    }
                ],
            },
        ]
    )

    assert result.view_count == 2
    assert result.view_iris == [plausible_view, message_like_view]
    assert result.query_snippet_count == 3
    assert [view.label for view in result.analysis_views] == [
        "Plausible messages",
        "Message-like rows",
    ]
    assert [action.tool.removeprefix("doxabase.") for action in result.suggested_next_actions] == [
        "describe_query_context",
        "describe_query_context",
    ]
    assert all(
        db.describe_query_context(view_iri).readiness == "logical_analysis_view"
        for view_iri in result.view_iris
    )
    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_record_map_analysis_view_bundle_rejects_duplicate_views_before_mutation(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/analysis-view-bundle#"
    view = f"{base}message_like_rows"
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match="duplicates"):
        db.record_map_analysis_view_bundle(
            [
                {"iri": view, "label": "Message-like rows"},
                {"view_iri": view, "label": "Duplicate message-like rows"},
            ]
        )

    assert _mutable_graph_counts(db) == before_counts


def test_record_analysis_packet_preserves_views_artifacts_and_tasks(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/analysis-packet#"
    source = f"{base}messages"
    packet = f"{base}western_power_packet"
    parent_view = f"{base}western_power_policy"
    lane_view = f"{base}western_power_policy_operational_lane"
    parent_caveat = f"{base}western_power_policy_population_caveat"
    aggregate_json = f"{base}western_power_lanes_json"
    register_tables_recipe = f"{base}register_tables_recipe"
    attachment_join_recipe = f"{base}attachment_join_recipe"
    lane_chart = f"{base}operational_lane_chart"

    db.record_map_dataset(source, label="Messages", is_table=True)
    db.record_map_caveat(
        parent_caveat,
        label="Western policy population caveat",
        description="The Western policy subcorpus depends on reviewed search terms.",
        severity="rc:Moderate",
    )
    result = db.record_analysis_packet(
        packet,
        label="Western power policy packet",
        summary=(
            "Reviewed aggregate packet for Western power policy lanes and "
            "visual artifacts."
        ),
        analysis_views=[
            {
                "iri": parent_view,
                "label": "Western power policy subcorpus",
                "source_datasets": [source],
                "row_count_snapshot": 107510,
                "denominator_description": (
                    "Message-like rows matching reviewed Western power terms."
                ),
                "caveats": [parent_caveat],
                "query_snippets": [
                    {
                        "label": "Subcorpus definition",
                        "query_text": (
                            "select * from messages where western_policy_match"
                        ),
                        "query_language": "DuckDB SQL",
                        "query_engine": "duckdb",
                    }
                ],
            },
            {
                "iri": lane_view,
                "label": "Operational ISO lane",
                "source_datasets": [parent_view],
                "row_count_snapshot": 37017,
                "denominator_description": (
                    "Western policy rows matching operational ISO terms."
                ),
            },
        ],
        artifacts=[
            {
                "iri": aggregate_json,
                "label": "Western lane aggregate JSON",
                "summary": "Aggregate lane counts and overlaps.",
                "source_path": "scratch://western_power_policy_lanes.json",
                "artifact_role": "lane aggregate",
                "media_type": "application/json",
                "supports": [parent_view, lane_view],
            },
            {
                "iri": lane_chart,
                "label": "Operational lane chart",
                "source_path": "scratch://visuals/operational_lane.png",
                "artifact_role": "visualization",
                "media_type": "image/png",
                "image_width": 1200,
                "image_height": 800,
                "supports": [lane_view],
            },
        ],
        query_recipes=[
            {
                "iri": register_tables_recipe,
                "label": "Register Enron message tables",
                "description": "DuckDB setup snippet for the packet cookbook.",
                "query_text": "create view eml_messages as select * from read_parquet(?)",
                "query_language": "DuckDB SQL",
                "query_engine": "duckdb",
                "targets": [source],
            },
            {
                "query_recipe_iri": attachment_join_recipe,
                "label": "Join attachments by document identity",
                "query_text": (
                    "select * from eml_messages m "
                    "left join eml_attachments a on a.parent_doc_id = m.doc_id"
                ),
                "query_language": "DuckDB SQL",
                "query_engine": "duckdb",
                "targets": [parent_view],
            },
        ],
        followup_tasks=[
            {
                "label": "Inspect April 2001 operational spike",
                "task_text": (
                    "Trace week-level operational ISO subjects across the "
                    "reviewed custodians."
                ),
                "priority": "high",
                "targets": [lane_view],
            }
        ],
        pattern_summary="Western power lanes need packet-level handoff.",
        pattern_text=(
            "The Western power analysis combines logical populations, aggregate "
            "JSON, and visualization artifacts that should be carried together."
        ),
        pattern_rationale=(
            "Future agents need one graph-native entry point for the lane "
            "definitions and external artifact locators."
        ),
    )

    assert result.packet_iri == packet
    assert result.evidence_iri == packet
    assert result.analysis_view_iris == [parent_view, lane_view]
    assert result.artifact_iris == [aggregate_json, lane_chart]
    assert result.query_recipe_iris == [
        register_tables_recipe,
        attachment_join_recipe,
    ]
    assert len(result.query_recipe_records) == 2
    assert len(result.followup_task_iris) == 1
    assert result.pattern_iri is not None
    assert {action.tool.removeprefix("doxabase.") for action in result.suggested_next_actions} >= {
        "get_context_graph",
        "describe_query_context",
    }
    overview = db.graph_overview()
    assert overview.key_counts["analysis_views"] == 2
    assert overview.key_counts["analysis_packets"] == 1
    assert overview.key_counts["analysis_artifacts"] == 2
    assert overview.key_counts["analysis_followup_tasks"] == 1
    assert overview.key_counts["executable_query_snippets"] == 3

    packet_resource = to_dict(db.describe_resource(packet, graph="evidence"))
    assert RC + "AnalysisPacket" in packet_resource["types"]
    recipe_resource = to_dict(
        db.describe_resource(register_tables_recipe, graph="evidence")
    )
    assert RC + "ExecutableQuerySnippet" in recipe_resource["types"]
    parent_description = db.describe_analysis_view(parent_view)
    lane_description = db.describe_analysis_view(lane_view)
    assert [caveat.iri for caveat in parent_description.caveats] == [
        parent_caveat
    ]
    assert parent_description.source_caveats == []
    assert lane_description.caveats == []
    assert [caveat.iri for caveat in lane_description.source_caveats] == [
        parent_caveat
    ]
    assert db.describe_query_context(parent_view).readiness == "logical_analysis_view"
    context = to_dict(db.get_context_graph([packet], profile="resource_brief"))
    assert packet in {resource["iri"] for resource in context["resources"]}
    assert register_tables_recipe in {
        resource["iri"] for resource in context["resources"]
    }
    analysis_view_actions = [
        action
        for action in context["suggested_next_actions"]
        if action["tool"] == "doxabase.describe_analysis_view"
    ]
    assert {action["args"]["iri"] for action in analysis_view_actions} == {
        parent_view,
        lane_view,
    }
    assert "read_parquet" in json.dumps(context)
    brief = db.project_brief(limit=10)
    assert brief.key_counts["analysis_packets"] == 1
    assert brief.queue_counts["analysis_packet_review"] == 1
    packet_task = next(
        task
        for task in brief.recommended_next_tasks
        if task.task_type == "analysis_packet_review"
    )
    assert packet_task.resource is not None
    assert packet_task.resource.iri == packet
    assert packet_task.suggested_next_action is not None
    assert packet_task.suggested_next_action.tool == "doxabase.get_context_graph"
    assert packet_task.suggested_next_action.args == {
        "seed_iris": [packet],
        "profile": "resource_brief",
    }
    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_record_analysis_packet_requires_existing_linked_analysis_views(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match="existing rc:AnalysisView"):
        db.record_analysis_packet(
            "https://example.test/analysis-packet#packet",
            summary="Packet with a missing linked view.",
            evidence_sources=["scratch://packet.md"],
            analysis_view_iris=[
                "https://example.test/analysis-packet#missing_view",
            ],
        )

    assert _mutable_graph_counts(db) == before_counts


def test_record_analysis_packet_allows_empty_optional_manifest_sections(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    packet = "https://example.test/analysis-packet#sidecar_packet"

    result = db.record_analysis_packet(
        packet,
        summary="Reviewed sidecar packet with artifact locators only.",
        analysis_views=[],
        query_recipes=[],
        artifacts=[
            {
                "source_path": "scratch://analysis_views.md",
                "artifact_role": "report",
            }
        ],
        followup_tasks=[],
    )

    assert result.packet_iri == packet
    assert result.analysis_view_iris == []
    assert result.query_recipe_iris == []
    assert len(result.artifact_iris) == 1
    assert result.followup_task_iris == []
    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


@pytest.mark.parametrize(
    ("query_recipes", "match"),
    [
        (
            [{"query_text": ""}],
            "query_recipes\\[1\\]\\.query_text",
        ),
        (
            [{"query_text": "select 1", "unexpected": "field"}],
            "unsupported field",
        ),
        (
            [
                {
                    "iri": "https://example.test/analysis-packet#recipe",
                    "query_text": "select 1",
                },
                {
                    "query_recipe_iri": "https://example.test/analysis-packet#recipe",
                    "query_text": "select 2",
                },
            ],
            "duplicates",
        ),
    ],
)
def test_record_analysis_packet_preflights_query_recipe_validation(
    tmp_path: Path,
    query_recipes: list[dict[str, object]],
    match: str,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match=match):
        db.record_analysis_packet(
            "https://example.test/analysis-packet#packet",
            summary="Packet with invalid query recipes.",
            evidence_sources=["scratch://packet.md"],
            query_recipes=query_recipes,
        )

    assert _mutable_graph_counts(db) == before_counts


def test_record_map_analysis_view_rejects_mixed_query_snippet_inputs(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    view = "https://example.test/analysis-view#message_like_rows"
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match="query_snippets cannot be combined"):
        db.record_map_analysis_view(
            view,
            label="Message-like rows",
            query_text="select * from messages",
            query_snippets=[
                {
                    "query_text": "select count(*) from messages",
                    "query_language": "DuckDB SQL",
                }
            ],
        )

    assert _mutable_graph_counts(db) == before_counts


def test_record_map_table_bundle_records_parquet_table_map(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/table-bundle#"
    table = f"{base}orders"
    amount = f"{base}orders__amount"

    result = db.record_map_table_bundle(
        table,
        label="Orders",
        description="Orders table from a reviewed Parquet export.",
        columns=[
            {
                "column_name": "order_id",
                "physical_type": "rc:Varchar",
                "nullable": False,
            },
            {
                "column_iri": amount,
                "column_name": "amount",
                "physical_type": "rc:Double",
                "value_type": f"{base}MoneyAmount",
                "nullable": True,
            },
        ],
        path_templates=["orders.parquet"],
        row_count_snapshot=120,
        row_semantics="rc:EventRow",
        schema_stability="rc:FixedSchema",
        layout_verification_status="rc:VerifiedByQueryLayout",
        layout_verification_note="DuckDB schema check reviewed on the local export.",
        storage_access_iri=f"{base}orders_storage",
        storage_label="Orders local Parquet object",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        location_kind="object",
        storage_root=str(tmp_path / "orders.parquet"),
        storage_path_templates=["orders.parquet"],
        storage_layout_verification_status="rc:VerifiedByListingLayout",
        physical_layout_iri=f"{base}orders_parquet_layout",
        physical_layout_label="Orders Parquet layout",
        file_format="rc:Parquet",
        compression_codec="rc:ZstdCompression",
        physical_layout_verification_status="rc:VerifiedByQueryLayout",
    )

    assert result.dataset.resource_type == RC + "Table"
    assert result.storage_access is not None
    assert result.storage_access.iri == f"{base}orders_storage"
    assert result.physical_layout is not None
    assert result.physical_layout.iri == f"{base}orders_parquet_layout"
    assert result.column_iris == [f"{table}__order_id", amount]
    assert [record.resource_type for record in result.columns] == [RC + "Column"] * 2
    assert result.suggested_next_actions[0].tool == "doxabase.describe_dataset"
    assert result.suggested_next_actions[1].tool == "doxabase.describe_query_context"

    description = db.describe_dataset(table)
    assert description.label == "Orders"
    assert description.row_count_snapshot == 120
    assert description.row_semantics is not None
    assert description.row_semantics.iri == RC + "EventRow"
    assert [column.column_name for column in description.columns] == [
        "amount",
        "order_id",
    ]
    amount_column = next(
        column for column in description.columns if column.column_name == "amount"
    )
    assert amount_column.value_type is not None
    assert amount_column.value_type.iri == f"{base}MoneyAmount"
    assert description.storage_accesses[0].storage_protocol is not None
    assert description.storage_accesses[0].storage_protocol.iri == (
        RC + "LocalFilesystemStorage"
    )
    assert description.physical_layouts[0].file_format is not None
    assert description.physical_layouts[0].file_format.iri == RC + "Parquet"
    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_record_map_table_bundle_preflights_column_specs(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match="unsupported field"):
        db.record_map_table_bundle(
            "https://example.test/table-bundle#orders",
            columns=[
                {
                    "column_name": "order_id",
                    "unexpected": "not supported",
                }
            ],
            file_format="rc:Parquet",
        )

    assert _mutable_graph_counts(db) == before_counts

    with pytest.raises(DoxaBaseError, match="physical_layout_label must be a string"):
        db.record_map_table_bundle(
            "https://example.test/table-bundle#orders",
            columns=[{"column_name": "order_id"}],
            storage_access_iri="https://example.test/table-bundle#orders_storage",
            storage_protocol="rc:LocalFilesystemStorage",
            access_mode="rc:ReadOnlyAccess",
            location_kind="object",
            storage_root="/tmp/orders.parquet",
            physical_layout_label=42,
            file_format="rc:Parquet",
        )

    assert _mutable_graph_counts(db) == before_counts


def test_record_map_relationship_accepts_core_class_aliases(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/relationship-aliases#"
    messages = f"{base}messages"
    attachments = f"{base}attachments"
    counts = f"{base}attachment_counts"
    doc_id = f"{base}messages__doc_id"
    parent_doc_id = f"{base}attachments__parent_doc_id"
    body = f"{base}messages__body"
    body_top = f"{base}messages__body_top"
    count = f"{base}attachment_counts__attachment_count"

    db.record_map_dataset(messages, label="Messages", is_table=True)
    db.record_map_dataset(attachments, label="Attachments", is_table=True)
    db.record_map_dataset(counts, label="Attachment counts", is_table=True)
    for column_iri, table_iri, column_name in (
        (doc_id, messages, "doc_id"),
        (parent_doc_id, attachments, "parent_doc_id"),
        (body, messages, "body"),
        (body_top, messages, "body_top"),
        (count, counts, "attachment_count"),
    ):
        db.record_map_column(column_iri, table_iri=table_iri, column_name=column_name)

    records = [
        db.record_map_relationship(
            f"{base}attachment_parent_fk",
            relationship_type="rc:ForeignKey",
            from_column=parent_doc_id,
            to_column=doc_id,
        ),
        db.record_map_relationship(
            f"{base}doc_id_shared_identifier",
            relationship_type=RC + "SharedIdentifier",
            identifying_columns=[doc_id, parent_doc_id],
        ),
        db.record_map_relationship(
            f"{base}body_preview_derivation",
            relationship_type="Derivation",
            source_columns=[body],
            derived_columns=[body_top],
        ),
        db.record_map_relationship(
            f"{base}attachment_count_rollup",
            relationship_type="rc:Aggregation",
            source_dataset=attachments,
            target_dataset=counts,
            group_by_columns=[parent_doc_id],
            aggregated_columns=[
                {
                    "target_column": count,
                    "source_columns": [parent_doc_id],
                    "aggregation_function": "rc:Count",
                }
            ],
        ),
    ]

    assert [record.resource_type for record in records] == [
        RC + "ForeignKey",
        RC + "SharedIdentifier",
        RC + "Derivation",
        RC + "Aggregation",
    ]
    relationships = db.describe_dataset(messages).relationships
    assert {relationship.relationship_type for relationship in relationships} >= {
        "foreign_key",
        "shared_identifier",
        "derivation",
    }
    derivation = next(
        relationship
        for relationship in relationships
        if relationship.relationship_type == "derivation"
    )
    assert [column.iri for column in derivation.source_columns] == [body]
    assert [column.column_name for column in derivation.source_columns] == ["body"]
    assert [column.iri for column in derivation.derived_columns] == [body_top]
    assert [column.column_name for column in derivation.derived_columns] == [
        "body_top"
    ]
    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_record_map_relationship_rejects_data_assets_in_column_slots(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/project#"
    raw_files = f"{base}raw_files"
    clean_files = f"{base}clean_files"

    db.record_map_dataset(raw_files, label="Raw files", is_table=True)
    db.record_map_dataset(clean_files, label="Clean files", is_table=True)
    before_map_count = db.triple_count("map")

    with pytest.raises(
        DoxaBaseError,
        match="source_columns.*data asset resource.*rc:Column",
    ):
        db.record_map_relationship(
            f"{base}clean_files_derivation",
            relationship_type="derivation",
            source_dataset=raw_files,
            target_dataset=clean_files,
            source_columns=[raw_files],
            derived_columns=[clean_files],
        )

    with pytest.raises(
        DoxaBaseError,
        match=r"aggregated_columns\[1\]\.target_column.*data asset resource.*rc:Column",
    ):
        db.record_map_relationship(
            f"{base}clean_files_rollup",
            relationship_type="aggregation",
            source_dataset=raw_files,
            target_dataset=clean_files,
            aggregated_columns=[
                {
                    "target_column": clean_files,
                    "source_columns": [raw_files],
                    "aggregation_function": "rc:Count",
                }
            ],
        )

    assert db.triple_count("map") == before_map_count


def test_record_map_relationship_rejects_unrecorded_column_iris(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/project#"
    messages = f"{base}messages"
    body = f"{base}messages__body"
    body_top = f"{base}messages__body_top"

    db.record_map_dataset(messages, label="Messages", is_table=True)
    before_map_count = db.triple_count("map")

    with pytest.raises(
        DoxaBaseError,
        match=r"source_columns.*not a recorded rc:Column",
    ):
        db.record_map_relationship(
            f"{base}body_preview_derivation",
            relationship_type="derivation",
            source_columns=[body],
            derived_columns=[body_top],
        )

    assert db.triple_count("map") == before_map_count


def test_record_map_relationship_rejects_raw_column_names_with_specific_hint(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/project#"
    messages = f"{base}messages"
    body_top = f"{base}messages__body_top"

    db.record_map_dataset(messages, label="Messages", is_table=True)
    before_map_count = db.triple_count("map")

    with pytest.raises(DoxaBaseError) as exc_info:
        db.record_map_relationship(
            f"{base}body_preview_derivation",
            relationship_type="derivation",
            source_columns=["body"],
            derived_columns=[body_top],
        )

    message = str(exc_info.value)
    assert "source_columns values must be recorded column IRIs or CURIEs" in message
    assert "not raw column names: 'body'" in message
    assert "record_map_column" in message
    assert "rc:Moderate" not in message
    assert db.triple_count("map") == before_map_count


def test_record_map_relationship_rejects_columns_in_dataset_endpoints(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/project#"
    messages = f"{base}messages"
    body = f"{base}messages__body"
    body_top = f"{base}messages__body_top"

    db.record_map_dataset(messages, label="Messages", is_table=True)
    db.record_map_column(body, table_iri=messages, column_name="body")
    db.record_map_column(body_top, table_iri=messages, column_name="body_top")
    before_map_count = db.triple_count("map")

    with pytest.raises(
        DoxaBaseError,
        match="source_datasets.*recorded rc:Column.*source_columns/derived_columns",
    ):
        db.record_map_relationship(
            f"{base}body_preview_derivation",
            relationship_type="derivation",
            source_datasets=[body],
            target_datasets=[body_top],
        )

    assert db.triple_count("map") == before_map_count


def test_record_map_relationship_supports_asset_level_endpoints(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/asset-frontier#"
    raw_bags = f"{base}raw_sonar_bag_files"
    navigation = f"{base}navigation_corrections_yaml"
    mosaic = f"{base}survey_mosaic_geotiff"
    contact_sheet = f"{base}qa_contact_sheet_png"

    db.record_map_dataset(raw_bags, label="Raw side-scan sonar bag files")
    db.record_map_dataset(navigation, label="Navigation correction pack")
    db.record_map_dataset(mosaic, label="Survey mosaic GeoTIFF")
    db.record_map_dataset(contact_sheet, label="QA contact sheet PNG")
    db.record_map_relationship(
        f"{base}mosaic_from_bags_and_navigation",
        relationship_type="derivation",
        label="mosaic from bags and navigation corrections",
        source_endpoints=[
            {
                "dataset": raw_bags,
                "role": "primary sonar input",
                "order": 1,
            },
            {
                "dataset": navigation,
                "role": "navigation correction input",
                "order": 2,
            },
        ],
        target_datasets=[mosaic],
        derivation_properties=["rc:Deterministic", "rc:Lossy"],
    )
    db.record_map_relationship(
        f"{base}contact_sheet_from_mosaic",
        relationship_type="aggregation",
        label="contact sheet from mosaic",
        source_datasets=[mosaic],
        target_datasets=[contact_sheet],
    )

    assert db.validate_graph(scope="all").conforms

    mosaic_description = db.describe_dataset(mosaic)
    derivation = next(
        relationship
        for relationship in mosaic_description.relationships
        if relationship.relationship_type == "derivation"
    )
    assert {dataset.iri for dataset in derivation.source_datasets} == {
        raw_bags,
        navigation,
    }
    assert [dataset.iri for dataset in derivation.source_datasets] == [
        raw_bags,
        navigation,
    ]
    assert [
        (endpoint.dataset.iri if endpoint.dataset else None, endpoint.role)
        for endpoint in derivation.source_endpoints
    ] == [
        (raw_bags, "primary sonar input"),
        (navigation, "navigation correction input"),
    ]
    assert [endpoint.order for endpoint in derivation.source_endpoints] == [1, 2]
    assert {endpoint.direction for endpoint in derivation.source_endpoints} == {
        "source"
    }
    assert [dataset.iri for dataset in derivation.target_datasets] == [mosaic]
    assert derivation.source_columns == []
    assert derivation.derived_columns == []
    assert {related.relationship for related in mosaic_description.related_datasets} >= {
        "derived_from",
        "source_of_aggregation",
    }
    assert not any(
        related.relationship == "aggregated_from"
        and related.relationship_kind == RC + "Derivation"
        for related in mosaic_description.related_datasets
    )

    raw_description = db.describe_dataset(raw_bags)
    assert any(
        related.iri == mosaic
        and related.relationship == "source_of_derivation"
        and related.relationship_kind == RC + "Derivation"
        for related in raw_description.related_datasets
    )

    contact_description = db.describe_dataset(contact_sheet)
    assert any(
        related.iri == mosaic
        and related.relationship == "aggregated_from"
        and related.relationship_kind == RC + "Aggregation"
        for related in contact_description.related_datasets
    )


def test_record_map_asset_transform_captures_conditions_outputs_and_tuple_grain(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/asset-transform#"
    raw_bags = f"{base}raw_sonar_bag_files"
    navigation = f"{base}navigation_corrections_yaml"
    mosaic = f"{base}survey_mosaic_geotiff"
    condition = f"{base}valid_navigation_filter"

    db.record_map_dataset(raw_bags, label="Raw side-scan sonar bag files")
    db.record_map_dataset(navigation, label="Navigation correction pack")
    db.record_map_dataset(mosaic, label="Survey mosaic GeoTIFF")
    result = db.record_map_asset_transform(
        f"{base}mosaic_from_bags_and_navigation",
        relationship_type="derivation",
        label="mosaic from bags and navigation corrections",
        source_endpoints=[
            {
                "dataset": raw_bags,
                "role": "primary sonar input",
                "order": 1,
            },
            {
                "dataset": navigation,
                "role": "navigation correction input",
                "order": 2,
            },
        ],
        target_datasets=[mosaic],
        derivation_properties=["rc:Deterministic", "rc:Lossy"],
        conditions=[
            {
                "iri": condition,
                "label": "valid navigation filter",
                "condition_kind": "rc:FilterCondition",
                "expression": "only pings with a reviewed navigation correction fix",
                "expression_language": "reviewed prose",
                "applies_to_datasets": [raw_bags, navigation],
            }
        ],
        outputs=[
            {
                "target_dataset": mosaic,
                "role": "corrected mosaic output",
                "formula": "grid corrected ping intensities into a GeoTIFF mosaic",
                "expression_language": "reviewed prose",
                "function": f"{base}BuildCorrectedMosaic",
                "conditions": [condition],
                "tuple_grain": {
                    "label": "mosaic tile tuple grain",
                    "components": [
                        {
                            "dataset": raw_bags,
                            "role": "source survey",
                            "order": 1,
                        },
                        {
                            "expression": "mosaic tile coordinate in the output grid",
                            "role": "tile coordinate",
                            "order": 2,
                        },
                    ],
                },
            }
        ],
    )

    assert result.resource_type == RC + "Derivation"
    assert db.validate_graph(scope="all").conforms

    mosaic_description = db.describe_dataset(mosaic)
    assert mosaic_description.columns == []
    assert len(mosaic_description.tuple_grains) == 1
    grain = mosaic_description.tuple_grains[0]
    assert [component.role for component in grain.components] == [
        "source survey",
        "tile coordinate",
    ]
    assert grain.components[0].dataset is not None
    assert grain.components[0].dataset.iri == raw_bags
    assert grain.components[1].expression == "mosaic tile coordinate in the output grid"

    relationship = next(
        item
        for item in mosaic_description.relationships
        if item.relationship_type == "derivation"
    )
    assert [dataset.iri for dataset in relationship.source_datasets] == [
        raw_bags,
        navigation,
    ]
    assert [dataset.iri for dataset in relationship.target_datasets] == [mosaic]
    assert [prop.iri for prop in relationship.derivation_properties] == [
        RC + "Deterministic",
        RC + "Lossy",
    ]
    assert len(relationship.transform_conditions) == 1
    described_condition = relationship.transform_conditions[0]
    assert described_condition.iri == condition
    assert described_condition.condition_kind is not None
    assert described_condition.condition_kind.iri == RC + "FilterCondition"
    assert described_condition.expression == (
        "only pings with a reviewed navigation correction fix"
    )
    assert {dataset.iri for dataset in described_condition.applies_to_datasets} == {
        raw_bags,
        navigation,
    }
    assert len(relationship.transform_outputs) == 1
    output = relationship.transform_outputs[0]
    assert output.target_dataset is not None
    assert output.target_dataset.iri == mosaic
    assert output.formula == "grid corrected ping intensities into a GeoTIFF mosaic"
    assert output.function is not None
    assert output.function.iri == f"{base}BuildCorrectedMosaic"
    assert [item.iri for item in output.conditions] == [condition]
    assert output.tuple_grain is not None
    assert [component.role for component in output.tuple_grain.components] == [
        "source survey",
        "tile coordinate",
    ]

    before_map_count = db.triple_count("map")
    with pytest.raises(
        DoxaBaseError,
        match=r"outputs\[1\]\.conditions references .*not a supplied or existing rc:TransformCondition",
    ):
        db.record_map_asset_transform(
            f"{base}bad_condition_reference",
            relationship_type="derivation",
            source_datasets=[raw_bags],
            target_datasets=[mosaic],
            outputs=[
                {
                    "target_dataset": mosaic,
                    "conditions": [f"{base}missing_condition"],
                }
            ],
        )
    assert db.triple_count("map") == before_map_count

    with pytest.raises(
        DoxaBaseError,
        match=r"outputs\[1\]\.tuple_grain\.components\[1\]\.column.*data asset resource.*rc:Column",
    ):
        db.record_map_asset_transform(
            f"{base}bad_grain",
            relationship_type="derivation",
            source_datasets=[raw_bags],
            target_datasets=[mosaic],
            outputs=[
                {
                    "target_dataset": mosaic,
                    "tuple_grain": {
                        "components": [
                            {"column": raw_bags, "role": "not a column"},
                            {"expression": "tile coordinate"},
                        ],
                    },
                }
            ],
        )
    assert db.triple_count("map") == before_map_count

    db.record_map_column(
        f"{base}survey_mosaic_geotiff__body_top",
        table_iri=mosaic,
        column_name="body_top",
    )
    before_map_count = db.triple_count("map")
    with pytest.raises(
        DoxaBaseError,
        match=r"outputs\[1\]\.target_dataset.*recorded rc:Column.*data assets",
    ):
        db.record_map_asset_transform(
            f"{base}bad_output_dataset",
            relationship_type="derivation",
            source_datasets=[raw_bags],
            target_datasets=[mosaic],
            outputs=[
                {
                    "target_dataset": f"{base}survey_mosaic_geotiff__body_top",
                    "formula": "clean top-level message text",
                }
            ],
        )
    assert db.triple_count("map") == before_map_count


def test_record_map_asset_transform_accepts_core_class_aliases(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/asset-transform-aliases#"
    source = f"{base}raw_files"
    target = f"{base}rollup"

    db.record_map_dataset(source, label="Raw files")
    db.record_map_dataset(target, label="Rollup")
    result = db.record_map_asset_transform(
        f"{base}rollup_from_raw",
        relationship_type="rc:Aggregation",
        source_datasets=[source],
        target_datasets=[target],
    )

    assert result.resource_type == RC + "Aggregation"
    assert db.describe_dataset(target).relationships[0].relationship_type == "aggregation"


def test_record_map_relationship_rejects_project_specific_derivation_properties(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/asset-frontier#"
    source = f"{base}raw_sonar_bag_files"
    target = f"{base}survey_mosaic_geotiff"

    db.record_map_dataset(source, label="Raw side-scan sonar bag files")
    db.record_map_dataset(target, label="Survey mosaic GeoTIFF")

    with pytest.raises(
        DoxaBaseError,
        match="derivation_properties must be one of",
    ):
        db.record_map_relationship(
            f"{base}mosaic_from_bags",
            relationship_type="derivation",
            source_datasets=[source],
            target_datasets=[target],
            derivation_properties=[f"{base}RadiometricGainCorrected"],
        )

    assert db.search("RadiometricGainCorrected", graph="map").matches == []
    assert db.validate_graph(scope="all").conforms

