# Polymath Sealed Arc-Recovery Benchmark — JUDGE REPORT

Judge session, 2026-08-13. Governing document:
/workspaces/doxybase/docs/journal/trials/2026-08-polymath-benchmark-protocol.md.
Working files: this directory (phase-A.md frozen before seal access; phase-B.md;
arcs-dump.json; verify.py outputs; fetch-ledger.txt).

Integrity preliminaries:
- Frozen output hashes verified against FREEZE-HASHES.txt (capsule 53ee499b…,
  INGEST-1.md 8bc246e8…). Capsule inspected via a scratch-dir copy only.
- Seal SHA-256 verified BEFORE opening: 240eda8915… = protocol §7 exactly.
  First hex digit 2 (EVEN) → graded in registry order, as done below.
- I am the first and only reader of the seal. Phase A was written and frozen
  before any seal access. NO seal addendum file exists (reported per seal
  footer): /home/codex/polymath-seal/ contains only README.md, the seal, and
  sources/.

## VERDICT: **PASS** (not STRONG PASS, not FAIL)

§8 criteria, one by one (PASS requires ALL):
1. ≥4 of 6 HIGH arcs ≥ PARTIAL — **met, 6/6** (P1 R, P2 P, P3 P, P5 P, P7 P, P8 R).
2. ≥2 of 6 HIGH arcs RECOVERED — **met exactly, 2** (P1, P8).
3. ZERO hallucinated-established-claims — **met** (all 9 kh:becameAutomatic
   claims and every settled/computed-value assertion anchor-audited; none
   refuted; details below).
4. ≥3 of 5 negatives correct — **met, 5/5**.
5. Headline score ≥ 3.0 — **met, 4.5** = 2 RECOVERED + 0.5×5 PARTIAL − 0
   hallucinated, over the 8 seal arcs.

STRONG PASS checked: ≥5/6 HIGH ≥PARTIAL ✓ (6/6); ≥3 RECOVERED ✗ (**2** — this
is the failing gate); SP-1 ≥ PARTIAL ✓; ≥4/5 negatives ✓ (5/5); zero
hallucinated arcs of any kind ✓. → Not a STRONG PASS.

NULL/VOID check: no D1 deviation found anywhere (allowlist-only fetching
attested by journal + ledger and consistent with all coverage statements I
spot-verified; seal unread before Phase A; hashes clean; rules untouched).

## Grading discipline applied (fixed in phase-B.md before grading)

Seal arcs were graded against the Phase A frozen normalization (the ingester's
9 arcs with members/anchors/quotes, its episodes as cited there, 3
DeclinedOptions, refusal list, establishment inventory), with each seal
entry's own recovery note as the binding tolerance. Post-seal capsule text
searches (run with seal-derived terms) were quarantined: used for Phase D,
negative checks, and gap commentary only — never to upgrade an arc grade.
This is disclosed as a judge-side procedural note in the deviation ledger.

## Per-seal-arc grades (registry order), one-line evidence each

- **ARC-P1 (HIGH): RECOVERED.** Ingester arc `proof-strategy-collapse-to-
  breakthrough` opens on the Feb 1 post-body triangle-removal frame with its
  same-breath anomaly ("Wow… Unfortunately it doesn't" — verified in the t4
  body), carries the weakening (thread-6 body member; objections harvested),
  and records the silent set-aside via the Feb 13 survey member ("we have not
  been concentrating on it recently" — verified) with the corners analogy
  retained into the A-Sz redirect; abandoned-but-retained, never established
  (seal note satisfied; N1 not tripped).
- **ARC-P2 (HIGH): PARTIAL.** The merge-into-the-proof end is in the
  normalized registry (A7 crisis members = 12-set/complexity-1 machinery,
  anchors #comment-2595/2596/2597/2600/2601 all verified; DeclinedOption D-1
  retains the 12-set argument with Gowers's verbatim revival condition); the
  Feb 8 catalog→claim collapse is not in the normalized synthesis (rich in
  harvest only — Conjecture 411, richness-profile synthesis — noted as
  under-synthesis, not credited). Seal note grants PARTIAL for one end.
- **ARC-P3 (HIGH): PARTIAL** (also capped by its own note). Onset (equal-
  slices as working device, Feb 9–11, anchors verified) and terminus
  (O'Donnell's conversion, "the expression in #567 is so elegant, how can I
  not be on board for equal-slices now?" — verbatim at #comment-2308) match;
  the Feb 14–15 two-way bridge lemmas are not the arc's pivot (it uses the
  Feb 11 ergodic synthesis); and the arc's thesis ("interchangeable technical
  convenience") is the note's files-as-technicality case → at most PARTIAL.
- **ARC-P4 (MEDIUM): MISSED.** No toy-ladder arc; not merged into the
  P5-matching arc as base-case development (the note's PARTIAL branch);
  only the DHJ(2.6) review episode touches the ladder at synthesis level.
  The harvest holds much ladder material un-synthesized — reported as a
  machinery finding (exploratory-structure synthesis gap), not credit.
- **ARC-P5 (HIGH): PARTIAL.** Interior crisis (Mar 6 "Probable collapse" →
  Mar 8 double-partition; anchors verified), pivot (Mar 9 sketch/"in the
  bag" at #comment-2633 — the seal's own Gowers.2633; verified), and terminus
  (Mar 10 hedged announcement; verified verbatim) all match; the Feb 18–21
  analogy-transplant onset is absent from the normalized registry (the
  Feb 21 triple exists in harvest at ids 2327/2329/2331 — exactly the ids
  the seal cites — but no recovered arc carries it as onset). Note requires
  all three incl. transplant onset for full credit → PARTIAL.
- **ARC-P6 (MEDIUM): PARTIAL.** Branch onset (Feb 5 Tao bounds post, in
  registry as an A2 member, anchor verified) and the branch's computational
  verification protocol + HOC-open status are normalized (establishment
  inventory; HOC overflow episode); the HOC-as-interior and the two-papers
  terminus live in harvest, not synthesis; A9 is a genuine numbers-branch
  arc but covers only the generalization tail. ≥2 composite elements →
  PARTIAL; no establishment error (values carried WITH the group's
  two-independent-methods gate; HOC never asserted resolved).
- **ARC-P7 (HIGH): PARTIAL.** Onset (Feb 11–12 reading-seminar split —
  episode + A3 member, anchors #comment-2140/2141/2145 verified) and pivot
  (Austin's independent proof, attested in the normalized announcement-post
  member and anchored) match; the Mar 12/14 translation merge-back is
  harvest-only and no ergodic arc was drawn. ≥2 → PARTIAL; NEG-N2 held.
- **ARC-P8 (HIGH): RECOVERED.** Via arcs `establishment-verification-
  standard` + `credit-becomes-named-policy` (+ the explicit A7/A8 braid on
  the announcement): onset ✓ (Mar 9 sketch member + Mar 10 announcement,
  "I hereby state that I am basically sure… (though not in the way
  originally envisaged)" verified verbatim in the post body with the
  robustness reasons and "within a week or so" DHJ(k) expectation); pivot ✓
  (Kalai's challenge #comment-2760 → Gowers's verification standard
  #comment-2762, tree-structure quote verified verbatim, hedge retained);
  terminus ✓ (fast DHJ(k) generalization + pseudonymous write-up: "I would
  of course propose 'D.H.J. Polymath'" verified at #comment-3227, policy at
  #comment-3328 verified). The hedge is preserved throughout → the note's
  flattened-epistemics cap does not bite.

## Negatives (5/5 correct)

- **N1 (HIGH) correct**: triangle-removal recorded abandoned/deprioritized;
  the proof recorded as modified-Ajtai–Szemerédi density increment.
- **N2 (HIGH) correct**: Austin's proof recorded as independent, parallel,
  individually-credited corroboration ("Tim Austin has independently
  produced…" in the announcement-body record) — never as the project's proof.
- **N3 (HIGH) correct**: Fourier work recorded as empirically-checked-not-
  proved, then bogging down and self-diagnosed as a dead end for DHJ(3);
  DHJ(2)-only successes recorded as DHJ(2)-only. Never the proof route.
- **N4 (MEDIUM) correct**: HOC recorded as a conjecture; weighted-HOC
  "unique solution" claims invalidated via the overflow-bug episode;
  higher-dimensional failure flagged; k=3 confidence downgraded; never
  resolved, never load-bearing.
- **N5 (MEDIUM) correct**: the Moser(6)⇒DHJ(3) cross-link (jozsef =
  Solymosi) was read and deliberately NOT recorded — "absent," which the
  seal defines as correct.

## Probes

- **SP-1 (peripheral-becomes-central): PARTIAL.** The status elevation is
  captured (doubt → "how can I not be on board", the measure becomes where
  the work happens) but the arc frames the story as a strategic fork
  dissolving into technicality rather than a device promoted to ambient
  substrate. Meets the STRONG-PASS bar (≥ PARTIAL), which is moot anyway.
- **SP-2 (abandoned-approaches-retained): PASS.** Retained with reasons:
  obstructions catalog (1) ✓; triangle-removal with abandonment reason (2)
  ✓; Austin translations (5) ✓; HOC open (6) ✓; bounds tables as the
  numbers branch's product (7) ✓ — five clean checkables (≥3 required);
  (3)/(4) are additionally present in harvest (ids 2622/2624; 2329/2331).
- **SP-3 (chronology traps): PASS.** The 1050-1099/1100-1199 inversion
  preserved AND explained (branch pacing); Austin's in-thread adjacency
  never conflated; inline-number collisions/decimals/soft boundaries never
  smoothed (WordPress ids used as anchors throughout; the "copy of 340"
  timestamp irregularity kept as observed).

## Sealed terminus-surface prediction: NOT borne out

All nine ingester arcs carry kh:silentTerminus — a uniform surface, which
the seal itself pre-declared to be evidence against the v3 terminus-surface
machinery's discriminating power. Honest mitigation (product finding, not a
grade rescue): the seeded vocabulary documents kh:narratedTerminus as
syzbot-bot-specific, so a dialect-conforming ingester could not legally mark
the announcement narrated; the ingester routed the narration signal into
prose fields instead (terminusBasis "PARTICIPANT-STATED" on the
establishment arc; the Session 8 ritual-close-vs-fade asymmetry note). This
is a clean couldn't-say for the distiller ledger: the narrated/silent split
the seal predicted is real in the record but inexpressible in the frozen v3
surface vocabulary as scoped.

## Plausible-novel findings (seal gaps; anchors verified)

The seal's registry contains no governance/process arcs. Four verified-
anchor ingester arcs match no seal entry and are genuine, record-supported
trajectories — reported as seal gaps, not penalties:
1. `numbering-becomes-routine` (collision saga at ids 1713–1721 incl.
   Gasarch's 45.5 → comment 300's block scheme, verbatim → routine closes).
2. `thread-splitting-learns-from-failure` (Dyer's early proposals → Tao's
   verbatim die-out diagnosis at #comment-2234 → same-day meta-thread
   founding, 7:10pm/7:45pm Mar 10, verified).
3. `rule-six-becomes-standing-policy` (launch rules → "because I formulated
   rule 6 I have felt obliged to stick to it" verified → policy stated
   without permission at comment 816, verified).
4. `self-correction-becomes-routine` (the register-flattening arc:
   "completely false" → "back to the drawing board" → "a bit of a scare" →
   "math with a net" (verbatim at #comment-2926) → one-sentence concession
   at #comment-37561, verified) — a longitudinal pattern no retrospective
   names; in my judgment the run's most interesting novel arc.
Plus the launch-thread credit-question span of `credit-becomes-named-policy`
(the part beyond P8's terminus). None contradicts any HIGH negative.
HALLUCINATED arcs: **zero**. Hallucinated-established-claims: **zero**.

## Deviation ledger

- **D2** (recorded; verdict stands): session chunking as pre-committed in
  the run ledger differs from protocol §6's sketch ("2–3 threads each" —
  s2 ran the 221-comment thread alone). Decided and recorded before first
  launch; no content effect.
- **D3**: s7's source-14 URL returned HTTP 301 to a longer canonical slug;
  followed transparently, same content and comment ids (run ledger).
- **D3**: ingester used direct HTTP GET + local parsing rather than the
  summarizing fetch tool — cosmetic tool choice that improved anchor
  fidelity; all fetches within the allowlist.
- **Not a deviation** (noted): comments dated after 2009-03-30 (to 25 Jun
  2009) were read on allowlisted threads 17/18 — the protocol requires
  fetching all pages/comments of a listed URL; the window closes with the
  DHJ(k) thread inclusive of its comment tail.
- **D3** (quote-discipline blemish, ingester): one becameAutomatic field
  (establishment arc) renders a post-body paraphrase inside quote marks
  ("preparatory sketches of DHJ(3) and DHJ(k) exist on the wiki" vs the
  actual "…it is more like preparatory sketches… found on the wiki").
  Substance fully supported by the page; no claim refuted; kh:pivotQuote
  fields (the ingester's own verbatim-gated class) all verified verbatim.
- **D3** (seal-side, noted): the seal's "Gowers.2327/2329/2331" uses
  WordPress ids where the wiki timeline uses inline numbers (580/581/582);
  both resolve to the same comments (verified). Seal ledger item D-6 labels
  thread 4 "the launch post" (221 responses; the actual launch post has
  247) — cosmetic wording, no grading effect. One S6 [EG] entry differs
  trivially ("to get" vs "for" in a timeline title); substance identical;
  no D2 drop required.
- **D3** (judge-side procedural disclosures): (a) post-seal capsule
  searches with seal-derived terms were run and quarantined per the
  discipline in phase-B.md; (b) the S8 [EG] quote was not re-verified
  because it was not load-bearing for any grade (N4 graded on ingester
  behavior/absence); (c) judge fetches totaled 21 of ≤40, ledger kept
  (fetch-ledger.txt).
- **No D1** anywhere.

## Anchor-audit statistics

- Comment-level anchor checks: **81 run, 81 passed, 0 failed.** (Four
  initial near-misses all resolved within the ingester's own anchor sets:
  die-out quote verbatim at #comment-2234; "with a net" at #comment-2926;
  Gasarch 45.5 at #comment-1713; Ajtai–Szemerédi pivot verbatim at
  #comment-2600 modulo diacritics.)
- Post-body anchor checks: 11 run; 10 verbatim-pass; 1 substance-pass with
  the paraphrase blemish logged above.
- Verbatim pivot quotes verified on live pages: 9/9 arcs' load-bearing
  quotes (block-numbering scheme; die-out; rule-6 bind; "math with a net";
  ergodic-synthesis credit; #567 reversal; "back to Ajtai-Szemerédi";
  tree-structure standard; DHJ(k) retitle; "D.H.J. Polymath" proposal;
  "so much for the naive conjecture").
- [EG] seal-quote re-verification: 4/4 S1 quotes verbatim; 24/24 S6
  timeline entries verified (1 trivial title variance); announcement-post
  [EG] quotes verified verbatim on the live page. Zero drops, zero D2
  re-grades.
- Establishment-semantics sweep: 9/9 becameAutomatic claims supported by
  the record (including negative checks: no attribution renegotiation
  after the May 8 policy anywhere in thread 17; no re-litigation of
  solvedness after Mar 16). Zero refutations.
- Judge fetch budget: 21 of ≤40 used (9 Gowers threads, 8 Tao thread-pages,
  thread 11, thread-10 p2, S1, S6).

## Honest confidence notes

- The two RECOVERED grades (P1, P8) are firm: their elements sit in the
  normalized arc registry with verbatim-verified anchors, and each seal
  entry's own note is satisfied on its stated terms.
- P2 and P5 are the grades most sensitive to interpretation. Under a
  laxer element-recovery reading (crediting harvest-level material the
  ingester recorded but never synthesized into arcs), both would rise to
  RECOVERED and the verdict would become STRONG PASS (headline ~5.5–6.5).
  I rejected that reading because Phase A's freeze exists precisely to
  stop the judge from rummaging the 394-observation harvest with
  seal-derived search terms after unsealing — which is how I found that
  material. The conservative reading is the one the blinding design
  supports; the sensitivity is reported so James can overrule with eyes
  open. Under no defensible reading is the verdict below PASS.
- P4 MISSED and P6 PARTIAL are honest reflections of a real pattern: the
  ingester's synthesis drew 6 governance/process arcs and 3 mathematical
  ones; the seal drew 8 mathematical/structural ones and 0 governance
  ones. Each lens misses the other's arcs. That symmetry — vocabulary
  pulls synthesis toward process formation; retrospectives pull the seal
  toward mathematical structure — is, in my judgment, the run's most
  useful product finding alongside the terminus-surface couldn't-say.
- The P5-onset miss replicates ARCS-1's core finding at a finer grain:
  the transplant onset was IN the harvest (at the exact ids the seal
  cites) and still did not surface as an arc onset. Onsets stay the
  structurally hard part even when the substrate contains them.
- The negatives being 5/5 despite pretraining contamination pressure, with
  zero hallucinated establishment claims across 394 observations and 9
  arcs, is the strongest single result in the run — it is also the least
  contaminatable one, since it is graded on anchored in-record behavior.

## Claim boundary (§9 counterweights, in my own words)

This PASS does not show that the machinery can recover understanding-arcs
from a corpus the model has never seen. Polymath1 is saturated in
pretraining; the ingester model almost certainly already knew this story,
its dead ends, and its warnings. What this trial's design actually
measured, and what the PASS certifies, is narrower: that the machinery can
carry a famous story with evidence attached — comment-level anchors that
survive an adversarial audit (81/81), establishment semantics that never
outrun the record (0 refuted claims), honest refusal where the record is
silent, expression within a frozen vocabulary including its couldn't-says,
and continuity across nine sessions where the capsule, not the context,
held the memory. It is one corpus, one genre, n=1 — a single-venue,
all-human, seven-week, publicly-narrated mathematical collaboration — and
says nothing about kernel-style multi-venue records, email genres, machine
participants, authority regimes, or decade-long arcs. The seal itself is
winner's history built from retrospectives, and this run demonstrated that
bias concretely (four verified governance arcs the seal never anticipated;
a toy-ladder arc the synthesis never drew). And the sealed character is
spent: win or no, this seal cannot be reused, and a re-run would prove
nothing. The claims stop there.
