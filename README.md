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
- `search_staged_patch_payloads()` for routing remembered staged-only terms in
  patch payloads back to their owning staged revisions.
- `project_brief()` for read-only frontier summaries, health tasks, and
  recommended next workflow tasks.
- `describe_resource()` for type-aware retrieval workflows over RDF resources.
- `describe_pattern()` for compact handoff context around pattern syntheses.
- `list_graph_revisions()` for discovering staged, applied, and history records.
- `describe_graph_revision()` for compact history review over revision records.
- `describe_revision_lineage()`, `list_resource_revisions()`, and
  `describe_resource_revision_lineage()` for staged/applied/history routing.
- Revision snapshot evidence and graph-snapshot inspection helpers for
  cross-capsule staged-review handoffs.
- `describe_dataset()` for bounded table schema, row semantics, relationship,
  caveat, provenance, and linked-pattern context.
- `describe_profile_run()` for profile observations on one dataset linked to one
  shared profile-run evidence resource.
- `draft_profile_map_updates()`, `stage_profile_map_updates()`, and
  `export_profile_insight_review_bundle()` for reviewable profile-to-map
  promotion workflows.
- `describe_query_context()` for compact non-secret query-planning context,
  physical-metadata readiness, info/warning/error issues, and separate
  analytical caveat warnings.
- `draft_query_plan()` for non-executed query handoff planning over reviewed
  storage/layout/path context.
- `describe_context_slice()` for route-explained dataset, pattern, and deep-lore
  graph slices.
- `record_observation()` for first-class observation and evidence resources.
- `record_claim_observation()` for common observation, claim, evidence, and source-span capture.
- `record_query_result()` for preserving external query results or failures.
- `record_pattern()` for syntheses that connect related findings to map targets.
- `record_dataset_profile()` for bundling a profile observation, including
  optional observed value-frequency pairs and scalar metrics, with an optional
  map row-count snapshot and agent-authored profile pattern.
- `record_column_profile()` for bundling a column profile observation with
  optional observed value-frequency pairs, scalar metrics, map column metadata,
  and an agent-authored profile pattern.
- `record_profile_bundle()` for recording one dataset profile plus related
  column profiles from the same profiling pass, with shared run metadata,
  sample context, and optional shared evidence.
- `record_profiled_parquet_table()` for recording reviewed Parquet schema,
  storage/layout metadata, and aggregate profile observations together without
  reading the Parquet files.
- `record_profile_to_capsule_manifest()` for applying a reviewed
  `doxabase.profile_to_capsule_manifest.v1` ingestion manifest with optional
  caveats, multiple profiled Parquet tables, optional analysis views, and
  reviewed aggregate domain-network profiles.
- `python -m doxabase.parquet_manifest` for generating a reviewable
  profile-to-capsule manifest scaffold from local Parquet footer/schema
  metadata when optional `pyarrow` is installed.
- `python -m doxabase.profile_manifest_merge` for merging reviewed aggregate
  profile facts into that scaffold without reading raw rows.
- `record_analysis_packet()` for preserving reviewed analysis-view links,
  aggregate artifact locators, visual metadata, follow-up tasks, and optional
  pattern support as one graph-native handoff node.
- `python -m doxabase.analysis_packet` for applying a reviewed
  `doxabase.analysis_packet_manifest.v1` JSON handoff, or scaffolding one from
  sidecar locators with optional review-only Markdown `CREATE VIEW` extraction.
- Map authoring helpers for current-best datasets, columns, caveats, storage
  access, physical layouts, partition schemes, and relationships.
- `record_graph_revision()` for history metadata about graph changes and review
  bundles.
- `describe_assertion_support()` and `draft_map_assertion_change()` for
  read-only assertion review before staging a single map assertion change.
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
- `describe_applied_revision_diff()` for stored before/after snapshot diffs on
  applied staged revision events, with exact triple arrays opt-in.
- `describe_graph_version_diff()` for comparing a stored graph-version snapshot
  with another stored snapshot or the current live graph.
- `draft_staged_revision_rebase()` for read-only repair planning when a staged
  revision routes to repair/replace rather than mechanical restage.
- `plan_staged_revision_recovery()` and `restage_staged_revisions()` for
  mixed staged-frontier recovery and batch restage classification.
- `restage_staged_revision()` for refreshing a stale staged proposal against
  current graph state while preserving a link to the older proposal.
- Row-level staged graph snapshot storage for exact count/digest drift reporting
  in apply checks and staged-review Markdown.
- Privacy/export hygiene preflight and scanning for graph, TriG, revision
  snapshot, staged-review, and handoff exports.
- Agent-authored observation and pattern RDF vocabulary for structured claims,
  source spans, confidence, and status.
- Stricter SHACL validation for observation/pattern/evidence/claim resources.
- Non-secret storage access metadata for physical query planning.
- Draft Rich Canopy `rc:` base ontology and open SHACL shapes.
- Representative AIS and Polymarket fixtures converted from the Manifest prototype.
- Thin MCP server for agent use.
- Agent-facing docs exposed through MCP tools.

Not implemented yet:

- Full staged revision semantic merge/rebase and durable graph version browsing
  beyond the current recovery planning, restage, lineage, and snapshot-evidence
  workflows.
- Query execution or full SQL generation. Current query helpers produce
  non-executed planning handoffs and record external results/failures.
- Full SPARQL endpoint.

## Layout

- `doxabase_design_docs/` - V1 design brief, API sketch, storage sketch, and ontology notes.
- `docs/agent/` - short operational docs exposed through MCP.
- `docs/agent/field-trials.md` - playbook for running bounded sub-agent product trials.
- `doxabase/` - Python package.
- `ontology/rc_core.ttl` - draft immutable `rc:` base ontology seed graph.
- `ontology/rc_shapes.ttl` - draft immutable open SHACL shape seed graph.
- `examples/manifest-prototype-rc/` - representative AIS and Polymarket fixtures converted from Manifest vocabulary to `rc:`.
- `examples/local-csv-query-smoke.py` - scratch local CSV query-planning and
  result-capture smoke workflow.
- `examples/missing-metadata-query-repair-smoke.py` - staged storage/layout
  repair workflow from missing physical metadata to a query-plan handoff.
- `examples/query-evidence-storage-overlay-smoke.py` - query-result evidence
  overlay workflow from a scanned local CSV to staged storage/layout metadata
  and a ready query-plan handoff.
- `examples/ais-query-overlay-smoke.py` - scratch AIS DailyIndex overlay and
  stale-link repair workflow for the documented query-planning pressure test.
- `examples/profile-frontier-workflow.py` - scratch workflow for profile-derived map updates and staged-frontier review.
- `examples/profile-to-capsule-cookbook.py` - maintained cookbook that composes
  table map bundles, profile bundles, logical analysis views, and
  recovery-complete handoff verification from reviewed aggregate facts.
- `examples/rich-profile-manifest-smoke.py` - scaffold-plus-external-profile
  manifest route that records reviewed aggregate profile facts without local
  row scanning.
- `examples/analysis-packet-manifest-smoke.py` - reviewed analysis-packet JSON
  manifest route for graph-native handoffs over logical views, artifacts,
  query recipes, and follow-up tasks.
- `examples/staged-semantic-repair-smoke.py` - scratch semantic same-slot
  staged-revision repair workflow after applying one competing alternative.
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
uv run pytest -q -n 16
```

For focused debugging, run the relevant test file or node serially first, then
use the parallel full-suite command before finishing. On the current July 1,
2026 YOLO container, `-n 16` measured faster than `-n auto`; remeasure if the
visible CPU count or cgroup limits change.

Run the smallest end-to-end example:

```bash
uv run python examples/first-workflow.py
```

It creates a scratch capsule under `/tmp`, loads the bundled fixtures, prints a
few table/search/query-readiness cues, records one observation, and validates
the graph. Use `examples/profile-frontier-workflow.py` after that to exercise
profile-derived map updates and staged-frontier recovery. Use
`examples/local-csv-query-smoke.py` when you want a no-network local
query-planning and result-capture smoke test. Use
`examples/missing-metadata-query-repair-smoke.py` when you want to exercise
staged query metadata repair from `missing_storage_access` through
`missing_physical_layout` to a ready local CSV query handoff. Use
`examples/query-evidence-storage-overlay-smoke.py` when you want to exercise
the evidence-first route from `record_query_result` through
`draft_query_evidence_storage_overlay` and staged application to a ready local
CSV query handoff. Use
`examples/ais-query-overlay-smoke.py` when you want to exercise the reduced AIS
fixture's path from reviewed metadata overlay through stale partition-link
repair to a non-executed DuckDB handoff. Use
`examples/rich-profile-manifest-smoke.py` when you want to check the route from
a Parquet footer/schema scaffold plus reviewed external aggregate profile facts
to a capsule. Use
`examples/analysis-packet-manifest-smoke.py` when you want to check the reviewed
analysis-packet JSON manifest route for sidecar-to-graph handoffs. Use
`examples/staged-semantic-repair-smoke.py` when you want a compact semantic
same-slot rebase loop. Use `examples/adversarial-field-trial.py` when you want
a more demanding staged-revision and systematisation exercise.

The examples keep stable `/tmp/doxabase-*` paths by default for easy manual
inspection. When running examples concurrently, set
`DOXABASE_EXAMPLE_RUN_ROOT=/tmp/some-run-root`; each example will write under a
name-specific subdirectory there instead of sharing the default paths.

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

Use `DoxaBase(path)` to reopen an existing capsule when schema, seed, and
search-index maintenance writes are acceptable. Use
`DoxaBase.open_readonly(path)` for non-mutating inspection of copied, mounted,
or permission-restricted capsules. `DoxaBase.create(...)` creates or replaces a
capsule depending on `overwrite`.

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
4. `doxabase.project_brief` for a read-only summary of datasets and active
   review queues
   (`health_tasks`, `next_best_expansion`, and `full_frontier_expansion` are the
   key fields when a bounded first pass hides work)
5. `doxabase.plan_staged_revision_recovery` when `project_brief` reports
   `staged_frontier_review`
6. `doxabase.graph_overview`
7. `doxabase.search` for remembered terms, caveats, observations, or evidence
   and `doxabase.search_staged_patch_payloads` when the term may live only in a
   staged patch proposal
8. `doxabase.list_entities` with `type="rc:Table"` and `graph="map"`
9. `doxabase.describe_dataset` with a table IRI from `list_entities`
10. `doxabase.describe_profile_run` when a profile-summary candidate evidence
   IRI needs full profile-run retrieval
11. `doxabase.describe_query_context` when you need storage, layout, path,
   partition, caveat, and readiness context before planning a query
12. `doxabase.describe_context_slice` when a route-explained graph slice would
   help a deeper handoff or review
13. `doxabase.describe_pattern` for pattern handoff context after finding an
   `rc:Pattern`
14. `doxabase.describe_resource` for typed resources such as `rc:Claim`,
   `rc:Evidence`, or `rc:SourceSpan`
15. `doxabase.list_graph_revisions` when you need to find staged, applied, or
    historical revision records before inspecting a specific one
16. `doxabase.record_observation` for useful point-in-time findings
17. `doxabase.record_query_result` after an external query attempt produces a
    result or failure worth preserving
18. `doxabase.record_claim_observation` for structured claim observations
19. `doxabase.record_dataset_profile` for profile outputs that should write an
    observation and optionally update map/pattern context together
20. `doxabase.record_column_profile` for column profile outputs that should
    write an observation and optionally update map/pattern context together
21. `doxabase.record_profile_bundle` for a dataset profile plus related column
    profiles from one profiling pass
22. `doxabase.record_profiled_parquet_table` when reviewed Parquet schema,
    storage/layout metadata, and aggregate profiles should be recorded together
23. `doxabase.record_profile_to_capsule_manifest` when a reviewed structured
    ingestion manifest should record caveats, profiled tables, analysis views,
    and reviewed aggregate domain-network profiles together without reading
    files
24. `python -m doxabase.parquet_manifest` when local Parquet footer/schema
    metadata should become a reviewable profile-to-capsule manifest scaffold,
    including S3/MinIO route options when local footer copies represent an
    object-store source
25. `python -m doxabase.profile_manifest_merge` when reviewed aggregate
    profile facts should be merged into that scaffold without raw-row I/O
26. `doxabase.record_analysis_packet` when reviewed analysis-view links,
    aggregate artifacts, visuals, and follow-up tasks need one handoff seed
27. `python -m doxabase.analysis_packet` when that reviewed packet already
    lives as a local `doxabase.analysis_packet_manifest.v1` JSON file, or when
    sidecar files need a reviewable scaffold before graph-native recording
28. `doxabase.record_pattern` for syntheses over related findings
29. `doxabase.stage_graph_revision` for reviewable additions/removals that
    should not be applied yet, including validation diagnostics for failed
    previews
30. `doxabase.stage_systematisation` for alternative RDF framings of one
    modelling hunch, optionally with shared proposed context
31. `doxabase.stage_pattern_promotion` for pattern-supported graph changes that
    should remain reviewable before becoming durable structure
32. `doxabase.describe_staged_revision` when reviewing a staged patch proposal
33. `doxabase.check_staged_revision_apply` before turning a staged proposal
    into durable graph state
34. `doxabase.draft_staged_revision_rebase` when a staged proposal routes to
    repair or replacement before a successor should be authored
35. `doxabase.restage_staged_revision` when count or digest drift made a
    still-useful staged proposal stale
36. `doxabase.describe_applied_revision_diff` when an applied staged revision
    needs stored before/after snapshot diff counts or opt-in exact triples
37. `doxabase.describe_graph_version_diff` when a stored graph version should
    be compared with another stored version or the current live graph
38. `doxabase.apply_staged_revision` when a staged proposal should become
    durable graph state after conflict and validation checks
39. `doxabase.record_map_dataset` and related map helpers for current-best facts
40. `doxabase.validate_graph` with `scope="all"`
41. `doxabase.export_preflight` before unattended or shareable RDF/snapshot
    exports, so scanner-clean and block decisions are explicit before choosing
    paths
42. `doxabase.export_trig` when you need a named-graph project review bundle
43. `doxabase.record_graph_revision` when the bundle/change rationale should be
    preserved in `history`
44. `doxabase.describe_graph_revision` when reviewing a history record

Use `doxabase.load_example_fixtures` only in a fresh scratch or example capsule,
after confirming you are not attached to a real project capsule.

For the maintained MCP surface, read `docs/agent/mcp-tools.md` or call
`doxabase.list_docs` and `doxabase.get_doc(doc_id="mcp_tools")`. The server
instructions also summarize the current tool families at startup. Avoid treating
the first-call route above as an exhaustive tool list.

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
3. Deepen storage-metadata-assisted query planning and execution handoff
   helpers.
4. Consider semantic or hybrid search later, after the lexical RDF search surface has settled.
