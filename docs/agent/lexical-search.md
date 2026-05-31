# Lexical Search

Search makes captured lore cheap to rediscover.

DoxyBase stores claims as RDF, but agents do not usually arrive knowing the
right resource IRI, graph role, or predicate. Lexical search is the low-friction
way to ask, "Have we already noticed something about this?"

## What It Indexes

V1 search indexes literal RDF objects from the quad store. That includes common
human-facing text such as:

- `rdfs:label`
- `rdfs:comment`
- `rc:summary`
- `rc:caveatDescription`
- `rc:sourceDescription`
- `rc:columnName`
- `rc:pathTemplate`
- evidence source strings

The index is derivative. The RDF quads remain the source of truth, and the
search index is rebuilt from them after graph writes and clears.

## What A Match Means

`doxybase.search` returns matched resources, not detached text snippets. Each
match includes:

- graph role
- resource IRI or blank-node identifier
- display label when available
- RDF types from the matched graph
- matched predicate
- matched text
- highlighted snippet

Treat matches as candidate context. A match can tell you that a caveat,
observation, path template, or source note exists; it does not decide whether
that claim is current, complete, or applicable to the task.

## Observation And Systematisation

Search is especially important for the observation/systematisation loop.

Observations and evidence let agents capture point-in-time findings without
pretending they are permanent model facts. Search lets later agents find those
findings again, compare them with the current map, and decide whether to promote
useful knowledge into `map`, `ontology`, `shapes`, or future revision metadata.

In other words, search is a memory retrieval affordance, not a semantic judge.
The agent still supplies the judgement.

## Graph Scoping

Use `graph` to narrow the search:

- `graph="map"` for current consolidated project knowledge.
- `graph="observations"` for point-in-time findings.
- `graph="evidence"` for supporting source notes.
- `graph="ontology"` for shared and project vocabulary.
- `graph=None` to search every graph.

Logical graph expansion applies where it already exists: `ontology` includes
`base_ontology + ontology`.

## Examples

Python:

```python
matches = db.search("MMSI vessel", graph="map", limit=10)
```

MCP:

```text
doxybase.search(query="Parquet schemas", graph="map", limit=5)
```

After finding a candidate, inspect the surrounding resource with the most
specific available tool. For tables, use `describe_dataset`. For broader graph
context, use the returned graph, IRI, predicate, and snippet to guide the next
lookup or future graph-slice request.

## Current Limits

V1 search is lexical FTS over RDF literals. It is not embedding search, semantic
retrieval, SPARQL, or graph-neighborhood expansion. It is intentionally simple:
fast enough to find remembered claims, conservative enough to keep provenance
visible.
