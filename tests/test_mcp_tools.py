from pathlib import Path

import pytest

from doxybase import DoxyBase
from doxybase.mcp_server import build_server
from doxybase.mcp_tools import (
    graph_overview_tool,
    list_docs_tool,
    list_entities_tool,
    load_example_fixtures_tool,
    validate_graph_tool,
)


@pytest.mark.anyio
async def test_build_server_registers_expected_tools(tmp_path: Path) -> None:
    server = build_server(tmp_path / "mcp.sqlite")
    tool_names = {tool.name for tool in await server.list_tools()}

    assert "doxybase.list_docs" in tool_names
    assert "doxybase.get_doc" in tool_names
    assert "doxybase.graph_overview" in tool_names
    assert "doxybase.list_entities" in tool_names
    assert "doxybase.load_example_fixtures" in tool_names
    assert "doxybase.validate_graph" in tool_names


def test_doc_tools_return_json_like_payloads() -> None:
    result = list_docs_tool()
    doc_ids = {doc["id"] for doc in result["docs"]}

    assert "overview" in doc_ids
    assert "graph_roles" in doc_ids


def test_fixture_loading_and_validation_tools(tmp_path: Path) -> None:
    db = DoxyBase.create(tmp_path / "capsule.sqlite")

    load_result = load_example_fixtures_tool(db)
    overview = graph_overview_tool(db)
    tables = list_entities_tool(db, type="rc:Table", graph="map")
    validation = validate_graph_tool(db, scope="all")

    assert load_result["total_imported"] == 735
    assert overview["key_counts"]["tables"] >= 7
    assert tables["count"] >= 7
    assert validation["conforms"] is True


def test_fixture_loading_replace_keeps_all_fixtures(tmp_path: Path) -> None:
    db = DoxyBase.create(tmp_path / "capsule.sqlite")

    load_result = load_example_fixtures_tool(db, replace=True)
    tables = list_entities_tool(db, type="rc:Table", graph="map")
    labels = {entity["label"] for entity in tables["entities"]}

    assert load_result["replace"] is True
    assert "AIS Daily Broadcast Positions" in labels
    assert "AIS Daily Vessel Index" in labels
    assert "Gamma Market Snapshots" in labels
    assert "Trade Events" in labels
