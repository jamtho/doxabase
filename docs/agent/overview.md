# DoxaBase Agent Overview

DoxaBase is a local RDF memory capsule for data projects.

If you are arriving cold or resuming after compaction, read `start_here` before
using this status overview.

The agent-facing contract is:

> The agent supplies semantic judgement; DoxaBase supplies graph mechanics.

DoxaBase stores named RDF graphs in a local SQLite file. It ships a small Rich Canopy base ontology under the `rc:` prefix and open SHACL shapes for basic validation. Client projects can extend the ontology freely with their own namespaces and RDF patterns.

Current implementation status:

- SQLite-backed named graph storage.
- Immutable shipped seed graphs: `base_ontology`, `base_shapes`.
- Mutable project graphs: `map`, `ontology`, `observations`, `patterns`, `evidence`, `shapes`, `history`.
- Turtle import into one graph.
- TriG import/export for graph roles.
- `graph_overview()`, `list_entities()`, and `validate_graph()`.
- `search()` for lexical retrieval over literal RDF claims.
- `describe_resource()` for type-aware retrieval workflows over RDF resources.
- `describe_pattern()` for compact handoff context around pattern syntheses.
- `list_graph_revisions()` for discovering staged, applied, and history records.
- `describe_graph_revision()` for compact review of history records.
- `describe_dataset()` for bounded table schema, row semantics, relationship, caveat, provenance, and linked-pattern context.
- `describe_profile_run()` for the profile observations on one dataset linked
  to one shared profile-run evidence resource.
- `describe_query_context()` for compact non-secret query-planning context,
  physical-metadata readiness, info/warning/error issues, and separate
  analytical caveat warnings.
- `describe_context_slice()` for route-explained dataset, pattern, and deep-lore graph slices.
- `record_observation()` for point-in-time findings and linked evidence.
- `record_dataset_profile()` for profile observations that may also update map
  row-count snapshots and linked profile patterns.
- `record_column_profile()` for column profile observations that may also
  update map column metadata and linked profile patterns.
- `record_profile_bundle()` for one dataset profile plus related column
  profiles from the same profiling pass.
- `record_claim_observation()` for structured observation, claim, evidence, and source-span capture.
- `record_claim_reconsideration()` for marking when later claims weaken,
  contradict, supersede, or refine earlier claims.
- `record_pattern()` for syntheses that connect related findings to map targets.
- Map authoring helpers for current-best datasets, columns, caveats, storage
  access, and relationships.
- `record_graph_revision()` for history metadata about graph changes and review
  bundles.
- `stage_graph_revision()`, `describe_staged_revision()`, and
  `export_staged_revision()` / `export_staged_revisions()` for reviewable graph
  patch proposals with structured validation diagnostics.
- `stage_systematisation()` for preserving alternative caller-authored RDF
  framings of a modelling hunch, with optional shared proposed context.
- `stage_pattern_promotion()` for staging caller-authored graph changes backed
  by existing patterns and their support links.
- `check_staged_revision_apply()` for read-only application diagnostics.
- `restage_staged_revision()` for refreshing stale staged proposals after
  count or digest drift conflicts.
- `apply_staged_revision()` for applying one staged revision after conservative
  graph-state conflict checks and preview validation.
- Agent-authored observation and pattern RDF for structured claims, source spans, confidence, and status.
- Stricter SHACL checks for observation, pattern, evidence, claim, and source-span resources.
- Non-secret storage access metadata for physical query planning.
- MCP tools for docs, overview, search, listing, dataset description,
  context slicing, observation/history recording, systematisation and
  pattern-promotion staging, import/export, validation, and fixture loading.

Important V1 limits:

- No rich staged revision semantic merge/rebase workflow or historical graph
  checkout/replay beyond the stored snapshot timeline yet.
- No full SPARQL endpoint.
- No direct query generation or execution helpers yet.
- No embedded LLM, semantic search, or embedding index.
- SHACL validation is explicit and diagnostic, not a commit gate.
