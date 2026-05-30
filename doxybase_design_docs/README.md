# DoxyBase Design Docs

DoxyBase is a project under the broader Rich Canopy brand. Shared vocabulary terms should use the `rc:` IRI prefix.

This folder contains V1 implementation notes intended for a coding agent, especially Codex running GPT-5.5 xhigh.

## Files

- `01-doxybase-v1-design-brief.md` — product thesis, architecture, storage, validation, retrieval, and implementation guidance.
- `02-doxybase-v1-api-spec.md` — proposed Python/MCP API shape and semantics.
- `03-doxybase-v1-storage-schema.md` — SQLite-backed RDF-ish storage sketch.
- `04-doxybase-v2-backlog.md` — deferred ideas and future architecture notes.
- `05-rich-canopy-base-ontology.md` — base `rc:` ontology principles, graph placement, and initial data-modeling term families.

## Ontology Seed Files

- `../ontology/rc_core.ttl` — draft immutable Rich Canopy base ontology seed graph.
- `../ontology/rc_shapes.ttl` — draft immutable open SHACL shape seed graph.
