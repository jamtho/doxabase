# Observation Recording

DoxaBase distinguishes current project knowledge, point-in-time findings, and
synthesis patterns.

Use the `map` graph for consolidated facts that should describe the current best
understanding of a dataset. Use the `observations` graph for things an agent,
profiler, query, or human just discovered in a particular context.
Use the `patterns` graph when related observations or claims now look like a
repeatable or explanatory pattern.

An observation is not automatically a durable model assertion. It may later be
summarized, contradicted, synthesized into a pattern, or used as evidence for a
map update.

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

The base observation SHACL expects observations to link to evidence. The helper
can still create a bare observation when a caller omits evidence fields, but that
is mainly for scratch notes; prefer evidence-backed observations when you expect
the capsule to validate cleanly.

## Identifiers

If no IRI is supplied, DoxaBase mints generated observation and evidence IRIs
under:

```text
https://richcanopy.org/doxabase/generated/
```

Callers may provide `observation_iri` or `evidence_iri` when they need stable
project-specific identifiers.

## Two Observation Lanes

The helper accepts structured fields rather than arbitrary RDF snippets. This
keeps routine observation capture safe, parse-valid, and easy to expose through
MCP.

For nuanced findings, agents may also author observation RDF directly using the
base observation vocabulary. Use that lane for structured caveat, join,
transformation, access, source-span, or proposed-map claims. See
`observation_rdf` for examples.

For the common middle case, use `doxabase.record_claim_observation`. It writes
the standard `rc:Observation` + `rc:Claim` + `rc:Evidence` + optional
`rc:SourceSpan` pattern without requiring hand-authored TriG.

When several observations or claims belong together, use
`doxabase.record_pattern`. Patterns are the preferred bridge from noticed facts
to map facts: they record the agent's rationale before, during, or after map
systematisation. See `patterns` for the dedicated pattern workflow.

When a later claim changes how an earlier claim should be read, use
`doxabase.record_claim_reconsideration`. This is the right move for "I used to
think X, but evidence now makes Y safer" moments. The relation can be
`weakens`, `contradicts`, `supersedes`, or `refines`; choose the lightest
relation that captures the change. For example, use `weakens` when a hunch is
still partly useful but too broad, and `contradicts` when later evidence makes
the earlier claim false.

Reconsiderations preserve exploratory work without pretending every hunch
survived unchanged. They can cite DoxaBase retrieval output as evidence with
`source_kind="rc:DoxaBaseAPISource"` when the supporting artifact is a search,
context slice, dataset description, or other API result. Provide `source_path`
when you want that source kind preserved on an `rc:SourceSpan`; for example,
point it at a scratch JSON export of the retrieval output.

After recording a reconsideration, inspect the older claim through
`describe_resource` or as a supporting claim in `describe_pattern`. Claim
descriptions include a `lifecycle_summary` plus incoming/outgoing
reconsideration details.

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
