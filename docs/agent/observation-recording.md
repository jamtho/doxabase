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
metric-kind IRIs for more specific profiler output. Before recording, use
`list_entities(type="rc:ProfileMetricKind", graph="base_ontology")` when you
need the current built-in list. Unknown `rc:` metric kinds are rejected so typos
such as `rc:MinValue` do not become ad hoc RDF. For project-specific metrics,
prefer full IRIs unless the project has explicitly configured a prefix, and
define reusable terms in the project ontology when they become durable
vocabulary. Counts and frequencies must be non-negative. A profile metric may
also include `target` when the scalar is specifically about a resource narrower
than the profile as a whole, for example a column measured during a
dataset-level profile. Treat these as observed sample/profile facts, not
declared allowed values or constraints.
Column profile helpers also record the supplied source-level name as
`observed_column_name`, so observation-only columns can be read without parsing
their IRIs.

For example, an untargeted dataset metric applies to the profile observation
or observed asset as a whole, while a targeted metric points at the narrower
resource it measured:

```python
profile_metrics=[
    {
        "metric": "https://example.test/project#CompletenessRatio",
        "value": "0.9167",
        "datatype": "xsd:decimal",
    },
    {
        "metric": "https://example.test/project#MeanCharacterLength",
        "target": "https://example.test/project#customer_name",
        "value": "14.25",
        "datatype": "xsd:decimal",
    },
]
```

Use `doxabase.record_dataset_profile` when a dataset-level profile should also
update the current-best map row-count snapshot or preserve a linked pattern
synthesis. Use plain `record_observation` when the profile result is only a
single point-in-time noticing.

Use `doxabase.record_column_profile` when a column-level profile should also
update current-best map column metadata, such as nullability or physical type,
or preserve a linked pattern synthesis.

Use `doxabase.record_profile_bundle` when one profiling pass produced a
dataset-level summary and several column-level summaries. The bundle helper
writes the same ordinary dataset and column profile records as the single
helpers, but lets column entries share run metadata such as `observed_at`,
`observed_by`, `evidence_summary`, `evidence_sources`, `sample_size`,
`sample_scope`, and `sample_method`. Column entries can override shared values,
and `column_defaults` can set repeated column options such as
`update_map_column=false`. By default, shared evidence means shared evidence
fields and source strings. Pass `shared_evidence_iri` when all profiles in the
pass should link to the same `rc:Evidence` resource.
The helper preflights bundled column payloads and shared evidence summaries
before writing the dataset profile, so invalid bundle inputs do not leave
partial profile, evidence, or map state behind.
`describe_dataset().profile_summary.handoff_note` then gives later agents a
compact cue that profile lore is observed evidence, while storage/path/layout
warnings are physical query-planning metadata gaps rather than profile-recording
failures. When `profile_summary.profile_run_candidates` names shared run
evidence, its `profile_observation_iris` list points at the returned profile
observations that make up that candidate run. If the dataset profile lists are
bounded or omitted counts are non-zero, call
`describe_profile_run(dataset_iri, shared_evidence_iri)` to retrieve all profile
observations linked to that run evidence. Check the returned
`dataset_profile_observations`, `mapped_column_profile_observations`, and
`unmapped_column_profile_observations` lists, together with the top-level
`returned_dataset_profile_count`, `returned_mapped_column_profile_count`,
`returned_unmapped_column_profile_count`, `returned_profile_count`, and matching
`total_*` / `omitted_*` fields, before deciding a profile-run handoff is
complete.

The bundle's `pattern_summary`/`pattern_text` arguments create a pattern
supported by the dataset profile observation only by default. Set
`pattern_support_scope="all_profiles"` when the synthesis should cover the
dataset profile and every bundled column profile. When the synthesis also needs
supporting claims or hand-picked observations, record the bundle first, then
collect the returned observation IRIs and call `record_pattern` with the same
shared evidence:

```python
bundle = db.record_profile_bundle(
    "https://example.test/project#orders",
    dataset_summary="Orders were profiled in one full-table pass.",
    evidence_summary="DuckDB profile query over the local Orders table.",
    evidence_sources=["scratch://orders-profile.sql"],
    sample_size=1000,
    sample_scope="All rows in the local Orders table.",
    sample_method="DuckDB aggregate profile query.",
    row_count=1000,
    map_label="Orders",
    is_table=True,
    shared_evidence_iri="https://example.test/project#OrdersProfileRunEvidence",
    pattern_summary="Orders profile pass links dataset and column measurements.",
    pattern_text="The row count, status distinct count, and amount mean came from one profiling pass.",
    pattern_rationale="Every supporting profile observation links to the same shared run evidence.",
    pattern_support_scope="all_profiles",
    column_defaults={"update_map_column": False},
    column_profiles=[
        {
            "column_iri": "https://example.test/project#orders__status",
            "column_name": "status",
            "summary": "Status values were profiled.",
            "distinct_count": 3,
        },
        {
            "column_iri": "https://example.test/project#orders__amount",
            "column_name": "amount",
            "summary": "Amount values were profiled.",
            "profile_metrics": [{"metric": "rc:MeanValue", "value": "42.5"}],
        },
    ],
)
```

If the synthesis also needs a guardrail claim or narrower support set, call
`describe_profile_run(bundle.dataset_iri, bundle.shared_evidence_iri)` and pass
`profile_run.profile_observation_iris` plus any claims to `record_pattern`
manually instead of using `pattern_support_scope`.

Be explicit about the map update booleans. `record_dataset_profile` defaults
`update_map_snapshot=true` and can write `rc:rowCountSnapshot` when `row_count`
is supplied. `record_column_profile` defaults `update_map_column=true` and can
write map column metadata when map fields are supplied. Set these booleans to
`false` when the profile result is a scratch sample, a tentative measurement, or
otherwise not ready to become current-best map context.
For bundle dataset profiles, `update_map_snapshot=false` also suppresses the
bundle's dataset map label/type/snapshot write. If a receiver should start from
`describe_dataset()` while the profile row count stays observation-only, call
`record_map_dataset()` first to create the map shell. When
`update_map_snapshot=false` on a brand-new dataset, `describe_dataset()` may not
find the dataset until map context is recorded. Use
`record_profile_bundle(...).handoff_entrypoints`, call
`describe_profile_run(dataset_iri, shared_evidence_iri)`, or seed
`describe_context_slice` from profile observation IRIs for observation-only
handoffs.
When a column profile uses `update_map_column=false` and the column is not yet a
map column, `describe_dataset` surfaces it under
`unmapped_column_profile_observations` rather than `columns[]`. The supplied
column name remains available as `observed_column_name` and as a fallback on
`observed_column.column_name`, without promoting the column into the map.

When observed values should not become durable semantics, keep the profile
observation-led and record the interpretation separately:

1. Call `record_column_profile(..., update_map_column=false)` with the observed
   counts and value frequencies.
2. Call `record_claim_observation` for the guardrail, such as "these observed
   values are not an allowed-value domain".
3. Call `record_pattern` over the profile observation and guardrail claim when
   the pair is useful lore for future agents.

For example, a sampled top-N value profile can preserve distribution lore
without implying a closed domain:

```python
profile = db.record_column_profile(
    "https://example.test/project#orders__status",
    table_iri="https://example.test/project#orders",
    column_name="status",
    summary="Sampled top-N profile counted frequent order status values.",
    evidence_sources=["scratch://orders-status-topn"],
    sample_size=50000,
    sample_scope="50,000 sampled orders from the current reporting month.",
    sample_method="DuckDB reservoir sample, then GROUP BY status LIMIT 5.",
    null_count=0,
    distinct_count=7,
    value_frequencies=[
        {"value": "fulfilled", "frequency": 38410},
        {"value": "pending", "frequency": 6412},
    ],
    update_map_column=False,
)
claim = db.record_claim_observation(
    summary="Sampled status values are not a closed domain.",
    claim_text=(
        "The sampled top-N status values are distribution evidence only; "
        "they are not an allowed-value domain."
    ),
    claim_kind="rc:CaveatClaim",
    claim_targets=["https://example.test/project#orders__status"],
    evidence_sources=["scratch://orders-status-topn"],
)
db.record_pattern(
    summary="Status top-N profile needs a domain guardrail.",
    pattern_text=(
        "The observed status frequencies are useful operating lore, but the "
        "profile method can miss rare values."
    ),
    rationale="The profile used a sample and a top-N query.",
    pattern_targets=["https://example.test/project#orders__status"],
    supporting_observations=[profile.observation.observation_iri],
    supporting_claims=[claim.claim_iri],
)
```

When a profile helper creates a pattern and the profile observation has
evidence, DoxaBase links that same evidence to the pattern so
`describe_pattern` can show the source directly.

Project-specific profile metric IRIs are allowed before they are durable
vocabulary, but explain them before relying on the local name alone. A useful
low-commitment loop is:

1. Record the profile metric with a full project IRI.
2. Record a claim that says what the metric means and what it does not mean.
3. Record a pattern with the metric IRI in `pattern_targets` and
   `map_implications`.
4. When the meaning is ready to become vocabulary, use
   `stage_pattern_promotion` to propose ontology terms such as
   `rc:ProfileMetricKind` labels, comments, units, or calculation notes.

The promotion framing is usually caller-authored Turtle. A conservative
definition can use `rdfs:comment` for calculation and unit notes until the
project defines sharper vocabulary. After applying the staged ontology
revision, remember that `list_entities(type="rc:ProfileMetricKind",
graph="ontology")` is an effective-ontology lookup: it includes built-in
`base_ontology` metric kinds as well as project ontology terms. When you need
project-local metric kinds only, filter the returned entities for
`graph == "ontology"`.

```python
metric = "https://example.test/project#FreshnessLagP95Seconds"
profile = db.record_dataset_profile(
    "https://example.test/project#orders",
    summary="Orders freshness lag was profiled from ingestion timestamps.",
    evidence_sources=["scratch://orders-freshness.sql"],
    profile_metrics=[{"metric": metric, "value": 42}],
    update_map_snapshot=False,
)
claim = db.record_claim_observation(
    summary="Freshness lag p95 is an operational quality metric.",
    claim_text=(
        "FreshnessLagP95Seconds measures ingestion delay, not row validity or "
        "a value-domain constraint."
    ),
    claim_kind="rc:InterpretationClaim",
    claim_targets=[metric],
    evidence_sources=["scratch://orders-freshness.sql"],
)
pattern = db.record_pattern(
    summary="Orders freshness metric needs vocabulary before reuse.",
    pattern_text=(
        "The profile metric is useful for operational quality handoff, but its "
        "calculation and units should be defined before other agents compare it."
    ),
    rationale="The profile and interpretation claim describe the same metric.",
    pattern_targets=[metric],
    supporting_observations=[profile.observation.observation_iri],
    supporting_claims=[claim.claim_iri],
    evidence_iri=profile.observation.evidence_iri,
    map_implications=[metric],
)
db.stage_pattern_promotion(
    patterns=[pattern.pattern_iri],
    summary="Define orders freshness lag metric",
    rationale="The metric now has profile evidence and an interpretation claim.",
    framings=[
        {
            "label": "ontology definition",
            "graph": "ontology",
            "content": f'''
                @prefix rc: <https://richcanopy.org/ns/rc#> .
                @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                <{metric}> a rc:ProfileMetricKind ;
                    rdfs:label "freshness lag p95 seconds" ;
                    rdfs:comment "95th percentile ingestion delay in seconds." .
            ''',
        }
    ],
)
```

Because this example keeps the profile observation-only, a metric-seeded
`describe_context_slice(..., profile="dataset_brief")` preserves the profile row
in `seed_profile_observations` but may not include `dataset_contexts`. Call
`record_map_dataset()` first when a receiving agent should start from a dataset
entrypoint, and use `describe_pattern(pattern.pattern_iri)` for the pattern
handoff rather than expecting `pattern_brief` expansion from the metric IRI.

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
