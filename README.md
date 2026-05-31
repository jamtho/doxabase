# DoxaBase

DoxaBase is a local, agent-operated RDF memory capsule for data projects.

The core idea is that useful knowledge about data rarely arrives fully
systematised. Agents and humans notice things while working: row-count facts,
schema caveats, source quirks, query results, suspected joins, broken
assumptions, and interpretations that may or may not hold tomorrow. DoxaBase
gives those claims somewhere durable to live as RDF, without requiring every
claim to be promoted immediately into stable project structure.

It is built around a two-phase loop:

1. **Observation**: record point-in-time or source-scoped findings, with
   evidence, as RDF resources.
2. **Systematisation**: later consolidate useful findings into a more durable
   project map, ontology terms, shapes, caveats, and revision history.

The graph is deliberately open-ended: projects can record arbitrary RDF claims
about datasets. At the same time, DoxaBase ships a small Rich Canopy `rc:`
ontology for common dataset concepts such as assets, tables, columns, physical
layouts, caveats, observations, evidence, and provenance. That shared structure
is meant to make knowledge portable across projects without forcing every
project into a closed schema.

Another image for the project is the handover conversation you wish came with
every complex dataset. When you inherit data, you need more than field names:
you want the hidden facts, local caveats, awkward history, and the mindset
behind how the dataset was created. DoxaBase tries to make that lore cheap to
transfer one-to-many: once a human or agent has worked something out, the claim,
evidence, caveat, and rationale can be recorded for every future reader.

The implementation is intentionally small: a Python package backed by a local
SQLite file, with RDFLib handling parsing and pySHACL handling explicit
validation. There is no embedded LLM in the library. Agents supply semantic
judgement; DoxaBase supplies graph mechanics, storage, retrieval affordances,
and validation.

## Current Status

Implemented:

- SQLite-backed named graph capsule.
- Immutable shipped seed graphs: `base_ontology` and `base_shapes`.
- Mutable project graphs: `map`, `ontology`, `observations`, `evidence`, `shapes`, and `history`.
- Turtle import into one graph.
- TriG import into graph roles.
- `graph_overview()`, `list_entities()`, and `validate_graph()`.
- `search()` for lexical retrieval over literal RDF claims.
- `describe_dataset()` for bounded table schema, layout, caveat, and provenance context.
- `record_observation()` for first-class observation and evidence resources.
- Draft Rich Canopy `rc:` base ontology and open SHACL shapes.
- Representative AIS and Polymarket fixtures converted from the Manifest prototype.
- Thin MCP server for agent use.
- Agent-facing docs exposed through MCP tools.

Not implemented yet:

- Context graph slicing.
- Graph revision/diff workflow.
- Full SPARQL endpoint.
- MCP tools for graph context slicing or graph revision.

## Layout

- `doxabase_design_docs/` - V1 design brief, API sketch, storage sketch, and ontology notes.
- `docs/agent/` - short operational docs exposed through MCP.
- `doxabase/` - Python package.
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
from doxabase import DoxaBase

db = DoxaBase.create(".doxabase.sqlite", overwrite=True)
db.import_trig("examples/manifest-prototype-rc/ais.trig")
db.import_trig("examples/manifest-prototype-rc/polymarket.trig")

overview = db.graph_overview()
tables = db.list_entities(type="rc:Table", graph="map")
dataset = db.describe_dataset(tables.entities[0].iri)
matches = db.search("MMSI vessel", graph="map")
observation = db.record_observation(
    summary="AIS daily broadcasts were inspected during setup.",
    observed_asset=dataset.iri,
    evidence_summary="Example observation recorded from the README workflow.",
)
validation = db.validate_graph(scope="all")
```

The capsule seeds immutable `base_ontology` and `base_shapes` graphs from `ontology/rc_core.ttl` and `ontology/rc_shapes.ttl`. Project imports can write to mutable graph roles such as `map`, `ontology`, `observations`, `evidence`, `shapes`, and `history`.

## MCP Server

Run the stdio MCP server:

```bash
uv run python -m doxabase.mcp_server --capsule .doxabase.sqlite
```

Useful first tool calls for an agent:

1. `doxabase.list_docs`
2. `doxabase.get_doc` with `doc_id="overview"`
3. `doxabase.get_doc` with `doc_id="graph_roles"`
4. `doxabase.load_example_fixtures`
5. `doxabase.graph_overview`
6. `doxabase.search` for remembered terms, caveats, observations, or evidence
7. `doxabase.list_entities` with `type="rc:Table"` and `graph="map"`
8. `doxabase.describe_dataset` with a table IRI from `list_entities`
9. `doxabase.record_observation` for useful point-in-time findings
10. `doxabase.validate_graph` with `scope="all"`

Current MCP tools:

- `doxabase.list_docs`
- `doxabase.get_doc`
- `doxabase.graph_overview`
- `doxabase.search`
- `doxabase.list_entities`
- `doxabase.describe_dataset`
- `doxabase.record_observation`
- `doxabase.import_trig`
- `doxabase.load_example_fixtures`
- `doxabase.validate_graph`

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

1. Add non-secret executable catalog metadata, such as storage layout, bucket/prefix, endpoint profile, and access-mode facts, so query-generation tools do not depend on out-of-band docs.
2. Add graph slice/revision metadata.
3. Expand MCP tools around context retrieval once the Python API is ready.
4. Consider semantic or hybrid search later, after the lexical RDF search surface has settled.
