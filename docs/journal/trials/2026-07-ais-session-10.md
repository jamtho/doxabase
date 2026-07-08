# AIS Real-Work Study — Session 10: Vocabulary v2 (2026-07-08)

Fable reviser; the second ontology-pack iteration, acting on expert
round 2 (fully recorded) plus sessions 6–9 usage evidence. Brief:
`/home/codex/ais-study/BRIEF-10.md`. End state: graph conforms, zero
staged rows, ontology 129→226 triples (34 active + 4
superseded-retained terms), map 725→755. Design note for James:
`/home/codex/ais-study/VOCAB-NOTE-V2.md`.

## What v2 did (all ≥2-item justified, citations in comments)

- **The expert's layering directive executed**: CargoOperation and
  cargoDirection SUPERSEDED (retained with v1 meaning quoted verbatim
  in the comment) by DraftChangeEvent + draftChangeReading;
  OperationalTie/tieKind superseded by RecurringCoPresence +
  coPresenceReading. Every layer-2 "reading" now carries
  **readingBasis** — the generalization of the hullContinuityBasis
  lesson (the fleet-clone story forged its own corroborator).
- **The declaration threshold encoded**: declaredHullRecord (the solid
  non-AIS-record anchor) exists as a property with deliberately ZERO
  instances — absence-as-signal: everything in the capsule is
  correctly a candidate today. Emitter relabelled "AIS-inferred
  candidate". externalBasis added for weaker non-feed sourcing.
- **Indexicality + ephemera hooks**: assessedAt/assessmentDataWindow on
  all 8 operatingProfile bearers (timestamps taken from recorded
  history, not fabricated; window = "NOAA AIS feed, 2024-01-01..
  2025-12-31"); derivedFromRun + representsDetectorRows link promoted
  exemplars to their regenerable detector rows (resolving session 6's
  merged-gap couldn't-say); trackContext imports M8's exact value set;
  ofEmitter makes session 6's "dominant occupant only" prose scoping
  structural.
- **Migration by re-typing, not bridging**, where the resource's own
  recorded description already matched the v2 semantics; trackContext
  deliberately NOT asserted where no M8 result exists
  (in-doubt-leave-it-out); the discipline held.
- **GearBeacon correctly REJECTED** at the ≥2-story bar: the in-feed
  941xxxxxx buoys each carry their own MMSI (recorded knowledge from
  the story corpus), while the expert's same-MMSI battery-in-COG fleet
  is unobserved in this feed — so it stays on the couldn't-say list
  until someone finds one. The evidence rule beat the novelty pull.
- Couldn't-say v2: Voyage, lanes/RecurrentPattern, MmsiUsagePeriod (the
  expert's alternative primitive — held pending the primitive
  question), Place-as-resource and the dwell-attribute pile (awaiting
  the RDF/dataframe rule of thumb), tempo metrics, tow/escort legs.

## Product findings (batch-2 ledger)

1. **stage_revision kind="graph" has no dry-run planner** — the
   preview loop is realized as stage → apply_staged_revision
   dry_run=true → apply. Either wire dry_run for kind="graph" or
   document the realized loop as the intended one.
2. **Term supersession has no first-class channel**:
   record_claim_reconsideration rejects non-Claim IRIs; no
   supersededBy/deprecated predicate exists in the base ontology, so
   comment-text conventions are doing structural work. A real
   vocabulary-lifecycle gap, now with two sessions of evidence (5, 10).
3. Lexical search tokenization can't find "couldn't-say"/"mergesGap"
   prose — synonym-guessing required.
4. aisv: CURIE expansion still unregistered (known); describe_revision
   aspect params and the graph-patch dict remain error-discovered.
