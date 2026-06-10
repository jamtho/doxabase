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
2. Read `physical_layouts`, `partition_schemes`, `path_templates`, and
   `storage_accesses` together.
3. Check `layout_verification_status` and `layout_verification_note` on the
   dataset and on relevant layout, partition, and storage resources.
4. Combine storage root or bucket/prefix facts with the dataset path template
   only when the verification status and notes make that reasonable.
5. Check caveats before generating a query.
6. If a query is run, record the result or failure with
   `doxabase.record_observation` and supporting evidence.

## Current Limits

This is catalog metadata, not a query engine. DoxaBase does not yet expose
helpers that turn these facts directly into DuckDB SQL, S3 settings, or runtime
connection objects.

For now, the value is handoff and planning: the next agent can see where the data
is, how it is physically shaped, what local profile to use, which layout claims
need verification, and which caveats should travel with generated work.
