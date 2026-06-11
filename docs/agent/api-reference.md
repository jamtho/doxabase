# API Reference

Current Python API entry point:

```python
from doxabase import DoxaBase
```

## Create or Open a Capsule

```python
db = DoxaBase.create(".doxabase.sqlite", overwrite=True)
```

This initializes the SQLite schema, registers default graph roles, and seeds immutable `base_ontology` and `base_shapes`.

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
supplied, it also writes a linked `rc:Evidence` resource to the `evidence` graph.

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
and records `rc:GraphPatch` entries for later review. When validation reports
results, the staged revision stores linked `sh:ValidationResult` diagnostics
with focus node, result path, constraint, severity, value, and messages where
pySHACL provides them.

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
rationale, changed/included graph roles, graph-count snapshots, validation
result, structured validation diagnostics, export path, revision anchors, and
supporting observation/claim/pattern/evidence links.

`describe_staged_revision()` returns staged patch payloads, stance, review
notes/recommendations, validation status, structured validation diagnostics,
support links, revision anchors, and count previews. `export_staged_revision()`
writes a Markdown review bundle with diagnostics before patch payloads.
`export_staged_revisions()` writes one Markdown review bundle for several staged
revisions in caller-chosen order; pass `executive_summary` when the comparison
needs an agent-authored synthesis at the top of the artifact.

`describe_pattern()` returns compact handoff context for a pattern: pattern text,
rationale, targets, supporting observations and claims, evidence/source spans,
and map implications.

`describe_resource()` returns outgoing and incoming triples for one resource.
Use it after `list_entities(type="rc:Claim")`, `list_entities(type="rc:Evidence")`,
or `list_entities(type="rc:SourceSpan")` when you need generic structured
context rather than a type-specific helper.

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
