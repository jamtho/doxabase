from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from doxabase import DoxaBase
from doxabase.mcp_tools import load_example_fixtures_tool
from examples._runtime_paths import example_artifact, reset_file


CAPSULE = example_artifact(
    "first-workflow",
    "/tmp/doxabase-first-workflow.sqlite",
    filename="capsule.sqlite",
)
AGENT = "urn:doxabase:first-workflow-agent"


def main() -> None:
    reset_file(CAPSULE)

    db = DoxaBase.create(CAPSULE, overwrite=True)
    loaded = load_example_fixtures_tool(db, replace=True)

    overview = db.graph_overview()
    tables = db.list_entities(type="rc:Table", graph="map", limit=5).entities
    table = _choose_table(tables)
    description = db.describe_dataset(table.iri)
    matches = db.search("MMSI vessel", graph="map", limit=3).matches
    query_context = db.describe_query_context(table.iri)

    observation = db.record_observation(
        summary=(
            "First workflow inspected the example fixtures and found a table "
            "ready for follow-up review."
        ),
        observed_asset=table.iri,
        observed_by=AGENT,
        evidence_summary=(
            "examples/first-workflow.py loaded bundled fixtures, inspected "
            "table metadata, searched map lore, and checked query context."
        ),
        evidence_sources=["examples/first-workflow.py"],
    )
    validation = db.validate_graph(scope="all")

    print("# DoxaBase First Workflow")
    print(f"Capsule: {CAPSULE}")
    print(f"Loaded fixture triples: {loaded['total_imported']}")
    print(_key_counts_line(overview.key_counts))
    print()
    print("Tables:")
    for item in tables:
        print(f"- {item.label or item.iri} ({item.iri})")
    print()
    print(f"Selected table: {description.label or description.iri}")
    print(f"Column count: {len(description.columns)}")
    print(f"Caveat count: {len(description.caveats)}")
    print(f"Query readiness: {query_context.readiness}")
    decision = query_context.query_target_decision
    print(
        "Query decision: "
        f"{decision.status}"
        f" candidate={decision.candidate_index}"
        f" path_status={decision.candidate_path_status}"
    )
    if decision.candidate_path:
        print(f"Query candidate path: {decision.candidate_path}")
    if query_context.suggested_next_actions:
        action = query_context.suggested_next_actions[0]
        print(f"Next action: {action.call or action.tool_name}")
    if query_context.issues:
        print("Query issues:")
        for issue in query_context.issues[:3]:
            print(f"- {issue.code}: {issue.message}")
            fixture_hint = (
                issue.details.get("fixture_staleness_hint")
                if issue.details is not None
                else None
            )
            if fixture_hint is not None:
                print(f"  fixture hint: {fixture_hint['hint_type']}")
        if "dailyindex" in table.iri.lower():
            print(
                "  see docs/agent/query-planning.md#"
                "ais-dailyindex-question-to-handoff-gap"
            )
    else:
        print("Query issues: none")
    print()
    print("Search matches:")
    for match in matches:
        print(f"- {match.label or match.iri} [{match.graph}]")
    print()
    print(f"Recorded observation: {observation.observation_iri}")
    print(f"Validation conforms: {validation.conforms}")


def _choose_table(tables: list[object]) -> object:
    for table in tables:
        haystack = f"{table.iri} {table.label}".lower()
        if "dailyindex" in haystack or "daily index" in haystack:
            return table
    for table in tables:
        haystack = f"{table.iri} {table.label}".lower()
        if "ais" in haystack:
            return table
    return tables[0]


def _key_counts_line(key_counts: dict[str, int]) -> str:
    keys = ["tables", "columns", "patterns", "storage_accesses"]
    values = ", ".join(f"{key}={key_counts[key]}" for key in keys)
    return f"Key counts: {values}"


if __name__ == "__main__":
    main()
