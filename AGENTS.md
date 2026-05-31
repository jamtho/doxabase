# Agent Guide

This repository is DoxyBase: a small local RDF memory capsule for data projects.
Agents supply semantic judgement; DoxyBase supplies storage, parsing, named graph
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

1. `README.md` for status, commands, and project direction.
2. `ARCHITECTURE.md` for boundaries and near-term build order.
3. `docs/agent/overview.md`, `docs/agent/graph-roles.md`, and `docs/agent/workflow.md`
   for operational graph conventions.

Use the DoxyBase MCP docs tools when available:

1. `doxybase.list_docs`
2. `doxybase.get_doc` with `doc_id="overview"`
3. `doxybase.get_doc` with `doc_id="graph_roles"`
4. `doxybase.graph_overview`

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

- `doxybase/core.py` owns storage and graph behavior.
- `doxybase/mcp_tools.py` owns testable MCP-callable business logic.
- `doxybase/mcp_server.py` should stay thin.
- `docs/agent/` contains short agent-facing docs; register new docs in
  `doxybase/agent_docs.py`.
- `doxybase_design_docs/` and `ARCHITECTURE.md` hold broader direction.

Use type hints generously; they help both humans and agents understand graph
payloads, helper contracts, and return shapes. Keep MCP responses easy to
serialize with plain dicts, lists, strings, numbers, and booleans. Prefer
structured RDFLib, SQLite, and helper APIs over ad hoc text parsing.

Comments are welcome when they preserve useful context, for example graph
rationale, validation assumptions, data caveats, invariants, or why an apparently
simpler approach is not right here. Avoid comments that only restate obvious
Python syntax.

## Rules For Building Graphs With DoxyBase

- Do not write ordinary user/project facts to immutable seed graphs:
  `base_ontology` and `base_shapes`.
- Put project vocabulary/model terms in `ontology`.
- Put current best project/data facts in `map`.
- Put point-in-time or tentative findings in `observations`.
- Put source/query/hash/sample support in `evidence`.
- Put project SHACL extensions in `shapes`.
- Use `history` for revision metadata when that feature exists.

Project-specific vocabulary belongs in project namespaces, not
`ontology/rc_core.ttl`, unless it truly belongs in the shared Rich Canopy kernel.
Fixture graph IRIs under `https://richcanopy.org/graph/{role}` map to local graph
roles such as `map`, `ontology`, `observations`, and `evidence`.

The AIS and Polymarket fixtures are representative pressure tests, not full
mechanical conversions. The AIS fixture is intentionally reduced and should not
be treated as a full executable catalog.

Graph version storage and revision workflows are planned but not implemented in
the current runtime. For the longer plan, see
`doxybase_design_docs/03-doxybase-v1-storage-schema.md` and the revision model
in `doxybase_design_docs/01-doxybase-v1-design-brief.md`.

## Repository Hygiene

Do not commit local capsule files such as `.doxybase.sqlite`, credentials, or
local credential notes unless explicitly asked. Be careful with untracked session
artifacts under `docs/agent/` and `examples/session-observations/`; include them
only when the user wants the observations preserved in git.

If changing fixture behavior, update tests and the relevant agent docs. If adding
new agent docs, update both `docs/agent/` and `doxybase/agent_docs.py`.

Commit messages should explain the rationale, not just the file touched. A short
body is helpful when the change affects graph semantics, fixture behavior,
validation, or agent workflows.

## Current Build Priorities

The near-term order is:

1. Add first-class observation and evidence recording.
2. Add lexical search over labels, comments, evidence summaries, and observation
   notes.
3. Add non-secret executable catalog metadata for physical layouts and storage
   access patterns.
4. Add graph slice/revision metadata and broader MCP context retrieval tools.
