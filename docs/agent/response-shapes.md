# Response Shape Examples

Use this doc when scripting against the Python API or MCP helper payloads. The
workflow docs explain what to do; this page names the fields agents commonly
need so they do not have to infer near-miss attribute names.

Python API calls return dataclass-like objects. MCP helper functions in
`doxabase.mcp_tools` return JSON-like dictionaries. Prefer MCP helpers when you
need serializable payloads; prefer the Python API when you are running a local
scratch capsule script.

## Docs And Overview

`list_docs_tool()` returns:

```python
{
    "docs": [
        {"id": "start_here", "title": "Start Here", "description": "..."},
        ...
    ]
}
```

`graph_overview_tool(db)` returns:

```python
{
    "named_graphs": [
        {
            "name": "map",
            "description": "Current best project/data map",
            "mutable": True,
            "system_seed": False,
            "source_path": None,
            "triple_count": 574,
        },
        ...
    ],
    "class_counts": [{"class": "rc:Column", "count": 42}, ...],
    "predicate_counts": [{"predicate": "rdf:type", "count": 574}, ...],
    "key_counts": {"datasets": 7, "tables": 7, "patterns": 1, ...},
    "namespaces": {"rc": "https://richcanopy.org/ns/rc#", ...},
}
```

There is no top-level `graph_counts` field. Derive graph counts from
`named_graphs[].triple_count`.

`load_example_fixtures_tool(db, replace=True)` returns:

```python
{
    "replace": True,
    "fixtures": [
        {
            "path": "examples/manifest-prototype-rc/ais.trig",
            "imported": {"ontology": 94, "map": 223, ...},
        },
        ...
    ],
    "totals": {"ontology": 177, "observations": 26, "map": 574, "patterns": 14, ...},
    "total_imported": 800,
}
```

Use `total_imported` when you want the total fixture triple count. Per-graph
counts live under `totals`.

## Search

`db.search(...)` returns a `SearchResult` with:

```python
result.query
result.graph
result.matches
result.limit
result.offset
```

Each `SearchMatch` has:

```python
match.iri
match.graph
match.label
match.types
match.predicate
match.predicate_label
match.text
match.snippet
```

Use `match.iri` for the matched resource. There is no `match.subject` field.

## Assertion Support

`db.describe_assertion_support(subject, predicate, object=None, ...)` returns an
`AssertionSupportDescription`:

```python
support.graph
support.subject
support.owner_dataset
support.predicate
support.predicate_label
support.requested_object
support.assertion_present
support.matching_triples
support.same_subject_predicate_triples
support.target_resources
support.nearby_caveats
support.nearby_caveat_links
support.nearby_context_triples
support.related_observations
support.related_claims
support.related_patterns
support.related_evidence
support.related_revisions
support.related_routes
support.related_route_summaries
support.predicate_hints
support.context_note
support.support_scope_note
support.absence_note
support.suggested_next_actions
support.suggested_next_calls
```

Use this when the question is "why is this map assertion here?" or "what lore
hangs off this caveat/type/relationship assertion?" It is retrieval context, not
proof. `assertion_present=False` means the requested triple was not found in the
selected graph; the helper may still return context for the subject or requested
object. Literal object matching accepts common typed scalar equivalents, so
plain string inputs such as `"12"` and `"true"` can match stored integer and
boolean literals. Inspect `matching_triples[].object_datatype` to see what the
graph actually stores.

When `object` is supplied, `same_subject_predicate_triples` lists the current
triples for the same subject and predicate in the selected graph. This is
especially important when `assertion_present=False`: the exact requested value
may be absent because the map already records a different, more careful value.
`support_scope_note` explains which resources were searched for lore and which
nearby resources only contributed caveat context. For column subjects,
`owner_dataset` gives the owning dataset summary when the map has one; use the
owner-seeded suggested actions for broader dataset lore. The first suggested
context slice action is owner-seeded when the assertion subject is a column.
`absence_note` is present when an exact requested object is absent. It
distinguishes wrong-object cases, where the requested predicate is present with
different current values, from wrong-predicate cases, where the requested
predicate is absent on the subject in the selected graph. `nearby_context_triples`
contains selected direct layout/path facts such as `rc:layoutVerificationStatus`,
`rc:layoutVerificationNote`, and `rc:pathTemplate`; these can matter when an
assertion is present but not yet safe to use for executable planning.
When no current triples use the requested predicate on the subject,
`predicate_hints` lists nearby predicates already present on that subject,
ranked by local-name similarity and including full predicate IRIs,
`predicate_curie` display values when known, labels, descriptions, triple counts,
and sample values. Use it to recover from predicate-shape guesses such as asking
for `rc:hasPartitionScheme` when the map actually uses `rc:partitionedBy`.

`nearby_caveats` is the unique list of caveats near the assertion.
`nearby_caveat_links` explains why each caveat was included:

```python
link.caveat
link.scope
link.route_type
link.route_label
link.via_resource
link.matched_resource
```

Check `scope` before treating a caveat as column-specific. An
`owner_dataset` caveat came from the table that owns the column; it may still
matter, but it is not automatically a direct caveat on that column.

`suggested_next_actions` is the machine-readable form of the follow-up route:

```python
action.tool_name
action.mcp_tool_name
action.arguments
action.reason
action.call
```

Use `mcp_tool_name` and `arguments` when driving MCP calls. `tool_name` is the
local helper-style name, and `suggested_next_calls` contains equivalent display
strings for humans and older callers.

`related_route_summaries` groups and ranks `related_routes` by related resource.
Scan these first when the payload has many routes; use raw routes when you need
the exact link that pulled a resource in. Each summary has:

```python
summary.rank
summary.resource
summary.resource_kind
summary.route_count
summary.route_types
summary.route_labels
summary.matched_resources
summary.strongest_route_type
summary.strongest_route_label
summary.route_note
```

`related_routes` explains why related lore entered the payload. Each route has:

```python
route.resource
route.resource_kind
route.route_type
route.route_label
route.matched_resource
```

Use route summaries to find the most directly relevant resources, then use raw
routes to distinguish direct matches from indirect lore such as "claim target",
"pattern target", "pattern map implication", "observation observed column", or
"evidence linked from claim".

Each `requested_object` is an `AssertionValue`:

```python
value.value
value.value_label
value.value_kind
value.datatype
value.lang
value.resource
value.caveat
```

By default `object_kind="auto"` treats known CURIE/IRI-looking values as
resources and plain strings as literals. Use `object_kind="literal"` when you
need to match a literal that contains a colon.

## Staged Map Assertion Changes

`db.stage_map_assertion_change(subject, predicate, object, rationale, ...)`
returns a `StagedMapAssertionChangeRecord`:

```python
change.change_kind
change.graph
change.subject
change.predicate
change.object_value
change.object_kind
change.assertion_present_before
change.current_values_before
change.additions
change.removals
change.assertion_support
change.staged_revision
change.judgement_panel
change.review_note
change.review_recommendation
```

Use this response when reviewing a single map assertion add/remove/replace. The
`judgement_panel` is the compact reviewer view to check first:

```python
panel.headline
panel.recommendation
panel.assertion_present_before
panel.current_values
panel.proposed_value
panel.absence_note
panel.semantic_risk_level
panel.semantic_risk_reasons
panel.value_type_context
panel.why_current_value_may_be_intentional
panel.caveats
panel.strongest_routes
panel.impacts
panel.safety_notes
```

The panel does not decide whether the change is right. It packages the current
and proposed values, physical/value-type context, reasons the current value may
be intentional, caveat scopes, strongest related-lore routes, deterministic
impact spotlight entries, and safety notes that a reviewer should consider
before apply. `semantic_risk_level` is `none`, `attention`, or `high`; it is a
review cue, not a validation failure.

For physical type changes, `panel.value_type_context` lists current
`rc:valueType` resources and any `rc:requiredPhysicalType` they declare, with
booleans for whether that required type matches the current or proposed physical
type. `panel.strongest_routes[*].generic_value_only` is true when a route only
matched a generic shared value such as `rc:Varchar`; treat those as weak context
unless other routes tie the lore to the assertion subject or owner dataset.

The `assertion_support` field remains the full pre-change
`AssertionSupportDescription`. `additions` and `removals` are the generated
Turtle patch specs passed to staged revision machinery. `staged_revision` is the
normal `StagedGraphRevisionRecord` and can be inspected with
`describe_staged_revision`.

## Context Slices

`db.describe_context_slice(seed_iris, ...)` returns a `ContextSlice`:

```python
context.profile
context.seeds
context.reading_order
context.resources
context.resource_count
context.route_legend
context.route_counts
context.graph_counts
context.triples
context.triple_count
context.returned_triple_count
context.candidate_triple_count
context.omitted_triple_count
context.max_triples
context.truncated
context.truncation_scope
context.trig
context.dataset_contexts
context.pattern_contexts
context.warnings
```

`route_counts` is keyed by route id. `route_legend` explains those ids with
labels, meanings, priorities, and counts. `reading_order` is static guidance for
how to read the returned slice; it is not recomputed as a custom plan for each
query.

Each item in `context.resources` is a `ContextSliceResource`:

```python
resource.iri
resource.label
resource.description
resource.types
resource.graphs
resource.referenced_only
resource.primary_route
resource.routes
```

`referenced_only=True` means the resource is mentioned by returned context but
was not itself expanded into full resource detail in the slice. Do not treat that
as evidence the resource is missing from the capsule.

Each route has:

```python
route.route
route.route_label
route.source_iri
route.source_label
route.depth
```

## Dataset Description

`db.describe_dataset(table_iri)` returns a `DatasetDescription` with common
fields:

```python
dataset.iri
dataset.graph
dataset.label
dataset.description
dataset.types
dataset.row_semantics
dataset.entity_key
dataset.snapshot_timestamp
dataset.schema_stability
dataset.row_count_snapshot
dataset.layout_verification_status
dataset.layout_verification_note
dataset.profile_observations
dataset.columns
dataset.path_templates
dataset.physical_layouts
dataset.storage_accesses
dataset.partition_schemes
dataset.caveats
dataset.upstream_caveats
dataset.operational_warnings
dataset.relationships
dataset.linked_patterns
dataset.linked_pattern_reasons
```

`dataset.profile_observations` contains recent dataset-scoped
`ProfileObservationSummary` items for observations whose `observed_asset` is the
dataset and whose `observed_column` is absent:

```python
profile.iri
profile.summary
profile.observed_at
profile.observed_by
profile.observed_asset
profile.observed_column
profile.sample_size
profile.row_count
profile.null_count
profile.distinct_count
profile.value_frequencies
profile.profile_metrics
profile.evidence
```

`profile.evidence` items use the richer evidence description shape:

```python
evidence.iri
evidence.label
evidence.summary
evidence.sources
evidence.source_spans
```

`profile.value_frequencies` contains recent profiled values or value buckets
paired with their observed frequencies:

```python
value_frequency.iri
value_frequency.value
value_frequency.frequency
```

`profile.profile_metrics` contains scalar profiler outputs such as min, max,
mean, median, or project-specific metric kinds:

```python
profile_metric.iri
profile_metric.metric
profile_metric.value
profile_metric.value_datatype
profile_metric.value_lang
```

Treat `profile.profile_metrics` as an unordered list unless the response says
otherwise. Use `profile_metric.metric.iri` rather than list position when
reading specific values. Like observed value frequencies, profile metrics are
observed evidence rather than allowed-value domains, constraints, or durable map
semantics by themselves.

Each `dataset.columns[]` item can also include `profile_observations` for recent
profile observations whose `observed_column` is that column. Use these before
searching raw observation triples when you need profile counts, distinctness,
null counts, top observed values, or scalar metrics attached to a dataset
handoff.
Observed value frequencies are profile evidence, not allowed-value domains by
themselves. Look for linked claims and patterns before treating them as map
semantics.

Each column in `dataset.columns` is a `ColumnDescription`:

```python
column.iri
column.label
column.description
column.column_name
column.physical_type
column.value_type
column.nullable
column.profile_observations
```

`physical_type` and `value_type` are resource summaries with `iri`, `label`, and
`description`. There is no `column.semantic_role` field; use `column.value_type`
for the semantic value concept when present.

`db.describe_query_context(table_iri)` returns a `QueryPlanningContext`:

```python
query.dataset
query.readiness
query.issues
query.planning_notes
query.row_count_snapshot
query.columns
query.path_templates
query.physical_layouts
query.storage_accesses
query.partition_schemes
query.caveats
query.upstream_caveats
```

`readiness` is one of `ready_for_query_planning`, `needs_review`,
`insufficient_metadata`, or `blocked_by_contradiction`. Treat it as a planning
hint, not permission to execute a query. Missing or risky metadata warnings and
errors are returned in `query.issues`; there is no
`query.missing_or_risky_metadata` field. Each issue has:

```python
issue.code
issue.severity
issue.message
issue.resource
```

Use `describe_query_context` when the task is physical query planning and you
need the storage/layout/path/caveat projection without the full relationship and
pattern handoff in `describe_dataset`.

Each caveat in `dataset.caveats` has:

```python
caveat.iri
caveat.label
caveat.description
caveat.impact
caveat.severity
```

## Patterns

`db.record_pattern(...)` returns a `PatternRecord`:

```python
pattern.pattern_iri
pattern.evidence_iri
pattern.source_span_iri
pattern.pattern_triples
pattern.evidence_triples
```

`pattern.evidence_triples` is the number of new evidence triples written during
that call. It may be `0` when the pattern links to evidence that already exists,
for example profile evidence created by `record_dataset_profile` or
`record_column_profile`. Use `describe_pattern(pattern_iri)` when you need the
evidence surface available to readers.

`db.describe_pattern(pattern_iri)` returns a `PatternDescription`:

```python
description.iri
description.graph
description.label
description.summary
description.pattern_text
description.rationale
description.pattern_targets
description.supporting_observations
description.supporting_claims
description.evidence
description.confidence
description.confidence_label
description.observation_status
description.observation_status_label
description.pattern_stability
description.pattern_stability_label
description.map_implications
```

Use `pattern_targets`, not `targets`.

## Staged Revisions

`db.stage_systematisation(...)` returns a `SystematisationDraftRecord`:

```python
draft.summary
draft.intent
draft.anchors
draft.warnings
draft.framings
draft.staged_revisions
```

Each item in `draft.staged_revisions` is a `StagedGraphRevisionRecord` with:

```python
revision.revision_iri
revision.revision_type
revision.revision_stance
revision.graph
revision.triples
revision.changed_graphs
revision.patches
revision.validation_scope
revision.validation_conforms
revision.validation_result_count
revision.validation_results
```

`db.list_graph_revisions(...)` returns `GraphRevisionList`:

```python
revisions.revisions
revisions.count
revisions.limit
revisions.offset
revisions.revision_type
revisions.include_apply_checks
```

Each item in `revisions.revisions` has:

```python
item.iri
item.record_kind
item.summary
item.revision_type
item.revision_type_label
item.revision_stance
item.revision_stance_label
item.created_at
item.changed_graphs
item.validation_scope
item.validation_conforms
item.validation_result_count
item.has_patch_payload
item.patch_count
item.applied_by
item.applies_staged_revision
item.alternative_to
item.restaged_from
item.restaged_by
item.application_status
item.application_decision
item.application_can_apply
item.application_blocking_reasons
item.application_count_drifts
item.application_snapshot_drifts
item.suggested_next_actions
item.suggested_next_calls
```

`application_*` fields are only populated when `include_apply_checks=True` and
the revision has staged patch payloads, except applied revision events report
`application_status="applied_event"` for scanning. `record_kind` is a compact row
class such as `staged_patch`, `applied_event`, `export_record`, `import_record`,
or `history_record`. Use `has_patch_payload` and `patch_count` to decide whether
`describe_staged_revision` is available. Use `list_graph_revisions` to discover
reviewable or applied history before calling `describe_graph_revision` or
`describe_staged_revision` on a specific IRI.

`db.describe_staged_revision(revision_iri)` returns the fuller
`StagedGraphRevisionDescription`:

```python
description.iri
description.graph
description.label
description.summary
description.revision_type
description.revision_type_label
description.revision_stance
description.revision_stance_label
description.rationale
description.review_note
description.review_recommendation
description.alternative_to
description.restaged_from
description.changed_graphs
description.included_graphs
description.created_at
description.created_by
description.validation_scope
description.validation_conforms
description.validation_result_count
description.validation_results
description.graph_snapshots
description.patches
description.impacts
description.supporting_observations
description.supporting_claims
description.supporting_patterns
description.revision_anchors
description.evidence
description.judgement_panel
```

Use `revision_stance`, not `stance`.

Each `description.graph_snapshots[]` item has:

```python
snapshot.graph_role
snapshot.triple_count
snapshot.content_digest
```

`content_digest` is currently `sha256:<hex>` when present. It fingerprints the
graph role contents at the time the revision snapshot was recorded; use it with
`triple_count` when deciding whether two revision contexts are exactly the same,
not as semantic proof that a graph change is safe.

`description.alternative_to` means this staged revision competes with or refines
another revision. `description.restaged_from` means this staged revision replayed
an older stale proposal against current graph state; it is provenance for a
graph-state drift repair, not a competing framing.

`description.judgement_panel` is present for simple single-assertion `map`
staged changes that still replay cleanly against current graph state. It has
the same shape as `change.judgement_panel` from
`stage_map_assertion_change`. It is `None` for complex revisions, stale staged
patches, already-applied staged revisions, or changes that cannot be reduced to
one subject/predicate assertion.

Each patch in `description.patches` is a `GraphPatchDescription`:

```python
patch.iri
patch.operation
patch.operation_label
patch.target_graph
patch.format
patch.patch_role
patch.patch_role_label
patch.sequence_index
patch.triple_count
patch.before_triple_count
patch.after_triple_count
patch.content
```

Use `operation` and `triple_count`, not `patch_operation` or
`patch_triple_count`.

Each impact in `description.impacts` is a deterministic review-context record,
not a validation result:

```python
impact.impact_type
impact.severity
impact.changed_graph
impact.subject
impact.predicate
impact.predicate_label
impact.message
impact.removed_values
impact.added_values
impact.related_observations
impact.related_claims
impact.related_patterns
impact.related_evidence
impact.related_revisions
impact.related_context_note
```

Each value in `impact.removed_values` or `impact.added_values` has:

```python
value.value
value.value_label
value.value_kind
value.caveat
```

`value.caveat` is present when the changed value is a known caveat; it carries
the caveat description, impact, and severity summary inline.

Use impacts to notice consequences such as caveat removals, physical/value type
changes, nullability changes, row/grain signal changes, grouping changes,
layout/path changes, and documentation changes attached to the same subject as
another semantic impact.
Do not treat `impacts` as proof that a staged revision is wrong; they are a
review spotlight.

`db.check_staged_revision_apply(revision_iri)` returns a
`StagedRevisionApplyCheck`:

```python
check.staged_revision_iri
check.can_apply
check.status
check.decision
check.summary
check.review_recommended
check.semantic_risk_level
check.semantic_risk_reasons
check.blocking_reasons
check.recommended_resolution
check.already_applied_by
check.changed_graphs
check.patch_checks
check.count_drifts
check.snapshot_drifts
check.conflicts
check.validation_scope
check.validation_conforms
check.validation_skipped_reason
check.validation_result_count
check.validation_results
check.patches_checked
check.triples_to_add
check.triples_to_remove
check.suggested_next_actions
check.suggested_next_calls
```

Read `status`, `summary`, and `semantic_risk_level` first. Current statuses are
`ready`, `already_applied`, `conflict`, `validation_failed`, and `not_ready`.
`decision` is the stable branch hint, for example `review_then_apply`,
`inspect_applied_revision`, `restage_against_current_graph`, or
`inspect_validation_results`. `review_recommended=True` means the patch replays
and validates, but the caller should still review the staged revision before
applying. `blocking_reasons` uses compact values such as `target_count_drift`,
`target_digest_drift`, `validation_failed`, or `already_applied`. When
`validation_conforms is None`, read `validation_skipped_reason` before guessing
why validation did not run; common values are `conflicts_present` and
`already_applied`.
`count_drifts` gives patch-level count drift context: target graph, expected
before count, current count, delta, and whether exact changed triples are
available. It also reports `patch_operation`, `patch_triples_checked`,
`patch_triples_currently_present`, `patch_triples_currently_absent`, and
`patch_triple_status` (`all_patch_triples_absent`,
`all_patch_triples_present`, or `mixed_patch_triples_present`). In the current
runtime, DoxaBase can inspect the staged patch triples themselves, but exact
unrelated changed triples still require future graph version storage.
`snapshot_drifts` reports graph-level digest mismatches: graph role, snapshot
triple count, current triple count, staged snapshot digest, current graph digest,
and whether exact changed triples are available. A digest mismatch means the
target graph state is not identical to the state at staging time, even when
triple counts still match.
`suggested_next_actions` uses the same structured action shape as assertion
support: tool name, MCP tool name, arguments, reason, and display call string.
For staged apply checks, actions are ordered review-first; mutating actions such
as `apply_staged_revision` and `restage_staged_revision` come after inspection
or export suggestions.
`can_apply=True` means the patch replays and validates mechanically; it is not
semantic approval. If `semantic_risk_level` is `attention` or `high`, inspect the
judgement panel, impacts, and supporting lore before applying.

`export_staged_revision()` and `export_staged_revisions()` embed this live apply
check into the Markdown artifact at export time. Treat the `Current Apply Check`
section as the review bundle's current-status header: it may say a staged
revision is stale or already applied even when the original staged description
still records the validation result from the time it was created.
In grouped exports, `Staged validation` is the staged description's original
preview result, while `Current validation` is derived from the live apply check
and can be `skipped: conflicts_present`. Both cells include a result count when
available, for example `True (0 result(s))`.

When `validation_conforms` is false, read `validation_results` before inferring
the problem from patch text. Validation results usually include focus node,
result path, constraint, severity, value, and messages.
