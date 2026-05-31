# Agent-Authored Observation RDF

DoxaBase has two observation lanes.

Use `doxabase.record_observation` for simple notes, counts, and routine
evidence-backed findings. The helper writes ordinary `rc:Observation` and
`rc:Evidence` RDF for you.

Use agent-authored RDF when the observation is more nuanced: a caveat, join
claim, transformation claim, access finding, source-span citation, or a proposed
map assertion that may later be systematised.

For the common richer pattern, prefer `doxabase.record_claim_observation`: it
writes one `rc:Observation`, one linked `rc:Claim`, one `rc:Evidence`, and
optionally one `rc:SourceSpan`. Drop to hand-authored RDF when you need multiple
claims, unusual relationships, custom project vocabulary, or a proposed
assertion graph that the helper cannot express cleanly.

## Graph Placement

Put agent-authored observation RDF in these graph roles:

- `observations`: `rc:Observation` and `rc:Claim` resources.
- `evidence`: `rc:Evidence` and `rc:SourceSpan` resources.
- `map`: only durable current-best facts, not tentative claims.
- `ontology`: project-specific terms used by the observation.

Observation RDF is validated more aggressively than map RDF. Observation
resources should have a summary and evidence. Claim resources should have a
claim kind, claim text, and at least one target.

Import observation RDF with the normal TriG import path, then run
`doxabase.validate_graph` with `scope="all"`. If the RDF is only a draft, keep it
in a scratch capsule until it validates.

## Minimal Pattern

```trig
@prefix enron: <https://example.test/enron#> .
@prefix rc:    <https://richcanopy.org/ns/rc#> .
@prefix rcg:   <https://richcanopy.org/graph/> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .

rcg:observations {
    enron:obs_eml_body_top a rc:Observation ;
        rc:summary "body_top is cleaned message text, not raw email text." ;
        rc:observedAt "2026-05-31T00:00:00Z"^^xsd:dateTime ;
        rc:observedAsset enron:eml_messages ;
        rc:observationStatus rc:Tentative ;
        rc:evidence enron:evidence_readme_body_processing ;
        rc:hasClaim enron:claim_body_top_transformation .

    enron:claim_body_top_transformation a rc:Claim ;
        rc:claimKind rc:TransformationClaim ;
        rc:claimTarget enron:eml_messages_body_top ;
        rc:claimText "The body_top column stores new message text above reply separators after footer stripping." ;
        rc:confidence rc:HighConfidence ;
        rc:observationStatus rc:Checked ;
        rc:proposedAssertion enron:body_top_transformation_caveat .
}

rcg:evidence {
    enron:evidence_readme_body_processing a rc:Evidence ;
        rc:summary "Enron README body processing section." ;
        rc:sourceSpan enron:span_readme_body_processing .

    enron:span_readme_body_processing a rc:SourceSpan ;
        rc:sourceKind rc:DocumentationSource ;
        rc:sourcePath "/home/james/github.com/jamtho/enron-emails/README.md" ;
        rc:sourceSection "Body processing" .
}
```

## Claim Kinds

Use the closest `rc:ClaimKind`:

- `rc:CaveatClaim`
- `rc:JoinClaim`
- `rc:SchemaClaim`
- `rc:TransformationClaim`
- `rc:AccessClaim`
- `rc:ProfileClaim`
- `rc:InterpretationClaim`

Project ontologies may add narrower claim kinds when the shared vocabulary is
too coarse.

## Status And Confidence

Use `rc:observationStatus` for lifecycle state:

- `rc:Tentative`: plausible but not fully checked.
- `rc:Checked`: supported by inspection, query, docs, or code review.
- `rc:Contradicted`: superseded or shown false by later evidence.
- `rc:Promoted`: systematised into durable map, ontology, or shape facts.

Use `rc:confidence` on `rc:Claim` resources:

- `rc:LowConfidence`
- `rc:MediumConfidence`
- `rc:HighConfidence`

## Proposed Assertions

`rc:proposedAssertion` points at a named resource representing a candidate future
map assertion. The candidate resource does not have to be fully materialised in
the same observation, but naming it gives future agents something stable to
promote, refine, or reject.

For example, a transformation claim may propose a future `rc:KnownCaveat`; a
join claim may propose a future `rc:ForeignKey` or `rc:SharedIdentifier`.

## Evidence And Source Spans

Prefer `rc:SourceSpan` when citing docs, code, queries, or small data samples.
Use non-secret source paths or URIs only. Do not put credentials, tokens, local
secret note paths, or private key material in evidence.

Useful source span fields:

- `rc:sourcePath`: path, URI, object key, or other source locator.
- `rc:sourceSection`: heading, table name, query name, or local section.
- `rc:startLine` and `rc:endLine`: one-based line numbers when useful.
- `rc:sourceKind`: `rc:DocumentationSource`, `rc:QuerySource`,
  `rc:DataSampleSource`, `rc:CodeSource`, or `rc:StorageSource`.

## When To Use The Helper Instead

Use `record_observation` when the finding is simple and the structure would add
little value. A pile of small notes should not become hand-authored RDF just for
ceremony. Use RDF when structure will help the next agent retrieve, compare, or
promote the claim.

Use `record_claim_observation` for the middle ground: one structured claim with
ordinary evidence and source-span support.
