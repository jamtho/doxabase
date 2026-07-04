# Project Strategy

> **SUSPENDED — Distillation Program active.** The build axes below
> (`staged_conflict_rebase_versions`, `profile_metrics_and_joint_writes`,
> `storage_aware_query_planning`) are suspended until the Distillation
> Program in `doxabase_design_docs/07-distillation-program.md` exits. That
> document governs all loop priorities; its Permanent Loop Rules (mirrored
> in `AGENTS.md`) apply to every wave. The material below is retained for
> the post-program resumption decision only.

This doc is for autonomous repo-improvement loops, not capsule state.
`project_brief` answers: what is safe, blocked, or ready in one capsule?
This doc answers: which product/workflow priorities should the outer loop
deliberately test next? Do not add these priorities to `project_brief`
queues, and do not treat this doc as user capsule data.

## The Suspended Build Axes

- **staged_conflict_rebase_versions** — agents can recover, rebase,
  compare, export, import, and apply staged changes after realistic drift
  without losing rationale. Done signals: a cold receiver can choose the
  next staged action without hidden local state; stale/refreshed successors
  route cleanly at resource level; review artifacts make alternatives,
  no-ops, and validation failures explicit.
- **profile_metrics_and_joint_writes** — profile evidence is recorded,
  ordinary map drift is distinguished from metric/type vocabulary
  questions, and only reviewed current-best implications are staged. Done
  signals: profile-derived updates staged with evidence and route sources;
  vocabulary work reviewable rather than forced into map; bundles expose
  semantic selection risks.
- **storage_aware_query_planning** — from dataset lore to a reviewed,
  non-secret query handoff, with external outcomes recorded as evidence.
  Done signals: no unreviewed or secret-bearing access paths; plans carry
  relation/path provenance and review gates; results link back to sources
  and caveats.

## Loop Discipline (Post-Program)

Safety first: clear privacy/export blocks, stale seed recovery, incomplete
handoff imports, and staged-recovery chains before mutation trials. Then
pick a broad axis rather than repeatedly polishing one helper family. Leave
local queue work when consecutive loops only improve wording in the same
family, or when a workflow is known only from unit tests and not from a
fresh scratch trial. Stay local when a gate blocks mutation, a recovery
chain is mid-flight, or a regression needs fixing. Treat trial reports as
product signal even when the right next move is a doc fix or nothing;
scanner-clean exports still require explicit shareability review.
