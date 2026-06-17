from pathlib import Path

import pytest
from rdflib.namespace import XSD

import doxabase.mcp_tools as mcp_tools
from doxabase import DoxaBase
from doxabase.mcp_server import build_server
from doxabase.mcp_tools import (
    apply_staged_revision_tool,
    check_staged_revision_apply_tool,
    describe_assertion_support_tool,
    describe_context_slice_tool,
    describe_dataset_tool,
    describe_graph_revision_tool,
    describe_pattern_tool,
    describe_query_context_tool,
    describe_resource_tool,
    describe_staged_revision_tool,
    export_graph_tool,
    export_staged_revision_tool,
    export_staged_revisions_tool,
    export_trig_tool,
    graph_overview_tool,
    list_docs_tool,
    list_entities_tool,
    list_graph_revisions_tool,
    load_example_fixtures_tool,
    record_claim_observation_tool,
    record_claim_reconsideration_tool,
    record_column_profile_tool,
    record_dataset_profile_tool,
    record_map_caveat_tool,
    record_map_column_tool,
    record_map_dataset_tool,
    record_map_partition_scheme_tool,
    record_map_physical_layout_tool,
    record_map_relationship_tool,
    record_map_storage_access_tool,
    record_graph_revision_tool,
    record_observation_tool,
    record_pattern_tool,
    record_profile_bundle_tool,
    restage_staged_revision_tool,
    search_tool,
    stage_graph_revision_tool,
    stage_map_assertion_change_tool,
    stage_pattern_promotion_tool,
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
    assert "doxabase.describe_query_context" in tool_names
    assert "doxabase.describe_context_slice" in tool_names
    assert "doxabase.describe_resource" in tool_names
    assert "doxabase.describe_graph_revision" in tool_names
    assert "doxabase.list_graph_revisions" in tool_names
    assert "doxabase.describe_staged_revision" in tool_names
    assert "doxabase.check_staged_revision_apply" in tool_names
    assert "doxabase.describe_pattern" in tool_names
    assert "doxabase.record_observation" in tool_names
    assert "doxabase.record_claim_observation" in tool_names
    assert "doxabase.record_claim_reconsideration" in tool_names
    assert "doxabase.record_column_profile" in tool_names
    assert "doxabase.record_dataset_profile" in tool_names
    assert "doxabase.record_profile_bundle" in tool_names
    assert "doxabase.record_pattern" in tool_names
    assert "doxabase.record_map_dataset" in tool_names
    assert "doxabase.record_map_column" in tool_names
    assert "doxabase.record_map_caveat" in tool_names
    assert "doxabase.record_map_storage_access" in tool_names
    assert "doxabase.record_map_physical_layout" in tool_names
    assert "doxabase.record_map_partition_scheme" in tool_names
    assert "doxabase.record_map_relationship" in tool_names
    assert "doxabase.search" in tool_names
    assert "doxabase.export_graph" in tool_names
    assert "doxabase.export_staged_revision" in tool_names
    assert "doxabase.export_staged_revisions" in tool_names
    assert "doxabase.export_trig" in tool_names
    assert "doxabase.record_graph_revision" in tool_names
    assert "doxabase.stage_graph_revision" in tool_names
    assert "doxabase.restage_staged_revision" in tool_names
    assert "doxabase.stage_map_assertion_change" in tool_names
    assert "doxabase.stage_systematisation" in tool_names
    assert "doxabase.stage_pattern_promotion" in tool_names
    assert "doxabase.apply_staged_revision" in tool_names
    assert "doxabase.load_example_fixtures" in tool_names
    assert "doxabase.validate_graph" in tool_names


def test_doc_tools_return_json_like_payloads() -> None:
    result = list_docs_tool()
    doc_ids = {doc["id"] for doc in result["docs"]}

    assert result["docs"][0]["id"] == "start_here"
    assert "start_here" in doc_ids
    assert "overview" in doc_ids
    assert "graph_roles" in doc_ids
    assert "response_shapes" in doc_ids


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
    assert token_support["related_route_summaries"] == []
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
    assert description["graph_snapshots"][0]["content_digest"].startswith("sha256:")
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


def test_restage_staged_revision_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = stage_graph_revision_tool(
        db,
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
    stale_check = check_staged_revision_apply_tool(db, iri=staged["revision_iri"])
    assert stale_check["status"] == "conflict"
    assert stale_check["validation_skipped_reason"] == "conflicts_present"
    assert stale_check["count_drifts"][0]["target_graph"] == "map"
    assert stale_check["count_drifts"][0]["delta"] == db.triple_count("map")
    assert stale_check["count_drifts"][0]["exact_changed_triples_available"] is True
    assert stale_check["count_drifts"][0]["patch_triples_checked"] == 1
    assert stale_check["count_drifts"][0]["patch_triples_currently_present"] == 0
    assert stale_check["count_drifts"][0]["patch_triples_currently_absent"] == 1
    assert stale_check["count_drifts"][0]["patch_triple_status"] == (
        "all_patch_triples_absent"
    )
    assert stale_check["snapshot_drifts"][0]["graph_role"] == "map"
    assert stale_check["snapshot_drifts"][0]["snapshot_content_digest"].startswith(
        "sha256:"
    )
    assert stale_check["snapshot_drifts"][0]["current_content_digest"].startswith(
        "sha256:"
    )
    assert stale_check["snapshot_drifts"][0]["exact_changed_triples_available"] is True
    assert stale_check["snapshot_drifts"][0]["triples_added_since_snapshot"]
    assert stale_check["snapshot_drifts"][0]["triples_removed_since_snapshot"] == []
    added_drift_triple = stale_check["snapshot_drifts"][0][
        "triples_added_since_snapshot"
    ][0]
    assert "subject_display" in added_drift_triple
    assert "predicate_display" in added_drift_triple
    assert "object_display" in added_drift_triple
    assert stale_check["suggested_next_actions"][0]["tool_name"] == (
        "describe_staged_revision"
    )
    assert stale_check["suggested_next_actions"][-1]["tool_name"] == (
        "restage_staged_revision"
    )

    restaged = restage_staged_revision_tool(db, iri=staged["revision_iri"])

    assert restaged["revision_iri"] != staged["revision_iri"]
    assert restaged["patches"][0]["before_triple_count"] == db.triple_count("map")
    description = describe_staged_revision_tool(db, restaged["revision_iri"])
    assert description["restaged_from"]["iri"] == staged["revision_iri"]
    assert check_staged_revision_apply_tool(
        db,
        iri=restaged["revision_iri"],
    )["status"] == "ready"


def test_export_staged_revisions_tool_resolves_relative_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mcp_tools, "ROOT", tmp_path)
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = stage_graph_revision_tool(
        db,
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

    export = export_staged_revisions_tool(
        db,
        revision_iris=[staged["revision_iri"]],
        path="nested/../bundle.md",
        title="Relative bundle",
    )

    expected_path = (tmp_path / "bundle.md").resolve()
    assert export["path"] == str(expected_path)
    assert expected_path.exists()
    assert expected_path.read_text(encoding="utf-8").startswith("# Relative bundle\n")


def test_list_graph_revisions_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = stage_graph_revision_tool(
        db,
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
    result = list_graph_revisions_tool(
        db,
        revision_type="rc:StagedRevision",
        include_apply_checks=True,
    )

    assert result["count"] == 1
    assert result["include_apply_checks"] is True
    assert result["drift_detail"] == "summary"
    assert result["revision_type"] == "https://richcanopy.org/ns/rc#StagedRevision"
    assert result["revisions"][0]["iri"] == staged["revision_iri"]
    assert result["revisions"][0]["record_kind"] == "staged_patch"
    assert result["revisions"][0]["has_patch_payload"] is True
    assert result["revisions"][0]["patch_count"] == 1
    assert result["revisions"][0]["application_status"] == "ready"
    assert result["revisions"][0]["application_decision"] == "review_then_apply"
    assert result["revisions"][0]["application_can_apply"] is True
    assert result["revisions"][0]["suggested_next_actions"]


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
    )

    assert result["change_kind"] == "replace"
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
    assert result["staged_revision"]["changed_graphs"] == ["map"]
    assert result["staged_revision"]["validation_conforms"] is True
    assert db.triple_count("map") == before_map_count

    description = describe_staged_revision_tool(
        db,
        result["staged_revision"]["revision_iri"],
    )
    assert description["judgement_panel"]["proposed_value"]["label"] == "DOUBLE"
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
        route["resource_iri"] for route in ais_panel["strongest_routes"]
    }
    ais_description = describe_staged_revision_tool(
        db,
        ais_result["staged_revision"]["revision_iri"],
    )
    assert ais_description["judgement_panel"]["value_type_context"][0][
        "value_type"
    ]["label"] == "Raw AIS Timestamp String"
    assert ais_description["judgement_panel"]["strongest_routes"] == []
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


def test_apply_staged_revision_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = stage_graph_revision_tool(
        db,
        summary="Stage messages table",
        rationale="Messages should become durable map context after review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Messages a rc:Dataset, rc:Table ;
                        rdfs:label "Messages" .
                """,
            }
        ],
    )

    check = check_staged_revision_apply_tool(db, iri=staged["revision_iri"])
    assert check["can_apply"] is True
    assert check["status"] == "ready"
    assert check["decision"] == "review_then_apply"
    assert check["review_recommended"] is True
    assert check["blocking_reasons"] == []
    assert check["validation_skipped_reason"] is None
    assert "proposal is still desired" in check["recommended_resolution"]
    assert check["summary"] == (
        "Ready to apply 1 patch(es) across map: +3 triple(s), -0 triple(s)."
    )
    assert check["conflicts"] == []
    assert check["patch_checks"][0]["preview_triple_count"] == 3
    assert check["suggested_next_actions"][0]["tool_name"] == (
        "describe_staged_revision"
    )
    assert check["suggested_next_calls"][0].startswith("describe_staged_revision(")
    assert check["suggested_next_actions"][-1]["tool_name"] == (
        "apply_staged_revision"
    )

    result = apply_staged_revision_tool(db, iri=staged["revision_iri"])

    assert result["staged_revision_iri"] == staged["revision_iri"]
    assert result["changed_graphs"] == ["map"]
    assert result["patches_applied"] == 1
    assert result["triples_added"] == 3
    assert result["validation_conforms"] is True
    description = describe_graph_revision_tool(db, result["applied_revision_iri"])
    assert description["revision_type_label"] == "applied staged revision"
    assert describe_dataset_tool(
        db,
        "https://example.test/project#Messages",
    )["label"] == "Messages"


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
                "review_note": "The pattern framing keeps the idea tentative.",
                "review_recommendation": "Preferred until the map vocabulary settles.",
            },
            {
                "label": "Map candidate",
                "graph": "map",
                "content": map_framing,
                "stance": "rc:CandidateRevision",
                "reviewNote": "This is reviewable but slightly too early.",
                "reviewRecommendation": "Keep as a concrete alternative.",
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
    assert result["framings"][0]["review_note"] == (
        "The pattern framing keeps the idea tentative."
    )
    assert result["framings"][1]["review_recommendation"] == (
        "Keep as a concrete alternative."
    )

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

    export_path = tmp_path / "identity-ladder-review.md"
    export = export_staged_revisions_tool(
        db,
        revision_iris=[
            revision["revision_iri"] for revision in result["staged_revisions"]
        ],
        path=str(export_path),
        title="Identity ladder MCP bundle",
        executive_summary="Pattern-first is preferred, but both framings remain useful.",
    )
    exported = export_path.read_text(encoding="utf-8")
    assert export["revision_iris"] == [
        revision["revision_iri"] for revision in result["staged_revisions"]
    ]
    assert exported.startswith("# Identity ladder MCP bundle\n")
    assert "## Review Summary" in exported
    assert "Pattern-first is preferred" in exported
    assert "Preferred until the map vocabulary settles." in exported
    assert "The pattern framing keeps the idea tentative." in exported
    assert "## Summary" in exported
    assert "Pattern first" in exported
    assert "Map candidate" in exported


def test_stage_pattern_promotion_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    target = "https://example.test/project#messages__body_top"
    implication = "https://example.test/project#body_top_lossy_caveat"
    observation = db.record_observation(
        "body_top behaves like cleaned top-level message text.",
        observed_column=target,
        evidence_sources=["test://body-top-profile"],
    )
    pattern = db.record_pattern(
        summary="body_top is cleaned message text.",
        pattern_text="Source notes and checks support body_top as cleaned sender-new text.",
        rationale="The claim is durable enough to stage as a map caveat.",
        pattern_targets=[target],
        supporting_observations=[observation.observation_iri],
        evidence_sources=["test://body-top-pattern"],
        map_implications=[implication],
    )

    result = stage_pattern_promotion_tool(
        db,
        patterns=[pattern.pattern_iri],
        summary="Promote body_top caveat",
        framings=[
            {
                "label": "Map caveat",
                "graph": "map",
                "content": f"""
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:body_top_lossy_caveat a rc:KnownCaveat ;
                        rdfs:label "body_top lossy caveat" ;
                        rc:caveatDescription "body_top is cleaned text, not a byte-exact source body." .

                    <{target}> rc:hasKnownCaveat ex:body_top_lossy_caveat .
                """,
            }
        ],
    )

    assert result["summary"] == "Promote body_top caveat"
    assert result["intent"] == (
        "Stage one or more graph changes supported by selected patterns."
    )
    assert result["anchors"] == [pattern.pattern_iri, target, implication]
    assert result["framings"][0]["stance"] == (
        "https://richcanopy.org/ns/rc#CandidateRevision"
    )
    staged = describe_staged_revision_tool(
        db,
        result["staged_revisions"][0]["revision_iri"],
    )
    assert staged["supporting_patterns"][0]["iri"] == pattern.pattern_iri
    assert staged["supporting_observations"][0]["iri"] == observation.observation_iri
    assert {anchor["iri"] for anchor in staged["revision_anchors"]} == {
        pattern.pattern_iri,
        target,
        implication,
    }
    assert "Selected pattern support" in staged["rationale"]


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


def test_describe_query_context_tool_returns_planning_projection(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)

    result = describe_query_context_tool(
        db,
        iri="https://richcanopy.org/example/manifest/ais#DailyBroadcasts",
    )

    assert result["dataset"]["label"] == "AIS Daily Broadcast Positions"
    assert result["readiness"] == "needs_review"
    assert "broadcasts/{year}/ais-{date}.parquet" in result["path_templates"]
    assert result["storage_accesses"][0]["endpoint_profile"] == "local-minio"
    assert any(
        issue["code"] == "layout_needs_verification"
        and issue["severity"] == "warning"
        for issue in result["issues"]
    )
    assert "non-secret planning metadata" in result["planning_notes"][0]


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
        and warning["resource"]["iri"]
        == "https://richcanopy.org/example/manifest/ais#DailyIndex"
        for warning in result["operational_warnings"]
    )
    assert result["caveats"] == []
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

    wrong_predicate = describe_assertion_support_tool(
        db,
        subject="https://richcanopy.org/example/manifest/ais#DailyIndex",
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


def test_record_dataset_profile_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Messages"

    result = record_dataset_profile_tool(
        db,
        dataset_iri=dataset,
        summary="MCP helper recorded a profile bundle.",
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
            {"metric": "rc:MinimumValue", "value": 3},
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
        (item["metric"]["iri"], item["value"], item["value_datatype"])
        for item in profile["profile_metrics"]
    } == {
        ("https://richcanopy.org/ns/rc#MinimumValue", "3", str(XSD.integer)),
        ("https://richcanopy.org/ns/rc#MaximumValue", "99", str(XSD.integer)),
    }
    assert profile["evidence"][0]["iri"] == result["observation"]["evidence_iri"]
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
    assert len(result["column_profiles"]) == 1
    assert result["column_profiles"][0]["column_iri"] == status_column
    assert result["column_profiles"][0]["map_column"] is None
    assert result["dataset_profile"]["observation"]["evidence_iri"] == shared_evidence
    assert result["column_profiles"][0]["observation"]["evidence_iri"] == shared_evidence

    dataset = describe_dataset_tool(db, table)

    assert dataset["row_count_snapshot"] == 1000
    assert dataset["columns"] == []
    assert dataset["profile_summary"]["returned_dataset_profile_count"] == 1
    assert dataset["profile_summary"]["returned_mapped_column_profile_count"] == 0
    assert dataset["profile_summary"]["returned_unmapped_column_profile_count"] == 1
    assert dataset["profile_summary"]["returned_profile_count"] == 2
    assert dataset["profile_summary"]["mapped_profiled_column_count"] == 0
    assert dataset["profile_summary"]["evidence_iris"] == [shared_evidence]
    assert dataset["profile_summary"]["evidence_profile_counts"] == {
        shared_evidence: 2,
    }
    assert dataset["profile_summary"]["shared_evidence_iris"] == [shared_evidence]
    profile = dataset["unmapped_column_profile_observations"][0]
    assert profile["sample_scope"] == "Twenty-five sampled Orders rows."
    assert profile["sample_method"] == "DuckDB sampled profile query."
    assert profile["evidence"][0]["iri"] == shared_evidence
    assert profile["evidence"][0]["sources"] == ["tests/test_mcp_tools.py"]
    assert validate_graph_tool(db, scope="all")["conforms"] is True


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

    assert dataset["columns"] == []
    assert dataset["profile_observations"] == []
    assert dataset["profile_summary"]["returned_unmapped_column_profile_count"] == 1
    assert dataset["profile_summary"]["returned_profile_count"] == 1
    profiles = dataset["unmapped_column_profile_observations"]
    assert len(profiles) == 1
    assert profiles[0]["iri"] == result["observation"]["observation_iri"]
    assert profiles[0]["observed_column"]["iri"] == column
    assert profiles[0]["sample_method"] == "Top-N sampled value-frequency query."
    assert [
        (item["value"], item["frequency"])
        for item in profiles[0]["value_frequencies"]
    ] == [("fulfilled", 18), ("pending", 4)]
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

    result = describe_assertion_support_tool(
        db,
        subject="https://example.test/project#Messages",
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
    assert result["owner_dataset"] is None
    assert result["absence_note"] is None
    assert result["nearby_context_triples"] == []
    assert result["nearby_caveat_links"] == []
    assert result["related_routes"] == []
    assert result["related_route_summaries"] == []
    assert result["suggested_next_actions"][0]["tool_name"] == (
        "describe_context_slice"
    )
    assert result["suggested_next_actions"][0]["mcp_tool_name"] == (
        "doxabase.describe_context_slice"
    )
    assert result["suggested_next_actions"][0]["arguments"]["seed_iris"] == [
        "https://example.test/project#Messages",
        "https://example.test/project#message_id",
    ]
    assert result["requested_object"]["resource"]["column_name"] == "message_id"
    assert "retrieval aid" in result["context_note"]
    assert "same-subject predicate triples" in result["support_scope_note"]


def test_record_claim_reconsideration_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    older = record_claim_observation_tool(
        db,
        summary="Initial MMSI identity hunch.",
        claim_text="MMSI can be treated as the stable vessel identity key.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=["https://example.test/ais#mmsi"],
        evidence_sources=["trial setup"],
    )
    newer = record_claim_observation_tool(
        db,
        summary="MMSI caveat check.",
        claim_text="MMSI is an operational grouping key, not proof of vessel identity.",
        claim_kind="rc:CaveatClaim",
        claim_targets=["https://example.test/ais#mmsi"],
        evidence_sources=["retrieved caveat"],
        observation_status="rc:Checked",
    )

    result = record_claim_reconsideration_tool(
        db,
        newer_claim=newer["claim_iri"],
        older_claim=older["claim_iri"],
        relation="weakens",
        rationale="The retrieved caveat makes the first hunch too strong.",
        evidence_sources=["DoxaBase search(\"MMSI vessel\")"],
        source_path="/tmp/doxabase-search-mmsi-vessel.json",
        source_kind="rc:DoxaBaseAPISource",
    )

    assert result["relation"] == "https://richcanopy.org/ns/rc#Weakening"
    assert result["older_claim_status"] == "https://richcanopy.org/ns/rc#Weakened"
    assert result["evidence_iri"] is not None
    assert result["source_span_iri"] is not None
    context = describe_resource_tool(
        db,
        iri=older["claim_iri"],
        graph="observations",
    )
    assert context["claim"]["lifecycle_summary"] == (
        "Current status: weakened. Later claims reconsider this claim: 1 weakening."
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
