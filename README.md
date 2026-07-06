# DoxaBase

Understanding of anything complex is built by a group, over time: many
sessions of noticing, checking, being wrong, and slowly getting it right.
Data work makes this acute — every serious dataset accumulates hard-won
lore ("the MMSI column lies sometimes"; the join that looks right and
isn't; the population you must exclude before any count is honest) — and
that lore mostly lives in one person's head or a chat scrollback, and dies
there. Now that AI agents do real analytical work, the group has grown and
the memory has gotten worse: every new session starts naive and pays the
same tuition again.

DoxaBase is the group's memory, with discipline. It is a local capsule —
one SQLite file of RDF named graphs — where agents and humans record what
they notice as **evidenced observations** *while they work*, synthesize
recurring findings into **patterns**, and promote reviewed conclusions
into a **current-best map** of the data. The point is not documentation
after the fact: knowledge is encoded in a transferable form as it is being
developed, so building understanding and sharing it become the same act.
The handover conversation you wish came with every complex dataset stops
being a conversation and becomes a file.

The epistemics are what keep a shared memory trustworthy as it grows:
observations must cite evidence; claims carry confidence and are never
silently deleted — only weakened, contradicted, superseded, or refined;
map changes go through staged review with rationale; and privacy gates
treat "scanner-clean" as a review prompt, not export approval. Agents
supply the judgement; DoxaBase supplies the mechanics that keep judgement
honest. The next session — human or agent — opens the capsule and starts
where the group left off.

The loop, concretely:

1. **Observation**: record point-in-time or source-scoped findings, with
   evidence, as RDF resources.
2. **Pattern**: synthesize related findings into explicit rationale that can
   explain why something looks durable or important.
3. **Systematisation**: consolidate useful patterns and findings into a more
   durable project map, ontology terms, shapes, caveats, and revision
   history.

The graph is deliberately open-ended: projects can record arbitrary RDF
claims. DoxaBase ships a small Rich Canopy `rc:` ontology for common
dataset concepts — assets, tables, columns, physical layouts, caveats,
observations, evidence, provenance — so knowledge stays portable across
projects without forcing any project into a closed schema.

The implementation is intentionally small: a Python package backed by a
local SQLite file, with RDFLib handling parsing and pySHACL handling
explicit validation. There is no embedded LLM in the library.

## Current Status: Distillation (V1 → V1.5)

V1 was built fast by an autonomous improvement loop and works — the full
observation → pattern → staged-map workflow, profiling, query-planning
handoffs, staged revisions with drift detection, privacy preflights, and an
MCP server are all real and tested. But the loop had no subtractive pressure,
and the surface grew far past the design brief: 89 MCP tools against an
intended ~10, orientation responses in the tens of thousands of tokens, and a
75k-line core module. The external review in
`doxabase_design_docs/06-fresh-eyes-review-2026-07-03.md` diagnosed this, and
the project is now executing the **Distillation Program**
(`doxabase_design_docs/07-distillation-program.md`): same capability, a small
fraction of the surface and context cost. Until the program exits, it
supersedes every other stated priority in this repo.

Progress and budgets are measured, not asserted: `tools/scoreboard.py` prints
the scoreboard, ceilings only ratchet downward, and `tests/test_budgets.py`
enforces them in the ordinary test run. The wave-by-wave log lives in
`docs/journal/waves.md`.

Done so far: instrumentation and loop rules; packaging (installable wheel,
`doxabase-mcp` entry point, CI gate with a clean-venv install smoke); the
core monolith split into ~30 readable modules; response envelopes that omit
null/empty; RDF-first context graphs (TriG payload by default — the same
graph content costs ~10x less as TriG than as JSON triples). In progress:
response-size diets, collapsing the tool surface to ≤25
(`doxabase_design_docs/08-mcp-surface-v2.md` is the mapping), and rebuilding
`project_brief` as state-not-script.

## How To Read This Project

For a human overview: this README, then `docs/worked-example.md` (a real
session, call by call — the fastest way to *feel* how the capsule works),
then `ARCHITECTURE.md` and the design
docs in `doxabase_design_docs/` (01–05 the original design, 06–08 the review
and distillation program).

For a fresh agent: `AGENTS.md` (the Permanent Loop Rules), then
`docs/agent/start-here.md`, `docs/agent/working-the-capsule.md`, and
`docs/agent/response-conventions.md`. Operational topic docs live in
`docs/agent/`; dated history lives in `docs/journal/` and is deliberately
not agent-reference material.

## Install And Run

```bash
# from a checkout
uv sync
uv run doxabase-mcp --capsule .doxabase.sqlite   # stdio MCP server

# or as a wheel
uv build && pip install dist/doxabase-*.whl
doxabase-mcp --capsule /path/to/capsule.sqlite
```

Runtime dependencies are `mcp`, `rdflib`, and `pyshacl`; Parquet helpers need
the `doxabase[parquet]` extra. The ontology seeds, agent docs, and example
fixtures ship inside the wheel.

## Python Quickstart

```python
from doxabase import DoxaBase

db = DoxaBase("project.sqlite")          # creates + seeds on first open
db.record_observation(
    "MMSI reuse observed across two vessels in the 2020-01 sample.",
    observed_by="analyst",
    evidence_summary="Manual inspection of 14 conflicting position tracks.",
    evidence_sources=["s3://bucket/ais/2020-01/"],
)
print(db.search(query="mmsi", limit=5).matches)
print(db.validate_graph(scope="all").conforms)
db.close()
```

`DoxaBase.open_readonly(path)` gives concurrent readers; a capsule has one
writer at a time (see `ARCHITECTURE.md` for the concurrency stance).

## Development

The full pre-commit gate:

```bash
bash tools/gate.sh
```

which runs the test suite (`uv run pytest -q -n 16`), RDF asset validation,
the budget scoreboard (`uv run python tools/scoreboard.py --check`),
`git diff --check`, a wheel build, and an install smoke in a clean venv.
CI (`.github/workflows/ci.yml`) runs exactly the same script.

Layout: `doxabase/core/` is the capsule engine (one module per subsystem,
composed into the `DoxaBase` facade); `doxabase/mcp_tools.py` holds testable
MCP-callable logic; `doxabase/mcp_server.py` registers tools;
`doxabase/agent_docs.py` registers the agent docs; `tests/core/` and
`tests/mcp/` mirror the module split.

## Graph Roles

Immutable seed graphs `base_ontology` and `base_shapes` ship with the
package. Mutable project graphs: `map` (current-best facts), `ontology`
(project vocabulary), `observations`, `patterns`, `evidence`, `shapes`
(project SHACL extensions), and `history` (revision rationale and
snapshots). `docs/agent/graph-roles.md` has the placement rules.

## Project Direction

The Distillation Program's exit criteria (doc 07) define near-term
direction: ≤25 tools, budget-tested response sizes, state-not-script
orientation, distilled reference docs, and an external case study from an
installed wheel. Feature development resumes only after the program's
retrospective (`doxabase_design_docs/09-...`, forthcoming); the V2 ideas
parked in `doxabase_design_docs/04-doxabase-v2-backlog.md` are inputs to
that decision, not commitments.
