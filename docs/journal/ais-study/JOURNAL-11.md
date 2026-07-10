# JOURNAL-11: Anchor or Berth? (physical discriminator, NavStatus reliability)

## Orientation (bridge only)

- `doxabase.project_brief`: 7 datasets/tables, 44 patterns, 117 observations, 89 claims,
  12 graph revisions. M1-M5 are formal analysis_views; M6/M7/M8 are patterns
  (not yet promoted to analysis views) found via search.
- **M7** (pattern 208f3abb): two-layer index-only track-state classifier.
  Layer 1 per (mmsi,date): sog_mean>=3 or distance_m>=50000 -> underway (or
  transition_day if status_codes also contains moored/anchored); else status
  code 5 -> berthed, status code 1 -> anchored, else sog_mean<1 and
  distance_m<5000 -> stationary_unclassified, else transition_day.
  Layer 2: gaps-and-islands over stationary_candidate days (sog_mean<3 AND
  distance_m<50000) per mmsi, missing-day-corrected (2024-08-26), with
  edge-day-excluded dispersion (core_lat_spread/core_lon_spread over interior
  days only -- edge days are transit-polluted). any_moored AND any_anchored
  on one span = anchorage-then-berth two-step.
  Caveats baked in: status_codes is a whole-day DISTINCT list (not
  point-in-time); edge-day dispersion is badly inflated if not excluded;
  missing day 2024-08-26 must be bridged; Class B rarely reports status_codes
  so falls to stationary_unclassified (a documented gap M7 doesn't solve --
  exactly session 11's opening).
- **M8** (pattern c768eaa1): joins M4 draft events to M7 dwell spans
  (+-1 day tolerance) -> at_berth/at_anchor/no_dwell_nearby/dwell_unclassified.
  EAGLE HALIFAX (235076282) flagged as unusually anchor-heavy: 27 loading +
  31 discharge events AT ANCHOR (not berth), fixed Gulf-of-Mexico position,
  consistent with lightering/STS transfer -- but at least one of those events
  is a single-message draft glitch (see caveat below), so don't take the
  anchor-heavy read at face value without a spot check.
- **Round-3 observation** (obs b21712a9): the actual research question.
  Confirms M7's berthed/anchored split leans on self-reported status codes.
  Confirms the four candidate signal families this brief lists.

### Caveats oriented on
- `caveat/m4-single-message-draft-glitch`: a single stray broadcast message
  (day's FIRST value convention) can fake a draft event. Confirmed case:
  EAGLE HALIFAX 2024-01-21 00:01:08Z reads draft=8.7 vs 11.2 on every
  neighbour -- a transmission glitch, not physical. A second superficially
  similar case (2024-03-11) was genuine (30+ sustained messages, status=3).
  Relevant here because EAGLE HALIFAX's anchor dwell spans are my main
  anchor-swing proving ground -- I need to make sure I'm not timing my
  broadcast window off a glitchy day.
- `caveat/sentinel-encoding-shift-2025`: heading=511/cog=360 are 2024-only
  sentinels; 2025+ uses true NULL for heading/cog specifically. sog=102.3
  is a sentinel in BOTH years and never NULL. Must branch by year (or just
  filter both forms) when screening heading/cog for "not available".
- `caveat/message-type-merging`: static fields (name, dims...) are carried
  forward from Message 5 onto positional rows: not synchronized to the row's
  own timestamp. Not directly load-bearing for kinematics but keep in mind
  if I use vessel_type/length to pick candidates.
- `caveat/timestamp-cet-parse-bug` (via reconciliation pattern): the parsed
  `timestamp` column has a CET/CEST mis-parse (this project's own bug, not
  a NOAA artifact) -- ALWAYS use `base_date_time` for anything requiring
  correct time ordering/deltas (message spacing, swing drift-over-hours).
  Confirmed by M6 pattern too.
- gear beacon caveat (obs 9333b23f): AIS transmitters tag fishing gear;
  gear units share one MMSI, dispersed simultaneous positions, and encode
  BATTERY LEVEL in the COG field -- COG is untrustworthy as kinematics
  without a plausibility screen. Relevant: prefer true `heading` over COG
  for heading-behavior signal; treat COG-near-zero-SOG with suspicion per
  the brief's own instruction.

### Storied vessels identified for the proving ground
- **Hospital ship**: MMSI 368817000 (COMFORT, IMO7390478, type 58, 273m).
  Gulf-coast berth 30.68N/-88.03W. Exactly-bounded 91-day berth stay
  2025-02-05..2025-05-06, sog 0.0-0.1kn throughout (per existing claim) --
  the brief's "exact repeated coordinate" berth ground truth.
- **Great Lakes winter berth**: MMSI 366971370 (EDWIN H GOTT, 305x32m bulk
  carrier). Winter lay-up at Toledo, 41.693N/-83.462W, mid-Jan to mid-Mar
  both years.
- **M7's own anchorage-then-berth two-step**: MMSI 338617000 (PENNSYLVANIA).
  Tampa two-step within the M7-flagged span 2024-04-27..05-01: anchorage
  first, berth after (and 2024-05-19..21 similarly). Layer-1 example already
  recorded: 05-03 transition/anchorage, 05-04 transition/berthed, 05-05
  clean berthed.
- **EAGLE HALIFAX**: MMSI 235076282, unusually anchor-heavy (M8). Anchor
  position ~28.843N/-94.578W (offshore Gulf of Mexico), first documented
  window 2024-01-20/21 (contains the draft glitch -- avoid dating the swing
  window off that alone).
- **Newport<->Catalina fleet**: not yet in the graph; found via query.py
  vessel-name scan of the daily index: CATALINA FLYER (367001740, Newport
  Beach<->Avalon day boat), CATALINA EXPRESS (366943960), NEWPORT HORNBLOWER
  (367381060), plus assorted small AVALON-named craft. Plan: use
  CATALINA FLYER as the fleet's flagship and pull a few of the small
  AVALON/CATALINA-named craft that dwell near Catalina Island as the
  mooring-buoy middle case.

## Plan
1. Index-level: pull M7-style dwell spans for the 5 proving-ground MMSIs to
   pick exact stationary date windows (cheap, already mostly known above).
2. Broadcast-level, surgical: pull only the specific vessel-days for each
   dwell window to build (a) anchor-swing geometry metrics and (b) heading
   behavior metrics.
3. Crowd evidence: index-level position clustering (round lat/lon) across
   many MMSIs to separate berth infrastructure vs anchorage ground by
   distinct-vessel-count + dispersion; broadcast-level heading spot check
   on 1-2 clusters only.
4. Cross-tabulate physical read vs self-reported status_codes across the
   proving set spans -> NavStatus reliability number.
5. Record the M-method pattern(s), 1-2 promoted "physical corrects
   self-report" examples, validate graph, write final report.

## Execution log

### Index-level candidate selection (cheap, whole-feed or per-vessel)
- COMFORT (368817000): confirmed clean berth window 2025-02-05..02-07/09-12,
  status=[5], centroid ~30.6788N/-88.0340W (this session's own decimals,
  slightly refined from the prior claim's rounded 30.68/-88.03).
- EDWIN H GOTT (366971370): full-year scan needed -- the "mid-Jan to mid-Mar"
  description from the existing story did NOT hold for 2024 (vessel was
  actively steaming most of Jan-May 2024, only scattered near-zero-distance
  days near Toledo). Found the REAL multi-week stationary window at
  2025-01-24..2025-03-20 (~8 weeks) at 41.693N/-83.462W, self-report
  cycling [1]->[1]->...->[1,5]->[5]. This became the session's strongest
  NavStatus-reliability finding.
- PENNSYLVANIA (338617000): confirmed the M7-documented Tampa two-step is
  actually TWO separate stops within its May 2024 window; the Lake
  Charles-area stop 04-27..05-01 (30.18N/-93.32W) is NOT Tampa -- the real
  Tampa anchorage-then-berth two-step is 05-03 (transit/anchor arrival),
  05-04 (transition, mixed status), 05-05 (clean berth, 27.92N/-82.44W).
- EAGLE HALIFAX (235076282): confirmed berth window 2024-01-16..01-18
  (status=[5], 30.01N/-93.97W) and TWO anchor windows, 2024-01-20..01-22
  (contains the known m4-single-message-draft-glitch date 2024-01-21 --
  avoided) and the cleaner 2024-01-30..01-31 (status=[1], 29.42N/-93.69W),
  used instead.
- Newport<->Catalina fleet: NOT in the graph yet. Found by scanning the
  daily index for vessel_names matching CATALINA/AVALON/NEWPORT. CATALINA
  FLYER/EXPRESS/NEWPORT HORNBLOWER are active day-boats (145-284 km/day),
  not stationary -- not useful as the mooring-field case. Instead found the
  actual mooring fields directly: a single-day box scan (33.30-33.50N /
  -118.55..-118.25W, sog_mean<1.0) on 2024-07-15 turned up 30+ distinct
  small recreational MMSIs holding position at two named Catalina Island
  features, Avalon (~33.347N/-118.325W) and Two Harbors (~33.45N/-118.50W),
  all Class B with empty status_codes. Picked DRIFTWOOD (367083980, Avalon)
  and MALILIA (368140610, Two Harbors) after confirming 5-day persistence.
- Crowd evidence (whole-feed, index-level): two location-clustering sweeps
  (tight <3km/day and wide 8-60km/day, both sog_mean<1.0, >=5 distinct
  MMSIs, restricted to vessel_types 70-89 after a first unrestricted pass
  surfaced a tug/tow/dredge-dominated false positive at 29.75N/-95.10W,
  status=[12]/[0] almost exclusively -- power-driven-vessel-towing/pushing
  standby, not anchoring or mooring in the AIS-spec sense; recorded as a
  failure mode, not used as ground truth). Clean results: large-ship berth
  complexes at Norfolk VA, Houston Ship Channel, Portland OR, Vancouver BC,
  New Orleans-area (frac_moored 0.97-1.0 across 10+ locations, 1500+
  vessel-days); anchorage-shaped locations split sharply by culture/type --
  Vancouver English Bay frac_anchored 0.77-1.0, an offshore Louisiana
  location (29.13N/-90.21W, OSV-name-pattern composition) frac_anchored
  0.0022 vs frac_underway0 0.90 (ambiguous: may be genuine NavStatus error
  or may be physically-correct engine-holding loiter rather than anchoring
  -- left unresolved, documented as a gap).

### Broadcast-level surgical pulls (21 vessel-days total, all listed in the
recorded M11 pattern's evidence_sources)
Built one SQL template (M11a: radius-from-centroid + hollow_frac; M11b:
circular heading concentration R, heading sentinel-filtered for both
2024/511 and 2025+/NULL forms) and ran it per vessel-window:
- COMFORT 2025-02-05..07: n=1119, radius_mean=3.05m, hollow_frac=0.967,
  heading_R=0.953 (851/1119 valid) -- clean berth baseline.
- EDWIN H GOTT 2025-01-24 (n=56, radius_max=13.7m, 0 valid headings),
  2025-03-02 (n=172, radius_max=9.6m), 2025-03-19 (n=389, radius_max=12.0m);
  combined: radius_mean=3.94m, hollow_frac=0.896, heading_R=0.99998 --
  IDENTICAL physical signature regardless of self-reported status.
- PENNSYLVANIA 2024-05-04 00:00-04:32 (anchor-wait): n=241,
  radius_mean=123.2m, hollow_frac=0.336, heading_R=0.757, heading sweeping
  273 deg -> wraps through 22 deg over 4.5 hours while sog=0.0 the entire
  time; self-report mostly status=0 (under way) with brief status=1
  flickers. 2024-05-05 (clean berth): n=497, radius_mean=3.4m,
  hollow_frac=0.940, heading_R=0.999997, self-report clean [5]. This
  within-vessel, next-day pair is the cleanest single proof in the session.
- EAGLE HALIFAX 2024-01-16..18 (berth): n=1237, radius_mean=2.68m,
  hollow_frac=0.992, heading_R~1.0. 2024-01-30..31 (anchor): n=939,
  radius_mean=166.9m, hollow_frac=0.635, heading_R=0.649. Self-report
  agreed with physical read BOTH times here -- the discriminator's positive
  control (not every vessel lies).
- DRIFTWOOD (Avalon) 2024-07-14..16: n=747, radius_mean=1.2m,
  hollow_frac=0.886 (berth-like). MALILIA (Two Harbors) same window: n=130,
  radius_mean=7.9m, hollow_frac=0.338 (anchor-like). Neither transmitted a
  single valid true heading (n_heading_valid=0/both). Checked COG as a
  fallback: combined COG circular-R=0.125 (near-random) -- confirms the
  brief's own caveat that COG is untrustworthy at near-zero SOG; not used.

### Graph writes
Recorded via `doxabase.record_observation` (kind=claim for the two
promoted corrections, kind=observation for the three supporting findings)
and `doxabase.record_pattern` (M11, referencing all five). See IRIs below.
`doxabase.validate_graph {"scope":"all"}` after all writes: conforms=true,
result_count=0. project_brief counts before/after: observations 117->122,
claims 89->91, patterns 44->45, evidence 133->139; graph_revisions
unchanged at 12 (these tools commit directly, no staged/pending revision
was left open).

Recorded IRIs:
- claim/7da6f28c... (EDWIN H GOTT correction) + observation/dc7567a6...
- claim/762ab611... (PENNSYLVANIA correction) + observation/69cf1010...
- observation/9edfacf0... (EAGLE HALIFAX positive control)
- observation/ae5c3007... (Newport-Catalina mooring middle case)
- observation/78709f6a... (crowd-evidence NavStatus reliability sweep)
- pattern/2fb8d9b7-80e9-44e7-b5f9-181b2f271008 (M11 method, full pattern
  text/SQL/thresholds/decision-rule/failure-modes)

## Do-not-read compliance
Did not open JOURNAL-1..10.md, BRIEF-1..10.md, VOCAB-NOTE*.md,
expert-*.md, tools1-10.json, or anything under /workspaces/doxybase.
Capsule accessed only via bridge.py; data only via query.py plus work/
artifacts (only listed work/ directory names, did not read prior
sessions' scratch file contents beyond that).
