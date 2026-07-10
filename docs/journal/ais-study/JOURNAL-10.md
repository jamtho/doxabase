# JOURNAL-10 — Vocabulary v2 revision session

Role: vocabulary reviser (session 10). Brief: /home/codex/ais-study/BRIEF-10.md.

## Setup

- Read BRIEF-10.md, VOCAB-NOTE.md, expert-feedback-round-2.md (the two
  explicitly allowed design-dialogue files). Other predecessor scratch
  (JOURNAL-1..9, BRIEF-1..9, tools*.json) left unread.
- Dumped tool schemas via `bridge.py tools` to session scratchpad (not
  into the study dir, to avoid colliding with off-limits tools*.json).
- Bridge works; 25 doxabase.* tools available.

## Orientation (in brief order)

- project_brief: 7 datasets, 116 obs, 89 claims, 44 patterns, 8 graph
  revisions; queues = analysis_view_review (5), query_plan_handoff (2);
  nothing blocking for a distillation session.
- list_revisions current_staged_work_only=true -> count 0. Clean start:
  no orphaned staged rows before my work.
- Ontology graph = 129 triples; fetched full TriG of all 25 aisv: terms
  via get_context_graph -> work/v2/ontology-v1.trig. All comments carry
  justifications + rdfs:seeAlso per the repaired session-5 convention.
- Expert round-2 observation IRIs found via search (recorded digests of
  expert-feedback-round-2.md):
  - 14a4f98b-91c2-453d-84d8-a24e3bf6db1b layering + naming humility
    (CargoOperation, OperationalTie; "users will take our words...")
  - 563873b6-7bea-49dc-ae46-0b7c80940306 modelling primitives, usage
    periods vs events, deterministic-derivation principle
  - 8f177325-207e-4c29-92a3-41e7ae246343 indexical provenance
    (operatingProfile when-assessed / over-what-data)
  - 92240e42-d4a7-407f-b685-50b4dbd8a46a RDF/dataframe boundary, draft
    track-context, Voyage still subtle, tow/escort later
  - 72d7a572-3901-46b2-bdbd-ff9f818ad78a Transmitter existence: state
    vs ephemera, pre-minted vs AIS-inferred
  - 3b63b49b-7548-4401-837c-23bb54e701da identity-declaration threshold
    (hull declared only against solid non-AIS record)
  - 9333b23f-b7f4-40b9-b799-07b1fcec4c11 gear beacons (same-MMSI
    fleets, battery-in-COG, benign multi-emitter)
  - 1386b1ed / 62f41519 / 8f7db46c / c75d31f1 addenda 3-4 (tradecraft,
    shuttles, Foursquare, SOG bimodality) - context, not vocab-driving
- Usage in anger (list_entities per class, graph=map):
  - AisIdentity: 5 (311050400, 367369920, 368817000, 374158000,
    538002783)
  - Emitter: 3 (367369920 beaumont/lafourche units, 374158000
    long-beach unit)
  - IdentityChange: 3 (311050400 rename, 367369920 slot handover,
    374158000 statics correction)
  - DwellPeriod: 3; SilencePeriod: 5; CargoOperation: 2 (the NOR'EASTER
    cluster stand-ins); OperationalTie: 0 instances.
- Session 6 couldn't-say traces found in capsule: claim
  374158000-multi-site-emitters says "recorded as a couldn't-say for
  this session (see JOURNAL-6)"; silence event 368817000-silence-2025-06-08
  label notes "M3 splits this into two gap rows" (merged-gap
  provenance); session-6 staged revision edb20bff (applied a6aa2a1f).
- Session 7: pattern c768eaa1 = M8 draft-change track-context
  (at_berth / at_anchor / no_dwell_nearby / dwell_unclassified),
  operationalising the expert's berth/anchor/underway guidance; M7
  track-state layer, plus obs 0b47b24d (7th port stay found by M7).
- Sessions 8-9: M9 shuttle census + M10 stop-verification; populations
  live in work/*.parquet (dwell spans, m2 emitter classes), promoted
  exemplars in graph - the state-vs-ephemera split already practiced.
- Session-6 background-knowledge couldn't-say confirmed in capsule:
  claim 368817000-identity-and-mobility carries the USNS Comfort
  identification as prose flagged "not derived from the feed itself and
  not load-bearing"; claim 941217116-identity rests on ITU block
  conventions (world knowledge doing load-bearing work).
- Bridge friction #1: stage_revision kind='graph' has NO dry-run
  planner (dry_run supports map_assertion/profile_map_updates/
  query_evidence_overlay/systematisation only). The brief's "dry-run
  preview -> apply" is realized as stage -> apply_staged_revision
  dry_run=true (read-only apply check) -> apply.
- Patch format discovered by targeted-error probing: additions/removals
  = [{"graph": <role>, "content": <turtle>}].
- Apply dates for honest aisv:assessedAt values: session-5 proof
  applied 2026-07-06 (82dcb85b), session-6 stories 2026-07-07
  (a6aa2a1f).

## v2 design (before staging)

Fact/reading split made systematic (SilencePeriod/silenceReading was
v1's correct model; CargoOperation and OperationalTie now follow):

New classes (2): DraftChangeEvent (supersedes CargoOperation),
RecurringCoPresence (supersedes OperationalTie).
New properties (11): draftChangeReading (supersedes cargoDirection),
coPresenceReading (supersedes tieKind), readingBasis, trackContext
(M8's four values), assessedAt, assessmentDataWindow, derivedFromRun,
representsDetectorRows, ofEmitter, declaredHullRecord, externalBasis.
Superseded (4, retained + rewritten comments, never deleted):
CargoOperation, cargoDirection, OperationalTie, tieKind.
Strengthened comments (8, meaning-preserving appends): AisIdentity,
Emitter (+label), IdentityChange, SilencePeriod, operatingProfile,
emitterMultiplicity, emitterKind, silenceReading.

Deliberately NOT minted (couldn't-say v2): Voyage (expert: no
universal version), RecurrentPattern/lane class (expert agreed wait),
GearBeacon class / gear-fleet multiplicity value (only 1 in-feed story;
the expert's same-MMSI battery-in-COG fleet is unobserved in this
feed), MmsiUsagePeriod alternative primitive (isomorphic, deferred),
datingQuality 'not_a_real_world_event' (tied to the open primitive
question), Place-as-resource, structured draft values, tow/escort
events, dwell attribute pile (RDF/dataframe boundary awaiting the
expert's rule of thumb).

Map migration: retype the 2 CargoOperation cluster resources; move
cargoDirection -> draftChangeReading; add readingBasis/
representsDetectorRows/derivedFromRun; representsDetectorRows +
derivedFromRun on the merged-gap silence; ofEmitter on the 374158000
statics-correction; externalBasis on vessel 368817000; assessedAt +
assessmentDataWindow on the 8 profile-bearing resources (5 vessels, 3
emitters; dates 2026-07-06/07 from history).

## Staging

Payloads built programmatically (work/v2/build_ontology_rev.py,
build_map_rev.py) parsing the live-graph TriG slices with rdflib so
removal literals match byte-for-byte; both payload files kept
(work/v2/stage-ontology-v2.json, stage-map-v2.json).

1. Ontology v2: staged f5d7e085-00df-4587-aedd-215d29238e81
   (+114/-17 triples, pre-stage validation scope=all conforms) ->
   apply check dry_run: can_apply=true, status=ready, semantic risk
   'attention' (linked obs/claims/patterns - expected) -> applied as
   fc6d1b44-094b-4d94-a899-7e3ccad7977a, validation_conforms=true.
2. Map migration: staged e3a48b76-462c-470b-a9b0-5fde510027fd
   (+37/-7 triples, conforms) -> apply check ready -> applied as
   43c61b65-04e7-43a2-8aa7-ab4050faecb0, validation_conforms=true.
3. Attempted record_claim_reconsideration for the 4 term
   supersessions (relation=supersedes): rejected - "newer_claim must
   identify an existing rc:Claim". Terms are not claims; supersession
   is therefore carried by the rewritten term comments (v1 meaning
   quoted verbatim), seeAlso cross-links, and the revision metadata.
   Recorded as friction #2.

## Final state checks

- validate_graph scope=all: conforms=true, 0 results.
- list_revisions current_staged_work_only: 0 rows (no orphaned staged
  revisions).
- plan_staged_revision_recovery: "No staged revisions matched the
  recovery-plan selection."
- Spot-checked end state via get_context_graph: CargoOperation carries
  the supersession comment + seeAlso to DraftChangeEvent; the Saint
  John cluster resource is typed DraftChangeEvent with
  draftChangeReading/readingBasis/representsDetectorRows/
  derivedFromRun/assessedAt/assessmentDataWindow; the 374158000
  statics-correction carries ofEmitter; vessel 538002783 carries
  assessedAt 2026-07-06 + window.
- Wrote VOCAB-NOTE-V2.md (expert deliverable).

## Capsule friction found (for the report)

1. stage_revision kind='graph' has no dry-run planner even though the
   session-5-era convention (and this session's brief) describe a
   dry-run-preview step; the working equivalent is
   apply_staged_revision dry_run=true after staging. Either the
   planner or the documented convention should be aligned.
2. record_claim_reconsideration only accepts rc:Claim IRIs, so term
   supersession in the ontology graph has no first-class
   reconsideration record; there is also no supersededBy/deprecated
   predicate anywhere in the base ontology. Comment-text conventions
   are doing structural work.
3. The aisv: prefix is still not registered for CURIE expansion in
   bridge tools (brief warned of this; confirmed - full IRIs required
   everywhere).
4. search scope='graphs' tokenizes hyphenated terms oddly ("couldn't-
   say" matched nothing; "mergesGap" matched nothing even though the
   session-6 comment contains 'merges two mechanically-distinct M3 gap
   rows') - finding prose couldn't-says required knowing synonyms.
5. Minor: describe_revision aspect='auto' rejects include_triples
   (aspect-specific params take trial and error); get_context_graph
   has no 'raw resource set' profile, so fetching exact term triples
   rides on the dataset_brief profile's trig payload.

Session complete: v2 applied, validated conforming (scope all), no
orphaned staged rows, VOCAB-NOTE-V2.md delivered.

