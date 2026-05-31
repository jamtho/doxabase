# DoxyBase

DoxyBase is a local, agent-operated RDF memory capsule for data projects.

It lets agents store RDF observations about datasets, consolidate those observations into named graph roles, inspect bounded summaries, and run explicit SHACL validation. The project is intentionally small: a Python package backed by a local SQLite file, with RDFLib handling parsing and pySHACL handling validation.

## Current Status

Implemented:

- SQLite-backed named graph capsule.
- Immutable shipped seed graphs: `base_ontology` and `base_shapes`.
- Mutable project graphs: `map`, `ontology`, `observations`, `evidence`, `shapes`, and `history`.
- Turtle import into one graph.
- TriG import into graph roles.
- `graph_overview()`, `list_entities()`, and `validate_graph()`.
- Draft Rich Canopy `rc:` base ontology and open SHACL shapes.
- Representative AIS and Polymarket fixtures converted from the Manifest prototype.
- Thin MCP server for agent use.
- Agent-facing docs exposed through MCP tools.

Not implemented yet:

- Context graph slicing.
- Graph revision/diff workflow.
- Observation recording helper API.
- Search/FTS.
- Dataset/table description API for bounded schema, layout, caveat, and provenance context.
- Full SPARQL endpoint.
- MCP tools for context retrieval or graph revision.

## Layout

- `doxybase_design_docs/` - V1 design brief, API sketch, storage sketch, and ontology notes.
- `docs/agent/` - short operational docs exposed through MCP.
- `doxybase/` - Python package.
- `ontology/rc_core.ttl` - draft immutable `rc:` base ontology seed graph.
- `ontology/rc_shapes.ttl` - draft immutable open SHACL shape seed graph.
- `examples/manifest-prototype-rc/` - representative AIS and Polymarket fixtures converted from Manifest vocabulary to `rc:`.
- `tests/` - parser, validation, capsule, and MCP helper tests.
- `tools/validate_rdf.py` - parser, term-definition, and SHACL validation checks.
- `ARCHITECTURE.md` - project architecture and implementation notes for future agents.

## Development

Set up the uv environment:

```bash
uv sync
```

Run the RDF validation script:

```bash
uv run python tools/validate_rdf.py
```

Run tests:

```bash
uv run pytest
```

## Python Capsule Example

```python
from doxybase import DoxyBase

db = DoxyBase.create(".doxybase.sqlite", overwrite=True)
db.import_trig("examples/manifest-prototype-rc/ais.trig")
db.import_trig("examples/manifest-prototype-rc/polymarket.trig")

overview = db.graph_overview()
tables = db.list_entities(type="rc:Table", graph="map")
validation = db.validate_graph(scope="all")
```

The capsule seeds immutable `base_ontology` and `base_shapes` graphs from `ontology/rc_core.ttl` and `ontology/rc_shapes.ttl`. Project imports can write to mutable graph roles such as `map`, `ontology`, `observations`, `evidence`, `shapes`, and `history`.

## MCP Server

Run the stdio MCP server:

```bash
uv run python -m doxybase.mcp_server --capsule .doxybase.sqlite
```

Useful first tool calls for an agent:

1. `doxybase.list_docs`
2. `doxybase.get_doc` with `doc_id="overview"`
3. `doxybase.get_doc` with `doc_id="graph_roles"`
4. `doxybase.load_example_fixtures`
5. `doxybase.graph_overview`
6. `doxybase.list_entities` with `type="rc:Table"` and `graph="map"`
7. `doxybase.validate_graph` with `scope="all"`

Current MCP tools:

- `doxybase.list_docs`
- `doxybase.get_doc`
- `doxybase.graph_overview`
- `doxybase.list_entities`
- `doxybase.import_trig`
- `doxybase.load_example_fixtures`
- `doxybase.validate_graph`

## Graph Roles

Immutable seed graphs:

- `base_ontology`: shipped Rich Canopy vocabulary.
- `base_shapes`: shipped open SHACL shapes.

Mutable project graphs:

- `ontology`: project/client vocabulary and model terms.
- `map`: current best structured project/data map.
- `observations`: point-in-time and tentative findings.
- `evidence`: source/query/hash/sample support.
- `shapes`: project/client SHACL shapes.
- `history`: revisions, diffs, and consolidation rationale.

Logical includes:

- `ontology` means `base_ontology + ontology`.
- `shapes` means `base_shapes + shapes`.

## Project Direction

The next useful implementation steps are:

1. Add bounded dataset/table context retrieval, such as a `describe_dataset` view over columns, physical types, value types, path templates, caveats, provenance, and related datasets.
2. Add observation recording as first-class graph resources, with linked evidence.
3. Fix or document replacement semantics for multi-fixture imports that target the same graph roles.
4. Add non-secret executable catalog metadata, such as storage layout, bucket/prefix, endpoint profile, and access-mode facts, so query-generation tools do not depend on out-of-band docs.
5. Add basic lexical search over labels/comments/evidence.
6. Add graph slice/revision metadata.
7. Expand MCP tools around context retrieval once the Python API is ready.
