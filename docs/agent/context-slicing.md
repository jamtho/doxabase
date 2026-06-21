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
  claims, or observations.

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

Every selected resource includes one or more `routes` explaining why it entered
the slice. Read those routes before reading raw triples. They are the difference
between a lore handoff and an opaque RDF neighborhood.
`route_counts` count route occurrences rather than unique resources, so one
resource can legitimately contribute to multiple route totals when it was useful
for more than one reason.

Useful fields:

- `reading_order`: a short static protocol for reading a slice: seeds,
  structured contexts, routes, resources, then raw RDF when needed.
- `resources`: selected resources with labels, descriptions, types, graphs, and
  route reasons. `primary_route` is the highest-priority inclusion reason;
  `referenced_only=true` means the resource was selected as an object/reference
  but has no subject triples in the selected graphs.
- `route_legend`: compact meanings for the route names present in this slice,
  including their priority and count. Use it with `route_counts` before
  inspecting raw triples.
- `route_counts`: how many resources were included through each route.
- `dataset_contexts` and `pattern_contexts`: structured summaries for the main
  domain objects in the slice. Dataset profile lists remain bounded; check
  profile summary total and omitted counts before assuming no older profile
  observations exist.
- `warnings`: notes about how to read the slice. In `deep_lore`, a warning may
  explicitly say that no claims, patterns, reconsiderations, evidence, or
  revision history were found beyond ordinary map context.
- `triples`: selected RDF triples, preserving graph roles.
- `trig`: optional TriG text when `include_trig=true`.
- `resource_count`, `candidate_triple_count`, `returned_triple_count`, and
  `omitted_triple_count`: size signals for the selected resource set and raw
  triple payload.
- `truncated`: true when `max_triples` cut off the selected triples. The
  truncation scope is `triples_only`: resources, route counts, and structured
  contexts still describe the full selected slice.

Treat a slice as a conversation brief, not a proof of closure. If an important
resource is absent, use the routes and raw triples to decide whether the profile
is too narrow, the map lacks a relationship, or the ontology needs a new
predicate.

When `dataset_brief` is truncated but `pattern_contexts` identifies the relevant
synthesis, switch to `pattern_brief` seeded with that pattern for a smaller
handoff. Raise `max_triples` only when you need the raw RDF payload rather than
the structured dataset, pattern, and route summaries.
