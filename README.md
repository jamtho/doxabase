# DoxyBase

DoxyBase is a local, agent-operated RDF memory capsule for data projects.

This repository currently contains V1 design notes, a draft Rich Canopy base ontology, open SHACL shapes, and converted fixtures from the Manifest prototype.

## Layout

- `doxybase_design_docs/` - V1 design brief, API sketch, storage sketch, and ontology notes.
- `ontology/rc_core.ttl` - draft immutable `rc:` base ontology seed graph.
- `ontology/rc_shapes.ttl` - draft immutable open SHACL shape seed graph.
- `examples/manifest-prototype-rc/` - representative AIS and Polymarket fixtures converted from Manifest vocabulary to `rc:`.
- `tools/validate_rdf.py` - parser, term-definition, and SHACL validation checks.

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

## Minimal Capsule Example

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
