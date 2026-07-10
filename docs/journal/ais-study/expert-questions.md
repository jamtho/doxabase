# Expert Questions — Session 1

Context for all three: the data is a 2024–2025 daily-parquet AIS feed around the USA
(NOAA-style; broadcasts + per-MMSI-per-day index). Questions are ordered by how much
method work they unblock.

## Q1 — Is static identity really frozen per year upstream, and is there a source that preserves within-year changes?

We found that vessel identity (name, IMO, call sign, type, dimensions) is constant per
MMSI within each calendar year: 2,736 of 2,738 day-level name transitions land exactly on
the 2024→2025 file boundary, many as pure spelling re-canonicalizations (e.g. VERMILLION
BAY→VERMILION BAY, NOAA SHIP PISCES→PISCES); the sole exception is a US Navy patrol boat
(MMSI 369914086). Is this a known property of how these annual products are built (one
canonical static record per MMSI per year merged onto every day's positions)? If so, what
upstream source would you use to recover the true within-year timing of renames,
re-registrations, and MMSI handovers — raw NMEA archives, monthly static snapshots,
USCG/FCC registries? Every identity method we built is currently capped at year
granularity because of this.

## Q2 — What is the effective coverage envelope of this receiver network, especially offshore?

Silence in this feed usually means "out of receiver range", not "transponder off" (e.g.
training ship GOLDEN BEAR is cleanly received at Guam, goes silent for 16 days
mid-Pacific, reappears at the Strait of Juan de Fuca). To turn our silence-gap
segmentation into real anomaly detection we need a coverage model: is this
terrestrial-only (no satellite AIS mixed in)? What is a realistic offshore detection
range for Class A vs Class B (we see Class B duty apparently worse)? Is there a
published/queryable receiver-site list or coverage mask for the network behind
MarineCadastre-style products, and does coverage change materially over 2024–2025
(we found one whole missing day, 2024-08-26, but suspect softer regional outages too)?

## Q3 — How should we triage shared-MMSI hits: which are legitimate infrastructure beacons vs clones or misprogrammed units?

Our multi-emitter detector flags 318 MMSIs where two-plus transmitters demonstrably share
one identity. The population clearly mixes very different things: a fixed oil-platform
beacon broadcasting 'WD143 SHELL RIG' with 100 m × 100 m "dimensions" on MMSI 367373000
(colliding with unrelated Florida vessels), round-number defaults like 360000000 and
338000000 ('DREDGE PIPELINE' — apparently dredge-pipe markers nationwide), and ordinary
duplicated Class B units. Operationally: are platform/AtoN-style transmitters allowed or
known to operate with ordinary ship-format MMSIs (rather than 99xxxxxxx AtoN format)?
Which registry (FCC licence data, USCG MISLE, ITU MARS) is the practical cross-reference
to classify a flagged MMSI as licensed-fixed-infrastructure vs vessel-clone vs
factory-default, and how do practitioners usually tell "same MMSI programmed into two
sister vessels" from deliberate identity theft?
