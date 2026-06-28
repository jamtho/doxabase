# Profiling Workflows

Use profiling helpers when profiler output should become durable handoff
context without pretending every observed value is already a current-best map
fact. Profile observations live in `observations`, optional profile evidence
usually lives in `evidence`, synthesized profile lore can live in `patterns`,
and accepted current-best facts should move through reviewed map/staged flows.

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
`total_profile_count`.

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
Grouped action source blocks expose stable `route_group_key` and
`route_step_key` fields. Use the group key to connect a draft lane, such as a
profile map-update duplicate group or metric/type advisory group, to later
`export_profile_insight_review_bundle().candidates[].profile_route_keys`.
Use the step key when several actions belong to the same group.
When the dataset already has physical-query metadata such as a path template or
layout but `describe_query_context` reports blocking metadata issues, the draft
adds a leading `query_context_review` lane. Follow that lane before relying on
profile-derived map updates for query-planning work. The profile update lanes
remain available for explicit review; the query lane is an ordering cue, not a
rejection of the profile evidence.
`source_query_context.route_anchor_iris` names the dataset, so a staged
dataset-anchored query repair can still bridge back to the query-context route
inside a later profile insight review bundle.

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
all supporting profile observations. For scalar conflicts, choose at most one option
from `profile_scalar_conflict_review` or from
`scalar_conflict_groups[].options[]`; those options intentionally stay out of
flat `suggested_next_actions`.

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
staging the related work. It scans current staged revisions and exports a
grouped Markdown review bundle for revisions connected to the profile run by
profile evidence, supporting profile observations, related support patterns, or
profile-derived anchors.
If `project_brief` shows `staged_frontier_review` or a profile task with
`pending_staged_profile_update_iris`, run `plan_staged_revision_recovery` or
review the staged profile-map update before calling `stage_profile_map_updates`
again for the same dataset/evidence. Other staged revisions that merely share
the same profile evidence remain staged-frontier work, but they should not be
treated as duplicate profile-map-update staging.
The returned candidates and Markdown `Profile Route Bridge` table preserve
matched profile route keys, so reviewers can see which draft duplicate/advisory
group led to each staged row without reverse-joining action indexes by hand.

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

For exact response fields, read `response_shapes` sections "Profile Helper
Records", "Describe Profile Run", and "Profile Map Update Drafts". For broader
map-authoring rationale, read `map_authoring`.
