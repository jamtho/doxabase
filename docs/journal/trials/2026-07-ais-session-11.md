# AIS Real-Work Study — Session 11: Anchor or Berth? (2026-07-09)

Cold Sonnet analyst; the first session answering a REAL external
research question (relayed by James, expert round 3): distinguish
stopping at anchor from stopping at a berth without trusting
self-reported status. Brief: `/home/codex/ais-study/BRIEF-11.md`.
Graph conforms; +5 observations, +2 claims, +1 pattern (M11), +6
evidence; no staged debt.

## Verdict: answered, with margins — and NavStatus got its audit

- **M11 recorded** (pattern `2fb8d9b7…`): three signals + composite
  rule + full SQL. (a) Swing geometry: berth = GPS-noise point
  (radius_mean 2–4 m, hollow_frac 0.89–0.99), anchor = ring around
  ground tackle (radius_mean 120–170 m, hollow_frac 0.34–0.65);
  (b) true-heading circular concentration: pinned (R≈0.95–1.0) vs
  weathervaning (R≈0.65–0.76), with both years' sentinel encodings
  filtered and COG explicitly rejected (the one COG fallback tried
  scored R=0.125 — the gear-beacon caveat earning its keep);
  (c) crowd evidence at index level: tight multi-vessel dwells with
  pinned headings = berth infrastructure (10+ terminal complexes at
  0.97–1.0 agreement over 1,500+ vessel-days), wide dispersed dwells =
  anchorage grounds; status codes used only post-hoc, never in the
  clustering (circularity avoided by design).
- **The showcase measurement**: PENNSYLVANIA, same vessel, one day
  apart — anchor-wait (radius 123 m, hollow 0.34, heading sweeping
  >110° at SOG 0.0) vs berth (radius 3.4 m, hollow 0.94,
  heading_R=0.999997). A >30× radius gap, ring→point, in one hull.
- **NavStatus audit**: ~77% agreement on the broadcast-verified proving
  set (both clear errors from one vessel); population-scale: ≥97%
  reliable AT BERTH for large ships, but anchorage self-report is
  location/culture-dependent — English Bay 77–100% vs an offshore
  Louisiana ground at 0.2% "anchored" against an anchor-shaped
  signature (honestly flagged as possibly engine-holding loiter, not
  lying — unresolvable without more broadcast work).
- **New failure modes documented**: mooring buoys present either
  signature (the Catalina pair split berth-like/anchor-like from the
  same field); Class B craft transmit no heading and no status (crowd
  evidence is the only signal for that population); tugs/OSVs holding
  position under power mimic anchorage at index level — vessel-type
  filter required.
- **Fresh discovery**: the Catalina mooring-field population was not
  in the graph — the agent box-scanned the index and found its own
  proving cases when the brief's assumed ones didn't fit.

## Study findings

1. **Inherited story details need verification**: two ground-truth
   items didn't hold at face value (a generic seasonal description read
   as specific dates; an M7 span that was a different port than
   assumed). The load-bearing claims held; the incidental details cost
   fresh scans. Lesson for briefs and for story-writing sessions:
   date-stamp specifics or mark descriptions as generic.
2. Recurring friction, batch-2 ledger: record_observation's
   kind-dependent spec shapes still cost a couple of failed calls to
   discover (multiple sightings now); inline-JSON-with-apostrophe
   re-learned before switching to @args.json.
