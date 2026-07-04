"""Wheel install smoke: prove an installed doxabase works outside the repo.

Run by tools/gate.sh from a clean venv in a temp directory (program Phase
1.4). Exercises: capsule creation, packaged-fixture loading, search, an
observation write, SHACL validation, and MCP server construction with tool
listing. Fails loudly if the packaged data root is not in use.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path


def main() -> None:
    import doxabase.core as core
    from doxabase import mcp_tools as mt
    from doxabase.core import DoxaBase
    from doxabase.mcp_server import build_server

    if core.ROOT.name != "_data":
        raise SystemExit(
            f"smoke must run against an installed wheel; data root is {core.ROOT}"
        )

    with tempfile.TemporaryDirectory(prefix="doxabase-smoke-") as tmp:
        capsule = Path(tmp) / "smoke.sqlite"
        db = DoxaBase(capsule)
        try:
            loaded = mt.load_example_fixtures_tool(db)
            assert loaded["total_imported"] > 0, "fixture load imported nothing"

            search = db.search(query="mmsi", limit=5)
            assert search.matches, "search over fixtures returned no matches"

            record = db.record_observation(
                "Install smoke observation: packaged fixtures load and search.",
                observed_by="install-smoke",
                evidence_summary="Search over packaged fixtures returned matches.",
                evidence_sources=["smoke://install-smoke/search"],
            )
            assert record.observation_iri

            validation = db.validate_graph(scope="all")
            assert validation.conforms, "fresh capsule failed SHACL validation"
        finally:
            db.close()

        server = build_server(capsule)
        tools = asyncio.run(server.list_tools())
        assert tools, "MCP server registered no tools"

        print(
            f"install smoke ok: data root {core.ROOT}, "
            f"{loaded['total_imported']} triples, {len(tools)} MCP tools"
        )


if __name__ == "__main__":
    main()
