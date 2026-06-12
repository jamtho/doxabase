# MCP Tools

The MCP server is intentionally thin. It exposes the current Python API plus short operational docs.

## Documentation

`doxabase.list_docs`

Returns available agent docs with IDs, titles, and descriptions.

`doxabase.get_doc`

Returns one markdown doc by ID. Use `max_chars` to bound output.

## Capsule Inspection

`doxabase.graph_overview`

Returns named graph counts, top classes, top predicates, key entity counts, and known namespaces.

`doxabase.list_entities`

Lists entities by RDF type, graph role, optional text filter, limit, and offset. Start with `type="rc:Table"` and `graph="map"`.
For type-aware retrieval, use types such as `rc:Pattern`, `rc:Claim`,
`rc:Evidence`, or `rc:SourceSpan`; the text filter searches literal facts
attached to each resource, not only labels.

`doxabase.describe_resource`

Returns outgoing and incoming triples for one resource, with available labels
and RDF types. Use it after `list_entities` when lexical search found a resource
but you need its structured claim/evidence/source-span context.

`doxabase.describe_graph_revision`

Returns compact revision context for one `rc:GraphRevision`: summary,
rationale, revision type, changed graph roles, included review/export graph
roles, validation result, export path, graph-count snapshots, and support links.

`doxabase.search`

Lexically searches literal RDF claims and returns matched resources with graph, IRI, label, types, predicate, matched text, and snippet. Use it to rediscover caveats, observations, evidence, labels, path templates, source notes, and column names.

`doxabase.describe_dataset`

Returns bounded context for one dataset/table IRI: row semantics, entity and
snapshot keys, columns, physical/value types, path templates, dataset/layout
verification status and notes, layouts, storage access descriptions, partitions,
direct caveats with impact/severity, upstream caveats inherited through
relationships, provenance transformations,
relationships, directly related datasets, grouped related dataset reasons, and
linked patterns. Column summaries include column names and
owning dataset context when available; related dataset entries include
relationship labels/kinds, grouped reasons can fold same-column relationship
tags, linked patterns include pattern text as their description, and
`linked_pattern_reasons` explains why each pattern matched when available.
Relationship entries and grouped reasons may include `source_caveats`, meaning
caveats attached to source datasets or source-side columns that should remain
visible when interpreting an aggregation, derivation, or foreign key. The
top-level `upstream_caveats` field is a deduped rollup of those inherited
caveats; it is separate from direct `caveats`.
Check `layout_verification_status` and `layout_verification_note` before using
`path_templates` for executable query planning. Child `physical_layouts`,
`storage_accesses`, and `partition_schemes` may carry their own verification
status/notes when the uncertainty belongs to one part of the physical metadata.
Within each linked-pattern reason, `iri` and `pattern_iri` both name the linked
pattern. Scan `match_groups` first for relevance tiers, route labels, resource
kinds, and supporting resources; use raw `matches` when every route matters.
Treat group and tier counts as triage hints, not as confidence scores:
`relevance_tier_counts` counts grouped matches, while `raw_match_count` counts
unfolded route matches. Direct and map-implication groups are usually the
strongest local relevance signals, while claim/observation-supported groups
explain the surrounding lore. Call `doxabase.describe_pattern` before using a
pattern as a decision rule.

`doxabase.describe_context_slice`

Returns a bounded, route-explained subgraph around one or more seed IRIs. Use
`profile="dataset_brief"` for table handoff context, `profile="pattern_brief"`
for pattern support context, and `profile="deep_lore"` when explicit revision
metadata should come along too. Read `resources[].routes` and `route_counts`
before raw triples; those fields explain why each resource entered the slice.
`reading_order` and `route_legend` provide the static reading protocol and
meanings for the routes present in the response. Set `include_trig=true` when
you need importable TriG text, and raise
`max_triples` when `truncated` is true and the slice still looks relevant.
Truncation only affects raw `triples` and `trig`; resources and structured
contexts still describe the full selected slice.

`doxabase.describe_pattern`

Returns compact handoff context for one `rc:Pattern`: pattern text, rationale,
targets, supporting observations, supporting claims, evidence/source spans, and
map implications.

`doxabase.record_observation`

Records a structured observation in the `observations` graph. Optional evidence fields create a linked `rc:Evidence` resource in the `evidence` graph. Use this for point-in-time findings, profile counts, query outputs, and workflow notes that should remain available to later agents.

`doxabase.record_claim_observation`

Records the common richer pattern: one `rc:Observation`, one linked `rc:Claim`,
one `rc:Evidence`, and optionally one `rc:SourceSpan`. Use this for caveat,
join, schema, transformation, access, profile, or interpretation claims that are
more structured than a note but do not require hand-authored TriG.

`doxabase.record_pattern`

Records one `rc:Pattern` in the `patterns` graph and optionally linked
`rc:Evidence` / `rc:SourceSpan` resources in the `evidence` graph. Use this when
several observations, claims, or sources belong together and suggest a more
durable pattern or map implication.

`doxabase.record_claim_reconsideration`

Records that a newer claim weakens, contradicts, supersedes, or refines an
older claim. Use this when exploration changes an agent's mind but the earlier
hunch remains useful context. The helper writes an `rc:ClaimReconsideration`,
adds a direct relation such as `rc:weakens`, optionally writes evidence/source
span context, and marks the older claim as `rc:Weakened`, `rc:Contradicted`, or
`rc:Superseded` when that follows from the relation. `describe_pattern` and
`describe_context_slice` surface incoming and outgoing reconsiderations around
claims, and claim descriptions include a compact `lifecycle_summary`.

`doxabase.record_map_dataset`

Records or updates a dataset/table resource in the `map` graph. Omit
`is_table` for partial updates that should preserve existing dataset/table
typing.

`doxabase.record_map_column`

Records or updates a column resource and can link it to a table with
`rc:hasColumn`.

`doxabase.record_map_caveat`

Records or updates a `rc:KnownCaveat` and can link it to affected datasets.

`doxabase.record_map_storage_access`

Records or updates non-secret storage access metadata and can link it to
datasets.

`doxabase.record_map_physical_layout`

Records or updates file-format/compression layout metadata and can link it to
datasets. Use `layout_verification_status` and `layout_verification_note` when
the physical format or layout has only been generated, proposed, listed, or
query-verified.

`doxabase.record_map_partition_scheme`

Records or updates partition metadata, including partition columns,
granularity, path template, redundant partition key, and layout verification
status/notes. Use it when uncertainty belongs to a partition/path template
rather than to the whole dataset.

`doxabase.record_map_relationship`

Records or updates a relationship resource. Supported relationship types are
`foreign_key`, `shared_identifier`, `derivation`, and `aggregation`. Aggregation
relationships accept `group_by_columns` and `aggregated_columns`; each aggregate
mapping should include `target_column`, `source_columns`, optional
`aggregation_function`, and optional `within_group_ordering`.

`doxabase.record_graph_revision`

Records revision metadata in the `history` graph: changed graph roles, summary,
rationale, optional included review/export graph roles, optional supporting
observations/claims/patterns/evidence, optional `revision_anchors`, validation
result, export path, and graph-count snapshots. It does not compute diffs or
apply graph edits.

`doxabase.stage_graph_revision`

Records a staged graph revision in `history` without applying it. Pass
`additions` and/or `removals` as Turtle payloads with target graph roles. Use
`stance` values such as `rc:ExploratoryHunch`, `rc:CandidateRevision`,
`rc:ConservativeCleanup`, or `rc:AlternativeSystematisation` to preserve the
kind of systematisation move being made. The helper parses patch RDF, previews
graph counts, runs SHACL validation over `validation_scope`, and returns patch
metadata plus structured validation diagnostics when validation reports
results. `revision_anchors` can name graph resources the staged proposal is
about without treating them as evidence or support.

`doxabase.stage_systematisation`

Stages one or more caller-authored RDF framings for the same modelling hunch.
Use it when an agent is choosing between pattern-first, ontology-first, map-first,
or other RDF shapes and wants to keep alternatives reviewable. Each framing may
use simple `graph` + `content` Turtle shorthand, or full `additions` /
`removals` patch lists. Use `shared_additions` / `shared_removals` for
provisional vocabulary or assumptions that every framing should validate
against. Shared patches can include provisional `shapes`; staged shapes are
active during the preview validation for each framing. The helper records the
systematisation intent, anchors, rationale, optional review notes and
recommendations, validation preview, and linked staged revisions; it does not
decide the ontology design for the agent.

`doxabase.stage_pattern_promotion`

Stages one or more caller-authored RDF framings supported by existing
`rc:Pattern` resources. Use it when a pattern looks ready to become map,
ontology, shape, or other durable project structure, but the graph move should
remain reviewable. The helper does not infer the map shape. It uses the selected
patterns as `supporting_patterns`, rolls up their supporting observations,
claims, and evidence, and uses pattern targets plus `map_implication` resources
as revision anchors before delegating to the staged systematisation workflow.

`doxabase.describe_staged_revision`

Returns a staged revision with stance, rationale, support links, revision
anchors, review note/recommendation, patch payloads, before/after count
previews, validation status, and structured SHACL diagnostics such as focus
node, result path, constraint, and messages.

`doxabase.check_staged_revision_apply`

Previews whether one staged revision can apply without mutating graph state.
Returns `can_apply`, already-applied state, per-patch current/preview counts,
count-drift conflicts, and preview validation diagnostics. Use it before
`doxabase.apply_staged_revision` when an agent or human wants an explicit
read-only check.

`doxabase.apply_staged_revision`

Applies one staged revision to its target graph roles after conservative
count-based conflict checks and preview SHACL validation. The helper rejects
already-applied staged revisions and rejects graph-count drift from the staged
`beforeTripleCount` values. On success it records an `rc:AppliedStagedRevision`
history event linked to the staged revision. It is a first apply path, not a
full merge/rebase workflow.

`doxabase.export_staged_revision`

Writes a Markdown review bundle for a staged revision, including validation
diagnostics before patch payloads when validation failed. This is for
human/agent review.

`doxabase.export_staged_revisions`

Writes one Markdown review bundle for several staged revisions in caller-chosen
order. Use it after `stage_systematisation` when failed, repaired, and
alternative framings should travel together for review. Pass
`executive_summary` when the bundle should open with the agent's current
provisional verdict.

## Import and Validation

`doxabase.import_trig`

Imports a TriG file into graph roles. Fixture graph IRIs such as `https://richcanopy.org/graph/map` map to local role names like `map`.

`doxabase.export_graph`

Exports one or more graph roles as one flattened RDF graph file. The default is
the `map` graph in Turtle. Use it for quick single-graph review artifacts. The
result includes per-graph triple counts.

`doxabase.export_trig`

Exports graph roles as a named-graph TriG bundle using graph IRIs such as
`https://richcanopy.org/graph/map`. Use it when preserving graph roles matters,
for example when dumping a scratch capsule after a field trial.

By default this exports the mutable project graphs: `ontology`, `map`,
`observations`, `patterns`, `evidence`, `shapes`, and `history`. Useful presets
are `workflow` / `review_bundle` for `map`, `observations`, `patterns`, and
`evidence`, plus `all_with_seeds` when you explicitly need immutable seed graphs
included too. All-with-seeds bundles may require special import handling because
normal capsules protect `base_ontology` and `base_shapes`.

`doxabase.load_example_fixtures`

Convenience tool that imports the AIS and Polymarket RC fixtures.

When called with `replace=true`, DoxaBase clears the graph roles used by the bundled fixture set once, then imports all fixtures into those roles. This resets the example fixture data without letting later fixtures erase earlier fixtures.

`doxabase.validate_graph`

Runs pySHACL over the selected scope using logical `shapes`
(`base_shapes + shapes`). Use `scope="patterns"` for pattern work and
`scope="all"` after importing fixtures. Validation uses RDFS inference, so
class membership can be inferred from vocabulary such as `rdfs:range`; use
property, node-kind, count, or value constraints when explicit checks matter.
The response includes bounded structured `results` with focus node, result path,
constraint, severity, value, and messages when pySHACL reports failures.
