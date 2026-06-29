# Patterns

DoxaBase uses patterns for the synthesis layer between observations and the
project map.

The useful distinction is epistemic, not necessarily temporal:

- `observations`: things noticed, measured, queried, or read in a particular
  context.
- `patterns`: connected interpretations over observations, claims, or evidence.
- `map`: the current operating model future agents should start from.

A strong agent may record all three layers in one session. A cautious agent may
record only observations. A later agent or human can synthesize patterns from
older findings and then systematize them into the map.

## Pattern Resources

Patterns live in the `patterns` graph as `rc:Pattern` resources. Use them when
you want to say:

- these observations or claims belong together;
- this repeated or checked finding looks more durable than a one-off note;
- this synthesis explains why map facts should exist or be revised;
- this interpretation is useful, but not quite the same as an accepted map fact.

The common fields are:

- `rc:summary`: short description of the synthesis.
- `rc:patternText`: concise statement of the pattern.
- `rc:rationale`: why the supporting material belongs together.
- `rc:patternTarget`: resources the pattern is about.
- `rc:supportingObservation`: observations that support the pattern.
- `rc:supportingClaim`: structured claims that support the pattern.
- `rc:evidence`: direct source support when the pattern cites a source.
- `rc:confidence`: `rc:LowConfidence`, `rc:MediumConfidence`, or
  `rc:HighConfidence`.
- `rc:patternStability`: `rc:EmergingPattern`, `rc:RepeatedPattern`, or
  `rc:InvariantPattern`.
- `rc:mapImplication`: map resources or named candidate implications suggested
  by the pattern.

`record_pattern()` preflights the controlled `confidence`, `pattern_status`, and
`pattern_stability` values before writing RDF. Use the listed RC terms rather
than severity terms such as `rc:Moderate` or ad hoc confidence names.

Use `rc:mapImplication` for soft forward links. It does not mean the map has
already been edited.

## Helper

Use `doxabase.record_pattern` for the common case. The helper writes one
`rc:Pattern` to `patterns` and can write linked `rc:Evidence` and
`rc:SourceSpan` resources to `evidence`.

```python
pattern = db.record_pattern(
    summary="body_top behaves like cleaned top-level message text.",
    pattern_text="README guidance, schema inspection, and profiling all support treating body_top as cleaned sender-new message text.",
    rationale="The source docs describe reply splitting, the column is present on EML messages, and profile checks found it consistently populated.",
    pattern_targets=["https://example.test/enron#eml_messages__body_top"],
    supporting_claims=[
        "https://example.test/enron#claim_body_top_transformation",
    ],
    source_path="/home/james/github.com/jamtho/enron-emails/README.md",
    source_section="Body processing",
    source_kind="rc:DocumentationSource",
    confidence="rc:HighConfidence",
    pattern_stability="rc:RepeatedPattern",
    map_implications=[
        "https://example.test/enron#caveat_body_processing_lossy",
    ],
)
```

## Relation To Proposed Assertions

`rc:proposedAssertion` still exists for claim-level RDF that points at a
candidate durable assertion. Prefer patterns when you are grouping related
findings and explaining why they matter. Use proposed assertions only when a
single claim really does point at a candidate map assertion.

`proposed_assertions` and `map_implications` are resource links. Pass IRIs or
CURIEs there; put prose in `claim_text`, `pattern_text`, or `rationale`.

Use `doxabase.describe_pattern` when a pattern should teach a future reader how
to think about a dataset. It returns the pattern, targets, supporting claims,
observations, evidence/source spans, and map implications in one compact object.

## Relation To Map Helpers

Patterns are not promoted automatically. If a pattern supports a direct
current-best map fact, record the map fact with a map authoring helper and keep
the pattern linked via `rc:mapImplication`.

When the promotion is more nuanced, use `doxabase.stage_pattern_promotion`.
It takes existing pattern IRIs plus caller-authored RDF framings and records
reviewable staged revisions in `history`. The selected patterns become
`supporting_patterns`; their supporting observations and claims are rolled into
the staged revision metadata; and their targets/map implications are used as
revision anchors. Evidence linked through those observations or claims remains
reachable through context-slice routes, but it is not direct staged-revision
evidence unless you pass it explicitly or link it directly on the pattern. The
grouped review can therefore show direct `evidence: 0` while still listing
supporting claims or observations whose own evidence is reachable by slice.
helper does not decide the graph shape for you. Use it for pattern-supported
map, ontology, or shape changes that should be validated and reviewed before
becoming durable project structure.

A useful promotion bundle can share provisional project vocabulary across
several framings. Put common project ontology and any temporary project SHACL
rules in shared additions, then let each framing supply its own map additions.
Shared additions are included in every staged framing, so do not put ontology or
shape patches there if one fallback framing is meant to avoid them.
Keeping one intentionally incomplete or invalid framing is often useful: it
turns validation diagnostics into a review cue while a complete sibling remains
ready to apply. For example, a pattern might support a project-local
`wf:SemanticStorageClass` term and a `wf:semanticStorageClass` predicate; one
framing can classify every current dataset, while another omits a dataset so
the grouped review bundle shows exactly how the shape catches missing
assignments. If the ready sibling is applied, stale alternatives should still be
read alongside their original staged validation diagnostics before deciding
whether to repair, supersede, or discard them.

## Validation

Pattern validation is intentionally stricter than map validation. A pattern must
have summary text, pattern text, rationale, at least one target, and support from
observations, claims, or evidence. Keep draft patterns in a scratch capsule until
`doxabase.validate_graph(scope="all")` conforms.
