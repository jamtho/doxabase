# DoxyBase Architecture

This document orients future agents working in the repository. It describes what exists now, the main boundaries, and the near-term design direction.

## Purpose

DoxyBase is a local RDF memory capsule for data projects.

The library does not contain an LLM and does not try to decide semantics itself. Agents supply semantic judgement. DoxyBase supplies storage, parsing, named graph mechanics, graph inspection, and explicit validation.

## Repository Map

- `doxybase/`: runtime Python package.
- `doxybase/core.py`: SQLite-backed capsule implementation.
- `doxybase/mcp_server.py`: thin MCP server over the current Python API.
- `doxybase/mcp_tools.py`: JSON-like helper functions used by MCP tools and tests.
- `doxybase/agent_docs.py`: registry for short agent-facing docs.
- `docs/agent/`: operational docs exposed through MCP.
- `ontology/rc_core.ttl`: immutable Rich Canopy base ontology seed graph.
- `ontology/rc_shapes.ttl`: immutable open SHACL shape seed graph.
- `examples/manifest-prototype-rc/`: representative RC fixtures converted from the Manifest prototype.
- `doxybase_design_docs/`: design docs and V1/V2 direction.
- `tools/validate_rdf.py`: repository validation script for ontology and fixtures.
- `tests/`: pytest coverage for RDF assets, core storage/API, docs, and MCP helpers.

## Runtime Model

The central runtime object is:

```python
from doxybase import DoxyBase
```

A `DoxyBase` instance owns one SQLite file, defaulting to `.doxybase.sqlite`.

On creation, it:

1. Creates minimal SQLite tables.
2. Registers default named graph roles.
3. Seeds immutable `base_ontology` and `base_shapes` from package Turtle files.

The current storage is intentionally direct:

- RDF terms are stored as strings in a `quads` table.
- Subjects and objects carry simple kind markers: `uri`, `bnode`, or `literal`.
- Literal datatype and language are stored separately.
- RDFLib is used for parsing source RDF and reconstructing RDF graphs for validation.

This is not a custom RDF engine. It is a small local graph memory with enough structure to build V1 behavior.

## Named Graph Roles

DoxyBase distinguishes immutable shipped seed graphs from mutable project graphs.

Immutable:

- `base_ontology`: shipped `rc:` vocabulary from `ontology/rc_core.ttl`.
- `base_shapes`: shipped SHACL shapes from `ontology/rc_shapes.ttl`.

Mutable:

- `ontology`: project/client vocabulary and model terms.
- `map`: current best structured project/data map.
- `observations`: point-in-time findings and tentative RDF.
- `evidence`: support for observations or map assertions.
- `shapes`: project/client SHACL shapes.
- `history`: versions, revisions, diffs, and consolidation rationale.

Logical includes:

- `ontology` expands to `base_ontology + ontology`.
- `shapes` expands to `base_shapes + shapes`.

Ordinary imports reject writes to immutable seed graphs unless internal seeding explicitly opts in.

## Core API Surface

Implemented:

```python
DoxyBase.create(path, overwrite=False, seed=True)
DoxyBase.import_turtle(source, graph="map", replace=False)
DoxyBase.import_trig(source, replace=False)
DoxyBase.graph_overview(limit=100)
DoxyBase.list_entities(type=None, graph="map", text=None, limit=100, offset=0)
DoxyBase.validate_graph(scope="map", limit_results=100)
DoxyBase.to_graph(graphs=None)
```

`import_trig()` maps fixture graph IRIs such as:

```text
https://richcanopy.org/graph/map
```

to local graph names such as:

```text
map
```

## Validation

Validation is explicit and diagnostic.

`validate_graph()` reconstructs a combined RDFLib graph for the requested scope and runs pySHACL using logical shapes, meaning `base_shapes + shapes`.

Supported scopes:

- `map`
- `ontology`
- `shapes`
- `all`

Current shapes are open. They validate common authoring mistakes for `rc:` terms but do not reject arbitrary client RDF.

## MCP Layer

The MCP server is intentionally thin. It lives in `doxybase/mcp_server.py` and uses the official Python MCP SDK:

```python
from mcp.server.fastmcp import FastMCP
```

Run it with:

```bash
uv run python -m doxybase.mcp_server --capsule .doxybase.sqlite
```

Default transport is stdio.

Current MCP tools:

- `doxybase.list_docs`
- `doxybase.get_doc`
- `doxybase.graph_overview`
- `doxybase.list_entities`
- `doxybase.import_trig`
- `doxybase.load_example_fixtures`
- `doxybase.validate_graph`

Tool functions delegate to `doxybase/mcp_tools.py`. Keep business logic there or in `DoxyBase`, not inside nested MCP decorators, so behavior remains testable without a running MCP client.

## Agent Docs

Agent docs live in `docs/agent/` and are registered in `doxybase/agent_docs.py`.

The MCP docs tools expose these docs:

- `overview`
- `graph_roles`
- `agent_workflow`
- `ontology_primer`
- `mcp_tools`
- `api_reference`
- `fixture_notes`

These docs are deliberately shorter and more operational than the design docs. They tell an agent how to use the current system, where to put facts, and what V1 cannot do yet.

## Ontology Assets

The Rich Canopy base ontology is in `ontology/rc_core.ttl`.

Design posture:

- `rc:` contains shared structural vocabulary.
- Client/domain terms stay in project namespaces, such as `ais:` or `pm:`.
- The ontology is a helpful kernel, not a closed or complete model.

The base shapes are in `ontology/rc_shapes.ttl`.

The Manifest prototype fixtures in `examples/manifest-prototype-rc/` are the current pressure test for the ontology. They exercise data assets, tables, columns, value types, embedded structures, caveats, layout, partitioning, derivations, aggregations, foreign keys, and shared identifiers.

## Tests and Validation Commands

Run all tests:

```bash
uv run pytest
```

Run RDF asset validation:

```bash
uv run python tools/validate_rdf.py
```

Expected state at the time of writing:

- `rc_core.ttl`: 625 triples.
- `rc_shapes.ttl`: 471 triples.
- `ais.trig`: 306 quads.
- `polymarket.trig`: 429 quads.
- All fixtures conform to base SHACL shapes.

## Known Technical Debt

- Storage currently stores term strings directly rather than using interned term IDs.
- Blank node IDs are imported as-is; this is sufficient for current fixtures but not a robust merge strategy.
- There is no revision/diff model yet.
- There is no bounded context graph retrieval yet.
- There is no search/FTS yet.
- The MCP interface exposes inspection and validation, not graph editing or context slices.
- There is no bounded dataset/table description API, so agents may need to read fixture files directly to recover columns, physical layout, caveats, and provenance.
- There is no first-class observation/evidence writer; agents currently need to author RDF/TriG and import it.
- The AIS fixture is representative rather than executable-catalog complete: the real broadcast/index schemas and non-secret storage metadata are richer than the current graph.
- RDFLib emits deprecation warnings for some Dataset/TriG internals during tests.

## Near-Term Build Order

Recommended next implementation steps:

1. Add bounded dataset/table description, either as a focused `describe_dataset()` API or as the first policy for `preview_context_graph()` and `get_context_graph()`.
2. Add observation recording as graph resources with linked evidence.
3. Add lexical search over labels, comments, evidence summaries, and observation notes.
4. Add non-secret executable catalog metadata for physical layouts and storage access patterns.
5. Add slice metadata and revision scaffolding.
6. Add MCP tools for context retrieval after the Python API is stable.

## AIS/DuckDB Pressure Points

The AIS DuckDB handoff notes in `docs/agent/ais-duckdb-doxybase-observations.md` are a useful current pressure test for the architecture.

The session showed that DoxyBase can preserve semantic context, caveats, profile observations, and evidence, but it is not yet enough to drive executable analytics by itself. The successful DuckDB query depended on richer local documentation for the real AIS Parquet schemas and MinIO layout. To support DoxyBase-driven query planning, future graph content and APIs need to expose:

- full logical and physical schemas for the relevant datasets;
- dataset-specific path templates and storage layout, including distinct broadcast and index layouts;
- non-secret storage connection metadata such as bucket, prefix, endpoint profile, and path-style access requirements;
- caveats that should travel with generated queries and results;
- a direct way to record query outputs as observations with evidence.
