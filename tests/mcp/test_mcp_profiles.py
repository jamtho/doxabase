"""Split from test_mcp_tools.py (distillation Phase 2); tests verbatim."""

from tests.mcp.support_mcp import *  # noqa: F401,F403


@pytest.mark.anyio
async def test_profile_mcp_tools_expose_sampled_snapshot_gate(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "mcp.sqlite")
    # The sampled-snapshot gate now lives behind record_profile's per-kind
    # spec; the dispatcher's targeted errors must reveal it as a valid field
    # for both kinds.
    for kind in ("dataset", "bundle"):
        with pytest.raises(DoxaBaseError) as excinfo:
            record_profile_tool(db, kind=kind, spec={"bogus_field": 1})
        assert "allow_sampled_row_count_snapshot" in str(excinfo.value)
        assert "bogus_field" in str(excinfo.value)


def test_query_context_keeps_query_overlay_with_profile_run_candidates(
    tmp_path: Path,
) -> None:
    warehouse = tmp_path / "warehouse"
    warehouse.mkdir()
    csv_path = warehouse / "orders.csv"
    csv_path.write_text("order_id,status\n1,paid\n2,pending\n", encoding="utf-8")
    result_path = tmp_path / "orders_status.json"
    result_path.write_text('{"paid": 1, "pending": 1}\n', encoding="utf-8")

    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    profile_evidence = "https://example.test/project#OrdersProfileEvidence"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    record_profile_bundle_tool(
        db,
        dataset_iri=dataset,
        dataset_summary="Orders profile run recorded row and status evidence.",
        evidence_summary="Synthetic profile run before query planning.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=profile_evidence,
        row_count=2,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": "https://example.test/project#OrdersStatus",
                "column_name": "status",
                "summary": "Status was profiled in the same run.",
                "row_count": 2,
            }
        ],
    )
    query_result = record_query_result_tool(
        db,
        summary="Orders status aggregate scanned the reviewed local CSV.",
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path=str(tmp_path / "orders_status.sql"),
        query_hash="sha256:mixed-profile-query",
        result_sources=[str(result_path)],
        scanned_source_paths=[str(csv_path)],
        row_count=2,
    )

    context = describe_query_context_tool(db, iri=dataset)

    assert context["readiness"] == "insufficient_metadata"
    assert context["profile_summary"]["profile_run_candidates"][0][
        "evidence_iri"
    ] == profile_evidence
    action_tools = [
        action["tool"].removeprefix("doxabase.") for action in context["suggested_next_actions"]
    ]
    assert action_tools[:2] == [
        "describe_resource",
        "stage_revision",
    ]
    overlay_actions = [
        action
        for action in context["suggested_next_actions"]
        if (action["tool"], action["args"].get("kind"), action["args"].get("dry_run")) == ("doxabase.stage_revision", "query_evidence_overlay", True)
    ]
    assert len(overlay_actions) == 1
    overlay_action = overlay_actions[0]
    assert overlay_action["args"]["spec"]["dataset_iri"] == dataset
    assert overlay_action["args"]["spec"]["evidence_iri"] == (
        query_result["evidence_iri"]
    )


def test_record_profiled_parquet_table_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/mcp-profiled-parquet#"
    table = f"{base}orders"

    result = record_profiled_parquet_table_tool(
        db,
        iri=table,
        label="Orders",
        dataset_summary="Orders profile captured reviewed aggregate counts.",
        evidence_summary="Reviewed no-I/O Parquet profile manifest.",
        evidence_sources=["scratch://orders-profile.json"],
        columns=[
            {
                "column_name": "order_id",
                "physical_type": "rc:Varchar",
                "nullable": False,
                "null_count": 0,
                "distinct_count": 12,
            },
            {
                "column_name": "status",
                "physical_type": "rc:Varchar",
                "null_count": 0,
                "distinct_count": 3,
            },
        ],
        path_templates=["orders/current.parquet"],
        row_count=12,
        storage_access_iri=f"{base}orders_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        location_kind="object",
        storage_root=str(tmp_path / "orders.parquet"),
        physical_layout_iri=f"{base}orders_layout",
        compression_codec="rc:ZstdCompression",
    )

    assert result["dataset_iri"] == table
    assert result["shared_evidence_iri"] == f"{table}/profile-evidence/parquet"
    assert result["table_bundle"]["physical_layout"]["iri"] == (
        f"{base}orders_layout"
    )
    assert result["table_bundle"]["column_iris"] == [
        f"{table}__order_id",
        f"{table}__status",
    ]
    assert result["profile_observation_count"] == 3
    assert result["profile_bundle"]["handoff_entrypoints"][
        "profile_run_available"
    ] is True
    assert isinstance(result["profile_draft_recommendation_count"], int)
    assert isinstance(result["query_readiness"], str)
    assert any(
        action["tool"] == "doxabase.describe_resource"
        and action["args"].get("aspect") == "profile_run"
        for action in result["suggested_next_actions"]
    )

    profile_run = describe_resource_tool(
        db,
        aspect="profile_run",
        iri=table,
        evidence_iri=result["shared_evidence_iri"],
        limit=None,
    )
    assert profile_run["total_profile_count"] == 3
    assert db.validate_graph(scope="all").conforms


def test_record_profile_to_capsule_manifest_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/mcp-profile-manifest#"
    table = f"{base}orders"
    view = f"{base}paid_orders"

    result = record_profile_to_capsule_manifest_tool(
        db,
        manifest={
            "format": "doxabase.profile_to_capsule_manifest.v1",
            "table_defaults": {
                "storage_protocol": "rc:LocalFilesystemStorage",
                "access_mode": "rc:ReadOnlyAccess",
                "location_kind": "directory",
                "storage_root": str(tmp_path),
                "layout_verification_status": "rc:VerifiedByQueryLayout",
                "physical_layout_verification_status": "rc:VerifiedByQueryLayout",
            },
            "tables": [
                {
                    "iri": table,
                    "label": "Orders",
                    "dataset_summary": "Orders profile captured reviewed counts.",
                    "evidence_summary": "Reviewed Orders profile manifest.",
                    "evidence_sources": ["scratch://profiles/orders.json"],
                    "path_templates": ["orders/current.parquet"],
                    "storage_path_templates": ["orders/current.parquet"],
                    "row_count": 6,
                    "columns": [
                        {"column_name": "order_id", "physical_type": "rc:Integer"},
                        {"column_name": "status", "physical_type": "rc:Varchar"},
                    ],
                }
            ],
            "analysis_views": [
                {
                    "iri": view,
                    "label": "Paid orders",
                    "source_datasets": [table],
                    "row_count_snapshot": 3,
                    "query_snippets": [
                        {
                            "query_text": "select * from orders where status = 'paid'",
                            "query_language": "DuckDB SQL",
                            "query_engine": "duckdb",
                        }
                    ],
                }
            ],
        },
    )

    assert result["manifest_format"] == "doxabase.profile_to_capsule_manifest.v1"
    assert result["table_iris"] == [table]
    assert result["analysis_view_iris"] == [view]
    assert result["table_count"] == 1
    assert result["analysis_view_count"] == 1
    assert result["domain_network_profile_count"] == 0
    assert result["domain_network_profile_observation_count"] == 0
    assert result.get("domain_network_profile_evidence_iris", []) == []
    assert result.get("domain_network_pattern_iris", []) == []
    assert result["profile_observation_count"] == 3
    assert result["query_readiness_counts"] == {"ready_for_query_planning": 1}
    assert result["analysis_view_bundle"]["query_snippet_count"] == 1
    assert "describe_query_context" in {
        action["tool"].removeprefix("doxabase.") for action in result["suggested_next_actions"]
    }
    assert (
        describe_query_context_tool(db, iri=view)["readiness"]
        == "logical_analysis_view"
    )
    assert db.validate_graph(scope="all").conforms


def test_record_domain_network_profile_tool_returns_handoff_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/mcp-domain-network#"
    dataset = f"{base}messages"
    evidence = f"{base}domain_network_profile_evidence"
    view = f"{base}network_view"

    record_map_table_bundle_tool(
        db,
        iri=dataset,
        label="Messages",
        columns=[
            {"column_name": "sender_domain", "physical_type": "rc:Varchar"},
            {"column_name": "recipient_domain", "physical_type": "rc:Varchar"},
        ],
        row_count_snapshot=50,
    )
    result = record_domain_network_profile_tool(
        db,
        dataset_iri=dataset,
        summary="Domain-network extraction profile.",
        evidence_summary="Reviewed aggregate counts from a domain parser.",
        evidence_sources=["scratch://domain-network-profile.json"],
        evidence_iri=evidence,
        sample_size=50,
        sample_scope="All reviewed message-like rows.",
        sample_method="Aggregate query over parsed domains.",
        extraction_method="Lowercase domain extraction from parsed addresses.",
        coverage_counts=[
            {"bucket": "sender_and_recipient_extracted", "count": 40},
            {"bucket": "neither_extracted", "count": 10},
        ],
        coverage_counts_exhaustive=True,
        domain_pair_counts=[
            {
                "sender_domain": "example.test",
                "recipient_domain": "vendor.test",
                "count": 12,
            }
        ],
        analysis_view_iri=view,
        analysis_view_label="Message-like network view",
        caveat_description="Domain graphs depend on extraction coverage.",
        pattern_summary="Domain networks require extraction denominators.",
        pattern_text=(
            "Aggregate domain-pair counts should be read with the coverage "
            "matrix."
        ),
        pattern_rationale="The parser can miss senders or recipients.",
    )

    assert result["dataset_iri"] == dataset
    assert result["evidence_iri"] == evidence
    assert result["analysis_view"]["iri"] == view
    assert result["caveat"]["resource_type"] == RC + "KnownCaveat"
    assert result["pattern"]["pattern_iri"].startswith(
        "https://richcanopy.org/doxabase/generated/pattern/"
    )
    assert len(result["profile_observation_iris"]) == 2
    assert [action["tool"].removeprefix("doxabase.") for action in result["suggested_next_actions"]] == [
        "describe_dataset",
        "describe_resource",
        "describe_resource",
        "describe_resource",
    ]
    assert result["suggested_next_actions"][1]["args"]["aspect"] == "profile_run"
    assert result["suggested_next_actions"][2]["args"]["aspect"] == "analysis_view"
    assert result["suggested_next_actions"][3]["args"]["aspect"] == "pattern"

    profile_run = describe_resource_tool(
        db,
        aspect="profile_run",
        iri=dataset,
        evidence_iri=evidence,
        limit=None,
    )
    assert profile_run["total_profile_count"] == 2
    assert describe_query_context_tool(db, iri=view)["readiness"] == (
        "logical_analysis_view"
    )


def test_describe_query_context_tool_routes_profile_evidence_before_query_draft(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)
    dataset = "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"
    shared_evidence = "https://example.test/project#AISProfileRunEvidence"

    record_profile_bundle_tool(
        db,
        dataset_iri=dataset,
        dataset_summary=(
            "AIS daily broadcasts were profiled before drafting a query plan."
        ),
        evidence_summary="Synthetic profile run for query-planning route coverage.",
        evidence_sources=["test://ais-query-profile-routing"],
        shared_evidence_iri=shared_evidence,
        sample_size=42,
        sample_scope="Synthetic bounded fixture profile.",
        sample_method="Focused query-planning routing trial.",
        row_count=42,
        update_map_snapshot=True,
        map_label="AIS Daily Broadcast Positions",
        is_table=True,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": (
                    "https://richcanopy.org/example/manifest/ais#bc_date"
                ),
                "column_name": "date",
                "summary": "AIS broadcast date was profiled in the same run.",
                "row_count": 42,
            }
        ],
    )

    context = describe_query_context_tool(db, iri=dataset)

    assert context["row_count_snapshot"] == 42
    assert context["query_target_decision"]["candidate_index"] == 0
    assert len(context["query_target_candidates"]) == 1
    candidate_selector = context["query_target_candidates"][0]["candidate_selector"]
    assert candidate_selector.startswith("query-target:")
    assert context["profile_summary"]["profile_run_candidates"][0][
        "evidence_iri"
    ] == shared_evidence
    assert context["profile_summary"]["profile_run_candidates"][0][
        "returned_profile_count"
    ] == 2
    assert context["profile_summary"]["profile_run_candidates"][0][
        "dataset_profile_row_count_bases"
    ] == {"42": ["full_scan"]}
    assert context["profile_summary"]["profile_run_candidates"][0][
        "row_count_snapshot_basis"
    ] == "full_scan"
    assert [
        action["tool"].removeprefix("doxabase.") for action in context["suggested_next_actions"]
    ] == [
        "describe_resource",
        "describe_query_context",
    ]
    assert "plan_candidate" in context["suggested_next_actions"][1]["args"]

    profile_action = context["suggested_next_actions"][0]
    assert profile_action["args"] == {
        "iri": dataset,
        "aspect": "profile_run",
        "evidence_iri": shared_evidence,
    }
    profile_run = describe_resource_tool(db, **profile_action["args"])
    assert profile_run["returned_profile_count"] == 2
    assert profile_run["returned_dataset_profile_count"] == 1
    assert profile_run["returned_mapped_column_profile_count"] == 1
    assert profile_run["row_count_snapshot"] == 42
    assert profile_run["dataset_profile_row_counts"] == [42]
    assert profile_run["dataset_profile_row_count_bases"] == {"42": ["full_scan"]}
    assert profile_run["row_count_snapshot_matches"] is True
    assert profile_run["row_count_snapshot_basis"] == "full_scan"

    draft_action = context["suggested_next_actions"][1]
    assert draft_action["args"] == {
        "iri": dataset,
        "plan_candidate": candidate_selector,
    }
    draft = describe_query_context_tool(db, **draft_action["args"])
    assert draft["handoff_kind"] == "metadata_review_required"
    assert draft["source_context"]["selection_mode"] == "candidate_selector"
    assert draft["source_context"]["selected_candidate_index"] == 0
    assert draft["source_context"]["selected_candidate_selector"] == (
        candidate_selector
    )
    assert draft["source_context"]["requested_candidate_selector"] == (
        candidate_selector
    )
    assert draft["handoff_summary"]["selected_candidate_selector"] == (
        candidate_selector
    )
    assert draft["scan"]["uri_template"] == (
        "s3://ais-noaa/broadcasts/{year}/ais-{date}.parquet"
    )


def test_get_context_graph_tool_preserves_profile_routes(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    metric_kind = "https://example.test/project#CompletenessRatio"
    record_map_dataset_tool(db, dataset, label="Orders", is_table=True)
    profile = record_dataset_profile_tool(
        db,
        dataset_iri=dataset,
        summary="Orders were profiled for completeness.",
        evidence_summary="Dataset profile run.",
        evidence_sources=["test://orders-profile"],
        profile_metrics=[
            {"metric": metric_kind, "value": 0.98, "target": dataset},
        ],
        update_map_snapshot=False,
    )

    result = get_context_graph_tool(
        db,
        seed_iris=[metric_kind],
        profile="dataset_brief",
        max_triples=200,
    )

    resource_iris = {resource["iri"] for resource in result["resources"]}
    assert metric_kind in resource_iris
    assert profile["observation"]["observation_iri"] in resource_iris
    assert dataset in resource_iris
    assert dataset in result["trig"]
    assert [
        profile_summary["iri"]
        for profile_summary in result["seed_profile_observations"]
    ] == [profile["observation"]["observation_iri"]]
    seed_profile = result["seed_profile_observations"][0]
    assert seed_profile["profile_metrics"][0]["iri"]
    assert seed_profile["profile_metrics"][0]["metric"]["iri"] == metric_kind
    assert seed_profile["profile_metrics"][0]["target"]["iri"] == dataset
    assert seed_profile["profile_metrics"][0]["value"] == "0.98"
    assert seed_profile["profile_metrics"][0]["value_datatype"].startswith(
        "http://www.w3.org/2001/XMLSchema#"
    )
    assert seed_profile["profile_metrics"][0].get("value_lang") is None
    assert result["route_counts"]["seed_profile_metric_kind"] == 1
    assert result["route_counts"]["profile_metric_observation"] == 1
    legend = {row["route"]: row for row in result["route_legend"]}
    assert legend["profile_metric_observation"]["meaning"].startswith(
        "A profile observation reached from a selected observed profile metric"
    )


def test_record_observation_tool_accepts_profile_type_findings(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    column = "https://example.test/project#OrdersStatus"
    value_type = "https://example.test/project#OrderStatusCode"
    record_map_dataset_tool(db, dataset, label="Orders", is_table=True)
    db.replace_graph_triples(
        graph="ontology",
        additions=f"""
            @prefix rc: <https://richcanopy.org/ns/rc#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            <{value_type}> a rc:ValueType ;
                rdfs:label "Order status code" .
        """,
        allow_count_change=True,
    )

    result = record_observation_tool(
        db,
        summary="MCP helper wrote a profile type finding.",
        observation_type="profile",
        observed_asset=dataset,
        observed_column=column,
        observed_column_name="status",
        observed_physical_type="rc:Integer",
        observed_value_type=value_type,
        evidence_summary="Synthetic profile type evidence.",
        evidence_sources=["tests/test_mcp_tools.py"],
    )

    profile_run = describe_resource_tool(
        db,
        aspect="profile_run",
        iri=dataset,
        evidence_iri=result["evidence_iri"],
    )
    profile = profile_run["unmapped_column_profile_observations"][0]
    assert profile["iri"] == result["observation_iri"]
    assert profile["observed_physical_type"]["iri"] == RC + "Integer"
    assert profile["observed_value_type"]["iri"] == value_type
    assert [
        action["tool"].removeprefix("doxabase.") for action in profile_run["suggested_next_actions"]
    ] == ["stage_revision"]
    assert profile_run["suggested_next_actions"][0]["args"] == {
        "kind": "profile_map_updates",
        "dry_run": True,
        "spec": {
            "dataset_iri": dataset,
            "evidence_iri": result["evidence_iri"],
        },
    }
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_record_dataset_profile_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Messages"
    evidence = "https://example.test/project#messages_profile_evidence"

    result = record_dataset_profile_tool(
        db,
        dataset_iri=dataset,
        summary="MCP helper recorded a profile bundle.",
        evidence_iri=evidence,
        evidence_summary="Synthetic profile evidence.",
        evidence_sources=["tests/test_mcp_tools.py"],
        sample_size=55,
        sample_scope="All rows in the synthetic Messages table.",
        sample_method="DuckDB full-table profile.",
        row_count=55,
        distinct_count=54,
        value_frequencies=[
            {"value": "open", "frequency": 40},
            {"value": "closed", "frequency": 15},
        ],
        profile_metrics=[
            {"metric": "rc:MinimumValue", "value": 3, "target": dataset},
            {"metric": "rc:MaximumValue", "value": 99},
        ],
        map_label="Messages",
        is_table=True,
        pattern_summary="Messages profile looks stable.",
        pattern_text="The profile row count and distinct count nearly match.",
        pattern_rationale=(
            "A linked profile pattern keeps the profile synthesis reviewable."
        ),
    )

    assert result["dataset_iri"] == dataset
    assert result["observation"]["evidence_iri"] == evidence
    assert result["observation"]["observation_type"] == "profile"
    assert result["map_dataset"]["iri"] == dataset
    assert result["pattern"]["pattern_iri"].startswith(
        "https://richcanopy.org/doxabase/generated/pattern/"
    )
    assert describe_dataset_tool(db, dataset)["row_count_snapshot"] == 55
    profile = describe_dataset_tool(db, dataset)["profile_observations"][0]
    assert profile["sample_size"] == 55
    assert profile["sample_scope"] == "All rows in the synthetic Messages table."
    assert profile["sample_method"] == "DuckDB full-table profile."
    assert profile["row_count"] == 55
    assert profile["distinct_count"] == 54
    assert [
        (item["value"], item["frequency"]) for item in profile["value_frequencies"]
    ] == [("open", 40), ("closed", 15)]
    assert {
        (
            item["metric"]["iri"],
            item.get("target", {}).get("iri"),
            item["value"],
            item["value_datatype"],
        )
        for item in profile["profile_metrics"]
    } == {
        (
            "https://richcanopy.org/ns/rc#MinimumValue",
            dataset,
            "3",
            str(XSD.integer),
        ),
        (
            "https://richcanopy.org/ns/rc#MaximumValue",
            None,
            "99",
            str(XSD.integer),
        ),
    }
    assert profile["evidence"][0]["iri"] == evidence
    assert profile["evidence"][0]["sources"] == ["tests/test_mcp_tools.py"]
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_record_column_profile_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Messages"
    column = "https://example.test/project#MessagesDocId"
    record_map_dataset_tool(db, table, label="Messages", is_table=True)

    result = record_column_profile_tool(
        db,
        column_iri=column,
        column_name="doc_id",
        table_iri=table,
        summary="MCP helper recorded a column profile bundle.",
        evidence_summary="Synthetic column profile evidence.",
        evidence_sources=["tests/test_mcp_tools.py"],
        sample_size=55,
        sample_scope="All doc_id values in the synthetic Messages table.",
        sample_method="DuckDB column aggregate query.",
        row_count=55,
        null_count=0,
        distinct_count=55,
        value_frequencies=[
            {"value": "doc-001", "frequency": 1},
            {"value": "doc-002", "frequency": 1},
        ],
        profile_metrics=[
            {"metric": "rc:MeanValue", "value": 12.5},
        ],
        map_label="Messages.doc_id",
        physical_type="rc:Varchar",
        nullable=False,
        pattern_summary="doc_id profile looks complete.",
        pattern_text="The profile found no null doc_id values and all values distinct.",
        pattern_rationale="The profile is a useful identity hunch for later review.",
    )

    assert result["column_iri"] == column
    assert result["table_iri"] == table
    assert result["observation"]["observation_type"] == "profile"
    assert result["map_column"]["iri"] == column
    assert result["pattern"]["pattern_iri"].startswith(
        "https://richcanopy.org/doxabase/generated/pattern/"
    )
    dataset = describe_dataset_tool(db, table)
    assert dataset["columns"][0]["iri"] == column
    assert dataset["columns"][0]["nullable"] is False
    profile = dataset["columns"][0]["profile_observations"][0]
    assert profile["sample_size"] == 55
    assert profile["sample_scope"] == (
        "All doc_id values in the synthetic Messages table."
    )
    assert profile["sample_method"] == "DuckDB column aggregate query."
    assert profile["row_count"] == 55
    assert profile["null_count"] == 0
    assert profile["distinct_count"] == 55
    assert [
        (item["value"], item["frequency"]) for item in profile["value_frequencies"]
    ] == [("doc-001", 1), ("doc-002", 1)]
    assert profile["profile_metrics"][0]["metric"]["iri"] == (
        "https://richcanopy.org/ns/rc#MeanValue"
    )
    assert profile["profile_metrics"][0]["value"] == "12.5"
    assert profile["observed_column"]["iri"] == column
    assert profile["evidence"][0]["sources"] == ["tests/test_mcp_tools.py"]
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_record_profile_bundle_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    shared_evidence = "https://example.test/project#OrdersProfileRunEvidence"

    result = record_profile_bundle_tool(
        db,
        dataset_iri=table,
        dataset_summary="MCP helper recorded a dataset and column profile pass.",
        evidence_summary="Synthetic profile bundle evidence.",
        evidence_sources=["tests/test_mcp_tools.py"],
        sample_size=25,
        sample_scope="Twenty-five sampled Orders rows.",
        sample_method="DuckDB sampled profile query.",
        row_count=1000,
        map_label="Orders",
        is_table=True,
        shared_evidence_iri=shared_evidence,
        pattern_summary="Orders profile bundle supports a run-level synthesis.",
        pattern_text=(
            "The dataset profile and status column profile came from the same "
            "sampled Orders profiling pass."
        ),
        pattern_rationale="Both returned profile observations link to shared evidence.",
        pattern_support_scope="all_profiles",
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Sampled status values were profiled.",
                "distinct_count": 3,
                "value_frequencies": [
                    {"value": "fulfilled", "frequency": 18},
                    {"value": "pending", "frequency": 4},
                ],
            }
        ],
    )

    assert result["dataset_iri"] == table
    assert result["shared_evidence_iri"] == shared_evidence
    assert result["dataset_profile"]["observation"]["observation_type"] == "profile"
    assert result["dataset_profile"]["map_dataset"]["iri"] == table
    assert result["dataset_profile"]["pattern"]["pattern_iri"].startswith(
        "https://richcanopy.org/doxabase/generated/pattern/"
    )
    assert len(result["column_profiles"]) == 1
    assert result["column_profiles"][0]["column_iri"] == status_column
    assert result["column_profiles"][0].get("map_column") is None
    assert result["dataset_profile"]["observation"]["evidence_iri"] == shared_evidence
    assert result["column_profiles"][0]["observation"]["evidence_iri"] == shared_evidence
    assert result["handoff_entrypoints"]["dataset_iri"] == table
    assert result["handoff_entrypoints"]["shared_evidence_iri"] == shared_evidence
    assert result["handoff_entrypoints"]["dataset_describe_available"] is True
    assert result["handoff_entrypoints"]["profile_run_available"] is True
    assert result["handoff_entrypoints"]["profile_observation_iris"] == [
        result["dataset_profile"]["observation"]["observation_iri"],
        result["column_profiles"][0]["observation"]["observation_iri"],
    ]
    assert [
        action["tool"].removeprefix("doxabase.")
        for action in result["handoff_entrypoints"]["suggested_next_actions"]
    ] == [
        "describe_dataset",
        "describe_resource",
        "stage_revision",
        "get_context_graph",
        "get_context_graph",
    ]
    assert result["handoff_entrypoints"]["suggested_next_actions"][1][
        "args"
    ] == {
        "iri": table,
        "aspect": "profile_run",
        "evidence_iri": shared_evidence,
    }
    assert result["handoff_entrypoints"]["suggested_next_actions"][2][
        "args"
    ] == {
        "kind": "profile_map_updates",
        "dry_run": True,
        "spec": {
            "dataset_iri": table,
            "evidence_iri": shared_evidence,
        },
    }
    assert result["handoff_entrypoints"]["suggested_next_actions"][-1][
        "args"
    ] == {
        "seed_iris": result["handoff_entrypoints"]["profile_observation_iris"],
        "profile": "dataset_brief",
    }

    dataset = describe_dataset_tool(db, table)

    assert dataset.get("row_count_snapshot") is None
    assert dataset.get("columns", []) == []
    assert dataset["profile_summary"]["returned_dataset_profile_count"] == 1
    assert dataset["profile_summary"]["returned_mapped_column_profile_count"] == 0
    assert dataset["profile_summary"]["returned_unmapped_column_profile_count"] == 1
    assert dataset["profile_summary"]["returned_profile_count"] == 2
    assert dataset["profile_summary"]["total_profile_count"] == 2
    assert dataset["profile_summary"]["omitted_profile_count"] == 0
    assert dataset["profile_summary"]["mapped_profiled_column_count"] == 0
    assert dataset["profile_summary"]["evidence_iris"] == [shared_evidence]
    assert dataset["profile_summary"]["evidence_profile_counts"] == {
        shared_evidence: 2,
    }
    assert dataset["profile_summary"]["shared_evidence_iris"] == [shared_evidence]
    assert dataset["profile_summary"]["profile_run_candidates"] == [
        {
            "evidence_iri": shared_evidence,
            "returned_profile_count": 2,
            "profile_observation_iris": [
                result["dataset_profile"]["observation"]["observation_iri"],
                result["column_profiles"][0]["observation"]["observation_iri"],
            ],
            "dataset_profile_row_counts": [1000],
            "dataset_profile_row_count_bases": {"1000": ["sample"]},
            "row_count_snapshot_matches": False,
            "shared_by_all_returned_profiles": True,
        }
    ]
    query_context = describe_query_context_tool(db, table)
    assert query_context.get("row_count_snapshot") is None
    assert query_context["profile_summary"]["evidence_iris"] == [shared_evidence]
    assert query_context["profile_summary"]["profile_run_candidates"] == (
        dataset["profile_summary"]["profile_run_candidates"]
    )
    assert "Profile lore is observed evidence" in (
        query_context["profile_summary"]["handoff_note"]
    )
    assert [
        action["tool"].removeprefix("doxabase.") for action in query_context["suggested_next_actions"]
    ] == [
        "describe_resource",
    ]
    assert query_context["suggested_next_actions"][0]["args"] == {
        "iri": table,
        "aspect": "profile_run",
        "evidence_iri": shared_evidence,
    }
    profile_run = describe_resource_tool(
        db,
        aspect="profile_run",
        iri=table,
        evidence_iri=shared_evidence,
    )
    assert profile_run["returned_profile_count"] == 2
    assert profile_run["total_profile_count"] == 2
    assert profile_run["omitted_profile_count"] == 0
    assert set(profile_run["profile_observation_iris"]) == {
        result["dataset_profile"]["observation"]["observation_iri"],
        result["column_profiles"][0]["observation"]["observation_iri"],
    }
    bundle_pattern = describe_resource_tool(
        db,
        aspect="pattern",
        iri=result["dataset_profile"]["pattern"]["pattern_iri"],
    )
    assert {item["iri"] for item in bundle_pattern["supporting_observations"]} == set(
        profile_run["profile_observation_iris"]
    )
    assert bundle_pattern["evidence"][0]["iri"] == shared_evidence
    pattern = record_pattern_tool(
        db,
        summary="Orders profile bundle supports a cross-profile synthesis.",
        pattern_text=(
            "The dataset profile and status column profile came from the same "
            "sampled Orders profiling pass."
        ),
        rationale="Both returned profile observations link to the same run evidence.",
        pattern_targets=[table, status_column],
        supporting_observations=profile_run["profile_observation_iris"],
        evidence_iri=shared_evidence,
    )
    assert pattern["evidence_iri"] == shared_evidence
    assert describe_resource_tool(
        db, aspect="pattern", iri=pattern["pattern_iri"]
    )["evidence"][0]["iri"] == (
        shared_evidence
    )
    profile = dataset["unmapped_column_profile_observations"][0]
    assert profile["observed_column_name"] == "status"
    assert profile["observed_column"]["column_name"] == "status"
    assert profile["sample_scope"] == "Twenty-five sampled Orders rows."
    assert profile["sample_method"] == "DuckDB sampled profile query."
    assert profile["evidence"][0]["iri"] == shared_evidence
    assert profile["evidence"][0]["sources"] == ["tests/test_mcp_tools.py"]
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_profile_type_review_tool_keeps_direct_map_undefined_value_type_visible(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/profile-direct#Orders"
    amount_column = f"{table}Amount"
    money_value_type = "https://example.test/profile-direct#MoneyAmountValue"
    shared_evidence = f"{table}ProfileEvidence"

    db.record_map_dataset(table, label="Orders", is_table=True)
    record_profile_bundle_tool(
        db,
        dataset_iri=table,
        dataset_summary="Orders were profiled and amount was mapped directly.",
        evidence_summary="Synthetic amount profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=shared_evidence,
        update_map_snapshot=False,
        column_profiles=[
            {
                "column_iri": amount_column,
                "column_name": "amount",
                "summary": "Amount was observed as decimal money.",
                "physical_type": "rc:Decimal",
                "value_type": money_value_type,
                "update_map_column": True,
            }
        ],
    )

    result = draft_profile_map_updates_tool(
        db,
        dataset_iri=table,
        evidence_iri=shared_evidence,
    )

    assert result["recommendation_count"] == 0
    assert result["status"] == "pending profile advisory review"
    assert result["type_advisory_count"] == 1
    assert result["type_advisory_status_counts"] == {
        "type_finding_current_map_undefined_value_type": 1,
    }
    advisory = result["type_advisories"][0]
    assert advisory["observed_value_type"]["iri"] == money_value_type
    assert advisory["current_value_type"]["iri"] == money_value_type
    assert "not defined as rc:ValueType" in advisory["rationale"]
    assert list(result["suggested_next_action_groups"]) == [
        "profile_type_review"
    ]
    assert [
        action["tool"].removeprefix("doxabase.")
        for action in result["suggested_next_action_groups"]["profile_type_review"]
    ] == [
        "get_context_graph",
        "record_pattern",
        "stage_revision",
    ]
    grouped_actions = result["suggested_next_action_groups"]["profile_type_review"]


def test_stage_query_storage_access_repair_tool_accepts_profile_route_sources(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/profile-query-repair-tool#"
    table = f"{base}SupportEvents"
    evidence = f"{base}SupportEventsProfileEvidence"

    db.record_map_dataset(
        table,
        label="Support Events",
        is_table=True,
        row_count_snapshot=3,
        path_templates=["support_events/current.csv"],
    )
    db.record_map_physical_layout(
        f"{base}SupportEventsCsvLayout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
        datasets=[table],
    )
    record_profile_bundle_tool(
        db,
        dataset_iri=table,
        dataset_summary="Support events full profile pass.",
        evidence_summary="Support events profile evidence.",
        evidence_sources=["test://support-events/full"],
        shared_evidence_iri=evidence,
        sample_size=4,
        sample_scope="All rows in the local support events table.",
        sample_method="DuckDB full-table profile.",
        row_count=4,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
    )

    draft = draft_profile_map_updates_tool(db, table, evidence)
    query_source = next(
        source
        for source in db._profile_insight_route_sources(
            db.draft_profile_map_updates(table, evidence)
        )
        if source["review_lane"] == "query_context_review"
    )
    repair = stage_query_storage_access_repair_tool(
        db,
        dataset_iri=table,
        storage_access_iri=f"{base}SupportEventsStorage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(tmp_path / "warehouse"),
        location_kind="directory",
        rationale="Reviewed local storage root for the profile/query interlock.",
        profile_route_sources=[query_source],
    )
    described = describe_staged_revision_tool(
        db,
        repair["revision_iri"],
    )
    assert len(described["profile_route_sources"]) == 1
    stored_source = described["profile_route_sources"][0]
    assert stored_source["review_lane"] == "query_context_review"
    assert stored_source["direct_review_lane"] == "query_context_review"
    assert stored_source["route_group_key"] == query_source["route_group_key"]
    assert stored_source["route_step_key"] == query_source["route_step_key"]

    review = export_profile_insight_review_bundle_tool(
        db,
        dataset_iri=table,
        evidence_iri=evidence,
        path=str(tmp_path / "profile-query-repair-review.md"),
        revision_iris=[repair["revision_iri"]],
    )
    candidate = review["candidates"][0]
    assert candidate["semantic_apply_role"] == "query_context_repair_candidate"
    route_groups = {
        group["review_lane"]: group for group in candidate["profile_route_groups"]
    }
    assert route_groups["query_context_review"]["match_strength"] == (
        "direct_action"
    )
    assert {
        lane["review_lane"] for lane in review["open_profile_review_lanes"]
    }.isdisjoint({"query_context_review"})


def test_describe_dataset_tool_returns_unmapped_column_profiles(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Orders"
    column = "https://example.test/project#OrdersStatus"
    record_map_dataset_tool(db, table, label="Orders", is_table=True)

    result = record_column_profile_tool(
        db,
        column_iri=column,
        column_name="status",
        table_iri=table,
        summary="MCP helper recorded an unmapped sampled column profile.",
        evidence_summary="Synthetic sampled profile evidence.",
        evidence_sources=["tests/test_mcp_tools.py"],
        sample_size=25,
        sample_scope="Twenty-five sampled Orders rows.",
        sample_method="Top-N sampled value-frequency query.",
        null_count=0,
        distinct_count=3,
        value_frequencies=[
            {"value": "fulfilled", "frequency": 18},
            {"value": "pending", "frequency": 4},
        ],
        update_map_column=False,
    )

    dataset = describe_dataset_tool(db, table)

    assert dataset.get("columns", []) == []
    assert dataset.get("profile_observations", []) == []
    assert dataset["profile_summary"]["returned_unmapped_column_profile_count"] == 1
    assert dataset["profile_summary"]["returned_profile_count"] == 1
    profiles = dataset["unmapped_column_profile_observations"]
    assert len(profiles) == 1
    assert profiles[0]["iri"] == result["observation"]["observation_iri"]
    assert profiles[0]["observed_column"]["iri"] == column
    assert profiles[0]["observed_column_name"] == "status"
    assert profiles[0]["observed_column"]["column_name"] == "status"
    assert profiles[0]["sample_method"] == "Top-N sampled value-frequency query."
    assert [
        (item["value"], item["frequency"])
        for item in profiles[0]["value_frequencies"]
    ] == [("fulfilled", 18), ("pending", 4)]
    assert validate_graph_tool(db, scope="all")["conforms"] is True

