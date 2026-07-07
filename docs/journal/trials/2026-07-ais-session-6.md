# AIS Real-Work Study — Session 6: The Vocabulary Transfer Probe (2026-07-07)

Cold Sonnet analyst; the blind test of session 5's deliverable. The brief
(`/home/codex/ais-study/BRIEF-6.md`) asked for two deep vessel stories
recorded "in the most precise, machine-readable form the capsule
supports" — and **never mentioned `aisv:`, the ontology graph, or
session 5**. Grading criteria were written before launch
(scratchpad `probe-6-grading.md`): discovery route, the three semantic
traps, fallback behavior, integrity, economics.

## Verdict: the vocabulary transfers

- **Discovery: PASS, via plain orientation.** project_brief →
  get_doc (ontology_primer among ten docs) → graph_overview surfaced the
  25-term vocabulary, its staged-revision provenance, and the three
  worked examples. Distiller pass 1's discoverability fixes were part of
  the route it took.
- **The meta-inheritance moment**: the agent read session 5's FAILED
  first map-proof revision (41 SHACL violations) and its repaired
  successor in the history graph, extracted the convention from the
  repair's rationale (`rdfs:seeAlso` for claim citations, never
  `rc:supportingClaim` on non-kernel classes), and wrote: "I inherit the
  lesson rather than rediscovering it the hard way." The history graph
  paid rent — a *mistake* transferred, not just knowledge.
- **Semantic traps: 2/2 applicable passed.**
  - AisIdentity ≠ Emitter applied with exactly the intended restraint:
    both vessels got AisIdentity nodes; an Emitter was minted only for
    374158000's confidently-segregated dominant occupant, and the
    unsegregated secondary emitters were deliberately left in
    claim-prose ("a resource I could not fully justify").
  - `datingQuality=year_only_undatable` on the year-boundary
    IdentityChange (the Jan-1 artifact honored).
  - `ambiguous_ballast` untestable — no cargo story this session.
- **Integrity: PASS.** Full staged loop with dry-run; claims first with
  parquet-glob evidence; a `record_claim_reconsideration`
  (relation=refines) correctly filed against the existing M1
  worked-example claim it nuanced; validate_graph(scope="all") conforms;
  no orphaned staged rows.

## The stories (both new knowledge)

- **374158000**: a validly-formatted Panama MMSI behaving like the
  junk-MMSI family — dominant occupant physically persistent at one
  Long Beach anchorage across both years while its displayed identity
  flips placeholder→real (read as statics_correction), PLUS genuine
  simultaneous multi-emitters broadcasting the identical borrowed
  name+IMO+call sign from scattered East Coast sites (M2's widest
  conflict-span case, 33.1° median).
- **368817000 COMFORT**: rare type-58 hospital ship (11 MMSIs
  feed-wide), motionless at one Gulf berth for most of two years, three
  in-place winter silences at the same coordinate to three decimals —
  and a fresh M3 failure mode: one continuous ~68-day voyage fragmented
  into two gap rows by a single intervening fix (distinct from the
  recorded coverage-geometry caveat).

## Vocabulary v2 evidence (the couldn't-say list, independently confirmed)

The agent rediscovered session 5's Voyage-class gap without reading
VOCAB-NOTE.md, and added new ones: multi-mechanism identity readings
(one MMSI with two simultaneously-true mechanisms vs single-valued
changeMechanism), merged-gap provenance (no `aisv:mergesGap`),
background-knowledge sourcing (no rc:SourceKind for world-knowledge
identification), unsegregated-emitter representation.

## Product findings

1. **FIXED same-day**: post-apply stale-sibling recheck flagged a
   revision already CLOSED by a review decision (superseded) —
   contradicting plan_staged_revision_recovery, which correctly excludes
   resolved rows. `_post_apply_recheck_revisions` now skips rows with an
   `rc:resolvesStagedRevision` pointer; regression-tested.
2. Distiller ledger: `stage_revision(kind="graph")` additions dict shape
   (`{"graph":..., "content":...}`) not spelled out in the generated
   doc — the agent inferred it from a doc shorthand plus a stored patch;
   project-namespace prefixes (aisv:) are not registered for CURIE
   expansion, so `list_entities(type="aisv:AisIdentity")` silently
   returns [] while the full IRI works (curator-found during grading).
3. The `@args.json` bridge payload route (documented by distiller
   pass 1, implemented in the study bridge same day) was load-bearing:
   "long claim/rationale text genuinely requires it."
