# MCP Tools

The MCP server is intentionally thin. It exposes the current Python API plus short operational docs.

## Documentation

`doxabase.list_docs`

Returns available agent docs with IDs, titles, descriptions, character sizes,
and section headings.

`doxabase.get_doc`

Returns one markdown doc by ID. Use `max_chars` to bound output, `start_char`
to continue a truncated document, or `section` to jump to a heading/anchor.
Start with `doc_id="start_here"` when arriving cold or resuming after
compaction.

## Capsule Inspection

`doxabase.graph_overview`

Returns named graph counts, top classes, top predicates, key entity counts, and known namespaces.

`doxabase.list_entities`

Lists entities by RDF type, graph role, optional text filter, limit, and offset. Start with `type="rc:Table"` and `graph="map"`.
For type-aware retrieval, use types such as `rc:Pattern`, `rc:Claim`,
`rc:Evidence`, or `rc:SourceSpan`; the text filter searches literal and
URI-valued facts attached to each resource, not only labels.

`doxabase.describe_resource`

Returns outgoing and incoming triples for one resource, with available labels
and RDF types. Use it after `list_entities` when lexical search found a resource
but you need its structured claim/evidence/source-span context.

`doxabase.describe_assertion_support`

Explains one subject/predicate/object map assertion, or all assertions matching
one subject/predicate when `object` is omitted. Returns whether the assertion is
present, exact matching triples, current same-subject/predicate triples,
subject/object resource summaries, an owner-dataset summary for column subjects,
nearby caveats, selected direct layout/path context triples, related
observations, claims, patterns, evidence, revisions, a support-scope note, an
absence note, scoped caveat-link metadata, grouped route summaries and raw route
explanations for related lore, and structured suggested next actions plus
display call strings. Use it for questions like "why is this caveat link here?"
or "what lore supports this column type?" It is retrieval context, not proof
that the assertion is correct.
When an exact requested object is absent, inspect
`same_subject_predicate_triples` and `absence_note` before deciding whether the
current map already contains a more careful value. For column subjects, follow
the owner-dataset suggested actions when you need table-level lore. For layout,
partition, or storage assertions, inspect `nearby_context_triples` before using
the assertion as executable planning context. Use `related_route_summaries` to
find the most directly related lore resources, and `related_routes` when you
need to know whether an observation, claim, pattern, evidence item, or revision
matched the subject, requested object, current same-slot object, or another
nearby lore item. Prefer `suggested_next_actions` over parsing
`suggested_next_calls`; each action has `tool_name`, `mcp_tool_name`,
`arguments`, `reason`, `call`, and an `action_label` that names its role. Use
`mcp_tool_name` for MCP dispatch. Check
`nearby_caveat_links.scope` before treating a table-level caveat as specific to
one column. When no current triples use the requested predicate on the subject,
`predicate_hints` lists nearby predicates already present on that subject with
sample values. Each hint keeps the full predicate IRI and may also include
`predicate_curie`, such as `rc:partitionedBy`, for faster display and follow-up
calls. Use these hints to recover from plausible predicate-name guesses before
assuming the map lacks the concept.

`doxabase.describe_graph_revision`

Returns compact revision context for one `rc:GraphRevision`: summary,
rationale, revision type, changed graph roles, included review/export graph
roles, validation result, export path, graph snapshots with counts and
`sha256:<hex>` content digests, `applies_staged_revision` for applied events,
`applied_source` compact source context for applied staged revision events, and
support links. Applied events include suggested actions for
`describe_graph_revision` and `describe_applied_revision_diff`.
`snapshot_evidence` classifies whether RDF history metadata and SQLite snapshot
rows are both present for exact diff/drift work.
`record_kind` mirrors list rows (`staged_patch`, `applied_event`,
`export_record`, `import_record`, or `history_record`) so callers can route a
detail response the same way they route `list_graph_revisions` rows.
`applied_source` omits patch content and full diagnostics; call
`describe_staged_revision` on `applies_staged_revision` when those are needed.

`doxabase.describe_revision_snapshot_evidence`

Classifies revision recovery evidence for one revision IRI without requiring
the full revision detail to exist. Status values are `history_missing`,
`history_only_count_digest`, `history_plus_snapshot_rows`, and
`snapshot_rows_without_history`. Use this after RDF/snapshot imports to detect
whether exact changed triples are available, only count/digest RDF snapshots
survived, or snapshot JSON was imported without the matching `history` graph.
The response includes structured `suggested_next_actions`: missing exact rows
point at `doxabase.import_revision_snapshots`, and orphan snapshot rows point at
`doxabase.import_trig` for the missing project/history RDF. The suggested import
paths are placeholders marked with `path_is_placeholder=True`; replace them with
the real handoff artifact path before executing the action. Revision list,
detail, and lineage responses promote these import actions to top-level
`suggested_next_actions`; list and lineage `next_action` use the
`complete_handoff_import` queue before exact diff or stale-drift inspection.

`doxabase.describe_revision_graph_snapshot`

Returns one revision snapshot for one graph role. It reports the revision-wide
`snapshot_evidence`, the role-local count/digest, whether exact stored snapshot
rows are available, and optionally bounded triples with
`include_triples=true`. Use this when `describe_applied_revision_diff` tells you
which staged source and applied event form the before/after pair, but you need
the full stored contents of one side rather than only added/removed triples. If
only RDF history count/digest metadata is present, the response uses
`count_basis="rdf_history_graph_snapshot"` and leaves triples empty until a
companion snapshot JSON bundle is imported.

`doxabase.list_graph_revisions`

Lists `rc:GraphRevision` resources from `history`, newest first. Use
`revision_type` such as `rc:StagedRevision` to narrow the list. Set
`include_apply_checks=True` when you need staged proposal status without already
knowing which proposals are ready, stale, or already applied. Apply checks are
only populated for revisions with graph patch payloads. Rows include
`record_kind`, `has_patch_payload`, `patch_count`, revision relation links,
selected apply-check blockers/drift summaries, and review-first suggested next
actions. Rows also include `snapshot_evidence` for the same history/snapshot-row
classification as revision detail, and `alternative_gate` so a ready row that is
an alternative to an already-applied source carries a local
`semantic_review_required` signal. Use `record_kind`, `application_status`,
`staged_validation_status`, and `stale_resolution_state` filters to ask
directly for applied events, ready staged proposals, rows with stored staged-time
validation failures, unresolved stale sources, or handled stale sources. Rows
also include `is_current_staged_work`; pass `current_staged_work_only=True` for
the live staged work queue, excluding applied sources and stale rows already
handled by restage. Responses include page-scoped `next_action_queue_items`,
`next_action_queue_item_counts`, and `semantic_review_required_queue_counts`.
Queue items preserve the old row-IRI queue while adding
`resolved_target_iri`, `resolved_target_record_kind`, `row_is_target`, status
fields, and alternative-gate fields for automation. Non-current rows include
`not_current_staged_work_reason`,
such as
`already_applied_source`, `superseded_by_restage`, or `applied_event_record`.
Do not route full-list `application_status="conflict"` rows directly: a handled
stale original can still be historically conflicted while
`is_current_staged_work=False` and `stale_resolution_state="stale_handled_by_restage"`.
Response-level `returned_application_status_counts` summarizes the returned
page, including those historical rows; use
`returned_current_staged_work_application_status_counts` for the returned-page
subset where `is_current_staged_work=True`.
Status, stale-state, and current-work filters automatically compute apply
checks. `staged_validation_status="failed"` filters stored staged-time
validation, while `application_status="validation_failed"` filters the current
live replay branch.
`drift_detail="summary"` is the default and omits exact changed-triple
arrays from snapshot drift rows, but still includes drift relevance, overlap
arrays, and added/removed exact-change counts. Set `drift_detail="exact"` or
call `check_staged_revision_apply` when you need the actual changed triples.

`doxabase.describe_revision_lineage`

Describes one graph revision's staged/applied lineage by revision IRI. Use it
when you already have a staged source, restaged successor, or applied event IRI
and need the compact relationship card without opening patch payloads. The
response includes the selected list row, selected role, visible paired
staged/applied row, applied and staged revision IRIs, current staged successor
when one is still live, latest applied/current revision, restage chain IRIs,
alternative revision IRIs, related revision IRIs, warnings for broken lineage,
and next-action routing from the latest row. Related IRIs also include applied
events reachable from alternative staged rows when those alternatives have
already been applied, plus every visible restage successor when imported history
has ambiguous parallel successors, including applied events already attached to
those successor branches. Top-level warnings report missing restage or
applied-source links, non-staged rows inside a restage chain, parallel restage
successors where the current route chose one branch, and snapshot handoff gaps.
When list rows expose only RDF history/count/digest metadata, warnings remind
callers to import companion revision snapshot JSON before expecting exact
applied diffs or stale drift triples. It is a read-only routing helper, not a
diff browser; call `describe_staged_revision` for patch content and
`describe_applied_revision_diff` for stored before/after diffs.

`doxabase.list_resource_revisions`

Lists revisions that explicitly touch one resource. Matches come from
`rc:revisionAnchor`, exact subject/predicate/object URI mentions in staged patch
payloads, or an applied event whose staged source matched the resource. The
response top-level collection is `revisions` with total `count`; each row wraps
the normal revision list row under `revision` and adds
`match_types`, `patch_mentions`, `applied_source_revision_iri`, and
`applied_source_patch_mentions`. `patch_mention_scan` and per-row incomplete
flags report missing or unparseable patch payloads; when
`omitted_match_risk=true`, unanchored patch-only matches may be absent from the
filtered list. Pass `current_staged_work_only=True` for the resource-scoped live
mutation-review queue; keep `include_patch_mentions=True` when patch-only
current work should remain discoverable. Top-level unreadable revision counts
are distinct pre-pagination source/staged revision counts, not returned-row
counts. Patch mentions are
compact flags, not full patch content: patch IRI, target graph, operation,
role, sequence, `matched_term_roles`, `matched_triples`, and total
`triple_count`. Use
`describe_staged_revision` when you need the patch payload itself.

`doxabase.describe_resource_revision_lineage`

Describes one `resource_iri` / `revision_iri` match from
`list_resource_revisions` and adds immediate staged/applied context. Use it when
a resource revision row needs a compact lineage card: selected row, paired
staged/applied row when visible, graph-level `restage_chain_iris`,
`alternative_revision_iris`, merged `related_revision_iris`, graph-lineage
warnings, selected next action, and the same patch scan status used by
`list_resource_revisions`. When
an applied event is linked, the response can include a resource-filtered applied
diff summary with exact added/removed triples for that resource. If the selected
row is an old stale source whose restaged successor has already been applied,
`applied_revision_iri` and the diff summary follow that applied successor while
`restage_chain_iris` preserves the original source route. This is not full
graph-version browsing; call `describe_staged_revision` when patch content is
needed. RDF-only imports can preserve resource route and staged/applied pairing,
but exact resource-level applied diffs need the companion revision snapshot JSON
import.

`doxabase.search`

Lexically searches literal RDF claims and URI-valued graph terms, returning
matched resources with graph, IRI, label, types, predicate, matched text, and
snippet. Use it to rediscover caveats, observations, evidence, labels, path
templates, source notes, column names, and exact project vocabulary tokens such
as custom profile metric kinds.

`doxabase.describe_dataset`

Returns bounded context for one dataset/table IRI: row semantics, entity and
snapshot keys, columns, physical/value types, path templates, dataset/layout
verification status and notes, layouts, storage access descriptions, partitions,
direct caveats with impact/severity, upstream caveats inherited through
relationships, provenance transformations,
relationships, directly related datasets, grouped related dataset reasons, and
linked patterns. Column summaries include column names and
owning dataset context when available; related dataset entries include
relationship labels/kinds, grouped reasons can fold same-column relationship
tags, linked patterns include pattern text as their description, and
`linked_pattern_reasons` explains why each pattern matched when available.
The `profile_summary` field gives quick counts of the profile observations
returned in this bounded response, including dataset-level, mapped-column, and
unmapped-column profile counts. It also rolls up profile evidence IRIs and
lists `shared_evidence_iris` that appear on every returned profile observation.
Read total and omitted profile counts before assuming returned profiles are the
whole profile history for the dataset.
When mixed profile history means no evidence is shared by all returned profiles,
`profile_run_candidates` lists evidence IRIs that support more than one returned
profile, sorted by returned profile count. Each candidate includes
`profile_observation_iris`, the returned profile observations linked to that
evidence IRI, so a handoff can seed `describe_context_slice` or inspect the run
without reconstructing membership from nested profile lists.
Its `handoff_note` is a compact reading cue for profile-only handoffs: profile
lore is observed evidence, while storage/path/layout warnings remain physical
query-planning metadata gaps.
Relationship entries and grouped reasons may include `source_caveats`, meaning
caveats attached to source datasets or source-side columns that should remain
visible when interpreting an aggregation, derivation, or foreign key. The
top-level `upstream_caveats` field is a deduped rollup of those inherited
caveats; it is separate from direct `caveats`.
Check `layout_verification_status` and `layout_verification_note` before using
`path_templates` for executable query planning. Child `physical_layouts`,
`storage_accesses`, and `partition_schemes` may carry their own verification
status/notes when the uncertainty belongs to one part of the physical metadata.
The `operational_warnings` field carries dataset-owned physical-metadata
`QueryPlanningIssue` objects that also appear in `describe_query_context.issues`;
scan it when a full dataset handoff should still surface query-planning hazards
such as unverified layouts. Candidate-derived issues such as path/template
composition warnings are only guaranteed in `describe_query_context.issues` and
`query_target_candidates[].review_reasons`. These warnings carry
`domain="query_planning"` so their severity is not confused with profile
recording or graph validation status.
Info-level issues such as
`verification_status_not_recorded` make missing verification status visible
without changing query-planning readiness. Query-context `analysis_warnings`
are separate caveat warnings for analytical interpretation after a query can be
planned and carry `domain="analysis"`.
Within each linked-pattern reason, `iri` and `pattern_iri` both name the linked
pattern. Scan `match_groups` first for relevance tiers, route labels, resource
kinds, and supporting resources; use raw `matches` when every route matters.
Treat group and tier counts as triage hints, not as confidence scores:
`relevance_tier_counts` counts grouped matches, while `raw_match_count` counts
unfolded route matches. Direct and map-implication groups are usually the
strongest local relevance signals, while claim/observation-supported groups
explain the surrounding lore. Call `doxabase.describe_pattern` before using a
pattern as a decision rule.

`doxabase.describe_profile_run`

Returns the profile observations for one dataset that link to one evidence IRI.
Use it after `describe_dataset().profile_summary.profile_run_candidates` points
at a shared profiler-run evidence resource, especially when the bounded
`describe_dataset` response has omitted profile observations. The result
includes the dataset and evidence summaries, top-level returned/total/omitted
count fields,
`profile_observation_iris`, and profile rows split into dataset-level,
mapped-column, and unmapped-column observations. The three list fields are
`dataset_profile_observations`, `mapped_column_profile_observations`, and
`unmapped_column_profile_observations`; use the top-level
`returned_dataset_profile_count`, `returned_mapped_column_profile_count`,
`returned_unmapped_column_profile_count`, `returned_profile_count`, and matching
`total_*` / `omitted_*` fields when checking whether a handoff contains the
whole profiler pass. `limit=None`
returns the full matching run; pass a positive `limit` only when a client
intentionally wants a capped payload. The run is inferred from profile
observations linked to the requested evidence IRI, not from a separate
persisted profile-run node.

### doxabase.draft_profile_map_updates

Returns read-only review recommendations by comparing one
`describe_profile_run(dataset_iri, evidence_iri)` result with current map facts.
Use it after a shared-evidence profile run surfaces row-count drift, mapped
column nullability evidence, unmapped profiled columns, or project-specific
profile metric IRIs that may need vocabulary review. The helper does not mutate
or stage graph changes. It returns `recommendations` with helper names and
arguments for accepted map-helper updates, plus `metric_advisories` for
project-specific metric kinds that should be defined before reuse. Sampled
zero-null profiles are intentionally not promoted into non-null map
recommendations. Metric advisory rows include `advisory_status`,
`definition_found`, optional `definition`, `promotion_patterns`,
`mixed_support_patterns`, `mixed_support_note`, `context_patterns`, and
structured `suggested_next_actions` so agents can inspect existing ontology
definitions or nearby metric vocabulary before recording
claims/patterns/promotions. When an undefined or ambiguously typed metric has a
same-evidence pattern naming it as a target or map implication, the advisory
also suggests `describe_pattern` and a reviewable
`stage_pattern_promotion` skeleton for an ontology `rc:ProfileMetricKind`.
That skeleton seeds its `rdfs:comment` from metric-specific supporting pattern
text, rationale, or summary when available; otherwise it uses a generic
review-first comment. It is still a draft vocabulary definition; sharpen units,
calculation, and comparison semantics before applying it unchanged.
Same-evidence prose patterns that mention the metric but do not name it
structurally appear as `context_patterns` with `describe_pattern` actions only;
do not treat them as automatic promotion support.
Do not infer metric vocabulary status from `describe_context_slice` alone:
metric-kind resources that are only profile-metric objects can appear as
`referenced_only`. Use `metric_advisories[].advisory_status` and
`definition_found` for the authoritative review cue.
Type findings are not accepted profile-map recommendation indexes.
`physical_type` and `value_type` are persisted on profile observations as
observed evidence; when they differ from or fill gaps in current map column
facts, the draft returns `type_advisories` with context, pattern, and focused
`stage_map_assertion_change` suggested actions for review. Unmapped-column type
advisories also name related `unmapped_profiled_column` recommendation indexes
so agents can stage the column shell before reviewing type assertions.
Type-context actions seed `describe_context_slice` with the profile observation,
column, and observed type resources that already exist in the graph. If an
observed project value type has not been defined yet, it is omitted from the
context-slice seed list so the suggested action remains runnable, but it still
appears in the `record_pattern` map implications and the focused
`stage_map_assertion_change` value-type assertion payload.
When an undefined or not-yet-typed project value type has a same-evidence
pattern naming it as a target or map implication, the type advisory also
suggests `describe_pattern` and a reviewable `stage_pattern_promotion` skeleton
for an ontology `rc:ValueType`. That skeleton defines only the vocabulary shell
with label/comment; review domain meaning, allowed values, and physical-type
expectations before applying it unchanged.
If the same promotion pattern supports both metric vocabulary and type review,
both advisory rows expose `mixed_support_patterns` and `mixed_support_note`;
grouped promotion/assertion actions also include
`source_profile_advisory.mixed_support` plus a review-note cue. Inspect the
shared pattern before promoting or asserting either lane independently; when
both lanes generate staged drafts, review or export those drafts together before
applying either lane on its own.
The draft
also includes `recommendation_count`, `representative_recommendation_indexes`,
`metric_advisory_count`, `representative_metric_advisory_indexes`,
`metric_advisory_status_counts`, `type_advisory_count`,
`representative_type_advisory_indexes`, `type_advisory_status_counts`, and
top-level `suggested_next_actions` / `suggested_next_calls` for compatibility.
Prefer `suggested_next_action_groups` / `suggested_next_call_groups` for quick
routing; non-empty lanes are grouped as `profile_map_updates`,
`metric_vocabulary_review`, and `profile_type_review`. Use representative
advisory indexes when you need one review row per duplicate metric or type
advisory group; each row also carries `metric_advisory_index` or
`type_advisory_index` for row-local routing. Group lanes may de-duplicate shared
actions, such as one `describe_pattern` call supporting several metric
advisories; grouped metric/type actions carry `source_profile_advisory` with
the source advisory kind, index field, represented advisory indexes, duplicate
group keys, duplicate advisory indexes, duplicate profile-observation IRIs, and
optional `mixed_support`.
Use that source block for direct lane routing, or use each advisory row's own
`suggested_next_actions` for per-metric or per-column follow-through.
Recommendation rows carry `recommendation_index`, `default_stageable`,
`default_skip_reason`, and duplicate-group fields; metric and type advisories
carry duplicate-group fields too.
If a top-level `stage_profile_map_updates` action is present, review the draft
and use that action as a starting point. Its accepted indexes default to the
representative indexes whose rows have `default_stageable=True`. Sampled
row-count recommendations remain review candidates in
`representative_recommendation_indexes`, but they are omitted from the default
staging action unless the caller explicitly opts in with
`allow_sampled_row_count_updates=true`. If
`recommendation_count == 0` and either metric or type advisories are present,
handle the result as advisory-only: follow advisory grouped suggested actions and
do not call `doxabase.stage_profile_map_updates`. When recommendations and
advisories coexist, follow `profile_map_updates` for map staging and keep metric
or type review lanes separate.

### doxabase.stage_profile_map_updates

Stages accepted `draft_profile_map_updates` recommendation indexes as one
grouped reviewable `map` revision. Pass `dataset_iri`, `evidence_iri`, and
`accepted_recommendation_indexes`. The result returns item statuses,
`staged_recommendation_indexes`, `skipped_recommendation_indexes`,
`not_selected_recommendation_indexes`, `status_counts`, metric advisories,
type advisories, their status counts, and the staged revision when at least one
accepted recommendation was staged. When a staged
revision is created, `suggested_next_actions` points to
`check_staged_revision_apply` for the read-only pre-apply check. The helper uses
helper-equivalent RDF for dataset and column shells, keeps metric advisories as
review prompts, keeps type advisories separate from staged map patches,
preserves every grouped profile observation when one duplicate representative is accepted, and skips
accepted sampled row-count
recommendations unless
`allow_sampled_row_count_updates=true`. Optional `supporting_claims`,
`supporting_patterns`, and `revision_anchors` are passed through to the staged
revision when at least one recommendation creates a patch; caller anchors are
merged with the automatic profile-derived anchors.
Default `stage_profile_map_updates` suggestions only auto-pass same-evidence
patterns that target or imply the dataset or recommended map resources. Keep
metric-only and type-only patterns in their advisory lanes unless you explicitly
want them to support the map patch. Column-targeted patterns that mention
observed physical/value type resources are treated as type-review patterns even
when they also name the profiled column. When authoring a metric vocabulary
pattern that should stay advisory-only, target or imply the metric IRI rather
than the dataset; dataset-targeted metric patterns are eligible map-patch
support.
When accepted recommendations stage unmapped column shells and current type
advisories are still `type_finding_unmapped_column`, the returned and stored
review note tells agents to apply the shell after review and rerun
`draft_profile_map_updates` for the same dataset/evidence. That rerun is what
turns related type advisories into map-present `rc:physicalType` /
`rc:valueType` assertion actions.

### doxabase.describe_query_context

Returns a compact read-only projection for query planning around one dataset:
dataset summary, physical-metadata readiness, `readiness_note`, an `issues`
list for missing, risky, or informational physical metadata, `analysis_warnings`
for caveats that matter after a query can be planned, planning notes, columns,
path templates, derived `query_target_decision` and `query_target_candidates`,
physical layouts, storage access descriptions, partition schemes,
dataset/layout verification status and note, caveats, and structured
`suggested_next_actions` for drafting the selected route. It returns
`profile_summary` beside `row_count_snapshot`, so a planner can follow profile
evidence IRIs and `profile_run_candidates` without a separate
`describe_dataset` call when row counts or metric context came from profiling.
When profile run candidates exist, `suggested_next_actions` includes
`describe_profile_run` first; a draft-plan action follows when a query target
candidate is available. In mixed profile history, match the dataset-profile
`row_count` in candidate runs to `row_count_snapshot` before relying on a
profile-derived count. Also read `row_count_snapshot_basis` and
`dataset_profile_row_count_bases`; a matching row count can still come from
sampled or unknown-scope profile evidence.
It also returns `ready_candidate_indexes`, `unselected_ready_candidate_indexes`,
`direct_clean_candidate_indexes`, and
`unselected_direct_clean_candidate_indexes` so callers can see peer strict-ready
routes and peer direct-clean routes before drafting. The ready indexes are
candidate-local direct readiness and may be non-empty while top-level
`readiness` is `needs_review` because sibling candidate metadata still blocks
the whole context. Use it before
drafting DuckDB/S3/local-file queries when you need to decide whether graph
metadata is executable or only useful for orientation, especially when you need
physical metadata and warnings without the full relationship/pattern handoff in
`describe_dataset`. Read `query_target_decision` first; its zero-based
`candidate_index` points into `query_target_candidates`. Candidate
`review_required` includes whole-context blockers; `direct_review_required`
ignores sibling blockers and shows which target candidates have their own
storage/path/layout problem. `selected_candidate_direct_clean` gives the same
cue on the selected decision row. When that selected candidate is direct-clean
but context-blocked, the suggested `draft_query_plan` action carries
`allow_context_blocked_candidate=true` and the explicit candidate index. For
multiple direct-ready candidates, inspect `unselected_ready_candidate_indexes`
and rerun/draft with an explicit `candidate_index` if candidate order picked the
wrong route; peer suggested actions include the same allowance when sibling
candidate metadata is the only broader blocker. In a globally blocked context,
inspect
`unselected_direct_clean_candidate_indexes` when strict ready indexes are empty
but another candidate has no direct blocker. When linked physical layouts are
ambiguous, suggested `draft_query_plan` actions include explicit
`candidate_index` / `physical_layout_iri` pairs for the selected candidate and
peer candidates whose only direct blocker is layout ambiguity. For
database-backed storage, only
storage-access-owned templates become `relation_identifier` values. Dataset or
partition path templates paired with database storage are review-only
`database_relation_template_source_mismatch` candidates with no relation
identifier; record the schema/table/relation on the storage access before using
a database handoff. Read `issues[].details.repair_hint` for the ordered repair:
stage an add of the reviewed relation identifier onto the storage access, then
stage removal of the misplaced source template only if review confirms it was
relation metadata rather than a real file/object path. Repair actions declare
`required_extra_arguments=["rationale"]`; add a reviewed rationale to the copied
arguments before calling `stage_map_assertion_change`. The stale dataset or
partition path is review context, not the relation identifier. Root-only
database storage without a storage-access relation template is also review-only
with `database_relation_template_missing`, even when `location_kind="object"`;
read `issues[].details.repair_hint` for the reviewed add-template action on the
storage access.
When `missing_storage_access` appears, read `issues[].details.repair_hint` for
reviewed repair templates: record a non-secret storage access and link it to the
dataset, or stage a reviewed `rc:hasStorageAccess` assertion to an existing
storage access. If `issues[].details.fixture_staleness_hint` is present, known
AIS or Polymarket fixture tables exist but the capsule has zero
`rc:StorageAccess` resources; treat that as a stale/reduced fixture capsule and
load fresh fixtures into scratch before judging query-target behavior.

### doxabase.draft_query_plan

Returns a non-executed, review-gated physical plan draft over
`describe_query_context`. It currently supports `engine="duckdb"` and selects
the candidate named by `query_target_decision.candidate_index` by default. Pass
`candidate_index` or `storage_access_iri` for an explicit route selection, pass
`physical_layout_iri` after reviewing linked physical layouts with distinct
signatures, and use `allow_context_blocked_candidate=true` only when the
selected candidate is
direct-clean but sibling metadata still blocks the whole context. When the
blocker comes only from sibling candidate metadata, pair the allowance with
an explicit `candidate_index` or `storage_access_iri`; selectorless automatic
drafts keep the context review gate and report
`context_blocked_candidate_allowed=true` /
`context_blocked_candidate_used=false`. If `storage_access_iri` matches
multiple candidate paths, prefer the explicit peer `draft_query_plan` actions
returned by `describe_query_context`; otherwise rerun with `candidate_index`
using the returned candidate snippets. `source_context`
also reports `candidate_count`, `ready_candidate_indexes`, and
`unselected_ready_candidate_indexes`, plus direct-clean peer indexes, so
automatic plans reveal peer ready or context-blocked-direct-clean candidates
that may deserve explicit selection. It also includes
`selected_candidate_note`, a compact prose summary of the selected candidate,
route kind, and any sibling/context blocker codes that remain visible in
`review_gate.all_issue_codes`. Read
`context_blocked_candidate_allowed` with `context_blocked_candidate_used`: if the
switch was requested but not used, direct blocking codes distinguish already
ready candidates from candidates that still need review. The payload
includes the selected candidate, scan hint such as `read_parquet`, URI/path
template for file/object storage, database relation fields for database-backed
storage, scan-adjacent `execution_attempt_ready` and
`primary_execution_attempt_blocking_reason_code` /
`execution_attempt_blocking_reason_codes` mirrors of the review gate, parsed
`required_bindings`, structured `binding_requirements`, non-secret storage
environment hints, copied issues and analysis warnings, caveats, and a
`review_gate`. Distinct linked physical layouts produce
`ambiguous_physical_layout`, leave `scan.function` unset, and keep
`review_gate.ready_for_execution_attempt=false` until the intended layout is
modeled or selected with `physical_layout_iri`; selected drafts record the
choice in `source_context.requested_physical_layout_iri`,
`scan.physical_layout`, and `scan.physical_layout_selection_note`. Binding rows
preserve the source text and say
when DoxaBase has not inferred derivation or runtime values. When the selected
template comes from partition metadata, binding rows also carry
`binding_kind="partition_template_placeholder"` plus optional
`partition_scheme`, `partition_column`, and `partition_granularity` handoff
hints; the granularity describes the partition scheme rather than necessarily
the individual placeholder. Placeholders that do not match a declared partition
column, and ordinary dataset/storage placeholders, may include
`candidate_column_matches` when placeholder names match dataset columns; use them
as best-effort handoff hints, not runtime binding values.
`candidate_column_match_status` marks the hint set as `none`, `single`, or
`ambiguous`; review ambiguous rows before choosing any source column, even when
individual matches have `confidence="high"`. Confidence is per match, while the
status summarizes the whole hint set. Top-level
`handoff_kind` gives a compact machine-readable route, such as
`metadata_review_required`, `context_review_required`,
`runtime_resolution_required`, `database_relation_handoff`,
`binding_values_required`, or `execution_attempt_ready`. `review_gate`
includes `blocking_reason_codes`, `all_issue_codes`, the legacy `reason_codes`
alias for blocking reasons, `binding_values_required`,
`ready_for_execution_attempt`, `primary_execution_attempt_blocking_reason_code`,
and `execution_attempt_blocking_reason_codes`. The primary execution blocker is
the first item from the ordered blocker list, or `None` when no
execution-attempt blocker remains. It may add
handoff-only blockers such as `query_context_has_other_blockers` for clean
selected candidates with bad siblings, or `scan_function_not_inferred` when
DuckDB has no file-scan function for the selected storage/layout shape.
`source_context` reports selection mode/request/status/note, and `review_gate`
reports selection override, context-block allowance/use, direct blocking codes,
and context blocking codes.
`executable_without_review=true` means the selected graph metadata has no
review blocker; `ready_for_execution_attempt=true` also requires no recorded
runtime resolution and no required binding placeholders to remain.
Use `ready_for_execution_attempt`, not `handoff_kind` alone, as the gate for
any execution attempt; `database_relation_handoff` means the selected route is a
relation/connection handoff, not that execution is safe.
If `ready_for_execution_attempt=false`, route relation fields before generic
runtime resolution, then route
`primary_execution_attempt_blocking_reason_code` as the compact next blocker,
using `execution_attempt_blocking_reason_codes` for the full ordered detail.
Then inspect `runtime_resolution_required`, `binding_values_required`, and
remaining issue codes. Empty
`blocking_reason_codes` and `executable_without_review=true` do not make a plan
execution-ready. The scan card repeats the same gate as
`scan.execution_attempt_ready`; when it is false, treat URI templates and
relation identifiers as handoff context rather than execution permission.
Database-backed storage still uses this generic
review-draft shape today, so expect `scan.function=None` and review gating
rather than executable SQL; read `scan.relation_identifier` and
`scan.connection_reference` instead of `scan.uri_template` for the recorded
database handoff. If the selected database candidate came from a dataset or
partition path, `scan.relation_identifier` stays absent and the plan remains
`metadata_review_required`. These scan fields mirror the selected candidate's
database-specific fields. The `scan` card includes dataset-level
verification notes plus template lineage and source verification fields, so
surprising shared or inherited path templates stay attached to their source
resource and warning notes. It does not resolve endpoint profiles, credentials,
object existence, or execute SQL.

`doxabase.describe_context_slice`

Returns a bounded, route-explained subgraph around one or more seed IRIs. Use
`profile="dataset_brief"` for table handoff context, `profile="pattern_brief"`
for pattern support context, and `profile="deep_lore"` when explicit revision
metadata should come along too. Dataset/deep-lore slices include bounded profile
observations, observed value-frequency nodes, scalar profile metric nodes, and
profile metric kinds returned through the dataset context. They can also start
from a profile observation, observed profile metric node, or metric-kind IRI
used by profile metrics. Deep-lore slices can also start from an
`rc:GraphRevision` seed and expand support, evidence, anchors, application,
restage, and alternative links. `seed_profile_observations` preserves structured
profile summaries selected by those profile/metric seeds even when the same row
is older than the bounded dataset profile list. Read `resources[].primary_route`,
`resources[].routes`, and `route_counts` before raw triples; those fields
explain why each resource entered the slice. `resources[].primary_route` is the
first full route object, so use `resources[].primary_route.route` when only the
route id is needed.
Read `resources[].surface_role` as the compact trust cue for whether a resource
is current map context, observation context, pattern synthesis, evidence support,
revision history, vocabulary context, mixed context, or a referenced-only object.
For project profile metric kinds, `referenced_only` means the slice reached the
IRI as an object/reference; it does not answer whether the metric vocabulary is
defined. Pair metric-oriented slices with `draft_profile_map_updates` when that
status matters.
`reading_order` and `route_legend` provide the static reading protocol and
meanings for the routes present in the response. Set `include_trig=true` when
you need importable TriG text, and raise
`max_triples` when `truncated` is true and the slice still looks relevant.
Truncation only affects raw `triples` and `trig`; resources and structured
contexts still describe the full selected slice.

`doxabase.describe_pattern`

Returns compact handoff context for one `rc:Pattern`: pattern text, rationale,
targets, supporting observations, supporting claims, evidence/source spans, and
map implications.

`doxabase.record_observation`

Records a structured observation in the `observations` graph. Optional evidence
fields create a linked `rc:Evidence` resource in the `evidence` graph. Use this
for point-in-time findings, profile counts, query outputs, and workflow notes
that should remain available to later agents. For validation-clean evidence,
include `evidence_sources`; `evidence_summary` alone is descriptive prose, not a
source identity. When `observed_column` names a column that is not yet in the
map, `observed_column_name` can preserve the source-level column name without
promoting the column into current map state. For `observation_type="profile"`,
`observed_physical_type` and `observed_value_type` preserve type findings as
evidence without asserting them as current map facts.

`doxabase.record_dataset_profile`

Records one dataset profile: a profile observation, optional evidence,
an optional current-best map row-count snapshot, and an optional
agent-authored profile pattern linked back to the observation. Use it when a
profile run should preserve both the raw noticing and the emerging synthesis.
`describe_dataset` surfaces recent dataset profile observations and their
sample, row, null, distinct, observed value-frequency, and scalar metric values.
Use `sample_scope` for the population or slice covered by the profile, and
`sample_method` for how the profile was produced.
`value_frequencies` outputs always use `frequency`; inputs may use `count` as a
profiler-output convenience alias.
Use `profile_metrics=[{"metric": "rc:MinimumValue", "value": ...}]` for
observed min/max/mean/median-style profiler output. These scalar metrics are
observed profile evidence, not constraints, shapes, allowed values, or durable
map semantics by themselves. Use `list_entities(type="rc:ProfileMetricKind",
graph="base_ontology")` to list built-in metric kinds before recording. Use
full project-specific metric kind IRIs for profiler outputs that do not fit the
base `rc:` metric kinds; define those terms in the project ontology once they
become durable vocabulary. `graph="ontology"` is an effective-ontology listing,
so it includes built-in `base_ontology` results; filter returned entities by
`graph == "ontology"` when you need project-local metric kinds only. DoxaBase
rejects unknown `rc:` metric kinds so typos
such as `rc:MinValue` do not become ad hoc RDF. A metric item may include
`target` when the scalar is specifically about a resource narrower than the
profile observation as a whole. Profile evidence entries include source strings
and source spans when recorded.
`update_map_snapshot` defaults to true, but row counts are written to
`rc:rowCountSnapshot` only when the profile basis looks like a full scan.
Sampled or unknown-scope row counts remain observation evidence by default; pass
`allow_sampled_row_count_snapshot=true` only when that profiled population is
the intended durable map population. Set `update_map_snapshot=false` for scratch
or tentative profile runs that should remain observation-only. If that is a
brand-new dataset, `describe_dataset()` may not find it until map context is
recorded; use `describe_profile_run(dataset_iri, evidence_iri)` or
profile-observation context-slice seeds for handoff retrieval. When matching
profile observations exist, the `describe_dataset()` not-found error includes
this recovery hint and points at `record_map_dataset` for creating map context.
If the helper creates a pattern, the profile evidence is linked to that pattern
as well as the
observation. When `pattern_map_implications` is omitted, the helper-created
pattern points at the dataset plus any project-specific profile metric kind IRIs
named in `profile_metrics`; built-in `rc:` metric kinds stay evidence-only.
Pass `pattern_map_implications` explicitly when a synthesis should point
somewhere narrower or different.
For a capsule that only records profile lore, `describe_dataset` may still emit
missing storage/path/layout warnings. Those are query-planning gaps rather than
profile validation failures. Read `profile_summary.handoff_note` when deciding
whether a profile-only handoff is missing physical query-planning metadata or
missing profile evidence.

`doxabase.record_profile_bundle`

Records one dataset profile plus zero or more related column profiles from the
same profiling pass. It writes ordinary profile observations, optional map
updates, optional linked profile patterns, and evidence using the same semantics
as `record_dataset_profile` and `record_column_profile`.
Use it when a profiler has produced a dataset-level summary and a set of column
summaries that share run metadata, evidence fields, or sample context.
The top-level `observed_at`, `observed_by`, `evidence_summary`,
`evidence_sources`, `sample_size`, `sample_scope`, and `sample_method` values
default into each column profile unless the column entry overrides them.
Pass `shared_evidence_iri` when the dataset profile and column profiles should
all point at one shared profiler-run `rc:Evidence` resource. A column entry can
still override that with its own `evidence_iri`.
The returned bundle includes `shared_evidence_iri` at top level for quick
run-level checks and `handoff_entrypoints` with profile observation seeds,
availability flags, structured `suggested_next_actions`, and compatibility
`suggested_next_calls` for the next agent. When both map dataset context and a
shared evidence run are available, handoff actions include
`draft_profile_map_updates` before context-slice routes. Map-present bundles may
include two `describe_context_slice` actions: one dataset-seeded map-context
slice and one profile-observation-seeded run handoff. Read `action_label` and
`arguments` rather than treating repeated `tool_name` values as duplicates.
In `handoff_entrypoints`, prefer `updated_map_column_iris` for columns whose map
facts were written by this bundle call, and `mapped_profiled_column_iris` for
all bundled column profiles that are mapped after the call. `map_column_iris`
remains as a legacy alias for `updated_map_column_iris`.
Use `column_defaults` for repeated column options such as
`{"update_map_column": false}`. Each `column_profiles[]` item accepts the same
fields as `record_column_profile` and must include `column_iri`, `column_name`,
and `summary`. After recording a bundle, `describe_dataset().profile_summary`
lists shared evidence IRIs, profile run candidates, grouped profile observation
IRIs, and a handoff note that can help a later agent recognise one profiler run
without walking every observation.
Use `describe_profile_run(dataset_iri, shared_evidence_iri)` when the full run
may be wider than the bounded dataset profile lists or when an observation-only
brand-new dataset is not yet available through `describe_dataset()`. If the bundle's
`pattern_summary`/`pattern_text` arguments are supplied, the helper-created
pattern is supported by the dataset profile observation only by default. Set
`pattern_support_scope="all_profiles"` when the helper-created pattern should
be supported by the dataset profile and every bundled column profile. For a
synthesis that also needs claims or hand-picked support, call `record_pattern`
after the bundle using `describe_profile_run(...).profile_observation_iris`
plus the extra support, and pass the shared `evidence_iri` to reuse the
profile-run evidence. When `pattern_map_implications` is omitted, bundle-created
patterns default to the dataset plus project-specific top-level profile metric
kind IRIs; with `pattern_support_scope="all_profiles"`, project-specific column
metric kind IRIs are included too. Built-in `rc:` metric kinds remain observed
profile evidence only.

`doxabase.record_column_profile`

Records one column profile: a profile observation with
`observed_column`, optional evidence, optional current-best map column metadata,
and an optional linked profile pattern. Use it when profiling output says
something useful about nullability, distinctness, physical type, or identity
behavior for a column. Column profile observations appear on the matching
`describe_dataset().columns[]` entry, including any observed value-frequency
pairs and scalar metrics supplied by the profiler.
Use `sample_scope` and `sample_method` to make sample caveats retrievable
without parsing the evidence prose.
Scalar `profile_metrics` are observed evidence, not constraints, shapes, allowed
values, or durable map semantics by themselves. When a column helper creates a
pattern and `pattern_map_implications` is omitted, project-specific metric kind
IRIs from `profile_metrics` become map implications alongside the column so
draft vocabulary-promotion routes can find the supporting pattern. Built-in
`rc:` metric kinds stay evidence-only.
`update_map_column` defaults to true; set it to false when counts or observed
values are only sample evidence. For value-frequency guardrails, record the
profile, then add a `record_claim_observation` and synthesize both with
`record_pattern`.
If `update_map_column=false` and the observed column is not yet in the map,
`describe_dataset` surfaces the profile under
`unmapped_column_profile_observations`. The profile keeps the supplied column
name as `observed_column_name`; `observed_column.column_name` also uses that
name as a fallback until the column becomes a current map column.

`doxabase.record_claim_observation`

Records the common richer pattern: one `rc:Observation`, one linked `rc:Claim`,
one `rc:Evidence`, and optionally one `rc:SourceSpan`. Use this for caveat,
join, schema, transformation, access, profile, or interpretation claims that are
more structured than a note but do not require hand-authored TriG.

`doxabase.record_pattern`

Records one `rc:Pattern` in the `patterns` graph and optionally linked
`rc:Evidence` / `rc:SourceSpan` resources in the `evidence` graph. Use this when
several observations, claims, or sources belong together and suggest a more
durable pattern or map implication. Pass `evidence_iri` when the pattern should
reuse an existing evidence resource, such as shared profile-run evidence from
`record_profile_bundle`. `map_implications` is a list of resource references:
pass IRIs or CURIEs for map resources or assertion nodes the pattern may affect.
Put explanatory prose in `pattern_text`, `rationale`, observations, or claims.

`doxabase.record_claim_reconsideration`

Records that a newer claim weakens, contradicts, supersedes, or refines an
older claim. Use this when exploration changes an agent's mind but the earlier
hunch remains useful context. The helper writes an `rc:ClaimReconsideration`,
adds a direct relation such as `rc:weakens`, optionally writes evidence/source
span context, and marks the older claim as `rc:Weakened`, `rc:Contradicted`, or
`rc:Superseded` when that follows from the relation. `describe_pattern` and
`describe_context_slice` surface incoming and outgoing reconsiderations around
claims, and claim descriptions include a compact `lifecycle_summary`.

`doxabase.record_map_dataset`

Records or updates a dataset/table resource in the `map` graph. Omit
`is_table` for partial updates that should preserve existing dataset/table
typing. Resource-valued links and controls such as `columns`, `caveats`,
`storage_accesses`, `physical_layouts`, `companion_datasets`, `extra_types`,
`row_semantics`, `schema_stability`, and `layout_verification_status` expect
IRIs or CURIEs like `rc:EventRow`, not descriptive prose. `schema_stability`
accepts `rc:FixedSchema`, `rc:InferredSchema`, or `rc:VariableSchema`.
Layout verification status accepts `rc:UnverifiedLayout`,
`rc:GeneratedFromManifestLayout`, `rc:CandidateLayout`,
`rc:VerifiedByListingLayout`, `rc:VerifiedByQueryLayout`, or
`rc:ContradictedLayout`.

`doxabase.record_map_column`

Records or updates a column resource and can link it to a table with
`rc:hasColumn`. Resource-valued fields such as `physical_type`, `value_type`,
and `table_iri` expect IRIs or CURIEs, not prose.

`doxabase.record_map_caveat`

Records or updates a `rc:KnownCaveat` and can link it to affected datasets.
Use prose for the caveat description, and use IRIs or CURIEs for `severity` and
`targets`.

`doxabase.record_map_storage_access`

Records or updates non-secret storage access metadata and can link it to
datasets. Use IRIs or CURIEs for resource-valued controls such as
`storage_protocol`, `access_mode`, `layout_verification_status`, and
`datasets`. For S3-compatible storage, include enough non-secret runtime
orientation such as `endpoint_profile`, `credential_reference`, or `region`.
For non-S3 protocols, prefer protocol-appropriate roots, URLs, or connection
references rather than S3-shaped `bucket_name`/`key_prefix` alone. Complete
path templates are checked against the protocol and bucket/prefix metadata, and
relative templates that already include the recorded key prefix are treated as
review-only because path composition would duplicate that prefix. A relative
dataset path template does not make an otherwise rootless storage access ready
for query planning; record the storage access location as well.
`location_kind` is a root-shape value, not a protocol value: use exactly one of
`"object"`, `"directory"`, `"prefix"`, or `"connection"`. Do not use
`"local_path"`; localness belongs in
`storage_protocol="rc:LocalFilesystemStorage"`. When the storage root itself is
the only candidate dataset location, set `location_kind="object"` only if that
root names the dataset object/location exactly. Use `location_kind="directory"`,
`"prefix"`, or `"connection"` for broader roots and add a path template before
executable use.

`doxabase.record_map_physical_layout`

Records or updates file-format/compression layout metadata and can link it to
datasets. Use `layout_verification_status` and `layout_verification_note` when
the physical format or layout has only been generated, proposed, listed, or
query-verified. Use IRIs or CURIEs for resource-valued controls such as
`file_format`, `compression_codec`, and `datasets`.

`doxabase.record_map_partition_scheme`

Records or updates partition metadata, including partition columns,
granularity, path template, redundant partition key, and layout verification
status/notes. Use it when uncertainty belongs to a partition/path template
rather than to the whole dataset. Use IRIs or CURIEs for partition columns,
granularity, redundant partition keys, layout verification status, and linked
datasets. `redundant_partition_key` is usually the partition column IRI/CURIE,
not the literal placeholder token from `path_template`. Dataset descriptions
expose all partition columns as `partition_columns`; the older singular
`partition_column` field is retained as a first-column compatibility shortcut.
Treat `partition_columns` as unordered
unless a future response explicitly carries ordering metadata.

`doxabase.record_map_relationship`

Records or updates a relationship resource. Supported relationship types are
`foreign_key`, `shared_identifier`, `derivation`, and `aggregation`. Aggregation
relationships accept `group_by_columns` and `aggregated_columns`; each aggregate
mapping should include `target_column`, `source_columns`, optional
`aggregation_function`, and optional `within_group_ordering`. Relationship
endpoints, columns, functions, and properties are resource-valued fields, so use
IRIs or CURIEs rather than prose. Dataset relationship descriptions expose
`relationship_kind` as the RDF class IRI and `relationship_type` as the helper
token such as `foreign_key` or `aggregation`.

`doxabase.record_graph_revision`

Records revision metadata in the `history` graph: changed graph roles, summary,
rationale, optional included review/export graph roles, optional supporting
observations/claims/patterns/evidence, optional `revision_anchors`, validation
result, export path, and graph-count snapshots. It does not compute diffs or
apply graph edits.

`doxabase.stage_graph_revision`

Records a staged graph revision in `history` without applying it. Pass
`additions` and/or `removals` as Turtle payloads with target graph roles. Use
`stance` values such as `rc:ExploratoryHunch`, `rc:CandidateRevision`,
`rc:ConservativeCleanup`, or `rc:AlternativeSystematisation` to preserve the
kind of systematisation move being made. The helper parses patch RDF, previews
graph counts, runs SHACL validation over `validation_scope`, and returns patch
metadata plus structured validation diagnostics when validation reports
results. The returned staged revision record includes the `summary`,
`rationale`, `review_note`, and `review_recommendation` that were recorded, so
scratch logs do not need an immediate describe call for the proposal headline.
`revision_anchors` can name graph resources the staged proposal is about without
treating them as evidence or support.
Use `restages_revision` when the new payload is a caller-authored repaired or
rebased successor for a stale staged revision. The tool records
`rc:restagesRevision` / `restaged_from` while keeping the provided additions and
removals intact. If the stale source already has `restaged_by` /
`current_restaged_by`, inspect or target that current successor instead; the
tool rejects parallel successors.

`doxabase.stage_map_assertion_change`

Stages a reviewable add/remove/replace for one `map` assertion. Use this before
generic `stage_graph_revision` when the change is a single subject/predicate
assertion such as a physical type, caveat link, nullability, path, layout, or
relationship claim. The helper calls `describe_assertion_support`, generates
small Turtle addition/removal patches, records related observations, claims,
patterns, evidence, caveat scopes, and assertion anchors on the staged revision,
and returns the assertion-support snapshot, staged revision record, and a compact
`judgement_panel`. The JSON also carries top-level `revision_iri` as an alias
of `staged_revision.revision_iri` for parity with generic staged-revision tools.
Check the panel first for current/proposed values, caveat
scopes, semantic risk level/reasons, value-type context, reasons the current
value may be intentional, strongest route summaries, impact spotlight entries,
and safety notes. For physical type changes, `value_type_context` surfaces
current `rc:valueType` resources and declared `rc:requiredPhysicalType` values.
`target_value` names the requested object for add, replace, and remove changes;
`removed_value` is populated for remove changes so reviewers do not have to
interpret legacy `proposed_value` as the removed value. For typed or
language-tagged literals, pass `object_datatype` such as `"xsd:boolean"` or
`"xsd:decimal"`, or `object_lang` such as `"en"`; the helper uses those fields
for exact matching and for the Turtle it authors. For exact removals,
`removed_value` reflects the matched graph triple, including datatype or
language-tag context. Remove-all changes still put the removed assertions in
`current_values` and the removal patch.
Routes marked `generic_value_only` matched only shared values such as
`rc:Varchar`; treat them as weak context. Drill into `assertion_support` and
`describe_staged_revision` when the change needs more thought.
For `replace`, the generated patch set adds the requested assertion and removes
current same-subject/predicate values except the requested object. The recorded
patch sequence shows the exact preview/apply order. If the requested value is
already present on a multi-valued predicate, treat the replace as mainly a
removal of the other current values and review their support routes before
applying. It does not apply the change; use `describe_staged_revision` and
`check_staged_revision_apply` before application.
Use `restages_revision` here when the repaired successor is itself a single
assertion add, remove, or replace, especially after a stale single-assertion
candidate needs a different value or an explicit replacement patch.
A competing singleton `add`, such as a second `rc:physicalType`, may correctly
fail validation while a `replace` candidate remains reviewable. Re-run apply
checks for sibling staged assertions after any successful apply.
`can_apply=True` means the patch replays and validates mechanically; it does not
mean the semantic change is wise.

`doxabase.stage_systematisation`

Stages one or more caller-authored RDF framings for the same modelling hunch.
Use it when an agent is choosing between pattern-first, ontology-first, map-first,
or other RDF shapes and wants to keep alternatives reviewable. Each framing may
use simple `graph` + `content` Turtle shorthand, or full `additions` /
`removals` patch lists. Use `shared_additions` / `shared_removals` for
provisional vocabulary or assumptions that every framing should validate
against. Shared patches can include provisional `shapes`; staged shapes are
active during the preview validation for each framing. The helper records the
systematisation intent, anchors, rationale, optional review notes and
recommendations, validation preview, and linked staged revisions; it does not
decide the ontology design for the agent. The result has
`result_kind="systematisation_draft"`, `warnings`, `structured_warnings`,
`next_action_queue`, `next_action_queue_items`, queue counts, suggested next
actions, and suggested next calls, so automation can route validation-failed
framings to repair and ready framings to review/apply checks before writing a
Markdown bundle. Queue items expose resolved targets and semantic-gate fields
without requiring a grouped export first. If later framings actually
default-linked to a first framing that did not route to `apply_after_review`,
`structured_warnings` includes `first_alternative_anchor_not_ready` with
`suggested_rerun_arguments={"link_alternatives": False}`. Per-framing
`alternative_to` values reroute siblings without that warning.

`doxabase.stage_pattern_promotion`

Stages one or more caller-authored RDF framings supported by existing
`rc:Pattern` resources. Use it when a pattern looks ready to become map,
ontology, shape, or other durable project structure, but the graph move should
remain reviewable. The helper does not infer the map shape. It uses the selected
patterns as `supporting_patterns`, rolls up their supporting observations,
claims, and evidence, and uses pattern targets plus `map_implication` resources
as revision anchors before delegating to the staged systematisation workflow.
It returns the same `systematisation_draft` result shape and routing fields.

`doxabase.describe_staged_revision`

Returns a staged revision with stance, rationale, support links, revision
anchors, review note/recommendation, patch payloads, before/after count
previews, validation status, structured SHACL diagnostics such as focus node,
result path, constraint, and messages, optional `judgement_panel`, and `impacts`
review context. `restaged_from` is present when this staged revision was created
by replaying an older stale staged proposal against current graph state;
`restaged_by` is present when this staged revision is the stale source for a
later refreshed proposal; `current_restaged_by` follows deeper restage chains to
the latest known successor; `restage_reason` gives the compact reason when it
can be derived from the recorded rationale. `applied_by` and
`application_status="already_applied"` are present after the staged revision is
applied.
`judgement_panel` is present for simple single-assertion `map`
changes that still replay cleanly; it is absent for complex or stale staged
revisions. When the panel is absent, `stored_review_context` may still summarize
persisted review/support metadata such as review-note signals, linked support
counts, semantic risk reasons, and attention impacts. It is not a replayed
panel. Impact
entries are deterministic consequence notes, not validation failures. They call
out changes such as removed caveats, changed physical/value types,
nullability, row/grain signals, grouping, layout/path assertions, and
documentation attached to the same subject as another semantic change, with
related observations, claims, patterns, evidence, and revisions when DoxaBase can
find them.
Pass `include_current_apply_check=true` when reviewing one staged revision and
you need a compact live apply branch beside the patch payload. The nested
`current_apply_check` includes status, decision, `routing_decision`, blockers,
current validation headline, drift summaries, compact `next_action`, and
suggested next actions.
It omits full `patch_checks`, `conflicts`, and `validation_results`; call
`check_staged_revision_apply` for those.

### doxabase.check_staged_revision_apply

Previews whether one staged revision can apply without mutating graph state.
Returns `can_apply`, already-applied state, per-patch current/preview/effective counts,
count-drift and snapshot-digest conflicts, preview validation diagnostics,
`status`, `decision`, `summary`, `review_recommended`, `blocking_reasons`,
`recommended_resolution`, `validation_skipped_reason`, `count_drifts`,
`snapshot_drifts`, `next_action`, and structured `suggested_next_actions`.
`next_action` is the compact route derived from the status/decision and the
same action list used by revision-list rows and grouped exports. The response
includes both `staged_revision_iri` and the alias `revision_iri` for
script-friendly payload handoffs, plus `restaged_by`, `current_restaged_by`, and
`stale_resolution_state` for the same handled-stale routing used by revision
lists and exports. Read `status`, `decision`, and `summary` first:
`ready` means the staged patch replays
and validates with an effective graph delta, with decision `review_then_apply`;
`noop` means replay validates but would not change graph triples and uses
decision `inspect_no_effective_change`; `conflict` with
`target_count_drift` or `target_digest_drift` means graph counts or content
digests drifted since staging and can usually be restaged; `conflict` with
`patch_conflict` means the stored patch is unreplayable and uses decision
`inspect_patch_conflict`; `validation_failed` means patch counts replay but
SHACL diagnostics need inspection; `already_applied` means an applied revision
event exists; `superseded_by_restage` means this source already has a refreshed
successor and uses decision `inspect_current_successor`. When validation did not run,
`validation_skipped_reason` explains why. `count_drifts` records
expected/current graph counts and deltas for count conflicts, plus whether the
staged patch triples themselves are currently present, absent, or mixed in the
target graph. `patch_sequence_index` and `expected_before_basis` explain
sequence-based counts in multi-patch revisions. `patch_checks` records
effective add/remove counts and already-present/absent payload triples for
partial or no-op replay.
When stale count/digest drift remains a `conflict` but every patch already has
zero effective add/remove delta, compact `next_action` routes to
`inspect_no_effective_change` in the `informational` queue and mutation
suggestions omit mechanical restage. Treat this as "already effective in current
graph state", not as `already_applied`; there is no applied revision event or
durable review lineage unless `already_applied` says so.
When a conflicted stale source already has `restaged_by` /
`current_restaged_by`, compact `next_action` routes to inspect the current
successor and suggested mutations omit another restage. If that current
successor has already been applied, `current_restaged_by` still names the staged
successor, but `next_action.arguments["iri"]` and the first suggested actions
point to the applied event with `describe_graph_revision` /
`describe_applied_revision_diff`. In list and export responses,
`next_action_queue` values remain returned row IRIs; use
`next_action_queue_items[].resolved_target_iri` or the row-local action
arguments for the actual call target.
`snapshot_drifts` records staged/current `sha256:<hex>` digest
mismatches, including same-count graph changes. For revisions staged with the
current runtime, it also includes exact triples added to and removed from the
target graph since the stored snapshot. It also includes `drift_relevance`,
`patch_overlap_subjects`, `patch_overlap_predicates`, `patch_overlap_objects`,
and `revision_anchor_overlap` so agents can separate "no staged patch subject
changed" from stronger overlaps. Predicate and object overlap can be broad, so
they are review hints rather than apply decisions.
One narrow exception to the usual restage route is a stale single-assertion add
or authored replacement for a curated singleton map slot where exact snapshot
rows show the current map added a different value for the same subject and
predicate. Current guarded slots are `rc:rowSemantics`, column
`rc:physicalType`, column `rc:nullable`, and data-asset `rc:schemaStability`. In
those cases `suggested_next_actions` includes `stage_map_assertion_change` with
`change_kind="replace"` and `restages_revision` set to the stale source, and
compact `next_action` routes to `repair_or_replace`; execute it only after
reviewing the semantics.
`broad_patch_object_overlap` is the weak object-overlap label for shared
class/type vocabulary such as `rc:Dataset` or `rc:Table`. Anchor overlap means exact drift
touched a resource the staged revision named as review context. Older revisions may report
`exact_changed_triples_available=False` when they predate snapshot row storage.
Suggested actions are ordered review-first, so inspect/export suggestions
come before mutation calls such as apply or restage. Use it before
`doxabase.apply_staged_revision` when an agent or human wants an explicit
read-only check.

`doxabase.describe_applied_revision_diff`

Returns stored before/after snapshot diffs for an applied staged revision. Pass
the applied revision event IRI, not the staged source IRI. The response links
`applied_revision_iri` to `staged_revision_iri`, lists changed graphs, and
returns one `graph_diffs[]` row per graph with before/after counts, digests, and
exact added/removed counts when snapshot rows are available. Changed-triple
arrays are omitted by default; pass `include_triples=true` to include them, with
`max_triples` capping each added/removed array. Use this after
`describe_graph_revision()` when an agent needs the actual triples changed by an
applied staged revision. The response includes `snapshot_evidence` for the
applied event and `source_snapshot_evidence` for the staged source, so agents
can follow import-snapshot recovery actions without parsing graph-diff notes; use
`describe_staged_revision()` for patch payloads, validation diagnostics,
impacts, and judgement context.

`doxabase.restage_staged_revision`

Creates a fresh staged revision from a conflicted staged revision's patch
payloads, rerunning preview counts and validation against the current graph
state. Use it for `target_count_drift` or `target_digest_drift` from
`check_staged_revision_apply`, especially when an unrelated graph edit made an
otherwise still-useful proposal stale and the patch still has an effective
current delta. Already-effective stale sources are rejected instead of becoming
no-op successors. The new staged revision records
`rc:restagesRevision` / `restaged_from` back to the stale proposal and preserves
support links, anchors, stance, review notes, and patch payloads. Its generated
rationale summarizes the stale apply-check drift evidence, including exact
snapshot drift triples when available. It does not merge semantic conflicts,
repair SHACL failures, or apply the result; review the new staged revision and
run `check_staged_revision_apply` again. If the stale source already has a
`restaged_by` / `current_restaged_by` successor, this helper refuses to create a
parallel successor; inspect or restage the current successor instead. The
immediate return includes `restaged_from`, `restage_reason`, `alternative_to`,
and `current_restaged_by` so the handoff can record provenance without an
immediate describe call.
If the old payload needs a human/model-authored repair, use
`doxabase.stage_graph_revision(..., restages_revision=...)` or
`doxabase.stage_map_assertion_change(..., restages_revision=...)`; this helper
is the same-patch replay path. Caller-authored repaired successors inherit the
source row's stored `alternative_to` link unless an explicit replacement is
supplied.

### doxabase.restage_staged_revisions

Batch recovery helper for stale staged revisions. It accepts staged revision
IRIs, checks each current apply state, restages count/digest-drift rows that do
not already have a `restaged_by` successor, skips already-handled stale sources
and non-restageable rows, and returns per-source actions, old-to-current mappings,
`review_revision_iris`, `revision_summaries`, and `bundle_summary`. Pass `path`
to write the grouped Markdown bundle over stale sources and current refreshed
successors. Pass `dry_run=true` to classify the same batch without creating
successors; restageable drift conflicts return `action="would_restage"` and are
listed in `would_restage_revision_iris`. `patch_conflict` rows are
`skipped_not_restageable` with `not_restageable_reason="patch_conflict"` and
should be repaired or replaced with a new staged candidate. Ready,
already-applied, and validation-failed rows use the same action with their own
compact reasons; `not_restageable_revision_iris_by_reason` groups those skipped
IRIs for triage. In dry-run rows that would be restaged,
`current_revision_by_source` still points to the stale source because no
successor exists yet. For `skipped_not_restageable`, inspect `status_before` and
`decision_before` to distinguish ready, validation-failed, and already-applied
rows; use `routing_decision_before` / `routing_decision_after` for the effective
next route when a stale-conflict decision is broad. Each item also carries
`status_after`, `decision_after`, `routing_decision_after`,
`stale_resolution_state_after`, `blocking_reasons_after`, and effective triple
deltas for `current_revision_iri` after the batch decision. Treat
`source_staged_validation_status` / `source_validation_result_count` and
`current_staged_validation_status` / `current_validation_result_count` as the
stored staged-time validation signals for the source and current rows; they are
separate from the live apply status fields. Each item also carries
`source_snapshot_evidence` / `source_snapshot_evidence_completeness` and
`current_snapshot_evidence` / `current_snapshot_evidence_completeness`, using
the same completeness labels as grouped Markdown, so scripts can tell whether
exact drift evidence is complete, partial, partial-extra-rows, history-only,
snapshot-only, or missing before mutating.
Guarded same-slot conflicts that already carry a
`stage_map_assertion_change` replacement suggestion are also
`skipped_not_restageable`, with
`not_restageable_reason="same_slot_replacement"`; follow
`next_action_after` / `suggested_next_actions_after` instead of forcing a
mechanical restage. A direct `restage_staged_revision()` call rejects the same
route; stage the replacement with `restages_revision` so the repaired proposal
supersedes the stale source while preserving any source alternative link.
Stale conflicts whose patch payload already has no effective delta are likewise
`skipped_not_restageable`, with
`not_restageable_reason="already_effective"`; inspect/export the stale source
instead of creating a no-op successor.
In real batch runs, top-level `current_revision_by_source` is recomputed after
the whole batch, so a requested stale ancestor maps to the latest successor even
when an intermediate successor was also processed and restaged. Item-level
`current_revision_iri` remains the route observed while that row was processed.
`restaged_revision_iris` as a creation list, not an apply queue; use
`bundle_summary.ready_restage_successor_revision_iris` plus a final apply check
for candidates to apply. If an already-handled row has
`stale_resolution_state_after="restaged_successor_stale_unresolved"`, its
current successor is stale too; inspect or restage `current_revision_iri`.
If the bundle also lists a ready successor in
`ready_restage_successor_alternative_to_applied_source_iris`, it is still an
alternative to an already-applied staged source; treat that as semantic review
gating even when the row's next action is `apply_after_review`.
Each item also carries `next_action_after` and
`next_action_queue_item_after` / `suggested_next_actions_after` for that
`current_revision_iri`, which is the direct row-level route to follow after the
batch decision. `next_action_queue_item_after` is scoped to
`current_revision_iri`, not the original source row.
Each item also carries `restaged_from` when its source is itself a refreshed
successor. It does not apply refreshed revisions; review and apply
remain explicit follow-up steps. In dry-run mode, passing `path` still writes
the requested review export while leaving graph history unmutated.

`doxabase.apply_staged_revision`

Applies one staged revision to its target graph roles after conservative
graph-state conflict checks and preview SHACL validation. The helper rejects
already-applied staged revisions and rejects target graph count or digest drift
from the staged `beforeTripleCount` values and graph snapshots. Patch checks
follow the recorded `rc:patchSequence` order from the original preview. On
success it records an `rc:AppliedStagedRevision` history event linked to the
staged revision. The return payload includes
`post_apply_recheck_revision_iris` for other current staged revisions sharing
changed graphs or validation dependencies, plus `post_apply_recheck_revisions`
rows with each revision's `changed_graphs`, `shared_changed_graphs`,
`recheck_reasons`, fresh `application_status`, `decision`, `blocking_reasons`,
`next_action`, `suggested_next_actions`, and `suggested_next_calls`. Re-run
apply checks on those rows before further mutation when other graph changes may
have happened. It is a first apply path, not a full merge/rebase workflow.

`doxabase.export_staged_revision`

Writes a Markdown review bundle for a staged revision, including validation
diagnostics before patch payloads when validation failed. The bundle also
includes a live `Current Apply Check`, so stale exports show conflict status,
count or digest drift, validation-skipped reason, and suggested next calls as of
export time. Exports can include a `Semantic Review Warning` before the apply
check when the live apply check reports semantic risk. For simple
single-assertion `map` changes that still replay cleanly, the export includes a
`Judgement Panel` section with values, value-type context, rationale, caveats,
routes, and safety notes. Stale single-assertion exports may lack the judgement
panel but still warn from stored review context. Restaged exports include a
top metadata `Restage headline` before the apply check; stale original exports
include a top `Restaged by` line when a refreshed successor already exists.
Exports include a `Linked Support` section when supporting observations, claims,
patterns, or evidence are recorded on the staged revision.
Suggested export actions use revision-derived `/tmp` filenames with a short hash
to reduce collisions across concurrent runs; callers may override the path. This
is for human/agent review.

### doxabase.export_staged_revisions

Writes one Markdown review bundle for several staged revisions in caller-chosen
order. Use it after `stage_systematisation` when failed, repaired, and
alternative framings should travel together for review. Pass
`executive_summary` when the bundle should open with the agent's current
provisional verdict. The summary table includes each staged revision's current
apply status, decision, current validation state, and staged-time validation
result. The returned payload includes `revision_summaries` with the same status
rows as structured data: current apply status, blockers, validation state,
alternative/restage links, authored review recommendations, live
`apply_recommended_resolution` guidance, effective `summary_recommendation`
text matching the grouped Markdown table, recommendation source/scope fields,
per-row `next_action`, and suggested next actions. Stale
sources that already have `restaged_by` point suggested actions at the refreshed
current successor instead of another restage. `current_restaged_by` follows
deeper restage chains while `restaged_by` preserves the direct provenance edge.
`current_alternative_to` follows refreshed successors while `alternative_to`
preserves provenance. The payload also returns
`bundle_summary` with status/state counts, unresolved stale sources, handled
stale sources, ready successors, all validation-failed revisions by current
apply status, deduped
`recommended_review_iris`, `recommended_mutation_review_iris`,
`recommended_apply_or_restage_review_iris`, `recommended_repair_review_iris`,
and `recommended_applied_inspection_iris`. Prefer
`bundle_summary.next_action_queue` when an autonomous script needs the most
direct apply/restage/repair/inspection routing without joining the older fields
manually. `bundle_summary.next_action_queue_items` adds the resolved target IRI,
row-vs-target flag, and semantic alternative gate fields for each queued row;
`semantic_review_required_queue_counts` flags gated rows by queue.
`bundle_summary.warnings` calls out
bundle-level sequencing hazards such as ready/no-op reviews sharing a changed
graph that should be re-checked after each apply, plus source-only bundles whose
recommended review target is outside the current bundle. If imported odd
history has a parallel restage successor that is already applied outside the
followed current route, the bundle recommends applied-event inspection and names
the source, successor, and applied event in warnings;
`post_apply_recheck_revision_iris` is the machine-readable affected-revision
list for pre-apply grouped-review hazards.
`sequential_apply_recheck_candidate_iris` is a clearer alias for the same list.
`apply_staged_revision` returns the post-apply affected-sibling queue for the
revision that was actually applied, including live routing fields on each row.
Treat
`recommended_mutation_review_iris` as a broad compatibility queue and prefer the
narrower apply/restage, repair, or applied-inspection fields when routing
automation.
Grouped Markdown mirrors those buckets in a `Review Queues` section so human
reviewers do not have to infer the routing from the summary table alone. It also
mirrors the top-level recommended-review sets and derived next-action buckets
there; the older `post_apply_recheck_revision_iris` field is labeled as
sequential apply recheck candidates because it is a pre-apply grouped-review
hazard list.
Bundles with restaged revisions include a `Restage Context` section near the
top. When a stored alternative target has a restaged successor, grouped
Markdown includes `Alternative Context` with the current comparison target.
Relative export paths are resolved from the repository root and returned as
normalized absolute paths.

## Import and Validation

`doxabase.import_trig`

Imports a TriG file into graph roles. Fixture graph IRIs such as `https://richcanopy.org/graph/map` map to local role names like `map`.

`doxabase.import_revision_snapshots`

Imports a JSON revision snapshot handoff bundle written by
`doxabase.export_revision_snapshots`. Use it after an RDF project/history import
when exact applied-diff or stale-drift triples must be available in the
receiving capsule. Existing `(revision_iri, graph_role)` snapshot pairs are
skipped by default; pass `replace=true` to overwrite them. The result includes
`post_import_snapshot_evidence` with the same status/action shape as
`describe_revision_snapshot_evidence`; if rows were imported before history RDF,
follow its `import_trig` action.

`doxabase.export_graph`

Exports one or more graph roles as one flattened RDF graph file. The default is
the `map` graph in Turtle. Use it for quick single-graph review artifacts. The
result includes per-graph triple counts.

`doxabase.replace_graph_triples`

Removes caller-authored Turtle triples and inserts caller-authored replacement
triples in one mutable graph. The default `allow_count_change=false` makes this
a controlled same-count replacement helper: DoxaBase checks the effective
mutation first and raises before writing if the graph count would change. The
result includes before/after counts, before/after content digests, actual
removed/added triple counts, `same_count`, and `digest_changed`.

Use it for small graph maintenance moves and staged-revision field trials where
you need a same-count digest drift without exporting, RDFLib-editing, and
re-importing the whole graph. It is not a semantic merge/rebase tool.

`doxabase.export_trig`

Exports graph roles as a named-graph TriG bundle using graph IRIs such as
`https://richcanopy.org/graph/map`. Use it when preserving graph roles matters,
for example when dumping a scratch capsule after a field trial.

By default this exports the mutable project graphs: `ontology`, `map`,
`observations`, `patterns`, `evidence`, `shapes`, and `history`. Useful presets
are `workflow` / `review_bundle` for `map`, `observations`, `patterns`, and
`evidence`, plus `all_with_seeds` when you explicitly need immutable seed graphs
included too. Workflow/review-bundle exports do not include `history`, so use
the default project export or an explicit history-bearing bundle for
revision-lineage handoffs. All-with-seeds bundles may require special import
handling because normal capsules protect `base_ontology` and `base_shapes`.

`doxabase.export_revision_snapshots`

Exports stored SQLite-side revision snapshot rows as JSON. This is separate
from RDF graph export: TriG preserves revision metadata and graph snapshot
summaries, while this bundle preserves the exact rows used by
`doxabase.describe_applied_revision_diff(include_triples=true)`. Filter with
`revision_iris=[applied_iri]` and `graph_roles` when a handoff only needs one
applied diff; applied-event filters include the staged source snapshot rows
needed for before/after reconstruction. The bundle may include historical
triples that are no longer current graph facts.

`doxabase.load_example_fixtures`

Convenience tool that imports the AIS and Polymarket RC fixtures.

When called with `replace=true`, DoxaBase clears the graph roles used by the bundled fixture set once, then imports all fixtures into those roles. This resets the example fixture data without letting later fixtures erase earlier fixtures.

`doxabase.validate_graph`

Runs pySHACL over the selected scope using logical `shapes`
(`base_shapes + shapes`). Use `scope="patterns"` for pattern work and
`scope="all"` after importing fixtures. Validation uses RDFS inference, so
class membership can be inferred from vocabulary such as `rdfs:range`; use
property, node-kind, count, or value constraints when explicit checks matter.
The response includes bounded structured `results` with focus node, result path,
constraint, severity, value, and messages when pySHACL reports failures.
