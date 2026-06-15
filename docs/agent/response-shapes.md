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
    "predicate_counts": [{"predicate": "rdf:type", "count": 569}, ...],
    "key_counts": {"datasets": 7, "tables": 7, "patterns": 0, ...},
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
            "imported": {"ontology": 70, "map": 243, ...},
        },
        ...
    ],
    "totals": {"ontology": 177, "observations": 10, "map": 574, ...},
    "total_imported": 767,
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
support.predicate
support.predicate_label
support.requested_object
support.assertion_present
support.matching_triples
support.target_resources
support.nearby_caveats
support.related_observations
support.related_claims
support.related_patterns
support.related_evidence
support.related_revisions
support.context_note
support.suggested_next_calls
```

Use this when the question is "why is this map assertion here?" or "what lore
hangs off this caveat/type/relationship assertion?" It is retrieval context, not
proof. `assertion_present=False` means the exact requested triple was not found
in the selected graph; the helper may still return context for the subject or
requested object.

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
dataset.columns
dataset.path_templates
dataset.physical_layouts
dataset.storage_accesses
dataset.partition_schemes
dataset.caveats
dataset.upstream_caveats
dataset.relationships
dataset.linked_patterns
dataset.linked_pattern_reasons
```

Each column in `dataset.columns` is a `ColumnDescription`:

```python
column.iri
column.label
column.description
column.column_name
column.physical_type
column.value_type
column.nullable
```

`physical_type` and `value_type` are resource summaries with `iri`, `label`, and
`description`. There is no `column.semantic_role` field; use `column.value_type`
for the semantic value concept when present.

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
```

Use `revision_stance`, not `stance`.

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
check.already_applied_by
check.changed_graphs
check.patch_checks
check.conflicts
check.validation_scope
check.validation_conforms
check.validation_result_count
check.validation_results
check.patches_checked
check.triples_to_add
check.triples_to_remove
```

When `validation_conforms` is false, read `validation_results` before inferring
the problem from patch text. Validation results usually include focus node,
result path, constraint, severity, value, and messages.
