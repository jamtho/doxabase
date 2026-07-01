# Map Authoring

Use the `map` graph for current-best project structure: datasets, tables,
columns, caveats, storage access, and relationships that future agents should
start from.

Map facts are not necessarily eternal. A row-count snapshot, inferred join, or
known caveat can be revised. The point is that the project currently treats the
fact as useful operating context, ideally with observations, patterns, or
evidence explaining why.

## Helpers

Use first-class map helpers for routine map writes:

- `doxabase.record_map_dataset`
- `doxabase.record_map_column`
- `doxabase.record_map_caveat`
- `doxabase.record_map_storage_access`
- `doxabase.record_map_physical_layout`
- `doxabase.record_map_partition_scheme`
- `doxabase.record_map_relationship`

These helpers write to `map` and update the common predicates they own for a
resource. They avoid hand-authored TriG for ordinary table/column/caveat/storage
facts, while still leaving the graph open for project-specific RDF.

When you supply helper-owned fields on the resource being recorded, those
same-subject predicates are replaced for that resource. Incoming convenience
links are different: arguments such as `record_map_caveat(targets=[...])`,
`record_map_storage_access(datasets=[...])`, and
`record_map_column(table_iri=...)` add links from other resources and do not
prune older incoming links. To narrow those links, update the owning dataset or
table helper where applicable, stage a reviewed assertion change, or use
`replace_graph_triples()` for exact graph maintenance.
For scalar helper-owned literal fields, omitting a parameter preserves existing
values, while passing an explicit empty string includes that predicate in the
replacement set and clears it.

For `record_map_dataset`, omit `is_table` on partial updates when you want to
preserve the current dataset/table typing. Pass `is_table=True` or
`is_table=False` when you intentionally want to set that typing.
You can link columns either with `record_map_dataset(columns=[...])` or with
`record_map_column(table_iri=...)`. Supplying the same link through both helpers
is harmless; DoxaBase treats repeated identical RDF edges as one graph fact in
descriptions.
Link partition schemes to datasets with
`record_map_partition_scheme(datasets=[...])`; `record_map_dataset` does not
take a `partition_schemes` argument.
Resource-valued fields across these helpers expect IRIs or CURIEs, not
descriptive prose. Pass terms such as `rc:EventRow`, `rc:FixedSchema`,
`rc:Parquet`, `rc:PNG`, `rc:GeoTIFF`, or a project IRI for columns, datasets,
caveats, storage access, and relationship endpoints. Common base file-format
terms include `rc:Parquet`, `rc:CSV`, `rc:JSON`, `rc:JPEG`, `rc:PNG`,
`rc:TIFF`, `rc:GeoTIFF`, and `rc:PDF`; define a project-local
`rc:FileFormat` only when the base vocabulary lacks the reviewed format. Put
ordinary explanation in `description`, `layout_verification_note`, caveat text,
observations, or patterns.
`schema_stability` accepts `rc:FixedSchema`, `rc:InferredSchema`, or
`rc:VariableSchema`. `layout_verification_status` accepts
`rc:UnverifiedLayout`, `rc:GeneratedFromManifestLayout`, `rc:CandidateLayout`,
`rc:VerifiedByListingLayout`, `rc:VerifiedByQueryLayout`, or
`rc:ContradictedLayout`. Caveat `severity` accepts `rc:Minor`,
`rc:Moderate`, or `rc:Severe`; do not use confidence terms such as
`rc:HighConfidence` or ad hoc values such as `rc:High`.
`row_semantics` accepts `rc:EventRow`, `rc:SnapshotRow`, `rc:AggregateRow`, or
`rc:DimensionRow`. For partition schemes, `granularity` accepts `rc:Daily`,
`rc:Hourly`, `rc:Monthly`, and `rc:ByValue`; the helper rejects other values
before graph validation. `redundant_partition_key` is also a resource-valued
field, usually the partition column IRI or CURIE. Do not pass the literal
template placeholder such as `"event_date"` or `"date"`; keep that token in
`path_template`.

Map helpers are not only for tables. For an API endpoint, document collection,
message stream, model artifact, or other non-tabular asset, call
`record_map_dataset(..., is_table=False, extra_types=[...])` with project
types when useful, then attach caveats, storage or access metadata, evidence,
claims, observations, and patterns as usual. Use `record_map_column` only for
real table-like fields. For non-tabular handoffs, prefer
`describe_resource()` or `describe_context_slice(profile="deep_lore")`; direct
query-planning helpers return `not_applicable_non_tabular_asset` unless a
separate queryable table route has been modeled.

## When To Use Map Helpers

Use map helpers when you are comfortable saying:

- this table or dataset exists in the current project model;
- this column is part of a table and has this physical or semantic type;
- this caveat should be visible whenever a future agent inspects the dataset;
- this storage access metadata is non-secret and useful for planning;
- this relationship is part of the current operating model, even if inferred.

Use `record_observation` for a single noticing. Use `record_pattern` when
several noticings or claims explain why a map fact seems right. Then use map
helpers to systematize the current-best facts.

## Profile-Derived Updates

When a shared-evidence profile run suggests map changes, call
`describe_profile_run()` and `draft_profile_map_updates()` before mutating the
map. The draft rows carry sample scope, confidence, helper arguments,
`default_stageable`, `default_skip_reason`, and metric advisories so the agent
can decide which recommendations to accept.
Duplicate groups are explicit: when repeated profile observations produce the
same review row, accept one representative index unless the siblings need
different modelling judgement. For `unmapped_profiled_column` shell rows, the
duplicate group is keyed to the helper mutation rather than profile-specific
sample or null details, so one representative stages one map shell with all
supporting profile observations. Prefer the draft's
`suggested_next_action_groups`: `profile_map_updates` starts from representative
indexes whose rows are `default_stageable`, `profile_scalar_conflict_review`
surfaces mutually exclusive choose-one scalar options, and
`metric_vocabulary_review` / `profile_type_review` keep advisories out of the
map-staging batch. Use `advisory_followthrough_plan` for the compact metric/type
next-step menu before staging vocabulary, type assertions, or fallback
systematisations. Sampled row-count representatives stay visible for review but
require an explicit override call. Same-evidence scalar conflicts stay visible
too, but the default map-staging action omits them; choose at most one observed
row-count or nullable value from the `profile_scalar_conflict_review` lane or
`scalar_conflict_groups[].options[]` after reading the supporting profile
observations. After one scalar-conflict value has been applied, sibling values
from the same evidence should still route through scalar-conflict review; do not
stage them as ordinary map updates just because the mechanical apply check would
be ready.
Profile type findings are not accepted `stage_profile_map_updates`
recommendation indexes. `physical_type` and `value_type` are still persisted on
profile observations when `update_map_column=False`; `draft_profile_map_updates`
surfaces them as `type_advisories` with context, pattern, and focused staged
assertion suggestions. Review those advisories before turning type evidence into
current map facts. The suggested context-slice action only seeds observed type
resources that already exist, so undefined project value types may be absent
from that context call while still appearing in the pattern and staged assertion
arguments. If you follow the suggested `record_pattern` action first,
copy the returned `pattern_iri` into the following
`stage_map_assertion_change(..., supporting_patterns=[...])` call.
Treat the grouped `profile_type_review` lane as a representative action queue:
its labels may repeat across advisory groups. For automation, iterate
`representative_type_advisory_indexes` first and use each representative
advisory's `suggested_next_actions`; read its `duplicate_group_key` /
`type_advisory_index` / `duplicate_advisory_indexes` when you need the grouped
sibling rows. Metric vocabulary review has the same shape through
`representative_metric_advisory_indexes` and `metric_advisory_index`. This keeps
the column, observed types, metric vocabulary, and duplicate observation support
clear without making scripts reconstruct groups manually.
That staged assertion also merges related assertion-support lore, so the final
revision may include both the pattern you just recorded and patterns that
directly target, imply, or claim-support the column or assertion. Same-profile
observation or metric-vocabulary patterns that do not directly support the
assertion stay reachable through context slices instead of becoming direct
`supporting_patterns`.

Use `stage_profile_map_updates(..., accepted_recommendation_indexes=[...])` when
accepted profile-derived changes should be reviewed before apply. It stages one
grouped helper-equivalent map revision, including multi-triple dataset and
column shells, so applying one accepted profile batch does not create sibling
staged revisions that immediately drift after the first apply.
If the draft has no recommendations and metric or type advisories are present,
handle it as advisory-only: follow the grouped advisory calls for vocabulary,
context, or type review and do not call `stage_profile_map_updates`. Advisory
rows are not map-update recommendations, and no-op advisory staging is deferred.
After applying unmapped column shells, rerun
`draft_profile_map_updates(dataset_iri, evidence_iri)` before treating the
profile pass as advisory-only. The newly map-present column may surface ordinary
map recommendations, such as nullability, that should go through
`profile_map_updates` first. When `stage_profile_map_updates` staged the shell,
its `suggested_next_actions` includes this rerun after the staged revision
apply-check action.
An accepted index is still routed through guardrails: it may be `staged` or
`skipped`, while `not_selected` means the draft row was not accepted for that
call. Accepted sampled row counts can be skipped by default, and accepted
same-evidence scalar conflicts are skipped when the same call chooses multiple
values for one row-count or nullable assertion. Check `status_counts` first,
then item reasons. Those counts describe the full draft, not only the accepted
indexes in the call; a one-option scalar conflict stage can legitimately report
many `not_selected` rows.
When a profile-derived change is backed by synthesized lore, pass
`supporting_claims`, `supporting_patterns`, or extra `revision_anchors`; these
links are recorded on the staged revision for later review.
The default `profile_map_updates` suggested action pre-fills
`supporting_patterns` when same-evidence profile patterns clearly overlap the
profile run's dataset or recommended map resources, while skipping patterns that
mention observed physical/value type resources from the profile type-review
lane. Keep the auto-filled patterns unless review shows one is unrelated to the
accepted map changes. Profiled-column-only type rationale belongs in the
`profile_type_review` lane unless you explicitly pass it as support to a focused
type assertion change.
When reviewing the staged revision, treat `supporting_patterns` as direct
rationale for the map patch. `impacts[].related_patterns` is broader nearby
context and may include metric/type advisory lore that was intentionally kept
out of direct staged-revision support.
Representative duplicate staging preserves every grouped profile observation as
staged-revision support, so accepting one duplicate row does not discard sibling
evidence.
Mixed followthroughs are expected: a duplicate full run may stage representative
map updates, route metric vocabulary through `stage_pattern_promotion`, and
route type findings through `record_pattern` plus
`stage_map_assertion_change(..., supporting_patterns=[...])`; a sampled run in
the same capsule still skips row-count updates by default while allowing other
stageable recommendations.

Use direct map helpers only when immediate mutation is intended. Treat sampled
row-count recommendations conservatively: the staging helper skips them by
default unless `allow_sampled_row_count_updates=True` is supplied because the
sample scope is the durable population. Draft rows preview that default with
`default_stageable=False` and a skip reason. Metric and type advisories are
review prompts, not automatic map facts; in draft results, use their grouped
lanes separately from `profile_map_updates`. In staging results, follow
`metric_advisory_suggested_next_actions` separately from the map revision's
`suggested_next_actions`, and follow `type_advisory_suggested_next_actions`
for type-finding review or focused type assertions.

Typical mixed staging after a sampled profile run:

```python
staged = db.stage_profile_map_updates(
    dataset,
    evidence,
    accepted_recommendation_indexes=[0, 1, 2],
)
assert 0 in staged.skipped_recommendation_indexes
assert staged.status_counts["staged"] == 2
```

Here recommendation `0` is a sampled row-count update, while `1` and `2` are
accepted column updates that still become one reviewable staged revision.

## Example

```python
table = "https://example.test/enron#eml_messages"
doc_id = "https://example.test/enron#eml_messages__doc_id"
caveat = "https://example.test/enron#caveat_body_processing_lossy"
storage = "https://example.test/enron#local_parquet_access"

db.record_map_storage_access(
    iri=storage,
    label="local parquet access",
    route_roles=["rc:SampleRoute"],
    storage_protocol="rc:LocalFilesystemStorage",
    access_mode="rc:ReadOnlyAccess",
    location_kind="directory",
    storage_root="/home/james/github.com/jamtho/enron-emails",
    path_templates=["data/parquet/*.parquet"],
    datasets=[table],
)

db.record_map_caveat(
    iri=caveat,
    label="body processing lossy",
    description="body_top is cleaned sender-new text, not raw email text.",
    severity="rc:Moderate",
    targets=[table],
)

db.record_map_dataset(
    iri=table,
    label="EML messages",
    description="One row per parsed raw .eml message.",
    is_table=True,
    path_templates=["data/parquet/eml_messages.parquet"],
    row_semantics="rc:EventRow",
    entity_key=doc_id,
    schema_stability="rc:FixedSchema",
    caveats=[caveat],
    storage_accesses=[storage],
)

db.record_map_column(
    iri=doc_id,
    table_iri=table,
    column_name="doc_id",
    physical_type="rc:Varchar",
    value_type="https://example.test/enron#DocId",
    nullable=False,
)
```

Use `route_roles` on storage access records when a dataset has multiple viable
routes. Built-in reviewed roles include `rc:ProductionRoute`, `rc:CurrentRoute`,
`rc:CanonicalRoute`, `rc:SampleRoute`, `rc:ArchiveRoute`, and
`rc:BackfillRoute`; define project-local `rc:RouteRole` terms when those are too
coarse. Query target candidates inherit these roles so agents can choose reviewed
production/current routes without parsing labels or path names.

## Relationships

`record_map_relationship` currently supports:

- `relationship_type="foreign_key"`
- `relationship_type="shared_identifier"`
- `relationship_type="derivation"`
- `relationship_type="aggregation"`

Use `foreign_key` for parent/child column relationships, whether declared
upstream or inferred by checks. Use `shared_identifier` when several columns
carry IDs from the same logical population. Use `derivation` for transformed
columns such as cleaned text, normalized subjects, or generated features. Use
`aggregation` for grouped summaries, rollups, and index tables that compute
target columns from source columns.

Relationship column fields are for column resources. The helper rejects known
data assets, datasets, or tables in `from_column`, `to_column`,
`identifying_columns`, `source_columns`, `derived_columns`, `group_by_columns`,
and aggregate mapping column fields.

For no-column asset-level derivation or aggregation, use `source_datasets` and
`target_datasets` without column fields. The singular `source_dataset` and
`target_dataset` arguments are still accepted as compatibility shortcuts for
one endpoint each. Use `source_endpoints` and `target_endpoints` when endpoint
role or precedence matters:

```python
record_map_relationship_tool(
    db,
    iri="ex:masks_from_images_labels_and_sidecars",
    relationship_type="derivation",
    source_endpoints=[
        {"dataset": "ex:RawImages", "role": "primary image input", "order": 1},
        {"dataset": "ex:LabelSchema", "role": "class-id lookup", "order": 2},
        {"dataset": "ex:Sidecars", "role": "geometry sidecar input", "order": 3},
    ],
    target_endpoints=[
        {"dataset": "ex:SegmentationMasks", "role": "indexed mask output"},
    ],
)
```

Endpoint specs still write ordinary `sourceDataset` / `targetDataset` edges for
compatibility, while `describe_dataset` exposes the ordered `source_endpoints`
and `target_endpoints` lists. When the relationship needs reviewed filters,
selection rules, per-output formulas, or tuple output grain, use
`record_map_asset_transform` rather than packing those details into prose.

Column-shaped aggregation relationships can carry `source_dataset`,
`target_dataset`, `group_by_columns`, and `aggregated_columns`. Each
`aggregated_columns` entry uses `target_column`, `source_columns`, optional
`aggregation_function`, and optional `within_group_ordering`:

```python
record_map_relationship_tool(
    db,
    iri="ex:attachment_counts_by_message",
    relationship_type="aggregation",
    source_dataset="ex:Attachments",
    target_dataset="ex:AttachmentCounts",
    group_by_columns=["ex:attachment_parent_doc_id"],
    aggregated_columns=[
        {
            "target_column": "ex:attachment_count",
            "source_columns": ["ex:attachment_parent_doc_id"],
            "aggregation_function": "rc:Count",
        },
    ],
)
```

For conditional asset-level aggregates or derivations, use
`record_map_asset_transform` with `conditions` and `outputs`. Conditions carry a
controlled `condition_kind` of `rc:FilterCondition` or `rc:SelectionCondition`
and reviewed `expression` text; outputs carry `target_dataset`, optional
`formula`, optional `function`, optional linked `conditions`, and optional
`tuple_grain`:

```python
record_map_asset_transform_tool(
    db,
    iri="ex:mosaic_from_bags_and_navigation",
    relationship_type="derivation",
    source_endpoints=[
        {"dataset": "ex:RawSonarBags", "role": "primary sonar input", "order": 1},
        {"dataset": "ex:NavigationCorrections", "role": "navigation input", "order": 2},
    ],
    target_datasets=["ex:SurveyMosaic"],
    conditions=[
        {
            "iri": "ex:valid_navigation_filter",
            "condition_kind": "rc:FilterCondition",
            "expression": "only pings with reviewed navigation fixes",
        },
    ],
    outputs=[
        {
            "target_dataset": "ex:SurveyMosaic",
            "formula": "grid corrected ping intensities into a GeoTIFF mosaic",
            "conditions": ["ex:valid_navigation_filter"],
            "tuple_grain": {
                "components": [
                    {"dataset": "ex:RawSonarBags", "role": "source survey"},
                    {"expression": "mosaic tile coordinate", "role": "tile"},
                ],
            },
        },
    ],
)
```

Derivation relationships can name `source_columns`, `derived_columns`,
`derivation_function`, and `derivation_properties`. Treat those as relationship
level context, not per-output formulas. `derivation_properties` is restricted to
the current shared RC values `rc:Deterministic`, `rc:Invertible`, and `rc:Lossy`;
stage project-specific transform properties through ontology/systematisation
instead of passing them to the map helper. When a derived column's exact
expression or source-to-target mapping matters, record a claim/pattern or stage
a richer project RDF framing instead of implying the helper captured the
formula.

## Grain And Row Units

Use the existing map signals for ordinary tabular grain:

- `rowSemantics` for the broad row kind: event, snapshot, aggregate, or
  dimension.
- `entityKey` and `snapshotTimestamp` for recurring entity snapshots.
- `record_map_relationship(..., relationship_type="aggregation")` with
  `group_by_columns` when a target dataset has one row per source group.
- `aggregated_columns` when target columns are computed from source columns.
- Caveats when the row unit is only approximate, inferred, or source-dependent.

For aggregate datasets with tuple grain, such as one row per
`(customer_id, order_date)`, prefer `row_semantics="rc:AggregateRow"` plus an
aggregation relationship whose `group_by_columns` names every grouping column.
Do not squeeze a composite grain into `entity_key`; use `entity_key` only when
one map column really behaves as the row identity. Put the tuple-grain wording
in the dataset description or a pattern when future agents must not miss it.

For non-tabular output assets or tuple grain that is not honestly a column list,
use `record_map_asset_transform(..., outputs=[{"tuple_grain": ...}])`.
Tuple-grain components accept exactly one of `column`, `dataset`, or
`expression`. `column` must name a real column resource; known datasets/tables
are rejected in that slot so agents do not mint fake columns for assets.
`describe_dataset` exposes direct `tuple_grains` on the output asset and nested
`transform_outputs[].tuple_grain` on the relationship.

## Limits

These helpers do not promote patterns automatically. If a pattern supports a
straightforward current-best map fact, record the map fact with the helper and
keep the pattern linked via `rc:mapImplication`. If the promotion should remain
reviewable or needs caller-authored RDF beyond the map helper surface, use
`doxabase.stage_pattern_promotion` so the selected pattern and its support links
travel with the staged graph change.

Map helpers also do not mint project IRIs. Prefer stable project namespaces over
generated IDs for durable map resources.
