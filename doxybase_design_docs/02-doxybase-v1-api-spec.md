# DoxyBase V1 API Spec

## Python API Shape

Names may change, but this is the target V1 shape.

```python
from typing import Literal

class DoxyBase:
    def graph_overview(
        self,
        limit: int = 100,
    ) -> GraphOverview:
        ...

    def list_entities(
        self,
        type: str | None = None,
        graph: str | None = "map",
        text: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> EntityList:
        ...

    def search(
        self,
        query: str,
        graph: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> SearchResults:
        ...

    def preview_context_graph(
        self,
        focus: list[str],
        policy: Literal["exact", "expanded", "validation"] = "expanded",
        include: list[str] = ["map", "ontology"],
        limit: int = 100,
    ) -> GraphSlicePreview:
        ...

    def get_context_graph(
        self,
        focus: list[str],
        policy: Literal["exact", "expanded", "validation"] = "expanded",
        include: list[str] = ["map", "ontology"],
        limit_triples: int = 1000,
        format: Literal["turtle", "trig"] = "turtle",
    ) -> GraphSlice:
        ...

    def record_observation(
        self,
        about: list[str],
        note: str,
        evidence: Evidence | None = None,
        triples: str | None = None,
    ) -> str:
        ...

    def submit_graph_revision(
        self,
        base_slice_id: str,
        revised_graph: str,
        rationale: str,
        target_graph: str = "map",
    ) -> RevisionResult:
        ...

    def validate_graph(
        self,
        scope: Literal["slice", "map", "ontology", "shapes", "all"] = "map",
        slice_id: str | None = None,
        limit_results: int = 100,
    ) -> ValidationResult:
        ...
```

## Logical Graph Includes

V1 should seed every capsule with immutable shipped graphs:

```text
base_ontology
base_shapes
```

Project-owned mutable graphs include:

```text
map
ontology
observations
evidence
shapes
history
```

For ordinary retrieval, callers may use logical includes:

- `ontology` expands to `base_ontology` plus project `ontology`.
- `shapes` expands to `base_shapes` plus project `shapes`.

If an implementation exposes physical graph names directly, it should still keep `base_ontology` and `base_shapes` read-only for ordinary revision APIs.

## Function Semantics

### `graph_overview()`

Cheap orientation call for agents arriving cold.

Returns a compact overview of the memory capsule:

- graph version
- named graph layers and triple counts
- top RDF classes by instance count
- top predicates by usage count
- known namespaces
- counts of datasets/tables/columns/observations/shapes
- suggested entry points
- all fields limited by `limit`

V1 may return JSON. Later versions may support RDF/VoID-style output.

### `list_entities()`

Lists entities, usually by RDF type.

Example:

```python
rc.list_entities(type="rc:Table", limit=100)
```

Use this instead of making `get_context_graph()` double as a general query system.

Returns compact entity rows:

- IRI
- label if known
- RDF types if useful
- graph/layer if useful

### `search()`

Lexical search only in V1.

No embedded LLM. No semantic interpretation.

The current implementation uses SQLite FTS over literal RDF objects, including:

- `rdfs:label`
- `rdfs:comment`
- `rc:summary`
- `rc:caveatDescription`
- `rc:sourceDescription`
- `rc:columnName`
- `rc:pathTemplate`
- evidence summaries

Returns matched resources with graph role, IRI, labels when available, RDF
types, matched predicate, matched text, and snippet.

### `preview_context_graph()`

Preflight call for bounded graph retrieval.

Returns no full Turtle. It estimates or computes the shape of the slice:

- estimated triples
- estimated nodes
- top classes in slice
- top predicates in slice
- likely truncation
- warnings

This should be cheap and safe to call often.

### `get_context_graph()`

Returns a bounded RDF slice.

The response includes:

- `slice_id`
- base graph version
- focus nodes
- policy
- included graph layers
- triple count
- truncated flag
- RDF fragment as Turtle/TriG

Do not return unbounded data.

If the result is truncated, say so clearly in the response object.

### `record_observation()`

Records online agent observations.

The note is natural language. Optional `triples` are weak/provisional RDF and must parse if supplied.

Observation resources should be represented in the graph, not merely hidden in SQL rows.

### `submit_graph_revision()`

Agent submits a revised version of a previously fetched graph slice.

The library:

1. Locates the base slice.
2. Parses the revised RDF.
3. Rejects if parsing fails.
4. Rejects if `target_graph` is immutable, such as `base_ontology` or `base_shapes`.
5. Computes diff between base slice and revised slice.
6. Applies diff to target graph in a SQLite transaction.
7. Creates a new graph version.
8. Stores revision metadata and rationale.

V1 does not need a multi-step revision session.

### `validate_graph()`

Runs graph validation.

V1 should at minimum return parse/structural validation results. If SHACL support is implemented, this call should run SHACL and return limited validation failures.

Do not make full SHACL validation a mandatory gate for every V1 graph revision.

## Context Policy Description API

Policies should be inspectable by the agent.

V1 can provide:

```python
def list_context_policies() -> list[str]: ...
def describe_context_policy(name: str) -> ContextPolicyDescription: ...
```

or include policy descriptions in `graph_overview()`.

Avoid putting long policy descriptions into every MCP tool definition. Make them discoverable.

## MCP Surface

If exposing via MCP, keep the tool surface small.

Suggested tools:

```text
doxybase.graph_overview
doxybase.list_entities
doxybase.search
doxybase.preview_context_graph
doxybase.get_context_graph
doxybase.record_observation
doxybase.submit_graph_revision
doxybase.validate_graph
```

Optional:

```text
doxybase.list_context_policies
doxybase.describe_context_policy
```

Do not create one MCP tool per tiny graph operation. Use parameterised tools.
