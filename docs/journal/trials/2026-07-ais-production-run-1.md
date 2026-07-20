# AIS Study — Production Run 1: The Full Stops Series (2026-07-19/20)

Not a graded trial — the first PRODUCTION run of the state-vs-ephemera
pipeline: M12 executed over the entire feed from its recorded contract,
by an agent, with the frames then described back into the capsule.
Prompted by James noticing the workbench showed "not a lot of vessels"
— the correct fix being population frames, not mass promotion (doc 14).

## The run

- 6.13B raw broadcast rows → 6.11B after dedup; hash-bucketed by MMSI
  (64 buckets) so no stop event can span a chunk boundary — the
  boundary problem dissolved by chunking on the vessel axis instead of
  time. ~50 min wall on 16 workers; determinism per the phase-2
  lessons (integer total orders, single-threaded buckets).
- **Output: 30,080,069 stop events across 91,977 vessels** (of 131,693
  MMSIs in the feed), 2.5GB, 24 monthly partitions. Per-vessel dwell
  counts: median 58, mean 327, max 25,121.
- Sample-vs-full agreement on the 449 proven vessels: −0.019% — the
  dedup/tie-break fix's exact signature, decomposing phase 2's −0.22%.
- Two frames now live as DESCRIBED capsule datasets
  (stops-series-full, m11-survey-sample) with columns, caveats, and
  contract/claim citations; graph conforms; the workbench queries them
  in the browser (local-frame support added).

## Full-scale surprises (recorded in the capsule)

1. **The multi-day tail is feed-outage-quantized**: thousands of
   unrelated vessels share bit-identical stop boundaries (one 2025-08
   outage chops 12,243 vessels' stops at the same second). Long-stop
   maxima are reception artifacts, not behaviour — a caveat the sample
   could never have shown.
2. Placeholder MMSIs pass M12's contract filters (~0.02% of events) —
   recorded as a consumer caveat; the contract needs an MMSI screen
   parameter in its v2.
3. The position-suspect rate FELL at full population (5.97% vs the
   sample's 6.98%): glitches concentrate in large-vessel classes the
   sample over-weighted.
