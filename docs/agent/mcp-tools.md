# MCP Tools

The MCP server is intentionally thin. It exposes the current Python API plus short operational docs.

## Documentation

`doxabase.list_docs`

Returns available agent docs with IDs, titles, and descriptions.

`doxabase.get_doc`

Returns one markdown doc by ID. Use `max_chars` to bound output. Start with
`doc_id="start_here"` when arriving cold or resuming after compaction.

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

`doxabase.describe_assertion_support`

Explains one subject/predicate/object map assertion, or all assertions matching
one subject/predicate when `object` is omitted. Returns whether the assertion is
present, exact matching triples, current same-subject/predicate triples,
subject/object resource summaries, an owner-dataset summary for column subjects,
nearby caveats, selected direct layout/path context triples, related
observations, claims, patterns, evidence, revisions, a support-scope note, an
absence note, scoped caveat-link metadata, grouped route summaries and raw route
explanations for related lore, and structured suggested next actions plus
display call strings. Use it for questions like "why is this caveat link here?"
or "what lore supports this column type?" It is retrieval context, not proof
that the assertion is correct.
When an exact requested object is absent, inspect
`same_subject_predicate_triples` and `absence_note` before deciding whether the
current map already contains a more careful value. For column subjects, follow
the owner-dataset suggested actions when you need table-level lore. For layout,
partition, or storage assertions, inspect `nearby_context_triples` before using
the assertion as executable planning context. Use `related_route_summaries` to
find the most directly related lore resources, and `related_routes` when you
need to know whether an observation, claim, pattern, evidence item, or revision
matched the subject, requested object, current same-slot object, or another
nearby lore item. Prefer `suggested_next_actions` over parsing
`suggested_next_calls`; each action has `tool_name`, `mcp_tool_name`,
`arguments`, `reason`, and `call`. Use `mcp_tool_name` for MCP dispatch. Check
`nearby_caveat_links.scope` before treating a table-level caveat as specific to
one column.

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

`doxabase.record_dataset_profile`

Records one dataset profile bundle: a profile observation, optional evidence,
an optional current-best map row-count snapshot, and an optional
agent-authored profile pattern linked back to the observation. Use it when a
profile run should preserve both the raw noticing and the emerging synthesis.

`doxabase.record_column_profile`

Records one column profile bundle: a profile observation with
`observed_column`, optional evidence, optional current-best map column metadata,
and an optional linked profile pattern. Use it when profiling output says
something useful about nullability, distinctness, physical type, or identity
behavior for a column.

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

`doxabase.stage_map_assertion_change`

Stages a reviewable add/remove/replace for one `map` assertion. Use this before
generic `stage_graph_revision` when the change is a single subject/predicate
assertion such as a physical type, caveat link, nullability, path, layout, or
relationship claim. The helper calls `describe_assertion_support`, generates
small Turtle addition/removal patches, records related observations, claims,
patterns, evidence, caveat scopes, and assertion anchors on the staged revision,
and returns the assertion-support snapshot, staged revision record, and a compact
`judgement_panel`. Check the panel first for current/proposed values, caveat
scopes, value-type context, reasons the current value may be intentional,
strongest route summaries, impact spotlight entries, and safety notes. For
physical type changes, `value_type_context` surfaces current `rc:valueType`
resources and declared `rc:requiredPhysicalType` values. Routes marked
`generic_value_only` matched only shared values such as `rc:Varchar`; treat them
as weak context. Drill into `assertion_support` and `describe_staged_revision`
when the change needs more thought.
For `replace`, the generated patch set adds the requested assertion and removes
current same-subject/predicate values except the requested object. The recorded
patch sequence shows the exact preview/apply order. It does not apply the change;
use `describe_staged_revision` and `check_staged_revision_apply` before
application.

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
previews, validation status, structured SHACL diagnostics such as focus node,
result path, constraint, and messages, optional `judgement_panel`, and `impacts`
review context. `restaged_from` is present when this staged revision was created
by replaying an older stale staged proposal against current graph counts.
`judgement_panel` is present for simple single-assertion `map`
changes that still replay cleanly; it is absent for complex or stale staged
revisions. Impact
entries are deterministic consequence notes, not validation failures. They call
out changes such as removed caveats, changed physical/value types,
nullability, row/grain signals, grouping, layout/path assertions, and
documentation attached to the same subject as another semantic change, with
related observations, claims, patterns, evidence, and revisions when DoxaBase can
find them.

`doxabase.check_staged_revision_apply`

Previews whether one staged revision can apply without mutating graph state.
Returns `can_apply`, already-applied state, per-patch current/preview counts,
count-drift conflicts, preview validation diagnostics, `status`, `decision`,
`summary`, `review_recommended`, `blocking_reasons`,
`recommended_resolution`, `validation_skipped_reason`, and structured
`suggested_next_actions`. Read `status`, `decision`, and `summary` first:
`ready` means the staged patch replays
and validates, with decision `review_then_apply`; `conflict` usually means graph
counts drifted since staging; `validation_failed` means patch counts replay but
SHACL diagnostics need inspection; `already_applied` means an applied revision
event exists. When validation did not run, `validation_skipped_reason` explains
why. Suggested actions are ordered review-first, so inspect/export suggestions
come before mutation calls such as apply or restage. Use it before
`doxabase.apply_staged_revision` when an agent or human wants an explicit
read-only check.

`doxabase.restage_staged_revision`

Creates a fresh staged revision from a conflicted staged revision's patch
payloads, rerunning preview counts and validation against the current graph
state. Use it for the count-drift branch from
`check_staged_revision_apply`, especially when an unrelated graph edit made an
otherwise still-useful proposal stale. The new staged revision records
`rc:restagesRevision` / `restaged_from` back to the stale proposal and preserves
support links, anchors, stance, review notes, and patch payloads. It does not
merge semantic conflicts, repair SHACL failures, or apply the result; review the
new staged revision and run `check_staged_revision_apply` again.

`doxabase.apply_staged_revision`

Applies one staged revision to its target graph roles after conservative
count-based conflict checks and preview SHACL validation. The helper rejects
already-applied staged revisions and rejects graph-count drift from the staged
`beforeTripleCount` values. Patch checks follow the recorded
`rc:patchSequence` order from the original preview. On success it records an
`rc:AppliedStagedRevision` history event linked to the staged revision. It is a
first apply path, not a full merge/rebase workflow.

`doxabase.export_staged_revision`

Writes a Markdown review bundle for a staged revision, including validation
diagnostics before patch payloads when validation failed. For simple
single-assertion `map` changes that still replay cleanly, the export includes a
`Judgement Panel` section with values, value-type context, rationale, caveats,
routes, and safety notes. This is for human/agent review.

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
