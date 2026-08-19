# FINDINGS — AIS-X-A0 (Hawaiian Islands, 2024-01-01 .. 2025-12-31)

Three findings about the maritime world visible in this AIS feed within the
box lat 18.0-23.5N, lon -161.5..-154.0W. Each section gives the finding, why
it's interesting, the full evidence chain (ledger query numbers, every
intermediate, every verification step, capsule IRIs), and what would have to
be true for the finding to be wrong.

Query numbers (`q00NN`) refer to rows in `query-ledger.jsonl`. Output files
referenced as `work/query_outputs/00NN_*.txt` are the retained, re-runnable
evidence for each query; the SQL for multi-line queries also lives under
`queries/*.sql`.

---

## Finding 1 — A six-week, internationally diverse naval surge appears in the Hawaii AIS feed in summer 2024, and nowhere in 2025

**The finding.** From roughly 2024-06-25 through 2024-08-03, the number of
distinct vessels broadcasting AIS `vessel_type=35` ("military ops") inside
the Hawaii study box jumps from a baseline of 5-8 per day to a plateau of
16-21 per day, peaking at 21 distinct vessels on 2024-07-12. Named among
these vessels, by their self-reported AIS `vessel_name`/`call_sign` fields,
are warships identifiable as German (GERMAN WARSHIP F222 / DRAD), French
(FRENCH WARSHIP), Canadian (CDN WARSHIP 432, and the support ship ASTERIX),
Mexican (ARM USUMACINTA A412), Indian (INDIAN WARSHIP, callsign F 47),
Japanese (HAGURO, callsign JSLL), South Korean (ROK GOV VESSEL), Australian
(AUSTRALIAN WARSHIP), Bruneian (KDB DARUSSALAM), Indonesian (IDN WARSHIP
331), Malaysian (RMN WARSHIP 30), and Peruvian (BAP PISCO) — alongside a
standing baseline of US-flagged range and support craft. Of the 71 distinct
`vessel_type=35` MMSIs seen in the box across the full two years, roughly
13-15 have their *entire* observed footprint in this dataset confined to
that six-week window; the remainder are a locally-based standing population
(Coast Guard cutters, Pacific Missile Range Facility range/support craft)
present most of the year, with only a modest bump during the window. The
identical calendar window one year later (2025-05-15..08-15) shows no such
ramp — daily counts stay flat at 3-11 — and the vessel-name sample for the
equivalent 2025 dates is exclusively US-flagged, with zero foreign warship
names.

**Why it's interesting.** This is a live, dated, internationally-specific
geopolitical/military event legible from nothing but civilian AIS position
reports — the data effectively lets you read off the guest list of a
multinational exercise by nationality and hull, purely from self-reported
ship names and the rhythm of a temporary population against a stable
baseline. It is a strong, retellable, "the data noticed something real in
the world" story, and it is falsifiable in several independent ways at
once (count, timing, identity, year-over-year contrast).

**Full evidence chain.**

1. `q0007` — vessel-type census over the full 2-yr bbox-filtered index
   (`work/query_outputs/0007_vessel_type_dist.txt`) surfaces `vessel_type=35`
   at 71 distinct MMSI / 5007 mmsi-day rows — notable enough to follow up.
2. `q0008` — monthly distinct-MMSI count for `vtype=35` in bbox
   (`work/query_outputs/0008_mil_monthly.txt`): Jun/Jul/Aug 2024 = 28/33/31,
   every other month of 2024 and all of 2025 in the 10-20 range (max 20).
3. `q0009` — daily granularity, 2024-05-15..08-15
   (`work/query_outputs/0009_mil_daily_2024.txt`): ramp begins 2024-06-25,
   plateau 16-21/day through late July, back to baseline by 2024-08-09.
4. `q0010` — `DISTINCT mmsi, vessel_names, call_signs` for `vtype=35` in the
   2024-07-08..07-23 peak window
   (`work/query_outputs/0010_mil_names_peak.txt`): the multinational roster
   quoted above.
5. `q0011` + `q0012` — identical daily-count and name-sample queries for the
   2025 equivalent window
   (`work/query_outputs/0011_mil_daily_2025.txt`,
   `work/query_outputs/0012_mil_names_2025.txt`): flat counts, all-US roster
   — the negative control.
6. `q0035` (superseded by the next step, kept for the record) and `q0036` —
   per-MMSI `total_days` vs `window_days` breakdown for all 71 MMSIs
   (`work/query_outputs/0035_mil_window_classify.txt`,
   `work/query_outputs/0036_mil_footprint.txt`): the two-tier structure
   (foreign transients whose whole footprint sits in the window; a US-flagged
   standing baseline present most of the year).
7. Verification: `q0032` (empty — picked a date the vessel wasn't present),
   `q0033` (found the vessel's actual index dates), `q0034` (point-level
   broadcast pull for MMSI 211920000 on 2024-07-10:
   `work/query_outputs/0034_rimpac_verify_broadcast2.txt`) — a real,
   independently-moving track (1-minute-cadence fixes, smooth deceleration
   20.0kn -> 10.2kn), ruling out a stale/static-record artifact.

**Capsule IRIs.**
Claim: `https://richcanopy.org/doxabase/generated/claim/ddebb089-4b7c-4727-b2b7-353d35828a3e`
(wrapper observation `https://richcanopy.org/doxabase/generated/observation/8ec253aa-849c-4566-bdb6-683057e21eeb`,
evidence `https://richcanopy.org/doxabase/generated/evidence/507ad864-1642-4585-b7e0-8d5ced3514ab`).
Supporting narrative observations (in investigation order): vessel-type
census `.../observation/89e11048-9700-41f5-9cc3-b17abf6a65b0`; monthly
profile `.../observation/b76b6034-bfdc-4797-a931-02d02791688e`; daily
profile `.../observation/07993f40-d1b5-493e-b4a4-e4828144764a`; name sample
`.../observation/056aab7f-1714-464d-964a-c7d761d1af32`; 2025 comparison
`.../observation/e32cd86e-3012-4f53-9dc5-c2b917d42f80`; footprint
classification `.../observation/378c7e01-3c8c-48d4-9c1b-101337594891`; point
verification `.../observation/9086e338-ee83-41b5-b6cc-2ec799f4503c`.

**What would have to be true for this to be wrong.** (a) `vessel_type=35`
would have to be a mis-set or default code that a non-military fleet happens
to use seasonally — ruled out as a general explanation by the specific,
plausible, internationally varied warship names, which a mislabeling
artifact would not produce. (b) The 2024-only pattern could be a one-off
coincidence unrelated to any recurring exercise — the finding as evidenced
does NOT depend on the RIMPAC identification: the surge, its multinational
composition, and its absence in 2025 are all directly supported by the data
regardless of what caused it. The RIMPAC label itself is an interpretation
drawn from background knowledge not verified against any source in this
session, and is flagged as such in the claim text; if that identification
is wrong (wrong exercise, wrong cause), the underlying AIS pattern still
stands. (c) If NOAA's feed happened to route non-Hawaii-area military traffic
through this bbox by a routing/relay artifact unique to summer 2024, that
would undermine the finding — nothing in the investigation ruled this out
beyond the point-level track looking like genuine, geographically
plausible motion within the box.

---

## Finding 2 — The Hawaii-based longline-length fishing fleet shows an offshore behavioural discontinuity that raw position density hides

**The finding.** Among the 137 `vessel_type=30` (fishing) MMSIs in the
bbox whose maximum reported length is 15-30m (the size class matching the
Hawaii-based commercial longline fleet, distinguished from a mixed
near-shore/small-boat and large-foreign-vessel population sharing the same
AIS type code), the fraction of broadcasts at low speed (sog<3kn, a proxy
for gear-handling rather than transit) falls to a minimum of **0.5%** in the
50-75nm band from the nearest main island (median speed 6.9kn — steady
transit), after being 92.2% within 25nm (harbor mooring, a different
phenomenon) and 1.7% at 25-50nm. Beyond 75nm the slow-speed fraction climbs
steadily: 3.6% (75-100nm), 4.7% (100-125nm), 14.8% (125-150nm) — roughly a
**30x** rise from the 50-75nm minimum. A control population (cargo vessels,
type 70-79, no length restriction) run through the identical methodology
shows the same minimum location (50-75nm, 3.3%) but only a ~2x rise beyond
it (max 7.1%) — far short of the fishing cohort's ~30x rise. Critically,
this pattern is invisible in raw position-density banding (which two
successive attempts, both dead ends, show is dominated by harbor dwell and
undifferentiated transit-vs-work presence); it only appears once the
population is isolated by vessel size and the lens is switched from
"where are they" to "how fast are they going."

**Why it's interesting.** It is a case where the *first two* reasonable
analyses (raw density banding, then density banding on an underway-only
filter) both come back negative, and the real signal only appears after
diagnosing two separate confounds (a mixed vessel population, and a
transit/dwell-biased metric) and picking a better one (speed-based, cohort-
isolated). The resulting pattern is plausibly the visible footprint of the
federal Hawaii longline exclusion zone — a real regulatory buffer — read
directly out of fleet behaviour, not fleet position, which is a more
interesting and more defensible kind of evidence than a simple map of where
boats are.

**Full evidence chain.**

1. `q0007` — `vessel_type=30` has by far the most mmsi-day rows of any type
   in the bbox (35504 rows / 196 vessels): flagged as worth a closer look.
2. `q0016` (`work/query_outputs/0016_fish_dist_bands.txt`) and `q0017`
   (`work/query_outputs/0017_fish_dist_bands_fine.txt`, `queries/fish_distance_bands.sql`,
   `queries/fish_distance_bands_fine.sql`) — **dead end 1**: coarse and fine
   distance-banded raw position/vessel-hour density, no dip at 50-75nm;
   0-25nm dominated by harbor dwell even after excluding `status=0`.
3. `q0018` (`work/query_outputs/0018_fish_length_hist.txt`) — length
   histogram of `vtype=30` MMSIs is multi-modal: 137 vessels at 15-30m, 34 at
   50-85m, a handful at 110-200m. `q0019`
   (`work/query_outputs/0019_fish_longline_mmsi_list.txt`) extracts the
   137-MMSI 15-30m cohort by explicit MMSI list.
4. `q0020` (`work/query_outputs/0020_fish_longline_only_dist.txt`) —
   **dead end 2**: re-running the fine distance band on the 137-MMSI cohort
   with `status=0` as the underway filter collapses to ~1 distinct vessel
   per band, an absurd result. `q0021`
   (`work/query_outputs/0021_fish_status_diag.txt`) diagnoses this: `status`
   is NULL for ~93% of this population's broadcasts (recorded as map caveat
   `caveat_status_mostly_null`). `q0022`
   (`work/query_outputs/0022_fish_longline_only_dist_v2.txt`,
   `queries/fish_longline_only_dist_v2.sql`) fixes the filter (sog 1-12kn
   instead of `status=0`), restoring 110-132 distinct vessels per band —
   but the density profile is still a smooth monotonic decay, no dip.
5. `q0023` (`work/query_outputs/0023_fish_speed_by_band.txt`,
   `queries/fish_speed_by_band.sql`) — **the decisive query**: percent of
   broadcasts at sog<3kn and median sog, by 25nm band, for the 137-MMSI
   cohort. This produces the 92.2% / 1.7% / 0.5% / 3.6% / 4.7% / 14.8%
   sequence quoted above.
6. `q0024` (`work/query_outputs/0024_cargo_speed_by_band.txt`,
   `queries/cargo_speed_by_band.sql`) — control group (cargo, type 70-79):
   same-location minimum, much weaker rise beyond it. This is what makes the
   finding fishing-specific rather than a generic port-approach artifact.

**Capsule IRIs.**
Claim: `https://richcanopy.org/doxabase/generated/claim/52c8b43d-187b-4afb-9bb0-c095d3b10988`
(wrapper observation `https://richcanopy.org/doxabase/generated/observation/fa2651cf-7ac5-4157-affa-ed52889049c9`,
evidence `https://richcanopy.org/doxabase/generated/evidence/10a13ad1-8402-4048-ad2c-b5415b9ef8f6`).
Supporting narrative observations: dead end 1
`.../observation/56a2863f-8906-4dd7-9d01-7ced6a475007`; length-cohort
diagnosis `.../observation/b23ec368-22e2-4512-84e4-2adb349f3808`; dead end 2
+ status diagnosis `.../observation/ccac7464-c6d1-4c85-a438-ef26c7897b44`;
breakthrough `.../observation/e9042c3f-6b2b-4439-9cfa-1e6d701c2d73`; cargo
control `.../observation/a390be5f-9145-49be-bbb5-4280bba88cb9`. Map caveat:
`https://ais-x-a0.study/entity#caveat_status_mostly_null`.

**What would have to be true for this to be wrong.** This finding is
recorded at **medium confidence**, lower than the other two, because of a
genuine, acknowledged alternative explanation: pelagic longline target
species (tuna, swordfish) may simply be more abundant or economical to fish
well offshore regardless of any regulatory boundary, in which case the same
"transit near shore, work far out" pattern would appear with no exclusion
zone at all — biology and economics, not regulation, would be the real
cause, and this dataset cannot distinguish the two. Also: (a) if the
15-30m length cohort is not actually dominated by longline-gear vessels
(e.g. it is mostly trap/handline boats of a similar size), the "longline
fleet" framing would be wrong even if the behavioural pattern itself is
real; (b) if `sog<3kn` is a poor proxy for "working" for this gear type
(e.g. longline setting happens at 6-9kn, indistinguishable from transit,
and only hauling is slow), the metric could be under-detecting work close
to shore and over-attributing it far offshore for reasons unrelated to any
zone; (c) the 125-150nm band's 14.8% figure rests on a comparatively small
sample (n=1158 raw positions) and should be treated as more uncertain than
the well-populated 50-100nm bands.

---

## Finding 3 — Pride of America runs a near-mechanically-regular weekly interisland circuit, visibly interrupted once by an apparent drydock

**The finding.** MMSI 366994450 (vessel_name PRIDE OF AMERICA) is present
in the Hawaii study box on 697 of the 731 possible days across 2024-2025
(95%) — far more than any other passenger vessel, and in stark contrast to
roughly 20 foreign-flagged cruise ships (Koningsdam, Ruby Princess,
Norwegian Sun, Grand Princess, Viking Neptune, Carnival Radiance, Zaandam,
Carnival Miracle, Disney Wonder, Celebrity Edge/Solstice, Crown Princess,
Westerdam, and others) each present only 19-68 days. Of 213 index-identified
"in-port" days (daily summed track distance under 10nm), 93 fall at a
location matching Kahului, Maui, and **every single one of those 93** falls
on a Monday; 97 fall at a location matching Nawiliwili, Kauai, and 95 of
those 97 (98%) fall on a Friday. Point-level broadcast verification confirms
the vessel is genuinely moored (`status=5`, sog~0) at the exact reported
coordinates on a sampled date. Between 2025-05-11 and 2025-05-30 the
vessel's stationary-day location shifts entirely away from Hawaii to
approximately 45.6N/122.7W (the Columbia River / Portland-Vancouver,
Oregon-Washington area), then resumes the identical Monday-Kahului /
Friday-Nawiliwili pattern from 2025-06-09 onward with no phase drift.

**Why it's interesting.** It is a single vessel behaving, over two full
years, more like scheduled infrastructure than like a cruise ship — a fixed
weekly public-transit-grade timetable, legible entirely from AIS "in-port"
clustering, that is interrupted exactly once by what reads as a scheduled
absence and then resumes on the identical day-of-week phase. The contrast
against the ~20 foreign-flagged ships (each a single/occasional port call)
turns a single vessel's oddity into a structural fact about the Hawaii
cruise market: one operator runs a resident weekly circuit, everyone else
visits.

**Full evidence chain.**

1. `q0027` (`work/query_outputs/0027_passenger_persistence.txt`) —
   persistence ranking (`count(distinct date)`) for `vtype 60-69` in bbox
   surfaces the 697/731-day outlier and the contrast against the
   occasional-visitor foreign fleet.
2. `q0028` (`work/query_outputs/0028_poa_daily_track.txt`) — full 2-yr daily
   centroid pull for MMSI 366994450 shows the repeating multi-port sequence
   by inspection (e.g. 2024-01-01/08/15/22/29, all Mondays, identical
   Kahului-area centroid).
3. `q0029` (`work/query_outputs/0029_poa_periodicity.txt`) — first
   periodicity attempt (raw lag-7 self-join on daily centroid), noisy
   because transit-day centroids vary with position-along-route; superseded
   by method, kept as a recorded dead end in the methodology.
4. `q0030` (`work/query_outputs/0030_poa_inport_days.txt`) — cleaner
   approach: isolate "in-port" days (`distance_m/1852 < 10`) with
   day-of-week and rounded location. Local (no additional S3 query)
   aggregation of these 213 rows gives the 93/93 Monday-Kahului and 95/97
   Friday-Nawiliwili counts, and surfaces the 2025-05-11..05-30 Pacific-NW
   excursion with resumption from 2025-06-09.
5. `q0031` (`work/query_outputs/0031_poa_verify_broadcast.txt`) —
   point-level broadcast verification: raw pings for MMSI 366994450 on
   2024-01-01 show `status=5` (moored), sog 0.0-0.1kn, essentially fixed
   position at 20.8965N/-156.466W across 3-minute-cadence reports.

**Capsule IRIs.**
Claim: `https://richcanopy.org/doxabase/generated/claim/b5331f66-8201-4a57-9e21-d7e78e6e5bfa`
(wrapper observation `https://richcanopy.org/doxabase/generated/observation/5328ea7c-f648-4b1e-a6d2-7279748faf06`,
evidence `https://richcanopy.org/doxabase/generated/evidence/fb112d66-0106-4672-a2e8-fc9210bb159b`).
Supporting narrative observations: persistence ranking
`.../observation/a9aca685-68aa-4045-a607-b810c62fbadd`; daily track
`.../observation/4e5b5ef2-a2bf-4964-925c-36fe33eebe04`; periodicity method
`.../observation/92061b32-15e7-42a1-bfd5-89504f06026c`; drydock excursion
`.../observation/2341b630-a8f2-470b-92f2-9335171f2745`; point verification
`.../observation/52a7f893-f6d2-44bd-ba40-8f39f39d3ac7`.

**What would have to be true for this to be wrong.** (a) If MMSI 366994450
were shared/reassigned between different physical vessels at some point in
2024-2025 (AIS MMSI reuse does happen), the "single vessel" framing would be
wrong even if the schedule pattern in the data is real — nothing in this
investigation rules out MMSI reassignment beyond the name field staying
"PRIDE OF AMERICA" throughout the sampled points. (b) The 45.6N/122.7W
identification as "Pacific Northwest, consistent with drydock" is a
plausible geographic read of two coordinates plus background knowledge, not
a confirmed shipyard record — if that stationary period was actually
something else (e.g., a different kind of extended layover), the schedule-
interruption-and-resumption fact would still stand, but the "drydock"
characterization specifically would not. (c) The two Nawiliwili-day
exceptions (2 of 97 not landing on Friday) are unexplained; if a systematic
reason for those (rather than ordinary schedule perturbation) turned out to
undermine the day-of-week regularity more broadly, the "98% Friday" claim
would need revisiting — as evidenced here it is a minor, disclosed
imperfection, not grounds to doubt the overall pattern.

---

## Refused finding: a Transpacific Yacht Race signature

Investigated and declined — see `JOURNAL.md` "Refusals" section for the
full writeup, revival conditions, and evidence (`q0025`, `q0026`).
