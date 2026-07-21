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

## Current Status: Field Studies on a Distilled Core

The **Distillation Program completed 2026-07-05** (`v0.2.0`): the V1
autonomous loop had grown the surface to 89 MCP tools and a 75k-line
core; the program cut it to **25 tools, a 31k-char schema, and ~30
readable modules** with the same capability, enforced by a scoreboard
whose ceilings only ratchet downward (`tools/scoreboard.py`,
`tests/test_budgets.py`, wave log in `docs/journal/waves.md`). The
retrospective is `doxabase_design_docs/09-distillation-retrospective.md`.

Since then the project runs a **recorded-trials / deferred-distiller
loop** (doc 10): real analytical work happens in cold agent sessions
against real data, everything is graded and recorded, and product
changes land in small evidence-batched distiller passes rather than
reflexively. The first field study — fourteen sessions on two years of
NOAA AIS data with a domain expert in the loop — is written up in
`CASE-STUDY-AIS.md`.

Because this is research, here is the honest state of the claims:

- **Demonstrated, with graded trial records** (`docs/journal/trials/`):
  knowledge transfer between cold agents that never met, including a
  deliberately weaker model applying an inherited method correctly and
  extending it; a domain vocabulary distilled from recorded cases and
  then transferred *blind* to an agent never told it existed; and
  analytical methods regenerated from RDF behavioural contracts alone
  at 99.8% agreement, with the contract's invariants catching a real
  bug in the regenerated code.
- **Working practice, one domain so far**: the state-vs-ephemera
  architecture (populations in regenerable frames, methods and
  promoted judgements in the graph), evidenced parameters whose
  thresholds cite their validation surveys, and identity-by-promotion
  for derived entities (doc 14). A second, independent case study is
  underway to test generalization; nothing enters the core ontology
  until two domains need it.
- **Design-stage, deliberately speculative**: the capsule observatory
  (doc 11), RDF method contracts as general engineering practice
  (doc 12 — pilot passed), and search-based method improvement over
  contracts. These are stated as designs with pilot evidence, not
  shipped claims; expect them to be revised as trials accumulate.

**The Capsule Workbench is real and usable now** — it moved into this
repo as the `workbench/` package (2026-07-20, at the owner's direction;
previously `jamtho/doxabase-workbench`). Install the optional extra
(`pip install doxabase[workbench]`) and point it at any capsule
(`doxabase-workbench capsule.sqlite`) to browse it in your browser — the
project brief as a landing page, a `/datasets` overview leading with
recorded row counts and storage reachability, every IRI clickable with
claims and evidence expanded inline, dataset pages that refuse to show
data without its caveats, a guarded SQL box over the frames a capsule
describes — any query result whose columns carry a coordinate pair also
renders as a Leaflet map with color-by and path-join affordances, the map
being a second renderer for query results rather than a separate
geospatial subsystem — the full revision timeline with staged→applied
lineage, and supersession chains rendered so you can watch conclusions
change as evidence arrives. It opens the capsule strictly read-only:
agents write, humans see. `workbench/` is a sibling top-level package, not part of
`doxabase/` — the distillation scoreboard doesn't measure it. Design
contract in doc 13.

## How To Read This Project

For a human overview: this README, then `CASE-STUDY-AIS.md` (what a
fourteen-session field study on real maritime data looked like and what
came out of it), then `docs/worked-example.md` (a real session, call by
call — the fastest way to *feel* how the capsule works),
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
the `doxabase[parquet]` extra, and the Capsule Workbench (`workbench/`, doc
13) needs `doxabase[workbench]` — `pip install doxabase[workbench]` then
`doxabase-workbench capsule.sqlite`. The ontology seeds, agent docs, and
example fixtures ship inside the wheel.

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

Direction is set by `doxabase_design_docs/10-next-directions.md` (the
trials/distiller loop) and the design docs it has since produced:
11 (capsule observatory), 12 (RDF method contracts), 13 (capsule
workbench), 14 (anchored derivations) — each written from field-study
need and carrying its pilot evidence and open decision points. The
core's surface stays frozen under the distillation budgets; product
changes arrive through evidence-batched distiller passes
(`docs/journal/distiller-pass-1.md` is the first, and the template).
The V2 ideas parked in `doxabase_design_docs/04-doxabase-v2-backlog.md`
remain inputs, not commitments.
