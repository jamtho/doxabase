# Context Slicing

`doxabase.describe_context_slice` builds a bounded, route-explained subgraph
around one or more seed resources. Use it when `describe_dataset` or
`describe_pattern` has identified the right entry point, but you need a richer
conversation brief with the surrounding RDF.

The slicer is intentionally profile-based rather than a generic graph crawl:

- `dataset_brief` starts from map datasets/tables. It includes dataset context,
  columns, layout/storage/partition resources, caveats, provenance,
  relationships, related dataset reasons, linked patterns, and pattern support.
- `pattern_brief` starts from patterns. It includes pattern targets, map
  implications, supporting claims, observations, evidence, and source spans.
- `deep_lore` follows the same explicit routes and also pulls in relevant
  revision metadata when history records directly support selected patterns,
  claims, or observations.

Every selected resource includes one or more `routes` explaining why it entered
the slice. Read those routes before reading raw triples. They are the difference
between a lore handoff and an opaque RDF neighborhood.

Useful fields:

- `resources`: selected resources with labels, descriptions, types, graphs, and
  route reasons. `primary_route` is the highest-priority inclusion reason;
  `referenced_only=true` means the resource was selected as an object/reference
  but has no subject triples in the selected graphs.
- `route_counts`: how many resources were included through each route.
- `dataset_contexts` and `pattern_contexts`: structured summaries for the main
  domain objects in the slice.
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
