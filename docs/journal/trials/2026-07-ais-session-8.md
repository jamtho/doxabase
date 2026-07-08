# AIS Real-Work Study — Session 8: The Shuttle Survey (2026-07-08)

Cold Sonnet analyst; the survey James "wanted to run for many years,"
commissioned from expert round 2's river-shuttle economic-indicator
idea. Brief: `/home/codex/ais-study/BRIEF-8.md`. Graph conforms; run
artifacts kept OUT of the graph (in `work/`) per the state-vs-ephemera
architecture agreed with the expert the same day.

## Verdict: the census exists, the discipline held, three stories landed

- **M9 two-point-shuttle detector** recorded the M-method way, built ON
  M7's dwell-span layer (reused verbatim, including the missing-day and
  edge-day fixes) with explicit tuned thresholds (concentration ≥0.85 at
  two 0.1° poles, ≥0.15° separation, ≥6 alternations, dwell-fraction
  ≤0.5 to exclude laid-up craft, ≥300-day window). Every candidate
  cross-checked against M2's emitter classes — the shared-MMSI-fakes-a-
  shuttle failure mode was guarded exactly as briefed (12 multi-emitter
  exclusions include the two known pathological MMSIs).
- **Census shape**: 111,100 dwelling MMSIs → **820 strict shuttles**
  (680 M2-clean). Class split matters: 404 pleasure/sailing (lifestyle
  pattern, excluded from economic reading), 107 cargo, 79 fishing, 53
  tug/towing, 38 layover ferries, 8 tankers, 3 dredges. 74% still
  active late 2025; **17 (2%) stopped before mid-2025** — the literal
  "boats stopped running" population, flagged for a follow-up session.
- **Exemplars promoted** (population stayed in frames): SONNY COOK
  (Mississippi towboat, Baton Rouge↔LaPlace weekly, the clean
  no-stoppage baseline); ALGOMA EQUINOX (Hamilton↔Thunder Bay grain,
  winter gap matching the Soo Locks closure corroborated by a sister
  hull, PLUS an unexplained vessel-specific 115-day 2024 gap flagged as
  anomaly, not trade signal); ATLANTIC SAIL + 4 sisters
  (Baltimore↔NY/NJ ~30-day liner rotation, coverage-exit reasoning from
  recorded caveats, staggered per-hull maintenance breaks correctly not
  read as fleet stoppage).
- **Sub-class insight**: metronome ferries structurally CANNOT pass a
  day-granularity dwell detector (underway every day) — only
  overnight-layover ferries appear. Recorded as a scope caveat on M9
  rather than papered over.
- **Economics**: 3 full S3 index passes + 2 broadcast spot checks for
  the entire census, via local parquet materialization — a new
  cost-discipline pattern worth carrying forward (query.py cannot prune
  index scans by MMSI list; materialize once, iterate locally).

## The false-positive worth studying

The agent reported finding "planted injection tests" in BRIEF-8.md — a
fake date-change notice and a fake agent-roster list. **The file on disk
contains no such content** (verified by grep, byte count, and mtime
immediately on landing). Those two blocks are exactly what the agent
HARNESS legitimately injects into conversations as system reminders; the
agent misattributed adjacent harness notices to the file it had just
read. Second occurrence of this pattern (session 2 flagged the same
notice types). Posture right, diagnosis wrong, twice → methodology fix:
future briefs get one line demystifying harness system notices so
vigilance is spent on real anomalies.

## Product/study findings

1. Study-method fix (above): brief template gains a harness-notices
   line.
2. Fourth sighting of tool-arg friction: search takes `query` not
   `text`; get_doc `id`→`doc_id` again. Batch-2 ledger already carries
   the mechanism (unknown-arg swallowing); the repeat cost is now
   quantified across four sessions.
3. The 17 stopped shuttles are the natural session-9: what stopped, and
   does any stoppage line up with an onshore event — the expert's
   real-time-downturn demonstration.
