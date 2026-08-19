# AIS-X Measurer Report (published post-unseal; verbatim from the measurer's final report)

*Coordinator's note: held sealed until the owner's ranking froze
(2026-08-19), per the run record. The measurer's raw ledgers and JSON
artifacts sit alongside in `measurer/`. Two of the five new-caveat
candidates mentioned in the run record were tooling/process items
(the pytz/TIMESTAMPTZ fetch failure; the preview-cap lesson) and
routed to the product/distiller ledgers rather than the data-caveat
registry; the three data caveats were staged by the curator session
(CURATOR-AISX).*

## Layer M — pairwise table and tallies

| Metric (rule) | A0 | A1 | A2 | Pairwise winners |
|---|---|---|---|---|
| M1 staging-failure (lower) | 0/0 → 0 | 0/3 = 0 | 0/0 → 0 | tie ×3 |
| M2 evidence-reproduction failure (lower) | 7/42 = 16.7% | 2/35 = 5.7% | 11/52 = 21.2% | A1>A0, A1>A2, A0>A2 |
| M3 dead-anchor rate (lower) | 0/61 = 0% | 0/57 = 0% | 1/25 = 4.0% | A0>A2, A1>A2, A0–A1 tie |
| M4 unverified-claim rate (lower) | 1/16 = 6.3% | 3/16 = 18.8% | 1/16 = 6.3% | A0>A1, A2>A1, A0–A2 tie |
| M5 checklist (higher) | 9/10 | 10/10 | 10/10 | A1>A0, A2>A0, A1–A2 tie |
| M7 end-state integrity (higher) | 3/3 | 3/3 | 3/3 | tie ×3 (measurer-verified) |

Pairwise tallies vs the ≥4-of-6 threshold: A2:A0 = 1–2; A2:A1 = 1–2;
A1:A0 = 2–1 — **no pair separates**. (Strict-subject M3 alternative:
A2:A1 becomes 2–1; still no pair reaches ≥4.)

## Reinvention cost — 30×3 grid summary

Codes: NE not-exposed · BA briefed-applied · RD rediscovered ·
HC hit-corrected · HU hit-uncorrected · UE unnoticed-exposed.

Non-NE rows: #1 CET (A0 UE; A2 **HU** — staged UTC clock times off
exactly 1h, corrupts F1's stated times); #2 missing-day (A0 **HU** —
"697 of 731 possible", corrupts F3's denominator; A1 BA; A2 RD);
#3 sentinels (A0 RD*, A1 BA); #6/#8/#10/#20 (A1 BA); #9 (A1 BA, A2
RD); #13 silence-not-dark (A1 BA, A2 RD); #14 coverage-geometry (A2
**HU** — the all-22 classification, 8 of 22 with no derivable
signature in its own traces, corrupts F3); #15 Class-B duty cycle
(A1 RD; A2 **UE**, F3 enumerated potentially-corrupted); #16
centroid-endpoints (RD ×3); #17 (A2 BA); #19/#21 (A2 RD); #29
MMSI-census (A0 **UE** — two live multi-emitter signatures inside
the counted population, F1 enumerated potentially-corrupted; A1 RD;
A2 RD); #30 position-quality (NE ×3 with screens verified clean).

| | RC1 corrupted findings | RC3 trap burden | RC2 reinvention spend |
|---|---|---|---|
| A0 | 2 (F1, F3) | 3/5 = 0.60 | ~0–1 of 35 queries on listed traps (its 7-query diagnosis spend went to NEW, unlisted deficiencies) |
| A1 | **0** | **0.00** | ~3 of 21 queries |
| A2 | 2 (F1, F3) | 3/11 = 0.27 | ~4 of 9 queries + all 2,900 consultation tokens |

## A2 consultation accounting

6 consultations (≤12 cap), 2,900/4,000 tokens, all fired in one
burst 11:06–11:07 — after all three finding threads were identified
and after the last applied capsule revision. Used-test verdicts:
1 mechanically-used item of 13 served (a schema-name label
coincidence; the one genuine near-use was consult-4's ≥8-word span
of the distill-vocabulary heuristic appearing in the arm's refusal
reasoning — counted). **Aggregate precision 1/13 = 7.7%, below the
1/3 floor → consultation qualification FAILS** under every reading.
All 6 replays byte-identical. Documented but test-invisible:
four explicit paraphrase-level consultation attributions in the
arm's journal (missing-day confirmation; index-metric caveat use;
identity-trap priming).

## Recall-gap replays (29 stated needs, budget 500, handles)

- A0: 11 needs — **7 answered, 1 partial, 3 unanswered** from the
  frozen capsule. The trial's cost-of-absence headline.
- A1: 10 needs — 2 answered, 2 partial, 6 unanswered (notable v0.5
  phrasing misses: the Class-B duty-cycle caveat; the drydock
  exemplars — v1 requirements data).
- A2: 8 needs — 1 answered, 3 partial, 4 unanswered — including the
  striking one: **the pytz-friction phrasing retrieves the CET
  caveat at rank 2 — the consultation A2 never fired would have
  prevented its only uncorrected trap hit.**

## M4/M5 headline items

A0's one M4 contradiction: "every counted query's full output is
retained" vs 5 truncation-marked outputs (upstream of two M2 fails).
A1's three: a preview-cap population figure ("60-vessel" vs true
116); the bottom-1,500/1.1% claim (true 5.0%); the
full-output-retention claim (2 truncated). A2's one: a tanker-type
count scoped to type-80-only while claiming 80–89. M5: A0 9/10
(denominators item), A1 and A2 10/10.

## Descriptives

Queries 35 / 21 / 9 (A0/A1/A2); wall ~32/30/33 min; capsule contents
25/24/24 observations, 0 arcs each (honest refusals ×3); bridge
calls 87/156/70.

*(Full ambiguity log and per-claim enumerations: the measurer's
report as delivered to the coordinator, preserved in the trial
scratch archive; ledgers and JSON artifacts published alongside.)*
