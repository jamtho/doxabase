# JOURNAL — AIS-X open exploration, Hawaiian Islands tranche

Analyst: ais-x-a2-analyst. Region: 18.0–23.5N, −161.5 to −154.0W, WGS84,
2024‑01‑01 through 2025‑12‑31. This is the human-readable render; the
observation stream in `capsule.sqlite` is the durable original.

## Setup log

1. Read `BRIEF.md` in full before touching anything.
2. Inspected the working directory: `bridge.py`, `query.py`,
   `assemble_context.py`, `kh-vocab-seed.trig`, `ais-capsule-frozen.sqlite`,
   a pre-built `venv`. Confirmed S3-style credentials
   (`MINIO_ENDPOINT`/`MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY`) present in the
   environment without echoing them.
3. Read `bridge.py`'s tool list and the `doxabase` agent docs
   (`start_here`, `working_the_capsule`, `observation_recording`, the
   `mcp_tools` reference) via `doxabase.get_doc` to understand the
   recording API before writing anything — this is the installed wheel
   inside my working directory, not outside documentation.
4. Free orientation call: `python3 assemble_context.py
   ais-capsule-frozen.sqlite --describe` — confirmed the frozen capsule
   holds 14 methods, a 29-entry caveat registry, ~20 vessel stories, 149
   observations / 102 claims, and explicitly nothing about Hawaii.
5. First bridge call: `doxabase.import_bundle(kind="trig",
   path="kh-vocab-seed.trig")` — this both created `capsule.sqlite` and
   loaded 1,180 triples (753 ontology + 427 shapes).
6. `doxabase.validate_graph(scope="all")` → `conforms: true, result_count:
   0`, before any staging, as required.
7. `doxabase.project_brief` — no gates, empty datasets/observations/claims,
   66 shapes only. Clean start confirmed.

One real hiccup during setup, corrected immediately (see Friction): I ran
two ad-hoc DuckDB debug calls directly rather than through a ledgered
wrapper while isolating a client-side error. One is retroactively
ledgered as `n=2` with a clear "RETROACTIVE / out-of-band" label; the
other never touched S3 rows (a schema-only `DESCRIBE`) and is folded into
that same note. From `n=3` onward every S3-touching call went through
`scripts/runq.py`, which writes the ledger row before firing, as the
brief requires.

## How the investigation unfolded

**Tooling first.** Before querying, I built `scripts/runq.py`: a thin
wrapper around the same DuckDB/httpfs connection recipe as the provided
`query.py`, but one that (a) writes the ledger row *before* firing, (b)
saves full query output to `query-outputs/` instead of a 50-row preview,
and (c) can optionally `COPY` a full result to a local Parquet file. This
turned out to be the single highest-leverage decision of the session: it
let me pull the entire Hawaii-box slice of the index layer in one S3
query (query 6) and then do all subsequent exploratory aggregation
*locally*, for free, against that Parquet file — dozens of local
DuckDB/pandas queries never touched the ledger because they never touched
S3.

**A real environment bug, fast triage.** The very first query (`n=1`)
failed client-side: DuckDB's Python client needs `pytz` to materialize
`TIMESTAMP WITH TIME ZONE` values, and `pytz` is not installed in the
provided venv (confirmed: not importable, no `pip` binary in the venv
either, and I did not look outside my working directory for a wheel to
install it, per the access rules). Isolated the exact cause with a
`DESCRIBE` (schema-only, no row data) showing `first_timestamp` /
`last_timestamp` in the index layer and `timestamp` in broadcasts are
both `TIMESTAMP WITH TIME ZONE`. Workaround: `col AT TIME ZONE 'UTC'`
converts to a plain `TIMESTAMP`, which the client handles fine — used in
every subsequent query that needed a timestamp value.

**Recon via the index layer.** With the workaround in hand: query 4
confirmed `read_parquet('s3://ais-noaa/index/*/ais-*.parquet')` glob-reads
the whole two-year feed in one query (14,638,201 rows, 730 distinct
dates — one short of the 731 calendar days in the window; see Population
reductions). Query 5 counted candidates whose daily bounding box overlaps
the study box (124,335 rows, 2,046 distinct MMSI). Query 6 pulled every
column for that candidate set to a local Parquet file — the backbone of
everything that follows.

**Local mining turned up three threads fast.** A per-MMSI rollup by
AIS ship-type immediately showed fishing (30) dominant by raw
vessel-days, but tug/tow types (31/32/52) forming an unusually
persistent, low-count population; a passenger-type (60–69) rollup showed
one MMSI (PRIDE OF AMERICA) as a clear outlier on every axis; a
week-by-week histogram of newly-arriving sailing-type (36) MMSI showed a
sharp July spike in *both* years. All three were pursued in parallel from
that point.

**Consulting memory before digging further.** Six consultations
(2,900 of the 4,000-token budget, well under the 12-call cap):
1. MMSI identity traps — motivated checking the tug/tow roster for
   shared/reassigned MMSIs before trusting day-coverage as "the same
   vessel." Directly led to catching MMSI 368243940 (a multi-emitter/GPS
   artifact, not a real Hawaii vessel) and MMSI 366887950 (a genuine
   rename, GUARDSMAN→TITAN).
2. Index-metric caveats (`distance_m`, `sog`, `status_codes`) — the
   NavStatus-reliability observation returned (status codes are not a
   fixed-rate ground truth, varies by location) is why Finding 1 leans on
   *position clustering and broadcast ground truth*, not `status_codes`
   counts, for its "stop" language.
3–4. Two attempts at "two-point-shuttle census" (a named method in the
   frozen capsule's method list) — first a paraphrased question, then the
   literal term. Both returned "nothing strong" (score 11.3, then
   explicit emptiness). Proceeded on my own judgement per the assembler's
   own guidance, and did — position-clustering plus a broadcast-level
   route check, described in Finding 1.
5. Feed-outage detection — confirmed 2024‑08‑26 is a global missing day
   (both layers, all vessels), matching what I had already found myself
   independently via the 730-vs-731 discrepancy in query 4. Consulted
   *after* being surprised by my own data, exactly as the brief
   recommends.
6. Port-call detection method — returned an adjacent result (the M13
   feed-outage-census dataset) rather than direct threshold guidance;
   used it mainly as further evidence that micro-outages are a real
   background phenomenon to keep in mind, and proceeded with my own
   position/speed-based stop logic rather than importing thresholds I
   was not shown.

**Ground-truthing.** For each thread I dropped from the free/local index
layer down to the metered broadcast layer exactly once or twice, to
verify a specific claim against raw per-message data rather than
aggregates:
- Query 7: a first attempt at a tug's broadcast track (2024‑06‑01…14)
  came back showing the vessel stationary in Honolulu the entire window —
  a genuine dead end, kept in the ledger and in Finding 1's evidence
  chain rather than quietly discarded. The index layer had already shown
  this vessel *does* leave Oahu on other dates, so query 8 targeted one
  of those dates instead and produced the clean multi-port track used in
  Finding 1.
- Query 9 and 11: nationwide (not Hawaii-restricted) index pulls for
  samples of the July-pulse sailing vessels, tracing them back to real
  coastal departure points before the Hawaii box — the strongest single
  piece of evidence in the whole session, because it turns "a lot of new
  MMSIs appeared in July" into "these specific vessels really did sail
  from the US mainland, went dark for days, and reappeared near Hawaii."
- Query 10: one broadcast-level spot check of Pride of America's Friday
  Kauai stop, confirming `status=5`, `sog=0.0`, and the raw `vessel_name`
  field.

**A late self-audit caught two real numeric errors.** Before writing
FINDINGS.md I went back through every number in the three claims and
re-derived each one from a fresh, exact query rather than trusting my
earlier reading of a printed table. Two were wrong: Finding 1's
day-coverage range (I had described a hand-picked list of "top" vessels,
not the strict top 19, so the stated range 598–729 should have been
618–729, and "17 of 19" should have been "16 of 19"); Finding 3's MID
percentages (I had read "~89%/~85%" off a table by eye; the true,
precisely-summed values are 81.3%/69.7%), and its day-concentration
figure had conflated the two-year combined pulse count (91) with the
2024-only window (actually 47). Both corrections are recorded properly
in the capsule (new corrected claims `*-v2`, `record_claim_reconsideration`
with `relation="refines"` linking old to new) rather than silently
edited — see Capsule end state and FINDINGS.md's "self-audit" notes. In
both cases the qualitative finding survived unchanged; only the precise
numbers moved (and in Finding 3's case, the correction if anything
*strengthens* the claim).

## Population reductions (counts and reasons)

| Step | Population | Count | Reason |
|---|---|---|---|
| Feed-wide index rows, 2024–2025 | all (mmsi,date) rows | 14,638,201 | full glob read, query 4 |
| Distinct calendar days covered | — | 730 of 731 | 2024‑08‑26 missing feed-wide (confirmed via consultation 5); not a Hawaii-specific gap |
| Candidate Hawaii-box (mmsi,date) rows | bbox-overlap filter | 124,335 | query 5/6; **overlap, not containment** — a vessel's full-day bounding box need only touch the study box, so some candidates may only graze it (see Couldn't-say) |
| Distinct candidate MMSI | — | 2,046 | query 5 |
| Tug/tow-type (31/32/52) candidate MMSI | type filter | 85 | local, query-6 file |
| — minus 1 excluded artifact (368243940) | data-quality exclusion | 84 genuine | multi-emitter/GPS-corruption signature, not a real Hawaii vessel (f1_o5_caveat) |
| Top tug/tow tier used in Finding 1 | strict top-19 by day-coverage | 19 | re-derived exactly after catching the hand-picked-list error (f1_o7_correction) |
| Passenger-type (60–69) candidate MMSI | type filter | not separately counted as a headline number; used only for the >300-day persistent-vessel comparison table in Finding 2 | |
| Sailing-type (36) candidate MMSI | type filter | 309 (91 pulse + 218 baseline) | f3_o3/f3_o7 |
| 2024 pulse window population | date-window filter | 47 | corrected from an earlier conflation with the 2-year combined figure |
| 2025 pulse window population | date-window filter | 44 | |
| Combined 2-year pulse population | union | 91 | 47+44, used only for the MID-composition test |
| Nationwide trace sample (2024) | convenience sample | 12 of 91 | not a census — see Refusals |
| Nationwide trace sample (2025) | convenience sample | 10 of 91 | not a census — see Refusals |

## Final capsule state (from a graph read)

`doxabase.project_brief` and `doxabase.graph_overview`, read after all
recording and corrections:

- `observations`: 24 (17 plain findings-support observations across the
  three threads, 2 self-audit correction observations, 3 claim-observations
  from the corrected `*-v2` claims, plus the 2 original claim-observations
  now superseded in status — see below for the exact roll-up)
- `claims`: 5 — `hawaii-tug-tow-fleet` (original, `observationStatus`
  now `rc:Superseded`), `hawaii-tug-tow-fleet-v2` (current),
  `pride-of-america-weekly-cycle` (current, never needed correction),
  `july-sailing-arrival-pulse` (original, superseded),
  `july-sailing-arrival-pulse-v2` (current)
- `patterns`: 3 (one synthesis per finding, each linking its constituent
  observations and its claim — the two patterns for Findings 1 and 3
  still formally cite the *original* claim IRIs in `supporting_claims`
  since patterns are not auto-updated by a reconsideration; the
  reconsideration record is the authoritative link from original → `-v2`)
- `evidence`: 27
- `shapes`: 66 (from the imported `kh-vocab-seed.trig`; unchanged)
- `map` / `ontology` / `history` / project-owned `shapes` graphs: empty —
  this tranche recorded findings as observations/claims/patterns, not
  dataset-schema map facts, which is the right lane per
  `working_the_capsule`'s graph-placement guidance for domain findings
  rather than dataset metadata
- `doxabase.validate_graph(scope="all")`: **`conforms: true, result_count:
  0`** (confirmed as the very last action before writing this journal)
- `doxabase.plan_staged_revision_recovery`: `total_count: 0` — zero staged
  revision debt (no `stage_revision`/`apply_staged_revision` calls were
  made at all this session; every finding was recorded directly as
  observations/claims/patterns, which is the correct lane for
  investigative findings about the world rather than map-fact staging)
- `doxabase.export_preflight(kind="handoff_bundle")`:
  `scanner_clean: true`, `sensitive_literal_count: 0`,
  `validation_conforms: true`, `decision: "clean_by_scanner_only"`,
  `shareability_review_required: true`,
  `shareability_review_status: "required_not_completed"`,
  `artifact_disposition: "local_only_pending_shareability_review"`.
  Per the brief, the shareability review itself is the owner's call, not
  mine — reported here, not acted on.

Every IRI referenced above is enumerated with its minted form in
`staging/all_iris.json`.

## Query-budget accounting

- Budget: ~150 data-bearing S3 queries.
- Ledgered rows: 11 (`query-ledger.jsonl`, `n=1`…`n=11`).
- `n=1`: client-side error (missing `pytz`), does not count against
  budget per the brief's rule, and no S3 bytes were read.
- `n=2`: retroactively ledgered, schema-only `DESCRIBE`, no row data
  fetched — counted here as effectively free/orientation, not a
  data-bearing analysis query.
- `n=3`–`n=11`: **9 real data-bearing queries**, all through
  `scripts/runq.py`. Of these, `n=6` (the full Hawaii-box index
  extraction) did essentially all the heavy lifting; `n=9` and `n=11`
  were the most valuable per query (nationwide vessel traces that turned
  the sailing-pulse thread from suggestive to load-bearing).
- **9 of ~150 used — a large margin of unused budget remained** at the
  point I judged the three findings sufficiently strong and moved to
  recording and write-up. I did not spend the remainder on a fourth or
  fifth thread because the brief asks for the three *best* findings, not
  the most queries spent; see Refusals for what the unused budget would
  have gone to if I had pursued a fourth thread.
- Consultations: 6 of a maximum 12, 2,900 of 4,000 tokens budgeted
  (`consultations.jsonl`, `assembly-1.md`…`assembly-6.md`).

## Friction (what the tooling made hard)

- **`pytz` missing from the provided venv** blocked every query that
  touched a `TIMESTAMP WITH TIME ZONE` column (both `timestamp` in
  broadcasts and `first_timestamp`/`last_timestamp` in the index) until I
  found the `col AT TIME ZONE 'UTC'` workaround. This is a real gap
  between the provided `query.py` helper and the actual schema: `query.py`
  as shipped cannot run a plain `SELECT *` against either layer without
  hitting this error. I did not attempt to install `pytz` from outside my
  working directory (per the access rules), and did not modify the
  provided `query.py`; instead I built `scripts/runq.py` with the
  workaround baked into every query I wrote.
- **One access-rule slip, corrected in place.** While isolating the
  `pytz` error I ran two `DuckDB`-over-S3 calls directly rather than
  through a ledgered wrapper (the wrapper did not exist yet). Both are
  schema-only and neither returned row data, but the letter of the rule
  ("ledger EVERY query... BEFORE firing it") was still violated for a few
  minutes at the very start of the session. Corrected by retroactively
  ledgering the DESCRIBE call with an explicit "RETROACTIVE / out-of-band"
  label the moment I noticed, and by never repeating the pattern —
  every query from `n=3` onward was ledgered first, through the wrapper,
  automatically.
- **`record_observation`/`record_pattern`'s custom-IRI parameters are
  inconsistently honored.** For `kind="claim"`, a custom `claim_iri` /
  `observation_iri` / `evidence_iri` passed inside `spec` was respected.
  For plain `kind="observation"` calls, an `observation_iri` /
  `evidence_iri` passed at the top level (as the `mcp_tools` doc's
  wording implied it should be, since those fields are listed as
  auto-merged) was silently ignored and a `richcanopy.org/.../generated/`
  IRI was minted instead — no error, just quietly different behaviour
  from the documented merge rule. Same for `record_pattern`'s `pattern_iri`
  even when nested under `spec`. Worked around by resolving real minted
  IRIs from each call's own return value before building anything that
  needed to reference them (see `scripts/build_specs2.py`'s docstring).
  This cost some rework (had to reset the capsule once, early on, after
  discovering the pattern) but nothing was lost.
- **`record_claim_reconsideration`'s `older_claim_status` enum is
  stricter than the relation vocabulary suggests.** Passing
  `older_claim_status: "rc:Refined"` (a natural-seeming value to pair with
  `relation: "refines"`) is not a valid `observationStatus` value — the
  controlled list is `Tentative/Checked/Weakened/Contradicted/Superseded/
  Promoted` only, no `Refined`. This produced a `validate_graph` failure
  (and a live `export_validation_review` gate) that I fixed by re-calling
  with `older_claim_status: "rc:Superseded"`; the second call's identical
  `(older_claim, newer_claim, relation)` key overwrote the bad status
  triple rather than duplicating it (confirmed by the `status_triples: 1`
  in both calls' return value and by `validate_graph` conforming
  afterward), so no core-API fallback was needed.
- **The provided `query.py` truncates at 50 rows by default** and has no
  option to write a full result set anywhere — fine for point lookups,
  but I needed full result sets for local re-aggregation, hence
  `scripts/runq.py`'s `--parquet`/`--csv` flags. Not a defect exactly
  (the brief says "how you use the two layers is yours to decide"), but
  worth flagging since a future analyst starting from `query.py` alone
  would hit the same wall.
- **No canonical port/harbor coordinate reference is available.** Several
  of Finding 1's location clusters read, by general geography, as
  Honolulu Harbor, Kawaihae, and waters off Hilo and Maui — but nothing
  in this exercise's scope lets me verify that against an authoritative
  harbor-coordinate table. I have kept those identifications as informal,
  hedged color commentary, never as part of a staged claim's load-bearing
  content.

## Couldn't-say (what the data cannot know, vs. what I did not look at)

**What this data cannot know:**
- Vessel ownership, operating company, or flag-state registration beyond
  what the `vessel_name` field suggests by naming convention. I did not
  assert "Foss Maritime" or "Young Brothers" as fact anywhere in the
  staged claims, even though the naming patterns are suggestive.
- Cargo contents of any tow/barge combination (the `cargo` code field
  exists but was not part of this investigation's evidence chain).
- The regulatory reason (Jones Act/PVSA cabotage) behind Pride of
  America's unique operating pattern — genuinely outside what AIS data
  can show; flagged explicitly in Finding 2 as background interpretation,
  not part of the evidenced claim.
- The identity of any organizing event (race, rally, or otherwise) behind
  the July sailing pulse — no event calendar or vessel-registration
  overlay is available to this analysis; the claim is deliberately scoped
  to only what the AIS pattern itself supports.
- Whether any of the excluded/caveated MMSIs (368243940, 366887950)
  represent a broader class of similar cases elsewhere in the 85-vessel
  tug/tow roster — I checked the two anomalies that surfaced during
  ordinary inspection, not every one of the 85 systematically.

**What I did not look at (time/scope, not data limits):**
- The fishing fleet (type 30), the single largest population by raw
  vessel-days in the box, was noted early and deliberately not pursued as
  one of the three findings — see Refusals.
- The tanker/fuel-supply population (types 80–89) and the Coast
  Guard/law-enforcement presence (types 51/55) were seen in the initial
  type breakdown and not investigated further.
- A full (not sampled) nationwide trace of all 91 July-pulse sailing
  MMSIs, and of the full 2025 pulse population beyond the 10-vessel
  sample.
- A systematic audit of all 85 tug/tow MMSIs for identity anomalies
  (only the two that surfaced incidentally were checked).
- Draft/cargo event reading for any vessel population in this region — a
  documented method in the frozen capsule that I did not have occasion to
  apply here.

## Refusals (finding-candidates declined, with reasons and revival conditions)

1. **Fishing-fleet duty-cycle story** (type 30, the largest single
   population by raw vessel-days in the box). Declined in favor of the
   tug/tow, Pride of America, and sailing-pulse trio for topical
   diversity (industry/infrastructure, single-vessel behaviour, seasonal
   event) rather than two industry-population stories. **Revival
   condition:** would need index-based trip-length/absence-gap
   segmentation (in the spirit of the frozen capsule's silence-gap
   method) plus verification that extended absences reflect genuine
   distant-water longline trips rather than simple reception gaps —
   worth a dedicated session, not a bolt-on to this one.
2. **Tanker/fuel-supply story** (types 80–89, 2,619 candidate mmsi-days).
   Noted in the initial type breakdown, not investigated. **Revival
   condition:** trace specific tanker MMSIs' call frequency/cadence to
   Hawaii's ports to characterize the fuel-supply rhythm.
3. **Coast Guard/law-enforcement presence** (types 51/55). Noted, not
   pursued — expected/unsurprising on its own without a sharper angle.
   **Revival condition:** a specific behavioral question (e.g., patrol
   pattern regularity) rather than mere presence.
4. **Naming a specific ocean race for Finding 3.** Deliberately declined
   even though the pattern is highly suggestive (two distinct mainland
   departure regions converging on Hawaii the same week, in two
   different years). **Revival condition:** an authoritative external
   event calendar or vessel-registration cross-reference, which is out of
   scope/access for this tranche by design (no web, no external
   documentation).
5. **Precise official port/harbor identification** for Finding 1's
   location clusters. Used informally as hedged color commentary based on
   general geography, not as load-bearing claim content, because no
   canonical port-coordinate reference is available in this exercise.
   **Revival condition:** access to an authoritative harbor-coordinate
   table.
