# JOURNAL -- AIS-X-A1 (Hawaiian Islands region tranche)

## Setup log

1. Read `/home/codex/ais-x-a1/BRIEF.md` in full before touching any tool.
2. `venv/bin/python bridge.py tools` -- listed 24 MCP tools; `bridge.py call
   doxabase.get_doc` (docs `start_here`, `working_the_capsule`,
   `observation_recording`, `map_authoring`, `staged_revisions`,
   `mcp_tools`) to learn the recording model before writing anything.
   First bridge call auto-created `capsule.sqlite` (3.4MB, base ontology +
   46 shapes already present).
3. `import_bundle(kind="trig", spec={"path":"kh-vocab-seed.trig"})` --
   imported 427 shapes + 753 ontology triples (1,180 total). Note: the
   `kh:` vocabulary in the seed file turned out to be the *program's own*
   meta-vocabulary (episodes, arcs, delegation contracts, elicitation
   rounds -- concepts for studying agent/session behaviour itself, per an
   internal comment referencing a firewalled-off `aisv:` AIS-domain
   vocabulary that is deliberately *not* included here). None of it is
   AIS-domain content; it was imported anyway per the brief's literal
   instruction, and none of the findings use `kh:` terms -- domain claims
   below use `rc:Observation`/`rc:Claim`/`rc:Evidence` plus a small
   project-local entity namespace (`https://ais-x-a1.study/entity/...`)
   minted for vessels/fleets/the population.
4. `validate_graph(scope="all")` -> `conforms: true, result_count: 0`
   BEFORE any staging, as required.
5. Wrote `scripts/qrun.py`: a thin wrapper around the same DuckDB/S3
   connection logic as the provided `query.py`, whose only added behaviour
   is to append the ledger row to `query-ledger.jsonl` *before* firing the
   query (per brief S3), then run it and save full output to
   `outputs/qN.txt`, auto-incrementing `n` from the ledger's own history.
   This is not a new access path -- same env credentials, same bucket,
   same query.py-style DuckDB S3 setup -- just removes the risk of
   forgetting to ledger a query before running it.

## Investigation as it unfolded

**Orientation (q1-q3).** Confirmed the index layer spans 730 distinct
dates, not 731 (q1) -- directly reproducing the program's recorded
"2024-08-26 missing" caveat rather than assuming it. Compared box-overlap
vs. centroid-in-box as the region-membership predicate (q2): 124,335 vs.
124,038 day-rows, 2,046 vs. 1,982 distinct MMSI -- close enough (~0.25%
divergence) that the choice barely matters, but I adopted **overlap** as
the more literal reading of brief S1 ("all vessel activity in the box").
Vessel-type distribution (q3) showed fishing (type 30) as the single
busiest type by both day-rows (35,504) and distinct-MMSI (196), with tug
(type 52) a distant third in day-rows (12,598, only 46 MMSI) but with
disproportionate messages/vessel (154k vs. 75k for fishing) -- this one
table motivated two of the three eventual findings.

**Finding-1 thread (q4-q9, q19).** Pulled the passenger-type (60-69)
population (q4) looking for a distinctive operator; PRIDE OF AMERICA
(MMSI 366994450) stood out immediately at 697/730 days present and the
highest message count in its type. Pulled its full daily index history
(q5) and found a repeating spatial pattern by eye in the printed rows
before formalizing it: q6 (calendar-gap diff) found only 7 entirely-
missing dates, but q7 (same MMSI, box-membership filter *inverted*)
resolved those into a much larger and more interesting 26-day episode: a
motionless ~3-week stay near the Columbia River followed by a direct,
accelerating transit back toward Hawaii -- the shape of a scheduled
drydock, not a service gap. q8 isolated the Nawiliwili-cluster dates (97
of them) and q9's day-of-week histogram found 95/97 on one weekday --
strong, cheap, fully data-internal evidence of a weekly schedule. q19
cross-checked identity stability (name/IMO/length constant across both
years) to rule out MMSI reuse as a confound.

**Finding-2 thread (q10-q14, q21) -- the biggest population reduction and
the biggest correction in reasoning this session.** Starting hypothesis
was a "longline exclusion zone" story (a real, well-known regulatory
closure keeping longliners away from shore near the main islands). First
spatial grid (q10, type-30 fixes, 12-day sample) showed a *massive*
fishing-vessel hotspot at (21.3N, -157.9W) with 184,617 fixes -- the
opposite of what an exclusion-zone story predicts near shore. This was
the session's real dead end avoided just in time: that cell is not open
water, it is the fleet's home harbor. q11 (control grid, all non-fishing
traffic, same 12 days) confirmed general vessel traffic is dense there
too, and q12 (sog/status breakdown restricted to that one cell) showed
97%+ of the fishing fixes there are stationary (sog<0.5kt) -- a moored
fleet, not an active fishing ground. The story pivoted from "exclusion
zone" (which I cannot verify the geometry of without web/gazetteer
access, forbidden by brief S2) to "single-port fleet structure", which is
fully provable from the feed alone: q13 (full 2-year, not sampled) found
76.8% of all type-30 vessel-days concentrated in that one window, and the
three next-busiest inter-island harbor windows -- busy with *other*
traffic per q11 -- combine for only 12 fishing-vessel-days in the entire
2-year record (q14 detail: 6 small vessels, no pattern). q21 checked that
the 196-MMSI fleet population is not an artifact of the program's
registered year-boundary identity-freeze caveat (only 6/164 name changes
across the boundary).

**Finding-3 thread (q16-q18, q20).** Followed directly from the q3
observation that tug/pilot/passenger types produce outsized message
volume relative to their vessel counts. q16 ranked all 2,046 box MMSI by
total messages; q17 computed the Lorenz-style cumulative share (52.4% in
top 100, 85.1% in top 300); q18 characterized both tails by vessel_type
to confirm the concentration tracks *days present* (a behavioural
signature) and not just raw message count (which could be confounded by
transponder chattiness); q20 ruled out (mmsi,date) duplication as a
mechanical explanation for the concentration before trusting it.

**Explored and set aside: the tug/barge network (q15).** Pulled the
type-52 (tug) population hoping for a Young-Brothers-style interisland
hub-and-spoke story to complement fishing's single-port pattern. Names
split visibly into two clusters -- Hawaiian-language names (PI'ILANI,
KEKOA, MIKIOI, KAHU, MOI, MAMO) vs. mainland-style names (AMERICAN
CONTENDER/CHALLENGER/EMERALD, HENRY SAUSE, DANIEL FOSS, MONTLAKE) --
suggestive of two different operators, but confirming *who* operates them
would require corporate/registry records this capsule has no access to
(brief S2 forbids web/search access). Declined as a finding on its own;
recorded as a dead-end observation with a revival condition (see
Refusals below). The same underlying tug prominence instead fed Finding 3,
which needed no operator identity to stand up.

## Population reductions, with counts and reasons

| step | population | count | reason for reduction |
|---|---|---|---|
| 0 | nationwide feed, index layer, 2 years | 14,638,201 rows / 730 days | full feed-wide index scan (q1, q20) |
| 1 | -> Hawaii box (overlap), full 2 years | 124,335 day-rows / 2,046 MMSI | region filter per brief S1 (q2) |
| 2 | -> type-30 (fishing) subset of box population | 35,504 day-rows / 196 MMSI | vessel-type filter for Finding 2 (q3) |
| 3 | -> type-30 vessel-days inside the Honolulu window | 27,273 day-rows (76.8% of step 2) | spatial filter, full population (q13) |
| 4 | -> type-30 vessel-days inside the 3 neighbor-harbor windows | 12 day-rows (0.03% of step 2), 6 MMSI | spatial filter, full population, the "exception" set (q13/q14) |
| 5 | -> box population ranked by messages, top 100 / top 300 / bottom ~1500 | 52.4% / 85.1% / <1.1% of 54,422,109 messages | Lorenz-style rank cut for Finding 3 (q17) |
| 6 | -> 12-day cross-season broadcast sample (from 730 days) | 12 of 730 days | deliberate sampling for spatial-grid queries against the much larger broadcasts layer, spread across both years and all 4 seasons to avoid seasonal bias; full-population index queries used wherever the headline number needed to be exact (q13, q16, q17) rather than sampled |
| 7 | -> single MMSI (366994450) selected from the 60-vessel passenger-type population (q4) | 1 of 60 | selected as the most extreme/prominent case for Finding 1, by inspection after ranking by day-presence and message count |

The single day 2024-08-26 (missing from both layers, feed-wide) was
treated as no-coverage throughout, not vessel silence; all day-count
denominators use 730, not 731.

## Final capsule state (from a graph read, post-cleanup)

`project_brief` / `graph_overview` after all recording and both cleanup
passes:

```
observations: 24    claims: 3      patterns: 3     evidence: 27
source_spans: 17     shapes: 66     graph_revisions: 6
graph_patches: 4     graph_snapshots: 8
```

`rc:evidence` link-triple count = 27, exactly matching 24 observations +
3 patterns (one link each) -- verified parity, no orphaned evidence, no
observation without evidence. `validate_graph(scope="all")` ->
`conforms: true, result_count: 0`. `plan_staged_revision_recovery
(current_staged_work_only=true)` -> 0 rows: zero staged debt. Three
`stage_revision(kind="graph")` cleanup revisions were staged, dry-run
checked, and applied during this session (see Friction); no revision was
left staged-but-unapplied.

The 24 observations break down as: 4 general/orientation observations
(box-definition choice, day-coverage confirmation, vessel-type headline,
the tug/barge dead-end), 17 `kind="query_result"` observations (one per
load-bearing query behind the three findings), and 3 `kind="claim"`
observations (one per finding, each with a linked `rc:Claim` resource).
The 3 patterns synthesize the 17 query_result observations into the three
finding narratives; the 3 claims cite the patterns via
`proposed_assertions`. Full IRIs are listed in FINDINGS.md against each
finding.

## Friction

Two silent-failure traps in the MCP argument binding, both self-inflicted
and both caught by manual verification rather than by the tool surface
itself:

1. **`record_observation(kind="query_result")` silently drops kind-specific
   fields passed at the top level instead of nested in `spec`.** My first
   batch of 17 query_result calls put `execution_status`, `query_source_path`,
   `result_sources`, `scanned_source_handles`, `sample_size`, etc. as
   top-level JSON keys (matching the flat style that works fine for plain
   `kind="observation"` calls). The call *succeeded* with no error, but
   every one of those fields was discarded by argument binding, leaving a
   bare `rc:Observation` with **zero** evidence. Unlike a plain observation
   missing evidence, this one wasn't obvious from the success response
   alone (`observation_triples: 5, evidence_triples: 0` needed inspecting
   to notice) -- `validate_graph` *did* eventually catch it: 34 MinCount
   violations on `rc:evidence` after also duplicating the batch by
   re-running it once by accident while debugging a separate shell issue.
   Fixed by writing a diagnostic isolation test to confirm `spec`-wrapping
   was the actual cause, then removing all 35 malformed/duplicate
   resources via one `stage_revision(kind="graph")` removal patch
   (reconstructed exactly via `describe_resource` on each bad IRI, not
   from memory of what was sent -- to guarantee exact triple matches) and
   re-recording all 17 correctly.
2. **`record_observation(kind="claim")` has the identical trap and it is
   worse: it fails *silently even past `validate_graph`*.** `claim_text`,
   `claim_kind`, `claim_targets`, `confidence`, `observation_status`, and
   `proposed_assertions` sent at the top level are dropped the same way,
   but the fallback result is a plain `rc:Observation` with intact
   evidence (since `evidence_summary`/`evidence_sources` *are* real
   top-level flat parameters) -- so it satisfies the Observation SHACL
   shape and `validate_graph(scope="all")` reports `conforms: true` with
   nothing wrong. The only way this was caught was by manually
   `describe_resource`-ing a freshly created "claim" and noticing it had
   6 generic triples and no `rc:hasClaim`/`claim_iri` in the tool
   response, where a working call returns a distinct `claim_iri`. Fixed
   the same way: exact-triple removal (this time spanning two graphs,
   `observations` and `evidence`, in one patch) followed by
   correctly-`spec`-wrapped re-recording, which does return a `claim_iri`.
   A third, smaller cleanup was needed after that: the very first
   diagnostic test call (used to confirm the `spec` fix) had created a
   real, valid evidence+source-span pair whose parent observation was
   deleted in cleanup (1) without also deleting its evidence -- caught
   only because `graph_overview`'s evidence count (28) didn't match the
   `rc:evidence` link-triple count (27) in the predicate histogram.
   **Lesson for the next agent, stated plainly since the docs say kind-
   specific fields "go in spec" but every worked example in `get_doc`
   output shows a flat call shape for the common case:** for
   `kind="claim"` and `kind="query_result"` specifically, always
   explicitly nest every field beyond `summary`/`observed_*`/
   `evidence_summary`/`evidence_sources` inside a `"spec": {...}` object,
   and always inspect the raw JSON response for a kind-specific marker
   (`claim_iri` for claims; nonzero `evidence_triples` for query_result)
   rather than trusting the absence of an error.

Smaller friction: `query.py`'s default `--max-rows 50` needed to be
raised per-query for grid-shaped results (up to a few thousand rows);
`scripts/qrun.py` defaults to 200 and accepts an override, with full
output always retained in `outputs/` regardless of what's echoed to the
terminal, which mattered for the two >700-cell density-grid queries
(q10, q11).

## Couldn't-say (what this data cannot know, vs. what I did not look at)

**Cannot know from this data:**
- Why the fishing fleet is single-port (Finding 2) -- regulatory
  requirement, economic convenience, infrastructure availability
  elsewhere, or some mix. The data shows the pattern with high confidence,
  not the cause.
- Whether Finding 1's ~3.5-week absence is specifically a *drydock* as
  opposed to some other single-location, multi-week event (repair, crew
  matter, ownership transfer) -- the data shows the behavioural shape
  (static period bracketed by direct transits), not a stated purpose.
- Vessel ownership/operator identity beyond the self-reported name/IMO/
  call sign fields -- this is exactly why the tug/barge two-cluster story
  was declined rather than pursued.
- True AIS-off / dark-vessel activity at sea (program's own M3 caveat):
  silence means "not received," not "transponder off," for anything
  beyond terrestrial receiver range.
- Real-world harbor names with gazetteer-grade certainty -- identifications
  of the Kahului/Nawiliwili/Kona-area/Honolulu windows rest on general
  geographic knowledge plus internal cross-referencing against Pride of
  America's own confirmed stops, not an authoritative source (no web/
  documentation access permitted by brief S2).

**Did not look at, for time/budget triage, not because the data can't
answer it:**
- `h3_res15` / `geometry` columns -- used plain lat/lon throughout instead.
- `draft`, `cargo` code fields -- not touched by any of the three findings.
- `cog`/`heading` fields -- not used; Finding 1's "accelerating transit"
  language comes from consecutive-day centroid deltas, not course data.
- Seasonal variation within the fishing fleet's single-port pattern
  (Finding 2) -- the 12-day sample spans all 4 seasons but was not broken
  out by season.
- Gap-duration distribution for the fishing fleet (short local trips vs.
  multi-week offshore voyages) -- a natural companion analysis to Finding
  2, using the same coverage-gap machinery as Finding 1's drydock episode;
  set aside to keep verification depth on 3 findings rather than breadth
  across 4.
- Transceiver class (A/B) as a control variable for Finding 3's
  message-volume concentration -- flagged explicitly as a residual
  confound in FINDINGS.md rather than left unmentioned.

## Refusals -- finding-candidates declined, with reasons and revival conditions

1. **Interisland tug/barge two-operator network** (vessel_type 52, from
   q15). Declined because confirming real operator identity behind the
   two visually distinct name clusters would require corporate/registry
   records outside this capsule's access (brief S2). Recorded as a dead-
   end observation. **Revival condition:** a future tranche with access to
   vessel-registry or corporate-ownership data could turn this into a
   real operator-segmentation finding; the underlying route/frequency data
   is already interesting, only the identity layer is missing.
2. **Longline exclusion-zone compliance** (the original hypothesis behind
   Finding 2's investigation thread). Declined as its own finding because
   I have no independently verified geometry for the actual regulatory
   boundary and no web/gazetteer access to obtain one (brief S2); a claim
   of "compliance with a specific regulatory zone" would rest on an
   unverifiable boundary. Substituted with the fully data-provable
   "single-port fleet structure" finding, which is a strict subset of what
   the exclusion-zone story would have needed to show (it demonstrates a
   real spatial pattern without asserting *why* it exists). **Revival
   condition:** if a future tranche has access to the actual exclusion-
   zone boundary geometry, re-run the spatial analysis against it directly
   rather than against harbor proximity as a proxy.
3. **Fishing-trip gap-duration bimodality** (short day-trips vs. multi-week
   offshore voyages, a temporal companion to Finding 2). Declined for time/
   budget triage -- not because it looked weak, but because deepening
   verification on 3 solid findings seemed more valuable than adding a
   4th shallower one within this session. **Revival condition:** straight-
   forward next step using the same per-MMSI gap-detection approach as
   Finding 1's drydock episode, applied to the 196-MMSI fishing population
   instead of one vessel.

## Query-budget accounting

21 of ~150 budgeted data-bearing S3 queries used (14%), all logged in
`query-ledger.jsonl` before firing, all succeeded (0 client-side errors,
0 queries excluded from the budget for erroring). Every query's full
output is retained under `outputs/q1.txt` .. `outputs/q21.txt`.
`scripts/qrun.py` is the re-runnable wrapper used for all 21 queries;
`query.py` (the originally provided tool) was read to understand its
DuckDB/S3 connection pattern before writing the wrapper, but never
executed directly -- all 21 data queries went through `qrun.py`, so the
full query-ledger.jsonl accounts for every query actually fired this
session.
