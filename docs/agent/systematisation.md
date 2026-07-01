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
When a systematisation framing directly implements a lane from
`draft_profile_map_updates`, pass that action source through
`profile_route_sources`, for example
`profile_route_sources=[query_action.source_query_context]`. This persists the
profile route on the staged revision so
`export_profile_insight_review_bundle` can mark the lane as `direct_action`
instead of only related support. Check the returned
`profile_route_source_count`; when it is `0` after you supplied sources, use the
draft warning to correct the source shape before relying on the review bundle.
Top-level `profile_route_sources` apply to every framing. When alternatives
close different semantic moves, put `profile_route_sources` or
`profileRouteSources` on the individual framing objects instead; those
framing-level sources are recorded only on that staged revision.
Generated metric/type advisory actions already include `profile_route_sources`
when their primary call stages a map assertion, pattern promotion, or
systematisation. Preserve that argument when following the generated call. For
caller-authored followthrough alternatives, use the matching
`advisory_followthrough_plan[].source_profile_advisories` entry the same way.
For a combined type-review framing, such as defining a project value type and
asserting `rc:valueType` on a column in one staged revision, include the route
sources for both `define_value_type` and `assert_map_type`. The review bundle
closes lanes by route source, not by guessing intent from arbitrary Turtle.

Put the preferred comparison anchor first when `link_alternatives=True`, because
later framings are linked with `alternative_to` pointing at the first framing by
default. If the first framing is diagnostic, complementary, or expected to fail
validation, pass explicit `alternative_to` values or set
`link_alternatives=False`.
When the alternative target is another framing in the same call rather than an
existing staged revision, put `alternative_to_framing_index` on the later
framing. The value is 1-based and must reference an earlier framing, for example
`{"label": "Fallback", "alternative_to_framing_index": 1, ...}`.
When a draft detects this mistake after staging, the first suggested next action
is a complete `stage_systematisation(..., link_alternatives=False)` rerun call.
That rerun can still report
`shared_semantic_context_applies_to_all_framings` when shared ontology or shapes
are intentionally global to every framing.

## Shared Context

Use `shared_additions`, `shared_removals`, and `shared_context_summary` when
several framings need the same provisional vocabulary, shape, or assumption.
Shared patches are included in every staged framing preview and patch bundle,
including fallback framings.

For multi-framing drafts, read `structured_warnings`. The warning code
`shared_semantic_context_applies_to_all_framings` means shared `ontology` or
`shapes` patches also apply to fallback alternatives; its
`suggested_rerun_arguments` names the graph roles and original
`shared_additions` / `shared_removals` source indexes to move into per-framing
patches when a fallback should avoid that semantic context.
Use `shared_patch_summaries` to see the parsed shared patch target, operation,
count basis, format, and triple count, then map
`fallback_revision_iris_with_shared_semantic_context` back to
`framings[].revision_iri` before rerunning. That fallback IRI list is an
inspection subset of later framings that currently carry shared context, not an
automatic list of framings that should drop it; choose which framings keep
ontology/shapes patches by semantic review.
Grouped review exports reconstruct the same shared-context signal from stored
patch roles as `bundle_summary.shared_semantic_context_warnings`; carry the
draft warning into `executive_summary` only when reviewers need additional
agent judgement beyond the structured fields.
When recovering from export-only state, call `describe_staged_revision` on the
affected rows and read patch roles. Copy `SharedContextPatch` ontology/shapes
patches only into the semantically selected framing's `additions`, copy each
fallback's own `FramingPatch` content into that fallback, remove shared
ontology/shapes from the rerun, then check/export the rerun. This still requires
semantic judgement: use review notes, evidence, and target framing intent to
decide which framing keeps the ontology or shape context.
When the staged rows are available in the capsule, prefer
`draft_systematisation_shared_context_rerun(revision_iris=[...],
shared_context_target_revision_iris=[...])` after that semantic choice. It emits
the complete `stage_systematisation` arguments with shared ontology/shapes moved
into the selected framings, so agents do not need to copy Turtle by hand.

## Project Ontology And Shapes

When an awkward hunch needs a project vocabulary term, shape, or constraint,
stage it with the candidate graph move instead of mutating `ontology` or
`shapes` directly. Put project vocabulary in `ontology`, project validation
rules in `shapes`, and the current-best operational facts in `map`.

If one framing is "ontology or shape first" and another is a pattern-only or
map-only fallback, keep the ontology and shape patches in that framing's own
additions rather than `shared_additions`. Shared ontology or shape context is
included in every staged preview, so it can accidentally make a fallback depend
on provisional vocabulary it was meant to avoid.

It is often useful to stage one complete shape-backed framing beside an
intentionally incomplete or diagnostic sibling. Keep the diagnostic sibling
reviewable, set `link_alternatives=False` when the first framing is not the
preferred comparison anchor, and use stored validation results to explain what
the shape would require before choosing the durable model.
If a staged `rc:Pattern` fails validation for missing support even though the
staged revision has linked support metadata, add support inside the pattern
framing Turtle itself: `rc:supportingObservation`, `rc:supportingClaim`, or
`rc:evidence`. Revision-level support does not satisfy `rc:PatternShape`.

## Route The Draft

Use `next_action_queue` to separate ready framings from validation failures,
repair lanes, and informational rows. The queue is a routing surface, not a
preference order among alternatives. Use `revision_summaries`,
`review_recommendation`, `alternative_to`, and `current_alternative_to` to
understand comparison meaning. When linked alternatives are returned together,
`next_action_queue_items` carries `alternative_set_iris`,
`alternative_set_source_iri`, and `alternative_set_role` on every member,
including the first/source framing. `choose_one_groups` and
`choose_one_group_count` expose the same comparison set directly on the draft
response, which is simpler for cold automation than reconstructing it from
queue items or exporting Markdown first.

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
This is especially useful for profile-derived metric or type findings whose
meaning is still ambiguous: compare a project vocabulary definition against a
caveat/pattern fallback rather than blindly applying a generated metric
promotion skeleton.

For exact response fields, read `response_shapes` section "Staged Revisions".
For staged revision apply/restage/rebase behaviour, read `staged_revisions`.
