# DoxaBase Agent Overview

DoxaBase is a local RDF memory capsule for data projects.

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
- `describe_graph_revision()` for compact review of history records.
- `describe_dataset()` for bounded table schema, layout, storage access, caveat, and provenance context.
- `record_observation()` for point-in-time findings and linked evidence.
- `record_claim_observation()` for structured observation, claim, evidence, and source-span capture.
- `record_pattern()` for syntheses that connect related findings to map targets.
- Map authoring helpers for current-best datasets, columns, caveats, storage
  access, and relationships.
- `record_graph_revision()` for history metadata about graph changes and review
  bundles.
- Agent-authored observation and pattern RDF for structured claims, source spans, confidence, and status.
- Stricter SHACL checks for observation, pattern, evidence, claim, and source-span resources.
- Non-secret storage access metadata for physical query planning.
- MCP tools for docs, overview, search, listing, dataset description,
  observation/history recording, import/export, validation, and fixture loading.

Important V1 limits:

- No context slicing yet.
- No staged revision/diff workflow yet.
- No full SPARQL endpoint.
- No direct query generation or execution helpers yet.
- No embedded LLM, semantic search, or embedding index.
- SHACL validation is explicit and diagnostic, not a commit gate.
