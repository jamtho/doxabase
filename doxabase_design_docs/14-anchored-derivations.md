# Design Doc 14: Anchored Derivations
## (Resources that describe ephemeral entities)

**Date**: 2026-07-12 (the ephemeral-entities design session James
requested — "a key thing we'll need to get right to set up scale in
the long term")
**Status**: Position for James's reaction; distilled from the AIS
study's working practice, stated generically.
**The problem**: derived entities — places, candidate emitters,
shuttles, stop events, (elsewhere) supplier groups — live at
population scale in regenerable frames, where their identities are
run-local artifacts: rerun the pipeline with better code and cluster
17 becomes cluster 23, splits in two, or vanishes. But analysis needs
to SAY things about some of them, durably, with evidence. How do
durable graph resources describe entities whose identity is an
artifact of a run?

---

## 1. The pattern (already implicit in the study; here made law)

**Identity lives in the graph only by promotion; membership is
recomputed per run; the two are joined by matching, never by ID.**

1. **Populations stay in frames**, keyed by run (code version + data
   window + parameters — with doc 12, that key is the contract
   provenance quadruple). Run-local IDs are honest WITHIN a run and
   meaningless across runs. Nothing in the graph ever references one.
2. **Promotion mints identity.** When a story, claim, or method makes
   a derived entity load-bearing, it gets a minted IRI plus an
   **anchor descriptor** — the minimal stable characterization that
   lets any future run's rows be matched back to it:
   - a Place: anchor geometry (point/region) + kind;
   - a candidate Emitter: the hull-evidence basis (position-stream
     segment + identity tuple observed);
   - a stop/dwell event: (subject identity, time interval, location);
   - a supplier-group-like entity: the anchoring member set + period.
   The anchor is chosen so that matching is cheap and deterministic
   (spatial join, interval overlap, key intersection).
3. **The match-back is itself a method** — with a doc-12 contract:
   parameters (tolerances), invariants ("every promoted entity matches
   at most one cluster per run"; "match rate reported, never
   assumed"), and run provenance. This closes the loop: even the glue
   between graph and frames is evidenced, regenerable knowledge.
4. **Assertions about a promoted entity carry their run context**
   (`derivedFromRun`, `representsDetectorRows`, assessedAt/window —
   all shipped in vocabulary v2). "This place served 14 shuttles" is
   indexical to a run and a window, and says so.

## 2. Lifecycle and drift (the new decisions)

- **States**: population-only (in frames, no graph presence) →
  **promoted** (IRI + anchor + evidence) → **superseded** (a better
  run splits/merges/moves it; the old resource is never deleted — a
  reconsideration records what the new run shows, and a successor
  entity links back). This is the claim ladder applied to entity
  identity itself.
- **Drift policy**: the anchor is a CLAIM, not a constant. When a
  rerun's matched cluster drifts beyond the match tolerance (the
  contract's parameter), the match-back method must NOT silently
  re-anchor — it reports a drift finding, and re-anchoring is a
  staged revision with the drift evidence attached. Silent re-anchor
  is the ephemeral-world equivalent of the identity-freeze bug.
- **Counting discipline**: an aggregate must name whether it counts
  frame population or promoted entities (they differ by construction —
  promotion is interest-biased). This is the denominator rule wearing
  new clothes, and it matters doubly for anything public-facing.
- **Promotion rate is the capsule's scale-control knob.** The capsule
  holds O(promoted), never O(population). If promotion pressure grows
  (every shuttle "seems worth keeping"), the answer is a richer frame
  + better workbench browsing (doc 13), not mass promotion. Rule of
  thumb: promote when something needs to be SAID about the entity
  that a frame row cannot carry — a claim, a story, a correction, an
  expert judgement.

## 3. Why this generalizes (the second-domain test)

The structure is domain-free: any clustering/resolution pipeline
(place discovery, emitter segregation, corporate-group construction,
duplicate-record folding) produces run-relative entities, and any
serious analysis promotes a few of them into durable, evidenced,
reconsiderable identities. The AIS study exercised promotion for
places-by-hand and emitters; the second case study's entity resolution
will exercise it at legal-risk stakes, where "cluster 17 became
cluster 23" is the difference between two companies being confused.
If both domains run on this pattern unchanged, its terms (anchor
descriptor, match-back contract, drift finding, promotion) are `rc:`
candidates — by the two-domain law, not before.

## 4. Decision points for James

1. **Anchor descriptor per kind**: is minimal-stable-characterization
   the right rule, and who defines it — the promoting session (my
   lean: yes, recorded with the promotion, since anchors are
   domain judgement) or the vocabulary?
2. **Drift tolerance ownership**: parameter of the match-back
   contract (my lean — it then ages via assessment windows like any
   threshold) vs per-entity override?
3. **Successor semantics**: when a promoted entity splits, does the
   old IRI point at both successors ("supersededBy" ×2) with the
   split evidence, or at a split-event resource? (My lean: plain
   supersededBy links + the reconsideration carrying the story;
   resist minting event-reification until a case demands it.)
4. **Workbench surfacing** (doc 13 tie-in): promoted entities' pages
   should show live match-back status against the CURRENT run
   ("anchor last matched run R, drift 3m") — is that v1 or later?
