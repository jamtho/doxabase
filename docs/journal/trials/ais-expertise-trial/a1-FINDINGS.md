# FINDINGS — AIS-X-A1 (Hawaiian Islands, 2024-01-01..2025-12-31)

Region: latitude 18.0-23.5N, longitude -161.5..-154.0 (WGS84), defined as
bounding-box **overlap** with each vessel-day's index bounding box (see
q2 / JOURNAL.md "box definition"). Day denominator throughout: **730**
observed days, not 731 -- `s3://ais-noaa/index/*/*.parquet` has no file for
2024-08-26 (confirmed directly, q1), matching the program's recorded
caveat.

All query numbers below (`qN`) refer to `query-ledger.jsonl` line `n` and
the matching `outputs/qN.txt`. Capsule IRIs use the base
`https://richcanopy.org/doxabase/generated/` unless noted.

---

## Finding 1 -- Pride of America's near-perfect weekly Hawaii circuit, broken exactly once, in the shape of a scheduled drydock

**The finding.** MMSI 366994450 -- self-reported name PRIDE OF AMERICA, IMO
9209221, length 280.0m, identity stable across both years (q19) -- operates
a fixed, repeating weekly multi-island circuit for essentially the entire
study window. It is present in the Hawaii box on 697 of 730 days and, more
tellingly, its position on a distinctive Nawiliwili/Kauai-area anchorage
(21.90-22.00N, -159.40..-159.30W) recurs on 97 distinct dates -- 95 of them
(97.9%) landing on the *same* day of the week (q9). Its one substantial
absence from the box across the whole two years, 2025-05-09 through
2025-06-03 (~3.5 weeks), is not a silent gap: the vessel's position sits
motionless (status=moored, sub-0.001-degree lat/lon spread) at a single
point near 45.567N/-122.728W -- the lower Columbia River, Portland OR/
Vancouver WA area -- for three weeks, then moves southwest with steadily
increasing speed on 2025-06-01..06-03, heading directly back toward
Hawaii, before two final gap days that plausibly mark the open-ocean leg
of that return transit (q7). No other absence anywhere in the record has
this shape or length.

**Why it's interesting.** It is a rare case where pure position data lets
you read an operator's published schedule and a one-off maintenance event
straight off the map, with no external schedule or corporate record: the
weekday-locked port call and the singular, transit-bookended absence are
both independently legible in two years of raw AIS pings for one hull.

**Full evidence chain.**
- q1 -- index glob spans 730 distinct dates (day denominator).
- q5 -- base pull: full daily index history (centroid, status_codes,
  message_count, sog_max) for MMSI 366994450, 2024-01-01..2025-12-31.
  `outputs/q5.txt`, 723 rows returned (of 730 possible).
- q6 -- calendar diff (730-day calendar minus 2024-08-26) against q5's
  dates -> only 7 missing dates: 2024-04-17 (isolated) plus 2025-05-05..
  05-08 and 2025-06-04..06-05 (edges of the q7 gap). `outputs/q6.txt`.
- q7 -- re-ran q5 *without* the box filter, restricted to days whose
  bounding box does not overlap the Hawaii box -> 26 days. These resolve
  the q6 gap: 2025-05-09..05-31 static at ~45.567N/-122.728W (status=[5]
  every day); 2025-06-01..06-03 moving southwest and accelerating.
  `outputs/q7.txt`.
- q8 -- full 2-year index history filtered to the tight Nawiliwili-cluster
  window (21.90-22.00N, -159.40..-159.30W) -> 97 dates. `outputs/q8.txt`.
- q9 -- day-of-week histogram of the 97 q8 dates -> 95 on `dayofweek()=5`
  (Friday, confirmed since 2024-01-01 is a known Monday and 2024-01-05,
  the first cluster date, is dow=5), 1 on dow=4, 1 on dow=3.
  `outputs/q9.txt`.
- q19 -- identity-stability check: name/IMO/length identical across 2024
  and 2025 for this MMSI -- rules out MMSI reuse/cloning as a confound.
  `outputs/q19.txt`. (Cross-check, not a capsule data source: 280m matches
  the real Pride of America's published length overall of ~280.7m/921ft --
  offered as a plausibility sanity-check on the self-reported dimension
  field, not as evidence drawn from this capsule.)
- **Verification performed:** re-derived the 97/95 figures directly from
  q8's output before writing them here; cross-checked q6's 7 missing dates
  against q7's 26 out-of-box dates to confirm they are the same underlying
  absence, not two unrelated phenomena (7 + 26 does not overlap-double
  count: q6 finds *entirely missing* days, q7 finds days present but
  outside the box -- together they fully explain all 33 days where the
  vessel is not "in the box present").
- **Capsule record:** pattern
  `pattern/49ce3ee4-834b-4d38-913b-63a38def038e` (evidence
  `evidence/962c9d80-fffa-4d71-a3a2-a6c8153b2b41`) synthesizes observations
  `observation/32698a49-...` (q5), `.../ff6bfd1f-...` (q6),
  `.../f7f5fa2c-...` (q7), `.../d49ec15e-...` (q8), `.../0fedb53f-...` (q9),
  `.../78d2e943-...` (q19). Claim
  `claim/e9cbdd06-4f07-40fc-b2bd-481f9b7717bf` (on observation
  `observation/bfc20110-5e14-458f-b7b7-278cde024340`, evidence
  `evidence/6a4222c7-9679-48f0-916e-22740ba1a626`), `claim_kind
  rc:InterpretationClaim`, `confidence rc:HighConfidence`, target
  `https://ais-x-a1.study/entity/vessel/mmsi-366994450`.

**What would have to be true for this to be wrong.**
- The periodicity claim (95/97 same-weekday) would be undermined if
  `dayofweek()` or `base_date_time`->date parsing were unreliable across
  the 2024/2025 boundary -- the program's own caveat registry flags a
  string-format shift in `base_date_time`, but I used `date` (already
  parsed) throughout q5-q9, not string operations on `base_date_time`, so
  this risk is small but not zero for the two off-pattern dates.
- The single-MMSI identity would have to be compromised -- e.g. two
  different physical hulls sharing 366994450 -- for the "one vessel, one
  circuit" framing to fail; q19's stable name/IMO/length across both years
  argues against this, but per the program's registered caveat that
  identity fields are self-reported and unverified, I cannot rule out a
  deliberate MMSI clone with an identical spoofed identity.
- The **drydock interpretation** specifically is inference beyond the raw
  position data, not a direct fact this feed can confirm -- I have no
  shipyard record, AIS destination field, or Message-5 ETA/purpose text to
  corroborate it. What the data actually shows without interpretation:
  one ~3.5-week period of near-total stillness at a single Pacific
  Northwest coordinate, directly bracketed by transit legs to and from
  the vessel's normal Hawaii operating pattern, unique in the 2-year
  record. "Scheduled drydock" is the most plausible reading of that shape
  (a fault or emergency repair could look similar but would be less
  likely to produce three full weeks of *complete* stillness with no
  intervening movement); a reader should treat the periodicity claim as
  data-certain and the drydock *label* as a labeled, flagged inference.

---

## Finding 2 -- Hawaii's commercial fishing fleet is structurally single-port: overwhelmingly Honolulu, almost absent from the inter-island harbor network

**The finding.** Of 196 distinct AIS type-30 ("fishing") MMSI recorded in
the Hawaii box across the full 2 years (35,504 vessel-days, full-population
count, q3), 76.8% of those vessel-days -- 27,273 of 35,504 -- have their
daily centroid inside one narrow window over Honolulu Harbor
(21.20-21.40N, -157.80..-157.95W) (q13, full 2-year population, not
sampled). A 12-day cross-season/cross-year broadcast sample independently
confirms that window's busiest cell is 97%+ stationary (sog<0.5kt, 142
distinct MMSI) -- a home-port signature, not an active fishing ground
(q12). Meanwhile the three next-busiest inter-island harbor windows --
near Kahului/Maui, Nawiliwili/Kauai, and the Kona area, each identified
from Pride of America's own confirmed port calls (Finding 1) and each
carrying thousands of *non*-fishing vessel fixes in the same 12-day sample
(26,319 / 4,823 / 6,326 respectively, q11) -- combine for only **12**
fishing-vessel-days across the *entire* 2-year record, contributed by just
6 small (10-50m) vessels distinct from the main fleet, none of them
repeating a regular pattern (q14). The fishing fleet is the single busiest
vessel type in the whole region by both day-count and distinct-MMSI count
(q3) -- it plainly operates across the full box -- but it comes home to
essentially one harbor, unlike the passenger, cargo, and tug traffic that
visibly uses all four main islands.

**Why it's interesting.** It is a clean, quantified population-structure
fact about a real industry (Hawaii's fishing fleet is widely known to be
Honolulu-centered in general terms) derived entirely from raw position
data, with the counter-example population (other harbors, other vessel
types) built from the same feed as an internal control -- no external
economic or regulatory record was needed to find or state it.

**Full evidence chain.**
- q3 -- vessel-type distribution, full 2-year box-overlap index: type 30
  leads on day-rows (35,504) and distinct MMSI (196). `outputs/q3.txt`.
- q10 -- 0.1x0.1-degree spatial density grid of type-30 broadcast fixes,
  12 sample days (15th of alternating months, both years, all 4 seasons):
  716 cells, 227,024 fixes. `outputs/q10.txt`.
- q11 -- identical grid for *non*-fishing fixes, same 12 days -- the
  control layer that locates harbor cells independently of the fishing
  data: 1,490 cells, 663,973 fixes. `outputs/q11.txt`.
- q12 -- sog/status breakdown of type-30 fixes inside the single busiest
  cell identified by comparing q10 against q11 locally (21.25-21.35N,
  -157.85..-157.95W): 173,669 of ~178k fixes have sog<0.5kt (sentinel
  sog=102.3 and NULL excluded), 142 distinct MMSI. `outputs/q12.txt`.
- q13 -- **full 2-year, not sampled**: count of type-30 vessel-days inside
  the Honolulu window vs. the three neighbor-harbor windows ->
  27,273 / 35,504 Honolulu; 8+2+2=12 combined elsewhere. `outputs/q13.txt`.
- q14 -- row-level detail on the 12 q13 exception-days: 6 distinct small
  (10-50m) MMSI, no repeating pattern. `outputs/q14.txt`.
- q21 -- identity-churn robustness check: of the 196 type-30 MMSI, 164 seen
  in both years, only 6 (3.7%) show a different normalized name year over
  year -- small enough not to threaten treating the 196 as one coherent
  population despite the program's registered year-boundary identity
  caveat. `outputs/q21.txt`.
- **Verification performed:** deliberately built the "other traffic"
  baseline (q11) from the *same* 12 days as the fishing grid (q10) so the
  comparison is not confounded by seasonal effects; then independently
  confirmed the headline 76.8% figure against the **full** 2-year
  population (q13) rather than resting the core claim on the 12-day
  sample -- the sample is used only for the sog/status texture (q12) and
  the "how much non-fishing traffic is really there" baseline (q11), both
  explicitly labeled as sample-derived in the pattern text.
- **Capsule record:** pattern
  `pattern/751a45a4-4a9f-4465-8e54-8e5fc6a3b36c` synthesizing observations
  for q3 (`.../c23538c7-...`), q10 (`.../e7b5b005-...`), q11
  (`.../e6f5b60a-...`), q12 (`.../83fa64ef-...`), q13 (`.../ece301b6-...`),
  q14 (`.../04857a4d-...`), q21 (`.../04edb0fc-...`). Claim
  `claim/0b0860b3-0835-4530-95a3-4ad00db86584` (on observation
  `observation/05b76b0d-6b97-4a93-be93-808aa82898ba`, evidence
  `evidence/2776db7b-2aa7-4bc8-ae9b-4d9a6e185269`), `claim_kind
  rc:InterpretationClaim`, `confidence rc:HighConfidence`, target
  `https://ais-x-a1.study/entity/fleet/hawaii-fishing-vessel-type30-2024-2025`.

**What would have to be true for this to be wrong.**
- AIS type 30 ("fishing") is self-reported and, per the AIS spec, covers
  both commercial and some recreational fishing vessels -- if a large
  share of the 196 MMSI were actually small recreational boats rather than
  the commercial fleet, "Hawaii's commercial fishing fleet" would overstate
  what's shown. I did not independently separate commercial from
  recreational within type 30; the 10-50m exception vessels in q14 (small
  craft) suggest the population is not homogeneous, though the 142-MMSI,
  97%-stationary Honolulu-hub cell (large N, tight behavior) is much more
  consistent with a commercial home-port pattern than a recreational one.
- The neighbor-harbor window coordinates were located via Pride of
  America's own confirmed port calls (Finding 1) and general geographic
  knowledge, not an independently verified gazetteer (no web/documentation
  access per the brief) -- if any of those three windows is actually
  centered on the wrong real-world harbor, the *place names* in this
  write-up would be wrong, but the core structural claim (substantial
  non-fishing traffic in specific windows, near-zero fishing traffic in
  the same windows) would be unaffected, since it does not depend on
  correctly naming the location.
- If the 12 sample days happened to coincide with an unusual fishing
  closure or event pattern, the q11/q12 texture could be non-representative
  -- mitigated by spreading the 12 days across both years and all 4
  seasons, and by resting the headline percentage on the full 2-year
  population (q13) rather than the sample.

---

## Finding 3 -- AIS message volume in the Hawaii box is dominated by a small, persistently-present "resident/utility" core; the much larger transient population barely registers

**The finding.** Ranking all 2,046 distinct MMSI recorded in the Hawaii
box across 2024-2025 by total message_count (54,422,109 messages,
box-overlap, full 2-year index -- verified free of (mmsi,date) duplication
feed-wide, q20), the distribution is steeply Zipf/Lorenz-concentrated: the
top 100 vessels (4.9% of the population) account for **52.4%** of all
messages; the top 300 (14.7%) account for **85.1%**; the bottom ~1,500
vessels (73% of the population) contribute under 1.1% combined (q17). This
is not an arbitrary artifact of the ranking -- breaking the two tails down
by vessel_type (q18) shows the top-100 group averages 325-620 *days
present* per vessel and is dominated by tug (52), fishing (30), sailing
(36), other/utility (90), towing (31/32), passenger (60) and military (35)
types -- vessel types whose operating model is inherently local and
near-daily. The <=500-total-message long tail averages only 1.0-5.5 days
present per vessel and is dominated by unknown-type contacts (229 vessels
averaging 1.3 days and 13 messages each), pleasure craft, cargo, and
tankers -- consistent with brief transits through the region rather than
local operation.

**Why it's interesting.** It reframes what "the Hawaii AIS feed" actually
*is*: not primarily a record of the ~2,000 distinct ships that pass
through, but overwhelmingly the operational log of a few hundred resident
service craft (tugs, pilots, ferries, the fishing fleet, one cruise ship)
that happen to also share the channel with a much larger, nearly-silent
population of passers-through.

**Full evidence chain.**
- q16 -- per-MMSI total message_count and day-count, full 2-year
  box-overlap population (2,046 MMSI), ranked descending.
  `outputs/q16.txt`.
- q17 -- cumulative message-share by rank (window function over q16's
  population): rnk100->52.4%, rnk300->85.1%, rnk1500->99.9% cumulative.
  `outputs/q17.txt`.
- q18 -- vessel_type breakdown of the top-100-by-messages group vs. the
  <=500-total-message long tail, with average days-present and average
  messages per vessel_type x tail. `outputs/q18.txt`.
- q20 -- data-quality check: (mmsi,date) is a clean unique key across the
  *entire* feed (14,638,201 rows = 14,638,201 distinct keys) -- rules out
  duplicate-row inflation of the message totals this finding depends on.
  `outputs/q20.txt`.
- **Verification performed:** ran q20 specifically because a Lorenz-style
  concentration statistic is exactly the kind of number that looks "too
  clean" if there is a hidden duplication bug in the source join; confirmed
  the index's (mmsi,date) grain is genuinely 1:1 feed-wide before trusting
  q17's percentages. Also deliberately checked *both* message-count and
  day-count in q18 rather than message-count alone, since a single
  hyperactive transponder could in principle inflate message_count without
  reflecting real "residency" -- the day-count column moving in the same
  direction as message_count for both tails is the check that the
  concentration reflects genuine presence duration, not just a chatty
  transponder.
- **Capsule record:** pattern
  `pattern/bca0575c-a24b-4bc7-aa4c-541689dc3255` synthesizing observations
  for q16 (`.../10be842b-...`), q17 (`.../3fc47fdc-...`), q18
  (`.../c470cdcb-...`), q20 (`.../c1591e85-...`). Claim
  `claim/ff4b17e6-4b9b-44ad-80d4-2817d97bb487` (on observation
  `observation/2d2dce53-066f-4e25-81b2-eff65a1a2585`, evidence
  `evidence/57035299-0523-42c0-b525-7addc62d4561`), `claim_kind
  rc:InterpretationClaim`, `confidence rc:HighConfidence`, target
  `https://ais-x-a1.study/entity/population/hawaii-box-vessel-population-2024-2025`.

**What would have to be true for this to be wrong.**
- AIS Class A transponders report far more frequently than Class B by
  design, independent of "residency" -- if the top-100 group happens to be
  disproportionately Class A-equipped for reasons unrelated to being
  locally resident (e.g. regulatory requirement by vessel size, not by
  role), message-count concentration could partly reflect equipment class
  rather than behavior. I mitigated this by cross-checking day-count
  (equipment-class-independent) alongside message-count in q18 and finding
  both move together, but I did not directly control for transceiver class
  (the `transceiver` A/B column) in this analysis -- a natural next check
  for a future tranche.
- Self-reported MMSI can be duplicated or spoofed (program caveat); if a
  meaningful share of the 2,046-vessel denominator is actually the same
  physical vessel double-counted under two MMSIs, the *population* size
  (and thus the "4.9% of vessels" framing) would be off, though the
  underlying concentration of message volume among a small set of IDs
  would likely persist regardless.
- The concentration statistic itself would be undermined by exactly the
  kind of duplicate-row bug q20 was run to rule out; q20 found none, but a
  more subtle duplication (e.g. overlapping but non-identical rows) is not
  fully excluded by a single key-uniqueness check.

---

## Notes on scope and rigor common to all three

Every number above traces to a specific ledgered query (`query-ledger.jsonl`,
lines 1-21) and a retained output file under `outputs/`. All 21 queries
this session succeeded (0 client-side errors); ~21 of the ~150-query budget
was used. Two candidate storylines were explored and explicitly declined --
see JOURNAL.md "Refusals" -- rather than forced into a weak third or fourth
finding.
