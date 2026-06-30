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
- Staged revisions store row-level snapshots of their target graphs so apply
  checks can report exact triples added or removed since staging when count or
  digest drift occurs.

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
- `patterns`: syntheses that connect observations to map facts.
- `evidence`: support for observations or map assertions.
- `shapes`: project/client SHACL shapes.
- `history`: revision metadata, staged patch payloads, applied-revision links,
  graph-count/digest snapshots, review-bundle metadata, and consolidation
  rationale.

Logical includes:

- `ontology` expands to `base_ontology + ontology`.
- `shapes` expands to `base_shapes + shapes`.

Ordinary imports reject writes to immutable seed graphs unless internal seeding explicitly opts in.

## Core API Surface

The exact API is maintained in code and in `docs/agent/api-reference.md` /
`docs/agent/mcp-tools.md`. Current implemented families include:

- capsule lifecycle, graph import/export, export preflight, sensitive-literal
  scanning, controlled graph replacement, and RDFLib graph/dataset conversion;
- graph overview, lexical search, staged-payload search, entity listing,
  resource description, pattern description, dataset description, context
  slicing, and project briefs;
- profile-run retrieval, profile-to-map draft/stage helpers, and profile review
  bundle export;
- storage-aware query context, non-executed query-plan drafting, and external
  query-result/failure capture;
- observation, claim, reconsideration, evidence, source-span, profile, pattern,
  map, storage, layout, partition, relationship, and graph-revision recording;
- assertion-support review plus draft/staged single-assertion map changes;
- staged graph revision staging, systematisation alternatives,
  pattern-promotion staging, apply checks, recovery planning, read-only rebase
  drafting, single and batch restage, grouped exports, and apply;
- revision listing, graph lineage, resource-centric revision discovery, applied
  diff inspection, revision snapshot import/export, and snapshot evidence or
  graph-snapshot inspection;
- fixture loading and explicit SHACL validation.

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

The MCP surface mirrors the Python workflow families through
`doxabase/mcp_tools.py` and thin registrations in `doxabase/mcp_server.py`.
For the maintained list and response-shape notes, call `doxabase.list_docs`
and read `doc_id="mcp_tools"` / `doc_id="response_shapes"`, or run
`codex mcp list` in a configured Codex environment. Avoid treating this
architecture note as the authoritative MCP inventory.

Tool functions delegate to `doxabase/mcp_tools.py`. Keep business logic there or in `DoxaBase`, not inside nested MCP decorators, so behavior remains testable without a running MCP client.

## Agent Docs

Agent docs live in `docs/agent/` and are registered in `doxabase/agent_docs.py`.

The MCP docs tools expose these docs:

- `start_here`
- `overview`
- `graph_roles`
- `agent_workflow`
- `ontology_primer`
- `mcp_tools`
- `response_shapes`
- `observation_recording`
- `observation_rdf`
- `patterns`
- `map_authoring`
- `profiling`
- `systematisation`
- `query_planning`
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
location kind, endpoint profile, path-style S3 requirements, credential
references, and access mode. Secrets do not belong in the graph; credential and
endpoint fields are names that local runtime configuration resolves.

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

- `rc_core.ttl`: 1242 triples.
- `rc_shapes.ttl`: 1219 triples.
- `ais.trig`: 325 quads.
- `polymarket.trig`: 480 quads.
- All fixtures conform to base SHACL shapes.

## Known Technical Debt

- Storage currently stores term strings directly rather than using interned term IDs.
- Blank node IDs are imported as-is; this is sufficient for current fixtures but not a robust merge strategy.
- Staged revisions can be applied with conservative graph-state conflict checks
  and stale proposals can be planned, restaged, grouped, exported, and routed
  through lineage and snapshot-evidence helpers. Rich semantic merge/rebase and
  durable graph version browsing beyond staged/applied snapshots are not
  implemented yet.
- Context slices are route-explained first passes, not a complete staged review
  or proof-of-closure mechanism.
- Search is lexical-only; there is no embedding or hybrid semantic retrieval yet.
- The MCP interface exposes the current workflow families through thin wrappers;
  keep `docs/agent/mcp-tools.md` and tests as the maintained inventory.
- The AIS fixture is representative rather than executable-catalog complete: the real broadcast/index schemas and storage layout are richer than the current graph.
- RDFLib emits deprecation warnings for some Dataset/TriG internals during tests.

## Near-Term Build Order

Recommended next implementation steps:

1. Add fuller staged semantic conflict/rebase/version workflows.
2. Add deeper profiling helpers and field-tested metric recipes.
3. Deepen query-planning helpers that consume storage access metadata and
   produce better execution handoffs.
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
