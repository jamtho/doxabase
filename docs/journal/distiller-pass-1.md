# Distiller Pass 1 — 2026-07-06

First pass of the recorded-trials/deferred-distiller loop
(`doxabase_design_docs/10-next-directions.md` §1). Brief: read the whole
accumulated trial record, then make at most a small batch of product
changes, each justified across multiple observations, with simplicity and
conceptual clarity as the explicit goal. Counterweight to additive drift —
when in doubt, don't.

**Evidence base read in full**: `docs/journal/trials/` (2026-07-baseline,
gate3, gates-5-6, enron-case-study, ais-session-1 through 5), the friction
tails of `docs/journal/waves.md` (waves 11–25), doc 06/07 anti-pattern
definitions, and `handoff/fable-parting-notes-2026-07-06.md`.

**Constraint check**: no new tools, no new response fields, no new doc
sections; every fix drawn from the allowed ladder (state presentation in an
existing field → rewritten doc sentence → merged/simplified response).
Anti-pattern self-check done against doc 07's six named reflexes.

## Items chosen (6)

### 1. Draft-plan review-reason triplication → wire subtraction

- **Evidence**: gates-5-6 seed #3 (issues / review_reasons /
  direct_review_reasons repeat the same content 3×); baseline friction #2
  (agents self-rated 30–60% of received bytes as envelope noise).
- **Semantics read** (`core/query_planning.py`):
  `direct_review_reasons` is *always* `review_reasons` minus the single
  synthesized `query_context_has_other_blockers` rollup issue — a pure
  derivation, never independent state.
- **Change**: `QueryTargetCandidate.direct_review_reasons` marked
  `doxabase_internal` (the wave-15 mechanism: Python API keeps it, MCP wire
  drops it), with the derivation rule recorded at the field. The wire keeps
  the minimal truthful set: `context.issues` (context scope),
  `review_reasons` (candidate scope), `direct_review_required` (bool), and
  the review gate's code lists. Six MCP envelope tests reconciled without
  weakening which-value semantics; one asserts the field stays off the wire.
- **Measured**: describe_query_context 14,732 → 12,761 chars (−13.4%,
  end-state 12,000 nearly reached); ceiling ratcheted 15,300 → 13,300.

### 2. Required-vs-optional split in targeted spec errors

- **Evidence**: ais-session-4 friction (claim recording requires
  spec.summary but the error listed fields without a required split);
  gate3/gates-5-6 established targeted errors as the intended discovery
  path; ais-session-1 rated them "the redeeming feature" — so their
  precision is load-bearing product surface.
- **Change**: `_dispatch_kind` and `_merge_spec_into_call` errors now render
  `required fields for this kind: [...]; optional: [...]` (or
  `valid spec fields (all optional): [...]`) via one shared
  `_required_optional_note` helper — the same split `tools/gen_docs.py`
  already prints, now also at the moment of failure. Existing error-text
  assertions still match; three regression tests added.

### 3. Vocabulary discoverability (list_entities vs base_ontology)

- **Evidence**: ais-session-1 (`list_entities(type="rc:PhysicalType")`
  returned 0, misleading); deferred again at wave 25; parting notes §6.
- **Finding**: the mechanism already works — `_expand_graphs` maps
  `graph="ontology"` to `base_ontology + ontology` (verified live: 18
  rc:PhysicalType rows). The failure was the silent default
  `graph="map"` plus no doc naming the route. Least-code truthful fix is
  documentation, not code.
- **Change**: list_entities docstring now states the default and the
  vocabulary route (regenerated into mcp-tools.md); ontology-primer.md
  gained the exact listing call and why `graph="map"` returns 0.

### 4. Generated-doc/docstring truthfulness batch

- **Evidence**: ais-session-5 (review_decision enum only discoverable via
  error); ais-session-2 (record_observation claim/query_result spec-nesting
  wording ambiguous); ais-session-1 (analysis_view_bundle reads as a
  grouping resource; it is a bulk-write helper).
- **Changes**: `decision` parameter annotated with its
  Literal enum — the generated `stage_revision kind="review_decision"`
  section now shows all four values at zero schema-char cost (the handler
  is not a registered tool); the spec-merge sentence rewritten to state
  exactly which flats merge, that explicit spec wins, and that required-ness
  is checked after the merge; map-authoring.md and analysis-packets.md now
  say `analysis_view_bundle` = several views in one call, no grouping
  resource (rename rejected: single-trial complaint vs the ~10-shape rename
  ripple in parting notes §3.5).
- **Bug found while aligning**: flat `observed_column` was silently dropped
  on the claim/query_result path though `record_claim_observation` accepts
  it. Now merged like the other flats; kinds that reject it fail with the
  targeted error. Fixing it also let the claim branch reuse
  `_RECORD_OBSERVATION_SPEC_KINDS` instead of rebuilding the handler map.
  Regression-tested both ways.

### 5. Bridge payload ergonomics → documented pattern, no shipped bridge

- **Evidence**: JSON-with-apostrophes shell quoting broke agents in
  ais-session-2 and ais-session-3 (promoted to "firm distiller item");
  ais-session-4 confirmed scratch-file payload passing eliminates it.
- **Decision**: document, don't ship. A repo bridge in `examples/` would be
  a new maintained artifact tracking `build_server` — the docs-rot lesson
  argues against it while every study writes a 30-line bridge anyway.
- **Change**: field-trials.md Runtime Notes now opens with the bridge
  dispatch pattern and the rule: payloads via scratch file
  (`bridge.py call <tool> @args.json`), never inline shell JSON.

### 6. record_pattern dangling supporting-claim IRIs → documented open-world

- **Evidence**: ais-session-4 only — a single-trial observation, so under
  the single-trial-fix ban it gets the doc decision, not a behavior change.
- **Finding**: write-time is deliberately open-world (forward references to
  claims recorded later are legal), and the guard already exists
  downstream — verified live: a dangling supporting claim fails
  `validate_graph(scope="all")` with shape violations on the missing IRI.
- **Change**: one sentence in patterns.md Validation stating the open-world
  posture and that validate-after-recording is the net. Validate-and-error
  at write time rejected: it would break the record-pattern-then-claims
  order and be inconsistent with every other IRI-reference field.

## Items explicitly deferred

- **mcp_tools.py split** (ledger #10): deferred. At 3,796/3,800 lines with
  a 3,000 end-state the split is inevitable, but it is a structural wave of
  its own, not a distiller item: no trial agent ever saw the module size,
  and parting notes §8 requires deciding gen_docs introspection first.
  Recommended shape for that wave: an `mcp_tools/` package whose
  `__init__` re-exports every current name and dispatch table so
  `gen_docs`'s `mt._*_KINDS` imports and `doxabase.mcp_tools` callers are
  untouched. This pass paid the ceiling back under budget (claim-branch
  consolidation) rather than pre-splitting.
- **History-graph repair staged route** (ais-session-5): too big to build
  now, and n=1 corruption (its cause already fixed). Design question
  recorded in doc 04 backlog under Validation and Transactions.
- **rc:citesClaim and all rc: ontology semantics**: reserved for James
  (out of scope by mandate).
- **M-method upgrades / vessel-doings vocabulary** (ais-session-4 gaps,
  session-5 couldn't-say list): study-capsule knowledge, not product
  surface; stays with the AIS study and the ontology-pack track.
- **Caveat targeting/doc remainders already fixed same-day in sessions**
  (wave 25, session-2/3/5 fixes): verified landed; nothing re-done here.

## Subtraction accounting

- Wire: one response field removed from every query-target candidate
  (`direct_review_reasons`); zero fields added. describe_query_context
  −1,971 chars on the fixture capsule; ceiling ratcheted −2,000.
- Code: duplicate kind→handler mapping in record_observation_tool deleted;
  mcp_tools.py net +21 lines (error-split helper) under an unchanged
  ceiling; no new tools, docs, or doc sections.
- Costs accepted: +267 schema chars (two docstrings made truthful) and
  +1.9KB agent docs (all rewrites inside existing sections), both under
  ceilings; per rule 3 nothing comparable was added (no tool/field/section).

## Verification

- `bash tools/gate.sh`: all checks passed — 739 passed, 1 skipped (736
  before the pass; +3 regression tests), validate_rdf conforms, scoreboard
  all green (describe_query_context 12,761 ≤ 13,300 ratcheted ceiling,
  largest module 3,796 ≤ 3,800), git diff --check clean, wheel install
  smoke ok (805 triples, 25 tools).
- `tools/gen_docs.py` regenerated; drift test green.
- Live checks: dangling-claim SHACL failure reproduced; ontology listing
  route verified against the fixture capsule; new error text rendered and
  asserted in tests.

## Template notes for the next pass

Keep this file's shape: evidence base named up front; per-item *evidence →
finding → change → measurement*; deferrals with reasons; subtraction
accounting with the costs accepted, not just the wins; verification lines
that a reviewer can re-run. Read the semantics before consolidating
(item 1's field was only deletable because the derivation rule was exact),
and let single-trial observations buy sentences, not behavior.
