# DoxaBase Agent Overview

DoxaBase is a local RDF memory capsule for data projects: one SQLite file of
named graphs holding a project's durable knowledge. The contract:

> The agent supplies semantic judgement; DoxaBase supplies graph mechanics.

If you are arriving cold or resuming after compaction, read `start_here`
first, then `working_the_capsule` for how to reason about gates, the
observation → pattern → map ladder, profiles, and query handoffs.

## What Exists

- SQLite-backed named graph storage with immutable seed graphs
  (`base_ontology`, `base_shapes`) and mutable project graphs (`map`,
  `ontology`, `observations`, `patterns`, `evidence`, `shapes`, `history`).
- 25 MCP tools: orientation reads (`project_brief`, `graph_overview`,
  `search`, `list_entities`), bounded describers (`describe_resource`,
  `describe_dataset`, `describe_query_context`, `describe_revision`,
  `list_revisions`), route-explained context slices (`get_context_graph`),
  kind-dispatched recorders (`record_observation`, `record_profile`,
  `record_map_fact`, `record_pattern`, `record_claim_reconsideration`,
  `record_graph_revision`), the staged-change family (`stage_revision`,
  `apply_staged_revision`, `restage_staged_revision`,
  `plan_staged_revision_recovery`), privacy-gated export/import
  (`export_preflight`, `export_bundle`, `import_bundle`), SHACL diagnostics
  (`validate_graph`), and docs (`get_doc`). The generated `mcp_tools` doc
  lists every parameter and every kind's spec fields.
- The same capability is available as a Python library (`from doxabase
  import DoxaBase`); the Python facade keeps some finer-grained methods that
  the MCP surface folds into kind parameters.
- Response sizes on the standard fixture capsule are budget-tested; graph
  content travels as TriG, JSON is the envelope (`response_conventions`).

## Deliberate Limits

- No query execution, no SPARQL endpoint, no embedded LLM, no embedding or
  semantic search. Search is lexical FTS over RDF literals.
- SHACL validation is an explicit diagnostic, not a mutation commit gate.
  Importable exports do gate on invalid live graphs by default.
- Staged revisions use conservative graph-state conflict checks with exact
  snapshot drift reporting — not semantic merge, rebase, or historical graph
  checkout.
- Privacy scanning is conservative pattern matching; scanner-clean is a
  review prompt, never export approval.
