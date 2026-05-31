import warnings
from pathlib import Path

import pytest
from rdflib import Literal, URIRef
from rdflib.namespace import DCTERMS, RDF

from doxabase import DoxaBase, DoxaBaseError, ImmutableGraphError

ROOT = Path(__file__).resolve().parents[1]
AIS_FIXTURE = ROOT / "examples" / "manifest-prototype-rc" / "ais.trig"
POLYMARKET_FIXTURE = ROOT / "examples" / "manifest-prototype-rc" / "polymarket.trig"
RC = "https://richcanopy.org/ns/rc#"


def test_capsule_creation_seeds_base_graphs(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    overview = db.graph_overview()

    graphs = {graph.name: graph for graph in overview.named_graphs}
    assert graphs["base_ontology"].triple_count == 807
    assert graphs["base_ontology"].mutable is False
    assert graphs["base_shapes"].triple_count == 657
    assert graphs["base_shapes"].mutable is False
    assert graphs["map"].mutable is True


def test_immutable_seed_graphs_reject_normal_imports(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(ImmutableGraphError):
        db.import_turtle("@prefix ex: <https://example.test/> . ex:s ex:p ex:o .", graph="base_ontology")


def test_import_trig_maps_graph_iris_to_roles(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    imported = db.import_trig(AIS_FIXTURE)

    assert imported == {
        "evidence": 3,
        "map": 219,
        "observations": 5,
        "ontology": 94,
    }
    assert db.triple_count("map") == 219
    assert db.triple_count("ontology") == 94


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
    assert description.path_templates == ["broadcasts/{year}/ais-{date}.parquet"]
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
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    with pytest.raises(DoxaBaseError, match="was not found"):
        db.describe_dataset("https://richcanopy.org/example/manifest/ais#MissingDataset")


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
        Literal("tests/test_doxabase_core.py"),
    ) in evidence

    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_record_observation_rejects_invalid_inputs(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match="summary"):
        db.record_observation("   ")
    with pytest.raises(DoxaBaseError, match="row_count"):
        db.record_observation("Bad count", row_count=-1)
    with pytest.raises(DoxaBaseError, match="observation_type"):
        db.record_observation("Bad type", observation_type="note")  # type: ignore[arg-type]
