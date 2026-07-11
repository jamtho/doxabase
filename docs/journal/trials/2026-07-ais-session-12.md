# AIS Real-Work Study — Session 12: The M11 Threshold Survey (2026-07-11)

Cold Sonnet analyst; the validation-doctrine session commissioned from
expert round 4 ("foundational measures get whole-dataset surveys...
humans trust thresholds through plots"). Brief:
`/home/codex/ais-study/BRIEF-12.md`. Graph conforms; survey cache
`work/m11_survey.parquet` (4,710 windows); five plots at
`work/plots/m11_*.png` (repo copies: `docs/journal/ais-study/
plots-s12/`); full-survey SQL recorded as the deterministic pipeline.

## Verdict: thresholds confirmed, shape expectation revised, and a new
## failure mode found

- **Population honesty**: 7,316,288 eligible stationary vessel-day
  windows exist — a full broadcast pass was correctly declared
  infeasible; the sample is 4,710 windows stratified by 11 vessel
  classes × 5° geography (caps documented), fetched in ONE 90.8s
  broadcast join rather than 727 day-queries. The complete-survey SQL
  is recorded for a production run (the ephemera pipeline pattern).
- **Thresholds: keep M11's tuned values.** The empirical radius valley
  sits at ~20 m, matching the tuned berth bound; the decision-rule box
  sits in low-density territory on the 2D scatter; heading dispersion
  lifts off its near-zero floor exactly where the radius valley sits —
  two independent signals agreeing on the transition zone (plot e, the
  decisive one).
- **Doctrine revision**: the expected "two clean superimposed humps"
  is NOT the real shape — it is one dominant pinned/berth mode plus a
  long diffuse anchor/other tail. The ambiguous middle M11 already
  refuses to classify is population-validated, not just inferred from
  four proving vessels.
- **The expert's first-ever heading-dispersion view** (plot c): 62.4%
  of heading-available stopped windows pinned at ~0° SD; monotonic
  tail to 170°; no second mode.
- **Class dependence confirmed as predicted**: cargo/tanker/tug_tow
  hold the thresholds cleanly (tug_tow anchored heading_R median 0.640
  lands in the proving-set anchor band); small-craft "anchored"
  self-reports show berth-zone radii (3–20 m) — real short-scope
  anchoring vs loose status use, unresolved. Mooring-buoy geometry-only
  classification generalizes (n=931 pleasure/sailing: 53/17/30
  berth-like/anchor-like/ambiguous).
- **NEW data-quality failure mode**: 10.1% of sampled windows are
  position-suspect. Worst case: longitude frozen bit-identical across
  317 messages while latitude drifts ~750 km at self-reported
  SOG 0/moored — smooth drift, invisible to M2's jump heuristic, and
  the index's own `distance_m` reads 5,245 m against a ~750 km raw
  spread. Recorded as evidenced observation; formal caveat promotion
  left for a future session.

## For James (index builder)

The `distance_m` definition question is his: nothing in the schema or
capsule docs pins down its formula, and it disagrees with raw broadcast
spread by two orders of magnitude on the glitch case. Added to the
pipeline-reminders list alongside the frozen-coordinate artifact.

## Study findings

1. Study venv lacks pandas/pyarrow — plotting worked via
   duckdb.fetchnumpy(); fine, but note for future plotting briefs.
2. record_map_fact's caveat kind/spec vocabulary wasn't confidently
   discoverable in-session (the agent recorded an observation instead
   of a formal KnownCaveat) — another sighting for the batch-2
   discoverability items.
3. DuckDB numeric edge: sqrt(-2*ln(R)) needs LEAST(R,1.0) clamp —
   recorded in the method SQL.
