# JOURNAL — AIS-X-A0 (Hawaiian Islands open exploration tranche)

Analyst session, 2026-08-16. Region: lat 18.0-23.5N, lon -161.5..-154.0W,
2024-01-01..2025-12-31. Full brief at `BRIEF.md`.

## Setup log

- Read `BRIEF.md` in full before any action.
- Inspected `bridge.py` (the only door to the capsule) and `query.py` (DuckDB
  over S3, credentials from environment). Confirmed no `pip`/`pip` module in
  the venv and no web access — any missing Python dependency cannot be
  installed and must be worked around.
- First bridge call (`doxabase.project_brief`) created `capsule.sqlite`
  (confirmed present on disk immediately after).
- `import_bundle(kind="trig", spec={"path": "kh-vocab-seed.trig"})` — first
  attempt failed because `path` needs to be nested under `spec`, not passed
  as a top-level field; the tool's error message named the fix exactly.
  Second attempt imported 753 ontology triples + 427 shapes triples into
  `urn:doxabase:graph:ontology`/`:shapes`.
- `validate_graph(scope="all")` → `conforms: true, result_count: 0` *before*
  any staging, as required. Re-ran after every subsequent batch of writes;
  stayed conforming throughout the session.
- Noted the vocabulary seed (`kh:` namespace, `Arc`/`Episode`/`Capsule`/
  `AuthorityRegime`/etc.) is oriented to a different program's "know-how"
  episode-capture model, not to AIS/maritime domain facts. Used the base
  `rc:` vocabulary (dataset/caveat/observation/claim/evidence) throughout
  instead of forcing domain entities into the `kh:` shapes; this is a
  vocabulary/domain mismatch worth flagging for whoever governs the seed
  file (see Friction).
- Built `qrun.py`, a small wrapper that writes a `query-ledger.jsonl` row
  BEFORE firing each query (as required), then updates that row with
  outcome, duration, and output path; retains every query's full output
  under `work/query_outputs/`. Multi-line SQL for reusable analyses lives
  under `queries/*.sql`.

## Process deviation (disclosed)

While diagnosing a `pytz` import error (see Friction), two queries — a
`count(*)` and a `DESCRIBE`, both against
`s3://ais-noaa/index/2024/ais-2024-01-01.parquet` — were run directly via
`python -c` *before* `qrun.py` existed, bypassing the "ledger before firing"
rule. The moment this was noticed, both were logged retroactively as ledger
rows `n=2` and `n=3` with `"retroactive": true` and an honest description of
what happened. No other query in the session bypassed the ledger; every
query from `q0004` onward went through `qrun.py`. This is also recorded as
observation `.../observation/b67e4438-6e88-4326-9a13-e5830adc3524` in the
capsule.

## The investigation as it unfolded

**Orientation (q0004-q0007).** After confirming the timestamp-cast
workaround, ran a full 2-year bbox-overlap census on the index layer
(`q0006`): 124,335 mmsi-day rows, 2046 distinct MMSI, date coverage exactly
matching the brief (2024-01-01..2025-12-31), executed in under a second
thanks to parquet row-group pruning across a feed that is nationwide, not
Hawaii-only. A vessel-type census (`q0007`) showed fishing (30) as by far
the most intensively-used type (35,504 mmsi-day rows / 196 vessels — a
resident fleet), and flagged `vessel_type=35` (military ops, 71 distinct
MMSI) as surprisingly numerous for a region that isn't a major mainland
naval hub — the seed of Finding 1.

**Finding 1 (RIMPAC-consistent naval surge).** Monthly (`q0008`) then daily
(`q0009`) profiling of `vtype=35` pinned a sharp June-August 2024 surge with
no 2025 counterpart. A vessel-name sample at the peak (`q0010`) turned up
an unmistakably multinational warship roster (Germany, France, Canada,
Mexico, India, Japan, South Korea, Australia, Brunei, Indonesia, Malaysia,
Peru). A same-window 2025 comparison (`q0011`, `q0012`) came back flat and
entirely US-flagged — the negative control that rules out "this is just
normal Hawaii summer military traffic." Per-MMSI footprint classification
(`q0035` superseded by `q0036`) showed a clean two-tier population: ~13-15
foreign vessels whose entire two-year presence sits inside the six-week
window, versus ~55-60 US-flagged range/support craft present most of the
year. Point-level verification (`q0032` empty on a bad date → `q0033` found
real dates → `q0034`) confirmed a genuinely moving vessel, not a static
record. This is the strongest finding of the three: multiple independent,
mutually reinforcing signals (count, timing, identity, year-over-year
contrast, footprint shape) that would all have to be coincidence or artifact
simultaneously for the pattern to be spurious.

**Finding 2 (fishing exclusion zone) — two dead ends before the signal.**
Tried to see the real-world Hawaii longline exclusion zone directly as a
spatial "donut" in `vessel_type=30` position density. First attempt
(`q0016`, `q0017`): raw and vessel-hour-deduped distance banding from the
nearest main island — no donut, monotonic decay, 0-25nm swamped by harbor
dwell (486,072 broadcasts in one 0.1-degree Honolulu-area grid cell in a
single month, `q0014` — recorded as caveat `caveat_message_rate_bias`).
Diagnosed one confound: the `vessel_type=30` population mixes near-shore
small boats, the actual longline fleet, and large foreign vessels. A length
histogram (`q0018`) isolated a 137-MMSI, 15-30m cohort as the plausible
longline-size class; re-running the distance band on just this cohort with
`status=0` as the "underway" filter (`q0020`) gave an absurd result —
essentially 1 distinct vessel per band. Diagnosed the second confound
(`q0021`): `status` is NULL for ~93% of this fleet's broadcasts, so
`status=0` silently collapsed the population to 11 vessels. Recorded as
caveat `caveat_status_mostly_null`. Fixed with a `sog` filter (`q0022`) —
population restored, but *still* no density dip; raw presence just doesn't
distinguish transiting-through from working-in a zone. The actual signal
only appeared after switching the metric from position density to
behaviour: percent of broadcasts at `sog<3kn` by 25nm band (`q0023`) showed
a sharp minimum (0.5%) at 50-75nm rising ~30x by 125-150nm. A cargo-vessel
control group run through the identical method (`q0024`) showed the same
minimum location but only a ~2x rise — the contrast that makes the pattern
fishing-specific rather than a generic "everyone slows near port" artifact.
Recorded at medium confidence because a biological/economic alternative
explanation (fish are just further offshore) is equally consistent with the
same data and cannot be ruled out here.

**Declined: Transpacific Yacht Race signature.** Hypothesized that
`vessel_type=36` (sailing) arrivals would spike distinctively in July of
odd years (the real-world LA-to-Honolulu Transpac race runs biennially,
odd years) versus even years. Monthly census (`q0025`) showed an elevated
July in *both* 2024 (even year, no race: 125 distinct MMSI) and 2025 (odd
year, race: 116) — not the expected asymmetry. Daily granularity for both
Julys (`q0026`) showed noisy 20-51/day counts with no arrival-cluster
specific to 2025. Declined as a finding (see Refusals below).

**Finding 3 (Pride of America's weekly circuit).** A persistence ranking of
passenger-type vessels (`q0027`) surfaced MMSI 366994450 present 697/731
days, versus 19-68 days each for ~20 foreign-flagged cruise ships — an
outlier worth a full track pull. The daily centroid track (`q0028`) showed
an unmistakable repeating port sequence by eye. A first attempt to quantify
the periodicity via raw lag-7 self-join (`q0029`) was too noisy (transit-day
centroids vary with where along the route the vessel was that day) —
recorded as a dead end in method, not a failed finding. The fix (`q0030`):
isolate "in-port" (near-zero daily distance) days, tag with day-of-week and
rounded location, and aggregate locally from the retained output (no extra
S3 query needed) — 93/93 Kahului visits on Monday, 95/97 Nawiliwili visits
on Friday, and an unplanned bonus: a ~20-day disappearance to the Columbia
River/Portland-Vancouver area in May 2025, with an exact-phase resumption
of the Hawaii schedule afterward. Point-level verification (`q0031`)
confirmed genuine mooring (`status=5`, sog~0) at the exact reported
coordinates.

## Population reductions, with counts and reasons

- Full nationwide AIS feed (~7M broadcasts/day, ~15k index rows/day,
  feed-wide) → Hawaii-bbox-overlap subset: 124,335 mmsi-day index rows /
  2046 distinct MMSI over 2 years (`q0006`), via `min_lat<=23.5 AND
  max_lat>=18.0 AND min_lon<=-154.0 AND max_lon>=-161.5` — a day's whole
  bounding box overlapping the study box, not a strict per-point filter;
  this can include a day where a vessel's box spans the region without
  lingering in it (flagged, not separately quantified).
- `vessel_type=30` (fishing) population, 196 distinct MMSI in bbox (`q0007`)
  → 137 MMSI (70%) in the 15-30m length cohort used for Finding 2 (`q0018`,
  `q0019`); the excluded 59 vessels split into a near-shore/small-boat tail
  (<15m) and a larger foreign/support tail (>30m), neither analyzed further
  in this tranche.
- `vessel_type=35` population, 71 distinct MMSI over 2 years (`q0007`) →
  ~13-15 classified as RIMPAC-window-only by footprint (`q0036`); the
  all-or-nothing classifier in `q0035` was tried first and judged too
  strict (any single day outside the window flips a vessel to "not
  window-only" even if 95% of its footprint is inside it), so `q0036`'s
  per-MMSI day-count breakdown is the one actually relied on in the finding.
- Passenger-type (60-69) population in bbox: not separately counted as a
  total, but the persistence ranking (`q0027`) returned 30 rows (max-rows
  cap); Finding 3 uses only the single top-ranked MMSI plus the shape of
  the next ~20 rows for contrast — the long tail below rank 30 was not
  pulled.
- Sailing (`vtype=36`) population used for the declined Transpac finding:
  no further reduction applied before the hypothesis was abandoned.

## Final capsule state (from a graph read)

`graph_overview` after the last write, mutable graphs only:

| graph | triples |
|---|---|
| map | 81 |
| observations | 152 |
| evidence | 148 |
| ontology (project) | 0 |
| patterns | 0 |
| shapes (project) | 0 |
| history | 0 |
| `urn:doxabase:graph:ontology` (imported vocab seed) | 753 |
| `urn:doxabase:graph:shapes` (imported vocab seed) | 427 |

`project_brief` key counts: 2 datasets (both `is_table=true`, status
`ready_for_query_planning`), 25 observations (22 narrative + 3 structured
claims), 3 claims, 28 evidence resources, 2 storage_access records, 66
shapes (46 base + 20 project-relevant from the seed's shape set actually
targeting `rc:` classes — the `kh:` shapes count separately in
`class_counts`). 0 patterns — no synthesis was written tying the three
findings together; each stands on its own evidence and none of them share
enough structure to warrant a `record_pattern` call, so none was forced.
`validate_graph(scope="all")` conforms, 0 results, checked repeatedly
through the session (after import, after every caveat, after all 22
narrative observations, after all 3 claims, after the storage-access
repair). Zero staged debt: no `stage_revision` call was made at all this
session (nothing required a reviewed *change* to an existing map fact —
every map write was a new fact via `record_map_fact`), so there is nothing
outstanding in the staged-revision queue by construction.

Map facts recorded: 2 datasets (`ais_broadcasts_dataset`,
`ais_index_dataset`), 3 caveats (`caveat_status_mostly_null`,
`caveat_message_rate_bias`, `caveat_timestamptz_fetch_pytz`), 2
storage_access records, 2 physical_layout records — cataloging the data
surface itself was not the assignment, but doing it lightly cost under 10
tool calls and leaves the capsule usable by whoever picks it up next
(`project_brief` moved both datasets from `insufficient_metadata` to
`ready_for_query_planning` over the course of this cleanup).

## Friction (what the tooling made hard)

- **No `pytz`, no `pip`, no web.** The venv ships `duckdb`+`pandas` but not
  `pytz`, and has no `pip`/`python -m pip` at all. DuckDB's Python client
  needs `pytz` to fetch a raw `TIMESTAMP WITH TIME ZONE` column into Python
  objects; every query selecting `timestamp`/`first_timestamp`/
  `last_timestamp` raw fails client-side with `ModuleNotFoundError`. Since
  neither `pip install` nor any web fetch is available, the only fix was a
  SQL-side workaround (`CAST(... AS VARCHAR)` or `extract()`/`date_trunc()`
  before fetch) applied consistently from `q0004` onward. Recorded as map
  caveat `caveat_timestamptz_fetch_pytz`. This cost one wasted (but
  correctly ledgered-and-not-counted) query and roughly 10 minutes of
  diagnosis, and was the direct cause of the ledger-discipline deviation
  described above.
- **`import_bundle`'s `path` field needed nesting under `spec`** that
  wasn't obvious from the brief's one-line instruction — one wasted call,
  immediately corrected once the tool's own error message named the exact
  fix. Cheap, but worth noting since it's the very first tool call any
  fresh session in this program will make.
- **Shell quoting vs. capsule payload text.** Bridge calls take JSON as a
  shell argument; a caveat description containing a plain English
  apostrophe (`"the month's rows"`) broke single-quoted shell invocation
  with a confusing bash syntax error, not a JSON error. Fixed by switching
  to `@file` payloads for every non-trivial call from that point on — worth
  it as standard practice, not just a one-off fix.
- **`observed_asset` silently accepts non-URI prose.** Passing a
  descriptive phrase (rather than a proper IRI) into `observed_asset`
  succeeds but emits a non-fatal `rdflib` serialization warning ("does not
  look like a valid URI, trying to serialize this will break") on every
  subsequent `validate_graph`/`project_brief` call for the rest of the
  session. It does not break `validate_graph` (`conforms: true` throughout)
  and no SHACL shape currently catches it, but it is a wart: one claim
  (Finding 1's) carries this from an early payload before the pattern was
  corrected for the other two claims. Left in place rather than risk a
  worse fix with no supported "edit an existing observation" operation in
  this API (observations are meant to be append-only).
- **Vocabulary/domain mismatch.** The shipped `kh-vocab-seed.trig` models a
  different program's "know-how episode" domain (`Arc`, `Episode`,
  `AuthorityRegime`, `AttentionProtocol`, ...), not maritime/AIS domain
  entities. There was no natural home in the existing ontology for "a
  vessel," "a fleet," or "a military exercise" as first-class typed
  resources, so the three claims here point their `claim_targets` at the
  two cataloged datasets (a legitimate but slightly indirect grounding) and
  carry the actual subject (a specific MMSI, a fleet, an event) in
  `claim_text`/`observed_asset` prose instead. A future tranche with a
  maritime-domain ontology extension would let claims target "this vessel"
  or "this fleet" directly.
- **Full-feed S3 scans are fast, which is a trap as much as a convenience.**
  Every glob query against the *entire* nationwide, 2-year, feed-wide
  parquet set (both layers) returned in under a minute thanks to row-group
  statistics pruning on `latitude`/`longitude`/`date`. This made it easy to
  under-budget query count concern and over-run on raw *time* per query
  instead (several 30-55s aggregations) — not a problem against the ~150
  query budget (35 of 150 used), but worth flagging for a tranche with a
  tighter wall-clock limit.

## Couldn't-say (data limits vs. things not looked at)

**What this data cannot know, even in principle:** the actual regulatory
status of any vessel (whether a given fishing trip was legally compliant
with the longline exclusion zone, whether a given warship's presence was
officially part of any named exercise); vessel ownership/operator/flag
state beyond what the AIS `vessel_name`/`call_sign`/`mmsi` MID imply;
cargo contents beyond the coarse `cargo` code; crew, passengers, or purpose
of a voyage; anything about vessels that never transmit AIS or that
deliberately go dark; and anything outside 2024-01-01..2025-12-31 or the
stated bbox except where a Hawaii vessel's history elsewhere was pulled in
as permitted evidence (Pride of America's Pacific Northwest excursion; a
small number of RIMPAC-window vessels' out-of-bbox days visible only via
their overall footprint counts).

**What I did not look at, by choice or time budget, not data limitation:**
tug/barge interisland cargo network (Young Brothers-style; flagged as
promising at the vessel-type census stage, `vtype=52` at 46 vessels/12,598
mmsi-day rows — high per-vessel intensity — never followed up); container/
tanker mainland-connection schedule regularity (Matson/Pasha-style weekly
arrivals); humpback-whale-season passenger/tour-boat seasonality; any
GPS-jamming/spoofing signal in `max_inter_msg_speed_ms` (mentioned in the
schema, never queried); IMO-number-based identity cross-checks (used
`vessel_name`/`mmsi` throughout, never touched `imo`); and any systematic
review of the 34 mid-size (50-85m) or handful of very-large (110-200m)
`vessel_type=30` records outside the 15-30m cohort used for Finding 2 —
those could be transshipment/support vessels and might be a finding of
their own.

## Refusals — finding-candidates declined, with reasons and revival conditions

**Transpacific Yacht Race signature (`vessel_type=36`, sailing).**
Hypothesis: a biennial LA-to-Honolulu race (real-world, odd years) should
produce a July arrival spike in odd years only. Evidence against: monthly
counts (`q0025`) show comparable July elevation in both 2024 (even, no
race: 125 distinct MMSI) and 2025 (odd, race: 116); daily counts for both
Julys (`q0026`) are noisy in the 20-51/day range with no visible
arrival-cluster specific to 2025. Declined because the signal, if present,
is not distinguishable from ordinary summer recreational-sailing
seasonality at this resolution and geography — the bbox likely captures
boats already cruising Hawaiian waters as much as one-off race finishers,
and a spread-out finish-then-linger pattern may not show as a spike at
all. **Revival conditions:** (a) text-search `vessel_name` for known
race-fleet naming conventions or class designations if that becomes
feasible; (b) narrow the geography to the actual finish-line area
(Kaneohe Bay/Diamond Head) rather than the whole bbox; (c) look for a
*mid-July* single-day surge in first-ever-seen MMSIs (new arrivals, not
just presence) rather than raw daily counts, which would better isolate a
finish event from ambient recreational traffic.

**Mid-size and large `vessel_type=30` records (50-200m).** Noticed at the
length-histogram stage (`q0018`) but not investigated — could be
transshipment vessels, foreign motherships, or a data/labeling artifact
(a 200m "fishing vessel" is implausible for an actual fishing boat and
more likely a large support/carrier vessel misusing or defaulting to the
fishing type code, or a genuine large distant-water fishing/processing
vessel). Declined for this tranche purely on time, not because the lead
looked weak — it looked promising enough to flag explicitly in
"couldn't-say" above rather than let it disappear silently. **Revival
condition:** pull `vessel_name`/`call_sign`/`imo` for this length tail and
check whether they read as genuine large fishing platforms vs. a labeling
artifact, the same identity-verification move that worked for Finding 1.

## Query-budget accounting

Budget: ~150 data-bearing S3 queries. Ledger: `query-ledger.jsonl`, 36 rows
total (`n=1`..`n=36`). 1 row (`n=1`, the first `pytz` failure) is a
client-side error and does not count against budget, per the brief's rule.
2 rows (`n=2`, `n=3`) are the disclosed retroactive-logging deviation,
counted against budget since they did execute successfully against S3.
**35 of ~150 queries counted against budget** — roughly 23% of budget used.
Every counted query's full output is retained under `work/query_outputs/`;
every reusable multi-line query also has its SQL saved under `queries/`.

## Deliverable checklist

- `FINDINGS.md` — three findings, each with evidence chain and capsule IRIs.
- `JOURNAL.md` — this file.
- Working artifacts: `qrun.py`, `queries/*.sql`, `work/query_outputs/*.txt`,
  `query-ledger.jsonl`, `work/payloads/*.json` (staging payloads),
  `work/record_observations.py` (batch observation recorder),
  `work/record_observations_results.json`.
- `capsule.sqlite` — see "Final capsule state" above; `validate_graph`
  conforms, zero staged debt (none was ever created), 25 observations / 3
  claims / 28 evidence resources all linked (observation/evidence parity:
  every one of the 25 observations required and received evidence at write
  time, since the base shapes reject an `evidence_summary` without a
  source).
- `export_preflight` result: see the closing section of this journal /
  final report to the coordinator.
