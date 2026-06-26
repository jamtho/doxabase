# Staged Revisions

Use staged revisions when an agent wants to propose graph changes without
mutating the durable project map, ontology, observations, patterns, evidence, or
shapes yet.

Staging is not a demand for proof. It is a way to preserve a reviewable trace of
the agent's systematisation move: what it wants to add or remove, why that move
might be useful, how bold or conservative the move is, and whether the previewed
graph still validates.

## Stance

Set `stance` to describe the kind of thinking being captured:

- `rc:ExploratoryHunch`: a strong gestalt or promising framing that may not yet
  have tidy proof.
- `rc:CandidateRevision`: a proposal that seems ready for review as a graph
  change.
- `rc:ConservativeCleanup`: a mostly mechanical consistency or clarity change.
- `rc:AlternativeSystematisation`: one plausible framing among several.
- `rc:SupersededRevision`: a staged idea kept for memory but no longer preferred.

Rationale can be candid. It is fine to say that a proposed systematisation feels
more robust, explains more observed mess, or should generalise better under
future data, even if the evidence is not courtroom-grade.

## Tool Flow

Call `doxabase.stage_graph_revision` with Turtle payloads grouped as additions
and removals:

```python
result = stage_graph_revision_tool(
    db,
    summary="Treat messages as the map anchor",
    rationale=(
        "Exploratory hunch: this framing should make later joins easier to "
        "reason about as more message-like datasets arrive."
    ),
    stance="rc:ExploratoryHunch",
    additions=[
        {
            "graph": "map",
            "format": "turtle",
            "content": """
                @prefix ex: <https://example.test/project#> .
                @prefix rc: <https://richcanopy.org/ns/rc#> .
                @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                ex:Messages a rc:Dataset, rc:Table ;
                    rdfs:label "Messages" .
            """,
        }
    ],
    validation_scope="all",
)
```

For table row grain, `rc:rowSemantics` is controlled vocabulary, not prose.
Use one of `rc:EventRow`, `rc:SnapshotRow`, `rc:AggregateRow`, or
`rc:DimensionRow`, and put row-grain explanation in `rdfs:comment`,
description, caveats, observations, or patterns:

```turtle
@prefix ex: <https://example.test/project#> .
@prefix rc: <https://richcanopy.org/ns/rc#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:Orders a rc:Dataset, rc:Table ;
    rdfs:label "Orders" ;
    rdfs:comment "One row per order event in the source system." ;
    rc:rowSemantics rc:EventRow ;
    rc:schemaStability rc:FixedSchema .
```

For a single `map` subject/predicate assertion, prefer
`doxabase.stage_map_assertion_change`. It calls `describe_assertion_support`,
generates the Turtle patch payloads, links related lore and anchors, and returns
the normal staged revision record alongside the support snapshot and a compact
`judgement_panel`. Read the panel first when deciding whether a single assertion
change is plausible: it brings current/proposed values, value-type context,
semantic risk level/reasons, reasons the current value may be intentional,
caveat scopes, strongest routes, impact entries, and safety notes into one
place. Use generic
`stage_graph_revision` when the patch is multi-resource, multi-graph, or cannot
be expressed as one assertion add/remove/replace.

Each patch must target one mutable graph role other than `history`. Staged
revision metadata is itself recorded in `history`, so a staged patch cannot use
`history` as its target graph; use `record_graph_revision` for durable history
notes. The helper parses the RDF, rejects empty or malformed payloads, previews
additions/removals in memory, runs SHACL validation over the preview scope, and
records staged metadata in `history`.

The target graph is not changed when a revision is staged. Staged revisions are
review objects until `doxabase.apply_staged_revision` applies one.

Use `doxabase.describe_staged_revision` to inspect patch payloads, stance,
validation status, structured validation result diagnostics, support links, and
before/after count previews. For simple single-assertion `map` changes that
still replay cleanly, it also returns `judgement_panel`, the same compact review
surface used by `stage_map_assertion_change`. It also returns `impacts`:
deterministic review context for consequences such as caveat removals,
physical/value type changes, row-semantics changes, grouping changes, and
layout/path changes. Treat impacts as a spotlight, not a judge. They exist to
show linked observations, claims,
patterns, evidence, and revisions that may explain why a map assertion or caveat
was there. They do not make the proposal invalid by themselves.
Pass `include_current_apply_check=True` when reviewing one staged revision cold
and you want its live `ready`, `conflict`, `validation_failed`, `noop`, or
`already_applied` branch beside the patch payload. The embedded summary omits
full patch checks and validation result payloads; call
`check_staged_revision_apply` for those diagnostics.

Use `doxabase.export_staged_revision` to write a Markdown review bundle for one
proposal. The export includes a live `Current Apply Check` section generated at
export time, so stale proposals carry their current conflict status, count or
digest drift, validation-skipped reason, and suggested next calls in the review
artifact itself. For simple single-assertion `map` changes that still replay
cleanly, the export may include a `Semantic Review Warning` before the apply
check, and also includes a `Judgement Panel` section so human and agent
reviewers can see the same compact values, value-type context, caveats, routes,
and safety notes that the JSON helper returned. Stale single-assertion exports
can still include a `Semantic Review Warning` reconstructed from the live apply
check even when the judgement panel is unavailable. `can_apply=True` means replay
and validation readiness, not semantic approval. Restaged single exports include
a top metadata `Restage headline` before the current apply check, so reviewers
can see why the stale proposal was refreshed before reading patch payloads.
Stale original exports include a top metadata `Restaged by` line when a
refreshed successor already exists. Use
`doxabase.export_staged_revisions` when
several alternatives, failed candidates, and repaired candidates should be
reviewed together; its summary table includes the current apply status and
decision, plus current and staged-time validation state for each staged
revision. When the bundle contains restaged revisions, a `Restage Context`
section appears near the top before the detailed revision bodies. When an
alternative points to a stale revision whose successor is also in play, an
`Alternative Context` section names the current successor to compare against.

A stale export should be read like this:

```text
## Current Apply Check

- Status: conflict
- Decision: restage_against_current_graph
- Mechanically can apply: False
- Blocking reasons: target_count_drift
- Validation skipped: conflicts_present

### Count Drift
...

### Snapshot Drift
...

### Suggested Next Calls
- **Review stale source:** describe_staged_revision(...)
- **Export conflict bundle:** export_staged_revision(...)
- **Restage stale source:** restage_staged_revision(...)
```

For larger stale sets, use `doxabase.restage_staged_revisions(...)` instead of
looping manually. It restages conflicted rows that do not already have a
successor, skips already-handled or non-conflicted rows, preserves caller order,
returns source-to-current mappings, and can write the grouped review bundle when
you pass `path`. Use `dry_run=true` first when you want the same per-source
classification without creating refreshed successors; unhandled conflicts report
`action="would_restage"`. Treat `restaged_revision_iris` as a list of successors
created during that run, not as an apply queue. Each item's `status_after`,
`decision_after`, `stale_resolution_state_after`, and `blocking_reasons_after`
describe `current_revision_iri` after the batch decision; use
`next_action_after` and `suggested_next_actions_after` for the concrete
post-batch route, then use `check_staged_revision_apply()` before each apply.
After any successful apply,
discard old grouped readiness and re-check or regenerate the bundle before
touching remaining candidates. In a mixed batch, a created successor can be
no-op or validation-failed; keep those out of the apply path and route by
`bundle_summary.next_action_queue` plus the item's `next_action_after`. If a
skipped already-handled row reports
`stale_resolution_state_after="restaged_successor_stale_unresolved"`, the
current successor is stale too; inspect or restage `current_revision_iri`.
If a current or freshly restaged successor reports
`status_after="validation_failed"`, do not restage the same patch again hoping
for semantic repair. Inspect `validation_results`, then stage a repaired or
alternative candidate. For overlapping single-assertion cases, the repair is
usually a removal+addition patch or a `stage_map_assertion_change` replacement
that explicitly replaces the now-current assertion.
If a row was validation-failed at staging time and later becomes stale, the
first dry-run may route it as count/digest drift because the current graph no
longer matches the staged snapshot. Restage or inspect the refreshed successor
before assuming there is no repair work; validation failures can reappear after
the patch is replayed against the current graph.
Grouped exports keep handled stale rows in the summary for provenance, but their
effective `summary_recommendation` redirects to the refreshed successor.
Structured consumers should follow `active_recommendation_field`, and treat
`apply_recommended_resolution` as prior/source context when
`apply_recommendation_scope="prior_source_apply_check_context"`. Restage
Context lines for successors describe prior/source apply-check context, not
necessarily the successor's current status.
In mixed recovery queues, a dry-run can legitimately classify an already-handled
stale source as skipped and classify its ready successor as not restageable with
reason `ready`. That does not mean there is no next action. Read
`current_revision_by_source`, `bundle_summary.ready_restage_successor_revision_iris`,
and the grouped export's apply/repair review queues to find the active successor
to review or the remaining patch-conflict candidate to repair.
After applying one ready alternative, sibling alternatives may become stale or
conflicted because the applied candidate changed the same graph roles. Preserve
their original staged validation diagnostics in your review: a stale live check
explains current replay state, while the staged diagnostic can still explain the
semantic repair that made the sibling useful to keep.

### Grouped Review Recipe

Use this shape when several staged revisions touch the same graph and some of
them may be stale:

| Check result | Usual next move |
| --- | --- |
| `ready` | Review/export, apply at most one, then regenerate checks before siblings. |
| `target_count_drift` or `target_digest_drift` | Review/export the conflict, then restage against current graph state. |
| `patch_conflict` | Inspect patch diagnostics or export; stage a repaired or alternative proposal. |
| `validation_failed` | Inspect `validation_results`; stage a repaired or alternative proposal. For overlapping single assertions, prefer removal+addition or `stage_map_assertion_change` replacement over another restage. |
| `noop` | Inspect/export; do not apply unless the no-op is exactly the intended durable event. |
| `already_applied` | Inspect the applied event and staged source; do not replay it. |

For scratch trials that need a disposable capsule path, use the Python helpers.
The MCP server tools operate on the configured server capsule; a local
`DoxaBase.create(...)` gives a trial its own temporary store.

```python
from doxabase import DoxaBase
from doxabase.mcp_tools import (
    apply_staged_revision_tool,
    check_staged_revision_apply_tool,
    record_map_dataset_tool,
    restage_staged_revisions_tool,
    stage_graph_revision_tool,
)

db = DoxaBase.create("/tmp/doxabase-staged-recovery.sqlite", overwrite=True)
record_map_dataset_tool(
    db,
    iri="https://example.test/project#Seed",
    label="Seed",
    is_table=True,
)

first = stage_graph_revision_tool(
    db,
    summary="Add orders table",
    rationale="Candidate map addition for recovery workflow testing.",
    additions=[
        {
            "graph": "map",
            "format": "turtle",
            "content": """
                @prefix ex: <https://example.test/project#> .
                @prefix rc: <https://richcanopy.org/ns/rc#> .
                @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                ex:Orders a rc:Dataset, rc:Table ;
                    rdfs:label "Orders" .
            """,
        }
    ],
)
second = stage_graph_revision_tool(
    db,
    summary="Add order lifecycle table",
    rationale="Sibling candidate that must be rechecked after any apply.",
    additions=[
        {
            "graph": "map",
            "format": "turtle",
            "content": """
                @prefix ex: <https://example.test/project#> .
                @prefix rc: <https://richcanopy.org/ns/rc#> .
                @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                ex:OrderLifecycle a rc:Dataset, rc:Table ;
                    rdfs:label "Order lifecycle" .
            """,
        }
    ],
)

# Create unrelated drift so the staged rows need review/restage.
record_map_dataset_tool(
    db,
    iri="https://example.test/project#DriftDataset",
    label="Drift dataset",
)

sources = [first["revision_iri"], second["revision_iri"]]
dry = restage_staged_revisions_tool(db, revision_iris=sources, dry_run=True)
assert dry["would_restage_revision_iris"] == sources

batch = restage_staged_revisions_tool(
    db,
    revision_iris=sources,
    path="/tmp/doxabase-staged-recovery-review.md",
    overwrite=True,
)

first_current = batch["current_revision_by_source"][first["revision_iri"]]
check_staged_revision_apply_tool(db, iri=first_current)
apply_staged_revision_tool(db, iri=first_current)

# Applying one successor can make the sibling successor stale.
second_current = batch["current_revision_by_source"][second["revision_iri"]]
check_staged_revision_apply_tool(db, iri=second_current)
```

In grouped exports, `Staged validation` is the validation result from when the
proposal was created. `Current validation` comes from the live apply check and
may say `skipped: conflicts_present` when count or digest drift prevents a
replay. Prefer the current apply status when deciding what to do next.
Validation cells include their result count when available, for example
`True (0 result(s))`.

## Systematisation Drafts

Call `doxabase.stage_systematisation` when you have a modelling hunch and want
to preserve one or more possible RDF framings for it. This helper is deliberately
not a promotion wizard. It does not choose the ontology shape for you; it packages
caller-authored RDF framings as staged revisions, validates them, and links later
framings as alternatives to the first by default. When several framings need the
same provisional vocabulary or assumptions, pass `shared_additions` or
`shared_removals`; those shared patches are included in each framing preview and
exported as `rc:SharedContextPatch` entries. Shared patches can target
`ontology`, `shapes`, or other mutable graph roles. Staged `shapes` patches
participate in the preview SHACL validation for each framing.

Use it for the part of the work where graph judgement matters:

- a pattern-first framing versus an ontology-first framing;
- a bold hunch that needs a new project vocabulary term;
- several plausible map shapes where one feels more robust but the reason is not
  yet fully mechanical;
- a conservative candidate plus a more speculative alternative.

Each framing can use the shorthand `graph` + `content` for one addition, or full
`additions` / `removals` patch lists when the graph move is more complex.
Add `review_note` and `review_recommendation` when the comparison itself needs
human-readable judgement, for example "preferred for now", "too bold but
informative", or "keep as a concrete alternative". These fields are not proof
and they do not apply the revision by themselves; they are review cues preserved
with the staged proposal.
Shared context patches are previewed before each framing's own patches:

```python
result = stage_systematisation_tool(
    db,
    summary="Explore identity-ladder modelling",
    intent=(
        "Keep two RDF framings alive while deciding whether this belongs in "
        "project vocabulary or as a pattern first."
    ),
    anchors=["ex:Messages", "ex:observation-123"],
    rationale=(
        "The concept may explain repeated identity hints better than a single "
        "fixed key model."
    ),
    shared_context_summary=(
        "Define provisional identity-ladder vocabulary so multiple framings can "
        "refer to the same tentative concept."
    ),
    shared_additions=[
        {
            "graph": "ontology",
            "content": "... Turtle defining ex:IdentityLadder ...",
        },
    ],
    framings=[
        {
            "label": "Deeper pattern hunch",
            "graph": "patterns",
            "content": "... Turtle defining an rc:Pattern ...",
            "review_note": "Keeps the strong hunch alive without forcing the map.",
            "review_recommendation": "Preferred for now.",
        },
        {
            "label": "Concrete map candidate",
            "graph": "map",
            "content": "... Turtle using the shared vocabulary ...",
            "stance": "rc:CandidateRevision",
            "review_recommendation": "Useful alternative, but wait for more support.",
        },
    ],
    validation_scope="all",
)
```

After staging several framings, export them together for review:

```python
db.export_staged_revisions(
    [revision.revision_iri for revision in result.staged_revisions],
    "/tmp/systematisation-review.md",
    title="Identity ladder alternatives",
    executive_summary=(
        "Prefer the pattern-first framing for now, while keeping the map "
        "candidate as useful pressure on the model."
    ),
)
```

The staged revision rationale records the systematisation intent, anchors,
overall rationale, shared-context summary, and framing-specific rationale. The
grouped export also surfaces review notes, recommendations, and diagnostic
headlines in its top sections so a reviewer can understand the semantic delta
without reading every Turtle payload first.

Systematisation anchors are also recorded as `rc:revisionAnchor` triples on each
staged revision. Use anchors for resources the hunch is about, such as columns,
tables, caveats, relationships, observations, or patterns. Do not use anchors as
a substitute for evidence: supporting observations, claims, patterns, and
evidence links still carry the justification for the proposal.

## Pattern-Supported Promotion

Call `doxabase.stage_pattern_promotion` when one or more existing patterns are
the reason a graph change now seems worth staging. This is a pattern-aware
wrapper over `stage_systematisation`, not an automatic map editor. Pass the
pattern IRIs and caller-authored framings. The helper:

- records the selected patterns as `supporting_patterns`;
- rolls up their supporting observations, claims, and evidence into revision
  metadata;
- uses the pattern IRIs, pattern targets, and `rc:mapImplication` resources as
  revision anchors;
- delegates patch parsing, preview counts, validation, alternatives, and review
  notes to the ordinary staged systematisation flow.

Use it when a pattern supports a caveat, relationship, project vocabulary term,
shape, or other durable structure but the exact graph move still deserves review.

## Applying Staged Revisions

Use `doxabase.apply_staged_revision` after reviewing a staged revision and
deciding it should become durable graph state. The helper is intentionally
conservative:

- it rejects a staged revision that already has an applied-revision event;
- it checks patches in recorded `patchSequence` order and compares each target
  graph count against the recorded `beforeTripleCount`;
- it previews all patches in memory and reruns validation before mutating graph
  state;
- it applies additions/removals only after those checks pass;
- it records an `rc:AppliedStagedRevision` history event linked back with
  `rc:appliesStagedRevision`;
- it returns `post_apply_recheck_revision_iris` and
  `post_apply_recheck_revisions` for other current staged revisions sharing
  changed graphs that should be rechecked before any further apply.

After an apply, treat `post_apply_recheck_revisions` as the affected-sibling
queue for the mutation that just happened. For each row, inspect
`shared_changed_graphs`, then use the row's fresh `application_status`,
`next_action`, `suggested_next_actions`, and `suggested_next_calls` to route the
next step. Re-run `check_staged_revision_apply` before mutating if substantial
time has passed or other graph changes have happened. The queue is a recheck
cue, not permission to apply the siblings.

After application, `describe_graph_revision()` on the applied event exposes
`applies_staged_revision`, and `describe_staged_revision()` on the staged source
exposes `applied_by` plus `application_status="already_applied"`.

Use `doxabase.check_staged_revision_apply` first when you want a read-only
answer. It reports whether the staged revision has already been applied, whether
any patch target graph has drifted from its recorded `beforeTripleCount` or
staging-time graph digest, the preview count for each patch, preview validation
diagnostics, `status`, `summary`, and structured `suggested_next_actions`. Read
`status` and `summary` first. Current statuses are `ready`, `noop`,
`already_applied`, `superseded_by_restage`, `conflict`,
`validation_failed`, and `not_ready`. `decision`
is the compact branch hint: `review_then_apply`,
`inspect_no_effective_change`, `inspect_applied_revision`,
`inspect_current_successor`,
`restage_against_current_graph`, `inspect_patch_conflict`,
`inspect_validation_results`, or
`inspect_staged_revision`. `review_recommended=True` means the staged revision
needs review before the next mutation. On `ready` checks that means review
before application; on count/digest-drift `conflict` checks that means review
before restaging; on `patch_conflict` checks that means inspect/export before
staging a repaired or alternative candidate. When a ready check has
`semantic_risk_level` of `attention` or `high`, the apply action is labelled
`Apply only after semantic review`. Conflict review actions include
`include_current_apply_check=True` so the next inspection reloads the current
blocked status.
Use `blocking_reasons` and `recommended_resolution` to distinguish count drift,
digest drift, validation failure, and already-applied state. When
`validation_conforms` is `None`, `validation_skipped_reason` explains why
validation did not run.
`noop` uses `no_effective_patch_triples` and means the patch replay validates
but would not change graph triples, usually because another path already
realized the proposed addition or removal. Inspect/export or stage a replacement
instead of applying it. `triples_to_add` and `triples_to_remove` are effective
current-preview deltas; `patch_checks` also reports effective add/remove counts
and already-present/absent payload triples.
If `blocking_reasons` contains `patch_conflict`, the stored patch itself could
not be replayed. Inspect `patch_checks[].conflict` and export the staged
revision before mutating. Common causes are malformed stored patch Turtle or a
stored target graph that is not exactly one concrete mutable graph role.
Ordinary restaging is for count/digest drift and may not repair these cases, so
stage a repaired or alternative candidate when the graph intent is still useful.
`count_drifts` gives expected/current graph counts and deltas for count drift.
It can also say whether the staged patch triples themselves are currently
present, absent, or mixed in the target graph. When stored snapshot rows are
available, `snapshot_drifts` carries the exact target graph triples added and
removed since staging, plus a conservative `drift_relevance` hint and any
patch-subject, patch-predicate, patch-object, or revision-anchor overlaps.
Revision-list summary rows keep those relevance and overlap fields, plus
added/removed exact-change counts, while omitting the actual changed-triple
arrays unless `drift_detail="exact"` is requested.
Treat `no_patch_subject_overlap` as "probably unrelated but still stale", not
as permission to apply without review. Predicate and object overlap can be
broad; `broad_patch_object_overlap` is the weak object-overlap label for shared
class/type vocabulary such as `rc:Dataset`. Anchor overlap means the drift
touched a resource the staged revision named as review context. Older revisions can still report
`exact_changed_triples_available=False` if they were recorded before snapshot
row storage existed. `snapshot_drifts` also gives staged/current graph content
digests and stored graph counts for digest drift, including same-count graph
changes. Markdown exports show compact display values in the exact-drift tables;
use the API payload's raw fields when a follow-up graph edit needs exact RDF
terms.
Suggested actions are ordered review-first; apply or restage calls come after
inspection/export suggestions. If stale drift has count/digest evidence but
`exact_changed_triples_available=False`, the suggested actions can include
`import_revision_snapshots` before restage; follow that action when a companion
snapshot JSON bundle is available so drift relevance can be classified with
exact triples.

This is not a full merge system. A harmless unrelated graph change can still
show up as a conflict because the guards compare staged graph state with current
graph state. In that case, call `doxabase.restage_staged_revision` to copy the
stale proposal into a fresh staged revision with current before/after counts and
graph snapshots, then review and check the new revision before applying. The
refreshed revision records `rc:restagesRevision` back to the stale proposal, and
its generated rationale summarizes the stale apply check, including exact
snapshot drift triples when available. `describe_staged_revision` also surfaces
a compact `restage_reason` when it can derive one from that rationale, and
`restaged_by` on the stale source when a refreshed successor exists. If a
restage chain grows deeper, `current_restaged_by` points to the latest known
successor while direct `restaged_by` keeps the immediate provenance edge. The
single-restage helper refuses to create a parallel successor for a stale source
that already has one; inspect or restage `current_restaged_by` instead.
Markdown exports surface that same reason as a top `Restage headline`; stale
original exports surface `Restaged by` and, when needed, `Current restaged by`.
Grouped exports collect restage reasons in `Restage Context`. Grouped export
payloads also include per-row `stale_resolution_state`, `current_alternative_to`,
`current_restaged_by`, and a `bundle_summary` so recovery scripts can find
unresolved stale proposals, already-handled stale sources, ready successors,
validation-failed rows, the current mutation-review set, and already-applied
inspection set without recomputing those buckets. Prefer
`bundle_summary.next_action_queue` when routing autonomous work; it groups rows
by derived next action (`apply_after_review`, `restage_after_review`,
`repair_or_replace`, `inspect_already_applied`, and `informational`) without
requiring the agent to join status, stale state, and recommendation fields.
That queue describes current mechanics, not all staged-time semantics. When a
row has `staged_validation_conforms=False` or a failed
`staged_validation_status`, preserve that repair signal even if the live apply
check now reports count or digest drift.
Grouped Markdown mirrors the important `current_alternative_to` case in
`Alternative Context` when a stored alternative target has been restaged.
Restaging is for count or digest drift conflicts; validation failures still need
graph repair, and their suggested actions now point agents toward structured
diagnostics plus a Markdown review export before staging a repaired candidate.
When the original intent is still live but the payload itself needs a
caller-authored repair or rebase, stage the repaired patch with
`restages_revision=<stale_revision_iri>` through `stage_graph_revision` or
`stage_map_assertion_change`. That records the same `rc:restagesRevision`
provenance without replaying the old payload. Use `alternative_to` only for a
competing framing, not for a repaired successor to stale work. If the stale
source already has `restaged_by` / `current_restaged_by`, target the current
successor; parallel repaired successors are rejected for the same reason
parallel mechanical restages are rejected.
If a caller-authored successor supersedes a source that would otherwise still
replay cleanly, direct apply checks on the source return
`status="superseded_by_restage"`, `can_apply=False`, and an
inspect-current-successor action. Apply the current successor after review, not
the old source.
Already-applied revisions should be inspected rather than replayed.
Batch restage is also review-first: it prepares refreshed staged revisions and a
bundle summary, but applying remains an explicit separate step because applying
one staged revision can make sibling ready/no-op revisions on the same changed
graph stale. Grouped bundle summaries put that sequencing hazard in `warnings`
and `sequential_apply_recheck_candidate_iris`; `post_apply_recheck_revision_iris`
is the same list under its older compatibility name. Both are pre-apply
grouped-review hazard lists. After the actual mutation, prefer the
`post_apply_recheck_revisions` returned by `apply_staged_revision`, then re-run
`check_staged_revision_apply` or `export_staged_revisions` before acting on
siblings. The recheck list can include repair-only rows such as patch conflicts
or validation failures when they share changed graphs, so route by the fresh
check/export `next_action_queue` rather than by the recheck list alone. In
scripts, the practical loop is: batch restage, review
`ready_restage_successor_revision_iris`, apply at most one ready successor,
then feed `apply_staged_revision().post_apply_recheck_revision_iris` into the
next check/export/restage pass.
Grouped Markdown also includes a `Review Queues` section that mirrors the
derived next-action buckets plus the compatibility apply/restage, repair,
applied-inspection, and post-apply recheck buckets from `bundle_summary`.
When a requested stale source already has a restage chain, batch restage maps it
to `current_restaged_by` so the review bundle opens the latest known successor.
The summary also keeps
`recommended_apply_or_restage_review_iris` separate from
`recommended_repair_review_iris` while preserving
`recommended_mutation_review_iris` as the broad compatibility review queue.
Rows skipped as
`skipped_not_restageable` carry `not_restageable_reason`, and the batch-level
`not_restageable_revision_iris_by_reason` groups ready, already-applied,
validation-failed, and `patch_conflict` skips for quick triage. Use
`dry_run=true` when an autonomous loop wants to inspect which rows would be
refreshed before taking the mutation.

## What Gets Recorded

Staged revisions are `rc:GraphRevision` resources with `rc:StagedRevision` type,
optional support links to observations, claims, patterns, and evidence, optional
`rc:revisionAnchor` topical links, optional linked `sh:ValidationResult`
diagnostics, plus one or more `rc:GraphPatch` resources.
Each graph snapshot records the graph role, triple count, and `content_digest`
for the graph state at staging time. Apply checks compare those digests when
available, so same-count graph changes can still surface as conflicts.
For scratch trials or controlled graph maintenance that intentionally needs a
same-count digest drift, use `replace_graph_triples()` /
`doxabase.replace_graph_triples` with `expected_count` and the default
`allow_count_change=false`. That avoids staging and applying a throwaway helper
revision or exporting, RDFLib-editing, and re-importing the whole graph. The
helper returns the effective added/removed triple counts and graph digests, but
ordinary history records do not reconstruct exact replacement triples by
themselves. If exact changed triples matter later, keep before/after exports,
record the replacement result in revision rationale/metadata, or rely on a
staged snapshot/apply-check that captured the earlier graph state.

Patch entries record:

- `rc:patchOperation`: addition or removal;
- `rc:targetGraph`: the mutable graph role;
- `rc:patchFormat` and `rc:patchContent`;
- `rc:patchRole`: `rc:SharedContextPatch` or `rc:FramingPatch`;
- `rc:patchSequence`: one-based preview/check/apply order;
- `rc:patchTripleCount`;
- `rc:beforeTripleCount` and `rc:afterTripleCount` for the preview sequence.

Use `alternative_to` when recording competing staged systematisations. Keeping
alternatives side by side is expected; staged revisions are cheap memory for
creative exploration, not a forced march toward one approved answer.

Use `restaged_from` / `rc:restagesRevision` when a staged revision is the same
patch intent replayed against a newer graph state, or when a caller-authored
repair intentionally supersedes a stale staged payload. This is different from
`alternative_to`: alternatives compete as different framings, while restaging
keeps the older stale proposal as provenance for the refreshed proposal.
`restaged_by` is the reverse relation on the stale source revision.
`restage_reason` is the quick review headline and appears early in Markdown
exports; read the full rationale when the drift evidence matters.

## Validation Notes

DoxaBase runs pySHACL with RDFS inference during preview validation. That is
usually helpful because ordinary RDF vocabulary such as `rdfs:range` can teach
the validator useful class context. It also means a shape using `sh:class` may
pass because the class was inferred rather than explicitly written. When a trial
needs a stricter check, add shape constraints for the concrete property,
node-kind, count, or value that should be present.

When validation fails, staged revisions preserve structured SHACL diagnostics in
`validation_results`. Read these before guessing from patch text. Each result
can include focus node, result path, source constraint component, severity,
value, and one or more messages. Markdown staged-revision exports include the
same diagnostics before the patch payloads. In API and MCP JSON, these
diagnostics are always exposed as `validation_results`; prose that says
"diagnostics" and Markdown sections titled `Validation Results` refer to the
same SHACL result records.

## Repair Loop Example

A useful staged-validation loop is:

1. Record the lore first as observations, claims, or patterns.
2. Stage shared provisional ontology and shapes for the hunch.
3. Let a candidate fail if it is incomplete.
4. Inspect `describe_staged_revision(...).validation_results`.
5. Stage a repaired candidate using the diagnostic focus node, result path, and
   message.
6. Keep a pattern-first or bolder alternative if the deeper hunch should not be
   collapsed into the conservative map candidate.

For example, a Polymarket trial treated `outcomes` and `clobTokenIds` as
parallel JSON arrays that bridge Gamma market snapshots to scalar CLOB token
identifiers. The agent first recorded claims and a pattern saying this was a
positional array bridge, not a plain foreign key. It then staged shared
provisional vocabulary and a shape requiring each `OutcomeTokenAlignment` to
name the market table, condition column, outcome-label array column, CLOB
token-id array column, downstream token columns, and alignment basis.

The first map candidate intentionally omitted the token-id array column. Its
staged revision failed with a diagnostic like:

```text
focus_node: ft:outcome_token_alignment_v1
result_path: ft:clobTokenIdArrayColumn
constraint: sh:MinCountConstraintComponent
message: Outcome token alignments must name the CLOB token-id array column.
```

The repair was then a graph move rather than guesswork: add
`ft:clobTokenIdArrayColumn pm:mkt_clob_token_ids` to that same focus node and
stage a new candidate. A third framing kept the more conceptual hunch alive as
a pattern-first latent outcome-slot model. This is the intended feel of the
workflow: validation is a guide for graph repair, while alternatives preserve
creative modelling space.

## Awkward Concept Test

Promotion helpers should be tested against ideas that do not fit neatly into the
current ontology. A good helper should let an agent say, in effect:

- this may need a new project vocabulary term;
- this may belong in `ontology` before it belongs in `map`;
- this is a useful intermediate concept even if no existing helper shape covers
  it;
- here are several plausible RDF framings, and this one feels more robust.

If a promotion helper can only produce familiar map facts, it is too narrow. The
agent's knowledge-graph reasoning should remain primary; DoxaBase should help
draft, validate, and preserve the graph move, not decide that only existing
templates are legitimate.

## Limits

DoxaBase can apply one staged revision with conservative graph-state conflict
checks and can restage a stale proposal when the target graph has drifted. New
staged revisions store snapshot rows for exact count/digest drift reporting. It
does not yet support rich semantic merge diagnostics, rebasing, approval state
machines, or durable graph version browsing beyond those staged snapshots.
