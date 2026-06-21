# Response Shape Examples

Use this doc when scripting against the Python API or MCP helper payloads. The
workflow docs explain what to do; this page names the fields agents commonly
need so they do not have to infer near-miss attribute names.

Python API calls return dataclass-like objects. Use `to_dict()` for one returned
object and `to_jsonable()` for lists or nested structures when a scratch script
needs a serializable payload:

```python
from doxabase import to_dict, to_jsonable

pattern_payload = to_dict(db.describe_pattern(pattern_iri))
tables_payload = to_jsonable(db.list_entities(type="rc:Table").entities)
```

MCP helper functions in `doxabase.mcp_tools` already return JSON-like
dictionaries. Prefer MCP helpers when you need serializable payloads; prefer the
Python API when you are running a local scratch capsule script.

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

`db.replace_graph_triples(...)` returns `GraphTripleReplacementRecord`:

```python
replacement.graph
replacement.format
replacement.before_count
replacement.after_count
replacement.count_delta
replacement.before_digest
replacement.after_digest
replacement.digest_changed
replacement.removal_triples
replacement.addition_triples
replacement.triples_removed
replacement.triples_added
replacement.same_count
replacement.expected_count
replacement.allow_count_change
```

MCP `replace_graph_triples_tool(...)` returns the same fields as a dictionary.
`removal_triples` and `addition_triples` count unique triples parsed from the
caller payloads; `triples_removed` and `triples_added` count the effective graph
mutation after accounting for current graph state. With the default
`allow_count_change=False`, count-changing replacements raise before mutating.

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
Search text can come from a literal object or a URI-valued graph term. URI
matches are useful for exact project vocabulary tokens such as custom profile
metric kinds; add labels or descriptions in the ontology when agents need
natural-language discovery.

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

For `replace`, if `panel.assertion_present_before` is true and
`panel.current_values` includes other values, the meaningful mutation is removal
of those other values. Check `panel.safety_notes`,
`panel.semantic_risk_reasons`, and the related support routes before applying.

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
query. Route counts are route occurrences, not unique resource counts; a
resource reached through two useful routes contributes to both route counts.
Dataset/deep-lore slices can include routes such as
`dataset_profile_observation`, `column_profile_observation`,
`unmapped_column_profile_observation`, `observed_profile_metric`,
`observed_value_frequency`, `profile_metric_kind`, and
`profile_metric_target`. These routes are bounded by the same returned profile
observations used by `describe_dataset()`. A metric-kind IRI that has no subject
triples can still appear with `referenced_only=True` when it was reached through
`rc:profileMetricKind`. Broad metric-kind seeds are capped; read `warnings` for
omitted observed profile metric counts and use narrower seeds when needed.
Profile and metric seeds may include bounded same-dataset profile context
beyond the exact seed while avoiding unrelated dataset leakage.

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

## Profile Helper Records

`db.record_dataset_profile(...)` returns a `DatasetProfileRecord`:

```python
profile.dataset_iri
profile.observation
profile.map_dataset
profile.pattern
```

`db.record_column_profile(...)` returns a `ColumnProfileRecord`:

```python
profile.column_iri
profile.table_iri
profile.observation
profile.map_column
profile.pattern
```

`profile.map_dataset`, `profile.map_column`, and `profile.pattern` may be
`None` when the caller kept the profile observation-only or did not request a
linked synthesis.

`db.record_profile_bundle(...)` returns a `ProfileBundleRecord`:

```python
bundle.dataset_iri
bundle.shared_evidence_iri
bundle.dataset_profile
bundle.column_profiles
```

`bundle.dataset_profile` has the same shape as `DatasetProfileRecord`, and each
`bundle.column_profiles[]` item has the same shape as `ColumnProfileRecord`.
The bundle helper does not create a separate RDF bundle node; it is an API
convenience over the normal profile records. `shared_evidence_iri`, when
supplied, makes the returned profile observations point at the same evidence
IRI unless a column item overrides it with its own `evidence_iri`.

Copyable bundle shape:

```python
bundle = db.record_profile_bundle(
    "https://example.test/project#orders",
    dataset_summary="Orders were profiled in one full-table pass.",
    evidence_summary="DuckDB profile query over the local Orders table.",
    evidence_sources=["scratch://orders-profile.sql"],
    sample_size=1000,
    sample_scope="All rows in the local Orders table.",
    sample_method="DuckDB aggregate profile query.",
    row_count=1000,
    map_label="Orders",
    is_table=True,
    shared_evidence_iri="https://example.test/project#OrdersProfileRunEvidence",
    column_defaults={"update_map_column": False},
    column_profiles=[
        {
            "column_iri": "https://example.test/project#orders__status",
            "column_name": "status",
            "summary": "Sampled status values were observed.",
            "distinct_count": 3,
            "value_frequencies": [
                {"value": "fulfilled", "frequency": 700},
                {"value": "pending", "frequency": 200},
            ],
        },
        {
            "column_iri": "https://example.test/project#orders__amount",
            "column_name": "amount",
            "summary": "Amount was profiled as a non-null decimal.",
            "null_count": 0,
            "physical_type": "rc:Decimal",
            "nullable": False,
            "update_map_column": True,
        },
    ],
)
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
dataset.profile_summary
dataset.profile_observations
dataset.unmapped_column_profile_observations
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

`dataset.profile_summary` is a quick count of the profile lore returned in this
bounded `describe_dataset` response:

```python
profile_summary.returned_dataset_profile_count
profile_summary.returned_mapped_column_profile_count
profile_summary.returned_unmapped_column_profile_count
profile_summary.returned_profile_count
profile_summary.mapped_profiled_column_count
profile_summary.evidence_iris
profile_summary.evidence_profile_counts
profile_summary.shared_evidence_iris
profile_summary.profile_run_candidates
profile_summary.handoff_note
```

These are response counts, not a promise that the capsule has no older profile
observations beyond the returned limit. `evidence_iris` lists unique evidence
IRIs linked from returned profile observations. `evidence_profile_counts` counts
how many returned profile observations link to each evidence IRI.
`shared_evidence_iris` lists evidence IRIs that are linked from every returned
profile observation in the bounded response; it can be empty when older or
unrelated returned profiles are mixed with a newer shared-evidence bundle. In
that mixed-history case, use `evidence_profile_counts` to spot evidence IRIs
that support several profiles from the same run. `profile_run_candidates`
contains the count-ranked evidence IRIs that support more than one returned
profile; each candidate has `evidence_iri`, `returned_profile_count`, and
`shared_by_all_returned_profiles`. It is a bounded response convenience, not a
separate persisted profile-run node. `handoff_note` is a compact reading cue for
profile-only handoffs: profile lore is observed evidence, while
storage/path/layout warnings remain physical query-planning metadata gaps.

Partition schemes under `dataset.partition_schemes[]` include both a compatibility
shortcut and the full list:

```python
partition.iri
partition.label
partition.description
partition.partition_column      # first returned column, compatibility shortcut
partition.partition_columns     # full list of ResourceSummary objects
partition.granularity
partition.path_template
partition.redundant_partition_key
partition.layout_verification_status
partition.layout_verification_note
```

Treat `partition.partition_columns` as an unordered set of resources unless a
future response explicitly carries an ordering field. The singular
`partition.partition_column` is useful for old single-column callers, not for
inferring authoring order.

Relationship entries under `dataset.relationships[]` include RDF class context
and helper-style tokens:

```python
relationship.iri
relationship.label
relationship.description
relationship.types
relationship.relationship_kind        # RDF class IRI, such as rc:ForeignKey
relationship.relationship_kind_label
relationship.relationship_type        # helper token, such as "foreign_key"
relationship.source_dataset
relationship.target_dataset
relationship.foreign_key_from
relationship.foreign_key_to
relationship.referential_integrity
relationship.declared
relationship.identifying_columns
relationship.source_columns
relationship.derived_columns
relationship.derivation_function
relationship.derivation_properties
relationship.group_by_columns
relationship.aggregated_columns
relationship.source_caveats
```

For foreign keys, use `foreign_key_from` and `foreign_key_to`; there are no
generic `from_column` or `to_column` response fields. For derivations, use
`source_columns` and `derived_columns`. For aggregations, use `group_by_columns`
and `aggregated_columns`.

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
profile.observed_column_name
profile.sample_size
profile.sample_scope
profile.sample_method
profile.row_count
profile.null_count
profile.distinct_count
profile.value_frequencies
profile.profile_metrics
profile.evidence
```

`profile.sample_scope` describes what population, file set, query result, or
slice the profile covered. `profile.sample_method` describes how the profile was
produced. Both fields are short strings; use the linked evidence for source
identity and detailed provenance.

`dataset.unmapped_column_profile_observations` contains recent column profile
observations whose `observed_asset` is the dataset but whose `observed_column`
is not one of the dataset's current map columns. Use it when a sampled or
scratch column profile was recorded with `update_map_column=false`. These
profiles are observation lore, not map column assertions. When the helper was
given a column name, `profile.observed_column_name` preserves that observed name
and `profile.observed_column.column_name` uses it as a fallback if the column is
not mapped.

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
profile_metric.target
profile_metric.value
profile_metric.value_datatype
profile_metric.value_lang
```

Treat `profile.profile_metrics` as an unordered list unless the response says
otherwise. Use `profile_metric.metric.iri` rather than list position when
reading specific values. `profile_metric.target` may be `None`; that means the
metric applies to the profile observation or observed asset as a whole. When
present, it is the narrower resource the scalar is specifically about. Like
observed value frequencies, profile metrics are observed evidence rather than
allowed-value domains, constraints, or durable map semantics by themselves.

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
query.readiness_note
query.issues
query.analysis_warnings
query.planning_notes
query.row_count_snapshot
query.layout_verification_status
query.layout_verification_note
query.columns
query.path_templates
query.query_target_candidates
query.physical_layouts
query.storage_accesses
query.partition_schemes
query.caveats
query.upstream_caveats
```

`readiness` is one of `ready_for_query_planning`, `needs_review`,
`insufficient_metadata`, or `blocked_by_contradiction`. It is about physical
query-planning metadata, not analytical safety. `readiness_note` says that
explicitly and points to analysis caveats when present.

Missing, risky, or informational physical metadata notes are returned in
`query.issues`; there is no `query.missing_or_risky_metadata` field. An issue
with `severity="error"` can mean "not enough physical metadata to plan a
query"; it does not necessarily mean profile observations, map lore, or
validation are broken. An issue with `severity="info"` does not change
`readiness`; for example, `verification_status_not_recorded` means path/layout
metadata exists but no explicit verification status has been recorded.

`query.analysis_warnings` returns caveat-shaped interpretation warnings that
matter after a query can be planned, such as deduplication, mixed payload
coercion, or JSON parsing caveats. These warnings do not change `readiness`.

`query.query_target_candidates` contains derived path/template planning cards
for callers that need a safer handoff than raw `path_templates` plus
`storage_accesses`. Each card preserves the template provenance
(`dataset`, `partition_scheme`, or `storage_access`), the relevant storage
access metadata, a best-effort `candidate_path`, a `composition` value such as
`template_as_returned`, `storage_root_joined`, `bucket_prefix_joined`,
`key_prefix_joined`, or `unresolved`, and `review_reasons` copied from physical
query-planning issues that apply to the candidate. These cards do not resolve
credentials, endpoint profiles, or executable SQL. `review_reasons` may include
info-only notes; use `review_required` to tell whether any warning or error
requires review before executable use.
If the overall query context is blocked by other dataset metadata, a candidate
may include `query_context_has_other_blockers` even when its own storage access
looks clean. Protocol/location warnings such as
`s3_access_resolution_unrecorded` and `storage_protocol_location_mismatch` mean
the candidate path is only an orientation aid until storage access is clarified.
Partition-specific blockers are candidate-local only for the partition that
owns them; sibling partition candidates should carry
`query_context_has_other_blockers` instead of the sibling's direct
contradiction.

Each query target candidate has:

```python
candidate.template
candidate.template_source
candidate.source_resource
candidate.storage_access
candidate.storage_protocol
candidate.storage_root
candidate.endpoint_profile
candidate.bucket_name
candidate.key_prefix
candidate.candidate_path
candidate.composition
candidate.candidate_path_status
candidate.requires_endpoint_profile
candidate.credential_reference
candidate.path_style_access
candidate.review_required
candidate.review_reasons
```

`candidate_path_status` is `ready` when the path is suitable as a planning
input after normal review, `orientation_only` when warnings/errors make it a
handoff clue rather than executable guidance, and `unresolved` when the graph
lacks enough storage-location metadata for an executable path.

Each issue or analysis warning has:

```python
issue.code
issue.domain
issue.severity
issue.message
issue.resource
```

`domain` is `query_planning` for physical metadata readiness issues and
`analysis` for caveat-shaped interpretation warnings. Read it before reacting
to `severity`: an `error` in `query_planning` means executable query-planning
metadata is missing or contradicted, not that profile lore or graph validation
failed.

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

`description.supporting_claims` contains `ClaimDescription` items:

```python
claim.iri
claim.label
claim.claim_text
claim.claim_kind
claim.claim_kind_label
claim.claim_targets
claim.confidence
claim.confidence_label
claim.observation_status
claim.observation_status_label
claim.proposed_assertions
claim.lifecycle_summary
claim.outgoing_reconsiderations
claim.incoming_reconsiderations
```

`claim.claim_kind` is a string IRI, not a `ResourceSummary` object. Use
`claim.claim_kind_label` when you want display text and `claim.claim_targets`
when you need the resource summaries the claim is about.

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
revisions.drift_detail
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
item.current_alternative_to
item.restaged_from
item.restaged_by
item.current_restaged_by
item.stale_resolution_state
item.application_status
item.application_decision
item.application_can_apply
item.application_summary
item.application_recommended_resolution
item.application_validation_skipped_reason
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
or `history_record`.

First-read triage fields:

```python
item.record_kind
item.has_patch_payload
item.patch_count
item.changed_graphs
item.application_status
item.application_decision
item.application_can_apply
item.application_summary
item.application_recommended_resolution
item.application_validation_skipped_reason
item.application_blocking_reasons
item.stale_resolution_state
item.suggested_next_calls
```

Use those to decide whether the row is ready to review, already applied, blocked
by graph drift, or better handled by an export or detail call. Then inspect
detail fields such as `application_count_drifts`,
`application_snapshot_drifts`, `suggested_next_actions`, validation fields, and
relation links when you need exact drift triples, machine-readable action
records, or revision provenance. Use `has_patch_payload` and `patch_count` to
decide whether `describe_staged_revision` is available. Use
`list_graph_revisions` to discover reviewable or applied history before calling
`describe_graph_revision` or `describe_staged_revision` on a specific IRI.
`drift_detail="summary"` is the default and omits exact changed-triple arrays
from list-row snapshot drift entries. Summary rows still include
`drift_relevance`, all overlap arrays, and added/removed exact-change counts
when exact drift is available. Use `drift_detail="exact"` or
`check_staged_revision_apply()` when the actual changed-triple arrays should be
included.

`db.describe_graph_revision(revision_iri)` returns `GraphRevisionDescription`:

```python
description.iri
description.graph
description.label
description.summary
description.revision_type
description.revision_type_label
description.rationale
description.changed_graphs
description.included_graphs
description.created_at
description.created_by
description.export_path
description.applies_staged_revision
description.applied_source
description.validation_scope
description.validation_conforms
description.validation_result_count
description.validation_results
description.graph_snapshots
description.supporting_observations
description.supporting_claims
description.supporting_patterns
description.revision_anchors
description.evidence
```

For applied staged revision events, `applied_source` is a compact source card
with staged summary, stance, review note/recommendation, restage links, staged
validation headline, graph snapshots, patch counts, patch metadata without
content, and support-link counts. It is meant for quick history scanning; call
`describe_staged_revision(description.applies_staged_revision)` for patch
content, full diagnostics, impacts, or judgement panels.

`applied_source` has:

```python
applied_source.iri
applied_source.summary
applied_source.revision_type
applied_source.revision_type_label
applied_source.revision_stance
applied_source.revision_stance_label
applied_source.review_note
applied_source.review_recommendation
applied_source.alternative_to
applied_source.restaged_from
applied_source.restaged_by
applied_source.current_restaged_by
applied_source.restage_reason
applied_source.created_at
applied_source.created_by
applied_source.validation_scope
applied_source.validation_conforms
applied_source.validation_result_count
applied_source.changed_graphs
applied_source.included_graphs
applied_source.graph_snapshots
applied_source.patch_count
applied_source.patches
applied_source.supporting_observation_count
applied_source.supporting_claim_count
applied_source.supporting_pattern_count
applied_source.evidence_count
applied_source.revision_anchor_count
```

Each `applied_source.patches[]` item has:

```python
patch.operation
patch.operation_label
patch.target_graph
patch.patch_role
patch.patch_role_label
patch.sequence_index
patch.triple_count
patch.before_triple_count
patch.after_triple_count
```

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
description.restaged_by
description.current_restaged_by
description.applied_by
description.application_status
description.restage_reason
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
graph-state drift repair, not a competing framing. `description.restaged_by`
points to a refreshed successor when the described revision is the stale source
for a later restage. `description.applied_by` points to the applied revision
event when this staged revision has already been applied; in that case
`description.application_status` is `already_applied`. `description.restage_reason`
is a compact human-readable summary of why the restage happened when that can be
derived from the recorded rationale.

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
`inspect_applied_revision`, `restage_against_current_graph`,
`inspect_patch_conflict`, or `inspect_validation_results`.
`review_recommended=True` means the caller should
review the staged revision before the next mutation. For `ready` checks that
means review before applying; for count/digest-drift `conflict` checks it means
review before restaging; for `patch_conflict` checks it means inspect/export
before staging a repaired or alternative candidate. `blocking_reasons` uses compact
values such as `target_count_drift`,
`target_digest_drift`, `patch_conflict`, `validation_failed`, or
`already_applied`. When
`validation_conforms is None`, read `validation_skipped_reason` before guessing
why validation did not run; common values are `conflicts_present` and
`already_applied`.
For `patch_conflict`, inspect `patch_checks[].conflict` before mutating; it
means the stored patch cannot currently be replayed, not merely that the target
graph count or digest drifted. Suggested actions for `patch_conflict` omit
`restage_staged_revision`.
`count_drifts` gives patch-level count drift context: target graph, expected
before count, current count, delta, and whether exact changed triples are
available. It also reports `patch_operation`, `patch_triples_checked`,
`patch_triples_currently_present`, `patch_triples_currently_absent`, and
`patch_triple_status` (`all_patch_triples_absent`,
`all_patch_triples_present`, or `mixed_patch_triples_present`). In the current
runtime, DoxaBase can inspect the staged patch triples themselves; when stored
snapshot rows exist, exact target graph additions and removals are available in
`snapshot_drifts`.
`snapshot_drifts` reports graph-level digest mismatches: graph role, snapshot
triple count, current triple count, staged snapshot digest, current graph digest,
whether exact changed triples are available, whether they are included in this
response,
`triples_added_since_snapshot_count`,
`triples_removed_since_snapshot_count`,
`drift_relevance`, `patch_overlap_subjects`, `patch_overlap_predicates`,
`patch_overlap_objects`, `revision_anchor_overlap`,
`triples_added_since_snapshot`, and `triples_removed_since_snapshot`.
`drift_relevance` is a conservative hint, not an auto-merge decision. Current
values include `no_patch_subject_overlap`, `patch_subject_overlap`,
`patch_subject_and_predicate_overlap`, `patch_object_overlap`,
`patch_object_and_anchor_overlap`, `revision_anchor_overlap`,
`unknown_no_exact_diff`, and `unknown_no_patch_terms`. Predicate and object
overlap can be broad, for example `rdf:type` or `rc:Dataset`, so read them as
review hints. Anchor overlap means drift touched one of the staged revision's
review anchors even if the staged patch subjects were untouched. A digest
mismatch means the target graph state is not identical to the state at staging
time, even when triple counts still match. Older revisions can report
`exact_changed_triples_available=False` when they predate snapshot row storage.
Revision-list summary mode may report `exact_changed_triples_available=True`
and `exact_changed_triples_included=False`; that means exact triples exist but
were intentionally omitted from the list response. The added/removed count
fields still report how many exact triples were omitted when those counts are
known.
Each changed-triple item carries exact raw RDF fields (`subject`, `subject_kind`,
`predicate`, `object`, `object_kind`, `datatype`, `lang`) plus scan-friendly
fields (`subject_curie`, `subject_display`, `predicate_curie`,
`predicate_display`, `object_curie`, `object_display`). Use the raw fields for
precise graph work and the display fields for human review.
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
When the live apply check reports semantic risk, the export can include a
`Semantic Review Warning` before `Current Apply Check` even if the compact
judgement panel is unavailable for a stale proposal.
Restaged single exports also include a top metadata `Restage headline` before
the current apply check. Grouped exports include `Restage Context` near the top
when one or more revisions were refreshed from stale proposals. They include
`Alternative Context` when a stored alternative target has been restaged and the
current comparison target is a refreshed successor.
Stale original exports include a top metadata `Restaged by` line when a
refreshed successor already exists.
In grouped exports, `Staged validation` is the staged description's original
preview result, while `Current validation` is derived from the live apply check
and can be `skipped: conflicts_present`. Both cells include a result count when
available, for example `True (0 result(s))`.

`db.export_staged_revisions(...)` returns `StagedGraphRevisionsExportRecord`:

```python
export.path
export.format
export.revision_iris
export.bytes_written
export.revision_summaries
export.bundle_summary
```

Each item in `revision_summaries` is a
`StagedGraphRevisionExportSummary`:

```python
item.revision_iri
item.summary
item.revision_stance
item.revision_stance_label
item.alternative_to
item.current_alternative_to
item.changed_graphs
item.apply_status
item.apply_decision
item.apply_can_apply
item.apply_summary
item.apply_blocking_reasons
item.apply_validation_conforms
item.apply_validation_skipped_reason
item.apply_validation_result_count
item.apply_check_error
item.current_validation
item.staged_validation
item.staged_validation_conforms
item.staged_validation_result_count
item.validation_diagnostic_headline
item.review_recommendation
item.restaged_from
item.restaged_by
item.current_restaged_by
item.stale_resolution_state
item.suggested_next_actions
item.suggested_next_calls
```

Use these rows when a script needs the same grouped current-status information
shown in the Markdown summary table without making separate apply-check calls.
`alternative_to`, `current_alternative_to`, `restaged_from`, `restaged_by`,
`current_restaged_by`, and `stale_resolution_state` let recovery scripts keep
alternative groups and stale/restaged chains together without a second revision
list lookup.
`alternative_to` preserves the stored provenance target; `current_alternative_to`
follows restage successors when the alternative target has been refreshed. When a
stale source already has `restaged_by`, `current_restaged_by` follows the
restage chain to the latest known successor, and suggested next actions point at
that current successor instead of recommending another restage.

`export.bundle_summary` is a `StagedGraphRevisionBundleSummary`:

```python
bundle.total_revisions
bundle.apply_status_counts
bundle.stale_resolution_state_counts
bundle.unresolved_stale_revision_iris
bundle.stale_handled_by_restage_revision_iris
bundle.ready_restage_successor_revision_iris
bundle.validation_failed_revision_iris
bundle.recommended_review_iris
bundle.recommended_mutation_review_iris
bundle.recommended_applied_inspection_iris
```

Use `stale_resolution_state == "stale_unresolved"` to find stale proposals that
still need restaging. `stale_handled_by_restage` means the source is stale but
already points to a refreshed successor. `restaged_successor_ready` marks a
ready refreshed proposal. The bundle's `recommended_review_iris` de-duplicates
the current review set in bundle order, replacing handled stale sources with
their successors. `validation_failed_revision_iris` lists rows whose patch counts
replay but whose preview validation does not conform. Use
`recommended_mutation_review_iris` when you only want staged revisions that may
still need restage, repair, or apply decisions. Use
`recommended_applied_inspection_iris` for already-applied staged revisions that
are useful to inspect but should not be applied again.

`db.restage_staged_revisions(...)` returns
`StagedGraphRevisionBatchRestageRecord`:

```python
batch.requested_revision_iris
batch.processed_revision_iris
batch.dry_run
batch.would_restage_revision_iris
batch.restaged_revision_iris
batch.skipped_revision_iris
batch.already_handled_revision_iris
batch.not_restageable_revision_iris
batch.not_restageable_revision_iris_by_reason
batch.restaged_revision_by_source
batch.current_revision_by_source
batch.review_revision_iris
batch.items
batch.revision_summaries
batch.bundle_summary
batch.export_record
```

Each `batch.items` row reports `source_revision_iri`, `summary`,
`status_before`, `decision_before`, `stale_resolution_state_before`,
`blocking_reasons_before`, `action`, `not_restageable_reason`,
`restaged_revision_iri`,
`restaged_from`, `current_restaged_by`, `current_revision_iri`, and `note`.
`restaged_from` is present when the source item is itself a refreshed successor
of an older stale proposal. Current actions are
`restaged`, `would_restage`, `skipped_already_handled`, and
`skipped_not_restageable`. `would_restage` only appears when `dry_run=True`; in
that case no successor is created, `restaged_revision_iris` stays empty, and
`would_restage_revision_iris` lists the stale source revisions that a real run
would refresh. For those would-restage rows, `current_revision_by_source` still
points at the stale source because no current successor exists yet.
`skipped_not_restageable` includes ready, validation-failed, already-applied,
and `patch_conflict` rows; read `status_before`, `decision_before`, and
`blocking_reasons_before` before deciding whether the row needs apply, repair,
or inspection. `not_restageable_reason` gives the compact reason for those rows,
and `not_restageable_revision_iris_by_reason` groups skipped source IRIs by the
same value, for example `ready`, `already_applied`, `validation_failed`, or
`patch_conflict`. If `path` was passed, `export_record` is the
grouped Markdown export for `review_revision_iris`; otherwise it is `None` and
the summary fields are computed in memory. In dry-run mode, `path` still writes
the requested review export even though no refreshed successor is created.

When `validation_conforms` is false, read `validation_results` before inferring
the problem from patch text. Validation results usually include focus node,
result path, constraint, severity, value, and messages.
