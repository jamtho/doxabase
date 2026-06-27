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

Dataset and deep-lore slices also understand profile seeds. A seed
`rc:ProfileObservation` expands to its observed asset/column, evidence, value
frequencies, profile metric nodes, and the observed dataset when available. A
seed `rc:ObservedProfileMetric`, or a metric-kind IRI that is only used as an
`rc:profileMetricKind` object, expands back to the parent profile observation
and dataset context. This is a profile handoff route, not proof that the metric
is durable ontology; define labelled project metric kinds in `ontology` when
the vocabulary should be shared. Metric-kind seed expansion is capped and emits
a warning when many observed metrics match; use a dataset, profile observation,
or observed metric node seed for a narrower complete handoff.
When a project metric kind is only mentioned as a profile metric kind, its
resource row may be `referenced_only` without a warning. Treat that as slice
surface context, not vocabulary status. For profile metric vocabulary review,
use `draft_profile_map_updates.metric_advisories[].advisory_status` and
`definition_found`.
The `seed_profile_observations` field preserves structured profile summaries
selected by profile-observation, observed-profile-metric, or metric-kind seeds
even when those rows are older than the bounded dataset profile lists.
For metric-kind seeds, use `seed_profile_observations` to identify the exact
matching profile rows; `route_counts` and `dataset_contexts` describe broader
handoff context and repeated inclusion routes, not exact metric match counts.

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
lore without first rediscovering the owning dataset by hand. If a column was
recorded only in a profile observation with `update_map_column=false`, its IRI
is an observed object rather than a mapped `rc:Column` subject; dataset/deep
slices still accept that IRI and expand through the matching profile
observation(s) with a `seed_observed_column` route.

Deep-lore slices also understand revision seeds. A seed `rc:GraphRevision`
expands to supporting observations, claims, patterns, revision evidence, anchor
resources, restage/application links, and alternatives when those links are
recorded in `history`. This is the compact route for reading an applied
revision event, stale staged source, or restaged successor without first finding
the dataset or pattern that led to it.

Every selected resource includes one or more `routes` explaining why it entered
the slice. Read those routes before reading raw triples. They are the difference
between a lore handoff and an opaque RDF neighborhood.
`route_counts` count route occurrences rather than unique resources, so one
resource can legitimately contribute to multiple route totals when it was useful
for more than one reason.
There is no `route_explained` profile; route explanations are returned through
`routes`, `route_legend`, and `route_counts` on every valid profile.

Useful fields:

- `profile` and `seeds`: the selected profile name and normalized seed resource
  summaries that produced the slice.
- `reading_order`: a short static protocol for reading a slice: seeds,
  warnings, structured contexts including `seed_profile_observations`, routes,
  resources, then raw RDF when needed.
- `resources`: selected resources with labels, descriptions, types, graphs,
  `surface_role`, and route reasons. `primary_route` is the highest-priority
  inclusion reason. `surface_role` is the quick trust cue: current map context,
  observation context, pattern synthesis, evidence support, revision history,
  vocabulary context, mixed context, or a referenced-only object. `referenced_only=true`
  means the resource was selected as an object/reference but has no subject
  triples in the selected graphs.
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
  routes when raw triples are truncated. Pattern narrowing actions come before
  the same-seed higher-`max_triples` retry because structured context is often
  enough.
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

When `truncated=true`, read `warnings` before assuming the returned payload is
small. Raw RDF is capped by `max_triples`, but structured contexts still return
their full selected summaries; wide datasets or very broad seed sets emit a
warning and should usually be narrowed to a column, profile, metric, or pattern
seed for a smaller handoff. Follow `suggested_next_actions` to narrow to linked
patterns first; raise `max_triples` only when exact raw RDF triples are needed.
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
