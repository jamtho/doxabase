# Systematisation Workflows

Use systematisation helpers when the graph move itself carries modelling
judgement: alternative RDF framings, provisional project vocabulary, candidate
shapes, pattern-supported promotions, or awkward concepts that should stay
reviewable before becoming durable map or ontology state.

## Stage Alternative Framings

Call `stage_systematisation` when one modelling hunch has one or more plausible
RDF framings. The helper does not choose the model for you. It packages
caller-authored additions and removals as staged revisions, validates each
preview, records review notes, and returns routing fields such as
`next_action_queue`, `next_action_queue_items`, and `suggested_next_actions`.

Use anchors for the resources the hunch is about: datasets, columns, caveats,
relationships, observations, patterns, or other graph resources. Use
supporting observations, claims, patterns, and evidence for justification; do
not use anchors as a substitute for evidence.

Put the preferred comparison anchor first when `link_alternatives=True`, because
later framings are linked with `alternative_to` pointing at the first framing by
default. If the first framing is diagnostic, complementary, or expected to fail
validation, pass explicit `alternative_to` values or set
`link_alternatives=False`.

## Shared Context

Use `shared_additions`, `shared_removals`, and `shared_context_summary` when
several framings need the same provisional vocabulary, shape, or assumption.
Shared patches are included in every staged framing preview and patch bundle,
including fallback framings.

For multi-framing drafts, read `structured_warnings`. The warning code
`shared_semantic_context_applies_to_all_framings` means shared `ontology` or
`shapes` patches also apply to fallback alternatives; its
`suggested_rerun_arguments` names the graph roles to move into per-framing
patches when a fallback should avoid that semantic context.

## Route The Draft

Use `next_action_queue` to separate ready framings from validation failures,
repair lanes, and informational rows. The queue is a routing surface, not a
preference order among alternatives. Use `revision_summaries`,
`review_recommendation`, `alternative_to`, and `current_alternative_to` to
understand comparison meaning.

Before applying, repairing, or restaging a candidate, rerun
`check_staged_revision_apply` if any graph changes may have happened since the
draft was created. Export related framings together with
`export_staged_revisions` when reviewers need to compare Turtle payloads and
review notes.

## Pattern-Supported Promotion

Call `stage_pattern_promotion` when existing patterns are the reason a graph
change now seems worth staging. It is a pattern-aware wrapper around
`stage_systematisation`, not an automatic map editor. It records the selected
patterns as `supporting_patterns`, rolls up pattern support into revision
metadata, uses pattern targets and map implications as anchors, and still
requires caller-authored RDF framings.

Use it for reviewable moves such as promoting a pattern-backed caveat,
relationship, project vocabulary term, shape, or map assertion. If the exact
graph move is not yet clear, keep the synthesis in `patterns` and stage several
candidate framings instead of forcing one current-best fact.

For exact response fields, read `response_shapes` section "Systematisation
Drafts". For staged revision apply/restage/rebase behaviour, read
`staged_revisions`.
