# AIS Study — Session 8 Brief: The Shuttle Survey

You are the eighth analyst. The domain expert's latest guidance (in the
capsule: search for "expert round 2" observations, including the river-
shuttle idea) proposes a survey: some vessels run between exactly two
points — presumably warehouses or terminals — year after year, and a
census of them is the foundation for using fleet activity as a
real-time industry indicator (when the boats stop running, something
happened onshore).

## Interfaces (as ever)

- Capsule ONLY via `venv/bin/python bridge.py tools` (once → tools8.json)
  and `venv/bin/python bridge.py call <tool> '<json>'`; payloads with
  quotes via scratch file: `@args.json`. Orient FIRST: methods M1–M8
  (M7's track-state/dwell-span layer is your workhorse), caveats, the
  expert round-2 observations, existing story conventions.
- Data ONLY via `venv/bin/python query.py "SQL" --max-rows 40`. Never
  echo credentials. Do not read predecessors' scratch files
  (JOURNAL-*.md, BRIEF-1..7, VOCAB-NOTE.md, expert-*.md, tools1-7.json)
  or /workspaces/doxybase.

## Task

1. **Build the shuttle detector**: per MMSI, find vessels whose
   stationary time concentrates in exactly TWO recurring dwell
   locations with regular alternation between them. Index layer first.
   Define your regularity/concentration metrics explicitly; mind the
   recorded caveats (timestamp column, missing day, placeholder MMSIs,
   shared-MMSI pathologies — a shared MMSI can fake a shuttle).
2. **Run the census** over both years. Report its SHAPE as summary
   observations (how many shuttles, cadence distribution, geographic
   clusters, year-over-year survival) — do NOT dump the full population
   into the graph. The expert's architecture guidance is explicit:
   population-scale outputs are regenerable run artifacts; the graph
   gets the METHOD, summary statistics, and promoted exemplars only.
3. **Promote 2–3 exemplar shuttles** as proper vessel stories: the
   endpoints (coordinates + what the recorded methods say about the
   dwells), cadence, any stoppage or cadence-break windows — a
   stoppage with a clean before/after is exactly the economic-signal
   demonstration the expert wants. Note what industry the endpoints
   might serve ONLY as clearly-flagged conjecture (no external data).
4. **Record the method** the M-method way: pattern + executable SQL +
   caveats found while proving (e.g., dredges and ferries also
   two-point-shuttle — how did you separate them or did you keep them
   as labelled sub-classes?).

## Discipline

Budget queries (the census must be index-only; broadcasts only for
exemplar spot checks). Keep `JOURNAL-8.md`. Validate the graph
(scope "all") at the end; no orphaned staged rows.

## Final report

(1) detector definition and metrics; (2) census shape with numbers;
(3) the exemplar stories in brief, especially any stoppage windows;
(4) sub-classes found (ferries, dredges, ...) and how labelled;
(5) methods/caveats used by IRI; (6) friction notes.
