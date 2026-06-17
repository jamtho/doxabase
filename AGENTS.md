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

Run the RDF asset validation script:

```bash
uv run python tools/validate_rdf.py
```

Run tests:

```bash
uv run pytest
```

For focused work, run the relevant pytest file first, then the full suite before
finishing.

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
Rich conflict handling, rebasing, and durable graph version browsing beyond
those staged snapshots are not implemented yet. For the longer plan, see
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

The near-term order is:

1. Add fuller staged conflict/rebase/version workflows.
2. Add richer profile metrics and profiling helpers that can write map facts,
   observations, and patterns together.
3. Add query-planning helpers that consume storage access metadata.

When extending promotion helpers, preserve agents' knowledge-graph reasoning. A
helper should draft and validate graph moves, not force every insight into an
existing template. Test it with at least one awkward systematisation that may
need a project vocabulary term, ontology extension, or competing RDF framings.
