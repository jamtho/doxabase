import warnings
from pathlib import Path

import pytest
from rdflib import Dataset, Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, RDF, XSD

from doxabase import DoxaBase, DoxaBaseError, ImmutableGraphError

ROOT = Path(__file__).resolve().parents[1]
AIS_FIXTURE = ROOT / "examples" / "manifest-prototype-rc" / "ais.trig"
POLYMARKET_FIXTURE = ROOT / "examples" / "manifest-prototype-rc" / "polymarket.trig"
RC = "https://richcanopy.org/ns/rc#"


def test_capsule_creation_seeds_base_graphs(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    overview = db.graph_overview()

    graphs = {graph.name: graph for graph in overview.named_graphs}
    assert graphs["base_ontology"].triple_count == 1139
    assert graphs["base_ontology"].mutable is False
    assert graphs["base_shapes"].triple_count == 1155
    assert graphs["base_shapes"].mutable is False
    assert graphs["map"].mutable is True
    assert graphs["patterns"].mutable is True


def test_immutable_seed_graphs_reject_normal_imports(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(ImmutableGraphError):
        db.import_turtle("@prefix ex: <https://example.test/> . ex:s ex:p ex:o .", graph="base_ontology")


def test_import_trig_maps_graph_iris_to_roles(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    imported = db.import_trig(AIS_FIXTURE)

    assert imported == {
        "evidence": 3,
        "map": 223,
        "observations": 5,
        "ontology": 94,
    }
    assert db.triple_count("map") == 223
    assert db.triple_count("ontology") == 94


def test_import_trig_maps_patterns_graph_role(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    imported = db.import_trig(
        """
        @prefix ex:  <https://example.test/project#> .
        @prefix rc:  <https://richcanopy.org/ns/rc#> .
        @prefix rcg: <https://richcanopy.org/graph/> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        rcg:patterns {
            ex:body_top_pattern a rc:Pattern ;
                rc:summary "body_top behaves like cleaned top-level text." ;
                rc:patternText "Repeated source notes support treating body_top as cleaned message text." ;
                rc:rationale "The README and profile checks describe the same transformation." ;
                rc:patternTarget ex:body_top ;
                rc:evidence ex:body_top_pattern_evidence ;
                rc:synthesizedAt "2026-06-01T00:00:00Z"^^xsd:dateTime .
        }

        rcg:evidence {
            ex:body_top_pattern_evidence a rc:Evidence ;
                rc:summary "README body processing section." ;
                <http://purl.org/dc/terms/source> "tests/test_doxabase_core.py" .
        }
        """
    )

    assert imported["patterns"] > 0
    assert db.validate_graph(scope="all").conforms


def test_export_graph_writes_flattened_turtle(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    export_path = tmp_path / "map.ttl"

    result = db.export_graph(export_path, graphs="map")

    assert result.path == str(export_path)
    assert result.format == "turtle"
    assert result.graphs == ["map"]
    assert result.graph_counts == {"map": db.triple_count("map")}
    assert result.triples == db.triple_count("map")
    assert result.bytes_written == export_path.stat().st_size

    graph = Graph()
    graph.parse(export_path, format="turtle")
    assert len(graph) == db.triple_count("map")
    assert (
        URIRef("https://richcanopy.org/example/manifest/ais#DailyBroadcasts"),
        RDF.type,
        URIRef(RC + "Table"),
    ) in graph

    with pytest.raises(DoxaBaseError, match="already exists"):
        db.export_graph(export_path, graphs="map")


def test_export_trig_preserves_graph_roles_for_round_trip(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    export_path = tmp_path / "bundle.trig"

    result = db.export_trig(export_path)

    assert result.format == "trig"
    assert result.graphs == [
        "ontology",
        "map",
        "observations",
        "patterns",
        "evidence",
        "shapes",
        "history",
    ]
    assert result.graph_counts == {
        graph: db.triple_count(graph) for graph in result.graphs
    }
    assert result.triples == sum(db.triple_count(graph) for graph in result.graphs)

    dataset = Dataset()
    dataset.parse(export_path, format="trig")
    identifiers = {str(context.identifier) for context in dataset.graphs() if len(context)}
    assert "https://richcanopy.org/graph/base_ontology" not in identifiers
    assert "https://richcanopy.org/graph/map" in identifiers
    assert "https://richcanopy.org/graph/observations" in identifiers

    round_trip = DoxaBase.create(tmp_path / "round-trip.sqlite")
    imported = round_trip.import_trig(export_path)
    assert imported["map"] == db.triple_count("map")
    assert imported["observations"] == db.triple_count("observations")
    assert imported["evidence"] == db.triple_count("evidence")
    assert imported["ontology"] == db.triple_count("ontology")


def test_export_trig_all_with_seeds_requires_explicit_seed_import(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    export_path = tmp_path / "all-with-seeds.trig"

    result = db.export_trig(export_path, graphs="all_with_seeds")

    assert result.graphs[:2] == ["base_ontology", "base_shapes"]
    assert result.graph_counts["base_ontology"] == db.triple_count("base_ontology")
    assert result.graph_counts["base_shapes"] == db.triple_count("base_shapes")

    round_trip = DoxaBase.create(tmp_path / "round-trip-with-seeds.sqlite")
    with pytest.raises(ImmutableGraphError, match="base_(ontology|shapes)"):
        round_trip.import_trig(export_path)


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
    assert description.revision_type == RC + "ExportRevision"
    assert description.revision_type_label == "export revision"
    assert description.changed_graphs == ["observations"]
    assert description.included_graphs == ["map", "observations"]
    assert description.export_path == "/tmp/ais-review-bundle.trig"
    assert description.validation_conforms is True
    assert description.validation_result_count == 0
    assert {
        snapshot.graph_role: snapshot.triple_count
        for snapshot in description.graph_snapshots
    } == graph_counts
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


def test_stage_graph_revision_records_reviewable_patch_without_mutating_map(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_map_count = db.triple_count("map")
    addition = """
    @prefix ex: <https://example.test/project#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:Messages a rc:Dataset, rc:Table ;
        rdfs:label "Messages" .
    """

    staged = db.stage_graph_revision(
        summary="Try messages table framing",
        rationale=(
            "Exploratory hunch: treating messages as the map anchor should make "
            "later join reasoning easier."
        ),
        additions=[{"graph": "map", "content": addition}],
        stance="rc:ExploratoryHunch",
        validation_scope="all",
    )

    assert staged.revision_type == RC + "StagedRevision"
    assert staged.revision_stance == RC + "ExploratoryHunch"
    assert staged.changed_graphs == ["map"]
    assert staged.validation_conforms is True
    assert staged.validation_result_count == 0
    assert staged.patches[0].operation == RC + "AdditionPatch"
    assert staged.patches[0].target_graph == "map"
    assert staged.patches[0].patch_role == RC + "FramingPatch"
    assert staged.patches[0].sequence_index == 1
    assert staged.patches[0].triple_count == 3
    assert staged.patches[0].before_triple_count == before_map_count
    assert staged.patches[0].after_triple_count == before_map_count + 3
    assert db.triple_count("map") == before_map_count

    description = db.describe_staged_revision(staged.revision_iri)
    assert description.revision_stance_label == "exploratory hunch"
    assert description.revision_type_label == "staged revision"
    assert description.validation_conforms is True
    assert description.patches[0].patch_role_label == "framing patch"
    assert description.patches[0].sequence_index == 1
    assert description.patches[0].content is not None
    assert "ex:Messages" in description.patches[0].content
    overview = db.graph_overview()
    assert overview.key_counts["graph_revisions"] == 1
    assert overview.key_counts["graph_patches"] == 1
    assert db.validate_graph(scope="all").conforms

    export_path = tmp_path / "staged-review.md"
    export = db.export_staged_revision(staged.revision_iri, export_path)
    assert export.path == str(export_path)
    assert export.format == "markdown"
    export_text = export_path.read_text()
    assert "exploratory hunch" in export_text
    assert "ex:Messages" in export_text


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
    assert "describe_context_slice" in column_support.suggested_next_calls[0]
    assert "https://example.test/project#PriceSnapshots" in (
        column_support.suggested_next_calls[0]
    )
    assert column_support.suggested_next_actions[0].tool_name == (
        "describe_context_slice"
    )
    assert column_support.suggested_next_actions[0].mcp_tool_name == (
        "doxabase.describe_context_slice"
    )
    assert column_support.suggested_next_actions[0].arguments["seed_iris"][0] == (
        "https://example.test/project#PriceSnapshots"
    )
    assert any(
        action.tool_name == "describe_dataset"
        and action.arguments["iri"] == "https://example.test/project#PriceSnapshots"
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
    assert "https://example.test/project#PriceSnapshots" in (
        absent_support.suggested_next_calls[0]
    )
    assert any(
        action.tool_name == "describe_assertion_support"
        and action.arguments["object"] is None
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
        }

        rcg:map {
            ex:PriceSnapshots a rc:Dataset, rc:Table ;
                rdfs:label "Price snapshots" ;
                rc:hasColumn ex:px_price ;
                rc:hasKnownCaveat ex:mixed_price_payload_caveat .

            ex:px_price a rc:Column ;
                rc:columnName "price" ;
                rc:physicalType rc:Varchar ;
                rc:valueType ex:RawPricePayload .

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

    staged_change = db.stage_map_assertion_change(
        subject="https://example.test/project#px_price",
        predicate="rc:physicalType",
        object="rc:Double",
        change_kind="replace",
        rationale=(
            "Testing a tempting but risky coercion so the review bundle should "
            "make the existing VARCHAR and attached lore visible."
        ),
        review_note="This is deliberately staged for review, not applied.",
    )

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
    assert db.triple_count("map") == before_map_count

    description = db.describe_staged_revision(
        staged_change.staged_revision.revision_iri
    )
    assert description.judgement_panel is not None
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
    export_path = tmp_path / "price-change-review.md"
    db.export_staged_revision(staged_change.staged_revision.revision_iri, export_path)
    exported = export_path.read_text()
    assert "## Judgement Panel" in exported
    assert "### Value Type Context" in exported
    assert "Raw price payload" in exported
    assert "Current matches" in exported
    assert "Proposed matches" in exported
    assert "Why Current Value May Be Intentional" in exported


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
    assert check.suggested_next_actions[0].tool_name == "describe_staged_revision"
    assert check.suggested_next_actions[0].mcp_tool_name == (
        "doxabase.describe_staged_revision"
    )
    assert check.suggested_next_actions[0].arguments == {"iri": staged.revision_iri}
    assert check.suggested_next_calls[0].startswith("describe_staged_revision(")
    assert check.suggested_next_actions[-1].tool_name == "apply_staged_revision"

    result = db.apply_staged_revision(staged.revision_iri)

    assert result.staged_revision_iri == staged.revision_iri
    assert result.changed_graphs == ["map"]
    assert result.patches_applied == 1
    assert result.triples_added == 3
    assert result.triples_removed == 0
    assert result.validation_conforms is True
    assert db.triple_count("map") == 3
    messages = db.describe_dataset("https://example.test/project#Messages")
    assert messages.label == "Messages"

    applied = db.describe_graph_revision(result.applied_revision_iri)
    assert applied.revision_type == RC + "AppliedStagedRevision"
    assert applied.revision_type_label == "applied staged revision"
    assert applied.changed_graphs == ["map"]
    assert applied.validation_conforms is True
    assert applied.graph_snapshots[0].graph_role == "map"
    assert applied.graph_snapshots[0].triple_count == 3
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
    assert applied_check.suggested_next_actions[0].tool_name == (
        "describe_graph_revision"
    )


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
    assert db.triple_count("map") == 0
    with pytest.raises(DoxaBaseError, match="Messages"):
        db.describe_dataset("https://example.test/project#Messages")


def test_mixed_staged_revision_uses_recorded_patch_sequence_for_apply_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:Messages a rc:Dataset, rc:Table ;
            rdfs:label "Messages" .
        """,
        graph="map",
    )

    minted_patch_iris = iter(
        [
            "https://example.test/generated/graph-patch/z-addition",
            "https://example.test/generated/graph-patch/a-removal",
            "https://example.test/generated/staged-revision/sequence-test",
        ]
    )

    def mint_iri(kind: str) -> str:
        if kind in {"graph-patch", "staged-revision"}:
            return next(minted_patch_iris)
        return f"https://example.test/generated/{kind}/fallback"

    monkeypatch.setattr(db, "_mint_iri", mint_iri)

    staged = db.stage_graph_revision(
        summary="Swap message label for comment",
        rationale=(
            "Regression test: the removal patch has a lexically earlier IRI than "
            "the addition patch, but apply checks must use recorded preview order."
        ),
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Messages rdfs:comment "Staged explanatory comment." .
                """,
            }
        ],
        removals=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Messages rdfs:label "Messages" .
                """,
            }
        ],
        validation_scope="all",
    )

    description = db.describe_staged_revision(staged.revision_iri)
    assert [patch.sequence_index for patch in description.patches] == [1, 2]
    assert [patch.operation for patch in description.patches] == [
        RC + "AdditionPatch",
        RC + "RemovalPatch",
    ]
    assert description.patches[0].before_triple_count == 3
    assert description.patches[0].after_triple_count == 4
    assert description.patches[1].before_triple_count == 4
    assert description.patches[1].after_triple_count == 3

    check = db.check_staged_revision_apply(staged.revision_iri)
    assert check.can_apply is True
    assert check.conflicts == []
    assert [patch.current_triple_count for patch in check.patch_checks] == [3, 4]


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
    assert check.review_recommended is False
    assert check.blocking_reasons == ["target_count_drift"]
    assert check.recommended_resolution is not None
    assert "Restage the proposal" in check.recommended_resolution
    assert check.summary.startswith("Blocked by 1 conflict(s); first conflict:")
    assert check.validation_conforms is None
    assert check.validation_skipped_reason == "conflicts_present"
    assert len(check.conflicts) == 1
    assert len(check.count_drifts) == 1
    assert check.count_drifts[0].target_graph == "map"
    assert check.count_drifts[0].expected_before_triple_count == 0
    assert check.count_drifts[0].current_triple_count == db.triple_count("map")
    assert check.count_drifts[0].delta == db.triple_count("map")
    assert check.count_drifts[0].exact_changed_triples_available is False
    assert check.count_drifts[0].patch_operation == RC + "AdditionPatch"
    assert check.count_drifts[0].patch_triples_checked == 1
    assert check.count_drifts[0].patch_triples_currently_present == 0
    assert check.count_drifts[0].patch_triples_currently_absent == 1
    assert check.count_drifts[0].patch_triple_status == "all_patch_triples_absent"
    assert "unrelated changed triples" in check.count_drifts[0].note

    export_path = tmp_path / "stale-staged-review.md"
    db.export_staged_revision(staged.revision_iri, export_path)
    export_text = export_path.read_text(encoding="utf-8")

    assert "## Current Apply Check" in export_text
    assert "- Status: conflict" in export_text
    assert "- Decision: restage_against_current_graph" in export_text
    assert "- Can apply: False" in export_text
    assert "- Blocking reasons: target_count_drift" in export_text
    assert "- Validation skipped: conflicts_present" in export_text
    assert "### Count Drift" in export_text
    assert "| Patch | Graph | Expected before | Current | Delta |" in export_text
    assert "| map | 0 |" in export_text
    assert f"| 0 | {db.triple_count('map')} |" in export_text
    assert "all_patch_triples_absent" in export_text
    assert "### Suggested Next Calls" in export_text
    assert "restage_staged_revision" in export_text
    assert "expected 0 triples before patch" in check.conflicts[0]
    assert check.patch_checks[0].can_apply is False
    assert check.suggested_next_actions[0].tool_name == "describe_staged_revision"
    assert check.suggested_next_calls[0].startswith("describe_staged_revision(")
    assert check.suggested_next_actions[-1].tool_name == "restage_staged_revision"

    with pytest.raises(DoxaBaseError, match="Staged revision cannot be applied"):
        db.apply_staged_revision(staged.revision_iri)

    with pytest.raises(DoxaBaseError, match="Messages"):
        db.describe_dataset("https://example.test/project#Messages")


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
    restaged_description = db.describe_staged_revision(restaged.revision_iri)
    assert restaged_description.restaged_from is not None
    assert restaged_description.restaged_from.iri == staged.revision_iri
    assert restaged_description.review_note == (
        "Original note should travel with the refreshed proposal."
    )
    assert "Restaged stale revision" in (restaged_description.rationale or "")

    fresh_check = db.check_staged_revision_apply(restaged.revision_iri)
    assert fresh_check.can_apply is True
    assert fresh_check.status == "ready"
    assert fresh_check.blocking_reasons == []

    stale_check_after = db.check_staged_revision_apply(staged.revision_iri)
    assert stale_check_after.status == "conflict"

    result = db.apply_staged_revision(restaged.revision_iri)
    assert result.triples_added == 1
    assert db.describe_dataset("https://example.test/project#Messages").iri == (
        "https://example.test/project#Messages"
    )


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
    assert staged_listing.revisions[0].iri == staged.revision_iri
    assert staged_listing.revisions[0].record_kind == "staged_patch"
    assert staged_listing.revisions[0].revision_type == RC + "StagedRevision"
    assert staged_listing.revisions[0].revision_type_label == "staged revision"
    assert staged_listing.revisions[0].has_patch_payload is True
    assert staged_listing.revisions[0].patch_count == 1
    assert staged_listing.revisions[0].application_status == "ready"
    assert staged_listing.revisions[0].application_can_apply is True
    assert staged_listing.revisions[0].suggested_next_actions

    applied = db.apply_staged_revision(
        staged.revision_iri,
        created_at="2026-06-01T10:01:00Z",
    )
    listing = db.list_graph_revisions(include_apply_checks=True)

    assert listing.count == 2
    by_iri = {item.iri: item for item in listing.revisions}
    assert by_iri[staged.revision_iri].applied_by == applied.applied_revision_iri
    assert by_iri[staged.revision_iri].application_status == "already_applied"
    assert by_iri[applied.applied_revision_iri].applies_staged_revision == (
        staged.revision_iri
    )
    assert by_iri[applied.applied_revision_iri].record_kind == "applied_event"
    assert by_iri[applied.applied_revision_iri].has_patch_payload is False
    assert by_iri[applied.applied_revision_iri].patch_count == 0
    assert by_iri[applied.applied_revision_iri].application_status == "applied_event"
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

    drift_listing = db.list_graph_revisions(include_apply_checks=True)
    drift_by_iri = {item.iri: item for item in drift_listing.revisions}
    stale_item = drift_by_iri[stale.revision_iri]
    assert stale_item.application_status == "conflict"
    assert stale_item.application_blocking_reasons == ["target_count_drift"]
    assert stale_item.application_count_drifts[0].target_graph == "map"
    assert stale_item.suggested_next_actions[-1].tool_name == "restage_staged_revision"
    assert stale_item.restaged_by == restaged.revision_iri
    assert drift_by_iri[restaged.revision_iri].restaged_from == stale.revision_iri


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
    assert check.suggested_next_actions[0].tool_name == "describe_staged_revision"

    with pytest.raises(DoxaBaseError, match="Applying staged revision would fail"):
        db.apply_staged_revision(staged.revision_iri)


def test_stage_graph_revision_rejects_immutable_seed_targets(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(ImmutableGraphError, match="base_ontology"):
        db.stage_graph_revision(
            summary="Invalid staged seed patch",
            rationale="Project-level staged revisions must not target shipped seeds.",
            additions=[
                {
                    "graph": "base_ontology",
                    "content": (
                        "@prefix ex: <https://example.test/> . "
                        "ex:s ex:p ex:o ."
                    ),
                }
            ],
        )


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

    assert draft.summary == "Explore identity-ladder modelling"
    assert draft.anchors == [
        observation.observation_iri,
        "https://example.test/project#Messages",
    ]
    assert len(draft.staged_revisions) == 2
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
    assert export.bytes_written == len(exported.encode("utf-8"))
    assert exported.startswith("# Identity ladder alternatives\n")
    assert "## Review Summary" in exported
    assert "Prefer the pattern-first framing for now" in exported
    assert "## Summary" in exported
    assert "Apply status" in exported
    assert "review_then_apply" in exported
    assert "Recommendation" in exported
    assert "Preferred for now." in exported
    assert "## Review Notes" in exported
    assert "This keeps the bold hunch alive without forcing the map." in exported
    assert "| 1 | Explore identity-ladder modelling: Project vocabulary term" in exported
    assert "| 2 | Explore identity-ladder modelling: Pattern first" in exported
    assert "## Revision 1: Explore identity-ladder modelling: Project vocabulary term" in exported
    assert "## Revision 2: Explore identity-ladder modelling: Pattern first" in exported
    assert "## Alternative To" in exported
    assert "IdentityLadderPattern" in exported


def test_stage_pattern_promotion_rolls_pattern_support_into_staged_revision(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/ais#"
    mmsi_column = f"{base}broadcasts__mmsi"
    caveat = f"{base}mmsi_operational_identity_caveat"
    observation = db.record_observation(
        "MMSI appears repeatedly as a useful but imperfect grouping key.",
        observed_column=mmsi_column,
        evidence_summary="Synthetic profile note for pattern promotion.",
        evidence_sources=["test://mmsi-profile"],
    )
    claim = db.record_claim_observation(
        summary="MMSI identity caveat.",
        claim_text="MMSI is useful for grouping broadcasts but is not stable vessel identity.",
        claim_kind="rc:CaveatClaim",
        claim_targets=[mmsi_column],
        evidence_sources=["test://mmsi-caveat"],
    )
    pattern = db.record_pattern(
        summary="MMSI is operational identity, not vessel identity.",
        pattern_text=(
            "Repeated checks support treating MMSI as an operational grouping key "
            "with identity caveats."
        ),
        rationale=(
            "The observation and claim agree that MMSI is useful but should not "
            "be promoted as a stable vessel identifier."
        ),
        pattern_targets=[mmsi_column],
        supporting_observations=[observation.observation_iri],
        supporting_claims=[claim.claim_iri],
        evidence_iri=claim.evidence_iri,
        map_implications=[caveat],
        confidence="rc:HighConfidence",
        pattern_stability="rc:RepeatedPattern",
    )
    before_map_count = db.triple_count("map")
    before_ontology_count = db.triple_count("ontology")

    draft = db.stage_pattern_promotion(
        patterns=[pattern.pattern_iri],
        summary="Promote MMSI caveat from pattern",
        intent="Preserve the MMSI hunch as current map caveat plus a project term.",
        rationale=(
            "This is a cautious promotion: the strong pattern becomes a caveat, "
            "not a hard identity-key assertion."
        ),
        shared_additions=[
            {
                "graph": "ontology",
                "content": """
                    @prefix ais: <https://example.test/ais#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ais:OperationalIdentityCaveat a rdfs:Class ;
                        rdfs:subClassOf rc:KnownCaveat ;
                        rdfs:label "Operational identity caveat" .
                """,
            }
        ],
        framings=[
            {
                "label": "Map caveat",
                "graph": "map",
                "content": f"""
                    @prefix ais: <https://example.test/ais#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ais:mmsi_operational_identity_caveat
                        a rc:KnownCaveat, ais:OperationalIdentityCaveat ;
                        rdfs:label "MMSI operational identity caveat" ;
                        rdfs:comment "MMSI can group broadcasts but should not be treated as stable vessel identity." ;
                        rc:caveatDescription "MMSI can group broadcasts but should not be treated as stable vessel identity." ;
                        rc:impact "Identity-level analysis should avoid assuming one MMSI equals one vessel." ;
                        rc:severity rc:Moderate .

                    <{mmsi_column}> rc:hasKnownCaveat ais:mmsi_operational_identity_caveat .
                """,
                "review_note": "Pattern support is strong, but the map change remains staged.",
            }
        ],
        validation_scope="all",
    )

    assert draft.summary == "Promote MMSI caveat from pattern"
    assert draft.intent == (
        "Preserve the MMSI hunch as current map caveat plus a project term."
    )
    assert draft.anchors == [pattern.pattern_iri, mmsi_column, caveat]
    assert draft.framings[0].target_graphs == ["ontology", "map"]
    assert draft.framings[0].validation_conforms is True
    assert db.triple_count("map") == before_map_count
    assert db.triple_count("ontology") == before_ontology_count

    staged = db.describe_staged_revision(draft.staged_revisions[0].revision_iri)
    assert staged.revision_stance == RC + "CandidateRevision"
    assert staged.rationale is not None
    assert "Selected pattern support" in staged.rationale
    assert "Promotion rationale" in staged.rationale
    assert {pattern_summary.iri for pattern_summary in staged.supporting_patterns} == {
        pattern.pattern_iri
    }
    assert {
        observation_summary.iri
        for observation_summary in staged.supporting_observations
    } == {observation.observation_iri}
    assert {claim_summary.iri for claim_summary in staged.supporting_claims} == {
        claim.claim_iri
    }
    assert {evidence_summary.iri for evidence_summary in staged.evidence} == {
        claim.evidence_iri
    }
    assert {anchor.iri for anchor in staged.revision_anchors} == {
        pattern.pattern_iri,
        mmsi_column,
        caveat,
    }


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


def test_list_entities_returns_tables_from_map(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    db.import_trig(POLYMARKET_FIXTURE)

    result = db.list_entities(type="rc:Table", graph="map", limit=20)
    labels = {row.label for row in result.entities}

    assert "AIS Daily Broadcast Positions" in labels
    assert "AIS Daily Vessel Index" in labels
    assert "Gamma Market Snapshots" in labels
    assert "Trade Events" in labels


def test_describe_dataset_returns_bounded_table_context(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    description = db.describe_dataset(
        "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"
    )

    assert description.label == "AIS Daily Broadcast Positions"
    assert "https://richcanopy.org/ns/rc#Table" in description.types
    assert description.row_semantics is not None
    assert description.row_semantics.iri == RC + "EventRow"
    assert description.schema_stability is not None
    assert description.schema_stability.iri == RC + "FixedSchema"
    assert description.layout_verification_status is None
    assert description.layout_verification_note is None
    assert description.path_templates == ["broadcasts/{year}/ais-{date}.parquet"]
    assert description.partition_schemes[0].layout_verification_status is not None
    assert description.partition_schemes[0].layout_verification_status.iri == (
        RC + "GeneratedFromManifestLayout"
    )
    assert description.partition_schemes[0].layout_verification_note is not None
    assert "verify against storage listing" in (
        description.partition_schemes[0].layout_verification_note
    )
    assert len(description.storage_accesses) == 1
    storage_access = description.storage_accesses[0]
    assert storage_access.storage_protocol is not None
    assert storage_access.storage_protocol.label == "S3-compatible object storage"
    assert storage_access.storage_root == "s3://ais-noaa/"
    assert storage_access.endpoint_profile == "local-minio"
    assert storage_access.bucket_name == "ais-noaa"
    assert storage_access.region == "local"
    assert storage_access.path_style_access is True
    assert storage_access.credential_reference == "profile:ais-readonly"
    assert storage_access.access_mode is not None
    assert storage_access.access_mode.label == "read-only"
    assert {column.column_name for column in description.columns} >= {
        "mmsi",
        "timestamp",
        "h3_res15",
    }
    mmsi = next(column for column in description.columns if column.column_name == "mmsi")
    assert mmsi.physical_type is not None
    assert mmsi.physical_type.label == "INTEGER"
    assert mmsi.value_type is not None
    assert mmsi.value_type.label == "Maritime Mobile Service Identity"
    assert mmsi.nullable is True
    caveat_text = " ".join(caveat.description or "" for caveat in description.caveats)
    assert "MMSI does not reliably identify a single vessel" in caveat_text
    assert any(caveat.severity is not None for caveat in description.caveats)
    assert description.upstream_caveats == []
    assert any(
        provenance.description
        and "NOAA Marine Cadastre AIS data" in provenance.description
        for provenance in description.provenance
    )
    assert any(
        relationship.relationship_kind == RC + "Derivation"
        and relationship.derived_columns
        and relationship.derived_columns[0].iri
        == "https://richcanopy.org/example/manifest/ais#bc_timestamp"
        and relationship.derived_columns[0].column_name == "timestamp"
        and relationship.derived_columns[0].owning_dataset_label
        == "AIS Daily Broadcast Positions"
        for relationship in description.relationships
    )
    aggregation = next(
        relationship
        for relationship in description.relationships
        if relationship.relationship_kind == RC + "Aggregation"
    )
    assert aggregation.target_dataset is not None
    assert aggregation.target_dataset.iri == (
        "https://richcanopy.org/example/manifest/ais#DailyIndex"
    )
    assert [column.column_name for column in aggregation.group_by_columns] == ["mmsi"]
    aggregate_mapping = next(
        mapping
        for mapping in aggregation.aggregated_columns
        if mapping.target_column is not None
        and mapping.target_column.column_name == "distance_m"
    )
    assert {column.column_name for column in aggregate_mapping.source_columns} == {
        "latitude",
        "longitude",
    }
    assert aggregate_mapping.aggregation_function is not None
    assert aggregate_mapping.aggregation_function.label == (
        "Haversine distance from first to last position"
    )
    assert aggregate_mapping.within_group_ordering is not None
    assert aggregate_mapping.within_group_ordering.column_name == "timestamp"
    assert any(
        caveat.description
        and "MMSI does not reliably identify a single vessel" in caveat.description
        for caveat in aggregation.source_caveats
    )
    assert any(
        related.iri == "https://richcanopy.org/example/manifest/ais#DailyIndex"
        and related.relationship == "source_of_aggregation"
        for related in description.related_datasets
    )

    index_description = db.describe_dataset(
        "https://richcanopy.org/example/manifest/ais#DailyIndex"
    )
    assert index_description.layout_verification_status is not None
    assert index_description.layout_verification_status.iri == RC + "UnverifiedLayout"
    assert index_description.layout_verification_note is not None
    assert "index/{year}/ais-{date}.parquet" in (
        index_description.layout_verification_note
    )
    assert any(
        warning.code == "layout_needs_verification"
        and warning.resource is not None
        and warning.resource.iri
        == "https://richcanopy.org/example/manifest/ais#DailyIndex"
        for warning in index_description.operational_warnings
    )
    assert index_description.caveats == []
    assert any(
        caveat.description
        and "MMSI does not reliably identify a single vessel" in caveat.description
        for caveat in index_description.upstream_caveats
    )
    broadcast_group = next(
        group
        for group in index_description.related_dataset_groups
        if group.iri == "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"
    )
    broadcast_reason = next(
        reason
        for reason in broadcast_group.reasons
        if reason.relationship == "aggregated_from"
    )
    assert any(
        caveat.impact and "Grouping by MMSI may conflate" in caveat.impact
        for caveat in broadcast_reason.source_caveats
    )

    wrong_predicate_support = db.describe_assertion_support(
        "https://richcanopy.org/example/manifest/ais#DailyIndex",
        "rc:hasPartitionScheme",
        "https://richcanopy.org/example/manifest/ais#daily_date_partition",
        object_kind="iri",
    )
    assert wrong_predicate_support.assertion_present is False
    assert wrong_predicate_support.absence_note is not None
    assert "the requested predicate is absent on this subject" in (
        wrong_predicate_support.absence_note
    )
    assert "Nearby predicates on the same subject include" in (
        wrong_predicate_support.absence_note
    )
    assert "rc:partitionedBy" in wrong_predicate_support.absence_note
    partition_hint = next(
        hint
        for hint in wrong_predicate_support.predicate_hints
        if hint.predicate == RC + "partitionedBy"
    )
    assert partition_hint.predicate_curie == "rc:partitionedBy"
    assert partition_hint.triple_count == 1
    assert partition_hint.sample_values[0].value == (
        "https://richcanopy.org/example/manifest/ais#daily_date_partition"
    )


def test_describe_query_context_reports_planning_metadata_and_issues(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    context = db.describe_query_context(
        "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"
    )

    assert context.dataset.label == "AIS Daily Broadcast Positions"
    assert context.readiness == "needs_review"
    assert context.path_templates == ["broadcasts/{year}/ais-{date}.parquet"]
    assert context.storage_accesses[0].endpoint_profile == "local-minio"
    assert context.storage_accesses[0].credential_reference == "profile:ais-readonly"
    assert {column.column_name for column in context.columns} >= {
        "mmsi",
        "timestamp",
    }
    assert any(
        issue.code == "layout_needs_verification"
        and issue.severity == "warning"
        and issue.resource is not None
        and issue.resource.iri
        == "https://richcanopy.org/example/manifest/ais#daily_date_partition"
        and "verify against storage listing" in issue.message
        for issue in context.issues
    )
    assert "non-secret planning metadata" in context.planning_notes[0]


def test_describe_query_context_reports_missing_planning_metadata(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Messages"
    db.record_map_dataset(dataset, label="Messages", is_table=True)

    context = db.describe_query_context(dataset)

    assert context.readiness == "insufficient_metadata"
    assert {issue.code for issue in context.issues} >= {
        "missing_path_template",
        "missing_storage_access",
        "missing_physical_layout",
    }
    assert [issue.severity for issue in context.issues[:2]] == ["error", "error"]


def test_describe_dataset_reports_missing_dataset(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    with pytest.raises(DoxaBaseError, match="was not found"):
        db.describe_dataset("https://richcanopy.org/example/manifest/ais#MissingDataset")


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
    assert description.partition_schemes[0].partition_column is not None
    assert description.partition_schemes[0].partition_column.iri == doc_id
    assert description.partition_schemes[0].granularity is not None
    assert description.partition_schemes[0].granularity.iri == RC + "Daily"
    assert description.partition_schemes[0].path_template == (
        "data/parquet/dt={date}/eml_messages.parquet"
    )
    assert description.partition_schemes[0].redundant_partition_key is not None
    assert description.partition_schemes[0].redundant_partition_key.iri == doc_id
    assert description.partition_schemes[0].layout_verification_status is not None
    assert description.partition_schemes[0].layout_verification_status.iri == (
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


def test_describe_dataset_links_relevant_patterns(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/enron#"
    messages = f"{base}eml_messages"
    doc_id = f"{base}eml_messages__doc_id"
    caveat = f"{base}eml_messages_id_caveat"
    claim = f"{base}claim_doc_id_join"

    db.record_map_dataset(
        messages,
        label="EML messages",
        is_table=True,
        path_templates=["data/messages.parquet"],
    )
    db.record_map_column(
        doc_id,
        table_iri=messages,
        column_name="doc_id",
        physical_type="rc:Varchar",
    )
    db.record_map_caveat(
        caveat,
        description="Message identifiers are stable within this source but not globally.",
        targets=[messages],
    )
    claim_result = db.record_claim_observation(
        summary="doc_id behaves as the message entity key.",
        claim_text="doc_id behaves as the message entity key.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=[doc_id],
        claim_iri=claim,
        evidence_summary="Unit test evidence.",
        evidence_sources=["tests/test_doxabase_core.py"],
    )
    pattern_result = db.record_pattern(
        summary="doc_id is the stable message identity handle.",
        pattern_text="Use doc_id as the stable message identity handle.",
        rationale="A claim about the table column supports this reader protocol.",
        pattern_targets=[messages, caveat],
        supporting_claims=[claim_result.claim_iri],
    )

    description = db.describe_dataset(messages)

    assert [pattern.iri for pattern in description.linked_patterns] == [
        pattern_result.pattern_iri
    ]
    assert description.linked_patterns[0].label == (
        "doc_id is the stable message identity handle."
    )
    assert description.linked_patterns[0].description == (
        "Use doc_id as the stable message identity handle."
    )
    assert len(description.linked_pattern_reasons) == 1
    pattern_reason = description.linked_pattern_reasons[0]
    assert pattern_reason.iri == pattern_result.pattern_iri
    assert pattern_reason.pattern_iri == pattern_result.pattern_iri
    assert pattern_reason.pattern_text == (
        "Use doc_id as the stable message identity handle."
    )
    assert pattern_reason.rationale == (
        "A claim about the table column supports this reader protocol."
    )
    assert {
        (match.match_type, match.matched_resource.iri)
        for match in pattern_reason.matches
    } == {
        ("pattern_target", caveat),
        ("pattern_target", messages),
        ("supporting_claim_target", doc_id),
    }
    assert pattern_reason.match_group_count == 3
    assert pattern_reason.raw_match_count == 3
    assert pattern_reason.relevance_tier_counts == {
        "direct": 2,
        "claim_supported": 1,
    }
    assert {
        (group.relevance_tier, group.matched_resource.iri)
        for group in pattern_reason.match_groups
    } == {
        ("direct", caveat),
        ("direct", messages),
        ("claim_supported", doc_id),
    }
    caveat_group = next(
        group
        for group in pattern_reason.match_groups
        if group.matched_resource.iri == caveat
    )
    assert caveat_group.matched_resource_kind == "KnownCaveat"
    assert caveat_group.matched_resource.description == (
        "Message identifiers are stable within this source but not globally."
    )
    direct_group = next(
        group
        for group in pattern_reason.match_groups
        if group.matched_resource.iri == messages
    )
    assert direct_group.matched_resource_kind == "Table"
    assert direct_group.route_labels == ["direct pattern target"]
    claim_group = next(
        group
        for group in pattern_reason.match_groups
        if group.matched_resource.iri == doc_id
    )
    assert claim_group.matched_resource_kind == "Column"
    assert claim_group.route_labels == ["via supporting claim target"]
    assert claim_group.supporting_claims[0].iri == claim_result.claim_iri
    claim_match = next(
        match
        for match in pattern_reason.matches
        if match.match_type == "supporting_claim_target"
    )
    assert claim_match.supporting_claim is not None
    assert claim_match.supporting_claim.iri == claim_result.claim_iri
    assert claim_match.matched_resource.column_name == "doc_id"
    assert description.path_templates == ["data/messages.parquet"]


def test_describe_context_slice_returns_route_explained_dataset_brief(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/enron#"
    messages = f"{base}eml_messages"
    doc_id = f"{base}eml_messages__doc_id"
    claim = f"{base}claim_doc_id_join"

    db.record_map_dataset(
        messages,
        label="EML messages",
        description="Parsed email message records.",
        is_table=True,
        path_templates=["data/messages.parquet"],
        layout_verification_status="rc:CandidateLayout",
        layout_verification_note="Path pattern is plausible but not verified.",
    )
    db.record_map_column(
        doc_id,
        table_iri=messages,
        column_name="doc_id",
        physical_type="rc:Varchar",
    )
    claim_result = db.record_claim_observation(
        summary="doc_id behaves as the message entity key.",
        claim_text="doc_id behaves as the message entity key.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=[doc_id],
        claim_iri=claim,
        evidence_summary="Unit test evidence.",
        source_path="tests/test_doxabase_core.py",
        source_kind="rc:DocumentationSource",
    )
    pattern_result = db.record_pattern(
        summary="doc_id is the stable message identity handle.",
        pattern_text="Use doc_id as the stable message identity handle.",
        rationale="A claim about the table column supports this reader protocol.",
        pattern_targets=[messages],
        supporting_claims=[claim_result.claim_iri],
    )

    context_slice = db.describe_context_slice(
        [messages],
        profile="dataset_brief",
        include_trig=True,
        max_triples=200,
    )

    assert context_slice.profile == "dataset_brief"
    assert context_slice.seeds[0].iri == messages
    assert context_slice.dataset_contexts[0].iri == messages
    assert context_slice.pattern_contexts[0].iri == pattern_result.pattern_iri
    assert context_slice.truncated is False
    assert context_slice.truncation_scope == "triples_only"
    assert context_slice.resource_count == len(context_slice.resources)
    assert context_slice.triple_count <= 200
    assert context_slice.returned_triple_count == context_slice.triple_count
    assert context_slice.candidate_triple_count == context_slice.triple_count
    assert context_slice.omitted_triple_count == 0
    assert context_slice.graph_counts["map"] >= 1
    assert context_slice.graph_counts["patterns"] >= 1
    assert context_slice.graph_counts["observations"] >= 1
    assert context_slice.graph_counts["evidence"] >= 1
    assert context_slice.route_counts["dataset_column"] == 1
    assert context_slice.route_counts["layout_verification_status"] == 1
    assert context_slice.route_counts["linked_pattern"] == 1
    assert context_slice.route_counts["supporting_claim"] >= 1
    assert context_slice.reading_order[0].startswith("Start with seeds")
    route_legend = {row.route: row for row in context_slice.route_legend}
    assert route_legend["seed"].count == 1
    assert route_legend["seed"].priority == 0
    assert route_legend["seed"].meaning == (
        "The resource the caller asked about directly."
    )
    assert route_legend["dataset_column"].count == 1
    assert route_legend["layout_verification_status"].meaning == (
        "A verification-status term attached to dataset, layout, storage, or partition path metadata."
    )

    resources = {resource.iri: resource for resource in context_slice.resources}
    assert messages in resources
    assert doc_id in resources
    assert RC + "CandidateLayout" in resources
    assert pattern_result.pattern_iri in resources
    assert claim_result.claim_iri in resources
    assert claim_result.evidence_iri in resources
    assert resources[messages].referenced_only is False
    assert resources[messages].primary_route.route == "seed"
    assert any(route.route == "seed" for route in resources[messages].routes)
    assert any(route.route == "dataset_column" for route in resources[doc_id].routes)
    assert any(
        route.route == "layout_verification_status"
        for route in resources[RC + "CandidateLayout"].routes
    )
    assert any(
        route.route == "linked_pattern"
        for route in resources[pattern_result.pattern_iri].routes
    )

    assert context_slice.trig is not None
    dataset = Dataset()
    dataset.parse(data=context_slice.trig, format="trig")
    graph_iris = {str(graph.identifier) for graph in dataset.graphs() if len(graph)}
    assert "https://richcanopy.org/graph/map" in graph_iris
    assert "https://richcanopy.org/graph/patterns" in graph_iris


def test_deep_lore_context_slice_reports_absent_lore_layer(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#plain_table"
    db.record_map_dataset(
        dataset,
        label="Plain table",
        description="A table with map context but no recorded lore.",
        is_table=True,
        path_templates=["data/plain.parquet"],
    )

    context_slice = db.describe_context_slice([dataset], profile="deep_lore")

    assert context_slice.pattern_contexts == []
    assert context_slice.route_counts["seed_dataset"] == 1
    assert context_slice.warnings == [
        "deep_lore found no claims, patterns, reconsiderations, "
        "evidence, or revision history beyond map context for these seeds."
    ]


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


def test_search_finds_fixture_literals_with_resource_context(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    results = db.search("MMSI vessel", graph="map", limit=10)

    assert results.query == "MMSI vessel"
    assert results.graph == "map"
    assert results.limit == 10
    match = next(
        result
        for result in results.matches
        if "MMSI does not reliably identify" in result.text
    )
    assert match.graph == "map"
    assert match.predicate == RC + "caveatDescription"
    assert "MMSI" in match.snippet


def test_search_falls_back_to_same_dataset_co_mentions(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(POLYMARKET_FIXTURE)

    results = db.search("outcomes clobTokenIds", graph="map", limit=10)
    matched_iris = {match.iri for match in results.matches}

    assert (
        "https://richcanopy.org/example/manifest/polymarket#mkt_outcomes"
        in matched_iris
    )
    assert (
        "https://richcanopy.org/example/manifest/polymarket#mkt_clob_token_ids"
        in matched_iris
    )
    assert {match.graph for match in results.matches} == {"map"}


def test_search_finds_recorded_observation_and_evidence(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    record = db.record_observation(
        summary="Handover lore says this hidden join relies on source ordering.",
        evidence_summary="Notebook evidence captured during dataset takeover.",
        evidence_sources=["tests/test_doxabase_core.py"],
    )

    observations = db.search("hidden join", graph="observations")
    evidence = db.search("notebook takeover", graph="evidence")

    assert observations.matches[0].iri == record.observation_iri
    assert observations.matches[0].label == (
        "Handover lore says this hidden join relies on source ordering."
    )
    assert observations.matches[0].types == [RC + "Observation"]
    assert evidence.matches[0].iri == record.evidence_iri
    assert evidence.matches[0].graph == "evidence"


def test_scratch_capsule_observation_write_recovers_search_index(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "doxabase-enron-fieldtrial.sqlite")
    db._conn.execute("DROP TABLE literal_search_data")
    db._conn.commit()

    record = db.record_observation(
        summary="Enron EML messages are the richer analyst-facing table.",
        evidence_summary="README documents EML parsing as including bodies and reply analysis.",
        evidence_sources=[
            "/home/james/github.com/jamtho/enron-emails/README.md",
        ],
    )

    assert record.evidence_iri is not None
    assert db.search("richer analyst", graph="observations").matches[0].iri == (
        record.observation_iri
    )
    assert db.search("reply analysis", graph="evidence").matches[0].iri == (
        record.evidence_iri
    )


def test_search_index_survives_repeated_rebuilds_after_scratch_import(
    tmp_path: Path,
) -> None:
    capsule = tmp_path / "capsule.sqlite"
    db = DoxaBase.create(capsule)
    db.import_turtle(
        """
        @prefix ex: <https://example.test/> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:EnronEmails a rc:Dataset ;
            rdfs:label "Enron Emails" ;
            rc:summary "README-derived scratch map for the Enron email corpus." .
        """,
        graph="map",
    )
    db.record_observation(
        summary="Enron EML messages include body_top and reply depth fields.",
        evidence_summary="README EML pipeline section.",
        evidence_sources=["/home/james/github.com/jamtho/enron-emails/README.md"],
    )
    db.close()

    reopened = DoxaBase(capsule)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        record = reopened.record_observation(
            summary="Enron embeddings join to messages by doc_id.",
            evidence_summary="README embeddings section.",
            evidence_sources=[
                "/home/james/github.com/jamtho/enron-emails/README.md",
            ],
        )

    runtime_warnings = [
        warning
        for warning in caught
        if issubclass(warning.category, RuntimeWarning)
    ]
    assert runtime_warnings == []
    assert reopened.search("doc_id", graph="observations").matches[0].iri == (
        record.observation_iri
    )
    reopened.close()


def test_agent_authored_observation_rdf_imports_and_validates(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    imported = db.import_trig(
        """
        @prefix enron: <https://example.test/enron#> .
        @prefix rc:    <https://richcanopy.org/ns/rc#> .
        @prefix rcg:   <https://richcanopy.org/graph/> .
        @prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .

        rcg:map {
            enron:eml_messages a rc:Table ;
                rdfs:label "eml_messages.parquet" .

            enron:body_top a rc:Column ;
                rc:columnName "body_top" .
        }

        rcg:observations {
            enron:obs_body_top_transformation a rc:Observation ;
                rc:summary "body_top is cleaned message text, not raw email text." ;
                rc:observedAt "2026-05-31T00:00:00Z"^^xsd:dateTime ;
                rc:observedAsset enron:eml_messages ;
                rc:observationStatus rc:Checked ;
                rc:evidence enron:evidence_readme_body_processing ;
                rc:hasClaim enron:claim_body_top_transformation .

            enron:claim_body_top_transformation a rc:Claim ;
                rc:claimKind rc:TransformationClaim ;
                rc:claimTarget enron:body_top ;
                rc:claimText "The body_top column stores text above reply separators after footer stripping." ;
                rc:confidence rc:HighConfidence ;
                rc:observationStatus rc:Checked ;
                rc:proposedAssertion enron:body_top_transformation_caveat .
        }

        rcg:evidence {
            enron:evidence_readme_body_processing a rc:Evidence ;
                rc:summary "Enron README body processing section." ;
                rc:sourceSpan enron:span_readme_body_processing .

            enron:span_readme_body_processing a rc:SourceSpan ;
                rc:sourceKind rc:DocumentationSource ;
                rc:sourcePath "/home/james/github.com/jamtho/enron-emails/README.md" ;
                rc:sourceSection "Body processing" ;
                rc:startLine 186 ;
                rc:endLine 191 .
        }
        """
    )

    assert imported["observations"] > 0
    assert imported["evidence"] > 0
    assert db.validate_graph(scope="all").conforms
    assert db.search("reply separators", graph="observations").matches
    assert db.search("Body processing", graph="evidence").matches


def test_agent_authored_observation_rdf_requires_evidence(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(
        """
        @prefix enron: <https://example.test/enron#> .
        @prefix rc:    <https://richcanopy.org/ns/rc#> .
        @prefix rcg:   <https://richcanopy.org/graph/> .

        rcg:observations {
            enron:obs_without_evidence a rc:Observation ;
                rc:summary "This observation should fail stricter observation validation." .
        }
        """
    )

    validation = db.validate_graph(scope="all")

    assert not validation.conforms
    assert "Observation resources should link to at least one named Evidence" in (
        validation.report_text
    )


def test_record_claim_observation_writes_common_rdf_pattern(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    result = db.record_claim_observation(
        summary="The Enron body_top column is transformed message text.",
        claim_text="body_top stores text above reply separators after footer stripping.",
        claim_kind="rc:TransformationClaim",
        claim_targets=["https://example.test/enron#eml_messages_body_top"],
        observed_asset="https://example.test/enron#eml_messages",
        observed_at="2026-05-31T00:00:00Z",
        observed_by="urn:doxabase:test-agent",
        evidence_summary="README body processing section.",
        source_path="/home/james/github.com/jamtho/enron-emails/README.md",
        source_section="Body processing",
        start_line=186,
        end_line=191,
        source_kind="rc:DocumentationSource",
        confidence="rc:HighConfidence",
        observation_status="rc:Checked",
        proposed_assertions=[
            "https://example.test/enron#body_top_transformation_caveat",
        ],
    )

    assert result.claim_iri.startswith(
        "https://richcanopy.org/doxabase/generated/claim/"
    )
    assert result.source_span_iri is not None
    assert result.observation_triples > 0
    assert result.evidence_triples > 0
    assert db.validate_graph(scope="all").conforms

    claims = db.list_entities(
        type="rc:Claim",
        graph="observations",
        text="reply separators",
    )
    assert [claim.iri for claim in claims.entities] == [result.claim_iri]
    assert claims.entities[0].label == (
        "body_top stores text above reply separators after footer stripping."
    )

    context = db.describe_resource(result.claim_iri, graph="observations")
    outgoing_predicates = {triple.predicate for triple in context.outgoing}

    assert context.label == (
        "body_top stores text above reply separators after footer stripping."
    )
    assert "https://richcanopy.org/ns/rc#claimKind" in outgoing_predicates
    assert "https://richcanopy.org/ns/rc#claimTarget" in outgoing_predicates
    assert any(
        triple.subject == result.observation_iri
        and triple.predicate == "https://richcanopy.org/ns/rc#hasClaim"
        for triple in context.incoming
    )

    evidence_context = db.describe_resource(result.evidence_iri, graph="evidence")
    assert any(
        triple.predicate == "https://richcanopy.org/ns/rc#sourceSpan"
        and triple.object == result.source_span_iri
        for triple in evidence_context.outgoing
    )


def test_record_claim_reconsideration_links_claim_lifecycle(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    older = db.record_claim_observation(
        summary="Initial MMSI identity hunch.",
        claim_text="MMSI can be treated as the stable vessel identity key.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=["https://example.test/ais#mmsi"],
        evidence_sources=["trial setup"],
    )
    newer = db.record_claim_observation(
        summary="MMSI caveat check.",
        claim_text="MMSI is an operational grouping key, not proof of vessel identity.",
        claim_kind="rc:CaveatClaim",
        claim_targets=["https://example.test/ais#mmsi"],
        evidence_sources=["retrieved caveat"],
        observation_status="rc:Checked",
    )

    reconsideration = db.record_claim_reconsideration(
        newer_claim=newer.claim_iri,
        older_claim=older.claim_iri,
        relation="weakens",
        summary="MMSI identity hunch weakened.",
        rationale=(
            "The retrieved caveat shows MMSI remains useful for operational "
            "grouping but is too weak for durable vessel identity."
        ),
        evidence_sources=["DoxaBase search(\"MMSI vessel\")"],
        source_path="/tmp/doxabase-search-mmsi-vessel.json",
        source_kind="rc:DoxaBaseAPISource",
    )

    assert reconsideration.relation == RC + "Weakening"
    assert reconsideration.direct_predicate == RC + "weakens"
    assert reconsideration.older_claim_status == RC + "Weakened"
    assert reconsideration.source_span_iri is not None
    assert reconsideration.status_triples == 1
    assert db.validate_graph(scope="all").conforms

    older_context = db.describe_resource(older.claim_iri, graph="observations")
    assert older_context.claim is not None
    assert older_context.claim.lifecycle_summary is not None
    assert "Current status: weakened." in older_context.claim.lifecycle_summary
    assert "1 weakening." in older_context.claim.lifecycle_summary
    older_statuses = [
        triple.object
        for triple in older_context.outgoing
        if triple.predicate == RC + "observationStatus"
    ]
    assert older_statuses == [RC + "Weakened"]

    newer_context = db.describe_resource(newer.claim_iri, graph="observations")
    assert any(
        triple.predicate == RC + "weakens" and triple.object == older.claim_iri
        for triple in newer_context.outgoing
    )

    pattern = db.record_pattern(
        summary="MMSI hunch should be read as operational, not identity-level.",
        pattern_text=(
            "The later caveat claim weakens the earlier vessel-identity hunch "
            "without making MMSI useless for grouping."
        ),
        rationale="The reconsideration preserves both the tempting hunch and the correction.",
        pattern_targets=["https://example.test/ais#mmsi"],
        supporting_claims=[older.claim_iri],
        evidence_sources=["claim reconsideration test"],
    )
    description = db.describe_pattern(pattern.pattern_iri)

    incoming = description.supporting_claims[0].incoming_reconsiderations
    assert description.supporting_claims[0].lifecycle_summary is not None
    assert "Later claims reconsider this claim: 1 weakening." in (
        description.supporting_claims[0].lifecycle_summary
    )
    assert [item.iri for item in incoming] == [reconsideration.reconsideration_iri]
    assert incoming[0].newer_claim is not None
    assert incoming[0].newer_claim.iri == newer.claim_iri
    assert incoming[0].relation_label == "weakening"

    context_slice = db.describe_context_slice(
        [older.claim_iri],
        profile="deep_lore",
    )
    assert context_slice.route_counts["incoming_claim_reconsideration"] == 1
    assert context_slice.route_counts["reconsidering_claim"] == 1


def test_record_pattern_links_observations_claims_evidence_and_targets(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    observation = db.record_observation(
        summary="body_top was populated in the inspected local parquet profile.",
        evidence_summary="Synthetic profile evidence.",
        evidence_sources=["tests/test_doxabase_core.py"],
    )
    claim = db.record_claim_observation(
        summary="body_top transformation claim.",
        claim_text="body_top is cleaned top-level message text.",
        claim_kind="rc:TransformationClaim",
        claim_targets=["https://example.test/enron#eml_messages__body_top"],
        evidence_summary="README body processing section.",
        source_path="/home/james/github.com/jamtho/enron-emails/README.md",
        source_section="Body processing",
        source_kind="rc:DocumentationSource",
        confidence="rc:HighConfidence",
        observation_status="rc:Checked",
    )

    result = db.record_pattern(
        summary="body_top behaves like cleaned top-level message text.",
        pattern_text=(
            "Documentation, a profile observation, and the transformation claim "
            "all support treating body_top as cleaned sender-new text."
        ),
        rationale=(
            "The supporting observation says the field is populated, while the "
            "claim and source span explain the reply-splitting transformation."
        ),
        pattern_targets=["https://example.test/enron#eml_messages__body_top"],
        supporting_observations=[observation.observation_iri],
        supporting_claims=[claim.claim_iri],
        source_path="/home/james/github.com/jamtho/enron-emails/README.md",
        source_section="Body processing",
        start_line=186,
        end_line=191,
        source_kind="rc:DocumentationSource",
        confidence="rc:HighConfidence",
        pattern_status="rc:Checked",
        pattern_stability="rc:RepeatedPattern",
        map_implications=["https://example.test/enron#caveat_body_processing_lossy"],
    )

    assert result.pattern_iri.startswith(
        "https://richcanopy.org/doxabase/generated/pattern/"
    )
    assert result.evidence_iri is not None
    assert result.source_span_iri is not None
    assert result.pattern_triples > 0
    assert result.evidence_triples > 0
    assert db.graph_overview().key_counts["patterns"] == 1
    assert db.validate_graph(scope="patterns").conforms
    assert db.validate_graph(scope="all").conforms

    patterns = db.list_entities(
        type="rc:Pattern",
        graph="patterns",
        text="sender-new",
    )
    assert [pattern.iri for pattern in patterns.entities] == [result.pattern_iri]
    assert patterns.entities[0].label == (
        "body_top behaves like cleaned top-level message text."
    )

    context = db.describe_resource(result.pattern_iri, graph="patterns")
    outgoing_predicates = {triple.predicate for triple in context.outgoing}

    assert context.label == "body_top behaves like cleaned top-level message text."
    assert "https://richcanopy.org/ns/rc#supportingObservation" in outgoing_predicates
    assert "https://richcanopy.org/ns/rc#supportingClaim" in outgoing_predicates
    assert "https://richcanopy.org/ns/rc#mapImplication" in outgoing_predicates
    assert db.search("sender-new", graph="patterns").matches[0].iri == (
        result.pattern_iri
    )

    description = db.describe_pattern(result.pattern_iri)
    assert description.summary == "body_top behaves like cleaned top-level message text."
    assert description.pattern_text is not None
    assert "sender-new text" in description.pattern_text
    assert description.rationale is not None
    assert description.confidence == RC + "HighConfidence"
    assert description.confidence_label == "high confidence"
    assert description.observation_status == RC + "Checked"
    assert description.observation_status_label == "checked"
    assert description.pattern_stability == RC + "RepeatedPattern"
    assert description.pattern_stability_label == "repeated pattern"
    assert [target.iri for target in description.pattern_targets] == [
        "https://example.test/enron#eml_messages__body_top"
    ]
    assert [support.iri for support in description.supporting_observations] == [
        observation.observation_iri
    ]
    assert description.supporting_observations[0].label == (
        "body_top was populated in the inspected local parquet profile."
    )
    assert [support.iri for support in description.supporting_claims] == [
        claim.claim_iri
    ]
    assert description.supporting_claims[0].claim_text == (
        "body_top is cleaned top-level message text."
    )
    assert description.evidence[0].source_spans[0].source_section == "Body processing"
    assert description.evidence[0].source_spans[0].start_line == 186
    assert [implication.iri for implication in description.map_implications] == [
        "https://example.test/enron#caveat_body_processing_lossy"
    ]


def test_record_pattern_requires_support_or_source(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match="supporting_observations"):
        db.record_pattern(
            summary="Unsupported synthesis.",
            pattern_text="This pattern has no support.",
            rationale="A pattern should not be a free-floating hunch.",
            pattern_targets=["https://example.test/enron#eml_messages"],
        )
    with pytest.raises(DoxaBaseError, match="evidence_summary requires"):
        db.record_pattern(
            summary="Evidence summary without a source.",
            pattern_text="This pattern has support but no evidence source.",
            rationale="Evidence summaries should not create source-less evidence.",
            pattern_targets=["https://example.test/enron#eml_messages"],
            supporting_observations=["https://example.test/enron#obs"],
            evidence_summary="This summary has no source.",
        )


def test_record_pattern_rejects_prose_map_implications(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match="map_implications values"):
        db.record_pattern(
            summary="Prose map implication.",
            pattern_text="This pattern should fail before TriG export.",
            rationale="Map implications should point at map resources.",
            pattern_targets=["https://example.test/enron#eml_messages"],
            supporting_observations=["https://example.test/enron#obs"],
            map_implications=[
                "Map remains unchanged in this run; review rationale is in history.",
            ],
        )


def test_agent_authored_pattern_rdf_requires_rationale(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(
        """
        @prefix ex:  <https://example.test/project#> .
        @prefix rc:  <https://richcanopy.org/ns/rc#> .
        @prefix rcg: <https://richcanopy.org/graph/> .

        rcg:patterns {
            ex:unsupported_pattern a rc:Pattern ;
                rc:summary "A pattern without rationale should fail." ;
                rc:patternText "This pattern skips rationale." ;
                rc:patternTarget ex:eml_messages ;
                rc:evidence ex:evidence .
        }

        rcg:evidence {
            ex:evidence a rc:Evidence ;
                <http://purl.org/dc/terms/source> "tests/test_doxabase_core.py" .
        }
        """
    )

    validation = db.validate_graph(scope="all")

    assert not validation.conforms
    assert "Pattern resources must have exactly one string rationale" in (
        validation.report_text
    )


def test_record_claim_observation_requires_source(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match="evidence_sources or source_path"):
        db.record_claim_observation(
            summary="Missing evidence source.",
            claim_text="This claim should be rejected before RDF is written.",
            claim_kind="rc:CaveatClaim",
            claim_targets=["https://example.test/enron#eml_messages"],
            evidence_summary="Summary alone is not enough for source-backed evidence.",
        )


def test_record_claim_observation_rejects_prose_proposed_assertions(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match="proposed_assertions values"):
        db.record_claim_observation(
            summary="Prose proposed assertion.",
            claim_text="This claim should fail before TriG export.",
            claim_kind="rc:CaveatClaim",
            claim_targets=["https://example.test/enron#eml_messages"],
            evidence_sources=["tests/test_doxabase_core.py"],
            proposed_assertions=[
                "Map remains unchanged in this run; review rationale is in history.",
            ],
        )


def test_search_index_updates_after_graph_clear(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    assert db.search("downsampling", graph="map").matches

    db.clear_graph("map")

    assert db.search("downsampling", graph="map").matches == []


def test_search_rejects_invalid_queries(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match="Search query"):
        db.search("   ")
    with pytest.raises(DoxaBaseError, match="searchable token"):
        db.search("...")


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


def test_record_observation_writes_observation_and_evidence_graphs(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    before = db.graph_overview().key_counts["observations"]

    result = db.record_observation(
        summary="AIS daily broadcasts were sampled for row coverage.",
        observation_type="profile",
        observed_asset="https://richcanopy.org/example/manifest/ais#DailyBroadcasts",
        observed_at="2026-05-31T12:00:00Z",
        observed_by="urn:doxabase:test-agent",
        evidence_summary="Synthetic test evidence for the observation writer.",
        evidence_sources=["tests/test_doxabase_core.py"],
        row_count=123,
        distinct_count=45,
        value_frequencies=[
            {"value": "open", "frequency": 70},
            {"value": "closed", "frequency": 53},
        ],
        profile_metrics=[
            {"metric": "rc:MinimumValue", "value": 1.5},
            {"metric": "rc:MaximumValue", "value": "9.25", "datatype": "xsd:decimal"},
        ],
    )

    assert result.observation_type == "profile"
    assert result.evidence_iri is not None
    assert result.observation_triples > 0
    assert result.evidence_triples > 0
    assert db.graph_overview().key_counts["observations"] == before + 1

    observations = db.to_graph(["observations"])
    evidence = db.to_graph(["evidence"])
    observation_iri = URIRef(result.observation_iri)
    evidence_iri = URIRef(result.evidence_iri)

    assert (observation_iri, RDF.type, URIRef(RC + "ProfileObservation")) in observations
    assert (
        observation_iri,
        URIRef(RC + "rowCount"),
        Literal(123),
    ) in observations
    assert (
        observation_iri,
        URIRef(RC + "evidence"),
        evidence_iri,
    ) in observations
    value_frequency_iris = list(
        observations.objects(observation_iri, URIRef(RC + "observedValueFrequency"))
    )
    assert len(value_frequency_iris) == 2
    assert {
        (
            str(observations.value(value_iri, URIRef(RC + "observedValue"))),
            int(str(observations.value(value_iri, URIRef(RC + "valueFrequency")))),
        )
        for value_iri in value_frequency_iris
    } == {("open", 70), ("closed", 53)}
    assert all(
        (value_iri, RDF.type, URIRef(RC + "ObservedValueFrequency")) in observations
        for value_iri in value_frequency_iris
    )
    metric_iris = list(
        observations.objects(observation_iri, URIRef(RC + "observedProfileMetric"))
    )
    assert len(metric_iris) == 2
    assert {
        (
            str(observations.value(metric_iri, URIRef(RC + "profileMetricKind"))),
            str(observations.value(metric_iri, URIRef(RC + "profileMetricValue"))),
        )
        for metric_iri in metric_iris
    } == {
        (RC + "MinimumValue", "1.5"),
        (RC + "MaximumValue", "9.25"),
    }
    assert all(
        (metric_iri, RDF.type, URIRef(RC + "ObservedProfileMetric")) in observations
        for metric_iri in metric_iris
    )
    assert (evidence_iri, RDF.type, URIRef(RC + "Evidence")) in evidence
    assert (
        evidence_iri,
        DCTERMS.source,
        Literal("tests/test_doxabase_core.py"),
    ) in evidence

    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_record_dataset_profile_writes_observation_map_snapshot_and_pattern(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Messages"

    result = db.record_dataset_profile(
        dataset,
        summary="Messages were profiled for row and identity coverage.",
        observed_by="urn:doxabase:test-agent",
        evidence_summary="Synthetic profile output from a local DuckDB query.",
        evidence_sources=["test://messages-profile"],
        row_count=123,
        distinct_count=120,
        value_frequencies=[
            {"value": "open", "frequency": 80},
            {"value": "closed", "frequency": 43},
        ],
        profile_metrics=[
            {"metric": "rc:MinimumValue", "value": 1},
            {"metric": "rc:MaximumValue", "value": 123},
        ],
        map_label="Messages",
        is_table=True,
        pattern_summary="Messages profile is internally consistent.",
        pattern_text=(
            "The sampled Messages profile has a stable row count and near-row "
            "distinctness on the inspected identity field."
        ),
        pattern_rationale=(
            "Keeping the profile observation, map snapshot, and pattern linked "
            "makes later review cheaper."
        ),
    )

    assert result.dataset_iri == dataset
    assert result.observation.observation_type == "profile"
    assert result.observation.evidence_iri is not None
    assert result.map_dataset is not None
    assert result.map_dataset.iri == dataset
    assert result.pattern is not None

    description = db.describe_dataset(dataset)
    assert description.label == "Messages"
    assert description.row_count_snapshot == 123
    assert len(description.profile_observations) == 1
    profile = description.profile_observations[0]
    assert profile.iri == result.observation.observation_iri
    assert profile.row_count == 123
    assert profile.distinct_count == 120
    assert profile.null_count is None
    assert [(item.value, item.frequency) for item in profile.value_frequencies] == [
        ("open", 80),
        ("closed", 43),
    ]
    assert {
        (item.metric.iri, item.value, item.value_datatype)
        for item in profile.profile_metrics
    } == {
        (RC + "MinimumValue", "1", str(XSD.integer)),
        (RC + "MaximumValue", "123", str(XSD.integer)),
    }
    assert profile.evidence[0].iri == result.observation.evidence_iri
    assert profile.evidence[0].sources == ["test://messages-profile"]

    pattern = db.describe_pattern(result.pattern.pattern_iri)
    assert [target.iri for target in pattern.pattern_targets] == [dataset]
    assert [target.iri for target in pattern.map_implications] == [dataset]
    assert [item.iri for item in pattern.supporting_observations] == [
        result.observation.observation_iri
    ]
    assert [item.iri for item in pattern.evidence] == [
        result.observation.evidence_iri
    ]

    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_describe_dataset_profile_without_value_frequencies_returns_empty_list(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"

    db.record_dataset_profile(
        dataset,
        summary="Orders were profiled before value-frequency capture existed.",
        evidence_summary="Synthetic profile output.",
        row_count=10,
    )

    description = db.describe_dataset(dataset)

    assert len(description.profile_observations) == 1
    assert description.profile_observations[0].value_frequencies == []


def test_record_column_profile_writes_observation_map_column_and_pattern(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Messages"
    column = "https://example.test/project#MessagesDocId"
    db.record_map_dataset(table, label="Messages", is_table=True)

    result = db.record_column_profile(
        column,
        column_name="doc_id",
        table_iri=table,
        summary="Messages doc_id was profiled for null and distinct counts.",
        evidence_summary="Synthetic column profile output.",
        evidence_sources=["test://messages-doc-id-profile"],
        row_count=123,
        null_count=0,
        distinct_count=123,
        value_frequencies=[
            {"value": "doc-001", "frequency": 1},
            {"value": "doc-002", "frequency": 1},
        ],
        map_label="Messages.doc_id",
        physical_type="rc:Varchar",
        nullable=False,
        pattern_summary="doc_id behaves like a complete identifier.",
        pattern_text="The profiled doc_id column had no nulls and all values distinct.",
        pattern_rationale=(
            "A complete distinct profile is a useful hunch for later identity "
            "and join modelling."
        ),
    )

    assert result.column_iri == column
    assert result.table_iri == table
    assert result.observation.observation_type == "profile"
    assert result.map_column is not None
    assert result.map_column.iri == column
    assert result.pattern is not None
    pattern = db.describe_pattern(result.pattern.pattern_iri)
    assert [item.iri for item in pattern.evidence] == [
        result.observation.evidence_iri
    ]

    description = db.describe_dataset(table)
    assert [item.iri for item in description.columns] == [column]
    assert description.profile_observations == []
    assert description.columns[0].nullable is False
    assert description.columns[0].physical_type is not None
    assert description.columns[0].physical_type.iri == RC + "Varchar"
    assert len(description.columns[0].profile_observations) == 1
    profile = description.columns[0].profile_observations[0]
    assert profile.iri == result.observation.observation_iri
    assert profile.row_count == 123
    assert profile.null_count == 0
    assert profile.distinct_count == 123
    assert [(item.value, item.frequency) for item in profile.value_frequencies] == [
        ("doc-001", 1),
        ("doc-002", 1),
    ]
    assert profile.observed_asset is not None
    assert profile.observed_asset.iri == table
    assert profile.observed_column is not None
    assert profile.observed_column.iri == column
    assert profile.evidence[0].sources == ["test://messages-doc-id-profile"]

    pattern = db.describe_pattern(result.pattern.pattern_iri)
    assert [target.iri for target in pattern.pattern_targets] == [column]
    assert [target.iri for target in pattern.map_implications] == [column]
    assert [item.iri for item in pattern.supporting_observations] == [
        result.observation.observation_iri
    ]

    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_record_observation_rejects_invalid_inputs(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match="summary"):
        db.record_observation("   ")
    with pytest.raises(DoxaBaseError, match="row_count"):
        db.record_observation("Bad count", row_count=-1)
    with pytest.raises(DoxaBaseError, match="value_frequencies"):
        db.record_observation(
            "Bad value frequency",
            observation_type="profile",
            value_frequencies=[{"value": "open", "frequency": -1}],
        )
    with pytest.raises(DoxaBaseError, match="observation_type"):
        db.record_observation("Bad type", observation_type="note")  # type: ignore[arg-type]
