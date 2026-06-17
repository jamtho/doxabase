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
- top observed values or value buckets with frequencies
- scalar profile metrics such as observed minimum, maximum, mean, or median
- column-specific profiling results

Profile observations may include `sample_size`, `sample_scope`,
`sample_method`, `row_count`, `null_count`, and `distinct_count`.
Use `sample_scope` for the bounded population, file set, query result, or slice
covered by the profile. Use `sample_method` for how it was produced, such as
full scan, random sample, stratified sample, or top-N query. Profile observations
may also include `value_frequencies`, a list of
`{"value": ..., "frequency": ...}` objects for observed values or value
buckets, and `profile_metrics`, a list of
`{"metric": "rc:MinimumValue", "value": ...}` objects. Use base metric kinds
such as `rc:MinimumValue`, `rc:MaximumValue`, `rc:MeanValue`,
`rc:MedianValue`, and `rc:StandardDeviationValue` when they fit; use project
metric-kind IRIs for more specific profiler output. Counts and frequencies must
be non-negative. Treat these as observed sample/profile facts, not declared
allowed values or constraints.

Use `doxabase.record_dataset_profile` when a dataset-level profile should also
update the current-best map row-count snapshot or preserve a linked pattern
synthesis. Use plain `record_observation` when the profile result is only a
single point-in-time noticing.

Use `doxabase.record_column_profile` when a column-level profile should also
update current-best map column metadata, such as nullability or physical type,
or preserve a linked pattern synthesis.

Be explicit about the map update booleans. `record_dataset_profile` defaults
`update_map_snapshot=true` and can write `rc:rowCountSnapshot` when `row_count`
is supplied. `record_column_profile` defaults `update_map_column=true` and can
write map column metadata when map fields are supplied. Set these booleans to
`false` when the profile result is a scratch sample, a tentative measurement, or
otherwise not ready to become current-best map context.

When observed values should not become durable semantics, keep the profile
observation-led and record the interpretation separately:

1. Call `record_column_profile(..., update_map_column=false)` with the observed
   counts and value frequencies.
2. Call `record_claim_observation` for the guardrail, such as "these observed
   values are not an allowed-value domain".
3. Call `record_pattern` over the profile observation and guardrail claim when
   the pair is useful lore for future agents.

When a profile helper creates a pattern and the profile observation has
evidence, DoxaBase links that same evidence to the pattern so
`describe_pattern` can show the source directly.

Profile-only capsules may still show `describe_dataset` operational warnings
about missing storage access, path templates, or physical layouts. Those
warnings mean DoxaBase cannot yet give complete query-planning context; they do
not mean the profile observations failed validation.

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

`evidence_summary` is useful prose, but it is not by itself a source identity.
For validation-clean capsules, include `evidence_sources` or a source span when
you create evidence.

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
    sample_scope="All local AIS daily index Parquet files available on 2026-05-31.",
    sample_method="DuckDB full-table aggregate scan.",
    row_count=14638201,
)
```
