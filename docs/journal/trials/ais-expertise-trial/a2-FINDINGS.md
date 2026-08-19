# FINDINGS — AIS-X open exploration, Hawaiian Islands tranche

Region: latitude 18.0–23.5N, longitude −161.5 to −154.0W (WGS84), 2024‑01‑01
through 2025‑12‑31. Analyst: ais-x-a2-analyst. All figures below are
re-derived exactly as stated; where an earlier hand-read figure turned out
to be wrong, the correction and the reconsideration trail are described
in-line — see the "self-audit" note under Findings 1 and 3.

---

## Finding 1 — A small, persistent tug/tow fleet is Hawaii's inter-island freight backbone

**The finding.** Hawaii has no bridges, tunnels, or rail links between its
islands: everything that cannot fly moves by water. In this AIS feed, that
freight movement is dominated by a strikingly small population of
tug/towing-type vessels (AIS ship-type 31 "towing", 32 "towing, large", 52
"tug"): 85 distinct MMSIs in total appear in the Hawaii box over the two
years, but the top 19 of them by day-coverage are present on 618–729 of the
730 available feed-days — i.e. almost every vessel in this top tier
transmitted from inside the box on 85–100% of all days the feed covers. Of
those 19, 16 range across more than two widely separated geographic
clusters (Oahu plus at least one neighbor island); only three (PI ILANI,
MIKIOI, TIGER2) stay in a single Oahu-area cluster and read as harbor tugs
rather than line-haul vessels. Broadcast-level (raw per-message) ground
truth for one exemplar, KAPENA GEORGE PANUI (MMSI 338033000, 709 days,
rank 5), shows a real six-day, four-port working cycle: moored at Kawaihae
on Hawaii Island → an overnight transit to Honolulu, Oahu → a working stop
off Maui → back to Honolulu → a long run past Maui to waters off Hilo,
Hawaii Island → return toward Honolulu — with the vessel essentially never
idle beyond its two harbor turnarounds. The named sub-fleets are
recognizable even from vessel names alone: a "KAPENA `<person>`" series
(Hawaiian-language "Captain" + name, a Young Brothers-style naming
convention), an "AMERICAN `<word>`" series, a "`<name>` SAUSE" pair, and a
"TIGER `<n>`" numbered series, among others.

**Why it's interesting.** It is easy to think of an island chain's economy
in terms of the ferries and planes carrying people; the freight backbone —
the thing that actually moves fuel, containers, and building materials
between islands — is far less visible and, in this data, turns out to be a
strikingly small, highly disciplined population of working vessels running
what amounts to a private highway system. The picture that emerges (a
handful of tugs almost never off duty, doing multi-hundred-kilometre runs
day after day) is a vivid, concrete illustration of what "no bridges"
means logistically.

**Full evidence chain.**
- Query 5 (`query-ledger.jsonl#n=5`): count of index-layer (mmsi,date) rows
  whose daily bounding box overlaps the study box, across
  `s3://ais-noaa/index/*/ais-*.parquet` — 124,335 rows, 2,046 distinct
  candidate MMSIs.
- Query 6 (`#n=6`): full-column extraction of that same filtered row set to
  a local Parquet file (`query-outputs/q006_hawaii_box_index.parquet`,
  124,335 rows). This one query is the basis for essentially all
  downstream local (S3-free) analysis: day-coverage per MMSI, identity
  stability (distinct vessel_name/IMO per MMSI), and 0.5°-grid
  region-visitation counts for the type-31/32/52 population.
- Query 7 (`#n=7`): a first broadcast-level pull for KAPENA GEORGE PANUI
  (2024‑06‑01…14) — a dead end kept for the record: the index showed this
  vessel centred on Oahu that whole month, and the broadcast track
  confirms it, so this window shows no transit.
- Query 8 (`#n=8`): a second broadcast-level pull, 2024‑01‑06…11, chosen
  because the local rollup of query 6 showed this vessel's centroid away
  from Oahu on those calendar dates. This is the track described above
  (`query-outputs/q008_kapena_track_jan6_11.parquet`, 5,596 raw position
  reports), segmented locally into stop/transit legs with pandas.
- Consultations 1 and 2 (`consultations.jsonl#n=1,2`) primed a check for
  MMSI-identity traps and index-metric caveats; they supplied no
  Hawaii-specific numbers, only the questions to ask of my own data.
  Acting on that, I found and excluded one artifact MMSI (368243940,
  "CAPTAIN ROB": Georgia-area centroids in 2024, billions-of-metres daily
  "distance" in 2025 — a clear multi-emitter/GPS-corruption case, not a
  real Hawaii vessel) and one genuine renaming (366887950: GUARDSMAN →
  TITAN, same operating pattern before and after, read as one vessel, not
  a shared MMSI). Neither is in the top-19 tier so neither affects the
  headline numbers, but both are recorded.

**Capsule IRIs.**
- Observations: `f1_o1`–`f1_o6` and the self-audit correction `f1_o7` —
  minted IRIs listed in `staging/all_iris.json` (e.g. `f1_o1` →
  `https://richcanopy.org/doxabase/generated/observation/e4aefec2-16fa-4c27-a9d8-721f688f252d`).
- Claim (original): `https://ais-x-a2.study/claim/hawaii-tug-tow-fleet`
- Claim (corrected, current): `https://ais-x-a2.study/claim/hawaii-tug-tow-fleet-v2`
- Reconsideration (`refines`, original superseded in status only):
  `https://richcanopy.org/doxabase/generated/claim-reconsideration/ee948f47-17ca-40f4-bf3c-a125df1436da`
- Pattern (synthesis): `https://richcanopy.org/doxabase/generated/pattern/57cc808b-0377-4e07-a00a-a953efc42dcf`

**Self-audit note.** The first version of this claim stated the top-tier
day-coverage range as "598–729" and "17 of 19" vessels as multi-region,
numbers read off a hand-picked list assembled during exploration rather
than the *strict* top 19 by day-coverage. A final re-verification pass
(recorded before writing this document) caught the discrepancy,
re-derived the true top-19 set by exact query, and produced the corrected
range (618–729) and count (16 of 19) used above. The original claim was
reconsidered with relation `refines`; its `observationStatus` is now
`rc:Superseded`. The qualitative finding is unchanged — only the precise
figures moved, and the exemplar vessel (KAPENA GEORGE PANUI) was
unaffected either way.

**What would have to be true for this to be wrong.** The core claim would
fail if: (a) the top-19 vessels are not actually persistent single
identities but heavily shared/reassigned MMSIs stitching together
multiple physical vessels — checked for directly (§ evidence above) and
not found for this tier, though the check was not exhaustive across all
85 candidates; (b) the 0.5°-grid "region visitation" measure is a poor
proxy for genuine multi-island operation — mitigated by the
broadcast-level ground truth for one exemplar, but that ground truth is a
single vessel and a single 6-day window, not a full-fleet audit; (c) the
region-overlap candidate filter itself is systematically pulling in
vessels that merely pass near, not through, the box — this is a real
limitation of a bounding-box test (see JOURNAL.md, Friction), though it
would need to be biased specifically toward the tug/tow type code to
undermine this finding, which seems unlikely given how tightly clustered
these vessels' actual positions are around known island locations.

---

## Finding 2 — Pride of America is a structurally unique resident cruise operation

**The finding.** One vessel, MMSI 366994450 (PRIDE OF AMERICA, AIS type
69, passenger), is unlike every other repeatedly-observed passenger
vessel in the region. Every other persistent (>300-day) passenger vessel
in the box stays inside a single island's waters (1–6 distinct
0.5°-regions — day-tour and dinner-cruise boats); every large cruise ship
that ranges widely (up to 25 regions) does so on only 5–68 days a year —
an occasional port call, not a resident. PRIDE OF AMERICA combines both:
present 697 of 730 feed-days, ranging across 24 distinct regions, with
~143.4 million metres of summed inter-fix distance — more than double the
next-closest persistent vessel (SAFARI EXPLORER, 12 regions, ~28M metres,
and present on only half as many days, 366). Most strikingly, the
day-to-day autocorrelation of its daily-distance time series peaks
sharply at lag 7 (Pearson r=0.884), lag 14 (r=0.881), and lag 21
(r=0.871) — every other lag from 1 to 20 shows weak-to-moderate *negative*
correlation. This is the signature of an unbroken weekly cycle sustained
across essentially the entire two-year window. Manually inspecting the
first five weeks shows the mechanism: every Monday it is stationary at
(20.90N,156.47W) — Maui; every Friday at (21.95N,159.36W) — Kauai; the
intervening days are transit and other-island time. Broadcast-level
ground truth for one such Friday (2024‑01‑05) confirms 237 raw position
reports, all status=5 (moored), sog=0.0, at a fixed point matching that
Kauai location, with the vessel_name field reading "PRIDE OF AMERICA"
directly off the raw broadcast.

**Why it's interesting.** A single ship running an unbroken weekly loop
around an entire island state for two years straight, verified down to
the raw radio message, is the kind of concrete, checkable oddity that
makes a knowledgeable reader want to know why — and the "why" (a US-flag
requirement that makes continuous inter-island cruising by a foreign-built
or foreign-flagged ship legally impractical) is well known in the cruise
industry, though it is explicitly *not* something this dataset can prove;
see below.

**Full evidence chain.**
- Query 6 (`#n=6`, same local Parquet as Finding 1) is the basis for the
  passenger-fleet population rollup (day-count, total distance, region
  count for every type-60–69 MMSI) and for the weekday-stop inspection.
- Local computation (no additional S3 cost): the lag-1…21 autocorrelation
  of the daily-distance series (697 present days, calendar-reindexed to
  the full 730-day span so missing days do not silently shift the lag
  alignment) and the naive week-over-week centroid match (52% of 681
  week-pairs match closely; see caveat below).
- Query 10 (`#n=10`): broadcast-level pull for MMSI 366994450 on
  2024‑01‑05 (`s3://ais-noaa/broadcasts/2024/ais-2024-01-05.parquet`),
  237 raw messages, saved to
  `query-outputs/q010_poa_jan5_broadcast.parquet`.

**Capsule IRIs.**
- Observations `f2_o1`–`f2_o5` (including the phase-shift caveat
  `f2_o5_caveat`) — IRIs in `staging/all_iris.json`.
- Claim: `https://ais-x-a2.study/claim/pride-of-america-weekly-cycle`
  (no correction needed on re-audit).
- Pattern: `https://richcanopy.org/doxabase/generated/pattern/86426d2e-853a-48ee-85c1-ba8af5797b06`

**Where interesting and defensible pull apart.** The *pattern* — unique
presence/range combination, phase-shift-robust weekly periodicity,
broadcast-verified port stop — is as defensible as anything in this
report. The *explanation* most people would reach for (a Jones Act/PVSA
cabotage requirement forcing a US-flag ship into permanent inter-island
service) is background knowledge, not something derivable from AIS data
alone: nothing in this feed records flag state, ownership, or legal
status. I have deliberately kept that explanation out of the staged
claim text and confined it to this paragraph, clearly labeled as
interpretation the data cannot confirm.

**What would have to be true for this to be wrong.** The uniqueness claim
would fail if there is a second vessel with a similarly high day-count and
region-spread that was missed by the >300-day/type-60–69 filter used to
build the comparison population (checked across the full type-60-69
roster, not just a sample, so this risk is low but not zero — a vessel
with, say, exactly 299 days would have been excluded). The periodicity
claim would fail if the daily-distance series had structural artifacts
producing a spurious lag-7 correlation (e.g. a reporting-cadence effect
tied to the calendar) — the observed correlation pattern (strong positive
at exact multiples of 7 and consistently negative in between) is not the
shape a reporting artifact would typically produce, and it is corroborated
by the independent weekday-stop inspection and the broadcast spot check.

---

## Finding 3 — A recurring, US-dominated sailing-fleet arrival pulse each July

**The finding.** Both years of the study show a sharp surge of newly
arriving AIS type-36 (sailing) vessels in late June/July — the two
largest single-week new-arrival counts anywhere in the two-year window:
week of 2024‑07‑22 (24 new MMSIs) and 2024‑07‑29 (18 new); week of
2025‑07‑07 (17 new) and 2025‑07‑14 (15 new). Within the 2024 window alone
(2024‑07‑15…08‑05, 47 vessels), arrivals cluster even more tightly:
2024‑07‑27 through 07‑29 alone account for 30 of the 47 (64%). The
combined two-year pulse population (91 MMSIs: 47 in 2024, 44 in the
analogous 2025 window) is 81.3% US-registered (74/91, MID blocks
338/366/367/368/369) — *higher* than the 69.7% US share of the year-round
type-36 baseline (152/218), ruling out a foreign-fleet explanation.
Nationwide (not Hawaii-box-restricted) AIS index history for 22 sampled
vessels across both years traces a consistent three-part signature: real
AIS reception at a specific US Pacific-coast location — Los Angeles/San
Diego or San Francisco Bay in 2024; those two plus Puget Sound in 2025 —
through the departure month; then 3–9 days with *zero* fixes anywhere in
the nationwide feed (consistent with sailing beyond coastal-receiver
range); then reappearance approaching Hawaii from the east/east-northeast
in the final 1–3 days before entering the study box. All 22 sampled
vessels fit this pattern; none show weeks of prior nationwide presence
that would suggest a quiet local boat simply switching its transponder
back on.

**Why it's interesting.** This is the data showing its own reach: a
seasonal ocean crossing, invisible while it happens (the vessels are
literally outside the feed's coverage for most of the passage), bookended
by two real, geographically specific, and dramatically different
departure regions converging on the same small patch of ocean in the same
week, in two different years. It has the shape of an organized event
(a race or rally) without this dataset being able to name one.

**Full evidence chain.**
- Query 6 (`#n=6`) is the basis for the weekly/daily arrival histograms
  and the MID composition test (all local, no additional S3 cost beyond
  the original extraction).
- Query 9 (`#n=9`): nationwide index history for 12 sampled 2024-pulse
  MMSIs, `s3://ais-noaa/index/2024/ais-*.parquet` filtered by MMSI and
  date, saved to `query-outputs/q009_pulse_sample_nationwide.parquet`.
- Query 11 (`#n=11`): the same for 10 sampled 2025-pulse MMSIs against
  `s3://ais-noaa/index/2025/ais-*.parquet`, saved to
  `query-outputs/q011_pulse2025_sample_nationwide.parquet`.
- Consultation 5 (`consultations.jsonl#n=5`) confirmed the one missing
  feed-day (2024‑08‑26) is a global outage, not vessel silence — relevant
  context for the "open-ocean gap" read (the gap is real vessel behaviour,
  not a second data hole, since it doesn't align with the missing day).

**Capsule IRIs.**
- Observations `f3_o1`–`f3_o6` and the self-audit correction `f3_o7` —
  IRIs in `staging/all_iris.json`.
- Claim (original): `https://ais-x-a2.study/claim/july-sailing-arrival-pulse`
- Claim (corrected, current): `https://ais-x-a2.study/claim/july-sailing-arrival-pulse-v2`
- Reconsideration (`refines`):
  `https://richcanopy.org/doxabase/generated/claim-reconsideration/e10b7113-65ea-40b7-9179-68d235fc19e4`
- Pattern: `https://richcanopy.org/doxabase/generated/pattern/7ceb8d63-b418-4489-8eda-6d3a9e0ce6c9`

**Self-audit note.** The first version of this claim stated the MID
composition as "~89% pulse / ~85% baseline, closely matching" and the
day-concentration figure as "2024‑07‑27..29 contributing roughly a third
of the 91-vessel 2024 pulse population" — both read by eye off printed
tables rather than computed exactly. A final verification pass found: the
true MID shares are 81.3%/69.7% (the pulse is *more* domestic than
baseline, not merely similar — if anything this strengthens the
"not a foreign fleet" reading), and the 91 figure is the *combined
two-year* pulse population, not the 2024-only count (47); the corrected
day-concentration figure is 30 of 47 (64%). The original claim was
reconsidered with relation `refines`; its `observationStatus` is now
`rc:Superseded`.

**Where interesting and defensible pull apart, and what would have to be
true for this to be wrong.** The descriptive pattern — timing, count,
composition, and the nationwide departure/gap/arrival trace — is
independently reproducible and is what the staged claim asserts. The more
interesting causal reading (an organized ocean race or rally) is
explicitly *not* part of the claim, because this dataset has no event
calendar, no vessel-registration data, and no way to distinguish
"registered race fleet" from "many individuals independently choosing the
same seasonal weather window" — both would produce exactly this signature.
The finding would be wrong if the 22-vessel sample were unrepresentative
of the full 91/pulse-population's departure geography (it is a sample,
not a census — see Refusals in JOURNAL.md for what a full census would
take) or if NOAA coastal-receiver coverage itself has a seasonal gap that
coincidentally produces an arrival-look artifact (checked against the one
confirmed feed-wide outage day, which does not fall in the pulse window,
but a systematic seasonal coverage difference was not separately ruled
out).
