# MCP Tools

The MCP server is intentionally thin. It exposes the current Python API plus short operational docs.

## Documentation

`doxybase.list_docs`

Returns available agent docs with IDs, titles, and descriptions.

`doxybase.get_doc`

Returns one markdown doc by ID. Use `max_chars` to bound output.

## Capsule Inspection

`doxybase.graph_overview`

Returns named graph counts, top classes, top predicates, key entity counts, and known namespaces.

`doxybase.list_entities`

Lists entities by RDF type, graph role, optional text filter, limit, and offset. Start with `type="rc:Table"` and `graph="map"`.

## Import and Validation

`doxybase.import_trig`

Imports a TriG file into graph roles. Fixture graph IRIs such as `https://richcanopy.org/graph/map` map to local role names like `map`.

`doxybase.load_example_fixtures`

Convenience tool that imports the AIS and Polymarket RC fixtures.

`doxybase.validate_graph`

Runs pySHACL over the selected scope using logical `shapes` (`base_shapes + shapes`). Use `scope="all"` after importing fixtures.
