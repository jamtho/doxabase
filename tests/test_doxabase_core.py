import warnings
from pathlib import Path

import pytest
from rdflib import Dataset, Graph, Literal, URIRef
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
    assert graphs["base_ontology"].triple_count == 932
    assert graphs["base_ontology"].mutable is False
    assert graphs["base_shapes"].triple_count == 844
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
        "map": 219,
        "observations": 5,
        "ontology": 94,
    }
    assert db.triple_count("map") == 219
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
    assert any(caveat.severity is not None for caveat in description.caveats)
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


def test_record_map_helpers_write_describable_map_resources(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/enron#"
    messages = f"{base}eml_messages"
    attachments = f"{base}eml_attachments"
    doc_id = f"{base}eml_messages__doc_id"
    parent_doc_id = f"{base}eml_attachments__parent_doc_id"
    caveat = f"{base}caveat_body_processing_lossy"
    storage = f"{base}local_parquet_access"

    storage_record = db.record_map_storage_access(
        storage,
        label="local parquet access",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        storage_root="/home/james/github.com/jamtho/enron-emails",
        path_templates=["data/parquet/*.parquet"],
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
        caveats=[caveat],
        storage_accesses=[storage],
    )
    db.record_map_dataset(
        attachments,
        label="EML attachments",
        is_table=True,
        path_templates=["data/parquet/eml_attachments.parquet"],
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
    relationship = db.record_map_relationship(
        f"{base}eml_attachment_parent_doc_id_fk",
        relationship_type="foreign_key",
        label="attachment parent doc id fk",
        from_column=parent_doc_id,
        to_column=doc_id,
        declared=False,
        referential_integrity="rc:StrictIntegrity",
    )

    assert storage_record.resource_type == RC + "StorageAccess"
    assert caveat_record.resource_type == RC + "KnownCaveat"
    assert table_record.resource_type == RC + "Table"
    assert doc_column.resource_type == RC + "Column"
    assert relationship.resource_type == RC + "ForeignKey"
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
    assert description.path_templates == [
        "data/parquet/eml_messages.parquet",
        "data/parquet/*.parquet",
    ]
    assert description.columns[0].column_name == "doc_id"
    assert description.columns[0].nullable is False
    assert description.storage_accesses[0].storage_root == (
        "/home/james/github.com/jamtho/enron-emails"
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
        pattern_targets=[messages],
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
        ("pattern_target", messages),
        ("supporting_claim_target", doc_id),
    }
    assert {
        (group.relevance_tier, group.matched_resource.iri)
        for group in pattern_reason.match_groups
    } == {
        ("direct", messages),
        ("claim_supported", doc_id),
    }
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
