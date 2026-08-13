# GERRIT-PILOT-1 — phase-2 harvest arm, tranche 1, on the frozen v3 vocabulary

**Date**: 2026-08-13. **Operator**: gerrit-pilot-1 archivist, per the scout memo
(`docs/journal/knowhow-study/gerrit-scout-memo.md` — its pilot shape and two GO
conditions treated as law: the chained-inline-thread filter, not raw counts; the
AI-participant question investigated honestly) and the v3 vocabulary
(VOCAB-NOTE-KH3 / DISTILL-3: shapes carry kh:observedInCorpus, termini carry
basis+surface, machine participants are typed actors, the terminus-reversal
graveyard entry names Gerrit as its expected revival source).

**Hard rules honored**: review.opendev.org public REST only; UA
`doxabase-knowhow-gerrit-pilot/0.1`; **2.0s pace** (robots.txt crawl-delay — the
scout's 1.2s was flagged as a pilot correction and is corrected here); every
operation ledgered to `ops_ledger.jsonl` before firing; budget 120 enforced
mechanically in `fetch.sh`; the scout's 12 graded changes and raw fetches REUSED,
not re-fetched. Person-model claims permitted this tranche under the owner's
public-record posture: at most 3, each on >=2 independent-change sightings, each
carrying kh:authorityBasis kh:publicRecordRegime, names as public Gerrit
identities. Corpus-separate: nothing here writes to any capsule but
`/home/codex/gerrit-knowhow/capsule.sqlite`.

## Setup log

- `/home/codex/gerrit-knowhow/` created; `uv venv venv`; doxabase 0.2.0 wheel
  installed from `/workspaces/doxybase/dist` (wheel mtime 2026-08-13 00:48, newer
  than the last source-touching commit 2026-08-10 — no rebuild needed; repo
  untouched).
- `bridge.py` copied from the AIS study — the only door to the capsule.
- Capsule seeded (`DoxaBase('capsule.sqlite')`).
- **v3 seed imported**: `/home/codex/knowhow-study/kh-vocab-seed.trig` via
  `import_bundle` — first call hit the kind/spec targeted error (fields belong in
  `spec`), which taught the fix in one step, as designed; imported 1151 quads
  (ontology 724, shapes 427). `validate_graph scope=all`: **conforms, 0 results**.
- v3 terms verified present: `kh:observedInCorpus` (on all 22 EpisodeShape
  individuals, incl. the 9 dialect shapes), `kh:MachineParticipant` (with the
  machines-are-never-persons law in its comment), `kh:terminusBasis`,
  `kh:TerminusSurface` (narrated/silent individuals), `kh:publicRecordRegime` (the
  owner's reasoning quoted verbatim), `khcap:` registry nodes for
  knowhow-study/enron/syzbot.
- SHACL constraints for everything this tranche stages were read out of the seed
  BEFORE staging (EpisodeNodeShape, EpisodeV2/V3, Arc + ArcV3 + the rc:Pattern
  dual-typing trap both prior pilots hit, MachineParticipantShape, PersonShape,
  PersonModelClaimShape, CapsuleShape, EpisodeShapeShape).

## Network-operation ledger (running; budget 120)

- ops 1-6: bulk list calls, 6 new projects (keystone, glance, swift, ironic,
  manila, octavia), `status:merged`, n=50 each, with
  ALL_REVISIONS+MESSAGES+DETAILED_LABELS+DETAILED_ACCOUNTS (the scout's lists
  lacked DETAILED_ACCOUNTS; its 3 lists for nova/neutron/cinder are reused as-is).
  300 new changes screened at 6 ops.
- ops 7-8: AI-marker probes — `message:"Generated-By"` and `message:"Assisted-By"`
  cross-project (n=30 each). These two ops alone settled the direction of RQ2
  (below).
- op 9: revert-stream probe — `message:"This reverts commit"` over
  nova/neutron/cinder/keystone/ironic (n=40), for the terminus-reversal question.
- ops 10-89: 80 per-change `/comments` calls (the chained-thread filter signal +
  full quotable threads, one op per candidate — the scout's 2-op grading substrate
  collapsed to 1 op/change because the bulk lists already carry messages+labels).
- op 90: flagship reversal original (`q=commit:eab0de29...` -> nova #891036).
- op 91: comments for revert #950336 (rubber-stamp — confirms the reversal
  DISCUSSION lives in the revert commit message + original change, not inline).
- Zero errors, zero anti-bot friction, all HTTP 200 (fetch log verified).

## Screening (free, from list data)

Tier-1 (REWORK-kind patchsets >= 3, scout's refined rule): 100 candidates of 450
listed across 9 projects (nova 16, neutron 12, cinder 18, keystone 8, glance 10,
swift 6, ironic 11, manila 11, octavia 8), scout's 12 excluded.

Selection for grading (80 changes, tagged by reason in `selection.json`):
- 62 pure tier1 by rank (per-project quotas: nova 8, neutron 8, cinder 8,
  keystone 7, glance 7, swift 5, ironic 9, manila 8, octavia 6);
- 3 tier1+AI-known, 9 ai-forced sub-tier1 (deliberate RQ2 sampling from the probe
  hits present in our lists; Zanata imports and a trivial one-liner excluded);
- 4 traps (driver-heavy, REWORK<3, >=12 tag-null messages — the vendor-CI
  inflation signature, deliberately graded for RQ4);
- 2 restore-event changes (cinder #988260, #994947 — RQ1 adjacent texture).

Chained-thread filter result (from the 80 comments calls): 47/80 carry >=2
chained inline/patchset-level threads. By selection reason: tier1 44/62 (71%),
tier1+ai 1/3, ai-forced 0/9, traps 2/4, restores 0/2. The ai-forced zero is
itself RQ2 texture (AI-authored changes in this sample get thin chained review).

## Pre-grading findings (fixed by the probes + mechanical census, before any grades)

### RQ2 broke open at op 8: the scout's zero-AI finding was a fetch-depth artifact

The two AI-marker probes (`message:"Generated-By"`, `message:"Assisted-By"`)
returned a dense 2025-2026 AI-authorship layer across OpenStack: Generated-By
trailers naming Claude Fable 5, Claude Opus 5, Claude Code (claude-fable-5),
OpenCode (claude-opus-4.6), GitHub Copilot (Claude Opus 4.6), Kiro-cli
(trove, neutron, ironic, designate, tooz, ceilometer, masakari-monitors);
Assisted-By trailers naming Claude Opus 4.6/4.8/5, Claude Sonnet 4.5/4.6,
OpenAI GPT-5.6 Sol, Codex, Kiro (manila, ironic, ironic-python-agent, neutron,
nova, octavia, cyborg, rally, security-doc). The ironic container-steps series
alone carries ~10 `Assisted-by: Claude Opus 4.8` changes (July 2026).

**Scout correction (honest record)**: two of the scout's own 12 graded changes
are AI-authored — #977349 (its A-graded "author self-narrates root-cause"
exemplar: `Generated-by: GitHub Copilot (Claude Opus 4.6)`) and #995162 (its
B-graded unresolved-minus-2 exemplar: `Generated-By: OpenCode (claude-opus-4.6)`).
The scout reported "no AI-authored or AI-review-bot participant" because it never
fetched commit messages. Recorded as observation m-authorship-census.

### A content-generating AI reviewer exists, in-band, and was publicly renegotiated

octavia runs (ran) an AI review agent: Gerrit tag `autogenerated:claude-review`,
banner "*Reviewed by claude-sonnet-4-6*", posting structured code reviews AND
DevStack integration-test result tables, under its operator's own account
(sightings: 990822, 990783, 993556, 983016, 986889). On #993556 the community
renegotiated its participation: an objection priced review-attention ("I have now
to review this review, rather then review the code"), a second reviewer audited a
machine finding down to a bounded corner case, and the operator disabled the
agent's posting in stages, ending with a stated protocol ("I've disabled it's
ability to post to Gerrit and I'll parse the output myself for useful info in
future"). Contrast with the kernel's Sashiko (off-list, behind URLs, entering as
human restatement): Gerrit's machine reviewer is in-band, tagged autogenerated,
no-vote by design, and its terms were renegotiated in public. Observation
m-claude-review.

Also fixed pre-grading: the kernel relay formula reappears verbatim in swift
#996633 ("another review comment from Claude which makes sense to me." — and its
counterpart, a human refuting the machine against its own earlier advice); the
OpenInfra AI policy is enforced as a process norm in two independent changes
(manila #989946, octavia #970404: detect -> cite written policy -> author
discloses/amends) — a Gerrit-native dialect shape candidate at n=2, journaled for
the distiller, not minted here. Observations m-relay-swift, m-disclosure.

### RQ1: the revert stream supplies the reversal events the graveyard term waits for

Three independent apply-then-reopen instances, all with verbatim in-record
reversal reasons (observations rev-glance-location, rev-ironic-power,
rev-neutron-chassis):
1. **nova glance-location cycle** — #891036 merged 2025-04-24; reopened 25 days
   later by revert #950336 ("Due to glance behavioral changes... undeletable
   images. Revert this until glance can resolve the issue."); re-decided by
   Revert^2 #950623 merged 2025-08-07, gated Depends-On the glance fix. A full
   apply -> reopen -> re-decide cycle.
2. **ironic #985362** — merged soft-power-off change reopened by a late regression
   ("causing fast-track to not work for PXE (but it should)").
3. **neutron #963390** — merged OVN chassis change reopened NEXT DAY by
   cross-project breakage ("this patch is breaking the Ironic CI") — the closest
   structural echo of the kernel's asus cross-subsystem event.
Adjacent non-instances kept honest: #975846 (revert used proactively to force a
discussion), cinder abandon->restore pairs (#988260, #994947 — they reopen an
abandonment, not an apply).

### Vendor-CI census (450 changes): the trap is real but narrower than 2022-2023

Zuul on 449/450. NetApp-CI (48 changes) and Pure Storage Third-Party CI (29)
still post build results on the tag=null human channel; NEC, Seagate, HPE MSA,
Dell PVME, SAP and others have migrated to `autogenerated:*` tags; ExaScaler
posts through a personal-named account ("Ranjith"), and HPE's manila CI posts as
"ananta agarwalla" — vendor CIs wearing human names. No vendor CI in the census
left a single inline file/line comment: the chained-thread filter's immunity
mechanism held at N=450. Observation m-vendor-ci.

## Grading (4 parallel graders, GRADING-BRIEF.md, digests only)

**N=80 newly graded: A=28, B=28, C=24 (70% A+B).** Per project: nova 4/3/2
(A/B/C), neutron 3/4/2, cinder 3/8/2, keystone 1/1/5, glance 1/5/1, swift 4/0/1,
ironic 4/3/7, manila 4/3/2, octavia 4/1/2. 130 episodes proposed; **277/277
quotes passed mechanical digest verification (whitespace-normalized), zero
failures** — the quote discipline held across all four graders. One grader
independently reported all its C-grades had zero chained threads ("matching
traps #1 and #2 explicitly").

### Filter precision (RQ4, the tranche's sharpest number)

| Slice | chained>=2 | chained<=1 |
|---|---|---|
| All 80 | **47/47 A+B (100%)** | 9/33 A+B (27%, all B) |
| Driver-heavy (cinder/ironic/manila) | **19/19 A+B (100%)** | 6/17 (35%) |

The four deliberate traps split exactly on the filter line: chained>=2 traps
(978564, 990291) graded B — the filter RECOVERED real formation the raw counts
obscured; chained<=1 traps (980853, 990681) graded C. Caveats recorded in
meta-rq4: the filter trades recall (9 B's below the line) for its precision;
graders saw chained counts in digest headers; the sample was Tier-1 pre-ranked.

## Harvest record (all applied, conforms after each, zero staged debt)

- **74 harvest/evidence observations** (2 anchors, 5 machine-texture, 3 reversal,
  62 curated-episode 1:1, 2 scout-supplements) + **6 metas** (5 RQ verdicts +
  session) = 80 observations / 80 evidence.
- **R1** (ontology, 19 triples): khcap:gerrit-knowhow registered (CapsuleShape:
  label/comment/seeAlso->registry obs) + **15 kh:observedInCorpus uptake edges**
  — every uptake edge backed by >=2 independent-change instances now IN this
  capsule's map graph, not journal-trusted.
- **R2** (map, 522 triples): 62 kh:Episode (each: one label, one decision,
  rationale/outcome as verbatim-wrapped quotes, kh:fromObservation anchor,
  hasShape from the imported v3 individuals; machineActor/machineOutcome/
  relayVouch/attestedNotWitnessed where earned); 4 kh:MachineParticipant (zuul,
  claude-review-octavia, claude-assistant, netapp-ci); 3 kh:Person + **3
  kh:PersonModelClaim under kh:publicRecordRegime** — the mandate's exact
  ceiling, each with >=2 independent-change sightings, assessedAt=2026-08-13,
  explicit assessment windows, claimEvidence >=2:
  1. *kajinami-evidence-and-confession* (952308 confession + 996316 real-hw
     validation + 994764 confession; scout 994343 as third family);
  2. *mooney-layering-boundary* (994342 boundary -1 + scout 990552);
  3. *alonso-mechanics-as-instruments* (963390/975846 reverts + scout 995162
     -2 + 995666 AI relay).
- **R3** (map, 86 triples): **5 kh:Arc** dual-typed rc:Pattern. First staging
  FAILED the gate — rc:patternTarget requires IRIs, not prose (the rc:Pattern
  dual-typing gate's third pilot appearance, new variant; syzbot convention
  adopted: change URLs as targets); row closed discarded with rationale,
  restaged, applied clean.

### The five arcs (2 narratedTerminus — the first outside the kernel corpus)

1. **octavia-ai-review-renegotiation** (narrated; onset off-record, marked via
   inCorpusArrival) — pivot: *"I am extremely confused by AI reviews of the
   code..."*; became automatic: machine output human-filtered as standing
   practice.
2. **nova-glance-location-reversal-cycle** (narrated) — the apply->reopen->
   re-decide cycle; pivot: the revert's own reason; re-decision gated Depends-On.
3. **nova-compute-manager-boundary** (silent) — three changes, two enforcers
   (sean mooney 990552/994342, Dan Smith 998752); boundary holds unargued by
   994930.
4. **ironic-node-history-onboarding** (silent) — norms run unprompted by the
   series' end ("I've removed the Depends-On line in the latest patchset").
5. **swift-human-machine-review-loop** (silent) — relay-with-vouch + refute-
   against-the-machine's-own-record, one lifecycle.

Every pivot verbatim-verified; all five have in-record termini — nothing mid-arc
was promoted.

## Research-question verdicts (full text in the meta observations)

- **RQ1 (terminus reversal)**: revival condition MET — three independent
  apply-then-reopen instances from exactly the stream the graveyard entry
  predicted (glance-location cycle, ironic 985362, neutron 963390); instances
  recorded here with typed episodes + arc; **the revival act itself belongs to
  the home distiller** via re-expression (sourceCapsule khcap:gerrit-knowhow).
  Abandon->restore and revert-to-discuss kept distinct as non-instances.
- **RQ2 (AI participants)**: rich but **authorship-forward and policy-mediated**
  — near-inverse of the kernel's reviewer-forward texture. Trailer-disclosed AI
  authorship across 15+ projects (12 graded AI-known changes: 9 C / 2 B / 1 A —
  thin review is the norm but not intrinsic, see 999279); one in-band AI reviewer
  publicly renegotiated away; the kernel relay formula transferring verbatim;
  disclosure enforcement against the WRITTEN OpenInfra policy. Scout's zero-AI
  finding corrected: a fetch-depth artifact (two of its own 12 were AI-authored).
- **RQ3 (dialect transfer)**: kernel shapes transfer broadly — 15 shapes earned
  gerrit uptake edges at >=2 in-graph instances (objectionRevision 6 changes,
  diagnosisExchange 6, expertCorrectionAdopted 7, reversalWithEvidence 7,
  deferralWithTrigger 7, boundaryAssertion 6...). The email-dialect shapes'
  strong showing (boundaryAssertion 6, counterpartyPositionHold 4) says they are
  less genre-bound than their single-corpus marking implies. Gerrit's OWN
  dialect, journaled for the distiller, not minted: **aiDisclosureEnforced**
  (n=2: 989946, 970404), **crossChangeResolution** (n>=3: 994764->994930,
  998385->999724, 995666->series), **offRecordCallClose** (n=2: 989469, 992034).
  Not observed: scopedDelegationRequest (1 borderline), dormancyBrokenByPing.
- **RQ4 (vendor-CI trap)**: filter precision CONFIRMED (table above); mechanism
  verified at N=450 — zero vendor-CI inline comments anywhere; NetApp-CI (48)
  and Pure Storage CI (29) still on the tag=null channel; fleet partially
  migrated to autogenerated tags; two vendor CIs post under personal names.
- **RQ5 (economics)**: **1.14 ops/graded change, 1.63 ops/A+B unit** (kernel:
  ~3.0 / ~4.4; scout projected 2.0/change) — the bulk list with
  DETAILED_ACCOUNTS carries the grading substrate, so grading costs one
  /comments call. A 150-200-change pilot at the measured rate ≈ 180-240 ops.

## Ops accounting — CLOSED

**91 of 120 budget used**: 6 project lists + 3 probes + 80 comments + 1
flagship-original lookup + 1 revert-comments follow-up. Zero errors, zero
anti-bot friction, all HTTP 200; every op ledgered before firing; 2.0s pace
honored throughout; scout raw data reused without re-fetch (0 ops). 29 unused.

## Final state (graph-verified read-only, not journal-trusted)

validate_graph scope=all: conforms, 0 results (after every apply and at close).
plan_staged_revision_recovery: 0 rows. Map graph census via read-only sqlite:
62 kh:Episode, 5 kh:Arc (+5 rc:Pattern dual-types), 4 kh:MachineParticipant,
3 kh:Person, 3 kh:PersonModelClaim; ontology carries 15 gerrit uptake edges +
khcap:gerrit-knowhow. export_preflight: scanner clean, shareability review
required-not-completed (correct — nothing leaves without the owner). Retrieval
sanity: the AI-renegotiation arc ranks FIRST for its natural query (above
observation and history rows); reversal observations rank 1-2 for theirs.

## Friction (for the product ledger)

1. **rc:patternTarget NodeKind trap** — the rc:Pattern dual-typing gate's THIRD
   pilot appearance (Enron 3-stagings, syzbot 20-violation staging, now this
   variant: prose vs IRI targets). The seed's ArcShape still doesn't mention the
   base Pattern shape's requirements; each new harvester pays one failed staging
   to learn them. The one-line ArcShape note (syzbot friction 2) is now
   thrice-earned.
2. **History rows in search**: improved but present — live nodes now outrank
   history patch rows for arc queries (rank 1 vs 3), but full staged-payload
   literals still surface on page one. Sixth sighting family for the
   graph-role-filter fix.
3. **export_preflight remains blind to typed sensitive categories** — khgp:/
   khgpm: person content in a NON-home capsule now joins the family (nothing
   fired; correct only because the shareability-review block holds everything).
   The category-aware scanner's justification grows a fourth time.
4. **Positive**: the kind/spec targeted errors taught import_bundle and
   review_decision in one step each, as designed; stage/apply worked first-try
   for R1/R2; the 1:1 obs-per-episode pipeline (syzbot pattern) scaled to 62
   without friction.
5. **Grader-scale**: 4 Sonnet graders, ~20 digests each, all four returned
   parseable single-file outputs with zero quote failures — the brief's
   enumerated traps (vendor-CI, patchset lies, quote discipline) fully amortized;
   no resumptions needed this time.

## For the next distiller (explicitly queued)

- RQ1 instances await home-capsule re-expression to revive the terminus-reversal
  term (>=2 independent events now exist; counting note in meta-rq1).
- Three Gerrit-dialect shape candidates with instance pointers (meta-rq3).
- The email-dialect shapes' genre-boundedness deserves a re-look given their
  Gerrit uptake.
- Machine-outcome enum: this corpus adds outcome kinds (renegotiated-away,
  policy-disclosure-complied, refuted-against-own-record) to the kernel's seven;
  the enum refusal can be re-tested against the merged tally.
- The claude-review agent's announced return "behind a proper service account"
  is a natural continuation probe for tranche 2.
