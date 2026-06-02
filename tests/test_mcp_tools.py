from pathlib import Path

import pytest

from doxabase import DoxaBase
from doxabase.mcp_server import build_server
from doxabase.mcp_tools import (
    describe_dataset_tool,
    describe_resource_tool,
    export_graph_tool,
    export_trig_tool,
    graph_overview_tool,
    list_docs_tool,
    list_entities_tool,
    load_example_fixtures_tool,
    record_claim_observation_tool,
    record_map_caveat_tool,
    record_map_column_tool,
    record_map_dataset_tool,
    record_map_relationship_tool,
    record_map_storage_access_tool,
    record_observation_tool,
    record_pattern_tool,
    search_tool,
    validate_graph_tool,
)


@pytest.mark.anyio
async def test_build_server_registers_expected_tools(tmp_path: Path) -> None:
    server = build_server(tmp_path / "mcp.sqlite")
    tool_names = {tool.name for tool in await server.list_tools()}

    assert "doxabase.list_docs" in tool_names
    assert "doxabase.get_doc" in tool_names
    assert "doxabase.graph_overview" in tool_names
    assert "doxabase.list_entities" in tool_names
    assert "doxabase.describe_dataset" in tool_names
    assert "doxabase.describe_resource" in tool_names
    assert "doxabase.record_observation" in tool_names
    assert "doxabase.record_claim_observation" in tool_names
    assert "doxabase.record_pattern" in tool_names
    assert "doxabase.record_map_dataset" in tool_names
    assert "doxabase.record_map_column" in tool_names
    assert "doxabase.record_map_caveat" in tool_names
    assert "doxabase.record_map_storage_access" in tool_names
    assert "doxabase.record_map_relationship" in tool_names
    assert "doxabase.search" in tool_names
    assert "doxabase.export_graph" in tool_names
    assert "doxabase.export_trig" in tool_names
    assert "doxabase.load_example_fixtures" in tool_names
    assert "doxabase.validate_graph" in tool_names


def test_doc_tools_return_json_like_payloads() -> None:
    result = list_docs_tool()
    doc_ids = {doc["id"] for doc in result["docs"]}

    assert "overview" in doc_ids
    assert "graph_roles" in doc_ids


def test_fixture_loading_and_validation_tools(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    load_result = load_example_fixtures_tool(db)
    overview = graph_overview_tool(db)
    tables = list_entities_tool(db, type="rc:Table", graph="map")
    validation = validate_graph_tool(db, scope="all")

    assert load_result["total_imported"] == 762
    assert overview["key_counts"]["tables"] >= 7
    assert tables["count"] >= 7
    assert validation["conforms"] is True


def test_export_tools_write_review_artifacts(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)
    graph_path = tmp_path / "map.ttl"
    trig_path = tmp_path / "bundle.trig"

    graph_result = export_graph_tool(db, path=str(graph_path), graphs=["map"])
    trig_result = export_trig_tool(
        db,
        path=str(trig_path),
    )

    assert graph_result["path"] == str(graph_path)
    assert graph_result["format"] == "turtle"
    assert graph_result["graphs"] == ["map"]
    assert graph_result["graph_counts"] == {"map": db.triple_count("map")}
    assert graph_result["triples"] == db.triple_count("map")
    assert graph_path.exists()

    assert trig_result["path"] == str(trig_path)
    assert trig_result["format"] == "trig"
    assert trig_result["graphs"] == [
        "ontology",
        "map",
        "observations",
        "patterns",
        "evidence",
        "shapes",
        "history",
    ]
    assert "base_ontology" not in trig_result["graphs"]
    assert trig_result["triples"] == sum(trig_result["graph_counts"].values())
    assert trig_path.exists()


def test_describe_dataset_tool_returns_json_like_context(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)

    result = describe_dataset_tool(
        db,
        iri="https://richcanopy.org/example/manifest/polymarket#MarketSnapshots",
    )

    assert result["label"] == "Gamma Market Snapshots"
    assert "data/parquet/gamma/markets/dt={date}/hour={hour}.parquet" in result[
        "path_templates"
    ]
    assert {column["column_name"] for column in result["columns"]} >= {
        "id",
        "bestBid",
        "bestAsk",
    }
    assert result["physical_layouts"][0]["compression_codec"]["label"] == "zstd"
    assert result["storage_accesses"][0]["storage_protocol"]["label"] == "local filesystem"
    assert result["storage_accesses"][0]["storage_root"] == "data/parquet"
    assert result["storage_accesses"][0]["access_mode"]["label"] == "read-only"
    assert any(
        caveat["description"]
        and "Parquet schemas are inferred" in caveat["description"]
        for caveat in result["caveats"]
    )


def test_record_observation_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    result = record_observation_tool(
        db,
        summary="MCP helper wrote a structured observation.",
        observed_by="urn:doxabase:test-agent",
        evidence_summary="Evidence written by the MCP helper test.",
        evidence_sources=["tests/test_mcp_tools.py"],
    )

    assert result["observation_iri"].startswith(
        "https://richcanopy.org/doxabase/generated/observation/"
    )
    assert result["observation_type"] == "observation"
    assert result["evidence_iri"] is not None
    assert result["observation_triples"] > 0
    assert result["evidence_triples"] > 0
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_record_claim_observation_tool_and_resource_context(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    result = record_claim_observation_tool(
        db,
        summary="MCP helper wrote a structured claim observation.",
        claim_text="The embeddings output joins to eml_messages by doc_id.",
        claim_kind="rc:JoinClaim",
        claim_targets=[
            "https://example.test/enron#eml_embeddings_body_top_doc_id",
            "https://example.test/enron#eml_messages_doc_id",
        ],
        evidence_summary="README embeddings section.",
        source_path="/home/james/github.com/jamtho/enron-emails/README.md",
        source_section="Embeddings",
        source_kind="rc:DocumentationSource",
        confidence="rc:HighConfidence",
        observation_status="rc:Checked",
    )
    claims = list_entities_tool(
        db,
        type="rc:Claim",
        graph="observations",
        text="doc_id",
    )
    context = describe_resource_tool(
        db,
        iri=result["claim_iri"],
        graph="observations",
    )

    assert result["claim_iri"] in {claim["iri"] for claim in claims["entities"]}
    assert context["label"] == "The embeddings output joins to eml_messages by doc_id."
    assert any(
        triple["predicate"] == "https://richcanopy.org/ns/rc#claimKind"
        for triple in context["outgoing"]
    )
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_record_pattern_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    claim = record_claim_observation_tool(
        db,
        summary="MCP helper wrote a claim for pattern support.",
        claim_text="The child table joins to the parent table by parent_doc_id.",
        claim_kind="rc:JoinClaim",
        claim_targets=[
            "https://example.test/enron#eml_attachments_parent_doc_id",
            "https://example.test/enron#eml_messages_doc_id",
        ],
        evidence_summary="README attachments section.",
        source_path="/home/james/github.com/jamtho/enron-emails/README.md",
        source_kind="rc:DocumentationSource",
        confidence="rc:HighConfidence",
        observation_status="rc:Checked",
    )

    result = record_pattern_tool(
        db,
        summary="parent_doc_id behaves as the attachment-to-message join.",
        pattern_text="The structured claim and source docs support parent_doc_id as the join from attachments to messages.",
        rationale="The claim names both join columns, and the source span records where the handoff describes the relationship.",
        pattern_targets=["https://example.test/enron#eml_attachments_parent_doc_id"],
        supporting_claims=[claim["claim_iri"]],
        source_path="/home/james/github.com/jamtho/enron-emails/README.md",
        source_section="Attachments",
        source_kind="rc:DocumentationSource",
        confidence="rc:HighConfidence",
        pattern_status="rc:Checked",
        pattern_stability="rc:RepeatedPattern",
    )
    patterns = list_entities_tool(
        db,
        type="rc:Pattern",
        graph="patterns",
        text="attachment-to-message",
    )
    context = describe_resource_tool(
        db,
        iri=result["pattern_iri"],
        graph="patterns",
    )

    assert result["pattern_iri"] in {pattern["iri"] for pattern in patterns["entities"]}
    assert patterns["entities"][0]["label"] == (
        "parent_doc_id behaves as the attachment-to-message join."
    )
    assert context["label"] == "parent_doc_id behaves as the attachment-to-message join."
    assert any(
        triple["predicate"] == "https://richcanopy.org/ns/rc#supportingClaim"
        for triple in context["outgoing"]
    )
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_map_authoring_tools_return_json_like_payloads(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/project#"
    table = f"{base}messages"
    column = f"{base}messages__doc_id"
    caveat = f"{base}messages_caveat"
    storage = f"{base}local_access"

    table_result = record_map_dataset_tool(
        db,
        iri=table,
        label="Messages",
        is_table=True,
        path_templates=["data/messages.parquet"],
    )
    column_result = record_map_column_tool(
        db,
        iri=column,
        table_iri=table,
        column_name="doc_id",
        physical_type="rc:Varchar",
        nullable=False,
    )
    caveat_result = record_map_caveat_tool(
        db,
        iri=caveat,
        description="Message identifiers are source-system identifiers.",
        severity="rc:Minor",
        targets=[table],
    )
    storage_result = record_map_storage_access_tool(
        db,
        iri=storage,
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        storage_root="/tmp/example",
        datasets=[table],
    )
    relationship_result = record_map_relationship_tool(
        db,
        iri=f"{base}messages_doc_id_shared",
        relationship_type="shared_identifier",
        identifying_columns=[column, f"{base}other_messages__doc_id"],
    )

    assert table_result["resource_type"] == "https://richcanopy.org/ns/rc#Table"
    assert column_result["resource_type"] == "https://richcanopy.org/ns/rc#Column"
    assert caveat_result["resource_type"] == "https://richcanopy.org/ns/rc#KnownCaveat"
    assert storage_result["resource_type"] == "https://richcanopy.org/ns/rc#StorageAccess"
    assert relationship_result["resource_type"] == (
        "https://richcanopy.org/ns/rc#SharedIdentifier"
    )
    assert describe_dataset_tool(db, iri=table)["label"] == "Messages"
    assert validate_graph_tool(db, scope="map")["conforms"] is True


def test_search_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)

    result = search_tool(db, query="Parquet schemas", graph="map", limit=5)

    assert result["query"] == "Parquet schemas"
    assert result["graph"] == "map"
    assert result["limit"] == 5
    assert result["count"] >= 1
    assert any(
        "Parquet schemas are inferred" in match["text"]
        for match in result["matches"]
    )


def test_fixture_loading_replace_keeps_all_fixtures(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    load_result = load_example_fixtures_tool(db, replace=True)
    tables = list_entities_tool(db, type="rc:Table", graph="map")
    labels = {entity["label"] for entity in tables["entities"]}

    assert load_result["replace"] is True
    assert "AIS Daily Broadcast Positions" in labels
    assert "AIS Daily Vessel Index" in labels
    assert "Gamma Market Snapshots" in labels
    assert "Trade Events" in labels
