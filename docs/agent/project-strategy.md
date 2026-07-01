# Project Strategy

This doc is for autonomous repo-improvement loops. It is not capsule state, and
it should not be folded into `project_brief`.

`project_brief` answers: what is currently safe, blocked, hidden, or ready in
one DoxaBase capsule?

`project_strategy` answers: after local safety and frontier checks, which
DoxaBase product/workflow priorities should the outer loop deliberately test?

## Strategic Frontier Contract

Use this sequence when working unattended:

1. Run `project_brief` first when a capsule is involved.
2. Clear safety gates before mutation: privacy/export blocks, stale seed
   recovery, incomplete handoff imports, and current staged-revision recovery.
3. Use this doc to choose broader repo-development trial axes instead of
   repeatedly polishing the same local helper family.
4. Do not spend more than a bounded number of consecutive loops on one queue
   family unless it is resolving a coherent blocker or staged/recovery chain.
5. Treat trial reports as product signal even when the right next move is docs,
   response-shape clarification, or a new workflow primitive rather than code.

## Cold Frontier Decision Table

Use this table after `project_brief.first_unattended_action` and any safety
gate have been handled. It maps capsule-local routing hints to the broader
repo-improvement axis to test next; it does not add strategic labels to
`project_brief.queue_counts`.

| `project_brief` signal | Strategic axis | Practical next trial |
| --- | --- | --- |
| `health_tasks[].task_type == "seed_recovery_review"` | `staged_conflict_rebase_versions` | Verify the recovery-complete handoff route; if the current agent cannot write/import the handoff, stop polishing visible query/profile queues and report the recovery gate. |
| `recommended_next_tasks[].task_type == "staged_frontier_review"` or current staged work exists | `staged_conflict_rebase_versions` | Run `plan_staged_revision_recovery`, grouped export/import, or resource-lineage trials before staging new helper output. |
| `recommended_next_tasks[].task_type == "profile_review"` or `profile_queue_counts` shows omitted profile candidates | `profile_metrics_and_joint_writes` | Expand profile candidates when advised, then test profile-to-map, metric/type vocabulary, pattern support, and review-bundle routing. |
| `recommended_next_tasks[].task_type` is `query_context_review`, `query_repair_review`, or `query_plan_handoff` | `storage_aware_query_planning` | Test whether storage/layout/path metadata leads to a reviewed non-secret query handoff, especially when fixture staleness or required bindings are present. |
| `health_tasks[].task_type == "query_fixture_staleness_review"` | `storage_aware_query_planning` | Compare the active capsule with a fresh scratch fixture load before drawing product conclusions from missing storage repairs. |
| `export_preflight` is scanner-clean but `shareability_review_required=true` | Cross-cutting safety | Treat scanner-clean as a review prompt, not export approval; continue only after the intended shareability review is explicit. |

## Current Build Priorities

### staged_conflict_rebase_versions

Goal: agents can recover, rebase, compare, export, import, and apply staged
graph changes after realistic drift without losing rationale or semantic review
context.

Trial axes:

- multi-revision drift with stale, restaged, applied, no-op, and alternative
  candidates;
- handoff between capsules with history plus snapshot rows;
- exact graph-version and resource-lineage inspection before apply;
- review bundles that distinguish mechanical readiness from semantic choice.

Touchpoints:

- `plan_staged_revision_recovery`
- `list_resource_revisions`
- `describe_revision_lineage`
- `describe_graph_version_diff`
- `export_handoff_bundle`
- `export_staged_revisions`

Done signals:

- a cold receiver can choose the next staged action without hidden local state;
- stale and refreshed successors are easy to route at resource level;
- review artifacts make alternatives, no-ops, and validation failures explicit.

### profile_metrics_and_joint_writes

Goal: agents can record profile evidence, distinguish ordinary map drift from
metric/type vocabulary questions, preserve supporting observations and patterns,
and stage only the reviewed current-best map implications.

Trial axes:

- full-scan vs sampled profile evidence;
- repeated profile runs with conflicting scalar values;
- project-specific metric and value-type promotion;
- profile insight review bundles where semantic alternatives are not bulk
  applied just because they are mechanically ready.

Touchpoints:

- `record_profile_bundle`
- `describe_profile_run`
- `draft_profile_map_updates`
- `plan_profile_followthrough`
- `stage_profile_map_updates`
- `stage_pattern_promotion`
- `stage_systematisation`
- `export_profile_insight_review_bundle`

Done signals:

- profile-derived map updates are staged with evidence and route sources;
- metric/type vocabulary work remains reviewable rather than forced into map;
- bundles expose shared support groups and semantic selection risks clearly.

### storage_aware_query_planning

Goal: agents can move from dataset lore to a reviewed, non-secret query handoff
using storage/layout/path metadata, then record external query outcomes as
evidence without pretending DoxaBase executed the query.

Trial axes:

- missing storage access through reviewed repair to a draft query plan;
- database-backed relation identifiers versus object/path templates;
- fixture overlays for AIS and Polymarket;
- query-result and failure recording with source spans and hashes;
- privacy/export preflight around storage paths and generated handoffs.

Touchpoints:

- `describe_query_context`
- `stage_query_storage_access_repair`
- `stage_query_physical_layout_repair`
- `draft_query_plan`
- `record_query_result`
- `export_preflight`
- `describe_context_slice`

Done signals:

- agents do not execute unreviewed or secret-bearing access paths;
- query plans carry relation/path provenance and review gates;
- recorded results link back to query source, scanned source, output, and caveats.

## When To Leave Local Queue Work

Leave a local queue family and run a broader trial when:

- two consecutive loops only improve wording or response shape in the same
  helper family;
- `project_brief` reports no safety blocker and no hidden frontier expansion;
- the last fix did not exercise profile, staged revision, query planning,
  privacy/export, or handoff behavior end to end;
- a workflow remains known only from unit tests and not from a fresh scratch
  trial or sub-agent report.

Do not leave local work when:

- a safety gate blocks mutation or export;
- a staged recovery chain is mid-flight;
- a failing regression needs to be fixed and verified;
- a broad semantic/API direction change would need user review first.

## Cadence

For each wave, pick one or more strategic priorities, run one to three
sub-agent or scripted trials, and ask:

- Could an agent complete the workflow from cold context?
- Did it know which graph role and helper to use?
- Did the response shape expose the next action without prose parsing?
- Did review artifacts preserve semantic alternatives and evidence?
- Did privacy/export and handoff behavior stay safe?

Implement fixes only when the trial exposes concrete workflow friction. Keep
raw scratch capsules local; preserve distilled lessons in tracked docs when
they change how future agents should work.

## Non-Goals

- Do not add these priorities to `project_brief.queue_counts`.
- Do not treat this doc as user capsule data.
- Do not make every loop produce code; a verified "no runtime gap" trial can be
  a useful result when it updates strategy or prevents unsafe automation.
