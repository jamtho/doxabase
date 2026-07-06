# Patterns

Patterns are the synthesis layer between observations and the project map.
The distinction is epistemic, not temporal:

- `observations` — things noticed, measured, queried, or read in context.
- `patterns` — connected interpretations over observations, claims, or
  evidence: "this keeps being true", "these findings belong together".
- `map` — the current operating model future agents should start from.

A strong agent may record all three layers in one session; a cautious agent
may record only observations and let a later agent synthesize. Both are
correct uses.

## Recording

`doxabase.record_pattern` writes one `rc:Pattern` to `patterns`, with
optional linked evidence and source span in `evidence`. Required:
`summary`, `pattern_text` (the concise statement), `rationale` (why the
support belongs together), and `pattern_targets` (the resources the pattern
is about). Support comes from `supporting_observations`, `supporting_claims`,
and/or evidence fields — validation requires at least one summary-bearing
support route, and an `evidence_summary` requires `evidence_sources` or a
`source_path`.

Controlled values (preflighted; do not invent severity-style terms):

- `confidence`: `rc:LowConfidence` / `rc:MediumConfidence` /
  `rc:HighConfidence`.
- `pattern_status`: defaults `rc:Tentative`.
- `pattern_stability`: `rc:EmergingPattern` / `rc:RepeatedPattern` /
  `rc:InvariantPattern`.

`map_implications` are soft forward links to map resources or named candidate
implications — IRIs or CURIEs, not prose. An implication does not mean the
map has been edited.

## Reading

`describe_resource` on a pattern IRI auto-detects the type and returns the
pattern handoff card: targets, supporting claims and observations, evidence
and source spans, and map implications. Read a pattern before applying it as
a decision rule. When you need the surrounding RDF, seed
`get_context_graph(seed_iris=[pattern_iri], profile="pattern_brief")`.

In `describe_dataset`, linked-pattern reasons arrive as match groups: direct
and map-implication groups are the strongest local relevance signals; claim-
and observation-supported groups show surrounding lore. Treat group counts as
navigation hints, not confidence scores.

## Promotion

Patterns are never promoted automatically.

- If a pattern supports a straightforward NEW current-best fact, record it
  with `record_map_fact` and keep the pattern linked via `map_implications`.
- If the promotion changes existing facts, needs review, or needs
  caller-authored RDF beyond the map helpers, use
  `stage_revision(kind="pattern_promotion")`: it takes the pattern IRIs plus
  RDF framings, records the patterns as staged-revision support, uses their
  targets and map implications as revision anchors, and leaves the change
  reviewable until `apply_staged_revision`. Evidence linked only through a
  pattern's observations or claims stays reachable by context slice but is
  not direct staged-revision evidence unless passed explicitly.
- When one hunch has several plausible framings, use
  `stage_revision(kind="systematisation")` instead and compare alternatives
  (see the `systematisation` doc).

## Validation

Pattern validation is intentionally stricter than map validation: summary,
pattern text, rationale, at least one target, and support are all required.
Support IRIs are not existence-checked at write time — recording is
open-world, so a pattern may cite claims or observations recorded later —
but a supporting claim that never materializes fails
`validate_graph(scope="all")` (the shapes flag the dangling IRI), so
validate after recording.
Note that a staged `rc:Pattern` inside a systematisation framing must carry
its support inside the framing Turtle itself (`rc:supportingObservation`,
`rc:supportingClaim`, or `rc:evidence`) — revision-level support links do not
satisfy `rc:PatternShape`. Keep draft patterns in a scratch capsule until
`validate_graph(scope="all")` conforms.
