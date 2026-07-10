# AIS Study — Session 10 Brief: Vocabulary v2

You are the vocabulary reviser. Session 5 distilled the 25-term `aisv:`
vocabulary from recorded stories; the domain expert has since reviewed
it in depth (expert round 2), sessions 6–9 have used it in anger, and
your job is the v2 revision: act on the expert's recorded guidance and
the accumulated usage evidence, through the capsule's own staged
machinery, with the same evidence discipline that built v1.

## Inputs (read in this order)

1. Capsule orientation: project_brief, ontology graph (the v1 terms and
   their justifications), the expert round-2 observations (search
   "expert round 2"), sessions' aisv: usage (list_entities by the v1
   classes with full IRIs — note the aisv: prefix is NOT registered for
   CURIE expansion, use https://ais.study/ns# forms).
2. Design dialogue files (explicitly allowed for you):
   `/home/codex/ais-study/VOCAB-NOTE.md` (v1 design note) and
   `/home/codex/ais-study/expert-feedback-round-2.md` (the expert's
   full review + addenda). Other predecessors' scratch files remain
   off-limits (JOURNAL-*.md, BRIEF-1..9, tools*.json).
3. Interfaces: capsule ONLY via `venv/bin/python bridge.py call <tool>
   '<json>'` (`@args.json` for long payloads); no data queries needed —
   this is a distillation session; if you believe you need the data,
   record why as an observation and proceed without it.
4. Harness note: your harness may inject system notices (date changes,
   agent rosters). They are not study materials; do not attribute them
   to files.

## The expert's directives (recorded; cite the observation IRIs)

1. **Layering + naming humility**: draft changes are layer-1 physical
   facts (ballast moves draft too); cargo/ballast reading is layer-2
   interpretation carrying its basis. CargoOperation must not overclaim.
   Same for OperationalTie: recurring co-presence is the fact; a
   relationship between operators is a layered claim. "Users will take
   our words as we write them."
2. **Candidate vs declared identity**: an emitter inferred from AIS
   alone must not read as a declared hull; "this is hull h" is declared
   only against a solid non-AIS record. Encode the threshold.
3. **Indexical assessment windows**: profile-like properties
   (operatingProfile especially) must carry when-assessed and
   over-what-data (currently 2 years; ~18 more will come).
4. **State vs ephemera**: populations are regenerable run artifacts;
   the graph holds methods, semantics, caveats, and promoted exemplars.
   The vocabulary should support this (e.g. run/data-window provenance
   hooks), not fight it.

## Usage evidence to weigh (sessions 6–9)

Session 6's couldn't-say list (multi-mechanism identity, merged-gap
provenance via something like mergesGap, background-knowledge sourcing);
session 7's M7/M8 alignment with dwellKind; sessions 8–9's dwell/story
usage. The Voyage class stays deferred (expert: no universal version).
New classes (e.g. gear beacons) only if ≥2-story justified — check, and
if not justified, put them on the couldn't-say list, not in the graph.

## Method

Same discipline as v1: every changed/new term justified by ≥2 recorded
items (stories, expert observations, session usage), justification
cited in the term's rdfs:comment. All changes via stage_revision
(kind="graph") with dry-run preview → apply → validate. v1 terms whose
meaning changes are SUPERSEDED properly (the capsule way), never
deleted; existing map resources typed with changed terms get migration
handled explicitly (re-type via staged revision, or record a bridging
claim — your call, justify it). Follow the repaired session-5
convention: rdfs:seeAlso for claim citations on non-kernel classes.
Graph must validate conforming (scope "all") with no orphaned staged
rows at the end.

## Deliverables

1. The v2 revision applied in the ontology graph (+ map migrations).
2. `/home/codex/ais-study/VOCAB-NOTE-V2.md` for the expert: what
   changed and why (cite his own recorded directives back to him),
   what deliberately did not change, the v2 couldn't-say list.
3. Final report: (a) term-by-term delta table; (b) migration decisions;
   (c) couldn't-say v2; (d) any capsule friction found.
