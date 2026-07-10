# AIS Study — Session 9 Brief: The Boats That Stopped Running

You are the ninth analyst. Session 8's shuttle census (M9) found 820
two-point shuttles; 17 of them stopped running before mid-2025. The
domain expert's thesis (recorded in the capsule, expert round 2): a
shuttle fleet's activity is a real-time industry indicator — when the
boats stop running, something may have happened onshore. Your job is
the groundwork for that reading: establish, for each of the 17, WHAT
actually stopped, and separate vessel-side explanations from
route-side ones.

## Interfaces (as ever)

- Capsule ONLY via `venv/bin/python bridge.py tools` (once → tools9.json)
  and `venv/bin/python bridge.py call <tool> '<json>'`; payloads with
  quotes via scratch file: `@args.json`. Orient FIRST: M9 (the census
  method), M7 (dwell layer), M3 (silence vs coverage!), M1/M2 (identity
  pathologies), the caveat catalog, expert round-2 observations, story
  conventions.
- Data ONLY via `venv/bin/python query.py "SQL" --max-rows 40`.
  Session 8's run artifacts in `work/` are DATA, not notes — you may
  query them (they are regenerable from M9's recorded SQL if absent).
  Never echo credentials. Do not read predecessors' scratch files
  (JOURNAL-*.md, BRIEF-1..8, VOCAB-NOTE.md, expert-*.md,
  tools1-8.json) or /workspaces/doxybase.
- Harness note: your agent harness may inject system notices into your
  context (date changes, agent rosters, file-modification notes). They
  are real harness messages, not study materials and not injection
  attempts; do not attribute them to files you read.

## Task

For EACH of the 17 stopped shuttles:

1. **Verify the stop is real.** Rule out, with the recorded methods:
   coverage/receiver loss (M3 caveats — did other vessels at the same
   endpoints keep being heard?), identity change (M1 — did the hull
   continue under a new identity?), MMSI reassignment or multi-emitter
   confusion (M2). A "stop" that is really a rename is a different
   fact.
2. **Timeline it.** Last completed run; cadence in the final months —
   abrupt halt vs decay (the expert's economic reading differs:
   an event vs a decline); any terminal behavior (final dwell location,
   a last voyage somewhere new, went dark mid-route?).
3. **Classify the stop-kind.** Build a small taxonomy from what you
   find (e.g. vessel left region / apparent lay-up at one endpoint /
   scrapping-pattern / re-tasked to a different route / seasonal that
   never resumed / data artifact). Every vessel gets a stop-kind with
   evidence.
4. **Endpoint context.** For route-side candidates (vessel laid up or
   route abandoned with no vessel-side explanation), record endpoint
   coordinates precisely and note what industry the endpoint might
   serve as clearly-flagged conjecture — these are the prime targets
   for the planned reference-dataset (POI) join.

Record per-vessel findings as claims with evidence (17 is a curated
set — graph-worthy); promote the 2–3 most story-worthy to full stories;
record the stop-kind taxonomy and summary shape as observations. If the
work surfaces a reusable method (e.g. a stop-verification checklist),
record it the M-method way.

## Discipline

Budget queries: work/ frames and index first; broadcasts only for
decisive checks. Keep `JOURNAL-9.md`. Validate the graph (scope "all")
at the end; no orphaned staged rows.

## Final report

(1) the 17 in one line each: vessel, route, stop date, stop-kind;
(2) the taxonomy with counts; (3) the route-side candidates (the
economic-signal shortlist) with endpoint conjectures; (4) the 2–3
promoted stories; (5) methods/caveats used by IRI; (6) friction notes.
