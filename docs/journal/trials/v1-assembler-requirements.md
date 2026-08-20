# The v1 assembler requirements corpus — consolidated

*2026-08-20. Consolidates the retrieval evidence three sealed trials
and two field studies produced, per the live-retrieval protocol's own
instruction ("the consultation ledger's per-item verdicts are the
requirements list for [v1]") and doc 07 §7.2's seed-list duty. This is
a requirements document, not an implementation: per the program's loop
rules, feature work resumes on the owner's review. Sources: the
live-retrieval trial (protocol + record), the consumption trial, the
AIS-X expertise trial (measurer report), assemble_context.py v0.6's
own docstring, and field use in two capsule studies. The v0 docstring's
sequencing gate — "v1 … sequenced after the AIS expertise trial" — is
now open: that trial is complete.*

## 1. What the evidence established

Three verdicts frame everything. The consumption trial (static
hand-rendered brief): NULL — content-presence at brief time alone
moved nothing, and that render was a STRONGER static form than v0
produces. The live-retrieval trial: LIVE WIN — mid-task assembly beat
the static render on the sealed conditions, with the static arm using
its briefing render 0-of-3 and the live arm reaching aggregate
precision 0.40 (alternate reading 0.10 — one generic class-label match
is a 4× swing). The AIS-X trial (alien domain, three arms): no pair
separated mechanically, and the live-consultation arm's precision
FAILED the floor at 1/13 — with all six consultations fired in one
burst AFTER every finding thread was already identified.

Read together: **when assembly happens matters more than that it
happens** (live win at verification-time consultation; null at brief
time; fail at after-the-fact burst), **the store usually has what the
agent needs** (AIS A0's replay answered 7 of 11 stated needs from the
frozen capsule — the failure is query-side), and **the only content
that produced genuine textual hits in either trial was
refusal/graveyard reasoning** — negative knowledge transfers through
retrieval better than anything else measured.

## 2. Requirements (evidence-cited)

**V1-R1. Phrasing invariance beyond PRF.** The live record's own first
v1 entry: a need the arm's abstract phrasing retrieved was missed by
the more concrete replay phrasing. AIS adds two named v0.5 misses (the
Class-B duty-cycle caveat; the drydock exemplars) AFTER
pseudo-relevance feedback shipped — PRF is evidenced insufficient. The
AIS search surface adds tokenizer-level failures (hyphenated and
camelCase terms unfindable: "couldn't-say", "mergesGap"). Doc 17's
named v1 mechanism (embeddings) is the candidate answer; the
acceptance evidence exists as replayable stated-need ledgers
(measurer's recall_questions.json + replay-ledger.jsonl).

**V1-R2. Ranking is a requirement, not a nicety.** The sharpest single
datum: the pytz-friction phrasing retrieves the CET caveat at rank 2 —
and rank 2 was equivalent to nothing, because budget admits little and
the consultation never fired. Recall without rank order fails silently.

**V1-R3. No label-shaped items, verified against serving reality.**
v0.5 excluded schema tiers, yet AIS-X's only "used" item was still a
schema-NAME label coincidence, and the live trial's precision rode a
generic class-label knife-edge (0.40 vs 0.10). v1 must test served
items against label-only content, not just tier membership.

**V1-R4. Chunk serving with discretionary boundaries.** v0's static
render spent essentially its whole 1500-token budget on one ~4,000-word
mega-observation (plus a hop-expanded item whose entire content was a
file path). v0.6's fixed-width chunking is the declared stand-in; doc
17's sleep-built chunk index is the v1 mechanism. Serve the right
SLICE of the right node — tier weighting already finds the right layer
(keep-list K-3).

**V1-R5. Verification state travels with served items.** New, from the
uk-money benchmark (WP-D R1): a claim served without its tier,
matchBasis, and supersession context invites the measured
error-transmission failure (a stale match inherited at "exact" grade,
6→4→4→3 across rounds) at the retrieval layer. `handles` mode already
carries IRIs; v1 must carry the epistemic state — tier, basis,
supersededness, assessedAt — as first-class render furniture, cheap
enough to survive budget trimming.

**V1-R6. Push at the moment of relevance, or accept the demand
problem.** Both trials met the mid-task condition in letter only
(consultations clustered at write-up/verification time). Field
counter-evidence: the public-money study's working sessions found launch-time `--prime`
"helped directly" three sessions running, while MID-session pulls
returned mostly the session's own writes and lost to the native tools
for targeted research. The demand side is real and unsolved: the
protocol's own "unused instrument" verdict-name exists because offered
retrieval goes unused. v1 design should treat WHEN-to-assemble as a
first-class problem (trigger hooks — e.g. on staging a caveat, on
first touch of a dataset), not only HOW-to-rank.

**V1-R7. Worklist queries.** The AIS study reconstructed "which
vessels are already storied" from raw pattern listings across three
sessions; the public-money study's review queues sat unowned for four.
"What has been done / what awaits" is an assembly-shaped question the
graph answers today only by manual reconstruction.

**V1-R8. Keep the metric, restate the floor.** All published numbers
are denominated in the sealed used test (IRI / exact label / ≥8-word
span, post-assembly, own-outputs excluded). v1 acceptance should reuse
it — while acknowledging its measured blind spot (four documented
paraphrase-level uses invisible to it) and restating the 1/3 floor,
which is explicitly a v0 whole-node-serving artifact, for chunk-grain
serving (OQ-8).

## 3. Keep-list (confirmed by trial or field, do not regress)

Determinism/byte-identical replays (both trials); budget-binds-not-
entries; ladder tier weights (the calibration render surfaced exactly
the right tier's records); honest emptiness + ledgered zero-yield
consultations as recall-gap instruments; `--provenance handles` as
default (no mode-attributable friction anywhere); `--describe`;
launch-time `--prime` (three field sightings of direct help — the
push/pull ladder boundary working as doc 17 intended); history-graph
exclusion from serving; edge-type weights (no recorded complaint).

## 4. Open questions carried forward (not resolvable from this corpus)

Provenance-mode comparison (digest/handles/full) — zero comparative
evidence exists, deferred by design to its own trial. The live trial's
R3 was defined but never published (the per-candidate replay tables
are the gap; AIS supplies the only published recall-gap numbers).
v1-vs-hand-curated-static is untested (the consumption trial's render
was human-selected; the live trial compared machine-vs-machine).
Teaching-vs-licensing inseparable at this instrument. `--prime` has
field evidence but no sealed trial. n=1 per cell throughout; the
live-trial seal is spent — successor trials need fresh allocation.

## 5. Suggested acceptance shape for v1 (proposal only)

A successor sealed trial in the house style: same used test, chunk-
grain floor restated, R3 published this time, provenance_mode as the
trial parameter (the owner's parameter-not-decision doctrine), one arm
with trigger-hook push (V1-R6) — scored on (a) recall-gap closure
against the three existing replayable need-ledgers, (b) rank-1 rate on
the named misses (CET-via-pytz; Class-B duty cycle; drydock
exemplars), (c) precision under the alternate (label-excluded)
reading, which is the honest one.
