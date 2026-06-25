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

Then call `draft_query_plan(dataset_iri)` for a non-executed handoff:

1. `scan.uri_template` is for file/object scans.
2. `scan.relation_identifier` and `scan.connection_reference` are for
   database-backed storage handoffs; do not treat the candidate path as a file
   URI in that case.
3. `required_bindings` and `binding_requirements` still need runtime values.
   `ready_for_execution_attempt=True` does not mean DoxaBase has supplied those
   values.
4. `review_gate.executable_without_review` says graph metadata has no recorded
   review blocker for the selected candidate.
5. `storage_environment.runtime_resolution_required` says endpoint, credential,
   region, or equivalent runtime context still needs resolving.
6. `review_gate.ready_for_execution_attempt` is the stricter handoff boolean:
   it is true only when the review gate is clear and runtime resolution is not
   required.
   `review_gate.blocking_reason_codes` can add
   `query_context_has_other_blockers` when the selected candidate is clean but
   the broader query context is not.

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

If `runtime_resolution_required=False` for bare database storage, read the note
before treating it as reachable. The boolean only says there is no recorded
endpoint or credential profile left for DoxaBase to resolve; it is not a
database connectivity guarantee.
