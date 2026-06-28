# Agent Workflow

Use this sequence when you already know you are operating inside a DoxaBase
capsule and need the fuller workflow. If you are arriving cold or resuming after
compaction, read `start_here` first.

1. Call `doxabase.list_docs`.
2. Read `start_here`, then read only the specific docs needed for the task:
   `graph_roles` for graph placement, `observation_recording` /
   `observation_rdf` / `patterns` for preserving lore, `map_authoring` /
   `staged_revisions` / `revisions` for graph changes, `context_slicing` /
   `lexical_search` for retrieval, `response_shapes` before scripting against
   returned objects, and `field_trials` for sub-agent trials.
3. Call `doxabase.graph_overview` to inspect named graphs, counts, common classes, and predicates.
4. Call `doxabase.search` when you have a remembered term, caveat, column name, source note, or question-shaped keyword.
5. Call `doxabase.list_entities` for likely entry points, usually `type="rc:Table"` or `type="rc:Dataset"` in `graph="map"`.
6. Call `doxabase.describe_dataset` for a bounded view of one table's row semantics, columns, layouts, storage access, caveats, provenance, relationships, linked patterns, linked-pattern reasons, and grouped related-dataset reasons.
7. Call `doxabase.describe_profile_run` with a dataset IRI and shared evidence IRI when `describe_dataset().profile_summary.profile_run_candidates` points at a profiler run whose full returned observations matter.
   If `draft_profile_map_updates()` returns no recommendations but
   metric or type advisories are present, treat it as advisory-only and do not
   call `stage_profile_map_updates`. Prefer
   `suggested_next_action_groups`: use `profile_map_updates` for accepted map
   facts, `profile_scalar_conflict_review` for choose-one scalar conflicts,
   `metric_vocabulary_review` for metric vocabulary, and `profile_type_review`
   for type evidence. Metric advisories may include a reviewable
   `stage_pattern_promotion` skeleton, while type advisories may include
   context, pattern, related column shell, or focused
   `stage_map_assertion_change` routes.
8. Call `doxabase.describe_query_context` when the task is physical query planning and you need storage/layout/path/caveat readiness without the full handoff.
9. Call `doxabase.describe_context_slice` when you need a route-explained subgraph around a dataset, pattern, or lore thread.
   Use `profile="dataset_brief"` for dataset/table/profile/metric handoffs,
   `profile="pattern_brief"` for pattern handoffs, and `profile="deep_lore"`
   when revision/history links or broader lore may matter.
10. Use `doxabase.list_entities` with `type="rc:Pattern"` followed by `doxabase.describe_pattern` when you need the full handoff behind a linked pattern.
11. Use `doxabase.list_entities` with types such as `rc:Claim`, `rc:Evidence`, or `rc:SourceSpan`, then `doxabase.describe_resource`, when you need generic type-aware retrieval instead of lexical search.
12. Use `doxabase.record_observation` when you discover a simple point-in-time finding that should remain available to later agents.
13. Use `doxabase.record_dataset_profile` when a profiling result should write
    a profile observation and optionally update map/pattern context together.
14. Use `doxabase.record_column_profile` when a column profiling result should
    write a profile observation and optionally update map/pattern context
    together.
15. Use `doxabase.record_profile_bundle` when one profiling pass produced a
    dataset-level profile and several related column profiles that should share
    run metadata, evidence fields, or sample context. Pass
    `shared_evidence_iri` when they should all point at one shared evidence
    resource.
16. Use `doxabase.record_claim_observation` for the common observation + claim + evidence + source-span pattern.
    For more complex caveat, join, transformation, access, or source-span claims, write agent-authored observation RDF using the `observation_rdf` patterns.
17. Use `doxabase.record_claim_reconsideration` when a newer claim weakens,
    contradicts, supersedes, or refines an earlier claim. This keeps the earlier
    hunch available while making the changed reading explicit.
18. Use `doxabase.record_pattern` when several observations or claims belong together and explain a more durable pattern.
19. Use `doxabase.stage_map_assertion_change` when you want to propose a
    reviewable add/remove/replace for one current-best map assertion. It carries
    assertion support, caveat scope, route summaries, generated patches, and
    staged revision metadata together.
20. Use `doxabase.stage_graph_revision` when you want to propose additions or
    removals without applying them. This is appropriate for exploratory hunches,
    alternative systematisations, and reviewable candidate map changes.
21. Use `doxabase.stage_systematisation` when one modelling hunch has several
    plausible RDF framings. This is especially useful for pattern-first versus
    ontology-first alternatives, or for awkward concepts that do not fit current
    helper templates. Use shared proposed context when several framings need the
    same tentative vocabulary or assumptions.
22. Use `doxabase.stage_pattern_promotion` when existing patterns support a
    caller-authored map, ontology, shape, or other graph change that should
    remain reviewable before being applied.
23. Use map authoring helpers such as `doxabase.record_map_dataset`, `doxabase.record_map_column`, `doxabase.record_map_caveat`, `doxabase.record_map_storage_access`, `doxabase.record_map_physical_layout`, `doxabase.record_map_partition_scheme`, and `doxabase.record_map_relationship` when a finding is ready to become current-best map context.
24. Use `doxabase.validate_graph` when you need an explicit SHACL diagnostic.
25. Use `doxabase.record_graph_revision` after a meaningful graph change or
    review-bundle export when later agents should know what changed, what graph
    roles were included for review, and why.
26. Use `doxabase.list_graph_revisions` when you need to discover staged,
    applied, or historical revision records before choosing one to inspect.
27. Use `doxabase.check_staged_revision_apply` when a staged proposal is being
    reviewed for application.
28. Use `doxabase.restage_staged_revision` when the apply check reports
    `target_count_drift` or `target_digest_drift` and the same patch intent
    should be replayed against current graph state.
29. Use `doxabase.apply_staged_revision` when a staged proposal should become
    durable graph state after conflict and validation checks.
30. Use `doxabase.describe_graph_revision` when reviewing a history record, and
    `doxabase.describe_staged_revision` when reviewing a staged patch proposal.

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

In the current V1 slice, the MCP interface exposes route-explained context
slices and reviewable staged revisions. It can apply one staged revision with
conservative graph-state conflict checks, and new staged revisions store
snapshot rows for exact count/digest drift reporting. It does not yet provide
rich conflict handling, rebasing, or durable graph version browsing beyond those
staged snapshots.
