# DoxaBase V1 Storage Schema Sketch

## Storage Goal

DoxaBase uses a single SQLite file as a local memory capsule.

Default path:

```text
.doxabase.sqlite
```

The conceptual model is RDF/named graphs. SQLite is the implementation container.

## Minimal Schema Sketch

This schema is illustrative. Codex may refine it while preserving the product semantics.

```sql
CREATE TABLE terms (
    id INTEGER PRIMARY KEY,
    value TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL
);

CREATE TABLE named_graphs (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    mutable INTEGER NOT NULL DEFAULT 1,
    system_seed INTEGER NOT NULL DEFAULT 0,
    source_path TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE graph_versions (
    id TEXT PRIMARY KEY,
    parent_id TEXT,
    created_at TEXT NOT NULL,
    created_by TEXT,
    rationale TEXT
);

CREATE TABLE quads (
    graph_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    predicate_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,
    object_kind TEXT NOT NULL,
    graph_version_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    retired_at TEXT,
    revision_id TEXT
);

CREATE INDEX quads_spo ON quads(subject_id, predicate_id, object_id);
CREATE INDEX quads_pos ON quads(predicate_id, object_id, subject_id);
CREATE INDEX quads_osp ON quads(object_id, subject_id, predicate_id);
CREATE INDEX quads_gspo ON quads(graph_id, subject_id, predicate_id, object_id);

CREATE TABLE observations (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    about_json TEXT NOT NULL,
    note TEXT NOT NULL,
    graph_version_id TEXT,
    evidence_json TEXT,
    weak_triples TEXT
);

CREATE TABLE evidence (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    kind TEXT NOT NULL,
    summary TEXT,
    body TEXT,
    uri TEXT,
    content_hash TEXT
);

CREATE TABLE slices (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    graph_version_id TEXT NOT NULL,
    focus_json TEXT NOT NULL,
    policy TEXT NOT NULL,
    include_json TEXT NOT NULL,
    format TEXT NOT NULL,
    triple_count INTEGER NOT NULL,
    truncated INTEGER NOT NULL,
    graph_text TEXT NOT NULL
);

CREATE TABLE revisions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    base_slice_id TEXT NOT NULL,
    base_graph_version_id TEXT NOT NULL,
    new_graph_version_id TEXT,
    target_graph TEXT NOT NULL,
    rationale TEXT NOT NULL,
    revised_graph_text TEXT NOT NULL,
    parse_valid INTEGER NOT NULL,
    status TEXT NOT NULL
);
```

## FTS

Add SQLite FTS over:

- term local names
- labels
- comments
- definitions
- observation notes
- evidence summaries
- revision rationales

Exact table design is left to implementation.

## Graph Versions

V1 can use a simple append/supersede approach.

A graph revision should:

1. Reference a base slice.
2. Parse the revised RDF.
3. Compute removed/added triples.
4. Apply changes in a SQLite transaction.
5. Create a new graph version.

V1 does not need fully fledged branch/merge semantics.

## Named Graph Defaults

Suggested default graph names:

```text
base_ontology
base_shapes
map
ontology
observations
evidence
shapes
history
```

`base_ontology` and `base_shapes` are immutable shipped seed graphs loaded from package Turtle files such as:

```text
ontology/rc_core.ttl
ontology/rc_shapes.ttl
```

They should have `mutable = 0` and `system_seed = 1`. Project graphs should have `mutable = 1`.

Retrieval APIs may treat `ontology` as a logical include that expands to `base_ontology + ontology`, and `shapes` as a logical include that expands to `base_shapes + shapes`.

Graph revision APIs should reject revisions targeting immutable seed graphs. Changes to seed graphs happen through package/version migrations, not ordinary project edits.

## RDF Libraries

Use RDFLib initially for Turtle parsing and serialization.

Oxigraph may be revisited later, but V1 should prefer predictable dependencies.
