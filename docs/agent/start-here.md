# Start Here

DoxaBase is a local RDF memory capsule for data projects: one SQLite file
holding named graphs of project knowledge — current-best facts (`map`),
dated findings (`observations`), syntheses (`patterns`), supporting
`evidence`, vocabulary (`ontology`), SHACL `shapes`, and change rationale
(`history`). You supply semantic judgement; DoxaBase supplies storage,
validation, staged change, and privacy scanning. It never executes your
queries and never calls an LLM.

## First Calls

1. `doxabase.project_brief` — capsule state: counts, dataset one-liners,
   **gates** (what is blocked and the one call that inspects each blocker),
   queues of pending work, up to five suggestions.
2. `doxabase.search` — lexical search over graph literals; the fastest
   route to a specific fact, caveat, or resource.
3. `doxabase.describe_resource` — everything asserted about one IRI.
4. `doxabase.describe_dataset` — columns, caveats, storage, relationships
   for one dataset.
5. `doxabase.get_context_graph` — a bounded, profile-shaped RDF slice
   (TriG) around seed IRIs, for when you need the actual statements.

Respect gates before mutating or exporting; read-only inspection is always
safe. How to reason about gates, the observation → pattern → map ladder,
profiles, and query handoffs: read the `working_the_capsule` doc. Envelope
rules (absent == null == empty, truncation fields, suggestion shape):
`response_conventions`.

## Graph Placement Cheat Sheet

- Current best project/data facts → `map`
- Point-in-time or tentative findings → `observations`
- Syntheses over related findings → `patterns`
- Source/query/hash/sample support → `evidence`
- Project vocabulary/model terms → `ontology`
- Project SHACL extensions → `shapes`
- Change rationale, review bundles, snapshots → `history`
- Never write to `base_ontology` / `base_shapes` (immutable seeds)

Fixture graph IRIs under `https://richcanopy.org/graph/{role}` map to these
roles. Observations must link at least one named evidence resource or
SHACL validation will flag them.

## Recording

- `record_observation` for findings (attach evidence sources);
  `record_observation(kind="claim")` for structured claims;
  `record_claim_reconsideration` to weaken, contradict, supersede, or
  refine — never delete.
- `record_pattern` to synthesize related observations. Note: an
  `evidence_summary` requires `evidence_sources` or `source_path`.
- New current-best facts: `record_map_fact`. Changes to existing map facts
  go through staged revisions: `stage_revision` → check
  (`apply_staged_revision(dry_run=true)`) → `apply_staged_revision` →
  `validate_graph(scope="all")`. Rationale fields are for the next agent.

## Topic Docs

Fetch with `doxabase.get_doc` (`section=` for a slice, cheap): graph roles
(`graph_roles`), observations (`observation_recording`), patterns
(`patterns`), map authoring (`map_authoring`), staged revisions
(`staged_revisions`), revision history (`revisions`), profiling
(`profiling`), systematisation (`systematisation`), query planning
(`query_planning`), storage metadata (`executable_catalog`), context slices
(`context_slicing`), search (`lexical_search`), analysis packets
(`analysis_packets`), field trials (`field_trials`). Every tool's
parameters and per-kind spec fields: `mcp_tools` (generated).

Repo direction and loop rules live in `AGENTS.md` and
`doxabase_design_docs/07-distillation-program.md`, not in capsule docs.
