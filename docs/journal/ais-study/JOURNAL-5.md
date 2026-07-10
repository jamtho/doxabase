# JOURNAL-5 — Session 5: Distill the Vessel-Doings Vocabulary

Analyst 5 (the distiller). Task: harvest the 18 vessel stories + methods +
caveats + expert observations; distill a MINIMAL `aisv:` vocabulary
(https://ais.study/ns#); stage it into the ontology graph via
stage_revision(kind="graph"); prove it by re-expressing 3 stories; write
VOCAB-NOTE.md.

## Orientation

- tools dumped once to tools5.json (25 tools, same byte count as prior sessions).
- Read predecessors' journals (permitted context; scratch files untouched).
- Interfaces: bridge.py only; JSON via scratch file + "$(cat f)"; query.py only
  if a term's justification needs a fresh check.
- Read docs: staged_revisions, ontology_primer, mcp_tools#stage-revision-kind-graph.
  stage_revision(kind=graph) spec: summary/rationale required; additions =
  Turtle payloads targeting one mutable graph role; supporting_patterns etc.
  accepted; validation_scope default 'all'.
- Kernel predicates to REUSE on event resources (not duplicate): rc:summary,
  rc:supportingClaim (confirmed in patterns graph), rdfs:label/comment/seeAlso.
- vessel/mmsi-N resources exist only as bare pattern/claim targets (0 outgoing
  triples) — free to type as aisv: identities in the map revision.

## Harvest (done)

Read all 20 vessel stories (18 ais.study pattern/vessel-* + 2 generated:
367615990 JACOB BRENT/PERCIVAL, 338617000 PENNSYLVANIA), all 6 method
patterns (M1-M6), all 24 caveats, 4 expert observations (a79e1c6e keep
curiosities + track segregation; 6b13e8f8 draft-weighing/ballast/backdating;
70bbc8a0 coverage envelope; bb0e36d6 identity freeze is upstream).

Tabulation of what stories actually needed to say:

THINGS:
- Physical emitter distinct from the MMSI identity: needed by every shared-MMSI
  story (367373000, 360000000, 999999999, 367369920, 368574000).
- Emitter kinds: vessel (most), fixed installation (368166560, 367373000-e1),
  gear beacon (941217116 + 338000000 pipe beacons in 999999999/M2), aircraft
  (111227501 only — single story).
- The MMSI identity slot itself as the thing stories are about before emitter
  separation (all stories target vessel/mmsi-N).

EVENTS:
- Identity change: rename (311050400, 367677560, 367615990), reassignment
  (366991421, M1 LOTTUS->EVER FOCUS), statics-correction (366991421),
  slot-handover between sharers (360000000, 367369920), collision-then-relabel
  (368574000). One event class + mechanism beats five classes.
- Dwell periods: port/terminal calls (338617000 x6, 303520000, 538002783),
  lay-ups/refits (311050400, 316001262, 366971370), worksite deployments
  (369305000, 338024391), berth stays (366991421).
- Silence periods: in-place power-down (366971370, 366991421), coverage-exit
  voyage (538002783 x2, 366991421 Panama, M3 GOLDEN BEAR), gear recovery
  (941217116), unexplained (367615990).
- Cargo operations from draft: 303520000, 538002783, 367677560, 338617000,
  366971370 (dry-bulk M4 gap), M4 PEGASUS VOYAGER; ballast ambiguity is load-
  bearing (303520000 + expert 6b13e8f8).
- Operational ties: project-fleet sisters (369305000), towed spread + tug
  (338024391), company tug pair (M5 SMITH).
- Observed transits/excursions/repositionings (367615990, 311050400,
  338024391): candidate Voyage class — DELIBERATELY LEFT OUT (see couldn't-say).

ASSESSMENTS:
- Emitter multiplicity of an MMSI: single / position_jitter / multi_emitter /
  placeholder_shared (M2 + 367615990, 338617000 gray-zone resolutions).
- Hull-continuity basis across identity change: imo+callsign (367677560),
  dims+operating continuity (367615990), draft continuity (366991421),
  position-stream continuity (368574000), forged/none (367369920).
- Dating quality: apparent Jan-1 feed date vs real window (all identity
  stories); windowed-to-lay-up (311050400, 366991421), undatable (367615990,
  367677560), behaviourally dated (368574000 ~04-18).
- Operating profile / story-kind line: every story has one (metronome, seasonal
  trader, hub-and-spokes, niche shuttle, corridor linehaul...).
- Place naming is position-inferred, never verified geocode (M4/M6 convention,
  338024391, 338617000).

## Distillation decisions

- One IdentityChange class + aisv:changeMechanism literal, NOT five event
  subclasses (rule: prefer properties).
- One DwellPeriod class + aisv:dwellKind covers port call/lay-up/refit/
  worksite/berth-stay (each kind justified by >=2 stories).
- SilencePeriod + aisv:silenceReading mirrors M3's classes; silence is an
  evidence-state, not behaviour (m3-silence-is-not-dark honored in comment).
- CargoOperation + aisv:cargoDirection with 'ambiguous_ballast' as an explicit
  value (the 303520000 lesson).
- OperationalTie + aisv:tieKind for M5-class relationships.
- Emitter + aisv:usesMmsi + aisv:emitterKind for shared/non-ship MMSIs;
  AisIdentity + aisv:emitterMultiplicity for the identity slot.
- Assessments as literal-valued properties (datingQuality, hullContinuityBasis,
  apparentDate) — reuse rc:Claim/rc:supportingClaim for epistemics, no new
  confidence machinery.
- Values are documented literals, not minted individuals (keeps term count at
  25 and avoids justifying 20+ individuals).
- LEFT OUT (couldn't-say candidates): Voyage/excursion events, distanceKm,
  draftShift (structured draft values), operating-tempo metrics, data-quality
  artifact events, Place as a class, aircraft as anything more than an
  emitterKind value (single story).

## Revision 1: ontology vocabulary (done)

- Turtle validated locally with rdflib first: 129 triples, 7 classes + 18
  properties = 25 terms, every term has rdfs:comment with justified-by.
- staged: revision 1cb51827-077b-485e-b20b-38166a3927f0 (stance
  rc:CandidateRevision, patch 04002b7b, +129 triples to ontology graph,
  staged-time SHACL conforms, scope all).
- dry-run apply check: status ready, can_apply true, semantic_risk
  'attention' only because support links exist (expected).
- applied: applied-revision 63a8dbb1-4d56-4ada-8b1b-947d392c6442,
  validation_conforms true, 0 results.
- validate_graph scope=all after apply: conforms=true, 0 results.

## Revision 2: three stories re-expressed in the map graph

Picks (diverse kinds): 311050400 (rename + lay-up dwells, windowed dating),
538002783 (cargo ops + coverage-exit silences), 367369920 (fleet clone:
emitters + slot handover + forged corroborator). OperationalTie/tieKind/
dwellKind=worksite stay staged-but-unproven (noted in report).
Findings while writing the Turtle (feed the couldn't-say list):
- Stories speak in AGGREGATES (224 events, 16+ loadings, no discharge at
  hub); no term for a recurring event cluster / trade lane. CargoOperation
  resources for NOR'EASTER stand for clusters, flagged in rc:summary.
- datingQuality has no honest value for the clone slot-handover: no real-
  world event exists at all. Omitted rather than force-fit.
- Emitter home base: aisv:place is event-scoped; emitter bases went into
  rc:summary prose.

### Revision 2 execution log

- First candidate 82e62837 staged; SHACL preview FAILED (41 results): the
  base shapes treat any subject of rc:supportingClaim as a pattern
  (requires patternText/rationale/patternTarget/summary), and rc:hasClaim
  is domain-bound to rc:Observation. Lesson: kernel claim-link predicates
  are reserved for kernel classes; foreign event resources must cite
  claims via rdfs:seeAlso and carry prose in rdfs:comment.
- Repaired payload (rdfs:seeAlso / rdfs:comment swap only) staged as
  alternative cca8ed52-5cf5-471b-a61b-670da733b6cb: staged validation
  conforms; dry-run apply check ready (alternative gate informational -
  source unapplied); applied as 82dcb85b-05f1-434b-92b9-c555584966b8,
  +108 triples to map, validation conforms 0 results.
- Closed the failed row via stage_revision(kind=review_decision,
  decision=superseded). TWO frictions here: (1) decision enum is
  accepted_elsewhere/discarded/no_effective_change/superseded (doc doesn't
  list them; targeted error does); (2) I passed resolution_revision_iri=
  cca8ed52 believing it a successor pointer - it is actually the IRI AT
  WHICH the decision record is written, so the tool wrote a second
  createdAt/revisionType/summary/rationale/changedGraph/snapshot onto the
  successor row and broke SHACL (7 max-count violations on cca8ed52 and
  its snapshot/1).
- History repair: export_bundle(kind=trig, graphs=[history]) -> removed
  exactly the 12 mis-addressed triples with rdflib (digest disambiguated
  against the failed twin's map@537 snapshot: original 2b877064, stray
  b5f91fc9) -> import_bundle(kind=trig, replace=true) -> validate all
  conforms 0. Then re-recorded the review decision WITHOUT
  resolution_revision_iri; tool minted graph-revision/674ffe5a-8d8f-428a-
  b45c-0bb3fdeb21cb correctly; closes_current_staged_work true.
- Final state: validate_graph scope=all conforms=true 0 results;
  list_revisions current_staged_work_only=true -> 0 rows;
  plan_staged_revision_recovery -> no mutation frontier.
- Spot-checks: ns#IdentityChange live in ontology graph (6 triples);
  event/367369920-slot-handover live in map with all aisv: properties.

## Deliverables

- VOCAB-NOTE.md written (vocabulary table, couldn't-say list, 10-line
  reflection).
- Revision ledger:
  - ontology vocab: staged 1cb51827-077b-485e-b20b-38166a3927f0 ->
    applied 63a8dbb1-4d56-4ada-8b1b-947d392c6442 (+129 triples).
  - map proof: staged cca8ed52-5cf5-471b-a61b-670da733b6cb (alternative
    to failed 82e62837-e14b-491e-a282-dce37c73b2ca) -> applied
    82dcb85b-05f1-434b-92b9-c555584966b8 (+108 triples, 13 resources).
  - review decision closing 82e62837: graph-revision/674ffe5a-8d8f-428a-
    b45c-0bb3fdeb21cb (superseded).

## Friction notes (for the product)

1. Base shapes silently reserve rc:supportingClaim (pattern contract via
   targetSubjectsOf) and rc:hasClaim (domain rc:Observation): there is no
   documented way for a project-domain resource to cite an rc:Claim. The
   ontology_primer encourages project namespaces but the epistemic-link
   predicates don't extend to them. rdfs:seeAlso works but is weak
   semantics. Product gap: an open 'citesClaim' predicate.
2. stage_revision(kind=review_decision): resolution_revision_iri is the
   IRI to MINT the decision record at, not a pointer to the resolving
   revision. Passing an existing revision IRI silently corrupts that row
   (duplicate single-cardinality fields; SHACL only catches it on the
   next full validate). The tool should refuse an IRI that already exists
   in history.
3. review_decision's valid decisions are only discoverable via the
   targeted error, and 'rejected' is not among them (superseded fits a
   validation-failed-with-successor row).
4. No staged route exists for repairing the history graph itself
   (stage_revision refuses history targets by design), so the only remedy
   for friction #2 was raw TriG export/edit/reimport with replace=true -
   heavy machinery for removing 12 triples, and it bypasses the staged
   review trail (documented here instead).
5. Positive: staging-time SHACL preview on kind=graph caught the
   rc:supportingClaim mistake before anything touched the map graph -
   the stage -> dry-run -> apply -> validate loop worked exactly as
   intended, twice.
6. bridge.py + scratch-file JSON + "$(cat f)" had zero quoting incidents
   across ~45 calls (apostrophes in NOR'EASTER etc. included).
7. No query.py calls were needed: every term's justification was already
   in recorded knowledge - which is itself evidence for the capsule
   experiment's thesis.
