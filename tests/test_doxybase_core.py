from pathlib import Path

import pytest
from rdflib import Literal, URIRef
from rdflib.namespace import DCTERMS, RDF

from doxybase import DoxyBase, DoxyBaseError, ImmutableGraphError

ROOT = Path(__file__).resolve().parents[1]
AIS_FIXTURE = ROOT / "examples" / "manifest-prototype-rc" / "ais.trig"
POLYMARKET_FIXTURE = ROOT / "examples" / "manifest-prototype-rc" / "polymarket.trig"
RC = "https://richcanopy.org/ns/rc#"


def test_capsule_creation_seeds_base_graphs(tmp_path: Path) -> None:
    db = DoxyBase.create(tmp_path / "capsule.sqlite")
    overview = db.graph_overview()

    graphs = {graph.name: graph for graph in overview.named_graphs}
    assert graphs["base_ontology"].triple_count == 625
    assert graphs["base_ontology"].mutable is False
    assert graphs["base_shapes"].triple_count == 471
    assert graphs["base_shapes"].mutable is False
    assert graphs["map"].mutable is True


def test_immutable_seed_graphs_reject_normal_imports(tmp_path: Path) -> None:
    db = DoxyBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(ImmutableGraphError):
        db.import_turtle("@prefix ex: <https://example.test/> . ex:s ex:p ex:o .", graph="base_ontology")


def test_import_trig_maps_graph_iris_to_roles(tmp_path: Path) -> None:
    db = DoxyBase.create(tmp_path / "capsule.sqlite")
    imported = db.import_trig(AIS_FIXTURE)

    assert imported == {
        "evidence": 3,
        "map": 204,
        "observations": 5,
        "ontology": 94,
    }
    assert db.triple_count("map") == 204
    assert db.triple_count("ontology") == 94


def test_list_entities_returns_tables_from_map(tmp_path: Path) -> None:
    db = DoxyBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    db.import_trig(POLYMARKET_FIXTURE)

    result = db.list_entities(type="rc:Table", graph="map", limit=20)
    labels = {row.label for row in result.entities}

    assert "AIS Daily Broadcast Positions" in labels
    assert "AIS Daily Vessel Index" in labels
    assert "Gamma Market Snapshots" in labels
    assert "Trade Events" in labels


def test_describe_dataset_returns_bounded_table_context(tmp_path: Path) -> None:
    db = DoxyBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    description = db.describe_dataset(
        "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"
    )

    assert description.label == "AIS Daily Broadcast Positions"
    assert "https://richcanopy.org/ns/rc#Table" in description.types
    assert description.path_templates == ["broadcasts/{year}/ais-{date}.parquet"]
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
    assert any(
        provenance.description
        and "NOAA Marine Cadastre AIS data" in provenance.description
        for provenance in description.provenance
    )
    assert any(
        related.iri == "https://richcanopy.org/example/manifest/ais#DailyIndex"
        and related.relationship == "source_of"
        for related in description.related_datasets
    )


def test_describe_dataset_reports_missing_dataset(tmp_path: Path) -> None:
    db = DoxyBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    with pytest.raises(DoxyBaseError, match="was not found"):
        db.describe_dataset("https://richcanopy.org/example/manifest/ais#MissingDataset")


def test_describe_dataset_handles_blank_node_physical_layout(tmp_path: Path) -> None:
    db = DoxyBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    description = db.describe_dataset(
        "https://richcanopy.org/example/manifest/ais#DailyIndex"
    )

    assert len(description.physical_layouts) == 1
    layout = description.physical_layouts[0]
    assert layout.iri
    assert layout.file_format is not None
    assert layout.file_format.label == "Parquet"


def test_graph_overview_counts_imported_fixtures(tmp_path: Path) -> None:
    db = DoxyBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    db.import_trig(POLYMARKET_FIXTURE)

    overview = db.graph_overview()

    assert overview.key_counts["tables"] >= 7
    assert overview.key_counts["columns"] >= 40
    assert any(
        predicate == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
        for predicate, _ in overview.predicate_counts
    )


def test_validate_graph_uses_base_and_project_shapes(tmp_path: Path) -> None:
    db = DoxyBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    db.import_trig(POLYMARKET_FIXTURE)

    result = db.validate_graph(scope="all")

    assert result.conforms, result.report_text
    assert result.result_count == 0


def test_record_observation_writes_observation_and_evidence_graphs(tmp_path: Path) -> None:
    db = DoxyBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    before = db.graph_overview().key_counts["observations"]

    result = db.record_observation(
        summary="AIS daily broadcasts were sampled for row coverage.",
        observation_type="profile",
        observed_asset="https://richcanopy.org/example/manifest/ais#DailyBroadcasts",
        observed_at="2026-05-31T12:00:00Z",
        observed_by="urn:doxybase:test-agent",
        evidence_summary="Synthetic test evidence for the observation writer.",
        evidence_sources=["tests/test_doxybase_core.py"],
        row_count=123,
        distinct_count=45,
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
    assert (evidence_iri, RDF.type, URIRef(RC + "Evidence")) in evidence
    assert (
        evidence_iri,
        DCTERMS.source,
        Literal("tests/test_doxybase_core.py"),
    ) in evidence

    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_record_observation_rejects_invalid_inputs(tmp_path: Path) -> None:
    db = DoxyBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxyBaseError, match="summary"):
        db.record_observation("   ")
    with pytest.raises(DoxyBaseError, match="row_count"):
        db.record_observation("Bad count", row_count=-1)
    with pytest.raises(DoxyBaseError, match="observation_type"):
        db.record_observation("Bad type", observation_type="note")  # type: ignore[arg-type]
