# Query Planning

Use this as the compact route from map metadata to a query-planning handoff.
For the fuller model, read `executable_catalog`; for exact field shapes, read
`response_shapes`.

Direct query helpers are table-oriented. For map datasets recorded with
`is_table=false`, `describe_query_context` returns
`readiness="not_applicable_non_tabular_asset"` with no query target candidates,
and `draft_query_plan` returns
`handoff_kind="not_applicable_non_tabular_asset"` rather than a file/database
scan. Use `describe_context_slice` or `describe_resource` for those assets
unless a separate queryable table route has been modeled.

When starting from a query metadata resource instead of a dataset, such as a
storage access, physical layout, partition scheme, or mapped column, call
`describe_context_slice(seed, profile="resource_brief")` first. If the slice
finds a directly owning table whose query context has repair groups or
operational warnings, `suggested_next_actions` will point to
`describe_query_context(table_iri)` so agents do not have to infer the dataset
handoff from generic incoming routes.

Query-planning helpers preserve reviewed non-secret handles faithfully:
source paths, result-source paths, endpoint profile names, credential-reference
handles, storage roots, URI templates, relation identifiers, and database
connection references can appear in `describe_dataset`, `describe_query_context`,
`draft_query_plan`, `describe_profile_run`, context slices, and exports. Treat
them as collaborator-visible planning metadata, not credentials. Do not paste raw
payloads into reports unless those handles and paths are safe for that audience;
summarize or redact surprising local/runtime references.

Before fixture query-planning trials against the active MCP capsule, sanity-check
`graph_overview.key_counts`. If AIS or Polymarket tables exist but
`storage_accesses == 0`, treat that capsule as stale or intentionally reduced
and load the current fixtures into a scratch capsule before drawing product
conclusions about query-target behavior. `describe_query_context` now carries
the same warning in `missing_storage_access.details.fixture_staleness_hint` when
known fixture tables are present with no storage access resources.

## AIS DailyIndex Question-To-Handoff Gap

The bundled AIS fixture is a representative reduced pressure test, not a full
executable AIS catalog. Do not silently "fix" its reduced shape unless the
fixture's purpose changes. For the current question-to-DuckDB-handoff gap, the
sensible smallest move is a walkthrough or example that overlays reviewed
metadata in a scratch capsule. The next larger product move is a separate full
executable AIS fixture/example.

Known exact gap:

- `ais:DailyIndex` currently inherits `ais:daily_date_partition`, whose
  `rc:pathTemplate` is `broadcasts/{year}/ais-{date}.parquet`. That is the
  broadcast route. The observed daily-index route used by DuckDB was
  `s3://ais-noaa/index/*/*.parquet`; the partition-shaped template is
  `index/{year}/ais-{date}.parquet`.
- The fixture's daily-index schema is reduced to `mmsi`, `date`,
  `message_count`, `first_timestamp`, `last_timestamp`, and `distance_m`.
  The observed index has `vessel_names` plus other list and statistic columns
  such as `imos`, `call_signs`, `vessel_types`, `cargos`, `lengths`, `widths`,
  `drafts`, `transceiver_classes`, `status_codes`, `duration_s`,
  `centroid_lat`, `centroid_lon`, `min_lat`, `max_lat`, `min_lon`, `max_lon`,
  `h3_cell_count`, `sog_min`, `sog_max`, `sog_mean`, and
  `max_inter_msg_speed_ms`. The observed broadcast files also include
  `vessel_name`, `imo`, `call_sign`, `vessel_type`, `status`, `length`,
  `width`, `draft`, `cargo`, `transceiver`, `cog`, and `heading`.
- Importing the AIS session-observation bundles makes this lore rediscoverable
  through `describe_context_slice(profile="dataset_brief")`, but it does not
  turn observation/evidence facts into current map facts. `describe_query_context`
  will still plan from the stale inherited broadcast partition until reviewed
  map metadata is added.

A scratch overlay that reaches a credible non-executed DuckDB handoff needs all
of these reviewed map moves:

1. Add `ais:ix_vessel_names` as a `rc:Column` on `ais:DailyIndex` with
   `rc:columnName "vessel_names"` and physical type `rc:VarcharList`.
2. Add a daily-index storage access linked to `ais:DailyIndex` with the existing
   non-secret S3-compatible facts and `rc:pathTemplate "index/*/*.parquet"`.
   Mark the route `rc:VerifiedByQueryLayout` only when the DuckDB/listing
   evidence is in scope.
3. Add a separate `ais:daily_index_date_partition` with
   `rc:pathTemplate "index/{year}/ais-{date}.parquet"` and
   `rc:partitionColumn ais:ix_date`.
4. Update `ais:DailyIndex` itself to `rc:VerifiedByQueryLayout` with a note that
   DuckDB verified the schema and `s3://ais-noaa/index/*/*.parquet` route.
5. Stage and apply removal of the inherited
   `ais:DailyIndex rc:partitionedBy ais:daily_date_partition` assertion. If
   that old link remains, the corrected index candidates stay context-blocked
   by the stale broadcast partition even when selected explicitly.
   `describe_query_context` exposes this as a reviewed
   `suggested_repair_action_groups` row with
   `repair_action_type="remove_stale_partition_scheme_link"` when a
   direct-clean selected candidate is blocked by the stale partition scheme.
   The same lane can expose
   `repair_action_type="remove_stale_physical_layout_link"` for a stale
   `rc:hasPhysicalLayout` link when a verified sibling layout with the same
   file-format/compression signature remains linked to the dataset.
   Distinct-signature linked layouts, for example verified Parquet plus
   candidate CSV, are intentionally treated as ambiguity rather than automatic
   stale-link cleanup. Review the layout-selection actions, then verify or remove
   the non-selected layout through an explicit reviewed graph change.

After those moves, the wildcard index candidate should draft as
`handoff_kind="runtime_resolution_required"` with
`scan.uri_template="s3://ais-noaa/index/*/*.parquet"`, no required bindings, and
`review_gate.executable_without_review=True`. It should still have
`ready_for_execution_attempt=False` until endpoint profile and credentials are
resolved outside DoxaBase.

Run `uv run python examples/ais-query-overlay-smoke.py` for the maintained
scratch version of this pressure test. It loads the reduced AIS fixture, records
the reviewed DailyIndex overlay, follows the stale partition-link repair group,
applies the staged removal, and confirms that `draft_query_plan` selects
`s3://ais-noaa/index/*/*.parquet` with only runtime resolution still blocking
execution.

## Field Precedence

Start with `describe_query_context(dataset_iri)`:

1. `query_target_decision` chooses the candidate. Its `candidate_index` points
   into `query_target_candidates`, and `status` routes the selected target's
   direct state: ready, review-only, blocked, or absent. Automatic selection
   prefers safer candidates first, then fewer required template bindings, then
   file/object scans before database relation handoffs when otherwise tied, then
   route-specific storage-access sources before broader partition or dataset
   templates within that same shape of handoff.
2. Read `unselected_ready_candidate_indexes`. If it is non-empty, the selected
   candidate has peer ready candidates; inspect `query_target_candidates` and
   pass an explicit `candidate_index` when a different route is intended.
   These indexes are candidate-local direct readiness, so they can be non-empty
   even when top-level `readiness == "needs_review"` because sibling metadata
   still blocks the whole context.
   When global context blockers are present, `ready_candidate_indexes` may be
   empty even though some candidates have no direct warning or error. In that
   case read `direct_clean_candidate_indexes` and
   `unselected_direct_clean_candidate_indexes` before choosing an explicit
   candidate with `allow_context_blocked_candidate=True`.
3. Read `row_count_snapshot` with `profile_summary` when profiler evidence
   informs planning. `profile_summary.profile_run_candidates` gives the
   evidence IRI(s) to inspect with `describe_profile_run` before treating a
   profile-derived count as fresh enough for a query handoff. Candidates are
   count-ranked; ties prefer evidence whose dataset-profile `row_count` matches
   `row_count_snapshot`, then fall back to evidence IRI order. In mixed profile
   history, inspect all profile-run actions before treating the profile-derived
   count as current; query context adds additional `describe_profile_run`
   actions when candidate row counts disagree, or when the snapshot-matching
   run is sampled, unknown, or mixed basis. Read
   `profile_summary.profile_run_candidates[].row_count_snapshot_basis` with
   each candidate's `dataset_profile_row_count_bases` to distinguish full-scan,
   sampled, and unknown-scope count support.
   When `profile_summary.evidence_iris` is non-empty but
   `profile_run_candidates` is empty, follow the singleton
   `describe_profile_run` action before drafting. This commonly means a
   profile-like `record_query_result` observation has one evidence-linked profile
   row; the action's `source_profile_evidence` preview carries query-source
   paths, result sources, structured execution status, engine, query hash when
   available, and the short profile summary.
   When physical storage/path/layout blockers remain, the same context may add a
   `draft_query_evidence_storage_overlay` skeleton action. Replace every
   placeholder named in its `placeholder_fields` / `reviewed_value_fields` and
   supply `required_extra_arguments` after reviewing the actual source; the
   helper does not infer storage values from query artifacts.
4. `query_target_candidates` explain the physical path, relation, template
   source, storage access, verification status, and review reasons.
   For non-database storage with `location_kind="object"`, prefer the exact
   `storage_access_location` candidate; candidates that append dataset or
   partition templates to that object root are review-only with
   `storage_object_location_has_path_template`.
   In mixed storage cases, do not assume `storage_access_iri` uniquely selects
   one plan. One storage access can produce both a partition-template candidate
   and a storage-access wildcard candidate. The safe unattended selector route
   is:

   ```python
   context = db.describe_query_context(dataset_iri)

   # Inspect context.query_target_candidates and the suggested draft actions.
   object_plan = db.draft_query_plan(
       dataset_iri,
       candidate_index=reviewed_object_candidate_index,
       physical_layout_iri=reviewed_object_layout_iri,
       allow_context_blocked_candidate=True,
   )

   database_plan = db.draft_query_plan(
       dataset_iri,
       candidate_index=reviewed_database_candidate_index,
       physical_layout_iri=reviewed_database_layout_iri,
       allow_context_blocked_candidate=True,
   )
   ```

   Use `draft_query_plan.handoff_summary` for the reportable result, then read
   `scan`, `review_gate`, `issues`, and `storage_environment` before execution.
   If similar storage is linked to another dataset, treat it as a
   `missing_storage_access` repair candidate only; review
   `linked_dataset_iris` and `match_reasons` before staging a link.
5. Always compare `readiness` and `issues` with the selected candidate. Broader
   context blockers, including sibling storage facts, can make the whole
   context review-required even when `query_target_decision.status == "ready"`
   for a direct-clean selected candidate.
   `query_target_decision.selected_candidate_direct_clean` is the compact
   boolean for "the selected candidate itself has no direct blocker."
   `analysis_warnings` are separate caveat warnings for interpretation after a
   plan is physically possible. For caveat warnings, read
   `details.caveat_severity_iri`; pause or narrow scope on severe caveats even
   when physical query planning is ready.
   When `missing_storage_access` appears, read its `details.repair_hint` before
   guessing at a path: either record reviewed non-secret storage access metadata
   and link it to the dataset, or stage a reviewed `rc:hasStorageAccess` link to
   an existing access resource. The repair hint includes
   `candidate_existing_storage_accesses` when current map storage accesses exist;
   use those ranked candidates for review only. A candidate can carry
   `pending_staged_repair_iris` and `candidate_status="already_pending"` when
   the exact dataset/storage link is already staged. When any visible candidate
   is already pending, the repair hint and lifted repair group also expose
   `already_pending_candidate_count`, `already_pending_storage_access_iris`, and
   `pending_staged_repair_iris`; review those staged rows before choosing the
   same candidate again. Candidate ranking now includes exact path-template
   matches, dataset-token overlap with labels/IRIs/locations, weaker separately
   reported generic-token overlap, and a linked-dataset caution when an access
   is already attached elsewhere. Do not auto-link the first candidate just
   because it is listed; fill
   the staged link's `object` with the chosen reviewed access IRI. When recording
   a new storage access, omit the
   optional storage-owned `path_templates` field if the dataset
   or partition already carries the reviewed path template; duplicating it can
   create equivalent ready candidates. Database relation identifiers are the
   important exception and should be recorded as storage-access-owned templates.
   After direct database-storage repair, rerun `describe_query_context`; if the
   same relation-like value still lives on the dataset or partition, follow the
   `database_relation_template_source_mismatch` repair group to remove or move
   that misplaced template. Direct `record_map_storage_access` repairs do not
   record graph-revision rationale, so preserve the reviewed rationale in the
   calling workflow or use staged assertion helpers when durable review history
   matters.
   For controlled field examples, read the `executable_catalog` storage-access
   recipe; a local read-only directory access uses
   `storage_protocol="rc:LocalFilesystemStorage"`,
   `access_mode="rc:ReadOnlyAccess"`, and `location_kind="directory"`.
6. Use `suggested_repair_action_groups` when scripting metadata repairs. It is a
   top-level `query_repair_review` lane over existing
   `issues[].details.repair_hint.actions[]`, preserving issue index/code/resource
   and ordered repair templates. In `project_brief`, `query_repair_review`
   means this lane exists, while `query_context_review` can mean the dataset is
   blocked by layout, verification, runtime, or binding review but has no
   repair template to follow yet. Follow that task's `describe_query_context`
   action before using any review-gated `draft_query_plan` action preserved in
   the dataset summary. Review-gated `draft_query_plan` handoffs also copy the
   first non-skippable pending repair option into
   `handoff_summary.primary_repair_*`; use that as a compact cue, then read the
   full repair group before staging a metadata change. Read
   `pending_action_count`, `skippable_action_count`, `action_status_counts`, and
   `pending_action_options` before routing a group. The compact options carry
   branch labels plus available `reason`, `condition`, and
   `review_rationale_guidance`; database relation template mismatch options also
   carry `misplaced_template_subject_iri`, `misplaced_template_source`, and
   `misplaced_template` so scripts can distinguish dataset and partition sources
   without parsing action arguments. Use the full action templates when you need
   call arguments or rationale/protocol templates. `choice_mode="choose_one"`
   means the actions are alternatives; use the selected action's own
   `required_extra_arguments` rather than the group-level union in
   `pending_required_extra_arguments`. Mixed database relation repairs can
   include an already-satisfied action that should be skipped after the pending
   cleanup is reviewed. Context-blocked direct-clean routes can also expose a
   `remove_stale_partition_scheme_link` template for a stale
   `rc:partitionedBy` assertion, or
   `remove_stale_physical_layout_link` for a stale `rc:hasPhysicalLayout`
   assertion when a verified matching physical layout remains linked. When
   storage is already linked but no physical layout is present,
   `missing_physical_layout` exposes a reviewed
   `record_map_physical_layout` template; for database storage, choose a
   database table layout such as `rc:PostgreSQLTable`, `rc:SQLiteTable`, or
   `rc:MySQLTable` after review. These are reviewed templates, not call-ready
   `suggested_next_actions`: fill placeholders, add required fields such as
   `rationale`, skip actions marked `already_satisfied` or `already_pending`,
   and check each `condition` before calling the named tool.
   In multiple-candidate missing-storage groups, the group-level
   `stage_existing_storage_access_link` action may still be pending because a
   different non-pending candidate could be chosen after review; use the
   pending-candidate summary fields on its compact action option to avoid
   staging a duplicate link to a candidate that is already pending.
   If `project_brief.recommended_next_tasks[]` reports
   `pending_staged_repair_iris` for a query repair task, review the corresponding
   `staged_frontier_review` / `staged_review` item before staging another
   repair. The pending staged row is already anchored to the dataset or a linked
   query resource such as a storage access, physical layout, partition scheme, or
   column, and changes query-planning metadata such as storage links, path
   templates, storage fields, physical-layout fields, or partition metadata.
   When any current staged work exists, project brief also orders
   returned `staged_review` rows ahead of fresh query-repair staging tasks; use
   `health_tasks` / `omitted_queue_counts` to widen the brief if a fresh repair
   queue is omitted by a low limit.
   Exact matching actions in `describe_query_context.suggested_repair_action_groups`
   are marked `already_pending`; unrelated same-dataset caveat/profile work
   remains only in the staged-review lanes.
7. Use `suggested_next_actions` when scripting the next step. If profile run
   candidates exist, profile evidence inspection actions come before query-plan
   drafting; when multiple candidate runs need review, several
   `describe_profile_run` actions can appear before the first `draft_query_plan`.
   Peer ready or context-blocked direct-clean candidates are also exposed as
   explicit `draft_query_plan(candidate_index=...)` actions, so scripts should
   follow actions instead of parsing peer indexes from prose or storage-selector
   ambiguity errors. In the context-blocked direct-clean case, draft actions
   include `allow_context_blocked_candidate=True`.

A common non-error shape is:

```text
readiness = "needs_review"
query_target_decision.status = "ready"
ready_candidate_indexes = [1, 3, 4]
unselected_ready_candidate_indexes = [3, 4]
issues = ["database_relation_template_source_mismatch"]
suggested_next_actions[0].arguments = {
    "iri": dataset_iri,
    "candidate_index": 1,
    "allow_context_blocked_candidate": True,
}
```

Here `ready_candidate_indexes` means candidate-local direct readiness, not
global context readiness. Follow the structured draft action when it matches
your intended candidate; it preserves the sibling issue audit in the resulting
review gate while allowing the clean selected route to draft.

Then call `draft_query_plan(dataset_iri)` for a non-executed handoff:

1. `handoff_kind` is the compact machine-readable route. Use it for first-pass
   client dispatch, then read `review_gate`, `scan`, `binding_requirements`,
   and `storage_environment` for the details behind that route.
   Do not treat `handoff_kind` alone as execution permission:
   `database_relation_handoff` means the selected route is a relation/connection
   handoff, while `review_gate.ready_for_execution_attempt` is the strict gate
   for any execution attempt.
2. Read `source_context.unselected_ready_candidate_indexes`. It mirrors the
   context-level peer-ready route after applying any explicit selection.
   Also read `source_context.unselected_direct_clean_candidate_indexes` when the
   source context is blocked by sibling metadata; those candidates may be usable
   for a review-gated draft with an explicit selector even while
   `ready_candidate_indexes` is empty.
   Candidate order is not an authoring-preference contract. Treat
   `candidate_index` as a pointer into the returned list; use the selected
   decision and peer indexes to compare materially different ready routes.
3. Read `source_context.selected_candidate_note` for a compact handoff summary
   of the selected candidate, route kind, and sibling/context blocker codes
   that still remain in `review_gate.all_issue_codes`.
4. `scan.uri_template` is for file/object scans.
5. `scan.relation_identifier` is the database-backed storage handoff; do not
   treat the candidate path as a file URI in that case. Relation identifiers
   come from storage-access-owned templates, not dataset or partition file paths.
   `scan.connection_reference` without `scan.relation_identifier` is
   repair/review context, not a database relation handoff.
   A successful database-storage repair loop can still leave
   `ready_for_execution_attempt=false`: clear `missing_storage_access`, add the
   reviewed physical layout, move/add the relation template onto the storage
   access, remove the misplaced dataset or partition template, then treat
   `handoff_kind="database_relation_handoff"` plus `scan.relation_identifier`
   as the non-executed handoff success signal.
   Mixed object/database metadata does not treat dataset or partition file
   templates as database-relation repair work when those templates already form
   a clean non-database candidate. If
   `database_relation_template_source_mismatch` still appears, either no clean
   file/object route was available for that template or the intended database
   route still needs a reviewed storage-access-owned relation identifier.
6. `scan.function` is only a hint when the physical layout is unambiguous. If a
   dataset links multiple distinct file formats or compression codecs,
   `ambiguous_physical_layout` blocks execution-readiness and leaves the scan
   function unset. After reviewing the linked layouts, pass
   `physical_layout_iri` to `draft_query_plan` to select one for that draft; the
   source context records the requested layout and `scan.physical_layout`
   records the selected layout. `describe_query_context.suggested_next_actions`
   includes one `draft_query_plan` action per distinct linked layout signature
   for the selected candidate, plus peer candidates whose only direct blocker
   is layout ambiguity, so scripts can choose a reviewed layout without parsing
   issue details by hand.
   When a single linked physical layout is unambiguous but a clear candidate
   path extension conflicts with it, for example `.csv` with `rc:Parquet`,
   `physical_layout_path_extension_mismatch` keeps the candidate review-gated
   and `ready_for_execution_attempt=false`. Treat the scan function as review
   context until either the path/template or the layout file format is fixed.
7. `required_bindings` and `binding_requirements` still need runtime values.
   `review_gate.binding_values_required=True` and
   `handoff_kind="binding_values_required"` make that case explicit. When a
   selected template comes from partition metadata, binding rows may include
   `partition_scheme`, `partition_column`, and `partition_granularity` as
   handoff hints; the granularity describes the partition scheme, not
   necessarily the individual placeholder. When a partition-owned placeholder
   does not match a declared partition column, or when a dataset/storage-owned
   placeholder is used, the row may include `candidate_column_matches` when
   placeholder names match dataset columns exactly or by suffix.
   `candidate_column_match_status` says whether those hints are absent,
   singular, or ambiguous. These fields help humans and agents find likely
   source columns; they do not supply execution-time values, and ambiguous rows
   need review before choosing any source column. Treat `confidence` as a
   per-match score; `candidate_column_match_status` summarizes the whole
   binding.
7. `review_gate.executable_without_review` says graph metadata has no recorded
   review blocker for the selected candidate.
8. `storage_environment.runtime_resolution_required` says endpoint, credential,
   region, or equivalent runtime context still needs resolving.
9. `review_gate.ready_for_execution_attempt` is the stricter handoff boolean:
   it is true only when the review gate is clear, runtime resolution is not
   required, and no required binding placeholders remain in the selected
   template.
   Do not treat `review_gate.status="ready"` as execution permission. After
   selecting an ambiguous `physical_layout_iri`, the selected candidate can have
   `status="ready"` while `ready_for_execution_attempt` and
   `scan.execution_attempt_ready` remain false because sibling context blockers,
   runtime resolution, or binding placeholders still need review.
   Runtime-only cases may also have empty `blocking_reason_codes` and
   `all_issue_codes`; route from `execution_attempt_blocking_reason_codes` when
   `ready_for_execution_attempt` is false.
   `scan.execution_attempt_ready` mirrors this boolean next to the scan fields
   so clients do not need to leave the scan card to see whether scan hints are
   eligible for an execution attempt.
   `review_gate.blocking_reason_codes` can add
   `query_context_has_other_blockers` when the selected candidate is clean but
   the broader query context is not.
   `review_gate.execution_attempt_blocking_reason_codes` folds in non-review
   execution blockers such as runtime resolution and missing binding values, so
   it is the better machine-routing list when this boolean is false.
   `review_gate.primary_execution_attempt_blocking_reason_code` is the first
   code from that ordered list, or `None` when the plan is execution-attempt
   ready. `scan.primary_execution_attempt_blocking_reason_code` and
   `scan.execution_attempt_blocking_reason_codes` mirror those values beside
   `scan.uri_template` and `scan.relation_identifier`.

For downstream consumers, keep the routing order simple:

1. If `review_gate.ready_for_execution_attempt` is true, and the plan still
   matches the intended client/runtime, a non-executing handoff may become an
   execution-attempt candidate.
2. Otherwise, if `scan.relation_identifier` is present, route it as a database
   relation handoff before generic runtime resolution. The relation can be
   useful even when execution is not ready. A `scan.connection_reference` without
   a relation is repair/review context.
3. Otherwise, route `review_gate.primary_execution_attempt_blocking_reason_code`
   first, using `review_gate.execution_attempt_blocking_reason_codes` for the
   full ordered detail. Then inspect
   `storage_environment.runtime_resolution_required`,
   `review_gate.binding_values_required`, and remaining
   `blocking_reason_codes` / `all_issue_codes`. Empty blocking codes or
   `executable_without_review=True` do not override a false
   `ready_for_execution_attempt`.
4. Treat `binding_requirements`, partition hints, and candidate column matches
   as review hints. They do not supply runtime values.

If a reviewed plan is executed by an external runtime, record the result or
failure with `record_query_result`. Use `result_sources` for arbitrary aggregate
payloads such as grouped counts or JSON output; fill profile-shaped fields such
as `row_count` only when `summary`, `sample_scope`, and `sample_method` make
their meaning unambiguous. For local smoke tests, a Python CSV fallback is fine
when DuckDB is unavailable as long as `engine` and `sample_method` say what
actually ran. `record_query_result` stores execution status, engine, and query
hash as structured evidence metadata, so custom evidence summaries still remain
machine-readable in later query-context handoffs.
When `observed_asset` is supplied, follow the returned
`suggested_next_actions`: profile-shaped results start with
`describe_profile_run(dataset_iri=observed_asset, evidence_iri=...)`, and all
observed-asset results include `describe_query_context(iri=observed_asset)`.

If that evidence identifies a reviewed source but the map still lacks physical
query-planning metadata, call `draft_query_evidence_storage_overlay` with the
dataset IRI, evidence IRI, and reviewed storage/path/layout values. The helper
does not parse query artifacts to guess storage. It returns validation-previewed
`stage_graph_revision` arguments that add storage access and physical layout
metadata with the query/profile observation as support. Stage, check, apply,
and rerun `describe_query_context` before drafting the next plan.
When `describe_query_context.suggested_next_actions` proposes this overlay from
singleton evidence, use the action as a template only: replace placeholder
storage protocol, root, location kind, path template, file format, and layout
note values with reviewed non-secret values before calling.
If the dataset already has a different layout verification status or note, the
drafted stage arguments may include removal patches for those old dataset-level
values. Keep them with the addition patch; otherwise the reviewed overlay can
fail the single-status/single-note SHACL constraints.

When a known-good storage route is blocked only by stale or malformed sibling
metadata, keep `describe_query_context()` as the inventory and call
`draft_query_plan(..., candidate_index=..., allow_context_blocked_candidate=True)`
or `draft_query_plan(..., storage_access_iri=..., allow_context_blocked_candidate=True)`.
Do not use the allowance selectorless: the automatic selection path keeps the
context review gate active and reports `context_blocked_candidate_allowed=True`
with `context_blocked_candidate_used=False` until the caller names an explicit
candidate. When peer ready candidates are present, prefer the suggested
`draft_query_plan` actions; they include `allow_context_blocked_candidate=True`
when sibling candidate metadata is the only broader blocker.
The source context keeps the automatic `query_target_decision` plus the explicit
selection mode, and the review gate reports whether a context-blocked candidate
was used. Only use this switch when `direct_review_required` is false for the
selected candidate; direct blockers still keep the plan review-gated.
Interpret the allowance fields together: `allowed=false/used=false` means no
override was requested; `allowed=true/used=true` means sibling-only context
blockers were excluded for this selected candidate; `allowed=true/used=false`
with no direct blocking codes usually means the selected candidate was already
ready or had no sibling-only context blockers to exclude; `allowed=true/used=false`
with direct blocking codes means the switch did not apply and the candidate
still needs review.

When `storage_access_iri` matches multiple candidate paths, the error includes
compact candidate snippets. Choose from those snippets and rerun with
`candidate_index`; the storage selector must identify exactly one candidate.
This can happen even for database storage when the same storage access is linked
to dataset or partition template review cards; use the candidate snippet for the
storage-owned relation when you want the database relation handoff.

## Common Cases

Local file/object candidates can be ready for an execution attempt when the
path or template is verified enough, the scan function is inferred, and runtime
resolution is not required. Still supply binding values and perform ordinary
filesystem/object-existence checks before running anything.

S3-compatible candidates often need endpoint profile, credential reference, and
region or equivalent local runtime setup. DoxaBase records non-secret planning
facts; it does not store secrets or prove the object exists.
When `storage_protocol_location_mismatch` appears, read
`details.repair_hint` before hand-authoring a repair. It offers reviewed
`stage_map_assertion_change` templates for fixing protocol/root/bucket/prefix
metadata and, when a path template caused the mismatch, adding a reviewed
replacement template or removing the conflicting exact template. Templated
protocol/location actions name `placeholder_fields` and
`reviewed_value_fields` for the reviewed value to copy into the call.

Database candidates currently use the generic draft-plan shape. A relation can
be metadata-ready in `describe_query_context()` while
`draft_query_plan().review_gate.executable_without_review` is false because the
generic DuckDB file-scan function is not inferred. Use
`relation_identifier` and `connection_reference` as the handoff, then verify the
database connection outside DoxaBase.
For database storage, only a storage-access-owned path template is treated as a
relation identifier. Dataset or partition path templates paired with database
storage are review-only inventory cards with
`database_relation_template_source_mismatch`, even when the template text looks
like `schema.table`; record the schema/table/relation on the storage access
before using a database handoff. The issue carries
`details.repair_hint` with ordered, review-gated
`stage_map_assertion_change` templates; follow `repair_hint.actions` order. In
the common move case, add the reviewed relation identifier to the storage
access, then remove the misplaced source template only if review confirms it was
relation metadata rather than a real file/object path. If the storage access
already carries relation template(s), the remove action is first and the add
action is marked `action_status="already_satisfied"` with
`skip_when_already_satisfied=true`, so automation should skip that duplicate
add and inspect `candidate_relation_identifier.storage_access_relation_templates`
instead. Repair hints and compact pending options carry
`misplaced_template_subject_iri`, `misplaced_template_source`, and
`misplaced_template` for distinguishing dataset-owned and partition-owned stale
templates that share the same storage access issue resource; compare them
against the query target candidates. Each add-template repair declares
`required_extra_arguments=["object", "rationale"]` and
`placeholder_fields=["object"]`; replace `object` with the reviewed relation
identifier and add a reviewed rationale before calling
`stage_map_assertion_change`. The stale dataset or partition path is context for
review, not the relation identifier. Root-only database storage without such a
template carries `database_relation_template_missing` even when
`location_kind == "object"`;
its `details.repair_hint` gives the reviewed add-template action for the
storage access. After applying each query-planning metadata repair, rerun
`describe_query_context` for the dataset before applying the next repair or
drafting a plan; apply responses route staged frontier recovery, not the full
query-context repair checklist.

If `runtime_resolution_required=False` for bare database storage, read the note
before treating it as reachable. The boolean only says there is no recorded
endpoint or credential profile left for DoxaBase to resolve; it is not a
database connectivity guarantee.

Current `handoff_kind` values are `no_query_target`,
`not_applicable_non_tabular_asset`, `metadata_review_required`,
`context_review_required`, `runtime_resolution_required`,
`database_relation_handoff`, `binding_values_required`, and
`execution_attempt_ready`.
