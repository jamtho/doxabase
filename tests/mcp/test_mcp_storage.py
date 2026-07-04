"""Split from test_mcp_tools.py (distillation Phase 2); tests verbatim."""

from tests.mcp.support_mcp import *  # noqa: F401,F403


@pytest.mark.anyio
async def test_build_server_registers_expected_tools(tmp_path: Path) -> None:
    server = build_server(tmp_path / "mcp.sqlite")
    tools = await server.list_tools()
    tool_names = {tool.name for tool in tools}

    assert "doxabase.project_brief" in server.instructions
    assert "doxabase.export_preflight" in server.instructions
    assert "doxabase.list_docs" in tool_names
    assert "doxabase.get_doc" in tool_names
    assert "doxabase.graph_overview" in tool_names
    assert "doxabase.scan_sensitive_literals" in tool_names
    assert "doxabase.export_preflight" in tool_names
    assert "doxabase.project_brief" in tool_names
    assert "doxabase.list_entities" in tool_names
    assert "doxabase.describe_dataset" in tool_names
    assert "doxabase.describe_analysis_view" in tool_names
    assert "doxabase.describe_profile_run" in tool_names
    assert "doxabase.draft_profile_map_updates" in tool_names
    assert "doxabase.plan_profile_followthrough" in tool_names
    assert "doxabase.stage_profile_map_updates" in tool_names
    assert "doxabase.describe_query_context" in tool_names
    assert "doxabase.draft_query_plan" in tool_names
    assert "doxabase.stage_query_physical_layout_repair" in tool_names
    assert "doxabase.stage_query_storage_access_repair" in tool_names
    assert "doxabase.describe_context_slice" in tool_names
    assert "doxabase.preflight_context_slice_export" in tool_names
    assert "doxabase.export_context_slice" in tool_names
    assert "doxabase.describe_resource" in tool_names
    assert "doxabase.describe_graph_revision" in tool_names
    assert "doxabase.describe_revision_snapshot_evidence" in tool_names
    assert "doxabase.describe_revision_graph_snapshot" in tool_names
    assert "doxabase.describe_applied_revision_diff" in tool_names
    assert "doxabase.describe_graph_version_diff" in tool_names
    assert "doxabase.list_graph_revisions" in tool_names
    assert "doxabase.list_graph_versions" in tool_names
    assert "doxabase.describe_revision_lineage" in tool_names
    assert "doxabase.list_resource_revisions" in tool_names
    assert "doxabase.describe_resource_revision_lineage" in tool_names
    assert "doxabase.describe_staged_revision" in tool_names
    assert "doxabase.check_staged_revision_apply" in tool_names
    assert "doxabase.draft_staged_revision_rebase" in tool_names
    assert "doxabase.draft_systematisation_shared_context_rerun" in tool_names
    assert "doxabase.plan_staged_revision_recovery" in tool_names
    assert "doxabase.start_staged_revision_recovery_session" in tool_names
    assert "doxabase.describe_staged_revision_recovery_session" in tool_names
    assert "doxabase.describe_pattern" in tool_names
    assert "doxabase.record_observation" in tool_names
    assert "doxabase.record_query_result" in tool_names
    assert "doxabase.record_claim_observation" in tool_names
    assert "doxabase.record_claim_reconsideration" in tool_names
    assert "doxabase.record_column_profile" in tool_names
    assert "doxabase.record_dataset_profile" in tool_names
    assert "doxabase.record_profile_bundle" in tool_names
    assert "doxabase.record_domain_network_profile" in tool_names
    assert "doxabase.record_pattern" in tool_names
    assert "doxabase.record_map_dataset" in tool_names
    assert "doxabase.record_map_analysis_view" in tool_names
    assert "doxabase.record_map_analysis_view_bundle" in tool_names
    assert "doxabase.record_analysis_packet" in tool_names
    assert "doxabase.record_map_table_bundle" in tool_names
    assert "doxabase.record_profiled_parquet_table" in tool_names
    assert "doxabase.record_profile_to_capsule_manifest" in tool_names
    assert "doxabase.record_map_column" in tool_names
    assert "doxabase.record_map_caveat" in tool_names
    assert "doxabase.record_map_storage_access" in tool_names
    assert "doxabase.record_map_physical_layout" in tool_names
    assert "doxabase.record_map_partition_scheme" in tool_names
    assert "doxabase.record_map_relationship" in tool_names
    assert "doxabase.record_map_asset_transform" in tool_names
    assert "doxabase.search" in tool_names
    assert "doxabase.search_staged_patch_payloads" in tool_names
    assert "doxabase.export_graph" in tool_names
    assert "doxabase.export_handoff_bundle" in tool_names
    assert "doxabase.export_profile_insight_review_bundle" in tool_names
    assert "doxabase.export_revision_snapshots" in tool_names
    assert "doxabase.import_handoff_bundle" in tool_names
    assert "doxabase.import_revision_snapshots" in tool_names
    assert "doxabase.replace_graph_triples" in tool_names
    assert "doxabase.export_staged_revision" in tool_names
    assert "doxabase.export_staged_revisions" in tool_names
    assert "doxabase.export_trig" in tool_names
    assert "doxabase.record_graph_revision" in tool_names
    assert "doxabase.stage_graph_revision" in tool_names
    assert "doxabase.restage_staged_revision" in tool_names
    assert "doxabase.restage_staged_revisions" in tool_names
    assert "doxabase.draft_map_assertion_change" in tool_names
    assert "doxabase.stage_map_assertion_change" in tool_names
    assert "doxabase.stage_systematisation" in tool_names
    assert "doxabase.stage_pattern_promotion" in tool_names
    assert "doxabase.apply_staged_revision" in tool_names
    assert "doxabase.load_example_fixtures" in tool_names
    assert "doxabase.validate_graph" in tool_names

    tool_by_name = {tool.name: tool for tool in tools}
    storage_access_description = (
        tool_by_name["doxabase.record_map_storage_access"].description or ""
    )
    assert "rc:DatabaseStorage" in storage_access_description
    assert "database relation identifiers" in storage_access_description
    assert "storage_root" in storage_access_description
    assert 'location_kind="bucket"' in storage_access_description
    assert "external:intentionally-unrecorded" in storage_access_description
    relationship_description = (
        tool_by_name["doxabase.record_map_relationship"].description or ""
    )
    assert "foreign_key" in relationship_description
    assert "rc:ForeignKey" in relationship_description
    assert "body -> body_top" in relationship_description
    assert "source_columns" in relationship_description
    assert "record_map_asset_transform" in relationship_description
    asset_transform_description = (
        tool_by_name["doxabase.record_map_asset_transform"].description or ""
    )
    assert "asset-level transform" in asset_transform_description
    assert "rc:Aggregation" in asset_transform_description
    assert "outputs[].target_dataset" in asset_transform_description
    assert "body -> body_top" in asset_transform_description
    assert "source_columns" in asset_transform_description


@pytest.mark.anyio
async def test_server_doc_tools_do_not_open_capsule_at_startup(
    tmp_path: Path,
) -> None:
    capsule_path = tmp_path / "missing" / "mcp.sqlite"
    server = build_server(capsule_path)

    assert not capsule_path.exists()

    _, result = await server.call_tool(
        "doxabase.get_doc",
        {"doc_id": "start_here", "max_chars": 80},
    )

    assert result["id"] == "start_here"
    assert result["content"].startswith("# Start Here")
    assert not capsule_path.exists()

    graph_capsule_path = tmp_path / "graph.sqlite"
    graph_server = build_server(graph_capsule_path)
    assert not graph_capsule_path.exists()

    _, overview = await graph_server.call_tool(
        "doxabase.graph_overview",
        {"limit": 5},
    )

    assert graph_capsule_path.exists()
    assert "named_graphs" in overview


@pytest.mark.anyio
async def test_mcp_tool_schemas_match_tool_layer_signatures(
    tmp_path: Path,
) -> None:
    server = build_server(tmp_path / "mcp.sqlite")
    mismatches: dict[str, dict[str, list[str]]] = {}

    for tool in await server.list_tools():
        short_name = tool.name.removeprefix("doxabase.")
        tool_func = getattr(mcp_tools, f"{short_name}_tool", None)
        if tool_func is None:
            continue
        tool_parameters = [
            name
            for name in inspect.signature(tool_func).parameters
            if name != "db"
        ]
        schema_properties = list(tool.inputSchema.get("properties", {}))
        missing = [
            name for name in tool_parameters if name not in schema_properties
        ]
        extra = [
            name for name in schema_properties if name not in tool_parameters
        ]
        if missing or extra:
            mismatches[tool.name] = {"missing": missing, "extra": extra}

    assert mismatches == {}


def test_doc_tools_return_json_like_payloads() -> None:
    result = list_docs_tool()
    doc_ids = {doc["id"] for doc in result["docs"]}
    response_shapes_doc = next(
        doc for doc in result["docs"] if doc["id"] == "response_shapes"
    )

    assert result["docs"][0]["id"] == "start_here"
    assert "start_here" in doc_ids
    assert "overview" in doc_ids
    assert "graph_roles" in doc_ids
    assert "response_shapes" in doc_ids
    assert "profiling" in doc_ids
    assert "systematisation" in doc_ids
    assert response_shapes_doc["size_chars"] > 0
    assert {
        section["anchor"]
        for section in response_shapes_doc["sections"]
    } >= {
        "profile-helper-records",
        "dataset-storage-and-layout",
        "linked-pattern-reasons",
        "query-context",
        "draft-query-plan",
        "staged-detail-and-current-apply-summary",
        "apply-check-patch-checks-and-snapshot-drift",
        "validation-diagnostics",
        "staged-revisions",
    }

    section = get_doc_tool(
        "response_shapes",
        section="Profile Helper Records",
        max_chars=300,
    )
    assert section["selected_section"]["anchor"] == "profile-helper-records"
    assert section["start_char"] == section["selected_section"]["start_char"]
    assert section["content"].startswith("## Profile Helper Records")
    assert section["truncated"] is True

    offset = get_doc_tool(
        "response_shapes",
        start_char=section["end_char"],
        max_chars=120,
    )
    assert offset["start_char"] == section["end_char"]
    assert len(offset["content"]) <= 120
    assert offset["selected_section"]["anchor"] == "profile-helper-records"

    nested_section = get_doc_tool(
        "response_shapes",
        section="Apply Check, Patch Checks, And Snapshot Drift",
        max_chars=300,
    )
    assert nested_section["selected_section"]["anchor"] == (
        "apply-check-patch-checks-and-snapshot-drift"
    )
    assert nested_section["content"].startswith(
        "### Apply Check, Patch Checks, And Snapshot Drift"
    )


def test_fixture_loading_and_validation_tools(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    load_result = load_example_fixtures_tool(db)
    overview = graph_overview_tool(db)
    tables = list_entities_tool(db, type="rc:Table", graph="map")
    validation = validate_graph_tool(db, scope="all")

    assert load_result["total_imported"] == 805
    assert load_result["totals"]["patterns"] == 14
    assert overview["key_counts"]["tables"] >= 7
    assert overview["key_counts"]["patterns"] >= 1
    assert tables["count"] >= 7
    assert validation["conforms"] is True

    support = describe_assertion_support_tool(
        db,
        subject="https://richcanopy.org/example/manifest/polymarket#px_price",
        predicate="rc:physicalType",
        object="rc:Varchar",
    )

    assert support["related_observations"][0]["iri"] == (
        "https://richcanopy.org/example/manifest/polymarket#"
        "obs_price_payload_caveat_from_manifest"
    )
    assert support["related_claims"][0]["iri"] == (
        "https://richcanopy.org/example/manifest/polymarket#"
        "claim_price_payload_requires_filtering"
    )

    assert support["related_patterns"][0]["iri"] == (
        "https://richcanopy.org/example/manifest/polymarket#"
        "pattern_price_payload_boundary"
    )
    assert support["related_evidence"][0]["iri"] == (
        "https://richcanopy.org/example/manifest/polymarket#"
        "evidence_price_payload_caveat_manifest"
    )
    route_types = {route["route_type"] for route in support["related_routes"]}
    assert "observed_column" in route_types
    assert "claim_target" in route_types
    assert "pattern_target" in route_types
    assert "supporting_claim" in route_types
    summary_by_kind = {
        summary["resource_kind"]: summary
        for summary in support["related_route_summaries"]
    }
    assert summary_by_kind["claim"]["strongest_route_type"] == "claim_target"
    assert "claim target" in summary_by_kind["claim"]["route_labels"]
    assert summary_by_kind["pattern"]["route_count"] >= 2

    token_support = describe_assertion_support_tool(
        db,
        subject="https://richcanopy.org/example/manifest/polymarket#px_token_id",
        predicate="rc:physicalType",
        object="rc:Double",
    )

    assert token_support["assertion_present"] is False
    assert "Current same-subject/predicate value(s): VARCHAR" in (
        token_support["absence_note"]
    )
    assert token_support.get("related_route_summaries", []) == []
    mixed_price_links = [
        link
        for link in token_support["nearby_caveat_links"]
        if link["caveat"]["iri"]
        == "https://richcanopy.org/example/manifest/polymarket#caveat_mixed_type_price"
    ]
    assert len(mixed_price_links) == 1
    assert mixed_price_links[0]["scope"] == "owner_dataset"
    assert mixed_price_links[0]["route_type"] == "owner_dataset_has_known_caveat"
    assert mixed_price_links[0]["via_resource"]["iri"] == (
        "https://richcanopy.org/example/manifest/polymarket#PriceSnapshots"
    )
    assert mixed_price_links[0]["matched_resource"]["iri"] == (
        "https://richcanopy.org/example/manifest/polymarket#px_token_id"
    )


def test_replace_graph_triples_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:Customers a rc:Dataset ;
            rdfs:label "Customers scratch table" .
        """,
        graph="map",
    )

    result = replace_graph_triples_tool(
        db,
        graph="map",
        removals="""
            @prefix ex: <https://example.test/project#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            ex:Customers rdfs:label "Customers scratch table" .
        """,
        additions="""
            @prefix ex: <https://example.test/project#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            ex:Customers rdfs:label "Customers scratch table, drifted" .
        """,
        expected_count=2,
    )

    assert result["graph"] == "map"
    assert result["before_count"] == 2
    assert result["after_count"] == 2
    assert result["same_count"] is True
    assert result["digest_changed"] is True
    assert result["triples_removed"] == 1
    assert result["triples_added"] == 1
    assert result["expected_count"] == 2
    assert result["allow_count_change"] is False


def test_map_authoring_tools_return_json_like_payloads(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/project#"
    table = f"{base}messages"
    column = f"{base}messages__doc_id"
    other_table = f"{base}other_messages"
    other_column = f"{base}other_messages__doc_id"
    caveat = f"{base}messages_caveat"
    storage = f"{base}local_access"
    layout = f"{base}parquet_layout"
    partition = f"{base}daily_partition"

    table_result = record_map_dataset_tool(
        db,
        iri=table,
        label="Messages",
        is_table=True,
        path_templates=["data/messages.parquet"],
        layout_verification_status="rc:CandidateLayout",
        layout_verification_note="A plausible test path before query verification.",
    )
    record_map_dataset_tool(
        db,
        iri=other_table,
        label="Other messages",
        is_table=True,
    )
    column_result = record_map_column_tool(
        db,
        iri=column,
        table_iri=table,
        column_name="doc_id",
        physical_type="rc:Varchar",
        nullable=False,
    )
    record_map_column_tool(
        db,
        iri=other_column,
        table_iri=other_table,
        column_name="other_messages__doc_id",
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
        layout_verification_status="rc:VerifiedByListingLayout",
        layout_verification_note="Confirmed by a local directory listing.",
        datasets=[table],
    )
    layout_result = record_map_physical_layout_tool(
        db,
        iri=layout,
        file_format="rc:Parquet",
        compression_codec="rc:ZstdCompression",
        layout_verification_status="rc:VerifiedByQueryLayout",
        layout_verification_note="A representative read used this file format.",
        datasets=[table],
    )
    partition_result = record_map_partition_scheme_tool(
        db,
        iri=partition,
        partition_columns=[column],
        granularity="rc:Daily",
        path_template="data/messages/dt={date}.parquet",
        redundant_partition_key=column,
        layout_verification_status="rc:CandidateLayout",
        layout_verification_note="Partition path still needs a real object listing.",
        datasets=[table],
    )
    relationship_result = record_map_relationship_tool(
        db,
        iri=f"{base}messages_doc_id_shared",
        relationship_type="shared_identifier",
        identifying_columns=[column, other_column],
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
    assert layout_result["resource_type"] == (
        "https://richcanopy.org/ns/rc#PhysicalLayout"
    )
    assert partition_result["resource_type"] == (
        "https://richcanopy.org/ns/rc#PartitionScheme"
    )
    assert relationship_result["resource_type"] == (
        "https://richcanopy.org/ns/rc#SharedIdentifier"
    )
    description = describe_dataset_tool(db, iri=table)
    assert description["label"] == "Messages"
    assert description["layout_verification_status"]["iri"] == (
        "https://richcanopy.org/ns/rc#CandidateLayout"
    )
    assert description["layout_verification_note"] == (
        "A plausible test path before query verification."
    )
    assert description["storage_accesses"][0]["layout_verification_status"]["iri"] == (
        "https://richcanopy.org/ns/rc#VerifiedByListingLayout"
    )
    assert description["storage_accesses"][0]["layout_verification_note"] == (
        "Confirmed by a local directory listing."
    )
    assert description["physical_layouts"][0]["file_format"]["iri"] == (
        "https://richcanopy.org/ns/rc#Parquet"
    )
    assert description["physical_layouts"][0]["layout_verification_status"]["iri"] == (
        "https://richcanopy.org/ns/rc#VerifiedByQueryLayout"
    )
    assert description["partition_schemes"][0]["path_template"] == (
        "data/messages/dt={date}.parquet"
    )
    assert description["partition_schemes"][0]["layout_verification_status"]["iri"] == (
        "https://richcanopy.org/ns/rc#CandidateLayout"
    )
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

