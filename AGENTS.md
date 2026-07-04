# Agent Guide

This repository is DoxaBase: a small local RDF memory capsule for data projects.
Agents supply semantic judgement; DoxaBase supplies storage, parsing, named graph
mechanics, graph inspection, and explicit validation.

These notes are meant to reduce rediscovery, not replace judgement. If the code,
the data model, or the user's request points toward a better local choice, take
that path and leave enough context for the next reader to follow it.

Nothing here is set in stone. If any guidance seems unhelpful, stale, or at odds
with how the project is evolving, raise that to the user instead of silently
working around it. It can easily be changed and improved.

## Collaboration Posture

Treat work on this project as collaborative exploration. Agents and models are
capable enough to notice tradeoffs, suggest better paths, and surface uncertainty
rather than only following instructions literally. When the user's direction is
clear, act decisively; when the shape of the work is still emerging, help clarify
it with good questions, concrete options, and thoughtful implementation choices.

Always make the user aware if they seem to be missing something, misunderstanding
something, or generally heading in a direction that may not serve the project.

Avoid turning this guide into a rigid checklist. The point is to help humans and
agents think together with less friction.

## Active Program: Distillation (V1 → V1.5)

**`doxabase_design_docs/07-distillation-program.md` is the active program and
supersedes the build priorities in this file, `README.md`, `ARCHITECTURE.md`,
and `docs/agent/project-strategy.md` until its exit criteria are met.** Read it
(and the review it executes, doc 06) before starting any wave of work. The
goal is the same capability at a small fraction of today's surface and context
cost — distill, don't extend. During the program: no new MCP tools, no new
response fields, no new agent-doc sections, no new helpers, except where a
program phase item explicitly creates one.

## Permanent Loop Rules

These govern autonomous improvement work from now on, during the program and
after it:

1. **Scoreboard gate.** The pre-commit gate is `uv run pytest -q -n 16`,
   `uv run python tools/validate_rdf.py`,
   `uv run python tools/scoreboard.py --check`, and `git diff --check`. A
   scoreboard regression blocks the commit. Budget ceilings only ratchet
   downward; loosening any ceiling requires James.
2. **Wave shape.** Every wave: pick the next program item → implement → full
   gate → wave-journal entry (≤ 15 lines: what changed, measured effect on the
   scoreboard, next item). Journal entries go in `docs/journal/waves.md`,
   never in reference docs.
3. **Subtraction quota.** During the program, every wave must leave the
   scoreboard net-equal-or-better. After the program: any wave that adds a
   tool, response field, or doc section must remove or shrink something
   comparable, and must first show that improving an existing field or doc
   could not close the same gap.
4. **Trials measure tokens-to-outcome.** A trial's primary metrics are task
   success against its rubric and total context cost (tool-schema chars + doc
   chars fetched + response chars consumed, ÷4). A fix that removes a
   confusion but raises cold-start cost is a regression.
5. **No compatibility shims.** Pre-1.0 with zero external users: delete old
   names outright — no aliases, no deprecation wrappers, no dual code paths.
6. **No new routing fields.** When a trial agent gets lost, the allowed fixes
   are, in order: better state presentation in an existing field; a rewritten
   doc sentence; a merged/simplified response. A new field must replace at
   least one old field.
7. **Docs are reference, never journal.** No dated entries, timing
   measurements, or trial narratives in `docs/agent/`; that material goes to
   `docs/journal/`.
8. **Escalate to James** (pause the loop, write a handoff) for: storage schema
   changes; `rc:` ontology semantic changes; any budget loosening; a phase
   gate failing twice; anything that would weaken privacy/validation/staged
   conflict guarantees; anything irreversible.

Self-check each wave against the named anti-patterns: the Additive Reflex,
the Routing-Field Reflex, the Doc-Append Reflex, the Compat-Shim Reflex, the
Self-Referential Trial, and the Smallest-Fix Trap (definitions in doc 07).

Pause and report before broad storage migrations, public API breaks, surprising
container data exposure, or large semantic direction changes. Read-only data
available in the container is generally usable, but do not print anything marked
as secret or obviously credential-like.

## Start Here

Read these first when arriving cold:

1. `docs/agent/start-here.md` for the cold-start and post-compaction route.
2. `README.md` for project purpose, status, commands, and direction.
3. `ARCHITECTURE.md` for boundaries and near-term build order.
4. `docs/agent/graph-roles.md` and `docs/agent/workflow.md` when you need
   fuller operational graph conventions.

Use the DoxaBase MCP docs tools when available:

1. `doxabase.list_docs`
2. `doxabase.get_doc` with `doc_id="start_here"`
3. `doxabase.get_doc` with `doc_id="graph_roles"` when placement rules matter
4. `doxabase.get_doc` with `doc_id="context_slicing"` when retrieval scope matters
5. `doxabase.graph_overview`

## Daily Commands

The full pre-commit gate:

```bash
uv run pytest -q -n 16
uv run python tools/validate_rdf.py
uv run python tools/scoreboard.py --check
git diff --check
```

For focused work, run the relevant pytest file first, then the full gate before
finishing. Use serial pytest for one-off debugging when worker startup would
obscure local output.

## Working In The Codebase

- `doxabase/core.py` owns storage and graph behavior.
- `doxabase/mcp_tools.py` owns testable MCP-callable business logic.
- `doxabase/mcp_server.py` should stay thin.
- `docs/agent/` contains short agent-facing docs; register new docs in
  `doxabase/agent_docs.py`.
- `doxabase_design_docs/` and `ARCHITECTURE.md` hold broader direction.

Use type hints generously; they help both humans and agents understand graph
payloads, helper contracts, and return shapes. Keep MCP responses easy to
serialize with plain dicts, lists, strings, numbers, and booleans. Prefer
structured RDFLib, SQLite, and helper APIs over ad hoc text parsing.

Comments are welcome when they preserve useful context, for example graph
rationale, validation assumptions, data caveats, invariants, or why an apparently
simpler approach is not right here. Avoid comments that only restate obvious
Python syntax.

## Rules For Building Graphs With DoxaBase

- Do not write ordinary user/project facts to immutable seed graphs:
  `base_ontology` and `base_shapes`.
- Put project vocabulary/model terms in `ontology`.
- Put current best project/data facts in `map`.
- Put point-in-time or tentative findings in `observations`.
- Put syntheses over related observations, claims, or evidence in `patterns`.
- Put source/query/hash/sample support in `evidence`.
- Put project SHACL extensions in `shapes`.
- Put graph-change rationale, review-bundle metadata, and graph-count snapshots
  in `history`.

Project-specific vocabulary belongs in project namespaces, not
`ontology/rc_core.ttl`, unless it truly belongs in the shared Rich Canopy kernel.
Fixture graph IRIs under `https://richcanopy.org/graph/{role}` map to local graph
roles such as `map`, `ontology`, `observations`, `patterns`, and `evidence`.

The AIS and Polymarket fixtures are representative pressure tests, not full
mechanical conversions. The AIS fixture is intentionally reduced and should not
be treated as a full executable catalog.

Revision metadata and staged graph patch proposals exist. The current runtime
can apply one staged revision with conservative graph-state conflict checks, and
new staged revisions store snapshot rows for exact count/digest drift reporting.
Rich conflict handling, rebasing, and historical graph checkout/replay are not
implemented yet; use `list_graph_versions` for a read-only timeline over stored
graph snapshots. For the longer plan, see
`doxabase_design_docs/03-doxabase-v1-storage-schema.md` and the revision model
in `doxabase_design_docs/01-doxabase-v1-design-brief.md`.

## Repository Hygiene

Do not commit local capsule files such as `.doxabase.sqlite`, credentials, or
local credential notes unless explicitly asked. Be careful with untracked session
artifacts under `docs/agent/` and `examples/session-observations/`; include them
only when the user wants the observations preserved in git.

If changing fixture behavior, update tests and the relevant agent docs. If adding
new agent docs, update both `docs/agent/` and `doxabase/agent_docs.py`.

Commit messages should explain the rationale, not just the file touched. A short
body is helpful when the change affects graph semantics, fixture behavior,
validation, or agent workflows.

## Current Build Priorities

Suspended. The distillation program
(`doxabase_design_docs/07-distillation-program.md`) defines all build
priorities until its exit criteria are met. The former build axes (staged
conflict/rebase, richer profiling, query planning) resume, if at all, only
after the program's retrospective.

When touching promotion helpers, preserve agents' knowledge-graph reasoning. A
helper should draft and validate graph moves, not force every insight into an
existing template.
