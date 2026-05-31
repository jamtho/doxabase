from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from doxybase import DoxyBase
from doxybase.mcp_tools import (
    describe_dataset_tool,
    get_doc_tool,
    graph_overview_tool,
    import_trig_tool,
    list_docs_tool,
    list_entities_tool,
    load_example_fixtures_tool,
    record_observation_tool,
    search_tool,
    validate_graph_tool,
)

SERVER_INSTRUCTIONS = """DoxyBase is a local RDF memory capsule for data projects.
Start with doxybase.list_docs, then read overview, graph_roles, and agent_workflow.
Use graph_overview, search, list_entities, and describe_dataset before asking for broader graph context.
Current V1 tools support inspection, lexical search, bounded dataset description, observation recording, import, fixture loading, and validation; context slicing is not implemented yet."""


def build_server(capsule_path: str | Path = ".doxybase.sqlite") -> FastMCP:
    db = DoxyBase.create(capsule_path, overwrite=False)
    server = FastMCP("doxybase", instructions=SERVER_INSTRUCTIONS)

    @server.tool(name="doxybase.list_docs")
    def list_docs() -> dict[str, Any]:
        """List short agent-facing DoxyBase docs available through MCP."""

        return list_docs_tool()

    @server.tool(name="doxybase.get_doc")
    def get_doc(doc_id: str, max_chars: int = 12000) -> dict[str, Any]:
        """Return one agent-facing markdown doc by ID."""

        return get_doc_tool(doc_id, max_chars=max_chars)

    @server.tool(name="doxybase.graph_overview")
    def graph_overview(limit: int = 100) -> dict[str, Any]:
        """Return named graph counts, common classes, predicates, and key counts."""

        return graph_overview_tool(db, limit=limit)

    @server.tool(name="doxybase.list_entities")
    def list_entities(
        type: str | None = None,
        graph: str | None = "map",
        text: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List graph entities by RDF type, graph role, and optional text filter."""

        return list_entities_tool(
            db,
            type=type,
            graph=graph,
            text=text,
            limit=limit,
            offset=offset,
        )

    @server.tool(name="doxybase.describe_dataset")
    def describe_dataset(iri: str, graph: str | None = "map") -> dict[str, Any]:
        """Return bounded schema, layout, caveat, and provenance context for one dataset."""

        return describe_dataset_tool(db, iri=iri, graph=graph)

    @server.tool(name="doxybase.record_observation")
    def record_observation(
        summary: str,
        observation_type: str = "observation",
        observed_asset: str | None = None,
        observed_column: str | None = None,
        observed_at: str | None = None,
        observed_by: str | None = None,
        evidence_summary: str | None = None,
        evidence_sources: list[str] | None = None,
        sample_size: int | None = None,
        row_count: int | None = None,
        null_count: int | None = None,
        distinct_count: int | None = None,
    ) -> dict[str, Any]:
        """Record a structured observation, optionally linked to evidence."""

        return record_observation_tool(
            db,
            summary=summary,
            observation_type=observation_type,
            observed_asset=observed_asset,
            observed_column=observed_column,
            observed_at=observed_at,
            observed_by=observed_by,
            evidence_summary=evidence_summary,
            evidence_sources=evidence_sources,
            sample_size=sample_size,
            row_count=row_count,
            null_count=null_count,
            distinct_count=distinct_count,
        )

    @server.tool(name="doxybase.search")
    def search(
        query: str,
        graph: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Lexically search literal RDF claims and return matched resources."""

        return search_tool(
            db,
            query=query,
            graph=graph,
            limit=limit,
            offset=offset,
        )

    @server.tool(name="doxybase.import_trig")
    def import_trig(path: str, replace: bool = False) -> dict[str, Any]:
        """Import a TriG file into DoxyBase graph roles."""

        return import_trig_tool(db, path=path, replace=replace)

    @server.tool(name="doxybase.load_example_fixtures")
    def load_example_fixtures(replace: bool = False) -> dict[str, Any]:
        """Import the bundled AIS and Polymarket RC fixture graphs."""

        return load_example_fixtures_tool(db, replace=replace)

    @server.tool(name="doxybase.validate_graph")
    def validate_graph(scope: str = "map", limit_results: int = 100) -> dict[str, Any]:
        """Run SHACL validation for map, ontology, shapes, or all graph scope."""

        return validate_graph_tool(db, scope=scope, limit_results=limit_results)

    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the DoxyBase MCP server.")
    parser.add_argument(
        "--capsule",
        default=".doxybase.sqlite",
        help="SQLite capsule path. Defaults to .doxybase.sqlite in the current directory.",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport. Defaults to stdio.",
    )
    args = parser.parse_args()
    build_server(args.capsule).run(args.transport)


if __name__ == "__main__":
    main()
