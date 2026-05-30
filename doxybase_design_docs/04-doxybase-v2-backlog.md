# DoxyBase V2 Backlog

These are deliberate deferrals from V1.

## Retrieval

- Full retrieval provenance by phase.
- Per-phase accounting: triples/nodes added by each step.
- Configurable policy language.
- Embedding/hybrid semantic search.
- Adaptive retrieval policies.
- Continuation/pagination for large graph slices.
- Query-plan explanations.
- Richer graph-shape statistics.

## Validation and Transactions

- Staged graph revision sessions:

```text
begin_revision()
apply_change()
apply_change()
validate_revision()
commit_revision()
```

- SHACL-at-commit policies.
- Validation scopes and branches.
- Validation failure graph.
- Rollback API.
- Migration support for ontology refactors.

## RDF and Graph Backend

- TriG-first multi-graph slices.
- Graph overview as RDF/VoID-style description.
- JSON-LD support.
- Oxigraph backend.
- SPARQL endpoint or controlled SPARQL query support.
- More complete named graph semantics.

## Agent Workflows

- Agent debate / critic workflow.
- Multiple agents reviewing graph revisions.
- Automatic sleep-style consolidation recipes.
- Proposal/rationale packs.
- Human review mode.
- Multi-user governance.

## Product / Operational

- Hosted service option.
- Project-level access control.
- Larger-scale graph storage.
- UI for graph overview, revisions, validation failures, and ontology churn.
