# Context Slicing

`doxabase.describe_context_slice` builds a bounded, route-explained subgraph
around one or more seed resources. Use it when `describe_dataset` or
`describe_pattern` has identified the right entry point, but you need a richer
conversation brief with the surrounding RDF.

The slicer is intentionally profile-based rather than a generic graph crawl:

- `dataset_brief` starts from map datasets/tables. It includes dataset context,
  columns, layout/storage/partition resources, layout verification status terms,
  caveats, provenance, relationships, related dataset reasons, bounded returned
  profile observations and metrics, linked patterns, and pattern support.
- `pattern_brief` starts from patterns. It includes pattern targets, map
  implications, supporting claims, observations, evidence, and source spans.
- `deep_lore` follows the same explicit routes and also pulls in relevant
  revision metadata when history records directly support selected patterns,
  claims, or observations. It can also start from an `rc:GraphRevision` seed
  when the revision itself is the handoff entry point.
- `resource_brief` starts from arbitrary RDF resources. It includes direct
  resource types, direct outgoing URI references, bounded blank-node URI
  references, direct incoming URI subjects, URI owners of incoming blank-node
  references, named owners reached from blank-node seeds, and subjects that use
  the seed as an RDF predicate. It includes project and base shape graphs, but
  stays seed-centered rather than crawling recursively. When an evidence seed is
  referenced by an observation, resource brief also includes that observation's
  observed asset and can suggest `describe_query_context` for an observed table
  with query-planning warnings or repair groups.

When lexical search finds a likely pattern, seed that pattern directly with
`profile="pattern_brief"` before trying a broad dataset slice. Pattern seeds
usually give a smaller, clearer handoff for the synthesized lore, support, and
evidence that search found. Use `describe_resource()` for a quick resource card,
but do not treat it as high-degree lore recovery; it does not carry slice route
counts, omitted counts, or offset-style browsing.

For claim seeds, `describe_resource(graph="observations")` includes claim
lifecycle status and nested reconsideration evidence/source spans. Use
`pattern_brief` or `deep_lore` when you need the broader support trail across
patterns, observations, and revision history.

For arbitrary project RDF, such as ontology terms, SHACL shapes, evidence
resources, source spans, or non-dataset map resources, start with
`list_entities()` or `search()`, then use
`describe_context_slice(..., profile="resource_brief")` when you need a
route-explained handoff across graph roles. Use `describe_resource()` when you
need paged direct triples or exact blank-node closure controls. For SHACL node
shapes or other resources whose details sit behind blank-node objects, call
`describe_resource(graph="shapes", include_blank_node_closure=True)` and read
`blank_node_triples`, `blank_node_total_count`, and
`blank_node_omitted_count`. When `blank_node_depth_exhausted=true`, rerun with
a larger `blank_node_depth`; when only `blank_node_omitted_count` is non-zero,
raise `blank_node_limit`. Use `export_graph()` or `export_trig()` when
reviewers need complete Turtle for a graph role.
When lexical search lands on an opaque blank-node shape fragment, do not treat
that blank node as the main handoff. Seed it with
`describe_context_slice(..., profile="resource_brief")`, find the
`blank_node_seed_owner` route, then inspect the named owner shape with
`describe_resource(graph="shapes", include_blank_node_closure=True)`.
For predicate seeds, read `predicate_usage_subject` and
`incoming_blank_node_owner` routes together: a project predicate can be defined
in ontology, constrained in shapes, and used by map resources in the same
slice. `incoming_blank_node_owner` walks through nested SHACL blank-node
fragments, so a predicate used inside `sh:qualifiedValueShape` can still route
back to the named owner shape.
Route-cap warnings are separate from raw triple truncation. Raising
`max_triples` only returns more triples for resources already selected; it does
not recover omitted `resource_brief` route resources. Use the
`suggested_next_actions`: direct outgoing/incoming caps page through
`describe_resource`, blank-node reference caps inspect
`include_blank_node_closure`, and predicate-usage caps currently require
exporting/narrowing because there is no paged predicate-usage browser yet.
Incoming reference caps are usefulness-ranked before selection: resources with
direct claims, caveats, patterns, profile observations, staged revisions, or
dataset/column roles are preferred over plain generic references. Paging is
still the route for exhaustive inbound review.
This applies to durable graph content. Proposed ontology or SHACL resources
inside staged patch Turtle are not materialized as ordinary graph resources
until the staged revision is applied, so `resource_brief` and
`describe_resource()` cannot inspect a proposed shape's blank-node property
constraints directly. For staged ontology/shape proposals, use
`describe_staged_revision()` and grouped staged exports to read the patch
payload, validation diagnostics, and review context.
If a seed IRI is not found, or `describe_resource()` returns an all-empty card
for a remembered proposal IRI, check staged patch payloads before treating the
resource as absent. Use
`list_resource_revisions(resource_iri=..., include_patch_mentions=True)` when
you know the exact IRI, or `search_staged_patch_payloads(...)` when you only
remember a label, local name, or proposal prose.

Dataset and deep-lore slices also understand profile seeds. A seed
`rc:ProfileObservation` expands to its observed asset/column, evidence, value
frequencies, profile metric nodes, and the observed dataset when available. A
seed `rc:ObservedProfileMetric`, or a metric-kind IRI that is only used as an
`rc:profileMetricKind` object, expands back to the parent profile observation
and dataset context. A value-type IRI used only as an
`rc:observedValueType` object likewise expands through matching profile
observations, even before that value type has durable ontology triples. These
are profile handoff routes, not proof that the metric or value type is durable
ontology; define labelled project metric kinds or value types in `ontology`
when the vocabulary should be shared. Metric-kind and observed-value-type seed
expansion is capped and emits a warning when many profile rows match; use a
dataset, profile observation, observed column, or observed metric node seed for
a narrower complete handoff.
When a project metric kind is only mentioned as a profile metric kind, its
resource row may be `referenced_only` without a warning. Treat that as slice
surface context, not vocabulary status. For profile metric vocabulary review,
use `draft_profile_map_updates.metric_advisories[].advisory_status` and
`definition_found`.
The `seed_profile_observations` field preserves structured profile summaries
selected by profile-observation, observed-profile-metric, metric-kind, or
observed-value-type seeds even when those rows are older than the bounded
dataset profile lists. For metric-kind or observed-value-type seeds, use
`seed_profile_observations` to identify the exact matching profile rows;
`route_counts` and `dataset_contexts` describe broader handoff context and
repeated inclusion routes, not exact metric/value-type match counts.

Dataset and deep-lore slices also understand ordinary `rc:Observation` seeds.
They expand through observed assets/columns, claims, evidence, value
frequencies, metrics, linked dataset patterns, and, for `deep_lore`, revision
records that cite the observation. Profile observations keep their separate
`seed_profile_observation` route and structured `seed_profile_observations`
summary.

Dataset and deep-lore slices also understand mapped column seeds. A seed
`rc:Column` expands to its owning dataset plus claims, patterns, observations,
and reconsiderations that directly target or observe that column. This is the
preferred route when an agent starts from a column IRI and needs column-specific
lore without first rediscovering the owning dataset by hand. If that owner table
has query-planning warnings or repair groups, `suggested_next_actions` includes
a `describe_query_context` action for the owner just as it would for a table
seed. If a column was recorded only in a profile observation with
`update_map_column=false`, its IRI is an observed object rather than a mapped
`rc:Column` subject; dataset/deep slices still accept that IRI and expand
through the matching profile observation(s) with a `seed_observed_column` route.

Deep-lore slices also understand revision seeds. A seed `rc:GraphRevision`
expands to supporting observations, claims, patterns, revision evidence, anchor
resources, restage/application links, and alternatives when those links are
recorded in `history`. This is the compact route for reading an applied
revision event, stale staged source, or restaged successor without first finding
the dataset or pattern that led to it.
When a selected map resource such as a dataset, storage access, physical layout,
or partition scheme is named by `rc:revisionAnchor`, `deep_lore` also includes
the staged or applied revision through `revision_anchor_match`; use this when
asking what changed around a dataset's physical/query metadata.
When the seed itself is storage access, physical layout, or partition scheme
metadata, `deep_lore` may only include the seed directly because it is a
lore/history profile. Follow the `Retry with resource brief` suggested action
to recover owner-table `incoming_reference` routes and any
`describe_query_context` repair follow-up.

Every selected resource includes one or more `routes` explaining why it entered
the slice. Read those routes before reading raw triples. They are the difference
between a lore handoff and an opaque RDF neighborhood.
`route_counts` count route occurrences rather than unique resources, so one
resource can legitimately contribute to multiple route totals when it was useful
for more than one reason.
There is no `route_explained` profile; route explanations are returned through
`routes`, `route_legend`, and `route_counts` on every valid profile.
There is also no `route_summaries` field; start with `reading_order`,
`route_counts`, and `route_legend`, then read each resource's `primary_route` and
`routes`.

Useful fields:

- `profile` and `seeds`: the selected profile name and normalized seed resource
  summaries that produced the slice.
- `reading_order`: a short static protocol for reading a slice: seeds,
  warnings, structured contexts including `seed_profile_observations`, routes,
  resources, then raw RDF when needed. It also reminds callers that
  `route_counts` and `route_legend` are the route-summary surface.
- `resources`: selected resources with labels, descriptions, types, graphs,
  `surface_role`, and route reasons. `primary_route` is the highest-priority
  route object, not a scalar route id; read `primary_route.route` in Python or
  `primary_route["route"]` in MCP payloads. `surface_role` is the quick trust
  cue: current map context, observation context, pattern synthesis, evidence
  support, revision history, vocabulary context, validation shape context,
  mixed context, or a referenced-only object. `referenced_only=true` means the
  resource was selected as an object/reference but has no subject triples in the
  selected graphs.
- `route_legend`: list of route legend rows for the route names present in this
  slice, including `route`, `route_label`, `meaning`, `priority`, and `count`.
  Build a dict keyed by `route` if that is more convenient.
- `route_counts`: how many route occurrences were included through each route.
- `dataset_contexts` and `pattern_contexts`: structured summaries for the main
  domain objects in the slice. Dataset profile lists remain bounded; check
  profile summary total and omitted counts before assuming no older profile
  observations exist.
- `seed_profile_observations`: structured profile rows selected by
  profile-observation, observed-profile-metric, metric-kind, or observed-column
  seeds, independent of the bounded dataset profile lists.
- `warnings`: notes about how to read the slice. In `deep_lore`, a warning may
  explicitly say that no claims, patterns, reconsiderations, evidence, or
  revision history were found beyond ordinary map context. When a seed type does
  not match the selected profile, the warning names the seed type and the profile
  to retry, for example rerunning an `rc:Pattern` seed with `pattern_brief` or
  `deep_lore`.
- `suggested_next_actions` and `suggested_next_calls`: structured follow-up
  routes. When a seed table or seed-reached owner table carries operational
  query-planning warnings or query-context repair groups, a
  `describe_query_context` action points to readiness, target candidates, and
  repair hints even if raw triples were not truncated. The action reason names
  actual repair groups separately from warning-only codes. When raw triples are
  truncated, pattern narrowing actions come before the same-seed higher
  `max_triples` retry because structured context is often enough.
- `triples`: selected RDF triples, preserving graph roles.
- `trig`: optional TriG text when `include_trig=true`.
- `resource_count`, `candidate_triple_count`, `returned_triple_count`, and
  `omitted_triple_count`: size signals for the selected resource set and raw
  triple payload.
- `graph_counts` and `triple_count`: graph-role counts for returned triples and
  the compact total returned triple count.
- `truncated`: true when `max_triples` cut off the selected triples. The
  truncation scope is `triples_only`: resources, route counts, and structured
  contexts still describe the full selected slice.

Use `preflight_context_slice_export()` and `export_context_slice()` when the
handoff needs an importable, resource-scoped TriG artifact. These helpers reuse
the selected `describe_context_slice` triples, scan only those selected triples
for credential-like terms, and omit immutable seed graphs by default so a fresh
DoxaBase capsule can import the bundle without `allow_immutable=True`. This is
the safer route when the target resource shares a graph role with unrelated
private or noisy resources. By contrast, `describe_context_slice(include_trig=True)`
is an inspection surface; it may include base ontology or base shape triples
selected for route context and should not be assumed to be a recovery or
shareable handoff bundle.

When `truncated=true`, read `warnings` before assuming the returned payload is
small. Raw RDF is capped by `max_triples`, but structured contexts still return
their full selected summaries; wide datasets or very broad seed sets emit a
warning and should usually be narrowed to a column, profile, metric, or pattern
seed for a smaller handoff. Follow `suggested_next_actions` to narrow to linked
patterns first; those pattern suggestions prefer route-relevant linked patterns
over broad filler when the structured dataset context exposes that distinction.
Raise `max_triples` only when exact raw RDF triples are needed.
Mapped column seeds narrow the route explanation and raw RDF neighborhood, but
`dataset_contexts` still includes the owning dataset's full selected column
inventory; use a profile, metric, or pattern seed when the full table inventory
is not useful to the handoff.

Treat a slice as a conversation brief, not a proof of closure. If an important
resource is absent, use the routes and raw triples to decide whether the profile
is too narrow, the map lacks a relationship, or the ontology needs a new
predicate.

When `dataset_brief` is truncated but `pattern_contexts` identifies the relevant
synthesis, switch to `pattern_brief` seeded with that pattern for a smaller
handoff. Raise `max_triples` only when you need the raw RDF payload rather than
the structured dataset, pattern, and route summaries.
