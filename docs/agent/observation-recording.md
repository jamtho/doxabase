# Observation Recording

Observations are dated, evidenced notices: things an agent, profiler, query,
or human found in a particular context. They are not yet durable model facts —
they may later be synthesized into patterns, promoted into the map, or
contradicted. Record at the confidence you actually have.

## One Recording Door, Four Kinds

`doxabase.record_observation` writes to `observations` (+ linked `evidence`):

- `kind="observation"` (default) — a general finding: a caveat noticed during
  exploration, a failed assumption, a useful note. Uses the flat parameters
  (`summary`, `observed_asset`, `observed_column`, `observed_at`,
  `observed_by`, evidence fields).
- `kind="profile"` — a profiling-style finding: row/null/distinct counts,
  `sample_size`/`sample_scope`/`sample_method`, `value_frequencies`
  (`{"value": ..., "frequency": ...}` rows), and `profile_metrics`
  (`{"metric": ..., "value": ..., "datatype": ..., "target": ...}` rows).
  For runs that should also touch map state or group several columns, use
  `record_profile` instead (see the `profiling` doc).
- `kind="claim"` — the structured observation + claim + evidence +
  source-span bundle. Fields go in `spec` (see below and the `mcp_tools`
  doc's per-kind list).
- `kind="query_result"` — an externally executed query's result or failure
  preserved as evidence. Fields go in `spec`: `execution_status`
  (`succeeded`/`failed`/`blocked`/`cancelled`/`partial`), `engine`,
  `query_source_path` (+ line range → an `rc:QuerySource` span),
  `query_hash`, `result_sources` for output artifacts,
  `scanned_source_paths` for non-secret inputs, and `scanned_source_handles`
  for reviewed runtime handles such as `warehouse-prod:mart.orders`.
  Only fill profile-shaped count fields when `summary`, `sample_scope`, and
  `sample_method` make their meaning unambiguous; failed or blocked attempts
  carry `failure_summary`, never profile counts.

## Evidence Is Not Optional

The base SHACL shapes expect observations to link evidence. Supply
`evidence_summary` plus `evidence_sources` (or a source path): what produced
the finding — source files or URI patterns, query text locations, profiler
names, sampling notes. `evidence_summary` alone is prose, not a source
identity; an `evidence_summary` without `evidence_sources` or a source path
fails with a targeted error. Never put credentials, tokens, or secret note
paths in evidence.

IRIs are minted under `https://richcanopy.org/doxabase/generated/` unless you
pass `observation_iri` / `evidence_iri`; prefer stable project IRIs for
resources other work will reference.

## Structured Claims

Use `kind="claim"` when the finding asserts something checkable about a
target: `claim_text`, a `claim_kind`, and `claim_targets`, with ordinary
evidence and an optional source span. Claim kinds are `rc:CaveatClaim`,
`rc:JoinClaim`, `rc:SchemaClaim`, `rc:TransformationClaim`, `rc:AccessClaim`,
`rc:ProfileClaim`, and `rc:InterpretationClaim`; projects may define narrower
kinds in their own namespace.

Controlled vocabularies are preflighted before any RDF is written:

- `confidence`: `rc:LowConfidence`, `rc:MediumConfidence`,
  `rc:HighConfidence`.
- `observation_status`: `rc:Tentative`, `rc:Checked`, `rc:Weakened`,
  `rc:Contradicted`, `rc:Superseded`, `rc:Promoted`.

`proposed_assertions` links a claim to named candidate future map assertions.
Pass IRIs or CURIEs, never inline Turtle or prose — the explanation belongs in
`claim_text`, or in a pattern when the synthesis is broader.

## Reconsiderations

When a later claim changes how an earlier claim should be read, use
`doxabase.record_claim_reconsideration` — never delete. The relation is
`weakens`, `contradicts`, `supersedes`, or `refines`; choose the lightest one
that captures the change (`weakens` for still-useful-but-too-broad,
`contradicts` when later evidence makes the claim false). The trail is the
product: `describe_resource` on a claim returns its lifecycle summary and the
incoming/outgoing reconsideration rows, and both should be read before
promoting a related map fact. Reconsiderations can cite DoxaBase retrieval
output as evidence with `source_kind="rc:DoxaBaseAPISource"`.

## Hand-Authored Observation RDF

For findings the structured kinds cannot express cleanly — multiple claims in
one move, custom project vocabulary, unusual relationships — author the RDF
yourself and load it with `import_bundle(kind="trig")`, then run
`validate_graph(scope="all")`. Placement: `rc:Observation` and `rc:Claim` in
`observations`; `rc:Evidence` and `rc:SourceSpan` in `evidence`; project
terms in `ontology`; nothing tentative in `map`.

```trig
@prefix ex:  <https://example.test/project#> .
@prefix rc:  <https://richcanopy.org/ns/rc#> .
@prefix rcg: <https://richcanopy.org/graph/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

rcg:observations {
    ex:obs_body_top a rc:Observation ;
        rc:summary "body_top is cleaned message text, not raw email text." ;
        rc:observedAt "2026-05-31T00:00:00Z"^^xsd:dateTime ;
        rc:observedAsset ex:eml_messages ;
        rc:observationStatus rc:Tentative ;
        rc:evidence ex:evidence_readme_body ;
        rc:hasClaim ex:claim_body_top .

    ex:claim_body_top a rc:Claim ;
        rc:claimKind rc:TransformationClaim ;
        rc:claimTarget ex:eml_messages_body_top ;
        rc:claimText "body_top stores new message text above reply separators." ;
        rc:confidence rc:HighConfidence .
}

rcg:evidence {
    ex:evidence_readme_body a rc:Evidence ;
        rc:summary "Source README, body processing section." ;
        rc:sourceSpan ex:span_readme_body .

    ex:span_readme_body a rc:SourceSpan ;
        rc:sourceKind rc:DocumentationSource ;
        rc:sourcePath "docs/README.md" ;
        rc:sourceSection "Body processing" .
}
```

Source-span fields: `rc:sourcePath` (path, URI, or object key —
non-secret only), `rc:sourceSection`, `rc:startLine`/`rc:endLine`, and
`rc:sourceKind` (`rc:DocumentationSource`, `rc:QuerySource`,
`rc:DataSampleSource`, `rc:CodeSource`, `rc:StorageSource`,
`rc:DoxaBaseAPISource`).

Observation RDF is validated more strictly than map RDF: observations need a
summary and evidence; claims need a kind, text, and at least one target. If
the RDF is still a draft, keep it in a scratch capsule until it validates.

## Choosing The Lane

- A simple evidence-backed note → `record_observation` flat fields. A pile of
  small notes should not become hand-authored RDF for ceremony's sake.
- One structured claim with ordinary support → `kind="claim"`.
- Several findings that belong together → `record_pattern`
  (see the `patterns` doc); patterns are the bridge from noticed facts to
  map facts.
- New current-best facts → `record_map_fact`; reviewed changes to existing
  map facts → `stage_revision` (see `map_authoring`).

Python API note: the library exposes the pre-fold methods directly —
`db.record_claim_observation(...)` and `db.record_query_result(...)` take as
keywords what the MCP door takes in `spec`.

Controlled-value strictness: `profile_metrics[].metric`,
`observed_physical_type`, and `observed_value_type` take CURIEs or IRIs
(`rc:...` or project-namespace terms), not prose; validation errors name
the offending field.
