# Executable Catalog Metadata

DoxaBase records non-secret facts about physical storage so an agent can move
from semantic understanding to a plausible query plan — without turning the
graph into a secret store or runtime configuration file. This is catalog
metadata, not a query engine: DoxaBase never resolves credentials, checks
object existence, or executes anything.

## What Belongs In The Graph

Facts useful for planning, review, and handoff, safe for collaborators:

- `rc:hasStorageAccess` links a dataset to a storage access description.
- `rc:storageProtocol` — `rc:LocalFilesystemStorage`,
  `rc:S3CompatibleStorage`, HTTPS, or `rc:DatabaseStorage`.
- `rc:storageRoot`, `rc:bucketName`, `rc:keyPrefix`, `rc:pathTemplate` —
  where data lives.
- `rc:locationKind` — the shape of the recorded root: `object` (the root IS
  the dataset file/object — the only root-only shape that is directly
  executable), `directory`, `prefix`, or `connection` (broader roots need
  path templates). The authoring spec accepts `location_kind="bucket"` as a
  convenience for S3 bucket/prefix routes; it is stored as `prefix`. There
  is no `local_path` location kind — local filesystem is a
  `storage_protocol`, not a root shape.
- `rc:endpointProfile` — a locally resolved endpoint name such as
  `local-minio`; `rc:pathStyleAccess` for the S3 quirk engines need.
- `rc:credentialReference` — names credential material without storing it:
  `profile:<name>`, `env:<VAR_NAME>`, or
  `external:intentionally-unrecorded` (the credential exists outside the
  graph or is deliberately unavailable).
- `rc:accessMode` — `rc:ReadOnlyAccess` / read-write intent.
- `rc:fileFormat` and `rc:compressionCodec` on physical layouts —
  resource values (`rc:Parquet`, `rc:ZstdCompression`), not strings.
- `rc:layoutVerificationStatus` + `rc:layoutVerificationNote` — how much to
  trust path/layout claims. Use `rc:VerifiedByListingLayout` only after a
  real listing/schema check and `rc:VerifiedByQueryLayout` only after an
  actual query; `rc:CandidateLayout` is the honest state for handoff-note
  guesses, and it keeps plans review-gated by design.
- `route_roles` on storage accesses when a dataset has several viable
  routes: `rc:ProductionRoute`, `rc:CurrentRoute`, `rc:CanonicalRoute`,
  `rc:SampleRoute`, `rc:ArchiveRoute`, `rc:BackfillRoute`. Query candidates
  inherit these, so route intent is chosen from reviewed facts, not from
  parsing path names.

Database-backed storage is the important template exception: for
`rc:DatabaseStorage`, storage-access-owned `path_templates` are database
relation identifiers such as `schema.table`, and `storage_root` is the
connection reference — not a file root. Relation identifiers must live on
the storage access; a relation-shaped template on the dataset or partition
scheme is flagged as misplaced by query context.

For S3/object routes, keep templates relative to the recorded `key_prefix`
(`path_templates=["month={month}/*.parquet"]`, not the prefix repeated), and
avoid duplicating the same template on both the dataset and the storage
access — duplication creates equivalent ready candidates.

## What Stays Outside

Never in the graph: access keys, secret keys, tokens, passwords, private
connection strings, or user-specific absolute paths that should not travel
with the project. Point at local runtime configuration with the credential
reference and endpoint profile markers instead.

Non-secret paths are still share-review material: before writing shareable
artifacts, run `export_preflight` for the intended kind
(`kind="scan_only"` gives the bare redacted scan). The scanner catches
credential-shaped literals; it does not decide whether local paths or
endpoint URLs are appropriate for the audience. Exports are faithful, never
auto-redacted; treat `decision="block"` as stop-and-review, and pass
`fail_on_sensitive: true` on final exports even after a clean preflight.

## Recording

All of this is written through `record_map_fact` — `kind="storage_access"`,
`kind="physical_layout"`, `kind="partition_scheme"` for individual
resources, or `kind="table_bundle"` for one reviewed table + columns +
storage + layout in a single no-I/O call. The `mcp_tools` doc lists each
kind's fields. A typical minimal catalog slice for one local directory
route: a storage access (`storage_protocol="rc:LocalFilesystemStorage"`,
`access_mode="rc:ReadOnlyAccess"`, `location_kind="directory"`,
`storage_root=...`, `datasets=[table]`), a physical layout
(`file_format="rc:Parquet"`, `datasets=[table]`), a partition scheme
(`path_template="events/event_date={date}/*.parquet"`,
`partition_columns=[...]`, `granularity="rc:Daily"`, `datasets=[table]`),
each carrying its own verification status and note. Put a template on the
resource that owns the verification story; duplicate only deliberately.

Direct recording is for NEW reviewed facts. Repairs to what the map already
asserts — adding missing storage to a dataset another agent modelled,
replacing a stale layout link — go through the staged repair kinds
(`stage_revision` with `kind="query_storage_access_repair"` /
`kind="query_physical_layout_repair"`), which carry rationale into history.
See `query_planning` for the repair loop and `map_authoring` for the
direct-vs-staged rule.

## Using It

`describe_dataset` shows the recorded facts; `describe_query_context` turns
them into readiness, candidates, issues, and repair templates; adding
`plan_candidate=` drafts the non-executed handoff. That workflow — including
verification-status gates, route-role choice among ready candidates, and
recording external results with `record_observation(kind="query_result")` —
lives in the `query_planning` doc.
