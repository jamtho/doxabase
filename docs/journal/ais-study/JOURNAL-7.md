# JOURNAL-7 -- Track context, fast

Brief: prototype kinematic-context primitives (track-state classifier +
draft-change contextualizer) as DuckDB views, prove them on known and fresh
vessels, record what earns its keep.

## Orientation

- `bridge.py tools` -> tools7.json (25 tools).
- `project_brief`: 7 datasets, 5 analysis views (M1-M5), 34 patterns
  (M1-M6 methods + 20 vessel stories + 7 reconciliations), 81 observations,
  63 claims, 24 caveats. No staged/queue debt at session start.
- `search("expert round 2")`: five expert observations. The load-bearing one
  for this session (obs 92240e42): draft-change interpretation needs
  positional track context (underway/berth/anchor read differently), expert
  suggests prototyping SQL views and possibly storing the DuckDB SQL in the
  capsule. Companion obs 14a4f98b: draft changes are NOT just cargo --
  ballast water discharge/uptake also moves draft; keep vocabulary/claims
  close to the observed physical fact, layer interpretation on top.
- M1-M5 are registered `analysis_view` map facts with query snippets +
  caveats; M6 ("port/terminal visits from SOG crossings + draft cross-check,
  no port database") is a `Pattern` only, not yet formalised -- explicit
  precedent that a proven-but-new method can stay at pattern level. Followed
  that precedent for my own views rather than promoting to `analysis_view`.
- Existing vessel stories (session-4 story-corpus observation, `pattern/vessel-*`):
  used 338617000 PENNSYLVANIA (M6 worked example, 6 documented port calls,
  May 2024), 538002783 NOR'EASTER (224 M4 events, hub-and-spokes, clean cargo
  direction), 303520000 SULPHUR ENTERPRISE (179 M4 events, the expert's own
  ballast-ambiguity exemplar), 367677560 BAY STATE/FLORIDA VOYAGER (182 M4
  events, steady trade) as known ground.
- Ontology already has `aisv:DwellPeriod`/`dwellKind` with controlled values
  including `berth_stay` and `anchorage_wait` -- my taxonomy's berthed/
  anchored labels were chosen to line up with this existing vocabulary
  rather than invent parallel terms.

## Design pass 1: per-day classifier (index layer)

First cut used `status_codes` (list_contains 5/1) with sog/distance as
fallback only. Tested on 338617000 May 2024 day-by-day: heavily
over-labelled "berthed" on real transit/arrival/departure days, because
`status_codes` is a whole-day DISTINCT LIST -- any hour touching status 5
marks the whole day, even a 484 km transit day.

Fix: kinematics decide underway-vs-not FIRST (sog_mean>=3 OR distance_m>=50000
km); only within "not clearly underway" days does `status_codes` disambiguate
berthed/anchored; mixed-signal days (kinematically underway-ish but touching
a stationary status code) become a first-class `transition_day` bucket
instead of being forced into berthed. Re-tested on the same window: matches
the M6 story closely, including correctly NOT calling the 2024-05-08
Empire/Donaldsonville river slowdowns (sog_mean 6.95, 214 km that day) a
port call -- the story explicitly says these are "not separate port calls."

Bonus finding: the same day-by-day run over the *entire* May window (not
just the six documented stay windows) turned up an apparent 7th, unrecorded
short Tampa call, 2024-05-14..05-16, at the exact documented Tampa berth
coordinates (27.91N/-82.44W), sandwiched between the recorded Baton Rouge
and second-Lake-Charles stays. Recorded as observation
`0b47b24d-63fe-46f2-8e53-59239549b3f1` rather than asserted as a story
correction.

## Design pass 2: dwell spans ("dwell overlap")

Gaps-and-islands grouping of consecutive `stationary_candidate` days
(sog_mean<3, distance<50000) per mmsi, corrected for the single feed-wide
missing day 2024-08-26 (mirrors M3's own correction) so a real dwell
straddling that day isn't spuriously split.

First version computed span dispersion (lat/lon spread) over ALL days in
the span -- badly polluted by partial arrival/departure days (one span:
0.52 deg lat-spread for what proved to be a genuinely dead-flat berth stay).
Fix: exclude first/last day when span_days>2 ("core" days only) -- spread
collapsed to 0.0/0.0 on the same span. Kept both any_moored/any_anchored
flags per span; spans with BOTH true flag an anchorage-then-berth two-step,
which matched 338617000's documented offshore-then-berth approach pattern
at Lake Charles and Tampa.

## Design pass 3: draft-change track-context

Joined M4's per-event (mmsi, prev_date, change_date, delta_m, event) against
the dwell-span layer with a +-1 day tolerance, labelling each event
at_berth / at_anchor / no_dwell_nearby / dwell_unclassified. Internal check:
event totals reproduced from this rebuild matched the recorded M4 counts
exactly (303520000: 98 loading/81 discharge; 538002783: 109 loading/115
discharge) -- confirms the rebuild is faithful to M4, not a different filter.

## Proving numbers (share of events tied to a recognised dwell: at_berth+at_anchor)

| MMSI | vessel | known ground | dwell-attached share |
|---|---|---|---|
| 338617000 | PENNSYLVANIA | M6-confirmed genuine port calls | 92-95% |
| 367677560 | BAY STATE/FLORIDA VOYAGER | steady legit trade | ~89% |
| 538002783 | NOR'EASTER | clean hub-and-spokes | 65-75% |
| 538002221 | GREAT EASTERN (fresh) | -- | 67-76% |
| 235076282 | EAGLE HALIFAX (fresh) | -- | 79-85%, unusually anchor-heavy |
| 311000111 | PEGASUS VOYAGER (fresh) | already flagged in M4's own caveat text (offshore-smeared events) | 40-55%, worst dwell_unclassified share (21%) |
| 303520000 | SULPHUR ENTERPRISE | expert's ballast-ambiguity exemplar | 38-53%, lowest overall; its "loading" (ambiguous direction) events worst-attached at 37.8% |

Ordering is monotonic with how "clean"/confirmed each vessel's cargo story
already was, with the expert's own flagged ballast-ambiguous case scoring
lowest and the M6-confirmed textbook case scoring highest -- obtained with
zero external trade knowledge, purely from track context.

## Broadcast-level spot checks (fresh vessel 235076282)

- 2024-01-20/21 anchor stay at 28.843N/-94.578W: draft holds at 11.2 across
  every message except ONE at 2024-01-21T00:01:08Z reading 8.7 -- a single-
  message glitch promoted into a fake M4/M7 "discharge" event because it
  happened to be the day's first message (M4/M7 both use day's-first-value).
  New caveat recorded: `caveat/m4-single-message-draft-glitch`.
- 2024-03-11 anchor stay, same vessel: draft->8.5m sustained across 30+
  consecutive messages, status=3 -- a genuine change, not a glitch. So the
  failure mode is real but not universal; recommend spot-checking isolated
  events rather than trusting the day's-first-value convention blindly.

## Recorded to the capsule

- Observation `2e4f7df4-0dfb-45c2-a4fc-34340346e73c` -- single-message draft
  glitch finding.
- Observation `0b47b24d-63fe-46f2-8e53-59239549b3f1` -- likely 7th
  unrecorded Tampa call for 338617000.
- Caveat `https://ais.study/caveat/m4-single-message-draft-glitch` (targets
  broadcasts + daily-index).
- Pattern `208f3abb-08c7-4186-8122-dd15e4205b2f` -- M7 track-state
  classifier (layer 1 + layer 2 SQL, caveats, proving evidence).
- Pattern `c768eaa1-b2ed-49ba-b8ac-50a03c99ed5e` -- M8 draft-change
  track-context (SQL, proving numbers across 6 vessels, evidence).

Kept both at Pattern level (not promoted to `analysis_view` map facts),
mirroring M6's own precedent for a proven-but-new, not-yet-formal method.

## Query budget

~20 `query.py` calls total (all index-layer except 4 targeted
broadcast-level spot checks: one for 338617000 May 2024 boundary detail
already covered by index granularity, three for the 235076282 glitch
check). No full unfiltered broadcast scans.

## Final checks

- `validate_graph(scope="all")`: conforms=True, 0 issues.
- No staged revisions created this session (none to check for drift/orphans).
- `project_brief` queue counts unchanged (`analysis_view_review`: 5,
  `query_plan_handoff`: 2) -- no new queue debt introduced.
