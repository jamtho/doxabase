# Profiling

DoxaBase never runs a profiler. An external scan produces numbers; DoxaBase
records them as evidence and helps you decide — deliberately, per finding —
what becomes current map truth. Three different things can follow from a
profile, and they should not be conflated: ordinary map drift (a scalar
changed; stage the update), a vocabulary question (the data wants a metric or
value type the ontology lacks; keep it reviewable), and a caveat (often the
most valuable outcome).

## Recording A Run

`doxabase.record_profile(kind=..., spec={...})`:

- `kind="dataset"` — one dataset-level profile. May also update the map
  row-count snapshot (`update_map_snapshot`, default true) — but only when
  the basis looks like a full scan; sampled counts stay evidence unless
  `allow_sampled_row_count_snapshot=true` is passed deliberately.
- `kind="column"` — one column profile. `update_map_column` (default true)
  writes observed column metadata into the map; set it false for scratch
  samples. Observed `physical_type`/`value_type` are stored as evidence
  either way and can surface later as type advisories.
- `kind="bundle"` — one pass that produced a dataset profile plus column
  profiles sharing run metadata. Pass `shared_evidence_iri` so the whole run
  is retrievable as a group; `column_defaults` sets repeated options such as
  `update_map_column: false`. Bundles can also create a linked pattern
  (`pattern_summary`/`pattern_text`/`pattern_rationale`;
  `pattern_support_scope="all_profiles"` widens its support).
- `kind="domain_network"` — reviewed aggregate sender/recipient-domain
  coverage for communication-like data. Aggregates only: no addresses,
  message IDs, subjects, or row samples.

Treat metrics, value frequencies, types, and counts as observed evidence, not
constraints or allowed values. Always fill `sample_scope` and `sample_method`
so later agents know what population the numbers cover. Metric kinds: use
base `rc:MinimumValue`/`rc:MaximumValue`/`rc:MeanValue`/`rc:MedianValue`/
`rc:StandardDeviationValue` when they fit (unknown `rc:` kinds are rejected,
so typos do not become RDF); use full project IRIs for profiler-specific
metrics and define them in `ontology` once they become shared vocabulary.

For reviewed no-I/O sidecars there are bulk doors: `record_map_fact` with
`kind="profiled_parquet_table"` (one table's reviewed schema + storage +
profile) or `kind="profile_manifest"` (several tables + caveats + views,
format `doxabase.profile_to_capsule_manifest.v1`). Companion CLIs —
`python -m doxabase.parquet_manifest` (scaffold from Parquet footers;
needs the `pyarrow` extra), `python -m doxabase.profile_manifest_merge`
(merge reviewed external aggregate facts), and
`python -m doxabase.profile_to_capsule` (apply a manifest file) — stay
outside MCP.

## Retrieving A Run

Start from `describe_dataset`: `profile_summary.profile_run_candidates`
names shared evidence IRIs supporting several returned profile rows. When
the bounded dataset lists omit rows, or before drafting map changes, call
`describe_resource(iri=dataset_iri, aspect="profile_run",
evidence_iri=...)` for the full run: dataset, mapped-column, and
unmapped-column profile lists with total/omitted counts. Columns profiled
with `update_map_column=false` appear under unmapped-column rows (with
`observed_column_name`) rather than as map columns — that is the design, not
a failure. For route-explained handoffs, seed `get_context_graph` with the
dataset, a profile observation, a metric node, or a project metric-kind IRI.

## Drafting Map Updates

Before staging anything, draft:

```text
stage_revision(kind="profile_map_updates", dry_run=true,
               spec={"dataset_iri": ..., "evidence_iri": ...})
```

Nothing is written. The draft compares the run with current map state and
separates the review lanes:

- **map updates** — default-stageable accepted facts, grouped by duplicate;
  accept one representative per group.
- **scalar conflicts** — same-evidence choose-one row-count or nullable
  options; pick at most one after reading the supporting rows, and after one
  choice is applied, siblings stay in conflict review — never stage them as
  ordinary updates just because a mechanical check would pass.
- **metric vocabulary** — project metric IRIs that lack ontology
  definitions; route through pattern promotion, not direct map writes.
- **type review** — observed physical/value types; turn them into map
  assertions only after review, via a staged assertion with the supporting
  pattern carried along.

A draft with no recommendations but open advisories is advisory-only: do not
stage just to clear it. Sampled row counts stay visible but are skipped by
default (`allow_sampled_row_count_updates` exists for the rare deliberate
case). The same dry-run door also serves the follow-through plan: adding
`result_bindings` (for example a freshly recorded `pattern_iri`) or
`staged_revision_iris` to the spec returns binding-resolved next actions and
staged-row rechecks instead of the bare draft.

## Staging Accepted Facts

```text
stage_revision(kind="profile_map_updates",
               spec={"dataset_iri": ..., "evidence_iri": ...,
                     "accepted_recommendation_indexes": [...]})
```

This stages ONE grouped reviewable revision (including any accepted
unmapped-column shells), so applying a batch does not strand sibling staged
rows in drift. Accepted indexes are still guarded — check `status_counts`
and item reasons: `staged`, `skipped` (for example sampled counts), and
`not_selected` (not accepted in this call) are all normal. If updates for
the same dataset/evidence pair are already staged, the helper refuses a
duplicate by default; review the pending row first
(`plan_staged_revision_recovery`) and pass
`allow_pending_profile_updates=true` only when a second staging is
intentional. After applying column shells, redraft — newly map-present
columns can expose ordinary recommendations that were invisible before.

Then the ordinary staged flow applies: `apply_staged_revision(dry_run=true)`
to check, apply one row, replan (see `staged_revisions`).

## Reviewing A Multi-Lane Run

When one run led to several staged lanes, export a grouped review:

```text
export_bundle(kind="profile_insight_review",
              spec={"dataset_iri": ..., "evidence_iri": ..., "path": ...})
```

It bundles the staged rows connected to the run (by evidence, supporting
observations, patterns, or anchors) with a route bridge back to the draft
lanes, open-lane accounting, and semantic apply gates. The gate fields are
the executor contract: mechanical readiness is not permission to bulk-apply
semantic choices. Require exactly one IRI in the safe-single-apply list,
check it with `apply_staged_revision(dry_run=true)`, apply that one row,
then redraft/re-export before further mutation. A candidate count of zero
writes no artifact — inspect warnings and open lanes before assuming the
review is resolved. The bundle carries the standard export privacy fields;
scanner-clean review Markdown still needs explicit shareability review.

Python API note: the library keeps the pre-fold helpers —
`db.record_dataset_profile`, `db.record_column_profile`,
`db.record_profile_bundle`, `db.describe_profile_run`,
`db.draft_profile_map_updates`, `db.plan_profile_followthrough`,
`db.stage_profile_map_updates`, and
`db.export_profile_insight_review_bundle` — with the same fields the MCP
doors take in `spec`.
