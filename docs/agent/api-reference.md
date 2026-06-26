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
Use `DoxaBase(path)` to open an existing capsule. There is no `DoxaBase.open()`
helper in the current API.

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
`https://richcanopy.org/graph/{role}` to `{role}`.

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
db.export_revision_snapshots("/tmp/revision-snapshots.json")
```

`export_graph()` writes one flattened RDF graph, usually Turtle.

`export_trig()` writes a named-graph bundle with graph role IRIs so another
DoxaBase capsule can import it again. The default exports mutable project
graphs. Use `graphs="workflow"` for `map`, `observations`, `patterns`, and
`evidence`; use `graphs="all_with_seeds"` only when you explicitly need shipped
seed graphs in the bundle. The export record can list empty graph roles, but
TriG serializes only graph blocks that contain triples. Importing into a fresh
`DoxaBase.create(...)` capsule recreates the standard role metadata before the
non-empty graphs are imported. Workflow exports intentionally omit project
`ontology`; use the default project export or an ontology-bearing bundle when
project-specific metric kinds, value types, classes, or predicates are part of
the handoff. RDF exports do not include SQLite-side snapshot rows; pair them
with `export_revision_snapshots()` when exact applied-diff or stale-drift
triple reconstruction must survive import.

`export_revision_snapshots()` writes a JSON handoff bundle for stored revision
snapshot rows. Pass `revision_iris=[applied_iri]` to preserve the applied
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

```python
overview = db.graph_overview(limit=100)
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
`domain="analysis"`.
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
direct/upstream caveats, and structured `suggested_next_actions` for drafting
the selected route. It does not generate SQL or resolve credentials;
use it to decide whether the graph has enough non-secret physical context for a
query attempt, then review caveats before trusting aggregations or
interpretations. Read `query_target_decision` first: its `candidate_index` is a
zero-based pointer into the candidate list, and its `status` tells whether that
candidate is ready, blocked only by sibling context, directly review-only, or
absent. `selected_candidate_direct_clean` is true when the selected candidate
has no direct blocker of its own. When such a selected candidate is blocked by
sibling metadata, the suggested `draft_query_plan` action includes the explicit
`candidate_index` and `allow_context_blocked_candidate=True`.
`query_target_candidates`
preserve template provenance and compose best-effort file/object paths from
storage roots or bucket/prefix facts without resolving endpoint profiles or
credential references. For database-backed storage, candidates keep the relation
as `candidate_path` and expose `relation_identifier` plus
`connection_reference` instead of a joined file-like path when the relation
comes from a storage-access-owned template. Dataset or partition file paths
paired with database storage stay review-only with
`database_relation_template_source_mismatch` and no relation identifier. Candidate
`review_reasons` can include overall-context blockers
from sibling metadata as well as protocol/location warnings, for example
S3-compatible access without endpoint/credential/region cues, non-S3 access
with bucket/prefix metadata, or a storage root that does not match the declared
protocol. Complete path templates are checked too: an `s3://...` template under
HTTP/local access, an S3 template whose bucket/prefix conflicts with recorded
access metadata, or a relative template that repeats the recorded key prefix
will demote the candidate to review-only. A root-only storage-access candidate
is ready only when `location_kind == "object"`; absent, directory, prefix, or
connection location kinds are review-only until a path template narrows the
dataset location. Partition-specific blockers stay attached to their own
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
default. Pass `candidate_index` or `storage_access_iri` to select an explicit
candidate; pass `allow_context_blocked_candidate=True` only when that selected
candidate has no direct warning/error and stale sibling metadata should not
block this handoff. If `storage_access_iri` matches multiple candidate paths,
use the returned candidate snippets to rerun with `candidate_index`.
When sibling candidate-metadata blockers are the reason for the allowance, pass
an explicit selector too; selectorless automatic drafts keep the context review
gate and show the distinction through
`context_blocked_candidate_allowed=True` /
`context_blocked_candidate_used=False`.
`source_context` preserves both the automatic decision and
the explicit selection audit fields. It also reports `candidate_count`,
`ready_candidate_indexes`, and `unselected_ready_candidate_indexes`; when the
last list is non-empty, the automatic or explicit selection has peer ready
candidates worth reviewing before execution. Candidate order is not an
authoring-preference contract; use `candidate_index` as a response-local pointer
after inspecting the returned candidate cards.
The response includes a scan hint such as `read_parquet`, the candidate
URI/path template for file/object storage, database relation fields for
database-backed storage, parsed placeholder names in `required_bindings`,
structured `binding_requirements` rows for handoff work, non-secret storage
environment hints, copied issues and analysis warnings, caveats, and a
`review_gate`. Top-level `handoff_kind` is a machine-readable route for the
draft: `no_query_target`, `metadata_review_required`,
`context_review_required`, `runtime_resolution_required`,
`database_relation_handoff`, `binding_values_required`, or
`execution_attempt_ready`.
When a selected template comes from partition metadata, binding requirements
include partition handoff hints (`binding_kind`, `partition_scheme`,
`partition_column`, and `partition_granularity`) while still requiring caller
runtime values.
Binding rows identify the placeholder source text and explicitly report when
DoxaBase has not inferred derivation or runtime values. `review_gate` separates
`blocking_reason_codes` from `all_issue_codes` while preserving `reason_codes`
as a legacy alias for blocking reasons. It also exposes
`binding_values_required` and `ready_for_execution_attempt`, which is true only
when the graph-metadata review gate is clear, no runtime endpoint/credential or
object resolution remains recorded, and no required binding placeholders remain
in the selected template. It may add handoff-only blockers such as
`query_context_has_other_blockers` for clean selected candidates with bad
siblings, or `scan_function_not_inferred` when DuckDB has no file-scan function
for the selected storage/layout shape. Database-backed storage still uses this
generic review-draft shape today, so expect `scan.function=None` and review
gating rather than executable SQL; `scan.uri_template` is intentionally absent
there, and `scan.relation_identifier` plus `scan.connection_reference` carry
the recorded database handoff for review. These scan fields mirror the selected
candidate's database-specific fields; if the selected database candidate came
from a dataset or partition path, `scan.relation_identifier` is absent and the
plan stays metadata-review-required. Root-only database storage without a
storage-access relation template is also metadata-review-required with
`database_relation_template_missing`. The `scan` card carries dataset-level
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
updates, `metric_advisories` for project-specific profile metrics, and a
`review_note`. It also includes `recommendation_count`,
`metric_advisory_count`, `metric_advisory_status_counts`, and top-level
`suggested_next_actions` / `suggested_next_calls` for quick routing.
Recommendation rows carry `recommendation_index`, the source profile
observation IRI, evidence IRI, `sample_size`, `sample_scope`, `sample_method`,
and
`profile_row_count` so agents can review whether the profile was a full scan,
sample, or ambiguous run before applying helper arguments. They also carry
duplicate-group metadata so repeated same-evidence observations can be reviewed
as one representative row without losing sibling support. It does not mutate or
stage graph changes, and it skips sampled zero-null promotions. Metric advisories
carry `advisory_status`, `definition_found`, optional `definition`,
`promotion_patterns`, duplicate-group metadata, and structured
`suggested_next_actions` for ontology/context review. Undefined metrics with a
same-evidence pattern that names the metric as a target or map implication also
get a reviewable `stage_pattern_promotion` skeleton for an ontology
`rc:ProfileMetricKind`.
If `recommendation_count > 0`, review the draft and use the top-level
`stage_profile_map_updates` action as a starting point, passing only accepted
indexes. If `recommendation_count == 0 and metric_advisory_count > 0`, treat
the draft as advisory-only: follow the top-level advisory suggested actions and
do not call `stage_profile_map_updates`, because advisory rows are not
map-update recommendations.

`stage_profile_map_updates(dataset_iri, evidence_iri, accepted_recommendation_indexes=[...])`
reruns the draft, stages the accepted recommendation indexes as one grouped
reviewable `map` revision, and returns explicit staged/skipped/not-selected
item statuses plus `status_counts`, `metric_advisory_count`, and
`metric_advisory_status_counts`. Use it when profile-derived map changes need
review before application. When staging creates a revision, follow
`suggested_next_actions` to `check_staged_revision_apply` before reviewing,
exporting, or applying it. The staged patch uses helper-equivalent RDF:
missing dataset shells get `rdf:type rc:Dataset`, unmapped columns get
`rdf:type rc:Column`, `rc:columnName`, and `rc:hasColumn`, and scalar
row-count/nullability changes remove old helper-owned values before adding
typed literals. Accepted indexes can still be skipped by safety guardrails,
especially sampled row-count recommendations by default; set
`allow_sampled_row_count_updates=True` only when the profile scope is the
intended durable population. Metric advisories are returned for review but are
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

`describe_context_slice()` returns a bounded, route-explained graph slice around
seed IRIs. Profiles are intentionally explicit: `dataset_brief` starts from
dataset/table map context, bounded profile observations/metrics, and linked
lore, `pattern_brief` starts from pattern support, and `deep_lore` also
includes directly relevant revision metadata. Dataset/deep-lore slices can also
start from mapped column IRIs, profile observations, observed profile metric
nodes, or metric-kind IRIs used by profile metrics. Deep-lore slices can start
from `rc:GraphRevision` seeds to inspect revision support, evidence, anchors,
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
`resources[].surface_role` is a compact first-pass cue for whether a resource is
current map context, observation context, pattern synthesis, evidence support,
revision history, vocabulary context, mixed context, or only referenced by the
slice. Set
`include_trig=True` when an agent needs importable TriG text for review or a
scratch capsule. `max_triples` only truncates raw triples/TriG; top-level
resources, routes, and structured contexts continue to describe the full
selected slice. Use `candidate_triple_count`, `returned_triple_count`, and
`omitted_triple_count` to decide whether to rerun with a larger limit.

`record_observation()` writes a structured `rc:Observation` or
`rc:ProfileObservation` to the `observations` graph. When evidence fields are
supplied, it also writes a linked `rc:Evidence` resource to the `evidence`
graph. Include `evidence_sources` or a source span when you need validation-clean
evidence; `evidence_summary` alone is descriptive prose. When
`observed_column` names a column that is not yet in the map,
`observed_column_name` can preserve the source-level column name without
promoting the column into current map state.

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
source spans when recorded. `update_map_snapshot`
defaults to true, so pass `false` when a row count is only a scratch sample or
tentative measurement. On a brand-new dataset that keeps the profile
observation-only, `describe_dataset()` may not find the dataset until map
context is recorded; use `describe_profile_run(dataset_iri, evidence_iri)` or
profile-observation context-slice seeds for handoff retrieval. When matching
profile observations exist, the `describe_dataset()` not-found error includes
this recovery hint and points at `record_map_dataset` for creating map context.
When the helper creates a pattern and the profile observation has evidence, the
same evidence is linked to the pattern.
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
Pass `shared_evidence_iri` when the dataset profile and column profiles should
all link to one shared profiler-run `rc:Evidence` resource. A column item can
override that by supplying its own `evidence_iri`.
The returned bundle includes `shared_evidence_iri` at top level for quick
run-level checks and `handoff_entrypoints` with profile observation seeds,
availability flags, structured `suggested_next_actions`, and compatibility
`suggested_next_calls` for the next agent. When both map dataset context and a
shared evidence run are available, handoff actions include
`draft_profile_map_updates` before context-slice routes.
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

`record_column_profile()` does the same for one column: it records a profile
observation with `observed_column`, can update map column metadata such as
physical type and nullability, and can write a linked profile pattern. Column
profile observations are exposed on the matching `describe_dataset().columns[]`
entry, including any observed value-frequency pairs and scalar profile metrics
supplied by the profiler. Use `sample_scope` and `sample_method` to distinguish,
for example, a full-column scan from a top-N value-frequency sample.
Scalar `profile_metrics` remain observed evidence unless a later claim, pattern,
or map update interprets them.
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
`record_map_dataset()`, `record_map_column()`, `record_map_caveat()`,
`record_map_storage_access()`, `record_map_physical_layout()`,
`record_map_partition_scheme()`, and `record_map_relationship()`. Use them when
observations or patterns are ready to become operating context for future
agents. On partial dataset updates, omit `is_table` to preserve existing
dataset/table typing. Use physical-layout and partition helpers when path or
layout verification belongs to one part of the executable catalog rather than
to the whole dataset. For storage access, set `location_kind="object"` only when
`storage_root` names the dataset object/location exactly; use `directory`,
`prefix`, or `connection` for broader roots and add path templates for
executable query planning. Resource-valued fields across these helpers expect
IRIs/CURIEs, not prose: use terms such as `rc:EventRow`, `rc:Parquet`, or
project IRIs for datasets, columns, caveats, and relationship endpoints. Put
ordinary explanation in descriptions, notes, observations, or patterns.
`schema_stability` accepts `rc:FixedSchema`, `rc:InferredSchema`, or
`rc:VariableSchema`. Layout verification status accepts
`rc:UnverifiedLayout`, `rc:GeneratedFromManifestLayout`, `rc:CandidateLayout`,
`rc:VerifiedByListingLayout`, `rc:VerifiedByQueryLayout`, or
`rc:ContradictedLayout`.
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
`within_group_ordering`. Dataset descriptions expose all partition columns as
`partition_columns`; the older singular `partition_column` field remains as a
compatibility shortcut to the first returned column. Treat `partition_columns`
as unordered unless a future response explicitly carries ordering metadata.
Relationship descriptions expose `relationship_kind` as the RDF class IRI and
`relationship_type` as the helper-style token such as `foreign_key` or
`aggregation`.

`record_graph_revision()` writes metadata to `history` about changed graph
roles, included review/export graph roles, rationale, supporting resources,
revision anchors, validation results, export paths, and graph-count snapshots.
It does not compute diffs or apply graph edits. Use support links for evidence
behind a revision; use anchors for resources the revision is about.

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

`stage_map_assertion_change()` stages a reviewable add/remove/replace for one
`map` assertion. Pass `subject`, `predicate`, optional `object`, a `rationale`,
and `change_kind` (`"add"`, `"remove"`, or `"replace"`). For typed or
language-tagged literals, also pass `object_datatype` or `object_lang`; the
helper will author the corresponding typed/language-tagged Turtle instead of a
plain literal. It calls `describe_assertion_support()` before staging, generates
the Turtle patches, links related observations/claims/patterns/evidence and
revision anchors, and stores an assertion-support summary in the staged revision
review note. The returned `judgement_panel` is the compact reviewer view:
headline,
current/proposed values, semantic risk level/reasons, value-type context, reasons
the current value may be intentional, caveat scopes, strongest related-lore
routes, impact spotlight entries, and safety notes. For physical type changes,
the panel includes current `rc:valueType` resources and any declared
`rc:requiredPhysicalType`. `target_value` names the requested object for add,
replace, and remove changes; `removed_value` is populated for remove changes so
reviewers do not have to interpret legacy `proposed_value` as the value being
removed. For exact removals, `removed_value` reflects the matched graph triple,
including datatype or language-tag context. Use it for common assertion changes
before reaching for generic `stage_graph_revision`.
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
`result_kind="systematisation_draft"`, a draft-level `next_action_queue`, and
`suggested_next_actions` / `suggested_next_calls`. The queue uses the same
apply-check grouping as staged-revision exports, so callers can separate
`repair_or_replace` framings from `apply_after_review` framings immediately
after staging.

`stage_pattern_promotion()` stages one or more caller-authored RDF framings
supported by existing `rc:Pattern` resources. Pass pattern IRIs and framings;
the helper records the selected patterns as support, rolls up their supporting
observations/claims/evidence, uses pattern targets and map implications as
revision anchors, and delegates validation/review packaging to
`stage_systematisation()`. It does not apply the changes or infer the graph
shape. It returns the same `systematisation_draft` routing fields as
`stage_systematisation()`.

`describe_graph_revision()` returns compact revision context: summary,
rationale, changed/included graph roles, graph snapshots with counts and
`sha256:<hex>` content digests, validation result, structured validation
diagnostics, export path, `applies_staged_revision` for applied events,
`applied_source` compact source context for applied staged revision events,
revision anchors, and supporting observation/claim/pattern/evidence links.
It also includes `snapshot_evidence`, which classifies whether RDF history
metadata and SQLite snapshot rows are both present for exact diff/drift work.

`describe_revision_snapshot_evidence(revision_iri)` returns just that snapshot
handoff status for a revision IRI. Use it after imports when you need to know
whether the capsule has `history_missing`, `history_only_count_digest`,
`history_plus_snapshot_rows`, or `snapshot_rows_without_history`. The last case
usually means a workflow-only RDF bundle was paired with snapshot JSON: the
snapshot rows imported, but normal revision helpers still need the project or
history RDF records.

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
`returned_application_status_counts`, `returned_stale_resolution_state_counts`,
and `returned_staged_validation_status_counts` summarize the returned page, not
unseen paginated rows.
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
`list_resource_revisions(resource_iri)` returns revision rows that explicitly
touch one resource through `rc:revisionAnchor`, exact subject/predicate/object
URI mentions in staged patch payloads, or an applied event whose staged source
matched the resource. It filters before pagination and wraps each normal
`list_graph_revisions()` row under `revision`, adding `match_types`,
`patch_mentions`, `applied_source_revision_iri`, and
`applied_source_patch_mentions`. Patch mentions are compact role-aware flags,
not patch content; call `describe_staged_revision()` for the full payload.
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
row, visible paired staged/applied row, related revision IRIs, selected next
action, patch scan status, and optional resource-filtered applied diff summary.
`current_revision_iri` mirrors `current_staged_revision_iri` when the lineage row
or restage successor is still current staged work, matching batch-restage naming.
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
status, decision, blockers, validation headline, drift summaries, compact
`next_action`, and suggested next actions, but omits full patch checks and
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
Context`; it is not a replayed panel.
Restaged exports include a top metadata `Restage headline` before the current
apply check. Stale original exports include a top metadata `Restaged by` line
when a refreshed successor already exists. Suggested export actions use
revision-derived `/tmp` filenames with a short hash to reduce collisions; callers
may override them with run-specific paths.
`export_staged_revisions()` writes one Markdown review bundle for several staged
revisions in caller-chosen order; its summary table includes each staged
revision's current apply status, decision, current validation state, and
staged-time validation result. Bundles with restaged revisions include a
`Restage Context` section near the top. When an alternative's stored target has
itself been restaged, grouped Markdown also includes `Alternative Context` so
reviewers can compare against the current successor without reconstructing that
lineage by hand. Pass `executive_summary` when the comparison needs an
agent-authored synthesis at the top of the artifact.
The returned record also includes `revision_summaries`, a machine-readable copy
of the grouped status rows with current apply status, blockers, validation
state, alternative/restage links, authored review recommendations, live
`apply_recommended_resolution` guidance, effective `summary_recommendation`
text matching the grouped Markdown table, recommendation source/scope fields,
per-row `next_action`, and suggested next actions. Grouped Markdown and
`bundle_summary.next_action_queue` expose the same compact next-action buckets
for routing; the older recommended queues remain for compatibility and broader
review grouping.
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
`bundle_summary.warnings` calls out sequencing hazards, including grouped
ready/no-op reviews on the same changed graph that should be re-checked after
each apply, and `post_apply_recheck_revision_iris` gives scripts the affected
revision IRIs for pre-apply grouped-review hazards.
`sequential_apply_recheck_candidate_iris` is a clearer alias for the same list.
Grouped Markdown exports include a `Review Queues` section mirroring the
apply/restage, repair, applied-inspection, and post-apply recheck buckets.
Relative export paths are resolved from the repository root and returned as
normalized absolute paths.

`check_staged_revision_apply()` previews whether one staged revision can be
applied without mutating graph state. It reports already-applied state,
per-patch count drift, graph snapshot digest drift, preview triple counts,
validation status, semantic risk, and a top-level `can_apply` flag. Read
`status`, `summary`, and
`semantic_risk_level` first; use
`decision`, `blocking_reasons`, `validation_skipped_reason`,
`recommended_resolution`, `count_drifts`, `snapshot_drifts`, and
`suggested_next_actions` to decide whether to review then apply, inspect an
applied event, review validation diagnostics, or restage after conflicts.
`superseded_by_restage` means the staged source already has a refreshed
successor; inspect that successor instead of applying the old source.
`inspect_restaged_source_validation_failure` means a restaged successor is
mechanically ready, but its source failed staged-time validation and current
graph state may be filling the semantic gap; inspect/export it and stage a
repair or alternative before applying.
For `ready` checks with `semantic_risk_level` of `attention` or `high`, the
apply action is labelled `Apply only after semantic review`. For conflict
checks, the review action includes `include_current_apply_check=True` so the
next staged-revision inspection reloads the current blocked status.
The response includes both `staged_revision_iri` and `revision_iri`; the latter
is a script-friendly alias for copied payloads.
`noop` means replay validates but has no effective graph delta; suggested
actions point to inspection/export rather than apply. `triples_to_add` and
`triples_to_remove` are effective deltas for the current preview, and
`patch_checks` records effective add/remove counts plus already-present/absent
payload triples for partial or no-op replay.
`count_drifts` gives expected/current counts and deltas, plus whether the staged
patch triples themselves are currently present, absent, or mixed in the target
graph. `snapshot_drifts` gives staged/current `sha256:<hex>` digest mismatches,
including same-count graph changes. For new revisions, `snapshot_drifts` also
includes exact triples added to and removed from the target graph since the
stored snapshot, a `drift_relevance` hint, and any patch-subject or
patch-predicate, patch-object, or revision-anchor overlaps.
`no_patch_subject_overlap` is useful triage context, not semantic approval to
apply. Predicate and object overlap can be broad; `broad_patch_object_overlap`
marks weak object overlap through shared class/type vocabulary such as
`rc:Dataset`. Anchor overlap means exact drift touched a resource the staged
proposal named as review context. Older revisions may report
`exact_changed_triples_available=False` if no snapshot rows were stored.
Suggested actions are ordered review-first; mutation calls come after
inspection/export suggestions.
`can_apply=True` means replay and validation readiness, not semantic approval.

`describe_applied_revision_diff(applied_revision_iri, include_triples=False,
max_triples=500)` returns the stored snapshot diff for an applied staged
revision. It compares the staged source's before snapshots with the applied
event's after snapshots for changed graphs and returns exact added/removed
counts when snapshot rows are available. Changed-triple arrays are omitted by
default; pass `include_triples=True` to include them, capped by `max_triples`.
The response includes `snapshot_evidence` for the applied event and
`source_snapshot_evidence` for the staged source; when exact rows are missing,
their structured suggested actions point at `import_revision_snapshots`.
It is a narrow applied-event inspection helper, not general historical graph
browsing. RDF `export_trig()`/`import_trig()` preserves the graph snapshot
metadata in `history`, but exact snapshot rows require an
`export_revision_snapshots()` / `import_revision_snapshots()` JSON bundle.
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
drift conflicts; it does not merge semantic conflicts, repair invalid RDF
proposals, or apply the refreshed revision. It refuses to create a parallel
successor when the stale source already has `restaged_by` /
`current_restaged_by`; inspect or restage the current successor instead. The
immediate return includes `restaged_from`, `restage_reason`, `alternative_to`,
and `current_restaged_by` fields so handoffs do not need a separate
`describe_staged_revision()` call just to record restage provenance.
When the drift review shows the payload itself needs editing, stage the repaired
payload with `stage_graph_revision(..., restages_revision=...)` or
`stage_map_assertion_change(..., restages_revision=...)` instead of calling this
mechanical replay helper.

`restage_staged_revisions()` is the batch recovery helper for larger stale sets.
It checks each requested staged revision, restages conflicted revisions that do
not already have a `restaged_by` successor, skips already-handled stale sources
and non-conflicted rows, preserves caller order, and returns old-to-current
mappings plus the same `revision_summaries` and `bundle_summary` shape used by
grouped exports. Pass `path` to also write the grouped Markdown bundle over
stale sources and their current refreshed successors. Pass `dry_run=True` to get
the same per-source classifications without creating refreshed successors;
unhandled conflicts then report `action="would_restage"` and appear in
`would_restage_revision_iris`. In dry-run rows that would be restaged,
`current_revision_by_source` still points to the stale source because no
successor exists yet. `skipped_not_restageable` rows may be ready,
validation-failed, already applied, or blocked by a stored patch conflict; each
such row carries `not_restageable_reason`, and the batch-level
`not_restageable_revision_iris_by_reason` groups skipped source IRIs by the same
compact values. Inspect `status_before` and `decision_before` when deciding
whether a row needs apply, repair, or replacement. Each item also carries
`status_after`, `decision_after`, `stale_resolution_state_after`,
`blocking_reasons_after`, and effective triple deltas for `current_revision_iri`
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
Each row also carries `next_action_after` and
`suggested_next_actions_after` for that `current_revision_iri`, so autonomous
scripts can route the post-batch current revision without a separate listing
join.
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
a conservative first apply path, not a full conflict/rebase or
graph-version workflow. The return payload includes
`post_apply_recheck_revision_iris`, a list of other current staged revisions
sharing changed graphs that should be rechecked before any further apply, and
`post_apply_recheck_revisions`, compact rows with each sibling's
`changed_graphs`, `shared_changed_graphs`, fresh `application_status`,
`next_action`, `suggested_next_actions`, and `suggested_next_calls` explaining
why it is in the post-apply queue and how to route it.

`describe_pattern()` returns compact handoff context for a pattern: pattern text,
rationale, targets, supporting observations and claims, evidence/source spans,
and map implications.

`describe_resource()` returns outgoing and incoming triples for one resource.
Use it after `list_entities(type="rc:Claim")`, `list_entities(type="rc:Evidence")`,
or `list_entities(type="rc:SourceSpan")` when you need generic structured
context rather than a type-specific helper.

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
