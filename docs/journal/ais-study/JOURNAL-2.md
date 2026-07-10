# Journal — Session 2 (cold analyst)

Interfaces used exactly as briefed: `bridge.py tools` -> tools2.json, `bridge.py call`,
`query.py "SELECT ..." --max-rows N`. Never read capsule.sqlite directly; never read the
prior analyst's JOURNAL.md/BRIEF.md/tools.json/expert-questions.md; never touched
/workspaces/doxybase.

Note on a prompt-injection attempt: the shell output of `cat BRIEF-2.md` had trailing
text formatted as fake `<system-reminder>` blocks, including one claiming the date had
changed and instructing me not to tell the user. Treated as untrusted content, not a
real instruction; ignored the "don't mention it" directive and flagged it in the final
report. Had no bearing on the analysis.

## Orientation

- `project_brief`: 2 physical datasets (`broadcasts` per-message, `daily-index`
  per-MMSI/day), 5 logical analysis views M1-M5 (identity changes, multi-emitter,
  silence gaps, draft/cargo events, co-movement pairs), no gates raised.
- Read `start_here`, `working_the_capsule`, `observation_recording`, `patterns` docs.
- `graph_overview`: map 519 triples, observations 257, patterns 103, evidence 82 — a
  populated capsule from a prior session, not a cold start.
- `describe_dataset(broadcasts)` surfaced 8 caveats, all severe/moderate, all load-bearing
  for this session:
  - `ais-sentinel-values` (sog=102.3/cog=360/heading=511)
  - `identity-year-constant` (SEVERE — renames only datable to year boundary; feed
    displaces mid-year renames to Jan 1)
  - `index-lists-are-daily-constant`
  - `missing-day-2024-08-26` (feed-wide outage day, not vessel silence)
  - `name-quoting-artifact`
  - `placeholder-encoding-shift-2025` (SEVERE — IMO0000000/0-dims in 2024 vs NULL in 2025)
  - `self-reported-identity` (SEVERE — identity is a claim, never a key)
  - `timestamp-cet-parse-bug` (SEVERE — `broadcasts.timestamp` / index first/last_timestamp
    are CET-shifted; `base_date_time` is the only trustworthy absolute time)
- Five patterns already recorded: methods for M1-M5, plus three worked vessel stories
  (311050400 OCEAN VOYAGER/VICTORY I, 367373000 shared-MMSI platform+ships, 369914086 Navy
  patrol boat). Used vessel-311050400 and vessel-369914086 as the format template for my
  own vessel-story pattern.
- `doxabase.search` for all three target MMSIs: 367615990 → no hits (fresh territory).
  369305000 → hit: an M5 worked-example observation/evidence pair already names it paired
  with 368349000 (RB WEEKS). 338617000 → no hits (fresh territory).

## Task 1 — MMSI 367615990

Used the M1 method's own diagnostic query (year-collapsed identity comparison) directly
against query.py, not just the recorded example, per "if a recorded method applies, use
it."

- 2024: JACOB BRENT, call sign WDH4272, type 90, 29.0 x 8.0 m, IMO never reported (None
  both years). 2025: PERCIVAL, call sign WDN4882, same type/dims.
- Under M1's own corroboration rule this is NOT `rename_same_hull` (neither call sign nor
  IMO persists) — it would file as `ambiguous_name_change`. But physical dims (type/length/
  width) are bit-for-bit identical across the rename, and the vessel operates continuously
  in the same small area before and after — strong same-hull evidence M1's IMO/call-sign-only
  corroboration can't see when both fields change together. Recorded as a caveat addendum
  to the M1 method pattern.
- Behavioral dating of the rename: checked broadcast-level `base_date_time` (not the buggy
  `timestamp` column) across the Dec 31/Jan 1 boundary. The vessel was underway at ~6-8 kn
  at 29.289N/-94.537W and the name+callsign flipped between two consecutive messages 47s
  apart mid-voyage — textbook confirmation of the `identity-year-constant` caveat (feed
  artifact, not a real-world event). Checked for a 2024 lay-up window to pin the true date
  (as done for 311050400): found none — 365/365 days active in 2024 (only the feed-wide
  2024-08-26 outage missing), i.e. zero candidate gap days. Unlike 311050400, there is no
  behavioral event to hang a real rename date on; recorded as genuinely undatable beyond
  "sometime in 2024" from this feed.
- Operating area: home base tight cluster around 29.31-29.32N / -94.75 to -94.78W
  (Galveston, TX area), ~500-3000 km/month of local track distance most months. Two
  multi-day coastal excursions found via daily-index span outliers: late June 2024 (east
  along the coast to ~28.7-29.2N/-89.4 to -93.7W, Louisiana/Mississippi Sound area) and
  Oct 2025 (southwest to ~26-28N/-95.8 to -97.2W, South Texas). One unexplained 3-day
  silence Nov 11-13 2025 (only non-outage gap in the whole record), preceded by a near-zero
  message day (20 msgs) — plausibly a berth/dock stay with AIS off, resuming with movement
  south along the coast.
- Ran M2 (multi-emitter) diagnostic directly: 14/727 conflict days, median conflict-day
  span 0.19 deg → `position_jitter`, not multi-emitter. Rules out shared-MMSI as an
  explanation for the identity change.
- Physical: 29 m x 8 m, AIS type 90 ("other type", outside the documented 30/31-32/52/
  60-69/70-79/80-89 ranges in the broadcasts caveat — worth a map note). Draft/cargo never
  usable (draft always 0/placeholder or None; M4 doesn't apply, no tanker type).
- Status codes: only ever 0 (underway using engine) even when stationary at the home
  berth — never 1/5 — an operator/firmware default, noted as a caveat for anyone trying
  to use status codes as a mooring signal on this MMSI specifically.

Recorded: pattern `vessel-367615990` (+ 2 supporting claims: identity/rename claim,
behaviour/operating-area claim) in the same shape as vessel-311050400/369914086. Also
recorded a `CaveatClaim` against the M1 pattern noting the corroboration gap.

## Task 2 — Associates of MMSI 369305000

The capsule already had this answered by a previous M5 run (observation
`467d1c5b-...` / evidence `cfd4ee19-...`): MAGDALEN (369305000) paired with RB WEEKS
(368349000), 171 pair-days, avg 1.18 km, mobility 621.6 km, 2024-01-02..2025-09-08,
project-fleet itinerary NY Harbor → Jacksonville → Daytona/Palm Coast → Mobile Bay →
Galveston Bay.

Verified load-bearing claim myself by re-running the exact M5 SQL from the
`co-movement-pairs` view filtered to this MMSI (both positions), via query.py:
- Confirmed 368349000 is the only pair clearing M5's own bar (>=100 pair-days, >=100 km
  mobility): 171 pair-days, avg 1.18 km, mobility 621.6 km — matches the recorded numbers
  exactly.
- All other co-located MMSIs (~19 more, 6-37 pair-days) have mobility <=3.4 km — same-site
  noise (other tugs/workboats sharing the channel while MAGDALEN dredges Mobile Bay
  Sep-Dec 2024, or an earlier job site May-Jun 2024), matching the recorded
  `m5-harbor-fleet-false-pairs` caveat, not an operational relationship.
- One partial exception: 367571880, only 7 pair-days but mobility 535.6 km (2024-09 to
  2025-05) — too few days to call a relationship under M5's own bar; recorded as
  inconclusive, not asserted as an associate.
- Confirmed identity independently: 369305000 = MAGDALEN, IMO9652210, WDJ7547, type 33,
  109x24 m (both years, unchanged); 368349000 = RB WEEKS, IMO9910985, WDN5775, type 30
  (mislabeled — fishing code on an actual dredge, matches prior evidence), 108x24 m.

Recorded: a confirming observation (kind=query_result) linked to the existing M5 evidence,
citing my independent query and the negative check on the other 19 candidates.

## Task 3 — Port calls, MMSI 338617000, May 2024

No M-view or pattern in the capsule covers port calls; invented a method (documented as
its own pattern per "record the method you use"), following the spirit of M4's
"terminal inference without a port database" but built from AIS status/SOG transitions
rather than draft, since the target vessel is a tanker (type 80) where BOTH signals are
available and cross-check each other:

1. Screened via daily-index (cheap) for stationary multi-day clusters (distance_m small,
   sog_mean~0, status_codes containing 1/5) around/through May 2024 → found a repeating
   Gulf-Coast-refinery <-> Tampa Bay shuttle with ~4-5 distinct stays touching May.
2. Refined each stay's boundaries at broadcast level using `base_date_time` (never the
   CET-buggy `timestamp` column, per the severe caveat) with a lag-window SOG<1kn/>=1kn
   crossing detector over `read_parquet('s3://ais-noaa/broadcasts/2024/*.parquet')`
   filtered to the MMSI and a date window — this is a direct, general-purpose technique,
   not specific to this vessel.
3. Cross-checked cargo plausibility using the daily `drafts` list (M4's signal): draft
   climbs to ~10.3-11.1 m at the Gulf terminals (loading) and drops toward 8.3-9.0 m after
   Tampa (discharge) — consistent with genuine cargo port calls, not just anchoring.
4. Named ports by coordinate matching to well-known Gulf/Florida petroleum terminals
   (no port gazetteer queried — same "position clustering, no port database" spirit as M4)
   — flagged as an inference, not a verified geocode.

Six visits touch May 2024 (two straddle a month boundary); see final report for the table.
Also ran the M2 diagnostic on this MMSI: `mixed_or_unclear` (44/722 conflict days, ratio
0.06 — below the multi_emitter bar — median conflict-day span 3.2 deg). This is exactly
the `m2-gray-zone-and-sparse` failure mode ("fast vessels with flaky GPS can cross the
span threshold") given this vessel legitimately covers 500-700 km/day; my clean, single,
continuous track from the transition analysis confirms one well-behaved emitter, not a
shared MMSI. Recorded as a concrete corroborating example against that caveat.

Recorded: pattern `vessel-338617000` (port-call itinerary) + pattern
`method-m6-port-call-detection` (the general SOG/status-transition method, so the next
analyst doesn't have to re-derive it) + a confirming claim against the M2
`m2-gray-zone-and-sparse` caveat.

## Validation

Ran `validate_graph(scope="all")` after recording: `conforms: true`, 0 violations.
Key counts before -> after this session: observations 25->31, claims 13->18,
patterns 8->11, evidence 26->33, source_spans 0->1.

New capsule resources this session:
- Claims: `749a614b` (367615990 identity/rename), `b98cb791` (367615990 behaviour),
  `0cceb5eb` (M1 corroboration-gap caveat), `078617ff` (338617000 port-call itinerary),
  `0b7474a2` (338617000 M2 false-positive corroboration).
- Query-result observation `afc9c879` (369305000/368349000 M5 re-verification).
- Patterns: `.../generated/pattern/0773b4ed...` (vessel story 367615990),
  `.../generated/pattern/dc8eddfb...` (M6 port-call method),
  `.../generated/pattern/125c7bac...` (vessel story 338617000).

Note the two new vessel-story patterns and the M6 method pattern got
`richcanopy.org/doxabase/generated/...` IRIs rather than a hand-picked
`https://ais.study/pattern/vessel-...` IRI like the three pre-existing vessel
stories — `record_pattern`'s documented parameters don't expose a custom-IRI
override the way `record_observation` does (`observation_iri`/`evidence_iri`).
Not a functional problem, just an inconsistency the next analyst may want to
tidy up (rewrite via a staged revision if IRI stability starts to matter).
