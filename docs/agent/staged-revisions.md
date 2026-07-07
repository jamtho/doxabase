# Staged Revisions

A staged revision proposes graph changes without mutating the target graph.
Staging is not a demand for proof — it preserves a reviewable trace of a
systematisation move: what would be added or removed, why, how bold the move
is, and whether the previewed graph still validates. The target graph changes
only when `apply_staged_revision` applies one reviewed row.

## Staging

`stage_revision(kind=..., spec={...}, dry_run=...)` is the one staging door.
Kinds: `graph` (arbitrary Turtle patches), `map_assertion` (one map
subject/predicate add/remove/replace with support snapshot and judgement
panel), `systematisation` and `pattern_promotion` (see `systematisation`),
`profile_map_updates` (see `profiling`), `query_storage_access_repair` and
`query_physical_layout_repair` (see `query_planning`), and `review_decision`
(closes a staged row; below). `dry_run=true` runs the read-only planner for
the kinds that have one (`map_assertion`, `profile_map_updates`,
`systematisation` rerun, `query_evidence_overlay`) — same response shape,
nothing written. The `mcp_tools` doc lists each kind's spec fields.

For `kind="graph"`: additions/removals are lists of patch dicts, each
`{"graph": "<role>", "content": "<Turtle>"}`, targeting exactly one mutable
graph role other than `history` (staged metadata itself lands in `history`;
use `record_graph_revision` for durable history notes).
The helper parses the RDF, rejects empty or malformed payloads, previews the
patch in memory, runs SHACL over the preview scope, and records the staged
row. Set `stance` to describe the thinking: `rc:ExploratoryHunch`,
`rc:CandidateRevision`, `rc:ConservativeCleanup`,
`rc:AlternativeSystematisation`, `rc:SupersededRevision`. Rationale can be
candid — "this framing should generalise better" is a fine rationale.

For a single existing map assertion, prefer `kind="map_assertion"`: it calls
assertion support itself, generates the patch, and returns a judgement panel
(current/proposed values, semantic risk, reasons the current value may be
intentional, caveat scopes, impacts). Draft first with `dry_run=true` when
you are still deciding whether the change should exist.

## Inspecting

- `describe_revision(iri)` auto-detects staged rows and returns patch
  payloads, stance, validation diagnostics, support links, count previews,
  and impact context. `include_current_apply_check=true` adds the live
  ready/conflict/validation branch beside the payload. Impacts are a
  spotlight, not a judge.
- `describe_revision(iri, aspect="lineage")` gives the staged/applied
  pairing, restage chain, alternatives, and next route without payloads —
  the right first call when you hold one IRI cold.
- `list_revisions(kind="graph", current_staged_work_only=true,
  include_apply_checks=true)` is the live mutation-review queue: stale
  originals with successors and staged sources with applied events are
  excluded as current work but kept as history.
- `search(query=..., scope="staged_patches")` finds staged-only prose,
  proposed ontology labels, or IRI local names inside stored patch payloads
  when you remember words but not the revision IRI. If a remembered proposal
  IRI describes as empty, check staged payloads before concluding it is
  absent — proposed resources materialize only on apply.

## Checking And Applying

`apply_staged_revision(iri, dry_run=true)` is the read-only apply check;
it is free and names conflicts exactly. Statuses:

- `ready` — replays and validates against the current graph. Ready means
  mechanically ready; semantic review is still yours (and the check says so
  when linked support or alternatives raise semantic risk).
- `noop` — the replay validates but would change nothing; inspect rather
  than apply, unless the no-op event is exactly what you intend.
- `already_applied` — inspect the applied event; never replay.
- `superseded_by_restage` — a refreshed successor exists; work with it.
- `conflict` (`target_count_drift` / `target_digest_drift`) — the target
  graph is no longer the state the proposal was previewed against. Drift
  checks are deliberately conservative: an unrelated write elsewhere in the
  same graph stales the proposal. Snapshot drift rows carry the exact
  added/removed triples since staging plus overlap hints; "no patch subject
  overlap" means probably unrelated, not safe-to-force.
- `validation_failed` — the replay fails SHACL now; inspect
  `validation_results` and stage a repaired or alternative candidate rather
  than restaging the same payload.
- `patch_conflict` — the stored patch itself cannot replay (malformed
  Turtle, bad target); repair, do not restage.

`apply_staged_revision(iri)` applies after the same checks: it refuses
already-applied rows, compares recorded before-counts, previews and
revalidates in memory, mutates only after those pass, and records an applied
event linked back to the staged source. The response's post-apply recheck
list is only the affected-sibling subset — one apply can stale independent
siblings, so rerun the recovery planner before the next mutation instead of
trusting any pre-apply queue.

## Drift Recovery

- **Unrelated count/digest drift** → `restage_staged_revision(iri)` copies
  the stale proposal into a fresh staged revision against current graph
  state (recording the restage provenance chain), then check and apply the
  successor. Pass a list of IRIs for the batch path, which classifies each
  row, skips already-handled and non-conflicted rows, and can write a
  grouped review bundle via `path`. `dry_run=true` first: with one IRI it
  returns the read-only rebase draft (which can convert recognizable
  same-slot conflicts into a reviewed replacement action); with a list, the
  would-restage classification. Feed only the would-restage list into a real
  batch.
- **Same-slot semantic drift** (the current graph now asserts a different
  value in the slot the patch writes) → mechanical restage is refused;
  follow the rebase draft's replacement route — typically
  `stage_revision(kind="map_assertion")` with `restages_revision` set so the
  replacement supersedes the stale source.
- **Already-effective stale rows** (drift present, but every patch triple
  already holds) → informational; do not apply, do not restage. When review
  confirms such a row should stop returning to the frontier, close it with
  `stage_revision(kind="review_decision", spec={"revision_iri": ...,
  "decision": "no_effective_change", ...})` — a history-only resolution that
  removes it from current-work queues without deleting anything.

## Recovery Planning

For mixed or multi-row queues, `plan_staged_revision_recovery()` is the
read-only planner: it discovers current staged work (or takes explicit
`revision_iris`), classifies every row into lanes, and returns the mutation
frontier — deduped apply/restage targets plus helper actions for repair
lanes that have no successor yet. The loop it expects:

1. Plan (`current_staged_work_only=true`). If the plan says handoff
   preflight imports are required first, run those and replan.
2. Review the lanes. Mechanical restage only for the would-restage list;
   repair-or-replace and informational rows stay out of bulk operations.
3. Batch-restage dry-run, then the real restage over the same list.
4. Check one successor, apply at most one ready row after review.
5. Replan before the next mutation.

Rows that are alternatives to already-applied work stay semantic-review-gated
even when mechanically ready — the planner and queue items flag this; do not
apply them unattended. For work spanning several calls or an imported
handoff, persist the plan: `start_session=true` creates a durable recovery
session (with `summary`, `handoff_manifest_path`, `created_*`); later calls
with `session_iri=...` describe that session with a live replan, so
continuation does not depend on local notes. `project_brief` foregrounds an
overlapping session while current staged work remains.

## Review Bundles

`export_bundle(kind="staged_revisions", spec={"revision_iris": ...,
"path": ...})` writes the Markdown review bundle — one IRI string for a
single-revision bundle, a list for the grouped comparison (grouped-only:
`title`, `executive_summary`). Bundles embed the live apply check at export
time, a reviewer decision matrix, restage/alternative context, modelling-
choice rows, and linked support. Choose-one alternative groups are labelled:
apply at most one member, then regenerate. Staged Markdown can be dirty even
when the patch is clean (drift summaries render current graph terms), so
keep `fail_on_sensitive: true` for unattended or shareable exports, and
remember the export record's shareability-review flag: scanner-clean is not
approval. Grouped exports take staged patch IRIs; pass an applied event's
staged source, not the event itself.

Python API note: the library keeps `db.stage_graph_revision`,
`db.check_staged_revision_apply` (the MCP check is
`apply_staged_revision(dry_run=true)`), `db.restage_staged_revisions`,
`db.draft_staged_revision_rebase`,
`db.record_staged_revision_review_decision`, and
`db.start_staged_revision_recovery_session` /
`db.describe_staged_revision_recovery_session` (the MCP doors are
`plan_staged_revision_recovery(start_session=true)` / `(session_iri=...)`).
