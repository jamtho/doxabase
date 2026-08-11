# CROSS-CORPUS SYNTHESIS — three corpora, one vocabulary (phase-1 capstone)

**Date**: 2026-08-11 (overnight). **Role**: cross-corpus synthesist, closing the corpus program's
first phase. **Inputs**: the three capsules read directly (every count below re-verified against
the graphs, not trusted from journals — the program's own graph-over-journals law), plus the six
journals/memos (ENRON-PILOT-1, SYZBOT-PILOT-1, both scout memos, syzbot-sample-memo; ARCS-1-report,
VOCAB-NOTE-KH2, PROMOTE-1).

**Capsule states at synthesis time (all verified this session)**:

| | HOME (knowhow-study) | EMAIL (enron-knowhow) | KERNEL (syzbot-knowhow) |
|---|---|---|---|
| observations | 308 | 41 | 77 |
| kh:Episode | 55 | 36 | 61 |
| kh:Arc | 13 | 1 | 5 |
| kh:Heuristic | 10 | 0 | 0 |
| kh:PersonModelClaim | 7 (consent basis) | 6 (research-corpus basis) | 0 (posture unset — none allowed) |
| episodes carrying a hasShape | 42/55 (76%) | 5/36 (14%) | 21/61 (34%) |
| distinct shapes instantiated | 11 of 12 | 3 of 12 | 7 of 12 |
| validate_graph scope=all | conforms | conforms | conforms |
| staged debt | 0 | 0 | 0 |

---

## The three exhibits (concrete first, per your law)

### Exhibit 1 — the terminus, in three genres

Your dog-walk criterion — *the arc completes when its decisions stop being decisions* — is now a
three-genre empirical result. All three quotes below are graph-verified `kh:becameAutomatic`
values on live arcs:

- **Design history** (kha:identity-freeze): "Jan-1 identity dates are never again read as
  real-world events — cold agents apply the caveat without being taught it and are graded on
  doing so."
- **Year-2000 contract law** (khea:vitro-consolidation): "By late June the double-payment
  exposure test ... and the guaranty-as-post-execution-deliverable device are applied without
  re-derivation; after 06-26 no position is re-argued and the thread collapses into
  version-chasing" — the collapse itself audible in the record: "I just want to make sure that
  the fully executed document has been processed" → "now I'm trying to find the signed original."
- **Kernel review** (machine-authorship-norm arc): the only arc in any capsule whose
  becameAutomatic is stated *literally by a participant, in-thread*: a maintainer rejects an
  AI-authored From: line, and the bot operator closes the arc with "Now the sending mechanism
  will automatically set the right From: line" — a review norm converted into pipeline tooling
  so the objection can never need making again.

Score: 13/13 home, 1/1 email, 5/5 kernel arcs carry verbatim pivotQuote + becameAutomatic.
The completion criterion did not merely survive translation; kernel culture *implements* it.

### Exhibit 2 — one shape, three genres: selfCorrectionConfessed

Where an EpisodeShape names a genre-independent craft move, it transfers. The same reflex —
the confession travels into the durable record — in three unrelated crafts:

- **Home** (batch-regex over-reach, within the hour, unprompted): "My regex pass over-matched —
  reverting it and handing the precise reconciliation back to the agent that already has the
  full context."
- **Kay Mann, 2001** (three-word inline reversal to a paralegal): "Just use a regular CA
  **(yes, I changed my mind)**"; and minutes after sending drafting instructions: "I think I
  misspoke (or miswrote). The change I suggested would belong in both versions."
- **Kernel, 2026** (usbtmc): fifteen minutes after arguing a 1-byte endpoint is "not really"
  illegal, the reviewer posts a self-correction citing the spec table — and that correction
  becomes *the opening sentence of the v3 commit message*.

The three shapes with instances in all three corpora are exactly the genre-neutral ones:
expertCorrectionAdopted (6 home / 1 email / 9 kernel), deferralWithTrigger (6/2/2),
selfCorrectionConfessed (1/2/2).

### Exhibit 3 — the refusal, in three corpora: the discipline transferred better than any term

- **Home** (ARCS-1): one arc left mid-flight at corpus close; two single-window candidates
  deliberately unrecorded.
- **Email**: the GE-standardization arc REFUSED despite a clean onset and 7 rich members —
  its terminus lies outside the corpus (the master form still in progress at the edge: "How's
  the GE master form agreement coming along?"). becameAutomatic could not be honestly asserted.
- **Kernel**: kcov/PREEMPT_RT — the richest lifecycle in the whole corpus (draft→v7, an
  AI-sourced causal claim publicly refuted by the RT maintainer, the retraction reported back
  into the thread) — episodes recorded, arc NOT promoted: mid-arc at capture, no honest terminus.

And the mechanical half of the discipline transferred too: the SHACL staging gate refused
under-specified arcs in BOTH foreign capsules exactly as at home (Enron batch B: 4 MinCount
violations, graph untouched; syzbot batch B: 20 violations, restaged with real Pattern content).
The gates needed zero tuning for foreign material.

---

## 1. The generalization verdict, graded

**Transferred everywhere (graph-verified)**:
- The episode/arc/claim spine: kh:Episode with exactly-one-decision + fromObservation anchoring;
  kh:Arc ⊑ rc:Pattern with mandatory pivotQuote/becameAutomatic; evidence-cited observations
  under the ≥2 rule. The exactly-one-decision rule fit email surprisingly well (one message ≈
  one decision) and kernel natively (a vN changelog delta IS a dated decision with stated
  rationale — the genre writes kh:showsFormationOf linkage as a convention).
- The five OnsetShape kinds: every promoted foreign arc took an existing kind with no strain
  (email: questionArrives; kernel: anomalyRegistered ×4, casesAccumulate ×1). Onset kinds are
  more corpus-general than episode shapes — the Enron pilot predicted this and the kernel pilot
  confirmed it.
- The staging gates, supersede-retain, zero-staged-debt hygiene, verbatim-quote law
  (every foreign quote mechanically re-verified against source), and the refusal discipline
  (Exhibit 3).
- The vocabulary seed itself: `import_bundle` of kh-vocab-seed.trig landed first-try in both
  foreign capsules (731 triples; conforms immediately).

**Transferred partially — the EpisodeShape gradient, quantified**:
home 42/55 episodes shaped (76%, 11 of 12 shapes) → kernel 21/61 (34%, 7 of 12) →
email 5/36 (14%, 3 of 12). The gradient tracks **genre distance from the seed corpus**, not
corpus quality: kernel review is, like home, a review-of-an-evolving-artifact genre, so nearly
half the shapes carry over (with expertCorrectionAdopted dominating at 9 — kernel review IS
expert correction); email is a compression genre (reasoning pre-compressed to a sentence before
the ask), so only the genre-neutral reflex shapes survive. The five shapes with zero foreign
instances are precisely the operator-workflow ones: escalationToOwner, freshEyesUnderConstraint,
labelledWorkaround, decisionWithFalsificationTest, interruptionResume. Conclusion for the
architecture: **shapes are corpus-idiomatic; the spine is general.** A two-layer shape system
(small genre-neutral core + per-genre dialects) is the natural v3 design question.
(One journal discrepancy found and resolved by the graph: syzbot META-RQ1 says
expertCorrectionAdopted ×8; the live graph says 9 — batch C added one. Graph over journals.)

**Failed to transfer / unassertable**:
- From email: kh:conversionLatency, kh:frameAdopted, kh:correctedInFlight — all three absences
  predicted exactly by the scout's genre analysis (compression, not exposition; corrections
  happen *between* messages).
- Everywhere foreign: kh:ElicitationRound, kh:AttentionProtocol, kh:DelegationContract — zero
  foreign instances; they encode the owner-operator interface, not general craft.
- kh:consentBasis: unusable in both foreign regimes (Mann cannot consent; the living-maintainers
  posture is deliberately unset) — which is itself the finding that authority-basis needs to be
  a first-class dimension (see docket item 6).

**What each foreign corpus DEMANDED that home never showed**:
- **Email demanded**: four foreign shape candidates at ≥2 sightings each (scoped-delegation-
  request ≥4, counterparty-position-hold-with-invite ≥3, precedent-conformance-check ≥3,
  boundary-assertion ≥2); the micro-decision vs drafting-move distinction (single messages
  deciding 3–5 small things); **terminus-visibility-as-corpus-property** (becameAutomatic is
  only assertable when the thread outlives its formation — a property of the corpus, not of the
  understanding); and the person-model's **second authority regime** (research-corpus basis, doc
  16 §6.3's anticipated case, now instantiated in obs fdb34f6f with mitigations logged).
- **Kernel demanded**: **machine participants** (the dominant strain — machines author, review,
  validate, get publicly refuted, are invoked as anticipated FUTURE scrutiny, and price review
  churn; Sashiko in 10/47 lifecycles, patchwork-bot 12/47, Assisted-by trailers across three
  assistant vendors; seven observed human-outcome kinds for machine reviews:
  adopted-with-credit / adopted-with-recorded-skepticism / relayed-with-soft-vouch /
  resolved-by-citation / dismissed / ignored / void); **terminus REVERSAL** (hid/asus: v1
  applied to the tree, a cross-subsystem concurrency objection lands hours later, "Now dropped
  from the queue." — an applied decision resumes being a decision; no vocabulary can currently
  say this); **lifecycle ≠ bug identity** (one fix closes 4 extids; one extid carries 2 disjoint
  fixes; threads shared across bugs — kh:Arc absorbed it via multiple rc:patternTarget, but
  bug-keyed harvesting strains); **changelog-fossils** (formation attested ONLY by the artifact
  delta — off-list reviews behind URLs, uncaptured early versions — where kh:fromObservation
  wants a witnessed objection that does not exist on-list); and terminus-*surface* as a
  subsystem-tooling property (patchwork-narrated merge vs silence — two surfaces, one signature).

## 2. The heuristics docket check (each verified against actual foreign episodes)

**hotfix-narrow-migrate-deliberately — SECOND WITNESS FOUND. Recommend revival (not executed).**
The kernel capsule supplies two clean, independent sightings of the behavioural statement
("scope emergency fixes to the emergency; schedule the migration as a deliberate follow-up"):
- `56e3c883` (media/dri): the maintainer explains the patch "deliberately fixes the immediate
  crash with minimal change" after an earlier attempt at the broad fix produced non-trivial
  deadlocks; the reviewer "accepted the scoping, deferring the architectural rework."
- `daa88ce3` (net/zcrx): the developer weighs failing the getter properly, then settles "on
  shipping a 7.2 fix now and deferring anything nicer."
Plus two graded supplements the promotion would want: `e42356e4` (scope the fix to the
subsystem's ownership conventions, not the widest scope that works — an applicabilityCondition)
and `a5110d5e` (the narrow patch *withdrawn* because a broader fix was already in flight — a
knownFailureMode: don't hotfix-narrow when the deliberate migration already exists).
Graded honestly: the revival condition asked for "a second independent upstream break handled
hotfix-narrow"; these are the same craft rule under a different trigger (crash-fix scoping), and
they are third-party behaviour rather than operator behaviour — a new, arguably *stronger*
evidence tier (independent professionals exhibiting the rule). **Mechanical blocker, exactly as
PROMOTE-1 pre-stated**: khs:HeuristicShape requires citesEpisode → typed kh:Episode nodes, and
the witnesses live in the corpus-separate syzbot capsule. Reviving honestly forces the
cross-capsule-citation decision (or a sanctioned re-expression convention). Recommendation:
distiller-3 docket, owner decides the citation mechanism; do not weaken the gate.

**tests-encode-semantics — no second witness. Stays in the graveyard.**
Scanned both foreign corpora: no episode anywhere shows anyone *editing tests as semantic
assertions*. Kernel has adjacent instrumentation-semantics texture (`18c8de3f`: the OOB read is
invisible to KASAN because it lands inside the same heap object; `78294aca`: the reviewer builds
a 4094-vlan reproducer and tests the fix one layer further than the bug) — but that is about
test *reach*, not test *editing at semantic granularity*. Email has nothing test-shaped at all.
Revival still awaits the second-pair corpus or fresh product work.

**separation-conceptual-not-nominal — no second witness, and the nearest kernel material is
instructively the INVERSE.** The machine-authorship arc is genuinely about nominal-vs-conceptual
(the From: line vs who can certify the DCO), but the community's resolution *enforces the
nominal surface* — the tooling is changed so the From: line mechanically matches conceptual
authorship. That is attribution/identity, not a concept-level firewall; and the revival
condition explicitly names a firewall domain (the second private case study or the second-pair
corpus), which neither foreign corpus is. Stays.

**Bonus, outside the docket — the first cross-corpus heuristic RESONANCE**: promoted
khh:delegation-contract-form ("brief delegates with evidence, invariants, and role boundaries...
state falsifiable expectations") is independently exhibited by Kay Mann's scoped-delegation
claim — every commissioned review carries an explicit depth cap ("Nothing comprehensive, just a
fatal flaw analysis"; "I only want the simplest of explanations"; 4+ sightings, 4 matters).
First evidence that a promoted behavioural statement is not owner-shaped — the transfer question
PROMOTE-1 pre-stated for the second-pair corpus, part-answered early by a year-2000 lawyer.

## 3. The distiller-3 agenda (all parked/strained items, consolidated and ranked by cross-corpus support)

1. **Foreign EpisodeShape candidates — 2 corpora, 9 named candidates, the largest instance
   mass.** Kernel: the pilot's kind-tags already ran as a de facto dialect across all 61
   episodes — objection-revision 23, diagnosis 15, process-norm 12, machine-review-outcome 7,
   maintainer-override 3 (graph-counted). Email: scoped-delegation-request ≥4,
   counterparty-position-hold-with-invite ≥3, precedent-conformance-check ≥3,
   boundary-assertion ≥2. Design decision required first: shared-seed shapes vs per-genre
   dialect namespaces (the gradient in §1 argues for a two-layer system).
2. **Terminus vocabulary — the only gap all THREE corpora demand.** (a) terminus-visibility-as-
   corpus-property (home mid-flight arc + Enron GE refusal + syzbot kcov refusal = one refusal
   discipline, three corpora, no term); (b) terminus-REVERSAL (syzbot `defe2dfc`, n=1 event,
   currently unsayable); (c) terminus-surface (narrated vs silent — two surfaces of one
   signature, sample memo + pilot both).
3. **Machine-participant vocabulary — 1 corpus, but the dominant strain by volume, and
   OWNER-GATED.** Roles beyond reviewer/author: trailer-only analysis sources (Analyzed-by:),
   AI reporters seeking admission, anticipated-future-scrutiny, churn-pricing ("Given the
   amount of work we currently have with various AI reports..."). Plus the seven human-outcome
   kinds as a property candidate. Gerrit would supply the second corpus before minting.
4. **Evidence-by-artifact-delta (changelog-fossils) — syzbot ≥3 instances** (ext4 `0c89d865`,
   bluetooth `535ecc84`, off-list Sashiko URLs), with an email analog (REV-4 version bumps; the
   contract drafts themselves absent). kh:fromObservation needs a sanctioned
   attested-not-witnessed evidence form.
5. **Onset additions**: lifecycle-scale dormancy-broken-by-ping (syzbot, ≥3 sightings, parked
   with naming explicitly left to distiller+owner; distinct from session-scoped
   interruptionResume); in-corpus-arrival marking now used in 2 corpora (home maps arc, syzbot
   hfs arc — candidate annotation, not new kind); instrumentation-reveals-latent-anomaly
   (bridge arc, n=1); limit-predicted still n=1.
6. **Person-model second-regime learnings**: authority-basis now has two instantiated regimes
   (consent ladder at home; research-corpus basis at Enron) → candidate first-class term;
   kh:Person class now has n=2 modelled persons *across* capsules (khperson:james, kay-mann) —
   forces the cross-capsule person-reference parking; export scanner still blind to
   khpm:/khperson: namespaces (PROMOTE-1 friction 4 — the consent condition deserves a
   mechanical guard).
7. **Cross-capsule citesEpisode** — no longer hypothetical: §2's revival recommendation is
   blocked on it. Same decision governs cross-capsule claim evidence and person references.
8. **Micro-decision vs drafting-move** (email, several instances, 1 corpus).
9. **Heuristic staleness indexicality** (PROMOTE-1 parking c) — now live, since foreign evidence
   exists that could contradict promoted statements and heuristics carry no assessedAt.
10. **Seed/tool fixes with 2-corpus support** (product ledger): ArcShape note about the four
    rc:Pattern MinCount fields dual-typing pulls in (both pilots burned one staging each);
    apply_staged_revision `iri` vs stage's `revision_iri` (both pilots); bridge lacks the
    review_decision tool (Enron needed the core API); list_entities blind to imported kh:
    classes on the ontology graph; history-rows-outrank-live-nodes in search (4th sighting).

## 4. Corpus economics — and the artifact-interleaving thesis assessed

- **Home**: 55 typed episodes + 13 arcs + 10 heuristics from ~302 observations, but capture was
  self-recorded across ~9 sessions — the zero-marginal-capture case; not cost-comparable.
- **Email**: one pilot session; funnel 27,978 custodian rows → 3,871 harvestable (71% of
  authored mail was parallel-export duplicates!) → 108 formation-triage hits → 36 episodes +
  1 arc + 6 claims. ~0.9% row-to-episode; formation density 1-in-8..15 unfiltered. Near-zero
  marginal network (bulk parquet), heavy local triage.
- **Kernel**: one pilot session; 142 network ops → 68 screened → 47 graded (68% A+B) → 61
  episodes + 5 arcs. **0.43 episodes per network op; one A/B lifecycle fully harvested per
  ~4.4 ops.** Triage nearly free: the metadata-only Tier-1 filter is an 83% formation-bearing
  predictor (though only a 33–43% arc-grade-A predictor — the sample's 8/8 was small-N optimism).

**The thesis (obs 9fcf7c42: yield follows artifact-interleaving) is CONFIRMED with one
refinement.** The artifact-interleaved corpus delivered ~1.7× the episodes and 5× the arcs of
the conversation-only corpus at comparable session effort, with message-id-provenanced quotes —
because the vN-changelog convention does the objection→delta joining that email needed inference
for, and the version track makes termini checkable. Home, the densest of all, was itself
artifact-interleaved (transcripts + commits + capsule revisions). The refinement the pilots
earned: **interleaving also fossilizes.** Where the artifact track substitutes for the
conversation (changelog-fossils, off-list reviews), formation is attested without being
witnessed — which is exactly where the cheap-verification rule broke (the richest lifecycles
graded C on a capped fetch budget). So: artifact-interleaving predicts *yield*;
conversation-completeness predicts *verifiability*. Rank future corpora on both axes.

## 5. What phase 2 should be

**Recommendation: distill before harvesting again — then Gerrit as the harvest arm.**

1. **DISTILLER-3 FIRST.** The docket above is banked, ≥2-supported at its head, and every
   further harvest without a v3 vocabulary re-pays the same strains by hand (both pilots
   hand-wrote machine-participant prose and shape dialects into summaries). It is also the
   cheapest item on the board: no network, no new rights posture, evidence already verified.
   Owner decisions to schedule inside it: machine-participant terms (owner-gated), cross-capsule
   citesEpisode (blocks the §2 revival), the shape-dialect architecture, and — when wanted —
   the living-maintainers person-model posture (currently unset; nothing blocked by leaving it).
2. **GERRIT AT SCALE as the phase-2 harvest.** Highest expected information per unit effort of
   the named options: artifact-interleaved at patchset granularity (the confirmed yield
   predictor), machine-reviewer-rich (the second corpus the machine-participant vocabulary
   needs before minting), ready-made research corpora (CROP, Rev-rec, Review4Repair) to
   de-risk the join, and big enough to stress the refined filters and the shape-dialect design
   at N in the hundreds.
3. **POLYMATH as the SEALED benchmark — after the v3 freeze, not before.** Its value is
   precisely that it is small, pure, and one-shot: ingest chronologically against a *frozen*
   vocabulary and score what the machinery recovers (approach/objection/lemma arcs). Running it
   before distiller-3 spends its sealed character on a vocabulary about to change.
4. **The friend corpus, whenever it arrives** — slot it immediately regardless of the above:
   it is the only source that can discharge the heuristic-transfer question (which of the ten
   are owner-shaped), consent-first person-modelling as precedent (his 813ba95e-equivalent
   recorded BEFORE any claim), kh:Person at n≥2 within one capsule, and the cross-pair
   citation tier. Owner-gated by nature.
5. **Deepening Enron: last.** The marginal question it can still answer cheaply (do the four
   email shapes recur for a second custodian?) is worth a targeted mini-harvest only if
   distiller-3 wants that check before minting the email dialect. Full-scale deepening is the
   lowest yield-per-effort option on the board and the person-model result is already in hand.

## 6. Recorded in the home capsule

Four meta-observations recorded via the bridge (the home capsule is the program's memory; both
foreign capsules stay corpus-separate and untouched this session), citing the foreign journals
as evidence:
- `c280bc87` — the graded generalization verdict (spine general; shape gradient 76/34/14 with
  the genre-distance explanation; what each corpus demanded).
- `bdd45f7e` — the docket check (hotfix-narrow second witness found, revival recommended
  pending the cross-capsule citesEpisode decision; the other two stay; the
  delegation-contract-form resonance).
- `34146983` — the ranked distiller-3 agenda.
- `bf9bf9a5` — economics, the artifact-interleaving verdict, and the phase-2 recommendation.
Payloads kept at /home/codex/knowhow-study/payloads-synthesis/. After the writes: home at 312
observations / 312 evidence; validate_graph scope=all CONFORMS (0 results); staged debt zero
(recovery planner: 0 rows). Retrieval sanity: the distiller-3 meta retrieves first on its
natural query. Both foreign capsules also verified conforming with zero staged debt this
session (read-only).
