# API Reference

Current Python API entry point:

```python
from doxabase import DoxaBase, to_dict, to_jsonable
```

For compact returned-field examples, read `response_shapes`. It names the
common dataclass and MCP helper fields that agents usually need when scripting.

## Create or Open a Capsule

```python
db = DoxaBase.create(".doxabase.sqlite", overwrite=True)
```

This initializes the SQLite schema, registers default graph roles, and seeds
immutable `base_ontology` and `base_shapes`.
Use `DoxaBase(path)` to open an existing capsule with normal schema, graph-role,
seed, and search-index maintenance. Use `DoxaBase.open_readonly(path)` when a
field trial or safety preflight must inspect an existing capsule without any
DoxaBase initialization writes; it opens SQLite with `mode=ro`, so mutating
helpers fail at the database layer.
`seed_base_graphs()` seeds only empty immutable seed graphs; it is not a seed
refresh or migration helper for older non-empty capsules. If staging reports
that immutable `base_ontology` is missing current staging vocabulary, follow
`project_brief`'s stale-seed health action and preflight a handoff export before
creating a fresh `DoxaBase.create(...)` capsule. `export_handoff_bundle(...)`
is valid even when there are no staged revision rows; the snapshot JSON will be
empty and `import_handoff_bundle(...)` will return an empty recovery plan plus a
`project_brief()` follow-up action for the receiving capsule. Do not use a
normal `all_with_seeds` import for this recovery path because
immutable seed graphs are protected. When the stale capsule has staged revision
rows or exact revision recovery matters, preserve the project/history TriG plus
companion revision snapshot JSON, import both artifacts into the fresh capsule,
then follow the staged recovery plan returned by `import_handoff_bundle(...)`.

Use `to_dict(result)` or `to_jsonable(results)` when a direct Python script
needs serializable versions of returned dataclass-like API objects. MCP helpers
already return JSON-like dictionaries.

## Import Data

```python
db.import_turtle("path/to/file.ttl", graph="map")
db.import_trig("path/to/file.trig")
db.import_revision_snapshots("path/to/revision-snapshots.json")
```

`import_turtle()` writes all triples to one graph.

`import_trig()` preserves named graph roles and maps
`https://richcanopy.org/graph/{role}` to `{role}`. It preflights all non-empty
named graphs before writing, so an import that later hits an immutable seed graph
or unknown Rich Canopy role leaves the target capsule unchanged. Normal imports
still reject `base_ontology` and `base_shapes`; import all-with-seeds bundles
only with deliberate seed-handling. The MCP `doxabase.import_trig` wrapper also
reports bounded `post_import_snapshot_evidence` for imported history revisions;
follow its `import_revision_snapshots` action when a context-slice import
validated but still has only RDF count/digest snapshot metadata.

`import_revision_snapshots()` restores an opt-in JSON bundle of SQLite-side
revision snapshot rows. Use it after an RDF project/history import when exact
`describe_applied_revision_diff(include_triples=True)` reconstruction must
survive the handoff. Existing snapshot pairs are skipped unless `replace=True`.
The result includes `post_import_snapshot_evidence`; if snapshot rows were
imported before history RDF, follow its structured `import_trig` action before
using normal revision helpers.

## Export Data

```python
db.export_graph("/tmp/map.ttl", graphs="map")
db.export_trig("/tmp/project-review-bundle.trig")
db.export_trig("/tmp/workflow-review-bundle.trig", graphs="workflow")
db.export_trig(
    "/tmp/shareable-project.trig",
    fail_on_sensitive=True,
    fail_on_invalid=True,
)
db.export_preflight(export_kind="handoff_bundle")
db.preflight_context_slice_export(
    ["https://example.test/project#child_table"],
    profile="dataset_brief",
)
db.export_context_slice(
    "/tmp/child-table-context.trig",
    ["https://example.test/project#child_table"],
    profile="dataset_brief",
    fail_on_sensitive=True,
)
db.scan_sensitive_literals(graphs=["map", "evidence"])
db.export_revision_snapshots("/tmp/revision-snapshots.json", fail_on_sensitive=True)
db.export_handoff_bundle(
    "/tmp/project-handoff.trig",
    "/tmp/revision-snapshots.json",
    manifest_path="/tmp/handoff-manifest.json",
    fail_on_sensitive=True,
    fail_on_invalid=True,
)
```

`export_graph()` writes one flattened RDF graph, usually Turtle.
`scan_sensitive_literals()` returns redacted credential-like matches for selected
graph roles, including subject URI, predicate URI, object URI, and literal
terms. Matches carry `term_position` and `term_kind`. `export_graph()` and
`export_trig()` include `sensitive_literal_count` and `privacy_warnings`;
exports are not redacted automatically. For unattended or shareable exports, pass
`fail_on_sensitive=True` to scan selected graph roles first and raise before
creating or overwriting the artifact when potential sensitive graph terms are
found. The scanner is conservative and not a complete secret detector, but it
catches common private-key headers, bearer tokens, AWS access key IDs,
`sk_` live/test style keys, key/password/secret assignments or query parameters,
and explicit fake-secret test markers.
Graph/TriG/handoff exports also validate the selected live graph scope by
default and raise before writing when SHACL does not conform. Pass
`fail_on_invalid=False` only for a deliberately reviewed invalid diagnostic
artifact; results include validation scope, conformance, result count, and
diagnostics.
TriG workflow/review exports also include a non-privacy `warnings` entry saying
they are review context only and omit history plus revision snapshot rows. Use
`export_context_slice()` when a handoff should include only the selected
resource neighborhood instead of every resource in a graph role. It omits
immutable seed graphs by default so fresh capsules can import the artifact, and
its preflight scans only selected context-slice triples; scanner-clean still
requires separate shareability review. Use
`export_handoff_bundle()` or project TriG plus `export_revision_snapshots()` for
recovery handoffs.
Read-only orientation payloads that sit near privacy workflows, including
`project_brief()` resource descriptions, profile/evidence summaries, evidence
source lists, profile value previews, and context-slice export `seeds[]`
labels/descriptions, redact scanner-matching display text. This does not redact
RDF or Markdown exports; use `fail_on_sensitive=True` when selected graph or
review content must block before writing.
Export records carry `artifact_kind`, `importable`, `recommended_import_tool`,
and `recovery_complete` so scripts do not have to infer artifact class from the
helper name or file extension. Markdown staged/profile review bundles are
`importable=False`; workflow TriG is importable review context but
`recovery_complete=False`; a full handoff bundle is the recovery-complete
artifact because it pairs project/history RDF with revision snapshot JSON.
`export_preflight()` is a read-only companion for `export_graph()`,
`export_trig()`, `export_revision_snapshots()`, and `export_handoff_bundle()`.
It selects the same graph roles and snapshot rows, returns redacted match
locators with stable non-secret `match_id` values, and reports `decision="block"`
when `fail_on_sensitive=True` would block the corresponding write. A clean
preflight reports `decision="clean_by_scanner_only"` and still sets
`shareability_review_required=True` plus
`shareability_review_status="required_not_completed"`; agents must separately
decide whether paths, endpoints, history payloads, or project facts are
appropriate to share. Non-credential hygiene signals such as absolute local
home/private paths appear in `shareability_hints`, and export records expose
`artifact_disposition` plus `git_safe`; with the current incomplete review
status, `git_safe` remains false.
When a broad graph/TriG/handoff preflight blocks and the task has a known target
resource, follow the suggested
`preflight_context_slice_export(seed_iris=["<target-resource-iri>"])` route to
test a narrower review-context bundle. Context-slice exports can be imported
with `import_trig`, but they are not recovery-complete because they omit
SQLite-side revision snapshot rows.
Non-secret path-shaped values such as local paths, object-store URIs, endpoint
URLs, and relative paths remain ordinary graph content: they are preserved in
faithful RDF exports and do not by themselves trigger `privacy_warnings`.
Review artifact shareability separately from sensitive-literal scanning; keep
user-specific paths or endpoint details that should not travel out of the graph
or replace them with collaborator-safe references before export.

`export_trig()` writes a named-graph bundle with graph role IRIs so another
DoxaBase capsule can import it again. The default exports mutable project
graphs. Use `graphs="workflow"` for `map`, `observations`, `patterns`, and
`evidence`; use `graphs="all_with_seeds"` only when you explicitly need shipped
seed graphs in the bundle. The export record can list empty graph roles, but
TriG serializes only graph blocks that contain triples. Importing into a fresh
`DoxaBase.create(...)` capsule recreates the standard role metadata before the
non-empty graphs are imported. Workflow exports intentionally omit project
`ontology` and `history`; use the default project export or an explicit
history-bearing bundle for revision-lineage handoffs, and use an
ontology-bearing bundle when project-specific metric kinds, value types,
classes, or predicates are part of the handoff. RDF exports do not include
SQLite-side snapshot rows; pair them with `export_revision_snapshots()` when
exact applied-diff or stale-drift
triple reconstruction must survive import.
The workflow/review export record repeats this as a `warnings` entry so callers
do not mistake review context for a recovery bundle.
Use `export_handoff_bundle()` when a receiver needs both project/history RDF and
exact revision snapshots. It writes the project TriG artifact and companion
snapshot JSON together, preflighting both output paths and combined privacy
warnings before creating either file. Pass `manifest_path` to persist a small
JSON manifest with artifact paths, redacted privacy warnings, preflight-style
scanner/shareability metadata, and the expected receiver import sequence. On
the receiving capsule, prefer
`import_handoff_bundle(manifest_path, dry_run=True)` followed by
`import_handoff_bundle(manifest_path)` when that manifest is available; the
helper imports the paired TriG before snapshot JSON and returns snapshot
evidence plus a staged recovery plan. Relative artifact paths resolve from the
manifest directory, and copied manifests with stale absolute artifact paths can
still import when the paired artifacts with matching basenames sit next to the
manifest. If the imported history already contains a matching
`rc:StagedRevisionRecoverySession`, follow the returned
`describe_staged_revision_recovery_session` action before creating a
receiver-local session. Treat `scanner_clean=true` as scanner output only while
`shareability_review_status="required_not_completed"`.

`export_revision_snapshots()` writes a faithful JSON handoff bundle for stored
revision snapshot rows. Its result includes `sensitive_literal_count` and
`privacy_warnings`; pass `fail_on_sensitive=True` to raise before creating or
overwriting the JSON artifact when stored snapshot quad subjects, predicates, or
object terms scan dirty. Pass `revision_iris=[applied_iri]` to preserve the
applied
after-snapshot plus the staged source before-snapshot needed by one applied
staged revision diff, or omit the filter to export all stored snapshot rows in
the capsule.

## Replace Graph Triples

```python
replacement = db.replace_graph_triples(
    "map",
    removals="""
        @prefix ex: <https://example.test/project#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:Customers rdfs:label "Customers scratch table" .
    """,
    additions="""
        @prefix ex: <https://example.test/project#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:Customers rdfs:label "Customers scratch table, drifted" .
    """,
    expected_count=db.triple_count("map"),
)
```

`replace_graph_triples()` removes caller-authored Turtle triples and inserts
caller-authored replacement triples in one mutable graph. It returns before and
after counts, graph content digests, and actual removed/added triple counts.
The default `allow_count_change=False` makes it useful for controlled
same-count replacements: DoxaBase computes the effective mutation first and
raises before writing if the graph count would change. Pass
`allow_count_change=True` only when an intentional count-changing edit is the
right move.

Use this for controlled graph maintenance or staged-revision field trials. It is
not a semantic merge/rebase helper; staged proposals that become stale still
need `check_staged_revision_apply()`, review, and usually
`restage_staged_revision()`. If the exact replacement diff must remain
mechanically retrievable later, preserve it with before/after exports, a staged
snapshot/apply-check, or explicit revision rationale/metadata when you record
the graph revision.

## Inspect

`graph_overview()` returns `named_graphs`; it does not expose a `.graph_counts`
attribute. Derive per-graph counts from each card's `triple_count`.
`search()` returns `SearchResults` with `.matches`, `.returned_count`,
`.total_count`, `.omitted_count`, `.has_more`, and `.next_offset`; it does not
expose a `.count` attribute. `list_entities()` exposes the same explicit
pagination fields on `EntityList`.

```python
overview = db.graph_overview(limit=100)
brief = db.project_brief(limit=20, profile_candidate_limit=2)
tables = db.list_entities(type="rc:Table", graph="map", limit=100)
dataset = db.describe_dataset(tables.entities[0].iri)
context_slice = db.describe_context_slice(
    [dataset.iri],
    profile="dataset_brief",
    include_trig=True,
)
claims = db.list_entities(type="rc:Claim", graph="observations", text="join")
patterns = db.list_entities(type="rc:Pattern", graph="patterns", text="body_top")
matches = db.search("MMSI vessel", graph="map", limit=10)
observation = db.record_observation(
    summary="Dataset was inspected during the current workflow.",
    observed_asset=dataset.iri,
    evidence_summary="Recorded from the API reference example.",
    evidence_sources=["docs/agent/api-reference.md"],
)
claim = db.record_claim_observation(
    summary="Example source-backed join claim.",
    claim_text="The child table joins to the parent table by parent_doc_id.",
    claim_kind="rc:JoinClaim",
    claim_targets=["https://example.test/project#parent_doc_id"],
    evidence_summary="Recorded from the API reference example.",
    source_path="docs/agent/api-reference.md",
    source_kind="rc:DocumentationSource",
)
weaker_claim = db.record_claim_observation(
    summary="Example caveat claim.",
    claim_text="The join is useful operationally but is not enforced upstream.",
    claim_kind="rc:CaveatClaim",
    claim_targets=["https://example.test/project#parent_doc_id"],
    evidence_sources=["DoxaBase describe_dataset output"],
    source_kind="rc:DoxaBaseAPISource",
)
reconsideration = db.record_claim_reconsideration(
    newer_claim=weaker_claim.claim_iri,
    older_claim=claim.claim_iri,
    relation="weakens",
    rationale="The caveat narrows the earlier join claim without making it useless.",
    evidence_sources=["DoxaBase describe_dataset output"],
    source_path="/tmp/doxabase-describe-dataset-output.json",
    source_kind="rc:DoxaBaseAPISource",
)
pattern = db.record_pattern(
    summary="Repeated evidence supports the parent_doc_id join.",
    pattern_text="Documentation and join checks both indicate parent_doc_id links child rows to message rows.",
    rationale="The claim names the join columns and the source span records where the handoff explains them.",
    pattern_targets=["https://example.test/project#parent_doc_id"],
    supporting_claims=[claim.claim_iri],
    source_path="docs/agent/api-reference.md",
    source_kind="rc:DocumentationSource",
)
table = db.record_map_dataset(
    iri="https://example.test/project#child_table",
    label="Child table",
    is_table=True,
    path_templates=["data/child.parquet"],
)
column = db.record_map_column(
    iri="https://example.test/project#child_table__parent_doc_id",
    table_iri=table.iri,
    column_name="parent_doc_id",
    physical_type="rc:Varchar",
)
export = db.export_trig("/tmp/project-review-bundle.trig", graphs="workflow")
validation = db.validate_graph(scope="all")
revision = db.record_graph_revision(
    summary="Example workflow bundle exported",
    rationale="The claim and pattern explain why the child table map fact was recorded.",
    changed_graphs=["map", "observations", "patterns", "evidence"],
    included_graphs=export.graphs,
    revision_type="rc:ExportRevision",
    supporting_claims=[claim.claim_iri],
    supporting_patterns=[pattern.pattern_iri],
    export_path=export.path,
    graph_counts=export.graph_counts,
    validation_scope=validation.scope,
    validation_conforms=validation.conforms,
    validation_result_count=validation.result_count,
)
context = db.describe_resource(claim.claim_iri, graph="observations")
```

For unattended project-frontier loops, prefer `brief.first_unattended_action` /
`brief.first_unattended_call`. It resolves blocking privacy/export safety review
or stale seed recovery before frontier expansion or task review. Use
`brief.frontier_status` to audit hidden queue/profile counts, `must_rerun_call`,
and the coarse `mutation_allowed_after` gate. `brief.frontier_first_action`
remains the safety-cleared frontier hop over `full_frontier_expansion`,
`next_best_expansion`, and `recommended_next_tasks[0]`.
After a safety/export review, use that frontier hop or `must_rerun_call` only
for read-only inspection until a rerun clears `mutation_allowed_after`.

`describe_dataset()` returns bounded context for one dataset/table: row
semantics, entity/snapshot keys, columns, physical/value types, path templates,
dataset/layout verification status and notes, physical layouts, storage access
descriptions, partition schemes, direct caveats with impact/severity, upstream
caveats inherited through relationships,
provenance transformations, relationships, directly related datasets, and linked
patterns. Column resource summaries include `column_name`
and owning dataset context when the map provides it; related datasets may be
inferred from column-level relationships even when a relationship resource lacks
explicit source/target dataset triples. Related dataset entries include
relationship labels/kinds; `related_dataset_groups` groups repeated links by
target dataset and folds same-column reasons into relationship tags with
current/related columns and integrity metadata when available. Linked pattern
summaries use the pattern text as their description when available;
relationship entries and grouped reasons may include `source_caveats`, meaning
caveats attached to source datasets or source-side columns that should remain
visible when interpreting an aggregation, derivation, or foreign key.
`upstream_caveats` is the dataset-level deduped rollup of those relationship
caveats and is intentionally separate from direct `caveats`.
`profile_summary` gives quick counts of the profile observations returned in the
bounded dataset description, split across dataset-level, mapped-column, and
unmapped-column profile lore. It also rolls up profile evidence IRIs and lists
`shared_evidence_iris` that appear on every returned profile observation. Total
and omitted profile counts make the response bound explicit when older or
additional profile observations are not included in the returned lists.
`profile_summary.profile_run_candidates` lists evidence IRIs that support more
than one returned profile, sorted by returned profile count, so mixed profile
history can still reveal likely profiler runs. Each candidate includes
`profile_observation_iris`, the returned profile observations linked to that
evidence IRI, so agents can seed a context slice or inspect the grouped run
directly.
Use `describe_profile_run(dataset_iri, evidence_iri)` when the candidate points
at a run that may be wider than the bounded `describe_dataset()` profile lists.
`profile_summary.handoff_note` gives a short reading cue for profile-only
handoffs: profile lore is observed evidence, while storage/path/layout warnings
remain physical query-planning metadata gaps.
Check `layout_verification_status` and `layout_verification_note` before using
`path_templates` for executable query planning. Child physical layout, storage,
and partition descriptions may carry their own verification fields when the
uncertainty belongs to one part of the path/layout model.
`operational_warnings` carries dataset-owned `QueryPlanningIssue` objects that
also appear in `describe_query_context().issues`, so a full dataset handoff can
still flag unverified layouts, missing storage access, or missing physical
layout before an agent writes query plans. Candidate-derived issues such as
path composition warnings are only guaranteed in `describe_query_context().issues`
and `query_target_candidates[].review_reasons`. These warnings carry
`domain="query_planning"` so their severity is not confused with profile
recording or graph validation status. Query-context `analysis_warnings` carry
`domain="analysis"` and, for caveat warnings, preserve the original caveat
severity in `details.caveat_severity_iri` /
`details.caveat_severity_label`.
`linked_pattern_reasons` explains whether a pattern matched through a direct
target, map implication, supporting claim, or supporting observation. Each
reason uses `iri` for the pattern IRI and also exposes the same value as
`pattern_iri` for consumers that prefer the explicit name. Use `match_groups`
for a compressed first pass with relevance tiers, route labels, resource kinds,
and supporting claim/observation links. The compact `match_group_count`,
`raw_match_count`, and `relevance_tier_counts` fields are triage hints, not
confidence scores; `relevance_tier_counts` counts grouped matches, while
`raw_match_count` counts unfolded routes. Prefer direct and map-implication
groups when scanning; use claim/observation-supported groups for context; call
`describe_pattern()` before acting on a pattern; use raw `matches` when you need
every route.

`describe_query_context()` returns a compact read-only query-planning projection
for one dataset. It includes the dataset summary, physical-metadata readiness,
a `readiness_note`, an `issues` list for missing, risky, or informational
physical metadata, `analysis_warnings` for caveats that matter after a query
can be planned, planning notes, columns, path templates, physical layouts,
derived `query_target_decision` and `query_target_candidates`, dataset/layout
verification status and note, storage access descriptions, partition schemes,
direct/upstream caveats, `row_count_snapshot`, `profile_summary`,
`ready_candidate_indexes`,
`unselected_ready_candidate_indexes`, `direct_clean_candidate_indexes`,
`unselected_direct_clean_candidate_indexes`, and structured `suggested_next_actions`
for drafting the selected route. `suggested_repair_action_groups` lifts existing
`issues[].details.repair_hint.actions[]` into a top-level `query_repair_review`
lane with the issue index/code/resource, repair hint type, copied context, and
ordered action templates. Each group also reports `action_status_counts`,
`pending_action_count`, `skippable_action_count`, and
`pending_action_options` so scripts can triage mixed pending and
already-satisfied repair groups before reviewing the templates. If
the dataset is an `rc:AnalysisView`, the query context returns
`readiness="logical_analysis_view"`, no query target candidates, and no
storage-repair groups; call `describe_analysis_view()` for the denominator,
source datasets, caveats, and query snippets before deciding whether to query
or repair source datasets.
If
`action_status="pending_review"`, the option is an actionable review-gated
repair template; fill its required fields rather than treating the status as
blocked. If
`choice_mode="choose_one"`, select one action and follow that action's own
`required_extra_arguments`; the legacy `pending_required_extra_arguments` field
is the group-level union, not one call signature. These repair rows are reviewed
templates rather than call-ready next actions: fill placeholders, add required
extra arguments such as `rationale`, skip actions marked `already_satisfied` or
`already_pending`, and check conditions before calling the named tool.
Context-blocked direct-clean routes can expose
`remove_stale_partition_scheme_link` for reviewed removal of a stale
`rc:partitionedBy` assertion. For database
template-source mismatches and
storage protocol/location mismatches, use `suggested_repair_action_groups` for
ordered, review-gated repair templates; `repair_hint_path` points back to the
nested source detail when needed.
In the common database template-source move, add the reviewed relation
identifier to the storage access, then remove the misplaced source template
only if it was relation metadata rather than a real file/object path. If
`candidate_relation_identifier.storage_access_relation_templates` is present,
the storage access already has relation template(s); the remove action is first,
and the add action is marked `action_status="already_satisfied"` with
`skip_when_already_satisfied=true`. `already_on_storage_access` remains the
exact-value flag for whether the misplaced source template itself is already on
the storage access. Exact matching pending staged repairs on linked storage,
layout, partition, or column resources are marked `already_pending` in compact
repair options and appear in project-brief `pending_staged_repair_iris`.
Protocol/location hints offer reviewed
protocol/root/bucket/prefix edits
and exact path-template add/remove repairs when a template caused the mismatch.
Their templated actions name `placeholder_fields` and `reviewed_value_fields`
for the reviewed value to fill in; database relation add-template actions mark
`object` as the reviewed placeholder and require both `object` and `rationale`.
For `missing_storage_access`, prefer `stage_query_storage_access_repair()` when
a reviewed new storage access should carry graph-revision rationale before map
mutation. The direct record-new-storage template remains available for
intentional current-best writes. In both routes, optional `path_templates` should
be omitted when the dataset or partition already owns the reviewed file/object
path template; duplicating it can produce equivalent ready query candidates. Use
storage-access-owned templates for database relation identifiers. Include
`route_roles` when the reviewed storage route is production/current/canonical,
sample, archive, or backfill. If this repair
comes from a profile draft's `query_context_review` lane, pass
`profile_route_sources=[query_action.source_query_context]` so profile insight
review can mark the staged storage repair as the direct query-context action.
For sampled profile drafts, that route source also carries the profile quality
summary and sampled-evidence caution into generic staged review exports.
Existing
storage candidates can carry
`pending_staged_repair_iris` and `candidate_status="already_pending"` when that
exact dataset/storage link is already staged.
Follow each repair action's `required_extra_arguments`, `placeholder_fields`,
and `reviewed_value_fields` before calling `stage_map_assertion_change`; do not
run `arguments_template` unchanged. It does not generate SQL
or resolve credentials; use it to decide whether the graph has enough
non-secret physical context for a query attempt, then review caveats before
trusting aggregations or
interpretations. Read `query_target_decision` first: its `candidate_index` is a
zero-based pointer into the candidate list, and each candidate has a stable
`candidate_selector` for reviewed follow-up calls. Its `status` tells whether
that candidate is ready, blocked only by sibling context, directly review-only,
or absent. `selected_candidate_direct_clean` is true when the selected candidate
has no direct blocker of its own. When such a selected candidate is blocked by
sibling metadata, the suggested `draft_query_plan` action includes the explicit
`candidate_selector` and `allow_context_blocked_candidate=True`; peer ready actions
include the same allowance when sibling candidate metadata is the only broader
blocker.
Every suggested `draft_query_plan` action also carries `route_card` with the
candidate selector, storage label, route roles, path or relation handle, direct
issue codes, required bindings, and any partition binding examples. Use that
structured card instead of parsing action prose when choosing peer,
production/current, sample/archive, or layout-selection routes. Candidate cards
and route cards include non-secret storage orientation such as `access_mode`,
`region`, `endpoint_profile`, `credential_reference`, `path_style_access`, and
`requires_endpoint_profile`; use `credential_reference` markers such as
`profile:<name>`, `env:<VAR_NAME>`, or
`external:intentionally-unrecorded`, never secret material. DoxaBase still does
not resolve credentials, endpoint profiles, or object existence. Candidate cards
also include
`required_bindings`, `required_binding_details`, `binding_example`, and
`binding_examples` so scripts can compare runtime parameter needs before
drafting a selected route.
When `row_count_snapshot` or profile metrics matter to the query handoff,
`profile_summary.profile_run_candidates` gives the evidence IRIs to inspect with
`describe_profile_run()` without first switching to `describe_dataset()`.
Candidate rows expose `dataset_profile_row_count_bases` and
`row_count_snapshot_basis` under `profile_summary.profile_run_candidates[]`, so
a count that matches the map snapshot can still be recognized as full-scan,
sampled, or unknown-scope support.
When candidate row counts disagree, or when the snapshot-matching run is
sampled, unknown, or mixed basis, `suggested_next_actions` includes additional
`describe_profile_run` actions before query-plan drafting.
When profile evidence exists but all returned evidence is singleton evidence, so
`profile_run_candidates` is empty, `suggested_next_actions` still includes a
bounded `describe_profile_run` action before query-plan drafting. Its
`source_profile_evidence` preview carries the evidence summary, result sources,
query-source paths, structured execution status/engine/query hash from
`record_query_result()` evidence metadata, old summary-parsing fallback values,
and short profile summaries.
`safe_inspection_action_indexes` and `first_safe_inspection_action_index` point
at read-only inspection actions such as `describe_profile_run`. Prefer that
first safe inspection hop before using `first_unattended_action_index`, which
continues to choose among draft-query-plan actions.
If physical metadata blockers remain, the same context can also include a
`draft_query_evidence_storage_overlay` skeleton action. Treat the skeleton as a
review checklist: replace placeholder values named in `placeholder_fields` /
`reviewed_value_fields`, include `route_roles` when the reviewed source route
has known intent, and supply `required_extra_arguments` before calling the
helper.
`unselected_ready_candidate_indexes` names peer direct-ready candidates before a
draft is requested; inspect those cards and pass an explicit `candidate_selector`
when candidate order selected a different route than intended. These indexes
describe candidate-local direct readiness, so they may be non-empty while
top-level `readiness == "needs_review"` because sibling candidate metadata
still blocks the whole context.
When global sibling blockers leave strict ready indexes empty,
`direct_clean_candidate_indexes` and
`unselected_direct_clean_candidate_indexes` name candidates with no direct
warning/error that may still be draftable with an explicit selector and
`allow_context_blocked_candidate=True`.
`query_target_candidates`
preserve template provenance, expose a stable `candidate_selector` for reviewed
follow-up calls, carry storage-access `route_roles`, and compose best-effort
file/object paths from
storage roots or bucket/prefix facts without resolving endpoint profiles or
credential references. They also carry the same non-secret access handles used
by route cards, including `access_mode` and `region`. For database-backed
storage, candidates keep the relation
as `candidate_path` and expose `relation_identifier` plus
`connection_reference` instead of a joined file-like path when the relation
comes from a storage-access-owned template. Dataset or partition file paths
paired with database storage stay review-only with
`database_relation_template_source_mismatch` and no relation identifier. Candidate
`query_target_decision.route_intent_review_candidate_indexes` points at ready or
direct-clean peer candidates with production/current/canonical route-role intent
that the selected candidate lacks; inspect those cards and pass their
`candidate_selector` when they match project intent.
`review_reasons` can include overall-context blockers
from sibling metadata as well as protocol/location warnings, for example
S3-compatible access without endpoint/credential/region cues, non-S3 access
with bucket/prefix metadata, or a storage root that does not match the declared
protocol. For S3-compatible access, a recorded `s3://...` storage root is also
checked against separately recorded `bucket_name` and `key_prefix` facts.
Complete path templates are checked too: an `s3://...` template under HTTP/local
access, an S3 template whose bucket/prefix conflicts with recorded access
metadata, or a relative template that repeats the recorded key prefix will demote
the candidate to review-only. A root-only storage-access candidate is ready only
when `location_kind == "object"`; absent, directory, prefix, or connection
location kinds are review-only until a path template narrows the dataset
location. For non-database storage, an exact object root remains
available as a `storage_access_location` candidate even when dataset or
partition templates are present; candidates that would append those templates to
the object root are review-only with `storage_object_location_has_path_template`.
Partition-specific blockers stay attached to their own
partition candidate; sibling candidates receive an overall-context blocker
instead.
Use `direct_review_required` and `direct_review_reasons` when selecting a first
candidate to inspect: they exclude `query_context_has_other_blockers`, so a
candidate with no direct warning/error can still be distinguished from the stale
or malformed sibling that blocks the overall context. The top-level
`query_target_decision` applies that rule for callers; the candidates remain
supporting cards, not an ordered recommendation contract.
`candidate_path_status` separates path usability from composition: `ready`
means a usable planning input, `orientation_only` means the candidate path is a
review clue, and `unresolved` means executable location metadata is incomplete.
Pair it with `query_target_decision.status` and `direct_review_required`: a
locally clean selected candidate may still be `orientation_only` when unrelated
sibling hints block the overall context.

`draft_query_plan()` returns a non-executed, review-gated physical plan draft
over `describe_query_context()`. It currently supports `engine="duckdb"` and
selects the candidate identified by `query_target_decision.candidate_index` by
default. Pass `candidate_selector`, `candidate_index`, or `storage_access_iri`
to select an explicit candidate; pass `physical_layout_iri` after reviewing linked physical layouts
with distinct signatures; pass `allow_context_blocked_candidate=True` only when
that selected candidate has no direct warning/error and stale sibling metadata
should not block this handoff. If `storage_access_iri` matches multiple
candidate paths,
use the returned candidate snippets to rerun with `candidate_selector`.
When sibling candidate-metadata blockers are the reason for the allowance, pass
an explicit selector too; selectorless automatic drafts keep the context review
gate and show the distinction through
`context_blocked_candidate_allowed=True` /
`context_blocked_candidate_used=False`.
`source_context` preserves both the automatic decision and
the explicit selection audit fields. It also reports `candidate_count`,
`ready_candidate_indexes`, `unselected_ready_candidate_indexes`,
`direct_clean_candidate_indexes`, and
`unselected_direct_clean_candidate_indexes`; when the ready or direct-clean peer
lists are non-empty, the automatic or explicit selection has peer candidates
worth reviewing before execution. Candidate order is not an
authoring-preference contract; use `candidate_index` as a response-local pointer
only after inspecting the returned candidate cards, and use
`candidate_selector` for reviewed follow-up calls.
`source_context.selected_candidate_note` summarizes the actual selected
candidate, route kind, and sibling/context blocker codes that remain visible in
`review_gate.all_issue_codes`.
The response includes a scan hint such as `read_parquet`, the candidate
URI/path template for file/object storage, database relation fields for
database-backed storage, scan-adjacent `execution_attempt_ready`,
`primary_execution_attempt_blocking_reason_code`, and
`execution_attempt_blocking_reason_codes` mirrors of the review gate, parsed
placeholder names in `required_bindings`, structured `binding_requirements`
rows for handoff work, non-secret storage environment hints, copied issues and
analysis warnings, caveats, and a `review_gate`. Top-level `handoff_summary`
copies the compact routing fields most useful for reports: selected candidate
index/note, scan function, URI or database relation identifier, execution gate
booleans, ordered execution blockers, required bindings, issue codes,
warning/caveat counts, and unselected ready/direct-clean peer indexes. Read it
first for handoff routing, then inspect the full fields it summarizes. Top-level
`handoff_kind` is a machine-readable route for the draft: `no_query_target`,
`metadata_review_required`,
`context_review_required`, `runtime_resolution_required`,
`database_relation_handoff`, `binding_values_required`, or
`execution_attempt_ready`.
When a selected template comes from partition metadata, binding requirements
include partition handoff hints (`binding_kind`, `partition_scheme`,
`partition_column`, and `partition_granularity`) while still requiring caller
runtime values. Partition placeholders that do not match a declared partition
column, and ordinary dataset/storage placeholders, may include
`candidate_column_matches` when placeholder names match dataset columns; these
are best-effort handoff hints, not inferred runtime values.
The pre-draft `route_card.binding_example` and `binding_examples[]` fields use
illustrative reviewed placeholder values, such as `event_date='2026-06-30'`,
only to show where runtime bindings land in the template.
`candidate_column_match_status` flags absent, singular, or ambiguous hint sets;
ambiguous rows need review before choosing any source column.
Binding rows identify the placeholder source text and explicitly report when
DoxaBase has not inferred derivation or runtime values. `review_gate` separates
`blocking_reason_codes` from `all_issue_codes` while preserving `reason_codes`
as a legacy alias for blocking reasons. It also exposes
`binding_values_required`, `ready_for_execution_attempt`,
`primary_execution_attempt_blocking_reason_code`, and
`execution_attempt_blocking_reason_codes`. The primary execution blocker is the
first item from the ordered blocker list, or `None` when no execution-attempt
blocker remains. `ready_for_execution_attempt` is true only when the
graph-metadata review gate is clear, no runtime endpoint/credential or object
resolution remains recorded, and no required binding placeholders remain in the
selected template. The scan card mirrors those execution-attempt fields
so a present `scan.uri_template` or `scan.relation_identifier` is not mistaken
for execution permission. It may add handoff-only blockers such as
`query_context_has_other_blockers` for clean selected candidates with bad
siblings, or `scan_function_not_inferred` when DuckDB has no file-scan function
for a selected file/object storage-layout shape. Database relation handoffs
intentionally keep `scan.function=None`; their execution gate is runtime
resolution, not missing file-scan inference.
`physical_layout_path_extension_mismatch` is also a review blocker: it means a
clear candidate path extension, such as `.csv`, conflicts with the single linked
or caller-selected physical layout file format, such as `rc:Parquet`.
`physical_layout_storage_protocol_mismatch` is also a review blocker: it means
the caller explicitly paired a selected storage route with a layout format from
the wrong route kind, such as database storage plus `rc:CSV` or local file
storage plus `rc:PostgreSQLTable`. Database-backed storage still uses this
generic draft shape today, so expect `scan.function=None`,
`ready_for_execution_attempt=false`, and `runtime_resolution_required` rather
than executable SQL; `scan.uri_template` is intentionally absent there, and
`scan.relation_identifier` plus `scan.connection_reference` carry the recorded
database handoff for review. These scan fields mirror the selected
candidate's database-specific fields; if the selected database candidate came
from a dataset or partition path, `scan.relation_identifier` is absent and the
plan stays metadata-review-required. Root-only database storage
without a storage-access relation template is also metadata-review-required with
`database_relation_template_missing`; the issue's `details.repair_hint` gives
the reviewed add-template action for the storage access. The `scan` card carries
dataset-level
verification status/notes and template lineage/source verification fields so
agents can see, for example, that a dataset-owned path was verified by listing
or that an aggregate table's path came from a shared partition scheme and is
review-gated. It does not resolve endpoint profiles, credentials, object
existence, or run SQL; use it as a handoff object before deciding whether an
execution attempt is safe.

`describe_profile_run(dataset_iri, evidence_iri, limit=None)` returns profile
observations for one dataset linked to one evidence resource. It does not create
or require a persisted run node; membership is inferred from the dataset's
profile observations that link to the requested evidence IRI. The response
includes dataset and evidence summaries, top-level
`returned_dataset_profile_count`, `returned_mapped_column_profile_count`,
`returned_unmapped_column_profile_count`, `returned_profile_count`, matching
`total_*` / `omitted_*` count fields, `profile_observation_iris`,
`dataset_profile_observations`, `mapped_column_profile_observations`,
`unmapped_column_profile_observations`, and a `retrieval_note`. The default
`limit=None` is intended to retrieve the whole run even when
`describe_dataset()` is bounded; pass a positive `limit` only when a capped
payload is useful. It also works for observation-only profile runs where no map
dataset exists yet.

`draft_profile_map_updates(dataset_iri, evidence_iri)` compares one profile run
with current map facts and returns read-only review recommendations. Use it
after `describe_profile_run` when profile evidence suggests row-count snapshot
drift, mapped-column nullability changes, unmapped profiled columns, or
project-specific metric kinds that need vocabulary review. It returns
`recommendations` with `helper_name`/`helper_arguments` for accepted map-helper
updates, `metric_advisories` for project-specific profile metrics,
`type_advisories` for observed profile type findings, and a `review_note`. It
also includes `recommendation_count`, `representative_recommendation_indexes`,
`scalar_conflict_groups`, `scalar_conflict_group_count`, metric advisory counts
plus `representative_metric_advisory_indexes`, type advisory counts plus
`representative_type_advisory_indexes`, grouped
`suggested_next_action_groups` / `suggested_next_call_groups`,
`advisory_followthrough_plan`, `mixed_support_review_groups`, and flat top-level
`suggested_next_actions` / `suggested_next_calls` for compatibility. Use
`mixed_support_review_groups` before staging when one support pattern feeds both
metric vocabulary and type-review lanes.
Each metric/type advisory row also carries its row-local
`metric_advisory_index` or `type_advisory_index`.
Prefer grouped routing: `profile_map_updates`,
`profile_scalar_conflict_review`, `metric_vocabulary_review`, and
`profile_type_review` are present only when that lane has actions.
`query_context_review` can appear before those lanes when the dataset already
has physical-query metadata such as a path template or layout, but
`describe_query_context` still reports blocking physical metadata issues. Its
action points to `describe_query_context` and carries `source_query_context`
with readiness, blocking issue codes, repair group count, and the dataset route
anchor; follow it before treating profile-derived map updates as query-ready
context. The scalar
conflict lane is present when same-evidence scalar recommendations require a
choose-one decision. Grouped metric/type actions carry
`source_profile_advisory` with the source advisory kind, index field,
represented advisory indexes, duplicate group keys, duplicate advisory indexes,
duplicate profile-observation IRIs, and optional metric-only
`observed_metric_iris`, so scripts can route directly from the grouped lane
without rejoining every action to the advisory rows first. Grouped profile
map-update actions carry `source_profile_map_update` with represented
recommendation indexes, duplicate group keys, duplicate profile-observation
IRIs, route anchors, and route patterns. All grouped profile action source
blocks carry stable `route_group_key` and `route_step_key` fields; use the group
key to bridge draft lanes to profile insight bundle candidates. When these
actions are copied into `project_brief`, their nested arguments, calls, and
source route blocks are scanner-redacted for orientation safety; use
`draft_profile_map_updates` directly when you need the executable raw action
payload. If
`source_profile_advisory.mixed_support` is present on promotion or assertion
actions in both metric and type lanes, review or export those generated drafts
together before applying either lane independently.
`advisory_followthrough_plan` summarizes those grouped advisory actions by
semantic move: `define_metric`, `define_value_type`, `assert_map_type`, or
`caveat_fallback`. Use its primary call, `primary_action_kind`, graph-write
flag, advisory indexes, status counts, route keys, route anchors/patterns, and
`source_profile_advisories` when a script needs the next review move without
rejoining every advisory row. Generated mutating advisory actions already include
`profile_route_sources` in their arguments; use `source_profile_advisories` when
staging a caller-authored alternative. Match `semantic_move` plus
`primary_action_kind` when selecting a mutation; the same semantic move can
include inspect-only and staging rows.
Recommendation rows carry `recommendation_index`, the source profile
observation IRI, evidence IRI, `sample_size`, `sample_scope`, `sample_method`,
and
`profile_row_count` so agents can review whether the profile was a full scan,
sample, or ambiguous run before applying helper arguments. They also carry
`default_stageable`, `default_skip_reason`, and duplicate-group metadata so
repeated same-evidence observations can be reviewed as one representative row
without losing sibling support. `default_stageable=False` previews guardrails
such as sampled row-count recommendations that default staging will skip unless
the caller opts in, and same-evidence scalar conflicts where profile
observations propose multiple values for one row-count or nullable assertion.
For explicit non-table assets, profile row counts remain observation evidence
and are not drafted as `dataset_row_count_snapshot` map recommendations.
Those conflicts are also summarized in `scalar_conflict_groups[]`, where each
initial option carries one explicit `stage_profile_map_updates` action for a
chosen observed value. If one same-evidence scalar value is already current
after apply, sibling options route to inspection instead of a new stage call.
Option actions are exposed in the grouped
`profile_scalar_conflict_review` lane with `source_scalar_conflict` metadata,
including route group/step keys, but are not copied into the default flat
`suggested_next_actions`. Each option and lane source includes
`recommendation_contexts[]`, which repeats the profile observation, sample,
basis, observed-count, profile-row-count, and confidence fields needed to judge
support strength without rejoining against the recommendation list. It does not
mutate or stage graph changes, and it skips sampled zero-null promotions. Metric
advisories
carry `advisory_status`, `definition_found`, optional `definition`,
`promotion_patterns`, `context_patterns`, `pending_staged_promotion_iris`,
duplicate-group metadata, and structured `suggested_next_actions` for
ontology/context review. Undefined or ambiguously typed metrics with a
same-evidence pattern that names the metric as a target or map implication get
`describe_pattern`; when no matching current staged vocabulary skeleton exists,
they also get a reviewable `stage_pattern_promotion` skeleton for an ontology
`rc:ProfileMetricKind`. If such staged work is already pending, the advisory
routes to inspect/export that staged revision instead of proposing a duplicate.
Ambiguous metrics keep the existing-definition inspection action ahead of the
repair skeleton. Prose-only same-evidence patterns that mention the metric
appear as context patterns only.
The skeleton seeds its `rdfs:comment` from promotion-pattern text, rationale, or
summary only when that text names the metric IRI, local name, or normalized
local-name phrase. Otherwise it uses a generic review-first comment. Review and
tighten units, calculation, and comparison semantics before applying it
unchanged.
Type findings are outside the accepted recommendation-index set:
`physical_type` and `value_type` are persisted on profile observations as
observed evidence, and observation-only profile records now produce
`type_advisories` when they differ from or fill gaps in current map column
facts. Follow those advisories for context loading, pattern recording, or
focused `stage_map_assertion_change` calls before turning type evidence into
durable map assertions. For unmapped columns, the advisory names related
`unmapped_profiled_column` recommendation indexes so agents can stage the
column shell before reviewing type assertions.
If the `profile_map_updates` lane has a `stage_profile_map_updates` action,
review the draft and use that action as a starting point. Its
`accepted_recommendation_indexes`
defaults to the representative indexes whose rows have `default_stageable=True`,
so agents do not have to stage duplicate siblings just to preserve observation
support or accidentally stage sampled row-count or conflicting scalar rows.
Sampled row-count and same-evidence scalar-conflict representatives remain in
`representative_recommendation_indexes` for explicit review/override; for a
conflict, use `profile_scalar_conflict_review` or
`scalar_conflict_groups[].options[]` to choose at most one observed value. If
`recommendation_count == 0` and either metric or type advisories are present,
treat the draft as advisory-only: follow metric/type review lanes and do not
call `stage_profile_map_updates`, because advisory rows are not accepted
map-update recommendations. When recommendations and advisories coexist, stage
accepted map facts from `profile_map_updates`, then continue
`metric_vocabulary_review` and `profile_type_review` separately.

`plan_profile_followthrough(dataset_iri, evidence_iri, result_bindings=None,
staged_revision_iris=None, restage_stale_revisions=False)` reruns the profile
draft and materializes advisory follow-through actions from the fresh grouped
lanes. Use it after executing a generated `record_pattern` action: pass the
route-scoped `binding_key` and returned `pattern_iri` in `result_bindings`, and
the paired `stage_map_assertion_change` actions come back with
`arguments.supporting_patterns` and `arguments.profile_route_sources`
updated. The helper also returns `produced_bindings`,
`binding_resolutions`, `action_resolutions`, and fresh
`suggested_next_actions` / `suggested_next_calls`.
When `staged_revision_iris` are supplied, the helper rechecks those rows with
`check_staged_revision_apply`. It restages only when
`restage_stale_revisions=True` and the staged row's next action is
`restage_staged_revision`; it never applies the generated profile follow-up
changes.

`stage_profile_map_updates(dataset_iri, evidence_iri, accepted_recommendation_indexes=[...])`
reruns the draft, stages the accepted recommendation indexes as one grouped
reviewable `map` revision, and returns explicit staged/skipped/not-selected
item statuses plus `status_counts`, metric advisory counts, and type advisory
counts. Use it when profile-derived map changes need review before application.
When staging creates a revision, follow
`suggested_next_actions` to `check_staged_revision_apply`, then export the
seeded `export_profile_insight_review_bundle` action before reviewing or
applying it. Re-run that export after staging related metric vocabulary,
type-review, or caveat/systematisation alternatives. The staged patch uses
helper-equivalent RDF:
missing dataset shells get `rdf:type rc:Dataset`, unmapped columns get
`rdf:type rc:Column`, `rc:columnName`, and `rc:hasColumn`, and scalar
row-count/nullability changes remove old helper-owned values before adding
typed literals. Accepted indexes can still be skipped by safety guardrails,
especially sampled row-count recommendations by default; set
`allow_sampled_row_count_updates=True` only when the profile scope is the
intended durable population. If the accepted set includes multiple disagreeing
same-evidence scalar values for one row-count or nullable assertion, those
conflicting rows are skipped; choose one value explicitly after reviewing the
profile observations. Metric advisories are returned for review but are
not converted into map patches; follow
`metric_advisory_suggested_next_actions` as a separate vocabulary-review lane
when `metric_vocabulary_review_required` is true. Their compact summary is also
stored in the staged revision review note. Pass `supporting_claims`,
`supporting_patterns`, and `revision_anchors` when profile-derived map changes
already have synthesized claim/pattern rationale; caller anchors are merged with
the automatic dataset and recommendation anchors. These support links are
recorded only when at least one accepted recommendation creates a staged
revision. When one accepted recommendation represents a duplicate group, all
grouped `duplicate_profile_observation_iris` are preserved as staged-revision
support observations.
Default `stage_profile_map_updates` suggestions only auto-pass same-evidence
patterns that target or imply the dataset or recommended map resources. Keep
metric-only and type-only patterns in their advisory lanes unless you explicitly
want them to support the map patch.

`export_profile_insight_review_bundle(dataset_iri, evidence_iri, path)` writes a
grouped Markdown review bundle for staged revisions connected to one profile
run. It discovers current staged work and already-applied staged source rows
through profile evidence, supporting profile observations, related patterns, and
profile-derived anchors, then delegates the Markdown body to
`export_staged_revisions()`. Use it after staging the profile map-update
revision plus any metric vocabulary, type-review, or caveat/systematisation
alternatives that should be reviewed together. Keep the default applied-source
scan for post-apply handoffs; set `include_applied_staged_sources=false` only
when the bundle should ignore already-applied profile-map sources. Returned
candidates expose `profile_route_keys` and `profile_route_groups`, and the
Markdown review summary includes a `Profile Route Bridge` table when candidates
match draft route groups. The bridge's `Row` column uses the same `Revision N`
row number as the grouped bundle sections and repeats the candidate summary so
Markdown-only reviewers can map lanes back to detailed rows. Repeated same-lane
route groups are grouped in Markdown with a route-group count, while the JSON
payload keeps every `profile_route_key` and `profile_route_group`. It does not
stage missing advisory-lane work for you. Already-applied profile-map candidates keep
their persisted direct route source, while fresh same-lane live follow-ups are
support routes until staged separately.
The nested `export` record is the same staged Markdown export shape and carries
`shareability_review_required` / `shareability_review_status`.
Pass `fail_on_sensitive=True` when unattended or shareable profile review
exports should raise before writing if the generated Markdown contains
credential-like or secret-looking literals.

`describe_context_slice()` returns a bounded, route-explained graph slice around
seed IRIs. Profiles are intentionally explicit: `dataset_brief` starts from
dataset/table map context, bounded profile observations/metrics, and linked
lore, `pattern_brief` starts from pattern support, and `deep_lore` also
includes directly relevant revision metadata. `resource_brief` starts from
arbitrary RDF resources and returns a bounded route-explained one-hop handoff
across map, ontology, shape, observation, pattern, evidence, and history graph
roles. Dataset/deep-lore slices can also start from mapped column IRIs, profile
observations, observed profile metric nodes, or metric-kind IRIs used by profile
metrics. Deep-lore slices can start from `rc:GraphRevision` seeds to inspect
revision support, evidence, anchors,
application, restage, and alternative links. Column seeds expand to their owning
dataset plus directly targeting claims, patterns, observations, and
reconsideration lore. Profile-only column IRIs recorded with
`update_map_column=false` are object references rather than mapped column
subjects; seed their profile observation IRIs when you need that handoff.
`seed_profile_observations` preserves structured profile summaries selected by
profile/metric seeds even when the same row is older than the bounded dataset
profile list.
Use `resources[].routes`, `route_counts`, `dataset_contexts`, and
`pattern_contexts` as the reading path before raw `triples`. The response also
includes `reading_order` and a filtered `route_legend` so cold agents can follow
the intended reading protocol without rediscovering route meanings.
There is no `route_summaries` field; `reading_order`, `route_counts`, and
`route_legend` are the compact route-summary surface.
`resources[].primary_route` is the first full route object from
`resources[].routes`; use `resources[].primary_route.route` for the route id.
`resources[].surface_role` is a compact first-pass cue for whether a resource is
current map context, observation context, pattern synthesis, evidence support,
revision history, vocabulary context, validation shape context, mixed context,
or only referenced by the slice. Set
`resource_brief` slices can suggest `describe_query_context` when a seed or
direct seed-reached resource is an owning table with query repair groups or
operational warnings; this covers storage access, physical-layout,
partition-scheme, and mapped-column handoffs without making the slice a full
dataset brief. Set
`include_trig=True` when an agent needs importable TriG text for review or a
scratch capsule. `max_triples` only truncates raw triples/TriG; top-level
resources, routes, and structured contexts continue to describe the full
selected slice. Use `candidate_triple_count`, `returned_triple_count`, and
`omitted_triple_count` to decide whether to rerun with a larger limit.

`record_observation()` writes a structured `rc:Observation` or
`rc:ProfileObservation` to the `observations` graph. When evidence fields are
supplied, it also writes a linked `rc:Evidence` resource to the `evidence`
graph. Include `evidence_sources` when you need validation-clean evidence;
`evidence_summary` alone is descriptive prose. When `observed_column` names a
column that is not yet in the map,
`observed_column_name` can preserve the source-level column name without
promoting the column into current map state. For `observation_type="profile"`,
`observed_physical_type` and `observed_value_type` preserve type findings as
evidence without asserting them as current map facts.

`record_query_result()` records an externally executed query result or failure
using the same observation/evidence model. It does not execute the query. When
successful profile-like fields such as `row_count`, `sample_size`,
`value_frequencies`, or `profile_metrics` are supplied, it writes a
`rc:ProfileObservation`; failed, blocked, cancelled, or partial attempts write
ordinary observations and reject profile count fields. Use `query_source_path`
for a non-secret query file or query artifact, which is stored as an
`rc:SourceSpan` with `rc:QuerySource`; use `result_sources` for result files,
logs, or output artifacts; use `scanned_source_paths` for non-secret files,
object keys, or URI-like inputs that should become `rc:DataSampleSource` spans;
and use `scanned_source_handles` for reviewed source handles the external
runtime actually scanned. Handle-only values are stored as
`rc:scannedSourceHandle` metadata and are not copied into `sourcePath`.
When `observed_asset` is supplied, the returned record includes
`suggested_next_actions`: profile-like results start with
`describe_profile_run(observed_asset, evidence_iri)`, and all observed-asset
results include `describe_query_context(iri=observed_asset)`. Use those actions
before drafting another query plan or promoting profile-derived facts.
Dataset-seeded `describe_context_slice(profile="dataset_brief"|"deep_lore")`
also includes a bounded set of recent ordinary observations that name the
dataset as `rc:observedAsset`, so blocked or failed query-result attempts remain
discoverable from the dataset handoff. Seed the returned observation or
`evidence_iri` directly when an export should carry only one attempt.

`record_dataset_profile()` records a profile observation for one dataset and can
also update the map row-count snapshot and write an agent-authored profile
pattern linked back to the observation. Use it when a profiling result should
arrive as observation, optional current-best map context, and optional synthesis
without making three separate helper calls. `describe_dataset()` surfaces recent
dataset profile observations and their sample, row, null, distinct, and observed
value-frequency counts, plus scalar `profile_metrics` such as observed minimum
or mean values. Use `sample_scope` for the bounded population or slice profiled
and `sample_method` for how the profile was produced. Pass metrics as
`profile_metrics=[{"metric": "rc:MinimumValue", "value": ...}]`, using project
metric-kind IRIs when the base metric kinds do not fit. Use
`list_entities(type="rc:ProfileMetricKind", graph="base_ontology")` to discover
the built-in base kinds. These scalar metrics are observed profile evidence,
not constraints, shapes, allowed values, or durable map semantics by themselves.
DoxaBase rejects unknown `rc:` metric kinds to catch typos; use a full project
IRI for durable project-specific metric kinds and define it in the project
ontology once it becomes stable shared vocabulary. When checking promoted
project terms, `list_entities(type="rc:ProfileMetricKind", graph="ontology")`
includes both `base_ontology` and project ontology results; filter each returned
entity's `graph` field for project-local vocabulary. A metric item may include `target`
when the scalar is specifically about a resource narrower than the profile
observation as a whole. Profile evidence entries include source strings and
source spans when recorded. Pass `evidence_iri` when a dataset profile should
reuse a reviewed profiler-run evidence resource; this mirrors
`record_column_profile()` and avoids switching to `record_profile_bundle()`
solely to share evidence. `update_map_snapshot` defaults to true, but row
counts are written to `rc:rowCountSnapshot` only when the profile basis looks
like a full scan. Sampled or unknown-scope row counts stay as profile evidence
by default; pass `allow_sampled_row_count_snapshot=True` only when that profiled
population is the intended durable map population, or pass
`update_map_snapshot=False` for observation-only profile runs. On a brand-new
dataset that keeps the profile observation-only, `describe_dataset()` may not
find the dataset until map context is recorded; use
`describe_profile_run(dataset_iri, evidence_iri)` or profile-observation
context-slice seeds for handoff retrieval. When matching profile observations
exist, the `describe_dataset()` not-found error includes this recovery hint and
points at `record_map_dataset` for creating map context.
When the helper creates a pattern and the profile observation has evidence, the
same evidence is linked to the pattern. When `pattern_map_implications` is
omitted, the helper-created pattern points at the dataset plus any
project-specific profile metric kind IRIs named in `profile_metrics`; built-in
`rc:` metric kinds stay evidence-only. Pass `pattern_map_implications`
explicitly when a synthesis should point somewhere narrower or different.
`profile_summary.shared_evidence_iris` means an evidence IRI appears on every
returned profile observation in the bounded `describe_dataset()` response. When
older profile history is mixed with a newer shared-evidence bundle, inspect
`profile_summary.profile_run_candidates` or
`profile_summary.evidence_profile_counts` to see which evidence IRIs support
several profiles from one profiler run; use the candidate's
`profile_observation_iris` to inspect the grouped returned observations, or call
`describe_profile_run()` for full retrieval when the bounded response omits
profiles.
If a capsule only contains profile lore, `describe_dataset()` may still report
missing storage/path/layout warnings; treat those as query-planning gaps, not
profile validation failures. Check `profile_summary.handoff_note` when deciding
whether a profile-only handoff is missing physical query-planning metadata or
missing profile evidence.

`record_profile_bundle()` records one dataset profile plus zero or more related
column profiles from the same profiling pass. It composes
`record_dataset_profile()` and `record_column_profile()`, so it does not create
a special bundle ontology object. Use it when the profiler produced a
dataset-level summary and several column-level summaries that share evidence
fields or sample context. Top-level `observed_at`, `observed_by`,
`evidence_summary`, `evidence_sources`, `sample_size`, `sample_scope`, and
`sample_method` default into each column profile unless the column item
overrides them.
`value_frequencies` inputs accept `count` as a convenience alias, but returned
profile observations normalize the field to `frequency`.
Pass `shared_evidence_iri` when the dataset profile and column profiles should
all link to one shared profiler-run `rc:Evidence` resource. A column item can
override that by supplying its own `evidence_iri`.
The returned bundle includes `shared_evidence_iri` at top level for quick
run-level checks and `handoff_entrypoints` with profile observation seeds,
availability flags, structured `suggested_next_actions`, and compatibility
`suggested_next_calls` for the next agent. When both map dataset context and a
shared evidence run are available, handoff actions include
`draft_profile_map_updates` before context-slice routes.
`record_profiled_parquet_table()` records one reviewed Parquet table handoff in
one no-I/O call. It composes `record_map_table_bundle()` and
`record_profile_bundle()`, defaults the physical layout to `rc:Parquet`, creates
a stable shared evidence IRI when none is supplied, and returns the table
bundle, profile bundle, profile observation count, profile draft recommendation
count, query readiness, issue codes, and suggested next actions. Use it when an
external profiler or case-study script has already produced reviewed schema,
storage/layout, and aggregate profile facts; do not use it as a Parquet scanner
or a place to preserve raw row samples.
`record_domain_network_profile()` is the aggregate communication-network
profile helper. It records reviewed sender/recipient extractability buckets,
optional domain-pair/domain-frequency counts, shared evidence, and optional
analysis-view/caveat/pattern support. The helper does not read data, parse
addresses, infer internal-domain rules, or make network-validity claims. Values
containing `@` are rejected, and low-frequency domain-pair buckets require an
explicit privacy-review override.
In `handoff_entrypoints`, `map_column_iris` is a legacy alias for the columns
whose map facts were written by this bundle call. Prefer
`updated_map_column_iris` for that meaning, and use
`mapped_profiled_column_iris` when you need all bundled column profiles that are
mapped after the call, including pre-existing mapped columns profiled with
`update_map_column=false`.
Use `column_defaults` for repeated column options, for example
`{"update_map_column": false}` when sampled column profiles should stay
observation-only. Each `column_profiles[]` item accepts the same fields as
`record_column_profile()` and must include `column_iri`, `column_name`, and
`summary`. After recording a bundle, `describe_dataset().profile_summary` lists
shared evidence IRIs, profile run candidates, and a handoff note that can help a
later agent recognise one profiler run without walking every observation.
`describe_profile_run(dataset_iri, shared_evidence_iri)` retrieves that run
directly, including for observation-only brand-new datasets that are not yet
available through `describe_dataset()`. Bundle-created patterns support the
dataset profile observation only by default. Set
`pattern_support_scope="all_profiles"` when the pattern should be supported by
the dataset profile plus every bundled column profile. For a synthesis that
also needs claims or a hand-picked support set, collect
`describe_profile_run(...).profile_observation_iris` and call
`record_pattern(..., supporting_observations=[...], supporting_claims=[...], evidence_iri=shared_evidence_iri)`.
When `pattern_map_implications` is omitted, bundle-created patterns default to
the dataset plus project-specific top-level profile metric kind IRIs; with
`pattern_support_scope="all_profiles"`, project-specific column metric kind
IRIs and project-specific column value-type IRIs are included too. Built-in
`rc:` metric kinds and `rc:` value types remain observed profile evidence only.

`record_column_profile()` does the same for one column: it records a profile
observation with `observed_column`, can update map column metadata such as
physical type and nullability, and can write a linked profile pattern. Column
profile observations are exposed on the matching `describe_dataset().columns[]`
entry, including any observed value-frequency pairs and scalar profile metrics
supplied by the profiler. Use `sample_scope` and `sample_method` to distinguish,
for example, a full-column scan from a top-N value-frequency sample.
Scalar `profile_metrics` remain observed evidence unless a later claim, pattern,
or map update interprets them. When a column helper creates a pattern and
`pattern_map_implications` is omitted, project-specific metric kind IRIs from
`profile_metrics` and the observed project-specific `value_type` IRI become
map implications alongside the column so draft vocabulary-promotion routes can
find the supporting pattern. Built-in `rc:` metric kinds and `rc:` value types
stay evidence-only.
`update_map_column` defaults to true, so pass `false` when observed values or
counts should stay observation-only. For a profile such as "BUY/SELL appeared in
this sample, but that is not an allowed-value domain", combine
`record_column_profile(update_map_column=false)`,
`record_claim_observation()`, and `record_pattern()`.
If the column is not yet in the map, `describe_dataset()` returns that profile
under `unmapped_column_profile_observations` rather than `columns[]`. The
profile keeps the supplied column name as `observed_column_name`;
`observed_column.column_name` also uses that name as a fallback until the
column becomes a current map column.

`record_claim_observation()` writes one `rc:Observation`, one linked `rc:Claim`,
one `rc:Evidence`, and optionally one `rc:SourceSpan`. Use it for the common
claim-shaped observation pattern without hand-authoring TriG.

`record_claim_reconsideration()` writes an `rc:ClaimReconsideration` in
`observations`, optionally writes evidence, and links a newer claim to an older
claim with `weakens`, `contradicts`, `supersedes`, or `refines`. Use it when an
agent learns that a previous hunch was too broad, wrong, replaced by a better
framing, or still useful but narrower than first thought.

`record_pattern()` writes one `rc:Pattern` to the `patterns` graph and can write
linked evidence/source-span resources. Use it when several observations, claims,
or sources belong together and explain a more durable pattern or map
implication.

Map authoring helpers write current-best project facts to `map`:
`record_map_dataset()`, `record_map_analysis_view()`,
`record_map_table_bundle()`, `record_map_column()`, `record_map_caveat()`,
`record_map_storage_access()`, `record_map_physical_layout()`,
`record_map_partition_scheme()`, `record_map_relationship()`, and
`record_map_asset_transform()`. Use them when observations or patterns are ready
to become operating context for future
agents. On partial dataset updates, omit `is_table` to preserve existing
dataset/table typing. Use physical-layout and partition helpers when path or
layout verification belongs to one part of the executable catalog rather than
to the whole dataset. For storage access, set `location_kind="object"` only when
`storage_root` names the dataset object/location exactly; use `directory`,
`prefix`, or `connection` for broader roots and add path templates for
executable query planning. The helper accepts `location_kind="bucket"` as an
input alias for S3-shaped bucket/key-prefix routes and stores it as `prefix`.
Do not use `location_kind="local_path"`; local
filesystem belongs in `storage_protocol="rc:LocalFilesystemStorage"` and
`location_kind` describes the root shape. Resource-valued fields across these
helpers expect IRIs/CURIEs, not prose: use terms such as `rc:EventRow`,
`rc:Parquet`, `rc:PNG`, `rc:GeoTIFF`, or project IRIs for datasets, columns,
caveats, and relationship endpoints. Put ordinary explanation in descriptions,
notes, observations, or patterns. Common base file-format terms include
`rc:Parquet`, `rc:CSV`, `rc:JSON`, `rc:JPEG`, `rc:PNG`, `rc:TIFF`,
`rc:GeoTIFF`, and `rc:PDF`; define a project-local `rc:FileFormat` only when
the base vocabulary lacks the reviewed format.
For storage access `route_roles`, use built-ins such as `rc:ProductionRoute`,
`rc:CurrentRoute`, `rc:CanonicalRoute`, `rc:SampleRoute`, `rc:ArchiveRoute`, or
`rc:BackfillRoute`, or define project-local `rc:RouteRole` terms. Query target
candidates inherit these roles for reviewed route selection.
For `record_map_partition_scheme`, `redundant_partition_key` is one of those
resource-valued fields, usually the partition column IRI/CURIE. Keep literal
placeholder names such as `date` or `event_date` in `path_template`.
`schema_stability` accepts `rc:FixedSchema`, `rc:InferredSchema`, or
`rc:VariableSchema`. Layout verification status accepts
`rc:UnverifiedLayout`, `rc:GeneratedFromManifestLayout`, `rc:CandidateLayout`,
`rc:VerifiedByListingLayout`, `rc:VerifiedByQueryLayout`, or
`rc:ContradictedLayout`.
Use `record_map_analysis_view()` for current-best named logical analysis
populations, denominator definitions, and reviewed query recipes that are not
physical routes. It writes an `rc:AnalysisView`, optional
`rc:AnalysisDenominator`, and one or more optional
`rc:ExecutableQuerySnippet` resources in `map`. Use `query_snippets=[...]` for
multiple reviewed recipes, and do not combine that list with legacy
single-snippet fields such as `query_text`; `query_snippets=[]` clears snippet
links.
`describe_analysis_view()` reads that logical definition, while
`describe_query_context()` reports `readiness="logical_analysis_view"` and does
not offer missing-storage repair groups for the view itself.
Use `record_map_table_bundle()` when reviewed table schema/storage/layout facts
are already available from an external profiler, Parquet footer inspection, or
catalog. It is a no-I/O convenience wrapper over the ordinary map helpers: it
records the table, columns, optional storage access, and optional physical
layout, then returns `describe_dataset` and `describe_query_context` follow-up
actions. It does not infer physical types or replace profile evidence helpers.
When the same reviewed Parquet manifest also contains aggregate profile facts,
prefer `record_profiled_parquet_table()` so the map facts, shared profile run,
and profile/query follow-up actions stay connected.
Supplied same-subject fields replace the helper-owned predicates on the
resource being recorded, but incoming convenience links such as
`record_map_caveat(targets=...)`, `record_map_storage_access(datasets=...)`,
and `record_map_column(table_iri=...)` add links and do not prune old incoming
links. To narrow links, update the owning dataset/table helper when possible,
stage a reviewed assertion change, or use `replace_graph_triples()` for exact
maintenance. For scalar helper-owned literal fields, omitting a parameter
preserves existing values, while passing an explicit empty string includes that
predicate in the replacement set and clears it.
`record_map_relationship()` supports foreign keys, shared
identifiers, derivations, and aggregations; for aggregations, pass
`group_by_columns` plus `aggregated_columns` mappings with `target_column`,
`source_columns`, optional `aggregation_function`, and optional
`within_group_ordering`. For no-column asset-level derivations or aggregations,
pass `source_datasets` and `target_datasets`; the singular `source_dataset` and
`target_dataset` arguments remain compatibility shortcuts. When role or
precedence matters for asset endpoints, pass `source_endpoints` or
`target_endpoints` entries such as
`{"dataset": "ex:RawImages", "role": "primary image input", "order": 1}`.
Endpoint specs also write the compatibility `sourceDataset` / `targetDataset`
edges. Relationship column fields must point to column
resources already recorded as `rc:Column`; known data assets, datasets, tables,
and fresh unrecorded IRIs are rejected in those slots.
For `relationship_type`, use helper tokens such as `foreign_key` or the
matching core class CURIE/full IRI such as `rc:ForeignKey`; descriptions always
return the normalized helper token plus the RDF class IRI.
Use `record_map_asset_transform()` for asset-level derivations or aggregations
that need reviewed filters, selection rules, per-output formulas, output
functions, or tuple grain. Its tuple-grain components accept exactly one of a
real `column`, a `dataset`, or a reviewed `expression`; do not invent fake
columns to represent non-tabular grain.
Dataset descriptions expose all partition columns as
`partition_columns`; the older singular `partition_column` field remains as a
compatibility shortcut to the first returned column. Treat `partition_columns`
as unordered unless a future response explicitly carries ordering metadata.
Relationship descriptions expose `relationship_kind` as the RDF class IRI and
`relationship_type` as the helper-style token such as `foreign_key` or
`aggregation`, even when the write helper received an RDF class alias.

`record_graph_revision()` writes metadata to `history` about changed graph
roles, included review/export graph roles, rationale, supporting resources,
revision anchors, validation results, export paths, and graph-count snapshots.
It does not compute diffs or apply graph edits. Use support links for evidence
behind a revision; use anchors for resources the revision is about.

`record_staged_revision_review_decision()` writes a history-only reviewer
disposition for one staged revision without applying its patch payload. Use it
after reviewing an informational `noop` or already-effective stale source and
deciding the staged row should be closed rather than restaged again. Supported
decisions are `accepted_elsewhere`, `superseded`, `discarded`, and
`no_effective_change`. The record is an `rc:StagedRevisionReviewResolution`
linked to the staged source with `rc:resolvesStagedRevision`; the staged source
remains visible in full history with `review_resolution`, but is no longer
selected by `current_staged_work_only=True` frontiers. The helper refuses
current apply/restage/repair targets unless `allow_mutation_target=True` is
passed after explicit review.

`stage_graph_revision()` writes a reviewable staged revision to `history`
without mutating the target graph. Pass Turtle payloads in `additions` and/or
`removals`, set a stance such as `rc:ExploratoryHunch` or
`rc:CandidateRevision`, and choose a `validation_scope`. The helper parses the
patch RDF, previews before/after counts, runs SHACL validation over the preview,
and records ordered `rc:GraphPatch` entries for later review. Each patch has an
`rc:patchSequence` value; describe, export, check, and apply use that recorded
preview order. When validation reports results, the staged revision stores
linked `sh:ValidationResult` diagnostics with focus node, result path,
constraint, severity, value, and messages where pySHACL provides them.
Staged patch targets cannot be `history`, because staging metadata is itself
written there and would make the target snapshot immediately stale. Use
`record_graph_revision()` for durable history notes.
The immediate staged record also returns its `summary`, `rationale`,
`review_note`, and `review_recommendation` so scratch logs and wrapper payloads
do not need a second describe call just to show the proposal headline.
Pass `restages_revision=<stale_revision_iri>` when this staged patch is a
caller-authored repaired or rebased successor for stale work. The helper records
`rc:restagesRevision` / `restaged_from` while preserving the exact new payload
you provide. If the stale source already has `restaged_by` /
`current_restaged_by`, inspect or target that current successor instead; the
helper rejects parallel successors.

`stage_query_physical_layout_repair()` is the narrow staged helper for a
`missing_physical_layout` query repair after storage is already linked. Pass the
dataset IRI, reviewed layout IRI, reviewed file format, and rationale; optional
verification fields become physical-layout metadata. It stages the layout
resource and dataset `rc:hasPhysicalLayout` link together, preserving review
rationale before agents check/apply the row and rerun query planning. It also
accepts `profile_route_sources` for profile `query_context_review` lanes.

`draft_map_assertion_change()` previews the same reviewable add/remove/replace
for one `map` assertion without writing a staged revision. Pass `subject`,
`predicate`, optional `object`, a `rationale`, and `change_kind` (`"add"`,
`"remove"`, or `"replace"`). It returns addition/removal Turtle payloads, patch
count previews, validation fields, impact entries, assertion support, the compact
`judgement_panel`, and `stage_arguments` for the write step. Use it when the
question is whether a single assertion should change; follow
`suggested_next_actions[0]` only after the draft support, impacts, and semantic
risk justify staging.

`stage_map_assertion_change()` stages that reviewable add/remove/replace. For
typed or language-tagged literals, also pass `object_datatype` or `object_lang`;
the helper will author the corresponding typed/language-tagged Turtle instead of
a plain literal. It calls `describe_assertion_support()` before staging,
generates the Turtle patches, links related observations/claims/patterns/evidence
and revision anchors, and stores an assertion-support summary in the staged
revision review note. The response includes top-level `revision_iri` as an alias
of `staged_revision.revision_iri`. The returned `judgement_panel` is the compact
reviewer view: headline, current/proposed values, semantic risk level/reasons,
value-type context, reasons the current value may be intentional, caveat scopes,
strongest related-lore routes, impact spotlight entries, and safety notes. For
physical type changes, the panel includes current `rc:valueType` resources and
any declared `rc:requiredPhysicalType`. `target_value` names the requested object
for add, replace, and remove changes; `removed_value` is populated for remove
changes so reviewers do not have to interpret legacy `proposed_value` as the
value being removed. For exact removals, `removed_value` reflects the matched
graph triple, including datatype or language-tag context. Use it for common
assertion changes before reaching for generic `stage_graph_revision`.
It also accepts `restages_revision` for the common case where a stale
single-assertion candidate should be replaced by a caller-authored add, remove,
or replace patch instead of mechanically replaying the old payload.
When testing a changed singleton assertion such as `rc:physicalType`, a
competing `add` may correctly fail validation while an explicit `replace` stays
reviewable. After applying any staged assertion, re-run apply checks for sibling
revisions before relying on earlier readiness.
For `replace`, the generated patch set adds the requested assertion and removes
current same-subject/predicate values except the requested object. The recorded
patch sequence shows the exact preview/apply order. If the requested value is
already present on a multi-valued predicate, treat the replace as mainly a
removal of the other current values and review their support routes before
applying.

`stage_systematisation()` stages one or more caller-authored RDF framings for a
modelling hunch. Pass `summary`, `intent`, optional `anchors`, and a list of
`framings`. Each framing can use `graph` + `content` shorthand or full
`additions` / `removals` patch lists. A framing may also include
`review_note` / `review_recommendation` prose to say what the agent thinks the
proposal is doing and whether it is preferred, risky, obsolete, or worth keeping
as an alternative. Later framings are linked as alternatives to the first by
default. Use `shared_additions` / `shared_removals` when several framings should
validate against the same provisional context. Shared patches may include
provisional `shapes`; staged shapes are active during the preview SHACL
validation for each framing. This is a drafting and validation scaffold, not an
ontology decision engine. Anchors are recorded as `rc:revisionAnchor` metadata
on each staged revision and are also repeated in rationale text for readability.
The returned `SystematisationDraftRecord` carries
`result_kind="systematisation_draft"`, readable `warnings`, machine-readable
`structured_warnings`, a draft-level `next_action_queue`, and
`next_action_queue_items` / `next_action_queue_item_counts` /
`semantic_review_required_queue_counts`, plus `suggested_next_actions` /
`suggested_next_calls`. The queue uses the same apply-check grouping as
staged-revision exports, so callers can separate `repair_or_replace` framings
from `apply_after_review` framings immediately after staging. Queue items expose
the same resolved-target and semantic-gate fields as grouped export summaries.
Rows in `staged_revisions[]` carry `framing_index` and `framing_label` when
they came from `stage_systematisation()` or `stage_pattern_promotion()`, which
lets automation map revisions back to caller-authored framings without relying
on parallel list positions.
When later framings actually default-linked to a first framing that did not
route to `apply_after_review`, `structured_warnings` includes
`warning_code="first_alternative_anchor_not_ready"` and
`suggested_rerun_arguments={"link_alternatives": False}`; in that case the first
`suggested_next_actions` entry is a complete `stage_systematisation` rerun call
with explicit alternative routing. Per-framing `alternative_to` values reroute
siblings without that warning. Per-framing `alternative_to_framing_index` points
to an earlier framing in the same call when a generated or hand-authored rerun
needs explicit sibling routing before the target revision IRI exists. When
multiple framings share `ontology` or
`shapes` patches, `structured_warnings` includes
`warning_code="shared_semantic_context_applies_to_all_framings"` and suggested
rerun arguments naming the shared graph roles and original shared patch source
indexes to move into per-framing patches if fallback alternatives should avoid
that provisional semantic context. The warning also carries
`shared_patch_summaries` and
`fallback_revision_iris_with_shared_semantic_context` for structured inspection.
If the staged rows already exist and semantic review has selected which
framings should keep shared ontology/shapes context, call
`draft_systematisation_shared_context_rerun(revision_iris=[...],
shared_context_target_revision_iris=[...])`. It returns a read-only
`stage_systematisation_arguments` payload with shared context patches copied
into only the selected framings' additions/removals, avoiding manual Turtle
copying from `describe_staged_revision`.
Pass `profile_route_sources` when a caller-authored framing is meant to resolve
a route from `draft_profile_map_updates`, for example
`profile_route_sources=[query_action.source_query_context]` for a
`query_context_review` repair. Top-level explicit route sources are persisted on
each staged framing as direct profile review routes, so
`export_profile_insight_review_bundle()` can close that lane instead of treating
the revision as support-only context. When multiple framings close different
semantic moves, put `profile_route_sources` or `profileRouteSources` on each
framing object; framing-level sources are recorded only on that staged
revision. The returned `profile_route_source_count` echoes how many usable
unique sources were persisted; a provided input with count `0` emits a warning
and usually means the source block was shaped incorrectly.

`stage_map_assertion_change()` also accepts `profile_route_sources`. Preserve the
generated action's `arguments.profile_route_sources` when a profile type-review
assertion is meant to close the selected advisory route. The returned
`profile_route_source_count` reports how many usable source blocks were stored.
Profile insight review bundles reserve `direct_action` for persisted route
sources; shared live draft support is not enough to close a lane.

`stage_pattern_promotion()` stages one or more caller-authored RDF framings
supported by existing `rc:Pattern` resources. Pass pattern IRIs and framings;
the helper records the selected patterns as support, rolls up their supporting
observations/claims/evidence, uses pattern targets and map implications as
revision anchors, and delegates validation/review packaging to
`stage_systematisation()`. It accepts `profile_route_sources` and forwards them
to `stage_systematisation()`, so promotion calls selected from
`advisory_followthrough_plan` can persist explicit profile review route closure.
It does not apply the changes or infer the graph shape. It returns the same
`systematisation_draft` routing fields as `stage_systematisation()`.

`describe_graph_revision()` returns compact revision context: summary,
rationale, `record_kind`, changed/included graph roles, graph snapshots with
counts and `sha256:<hex>` content digests, validation result, structured
validation diagnostics, export path, `applies_staged_revision` for applied events,
`applied_source` compact source context for applied staged revision events,
revision anchors, supporting observation/claim/pattern/evidence links, and
applied-event suggested calls to inspect the event diff.
It also includes `snapshot_evidence`, which classifies whether RDF history
metadata and SQLite snapshot rows are both present for exact diff/drift work.

`describe_revision_snapshot_evidence(revision_iri)` returns just that snapshot
handoff status for a revision IRI. Use it after imports when you need to know
whether the capsule has `history_missing`, `history_only_count_digest`,
`history_plus_snapshot_rows`, or `snapshot_rows_without_history`. The last case
usually means a workflow-only RDF bundle was paired with snapshot JSON: the
snapshot rows imported, but normal revision helpers still need the project or
history RDF records. Revision list, detail, and lineage responses promote
snapshot-evidence import actions to top-level `suggested_next_actions`; list
and lineage routing use queue `complete_handoff_import` before exact diff or
stale-drift inspection.

`list_graph_revisions()` returns compact history rows for `rc:GraphRevision`
resources, newest first. Each row includes summary, revision type/stance,
record kind, created time, changed graphs, validation headline, patch payload
presence/count, relation links such as `applied_by`, `applies_staged_revision`,
`alternative_to`, `current_alternative_to`, `restaged_from`, `restaged_by`, and
`current_restaged_by`, plus `stale_resolution_state` and optional staged
apply-check status, summary, recommended resolution, validation-skipped reason,
blockers, drift summaries, and suggested actions when `include_apply_checks=True`.
Rows also carry `snapshot_evidence` so list consumers can see whether exact
snapshot rows are present without opening the revision detail first.
When apply checks are present, each row also carries `next_action`, a compact
advisory route derived from status, stale/restage state, and the structured
suggested actions. The response-level `next_action_queue` groups returned rows
into queues such as `apply_after_review`, `restage_after_review`,
`repair_or_replace`, `inspect_already_applied`, and `informational`.
`next_action_queue_items` is the machine-readable companion: each item names the
queued `row_iri`, `resolved_target_iri`, `resolved_target_record_kind`, whether
`row_is_target`, the selected tool/call, row status fields, and alternative-gate
fields. When returned rows compete as alternatives, items also carry
`alternative_set_iris`, `alternative_set_source_iri`, and
`alternative_set_role` for every member, including the source row. Use it when a
queued stale source redirects to a refreshed successor or applied event, or when
an `apply_after_review` row still requires semantic review. The
`next_action_queue_item_counts` and
`semantic_review_required_queue_counts` dictionaries are scoped to the same
returned page as `next_action_queue`. `count` and `total_count` are the
filtered total before pagination, while `returned_count` is the returned page
length; prefer the explicit alias fields in generic pagination scripts.
Most count/digest-drift conflicts stay in `restage_after_review`, but stale
single-assertion adds or authored replacements for curated singleton slots with
exact same-slot drift route to `repair_or_replace` and include a
`stage_map_assertion_change` replacement suggestion that preserves
`restages_revision`. Current guarded slots are `rc:rowSemantics`, column
`rc:physicalType`, column `rc:nullable`, and data-asset `rc:schemaStability`.
`returned_application_status_counts`, `returned_stale_resolution_state_counts`,
and `returned_staged_validation_status_counts` summarize the returned page, not
unseen paginated rows. Full lists may therefore include handled historical rows
such as stale originals with `application_status="conflict"`.
`returned_current_staged_work_application_status_counts` is also page-scoped, but
counts only returned rows where `is_current_staged_work=True`; use it for a
quick live mutation-queue status without losing historical rows from the page.
Use `record_kind`, `application_status`, `staged_validation_status`, and
`stale_resolution_state` filters to find rows such as applied events,
mechanically ready staged proposals, rows with stored staged-time validation
failures, unresolved stale sources, or handled stale sources without
hand-filtering the full list.
Each row also includes `is_current_staged_work`; pass
`current_staged_work_only=True` to keep only staged patch rows that still need
review, repair, restage, or application, excluding handled stale originals and
already-applied sources. When a row is not current staged work,
`not_current_staged_work_reason` explains whether it is an applied source,
superseded by restage, an applied event, or another history/export/import
record.
Filtering by `application_status` or `stale_resolution_state` automatically
computes apply checks for patch-backed revisions, as does
`current_staged_work_only=True`.
`describe_revision_lineage(revision_iri)` takes one staged source, restaged
successor, or applied event IRI and returns the compact graph-level relationship
card around it: selected row/role, `selected_revision_iri`, paired
staged/applied row when visible, `paired_revision_iri`, applied and staged
revision IRIs, `applied_source_revision_iri` for the staged row that actually
applied, restage chain, alternatives, related revision IRIs, latest/current
pointers, warnings, and next-action routing. Use it when the
question starts from a revision IRI rather than a resource IRI. It is
read-only and does not include patch payloads or arbitrary graph-version
snapshots; use staged, applied-diff, or snapshot helpers for those. Exact diff
availability still comes from the nested row `snapshot_evidence`, but lineage
warnings call out count/digest-only or orphan snapshot states so agents do not
miss import-recovery work. `next_action_queue_item` mirrors list queue items for
the selected row, including `resolved_target_iri` when the lineage next action
points at a successor or applied event.
`list_resource_revisions(resource_iri)` returns revision rows that explicitly
touch one resource through `rc:revisionAnchor`, exact subject/predicate/object
URI mentions in staged patch payloads, or an applied event whose staged source
matched the resource. It filters before pagination and wraps each normal
`list_graph_revisions()` row under `revision`, adding `revision_iri`,
`match_types`, `patch_mentions`, `applied_source_revision_iri`, and
`applied_source_patch_mentions`. Patch mentions are compact role-aware flags,
not patch content; call `describe_staged_revision()` for the full payload.
The top-level collection is `revisions`; `count` and `total_count` are the
filtered total before pagination, and `returned_count` is the returned page
length.
`timeline` is the compact chronological view of the returned page. It is useful
for first-pass resource-history answers because each event carries the
resource-match roles, apply/restage links, and resolved next-action target
without opening a lineage card. It is still page-scoped; check `timeline_note`,
`returned_count`, and `total_count` before treating it as complete history.
Use `current_staged_work_only=True` for the resource-scoped live
mutation-review queue. It filters before pagination and computes apply checks
automatically, like the graph-level filter. Do not use
`include_patch_mentions=False` as a live-work shortcut when unanchored
patch-only work may exist; it can hide the very rows you are looking for.
Rows also expose `patch_mentions_incomplete` /
`applied_source_patch_mentions_incomplete` plus unreadable counts when stored
patch payloads were missing or unparseable during resource matching. The
top-level `patch_mention_scan` summarizes complete/incomplete/not-requested
scan status and flags `omitted_match_risk` when unreadable patch payloads may
have hidden unanchored patch-only matches. Its unreadable revision count is a
distinct staged/source revision count across the pre-pagination scan, not a
returned-row count, and `omitted_match_risk` is a coarse absence-risk signal.
`describe_resource_revision_lineage(resource_iri, revision_iri)` takes one of
those rows and returns a compact resource-centric lineage card with the selected
row, `selected_revision_iri`, visible paired staged/applied row,
`paired_revision_iri`, `applied_source_revision_iri` for the staged row that
actually applied, related revision IRIs, selected next action, patch scan status,
and optional resource-filtered applied diff summary.
`current_revision_iri` mirrors `current_staged_revision_iri` when the lineage row
or restage successor is still current staged work, matching batch-restage naming.
`latest_revision_iri` / `latest_role` mirror graph lineage's latest family
pointer and can name an applied event after the current staged successor has
been applied. It also carries graph-level `restage_chain_iris` and
`alternative_revision_iris`, so a resource-first handoff can see sibling
alternatives without a separate generic lineage call. `next_action_queue_item`
provides the selected row's compact resolved-target card and, for visible
source/alternative rows, carries `alternative_set_iris`,
`alternative_set_source_iri`, and `alternative_set_role` like list/export queue
items.
It is not a full graph-version browser and does not replace
`describe_staged_revision()` when patch content is needed.
`application_status="validation_failed"` means the current replay reached SHACL
validation and failed. `staged_validation_status="failed"` means the stored
staged-time validation failed; it still finds rows that later became live
`conflict` entries after graph drift.
`drift_detail="summary"` is the default list mode: snapshot drift rows keep
counts, digests, drift relevance, overlap arrays, and added/removed exact-change
counts but omit exact changed-triple arrays. Use `drift_detail="exact"` when you
need those arrays in the list response, or call `check_staged_revision_apply()`
for a focused exact payload.
The drift row shape is the same as the apply-check shape, except list summary
mode may set `exact_changed_triples_included=False` and leave changed-triple
arrays empty.

`describe_staged_revision()` returns staged patch payloads, stance, review
notes/recommendations, validation status, structured validation diagnostics,
support links, revision anchors, count previews, optional `judgement_panel`, and
deterministic impact review context for important consequences of the patch. The
judgement panel is present for simple single-assertion `map` changes that still
replay cleanly. Impact entries are not an apply gate; they make nearby lore
visible when a proposal removes a caveat, changes a type, changes nullability,
changes row/grain signals, changes layout/path assertions, or removes
documentation from a subject that also has semantic
changes. Caveat impact values include the caveat description, impact, and
severity inline when those facts are known. `restaged_from` is present when the
staged revision was created by replaying an older stale proposal against current
graph state. `restaged_by` is present when this staged revision is the stale
source for a later refreshed proposal; `current_restaged_by` follows that chain
to the latest known successor for action routing. `restage_reason` gives a
compact "why this was restaged" summary when it can be derived from the recorded
rationale. `applied_by` and `application_status="already_applied"` are present
when this staged revision already has an applied revision event.
Pass `include_current_apply_check=True` when a one-revision review needs compact
live apply status beside the patch payload. `current_apply_check` includes
status, decision, `routing_decision`, blockers, validation headline, drift
summaries, compact `next_action`, and suggested next actions, but omits full patch checks and
validation result payloads.
`export_staged_revision()` writes a Markdown review bundle with the current
apply-check status, diagnostics, and impact review before patch payloads. Stale
exports include conflict status, count or digest drift, validation-skipped reason, and
suggested next calls as of export time. When the live apply check reports
semantic risk, it may add a `Semantic Review Warning` before the apply check even
if the compact judgement panel is unavailable because the proposal is stale. For
simple single-assertion `map` changes that still replay cleanly, it reconstructs
a `Judgement Panel` section so the export carries values, value-type context,
rationale, caveats, routes, and safety notes from the JSON review surface.
When the panel cannot be replayed, `stored_review_context` may still summarize
persisted review/support metadata and exports render it as `Stored Review
Context`; it is not a replayed panel. The export also includes `Linked Support`
when the revision records supporting observations, claims, patterns, or
evidence, so single ontology or shape promotion reviews can show their evidence
chain. Evidence entries include recorded sources and source spans, including
path, section, and line labels when available, so reviewers can follow linked
support from the Markdown artifact alone.
Restaged exports include a top metadata `Restage headline` before the current
apply check. Stale original exports include a top metadata `Restaged by` line
when a refreshed successor already exists. Suggested export actions use
revision-derived `/tmp` filenames with a short hash to reduce collisions; callers
may override them with run-specific paths. Pass `fail_on_sensitive=True` when
unattended or shareable Markdown review exports should raise before writing if
the generated bundle contains credential-like or secret-looking literals.
Returned staged Markdown export records also set
`shareability_review_required=True` and
`shareability_review_status="required_not_completed"`; scanner-clean review
Markdown still needs explicit shareability review before it leaves the intended
project context. They also expose preflight-style `decision`, `scanner_clean`,
`would_block_sensitive_export`, `shareability_hints`, `artifact_disposition`,
and `git_safe` fields.
`export_staged_revisions()` writes one Markdown review bundle for several staged
revisions in caller-chosen order; its summary table includes each staged
revision's current apply status, decision, current validation state, and
staged-time validation result. Bundles with restaged revisions include a
`Restage Context` section near the top. When an alternative's stored target has
itself been restaged, grouped Markdown also includes `Alternative Context` so
reviewers can compare against the current successor without reconstructing that
lineage by hand. When staged rows carry profile route sources, grouped Markdown
also includes a compact `Profile Route Bridge`; structured summaries expose the
same `profile_route_keys` and `profile_route_groups` fields. Pass
`executive_summary` when the comparison needs an
agent-authored synthesis at the top of the artifact.
The returned record also includes `revision_summaries`, a machine-readable copy
of the grouped status rows with current apply status, blockers, validation
state, alternative/restage links, authored review recommendations, live
`apply_recommended_resolution` guidance, effective `summary_recommendation`
text matching the grouped Markdown table, recommendation source/scope fields,
per-row shared-context patch counts/graphs, per-row `next_action`, and
suggested next actions. Grouped Markdown and
`bundle_summary.next_action_queue` expose the same compact next-action buckets
for routing; the older recommended queues remain for compatibility and broader
review grouping.
Duplicate input revision IRIs are normalized to first-seen order before summaries
and queue counts are built.
Stale sources that already have `restaged_by` point suggested actions at the
current refreshed successor instead of another restage. `current_restaged_by`
follows deeper restage chains while preserving direct `restaged_by` provenance.
`current_alternative_to` follows restage successors while preserving the stored
`alternative_to` provenance link.
The returned `bundle_summary` counts apply statuses and stale-resolution states,
lists unresolved stale sources, handled stale sources, ready successors, and a
deduped `recommended_review_iris` set. It also lists validation-failed revisions
whose patches replay but whose preview validation does not conform.
`recommended_mutation_review_iris` is the broad compatibility queue for
proposals that may still need restage, repair, apply, or manual mutation
decisions. Narrower mutation routes split that set into
`recommended_apply_or_restage_review_iris` for apply/restage decisions,
and `recommended_repair_review_iris` for validation-failed or patch-conflict
repair work. `recommended_applied_inspection_iris` covers already applied
staged revisions that are useful context but not mutation targets.
`next_action_queue` is the most direct routing surface for autonomous scripts:
it groups current per-row action hints without requiring callers to join apply
status, stale state, recommendation source, and suggested action fields by hand.
When the concrete follow-up target can differ from the queued row, use
`bundle_summary.next_action_queue_items[].resolved_target_iri`; its
`row_is_target` flag is false for redirects such as handled stale sources that
point at an applied event. The bundle also exposes
`next_action_queue_item_counts` and `semantic_review_required_queue_counts`, so
queue-only scripts can notice semantic review gates inside `apply_after_review`.
Grouped Markdown mirrors semantic risk and alternative gate status in the
`Resolved Targets` table for Markdown-only review.
For export-only handoffs from systematisation drafts, use
`bundle_summary.shared_context_graphs`,
`bundle_summary.shared_context_patch_summaries`,
`bundle_summary.fallback_revision_iris_with_shared_semantic_context`, and
`bundle_summary.shared_semantic_context_warnings` to recover shared ontology or
shape context that applies to fallback alternatives.
For a single cross-lane worklist, read `bundle_summary.review_sequence` first:
it orders the queue items into inspect-redirect, repair, restage, review/apply,
and recheck phases with row numbers, summaries, resolved targets, tools, and a
short reason. Grouped Markdown mirrors this as `Review Sequence` above the
lower-level `Review Queues` section.
For RDF handoffs imported without companion snapshot JSON,
`bundle_summary.snapshot_evidence` is the structured import gate: `complete`
false means at least one included row lacks exact stored snapshot rows, and row
`suggested_next_actions` point at `import_revision_snapshots` just like the
Markdown `Snapshot Evidence` table. When `complete` is true, grouped Markdown
still includes a compact positive `Snapshot Evidence` confirmation for human
reviewers. This does not change `next_action_queue`, which remains focused on
review/apply routing. The same incomplete condition is repeated in
`bundle_summary.warnings`, so grouped Markdown shows the handoff preflight before
`Review Queues`.
`bundle_summary.warnings` calls out sequencing hazards, including grouped
ready/no-op reviews on the same changed graph that should be re-checked after
each apply, and source-only bundles whose recommended review target is outside
the current bundle. `post_apply_recheck_revision_iris` gives scripts the
affected revision IRIs for pre-apply grouped-review hazards.
`sequential_apply_recheck_candidate_iris` is a clearer alias for the same list.
Grouped Markdown exports include a `Review Queues` section mirroring the
recommended-review sets, derived next-action buckets, apply/restage, repair,
applied-inspection, and sequential apply recheck candidate buckets.
They also include a `Review Sequence` table above those buckets when queued work
exists, giving reviewers an ordered route through inspection, repair, restage,
apply review, and post-apply recheck phases.
Relative export paths are resolved from the repository root and returned as
normalized absolute paths.

`check_staged_revision_apply()` previews whether one staged revision can be
applied without mutating graph state. It reports already-applied state,
per-patch count drift, graph snapshot digest drift, preview triple counts,
validation status, semantic risk, and a top-level `can_apply` flag. Read
`status`, `summary`, and
`semantic_risk_level` first; use
`decision`, `routing_decision`, `blocking_reasons`, `validation_skipped_reason`,
`recommended_resolution`, `count_drifts`, `snapshot_drifts`, and
`suggested_next_actions` to decide whether to review then apply, inspect an
applied event, review validation diagnostics, or restage after conflicts.
`routing_decision` is derived from `next_action` and can be more specific than
`decision` for stale conflicts.
`superseded_by_restage` means the staged source already has a refreshed
successor; inspect that successor instead of applying the old source.
`inspect_restaged_source_validation_failure` means a same-payload restaged
successor is mechanically ready, but its source failed staged-time validation
and current graph state may be filling the semantic gap; inspect/export it and
stage a repair or alternative before applying. A revised conforming successor
created with `restages_revision` still carries the source-failure warning, but
routes like an ordinary ready row after review.
For `ready` checks with `semantic_risk_level` of `attention` or `high`, the
apply action is labelled `Apply only after semantic review`. For conflict
checks, the review action includes `include_current_apply_check=True` so the
next staged-revision inspection reloads the current blocked status.
The response includes both `staged_revision_iri` and `revision_iri`; the latter
is a script-friendly alias for copied payloads.
It also includes `restaged_by`, `current_restaged_by`, and
`stale_resolution_state` so direct apply checks can route handled stale sources
the same way revision lists and exports do. When a stale source already has a
successor, compact `next_action` points at `current_restaged_by` and suggested
mutations omit another mechanical restage; the summary headline also starts
with handled-by-restage wording even though the historical graph-state status
may remain `conflict` or the old source may still report
`validation_failed` with preserved diagnostics.
`noop` means replay validates but has no effective graph delta; suggested
actions point to inspection/export rather than apply. `triples_to_add` and
`triples_to_remove` are effective deltas for the current preview, and
`patch_checks` records effective add/remove counts plus already-present/absent
payload triples for partial or no-op replay.
If a stale count/digest conflict has zero effective add/remove delta across all
patches, it remains `status="conflict"` with drift blockers but compact
`next_action` routes to `inspect_no_effective_change` in the `informational`
queue and restage is omitted from suggested mutations. This means the payload is
already effective in current graph state, not that the staged revision has an
applied event; reserve `already_applied` for durable `rc:appliesStagedRevision`
history.
`count_drifts` gives expected/current counts and deltas, plus whether the staged
patch triples themselves are currently present, absent, or mixed in the target
graph. `snapshot_drifts` gives staged/current `sha256:<hex>` digest mismatches,
including same-count graph changes. For new revisions, `snapshot_drifts` also
includes exact triples added to and removed from the target graph since the
stored snapshot, a `drift_relevance` hint, and any patch-subject or
patch-predicate, patch-object, or revision-anchor overlaps. It also includes a
capped `changed_resources[]` summary and
`changed_resource_suggested_next_actions` for resource-level review routing
before expanding raw triples.
`no_patch_subject_overlap` is useful triage context, not semantic approval to
apply. Predicate and object overlap can be broad; `broad_patch_object_overlap`
marks weak object overlap through shared class/type vocabulary such as
`rc:Dataset` or `rc:Table`. Anchor overlap means exact drift touched a resource the staged
proposal named as review context. Older revisions may report
`exact_changed_triples_available=False` if no snapshot rows were stored.
Suggested actions are ordered review-first; mutation calls come after
inspection/export suggestions.
Staged-revision `next_action`, `first_safe_next_action`, and effect-annotated
`suggested_next_actions` carry `mutation_scope`, `mutates_project_graph`,
`writes_history`, `writes_files`, and `writes_storage`. Use these fields before
following a compact action: `apply_staged_revision` is
`project_graph_and_history`, staged/restage helpers are `history`,
`import_revision_snapshots` is `snapshot_storage`, exports are `file_export`,
and inspection/draft helpers are `none`.
When `alternative_gate.semantic_review_required=true`, `next_action` can still
carry the post-review apply or repair call, but `first_safe_next_action` points
to semantic inspection with `queue="semantic_review_required"` and
`mutation_scope="none"`.
`can_apply=True` means replay and validation readiness, not semantic approval.

`draft_staged_revision_rebase()` is a read-only repair/rebase planner for one
staged revision. Use it when an apply check routes to `repair_or_replace`, or
after a mechanical restage produces a `validation_failed` successor. It returns
the live apply check, compact lineage context, `draft_status`, `draft_kind`,
`reason_codes`, repair candidates, repair actions, and a compact `next_action`.
When DoxaBase recognizes a safe singleton-slot repair, such as
`rc:rowSemantics` max-count validation failure where the current graph has
exactly one different IRI value, it drafts
`stage_map_assertion_change(change_kind="replace", restages_revision=...)`
arguments without staging them. If the source already has a successor or applied
event, the draft is a redirect instead of a parallel repair.
When no safe repair is drafted, inherited `draft_staged_revision_rebase` actions
are filtered from `next_action` and `suggested_next_actions`; follow the
remaining inspect/export/manual-repair route instead of looping the same helper.
The first slice is deliberately narrow: `rc:rowSemantics`, `rc:physicalType`,
and `rc:schemaStability` repair drafts require IRI objects; `rc:nullable` repair
drafts allow typed `xsd:boolean` literals; blank-node objects, free-text
`rc:rowSemantics` literals, and multiple current values are not drafted.
For drafted repair mutations, `preferred_action` and the first repair action are
the post-review staging calls. `next_action_queue_item.resolved_target_iri` may
be null because the call creates a repaired successor; use
`next_action.arguments["restages_revision"]` to see the source row.

`describe_applied_revision_diff(applied_revision_iri, include_triples=False,
max_triples=500)` returns the stored snapshot diff for an applied staged
revision. It compares the staged source's before snapshots with the applied
event's after snapshots for changed graphs and returns exact added/removed
counts when snapshot rows are available. Changed-triple arrays are omitted by
default; pass `include_triples=True` to include them, capped by `max_triples`.
The response includes `snapshot_evidence` for the applied event and
`source_snapshot_evidence` for the staged source; when exact rows are missing,
their structured suggested actions point at `import_revision_snapshots`, and
those import actions are promoted into top-level `suggested_next_actions`.
It is a narrow applied-event inspection helper, not general historical graph
browsing. RDF `export_trig()`/`import_trig()` preserves the graph snapshot
metadata in `history`, but exact snapshot rows require an
`export_revision_snapshots()` / `import_revision_snapshots()` JSON bundle.
`describe_revision_graph_snapshot(revision_iri, graph_role,
include_triples=False, max_triples=500)` returns one role-local revision
snapshot. It is the route for full before/after snapshot contents once another
helper has identified the staged source IRI or applied event IRI. When exact
stored rows are missing, it falls back to RDF count/digest metadata and leaves
triple arrays empty; the snapshot-evidence import action is also promoted into
top-level `suggested_next_actions`.
`list_graph_versions(graph_role, graph="history", exact_only=False,
include_current=True, record_kind=None, limit=50, offset=0)` lists stored
snapshot versions for one graph role, newest first. Each row carries the source
revision IRI, `record_kind`, lineage links, role-local count/digest,
`snapshot_evidence`, and `snapshot_semantics` values such as
`staged_before_graph`, `applied_after_graph`, or `recorded_graph_snapshot`.
Set `exact_only=True` to keep only rows with exact stored snapshot quads. This
is a read-only timeline browser over stored revision snapshots, not a graph
checkout or replay API.
`describe_graph_version_diff(graph_role, before_revision_iri,
after_revision_iri=None, compare_to_current=True, graph="history",
include_triples=False, max_triples=500)` compares a stored graph-version
snapshot with either another stored snapshot or the current live graph. It
returns before/after count and digest metadata plus exact added/removed triple
counts when stored rows are available. Changed-triple arrays are omitted by
default; pass `include_triples=True` to include them, capped by `max_triples`.
When one side is incomplete after a handoff import, snapshot-evidence import
actions are promoted into top-level `suggested_next_actions`.
The diff also includes compact before/after revision context and
`related_revision_iris`; follow its `describe_revision_lineage` and
`describe_applied_revision_diff` actions when the graph delta is being used to
understand staged, applied, or restaged recovery state.
Call `describe_revision_snapshot_evidence()` when imported capsules behave
surprisingly; it now carries structured import actions for missing snapshot rows
or missing project/history RDF. Those actions mark placeholder paths with
`path_is_placeholder=True`; replace the path with the actual handoff artifact
before importing. Snapshot JSON alone is not a standalone revision manifest.

`restage_staged_revision()` creates a fresh staged revision from a conflicted
staged revision's existing patch payloads, recomputing before/after counts and
validation against the current graph state. It records `rc:restagesRevision`
back to the stale proposal and preserves support links, anchors, stance, review
notes, and review recommendations. The generated rationale summarizes the stale
apply check, including count drift and exact snapshot drift triples when
available, before repeating the original rationale. Use it for count or digest
drift conflicts that still have an effective current delta; it does not merge
semantic conflicts, repair invalid RDF proposals, apply the refreshed revision,
or create no-op successors for `already_effective` stale sources. It refuses to
create a parallel successor when the stale source already has `restaged_by` /
`current_restaged_by`; inspect or restage the current successor instead. The
immediate return includes `restaged_from`, `restage_reason`, `alternative_to`,
and `current_restaged_by` fields so handoffs do not need a separate
`describe_staged_revision()` call just to record restage provenance. It also
includes `status_after`, `decision_after`, `routing_decision_after`,
`stale_resolution_state_after`, `blocking_reasons_after`, `next_action_after`,
`next_action_queue_item_after`, and `suggested_next_actions_after`, derived from
a fresh apply check on the new successor. Follow `next_action_after` before
applying or restaging anything else.
When the drift review shows the payload itself needs editing, stage the repaired
payload with `stage_graph_revision(..., restages_revision=...)` or
`stage_map_assertion_change(..., restages_revision=...)` instead of calling this
mechanical replay helper. Call `draft_staged_revision_rebase()` first when you
want DoxaBase to compose the read-only repair route and preserve alternative
lineage context for recognizable same-slot repairs.

`restage_staged_revisions()` is the batch recovery helper for larger stale sets.
It checks each requested staged revision, restages conflicted revisions that do
not already have a `restaged_by` successor, skips already-handled stale sources
and non-conflicted rows, preserves caller order, and returns old-to-current
mappings plus the same `revision_summaries` and `bundle_summary` shape used by
grouped exports. Pass `path` to also write the grouped Markdown bundle over
stale sources and their current refreshed successors. Pass `dry_run=True` to get
the same per-source classifications without creating refreshed successors;
unhandled conflicts then report `action="would_restage"` and appear in
`would_restage_revision_iris` only when they remain safe mechanical restage
candidates. Stale sources whose staged-time validation failed and whose
post-batch route is repair-first are withheld from that bulk list and returned
in `repair_first_revision_iris`; inspect their validation diagnostics or call
`draft_staged_revision_rebase` before creating another same-payload successor.
The withholding happens in the dry-run worklist. A real batch call still
restages the source IRIs supplied by the caller, including repair-first rows,
and then routes any created successor through repair/replacement review instead
of applying it.
In dry-run rows that would be restaged,
`current_revision_by_source` still points to the stale source because no
successor exists yet. `skipped_not_restageable` rows may be ready,
validation-failed, already applied, or blocked by a stored patch conflict; each
such row carries `not_restageable_reason`, and the batch-level
`not_restageable_revision_iris_by_reason` groups skipped source IRIs by the same
compact values. Inspect `status_before` and `decision_before` when deciding
whether a row needs apply, repair, or replacement; use
`routing_decision_before` / `routing_decision_after` for the effective route
when `decision_*` is a broad stale-conflict explanation.
For read-only planning over mixed source/current handoffs, prefer
`plan_staged_revision_recovery()`: its `lanes[]` preserve per-source provenance,
while `resolved_target_groups[]` collapses stale sources, refreshed successors,
and applied-event aliases into a deduped target-family worklist.
`include_drafts=True` now embeds a bounded repair-draft sample by default:
`repair_draft_limit=1`. Deferred repair lanes stay visible with
`repair_draft_deferred_reason="repair_draft_limit_reached"`; call
`draft_staged_revision_rebase()` for a deferred row or rerun with a larger
limit. Use `repair_draft_limit=None` only for exhaustive embedded drafts.
For scripts that intend to mutate, use `mutation_frontier_items` as the complete
worklist. It includes existing apply/restage targets, repair targets only when
the selected repair action is mutating, and same-slot repair helper actions that
create a successor; `mutation_frontier_iris` is the compatibility list for
existing resolved target IRIs only. Revision-target items carry grouped
`semantic_risk_level` / `semantic_risk_reasons`, `alternative_set_iris`,
`alternative_set_source_iri`, `alternative_set_roles`, and
`alternative_gate_statuses` so mutation scripts do not need to reconstruct
choose-one or semantic-review context from separate queue rows.
Before using that worklist, check `mutation_allowed_after`. If it is
`handoff_preflight_required_before_mutation`, run the imports in
`blocking_preflight_actions` / `blocking_preflight_calls` and rerun the plan
before mutating. `semantic_review_required_before_mutation` means no handoff
preflight is blocking the current frontier, but the reviewed lane semantics
still apply. `repair_inspection_required_before_mutation` means repair lanes
exist, but their current route is diagnostic inspection or a read-only repair
draft rather than an executable mutation. `no_mutation_frontier` means there is
no mutation worklist.
For a single executable-or-review next hop, read
`first_safe_review_or_mutation_action` and
`first_safe_review_or_mutation_call`. Handoff preflight keeps
`first_mutation_action` empty and points the safe first action at the blocking
import/preflight step. Once preflight is clear, `first_mutation_action` is
populated only when no mutation-frontier item is semantic-review-gated. If the
frontier is mixed, with one reviewed semantic choice and one mechanically
restageable sibling, `first_mutation_action` stays empty while
`mutation_frontier_items[]` preserves each post-review action and reason. The
safe first action prefers any earlier read-only or `mutation_scope="none"`
review suggestion before falling back to an ungated mutation.
For multi-step or imported recovery work without a matching imported source
session, call
`start_staged_revision_recovery_session(revision_iris=plan.processed_revision_iris,
handoff_manifest_path=...)` before mutating. The session stores the ordered
source set and planning parameters in `history`; later
`describe_staged_revision_recovery_session(session_iri)` calls recompute the
live plan, source workflow states, applied events, and mutation frontier after
each restage, repair, or apply.
Guarded same-slot conflicts whose apply check already suggests
`stage_map_assertion_change` replacement are skipped with
`not_restageable_reason="same_slot_replacement"`; use `next_action_after` rather
than forcing a mechanical restage. Direct `restage_staged_revision()` also
rejects this route, so stage the replacement with `restages_revision`.
Stale conflicts whose patch payload already has no effective current delta are
skipped with `not_restageable_reason="already_effective"`; inspect or export the
source rather than creating a refreshed no-op successor.
Each item also carries
`status_after`, `decision_after`, `routing_decision_after`,
`stale_resolution_state_after`, `blocking_reasons_after`, and effective triple deltas for `current_revision_iri`
after the batch decision. `restaged_revision_iris` is only a list of created
successors, not an apply queue. `source_staged_validation_status` /
`source_validation_result_count` and `current_staged_validation_status` /
`current_validation_result_count` preserve stored staged-time validation signals
for the source and post-batch current rows separately from live apply status;
created successors may still be
validation-failed, no-op, or otherwise not ready. Use
`bundle_summary.ready_restage_successor_revision_iris` plus a final
`check_staged_revision_apply()` before applying. If an already-handled row has
`stale_resolution_state_after="restaged_successor_stale_unresolved"`, its
current successor is stale too; inspect or restage `current_revision_iri`.
If `bundle_summary.ready_restage_successor_alternative_to_applied_source_iris`
is non-empty, those ready successors are still alternatives to already-applied
staged sources; treat them as semantic review targets even when mechanically
ready. The same condition is visible in `bundle_summary.next_action_queue_items`
through `alternative_semantic_review_required=True` and the applied-source /
applied-revision fields.
For unresolved alternatives that are bundled together, queue items use
`alternative_set_iris`, `alternative_set_source_iri`, and `alternative_set_role`
to mark both the source/default row and child alternatives.
Each row also carries `next_action_after` and
`next_action_queue_item_after` / `suggested_next_actions_after` for that
`current_revision_iri`, so autonomous scripts can route the post-batch current
revision without a separate listing join. The item-local queue item is scoped to
`current_revision_iri`; bundle-level queue items remain scoped to review rows.
The batch response also carries top-level `suggested_next_actions` and
`suggested_next_calls`. Dry runs with `would_restage_revision_iris` promote a
reviewed real `restage_staged_revisions(dry_run=False, revision_iris=[...])`
call and intentionally omit any dry-run export path. Real batch runs promote
deduped item-local continuation actions for the current successors. If
`requires_recheck_after_each_apply` is true, apply at most one ready successor
from those actions before rerunning the recovery plan or grouped export.
Each item also carries
`restaged_from` when its source is itself a refreshed successor. The helper
deliberately does not apply anything; applying one successor can make sibling
successors stale again. In dry-run mode, passing `path` still writes the
requested review export while leaving graph history unmutated.

`apply_staged_revision()` applies one staged revision after conservative
graph-state conflict checks and preview validation. It rejects already-applied
staged revisions, rejects target graph count or digest drift from the patch
`beforeTripleCount` values and graph snapshots, and records an
`rc:AppliedStagedRevision` history event linked to the staged revision. This is
a conservative first apply path, not a full conflict/rebase or graph checkout
workflow. Use `list_graph_versions` for the stored graph-version timeline. The
return payload includes
`post_apply_recheck_revision_iris`, a list of other current staged revisions
sharing changed graphs or validation dependencies that should be rechecked
before any further apply, and `post_apply_recheck_revisions`, compact rows with
each sibling's `changed_graphs`, `shared_changed_graphs`, `recheck_reasons`,
fresh `application_status`, `decision`, `blocking_reasons`, `next_action`,
`suggested_next_actions`, and `suggested_next_calls` explaining why it is in the
post-apply queue and how to route it. `post_apply_recheck_is_partial_queue` is
always true: this is the affected-sibling subset, not the complete remaining
frontier. Follow the top-level `suggested_next_actions[0]`
`plan_staged_revision_recovery(current_staged_work_only=True)` before deciding
the next mutation when unattended, or
`describe_staged_revision_recovery_session(session_iri)` when the work is part
of a persisted recovery session.

`describe_pattern()` returns compact handoff context for a pattern: pattern text,
rationale, targets, supporting observations and claims, evidence/source spans,
and map implications.

`describe_resource()` returns outgoing and incoming triples for one resource,
with per-direction total, returned, omitted, and offset fields. Use it after
`list_entities(type="rc:Claim")`, `list_entities(type="rc:Evidence")`,
or `list_entities(type="rc:SourceSpan")` when you need generic structured
context rather than a type-specific helper. For SHACL shapes or other RDF
structures whose details sit behind blank-node objects, pass
`include_blank_node_closure=True` with bounded `blank_node_depth` and
`blank_node_limit`; closure triples are returned separately from direct
outgoing triples. `blank_node_depth_exhausted` means another blank-node hop was
available beyond the requested depth; `blank_node_omitted_count` means the
closure rows found within that depth exceeded `blank_node_limit`.

`describe_assertion_support()` returns support context for one map assertion.
Pass `subject`, `predicate`, optional `object`, and optional `object_kind`
(`"auto"`, `"iri"`, or `"literal"`). For literal assertions, pass
`object_datatype` such as `"xsd:boolean"` or `"xsd:decimal"` for typed-literal
matching, or `object_lang` such as `"en"` for language-tagged matching. It
reports whether the assertion is present, exact matching triples, current
same-subject/predicate triples, the touched resources, column owner summary when
known, nearby caveats, related
observations/claims/patterns/evidence/revisions, selected direct layout/path
context triples, the retrieval boundary, absence notes, and suggested next
calls. `nearby_caveat_links` explains the scope of each caveat, for example
whether it is directly attached to the assertion target or came via the owning
dataset. `suggested_next_actions` is the structured form to drive tools;
`action_label` names each action's role, and `suggested_next_calls` is the
bare-call back-compat string form. It also returns
`related_route_summaries` and `related_routes`, which explain why each related
lore item entered the payload. Scan summaries first when there are many rows;
use raw routes when you need exact links. Use it when the question is "why is
this map assertion here?" rather than "show me everything around this dataset."
If an exact requested object is absent, the same-subject/predicate triples and
`absence_note` show whether the requested predicate is present with a different
value or absent on that subject in the selected graph. If the predicate is
absent, inspect `predicate_hints`; each hint keeps the full predicate IRI and may
also include a compact `predicate_curie` such as `rc:partitionedBy`. For column
subjects, follow the owner-dataset suggested actions when table-level lore may
matter, but check caveat-link `scope` before treating table caveats as
column-specific. For layout, partition, or storage assertions, inspect
`nearby_context_triples` for verification notes before treating the assertion as
executable planning context. Literal matching is forgiving for common scalar
inputs: an untyped string object such as `"12"` or `"true"` can match stored
typed integer or boolean literals while the returned triple still reports the
actual datatype.

`search()` lexically searches literal RDF claims and URI-valued graph terms,
then returns matched resources, their graph role, RDF types, matched predicate,
matched text, and snippet. Use it to rediscover labels, caveats, source
descriptions, path templates, observations, evidence, and exact project
vocabulary tokens before deciding what to trust or inspect next.
The result object has `matches`, not `count`; use `len(result.matches)` for the
returned match count.
Empty search results may still carry `suggested_next_actions` for shorter
project-graph searches, `list_entities` browsing, and current staged-payload
search. Treat those as bounded recovery routes before concluding that lore or a
proposed term is absent.

## Validate

```python
result = db.validate_graph(scope="all")
```

DoxaBase runs pySHACL with RDFS inference. A class constraint can therefore pass
because a class was inferred from vocabulary such as `rdfs:range`; use property,
node-kind, count, or value constraints when a stricter explicit check matters.
The returned `results` list contains bounded structured diagnostics with focus
node, result path, constraint, severity, value, and messages where pySHACL
provides them.

Supported scopes today:

- `map`
- `ontology`
- `patterns`
- `shapes`
- `all`

## Current Exceptions

`ImmutableGraphError`

Raised when trying to mutate `base_ontology` or `base_shapes` through ordinary import APIs.
