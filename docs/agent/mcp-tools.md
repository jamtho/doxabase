# MCP Tools

The MCP server is intentionally thin. It exposes the current Python API plus short operational docs.

## Documentation

`doxabase.list_docs`

Returns available agent docs with IDs, titles, and descriptions.

`doxabase.get_doc`

Returns one markdown doc by ID. Use `max_chars` to bound output.

## Capsule Inspection

`doxabase.graph_overview`

Returns named graph counts, top classes, top predicates, key entity counts, and known namespaces.

`doxabase.list_entities`

Lists entities by RDF type, graph role, optional text filter, limit, and offset. Start with `type="rc:Table"` and `graph="map"`.
For type-aware retrieval, use types such as `rc:Pattern`, `rc:Claim`,
`rc:Evidence`, or `rc:SourceSpan`; the text filter searches literal facts
attached to each resource, not only labels.

`doxabase.describe_resource`

Returns outgoing and incoming triples for one resource, with available labels
and RDF types. Use it after `list_entities` when lexical search found a resource
but you need its structured claim/evidence/source-span context.

`doxabase.search`

Lexically searches literal RDF claims and returns matched resources with graph, IRI, label, types, predicate, matched text, and snippet. Use it to rediscover caveats, observations, evidence, labels, path templates, source notes, and column names.

`doxabase.describe_dataset`

Returns bounded context for one dataset/table IRI: columns, physical/value types, path templates, layouts, storage access descriptions, partitions, caveats, provenance, and directly related datasets.

`doxabase.record_observation`

Records a structured observation in the `observations` graph. Optional evidence fields create a linked `rc:Evidence` resource in the `evidence` graph. Use this for point-in-time findings, profile counts, query outputs, and workflow notes that should remain available to later agents.

`doxabase.record_claim_observation`

Records the common richer pattern: one `rc:Observation`, one linked `rc:Claim`,
one `rc:Evidence`, and optionally one `rc:SourceSpan`. Use this for caveat,
join, schema, transformation, access, profile, or interpretation claims that are
more structured than a note but do not require hand-authored TriG.

`doxabase.record_pattern`

Records one `rc:Pattern` in the `patterns` graph and optionally linked
`rc:Evidence` / `rc:SourceSpan` resources in the `evidence` graph. Use this when
several observations, claims, or sources belong together and suggest a more
durable pattern or map implication.

`doxabase.record_map_dataset`

Records or updates a dataset/table resource in the `map` graph. Omit
`is_table` for partial updates that should preserve existing dataset/table
typing.

`doxabase.record_map_column`

Records or updates a column resource and can link it to a table with
`rc:hasColumn`.

`doxabase.record_map_caveat`

Records or updates a `rc:KnownCaveat` and can link it to affected datasets.

`doxabase.record_map_storage_access`

Records or updates non-secret storage access metadata and can link it to
datasets.

`doxabase.record_map_relationship`

Records or updates a relationship resource. Supported relationship types are
`foreign_key`, `shared_identifier`, and `derivation`.

## Import and Validation

`doxabase.import_trig`

Imports a TriG file into graph roles. Fixture graph IRIs such as `https://richcanopy.org/graph/map` map to local role names like `map`.

`doxabase.export_graph`

Exports one or more graph roles as one flattened RDF graph file. The default is
the `map` graph in Turtle. Use it for quick single-graph review artifacts. The
result includes per-graph triple counts.

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
`scope="all"` after importing fixtures.
