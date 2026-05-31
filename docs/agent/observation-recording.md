# Observation Recording

DoxaBase distinguishes current project knowledge from point-in-time findings.

Use the `map` graph for consolidated facts that should describe the current best
understanding of a dataset. Use the `observations` graph for things an agent,
profiler, query, or human just discovered in a particular context.

An observation is not automatically a durable model assertion. It may later be
promoted, summarized, contradicted, or used as evidence for a map update.

## Observation Resources

`doxabase.record_observation` writes an `rc:Observation` or
`rc:ProfileObservation` resource to the `observations` graph.

Use `observation_type="observation"` for general findings:

- a caveat noticed during exploration
- a failed assumption
- a useful note from inspecting a dataset
- a query result that is not just a profile count

Use `observation_type="profile"` for profiling-style findings:

- row counts
- sample sizes
- null counts
- distinct counts
- column-specific profiling results

Profile observations may include `sample_size`, `row_count`, `null_count`, and
`distinct_count`. Counts must be non-negative.

## Evidence Resources

Evidence belongs in the `evidence` graph. `record_observation` can create one
linked `rc:Evidence` resource when `evidence_summary`, `evidence_sources`, or an
explicit `evidence_iri` is supplied.

Evidence should explain how the observation was produced:

- source files or URI patterns
- query text locations or query hashes
- local artifact paths when appropriate
- profiler names or run summaries
- short notes about sampling scope

Do not put credentials or secrets in evidence summaries or sources.

## Identifiers

If no IRI is supplied, DoxaBase mints generated observation and evidence IRIs
under:

```text
https://richcanopy.org/doxabase/generated/
```

Callers may provide `observation_iri` or `evidence_iri` when they need stable
project-specific identifiers.

## V1 Shape

The V1 writer accepts structured fields rather than arbitrary RDF snippets. This
keeps routine observation capture safe, parse-valid, and easy to expose through
MCP. Richer graph-editing APIs can come later through the graph revision model.

The writer adds graph triples only after validating basic inputs such as summary
presence, observation type, ISO datetime syntax, and non-negative counts.

## Example

```python
db.record_observation(
    summary="AIS daily index scan covered 14,638,201 MMSI/day rows.",
    observation_type="profile",
    observed_asset="https://richcanopy.org/example/manifest/ais#DailyIndex",
    observed_at="2026-05-31T00:00:00Z",
    observed_by="urn:doxabase:codex-agent",
    evidence_summary="DuckDB scan over local AIS daily index Parquet files.",
    evidence_sources=["s3://ais-noaa/index/*/*.parquet"],
    row_count=14638201,
)
```
