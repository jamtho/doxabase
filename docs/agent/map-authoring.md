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
- `doxabase.record_map_relationship`

These helpers write to `map` and update the common predicates they own for a
resource. They avoid hand-authored TriG for ordinary table/column/caveat/storage
facts, while still leaving the graph open for project-specific RDF.

For `record_map_dataset`, omit `is_table` on partial updates when you want to
preserve the current dataset/table typing. Pass `is_table=True` or
`is_table=False` when you intentionally want to set that typing.

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

## Limits

These helpers do not yet promote patterns automatically. If a pattern supports a
map change, record the map fact with the helper and keep the pattern linked via
`rc:mapImplication` for now. Future promotion tools should make that relationship
explicit and mark supporting claims or patterns as promoted.

Map helpers also do not mint project IRIs. Prefer stable project namespaces over
generated IDs for durable map resources.
