# POLYMATH BENCHMARK — SEALED EXPECTED-ARC REGISTRY

**Sealed 2026-08-13, BEFORE any ingester run.** This file is the answer key for
the Polymath arc-recovery benchmark (protocol:
`polymath-benchmark-protocol.md`, which records this file's SHA-256). No
session may read this file except the eventual JUDGE, at judging time, after
the ingester's output is frozen. The sealer is the only other mind that has
seen it.

Built from RETROSPECTIVE sources only (ledger below; the same ledger appears
in the public protocol). The sealer's contact with chronological-side material
was limited to: the launch post (rules summary), the 2009-03-10 announcement
post (terminus event), two thread-existence checks (Tao Feb 5, Tao Mar 4), and
five blog monthly-archive pages (metadata only). No arc-interior claim below
is sourced from chronological threads.

**Quote provenance marks**: [VV] = verbatim-verified by the sealer against a
locally extracted full text (the Annals/arXiv paper, Cranshaw–Kittur). [EG] =
extraction-grade: pulled via a fetch-summarizer pipeline; the judge MUST
re-verify [EG] quotes against the source before grading; a quote that fails
re-verification is dropped and the arc re-graded on remaining evidence
(deviation class D2, per protocol).

**Seal-side sources** (ingester-forbidden), cited below by ID:

- S1 Gowers, "Polymath1 and open collaborative mathematics", 2009-03-10,
  gowers.wordpress.com/2009/03/10/polymath1-and-open-collaborative-mathematics/
- S2 Gowers, "Can Polymath be scaled up?", 2009-03-24,
  gowers.wordpress.com/2009/03/24/can-polymath-be-scaled-up/
- S3 Nielsen, "The Polymath project: scope of participation", 2009-03-20,
  michaelnielsen.org/blog/the-polymath-project-scope-of-participation/
- S4 Nielsen, "Update on the polymath project", 2009-02-09,
  michaelnielsen.org/blog/update-on-the-polymath-project/
- S5 D.H.J. Polymath, "A new proof of the density Hales-Jewett theorem",
  arXiv:0910.3926 / Annals of Math 175 (2012) 1283–1327. Full text extracted
  locally by the sealer; all S5 quotes are [VV].
- S6 Polymath wiki, "Timeline" page (participant-curated),
  michaelnielsen.org/polymath/index.php?title=Timeline
- S7 Polymath wiki, "Polymath1" page (thread ledger),
  michaelnielsen.org/polymath/index.php?title=Polymath1
- S8 Polymath wiki, "Hyper-optimistic conjecture" page.
- S9 Cranshaw & Kittur, "The polymath project: lessons from a successful
  online collaboration in mathematics", CHI 2011. Extracted locally; [VV].
- S10 Martin, Mette et al. (Kleinberg group), "Internet Collaboration on
  Extremely Difficult Problems", WWW 2016. Extracted locally; [VV].
- S11 Varshney, "Toward a Comparative Cognitive History: Archimedes and
  D.H.J. Polymath", CI 2012. Extracted locally.
- S12 Gowers & Nielsen, "Massively collaborative mathematics", Nature
  461:879–881 (2009). PAYWALLED — cited for existence only; no quotes used.
- S13 Gowers, "Polymath and the density Hales-Jewett theorem", in An
  Irregular Mind (2010) 659–687. PAYWALLED — cited for existence only.

S6/S7/S8 are participant-curated distillations (created from Feb 12, 2009
onward). They are classified seal-side because they are hindsight-organized;
the ingester must never touch them.

---

## How to read an arc entry

onset = the anomaly/question that started it; pivot = the leap, as the
retrospectives describe it; terminus = what became settled or automatic;
relations = branch/merge edges (the one-leap-powers-many structure);
confidence = the sealer's pre-committed grade with the reason; recovery
notes = judge tolerances fixed now, not at judging time.

Comment references like "Gowers.365" are the project's own numbering, as
recorded by S6. The sealer did NOT verify these anchors in-thread (that would
require reading chronological material); the judge verifies anchors during
Phase C.

---

## ARC-P1 — The titular approach: triangle-removal rises, stalls, is set aside

- **Onset**: the launch frame itself (2009-02-01). The project's stated aim
  was not "prove DHJ(3)" but "test ONE approach": a triangle-removal argument
  modeled on the corners theorem, or convincing arguments that it cannot work.
- **Interior**: a dedicated thread (comments 300–399, Feb 6). The approach is
  progressively weakened by the absence of a usable regularity/removal
  mechanism for the DHJ structure — the objection is crystallized by the
  obstructions-to-uniformity program (ARC-P2's onset is objection-X here).
- **Terminus**: SILENT abandonment as proof route — no funeral comment is
  expected in the record; the approach simply stops being worked when the
  density-increment turn (ARC-P5) takes over around Feb 21. Retained as
  know-how: the corners-problem analogy survives the approach's death and is
  transplanted into ARC-P5.
- **Relations**: parent-of P2 (obstruction collection begins in its service);
  analogical-ancestor-of P5 (analogy retained, proof template swapped).
- **Evidence**:
  - [EG, S1] "I deliberately set a rather modest aim: to explore just one
    approach to DHJ(3). In retrospect, this seems not to have been the right
    decision"
  - [EG, S1] "in the end we moved off into other directions that were more
    fruitful"
  - [VV, S5] "Very briefly, our proof of DHJk follows the density increment
    method, as pioneered by Roth" (i.e., NOT triangle removal).
- **terminusSurface prediction**: silentTerminus.
- **Confidence**: HIGH (two independent retrospectives + the paper's own
  method statement).
- **Recovery notes**: full credit requires the ingester to record the
  approach as abandoned-but-retained (not established, not deleted). An
  ingester that never notices the approach died scores MISSED here and
  likely trips NEG-N1.

## ARC-P2 — Obstructions to uniformity: anomaly catalog → complexity-1 insight → the correlation theorem

- **Onset**: Feb 2–3; S6 entries: "Gowers.19: Collect obstructions to
  uniformity!" and "Gowers.70: Collection of obstructions to uniformity
  begins". A deliberate anomaly-collection program — the arc begins as a
  catalog, not a theorem.
- **Pivot**: Feb 8, S6: "Gowers.403: Complexity 1 sets are more fundamental
  obstructions". The catalog collapses into a structural claim: line-free
  sets correlate locally with intersections of insensitive ("12-set" /
  complexity-1) sets.
- **Terminus**: the correlation half of the final proof. S6: Mar 10 "Tao:
  1-sets, 2-sets locally independent"; Mar 11 "Gowers: Correlation component
  of DHJ(k) proof complete". Institutionalized as S5 §8.
- **Relations**: born inside P1's frame; merges into P5 (correlation half +
  increment half = the proof).
- **Evidence**:
  - [VV, S5] "either A contains a combinatorial line or else it has a
    'density increment' within a somewhat structured subset of [k]n
    (specifically, an 'intersection of ab-insensitive sets')"
  - [EG, S6] the three dated timeline entries quoted above.
  - [VV, S5] §8 heading: "A key lemma showing how to obtain a density
    increment on a somewhat structured subset."
- **Confidence**: HIGH.
- **Recovery notes**: partial credit if the ingester finds the
  catalog-to-claim collapse OR the merge into the proof; full credit needs
  both ends.

## ARC-P3 — Equal-slices: a passing device becomes the ambient measure  [probe SP-1]

- **Onset**: Feb 9; S6: "Gowers.365: Equal slices measure introduced" —
  introduced in passing, INSIDE the triangle-removal thread, as a technical
  convenience.
- **Pivot (lemma-Y)**: Feb 14–15, the two-way bridge; S6: "Gowers: Equal
  slices implies uniform" and "Tao: Uniform implies equal slices". After the
  bridge, the measure is load-bearing everywhere at once. (Honest wrinkle,
  recorded not smoothed: Kalai states the hyper-optimistic conjecture IN
  equal-slices on Feb 11 — i.e. the measure was already spreading before the
  bridge lemmas were proved.)
- **Terminus**: ambient/automatic status. The final paper conducts the whole
  argument in it and devotes two sections to it.
- **Relations**: one-leap-powers-many exemplar — powers P4 (probabilistic
  DHJ(2)), P5 (the increment iteration lives in equal-slices), P6 (the
  c-mu-n / hyper-optimistic side is stated in it).
- **Evidence**:
  - [VV, S5] "As we saw with Sperner's theorem, it is often more natural to
    think of the DHJ problem under the equal-(nondegenerate-)slices
    distribution."
  - [VV, S5] section headings: "Definitions of the equal-slices
    distributions" (§5); "technical calculations which will let us pass
    freely between probability distributions" (§6).
  - [EG, S6] the dated entries above (Feb 9, Feb 14, Feb 15).
- **Confidence**: HIGH.
- **Recovery notes**: THE peripheral-becomes-central probe. Full credit
  requires the ingester to notice the PROMOTION (device → substrate), not
  merely that the measure exists. An ingester that files equal-slices as a
  technicality scores at most PARTIAL.

## ARC-P4 — The toy ladder: DHJ(2.x) variants as technique selector

- **Onset**: Feb 13–15, the proof-strategies thread; S6: "Tao: DHJ(2.6)
  proposed" (Tao.2196).
- **Interior**: a burst of competing proofs of deliberately weakened
  statements — S6 entries: "McCutcheon.518: Ramsey proof of DHJ(2.6)" (comment
  2206), "'Cave-man' proof of DHJ(2.6)" (2242), "O'Donnell: Ramsey-free proof
  of DHJ(2.6)?" (2222), "Fourier-analytic proof of DHJ(2)" / "Fourier +
  density increment proof of DHJ(2)" (2370, 2372), "Increment-free Fourier
  proof of DHJ(2)" (2496), "McCutcheon: DHJ(2.7)" (2356).
- **Terminus**: the ladder is dismantled; what survives into the paper is
  probabilistic DHJ(2)/Sperner as the base case (S5 §3, §4.3). DHJ(2.6)/(2.7)
  appear nowhere in the final argument.
- **Relations**: powered by P3; feeds its surviving rung into P5.
- **Evidence**:
  - [VV, S5] "The strategy begins with what we already know: probabilistic
    DHJ2" (§4.3).
  - [VV, S5] §3 heading: "Proofs for DHJ2: Sperner's theorem, and the
    Gunderson–Rödl–Sidorenko theorem."
  - [EG, S6] the dated ladder entries above.
- **Confidence**: MEDIUM — the EVENTS are well-attested (S6), but the
  "selector" function is the sealer's synthesis; no retrospective narrates
  the ladder's purpose explicitly.
- **Recovery notes**: pre-committed tolerance — an ingester that merges this
  material into P5 as "base-case development" earns PARTIAL for P4 (not a
  miss). Full credit requires recognizing the variant-statements episode as
  its own exploratory structure.

## ARC-P5 — The Ajtai–Szemerédi transplant: analogy → density-increment skeleton → proof  [central arc]

- **Onset**: Feb 18–21; S6: "Gowers: Corners(1,3)?" (Feb 18), then the Feb 21
  triple — "Extreme localisation + density increment = DHJ(3)?",
  "Use Ajtai-Szemeredi argument for density increment?", "Multidimensional
  Sperner" (Gowers.2327/2329/2331). The corners ANALOGY survives P1's death;
  the proof TEMPLATE swaps from triangle-removal to Ajtai–Szemerédi.
- **Interior**: Feb 25–26, S6: "Density increment on complexity 1 set",
  "Complexity 1 + Ajtai-Szemeredi DHJ(3) sketch". Crisis: Mar 6, S6: "12-set
  density increment difficulty identified". Resolution: Mar 8, S6:
  "Iterative partitioning of 12-sets?" — plus a standalone yield the same
  day: "New proof of Ajtai-Szemeredi".
- **Pivot**: Mar 9, S6: "Gowers.2633: Sketch of DHJ(3)".
- **Terminus**: the 2009-03-10 announcement; then the paper's skeleton IS
  this arc (density increment within structured sets; partition of
  insensitive sets into subspaces; Shkredov-style double iteration).
- **Relations**: inherits the corners analogy from P1; consumes P2
  (correlation half), P3 (ambient measure), P4 (base case); parent of P8.
- **Evidence**:
  - [VV, S5] "Very briefly, our proof of DHJk follows the density increment
    method, as pioneered by Roth."
  - [VV, S5] "This double-iteration proof structure was previously used by
    Shkredov ... to obtain strong bounds for the so-called 'Corners
    Problem', a simplified version of DHJ3."
  - [EG, S6] the dated chain Feb 18 → Mar 9 above.
- **terminusSurface prediction**: narratedTerminus (the announcement post).
- **Confidence**: HIGH.
- **Recovery notes**: the arc the trial is really about. Full credit
  requires: the analogy-transplant onset (corners template swap), the Mar 6
  difficulty → Mar 8 partitioning resolution (interior crisis), and the
  Mar 9–10 completion. Missing the crisis but getting both ends = PARTIAL.

## ARC-P6 — The numbers branch: c_n bounds, Moser numbers, hyper-optimistic conjecture

- **Onset**: Feb 5, Tao's thread (comments 200–299): bounds for c_n
  (largest line-free sets), the Moser cube problem — an explicitly
  computational/experimental branch from day 5.
- **Interior**: Feb 11, S6: "Kalai.455: Hyper-optimistic conjecture" (the
  extremal equal-slices sets are unions of slices; "if true, will imply the
  DHJ theorem" per S8). Feb 20, S6: "Solymosi.563: Moser(6) implies DHJ(3)"
  — an attempted cross-link back to the main line. Computational methods
  (integer programming, genetic algorithms per S6's curators).
- **Terminus**: institutionalized as the project's SECOND paper ("Density
  Hales-Jewett and Moser numbers", arXiv:1002.0374; threads run to Jan
  2010). The hyper-optimistic conjecture ends the window VERIFIED for n ≤ 6
  and OPEN — S8: "the hyper-optimistic conjecture is true for n ≤ 6".
- **Relations**: branches at launch; NEVER merges into the DHJ(3) proof;
  merges only at program level (sibling paper). Powered by P3 (the
  conjecture is stated in equal-slices).
- **Evidence**:
  - [EG, S8] "Gil Kalai and Tim Gowers have proposed a 'hyper-optimistic'
    conjecture." / "the hyper-optimistic conjecture is true for n ≤ 6".
  - [EG, S6] the Feb 5 / Feb 11 / Feb 20 entries above.
  - [VV, S10] "Polymath 1 (p1): 2 papers, 1509 comments, 112 active days"
    (the two-paper terminus, from the WWW16 dataset table).
- **Confidence**: MEDIUM overall (branch existence and two-paper terminus
  HIGH; interior detail rests mostly on curated S6 and one S8 page).
- **Recovery notes**: in the CORE ingestion variant (protocol §6) only two
  Tao threads are in the diet; grading then reduces to branch-existence +
  branch-relation only, pre-committed here.

## ARC-P7 — Ergodic know-how: reading seminar → finitization attempts → Austin's sibling proof

- **Onset**: Feb 11, Tao's "reading seminar on density Hales-Jewett"
  (comments 600–699) — reading Furstenberg–Katznelson with intent to
  finitize; Feb 13, S6: "McCutcheon.508: Ergodic proof strategy".
- **Interior**: Feb 14 seminar exchanges (S6: Tao "More randomness needed to
  invert maps" vs O'Donnell "Enough randomness already in [3]^n"; Tao
  "Finitary analogue of stationarity"); Feb 21, S6: "Tao: Finitary ergodic
  proof of DHJ(2) proposed"; Feb 25, S6: "Tao: Finitary ergodic sketch of
  DHJ(3)".
- **Pivot**: Mar 9, S6: "Austin.894: New ergodic proof of DHJ(k)" — the
  arc's product lands OUTSIDE the project's main line, announced in-thread
  one day before the main announcement.
- **Terminus**: the ergodic route never becomes the polymath proof (which is
  the "first elementary proof"); instead it is retained and partially
  merged back: Mar 12/14, S6: Tao's "Informal combinatorial translation of
  Austin's proof" / "Ramsey-free translation of Austin's proof".
- **Relations**: parallel track; exports intuition (stationarity, IP
  convergence) into the main line; produces an individually-credited sibling
  artifact; partial merge-back post-terminus.
- **Evidence**:
  - [VV, S5] "(Indeed, taking some inspiration from a few of these blog
    comments, Austin provided another new (ergodic) proof of the density
    Hales–Jewett theorem [Aus09].)"
  - [VV, S5] "In this paper, we give the first elementary proof of the
    theorem of Furstenberg and Katznelson" (abstract — the polymath proof is
    NOT the ergodic one).
  - [EG, S6] the dated chain Feb 11 → Mar 14 above.
- **Confidence**: HIGH.
- **Recovery notes**: the subtlest arc; its correct recovery and NEG-N2's
  correct rejection are two sides of one judgment. Anchor discipline
  decides.

## ARC-P8 — Establishment: robustness consensus → DHJ(k) within days → pseudonymous write-up

- **Onset**: Mar 9–10, the sketch (Gowers.2633) and the announcement post.
- **Pivot**: the group's establishment test is explicitly about robustness,
  not verification-by-authority. From the terminus event itself
  (chronological-side, used here only to describe the terminus): [EG] "I
  hereby state that I am basically sure that the problem is solved (though
  not in the way originally envisaged)"; [EG] "not just some calculations
  that magically manage not to go wrong, but higher-level explanations
  backed up by fairly easy calculations"; participants "share the feeling
  that the argument is 'robust'".
- **Interior**: Mar 11–12, S6: "Correlation component of DHJ(k) proof
  complete"; "No apparent obstacles to proving DHJ(k)"; "O'Donnell.1021:
  DHJ(k) => Varnavides completed".
- **Terminus**: the generalization surprise and the collective identity.
  [VV, S5]: "Unexpectedly, it turned out that once we had proved the case
  k = 3 of the density Hales–Jewett theorem, it was straightforward to
  generalize the argument to the k ≥ 4 cases." [VV, S5]: "it was proved in a
  rather unusual 'open source' way, which is why it is being published
  under a pseudonym." Write-up threads run through 2009–2010.
- **Relations**: child of P5; the DHJ(k) generalization retroactively
  upgrades P2/P3/P4 machinery to k-general form.
- **terminusSurface prediction**: narratedTerminus.
- **Evidence**: as quoted above, plus [EG, S1] "it looks as though we have
  proved a stronger result than seemed remotely feasible then".
- **Confidence**: HIGH.
- **Recovery notes**: full credit requires BOTH the consensus event (with
  its hedged form — "probably", "basically sure") AND the
  fast-generalization surprise. The hedge is part of the finding: an
  ingester that records an unhedged "proved on Mar 10" has flattened the
  epistemics and earns at most PARTIAL.

---

## Sealed prediction on terminus surfaces (ties to VOCAB-NOTE-KH3 §2)

Blog culture narrates its completions. Sealed expectation: positive
completions carry a NARRATED terminus surface (P5, P8, and P6's second-paper
terminus), while abandonments terminate SILENT (P1, P4's ladder, the Fourier
subtrack inside NEG-N3). If the ingester's harvest marks kh:terminusSurface,
this split is the expected pattern; a uniform surface across all arcs would
be evidence against the v3 terminus machinery's discriminating power.

---

## EXPECTED NEGATIVES — dead ends a naive reader might call arcs

Grading: for each negative, the CORRECT ingester behavior is to record the
material as abandoned/open know-how (retained, with its rejection reason),
and never to mark it established. An ingester output that asserts any
negative as an established claim is a hallucinated-established-claim (the
zero-tolerance class, protocol §4).

- **NEG-N1 (HIGH)**: "The triangle-removal approach produced the proof."
  FALSE. The final proof is density-increment; approach A was abandoned.
  Evidence: ARC-P1's quotes ([EG, S1] "moved off into other directions";
  [VV, S5] "follows the density increment method"). The trap: the launch
  post's title and frame, plus three weeks of triangle-removal work.
- **NEG-N2 (HIGH)**: "Austin's ergodic proof was the project's proof / the
  March-10 result." FALSE. Separate, individually-credited, ergodic (hence
  non-elementary) sibling, announced IN-THREAD on Mar 9. Evidence: [VV, S5]
  the "taking some inspiration" parenthesis; [VV, S5] "first elementary
  proof". The trap: proximity — one day before the announcement, in the
  same comment stream.
- **NEG-N3 (HIGH)**: "The Fourier-analytic route produced the proof."
  FALSE. Extensive February Fourier work (S6: O'Donnell.476 "Fourier-analytic
  Sperner computations" Feb 12; "Fourier computations on equal-slices measure
  begin" Feb 18; three Fourier DHJ(2) proofs Feb 23–28) was retired; the
  paper's method statement excludes it: [VV, S5] "the most advanced notion
  we need is that of the total variation distance between discrete
  probability distributions."
- **NEG-N4 (MEDIUM)**: "The hyper-optimistic conjecture was resolved / was
  load-bearing for the DHJ(3) proof." FALSE within the corpus window: stated
  Feb 11, verified n ≤ 6, OPEN at window close; numbers-branch only; the
  DHJ(3) proof does not use it. Evidence: [EG, S8]. MEDIUM because it rests
  on one curated wiki page.
- **NEG-N5 (MEDIUM)**: "Solymosi's Moser(6) ⇒ DHJ(3) observation became a
  proof route." FALSE as a route: a recorded cross-link (S6, Feb 20) with no
  follow-through to a proof within the window (Moser(6) was not computed).
  MEDIUM: single-entry sourcing; if the ingester asserts otherwise WITH
  anchors, the judge must check the anchors before scoring — the seal may
  lose this one honestly.

## Expected know-how retention (probe SP-2 checkables)

A good harvest RETAINS the abandoned/parallel material as first-class
know-how rather than deleting it or promoting it. Checkables (any 3+ of
these retained with rejection-reason/status intact = SP-2 pass):

1. The obstructions-to-uniformity catalog (P2 onset material).
2. The triangle-removal approach with its reason-for-abandonment (P1).
3. "New proof of Ajtai-Szemeredi" (Mar 8) — a standalone yield en route.
4. "Multidimensional Sperner written up" (O'Donnell, Mar 8).
5. Tao's combinatorial translations of Austin's proof (Mar 12/14).
6. The hyper-optimistic conjecture as OPEN (not resolved).
7. The c_n / Moser bounds tables as the numbers branch's product.

## Retrospective disagreements (trial material, recorded not smoothed)

- **D-1 Participation size**: Gowers [EG, S1/S3]: contributors "settled down
  to a handful, all of whom I knew personally"; Nielsen [EG, S3]: "23
  contributors to date"; Cranshaw–Kittur [VV, S9]: 39 users left numbered
  comments, and "the top three commenters produced 55% of the comments, and
  the top ten commenters produced nearly 90%". Not an error — three counting
  rules (core, notable, any-numbered-comment). An ingester's participation
  claims should be graded against WHICHEVER counting rule it states.
- **D-2 Comment totals**: "More than 1000 mathematical comments" at 7 weeks
  [EG, S3]; 1,228 numbered / 1,555 total on the 14 core posts, Feb 1–May 23
  [VV, S9]; 1,509 comments / 112 active days in the WWW16 dataset [VV, S10].
  Dataset-scope differences, all correct.
- **D-3 Toy-ladder dating**: S6 lists McCutcheon's "Ramsey proof of
  DHJ(2.6)" under Feb 14 (comment 2206) and Tao's "DHJ(2.6) proposed" under
  Feb 15 (comment 2196). Comment numbers resolve the order (proposal first);
  the timeline's day boundaries are soft. Kept as-is.
- **D-4 Numbered-range vs comment-count**: the wiki ledger's ranges (e.g.
  "1000-1049" for the announcement thread) undercount actual comments (133
  responses on that post) because meta/unnumbered comments don't get
  numbers. Both figures are right; the ingester should not "reconcile" them.
- **D-5 Thread-number/chronology inversion**: the thread numbered 1050–1099
  opened Mar 16 (Gowers), AFTER the thread numbered 1100–1199 (Tao, Mar 14).
  Verified via blog archives. A chronology trap (probe SP-3), not an error.
- **D-6 Launch-post count**: 221 responses on the launch post vs wiki range
  1–199. Same phenomenon as D-4.

## Probe index

- **SP-1** peripheral-becomes-central: ARC-P3 (grading inside P3).
- **SP-2** abandoned-approaches-retained: checkables above.
- **SP-3** chronology traps: D-5 inversion; NEG-N2's in-thread adjacency;
  D-3 soft day-boundaries. Pass = the ingester's chronology survives all
  three without confabulated smoothing.

## Sealed totals (for the protocol's public counts — content stays here)

8 arcs: 6 HIGH (P1, P2, P3, P5, P7, P8), 2 MEDIUM (P4, P6).
5 expected negatives: 3 HIGH (N1, N2, N3), 2 MEDIUM (N4, N5).
3 probes (SP-1, SP-2, SP-3). 1 sealed terminus-surface prediction.

— Sealed by the SEALER session, 2026-08-13. Nothing above may be edited
after the SHA-256 is recorded in the protocol. Corrections, if ever needed,
go in a separate dated addendum file whose existence the judge must report.
