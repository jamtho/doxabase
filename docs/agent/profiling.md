# Profiling Workflows

Use profiling helpers when profiler output should become durable handoff
context without pretending every observed value is already a current-best map
fact. Profile observations live in `observations`, optional profile evidence
usually lives in `evidence`, synthesized profile lore can live in `patterns`,
and accepted current-best facts should move through reviewed map/staged flows.
Use `plan_profile_followthrough` after `draft_profile_map_updates` when a
profile advisory needs a fresh, binding-aware next step, such as carrying a
returned `record_pattern().pattern_iri` into a staged map type assertion or
rechecking sibling staged rows after an apply.

## Record A Profile Run

Use `record_dataset_profile`, `record_column_profile`, or
`record_profile_bundle` when you want to preserve profiler output. Prefer
`record_profile_bundle` for one pass that produced dataset-level and column
profiles together. Pass `shared_evidence_iri` when the profiles all come from
one run and should be retrievable as a group.

Treat scalar `profile_metrics`, value frequencies, physical types, value types,
null counts, distinct counts, and row counts as observed evidence. They are not
constraints, SHACL shapes, allowed values, or durable map assertions by
themselves. Use `sample_scope` and `sample_method` so later agents know whether
the profile covered a full population, a sample, or an unknown slice.
For assets explicitly recorded with `is_table=false`, profile row counts remain
profile evidence; `draft_profile_map_updates` does not propose
`rc:rowCountSnapshot` map updates for them because the count may mean one
document, object, endpoint, or model artifact rather than table rows.

Bundled column-profile rows use `physical_type` and `value_type` for observed
type findings. The `observed_physical_type` and `observed_value_type` field
names belong to `record_observation`, not to `record_profile_bundle` rows.

```python
db.record_profile_bundle(
    dataset_iri,
    dataset_summary="Full table profile.",
    evidence_summary="Profiler output from the current warehouse snapshot.",
    evidence_sources=["file:///tmp/profile.json"],
    shared_evidence_iri=evidence_iri,
    sample_size=1000,
    sample_scope="All rows in the current table snapshot.",
    sample_method="DuckDB full-table profile.",
    column_profiles=[
        {
            "column_iri": column_iri,
            "column_name": "status",
            "null_count": 0,
            "physical_type": "rc:Varchar",
            "value_type": "project:StatusCodeValue",
        }
    ],
)
```

## Retrieve The Run

Start from `describe_dataset`. Its `profile_summary.profile_run_candidates`
lists shared evidence IRIs that support several returned profile observations.
Then call `describe_profile_run(dataset_iri, evidence_iri)` when bounded dataset
context omitted rows or when you need the full run before drafting map changes.
For exact response fields, read the `response_shapes` section
"Describe Profile Run"; count fields are named `returned_profile_count` and
`total_profile_count`. Follow the run's `suggested_next_actions`: if the run was
capped, expand it first, then call `draft_profile_map_updates`; otherwise the
draft action is the direct next step.

For route-explained handoffs, use `describe_context_slice` with
`profile="dataset_brief"` for table/profile summaries or seed the slice with a
specific profile observation, metric node, or project-specific metric-kind IRI.

## Draft Map Updates

Call `draft_profile_map_updates(dataset_iri, evidence_iri)` before staging
profile-derived map facts. The draft compares one shared-evidence profile run
with current map state and separates:

- `profile_map_updates` for default-stageable accepted map facts;
- `profile_scalar_conflict_review` for choose-one row-count or nullable scalar
  conflicts;
- `metric_vocabulary_review` for project-specific metric vocabulary;
- `profile_type_review` for observed physical/value type evidence.

Use `suggested_next_action_groups` instead of flattening every review lane into
one mutation queue. If the draft has no recommendations but metric or type
advisories are present, it is advisory-only: do not call
`stage_profile_map_updates` just to clear the draft.
Use `advisory_followthrough_plan` for a compact next-step menu over metric/type
lanes. It groups existing actions by `semantic_move`: `define_metric`,
`define_value_type`, `assert_map_type`, or `caveat_fallback`.
For type review, `caveat_fallback` is the pattern/systematisation alternative
when the finding is not ready for a direct assertion. It is not an additional
required move after the same route group has staged the reviewed
`assert_map_type` path. In value-type workflows, a vocabulary promotion can
close only `define_value_type`; stage the reviewed map assertion separately when
the profile finding should become current map truth.
If you author one combined `stage_systematisation` framing that both defines a
project value type and asserts `rc:valueType` on the column, carry route sources
for both semantic moves. Otherwise the review bundle should still show the
missing `define_value_type` or `assert_map_type` lane as open, even if the Turtle
contains both shapes of triple.
Do not select rows by `semantic_move` alone when scripting. A draft can expose
several `define_metric` rows, for example context inspection and a staging call.
Use `primary_action_kind` to choose the route you intend:
`stage_reviewable_change` for staged review work, `direct_graph_write` for
direct record helpers, and `inspect_context` for non-mutating review.
If same dataset/evidence profile map updates are already staged, the draft sets
`pending_staged_profile_update_iris` and puts a
`plan_staged_revision_recovery` action first in `profile_map_updates`. Review
that staged frontier before using any following `stage_profile_map_updates`
action for a deliberate alternative or duplicate. Direct
`stage_profile_map_updates` calls reject this pending same dataset/evidence case
by default; pass `allow_pending_profile_updates=true` only after review confirms
another staged update is intentional.
Grouped action source blocks expose stable `route_group_key` and
`route_step_key` fields. Use the group key to connect a draft lane, such as a
profile map-update duplicate group or metric/type advisory group, to later
`export_profile_insight_review_bundle().candidates[].profile_route_keys`.
Use the step key when several actions belong to the same group.
When the dataset already has physical-query metadata such as a path template or
layout but `describe_query_context` reports blocking metadata issues, the draft
adds a leading `query_context_review` lane. Follow that lane before relying on
profile-derived map updates for query-planning work. If you stage a dedicated
storage or layout repair for that lane with `stage_query_storage_access_repair`
or `stage_query_physical_layout_repair`, pass the route source from the query
context action with
`profile_route_sources=[query_action.source_query_context]` so later profile
insight exports treat the repair as a `direct_action`. Do the same for
caller-authored systematisation repairs. A systematisation draft returns
`profile_route_source_count`; for query repair helpers, confirm the stored route
with `describe_staged_revision().profile_route_sources` if needed. For sampled
profile evidence, that query-context route source also carries the draft's
profile quality summary and sampled-evidence caution, so a generic staged
export can still warn Markdown-only reviewers that a storage/layout repair came
from sampled profile context. The profile update lanes remain available for
explicit review; the query lane is an ordering cue, not a rejection of the
profile evidence.
The draft may not add this bridge when the dataset has no physical-query cue at
all, for example when the query blocker is only `missing_path_template`. In that
case use `describe_query_context` directly, add reviewed storage/path/layout
metadata, and rerun the profile draft once a physical-query cue exists.
`source_query_context.route_anchor_iris` names the dataset, so a staged
dataset-anchored query repair can still bridge back to the query-context route
inside a later profile insight review bundle.
`source_query_context.evidence_iri` and `profile_evidence_iri` name the profile
run that produced the blocker action; keep one of those fields with copied
first-hop `describe_query_context` actions when several profile runs on the
same dataset route to the same physical blocker.
For mixed profile/query lanes, do not let a profile insight bundle's
`do_not_bulk_apply` decision block reviewed query repair progress. The safe
loop is lane-specific: stage profile-routed storage/layout repairs, export the
profile insight or staged-revisions review, apply one repair only after
`check_staged_revision_apply` is ready, rerun `plan_staged_revision_recovery`
or `describe_query_context`, restage any stale sibling repair, recheck it, then
apply the refreshed successor before drafting the query plan.

## Stage Accepted Facts

Use `stage_profile_map_updates(..., accepted_recommendation_indexes=[...])`
for profile facts you want reviewed before they become current map state. The
helper stages one grouped revision, including any accepted unmapped-column
shells, so applying one accepted profile batch does not immediately drift
against sibling staged revisions.

Accept one representative from duplicate groups unless sibling rows need
different modelling judgement. Repeated `unmapped_profiled_column` shell rows are
grouped by the helper mutation, so profile-specific sample or null details do not
make agents stage the same shell twice; the accepted representative still carries
all supporting profile observations. For scalar conflicts, choose at most one
option from `profile_scalar_conflict_review` or from
`scalar_conflict_groups[].options[]`; those options intentionally stay out of
flat `suggested_next_actions`. Read each option's
`recommendation_contexts[]` before choosing; it carries the profile
observation, sample, basis, observed-count, profile-row-count, and confidence
fields needed to compare full-scan and sampled support. A focused option call to
`stage_profile_map_updates` still returns full-draft accounting: unrelated draft
recommendations appear as `not_selected` in `status_counts` / `items[]` even
though the selected scalar option was the only accepted index.

Sampled row-count updates are skipped by default unless the caller explicitly
allows sampled row-count updates and the sample scope really is the durable
population.
For non-table assets, row-count observations are not drafted as
`dataset_row_count_snapshot` recommendations at all; preserve them as profile
evidence or model a more precise project-specific metric when asset counts
matter.

## Export A Profile Insight Review

When a profile run leads to several staged lanes, use
`export_profile_insight_review_bundle(dataset_iri, evidence_iri, path)` after
staging the related work. It scans current staged revisions and already-applied
staged source rows, then exports a grouped Markdown review bundle for revisions
connected to the profile run by profile evidence, supporting profile
observations, related support patterns, or profile-derived anchors. Leave the
applied-source scan on for post-apply handoffs where the
profile map-update row has already been applied but still needs to travel with
remaining caveat, metric, type, or query-repair review work.
Explicit `revision_iris=[...]` are seeds for the bundle, not a strict filter.
For a strict review of only those requested staged rows, also pass
`include_current_staged_work=False` and
`include_applied_staged_sources=False`.
If `candidate_count` is `0`, no Markdown artifact is written and the returned
`export` field is `None`; inspect `warnings` and
`open_profile_review_lanes` before assuming the review lane is resolved.
If `project_brief` shows `staged_frontier_review` or a profile task with
`pending_staged_profile_update_iris`, run `plan_staged_revision_recovery` or
review the staged profile-map update before calling `stage_profile_map_updates`
again for the same dataset/evidence. The staging helper enforces this by
default and requires `allow_pending_profile_updates=true` for intentional
duplicates after review. Other staged revisions that merely share the same
profile evidence remain staged-frontier work, but they should not be treated as
duplicate profile-map-update staging. Pending profile-map updates only demote
pure map-update reruns; if scalar conflict, metric vocabulary, or type advisory
lanes remain open, `project_brief` keeps the `profile_review` task at normal
priority and its reason says advisory/conflict lanes remain open.
For any `profile_review` task, keep `profile_evidence_iri` with the work item.
It distinguishes multiple profile drafts on the same dataset even when their
first suggested action is the same dataset-level `describe_query_context` call.
The returned candidates and Markdown `Profile Route Bridge` table preserve
matched profile route keys, so reviewers can see which draft duplicate/advisory
group led to each staged row without reverse-joining action indexes by hand.
The returned `open_profile_review_lanes` list and Markdown
`Open Profile Review Lanes` table show live draft route groups that still lack
a `direct_action` candidate in the bundle. A staged profile-map update may be
included as `strong_support` or `related_support` for metric/type lanes, but
those lanes remain open until their own direct promotion or assertion revision
is staged.
After a metric promotion has been applied, a rerun may still show
`project_metric_defined` actions for context inspection. Those routes are not
open metric vocabulary work; `export_profile_insight_review_bundle` suppresses
them from `open_profile_review_lanes` while preserving the applied promotion as
the direct-action route in the bridge. `project_brief` follows the same
closed-lane cue: if a draft only has `project_metric_defined` metric context and
no map updates, scalar conflicts, open metric vocabulary, or type findings, it
does not create a `profile_review` task.
The bridge `Row` column uses the same row number as the grouped review bundle's
`Revision N` sections and repeats the candidate summary, so a Markdown-only
reviewer can map route lanes back to the detailed revision section directly.
Generic staged inspection preserves the stored trail too:
`describe_staged_revision()` exposes `profile_route_sources`,
`profile_route_keys`, and `profile_route_groups`, and
`export_staged_revisions()` adds a compact `Profile Route Bridge` when those
stored sources exist. The generic bridge includes evidence cautions from stored
profile route groups, including sampled-profile warnings. Use the full profile
insight bundle when you need live open-lane analysis; use the generic bridge
when a handoff only has a staged review bundle or one staged row.
When several route groups map to the same lane, match strength, and support
kind, the Markdown lane label is grouped with a route-group count; the returned
`profile_route_keys` and `profile_route_groups` still preserve every route key
for scripts. `profile_route_groups` rows are dict-shaped; scripts should index
fields such as `group["review_lane"]` rather than using attribute access.
Use `group["closed_semantic_moves"]`, `group["remaining_semantic_moves"]`, and
`group["direct_route_step_keys"]` when deciding what a staged row closed. A
single `profile_type_review` route group can contain both `define_value_type`
and `assert_map_type`; staging the value-type vocabulary skeleton closes the
definition move, not the later map assertion. The bundle-level
`semantic_move_closure_summary`, `closed_semantic_moves`, and
`remaining_semantic_moves` fields repeat this distinction for unattended
scripts, and the Markdown review summary renders a `Semantic Move Closure`
section before the open-lane table.
Use the profile bundle's semantic apply-gate fields for executor decisions:
`bulk_apply_allowed`, `safe_single_apply_candidate_revision_iris`,
`semantic_apply_gate_summary`, `semantic_apply_gate_counts`,
`executor_decision_summary`, and each candidate's `semantic_apply_role`,
`apply_cardinality`, and
`safe_single_apply_candidate`. Closed semantic moves, an empty open-lane list,
or staged rows in `apply_after_review` mean mechanical readiness and lane
accounting; they are not permission to bulk apply metric/type/query/fallback
semantic choices. A bundle with semantic candidates should be treated as
choose-one-and-recheck unless the apply gate explicitly says bulk apply is
allowed.
Use `executor_decision_summary` as the compact unattended routing object: it
names the decision, mutation policy, safe-single candidates, blocked candidates,
open lanes, candidate rationales, and whether a rerun is required after
mutation. Then inspect the detailed candidate/lane rows before applying
anything. When `sampled_evidence_caution` appears on the bundle, a candidate, or
`safe_single_apply_candidate_rationales[]`, or as an evidence caution in the
generic `export_staged_revisions()` Profile Route Bridge, treat it as a
scope-review prompt: the staged row may be mechanically ready without being
full-scan-backed.
For the narrow positive case with one ordinary profile map-update candidate,
`bulk_apply_allowed=true` and `decision="bulk_apply_after_review"` can be safe,
but scripts should still count, not parse the word "bulk": require exactly one
IRI in `safe_single_apply_candidate_revision_iris`, confirm
`check_staged_revision_apply(...).status == "ready"`, apply that one reviewed
row, and rerun `draft_profile_map_updates` / the profile insight export before
any further mutation. If a handoff needs post-apply review context, keep
`include_applied_staged_sources=true`; current-only exports should drop the
applied map-update candidate once the live draft is closed.
When a full-scan profile map update shares only supporting metric/type/fallback
context, the bundle may still expose that map row as a
`safe_single_apply_candidate` with
`decision="apply_one_safe_single_after_review"`. This is not bulk permission:
apply at most one ready map update, then rerun while metric/type/systematisation
lanes stay open. Query-context blockers and scalar-conflict lanes still block
safe-single status.
Scalar-conflict review is semantic context too. After one same-evidence scalar
choice is applied, a sibling row-count or nullable observation should stay out
of default `profile_map_updates`; the draft routes it through
`profile_scalar_conflict_review` inspection because one conflict value is
already current. A profile-map staged row that overlaps such scalar conflict
memory must not be treated as a `safe_single_apply_candidate` merely because
`check_staged_revision_apply` is mechanically ready.
New `stage_profile_map_updates` revisions persist their profile route source in
history, so post-apply exports can still show the original
`profile_map_updates` direct-action lane after the live draft no longer proposes
that map update. When the staged recommendation was chosen from
`profile_scalar_conflict_review`, the stored route also marks that scalar
conflict lane as the direct action, so choosing one option closes the route
group in `open_profile_review_lanes`. Fresh same-lane live follow-ups after
apply remain support routes, not direct-action satisfaction for the
already-applied row. Generated query-planning repair rows with review notes such as
`missing_storage_access query planning guidance` are also recovered as
`query_context_review` direct-action rows when the repair has already been
applied and the blocker no longer appears in the live draft.
Read each route group's `match_strength`: `direct_action` marks the lane a
staged row appears to implement, while `strong_support` and `related_support`
mean the row is included because it shares profile observations, support
patterns, or anchors with that lane.
If a profile-review handoff depends on a pending query repair such as
`missing_storage_access`, include the relevant `describe_query_context` output
or a default project TriG plus `export_revision_snapshots()` JSON alongside the
Markdown bundle. The profile Markdown bridge shows the staged row and route, but
compact candidate-pending fields such as `already_pending_candidate_count` live
in the query-context payload or recovered project-history capsule.

## Awkward Metric And Type Lanes

Metric/type advisories are review lanes, not orders to mint vocabulary. When a
metric advisory skeleton is semantically thin or mixed-support notes show the
same pattern supporting several interpretations, compare alternatives before
applying anything: one framing might define an ontology
`rc:ProfileMetricKind`, while another records a caveat or pattern-backed
fallback without promoting a metric term yet. Use `stage_systematisation` for
those alternatives when the graph move needs modelling judgement, and export the
grouped staged review before selecting a durable path.
`draft_profile_map_updates.mixed_support_review_groups` is the compact route for
those comparisons: it groups shared support patterns, review lanes, semantic
moves, advisory indexes, and suggested calls before anything is staged.
Generated mutating advisory actions for `stage_map_assertion_change`,
`stage_pattern_promotion`, and `stage_systematisation` already include
`profile_route_sources` in their arguments. Preserve that argument when calling
them. When you stage a caller-authored alternative from a plan item instead,
pass the matching `source_profile_advisories` entry through
`profile_route_sources` so profile insight review can close that advisory lane
as a direct action. A profile insight review bundle now reserves `direct_action`
for persisted route sources; live draft overlap is support context and should
not be treated as a closed lane. Metric and type-review lanes also generate
pattern-only `stage_systematisation` fallback actions when profile evidence is
not ready for project vocabulary or map assertions; use those calls before
falling back to ad hoc pattern recording.

When `stage_profile_map_updates` creates a staged revision, its
`suggested_next_actions` includes an `export_profile_insight_review_bundle`
action seeded with that revision. Use it for the first focused review bundle,
then rerun the export after staging metric vocabulary, type-review, or
caveat/systematisation alternatives that should be compared with the map
update.

This helper is a review bundler, not a staging shortcut. It will include the
profile map-update revision plus already-staged metric vocabulary promotions,
caveat/systematisation alternatives, or type-review assertions when they carry
the relevant support links. Follow remaining metric/type advisory lanes first
when expected review rows are not staged yet.

## Advisory Lanes

Metric advisories and type advisories are review prompts, not accepted map
recommendation indexes. Metric advisories may suggest `stage_pattern_promotion`
for vocabulary or pattern-supported modelling. Type advisories may suggest
context slices, `record_pattern`, related column shells, or focused
`stage_map_assertion_change` calls.
Profile-bundle helper pattern implication synthesis carries project-specific
metric IRIs, but observed project value-type IRIs may need a targeted
`record_pattern` before their type-review lane has the same support trail. When
a value-type finding should travel with metric/type review routing, record a
pattern that targets or implies the value type and shares the profile evidence
before staging the assertion or systematisation alternative.
When a type advisory or modelling note first routes through `record_pattern`,
carry the returned `pattern_iri` into the later assertion stage, for example
`stage_map_assertion_change(..., supporting_patterns=[pattern_iri])`, when the
candidate map assertion should preserve that pattern support. The review bundle
can then show the staged assertion as directly supported by the advisory pattern
instead of leaving the reviewer to reconnect the two rows manually. Preserve the
selected action's `arguments.profile_route_sources`; otherwise the staged
assertion may appear as strong support but will not close the advisory lane as
`direct_action`.
Generated profile type-review actions now expose this handoff as route-scoped
binding metadata. Read `produces_result_bindings[]` on the `record_pattern`
action and `consumes_result_bindings[]` on paired `stage_map_assertion_change`
actions; matching `binding_key` values tell an unattended script to append the
returned `pattern_iri` to `supporting_patterns`.
`plan_profile_followthrough(dataset_iri, evidence_iri, result_bindings={...})`
does that binding step from a fresh draft. Use it after recording the pattern
so newly visible `stage_pattern_promotion` actions and resolved
`stage_map_assertion_change` arguments are based on current graph state. Pass
related `staged_revision_iris` when a previous apply may have made sibling
staged rows stale; `restage_stale_revisions=True` can mechanically refresh
rows whose next action is `restage_staged_revision`, but the helper does not
apply profile-generated map or ontology changes.
When a same dataset/evidence profile map update is already pending,
`plan_profile_followthrough` keeps duplicate `stage_profile_map_updates` rows in
`action_resolution_groups.pending_profile_map_update_review` but omits them from
call-ready `suggested_next_actions`. Follow the paired
`plan_staged_revision_recovery` action first, and pass
`allow_pending_profile_updates=true` only after review confirms another staged
profile map update is intentional.
If the first follow-through pass reports `missing_binding_keys`, run or inspect
the producing action for those keys, then pass the returned values back through
`result_bindings`. For example, a value-type support route may need the
`pattern_iri` produced by `record_pattern` before its
`stage_map_assertion_change` arguments are complete.
If a metric advisory already has matching current staged vocabulary work, it
sets `pending_staged_promotion_iris` and routes to inspect/export that staged
revision instead of proposing a duplicate `stage_pattern_promotion` skeleton.
After a metric promotion applies, a rerun should report
`project_metric_defined` and stop suggesting another promotion skeleton. Use the
observed-metric context action for the local dataset handoff, and use a
`deep_lore` context slice from the metric, promotion pattern, or revision when
you need to rediscover why the ontology term exists.

After applying unmapped column shells, rerun `draft_profile_map_updates` for the
same dataset and evidence. Newly map-present columns can expose ordinary
profile recommendations, such as nullability, that should go through
`profile_map_updates` before you treat the run as advisory-only. When
`stage_profile_map_updates` staged an unmapped column shell, its
`suggested_next_actions` includes this `draft_profile_map_updates` rerun after
the staged revision apply-check and review-bundle export actions. The rerun
action carries a
`preconditions.staged_revision_applied` field naming the staged revision that
must be reviewed and applied before the rerun will show map-present follow-up
recommendations.
An independently ready `query_plan_handoff` task can remain useful while this
profile follow-up is open; follow the profile queue when the goal is map cleanup,
or the handoff queue when the goal is to produce an executable or runtime-ready
query handoff from already-sufficient context.

For exact response fields, read `response_shapes` sections "Profile Helper
Records", "Describe Profile Run", and "Profile Map Update Drafts". For broader
map-authoring rationale, read `map_authoring`.
