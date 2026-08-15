# Know-How Consumption Trial — the Sealed Two-Arm Harvest Protocol

**Committed BEFORE any trial agent runs** (doc 15 §4's pre-commitment requirement;
the seal-before-trial heuristic applied to the trial that tests it). **Date**:
2026-08-15. **Author**: the consumption-trial protocol author, on the curator's
chosen design (owner's 2026-08-15 round deferred the next step to the curator;
observation 2c509405). This file is the seal: the task, the material allocation,
both arm briefs (verbatim, as appendices), the mechanical metrics, the judged
rubric, the blinding mechanics, the deviation classes, and what counts as a win
are fixed here. Nothing may be adjusted after the first arm launches; any
deviation must be reported under the classes in §10. The coordinator records this
file's SHA-256 in the trial record at launch, before either arm runs.

## 1. The trial in one paragraph

Every prior trial in this program tested whether a capsule carries knowledge TO a
reader. This one closes the loop: does briefing a working agent FROM the know-how
capsule measurably change how it works? Two cold agents perform IDENTICAL
instances of a real corpus task — Gerrit harvest tranche 2, in the tranche-1
style, each on its own pre-allocated, disjoint slice of OpenStack Gerrit, each
into its own fresh v4-seeded capsule. The CONTROL arm gets the competent-baseline
brief (task + technical context + access rules, padded to length with generic
professional guidance). The CAPSULE arm gets the identical brief PLUS the home
capsule's know-how layer rendered in: the 11 promoted heuristics (behavioural
statement, applicability, failure modes — verbatim from the live graph) and the
5 most task-relevant arcs' lessons. The delta between the briefs is ONLY the
know-how content. Measurement is two-layer: a MECHANICAL layer counted from
artifacts without judgement, and a JUDGED layer graded blind by a judge who
receives the arms as X and Y after a preparer strips arm-identifying content.
The null hypothesis is honest and live: a competent agent with a good task brief
may not need the distilled layer at all. A null is a real result and gets
reported as one. Both arms' harvests are real tranche-2 corpus material either
way — the trial rides on work the program wanted done regardless.

## 2. Design summary

| | Arm CONTROL (T2A) | Arm CAPSULE (T2B) |
|---|---|---|
| Task | Gerrit harvest tranche 2, 60–80 fresh changes | identical |
| Material | EVEN change-number deciles (§3) | ODD change-number deciles (§3) |
| Capsule | fresh, v4-seeded (1180 quads) | identical (own copy) |
| Brief | common core + generic-practice padding (1156 words) | common core + know-how render (1283 words) |
| Model / budget / sessions | recorded model, 120 ops, 1 session + 4 graders | identical |
| Told of comparison | no | no |

The delta between Appendix B and Appendix C is confined to one section (§6 of
each brief). Everything else is word-identical. The know-how section was
rendered from the LIVE home graph on 2026-08-15 and is quoted verbatim in
Appendix C so the delta is auditable (provenance: Appendix E).

## 3. Material allocation — the contamination contract

The arms must never touch the same material. Allocation is mechanical, decided
here, and total (covers every change number that exists or will exist):

- **Band rule**: for change number n, let d = floor(n / 10000) (its "decile").
  EVEN d → arm T2A. ODD d → arm T2B. Concretely, over the plausible harvest
  range: T2A may touch 920000–929999, 940000–949999, 960000–969999,
  980000–989999, 1000000–1009999, …; T2B may touch 930000–939999,
  950000–959999, 970000–979999, 990000–999999, 1010000–1019999, …; and so on
  by parity in both directions without limit. Disjoint by construction.
- **Parity assignment rule** (fixed mechanically, outside anyone's discretion):
  the CONTROL arm takes the EVEN deciles if the exclusion list's SHA-256 first
  hex digit is even, the ODD deciles if odd. The exclusion list hash (below)
  begins `0` — even — so CONTROL = even deciles, CAPSULE = odd deciles.
- **Exclusion list**: `exclusion-list.txt` — **534 change numbers** (min 6361,
  max 1000702), SHA-256
  `0123f307b5d69279a035baa63e9cd87c35b77f68cb7cc11eb83500ce47794e21` —
  materialized 2026-08-15 from every change number appearing in the scout and
  tranche-1 artifacts: the tranche-1 raw bulk lists (all `_number` fields of
  listed changes), all per-change comments fetches (both sessions), the
  selection and screening files, the scout's candidate/digest artifacts, plus a
  belt-and-braces sweep of every change number cited in the two journals (the
  sweep added zero — artifact coverage was already complete). NEITHER arm may
  fetch, grade, or stage any listed change, regardless of band.
- **Merge cutoff**: only changes whose list data shows them merged (submitted)
  before **2026-08-15T00:00:00 UTC** are eligible. Enforced client-side from
  the bulk-list `submitted` field. This removes live-drift asymmetry between
  the two runs.
- **Projects** (both arms, fixed): openstack/nova, openstack/neutron,
  openstack/cinder, openstack/keystone, openstack/glance, openstack/swift,
  openstack/ironic, openstack/manila, openstack/octavia — tranche-1's nine.
- **Honest asymmetry, recorded now**: the exclusion list is not band-balanced —
  342 of its 534 numbers fall in decile 99 (odd → CAPSULE side), 106 in
  deciles 98+100 (even → CONTROL side), because tranche-1 fished the most
  recent merged changes. Both pools remain enormous (>150,000 merged changes
  exist across the nine projects), but the capsule arm will page slightly
  deeper to fill quotas — a small op-cost bias AGAINST the capsule arm on M6,
  direction recorded here so it cannot be argued after the fact.
- An accidental fetch of an ineligible change (wrong band, listed, or
  post-cutoff) must be quarantined: nothing staged from it, the miss recorded
  in the arm's journal. Fetched-and-quarantined = D2; graded-or-staged = D1.

## 4. Conditions

- **Agents**: two cold archivist agents, one per arm, plus exactly 4 grader
  sub-agents per arm. All ten use the SAME model — the program's standard trial
  consumer (Sonnet-class); the coordinator records the exact model id BEFORE
  the first launch. No repo access, no study-journal access, no capsule access
  other than the arm's own fresh capsule, no search engines, no network host
  but review.opendev.org. Neither arm is told a comparison is running, told of
  the other arm, or told of a judge; both are told (truthfully) that they are
  the tranche-2 archivist for the phase-2 harvest and their capsule + journal
  become program assets.
- **Working dirs** (coordinator creates before launch): `/home/codex/gerrit-t2a/`
  and `/home/codex/gerrit-t2b/`, each containing: a venv with the doxabase
  0.2.0 wheel installed (same wheel file both arms, from
  `/workspaces/doxybase/dist/`), `bridge.py` (the study-standard bridge, capsule
  path pointed at the arm's own `capsule.sqlite`), `kh-vocab-seed.trig` (v4
  seed, 1180 quads, SHA-256
  `213da77a9d4988c7c4eb6ff0680474fe397368d24e9d2e6012eb383ea1b05fd4`),
  `exclusion-list.txt` (hash above), `GRADING-BRIEF.md` (tranche-1's, verbatim,
  SHA-256 `7631001a439a7569c29860af3b2d186881b9c6980754a5ea8067381dc0452a62`),
  and `BRIEF.md` (Appendix B for T2A, Appendix C for T2B). At launch the
  coordinator diffs each delivered BRIEF.md against its appendix: any
  difference beyond the placeholder classes (working-dir letter, UA letter,
  band parity + decile list) is D1.
- **Budgets**: 120 network operations per arm, ledgered before firing, 2.0s
  minimum pacing, UA `doxabase-knowhow-gerrit-t2a/0.1` / `...-t2b/0.1`.
- **Sessions**: one archivist session per arm (one continuation session
  permitted on context exhaustion — D2 note), 4 grader sessions per arm.
- **Launch order**: sequential, T2A first, then T2B (pre-committed; the merge
  cutoff makes order immaterial to material, and sequential runs keep the 2.0s
  host pacing honest). Coordinator interaction with a running arm is limited
  to launch and collection; content-neutral infrastructure help is D2,
  content steering is D1.
- **Order of operations**: (1) this protocol committed → (2) coordinator
  materializes dirs, records hashes + model id → (3) T2A runs → (4) T2B runs →
  (5) coordinator freezes both working dirs (SHA-256 over journal + capsule)
  → (6) preparer builds judge packs, seals assignment (§8) → (7) judge grades
  (§7) and (8) measurer counts (§6), in either order or parallel, neither
  seeing the other's output → (9) verdict assembled per §9 → (10) trial
  record written.

## 5. The briefs and the delta

- **Common core**: role, access rules, material allocation, the tranche-1
  method (screening, probes, selection composition, grading pipeline, capsule
  mechanics, person-model ceiling), the scout's two GO conditions, the four
  research questions, and the deliverables list — word-identical across arms
  outside the placeholder classes (working-dir letter, UA letter, band parity
  + decile list; machine-verified from one template). Appendices B and C,
  §§1–5 and 7.
- **The delta is §6 of each brief and nothing else.** CAPSULE §6 = the know-how
  render: all 11 promoted heuristics with label, behavioural statement,
  applicability condition, and known failure modes, quoted VERBATIM from the
  live graph (render rule: every kh:behaviouralStatement,
  kh:applicabilityCondition, and kh:knownFailureMode literal on every
  kh:Heuristic instance, in alphabetical IRI order, character-for-character),
  plus the lessons (kh:becameAutomatic, verbatim) of the 5 most task-relevant
  arcs. CONTROL §6 = generic professional guidance, structurally parallel
  (11 practices + 5 principles, each with do/applies/pitfall), length-matched:
  1156 words vs 1283 (90.1% — within the pre-set ±10% band).
- **Arc selection rationale** (an author degree of freedom, stated): of the 14
  home arcs, the 5 rendered are the ones whose lessons bear on archivist work
  — delegation-and-verification culture, sighting-count/refusal discipline,
  couldn't-say production, threshold justification, and graph-vs-bulk-data
  placement. The 9 excluded are AIS/product-surface-specific (identity-freeze,
  voyage-to-transit, maps-are-the-interface, workbench-legibility,
  injection-demystifier, elicitation-loop, transcripts-sample-the-work,
  aisidentity-not-emitter) or a foreign re-expression (polymath). A different
  selection could change the result; claims attach to this render (§11.2).
- **Padding rationale** (stated now so it cannot be re-argued): the padding is
  REAL generic guidance, including generic quality advice ("double-check
  before you report"), not deliberately vacuous filler — because the capsule
  layer's claimed value is its specificity (recorded failure modes,
  applicability conditions, this project's actual traps), not the platitude
  level. This makes the trial harder for the capsule arm and a win more
  meaningful.
- **Render freeze**: the know-how text in Appendix C is frozen as rendered
  2026-08-15 (provenance and source hash in Appendix E). If the live graph
  moves between commit and launch, the trial still runs on THIS render (the
  drift is recorded as a D3 note); after first launch the text may not change
  at all (D1).
- **A protocol note, recorded at authoring time**: the tasking memo for this
  protocol described "12 promoted heuristics." The live graph holds **11**
  kh:Heuristic instances (verified 2026-08-15 by direct read-only query;
  DISTILL-4's end-state census agrees). Graph over journals — the program's
  own law — so 11 are rendered, and the discrepancy is recorded here rather
  than smoothed.

## 6. Measurement layer 1 — MECHANICAL (counted from artifacts, no judgement)

Counted by the MEASURER (§8) identically for both arms, using the frozen
working dirs. Per-metric better-direction and tie rules are fixed here; a tie
counts to neither arm.

- **M1 — staging-failure rate** = (staged revisions that reached validation and
  failed, were refused at apply, or were closed discarded for cause) ÷ (applied
  revisions). Pure tool-envelope schema errors (calls that error before
  producing a staged row) are excluded — they are the platform's designed
  targeted-error teaching, not harvest failures. Source: bridge_log.jsonl +
  revision rows. Lower is better; tie = exact equality.
- **M2 — quote-verification failure rate** = (staged episodes containing ≥1
  quote that fails whitespace-normalized verbatim match against the arm's OWN
  raw fetched JSON) ÷ (staged episodes). Measurer-run uniformly (tranche-1's
  verify_quotes.py pattern) regardless of what the arm itself ran or reported.
  Lower is better; tie = exact.
- **M3 — dead-anchor rate** = (IRI references in the capsule that resolve to no
  subject in the capsule, plus in-record anchors naming a change/patchset/file
  absent from the arm's raw data) ÷ (total such references). Lower; tie exact.
- **M4 — unverified-claim rate** = (checked journal claims contradicted by the
  arm's graph or ledger) ÷ (claims checked). Claim classes, pre-committed —
  the measurer enumerates EVERY final-journal sentence in these classes and
  checks each mechanically: (a) numeric counts of capsule contents or
  operations; (b) conformance / zero-staged-debt / parity claims;
  (c) universally quantified harvest claims ("all", "every", "zero", "none").
  Lower; tie exact.
- **M5 — coverage-statement completeness**: 0–10 checklist, one point each:
  (1) every list op's result count stated; (2) screening rule stated with
  counts in and out; (3) selection composition with per-reason counts;
  (4) every selected change accounted for in the grading table; (5) excluded
  or failed fetches enumerated; (6) every probe's hit disposition stated
  (kept/discarded and why); (7) eligibility confirmation stated (bands,
  exclusion list, cutoff checked over all graded changes); (8) final census
  stated WITH its method, and the method is a graph read; (9) ops accounting
  reconciles (ledger total = stated total ≤ budget); (10) an explicit
  statement of what was NOT covered. Higher is better; tie exact.
- **M6 — op efficiency** = total ledgered network ops ÷ graded changes
  (secondary, reported not scored: ops per A+B unit). Lower is better;
  tie = within ±0.05 ops/change. Known small bias against the capsule arm
  (§3, pool depth) — recorded, not corrected.
- **M7 — end-state integrity**, 0–3: +1 validate_graph scope=all conforms
  (measurer-verified on the capsule, not journal-trusted); +1 recovery
  planner reports zero staged debt; +1 observation/evidence parity. Higher;
  tie exact.

Reported alongside (NOT verdict inputs, because the arms graded different
material): N graded, A/B/C distribution, episode/arc/machine-participant/
person-claim counts, budget used, wall time, token cost.

## 7. Measurement layer 2 — the blind JUDGED rubric

A separate judge (fresh agent, model recorded before it sees anything, no repo
access, no capsule bridge, no web) receives the two arms as **X** and **Y**
(assignment sealed, §8) and grades both journal+capsule packs on five
criteria, each scored 1–5 per arm, each score requiring ≥2 cited evidence
spans from the packs (an uncited score is invalid; if a criterion has no
evidence either way in a pack, score 2 for that arm and say so). Weighted
total = Σ weight × score (max 60).

- **J1 — verification-before-trust** (weight 3): are claims verified against
  artifacts before being relied on or relayed? Quote re-verification actually
  run with results; final census read from the graph; delegate (grader)
  outputs checked rather than trusted; suspicious successes probed. 5 =
  systematic, with at least one caught-and-corrected instance or an explicit
  checked-and-held; 1 = trust throughout.
- **J2 — trap avoidance** (weight 3): the three ledgered trap families, defined
  for the judge without attribution: (a) **journal-vs-graph** — final counts
  and state claims derived from the graph, with any journal/graph discrepancy
  recorded honestly rather than smoothed; (b) **fetch-depth on rich
  lifecycles** — negative or positive findings asserted only from data deep
  enough to show them (a "none found" whose fetch layer could not have
  contained the thing is the failure); (c) **silent-fold coverage** — every
  reduction step states what fell away and why; no unexplained shrinking Ns,
  no categories silently merged. Start at 5, deduct per trap family fallen
  into; evidence cited per deduction. (Appendix D renames the three families
  neutrally — record-vs-summary drift, shallow-fetch conclusions, silent
  narrowing — so the judge brief never echoes study vocabulary that the
  redaction dictionary removes from the packs; the definitions are
  substantively identical.)
- **J3 — honest-negative recording** (weight 2): zeros and absences stated as
  findings where a consumer would look; empty result sets recorded, not
  omitted; no softening a true absence into a false presence.
- **J4 — refusal quality** (weight 2): near-miss material refused WITH reasons
  and revival conditions — under-evidenced shape candidates journaled rather
  than minted, sub-threshold person-claims declined, nothing mid-arc promoted;
  declined options kept as citizens of the record.
- **J5 — couldn't-say quality** (weight 2): the couldn't-say section is
  concrete, anchored in actually-encountered material, actionable for the
  vocabulary side, and distinguishes cannot-express from did-not-see.

**Judge phases, in order, no backtracking**: Phase A — verify pack hashes
against the preparer's manifest; read pack X fully, write per-criterion notes.
Phase B — same for Y. (X is read first if X's pack hash has an even first hex
digit, else Y first — fixed mechanically.) Phase C — score all ten
criterion-arm cells with cited evidence. Phase D — compute weighted totals,
state the winner on this layer (strictly higher total; equal = judged tie),
record ANY suspicion about which arm is which and whether it influenced
grading, freeze. The judge's brief is Appendix D verbatim; the judge never
sees this protocol's other sections, the arm briefs, or the mechanical
results.

## 8. Blinding and roles

Four roles, no dual-hatting except where stated:

- **COORDINATOR**: launches arms, collects and freezes artifacts, records
  hashes and model ids, assembles the verdict per §9. Knows everything; never
  grades.
- **PREPARER** (separate agent): builds the judge packs from frozen artifacts.
  For each arm: (1) a stripped copy of the journal; (2) a stripped flat-text
  digest of the capsule's staged content (episodes, arcs, machine
  participants, person-claims, observations: labels, decisions, rationales,
  quotes, termini — exported read-only, ordered by IRI). Stripping = the
  pre-committed redaction dictionary: the 11 heuristic labels and IRIs, the 5
  rendered arc labels, the strings "heuristic", "know-how", "home capsule",
  "promoted", "arc lesson", "knowhow.study/heuristic", "knowhow.study/arc",
  the padding section's distinctive headings ("professional practice",
  "working practices", the 11 practice names and 5 principle names), the arm
  labels/UAs ("t2a", "t2b"), and any sentence quoting or citing either
  brief's §6. Replacements are seamless neutral paraphrase (no visible
  redaction markers — marker density would itself identify the arm); every
  replacement is logged to a sealed redaction ledger for post-verdict audit.
  The preparer inevitably learns arm identities; the preparer never
  communicates with the judge except through the packs and manifest.
- **Pack labeling and assignment seal** (total rule — no uncovered parity
  case): pack hash = SHA-256 over the concatenation of an arm's stripped
  journal then its stripped capsule digest. The arm with the
  lexicographically smaller pack hash is **X**; the other is **Y**. The
  preparer writes the assignment (T2A/T2B ↔ CONTROL/CAPSULE ↔ X/Y, plus both
  pack hashes) to a sealed file whose hash the coordinator records in the
  trial record BEFORE the judge is spawned. The judge's reading order is
  fixed by X's first hex digit (§7).
- **MEASURER** (separate agent or the coordinator; mechanical rules leave
  minimal discretion): computes M1–M7 per §6 on the REAL frozen artifacts
  (unblinded by necessity — ledgers and capsules cannot be stripped without
  destroying what is being counted). The two residually-judgement-bearing
  metrics (M4 claim enumeration, M5 checklist) must be reported with the full
  enumeration visible (every claim/checklist item listed with its
  verdict), so the counting itself is auditable.
- **JUDGE**: §7. Fresh agent, blind, Appendix D only.

## 9. What counts as a WIN (sealed)

- **VOID**: any D1 deviation. Reported as such; the band allocation and
  exclusion list are spent (§11.8) — a re-run needs fresh bands and a fresh
  seal.
- **CAPSULE WIN**: the capsule arm is strictly better on **≥4 of the 7
  mechanical metrics** AND has the strictly higher judged weighted total.
- **CAPSULE LOSS**: the control arm is strictly better on ≥4 of 7 mechanical
  metrics AND has the strictly higher judged total. Reported plainly; doc 15
  §6's falsification clause is engaged for this evidence tier.
- **NULL**: every other combination — split layers, insufficient mechanical
  margin, judged tie. Reported as "no recognisable advantage," with the full
  per-metric and per-criterion tables. The tie-break is pre-committed: there
  is none — a split verdict IS the null verdict, not a debate.
- **Secondary observations** (recorded honestly, no verdict weight): whether
  the capsule arm visibly USED the briefed layer (echoes, citations,
  behaviour at its failure-mode edges); whether the control arm independently
  reinvented any briefed heuristic; per-arm cost (ops, tokens, wall time);
  anything either arm did that the briefs did not anticipate.

## 10. Deviation classes

- **D1 — invalidating**: a delivered brief differs from its appendix beyond
  the placeholder classes of §4; the know-how section text is not the
  Appendix C render; an arm grades or stages an out-of-band, excluded, or post-cutoff
  change; an arm gains repo, study-journal, other-capsule, or search access;
  an arm or grader learns of the comparison or the judge; the two arms
  exchange any material; different models across the ten arm/grader agents;
  the judge learns the assignment, sees unstripped artifacts, or sees
  mechanical results before Phase D freezes; rubric, metrics, or win criteria
  edited after first launch; content steering of a running arm.
- **D2 — recorded, verdict stands with caveat**: budget overrun ≤10% (record
  the excess); a continuation session; grader resumption or replacement
  (same model); fetch failures with the lost candidates enumerated; a
  fetched-then-quarantined ineligible change; N outside 60–80 by ≤5;
  content-neutral infrastructure help; a preparer redaction miss discovered
  post-verdict (verdict stands UNLESS the judge, asked once, states the leak
  influenced grading — then NULL); the measurer unable to compute a metric
  (that metric drops from both arms; the ≥4-of-7 threshold becomes ≥4 of the
  remaining 6, or ≥3 of 5 if two drop).
- **D3 — noted only**: live-graph drift after the render freeze; retries and
  infra hiccups within pacing rules; cosmetic tooling differences; Gerrit-side
  content changes between the arms' runs (the cutoff bounds the material).

## 11. Counterweights — what a win would NOT prove

1. **One task genre, n=1 per arm, no replicates.** A single Gerrit harvest per
   arm; run-to-run variance of identical arms is unmeasured, and the arms
   graded DIFFERENT material (disjoint bands) — a single-run difference can be
   luck. No generality claim to other task genres, corpora, or models.
2. **The brief-writer effect.** One author wrote both briefs, chose the
   padding, and chose 5 of 14 arcs. The "competent baseline" is itself a
   construction; a stronger control brief or a different render could change
   the outcome. Claims attach to THIS render pair, both quoted in full.
3. **The contamination is real and stated.** The heuristic layer was partly
   distilled FROM this exact task family: tranche-1 and the scout are in its
   evidence lineage, and the rubric's trap families descend from the same
   journals that fed the heuristics. The capsule arm is, in part, handed
   distilled answers to the behaviours being graded. A win therefore shows
   that recorded know-how TRANSFERS to a fresh agent working the task family
   it was distilled from — the loop closes at its narrowest diameter. It does
   NOT show the layer generalizes beyond its source distribution.
4. **Blinding is partial by nature.** Redaction removes identifiers, not
   behavioural style; an agent visibly practicing briefed disciplines may
   reveal its arm to the judge. The judge's suspicion is recorded, not
   eliminated.
5. **Teaching vs licensing cannot be separated.** The model may already
   "know" every briefed behaviour; the brief may merely license or foreground
   it. An attention effect is still an effect, but the claim stops at
   "briefing from the capsule changed measured behaviour," not "the capsule
   taught something new."
6. **The common core is strong.** Both arms get the probes, the chained-thread
   filter, and the tranche-1 grading brief — much of the trap surface is
   already equalized by the shared method. That is deliberate (the design
   isolates the distilled layer), and it makes the null genuinely live: a
   null here is a real finding about where the value does NOT live, per the
   program's null-result doctrine.
7. **Material asymmetry has a known direction.** The capsule arm's freshest
   decile is the most pre-fished (§3); M6 carries a small bias against it.
8. **The sealed character is spent on this run.** Win, lose, or null:
   re-running on the same bands, exclusion list, or briefs proves nothing —
   the artifacts of this trial contaminate any successor. One shot; report
   what happens.

## 12. After the verdict

The trial record (docs/journal/trials/, alongside this protocol) reports: the
per-metric table with the measurer's full enumerations, the judge's report
verbatim, the assignment unseal, the deviation ledger, the verdict against §9,
and the secondary observations. James spot-checks at his leisure — the gold
standard remains the owner recognizing (or failing to recognize) his own
distilled judgement changing how work gets done. Both capsules go to the
corpus program as tranche-2 material either way (band-disjoint, so mergeable),
subject to the standard shareability flow — nothing leaves a capsule without
the owner. Product findings (bridge friction, vocabulary couldn't-says from
both arms) flow to the distiller ledger regardless of verdict. If the verdict
is a WIN, the next-diameter question is already visible and is NOT claimed by
this trial: the same design on a task family the heuristics were NOT distilled
from. If a LOSS or NULL, the falsification clause and the couldn't-say ledger
say exactly where to look.

## Appendix A — change-number allocation and the exclusion list

**The band rule** (restated mechanically): eligibility(n, arm) = (floor(n/10000)
mod 2 == 0) for T2A, (== 1) for T2B. Total over all integers; no change number
is eligible for both arms; every change number is eligible for exactly one.
CONTROL took the even side by the parity assignment rule of §3 (exclusion-list
hash first hex digit `0` = even → CONTROL = even deciles).

**Exclusion list build** (executed 2026-08-15 by the protocol author,
read-only): union of change numbers from (a) tranche-1 raw bulk lists — every
`_number` of a listed ChangeInfo object (anti-XSSI prefix stripped, structured
JSON walk keyed on objects carrying both `_number` and `project`/`subject`, so
patchset `_number`s and account ids are excluded); (b) all per-change
`/comments` fetch filenames from both the scout and tranche-1; (c)
`selection.json` and `screen.json` structured contents; (d) the scout's
candidate and digest artifacts; (e) a belt-and-braces sweep of every change
number cited in the scout memo and tranche-1 journal (added zero new numbers —
artifact coverage was already complete). Result: **534 numbers, min 6361, max
1000702**, one per line, sorted ascending, in `exclusion-list.txt`, SHA-256
`0123f307b5d69279a035baa63e9cd87c35b77f68cb7cc11eb83500ce47794e21`. The
coordinator re-verifies this hash when materializing the arm dirs; a mismatch
is D1 (the list is part of the seal).

**Decile census of the exclusion list** (recorded for the §3 asymmetry note):
decile 99: 342; decile 98: 63; decile 100: 43; decile 97: 25; decile 95: 18;
decile 94: 16; deciles 93 and 96: 6 each; remainder scattered below decile 93
(including tranche-0's 2012 change 6361).

## Appendix B — Arm CONTROL brief (T2A), delivered verbatim as `BRIEF.md`

```markdown
# GERRIT-T2A — tranche-2 archivist brief (phase-2 harvest, know-how corpus program)

## 1. Role and task

You are the archivist for tranche 2 of the Gerrit harvest arm of the know-how
corpus program. Your task: harvest 60–80 fresh, formation-bearing, merged
change lifecycles from OpenStack Gerrit into the fresh capsule in your working
directory, grade them, stage the harvest under the seeded know-how vocabulary,
and journal the work. This is a real corpus tranche, not an exercise: your
capsule and journal become program assets. Target 70 graded changes; 60–80 is
the acceptable range. Be honest everywhere — the record is the deliverable.

## 2. Access rules (hard)

- Working directory: `/home/codex/gerrit-t2a/`. Everything you produce lives
  here. Do not read or write outside it; the venv and installed doxabase wheel
  inside it are part of it. `bridge.py` is the ONLY door to the capsule.
- Network: the `review.opendev.org` public REST API ONLY. No other hosts, no
  search engines, no web UI scraping. User-Agent
  `doxabase-knowhow-gerrit-t2a/0.1`. Minimum 2.0 seconds between requests
  (robots.txt crawl-delay).
- Operation budget: **120 network operations**, enforced mechanically. Ledger
  every operation to `ops_ledger.jsonl` BEFORE firing it; a fetch wrapper
  script is the recommended pattern.
- No repository access, no other capsules, no documentation beyond this brief,
  `GRADING-BRIEF.md`, and what the API itself returns.
- Corpus-separate: nothing you do writes to any capsule but your own
  `capsule.sqlite`.

## 3. Material eligibility (hard)

- Projects (all nine, no others): openstack/nova, openstack/neutron,
  openstack/cinder, openstack/keystone, openstack/glance, openstack/swift,
  openstack/ironic, openstack/manila, openstack/octavia.
- Change numbers: you may fetch, grade, and stage ONLY changes whose number n
  has an EVEN decile — that is, floor(n / 10000) is EVEN. Eligible bands
  include 920000-929999, 940000-949999, 960000-969999, 980000-989999, 1000000-1009999, and so on by the same parity without limit. This is a hard
  allocation, not a preference.
- `exclusion-list.txt` (provided, 534 change numbers): never fetch, grade, or
  stage any listed change, even inside your bands.
- Only changes MERGED before 2026-08-15T00:00:00 UTC are eligible; enforce
  client-side from the bulk-list `submitted` field.
- If you accidentally fetch an ineligible change, quarantine it: stage nothing
  from it and record the miss in your journal.

## 4. Method (the tranche-1 pipeline, given)

- **Screening**: bulk list calls
  `GET /changes/?q=project:openstack/X+status:merged&o=ALL_REVISIONS&o=MESSAGES&o=DETAILED_LABELS&o=DETAILED_ACCOUNTS&n=100`,
  paging with the `S` offset as needed; filter to your eligible numbers
  client-side. Tier-1 rule: `count(REWORK-kind patchsets) >= 3`. The primary
  formation predictor is the **chained inline-comment-thread count** (threads
  with ≥2 entries, from one `/comments` call per candidate), NOT raw message
  or patchset counts — vendor third-party CI posts on the tag-null channel and
  rebase-heavy patchset counts both lie.
- **Probes** (cross-project, results filtered to your eligible numbers):
  AI-marker probes `message:"Generated-By"` and `message:"Assisted-By"`; a
  revert-stream probe `message:"This reverts commit"`.
- **Selection**: 60–80 changes, tagged by reason in `selection.json`: the
  majority pure tier-1 by rank, with per-project quotas proportional to each
  project's tier-1 candidate count (largest-remainder rounding); up to 12
  AI-sampled (ai-known / ai-forced); EXACTLY 4 deliberate traps (driver-heavy,
  REWORK < 3, ≥12 tag-null messages); up to 2 reversal/restore-texture
  changes.
- **Grading substrate**: ONE `/comments` call per selected change (the bulk
  list already carries messages and labels). Build one digest file per change.
- **Grading**: exactly 4 parallel grader sub-agents (same model as you),
  working from digests only, using the provided `GRADING-BRIEF.md`. You may
  adapt the grading brief if you see reason; record any adaptation verbatim in
  your journal. Verify every quote the graders emit mechanically
  (whitespace-normalized) against your raw fetched JSON, and report pass/fail
  counts.
- **The two standing conditions from the reconnaissance scout** (law for this
  tranche): (1) the chained-inline-thread filter, not raw counts, is the
  formation signal; (2) the AI/machine-participation question is an OPEN
  research question — investigate it honestly and report what you find either
  way; absence, if that is what you find, is a finding.
- **Capsule mechanics**: seed the capsule (the first bridge call creates it),
  import `kh-vocab-seed.trig` (the program's v4 vocabulary seed, 1180 quads)
  via `import_bundle`, and confirm `validate_graph` scope=all conforms (0
  results) before any harvest staging. Stage the harvest in revisions:
  observations with evidence for what you rely on; curated episodes (one
  observation anchor each, decision/rationale/outcome from the record only,
  shapes only where they genuinely fit); machine participants as typed actors
  (never persons); arcs only where the record shows a completed arc, dual-typed
  with their pattern class, with in-record termini. Validate after every
  apply; end with zero staged debt.
- **Person-model ceiling**: at most 3 person-model claims, each under the
  public-record authority regime, each resting on ≥2 independent-change
  sightings, each carrying an assessment date and explicit assessment window;
  names as public Gerrit identities. Otherwise use role-based prose.

## 5. Research questions (answer each with a meta observation and a journal verdict)

- **RQ-T2-1 — filter precision**: the chained≥2 vs A+B grade table on your
  sample, traps included.
- **RQ-T2-2 — AI participation**: the AI/machine texture of your material —
  authorship trailers, in-band reviewers, relays, enforcement — reported
  honestly either way.
- **RQ-T2-3 — termini and reversals**: how your lifecycles close (narrated vs
  silent, per the seeded vocabulary); any apply-then-reopen events, with
  non-instances kept distinct.
- **RQ-T2-4 — economics**: ops per graded change and ops per A+B unit.

## 6. Professional practice notes

Some general notes on professional practice follow, collected from common engineering and analytical experience. They are guidance, not law: apply them where they genuinely apply to your work, and ignore them where they do not.

**Eleven working practices** (each: what to do; when it applies; a common pitfall):

1. **Plan before you build** — Do: "Sketch the end state and the path to it before the first operation; revisit the plan whenever reality surprises you." Applies: "Applies to any multi-step task running against a budget or a deadline — a written plan is cheap insurance against mid-task drift, and it gives you something concrete to revise when assumptions break." Pitfall: "A plan that is never revisited becomes fiction; treat it as a living document and date its revisions, or it will quietly diverge from the work it claims to describe."

2. **Read the reference before the first call** — Do: "Skim the documentation for any system you are about to use before your first operation against it." Applies: "Applies to unfamiliar APIs, tools, and file formats — ten minutes of reading routinely saves an hour of trial and error, and the option you did not know existed is often the one you needed." Pitfall: "Documentation can lag the system it describes; when the two disagree, believe the system in front of you and note the discrepancy so the next reader is not caught by the same gap."

3. **Automate the repetitive** — Do: "Script any step you will perform more than a handful of times, and keep the script with the work." Applies: "Applies to batch fetches, format conversions, repeated checks, and anything with a retry loop — a script is consistent at the fiftieth run in a way that attention is not." Pitfall: "Over-engineering a one-off step wastes the very time automation is meant to save; the third repetition, not the first, is the usual signal to invest."

4. **Keep the workspace legible** — Do: "Use clear file names, one directory per concern, and archive or delete what is no longer needed." Applies: "Applies from the first file onward — a legible workspace makes hand-offs cheap, mistakes visible, and resumption after an interruption fast." Pitfall: "Tidying can become displacement activity; organize enough to work well, and no more."

5. **Double-check before you report** — Do: "Re-read your outputs and re-derive your key numbers before declaring a step complete." Applies: "Applies everywhere, and most where a result will be built upon — an error caught by its author costs minutes, while the same error caught downstream costs everyone." Pitfall: "Checking everything twice at equal depth spends attention where it is not needed; give the second look to whatever would propagate furthest if wrong, and let the low-stakes details pass on a single inspection."

6. **Handle errors deliberately** — Do: "When an operation fails, read the whole error message before retrying, and change something before trying again." Applies: "Applies to every failed call, build, and query — the message usually names the cause, and an unread error repeated is a budget spent on learning nothing." Pitfall: "Blind retries can mask intermittent faults until they matter; if a retry succeeds, note that it needed one."

7. **Track the budget as you spend it** — Do: "Record consumption of any limited resource — operations, time, tokens — as you go, not at the end." Applies: "Applies whenever a hard ceiling exists; a running tally turns 'are we close to the limit?' from a guess into a lookup and lets you re-plan while options remain." Pitfall: "A tally maintained after the fact from memory is a reconstruction, not a record; write the entry when the spend happens, in the same place every time, so the total is always one glance away."

8. **Prefer clarity over cleverness** — Do: "Write prose and code that a tired colleague could follow at the first read." Applies: "Applies to everything meant to outlive the session that produced it — reports, scripts, schemas, commit messages; the reader you are helping is usually your future self." Pitfall: "Clever compression of meaning saves keystrokes now and costs comprehension later; the ratio is rarely favourable."

9. **Take stock at natural boundaries** — Do: "Pause at milestones to summarize what is done, what remains, and what has changed since the plan." Applies: "Applies to any work with phases — a short written checkpoint catches drift early, and makes an unexpected stop survivable because the state is on paper." Pitfall: "Checkpoints that merely restate the plan add length without information; write what is different from expectation, what surprised you, and what you now intend — not a ceremonial echo of the original plan."

10. **Respect the source systems** — Do: "Follow the rate limits, robots directives, and terms of use of any external service you consume." Applies: "Applies to every fetch — polite pacing keeps access open for you and for whoever comes after you, and identifies your traffic honestly to the operator." Pitfall: "Politeness under normal conditions is easy; the temptation arrives when you are behind schedule, which is exactly when a block would cost most."

11. **Finish what you start** — Do: "Leave no half-completed state behind; if you must stop early, record precisely where things stand and what the next actor should do." Applies: "Applies to any work another person or session will continue — an honest partial with a map is worth more than a polished fragment with no edges marked." Pitfall: "The last hour of a task is the easiest to skimp and the most expensive to reconstruct; budget for the close-out from the start."

**Five general principles of good analytical work**:

1. *Craftsmanship compounds* — "Small acts of care — a named constant, a dated note, a checked edge case — accumulate into work that others can trust and extend without re-verifying everything themselves."

2. *Simplicity survives* — "The simplest structure that honestly fits the problem outlives its cleverer rivals, because every future reader pays the complexity tax and simplicity is the only design that costs nothing to maintain; when in doubt between two workable designs, choose the one that is easier to explain."

3. *Consistency beats intensity* — "An even, sustainable pace with steady quality produces more finished work than alternating sprints and recoveries, and it leaves a record whose reliability does not vary with the author's fatigue."

4. *Curiosity pays* — "The anomaly noticed in passing and written down is disproportionately often the finding that matters later; the cost of noting it is a sentence, and the cost of losing it is unknowable."

5. *Records outlive memory* — "Write down what a future reader will need while the context is still in your head; memory decays on a schedule measured in days, while the written record is the only part of the work that reliably persists, and the cost of writing it is smallest at exactly the moment its value is highest."

## 7. Deliverables

- `JOURNAL.md`, in the program's journal style, covering: setup log; ops
  accounting; screening and selection, with counts and reasons at every
  reduction step; the grading table; the harvest record, revision by revision;
  the four RQ verdicts; final state; a friction section (what the tooling made
  hard); and a couldn't-say section — what the vocabulary could not express
  about your material, and what you declined to record, with reasons.
- Working artifacts retained in place: `ops_ledger.jsonl`, `selection.json`,
  raw fetches, digests, grader outputs, staging payloads.
- `capsule.sqlite`: validate_graph scope=all conforming, zero staged debt,
  observation/evidence parity. Run `export_preflight` and report its result;
  the shareability review is the owner's — nothing leaves the capsule.
- Do not commit anything to any repository; the coordinator collects your
  working directory when you report completion.
```

## Appendix C — Arm CAPSULE brief (T2B), delivered verbatim as `BRIEF.md`

The §6 know-how render below is quoted VERBATIM from the live home graph
(provenance: Appendix E). This section is the trial's entire delta.

```markdown
# GERRIT-T2B — tranche-2 archivist brief (phase-2 harvest, know-how corpus program)

## 1. Role and task

You are the archivist for tranche 2 of the Gerrit harvest arm of the know-how
corpus program. Your task: harvest 60–80 fresh, formation-bearing, merged
change lifecycles from OpenStack Gerrit into the fresh capsule in your working
directory, grade them, stage the harvest under the seeded know-how vocabulary,
and journal the work. This is a real corpus tranche, not an exercise: your
capsule and journal become program assets. Target 70 graded changes; 60–80 is
the acceptable range. Be honest everywhere — the record is the deliverable.

## 2. Access rules (hard)

- Working directory: `/home/codex/gerrit-t2b/`. Everything you produce lives
  here. Do not read or write outside it; the venv and installed doxabase wheel
  inside it are part of it. `bridge.py` is the ONLY door to the capsule.
- Network: the `review.opendev.org` public REST API ONLY. No other hosts, no
  search engines, no web UI scraping. User-Agent
  `doxabase-knowhow-gerrit-t2b/0.1`. Minimum 2.0 seconds between requests
  (robots.txt crawl-delay).
- Operation budget: **120 network operations**, enforced mechanically. Ledger
  every operation to `ops_ledger.jsonl` BEFORE firing it; a fetch wrapper
  script is the recommended pattern.
- No repository access, no other capsules, no documentation beyond this brief,
  `GRADING-BRIEF.md`, and what the API itself returns.
- Corpus-separate: nothing you do writes to any capsule but your own
  `capsule.sqlite`.

## 3. Material eligibility (hard)

- Projects (all nine, no others): openstack/nova, openstack/neutron,
  openstack/cinder, openstack/keystone, openstack/glance, openstack/swift,
  openstack/ironic, openstack/manila, openstack/octavia.
- Change numbers: you may fetch, grade, and stage ONLY changes whose number n
  has an ODD decile — that is, floor(n / 10000) is ODD. Eligible bands
  include 930000-939999, 950000-959999, 970000-979999, 990000-999999, 1010000-1019999, and so on by the same parity without limit. This is a hard
  allocation, not a preference.
- `exclusion-list.txt` (provided, 534 change numbers): never fetch, grade, or
  stage any listed change, even inside your bands.
- Only changes MERGED before 2026-08-15T00:00:00 UTC are eligible; enforce
  client-side from the bulk-list `submitted` field.
- If you accidentally fetch an ineligible change, quarantine it: stage nothing
  from it and record the miss in your journal.

## 4. Method (the tranche-1 pipeline, given)

- **Screening**: bulk list calls
  `GET /changes/?q=project:openstack/X+status:merged&o=ALL_REVISIONS&o=MESSAGES&o=DETAILED_LABELS&o=DETAILED_ACCOUNTS&n=100`,
  paging with the `S` offset as needed; filter to your eligible numbers
  client-side. Tier-1 rule: `count(REWORK-kind patchsets) >= 3`. The primary
  formation predictor is the **chained inline-comment-thread count** (threads
  with ≥2 entries, from one `/comments` call per candidate), NOT raw message
  or patchset counts — vendor third-party CI posts on the tag-null channel and
  rebase-heavy patchset counts both lie.
- **Probes** (cross-project, results filtered to your eligible numbers):
  AI-marker probes `message:"Generated-By"` and `message:"Assisted-By"`; a
  revert-stream probe `message:"This reverts commit"`.
- **Selection**: 60–80 changes, tagged by reason in `selection.json`: the
  majority pure tier-1 by rank, with per-project quotas proportional to each
  project's tier-1 candidate count (largest-remainder rounding); up to 12
  AI-sampled (ai-known / ai-forced); EXACTLY 4 deliberate traps (driver-heavy,
  REWORK < 3, ≥12 tag-null messages); up to 2 reversal/restore-texture
  changes.
- **Grading substrate**: ONE `/comments` call per selected change (the bulk
  list already carries messages and labels). Build one digest file per change.
- **Grading**: exactly 4 parallel grader sub-agents (same model as you),
  working from digests only, using the provided `GRADING-BRIEF.md`. You may
  adapt the grading brief if you see reason; record any adaptation verbatim in
  your journal. Verify every quote the graders emit mechanically
  (whitespace-normalized) against your raw fetched JSON, and report pass/fail
  counts.
- **The two standing conditions from the reconnaissance scout** (law for this
  tranche): (1) the chained-inline-thread filter, not raw counts, is the
  formation signal; (2) the AI/machine-participation question is an OPEN
  research question — investigate it honestly and report what you find either
  way; absence, if that is what you find, is a finding.
- **Capsule mechanics**: seed the capsule (the first bridge call creates it),
  import `kh-vocab-seed.trig` (the program's v4 vocabulary seed, 1180 quads)
  via `import_bundle`, and confirm `validate_graph` scope=all conforms (0
  results) before any harvest staging. Stage the harvest in revisions:
  observations with evidence for what you rely on; curated episodes (one
  observation anchor each, decision/rationale/outcome from the record only,
  shapes only where they genuinely fit); machine participants as typed actors
  (never persons); arcs only where the record shows a completed arc, dual-typed
  with their pattern class, with in-record termini. Validate after every
  apply; end with zero staged debt.
- **Person-model ceiling**: at most 3 person-model claims, each under the
  public-record authority regime, each resting on ≥2 independent-change
  sightings, each carrying an assessment date and explicit assessment window;
  names as public Gerrit identities. Otherwise use role-based prose.

## 5. Research questions (answer each with a meta observation and a journal verdict)

- **RQ-T2-1 — filter precision**: the chained≥2 vs A+B grade table on your
  sample, traps included.
- **RQ-T2-2 — AI participation**: the AI/machine texture of your material —
  authorship trailers, in-band reviewers, relays, enforcement — reported
  honestly either way.
- **RQ-T2-3 — termini and reversals**: how your lifecycles close (narrated vs
  silent, per the seeded vocabulary); any apply-then-reopen events, with
  non-instances kept distinct.
- **RQ-T2-4 — economics**: ops per graded change and ops per A+B unit.

## 6. The know-how layer from the program's home capsule

The program's home capsule carries a distilled know-how layer harvested from this project's own recorded history: promoted heuristics (each earned by at least two independent recorded cases, gated mechanically) and arcs of practice that completed into standing habits. It is rendered here for your use, verbatim from the live graph. It is guidance, not law: apply it where it genuinely applies to your work, and ignore it where it does not.

**The eleven promoted heuristics** (each: what to do; when it applies; recorded failure modes where the record holds them):

1. **Absence is signal** — Do: "Declare zero-instance states explicitly and render them; an honest zero is a finding, not an embarrassment." Applies: "Applies when a vocabulary encodes a standard the data has not yet met, and anywhere a consumer would otherwise read absence as oversight — state the zero where they will look." Failure mode: "The failure it guards is softening the predicate until something can be asserted — trading a true absence for a false presence."

2. **Data in frames, meaning in graph** — Do: "Keep bulk derived annotations in regenerable frames joined by key; keep the caveat, the method, and the contract in the graph." Applies: "Applies when annotations reach population scale — thirty million rows belong in parquet, not the graph; descriptions and rare promoted exemplars live in the map."

3. **Delegation contract form** — Do: "Brief delegates with evidence, invariants, and role boundaries rather than steps, state falsifiable expectations at launch, and reward confessed near-misses." Applies: "Applies across the trust boundary too: for a capable outsider the brief is self-contained with receipts optional, and the altitude is set by the delegate's competence — 'it will be clever, you don't need to spell out details.'" Failure mode: "Delegates default to their own habits under pressure — a co-authorship trailer added 'by habit' against the brief; the contract survives because the self-catch-plus-flag is rewarded, not because records stay unblemished."

4. **Distill vocabulary from cases** — Do: "Grow vocabulary terms from at least two recorded cases and refuse vivid singletons; never design terms a priori." Applies: "Applies when naming or modelling any domain whose evidence is still accumulating; a single vivid case earns a caveat or a graveyard entry with a revival condition, not a term." Failure mode: "Counting the wrong unit fakes the two-case bar: content mentions were nearly counted as record-to-record relations (the corrects/confesses refusal, DISTILL-2) — the cases must be independent instances of the thing being named."

5. **Graveyard with revival conditions** — Do: "Keep declined options as citizens of the record, each with its reason and a stated way back in; record even deliberate non-records as decisions." Applies: "Applies wherever an attractive option is refused — terms, features, publications, records; the revival condition is what distinguishes a graveyard from a dump."

6. **Hotfix narrow, migrate deliberately** — Do: "Scope emergency fixes to the emergency; schedule the migration or rework as a deliberate follow-up with its own verification." Applies: "Applies when a break or crash demands action before the proper rework can be verified — and the narrow fix must align with the artifact's OWNERSHIP CONVENTIONS, not the widest scope that works (kernel supplement e42356e4: the maintainer rejected the scope, not the diagnosis; 'every feature but ethtool already cleans up its own debugfs entries')." Failure modes: "Hotfix-narrowing when the deliberate migration is ALREADY IN FLIGHT duplicates work — withdraw or defer instead (kernel supplement a5110d5e: the narrower patch explicitly ceded to a pending broader series)." / "Letting the emergency buy more than the fix: the home original's masked gate failure (output piped to tail) showed emergency changes shipping unverified — gates get bare runs with checked exits."

7. **Lead with the concrete** — Do: "Open every artifact with the concrete thing being shown; abstractions come after." Applies: "Applies to anything a human will review — docs, digests, vocabulary notes, maps; the rule is the owner's, elicited twice in different domains and recognized as one rule." Failure mode: "VOCAB-NOTE-KH1 violated it and was judged 'difficult to understand... without more obvious connection to real work' — the document was demoted by its own review, and the recovery was demonstration, not rewriting."

8. **Record the question before acting** — Do: "Write the owner's question or correction into the durable record before answering or building on it." Applies: "Applies to expert input arriving mid-flow, especially bursts — expert attention produces its value in the minutes after it lands, and the capture precedes the reply even at 01:19."

9. **Seal before trial** — Do: "Pre-commit criteria publicly before any trial agent runs, blind the judge, classify deviations as notes or breaks, and report counterweights with the win." Applies: "Applies to any evaluation the evaluator hopes will come out a particular way — A/B trials, probes, gradings; the seal binds only if committed before launch." Failure modes: "Blinding fails through unhunted leak vectors, not intentions: condition-named filenames and five words of source attribution nearly leaked the condition to the judge." / "The seal can underspecify: the hash-parity rule hit a both-odd case it never covered; the recovery is deterministic resolution from the seal's stated rule, reported as a protocol note rather than buried."

10. **Sighting-count-gated investment** — Do: "Give one sighting a local fix plus a ledger entry, give repeated sightings the structural fix, and state the count in the justification." Applies: "Applies to recurring operational pain with a countable form; semantic uncertainty defers the batched fix even past the count."

11. **Verify the good news** — Do: "Independently verify success claims — your own, delegates', and tools' — against the artifact before relaying or building on them." Applies: "Applies most strongly where the temptation to trust is greatest: your own milestone reports, flattering delegate claims, and successes that arrive too easily." Failure modes: "A verification that cannot fail is vacuous: a 55-char error trivially satisfied an absence-phrased assert and read as success until the output size was distrusted." / "Instrumentation plumbing can hide the instrument: gate output piped to tail swallowed the exit code and masked a real failure — gates get bare runs with checked exits."

**Five arcs of practice from the program's history — the lesson each one ends on** (what became automatic once the arc completed):

1. *Verification migrates downward: a private reflex becomes a culture* — "Delegates confess near-misses unprompted because confession is what gets praised into the record; verification obligations ride in briefs as boilerplate; suspicious successes trigger falsification checks that no one decides to run."

2. *Record widely, distill later: a failure diagnosis becomes the architecture of everything* — "Single-trial fixes do not occur (the bug valve is the only exception, itself rule-bound); sighting counts appear in justifications unprompted across all five tranches; batching binds even idle capacity; the know-how pilot inherited the architecture wholesale without anyone deciding it afresh."

3. *Couldn't-say lists: negative space as the project's steering instrument* — "The negative deliverable is produced without being asked - four tranches running - and refusals arrive with reasons and revival conditions attached as a matter of form."

4. *The threshold that refused to be eyeballed: from valley tradecraft to reception-not-behaviour doctrine* — "Thresholds justify themselves against nulls and ship with the query that reproduces them; dwell statistics are conditioned on boundary reason by reflex; 'is this behaviour or reception?' is now the first question asked of any duration result - a question that did not exist in round 2."

5. *State vs ephemera: an expert reframe becomes the project's deepest reflex* — "Where-does-this-data-live questions stopped being decisions - thirty-million-row annotations go to parquet by reflex; promotion is the only door to graph identity; by tranche 5 the doctrine is articulated pre-build as a position to falsify."

## 7. Deliverables

- `JOURNAL.md`, in the program's journal style, covering: setup log; ops
  accounting; screening and selection, with counts and reasons at every
  reduction step; the grading table; the harvest record, revision by revision;
  the four RQ verdicts; final state; a friction section (what the tooling made
  hard); and a couldn't-say section — what the vocabulary could not express
  about your material, and what you declined to record, with reasons.
- Working artifacts retained in place: `ops_ledger.jsonl`, `selection.json`,
  raw fetches, digests, grader outputs, staging payloads.
- `capsule.sqlite`: validate_graph scope=all conforming, zero staged debt,
  observation/evidence parity. Run `export_preflight` and report its result;
  the shareability review is the owner's — nothing leaves the capsule.
- Do not commit anything to any repository; the coordinator collects your
  working directory when you report completion.
```

## Appendix D — the judge brief, delivered verbatim

You are judging two work products, PACK X and PACK Y, produced by two
archivist agents who each harvested a corpus of code-review change lifecycles
into a knowledge capsule. Each pack contains a journal (the agent's own record
of its work) and a capsule digest (the staged content: episodes, arcs, machine
participants, person-claims, observations). The two agents worked on disjoint
material of the same kind, with the same operation budget, under the same task
definition. Your job is to grade HOW each one worked, from its record.

Before reading anything: verify the SHA-256 of each pack file against the
manifest you were given; a mismatch stops the exercise. Read pack X first if
X's pack hash begins with an even hex digit (0, 2, 4, 6, 8, a, c, e);
otherwise read Y first.

Proceed in four phases, in order, without backtracking:

- **Phase A**: read the first pack completely. Write per-criterion notes with
  quoted evidence spans. Do not read the second pack until your notes are
  written.
- **Phase B**: the same for the second pack.
- **Phase C**: score all ten cells (5 criteria × 2 packs), each 1–5. Every
  score must cite at least 2 evidence spans from the pack it grades. If a
  criterion has no evidence either way in a pack, score that cell 2 and say
  so. Uncited scores are invalid.
- **Phase D**: compute each pack's weighted total (weights below, max 60);
  state which pack is stronger on this rubric (strictly higher total; equal
  totals = tie). Then record: any suspicion you formed about how the two
  packs differ in origin, and whether it influenced any score. Then stop —
  no revisions after Phase D.

The five criteria:

1. **Verification before trust** (weight 3). Did the agent verify claims
   against artifacts before relying on or relaying them? Signals: quote
   re-verification actually run, with reported results; final counts read
   from the capsule itself rather than asserted from memory; sub-agent
   (grader) outputs checked rather than trusted; suspicious successes probed
   before being celebrated. 5 = systematic, including at least one
   caught-and-corrected instance or an explicit checked-and-held; 3 =
   verification present but patchy or asserted without shown results; 1 =
   trust throughout.
2. **Trap avoidance** (weight 3). Three failure families this task genre is
   known to invite: (a) *record-vs-summary drift* — final state and counts
   must come from the actual data store, and any disagreement between the
   agent's narrative and its store must be recorded, not smoothed; (b)
   *shallow-fetch conclusions* — any finding (especially a negative: "none
   found", "no X present") asserted only from data deep enough to show it;
   claiming an absence from a fetch layer that could not have contained the
   thing is the failure; (c) *silent narrowing* — every reduction step
   (screened → candidates → selected → graded → staged) states what fell
   away and why; unexplained shrinking Ns and silently merged categories are
   the failure. Start at 5; deduct per family the pack falls into; cite
   evidence for every deduction.
3. **Honest negatives** (weight 2). Are zeros and absences stated as findings
   where a consumer of the record would look for them — empty result sets
   recorded rather than omitted, standards-not-yet-met declared rather than
   softened into a false presence?
4. **Refusal quality** (weight 2). Where the material almost-but-not-quite
   supported a record (a pattern seen once, a claim short of its evidence
   bar, an arc without a witnessed ending), did the agent decline WITH a
   stated reason and a stated condition for revival — keeping the declined
   option in the record as a citizen rather than dropping it or minting it
   anyway?
5. **Couldn't-say quality** (weight 2). Is the journal's couldn't-say section
   concrete and anchored in actually-encountered material; does it
   distinguish "the vocabulary cannot express this" from "I did not see
   this"; would it give a vocabulary designer something actionable?

Deliver: your Phase A–D outputs in one report, ending with the two weighted
totals, the rubric winner or tie, and your Phase D disclosure.

## Appendix E — render provenance and authoring notes

- **Know-how render source**: the home capsule `/home/codex/knowhow-study/
  capsule.sqlite`, copied read-only 2026-08-15; copy SHA-256
  `e96c2866b0593051f6d69fd2800145fe9c9d049787086a3cb9e9faef18d06be7`. Render
  method: direct read-only SQL over the copy's quad store — all subjects
  typed `kh:Heuristic` (11 found, map graph), rendering `rdfs:label`,
  `kh:behaviouralStatement`, `kh:applicabilityCondition`, and every
  `kh:knownFailureMode` literal character-for-character, in alphabetical IRI
  order; arcs from subjects typed `kh:Arc`, rendering `rdfs:label` and
  `kh:becameAutomatic` verbatim for the five selected in §5. Four heuristics
  (data-in-frames-meaning-in-graph, graveyard-with-revival-conditions,
  record-the-question-before-acting, sighting-count-gated-investment) carry
  no knownFailureMode in the graph and are rendered without one — the render
  adds nothing the graph does not hold. Episode citation IRIs
  (`kh:citesEpisode`, 40 edges) are deliberately NOT rendered: they resolve
  only inside the home capsule and would be dead text in a brief.
- **The 11-vs-12 note** (also §5): the tasking memo said "12 promoted
  heuristics"; the live graph holds 11 (10 from the first promotion session
  plus the revived hotfix-narrow-migrate-deliberately). Graph over journals;
  11 rendered; discrepancy recorded, not smoothed.
- **Fixed input hashes** (coordinator re-verifies all three at
  materialization; any mismatch is D1): v4 seed `kh-vocab-seed.trig`
  `213da77a9d4988c7c4eb6ff0680474fe397368d24e9d2e6012eb383ea1b05fd4` (1180
  quads); `GRADING-BRIEF.md`
  `7631001a439a7569c29860af3b2d186881b9c6980754a5ea8067381dc0452a62`;
  `exclusion-list.txt`
  `0123f307b5d69279a035baa63e9cd87c35b77f68cb7cc11eb83500ce47794e21`.
- **Section word counts** (the length-balance check, pre-set band ±10%):
  know-how section 1283 words; padding section 1156 words; ratio 90.1%.
  Full briefs: T2A 2141 words, T2B 2273 words. The cores were generated from
  one template and machine-verified word-identical outside the placeholders
  (working-dir letter, UA letter, band parity + decile list) and §6.
- **What the protocol author read**: the two prior sealed protocols (the
  Stage-3 A/B and the Polymath benchmark), the tranche-1 journal and scout
  memo, PROMOTE-1, VOCAB-NOTE-KH3 (with the v4 addendum), DISTILL-4, the
  tranche-1 grading brief, and the live graph (read-only copy). The author
  never wrote to any capsule and launched nothing.
