# AIS DuckDB + DoxyBase Handoff Notes

This note records observations from an exploratory session on 2026-05-31. It is
intended for a later agent working on DoxyBase, the AIS fixture, or DuckDB-based
analytics over the local AIS MinIO bucket.

## What Happened

- The DoxyBase MCP server was available to the agent as `mcp__doxybase.*`.
- Example fixtures were loaded into `.doxybase.sqlite`.
- The AIS fixture was inspected through DoxyBase and from
  `examples/manifest-prototype-rc/ais.trig`.
- The user asked whether the system could write DuckDB-based code to compute
  sophisticated facts from the data.
- A concrete query was run against the local AIS MinIO bucket to find MMSIs with
  the most distinct vessel names.
- The query result, workflow gaps, and several follow-on facts were recorded
  back into DoxyBase as `rc:Observation` / `rc:ProfileObservation` resources
  linked to `rc:Evidence` resources.

Important correction: that concrete DuckDB query was not substantially driven by
DoxyBase. DoxyBase provided high-level AIS semantics, but the executable schema
and S3 layout came from local project documentation outside DoxyBase.

## Observations Recorded In DoxyBase

Because there is no first-class observation-writing MCP tool yet, the session
used the current V1 workaround:

1. Author TriG bundles with `rcg:observations` and `rcg:evidence` graphs.
2. Import them with `doxybase.import_trig`.
3. Validate the capsule with `doxybase.validate_graph(scope="all")`.

The importable observation bundles are:

- `examples/session-observations/ais-duckdb-2026-05-31.trig`
- `examples/session-observations/ais-duckdb-2026-05-31-additional.trig`

After importing both bundles, the capsule had:

- `23` observation resources total
- `12` evidence resources total
- `observations`: `134` triples
- `evidence`: `42` triples
- all-graph SHACL validation: conforms

The recorded observations cover:

- AIS index coverage and schema introspection.
- MMSI/name distribution facts from the DuckDB query.
- Formatting-noise and interpretation caveats for vessel-name variation.
- Examples of high-message MMSIs with two canonical names.
- The fact that the AIS daily index is the right surface for name-variation
  queries.
- DuckDB/MinIO access behavior.
- DoxyBase fixture/schema gaps.
- The generated Manifest DailyIndex path mismatch.
- The fixture replacement footgun.
- Missing MCP affordances such as `describe_dataset`, query generation, and a
  first-class observation writer.
- The broader gap between semantic memory and executable data catalog.

## External Sources Used

Do not copy credentials into repo docs. The local credential note exists at:

- `/home/james/minio/ais-noaa.md`

The richer AIS dataset documentation exists at:

- `/home/james/github.com/jamtho/ais-noaa-fetch/README.md`
- `/home/james/github.com/jamtho/manifest-prototype/descriptions/generated/ais_description.md`

The local AIS data is in MinIO, bucket `ais-noaa`, with this layout:

- `broadcasts/{year}/ais-YYYY-MM-DD.parquet`
- `index/{year}/ais-YYYY-MM-DD.parquet`

The DuckDB query used the index files:

- `s3://ais-noaa/index/*/*.parquet`

## Useful Query Result

The MinIO AIS index scan covered:

- Date range: `2024-01-01` through `2025-12-31`
- Rows: `14,638,201` MMSI/day summaries
- MMSIs with at least one vessel name: `99,106`
- MMSIs with more than one normalized vessel name: `2,742`
- MMSIs with more than one punctuation-insensitive canonical vessel name: `2,700`
- Maximum distinct canonical names found for any MMSI: `2`

The top examples by canonical name count and message count were MMSIs that each
had two names, often split cleanly by year. Examples:

- `360000000`: `INGRAM DUPO` in 2024, `SOMMELIER` in 2025
- `367615990`: `JACOB BRENT` in 2024, `PERCIVAL` in 2025
- `367062370`: `MR LEWIS` in 2024, `MARY ANN` in 2025
- `367705210`: `MS ALLIE` in 2024, `EVERLEY JAYNE` in 2025
- `367430780`: `MISS GLORIA` in 2024, `JACE JAMES` in 2025

Interpretation caveat: these are names broadcast under an MMSI, not guaranteed
vessel rename histories. The existing AIS caveat still applies: MMSI can be
reused, shared, malformed, or spoofed.

## DoxyBase Deficiencies Exposed

### AIS Fixture Is Too Small

The DoxyBase AIS fixture in `examples/manifest-prototype-rc/ais.trig` is a
representative/reduced graph. It does not include the full physical schema used
by the real AIS Parquet files.

Missing from the DoxyBase fixture but present in the real data/docs:

- Broadcast columns: `vessel_name`, `imo`, `call_sign`, `vessel_type`,
  `status`, `length`, `width`, `draft`, `cargo`, `transceiver`, `cog`,
  `heading`
- Index columns: `vessel_names`, `imos`, `call_signs`, `vessel_types`,
  `cargos`, `lengths`, `widths`, `drafts`, `transceiver_classes`,
  `status_codes`, `duration_s`, `centroid_lat`, `centroid_lon`, `min_lat`,
  `max_lat`, `min_lon`, `max_lon`, `h3_cell_count`, `sog_min`, `sog_max`,
  `sog_mean`, `max_inter_msg_speed_ms`

Because `vessel_name` and `vessel_names` are absent from DoxyBase, DoxyBase
could not directly support the "most different names broadcast under their ID"
query.

### Physical Storage Is Not Represented Enough

DoxyBase currently records a path template for the AIS broadcast dataset, but it
does not capture enough executable storage metadata for DuckDB to discover and
query the real data:

- S3 endpoint
- bucket
- key prefixes
- auth profile or credential reference
- whether path-style S3 access is required
- which physical dataset corresponds to `broadcasts/` vs `index/`

These should be graph facts or evidence/provenance resources, without embedding
secrets.

### DoxyBase Cannot Yet Produce a Detailed Schema View via MCP

The MCP `list_entities` tool is useful for finding entities, but there is no MCP
tool for "describe this dataset/table" that returns:

- columns
- column names
- physical types
- value types
- nullability
- path templates
- derivations
- caveats
- provenance
- related aggregate datasets

During exploration, the agent had to read the TriG file directly with shell
commands. A later MCP tool should expose this as bounded structured context.

### No Query Planning Or DuckDB Generation Tool

There is no DoxyBase tool that maps graph facts to executable DuckDB SQL. The
desired workflow would be:

1. Resolve a semantic dataset such as `ais:DailyIndex`.
2. Resolve physical locations and storage settings.
3. Resolve needed columns and semantic caveats.
4. Generate a query template.
5. Run it through DuckDB or hand it to a DuckDB MCP/tool.
6. Record outputs as observations with evidence.

At present, steps 2-6 are manual and live outside DoxyBase.

### No Observation-Recording MCP Tool

The session produced useful facts about the AIS corpus and workflow, but there
is no MCP tool to record observations directly as structured inputs. The
workaround was to manually author TriG files and import them with
`doxybase.import_trig`.

The result should ideally be represented as:

- observation summary
- observed asset: AIS daily index or broadcast dataset
- observed time: execution time
- query text or query hash
- S3 path/prefix scanned
- row count/date coverage
- result sample or artifact path

### Fixture Loading Has A Footgun

When `doxybase.load_example_fixtures(replace=true)` was called, it imported AIS
and then Polymarket with replacement enabled for each fixture. Because both
fixtures write to the same graph roles, the second import overwrote the first
fixture's mutable graph data.

Workaround used in the session:

1. Load fixtures with `replace=true`.
2. Re-import `examples/manifest-prototype-rc/ais.trig` with `replace=false`.

Better behavior could be one of:

- `load_example_fixtures(replace=true)` clears each role once, then appends all
  fixtures.
- Documentation warns that replacement is per fixture and can leave only the
  final fixture visible.
- The tool returns a warning when multiple fixture imports target the same graph
  roles with replacement enabled.

### Potential Documentation Mismatch

The generated AIS description says the `DailyIndex` path template is
`broadcasts/{year}/ais-{date}.parquet`, but the actual `ais-noaa-fetch` README
and MinIO layout use:

- `index/{year}/ais-YYYY-MM-DD.parquet`

This may be a bug in the generated Manifest description or in the source model.
DoxyBase should prefer the actual project layout or represent both datasets with
distinct physical layouts.

### DoxyBase Fixture And Richer Manifest Description Diverge

The DoxyBase fixture appears to be a reduced conversion of representative
Manifest content, while the generated Manifest documentation contains richer AIS
schema and aggregation definitions. A later agent should decide whether to:

- update the DoxyBase fixture to the full current AIS model,
- add a second "full AIS" fixture, or
- implement an importer/converter from the richer Manifest source into DoxyBase.

## General Observations

- DuckDB is a natural execution backend for DoxyBase-described datasets.
- The AIS daily index is the right surface for many identity/name queries because
  it avoids scanning raw broadcast events.
- Semantic caveats matter: for name/MMSI analysis, DoxyBase should surface MMSI
  reliability warnings before or alongside generated queries.
- The dataset has strong year-bound name transitions for many MMSIs. This is
  likely a useful test case for DoxyBase observations, evidence, and generated
  analytical summaries.
- The current DoxyBase system is useful as a semantic memory, but not yet enough
  as an executable data catalog.

## Suggested Next Steps

1. Enrich the AIS DoxyBase graph with the full real broadcast and index schemas.
2. Add non-secret S3 physical layout metadata to the graph.
3. Add an MCP `describe_dataset` or `get_context` tool for bounded table context.
4. Add an MCP observation/evidence write tool.
5. Add DuckDB query generation helpers that consume DoxyBase graph facts.
6. Re-run the vessel-name query through the DoxyBase-driven path and record the
   result back into DoxyBase.
