"""Split from test_mcp_tools.py (distillation Phase 2); tests verbatim."""

from tests.mcp.support_mcp import *  # noqa: F401,F403


def test_draft_map_assertion_change_tool_returns_json_like_payload_without_write(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)
    before_map_count = db.triple_count("map")
    before_history_count = db.triple_count("history")

    result = draft_map_assertion_change_tool(
        db,
        subject="https://richcanopy.org/example/manifest/polymarket#px_price",
        predicate="rc:physicalType",
        object="rc:Double",
        rationale=(
            "Preview a tempting but unsafe type change before deciding whether "
            "to stage it."
        ),
        change_kind="replace",
    )

    assert result["result_kind"] == "draft_map_assertion_change"
    assert result["change_kind"] == "replace"
    assert result["assertion_present_before"] is False
    assert result["changed_graphs"] == ["map"]
    assert result["validation_conforms"] is True
    assert result["validation_result_count"] == 0
    assert result["assertion_support"]["related_route_summaries"]
    assert result["judgement_panel"]["semantic_risk_level"] == "high"
    assert any(
        impact["impact_type"] == "changed_physical_type"
        for impact in result["impacts"]
    )
    assert [
        action["tool_name"] for action in result["suggested_next_actions"]
    ] == ["describe_assertion_support", "stage_map_assertion_change"]
    assert result["suggested_next_actions"][0]["mcp_tool_name"] == (
        "doxabase.describe_assertion_support"
    )
    assert "high-risk" in result["suggested_next_actions"][0]["reason"]
    assert result["suggested_next_actions"][1]["mcp_tool_name"] == (
        "doxabase.stage_map_assertion_change"
    )
    assert result["stage_arguments"]["summary"] == (
        "Replace map assertion: price physicalType DOUBLE"
    )
    assert db.triple_count("map") == before_map_count
    assert db.triple_count("history") == before_history_count


def test_stage_map_assertion_change_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)
    before_map_count = db.triple_count("map")

    result = stage_map_assertion_change_tool(
        db,
        subject="https://richcanopy.org/example/manifest/polymarket#px_price",
        predicate="rc:physicalType",
        object="rc:Double",
        rationale=(
            "Exercise a tempting but unsafe type change so assertion support "
            "travels with the staged revision."
        ),
        change_kind="replace",
        profile_route_sources=[
            {
                "review_lane": "profile_type_review",
                "route_group_key": "profile_type_review:test-route",
                "route_step_key": "profile-route-step:test-route",
            }
        ],
    )

    assert result["change_kind"] == "replace"
    assert result["profile_route_source_count"] == 1
    assert result["assertion_present_before"] is False
    assert result["assertion_support"]["absence_note"] is not None
    assert "Current same-subject/predicate value(s): VARCHAR" in (
        result["assertion_support"]["absence_note"]
    )
    assert result["assertion_support"]["related_route_summaries"]
    assert result["review_recommendation"].startswith("Review assertion support")
    panel = result["judgement_panel"]
    assert panel["proposed_value"]["label"] == "DOUBLE"
    assert [value["label"] for value in panel["current_values"]] == ["VARCHAR"]
    assert panel["semantic_risk_level"] == "high"
    assert panel["semantic_risk_reasons"]
    assert panel["value_type_context"][0]["value_type"]["label"] == (
        "Raw CLOB Price Payload"
    )
    assert panel["value_type_context"][0]["current_physical_type_matches"] is True
    assert panel["value_type_context"][0]["proposed_physical_type_matches"] is False
    assert panel["caveats"]
    assert any(
        impact["impact_type"] == "changed_physical_type"
        for impact in panel["impacts"]
    )
    assert len(result["additions"]) == 1
    assert len(result["removals"]) == 1
    assert result["staged_revision"]["summary"] == (
        "Replace map assertion: price physicalType DOUBLE"
    )
    assert result["staged_revision"]["rationale"].startswith(
        "Exercise a tempting but unsafe type change"
    )
    assert (
        "Staged map assertion change kind: replace."
        in result["staged_revision"]["review_note"]
    )
    assert (
        "Current same-subject/predicate value(s): VARCHAR"
        in result["staged_revision"]["review_note"]
    )
    assert result["staged_revision"]["review_recommendation"].startswith(
        "Review assertion support"
    )
    assert result["staged_revision"]["changed_graphs"] == ["map"]
    assert result["staged_revision"]["validation_conforms"] is True
    assert result["revision_iri"] == result["staged_revision"]["revision_iri"]
    assert db.triple_count("map") == before_map_count

    description = describe_staged_revision_tool(
        db,
        result["staged_revision"]["revision_iri"],
    )
    assert description["judgement_panel"]["proposed_value"]["label"] == "DOUBLE"
    assert description.get("stored_review_context") is None
    assert description["judgement_panel"]["semantic_risk_level"] == "high"
    assert description["supporting_patterns"]
    assert "https://richcanopy.org/ns/rc#Varchar" not in {
        anchor["iri"] for anchor in description["revision_anchors"]
    }
    assert "https://richcanopy.org/ns/rc#Double" not in {
        anchor["iri"] for anchor in description["revision_anchors"]
    }
    assert any(
        impact["impact_type"] == "changed_physical_type"
        for impact in description["impacts"]
    )
    check = check_staged_revision_apply_tool(
        db,
        result["staged_revision"]["revision_iri"],
    )
    assert check["can_apply"] is True
    assert check["status"] == "ready"
    assert check["semantic_risk_level"] == "high"
    assert check["semantic_risk_reasons"]
    assert check["suggested_next_actions"][-1]["tool_name"] == (
        "apply_staged_revision"
    )
    assert check["suggested_next_actions"][-1]["action_label"] == (
        "Apply only after semantic review"
    )

    ais_result = stage_map_assertion_change_tool(
        db,
        subject="https://richcanopy.org/example/manifest/ais#bc_base_date_time",
        predicate="rc:physicalType",
        object="rc:TimestampTZ",
        rationale=(
            "Exercise a second tempting type cleanup after the Polymarket stage."
        ),
        change_kind="replace",
    )
    ais_panel = ais_result["judgement_panel"]
    assert ais_panel["value_type_context"]
    assert ais_panel["value_type_context"][0]["value_type"]["label"] == (
        "Raw AIS Timestamp String"
    )
    assert ais_panel["value_type_context"][0]["required_physical_type"]["label"] == (
        "VARCHAR"
    )
    assert ais_panel["value_type_context"][0]["current_physical_type_matches"] is True
    assert (
        ais_panel["value_type_context"][0]["proposed_physical_type_matches"] is False
    )
    assert any(
        "Raw AIS Timestamp String requires physical type VARCHAR" in note
        for note in ais_panel["why_current_value_may_be_intentional"]
    )
    assert result["staged_revision"]["revision_iri"] not in {
        route["resource_iri"] for route in ais_panel.get("strongest_routes", [])
    }
    ais_description = describe_staged_revision_tool(
        db,
        ais_result["staged_revision"]["revision_iri"],
    )
    assert ais_description["judgement_panel"]["value_type_context"][0][
        "value_type"
    ]["label"] == "Raw AIS Timestamp String"
    assert ais_description["judgement_panel"].get("strongest_routes", []) == []
    ais_export_path = tmp_path / "ais-judgement-review.md"
    export_staged_revision_tool(
        db,
        iri=ais_result["staged_revision"]["revision_iri"],
        path=str(ais_export_path),
    )
    ais_export = ais_export_path.read_text()
    assert "## Judgement Panel" in ais_export
    assert "### Value Type Context" in ais_export
    assert "Raw AIS Timestamp String" in ais_export
    assert "TIMESTAMP WITH TIME ZONE" in ais_export
    assert "| Value type | Required physical type | Current matches |" in ais_export
    assert "No strong related-lore routes surfaced" in ais_export
    assert db.triple_count("map") == before_map_count

    record_map_dataset_tool(
        db,
        "https://richcanopy.org/example/manifest/polymarket#scratch_drift",
        label="Scratch drift",
        is_table=True,
    )
    stale_description = describe_staged_revision_tool(
        db,
        result["staged_revision"]["revision_iri"],
        include_current_apply_check=True,
    )
    assert stale_description.get("judgement_panel") is None
    assert stale_description["stored_review_context"]["semantic_risk_level"] == "high"
    assert stale_description["stored_review_context"]["review_note_signals"][
        "has_value_type_context"
    ] is True
    assert stale_description["stored_review_context"]["linked_support_counts"][
        "patterns"
    ] >= 1
    assert stale_description["stored_review_context"]["attention_impacts"][0][
        "impact_type"
    ] == "changed_physical_type"


def test_analysis_view_tools_return_logical_context(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/mcp-analysis-view#"
    source = f"{base}messages"
    view = f"{base}sent_external_messages"
    caveat = f"{base}redacted_body_caveat"

    record_map_dataset_tool(db, iri=source, label="Messages", is_table=True)
    record_map_caveat_tool(
        db,
        iri=caveat,
        label="Redacted body caveat",
        description="Message bodies may be redacted in the source export.",
        severity="rc:Moderate",
    )
    record_result = record_map_analysis_view_tool(
        db,
        iri=view,
        label="Sent external messages",
        source_datasets=[source],
        row_count_snapshot=42,
        caveats=[caveat],
        denominator_description="One row per sent message with an external recipient.",
        denominator_row_count_snapshot=42,
        denominator_basis="direction = sent and recipient domain is external",
        query_text="select * from messages where direction = 'sent'",
        query_language="DuckDB SQL",
        query_engine="duckdb",
    )

    assert record_result["resource_type"] == RC + "AnalysisView"
    description = describe_analysis_view_tool(db, iri=view)
    assert description["label"] == "Sent external messages"
    assert description["source_datasets"][0]["iri"] == source
    assert description["denominator"]["row_count_snapshot"] == 42
    assert description["denominator"]["basis"] == (
        "direction = sent and recipient domain is external"
    )
    assert description["query_snippets"][0]["query_language"] == "DuckDB SQL"
    assert description["query_snippets"][0]["query_engine"] == "duckdb"
    assert description["caveats"][0]["iri"] == caveat
    assert description["suggested_next_actions"][0]["tool_name"] == (
        "describe_query_context"
    )

    context = describe_query_context_tool(db, iri=view)
    assert context["readiness"] == "logical_analysis_view"
    assert context["issues"][0]["code"] == "logical_analysis_view_not_physical_route"
    assert context["suggested_repair_action_group_count"] == 0
    assert context.get("query_target_candidates", []) == []
    assert context["query_target_decision"]["status"] == "logical_analysis_view"
    assert context["suggested_next_actions"][0]["tool_name"] == "describe_analysis_view"


def test_analysis_view_tool_accepts_multiple_query_snippets(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/mcp-analysis-view#"
    source = f"{base}messages"
    view = f"{base}message_like_rows"

    record_map_dataset_tool(db, iri=source, label="Messages", is_table=True)
    result = record_map_analysis_view_tool(
        db,
        iri=view,
        label="Message-like rows",
        source_datasets=[source],
        query_snippets=[
            {
                "label": "DuckDB view definition",
                "query_text": "select * from messages where folder <> 'calendar'",
                "query_language": "DuckDB SQL",
                "query_engine": "duckdb",
            },
            {
                "iri": f"{view}/query-snippet/count-check",
                "label": "Count check",
                "query_text": "select count(*) from message_like_rows",
                "query_language": "DuckDB SQL",
                "query_engine": "duckdb",
            },
        ],
    )

    assert result["resource_type"] == RC + "AnalysisView"
    description = describe_analysis_view_tool(db, iri=view)
    assert [snippet["label"] for snippet in description["query_snippets"]] == [
        "DuckDB view definition",
        "Count check",
    ]
    assert description["query_snippets"][1]["iri"] == (
        f"{view}/query-snippet/count-check"
    )
    assert (
        describe_query_context_tool(db, iri=view)["readiness"]
        == "logical_analysis_view"
    )


def test_analysis_view_bundle_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/mcp-analysis-view-bundle#"
    source = f"{base}messages"
    plausible_view = f"{base}plausible_messages"
    message_like_view = f"{base}message_like_rows"

    record_map_dataset_tool(db, iri=source, label="Messages", is_table=True)
    result = record_map_analysis_view_bundle_tool(
        db,
        views=[
            {
                "iri": plausible_view,
                "label": "Plausible messages",
                "source_datasets": [source],
                "row_count_snapshot": 120,
                "denominator_description": "Messages dated inside the reviewed window.",
                "query_snippets": [
                    {
                        "label": "View definition",
                        "query_text": (
                            "create view plausible_messages as "
                            "select * from messages where date_sent is not null"
                        ),
                        "query_language": "DuckDB SQL",
                        "query_engine": "duckdb",
                    }
                ],
            },
            {
                "iri": message_like_view,
                "label": "Message-like rows",
                "source_datasets": [source],
                "query_snippets": [
                    {
                        "label": "View definition",
                        "query_text": (
                            "create view message_like_rows as "
                            "select * from plausible_messages "
                            "where folder_family <> 'calendar'"
                        ),
                        "query_language": "DuckDB SQL",
                        "query_engine": "duckdb",
                    }
                ],
            },
        ],
    )

    assert result["view_count"] == 2
    assert result["view_iris"] == [plausible_view, message_like_view]
    assert result["query_snippet_count"] == 2
    assert result["analysis_views"][0]["query_snippets"][0]["query_engine"] == "duckdb"
    assert [action["tool_name"] for action in result["suggested_next_actions"]] == [
        "describe_query_context",
        "describe_query_context",
    ]
    assert (
        describe_query_context_tool(db, iri=message_like_view)["readiness"]
        == "logical_analysis_view"
    )


def test_record_analysis_packet_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/mcp-analysis-packet#"
    source = f"{base}messages"
    packet = f"{base}packet"
    view = f"{base}message_like_rows"
    artifact = f"{base}lane_chart"
    recipe = f"{base}attachment_join_recipe"

    record_map_dataset_tool(db, iri=source, label="Messages", is_table=True)
    result = record_analysis_packet_tool(
        db,
        iri=packet,
        label="Message-like analysis packet",
        summary="Reviewed packet with logical view and chart locator.",
        analysis_views=[
            {
                "iri": view,
                "label": "Message-like rows",
                "source_datasets": [source],
                "row_count_snapshot": 98,
            }
        ],
        artifacts=[
            {
                "iri": artifact,
                "source_path": "scratch://visuals/message_like_rows.png",
                "artifact_role": "visualization",
                "media_type": "image/png",
                "image_width": 900,
                "image_height": 600,
                "supports": [view],
            }
        ],
        query_recipes=[
            {
                "iri": recipe,
                "label": "Join attachments by parent document",
                "description": "Reusable cookbook query for message attachment joins.",
                "query_text": (
                    "select * from eml_messages m "
                    "left join eml_attachments a on a.parent_doc_id = m.doc_id"
                ),
                "query_language": "DuckDB SQL",
                "query_engine": "duckdb",
                "targets": [view],
            }
        ],
        followup_tasks=[
            {
                "task_text": "Inspect the top week in the message-like lane.",
                "targets": [view],
            }
        ],
    )

    assert result["packet_iri"] == packet
    assert result["evidence_iri"] == packet
    assert result["analysis_view_iris"] == [view]
    assert result["artifact_iris"] == [artifact]
    assert result["query_recipe_iris"] == [recipe]
    assert result["query_recipe_records"][0]["iri"] == recipe
    assert len(result["followup_task_iris"]) == 1
    assert result["analysis_view_bundle"]["view_count"] == 1
    assert result["suggested_next_actions"][0]["tool_name"] == (
        "get_context_graph"
    )
    assert (
        describe_query_context_tool(db, iri=view)["readiness"]
        == "logical_analysis_view"
    )
    context = get_context_graph_tool(
        db,
        seed_iris=[packet],
        profile="resource_brief",
    )
    assert recipe in {resource["iri"] for resource in context["resources"]}
    analysis_view_actions = [
        action
        for action in context["suggested_next_actions"]
        if action["tool_name"] == "describe_analysis_view"
    ]
    assert [action["arguments"]["iri"] for action in analysis_view_actions] == [
        view
    ]
    assert "parent_doc_id" in json.dumps(context)
    export_path = tmp_path / "analysis-packet-slice.trig"
    export = export_context_slice_tool(
        db,
        path=str(export_path),
        seed_iris=[packet],
        profile="resource_brief",
        fail_on_sensitive=True,
    )
    receiver = DoxaBase.create(tmp_path / "receiver.sqlite")
    imported = import_trig_tool(receiver, path=str(export_path))
    assert imported["total_imported"] == export["triples"]
    assert validate_graph_tool(receiver, scope="all")["conforms"] is True
    assert db.validate_graph(scope="all").conforms


def test_record_map_table_bundle_tool_returns_json_like_records(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/mcp-table-bundle#"
    table = f"{base}orders"

    result = record_map_table_bundle_tool(
        db,
        iri=table,
        label="Orders",
        columns=[
            {
                "column_name": "order_id",
                "physical_type": "rc:Varchar",
                "nullable": False,
            },
            {
                "column_name": "status",
                "physical_type": "rc:Varchar",
            },
        ],
        row_count_snapshot=12,
        schema_stability="rc:FixedSchema",
        storage_access_iri=f"{base}orders_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        location_kind="object",
        storage_root=str(tmp_path / "orders.parquet"),
        physical_layout_iri=f"{base}orders_layout",
        file_format="rc:Parquet",
        compression_codec="rc:ZstdCompression",
    )

    assert result["dataset"]["resource_type"] == RC + "Table"
    assert result["storage_access"]["iri"] == f"{base}orders_storage"
    assert result["physical_layout"]["iri"] == f"{base}orders_layout"
    assert result["column_iris"] == [
        f"{table}__order_id",
        f"{table}__status",
    ]
    assert [record["resource_type"] for record in result["columns"]] == [
        RC + "Column",
        RC + "Column",
    ]
    assert result["suggested_next_actions"][0]["tool_name"] == "describe_dataset"

    description = describe_dataset_tool(db, iri=table)
    assert description["row_count_snapshot"] == 12
    assert {column["column_name"] for column in description["columns"]} == {
        "order_id",
        "status",
    }
    assert description["physical_layouts"][0]["file_format"]["iri"] == RC + "Parquet"


def test_record_map_relationship_tool_accepts_asset_level_endpoints(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/mcp-assets#"
    raw = f"{base}raw_packets"
    correction = f"{base}navigation_corrections"
    mosaic = f"{base}survey_mosaic"

    record_map_dataset_tool(db, iri=raw, label="Raw packets")
    record_map_dataset_tool(db, iri=correction, label="Navigation corrections")
    record_map_dataset_tool(db, iri=mosaic, label="Survey mosaic")
    result = record_map_relationship_tool(
        db,
        iri=f"{base}mosaic_derivation",
        relationship_type="derivation",
        label="mosaic derivation",
        source_endpoints=[
            {
                "dataset": raw,
                "role": "primary packet input",
                "order": 1,
            },
            {
                "dataset": correction,
                "role": "navigation correction input",
                "order": 2,
            },
        ],
        target_datasets=[mosaic],
    )

    assert result["resource_type"] == RC + "Derivation"
    description = describe_dataset_tool(db, iri=mosaic)
    relationship = description["relationships"][0]
    assert [dataset["iri"] for dataset in relationship["source_datasets"]] == [
        raw,
        correction,
    ]
    assert [
        (endpoint["dataset"]["iri"], endpoint["role"], endpoint["order"])
        for endpoint in relationship["source_endpoints"]
    ] == [
        (raw, "primary packet input", 1),
        (correction, "navigation correction input", 2),
    ]
    assert [dataset["iri"] for dataset in relationship["target_datasets"]] == [
        mosaic
    ]
    assert any(
        related["relationship"] == "derived_from"
        and related["relationship_kind"] == RC + "Derivation"
        for related in description["related_datasets"]
    )
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_record_map_asset_transform_tool_serializes_transform_details(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/mcp-transform#"
    raw = f"{base}raw_packets"
    correction = f"{base}navigation_corrections"
    mosaic = f"{base}survey_mosaic"
    condition = f"{base}valid_navigation_filter"

    record_map_dataset_tool(db, iri=raw, label="Raw packets")
    record_map_dataset_tool(db, iri=correction, label="Navigation corrections")
    record_map_dataset_tool(db, iri=mosaic, label="Survey mosaic")
    result = record_map_asset_transform_tool(
        db,
        iri=f"{base}mosaic_derivation",
        relationship_type="derivation",
        label="mosaic derivation",
        source_endpoints=[
            {
                "dataset": raw,
                "role": "primary packet input",
                "order": 1,
            },
            {
                "dataset": correction,
                "role": "navigation correction input",
                "order": 2,
            },
        ],
        target_datasets=[mosaic],
        conditions=[
            {
                "iri": condition,
                "condition_kind": "rc:FilterCondition",
                "expression": "valid navigation fixes only",
            }
        ],
        outputs=[
            {
                "target_dataset": mosaic,
                "formula": "apply navigation corrections and rasterize packets",
                "conditions": [condition],
                "tuple_grain": {
                    "components": [
                        {"dataset": raw, "role": "source survey"},
                        {"expression": "tile coordinate", "role": "tile"},
                    ]
                },
            }
        ],
    )

    assert result["resource_type"] == RC + "Derivation"
    description = describe_dataset_tool(db, iri=mosaic)
    assert len(description["tuple_grains"]) == 1
    relationship = description["relationships"][0]
    assert relationship["transform_conditions"][0]["expression"] == (
        "valid navigation fixes only"
    )
    output = relationship["transform_outputs"][0]
    assert output["target_dataset"]["iri"] == mosaic
    assert output["formula"] == "apply navigation corrections and rasterize packets"
    assert output["conditions"][0]["iri"] == condition
    assert output["tuple_grain"]["components"][0]["dataset"]["iri"] == raw
    assert output["tuple_grain"]["components"][1]["expression"] == "tile coordinate"
    assert validate_graph_tool(db, scope="all")["conforms"] is True

