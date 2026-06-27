# Revision History

Use the `history` graph to record why graph state changed, what graph roles
changed, what graph roles were included for review, and where a reviewer can
inspect the resulting bundle.

Use `doxabase.record_graph_revision` after graph state has changed, after an
import/export, or after a review bundle when the rationale should remain
available to later agents. For proposed additions/removals that should be
reviewed before application, use `doxabase.stage_graph_revision`; see
`staged_revisions`.

## When To Record

Record a graph revision when you can say:

- these graph roles changed or were consolidated;
- these graph roles were included in the review/export context;
- this is why the change was made;
- these observations, claims, patterns, or evidence supported it;
- this validation result or export path helps a future reviewer.

Do not use ordinary revision records for `base_ontology` or `base_shapes`.
Changes to shipped seed graphs are package migrations, not project edits.

## Example

```python
validation = db.validate_graph(scope="all")
export = db.export_trig("/tmp/project-review.trig")

db.record_graph_revision(
    summary="Project review bundle exported",
    rationale="The map helper field trial produced current-best map facts and supporting observations.",
    changed_graphs=["map", "observations", "patterns", "evidence"],
    included_graphs=export.graphs,
    revision_type="rc:ExportRevision",
    supporting_patterns=[
        "https://example.test/project#pattern_doc_id_parent_doc_id_spine",
    ],
    export_path=export.path,
    graph_counts=export.graph_counts,
    validation_scope=validation.scope,
    validation_conforms=validation.conforms,
    validation_result_count=validation.result_count,
)
```

If an agent records new observations or patterns but leaves the map unchanged,
keep `changed_graphs` narrow and include the map only as review context:

```python
export = db.export_trig("/tmp/project-review.trig", graphs="workflow")

db.record_graph_revision(
    summary="No-map-edit review bundle exported",
    rationale="The map was exported for reviewer context, but only observations, patterns, and evidence changed.",
    changed_graphs=["observations", "patterns", "evidence"],
    included_graphs=export.graphs,
    revision_type="rc:FieldTrialRevision",
    export_path=export.path,
    graph_counts=export.graph_counts,
)
```

When `graph_counts` is supplied, DoxaBase also records those graph roles as
included review/snapshot context. Passing `included_graphs=export.graphs` makes
that distinction explicit for readers.

`changed_graphs` describes the content change being recorded. It should not
include `history` merely because `record_graph_revision()` writes revision
metadata there.

Use `list_graph_revisions()` when you need to discover staged, applied, or
historical revision records. Use `describe_graph_revision()` when you want a
compact review of one revision record instead of generic outgoing triples.
Use `describe_revision_lineage(revision_iri)` when you already have any staged
source, restaged successor, or applied event IRI and need the graph-level
restage/apply chain, current/latest pointers, alternatives, and next route
without patch payloads. Its `warnings` surface snapshot handoff hazards such as
RDF-only count/digest history that needs companion snapshot JSON before exact
diffs or stale drift triples are available, plus imported-history integrity
hazards such as missing applied sources, non-staged restage-chain rows, and
parallel restage successors.
Graph snapshots include both `triple_count` and a `sha256:<hex>` content digest;
matching counts alone do not prove two revision contexts are identical.
Exact staged/apply snapshot rows are SQLite-side review state. RDF
`export_trig()`/`import_trig()` preserves the history graph metadata, but it
does not include those stored snapshot rows. When exact applied-diff or
stale-drift triples must survive a capsule handoff, pair the RDF bundle with
`export_revision_snapshots()` and import it with `import_revision_snapshots()`
after the RDF import. Keep the source capsule or explicit before/after exports
when a downstream agent will only receive an RDF bundle. For controlled
replacements, record the exact removed/added assertions in the rationale or
preserve before/after exports when no snapshot bundle is available.
Use `describe_revision_graph_snapshot(revision_iri, graph_role,
include_triples=True)` when you need the full stored contents of one revision
snapshot role. It is narrower than historical graph browsing: pair it with
`describe_applied_revision_diff()` to discover the staged before IRI and
applied after IRI, then inspect the specific role snapshots you need.
Snapshot bundles can contain historical triples that are no longer present in
current graphs, so treat them as review artifacts with the same care as graph
exports.
Snapshot export filters are inclusive and quiet: if a requested revision IRI has
no stored rows, the export can still be a valid empty bundle. The returned
`revision_iris` and `graph_roles` list what was actually exported, in storage
order rather than caller input order. When a requested revision is an applied
staged-revision event, the filter also includes its staged source revision so
the bundle has both before and after rows for exact diff reconstruction. A
zero-quad snapshot row can still be meaningful, for example the empty
before-state of an applied staged revision.
That applied-event convenience includes the direct staged source, not every
older ancestor in a restage chain. If a receiving agent must recover exact drift
for the full restage chain, include those older staged revision IRIs explicitly;
lineage warnings call out visible chain rows that have RDF count/digest metadata
but no stored snapshot rows.
Use `describe_revision_snapshot_evidence(revision_iri)` after imports when the
revision recovery state is unclear. It classifies `history_missing`,
`history_only_count_digest`, `history_plus_snapshot_rows`, and
`snapshot_rows_without_history`. The last state means snapshot JSON was imported
but the matching RDF history records are absent; this commonly happens after a
workflow-only RDF handoff, and normal revision helpers still need a project or
history RDF import. The status includes structured `suggested_next_actions`:
missing exact rows point at `import_revision_snapshots`, and orphan snapshot
rows point at `import_trig` for the project/history RDF.
Those import actions include placeholder paths plus
`path_is_placeholder=True`; replace them with the actual handoff artifact paths
before calling the import tools. Revision list, detail, and lineage responses
promote these import actions to top-level `suggested_next_actions`; list and
lineage `next_action_queue` / `next_action` route them as
`complete_handoff_import` before diff or stale-drift inspection.
`import_revision_snapshots()` also returns `post_import_snapshot_evidence` for
the bundle's revision IRIs, so snapshot-before-history imports can be routed
without making a separate evidence call first.

## Revision List Triage

When reviewing unknown or possibly stale staged proposals, start with the list
row before opening the full staged revision:

```python
staged = db.stage_graph_revision(
    summary="Add trial dataset",
    rationale="Keep this proposal reviewable before making it current-best map context.",
    stance="rc:CandidateRevision",
    additions=[
        {
            "graph": "map",
            "format": "turtle",
            "content": """
                @prefix ex: <https://example.test/project#> .
                @prefix rc: <https://richcanopy.org/ns/rc#> .
                @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                ex:TrialDataset a rc:Dataset, rc:Table ;
                    rdfs:label "Trial dataset" .
            """,
        }
    ],
    validation_scope="all",
)

before = db.list_graph_revisions(include_apply_checks=True)

# Any ordinary map write can make an older staged snapshot stale.
db.record_map_dataset(
    iri="https://example.test/project#InterveningDataset",
    label="Intervening dataset",
    is_table=True,
)

after = db.list_graph_revisions(include_apply_checks=True)
```

When you already know the queue you need, narrow the list instead of scanning a
mixed history response. For example, use `record_kind="applied_event"` for
applied staged events, `application_status="ready"` for mechanically ready
staged proposals, or `stale_resolution_state="stale_unresolved"` for stale
sources that still need recovery. Filters on `application_status` and
`stale_resolution_state` automatically compute apply checks for staged patch
rows.
Use `current_staged_work_only=True` when you want the live mutation-review queue
without stale originals that already have restaged successors or staged sources
that already have applied events. The excluded rows remain useful history; they
just are not current work. This filter also computes apply checks, so the queue
includes live `application_status`, blocker, and suggested-action fields.
When inspecting a mixed history list, use `not_current_staged_work_reason` to see
why a false `is_current_staged_work` row was excluded from that queue.
If you keep the mixed page, `returned_application_status_counts` still counts
historical rows such as handled stale conflicts, while
`returned_current_staged_work_application_status_counts` narrows the same
returned page to rows where `is_current_staged_work=True`.

For a cold staged-work handoff, a good first pass is:

```python
queue = db.list_graph_revisions(
    current_staged_work_only=True,
    include_apply_checks=True,
    drift_detail="summary",
)
print(queue.returned_application_status_counts)
print(queue.returned_current_staged_work_application_status_counts)
for item in queue.revisions:
    print(
        item.application_status,
        item.stale_resolution_state,
        item.validation_conforms,
        item.validation_result_count,
        item.iri,
    )
```

For fast routing, prefer the queue fields in this order:

1. Use `next_action_queue` on `list_graph_revisions()` or
   `export_staged_revisions().bundle_summary` to group work by current action
   class.
2. Use each row's `next_action.queue`, `next_action.action_label`, and
   `next_action.arguments` for row-level routing.
3. Use `suggested_next_actions` when you need concrete follow-up calls and
   arguments.
4. Use `application_status`, `application_blocking_reasons`,
   `stale_resolution_state`, and `not_current_staged_work_reason` to explain
   why the row landed in that queue.

Treat that as a triage queue, not an apply queue. It can include ready mutation
candidates, validation-failed repair work, no-op rows, and stale refreshed
successors. `next_action_queue` groups returned row IRIs, not necessarily the
target IRI for the next call; read each row's `next_action.arguments["iri"]`
because a handled stale source can route to the applied event of its restaged
successor. Use `application_status="ready"` when you want only mechanically
ready candidates. Use `application_status="validation_failed"` to find rows
whose current replay still fails SHACL validation. The
`staged_validation_status` filter values are `conforms`, `failed`, and
`not_recorded`; use `conforms`, not `passed`, for staged-time validation that
had no failures. Use
`application_status="superseded_by_restage"` to find sources that would
otherwise replay but already point at a refreshed successor; inspect the
successor instead of applying the source. Use
`staged_validation_status="failed"` to find rows whose stored staged-time
preview failed validation, even if later graph drift now makes the live
`application_status` a conflict. Use `stale_resolution_state="stale_unresolved"`
for stale original proposals with no successor, and
`stale_resolution_state="restaged_successor_stale_unresolved"` when the active
refreshed successor is itself stale. The broader
`current_staged_work_only=True` queue is often the safest starting point because
it catches all of these active categories together.
When alternatives and stale successors are both in play, start there instead of
with a full mixed history list:

```python
queue = db.list_graph_revisions(
    current_staged_work_only=True,
    include_apply_checks=True,
    drift_detail="exact",
)
```

The active stale successor should remain visible with
`stale_resolution_state="restaged_successor_stale_unresolved"` and its own
`next_action.queue` and `next_action.arguments`. Route by
`is_current_staged_work`, `stale_resolution_state`, and `next_action`, not only
by `application_status`; handled stale originals can remain historical
`conflict` rows. If a stale source has `restaged_by` or `current_restaged_by`,
inspect or restage the current successor instead of the original source. If a
ready successor is an alternative to a source that has already been applied,
read `alternative_gate.status`, `alternative_gate.semantic_review_required`,
`alternative_gate.applied_source_iri`, and
`alternative_gate.applied_revision_iri` before mutating. `alternative_to` is the
stored provenance edge; `current_alternative_to` follows a restaged alternative
target to its current successor. Then open the relevant row with
`describe_revision_lineage(revision_iri)` or
`describe_resource_revision_lineage(resource_iri, revision_iri)`; lineage keeps
the competing applied family in `related_revision_iris` without making handled
stale originals look like current work.

Read `application_status`, `application_decision`, `application_can_apply`,
`application_summary`, `application_blocking_reasons`, and
structured `suggested_next_actions` first. Their `action_label`, `arguments`,
and `reason` tell you whether the staged proposal is ready for review, already
applied, blocked by graph drift, or needs fuller inspection.
The stored `validation_conforms` and `validation_result_count` fields describe
the staged-time preview. The `application_status` and related `application_*`
fields describe a live replay against the current graph. If a staged proposal
was validation-failed when recorded but later becomes stale, the live status may
be `conflict`; use `staged_validation_status="failed"` to rediscover it in
lists, then call `describe_staged_revision()` to inspect the stored validation
diagnostics as well as the current apply branch.
The default list call uses `drift_detail="summary"` so snapshot drift rows carry
counts, digests, drift relevance, overlap arrays, and added/removed exact-change
counts without large exact changed-triple arrays. Then use
`describe_staged_revision()`, `check_staged_revision_apply()`,
`list_graph_revisions(drift_detail="exact")`, or an export helper when you need
patch details, the actual exact drift triples, validation diagnostics, or a
human review bundle.

In summary mode, a snapshot drift row can deliberately say:

```python
exact_changed_triples_available=True
exact_changed_triples_included=False
triples_added_since_snapshot_count=2
triples_removed_since_snapshot_count=1
triples_added_since_snapshot=[]
triples_removed_since_snapshot=[]
```

That means exact changed triples exist, but the list row omitted them for
scanning. The scalar counts still show omitted drift volume. It is not missing
evidence; ask for exact detail when you need it. Snapshot drift rows can also
include `drift_relevance`, `patch_overlap_subjects`,
`patch_overlap_predicates`, `patch_overlap_objects`,
and `revision_anchor_overlap`. Treat these as triage hints:
`no_patch_subject_overlap` says exact drift did not touch the staged patch
subjects, while predicate/object overlap may still reflect broad schema
activity. `broad_patch_object_overlap` is the weak object-overlap label for
shared class/type vocabulary such as `rc:Dataset` or `rc:Table`. Anchor overlap is more
review-worthy because exact drift touched a resource the staged revision named
as context.

A staged patch can be blocked even when its own triples are still absent from the
target graph. DoxaBase applies staged revisions conservatively: unrelated count
or digest drift means the target graph is no longer the same graph state the
proposal was previewed against, so restage or inspect before applying.

## Stale Drift Cookbook

When a staged proposal reports `target_count_drift` or `target_digest_drift`,
use a short inspect-restage-apply loop:

```python
queue = db.list_graph_revisions(
    current_staged_work_only=True,
    include_apply_checks=True,
    drift_detail="summary",
)

stale = db.list_graph_revisions(
    stale_resolution_state="stale_unresolved",
    include_apply_checks=True,
    drift_detail="exact",
)

for item in stale.revisions:
    db.describe_staged_revision(item.iri, include_current_apply_check=True)
    restaged = db.restage_staged_revision(item.iri)
    check = db.check_staged_revision_apply(restaged.revision_iri)
    if check.can_apply:
        applied = db.apply_staged_revision(restaged.revision_iri)
        for recheck_iri in applied.post_apply_recheck_revision_iris:
            db.check_staged_revision_apply(recheck_iri)
```

After any apply, treat old readiness as stale. Re-list
`current_staged_work_only=True` or follow
`post_apply_recheck_revision_iris` before applying another same-graph proposal.
Use `record_kind="applied_event"` when you are browsing history after the live
mutation queue is empty.

## Revision Types

Common revision type IRIs:

- `rc:ManualRevision`
- `rc:ImportRevision`
- `rc:ExportRevision`
- `rc:MapAuthoringRevision`
- `rc:FieldTrialRevision`

Use project-specific revision types if these are too coarse. Declare custom
revision types as `rc:RevisionType` resources in project ontology before relying
on `validate_graph(scope="all")`.

## Staged Proposals

`doxabase.stage_graph_revision` records reviewable patch payloads in `history`
without mutating the target graph. Use it when an agent has a promising hunch,
an alternative systematisation, or a candidate map change that should be
preserved for review before it becomes current-best context.

Staged revisions are deliberately lighter than an approval process. They record
stance, rationale, support links, Turtle additions/removals, preview counts, and
SHACL validation results. They do not require proof before an agent can preserve
a bold idea.

Use `describe_staged_revision()` to inspect the proposal and
`export_staged_revision()` to write a Markdown review bundle.

## Post-Apply Recovery

When you need to reconstruct what happened after staged revisions have been
applied, start with `list_graph_revisions(include_apply_checks=True)`. Applied
events have `record_kind="applied_event"` and `applies_staged_revision`; staged
sources expose `applied_by` after application. Inspect the applied event with
`describe_graph_revision()` for the same `record_kind`, after-state graph
snapshots, and the compact `applied_source` card. Inspect the staged source with
`describe_staged_revision()` when you need patch content, full validation
diagnostics, impacts, or judgement panels. For a mixed queue, use
`export_staged_revisions()` or `restage_staged_revisions(path=...)` and read
`bundle_summary` to separate already-applied inspection targets, unresolved
stale proposals, validation failures, and current mutation-review candidates.
If your starting point is a single revision IRI and you only need routing
context, call `describe_revision_lineage()` first. It joins the selected row to
its visible staged/applied pair, restage chain, alternatives, latest row, and
next action without requiring a resource IRI or large patch payload. Read
`related_revision_iris` when an alternative branch may already have an applied
event, and read `warnings` before assuming exact snapshot-backed diffs are
available in an imported capsule.
When `staged_revision_iri` is `None` on an applied event lineage, read
`warnings`: the applied event may point to a staged source that is absent from
the visible history graph.

A cold recovery script usually follows this order:

1. Call `list_graph_revisions(include_apply_checks=True, drift_detail="exact")`.
2. Filter rows with `record_kind == "applied_event"`.
3. Call `describe_graph_revision(applied_iri)` for the applied event's
   after-state `graph_snapshots`, compact `applied_source`, and
   `applies_staged_revision` link. Applied-event rows and descriptions suggest
   this call plus `describe_applied_revision_diff(applied_iri)`.
4. Call `describe_applied_revision_diff(applied_iri, include_triples=True)` when
   you need before/after changed triples and snapshot evidence says exact rows
   are available.
5. Call `describe_staged_revision(description.applies_staged_revision)` for the
   original patch content, before-state snapshots, validation details, support,
   and judgement context. Use `include_current_apply_check=True` when you also
   want the source revision's live already-applied/stale/ready branch in the
   same response.
6. Follow `applied_by` on staged descriptions when starting from the source
   proposal rather than from the applied event.

Do not call `check_staged_revision_apply()` after application expecting an exact
before/after diff. It reports `status="already_applied"` and points you toward
inspection; it does not replay the patch or return drift arrays for the applied
event.

When the question is resource-centric, start with
`list_resource_revisions(resource_iri)` instead of scanning the whole history
queue by hand. It returns revisions that explicitly anchor the resource, staged
patches whose parsed RDF payload mentions the resource as subject, predicate, or
object, and applied events whose staged source matched. Patch mention summaries
are role-aware flags with matched triple counts; call
`describe_staged_revision()` for full patch content.

For a stale-restage-apply handoff between capsules:

1. Restage stale work with `restage_staged_revision(stale_iri)`.
2. Check the successor with
   `check_staged_revision_apply(restaged.revision_iri)`.
3. Apply only after review with `apply_staged_revision(restaged.revision_iri)`.
4. Export both the project/history RDF and SQLite-side snapshot rows:
   `export_trig(project_path, graphs="project")` plus
   `export_revision_snapshots(snapshot_path, revision_iris=[applied_iri])`.
   Include older stale ancestor IRIs explicitly if exact full-chain recovery
   matters beyond the direct staged source and applied event.
5. On the receiving capsule, run `import_trig(project_path)` first. Before the
   snapshot JSON import, expect `history_only_count_digest` and no exact triples.
6. Run `import_revision_snapshots(snapshot_path)` and verify
   `post_import_snapshot_evidence` or `describe_revision_snapshot_evidence()`
   reaches `history_plus_snapshot_rows`.
7. Then use `describe_applied_revision_diff(include_triples=True)` for changed
   triples, or `describe_revision_graph_snapshot(..., include_triples=True)`
   for full before/after snapshot contents. Suggested import paths are
   placeholders when `path_is_placeholder=True`; replace them with real handoff
   artifact paths.

After the successor is applied, direct routes from the older stale source keep
`restaged_by` / `current_restaged_by` pointing at the staged successor, but
`check_staged_revision_apply()`, `list_graph_revisions()`, and grouped export
rows can put `next_action.arguments["iri"]` on the applied event. Use lineage
when you need the full chain; use row-local `next_action` when you just need the
next inspection call.

Use the full provenance recipe when an autonomous agent needs to answer "what
changed this resource, why, and what review action remains?":

1. Call `list_resource_revisions(resource_iri, include_patch_mentions=True,
   include_apply_checks=True, drift_detail="summary")`.
2. Inspect `match_types`, patch mention flags, `revision.application_status`,
   `revision.stale_resolution_state`, `revision.next_action`, and the top-level
   `next_action_queue` before opening large payloads.
3. Open the relevant row with
   `describe_resource_revision_lineage(resource_iri, revision_iri,
   include_applied_diff=True)`.
4. Switch to `drift_detail="exact"` or a focused apply check before restaging
   stale work where exact drift matters.
5. After RDF-only handoff imports, call
   `describe_revision_snapshot_evidence()` or read applied-diff
   `snapshot_evidence` before assuming exact before/after triples are present.
6. For helper-owned single-valued fields, prefer replacement-style staged
   patches over additive annotations when validation says the helper-created
   resource already has a max-count value.
Use `describe_resource_revision_lineage(resource_iri, revision_iri)` after that
when one row needs a compact handoff card. It pairs applied events with their
staged source when visible, carries the selected row's next action, and can
summarize exact applied-diff triples filtered to the resource. It also exposes
the selected revision family's `restage_chain_iris` and
`alternative_revision_iris` so resource-first workflows can notice sibling
alternatives. It is a resource-centric helper, not full graph-version browsing.
Its
`current_staged_revision_iri` names only still-current staged work, and
`current_revision_iri` is the same value under the batch-restage current-row
name. `latest_revision_iri` / `latest_role` name the latest visible revision in
the selected staged/apply family, including an applied event after a successor
has been applied. If a restage successor has already been applied, follow
the lineage `next_action` / `suggested_next_actions`; they prefer inspecting
the applied event while keeping the stale source and successor discoverable in
`related_revision_iris`.

Call `describe_applied_revision_diff(applied_iri)` when you need stored
before/after snapshot counts and digests for an applied staged revision. Pass
`include_triples=True` when you also need exact changed-triple arrays; the
default response omits those arrays to keep MCP payloads small.
Read the per-graph `triples_added_count` and `triples_removed_count`, not only
the before/after graph counts. A replacement can keep the same triple count
while still adding and removing exact triples.
Use `describe_revision_graph_snapshot(staged_source_iri, graph_role,
include_triples=True)` for the full before snapshot and
`describe_revision_graph_snapshot(applied_iri, graph_role,
include_triples=True)` for the full after snapshot. On RDF-only imports, these
helpers can still report `rdf_history_graph_snapshot` count/digest metadata,
but exact triples require importing the companion snapshot JSON. On
snapshot-only imports, import the RDF history bundle before using normal
applied-diff helpers.
The response carries `snapshot_evidence` for the applied event and
`source_snapshot_evidence` for the staged source. If either says
`history_only_count_digest`, import the companion revision snapshot JSON before
assuming the graph-diff note is the full recovery context.

This is still provenance browsing, not durable graph-version browsing. The
applied event gives counts and content digests; `applied_source` gives compact
intent context; the staged source gives the full intended patch. The diff helper
compares the staged source's before snapshots with the applied event's after
snapshots for changed graphs. It does not browse arbitrary historical graph
versions.

## Limits

DoxaBase can apply staged patch proposals with conservative graph-state conflict
checks, and can restage a stale proposal against current graph state when
unrelated drift made it obsolete. New staged revisions store snapshot rows for
exact count/digest drift reporting, but DoxaBase does not yet provide rich
semantic merge diagnostics, approval workflows, or durable graph version
browsing beyond those staged snapshots. The revision helpers preserve rationale
and review context now, while leaving fuller slice replacement for later.
