# AIS Expertise Trial — the Scratch-vs-Caveats-vs-Expert Exploration Protocol (AIS-X)

**Committed BEFORE any trial agent runs** (doc 15 §4's pre-commitment requirement;
the seal-before-trial heuristic applied, as always, to the trial that tests the
program). **Date**: 2026-08-16. **Author**: the AIS-expertise-trial protocol
author, on the owner's own design (owner round recorded 2026-08-17, home-capsule
observation `bbbf391b-5fa7-4c57-af1e-badaae9ecaf3`): "if the big idea is that
know-how powers expert knowledge, we probably want to give the agents a pretty
unexplored area where they have to be quite creative and take major leaps... too
much process guidance and scaffold reduces the ceiling"; the AIS-data trial where
"the nuances of where the test agent effortlessly outperforms it might be very
informative"; and partial-capsule ablation "e.g. data deficiencies (so it does
not waste time) but not higher-level methods of analysis and meaning-finding."
This file is the seal: the task and its target, the three arm briefs (verbatim,
appendices), the A1 caveat render (verbatim), the mechanical metrics, the NEW
reinvention-cost instrument with its pre-committed trap list, the judged rubric,
the owner's impressiveness layer, blinding, deviation classes, and what counts
as a win. Nothing may be adjusted after the first arm launches; deviations
report under §12. The coordinator records this file's SHA-256 in the trial
record at launch, before any arm runs.

## 1. The trial in one paragraph

The live-retrieval trial (ENRON-2) proved, at n=1, that WHEN capsule memory is
assembled matters more than THAT it is assembled — on a harvest task whose
process was heavily scaffolded. The owner's critique of exactly that family:
scaffold lowers the ceiling; the know-how thesis needs an arena where creative
leaps are possible and an expert should *visibly* outperform. This trial builds
that arena. Three cold agents receive the same open task — investigate a
genuinely capsule-unstudied, data-rich region of the AIS feed (the Hawaiian
Islands box, §3) and deliver their three most interesting, defensible findings
about the world, each with its full evidence chain — with identical data
access, identical recording deliverables, and NO analytic scaffold. The delta
is purely what each arm knows at the start and can learn from memory along the
way: **A0 SCRATCH** gets the task and neutral schema basics only; **A1
CAVEATS** adds a static, mechanically-extracted render of the AIS capsule's
data-deficiency layer (the KnownCaveat registry, the owner's exact suggested
cut — deficiencies yes, methods and meaning-finding no); **A2 EXPERT** adds the
full frozen AIS capsule behind the v0.5 budgeted assembler with an
ENRON-2-style consultation protocol and a demand-side capability statement.
Measurement is three-layer: MECHANICAL (the house M-metrics adapted, plus the
trial's new instrument — REINVENTION COST, a pre-committed trap list diffing
each arm's work against the capsule's recorded traps: hit, never-noticed, or
independently rediscovered, with findings-corruption enumerated); BLIND-JUDGED
rigor (J1–J5 adapted); and — new and headline, per the owner's design intent —
**EXPERT-IMPRESSIVENESS: the owner himself ranks the three arms' stripped,
unlabeled findings packets** on interestingness, depth, and does-it-surprise,
on his own timeline. The ablation logic is explicit (A2>A1>A0 predicted per
layer; partial orderings each carry a named meaning), and the null is live and
honest: if a scratch agent matches the expert arm at this ceiling, the
accumulated know-how carries less transferable value than the thesis claims —
worth knowing. All three harvests are real study material regardless: the
region has never been touched, and three independent capsules of it join the
study either way.

## 2. Design summary

| | A0 SCRATCH | A1 CAVEATS | A2 EXPERT |
|---|---|---|---|
| Task | the §3 target, verbatim | identical | identical |
| Data access | full S3 (query.py pattern, credentials env) | identical | identical |
| Query budget | ~150 ledgered S3 queries | identical | identical |
| Schema basics | neutral render, brief §4 | identical | identical |
| Deficiency layer | none | static caveat render, brief §6 (Appendix C) | via consultation (and whatever it pulls) |
| Methods / meaning-finding | none | none | full frozen AIS capsule via v0.5 assembler ONLY |
| Consultation budget | — | — | 4000 tokens, ≤12 consultations, `--describe` once free |
| Harvest capsule | fresh, v4-seeded (1180 quads) | identical (own copy) | identical (own copy) |
| Model / sessions | recorded model, 1 session (+≤2 continuations) | identical | identical |
| Told of comparison | no | no | no |

The three briefs share sections §1–§5 and §7 word-identically (machine-verified
from one template; placeholder class: working-dir name only). The delta is §6:
absent for A0, the caveat render for A1, the consultation protocol plus
capability statement for A2. **Parity note, stated honestly**: unlike ENRON-2,
this trial does NOT equalize capsule-derived tokens across arms — the
inequality IS the experiment (an ablation of information regimes, not a
token-matched mechanism comparison). A1's §6 is ~1,900 words static; A2's §6 is
~600 words plus a 4,000-token live allowance; A0's §6 is nothing. Directions
recorded, not corrected.

## 3. The task target and its census

**The task, verbatim in every brief** (placeholder-free, identical):

> Investigate the maritime world of the Hawaiian Islands as seen in this AIS
> dataset — all vessel activity in the box latitude 18.0 to 23.5 N, longitude
> −161.5 to −154.0 (WGS84), 2024-01-01 through 2025-12-31 — and deliver your
> THREE most interesting, defensible findings about the world, each with its
> full evidence chain. "About the world" means about vessels, fleets, routes,
> industries, infrastructure, or behaviour — not about the dataset's file
> format. How you investigate is entirely yours.

**Why Hawaii** (the author's census, 2026-08-16, read-only; full record
Appendix A):

- **Genuinely unstudied.** A full-literal scan of the AIS capsule (observations,
  claims, map, patterns, evidence) finds the region's ONLY touches are: (a) two
  quotations of the provider-FAQ coverage sentence ("US coasts plus Alaska,
  Hawaii, Guam and Puerto Rico"); (b) one terminal datum in a Puget Sound
  story (THAT'S LIFE's single Maui ping, a coverage-exit reading); (c) the
  941-gear-beacon population's bounding box brushing Hawaii. Zero hits for
  Honolulu, Hilo, Kahului, Nawiliwili, Lahaina, Kona. No method exemplar, no
  vessel story, no claim, no caveat, no dwell/story coverage is anchored in the
  region. (The scan also confirmed the alternatives: Alaska would have been
  ideal but is EMPTY in this bucket — see Appendix A Q1/Q2, a census finding in
  its own right; Guam is thin; Puerto Rico is touched by two vessel stories.)
- **Data-rich, verified** (Appendix A Q3–Q5): continuous coverage, no dead
  months — ~5,000 index rows and 440–560 active MMSIs per month across all 24
  months; ~81,000 broadcast rows and ~175 broadcasting MMSIs per sampled day.
  Fishing is the largest vessel class (~145–158 MMSIs/month — the Honolulu
  longline fleet), plus ~40 tugs, 44–69 cargo/tanker, 12–37 passenger. Spatial
  structure confirmed: a dominant Oahu/Honolulu hub (1,023 distinct MMSIs at
  one 0.1° cell) with neighbor-island nodes.
- **Open enough for leaps.** An island economy supplied almost entirely by sea,
  a major US fishing fleet, inter-island logistics, transpacific arrivals, and
  a receiver network whose geometry the arms must reason about themselves. The
  census deliberately verified VOLUME only, not phenomena — the author did not
  pre-explore what is interesting there (contamination discipline; the risk
  that the region holds fewer than three genuinely interesting findings per
  arm is a recorded counterweight, §13.9).
- **Trap-dense.** Nearly the whole caveat registry is live here: sentinel
  speeds, the CET timestamp bug, the missing day, placeholder statics and the
  2025 encoding shift, identity year-constancy, name quoting, the hourly
  cadence artifact, harbor-fleet false pairs (Honolulu!), Class-B duty cycles
  (recreational craft), coverage-geometry gap reading (inter-island channels,
  transpacific departures). The reinvention-cost instrument has a full field
  of live traps to observe.

**Eligibility rules** (identical, all briefs, hard): findings must be about
the region; queries against `s3://ais-noaa` are unrestricted (out-of-box
context — e.g., a Hawaii vessel's mainland legs — is legitimate evidence); no
other data source, no web, no repo, no study journals, no capsule other than
the arm's own (plus, for A2 only, the frozen study capsule through the
assembler). **The quarantine is instruction-based, classed honestly**: the
feed (≈14.6M index rows, ≈5.3 billion broadcast rows) is too big to snapshot,
so unlike ENRON-2's construction-based window slices, out-of-scope access here
is forbidden by instruction and audited from artifacts (ledger + scripts +
journal), not made impossible. This is a stated retreat; §13.1 carries it. The
bucket itself is verified clean of capsule-derived artifacts (Appendix A:
top-level prefixes are `broadcasts/` and `index/` only — all M12/M13/M14
products live on local disk outside the arms' reach).

## 4. Conditions

- **Agents**: three cold analyst agents, one per arm. Plus coordinator,
  preparer, measurer, judge (§10) — the four graded-path agent roles (arms,
  preparer, measurer, judge) use the SAME model, the program's standard trial
  consumer (Sonnet-class); coordinator records the exact model id BEFORE the
  first launch. The OWNER is the fifth role and is a human; nothing about his
  layer is model-bound. Arms are not told of the comparison, the other arms,
  the judge, or the owner layer; each is told (truthfully) it is the analyst
  for an open exploration tranche of the AIS study program and that its
  capsule and journal become program assets.
- **Working dirs** (coordinator creates before launch): `/home/codex/ais-x-a0/`,
  `/home/codex/ais-x-a1/`, `/home/codex/ais-x-a2/`, each containing: a venv
  with the doxabase wheel from `/workspaces/doxybase/dist/` (same file all
  arms, hash recorded) plus duckdb/pandas/pyarrow/numpy (same versions,
  recorded); `bridge.py` (study-standard bridge, pointed at the arm's own
  `capsule.sqlite`); `query.py` (the study-standard S3 query helper —
  credentials from environment, never echoed into artifacts); `kh-vocab-seed.trig`
  (v4 seed, 1180 quads, SHA-256
  `213da77a9d4988c7c4eb6ff0680474fe397368d24e9d2e6012eb383ea1b05fd4` — the
  same file and hash ENRON-2 sealed, re-verified 2026-08-16); and `BRIEF.md`
  (Appendix B with the arm's §6 per Appendix C/D; A0's brief has no §6).
  **A2's dir additionally contains** `assemble_context.py` (v0.5, SHA-256
  `47c1421a3ce902f15da00e1bb89386dcb49bcbb5cbaeca4fedebe6cb8b8208f4`) and
  `ais-capsule-frozen.sqlite` (read-only copy of
  `/home/codex/ais-study/capsule.sqlite`, file mode 444; authoring-time hash
  `3acf6905ab82b3b72c27707e78d62805b6951df08fd535317d5810fcd5506efe`; the
  coordinator hashes the copy at materialization — drift from the
  authoring-time hash is D3, recorded; after first launch the copy may not
  change at all, D1). At launch the coordinator diffs each delivered BRIEF.md
  against its appendix (any difference beyond the working-dir placeholder is
  D1), verifies every hash, and verifies A0's and A1's dirs contain NO capsule
  copy and NO assembler (presence is D1).
- **Budgets**: (a) S3 queries: ~150 data-bearing queries per arm, every query
  ledgered to `query-ledger.jsonl` BEFORE firing (`{"n": k, "at": ISO-8601,
  "purpose": "...", "script": "path-or-inline"}`); client-side errors that read
  no data are ledgered but not counted; ≤10% overrun D2, more D1. (b) A2
  consultations: 4000 tokens total (sum of `--budget` arguments) across ≤12
  consultations, `--provenance handles` fixed, one `--describe` free
  (uncounted), each ledgered to `consultations.jsonl` before firing with full
  output saved to `assembly-k.md`; an erroring or nothing-strong consultation
  still gets its ledger row and file, counts against the ≤12, and spends no
  tokens. (c) Local compute: unmetered, but every analysis step scripted and
  retained.
- **Sessions**: one analyst session per arm; up to two continuation sessions
  on context exhaustion permitted by design (recorded); a fourth is D2.
- **Launch order**: sequential, A0 → A1 → A2 (pre-committed: ascending
  know-how, so no coordinator contact with a later arm can carry anything
  backward). Coordinator interaction limited to launch and collection;
  content-neutral infrastructure help D2; content steering D1.
- **Order of operations**: (1) this protocol committed, SHA recorded → (2)
  coordinator materializes dirs (hashes, model id, wheel version) → (3) A0
  runs → (4) A1 runs → (5) A2 runs → (6) coordinator freezes all three dirs
  (SHA-256 over journal, findings, capsule, ledgers, scripts, assembly
  outputs) → (7) preparer builds judge packs AND owner packets, seals
  assignments (§10) → (8) measurer counts (§6–§7) and judge grades (§8), in
  either order or parallel, neither seeing the other's output → (9) owner
  ranks (§9), on his own timeline → (10) verdict assembled per §11 → (11)
  trial record written. Steps 8 may be reported as interim results while
  waiting on 9; the verdict exists only after 9.

## 5. The briefs and the deltas

- **Common core** (Appendix B §§1–5, 7; word-identical across arms outside the
  working-dir placeholder): role and task (the §3 target verbatim); access and
  eligibility rules; the neutral schema basics; recording deliverables; the
  honesty frame. **The scaffold line is drawn deliberately and recorded**: the
  briefs impose the RECORDING scaffold (journal, scripted queries, ledger,
  capsule staging with evidence, conforming end state) because it is the
  measurement substrate and the program's genuine deliverable — but impose NO
  analytic scaffold: no funnel prescription, no method steps, no phenomena
  list, no "look at fishing" hints. The ceiling the owner asked for is opened
  in the analytic dimension; the recording dimension stays disciplined so the
  arms remain measurable and their capsules remain assets. The deep recording
  craft (indexicality, honest negatives, refusal quality) is deliberately NOT
  taught in the brief — it is part of what the judged layer measures and part
  of what A2's capsule knowledge should improve.
- **A0 §6**: absent (section numbering runs §5 → §7 with a one-line "no
  further briefing material" placeholder, so the numbering itself is not a
  tell to the judge later — packs never contain briefs anyway).
- **A1 §6** (Appendix C verbatim): one framing paragraph — "the program has
  previously recorded, from other work on this same feed, the following
  registry of known data deficiencies and encoding traps; they are offered so
  you do not lose time or findings to them; apply them where they genuinely
  apply" — followed by the caveat render. **The render is mechanically
  extracted** (rule pre-committed here): every `map`-graph node typed
  `KnownCaveat` whose IRI slug does NOT match `^m[0-9]+-` (those are failure
  modes of capsule methods A1 does not receive), PLUS exactly one pre-declared
  exception, `m3-silence-is-not-dark`, whose slug is method-bound but whose
  content is the feed-coverage deficiency the owner's cut plainly intends
  (named in the design decision itself). Each included caveat renders its
  `label`, `caveatDescription`, `impact` (where present), and severity
  localname, verbatim, sorted by IRI. That yields **13 of the 29 registry
  caveats**; the 16 excluded are method-bound (their content teaches
  method-M1/M2/M3/M4/M5/M13/M14 analysis moves — the meaning-finding layer the
  owner's cut withholds). **Known impurities of the cut, directions recorded**
  (§13.7): the included render leaks opaque method tokens ("M13", an N=200
  threshold, a session-14 reference, a dangling observation pointer) — tokens
  without definitions, slightly enriching A1 toward A2, i.e., biasing AGAINST
  finding an A2−A1 gap (conservative for the ablation); and one deficiency
  family lives OUTSIDE the registry entirely (the GPS position-quality /
  frozen-coordinate artifact, encoded as M12 screen parameters and survey
  observations — 6–10% of stationary windows) and is therefore honestly
  absent from A1's render, slightly weakening A1 (direction also recorded; it
  remains in the trap list, Appendix G #30).
- **A2 §6** (Appendix D verbatim): the capability statement (what the memory
  covers — adapted from the assembler's `--describe` output and the author's
  capsule census; the owner's directive that the agent must understand what it
  has access to), then the consultation protocol per the ENRON-2 live arm:
  command form, budget, ledger-before-firing, assembler-is-the-only-door, and
  the **memory-not-material rule adapted for a shared feed**: nothing served
  from the study capsule may be presented as a finding or as evidence — every
  finding's evidence chain must rest entirely on the arm's own ledgered
  queries; memory may steer, never substitute. (Structural protection: the
  capsule contains nothing about the region, so a capsule-lifted "finding"
  would also fail the §3 region rule.) Consultation guidance quotes the
  demand-side line: consult before investing effort something like it may have
  been met before, when the data surprises you, and before creative leaps.
- Both §6 deltas close with the identical guidance-not-law sentence used by
  the house briefs.

## 6. Measurement layer 1 — MECHANICAL (counted from artifacts, no judgement)

Counted by the MEASURER identically for all three arms from the frozen dirs;
per-metric better-direction and tie rules fixed here; a tie counts to neither
arm of a pair. All pairwise comparisons computed (A2:A0 headline, A2:A1,
A1:A0). **Naming collision, stated once**: metrics below are house M-metrics
(M1–M7); the AIS capsule's analysis methods are always written method-M1 …
method-M14. House M6 (op efficiency) stays dropped as in ENRON-2 — S3 query
counts are budget discipline and secondary observations, not a verdict metric
(penalizing exploration breadth would fight the trial's own ceiling-raising
purpose). The layer is 6 metrics; pairwise threshold per the house rule: ≥4
of 6, with the metric-drop rule (≥4 of 5, ≥3 of 4 if metrics drop, D2).

- **M1 — staging-failure rate** = (staged revisions reaching validation and
  failing, refused at apply, or closed discarded for cause) ÷ (applied
  revisions). Pure tool-envelope schema errors excluded (the platform's
  designed targeted-error teaching). Source: bridge_log.jsonl + revision rows.
  Lower; tie exact.
- **M2 — evidence-reproduction failure rate** (the genre's quote check:
  numbers are this task's quotes) = (load-bearing numeric assertions in
  FINDINGS.md and staged claims/observations that fail to reproduce when the
  measurer re-executes the arm's own retained scripts/queries against the
  feed, within the assertion's own stated precision) ÷ (assertions checked).
  The measurer checks EVERY numeric assertion in the three findings' evidence
  chains and a pre-committed complete sweep of staged claim literals
  containing digits. Lower; tie exact. (Re-execution nonreproducibility from
  feed-side nondeterminism is investigated and, if confirmed feed-side, the
  assertion is excluded from both arms' denominators — D2 note.)
- **M3 — dead-anchor rate** = (IRI references resolving to no subject in the
  arm's capsule, plus data anchors — (mmsi, date) pairs and file paths cited
  in staged records — absent from the feed) ÷ (total such references). Lower;
  tie exact.
- **M4 — unverified-claim rate** = (checked journal claims contradicted by the
  arm's graph, ledgers, or artifacts) ÷ (claims checked). Claim classes,
  pre-committed — the measurer enumerates EVERY final-journal sentence in
  these classes: (a) numeric counts of queries, findings, capsule contents;
  (b) conformance / zero-staged-debt / parity claims; (c) universally
  quantified claims ("all", "every", "zero", "none"). Lower; tie exact. Full
  enumeration published.
- **M5 — coverage and evidence-chain completeness**, 0–10 checklist, one point
  each: (1) region definition restated with box edges and an explicit
  statement of what lies outside it; (2) data layers used enumerated (index /
  broadcasts / both, with row-count sanity checks); (3) every finding's
  evidence chain is complete — raw query → intermediate → conclusion with no
  unstated step; (4) every rate or count states its denominator (which days,
  which population, which filters); (5) data-quality screens stated per
  analysis, including empty ones; (6) each finding addresses at least one
  alternative explanation (artifact-vs-world) and says why it fails; (7)
  final capsule census stated WITH its method, and the method is a graph
  read; (8) revision accounting reconciles (every staged revision accounted
  for in bridge log and journal); (9) query-ledger reconciles (ledger count
  matches retained scripts; purposes present); (10) an explicit statement of
  what was NOT investigated. Higher; tie exact.
- **M7 — end-state integrity**, 0–3: +1 validate_graph scope=all conforms
  (measurer-verified on the capsule); +1 zero staged debt; +1
  observation/evidence parity. Higher; tie exact.

Reported alongside (NOT verdict inputs): query counts and their index/broadcast
split, wall time, session count and token cost, capsule content counts
(observations/claims/evidence), and — for A2 — everything in §7's consultation
tables.

## 7. Measurement layer 1b — REINVENTION COST (new, this trial's instrument)

The measurer diffs each arm's complete artifact set (journal, scripts, ledger,
findings, capsule) against the **pre-committed trap list** (Appendix G: all 29
KnownCaveat registry entries plus one registry-external deficiency found by
the author's coverage verification, each with an exposure trigger and
detection signatures). Per arm, per trap, exactly one verdict:

- **NOT-EXPOSED**: none of the arm's analyses trigger the trap (per the
  trap's exposure trigger). No credit, no penalty.
- **BRIEFED-APPLIED** (A1/A2 only): the trap was in the arm's render or a
  saved consultation output, and the artifacts show the corresponding screen/
  correction applied where exposed.
- **REDISCOVERED**: the arm, without having been served the trap, detected
  and handled it — journal statement plus a mechanical trace (a comparison
  query, a filter with a stated reason). Credit, with **cost counted**:
  ledgered queries and journal segments attributable to the discovery episode.
- **HIT-CORRECTED**: the arm produced a wrong intermediate attributable to
  the trap (per the signature), later caught and corrected it. Time/queries
  lost counted.
- **HIT-UNCORRECTED**: a wrong intermediate or a wrong finding-input
  attributable to the trap persists in the final artifacts.
- **UNNOTICED-EXPOSED**: exposed, no handling anywhere, no hit yet visible —
  the measurer then checks each of the arm's three findings' evidence chains
  against the trap and enumerates which findings are **potentially corrupted**
  by it (published per-finding, per-trap).

Aggregates, all published with full per-trap verdicts:

- **RC1 — corrupted-findings count** (verdict input): number of the arm's
  three findings whose evidence chain contains a HIT-UNCORRECTED or is
  enumerated potentially-corrupted under an UNNOTICED-EXPOSED trap. 0–3.
  Lower is better.
- **RC3 — trap burden** (verdict input) = (HIT-UNCORRECTED + UNNOTICED-
  EXPOSED) ÷ (all EXPOSED traps, i.e., everything except NOT-EXPOSED). Lower
  is better.
- **RC2 — reinvention spend** (diagnostic, NOT a verdict input — high spend
  with correct results is honest work, and it is the headline
  "cost-of-scratch" number the owner's design asks about): ledgered queries +
  session segments spent in REDISCOVERED and HIT-CORRECTED episodes.
- Role in the verdict (§11): RC1 and RC3 qualify the mechanical layer — the
  expert arm must be no more trap-corrupted than the arm it claims to beat.

## 8. Measurement layer 2 — the blind JUDGED rigor rubric

A separate judge (fresh agent, model recorded before it sees anything, no repo
access, no capsule bridge, no web) receives the three arms as **X**, **Y**,
**Z** (assignment sealed, §10) and grades each journal+capsule-digest+findings
pack on five criteria, each 1–5, each score requiring ≥2 cited evidence spans
(uncited scores invalid; a criterion with no evidence either way scores 2 with
a statement). Weighted total = Σ weight × score (max 60 per pack). Judge brief
is Appendix E verbatim; the judge never sees this protocol, any brief, the
caveat render, any consultation artifact, or any measurer output.

- **J1 — verification-before-trust** (weight 3): numbers re-derived before
  being relied on; suspicious or delightful results probed before celebrated;
  final census from the data store.
- **J2 — trap avoidance** (weight 3), three families defined without
  attribution: (a) **record-vs-summary drift** — final counts and state
  claims derived from the actual store, discrepancies recorded not smoothed;
  (b) **artifact-vs-world attribution** — this genre's signature lie: the
  data-collection machinery (encodings, sentinel values, receiver coverage,
  upstream processing conventions) manufactures patterns that look like
  vessel behaviour; a claim about the world resting on an unexamined
  machinery artifact is the failure; (c) **silent narrowing** — every
  reduction (raw → screened → analyzed → reported) states what fell away and
  why. Start at 5, deduct per family fallen into, evidence cited.
- **J3 — honest-negative recording** (weight 2): zeros, absences, and failed
  hunts stated as findings where a consumer would look.
- **J4 — refusal quality** (weight 2): near-findings declined WITH reasons
  and revival conditions — a fourth candidate rejected on the record, claims
  short of their evidence bar declined, one-sighting patterns docketed rather
  than minted.
- **J5 — couldn't-say quality** (weight 2): concrete, anchored in
  actually-encountered material; distinguishes cannot-know-from-this-data
  from did-not-look.

**Judge phases, in order, no backtracking**: verify pack hashes against the
preparer's manifest; read packs fully in sealed order (§10) writing
per-criterion notes after each before opening the next; score all 15 cells
with cited evidence; compute totals and the layer ordering (strict totals;
equal = tie at that boundary); record ANY suspicion about how the packs differ
in origin and whether it influenced grading; freeze.

## 9. Measurement layer 3 — EXPERT-IMPRESSIVENESS (the owner's layer, headline)

Per the owner's design intent ("genuinely surprise and impress us"), the
trial's headline layer is his judgement, collected under a short pre-committed
rubric (Appendix F verbatim):

- The PREPARER builds three **findings packets** — each arm's FINDINGS.md
  stripped per §10 (no arm identity, no mechanism traces, no consultation or
  render echoes) and labeled **P1/P2/P3** by the sealed hash rule.
- The COORDINATOR delivers the packets and Appendix F to the owner with the
  one-paragraph truthful frame fixed in Appendix F (three independent
  investigators, same region, same data, same resources; rank what they
  found) — and **waits: his timeline, no deadline**. Nobody follows up with
  content; a nudge, if ever, is scheduling-only.
- His rubric (Appendix F): rank the three packets overall, plus per-packet
  notes on three axes — **interestingness** (would you retell this finding?),
  **depth** (how far beneath the surface does the evidence chain go?),
  **does-it-surprise** (did you learn something you did not expect about the
  maritime world?). **Defensibility is explicitly NOT his axis** — the rigor
  judge owns it; he is asked to assume all three packets survived a rigor
  audit, and any rigor doubts he still forms are welcome as notes, not
  rank-drivers. One absolute question per packet ("independent of ranking:
  would this finding set have impressed you as genuinely new work on your
  data — yes or no?") de-zero-sums the ranking (§13.8).
- His blindness is to ARM IDENTITY only, never to the domain — he knows this
  data deeply (that is what makes him the expert judge) and may well
  recognize study-flavored moves; Appendix F asks him to record any origin
  suspicion after ranking, exactly as the machine judge does.

## 10. Blinding and roles

Six roles: COORDINATOR (materializes, launches, collects, freezes, records
hashes and model ids, delivers owner packets, assembles the verdict; knows
everything, grades nothing), PREPARER, MEASURER, JUDGE (all as in the house
pattern), the three ARMS, and the OWNER.

- **PREPARER** builds, from frozen artifacts: per arm, a judge pack (stripped
  journal + stripped flat capsule digest + stripped findings) and an owner
  packet (stripped findings only). **Excluded from packs and packets
  entirely**: briefs, ledgers, assembly outputs, the caveat render.
  **Redaction dictionary, pre-committed**: "consult", "consultation",
  "assemble", "assembler", "assembly", "working-memory", "capsule copy",
  "frozen capsule", "caveat registry", "KnownCaveat", "render", "know-how",
  "knowhow", "brief", "budget", "v0.5", "ais.study/caveat", "ais.study/
  pattern", "richcanopy.org", arm ids ("A0","A1","A2","ais-x-a0/a1/a2", any
  casing), any sentence quoting or describing either §6 mechanism, **plus the
  dynamic rule**: every label, IRI, and distinctive ≥4-word phrase appearing
  in the Appendix C render or in any of A2's `assembly-*.md` files enters the
  dictionary before packs are built. Replacements are seamless neutral
  paraphrase; every replacement logged to a sealed redaction ledger for
  post-verdict audit. **Honesty note carried to §13.5**: knowledge cannot be
  stripped — an arm that correctly names an obscure feed trap without showing
  the work of finding it is an intrinsic tell; the judge's and owner's
  suspicion disclosures are the instrument for that, not deeper redaction
  (which would destroy the graded substance).
- **Assignment seal** (total rule, no discretion): pack hash = SHA-256 over
  stripped journal ‖ capsule digest ‖ findings. Sort the three pack hashes
  lexicographically → **X, Y, Z** (judge) and, over the findings-packet
  hashes computed the same way, → **P1, P2, P3** (owner). Judge reading order
  = X, Y, Z. The preparer writes the full assignment (arm ↔ X/Y/Z ↔ P1/P2/P3,
  all hashes) to a sealed file whose hash the coordinator records BEFORE the
  judge is spawned or any packet leaves for the owner.
- **MEASURER** computes §6 and §7 on the real frozen artifacts (unblinded by
  necessity); publishes every judgement-bearing enumeration (M4 claims, M5
  checklist, M2 assertion sweep, all per-trap verdicts and per-finding
  corruption enumerations, A2 used-item verdicts). Never sees the judge's or
  owner's output before the verdict; they never see the measurer's.
- **A2 consultation accounting** (measurer): R1 consultation count and
  timing; the **used test** exactly as ENRON-2 sealed it (item = `## ` node
  block; used iff its IRI, exact label, or a contiguous ≥8-word
  whitespace/case-normalized span appears in journal, scripts, findings, or
  capsule literals AFTER the consultation's timestamp; pulls themselves don't
  count); aggregate precision (item-weighted); nothing-strong outputs excluded
  from the precision denominator (v0.5's honest emptiness is not noise);
  recall-gap replays of every stated-need passage in ALL THREE arms' journals
  against the frozen capsule + assembler (budget 500, handles) — for A0/A1
  this measures what the memory COULD have answered, the trial's
  cost-of-absence number; reproducibility check: every ledgered consultation
  re-run; non-identical output investigated (D2, metrics from saved outputs).

## 11. What counts as a WIN (sealed)

Pre-committed predictions, all three layers: **A2 > A1 > A0**. The layers:

- **Layer M** (mechanical): pairwise winner = strictly better on ≥4 of 6
  metrics, **qualified by reinvention cost**: to take the pair, the winning
  arm must also have RC1 ≤ and RC3 ≤ its opponent (at least one strict unless
  both are 0/0 — two clean arms qualify on the metrics alone).
- **Layer J** (judged): pairwise winner = strictly higher weighted total.
- **Layer O** (owner): the overall ranking, plus the per-packet absolute
  answers.
- **A2's consultation qualification** (for any A2 win claim that credits the
  MEMORY rather than the agent): ≥3 ledgered consultations beyond the free
  `--describe`; at least one fired AFTER the arm's first finding-candidate
  appears in its journal (the mid-investigation letter) that serves ≥1 item
  passing the used test; aggregate used-precision ≥ 1/3 (the ENRON-2 floor,
  same pre-justification: reachable at v0-scale serving sizes; below it the
  pulled context did no attributable work and a win belongs to the agent).

**Named verdicts** (exactly one is declared):

- **VOID**: any D1. The region is spent (§13.11); a re-run needs a fresh
  target and a fresh seal.
- **EXPERT WIN** (the full claim): A2 first in the owner's ranking AND A2
  takes layer J against both other arms AND A2 takes layer M against A0 AND
  the consultation qualification holds. The owner's predicted nuance is then
  reported as the trial's yield: WHERE A2 outperformed (which traps, which
  depths, which surprises — the "nuances of where the test agent effortlessly
  outperforms").
- **KNOW-HOW WIN, RIGOR FORM**: A2 takes layers M and J against A0 (with
  qualification) but not the owner's top rank — the memory measurably
  improved the work but not the wow; bears on the thesis's rigor half only.
- **IMPRESSIVENESS WITHOUT SEPARATION**: A2 first in the owner's ranking but
  layers M and J both unseparated or lost — the leaps came without measurable
  mechanical/rigor advantage; reported as bearing on the ceiling thesis, with
  the explicit caution that one ranking at n=1 is the weakest signal class in
  the trial.
- **CAVEATS SUFFICE**: A1 ties or beats A2 on ≥2 layers while both beat A0 on
  ≥2 — the deficiency slice carries the transferable value; the owner's
  cheapest cut is the product recommendation, and the methods/meaning-finding
  layer's value claim fails at this diameter.
- **UNUSED INSTRUMENT**: A2 wins layers but the consultation qualification
  fails (never consulted, launch-only, or precision < 1/3) — the win cannot
  be attributed to live memory; reported by name (a doc 17 datum: offered
  memory that goes unused indicts the demand side).
- **NULL**: every other combination — split layers, ties, A0 parity. Honest
  and live: at this ceiling, with this instrument, accumulated exploration
  know-how did not separate from cold competence. The null still pays (§13.12).

**Ablation reading, pre-committed** (reported with any verdict): the A1
position localizes value. A1 ≈ A2 > A0 → deficiencies carry it. A2 > A1 ≈ A0
→ methods/meaning-finding carry it. A2 > A1 > A0 → both, deltas localize.
**A1 > A2 anywhere** is reported by name as a **caveat-sufficiency anomaly**
(static deficiency briefing beat full live memory there — evidence about
retrieval cost/noise, not about memory content). **A0 > A1** anywhere is
reported as **briefing drag** (the render cost more attention than it saved —
the consumption-trial null's shape, worth recognizing on sight).

## 12. Deviation classes

- **D1 — invalidating**: delivered brief differs from its appendix beyond the
  working-dir placeholder; A0/A1 in possession of any assembler or capsule
  copy; A2 reading `ais-capsule-frozen.sqlite` by any path other than the
  assembler; study-capsule content presented as a finding or as evidence; an
  arm accessing `/home/codex/ais-study/`, the repo, study journals, any
  search engine or web resource, or another arm's dir; arms exchanging
  material; an arm learning of the comparison, judge, or owner layer; query
  budget >165 data-bearing; consultation tokens >4400 or count >12; different
  models across the four graded-path agent roles; the judge learning the
  assignment or seeing unstripped artifacts or measurer output; the owner
  told arm identities before his ranking is frozen; rubric, metrics, trap
  list, or win criteria edited after first launch; content steering of a
  running arm; the frozen capsule copy changing after first launch.
- **D2 — recorded, verdict stands with caveat**: query or consultation-token
  overrun ≤10%; late-ledgered query or consultation (enumerated; still
  counts); a fourth session; content-neutral infrastructure help; a
  preparer redaction miss discovered post-verdict (verdict stands UNLESS the
  judge or owner, asked once, states the leak influenced their grading — then
  NULL); a metric the measurer cannot compute (drops pairwise from all arms;
  thresholds per §6); a consultation replay that does not reproduce
  byte-identically (saved outputs govern; mismatch reported); feed-side
  nondeterminism in an M2 re-execution (assertion excluded, noted).
- **D3 — noted only**: frozen-copy hash differing from the authoring-time
  hash recorded in §4 (the capsule may move between authoring and
  materialization; the freeze governs); MinIO hiccups/retries; cosmetic
  tooling differences; assembler v0.5 differing from the version ENRON-2
  sealed (expected — v0.5 post-dates that trial; hash fixed in §4).

## 13. Counterweights — what a win would NOT prove

1. **Eligibility is instruction-based, not construction-based** — a stated
   retreat from ENRON-2's materialized-slice quarantine, forced by data
   scale. Compliance is audited from artifacts, not guaranteed by
   architecture. A perfectly disciplined violation could evade the audit;
   the artifact-completeness rules (scripted queries, ledger-before-firing)
   narrow, not close, that door.
2. **Same-feed contamination is intrinsic and stated.** The capsule's
   know-how was recorded by sessions exploring THIS feed — different region,
   same data dialect. A2's advantage bundles feed-specific facts with
   transferable craft; the region boundary separates *findings*, not
   *fluency*. A win claims "accumulated exploration memory of a data world
   transfers to an unstudied region of that world" — NOT cross-domain
   transfer. (That narrower claim is exactly the owner's proposed experiment.)
3. **n=1 per arm.** Run-to-run variance unmeasured; one strong or weak run
   anywhere reorders layers by luck. No generality across regions, models,
   or moments.
4. **v0.5 bounds A2's retrieval.** Phrasing sensitivity is documented from
   ENRON-2; a poor walk can starve a willing consumer. A2 losses route
   partially to the instrument (the interpretation discipline of the ENRON-2
   protocol applies: precision < 1/3 indicts the walk before the thesis).
5. **Blinding is partial by nature, twice over.** Work rhythm and unearned
   trap-knowledge can identify arms to the judge; the owner may recognize
   study-flavored moves. Both record suspicion; neither is eliminated.
6. **The brief-writer effect.** One author chose the region, the box, the
   budgets, the A1 cut rule and its single exception, and the task phrasing.
   A different region or phrasing yields a different trial. Claims attach to
   THIS target and THIS protocol.
7. **The A1 cut is imperfect in both directions**, pre-measured: method
   tokens leak in (conservative against A2−A1 separation); one non-registry
   deficiency family is absent (conservative against A1−A0 separation on
   that trap). Both directions recorded in §5; neither is corrected.
8. **Ranking is zero-sum.** Three genuinely strong packets still produce a
   last place. The absolute per-packet question (§9) is the mitigation, not
   a cure.
9. **The region's ceiling is unverified by design.** The census proved
   volume and continuity, not wonder — the author deliberately did not
   pre-explore phenomena. Hawaii may hold fewer than three impressive
   findings per arm; a compressed impressiveness range flattens layer O
   through no arm's fault.
10. **Teaching vs licensing, and training priors.** Sonnet-class models may
    know AIS folklore (sentinels, MMSI structure) from training. A
    REDISCOVERED verdict credits the arm's judgement AND its priors,
    inseparably; BRIEFED-APPLIED credits attention, not knowledge. The claim
    stops at "the information regime changed measured behaviour."
11. **The seal is spent on this run.** Win, lose, or null: the region, the
    render, the trap list, and the frozen copy are burned for comparison
    purposes; a successor trial needs fresh allocation.
12. **A null still pays**: three fresh capsules of an unstudied region join
    the study; the trap list's per-arm verdicts are an empirical audit of
    the caveat registry itself (which recorded traps actually bite cold
    agents — registry curation data); A0's rediscovery ledger prices from
    scratch what the capsule sells; and every stated-need replay feeds the
    v1 assembler's requirements corpus.

## 14. After the verdict

The trial record (docs/journal/trials/, alongside this protocol) reports: the
pairwise metric tables with full enumerations; all per-trap verdicts and
per-finding corruption enumerations; the consultation tables and used-item
verdicts; the judge's report verbatim; the owner's ranking and notes verbatim
(his artifact, quoted with his consent per the shareability flow); the
assignment unseal; the deviation ledger; the named verdict per §11 with the
ablation reading. All three capsules join the AIS study as region tranches
pending the owner's shareability pass — nothing leaves a capsule without the
owner. New caveats discovered by ANY arm route to the study curator for
registry staging (whichever arm found them — a scratch arm's fresh trap is as
real as an expert arm's). RC verdicts flow to the caveat registry as curation
data; consultation ledgers and recall-gap replays flow to the v1 assembler
requirements; friction and couldn't-say yields flow to the distiller ledger
regardless of verdict. If EXPERT WIN: the owner's "nuances of where"
observations become the seed of the partial-capsule ablation program's next
cut, and the v1 assembler inherits a second live-use requirements corpus. If
CAVEATS SUFFICE: the deficiency-render becomes a standard product surface
(cheap, static, shippable) and the methods-layer value question returns to
the bench with better instruments. If NULL: doc 17's memory thesis takes its
first genuine dent at high ceiling, and honesty requires the program to say
so in those words.

---

## Appendix A — the census record (author, 2026-08-16, read-only)

**Method**: DuckDB + httpfs via the study-standard `query.py` against
`s3://ais-noaa` (MinIO; endpoint and credentials from environment, never
echoed into any artifact). **Ledger**: 5 data-bearing queries of the ≤8
budget, plus 2 metadata listing operations and 1 client-side 404 path error
that read no data (enumerated below — by the strictest count, 8 S3-touching
operations). Capsule reads were local, read-only (`mode=ro`), and unbudgeted.

- **Q1 — Alaska monthly census** (index, box lat ≥ 50.0 ∧ (lon ≤ −130.0 ∨
  lon ≥ 165.0), grouped by month): **60 index rows TOTAL across 2024–2025**
  (peak month: 2024-07 with 23 rows / 21 MMSIs). Alaska is effectively
  absent from this bucket. Candidate rejected — and the discrepancy with the
  provider FAQ's coverage sentence (quoted in the capsule) is itself a datum
  the study should eventually record.
- **Q2 — whole-feed footprint** (index, 5° bands, >500 rows): the feed lives
  in CONUS coastal bands (top: 45/−125 Puget Sound–Columbia 2.41M rows;
  25/−85 1.69M; 40/−75 1.55M) plus **Hawaii** (20/−160: 119,259 rows, 1,865
  MMSIs; 15/−160: 5,145 rows, 1,162 MMSIs), **Guam** (10/140: 19,761 rows,
  1,938 MMSIs), and Puerto Rico/USVI (15/−65: 193,793 rows). Nothing at ≥50°N.
- **Q3 — Hawaii monthly** (index, box lat 18.0–23.5, lon −161.5..−154.0):
  every one of the 24 months populated; idx_rows 4,738–6,219/month; distinct
  MMSIs 436–558/month; fishing (type-30) MMSIs 142–158/month — the largest
  single class; passenger 12–37; cargo+tanker 44–69; tug/tow 37–46. No dead
  months, no year asymmetry. (Full table in the working dir's census log.)
- **Q4 — Hawaii spatial structure** (index, 0.1° cells, ≥25 distinct MMSIs):
  Honolulu cell 21.3/−157.9 dominates (49,519 rows, 1,023 MMSIs), with a
  ring of Oahu cells (477, 455, 415 MMSIs), Kona coast 19.6/−156.0 (145
  MMSIs), and ~20 further cells ≥85 MMSIs. Clear hub-and-spokes structure
  for the arms to discover in their own right.
- **404 (no data read)**: first broadcast-layer path guess
  (`broadcasts/2024/2024-03-15.parquet`) — corrected from the capsule's
  recorded pathTemplate (`ais-{date}.parquet`), not by probing.
- **Q5 — Hawaii broadcast density** (broadcasts, the two files
  `ais-2024-03-15` + `ais-2025-03-15`, box filter): 81,239 and 81,165 rows;
  173 and 177 distinct MMSIs. Broadcast-level work in the region is cheap
  (~1% of a day-file).
- **Listings (2 ops)**: `glob('s3://ais-noaa/*/*')` (returned nothing — the
  bucket has no two-level objects) and `glob('s3://ais-noaa/*/*/*')` →
  top-level prefixes are **`broadcasts` and `index` only**: the bucket holds
  no capsule-derived artifacts (all method products — stops series, outage
  census, M14 segments — live on local disk outside the arms' reach).
- **Unstudied verification** (local, read-only): full-literal LIKE scan over
  the AIS capsule's observations/claims/map/patterns/evidence graphs for
  {Alaska, Bering, Aleutian, Anchorage(-AK), Dutch Harbor, Kodiak, Juneau,
  Ketchikan, Cook Inlet, Valdez, Hawaii, Honolulu, Guam, fishing, trawl,
  crab, seiner, cruise, weekly, weekend, …}: Hawaii's only touches are the
  FAQ coverage quotation, the THAT'S LIFE Maui terminal ping, and the
  941-beacon bbox; no method, claim, story, or caveat is anchored in the
  region. Fishing appears only as class-count table entries and one
  mis-typed dredge — fishing-fleet behaviour is unstudied.
- **Capsule census** (for §5's capability statement and Appendix G): 29
  KnownCaveat nodes; 48 pattern nodes = 14 methods (method-M1…method-M14) +
  ~20 vessel stories + 5 literature reconciliations + exemplars; 149
  observations; 102 claims; 175 evidence nodes; 14 datasets; 5 executable
  query snippets; 4 method contracts; 14 invariants; 15 parameters; aisv:
  ontology 345 quads.

## Appendix B — the common arm brief, delivered verbatim as `BRIEF.md`
(sections §1–§5, §7 identical for all arms; §6 per Appendix C/D; A0's §6 is
the single line shown)

```markdown
# AIS-X — open exploration brief (AIS study program, region tranche)

## 1. Role and task

You are the analyst for an open exploration tranche of the AIS study program.
This is a real study tranche, not an exercise: your capsule and journal become
program assets. Your task:

Investigate the maritime world of the Hawaiian Islands as seen in this AIS
dataset — all vessel activity in the box latitude 18.0 to 23.5 N, longitude
−161.5 to −154.0 (WGS84), 2024-01-01 through 2025-12-31 — and deliver your
THREE most interesting, defensible findings about the world, each with its
full evidence chain. "About the world" means about vessels, fleets, routes,
industries, infrastructure, or behaviour — not about the dataset's file
format. How you investigate is entirely yours.

Interesting and defensible are both load-bearing: a finding should make a
knowledgeable reader want to retell it, and it should survive a hostile audit
of every step from raw data to conclusion. Where the two pull apart, record
the tension honestly rather than sacrificing either. Be honest everywhere —
the record is the deliverable.

## 2. Access rules (hard)

- Working directory: `{WORKDIR}`. Everything you produce lives here. Do not
  read or write outside it; the venv and installed doxabase wheel inside it
  are part of it.
- Your data surface is the object store reachable through `query.py` (DuckDB
  over S3; credentials come from the environment — never copy them into
  files, capsule literals, journals, or reports). Layout in §4.
- No repository access, no study-journal access, no other capsules, no search
  engines, no web, no documentation beyond this brief and your working
  directory's contents.
- `bridge.py` is the ONLY door to your capsule. If you must close a failed
  staged row, the documented core-API fallback is permitted for that single
  operation, recorded in your journal.
- Corpus-separate: nothing you do writes anywhere but your own working
  directory and your own `capsule.sqlite`.

## 3. Query discipline and eligibility (hard)

- Budget: about 150 data-bearing S3 queries. Ledger EVERY query to
  `query-ledger.jsonl` BEFORE firing it, one JSON object per line:
  `{"n": k, "at": "<ISO-8601 UTC>", "purpose": "<one line>", "script":
  "<file or inline SQL>"}`. A query that errors client-side still gets its
  ledger row (marked) and does not count against the budget. Keep every
  analysis step as re-runnable scripts with their outputs retained.
- Your findings must be about the region defined in §1. Queries outside the
  box are allowed where they serve a regional finding (a Hawaii vessel's
  history elsewhere is legitimate evidence); a finding about somewhere else
  is out of scope.
- Record counts honestly at every reduction step: when a population shrinks
  (filtered, screened, sampled), say what fell away and why.

## 4. The data

One S3 bucket, `s3://ais-noaa`, holding an AIS feed of broadcasts received
around the USA (NOAA-style), 2024-01-01 through 2025-12-31, in two layers:

- `s3://ais-noaa/broadcasts/{year}/ais-{date}.parquet` — one file per UTC
  day, one row per received AIS broadcast (~7M rows/day feed-wide). Columns:
  mmsi (Maritime Mobile Service Identity of the transmitting station);
  base_date_time (source timestamp string as received); timestamp (parsed
  broadcast timestamp); date (UTC day, matches the file); latitude,
  longitude (degrees WGS84); sog (speed over ground, knots); cog (course
  over ground, degrees); heading (true heading, degrees); vessel_name;
  imo (reported IMO number string); call_sign; vessel_type (AIS ship-type
  code: 30 fishing, 31/32 towing, 52 tug, 60–69 passenger, 70–79 cargo,
  80–89 tanker); status (navigational status code: 0 under way engine, 1
  anchored, 5 moored, 15 undefined); length, width (metres); draft (reported
  draught, metres); cargo (cargo code); transceiver ('A'/'B');
  h3_res15 (H3 cell id); geometry (point geometry).
- `s3://ais-noaa/index/{year}/ais-{date}.parquet` — one file per UTC day,
  one row per (mmsi, date) (~15k rows/day feed-wide): message_count,
  first_timestamp, last_timestamp, duration_s, centroid_lat, centroid_lon,
  min/max_lat, min/max_lon, distance_m (summed inter-fix track distance),
  h3_cell_count, sog_min/mean/max, max_inter_msg_speed_ms (max implied
  inter-fix speed), and distinct-value lists for the day: vessel_names,
  imos, call_signs, vessel_types, lengths, widths, drafts, cargos,
  status_codes, transceiver_classes.

The index is ~500x cheaper to scan than broadcasts; how you use the two
layers is yours to decide.

## 5. Recording (the program's standing discipline)

- Your first bridge call creates your capsule; import `kh-vocab-seed.trig`
  via `import_bundle`; confirm `validate_graph` scope=all conforms (0
  results) BEFORE any staging.
- Journal INTO the capsule as you go: record observations liberally — what
  you tried, what you saw, what surprised you, what failed — with evidence
  for anything you rely on. Dense agent-written prose in literal values is
  welcome; do not restrain observation volume. The observation stream is the
  durable original; `JOURNAL.md` is the human-readable render.
- Stage your three findings as claims with evidence; every number a finding
  rests on must trace to a ledgered query. Validate after every apply; end
  with zero staged debt.
- Verify before you trust: re-derive any number you are about to rely on or
  publish, and probe results that look too good (or too strange) to be true
  before celebrating them.

## 6. {ARM-SPECIFIC — Appendix C (A1) / Appendix D (A2); for A0 this section
reads exactly: "No further briefing material."}

## 7. Deliverables

- `FINDINGS.md`: your three findings. For each: the finding in one
  paragraph; why it is interesting; the FULL evidence chain — every query
  (by ledger number), every intermediate, every verification step, and the
  capsule IRIs of its staged claim and evidence; and what would have to be
  true for the finding to be wrong.
- `JOURNAL.md`, in the program's journal style: setup log; the
  investigation as it actually unfolded, dead ends included; every
  population reduction with counts and reasons; the final capsule state
  (from a graph read); a friction section (what the tooling made hard); a
  couldn't-say section distinguishing what this data cannot know from what
  you did not look at; and refusals — finding-candidates you declined, with
  reasons and revival conditions.
- Working artifacts retained in place: scripts, query outputs,
  `query-ledger.jsonl`, staging payloads.
- `capsule.sqlite`: validate_graph scope=all conforming, zero staged debt,
  observation/evidence parity. Run `export_preflight` and report its result;
  the shareability review is the owner's — nothing leaves the capsule.
- Do not commit anything to any repository; the coordinator collects your
  working directory when you report completion.
```

## Appendix C — Arm A1 (CAVEATS) brief §6, delivered verbatim

```markdown
## 6. Known deficiencies of this data (recorded by the program)

The program has previously recorded, from other work on this same feed, the
following registry of known data deficiencies and encoding traps. They are
offered so you do not lose time or findings to them. It is guidance, not law:
apply it where it genuinely applies to your work, and ignore it where it does
not.

### AIS sentinel values encode 'not available'  [severity: Moderate]
sog=102.3, cog=360, heading=511 are AIS 'not available' sentinels, present in
broadcasts and propagated into index sog_max/sog_mean aggregates. Filter them
before computing speed statistics.
Impact: Unfiltered sog_max=102.3 rows look like impossible 102-knot sprints.

### base_date_time string format shifts at the 2024/2025 boundary
The base_date_time column (the authoritative ordering column) is an ISO-like
string whose separator changes between years: 2024 files use 'T'
(2024-05-04T00:00:06), 2025 files use a space (2025-05-04 19:57:31).
CAST(base_date_time AS TIMESTAMP) in DuckDB parses both correctly, which is
why five sessions used the column without noticing; string-level operations
(cross-year text sorting, prefix matching, substring time extraction) will
misbehave. Same shape as sentinel-encoding-shift-2025 but on the timestamp
column itself. Found by the session-14 phase-2 BLIND contract regeneration;
curator-verified live 2026-07-12.
Impact: String-level use of base_date_time across the year boundary silently
misorders or mismatches; always CAST to TIMESTAMP.

### A routine top-of-the-hour reporting burst inflates same-second
boundary-sharing counts and is NOT a reception outage  [severity: Moderate]
In the first ~5 minutes of essentially every UTC hour, broadcast message
volume RISES from a baseline of ~5,700/min to ~8,900-9,000/min before
decaying back to baseline (spot-checked directly against
s3://ais-noaa/broadcasts/ for multiple dates in both 2024 and 2025). This is
a volume INCREASE, not a reception gap, and it is not confined to any one
date -- 77-94% of moderate-size (8-199 vessel) stop-boundary-sharing clusters
detected by M13 fall within 90 seconds of a whole-hour mark, versus 15-30%
for clusters at or above the 200-vessel outage-qualification threshold.
Consequence: any analysis that treats same-second or same-minute boundary
sharing in the stops series as evidence of a reception event must screen for
this artifact (e.g. via M13's N=200 threshold, or by checking hour-of-day
alignment directly) or it will systematically over-count small 'outages' that
are really just this routine cadence effect. Mechanism unconfirmed from this
feed alone (plausibly: many Class A transponders schedule periodic
static/position reports from a shared, GPS-synced clock, concentrating report
density near round-minute marks).
Impact: Any per-second or per-minute clustering analysis on stop start/end
timestamps (or on broadcasts' base_date_time) that does not screen for this
will over-count small feed-outage-like events near whole-hour marks.

### Identity fields are year-constant per MMSI: renames can only be dated to
a year boundary  [severity: Severe]
Static identity (names, IMO, dims) is near-frozen per file-year in BOTH the
index and the raw broadcasts: 2,736/2,738 index name transitions land exactly
on Jan 1, and raw broadcasts flip renames at the year boundary even when the
true rename happened mid-year (311050400). Upstream mechanism unconfirmed;
one vessel (369914086) shows a surviving mid-year toggle, so it is not an
absolute annual snapshot. Treat within-year identity timing from this feed as
unreliable; date real renames behaviourally (gaps, draft, movement).
Impact: Mid-year identity changes are invisible or displaced to Jan 1;
year-boundary diffs overstate simultaneity of changes.

### Index 'list' columns mostly hold exactly one value; identity is
day-constant  [severity: Moderate]
Despite the VARCHAR[]/DOUBLE[] schema, vessel_names, imos, call_signs,
vessel_types, lengths and widths never contain more than one element per
(mmsi,date) row: the upstream feed carries one static-identity record per
MMSI per day. Only drafts (max 6), cargos (max 5), transceiver_classes (max
2) and status_codes (max 8) genuinely vary within a day. Consequences:
same-day identity flips cannot exist in this data; identity-change detection
operates at day granularity; an empty list means the field was not broadcast
that day.
Impact: Methods that expect intraday name/IMO conflicts will find none by
construction - not because vessels behave.

### M3 core limitation: silence means 'not received', not 'transponder off'
[severity: Severe]
This is a terrestrial-receiver feed covering US coasts plus Alaska, Hawaii,
Guam and Puerto Rico. A vessel sailing beyond receiver range goes silent
with its transponder on; most large-displacement gaps are ocean transits
(coverage_exit_voyage), not dark activity. True AIS-off detection at sea is
impossible from this data alone; silent_in_place events at a berth are
usually routine power-downs. Treat gap classes as descriptive segmentation,
and only escalate residual anomalies (e.g. implausible_jump, or in-coverage
displacements inconsistent with the vessel's habits).

### Static and positional fields come from different raw AIS message types,
merged onto one row by upstream processing  [severity: Moderate]
Raw AIS separates positional reports (Messages 1/2/3 for Class A; Message 18
for Class B, sent every few seconds while underway) from static/voyage data
(Message 5, Class A only, sent roughly every 6 minutes) -- confirmed
distinct message types per USCG NAVCEN documentation (MarineCadastre 'Other
AIS Resources'). This flat per-broadcast-point product (the 2015-onward
CSV/parquet convention; 2009-2015 data was instead normalized across three
related tables per the AIS FAQ) presents both message families as columns on
one row: static fields (vessel_name, imo, call_sign, length, width, draft,
cargo) are carried forward onto positional rows rather than reflecting an
actual Message-5 transmission at that row's own timestamp. Expect: static
fields to lag or lead the true moment they changed; and prefer
message-tagged/raw NMEA data over this feed for forensics-grade
static/positional joins (expert tradecraft note).
Impact: Row-level static fields (name/IMO/dims/draft/cargo) are 'last
known', not 'as-of this exact position fix'; treating them as synchronized
with the row's timestamp overstates precision, especially for
identity-change and draft-event timing.

### Day 2024-08-26 missing from both layers  [severity: Moderate]
Both broadcasts/ and index/ have no file for 2024-08-26 (730 files each
instead of 731 for 2024-01-01..2025-12-31). Any per-day time series or gap
analysis must treat that day as no-coverage, not vessel silence. Evidence:
observation 'coverage-gap-2024-08-26' in the observations graph.
Impact: Vessel 'gaps' spanning 2024-08-26 are partly or wholly a data
outage; day-count denominators over 2024 must use 365 observed days, not 366.

### vessel_name may embed literal quote characters; normalize before
comparing  [severity: Moderate]
Some vessel_name values are wrapped in literal double quotes (CSV-escape
residue upstream), and the same hull can alternate between quoted and
unquoted forms across days. Strip double quotes and trim whitespace (e.g.
trim(replace(name,'"',''))) before any distinct-count, join, or rename
detection on names.
Impact: Unnormalized name comparisons manufacture fake renames/conflicts;
the worst 'identity flipper' in the data is pure quoting noise.

### 2024 encodes missing statics as placeholders (IMO0000000, 0-dims); 2025
leaves them empty  [severity: Severe]
Normalize before any cross-year identity or dimension comparison: treat
imo='IMO0000000', vessel_type=0, length=0, width=0, draft=0 (2024 style) as
equivalent to NULL/empty (2025 style). Otherwise every placeholder vessel
appears to 'lose' its IMO/type/dims at 2025-01-01.
Impact: 42% of 2024 index rows carry IMO0000000; unnormalized cross-year
diffs generate ~50k fake identity-change events at the boundary.

### Identity and static fields are self-reported and unverified
[severity: Severe]
vessel_name, imo, call_sign, vessel_type, length, width, draft (and mmsi
itself) are typed into the transponder by the operator. Expect: multiple
names per MMSI per day (index lists), IMO0000000 placeholders, cloned/shared
MMSIs, and dimension/draft values that change without physical cause. Treat
identity as a time-varying claim, never a key.
Impact: Joining on vessel_name or trusting a single day's identity fields
silently merges or splits vessels.

### heading and cog switch from numeric sentinel to true NULL at the
2024/2025 boundary; sog does not  [severity: Severe]
Sampling one day per year via
read_parquet('s3://ais-noaa/broadcasts/*/*.parquet'): heading=511 appears in
3,943,345 rows on 2024-03-15 and 0 rows on 2025-03-15 (which instead has
3,983,560 true NULL headings); cog=360 appears in 1,204,379 rows on
2024-03-15 and 0 rows on 2025-03-15 (1,387,273 NULLs instead). sog=102.3
appears in BOTH years (15,804 in 2024; 19,767 in 2025) and sog is never NULL
in either year. This matches the NOAA data dictionary's 2025-present schema
explicitly marking heading/cog/sog nullable ('Null Allowed: Y') where the
2018-2024 dictionary page has no equivalent column -- but only heading and
cog actually changed encoding in the real feed; sog kept its literal 102.3
sentinel in both years. Treat heading=511 / cog=360 as 2024-only 'not
available' encodings and NULL as the 2025+ encoding for those two fields
specifically; continue to treat sog=102.3 as the sentinel in both years.
This is the same-shaped bug as the placeholder-statics shift (imo/
vessel_type/length/width/draft) but for the positional-quality fields
heading/cog.
Impact: A query that only checks for the numeric sentinel (511/360) will
silently miss all 'not available' heading/cog rows in 2025+; a query that
only checks IS NULL will miss all of them in 2024. sog is not affected by
this specific issue.

### timestamp column is UTC-mislabelled CET/CEST; use base_date_time as
truth  [severity: Severe]
broadcasts.timestamp = base_date_time parsed as Central European time:
subtract-shifted by 1h (winter) / 2h (EU summer) from true UTC, with flips
at EU DST switch dates. Column affected: broadcasts.timestamp; index
first_timestamp/last_timestamp inherit it. base_date_time (string, true UTC,
spans exactly the file's named day) is authoritative. Within-day deltas are
unaffected except on the two EU switch days; cross-day and absolute-time
work (e.g. rendezvous timing, gap edges) must use base_date_time or correct
the offset.
Impact: Absolute event times are off by 1-2 hours season-dependently; naive
UTC treatment misdates events near midnight and across DST switches.

It is guidance, not law: apply it where it genuinely applies to your work,
and ignore it where it does not.
```

*(Render provenance: extracted 2026-08-16 from the AIS capsule's map graph,
rule per §5 — 12 non-method-slugged KnownCaveats + the pre-declared
m3-silence-is-not-dark exception, labels/descriptions/impacts verbatim,
severity as localname, sorted by IRI with the exception in IRI position. Two
editorial normalizations only, both mechanical and recorded: internal
`caveat/<slug>` cross-references replaced by the referenced caveat's
description where the referent is not itself included (one instance:
placeholder-shift reference inside the heading/cog caveat), and the
column-name phrase "stops-series-full's start_ts/end_ts" in the cadence
caveat's impact line replaced by "stop start/end timestamps" (the dataset
named exists only inside the study). The coordinator re-runs the extraction
script at materialization and diffs against this appendix; any difference is
D1.)*

## Appendix D — Arm A2 (EXPERT) brief §6, delivered verbatim

```markdown
## 6. The program's memory of this data (consult it live)

Your working directory contains a read-only frozen copy of the AIS study
program's capsule (`ais-capsule-frozen.sqlite`) and the program's
working-memory assembler (`assemble_context.py`). The capsule is the
program's accumulated memory of sixteen recorded analysis sessions on this
exact feed: fourteen analysis methods (identity-change classification,
multi-emitter/shared-MMSI detection, silence-gap segmentation, draft/cargo
event reading, co-movement and fleet detection, port-call detection,
per-day track-state classification, draft-event context, two-point-shuttle
census, stop-verification checklists, berth-vs-anchor discrimination, an
event-level stops series, feed-outage detection, and placeholder-MMSI track
segregation) with their contracts, tuned parameters, invariants, and
executable SQL; a 29-entry registry of known data deficiencies and encoding
traps; some twenty deeply-verified vessel stories; provider-documentation
reconciliations; and 149 observations and 102 claims with evidence. It has
NEVER analyzed your region — no method exemplar, story, or claim touches the
Hawaiian Islands; what it knows is the data's dialect and the craft of
reading it, not your answers.

Start with the free orientation call (it does not count against your
budget):

    python3 assemble_context.py ais-capsule-frozen.sqlite --describe

Then consult it at any point in your work — before starting, mid-analysis,
mid-staging, whenever a question arises that the program's history might
answer:

    python3 assemble_context.py ais-capsule-frozen.sqlite "<your question>" --budget N --provenance handles

Consult it enthusiastically: BEFORE you invest effort in anything the
program may have met before, WHEN the data surprises you, and BEFORE
creative leaps — a two-minute consultation that saves a wrong afternoon is
the entire point of memory. Concrete, specific questions retrieve better
than abstract ones.

Rules (hard):

- Total budget across all consultations: **4000 tokens** (the sum of your
  `--budget` arguments), across **at most 12** consultations. Spend it in
  the chunks you find useful; unspent budget is fine.
- `--provenance handles` always (fixed for this tranche).
- Ledger EVERY consultation to `consultations.jsonl` BEFORE firing it, one
  JSON object per line: `{"n": k, "at": "<ISO-8601 UTC>", "question":
  "<verbatim>", "budget": N}` — and save the assembler's full output to
  `assembly-k.md`. An invocation that errors or returns nothing strong
  still gets its ledger row and output file (it counts as a consultation
  and spends no tokens).
- The assembler is the ONLY read path into `ais-capsule-frozen.sqlite`: no
  direct sqlite3 or SQL access, no other tool against that file, ever.
- It is memory, not material: nothing served from the program's capsule may
  be presented as a finding or cited as evidence. Every finding's evidence
  chain rests entirely on your own ledgered queries against the data.
  Memory may tell you where to dig and what to distrust; the digging is
  yours.
- `consultations.jsonl` and the `assembly-*.md` files are deliverables,
  retained in place.

It is guidance, not law: apply it where it genuinely applies to your work,
and ignore it where it does not.
```

## Appendix E — the judge brief, delivered verbatim

You are judging three work products, PACK X, PACK Y, and PACK Z, produced by
three analyst agents who each ran an open investigation of the same region of
a large vessel-tracking dataset and delivered three findings with evidence
chains, a journal, and a knowledge capsule. The three worked independently on
the same material of the same kind, under the same task definition and the
same resource rules. Your job is to grade HOW each one worked, from its
record — not which findings are more interesting (that is someone else's
axis; assume all three finding sets are of legitimate interest).

Before reading anything: verify the SHA-256 of each pack file against the
manifest you were given; a mismatch stops the exercise. Read the packs in the
order X, Y, Z.

Proceed in five phases, in order, without backtracking: **A** — read pack X
completely; write per-criterion notes with quoted evidence spans before
opening the next pack. **B** — the same for Y. **C** — the same for Z.
**D** — score all 15 cells (5 criteria × 3 packs), each 1–5; every score must
cite at least 2 evidence spans from the pack it grades; if a criterion has no
evidence either way in a pack, score that cell 2 and say so; uncited scores
are invalid. **E** — compute each pack's weighted total (weights below, max
60); state the strict ordering or ties; then record any suspicion you formed
about how the three packs differ in origin and whether it influenced any
score; then stop — no revisions after E.

The five criteria:

1. **Verification before trust** (weight 3). Did the agent re-derive numbers
   before relying on or publishing them; probe suspicious or delightful
   results before celebrating; read final state from the data store rather
   than assert it from memory? 5 = systematic, with at least one
   caught-and-corrected or checked-and-held instance; 3 = present but patchy
   or asserted without shown results; 1 = trust throughout.
2. **Trap avoidance** (weight 3). Three failure families this genre invites:
   (a) *record-vs-summary drift* — final counts and state claims must come
   from the actual store, and any disagreement between narrative and store
   must be recorded, not smoothed; (b) *artifact-vs-world attribution* — in
   this genre the data-collection machinery itself (field encodings,
   special marker values, the geography of receivers, upstream processing
   conventions) manufactures patterns that can look exactly like real-world
   behaviour; a claim about the world resting on an unexamined machinery
   artifact is the failure — look for whether the agent asked "could the
   pipeline have made this?" before "what does this mean?"; (c) *silent
   narrowing* — every reduction step (raw → screened → analyzed → reported)
   states what fell away and why; unexplained shrinking Ns are the failure.
   Start at 5; deduct per family the pack falls into; cite evidence for
   every deduction.
3. **Honest negatives** (weight 2). Are zeros, absences, and searches that
   found nothing stated as findings where a consumer of the record would
   look for them, rather than omitted or softened?
4. **Refusal quality** (weight 2). Where material almost-but-not-quite
   supported a finding (a pattern seen once, a claim short of its evidence,
   a tempting story the data cannot complete), did the agent decline WITH a
   stated reason and a revival condition — keeping the declined candidate in
   the record as a citizen rather than dropping it silently or minting it
   anyway?
5. **Couldn't-say quality** (weight 2). Is the journal's couldn't-say
   section concrete and anchored in actually-encountered material; does it
   distinguish "this data cannot know this" from "I did not look"; would it
   give the program something actionable?

Deliver: your Phase A–E outputs in one report, ending with the three
weighted totals, the ordering or ties, and your Phase E disclosure.

## Appendix F — the owner's packet brief, delivered verbatim

*(Delivered by the coordinator with packets P1, P2, P3. No deadline; nothing
in the trial moves until this returns.)*

Three independent investigators were each given the same open task on your
AIS data: investigate the Hawaiian Islands box (an area the study has never
touched) and deliver their three most interesting, defensible findings about
the world, each with its evidence chain. Same data, same resources, same
brief. The packets are their findings, identities withheld and light
redaction applied; a separate blind judge is auditing their rigor, so for
ranking purposes assume all three survived that audit — defensibility is
deliberately NOT your axis here.

Please:

1. **Rank the three packets overall** (1 = the work you would most want more
   of), on these axes: **interestingness** — would you retell this finding
   to someone who knows the sea?; **depth** — how far beneath the surface of
   the data does the evidence chain actually go?; **does-it-surprise** — did
   you learn something you did not expect about the maritime world? Brief
   notes per packet on each axis are more valuable to us than scores.
2. **Per packet, one absolute answer**, independent of the ranking: would
   this finding set have impressed you as genuinely new work on your data —
   yes or no?
3. **After** your ranking is written: note any suspicion you formed about
   which investigator produced which packet (or how they differed in what
   they knew), and whether it influenced your ranking. Then send everything
   back as-is — no revisions after that note.

Any rigor doubts you form anyway are welcome as notes; they route to the
audit, not the ranking. Take whatever time it takes.

## Appendix G — the reinvention-cost trap list (pre-committed, mechanical)

All 29 KnownCaveat registry entries plus one registry-external deficiency
(#30, found by this protocol's coverage verification). Per trap: the
**exposure trigger** (which analysis moves make it live) and the **detection
signature** the measurer applies. Verdict vocabulary per §7. General
signature rules: REDISCOVERED requires BOTH a journal/ledger trace of the
discovery AND a mechanical handling (filter, correction, screen) predating
any dependent finding work; HIT requires a concrete wrong intermediate or
wrong finding-input attributable to the trap (measurer re-derives);
UNNOTICED-EXPOSED is exposure with neither. For A1/A2, BRIEFED-APPLIED
requires the handling without claiming discovery credit. Where a signature
says "re-run with/without", the measurer executes the arm's own retained
script both ways and diffs.

1. **timestamp-cet-parse-bug** — Trigger: any use of `timestamp`,
   `first_timestamp`, or `last_timestamp` for absolute times, cross-day
   ordering, or event timing. Signature: re-derive any published absolute
   time from base_date_time; a 1–2h discrepancy in a stated time = HIT; a
   journal/ledger trace comparing the two columns + subsequent
   base_date_time use = REDISCOVERED; timing work exclusively on
   base_date_time with no comparison trace = check whether choice was
   stated (stated → BRIEFED-APPLIED/REDISCOVERED per arm; unstated →
   NOT-EXPOSED only if no absolute-time claim exists).
2. **missing-day-2024-08-26** — Trigger: any per-day series, activity
   calendar, or gap analysis spanning Aug 2024. Signature: a finding or
   intermediate treating 2024-08-26 as vessel behaviour (fleet-wide
   "silence", gap counts inflated by it) or a 366-day 2024 denominator =
   HIT; a journal note of the absent file with corrected denominators =
   REDISCOVERED.
3. **ais-sentinel-values** — Trigger: any speed/cog/heading statistic.
   Signature: re-run the arm's speed aggregations with sog=102.3 filtered;
   a changed load-bearing number = HIT (UNCORRECTED if published); an
   explicit sentinel filter + note = REDISCOVERED/BRIEFED-APPLIED; max-speed
   or "fastest vessel" findings are the prime corruption check.
4. **sentinel-encoding-shift-2025** — Trigger: heading/cog "not available"
   handling in any cross-year work. Signature: a 2024-only numeric-sentinel
   check or a 2025-only NULL check in retained scripts spanning both years
   = HIT if a dependent number changes under the dual check; dual handling
   with note = REDISCOVERED/BRIEFED-APPLIED.
5. **placeholder-encoding-shift-2025** — Trigger: any cross-year identity,
   dimension, or "vessel lost its IMO/type" comparison. Signature:
   fake-loss events at 2025-01-01 in intermediates or findings = HIT;
   normalization of IMO0000000/0-dims to NULL with note = REDISCOVERED/
   BRIEFED-APPLIED.
6. **identity-year-constant** — Trigger: any rename/identity-change dating,
   or any claim timing an identity event within a year. Signature: a
   mid-year rename date asserted from statics alone, or a Jan-1 change read
   as a real simultaneous event = HIT; a journal trace discovering the
   year-boundary pile-up (e.g., a transition-date histogram) = REDISCOVERED.
7. **index-lists-are-daily-constant** — Trigger: intraday identity-conflict
   analysis on index lists. Signature: a claim that same-day identity
   flips are absent as vessel behaviour (rather than by construction), or
   effort ledgered hunting intraday conflicts the schema cannot hold = HIT
   (time-loss form); a note deriving the day-constancy = REDISCOVERED.
8. **name-quoting-artifact** — Trigger: name-based joins, distinct-counts,
   or rename detection. Signature: re-run with trim(replace(name,'"',''));
   changed distinct-counts or a quoted/unquoted pair read as a rename =
   HIT; normalization present with note = REDISCOVERED/BRIEFED-APPLIED.
9. **self-reported-identity** — Trigger: any join on vessel_name, or any
   single-day identity fact used as a key. Signature: a finding merging or
   splitting physical vessels via name-join (measurer probes the finding's
   MMSI set for name collisions/variants) = HIT; identity treated as
   time-varying claim with cross-checks (IMO+call_sign+dims) = REDISCOVERED/
   BRIEFED-APPLIED.
10. **base-date-time-format-shift-2025** — Trigger: string-level operations
    on base_date_time across the year boundary (sorting, prefix matching,
    substring time extraction). Signature: re-run with CAST; changed
    ordering/matching = HIT; CAST discipline with note = REDISCOVERED/
    BRIEFED-APPLIED; CAST used without note and no string ops = NOT-EXPOSED.
11. **hourly-reporting-cadence-artifact** — Trigger: sub-minute clustering
    of broadcast or stop-boundary timestamps; any "synchronized event"
    reading. Signature: a burst at a whole-hour mark read as a real-world
    event without an hour-alignment screen = HIT; the screen present with
    note = REDISCOVERED/BRIEFED-APPLIED.
12. **message-type-merging** — Trigger: any claim synchronizing a static
    field (name/dims/draft/cargo) with a specific position fix at row-level
    precision. Signature: a finding whose timing precision depends on
    static-field freshness at the row's own timestamp = HIT; a stated
    lag/lead allowance = REDISCOVERED/BRIEFED-APPLIED.
13. **m3-silence-is-not-dark** — Trigger: any interpretation of a
    transmission gap. Signature: silence at sea read as "went dark"/
    transponder-off/evasion without a coverage argument = HIT (the genre's
    cardinal corruption; every finding with a gap in its chain is checked);
    a reasoned coverage-exit reading (receiver geography argued from the
    data, e.g. last-fix positions at box edges) = REDISCOVERED/
    BRIEFED-APPLIED.
14. **m3-coverage-geometry-blind** — Trigger: classifying gaps by
    displacement alone. Signature: a coverage/dark claim whose endpoints
    the measurer finds inconsistent with the arm's own coverage evidence
    (e.g., both endpoints in areas the arm's own data show as
    well-received) = HIT; endpoint-context checking = REDISCOVERED.
15. **m3-class-b-duty-cycle** — Trigger: gap/activity statistics over
    populations including Class B / leisure craft (large in this region).
    Signature: a behavioural finding driven by leisure-craft lifestyle
    gaps without a duty/class screen = HIT; duty-cycle or class filtering
    with note = REDISCOVERED/BRIEFED-APPLIED.
16. **m3-centroid-endpoints** — Trigger: precise gap-endpoint or same-day
    position claims from index centroids. Signature: an endpoint claim on
    a high-movement day (distance_m large) stated at centroid precision =
    HIT if load-bearing; broadcast-level endpoint verification =
    REDISCOVERED/BRIEFED-APPLIED.
17. **m2-day-granularity-no-localization** (generalized) — Trigger:
    multi-emitter/shared-MMSI claims from index signals alone. Signature:
    an emitter-count or emitter-location claim without broadcast-level
    clustering = HIT; clustering follow-up = REDISCOVERED.
18. **m2-dst-switch-days** — Trigger: single-day teleport/speed anomalies
    on 2024-03-31, 2024-10-27, 2025-03-30, 2025-10-26. Signature: an
    anomaly finding anchored on exactly those dates without the timestamp
    caveat = HIT; the date screen = REDISCOVERED.
19. **m2-gray-zone-and-sparse** (generalized) — Trigger: classifying MMSIs
    as shared/clean from threshold screens. Signature: a universal
    clean/shared claim without acknowledging the sparse-emitter and
    gray-zone escape classes = HIT if a finding depends on completeness;
    stated bounds = REDISCOVERED/BRIEFED-APPLIED.
20. **m1-placeholder-normalization-required** (generalized) — Trigger:
    year-boundary identity-change counting. Signature: identity-change
    event counts inflated by placeholder/quoting noise (measurer re-runs
    with normalization) = HIT; normalization first = REDISCOVERED/
    BRIEFED-APPLIED.
21. **m1-sister-vessel-confusion** (generalized) — Trigger: same-hull vs
    different-hull judgements on similar names. Signature: a fleet-serial
    name pair merged as one hull (measurer checks dims/IMO/callsign) =
    HIT; explicit sister-fleet handling = REDISCOVERED.
22. **m1-year-granularity** — Trigger: dating any identity change inside a
    year from statics. Signature: as #6's within-year form; behavioural
    dating (gaps/draft/movement) = REDISCOVERED.
23. **m4-draft-quality** — Trigger: draft-based cargo/loading inference.
    Signature: cargo claims on never-updating or zero-placeholder drafts
    (measurer checks the vessel's draft variance) = HIT; voluntary-field
    screening (nonzero, varying, type-appropriate) = REDISCOVERED/
    BRIEFED-APPLIED.
24. **m4-draft-update-lag** — Trigger: locating cargo operations from
    draft-change positions. Signature: a terminal/location claim from
    single-event positions on transit legs = HIT; modal clustering over
    many cycles = REDISCOVERED.
25. **m4-single-message-draft-glitch** — Trigger: any single draft event
    used as evidence. Signature: a load-bearing single event without
    multi-message corroboration (measurer pulls the day's broadcasts) that
    proves glitch-shaped = HIT; corroboration run = REDISCOVERED/
    BRIEFED-APPLIED.
26. **m5-day-centroid-resolution** (generalized) — Trigger: co-location or
    rendezvous claims from index day-centroids. Signature: a relationship
    claim without broadcast-level confirmation (proximity over hours,
    matched SOG) = HIT; confirmation run = REDISCOVERED.
27. **m5-harbor-fleet-false-pairs** — Trigger: any co-movement/
    relationship analysis (Honolulu's working fleets make this near-
    unavoidable if attempted). Signature: an operational-tie claim
    between vessels whose co-location sites are static (a mobility-style
    discriminator would score near zero — measurer computes it) = HIT;
    any mobility/wandering discriminator = REDISCOVERED/BRIEFED-APPLIED.
28. **m13-shoulder-undercounting** (generalized) — Trigger: attributing
    stop/silence boundaries to feed-wide events. Signature: outage-edge
    boundaries attributed to vessel behaviour (or vice versa) where the
    arm's own event extent shows gradual shoulders = HIT; shoulder
    awareness = REDISCOVERED.
29. **m14-track-count-imprecision** (generalized) — Trigger: emitter/track
    censuses of shared or placeholder MMSIs. Signature: an exact emitter
    count claimed from greedy segregation alone = HIT; "at least N" with
    identity corroboration = REDISCOVERED.
30. **position-quality artifact (registry-external)** — GPS-frozen and
    glitched position clouds: ~6–10% of stationary windows carry
    implausible radii/implied speeds (recorded in the study as M12's
    position_quality_suspect screen and the session-12 survey; NOT in the
    KnownCaveat registry, NOT in A1's render — all three arms face it
    equally except through A2's retrieval). Trigger: stationary-geometry
    or anchorage-behaviour analysis. Signature: a swing/dwell-geometry
    claim on windows whose max implied inter-fix speed or radius shape is
    glitch-class (measurer screens the arm's windows with the recorded
    thresholds) = HIT; any position-quality screen = REDISCOVERED (A2:
    BRIEFED-APPLIED if served).

## Appendix H — provenance and authoring notes

- **Authoring-time hashes** (coordinator re-verifies at materialization;
  §4 governs which mismatches are D1 vs D3): AIS capsule
  `/home/codex/ais-study/capsule.sqlite` =
  `3acf6905ab82b3b72c27707e78d62805b6951df08fd535317d5810fcd5506efe`
  (D3 if moved before freeze; frozen copy immutable after first launch);
  assembler v0.5 `/workspaces/doxybase/tools/assemble_context.py` =
  `47c1421a3ce902f15da00e1bb89386dcb49bcbb5cbaeca4fedebe6cb8b8208f4`
  (note: ENRON-2 sealed v0 at `403111be…`; v0.5 post-dates that trial by
  design); v4 seed `/home/codex/knowhow-study/kh-vocab-seed.trig` =
  `213da77a9d4988c7c4eb6ff0680474fe397368d24e9d2e6012eb383ea1b05fd4`
  (identical to the ENRON-2 seal). Wheel hash recorded at materialization.
- **Calibration probes** (recorded; not part of the seal): (1) `--describe`
  against the AIS capsule renders the map/patterns/observations census and
  25 named parameter/invariant labels — the basis of Appendix D's
  capability statement. (2) A region-flavored open question at budget 600
  served 3 nodes of 85 candidates (method-M2 + two berth/NavStatus
  observations) — v0.5 favors concrete vocabulary; hence Appendix D's
  "concrete questions retrieve better" line. (3) A concrete surprise
  question ("sog_max of 102.3 knots — real or artifact?") at budget 400
  served the sentinel caveat at rank 1 (score 79.1) — the instrument
  demonstrably answers trap-shaped questions; the demand side is what the
  trial measures.
- **The A0 schema-basics stripping rule** (§5, Appendix B §4): column
  descriptions derive from the capsule map's neutral comments with every
  clause stating a deficiency, reliability judgement, or analytic use
  removed (stripped examples: sog's sentinel note; mmsi's
  self-reported/cloned warning; imo's IMO0000000 note; draft's
  "changes reflect loading" analytic hint; vessel_name's typo warning).
  The dataset's one-line identity ("broadcasts received around the USA,
  NOAA-style") is retained: a real cold analyst would know what product
  they were handed, and withholding it would manufacture, not measure,
  ignorance. The line is drawn at identity-without-interpretation;
  recorded as an author degree of freedom.
- **The author read**: doc 17 (the memory thesis), the ENRON-2 protocol
  and run record (the house style and its verdict), the v0.5 assembler
  source, the owner-round observation (bbbf391b), the fable parting notes,
  and the AIS capsule read-only (registry, patterns, map, coverage scans).
  The author ran the Appendix A census (5 data-bearing queries + 2
  listings + 1 client-side 404), wrote to no capsule, and launched
  nothing.
- **Author degrees of freedom, enumerated** (§13.6): the region and box;
  the task phrasing; the ~150-query and 4000-token/≤12 budgets; the A1
  extraction rule and its single pre-declared exception; the two recorded
  editorial normalizations in Appendix C; the schema stripping rule; the
  trap-list generalizations of method-bound caveats (each generalizes the
  caveat's mechanism, not its method: e.g. #27 tests "co-location without
  a wandering discriminator", not knowledge of method-M5).
