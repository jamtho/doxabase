# Agent Workflow

Use this sequence when arriving cold in a DoxaBase capsule.

1. Call `doxabase.list_docs`.
2. Read `overview`, `graph_roles`, `ontology_primer`, `lexical_search`, `observation_rdf`, `patterns`, `map_authoring`, `revisions`, `executable_catalog`, and `field_trials` if you do not know the project conventions.
3. Call `doxabase.graph_overview` to inspect named graphs, counts, common classes, and predicates.
4. Call `doxabase.search` when you have a remembered term, caveat, column name, source note, or question-shaped keyword.
5. Call `doxabase.list_entities` for likely entry points, usually `type="rc:Table"` or `type="rc:Dataset"` in `graph="map"`.
6. Call `doxabase.describe_dataset` for a bounded view of one table's row semantics, columns, layouts, storage access, caveats, provenance, relationships, linked patterns, linked-pattern reasons, and grouped related-dataset reasons.
7. Use `doxabase.list_entities` with `type="rc:Pattern"` followed by `doxabase.describe_pattern` when you need the full handoff behind a linked pattern.
8. Use `doxabase.list_entities` with types such as `rc:Claim`, `rc:Evidence`, or `rc:SourceSpan`, then `doxabase.describe_resource`, when you need generic type-aware retrieval instead of lexical search.
9. Use `doxabase.record_observation` when you discover a simple point-in-time finding that should remain available to later agents.
10. Use `doxabase.record_claim_observation` for the common observation + claim + evidence + source-span pattern.
   For more complex caveat, join, transformation, access, or source-span claims, write agent-authored observation RDF using the `observation_rdf` patterns.
11. Use `doxabase.record_pattern` when several observations or claims belong together and explain a more durable pattern.
12. Use map authoring helpers such as `doxabase.record_map_dataset`, `doxabase.record_map_column`, `doxabase.record_map_caveat`, `doxabase.record_map_storage_access`, and `doxabase.record_map_relationship` when a finding is ready to become current-best map context.
13. Use `doxabase.validate_graph` when you need an explicit SHACL diagnostic.
14. Use `doxabase.record_graph_revision` after a meaningful graph change or
    review-bundle export when later agents should know what changed, what graph
    roles were included for review, and why.
15. Use `doxabase.describe_graph_revision` when reviewing a history record.

When reading linked-pattern reasons from `describe_dataset`, scan
`match_groups` before raw `matches`. Direct and map-implication groups are the
strongest local relevance signals; claim- and observation-supported groups show
surrounding lore. Treat group counts as navigation hints rather than confidence
scores; tier counts are over grouped matches, while raw match counts are over
unfolded routes. Call `describe_pattern` before applying a pattern as a decision
rule.

When adding future facts, choose graph roles by update pattern:

- Put vocabulary/model terms in `ontology`.
- Put consolidated current project knowledge in `map`.
- Put raw point-in-time findings in `observations`.
- Put syntheses over related findings in `patterns`.
- Put source/query/hash/sample support in `evidence`.
- Put project SHACL in `shapes`.
- Put revision rationale and review-bundle metadata in `history`.

Do not write to `base_ontology` or `base_shapes`; they are immutable package seed graphs.

In the current V1 slice, the MCP interface does not yet expose context-slice or
staged diff/commit tools. Treat revision records as metadata about graph changes,
not as transactional graph replacement.
