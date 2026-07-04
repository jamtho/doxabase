"""Distillation scoreboard: measure and enforce the program's budget metrics.

This is the instrument demanded by `doxabase_design_docs/07-distillation-program.md`
(Phase 0.1). It computes every budget metric on deterministic inputs and, with
`--check`, exits non-zero on any violation. `BUDGETS` below is the ONLY place
ceilings are defined; `tests/test_budgets.py` asserts the same ceilings through
these functions.

Rules (from the program):
- Ceilings only ever move toward the end-state targets (the ratchet).
  Loosening any ceiling requires James.
- Response sizes are `len(json.dumps(...))` chars on the standard fixture
  capsule: a fresh capsule with both bundled TriG fixtures loaded, default
  arguments. Rule of thumb: 4 chars ~= 1 token; JSON tokenizes worse.

Usage:
    uv run python tools/scoreboard.py            # print the table
    uv run python tools/scoreboard.py --check    # exit 1 on any violation
    uv run python tools/scoreboard.py --json     # machine-readable output

Not measured here: full-suite wall time (the gate runs pytest itself) and
wheel-install smoke (enforced by tools/gate.sh from Phase 1 on).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Ceilings. Initial values = 2026-07-04 actuals rounded up <= 5% so the
# ratchet starts immediately without failing. Phase items tighten these toward
# the end-state targets recorded alongside.
BUDGETS: dict[str, int] = {
    "mcp_tool_count": 65,
    "mcp_schema_chars": 86_000,
    "largest_module_lines": 5_000,
    "largest_test_module_lines": 5_000,
    "project_brief_chars": 4_850,
    "describe_dataset_chars": 24_000,
    "describe_query_context_chars": 21_600,
    "context_slice_chars": 46_300,
    "graph_overview_chars": 14_700,
    "search_chars": 6_500,
    "list_entities_chars": 16_000,
    "agent_docs_bytes": 1_200_000,
    "start_here_lines": 120,
}

# Where the program says each ceiling must end up (doc 07 budget table).
# Informational here; the ratchet moves BUDGETS toward these phase by phase.
END_STATE: dict[str, int] = {
    "mcp_tool_count": 25,
    "mcp_schema_chars": 25_000,
    "largest_module_lines": 3_000,
    "largest_test_module_lines": 5_000,
    "project_brief_chars": 8_000,
    "describe_dataset_chars": 12_000,
    "describe_query_context_chars": 12_000,
    "context_slice_chars": 32_000,
    "graph_overview_chars": 8_000,
    "search_chars": 8_000,
    "list_entities_chars": 4_000,
    "agent_docs_bytes": 150_000,
    "start_here_lines": 120,
}

# Deterministic measurement targets on the standard fixture capsule. DailyIndex
# is the 6-column AIS table the fresh-eyes review measured.
DATASET_IRI = "https://richcanopy.org/example/manifest/ais#DailyIndex"
SEARCH_QUERY = "mmsi"


def _line_count(path: Path) -> int:
    return sum(1 for _ in path.open("rb"))


def _largest_py(directory: Path) -> tuple[str, int]:
    best_name, best_lines = "", 0
    for path in sorted(directory.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        lines = _line_count(path)
        if lines > best_lines:
            best_name, best_lines = str(path.relative_to(ROOT)), lines
    return best_name, best_lines


def measure_static() -> dict[str, Any]:
    """Metrics that need no capsule: file sizes and docs weight."""
    largest_module, largest_module_lines = _largest_py(ROOT / "doxabase")
    largest_test, largest_test_lines = _largest_py(ROOT / "tests")
    agent_docs = sorted((ROOT / "docs" / "agent").glob("*.md"))
    return {
        "largest_module_lines": largest_module_lines,
        "largest_module_name": largest_module,
        "largest_test_module_lines": largest_test_lines,
        "largest_test_module_name": largest_test,
        "agent_docs_bytes": sum(p.stat().st_size for p in agent_docs),
        "start_here_lines": _line_count(ROOT / "docs" / "agent" / "start-here.md"),
    }


def measure_mcp_schema(capsule_path: Path) -> dict[str, Any]:
    """Tool count and total schema chars a client receives on session start."""
    from doxabase.mcp_server import build_server

    server = build_server(capsule_path)
    tools = asyncio.run(server.list_tools())
    schema_chars = sum(
        len(json.dumps(tool.model_dump(exclude_none=True), sort_keys=True))
        for tool in tools
    )
    return {"mcp_tool_count": len(tools), "mcp_schema_chars": schema_chars}


def measure_responses(capsule_path: Path) -> dict[str, Any]:
    """Response sizes on the standard fixture capsule, default arguments."""
    from doxabase import mcp_tools as mt
    from doxabase.core import DoxaBase

    db = DoxaBase(capsule_path)
    try:
        mt.load_example_fixtures_tool(db)

        def size(payload: Any) -> int:
            return len(json.dumps(payload, sort_keys=True))

        return {
            "project_brief_chars": size(mt.project_brief_tool(db)),
            "describe_dataset_chars": size(
                mt.describe_dataset_tool(db, iri=DATASET_IRI)
            ),
            "describe_query_context_chars": size(
                mt.describe_query_context_tool(db, iri=DATASET_IRI)
            ),
            "context_slice_chars": size(
                mt.get_context_graph_tool(db, seed_iris=[DATASET_IRI])
            ),
            "graph_overview_chars": size(mt.graph_overview_tool(db)),
            "search_chars": size(mt.search_tool(db, query=SEARCH_QUERY)),
            "list_entities_chars": size(mt.list_entities_tool(db)),
        }
    finally:
        db.close()


def measure_all() -> dict[str, Any]:
    metrics = measure_static()
    with tempfile.TemporaryDirectory(prefix="doxabase-scoreboard-") as tmp:
        capsule = Path(tmp) / "scoreboard.sqlite"
        metrics.update(measure_responses(capsule))
        metrics.update(measure_mcp_schema(capsule))
    return metrics


def violations(metrics: dict[str, Any]) -> list[str]:
    problems = []
    for key, ceiling in BUDGETS.items():
        actual = metrics[key]
        if actual > ceiling:
            problems.append(f"{key}: {actual:,} exceeds budget {ceiling:,}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 on violation")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args(argv)

    metrics = measure_all()
    problems = violations(metrics)

    if args.json:
        print(
            json.dumps(
                {"metrics": metrics, "budgets": BUDGETS, "violations": problems},
                indent=2,
            )
        )
    else:
        width = max(len(k) for k in BUDGETS)
        print(f"{'metric':<{width}}  {'actual':>12}  {'budget':>12}  {'end state':>12}")
        for key, ceiling in BUDGETS.items():
            actual = metrics[key]
            flag = "  OVER" if actual > ceiling else ""
            print(
                f"{key:<{width}}  {actual:>12,}  {ceiling:>12,}  "
                f"{END_STATE[key]:>12,}{flag}"
            )
        print(
            f"\nlargest module: {metrics['largest_module_name']} "
            f"({metrics['largest_module_lines']:,} lines)"
        )
        print(
            f"largest test module: {metrics['largest_test_module_name']} "
            f"({metrics['largest_test_module_lines']:,} lines)"
        )
        if problems:
            print("\nBUDGET VIOLATIONS:")
            for problem in problems:
                print(f"  - {problem}")
        else:
            print("\nall budgets green")

    if args.check and problems:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
