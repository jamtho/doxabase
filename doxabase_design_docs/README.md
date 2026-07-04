# DoxaBase Design Docs

DoxaBase is a project under the broader Rich Canopy brand. Shared vocabulary terms should use the `rc:` IRI prefix.

This folder contains V1 implementation notes intended for a coding agent, especially Codex running GPT-5.5 xhigh.

## Files

- `01-doxabase-v1-design-brief.md` — product thesis, architecture, storage, validation, retrieval, and implementation guidance.
- `02-doxabase-v1-api-spec.md` — proposed Python/MCP API shape and semantics.
- `03-doxabase-v1-storage-schema.md` — SQLite-backed RDF-ish storage sketch.
- `04-doxabase-v2-backlog.md` — deferred ideas and future architecture notes.
- `05-rich-canopy-base-ontology.md` — base `rc:` ontology principles, graph placement, and initial data-modeling term families.
- `06-fresh-eyes-review-2026-07-03.md` — external design review of the V1 implementation: diagnosis of surface-area growth, interface inversion, and loop incentives.
- `07-distillation-program.md` — the active V1 → V1.5 distillation program: budgets, permanent loop rules, and phased work plan. Until its exit criteria are met, it supersedes the build priorities elsewhere in the repo.

## Ontology Seed Files

- `../ontology/rc_core.ttl` — draft immutable Rich Canopy base ontology seed graph.
- `../ontology/rc_shapes.ttl` — draft immutable open SHACL shape seed graph.
