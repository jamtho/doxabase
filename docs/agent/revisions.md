# Revision History

The `history` graph records why graph state changed, what changed, and where
a reviewer can inspect the result. Staged proposals and applied events land
there automatically (see `staged_revisions`); this doc covers durable history
records, browsing, and moving revision state between capsules.

## Recording History

`doxabase.record_graph_revision` writes revision metadata after a meaningful
change, import/export, or review bundle: `summary`, `rationale`,
`changed_graphs` (only roles whose content actually changed — not `history`
itself), plus optional `included_graphs` for unchanged review context,
support links, `export_path`, `graph_counts`, and validation fields. Common
`revision_type` values: `rc:ManualRevision`, `rc:ImportRevision`,
`rc:ExportRevision`, `rc:MapAuthoringRevision`, `rc:FieldTrialRevision`;
declare project-specific types as `rc:RevisionType` in project ontology
before relying on `validate_graph(scope="all")`. Never record ordinary
revisions for `base_ontology`/`base_shapes` — seed changes are package
migrations, not project edits.

## Browsing

`list_revisions(kind=...)` is the discovery door:

- `kind="graph"` (default) — revision records, filterable by
  `revision_type`, `record_kind` (`staged_patch`, `applied_event`,
  `history_record`, `export_record`, `import_record`), `application_status`,
  `staged_validation_status` (`conforms`/`failed`/`not_recorded`),
  `stale_resolution_state`, and `current_staged_work_only`.
- `kind="versions"` — the stored snapshot timeline for one required
  `graph_role`: staged-before, applied-after, and recorded snapshots with
  role-local counts and content digests. Matching counts alone do not prove
  identical content; digests do. This is browsing, not checkout/replay.
- `kind="resource"` — everything that touched one required `resource_iri`:
  revisions that anchor it, staged patches whose parsed payload mentions it
  (subject, predicate, or object), and applied events whose staged source
  matched. The right first call for "what changed this resource and why".

`include_apply_checks=true` adds live application status, blockers, stale
state, and next-action routing per row (default on only for
`kind="resource"`). Rows route to their resolved target — a handled stale
source points at its successor or applied event, so follow the row's
resolved target rather than assuming row == target.

`describe_revision(iri, aspect=...)` inspects one revision:

- `aspect="auto"` — metadata; staged patch rows get the staged review shape
  (`include_current_apply_check=true` adds the live apply branch).
- `aspect="applied_diff"` — stored before/after diff for an applied event;
  `include_triples=true` for exact changed-triple arrays. Read the per-graph
  added/removed counts, not just before/after totals — a replacement can be
  count-neutral.
- `aspect="version_diff"` — compare a stored version (iri = the before
  revision; requires `graph_role`) with the current graph, or with
  `after_revision_iri`.
- `aspect="lineage"` — the staged/applied chain, restage links, current and
  latest pointers, alternatives, and next route for any revision IRI.
- `aspect="resource_lineage"` — the same, scoped to one required
  `resource_iri`, with the applied diff filtered to that resource.
- `aspect="snapshot_evidence"` — recovery-state classification (below).
- `aspect="graph_snapshot"` — full stored contents of one snapshot role
  (requires `graph_role`); pair with the applied diff to pick which
  snapshots matter. Snapshot contents can include historical triples no
  longer in current graphs — treat with export-level care.

## Snapshot Evidence And Handoffs

Exact staged/apply snapshot rows are SQLite-side state. RDF export/import
preserves history graph *metadata* (counts, digests, pairing) but not those
rows — so after an RDF-only handoff, exact diffs and stale-drift triples are
unavailable. `describe_revision(iri, aspect="snapshot_evidence")` classifies
the state:

- `history_plus_snapshot_rows` — complete; exact diffs available.
- `history_only_count_digest` — import the companion snapshot JSON.
- `snapshot_rows_without_history` — import the project/history RDF.
- `history_missing` — nothing arrived yet.

Moving revision state between capsules, source side:

1. `export_preflight(kind="handoff_bundle")` and review privacy warnings.
   Scanner-clean is a review prompt, not shareability approval.
2. `export_bundle(kind="handoff", spec={"trig_path": ...,
   "revision_snapshot_path": ..., "manifest_path": ...})` — project/history
   TriG plus companion snapshot JSON plus a pairing manifest. Narrow with
   `revision_iris`/`snapshot_graph_roles` only when the receiver needs a
   reduced bundle; an applied event's filter pulls in its direct staged
   source automatically, but older restage ancestors must be listed
   explicitly when full-chain drift recovery matters.
3. Markdown review bundles (`export_bundle(kind="staged_revisions")`) are
   review context, not recovery artifacts.

Receiving side:

1. With a manifest: `import_bundle(kind="handoff",
   spec={"manifest_path": ..., "dry_run": true})` to confirm paths, roles,
   and warnings, then the real import. It imports TriG then snapshot JSON
   and returns snapshot evidence plus a recovery plan; if a matching source
   recovery session arrived, continue that session
   (`plan_staged_revision_recovery(session_iri=...)`) before applying
   receiver-local frontier rows.
2. Without a manifest: `import_bundle(kind="trig", spec={"path": ...})`
   then `import_bundle(kind="revision_snapshots", spec={"path": ...})`;
   either order recovers, and the evidence helper names the missing half.
3. Verify the relevant rows reach `history_plus_snapshot_rows`, then work
   the staged queue through the ordinary planner
   (`plan_staged_revision_recovery(current_staged_work_only=true)`), one
   apply per replan.

Suggested import actions may carry placeholder paths — replace them with the
real artifact paths. A handoff bundle can be recovery-complete while its
component TriG and snapshot records each say they are not: neither artifact
is complete alone.

Choosing the export artifact: `export_bundle(kind="trig")` with workflow
graphs is review context only; `kind="context_slice"` is resource-scoped
review context (no snapshot rows); default project TriG is enough for
lineage triage; TriG + snapshot JSON (or `kind="handoff"`) is the portable
recovery bundle.

Python API note: the library keeps the pre-fold methods
(`db.list_graph_revisions`, `db.list_graph_versions`,
`db.list_resource_revisions`, `db.describe_graph_revision`,
`db.describe_applied_revision_diff`, `db.describe_graph_version_diff`,
`db.describe_revision_lineage`, `db.describe_revision_snapshot_evidence`,
`db.export_handoff_bundle`, `db.import_handoff_bundle`,
`db.export_revision_snapshots`, `db.import_revision_snapshots`) with the
same fields the MCP kinds/aspects take.
