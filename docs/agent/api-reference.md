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
```

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
