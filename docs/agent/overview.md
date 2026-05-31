# DoxyBase Agent Overview

DoxyBase is a local RDF memory capsule for data projects.

The agent-facing contract is:

> The agent supplies semantic judgement; DoxyBase supplies graph mechanics.

DoxyBase stores named RDF graphs in a local SQLite file. It ships a small Rich Canopy base ontology under the `rc:` prefix and open SHACL shapes for basic validation. Client projects can extend the ontology freely with their own namespaces and RDF patterns.

Current implementation status:

- SQLite-backed named graph storage.
- Immutable shipped seed graphs: `base_ontology`, `base_shapes`.
- Mutable project graphs: `map`, `ontology`, `observations`, `evidence`, `shapes`, `history`.
- Turtle import into one graph.
- TriG import into graph roles.
- `graph_overview()`, `list_entities()`, and `validate_graph()`.
- `describe_dataset()` for bounded table schema, layout, caveat, and provenance context.
- MCP tools for docs, overview, listing, dataset description, import, validation, and fixture loading.

Important V1 limits:

- No context slicing yet.
- No revision/diff workflow yet.
- No full SPARQL endpoint.
- No embedded LLM or semantic search.
- SHACL validation is explicit and diagnostic, not a commit gate.
