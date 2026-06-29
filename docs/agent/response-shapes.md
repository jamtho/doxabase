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
        {
            "id": "start_here",
            "title": "Start Here",
            "description": "...",
            "size_chars": 8123,
            "sections": [
                {
                    "heading": "First Ten Minutes",
                    "level": 2,
                    "anchor": "first-ten-minutes",
                    "line": 21,
                    "start_char": 912,
                    "end_char": 3350,
                },
                ...
            ],
        },
        ...
    ]
}
```

`get_doc_tool(doc_id, section="...", max_chars=...)` returns one bounded slice:

```python
{
    "id": "response_shapes",
    "content": "## Profile Helper Records\n...",
    "truncated": True,
    "start_char": 18342,
    "end_char": 30342,
    "total_chars": 111000,
    "max_chars": 12000,
    "selected_section": {"anchor": "profile-helper-records", ...},
    "sections": [...],
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
The Python `db.graph_overview()` object has the same `named_graphs` cards, but
its `class_counts` and `predicate_counts` are tuple pairs; the MCP helper
serializes those pairs as dictionaries with `class`/`predicate` and `count`.

`project_brief_tool(db, limit=20, profile_candidate_limit=2)` returns:

```python
{
    "key_counts": {"datasets": 7, "tables": 7, ...},
    "dataset_count": 7,
    "returned_dataset_count": 7,
    "dataset_query_readiness_counts": {
        "ready_for_query_planning": 3,
        "needs_storage_access": 4,
    },
    "returned_dataset_query_readiness_counts": {
        "ready_for_query_planning": 2,
        "needs_storage_access": 1,
    },
    "profile_queue_counts": {
        "profile_observations": 4,
        "profile_evidence": 2,
        "profile_run_candidates": 1,
        "profile_drafts": 2,
        "profile_draft_recommendations": 3,
        "profile_scalar_conflict_groups": 0,
        "profile_metric_advisories": 1,
        "profile_type_advisories": 0,
    },
    "queue_counts": {
        "staged_frontier_review": 1,
        "query_repair_review": 2,
        "profile_review": 1,
        "staged_review": 1,
    },
    "returned_queue_counts": {
        "staged_frontier_review": 1,
        "query_repair_review": 1,
        "profile_review": 1,
        "staged_review": 1,
    },
    "omitted_queue_counts": {"query_repair_review": 1},
    "active_queue_type_count": 4,
    "returned_queue_type_count": 4,
    "limit_crowded_queue_types": [],
    "health_tasks": [
        {
            "priority": 10,
            "task_type": "expand_project_brief",
            "source": "project_brief",
            "reason": "...",
            "suggested_next_action": {...},
            "suggested_next_call": "project_brief(...)",
            "queue_types": ["query_repair_review"],
            "omitted_queue_counts": {"query_repair_review": 1},
            "suggested_limit": 21,
            "sensitive_literal_count": null,
            "missing_seed_terms": [],
        },
        {
            "priority": 20,
            "task_type": "privacy_export_review",
            "source": "scan_sensitive_literals",
            "reason": "...",
            "suggested_next_action": {...},
            "suggested_next_call": "scan_sensitive_literals(...)",
            "queue_types": [],
            "omitted_queue_counts": {},
            "suggested_limit": null,
            "sensitive_literal_count": 1,
            "missing_seed_terms": [],
        },
    ],
    "datasets": [
        {
            "dataset": {"iri": "https://...", "label": "...", "description": ...},
            "is_table": true,
            "query": {
                "readiness": "ready_for_query_planning",
                "readiness_note": "...",
                "issue_codes": [],
                "repair_action_group_count": 0,
                "candidate_count": 1,
                "ready_candidate_indexes": [0],
                "direct_clean_candidate_indexes": [0],
                "suggested_next_actions": [...],
                "suggested_next_calls": [...],
            },
            "profile": {
                "total_profile_count": 4,
                "returned_profile_count": 4,
                "omitted_profile_count": 0,
                "profile_evidence_count": 1,
                "profile_evidence_iris": ["https://..."],
                "profile_run_candidate_count": 1,
                "profile_run_evidence_iris": ["https://..."],
                "draft_count": 1,
                "draft_evidence_iris": ["https://..."],
                "drafts": [
                    {
                        "evidence_iri": "https://...",
                        "profile_observation_count": 4,
                        "recommendation_count": 2,
                        "scalar_conflict_group_count": 0,
                        "metric_advisory_count": 1,
                        "metric_advisory_status_counts": {"proposed": 1},
                        "type_advisory_count": 0,
                        "type_advisory_status_counts": {},
                        "action_group_names": ["profile_map_updates"],
                        "suggested_next_actions": [...],
                        "suggested_next_calls": [...],
                    },
                ],
            },
        },
    ],
    "staged_review": {
        "count": 1,
        "returned_count": 1,
        "omitted_count": 0,
        "application_status_counts": {"pending": 1},
        "next_action_queue_item_counts": {"apply_after_review": 1},
        "items": [
            {
                "revision_iri": "https://...",
                "queue": "apply_after_review",
                "resolved_target_iri": "https://...",
                "revision_anchor_iris": ["https://..."],
                "evidence_iris": ["https://..."],
                "suggested_next_action": {...},
            }
        ],
    },
    "recommended_next_tasks": [
        {
            "priority": 10,
            "task_type": "query_repair_review",
            "source": "describe_query_context",
            "resource": {"iri": "https://...", "label": "...", "description": ...},
            "reason": "...",
            "suggested_next_action": {...},
            "suggested_next_call": "describe_query_context(...)",
            "profile_evidence_iri": null,
            "pending_staged_repair_iris": [],
            "pending_staged_profile_update_iris": [],
        },
    ],
    "limit": 20,
    "profile_candidate_limit": 2,
}
```

`project_brief` is an orientation helper, not a proof of correctness. Follow
its suggested actions into `describe_query_context`,
`draft_profile_map_updates`, `plan_staged_revision_recovery`,
`list_graph_revisions`, or the relevant focused inspection helper before making
durable graph changes.
`dataset_query_readiness_counts`, `profile_queue_counts`, and `queue_counts`
are computed across scanned table/dataset entities. For staged work,
`queue_counts["staged_frontier_review"]` appears when current staged work
exists. Its task points to `plan_staged_revision_recovery` so agents can inspect
`mutation_frontier_iris` and apply-one-then-recheck hazards before staging more
work. `queue_counts["staged_review"]` uses `staged_review.count`, while
`staged_review.items` and `returned_queue_counts` stay bounded by `limit`.
`staged_review.items[].revision_anchor_iris` lists graph revision anchors for
the returned staged row, and `evidence_iris` lists its direct revision evidence.
When a query repair task already has staged work anchored to the same dataset,
`pending_staged_repair_iris` names those staged revision IRIs and the task is
lowered behind `staged_review` so unattended agents review/apply the pending
repair before staging another one. This pending-repair field is query-specific:
the staged row must change query-planning metadata such as storage links, path
templates, storage fields, physical-layout fields, or partition metadata.
Unrelated same-dataset caveats or profile-map updates remain visible through
staged-review queues without marking the query repair pending. When a profile
task already has a staged profile-map-update revision anchored to the same
dataset and evidence,
`pending_staged_profile_update_iris` names those staged revision IRIs and the
task's suggested action is read-only `draft_profile_map_updates` instead of
another `stage_profile_map_updates` call. Generic same-evidence staged work
remains visible through `staged_frontier_review` / `staged_review` but does not
populate `pending_staged_profile_update_iris`. Pending profile-map updates only
demote pure map-update reruns; if scalar conflict, metric vocabulary, or type
advisory lanes remain open, the profile task stays at normal priority.
For `profile_review` tasks, `profile_evidence_iri` names the profile evidence
that scoped the task. Use it even when `suggested_next_action` is a shared
blocker action such as `describe_query_context`, because multiple profile
drafts for the same dataset can point at the same blocker first.
`datasets` and
`returned_dataset_query_readiness_counts` describe the bounded returned slice.
The recommended task selector keeps at least one task from each active queue
when the limit allows, then fills remaining slots by priority.
`health_tasks` is outside the bounded `recommended_next_tasks` slice. It reports
stable follow-ups such as `expand_project_brief` for omitted queues,
`privacy_export_review` when a redacted project scan finds potential sensitive
literals, and `seed_recovery_review` when immutable seed graphs are missing
current staging vocabulary. Check it before repeating the same visible task
types in an unattended loop.
When `limit_crowded_queue_types` is non-empty, the current `limit` was too low
to return a task from every active queue type. Rerun with a larger limit or
inspect `queue_counts`/`omitted_queue_counts` before choosing the next loop
target.
Non-table `rc:Dataset` resources stay visible in `datasets` with
`is_table=false`, but their query readiness is
`not_applicable_non_tabular_asset`; project brief routes them to
`non_tabular_asset_review` with a `describe_context_slice` action instead of
query repair queues.

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
graph actually stores. For exact typed decimals or language-tagged strings,
pass `object_datatype` or `object_lang`; those fields also let
`stage_map_assertion_change` author the same literal form.

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
Each predicate hint includes sample values in the same value shape used by
matching triples:

```python
hint.predicate
hint.predicate_curie
hint.predicate_label
hint.predicate_description
hint.triple_count
hint.sample_values
```

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
action.action_label
action.tool_name
action.mcp_tool_name
action.arguments
action.reason
action.call
```

Use `mcp_tool_name` and `arguments` when driving MCP calls. `action_label` is a
compact human label for the action's role in the route. `tool_name` is the local
helper-style name, and `suggested_next_calls` contains equivalent bare call
strings for older callers.
Some specialized actions carry extra structured fields. For example, a
profile-map rerun action can include `preconditions` naming the staged revision
that must be applied before the rerun is useful.

`RevisionNextAction` wraps the most relevant suggested action for queue routing:

```python
next_action.action_type
next_action.queue
next_action.action_label
next_action.tool_name
next_action.mcp_tool_name
next_action.arguments
next_action.reason
next_action.call
next_action.source
```

It is advisory. Use it to choose the first queue (`apply_after_review`,
`restage_after_review`, `repair_or_replace`, `inspect_already_applied`, or
`informational`), then inspect the full `suggested_next_actions` when the row
needs more context.

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
need to match a literal that contains a colon. Pass `object_datatype` such as
`"xsd:boolean"` or `"xsd:decimal"` to target or author a typed literal; pass
`object_lang` such as `"en"` to target or author a language-tagged literal.
Do not pass both on the same literal.

## Resource Context

`db.describe_resource(iri, graph=None, limit=50)` returns a `ResourceContext`:

```python
resource.iri
resource.graph
resource.label
resource.description
resource.types
resource.claim
resource.outgoing
resource.incoming
resource.blank_node_triples
resource.limit
resource.outgoing_offset
resource.incoming_offset
resource.outgoing_total_count
resource.outgoing_returned_count
resource.outgoing_omitted_count
resource.incoming_total_count
resource.incoming_returned_count
resource.incoming_omitted_count
resource.include_blank_node_closure
resource.blank_node_depth
resource.blank_node_limit
resource.blank_node_total_count
resource.blank_node_returned_count
resource.blank_node_omitted_count
resource.blank_node_depth_exhausted
resource.blank_node_unvisited_count
```

`outgoing[]` and `incoming[]` rows are `ResourceTriple` summaries:

```python
triple.graph
triple.subject
triple.subject_kind
triple.subject_label
triple.subject_types
triple.predicate
triple.predicate_label
triple.object
triple.object_kind
triple.object_label
triple.object_types
triple.object_datatype
triple.object_lang
```

Use this helper when a specific resource needs a local RDF neighborhood rather
than a route-explained context slice. The `claim` field is populated for claim
resources and has the normal claim-description shape.
Use `outgoing_offset` and `incoming_offset` to page high-degree resources when
the returned count is lower than the total count. Set
`include_blank_node_closure=True` for SHACL shapes and other RDF structures
whose important details live on blank nodes reached from direct outgoing
triples; closure rows are returned separately in `blank_node_triples` so
`outgoing` remains direct subject triples. If `blank_node_depth_exhausted` is
true, increase `blank_node_depth` before assuming the closure is complete; if
only `blank_node_omitted_count` is non-zero, increase `blank_node_limit`.

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
change.object_datatype
change.object_lang
change.assertion_present_before
change.current_values_before
change.additions
change.removals
change.assertion_support
change.revision_iri
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
panel.target_value
panel.removed_value
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

Common child rows inside the panel use these fields:

```python
value.value
value.label
value.value_kind
value.datatype
value.lang
value.caveat

caveat.caveat_iri
caveat.caveat_label
caveat.scope
caveat.route_label
caveat.via_resource
caveat.matched_resource
caveat.description
caveat.impact
caveat.severity_label

route.rank
route.resource_iri
route.resource_label
route.resource_kind
route.strongest_route_label
route.route_count
route.route_note
route.matched_resources
route.generic_value_only
route.relevance_note

impact.impact_type
impact.severity
impact.message
impact.removed_values
impact.added_values
```

The panel does not decide whether the change is right. It packages the current
and proposed values, physical/value-type context, reasons the current value may
be intentional, caveat scopes, strongest related-lore routes, deterministic
impact spotlight entries, and safety notes that a reviewer should consider
before apply. `semantic_risk_level` is `none`, `attention`, or `high`; it is a
review cue, not an apply decision or validation failure. `target_value` is the
requested assertion object for add, replace, and remove changes. `removed_value`
is populated for remove changes so reviewers do not have to read legacy
`proposed_value` as the value being removed. For exact removals,
`removed_value` reflects the graph triple that matched the request, so compatible
literal targeting keeps datatype or language-tag context visible even when the
request was a plain string. Remove-all changes leave `removed_value` empty; read
`current_values` and the removal patch to see every removed assertion.

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
Each value-type context row has:

```python
value_type_context.value_type
value_type_context.required_physical_type
value_type_context.current_physical_type_matches
value_type_context.proposed_physical_type_matches
value_type_context.note
```

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
context.seed_profile_observations
context.dataset_contexts
context.pattern_contexts
context.warnings
context.suggested_next_actions
context.suggested_next_calls
```

`seed_iris` is the input argument name. The returned field is `seeds` in Python
and `result["seeds"]` in MCP payloads.

`route_counts` is keyed by route id. `route_legend` is a list of rows, not a
dict; callers can build a dict keyed by `route` if that is more convenient.
There is no separate `route_summaries` field; use `reading_order`,
`route_counts`, and `route_legend` as the first route summary, then inspect
`resources[].primary_route` and `resources[].routes`.
Each `route_legend[]` item has:

```python
legend.route
legend.route_label
legend.meaning
legend.priority
legend.count
```

`reading_order` is static guidance for how to read the returned slice; it is not
recomputed as a custom plan for each query. Route counts are route occurrences,
not unique resource counts; a
resource reached through two useful routes contributes to both route counts.
Dataset/deep-lore slices can include routes such as
`dataset_profile_observation`, `column_profile_observation`,
`unmapped_column_profile_observation`, `seed_observed_column`,
`observed_profile_metric`, `observed_value_frequency`, `profile_metric_kind`, and
`profile_metric_target`. These routes are bounded by the same returned profile
observations used by `describe_dataset()`. A metric-kind IRI that has no subject
triples can still appear with `referenced_only=True` when it was reached through
`rc:profileMetricKind`. An observed-column IRI that has no mapped `rc:Column`
subject can still seed a dataset/deep-lore slice through matching
`rc:observedColumn` profile observations. Broad metric-kind seeds are capped;
read `warnings` for omitted observed profile metric counts and use narrower
seeds when needed.
Profile and metric seeds may include bounded same-dataset profile context
beyond the exact seed while avoiding unrelated dataset leakage.
`seed_profile_observations` gives structured `ProfileObservationSummary` rows
for explicit profile-observation seeds and profile observations reached from
observed-profile-metric, metric-kind, or observed-column seeds, even when those
rows are older than the bounded `dataset_contexts[].profile_observations` slice.
`resource_brief` slices are generic bounded resource handoffs. Their route
counts may include `resource_type`, `outgoing_reference`,
`blank_node_reference`, `incoming_reference`, `incoming_blank_node_owner`, and
`blank_node_seed_owner`, and `predicate_usage_subject`. Use raw
`triples`/`trig` to read the exact predicates behind those generic routes.
`incoming_blank_node_owner` can reach through nested blank-node shape fragments,
for example from a predicate used inside `sh:qualifiedValueShape` back to the
named owner shape. When a resource-brief route cap fires, warnings and
`suggested_next_actions` name the recovery route. Outgoing/incoming reference
caps point to paged `describe_resource` calls, blank-node reference caps point to
`describe_resource(..., include_blank_node_closure=True)`, and predicate usage
caps point to graph export/narrowing because there is no paged predicate-usage
browser yet. Raising `max_triples` does not recover route-capped resources; it
only returns more raw triples for resources already selected.
Incoming reference caps are usefulness-ranked before selection, so resources
with direct claims, caveats, patterns, profile observations, staged revisions,
or dataset/column roles are preferred over plain generic references. Use the
paged `describe_resource` action when you need the exhaustive inbound list.
`suggested_next_actions` can include `describe_query_context` for seed tables or
seed-reached owner tables whose query context has repair groups or whose nested
`dataset_contexts[].operational_warnings` contain query-planning errors or
warnings. This includes mapped column, storage access, physical-layout, and
partition-scheme seeds that expand to an owning table through direct
incoming/reference routes.
Non-table dataset seeds stay on context-slice/resource routes even when they
carry storage or layout metadata. Use that route to inspect readiness, target
candidates, and repair hints before drafting a query.
For `profile="deep_lore"`, selected resources can also pull in revision history
through `revision_anchor_match` when they are named by `rc:revisionAnchor`.
This lets dataset, storage, layout, and partition slices show staged or applied
query-metadata repairs even when the revision has no supporting claim,
observation, or pattern.
When `truncated=true`,
the remaining actions first offer narrower
`describe_context_slice(..., profile="pattern_brief")` calls for linked pattern
contexts, then a same-seed retry with `max_triples` raised to
`candidate_triple_count` for cases that truly need complete raw RDF. Use the
pattern action before raising the cap when the structured pattern summary is
enough.

Each item in `context.resources` is a `ContextSliceResource`:

```python
resource.iri
resource.label
resource.description
resource.types
resource.graphs
resource.surface_role
resource.referenced_only
resource.primary_route
resource.routes
```

`resource.primary_route` is the first full `ContextSliceRoute` object from
`resource.routes`, not a scalar route id. Read `resource.primary_route.route`
or MCP `resource["primary_route"]["route"]` when you only need the route name.

`surface_role` is a compact graph-role cue for first-pass reading. Current
values are `current_map_context`, `observation_context`, `pattern_synthesis`,
`evidence_support`, `revision_history`, `vocabulary_context`,
`validation_shape_context`, `mixed_context`, and `referenced_only`. Use it to
separate current map/model context from point-in-time observations, pattern
synthesis, evidence, revision metadata, validation shapes, and plain object
references before inspecting raw triples.

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

`db.record_observation(...)` returns an `ObservationRecord`:

```python
observation.observation_iri
observation.observation_type
observation.evidence_iri
observation.observation_triples
observation.evidence_triples
```

`db.record_query_result(...)` returns a `QueryResultRecord`:

```python
result.observation_iri
result.observation_type
result.evidence_iri
result.source_span_iri
result.execution_status
result.engine
result.query_source_path
result.query_hash
result.result_sources
result.observation_triples
result.evidence_triples
result.source_span_triples
```

The helper does not run queries. It records an externally executed result or
failure as an observation with evidence. Successful calls with profile-shaped
fields such as `sample_size`, `row_count`, `null_count`, value frequencies, or
profile metrics become `observation_type="profile"`; failed, blocked, partial,
or cancelled attempts stay ordinary observations and reject profile count
fields. For filtered or grouped aggregate result payloads, prefer
`result_sources` plus clear `summary`/`sample_scope`/`sample_method` text unless
the count-like value is intentionally profile evidence.

For direct profile type findings, call it with `observation_type="profile"`,
`observed_column`, and `observed_physical_type` / `observed_value_type`. These
persist observed type evidence without asserting current map facts.

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
bundle.handoff_entrypoints
```

`bundle.dataset_profile` has the same shape as `DatasetProfileRecord`, and each
`bundle.column_profiles[]` item has the same shape as `ColumnProfileRecord`.
The bundle helper does not create a separate RDF bundle node; it is an API
convenience over the normal profile records. `shared_evidence_iri`, when
supplied, makes the returned profile observations point at the same evidence
IRI unless a column item overrides it with its own `evidence_iri`.
When bundle pattern fields are supplied, the default
`pattern_support_scope="dataset_profile"` keeps the helper-created pattern
supported by the dataset profile observation only. Use
`pattern_support_scope="all_profiles"` for a run-level pattern supported by the
dataset profile plus every bundled column profile. If the synthesis also needs
claims or hand-picked observations, call `describe_profile_run(...)` and pass
`profile_observation_iris` plus the extra support to `record_pattern` manually.

`bundle.handoff_entrypoints` is the compact next-agent entrypoint object:

```python
bundle.handoff_entrypoints.dataset_iri
bundle.handoff_entrypoints.shared_evidence_iri
bundle.handoff_entrypoints.dataset_profile_observation_iri
bundle.handoff_entrypoints.column_profile_observation_iris
bundle.handoff_entrypoints.profile_observation_iris
bundle.handoff_entrypoints.map_dataset_recorded
bundle.handoff_entrypoints.map_column_iris
bundle.handoff_entrypoints.updated_map_column_iris
bundle.handoff_entrypoints.mapped_profiled_column_iris
bundle.handoff_entrypoints.dataset_describe_available
bundle.handoff_entrypoints.profile_run_available
bundle.handoff_entrypoints.suggested_next_actions
bundle.handoff_entrypoints.suggested_next_calls
bundle.handoff_entrypoints.handoff_note
```

When `dataset_describe_available` is false, do not start a handoff by calling
`describe_dataset`; use `describe_profile_run(dataset_iri, shared_evidence_iri)`
when `profile_run_available` is true, or seed `describe_context_slice` from
`profile_observation_iris`. This commonly happens when
`update_map_snapshot=False` keeps a brand-new dataset observation-only.
`map_dataset_recorded` means this bundle call wrote dataset map facts. It can be
false while `dataset_describe_available` is true when map context already existed
before a bundle recorded profile observations with `update_map_snapshot=False`.
`map_column_iris` is the legacy name for column map facts written by this bundle
call; prefer `updated_map_column_iris` for that meaning. Use
`mapped_profiled_column_iris` when a receiving agent needs every bundled column
profile that is mapped after the call, including pre-existing mapped columns
profiled with `update_map_column=False`.
Use `suggested_next_actions` for structured handoff routing; it carries the
same `SuggestedNextAction` shape used elsewhere, usually starting with
`describe_dataset` when map context exists, `describe_profile_run` when shared
evidence is available, `draft_profile_map_updates` when both map context and a
profile run are available, and profile-observation-seeded
`describe_context_slice`.
Map-present bundles can include two `describe_context_slice` actions. They are
not duplicates: the dataset-seeded action loads current map/dataset context,
while the profile-observation-seeded action is the direct profile-run handoff.
Distinguish them by `action_label` and `arguments`, not just by repeated
`tool_name`.
`suggested_next_calls` remains as a compatibility list of display call strings.

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
    pattern_summary="Orders profile pass links dataset and column measurements.",
    pattern_text="The row count, status distinct count, and amount nullability came from one profiling pass.",
    pattern_rationale="Every bundled profile observation links to the same shared run evidence.",
    pattern_support_scope="all_profiles",
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

`db.describe_dataset(table_iri)` returns a `DatasetDescription`. Common fields
include:

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

The current full payload also includes provenance and related-dataset handoff
fields such as `dataset.provenance`, `dataset.transformations`,
`dataset.related_datasets`, and `dataset.related_dataset_groups`. Treat the list
above as the common working set, not as an exhaustive whitelist.

Cold-route note: this long doc also contains linked pattern reasons,
query-context fields, and draft-query-plan fields. Use the section headings
`Linked Pattern Reasons`, `Query Context`, and `Draft Query Plan` when reading
through MCP `get_doc(section=...)`.

### Dataset Storage And Layout

Nested physical handoff rows use these common fields:

```python
layout.iri
layout.label
layout.description
layout.file_format
layout.compression_codec
layout.layout_verification_status
layout.layout_verification_note

storage.iri
storage.label
storage.description
storage.storage_protocol
storage.access_mode
storage.location_kind
storage.storage_root
storage.endpoint_profile
storage.bucket_name
storage.key_prefix
storage.region
storage.path_style_access
storage.credential_reference
storage.path_templates
storage.layout_verification_status
storage.layout_verification_note
```

Each `dataset.related_datasets[]` row is the compact peer summary:

```python
related.iri
related.label
related.description
related.relationship
related.relationship_iri
related.relationship_label
related.relationship_kind
related.relationship_kind_label
```

Related dataset groups preserve the relationship route that linked each peer:

```python
group.iri
group.label
group.description
group.reasons

reason.relationship
reason.relationship_iri
reason.relationship_label
reason.relationship_kind
reason.relationship_kind_label
reason.columns
reason.current_dataset_columns
reason.related_dataset_columns
reason.declared
reason.referential_integrity
reason.source_caveats
reason.relationship_tags

tag.relationship
tag.relationship_iri
tag.relationship_label
tag.relationship_kind
tag.relationship_kind_label
tag.declared
tag.referential_integrity
```

### Linked Pattern Reasons

Linked pattern reasons summarize why patterns were pulled into the dataset
handoff:

```python
pattern_reason.iri
pattern_reason.pattern_iri
pattern_reason.label
pattern_reason.pattern_text
pattern_reason.rationale
pattern_reason.match_group_count
pattern_reason.raw_match_count
pattern_reason.relevance_tier_counts
pattern_reason.match_groups
pattern_reason.matches
```

Resource-valued dataset fields such as `row_semantics`, `entity_key`, and
`schema_stability` return resource summaries or IRIs. Use `dataset.description`,
layout notes, caveats, observations, claims, or patterns for explanatory prose.

`dataset.profile_summary` is a quick count of the profile lore returned in this
bounded `describe_dataset` response:

```python
profile_summary.returned_dataset_profile_count
profile_summary.returned_mapped_column_profile_count
profile_summary.returned_unmapped_column_profile_count
profile_summary.returned_profile_count
profile_summary.total_dataset_profile_count
profile_summary.total_mapped_column_profile_count
profile_summary.total_unmapped_column_profile_count
profile_summary.total_profile_count
profile_summary.omitted_dataset_profile_count
profile_summary.omitted_mapped_column_profile_count
profile_summary.omitted_unmapped_column_profile_count
profile_summary.omitted_profile_count
profile_summary.mapped_profiled_column_count
profile_summary.evidence_iris
profile_summary.evidence_profile_counts
profile_summary.shared_evidence_iris
profile_summary.profile_run_candidates
profile_summary.handoff_note
```

Returned counts describe the bounded response; total and omitted counts tell
you whether additional profile observations exist beyond that returned slice.
`evidence_iris` lists unique evidence IRIs linked from returned profile
observations. `evidence_profile_counts` counts how many returned profile
observations link to each evidence IRI.
`shared_evidence_iris` lists evidence IRIs that are linked from every returned
profile observation in the bounded response; it can be empty when older or
unrelated returned profiles are mixed with a newer shared-evidence bundle. In
that mixed-history case, use `evidence_profile_counts` to spot evidence IRIs
that support several profiles from the same run. `profile_run_candidates`
contains the count-ranked evidence IRIs that support more than one returned
profile; each candidate has `evidence_iri`, `returned_profile_count`,
`profile_observation_iris`, `dataset_profile_row_counts`,
`dataset_profile_row_count_bases`, `row_count_snapshot_matches`,
`row_count_snapshot_basis`, and `shared_by_all_returned_profiles`.
Singleton evidence remains visible in `evidence_iris` and
`evidence_profile_counts` even when it is not a `profile_run_candidates[]` row.
Candidates are ordered by returned profile count, then by whether a returned
dataset-profile `row_count` matches `row_count_snapshot`, then by evidence IRI.
`dataset_profile_row_count_bases` is keyed by row-count string and records the
per-observation basis labels behind that count, such as `full_scan`, `sample`,
or `unknown`. `row_count_snapshot_basis` tells you the collapsed basis for the
matching map snapshot when there is one; it can be `mixed` when the matching
count has more than one basis. A match can still be sampled or unknown-scope
evidence.
Use
`profile_observation_iris` to seed `describe_context_slice` or inspect the
returned observations that make up the candidate run. It is a bounded response
convenience, not a separate persisted profile-run node. `handoff_note` is a
compact reading cue for profile-only handoffs: profile lore is observed
evidence, while storage/path/layout warnings remain physical query-planning
metadata gaps.

### Describe Profile Run

`db.describe_profile_run(dataset_iri, evidence_iri, limit=None)` returns a
`ProfileRunDescription`:

```python
profile_run.dataset
profile_run.evidence
profile_run.evidence_iri
profile_run.row_count_snapshot
profile_run.dataset_profile_row_counts
profile_run.dataset_profile_row_count_bases
profile_run.row_count_snapshot_matches
profile_run.row_count_snapshot_basis
profile_run.returned_dataset_profile_count
profile_run.returned_mapped_column_profile_count
profile_run.returned_unmapped_column_profile_count
profile_run.returned_profile_count
profile_run.total_dataset_profile_count
profile_run.total_mapped_column_profile_count
profile_run.total_unmapped_column_profile_count
profile_run.total_profile_count
profile_run.omitted_dataset_profile_count
profile_run.omitted_mapped_column_profile_count
profile_run.omitted_unmapped_column_profile_count
profile_run.omitted_profile_count
profile_run.profile_observation_iris
profile_run.dataset_profile_observations
profile_run.mapped_column_profile_observations
profile_run.unmapped_column_profile_observations
profile_run.retrieval_note
```

Use `describe_profile_run` when a `profile_run_candidates[]` entry identifies
a shared-evidence run that may be wider than the bounded `describe_dataset`
profile lists. With `limit=None`, returned and total counts should match unless
the run has no observations for that dataset. A positive `limit` caps returned
profiles and leaves omitted counts non-zero.
The row-count fields summarize all dataset-profile observations in the requested
evidence run, not only the capped returned slice.
`dataset_profile_row_count_bases` uses row-count strings as keys and records
per-observation basis labels such as `full_scan`, `sample`, or `unknown`; use
`row_count_snapshot_basis` to see the collapsed matching-snapshot basis, which
may be `mixed`, and keep the profile-run step aligned with the candidate warning
from `profile_summary.profile_run_candidates[]`.

### Profile Map Update Drafts

`db.draft_profile_map_updates(dataset_iri, evidence_iri)` returns a
`ProfileMapUpdateDraft`:

```python
draft.dataset
draft.evidence
draft.evidence_iri
draft.map_dataset_found
draft.profile_observation_iris
draft.recommendations
draft.recommendation_count
draft.representative_recommendation_indexes
draft.scalar_conflict_groups
draft.scalar_conflict_group_count
draft.metric_advisories
draft.metric_advisory_count
draft.representative_metric_advisory_indexes
draft.metric_advisory_status_counts
draft.type_advisories
draft.type_advisory_count
draft.representative_type_advisory_indexes
draft.type_advisory_status_counts
draft.suggested_next_actions
draft.suggested_next_calls
draft.suggested_next_action_groups
draft.suggested_next_call_groups
draft.review_note
```

Each `draft.recommendations[]` row is read-only review context, not an applied
or staged change:

```python
recommendation.kind
recommendation.recommendation_index
recommendation.action
recommendation.resource
recommendation.predicate
recommendation.current_value
recommendation.observed_value
recommendation.observed_count
recommendation.sample_size
recommendation.sample_scope
recommendation.sample_method
recommendation.profile_row_count
recommendation.profile_observation_iri
recommendation.evidence_iri
recommendation.basis
recommendation.confidence
recommendation.helper_name
recommendation.helper_arguments
recommendation.rationale
recommendation.default_stageable
recommendation.default_skip_reason
recommendation.duplicate_group_key
recommendation.duplicate_count
recommendation.duplicate_recommendation_indexes
recommendation.duplicate_profile_observation_iris
```

Current recommendation kinds cover `dataset_row_count_snapshot`,
`column_nullable`, and `unmapped_profiled_column`. The helper drafts candidates
from positive-null findings, full-scan zero-null findings, profile row counts,
and unmapped profiled columns. It intentionally skips sampled zero-null
promotion because a sample with no nulls does not prove a full-population
non-null constraint. For assets explicitly modeled with `is_table=false`, row
counts stay profile evidence and are not drafted as
`dataset_row_count_snapshot` recommendations. `default_stageable` and
`default_skip_reason` preview what
`stage_profile_map_updates` will do with default options; sampled row-count
recommendations remain review candidates but are skipped by default unless
`allow_sampled_row_count_updates=True`. Same-evidence scalar conflicts, such as
multiple full-scan row counts for one dataset or multiple nullable values for
one column, are also non-default-stageable until one value is chosen explicitly.
`unmapped_profiled_column` duplicate groups are keyed by the helper mutation,
not profile-specific sample details, so one accepted representative can stage the
column shell while preserving all supporting profile observations.

`scalar_conflict_groups[]` gives a structured choose-one route for those
non-default-stageable scalar conflicts:

```python
group.conflict_group_index
group.evidence_iri
group.resource
group.predicate
group.kind
group.current_value
group.option_count
group.options
group.review_note

option.observed_value
option.representative_recommendation_index
option.recommendation_indexes
option.duplicate_recommendation_indexes
option.duplicate_profile_observation_iris
option.suggested_next_action
option.suggested_next_call
```

Each option's suggested action is a `stage_profile_map_updates` call for one
representative recommendation index for that observed value. These option
actions also appear in the grouped `profile_scalar_conflict_review` lane with
`source_scalar_conflict` metadata, but are intentionally not copied into the
draft's flat `suggested_next_actions`; review the group and choose at most one
option before calling one explicitly.

`metric_advisories[]` rows name project-specific profile metric IRIs observed
in the run and recommend vocabulary review before reusable comparison or map
policy. Each advisory includes:

```python
advisory.profile_observation_iri
advisory.observed_metric_iri
advisory.metric_advisory_index
advisory.evidence_iri
advisory.metric
advisory.target
advisory.value
advisory.value_datatype
advisory.value_lang
advisory.advisory_status
advisory.definition_found
advisory.definition
advisory.promotion_patterns
advisory.promotion_pattern_count
advisory.mixed_support_patterns
advisory.mixed_support_pattern_count
advisory.mixed_support_note
advisory.context_patterns
advisory.context_pattern_count
advisory.pending_staged_promotion_iris
advisory.pending_staged_promotion_count
advisory.recommendation
advisory.rationale
advisory.suggested_next_actions
advisory.suggested_next_calls
advisory.duplicate_group_key
advisory.duplicate_count
advisory.duplicate_advisory_indexes
advisory.duplicate_profile_observation_iris
```

`advisory_status` is `project_metric_undefined`,
`project_metric_defined`, or `project_metric_definition_ambiguous`.
Undefined metrics point suggested actions at observed-metric context loading and
nearby ontology metric lookup. The first `describe_context_slice` action seeds
`observed_metric_iri`, not the broad metric-kind IRI, so the handoff stays on
the profiled dataset before reviewing wider same-metric usage. Ambiguous metrics
add existing-definition inspection before any repair path. If an undefined or
ambiguous metric also has a same-evidence
pattern that names the metric as a target or map implication, the advisory
includes `promotion_patterns` and adds `describe_pattern`. If matching current
staged metric vocabulary work already exists for the same metric, evidence, and
pattern support, `pending_staged_promotion_iris` names those staged revisions and
the advisory routes to `describe_staged_revision` plus
`export_staged_revisions` instead of proposing another duplicate
`stage_pattern_promotion` skeleton. Otherwise it adds a reviewable
`stage_pattern_promotion` ontology skeleton to `suggested_next_actions`.
When a rerun reports `project_metric_defined`, do not stage duplicate
vocabulary; use the observed-metric context action for the dataset handoff and a
`deep_lore` slice from the metric, promotion pattern, or revision when you need
the promotion support trail.
The skeleton seeds its `rdfs:comment` from matched pattern text, rationale, or
summary only when that text mentions the metric IRI, local name, or normalized
local-name phrase. Otherwise it uses a generic review-first comment. Treat it as
a draft definition and review units, calculation, and comparison semantics
before apply. If the same promotion pattern is also used by a type advisory,
`mixed_support_patterns`, `mixed_support_pattern_count`, and
`mixed_support_note` flag the shared evidence so agents do not promote the
metric without inspecting the type-review lane. Same-evidence prose
patterns that mention the metric without structurally targeting or implying it
appear in `context_patterns` and add `describe_pattern` actions only; they are
inspection cues, not automatic promotion support.
Defined metrics point at
`describe_resource(..., graph="ontology")` for the existing definition;
ambiguous metrics point at both the existing definition and nearby metric
lookup even when no promotion skeleton is available. Use
`metric_advisory_count` and `metric_advisory_status_counts` for queue routing
before reading full advisory rows.
Duplicate fields are populated for every recommendation and advisory. Count `1`
means the row is unique in this draft; higher counts mean repeated profile
observations produced the same review row. Agents can accept one representative
recommendation index from a duplicate group when the modelling judgement is the
same for all siblings. For advisory lanes, start with
`representative_metric_advisory_indexes` and
`representative_type_advisory_indexes` when you need one review row per
duplicate group, then read each representative advisory's duplicate fields when
you need the grouped profile observation support. Rows also carry their own
`metric_advisory_index` or `type_advisory_index`, so scripts do not need to
reconstruct list positions while following representative index lists.

`type_advisories[]` rows surface observation-only `physical_type` and
`value_type` findings. They are not accepted recommendation indexes and are not
staged automatically; follow their suggested actions to inspect context, record
a type-finding pattern, or stage a focused map assertion after review. Each row
includes:

```python
advisory.profile_observation_iri
advisory.type_advisory_index
advisory.evidence_iri
advisory.observed_column
advisory.observed_column_name
advisory.observed_physical_type
advisory.observed_value_type
advisory.map_column_found
advisory.current_physical_type
advisory.current_value_type
advisory.promotion_patterns
advisory.promotion_pattern_count
advisory.mixed_support_patterns
advisory.mixed_support_pattern_count
advisory.mixed_support_note
advisory.advisory_status
advisory.recommendation
advisory.rationale
advisory.routing_note
advisory.related_recommendation_indexes
advisory.related_recommendation_kinds
advisory.suggested_next_actions
advisory.suggested_next_calls
advisory.duplicate_group_key
advisory.duplicate_count
advisory.duplicate_advisory_indexes
advisory.duplicate_profile_observation_iris
```

`advisory_status` is `type_finding_unmapped_column`,
`type_finding_conflicts_current_map`, `type_finding_missing_map_type`, or
`type_finding_needs_review`. The `describe_context_slice` suggested action
omits observed type IRIs that do not yet exist as graph resources, so the action
can be followed directly; undefined project value types still remain in the
`record_pattern` map implications and focused `stage_map_assertion_change`
payloads. If an undefined or not-yet-typed project value type also has a
same-evidence pattern that names it as a target or map implication,
`suggested_next_actions` adds `describe_pattern` and a reviewable
`stage_pattern_promotion` ontology skeleton for `rc:ValueType`. The skeleton
borrows pattern prose for its `rdfs:comment` only when that prose mentions the
value type IRI, local name, or normalized local-name phrase; otherwise it uses a
generic review-first comment. If the same promotion pattern is also used by a
metric advisory, `mixed_support_patterns`, `mixed_support_pattern_count`, and
`mixed_support_note` flag the shared evidence; grouped promotion and
`stage_map_assertion_change` actions also carry this cue in
`source_profile_advisory.mixed_support` and review notes. Use
`type_advisory_count` and `type_advisory_status_counts` for queue routing before
reading full advisory rows. For `type_finding_unmapped_column`,
`related_recommendation_indexes` points at the matching
`unmapped_profiled_column` shell recommendation; review/stage that column-shell
route first, then rerun or review type assertions once the column is
map-present. When duplicate type advisories collapse to one top-level suggested
action set, the representative pattern/staged-assertion actions preserve every
grouped profile observation in `supporting_observations`.

Use `suggested_next_action_groups` for first-pass machine routing. Groups are
present only when non-empty and currently use `query_context_review`,
`profile_map_updates`, `profile_scalar_conflict_review`,
`metric_vocabulary_review`, and `profile_type_review`.
`query_context_review` appears first when the dataset already has physical-query
metadata such as a path template or layout, but `describe_query_context` still
reports blocking physical metadata issues such as `missing_storage_access`.
Follow that lane before treating profile-derived map updates as query-ready
context; the profile recommendations remain available for explicit review.
`suggested_next_call_groups`
mirrors those groups with display call strings. The flat top-level
`suggested_next_actions` / `suggested_next_calls` fields remain for compatibility
and include only bulk-safe default map/advisory lanes plus the leading
query-context review action when present; scalar-conflict option actions stay
grouped only. Group lanes may de-duplicate shared actions, such as one
`describe_pattern` action used by several metric advisories. Query-context
review actions carry `source_query_context`:

```python
action.source_query_context["review_lane"]
action.source_query_context["route_group_key"]
action.source_query_context["route_step_key"]
action.source_query_context["evidence_iri"]
action.source_query_context["profile_evidence_iri"]
action.source_query_context["route_anchor_iris"]
action.source_query_context["readiness"]
action.source_query_context["readiness_note"]
action.source_query_context["blocking_issue_codes"]
action.source_query_context["issue_codes"]
action.source_query_context["suggested_repair_action_group_count"]
```

`evidence_iri` and `profile_evidence_iri` both identify the profile run that
caused the query-context lane to appear. They keep first-hop
`describe_query_context` actions distinguishable when multiple profile runs on
one dataset share the same blocker.

Grouped profile map-update actions are `ProfileMapUpdateSuggestedNextAction`
rows and carry `source_profile_map_update`:

```python
action.source_profile_map_update["review_lane"]
action.source_profile_map_update["route_group_key"]
action.source_profile_map_update["route_step_key"]
action.source_profile_map_update["recommendation_indexes"]
action.source_profile_map_update["duplicate_group_keys"]
action.source_profile_map_update["duplicate_recommendation_indexes"]
action.source_profile_map_update["duplicate_profile_observation_iris"]
action.source_profile_map_update["route_anchor_iris"]
action.source_profile_map_update["route_pattern_iris"]
```

Grouped metric/type actions are `ProfileAdvisorySuggestedNextAction` rows and
carry source metadata:

```python
action.source_profile_advisory["review_lane"]
action.source_profile_advisory["route_group_key"]
action.source_profile_advisory["route_step_key"]
action.source_profile_advisory["advisory_kind"]
action.source_profile_advisory["index_field"]
action.source_profile_advisory["advisory_indexes"]
action.source_profile_advisory["duplicate_group_keys"]
action.source_profile_advisory["duplicate_advisory_indexes"]
action.source_profile_advisory["duplicate_profile_observation_iris"]
action.source_profile_advisory["route_anchor_iris"]
action.source_profile_advisory["route_pattern_iris"]
action.source_profile_advisory["observed_metric_iris"]
action.source_profile_advisory["mixed_support"]
```

Use `route_group_key` to connect grouped draft actions to later profile insight
bundle candidates, and `route_step_key` to distinguish individual actions within
the same duplicate/advisory group. Scripts should inspect optional metric-only
`observed_metric_iris` before choosing a context seed, and optional
`mixed_support` before applying grouped promotion or assertion actions; it names
shared promotion pattern IRIs, the other review lane, and the review note. When
both lanes generate staged promotion/assertion drafts from the same pattern,
review or export those drafts together before applying either lane independently.
Scripts that need per-metric or per-column follow-through can still iterate
`metric_advisories[]` or `type_advisories[]` by the representative advisory
indexes first, then use each representative advisory's row-local index,
duplicate-group fields, and own
`suggested_next_actions`. `profile_type_review`
is a representative action queue; labels such as `Inspect profile type context`
and `Stage physical type assertion` can repeat across advisory groups.
Drafts with at least one default-stageable representative recommendation include
a `stage_profile_map_updates` action whose
`accepted_recommendation_indexes` defaults to those representatives. Sampled
row-count recommendations can still appear in
`representative_recommendation_indexes` for review, but the default staging
action omits them unless the caller explicitly opts in. Same-evidence scalar
conflicts also stay visible for review but are omitted from the default staging
action. Their option actions appear in the
`profile_scalar_conflict_review` lane and carry `source_scalar_conflict`:

```python
action.source_scalar_conflict["route_group_key"]
action.source_scalar_conflict["route_step_key"]
action.source_scalar_conflict["selection_rule"]
action.source_scalar_conflict["conflict_group_index"]
action.source_scalar_conflict["kind"]
action.source_scalar_conflict["resource_iri"]
action.source_scalar_conflict["predicate"]
action.source_scalar_conflict["observed_value"]
action.source_scalar_conflict["representative_recommendation_index"]
action.source_scalar_conflict["duplicate_profile_observation_iris"]
```

Use `route_group_key` to keep all options for one choose-one decision together
and `route_step_key` to distinguish the individual explicit staging actions.
Use that lane for discovery, then pick at most one chosen value for each
row-count or nullable conflict group. These option actions are intentionally not
copied into flat `suggested_next_actions`.
When same-evidence
profile patterns target or imply the dataset or recommendation resources, the
suggested staging arguments also include `supporting_patterns` so the staged map
revision carries the directly relevant synthesis without a second pattern
lookup. Metric-only and type-only profile patterns stay in their advisory lanes
unless the caller explicitly passes them as support. Column-targeted patterns
that mention observed physical/value type resources stay in
`profile_type_review` by default even when they also name a recommended column.
When authoring a metric vocabulary pattern that should remain advisory-only,
target or imply the metric IRI rather than the dataset; dataset-targeted
patterns are eligible to support the map patch. Pass only the indexes actually
accepted after reviewing sample scope and modelling intent; include duplicate
sibling indexes only when they need distinct review treatment.
When `draft.recommendations` is empty and either metric or type advisories are
present, the draft is advisory-only. The grouped and flat suggested actions are
the deduped advisory actions for vocabulary/context/type review; do not call
`stage_profile_map_updates` because no-op advisory staging is deferred. When map
recommendations and advisories coexist, follow the `profile_map_updates` lane for
accepted map facts, then continue the metric/type review lanes separately.

### Profile Map Update Staging

`db.stage_profile_map_updates(dataset_iri, evidence_iri, accepted_recommendation_indexes=[...])`
returns a `ProfileMapUpdateStagingRecord`:

Optional caller support parameters:

```python
supporting_claims
supporting_patterns
revision_anchors
```

These links are written only when at least one accepted recommendation produces
a staged patch. Caller `revision_anchors` are merged with the automatic
profile-derived dataset/resource anchors.

```python
result.result_kind
result.dataset
result.evidence
result.evidence_iri
result.map_dataset_found
result.recommendation_count
result.accepted_recommendation_indexes
result.staged_recommendation_indexes
result.skipped_recommendation_indexes
result.not_selected_recommendation_indexes
result.status_counts
result.items
result.metric_advisories
result.metric_advisory_count
result.metric_advisory_status_counts
result.metric_vocabulary_review_required
result.metric_advisory_suggested_next_actions
result.metric_advisory_suggested_next_calls
result.type_advisories
result.type_advisory_count
result.type_advisory_status_counts
result.type_review_required
result.type_advisory_suggested_next_actions
result.type_advisory_suggested_next_calls
result.staged_revision
result.suggested_next_actions
result.suggested_next_calls
result.review_note
```

`result_kind` is `profile_map_update_staging`; use it as the semantic
discriminator when automation is handling several staged-revision-producing
helpers.

Each `result.items[]` row is a compact routing record:

```python
item.recommendation_index
item.kind
item.action
item.resource
item.status              # staged, skipped, or not_selected
item.reason
item.basis
item.confidence
item.sample_size
item.sample_scope
item.sample_method
item.profile_observation_iri
item.supporting_profile_observation_iris
```

When at least one accepted recommendation passes safety checks,
`result.staged_revision` is a normal `StagedGraphRevisionRecord` for one grouped
`map` revision. `suggested_next_actions` then starts with
`check_staged_revision_apply` for that staged revision, followed by an
`export_profile_insight_review_bundle` action seeded with the same staged
revision. Run the read-only check before reviewing or applying, and re-run the
bundle export after staging related metric vocabulary, type-review, or
caveat/systematisation alternatives that should be reviewed together. When the
staged patch added an unmapped column shell, `suggested_next_actions` also
includes a
`draft_profile_map_updates` rerun for the same dataset/evidence; follow it
after the staged shell has been reviewed and applied. That rerun action carries
`preconditions.staged_revision_applied` so scripts can avoid firing it before
the shell is durable. Each item echoes the profile
observation IRIs that support that recommendation, including duplicate sibling
observations when the row belongs to a duplicate group; accepted staged rows
feed those lists into the grouped revision support. Use
`describe_staged_revision()` to inspect caller claim/pattern support, revision
anchors, shared evidence, and the final grouped staged-revision support because
the immediate staging response
stays compact. In staged revision detail, `supporting_patterns` is the direct
support set for the map patch, while `impacts[].related_patterns` is broader
nearby context and may include metric/type advisory patterns that were not used
as direct support. If an accepted representative belongs to a duplicate group, the
staged revision preserves all `duplicate_profile_observation_iris` from that
group as supporting observations even though only the accepted index appears as
`staged`. Sampled row-count
recommendations are skipped by default and
reported in `skipped_recommendation_indexes`; accepted same-evidence scalar
conflicts are also skipped when the accepted set contains multiple observed
values for one row-count or nullable assertion. Choose one value explicitly
after reviewing the profile observations. Metric advisories stay in
`metric_advisories` and are not staged as map facts. When
`metric_vocabulary_review_required` is true,
`metric_advisory_suggested_next_actions` is the separate vocabulary-review lane;
follow it in addition to the map revision apply check, not as a replacement for
the apply check. These grouped actions also carry `source_profile_advisory` so
automation can see which metric advisory rows and duplicate support they cover.
The same advisory count and status summary appears in the staging response and
staged revision review note, so later reviewers can see whether undefined,
defined, or ambiguous project metric vocabulary was present.
When `type_review_required` is true,
`type_advisory_suggested_next_actions` is the separate profile-type review lane;
use it to inspect, record support patterns, or stage focused type assertions
after reviewing the map update. These grouped actions carry the same
`source_profile_advisory` metadata for type advisory rows. The type-review lane
is not part of the grouped map patch and is not a replacement for the staged
revision apply check. If the staged map patch added an unmapped column shell and
the review note mentions `type_finding_unmapped_column`, apply the shell after
review, then use the structured `draft_profile_map_updates` rerun action so the
type advisories can reclassify against a map-present column and expose focused
`stage_map_assertion_change` actions.
When no accepted recommendation produces a staged patch,
`result.staged_revision is None` and `suggested_next_actions` is empty.
An accepted recommendation index can therefore appear under either `staged` or
`skipped`; `not_selected` only means the draft recommendation was not accepted
for this staging call. Use `status_counts` for quick routing summaries before
reading per-item reasons.

### Profile Insight Review Bundle

`db.export_profile_insight_review_bundle(dataset_iri, evidence_iri, path, ...)`
returns a `ProfileInsightReviewBundleRecord`:

```python
result.result_kind
result.dataset
result.evidence
result.evidence_iri
result.profile_observation_iris
result.related_pattern_iris
result.candidate_revision_iris
result.candidate_count
result.candidates
result.export
result.warnings
result.review_note
```

`result_kind` is `profile_insight_review_bundle`. `export` is the nested
`StagedGraphRevisionsExportRecord` when at least one related staged revision was
found; otherwise it is `None` and `warnings` explains that no bundle was
written. When the nested staged Markdown export contains credential-like patch
literals, `result.export.sensitive_literal_count` and
`result.export.privacy_warnings` carry the same warning fields as direct grouped
staged exports. Pass `fail_on_sensitive=True` to block before writing the nested
Markdown bundle when such matches are present. Default discovery includes current
staged work and
already-applied staged source rows matched through the same profile
evidence/observation/pattern/anchor routes; set
`include_applied_staged_sources=false` only when a caller intentionally wants
current staged rows without applied profile-map sources. Raise
`applied_staged_source_limit` when a profile run has more applied source matches
than the default scan returns.

Each `result.candidates[]` row explains why one staged revision was included:

```python
candidate.revision_iri
candidate.summary
candidate.changed_graphs
candidate.relation_reasons
candidate.profile_route_keys
candidate.profile_route_groups
candidate.matched_evidence_iris
candidate.matched_profile_observation_iris
candidate.matched_supporting_pattern_iris
candidate.matched_revision_anchor_iris
candidate.explicit
```

`relation_reasons` can include `explicit_revision_iri`,
`shared_profile_evidence`, `supporting_profile_observation`,
`supporting_related_pattern`, and `profile_derived_anchor`. Same evidence alone
does not make an unrelated pattern related; patterns are discovered through
supporting profile observations, profile-derived targets/map implications, or
advisory patterns from `draft_profile_map_updates`.
When an already-applied staged source is found by the default applied-source
scan, `candidate.explicit` is still false; inspect the nested
`export.bundle_summary.recommended_applied_inspection_iris` or per-row
`next_action` to follow the applied event.
`profile_route_keys` names matched draft `route_group_key` values; each
`profile_route_groups[]` row has `route_group_key`, `review_lane`,
`route_step_keys`, `matched_by`, and `match_strength`. Strength values are
`direct_action`, `strong_support`, or `related_support`: direct means the staged
row appears to implement that draft lane, while strong/related support means it
shares profile observations, support patterns, or anchors with the lane. The
route keys can also come from profile route source metadata persisted on a staged
profile-map revision, or from generated query-planning repair review notes for
already-applied query repairs whose live blocker is gone.
Markdown export includes a `Profile Route Bridge` table in the review summary
when candidates match draft routes, and renders lane names with their strength.
The bridge includes the grouped bundle row number and candidate summary beside
the revision IRI so Markdown-only reviewers can move from a route lane to the
matching `Revision N` section without consulting the JSON payload.

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
`partition.redundant_partition_key` is a resource summary when present. When
recording it, pass the redundant partition column IRI/CURIE rather than the
literal placeholder token from the path template.

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
profile.observed_physical_type
profile.observed_value_type
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

### Query Context

`db.describe_query_context(table_iri)` returns a `QueryPlanningContext`:

```python
query.dataset
query.readiness
query.readiness_note
query.issues
query.analysis_warnings
query.suggested_repair_action_groups
query.suggested_repair_action_group_count
query.planning_notes
query.row_count_snapshot
query.profile_summary
query.layout_verification_status
query.layout_verification_note
query.columns
query.path_templates
query.query_target_decision
query.query_target_candidates
query.ready_candidate_indexes
query.unselected_ready_candidate_indexes
query.direct_clean_candidate_indexes
query.unselected_direct_clean_candidate_indexes
query.physical_layouts
query.storage_accesses
query.partition_schemes
query.caveats
query.upstream_caveats
query.suggested_next_actions
query.suggested_next_calls
```

`query.profile_summary` has the same shape as `dataset.profile_summary`.
Use it with `row_count_snapshot` when query planning depends on profiler output:
it exposes the evidence IRIs and `profile_run_candidates` behind the observed
row-count/profile handoff without requiring a separate `describe_dataset` call.
When candidates exist, `suggested_next_actions` includes a
`describe_profile_run` action first; when a query target candidate is available,
the draft-plan action is included after any profile-run inspection actions.
Additional `describe_profile_run` actions appear before the draft-plan action
when candidate row counts disagree, or when the selected snapshot-matching run
has `row_count_snapshot_basis` of `sample`, `unknown`, or `mixed`. In mixed
profile history, match the dataset-profile
`row_count` in candidate runs to `row_count_snapshot` before relying on a
profile-derived count, and check
`profile_summary.profile_run_candidates[].row_count_snapshot_basis` before
treating the matching count as full-scan evidence.
When `query.profile_summary.evidence_iris` is non-empty but
`profile_run_candidates` is empty, `suggested_next_actions` includes a bounded
singleton `describe_profile_run` action. That action has the normal
`SuggestedNextAction` fields plus `source_profile_evidence`:

```python
action.source_profile_evidence["evidence_iri"]
action.source_profile_evidence["profile_observation_count"]
action.source_profile_evidence["profile_observation_iris"]
action.source_profile_evidence["profile_summaries"]
action.source_profile_evidence["evidence_summary"]
action.source_profile_evidence["execution_status"]
action.source_profile_evidence["engine"]
action.source_profile_evidence["query_hash"]
action.source_profile_evidence["result_sources"]
action.source_profile_evidence["query_source_paths"]
action.source_profile_evidence["query_source_spans"]
action.source_profile_evidence["handoff_note"]
```

`readiness` is one of `ready_for_query_planning`, `needs_review`,
`insufficient_metadata`, `blocked_by_contradiction`, or
`not_applicable_non_tabular_asset`. It is about physical query-planning
metadata, not analytical safety. `readiness_note` says that explicitly and
points to analysis caveats when present. For non-table assets,
`query_target_candidates` is empty and `suggested_next_actions` points back to a
resource/context-slice handoff instead of query repair.

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
For caveat warnings, `warning.details` preserves the original caveat metadata:

```python
warning.details.scope
warning.details.caveat_iri
warning.details.caveat_label
warning.details.caveat_description
warning.details.caveat_impact
warning.details.caveat_severity_iri
warning.details.caveat_severity_label
```

Use these detail fields, especially `caveat_severity_iri`, when deciding
whether an otherwise plan-ready query should pause for semantic review. The
warning's own `severity` is still the query-planning issue level, not a full
copy of the caveat severity taxonomy.

`query.suggested_repair_action_groups` is a read-only top-level lane over
existing `issues[].details.repair_hint.actions[]`. It is meant for automation
that needs one place to find metadata repair templates without scanning every
issue detail. It is not folded into `suggested_next_actions` because repair
templates require review, often contain placeholders, and usually need caller
rationale before any mutation call. `suggested_repair_action_group_count` is the
number of groups returned.
`project_brief` uses `query_repair_review` only when this count is non-zero.
`query_context_review` means the query context still needs review, but no lifted
repair template currently exists. Its top-level task action points to
`describe_query_context`; the bounded dataset query summary may still keep a
review-gated `draft_query_plan` action for agents that need plan-specific scan,
runtime, and blocker fields after the context review.
Do not concatenate this lane into `suggested_next_actions` or call
`repair_group.actions[]` unchanged.

Each repair action group has:

```python
repair_group.group_name
repair_group.issue_index
repair_group.issue_code
repair_group.issue_severity
repair_group.issue_message
repair_group.issue_resource
repair_group.repair_hint_path
repair_group.repair_action_type
repair_group.requires_review
repair_group.repair_context
repair_group.choice_mode
repair_group.actions
repair_group.action_count
repair_group.action_status_counts
repair_group.pending_action_count
repair_group.skippable_action_count
repair_group.already_satisfied_action_count
repair_group.pending_required_extra_arguments
repair_group.pending_action_options
```

`group_name` is currently `query_repair_review`. `issue_index` points back into
`query.issues`, and `repair_hint_path` names the original nested source, for
example `issues[3].details.repair_hint`. `repair_context` copies the repair
hint without its `actions` array so scripts can inspect source/target metadata,
candidate reviewed values, and mismatch reasons. Jump back to
`query.issues[issue_index].details` for sibling issue details such as fixture
staleness hints.
`actions` preserves the original ordered repair action templates. Copy an
action's `arguments` or fill its `arguments_template`, add every
`required_extra_arguments` value such as `rationale`, replace fields named in
`placeholder_fields` / `reviewed_value_fields`, and review `condition` before
calling the named tool.
`choice_mode` is usually `review_all_applicable`; `choose_one` means the pending
actions are alternatives. For example, `missing_storage_access` lets the agent
either record a reviewed new storage access or stage a link to an existing
reviewed storage access. In choose-one groups, do not treat
`pending_required_extra_arguments` as one call's required fields; use
`pending_action_options[]` or the selected action's own
`required_extra_arguments`.
Use `pending_action_count` and `skippable_action_count` for first-pass routing:
an action with `action_status="already_satisfied"` and
`skip_when_already_satisfied=true` is counted as skippable, while pending
actions contribute their unique `required_extra_arguments` values to
`pending_required_extra_arguments`. `pending_action_options[]` repeats the
pending non-skippable actions' index, type, tool, label, required extra
arguments, placeholder fields, reviewed value fields, and available safety text
such as `reason`, `condition`, and `review_rationale_guidance` so scripts can
choose a branch without parsing every full action template. Use the selected
full action when you need `arguments`, `arguments_template`,
`rationale_template`, or protocol-specific guidance. Actions marked
`action_status="already_pending"` with `skip_when_already_pending=true` are
skippable too. Exact matching pending staged repairs can be anchored to the
dataset itself or to linked query resources such as storage accesses, physical
layouts, partition schemes, or columns; project-brief
`pending_staged_repair_iris` uses the same query-resource association. These
summaries do not remove the review requirement.
When a missing-storage group has visible storage candidates that are already
pending, `repair_context.already_pending_candidate_count`,
`repair_context.already_pending_storage_access_iris`, and
`repair_context.pending_staged_repair_iris` summarize them. The compact
`stage_existing_storage_access_link` pending option repeats those fields when it
remains pending because other candidate choices are still available.
When `missing_physical_layout` appears after storage is linked, its repair group
has `repair_action_type="record_physical_layout"` and a reviewed
`record_map_physical_layout` template. Its `repair_context.storage_protocol_iris`,
`repair_context.database_storage_present`, and `repair_context.file_format_guidance`
help pick a reviewed `file_format`; for database storage, use table-layout
formats such as `rc:PostgreSQLTable`, `rc:SQLiteTable`, or `rc:MySQLTable` when
the selected route is a database relation handoff.

Read `query.query_target_decision` before choosing from
`query_target_candidates`. It is a derived handoff hint, not a new graph fact.
`status` is one of `ready`, `context_blocked`, `candidate_needs_review`, or
`no_candidate`. `candidate_index` is a zero-based index into
`query_target_candidates` when a candidate was selected. `reason_codes` contains
the warning/error issue codes behind the decision; inspect the selected
candidate's full `review_reasons` and `direct_review_reasons` for messages and
info-only notes.
`suggested_next_actions` gives structured routing from the context inventory
into `draft_query_plan`. In a context-blocked but direct-clean candidate case,
it includes `candidate_index` and `allow_context_blocked_candidate=True` so a
script can draft the selected route while keeping the context issues visible.
When peer ready candidates or peer context-blocked direct-clean candidates
exist, `suggested_next_actions` also includes one explicit
`draft_query_plan(candidate_index=...)` action for each peer. Use those actions
instead of parsing peer indexes from prose or from
`storage_access_iri` ambiguity errors; they carry
`allow_context_blocked_candidate=True` when sibling candidate metadata is the
only broader blocker.
When `ambiguous_physical_layout` blocks the selected candidate,
`suggested_next_actions` also includes one `draft_query_plan` action per linked
layout signature with `candidate_index` and `physical_layout_iri`; it also emits
the same action shape for peer candidates whose only direct blocker is layout
ambiguity. Follow the candidate/layout pair you have reviewed before relying on
`scan.function`. When resolving that layout would leave a direct-clean selected
route and the remaining blockers are candidate metadata on sibling routes, the
layout-selection action also includes `allow_context_blocked_candidate=True` so
scripts can reach the next execution gate without an extra retry while
preserving context audit fields.
`ready_candidate_indexes` lists direct-ready candidates at the context stage;
`unselected_ready_candidate_indexes` is the same list excluding
`query_target_decision.candidate_index`. When it is non-empty, another ready
path or relation exists and the caller should inspect candidate cards before
treating the automatic index as intended. These indexes describe candidate-local
direct readiness, so they can be non-empty while top-level `readiness` is
`needs_review` because sibling candidate metadata still blocks the whole
context.
`direct_clean_candidate_indexes` lists candidates with no direct warning or
error even when the overall context is blocked by sibling metadata;
`unselected_direct_clean_candidate_indexes` excludes the selected decision
candidate. Use these lists when `ready_candidate_indexes` is empty but a
context-blocked route can be drafted with an explicit selector and
`allow_context_blocked_candidate=True`.
`suggested_next_calls` is the compatibility display-call list.

Each query target decision has:

```python
decision.status
decision.summary
decision.candidate_index
decision.candidate_path
decision.candidate_path_status
decision.direct_review_required
decision.selected_candidate_direct_clean
decision.reason_codes
```

`selected_candidate_direct_clean` is `true` when the selected candidate has no
direct warning or error of its own, even if `decision.status` is
`context_blocked` because sibling or broader context issues still require
review. Use it as the compact cue that the allowance route in
`suggested_next_actions` is selecting a direct-clean candidate deliberately.

`query.query_target_candidates` contains derived path/template planning cards
for callers that need a safer handoff than raw `path_templates` plus
`storage_accesses`. Each card preserves the template provenance
(`dataset`, `partition_scheme`, `storage_access`, or
`storage_access_location`), the relevant storage access metadata, a best-effort
`candidate_path`, a `composition` value such as `template_as_returned`,
`storage_root_joined`, `storage_root_as_candidate`, `bucket_prefix_joined`,
`key_prefix_joined`, database-specific values such as
`database_connection_and_relation`, `database_relation`, or
`database_connection_as_candidate`, or `unresolved`, and `review_reasons` copied
from physical query-planning issues that apply to the candidate. For
database-backed storage, `candidate_path` is the relation-like planning target
rather than a joined connection path; read `relation_identifier` and
`connection_reference` for the explicit database handoff. Only
storage-access-owned templates become database relation identifiers; dataset
or partition templates paired with database storage remain review-only
inventory and carry `database_relation_template_source_mismatch` instead of a
`relation_identifier`. The mismatch issue's `details.repair_hint` names the
source template, storage-access target, candidate relation value for review,
and ordered `stage_map_assertion_change` templates for adding the reviewed
relation identifier and optionally removing the misplaced source template. If
the storage access already has relation template(s), the remove action is
ordered first and the add action is marked already satisfied. Each add-template
action declares `required_extra_arguments=["object", "rationale"]` and
`placeholder_fields=["object"]`; replace `object` with the reviewed relation
identifier and add a reviewed rationale before calling
`stage_map_assertion_change`.
These cards do not resolve credentials, endpoint profiles, or executable SQL.
`review_reasons` may include
info-only notes; use `review_required` to tell whether any warning or error
requires review before executable use. `direct_review_reasons` excludes the
synthetic `query_context_has_other_blockers` warning, so use
`direct_review_required` to distinguish a candidate with its own blocker from a
candidate that only needs review because sibling metadata blocks the overall
context. Like `review_reasons`, `direct_review_reasons` can include info-only
notes that do not make `direct_review_required` true.
If the overall query context is blocked by other dataset metadata, a candidate
may include `query_context_has_other_blockers` even when its own storage access
looks clean. Protocol/location warnings such as
`s3_access_resolution_unrecorded` and `storage_protocol_location_mismatch` mean
the candidate path is only an orientation aid until storage access is clarified.
For `storage_protocol_location_mismatch`, read
`details.repair_hint.actions`: it gives reviewed `stage_map_assertion_change`
templates for protocol/root/bucket/prefix edits and, when applicable, exact
path-template add/remove repairs.
Complete path templates such as `s3://...` are checked against the declared
storage protocol and any recorded bucket/prefix; relative templates that repeat
the recorded key prefix are also review-only because the composed path would
duplicate that prefix.
When `template_source == "storage_access_location"`, no path template was
recorded and the storage root itself is the candidate location. Treat that as
executable only when `candidate.location_kind == "object"` and the root is known
to name the dataset object/location. When that exact object root appears beside
dataset or partition templates, template-appended candidates are review-only
with `storage_object_location_has_path_template`; use the
`storage_access_location` candidate for the exact object route. Database storage
is stricter: a root-only
database candidate is review-only with `database_relation_template_missing`
until a storage-access-owned template records the relation identifier. If
`location_kind` is absent or is `directory`, `prefix`, or `connection`, the
candidate is review-only and needs a path template before running a query.
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
candidate.location_kind
candidate.storage_root
candidate.endpoint_profile
candidate.bucket_name
candidate.key_prefix
candidate.candidate_path
candidate.relation_identifier
candidate.connection_reference
candidate.composition
candidate.candidate_path_status
candidate.requires_endpoint_profile
candidate.credential_reference
candidate.path_style_access
candidate.review_required
candidate.review_reasons
candidate.direct_review_required
candidate.direct_review_reasons
```

`candidate_path_status` is `ready` when the path is suitable as a planning
input after normal review, `orientation_only` when warnings/errors make it a
handoff clue rather than executable guidance, and `unresolved` when the graph
lacks enough storage-location metadata for an executable path. Read it together
with `query_target_decision.status` and `candidate.direct_review_required`.
A candidate can be `orientation_only` because sibling storage or partition hints
block the overall query context; when `direct_review_required` is false, the
selected candidate itself may be locally clean even though the context still
needs review.

Each issue or analysis warning has:

```python
issue.code
issue.domain
issue.severity
issue.message
issue.resource
issue.details
```

`domain` is `query_planning` for physical metadata readiness issues and
`analysis` for caveat-shaped interpretation warnings. Read it before reacting
to `severity`: an `error` in `query_planning` means executable query-planning
metadata is missing or contradicted, not that profile lore or graph validation
failed.
`details` is optional structured context for selected issue kinds. For example,
protocol/location mismatches include storage fields, mismatch reasons, and a
reviewed `repair_hint`, while `query_context_has_other_blockers` includes
excluded blocker counts, codes, and resource IRIs. `missing_storage_access`
includes `dataset_iri`,
`global_storage_access_count`, a `repair_hint`, and sometimes
`fixture_staleness_hint`. The repair hint offers reviewed action templates for
`record_map_storage_access(..., datasets=[...])` or a staged
`rc:hasStorageAccess` assertion to an existing access resource.
Missing-storage repair actions have stable `action_type` values:
`record_reviewed_storage_access` and `stage_existing_storage_access_link`.
When existing map storage accesses are present, the repair hint also carries
bounded `candidate_existing_storage_accesses` so agents can review likely link
targets before filling the staged assertion's `object`. In the
record-new-storage template, omit optional storage-owned `path_templates` when
the dataset or partition already carries the reviewed file/object path template;
duplicating it can create equivalent ready query candidates. Database relation
identifiers are the storage-owned exception. A fixture staleness hint means
known AIS or Polymarket fixture tables are present while the capsule has zero
`rc:StorageAccess` resources; use a fresh scratch fixture load before drawing
query-target conclusions.
When a direct-clean selected query target is context-blocked by a stale
partition scheme linked to the dataset, the blocking `layout_needs_verification`
issue can carry `details.repair_hint.action_type =
"remove_stale_partition_scheme_link"`. Its single reviewed action is a
`stage_map_assertion_change` template that removes
`<dataset> rc:partitionedBy <partition scheme>`, with `rationale` required
before calling the tool.
`database_relation_template_source_mismatch` includes the
template, template source, source resource IRI, storage access IRI, storage
protocol IRI, the allowed relation-template source list, and `repair_hint`.
The repair hint names the source template, target storage access, reviewed
relation placeholder, and ordered action templates; callers still supply a
`rationale` for each staged add/remove. If the storage access already carries
relation template(s), `candidate_relation_identifier` includes
`storage_access_relation_templates`, the remove action is ordered first, and
the add action is marked `action_status="already_satisfied"` so agents do not
stage a duplicate relation template. `already_on_storage_access` remains the
exact-value flag for whether the misplaced source template itself is already
on the storage access. Automation can also read
`skip_when_already_satisfied=True` on that add action.
`database_relation_template_missing` includes the affected storage access IRI,
storage protocol IRI, storage root, location kind, allowed relation-template
sources, and a `repair_hint` with a reviewed add-template action on the storage
access. The nested repair-hint shape is:

```python
repair_hint.action_type
repair_hint.choice_mode
repair_hint.candidate_existing_storage_accesses
repair_hint.candidate_existing_storage_access_count
repair_hint.candidate_existing_storage_access_total_count
repair_hint.candidate_existing_storage_accesses_truncated
repair_hint.candidate_existing_storage_accesses[].candidate_status
repair_hint.candidate_existing_storage_accesses[].pending_staged_repair_iris
repair_hint.already_pending_candidate_count
repair_hint.already_pending_storage_access_iris
repair_hint.pending_staged_repair_iris
repair_hint.source
repair_hint.target
repair_hint.candidate_relation_identifier
repair_hint.candidate_relation_identifier.value
repair_hint.candidate_relation_identifier.requires_review
repair_hint.candidate_relation_identifier.already_on_storage_access
repair_hint.candidate_relation_identifier.storage_access_relation_templates
repair_hint.candidate_relation_identifier.review_note
repair_hint.actions[].action_type
repair_hint.actions[].action_status
repair_hint.actions[].skip_when_already_satisfied
repair_hint.actions[].tool_name
repair_hint.actions[].mcp_tool_name
repair_hint.actions[].action_label
repair_hint.actions[].reason
repair_hint.actions[].required_extra_arguments
repair_hint.actions[].rationale_template
repair_hint.actions[].placeholder_fields
repair_hint.actions[].reviewed_value_fields
repair_hint.actions[].arguments_template
repair_hint.actions[].arguments
repair_hint.actions[].condition
```

Each missing-storage candidate includes a `storage_access` summary,
`storage_access_iri`, protocol/location fields, storage-owned path templates,
layout verification status, `match_reasons`, `dataset_token_matches`,
`generic_dataset_token_matches`, `dataset_partial_token_matches`,
`generic_dataset_partial_token_matches`, `linked_dataset_iris`,
`candidate_rank`, and a review-first note.
`match_reasons` can include `dataset_token_overlap`,
`dataset_token_partial_overlap`, `generic_dataset_token_overlap`,
`generic_dataset_token_partial_overlap`, or `linked_to_other_dataset`; these
affect ranking but remain review context, not permission to auto-link. Generic
token matches such as `data`, `parquet`, `snapshot`, or `trial` are weak review
evidence and are reported separately so they do not outrank project-specific
tokens by accumulation. `linked_to_other_dataset` is a caution even when token
overlap exists; review `linked_dataset_iris` before reusing that access.

Add actions use `arguments_template` with placeholders for reviewed values and
caller rationale; remove actions may use ready `arguments` plus the same
required `rationale` field. Storage protocol/location repair templates also
name `placeholder_fields` and `reviewed_value_fields`; database relation
add-template repairs do the same for `object` so generic repair scripts can
replace reviewed values without issue-specific field guessing.
Missing physical layout repair templates use the same fields for `file_format`,
`layout_verification_status`, and `layout_verification_note`.
`ambiguous_physical_layout` includes
the distinct file-format/compression signatures and linked layout IRIs; when it
is present, `draft_query_plan` leaves `scan.function` unset instead of guessing
from the first layout. After reviewing those layouts, pass
`physical_layout_iri` to `draft_query_plan` to select one for that draft; the
source context records the requested layout and the scan card reports the
selected layout. `physical_layout_path_extension_mismatch` means there is only
one linked layout, but a clear candidate path extension such as `.csv` conflicts
with that layout's file format such as `rc:Parquet`; keep the plan review-gated
until the path/template or physical layout is corrected.

Use `describe_query_context` when the task is physical query planning and you
need the storage/layout/path/caveat projection without the full relationship and
pattern handoff in `describe_dataset`.

### Draft Query Plan

`db.draft_query_plan(table_iri, engine="duckdb")` returns a non-executed
`DraftQueryPlan` over `describe_query_context`:

```python
plan.helper
plan.mode
plan.handoff_kind
plan.engine
plan.dataset
plan.source_context
plan.selected_candidate
plan.scan
plan.required_bindings
plan.binding_requirements
plan.binding_note
plan.storage_environment
plan.review_gate
plan.issues
plan.analysis_warnings
plan.caveats
plan.upstream_caveats
plan.planning_notes
```

The helper currently supports `engine="duckdb"` and drafts review context only:
it does not resolve endpoint profiles, credentials, object existence, or SQL
execution. `plan.handoff_kind` is a compact machine-readable route for the
selected draft. It is one of `no_query_target`, `metadata_review_required`,
`context_review_required`, `runtime_resolution_required`,
`database_relation_handoff`, `binding_values_required`, or
`execution_attempt_ready`. The field is derived from the selected candidate,
review gate, runtime-resolution state, scan shape, and binding requirements; it
is a shortcut for routing, not a replacement for reading the underlying fields.
`binding_values_required` appears when URI-template placeholders still need
caller-supplied runtime values; in that case
`review_gate.ready_for_execution_attempt` is false.
By default, `plan.selected_candidate` is the candidate named by
`query_target_decision.candidate_index`. Callers may override it with
`candidate_index` or `storage_access_iri`, and may select a reviewed layout
with `physical_layout_iri`; `source_context.query_target_decision` still
carries the automatic decision, while `selected_candidate_index`,
`candidate_count`, `ready_candidate_indexes`,
`unselected_ready_candidate_indexes`, `direct_clean_candidate_indexes`,
`unselected_direct_clean_candidate_indexes`, `selection_mode`, `requested_candidate_index`,
`requested_storage_access_iri`, `requested_physical_layout_iri`,
`selection_status`, `selection_note`, and `selected_candidate_note` /
`allow_context_blocked_candidate` describe the actual draft selection.
`selected_candidate_note` is a compact prose handoff for the selected route. In
context-blocked direct-clean cases it says which candidate was selected, what
route kind the draft produced, and which sibling/context blocker codes remain in
`review_gate.all_issue_codes`.

`plan.source_context` is the selection audit for the draft:

```python
source_context.api
source_context.readiness
source_context.readiness_note
source_context.query_target_decision
source_context.selected_candidate_index
source_context.candidate_count
source_context.ready_candidate_indexes
source_context.unselected_ready_candidate_indexes
source_context.direct_clean_candidate_indexes
source_context.unselected_direct_clean_candidate_indexes
source_context.selection_mode
source_context.requested_candidate_index
source_context.requested_storage_access_iri
source_context.requested_physical_layout_iri
source_context.selection_status
source_context.selection_note
source_context.selected_candidate_note
source_context.allow_context_blocked_candidate
```

`plan.scan` is the non-executed handoff card. Do not treat a relation or URI
field as execution permission without the review gate:

```python
scan.function
scan.uri_template
scan.relation_identifier
scan.connection_reference
scan.file_format
scan.compression
scan.candidate_path_status
scan.dataset_verification_status
scan.dataset_verification_note
scan.template
scan.template_source
scan.template_source_resource
scan.template_source_verification_status
scan.template_source_verification_note
scan.template_lineage
scan.composition
scan.physical_layout
scan.physical_layout_selection_note
scan.non_executed_note
scan.execution_attempt_ready
scan.primary_execution_attempt_blocking_reason_code
scan.execution_attempt_blocking_reason_codes
```

`plan.storage_environment` carries non-secret runtime orientation:

```python
storage_environment.storage_protocol
storage_environment.storage_root
storage_environment.bucket_name
storage_environment.key_prefix
storage_environment.region
storage_environment.endpoint_profile
storage_environment.credential_reference
storage_environment.access_mode
storage_environment.path_style_access
storage_environment.requires_endpoint_profile
storage_environment.runtime_resolution_required
storage_environment.duckdb_settings_from_context
storage_environment.runtime_resolution_note
```

If `unselected_ready_candidate_indexes` is non-empty, another direct-ready
candidate exists and agents should consider whether to rerun with explicit
`candidate_index`. The returned list order is not an authoring-preference
contract; `candidate_index` is a response-local pointer, so inspect the candidate
cards before treating one ready path or relation as intended.
If the source context is globally blocked, use
`unselected_direct_clean_candidate_indexes` to find peer candidates that lack
direct blockers but still need review-gated drafting.
`storage_access_iri` must identify exactly one query target candidate; when one
storage access has multiple candidate paths, the error includes compact
candidate snippets and callers should rerun with `candidate_index`. Prefer the
explicit candidate-index actions from `describe_query_context()` when available
so automation does not have to parse those snippets. If a
matching `physical_layout_iri` was also supplied, the error says the layout was
matched but the storage selector still spans multiple path/relation candidates.
`plan.scan` gives a best-effort scan
function such as `read_parquet`, a URI/path template for file/object storage,
file format, compression, and the selected candidate path status. For
database-backed storage, `scan.uri_template` is intentionally absent;
`scan.relation_identifier` and `scan.connection_reference` carry the graph's
relation/connection handoff for review rather than executable SQL and should
match the selected candidate's database fields. If a database candidate came
from a dataset or partition file path, `scan.relation_identifier` stays absent
and the selected candidate is review-gated with
`database_relation_template_source_mismatch`; record the relation on the
storage access before treating it as a database handoff. The scan card also
carries `physical_layout` and `physical_layout_selection_note`, plus the
dataset-level
`dataset_verification_status` / `dataset_verification_note`, and repeats path
lineage fields from the selected candidate: `template_source`,
`template_source_resource`, `template_source_verification_status`,
`template_source_verification_note`, and `template_lineage`. For dataset-owned
templates, the template-source verification fields mirror the dataset layout
verification fields; for partition/storage-owned templates they mirror that
source resource. When `template_source == "storage_access_location"`, no path
template exists and `template_lineage` describes the storage root candidate
instead. Read these before treating a surprising URI template or root as the
dataset's actual executable location; related or aggregate datasets can share a
partition template while still being review-gated.
`scan.execution_attempt_ready` mirrors
`review_gate.ready_for_execution_attempt`, and
`scan.primary_execution_attempt_blocking_reason_code` mirrors the first item in
`review_gate.execution_attempt_blocking_reason_codes`, or `None` when no blocker
remains. `scan.execution_attempt_blocking_reason_codes` mirrors
`review_gate.execution_attempt_blocking_reason_codes`; use these scan-adjacent
fields before treating `scan.uri_template` or `scan.relation_identifier` as
anything more than handoff context. `plan.required_bindings` is parsed from
`{placeholders}` in the selected path and remains as a compact compatibility
list. Prefer `plan.binding_requirements` for handoff work: each row has `name`,
`source`, `source_text`, `required`, `derivation_status`, `derivation_note`,
`binding_kind`, and optional partition hints:

```python
binding.name
binding.source
binding.source_text
binding.required
binding.derivation_status
binding.derivation_note
binding.binding_kind
binding.partition_scheme
binding.partition_column
binding.partition_granularity
binding.candidate_column_matches
binding.candidate_column_match_status
binding.candidate_column_matches[].column
binding.candidate_column_matches[].match_kind
binding.candidate_column_matches[].matched_field
binding.candidate_column_matches[].matched_value
binding.candidate_column_matches[].confidence
```

Path-template placeholders still report `derivation_status="not_inferred"`.
When the selected template comes from a partition scheme, `binding_kind` is
`partition_template_placeholder`, `partition_scheme` names that source, and
matching placeholders may carry `partition_column` and
`partition_granularity`. The granularity describes the partition scheme rather
than necessarily the individual placeholder. These fields are planning hints for
parameter handoff;
partition placeholders that do not match a declared partition column, and
ordinary dataset/storage placeholders, may carry `candidate_column_matches` when
a placeholder matches dataset column names, labels, or local IRIs exactly or by
suffix. These matches are best-effort handoff hints, not inferred runtime
binding values. `candidate_column_match_status` is `none`, `single`, or
`ambiguous` for hintable placeholders and `not_applicable` when a partition
column already matched the placeholder; ambiguous rows require review before
choosing any source column, even when individual matches have high confidence.
Match `confidence` describes one candidate row;
`candidate_column_match_status` summarizes the whole hint set.
`plan.storage_environment`
carries non-secret storage hints such as bucket, endpoint profile, credential
reference, path-style access, and DuckDB-shaped settings inferred directly from
graph metadata.
`plan.storage_environment.runtime_resolution_required` is true when endpoint or
credential references must be resolved, or when selected S3-compatible access is
review-gated because endpoint/credential/region metadata is not yet recorded.
`plan.review_gate` keeps the query-target decision status,
`blocking_reason_codes`, `execution_attempt_blocking_reason_codes`,
`primary_execution_attempt_blocking_reason_code`,
`all_issue_codes`, the legacy alias `reason_codes`,
`executable_without_review`, `runtime_resolution_required`,
`binding_values_required`, and
`ready_for_execution_attempt`. Treat the plan as review-required whenever
`executable_without_review` is false. The blocking codes are self-contained for
plan handoff: they may include decision reasons,
`query_context_has_other_blockers` when the selected candidate is clean but
sibling metadata blocks the overall context, or `scan_function_not_inferred`
when DuckDB has no file-scan function for the selected storage/layout shape.
They may also include `physical_layout_path_extension_mismatch` when the
candidate path extension conflicts with the single linked physical layout file
format.
After selecting `physical_layout_iri`, `status` may be `ready` while
`ready_for_execution_attempt` and `scan.execution_attempt_ready` remain false;
always route from the stricter execution-attempt fields before attempting a
scan. Runtime-only cases can have empty `blocking_reason_codes` and
`all_issue_codes`; `execution_attempt_blocking_reason_codes` still names
`runtime_resolution_required`.
`execution_attempt_blocking_reason_codes` starts with those review blockers and
also includes non-review execution-attempt blockers such as
`runtime_resolution_required` and `binding_values_required`, so downstream
automation does not have to merge booleans and review codes before routing a
false `ready_for_execution_attempt`.
`primary_execution_attempt_blocking_reason_code` is the first ordered blocker,
or `None` when the plan is ready for an execution attempt. The scan card repeats
the same values as
`scan.execution_attempt_ready` and
`scan.primary_execution_attempt_blocking_reason_code` /
`scan.execution_attempt_blocking_reason_codes` for consumers that start from the
URI, relation, or scan-function hints.
`review_gate.selection_overridden`, `context_blocked_candidate_allowed`,
`context_blocked_candidate_used`, `direct_blocking_reason_codes`, and
`context_blocking_reason_codes` explain whether an explicit or allowed
context-blocked selection changed the handoff gate. When
`allow_context_blocked_candidate=True` and the selected candidate has no direct
warning/error, sibling-only context blockers can be excluded from the selected
handoff while remaining visible in `issues`, the automatic decision, and
`context_blocking_reason_codes`.
For sibling candidate-metadata blockers, use an explicit `candidate_index` or
`storage_access_iri` with that allowance. A selectorless automatic draft may
still report `context_blocked_candidate_allowed=True`, but if
`context_blocked_candidate_used=False` the context gate remains active.
Interpret the two allowance booleans together: `allowed=false` / `used=false`
means no allowance was requested; `allowed=true` / `used=true` means the selected
candidate was made direct-clean by excluding sibling-only blockers;
`allowed=true` / `used=false` with no direct blocking codes usually means the
candidate was already ready or had no sibling-only blockers to exclude; and
`allowed=true` / `used=false` with direct blocking codes means direct candidate
issues still require review.
Database-backed storage currently uses this generic review-draft shape too;
expect `scan.function=None` and `scan_function_not_inferred` until a
database-query-specific plan mode exists. Those plans use
`handoff_kind="database_relation_handoff"` when the recorded relation is the
right thing to pass to a database-aware runtime rather than a file scan. A
dataset or partition path under database storage is not a recorded relation and
should stay `metadata_review_required`.
`executable_without_review=true` means DoxaBase found no recorded
physical-metadata blocker for the selected candidate. It is not a runtime
credential/object-existence guarantee.
`ready_for_execution_attempt` is the stricter handoff boolean: it is true only
when the review gate is clear, `runtime_resolution_required` is false, and
`binding_values_required` is false.
For consumer routing, check `ready_for_execution_attempt` first, or its scan
mirror `scan.execution_attempt_ready` when working inside the scan card. If the
gate is false
but `scan.relation_identifier` is present, hand it to a database-aware
review/runtime route before generic runtime-resolution work. A
`connection_reference` without a relation identifier is repair/review context,
not a database relation handoff. Then route
`primary_execution_attempt_blocking_reason_code` as the compact next blocker and
`execution_attempt_blocking_reason_codes` for the full ordered detail, followed
by unresolved storage environment, required bindings, and remaining issue codes.
Empty `blocking_reason_codes` or `executable_without_review=True` must not be
treated as execution permission.

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
`record_column_profile`. Pass `evidence_iri` when the pattern should reuse an
existing evidence resource, such as shared profile-run evidence. Use
`describe_pattern(pattern_iri)` when you need the evidence surface available to
readers.

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
`description.evidence` is a list of evidence resource summaries, even when the
pattern links to only one evidence resource. Treat it as plural and iterate over
the items rather than expecting a singular object.
`description.map_implications` contains resource summaries for map resources or
assertion nodes the pattern may affect; it is not a prose summary field. Use
`description.pattern_text` and `description.rationale` for explanation.

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
draft.result_kind
draft.summary
draft.intent
draft.anchors
draft.warnings
draft.structured_warnings
draft.framings
draft.staged_revisions
draft.next_action_queue
draft.next_action_queue_items
draft.next_action_queue_item_counts
draft.semantic_review_required_queue_counts
draft.suggested_next_actions
draft.suggested_next_calls
```

`result_kind` is `systematisation_draft`; `stage_pattern_promotion` returns the
same shape because it delegates to `stage_systematisation`. Use
`next_action_queue` for first-pass routing immediately after staging. It is
derived from the same apply-check summary logic as grouped staged-revision
exports, so validation-failed framings land in `repair_or_replace` while
mechanically ready framings land in `apply_after_review`.
`next_action_queue_items` mirrors the grouped export queue-item shape, including
`resolved_target_iri`, `resolved_target_record_kind`, `row_is_target`, status
fields, semantic-risk fields when populated, row-local alternative-gate fields,
and `alternative_set_iris` / `alternative_set_source_iri` /
`alternative_set_role` when sibling framings in the response compete. The suggested
actions normally include a grouped `export_staged_revisions` call plus
per-revision `check_staged_revision_apply` calls for fresh live routing. When
`first_alternative_anchor_not_ready` fires, the first suggested action is a
complete `stage_systematisation(..., link_alternatives=False)` rerun call so
automation can create a cleaner review bundle before exporting the anchored
draft. Suggested export paths include a readable revision slug and short hash to
reduce collisions across concurrent scratch runs; callers can still pass their
own run-specific path.

`draft.structured_warnings` is a machine-readable companion to selected prose
warnings. For example, when the first framing is not routed to
`apply_after_review` but later framings were linked to it as alternatives, the
draft includes:

```python
warning.warning_code
warning.message
warning.affected_revision_iris
warning.suggested_action
warning.suggested_rerun_arguments
warning.shared_patch_summaries
warning.fallback_revision_iris_with_shared_semantic_context
```

For that invalid-anchor case, `warning.warning_code` is
`first_alternative_anchor_not_ready` and
`warning.suggested_rerun_arguments == {"link_alternatives": False}`. The warning
only fires when a sibling actually default-linked to the first framing; use
per-framing `alternative_to` when ready siblings should point elsewhere. A
multi-framing draft with shared `ontology` or `shapes` patches also reports
`shared_semantic_context_applies_to_all_framings`; its suggested rerun arguments
name the shared graph roles and original `shared_additions` / `shared_removals`
source indexes that should move into per-framing patches if a fallback
alternative should avoid the provisional vocabulary or validation shape.
`shared_patch_summaries` gives the parsed target graph, operation, role, count
basis, format, and triple count; `fallback_revision_iris_with_shared_semantic_context`
is the affected fallback subset to inspect before rerunning. Use the structured
fields for automation; keep `warnings` for readable handoffs.

Each item in `draft.staged_revisions` is a `StagedGraphRevisionRecord` with:

```python
revision.revision_iri
revision.revision_type
revision.revision_stance
revision.summary
revision.rationale
revision.review_note
revision.review_recommendation
revision.graph
revision.triples
revision.changed_graphs
revision.patches
revision.validation_scope
revision.validation_conforms
revision.validation_result_count
revision.validation_results
revision.alternative_to
revision.restaged_from
revision.restage_reason
revision.current_restaged_by
```

Each `revision.patches[]` item has:

```python
patch.patch_iri
patch.operation
patch.target_graph
patch.count_basis
patch.format
patch.patch_role
patch.sequence_index
patch.triple_count
patch.before_triple_count
patch.after_triple_count
```

`db.list_graph_revisions(...)` returns `GraphRevisionList`:

```python
revisions.revisions
revisions.count
revisions.returned_count
revisions.total_count
revisions.limit
revisions.offset
revisions.revision_type
revisions.record_kind
revisions.application_status
revisions.staged_validation_status
revisions.stale_resolution_state
revisions.current_staged_work_only
revisions.returned_application_status_counts
revisions.returned_current_staged_work_application_status_counts
revisions.returned_stale_resolution_state_counts
revisions.returned_staged_validation_status_counts
revisions.next_action_queue
revisions.next_action_queue_items
revisions.next_action_queue_item_counts
revisions.semantic_review_required_queue_counts
revisions.include_apply_checks
revisions.drift_detail
```

Each item in `revisions.revisions` has:

```python
item.iri
item.record_kind
item.is_current_staged_work
item.not_current_staged_work_reason
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
item.staged_validation_status
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
item.snapshot_evidence
item.next_action
item.suggested_next_actions
item.suggested_next_calls
```

`is_current_staged_work` is true for patch-backed staged revisions that have not
already been applied and have not been superseded by a refreshed successor. Use
`current_staged_work_only=True` when a list should show the live mutation-review
queue instead of handled stale sources or applied history. The filter also
computes apply checks, so the returned rows include current application status
and suggested actions. `next_action` is a compact routing hint derived from
those fields; `next_action_queue` groups the returned rows by queues such as
`apply_after_review`, `restage_after_review`, `repair_or_replace`,
`inspect_already_applied`, `complete_handoff_import`, and `informational`.
`complete_handoff_import` means a row's snapshot evidence found an incomplete
RDF/snapshot handoff; follow the promoted `import_revision_snapshots` or
`import_trig` action before relying on exact applied diffs or stale drift
triples.
`next_action_queue_items` mirrors the same returned-row scope with one compact
row per routed item. It preserves the queued `row_iri`, adds
`resolved_target_iri`, `resolved_target_record_kind`, and `row_is_target`, and
carries row status, semantic-risk fields when available, and alternative-gate
fields. When returned rows include unresolved alternatives, the queue items also
carry `alternative_set_iris`, `alternative_set_source_iri`, and
`alternative_set_role` for every member, including the source row.
`next_action_queue_item_counts` counts those items by queue.
`semantic_review_required_queue_counts` counts queued rows whose alternative
gate still requires semantic review; it does not count ordinary semantic-risk
review cues. Grouped export bundle summaries also expose
`semantic_risk_queue_counts` for queued rows whose apply check reported
`semantic_risk_level` of `attention` or `high`.
Revision lists and recovery plans copy row-local semantic-risk fields onto queue
items when their apply checks have already computed that risk; grouped exports
also provide the aggregate count.
It is a routing surface, not a preference order for competing alternatives; use
row details such as `review_recommendation`, `alternative_to`, and
`current_alternative_to` when comparing alternative framings.
`count` and `total_count` are the filtered total before pagination;
`returned_count` is `len(revisions)` for the current page. Prefer
`returned_count` / `total_count` in generic pagination scripts and keep `count`
for compatibility with older DoxaBase-aware callers.
The `returned_*_counts` dictionaries summarize the returned page, matching
`next_action_queue`; raise `limit` or paginate when
`total_count > returned_count` and you need whole-result counts. Full pages can include handled historical rows
such as stale originals with `application_status="conflict"`.
`returned_current_staged_work_application_status_counts` is the same returned
page narrowed to rows where `is_current_staged_work=True`, which is useful when a
dashboard needs the live mutation queue without dropping the history rows.
When `is_current_staged_work` is false,
`not_current_staged_work_reason` explains why. Current reason values include
`already_applied_source`, `superseded_by_restage`, `applied_event_record`,
`export_record`, `import_record`, and `history_record`.

`application_*` fields are only populated when `include_apply_checks=True` and
the revision has staged patch payloads, except applied revision events report
`application_status="applied_event"` for scanning. `record_kind` is a compact row
class such as `staged_patch`, `applied_event`, `export_record`, `import_record`,
or `history_record`.

A minimal staged/applied scan looks like:

```python
revisions = db.list_graph_revisions(include_apply_checks=True)
for item in revisions.revisions:
    print(item.record_kind, item.application_status, item.iri)
```

For staged rows, expect `record_kind == "staged_patch"` and an apply-check
status such as `ready`, `conflict`, `noop`, `validation_failed`,
`superseded_by_restage`, or `already_applied`. For applied staged revision
events, expect
`record_kind == "applied_event"` and `application_status == "applied_event"`.

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
`item.snapshot_evidence` has the same shape as
`describe_revision_snapshot_evidence()` and lets list consumers see whether
exact snapshot rows are available before opening a detail view.
Stored `validation_conforms` and `validation_result_count` are staged-time
preview diagnostics. The `application_*` fields are a live apply check against
the current graph. A row can therefore have stored validation failures while
the live `application_status` is now `conflict` after graph drift; call
`describe_staged_revision()` when historical validation diagnostics matter.
List rows report validation status and result counts for routing, but omit full
`validation_results`; open a staged-revision detail or export when you need the
diagnostic rows.
Use `staged_validation_status="failed"` to filter for those stored staged-time
failures separately from live `application_status="validation_failed"`.
`drift_detail="summary"` is the default and omits exact changed-triple arrays
from list-row snapshot drift entries. Summary rows still include
`drift_relevance`, all overlap arrays, and added/removed exact-change counts
when exact drift is available. Use `drift_detail="exact"` or
`check_staged_revision_apply()` when the actual changed-triple arrays should be
included.

In list rows, relation fields such as `applied_by`,
`applies_staged_revision`, `alternative_to`, `current_alternative_to`,
`restaged_from`, `restaged_by`, and `current_restaged_by` are nullable IRI
strings. They are not nested resource objects.
`restaged_from` can come from the mechanical restage helpers or from a
caller-authored staged repair that used `restages_revision`; in both cases,
route follow-up work by `current_restaged_by` when the stale source has a
successor.

`db.describe_revision_lineage(revision_iri, include_apply_checks=True,
drift_detail="summary")` returns `RevisionLineageDescription`:

```python
lineage.selected_revision
lineage.selected_revision_iri
lineage.selected_role
lineage.paired_revision
lineage.paired_revision_iri
lineage.paired_role
lineage.applied_revision_iri
lineage.staged_revision_iri
lineage.applied_source_revision_iri
lineage.current_staged_revision_iri
lineage.current_revision_iri
lineage.latest_revision_iri
lineage.latest_role
lineage.restage_chain
lineage.restage_chain_iris
lineage.alternative_revision_iris
lineage.related_revision_iris
lineage.next_action
lineage.next_action_queue_item
lineage.suggested_next_actions
lineage.suggested_next_calls
lineage.warnings
lineage.include_apply_checks
lineage.drift_detail
```

`selected_revision`, `paired_revision`, and `restage_chain[]` are normal
`GraphRevisionListItem` rows. Use `selected_revision_iri` and
`paired_revision_iri` for first-pass routing when you do not need to inspect the
nested rows. `selected_role` / `paired_role` values include
`applied_event`, `applied_source`, `restaged_source`,
`current_staged_revision`, `staged_revision`, and other record kinds for
non-patch history. `restage_chain_iris` walks from the oldest visible source to
the latest visible successor for the selected proposal family. When a successor
has already been applied, `latest_revision_iri` points at the applied event and
`applied_source_revision_iri` names the staged successor that was actually
applied. Older stale-source lineages keep `staged_revision_iri` on the selected
source row for compatibility, so use `applied_source_revision_iri` when you need
the source patch for the applied event. `next_action` prefers the applied-event
inspection route; if that route came from a derived list-row action, lineage
also exposes it in `suggested_next_actions` / `suggested_next_calls` for simple
routers. When the applied source differs from the selected row, suggested
actions also include `describe_staged_revision(applied_source_revision_iri)`.
When a successor is still live staged work, `current_staged_revision_iri` and
`current_revision_iri` both name that current row. `related_revision_iris`
includes selected, paired, restage-chain, latest/current, alternative,
applied-event IRIs reachable from alternative staged rows, and every visible
restage successor for rows in the lineage when imported history contains
parallel successor links. It also includes applied events attached to those
visible parallel successor branches.
`next_action_queue_item` mirrors the list/export queue-item shape for the
selected lineage row and the lineage-level `next_action`. Use its
`resolved_target_iri`, `resolved_target_record_kind`, and `row_is_target` fields
when a stale selected row routes to a current successor or applied event.

`warnings` reports broken restage links and top-level snapshot handoff hazards.
It also warns when an applied event points to a missing staged source, when a
restage chain includes a non-staged history/import/export row, or when a source
has multiple visible restage successors and the current route follows one of
them. If a selected, paired, latest, or current row has
`snapshot_evidence.status == "history_only_count_digest"`, import companion
revision snapshot JSON before expecting exact applied diffs or stale drift
triples. If a row reports `snapshot_rows_without_history`, import the
project/history RDF bundle before using normal revision helpers.

Use this helper when the question starts with "what happened to this revision?"
and is not resource-specific. It is a compact lineage and routing card, not a
patch or diff payload. Use `describe_staged_revision()` for staged patch
content, `describe_applied_revision_diff()` for stored applied before/after
diffs, and `describe_resource_revision_lineage()` when the route should be
filtered through one resource.

`db.list_resource_revisions(resource_iri, include_patch_mentions=True,
include_apply_checks=True)` returns `ResourceRevisionList`:

```python
resource_revisions.resource
resource_revisions.revisions
resource_revisions.count
resource_revisions.returned_count
resource_revisions.total_count
resource_revisions.limit
resource_revisions.offset
resource_revisions.current_staged_work_only
resource_revisions.include_patch_mentions
resource_revisions.patch_mention_scan
resource_revisions.include_apply_checks
resource_revisions.drift_detail
resource_revisions.next_action_queue
```

The row collection is `revisions`, not `items`. `count` and `total_count` are
the filtered total before pagination; `returned_count` is the returned page
length. Each row then wraps the normal revision-list row under `revision`.
Use `current_staged_work_only=True` when the resource route should return only
live staged work before pagination. The filter auto-enables apply checks and
still depends on `include_patch_mentions=True` to discover unanchored patch-only
work.

Each `resource_revisions.revisions[]` item wraps a normal
`GraphRevisionListItem` under `revision` and adds resource-match context:

```python
item.revision
item.revision_iri
item.match_types
item.revision_anchor_match
item.patch_mention_match
item.applied_source_match
item.applied_source_revision_iri
item.patch_mentions
item.patch_mentions_incomplete
item.patch_mentions_unreadable_count
item.applied_source_patch_mentions
item.applied_source_patch_mentions_incomplete
item.applied_source_patch_mentions_unreadable_count
```

Use `item.revision_iri` for routing scripts; use `item.revision` when you need
the full graph-revision row.

`patch_mention_scan` summarizes whether patch payload scanning was complete
across all candidate revisions before pagination:

```python
resource_revisions.patch_mention_scan.status  # complete, incomplete, not_requested
resource_revisions.patch_mention_scan.unreadable_patch_count
resource_revisions.patch_mention_scan.unreadable_revision_count
resource_revisions.patch_mention_scan.omitted_match_risk
```

`match_types` values include `revision_anchor`, `patch_subject`,
`patch_predicate`, `patch_object`, `applied_source_revision_anchor`,
`applied_source_patch_subject`, `applied_source_patch_predicate`, and
`applied_source_patch_object`. Patch mention rows are compact summaries, not
patch content:

```python
mention.patch_iri
mention.target_graph
mention.operation
mention.operation_label
mention.patch_role
mention.patch_role_label
mention.sequence_index
mention.matched_term_roles
mention.matched_triples
mention.triple_count
```

When an incompleteness flag is true, one or more stored patch payloads were
missing or unparseable while scanning for exact resource mentions. If top-level
`omitted_match_risk` is true, unanchored patch-only matches may have been
filtered out because their patch payloads could not be read. Treat empty patch
mention arrays as "no readable matching mention found", not proof that the patch
did not touch the resource.
Top-level unreadable counts summarize the pre-pagination scan:
`unreadable_revision_count` counts distinct staged or source revisions whose
patch payloads could not be read, not the number of returned rows. The
`omitted_match_risk` flag is coarse; it means unreadable unanchored patch-only
matches may be absent from the filtered list, not that any returned row is known
to be incomplete.

Use this helper when the question is "what revisions touched this resource?"
It filters before pagination and matches exact expanded RDF terms in staged
patch payloads. Use `describe_staged_revision()` when the patch payload itself
is needed.

`db.describe_resource_revision_lineage(resource_iri, revision_iri,
include_applied_diff=True, include_triples=False, max_triples=100)` returns
`ResourceRevisionLineageDescription`:

```python
lineage.resource
lineage.selected_revision
lineage.selected_revision_iri
lineage.selected_role
lineage.paired_revision
lineage.paired_revision_iri
lineage.paired_role
lineage.applied_revision_iri
lineage.staged_revision_iri
lineage.current_staged_revision_iri
lineage.current_revision_iri
lineage.latest_revision_iri
lineage.latest_role
lineage.restage_chain_iris
lineage.alternative_revision_iris
lineage.related_revision_iris
lineage.warnings
lineage.patch_mention_scan
lineage.next_action
lineage.next_action_queue_item
lineage.suggested_next_actions
lineage.suggested_next_calls
lineage.applied_diff_status
lineage.applied_diff_note
lineage.applied_diff
```

`selected_revision` and `paired_revision` are `ResourceRevisionListItem` rows.
Use `selected_revision_iri` and `paired_revision_iri` for first-pass routing;
use the nested resource-revision rows when match types or patch mentions matter.
`selected_role` / `paired_role` values include `applied_event`,
`applied_source`, `restaged_source`, `current_staged_revision`,
`staged_revision`, and `history_record`. `latest_revision_iri` / `latest_role`
mirror graph lineage's latest family pointer, so a resource-first handoff can
see the applied event after a successor has been applied. When the selected row
is an old stale source whose restaged successor has already been applied,
`applied_revision_iri` and `applied_diff` follow that applied successor while
`staged_revision_iri` names the staged source that was actually applied.
`next_action_queue_item` names the selected row and exposes the resolved applied
or current target without requiring a separate resource list join.
`restage_chain_iris` preserves the original source route. `applied_diff_status`
is `available`, `unavailable`, `omitted`, or `not_applicable`. When present,
`applied_diff.graph_diffs[]` contains resource-filtered added/removed counts
and optional triple arrays:

```python
applied_diff.applied_revision_iri
applied_diff.staged_revision_iri
applied_diff.snapshot_evidence
applied_diff.source_snapshot_evidence
applied_diff.changed_graphs
applied_diff.include_triples
applied_diff.max_triples
applied_diff.graph_diffs

graph_diff.graph_role
graph_diff.count_basis
graph_diff.before_revision_iri
graph_diff.after_revision_iri
graph_diff.before_triple_count
graph_diff.after_triple_count
graph_diff.before_content_digest
graph_diff.after_content_digest
graph_diff.exact_changed_triples_available
graph_diff.exact_changed_triples_included
graph_diff.resource_triples_added_count
graph_diff.resource_triples_removed_count
graph_diff.resource_triples_added_truncated
graph_diff.resource_triples_removed_truncated
graph_diff.max_triples
graph_diff.resource_triples_added
graph_diff.resource_triples_removed
graph_diff.note
```

`graph_diff.count_basis` is `target_graph_only`: applied revision snapshot rows
store role-local graph counts. This can differ from staged patch preview counts
for `ontology` and `shapes`, which include immutable seed context.

This helper is a compact resource-centric lineage card, not full graph-version
browsing. It avoids requiring full staged patch payloads for imported applied
events; inspect `patch_mention_scan` and per-row incomplete flags before
treating empty patch mention arrays as absence.
RDF-only imports are enough for resource route and staged/applied pairing when
history metadata is present, but exact resource-level applied diffs require the
companion `export_revision_snapshots()` / `import_revision_snapshots()` JSON
bundle.
`current_revision_iri` is an alias for `current_staged_revision_iri` so
resource-lineage handoffs use the same current-row name as batch restage items.
It is only populated when the selected row or its latest restage successor is
still current staged work. Once a successor has been applied, the successor and
applied event remain discoverable through `related_revision_iris` instead of
being mislabeled as current staged work; the lineage `next_action` prefers
inspecting the applied event in that case.
`restage_chain_iris` and `alternative_revision_iris` mirror the graph-level
lineage helper for the selected revision, so resource-first callers can see
sibling alternatives without a second generic lineage call. `related_revision_iris`
merges the local resource staged/applied route with the generic lineage family.
`warnings` mirrors graph lineage integrity warnings, including imported oddities
such as non-staged rows in a restage chain, missing applied-source links,
parallel restage successors, and snapshot handoff gaps.

`db.describe_graph_revision(revision_iri)` returns `GraphRevisionDescription`:

```python
description.iri
description.graph
description.label
description.summary
description.record_kind
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
description.snapshot_evidence
description.supporting_observations
description.supporting_claims
description.supporting_patterns
description.revision_anchors
description.evidence
description.suggested_next_actions
description.suggested_next_calls
```

`record_kind` uses the same compact categories as list rows, for example
`staged_patch`, `applied_event`, `export_record`, `import_record`, and
`history_record`. For applied staged revision events, `applied_source` is a
compact source card with staged summary, stance, review note/recommendation,
restage links, staged validation headline, graph snapshots, patch counts, patch
metadata without content, and support-link counts. It is meant for quick
history scanning; call
`describe_staged_revision(description.applies_staged_revision)` for patch
content, full diagnostics, impacts, or judgement panels.
The `applied_source` relation fields are also nullable IRI strings.
Applied-event descriptions also suggest `describe_applied_revision_diff()` so
agents starting from history can jump directly to stored before/after snapshot
counts and exact changed triples.

`description.snapshot_evidence` has the same shape as
`describe_revision_snapshot_evidence()`:

```python
snapshot_evidence.revision_iri
snapshot_evidence.status
snapshot_evidence.history_revision_found
snapshot_evidence.rdf_snapshot_graph_roles
snapshot_evidence.stored_snapshot_graph_roles
snapshot_evidence.exact_snapshot_graph_roles
snapshot_evidence.missing_snapshot_row_graph_roles
snapshot_evidence.orphan_snapshot_row_graph_roles
snapshot_evidence.note
snapshot_evidence.suggested_next_actions
snapshot_evidence.suggested_next_calls
```

Status values are `history_missing`, `history_only_count_digest`,
`history_plus_snapshot_rows`, and `snapshot_rows_without_history`. A
workflow-only RDF import plus snapshot JSON can produce
`snapshot_rows_without_history`: snapshot rows exist, but normal revision
helpers still need the matching RDF history records. When snapshot evidence has
an import action, `describe_graph_revision()`, list rows, and lineage helpers
also promote it into top-level `suggested_next_actions`; list and lineage
`next_action` route to `complete_handoff_import`.

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
patch.count_basis
patch.patch_role
patch.patch_role_label
patch.sequence_index
patch.triple_count
patch.before_triple_count
patch.after_triple_count
```

`db.apply_staged_revision(staged_revision_iri)` returns
`AppliedStagedRevisionRecord`:

```python
applied.applied_revision_iri
applied.staged_revision_iri
applied.graph
applied.triples
applied.changed_graphs
applied.post_apply_recheck_revisions
applied.post_apply_recheck_revision_iris
applied.post_apply_recheck_is_partial_queue
applied.suggested_next_actions
applied.suggested_next_calls
applied.patches_applied
applied.triples_added
applied.triples_removed
applied.validation_scope
applied.validation_conforms
applied.validation_result_count
applied.validation_results
```

`post_apply_recheck_revision_iris` lists other current unapplied staged
revisions that share a changed graph or validation dependency with the applied
revision. `post_apply_recheck_is_partial_queue` is true because that list is an
affected-sibling subset, not the complete remaining staged frontier. The
top-level `suggested_next_actions` starts with
`plan_staged_revision_recovery(current_staged_work_only=True)` and then includes
affected-sibling row actions.
`post_apply_recheck_revisions` carries the same queue as compact rows:

```python
item.iri
item.changed_graphs
item.shared_changed_graphs
item.recheck_reasons
item.application_status
item.decision
item.routing_decision
item.blocking_reasons
item.next_action
item.suggested_next_actions
item.suggested_next_calls
```

The routing fields are computed immediately after the apply that created the
queue. Re-run `check_staged_revision_apply` before mutating if substantial time
has passed or another graph change has happened. `recheck_reasons` explains why
the row was included after this apply; values include
`shared_changed_graph:<graph>` and `validation_dependency_graph:<graph>`.
`shared_changed_graphs` is empty for dependency-only rechecks such as a project
shape change invalidating a map candidate. The list may include repair-only rows
such as patch conflicts or validation failures; route them through `decision`,
`blocking_reasons`, `next_action`, or the fresh apply check, not by the presence
of the recheck IRI alone.

`db.describe_applied_revision_diff(applied_revision_iri, include_triples=False,
max_triples=500)` returns `AppliedRevisionDiffDescription`:

```python
diff.applied_revision_iri
diff.staged_revision_iri
diff.snapshot_evidence
diff.source_snapshot_evidence
diff.changed_graphs
diff.include_triples
diff.max_triples
diff.graph_diffs
```

Each `diff.graph_diffs[]` row is an
`AppliedRevisionGraphSnapshotDiff`:

```python
graph_diff.graph_role
graph_diff.count_basis
graph_diff.before_revision_iri
graph_diff.after_revision_iri
graph_diff.before_triple_count
graph_diff.after_triple_count
graph_diff.before_content_digest
graph_diff.after_content_digest
graph_diff.exact_changed_triples_available
graph_diff.exact_changed_triples_included
graph_diff.triples_added_count
graph_diff.triples_removed_count
graph_diff.triples_added_truncated
graph_diff.triples_removed_truncated
graph_diff.max_triples
graph_diff.triples_added
graph_diff.triples_removed
graph_diff.note
```

`graph_diff.count_basis` is `target_graph_only`: applied revision snapshot rows
store role-local graph counts. This can differ from staged patch preview counts
for `ontology` and `shapes`, which include immutable seed context.

This helper only works for applied staged revision events. It compares the
staged source's stored before-snapshot rows with the applied event's stored
after-snapshot rows for changed graphs. `snapshot_evidence` describes the
applied event's after-snapshot recovery state; `source_snapshot_evidence`
describes the staged source's before-snapshot recovery state. Read their
`suggested_next_actions` before parsing graph-diff notes when exact rows are
missing. The default response keeps exact
added/removed counts but omits changed-triple arrays. Pass
`include_triples=True` when an agent needs raw triples; `max_triples` caps each
added/removed array and truncation flags say whether arrays were shortened.
Use `describe_staged_revision()` when you need original patch payloads,
validation diagnostics, impacts, or judgement context.

`db.describe_revision_graph_snapshot(revision_iri, graph_role,
include_triples=False, max_triples=500)` returns
`RevisionGraphSnapshotDescription`:

```python
snapshot.revision_iri
snapshot.graph_role
snapshot.snapshot_evidence
snapshot.triple_count
snapshot.content_digest
snapshot.count_basis
snapshot.stored_at
snapshot.exact_snapshot_available
snapshot.include_triples
snapshot.triples_included
snapshot.triples_truncated
snapshot.max_triples
snapshot.triples
snapshot.note
```

Use it for one full stored snapshot role, for example the staged source before
IRI or applied event after IRI discovered from
`describe_applied_revision_diff()`. `count_basis` is
`stored_snapshot_rows`, `rdf_history_graph_snapshot`, or `unavailable`. When
only RDF history metadata exists, exact triples are not included even if
`include_triples=True`; import the companion snapshot JSON bundle first.

`db.describe_revision_snapshot_evidence(revision_iri)` returns
`RevisionSnapshotEvidenceStatus`:

```python
snapshot_evidence.revision_iri
snapshot_evidence.status
snapshot_evidence.history_revision_found
snapshot_evidence.rdf_snapshot_graph_roles
snapshot_evidence.stored_snapshot_graph_roles
snapshot_evidence.exact_snapshot_graph_roles
snapshot_evidence.missing_snapshot_row_graph_roles
snapshot_evidence.orphan_snapshot_row_graph_roles
snapshot_evidence.note
snapshot_evidence.suggested_next_actions
snapshot_evidence.suggested_next_calls
```

Status values are `history_missing`, `history_only_count_digest`,
`history_plus_snapshot_rows`, and `snapshot_rows_without_history`. Use it after
RDF and snapshot JSON imports to decide whether exact applied diffs or stale
drift triples can be reconstructed. Snapshot rows without matching RDF history
records are orphan review artifacts; import a project/history RDF bundle before
using normal revision helpers. When exact rows are missing, suggested actions
point at `import_revision_snapshots`; when snapshot rows are orphaned, they
point at `import_trig` for the project/history RDF bundle. Import actions use
placeholder paths and include `path_is_placeholder=True`; substitute the real
handoff artifact path before executing them. Revision list/detail/lineage
responses promote these actions to their top-level `suggested_next_actions`, and
list/lineage `next_action` uses queue `complete_handoff_import`.

`db.export_graph(...)` and `db.export_trig(...)` return `GraphExportRecord`:

```python
export.path
export.format
export.graphs
export.graph_counts
export.triples
export.bytes_written
export.sensitive_literal_count
export.privacy_warnings
```

`sensitive_literal_count` and `privacy_warnings` come from a conservative
credential-like scan over selected subject URI, predicate URI, object URI, and
literal graph terms. They warn before sharing; they do not redact the exported
RDF. Pass `fail_on_sensitive=True` to block before creating or overwriting an
RDF export when the selected graph roles scan dirty. Call
`scan_sensitive_literals(graphs=...)`
for redacted match rows with `term_position` and `term_kind`; sensitive-looking
context fields in those rows are redacted too. These fields are not a
path/shareability hygiene signal: non-secret local paths, object-store URIs,
endpoint URLs, and relative paths remain in faithful exports unless the caller
keeps them out of the graph or replaces them before export.

`db.export_revision_snapshots(path, revision_iris=None, graph_roles=None, fail_on_sensitive=False)`
returns `RevisionSnapshotBundleExportRecord`:

```python
bundle.path
bundle.format
bundle.revision_iris
bundle.graph_roles
bundle.snapshot_count
bundle.quad_count
bundle.bytes_written
bundle.sensitive_literal_count
bundle.privacy_warnings
```

The JSON bundle is an opt-in companion to RDF exports. It preserves
SQLite-side snapshot rows used for exact applied diff and stale drift
inspection; it is not an RDF graph export. If `revision_iris` contains an
applied staged-revision event, export also includes that event's staged source
revision snapshots so applied diff reconstruction has both sides. It may
include historical triples that are no longer present in current graph roles.
Snapshot exports are faithful JSON, not redacted output. The warning fields come
from a conservative scan of stored snapshot quad subjects, predicates, and
object terms, and `fail_on_sensitive=True` blocks before creating or overwriting
the JSON file when potential sensitive graph terms are found.

`db.export_handoff_bundle(trig_path, revision_snapshot_path, ...)` returns
`HandoffBundleExportRecord`:

```python
handoff.trig
handoff.revision_snapshots
handoff.paths
handoff.manifest
handoff.graph_roles
handoff.snapshot_graph_roles
handoff.revision_iris
handoff.manifest_path
handoff.manifest_bytes_written
handoff.sensitive_literal_count
handoff.privacy_warnings
```

The nested `trig` and `revision_snapshots` fields have the same shapes as
`GraphExportRecord` and `RevisionSnapshotBundleExportRecord`. The helper writes
the project/history RDF handoff and snapshot JSON companion as a pair. It checks
both output paths and combined privacy warnings before either artifact is
created, so `fail_on_sensitive=True` or an existing path cannot leave a normal
partial two-file handoff. The `manifest` field is always returned; when
`manifest_path` is supplied, the same payload is written as
`doxabase.handoff_bundle.v1` JSON. The manifest pairs artifact paths, records
graph roles, revision IRIs, snapshot graph roles, redacted privacy warnings, and
the recommended receiver sequence: `import_trig` should yield
`history_only_count_digest`, then `import_revision_snapshots` should yield
`history_plus_snapshot_rows`.

`db.import_revision_snapshots(path, replace=False)` returns
`RevisionSnapshotBundleImportRecord`:

```python
bundle.path
bundle.format
bundle.replace
bundle.revision_iris
bundle.graph_roles
bundle.snapshot_count
bundle.imported_snapshot_count
bundle.skipped_snapshot_count
bundle.quad_count
bundle.imported_quad_count
bundle.post_import_snapshot_evidence
```

Import RDF project/history graphs first, then import the snapshot bundle.
Existing snapshot pairs are skipped unless `replace=True`.
`post_import_snapshot_evidence[]` has the same shape as
`describe_revision_snapshot_evidence()` for each imported bundle revision IRI.
If snapshot JSON was imported before history RDF, rows report
`status="snapshot_rows_without_history"` and include an `import_trig` suggested
action.

### Staged Detail And Current Apply Summary

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
description.current_apply_check
description.judgement_panel
description.stored_review_context
```

Use `revision_stance`, not `stance`.

On `StagedGraphRevisionDescription`, relation fields such as
`alternative_to`, `restaged_from`, `restaged_by`, `current_restaged_by`, and
`applied_by` are `ResourceSummary` objects when present. This differs from
revision list rows and grouped export summaries, where the same relation names
are IRI strings for script-friendly routing.

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

`description.current_apply_check` is `None` by default. Pass
`include_current_apply_check=True` to `describe_staged_revision()` when a
single-revision review needs the live apply branch beside the patch payload.
The nested `StagedRevisionApplySummary` is compact:

```python
current.staged_revision_iri
current.status
current.decision
current.routing_decision
current.can_apply
current.summary
current.review_recommended
current.semantic_risk_level
current.semantic_risk_reasons
current.blocking_reasons
current.recommended_resolution
current.already_applied_by
current.restaged_by
current.current_restaged_by
current.stale_resolution_state
current.alternative_gate
current.changed_graphs
current.validation_scope
current.validation_conforms
current.validation_skipped_reason
current.validation_result_count
current.patches_checked
current.triples_to_add
current.triples_to_remove
current.count_drifts
current.snapshot_drifts
current.next_action
current.suggested_next_actions
current.suggested_next_calls
current.error
```

`current.snapshot_drifts` uses summary drift rows: counts, digests, relevance,
and overlap arrays are present, but exact changed-triple arrays are omitted.
`current.next_action` is the compact queue route for the live apply branch and
matches the `RevisionNextAction` shape used by direct apply checks, revision
lists, grouped exports, and post-apply recheck rows. A mechanically ready row
whose `alternative_gate.semantic_review_required` is true can still use the
`apply_after_review` queue, but its compact action label and suggested actions
name the semantic gate; the apply suggestion says `Apply only after semantic
review` and names the already-applied source when known. On list and bundle
responses, `semantic_review_required_queue_counts` and
`next_action_queue_items[].alternative_semantic_review_required` make the same
gate visible without opening the full row.
For grouped export bundles, use `bundle_summary.semantic_risk_queue_counts`
when ordinary linked-support or judgement-panel risk also needs a
machine-readable queue aggregate; grouped export queue items also copy
`semantic_risk_level` and `semantic_risk_reasons` from the row summary.
Call `check_staged_revision_apply()` when you need full `patch_checks`,
`conflicts`, `validation_results`, or exact snapshot drift triples.

`description.judgement_panel` is present for simple single-assertion `map`
staged changes that still replay cleanly against current graph state. It has
the same shape as `change.judgement_panel` from
`stage_map_assertion_change`. It is `None` for complex revisions, stale staged
patches, already-applied staged revisions, or changes that cannot be reduced to
one subject/predicate assertion.
When `judgement_panel` is `None`, `description.stored_review_context` may still
summarize persisted review/support metadata. It is not a replayed judgement
panel. Its fields are:

```python
stored.source_fields
stored.semantic_risk_level
stored.semantic_risk_reasons
stored.review_recommendation
stored.review_note_signals.has_value_type_context
stored.review_note_signals.has_current_value_rationale
stored.review_note_signals.has_caveat_context
stored.review_note_signals.has_related_routes
stored.review_note_signals.has_user_review_note
stored.linked_support_counts.observations
stored.linked_support_counts.claims
stored.linked_support_counts.patterns
stored.linked_support_counts.evidence
stored.linked_support_counts.revision_anchors
stored.attention_impacts
```

Each patch in `description.patches` is a `GraphPatchDescription`:

```python
patch.iri
patch.operation
patch.operation_label
patch.target_graph
patch.count_basis
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

### Apply Check, Patch Checks, And Snapshot Drift

`db.check_staged_revision_apply(revision_iri)` returns a
`StagedRevisionApplyCheck`:

```python
check.staged_revision_iri
check.revision_iri
check.can_apply
check.status
check.decision
check.routing_decision
check.summary
check.review_recommended
check.semantic_risk_level
check.semantic_risk_reasons
check.blocking_reasons
check.recommended_resolution
check.already_applied_by
check.restaged_by
check.current_restaged_by
check.stale_resolution_state
check.alternative_gate
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
check.next_action
check.suggested_next_actions
check.suggested_next_calls
```

`revision_iri` is an alias of `staged_revision_iri` so copied check payloads
carry the checked resource under the same name used by list and export rows.
Use `check.status` on the direct apply-check object. Revision list rows, grouped
export summaries, and compact nested description rows use `application_status`
for the live or summarized apply-check status.
Each `check.patch_checks[]` row summarizes one staged patch replay:

```python
patch_check.patch_iri
patch_check.target_graph
patch_check.count_basis
patch_check.operation
patch_check.operation_label
patch_check.patch_role
patch_check.patch_role_label
patch_check.triple_count
patch_check.before_triple_count
patch_check.current_triple_count
patch_check.after_triple_count
patch_check.preview_triple_count
patch_check.effective_triples_to_add
patch_check.effective_triples_to_remove
patch_check.already_present_triples
patch_check.already_absent_triples
patch_check.can_apply
patch_check.conflict
```

Each `check.snapshot_drifts[]` row compares a stored graph snapshot with current
state:

```python
snapshot_drift.graph_role
snapshot_drift.snapshot_triple_count
snapshot_drift.current_triple_count
snapshot_drift.snapshot_content_digest
snapshot_drift.current_content_digest
snapshot_drift.exact_changed_triples_available
snapshot_drift.exact_changed_triples_included
snapshot_drift.triples_added_since_snapshot_count
snapshot_drift.triples_removed_since_snapshot_count
snapshot_drift.drift_relevance
snapshot_drift.patch_overlap_subjects
snapshot_drift.patch_overlap_predicates
snapshot_drift.patch_overlap_objects
snapshot_drift.revision_anchor_overlap
snapshot_drift.triples_added_since_snapshot
snapshot_drift.triples_removed_since_snapshot
snapshot_drift.note
```

`restaged_by`, `current_restaged_by`, and `stale_resolution_state` mirror the
revision-list/export routing fields on direct apply checks. A handled stale
source reports the direct successor in `restaged_by`, the latest known successor
in `current_restaged_by`, and routes compact `next_action` to inspect that
successor instead of another mechanical restage. If the latest successor has
already been applied, `current_restaged_by` still names the staged successor but
`next_action.arguments["iri"]` and the first suggested actions point to the
applied event. Its `status` may still be `conflict` for historical graph-state
drift or `validation_failed` for old failed validation diagnostics, but the
`summary` headline starts with handled-by-restage wording and names the
successor or applied event. Suggested actions inspect the successor or applied
event first and may include an `export_staged_revision` diagnostic bundle for
the handled failed source.
`alternative_gate` is the row-local alternative semantic gate. Its `status` is
`not_applicable`, `alternative_to_unapplied_source`, or
`alternative_to_applied_source`; the last status sets
`semantic_review_required=True` and carries `applied_source_iri` /
`applied_revision_iri`. Treat that as a semantic review gate even when
`status="ready"` and `next_action.queue="apply_after_review"`: mechanical
readiness is not approval to make both alternatives durable.

Read `status`, `summary`, and `semantic_risk_level` first. Current statuses are
`ready`, `noop`, `already_applied`, `superseded_by_restage`, `conflict`,
`validation_failed`, and `not_ready`. `decision` is the stable branch hint, for example
`review_then_apply`, `inspect_no_effective_change`,
`inspect_applied_revision`, `inspect_current_successor`,
`restage_against_current_graph`, `inspect_patch_conflict`, or
`inspect_validation_results`. A mechanically ready same-payload restaged
successor whose source failed staged-time validation uses
`inspect_restaged_source_validation_failure`; inspect/export it and stage a
repaired or alternative candidate before applying. A revised conforming
successor can use `review_then_apply` while still carrying the source-failure
warning.
`routing_decision` is the effective automation route derived from
`next_action`: it can be more specific than `decision` for stale conflicts, for
example `stage_same_slot_replacement`, `inspect_no_effective_change`, or
`restage_after_review`. Prefer `routing_decision` and `next_action` for the next
tool call; keep `decision` as the replay/status explanation.
`review_recommended=True` means the caller should
review the staged revision before the next mutation or replacement. For `ready` checks that
means review before applying; for count/digest-drift `conflict` checks it means
review before restaging; for `patch_conflict` checks it means inspect/export
before staging a repaired or alternative candidate. `noop` means replay
validates but would not change graph triples; inspect or replace it instead of
applying. `blocking_reasons` uses compact values such as `target_count_drift`,
`target_digest_drift`, `patch_conflict`, `validation_failed`,
`no_effective_patch_triples`, `superseded_by_restage`, or `already_applied`.
`next_action` is the compact queue route for the checked revision, using the
same `RevisionNextAction` shape as list/export rows. Prefer it for automation
after reading the full check: ordinary ready rows route to `apply_after_review`,
stale count/digest drift routes to `restage_after_review`, validation and patch
conflicts route to `repair_or_replace`, and already-applied rows route to
`inspect_already_applied`. A ready restaged successor with
`decision == "inspect_restaged_source_validation_failure"` also routes to
`repair_or_replace`, because current graph state may have supplied semantics
that the original same-payload framing omitted. A caller-authored successor with
a revised conforming patch payload keeps the source validation warning in
semantic-risk and review text, but can route to `apply_after_review`. Rows with
failed staged-time validation and no successor also route to `repair_or_replace`
even if later graph drift makes the live apply check report `conflict`. No-op
and superseded-by-restage rows usually route to informational inspection queues.
When `validation_conforms is None`, read
`validation_skipped_reason` before guessing
why validation did not run; common values are `conflicts_present` and
`already_applied`.
`next_action.tool_name` names the compact route target and can be mutating for
ready or stale rows; review-first scripts should execute
`suggested_next_actions` in order instead of blindly calling `next_action`.
For `patch_conflict`, inspect `patch_checks[].conflict` before mutating; it
means the stored patch cannot currently be replayed, not merely that the target
graph count or digest drifted. Suggested actions for `patch_conflict` omit
`restage_staged_revision`.
For `validation_failed`, inspect `validation_results` before staging a repair;
unhandled rows also suggest `draft_staged_revision_rebase` as a read-only repair
plan before any mutation.
If `apply_staged_revision()` raises this status, the exception includes the
staged revision IRI and an exact `describe_staged_revision(...,
include_current_apply_check=True)` call.
If the failure appears after restaging overlapping single-assertion proposals,
do not restage the same patch again; use a removal+addition patch or
`stage_map_assertion_change` replacement to make the intended replacement
explicit.
`triples_to_add` and `triples_to_remove` are effective graph deltas for the
current preview, not raw patch payload sizes. Each `patch_checks[]` row carries
`count_basis`, `effective_triples_to_add`, `effective_triples_to_remove`,
`already_present_triples`, and `already_absent_triples` so agents can see
partial or no-op replay before applying. `count_basis` is usually
`target_graph_only`; ontology and shape previews report
`target_graph_plus_base_ontology` or `target_graph_plus_base_shapes` because
their staged preview counts include immutable seed context.
`count_drifts` gives patch-level count drift context: target graph, patch
sequence, expected-before count, current count, delta, and whether exact changed
triples are available. `expected_before_basis` explains whether the expected
count is the original staged graph snapshot before patch 1 or the staged replay
point before a later patch. It also reports `patch_operation`, `patch_triples_checked`,
`patch_triples_currently_present`, `patch_triples_currently_absent`, and
`patch_triple_status` (`all_patch_triples_absent`,
`all_patch_triples_present`, or `mixed_patch_triples_present`). In the current
runtime, DoxaBase can inspect the staged patch triples themselves; when stored
snapshot rows exist, exact target graph additions and removals are available in
`snapshot_drifts`.
Each `count_drifts[]` row uses these exact field names:

```python
drift.patch_iri
drift.patch_sequence_index
drift.target_graph
drift.count_basis
drift.expected_before_triple_count
drift.expected_before_basis
drift.current_triple_count
drift.delta
drift.exact_changed_triples_available
drift.patch_operation
drift.patch_operation_label
drift.patch_triples_checked
drift.patch_triples_currently_present
drift.patch_triples_currently_absent
drift.patch_triple_status
drift.note
```

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
`broad_patch_object_overlap`, `patch_object_and_anchor_overlap`,
`revision_anchor_overlap`, `unknown_no_exact_diff`, and
`unknown_no_patch_terms`. Predicate and object overlap can be broad, for example
`rdf:type`, `rc:Dataset`, or `rc:Table`; `broad_patch_object_overlap` marks the weak case
where the only patch-object overlap is broad vocabulary such as shared
class/type terms. Anchor overlap means drift touched one of the staged
revision's review anchors even if the staged patch subjects were untouched. A digest
mismatch means the target graph state is not identical to the state at staging
time, even when triple counts still match. Older revisions can report
`exact_changed_triples_available=False` when they predate snapshot row storage.
Revision-list summary mode may report `exact_changed_triples_available=True`
and `exact_changed_triples_included=False`; that means exact triples exist but
were intentionally omitted from the list response. The added/removed count
fields still report how many exact triples were omitted when those counts are
known.
Stale drift rows use `triples_added_since_snapshot_count` and
`triples_removed_since_snapshot_count`. Applied revision diffs use
`triples_added_count` and `triples_removed_count`; they compare the staged
source's stored before snapshot with the applied event's stored after snapshot.
Each changed-triple item carries exact raw RDF fields (`subject`, `subject_kind`,
`predicate`, `object`, `object_kind`, `datatype`, `lang`) plus scan-friendly
fields (`subject_curie`, `subject_display`, `predicate_curie`,
`predicate_display`, `object_curie`, `object_display`). Use the raw fields for
precise graph work and the display fields for human review.
`suggested_next_actions` uses the same structured action shape as assertion
support: action label, tool name, MCP tool name, arguments, reason, and display
call string.
For staged apply checks, actions are ordered review-first; mutating actions such
as `apply_staged_revision` and `restage_staged_revision` come after inspection
or export suggestions.
`can_apply=True` means the patch replays and validates mechanically; it is not
semantic approval. If `semantic_risk_level` is `attention` or `high`, inspect the
judgement panel, impacts, and supporting lore before applying; the apply action
label says `Apply only after semantic review` in that case. Conflict review
actions include `include_current_apply_check=True` so the next inspection reloads
the current blocked status.

### Staged Revision Recovery Plan

`db.plan_staged_revision_recovery(...)` returns a
`StagedRevisionRecoveryPlan`:

```python
plan.result_kind
plan.helper
plan.mode
plan.selection_mode
plan.requested_revision_iris
plan.processed_revision_iris
plan.current_staged_work_only
plan.include_drafts
plan.validation_scope
plan.drift_detail
plan.limit
plan.offset
plan.count
plan.returned_count
plan.total_count
plan.lanes
plan.lane_counts
plan.next_action_queue
plan.next_action_queue_items
plan.next_action_queue_item_counts
plan.resolved_target_groups
plan.resolved_target_group_counts
plan.mutation_frontier_iris
plan.requires_recheck_after_each_apply
plan.semantic_review_required_queue_counts
plan.would_restage_revision_iris
plan.repair_first_revision_iris
plan.repair_or_replace_source_revision_iris
plan.not_restageable_revision_iris_by_reason
plan.current_revision_by_source
plan.review_revision_iris
plan.recommended_review_iris
plan.recommended_mutation_review_iris
plan.recommended_apply_or_restage_review_iris
plan.recommended_repair_review_iris
plan.recommended_applied_inspection_iris
plan.sequential_apply_recheck_candidate_iris
plan.revision_summaries
plan.bundle_summary
plan.suggested_next_actions
plan.suggested_next_calls
plan.warnings
plan.note
```

`mode` is `read_only_plan`: the helper does not stage, restage, apply, export,
or write files. With no explicit `revision_iris`, `selection_mode` is
`current_staged_work` by default and the helper plans over the bounded current
staged queue. With explicit `revision_iris`, it preserves first-seen order after
`limit` and `offset`.

Each `plan.lanes[]` row is a `StagedRevisionRecoveryLane`:

```python
lane.row_iri
lane.source_revision_iri
lane.current_revision_iri
lane.resolved_target_iri
lane.resolved_target_record_kind
lane.row_is_target
lane.lane
lane.action_type
lane.action_label
lane.batch_action
lane.not_restageable_reason
lane.summary
lane.changed_graphs
lane.status_before
lane.decision_before
lane.routing_decision_before
lane.stale_resolution_state_before
lane.blocking_reasons_before
lane.status_after
lane.decision_after
lane.routing_decision_after
lane.stale_resolution_state_after
lane.blocking_reasons_after
lane.source_staged_validation_status
lane.source_validation_result_count
lane.current_staged_validation_status
lane.current_validation_result_count
lane.source_snapshot_evidence
lane.source_snapshot_evidence_completeness
lane.current_snapshot_evidence
lane.current_snapshot_evidence_completeness
lane.triples_to_add_after
lane.triples_to_remove_after
lane.restaged_from
lane.restaged_revision_iri
lane.current_restaged_by
lane.alternative_gate
lane.next_action
lane.next_action_queue_item
lane.repair_draft
lane.repair_draft_error
lane.suggested_next_actions
lane.suggested_next_calls
lane.batch_item
lane.note
```

`lane.lane` is the effective queue, usually `apply_after_review`,
`restage_after_review`, `repair_or_replace`, `inspect_already_applied`, or
`informational`. `batch_action` comes from the dry-run batch classifier, for
example `would_restage`, `skipped_already_handled`, or
`skipped_not_restageable`. A dry-run `would_restage` lane has no successor yet:
`current_revision_iri` is still the stale source. A handled stale lane can have
`current_revision_iri` and `row_iri` set to a refreshed successor. An
already-applied source can have `resolved_target_iri` set to the applied event
and `row_is_target=False`.

`plan.resolved_target_groups[]` is the target-family view over those source
lanes. It collapses rows that point at the same queue and resolved target while
keeping source provenance:

```python
group.group_key
group.queue
group.action_type
group.action_label
group.resolved_target_iri
group.resolved_target_record_kind
group.lane_count
group.row_iris
group.source_revision_iris
group.requested_revision_iris
group.current_revision_iris
group.latest_revision_iris
group.restage_chain_iris
group.applied_event_iris
group.row_is_target_all
group.row_is_target_any
group.alternative_set_iris
group.alternative_set_source_iri
group.alternative_set_roles
group.alternative_gate_statuses
group.alternative_semantic_review_required
```

Use `resolved_target_groups` when explicit `revision_iris` mix stale sources,
current successors, and applied events: `lanes[]` remains one row per source,
while groups show the true target-family worklist. `resolved_target_group_counts`
counts those groups by queue and can be lower than `next_action_queue_item_counts`
when aliases collapse to one current target.

Use `next_action_queue_item.resolved_target_iri` or
`next_action.arguments["iri"]` for the concrete target when present. Raw
`next_action_queue` values are row IRIs and are intentionally not always the
same as the mutation or inspection target. Repair lanes may include
`repair_draft`; when the suggested repair creates a new successor,
`resolved_target_iri` can be `None`, so drive the reviewed repair from
`repair_draft.preferred_action.arguments` or `lane.next_action.arguments`.
`mutation_frontier_iris` is the compact deduped set of resolved targets in
apply/restage/repair queues; it intentionally excludes informational rows,
already-applied inspection targets, and repair helper calls that do not resolve
to an existing target IRI.
When `include_drafts=True` and a no-repair embedded draft already removed
`draft_staged_revision_rebase` from its own suggestions, the lane and top-level
plan suggestions use that draft's inspection/export route too. Do not call the
draft helper again unless it still appears in `lane.suggested_next_actions`.

`would_restage_revision_iris` is a mechanical restage worklist after review, not
an apply queue. `repair_or_replace_source_revision_iris` lists source rows whose
effective lane is `repair_or_replace`, including same-slot repair routes that
may not appear in `repair_first_revision_iris`. `repair_first_revision_iris`
marks stale sources whose staged validation history means a repair draft or
manual replacement should come before another same-payload restage. If
`sequential_apply_recheck_candidate_iris` is non-empty, apply at most one ready
row, then rerun `plan_staged_revision_recovery()` before the next mutation.
`requires_recheck_after_each_apply` is the boolean form of that same sequencing
hazard.
When lane snapshot evidence is incomplete, `plan.suggested_next_actions` promotes
`import_revision_snapshots` or `import_trig` before mutation actions. Treat
normal lane queues as post-preflight routes until that import is complete. When
handoff evidence is complete and `would_restage_revision_iris` is non-empty,
`plan.suggested_next_actions[0]` is a batch
`restage_staged_revisions` dry-run action with
`arguments.revision_iris == would_restage_revision_iris` and
`arguments.dry_run == True`. Keep the row-level restage actions for focused
single-row review, but prefer the batch dry-run before creating restage
successors in unattended loops.

### Staged Revision Rebase Draft

`db.draft_staged_revision_rebase(revision_iri)` returns a
`StagedRevisionRebaseDraft`:

```python
draft.result_kind
draft.helper
draft.mode
draft.source_revision_iri
draft.current_revision_iri
draft.draft_status
draft.draft_kind
draft.reason_codes
draft.source_staged_validation_status
draft.apply_check
draft.lineage
draft.validation_results
draft.repair_candidates
draft.repair_actions
draft.preferred_action
draft.next_action
draft.next_action_queue_item
draft.suggested_next_actions
draft.suggested_next_calls
draft.note
```

The helper is read-only. It never stages, restages, applies, or exports a
revision. Use it when a staged revision routes to `repair_or_replace`, or when a
mechanical restage produced a `validation_failed` successor and the next step is
a reviewed repair rather than another same-payload restage.

`draft_status` is `drafted`, `not_drafted`, or `redirect`.
`draft_kind` explains the route, for example `same_slot_replacement`,
`mechanical_restage_available`, `validation_repair_needed`,
`patch_conflict_repair_needed`, `already_effective`, `already_ready`,
`already_handled`, or `already_applied`. When the helper recognizes a safe
single-slot replacement, `preferred_action` and the first `repair_actions[]`
entry are ready-to-call `stage_map_assertion_change` arguments with
`change_kind="replace"` and `restages_revision` set to the selected staged row.
They still require normal semantic review; the helper only drafts the action.
For drafted repairs, `suggested_next_actions[0]` may also be that mutating
staging call. Treat it as the chosen post-review repair action, not as the
review-first ordering used by plain apply checks.
When no safe repair is drafted, the helper filters out its own
`draft_staged_revision_rebase` action from `next_action` and
`suggested_next_actions`; follow the remaining inspection/export action or
author a manual repair instead of calling the same helper in a loop.

Top-level `current_revision_iri` is the current route target for the selected
row; it can be an applied event IRI for redirect cases. Use `draft.lineage` when
you need staged-lineage fields such as `current_staged_revision_iri`. For a
drafted repair mutation, `next_action_queue_item.resolved_target_iri` can be
`None` and `row_is_target=False` because the action creates a new repaired
successor rather than pointing at an existing row. In that case drive the call
from `next_action.arguments`, especially `restages_revision`.

`draft.lineage` is compact lineage context:

```python
lineage.selected_revision_iri
lineage.current_staged_revision_iri
lineage.current_revision_iri
lineage.latest_revision_iri
lineage.latest_role
lineage.restage_chain_iris
lineage.alternative_revision_iris
lineage.related_revision_iris
lineage.alternative_to
lineage.current_alternative_to
lineage.alternative_gate_status
lineage.alternative_semantic_review_required
lineage.alternative_applied_source_iri
lineage.alternative_applied_revision_iri
```

This is enough to preserve alternative provenance when a repaired successor is
also a semantic alternative to an already-applied staged source. If
`draft_status == "redirect"`, follow `next_action` /
`next_action_queue_item.resolved_target_iri` instead of staging a parallel
repair.

Each `draft.repair_candidates[]` row contains:

```python
candidate.candidate_kind
candidate.candidate_status
candidate.graph
candidate.subject
candidate.predicate
candidate.object
candidate.object_kind
candidate.object_datatype
candidate.object_lang
candidate.current_same_subject_predicate_triples
candidate.proposed_triples
candidate.validation_results
candidate.action
candidate.note
```

For the current first slice, `candidate_kind="same_slot_replacement"` means the
helper recognized a singleton map slot such as `rc:rowSemantics` where the
current graph has exactly one different value. The helper only drafts this for
curated slot/object pairs: `rc:rowSemantics`, `rc:physicalType`, and
`rc:schemaStability` require IRI objects, while `rc:nullable` allows a typed
`xsd:boolean` literal. Blank-node objects and free-text `rc:rowSemantics`
literals are left as manual validation repair work.
`current_same_subject_predicate_triples` shows the value that a replacement
would remove, and `proposed_triples` shows the staged value that would be made
current. If no candidate appears, inspect `validation_results`, `patch_checks`,
and `suggested_next_actions` before authoring a repair.
For validation-failed stale work, `apply_check.recommended_resolution` may still
describe the mechanical restage route in broad terms; treat
`draft.apply_check.routing_decision`, `draft.draft_kind`, `next_action.queue`,
and batch `repair_first_revision_iris` as the authoritative repair-first
routing fields.

`export_staged_revision()` and `export_staged_revisions()` embed this live apply
check into the Markdown artifact at export time. Treat the `Current Apply Check`
section as the review bundle's current-status header: it may say a staged
revision is stale or already applied even when the original staged description
still records the validation result from the time it was created.
When the live apply check reports semantic risk, the export can include a
`Semantic Review Warning` before `Current Apply Check` even if the compact
judgement panel is unavailable for a stale proposal.
When the panel cannot be replayed but stored review signals exist, the export
adds `Stored Review Context` from `description.stored_review_context`.
Restaged single exports also include a top metadata `Restage headline` before
the current apply check. Grouped exports include `Restage Context` near the top
when one or more revisions were refreshed from stale proposals. They include
`Alternative Context` when a stored alternative target has been restaged and the
current comparison target is a refreshed successor.
Stale original exports include a top metadata `Restaged by` line when a
refreshed successor already exists.
If the generated staged Markdown contains credential-like or secret-looking
patch literals, the export inserts a top `Privacy Warning` section and returns
redacted warning fields. Warning line examples refer to the final written
Markdown artifact. The staged patch content itself is preserved and is not
redacted. Pass `fail_on_sensitive=True` to raise before writing when the
generated Markdown contains such matches.
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
export.sensitive_literal_count
export.privacy_warnings
```

`export.revision_iris` is normalized to first-seen unique revision IRIs; grouped
exports do not preserve duplicate input rows or inflate queue counts for repeated
IRIs.

Each item in `revision_summaries` is a
`StagedGraphRevisionExportSummary`:

```python
item.revision_iri
item.summary
item.revision_stance
item.revision_stance_label
item.alternative_to
item.current_alternative_to
item.alternative_gate
item.changed_graphs
item.apply_status
item.apply_decision
item.apply_can_apply
item.apply_summary
item.apply_recommended_resolution
item.apply_recommendation_scope
item.apply_blocking_reasons
item.apply_validation_conforms
item.apply_validation_skipped_reason
item.apply_validation_result_count
item.apply_check_error
item.semantic_risk_level
item.semantic_risk_reasons
item.current_validation
item.staged_validation
item.staged_validation_conforms
item.staged_validation_result_count
item.validation_diagnostic_headline
item.review_recommendation
item.summary_recommendation
item.summary_recommendation_source
item.active_recommendation_field
item.restaged_from
item.restaged_by
item.current_restaged_by
item.stale_resolution_state
item.shared_context_patch_count
item.shared_context_graphs
item.next_action
item.suggested_next_actions
item.suggested_next_calls
```

Use these rows when a script needs the same grouped current-status information
shown in the Markdown summary table without making separate apply-check calls.
`item.review_recommendation` is author-supplied prose stored on the staged
revision. `item.apply_recommended_resolution` is the live apply-check guidance
for the row's current status, such as validation repair or restage advice.
`item.apply_recommendation_scope` is `current_apply_check` for active row
guidance and `prior_source_apply_check_context` when a handled stale source
keeps its old apply-check guidance for provenance. The Markdown summary table
uses `item.summary_recommendation`, which redirects handled stale rows to their
current successor, then prefers staged-validation repair wording when a stale
count/digest conflict is repair-routed because the original staged preview
failed validation. Otherwise it uses live `item.apply_recommended_resolution`
and only falls back to authored review recommendations when no current
mechanical guidance is available. In that repair-routed stale-validation case,
`item.summary_recommendation_source` is `staged_validation_repair_route`.
`item.summary_recommendation_source` names that provenance
(`review_recommendation`, `stale_resolution_redirect`,
`staged_validation_repair_route`, `apply_recommended_resolution`, or `none`).
Structured consumers should follow
`item.active_recommendation_field`, which is `summary_recommendation` for these
grouped rows, unless they are deliberately inspecting raw apply-check context.
`alternative_to`, `current_alternative_to`, `restaged_from`, `restaged_by`,
`current_restaged_by`, and `stale_resolution_state` let recovery scripts keep
alternative groups and stale/restaged chains together without a second revision
list lookup.
`shared_context_patch_count` and `shared_context_graphs` mark rows whose stored
patches include shared `ontology` or `shapes` context, reconstructed from
`rc:SharedContextPatch` roles for grouped handoffs.
The relation fields in `revision_summaries` are nullable IRI strings, not
`ResourceSummary` objects.
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
bundle.ready_restage_successor_alternative_to_applied_source_iris
bundle.post_apply_recheck_revision_iris
bundle.sequential_apply_recheck_candidate_iris
bundle.warnings
bundle.validation_failed_revision_iris
bundle.staged_validation_failed_revision_iris
bundle.recommended_review_iris
bundle.recommended_mutation_review_iris
bundle.recommended_apply_or_restage_review_iris
bundle.recommended_repair_review_iris
bundle.recommended_applied_inspection_iris
bundle.review_sequence
bundle.next_action_queue
bundle.next_action_queue_items
bundle.next_action_queue_item_counts
bundle.snapshot_evidence
bundle.mutation_frontier_iris
bundle.requires_recheck_after_each_apply
bundle.semantic_risk_queue_counts
bundle.semantic_review_required_queue_counts
bundle.shared_context_graphs
bundle.shared_context_patch_summaries
bundle.fallback_revision_iris_with_shared_semantic_context
bundle.shared_semantic_context_warnings
```

`bundle.review_sequence[]` is the ordered cross-lane route for queued grouped
work:

```python
bundle.review_sequence[].phase
bundle.review_sequence[].phase_label
bundle.review_sequence[].row_index
bundle.review_sequence[].row_iri
bundle.review_sequence[].summary
bundle.review_sequence[].queue
bundle.review_sequence[].resolved_target_iri
bundle.review_sequence[].resolved_target_record_kind
bundle.review_sequence[].tool_name
bundle.review_sequence[].mcp_tool_name
bundle.review_sequence[].action_label
bundle.review_sequence[].reason
```

Use it before raw queue buckets when a grouped bundle mixes applied redirects,
validation repair, stale restage, ready apply review, and apply-one-then-recheck
work. Rows can appear again in the `recheck_after_apply` phase when
`requires_recheck_after_each_apply` is true.

`bundle.snapshot_evidence` is a
`StagedGraphRevisionSnapshotEvidenceSummary` for the same rows included in the
grouped export:

```python
bundle.snapshot_evidence.complete
bundle.snapshot_evidence.total_revision_count
bundle.snapshot_evidence.incomplete_revision_iris
bundle.snapshot_evidence.status_counts
bundle.snapshot_evidence.rows[].row_index
bundle.snapshot_evidence.rows[].revision_iri
bundle.snapshot_evidence.rows[].summary
bundle.snapshot_evidence.rows[].status
bundle.snapshot_evidence.rows[].completeness
bundle.snapshot_evidence.rows[].rdf_snapshot_graph_roles
bundle.snapshot_evidence.rows[].stored_snapshot_graph_roles
bundle.snapshot_evidence.rows[].exact_snapshot_graph_roles
bundle.snapshot_evidence.rows[].missing_snapshot_row_graph_roles
bundle.snapshot_evidence.rows[].orphan_snapshot_row_graph_roles
bundle.snapshot_evidence.rows[].note
bundle.snapshot_evidence.rows[].suggested_next_actions
bundle.snapshot_evidence.rows[].suggested_next_calls
```

Grouped export JSON keeps `bundle.next_action_queue` focused on the review/apply
route. For RDF-only handoffs, use `bundle.snapshot_evidence.complete`,
`incomplete_revision_iris`, and row `suggested_next_actions` as the structured
snapshot-import gate before relying on exact stale drift or applied-diff
triples. When the gate is incomplete, `bundle.warnings` repeats that handoff
preflight so Markdown readers see it before the review/apply queues.
When grouped rows carry shared semantic context, `bundle.shared_context_graphs`,
`bundle.shared_context_patch_summaries`, and
`bundle.fallback_revision_iris_with_shared_semantic_context` reconstruct the
draft-level shared-context signal from stored patch roles. Treat
`bundle.shared_semantic_context_warnings` as the export-time equivalent of
`shared_semantic_context_applies_to_all_framings`: inspect those fallback IRIs
before applying, or restage alternatives without shared context when only some
framings should carry provisional vocabulary or validation shapes. The grouped
Markdown repeats the warning in `Bundle Warnings`.

Use `stale_resolution_state == "stale_unresolved"` to find stale proposals that
still need restaging. `stale_handled_by_restage` means the source already
points to a refreshed successor, including stale sources and mechanically ready
sources that were caller-superseded. `restaged_successor_ready` marks a ready
refreshed proposal. `restaged_successor_noop` marks a refreshed proposal whose
replay validates but has no effective graph delta.
`restaged_successor_stale_unresolved` marks a refreshed successor that has
itself become stale again and needs restaging or replacement. The bundle's
`recommended_review_iris` de-duplicates the current review set in bundle order,
replacing handled stale sources with their successors. `next_action_queue`
groups the returned row IRIs by action class; inspect each row's
`next_action.arguments` for the target to call, because handled stale rows may
point to an applied event even though the queued row is the stale source.
`next_action_queue_items[].resolved_target_iri` exposes that target directly,
and `row_is_target=False` flags redirected rows.
`mutation_frontier_iris` is the deduped resolved-target worklist for
apply/restage/repair queues. Use it when an unattended script needs current
mutation targets rather than returned row IRIs; it omits informational handled
stale rows, already-applied inspection targets, and repair helpers whose action
does not name an existing `iri`.
`semantic_risk_queue_counts` counts queued rows whose row summary carries
`semantic_risk_level` of `attention` or `high`. This is separate from
`semantic_review_required_queue_counts`, which only counts alternative-gate
semantic-review requirements. Semantic risk can coexist with validation or
conflict blockers, so risk counts can appear under repair queues as well as
`apply_after_review`. Grouped Markdown mirrors each queue item's semantic risk
level and alternative gate status in the `Resolved Targets` table.
`ready_restage_successor_alternative_to_applied_source_iris` lists ready
refreshed successors whose `current_alternative_to` / `alternative_to` target is
already applied. Treat these rows as semantic review targets, not automatic
apply candidates, even though their row-local `next_action.queue` is still
`apply_after_review`. The same condition is exposed locally on list rows, direct
apply checks, staged descriptions, and export summaries as
`alternative_gate.status == "alternative_to_applied_source"`.
Grouped Markdown still keeps handled stale rows in the summary table for
provenance, but their recommendation points to the refreshed successor or
Review Queues instead of treating the stale source as an active restage target.
Grouped Markdown also includes a `Snapshot Evidence` section. When every row is
complete, it gives compact positive complete-row, status-count, and exact-role
confirmation. When any grouped row lacks full exact snapshot rows, it summarizes
snapshot-evidence status counts and lists each row's status, completeness
(`complete`, `partial`, `partial-extra-rows`, `history-only`, `snapshot-only`,
or `missing`), RDF snapshot graph roles, stored snapshot row roles, exact roles,
missing/orphan roles, and suggested next calls.
This is a review-artifact shortcut over each row's `snapshot_evidence` /
`describe_revision_snapshot_evidence()` payload. Use
`describe_revision_snapshot_evidence()` or the JSON `snapshot_evidence` fields
for positive machine-readable confirmation. Incomplete evidence is also
repeated in `Bundle Warnings` before `Review Queues`; those queues still
describe the post-preflight apply/restage/repair route.
`validation_failed_revision_iris` lists rows whose patch counts
replay but whose current preview validation does not conform.
`staged_validation_failed_revision_iris` lists rows whose stored staged-time
validation failed, even when later graph drift now makes the current apply
status a conflict or skips validation.
`sequential_apply_recheck_candidate_iris` is a clearer alias for
`post_apply_recheck_revision_iris` in grouped export summaries: both name ready
or no-op candidates that share changed graphs and should be rechecked after any
one of them is applied. Grouped Markdown labels this queue as sequential apply
recheck candidates, because it is a pre-apply hazard list rather than the
post-apply result from one completed mutation.
`requires_recheck_after_each_apply` is true when that hazard is present.
`recommended_mutation_review_iris` is the broad compatibility review queue for
staged revisions that may still need restage, repair, apply, or manual mutation
decisions. Use `recommended_apply_or_restage_review_iris` for rows that need
apply/reapply or restage judgement, and `recommended_repair_review_iris` for
validation-failed or patch-conflict rows that need a repaired proposal.
`next_action_queue` is the newer compact routing map derived from each row's
`next_action.queue`, so automation can start from apply-after-review,
restage-after-review, repair-or-replace, already-applied inspection, and
informational buckets without joining status, stale state, and recommendation
fields manually.
`warnings` calls out bundle-level sequencing hazards and recommended review IRIs
that are outside the current bundle. If a source-only handled-stale bundle points
at an external refreshed successor, export or describe that successor before
acting. If imported odd history has a parallel restage successor with an applied
event outside the followed current route, warnings name the source, successor,
and applied event, and `recommended_applied_inspection_iris` includes that
applied event. `post_apply_recheck_revision_iris` lists grouped ready/no-op
staged revisions sharing a changed graph whose old readiness should be discarded
after any successful apply. This includes mixed reviews where applying one ready
revision can make sibling ready or no-op revisions stale.
Use
`recommended_applied_inspection_iris` for already-applied staged revisions that
are useful to inspect but should not be applied again.

`db.restage_staged_revisions(...)` returns
`StagedGraphRevisionBatchRestageRecord`:

```python
batch.requested_revision_iris
batch.processed_revision_iris
batch.dry_run
batch.would_restage_revision_iris
batch.repair_first_revision_iris
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
`status_before`, `decision_before`, `routing_decision_before`,
`stale_resolution_state_before`, `blocking_reasons_before`, `source_staged_validation_status`,
`source_validation_result_count`, `source_snapshot_evidence`,
`source_snapshot_evidence_completeness`, `status_after`, `decision_after`,
`routing_decision_after`, `stale_resolution_state_after`, `blocking_reasons_after`,
`current_staged_validation_status`, `current_validation_result_count`,
`current_snapshot_evidence`, `current_snapshot_evidence_completeness`,
`triples_to_add_after`, `triples_to_remove_after`, `action`,
`not_restageable_reason`, `restaged_revision_iri`,
`restaged_from`, `current_restaged_by`, `current_revision_iri`,
`next_action_after`, `next_action_queue_item_after`,
`suggested_next_actions_after`, `repair_first_warning`, and `note`.
The snapshot evidence fields use the same status object as revision list rows,
and the completeness labels match grouped Markdown (`complete`, `partial`,
`partial-extra-rows`, `history-only`, `snapshot-only`, or `missing`). Read them
before trusting exact drift rationale from a dry-run or real batch row.
`restaged_from` is present when the source item is itself a refreshed successor
of an older stale proposal. Current actions are
`restaged`, `would_restage`, `skipped_already_handled`, and
`skipped_not_restageable`. `would_restage` only appears when `dry_run=True`; in
that case no successor is created, `restaged_revision_iris` stays empty, and
`would_restage_revision_iris` lists the stale source revisions that a real run
can mechanically refresh after review. Sources whose stored staged-time
validation failed and whose post-batch route is repair-first are withheld from
that bulk list and reported in `repair_first_revision_iris` instead.
`restaged_revision_iris` is a creation list, not an apply queue;
created successors can still be `validation_failed`, `noop`, or otherwise not
ready. For those would-restage rows, `current_revision_by_source` still points
at the stale source because no current successor exists yet. For all rows, the
`*_after` fields describe the apply check for `current_revision_iri` after the
batch decision. In real restage rows that is the new successor; in already
handled rows it is the latest known successor; in dry-run would-restage rows it
is still the stale source. In real batch runs, top-level
`current_revision_by_source` is recomputed after the whole batch, so stale
ancestors map to the latest successor even when an intermediate successor was
also processed. Use `next_action_after` as row-local explanation for
`current_revision_iri`; `next_action_queue_item_after` is the matching compact
queue item for that same current revision, including resolved target and target
record kind. For automation after a mixed batch, route from
`bundle_summary.next_action_queue` / `bundle_summary.next_action_queue_items` or
top-level `current_revision_by_source` before following per-item next actions.
Read `suggested_next_actions_after`
when a script needs concrete follow-up calls without joining back through
`list_graph_revisions`.
For single-row or per-item batch-restage automation, prefer
`next_action_after.arguments["iri"]` when present, or `current_revision_iri`
otherwise. `restaged_revision_iri` is only
populated for items whose current batch call created a new successor. In the
single-revision restage response, `revision_iri` is the newly created current
successor, and the response also carries `status_after`, `decision_after`,
`routing_decision_after`, `stale_resolution_state_after`,
`blocking_reasons_after`, `next_action_after`, `next_action_queue_item_after`,
and `suggested_next_actions_after` from a fresh apply check on that successor.
Follow `next_action_after` before applying or restaging anything else.
`routing_decision_before` and `routing_decision_after` mirror the effective
route behind each row's compact next action. Use them when `decision_before` or
`decision_after` says `restage_against_current_graph` but the actual route is a
same-slot replacement or already-effective inspection.
`source_staged_validation_status` and `source_validation_result_count` preserve
the source row's stored staged-time validation signal. The `current_*`
validation fields give the same stored staged-time signal for
`current_revision_iri`, which can differ after a real restage creates a
successor. These are separate from live `status_after` and
`blocking_reasons_after`. If a same-payload restaged successor is mechanically
ready only after current graph state fills a source validation gap,
`decision_after` becomes `inspect_restaged_source_validation_failure` and
`next_action_after.queue` is `repair_or_replace` rather than
`apply_after_review`. If the current successor is a revised conforming repair,
the source-failure warning remains visible but the ready row can route to
`apply_after_review`.
Rows with failed staged-time validation keep a `repair_or_replace` compact route
when no successor exists, even when later drift makes `status_after` a live
conflict. In that case, or when a same-payload real restage still routes to
repair, `repair_first_warning` names the hazard directly. Treat a non-empty
warning as stronger than `action="would_restage"`: use
`repair_first_revision_iris`, inspect validation results, or call
`draft_staged_revision_rebase()` before creating another mechanical successor.
`stale_resolution_state_after == "restaged_successor_stale_unresolved"` means a
skipped already-handled source points to a current successor that is itself
stale; inspect or restage `current_revision_iri` before applying anything.
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

Mixed batches often contain stale rows, ready rows, validation failures, and
no-op successors together. Read them in this order:

```python
batch.restaged_revision_iris
# Successors created by this batch, not an apply queue. Some may be no-op or
# validation-failed after replay.

batch.bundle_summary.ready_restage_successor_revision_iris
# Fresh successors that are ready for review/apply consideration.

batch.bundle_summary.next_action_queue
# Compact routing buckets such as apply_after_review, restage_after_review,
# repair_or_replace, inspect_already_applied, and informational.

applied = db.apply_staged_revision(ready_successor)
applied.post_apply_recheck_revision_iris
# Sibling staged revisions sharing changed graphs; re-check or regenerate a
# grouped review before applying any of them.
```

`next_action_queue` groups rows by next move; it is not a preference or
comparison order for alternative framings. Use `revision_summaries` fields such
as `review_recommendation`, `alternative_to`, and `current_alternative_to` when
the relative meaning of ready alternatives matters.

For example, if a batch creates two successors but only one appears in
`ready_restage_successor_revision_iris`, review/apply only that ready successor.
Inspect the other row's `status_after`, `decision_after`,
`stale_resolution_state_after`, and `blocking_reasons_after`; it may be a no-op
or validation-failed successor that belongs in an informational or repair queue.
After any apply, discard stale bundle readiness and feed
`post_apply_recheck_revision_iris` into a fresh check, grouped export, or batch
restage pass.

### Validation Diagnostics

When `validation_conforms` is false, read `validation_results` before inferring
the problem from patch text. Validation results usually include focus node,
result path, constraint, severity, value, messages, and sometimes a DoxaBase
`hint` with repair guidance for common mistakes. In API and MCP JSON, these
diagnostics are always exposed as `validation_results`; prose that says
"diagnostics" and Markdown sections titled `Validation Results` refer to the
same SHACL result records. Diagnostic text is in `messages`, a list of strings,
not a singular `message` field.
This SHACL `diagnostic.hint` is separate from query-planning
`issue.details.repair_hint`: query-planning repair actions are reviewed
`stage_map_assertion_change` templates and may declare required extra arguments
such as caller-supplied `rationale`.

`validate_graph()` returns a `ValidationResult`:

```python
validation.conforms
validation.report_text
validation.result_count
validation.scope
validation.results
```

Each `ValidationDiagnostic` row uses:

```python
diagnostic.iri
diagnostic.focus_node
diagnostic.focus_node_label
diagnostic.result_path
diagnostic.result_path_label
diagnostic.value
diagnostic.source_shape
diagnostic.source_constraint_component
diagnostic.source_constraint_component_label
diagnostic.severity
diagnostic.severity_label
diagnostic.messages
diagnostic.hint
```
