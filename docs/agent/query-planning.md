# Query Planning

DoxaBase curates the metadata a query needs; something else executes it.
A good handoff takes relations and paths ONLY from capsule assertions —
never invented, never "probably" — with explicit unresolved bindings, the
caveats that bear on interpretation, and the review gates a human must clear
before running anything.

`doxabase.describe_query_context(iri=dataset_iri)` is the inventory: compact
non-secret planning context with readiness, target candidates, issues, and
repair templates. The same tool drafts the plan: pass `plan_candidate=`
(`"auto"`, a candidate selector string, or a candidate index) to get a
non-executed, review-gated physical plan for that candidate. The other
planning parameters (`engine`, `storage_access_iri`, `physical_layout_iri`,
`allow_context_blocked_candidate`) are valid only alongside
`plan_candidate`.

Two special readiness shapes short-circuit the flow: non-tabular assets
(`is_table=false`) return `not_applicable_non_tabular_asset` — inspect them
with `describe_resource` or a context slice instead of repairing storage;
`rc:AnalysisView` resources return `readiness="logical_analysis_view"` —
inspect the view's definition and query its SOURCE datasets rather than
inventing physical storage for the view.

## Reading The Context

1. `query_target_decision` selects a candidate; each candidate card carries
   a stable `candidate_selector` to pass back as `plan_candidate` after
   review. Automatic selection is precedence, not project intent: when peer
   ready candidates exist, choose by the candidates' inherited storage
   `route_roles` (production/current/canonical vs sample/archive/backfill),
   not by labels or path strings.
2. Candidate cards preserve where each path came from (dataset-owned
   template, partition template, storage-access template, or the storage
   root itself). A root-only candidate is executable only when
   `location_kind="object"`; broader roots need templates. A template
   appended to an exact object root is review-only.
3. `readiness` and `issues` are context-wide: sibling metadata can keep the
   whole context review-required even when the selected candidate itself is
   clean. Candidate-local cleanliness fields distinguish the two; drafting a
   clean candidate out of a context blocked by sibling metadata requires the
   explicit selector plus `allow_context_blocked_candidate=true`, and never
   applies when the candidate has direct blockers.
4. Verification status gates trust: `rc:GeneratedFromManifestLayout` and
   `rc:CandidateLayout` are honest review context and keep plans gated;
   only real listing or query evidence justifies the verified statuses.
5. `analysis_warnings` are interpretation caveats, separate from physical
   readiness — pause on severe caveats even when the plan is ready.
6. Profile-run candidates in the context name evidence worth inspecting
   (`describe_resource(aspect="profile_run", ...)`) before trusting a
   profile-derived row count as current.

## Repairing Metadata

When issues carry repair templates, the repair groups are the metadata
mutation lane. They are reviewed templates, not call-ready actions: fill
placeholders, add `rationale`, skip already-satisfied or already-pending
options, and honor choose-one groups. The staged repair kinds carry
rationale into history:

- `stage_revision(kind="query_storage_access_repair", spec={...})` — a
  reviewed new non-secret storage access and dataset link (or a staged link
  to an existing access chosen from the ranked candidates — review them; a
  candidate already attached elsewhere is a caution, not an invitation).
- `stage_revision(kind="query_physical_layout_repair", spec={...})` — a
  reviewed physical layout; for database storage choose a table layout such
  as `rc:PostgreSQLTable` / `rc:SQLiteTable` / `rc:MySQLTable`.

Direct `record_map_fact` repairs are for intentional immediate writes only
and leave no revision rationale. After EACH applied repair, rerun
`describe_query_context` before the next repair or draft — one apply can
change the repair list (and can stale a pre-staged sibling repair: replan,
restage, recheck; see `staged_revisions`). Common late-stage repair groups:
removing a stale partition-scheme or physical-layout link that context-
blocks a corrected route, moving a misplaced database relation template
onto the storage access, and replacing a dataset's stale
`rc:layoutVerificationStatus` once storage and layout are verified.

Fixture staleness cue: if known AIS/Polymarket fixture tables exist with
zero storage accesses, the capsule is stale or intentionally reduced — load
fresh fixtures into scratch before drawing conclusions or staging repeated
per-table repairs.

## Reading The Draft

`describe_query_context(iri=..., plan_candidate=...)` returns the
non-executed plan. `handoff_kind` is the compact route:
`no_query_target`, `not_applicable_non_tabular_asset`,
`metadata_review_required`, `context_review_required`,
`runtime_resolution_required`, `database_relation_handoff`,
`binding_values_required`, `execution_attempt_ready`.

The gates, strictest last:

- `review_gate.executable_without_review` — no recorded review blocker for
  the selected candidate.
- `storage_environment.runtime_resolution_required` — endpoint, credential,
  or region context still resolves outside DoxaBase (normal for S3 and
  database routes).
- `binding_requirements` / `required_bindings` — template placeholders
  still need runtime values. Partition and column-match hints on binding
  rows help find likely source columns; they never supply values.
- `review_gate.ready_for_execution_attempt` — the only field that permits
  considering an execution attempt: review clear, no runtime resolution, no
  unresolved bindings. `status="ready"` or empty blocking codes never
  override it; when it is false, route from the execution-attempt blocking
  reason codes.

Scan card semantics: `scan.uri_template` is a file/object handoff;
`scan.relation_identifier` (+ `scan.connection_reference`) is a database
relation handoff — never treat the relation as a file path, and expect
`scan.function=None` there. A connection reference without a relation is
repair context, not a handoff. `scan.function` is only set when the physical
layout is unambiguous; with multiple linked layouts, review and pass
`physical_layout_iri`, and expect format/extension or format/protocol
mismatches to stay review-gated.

## Recording Outcomes

When an external runtime executes a reviewed plan — or refuses to — preserve
it: `record_observation(kind="query_result")` with `execution_status`,
`engine`, query source path/hash, `result_sources` for outputs,
`scanned_source_paths`/`scanned_source_handles` for reviewed inputs (a
database handle like `warehouse-prod:mart.orders` is a handle, not a fake
file path). Failures and blocked attempts are lore too, and carry
`failure_summary` instead of profile counts.

When query evidence identifies a reviewed source but the map still lacks
physical metadata, `stage_revision(kind="query_evidence_overlay",
dry_run=true, spec={...})` drafts validation-previewed
`stage_revision(kind="graph")` arguments that add storage and layout with
evidence support. It is dry-run-only by design: it never parses artifacts to
guess storage — you supply reviewed non-secret values, then stage the
returned arguments as `kind="graph"`, check, apply, rerun the context, and
only then draft the plan. Keep the verification status honest: a blocked
query supports a candidate route, not a verified one.

Non-secret handles travel faithfully through all these responses — paths,
endpoints, roots, relation identifiers. They are collaborator-visible
planning metadata, not credentials; summarize or redact surprising local
references before pasting payloads into reports.

## Worked Gap: AIS DailyIndex

The bundled AIS fixture is a deliberately reduced pressure test — do not
"fix" its shape in the fixture itself. `ais:DailyIndex` inherits
`ais:daily_date_partition`, whose template
`broadcasts/{year}/ais-{date}.parquet` is the BROADCAST route; the observed
index route is `s3://ais-noaa/index/*/*.parquet` (partition-shaped:
`index/{year}/ais-{date}.parquet`), and the real index schema is far wider
than the fixture's six columns. The graph marks this honestly:
`rc:UnverifiedLayout` on the dataset, the shared template
`rc:GeneratedFromManifestLayout`.

A scratch overlay that reaches a credible non-executed DuckDB handoff needs
all of these reviewed moves:

1. Add the missing index columns that matter (for example
   `ais:ix_vessel_names`, physical type `rc:VarcharList`).
2. Add a DailyIndex-linked storage access with the non-secret S3 facts and
   `rc:pathTemplate "index/*/*.parquet"` — verified status only when the
   listing/query evidence is actually in scope.
3. Add a separate `ais:daily_index_date_partition` with the index-shaped
   template and partition column.
4. Update the dataset's own verification status with a note naming the
   evidence.
5. Stage and apply REMOVAL of the inherited broadcast `rc:partitionedBy`
   link — while it remains, the corrected candidates stay context-blocked;
   the context exposes this as a remove-stale-partition-link repair group.

After those moves the wildcard index candidate drafts as
`runtime_resolution_required`: correct template, no bindings, review clear —
blocked only by endpoint/credential resolution outside DoxaBase, which is
the honest end state. `examples/ais-query-overlay-smoke.py` is the
maintained executable version of this walkthrough.

Python API note: the library exposes `db.draft_query_plan(...)` as its own
method (the MCP door is `plan_candidate=` on `describe_query_context`) and
`db.draft_query_evidence_storage_overlay(...)` (the MCP door is the
`query_evidence_overlay` dry-run kind).
