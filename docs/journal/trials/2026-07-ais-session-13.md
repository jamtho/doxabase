# AIS Real-Work Study — Session 13: The Stops Series (2026-07-11)

Cold Sonnet analyst; the foundational-layer session from expert
round 4 (recall check REQUIRED before trusting day-index stops; stops
series as the base layer). Brief: `/home/codex/ais-study/BRIEF-13.md`.
Graph conforms; M12 recorded; cache `work/stops_series.parquet`
(427,134 events, 37MB); recall plot in repo at
`docs/journal/ais-study/plots-s13/`.

## Verdict: the expert's caution, quantified — and his architecture
## vindicated

- **The recall headline** (457 stratified MMSIs, 92.4M broadcast rows
  in one 74s glob join): M7's day-level detection finds only **52.4%**
  of 10–30min stops, 60.8% of 30min–2h, 71.2% of 2–6h, 78.6% of
  6–24h, 99.0% of multi-day. Monotonic exactly as predicted. The
  perfect illustration: a Ventura passenger vessel cruising 19–20kn
  all day with one clean 9-minute mid-route stop — a day the index
  classifier can never flag.
- **M12 stops-series extractor recorded** (pattern `88a62586…`):
  SOG<0.5kn contiguous runs, >30min silence breaks runs (silence never
  assumed continuous — a real bug caught mid-build: a 70-day "stop"
  from 47 messages before the gap check), ≤2min flicker merge, 10min
  reporting floor, session-12 position-glitch screen reused verbatim
  (7.0% flagged). Honest failure modes documented in the pattern:
  creeping-slow work (dredges, trawling) chops into spurious events;
  anchor-swing jitter fragments long stays.
- **The stops-series-as-foundation hypothesis made concrete**: M9's
  own SQL rerun on the sample finds 14 shuttles; the same logic over
  the event-level series finds **43** — 3× more, with the 9 passing
  both being the clearest cases and all 5 day-only passes explainable
  as grid/conflation artifacts. Everything-derives-from-the-series is
  now evidenced, not hunch.
- Short stops are real and interesting: canal-junction queues, lock
  waits, tug holds — the expert's edge-case instinct given evidence.

## The injection false-positive, third occurrence — with a lesson

The agent again attributed the harness's own injected notices
(date-change + agent-roster) to the brief file — BRIEF-13.md verified
clean on landing (3,618 bytes, as written). NEW information: this
brief CARRIED the demystifier line, and it worked partially — the
agent refused compliance and flagged openly instead of silently — but
still misdiagnosed the source as the file. Refined methodology fix:
the demystifier must state that harness notices can appear
IMMEDIATELY ADJACENT TO FILE CONTENTS in the agent's context and are
never part of any file just read.

## Study findings

1. Sessions cannot read each other's SQL (scratch-file isolation), so
   session 13 reconstructed session 12's vessel-class taxonomy
   independently — labels matched, but this is duplicated effort; a
   shared work/lib/ convention (data, not notes) would fix it.
2. 8/457 MMSIs with zero stops (sparse pleasure craft, plausibly
   AIS-off-while-docked) — noted, not chased.
3. The map-interface ask was correctly NOT built here (not in brief);
   it remains the standing next-tool item.
