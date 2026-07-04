# Context Slicing

`doxabase.get_context_graph` builds a bounded, route-explained subgraph
around seed resources — the conversation brief for when a describer has
found the right entry point but you need the surrounding RDF. Graph content
arrives as TriG (`include_trig` defaults true); the envelope carries seeds,
warnings, structured contexts, route explanations, and a privacy scan.

## Profiles

The slicer follows explicit routes per profile, not a generic crawl:

- `dataset_brief` — from map datasets/tables: columns, layout/storage/
  partition resources, caveats, provenance, relationships, bounded profile
  observations and metrics, linked patterns and their support. Also
  understands profile-observation, metric, observed-value-type, ordinary
  observation, and mapped-column seeds, expanding each back to its dataset
  context.
- `pattern_brief` — from patterns: targets, map implications, supporting
  claims, observations, evidence, source spans. When search finds a likely
  pattern, seed it here before trying a broad dataset slice — it is usually
  the smaller, clearer handoff.
- `deep_lore` — the same routes plus revision history: records supporting
  selected patterns/claims/observations, `rc:GraphRevision` seeds, and
  revision-anchor matches around a dataset's physical/query metadata.
- `resource_brief` — from arbitrary RDF resources (ontology terms, shapes,
  evidence, source spans, packets): direct references both ways, bounded
  blank-node closure routes, predicate-usage subjects, and named owners
  reached from blank-node seeds. When a slice reaches exactly one queryable
  owner table, it suggests the owner's `describe_query_context`.

## Reading A Slice

Read `reading_order`, then warnings, then structured contexts, then routes —
raw RDF last. Every selected resource carries `routes` explaining why it
entered the slice; route counts count occurrences, not unique resources.
`referenced_only=true` marks resources selected as objects with no subject
triples in the selected graphs — surface context, not vocabulary status.

Truncation (`truncated=true`) is `triples_only`: structured contexts and
route counts still describe the full selected slice. Route caps are separate
from triple truncation — raising `max_triples` returns more triples for
already-selected resources but never recovers omitted route resources;
follow the narrowing suggestions (pattern seeds, `describe_resource` paging,
blank-node closure) instead. Prefer narrowing to a column, profile, metric,
or pattern seed over raising `max_triples`.

`describe_resource` is the quick card (paged direct triples, exact
blank-node closure controls); the slice is high-degree lore recovery with
route explanations. For SHACL shapes and other blank-node-heavy resources,
`describe_resource(graph="shapes", include_blank_node_closure=true)` reads
the constraint details; when search lands on an opaque blank-node fragment,
seed a `resource_brief` slice and follow the owner route to the named shape.

Proposed resources inside staged patch Turtle are not materialized until
apply: slices and describers cannot inspect them. Read staged payloads via
`describe_revision` or find them with `search(scope="staged_patches")`.

## Slice Exports

The slice response is an inspection surface, not a shareable artifact — it
may include seed-graph triples for route context, and its privacy scan
redacts match rows only. For an importable, resource-scoped TriG artifact:

1. `export_preflight(kind="context_slice", seed_iris=[...])` — scans exactly
   the selected slice triples and returns the shareability decision fields.
2. `export_bundle(kind="context_slice", spec={"path": ..., "seed_iris":
   [...]})` — writes the bundle, omitting immutable seed graphs by default
   so a fresh capsule can import it.

On `decision="block"`, follow the read-only suggestions (validate, inspect
locally, narrow seeds) rather than forcing. The validation check uses the
live graph scope implied by the selected roles, so an invalid sibling can
block a narrow slice; keep that default for unattended handoffs. A clean
slice export proves only that the selected triples passed the scanner — for
whole-capsule or staged/history review use
`export_preflight(kind="handoff_bundle")`. A slice that includes `history`
is importable review context, not a recovery handoff: it never carries the
SQLite-side snapshot rows (see `revisions`).

For the narrowest export of one query attempt or finding, seed with the
`evidence_iri` the recorder returned and use `profile="resource_brief"` —
that travels without unrelated dirty map siblings.
