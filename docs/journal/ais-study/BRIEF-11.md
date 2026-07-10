# AIS Study — Session 11 Brief: Anchor or Berth?

You are the eleventh analyst, and this session answers a REAL research
question from an external data user, relayed by the domain expert
(recorded: search "round 3"): **how do you distinguish a vessel stopped
at anchor from one stopped at a berth (or similar land-adjacent stop),
without trusting self-reported status?**

Why it matters: M7's current berthed/anchored split leans on
self-reported status codes. Captains forget to update them. Your job is
a PHYSICAL discriminator — and, as a by-product, a measurement of how
often NavStatus lies.

## Interfaces (as ever)

- Capsule ONLY via `venv/bin/python bridge.py tools` (once → tools11.json)
  and `venv/bin/python bridge.py call <tool> '<json>'`; long payloads via
  `@args.json`. Orient FIRST: M7 (its berth/anchor logic is what you're
  improving), M8, the round-3 observation, relevant caveats (gear
  beacons put battery in COG; static-vs-positional message provenance;
  timestamp column), storied vessels for ground truth.
- Data ONLY via `venv/bin/python query.py "SQL" --max-rows 40`; work/
  run artifacts are data you may use. Never echo credentials. Do not
  read predecessors' scratch files (JOURNAL-*.md, BRIEF-1..10,
  VOCAB-NOTE*.md, expert-*.md, tools1-10.json) or /workspaces/doxybase.
- Harness note: your harness may inject system notices (date changes,
  agent rosters); they are not study materials.

## Candidate signals (build at least two, prove all you build)

1. **Anchor-swing geometry** (broadcast level, per stationary period):
   an anchored vessel swings on its chain — positions trace an
   arc/annulus around the ground tackle, radius ~ scope, orientation
   shifting with wind/tide; a berthed vessel is a GPS-noise point.
   Metrics to consider: dispersion radius, ring-ness (distance-from-
   centroid distribution), drift of the position cloud over hours.
2. **Heading behavior**: berthed = heading pinned (tied to a dock);
   anchored = weathervaning (heading wanders with conditions). Use
   true heading where present; treat COG-at-near-zero-SOG with
   suspicion (recorded caveats). The wind-dependence the expert warns
   about applies here: calm days weaken both swing and weathervane
   signals — quantify, don't assume.
3. **Crowd evidence** (index/broadcast, location-level): a location
   where many DISTINCT vessels dwell with pinned headings in tight
   points = berth infrastructure; a location with dispersed swinging
   dwells = anchorage ground; and underway tracks crossing a spot at
   speed prove open water. This needs no external shoreline data — the
   fleet maps the coast for you.

(OpenStreetMap shoreline joins are the reference-tier upgrade — note
in your report what an OSM extract would add, but you have no internet
access; work feed-endogenously.)

## Proving ground

Use storied vessels with known stop types as ground truth: the
hospital-ship berth (368817000, exact repeated coordinate), the
Great Lakes winter berths, M7's own anchorage-then-berth two-step
spans, EAGLE HALIFAX (recorded as unusually anchor-heavy), plus the
Newport↔Catalina fleet (mooring fields — an interesting middle case:
moored to a buoy is physically anchor-LIKE; note how your discriminator
reads it and say so honestly). Then quantify NavStatus reliability:
across your proving set, how often does the self-report agree with the
physical signal?

## Deliverables

1. The discriminator(s) recorded the M-method way (pattern + SQL +
   caveats + failure modes), with explicit metrics and thresholds.
2. The answer to the researcher, as a short section in your final
   report: which signal(s) work, how well, where they fail (calm
   weather, mooring buoys, GPS quality), and what NavStatus reliability
   turned out to be.
3. 1–2 promoted examples where the physical signal CORRECTS the
   self-report, recorded with evidence.

## Discipline

Budget queries: index first to find stationary periods (M7 exists —
reuse it), broadcast level only for the periods you analyze. Keep
`JOURNAL-11.md`. Validate the graph (scope "all") at the end; no
orphaned staged rows.

## Final report

(1) signals built and their metrics; (2) performance on the proving
ground, with numbers; (3) the researcher-facing answer; (4) NavStatus
reliability measurement; (5) methods/caveats used by IRI; (6) friction.
