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
Resource-valued fields across these helpers expect IRIs or CURIEs, not
descriptive prose. Pass terms such as `rc:EventRow`, `rc:FixedSchema`,
`rc:Parquet`, or a project IRI for columns, datasets, caveats, storage access,
and relationship endpoints. Put ordinary explanation in `description`,
`layout_verification_note`, caveat text, observations, or patterns.
For partition schemes, `granularity` is SHACL-checked against
`rc:Daily`, `rc:Hourly`, `rc:Monthly`, and `rc:ByValue`; use a project term
only after extending the project shapes accordingly.

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
map. The draft rows carry sample scope, confidence, helper arguments, and
metric advisories so the agent can decide which recommendations to accept.

Use `stage_profile_map_updates(..., accepted_recommendation_indexes=[...])` when
accepted profile-derived changes should be reviewed before apply. It stages one
grouped helper-equivalent map revision, including multi-triple dataset and
column shells, so applying one accepted profile batch does not create sibling
staged revisions that immediately drift after the first apply.
If the draft has no recommendations and `metric_advisory_count > 0`, handle it
as advisory-only: follow the advisory suggested calls for vocabulary/context
review and do not call `stage_profile_map_updates`. Advisory rows are not
map-update recommendations, and no-op advisory staging is deferred.
An accepted index is still routed through guardrails: it may be `staged` or
`skipped`, while `not_selected` means the draft row was not accepted for that
call. Check `status_counts` first, then item reasons.

Use direct map helpers only when immediate mutation is intended. Treat sampled
row-count recommendations conservatively: the staging helper skips them by
default unless `allow_sampled_row_count_updates=True` is supplied because the
sample scope is the durable population. Metric advisories are vocabulary-review
prompts, not automatic map facts.

## Example

```python
table = "https://example.test/enron#eml_messages"
doc_id = "https://example.test/enron#eml_messages__doc_id"
caveat = "https://example.test/enron#caveat_body_processing_lossy"
storage = "https://example.test/enron#local_parquet_access"

db.record_map_storage_access(
    iri=storage,
    label="local parquet access",
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

Aggregation relationships can carry `source_dataset`, `target_dataset`,
`group_by_columns`, and `aggregated_columns`. Each `aggregated_columns` entry
uses `target_column`, `source_columns`, optional `aggregation_function`, and
optional `within_group_ordering`:

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

## Grain And Row Units

DoxaBase does not yet have a single generic `grain` helper or ontology pattern.
Use the existing map signals together:

- `rowSemantics` for the broad row kind: event, snapshot, aggregate, or
  dimension.
- `entityKey` and `snapshotTimestamp` for recurring entity snapshots.
- `record_map_relationship(..., relationship_type="aggregation")` with
  `group_by_columns` when a target dataset has one row per source group.
- `aggregated_columns` when target columns are computed from source columns.
- Caveats when the row unit is only approximate, inferred, or source-dependent.

If an agent needs a richer grain concept, it should say so explicitly and stage
or document the modelling hunch rather than forcing it into a misleading
current helper. This is an active design area for field trials.

## Limits

These helpers do not promote patterns automatically. If a pattern supports a
straightforward current-best map fact, record the map fact with the helper and
keep the pattern linked via `rc:mapImplication`. If the promotion should remain
reviewable or needs caller-authored RDF beyond the map helper surface, use
`doxabase.stage_pattern_promotion` so the selected pattern and its support links
travel with the staged graph change.

Map helpers also do not mint project IRIs. Prefer stable project namespaces over
generated IDs for durable map resources.
