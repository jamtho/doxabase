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
When the dataset already has physical-query metadata such as a path template or
layout but `describe_query_context` reports blocking metadata issues, the draft
adds a leading `query_context_review` lane. Follow that lane before relying on
profile-derived map updates for query-planning work. The profile update lanes
remain available for explicit review; the query lane is an ordering cue, not a
rejection of the profile evidence.

## Stage Accepted Facts

Use `stage_profile_map_updates(..., accepted_recommendation_indexes=[...])`
for profile facts you want reviewed before they become current map state. The
helper stages one grouped revision, including any accepted unmapped-column
shells, so applying one accepted profile batch does not immediately drift
against sibling staged revisions.

Accept one representative from duplicate groups unless sibling rows need
different modelling judgement. For scalar conflicts, choose at most one option
from `profile_scalar_conflict_review` or from
`scalar_conflict_groups[].options[]`; those options intentionally stay out of
flat `suggested_next_actions`.

Sampled row-count updates are skipped by default unless the caller explicitly
allows sampled row-count updates and the sample scope really is the durable
population.

## Advisory Lanes

Metric advisories and type advisories are review prompts, not accepted map
recommendation indexes. Metric advisories may suggest `stage_pattern_promotion`
for vocabulary or pattern-supported modelling. Type advisories may suggest
context slices, `record_pattern`, related column shells, or focused
`stage_map_assertion_change` calls.

After applying unmapped column shells, rerun `draft_profile_map_updates` for the
same dataset and evidence. Newly map-present columns can expose ordinary
profile recommendations, such as nullability, that should go through
`profile_map_updates` before you treat the run as advisory-only. When
`stage_profile_map_updates` staged an unmapped column shell, its
`suggested_next_actions` includes this `draft_profile_map_updates` rerun after
the staged revision apply-check action.

For exact response fields, read `response_shapes` sections "Profile Helper
Records", "Describe Profile Run", and "Profile Map Update Drafts". For broader
map-authoring rationale, read `map_authoring`.
