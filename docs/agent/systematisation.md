# Systematisation

Use systematisation staging when the graph move itself carries modelling
judgement: alternative RDF framings of one hunch, provisional project
vocabulary, candidate shapes, or awkward concepts that should stay reviewable
before becoming durable map or ontology state. The helper packages
caller-authored RDF; it never chooses the model for you.

## Staging Alternative Framings

`stage_revision(kind="systematisation", spec={...})` takes a `summary`,
`intent`, `rationale`, `anchors` (the resources the hunch is about — not a
substitute for evidence), and `framings`: each framing is a label plus either
the `graph` + `content` shorthand for one Turtle addition or full
`additions`/`removals` patch lists. Each framing becomes one staged revision
with its own validation preview. Add `review_note` and
`review_recommendation` per framing when the comparison needs human-readable
judgement ("preferred for now", "too bold but informative").

Alternative linking: later framings default to `alternative_to` the FIRST
framing, so put the preferred comparison anchor first. If the first framing
is diagnostic or expected to fail validation, pass explicit `alternative_to`
values, use `alternative_to_framing_index` (1-based, must reference an
earlier framing), or set `link_alternatives=false`. When the runtime detects
a bad default link it warns and suggests a complete rerun call — read
`structured_warnings`, not just prose.

Keeping one intentionally incomplete or invalid framing beside a complete
sibling is often useful: the stored validation diagnostics become a review
cue for what the shape would require.

## Shared Context

`shared_additions` / `shared_removals` / `shared_context_summary` carry
vocabulary or shapes that several framings need. Shared patches are included
in EVERY framing's preview and patch bundle — so keep ontology/shapes patches
out of `shared_additions` when a fallback framing is meant to avoid the
provisional vocabulary; give them to the specific framings instead. Drafts
with shared ontology/shapes patches emit the
`shared_semantic_context_applies_to_all_framings` warning with the patch
summaries and affected fallback IRIs; that list is an inspection subset, not
an automatic drop list — choose which framings keep semantic context by
review.

When review decides which framings should keep shared context, do not copy
Turtle by hand: `stage_revision(kind="systematisation", dry_run=true)` is the
shared-context rerun drafter — its spec takes the staged `revision_iris` and
`shared_context_target_revision_iris`, and it returns complete
re-stage arguments with the shared patches moved into the selected framings.
If the rerun would leave a diagnostic row mechanically ready only because
its validation context was removed, heed the warning and omit or explicitly
discard that row.

Note that a staged `rc:Pattern` framing must carry support inside its own
Turtle (`rc:supportingObservation` / `rc:supportingClaim` / `rc:evidence`);
revision-level support links do not satisfy `rc:PatternShape`.

## Pattern-Supported Promotion

`stage_revision(kind="pattern_promotion", spec={...})` is the pattern-aware
wrapper: pass existing `patterns` IRIs plus caller-authored framings. The
selected patterns become staged-revision support, their observations and
claims roll into revision metadata, and their targets and map implications
become revision anchors. Use it when patterns are the reason a caveat,
relationship, vocabulary term, shape, or map assertion now seems worth
staging — including profile-derived metric or type findings whose meaning is
still ambiguous, where one framing defines an ontology term and another
records a caveat/pattern fallback.

## Routing The Draft

The staging response routes itself: the next-action queue separates
mechanically ready framings from validation failures and informational rows
(it is a routing surface, not a preference order among alternatives);
choose-one groups expose the comparison set directly. Before applying,
repairing, or restaging, re-check with `apply_staged_revision(dry_run=true)`
if the graph may have changed since the draft. Export related framings
together with `export_bundle(kind="staged_revisions",
spec={"revision_iris": [...], "path": ...})` when reviewers should compare
Turtle payloads and review notes as one bundle; apply at most one member of
a choose-one group, then re-check the siblings (see `staged_revisions`).

Proposed ontology/SHACL resources inside staged patch Turtle are not
materialized until apply, so `describe_resource` cannot inspect a proposed
shape's blank-node constraints; read the patch payload through
`describe_revision` on the staged row or the grouped export.

Python API note: the library methods are `db.stage_systematisation`,
`db.stage_pattern_promotion`, and
`db.draft_systematisation_shared_context_rerun`.
