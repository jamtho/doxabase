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
