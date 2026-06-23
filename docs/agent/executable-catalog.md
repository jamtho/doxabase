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
- `rc:locationKind` says whether a root names an exact object/location,
  directory, prefix, or connection. Root-only query targets are executable
  candidates only when this is `object`; broader roots need path templates.
- `rc:endpointProfile` names a locally resolved endpoint profile, such as
  `local-minio`.
- `rc:pathStyleAccess` records an S3-compatible access quirk that query engines
  often need.
- `rc:credentialReference` names credential material without storing it.
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
configuration instead. The graph can say "use profile X"; the user's machine or
agent runtime decides how profile X resolves.

## How Agents Should Use It

1. Call `doxabase.describe_dataset` for the target dataset.
2. Call `doxabase.describe_query_context` when you want a compact physical
   planning projection with readiness and an `issues` list for missing, risky,
   or informational physical metadata.
3. Read `query_target_decision` first. Its zero-based `candidate_index` points
   at the candidate to inspect first, while `status` tells whether that target is
   ready, blocked only by sibling context, directly review-only, or absent.
4. Use `query_target_candidates` as supporting path/template cards. They preserve
   whether a template came from the dataset, a partition scheme, storage access,
   or a storage-root-only location, and they compose best-effort paths without
   resolving endpoint profiles or credentials.
   `template_source="storage_access_location"` means no path template was
   recorded, but the storage root itself is the candidate location; treat it as
   executable only when `location_kind="object"` confirms the root names the
   dataset object/location rather than a directory, prefix, or connection that
   still needs a template.
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
   SQL.
   Read `plan.scan.dataset_verification_note`, `plan.scan.template_lineage`,
   and the scan source verification fields before trusting a path. In the AIS
   fixture, `DailyIndex` currently shares the broadcast partition template and
   is intentionally review-gated until storage listing or query evidence
   confirms the real index layout.
10. If a query is run, record the result or failure with
   `doxabase.record_observation` and supporting evidence.

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
