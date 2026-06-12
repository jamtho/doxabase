# DoxaBase Architecture

This document orients future agents working in the repository. It describes what exists now, the main boundaries, and the near-term design direction.

## Purpose

DoxaBase is a local RDF memory capsule for data projects.

The library does not contain an LLM and does not try to decide semantics itself. Agents supply semantic judgement. DoxaBase supplies storage, parsing, named graph mechanics, graph inspection, and explicit validation.

## Repository Map

- `doxabase/`: runtime Python package.
- `doxabase/core.py`: SQLite-backed capsule implementation.
- `doxabase/mcp_server.py`: thin MCP server over the current Python API.
- `doxabase/mcp_tools.py`: JSON-like helper functions used by MCP tools and tests.
- `doxabase/agent_docs.py`: registry for short agent-facing docs.
- `docs/agent/`: operational docs exposed through MCP.
- `ontology/rc_core.ttl`: immutable Rich Canopy base ontology seed graph.
- `ontology/rc_shapes.ttl`: immutable open SHACL shape seed graph.
- `examples/manifest-prototype-rc/`: representative RC fixtures converted from the Manifest prototype.
- `doxabase_design_docs/`: design docs and V1/V2 direction.
- `tools/validate_rdf.py`: repository validation script for ontology and fixtures.
- `tests/`: pytest coverage for RDF assets, core storage/API, docs, and MCP helpers.

## Runtime Model

The central runtime object is:

```python
from doxabase import DoxaBase
```

A `DoxaBase` instance owns one SQLite file, defaulting to `.doxabase.sqlite`.

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

DoxaBase distinguishes immutable shipped seed graphs from mutable project graphs.

Immutable:

- `base_ontology`: shipped `rc:` vocabulary from `ontology/rc_core.ttl`.
- `base_shapes`: shipped SHACL shapes from `ontology/rc_shapes.ttl`.

Mutable:

- `ontology`: project/client vocabulary and model terms.
- `map`: current best structured project/data map.
- `observations`: point-in-time findings and tentative RDF.
- `evidence`: support for observations or map assertions.
- `shapes`: project/client SHACL shapes.
- `history`: revision metadata, graph-count snapshots, consolidation rationale,
  and future staged diffs.

Logical includes:

- `ontology` expands to `base_ontology + ontology`.
- `shapes` expands to `base_shapes + shapes`.

Ordinary imports reject writes to immutable seed graphs unless internal seeding explicitly opts in.

## Core API Surface

Implemented:

```python
DoxaBase.create(path, overwrite=False, seed=True)
DoxaBase.import_turtle(source, graph="map", replace=False)
DoxaBase.import_trig(source, replace=False)
DoxaBase.export_graph(path, graphs="map", format="turtle", overwrite=False)
DoxaBase.export_trig(path, graphs=None, overwrite=False)
DoxaBase.graph_overview(limit=100)
DoxaBase.list_entities(type=None, graph="map", text=None, limit=100, offset=0)
DoxaBase.search(query, graph=None, limit=20, offset=0)
DoxaBase.describe_dataset(iri, graph="map")
DoxaBase.describe_context_slice(seed_iris, profile="dataset_brief", ...)
DoxaBase.record_observation(summary, ...)
DoxaBase.record_dataset_profile(dataset_iri, summary, ...)
DoxaBase.record_column_profile(column_iri, column_name, summary, ...)
DoxaBase.record_graph_revision(summary, rationale, changed_graphs, included_graphs=None, ...)
DoxaBase.stage_graph_revision(summary, rationale, additions=None, removals=None, ...)
DoxaBase.stage_systematisation(summary, intent, framings, anchors=None, shared_additions=None, ...)
DoxaBase.stage_pattern_promotion(patterns, framings, summary=None, ...)
DoxaBase.check_staged_revision_apply(iri, ...)
DoxaBase.apply_staged_revision(iri, ...)
DoxaBase.describe_staged_revision(iri)
DoxaBase.export_staged_revision(iri, path)
DoxaBase.validate_graph(scope="map", limit_results=100)
DoxaBase.to_graph(graphs=None)
DoxaBase.to_dataset(graphs=None)
```

`import_trig()` maps fixture graph IRIs such as:

```text
https://richcanopy.org/graph/map
```

to local graph names such as:

```text
map
```

## Lexical Search

`search()` is the first retrieval affordance for remembered project lore.

The implementation keeps an FTS5 table named `literal_search` as a derivative
index over literal RDF objects in `quads`. The RDF graph remains the source of
truth; the search index is rebuilt from `quads` after imports, observation
writes, and graph clears.

Search returns matched resources rather than detached text. Each match carries
the graph role, subject IRI or blank node, display label, RDF types, matched
predicate, full matched text, and highlighted snippet. This is meant to help an
agent rediscover candidate claims, caveats, observations, evidence, path
templates, and source notes before deciding what to inspect or consolidate.

V1 search is lexical only. It is not semantic search, embedding retrieval,
SPARQL, or graph-neighborhood slicing.

## Validation

Validation is explicit and diagnostic. Staged revision previews preserve
structured SHACL result diagnostics in `history` so failed proposals can be
reviewed without rerunning the preview.

`validate_graph()` reconstructs a combined RDFLib graph for the requested scope and runs pySHACL using logical shapes, meaning `base_shapes + shapes`.

Supported scopes:

- `map`
- `ontology`
- `shapes`
- `all`

Current shapes are open. They validate common authoring mistakes for `rc:` terms but do not reject arbitrary client RDF.

## MCP Layer

The MCP server is intentionally thin. It lives in `doxabase/mcp_server.py` and uses the official Python MCP SDK:

```python
from mcp.server.fastmcp import FastMCP
```

Run it with:

```bash
uv run python -m doxabase.mcp_server --capsule .doxabase.sqlite
```

Default transport is stdio.

Current MCP tools:

- `doxabase.list_docs`
- `doxabase.get_doc`
- `doxabase.graph_overview`
- `doxabase.search`
- `doxabase.list_entities`
- `doxabase.describe_resource`
- `doxabase.describe_pattern`
- `doxabase.describe_graph_revision`
- `doxabase.describe_staged_revision`
- `doxabase.describe_dataset`
- `doxabase.describe_context_slice`
- `doxabase.record_observation`
- `doxabase.record_claim_observation`
- `doxabase.record_pattern`
- `doxabase.record_dataset_profile`
- `doxabase.record_column_profile`
- `doxabase.record_map_dataset`
- `doxabase.record_map_column`
- `doxabase.record_map_caveat`
- `doxabase.record_map_storage_access`
- `doxabase.record_map_physical_layout`
- `doxabase.record_map_partition_scheme`
- `doxabase.record_map_relationship`
- `doxabase.import_trig`
- `doxabase.export_graph`
- `doxabase.export_trig`
- `doxabase.record_graph_revision`
- `doxabase.stage_graph_revision`
- `doxabase.stage_systematisation`
- `doxabase.stage_pattern_promotion`
- `doxabase.check_staged_revision_apply`
- `doxabase.apply_staged_revision`
- `doxabase.export_staged_revision`
- `doxabase.export_staged_revisions`
- `doxabase.load_example_fixtures`
- `doxabase.validate_graph`

Tool functions delegate to `doxabase/mcp_tools.py`. Keep business logic there or in `DoxaBase`, not inside nested MCP decorators, so behavior remains testable without a running MCP client.

## Agent Docs

Agent docs live in `docs/agent/` and are registered in `doxabase/agent_docs.py`.

The MCP docs tools expose these docs:

- `overview`
- `graph_roles`
- `agent_workflow`
- `ontology_primer`
- `mcp_tools`
- `observation_recording`
- `observation_rdf`
- `patterns`
- `map_authoring`
- `revisions`
- `staged_revisions`
- `lexical_search`
- `context_slicing`
- `executable_catalog`
- `field_trials`
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

The Manifest prototype fixtures in `examples/manifest-prototype-rc/` are the current pressure test for the ontology. They exercise data assets, tables, columns, value types, embedded structures, caveats, layout, storage access, partitioning, derivations, aggregations, foreign keys, and shared identifiers.

## Executable Catalog Metadata

DoxaBase records non-secret physical access facts so agents can plan queries
without relying entirely on out-of-band notes.

`rc:StorageAccess` resources hang off data assets through
`rc:hasStorageAccess`. They may describe protocol, storage root, bucket/prefix,
endpoint profile, path-style S3 requirements, credential references, and access
mode. Secrets do not belong in the graph; credential and endpoint fields are
names that local runtime configuration resolves.

Physical layout resources can also record `rc:compressionCodec`. Query planning
should combine storage access, path templates, partition schemes, physical
layout, caveats, and provenance.

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

- `rc_core.ttl`: 1100 triples.
- `rc_shapes.ttl`: 1105 triples.
- `ais.trig`: 325 quads.
- `polymarket.trig`: 442 quads.
- All fixtures conform to base SHACL shapes.

## Known Technical Debt

- Storage currently stores term strings directly rather than using interned term IDs.
- Blank node IDs are imported as-is; this is sufficient for current fixtures but not a robust merge strategy.
- Staged revisions can be applied with conservative count-based conflict
  checks, but rebase, rich conflict resolution, and durable graph version
  storage are not implemented yet.
- Context slices are route-explained first passes, not a complete staged review
  or proof-of-closure mechanism.
- Search is lexical-only; there is no embedding or hybrid semantic retrieval yet.
- The MCP interface exposes inspection, context slicing, staged revision
  apply/review, helper-backed graph writing, validation, and revision metadata.
- The AIS fixture is representative rather than executable-catalog complete: the real broadcast/index schemas and storage layout are richer than the current graph.
- RDFLib emits deprecation warnings for some Dataset/TriG internals during tests.

## Near-Term Build Order

Recommended next implementation steps:

1. Add fuller staged conflict/rebase/version workflows.
2. Add richer profile metrics and profiling helpers.
3. Add query-planning helpers that consume storage access metadata.
4. Consider semantic or hybrid search later, once the literal RDF search surface has enough real usage.

Promotion helpers should be drafting aids, not form workflows. The acceptance
test is whether an agent can use them to stage an awkward systematisation that
does not already fit the current map helpers: a new project vocabulary term, an
ontology extension, or several alternative RDF framings. If the helper only
makes familiar map facts easy, it is suppressing the agent's knowledge-graph
reasoning rather than supporting it.

## Observation Recording Model

`record_observation()` writes structured `rc:Observation` or `rc:ProfileObservation` resources into the `observations` graph. If evidence fields are supplied, it also writes one linked `rc:Evidence` resource into the `evidence` graph.

This keeps routine online findings in RDF without requiring agents to hand-author TriG. The V1 writer deliberately accepts structured fields rather than arbitrary RDF snippets; graph revision APIs can handle richer edits later.

Use observations for point-in-time or source-scoped findings. Consolidated, durable knowledge still belongs in `map`, ideally with links back to supporting observations or evidence when that provenance matters.

## AIS/DuckDB Pressure Points

The AIS DuckDB handoff notes from earlier exploratory work are a useful current pressure test for the architecture.

The session showed that DoxaBase can preserve semantic context, caveats, profile observations, and evidence, but it is not yet enough to drive executable analytics by itself. The successful DuckDB query depended on richer local documentation for the real AIS Parquet schemas and MinIO layout. To support DoxaBase-driven query planning, future graph content and APIs need to continue improving:

- full logical and physical schemas for the relevant datasets;
- dataset-specific path templates and storage layout, including distinct broadcast and index layouts;
- non-secret storage connection metadata such as bucket, prefix, endpoint profile, and path-style access requirements;
- caveats that should travel with generated queries and results;
- richer ways to consolidate query outputs from observations into durable map assertions.
