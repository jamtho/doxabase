# Executable Catalog Metadata

DoxaBase should help an agent move from semantic understanding to a plausible
query plan without turning the RDF graph into a secret store or runtime
configuration file.

The V1 executable-catalog slice records non-secret facts about physical storage:

- file format and compression
- partition/path templates
- storage protocol
- bucket, key prefix, storage root, or local directory
- named endpoint profile
- path-style S3 requirement
- non-secret credential reference
- intended access mode
- layout/path verification status and notes

## What Belongs In The Graph

Put facts in the graph when they are useful for planning, review, or handoff and
are safe to share with project collaborators:

- `rc:hasStorageAccess` links a dataset/table to a storage access description.
- `rc:storageProtocol` says whether access is local filesystem,
  S3-compatible object storage, HTTPS, or database-backed.
- `rc:storageRoot`, `rc:bucketName`, `rc:keyPrefix`, and `rc:pathTemplate`
  describe where data lives.
  For `storage_protocol="rc:DatabaseStorage"`, storage-access-owned
  `path_templates` are database relation identifiers such as `schema.table`;
  `storage_root` is the connection reference, not a file/object root.
- `rc:locationKind` says whether a root names an exact `object`/location,
  `directory`, `prefix`, or `connection`. Root-only query targets are executable
  candidates only when this is `object`; broader roots need path templates.
  The authoring helper accepts `location_kind="bucket"` as a convenience for
  S3-shaped bucket/key-prefix routes, but stores the graph value as `prefix`.
  Do not use a value such as `local_path`: local filesystem is a
  `storageProtocol`, while `locationKind` describes the shape of the recorded
  root.
- `rc:endpointProfile` names a locally resolved endpoint profile, such as
  `local-minio`.
- `rc:pathStyleAccess` records an S3-compatible access quirk that query engines
  often need.
- `rc:credentialReference` names credential material without storing it. Use
  non-secret markers such as `profile:<name>`, `env:<VAR_NAME>`, or
  `external:intentionally-unrecorded`.
- `rc:accessMode` records whether the intended use is read-only or read-write.
- `rc:compressionCodec` records file compression on a physical layout.
- `rc:layoutVerificationStatus` records whether path/layout metadata is
  unverified, generated, candidate, verified by listing/query, or contradicted.
- `rc:layoutVerificationNote` carries a short note about what has or has not
  been checked.

These terms are intentionally boring. They give agents enough structure to
generate a DuckDB/S3/local-file plan, compare datasets, and ask good follow-up
questions without pretending DoxaBase can execute every environment by itself.

Agents can author these facts without hand-writing RDF:

- `doxabase.record_map_storage_access` for storage protocol/root/profile facts.
- `doxabase.record_map_physical_layout` for file format and compression facts.
- `doxabase.record_map_partition_scheme` for partition columns, granularity,
  path templates, and path-specific verification notes.

## What Must Stay Outside The Graph

Do not put secrets in DoxaBase:

- access keys
- secret keys
- bearer tokens
- passwords
- private connection strings
- user-specific absolute paths that should not travel with the project

Use `rc:credentialReference` or `rc:endpointProfile` to point at local runtime
configuration instead. The graph can say `profile:<name>`,
`env:<VAR_NAME>`, or `external:intentionally-unrecorded`; the user's machine or
agent runtime decides how the marker resolves, and the last form means the
credential exists outside the graph or is intentionally unavailable.
Before sharing exports, run `doxabase.export_preflight` for the export kind you
intend to create. It covers RDF graph roles and, for handoff bundles, stored
revision snapshot rows before any path is chosen or artifact is written. Treat
`decision="block"` as a stop-and-review signal: exports remain faithful RDF/JSON
and are not redacted automatically. When the preflight is scanner-clean, still
pass `fail_on_sensitive=true` to the final export so DoxaBase raises before
writing if selected graph roles or snapshot rows changed. Use
`doxabase.scan_sensitive_literals` when you need the detailed redacted graph-only
scan.
This preflight does not decide whether non-secret paths are appropriate to share:
local paths, object-store URIs, endpoint URLs, and relative paths are preserved
unless you keep them out of the graph or replace them with collaborator-safe
references before export.

## How Agents Should Use It

1. Call `doxabase.describe_dataset` for the target dataset.
2. Call `doxabase.describe_query_context` when you want a compact physical
   planning projection with readiness and an `issues` list for missing, risky,
   or informational physical metadata.
3. Read `query_target_decision` first. Its zero-based `candidate_index` points
   at the candidate to inspect first, while each candidate's
   `candidate_selector` is the stable value to pass back into
   `draft_query_plan` after review. `status` tells whether that target is
   ready, blocked only by sibling context, directly review-only, or absent.
4. Use `query_target_candidates` as supporting path/template cards. They preserve
   whether a template came from the dataset, a partition scheme, storage access,
   or a storage-root-only location, and they compose best-effort paths without
   resolving endpoint profiles or credentials. They also expose storage-access
   `route_roles`, which are the reviewed route-intent facts to use when deciding
   between production/current/canonical, sample, archive, or backfill routes.
   `template_source="storage_access_location"` means no path template was
   recorded, but the storage root itself is the candidate location; treat it as
   executable only when `location_kind="object"` confirms the root names the
   dataset object/location rather than a directory, prefix, or connection that
   still needs a template.
   When an exact object root appears beside dataset or partition templates,
   prefer the `storage_access_location` candidate for that object route; any
   template-appended candidate is review-only with
   `storage_object_location_has_path_template` unless the storage root is
   remodelled as a directory or prefix.
5. Read `physical_layouts`, `partition_schemes`, `path_templates`, and
   `storage_accesses` together when you need the raw graph facts behind a
   candidate.
6. Check `layout_verification_status` and `layout_verification_note` on the
   dataset and on relevant layout, partition, and storage resources. When a
   status is not recorded for otherwise usable path/layout metadata,
   `describe_query_context().issues` reports an informational
   `verification_status_not_recorded` issue.
7. Combine storage root or bucket/prefix facts with the dataset path template
   only when the verification status and notes make that reasonable. Complete
   templates such as `s3://...` should still match the declared storage protocol
   and any recorded bucket/prefix; if they do not, query target candidates are
   orientation-only.
8. Check `analysis_warnings` and caveats before trusting aggregations or
   interpretations.
9. Use `doxabase.draft_query_plan` when you want a non-executed DuckDB-oriented
   handoff object from the selected query target, structured binding
   requirements, storage hints, review gate, issues, and caveats. Binding rows
   tell you when DoxaBase has not inferred derivations or runtime values. It
   does not resolve credentials, endpoint profiles, object existence, or execute
   SQL. If selected S3-compatible access is missing endpoint, credential, and
   region metadata, `plan.storage_environment.runtime_resolution_required`
   remains true even though those fields are absent; resolve or record that
   runtime context before execution. Treat
   `plan.review_gate.ready_for_execution_attempt` as the compact "no recorded
   review or runtime-resolution blocker" signal before considering a local
   execution attempt. When it is false,
   `plan.review_gate.primary_execution_attempt_blocking_reason_code` names the
   first ordered execution-attempt blocker, or `None` if no blocker remains.
   Read `plan.handoff_summary` first when preparing a compact handoff report; it
   copies the selected candidate index/note, scan function, URI or relation
   identifier, readiness gate booleans, blocker codes, required bindings, issue
   codes, warning/caveat counts, and peer ready/direct-clean candidate indexes.
   Use `plan.handoff_kind` for first-pass machine routing:
   it distinguishes review-required drafts, runtime-resolution work, database
   relation handoffs, URI-template binding work, and execution-attempt-ready
   local/file/object drafts.
   If the automatic candidate is direct-clean but stale sibling storage or
   partition metadata blocks the context, pass `candidate_selector` or
   `storage_access_iri` with `allow_context_blocked_candidate=True` to draft the
   selected route while preserving the automatic decision and context blocker
   audit fields. A selectorless automatic call with that flag records the
   allowance but keeps the context review gate when the blocker belongs to
   sibling candidate metadata.
   Read `plan.scan.dataset_verification_note`, `plan.scan.template_lineage`,
   and the scan source verification fields before trusting a path. In the AIS
   fixture, `DailyIndex` currently shares the broadcast partition template and
   is intentionally review-gated until storage listing or query evidence
   confirms the real index layout. For database-backed storage, read
   `plan.scan.relation_identifier` and `plan.scan.connection_reference`;
   `plan.scan.uri_template` is reserved for file/object scan handoffs.
10. If a query is run, record the result or failure with
   `doxabase.record_observation` and supporting evidence.

## Copyable Helper Recipe

Use this shape when a scratch or project handoff needs one executable-catalog
slice without hand-authored RDF. Put a relative path template on either the
storage access or the partition scheme when that resource owns the verification
note. Duplicate a template only when both resources really need to carry their
own provenance.

```python
import json
from pathlib import Path

from doxabase import DoxaBase, to_dict

db = DoxaBase.create(Path("/tmp/doxabase-catalog-recipe.sqlite"), overwrite=True)
base = "https://example.test/catalog#"
table = f"{base}RetailEvents"
event_id = f"{base}retail_events__event_id"
event_date = f"{base}retail_events__event_date"
storage = f"{base}retail_events_storage"
layout = f"{base}retail_events_parquet_layout"
partition = f"{base}retail_events_daily_partition"
caveat = f"{base}retail_events_sparse_revenue"

db.record_map_column(event_id, column_name="event_id", table_iri=table)
db.record_map_column(event_date, column_name="event_date", table_iri=table)
db.record_map_storage_access(
    storage,
    label="retail events local storage",
    route_roles=["rc:SampleRoute"],
    storage_protocol="rc:LocalFilesystemStorage",
    access_mode="rc:ReadOnlyAccess",
    location_kind="directory",
    storage_root="/tmp/warehouse",
    datasets=[table],
    layout_verification_status="rc:CandidateLayout",
    layout_verification_note="Warehouse root came from a handoff note; verify listing.",
)
db.record_map_physical_layout(
    layout,
    file_format="rc:Parquet",
    compression_codec="rc:ZstdCompression",
    datasets=[table],
    layout_verification_status="rc:CandidateLayout",
)
db.record_map_partition_scheme(
    partition,
    path_template="retail/events/event_date={date}/*.parquet",
    partition_columns=[event_date],
    redundant_partition_key=event_date,
    granularity="rc:Daily",
    datasets=[table],
    layout_verification_status="rc:CandidateLayout",
    layout_verification_note="Path template came from a handoff note; verify listing.",
)
db.record_map_caveat(
    caveat,
    description="gross_revenue_cents is populated only for purchase events.",
    severity="rc:Moderate",
    targets=[table],
)
db.record_map_dataset(
    table,
    label="Retail events",
    is_table=True,
    row_semantics="rc:EventRow",
    entity_key=event_id,
    schema_stability="rc:InferredSchema",
    columns=[event_id, event_date],
    storage_accesses=[storage],
    physical_layouts=[layout],
    caveats=[caveat],
    layout_verification_status="rc:CandidateLayout",
)

dataset = db.describe_dataset(table)
query = db.describe_query_context(table)
plan = db.draft_query_plan(table)
slice_ = db.describe_context_slice([table], profile="dataset_brief")
validation = db.validate_graph(scope="all")

print(
    json.dumps(
        to_dict(
            {
                "dataset": dataset,
                "query_decision": query.query_target_decision,
                "review_gate": plan.review_gate,
                "slice_routes": slice_.route_counts,
                "validation_conforms": validation.conforms,
            }
        ),
        indent=2,
    )
)
```

`redundant_partition_key` names a resource, usually the partition column IRI or
CURIE. The placeholder token stays in `path_template`; do not pass `"date"` or
`"event_date"` as the redundant key unless you have deliberately minted that as
a resource identifier.

Tiny direct Python scratch example:

```python
import json
from pathlib import Path

from doxabase import DoxaBase, to_dict

db = DoxaBase.create(Path("/tmp/doxabase-query-context.sqlite"), overwrite=True)
db.import_trig("examples/manifest-prototype-rc/ais.trig")

context = db.describe_query_context(
    "https://richcanopy.org/example/manifest/ais#DailyBroadcasts",
)
plan = db.draft_query_plan(
    "https://richcanopy.org/example/manifest/ais#DailyBroadcasts",
)
payload = to_dict(context)
plan_payload = to_dict(plan)
print(
    json.dumps(
        {
            "readiness": payload["readiness"],
            "issues": payload["issues"],
            "analysis_warnings": payload["analysis_warnings"],
            "draft_scan": plan_payload["scan"],
            "binding_requirements": plan_payload["binding_requirements"],
            "review_gate": plan_payload["review_gate"],
        },
        indent=2,
    )
)
```

## Current Limits

This is catalog metadata, not a query engine. `describe_query_context` projects
the relevant graph facts and gaps, and `draft_query_plan` packages the selected
candidate into a non-executed review draft. DoxaBase still does not resolve
runtime credentials, endpoint profile details, object existence, or execute
queries.

For now, the value is handoff and planning: the next agent can see where the data
is, how it is physically shaped, what local profile to use, which layout claims
need verification, and which caveats should travel with generated work.

When an external runtime does execute a reviewed plan, preserve the result or
failure with `record_query_result()` rather than stuffing all context into a
generic note. For a local CSV smoke test, a typical shape is:

```python
result = db.record_query_result(
    summary="Orders CSV paid-count query returned two rows.",
    observed_asset="https://example.test/project#Orders",
    execution_status="succeeded",
    engine="python-csv",
    query_source_path="queries/orders_paid_count.sql",
    query_hash="sha256:...",
    result_sources=["/tmp/orders-paid-count.json"],
    scanned_source_handles=["/data/orders.csv"],
    sample_size=3,
    sample_scope="All rows in the reviewed local Orders CSV.",
    sample_method="External read-only aggregate after draft_query_plan.",
)
```

Use `result_sources` for arbitrary result-table or aggregate payloads such as
grouped counts, sums, or JSON output. Use `scanned_source_paths` for non-secret
inputs that should become data-sample source spans, and use
`scanned_source_handles` for reviewed runtime handles. For a database relation
handoff, record a reviewed relation handle such as
`warehouse-prod:mart.orders` rather than forcing the value into a fake file
path. Later query-context repair hints can turn scanned S3 URIs, local paths,
and database handles into review-only storage route candidate arguments; review
them before staging or drafting an overlay. The structured `sample_size`,
`row_count`, `null_count`, `distinct_count`, value-frequency, and metric fields
are profile-shaped observation fields; only fill them when their meaning is
clear in `summary`, `sample_scope`, and `sample_method`. For filtered or grouped
aggregate query results, keep counts such as "six scanned source rows", "two
paid rows", or grouped totals in the result payload unless the value is
genuinely profile evidence for a population.

For a disposable exact local CSV trial, use local object storage plus
`layout_verification_status="rc:VerifiedByListingLayout"` after checking the
path and header. `rc:CandidateLayout` is appropriate for unverified guesses, but
it can keep `draft_query_plan` review-gated. After an execution-ready draft and
an external full-scan aggregate, a reviewed assertion draft such as
`rc:rowCountSnapshot` can be justified by the query result evidence without
putting aggregate-only counts into profile fields.

For failed attempts, set `execution_status="failed"` and include
`failure_summary` plus a query source or result/log source; do not pass row,
null, distinct, value-frequency, or metric fields.
