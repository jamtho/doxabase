# Live-Retrieval Trial — the Sealed Static-vs-Live Assembly Protocol (ENRON-2)

**Committed BEFORE any trial agent runs** (doc 15 §4's pre-commitment requirement;
the seal-before-trial heuristic applied, as always, to the trial that tests the
program). **Date**: 2026-08-16. **Author**: the live-retrieval-trial protocol
author, on doc 17 §5's mandate (the falsification test for the capsule-as-
long-term-memory design). This file is the seal: the task, the custodian and
window allocation with its census, both arm briefs (verbatim, as appendices,
the static arm's assembly render embedded), the mechanical metrics, the NEW
retrieval metrics, the judged rubric, the blinding mechanics, the deviation
classes, and what counts as a win are fixed here. Nothing may be adjusted after
the first arm launches; any deviation must be reported under the classes in
§11. The coordinator records this file's SHA-256 in the trial record at launch,
before either arm runs.

## 1. The trial in one paragraph

The consumption trial tested whether briefing a working agent FROM the know-how
capsule changes how it works, on the task family the heuristics were distilled
from; its verdict was a null with a pointed signal. This trial closes that
protocol's narrowest-diameter caveat and tests doc 17's central design claim at
the same time: **does consulting the capsule MID-TASK (via the v0 budgeted
working-memory assembler) beat receiving the same assembly statically at
briefing time**, on a task family the promoted heuristics were NOT distilled
from? Two cold agents perform structurally identical instances of a real corpus
task — the second foreign-corpus email harvest, in the Kay Mann pilot's method,
each on its own pre-allocated, disjoint six-month window of ONE custodian
(Jeff Dasovich, dasovich-j), each into its own fresh v4-seeded capsule. The
STATIC arm's brief embeds, verbatim, a one-shot v0 assembly run at
protocol-authoring time against the home capsule (budget ~1500 tokens,
provenance=handles). The LIVE arm gets the identical brief WITHOUT the render;
instead its working directory holds the v0 assembler and a read-only frozen
copy of the home capsule, with license to consult mid-task under the same total
token budget, every consultation ledgered. The delta between the arms is ONLY
when and by whose question the capsule is assembled — not whether, not how
much. Measurement is three-layer: MECHANICAL (adapted from the consumption
trial's M-metrics), BLIND-JUDGED (the J1–J5 rubric, arm-identifying content
stripped including all assembler traces), and — new and central — RETRIEVAL
(consultation count, per-consultation precision, recall gap; the render's usage
rate on the static side, measured the same way). The null hypothesis is honest
and live, and doc 17 pre-states its meaning: "a null here would say the
assembly can be done as well statically at briefing time — also worth knowing,
and cheaper." Both arms' harvests are real phase-2 corpus material either way —
the trial rides on work the program wanted done regardless.

## 2. Design summary

| | Arm E2S (STATIC) | Arm E2L (LIVE) |
|---|---|---|
| Task | dasovich-j window harvest, 18–30 episodes, pilot's six conditions | identical |
| Material | **W1**: 2001-01-01 → 2001-07-01 (§3) | **W2**: 2001-07-01 → 2002-01-01 (§3) |
| Capsule | fresh, v4-seeded (1180 quads) | identical (own copy) |
| Home-capsule access | one 1500-token v0 render, embedded in brief §6, run 2026-08-16 | v0 assembler + frozen home-capsule copy; ≤1500 tokens total across ≤8 ledgered mid-task consultations |
| Provenance mode | handles (fixed this run) | handles (fixed this run) |
| Corpus surface | window-slice.parquet (materialized; no network, no credentials) | identical (own window) |
| Model / sessions | recorded model, 1 session (+1 continuation = D2) | identical |
| Told of comparison | no | no |

The delta between Appendix B and Appendix C is confined to §6 of each brief
plus the mechanical placeholder classes (working-dir name, window dates).
Everything else is word-identical, machine-verified from one template.
Provenance mode is a trial parameter by design (doc 17 §3); **this run fixes it
at `handles` for both arms — the digest-vs-handles-vs-full comparison is a
FUTURE trial, explicitly not this one.**

## 3. Material allocation — custodian, windows, and the contamination contract

**One custodian, two disjoint time windows — chosen over two custodians, and
here is why.** Custodian identity is the largest single material confounder
available in this corpus: the census below shows the two scouted candidates
differ enormously in forwarding habits (Kaminski's authored mail runs 48–86%
forward-marked depending on half-year; Dasovich 29–57%), in genre (research
management vs regulatory affairs), and in volume shape. Two windows of one
person hold genre, role, register, correspondent network, and personal-content
profile constant; the remaining within-person drift is measured and recorded
below. Contiguous windows also preserve thread integrity — interleaved slices
(the Gerrit protocol's decile trick) would cut email threads mid-arc, and
thread integrity is precisely what episode/arc harvest needs.

**The census** (author, 2026-08-16, read-only DuckDB over
`s3://enron-emails/eml_messages.parquet`, credentials env-held and never
echoed; 5 data-bearing queries of the ≤10 budget, plus 1 client-side parser
error that never executed; scripts and result JSONs retained in the trial
working dir — full tables in Appendix A):

- Candidate custodians (scout-designated): **kaminski-v** and **dasovich-j**.
- Authored-name resolution (Q1): kaminski-v = 'Vince J Kaminski' +
  'Kaminski, Vince J' (+ 'Vince Kaminski'); dasovich-j = 'Jeff Dasovich'
  (+ 'Dasovich, Jeff').
- Deduped authored half-year volumes (Q2, dedup = (subject, date, md5(body))):
  dasovich-j 2001-H1 **2,167** / 2001-H2 **1,860**; kaminski-v 2001-H1 1,749 /
  2001-H2 918. Kaminski's 2001-H2 forward-marked share hits 86% — his windows
  are not comparable to each other; Dasovich's are.
- Monthly resolution with own-prose proxy (Q3, >40 chars before the first
  forward marker): W1 own-prose **1,509**, formation-phrase hits **49**; W2
  own-prose **1,398**, formation hits **52**. The own-prose difference is
  7.6%; formation-hit difference 6%. This is the balanced pair.
- Exclusion-list collisions (Q4): **zero** excluded doc_ids present in either
  window (see below).
- Snapshot sizes (Q5, all custodian rows, pre-committed for materialization
  verification): **W1 = 28,108 rows (27,377 with bodies); W2 = 8,942 rows
  (8,077 with bodies)**.

**The allocation**:

- **W1** = dasovich-j, `date >= 2001-01-01T00:00Z and < 2001-07-01T00:00Z`
  (California crisis peak: blackouts, the PG&E bankruptcy, DWR contracting).
- **W2** = dasovich-j, `date >= 2001-07-01T00:00Z and < 2002-01-01T00:00Z`
  (settlement grind, MOU aftermath, and Enron's own collapse from October).
- Disjoint by construction on the `date` column; a message's parallel-export
  duplicates share its date, so no message can appear in both windows.
- **Window→arm assignment rule** (fixed mechanically, outside anyone's
  discretion): STATIC takes W1 if the frozen home-capsule copy's SHA-256 first
  hex digit is even, W2 if odd. The copy hash (Appendix E) begins `e` —
  even — so **E2S (STATIC) = W1, E2L (LIVE) = W2**.
- **Corpus surface**: each arm receives ONLY `window-slice.parquet` — the
  complete eml_messages rows for custodian dasovich-j in its window,
  materialized by the coordinator before launch (row counts must equal Q5
  above; mismatch is D1). Arms have **no network access and no object-store
  credentials**; out-of-window reads are impossible by construction, and the
  credential-echo hazard is removed rather than managed.
- **Exclusion list**: `exclusion-doc-ids.txt` — **151 full doc_ids + 275
  numeric prefixes**, SHA-256
  `4bf2854ece5cf01a29ff88f738726647a9a8a4a1d4ed2aad475efb2d9020414b`,
  materialized 2026-08-16 by sweeping every prior program Enron artifact (the
  scout memo, ENRON-PILOT-1 and its entire working directory, the enron-study
  case-study journal, the private-review copies) plus the frozen home-capsule
  copy's literals, for corpus doc_id references (builder script retained).
  Census Q4 found ZERO listed ids in either window — the list is
  belt-and-braces, carried because it costs nothing and the arms' §3 rule
  ("verify against your snapshot and state the result") turns it into an M5
  checklist item. Neither arm may stage any episode, claim evidence, or quote
  anchored on a listed id.
- **Honest asymmetries, recorded now with direction** (the assignment rule
  above landed them mechanically): W1 has **3.1×** the snapshot rows (28,108
  vs 8,942 — the crisis-peak inbound flood) but only +8% own-prose authored
  material — the W1 arm does more funnel work to reach comparable material.
  W2 is more forward-marked (57% vs 37% of deduped authored) and thematically
  darker (the collapse). Formation-phrase hits slightly favor W2 (52 vs 49).
  No correction is applied; the directions are recorded here so they cannot
  be argued after the fact.
- An accidental read of out-of-window or excluded material (e.g., a
  materialization fault) must be quarantined: nothing staged from it, the miss
  recorded in the arm's journal. Read-and-quarantined = D2; staged = D1.

## 4. Conditions

- **Agents**: two cold archivist agents, one per arm; no grader sub-agents
  (the pilot's single-archivist form — this task's grading IS the archivist's
  reading). Plus preparer, measurer, judge (§9). All five graded-path agents
  (two arms, preparer, measurer, judge) use the SAME model — the program's
  standard trial consumer (Sonnet-class); the coordinator records the exact
  model id BEFORE the first launch. Arms have: no repo access, no
  study-journal access, no search engines, no network; no capsule access
  other than the arm's own fresh capsule — plus, for E2L only, the frozen
  home-capsule copy THROUGH THE ASSEMBLER ONLY (§5). Neither arm is told a
  comparison is running, told of the other arm, or told of a judge; both are
  told (truthfully) that they are the ENRON-2 archivist for the phase-2
  foreign-corpus harvest and their capsule + journal become program assets.
- **Working dirs** (coordinator creates before launch): `/home/codex/enron-e2s/`
  and `/home/codex/enron-e2l/`, each containing: a venv with the doxabase
  0.2.0 wheel (same file both arms, from `/workspaces/doxybase/dist/`) plus
  duckdb/pandas/pyarrow (same versions both arms, recorded); `bridge.py` (the
  study-standard bridge, capsule path pointed at the arm's own
  `capsule.sqlite`); `kh-vocab-seed.trig` (v4 seed, 1180 quads, SHA-256
  `213da77a9d4988c7c4eb6ff0680474fe397368d24e9d2e6012eb383ea1b05fd4`);
  `exclusion-doc-ids.txt` (hash in §3); `window-slice.parquet` (the arm's
  window, hash + row count recorded at materialization, row count must equal
  §3/Q5); and `BRIEF.md` (Appendix B for E2S, Appendix C for E2L). E2L's dir
  additionally contains `assemble_context.py` (SHA-256
  `403111be89410231a0ed2622e0773f6098d3f2f59e4abe4407071d627f984e19`) and
  `home-capsule-frozen.sqlite` (read-only copy, SHA-256
  `e85cb43828865833335b0af37cf5e08693f6a8d18d5b553e214596a61d51d8c4`,
  file mode 444). At launch the coordinator diffs each delivered BRIEF.md
  against its appendix (any difference beyond the placeholder classes —
  working-dir name, window dates — is D1), verifies every hash above, and
  verifies E2S's dir contains NO capsule copy and NO assembler (presence
  is D1).
- **Budgets**: capsule-derived context is the budgeted resource — 1500
  nominal assembly tokens per arm (E2S: the one briefing render; E2L: the sum
  of its `--budget` arguments across ≤8 consultations). Local analysis
  compute is deliberately unmetered (see §6 on the dropped M6) but must be
  scripted and retained.
- **Sessions**: one archivist session per arm; one continuation session
  permitted on context exhaustion (D2 note).
- **Launch order**: sequential, E2S first, then E2L (pre-committed; the
  frozen snapshots make order immaterial to material). Coordinator
  interaction with a running arm is limited to launch and collection;
  content-neutral infrastructure help is D2, content steering is D1.
- **Order of operations**: (1) this protocol committed, SHA-256 recorded →
  (2) coordinator materializes dirs (snapshot pulls, hashes, model id) →
  (3) E2S runs → (4) E2L runs → (5) coordinator freezes both working dirs
  (SHA-256 over journal, capsule, ledgers, assembly outputs) → (6) preparer
  builds judge packs, seals assignment (§9) → (7) judge grades (§8) and
  (8) measurer counts (§6–§7), in either order or parallel, neither seeing
  the other's output → (9) verdict assembled per §10 → (10) trial record
  written.

## 5. The briefs and the delta

- **Common core** (Appendices B and C, §§1–5 and 7): role and task; access
  rules; material eligibility; the pilot's method as law — the six standing
  conditions (body-level forward-detection, (subject, date, body-hash) dedup,
  the personal-content exclusion machinery, third-party generalization to
  roles, the research-corpus authority posture recorded in-capsule,
  genre-honest recording including the exactly-one-decision rule, arcs only
  with in-corpus termini, the ≤6-person-claim ceiling at the ≥2
  independent-thread bar); doc 17's liberalized observation-tier language
  (identical in both briefs — it is a program-wide policy, not this trial's
  delta); the four research questions; deliverables. Word-identical outside
  the placeholder classes (working-dir name, window dates), machine-verified
  from one template.
- **The delta is §6 of each brief and nothing else.** E2S §6 = one framing
  paragraph plus the **frozen v0 render quoted verbatim** (produced
  2026-08-16; command, capsule-copy hash, and render hash in Appendix E).
  E2L §6 = the same framing sentence about the home capsule, then the
  consultation protocol: the assembler command form, the 1500-token/≤8-
  consultation budget, the ledger-before-firing rule, the
  assembler-is-the-only-door rule, and the memory-not-material rule (nothing
  from the home capsule may be staged as harvest content; anchors and quotes
  come from the arm's snapshot only). Both §6s close with the identical
  guidance-not-law sentence.
- **Parity accounting, stated honestly**: the two §6s cannot be
  length-matched the way the consumption trial's were — the delta here is a
  mechanism, not a prose layer. The equalized quantity is **capsule-derived
  tokens available: 1500 nominal per arm**. Brief word counts (Appendix E)
  therefore differ; the assembler's per-invocation header (which echoes the
  arm's OWN question, not capsule content) is excluded from the accounting.
  Known residual asymmetries, directions recorded: the static render sits in
  context from minute zero (always visible, never re-fetched — an attention
  advantage AND a fixed-relevance disadvantage; this trade IS the trial);
  the live arm pays session tokens for issuing consultations and reading
  outputs (a cost the static arm never pays; reported as a secondary
  observation, not corrected).
- **Render freeze**: the E2S §6 render is frozen as produced 2026-08-16
  (file `static-render-frozen.md`, SHA-256
  `ca1895f07ff269aa19845be1bacf2db4adca586cb40e48f760b84bd299e00c75`,
  reproducibility verified by byte-identical re-run). If the live home graph
  moves between commit and launch, the trial still runs on THIS render and
  THIS capsule copy (drift = D3 note); after first launch neither may change
  at all (D1).
- **A calibration note, recorded at authoring time so it cannot be re-argued
  as surprise**: at budget 1500/handles, v0 serves **3 nodes** (of 27
  scored candidates) for this task description — one distiller
  session-meta mega-observation (dense, and genuinely email-relevant: it
  carries the email dialect shapes and the authority regimes), the
  living-persons-posture policy, and a pilot evidence pointer. A probe at
  `--entries 16` returned the identical composition (budget, not entry
  count, is binding). This is the instrument's honest output, not a
  hand-curated brief; §12.2 and §12.5 carry the consequences. The LIVE arm
  facing the same instrument can split its 1500 tokens into smaller,
  differently-worded pulls — that freedom is precisely the mechanism under
  test.
- **The task description used for the render** is frozen in Appendix E
  verbatim; it is the author's one-sentence-honest description of the arm
  task, and an author degree of freedom (§12.4).

## 6. Measurement layer 1 — MECHANICAL (counted from artifacts, no judgement)

Counted by the MEASURER (§9) identically for both arms, using the frozen
working dirs. Per-metric better-direction and tie rules fixed here; a tie
counts to neither arm. These reuse the consumption trial's definitions with
the adaptations stated; **M6 (op efficiency) is dropped — it does not
transfer** (no network ops exist; local compute is deliberately unmetered
because the snapshot design removed the metered resource). The mechanical
layer is therefore **6 metrics**, and the win threshold (§10) uses the house
protocol's own pre-committed metric-drop rule (≥4 of 6).

- **M1 — staging-failure rate** = (staged revisions that reached validation
  and failed, were refused at apply, or were closed discarded for cause) ÷
  (applied revisions). Pure tool-envelope schema errors excluded (the
  platform's designed targeted-error teaching). Source: bridge_log.jsonl +
  revision rows. Lower is better; tie = exact.
- **M2 — quote-verification failure rate** = (staged episodes/claims
  containing ≥1 quote that fails whitespace-normalized verbatim match against
  the arm's OWN window-slice.parquet bodies) ÷ (staged episodes/claims with
  quotes). Measurer-run uniformly regardless of what the arm itself ran.
  Lower; tie exact.
- **M3 — dead-anchor rate** = (IRI references in the capsule resolving to no
  subject in the capsule, plus in-record doc_id anchors absent from the arm's
  snapshot) ÷ (total such references). Lower; tie exact.
- **M4 — unverified-claim rate** = (checked journal claims contradicted by
  the arm's graph, ledgers, or artifacts) ÷ (claims checked). Claim classes,
  pre-committed — the measurer enumerates EVERY final-journal sentence in
  these classes and checks each mechanically: (a) numeric counts of funnel
  stages, capsule contents, or consultations; (b) conformance /
  zero-staged-debt / parity claims; (c) universally quantified claims
  ("all", "every", "zero", "none"). Lower; tie exact. Full enumeration
  published with the verdicts.
- **M5 — coverage-statement completeness**: 0–10 checklist, one point each:
  (1) snapshot row count stated and reconciled against the materialization
  record; (2) authored-filter rule stated with counts in and out; (3)
  forward-detector described (patterns enumerated) with strip counts; (4)
  dedup rule stated with removed count; (5) every exclusion class enumerated
  with per-class counts including zeros; (6) triage rule stated with hit
  count and disposition of hits (read/kept/discarded and why); (7)
  eligibility confirmation stated (window + exclusion list checked over all
  staged anchors); (8) final census stated WITH its method, and the method is
  a graph read; (9) revision accounting reconciles (every staged revision
  accounted for in the bridge log and journal); (10) an explicit statement of
  what was NOT covered. Higher; tie exact.
- **M7 — end-state integrity**, 0–3: +1 validate_graph scope=all conforms
  (measurer-verified on the capsule, not journal-trusted); +1 zero staged
  debt; +1 observation/evidence parity. Higher; tie exact.

Reported alongside (NOT verdict inputs, because the arms worked different
windows): episode/arc/person-claim/observation counts, funnel stage counts,
wall time, session token cost, and — for E2L — everything in §7.

## 7. Measurement layer 3 — RETRIEVAL (new, central; counted from artifacts)

All computed by the measurer from frozen artifacts; every per-item and
per-candidate verdict published (auditable like M4).

- **The USED test (mechanical, fixed here)**: an assembly **item** is one
  `## `-headed node block in an assembler output. Item *i* counts as **used**
  by an arm iff, at any point AFTER the assembly's timestamp (for E2S: after
  session start), at least one of the following appears in the arm's journal,
  staged payloads, or capsule literals: (a) *i*'s IRI; (b) *i*'s rendered
  label (exact match, case-insensitive); (c) a contiguous **≥8-word** span
  from *i*'s rendered text (whitespace/case-normalized). Appearances inside
  the arm's own saved assembly outputs, its consultation ledger, or its brief
  do not count — those are the pull, not the use. (Eight words: shorter spans
  false-positive on shared study vocabulary.) The span/label tests are
  deliberately conservative — behavioural influence without textual echo goes
  uncounted, for both arms symmetrically; the judged layer is where
  uncredited influence can still surface.
- **R1 — consultation count** (E2L): ledgered assembler invocations. An
  invocation that errors or serves zero items is ledgered, counts toward R1
  and the ≤8 cap, consumes no token budget, and is recorded as a
  zero-yield consultation (prime recall-gap evidence). E2S's R1 ≡ 1 (the
  briefing render), by construction.
- **R2 — retrieval precision** (E2L): per consultation *c*, |items served in
  *c* that pass the used test| ÷ |items served in *c*|. **Aggregate
  precision** = Σ used ÷ Σ served over all item-servings (item-weighted; an
  item served by two consultations contributes to both denominators — each
  serving is a separate instrument decision). Zero-item consultations do not
  enter the denominator. Small-n quantization is acknowledged: at v0's
  serving sizes, per-consultation precision moves in large steps; that is
  why the floor in §10 is set where one-of-three reaches it.
- **R3 — recall gap** (both arms): count of **unmet-need events**, two kinds:
  (a) *reformulation events* (E2L only): consultation *c_k* (k≥2) where ≥1
  item served in *c_k* and subsequently used was absent from every earlier
  consultation's output — evidence that an earlier assembly should have
  carried it; (b) *stated-need events* (both arms): the measurer enumerates
  every final-journal/ledger passage containing a stated information gap
  ("couldn't find", "didn't know", "unclear whether", "had to guess", "no
  guidance on", or a process-directed question), then replays each against
  the frozen assembler + frozen capsule copy with the passage's question
  verbatim (budget 500, handles): if the replay serves an item that
  mechanically answers it (the item's text contains the missing
  rule/artifact/answer by the used-test's span standard), the event counts.
  Lower is better. R3 is **diagnostic, not a win criterion** — it feeds the
  interpretation clause (§10), because it is the number that says whether
  the capsule HAD what the arm needed.
- **R4 — render usage rate** (E2S): the used test applied to the 3 items of
  the frozen briefing render — the static arm's exact analogue of R2. Also
  computed for E2L over all served items, so the two arms' capsule-content
  usage is directly comparable.
- **Reproducibility check**: the measurer re-runs every ledgered consultation
  command against the frozen copy; a non-identical output is investigated
  (D2): retrieval metrics are computed from the SAVED outputs, and the
  mismatch is reported.

## 8. Measurement layer 2 — the blind JUDGED rubric

A separate judge (fresh agent, model recorded before it sees anything, no
repo access, no capsule bridge, no web) receives the two arms as **X** and
**Y** (assignment sealed, §9) and grades both journal+capsule-digest packs on
five criteria, each 1–5 per arm, each score requiring ≥2 cited evidence spans
(uncited scores invalid; a criterion with no evidence either way in a pack
scores 2 with a statement). Weighted total = Σ weight × score (max 60). The
judge's brief is Appendix D verbatim; the judge never sees this protocol, the
arm briefs, the render, any consultation artifact, or the mechanical/retrieval
results.

- **J1 — verification-before-trust** (weight 3): quote re-verification
  actually run with results; final census read from the graph; suspicious
  successes probed. 5 = systematic with a caught-and-corrected or
  checked-and-held instance; 1 = trust throughout.
- **J2 — trap avoidance** (weight 3): three failure families, defined for the
  judge without study attribution: (a) **record-vs-summary drift** — final
  counts and state claims derived from the actual data store, discrepancies
  recorded rather than smoothed; (b) **borrowed-words attribution** — claims
  about the subject person resting on text the subject merely forwarded or
  quoted, or behaviour-pattern counts inflated by duplicate copies of the
  same message (this genre's two documented mechanical lies); (c) **silent
  narrowing** — every funnel reduction states what fell away and why; no
  unexplained shrinking Ns. Start at 5, deduct per family fallen into,
  evidence cited per deduction.
- **J3 — honest-negative recording** (weight 2): zeros and absences stated
  as findings where a consumer would look; empty exclusion classes and
  failed searches recorded, not omitted.
- **J4 — refusal quality** (weight 2): near-miss material refused WITH
  reasons and revival conditions — unterminated arcs kept episodes-only,
  sub-threshold person-claims declined, singleton shapes docketed rather
  than minted; declined options citizens of the record.
- **J5 — couldn't-say quality** (weight 2): concrete, anchored in
  actually-encountered material, actionable for the vocabulary side,
  distinguishing cannot-express from did-not-see.

**Judge phases, in order, no backtracking**: Phase A — verify pack hashes
against the preparer's manifest; read the first pack fully (X first if X's
pack hash begins with an even hex digit, else Y first), write per-criterion
notes. Phase B — same for the second. Phase C — score all ten cells with
cited evidence. Phase D — weighted totals, layer winner (strictly higher;
equal = judged tie), then record ANY suspicion about how the packs differ in
origin and whether it influenced grading; freeze.

## 9. Blinding and roles

Five roles, no dual-hatting except where stated:

- **COORDINATOR**: materializes, launches, collects, freezes, records hashes
  and model ids, assembles the verdict per §10. Knows everything; never
  grades.
- **PREPARER** (separate agent): builds judge packs from frozen artifacts.
  Per arm: (1) a stripped copy of the journal; (2) a stripped flat-text
  digest of the capsule's staged content (episodes, arcs, person-claims,
  observations: labels, decisions, rationales, quotes, termini — exported
  read-only, ordered by IRI). **Excluded from packs entirely**: the brief,
  the consultation ledger, all assembly outputs, the render. Stripping = the
  pre-committed redaction dictionary: the strings "assemble", "assembler",
  "assembly", "working-memory", "consult", "consultation", "home capsule",
  "home-capsule", "know-how", "knowhow", "heuristic", "promoted", "distill",
  "provenance", "handles", "budget", "v0", "capsule copy",
  "knowhow.study", "richcanopy.org", the arm ids ("e2s", "e2l", any
  casing), any sentence quoting, citing, or describing either brief's §6
  mechanism, **plus a dynamic rule**: every rdfs:label, IRI, and distinctive
  ≥4-word phrase appearing in `static-render-frozen.md` or in any of E2L's
  assembly outputs is added to the dictionary before packs are built.
  Replacements are seamless neutral paraphrase (no visible redaction
  markers); every replacement logged to a sealed redaction ledger for
  post-verdict audit. The preparer inevitably learns arm identities; the
  preparer never communicates with the judge except through packs and
  manifest.
- **Pack labeling and assignment seal** (total rule): pack hash = SHA-256
  over stripped journal ‖ stripped capsule digest. Lexicographically smaller
  pack hash = **X**; the other = **Y**. The preparer writes the assignment
  (E2S/E2L ↔ STATIC/LIVE ↔ X/Y, both pack hashes) to a sealed file whose
  hash the coordinator records BEFORE the judge is spawned. Reading order
  fixed by X's first hex digit (§8).
- **MEASURER** (separate agent): computes M1–M5, M7 (§6) and R1–R4 (§7) on
  the REAL frozen artifacts (unblinded by necessity). The
  judgement-bearing enumerations (M4 claims, M5 checklist, R2 used-verdicts,
  R3 candidates-and-replays) are published in full so the counting is
  auditable. The measurer never sees the judge's output before the verdict;
  the judge never sees the measurer's.
- **JUDGE**: §8. Fresh agent, blind, Appendix D only.

## 10. What counts as a WIN (sealed)

- **VOID**: any D1. Reported as such; the windows, custodian, and render are
  spent (§12.10) — a re-run needs fresh allocation and a fresh seal.
- **LIVE WIN** — requires ALL THREE layers:
  1. E2L strictly better on **≥4 of the 6** mechanical metrics (the house
     protocol's own pre-committed threshold for a 6-metric layer);
  2. E2L has the strictly higher judged weighted total;
  3. **retrieval qualification**: R1 ≥ 2, with ≥1 consultation ledgered
     AFTER E2L's first applied staging revision that yields ≥1 used item
     (the mid-task condition — doc 17's thesis is that live retrieval wins
     where relevance shifts MID-task; a launch-only consultation is
     self-administered static briefing), AND aggregate retrieval precision
     (R2) **≥ 1/3**.
- **STATIC WIN**: E2S strictly better on ≥4 of 6 mechanical metrics AND
  strictly higher judged total. (No retrieval qualification — static IS the
  null mechanism.) Reported plainly; doc 17 §5's cheaper-null reading is
  engaged.
- **NULL**: every other combination — split layers, insufficient mechanical
  margin, judged tie, or layers 1–2 met by E2L with qualification 3 failed
  (reported by name as an **unattributable win**: the work won but the
  mechanism cannot claim it). If E2L never consults, or consults only at
  launch, the verdict cannot be LIVE WIN regardless of layers — reported as
  the named finding **unused instrument** (itself a doc 17 datum: offered
  retrieval that goes unused says the demand side is weaker than the
  thesis assumes). The tie-break is pre-committed: there is none — a split
  verdict IS the null verdict.
- **Why the 1/3 precision floor** (pre-justified): (a) v0 serves few, large
  items (the calibration render: 3), so the floor must be reachable at small
  n — one-of-three exactly reaches it; (b) below 1/3, most pulled context
  did no attributable work, and a win would belong to the arm's judgement,
  not the mechanism — the consumption trial already showed content-presence
  alone moving nothing; (c) above it, every consulted assembly is more
  signal than noise at the margin the used-test can see.
- **The interpretation clause** (pre-committed, because a v0 loss is
  ambiguous by construction): if the verdict is STATIC WIN or NULL **and**
  E2L's aggregate precision is **< 1/3**, the result is recorded as
  **instrument-limited** — it bears on the v0 walk, not on doc 17's thesis;
  the named follow-up is the v1 assembler, and the consultation ledger's
  per-item verdicts are the requirements list for it. If E2L's precision is
  **≥ 1/3** and it still did not win, the result bears on the thesis at this
  diameter: the assembly could be done as well statically at briefing time
  (doc 17 §5's stated, cheaper alternative). If LIVE WIN with precision
  ≥ 1/3, the timing/selection claim stands at this diameter — and R4-vs-R2
  is reported alongside: if the static render's usage rate matches or beats
  live precision, the selection half of the claim weakens even in a win, and
  the report says so.
- **Secondary observations** (recorded honestly, no verdict weight): what
  E2L consulted about and when (the demand pattern is v1's requirements
  data); whether E2S visibly used its render (R4 items, echoes at
  failure-mode edges); whether either arm independently reinvented served
  content; per-arm cost (session tokens, wall time); anything either arm did
  that the briefs did not anticipate.

## 11. Deviation classes

- **D1 — invalidating**: a delivered brief differs from its appendix beyond
  the placeholder classes; the E2S §6 render is not byte-identical to
  `static-render-frozen.md`; any launch-time hash mismatch (seed, wheel,
  snapshot, exclusion list, assembler, capsule copy) or snapshot row-count
  mismatch against §3/Q5; E2S found in possession of the capsule copy or
  assembler; E2L reading `home-capsule-frozen.sqlite` by any path other than
  the assembler; home-capsule content staged as harvest content; an arm
  stages material that is out-of-window or exclusion-listed; an arm gains
  network access, object-store credentials, repo, study-journal, or
  other-capsule access; the arms exchange any material; an arm learns of the
  comparison or the judge; different models across the five graded-path
  agents; the judge learns the assignment, sees unstripped artifacts, any
  §6 mechanism trace, or any measurer output before Phase D freezes;
  consultation token total exceeding 1500 by >10% or consultation count >8;
  rubric, metrics, or win criteria edited after first launch; content
  steering of a running arm.
- **D2 — recorded, verdict stands with caveat**: consultation token overrun
  ≤10% (record the excess); a consultation fired before its ledger row was
  written (late-ledgered, enumerated — the consultation still counts in R1/R2);
  a continuation session; episode count outside 18–30 (journal justification
  required); a read-then-quarantined ineligible message; content-neutral
  infrastructure help; a preparer redaction miss discovered post-verdict
  (verdict stands UNLESS the judge, asked once, states the leak influenced
  grading — then NULL); a metric the measurer cannot compute (drops from
  both arms; the mechanical threshold becomes ≥4 of 5, or ≥3 of 4 if two
  drop); a consultation replay that does not reproduce byte-identically
  (metrics from saved outputs, mismatch reported).
- **D3 — noted only**: live home-graph drift after the copy freeze (the
  trial runs on the frozen copy regardless); the frozen copy differing from
  the consumption trial's 2026-08-15 copy (already observed: `e96c…` →
  `e85c…`, the capsule moved between 08-15 and 08-16 — expected, recorded in
  Appendix E); MinIO hiccups/retries during coordinator materialization;
  cosmetic tooling differences.

## 12. Counterweights — what a win would NOT prove

1. **"Outside source distribution" means evidence lineage, not total
   novelty.** The promoted heuristics' citing episodes are home + kernel
   work; email contributed only 4 dialect shapes to the vocabulary, none to
   the heuristic layer. But much of the know-how is process-generic (any
   harvest benefits from verify-the-good-news), and the OBSERVATION tier
   demonstrably holds email-specific memory (the pilot and distiller records
   — the calibration render surfaced exactly those). A win shows the
   capsule's content TRANSFERS across the promoted layer's lineage boundary
   under live assembly; it does not show retrieval of domain-alien knowledge.
2. **The v0 instrument bounds the showing in both directions.** A LIVE loss
   with precision < 1/3 indicts the walk, not the thesis (the interpretation
   clause routes it); and the STATIC comparator is also v0-made — this trial
   compares live vs static assembly UNDER ONE INSTRUMENT. It cannot rank
   live v0 against a hand-curated static brief; the consumption trial's
   human-selected render was a stronger static form than this render.
3. **n=1, one genre, one custodian, disjoint windows.** Run-to-run variance
   is unmeasured; the arms worked different material; a single-run
   difference can be luck. No generality claim to other genres, corpora, or
   models.
4. **The brief-writer effect.** One author wrote both briefs, chose the
   render's task description (frozen, Appendix E), the 1500 budget, and the
   window pair. A different phrasing yields a different render; the
   calibration probes showed robustness to `--entries` but not to phrasing.
   Claims attach to THIS render and THIS protocol.
5. **The static render is thin, and that is recorded before launch, not
   discovered after.** Three nodes, one of them a mega-observation. If E2S
   loses, "the render was weak" is not an admissible objection — it is the
   instrument's honest 1500-token output, the same instrument E2L gets; if
   the live arm's smaller, targeted pulls beat one big static pull, that IS
   the finding, not a confound.
6. **Provenance mode is fixed at handles.** Nothing here compares interface
   modes; that is the owner's parameter-not-decision doctrine, decided by a
   future trial.
7. **Window asymmetries are real, directions recorded** (§3): E2S/W1 carries
   3.1× the funnel haystack; E2L/W2 carries heavier forwarding and the
   collapse-era material. The assignment was mechanical (hash parity); the
   asymmetry could favor either arm and is reported, not corrected.
8. **Teaching vs licensing cannot be separated.** The model may already know
   every behaviour involved; assembly may merely foreground it. An attention
   effect is still an effect; the claim stops at "mid-task assembly changed
   measured behaviour."
9. **Blinding is partial by nature.** Redaction removes identifiers, not
   work rhythm; a journal punctuated by mid-task reorientations may reveal
   its arm to the judge through style alone. The judge's suspicion is
   recorded, not eliminated.
10. **The seal is spent on this run.** Win, lose, or null: the windows, the
    custodian, the render, and the frozen copy are burned — a successor
    trial needs fresh allocation. One shot; report what happens.
11. **A null still pays.** Doc 17 built v0 explicitly to "generate the usage
    data the proper version needs" — the consultation ledger, the used-item
    verdicts, and the recall-gap replays are v1's requirements corpus under
    every verdict, and the trial's harvests are real phase-2 corpus material
    regardless.

## 13. After the verdict

The trial record (docs/journal/trials/, alongside this protocol) reports: the
per-metric table with full enumerations, the retrieval tables (per-consultation
rows, per-item used verdicts, recall-gap replays), the judge's report verbatim,
the assignment unseal, the deviation ledger, the verdict against §10 including
the interpretation clause's routing, and the secondary observations. James
spot-checks at his leisure — the gold standard remains the owner recognizing
(or failing to recognize) the difference between an agent that remembers and an
agent that was told. Both capsules go to the corpus program as ENRON-2 material
(window-disjoint, mergeable), subject to the standard shareability flow —
nothing leaves a capsule without the owner. Friction and couldn't-say yields
flow to the distiller ledger regardless of verdict. If LIVE WIN: the v1
assembler is justified as the next product batch's headline, and the
provenance-mode trial is the next-diameter question — explicitly NOT claimed by
this run. If STATIC WIN or NULL: the interpretation clause routes the result to
either the v1 requirements list (instrument-limited) or doc 17 §5's
static-is-enough conclusion (thesis-bearing), and the consumption trial's
brief-time render remains the program's standing consumption mechanism.

## Appendix A — the census record (author, 2026-08-16, read-only)

**Method**: DuckDB + httpfs against `s3://enron-emails/eml_messages.parquet`
(MinIO; endpoint and credentials from environment, never echoed into any
artifact). 5 data-bearing queries + 1 client-side parser error (a quoting bug
in the phrase list; caught before execution, fixed, recorded). Scripts
`census.py`, `census2.py`, `census3.py`, `census4.py` and result JSONs
retained in the trial working dir. Budget: ≤10 queries; used 5.

**Q1 — authored-name variants** (custodian, top senders): dasovich-j: 'Jeff
Dasovich' 29,127 rows; next-largest named sender 854 (Susan J Mara).
kaminski-v: 'Vince J Kaminski' 25,030 + 'Kaminski, Vince J' 267; also large
secretarial/staff volumes (Shirley Crenshaw 4,614). Authored filters fixed
accordingly (§3).

**Q2 — deduped authored half-years** (body-populated, 1997–2005 hygiene
window; dedup = (subject, date, md5(body)); fwd = body carries 'Forwarded by'
or '-----Original Message-----'; formation = 8 scout phrases):

| custodian | half | authored rows | deduped | fwd-marked | formation hits |
|---|---|---|---|---|---|
| dasovich-j | 2000-H2 | 11,170 | 1,498 | 438 | 38 |
| dasovich-j | 2001-H1 | 12,584 | **2,167** | 807 | **49** |
| dasovich-j | 2001-H2 | 3,193 | **1,860** | 1,062 | **52** |
| kaminski-v | 2000-H1 | 5,196 | 1,142 | 546 | 23 |
| kaminski-v | 2000-H2 | 10,997 | 1,356 | 725 | 24 |
| kaminski-v | 2001-H1 | 5,724 | 1,749 | 1,187 | 39 |
| kaminski-v | 2001-H2 | 932 | 918 | 793 | 17 |

(Fringe half-years with <100 deduped omitted here; full JSON retained.)
Kaminski's forward-marked share runs 48%→86% across halves — his windows are
internally incomparable; Dasovich's 2001 pair is the balanced allocation.

**Q3 — dasovich-j monthly, 2000-08→2001-12** (deduped / formation hits /
own-prose proxy = >40 chars before first forward marker): 2001: Jan
289/10/187, Feb 391/10/269, Mar 455/8/299, Apr 509/15/376, May 377/5/272,
Jun 146/1/106, Jul 524/4/403, Aug 84/0/65, Sep 396/16/285, Oct 536/23/421,
Nov 229/6/160, Dec 91/3/64. Window sums: W1 deduped 2,167, own-prose 1,509,
formation 49; W2 deduped 1,860, own-prose 1,398, formation 52. No dead months
(min 84); both windows have one thin month (Jun 146, Aug 84) — recorded, not
corrected.

**Q4 — exclusion collisions**: zero excluded doc_ids (full or prefix) present
among dasovich-j 2001 rows. The exclusion list is belt-and-braces.

**Q5 — snapshot sizes** (all senders, the arms' raw material): W1 = 28,108
rows (27,377 with non-empty body); W2 = 8,942 rows (8,077 with body). These
counts are the materialization check (§3): a coordinator snapshot pull that
does not reproduce them exactly is D1.

## Appendix B — Arm E2S (STATIC) brief, delivered verbatim as `BRIEF.md`

```markdown
# ENRON-E2S — window archivist brief (phase-2 foreign-corpus harvest, know-how corpus program)

## 1. Role and task

You are the archivist for ENRON-2, the second foreign-corpus harvest of the
know-how corpus program. The first was the Kay Mann pilot; its method is your
template and its six standing conditions are law here. Your task: harvest the
formation-bearing material of ONE custodian time-window of the Enron email
corpus — Jeff Dasovich (custodian `dasovich-j`), Enron government-affairs /
regulatory lead through the California power crisis, window **2001-01-01 to
2001-07-01 (UTC, `date` column)** — into the fresh capsule in your working
directory: build the mechanical funnel, read the formation seam, record
episodes, promote arcs only where the record shows completed arcs, stage
person-model claims at the program's sighting bar, and journal the work. This
is a real corpus tranche, not an exercise: your capsule and journal become
program assets. Target 18–30 curated episodes (the pilot yielded 36 from a
19-month window; yours is 6 months and denser). Be honest everywhere — the
record is the deliverable.

## 2. Access rules (hard)

- Working directory: `/home/codex/enron-e2s/`. Everything you produce lives
  here. Do not read or write outside it; the venv and installed doxabase
  wheel inside it are part of it.
- Your corpus surface is `window-slice.parquet` in your working directory —
  the complete message rows for your custodian and window, materialized for
  you. There is NO network access and NO object-store credential in your
  environment; you need neither. Do not attempt to reach any other corpus
  surface.
- `bridge.py` is the ONLY door to your capsule. One documented exception: the
  pilot found the bridge lacks the staged-review-decision tool; if and only
  if you must close a failed staged row, the documented core-API fallback is
  permitted for that single operation, recorded in your journal.
- No repository access, no study-journal access, no other capsules, no
  search engines, no documentation beyond this brief and your working
  directory's contents.
- Analysis compute is unmetered but must be scripted and retained: keep
  every funnel and analysis step as re-runnable scripts with their counts
  (the pilot's `pipeline.py` pattern).
- Corpus-separate: nothing you do writes to any capsule but your own
  `capsule.sqlite`.

## 3. Material eligibility (hard)

- Custodian `dasovich-j` only; message `date` within your window only. Your
  snapshot is already window-scoped — treat any row outside the window as a
  materialization fault: quarantine it, stage nothing from it, and record
  the miss in your journal.
- `exclusion-doc-ids.txt` (provided): never stage an episode, claim
  evidence, or quote anchored on a listed doc_id (a full id, or any id whose
  numeric prefix — the first two dot-separated fields — is listed with the
  PREFIX marker). A pre-run census found zero listed ids in your window;
  verify this against your snapshot and state the result in your journal.
- Quoted or forwarded content INSIDE your snapshot's messages may be read
  (it is part of the message), but it is never the custodian's prose:
  attribution discipline per §4 governs every claim.
- Dedup before any counting: parallel PST exports duplicate messages under
  multiple doc_ids; the (subject, date, body-hash) key is the pilot's
  standard. A sighting count made without dedup is fiction.

## 4. Method (the pilot's pipeline and six standing conditions, law here)

- **Forward-detection before anything.** Detect forward-wrapper markers in
  body text; the pilot needed 7 marker patterns (Lotus "Forwarded by",
  Outlook "Original Message", nested From:/Sent by: blocks, "X on date"
  attribution lines, bare date+To: blocks, To:…Subject: blocks) plus
  trailing-attribution trimming. The `is_forward` flag undercounts 4–5x —
  never rely on it. Isolate the custodian's own prose; every claim about
  the custodian rests ONLY on own prose.
- **Dedup** by (subject, date, body-hash) — before sightings, before counts.
- **Exclusion machinery before any capsule write**, each class logged with
  its count including zeros: folder-family exclusions (Calendar / Contacts
  / Tasks); family/health keyword trip-wires; freemail-only recipient
  detection; family-recipient detection from metadata (recipient domains and
  same-surname non-Enron addresses — the pilot's largest catch came from
  recipients, not keywords); personal-subject threads; privilege-marked
  litigation strategy (regulatory and deal reasoning is the target,
  litigation posture is not). Read nothing beyond recipients and subjects
  from excluded messages.
- **Third-party generalization**: non-custodian individuals appear only as
  roles ("the ISO contact", "his counterpart at the utility", "the senior
  lawyer"), never by name.
- **Authority posture**: record one observation stating the basis explicitly
  — research-corpus regime, NOT consent (the custodian cannot consent; FERC
  public record, standard research usage, scout-memo mitigations applied) —
  and carry the posture on the person node (comment + seeAlso), per the
  pilot.
- **Genre-honest recording**: email compresses reasoning — record what the
  record holds and nothing more. Episodes carry exactly one decision (split
  multi-decision messages by the dominant decision and note the rest);
  rationale only where the record has one; shapes only where they genuinely
  fit (the pilot found most email episodes honestly shape-less; candidate
  new shapes sighted ≥2 go to your journal's distiller docket, NOT minted).
  Arcs only where the terminus is IN your window's record — becameAutomatic
  assertable from the record itself; the pilot refused its second arc for
  exactly this. An unterminated formation stays episodes-only, the refusal
  recorded with a revival condition. Person-model claims: at most 6, each
  resting on ≥2 sightings in independent threads (deduped), each with
  assessedAt and an explicit assessment window, behaviour-over-window
  phrasing, names as public corpus identities only.
- **Triage, then read broadly**: a formation-phrase keyword pass (the
  pilot's phrase families) is triage, not a hard filter — the best material
  is often interpersonal micro-repair that keyword lists miss.
- **Capsule mechanics**: the first bridge call creates the capsule; import
  `kh-vocab-seed.trig` (the program's v4 vocabulary seed, 1180 quads) via
  `import_bundle`; confirm `validate_graph` scope=all conforms (0 results)
  BEFORE any harvest staging. Stage in revisions: observations with evidence
  for what you rely on; curated episodes (one observation anchor each,
  decision/rationale/outcome from the record only) with evidence_sources
  citing corpus doc_ids; arcs dual-typed with their pattern class carrying
  the full Pattern contract; machine participants — if any appear — as typed
  actors, never persons. Validate after every apply; end with zero staged
  debt.
- **Journal INTO the capsule as you go**: the observation stream is the
  durable original; `JOURNAL.md` is the human-readable render. Do not
  restrain observation volume — record what the material actually holds;
  dense agent-written prose in literal values is welcome.
- **Verify every quote** you stage mechanically (whitespace-normalized)
  against your snapshot bodies before applying the revision; report
  pass/fail counts.

## 5. Research questions (answer each with a meta observation and a journal verdict)

- **RQ-E2-1 — formation yield**: triage-hit precision on your window (hits
  read vs episodes yielded), against the pilot's 108-hit/36-episode
  precedent.
- **RQ-E2-2 — genre strain**: which seeded shapes fit your material and
  which did not; candidate foreign shapes sighted ≥2, docketed with
  evidence.
- **RQ-E2-3 — arc terminability**: can arcs complete inside a six-month
  window? Onsets without termini reported honestly as episodes-only
  refusals.
- **RQ-E2-4 — economics**: episodes per triage hit; reading-set size; where
  the effort actually went.

## 6. A briefing assembly from the program's home capsule

The program's home capsule is its long-term memory: promoted heuristics,
arcs, policies, and a deep observation store from the program's own recorded
history. Before your launch, a budgeted working-memory assembly was run
against it for your task (the v0 assembler, budget ~1500 tokens, handles
mode). Its output follows verbatim. It is guidance, not law: apply it where
it genuinely applies to your work, and ignore it where it does not.

# Working-memory assembly (v0)
task: Harvest a six-month time-window slice of one Enron custodian's email (Jeff Dasovich, regulatory affairs) into a fresh v4-seeded capsule: build the mechanical funnel (authored filter, forward-wrapper detection, dedup, personal-content exclusion), triage for formation-bearing messages, record episodes with decisions and rationale, promote understanding arcs only with in-record termini, stage person-model claims at the two-sighting bar under the research-corpus authority posture, verify quotes, journal honestly with refusals and couldn't-say
capsule: home-capsule-frozen.sqlite
budget: ~1500 tokens | mode: handles | nodes: 3 of 27 candidates

## 92016369-087f-466f-abd0-de00e49e8b71  [Observation]
<https://richcanopy.org/doxabase/generated/observation/92016369-087f-466f-abd0-de00e49e8b71>  (score 181.2, entry)
- summary: DISTILLER-3 SESSION META + COULDN'T-SAY v5 (2026-08-13, the cross-corpus v3 pass; journal DISTILL-3.md, note VOCAB-NOTE-KH3.md). EXECUTED under owner decision 60cb4ab4: (1) corpus provenance made mechanical — kh:observedInCorpus on every shape individual against khcap: registry nodes; per-genre namespaces refused. (2) Ten dialect shapes minted, all >=2 in-corpus graph-verified: kernel objectionRevision/diagnosisExchange/processNormEnacted/machineReviewOutcome/maintainerOverride + dormancyBrokenByPing (placed as EPISODE shape against the agenda's onset filing — all 3 instances lifecycle-interior; graph over journals); email scopedDelegationRequest/counterpartyPositionHold (2 clean instances, pilot said >=3, recorded honestly)/precedentConformanceCheck/boundaryAssertion. (3) Terminus: terminusBasis (prose, enum-by-cases in comment), TerminusSurface with narrated/silent individuals (13 home arcs typed silent), terminus-REVERSAL REFUSED at n=1 (defe2dfc) with graveyard entry + revival condition. (4) Machine vocabulary (owner-unlocked, all marked syzbot-only): MachineParticipant, machineActor, machineRole (role enum refused: one corpus), machineOutcome (seven-kind enum refused: 5 of 7 kinds under 2 independent events), relayVouch, machineClimateCited. Machines never kh:Person. (5) Three authority regimes as individuals (consent 813ba95e; research-corpus enron fdb34f6f; public-record 60cb4ab4 with the owner's reasoning quoted verbatim); kh:Person minted at n=2 across capsules; james typed under consentRegime. (6) Cross-capsule mechanism WITHOUT weakening the heuristic gate: kh:Capsule registry (3 nodes anchored to verification observations), reexpressedFrom + sourceCapsule with SHACL pairing guard (negative probe: 1 violation, apply refused, closed discarded). (7) REVIVAL EXECUTED: khh:hotfix-narrow-migrate-deliberately promoted citing 3 typed episodes (home original + re-expressed syzbot witnesses 56e3c883/daa88ce3); applicability from e42356e4; failure modes from a5110d5e + home; graveyard entry annotated REVIVED with decline reason retained. tests-encode-semantics and separation-conceptual-not-nominal stay declined (no witness). (8) Seven kh:PolicyStatement citizens (redaction-families, person-model-consent, private-first-routing, absence-by-request, silent-removals, shareability-flow, living-persons-posture) — prose + authority citations only, per doc 16 §6.2. COULDN'T-SAY v5 — resolved from v4: kh:Person parking (a: minted at n=2 via registry), cross-capsule person/citation reference (e: mechanism built), hotfix graveyard (revived). REFUSED this pass, standing with reasons on the terms: machine outcome-kind enum, machine role enum, terminus-reversal term (all await Gerrit as second corpus); per-genre shape namespaces. CARRIED: skill terminus (deliberately unbuilt); context-inversion (n=1 saga); outcome-status enum (case set stands); protocol-note-vs-break; ElicitationRound beat-properties; contract term-kind taxonomy; limit-predicted onset (n=1); instrumentation-reveals-latent-anomaly onset (n=1); span anchoring; interruption-resume ARC (await cross-window evidence); heuristic staleness indexicality (SHARPENED: now that a heuristic has been revived by foreign evidence, the symmetric case — foreign evidence CONTRADICTING a promoted statement — has no mechanism; assessedAt-style indexicality on kh:Heuristic is the expected shape, Gerrit the expected trigger); micro-decision vs drafting-move (email, 21fd9a83 exemplar); folding-phone (n=1). NEW PARKINGS: (i) machine-OPERATOR person-edges (the assign_fw bot operator steering in public is a human behaving measurably — person-territory under public-record regime, deliberately not modelled this pass: no per-person analysis need yet); (ii) re-expression for claims/person references (sourceCapsule deliberately domain-less to receive it); (iii) policy L1-L3 vocabulary (boundaries/categories/enforcement) — the policy distiller's work, from these 7 instances plus the AIS study's; (iv) narrated-terminus as harvest-cost predictor (narration makes termini cheap to detect — a corpus-selection heuristic candidate, 1 corpus). END STATE: validate_graph scope=all conforms; zero staged debt; 322 obs/evidence; ontology 725, shapes 427, map 759, patterns 404 quads; 57 kh:Episode, 11 kh:Heuristic, 13 arcs, 13 kh:DeclinedOption; export_preflight: the same 4 pre-existing tranche-3 residues, nothing from this session fired. Seed re-export follows this observation.
- observedAt: 2026-08-13T00:43:32.336661+00:00

## The living-persons posture (2026-08-13)  [PolicyStatement]
<https://knowhow.study/policy/living-persons-posture>  (score 117.8, entry)
- comment: IN FORCE from the owner's 2026-08-13 decision, its authority — QUOTED: building person-models of people named in public documents is fine because 'we're purely storing and presenting things they intentionally made public, and we're not ourselves even publishing the results, except via major abstractions.' Encoded as the public-record authority regime (kh:publicRecordRegime): analysis permitted in private capsules; PUBLICATION OF RESULTS ONLY VIA MAJOR ABSTRACTION — never republication of the person-model itself. This unlocked the machine-participant vocabulary and person-work on public-figure corpora. Supersedes nothing: the consent regime (813ba95e) and research-corpus regime (enron fdb34f6f) keep their own conditions; regimes coexist, each with its authority on record.

## 5240268d-0c31-4ae1-afd5-3d810c9cb36c  [Evidence]
<https://richcanopy.org/doxabase/generated/evidence/5240268d-0c31-4ae1-afd5-3d810c9cb36c>  (score 38.3, ←evidence)
- summary: Pilot journal and capsule at /home/codex/enron-knowhow/; journal mirrored to the private review repo.
- source: doxabase-private/knowhow-review/ENRON-PILOT-1.md

## 7. Deliverables

- `JOURNAL.md`, in the program's journal style: setup log; the funnel with
  counts and reasons at every reduction step; the reading record; the
  harvest, revision by revision; the four RQ verdicts; final state (from a
  graph read); a friction section (what the tooling made hard); a
  couldn't-say section distinguishing cannot-express from did-not-see; and
  refusals with reasons and revival conditions.
- Working artifacts retained in place: funnel scripts and counts JSON,
  reading-set files, staging payloads, verification outputs.
- `capsule.sqlite`: validate_graph scope=all conforming, zero staged debt,
  observation/evidence parity. Run `export_preflight` and report its result;
  the shareability review is the owner's — nothing leaves the capsule.
- Do not commit anything to any repository; the coordinator collects your
  working directory when you report completion.
```

## Appendix C — Arm E2L (LIVE) brief, delivered verbatim as `BRIEF.md`

Sections 1–5 and 7 are word-identical to Appendix B outside the placeholder
classes (working-dir `/home/codex/enron-e2l/`; window **2001-07-01 to
2002-01-01**; §1's window text and §3's window text change accordingly, and
§1's density remark reads "yours is 6 months and denser" identically). They
are not repeated here in the sealed file's body — the coordinator generates
both briefs from one template and diffs at launch (§4). The delta section:

```markdown
## 6. Mid-task consultation of the program's home capsule

The program's home capsule is its long-term memory: promoted heuristics,
arcs, policies, and a deep observation store from the program's own recorded
history. Your working directory contains a read-only frozen copy
(`home-capsule-frozen.sqlite`) and the program's v0 working-memory assembler
(`assemble_context.py`). You MAY consult it at any point in your work —
before starting, mid-funnel, mid-staging, whenever a question arises that
the program's history might answer:

    python3 assemble_context.py home-capsule-frozen.sqlite "<your question>" --budget N --provenance handles

Rules (hard):

- Total budget across all consultations: **1500 tokens** (the sum of your
  `--budget` arguments), across **at most 8** consultations. Spend it in
  the chunks you find useful; unspent budget is fine.
- `--provenance handles` always (fixed for this tranche).
- Ledger EVERY consultation to `consultations.jsonl` BEFORE firing it, one
  JSON object per line: `{"n": k, "at": "<ISO-8601 UTC>", "question":
  "<verbatim>", "budget": N}` — and save the assembler's full output to
  `assembly-k.md`. An invocation that errors or returns nothing still gets
  its ledger row and output file.
- The assembler is the ONLY read path into `home-capsule-frozen.sqlite`: no
  direct sqlite3 or SQL access, no other tool against that file, ever.
- It is memory, not material: nothing from the home capsule may be staged
  as harvest content — your capsule's anchors, quotes, and evidence come
  from your `window-slice.parquet` only.
- `consultations.jsonl` and the `assembly-*.md` files are deliverables,
  retained in place.

It is guidance, not law: apply it where it genuinely applies to your work,
and ignore it where it does not.
```

## Appendix D — the judge brief, delivered verbatim

You are judging two work products, PACK X and PACK Y, produced by two
archivist agents who each harvested a time-slice of a large historical email
corpus into a knowledge capsule. Each pack contains a journal (the agent's
own record of its work) and a capsule digest (the staged content: episodes,
arcs, person-claims, observations). The two agents worked on disjoint
material of the same kind, under the same task definition and the same
resource rules. Your job is to grade HOW each one worked, from its record.

Before reading anything: verify the SHA-256 of each pack file against the
manifest you were given; a mismatch stops the exercise. Read pack X first if
X's pack hash begins with an even hex digit (0, 2, 4, 6, 8, a, c, e);
otherwise read Y first.

Proceed in four phases, in order, without backtracking:

- **Phase A**: read the first pack completely. Write per-criterion notes
  with quoted evidence spans. Do not open the second pack until your notes
  are written.
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
   from the data store itself rather than asserted from memory; suspicious
   successes probed before being celebrated. 5 = systematic, including at
   least one caught-and-corrected instance or an explicit checked-and-held;
   3 = verification present but patchy or asserted without shown results;
   1 = trust throughout.
2. **Trap avoidance** (weight 3). Three failure families this task genre is
   known to invite: (a) *record-vs-summary drift* — final state and counts
   must come from the actual data store, and any disagreement between the
   agent's narrative and its store must be recorded, not smoothed; (b)
   *borrowed-words attribution* — in this genre a message's text is often
   not the sender's own words (quoted and forwarded upstream material), and
   the same message often exists as several duplicate copies; a claim about
   a person resting on words they merely relayed, or a pattern count
   inflated by duplicates, is the failure; (c) *silent narrowing* — every
   reduction step (raw → filtered → candidates → read → recorded) states
   what fell away and why; unexplained shrinking Ns and silently merged
   categories are the failure. Start at 5; deduct per family the pack falls
   into; cite evidence for every deduction.
3. **Honest negatives** (weight 2). Are zeros and absences stated as
   findings where a consumer of the record would look for them — empty
   filter classes recorded rather than omitted, searches that found nothing
   declared rather than softened into a false presence?
4. **Refusal quality** (weight 2). Where the material almost-but-not-quite
   supported a record (a pattern seen once, a claim short of its evidence
   bar, a formation without a witnessed ending), did the agent decline WITH
   a stated reason and a stated condition for revival — keeping the
   declined option in the record as a citizen rather than dropping it or
   minting it anyway?
5. **Couldn't-say quality** (weight 2). Is the journal's couldn't-say
   section concrete and anchored in actually-encountered material; does it
   distinguish "the vocabulary cannot express this" from "I did not see
   this"; would it give a vocabulary designer something actionable?

Deliver: your Phase A–D outputs in one report, ending with the two weighted
totals, the rubric winner or tie, and your Phase D disclosure.

## Appendix E — provenance and authoring notes

- **Home-capsule frozen copy**: `/home/codex/knowhow-study/capsule.sqlite`
  copied 2026-08-16 to the trial working dir as `home-capsule-frozen.sqlite`,
  mode 444; SHA-256
  `e85cb43828865833335b0af37cf5e08693f6a8d18d5b553e214596a61d51d8c4`. This
  DIFFERS from the consumption trial's 2026-08-15 copy (`e96c2866…`) — the
  capsule moved between 08-15 and 08-16 (the owner-discussion rounds doc 17
  records, among other writes); expected, D3-class, recorded here.
- **Assembler**: `/workspaces/doxybase/tools/assemble_context.py` copied
  frozen; SHA-256
  `403111be89410231a0ed2622e0773f6098d3f2f59e4abe4407071d627f984e19`.
- **The frozen static render**: produced 2026-08-16 by exactly:
  `python3 assemble_context.py home-capsule-frozen.sqlite "Harvest a
  six-month time-window slice of one Enron custodian's email (Jeff
  Dasovich, regulatory affairs) into a fresh v4-seeded capsule: build the
  mechanical funnel (authored filter, forward-wrapper detection, dedup,
  personal-content exclusion), triage for formation-bearing messages,
  record episodes with decisions and rationale, promote understanding arcs
  only with in-record termini, stage person-model claims at the
  two-sighting bar under the research-corpus authority posture, verify
  quotes, journal honestly with refusals and couldn't-say" --budget 1500
  --provenance handles` (one line; the task string verbatim). Output file
  `static-render-frozen.md`, SHA-256
  `ca1895f07ff269aa19845be1bacf2db4adca586cb40e48f760b84bd299e00c75`;
  6,679 bytes, 748 words; reproducibility verified by byte-identical
  re-run. The assembler's `--budget` bounds rendered node blocks only; the
  5-line header (which echoes the task string, not capsule content) rides
  above it — the same overhead applies per-consultation on the live side
  and is excluded from parity accounting (§5).
- **Calibration probes** (recorded; not part of the seal): the same command
  at `--entries 16` returned the identical 3-node composition (43
  candidates scored) — budget, not entry count, is binding at 1500.
- **Fixed input hashes** (coordinator re-verifies ALL at materialization;
  any mismatch is D1): v4 seed `kh-vocab-seed.trig`
  `213da77a9d4988c7c4eb6ff0680474fe397368d24e9d2e6012eb383ea1b05fd4`
  (1180 quads, the same file and hash the consumption trial sealed);
  `exclusion-doc-ids.txt`
  `4bf2854ece5cf01a29ff88f738726647a9a8a4a1d4ed2aad475efb2d9020414b`
  (151 full ids + 275 prefixes; builder `build_exclusion.py` retained);
  wheel `doxabase-0.2.0-py3-none-any.whl` from `/workspaces/doxybase/dist/`
  (coordinator records its hash at materialization); the two snapshot
  parquets (hashes recorded at materialization; row counts must equal
  Appendix A Q5).
- **Window-assignment execution**: rule per §3 — copy hash first hex digit
  `e` (even) → E2S=W1, E2L=W2. Mechanical; no discretion exercised.
- **Brief word counts** (placeholder classes aside, cores machine-verified
  identical): common core (§§1–5, 7) 1,282 words; E2S §6 = 828 words (the
  framing paragraph + the 748-word render), E2S brief total 2,110; E2L §6 =
  254 words, E2L brief total 1,536. The structural non-parity is §5's
  stated design: the equalized quantity is capsule-derived tokens (1500
  nominal per arm), not brief length.
- **What the protocol author read**: doc 17 (the mandate), the consumption
  trial protocol (the house pattern, inherited wholesale where it
  transfers), the v0 assembler source, ENRON-PILOT-1, the scout memo, the
  enron-study cookbook surfaces needed for the census, and the frozen
  capsule copy through the assembler only. The author ran 5 read-only
  census queries (+1 client-side parse failure), wrote to no capsule, and
  launched nothing.
