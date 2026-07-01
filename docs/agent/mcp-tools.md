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

## Storage Access Primer

For query planning and executable-catalog work, keep storage protocol separate
from root shape. `storage_protocol` values include `local_path`, S3-style
object storage, and database-backed storage such as `rc:DatabaseStorage`;
`location_kind` is one of `"object"`, `"directory"`, `"prefix"`, or
`"connection"`, never `"local_path"`. Local filesystem roots usually use
`rc:LocalFilesystemStorage`; database relation identifiers belong on storage
access records, and `path_templates` may live on the dataset, partition scheme,
or storage access. Always keep `storage_root` explicit enough for
`describe_query_context` to distinguish a real object from a directory/prefix
or database connection.

## Capsule Inspection

`doxabase.graph_overview`

Returns named graph counts, top classes, top predicates, key entity counts, and known namespaces.
The response field is `named_graphs`; there is no top-level `graph_counts`
field. Derive graph counts from `named_graphs[].triple_count`.

`doxabase.scan_sensitive_literals`

Scans selected graph roles for suspicious credential-like subject URI, predicate
URI, object URI, or literal terms and returns only redacted snippets. Each match
includes `term_position` and `term_kind` so agents can tell whether the hit came
from a subject IRI, predicate IRI, or object value. Use it for detailed
graph-only inspection when storage, evidence, source paths, identifiers, or
descriptions may contain secrets; use `export_preflight` for the export-level
decision. This is a conservative audit helper, not a proof that the graph is
secret-free. Export helpers report
`sensitive_literal_count` and `privacy_warnings` when this scan finds matches,
but exports remain faithful RDF and do not redact automatically. The scan result
itself uses `match_count`, `returned_match_count`, and `omitted_match_count`;
`sensitive_literal_count` is also present as an alias of `match_count` for
scripts that compare scan and export-preflight payloads.
If a returned context field such as `subject` or `predicate` itself contains a
sensitive-looking value, that context field is also replaced with a redacted
marker.
Privacy-adjacent orientation payloads also redact scanner-matching display text
in `ResourceSummary` cards, profile/evidence summaries, evidence source lists,
profile value previews, and context-slice export `seeds[]` labels/descriptions.
This protects response summaries from common copy-paste leaks; RDF and Markdown
exports remain faithful and should still use `fail_on_sensitive` when shareable
output must block.
`describe_context_slice` now includes redacted scanner metadata for the returned
raw triples, but its inspection payload remains faithful: raw `triples`, `trig`,
labels, summaries, and revision/evidence context can still contain project
terms. Report `sensitive_literal_count`, `privacy_warnings`, and redacted
`matches`; do not paste full context-slice JSON or TriG before preflight when
the content may travel outside the local project.
The scan is not a general path/shareability hygiene check: non-secret local
paths, object-store URIs, endpoint URLs, and relative paths are preserved in
exports and do not by themselves trigger `privacy_warnings`. Keep user-specific
paths or endpoint details that should not travel outside the project out of the
graph, or replace them with collaborator-safe references before export.

`doxabase.export_preflight`

Dry-runs the privacy/export scope for `graph`, `trig`, `revision_snapshots`, or
`handoff_bundle` exports without checking paths or writing artifacts. Use it
before unattended or shareable exports when you need a single decision object
rather than remembering separate scan and `fail_on_sensitive` steps. The result
selects the same graph roles and snapshot rows as the corresponding export
helper, returns redacted match locators with stable non-secret `match_id` values,
and reports `decision="block"` when `fail_on_sensitive=true` would block the
write. When no credential-like terms match, the decision is
`clean_by_scanner_only`; this still sets `shareability_review_required=true`
and `shareability_review_status="required_not_completed"` because scanner-clean
is not proof that paths, endpoints, project facts, or history payloads are
appropriate to share. Follow the suggested export action with
`fail_on_sensitive=true` after that separate review.
When a broader graph or handoff preflight blocks but the intended handoff only
needs clean context around known resources, the blocked response suggests
`preflight_context_slice_export(seed_iris=["<target-resource-iri>"])`. Use that
route for importable resource-scoped review context; do not treat it as a
recovery-complete revision handoff.
For a query result or query failure recorded with `record_query_result`, use the
returned `evidence_iri` as that seed and `profile="resource_brief"` when the
broad handoff is blocked by unrelated graph content. This preserves query
status, source-span, and scanned-source evidence without pulling unrelated dirty
map resources into the export; scanner-clean still requires shareability review.
In lazy tool-discovery environments, search for the exact dotted name
`doxabase.export_preflight` if a bare `export_preflight` or `preflight` lookup
does not expose the tool.

Privacy/export route matrix:

| Artifact goal | Preflight route | Write route |
| --- | --- | --- |
| Flattened graph/Turtle | `export_preflight(export_kind="graph", graphs=[...])` | `export_graph(..., fail_on_sensitive=true)` |
| Named-graph TriG | `export_preflight(export_kind="trig", graphs=...)` | `export_trig(..., fail_on_sensitive=true)` |
| Revision snapshot JSON | `export_preflight(export_kind="revision_snapshots", ...)` | `export_revision_snapshots(..., fail_on_sensitive=true)` |
| Recovery-complete project handoff | `export_preflight(export_kind="handoff_bundle", graphs=["project"])` | `export_handoff_bundle(..., fail_on_sensitive=true)` |
| Context slice TriG | `preflight_context_slice_export(...)` | `export_context_slice(..., fail_on_sensitive=true)` |
| Staged/profile Markdown review | Attempt the relevant export with `fail_on_sensitive=true` | `export_staged_revision`, `export_staged_revisions`, or `export_profile_insight_review_bundle` |

Staged/profile Markdown has no separate export preflight because the generated
review text depends on live apply checks and route accounting. Treat
`fail_on_sensitive=true` as the preflight: a staged row whose patch is clean can
still produce dirty Markdown if export-time drift or validation context quotes
unrelated current graph content. When a broad handoff preflight blocks, do not
share an apparently clean staged/profile Markdown review unless that export
succeeds with `fail_on_sensitive=true`.

`project_brief` privacy health follows the handoff-bundle route, so its
`sensitive_literal_count` can include both current project graph matches and
stored revision-snapshot matches.

`doxabase.project_brief`

Returns a read-only orientation brief over datasets and active queues. It
combines key graph counts, project-wide dataset query-readiness summaries,
profile-map-update draft counts for recent profile evidence, current staged
revision review counts, per-queue task counts, and bounded recommended next
tasks. Use it when arriving cold or when a loop may be over-polishing one
workflow while missing another active queue. If `limit_crowded_queue_types` is
non-empty, rerun with a larger `limit` or inspect `queue_counts` and
`omitted_queue_counts` before choosing the next task.
Dataset/task resource summary display text and profile/evidence orientation
summaries are redacted when they match the sensitive-term scanner, but the brief
remains an orientation payload, not a shareability proof.
Profile draft actions embedded in `project_brief` are also recursively redacted
in their `arguments`, `call`, and `source_*` route metadata. Call
`draft_profile_map_updates` directly when you need the executable raw action
payload for a local mutation decision.
Check `next_best_expansion` before repeating visible recommended tasks; if it is
non-null, follow or evaluate that rerun before trusting a tight brief's frontier.
In unattended loops, run `full_frontier_expansion` when it is non-null before
repeating visible recommended tasks; it expands both `limit` and
`profile_candidate_limit` enough to expose the currently counted task frontier
and hidden profile draft candidates together.
For scripts, prefer `first_unattended_action` / `first_unattended_call` as the
canonical first hop. It resolves the precedence rule directly: blocking
privacy/export safety review or stale seed recovery first, otherwise frontier
expansion or the first returned frontier task. `frontier_status` repeats the
routing audit in compact form, including hidden task/profile counts,
`must_rerun_call`, and
`mutation_allowed_after`.
Do not read `frontier_status.is_complete` as permission to mutate; it only says
the hidden frontier is fully exposed. `first_unattended_action` and
`mutation_allowed_after` remain authoritative when safety review is still
blocking.
After completing a safety/export review, resume with the prior
`frontier_first_action` or `frontier_status.must_rerun_call` only for read-only
inspection. Do not mutate or export until a rerun clears
`mutation_allowed_after`.
Check `safety_first_action` / `safety_first_call` when you need to explain the
safety branch separately; when a blocking privacy/export health task exists, it
points to the redacted `export_preflight` review before any expansion or
mutation-oriented work. When immutable seed graphs are missing current staging
vocabulary, it points to stale seed recovery guidance or handoff preflight
before query/profile mutation helpers that would fail on the stale seed.
`frontier_first_action` still chooses `full_frontier_expansion` first, then
`next_best_expansion`, then the first returned recommended task, and
`frontier_first_source` records which surface supplied it.
Then read `health_tasks`, which is not limited by `recommended_next_tasks` and
can also route agents to widen the brief, increase `profile_candidate_limit`, run
redacted privacy/export review, or handle stale immutable seed graphs.
Recommended task rows can also carry `task_advisories` and `task_group` when a
health issue directly affects that row. For example, fixture staleness remains an
advisory rather than a safety gate, but affected `query_repair_review` rows carry
`task_advisories[].code="query_fixture_staleness_review"` and a group with
`suppression_policy="review_group_before_member_mutation"` so scripts that
consume `recommended_next_tasks[]` do not need to separately correlate
`health_tasks[]`.
`profile_queue_counts["profile_candidate_omitted"]` and the
`expand_profile_candidate_limit` health task mean some profile evidence was not
drafted at all under the current candidate bound; rerun `project_brief` with the
suggested `profile_candidate_limit` before treating profile queues as exhausted.
When current staged work exists, a `staged_frontier_review` task points to
`plan_staged_revision_recovery`; follow that first before staging duplicate
profile or query repair work. `staged_review` rows are also ordered ahead of
fresh query/profile mutation tasks so a low-limit brief does not hide the
specific current staged item behind new staging work.
Pending query/profile fields are computed from current staged work beyond the
bounded `staged_review.items` slice, so a pending IRI may be hidden from the
returned staged rows when the brief is limited; use the IRI with
`plan_staged_revision_recovery` or rerun `project_brief` with a larger limit for
more display context.
When a low-limit brief can show only one task for a queue type,
`recommended_next_tasks` prefers pending-staged query/profile rows as the
representative so duplicate-staging warnings are not hidden behind fresher
same-type work.
For `expand_project_brief`, `suggested_limit` is a bounded next step and may be
iterative on a crowded project. When an unattended loop needs one rerun that
shows every task payload currently represented by `queue_counts`, use
`exhaustive_suggested_limit`.
Tasks labelled `query_repair_review` point back to `describe_query_context`,
not directly to `draft_query_plan`, so agents can inspect reviewed repair
templates before drafting or executing any route. Tasks labelled
`query_context_review` can also point at query blockers, but they mean the
context currently has no lifted repair template; the task action points to
`describe_query_context` even when the dataset summary still lists a
review-gated `draft_query_plan` action for deeper inspection.
Tasks labelled `query_plan_handoff` are low-priority ready-query lanes. They
appear when `describe_query_context` reports `ready_for_query_planning` and point
to the query context's `draft_query_plan` action when one is available, even when
profile-run inspection actions push that draft call beyond the bounded
`datasets[].query.suggested_next_actions` preview. Ready physical query handoffs
are visible in `recommended_next_tasks` instead of only inside the dataset query
summary. Read
`query_plan_handoff_summary` on those tasks before following the first draft
action; it surfaces the selected relation or URI, handoff kind, execution
blockers, required bindings, and unselected ready/direct-clean candidate indexes.
This is especially important for database-backed datasets where candidate 0 may
be an archive relation while candidate 1 is the current table.
Tasks labelled `profile_review` are scoped by `profile_evidence_iri`; keep that
evidence IRI with the work item even when the first suggested action is a shared
dataset-level blocker review such as `describe_query_context`. Pending staged
profile-map updates only lower the priority of pure map-update reruns; open
scalar conflict, metric vocabulary, or type advisory lanes keep the profile task
visible at normal priority.

`doxabase.list_entities`

Lists entities by RDF type, graph role, optional text filter, limit, and offset. Start with `type="rc:Table"` and `graph="map"`.
For type-aware retrieval, use types such as `rc:Pattern`, `rc:Claim`,
`rc:Evidence`, or `rc:SourceSpan`; the text filter searches literal and
URI-valued facts attached to each resource, not only labels.

`doxabase.describe_resource`

Returns outgoing and incoming triples for one resource, with available labels,
RDF types, per-direction total/returned/omitted counts, offsets, and optional
bounded blank-node closure. Use it after `list_entities` when lexical search
found a resource but you need its structured claim/evidence/source-span context.
For SHACL shapes, pass `include_blank_node_closure=true` and read
`blank_node_triples` separately from direct `outgoing` triples.

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
that the assertion is correct. Related claims and patterns can include
counter-evidence or reconsidered claims; read the claim text, lifecycle, and
route explanation before treating related lore as positive support.
When an exact requested object is absent, inspect
`same_subject_predicate_triples` and `absence_note` before deciding whether the
current map already contains a more careful value. For column subjects, follow
the owner-dataset suggested actions when you need table-level lore. For layout,
partition, or storage assertions, inspect `nearby_context_triples` before using
the assertion as executable planning context. Use `related_route_summaries` to
find the most directly related lore resources, and `related_routes` when you
need to know whether an observation, claim, pattern, evidence item, or revision
matched the subject, requested object, current same-slot object, or another
nearby lore item. Route summaries include `relevance_tier` and
`generic_value_only`; treat generic-value-only routes as weak context because
they only matched shared controlled values, not the specific assertion subject.
Prefer `suggested_next_actions` over parsing
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
`history_plus_snapshot_rows` can still emit an `import_trig` action when
`missing_current_graph_roles` is non-empty. That means history and snapshot rows
were imported, but one or more current project graph roles needed by the
snapshots are empty, so mutation recovery should wait for the complete project
RDF bundle.

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
only populated for revisions with graph patch payloads. `total_count` aliases
the legacy total `count`, and `returned_count` is the returned page length;
prefer those explicit fields in generic pagination scripts. Rows include
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
fields, semantic-risk fields when populated, alternative-gate fields, and
`alternative_set_iris` / `alternative_set_source_iri` / `alternative_set_role`
when returned rows compete as alternatives. Non-current rows include
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

`doxabase.list_graph_versions`

Lists stored graph-version snapshots for one graph role, newest first. Use this
when a workflow needs the timeline of `map`, `ontology`, `patterns`, or another
graph role without scripting over revision rows. Rows include `revision_iri`,
`record_kind`, `snapshot_semantics`, `triple_count`, `content_digest`,
`count_basis`, `exact_snapshot_available`, `snapshot_evidence_status`, lineage
links, and suggested calls to `describe_revision_graph_snapshot` and, for exact
rows, `describe_graph_version_diff`.
`snapshot_semantics` distinguishes `staged_before_graph`,
`applied_after_graph`, and `recorded_graph_snapshot`. Set `exact_only=True` to
hide RDF-only count/digest snapshots, and `include_current=False` when a caller
only wants historical snapshot rows. This is stored-snapshot timeline browsing,
not temporal checkout or replay.

`doxabase.describe_graph_version_diff`

Compares one stored graph-version snapshot with either another stored version
or the current live graph for the same graph role. Call it after
`list_graph_versions` when an agent needs to answer "what changed since this
version?" rather than merely inspect count/digest metadata. Pass
`after_revision_iri` to compare two stored snapshots; omit it to compare the
`before_revision_iri` snapshot with the current graph. Exact added/removed
triple counts are reported when stored rows are available, and
`include_triples=true` includes bounded changed-triple arrays.
The response also carries compact before/after revision context and
`related_revision_iris`, plus follow-up actions to `describe_revision_lineage`
and, for applied-event comparison points, `describe_applied_revision_diff`.
Use those actions when a graph-version diff is being used as recovery context;
the graph delta alone does not explain staged/applied/restaged lineage.

`doxabase.describe_revision_lineage`

Describes one graph revision's staged/applied lineage by revision IRI. Use it
when you already have a staged source, restaged successor, or applied event IRI
and need the compact relationship card without opening patch payloads. The
response includes the selected list row, `selected_revision_iri`, selected
role, visible paired staged/applied row, `paired_revision_iri`, applied and
staged revision IRIs,
`applied_source_revision_iri` for the staged row that actually applied, current
staged successor when one is still live, latest applied/current revision,
restage chain IRIs, alternative revision IRIs, related revision IRIs, warnings
for broken lineage, and next-action routing from the latest row. Related IRIs also include applied
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
`next_action_queue_item` mirrors list queue items for the selected row and
exposes the resolved next-call target.

`doxabase.list_resource_revisions`

Lists revisions that explicitly touch one resource. Matches come from
`rc:revisionAnchor`, exact subject/predicate/object URI mentions in staged patch
payloads, or an applied event whose staged source matched the resource. The
response top-level collection is `revisions` with total `count`; each row wraps
the normal revision list row under `revision`, exposes `revision_iri` for
first-pass routing, and adds
`match_types`, `patch_mentions`, `applied_source_revision_iri`, and
`applied_source_patch_mentions`. `total_count` aliases `count`, and
`returned_count` is the returned page length. `patch_mention_scan` and per-row incomplete
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
staged/applied row when visible, `selected_revision_iri`,
`paired_revision_iri`, graph-level `restage_chain_iris`,
`alternative_revision_iris`, merged `related_revision_iris`, graph-lineage
warnings, selected next action, and the same patch scan status used by
`list_resource_revisions`. When
an applied event is linked, the response can include a resource-filtered applied
diff summary with exact added/removed triples for that resource. If the selected
row is an old stale source whose restaged successor has already been applied,
`applied_revision_iri` and the diff summary follow that applied successor while
`restage_chain_iris` preserves the original source route; resource lineage now
also names the applied staged source explicitly as
`applied_source_revision_iri`, matching graph lineage.
This is not full
graph-version browsing; call `describe_staged_revision` when patch content is
needed. `next_action_queue_item` is the same row-vs-target card for the selected
resource row. RDF-only imports can preserve resource route and staged/applied
pairing, but exact resource-level applied diffs need the companion revision
snapshot JSON import.

`doxabase.search`

Lexically searches literal RDF claims and URI-valued graph terms, returning
matched resources with graph, IRI, label, types, predicate, matched text, and
snippet. Use it to rediscover caveats, observations, evidence, labels, path
templates, source notes, column names, and exact project vocabulary tokens such
as custom profile metric kinds. When an unscoped search page is dominated by
immutable seed graph hits, the response includes `scope_hint` and scoped retry
`suggested_next_actions`; follow those before concluding project map,
observation, pattern, or evidence facts are absent.
When `matches` is empty, the response can still include top-level
`suggested_next_actions` for shorter project-graph retries, entity browsing,
and current staged-payload search. Follow these before treating remembered lore
or proposed vocabulary as absent.
The result has `matches`; there is no `count` field. Use
`len(result.matches)` when scripting against the Python API.

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
planned and carry `domain="analysis"`. For caveat warnings, read
`details.caveat_severity_iri` / `details.caveat_severity_label` before routing
an executable handoff; `severity` remains the query-planning warning level.
Within each linked-pattern reason, `iri` and `pattern_iri` both name the linked
pattern. Scan `match_groups` first for relevance tiers, route labels, resource
kinds, and supporting resources; use raw `matches` when every route matters.
Treat group and tier counts as triage hints, not as confidence scores:
`relevance_tier_counts` counts grouped matches, while `raw_match_count` counts
unfolded route matches. Direct and map-implication groups are usually the
strongest local relevance signals, while claim/observation-supported groups
explain the surrounding lore. Call `doxabase.describe_pattern` before using a
pattern as a decision rule.

### doxabase.describe_profile_run

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
`definition_found`, `observed_metric_iri`, optional `definition`, `promotion_patterns`,
`mixed_support_patterns`, `mixed_support_note`, `context_patterns`, and
`pending_staged_promotion_iris`, and structured `suggested_next_actions` so
agents can inspect existing ontology definitions, pending staged vocabulary, or
nearby metric vocabulary before recording claims/patterns/promotions. When an
undefined or ambiguously typed metric has a same-evidence pattern naming it as a
target or map implication, the advisory suggests `describe_pattern`. If no
matching current staged metric vocabulary skeleton already exists, it also
suggests a reviewable `stage_pattern_promotion` skeleton for an ontology
`rc:ProfileMetricKind`; otherwise it routes to `describe_staged_revision` and
`export_staged_revisions` for the pending staged skeleton.
The first metric context action seeds `describe_context_slice` with
`observed_metric_iri` so the initial handoff stays on the profiled dataset; use
nearby metric-vocabulary actions when you intentionally want broader same-metric
usage.
When a metric reruns as `project_metric_defined` after a promotion, do not
stage duplicate vocabulary; use the observed-metric context action for the
dataset handoff and `describe_context_slice(..., profile="deep_lore")` from the
metric, promotion pattern, or revision when you need to rediscover the
supporting promotion trail. `project_brief` preserves the defined metric in
profile draft summaries and `profile_queue_counts`, but does not create a
`profile_review` task when `project_metric_defined` is the only remaining
profile finding for that draft.
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
`source_profile_advisory.mixed_support` plus a review-note cue.
`mixed_support_review_groups` lifts those shared-support comparisons to the top
level with review lanes, semantic moves, advisory indexes, and suggested calls.
Inspect the group before promoting or asserting either lane independently; when
both lanes generate staged drafts, review or export those drafts together before
applying either lane on its own.
The draft
also includes `recommendation_count`, `representative_recommendation_indexes`,
`scalar_conflict_groups`, `scalar_conflict_group_count`,
`metric_advisory_count`, `representative_metric_advisory_indexes`,
`metric_advisory_status_counts`, `type_advisory_count`,
`representative_type_advisory_indexes`, `type_advisory_status_counts`, and
`advisory_followthrough_plan`, and top-level `suggested_next_actions` /
`suggested_next_calls` for compatibility.
Prefer `suggested_next_action_groups` / `suggested_next_call_groups` for quick
routing; non-empty lanes are grouped as `query_context_review`,
`profile_map_updates`, `profile_scalar_conflict_review`,
`metric_vocabulary_review`, and `profile_type_review`.
When same dataset/evidence profile map updates are already staged, the draft
sets `pending_staged_profile_update_iris` and the `profile_map_updates` group
starts with `plan_staged_revision_recovery` for those staged rows. Treat any
following `stage_profile_map_updates` action as available only after reviewing
the pending staged work; direct staging rejects another same dataset/evidence
profile-map update by default, so pass
`allow_pending_profile_updates=true` only when another staged profile update is
intentional.
`query_context_review` appears first when the dataset already has physical-query
metadata such as a path template or layout, but `describe_query_context` still
reports blocking physical metadata issues. Its action points to
`describe_query_context` and carries `source_query_context` with readiness,
blocking issue codes, repair group count, and the dataset route anchor; follow
it before treating profile-derived map updates as query-ready context.
Use representative advisory indexes when you need one review row per duplicate
metric or type advisory group; each row also carries `metric_advisory_index` or
`type_advisory_index` for row-local routing. Group lanes may de-duplicate shared
actions, such as one `describe_pattern` call supporting several metric
advisories; grouped metric/type actions carry `source_profile_advisory` with
the source advisory kind, index field, represented advisory indexes, duplicate
group keys, duplicate advisory indexes, duplicate profile-observation IRIs, and
optional metric-only `observed_metric_iris` plus optional `mixed_support`.
Grouped profile map-update actions carry `source_profile_map_update` with
represented recommendation indexes, duplicate group keys, duplicate profile
observation IRIs, route anchors, and route patterns. All grouped profile action
source blocks include `route_group_key` and `route_step_key`; use the group key
to bridge draft actions to profile insight bundle candidates, and the step key
to distinguish individual actions within one route group. Use each advisory
row's own `suggested_next_actions` for per-metric or per-column follow-through.
Recommendation rows carry `recommendation_index`, `default_stageable`,
`default_skip_reason`, and duplicate-group fields; metric and type advisories
carry duplicate-group fields too.
Use `advisory_followthrough_plan` when you need a compact menu over the
metric/type lanes. Its `semantic_move` values group existing advisory actions
as `define_metric`, `define_value_type`, `assert_map_type`, or
`caveat_fallback`; each item echoes route keys, advisory indexes, status counts,
primary call, `primary_action_kind`, whether the primary call writes graph state,
route anchors/patterns, and `source_profile_advisories` blocks for
caller-authored alternatives. Match both `semantic_move` and
`primary_action_kind` when scripting a mutation; `semantic_move` alone can match
context-inspection rows and staging rows for the same metric/type lane.
Generated mutating advisory actions for `stage_map_assertion_change`,
`stage_pattern_promotion`, and `stage_systematisation` already include
`profile_route_sources` in their arguments; preserve that argument when calling
them. Profile insight review bundles treat persisted route sources as
`direct_action`; live draft overlap remains support-only context.
If a top-level `stage_profile_map_updates` action is present, review the draft
and use that action as a starting point. Its accepted indexes default to the
representative indexes whose rows have `default_stageable=True`. Sampled
row-count recommendations remain review candidates in
`representative_recommendation_indexes`, but they are omitted from the default
staging action unless the caller explicitly opts in with
`allow_sampled_row_count_updates=true`. Same-evidence scalar conflicts, such as
two full-scan row counts for the same dataset or two nullable values for the
same column, also get `default_stageable=False`; review the observations and
choose at most one value explicitly. Use `scalar_conflict_groups[]` for the
structured choose-one options; each option carries a
`stage_profile_map_updates` action for one representative observed value, but
those option actions are exposed through the
`profile_scalar_conflict_review` lane rather than the default
`profile_map_updates` lane or flat `suggested_next_actions`. Each lane action
has `source_scalar_conflict` metadata with route group/step keys and is mutually
exclusive with sibling options from the same conflict group. Both the option and
the lane source include `recommendation_contexts[]` with profile observation,
sample, basis, observed-count, profile-row-count, and confidence fields; review
that support before choosing between conflicting scalar values. After one scalar
conflict option has been applied, sibling observations from the same evidence
remain non-default-stageable when the applied value already matches the current
map; the scalar-conflict review lane then routes to inspection rather than a
new stage call. Treat that as conflict memory, not as permission to flip the map
back unattended. If
`recommendation_count == 0` and either metric or type advisories are present,
handle the result as advisory-only: follow advisory grouped suggested actions and
do not call `doxabase.stage_profile_map_updates`. When recommendations and
advisories coexist, follow `profile_map_updates` for map staging and keep metric
or type review lanes separate.

### doxabase.plan_profile_followthrough

Reruns `draft_profile_map_updates(dataset_iri, evidence_iri)` and returns a
route-aware follow-through plan for advisory lanes. Use it after a profile type
advisory first led you through `record_pattern`, or after applying one related
staged revision made sibling readiness uncertain. The helper resolves
`source_profile_advisory.produces_result_bindings` /
`consumes_result_bindings` metadata into refreshed structured action
arguments; do not parse `action.call`.

Pass `result_bindings` as a mapping from `binding_key` to the returned value,
for example `{binding_key: pattern_iri}` after `record_pattern`. The result
includes `binding_resolutions`, `action_resolutions`, `produced_bindings`, and
fresh `suggested_next_actions`. Use top-level `missing_binding_keys` as the
compact worklist when a first pass needs prior action results before some
actions can be called. A resolved paired
`stage_map_assertion_change` action has the bound `pattern_iri` appended to
`arguments.supporting_patterns` and annotated under
`arguments.profile_route_sources[].resolved_result_bindings`, preserving the
route source that profile insight review bundles use as `direct_action`.

Pass `staged_revision_iris` to recheck related staged rows. By default this is
read-only and echoes the existing `check_staged_revision_apply` next actions.
Set `restage_stale_revisions=true` only after review when stale siblings should
be mechanically refreshed with `restage_staged_revision`; the helper still does
not apply profile-generated map or ontology changes.

### doxabase.stage_profile_map_updates

Stages accepted `draft_profile_map_updates` recommendation indexes as one
grouped reviewable `map` revision. Pass `dataset_iri`, `evidence_iri`, and
`accepted_recommendation_indexes`. The result returns item statuses,
`staged_recommendation_indexes`, `skipped_recommendation_indexes`,
`not_selected_recommendation_indexes`, `status_counts`, metric advisories,
type advisories, their status counts, and the staged revision when at least one
accepted recommendation was staged. When a staged
revision is created, `suggested_next_actions` starts with
`check_staged_revision_apply` for the read-only pre-apply check, then an
`export_profile_insight_review_bundle` action scoped to that staged revision.
When every accepted recommendation is skipped, `staged_revision` is `null`,
the wrapper's top-level `revision_iri` alias is also `null`, and
`suggested_next_actions` is empty; inspect `items[]` and `status_counts` for the
skip reasons.
Run the export again after staging related metric vocabulary, type-review, or
caveat/systematisation alternatives so the bundle can compare all lanes
together. The helper uses
helper-equivalent RDF for dataset and column shells, keeps metric advisories as
review prompts, keeps type advisories separate from staged map patches,
preserves every grouped profile observation when one duplicate representative
is accepted, skips accepted sampled row-count recommendations unless
`allow_sampled_row_count_updates=true`, and has no row-count recommendations to
stage for explicit non-table assets. It also skips accepted scalar
recommendations when the accepted set contains multiple disagreeing
same-evidence values for the same map assertion; rerun the call with one chosen
value after review. If another current staged profile-map update already
anchors the same dataset/evidence pair, the helper raises before staging unless
`allow_pending_profile_updates=true` is passed after explicit review. Optional
`supporting_claims`,
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
`draft_profile_map_updates` for the same dataset/evidence; the returned
`suggested_next_actions` includes that structured rerun action after the staged
revision apply-check and review-bundle export actions, with
`preconditions.staged_revision_applied` naming the staged revision that must be
applied first. That rerun is what turns related type advisories into map-present
`rc:physicalType` / `rc:valueType` assertion actions.

### doxabase.export_profile_insight_review_bundle

Exports one grouped Markdown review bundle for staged revisions connected to a
profile run. Pass `dataset_iri`, `evidence_iri`, and `path`. The helper
discovers current staged revisions, plus already-applied staged source rows, by
shared profile evidence, supporting profile observations, related support
patterns, and profile-derived anchors such as the dataset, metric IRIs, columns,
and observed types from `draft_profile_map_updates`. Use it after staging
accepted profile map updates and any metric vocabulary, type-review, or
caveat/systematisation alternatives you want reviewed together. Set
`include_applied_staged_sources=false` to restrict discovery to current staged
work, or raise `applied_staged_source_limit` when a profile run has more applied
source matches than the default scan returns.
Explicit `revision_iris=[...]` are seeds, not a strict filter. For a strict
review of only those requested staged rows, also set
`include_current_staged_work=false` and
`include_applied_staged_sources=false`.
Pass `fail_on_sensitive=true` when unattended or shareable profile review
exports should raise before writing if the generated Markdown contains
credential-like or secret-looking literals.

The returned payload includes `candidates[]` with `relation_reasons`, matched
support/evidence/anchor fields, `profile_route_keys`,
`profile_route_groups`, `candidate_revision_iris`, and the nested
`export_staged_revisions` record when a bundle was written. When no candidate
revision is found, `candidate_count` is `0`, `export` is `None`, and no
Markdown file is written; use `warnings` and `open_profile_review_lanes` as the
handoff signal. It also includes
`open_profile_review_lanes`: live draft route groups that still lack a
`direct_action` candidate in the exported bundle. Treat support-only matches as
context, not completion; for example, a staged profile-map update can support a
metric or type lane while that lane remains open. The grouped
payload also includes `executor_decision_summary`, a compact routing object over
the semantic apply gate. Read its `decision`, `mutation_policy`,
`safe_single_apply_candidate_revision_iris`,
`safe_single_apply_candidate_rationales`, `blocked_candidate_revision_iris`, and
`open_review_lanes` before choosing any mutation, then inspect the detailed
candidate rows. Bundle and candidate `profile_quality_summary` /
`sampled_evidence_caution` fields call out sampled profile evidence that may be
mechanically ready without full-scan scope. The summary is derived from the same
gate fields and does not replace semantic review.
Markdown review summary includes a `Profile Route Bridge` table when candidates
match draft route groups. The bridge's `Row` column uses the same `Revision N`
row number as the later grouped bundle sections, and `Candidate` repeats the
row summary so Markdown-only reviewers can jump from a route lane to the
matching candidate without reverse-joining IRIs. Route groups include
`match_strength`:
use `direct_action` for the lane a staged row appears to implement, and treat
`strong_support` / `related_support` as related context rather than lane
satisfaction. New profile-map staged revisions persist their route source in
history, so already-applied sources can still show their original
`profile_map_updates` direct-action lane after the live draft is resolved. If a
fresh live draft later emits another `profile_map_updates` lane for the same
already-applied source, that follow-up is shown as `strong_support` or
`related_support`, not as another direct action for the applied row.
Generated query-planning repair rows can similarly recover a
`query_context_review` direct-action lane from their review note when the blocker
has already been fixed. Same evidence alone does not make an unrelated pattern a
related pattern; support should connect through profile observations, targets,
map implications, or explicit `revision_iris`.

### doxabase.describe_query_context

Returns a compact read-only projection for query planning around one dataset:
dataset summary, physical-metadata readiness, `readiness_note`, an `issues`
list for missing, risky, or informational physical metadata, `analysis_warnings`
for caveats that matter after a query can be planned, planning notes, columns,
path templates, derived `query_target_decision` and `query_target_candidates`,
physical layouts, storage access descriptions, partition schemes,
dataset/layout verification status and note, caveats, and structured
`suggested_next_actions` for drafting the selected route. It also returns
`suggested_repair_action_groups` for reviewed metadata repair templates, plus
`profile_summary` beside `row_count_snapshot`, so a planner can follow profile
evidence IRIs and `profile_run_candidates` without a separate
`describe_dataset` call when row counts or metric context came from profiling.
When profile run candidates exist, `suggested_next_actions` includes
`describe_profile_run` before query-plan drafting. Several profile-run actions
can appear before the draft action when candidate row counts disagree, or when a
snapshot-matching run is sampled, unknown, or mixed basis. Follow the profile
actions before treating a profile-derived count as current. Also read
`row_count_snapshot_basis` and `dataset_profile_row_count_bases` on
`profile_summary.profile_run_candidates[]`; a matching row count can still come
from sampled, unknown, or mixed-basis profile evidence.
When `profile_summary.evidence_iris` is non-empty but there are no
`profile_run_candidates`, query context still adds a bounded
`describe_profile_run` action for singleton profile evidence. That action carries
`source_profile_evidence` with the evidence summary, query-source paths, result
sources, parsed execution status/engine/query hash when available, and short
profile summaries.
If that singleton evidence coexists with missing storage, path, layout, format,
protocol, location, or layout-verification blockers, the context can also add a
`draft_query_evidence_storage_overlay` skeleton action. Treat its placeholder
arguments as a review checklist, not inferred truth: replace the fields listed
in `placeholder_fields` / `reviewed_value_fields` and supply
`required_extra_arguments` before calling the helper.
Use `dataset_profile_row_counts`, `dataset_profile_row_count_bases`,
`row_count_snapshot_matches`, and `row_count_snapshot_basis` on
`describe_profile_run` results to preserve that normalized row-count context
after following a profile-run action.
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
`candidate_index` points into `query_target_candidates`. Candidate cards also
include `candidate_selector`, a stable response field for reviewed
`draft_query_plan` calls. Candidate
`review_required` includes whole-context blockers; `direct_review_required`
ignores sibling blockers and shows which target candidates have their own
storage/path/layout problem. `selected_candidate_direct_clean` gives the same
cue on the selected decision row. When that selected candidate is direct-clean
but context-blocked, the suggested `draft_query_plan` action carries
`allow_context_blocked_candidate=true` and the explicit candidate selector. For
multiple direct-ready candidates, inspect `unselected_ready_candidate_indexes`
and rerun/draft with an explicit `candidate_selector` if candidate order picked the
wrong route; peer suggested actions include the same allowance when sibling
candidate metadata is the only broader blocker.
Every `describe_query_context` action whose `tool_name` is `draft_query_plan`
also carries `route_card`: a compact copy of the selected candidate's selector,
template source, storage label, route role summaries, path or relation handle,
direct issue codes, required bindings, and partition binding examples. Prefer
`action.route_card` over parsing `reason` text when choosing between peer,
layout-selection, production/current, sample, archive, or backfill routes.
`query_target_decision.route_intent_review_candidate_indexes` points at ready
or direct-clean peer cards with production/current/canonical route-role intent
that the selected candidate lacks; review those cards before unattended
execution. In a globally blocked context, inspect
`unselected_direct_clean_candidate_indexes` when strict ready indexes are empty
but another candidate has no direct blocker. When linked physical layouts are
ambiguous, suggested `draft_query_plan` actions include explicit
`candidate_selector` / `physical_layout_iri` pairs for the selected candidate and
peer candidates whose only direct blocker is layout ambiguity; their
`route_card.physical_layout_iri` mirrors the reviewed layout choice. For
database-backed storage, only
storage-access-owned templates become `relation_identifier` values. Dataset or
partition path templates paired with database storage are ignored for the
database route when they already form a clean non-database candidate. Otherwise
they are review-only `database_relation_template_source_mismatch` candidates
with no relation identifier; record the schema/table/relation on the storage
access before using that route as a database handoff. If the storage access
already has one or more relation templates, the repair action list puts
`remove_misplaced_source_template` first and marks the add action
`already_satisfied` with `skip_when_already_satisfied=true` so automation can
skip the duplicate add.
Use `suggested_repair_action_groups` as the scripting entrypoint; each group
preserves the source `repair_hint_path` when you need to jump back to
`issues[].details.repair_hint`. Database relation mismatch groups and compact
pending action options carry `misplaced_template_subject_iri`,
`misplaced_template_source`, and `misplaced_template`, so scripts can distinguish
dataset and partition source templates without parsing action arguments. In the
common move case, stage an add of the reviewed relation identifier onto the
storage access, then stage removal of the misplaced source template only if
review confirms it was relation metadata
rather than a real file/object path.
When `candidate_relation_identifier.storage_access_relation_templates` is
present, inspect those storage-owned relation templates against the target
candidates; skip the already-satisfied add action when one is the reviewed
relation and review the ordered remove action instead. Repair actions declare
`required_extra_arguments=["object", "rationale"]` and
`placeholder_fields=["object"]` for the add-template step; replace `object` with
the reviewed relation identifier and add a reviewed rationale before calling
`stage_map_assertion_change`. The stale dataset or partition path is review
context, not the relation identifier. Root-only
database storage without a storage-access relation template is also review-only
with `database_relation_template_missing`, even when `location_kind="object"`;
use the lifted `suggested_repair_action_groups` row for the reviewed
add-template action on the storage access.
For non-database storage, `location_kind="object"` means the storage root is the
exact dataset object/location. `describe_query_context` still exposes that
`storage_access_location` candidate when dataset or partition templates are
present, and any candidate that would append a template to the object root is
review-only with `storage_object_location_has_path_template`.
For storage protocol/location mismatch repairs, templated actions also name
`placeholder_fields` and `reviewed_value_fields` for the reviewed value to fill
in.
`suggested_repair_action_groups` lifts those existing nested repair hints into a
top-level `query_repair_review` lane with the source issue index/code/resource,
repair hint type, copied context, ordered action templates, action count,
status counts, pending/skippable counts, per-action pending options, and the
legacy union of pending required extra arguments. Use it for repair discovery
and scripting, but keep the review gate: these rows are templates, not flat
call-ready `suggested_next_actions`. `action_status="pending_review"` is the
normal actionable status for one of these review-gated templates. If
`choice_mode="choose_one"`, select one
action and follow that action's own `required_extra_arguments`; do not treat the
group-level `pending_required_extra_arguments` union as one call signature. Fill
placeholders, add required extra arguments such as `rationale`, skip actions
explicitly marked already satisfied or already pending, and review each action's
condition before calling the named tool.
Context-blocked direct-clean routes can expose
`repair_action_type="remove_stale_partition_scheme_link"` to stage reviewed
removal of a stale `rc:partitionedBy` link that is blocking an otherwise clean
query target.
When storage is already linked but no physical layout is present,
`missing_physical_layout` exposes
`repair_action_type="record_or_stage_physical_layout"`. Prefer the reviewed
`stage_query_physical_layout_repair` option when the layout/link should carry
graph-revision rationale before becoming map state; use
`record_map_physical_layout` only when a direct current-best map write is
intentional. Use `repair_context.storage_protocol_iris`,
`repair_context.database_storage_present`, and `file_format_guidance` to choose
the reviewed `file_format`; database relation handoffs should use table-layout
formats such as `rc:PostgreSQLTable`, `rc:SQLiteTable`, or `rc:MySQLTable` when
those match the engine.
When `missing_storage_access` appears, use the lifted repair group for reviewed
repair templates: stage a new non-secret storage access and dataset link, record
one directly only when direct map mutation is intentional, or stage a reviewed
`rc:hasStorageAccess` assertion to an existing storage access. Candidate ranking
uses exact path-template matches, dataset-token overlap, weak generic-token
overlap, and a linked-dataset caution for accesses already attached elsewhere;
read `dataset_token_matches`,
`generic_dataset_token_matches`, `dataset_partial_token_matches`,
`generic_dataset_partial_token_matches`, `linked_dataset_iris`, and
`match_reasons` before choosing a reviewed target. Missing-storage repair actions
have stable `action_type` values (`stage_reviewed_storage_access`,
`record_reviewed_storage_access`, and `stage_existing_storage_access_link`), and
the repair hint carries `choice_mode="choose_one"` plus
`candidate_existing_storage_accesses` when current map storage accesses are
available for review. A candidate can carry
`pending_staged_repair_iris` and `candidate_status="already_pending"` when a
current staged `rc:hasStorageAccess` add already proposes that exact
dataset/storage link; review the staged row before staging a duplicate. When
some visible candidates are already pending, the repair context and compact
stage-existing-link option expose `already_pending_candidate_count`,
`already_pending_storage_access_iris`, and `pending_staged_repair_iris`; the
link action can still be pending if other non-pending candidates remain
available for review. In `project_brief`, top-level
`pending_staged_repair_iris` is limited to current staged rows that change
query-planning metadata on the dataset or linked query resources such as storage
accesses, physical layouts, partition schemes, or columns, not arbitrary staged
caveats or profile work. `describe_query_context` also marks exact matching
repair actions as `already_pending` so compact `pending_action_options` can skip
duplicate storage/path/protocol/layout mutations. For staged or direct
new-storage actions, include the optional `path_templates` field only when the
storage access itself owns the path or database relation template. Omit it when
a dataset or partition already carries the reviewed file/object path template,
or you can create duplicate equivalent query target candidates. Database
relation identifiers are
the important storage-owned exception: for
`storage_protocol="rc:DatabaseStorage"`, `path_templates` are reviewed database
relation identifiers such as `schema.table`, and `storage_root` is the
connection reference. After direct database-storage repair,
rerun `describe_query_context`; if the same relation-like value remains on the
dataset or partition, follow the `database_relation_template_source_mismatch`
repair group. The direct `record_map_storage_access` template carries
`review_rationale_guidance` because the helper writes current-best map facts
without recording graph-revision rationale. If
`issues[].details.fixture_staleness_hint` is present,
known AIS or Polymarket fixture tables exist but the capsule has zero
`rc:StorageAccess` resources; treat that as a stale/reduced fixture capsule and
load fresh fixtures into scratch before judging query-target behavior. The
lifted `suggested_repair_action_groups[]` row also carries this warning in
`group_advisories`, so scripts that use the repair-group lane directly can
review the fixture-health condition before staging repeated missing-storage
repairs.
`project_brief.health_tasks[]` also surfaces this as
`query_fixture_staleness_review` when the current frontier contains query repair
work, with `fixture_names`, `known_fixture_table_iris`, `storage_access_count`,
and a representative `describe_query_context` action. Use it as an advisory
anti-loop cue before staging repeated missing-storage repairs; privacy/export
and stale-seed safety gates still take precedence.

### doxabase.draft_query_plan

Returns a non-executed, review-gated physical plan draft over
`describe_query_context`. It currently supports `engine="duckdb"` and selects
the candidate named by `query_target_decision.candidate_index` by default. Pass
`candidate_selector`, `candidate_index`, or `storage_access_iri` for an explicit route selection, pass
`physical_layout_iri` after reviewing linked physical layouts with distinct
signatures, and use `allow_context_blocked_candidate=true` only when the
selected candidate is
direct-clean but sibling metadata still blocks the whole context. When the
blocker comes only from sibling candidate metadata, pair the allowance with
an explicit `candidate_selector`, `candidate_index`, or `storage_access_iri`; selectorless automatic
drafts keep the context review gate and report
`context_blocked_candidate_allowed=true` /
`context_blocked_candidate_used=false`. If `storage_access_iri` matches
multiple candidate paths, prefer the explicit peer `draft_query_plan` actions
returned by `describe_query_context`; otherwise rerun with `candidate_selector`
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
`scan.physical_layout`, and `scan.physical_layout_selection_note`. A single
linked layout can also block execution when the candidate path extension
conflicts with its file format; `physical_layout_path_extension_mismatch`
keeps the draft metadata-review-required until the path/template or layout file
format is corrected. Binding rows
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
For the shorter pre-draft handoff, `describe_query_context.suggested_next_actions`
adds `route_card.binding_example` and `route_card.binding_examples` to partition
template actions, for example `event_date='2026-06-30' -> ...`. These examples
are illustrative reviewed-value placeholders, not DoxaBase inference of runtime
parameters.
`candidate_column_match_status` marks the hint set as `none`, `single`, or
`ambiguous`; review ambiguous rows before choosing any source column, even when
individual matches have `confidence="high"`. Confidence is per match, while the
status summarizes the whole hint set. Top-level
`handoff_kind` gives a compact machine-readable route, and top-level
`handoff_summary` copies the first-pass handoff facts most often needed in
reports: selected candidate index/note, scan function, URI or database relation
identifier, readiness gate booleans, execution-attempt blockers, required
bindings, issue codes, warning/caveat counts, and unselected ready/direct-clean
candidate indexes. Read `handoff_summary` first for routing, then inspect the
full `scan`, `storage_environment`, `review_gate`, `issues`, and caveats before
execution. `handoff_kind` values include
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
DuckDB has no file-scan function for a selected file/object storage-layout
shape. Database relation handoffs intentionally keep `scan.function=None`; their
execution gate is runtime resolution, not missing file-scan inference.
`physical_layout_storage_protocol_mismatch` means an explicit layout selection
crossed storage route kinds, such as database storage plus `rc:CSV` or local
file storage plus `rc:PostgreSQLTable`; keep it review-gated and choose a
layout compatible with the selected candidate route.
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
draft shape today, so expect `scan.function=None`,
`ready_for_execution_attempt=false`, and `runtime_resolution_required` rather
than executable SQL; read `scan.relation_identifier` and
`scan.connection_reference` instead of `scan.uri_template` for the recorded
database handoff. If the selected database candidate came from a dataset or
partition path, `scan.relation_identifier` stays absent and the plan remains
`metadata_review_required`. These scan fields mirror the selected candidate's
database-specific fields. The `scan` card includes dataset-level
verification notes plus template lineage and source verification fields, so
surprising shared or inherited path templates stay attached to their source
resource and warning notes. It does not resolve endpoint profiles, credentials,
object existence, or execute SQL.

### doxabase.draft_query_evidence_storage_overlay

Returns non-mutating `stage_graph_revision` arguments for turning reviewed
query/profile evidence into storage access and physical layout map metadata.
Use it after `record_query_result` or `describe_profile_run` shows that an
external query scanned or attempted a real source, but `describe_query_context`
is still blocked by missing storage, path, or layout metadata. The evidence may
be profile-shaped successful query evidence or ordinary blocked/failed/partial
query-result evidence, as long as it is linked to the requested dataset.
`describe_query_context` may suggest this helper directly for singleton
query/profile evidence with physical blockers; those suggested arguments contain
review placeholders and must be replaced before use.

The helper does not infer storage values from query text, result artifacts, or
logs. The caller supplies reviewed values such as `storage_protocol`,
`storage_root`, `location_kind`, `path_templates`, `file_format`, optional
endpoint/credential hints, compression, and a layout verification note. The
response echoes those reviewed values in `reviewed_overlay`, including generated
or caller-supplied storage/layout IRIs, labels, access mode,
endpoint/bucket/prefix/region/path-style fields, credential reference,
compression, and replaced dataset/storage/layout verification values. It also
reports the source query context and source profile/query evidence, previews
validation for the Turtle addition, and returns `stage_arguments` plus a
`stage_graph_revision` suggested action. Treat
`source_query_evidence.scanned_source_handles` /
`source_query_evidence.scanned_source_paths` as reviewed provenance context for
choosing those values, not as an automatically accepted storage root.
`source_profile_evidence` is retained as a compatibility alias for the same
payload.
Call that staged-revision helper, check/apply the staged row, then rerun
`describe_query_context` before drafting a query plan. When the dataset already
has a different
`rc:layoutVerificationStatus` or note, `stage_arguments` includes removal
patches for old dataset-level values. When the caller reuses existing
`storage_access_iri` or `physical_layout_iri`, the same removal graph also
replaces stale verification status/note triples on those resources so max-count
SHACL validation stays clean after staging and apply.
This route preserves graph-revision rationale and keeps the draft step
side-effect free.

### doxabase.stage_query_storage_access_repair

Stages a reviewed storage access resource and `rc:hasStorageAccess` dataset
link for a `missing_storage_access` query repair. Pass `dataset_iri`,
`storage_access_iri`, `storage_protocol`, `storage_root`, and a reviewed
`rationale`; optional location kind, access mode, path/relation templates,
endpoint fields, and verification note are written to the staged
`rc:StorageAccess`. Use storage-access-owned `path_templates` for database
relation identifiers, but omit them when the dataset or partition already owns
the file/object template. The helper returns a normal staged-revision record, so
run `check_staged_revision_apply`, apply the ready row, then rerun
`describe_query_context` before drafting a query plan. By default it rejects
datasets that already have storage access resources; pass
`allow_existing_storage_accesses=true` only after reviewing that an additional
route will not create duplicate query target candidates. When the repair comes
from a profile draft's `query_context_review` lane, pass
`profile_route_sources=[query_action.source_query_context]` so profile insight
review bundles can mark the staged repair as a direct query-context action. If
that profile draft used sampled evidence, the route source carries its sampled
evidence caution into generic staged exports as well.

### doxabase.stage_query_physical_layout_repair

Stages a reviewed physical layout resource and `rc:hasPhysicalLayout` dataset
link for a `missing_physical_layout` query repair. Pass `dataset_iri`,
`layout_iri`, `file_format`, and a reviewed `rationale`; optional label,
description, compression, verification status, and verification note are written
to the staged `rc:PhysicalLayout`. The helper returns a normal staged-revision
record, so run `check_staged_revision_apply`, apply the ready row, then rerun
`describe_query_context` before drafting a query plan. By default it rejects
datasets that already have physical layouts; pass
`allow_existing_physical_layouts=true` only after reviewing that an additional
layout will not create ambiguous query target candidates. It also accepts
`profile_route_sources` for profile `query_context_review` lanes, matching
`stage_query_storage_access_repair`.

`doxabase.describe_context_slice`

Returns a bounded, route-explained subgraph around one or more seed IRIs. Use
`profile="dataset_brief"` for table handoff context, `profile="pattern_brief"`
for pattern support context, and `profile="deep_lore"` when explicit revision
metadata should come along too. Use `profile="resource_brief"` for arbitrary
RDF resources such as ontology terms, SHACL shapes, evidence, source spans, and
non-dataset map resources that need route-explained one-hop context. Dataset/deep-lore
slices include bounded profile observations, observed value-frequency nodes,
scalar profile metric nodes, and profile metric kinds returned through the
dataset context. They can also start from a profile observation, observed
profile metric node, metric-kind IRI used by profile metrics, or value-type IRI
used as `rc:observedValueType` in profile observations. Deep-lore slices can
also start from an
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
revision history, vocabulary context, validation shape context, mixed context,
or a referenced-only object. For project profile metric kinds,
`referenced_only` means the slice reached the
IRI as an object/reference; it does not answer whether the metric vocabulary is
defined. Pair metric-oriented slices with `draft_profile_map_updates` when that
status matters.
`reading_order` and `route_legend` provide the static reading protocol and
meanings for the routes present in the response. Set `include_trig=true` when
you need raw TriG text for inspection, and raise
`max_triples` when `truncated` is true and the slice still looks relevant.
Truncation only affects raw `triples` and `trig`; resources and structured
contexts still describe the full selected slice.
There is no `route_summaries` field; use `reading_order`, `route_counts`, and
`route_legend` as the first route summary before inspecting each resource's
`primary_route` and `routes`.
For seed tables and table resources reached directly from the seed,
`suggested_next_actions` can include `describe_query_context` when either
dataset-owned operational warnings or query-context repair groups are present.
This includes storage access, physical-layout, partition-scheme, and mapped
column handoffs whose incoming/reference routes identify an owning table. It
catches query-only metadata issues such as misplaced database relation templates
that are not stored in `dataset_contexts[].operational_warnings`.

`doxabase.preflight_context_slice_export`

Dry-runs an importable context-slice TriG export without writing a file. Use it
when a handoff should include only the selected resource neighborhood rather
than every resource in a graph role. It reuses `describe_context_slice`
selection, omits immutable seed graphs by default, scans only the selected
export triples for credential-like graph terms, and returns the same
`decision`, `scanner_clean`, `shareability_review_required`,
`shareability_review_status`, `would_block_sensitive_export`,
`sensitive_literal_count`, `privacy_warnings`, `warnings`, and suggested-action
style used by broader export preflights. `scanner_clean=true` is still not a
shareability proof; local paths, endpoints, and confidential project facts need
human review. `handoff_fit` is `resource_scoped_review_context` for ordinary
slice exports and `resource_scoped_review_context_not_recovery_complete` when
history graph triples are included. If the selected slice includes `history`, the
preflight warning and suggested actions also point to
`export_handoff_bundle`; context slices can import revision review context but
do not carry the revision snapshot rows needed for exact recovery. Selected
history references pull in direct `rc:GraphPatch`, `rc:GraphSnapshot`, and
validation-result triples so a fresh receiver can validate the imported review
slice; that closure is also included in the preflight privacy scan.
If the selected slice is truncated, `graphs` and `graph_counts` describe only
the capped raw triples selected for export, not every structured resource role.
Read the truncation warning for selected surface roles and omitted graph roles;
the first suggested action reruns `preflight_context_slice_export` with the full
candidate triple cap before the normal write action.
Returned `seeds[]` are response summaries: label/description display text is
redacted when it matches the sensitive-term scanner. The selected export triples
are not redacted; use `fail_on_sensitive=true` to block writes when they contain
credential-like terms.

`doxabase.export_context_slice`

Writes the selected context-slice triples as TriG. Pass
`fail_on_sensitive=true` for unattended/shareable exports. Keep
`include_seed_graphs=false` unless you deliberately want a bundle that may
require `import_trig(..., allow_immutable=True)`: fresh DoxaBase capsules
already contain the standard base ontology and shape seed graphs. Prefer this
helper over `describe_context_slice(include_trig=true)` when the artifact must
round-trip into a fresh capsule or avoid unrelated graph siblings. A written
slice with `history` graph triples still has `recovery_complete=false` and
returns an `export_handoff_bundle` action for recovery-complete handoff needs,
even though selected patch/snapshot resources are validation-complete in the
TriG review artifact.

`doxabase.describe_pattern`

Returns compact handoff context for one `rc:Pattern`: pattern text, rationale,
targets, supporting observations, supporting claims, evidence/source spans, and
map implications.

`doxabase.record_observation`

Records a structured observation in the `observations` graph. Optional evidence
fields create a linked `rc:Evidence` resource in the `evidence` graph. Use this
for point-in-time findings, profile counts, and workflow notes that should
remain available to later agents. For validation-clean evidence, include
`evidence_sources`; `evidence_summary` alone is descriptive prose, not a source
identity. When `observed_column` names a column that is not yet in the map,
`observed_column_name` can preserve the source-level column name without
promoting the column into current map state. For `observation_type="profile"`,
`observed_physical_type` and `observed_value_type` preserve type findings as
evidence without asserting them as current map facts.

`doxabase.record_query_result`

Records an externally executed query result or failure without executing the
query. It writes an `rc:Observation` or, when successful profile/result counts
are supplied, an `rc:ProfileObservation`, linked evidence, and an optional
`rc:SourceSpan` with `rc:QuerySource` for the query text or query artifact.
Use it after `draft_query_plan` and an external runtime attempt. Supply
`result_sources` for result files, logs, or output artifacts, and
`query_source_path` when the query text has a durable non-secret location.
Supply `scanned_source_handles` for non-secret source files, objects, relation
handles, or path-like inputs the external runtime actually scanned. The older
`scanned_source_paths` name remains accepted as an alias. For database
handoffs, a reviewed handle such as `warehouse-prod:mart.orders` can preserve
`connection_reference` plus `relation_identifier`; do not coerce it into a fake
filesystem path. Later query-context and storage overlay handoffs expose scanned
source handles separately from query text and result artifacts.
Failed, blocked, cancelled, or partial attempts are ordinary observations; do
not pass profile count fields unless `execution_status="succeeded"`.
When `observed_asset` is supplied, the returned payload includes
`suggested_next_actions`: profile-shaped results start with
`describe_profile_run(observed_asset, evidence_iri)` and all observed-asset
results include `describe_query_context(iri=observed_asset)`. Follow those
actions before drafting another query plan or promoting profile-derived facts.

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
Pass `evidence_iri` when a dataset profile should reuse a reviewed profiler-run
evidence resource; this mirrors `record_column_profile` and avoids switching to
`record_profile_bundle` solely to share evidence.
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
For API endpoints, document collections, message streams, model artifacts, and
other non-tabular assets, pass `is_table=False` plus project `extra_types` where
useful. Use `describe_context_slice(profile="deep_lore")` or
`describe_resource` for handoff context; `describe_query_context` should report
`not_applicable_non_tabular_asset` unless a separate queryable table route is
modeled.

`doxabase.record_map_column`

Records or updates a column resource and can link it to a table with
`rc:hasColumn`. Resource-valued fields such as `physical_type`, `value_type`,
and `table_iri` expect IRIs or CURIEs, not prose.

`doxabase.record_map_caveat`

Records or updates a `rc:KnownCaveat` and can link it to affected datasets.
Use prose for the caveat description, and use IRIs or CURIEs for `severity` and
`targets`. `severity` is a closed project control: use `rc:Minor`,
`rc:Moderate`, or `rc:Severe`.

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
For `storage_protocol="rc:DatabaseStorage"`, `path_templates` are
storage-access-owned database relation identifiers such as `schema.table`, and
`storage_root` is the connection reference. Do not copy dataset or partition
file/object path templates here; if the relation is not reviewed yet, omit
`path_templates` and let `describe_query_context` surface the missing database
relation template.
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
`file_format`, `compression_codec`, and `datasets`. Common base file-format
CURIEs include `rc:Parquet`, `rc:CSV`, `rc:JSON`, `rc:JPEG`, `rc:PNG`,
`rc:TIFF`, `rc:GeoTIFF`, and `rc:PDF`.

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
`aggregation_function`, and optional `within_group_ordering`. Asset-level
derivations or aggregations can use `source_datasets` and `target_datasets`
without column mappings; singular `source_dataset` and `target_dataset` remain
compatibility shortcuts for one endpoint each. Use `source_endpoints` or
`target_endpoints` when endpoint role or order matters; each entry accepts
`dataset`, optional reviewed string `role`, optional one-based `order`, and
optional endpoint `iri`, while still writing compatibility source/target
dataset edges. Endpoint datasets, columns, functions, and properties are
resource-valued fields, so use IRIs or CURIEs rather than prose. Dataset
relationship descriptions expose `relationship_kind` as the RDF class IRI and
`relationship_type` as the helper token such as `foreign_key` or `aggregation`.
Column fields must point to column resources; known data assets, datasets, and
tables are rejected in those slots.

`doxabase.record_map_asset_transform`

Records or updates an asset-level derivation or aggregation with reviewed
transform details. Use it when endpoint role/order is not enough and the map
needs durable filters, selection rules, per-output formulas, output functions,
or tuple grain. `relationship_type` must be `derivation` or `aggregation`; the
helper accepts the same `source_dataset`, `target_dataset`, `source_datasets`,
`target_datasets`, `source_endpoints`, `target_endpoints`, and
`derivation_properties` arguments as `record_map_relationship`.

`conditions[]` entries accept optional `iri`, `label`, `description`,
controlled `condition_kind` (`rc:FilterCondition` or `rc:SelectionCondition`),
required reviewed `expression`, optional `expression_language`, and optional
`applies_to_datasets` / `applies_to_endpoints`. `outputs[]` entries require
`target_dataset` and can carry `role`, `formula`, `expression_language`,
`function`, linked `conditions`, and a `tuple_grain`. Tuple grain components
accept exactly one of `column`, `dataset`, or `expression`; `column` must be an
actual column resource, not a dataset/table asset.

`doxabase.record_graph_revision`

Records revision metadata in the `history` graph: changed graph roles, summary,
rationale, optional included review/export graph roles, optional supporting
observations/claims/patterns/evidence, optional `revision_anchors`, validation
result, export path, and graph-count snapshots. It does not compute diffs or
apply graph edits.

`doxabase.record_staged_revision_review_decision`

Records a durable reviewer decision for one staged revision without applying
its patch payload. Use it after reviewing an informational `noop` or
already-effective stale row and deciding there is no useful graph mutation left
to perform. Supported `decision` values are `accepted_elsewhere`, `superseded`,
`discarded`, and `no_effective_change`. The helper writes a
`rc:StagedRevisionReviewResolution` history event linked with
`rc:resolvesStagedRevision`, and the staged source then drops out of
`current_staged_work_only=True` queues while staying visible in full history
with `review_resolution`. By default it refuses live mutation targets routed to
apply, restage, or repair; pass `allow_mutation_target=true` only after explicit
review decides to close that proposal without mutating the graph.

`doxabase.search_staged_patch_payloads`

Search current staged `rc:patchContent` Turtle and route hits to owning
revision/patch actions. Use for staged-only labels before treating history hits
as live facts.

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
Use `evidence` only for actual evidence/source resources already recorded in
the capsule; use `revision_anchors` for affected map, ontology, shape, or
workflow resources. Passing ordinary map resources as evidence should fail
validation rather than silently invent support.
Use `restages_revision` when the new payload is a caller-authored repaired or
rebased successor for a stale staged revision. The tool records
`rc:restagesRevision` / `restaged_from` while keeping the provided additions and
removals intact. If the stale source already has `restaged_by` /
`current_restaged_by`, inspect or target that current successor instead; the
tool rejects parallel successors.

`doxabase.draft_map_assertion_change`

Builds the same single-assertion add/remove/replace preview as
`stage_map_assertion_change` without writing a staged revision to `history`. Use
it when you are asking "should this assertion change exist?" or when the likely
answer depends on caveats, related observations, value-type context, impacts, or
validation. The response includes addition/removal Turtle payloads, patch count
previews, validation fields, impact entries, `assertion_support`,
`judgement_panel`, and `stage_arguments`. If the panel still justifies the
write, follow the staging action in `suggested_next_actions` or pass
`stage_arguments` to `doxabase.stage_map_assertion_change`. High-risk or
do-not-stage drafts put `doxabase.describe_assertion_support` first and demote
staging to an explicit override action. The draft is read-only; history counts
and staged-revision queues should not change.

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
When the assertion stages a selected profile advisory route, preserve the
action's `arguments.profile_route_sources`; the response's
`profile_route_source_count` reports how many usable route sources were stored.
Profile insight review bundles use those persisted sources for exact
`direct_action` closure. Without them, the staged assertion can still appear as
support through shared observations, anchors, or patterns, but it does not close
the advisory lane.
Check the panel first for current/proposed values, caveat
scopes, semantic risk level/reasons, value-type context, reasons the current
value may be intentional, strongest route summaries, impact spotlight entries,
and safety notes. For physical type and value type changes,
`value_type_context` surfaces relevant `rc:valueType` resources and declared
`rc:requiredPhysicalType` values, including whether a proposed value type fits
the column's current `rc:physicalType`.
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
`rc:Varchar` or `rc:SnapshotRow`; treat them as weak context. Drill into
`assertion_support` and `describe_staged_revision` when the change needs more
thought.
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
without requiring a grouped export first. `choose_one_groups` and
`choose_one_group_count` expose the source/alternative comparison groups
directly on the draft response. Rows in `staged_revisions[]` also carry
`framing_index` and `framing_label`, so scripts can map a revision back to the
caller-authored framing without joining against `framings[]` by position. If
later framings actually
default-linked to a first framing that did not route to `apply_after_review`,
`structured_warnings` includes `first_alternative_anchor_not_ready` with
`suggested_rerun_arguments={"link_alternatives": False}`; in that case
`suggested_next_actions` starts with a complete `stage_systematisation` rerun
action using explicit alternative routing. Per-framing `alternative_to` values
reroute siblings without that warning. When multiple framings share `ontology`
or `shapes` patches, `structured_warnings` includes
`shared_semantic_context_applies_to_all_framings`; move those patches into
per-framing additions/removals when fallback alternatives should not carry the
same provisional vocabulary or validation shapes. That warning carries
`shared_patch_summaries`,
`fallback_revision_iris_with_shared_semantic_context`, and
`suggested_rerun_arguments.shared_patch_sources_to_move` so MCP clients can
construct the rerun without parsing prose or guessing which shared patch entry
to move.
When a caller-authored framing directly resolves a profile draft route, such as
a `query_context_review` lane from `draft_profile_map_updates`, pass the
action's source block in `profile_route_sources`:
`profile_route_sources=[query_action.source_query_context]`. Top-level sources
are recorded on every framing. If different alternatives close different
semantic moves, put `profile_route_sources` or `profileRouteSources` on each
framing object so only that staged revision carries that direct route. The
stored staged revision then closes that route as a direct action in
`export_profile_insight_review_bundle`, rather than appearing only as related
support through shared anchors. The returned `profile_route_source_count` should
be greater than `0`; if it is `0`, the draft warning usually means the caller
passed the whole suggested action instead of its source block.

`doxabase.stage_pattern_promotion`

Stages one or more caller-authored RDF framings supported by existing
`rc:Pattern` resources. Use it when a pattern looks ready to become map,
ontology, shape, or other durable project structure, but the graph move should
remain reviewable. The helper does not infer the map shape. It uses the selected
patterns as `supporting_patterns`, rolls up their supporting observations,
claims, and evidence, and uses pattern targets plus `map_implication` resources
as revision anchors before delegating to the staged systematisation workflow.
It accepts `profile_route_sources` and forwards them to
`stage_systematisation`, so profile followthrough plan primary promotion calls
can persist explicit route closure. It returns the same
`systematisation_draft` result shape and routing fields.

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
`recommended_resolution`, `validation_skipped_reason`,
`effective_delta_summary`, `count_drifts`, `snapshot_drifts`, `next_action`,
and structured `suggested_next_actions`.
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
Read `effective_delta_summary` before interpreting top-level
`triples_to_add=0` on conflicts. Its replayable fields match the top-level
delta, while `blocked_patch_triples_to_add/remove` reports the current effective
payload of conflicted patches that were excluded from direct replay. If
`already_effective=true`, inspect the stale row instead of mechanically
restaging it.
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
those cases DoxaBase only drafts the replacement when the current graph has
exactly one same-subject/predicate value and the staged object kind matches the
slot contract: `rowSemantics`, `physicalType`, and `schemaStability` require IRI
objects, while `nullable` allows typed boolean literals. Blank-node objects and
free-text `rowSemantics` literals are not safe automatic repair candidates. When
recognized, `suggested_next_actions` includes `stage_map_assertion_change` with
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

### doxabase.draft_staged_revision_rebase

Drafts a read-only repair/rebase plan for one staged revision. It does not
stage, restage, apply, or export anything. Use it after an apply check routes to
`repair_or_replace`, especially when overlapping single-slot alternatives have
become stale or `validation_failed` after a mechanical restage.

The response includes the live apply check, compact lineage context,
`mode="non_executed_review_draft"`, `draft_status`, `draft_kind`,
`reason_codes`, repair candidates, repair actions, and a compact `next_action`.
When DoxaBase recognizes a safe singleton-slot
repair, such as `rc:rowSemantics` max-count validation failure where the current
graph has exactly one different IRI value, it returns a ready-to-call
`stage_map_assertion_change(change_kind="replace", restages_revision=...)`
action. `repair_actions`, `preferred_action`, and a drafted repair
`suggested_next_actions[0]` are mutating staging calls after the agent has
reviewed `repair_candidates`; they are not the usual review-first apply-check
ordering. The action preserves the selected revision's `alternative_to` link
when present, so semantic alternative gates survive the repair. When the
selected row already has `restaged_by`, `current_restaged_by`, or `applied_by`,
the draft is a redirect and the compact action points at the current successor
or applied event instead of creating a parallel repair.
When no safe repair is drafted, the helper filters inherited
`draft_staged_revision_rebase` actions from `next_action` and
`suggested_next_actions`; follow the remaining inspect/export/manual-repair
route instead of calling the same helper in a loop.

### doxabase.plan_staged_revision_recovery

Plans read-only recovery routes for a staged revision queue. It does not stage,
restage, apply, export, or write files. Use it as the first call when several
staged rows may be ready, stale, already handled by restage, already applied, or
repair-first. With no `revision_iris`, it discovers current staged work through
`list_graph_revisions(include_apply_checks=True, current_staged_work_only=True)`.
With explicit `revision_iris`, it preserves caller order after pagination.
Explicit inputs must be staged patch revision IRIs. If an applied event IRI is
passed, recovery planning reports that it should be inspected with
`describe_graph_revision` or `describe_applied_revision_diff`, or retried with
the applied event's staged source IRI.

The helper wraps `restage_staged_revisions(..., dry_run=True, path=None)` for
classification, grouped queue summaries, old-to-current mappings, and
sequential-apply warnings. When `include_drafts=True`, repair lanes may include
a read-only `repair_draft` from `draft_staged_revision_rebase`. The default is
bounded: `repair_draft_limit=1` embeds one repair draft and defers later repair
lanes with `repair_draft_deferred_reason="repair_draft_limit_reached"`. Use
`repair_draft_limit=0` or `include_drafts=False` for no embedded drafts, and
`repair_draft_limit=None` only when an exhaustive embedded-draft pass is worth
the runtime. Failed draft attempts are reported as lane errors and warnings
while the dry-run route still returns.
If the embedded draft finds no safe automatic repair and has already filtered
out the self-call to `draft_staged_revision_rebase`, the lane and top-level plan
suggestions follow the draft's inspect/export route instead of recommending the
same draft call again.
When lane snapshot evidence is incomplete, the lane and top-level
`suggested_next_actions` promote `import_revision_snapshots` or `import_trig`
before apply/restage actions. The lane queue remains the post-preflight route.

Read `lanes[]` first. Each lane names the `source_revision_iri`,
`current_revision_iri`, `lane`, `batch_action`, status/decision before and
after classification, staged-validation status, snapshot-evidence completeness,
`next_action`, and `next_action_queue_item`. Queue values are row IRIs, not
always action targets. Use `next_action_queue_item.resolved_target_iri` and
`next_action.arguments["iri"]` when present; handled stale rows can route to a
refreshed successor or applied event, while repair actions can create a new
successor and therefore have no existing resolved target.
Use `effective_recovery_action` or `lane` as the route for unattended recovery.
`batch_action` is dry-run batch-restage classifier provenance and can say
`skipped_not_restageable` for ready apply lanes whose effective route is still
`apply_after_review`.
When explicit `revision_iris` include stale sources and current successors,
`lanes[]` intentionally preserves one row per requested source. Use
`resolved_target_groups[]` for the collapsed target-family worklist:
`source_revision_iris` / `requested_revision_iris` show which lanes collapsed
into the same `resolved_target_iri`, while `row_iris`, `current_revision_iris`,
`restage_chain_iris`, `applied_event_iris`, and alternative-set fields preserve
the browsing context. `resolved_target_group_counts` is the deduped queue count
by resolved target; compare it with `next_action_queue_item_counts` when the
source-lane count looks inflated.

`would_restage_revision_iris` is the post-review mechanical-restage list, not an
apply queue. `repair_or_replace_source_revision_iris` is the broad source-row
worklist for lanes currently routing to `repair_or_replace`; it includes
same-slot replacement routes that may not appear in `repair_first_revision_iris`.
For repair lanes whose concrete mutation is a helper call rather than an
existing revision target, `helper_mutation_frontier_actions` and
`helper_mutation_frontier_calls` expose the deduped preferred repair helper
mutations for included repair drafts. Deferred lanes remain in
`repair_or_replace_source_revision_iris`; call `draft_staged_revision_rebase`
for a deferred row or rerun the planner with a larger `repair_draft_limit` when
needed.
Use `mutation_frontier_items` as the complete unattended mutation worklist. It
combines existing apply/restage/repair targets with same-slot helper actions
that create a successor and therefore cannot appear in `mutation_frontier_iris`.
Keep `mutation_frontier_iris` for compatibility or when a script only accepts
existing revision targets. Revision-target items include grouped
`semantic_risk_level` / `semantic_risk_reasons`, `alternative_set_iris`,
`alternative_set_source_iri`, `alternative_set_roles`, and
`alternative_gate_statuses`, so an executor can see choose-one and
semantic-review context before restaging or applying.
`repair_first_revision_iris` and lanes with `lane="repair_or_replace"` should be
inspected or drafted before any restage.
If `sequential_apply_recheck_candidate_iris` is non-empty, apply at most one
ready row, then rerun this helper before taking the next mutation.

### doxabase.draft_systematisation_shared_context_rerun

Drafts a read-only `stage_systematisation` rerun for staged systematisation
rows that carry shared `ontology` or `shapes` context. Use it after
`plan_staged_revision_recovery` or grouped export shows
`shared_context_applies=true` / `shared_semantic_context_applies_to_all_framings`
and semantic review has chosen which framings should keep the provisional
vocabulary or shape context.

Pass the grouped `revision_iris` plus
`shared_context_target_revision_iris`, the subset that should receive the moved
shared context. The helper copies stored `rc:SharedContextPatch` Turtle into
those framings' ordinary additions/removals, leaves fallback framings with only
their own `rc:FramingPatch` content, and returns
`stage_systematisation_arguments` plus a ready suggested action. It does not
stage, restage, apply, or write files.

### doxabase.start_staged_revision_recovery_session

Persists a durable staged recovery session in the `history` graph and returns
the same live shape as `doxabase.describe_staged_revision_recovery_session`.
Use it when a recovery will span several calls, especially after
`import_handoff_bundle`, mixed restage/repair planning, or any queue where you
must apply one row and replan before continuing. The session stores the ordered
source revision list, optional handoff manifest path, initial lane counts, and
planning parameters; it does not restage, apply, or otherwise mutate project
graphs.

### doxabase.describe_staged_revision_recovery_session

Recomputes the current recovery plan for a persisted session. Read
`session_status`, `source_states[]`, `current_plan.mutation_frontier_items`, and
`suggested_next_actions` after every restage, repair staging, or apply. A
complete session can still return inspection actions such as
`describe_graph_revision` or `describe_applied_revision_diff`; those are review
follow-ups, not remaining mutations.

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
immediate describe call. It also includes post-restage routing fields
`status_after`, `decision_after`, `routing_decision_after`,
`stale_resolution_state_after`, `blocking_reasons_after`, `next_action_after`,
`next_action_queue_item_after`, and `suggested_next_actions_after`, derived from
a fresh apply check on the new successor. Follow `next_action_after` before
applying or restaging anything else.
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
listed in `would_restage_revision_iris` only when they remain safe mechanical
restage candidates. Stale sources whose staged-time validation failed and whose
post-batch route is repair-first are withheld from that bulk list and returned
in `repair_first_revision_iris`; inspect their validation diagnostics or call
`draft_staged_revision_rebase` before creating another same-payload successor.
`patch_conflict` rows are
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
The batch response also carries top-level `suggested_next_actions` and
`suggested_next_calls`. Dry runs with mechanical candidates promote one reviewed
`restage_staged_revisions(dry_run=False, revision_iris=[...])` action over
`would_restage_revision_iris`; the suggested call intentionally omits any
dry-run export path so a follow-up does not overwrite the review artifact. Real
batch runs promote deduped item-local continuation actions, such as apply,
inspect, or repair calls for the current successors. If
`requires_recheck_after_each_apply` is true, still apply at most one ready row
from that action list and rerun the recovery plan or export before the next
mutation.
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
have happened. `post_apply_recheck_is_partial_queue=true` makes explicit that
those rows are only the affected-sibling subset, not the full remaining staged
frontier; the top-level `suggested_next_actions` therefore starts with
`plan_staged_revision_recovery(current_staged_work_only=True)`. It is a first
apply path, not a full merge/rebase workflow.

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
When a Markdown privacy warning reports line examples, those line numbers refer
to the final written artifact, after the warning block has been inserted. Pass
`fail_on_sensitive=true` when unattended or shareable Markdown review exports
should raise before writing if the generated bundle contains credential-like or
secret-looking literals.
Suggested export actions use revision-derived `/tmp` filenames with a short hash
to reduce collisions across concurrent runs and include
`fail_on_sensitive=true` by default; callers may override the path. This is for
human/agent review.

### doxabase.export_staged_revisions

Writes one Markdown review bundle for several staged revisions in caller-chosen
order. Use it after `stage_systematisation` when failed, repaired, and
alternative framings should travel together for review. Pass
`executive_summary` when the bundle should open with the agent's current
provisional verdict. Suggested grouped staged-review export actions include
`fail_on_sensitive=true` by default. The summary table includes each staged revision's current
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
per-row `profile_route_keys` and `profile_route_groups` when staged rows store
profile route sources, and grouped Markdown includes a compact `Profile Route
Bridge` table for those rows. The bridge repeats stored sampled-profile
evidence cautions so a Markdown-only staged review does not hide scope warnings.
Use that bridge for profile-derived staged rows when you have only a generic
staged review bundle rather than a full `export_profile_insight_review_bundle`
artifact.
The payload also returns `bundle_summary` with status/state counts, unresolved
stale sources, handled
stale sources, ready successors, all validation-failed revisions by current
apply status, deduped
`recommended_review_iris`, `recommended_mutation_review_iris`,
`recommended_apply_or_restage_review_iris`, `recommended_repair_review_iris`,
`recommended_applied_inspection_iris`, and
`external_recommended_review_iris` for current review targets omitted from the
caller-requested export bundle. Prefer
`bundle_summary.next_action_queue` when an autonomous script needs the most
direct apply/restage/repair/inspection routing without joining the older fields
manually. `bundle_summary.next_action_queue_items` adds the resolved target IRI,
row-vs-target flag, semantic risk level, semantic alternative gate fields, and
symmetric alternative-set fields for each queued row. Grouped Markdown mirrors
the risk and gate fields in `Resolved Targets`. When stored staged rows include
shared `ontology` or `shapes` context patches, `revision_summaries` exposes
per-row `shared_context_patch_count` and `shared_context_graphs`, while
`bundle_summary.shared_context_graphs`,
`bundle_summary.shared_context_patch_summaries`,
`bundle_summary.fallback_revision_iris_with_shared_semantic_context`, and
`bundle_summary.shared_semantic_context_warnings` reconstruct the draft-level
shared-context warning for export-only handoffs. `bundle_summary.review_sequence`
orders those queue items into inspect-redirect, repair, restage, review/apply,
and recheck phases so unattended agents can follow one cross-lane worklist
before opening lower-level queue buckets;
`bundle_summary.snapshot_evidence` separately summarizes whether the included
rows have complete stored snapshot rows. Grouped Markdown includes a compact
positive `Snapshot Evidence` confirmation when `complete=true`; `complete=false`
rows carry the same `import_revision_snapshots` suggested actions as the
Markdown table, while `next_action_queue` keeps normal review/apply routing.
`bundle_summary.warnings` repeats incomplete snapshot evidence as a handoff
preflight so grouped Markdown readers see it in `Bundle Warnings` before the
`Reviewer Decision Matrix` and review queues.
`semantic_review_required_queue_counts` flags gated alternative rows by queue.
`semantic_risk_queue_counts` separately counts queued rows with apply-check
semantic risk (`attention` or `high`), including repair queues when semantic
risk coexists with validation or conflict blockers. List, recovery, and grouped
export queue items copy row-local `semantic_risk_level` and
`semantic_risk_reasons` when their apply check has already computed risk.
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
Grouped Markdown also includes a `Review Sequence` table above `Review Queues`;
prefer it for first-pass human or autonomous routing because it gives row
numbers, summaries, queue names, resolved targets, tools, and the phase reason
in one ordered list.
Bundles with restaged revisions include a `Restage Context` section near the
top. When a stored alternative target has a restaged successor, grouped
Markdown includes `Alternative Context` with the current comparison target.
Relative export paths are resolved from the repository root and returned as
normalized absolute paths.

## Import and Validation

`doxabase.import_trig`

Imports a TriG file into graph roles. Fixture graph IRIs such as
`https://richcanopy.org/graph/map` map to local role names like `map`. The
import preflights every non-empty named graph before mutating storage; normal
imports that encounter immutable seed roles such as `base_ontology` or
`base_shapes`, or an unknown Rich Canopy role, fail without partial graph writes.
When the incoming TriG includes `history` graph `rc:GraphRevision` rows, the
response includes bounded `post_import_snapshot_evidence` rows plus
`post_import_snapshot_evidence_complete`, status counts, incomplete revision
IRIs, and promoted `suggested_next_actions`. If those rows say
`history_only_count_digest`, import the companion revision snapshot JSON before
relying on exact applied-diff, stale-drift, or mutation-recovery triples.

`doxabase.import_revision_snapshots`

Imports a JSON revision snapshot handoff bundle written by
`doxabase.export_revision_snapshots`. Use it after an RDF project/history import
when exact applied-diff or stale-drift triples must be available in the
receiving capsule. Existing `(revision_iri, graph_role)` snapshot pairs are
skipped by default; pass `replace=true` to overwrite them. The result includes
`post_import_snapshot_evidence` with the same status/action shape as
`describe_revision_snapshot_evidence`; if rows were imported before history RDF,
follow its `import_trig` action.

`doxabase.import_handoff_bundle`

Imports a handoff manifest written by `doxabase.export_handoff_bundle`. Use it
when a receiver has the manifest as well as the paired project/history TriG and
revision snapshot JSON artifacts. The helper resolves relative artifact paths
from the manifest directory, reports pre-import snapshot evidence, imports the
TriG first and snapshot JSON second, then returns post-import snapshot evidence
plus `plan_staged_revision_recovery` for the manifest revisions. Manifest
revision lists may include ordinary non-staged `rc:GraphRevision` history or
snapshot context alongside staged patch rows; those import as informational
recovery lanes and should be inspected with `describe_graph_revision`, not
applied or restaged. A stale-seed recovery handoff can legitimately have no
revision rows; in that case the real import returns an empty recovery plan with
`mutation_allowed_after` set to `no_mutation_frontier`, and the next step is to
rerun `project_brief` in the fresh capsule. Pass `dry_run=true` to inspect the
manifest paths and expected receiver action without mutating the capsule. Pass
`replace=true` only when overwriting existing graph roles and stored snapshot
pairs is intentional.
Read `recovery_summary` first for a compact receiver smoke check. It reports
snapshot evidence completeness/status counts, matching recovery-session counts,
recovery lane and next-action queue counts, mutation-frontier IRIs, preserved
profile route keys/group counts, the first mutation-frontier action when one is
available, the first structured follow-up action, and a `recommended_next_step`
value such as `run_import_handoff_bundle`,
`continue_imported_recovery_session`, `follow_recovery_plan_mutation_frontier`,
`complete_handoff_preflight_before_recovery_mutation`,
`review_handoff_privacy_before_recovery`, or `resume_project_frontier`.
When the manifest records nonzero `sensitive_literal_count`, the import can
still be useful locally, but its top-level next action is a redacted
`doxabase.export_preflight(export_kind="handoff_bundle", ...)` privacy review
and recovery/mutation actions are not promoted as top-level continuations until
that review is explicit.
When a manifest revision resolves to a current staged successor that lacks exact
snapshot rows, the import promotes the blocking `import_revision_snapshots` or
preflight action ahead of recovery-session setup and suppresses
`first_mutation_action`; use the summary's first safe action before following
any mutation frontier.
If the imported history already contains a staged-revision recovery session for
the manifest revisions, the result exposes `imported_recovery_session_iris` and
`matching_recovery_session_iris`, and the first suggested action is
`doxabase.describe_staged_revision_recovery_session`. Prefer that imported
session over starting a duplicate receiver-local one. When no matching imported
session exists, the import prepends a
`doxabase.start_staged_revision_recovery_session` action for the processed
revision IRIs before the direct recovery-plan actions.

`doxabase.export_graph`

Exports one or more graph roles as one flattened RDF graph file. The default is
the `map` graph in Turtle. Use it for quick single-graph review artifacts. The
result includes per-graph triple counts plus privacy warning counts from
`scan_sensitive_literals`. Warnings do not block export and the written RDF is
not redacted. Pass `fail_on_sensitive=true` when the export should raise before
creating or overwriting an artifact if the selected graph roles contain
sensitive-looking subject URI, predicate URI, object URI, or literal terms.
Use `doxabase.export_preflight(export_kind="graph", graphs=[...])` first when an
agent needs a read-only decision, redacted match IDs, and the exact blocking
export action before choosing a path.
Export result records expose `artifact_kind`, `importable`,
`recommended_import_tool`, and `recovery_complete`. Use those fields rather
than file extension alone: staged/profile Markdown bundles are review artifacts
and not importable, workflow TriG is importable review context but not a full
recovery handoff, and `export_handoff_bundle` is the recovery-complete pair.

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
revision-lineage handoffs. Their export records include a non-privacy warning
that they are review context only and are not recovery bundles. The default
project export is faithful history, not a shareable no-history view: staged
patch payloads in `history` are exported unchanged when selected, with privacy
warnings rather than redaction.
All-with-seeds bundles may require special import handling because normal
capsules protect `base_ontology` and `base_shapes`.
`sensitive_literal_count` and `privacy_warnings` apply to the selected export
graphs; workflow exports include evidence, so source paths, subject IRIs, and
evidence source strings can trigger privacy warnings. Pass
`fail_on_sensitive=true` for unattended or shareable exports; the tool scans
first and raises before creating or overwriting the artifact when potential
sensitive graph terms are found.
If a copied or older capsule fails staging because immutable `base_ontology`
is missing current staging vocabulary, `seed_base_graphs()` will not refresh a
non-empty seed graph. `project_brief` reports `current_staged_revision_count`
on the `seed_recovery_review` health task and points first to
`export_preflight(export_kind="handoff_bundle")`. Preserve the project/history
TriG plus companion revision snapshot JSON, create a fresh seeded capsule, and
import the manifest there with `import_handoff_bundle`. When the stale capsule
has no stored revision snapshots, the snapshot JSON is empty and the import
returns an empty recovery plan plus a structured `project_brief()` follow-up for
the fresh capsule. When staged rows exist, follow the staged recovery plan
returned by the import.
For strictly non-mutating active-capsule recovery trials, use Python with
`DoxaBase.open_readonly(path)` for `project_brief`, `export_preflight`, and the
handoff export itself. The normal MCP server opens its configured capsule with
regular initialization semantics, which may update SQLite maintenance metadata
even for read-oriented calls.

`doxabase.export_handoff_bundle`

Writes a project/history TriG artifact plus a companion revision snapshot JSON
artifact as one handoff operation. Use it when a receiving capsule needs exact
applied-diff, stale-drift, or revision-lineage reconstruction after RDF import.
It composes the same faithful `export_trig` and `export_revision_snapshots`
payloads, but preflights both output paths and combined privacy warnings before
creating either file. Pass `fail_on_sensitive=true` for unattended or shareable
handoffs; pass `revision_iris` or `snapshot_graph_roles` only when the snapshot
JSON should be narrower than the default all-stored-snapshot export. Pass
`manifest_path` to also write a small JSON manifest that pairs the two artifact
paths, records redacted privacy warnings, sets top-level
`recommended_import_tool="doxabase.import_handoff_bundle"`, and still lists the
lower-level `import_trig` then `import_revision_snapshots` sequence with
expected snapshot evidence statuses. A bundle with no stored revision snapshots
is still recovery-complete for seed refresh or project-graph transfer; importing
it should preserve mutable graphs and return an empty staged-recovery plan. The
result contains nested `trig` and `revision_snapshots` export records, the
manifest payload, optional manifest write metadata, plus combined
`sensitive_literal_count`, graph/snapshot sensitive counts, `decision`,
`scanner_clean`,
`shareability_review_status`, `privacy_warnings`, and `warnings`.
`scanner_clean=true` still means scanner-clean only; receivers should treat
`shareability_review_status="required_not_completed"` as a live sharing gate.
Read `recovery_complete` at the paired handoff level for the bundle as a whole;
the nested TriG and snapshot JSON records are components and are not
recovery-complete by themselves.
When receiving a manifest, prefer `doxabase.import_handoff_bundle` over manually
translating component paths and calling lower-level import tools. The import
helper surfaces a warning when a manifest says shareability review is still
required.
Use `doxabase.export_preflight(export_kind="handoff_bundle")` before choosing
paths when you need to review both the RDF graph roles and stored snapshot rows
without creating artifacts.
If a blocked handoff preflight reports snapshot matches, follow its
snapshot-only `export_preflight(export_kind="revision_snapshots", ...)` action
to inspect stored snapshot rows directly; that avoids repeating a low-limit
combined handoff preflight where graph matches can fill the returned match list.

`doxabase.export_revision_snapshots`

Exports stored SQLite-side revision snapshot rows as JSON. This is separate
from RDF graph export: TriG preserves revision metadata and graph snapshot
summaries, while this bundle preserves the exact rows used by
`doxabase.describe_applied_revision_diff(include_triples=true)`. Filter with
`revision_iris=[applied_iri]` and `graph_roles` when a handoff only needs one
applied diff; applied-event filters include the staged source snapshot rows
needed for before/after reconstruction. That applied-event shortcut does not
include older restage-chain ancestors, so use a full snapshot export or include
those ancestor IRIs explicitly when the receiving agent needs exact full-chain
lineage recovery. The bundle may include historical triples that are no longer
current graph facts. Snapshot JSON is a faithful handoff artifact, not a
redacted shareable view. The export result includes `sensitive_literal_count`
and `privacy_warnings` from scanning stored snapshot quad subjects, predicates,
and object terms; pass `fail_on_sensitive=true` when unattended or shareable
snapshot exports should raise before creating or overwriting the JSON artifact.

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
