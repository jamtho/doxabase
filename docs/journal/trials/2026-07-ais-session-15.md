# AIS Study — Session 15: M13, Feed Outages and Boundary Reasons (2026-07-21)

Commissioned from round 9 (James: should artificial stop boundaries be
covered by the model, not just a caveat?). The answer, built: outage
detection + per-boundary attribution as sibling frames, with a full
doc-12 contract. Graph conforms; zero staged debt; journal at
/home/codex/ais-study/JOURNAL-15.md.

## Verdict: the stop model now knows WHY each boundary exists

- **854 feed outages detected** across 2024–2025 — one every ~1.2 days,
  from brief partial dips to total blackouts. The known 2025-08-23
  event confirmed at 12,044 vessels / ~38min near-total silence; a
  previously unnamed 2025-12-02 event (9,818 vessels) is a genuine
  ~80% volume drop.
- **Threshold methodology worth keeping**: the validation doctrine's
  "clear break" wasn't in raw magnitude — N=8 same-second sharing came
  from a Poisson-coincidence null (1,000× over chance), but the burst
  threshold N=200 required discovering a NEW artifact: **broadcast
  volume RISES every hour on the hour** (77–94% of small clusters are
  hour-aligned reporting cadence, not outages). Recorded as its own
  caveat (hourly-reporting-cadence-artifact) — a previously
  undocumented feed behavior found while validating a threshold.
  Geographic dispersion, not volume collapse, proved the right
  feed-wide test for small outages.
- **Attribution over all 60.16M boundaries**: movement 33.0%,
  silence_gap 63.9%, feed_outage 2.8%, series_edge 0.3% — with a
  verified structural invariant (movement boundaries match exactly
  across inter-stop transitions, 9,940,663 = 9,940,663). The
  101.34-day maximum stop now cites its two bounding outage ids by
  name in a claim.
- **The contract vocabulary held**: M13's contract needed ZERO new mc:
  terms, and reuses M12's silence-gap parameter by reference — the
  cross-method parameter-sharing question from doc 12 answered in
  practice (shared by citation, exactly as decided).
- Two frames described as capsule datasets (feed-outages,
  stop-boundary-reasons); frames composing by stop_id join — the
  sibling-frame pattern demonstrated.

## Study findings

1. record_claim_reconsideration requires rc:Claim on both sides — the
   prior "quantized" language lived in evidence/parameter text, so the
   agent recorded a fresh richly-linked claim instead of fabricating a
   retroactive prior. Correct call; noted for the ledger (reconsidering
   non-claim statements has no route).
2. The agent caught its own labeling over-reach mid-session
   (spot-check language applied too broadly) before recording —
   posture worth noting.
