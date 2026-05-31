# API Reference

Current Python API entry point:

```python
from doxybase import DoxyBase
```

## Create or Open a Capsule

```python
db = DoxyBase.create(".doxybase.sqlite", overwrite=True)
```

This initializes the SQLite schema, registers default graph roles, and seeds immutable `base_ontology` and `base_shapes`.

## Import Data

```python
db.import_turtle("path/to/file.ttl", graph="map")
db.import_trig("path/to/file.trig")
```

`import_turtle()` writes all triples to one graph.

`import_trig()` preserves named graph roles and maps `https://richcanopy.org/graph/{role}` to `{role}`.

## Inspect

```python
overview = db.graph_overview(limit=100)
tables = db.list_entities(type="rc:Table", graph="map", limit=100)
dataset = db.describe_dataset(tables.entities[0].iri)
matches = db.search("MMSI vessel", graph="map", limit=10)
observation = db.record_observation(
    summary="Dataset was inspected during the current workflow.",
    observed_asset=dataset.iri,
    evidence_summary="Recorded from the API reference example.",
)
```

`describe_dataset()` returns bounded context for one dataset/table: columns,
physical/value types, path templates, physical layouts, partition schemes,
caveats, provenance, and directly related datasets.

`record_observation()` writes a structured `rc:Observation` or
`rc:ProfileObservation` to the `observations` graph. When evidence fields are
supplied, it also writes a linked `rc:Evidence` resource to the `evidence` graph.

`search()` lexically searches literal RDF claims and returns matched resources,
their graph role, RDF types, matched predicate, matched text, and snippet. Use
it to rediscover labels, caveats, source descriptions, path templates,
observations, and evidence before deciding what to trust or inspect next.

## Validate

```python
result = db.validate_graph(scope="all")
```

Supported scopes today:

- `map`
- `ontology`
- `shapes`
- `all`

## Current Exceptions

`ImmutableGraphError`

Raised when trying to mutate `base_ontology` or `base_shapes` through ordinary import APIs.
