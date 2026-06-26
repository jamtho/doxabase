# Query Planning

Use this as the compact route from map metadata to a query-planning handoff.
For the fuller model, read `executable_catalog`; for exact field shapes, read
`response_shapes`.

## Field Precedence

Start with `describe_query_context(dataset_iri)`:

1. `query_target_decision` chooses the candidate. Its `candidate_index` points
   into `query_target_candidates`, and `status` routes the selected target's
   direct state: ready, review-only, blocked, or absent.
2. `query_target_candidates` explain the physical path, relation, template
   source, storage access, verification status, and review reasons.
3. Always compare `readiness` and `issues` with the selected candidate. Broader
   context blockers, including sibling storage facts, can make the whole
   context review-required even when `query_target_decision.status == "ready"`
   for a direct-clean selected candidate.
   `query_target_decision.selected_candidate_direct_clean` is the compact
   boolean for "the selected candidate itself has no direct blocker."
4. Use `suggested_next_actions` when scripting the next step. In the
   context-blocked direct-clean case it gives a `draft_query_plan` call with the
   explicit `candidate_index` and `allow_context_blocked_candidate=True`.

Then call `draft_query_plan(dataset_iri)` for a non-executed handoff:

1. `handoff_kind` is the compact machine-readable route. Use it for first-pass
   client dispatch, then read `review_gate`, `scan`, `binding_requirements`,
   and `storage_environment` for the details behind that route.
   Do not treat `handoff_kind` alone as execution permission:
   `database_relation_handoff` means the selected route is a relation/connection
   handoff, while `review_gate.ready_for_execution_attempt` is the strict gate
   for any execution attempt.
2. Read `source_context.unselected_ready_candidate_indexes`. If it is non-empty,
   the selected candidate has peer ready candidates; inspect
   `query_target_candidates` and rerun with explicit `candidate_index` when a
   different route is intended.
   Candidate order is not an authoring-preference contract. Treat
   `candidate_index` as a pointer into the returned list, not proof that the
   first ready relation/path is the preferred one.
3. `scan.uri_template` is for file/object scans.
4. `scan.relation_identifier` is the database-backed storage handoff; do not
   treat the candidate path as a file URI in that case. Relation identifiers
   come from storage-access-owned templates, not dataset or partition file paths.
   `scan.connection_reference` without `scan.relation_identifier` is
   repair/review context, not a database relation handoff.
5. `scan.function` is only a hint when the physical layout is unambiguous. If a
   dataset links multiple distinct file formats or compression codecs,
   `ambiguous_physical_layout` blocks execution-readiness and leaves the scan
   function unset until the intended layout is modeled or selected.
6. `required_bindings` and `binding_requirements` still need runtime values.
   `review_gate.binding_values_required=True` and
   `handoff_kind="binding_values_required"` make that case explicit. When a
   selected template comes from partition metadata, binding rows may include
   `partition_scheme`, `partition_column`, and `partition_granularity` as
   handoff hints; the granularity describes the partition scheme, not
   necessarily the individual placeholder. Dataset-owned and
   storage-access-owned templates may include `candidate_column_matches` when
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
   `review_gate.blocking_reason_codes` can add
   `query_context_has_other_blockers` when the selected candidate is clean but
   the broader query context is not.
   `review_gate.execution_attempt_blocking_reason_codes` folds in non-review
   execution blockers such as runtime resolution and missing binding values, so
   it is the better machine-routing list when this boolean is false.

For downstream consumers, keep the routing order simple:

1. If `review_gate.ready_for_execution_attempt` is true, and the plan still
   matches the intended client/runtime, a non-executing handoff may become an
   execution-attempt candidate.
2. Otherwise, if `scan.relation_identifier` is present, route it as a database
   relation handoff before generic runtime resolution. The relation can be
   useful even when execution is not ready. A `scan.connection_reference` without
   a relation is repair/review context.
3. Otherwise, route `review_gate.execution_attempt_blocking_reason_codes`, then
   `storage_environment.runtime_resolution_required`,
   `review_gate.binding_values_required`, and remaining
   `blocking_reason_codes` / `all_issue_codes`. Empty blocking codes or
   `executable_without_review=True` do not override a false
   `ready_for_execution_attempt`.
4. Treat `binding_requirements`, partition hints, and candidate column matches
   as review hints. They do not supply runtime values.

When a known-good storage route is blocked only by stale or malformed sibling
metadata, keep `describe_query_context()` as the inventory and call
`draft_query_plan(..., candidate_index=..., allow_context_blocked_candidate=True)`
or `draft_query_plan(..., storage_access_iri=..., allow_context_blocked_candidate=True)`.
Do not use the allowance selectorless: the automatic selection path keeps the
context review gate active and reports `context_blocked_candidate_allowed=True`
with `context_blocked_candidate_used=False` until the caller names an explicit
candidate.
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

## Common Cases

Local file/object candidates can be ready for an execution attempt when the
path or template is verified enough, the scan function is inferred, and runtime
resolution is not required. Still supply binding values and perform ordinary
filesystem/object-existence checks before running anything.

S3-compatible candidates often need endpoint profile, credential reference, and
region or equivalent local runtime setup. DoxaBase records non-secret planning
facts; it does not store secrets or prove the object exists.

Database candidates currently use the generic draft-plan shape. A relation can
be metadata-ready in `describe_query_context()` while
`draft_query_plan().review_gate.executable_without_review` is false because the
generic DuckDB file-scan function is not inferred. Use
`relation_identifier` and `connection_reference` as the handoff, then verify the
database connection outside DoxaBase.
For database storage, only a storage-access-owned path template is treated as a
relation identifier. Dataset or partition path templates paired with database
storage are review-only inventory cards with
`database_relation_template_source_mismatch`; record the schema/table/relation
on the storage access before using a database handoff. Root-only database
storage without such a template carries `database_relation_template_missing`
even when `location_kind == "object"`.

If `runtime_resolution_required=False` for bare database storage, read the note
before treating it as reachable. The boolean only says there is no recorded
endpoint or credential profile left for DoxaBase to resolve; it is not a
database connectivity guarantee.

Current `handoff_kind` values are `no_query_target`,
`metadata_review_required`, `context_review_required`,
`runtime_resolution_required`, `database_relation_handoff`,
`binding_values_required`, and `execution_attempt_ready`.
