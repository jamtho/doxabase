# API Reference

Current Python API entry point:

```python
from doxabase import DoxaBase
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

## Import Data

```python
db.import_turtle("path/to/file.ttl", graph="map")
db.import_trig("path/to/file.trig")
```

`import_turtle()` writes all triples to one graph.

`import_trig()` preserves named graph roles and maps `https://richcanopy.org/graph/{role}` to `{role}`.

## Export Data

```python
db.export_graph("/tmp/map.ttl", graphs="map")
db.export_trig("/tmp/project-review-bundle.trig")
db.export_trig("/tmp/workflow-review-bundle.trig", graphs="workflow")
```

`export_graph()` writes one flattened RDF graph, usually Turtle.

`export_trig()` writes a named-graph bundle with graph role IRIs so another
DoxaBase capsule can import it again. The default exports mutable project
graphs. Use `graphs="workflow"` for `map`, `observations`, `patterns`, and
`evidence`; use `graphs="all_with_seeds"` only when you explicitly need shipped
seed graphs in the bundle.

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
Check `layout_verification_status` and `layout_verification_note` before using
`path_templates` for executable query planning. Child physical layout, storage,
and partition descriptions may carry their own verification fields when the
uncertainty belongs to one part of the path/layout model.
`operational_warnings` carries the same `QueryPlanningIssue` objects returned
as `describe_query_context().issues`, so a full dataset handoff can still flag
unverified layouts, missing storage access, or missing physical layout before an
agent writes query plans.
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
for one dataset. It includes the dataset summary, readiness, an `issues` list
for missing or risky metadata, planning notes, columns, path templates, physical
layouts, storage access descriptions, partition schemes, and direct/upstream
caveats. It does not generate SQL or resolve credentials; use it to decide
whether the graph has enough non-secret physical context for a query attempt.

`describe_context_slice()` returns a bounded, route-explained graph slice around
seed IRIs. Profiles are intentionally explicit: `dataset_brief` starts from
dataset/table map context and linked lore, `pattern_brief` starts from pattern
support, and `deep_lore` also includes directly relevant revision metadata.
Use `resources[].routes`, `route_counts`, `dataset_contexts`, and
`pattern_contexts` as the reading path before raw `triples`. The response also
includes `reading_order` and a filtered `route_legend` so cold agents can follow
the intended reading protocol without rediscovering route meanings. Set
`include_trig=True` when an agent needs importable TriG text for review or a
scratch capsule. `max_triples` only truncates raw triples/TriG; top-level
resources, routes, and structured contexts continue to describe the full
selected slice. Use `candidate_triple_count`, `returned_triple_count`, and
`omitted_triple_count` to decide whether to rerun with a larger limit.

`record_observation()` writes a structured `rc:Observation` or
`rc:ProfileObservation` to the `observations` graph. When evidence fields are
supplied, it also writes a linked `rc:Evidence` resource to the `evidence`
graph. Include `evidence_sources` or a source span when you need validation-clean
evidence; `evidence_summary` alone is descriptive prose.

`record_dataset_profile()` records a profile observation for one dataset and can
also update the map row-count snapshot and write an agent-authored profile
pattern linked back to the observation. Use it when a profiling result should
arrive as observation, optional current-best map context, and optional synthesis
without making three separate helper calls. `describe_dataset()` surfaces recent
dataset profile observations and their sample, row, null, distinct, and observed
value-frequency counts, plus scalar `profile_metrics` such as observed minimum
or mean values. Pass metrics as
`profile_metrics=[{"metric": "rc:MinimumValue", "value": ...}]`, using project
metric-kind IRIs when the base metric kinds do not fit. These scalar metrics are
observed profile evidence, not constraints, shapes, allowed values, or durable
map semantics by themselves. Define project metric kinds in the project ontology
once they become stable shared vocabulary. Profile evidence entries include
source strings and source spans when recorded. `update_map_snapshot`
defaults to true, so pass `false` when a row count is only a scratch sample or
tentative measurement. When the helper creates a pattern and the profile
observation has evidence, the same evidence is linked to the pattern.

`record_column_profile()` does the same for one column: it records a profile
observation with `observed_column`, can update map column metadata such as
physical type and nullability, and can write a linked profile pattern. Column
profile observations are exposed on the matching `describe_dataset().columns[]`
entry, including any observed value-frequency pairs and scalar profile metrics
supplied by the profiler.
Scalar `profile_metrics` remain observed evidence unless a later claim, pattern,
or map update interprets them.
`update_map_column` defaults to true, so pass `false` when observed values or
counts should stay observation-only. For a profile such as "BUY/SELL appeared in
this sample, but that is not an allowed-value domain", combine
`record_column_profile(update_map_column=false)`,
`record_claim_observation()`, and `record_pattern()`.

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
to the whole dataset. `record_map_relationship()` supports foreign keys, shared
identifiers, derivations, and aggregations; for aggregations, pass
`group_by_columns` plus `aggregated_columns` mappings with `target_column`,
`source_columns`, optional `aggregation_function`, and optional
`within_group_ordering`.

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

`stage_map_assertion_change()` stages a reviewable add/remove/replace for one
`map` assertion. Pass `subject`, `predicate`, optional `object`, a `rationale`,
and `change_kind` (`"add"`, `"remove"`, or `"replace"`). It calls
`describe_assertion_support()` before staging, generates the Turtle patches,
links related observations/claims/patterns/evidence and revision anchors, and
stores an assertion-support summary in the staged revision review note. The
returned `judgement_panel` is the compact reviewer view: headline,
current/proposed values, semantic risk level/reasons, value-type context, reasons
the current value may be intentional, caveat scopes, strongest related-lore
routes, impact spotlight entries, and safety notes. For physical type changes,
the panel includes current `rc:valueType` resources and any declared
`rc:requiredPhysicalType`. Use it for common assertion changes before reaching
for generic `stage_graph_revision`.
For `replace`, the generated patch set adds the requested assertion and removes
current same-subject/predicate values except the requested object. The recorded
patch sequence shows the exact preview/apply order.

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

`stage_pattern_promotion()` stages one or more caller-authored RDF framings
supported by existing `rc:Pattern` resources. Pass pattern IRIs and framings;
the helper records the selected patterns as support, rolls up their supporting
observations/claims/evidence, uses pattern targets and map implications as
revision anchors, and delegates validation/review packaging to
`stage_systematisation()`. It does not apply the changes or infer the graph
shape.

`describe_graph_revision()` returns compact revision context: summary,
rationale, changed/included graph roles, graph snapshots with counts and
`sha256:<hex>` content digests, validation result, structured validation
diagnostics, export path, revision anchors, and supporting
observation/claim/pattern/evidence links.

`list_graph_revisions()` returns compact history rows for `rc:GraphRevision`
resources, newest first. Each row includes summary, revision type/stance,
record kind, created time, changed graphs, validation headline, patch payload
presence/count, relation links such as `applied_by`, `applies_staged_revision`,
`alternative_to`, `restaged_from`, and `restaged_by`, plus optional staged
apply-check status, blockers, drift summaries, and suggested actions when
`include_apply_checks=True`.

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
graph counts.
`export_staged_revision()` writes a Markdown review bundle with the current
apply-check status, diagnostics, and impact review before patch payloads. Stale
exports include conflict status, count drift, validation-skipped reason, and
suggested next calls as of export time. For simple single-assertion `map`
changes that still replay cleanly, it may add a `Semantic Review Warning` before
the apply check, and reconstructs a `Judgement Panel` section so the export
carries values, value-type context, rationale, caveats, routes, and safety notes
from the JSON review surface.
`export_staged_revisions()` writes one Markdown review bundle for several staged
revisions in caller-chosen order; its summary table includes each staged
revision's current apply status, decision, current validation state, and
staged-time validation result. Pass `executive_summary` when the comparison
needs an agent-authored synthesis at the top of the artifact. Relative export
paths are resolved from the repository root and returned as normalized absolute
paths.

`check_staged_revision_apply()` previews whether one staged revision can be
applied without mutating graph state. It reports already-applied state,
per-patch count drift, preview triple counts, validation status, semantic risk,
and a top-level `can_apply` flag. Read `status`, `summary`, and
`semantic_risk_level` first; use
`decision`, `blocking_reasons`, `validation_skipped_reason`,
`recommended_resolution`, `count_drifts`, `snapshot_drifts`, and
`suggested_next_actions` to decide whether to review then apply, inspect an
applied event, review validation diagnostics, or restage after conflicts.
`count_drifts` gives expected/current counts and deltas, plus whether the staged
patch triples themselves are currently present, absent, or mixed in the target
graph. `snapshot_drifts` gives staged/current `sha256:<hex>` digest mismatches,
including same-count graph changes. Exact unrelated changed triples still need
future graph version storage. Suggested actions are ordered review-first;
mutation calls come after inspection/export suggestions.
`can_apply=True` means replay and validation readiness, not semantic approval.

`restage_staged_revision()` creates a fresh staged revision from a conflicted
staged revision's existing patch payloads, recomputing before/after counts and
validation against the current graph state. It records `rc:restagesRevision`
back to the stale proposal and preserves support links, anchors, stance, review
notes, and review recommendations. Use it for count-drift conflicts; it does not
merge semantic conflicts, repair invalid RDF proposals, or apply the refreshed
revision.

`apply_staged_revision()` applies one staged revision after count-based conflict
checks and preview validation. It rejects already-applied staged revisions,
rejects target graph count drift from the patch `beforeTripleCount` values, and
records an `rc:AppliedStagedRevision` history event linked to the staged
revision. This is a conservative first apply path, not a full conflict/rebase or
graph-version workflow.

`describe_pattern()` returns compact handoff context for a pattern: pattern text,
rationale, targets, supporting observations and claims, evidence/source spans,
and map implications.

`describe_resource()` returns outgoing and incoming triples for one resource.
Use it after `list_entities(type="rc:Claim")`, `list_entities(type="rc:Evidence")`,
or `list_entities(type="rc:SourceSpan")` when you need generic structured
context rather than a type-specific helper.

`describe_assertion_support()` returns support context for one map assertion.
Pass `subject`, `predicate`, optional `object`, and optional `object_kind`
(`"auto"`, `"iri"`, or `"literal"`). It reports whether the assertion is
present, exact matching triples, current same-subject/predicate triples, the
touched resources, column owner summary when known, nearby caveats, related
observations/claims/patterns/evidence/revisions, selected direct layout/path
context triples, the retrieval boundary, absence notes, and suggested next
calls. `nearby_caveat_links` explains the scope of each caveat, for example
whether it is directly attached to the assertion target or came via the owning
dataset. `suggested_next_actions` is the structured form to drive tools;
`suggested_next_calls` is the display/back-compat string form. It also returns
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

`search()` lexically searches literal RDF claims and returns matched resources,
their graph role, RDF types, matched predicate, matched text, and snippet. Use
it to rediscover labels, caveats, source descriptions, path templates,
observations, and evidence before deciding what to trust or inspect next.

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
