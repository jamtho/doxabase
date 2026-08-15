# VOCAB-NOTE-KH3 — the know-how vocabulary, tranche 3 (cross-corpus revision), for James

**Date**: 2026-08-13. **Distiller-3**, the v3 pass you greenlit ("I'm sure we'll make
mistakes but that's fine, we'll find the path"), working the cross-corpus synthesis's ranked
agenda across all three capsules — home read-write, Enron and syzbot strictly read-only.
**State**: ontology 473 → 724 quads, shapes 258 → 427, map 685 → 759, patterns 390 → 404;
observations 313 → 324. Graph conforms scope "all"; zero staged debt; two applied revisions
plus one deliberate negative probe, rejected by the new gate and closed discarded. Seed
re-exported (1151 quads). Every foreign count below was verified against the foreign
**graphs**, not the pilot journals — twice this pass the journals and graphs disagreed, and
the graph won both times (details in §5).

**Per your style law, worked examples first. Abstractions after.**

---

## 1. Worked example: a machine review, end to end (netfs, 2026)

**The raw material.** In the syzbot corpus, lifecycle "netfs: KASAN: slab-use-after-free
Read in netfs_unbuffered_write" (foreign observation `bf5c14d4`, graph-verified): the v2 fix
deleted a duplicate write-issue path, asserting the loop redid everything it did. A machine
reviewer — **Sashiko** — reviewed the v2 posting off-list; the author's v3 cover changelog
credits that review for a set of deltas, and the v3 commit message records what changed (the
deleted path still needed the IN_PROGRESS flag set and the MADE_PROGRESS/transferred
accounting corrected). **The machine review's own text is behind a URL; only the author's
adoption of it is on-list.**

Under the v2 vocabulary this episode was expressible only as prose. Under v3 it renders —
here as a demonstration; the instances properly live in the kernel capsule, which stays
untouched:

```turtle
khsyz-mp:sashiko a kh:MachineParticipant ;
    rdfs:label "Sashiko (AI patch reviewer)" ;
    kh:machineRole "Reviewer: present in 10 of 47 lifecycles (21%); reviews often
        delivered off-list behind URLs, entering the record as human restatement." .

khsyz:netfs-review-adopted a kh:Episode ;
    kh:decision "Adopt the machine review's findings into v3: set IN_PROGRESS on the
        surviving path, correct MADE_PROGRESS/transferred accounting." ;
    kh:machineActor khsyz-mp:sashiko ;
    kh:machineOutcome "Adopted with credit: the v3 cover changelog attributes the
        deltas to the review by name." ;
    kh:attestedNotWitnessed "The review itself is off-list behind a URL; the record
        holds only the author's adoption. Formation attested by the v2->v3 changelog
        delta; the objection half is missing." .
```

Three v3 terms are doing real work here: the actor is typed (never a person — that
distinction is now law on the class), the human outcome is recorded as prose, and
`attestedNotWitnessed` keeps the evidentiary status honest — this episode's formation is
*attested by the artifact delta*, not witnessed in conversation. The same corpus supplies
the relay pattern the vouch property quotes: *"This sashiko report looks legit"* — a
reviewer forwarding a machine concern with a calibrated hedge (`kh:relayVouch`), which
turned out to be how machine review usually enters the kernel record: through a human,
with a vouch attached (six graph-verified instances).

What I deliberately did **not** mint: an outcome-kind enum. The seven observed kinds
(adopted-with-credit, adopted-with-recorded-skepticism, relayed-with-soft-vouch,
resolved-by-citation, dismissed, ignored, void) are all real, but my per-kind independent-
event tally puts five of seven below 2 independent events. The kinds are documented on the
property; the enum waits for Gerrit. Same refusal for a role enum: one corpus's bot culture
must not be frozen as machine-participation structure.

## 2. Worked example: the terminus, said three ways — and the one way refused

**Narrated.** The bridge-xstats arc completes as: Reviewed-by, Ack, and the patchwork-bot's
templated applied notice within a day. Its `becameAutomatic` states the finding itself:
*"the narrated-merge terminus surface of patchwork subsystems, with the same underlying
decisions-stop signature as the silent ones."* Now sayable: the arc takes
`kh:terminusSurface kh:narratedTerminus` (4 verified kernel instances).

**Silent.** The hfs arc completes as probes dissolving into *"OK. I think I can agree with
you."* and a later duplicate fix answered with a one-line pointer. Your 13 home arcs all
complete this way — cold agents applying caveats untaught, no narration event anywhere —
and all 13 now carry `kh:terminusSurface kh:silentTerminus` (15 verified instances across
all three corpora). Two surfaces, one invariant: the surface belongs to the corpus's
*tooling*; the completion criterion beneath is unchanged — your dog-walk criterion survived
a third genre intact.

**Refused: the reversal term.** The strongest single moment in the kernel harvest is the
asus lifecycle (`defe2dfc`): the maintainer applies v1 — *"Applied to hid.git#for-6.20/asus,
thanks."* — a cross-subsystem concurrency objection lands hours later, and the reply is
*"Now dropped from the queue."* An applied decision **resumed being a decision**. Your
completion criterion has an inverse event, and the vocabulary cannot name it — and after
verifying every candidate in all three graphs, it still cannot, because **exactly one such
event exists anywhere** (the steam withdrawal is pre-apply; the workbench repo reversal
reversed a decision that had never stopped being one). So the term is REFUSED at n=1 and
the event goes to the graveyard as a first-class citizen instead:

```turtle
kho:terminus-reversal-term a kh:DeclinedOption ;
    kh:declineReason "Exactly ONE event exists across all three corpora... one event
        is one event; the >=2 rule that gates every shape gates this one." ;
    kh:revivalCondition "A second independent apply-then-reopen event in any
        registered corpus revives the candidacy — Gerrit's submit/revert stream is
        the expected source." .
```

The refusal discipline transferred better than any term in phase 1; here it is applied to
the vocabulary itself. Meanwhile the event *is* recorded (the episode carries the kernel
dialect shape `kh:maintainerOverride`), and `kh:terminusBasis` prose can describe a
reversal wherever one occurs.

## 3. Worked example: the revival — a heuristic promoted on foreign witnesses, gate intact

PROMOTE-1 refused to promote **hotfix-narrow-migrate-deliberately**: its two citations were
one event in two records. The revival condition — "a second independent upstream break
handled hotfix-narrow" — was met by the kernel corpus, twice, by strangers:

- `56e3c883` (media/dri): the patch "deliberately fixes the immediate crash with minimal
  change" after the broad fix produced deadlocks; the reviewer "accepted the scoping,
  deferring the architectural rework."
- `daa88ce3` (net/zcrx): the developer weighs the nicer designs, then settles "on shipping
  a 7.2 fix now and deferring anything nicer."

The blocker was mechanical and PROMOTE-1 pre-stated it: the SHACL gate requires
`citesEpisode` → typed `kh:Episode` nodes, and the witnesses live in a different capsule.
The gate was **not weakened**. Instead, v3 built the citation mechanism the synthesis asked
for:

1. **Registry**: `khcap:syzbot-knowhow` (a `kh:Capsule` node) anchors an observation
   recording the foreign capsule's identity, path, and graph state as I verified it
   read-only today.
2. **Evidence**: two home observations quote each witness's foreign record **verbatim**
   (re-verified against the syzbot graph character-for-character) with its foreign IRI.
3. **Re-expression**: two home episodes (`khe:syzbot-dri-defer-architecture`,
   `khe:syzbot-zcrx-ship-now`) typed `kh:Episode`, anchored by `kh:fromObservation` to
   those evidence observations, and marked `kh:reexpressedFrom` (the foreign episode IRI) +
   `kh:sourceCapsule` (the registry node). A new SHACL shape enforces the pairing — staged
   without `sourceCapsule`, a probe re-expression drew exactly one violation and apply
   refused (§6).
4. **Promotion**: `khh:hotfix-narrow-migrate-deliberately` now cites three typed episodes —
   your original plus both kernel witnesses — with an applicability condition the kernel
   also supplied (*scope the narrow fix to the subsystem's ownership conventions, not the
   widest scope that works*, `e42356e4`) and a new failure mode (*don't hotfix-narrow when
   the deliberate migration is already in flight — withdraw*, `a5110d5e`).
5. **Graveyard honesty**: the PROMOTE-1 decline entry is retained untouched, with a
   `REVIVED 2026-08-13` note added — it was correct on the evidence it had. The audit chain
   runs heuristic → home episode → home evidence observation → registry → foreign graph,
   every link checkable.

The other two refusals stand: no witness anywhere for tests-encode-semantics or
separation-conceptual-not-nominal. (Corroborating color, no graph standing: the new Gerrit
scout reports a 2012 pre-Zuul hotfix-narrow sighting — the rule may be older than any of
our corpora.)

Same-event discipline, stated on the term: a re-expression and its foreign original are ONE
event for every counting rule.

---

## 4. What changed, at one altitude up

1. **Shapes are corpus-idiomatic; the spine is general — now mechanical.** Every
   EpisodeShape and OnsetShape carries `kh:observedInCorpus` → registered capsule nodes.
   Three shapes are three-corpus genre-neutral (expertCorrectionAdopted,
   deferralWithTrigger, selfCorrectionConfessed); five are home-only operator-workflow
   forms; the nine new ones are marked dialect. Per-genre namespaces were refused — the
   gradient is a property of the evidence, not of names.
2. **Ten dialect shapes minted** (each ≥2 in-corpus, graph-verified): kernel —
   objectionRevision (23), diagnosisExchange (15), processNormEnacted (12),
   machineReviewOutcome (7), maintainerOverride (3), dormancyBrokenByPing (3 — filed by the
   synthesis as an onset addition, but all three graph instances are lifecycle-interior, so
   it is an episode shape: graph over journals, applied to the agenda itself); email —
   scopedDelegationRequest (≥4), precedentConformanceCheck (≥3), boundaryAssertion (≥2),
   counterpartyPositionHold (2 clean where the pilot said ≥3 — recorded honestly on the
   term).
3. **The terminus gap closed to exactly its evidence**: terminusBasis (prose,
   enum-by-cases in the comment: in-corpus continuation 18, participant-stated 1,
   outside-corpus = the refusal ground ×3), TerminusSurface (narrated/silent, both ≥2),
   reversal refused at n=1 (§2).
4. **Machine participants** (your unlock): six terms, all single-corpus-marked, with the
   human-machine boundary as law — machines are never kh:Person, never aboutPerson targets;
   their *operators* remain person-territory.
5. **Three authority regimes as first-class individuals**, each quoting its authority:
   consent (813ba95e), research-corpus (Enron's fdb34f6f), and public-record — your exact
   reasoning quoted on the term: *"we're purely storing and presenting things they
   intentionally made public, and we're not ourselves even publishing the results, except
   via major abstractions."* kh:Person minted at n=2 modelled persons across capsules
   (james typed here under consentRegime; kay-mann referenced, her capsule untouched).
6. **Seven policies became L0 citizens** (`khpol:`, typed kh:PolicyStatement): the four
   redaction families, person-model consent, private-first routing, absence-by-request,
   silent removals, shareability flow, and the living-persons posture — prose plus
   authority citations only; the L1-L3 policy vocabulary is deliberately NOT designed ahead
   of its distiller (doc 16 §6.2 executed, §6.3's regime-coexistence now real).
7. **kh:Heuristic and its gate: untouched** — exercised through the front door by the
   revival, never edited.

## 5. Where the record and the graphs disagreed (kept honest)

1. The synthesis filed dormancy-broken-by-ping under *onset* additions; the graph shows all
   three instances mid-lifecycle. Minted as EpisodeShape with the placement decision on the
   term.
2. The Enron pilot counted counterparty-position-hold-with-invite at ≥3; my clean re-count
   against the graph is 2 (+1 adjacent). Still clears the bar; the discrepancy is on the
   term.
3. (And one of my own: the session meta stated the ontology at 725 quads; the graph says
   724. Correction observation recorded within the hour — the selfCorrectionConfessed shape
   practiced on its own distiller.)

## 6. The gate proven, again

A deliberate probe staged a re-expression without `sourceCapsule`: staging validation
flagged exactly 1 violation (the new ReexpressionShape's minCount), apply refused
(`can_apply: false, validation_failed`), the graph was never touched, and the row was
closed discarded with rationale kept — the v1/v2 negative-probe precedent extended to v3's
new surface. No inspection-re-run slip this session: every staging output was read from its
saved file.

## 7. Couldn't-say v5 (deltas; full ledger in the session meta observation)

**Resolved**: kh:Person parking (n=2 via registry); cross-capsule citation/person reference
(mechanism built); the hotfix graveyard entry (revived).
**Refused with reasons on the terms**: machine outcome-kind enum; machine role enum;
terminus-reversal term; per-genre shape namespaces.
**Sharpened**: heuristic staleness — a heuristic has now been *revived* by foreign
evidence; the symmetric case (foreign evidence contradicting a promoted statement) has no
mechanism; assessedAt-style indexicality on kh:Heuristic is the expected shape, Gerrit the
expected trigger.
**New parkings**: machine-operator person-edges (person-territory under the new regime, no
analysis need yet); re-expression for claims/person references (sourceCapsule is
deliberately domain-less to receive it); policy L1-L3 vocabulary (the policy distiller's,
from these instances); narrated-terminus as a harvest-cost predictor (1 corpus).

**Addendum 2026-08-15 (distiller-4, terminus-surface generalization)**: the "narrated-terminus
as a harvest-cost predictor (1 corpus)" parking above understated what was coming — the
Polymath sealed benchmark's judge found the narrated-vs-silent distinction REAL in an
all-human corpus but inexpressible, because §2's narratedTerminus was scoped to bot notices.
DISTILL-4 generalized all three terminus-surface terms corpus-neutral by supersede-retain
(narration by ANY participant or mechanism — bot notice, merge message, operator close,
human announcement post, ritual thread-close — vs silence-with-external-confirmation),
registered khcap:polymath-knowhow, and re-expressed three witnesses: the proof-strategy arc
whose terminus member is the 'Problem solved (probably)' announcement (now typed
narratedTerminus at home — the exact case v3 couldn't say), the thread-16 numbering-cap
ritual close, and the write-up-thread fade. Counts refreshed live: narrated 7 events /
silent 26 instances across five corpora. The gerrit graph had already typed a HUMAN
operator-narrated close under v3 — the scoping was comment prose, never graph law.
kh:reexpressedFrom lost its rdfs:domain (gate-taught: the arc was the first non-episode
carrier, exactly the widening v5 parked). The sealed prediction itself stays FAILED —
history is history; what changed is expressibility going forward. Couldn't-say v7 in
session-meta observation 0d8a0bb5; details in DISTILL-4.md.

**Addendum 2026-08-13 (revival 2)**: the terminus-reversal refusal above is DISCHARGED —
the Gerrit corpus met the graveyard entry's revival condition three times over
(glance-location cycle #891036->#950336->#950623, ironic #985362, neutron #963390);
kh:terminusReversal now exists as an EpisodeShape (observedInCorpus syzbot + gerrit), all
four witnesses re-expressed as typed home episodes (the two observation-grade originals
honestly marked under a widened reexpressedFrom contract), the graveyard entry annotated
REVIVED with its decline reason retained. Couldn't-say v6 is in session-meta observation
15591b0a; details in DISTILL-3.md §Revival 2.

## 8. Verification state

validate_graph scope "all": conforms, 0 results (checked after each apply and at close).
Zero staged debt (recovery planner: 0 rows; one probe row closed discarded). 324
observations / 324 evidence. export_preflight: the block gate shows the SAME 4 pre-existing
tranche-3 residue resources — nothing from this session fired, including the policy and
person nodes. Retrieval sanity: the new terms, dialect shapes, policies, and the revived
heuristic all retrieve on natural queries; two capsule-registry queries surfaced history
rows above live nodes — the history-outranking friction's fourth and fifth sightings,
logged in DISTILL-3 for the product ledger. Seed re-exported from the live graphs (1151
quads, re-parse-checked; previous seed kept as backup); foreign capsules verified untouched
and conforming at close.
