import json
import warnings
from collections.abc import Callable
from pathlib import Path

import pytest
from rdflib import Dataset, Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, RDF, XSD

from doxabase import (
    DoxaBase,
    DoxaBaseError,
    ImmutableGraphError,
    to_dict,
    to_jsonable,
)

ROOT = Path(__file__).resolve().parents[1]
AIS_FIXTURE = ROOT / "examples" / "manifest-prototype-rc" / "ais.trig"
POLYMARKET_FIXTURE = ROOT / "examples" / "manifest-prototype-rc" / "polymarket.trig"
RC = "https://richcanopy.org/ns/rc#"
MUTABLE_GRAPHS = (
    "map",
    "ontology",
    "observations",
    "patterns",
    "evidence",
    "shapes",
    "history",
)


def _mutable_graph_counts(db: DoxaBase) -> dict[str, int]:
    return {graph: db.triple_count(graph) for graph in MUTABLE_GRAPHS}


def _corrupt_staged_patch_target_graph(
    db: DoxaBase,
    patch_iri: str,
    target_graph: str,
) -> None:
    db._conn.execute(
        """
        UPDATE quads
        SET object = ?
        WHERE graph = 'history'
          AND subject = ?
          AND predicate = ?
        """,
        (target_graph, patch_iri, RC + "targetGraph"),
    )
    db._conn.commit()


def _corrupt_staged_patch_content(
    db: DoxaBase,
    patch_iri: str,
    content: str,
) -> None:
    db._conn.execute(
        """
        UPDATE quads
        SET object = ?
        WHERE graph = 'history'
          AND subject = ?
          AND predicate = ?
        """,
        (content, patch_iri, RC + "patchContent"),
    )
    db._conn.commit()


def test_capsule_creation_seeds_base_graphs(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    overview = db.graph_overview()

    graphs = {graph.name: graph for graph in overview.named_graphs}
    assert graphs["base_ontology"].triple_count == 1163
    assert graphs["base_ontology"].mutable is False
    assert graphs["base_shapes"].triple_count == 1194
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


def test_replace_graph_triples_updates_stale_incoming_link_and_search_index(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:Orders a rc:Dataset ;
            rc:hasColumn ex:CustomerV1 .

        ex:CustomerV1 a rc:Column ;
            rc:columnName "customer_id" ;
            rdfs:label "Customer feed v1" .
        """,
        graph="map",
    )
    before_digest = db._graph_content_digest("map")

    result = db.replace_graph_triples(
        "map",
        removals="""
            @prefix ex: <https://example.test/project#> .
            @prefix rc: <https://richcanopy.org/ns/rc#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            ex:Orders rc:hasColumn ex:CustomerV1 .

            ex:CustomerV1 a rc:Column ;
                rc:columnName "customer_id" ;
                rdfs:label "Customer feed v1" .
        """,
        additions="""
            @prefix ex: <https://example.test/project#> .
            @prefix rc: <https://richcanopy.org/ns/rc#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            ex:Orders rc:hasColumn ex:CustomerV2 .

            ex:CustomerV2 a rc:Column ;
                rc:columnName "customer_id" ;
                rdfs:label "Customer feed v2" .
        """,
        expected_count=5,
    )

    assert result.before_count == 5
    assert result.after_count == 5
    assert result.same_count is True
    assert result.triples_removed == 4
    assert result.triples_added == 4
    assert result.before_digest == before_digest
    assert result.after_digest != before_digest
    assert db.search("Customer feed v1", graph="map").matches == []
    assert len(db.search("Customer feed v2", graph="map").matches) == 1


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
    assert staged.summary == "Try messages table framing"
    assert staged.rationale == (
        "Exploratory hunch: treating messages as the map anchor should make "
        "later join reasoning easier."
    )
    assert staged.review_note is None
    assert staged.review_recommendation is None
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


def test_stage_graph_revision_parse_errors_include_parser_detail(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    malformed_patch = (
        "@prefix ex: <https://example.test/project#> .\n"
        "@prefix rc: <https://richcanopy.org/ns/rc#> .\n"
        "\n"
        "ex:Messages a rc:Dataset\n"
        "ex:Other a rc:Dataset ."
    )

    with pytest.raises(DoxaBaseError) as exc_info:
        db.stage_graph_revision(
            summary="Stage malformed patch",
            rationale="Malformed RDF should report parser detail.",
            additions=[
                {
                    "graph": "map",
                    "content": malformed_patch,
                }
            ],
        )

    message = str(exc_info.value)
    assert "Could not parse staged patch for graph 'map' as turtle" in message
    assert "at line" in message
    assert "expected '.'" in message
    assert "at ^ in" not in message


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
    assert column_support.suggested_next_actions[0].action_label == (
        "Load context slice"
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
    assert db.triple_count("map") == before_map_count

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
    assert check.suggested_next_actions[-1].tool_name == "apply_staged_revision"
    assert check.suggested_next_actions[-1].action_label == (
        "Apply only after semantic review"
    )
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
    assert ready_check.suggested_next_actions[-1].action_label == (
        "Apply only after semantic review"
    )

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
    assert check.suggested_next_actions[0].tool_name == "describe_staged_revision"
    assert check.suggested_next_actions[0].action_label == "Review staged revision"
    assert check.suggested_next_actions[0].mcp_tool_name == (
        "doxabase.describe_staged_revision"
    )
    assert check.suggested_next_actions[0].arguments == {"iri": staged.revision_iri}
    assert check.suggested_next_calls[0].startswith("describe_staged_revision(")
    assert check.suggested_next_actions[-1].tool_name == "apply_staged_revision"
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
    assert ready_summary.error is None

    result = db.apply_staged_revision(staged.revision_iri)

    assert result.staged_revision_iri == staged.revision_iri
    assert result.changed_graphs == ["map"]
    assert result.post_apply_recheck_revisions == []
    assert result.post_apply_recheck_revision_iris == []
    assert result.patches_applied == 1
    assert result.triples_added == 3
    assert result.triples_removed == 0
    assert result.validation_conforms is True
    assert db.triple_count("map") == 3
    messages = db.describe_dataset("https://example.test/project#Messages")
    assert messages.label == "Messages"

    applied = db.describe_graph_revision(result.applied_revision_iri)
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
    assert exact_map_diff.exact_changed_triples_included is True
    assert exact_map_diff.triples_added_truncated is False
    assert {triple.subject for triple in exact_map_diff.triples_added} == {
        "https://example.test/project#Messages"
    }
    project_path = tmp_path / "project.trig"
    snapshot_path = tmp_path / "revision-snapshots.json"
    db.export_trig(project_path, graphs="project")
    snapshot_export = db.export_revision_snapshots(
        snapshot_path,
        revision_iris=[staged.revision_iri, result.applied_revision_iri],
    )
    assert snapshot_export.snapshot_count == 2
    assert snapshot_export.quad_count == 3
    assert snapshot_export.revision_iris == [
        result.applied_revision_iri,
        staged.revision_iri,
    ]

    round_trip = DoxaBase.create(tmp_path / "round-trip.sqlite")
    round_trip.import_trig(project_path)
    imported_status_before_snapshots = round_trip.describe_revision_snapshot_evidence(
        result.applied_revision_iri
    )
    assert imported_status_before_snapshots.status == "history_only_count_digest"
    assert imported_status_before_snapshots.rdf_snapshot_graph_roles == ["map"]
    assert imported_status_before_snapshots.stored_snapshot_graph_roles == []
    assert [
        action.tool_name
        for action in imported_status_before_snapshots.suggested_next_actions
    ] == ["import_revision_snapshots"]
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
        action.tool_name
        for action in (
            imported_diff_before_snapshots.snapshot_evidence.suggested_next_actions
        )
    ] == ["import_revision_snapshots"]
    assert (
        imported_diff_before_snapshots.graph_diffs[0].exact_changed_triples_available
        is False
    )
    assert "import_revision_snapshots" in (
        imported_diff_before_snapshots.graph_diffs[0].note
    )

    snapshot_import = round_trip.import_revision_snapshots(snapshot_path)
    assert snapshot_import.imported_snapshot_count == 2
    assert snapshot_import.skipped_snapshot_count == 0
    assert snapshot_import.imported_quad_count == 3
    imported_status_after_snapshots = round_trip.describe_revision_snapshot_evidence(
        result.applied_revision_iri
    )
    assert imported_status_after_snapshots.status == "history_plus_snapshot_rows"
    assert imported_status_after_snapshots.exact_snapshot_graph_roles == ["map"]
    imported_exact_diff = round_trip.describe_applied_revision_diff(
        result.applied_revision_iri,
        include_triples=True,
    )
    assert imported_exact_diff.graph_diffs[0].exact_changed_triples_available is True
    assert {
        triple.subject
        for triple in imported_exact_diff.graph_diffs[0].triples_added
    } == {"https://example.test/project#Messages"}
    skipped_import = round_trip.import_revision_snapshots(snapshot_path)
    assert skipped_import.imported_snapshot_count == 0
    assert skipped_import.skipped_snapshot_count == 2
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
    workflow_round_trip.import_revision_snapshots(snapshot_path)
    orphan_status = workflow_round_trip.describe_revision_snapshot_evidence(
        result.applied_revision_iri
    )
    assert orphan_status.status == "snapshot_rows_without_history"
    assert orphan_status.orphan_snapshot_row_graph_roles == ["map"]
    assert [action.tool_name for action in orphan_status.suggested_next_actions] == [
        "import_trig"
    ]
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
    assert applied_check.suggested_next_actions[0].tool_name == (
        "describe_graph_revision"
    )
    assert applied_check.suggested_next_actions[1].tool_name == (
        "describe_applied_revision_diff"
    )
    assert applied_check.suggested_next_actions[1].arguments == {
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
    assert "**Inspect applied diff:**" in applied_export_text
    assert "describe_applied_revision_diff" in applied_export_text
    assert applied_export.bundle_summary.recommended_applied_inspection_iris == [
        staged.revision_iri
    ]


def test_stale_project_import_suggests_snapshot_json_before_restaging(
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
        "https://example.test/project#DriftDataset",
        label="Drift Dataset",
        is_table=True,
    )

    project_path = tmp_path / "project.trig"
    db.export_trig(project_path, graphs="project")
    round_trip = DoxaBase.create(tmp_path / "round-trip.sqlite")
    round_trip.import_trig(project_path)

    check = round_trip.check_staged_revision_apply(staged.revision_iri)

    assert check.status == "conflict"
    assert check.blocking_reasons == ["target_count_drift"]
    assert check.snapshot_drifts
    assert check.snapshot_drifts[0].exact_changed_triples_available is False
    assert [action.tool_name for action in check.suggested_next_actions] == [
        "describe_staged_revision",
        "export_staged_revision",
        "import_revision_snapshots",
        "restage_staged_revision",
    ]
    assert check.suggested_next_actions[2].action_label == (
        "Import snapshot bundle if available"
    )


def test_import_revision_snapshots_validates_bundle_before_writing(
    tmp_path: Path,
) -> None:
    valid_db = DoxaBase.create(tmp_path / "valid.sqlite")
    valid_revision = "https://example.test/revision#valid"
    invalid_revision = "https://example.test/revision#invalid"
    valid_snapshot = {
        "revision_iri": valid_revision,
        "graph_role": "map",
        "stored_at": "2026-06-25T00:00:00+00:00",
        "triple_count": 1,
        "content_digest": "sha256:valid",
        "quads": [
            {
                "subject": "https://example.test/project#Thing",
                "subject_kind": "uri",
                "predicate": "https://example.test/project#note",
                "object": "",
                "object_kind": "literal",
                "datatype": str(XSD.string),
                "lang": None,
            }
        ],
    }

    imported = valid_db.import_revision_snapshots(
        json.dumps(
            {
                "format": "doxabase.revision_snapshot_bundle.v1",
                "snapshots": [valid_snapshot],
            }
        )
    )
    assert imported.imported_snapshot_count == 1
    assert valid_db._graph_snapshot_storage_rows(valid_revision, "map")[0][3] == ""

    invalid_kind_db = DoxaBase.create(tmp_path / "invalid-kind.sqlite")
    with pytest.raises(DoxaBaseError, match="object_kind must be one of"):
        invalid_kind_db.import_revision_snapshots(
            json.dumps(
                {
                    "format": "doxabase.revision_snapshot_bundle.v1",
                    "snapshots": [
                        valid_snapshot,
                        {
                            "revision_iri": invalid_revision,
                            "graph_role": "map",
                            "stored_at": "2026-06-25T00:00:00+00:00",
                            "triple_count": 1,
                            "content_digest": "sha256:invalid",
                            "quads": [
                                {
                                    "subject": "https://example.test/project#Thing",
                                    "subject_kind": "uri",
                                    "predicate": "https://example.test/project#note",
                                    "object": "not a storage kind",
                                    "object_kind": "resource",
                                    "datatype": None,
                                    "lang": None,
                                }
                            ],
                        },
                    ],
                }
            )
        )

    assert not invalid_kind_db._graph_snapshot_storage_exists(valid_revision, "map")

    empty_uri_db = DoxaBase.create(tmp_path / "empty-uri.sqlite")
    with pytest.raises(DoxaBaseError, match="object must be non-empty"):
        empty_uri_db.import_revision_snapshots(
            json.dumps(
                {
                    "format": "doxabase.revision_snapshot_bundle.v1",
                    "snapshots": [
                        valid_snapshot,
                        {
                            "revision_iri": invalid_revision,
                            "graph_role": "map",
                            "stored_at": "2026-06-25T00:00:00+00:00",
                            "triple_count": 1,
                            "content_digest": "sha256:invalid",
                            "quads": [
                                {
                                    "subject": "https://example.test/project#Thing",
                                    "subject_kind": "uri",
                                    "predicate": "https://example.test/project#link",
                                    "object": "",
                                    "object_kind": "uri",
                                    "datatype": None,
                                    "lang": None,
                                }
                            ],
                        },
                    ],
                }
            )
        )

    assert not empty_uri_db._graph_snapshot_storage_exists(valid_revision, "map")

    empty_bnode_db = DoxaBase.create(tmp_path / "empty-bnode.sqlite")
    with pytest.raises(DoxaBaseError, match="object must be non-empty"):
        empty_bnode_db.import_revision_snapshots(
            json.dumps(
                {
                    "format": "doxabase.revision_snapshot_bundle.v1",
                    "snapshots": [
                        valid_snapshot,
                        {
                            "revision_iri": invalid_revision,
                            "graph_role": "map",
                            "stored_at": "2026-06-25T00:00:00+00:00",
                            "triple_count": 1,
                            "content_digest": "sha256:invalid",
                            "quads": [
                                {
                                    "subject": "https://example.test/project#Thing",
                                    "subject_kind": "uri",
                                    "predicate": "https://example.test/project#link",
                                    "object": "",
                                    "object_kind": "bnode",
                                    "datatype": None,
                                    "lang": None,
                                }
                            ],
                        },
                    ],
                }
            )
        )

    assert not empty_bnode_db._graph_snapshot_storage_exists(valid_revision, "map")


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


def test_stored_staged_patch_unknown_target_graph_blocks_apply_without_mutation(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = db.stage_graph_revision(
        summary="Stage messages table",
        rationale="Exercise stored target graph validation.",
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
    assert db.check_staged_revision_apply(staged.revision_iri).status == "ready"
    before_counts = _mutable_graph_counts(db)
    unknown_graph = "not_a_graph_role"
    assert db.triple_count(unknown_graph) == 0

    _corrupt_staged_patch_target_graph(
        db,
        staged.patches[0].patch_iri,
        unknown_graph,
    )

    description = db.describe_staged_revision(staged.revision_iri)
    assert description.patches[0].target_graph == unknown_graph
    check = db.check_staged_revision_apply(staged.revision_iri)
    assert check.can_apply is False
    assert check.status == "conflict"
    assert check.decision == "inspect_patch_conflict"
    assert check.blocking_reasons == ["patch_conflict"]
    assert check.recommended_resolution is not None
    assert "stage a repaired or alternative candidate" in check.recommended_resolution
    assert check.validation_conforms is None
    assert check.validation_skipped_reason == "conflicts_present"
    assert [action.tool_name for action in check.suggested_next_actions] == [
        "describe_staged_revision",
        "export_staged_revision",
    ]
    assert [action.action_label for action in check.suggested_next_actions] == [
        "Review patch conflict",
        "Export conflict bundle",
    ]
    assert check.patch_checks[0].target_graph == unknown_graph
    assert check.patch_checks[0].can_apply is False
    assert check.patch_checks[0].conflict is not None
    assert "targets unknown graph role" in check.patch_checks[0].conflict
    assert "targets unknown graph role" in check.conflicts[0]

    with pytest.raises(DoxaBaseError, match="targets unknown graph role"):
        db.apply_staged_revision(staged.revision_iri)
    with pytest.raises(DoxaBaseError, match="only handles count/digest drift"):
        db.restage_staged_revision(staged.revision_iri)

    batch = db.restage_staged_revisions([staged.revision_iri], dry_run=True)
    assert batch.would_restage_revision_iris == []
    assert batch.not_restageable_revision_iris == [staged.revision_iri]
    assert batch.not_restageable_revision_iris_by_reason == {
        "patch_conflict": [staged.revision_iri],
    }
    assert batch.items[0].action == "skipped_not_restageable"
    assert batch.items[0].not_restageable_reason == "patch_conflict"
    assert batch.items[0].decision_before == "inspect_patch_conflict"
    assert batch.bundle_summary.recommended_mutation_review_iris == [
        staged.revision_iri
    ]
    assert batch.bundle_summary.recommended_apply_or_restage_review_iris == []
    assert batch.bundle_summary.recommended_repair_review_iris == [
        staged.revision_iri
    ]
    assert batch.bundle_summary.next_action_queue == {
        "repair_or_replace": [staged.revision_iri],
    }

    assert _mutable_graph_counts(db) == before_counts
    assert db.triple_count(unknown_graph) == 0


def test_stored_malformed_staged_patch_conflict_includes_parser_detail(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    malformed_patch = (
        "@prefix ex: <https://example.test/project#> .\n"
        "@prefix rc: <https://richcanopy.org/ns/rc#> .\n"
        "\n"
        "ex:Messages a rc:Dataset\n"
        "ex:Other a rc:Dataset ."
    )
    staged = db.stage_graph_revision(
        summary="Stage messages table",
        rationale="Exercise stored patch parse diagnostics.",
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
    before_counts = _mutable_graph_counts(db)
    _corrupt_staged_patch_content(
        db,
        staged.patches[0].patch_iri,
        malformed_patch,
    )

    check = db.check_staged_revision_apply(staged.revision_iri)
    assert check.can_apply is False
    assert check.status == "conflict"
    assert check.decision == "inspect_patch_conflict"
    assert check.blocking_reasons == ["patch_conflict"]
    assert all(
        action.tool_name != "restage_staged_revision"
        for action in check.suggested_next_actions
    )
    assert check.patch_checks[0].conflict is not None
    assert "Could not parse staged patch" in check.patch_checks[0].conflict
    assert "at line" in check.patch_checks[0].conflict
    assert "expected '.'" in check.patch_checks[0].conflict
    assert "at ^ in" not in check.patch_checks[0].conflict

    with pytest.raises(DoxaBaseError, match="expected '\\.'"):
        db.apply_staged_revision(staged.revision_iri)

    assert _mutable_graph_counts(db) == before_counts


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
    assert check.review_recommended is True
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
    assert stale_summary.count_drifts[0].target_graph == "map"
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
    assert "| Patch | Graph | Expected before | Current | Delta |" in export_text
    assert "### Snapshot Drift" in export_text
    assert "#### Snapshot Drift Triples: map" in export_text
    assert "Added since snapshot" in export_text
    assert (
        "| Patch | Graph | Operation | Recorded preview before | "
        "Current preview before | Recorded preview after | Current preview | "
        "Effective + | Effective - | Already present | Already absent | "
        "Mechanically can apply | Conflict |"
    ) in export_text
    assert "| map | 0 |" in export_text
    assert f"| 0 | {db.triple_count('map')} |" in export_text
    assert "all_patch_triples_absent" in export_text
    assert "### Suggested Next Calls" in export_text
    assert "**Restage stale source:**" in export_text
    assert "Create a refreshed staged revision" in export_text
    assert "restage_staged_revision" in export_text
    assert "expected 0 triples before patch" in check.conflicts[0]
    assert check.patch_checks[0].can_apply is False
    assert check.suggested_next_actions[0].tool_name == "describe_staged_revision"
    assert check.suggested_next_actions[0].action_label == "Review stale source"
    assert check.suggested_next_actions[0].arguments == {
        "iri": staged.revision_iri,
        "include_current_apply_check": True,
    }
    assert check.suggested_next_calls[0].startswith("describe_staged_revision(")
    assert check.suggested_next_actions[-1].tool_name == "restage_staged_revision"
    assert check.suggested_next_actions[-1].action_label == "Restage stale source"

    with pytest.raises(DoxaBaseError, match="Staged revision cannot be applied"):
        db.apply_staged_revision(staged.revision_iri)

    with pytest.raises(DoxaBaseError, match="Messages"):
        db.describe_dataset("https://example.test/project#Messages")


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
    assert "patch objects and revision anchors" in drift.note


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
    assert "Restage the proposal" in stale_summary.apply_recommended_resolution
    assert "Handled by refreshed successor" in stale_summary.summary_recommendation
    assert (
        stale_summary.summary_recommendation_source
        == "stale_resolution_redirect"
    )
    assert stale_summary.active_recommendation_field == "summary_recommendation"
    assert stale_summary.restaged_by == restaged.revision_iri
    assert stale_summary.suggested_next_actions[-1].tool_name == (
        "describe_staged_revision"
    )
    assert stale_summary.suggested_next_actions[-1].action_label == (
        "Inspect current refreshed successor"
    )
    assert stale_summary.suggested_next_actions[-1].arguments == {
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
    assert "## Restage Context" in grouped_export
    assert grouped_export.index("## Restage Context") < grouped_export.index(
        "## Revisions"
    )
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
    assert not any(
        action.tool_name == "restage_staged_revision"
        for action in stale_check_after.suggested_next_actions
    )
    assert stale_check_after.suggested_next_actions[-1].arguments == {
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
    applied_grouped_export = db.export_staged_revisions(
        [staged.revision_iri, restaged.revision_iri],
        tmp_path / "applied-restaged-comparison.md",
    )
    assert applied_grouped_export.revision_summaries[1].stale_resolution_state == (
        "restaged_successor_already_applied"
    )
    assert applied_grouped_export.bundle_summary.recommended_mutation_review_iris == []
    assert applied_grouped_export.bundle_summary.recommended_applied_inspection_iris == [
        restaged.revision_iri
    ]
    assert db.describe_dataset("https://example.test/project#Messages").iri == (
        "https://example.test/project#Messages"
    )


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
    assert source_check.suggested_next_actions[0].tool_name == (
        "describe_staged_revision"
    )
    assert source_check.suggested_next_actions[0].action_label == (
        "Inspect current refreshed successor"
    )
    assert source_check.suggested_next_actions[0].arguments == {
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
    listing = db.list_graph_revisions(
        current_staged_work_only=True,
        include_apply_checks=True,
    )
    assert [item.iri for item in listing.revisions] == [repair.revision_iri]


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
    assert stale_check.count_drifts[0].patch_triple_status == (
        "all_patch_triples_present"
    )

    restaged = db.restage_staged_revision(staged.revision_iri)
    check = db.check_staged_revision_apply(restaged.revision_iri)

    assert check.status == "noop"
    assert check.can_apply is False
    assert check.decision == "inspect_no_effective_change"
    assert check.blocking_reasons == ["no_effective_patch_triples"]
    assert check.triples_to_add == 0
    assert check.triples_to_remove == 0
    assert check.validation_conforms is True
    patch_check = check.patch_checks[0]
    assert patch_check.effective_triples_to_add == 0
    assert patch_check.effective_triples_to_remove == 0
    assert patch_check.already_present_triples == 1
    assert patch_check.already_absent_triples == 0
    assert not any(
        action.tool_name == "apply_staged_revision"
        for action in check.suggested_next_actions
    )
    with pytest.raises(DoxaBaseError, match="no effective patch triples"):
        db.apply_staged_revision(restaged.revision_iri)

    export = db.export_staged_revisions(
        [staged.revision_iri, restaged.revision_iri],
        tmp_path / "noop-restage-review.md",
    )
    restaged_summary = export.revision_summaries[1]
    assert restaged_summary.apply_status == "noop"
    assert restaged_summary.stale_resolution_state == "restaged_successor_noop"
    assert export.bundle_summary.post_apply_recheck_revision_iris == []
    assert export.bundle_summary.recommended_mutation_review_iris == []
    assert export.bundle_summary.recommended_apply_or_restage_review_iris == []
    assert export.bundle_summary.recommended_repair_review_iris == []
    exported_text = (tmp_path / "noop-restage-review.md").read_text(
        encoding="utf-8"
    )
    assert "Effective +" in exported_text
    assert "no_effective_patch_triples" in exported_text


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
    assert batch.items[1].triples_to_add_after > 0
    assert batch.items[1].triples_to_remove_after == 0
    assert batch.items[2].not_restageable_reason == "ready"
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
    assert "- Post-apply recheck: " in exported
    assert "## Restage Context" in exported
    assert exported.index("## Review Queues") < exported.index("## Restage Context")
    assert "Stage order lifecycle table" in exported
    assert db.check_staged_revision_apply(restaged_second).status == "ready"

    db.apply_staged_revision(already_restaged.revision_iri)
    ready_after_apply = db.check_staged_revision_apply(ready.revision_iri)
    assert ready_after_apply.status == "conflict"
    assert "target_count_drift" in ready_after_apply.blocking_reasons


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
    assert item.status_after == "validation_failed"
    assert item.decision_after == "inspect_validation_results"
    assert item.stale_resolution_state_after == "restaged_successor_not_ready"
    assert item.blocking_reasons_after == ["validation_failed"]
    assert item.triples_to_add_after > 0
    assert item.triples_to_remove_after == 0
    assert "current revision fails validation" in item.note
    assert "stage a repaired or alternative candidate" in item.note
    assert "stage_map_assertion_change replacement" in item.note
    successor_check = db.check_staged_revision_apply(successor_iri)
    assert successor_check.recommended_resolution is not None
    assert "removal+addition" in successor_check.recommended_resolution
    assert "stage_map_assertion_change replacement" in (
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
    assert original_check.suggested_next_actions[-1].arguments == {
        "iri": current_successor.revision_iri
    }
    assert original_check.suggested_next_actions[-1].action_label == (
        "Inspect current refreshed successor"
    )

    listing = db.list_graph_revisions(include_apply_checks=True)
    by_iri = {item.iri: item for item in listing.revisions}
    assert by_iri[original.revision_iri].restaged_by == first_successor.revision_iri
    assert (
        by_iri[original.revision_iri].current_restaged_by
        == current_successor.revision_iri
    )
    assert by_iri[original.revision_iri].suggested_next_actions[-1].arguments == {
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
    exported = export_path.read_text(encoding="utf-8")
    assert "- Restaged by: " in exported
    assert "- Current restaged by: " in exported
    assert "**Inspect current refreshed successor:**" in exported
    assert "**Review stale source:**" in exported
    assert current_successor.revision_iri in exported

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
    assert export.bundle_summary.recommended_repair_review_iris == []
    assert export.bundle_summary.recommended_applied_inspection_iris == []
    assert "## Bundle Warnings" in exported
    assert exported.index("## Bundle Warnings") < exported.index("## Restage Context")
    assert "## Review Queues" in exported
    assert exported.index("## Review Queues") < exported.index("## Restage Context")
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
    assert len(result.post_apply_recheck_revisions) == 1
    assert result.post_apply_recheck_revisions[0].iri == second_restaged.revision_iri
    assert result.post_apply_recheck_revisions[0].changed_graphs == ["map"]
    assert result.post_apply_recheck_revisions[0].shared_changed_graphs == ["map"]
    second_check_after_apply = db.check_staged_revision_apply(
        second_restaged.revision_iri
    )
    assert second_check_after_apply.status == "conflict"
    assert "target_count_drift" in second_check_after_apply.blocking_reasons


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
    assert staged_listing.drift_detail == "summary"
    assert staged_listing.record_kind is None
    assert staged_listing.application_status is None
    assert staged_listing.staged_validation_status is None
    assert staged_listing.stale_resolution_state is None
    assert staged_listing.current_staged_work_only is False
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
    drift_by_iri = {item.iri: item for item in drift_listing.revisions}
    stale_item = drift_by_iri[stale.revision_iri]
    assert stale_item.application_status == "conflict"
    assert stale_item.application_summary is not None
    assert stale_item.application_summary.startswith("Blocked by 1 conflict")
    assert stale_item.application_recommended_resolution is not None
    assert "Restage the proposal" in stale_item.application_recommended_resolution
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
    assert [action.tool_name for action in check.suggested_next_actions] == [
        "describe_staged_revision",
        "export_staged_revision",
    ]
    assert "stage a repaired" in check.suggested_next_actions[0].reason
    assert "validation-failed" in check.suggested_next_actions[1].arguments["path"]
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
    assert validation_summary.suggested_next_actions[0].tool_name == (
        "describe_staged_revision"
    )
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

    with pytest.raises(DoxaBaseError, match="Applying staged revision would fail"):
        db.apply_staged_revision(staged.revision_iri)


def test_list_graph_revisions_filters_staged_validation_after_live_conflict(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = db.stage_graph_revision(
        summary="Stage invalid value type",
        rationale="Exercise stored validation diagnostics after target drift.",
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

    before_drift = db.list_graph_revisions(
        application_status="validation_failed",
        staged_validation_status="failed",
    )

    assert before_drift.include_apply_checks is True
    assert before_drift.application_status == "validation_failed"
    assert before_drift.staged_validation_status == "failed"
    assert [item.iri for item in before_drift.revisions] == [staged.revision_iri]
    assert before_drift.revisions[0].staged_validation_status == "failed"

    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:BenignOntologyTerm a rdfs:Class ;
            rdfs:label "Benign ontology term" .
        """,
        graph="ontology",
    )

    live_validation_failed = db.list_graph_revisions(
        application_status="validation_failed",
    )
    stored_validation_failed = db.list_graph_revisions(
        staged_validation_status="failed",
    )
    conflicted_stored_validation_failed = db.list_graph_revisions(
        application_status="conflict",
        staged_validation_status="failed",
    )

    assert live_validation_failed.count == 0
    assert stored_validation_failed.staged_validation_status == "failed"
    assert [item.iri for item in stored_validation_failed.revisions] == [
        staged.revision_iri
    ]
    stored_row = stored_validation_failed.revisions[0]
    assert stored_row.application_status is None
    assert stored_row.validation_conforms is False
    assert stored_row.validation_result_count == 1
    assert stored_row.staged_validation_status == "failed"
    assert conflicted_stored_validation_failed.include_apply_checks is True
    assert [item.iri for item in conflicted_stored_validation_failed.revisions] == [
        staged.revision_iri
    ]
    conflict_row = conflicted_stored_validation_failed.revisions[0]
    assert conflict_row.application_status == "conflict"
    assert conflict_row.stale_resolution_state == "stale_unresolved"
    assert conflict_row.application_validation_skipped_reason == "conflicts_present"

    export = db.export_staged_revisions(
        [staged.revision_iri],
        tmp_path / "validation-after-drift.md",
    )

    assert export.bundle_summary.validation_failed_revision_iris == []
    assert export.bundle_summary.staged_validation_failed_revision_iris == [
        staged.revision_iri
    ]


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


def test_stage_graph_revision_rejects_history_target_without_metadata_write(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_history_count = db.triple_count("history")

    with pytest.raises(
        DoxaBaseError,
        match="cannot target 'history'.*record_graph_revision",
    ):
        db.stage_graph_revision(
            summary="Invalid staged history patch",
            rationale="Staged patch metadata is itself written to history.",
            additions=[
                {
                    "graph": "history",
                    "content": (
                        "@prefix ex: <https://example.test/> . "
                        "ex:review ex:note \"Manual review note\" ."
                    ),
                }
            ],
        )

    assert db.triple_count("history") == before_history_count


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
    assert export.revision_summaries[1].suggested_next_actions[-1].tool_name == (
        "apply_staged_revision"
    )
    assert export.bytes_written == len(exported.encode("utf-8"))
    assert exported.startswith("# Identity ladder alternatives\n")
    assert "## Review Summary" in exported
    assert "Prefer the pattern-first framing for now" in exported
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
    assert len(context.query_target_candidates) == 1
    target = context.query_target_candidates[0]
    assert target.template == "broadcasts/{year}/ais-{date}.parquet"
    assert target.template_source == "partition_scheme"
    assert target.storage_root == "s3://ais-noaa/"
    assert target.bucket_name == "ais-noaa"
    assert target.candidate_path == "s3://ais-noaa/broadcasts/{year}/ais-{date}.parquet"
    assert target.composition == "storage_root_joined"
    assert target.endpoint_profile == "local-minio"
    assert target.requires_endpoint_profile is True
    assert target.credential_reference == "profile:ais-readonly"
    assert target.path_style_access is True
    assert target.review_required is True
    assert any(reason.code == "layout_needs_verification" for reason in target.review_reasons)
    assert context.storage_accesses[0].endpoint_profile == "local-minio"
    assert context.storage_accesses[0].credential_reference == "profile:ais-readonly"
    assert {column.column_name for column in context.columns} >= {
        "mmsi",
        "timestamp",
    }
    assert any(
        issue.code == "layout_needs_verification"
        and issue.domain == "query_planning"
        and issue.severity == "warning"
        and issue.resource is not None
        and issue.resource.iri
        == "https://richcanopy.org/example/manifest/ais#daily_date_partition"
        and "verify against storage listing" in issue.message
        for issue in context.issues
    )
    assert "non-secret planning metadata" in context.planning_notes[0]


def test_draft_query_plan_returns_review_gated_duckdb_plan(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    plan = db.draft_query_plan(
        "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"
    )

    assert plan.helper == "draft_query_plan"
    assert plan.mode == "non_executed_review_draft"
    assert plan.handoff_kind == "metadata_review_required"
    assert plan.engine.name == "duckdb"
    assert plan.source_context.api == "DoxaBase.describe_query_context"
    assert plan.source_context.readiness == "needs_review"
    assert plan.source_context.selected_candidate_index == 0
    assert plan.source_context.query_target_decision.status == (
        "candidate_needs_review"
    )
    assert plan.selected_candidate is not None
    assert plan.selected_candidate.template_source == "partition_scheme"
    assert plan.scan.function == "read_parquet"
    assert plan.scan.uri_template == (
        "s3://ais-noaa/broadcasts/{year}/ais-{date}.parquet"
    )
    assert plan.scan.file_format == "Parquet"
    assert plan.scan.compression == "zstd"
    assert plan.scan.candidate_path_status == "orientation_only"
    assert plan.scan.template_source == "partition_scheme"
    assert plan.scan.template_source_resource is not None
    assert plan.scan.template_source_resource.iri == (
        "https://richcanopy.org/example/manifest/ais#daily_date_partition"
    )
    assert plan.scan.template_source_verification_status is not None
    assert plan.scan.template_source_verification_status.iri == (
        RC + "GeneratedFromManifestLayout"
    )
    assert plan.scan.template_source_verification_note is not None
    assert "verify against storage listing" in (
        plan.scan.template_source_verification_note
    )
    assert plan.scan.template_lineage is not None
    assert "partition_scheme daily_date_partition" in plan.scan.template_lineage
    assert plan.required_bindings == ["year", "date"]
    assert [binding.name for binding in plan.binding_requirements] == [
        "year",
        "date",
    ]
    assert plan.binding_requirements[0].source == "path_template_placeholder"
    assert plan.binding_requirements[0].source_text == (
        "s3://ais-noaa/broadcasts/{year}/ais-{date}.parquet"
    )
    assert plan.binding_requirements[0].required is True
    assert plan.binding_requirements[0].derivation_status == "not_inferred"
    assert "has not inferred" in plan.binding_requirements[0].derivation_note
    assert plan.storage_environment.bucket_name == "ais-noaa"
    assert plan.storage_environment.endpoint_profile == "local-minio"
    assert plan.storage_environment.credential_reference == "profile:ais-readonly"
    assert plan.storage_environment.path_style_access is True
    assert plan.storage_environment.runtime_resolution_required is True
    assert plan.storage_environment.duckdb_settings_from_context == [
        "s3_url_style=path",
        "s3_region=local",
    ]
    assert plan.review_gate.executable_without_review is False
    assert plan.review_gate.binding_values_required is True
    assert plan.review_gate.status == "candidate_needs_review"
    assert plan.review_gate.blocking_reason_codes == ["layout_needs_verification"]
    assert plan.review_gate.all_issue_codes == [
        "layout_needs_verification",
        "verification_status_not_recorded",
    ]
    assert plan.review_gate.reason_codes == ["layout_needs_verification"]
    assert any(issue.code == "layout_needs_verification" for issue in plan.issues)
    assert plan.caveats
    assert "not executable code" in plan.planning_notes[-1]


def test_draft_query_plan_carries_dataset_template_verification(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    root = tmp_path / "warehouse"
    dataset = "https://example.test/project#LocalEvents"
    template = str(root / "events/date={date}/part-*.parquet")
    verification_note = "Complete absolute path template matched the scratch layout."
    storage = db.record_map_storage_access(
        "https://example.test/project#local_events_storage",
        label="Local events storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(root),
        location_kind="directory",
        access_mode="rc:ReadOnlyAccess",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#local_events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Local events",
        is_table=True,
        path_templates=[template],
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByListingLayout",
        layout_verification_note=verification_note,
    )

    plan = db.draft_query_plan(dataset)

    assert plan.selected_candidate is not None
    assert plan.selected_candidate.template_source == "dataset"
    assert plan.scan.template_source == "dataset"
    assert plan.scan.template_source_resource is not None
    assert plan.scan.template_source_resource.iri == dataset
    assert plan.scan.template_source_verification_status is not None
    assert plan.scan.template_source_verification_status.iri == (
        RC + "VerifiedByListingLayout"
    )
    assert plan.scan.template_source_verification_note == verification_note
    assert plan.scan.dataset_verification_status is not None
    assert plan.scan.dataset_verification_status.iri == (
        RC + "VerifiedByListingLayout"
    )
    assert plan.scan.dataset_verification_note == verification_note
    assert plan.scan.template_lineage is not None
    assert "dataset Local events" in plan.scan.template_lineage
    assert verification_note in plan.scan.template_lineage
    assert plan.handoff_kind == "binding_values_required"
    assert plan.review_gate.executable_without_review is True
    assert plan.review_gate.binding_values_required is True
    assert plan.review_gate.ready_for_execution_attempt is False


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
    assert {issue.domain for issue in context.issues} == {"query_planning"}
    assert context.query_target_decision.status == "no_candidate"
    assert context.query_target_decision.candidate_index is None
    assert context.query_target_decision.candidate_path is None
    assert context.query_target_decision.candidate_path_status is None
    assert context.query_target_decision.direct_review_required is None
    assert context.query_target_decision.reason_codes == []


def test_describe_query_context_summarizes_fixture_target_candidates(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    db.import_trig(POLYMARKET_FIXTURE)

    tables = db.list_entities(type="rc:Table", graph="map", limit=20).entities
    assert len(tables) == 7
    seen_sources: set[str] = set()

    for table in tables:
        context = db.describe_query_context(table.iri)

        assert context.query_target_candidates
        for target in context.query_target_candidates:
            seen_sources.add(target.template_source)
            assert target.template_source in {
                "dataset",
                "partition_scheme",
                "storage_access",
            }
            assert target.source_resource.iri
            assert target.storage_access is not None
            assert target.candidate_path is not None
            assert "data/parquet/data/parquet" not in target.candidate_path
            assert "s3://ais-noaa/ais-noaa" not in target.candidate_path
            assert target.review_required is any(
                reason.severity in {"error", "warning"}
                for reason in target.review_reasons
            )

    assert {"dataset", "partition_scheme"} <= seen_sources


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


def test_query_target_candidates_surface_global_blockers(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    local_storage = db.record_map_storage_access(
        "https://example.test/project#orders_z_local_storage",
        label="Orders local access",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/warehouse",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    stale_storage = db.record_map_storage_access(
        "https://example.test/project#orders_a_stale_s3_storage",
        label="Orders stale S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        bucket_name="old-orders",
        key_prefix="orders",
        credential_reference="profile:old-orders",
        layout_verification_status="rc:ContradictedLayout",
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
        path_templates=["orders/dt={date}.parquet"],
        storage_accesses=[local_storage.iri, stale_storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "blocked_by_contradiction"
    local_index = next(
        index
        for index, target in enumerate(context.query_target_candidates)
        if target.storage_access is not None
        and target.storage_access.iri == local_storage.iri
    )
    local_target = next(
        target
        for target in context.query_target_candidates
        if target.storage_access is not None
        and target.storage_access.iri == local_storage.iri
    )
    assert local_target.review_required is True
    assert local_target.direct_review_required is False
    assert local_target.direct_review_reasons == []
    assert any(
        reason.code == "query_context_has_other_blockers"
        and reason.severity == "error"
        for reason in local_target.review_reasons
    )
    stale_index = next(
        index
        for index, target in enumerate(context.query_target_candidates)
        if target.storage_access is not None
        and target.storage_access.iri == stale_storage.iri
    )
    stale_target = next(
        target
        for target in context.query_target_candidates
        if target.storage_access is not None
        and target.storage_access.iri == stale_storage.iri
    )
    assert stale_index < local_index
    assert any(
        reason.code == "contradicted_layout"
        for reason in stale_target.review_reasons
    )
    assert stale_target.direct_review_required is True
    assert any(
        reason.code == "contradicted_layout"
        for reason in stale_target.direct_review_reasons
    )
    assert context.query_target_decision.status == "context_blocked"
    assert context.query_target_decision.candidate_index == local_index
    assert context.query_target_decision.candidate_path == local_target.candidate_path
    assert context.query_target_decision.candidate_path_status == "orientation_only"
    assert context.query_target_decision.direct_review_required is False
    assert context.query_target_decision.reason_codes == [
        "query_context_has_other_blockers"
    ]
    plan = db.draft_query_plan(dataset)
    assert plan.handoff_kind == "context_review_required"
    assert plan.source_context.selection_mode == "automatic"
    assert plan.source_context.requested_candidate_index is None
    assert plan.source_context.requested_storage_access_iri is None
    assert plan.source_context.selection_status == "automatic"
    assert plan.source_context.allow_context_blocked_candidate is False
    assert plan.review_gate.selection_overridden is False
    assert plan.review_gate.context_blocked_candidate_allowed is False
    assert plan.review_gate.context_blocked_candidate_used is False
    assert plan.review_gate.direct_blocking_reason_codes == []
    assert plan.review_gate.context_blocking_reason_codes == [
        "query_context_has_other_blockers"
    ]
    assert plan.selected_candidate is not None
    assert plan.selected_candidate.candidate_path_status == "orientation_only"
    context_blocker = next(
        reason
        for reason in plan.selected_candidate.review_reasons
        if reason.code == "query_context_has_other_blockers"
    )
    assert context_blocker.details == {
        "excluded_blocker_count": 1,
        "excluded_blocker_codes": ["contradicted_layout"],
        "excluded_blocker_resource_iris": [stale_storage.iri],
    }

    allowed_plan = db.draft_query_plan(
        dataset,
        candidate_index=local_index,
        allow_context_blocked_candidate=True,
    )
    assert allowed_plan.source_context.query_target_decision.status == (
        "context_blocked"
    )
    assert allowed_plan.source_context.selected_candidate_index == local_index
    assert allowed_plan.source_context.selection_mode == "candidate_index"
    assert allowed_plan.source_context.requested_candidate_index == local_index
    assert allowed_plan.source_context.selection_status == "matched"
    assert allowed_plan.source_context.allow_context_blocked_candidate is True
    assert allowed_plan.selected_candidate is not None
    assert allowed_plan.selected_candidate.storage_access is not None
    assert allowed_plan.selected_candidate.storage_access.iri == local_storage.iri
    assert allowed_plan.selected_candidate.candidate_path_status == "ready"
    assert allowed_plan.selected_candidate.review_required is False
    assert allowed_plan.selected_candidate.review_reasons == []
    assert allowed_plan.scan.candidate_path_status == "ready"
    assert allowed_plan.review_gate.status == "ready"
    assert allowed_plan.review_gate.selection_overridden is True
    assert allowed_plan.review_gate.context_blocked_candidate_allowed is True
    assert allowed_plan.review_gate.context_blocked_candidate_used is True
    assert allowed_plan.review_gate.direct_blocking_reason_codes == []
    assert allowed_plan.review_gate.context_blocking_reason_codes == [
        "query_context_has_other_blockers"
    ]
    assert allowed_plan.review_gate.blocking_reason_codes == []
    assert allowed_plan.review_gate.executable_without_review is True
    assert allowed_plan.review_gate.binding_values_required is True
    assert allowed_plan.review_gate.ready_for_execution_attempt is False
    assert allowed_plan.handoff_kind == "binding_values_required"

    storage_selected_plan = db.draft_query_plan(
        dataset,
        storage_access_iri=local_storage.iri,
        allow_context_blocked_candidate=True,
    )
    assert storage_selected_plan.source_context.selection_mode == (
        "storage_access_iri"
    )
    assert storage_selected_plan.source_context.requested_storage_access_iri == (
        local_storage.iri
    )
    assert storage_selected_plan.source_context.selected_candidate_index == local_index
    assert storage_selected_plan.handoff_kind == "binding_values_required"

    direct_bad_plan = db.draft_query_plan(dataset, candidate_index=stale_index)
    assert direct_bad_plan.selected_candidate is not None
    assert direct_bad_plan.selected_candidate.storage_access is not None
    assert direct_bad_plan.selected_candidate.storage_access.iri == stale_storage.iri
    assert direct_bad_plan.review_gate.selection_overridden is True
    assert direct_bad_plan.review_gate.status == "candidate_needs_review"
    assert direct_bad_plan.review_gate.direct_blocking_reason_codes == [
        "contradicted_layout",
        "storage_protocol_location_mismatch",
    ]
    assert direct_bad_plan.review_gate.blocking_reason_codes == [
        "contradicted_layout",
        "storage_protocol_location_mismatch",
    ]


def test_draft_query_plan_rejects_ambiguous_or_invalid_candidate_selection(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_storage",
        label="Orders local access",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/warehouse",
        path_templates=[
            "orders/current/dt={date}.parquet",
            "orders/archive/dt={date}.parquet",
        ],
        layout_verification_status="rc:VerifiedByListingLayout",
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

    with pytest.raises(DoxaBaseError, match="either candidate_index or"):
        db.draft_query_plan(
            dataset,
            candidate_index=0,
            storage_access_iri=storage.iri,
        )
    with pytest.raises(DoxaBaseError, match="candidate_index must point"):
        db.draft_query_plan(dataset, candidate_index=2)
    with pytest.raises(DoxaBaseError, match="candidate_index must point"):
        db.draft_query_plan(dataset, candidate_index=-1)
    with pytest.raises(DoxaBaseError, match="did not match any"):
        db.draft_query_plan(
            dataset,
            storage_access_iri="https://example.test/project#missing_storage",
        )
    with pytest.raises(DoxaBaseError, match="matched multiple"):
        db.draft_query_plan(dataset, storage_access_iri=storage.iri)


def test_describe_query_context_warns_on_protocol_location_mismatch(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Snapshots"
    storage = db.record_map_storage_access(
        "https://example.test/project#snapshots_https_storage",
        label="Snapshots HTTPS access",
        storage_protocol="rc:HTTPSStorage",
        bucket_name="public",
        key_prefix="snapshots",
        path_templates=["dt={date}.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#snapshots_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Snapshots",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "needs_review"
    assert any(
        issue.code == "storage_protocol_location_mismatch"
        and issue.resource is not None
        and issue.resource.iri == storage.iri
        for issue in context.issues
    )
    target = context.query_target_candidates[0]
    assert target.review_required is True
    assert target.candidate_path_status == "orientation_only"
    mismatch = next(
        reason
        for reason in target.review_reasons
        if reason.code == "storage_protocol_location_mismatch"
    )
    assert mismatch.details is not None
    assert mismatch.details["storage_access_iri"] == storage.iri
    assert mismatch.details["storage_protocol_iri"] == RC + "HTTPSStorage"
    assert mismatch.details["bucket_name"] == "public"
    assert mismatch.details["key_prefix"] == "snapshots"
    assert any(
        "bucket/prefix" in reason
        for reason in mismatch.details["mismatch_reasons"]
    )


def test_describe_query_context_warns_on_non_s3_bucket_prefix(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    storage = db.record_map_storage_access(
        "https://example.test/project#events_local_storage",
        label="Events local access",
        storage_protocol="rc:LocalFilesystemStorage",
        bucket_name="ignored-bucket",
        key_prefix="local-shaped-prefix",
        path_templates=["events/dt={date}.parquet"],
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
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "needs_review"
    target = context.query_target_candidates[0]
    assert target.candidate_path == "local-shaped-prefix/events/dt={date}.parquet"
    assert target.candidate_path_status == "orientation_only"
    assert target.review_required is True
    assert any(
        reason.code == "storage_protocol_location_mismatch"
        and "bucket/prefix" in reason.message
        for reason in target.review_reasons
    )


@pytest.mark.parametrize(
    ("protocol", "storage_root", "expected_path"),
    [
        (
            "rc:S3CompatibleStorage",
            "/lake/not-s3",
            "/lake/not-s3/events/dt={date}.parquet",
        ),
        (
            "rc:HTTPSStorage",
            "s3://public-bucket/not-https",
            "s3://public-bucket/not-https/events/dt={date}.parquet",
        ),
    ],
)
def test_describe_query_context_warns_on_storage_root_protocol_mismatch(
    tmp_path: Path,
    protocol: str,
    storage_root: str,
    expected_path: str,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    storage = db.record_map_storage_access(
        "https://example.test/project#events_storage",
        label="Events access",
        storage_protocol=protocol,
        storage_root=storage_root,
        path_templates=["events/dt={date}.parquet"],
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
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "needs_review"
    target = context.query_target_candidates[0]
    assert target.candidate_path == expected_path
    assert target.candidate_path_status == "orientation_only"
    assert target.review_required is True
    assert any(
        reason.code == "storage_protocol_location_mismatch"
        and "storage_root" in reason.message
        for reason in target.review_reasons
    )


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


def test_describe_query_context_warns_on_unresolved_s3_access(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_s3_storage",
        label="Orders S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        bucket_name="orders",
        key_prefix="warehouse",
        path_templates=["dt={date}.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
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

    assert context.readiness == "needs_review"
    target = context.query_target_candidates[0]
    assert target.candidate_path == "s3://orders/warehouse/dt={date}.parquet"
    assert target.review_required is True
    assert any(
        reason.code == "s3_access_resolution_unrecorded"
        for reason in target.review_reasons
    )
    plan = db.draft_query_plan(dataset)
    assert plan.review_gate.executable_without_review is False
    assert plan.review_gate.blocking_reason_codes == ["s3_access_resolution_unrecorded"]
    assert plan.storage_environment.bucket_name == "orders"
    assert plan.storage_environment.key_prefix == "warehouse"
    assert plan.storage_environment.endpoint_profile is None
    assert plan.storage_environment.credential_reference is None
    assert plan.storage_environment.region is None
    assert plan.storage_environment.runtime_resolution_required is True
    assert plan.handoff_kind == "runtime_resolution_required"
    assert "Record or resolve the S3 endpoint profile" in (
        plan.storage_environment.runtime_resolution_note
    )


def test_describe_query_context_warns_on_complete_s3_template_without_runtime_resolution(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_s3_storage",
        label="Orders S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        path_templates=["s3://orders-bucket/warehouse/orders/*.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
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

    assert context.readiness == "needs_review"
    assert any(
        issue.code == "s3_access_resolution_unrecorded"
        and issue.resource is not None
        and issue.resource.iri == storage.iri
        for issue in context.issues
    )
    target = context.query_target_candidates[0]
    assert target.candidate_path == "s3://orders-bucket/warehouse/orders/*.parquet"
    assert target.composition == "template_as_returned"
    assert target.candidate_path_status == "orientation_only"
    assert target.review_required is True
    assert any(
        reason.code == "s3_access_resolution_unrecorded"
        for reason in target.review_reasons
    )


def test_describe_query_context_warns_on_complete_template_protocol_mismatch(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Snapshots"
    storage = db.record_map_storage_access(
        "https://example.test/project#snapshots_https_storage",
        label="Snapshots HTTPS access",
        storage_protocol="rc:HTTPSStorage",
        path_templates=["s3://public-bucket/snapshots/*.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#snapshots_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Snapshots",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "needs_review"
    target = context.query_target_candidates[0]
    assert target.candidate_path == "s3://public-bucket/snapshots/*.parquet"
    assert target.candidate_path_status == "orientation_only"
    assert target.review_required is True
    assert any(
        reason.code == "storage_protocol_location_mismatch"
        and "path template" in reason.message
        for reason in target.review_reasons
    )


def test_describe_query_context_warns_on_s3_template_bucket_prefix_conflict(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_s3_storage",
        label="Orders S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        bucket_name="orders-a",
        key_prefix="warehouse",
        path_templates=["s3://orders-b/raw/orders/*.parquet"],
        credential_reference="profile:orders-readonly",
        layout_verification_status="rc:VerifiedByListingLayout",
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

    assert context.readiness == "needs_review"
    target = context.query_target_candidates[0]
    assert target.candidate_path == "s3://orders-b/raw/orders/*.parquet"
    assert target.candidate_path_status == "orientation_only"
    assert any(
        reason.code == "storage_protocol_location_mismatch"
        and "bucket_name" in reason.message
        and "key_prefix" in reason.message
        for reason in target.review_reasons
    )


def test_describe_query_context_warns_on_key_prefix_repeated_in_template(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_s3_storage",
        label="Orders S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        bucket_name="lake",
        key_prefix="warehouse",
        path_templates=["warehouse/orders/dt={date}.parquet"],
        credential_reference="profile:orders-readonly",
        layout_verification_status="rc:VerifiedByListingLayout",
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

    assert context.readiness == "needs_review"
    target = context.query_target_candidates[0]
    assert target.candidate_path == (
        "s3://lake/warehouse/warehouse/orders/dt={date}.parquet"
    )
    assert target.candidate_path_status == "orientation_only"
    assert any(
        reason.code == "storage_protocol_location_mismatch"
        and "repeat recorded key_prefix" in reason.message
        for reason in target.review_reasons
    )


def test_describe_query_context_surfaces_storage_root_only_location(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage_root = str(tmp_path / "orders.parquet")
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_local_storage",
        label="Orders local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="object",
        storage_root=storage_root,
        layout_verification_status="rc:VerifiedByListingLayout",
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
    assert "missing_path_template" not in {issue.code for issue in context.issues}
    assert context.path_templates == []
    assert len(context.query_target_candidates) == 1
    target = context.query_target_candidates[0]
    assert target.template == storage_root
    assert target.template_source == "storage_access_location"
    assert target.source_resource.iri == storage.iri
    assert target.storage_access is not None
    assert target.storage_access.iri == storage.iri
    assert target.location_kind == "object"
    assert target.candidate_path == storage_root
    assert target.composition == "storage_root_as_candidate"
    assert target.candidate_path_status == "ready"
    assert target.review_required is False
    assert target.review_reasons == []
    assert context.storage_accesses[0].location_kind == "object"
    plan = db.draft_query_plan(dataset)
    assert plan.scan.template_lineage is not None
    assert (
        "Candidate storage root comes from storage access Orders local storage."
        in plan.scan.template_lineage
    )
    assert "Template comes from storage_access_location" not in plan.scan.template_lineage
    assert plan.storage_environment.runtime_resolution_required is False
    assert plan.review_gate.executable_without_review is True
    assert plan.review_gate.runtime_resolution_required is False
    assert plan.review_gate.binding_values_required is False
    assert plan.review_gate.ready_for_execution_attempt is True
    assert plan.handoff_kind == "execution_attempt_ready"
    assert "No endpoint or credential profile is recorded or required" in (
        plan.storage_environment.runtime_resolution_note
    )


def test_draft_query_plan_review_gates_database_backed_table_without_scan_function(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#VerifiedEvents"
    storage = db.record_map_storage_access(
        "https://example.test/project#verified_events_database_storage",
        label="Verified events database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="analytics-prod",
        path_templates=["public.verified_events"],
        endpoint_profile="warehouse-prod",
        credential_reference="profile:warehouse-readonly",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#verified_events_table_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Verified events",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "ready_for_query_planning"
    assert context.query_target_decision.status == "ready"
    assert context.query_target_decision.candidate_path == "public.verified_events"
    assert context.query_target_decision.reason_codes == []
    target = context.query_target_candidates[0]
    assert target.candidate_path == "public.verified_events"
    assert target.relation_identifier == "public.verified_events"
    assert target.connection_reference == "analytics-prod"
    assert target.composition == "database_connection_and_relation"

    plan = db.draft_query_plan(dataset)

    assert plan.selected_candidate is not None
    assert plan.selected_candidate.candidate_path == "public.verified_events"
    assert plan.selected_candidate.relation_identifier == "public.verified_events"
    assert plan.selected_candidate.connection_reference == "analytics-prod"
    assert plan.scan.function is None
    assert plan.scan.uri_template is None
    assert plan.scan.relation_identifier == "public.verified_events"
    assert plan.scan.connection_reference == "analytics-prod"
    assert plan.scan.composition == "database_connection_and_relation"
    assert "database endpoint profile" in (
        plan.storage_environment.runtime_resolution_note
    )
    assert "connection, schema, table, or source access" in (
        plan.storage_environment.runtime_resolution_note
    )
    assert plan.review_gate.executable_without_review is False
    assert plan.review_gate.ready_for_execution_attempt is False
    assert plan.review_gate.blocking_reason_codes == ["scan_function_not_inferred"]
    assert plan.review_gate.reason_codes == ["scan_function_not_inferred"]
    assert plan.handoff_kind == "database_relation_handoff"


@pytest.mark.parametrize("location_kind", [None, "directory", "prefix", "connection"])
def test_describe_query_context_demotes_non_object_root_only_location(
    tmp_path: Path,
    location_kind: str | None,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage_root = str(tmp_path / "orders")
    storage_kwargs = {
        "label": "Orders local storage",
        "storage_protocol": "rc:LocalFilesystemStorage",
        "storage_root": storage_root,
        "layout_verification_status": "rc:VerifiedByListingLayout",
    }
    if location_kind is not None:
        storage_kwargs["location_kind"] = location_kind
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_local_storage",
        **storage_kwargs,
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

    assert context.readiness == "needs_review"
    assert {issue.code for issue in context.issues} == {
        "storage_location_kind_needs_path_template"
    }
    assert context.storage_accesses[0].location_kind == location_kind
    target = context.query_target_candidates[0]
    assert target.template_source == "storage_access_location"
    assert target.location_kind == location_kind
    assert target.candidate_path == storage_root
    assert target.candidate_path_status == "orientation_only"
    assert target.review_required is True
    assert target.direct_review_required is True
    assert [reason.code for reason in target.review_reasons] == [
        "storage_location_kind_needs_path_template"
    ]
    assert [reason.code for reason in target.direct_review_reasons] == [
        "storage_location_kind_needs_path_template"
    ]
    assert context.query_target_decision.status == "candidate_needs_review"
    assert context.query_target_decision.candidate_index == 0
    assert context.query_target_decision.candidate_path == storage_root
    assert context.query_target_decision.candidate_path_status == "orientation_only"
    assert context.query_target_decision.direct_review_required is True
    assert context.query_target_decision.reason_codes == [
        "storage_location_kind_needs_path_template"
    ]
    plan = db.draft_query_plan(dataset)
    assert plan.scan.template_lineage is not None
    assert (
        "Candidate storage root comes from storage access Orders local storage."
        in plan.scan.template_lineage
    )
    assert "Template comes from storage_access_location" not in plan.scan.template_lineage


def test_record_map_storage_access_rejects_unknown_location_kind(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(
        DoxaBaseError,
        match="location_kind must be one of",
    ):
        db.record_map_storage_access(
            "https://example.test/project#orders_local_storage",
            location_kind="folder-ish",
        )


def test_query_target_storage_owned_template_warnings_do_not_bleed_to_siblings(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Feeds"
    storage = db.record_map_storage_access(
        "https://example.test/project#feeds_https_storage",
        label="Feeds HTTPS access",
        storage_protocol="rc:HTTPSStorage",
        storage_root="https://cdn.example.test/lake",
        path_templates=[
            "feeds/clean/date={date}.parquet",
            "s3://wrong-bucket/feeds/*.parquet",
        ],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#feeds_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Feeds",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "needs_review"
    assert any(
        issue.code == "storage_protocol_location_mismatch"
        and "path template from Feeds HTTPS access" in issue.message
        for issue in context.issues
    )
    clean_target = next(
        target
        for target in context.query_target_candidates
        if target.template == "feeds/clean/date={date}.parquet"
    )
    assert clean_target.candidate_path == (
        "https://cdn.example.test/lake/feeds/clean/date={date}.parquet"
    )
    assert clean_target.candidate_path_status == "ready"
    assert clean_target.review_required is False
    assert clean_target.review_reasons == []
    assert clean_target.direct_review_required is False
    assert clean_target.direct_review_reasons == []

    bad_target = next(
        target
        for target in context.query_target_candidates
        if target.template == "s3://wrong-bucket/feeds/*.parquet"
    )
    assert bad_target.candidate_path_status == "orientation_only"
    assert any(
        reason.code == "storage_protocol_location_mismatch"
        and "path template from Feeds HTTPS access" in reason.message
        for reason in bad_target.review_reasons
    )


def test_query_target_s3_storage_owned_template_warnings_do_not_bleed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Fleet"
    storage = db.record_map_storage_access(
        "https://example.test/project#fleet_s3_storage",
        label="Fleet S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        bucket_name="fleet-lake",
        key_prefix="warehouse",
        path_templates=[
            "fleet/storage-ok/dt={date}.parquet",
            "s3://wrong-bucket/raw/fleet/*.parquet",
            "warehouse/fleet/repeated/dt={date}.parquet",
        ],
        credential_reference="profile:fleet-readonly",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#fleet_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Fleet",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "needs_review"
    clean_target = next(
        target
        for target in context.query_target_candidates
        if target.template == "fleet/storage-ok/dt={date}.parquet"
    )
    assert clean_target.candidate_path == (
        "s3://fleet-lake/warehouse/fleet/storage-ok/dt={date}.parquet"
    )
    assert clean_target.candidate_path_status == "ready"
    assert clean_target.review_required is False
    assert clean_target.review_reasons == []

    wrong_bucket = next(
        target
        for target in context.query_target_candidates
        if target.template == "s3://wrong-bucket/raw/fleet/*.parquet"
    )
    assert wrong_bucket.candidate_path_status == "orientation_only"
    assert wrong_bucket.direct_review_required is True
    assert any(
        reason.code == "storage_protocol_location_mismatch"
        and "bucket_name" in reason.message
        for reason in wrong_bucket.direct_review_reasons
    )
    repeated_prefix = next(
        target
        for target in context.query_target_candidates
        if target.template == "warehouse/fleet/repeated/dt={date}.parquet"
    )
    assert repeated_prefix.candidate_path_status == "orientation_only"
    assert repeated_prefix.direct_review_required is True
    assert any(
        reason.code == "storage_protocol_location_mismatch"
        and "repeat recorded key_prefix" in reason.message
        for reason in repeated_prefix.direct_review_reasons
    )

    plan = db.draft_query_plan(dataset)
    assert plan.selected_candidate is not None
    assert plan.selected_candidate.template == "fleet/storage-ok/dt={date}.parquet"
    assert plan.review_gate.executable_without_review is False
    assert plan.review_gate.blocking_reason_codes == [
        "query_context_has_other_blockers"
    ]
    assert plan.review_gate.reason_codes == ["query_context_has_other_blockers"]
    assert plan.handoff_kind == "context_review_required"


def test_query_target_candidate_template_warnings_do_not_bleed_to_siblings(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    storage = db.record_map_storage_access(
        "https://example.test/project#events_local_storage",
        label="Events local access",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/warehouse",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    partition = db.record_map_partition_scheme(
        "https://example.test/project#events_verified_partition",
        label="Verified event partition",
        path_template="events/good/dt={date}.parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
        datasets=[dataset],
    )
    db.record_map_dataset(
        dataset,
        label="Events",
        is_table=True,
        path_templates=["s3://remote-bucket/events/bad/*.parquet"],
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "needs_review"
    assert any(
        issue.code == "storage_protocol_location_mismatch"
        and issue.resource is not None
        and issue.resource.iri == storage.iri
        and "path template from Events" in issue.message
        for issue in context.issues
    )

    dataset_target = next(
        target
        for target in context.query_target_candidates
        if target.template_source == "dataset"
    )
    assert dataset_target.candidate_path == "s3://remote-bucket/events/bad/*.parquet"
    assert dataset_target.candidate_path_status == "orientation_only"
    assert dataset_target.review_required is True
    assert dataset_target.direct_review_required is True
    assert any(
        reason.code == "storage_protocol_location_mismatch"
        and "path template from Events" in reason.message
        for reason in dataset_target.direct_review_reasons
    )

    partition_target = next(
        target
        for target in context.query_target_candidates
        if target.source_resource.iri == partition.iri
    )
    assert partition_target.candidate_path == "/warehouse/events/good/dt={date}.parquet"
    assert partition_target.candidate_path_status == "ready"
    assert partition_target.review_required is False
    assert partition_target.review_reasons == []
    assert partition_target.direct_review_required is False
    assert partition_target.direct_review_reasons == []


def test_query_target_candidates_scope_partition_blockers(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    storage = db.record_map_storage_access(
        "https://example.test/project#events_local_storage",
        label="Events local access",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/warehouse",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    verified_partition = db.record_map_partition_scheme(
        "https://example.test/project#events_verified_partition",
        label="Verified event partition",
        path_template="events/good/dt={date}.parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
        datasets=[dataset],
    )
    contradicted_partition = db.record_map_partition_scheme(
        "https://example.test/project#events_stale_partition",
        label="Stale event partition",
        path_template="events/stale/dt={date}.parquet",
        layout_verification_status="rc:ContradictedLayout",
        datasets=[dataset],
    )
    db.record_map_dataset(
        dataset,
        label="Events",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "blocked_by_contradiction"
    verified_target = next(
        target
        for target in context.query_target_candidates
        if target.source_resource.iri == verified_partition.iri
    )
    assert any(
        reason.code == "query_context_has_other_blockers"
        for reason in verified_target.review_reasons
    )
    assert verified_target.direct_review_required is False
    assert verified_target.direct_review_reasons == []
    assert not any(
        reason.code == "contradicted_layout"
        for reason in verified_target.review_reasons
    )

    contradicted_target = next(
        target
        for target in context.query_target_candidates
        if target.source_resource.iri == contradicted_partition.iri
    )
    assert any(
        reason.code == "contradicted_layout"
        for reason in contradicted_target.review_reasons
    )
    assert contradicted_target.direct_review_required is True
    assert any(
        reason.code == "contradicted_layout"
        for reason in contradicted_target.direct_review_reasons
    )


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
        and "Price analysis must filter" in warning.message
        and ".. Impact:" not in warning.message
        for warning in context.analysis_warnings
    )


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


def test_map_helpers_do_not_duplicate_column_links(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#messages"
    column = "https://example.test/project#message_id"

    db.record_map_dataset(
        table,
        label="Messages",
        is_table=True,
        columns=[column],
    )
    db.record_map_column(
        column,
        table_iri=table,
        column_name="message_id",
    )

    description = db.describe_dataset(table)
    assert [item.iri for item in description.columns] == [column]
    assert db.triple_count("map") == 6


@pytest.mark.parametrize(
    ("call", "match"),
    [
        pytest.param(
            lambda db: db.record_map_dataset(
                "https://example.test/project#messages",
                label="Messages",
                row_semantics="One row per source message.",
            ),
            "row_semantics.*not prose",
            id="dataset-row-semantics",
        ),
        pytest.param(
            lambda db: db.record_map_dataset(
                "https://example.test/project#messages",
                label="Messages",
                columns=["plain doc id column"],
            ),
            "columns.*not prose",
            id="dataset-column-link",
        ),
        pytest.param(
            lambda db: db.record_map_dataset(
                "https://example.test/project#messages",
                label="Messages",
                caveats=["body caveat prose"],
            ),
            "caveats.*not prose",
            id="dataset-caveat-link",
        ),
        pytest.param(
            lambda db: db.record_map_dataset(
                "https://example.test/project#messages",
                label="Messages",
                storage_accesses=["local parquet access"],
            ),
            "storage_accesses.*not prose",
            id="dataset-storage-link",
        ),
        pytest.param(
            lambda db: db.record_map_dataset(
                "https://example.test/project#messages",
                label="Messages",
                physical_layouts=["parquet physical layout"],
            ),
            "physical_layouts.*not prose",
            id="dataset-layout-link",
        ),
        pytest.param(
            lambda db: db.record_map_dataset(
                "https://example.test/project#messages",
                label="Messages",
                companion_datasets=["attachment companion table"],
            ),
            "companion_datasets.*not prose",
            id="dataset-companion-link",
        ),
        pytest.param(
            lambda db: db.record_map_dataset(
                "https://example.test/project#messages",
                label="Messages",
                extra_types=["special table class"],
            ),
            "extra_types.*not prose",
            id="dataset-extra-type",
        ),
        pytest.param(
            lambda db: db.record_map_column(
                "https://example.test/project#messages__doc_id",
                column_name="doc_id",
                physical_type="plain varchar prose",
            ),
            "physical_type.*not prose",
            id="column-physical-type",
        ),
        pytest.param(
            lambda db: db.record_map_column(
                "https://example.test/project#messages__doc_id",
                table_iri="plain table prose",
                column_name="doc_id",
            ),
            "table_iri.*not prose",
            id="column-table",
        ),
        pytest.param(
            lambda db: db.record_map_caveat(
                "https://example.test/project#body_caveat",
                description="Body text is cleaned text, not raw source text.",
                severity="high confidence warning",
            ),
            "severity.*not prose",
            id="caveat-severity",
        ),
        pytest.param(
            lambda db: db.record_map_caveat(
                "https://example.test/project#body_caveat",
                description="Body text is cleaned text, not raw source text.",
                targets=["the messages table"],
            ),
            "targets.*not prose",
            id="caveat-target",
        ),
        pytest.param(
            lambda db: db.record_map_storage_access(
                "https://example.test/project#local_access",
                storage_protocol="local filesystem storage",
            ),
            "storage_protocol.*not prose",
            id="storage-protocol",
        ),
        pytest.param(
            lambda db: db.record_map_storage_access(
                "https://example.test/project#local_access",
                datasets=["the messages table"],
            ),
            "datasets.*not prose",
            id="storage-dataset",
        ),
        pytest.param(
            lambda db: db.record_map_physical_layout(
                "https://example.test/project#messages_layout",
                file_format="parquet files",
            ),
            "file_format.*not prose",
            id="layout-file-format",
        ),
        pytest.param(
            lambda db: db.record_map_partition_scheme(
                "https://example.test/project#messages_partitioning",
                partition_columns=["the date column"],
            ),
            "partition_columns.*not prose",
            id="partition-column",
        ),
        pytest.param(
            lambda db: db.record_map_relationship(
                "https://example.test/project#attachment_parent_fk",
                relationship_type="foreign_key",
                from_column="parent doc id column",
                to_column="https://example.test/project#messages__doc_id",
            ),
            "from_column.*not prose",
            id="relationship-foreign-key-column",
        ),
        pytest.param(
            lambda db: db.record_map_relationship(
                "https://example.test/project#attachment_count_rollup",
                relationship_type="aggregation",
                aggregated_columns=[
                    {
                        "target_column": "attachment count column",
                        "source_columns": [
                            "https://example.test/project#attachments__parent_doc_id",
                        ],
                    },
                ],
            ),
            r"aggregated_columns\[1\]\.target_column.*not prose",
            id="relationship-aggregate-target",
        ),
    ],
)
def test_map_helpers_reject_prose_for_resource_fields(
    tmp_path: Path,
    call: Callable[[DoxaBase], object],
    match: str,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match=match):
        call(db)


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


def test_describe_dataset_returns_all_partition_columns(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/project#"
    table = f"{base}orders"
    order_date = f"{base}orders__order_date"
    region = f"{base}orders__region"
    partition_scheme = f"{base}orders_daily_region_partitioning"

    db.record_map_dataset(table, label="Orders", is_table=True)
    db.record_map_column(
        order_date,
        table_iri=table,
        column_name="order_date",
        physical_type="rc:Date",
    )
    db.record_map_column(
        region,
        table_iri=table,
        column_name="region",
        physical_type="rc:Varchar",
    )
    db.record_map_partition_scheme(
        partition_scheme,
        partition_columns=[region, order_date],
        granularity="rc:Daily",
        datasets=[table],
    )

    partition_description = db.describe_dataset(table).partition_schemes[0]

    assert {column.iri for column in partition_description.partition_columns} == {
        order_date,
        region,
    }
    assert partition_description.partition_column is not None
    assert partition_description.partition_column.iri in {order_date, region}


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


def test_describe_context_slice_warns_when_seed_profile_mismatches(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Messages"
    db.record_map_dataset(dataset, label="Messages", is_table=True)
    pattern = db.record_pattern(
        summary="Messages have stable document identifiers.",
        pattern_text="Use document identifiers when joining message exports.",
        rationale="Exercise profile mismatch guidance for pattern seeds.",
        pattern_targets=[dataset],
        source_path="tests/test_doxabase_core.py",
        source_kind="rc:DocumentationSource",
    )

    dataset_slice = db.describe_context_slice(
        pattern.pattern_iri,
        profile="dataset_brief",
    )

    assert dataset_slice.pattern_contexts == []
    assert any(
        "Seed is an rc:Pattern; rerun with profile='pattern_brief' or 'deep_lore'."
        in warning
        for warning in dataset_slice.warnings
    )

    pattern_slice = db.describe_context_slice(
        pattern.pattern_iri,
        profile="pattern_brief",
    )
    assert [context.iri for context in pattern_slice.pattern_contexts] == [
        pattern.pattern_iri
    ]
    assert pattern_slice.warnings == []


def test_describe_context_slice_includes_profile_observations_and_metrics(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    column = "https://example.test/project#orders__amount"
    metric_kind = "https://example.test/project#CompletenessRatio"
    db.record_map_dataset(dataset, label="Orders", is_table=True, columns=[column])
    db.record_map_column(
        column,
        table_iri=dataset,
        column_name="amount",
        physical_type="rc:Decimal",
    )
    dataset_profile = db.record_dataset_profile(
        dataset,
        summary="Orders were profiled for completeness.",
        evidence_summary="Dataset profile run.",
        evidence_sources=["test://orders-profile"],
        row_count=100,
        value_frequencies=[{"value": "present", "frequency": 98}],
        profile_metrics=[
            {"metric": metric_kind, "value": 0.98, "target": dataset},
        ],
        update_map_snapshot=False,
    )
    column_profile = db.record_column_profile(
        column,
        table_iri=dataset,
        column_name="amount",
        summary="Amount was profiled for mean value.",
        evidence_summary="Column profile run.",
        evidence_sources=["test://amount-profile"],
        profile_metrics=[{"metric": "rc:MeanValue", "value": 42.5}],
        update_map_column=False,
    )
    dataset_metric_iri = db._objects(
        ["observations"],
        dataset_profile.observation.observation_iri,
        "rc:observedProfileMetric",
    )[0]
    value_frequency_iri = db._objects(
        ["observations"],
        dataset_profile.observation.observation_iri,
        "rc:observedValueFrequency",
    )[0]

    context_slice = db.describe_context_slice(
        dataset,
        profile="dataset_brief",
        max_triples=300,
    )

    resources = {resource.iri: resource for resource in context_slice.resources}
    assert dataset_profile.observation.observation_iri in resources
    assert column_profile.observation.observation_iri in resources
    assert dataset_metric_iri in resources
    assert value_frequency_iri in resources
    assert metric_kind in resources
    assert resources[metric_kind].referenced_only is True
    assert dataset_profile.observation.evidence_iri in resources
    assert context_slice.route_counts["dataset_profile_observation"] == 1
    assert context_slice.route_counts["column_profile_observation"] == 1
    assert context_slice.route_counts["observed_profile_metric"] >= 2
    assert context_slice.route_counts["observed_value_frequency"] == 1
    assert context_slice.route_counts["profile_metric_kind"] >= 2


def test_context_slice_structures_seed_profile_outside_bounded_dataset_profiles(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    old_profile = db.record_dataset_profile(
        dataset,
        summary="Old one-off profile run.",
        observed_at="2026-01-01T00:00:00Z",
        evidence_summary="Old profile evidence.",
        evidence_sources=["test://orders-old-profile"],
        evidence_iri="https://example.test/project#OldProfileEvidence",
        row_count=10,
        update_map_snapshot=False,
    )
    for index in range(6):
        db.record_dataset_profile(
            dataset,
            summary=f"Newer profile run {index}.",
            observed_at=f"2026-02-{index + 1:02d}T00:00:00Z",
            evidence_summary=f"Newer profile evidence {index}.",
            evidence_sources=[f"test://orders-new-profile-{index}"],
            row_count=100 + index,
            update_map_snapshot=False,
        )

    context_slice = db.describe_context_slice(
        old_profile.observation.observation_iri,
        profile="dataset_brief",
        max_triples=300,
    )

    dataset_context = context_slice.dataset_contexts[0]
    returned_profile_iris = {
        profile.iri for profile in dataset_context.profile_observations
    }
    assert old_profile.observation.observation_iri not in returned_profile_iris
    assert dataset_context.profile_summary.omitted_dataset_profile_count == 2
    assert old_profile.observation.evidence_iri not in (
        dataset_context.profile_summary.evidence_iris
    )

    assert [
        profile.iri for profile in context_slice.seed_profile_observations
    ] == [old_profile.observation.observation_iri]
    assert [
        evidence.iri
        for evidence in context_slice.seed_profile_observations[0].evidence
    ] == [old_profile.observation.evidence_iri]
    assert any("warnings" in step for step in context_slice.reading_order)
    assert any(
        "seed_profile_observations" in step
        for step in context_slice.reading_order
    )
    assert context_slice.route_counts["seed_profile_observation"] == 1
    resources = {resource.iri: resource for resource in context_slice.resources}
    assert old_profile.observation.observation_iri in resources
    assert old_profile.observation.evidence_iri in resources


def test_describe_context_slice_expands_unmapped_observed_column_seed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    promo_column = "https://example.test/project#orders__promo_code"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled for redacted promo-code metrics.",
        evidence_summary="Orders profile run.",
        evidence_sources=["test://orders-profile"],
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": promo_column,
                "column_name": "promo_code",
                "summary": "Sampled redacted promo-code metrics.",
                "profile_metrics": [
                    {
                        "metric": "https://example.test/project#SuppressedValueBucketCount",
                        "value": 3,
                    }
                ],
            }
        ],
    )

    context_slice = db.describe_context_slice(
        [promo_column],
        profile="dataset_brief",
        max_triples=300,
    )

    profile_observation_iri = bundle.column_profiles[0].observation.observation_iri
    resources = {resource.iri: resource for resource in context_slice.resources}
    assert promo_column in resources
    assert resources[promo_column].referenced_only is True
    assert resources[promo_column].primary_route.route == "seed"
    assert any(
        route.route == "seed_observed_column"
        for route in resources[promo_column].routes
    )
    assert profile_observation_iri in resources
    assert dataset in resources
    assert context_slice.dataset_contexts[0].iri == dataset
    assert [
        profile.iri for profile in context_slice.seed_profile_observations
    ] == [profile_observation_iri]
    assert context_slice.route_counts["seed_observed_column"] == 1
    assert context_slice.route_counts["seed_profile_observation"] == 1
    assert context_slice.route_counts["observed_column"] == 1
    assert "Seed resource" not in " ".join(context_slice.warnings)


def test_describe_context_slice_expands_unmapped_observed_column_after_workflow_import(
    tmp_path: Path,
) -> None:
    source = DoxaBase.create(tmp_path / "source.sqlite")
    dataset = "https://example.test/project#Orders"
    promo_column = "https://example.test/project#orders__promo_code"
    source.record_map_dataset(dataset, label="Orders", is_table=True)
    bundle = source.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled for redacted promo-code metrics.",
        evidence_summary="Orders profile run.",
        evidence_sources=["test://orders-profile"],
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": promo_column,
                "column_name": "promo_code",
                "summary": "Sampled redacted promo-code metrics.",
                "profile_metrics": [
                    {
                        "metric": "https://example.test/project#SuppressedValueBucketCount",
                        "value": 3,
                    }
                ],
            }
        ],
    )
    export_path = tmp_path / "workflow.trig"

    export_result = source.export_trig(export_path, graphs="workflow")
    imported = DoxaBase.create(tmp_path / "workflow-import.sqlite")
    import_counts = imported.import_trig(export_path)
    context_slice = imported.describe_context_slice(
        [promo_column],
        profile="dataset_brief",
        max_triples=300,
    )

    assert "ontology" not in export_result.graphs
    assert import_counts["observations"] == source.triple_count("observations")
    profile_observation_iri = bundle.column_profiles[0].observation.observation_iri
    resources = {resource.iri: resource for resource in context_slice.resources}
    assert promo_column in resources
    assert resources[promo_column].referenced_only is True
    assert any(
        route.route == "seed_observed_column"
        for route in resources[promo_column].routes
    )
    assert profile_observation_iri in resources
    assert dataset in resources
    assert [
        profile.iri for profile in context_slice.seed_profile_observations
    ] == [profile_observation_iri]
    assert context_slice.route_counts["seed_observed_column"] == 1
    assert context_slice.route_counts["seed_profile_observation"] == 1
    assert context_slice.route_counts["observed_column"] == 1
    assert "Seed resource" not in " ".join(context_slice.warnings)


def test_describe_context_slice_expands_profile_metric_kind_seed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    metric_kind = "https://example.test/project#CompletenessRatio"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    profile = db.record_dataset_profile(
        dataset,
        summary="Orders were profiled for completeness.",
        evidence_summary="Dataset profile run.",
        evidence_sources=["test://orders-profile"],
        profile_metrics=[
            {"metric": metric_kind, "value": 0.98, "target": dataset},
        ],
        update_map_snapshot=False,
    )
    metric_iri = db._objects(
        ["observations"],
        profile.observation.observation_iri,
        "rc:observedProfileMetric",
    )[0]

    context_slice = db.describe_context_slice(
        metric_kind,
        profile="dataset_brief",
        max_triples=200,
    )

    resources = {resource.iri: resource for resource in context_slice.resources}
    assert metric_kind in resources
    assert resources[metric_kind].referenced_only is True
    assert metric_iri in resources
    assert profile.observation.observation_iri in resources
    assert dataset in resources
    assert context_slice.dataset_contexts[0].iri == dataset
    assert context_slice.route_counts["seed_profile_metric_kind"] == 1
    assert context_slice.route_counts["observed_profile_metric"] >= 1
    assert context_slice.route_counts["profile_metric_observation"] == 1
    assert "profile-specific expansion did not apply" not in " ".join(
        context_slice.warnings
    )

    metric_context = db.describe_context_slice(
        metric_iri,
        profile="dataset_brief",
        max_triples=200,
    )
    metric_resources = {resource.iri: resource for resource in metric_context.resources}
    assert metric_iri in metric_resources
    assert profile.observation.observation_iri in metric_resources
    assert dataset in metric_resources
    assert metric_context.route_counts["observed_profile_metric"] >= 1
    assert metric_context.route_counts["profile_metric_observation"] == 1

    observation_context = db.describe_context_slice(
        profile.observation.observation_iri,
        profile="dataset_brief",
        max_triples=200,
    )
    observation_resources = {
        resource.iri: resource for resource in observation_context.resources
    }
    assert profile.observation.observation_iri in observation_resources
    assert metric_iri in observation_resources
    assert dataset in observation_resources
    assert observation_context.route_counts["seed_profile_observation"] == 1
    assert observation_context.route_counts["observed_profile_metric"] >= 1


def test_describe_context_slice_caps_broad_profile_metric_kind_seed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    metric_kind = "rc:MeanValue"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    for index in range(27):
        db.record_dataset_profile(
            dataset,
            summary=f"Orders profile run {index}.",
            observed_at=f"2026-01-{index + 1:02d}T00:00:00+00:00",
            evidence_summary=f"Dataset profile run {index}.",
            evidence_sources=[f"test://orders-profile/{index}"],
            profile_metrics=[
                {"metric": metric_kind, "value": index, "target": dataset},
            ],
            update_map_snapshot=False,
        )

    context_slice = db.describe_context_slice(
        metric_kind,
        profile="dataset_brief",
        max_triples=1000,
    )

    assert context_slice.route_counts["seed_profile_metric_kind"] == 1
    assert context_slice.route_counts["profile_metric_observation"] == 25
    assert any(
        "matched 27 observed profile metric(s); included 25 and omitted 2"
        in warning
        for warning in context_slice.warnings
    )


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


def test_search_finds_uri_object_terms_for_profile_metric_kinds(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    metric_kind = "https://example.test/project#CompletenessRatio"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_dataset_profile(
        dataset,
        summary="Orders completeness profile",
        profile_metrics=[
            {"metric": metric_kind, "value": 0.98, "target": dataset},
        ],
        update_map_snapshot=False,
    )

    results = db.search("CompletenessRatio", graph="observations")
    match = next(
        result
        for result in results.matches
        if result.predicate == RC + "profileMetricKind"
    )
    assert match.text == metric_kind
    assert match.types == [RC + "ObservedProfileMetric"]

    entities = db.list_entities(
        type="rc:ObservedProfileMetric",
        graph="observations",
        text="CompletenessRatio",
    ).entities
    assert [entity.iri for entity in entities] == [match.iri]

    described = db.describe_dataset(dataset)
    described_metric_iris = {
        metric.iri
        for profile in described.profile_observations
        for metric in profile.profile_metrics
    }
    assert match.iri in described_metric_iris


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

    pattern_context_slice = db.describe_context_slice(
        [pattern.pattern_iri],
        profile="pattern_brief",
    )
    assert pattern_context_slice.route_counts["incoming_claim_reconsideration"] == 1
    assert pattern_context_slice.route_counts["reconsidering_claim"] == 1
    assert [context.iri for context in pattern_context_slice.pattern_contexts] == [
        pattern.pattern_iri
    ]


def test_context_slice_column_seed_expands_claim_reconsideration_lore(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/payments#transactions"
    column = "https://example.test/payments#transactions__merchant_category"
    db.record_map_dataset(
        dataset,
        label="Payments transactions",
        is_table=True,
    )
    db.record_map_column(
        column,
        table_iri=dataset,
        column_name="merchant_category",
        physical_type="rc:Varchar",
    )
    older = db.record_claim_observation(
        summary="Merchant category looked like a stable domain.",
        claim_text="merchant_category appeared to be a stable merchant domain.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=[column],
        evidence_sources=["scratch://merchant-category-profile.json"],
    )
    newer = db.record_claim_observation(
        summary="Merchant category needs acquirer-specific caveats.",
        claim_text=(
            "merchant_category is acquirer-normalized and should not be treated "
            "as a universal closed domain."
        ),
        claim_kind="rc:CaveatClaim",
        claim_targets=[column],
        evidence_sources=["scratch://merchant-category-review.json"],
        observation_status="rc:Checked",
    )
    db.record_claim_reconsideration(
        newer_claim=newer.claim_iri,
        older_claim=older.claim_iri,
        relation="weakens",
        rationale="Later review shows the original domain claim was too broad.",
        evidence_sources=["scratch://merchant-category-reconsideration.json"],
    )
    followup = db.record_pattern(
        summary="Merchant category claims require acquirer caveats.",
        pattern_text=(
            "Use the checked caveat claim before reusing the earlier merchant "
            "category domain hunch."
        ),
        rationale="Both claims target the same mapped column.",
        pattern_targets=[column],
        supporting_claims=[older.claim_iri, newer.claim_iri],
    )

    context_slice = db.describe_context_slice([column], profile="deep_lore")

    assert not context_slice.warnings
    assert context_slice.dataset_contexts[0].iri == dataset
    assert followup.pattern_iri in [
        pattern_context.iri for pattern_context in context_slice.pattern_contexts
    ]
    assert context_slice.route_counts["seed_column"] == 1
    assert context_slice.route_counts["related_dataset"] == 1
    assert context_slice.route_counts["supporting_claim"] >= 2
    assert context_slice.route_counts["claim_target"] >= 2
    assert context_slice.route_counts["incoming_claim_reconsideration"] == 1
    assert context_slice.route_counts["reconsidering_claim"] == 1
    route_legend = {row.route: row for row in context_slice.route_legend}
    assert route_legend["seed_column"].meaning == (
        "A seed resource expanded as a mapped column."
    )


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
    observed_asset = "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"

    result = db.record_observation(
        summary="AIS daily broadcasts were sampled for row coverage.",
        observation_type="profile",
        observed_asset=observed_asset,
        observed_at="2026-05-31T12:00:00Z",
        observed_by="urn:doxabase:test-agent",
        evidence_summary="Synthetic test evidence for the observation writer.",
        evidence_sources=["tests/test_doxabase_core.py"],
        sample_size=100,
        sample_scope="Full synthetic AIS fixture used by the test.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=123,
        distinct_count=45,
        value_frequencies=[
            {"value": "open", "frequency": 70},
            {"value": "closed", "frequency": 53},
        ],
        profile_metrics=[
            {"metric": "rc:MinimumValue", "value": 1.5, "target": observed_asset},
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
        URIRef(RC + "sampleSize"),
        Literal(100),
    ) in observations
    assert (
        observation_iri,
        URIRef(RC + "sampleScope"),
        Literal("Full synthetic AIS fixture used by the test."),
    ) in observations
    assert (
        observation_iri,
        URIRef(RC + "sampleMethod"),
        Literal("DuckDB full-table aggregate profile."),
    ) in observations
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
    assert any(
        (
            metric_iri,
            URIRef(RC + "profileMetricTarget"),
            URIRef(observed_asset),
        )
        in observations
        for metric_iri in metric_iris
    )
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


def test_record_observation_rejects_unknown_rc_profile_metric_kind(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match="unknown rc: profile metric kind"):
        db.record_observation(
            summary="Profile used a mistyped rc metric kind.",
            observation_type="profile",
            observed_asset="https://example.test/project#Orders",
            profile_metrics=[{"metric": "rc:MinValue", "value": 1}],
        )


def test_record_observation_accepts_project_profile_metric_kind_iri(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    metric_kind = "https://example.test/project#CompletenessRatio"

    result = db.record_observation(
        summary="Profile used a project-specific metric kind.",
        observation_type="profile",
        observed_asset="https://example.test/project#Orders",
        profile_metrics=[
            {
                "metric_kind": metric_kind,
                "value": "0.98",
                "datatype": "xsd:decimal",
            }
        ],
    )

    observations = db.to_graph(["observations"])
    metric_iri = next(
        observations.objects(
            URIRef(result.observation_iri),
            URIRef(RC + "observedProfileMetric"),
        )
    )
    assert (
        metric_iri,
        URIRef(RC + "profileMetricKind"),
        URIRef(metric_kind),
    ) in observations


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
        sample_size=123,
        sample_scope="All rows in the local Messages test table.",
        sample_method="DuckDB aggregate query over the full table.",
        row_count=123,
        distinct_count=120,
        value_frequencies=[
            {"value": "open", "frequency": 80},
            {"value": "closed", "frequency": 43},
        ],
        profile_metrics=[
            {"metric": "rc:MinimumValue", "value": 1, "target": dataset},
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
    assert description.profile_summary.returned_dataset_profile_count == 1
    assert description.profile_summary.returned_mapped_column_profile_count == 0
    assert description.profile_summary.returned_unmapped_column_profile_count == 0
    assert description.profile_summary.returned_profile_count == 1
    assert description.profile_summary.shared_evidence_iris == [
        result.observation.evidence_iri
    ]
    assert "Profile lore is observed evidence" in (
        description.profile_summary.handoff_note
    )
    assert "physical metadata gaps" in description.profile_summary.handoff_note
    profile = description.profile_observations[0]
    assert profile.iri == result.observation.observation_iri
    assert profile.sample_size == 123
    assert profile.sample_scope == "All rows in the local Messages test table."
    assert profile.sample_method == "DuckDB aggregate query over the full table."
    assert profile.row_count == 123
    assert profile.distinct_count == 120
    assert profile.null_count is None
    assert [(item.value, item.frequency) for item in profile.value_frequencies] == [
        ("open", 80),
        ("closed", 43),
    ]
    assert {
        (
            item.metric.iri,
            item.target.iri if item.target is not None else None,
            item.value,
            item.value_datatype,
        )
        for item in profile.profile_metrics
    } == {
        (RC + "MinimumValue", dataset, "1", str(XSD.integer)),
        (RC + "MaximumValue", None, "123", str(XSD.integer)),
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
        sample_size=123,
        sample_scope="All doc_id values in the local Messages test table.",
        sample_method="DuckDB column aggregate query over the full table.",
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
    assert profile.sample_size == 123
    assert profile.sample_scope == "All doc_id values in the local Messages test table."
    assert profile.sample_method == "DuckDB column aggregate query over the full table."
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


def test_describe_dataset_surfaces_unmapped_column_profile_observations(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Orders"
    column = "https://example.test/project#OrdersStatus"
    db.record_map_dataset(table, label="Orders", is_table=True)

    result = db.record_column_profile(
        column,
        column_name="status",
        table_iri=table,
        summary="Sampled status values were profiled without updating the map.",
        evidence_summary="Synthetic sampled top-N profile output.",
        evidence_sources=["test://orders-status-topn"],
        sample_size=50,
        sample_scope="Fifty sampled Orders rows.",
        sample_method="Top-N value-frequency query over a sample.",
        null_count=0,
        distinct_count=4,
        value_frequencies=[
            {"value": "fulfilled", "frequency": 38},
            {"value": "pending", "frequency": 8},
        ],
        update_map_column=False,
    )

    description = db.describe_dataset(table)

    assert description.columns == []
    assert description.profile_observations == []
    assert description.profile_summary.returned_dataset_profile_count == 0
    assert description.profile_summary.returned_mapped_column_profile_count == 0
    assert description.profile_summary.returned_unmapped_column_profile_count == 1
    assert description.profile_summary.returned_profile_count == 1
    assert description.profile_summary.shared_evidence_iris == [
        result.observation.evidence_iri
    ]
    assert "not mapped as current columns" in (
        description.profile_summary.handoff_note
    )
    assert len(description.unmapped_column_profile_observations) == 1
    profile = description.unmapped_column_profile_observations[0]
    assert profile.iri == result.observation.observation_iri
    assert profile.observed_asset is not None
    assert profile.observed_asset.iri == table
    assert profile.observed_column is not None
    assert profile.observed_column.iri == column
    assert profile.observed_column_name == "status"
    assert profile.observed_column.column_name == "status"
    assert profile.sample_scope == "Fifty sampled Orders rows."
    assert [(item.value, item.frequency) for item in profile.value_frequencies] == [
        ("fulfilled", 38),
        ("pending", 8),
    ]

    db.record_map_column(column, column_name="status", table_iri=table)

    description = db.describe_dataset(table)
    assert [item.iri for item in description.columns] == [column]
    assert description.unmapped_column_profile_observations == []
    assert description.profile_summary.returned_mapped_column_profile_count == 1
    assert description.profile_summary.returned_unmapped_column_profile_count == 0
    assert description.profile_summary.mapped_profiled_column_count == 1
    assert description.columns[0].profile_observations[0].iri == (
        result.observation.observation_iri
    )

    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_profile_summary_reports_bounded_profile_omissions(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Orders"
    db.record_map_dataset(table, label="Orders", is_table=True)

    for index in range(7):
        db.record_column_profile(
            f"https://example.test/project#OrdersProfiledColumn{index}",
            column_name=f"profiled_{index}",
            table_iri=table,
            summary=f"Profiled Orders column {index}.",
            evidence_summary=f"Synthetic profile output {index}.",
            evidence_sources=[f"test://orders-profile-{index}"],
            sample_size=25,
            sample_scope="Sampled Orders rows.",
            sample_method="Synthetic profile query.",
            null_count=0,
            distinct_count=3,
            update_map_column=False,
        )

    description = db.describe_dataset(table)

    assert len(description.unmapped_column_profile_observations) == 5
    assert description.profile_summary.returned_dataset_profile_count == 0
    assert description.profile_summary.returned_mapped_column_profile_count == 0
    assert description.profile_summary.returned_unmapped_column_profile_count == 5
    assert description.profile_summary.returned_profile_count == 5
    assert description.profile_summary.total_dataset_profile_count == 0
    assert description.profile_summary.total_mapped_column_profile_count == 0
    assert description.profile_summary.total_unmapped_column_profile_count == 7
    assert description.profile_summary.total_profile_count == 7
    assert description.profile_summary.omitted_dataset_profile_count == 0
    assert description.profile_summary.omitted_mapped_column_profile_count == 0
    assert description.profile_summary.omitted_unmapped_column_profile_count == 2
    assert description.profile_summary.omitted_profile_count == 2
    assert "2 additional profile observation(s)" in (
        description.profile_summary.handoff_note
    )

    context_slice = db.describe_context_slice([table], profile="deep_lore")

    assert context_slice.dataset_contexts[0].profile_summary.omitted_profile_count == 2


def test_record_profile_bundle_writes_dataset_and_column_profiles(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    amount_column = "https://example.test/project#OrdersAmount"
    shared_evidence = "https://example.test/project#OrdersProfileRunEvidence"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        physical_type="rc:Varchar",
    )

    result = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled with row count and column sketches.",
        observed_by="urn:doxabase:test-agent",
        evidence_summary="Synthetic DuckDB profiling pass.",
        evidence_sources=["test://orders-profile"],
        sample_size=100,
        sample_scope="All rows in the local Orders table.",
        sample_method="DuckDB full-table profiling query.",
        row_count=100,
        map_label="Orders",
        is_table=True,
        shared_evidence_iri=shared_evidence,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Top status values were observed in the profile.",
                "distinct_count": 3,
                "value_frequencies": [
                    {"value": "fulfilled", "frequency": 70},
                    {"value": "pending", "frequency": 20},
                ],
            },
            {
                "column_iri": amount_column,
                "column_name": "amount",
                "summary": "Order amount was profiled as a non-null decimal.",
                "null_count": 0,
                "profile_metrics": [{"metric": "rc:MeanValue", "value": 42.5}],
                "update_map_column": True,
                "physical_type": "rc:Decimal",
                "nullable": False,
            },
        ],
    )

    assert result.dataset_iri == dataset
    assert result.shared_evidence_iri == shared_evidence
    assert result.dataset_profile.observation.observation_type == "profile"
    assert result.dataset_profile.map_dataset is not None
    assert len(result.column_profiles) == 2
    assert result.column_profiles[0].map_column is None
    assert result.column_profiles[1].map_column is not None
    assert result.dataset_profile.observation.evidence_iri == shared_evidence
    assert {
        column_profile.observation.evidence_iri
        for column_profile in result.column_profiles
    } == {shared_evidence}
    assert result.handoff_entrypoints.dataset_iri == dataset
    assert result.handoff_entrypoints.shared_evidence_iri == shared_evidence
    assert result.handoff_entrypoints.dataset_profile_observation_iri == (
        result.dataset_profile.observation.observation_iri
    )
    profile_observation_iris = [
        result.dataset_profile.observation.observation_iri,
        *(
            column_profile.observation.observation_iri
            for column_profile in result.column_profiles
        ),
    ]
    assert set(result.handoff_entrypoints.profile_observation_iris) == {
        result.dataset_profile.observation.observation_iri,
        *(
            column_profile.observation.observation_iri
            for column_profile in result.column_profiles
        ),
    }
    assert result.handoff_entrypoints.map_dataset_recorded is True
    assert result.handoff_entrypoints.map_column_iris == [amount_column]
    assert result.handoff_entrypoints.updated_map_column_iris == [amount_column]
    assert result.handoff_entrypoints.mapped_profiled_column_iris == [
        status_column,
        amount_column,
    ]
    assert result.handoff_entrypoints.dataset_describe_available is True
    assert result.handoff_entrypoints.profile_run_available is True
    assert result.handoff_entrypoints.suggested_next_calls[0] == (
        f"describe_dataset('{dataset}')"
    )
    assert result.handoff_entrypoints.suggested_next_calls[1] == (
        f"describe_profile_run('{dataset}', '{shared_evidence}')"
    )
    assert result.handoff_entrypoints.suggested_next_calls[-1] == (
        f"describe_context_slice({profile_observation_iris!r}, "
        "profile='dataset_brief')"
    )

    description = db.describe_dataset(dataset)

    assert description.label == "Orders"
    assert description.row_count_snapshot == 100
    assert description.profile_summary.returned_dataset_profile_count == 1
    assert description.profile_summary.returned_mapped_column_profile_count == 2
    assert description.profile_summary.returned_unmapped_column_profile_count == 0
    assert description.profile_summary.returned_profile_count == 3
    assert description.profile_summary.mapped_profiled_column_count == 2
    assert description.profile_summary.evidence_iris == [shared_evidence]
    assert description.profile_summary.evidence_profile_counts == {
        shared_evidence: 3,
    }
    assert description.profile_summary.shared_evidence_iris == [shared_evidence]
    assert [
        candidate.evidence_iri
        for candidate in description.profile_summary.profile_run_candidates
    ] == [shared_evidence]
    assert set(
        description.profile_summary.profile_run_candidates[0].profile_observation_iris
    ) == {
        result.dataset_profile.observation.observation_iri,
        *(
            column_profile.observation.observation_iri
            for column_profile in result.column_profiles
        ),
    }
    assert (
        description.profile_summary.profile_run_candidates[0].returned_profile_count
        == 3
    )
    assert (
        description.profile_summary.profile_run_candidates[
            0
        ].shared_by_all_returned_profiles
        is True
    )
    assert "3 profile observation(s)" in description.profile_summary.handoff_note
    assert "one profiler run" in description.profile_summary.handoff_note
    assert len(description.profile_observations) == 1
    dataset_profile = description.profile_observations[0]
    assert dataset_profile.sample_scope == "All rows in the local Orders table."
    assert dataset_profile.evidence[0].iri == shared_evidence
    assert dataset_profile.evidence[0].sources == ["test://orders-profile"]

    assert {column.iri for column in description.columns} == {
        status_column,
        amount_column,
    }
    amount_description = next(
        column for column in description.columns if column.iri == amount_column
    )
    amount_profile = amount_description.profile_observations[0]
    assert amount_profile.sample_method == "DuckDB full-table profiling query."
    assert amount_profile.null_count == 0
    assert amount_profile.profile_metrics[0].metric.iri == RC + "MeanValue"
    assert amount_description.nullable is False
    assert amount_description.physical_type is not None
    assert amount_description.physical_type.iri == RC + "Decimal"
    status_description = next(
        column for column in description.columns if column.iri == status_column
    )
    assert status_description.profile_observations[0].distinct_count == 3
    assert [
        (item.value, item.frequency)
        for item in status_description.profile_observations[0].value_frequencies
    ] == [
        ("fulfilled", 70),
        ("pending", 20),
    ]

    unmapped = description.unmapped_column_profile_observations
    assert unmapped == []

    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_record_profile_bundle_pattern_support_scope_all_profiles(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    amount_column = "https://example.test/project#OrdersAmount"
    shared_evidence = "https://example.test/project#OrdersProfileRunEvidence"

    result = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled with row count and column sketches.",
        evidence_summary="Synthetic DuckDB profiling pass.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=shared_evidence,
        row_count=100,
        map_label="Orders",
        is_table=True,
        pattern_summary="Orders profile pass supports a run-level synthesis.",
        pattern_text=(
            "The dataset profile and column profiles came from one Orders "
            "profiling pass."
        ),
        pattern_rationale=(
            "The row count, status distribution, and amount mean all link to "
            "the same shared run evidence."
        ),
        pattern_support_scope="all_profiles",
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Top status values were observed in the profile.",
                "distinct_count": 3,
            },
            {
                "column_iri": amount_column,
                "column_name": "amount",
                "summary": "Order amount was profiled.",
                "profile_metrics": [{"metric": "rc:MeanValue", "value": 42.5}],
            },
        ],
    )

    assert result.dataset_profile.pattern is not None
    pattern = db.describe_pattern(result.dataset_profile.pattern.pattern_iri)
    assert [target.iri for target in pattern.pattern_targets] == [dataset]
    assert [target.iri for target in pattern.map_implications] == [dataset]
    assert [evidence.iri for evidence in pattern.evidence] == [shared_evidence]
    assert {item.iri for item in pattern.supporting_observations} == {
        result.dataset_profile.observation.observation_iri,
        *[
            column_profile.observation.observation_iri
            for column_profile in result.column_profiles
        ],
    }

    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_record_profile_bundle_default_pattern_scope_is_dataset_profile(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"

    result = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled with row count and column sketches.",
        evidence_summary="Synthetic DuckDB profiling pass.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri="https://example.test/project#OrdersProfileRunEvidence",
        row_count=100,
        pattern_summary="Orders dataset profile supports a dataset synthesis.",
        pattern_text="The dataset profile row count came from the profile pass.",
        pattern_rationale=(
            "Default bundle pattern scope preserves the historical dataset-only "
            "support behavior."
        ),
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Top status values were observed in the profile.",
                "distinct_count": 3,
            }
        ],
    )

    assert result.dataset_profile.pattern is not None
    pattern = db.describe_pattern(result.dataset_profile.pattern.pattern_iri)
    assert [item.iri for item in pattern.supporting_observations] == [
        result.dataset_profile.observation.observation_iri
    ]


def test_record_profile_bundle_rejects_unknown_pattern_support_scope(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(
        DoxaBaseError,
        match="pattern_support_scope must be one of",
    ):
        db.record_profile_bundle(
            "https://example.test/project#Orders",
            dataset_summary="Orders were profiled.",
            pattern_support_scope="whole_run",
        )


def test_profile_summary_surfaces_run_candidates_in_mixed_profile_history(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    older_evidence = "https://example.test/project#OlderProfileEvidence"
    newer_evidence = "https://example.test/project#NewerProfileRunEvidence"

    db.record_dataset_profile(
        dataset,
        summary="Older dataset-only profile result.",
        evidence_summary="Older one-off profiling pass.",
        evidence_sources=["test://orders-profile-old"],
        evidence_iri=older_evidence,
        row_count=80,
        map_label="Orders",
        is_table=True,
    )
    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Newer profile bundle over dataset and columns.",
        evidence_summary="Newer shared profiling pass.",
        evidence_sources=["test://orders-profile-new"],
        shared_evidence_iri=newer_evidence,
        sample_size=100,
        sample_scope="All rows in the local Orders table.",
        sample_method="DuckDB full-table profiling query.",
        row_count=100,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": "https://example.test/project#OrdersStatus",
                "column_name": "status",
                "summary": "Status values were profiled.",
                "distinct_count": 3,
            },
            {
                "column_iri": "https://example.test/project#OrdersAmount",
                "column_name": "amount",
                "summary": "Amount values were profiled.",
                "null_count": 0,
            },
        ],
    )

    description = db.describe_dataset(dataset)

    assert description.profile_summary.returned_profile_count == 4
    assert description.profile_summary.evidence_profile_counts == {
        newer_evidence: 3,
        older_evidence: 1,
    }
    assert description.profile_summary.shared_evidence_iris == []
    assert [
        candidate.evidence_iri
        for candidate in description.profile_summary.profile_run_candidates
    ] == [newer_evidence]
    run_candidate = description.profile_summary.profile_run_candidates[0]
    assert run_candidate.returned_profile_count == 3
    assert set(run_candidate.profile_observation_iris) == {
        bundle.dataset_profile.observation.observation_iri,
        *(
            column_profile.observation.observation_iri
            for column_profile in bundle.column_profiles
        ),
    }
    assert run_candidate.shared_by_all_returned_profiles is False


def test_profile_run_candidates_are_count_ranked_and_ignore_singletons(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence_a = "https://example.test/project#EvidenceA"
    evidence_b = "https://example.test/project#EvidenceB"
    evidence_c = "https://example.test/project#EvidenceC"
    evidence_singleton = "https://example.test/project#EvidenceSingleton"
    status_column = "https://example.test/project#OrdersStatus"
    amount_column = "https://example.test/project#OrdersAmount"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(status_column, column_name="status", table_iri=dataset)
    db.record_map_column(amount_column, column_name="amount", table_iri=dataset)
    for index in range(3):
        db.record_observation(
            summary=f"A-backed profile {index}",
            observation_type="profile",
            observed_asset=dataset,
            evidence_summary="Profile pass A.",
            evidence_iri=evidence_a,
        )
    for index in range(2):
        db.record_observation(
            summary=f"B-backed profile {index}",
            observation_type="profile",
            observed_asset=dataset,
            observed_column=status_column,
            evidence_summary="Profile pass B.",
            evidence_iri=evidence_b,
        )
        db.record_observation(
            summary=f"C-backed profile {index}",
            observation_type="profile",
            observed_asset=dataset,
            observed_column=amount_column,
            evidence_summary="Profile pass C.",
            evidence_iri=evidence_c,
        )
    db.record_observation(
        summary="One-off singleton profile",
        observation_type="profile",
        observed_asset=dataset,
        evidence_summary="One-off profile.",
        evidence_iri=evidence_singleton,
    )

    candidates = db.describe_dataset(dataset).profile_summary.profile_run_candidates

    assert [
        (candidate.evidence_iri, candidate.returned_profile_count)
        for candidate in candidates
    ] == [
        (evidence_a, 3),
        (evidence_b, 2),
        (evidence_c, 2),
    ]
    assert all(
        not candidate.shared_by_all_returned_profiles for candidate in candidates
    )
    assert all(candidate.profile_observation_iris for candidate in candidates)


def test_describe_profile_run_returns_wide_shared_evidence_run(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WideOrders"
    shared_evidence = "https://example.test/project#WideOrdersProfileRunEvidence"

    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Wide Orders dataset was profiled with many columns.",
        evidence_summary="Wide profile pass.",
        evidence_sources=["test://wide-orders-profile"],
        shared_evidence_iri=shared_evidence,
        row_count=100,
        map_label="Wide Orders",
        is_table=True,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": f"https://example.test/project#WideOrdersColumn{index}",
                "column_name": f"column_{index}",
                "summary": f"Wide Orders column {index} was profiled.",
                "distinct_count": index + 1,
            }
            for index in range(8)
        ],
    )

    bounded = db.describe_dataset(dataset)
    assert bounded.profile_summary.returned_profile_count == 6
    assert bounded.profile_summary.total_profile_count == 9
    assert bounded.profile_summary.omitted_profile_count == 3
    assert (
        bounded.profile_summary.profile_run_candidates[0].returned_profile_count
        == 6
    )

    profile_run = db.describe_profile_run(dataset, shared_evidence)

    assert profile_run.evidence_iri == shared_evidence
    assert profile_run.returned_dataset_profile_count == 1
    assert profile_run.returned_mapped_column_profile_count == 0
    assert profile_run.returned_unmapped_column_profile_count == 8
    assert profile_run.returned_profile_count == 9
    assert profile_run.total_profile_count == 9
    assert profile_run.omitted_profile_count == 0
    assert set(profile_run.profile_observation_iris) == {
        bundle.dataset_profile.observation.observation_iri,
        *(
            column_profile.observation.observation_iri
            for column_profile in bundle.column_profiles
        ),
    }
    assert "no separate persisted profile-run node" in profile_run.retrieval_note

    capped = db.describe_profile_run(dataset, shared_evidence, limit=3)

    assert capped.returned_profile_count == 3
    assert capped.total_profile_count == 9
    assert capped.omitted_profile_count == 6
    assert len(capped.profile_observation_iris) == 3


def test_describe_profile_run_works_for_observation_only_dataset(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#ObservationOnlyOrders"
    shared_evidence = "https://example.test/project#ObservationOnlyProfileRunEvidence"

    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Observation-only Orders profile.",
        evidence_summary="Observation-only profile pass.",
        evidence_sources=["test://observation-only-profile"],
        shared_evidence_iri=shared_evidence,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": "https://example.test/project#ObservationOnlyStatus",
                "column_name": "status",
                "summary": "Observation-only status profile.",
            }
        ],
    )

    assert bundle.handoff_entrypoints.map_dataset_recorded is False
    assert bundle.handoff_entrypoints.dataset_describe_available is False
    assert bundle.handoff_entrypoints.profile_run_available is True
    assert bundle.handoff_entrypoints.profile_observation_iris == [
        bundle.dataset_profile.observation.observation_iri,
        bundle.column_profiles[0].observation.observation_iri,
    ]
    assert bundle.handoff_entrypoints.suggested_next_calls[0] == (
        f"describe_profile_run('{dataset}', '{shared_evidence}')"
    )
    assert bundle.handoff_entrypoints.suggested_next_calls[-1] == (
        "describe_context_slice("
        f"{bundle.handoff_entrypoints.profile_observation_iris!r}, "
        "profile='dataset_brief')"
    )
    assert not any(
        call.startswith("describe_dataset")
        for call in bundle.handoff_entrypoints.suggested_next_calls
    )
    assert "No map dataset subject" in bundle.handoff_entrypoints.handoff_note

    with pytest.raises(DoxaBaseError, match="was not found") as exc_info:
        db.describe_dataset(dataset)
    error_message = str(exc_info.value)
    assert "profile observation(s) reference this dataset" in error_message
    assert "describe_profile_run" in error_message
    assert shared_evidence in error_message
    assert "seed describe_context_slice" in error_message
    assert "record_map_dataset" in error_message

    profile_run = db.describe_profile_run(dataset, shared_evidence)

    assert profile_run.dataset.iri == dataset
    assert profile_run.returned_dataset_profile_count == 1
    assert profile_run.returned_unmapped_column_profile_count == 1
    assert profile_run.returned_profile_count == 2


def test_profile_bundle_handoff_distinguishes_existing_map_context_without_snapshot(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#ExistingMapOrders"
    status_column = "https://example.test/project#ExistingMapOrdersStatus"
    shared_evidence = "https://example.test/project#ExistingMapOrdersProfileEvidence"
    db.record_map_dataset(dataset, label="Existing Map Orders", is_table=True)

    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Existing map Orders profile stayed observation-only.",
        evidence_summary="Profile pass over existing map shell.",
        evidence_sources=["test://existing-map-orders-profile"],
        shared_evidence_iri=shared_evidence,
        row_count=120,
        update_map_snapshot=False,
        profile_metrics=[{"metric": "rc:MeanValue", "value": 4.5}],
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Existing map Orders status values were profiled.",
                "distinct_count": 3,
                "profile_metrics": [{"metric": "rc:MaximumValue", "value": 9}],
            }
        ],
    )

    assert bundle.dataset_profile.map_dataset is None
    assert bundle.handoff_entrypoints.map_dataset_recorded is False
    assert bundle.handoff_entrypoints.dataset_describe_available is True
    assert bundle.handoff_entrypoints.profile_run_available is True
    assert bundle.handoff_entrypoints.suggested_next_calls[:2] == [
        f"describe_dataset('{dataset}')",
        f"describe_profile_run('{dataset}', '{shared_evidence}')",
    ]
    assert "already existed" in bundle.handoff_entrypoints.handoff_note
    assert "did not write dataset map facts" in bundle.handoff_entrypoints.handoff_note
    assert "row-count snapshot" in bundle.handoff_entrypoints.handoff_note

    description = db.describe_dataset(dataset)
    assert description.row_count_snapshot is None
    assert description.profile_summary.returned_profile_count == 2

    profile_run = db.describe_profile_run(dataset, shared_evidence)
    assert profile_run.returned_profile_count == 2
    assert set(profile_run.profile_observation_iris) == set(
        bundle.handoff_entrypoints.profile_observation_iris
    )

    context_slice = db.describe_context_slice(
        bundle.handoff_entrypoints.profile_observation_iris,
        profile="dataset_brief",
    )
    assert {
        profile.iri for profile in context_slice.seed_profile_observations
    } == set(bundle.handoff_entrypoints.profile_observation_iris)
    assert context_slice.route_counts["observed_profile_metric"] == 2


def test_draft_profile_map_updates_surfaces_review_candidates(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Payments"
    status_column = "https://example.test/project#PaymentsStatus"
    amount_column = "https://example.test/project#PaymentsAmount"
    settlement_column = "https://example.test/project#PaymentsSettlementMethod"
    evidence = "https://example.test/project#PaymentsProfileRunEvidence"
    project_metric = "https://example.test/project#CompletenessRatio"

    db.record_map_dataset(
        dataset,
        label="Payments",
        is_table=True,
        row_count_snapshot=10,
    )
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        nullable=False,
    )
    db.record_map_column(
        amount_column,
        table_iri=dataset,
        column_name="amount",
        nullable=False,
    )

    db.record_profile_bundle(
        dataset,
        dataset_summary="Payments were profiled with a full-table scan.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://payments-profile"],
        shared_evidence_iri=evidence,
        sample_size=12,
        sample_scope="All rows in the test Payments table.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=12,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": project_metric,
                "value": "0.90",
                "datatype": "xsd:decimal",
            }
        ],
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status had nulls in the full scan.",
                "null_count": 2,
                "distinct_count": 3,
            },
            {
                "column_iri": amount_column,
                "column_name": "amount",
                "summary": "Amount had no nulls in the full scan.",
                "null_count": 0,
                "distinct_count": 12,
            },
            {
                "column_iri": settlement_column,
                "column_name": "settlement_method",
                "summary": "Settlement method was observed but is unmapped.",
                "null_count": 0,
                "distinct_count": 2,
            },
        ],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.map_dataset_found is True
    assert draft.evidence_iri == evidence
    assert len(draft.profile_observation_iris) == 4
    assert "read-only review context" in draft.review_note
    assert [
        (recommendation.kind, recommendation.resource.iri)
        for recommendation in draft.recommendations
    ] == [
        ("dataset_row_count_snapshot", dataset),
        ("column_nullable", status_column),
        ("unmapped_profiled_column", settlement_column),
    ]

    row_count = draft.recommendations[0]
    assert row_count.action == "replace_map_value"
    assert row_count.current_value == 10
    assert row_count.observed_value == 12
    assert row_count.sample_size == 12
    assert row_count.sample_scope == "All rows in the test Payments table."
    assert row_count.sample_method == "DuckDB full-table aggregate profile."
    assert row_count.profile_row_count == 12
    assert row_count.basis == "full_scan"
    assert row_count.confidence == "high"
    assert row_count.helper_name == "record_map_dataset"
    assert row_count.helper_arguments == {
        "iri": dataset,
        "row_count_snapshot": 12,
    }

    nullable = draft.recommendations[1]
    assert nullable.action == "replace_map_value"
    assert nullable.current_value is False
    assert nullable.observed_value is True
    assert nullable.observed_count == 2
    assert nullable.sample_size == 12
    assert nullable.helper_arguments == {
        "iri": status_column,
        "table_iri": dataset,
        "column_name": "status",
        "nullable": True,
    }

    unmapped = draft.recommendations[2]
    assert unmapped.action == "add_map_column_shell"
    assert unmapped.current_value is None
    assert unmapped.observed_value == "settlement_method"
    assert unmapped.helper_arguments == {
        "iri": settlement_column,
        "table_iri": dataset,
        "column_name": "settlement_method",
    }

    assert len(draft.metric_advisories) == 1
    metric_advisory = draft.metric_advisories[0]
    assert metric_advisory.metric.iri == project_metric
    assert metric_advisory.advisory_status == "project_metric_undefined"
    assert metric_advisory.definition_found is False
    assert metric_advisory.definition is None
    assert [action.tool_name for action in metric_advisory.suggested_next_actions] == [
        "describe_context_slice",
        "list_entities",
    ]
    assert metric_advisory.suggested_next_actions[0].arguments == {
        "seed_iris": [project_metric],
        "profile": "dataset_brief",
    }
    assert metric_advisory.recommendation == (
        "review_metric_vocabulary_before_reuse"
    )

    description = db.describe_dataset(dataset)
    assert description.row_count_snapshot == 10
    assert {
        column.iri: column.nullable for column in description.columns
    } == {
        status_column: False,
        amount_column: False,
    }


def test_draft_profile_map_updates_reports_defined_project_metric_advisory(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"
    project_metric = "https://example.test/project#CompletenessScore"
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=100,
    )
    db.replace_graph_triples(
        "ontology",
        additions=f"""
            @prefix metric: <https://example.test/project#> .
            @prefix rc: <https://richcanopy.org/ns/rc#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            <{project_metric}> a rc:ProfileMetricKind ;
                rdfs:label "Completeness score" ;
                rdfs:comment "Share of records with complete required fields." .
        """,
        allow_count_change=True,
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Orders profile with a project metric.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        row_count=100,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": project_metric,
                "value": "0.99",
                "datatype": "xsd:decimal",
            }
        ],
        column_defaults={"update_map_column": False},
    )

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.recommendations == []
    assert len(draft.metric_advisories) == 1
    advisory = draft.metric_advisories[0]
    assert advisory.advisory_status == "project_metric_defined"
    assert advisory.definition_found is True
    assert advisory.definition is not None
    assert advisory.definition.iri == project_metric
    assert advisory.definition.label == "Completeness score"
    assert [action.tool_name for action in advisory.suggested_next_actions] == [
        "describe_context_slice",
        "describe_resource",
    ]
    assert advisory.suggested_next_actions[1].arguments == {
        "iri": project_metric,
        "graph": "ontology",
    }


def test_stage_profile_map_updates_groups_accepted_reviewable_changes(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Payments"
    status_column = "https://example.test/project#PaymentsStatus"
    settlement_column = "https://example.test/project#PaymentsSettlementMethod"
    evidence = "https://example.test/project#PaymentsProfileRunEvidence"

    db.record_map_dataset(
        dataset,
        label="Payments",
        is_table=True,
        row_count_snapshot=10,
    )
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        nullable=False,
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Payments were profiled with a full-table scan.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://payments-profile"],
        shared_evidence_iri=evidence,
        sample_size=12,
        sample_scope="All rows in the test Payments table.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=12,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status had nulls in the full scan.",
                "null_count": 2,
            },
            {
                "column_iri": settlement_column,
                "column_name": "settlement_method",
                "summary": "Settlement method was observed but is unmapped.",
            },
        ],
    )

    staged = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[0, 1, 2],
    )

    assert staged.staged_recommendation_indexes == [0, 1, 2]
    assert staged.skipped_recommendation_indexes == []
    assert staged.not_selected_recommendation_indexes == []
    assert staged.status_counts == {"staged": 3, "skipped": 0, "not_selected": 0}
    assert [item.status for item in staged.items] == ["staged", "staged", "staged"]
    assert staged.metric_advisories == []
    assert staged.staged_revision is not None
    assert staged.staged_revision.validation_conforms is True
    assert staged.staged_revision.changed_graphs == ["map"]
    assert [patch.target_graph for patch in staged.staged_revision.patches] == [
        "map",
        "map",
    ]
    assert {patch.triple_count for patch in staged.staged_revision.patches} == {
        2,
        5,
    }
    described = db.describe_staged_revision(staged.staged_revision.revision_iri)
    assert described.validation_conforms is True
    assert {anchor.iri for anchor in described.revision_anchors} == {
        dataset,
        status_column,
        settlement_column,
    }
    assert {item.iri for item in described.supporting_observations} == {
        item.profile_observation_iri for item in staged.items
    }
    assert [item.iri for item in described.evidence] == [evidence]

    description = db.describe_dataset(dataset)
    assert description.row_count_snapshot == 10
    assert {column.iri for column in description.columns} == {status_column}

    applied = db.apply_staged_revision(staged.staged_revision.revision_iri)
    assert applied.patches_applied == 2
    assert applied.triples_removed == 2
    assert applied.triples_added == 5
    assert applied.validation_conforms is True
    applied_description = db.describe_dataset(dataset)
    assert applied_description.row_count_snapshot == 12
    assert {
        column.iri: column.nullable for column in applied_description.columns
    } == {
        status_column: True,
        settlement_column: None,
    }


def test_stage_profile_map_updates_stages_thin_shell_for_missing_dataset(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#ObservationOnlyOrders"
    status_column = "https://example.test/project#ObservationOnlyOrdersStatus"
    evidence = "https://example.test/project#ObservationOnlyProfileRunEvidence"

    db.record_profile_bundle(
        dataset,
        dataset_summary="Observation-only Orders profile.",
        evidence_summary="Observation-only profile pass.",
        evidence_sources=["test://observation-only-profile"],
        shared_evidence_iri=evidence,
        sample_size=20,
        sample_scope="All rows in the observation-only Orders table.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=20,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Observation-only status profile.",
            }
        ],
    )

    staged = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[0, 1],
    )

    assert staged.map_dataset_found is False
    assert staged.staged_recommendation_indexes == [0, 1]
    assert staged.status_counts == {"staged": 2, "skipped": 0, "not_selected": 0}
    assert staged.staged_revision is not None
    assert staged.staged_revision.validation_conforms is True
    assert len(staged.staged_revision.patches) == 1
    patch_content = db.describe_staged_revision(
        staged.staged_revision.revision_iri
    ).patches[0].content
    assert patch_content is not None
    assert "rc:Dataset" in patch_content
    assert "rc:Column" in patch_content
    assert "rc:rowCountSnapshot 20" in patch_content
    assert "status" in patch_content
    assert [
        anchor.iri
        for anchor in db.describe_staged_revision(
            staged.staged_revision.revision_iri
        ).revision_anchors
    ] == [
        dataset,
        status_column,
    ]

    with pytest.raises(DoxaBaseError, match="was not found"):
        db.describe_dataset(dataset)


def test_stage_profile_map_updates_skips_sampled_row_count_by_default(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    referrer_column = "https://example.test/project#OrdersReferrer"
    evidence = "https://example.test/project#OrdersPartitionSampleEvidence"

    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=100,
    )
    db.record_map_column(
        referrer_column,
        table_iri=dataset,
        column_name="referrer",
        nullable=False,
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled from one sampled partition.",
        evidence_summary="Synthetic partition sample profile.",
        evidence_sources=["test://orders-partition-sample-profile"],
        shared_evidence_iri=evidence,
        sample_size=40,
        sample_scope="Sampled partition rows; not the full Orders table.",
        sample_method="DuckDB sampled partition profile.",
        row_count=40,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": referrer_column,
                "column_name": "referrer",
                "summary": "Referrer had nulls in the sampled partition.",
                "null_count": 3,
            }
        ],
    )

    staged = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[0],
    )

    assert staged.staged_recommendation_indexes == []
    assert staged.skipped_recommendation_indexes == [0]
    assert staged.not_selected_recommendation_indexes == [1]
    assert staged.status_counts == {"staged": 0, "skipped": 1, "not_selected": 1}
    assert staged.staged_revision is None
    assert staged.items[0].status == "skipped"
    assert staged.items[1].status == "not_selected"
    assert "Sampled row-count recommendations" in (staged.items[0].reason or "")
    assert db.describe_dataset(dataset).row_count_snapshot == 100

    mixed = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[0, 1],
    )
    assert mixed.staged_recommendation_indexes == [1]
    assert mixed.skipped_recommendation_indexes == [0]
    assert mixed.not_selected_recommendation_indexes == []
    assert mixed.status_counts == {"staged": 1, "skipped": 1, "not_selected": 0}
    assert mixed.staged_revision is not None

    override = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[0],
        allow_sampled_row_count_updates=True,
    )
    assert override.staged_recommendation_indexes == [0]
    assert override.status_counts == {"staged": 1, "skipped": 0, "not_selected": 1}
    assert override.staged_revision is not None
    assert override.staged_revision.validation_conforms is True


def test_draft_profile_map_updates_skips_sampled_zero_null_promotion(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    promo_column = "https://example.test/project#OrdersPromoCode"
    evidence = "https://example.test/project#OrdersSampleProfileEvidence"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(
        promo_column,
        table_iri=dataset,
        column_name="promo_code",
        nullable=True,
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled from a sample.",
        evidence_summary="Synthetic sampled profile.",
        evidence_sources=["test://orders-sample-profile"],
        shared_evidence_iri=evidence,
        sample_size=25,
        sample_scope="Not a full population; 25 sampled Orders rows.",
        sample_method="DuckDB random sample profile.",
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": promo_column,
                "column_name": "promo_code",
                "summary": "Promo code had zero nulls in the sample.",
                "null_count": 0,
                "distinct_count": 8,
            }
        ],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.recommendations == []
    assert draft.metric_advisories == []
    description = db.describe_dataset(dataset)
    assert description.columns[0].nullable is True


def test_draft_profile_map_updates_treats_explicit_sample_text_as_sample(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    sample_only_column = "https://example.test/project#OrdersSampleOnlyFlag"
    evidence = "https://example.test/project#OrdersPartitionSampleEvidence"

    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=100,
    )
    db.record_map_column(
        sample_only_column,
        table_iri=dataset,
        column_name="sample_only_flag",
        nullable=True,
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled from one sampled partition.",
        evidence_summary="Synthetic partition sample profile.",
        evidence_sources=["test://orders-partition-sample-profile"],
        shared_evidence_iri=evidence,
        sample_size=40,
        sample_scope="Sampled partition rows; not the full Orders table.",
        sample_method="DuckDB sampled partition profile.",
        row_count=40,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": sample_only_column,
                "column_name": "sample_only_flag",
                "summary": "Sample-only flag had zero nulls in the partition sample.",
                "null_count": 0,
                "distinct_count": 2,
            }
        ],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert [(item.kind, item.basis) for item in draft.recommendations] == [
        ("dataset_row_count_snapshot", "sample")
    ]
    row_count = draft.recommendations[0]
    assert row_count.confidence == "medium"
    assert row_count.sample_size == 40
    assert row_count.profile_row_count == 40
    assert "sampled partition" in (row_count.sample_method or "").lower()
    description = db.describe_dataset(dataset)
    assert description.row_count_snapshot == 100
    assert description.columns[0].nullable is True


def test_describe_profile_run_rejects_invalid_limit(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match="limit must be a positive integer"):
        db.describe_profile_run(
            "https://example.test/project#Orders",
            "https://example.test/project#ProfileEvidence",
            limit=0,
        )


def test_record_profile_bundle_rejects_unknown_column_fields(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match="unsupported record_column_profile"):
        db.record_profile_bundle(
            "https://example.test/project#Orders",
            dataset_summary="Orders were profiled.",
            column_profiles=[
                {
                    "column_iri": "https://example.test/project#OrdersStatus",
                    "column_name": "status",
                    "summary": "Status was profiled.",
                    "allowed_values": ["fulfilled"],
                }
            ],
        )

    assert _mutable_graph_counts(db) == before_counts
    assert db.search("Orders were profiled", graph="observations").matches == []


def test_record_profile_bundle_rejects_invalid_column_values_without_mutation(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(
        DoxaBaseError,
        match=(
            "column_profiles\\[0\\]\\.value_frequencies\\[0\\]\\.frequency"
        ),
    ):
        db.record_profile_bundle(
            "https://example.test/project#Orders",
            dataset_summary="Orders were profiled.",
            evidence_summary="Shared profiler run.",
            evidence_sources=["test://profile-run"],
            column_profiles=[
                {
                    "column_iri": "https://example.test/project#OrdersStatus",
                    "column_name": "status",
                    "summary": "Status was profiled.",
                    "value_frequencies": [
                        {"value": "fulfilled", "frequency": -1},
                    ],
                }
            ],
        )

    assert _mutable_graph_counts(db) == before_counts
    assert db.search("Orders were profiled", graph="observations").matches == []
    assert db.search("Shared profiler run", graph="evidence").matches == []


def test_record_profile_bundle_rejects_conflicting_shared_evidence_summary(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    shared_evidence = "https://example.test/project#OrdersProfileRunEvidence"
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match="conflicting evidence_summary"):
        db.record_profile_bundle(
            "https://example.test/project#Orders",
            dataset_summary="Orders were profiled.",
            evidence_summary="Dataset-level profiler run summary.",
            evidence_sources=["test://profile-run"],
            shared_evidence_iri=shared_evidence,
            column_profiles=[
                {
                    "column_iri": "https://example.test/project#OrdersStatus",
                    "column_name": "status",
                    "summary": "Status was profiled.",
                    "evidence_summary": "Column-level conflicting summary.",
                }
            ],
        )

    assert _mutable_graph_counts(db) == before_counts
    assert db.search("Orders were profiled", graph="observations").matches == []
    assert db.search("Dataset-level profiler run", graph="evidence").matches == []


@pytest.mark.parametrize(
    ("column_overrides", "match"),
    [
        (
            {"profile_metrics": [{"metric": "rc:MeanValue", "value": []}]},
            "column_profiles\\[0\\]\\.profile_metrics\\[0\\]\\.value",
        ),
        (
            {"profile_metrics": [{"metric": "rc:MinValue", "value": 1}]},
            "column_profiles\\[0\\]\\.profile_metrics\\[0\\]\\.metric",
        ),
        ({"physical_type": "plain physical type"}, "physical_type"),
        ({"value_type": "plain value type"}, "value_type"),
        ({"table_iri": "plain table name"}, "table_iri"),
        ({"pattern_summary": "Status looks categorical."}, "provided together"),
        (
            {
                "pattern_summary": "Status looks categorical.",
                "pattern_text": "Status has a small observed domain.",
                "pattern_rationale": "The profiler saw only a few statuses.",
                "pattern_map_implications": ["plain implication"],
            },
            "pattern_map_implications",
        ),
    ],
)
def test_record_profile_bundle_preflights_column_validation_without_mutation(
    tmp_path: Path,
    column_overrides: dict[str, object],
    match: str,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_counts = _mutable_graph_counts(db)
    column_profile = {
        "column_iri": "https://example.test/project#OrdersStatus",
        "column_name": "status",
        "summary": "Status was profiled.",
        **column_overrides,
    }

    with pytest.raises(DoxaBaseError, match=match):
        db.record_profile_bundle(
            "https://example.test/project#Orders",
            dataset_summary="Orders were profiled.",
            evidence_summary="Shared profiler run.",
            evidence_sources=["test://profile-run"],
            column_profiles=[column_profile],
        )

    assert _mutable_graph_counts(db) == before_counts
    assert db.search("Orders were profiled", graph="observations").matches == []
    assert db.search("Shared profiler run", graph="evidence").matches == []


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
    with pytest.raises(DoxaBaseError, match="observed_column_name requires"):
        db.record_observation("Bad column name", observed_column_name="status")
    with pytest.raises(DoxaBaseError, match="observed_column_name must not be empty"):
        db.record_observation(
            "Bad empty column name",
            observed_column="https://example.test/project#OrdersStatus",
            observed_column_name=" ",
        )


def test_record_observation_rejects_conflicting_reused_evidence_summary(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    evidence_iri = "https://example.test/project#ProfileRunEvidence"
    db.record_observation(
        "First profile note.",
        observation_type="profile",
        observed_asset="https://example.test/project#Orders",
        evidence_summary="Shared profiler run.",
        evidence_sources=["test://profile-run"],
        evidence_iri=evidence_iri,
    )
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match="conflicts with existing summary"):
        db.record_observation(
            "Second profile note.",
            observation_type="profile",
            observed_asset="https://example.test/project#Orders",
            evidence_summary="Different profiler run summary.",
            evidence_sources=["test://profile-run/second"],
            evidence_iri=evidence_iri,
        )

    assert _mutable_graph_counts(db) == before_counts
    assert db.search("Second profile note", graph="observations").matches == []
    assert db.validate_graph(scope="all").conforms
