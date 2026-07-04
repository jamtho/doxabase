"""Split from test_mcp_tools.py (distillation Phase 2); tests verbatim."""

from tests.mcp.support_mcp import *  # noqa: F401,F403


def test_describe_assertion_support_marks_generic_value_only_routes(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#DailyAccountStatus"
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Daily account status",
        is_table=True,
        row_semantics="rc:EventRow",
    )
    stage_graph_revision_tool(
        db,
        summary="Other snapshot row proposal",
        rationale=(
            "An unrelated staged row-semantics proposal should not become strong "
            "support just because it shares rc:SnapshotRow."
        ),
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:OtherTable rc:rowSemantics rc:SnapshotRow .
                """,
            }
        ],
        revision_anchors=["rc:SnapshotRow"],
        validation_scope="all",
    )

    result = describe_resource_tool(
        db,
        aspect="assertion_support",
        iri=dataset,
        predicate="rc:rowSemantics",
        object="rc:SnapshotRow",
        object_kind="iri",
    )

    summary = result["related_route_summaries"][0]
    assert summary["resource_kind"] == "revision"
    assert summary["route_types"] == ["revision_anchor"]
    assert summary["matched_resources"][0]["iri"] == RC + "SnapshotRow"
    assert summary["generic_value_only"] is True
    assert summary["relevance_tier"] == "generic_value_only"
    assert "Relevance tier: generic_value_only." in summary["route_note"]


def test_assertion_literal_metadata_tools_return_json_like_payloads(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:Orders a rc:Dataset, rc:Table ;
            rdfs:label "Orders"@en ;
            rc:hasColumn ex:is_active .

        ex:is_active a rc:Column ;
            rc:columnName "is_active" ;
            rc:physicalType rc:Boolean ;
            rc:nullable false .
        """,
        graph="map",
    )

    support = describe_resource_tool(
        db,
        aspect="assertion_support",
        iri="https://example.test/project#Orders",
        predicate="rdfs:label",
        object="Orders",
        object_kind="literal",
        object_lang="en",
    )
    assert support["requested_object"]["lang"] == "en"
    assert support["matching_triples"][0]["object_lang"] == "en"

    result = stage_map_assertion_change_tool(
        db,
        subject="https://example.test/project#is_active",
        predicate="rc:nullable",
        object="true",
        object_kind="literal",
        object_datatype="xsd:boolean",
        change_kind="replace",
        rationale="Exercise typed literal metadata through the MCP wrapper.",
    )

    assert result["object_datatype"] == str(XSD.boolean)
    assert result.get("object_lang") is None
    assert result["judgement_panel"]["proposed_value"]["datatype"] == str(
        XSD.boolean
    )
    description = describe_staged_revision_tool(
        db,
        result["staged_revision"]["revision_iri"],
    )
    assert description["judgement_panel"]["proposed_value"]["datatype"] == str(
        XSD.boolean
    )


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
    assert condition_id_reason.get("declared") is None
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


def test_describe_dataset_tool_exposes_aggregation_context(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)

    result = describe_dataset_tool(
        db,
        iri="https://richcanopy.org/example/manifest/ais#DailyIndex",
    )

    aggregation = next(
        relationship
        for relationship in result["relationships"]
        if relationship["relationship_kind"] == "https://richcanopy.org/ns/rc#Aggregation"
    )
    assert aggregation["source_dataset"]["label"] == "AIS Daily Broadcast Positions"
    assert aggregation["group_by_columns"][0]["column_name"] == "mmsi"
    assert result["layout_verification_status"]["iri"] == (
        "https://richcanopy.org/ns/rc#UnverifiedLayout"
    )
    assert "index/{year}/ais-{date}.parquet" in result[
        "layout_verification_note"
    ]
    assert result["partition_schemes"][0]["layout_verification_status"]["iri"] == (
        "https://richcanopy.org/ns/rc#GeneratedFromManifestLayout"
    )
    assert any(
        warning["code"] == "layout_needs_verification"
        and warning["domain"] == "query_planning"
        and warning["resource"]["iri"]
        == "https://richcanopy.org/example/manifest/ais#DailyIndex"
        for warning in result["operational_warnings"]
    )
    assert result.get("caveats", []) == []
    assert any(
        caveat["description"]
        and "MMSI does not reliably identify a single vessel" in caveat["description"]
        for caveat in result["upstream_caveats"]
    )
    message_count_mapping = next(
        mapping
        for mapping in aggregation["aggregated_columns"]
        if mapping["target_column"]["column_name"] == "message_count"
    )
    assert message_count_mapping["source_columns"][0]["column_name"] == "mmsi"
    assert message_count_mapping["aggregation_function"]["iri"] == (
        "https://richcanopy.org/ns/rc#Count"
    )

    wrong_predicate = describe_resource_tool(
        db,
        aspect="assertion_support",
        iri="https://richcanopy.org/example/manifest/ais#DailyIndex",
        predicate="rc:hasPartitionScheme",
        object="https://richcanopy.org/example/manifest/ais#daily_date_partition",
        object_kind="iri",
    )
    assert wrong_predicate["assertion_present"] is False
    assert "the requested predicate is absent on this subject" in (
        wrong_predicate["absence_note"]
    )
    assert "Nearby predicates on the same subject include" in (
        wrong_predicate["absence_note"]
    )
    assert "rc:partitionedBy" in wrong_predicate["absence_note"]
    assert any(
        hint["predicate"] == "https://richcanopy.org/ns/rc#partitionedBy"
        and hint["predicate_curie"] == "rc:partitionedBy"
        and hint["sample_values"][0]["value"]
        == "https://richcanopy.org/example/manifest/ais#daily_date_partition"
        for hint in wrong_predicate["predicate_hints"]
    )
    assert any(
        caveat["description"]
        and "MMSI does not reliably identify a single vessel" in caveat["description"]
        for caveat in aggregation["source_caveats"]
    )
    assert any(
        related["relationship"] == "aggregated_from"
        and related["label"] == "AIS Daily Broadcast Positions"
        for related in result["related_datasets"]
    )
    broadcast_group = next(
        group
        for group in result["related_dataset_groups"]
        if group["label"] == "AIS Daily Broadcast Positions"
    )
    assert any(
        caveat["impact"] and "Grouping by MMSI may conflate" in caveat["impact"]
        for reason in broadcast_group["reasons"]
        for caveat in reason["source_caveats"]
    )


def test_get_context_graph_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)
    seed_iri = "https://richcanopy.org/example/manifest/polymarket#MarketSnapshots"
    pattern = record_pattern_tool(
        db,
        summary="Market snapshots carry hourly Gamma market state.",
        pattern_text="Treat market snapshots as hourly Gamma state around condition IDs.",
        rationale="The fixture map describes snapshot rows, condition IDs, and hourly partitions together.",
        pattern_targets=[seed_iri],
        source_path="tests/test_mcp_tools.py",
        source_kind="rc:DocumentationSource",
    )

    result = get_context_graph_tool(
        db,
        seed_iris=[seed_iri],
        profile="dataset_brief",
        max_triples=120,
    )

    assert result["profile"] == "dataset_brief"
    assert result["seeds"][0]["label"] == "Gamma Market Snapshots"
    assert seed_iri in result["trig"]
    assert result["resource_count"] == len(result["resources"])
    assert result["route_counts"]["dataset_column"] >= 1
    assert result["route_counts"]["linked_pattern"] >= 1
    assert result["reading_order"][0].startswith("Start with seeds")
    assert any("route_summaries" in step for step in result["reading_order"])
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
    assert result["suggested_next_actions"][0]["args"] == {
        "seed_iris": [pattern["pattern_iri"]],
        "profile": "pattern_brief",
        "max_triples": 120,
    }
    assert result["suggested_next_actions"][1]["args"] == {
        "seed_iris": [seed_iri],
        "profile": "dataset_brief",
        "max_triples": result["candidate_triple_count"],
    }
    assert result.get("triples") is None
    assert seed_iri in result["trig"]
    preflight = preflight_context_slice_export_tool(
        db,
        seed_iris=[seed_iri],
        profile="dataset_brief",
        max_triples=5,
    )
    assert preflight["truncated"] is True
    role_loss_warning = next(
        warning
        for warning in preflight["warnings"]
        if "Context-slice export is truncated" in warning
    )
    assert "graphs and graph_counts describe only capped raw triples" in (
        role_loss_warning
    )
    assert "pattern_synthesis" in role_loss_warning
    assert [
        action["tool"].removeprefix("doxabase.") for action in preflight["suggested_next_actions"][:2]
    ] == [
        "preflight_context_slice_export",
        "export_context_slice",
    ]
    assert preflight["suggested_next_actions"][0]["args"] == {
        "seed_iris": [seed_iri],
        "profile": "dataset_brief",
        "max_triples": preflight["candidate_triple_count"],
        "include_seed_graphs": False,
        "limit": 20,
    }
    resources_by_iri = {resource["iri"]: resource for resource in result["resources"]}
    assert resources_by_iri[seed_iri]["surface_role"] == "current_map_context"
    assert resources_by_iri[pattern["pattern_iri"]]["surface_role"] == (
        "pattern_synthesis"
    )
    seed_resource = resources_by_iri[seed_iri]
    assert seed_resource["primary_route"] == seed_resource["routes"][0]
    assert set(seed_resource["primary_route"]) == {
        "depth",
        "route",
        "route_label",
    }
    assert any(
        resource["iri"]
        == "https://richcanopy.org/example/manifest/polymarket#MarketSnapshots"
        and resource["referenced_only"] is False
        and resource["primary_route"]["route"] == "seed"
        and any(route["route"] == "seed" for route in resource["routes"])
        for resource in result["resources"]
    )

    warning_db = DoxaBase.create(tmp_path / "warning-capsule.sqlite")
    warning_dataset = "https://example.test/project#Events"
    warning_layout = record_map_physical_layout_tool(
        warning_db,
        iri="https://example.test/project#events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        warning_db,
        iri=warning_dataset,
        label="Events",
        is_table=True,
        path_templates=["events/date={date}/*.parquet"],
        physical_layouts=[warning_layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    warning_result = get_context_graph_tool(
        warning_db,
        seed_iris=[warning_dataset],
        profile="dataset_brief",
    )
    assert warning_result["truncated"] is False
    assert warning_result.get("warnings", []) == []
    assert [
        action["tool"].removeprefix("doxabase.") for action in warning_result["suggested_next_actions"]
    ] == ["describe_query_context"]
    warning_action = warning_result["suggested_next_actions"][0]
    assert warning_action["tool"] == "doxabase.describe_query_context"
    assert warning_action["args"] == {"iri": warning_dataset}
    assert "missing_storage_access" in warning_action["reason"]

    repair_db = DoxaBase.create(tmp_path / "repair-capsule.sqlite")
    repair_dataset = "https://example.test/project#WarehouseOrders"
    relation = "mart.orders"
    repair_storage = record_map_storage_access_tool(
        repair_db,
        iri="https://example.test/project#orders_database_storage",
        label="Orders database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    repair_layout = record_map_physical_layout_tool(
        repair_db,
        iri="https://example.test/project#orders_table_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        repair_db,
        iri=repair_dataset,
        label="Warehouse orders",
        is_table=True,
        path_templates=[relation],
        storage_accesses=[repair_storage["iri"]],
        physical_layouts=[repair_layout["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    repair_result = get_context_graph_tool(
        repair_db,
        seed_iris=[repair_dataset],
        profile="dataset_brief",
    )
    assert repair_result["truncated"] is False
    assert [
        action["tool"].removeprefix("doxabase.") for action in repair_result["suggested_next_actions"]
    ] == ["describe_query_context"]
    repair_action = repair_result["suggested_next_actions"][0]
    assert repair_action["args"] == {"iri": repair_dataset}
    assert (
        "database_relation_template_source_mismatch" in repair_action["reason"]
    )
    repair_context = describe_query_context_tool(repair_db, iri=repair_dataset)
    assert repair_context["suggested_repair_action_groups"][0]["issue_code"] == (
        "database_relation_template_source_mismatch"
    )

    mismatch = get_context_graph_tool(
        db,
        seed_iris=[pattern["pattern_iri"]],
        profile="dataset_brief",
        max_triples=120,
    )
    assert any(
        "Seed is an rc:Pattern; rerun with profile='pattern_brief' or 'deep_lore'."
        in warning
        for warning in mismatch["warnings"]
    )
    claim = record_claim_observation_tool(
        db,
        summary="Market snapshots are hourly state.",
        claim_text="Market snapshots are hourly state.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=[seed_iri],
        evidence_summary="Context-slice wrapper claim evidence.",
        source_path="tests/test_mcp_tools.py",
        source_kind="rc:DocumentationSource",
    )
    claim_mismatch = get_context_graph_tool(
        db,
        seed_iris=[claim["claim_iri"]],
        profile="dataset_brief",
        max_triples=120,
    )
    assert claim_mismatch["route_counts"] == {"seed": 1}
    assert any(
        "Seed is an rc:Claim; rerun with profile='pattern_brief' or 'deep_lore'."
        in warning
        for warning in claim_mismatch["warnings"]
    )


def test_describe_assertion_support_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:Messages a rc:Dataset ;
            rc:hasColumn ex:message_id .

        ex:message_id a rc:Column ;
            rc:columnName "message_id" .
        """,
        graph="map",
    )

    result = describe_resource_tool(
        db,
        aspect="assertion_support",
        iri="https://example.test/project#Messages",
        predicate="rc:hasColumn",
        object="https://example.test/project#message_id",
    )

    assert result["assertion_present"] is True
    assert result["matching_triples"][0]["object"] == (
        "https://example.test/project#message_id"
    )
    assert result["same_subject_predicate_triples"][0]["object"] == (
        "https://example.test/project#message_id"
    )
    assert result.get("owner_dataset") is None
    assert result.get("absence_note") is None
    assert result.get("nearby_context_triples", []) == []
    assert result.get("nearby_caveat_links", []) == []
    assert result.get("related_routes", []) == []
    assert result.get("related_route_summaries", []) == []
    assert result["suggested_next_actions"][0]["tool"] == (
        "doxabase.get_context_graph"
    )
    assert result["suggested_next_actions"][0]["tool"] == (
        "doxabase.get_context_graph"
    )
    assert result["suggested_next_actions"][0]["args"]["seed_iris"] == [
        "https://example.test/project#Messages",
        "https://example.test/project#message_id",
    ]
    assert result["requested_object"]["resource"]["column_name"] == "message_id"
    assert "retrieval aid" in result["context_note"]
    assert "same-subject predicate triples" in result["support_scope_note"]


def test_search_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)

    result = search_tool(db, query="Parquet schemas", graph="map", limit=5)

    assert result["query"] == "Parquet schemas"
    assert result["graph"] == "map"
    assert result["limit"] == 5
    assert result["count"] >= 1
    assert result["returned_count"] == result["count"]
    assert result["total_count"] >= result["returned_count"]
    assert result["omitted_count"] >= 0
    assert result["has_more"] == (result.get("next_offset") is not None)
    assert any(
        "Parquet schemas are inferred" in match["text"]
        for match in result["matches"]
    )


def test_search_tool_serializes_pagination_metadata(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    for index in range(3):
        db.record_map_dataset(
            f"https://example.test/project#SearchToolPageDataset{index}",
            label=f"Search tool page dataset {index}",
            description=f"SearchToolPageProbe marker {index}",
            is_table=True,
        )

    result = search_tool(db, query="SearchToolPageProbe", graph="map", limit=2)

    assert result["count"] == 2
    assert result["returned_count"] == 2
    assert result["total_count"] == 3
    assert result["omitted_count"] == 1
    assert result["has_more"] is True
    assert result["next_offset"] == 2
    assert result["suggested_next_actions"][0]["tool"] == "doxabase.search"
    assert result["suggested_next_actions"][0]["args"] == {
        "query": "SearchToolPageProbe",
        "limit": 2,
        "offset": 2,
        "graph": "map",
    }


def test_list_entities_tool_serializes_pagination_metadata(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    for index in range(3):
        db.record_map_dataset(
            f"https://example.test/project#EntityToolPageDataset{index}",
            label=f"Entity tool page dataset {index}",
            description=f"EntityToolPageProbe marker {index}",
            is_table=True,
        )

    result = list_entities_tool(
        db,
        type="rc:Dataset",
        graph="map",
        text="EntityToolPageProbe",
        limit=2,
    )

    assert result["count"] == 2
    assert result["returned_count"] == 2
    assert result["total_count"] == 3
    assert result["omitted_count"] == 1
    assert result["has_more"] is True
    assert result["next_offset"] == 2
    assert result["suggested_next_actions"][0]["tool"] == "doxabase.list_entities"
    assert result["suggested_next_actions"][0]["args"] == {
        "limit": 2,
        "offset": 2,
        "type": "rc:Dataset",
        "graph": "map",
        "text": "EntityToolPageProbe",
    }


def test_search_tool_serializes_zero_match_retrieval_fallbacks(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    record_map_dataset_tool(
        db,
        iri="https://example.test/project#ForeshoreMaskBundle",
        label="Foreshore confidence mask bundle",
        description=(
            "Derived raster masks for harbor-margin QA, produced from "
            "phase-normalized tide correction."
        ),
        is_table=False,
    )

    result = search_tool(
        db,
        query="derived harbor QA mask shifted inland water-level adjustment",
        limit=5,
    )

    assert result["count"] == 0
    assert result.get("scope_hint") is None
    assert [action["tool"].removeprefix("doxabase.") for action in result["suggested_next_actions"]] == [
        "search",
        "search",
        "search",
        "list_entities",
        "search",
    ]
    assert result["suggested_next_actions"][1]["args"] == {
        "query": "harbor",
        "graph": "map",
        "limit": 5,
        "offset": 0,
    }
    assert result["suggested_next_actions"][3]["args"] == {
        "graph": "map",
        "text": "derived",
        "limit": 5,
        "offset": 0,
    }
    assert result["suggested_next_actions"][4]["tool"] == "doxabase.search"
    assert result["suggested_next_actions"][4]["args"]["scope"] == "staged_patches"


def test_search_tool_suggests_scoped_retries_for_seed_heavy_unscoped_results(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    record_map_storage_access_tool(
        db,
        iri="https://example.test/project#OnlyStorageAccess",
        label="Only project storage access",
        description="Project storage access fact that should be easy to find.",
        storage_protocol="rc:S3CompatibleStorage",
        location_kind="prefix",
        storage_root="s3://example-project",
    )

    result = search_tool(db, query="storage", limit=5)

    assert result.get("graph") is None
    assert result["scope_hint"]["status"] == "seed_heavy_unscoped_results"
    assert result["scope_hint"]["seed_match_count"] > result["scope_hint"][
        "project_match_count"
    ]
    assert result["scope_hint"]["suggested_graphs"] == [
        "map",
        "observations",
        "patterns",
        "evidence",
    ]
    assert result["suggested_next_actions"] == result["scope_hint"][
        "suggested_next_actions"
    ]
    first_action = result["suggested_next_actions"][0]
    assert first_action["tool"] == "doxabase.search"
    assert first_action["tool"] == "doxabase.search"
    assert first_action["args"] == {
        "query": "storage",
        "graph": "map",
        "limit": 5,
        "offset": 0,
    }

    scoped = search_tool(db, query="storage", graph="map", limit=5)
    assert scoped.get("scope_hint") is None
    assert scoped.get("suggested_next_actions", []) == []
    assert {match["graph"] for match in scoped["matches"]} == {"map"}

