# Map Authoring

The `map` graph holds current-best project structure: datasets, tables,
columns, caveats, storage access, physical layout, and relationships that
future agents should start from. Map facts are revisable — the point is that
the project currently treats them as operating context, ideally with
observations, patterns, or evidence explaining why.

## Direct Writes Versus Staged Changes

The rule, plainly:

- **`record_map_fact` writes directly.** Use it for authoring NEW facts —
  a table you just modelled, a caveat that should be visible immediately, a
  storage route you reviewed. The write happens now, with no review step.
- **`stage_revision` proposes reviewed CHANGES.** Use it whenever you are
  changing or removing facts the map already asserts — replacing a value,
  removing a stale link, promoting a contested interpretation. Stage, check
  with `apply_staged_revision(dry_run=true)`, then apply. The rationale trail
  lands in `history`.

Mechanically, `record_map_fact` can also overwrite: when you supply
helper-owned fields for an existing resource, those same-subject predicates
are replaced for that resource. That power is why the rule matters — an
unreviewed replace of an existing fact erases context another agent relied
on. When in doubt, stage.

Two edge behaviors of the replacement semantics: omitting a scalar parameter
preserves the current value, while passing an explicit empty string clears
that predicate. Incoming convenience links (`caveat` `targets`,
`storage_access` `datasets`, `column` `table_iri`) only add links from other
resources and never prune older ones; narrowing those requires the owning
resource's helper or a staged change.

## The Fact Kinds

`record_map_fact(kind=..., spec={...})` dispatches on kind; the `mcp_tools`
doc lists every kind's spec fields with the required/optional split, and a
wrong field fails with a targeted error. The kinds:

- `dataset` — datasets and tables. Omit `is_table` on partial updates to
  preserve current typing. Not only for tables: an API endpoint, document
  collection, or model artifact is `is_table=false` plus `extra_types`.
- `column` — a real table-like field, linked with `table_iri`.
- `caveat` — a fact future analysts must not miss. `severity` accepts
  `rc:Minor`, `rc:Moderate`, `rc:Severe` (not confidence terms).
- `relationship` — joins and column-level transforms (below).
- `storage_access`, `physical_layout`, `partition_scheme` — non-secret
  physical facts; field rules live in the `executable_catalog` doc.
- `asset_transform` — dataset-level derivations/aggregations with endpoints,
  conditions, per-output formulas, and tuple grain.
- `analysis_view` — a named logical population with denominators and
  reviewed query snippets; `analysis_view_bundle` writes several views in
  one call (a bulk helper — no grouping resource is created). See
  `analysis_packets`.
- `table_bundle` — one no-I/O write for a reviewed table + columns +
  optional storage/layout. DoxaBase does not read files or infer types;
  supply reviewed values.
- `analysis_packet`, `profile_manifest`, `profiled_parquet_table` — bulk
  reviewed-sidecar ingestion; see `analysis_packets` and `profiling`.

## Value Rules

Resource-valued fields take IRIs or CURIEs, not prose: `rc:EventRow`,
`rc:Parquet`, a project column IRI. Explanation goes in `description`,
caveat text, observations, or patterns. Controlled vocabularies (helpers
reject other values before graph validation):

- `row_semantics`: `rc:EventRow`, `rc:SnapshotRow`, `rc:AggregateRow`,
  `rc:DimensionRow`.
- `schema_stability`: `rc:FixedSchema`, `rc:InferredSchema`,
  `rc:VariableSchema`.
- `layout_verification_status`: `rc:UnverifiedLayout`,
  `rc:GeneratedFromManifestLayout`, `rc:CandidateLayout`,
  `rc:VerifiedByListingLayout`, `rc:VerifiedByQueryLayout`,
  `rc:ContradictedLayout`.
- file formats: `rc:Parquet`, `rc:CSV`, `rc:JSON`, `rc:JPEG`, `rc:PNG`,
  `rc:TIFF`, `rc:GeoTIFF`, `rc:PDF`; define a project `rc:FileFormat` only
  when these lack the reviewed format.
- partition `granularity`: `rc:Daily`, `rc:Hourly`, `rc:Monthly`,
  `rc:ByValue`. `redundant_partition_key` names the partition column
  resource; the placeholder token (`{date}`) stays in `path_template`.

Link partition schemes to datasets from the scheme side
(`partition_scheme` spec `datasets=[...]`); the dataset kind takes no
partition argument. Repeating a column link from both the dataset and the
column side is harmless — identical RDF edges are one fact.

## Relationships

`kind="relationship"` supports `relationship_type` values `foreign_key`,
`shared_identifier`, `derivation`, and `aggregation` (CURIE/IRI aliases such
as `rc:ForeignKey` are accepted and normalized).

Column fields (`from_column`, `to_column`, `identifying_columns`,
`source_columns`, `derived_columns`, `group_by_columns`, aggregate mappings)
accept only existing mapped `rc:Column` resources with concrete
`rc:columnName` evidence — datasets, assets, and fresh IRIs are rejected so
asset relationships cannot be squeezed through column slots. For
column-to-column transforms (`body` → `body_top`): record both columns
first, then a `derivation` with `source_columns`/`derived_columns`.
`derivation_properties` is restricted to `rc:Deterministic`,
`rc:Invertible`, `rc:Lossy`.

For asset-level relationships without columns, use `source_datasets` /
`target_datasets`, or `source_endpoints` / `target_endpoints` when role and
order matter. When the transform needs reviewed filters, per-output formulas,
or tuple output grain, use `kind="asset_transform"`: conditions carry
`condition_kind` (`rc:FilterCondition` / `rc:SelectionCondition`) and
reviewed `expression` text; tuple-grain components take exactly one of
`column`, `dataset`, or `expression`, and `column` must name a real column
resource.

## Grain

For ordinary tabular grain: `row_semantics` for the broad row kind;
`entity_key` / `snapshot_timestamp` for recurring entity snapshots; an
`aggregation` relationship whose `group_by_columns` names every grouping
column for grouped tables. Do not squeeze a composite grain into
`entity_key` — use `rc:AggregateRow` plus the aggregation relationship, and
put tuple-grain wording in the description or a pattern. Non-tabular tuple
grain belongs on `asset_transform` outputs.

## When Not To Write The Map

- A single noticing → `record_observation`.
- Related findings that explain why a fact seems right → `record_pattern`
  first; promotion can follow.
- A tentative or contested interpretation → keep it in observations, claims,
  patterns, or caveats until it is current-best structure.
- Profile output → the profile draft/stage flow in the `profiling` doc, so
  sampled values and vocabulary questions get reviewed instead of silently
  becoming map truth.

Map helpers do not mint project IRIs; prefer stable project namespaces over
generated IDs for durable resources.

Caveat conventions: target the owning **dataset** even for column-specific
caveats (`rc:hasKnownCaveat` is a dataset-level link; name the column in
the description) — this matches every shipped fixture. A caveat may cite
its support directly: `record_map_fact(kind="caveat")` accepts
`evidence_summary` + `evidence_sources` (and optional `evidence_iri`) in
spec, writing a linked `rc:Evidence` resource so "what's the evidence for
this caveat?" is one hop, not an archaeology exercise.
