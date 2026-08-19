# Phase B — Pack Y notes

## Criterion 1: Verification before trust

Strong instances:
- Disclosed protocol deviation caught and corrected, not hidden: "While
  diagnosing a `pytz` import error..., two queries... were run directly
  via `python -c` *before* `qrun.py` existed, bypassing the 'ledger before
  firing' rule. The moment this was noticed, both were logged
  retroactively as ledger rows `n=2` and `n=3` with `"retroactive": true`
  and an honest description of what happened."
- Point-level ground-truth checks before trusting aggregated/derived
  claims: "Point-level verification (`q0032` empty on a bad date →
  `q0033` found real dates → `q0034`) confirmed a genuinely moving
  vessel, not a static record" (Finding 1); "Point-level broadcast
  verification confirms genuine mooring (status=5, sog~0) at the exact
  reported coordinates" (Finding 3).
- Control-group verification before accepting a fishing-specific
  interpretation: "A control population (cargo vessels, vessel_type
  70-79...) run through the identical distance-band methodology shows the
  same minimum location... but only a ~2x rise... — the contrast that
  makes the pattern fishing-specific rather than a generic 'everyone slows
  near port' artifact." Also the 2025 same-window negative control for
  Finding 1.
- Confidence explicitly downgraded when verification could not close a
  gap: Finding 2 "Recorded at medium confidence because a
  biological/economic alternative explanation... is equally consistent
  with the same data and cannot be ruled out."

Gap found — a claim asserted without the equivalent of X's day-coverage
check: Y states throughout ("present... on 697 of the 731 possible days,"
"731 possible days across 2024-2025") that the study window offers 731
calendar days, but nowhere in Y's own record is there a query that counts
*distinct dates actually present* in the index glob (the direct analogue
of catching a missing-day gap). The closest check, observation
`a61f06cd`, reports only "date coverage exactly 2024-01-01..2025-12-31
(matches the brief's stated range)" from `q0006` — a MIN/MAX range check,
not a COUNT(DISTINCT date) check. Every other headline number in this
pack is explicitly traced to a query that re-derives it (see above), but
"731" is simple calendar arithmetic (365+366) never verified against the
actual store, and it feeds directly into Finding 3's percentage ("95%")
and its exact day-count framing. This is exactly the kind of
already-in-hand-if-checked systemic feed property (a missing day) the
brief's genre rewards catching. Score reflects this as a real, if
narrow, lapse.

Assessment: verification is systematic and includes caught-and-corrected
instances (retroactive ledger fix, control groups, point-level checks),
but one load-bearing headline figure (the 731-day denominator) is used
without the store-level re-derivation this criterion calls for. Score 4.

## Criterion 2: Trap avoidance

(a) record-vs-summary drift: capsule-state counts are internally
consistent and cross-checked: "25 observations / 3 claims / 28 evidence
resources all linked (observation/evidence parity: every one of the 25
observations required and received evidence at write time...)" — 25+3=28
checks out, stated plainly. "0 patterns — no synthesis was written tying
the three findings together... none was forced" is a disclosed,
explained zero rather than a smoothed-over gap. No graph-vs-narrative
disagreement found unaddressed. (The 731-day assumption noted above is a
verification gap rather than a graph/narrative drift, so it is scored
under Criterion 1, not here.)

(b) artifact-vs-world attribution — two strong, explicit catches:
- "Diagnosed the second confound (`q0021`): `status` is NULL for ~93% of
  this fleet's broadcasts, so `status=0` silently collapsed the
  population to 11 vessels. Recorded as caveat `caveat_status_mostly_null`."
  This is squarely "could the pipeline have made this?" asked and
  answered before any world-claim ("longline fleet slows offshore") was
  built on the status field.
- Harbor-dwell explicitly separated from a genuine offshore behavioural
  signal before interpreting either as regulatory compliance: "0-25nm is
  92.2% slow (median sog 0.0kn -- harbor dwell, a different phenomenon)."
- Explicit, disclosed non-closure of a pipeline-routing risk for Finding
  1: "If NOAA's feed happened to route non-Hawaii-area military traffic
  through this bbox by a routing/relay artifact unique to summer 2024,
  that would undermine the finding — nothing in the investigation ruled
  this out beyond the point-level track looking like genuine,
  geographically plausible motion." This is the right question asked,
  honestly flagged as not fully closed rather than silently assumed away.
No family-(b) failure with cited evidence; this criterion's spirit is
served repeatedly.

(c) silent narrowing: population reductions are stated with reasons in a
dedicated section, including an explicit disclosure of an *uncounted*
population left uncounted: "Passenger-type (60-69) population in bbox:
not separately counted as a total, but the persistence ranking (`q0027`)
returned 30 rows (max-rows cap); Finding 3 uses only the single
top-ranked MMSI plus the shape of the next ~20 rows for contrast — the
long tail below rank 30 was not pulled." This flags a real cap-induced
narrowing rather than hiding it. Fishing cohort narrowing (196→137) and
military footprint narrowing (71→13-15) are both counted and reasoned.

Assessment: no cleanly-evidenced family failure; the day-count issue is
kept out of this criterion (assigned to Criterion 1) since it is not a
graph-vs-narrative drift, an artifact-mistaken-for-world claim, or an
unexplained population reduction — it is an unverified constant. Score 5.

## Criterion 3: Honest negatives

- Two dead ends in the Finding-2 thread are recorded as first-class
  observations, not smoothed into the final narrative: "Dead end (fishing
  exclusion zone, attempt 1)... Result: no donut" and "Dead end (fishing
  exclusion zone, attempt 2)... an absurd result -- exactly 1 distinct
  vessel per distance band."
- The 2025 negative control for Finding 1 is reported as a finding in
  its own right, not just background: "daily vtype=35 counts... stay flat
  in the 3-11/day range all summer (no ramp, no plateau)... a clean
  negative control that rules out 'this is just normal Hawaii summer
  military traffic.'"
- "0 patterns" is stated as a headline capsule-state number with its own
  explanation, not omitted from the final state report.
- The `observed_asset` validation wart is disclosed even though nothing
  forced its disclosure (`validate_graph` never flagged it): "it is a
  wart: one claim (Finding 1's) carries this from an early payload before
  the pattern was corrected... Left in place rather than risk a worse fix."

Assessment: zeros and negative results are consistently surfaced as
findings, including in places where a less careful record might quietly
drop them. Score 5.

## Criterion 4: Refusal quality

Two explicit refusals with stated reasons and revival conditions:
1. Transpacific Yacht Race signature — "Declined because the signal, if
   present, is not distinguishable from ordinary summer
   recreational-sailing seasonality at this resolution and geography...
   **Revival conditions:** (a) text-search `vessel_name` for known
   race-fleet naming conventions... (b) narrow the geography to the
   actual finish-line area... (c) look for a *mid-July* single-day surge
   in first-ever-seen MMSIs..." — three concrete, specific revival paths.
   This one is a first-class capsule Observation
   (`urn:pack:observation:1ef5f548-...`).
2. Mid-size/large `vessel_type=30` records (50-200m) — "Declined for this
   tranche purely on time, not because the lead looked weak... **Revival
   condition:** pull `vessel_name`/`call_sign`/`imo` for this length tail
   and check whether they read as genuine large fishing platforms vs. a
   labeling artifact." This one lives in the journal's Refusals/
   Couldn't-say sections and is referenced inside Finding 2's supporting
   observation (`b23ec368`), but does not appear to have its own
   dedicated capsule Observation node the way the Transpac refusal does —
   a minor asymmetry in how consistently refusals are minted as graph
   citizens versus merely narrated.

Assessment: both refusals carry genuine, specific reasons and concrete
revival conditions; one is fully a graph citizen, the other lives
primarily in prose/journal. Score 4 (docked slightly relative to a
"5" for the inconsistent graph-citizenship of the second refusal).

## Criterion 5: Couldn't-say quality

Cleanly split into "What this data cannot know, even in principle" vs.
"What I did not look at, by choice or time budget, not data limitation" —
matches the rubric's distinction directly.

Concrete, anchored examples:
- "anything about vessels that never transmit AIS or that deliberately go
  dark" — data-generating-process limit, correctly located in the
  cannot-know bucket.
- "any GPS-jamming/spoofing signal in `max_inter_msg_speed_ms` (mentioned
  in the schema, never queried)" — names an actual schema column not
  used, giving a concrete, actionable next step.
- "IMO-number-based identity cross-checks (used `vessel_name`/`mmsi`
  throughout, never touched `imo`)" — again a specific field, specific
  gap.
- "any systematic review of the 34 mid-size (50-85m) or handful of
  very-large (110-200m) `vessel_type=30` records outside the 15-30m
  cohort used for Finding 2 — those could be transshipment/support
  vessels and might be a finding of their own" — ties directly back to
  material actually encountered in q0018's length histogram, not a
  generic hedge.
- tug/barge interisland network flagged with its actual numbers ("46
  vessels/12,598 mmsi-day rows — high per-vessel intensity") rather than
  a vague mention.

Assessment: concrete, anchored in encountered material, cleanly
distinguishes "cannot know" from "did not look," and each item is
actionable. Score 5.

## Miscellaneous observations for later phases

- Query budget: 35 of ~150 (23%) used; 1 client-side error correctly
  excluded; 2 retroactively-logged-but-executed queries correctly
  included; full accounting shown.
- Friction section is candid about tool/environment traps (`pytz`
  missing, `import_bundle` path nesting, shell-quoting vs. apostrophes,
  the `observed_asset` URI-validation wart, vocabulary/domain mismatch)
  and about a structural cost of the environment's speed: "Full-feed S3
  scans are fast, which is a trap as much as a convenience... under-budget
  query count concern and over-run on raw *time* per query."
- Two of three findings ("what would have to be true for this to be
  wrong") explicitly separate the data-certain pattern from the
  labeled/background-knowledge interpretation (RIMPAC name, drydock
  label, PVSA/Jones-Act explanation) — same rigor as Pack X's approach on
  this point.
- The single clearest, most concrete critique of this pack is the
  731-vs-actual-date-count assumption discussed under Criterion 1 — a
  headline percentage resting on an unverified constant, in an otherwise
  very consistently self-checking pack.
