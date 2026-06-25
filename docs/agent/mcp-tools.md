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
`rc:Evidence`, or `rc:SourceSpan`; the text filter searches literal and
URI-valued facts attached to each resource, not only labels.

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
`arguments`, `reason`, `call`, and an `action_label` that names its role. Use
`mcp_tool_name` for MCP dispatch. Check
`nearby_caveat_links.scope` before treating a table-level caveat as specific to
one column. When no current triples use the requested predicate on the subject,
`predicate_hints` lists nearby predicates already present on that subject with
sample values. Each hint keeps the full predicate IRI and may also include
`predicate_curie`, such as `rc:partitionedBy`, for faster display and follow-up
calls. Use these hints to recover from plausible predicate-name guesses before
assuming the map lacks the concept.

`doxabase.describe_graph_revision`

Returns compact revision context for one `rc:GraphRevision`: summary,
rationale, revision type, changed graph roles, included review/export graph
roles, validation result, export path, graph snapshots with counts and
`sha256:<hex>` content digests, `applies_staged_revision` for applied events,
`applied_source` compact source context for applied staged revision events, and
support links. `applied_source` omits patch content and full diagnostics; call
`describe_staged_revision` on `applies_staged_revision` when those are needed.

`doxabase.list_graph_revisions`

Lists `rc:GraphRevision` resources from `history`, newest first. Use
`revision_type` such as `rc:StagedRevision` to narrow the list. Set
`include_apply_checks=True` when you need staged proposal status without already
knowing which proposals are ready, stale, or already applied. Apply checks are
only populated for revisions with graph patch payloads. Rows include
`record_kind`, `has_patch_payload`, `patch_count`, revision relation links,
selected apply-check blockers/drift summaries, and review-first suggested next
actions. Use `record_kind`, `application_status`, and
`stale_resolution_state` filters to ask directly for applied events, ready
staged proposals, unresolved stale sources, or handled stale sources. Rows also
include `is_current_staged_work`; pass `current_staged_work_only=True` for the
live staged work queue, excluding applied sources and stale rows already handled
by restage. Non-current rows include `not_current_staged_work_reason`, such as
`already_applied_source`, `superseded_by_restage`, or `applied_event_record`.
Status, stale-state, and current-work filters automatically compute apply
checks.
`drift_detail="summary"` is the default and omits exact changed-triple
arrays from snapshot drift rows, but still includes drift relevance, overlap
arrays, and added/removed exact-change counts. Set `drift_detail="exact"` or
call `check_staged_revision_apply` when you need the actual changed triples.

`doxabase.search`

Lexically searches literal RDF claims and URI-valued graph terms, returning
matched resources with graph, IRI, label, types, predicate, matched text, and
snippet. Use it to rediscover caveats, observations, evidence, labels, path
templates, source notes, column names, and exact project vocabulary tokens such
as custom profile metric kinds.

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
The `profile_summary` field gives quick counts of the profile observations
returned in this bounded response, including dataset-level, mapped-column, and
unmapped-column profile counts. It also rolls up profile evidence IRIs and
lists `shared_evidence_iris` that appear on every returned profile observation.
Read total and omitted profile counts before assuming returned profiles are the
whole profile history for the dataset.
When mixed profile history means no evidence is shared by all returned profiles,
`profile_run_candidates` lists evidence IRIs that support more than one returned
profile, sorted by returned profile count. Each candidate includes
`profile_observation_iris`, the returned profile observations linked to that
evidence IRI, so a handoff can seed `describe_context_slice` or inspect the run
without reconstructing membership from nested profile lists.
Its `handoff_note` is a compact reading cue for profile-only handoffs: profile
lore is observed evidence, while storage/path/layout warnings remain physical
query-planning metadata gaps.
Relationship entries and grouped reasons may include `source_caveats`, meaning
caveats attached to source datasets or source-side columns that should remain
visible when interpreting an aggregation, derivation, or foreign key. The
top-level `upstream_caveats` field is a deduped rollup of those inherited
caveats; it is separate from direct `caveats`.
Check `layout_verification_status` and `layout_verification_note` before using
`path_templates` for executable query planning. Child `physical_layouts`,
`storage_accesses`, and `partition_schemes` may carry their own verification
status/notes when the uncertainty belongs to one part of the physical metadata.
The `operational_warnings` field carries dataset-owned physical-metadata
`QueryPlanningIssue` objects that also appear in `describe_query_context.issues`;
scan it when a full dataset handoff should still surface query-planning hazards
such as unverified layouts. Candidate-derived issues such as path/template
composition warnings are only guaranteed in `describe_query_context.issues` and
`query_target_candidates[].review_reasons`. These warnings carry
`domain="query_planning"` so their severity is not confused with profile
recording or graph validation status.
Info-level issues such as
`verification_status_not_recorded` make missing verification status visible
without changing query-planning readiness. Query-context `analysis_warnings`
are separate caveat warnings for analytical interpretation after a query can be
planned and carry `domain="analysis"`.
Within each linked-pattern reason, `iri` and `pattern_iri` both name the linked
pattern. Scan `match_groups` first for relevance tiers, route labels, resource
kinds, and supporting resources; use raw `matches` when every route matters.
Treat group and tier counts as triage hints, not as confidence scores:
`relevance_tier_counts` counts grouped matches, while `raw_match_count` counts
unfolded route matches. Direct and map-implication groups are usually the
strongest local relevance signals, while claim/observation-supported groups
explain the surrounding lore. Call `doxabase.describe_pattern` before using a
pattern as a decision rule.

`doxabase.describe_profile_run`

Returns the profile observations for one dataset that link to one evidence IRI.
Use it after `describe_dataset().profile_summary.profile_run_candidates` points
at a shared profiler-run evidence resource, especially when the bounded
`describe_dataset` response has omitted profile observations. The result
includes the dataset and evidence summaries, top-level returned/total/omitted
count fields,
`profile_observation_iris`, and profile rows split into dataset-level,
mapped-column, and unmapped-column observations. The three list fields are
`dataset_profile_observations`, `mapped_column_profile_observations`, and
`unmapped_column_profile_observations`; use the top-level
`returned_dataset_profile_count`, `returned_mapped_column_profile_count`,
`returned_unmapped_column_profile_count`, `returned_profile_count`, and matching
`total_*` / `omitted_*` fields when checking whether a handoff contains the
whole profiler pass. `limit=None`
returns the full matching run; pass a positive `limit` only when a client
intentionally wants a capped payload. The run is inferred from profile
observations linked to the requested evidence IRI, not from a separate
persisted profile-run node.

`doxabase.describe_query_context`

Returns a compact read-only projection for query planning around one dataset:
dataset summary, physical-metadata readiness, `readiness_note`, an `issues`
list for missing, risky, or informational physical metadata, `analysis_warnings`
for caveats that matter after a query can be planned, planning notes, columns,
path templates, derived `query_target_decision` and `query_target_candidates`,
physical layouts, storage access descriptions, partition schemes,
dataset/layout verification status and note, and caveats. Use it before
drafting DuckDB/S3/local-file queries when you need to decide whether graph
metadata is executable or only useful for orientation, especially when you need
physical metadata and warnings without the full relationship/pattern handoff in
`describe_dataset`. Read `query_target_decision` first; its zero-based
`candidate_index` points into `query_target_candidates`. Candidate
`review_required` includes whole-context blockers; `direct_review_required`
ignores sibling blockers and shows which target candidates have their own
storage/path/layout problem.

`doxabase.draft_query_plan`

Returns a non-executed, review-gated physical plan draft over
`describe_query_context`. It currently supports `engine="duckdb"` and selects
the candidate named by `query_target_decision.candidate_index`. The payload
includes the selected candidate, scan hint such as `read_parquet`, URI/path
template, parsed `required_bindings`, structured `binding_requirements`,
non-secret storage environment hints, copied issues and analysis warnings,
caveats, and a `review_gate`. Binding rows preserve the source text and say
when DoxaBase has not inferred derivation or runtime values. `review_gate`
includes `blocking_reason_codes`, `all_issue_codes`, and the legacy
`reason_codes` alias for blocking reasons. The `scan` card includes
dataset-level verification notes plus template lineage and source verification
fields, so surprising shared or inherited path templates stay attached to their
source resource and warning notes. It does not resolve endpoint profiles,
credentials, object existence, or execute SQL.

`doxabase.describe_context_slice`

Returns a bounded, route-explained subgraph around one or more seed IRIs. Use
`profile="dataset_brief"` for table handoff context, `profile="pattern_brief"`
for pattern support context, and `profile="deep_lore"` when explicit revision
metadata should come along too. Dataset/deep-lore slices include bounded profile
observations, observed value-frequency nodes, scalar profile metric nodes, and
profile metric kinds returned through the dataset context. They can also start
from a profile observation, observed profile metric node, or metric-kind IRI
used by profile metrics. Deep-lore slices can also start from an
`rc:GraphRevision` seed and expand support, evidence, anchors, application,
restage, and alternative links. `seed_profile_observations` preserves structured
profile summaries selected by those profile/metric seeds even when the same row
is older than the bounded dataset profile list. Read `resources[].routes` and `route_counts` before
raw triples; those fields explain why each resource entered the slice.
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

Records a structured observation in the `observations` graph. Optional evidence
fields create a linked `rc:Evidence` resource in the `evidence` graph. Use this
for point-in-time findings, profile counts, query outputs, and workflow notes
that should remain available to later agents. For validation-clean evidence,
include `evidence_sources`; `evidence_summary` alone is descriptive prose, not a
source identity. When `observed_column` names a column that is not yet in the
map, `observed_column_name` can preserve the source-level column name without
promoting the column into current map state.

`doxabase.record_dataset_profile`

Records one dataset profile: a profile observation, optional evidence,
an optional current-best map row-count snapshot, and an optional
agent-authored profile pattern linked back to the observation. Use it when a
profile run should preserve both the raw noticing and the emerging synthesis.
`describe_dataset` surfaces recent dataset profile observations and their
sample, row, null, distinct, observed value-frequency, and scalar metric values.
Use `sample_scope` for the population or slice covered by the profile, and
`sample_method` for how the profile was produced.
Use `profile_metrics=[{"metric": "rc:MinimumValue", "value": ...}]` for
observed min/max/mean/median-style profiler output. These scalar metrics are
observed profile evidence, not constraints, shapes, allowed values, or durable
map semantics by themselves. Use `list_entities(type="rc:ProfileMetricKind",
graph="base_ontology")` to list built-in metric kinds before recording. Use
full project-specific metric kind IRIs for profiler outputs that do not fit the
base `rc:` metric kinds; define those terms in the project ontology once they
become durable vocabulary. `graph="ontology"` is an effective-ontology listing,
so it includes built-in `base_ontology` results; filter returned entities by
`graph == "ontology"` when you need project-local metric kinds only. DoxaBase
rejects unknown `rc:` metric kinds so typos
such as `rc:MinValue` do not become ad hoc RDF. A metric item may include
`target` when the scalar is specifically about a resource narrower than the
profile observation as a whole. Profile evidence entries include source strings
and source spans when recorded.
`update_map_snapshot` defaults to true; set it to false for scratch or tentative
row counts that should remain observation-only. If that is a brand-new dataset,
`describe_dataset()` may not find it until map context is recorded; use
`describe_profile_run(dataset_iri, evidence_iri)` or profile-observation
context-slice seeds for handoff retrieval. When matching profile observations
exist, the `describe_dataset()` not-found error includes this recovery hint and
points at `record_map_dataset` for creating map context. If the helper creates a
pattern, the profile evidence is linked to that pattern as well as the
observation.
For a capsule that only records profile lore, `describe_dataset` may still emit
missing storage/path/layout warnings. Those are query-planning gaps rather than
profile validation failures. Read `profile_summary.handoff_note` when deciding
whether a profile-only handoff is missing physical query-planning metadata or
missing profile evidence.

`doxabase.record_profile_bundle`

Records one dataset profile plus zero or more related column profiles from the
same profiling pass. It writes ordinary profile observations, optional map
updates, optional linked profile patterns, and evidence using the same semantics
as `record_dataset_profile` and `record_column_profile`.
Use it when a profiler has produced a dataset-level summary and a set of column
summaries that share run metadata, evidence fields, or sample context.
The top-level `observed_at`, `observed_by`, `evidence_summary`,
`evidence_sources`, `sample_size`, `sample_scope`, and `sample_method` values
default into each column profile unless the column entry overrides them.
Pass `shared_evidence_iri` when the dataset profile and column profiles should
all point at one shared profiler-run `rc:Evidence` resource. A column entry can
still override that with its own `evidence_iri`.
The returned bundle includes `shared_evidence_iri` at top level for quick
run-level checks and `handoff_entrypoints` with profile observation seeds,
availability flags, and suggested next calls for the next agent.
In `handoff_entrypoints`, prefer `updated_map_column_iris` for columns whose map
facts were written by this bundle call, and `mapped_profiled_column_iris` for
all bundled column profiles that are mapped after the call. `map_column_iris`
remains as a legacy alias for `updated_map_column_iris`.
Use `column_defaults` for repeated column options such as
`{"update_map_column": false}`. Each `column_profiles[]` item accepts the same
fields as `record_column_profile` and must include `column_iri`, `column_name`,
and `summary`. After recording a bundle, `describe_dataset().profile_summary`
lists shared evidence IRIs, profile run candidates, grouped profile observation
IRIs, and a handoff note that can help a later agent recognise one profiler run
without walking every observation.
Use `describe_profile_run(dataset_iri, shared_evidence_iri)` when the full run
may be wider than the bounded dataset profile lists or when an observation-only
brand-new dataset is not yet available through `describe_dataset()`. If the bundle's
`pattern_summary`/`pattern_text` arguments are supplied, the helper-created
pattern is supported by the dataset profile observation only by default. Set
`pattern_support_scope="all_profiles"` when the helper-created pattern should
be supported by the dataset profile and every bundled column profile. For a
synthesis that also needs claims or hand-picked support, call `record_pattern`
after the bundle using `describe_profile_run(...).profile_observation_iris`
plus the extra support, and pass the shared `evidence_iri` to reuse the
profile-run evidence.

`doxabase.record_column_profile`

Records one column profile: a profile observation with
`observed_column`, optional evidence, optional current-best map column metadata,
and an optional linked profile pattern. Use it when profiling output says
something useful about nullability, distinctness, physical type, or identity
behavior for a column. Column profile observations appear on the matching
`describe_dataset().columns[]` entry, including any observed value-frequency
pairs and scalar metrics supplied by the profiler.
Use `sample_scope` and `sample_method` to make sample caveats retrievable
without parsing the evidence prose.
Scalar `profile_metrics` are observed evidence, not constraints, shapes, allowed
values, or durable map semantics by themselves.
`update_map_column` defaults to true; set it to false when counts or observed
values are only sample evidence. For value-frequency guardrails, record the
profile, then add a `record_claim_observation` and synthesize both with
`record_pattern`.
If `update_map_column=false` and the observed column is not yet in the map,
`describe_dataset` surfaces the profile under
`unmapped_column_profile_observations`. The profile keeps the supplied column
name as `observed_column_name`; `observed_column.column_name` also uses that
name as a fallback until the column becomes a current map column.

`doxabase.record_claim_observation`

Records the common richer pattern: one `rc:Observation`, one linked `rc:Claim`,
one `rc:Evidence`, and optionally one `rc:SourceSpan`. Use this for caveat,
join, schema, transformation, access, profile, or interpretation claims that are
more structured than a note but do not require hand-authored TriG.

`doxabase.record_pattern`

Records one `rc:Pattern` in the `patterns` graph and optionally linked
`rc:Evidence` / `rc:SourceSpan` resources in the `evidence` graph. Use this when
several observations, claims, or sources belong together and suggest a more
durable pattern or map implication. Pass `evidence_iri` when the pattern should
reuse an existing evidence resource, such as shared profile-run evidence from
`record_profile_bundle`. `map_implications` is a list of resource references:
pass IRIs or CURIEs for map resources or assertion nodes the pattern may affect.
Put explanatory prose in `pattern_text`, `rationale`, observations, or claims.

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
typing. Resource-valued links and controls such as `columns`, `caveats`,
`storage_accesses`, `physical_layouts`, `companion_datasets`, `extra_types`,
`row_semantics`, `schema_stability`, and `layout_verification_status` expect
IRIs or CURIEs like `rc:EventRow`, not descriptive prose.

`doxabase.record_map_column`

Records or updates a column resource and can link it to a table with
`rc:hasColumn`. Resource-valued fields such as `physical_type`, `value_type`,
and `table_iri` expect IRIs or CURIEs, not prose.

`doxabase.record_map_caveat`

Records or updates a `rc:KnownCaveat` and can link it to affected datasets.
Use prose for the caveat description, and use IRIs or CURIEs for `severity` and
`targets`.

`doxabase.record_map_storage_access`

Records or updates non-secret storage access metadata and can link it to
datasets. Use IRIs or CURIEs for resource-valued controls such as
`storage_protocol`, `access_mode`, `layout_verification_status`, and
`datasets`. For S3-compatible storage, include enough non-secret runtime
orientation such as `endpoint_profile`, `credential_reference`, or `region`.
For non-S3 protocols, prefer protocol-appropriate roots, URLs, or connection
references rather than S3-shaped `bucket_name`/`key_prefix` alone. Complete
path templates are checked against the protocol and bucket/prefix metadata, and
relative templates that already include the recorded key prefix are treated as
review-only because path composition would duplicate that prefix. A relative
dataset path template does not make an otherwise rootless storage access ready
for query planning; record the storage access location as well. When the storage
root itself is the only candidate dataset location, set `location_kind="object"`
only if that root names the dataset object/location exactly. Use
`location_kind="directory"`, `"prefix"`, or `"connection"` for broader roots and
add a path template before executable use.

`doxabase.record_map_physical_layout`

Records or updates file-format/compression layout metadata and can link it to
datasets. Use `layout_verification_status` and `layout_verification_note` when
the physical format or layout has only been generated, proposed, listed, or
query-verified. Use IRIs or CURIEs for resource-valued controls such as
`file_format`, `compression_codec`, and `datasets`.

`doxabase.record_map_partition_scheme`

Records or updates partition metadata, including partition columns,
granularity, path template, redundant partition key, and layout verification
status/notes. Use it when uncertainty belongs to a partition/path template
rather than to the whole dataset. Use IRIs or CURIEs for partition columns,
granularity, redundant partition keys, layout verification status, and linked
datasets. Dataset descriptions expose all partition columns as
`partition_columns`; the older singular `partition_column` field is retained as
a first-column compatibility shortcut. Treat `partition_columns` as unordered
unless a future response explicitly carries ordering metadata.

`doxabase.record_map_relationship`

Records or updates a relationship resource. Supported relationship types are
`foreign_key`, `shared_identifier`, `derivation`, and `aggregation`. Aggregation
relationships accept `group_by_columns` and `aggregated_columns`; each aggregate
mapping should include `target_column`, `source_columns`, optional
`aggregation_function`, and optional `within_group_ordering`. Relationship
endpoints, columns, functions, and properties are resource-valued fields, so use
IRIs or CURIEs rather than prose. Dataset relationship descriptions expose
`relationship_kind` as the RDF class IRI and `relationship_type` as the helper
token such as `foreign_key` or `aggregation`.

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
results. The returned staged revision record includes the `summary`,
`rationale`, `review_note`, and `review_recommendation` that were recorded, so
scratch logs do not need an immediate describe call for the proposal headline.
`revision_anchors` can name graph resources the staged proposal is about without
treating them as evidence or support.

`doxabase.stage_map_assertion_change`

Stages a reviewable add/remove/replace for one `map` assertion. Use this before
generic `stage_graph_revision` when the change is a single subject/predicate
assertion such as a physical type, caveat link, nullability, path, layout, or
relationship claim. The helper calls `describe_assertion_support`, generates
small Turtle addition/removal patches, records related observations, claims,
patterns, evidence, caveat scopes, and assertion anchors on the staged revision,
and returns the assertion-support snapshot, staged revision record, and a compact
`judgement_panel`. Check the panel first for current/proposed values, caveat
scopes, semantic risk level/reasons, value-type context, reasons the current
value may be intentional, strongest route summaries, impact spotlight entries,
and safety notes. For physical type changes, `value_type_context` surfaces
current `rc:valueType` resources and declared `rc:requiredPhysicalType` values.
`target_value` names the requested object for add, replace, and remove changes;
`removed_value` is populated for remove changes so reviewers do not have to
interpret legacy `proposed_value` as the removed value.
Routes marked `generic_value_only` matched only shared values such as
`rc:Varchar`; treat them as weak context. Drill into `assertion_support` and
`describe_staged_revision` when the change needs more thought.
For `replace`, the generated patch set adds the requested assertion and removes
current same-subject/predicate values except the requested object. The recorded
patch sequence shows the exact preview/apply order. If the requested value is
already present on a multi-valued predicate, treat the replace as mainly a
removal of the other current values and review their support routes before
applying. It does not apply the change; use `describe_staged_revision` and
`check_staged_revision_apply` before application.
A competing singleton `add`, such as a second `rc:physicalType`, may correctly
fail validation while a `replace` candidate remains reviewable. Re-run apply
checks for sibling staged assertions after any successful apply.
`can_apply=True` means the patch replays and validates mechanically; it does not
mean the semantic change is wise.

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
by replaying an older stale staged proposal against current graph state;
`restaged_by` is present when this staged revision is the stale source for a
later refreshed proposal; `current_restaged_by` follows deeper restage chains to
the latest known successor; `restage_reason` gives the compact reason when it
can be derived from the recorded rationale. `applied_by` and
`application_status="already_applied"` are present after the staged revision is
applied.
`judgement_panel` is present for simple single-assertion `map`
changes that still replay cleanly; it is absent for complex or stale staged
revisions. When the panel is absent, `stored_review_context` may still summarize
persisted review/support metadata such as review-note signals, linked support
counts, semantic risk reasons, and attention impacts. It is not a replayed
panel. Impact
entries are deterministic consequence notes, not validation failures. They call
out changes such as removed caveats, changed physical/value types,
nullability, row/grain signals, grouping, layout/path assertions, and
documentation attached to the same subject as another semantic change, with
related observations, claims, patterns, evidence, and revisions when DoxaBase can
find them.
Pass `include_current_apply_check=true` when reviewing one staged revision and
you need a compact live apply branch beside the patch payload. The nested
`current_apply_check` includes status, decision, blockers, current validation
headline, drift summaries, and suggested next actions. It omits full
`patch_checks`, `conflicts`, and `validation_results`; call
`check_staged_revision_apply` for those.

`doxabase.check_staged_revision_apply`

Previews whether one staged revision can apply without mutating graph state.
Returns `can_apply`, already-applied state, per-patch current/preview/effective counts,
count-drift and snapshot-digest conflicts, preview validation diagnostics,
`status`, `decision`, `summary`, `review_recommended`, `blocking_reasons`,
`recommended_resolution`, `validation_skipped_reason`, `count_drifts`,
`snapshot_drifts`, and
structured `suggested_next_actions`. The response includes both
`staged_revision_iri` and the alias `revision_iri` for script-friendly payload
handoffs. Read `status`, `decision`, and `summary` first:
`ready` means the staged patch replays
and validates with an effective graph delta, with decision `review_then_apply`;
`noop` means replay validates but would not change graph triples and uses
decision `inspect_no_effective_change`; `conflict` with
`target_count_drift` or `target_digest_drift` means graph counts or content
digests drifted since staging and can usually be restaged; `conflict` with
`patch_conflict` means the stored patch is unreplayable and uses decision
`inspect_patch_conflict`; `validation_failed` means patch counts replay but
SHACL diagnostics need inspection; `already_applied` means an applied revision
event exists. When validation did not run,
`validation_skipped_reason` explains why. `count_drifts` records
expected/current graph counts and deltas for count conflicts, plus whether the
staged patch triples themselves are currently present, absent, or mixed in the
target graph. `patch_checks` records effective add/remove counts and
already-present/absent payload triples for partial or no-op replay.
`snapshot_drifts` records staged/current `sha256:<hex>` digest
mismatches, including same-count graph changes. For revisions staged with the
current runtime, it also includes exact triples added to and removed from the
target graph since the stored snapshot. It also includes `drift_relevance`,
`patch_overlap_subjects`, `patch_overlap_predicates`, `patch_overlap_objects`,
and `revision_anchor_overlap` so agents can separate "no staged patch subject
changed" from stronger overlaps. Predicate and object overlap can be broad, so
they are review hints rather than apply decisions.
`broad_patch_object_overlap` is the weak object-overlap label for shared
class/type vocabulary such as `rc:Dataset`. Anchor overlap means exact drift
touched a resource the staged revision named as review context. Older revisions may report
`exact_changed_triples_available=False` when they predate snapshot row storage.
Suggested actions are ordered review-first, so inspect/export suggestions
come before mutation calls such as apply or restage. Use it before
`doxabase.apply_staged_revision` when an agent or human wants an explicit
read-only check.

`doxabase.describe_applied_revision_diff`

Returns stored before/after snapshot diffs for an applied staged revision. Pass
the applied revision event IRI, not the staged source IRI. The response links
`applied_revision_iri` to `staged_revision_iri`, lists changed graphs, and
returns one `graph_diffs[]` row per graph with before/after counts, digests, and
exact added/removed counts when snapshot rows are available. Changed-triple
arrays are omitted by default; pass `include_triples=true` to include them, with
`max_triples` capping each added/removed array. Use this after
`describe_graph_revision()` when an agent needs the actual triples changed by an
applied staged revision; use
`describe_staged_revision()` for patch payloads, validation diagnostics,
impacts, and judgement context.

`doxabase.restage_staged_revision`

Creates a fresh staged revision from a conflicted staged revision's patch
payloads, rerunning preview counts and validation against the current graph
state. Use it for `target_count_drift` or `target_digest_drift` from
`check_staged_revision_apply`, especially when an unrelated graph edit made an
otherwise still-useful proposal stale. The new staged revision records
`rc:restagesRevision` / `restaged_from` back to the stale proposal and preserves
support links, anchors, stance, review notes, and patch payloads. Its generated
rationale summarizes the stale apply-check drift evidence, including exact
snapshot drift triples when available. It does not merge semantic conflicts,
repair SHACL failures, or apply the result; review the new staged revision and
run `check_staged_revision_apply` again. If the stale source already has a
`restaged_by` / `current_restaged_by` successor, this helper refuses to create a
parallel successor; inspect or restage the current successor instead.

`doxabase.restage_staged_revisions`

Batch recovery helper for stale staged revisions. It accepts staged revision
IRIs, checks each current apply state, restages count/digest-drift rows that do
not already have a `restaged_by` successor, skips already-handled stale sources
and non-restageable rows, and returns per-source actions, old-to-current mappings,
`review_revision_iris`, `revision_summaries`, and `bundle_summary`. Pass `path`
to write the grouped Markdown bundle over stale sources and current refreshed
successors. Pass `dry_run=true` to classify the same batch without creating
successors; restageable drift conflicts return `action="would_restage"` and are
listed in `would_restage_revision_iris`. `patch_conflict` rows are
`skipped_not_restageable` with `not_restageable_reason="patch_conflict"` and
should be repaired or replaced with a new staged candidate. Ready,
already-applied, and validation-failed rows use the same action with their own
compact reasons; `not_restageable_revision_iris_by_reason` groups those skipped
IRIs for triage. In dry-run rows that would be restaged,
`current_revision_by_source` still points to the stale source because no
successor exists yet. For `skipped_not_restageable`, inspect `status_before` and
`decision_before` to distinguish ready, validation-failed, and already-applied
rows. Each item also carries `status_after`, `decision_after`,
`stale_resolution_state_after`, `blocking_reasons_after`, and effective triple
deltas for `current_revision_iri` after the batch decision. Treat
`restaged_revision_iris` as a creation list, not an apply queue; use
`bundle_summary.ready_restage_successor_revision_iris` plus a final apply check
for candidates to apply. If an already-handled row has
`stale_resolution_state_after="restaged_successor_stale_unresolved"`, its
current successor is stale too; inspect or restage `current_revision_iri`.
Each item also carries `restaged_from` when its source is itself a refreshed
successor. It does not apply refreshed revisions; review and apply
remain explicit follow-up steps. In dry-run mode, passing `path` still writes
the requested review export while leaving graph history unmutated.

`doxabase.apply_staged_revision`

Applies one staged revision to its target graph roles after conservative
graph-state conflict checks and preview SHACL validation. The helper rejects
already-applied staged revisions and rejects target graph count or digest drift
from the staged `beforeTripleCount` values and graph snapshots. Patch checks
follow the recorded `rc:patchSequence` order from the original preview. On
success it records an `rc:AppliedStagedRevision` history event linked to the
staged revision. The return payload includes
`post_apply_recheck_revision_iris` for other current staged revisions sharing
changed graphs, plus `post_apply_recheck_revisions` rows with each revision's
`changed_graphs` and `shared_changed_graphs`. Re-run apply checks on those rows
before further mutation. It is a first apply path, not a full merge/rebase
workflow.

`doxabase.export_staged_revision`

Writes a Markdown review bundle for a staged revision, including validation
diagnostics before patch payloads when validation failed. The bundle also
includes a live `Current Apply Check`, so stale exports show conflict status,
count or digest drift, validation-skipped reason, and suggested next calls as of
export time. Exports can include a `Semantic Review Warning` before the apply
check when the live apply check reports semantic risk. For simple
single-assertion `map` changes that still replay cleanly, the export includes a
`Judgement Panel` section with values, value-type context, rationale, caveats,
routes, and safety notes. Stale single-assertion exports may lack the judgement
panel but still warn from stored review context. Restaged exports include a
top metadata `Restage headline` before the apply check; stale original exports
include a top `Restaged by` line when a refreshed successor already exists.
This is for human/agent review.

`doxabase.export_staged_revisions`

Writes one Markdown review bundle for several staged revisions in caller-chosen
order. Use it after `stage_systematisation` when failed, repaired, and
alternative framings should travel together for review. Pass
`executive_summary` when the bundle should open with the agent's current
provisional verdict. The summary table includes each staged revision's current
apply status, decision, current validation state, and staged-time validation
result. The returned payload includes `revision_summaries` with the same status
rows as structured data: current apply status, blockers, validation state,
alternative/restage links, authored review recommendations, live
`apply_recommended_resolution` guidance, effective `summary_recommendation`
text matching the grouped Markdown table, recommendation source/scope fields,
and suggested next actions. Stale
sources that already have `restaged_by` point suggested actions at the refreshed
current successor instead of another restage. `current_restaged_by` follows
deeper restage chains while `restaged_by` preserves the direct provenance edge.
`current_alternative_to` follows refreshed successors while `alternative_to`
preserves provenance. The payload also returns
`bundle_summary` with status/state counts, unresolved stale sources, handled
stale sources, ready successors, all validation-failed revisions by current
apply status, deduped
`recommended_review_iris`, `recommended_mutation_review_iris`,
`recommended_apply_or_restage_review_iris`, `recommended_repair_review_iris`,
and `recommended_applied_inspection_iris`. `bundle_summary.warnings` calls out
bundle-level sequencing hazards such as ready/no-op reviews sharing a changed
graph that should be re-checked after each apply;
`post_apply_recheck_revision_iris` is the machine-readable affected-revision
list for pre-apply grouped-review hazards.
`sequential_apply_recheck_candidate_iris` is a clearer alias for the same list.
`apply_staged_revision` returns the post-apply affected-sibling queue for the
revision that was actually applied.
Treat
`recommended_mutation_review_iris` as a broad compatibility queue and prefer the
narrower apply/restage, repair, or applied-inspection fields when routing
automation.
Grouped Markdown mirrors those buckets in a `Review Queues` section so human
reviewers do not have to infer the routing from the summary table alone.
Bundles with restaged revisions include a `Restage Context` section near the
top. When a stored alternative target has a restaged successor, grouped
Markdown includes `Alternative Context` with the current comparison target.
Relative export paths are resolved from the repository root and returned as
normalized absolute paths.

## Import and Validation

`doxabase.import_trig`

Imports a TriG file into graph roles. Fixture graph IRIs such as `https://richcanopy.org/graph/map` map to local role names like `map`.

`doxabase.export_graph`

Exports one or more graph roles as one flattened RDF graph file. The default is
the `map` graph in Turtle. Use it for quick single-graph review artifacts. The
result includes per-graph triple counts.

`doxabase.replace_graph_triples`

Removes caller-authored Turtle triples and inserts caller-authored replacement
triples in one mutable graph. The default `allow_count_change=false` makes this
a controlled same-count replacement helper: DoxaBase checks the effective
mutation first and raises before writing if the graph count would change. The
result includes before/after counts, before/after content digests, actual
removed/added triple counts, `same_count`, and `digest_changed`.

Use it for small graph maintenance moves and staged-revision field trials where
you need a same-count digest drift without exporting, RDFLib-editing, and
re-importing the whole graph. It is not a semantic merge/rebase tool.

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
