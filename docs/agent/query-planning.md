# Query Planning

Use this as the compact route from map metadata to a query-planning handoff.
For the fuller model, read `executable_catalog`; for exact field shapes, read
`response_shapes`.

Direct query helpers are table-oriented. For map datasets recorded with
`is_table=false`, `describe_query_context` returns
`readiness="not_applicable_non_tabular_asset"` with no query target candidates,
and `draft_query_plan` returns
`handoff_kind="not_applicable_non_tabular_asset"` rather than a file/database
scan. Candidate layout or storage warnings on those assets are context for
handoff review, not query-repair work. Use `describe_context_slice` or
`describe_resource` for those assets unless a separate queryable table route has
been modeled.

When starting from a query metadata resource instead of a dataset, such as a
storage access, physical layout, partition scheme, or mapped column, call
`describe_context_slice(seed, profile="resource_brief")` first. If the slice
finds directly owning table(s), `suggested_next_actions` can point to
`describe_query_context(table_iri)` for each bounded owner. Follow those actions
when the owner has repair groups or operational warnings, and also when a
storage/layout/partition seed has multiple clean queryable owners so you choose
the intended table before drafting a plan.

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
the same warning in `missing_storage_access.details.fixture_staleness_hint` and
on the lifted repair group's `group_advisories` when known fixture tables are
present with no storage access resources.

The reduced Polymarket fixture can already contain enough storage, layout, and
partition metadata to produce a non-executed file handoff. For example,
`pm:Trades` can draft a DuckDB `read_parquet` handoff with required `{date,hour}`
bindings. Do not turn manifest-derived review notes into verified execution
readiness: `rc:GeneratedFromManifestLayout` is honest review context and may
route the plan to `metadata_review_required` / `layout_needs_verification`.
Only use `rc:VerifiedByListingLayout` or `rc:VerifiedByQueryLayout` after a
real listing, schema check, or query result is in scope. Recording a blocked
`record_query_result` for the handoff is preferable to pretending DoxaBase
executed or verified a local data lake mount.

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
   If the selected candidate uses a dataset-owned path template and storage plus
   physical layout metadata are already verified, a remaining dataset-scoped
   `layout_needs_verification` issue exposes
   `repair_action_type="replace_dataset_layout_verification_status"`. Choose the
   `rc:VerifiedByListingLayout` or `rc:VerifiedByQueryLayout` action only after
   reviewing the evidence type; the action stages a
   `stage_map_assertion_change` replacement for the dataset's
   `rc:layoutVerificationStatus`.

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
   into `query_target_candidates`, and each candidate also carries a stable
   `candidate_selector` for reviewed follow-up calls. `status` routes the
   selected target's direct state: ready, review-only, blocked, or absent.
   Automatic selection
   prefers safer candidates first, then fewer required template bindings, then
   file/object scans before database relation handoffs when otherwise tied, then
   route-specific storage-access sources before broader partition or dataset
   templates within that same shape of handoff.
2. Read `unselected_ready_candidate_indexes`. If it is non-empty, the selected
   candidate has peer ready candidates; inspect `query_target_candidates` and
   pass an explicit `candidate_selector` when a different route is intended.
   Candidate cards inherit storage-access `route_roles`, so prefer reviewed roles
   such as `rc:ProductionRoute`, `rc:CurrentRoute`, `rc:SampleRoute`,
   `rc:ArchiveRoute`, `rc:BackfillRoute`, and `rc:CanonicalRoute` over labels or
   path names when choosing among otherwise-ready routes.
   `query_target_decision.peer_ready_requires_intent_review` and
   `selection_caution` carry the same warning in a compact form, while
   `selection_reason_codes` records whether the selected route came from
   automatic ranking or an explicit selector. Treat automatic selection among
   peer ready candidates as precedence, not project intent.
   If `query_target_decision.route_intent_review_candidate_indexes` is non-empty,
   the selected candidate skipped ready, direct-clean, or layout-review-gated
   peer card(s) with reviewed production/current/canonical route intent. Inspect
   those cards and pass their `candidate_selector` when that route is intended.
   In that case, `draft_query_plan` suggested actions also mark the automatic
   selected action with `unattended_recommended=false` and the route-intent peer
   action(s) with `unattended_recommended=true`. Prefer
   `first_unattended_action_index` or
   `unattended_recommended_action_indexes[]` over following the first draft
   action blindly.
   If `safe_inspection_action_indexes[]` is non-empty, follow
   `first_safe_inspection_action_index` first for read-only evidence inspection
   such as `describe_profile_run`; then use the unattended draft-plan indexes
   after the evidence context is understood.
   These indexes are candidate-local direct cleanliness or resolvable layout
   ambiguity, so they can be non-empty even when strict
   `ready_candidate_indexes` is empty because sibling metadata or physical
   layout ambiguity still blocks the whole context.
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
   helper does not infer storage values from query artifacts. After the draft,
   use `reviewed_overlay` to audit the supplied non-secret storage/layout IRIs,
   labels, route roles, access mode, endpoint/bucket/prefix/region/path-style
   fields, credential reference, compression, and verification fields without
   parsing Turtle patch content.
   If ordinary non-profile `record_query_result` evidence is linked to the
   dataset and physical metadata blockers remain, the same overlay skeleton can
   appear with `source_query_evidence.profile_observation_count == 0`; use its
   scanned source paths/handles and result sources as provenance, not as
   automatic storage metadata.
4. `query_target_candidates` explain the physical path, relation, template
   source, storage access, verification status, and review reasons.
   They also carry storage-access `route_roles`; use those reviewed route intent
   facts to distinguish production/current/canonical routes from sample, archive,
   or backfill routes before unattended execution.
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
      candidate_selector=reviewed_object_candidate_selector,
      physical_layout_iri=reviewed_object_layout_iri,
      allow_context_blocked_candidate=True,
   )

   database_plan = db.draft_query_plan(
       dataset_iri,
       candidate_selector=reviewed_database_candidate_selector,
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
   guessing at a path: prefer `stage_query_storage_access_repair` for a reviewed
   new non-secret storage access and dataset link, use
   `record_map_storage_access` only when a direct current-best map write is
   intentional, or stage a reviewed `rc:hasStorageAccess` link to an existing
   access resource. Include `route_roles` on staged or direct storage repairs
   when the reviewed route is production/current/canonical, sample, archive, or
   backfill. The repair hint includes
   `candidate_existing_storage_accesses` when current map storage accesses exist;
   use those ranked candidates for review only. Existing-candidate rows carry
   `route_roles` and `route_role_labels`; prefer those reviewed route-intent
   fields over labels or path strings when deciding whether to link a
   production/current, sample, archive, backfill, or canonical route. A
   candidate can carry
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
   actions whose `action_status` is `pending_review`, the normal actionable
   state for review-gated repair templates. They also carry branch labels plus
   available `reason`, `condition`, and
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
   `missing_physical_layout` exposes
   `repair_action_type="record_or_stage_physical_layout"`. Prefer the
   `stage_query_physical_layout_repair` option when the reviewed layout should
   carry graph-revision rationale; use the `record_map_physical_layout` option
   only when a direct current-best map write is intentional. For database
   storage, choose a database table layout such as `rc:PostgreSQLTable`,
   `rc:SQLiteTable`, or `rc:MySQLTable` after review. These are reviewed
   templates, not call-ready `suggested_next_actions`: fill placeholders, add
   required fields such as `rationale`, skip actions marked `already_satisfied`
   or `already_pending`, and check each `condition` before calling the named
   tool.
   After applying staged storage and physical-layout repairs, rerun
   `describe_query_context` before drafting a plan. A dataset-owned template can
   still be blocked by the dataset's stale `rc:CandidateLayout`; when the
   prerequisites are satisfied, follow the
   `replace_dataset_layout_verification_status` repair group rather than
   hand-authoring a generic graph revision.
   When the repair came from a profile draft's `query_context_review` lane,
   keep the profile route source on each staged repair. If applying the first
   storage/layout repair makes a pre-staged sibling stale, run
   `plan_staged_revision_recovery`, dry-run or review the restage route, restage
   the sibling, recheck the successor, then apply it before drafting the final
   query plan.
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
   Repair groups can carry `group_advisories` for group-level routing warnings.
   For known AIS or Polymarket fixture tables with zero storage accesses, the
   missing-storage repair group repeats the fixture-staleness cue there so
   scripts that follow only `suggested_repair_action_groups` still pause before
   staging repeated per-table repairs. The advisory does not remove or mark
   actions as skipped; it says to review the stale/reduced fixture condition
   first.
   If `project_brief.health_tasks[]` includes
   `query_fixture_staleness_review`, known AIS or Polymarket fixture tables are
   present while `storage_accesses` is zero. Treat that as an advisory
   stale/reduced-capsule cue: inspect the representative query context or load
   fresh fixtures into scratch before staging a series of missing-storage
   repairs.
   In a fresh scratch capsule loaded with current fixtures, this staleness
   warning should disappear once storage access metadata exists. Polymarket
   tables such as `pm:Trades` can reach a reviewed query-plan handoff from
   fixture metadata, while AIS `DailyIndex` may still be `needs_review` because
   its inherited broadcast partition/layout gap is intentional. Do not interpret
   fresh-but-review-gated AIS as a failed fixture refresh.
   Exact matching actions in `describe_query_context.suggested_repair_action_groups`
   are marked `already_pending`; unrelated same-dataset caveat/profile work
   remains only in the staged-review lanes.
   For a maintained no-network repair walkthrough, run
   `examples/missing-metadata-query-repair-smoke.py`; it stages storage repair
   first, reruns `describe_query_context`, then stages physical-layout repair
   before drafting the final CSV handoff.
   Cold repair loop in compact form:

   ```python
   context = db.describe_query_context(dataset_iri)
   repair_group = context.suggested_repair_action_groups[0]
   repair_action = repair_group.pending_action_options[0]
   staged_storage = db.stage_query_storage_access_repair(...)
   db.apply_staged_revision(staged_storage.revision_iri)

   context = db.describe_query_context(dataset_iri)
   staged_layout = db.stage_query_physical_layout_repair(...)
   db.apply_staged_revision(staged_layout.revision_iri)

   plan = db.draft_query_plan(dataset_iri)
   ```

   Treat `suggested_repair_action_groups` as the metadata mutation lane. A
   `suggested_next_actions[]` entry for `draft_query_plan` can still be a
   review or handoff route while metadata is insufficient; it is not a signal
   to skip the repair group. After drafting, use
   `execution_attempt_blocking_reason_codes` for execution blockers. Broader
   fields such as `all_issue_codes` may still include informational context,
   for example a verification note that did not block the selected handoff.
7. Use `suggested_next_actions` when scripting the next step. If profile run
   candidates exist, profile evidence inspection actions come before query-plan
   drafting; when multiple candidate runs need review, several
   `describe_profile_run` actions can appear before the first `draft_query_plan`.
   Peer ready or context-blocked direct-clean candidates are also exposed as
   explicit `draft_query_plan(candidate_selector=...)` actions, so scripts
   should follow actions instead of parsing peer indexes from prose or
   storage-selector ambiguity errors. In the context-blocked direct-clean case,
   draft actions include `allow_context_blocked_candidate=True`.

A common non-error shape is:

```text
readiness = "needs_review"
query_target_decision.status = "ready"
ready_candidate_indexes = [1, 3, 4]
unselected_ready_candidate_indexes = [3, 4]
issues = ["database_relation_template_source_mismatch"]
suggested_next_actions[0].arguments = {
    "iri": dataset_iri,
    "candidate_selector": "query-target:...",
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
   For database-backed repairs, expect a reviewed two-step loop when both
   storage access and physical layout are missing: stage/apply the
   `rc:DatabaseStorage` access with a reviewed relation identifier and
   connection reference, rerun `describe_query_context`, then stage/apply a
   table layout such as `rc:SQLiteTable`, `rc:PostgreSQLTable`, or
   `rc:MySQLTable` before drafting the final relation handoff.
2. Read `source_context.unselected_ready_candidate_indexes`. It mirrors the
   context-level peer-ready route after applying any explicit selection.
   Also read `source_context.unselected_direct_clean_candidate_indexes` when the
   source context is blocked by sibling metadata; those candidates may be usable
   for a review-gated draft with an explicit selector even while
   `ready_candidate_indexes` is empty.
   Candidate order is not an authoring-preference contract. Treat
   `candidate_index` as a response-local pointer into the returned list; use the
   candidate's `candidate_selector` for a reviewed follow-up call.
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
   includes one `draft_query_plan` action per compatible linked layout signature
   for the selected candidate, omitting signatures whose known file format
   conflicts with the candidate path extension, plus peer candidates whose only
   direct blocker is layout ambiguity, so scripts can choose a reviewed layout
   without parsing issue details by hand. File/object routes are paired with
   file layouts such as `rc:CSV` or `rc:Parquet`; database routes are paired
   with table layouts such as `rc:PostgreSQLTable`, `rc:SQLiteTable`, or
   `rc:MySQLTable`.
   If a caller explicitly selects a cross-route pair, for example a database
   relation with `rc:CSV`, `physical_layout_storage_protocol_mismatch` keeps
   the plan review-gated.
   When a single linked physical layout, or a caller-selected physical layout,
   conflicts with a clear candidate path extension, for example `.csv` with
   `rc:Parquet`, `physical_layout_path_extension_mismatch` keeps the candidate
   review-gated and `ready_for_execution_attempt=false`. Treat the scan
   function as review context until either the path/template or the layout file
   format is fixed.
   Database relation handoffs intentionally leave `scan.function=None`; the
   relation identifier and connection reference are the handoff, and execution
   readiness is blocked by runtime resolution rather than by a missing DuckDB
   file-scan function.
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
payloads such as grouped counts or JSON output; use `scanned_source_paths` for
non-secret source files, object keys, or URI-like inputs that should become
`rc:DataSampleSource` spans; use `scanned_source_handles` for reviewed source
handles the external runtime actually scanned. For `database_relation_handoff`,
a value like
`warehouse-prod:mart.orders` is a suitable reviewed handle when it combines the
plan's `scan.connection_reference` and `scan.relation_identifier`; do not invent
a filesystem path. Fill profile-shaped fields such as `row_count` only when
`summary`, `sample_scope`, and `sample_method` make their meaning unambiguous.
For local smoke tests, a Python CSV fallback is fine when DuckDB is unavailable
as long as `engine` and `sample_method` say what actually ran.
`record_query_result` stores execution status, engine, query hash, query-source
paths, and scanned source paths as structured evidence metadata, so custom
evidence summaries still remain machine-readable in later query-context
handoffs.
After recording the result, follow the returned
`describe_context_slice(seed_iris=[evidence_iri], profile="resource_brief")`
action when you need the exact result evidence, relation handle, source span, or
scanned path/handle trail. The returned `describe_query_context` action is for
the refreshed dataset handoff; it is not a substitute for evidence inspection.
Directory storage with a reviewed wildcard CSV path template can also reach
`handoff_kind="execution_attempt_ready"`; after an external aggregate, seed
`describe_context_slice(profile="deep_lore")` from the dataset, returned
observation, or evidence IRI when the result artifact and scanned source paths
need to travel with the handoff. Dataset-seeded slices include a bounded set of
recent ordinary `rc:observedAsset` observations, including blocked or failed
query-result attempts; seed the returned observation or evidence IRI for a
narrower export when only that attempt should travel.
When `observed_asset` is supplied, follow the returned
`suggested_next_actions`: profile-shaped results start with
`describe_profile_run(dataset_iri=observed_asset, evidence_iri=...)`, and all
observed-asset results include `describe_query_context(iri=observed_asset)`.
For blocked or failed external query attempts, still record the failure with
`record_query_result(execution_status="blocked"|"failed", ...)`. If a broad
handoff preflight later blocks on unrelated dirty graph content, seed
`preflight_context_slice_export` from the returned `evidence_iri` with
`profile="resource_brief"` so the query status and source-span evidence can
travel without unrelated map siblings.

For a cold query-result handoff where the map has no executable storage
metadata yet, use this sequence:

1. Record the external result with `record_query_result(..., observed_asset=...)`.
2. Follow the returned `describe_query_context` action.
3. If the context suggests `draft_query_evidence_storage_overlay`, copy that
   action as a skeleton only. Replace every placeholder with reviewed
   non-secret storage/layout values from the actual source.
4. Call `draft_query_evidence_storage_overlay`, then stage its
   `stage_arguments` with `stage_graph_revision`.
   If it returns `query_evidence_storage_overlay_blocker`, follow the returned
   stale-seed handoff preflight and repeat the overlay in a fresh seeded capsule
   before staging.
5. Run `check_staged_revision_apply`, apply the ready row, rerun
   `describe_query_context`, and only then call `draft_query_plan`.

If that evidence identifies a reviewed source but the map still lacks physical
query-planning metadata, call `draft_query_evidence_storage_overlay` with the
dataset IRI, evidence IRI, and reviewed storage/path/layout values. The helper
does not parse query artifacts to guess storage. It can consume profile-shaped
successful query evidence or ordinary blocked/failed/partial query evidence
linked to the dataset. It returns validation-previewed `stage_graph_revision`
arguments that add storage access and physical layout metadata with evidence
support. Keep the verification status honest: a blocked query may support a
candidate route, but only real listing or query evidence should justify
`rc:VerifiedByListingLayout` or `rc:VerifiedByQueryLayout`. Stage, check, apply,
and rerun `describe_query_context` before drafting the next plan.
Mixed profile/query contexts can show profile-run inspection and ordinary query
evidence overlay actions together. Follow the profile action for semantic
profile context, but do not treat it as a substitute for the overlay action when
the ordinary query evidence names the reviewed storage route.
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
`draft_query_plan(..., candidate_selector=..., allow_context_blocked_candidate=True)`
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
`candidate_selector`; the storage selector must identify exactly one candidate.
This can happen even for database storage when the same storage access is linked
to dataset or partition template review cards; use the candidate snippet for the
storage-owned relation when you want the database relation handoff.

## Common Cases

Local file/object candidates can be ready for an execution attempt when the
path or template is verified enough, the scan function is inferred, and runtime
resolution is not required. Still supply binding values and perform ordinary
filesystem/object-existence checks before running anything.
If a storage access records an absolute local `storage_root`, complete absolute
path templates are review-only unless they stay under that root. This applies
to both dataset-owned templates and storage-access-owned templates.

S3-compatible candidates often need endpoint profile, credential reference, and
region or equivalent local runtime setup. DoxaBase records non-secret planning
facts; it does not store secrets or prove the object exists.
Complete S3 templates are checked against recorded S3 `storage_root` as well as
bucket/prefix fields; a template that escapes the reviewed root remains
orientation-only even when endpoint and credential references are present.
When `storage_protocol_location_mismatch` appears, read
`details.repair_hint` before hand-authoring a repair. It offers reviewed
`stage_map_assertion_change` templates for fixing protocol/root metadata, S3
bucket/prefix metadata when the recorded protocol is S3-compatible, and, when a
path template caused the mismatch, adding a reviewed replacement template or
removing the conflicting exact template. For non-S3 storage, existing
bucket/prefix facts appear as removal actions rather than new bucket/prefix
setters. Templated protocol/location actions name `placeholder_fields` and
`reviewed_value_fields` for the reviewed value to copy into the call.

Database candidates use the generic draft-plan shape, but a clean
storage-access-owned relation can have
`draft_query_plan().review_gate.executable_without_review=true` while
`ready_for_execution_attempt=false`. Use `relation_identifier` and
`connection_reference` as the handoff, then verify the database connection,
schema, table, credentials, and source access outside DoxaBase. Expect
`scan.function=None` and `runtime_resolution_required` for this relation
handoff; missing a DuckDB file-scan function is not the blocker for database
storage.
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

For database storage, `runtime_resolution_required=True` is the normal execution
gate until an external runtime resolves the connection, schema, table, and
source access. If older or unusual metadata yields
`runtime_resolution_required=False`, still read the note before treating it as
reachable; the boolean is not a database connectivity guarantee.

Current `handoff_kind` values are `no_query_target`,
`not_applicable_non_tabular_asset`, `metadata_review_required`,
`context_review_required`, `runtime_resolution_required`,
`database_relation_handoff`, `binding_values_required`, and
`execution_attempt_ready`.
