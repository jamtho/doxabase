# Phase A — Normalized registry of the ingester's recovered arcs

Judge session, 2026-08-13. Written BEFORE any access to /home/codex/polymath-seal/.
Sources read for this phase, and nothing else seal-side: the protocol, the run
ledger, /home/codex/polymath-frozen/INGEST-1.md (hash-verified
8bc246e85b8986b4339990b4a22f88cb95c3b097f8b66870cfeb912f1dffd941), and
/home/codex/polymath-frozen/capsule-frozen.sqlite (hash-verified
53ee499b9c9f120d23f6df4428068718fdf828cb06605be0fd3ab7632c065cf1, queried via a
scratch-dir copy).

Ingester output shape: 394 observations / 192 claims / 394 evidence / 26 kh:Episode /
9 kh:Arc / 3 kh:DeclinedOption; 4 refused near-miss arcs recorded with reasons;
all arcs use kh:terminusSurface = kh:silentTerminus. All comment-level anchors are
WordPress `#comment-<id>` fragments on allowlist URLs (the run ledger and Session 2/5
notes both state WordPress ids, not participants' inline numbers, are the anchor).

## The nine recovered arcs (normalized)

### A1. credit-becomes-named-policy
- Onset (questionArrives): credit/attribution raised in launch-thread comment #1
  (Michael Lugo, launch post #comment-1589, 2009-01-27); post-body pseudonym idea
  (launch post body); sustained doubts Chow #comment-1725 (#42), Bogdan's unresolved
  CC-BY-SA licensing question #comment-1763 (#49), Reid #comment-1947/1948/1950.
- Pivot: "I would of course propose \"D.H.J. Polymath\"." — Ryan O'Donnell logistics
  aside, thread 17 (1050-1099) #comment-3227/3228, 2009-04-15, implicitly approved.
- Terminus: Gowers's completion-and-licensing policy reply, thread 17 #comment-3328
  (2009-05-08): names off paper, wiki attribution, ~1-week skeleton-draft start, open
  use of unused material on declaring done; resolves Bogdan's launch-thread question.
  Silent terminus; never renegotiated afterward (O'Donnell's self-archiving
  #comment-3305 treats it as settled infrastructure).
- Establishment status: policy settled-in-record (becameAutomatic asserted for
  attribution/licensing negotiation ceasing). Confidence: Medium.

### A2. numbering-becomes-routine
- Onset (casesAccumulate): ad hoc lettering/numbering on thread 4 (post body,
  2009-02-01; convention founded #comment-1675 (#19)); collision-and-repair saga
  #comment-1713/1714/1717/1718/1719/1720/1721 (two "(48)"s, Gasarch "45.5").
- Pivot: Gowers comment 300, thread 6 #comment-1904 (2009-02-06): block scheme
  200s/300s/400s + 100-comment summarize-and-restart rule (verbatim pivotQuote).
- Terminus: rule applied as routine: Tao closes his bounds thread (#comment-35781,
  35799, comments 272/277, 2009-02-13) and thread 16's close #comment-37598/37616
  (2009-03-30) — applied without restatement. Silent terminus.
- Establishment status: became-automatic asserted (scheme never renegotiated).

### A3. thread-splitting-learns-from-failure
- Onset (casesAccumulate): Jason Dyer's organization proposals, thread 4
  #comment-1694 (unnumbered, 2009-02-02) and #comment-1699 (multi-post proposal
  deferred).
- Pivot: Tao: "we tried splitting up into more threads earlier, but found that all
  but one of them would die out quickly" — thread 9 #comment-2230 (17 Feb 2009; member
  45126b7e = comments 534-536, #comment-2229/2230/2234). Supporting: Gowers's
  "partially worked" metacomment thread 7 #comment-2137; Tao's reading-seminar
  counter-proposal #comment-2140/2141/2145.
- Terminus: later venue decisions swift/undisputed — threading poll post (thread 11
  body) + limited-threading adoption (thread 12 body); meta-thread founding, thread 15
  #comment-2688 (Tao proposes) / #comment-2691 (Gowers same-day commit), 2009-03-10.
  Silent terminus.
- Establishment status: became-automatic asserted (venue-opening becomes same-day
  undebated act).

### A4. rule-six-becomes-standing-policy
- Onset (UNASSIGNED, honestly: "no catalog kind cleanly fits a self-issued founding
  rule"): launch post body ground rules 6-9 (2009-01-27).
- Pivot: "because I formulated rule 6 I have felt obliged to stick to it." — Gowers,
  thread 9 Metacomments #comment-2241 (with Tao #comment-2249, Gil #comment-2251,
  17-18 Feb 2009); scoped protocol committed #comment-2253 (18 Feb).
  Prior invocation: thread 4 #comment-1816 (comment 109, rule 6 named, permission asked).
- Terminus: policy simply stated, not requested — thread 12 #comment-2414 (comment
  816, seven-step plan, "private calculations (though made public as soon as they
  work)") and #comment-2443 (comment 824, the inverted-disclosure norm as settled
  description). Silent terminus.
- Establishment status: became-automatic asserted (scoped exception is the default).

### A5. self-correction-becomes-routine
- Onset (UNASSIGNED, honestly: retraction already mid-correction when first
  recorded): Sperner pair-removal conjecture, thread 4 #comment-1677/1678 (comments
  21/22) retracted "completely false" #comment-1686 (comment 27, 2009-02-02).
- Members span every stage: 308→315 "back to the drawing board" (thread 6
  #comment-1921); Conjecture 411 refuted/adopted (thread 7 #comment-2029,
  #comment-2044/2045); DHJ-equivalence reversal (comments 492-496, #comment-2169…2183);
  Tao's Moser-bound confession (thread 10 #comment-36174, comment 773); 12-set
  collapse (thread 13 #comment-2595…2601); post-announcement bug confession
  (thread 15 #comment-2919, comment 1046, "it did give me a bit of a scare") and fix
  #comment-2920/2921.
- Pivot: "perhaps the good news is actually that polymath is like math with a net."
  — Randall, thread 15 #comment-2926/2927 (comment 1046.1, 2009-03-16).
- Terminus: register change — Tao's naive-saturation conjecture refuted and conceded
  in one undefended sentence ("Well, so much for the naive conjecture…"), thread 16
  #comment-37527 (proposed) and #comment-37557/37560/37561 (refuted, comments
  1185-1187, 2009-03-30). Silent terminus.
- Establishment status: became-automatic asserted as REGISTER change (correction stays
  public, stops being dramatic).

### A6. measure-choice-becomes-technical
- Onset (casesAccumulate): equal-slices vs uniform run as competing strategic
  commitments — thread 7 #comment-2068/2071/2073/2075 (comments 428-434, Boris
  counterexample testing) and onset member #comment-2101/2109/2119 (comments 447/452/
  459, Gowers's sustained defense, 10-11 Feb 2009).
- Pivot: Tao's "ergodic perspective" synthesis, thread 7 #comment-2120/2121/2123
  (comments 460-462); pivotQuote is Gowers's credit: "Terry, thanks for that useful
  summary. I think it's helped me to understand the ergodic side of things better".
- Terminus: MIXED, recorded honestly. Technical interchangeability completes —
  O'Donnell's reversal "the expression in #567 is so elegant, how can I not be on
  board for equal-slices now?" (thread 9 #comment-2308, comment 571, 2009-02-20, after
  Gowers's #comment-2299/2300). But the write-up's expository measure choice is STILL
  REVERSING at record's end (thread 17 #comment-3267/3273/3656, Apr-Jun 2009).
  becameAutomatic asserted ONLY for the technical strand. Silent terminus.
- Establishment status: partial/mixed, explicitly not smoothed.

### A7. proof-strategy-collapse-to-breakthrough
- Onset (anomalyRegistered): first proof idea self-undercut in the same post body
  ("Wow… Unfortunately it doesn't"), thread 4 post body letters O-R (2009-02-01);
  triangle-removal continuation (thread 6 post body); deprioritized in thread 9 post
  body four-strategy survey (2009-02-13).
- Pivot: "It is for this reason that I think our best hope is to go back to
  Ajtai-Szemeredi, because they avoided this problem." — Gowers, thread 13
  #comment-2600 (comment 875, 2009-03-07), after the 12-set "Probable collapse"
  #comment-2595 (comment 873, 2009-03-06) and confirmation #comment-2596/2597/2601.
- Terminus: double-partition idea hedged overnight and confirmed (#comment-2613/2617,
  comments 881/881.2, 2009-03-08); "in the bag" + DHJ(k) prioritization + same-night
  independent agreement (#comment-2633/2635/2637, comments 885-885.3, 2009-03-09);
  hedged public declaration (thread 15 post body, 2009-03-10); thread 17 post body
  pure write-up framing. Silent terminus; hedges kept.
- Establishment status: became-automatic asserted (strategy never re-litigated);
  the ingester records the announcement as HEDGED, not as "proof complete."

### A8. establishment-verification-standard
- Onset (UNASSIGNED, honestly: a declaration fits none of the five catalog onset
  kinds): the "basically sure… (probably)" announcement, thread 15 post body
  (2009-03-10) — SHARED MEMBER with A7's terminus.
- Pivot: Gowers's verification-standard reply to Gil Kalai's challenge — challenge
  #comment-2760 (comment 1015, 2009-03-11), reply #comment-2762 (comment 1015.1);
  pivotQuote: "But if one regards a write-up as having a tree structure, then it's
  all there on the wiki down to the small sticks, and only a few leaves are missing."
  Individual criterion (no unclosed logical gaps) + social criterion (participants'
  independent shared confidence); hedge explicitly retained.
- Terminus: standard tested for real — post-announcement error confessed
  #comment-2919 (comment 1046, 2009-03-16), fixed/generalized #comment-2920/2921,
  Randall's "math with a net" gloss #comment-2926/2927; afterward solvedness is never
  re-opened (thread 17 post body 2009-03-16 is pure write-up framing). Silent terminus.
- Establishment status: became-automatic asserted for the QUESTION ceasing, not for
  "the proof is verified" — participant-stated basis for the standard itself.

### A9. generalize-to-dhjk-frame-outlives-arithmetic
- Onset (casesAccumulate): un-flagged aside in a routine computation — Klas
  Markström, thread 16 #comment-37205 (comment 1135, 2009-03-23: "For which values of
  n and k is the optimum size (k-1)k^n?"); five-author chain #comment-37233/37239/
  37244/37249/37252/37254/37265 (comments 1137-1143).
- Pivot: Tao's formal retitle, thread 18 post body (2009-03-30): "The focus has now
  mostly shifted to generalisations… so I am changing the title here from DHJ(3) to
  DHJ(k) to reflect this."
- Terminus: DELIBERATELY MIXED — the FRAME becomes automatic (Eppstein newcomer
  material #comment-37674/37682, tiling program #comment-37925/37973/37975 proceed
  matter-of-factly under DHJ(k)); the MATHEMATICS fades: last-fetched comment is
  Kevin O'Bryant's unanswered speculative proposal #comment-38960 (comment 1270,
  2009-05-23; plus stray 2011 #comment-50467). Silent terminus, honest fade.
- Establishment status: became-automatic for frame only; math explicitly NOT settled.

## DeclinedOptions (abandoned approaches retained as know-how) — 3

- D-1: 12-set/subspace double-iteration density-increment argument
  (declined/12set-density-increment-argument, on episode
  gowers-reports-12set-density-increment-collapse, shape honestNegative). Decline
  reason: Gowers's shrinkage diagnosis ((1-1/n)^n vs (1-1/n)^(n^2)); REVIVAL CONDITION
  quoted ("…at the moment it feels to me as though a new idea is still needed").
  Anchors: thread 13 #comment-2595, #comment-2596/2597/2601.
- D-2: corners-theorem bypass route to Szemerédi skipping DHJ
  (declined/corners-bypass-route, new episode randall-corners-bypass-declined, shape
  refusedOption). Decline reason: proposer's own verdict "it seems to be complete
  garbage… I am convinced that the DHJ proof is the right one for Szemeredi after
  all." Anchor: obs f92b79b6 (Session 7's G15-C10, thread 15).
- D-3: further multi-way general-purpose thread-splitting
  (declined/further-multiway-thread-splitting, on episode
  tao-splits-into-local-thread-and-reading-seminar, shape processNormEnacted).
  Decline reason: Tao's die-out diagnosis + Gowers's "once the 400 thread was opened
  the 300 thread died pretty rapidly." No revival condition stated (none in record).

## Refused near-misses (recorded as refusals, NOT in graph) — 4 detailed

- R-1: wiki-as-collaborative-writing-venue arc — refused: its only clean pivot
  (thread 18 body wiki-first prescription) already serves A9; folded into A2/A9.
- R-2: "quasirandom subset of [3]^n" open-definition arc — refused on terminusBasis
  grounds: question silently bypassed, never used; "silence is not automaticity."
  (Gap flagged by Sessions 4, 6, 7, 8; never settled in the fetched record.)
- R-3: Randall's corners-bypass — refused as arc (single merged observation cannot
  honestly meet ArcShape's ≥2 members); recorded as DeclinedOption D-2 instead.
- R-4: jozsef's "removal lemma for DHJ" + "Shelah's vs DHJ" flip-flop exchange —
  refused: material deliberately never admitted to the graph by harvest sessions
  (self-contained, unresolved).
- Plus five smaller candidate onsets/pivots folded into synthesis friction notes,
  incl. two onset-shape near-uses declined (expertReframeReceived for A6 — the
  synthesis is the pivot, not the onset; priorFormationSurfaces for A4 — launch post
  is in-corpus day one, not off-channel prior formation). Also a fourth DeclinedOption
  candidate (Carter's Google Group / Starbureiy's Knol, Session 1) refused because no
  decline reason exists in the record.

## Establishment-semantics inventory (for the zero-tolerance check)

The ingester asserts establishment semantics ONLY in these places: the nine arcs'
kh:becameAutomatic fields (as itemized above; A6 and A9 deliberately partial/mixed),
their terminusBasis claims, and harvested observations that QUOTE participants'
own establishment claims with hedges preserved ("basically sure… (probably)";
"in the bag" recorded as a claim by Gowers with same-night agreement; computed
values c_5=150/c_6=450 recorded WITH their two-independent-methods confirmation
protocol and OEIS gate; c'_5=124 recorded as landing via Cantwell's proof, human
proof completed thread 18 #comment-…, with externally-caught missing case).
Notable honest negatives kept open by the ingester: quasirandom-subset definition
(never settled), HOC truth confidence downgrade (T18-C1), write-up measure choice
(still reversing at record end), thread 17/18 fade-out terminus (no successor named),
Austin's proof recorded as independent/parallel (not the group's), hyper-optimistic
conjecture NOT asserted proved anywhere; super-optimist conjecture recorded as
refuted same-day.

## Probe-relevant material (normalized before seal access)

- Peripheral-becomes-central candidates in the ingester record: equal-slices measure
  (doubted → central via Parseval identity, A6); Klas Markström's aside → DHJ(k)
  reframe (A9); Ajtai-Szemerédi (named in thread 9 survey as one of four, becomes THE
  route, A7); the wiki (side venue → carrier of write-up).
- Abandoned-approaches-retained: the three DeclinedOptions above + triangle-removal
  deprioritized (A7 members) + Varnavides fix "held in reserve" (G-B2, Session 3).
- Chronology traps the ingester handled: thread 16 (1100-1199) opened BEFORE thread
  17 (1050-1099) — preserved and explained (Session 8); comment 215 citing "a copy of
  340" hours before 340 existed (Session 3, left as observed); inline-number
  collisions (five on thread 9 alone) — anchors always WordPress ids; thread "1050-
  1099" numbering extending past nominal caps; unnumbered/decimal comments recorded
  as such.

Phase A is COMPLETE and FROZEN as of this file's writing. The seal has not been
opened, read, listed, or accessed in any way before this point.
