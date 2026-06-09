from pathlib import Path

import pytest

from doxabase import DoxaBase
from doxabase.mcp_server import build_server
from doxabase.mcp_tools import (
    describe_context_slice_tool,
    describe_dataset_tool,
    describe_graph_revision_tool,
    describe_pattern_tool,
    describe_resource_tool,
    describe_staged_revision_tool,
    export_graph_tool,
    export_staged_revision_tool,
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
    record_graph_revision_tool,
    record_observation_tool,
    record_pattern_tool,
    search_tool,
    stage_graph_revision_tool,
    stage_systematisation_tool,
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
    assert "doxabase.describe_context_slice" in tool_names
    assert "doxabase.describe_resource" in tool_names
    assert "doxabase.describe_graph_revision" in tool_names
    assert "doxabase.describe_staged_revision" in tool_names
    assert "doxabase.describe_pattern" in tool_names
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
    assert "doxabase.export_staged_revision" in tool_names
    assert "doxabase.export_trig" in tool_names
    assert "doxabase.record_graph_revision" in tool_names
    assert "doxabase.stage_graph_revision" in tool_names
    assert "doxabase.stage_systematisation" in tool_names
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

    assert load_result["total_imported"] == 763
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


def test_record_graph_revision_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)
    validation = validate_graph_tool(db, scope="all")
    export_path = tmp_path / "review.trig"
    export_result = export_trig_tool(db, path=str(export_path), graphs=["workflow"])

    result = record_graph_revision_tool(
        db,
        summary="Fixture review bundle exported",
        rationale="The MCP wrapper test records why this review bundle exists.",
        changed_graphs=["observations", "patterns", "evidence"],
        included_graphs=export_result["graphs"],
        revision_type="rc:ExportRevision",
        revision_anchors=[
            "https://richcanopy.org/example/manifest/ais#DailyIndex",
        ],
        export_path=export_result["path"],
        graph_counts=export_result["graph_counts"],
        validation_scope=validation["scope"],
        validation_conforms=validation["conforms"],
        validation_result_count=validation["result_count"],
    )

    assert result["revision_iri"].startswith(
        "https://richcanopy.org/doxabase/generated/graph-revision/"
    )
    assert result["revision_type"] == "https://richcanopy.org/ns/rc#ExportRevision"
    assert result["graph"] == "history"
    assert result["triples"] > 0
    context = db.describe_resource(result["revision_iri"], graph="history")
    outgoing = {(triple.predicate, triple.object) for triple in context.outgoing}
    assert ("https://richcanopy.org/ns/rc#changedGraph", "map") not in outgoing
    assert ("https://richcanopy.org/ns/rc#includedGraph", "map") in outgoing
    description = describe_graph_revision_tool(db, result["revision_iri"])
    assert description["summary"] == "Fixture review bundle exported"
    assert description["changed_graphs"] == ["evidence", "observations", "patterns"]
    assert description["included_graphs"] == [
        "evidence",
        "map",
        "observations",
        "patterns",
    ]
    assert description["revision_anchors"][0]["iri"] == (
        "https://richcanopy.org/example/manifest/ais#DailyIndex"
    )
    assert description["validation_conforms"] is True
    assert description["graph_snapshots"]
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_staged_revision_tools_return_json_like_payloads(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_map_count = db.triple_count("map")
    content = """
    @prefix ex: <https://example.test/project#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:Messages a rc:Dataset, rc:Table ;
        rdfs:label "Messages" .
    """

    result = stage_graph_revision_tool(
        db,
        summary="Try messages table framing",
        rationale=(
            "Exploratory hunch: this map shape may generalise better once "
            "more message-like datasets arrive."
        ),
        additions=[{"graph": "map", "content": content}],
        stance="rc:ExploratoryHunch",
        validation_scope="all",
    )

    assert result["revision_iri"].startswith(
        "https://richcanopy.org/doxabase/generated/staged-revision/"
    )
    assert result["revision_type"] == "https://richcanopy.org/ns/rc#StagedRevision"
    assert result["revision_stance"] == "https://richcanopy.org/ns/rc#ExploratoryHunch"
    assert result["changed_graphs"] == ["map"]
    assert result["validation_conforms"] is True
    assert result["validation_result_count"] == 0
    assert result["patches"][0]["operation"] == "https://richcanopy.org/ns/rc#AdditionPatch"
    assert result["patches"][0]["before_triple_count"] == before_map_count
    assert result["patches"][0]["after_triple_count"] == before_map_count + 3
    assert db.triple_count("map") == before_map_count

    description = describe_staged_revision_tool(db, result["revision_iri"])
    assert description["revision_stance_label"] == "exploratory hunch"
    assert description["patches"][0]["target_graph"] == "map"
    assert "ex:Messages" in description["patches"][0]["content"]
    assert validate_graph_tool(db, scope="all")["conforms"] is True

    export_path = tmp_path / "staged-review.md"
    export = export_staged_revision_tool(
        db,
        iri=result["revision_iri"],
        path=str(export_path),
    )
    assert export["format"] == "markdown"
    assert export_path.exists()
    assert "exploratory hunch" in export_path.read_text()


def test_stage_systematisation_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    observation = db.record_observation(
        "Message-like rows repeatedly require identity reasoning.",
        evidence_summary="Synthetic test note backing the staged systematisation.",
        evidence_sources=["test://identity-ladder"],
    )
    ontology_framing = """
    @prefix ex: <https://example.test/project#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:IdentityLadder a rdfs:Class ;
        rdfs:label "Identity ladder" .
    """
    pattern_framing = f"""
    @prefix ex: <https://example.test/project#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:IdentityLadderPattern a rc:Pattern ;
        rdfs:label "Identity ladder pattern" ;
        rc:summary "Identity hints become stronger as more columns agree." ;
        rc:patternText "Repeated message-like rows appear to form a ladder of identity hints." ;
        rc:rationale "This keeps the idea exploratory without forcing a single key model." ;
        rc:patternTarget ex:Messages ;
        rc:supportingObservation <{observation.observation_iri}> ;
        rc:patternStability rc:EmergingPattern .
    """
    map_framing = """
    @prefix ex: <https://example.test/project#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:Messages a rc:Dataset, rc:Table ;
        rdfs:label "Messages" .
    """

    result = stage_systematisation_tool(
        db,
        summary="Explore identity-ladder modelling",
        intent="Preserve two possible RDF shapes for the same modelling hunch.",
        anchors=[observation.observation_iri],
        shared_additions=[{"graph": "ontology", "content": ontology_framing}],
        shared_context_summary="Define provisional identity-ladder vocabulary once.",
        framings=[
            {
                "label": "Pattern first",
                "graph": "patterns",
                "content": pattern_framing,
            },
            {
                "label": "Map candidate",
                "graph": "map",
                "content": map_framing,
                "stance": "rc:CandidateRevision",
            },
        ],
    )

    assert result["summary"] == "Explore identity-ladder modelling"
    assert result["anchors"] == [observation.observation_iri]
    assert len(result["framings"]) == 2
    assert len(result["staged_revisions"]) == 2
    assert result["framings"][0]["target_graphs"] == ["ontology", "patterns"]
    assert result["framings"][1]["target_graphs"] == ["ontology", "map"]
    assert result["framings"][0]["validation_conforms"] is True
    assert result["framings"][1]["validation_conforms"] is True

    first_iri = result["staged_revisions"][0]["revision_iri"]
    second = describe_staged_revision_tool(
        db,
        result["staged_revisions"][1]["revision_iri"],
    )
    assert second["alternative_to"]["iri"] == first_iri
    assert second["revision_anchors"][0]["iri"] == observation.observation_iri
    assert second["patches"][0]["patch_role_label"] == "shared context patch"
    assert second["patches"][1]["patch_role_label"] == "framing patch"
    assert "Systematisation intent:" in second["rationale"]


def test_describe_dataset_tool_returns_json_like_context(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)

    result = describe_dataset_tool(
        db,
        iri="https://richcanopy.org/example/manifest/polymarket#MarketSnapshots",
    )

    assert result["label"] == "Gamma Market Snapshots"
    assert result["row_semantics"]["iri"] == "https://richcanopy.org/ns/rc#SnapshotRow"
    assert result["entity_key"]["iri"] == (
        "https://richcanopy.org/example/manifest/polymarket#mkt_id"
    )
    assert result["entity_key"]["column_name"] == "id"
    assert result["entity_key"]["owning_dataset_label"] == "Gamma Market Snapshots"
    assert result["snapshot_timestamp"]["iri"] == (
        "https://richcanopy.org/example/manifest/polymarket#mkt_fetched_at"
    )
    assert result["snapshot_timestamp"]["column_name"] == "_fetched_at"
    assert result["schema_stability"]["iri"] == (
        "https://richcanopy.org/ns/rc#InferredSchema"
    )
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
    assert any(
        caveat["impact"]
        and "physical types may vary" in caveat["impact"]
        and caveat["severity"]["iri"] == "https://richcanopy.org/ns/rc#Moderate"
        for caveat in result["caveats"]
    )
    assert {transformation["transformation_type"] for transformation in result[
        "transformations"
    ]} == {"collection", "compaction"}
    assert any(
        relationship["relationship_kind"]
        == "https://richcanopy.org/ns/rc#SharedIdentifier"
        and relationship["relationship_kind_label"] == "SharedIdentifier"
        and relationship["label"]
        == "Condition ID identifies the same market across datasets"
        and any(
            column["column_name"] == "conditionId"
            and column["owning_dataset_label"] == "Gamma Market Snapshots"
            for column in relationship["identifying_columns"]
        )
        for relationship in result["relationships"]
    )
    assert any(
        related["relationship"] == "shares_identifier_with"
        and related["relationship_label"]
        == "Condition ID identifies the same market across datasets"
        and related["relationship_kind"]
        == "https://richcanopy.org/ns/rc#SharedIdentifier"
        and related["relationship_kind_label"] == "SharedIdentifier"
        and related["label"] == "Trade Events"
        for related in result["related_datasets"]
    )
    trade_group = next(
        group
        for group in result["related_dataset_groups"]
        if group["label"] == "Trade Events"
    )
    condition_id_reason = next(
        reason
        for reason in trade_group["reasons"]
        if {
            (column["owning_dataset_label"], column["column_name"])
            for column in reason["columns"]
        }
        == {
            ("Gamma Market Snapshots", "conditionId"),
            ("Trade Events", "conditionId"),
        }
    )
    assert condition_id_reason["relationship"] == "target_of"
    assert condition_id_reason["relationship_label"] == "Trades to Markets via conditionId"
    assert condition_id_reason["relationship_kind_label"] == "ForeignKey"
    assert condition_id_reason["declared"] is None
    assert condition_id_reason["referential_integrity"]["iri"] == (
        "https://richcanopy.org/ns/rc#PartialIntegrity"
    )
    assert {
        tag["relationship_kind_label"]
        for tag in condition_id_reason["relationship_tags"]
    } == {"ForeignKey", "SharedIdentifier"}
    assert [
        column["column_name"]
        for column in condition_id_reason["current_dataset_columns"]
    ] == ["conditionId"]
    assert [
        column["column_name"]
        for column in condition_id_reason["related_dataset_columns"]
    ] == ["conditionId"]


def test_describe_context_slice_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)
    seed_iri = "https://richcanopy.org/example/manifest/polymarket#MarketSnapshots"
    record_pattern_tool(
        db,
        summary="Market snapshots carry hourly Gamma market state.",
        pattern_text="Treat market snapshots as hourly Gamma state around condition IDs.",
        rationale="The fixture map describes snapshot rows, condition IDs, and hourly partitions together.",
        pattern_targets=[seed_iri],
        source_path="tests/test_mcp_tools.py",
        source_kind="rc:DocumentationSource",
    )

    result = describe_context_slice_tool(
        db,
        seed_iris=[seed_iri],
        profile="dataset_brief",
        max_triples=120,
    )

    assert result["profile"] == "dataset_brief"
    assert result["seeds"][0]["label"] == "Gamma Market Snapshots"
    assert result["dataset_contexts"][0]["iri"] == seed_iri
    assert result["pattern_contexts"]
    assert result["resource_count"] == len(result["resources"])
    assert result["route_counts"]["dataset_column"] >= 1
    assert result["route_counts"]["linked_pattern"] >= 1
    assert result["reading_order"][0].startswith("Start with seeds")
    assert any(
        route["route"] == "seed"
        and route["count"] == 1
        and route["priority"] == 0
        and route["meaning"] == "The resource the caller asked about directly."
        for route in result["route_legend"]
    )
    assert result["triple_count"] <= 120
    assert result["returned_triple_count"] == result["triple_count"]
    assert result["candidate_triple_count"] >= result["returned_triple_count"]
    assert result["omitted_triple_count"] == (
        result["candidate_triple_count"] - result["returned_triple_count"]
    )
    assert result["truncation_scope"] == "triples_only"
    assert result["truncated"] is True
    assert result["omitted_triple_count"] > 0
    assert result["triples"][0]["subject"] == seed_iri
    assert result["trig"] is None
    assert any(
        resource["iri"]
        == "https://richcanopy.org/example/manifest/polymarket#MarketSnapshots"
        and resource["referenced_only"] is False
        and resource["primary_route"]["route"] == "seed"
        and any(route["route"] == "seed" for route in resource["routes"])
        for resource in result["resources"]
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
    pattern_description = describe_pattern_tool(db, result["pattern_iri"])

    assert result["pattern_iri"] in {pattern["iri"] for pattern in patterns["entities"]}
    assert patterns["entities"][0]["label"] == (
        "parent_doc_id behaves as the attachment-to-message join."
    )
    assert context["label"] == "parent_doc_id behaves as the attachment-to-message join."
    assert any(
        triple["predicate"] == "https://richcanopy.org/ns/rc#supportingClaim"
        for triple in context["outgoing"]
    )
    assert pattern_description["summary"] == (
        "parent_doc_id behaves as the attachment-to-message join."
    )
    assert pattern_description["supporting_claims"][0]["claim_text"] == (
        "The child table joins to the parent table by parent_doc_id."
    )
    assert pattern_description["evidence"][0]["source_spans"][0]["source_section"] == (
        "Attachments"
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
    record_pattern_tool(
        db,
        summary="doc_id is the message identity handle.",
        pattern_text="Use doc_id as the message identity handle before joining.",
        rationale="The map marks doc_id as the table column that participates in message identity.",
        pattern_targets=[column, relationship_result["iri"]],
        source_path="tests/test_mcp_tools.py",
        source_kind="rc:DocumentationSource",
    )

    assert table_result["resource_type"] == "https://richcanopy.org/ns/rc#Table"
    assert column_result["resource_type"] == "https://richcanopy.org/ns/rc#Column"
    assert caveat_result["resource_type"] == "https://richcanopy.org/ns/rc#KnownCaveat"
    assert storage_result["resource_type"] == "https://richcanopy.org/ns/rc#StorageAccess"
    assert relationship_result["resource_type"] == (
        "https://richcanopy.org/ns/rc#SharedIdentifier"
    )
    description = describe_dataset_tool(db, iri=table)
    assert description["label"] == "Messages"
    linked_pattern_reason = description["linked_pattern_reasons"][0]
    assert linked_pattern_reason["pattern_iri"] == linked_pattern_reason["iri"]
    assert linked_pattern_reason["pattern_text"] == (
        "Use doc_id as the message identity handle before joining."
    )
    assert linked_pattern_reason["match_group_count"] == 2
    assert linked_pattern_reason["raw_match_count"] == 2
    assert linked_pattern_reason["relevance_tier_counts"] == {"direct": 2}
    assert {
        match["matched_resource"]["iri"]: match["match_type"]
        for match in linked_pattern_reason["matches"]
    } == {
        column: "pattern_target",
        relationship_result["iri"]: "pattern_target",
    }
    groups_by_resource = {
        group["matched_resource"]["iri"]: group
        for group in linked_pattern_reason["match_groups"]
    }
    assert groups_by_resource[column]["matched_resource"]["column_name"] == "doc_id"
    assert groups_by_resource[column]["relevance_tier"] == "direct"
    assert groups_by_resource[column]["route_labels"] == ["direct pattern target"]
    relationship_group = groups_by_resource[relationship_result["iri"]]
    assert relationship_group["matched_resource_kind"] == "SharedIdentifier"
    assert relationship_group["matched_resource"]["description"] == (
        "Shared identifier across doc_id, other_messages__doc_id"
    )
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
