# DoxaBase

DoxaBase is a local, agent-operated RDF memory capsule for data projects.

The core idea is that useful knowledge about data rarely arrives fully
systematised. Agents and humans notice things while working: row-count facts,
schema caveats, source quirks, query results, suspected joins, broken
assumptions, and interpretations that may or may not hold tomorrow. DoxaBase
gives those claims somewhere durable to live as RDF, without requiring every
claim to be promoted immediately into stable project structure.

It is built around an observation-pattern-map loop:

1. **Observation**: record point-in-time or source-scoped findings, with
   evidence, as RDF resources.
2. **Pattern**: synthesize related findings into explicit rationale that can
   explain why something looks durable or important.
3. **Systematisation**: consolidate useful patterns and findings into a more durable
   project map, ontology terms, shapes, caveats, and revision history.

The graph is deliberately open-ended: projects can record arbitrary RDF claims
about datasets. At the same time, DoxaBase ships a small Rich Canopy `rc:`
ontology for common dataset concepts such as assets, tables, columns, physical
layouts, caveats, observations, evidence, and provenance. That shared structure
is meant to make knowledge portable across projects without forcing every
project into a closed schema.

Another image for the project is the handover conversation you wish came with
every complex dataset. When you inherit data, you need more than field names:
you want the hidden facts, local caveats, awkward history, and the mindset
behind how the dataset was created. DoxaBase tries to make that lore cheap to
transfer one-to-many: once a human or agent has worked something out, the claim,
evidence, caveat, and rationale can be recorded for every future reader.

The implementation is intentionally small: a Python package backed by a local
SQLite file, with RDFLib handling parsing and pySHACL handling explicit
validation. There is no embedded LLM in the library. Agents supply semantic
judgement; DoxaBase supplies graph mechanics, storage, retrieval affordances,
and validation.

## How To Read This Project

For a human overview, start with this README, then read `ARCHITECTURE.md` and
the design notes in `doxabase_design_docs/`.

For a fresh agent, or an agent resuming after compaction, start with
`docs/agent/start-here.md`. It gives the fastest route through the current
capsule: which docs to read, which graph-inspection calls to make first, where
different kinds of claims belong, and which runtime gotchas matter for
sub-agent field trials.

For exact operational details, use the short docs in `docs/agent/`, especially
`graph-roles.md`, `workflow.md`, `observation-recording.md`, `patterns.md`,
`map-authoring.md`, `staged-revisions.md`, and `field-trials.md`.

## Current Status

Implemented:

- SQLite-backed named graph capsule.
- Immutable shipped seed graphs: `base_ontology` and `base_shapes`.
- Mutable project graphs: `map`, `ontology`, `observations`, `patterns`,
  `evidence`, `shapes`, and `history`.
- Turtle import into one graph.
- TriG import/export for graph roles.
- `graph_overview()`, `list_entities()`, and `validate_graph()`.
- `search()` for lexical retrieval over literal RDF claims.
- `describe_resource()` for type-aware retrieval workflows over RDF resources.
- `describe_pattern()` for compact handoff context around pattern syntheses.
- `list_graph_revisions()` for discovering staged, applied, and history records.
- `describe_graph_revision()` for compact history review over revision records.
- `describe_dataset()` for bounded table schema, row semantics, relationship,
  caveat, provenance, and linked-pattern context.
- `describe_query_context()` for compact non-secret query-planning context,
  readiness, and an `issues` list for missing or risky metadata.
- `describe_context_slice()` for route-explained dataset, pattern, and deep-lore
  graph slices.
- `record_observation()` for first-class observation and evidence resources.
- `record_claim_observation()` for common observation, claim, evidence, and source-span capture.
- `record_pattern()` for syntheses that connect related findings to map targets.
- `record_dataset_profile()` for bundling a profile observation, including
  optional observed value-frequency pairs and scalar metrics, with an optional
  map row-count snapshot and agent-authored profile pattern.
- `record_column_profile()` for bundling a column profile observation with
  optional observed value-frequency pairs, scalar metrics, map column metadata,
  and an
  agent-authored profile pattern.
- Map authoring helpers for current-best datasets, columns, caveats, storage
  access, physical layouts, partition schemes, and relationships.
- `record_graph_revision()` for history metadata about graph changes and review
  bundles.
- `stage_graph_revision()` for reviewable additions/removals with stance,
  preview counts, validation, and structured SHACL diagnostics, without
  applying the patch.
- `stage_map_assertion_change()` for reviewable single-assertion map changes
  with pre-change support context and a compact judgement panel.
- `stage_systematisation()` for staging one or more caller-authored RDF framings
  of the same modelling hunch, with optional shared proposed context, as
  reviewable alternatives.
- `stage_pattern_promotion()` for staging caller-authored graph changes
  supported by existing patterns while preserving support links and anchors.
- `apply_staged_revision()` for applying one staged revision after conservative
  graph-state conflict checks and preview validation, while recording an applied
  revision event in history.
- `restage_staged_revision()` for refreshing a stale staged proposal against
  current graph state while preserving a link to the older proposal.
- Agent-authored observation and pattern RDF vocabulary for structured claims,
  source spans, confidence, and status.
- Stricter SHACL validation for observation/pattern/evidence/claim resources.
- Non-secret storage access metadata for physical query planning.
- Draft Rich Canopy `rc:` base ontology and open SHACL shapes.
- Representative AIS and Polymarket fixtures converted from the Manifest prototype.
- Thin MCP server for agent use.
- Agent-facing docs exposed through MCP tools.

Not implemented yet:

- Full staged revision semantic conflict resolution, rebase, and graph version
  storage.
- Query generation or execution helpers.
- Full SPARQL endpoint.

## Layout

- `doxabase_design_docs/` - V1 design brief, API sketch, storage sketch, and ontology notes.
- `docs/agent/` - short operational docs exposed through MCP.
- `docs/agent/field-trials.md` - playbook for running bounded sub-agent product trials.
- `doxabase/` - Python package.
- `ontology/rc_core.ttl` - draft immutable `rc:` base ontology seed graph.
- `ontology/rc_shapes.ttl` - draft immutable open SHACL shape seed graph.
- `examples/manifest-prototype-rc/` - representative AIS and Polymarket fixtures converted from Manifest vocabulary to `rc:`.
- `examples/adversarial-field-trial.py` - tiny scratch-capsule trial for checking the docs and staging workflow.
- `tests/` - parser, validation, capsule, and MCP helper tests.
- `tools/validate_rdf.py` - parser, term-definition, and SHACL validation checks.
- `ARCHITECTURE.md` - project architecture and implementation notes for future agents.

## Development

Set up the uv environment:

```bash
uv sync
```

Run the RDF validation script:

```bash
uv run python tools/validate_rdf.py
```

Run tests:

```bash
uv run pytest
```

## Python Capsule Example

```python
from doxabase import DoxaBase

db = DoxaBase.create(".doxabase.sqlite", overwrite=True)
db.import_trig("examples/manifest-prototype-rc/ais.trig")
db.import_trig("examples/manifest-prototype-rc/polymarket.trig")

overview = db.graph_overview()
tables = db.list_entities(type="rc:Table", graph="map")
dataset = db.describe_dataset(tables.entities[0].iri)
matches = db.search("MMSI vessel", graph="map")
observation = db.record_observation(
    summary="AIS daily broadcasts were inspected during setup.",
    observed_asset=dataset.iri,
    evidence_summary="Example observation recorded from the README workflow.",
)
validation = db.validate_graph(scope="all")
```

Use `DoxaBase(path)` to reopen an existing capsule. `DoxaBase.create(...)`
creates or replaces a capsule depending on `overwrite`.

The capsule seeds immutable `base_ontology` and `base_shapes` graphs from
`ontology/rc_core.ttl` and `ontology/rc_shapes.ttl`. Project imports can write
to mutable graph roles such as `map`, `ontology`, `observations`, `patterns`,
`evidence`, `shapes`, and `history`.

## MCP Server

Run the stdio MCP server:

```bash
uv run python -m doxabase.mcp_server --capsule .doxabase.sqlite
```

Useful first tool calls for an agent:

1. `doxabase.list_docs`
2. `doxabase.get_doc` with `doc_id="start_here"`
3. `doxabase.get_doc` with `doc_id="graph_roles"` when graph placement rules matter
4. `doxabase.load_example_fixtures`
5. `doxabase.graph_overview`
6. `doxabase.search` for remembered terms, caveats, observations, or evidence
7. `doxabase.list_entities` with `type="rc:Table"` and `graph="map"`
8. `doxabase.describe_dataset` with a table IRI from `list_entities`
9. `doxabase.describe_query_context` when you need storage, layout, path,
   partition, caveat, and readiness context before planning a query
10. `doxabase.describe_context_slice` when a route-explained graph slice would
   help a deeper handoff or review
11. `doxabase.describe_pattern` for pattern handoff context after finding an
   `rc:Pattern`
12. `doxabase.describe_resource` for typed resources such as `rc:Claim`,
   `rc:Evidence`, or `rc:SourceSpan`
13. `doxabase.list_graph_revisions` when you need to find staged, applied, or
    historical revision records before inspecting a specific one
14. `doxabase.record_observation` for useful point-in-time findings
15. `doxabase.record_claim_observation` for structured claim observations
16. `doxabase.record_dataset_profile` for profile outputs that should write an
    observation and optionally update map/pattern context together
17. `doxabase.record_column_profile` for column profile outputs that should
    write an observation and optionally update map/pattern context together
18. `doxabase.record_pattern` for syntheses over related findings
19. `doxabase.stage_graph_revision` for reviewable additions/removals that
    should not be applied yet, including validation diagnostics for failed
    previews
20. `doxabase.stage_systematisation` for alternative RDF framings of one
    modelling hunch, optionally with shared proposed context
21. `doxabase.stage_pattern_promotion` for pattern-supported graph changes that
    should remain reviewable before becoming durable structure
22. `doxabase.describe_staged_revision` when reviewing a staged patch proposal
23. `doxabase.check_staged_revision_apply` before turning a staged proposal
    into durable graph state
24. `doxabase.restage_staged_revision` when count or digest drift made a
    still-useful staged proposal stale
25. `doxabase.apply_staged_revision` when a staged proposal should become
    durable graph state after conflict and validation checks
26. `doxabase.record_map_dataset` and related map helpers for current-best facts
27. `doxabase.validate_graph` with `scope="all"`
28. `doxabase.export_trig` when you need a named-graph project review bundle
29. `doxabase.record_graph_revision` when the bundle/change rationale should be
    preserved in `history`
30. `doxabase.describe_graph_revision` when reviewing a history record

Current MCP tools:

- `doxabase.list_docs`
- `doxabase.get_doc`
- `doxabase.graph_overview`
- `doxabase.search`
- `doxabase.list_entities`
- `doxabase.describe_resource`
- `doxabase.describe_pattern`
- `doxabase.describe_graph_revision`
- `doxabase.list_graph_revisions`
- `doxabase.describe_staged_revision`
- `doxabase.describe_dataset`
- `doxabase.describe_query_context`
- `doxabase.describe_context_slice`
- `doxabase.record_observation`
- `doxabase.record_claim_observation`
- `doxabase.record_claim_reconsideration`
- `doxabase.record_pattern`
- `doxabase.record_dataset_profile`
- `doxabase.record_column_profile`
- `doxabase.record_map_dataset`
- `doxabase.record_map_column`
- `doxabase.record_map_caveat`
- `doxabase.record_map_storage_access`
- `doxabase.record_map_physical_layout`
- `doxabase.record_map_partition_scheme`
- `doxabase.record_map_relationship`
- `doxabase.import_trig`
- `doxabase.export_graph`
- `doxabase.export_staged_revision`
- `doxabase.export_staged_revisions`
- `doxabase.export_trig`
- `doxabase.record_graph_revision`
- `doxabase.stage_graph_revision`
- `doxabase.stage_systematisation`
- `doxabase.stage_pattern_promotion`
- `doxabase.check_staged_revision_apply`
- `doxabase.restage_staged_revision`
- `doxabase.apply_staged_revision`
- `doxabase.load_example_fixtures`
- `doxabase.validate_graph`

## Graph Roles

Immutable seed graphs:

- `base_ontology`: shipped Rich Canopy vocabulary.
- `base_shapes`: shipped open SHACL shapes.

Mutable project graphs:

- `ontology`: project/client vocabulary and model terms.
- `map`: current best structured project/data map.
- `observations`: point-in-time and tentative findings.
- `evidence`: source/query/hash/sample support.
- `patterns`: syntheses over related observations, claims, or evidence.
- `shapes`: project/client SHACL shapes.
- `history`: revision metadata, graph-count snapshots, and consolidation rationale.

Logical includes:

- `ontology` means `base_ontology + ontology`.
- `shapes` means `base_shapes + shapes`.

## Project Direction

The next useful implementation steps are:

1. Add fuller staged semantic conflict/rebase/version workflows.
2. Add deeper profiling helpers and field-tested metric recipes.
3. Consider query-planning helpers that consume storage access metadata.
4. Consider semantic or hybrid search later, after the lexical RDF search surface has settled.
