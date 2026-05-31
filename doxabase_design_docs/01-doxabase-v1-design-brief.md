# DoxaBase V1 Design Brief for Codex

## Project Name

The project name is **DoxaBase**.

DoxaBase sits under the broader **Rich Canopy** brand. Shared vocabulary terms should use the `rc:` RDF/IRI prefix.

## Purpose

DoxaBase is a local, agent-operated RDF memory capsule for data projects.

It lets agents record observations about datasets, consolidate those observations into a living RDF knowledge graph, retrieve bounded graph slices while doing later analytical work, and revise the graph safely over time.

The key design principle is:

> Do not abstract away the graph from the agent. Curate bounded RDF fragments for the agent, but preserve the RDF-shaped structure that frontier agents are good at reasoning over.

This is not a general metadata catalogue, and not a hosted graph database. V1 is deliberately small: a local Python library/CLI/MCP-compatible core backed by a single SQLite file.

## Product Thesis

Frontier LLM agents are unexpectedly good at working with RDF and knowledge graphs. They can read large RDF fragments, infer viable graph structures from messy notes, and make sensible graph edits.

DoxaBase should lean into that capability.

The library should not answer every semantic question itself. There is no LLM inside the library. The client agent supplies semantic judgement. DoxaBase supplies graph storage, retrieval, slicing, versioning, parse validation, observation capture, and optional SHACL validation.

The agent-facing contract is:

> Agent supplies semantic intent; DoxaBase supplies graph mechanics.

## Rich Canopy Base Ontology

V1 should include a small, extensible Rich Canopy base ontology under the `rc:` prefix.

This ontology is a helpful kernel for data-project modelling, not a closed world. Clients may add arbitrary classes, properties, vocabularies, and RDF patterns that suit their domain. DoxaBase should accept arbitrary parse-valid RDF; projects get more built-in retrieval and validation help when they use `rc:` terms, but they are not forced into them.

The base ontology direction is described in `05-rich-canopy-base-ontology.md`. Starter seed files live at `../ontology/rc_core.ttl` and `../ontology/rc_shapes.ttl` relative to this docs folder.

## Mental Model

There are two immutable seed graph roles and six project-owned graph roles.

### 1. Base Ontology Graph

The immutable Rich Canopy vocabulary shipped with DoxaBase.

This graph contains the starter `rc:` classes, properties, and named individuals. It should be loaded into the memory capsule as a named graph but not revised through normal project graph edits.

### 2. Base Shapes Graph

The immutable SHACL shapes shipped with DoxaBase.

These shapes validate common authoring mistakes for `rc:` terms. They are open and diagnostic; they are not a closed-world schema and should not block every V1 edit.

### 3. Map Graph

The current best structured map of the project/data world.

This is what later agents normally retrieve and reason over: datasets, tables, columns, current joins, mappings, caveats, computability claims, and links from project entities to ontology terms.

### 4. Ontology Graph

The project-owned slower-changing vocabulary/model layer.

This includes client-defined classes, properties, labels, comments, definitions, value vocabularies, SKOS concepts, domain/range-ish modelling, term deprecations, replacement links, and ontology-level relationships. It extends the immutable base ontology rather than replacing it.

### 5. Observations Graph

Raw observations, point-in-time profile facts, notes, agent runs, exploratory discoveries, failed assumptions, and tentative RDF.

Most isolated facts discovered during online work belong here first. Offline consolidation can infer more durable map assertions from many observations, including higher-level conclusions such as "this source is in flux".

### 6. Evidence Graph

Evidence records that support observations and map assertions: query text, summaries, file paths, source URIs, content hashes, row samples, or other reproducibility aids.

### 7. Shapes Graph

Project-owned SHACL shapes and validation constraints.

These are allowed to evolve along with the project ontology/model. V1 should validate descriptions explicitly when asked, not make every edit depend on immediate SHACL conformance. They extend the immutable base shapes rather than replacing them.

### 8. History Graph

Graph versions, revisions, diffs, superseded terms, deprecated mappings, and consolidation rationale.

V1 may implement this minimally, but the storage model should leave room for it.

## Online and Offline Phases

DoxaBase supports two broad modes of agent behaviour.

### Online noticing

While working on a data task, the agent records observations:

- column meanings
- candidate joins
- row-count/null-count discoveries
- enum/value semantics
- data-quality caveats
- metric computability notes
- failed assumptions
- SQL queries and evidence summaries

These observations may be messy and tentative.

### Offline consolidation / sleep phase

Later, the agent retrieves relevant observations and graph context, then revises the Map, Ontology, and Shapes graphs as appropriate.

This may involve:

- merging concepts
- renaming ontology terms
- adding classes/properties
- adding or changing SHACL shapes
- deprecating old mappings
- replacing ad hoc observations with durable structured knowledge

No human approval is required by default. Human review may be added later, but V1 should support agent-governed graph evolution with provenance and rollback-oriented design.

## V1 Non-Goals

Do not build these in V1:

- hosted service
- distributed graph database
- multi-user permissions
- large-scale graph traversal for millions/billions of triples
- embedded LLM/agent inside the library
- embeddings or hybrid semantic search
- multi-agent debate/review system
- mandatory SHACL-at-commit transaction system
- Oxigraph backend
- full SPARQL endpoint
- elaborate retrieval-provenance pipeline

V1 should be small, local, predictable, and easy to drop into a project.

## Storage

Use a single SQLite file as the project memory capsule.

Default path example:

```text
.doxabase.sqlite
```

The conceptual model is RDF/named graphs. SQLite is only the local storage container and index.

Required storage capabilities:

- RDF-ish quad store
- named graph registry
- graph version metadata
- slice metadata
- graph revisions
- observations
- evidence records
- SHACL shape storage
- FTS index for labels, notes, definitions, rationales, evidence summaries

## Named Graphs

V1 should support named graph layers, even if the first implementation is simple.

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

These can be represented as entries in `named_graphs`. `base_ontology` and `base_shapes` are immutable shipped seed graphs. The other graphs are project-owned and mutable.

The API should allow callers to include/exclude layers when fetching slices. For ordinary agent ergonomics, logical includes may expand as follows:

- `ontology` means `base_ontology` plus mutable project `ontology`.
- `shapes` means `base_shapes` plus mutable project `shapes`.

Advanced callers may still address physical graph names directly.

Agents should prefer these placement rules:

- `base_ontology`: immutable shipped `rc:` vocabulary terms.
- `base_shapes`: immutable shipped open SHACL shapes for `rc:` terms.
- `ontology`: project/client vocabulary terms, semantic types, value vocabularies, labels/comments/definitions, term deprecations and replacements.
- `map`: consolidated current project knowledge: data assets, tables, columns, accepted joins, current caveats, current profile summaries, computability claims, and links to ontology terms.
- `observations`: point-in-time findings, raw notes, tentative profile facts, failed assumptions, and unconsolidated discoveries.
- `evidence`: query text, source references, hashes, evidence summaries, and other support for observations or map assertions.
- `shapes`: project/client SHACL shapes.
- `history`: revisions, graph versions, diffs, deprecations, and consolidation rationale.

Ordinary graph revisions should reject `base_ontology` and `base_shapes` as targets. Updating those graphs is a package/version migration, not a project edit.

## Validation Rules

### Parse validation is mandatory

The library must never accept syntactically invalid RDF as graph content.

This applies to:

- graph revisions
- observation weak triples
- imported Turtle/TriG

If RDF parsing fails, nothing should be committed.

Malformed attempts can be stored as plain text notes or failed revision records, but not as graph triples.

### SHACL validation is V1-supported but not mandatory on every edit

V1 should include a `validate_graph()` function if feasible.

SHACL failure should not automatically block every graph revision in V1. Agents need to be able to make a series of related graph and shape changes before cleaning up validation failures.

The V1 posture:

- parse validation: mandatory gate
- structural safety checks: mandatory where easy
- SHACL validation: explicit diagnostic operation
- SHACL-at-commit: deferred to V2

## Retrieval Principles

All retrieval operations must have explicit limits.

No call should be able to accidentally return an unbounded graph fragment and fill the agent's context.

The main retrieval flow should be:

```text
1. graph_overview()       # agent gets broad map
2. list_entities()        # agent discovers candidate nodes by type
3. search()               # agent uses lexical search if needed
4. preview_context_graph()# agent checks slice size/shape
5. get_context_graph()    # agent fetches bounded RDF fragment
```

The library should return RDF fragments for graph context, not just prose answers.

## Context Policies

V1 supports three context policies.

### `exact`

Return a direct graph neighbourhood around focus nodes.

Suggested behaviour:

- include triples where focus node is subject
- include triples where focus node is object
- include labels for returned nodes if cheap
- obey `include` graph layers
- obey `limit_triples`

### `expanded`

Default policy.

Exact neighbourhood plus predictable additions:

- labels/comments/definitions for touched nodes
- `rdf:type` definitions
- property definitions for predicates used
- one-hop class hierarchy where relevant
- directly attached evidence summaries
- directly attached SHACL shapes if `shapes` included

Do not include embeddings or open-ended semantic similarity in V1.

### `validation`

Context for graph/SHACL work.

Include:

- focus graph slice
- relevant SHACL shapes
- classes/properties targeted by shapes
- recent validation failures if stored
- labels/comments/definitions

## Revision Model

V1 uses one-shot slice replacement.

Flow:

```text
1. Agent calls get_context_graph().
2. Library returns slice_id + RDF fragment.
3. Agent edits/replaces the RDF fragment.
4. Agent calls submit_graph_revision(base_slice_id, revised_graph, rationale).
5. Library parses revised graph.
6. Library computes diff.
7. Library applies diff and creates new graph version.
```

V1 must keep enough metadata to support a future staged revision model.

V2 target:

```text
begin_revision()
apply_change()
apply_change()
validate_revision()
commit_revision()
```

## Import / Export

V1 should support at least:

- import Turtle into a named graph
- export named graph as Turtle
- export context slice as Turtle

TriG support is useful but can be partial/secondary in V1.

Long-term, support:

- Turtle
- TriG
- JSON-LD maybe
- VoID-style graph overview export

## Return Limits

Every operation that can grow must have explicit limits.

Required examples:

- `graph_overview(limit=...)`
- `list_entities(limit=..., offset=...)`
- `search(limit=...)`
- `preview_context_graph(limit=...)`
- `get_context_graph(limit_triples=...)`
- `validate_graph(limit_results=...)`

No unbounded defaults.

## Error Handling

Graph submissions should fail clearly and atomically.

Examples:

- RDF parse failure: reject revision, do not commit
- unknown base slice: reject
- graph version mismatch: reject or warn, depending on implementation
- limit exceeded: return truncated result, not error, unless caller asked for strict mode
- SHACL failures: return validation result; do not necessarily reject V1 revision

## Testing Priorities

Codex should implement tests early.

Minimum tests:

1. Create new memory capsule.
2. Import simple ontology Turtle.
3. Insert map graph triples.
4. `graph_overview()` returns class/predicate counts.
5. `list_entities(type=...)` works with limit/offset.
6. `search()` finds labels and notes.
7. `preview_context_graph()` returns counts without full graph.
8. `get_context_graph(policy="exact")` returns bounded Turtle.
9. `get_context_graph(policy="expanded")` includes labels/type/property definitions.
10. `record_observation()` stores note as graph resource.
11. `record_observation(triples=bad_rdf)` fails.
12. `submit_graph_revision()` rejects invalid RDF.
13. `submit_graph_revision()` accepts valid slice replacement and creates new graph version.
14. `validate_graph()` returns limited validation output.

## Suggested Implementation Order

1. Project skeleton: Python package, tests, SQLite setup.
2. Term dictionary and quad storage.
3. Turtle import/export using RDFLib.
4. Named graph registry.
5. Graph overview counts.
6. Entity listing.
7. FTS search.
8. Context graph retrieval with `exact` policy.
9. Context graph retrieval with `expanded` policy.
10. Slice storage and preview.
11. Observation recording.
12. Slice replacement and graph revision commit.
13. Basic validation.
14. Optional SHACL validation.
15. MCP wrapper.

## Design Slogans

- The graph is the agent's working medium.
- The API should curate RDF, not hide RDF.
- The library has no embedded semantic intelligence.
- The agent supplies semantic judgement; the library supplies graph mechanics.
- Return bounded graph slices, not opaque answers.
- Parse-valid RDF only.
- SHACL is part of the model, but not a V1 hard gate on every edit.
- Store everything locally in one SQLite memory capsule.
- Keep V1 boring, small, and buildable.
