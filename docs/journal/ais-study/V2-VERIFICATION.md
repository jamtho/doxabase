# s3://ais-noaa v2 regeneration — verification report

Date: 2026-08-19. Role: read-only verification session, independent of the
pipeline agent that performed the in-place rebuild. All queries run via
DuckDB + httpfs against the live bucket, using a private copy of the
study's `query.py` pattern kept in this directory
(`/home/codex/ais-v2-verification/query.py`) — nothing was written to
`/home/codex/ais-study/` or its capsule. Query plan was ledgered in
`QUERY-LEDGER.md` before firing, as required. ~27 substantive queries
fired against the ~40-query budget (2 schema DESCRIBEs + 2 exploratory
globs also fired, not counted against the substantive budget). No S3
credentials appear anywhere in this file or its supporting scripts.

Bucket layout confirmed: `broadcasts/<year>/ais-<date>.parquet` (raw,
one row per received message) and `index/<year>/ais-<date>.parquet`
(one row per mmsi/day, aggregated). Session TimeZone is `Etc/UTC`.

## Per-claim verdict table

| # | Claim | Verdict | Evidence |
|---|-------|---------|----------|
| 1 | `base_date_time` normalized to `'YYYY-MM-DD HH:MM:SS'` both years | **CONFIRMED** | 6 sampled days (2024-01-15, 2024-06-15, 2024-12-31, 2025-01-01, 2025-06-15, 2025-12-31), regexp `^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$` matched 100% of rows on every file (7.3M–10.0M rows/day); zero rows contained `T`. Old 2024 'T'-separator / 2025 space-separator split is gone. |
| 2 | `timestamp` is true UTC (was CET/CEST-shifted) | **CONFIRMED** | 6 sampled days incl. both DST-switch dates (2024-03-31, 2025-03-30) plus winter/summer for each year: `date_diff('second', CAST(base_date_time AS TIMESTAMP), CAST(timestamp AS TIMESTAMP))` returned the single distinct value `0` on every file, no exceptions. Old behaviour (−1h winter, −2h summer) is gone. |
| 3 | 2024-08-26 restored | **CONFIRMED** | File present in both layers (confirmed structurally by the 366/366 file-count check below). Row count 9,870,901 — sane against neighbors 2024-08-23..29 (range 9.52M–10.57M). Index `sum(message_count)` for that day = 9,870,901, exactly equal to the broadcasts row count; index has 22,975 vessel-day rows that day. |
| 4 | `distance_m` recalculated (lat/lon argument-order fix) | **CONFIRMED** | Recomputed great-circle track distance (haversine over timestamp-ordered consecutive fixes per mmsi/day, R=6,371,000m) independently in SQL for 8 (mmsi, day) pairs spanning both years and three regimes (stationary, moderate/typical transit, and an extreme raw-data glitch). All 8 matched the index's stored `distance_m` to ~10–13 significant figures (floating-point-level agreement, not approximate). See detail table below. |
| 5 | New columns `position_spread_m` + `stationary_position_suspect`; flag rule; exemplar; suspect counts | **CONFIRMED** | Both columns present in index schema. Flag rule (`message_count>=10 AND sog_max<=0.5 AND position_spread_m>=1000`) spot-checked against all 22,612 index rows for 2025-05-22: **0 mismatches** (32 flagged, 32 rule-true). Pathological exemplar MMSI 367416060 / 2025-05-22 reproduced exactly: `distance_m=755105.8437056686` (recomputed independently: `755105.8437056687`), `suspect=True`, `message_count=317`, `sog_max=0.0`, `position_spread_m=755105.84` — this is the frozen-longitude (`min_lon=max_lon=-90.398`)/drifting-latitude (12.73→19.52) glitch from the session-12 followup, now correctly flagged. Suspect vessel-day counts: **6,111 for 2024, 7,210 for 2025** — both match the claim exactly (full-year `COUNT(*) WHERE stationary_position_suspect`). |
| 6 | `max_inter_msg_speed_ms` recalculated | **CONFIRMED** | Recomputed independently (max of consecutive-fix haversine-distance ÷ time-delta) for the same 8 (mmsi, day) pairs used for claim 4. All matched to ~9–13 significant figures, including the exemplar (13.352814496214835 vs recomputed 13.352814496215247) and the extreme case (374158000: 64653.312224522815 vs recomputed 64653.31222452285). |
| — | File counts 366/366 (2024, leap+restored day) / 365/365 (2025) | **CONFIRMED** | `glob` + regexp-extract-year count: broadcasts 2024=366, 2025=365; index 2024=366, 2025=365. All four match claimed counts exactly. |
| — | Total row counts 3,119,805,347 (2024) / 3,021,153,531 (2025) | **CONFIRMED** | `sum(message_count)` over the full-year index glob: 2024 = **3,119,805,347** (7,137,685 vessel-day rows), 2025 = **3,021,153,531** (7,523,491 vessel-day rows). Both exact matches to the claim. |

### Claim 4/6 detail table (index value vs independent SQL recompute)

| mmsi | date | message_count | index distance_m | recomputed distance_m | index max_inter_msg_speed_ms | recomputed |
|---|---|---|---|---|---|---|
| 367416060 (exemplar) | 2025-05-22 | 317 | 755105.8437056686 | 755105.8437056687 | 13.352814496214835 | 13.352814496215247 |
| 303829064 | 2024-07-15 | 1380 | 20790.449470369324 | 20790.449470553063 | 27.798731660713567 | 27.798731661272416 |
| 367456350 | 2024-07-15 | 1379 | 43705.12207303312 | 43705.12207297342 | 6.954050803656305 | 6.954050803656908 |
| 316001941 | 2024-07-15 | 270 | 0.0 | 0.0 | 0.0 | 0.0 |
| 374158000 (extreme glitch) | 2024-07-15 | 891 | 1907863871.1189084 | 1907863871.1189096 | 64653.312224522815 | 64653.31222452285 |
| 368257130 | 2025-01-15 | 1295 | 76342.24265867176 | 76342.2426587699 | 14.359165529314055 | 14.359165529303354 |
| 367529030 | 2025-01-15 | 1285 | 25452.63323890153 | 25452.633238909286 | 7.0288827117568164 | 7.02888271174305 |

All within floating-point noise of exact agreement across stationary,
typical, and pathological-extreme regimes, both years.

## Caveat fixed-vs-live enumeration

**FIXED-IN-DATA** (verified above, no further action needed on these):
- `base_date_time` format shift (2024 'T'-separator vs 2025 space) — FIXED.
- CET/CEST timestamp mis-parse — FIXED, offset is 0 everywhere sampled including DST-switch days.
- Missing day 2024-08-26 — FIXED, restored with sane counts and exact index/broadcasts reconciliation.
- `distance_m` argument-order formula bug — FIXED, now matches independent recomputation to float precision.
- `max_inter_msg_speed_ms` (same underlying formula bug) — FIXED, same evidence.

**STILL LIVE / unaffected by these six fixes** (none of the six claims addressed these, and evidence below confirms they persist unchanged):
- **Sparse-fix / gross-position-glitch distance inflation is NOT fixed.** The `distance_m` *formula* is now correct, but raw broadcast positions still contain physically-impossible jumps that flow straight through: MMSI 374158000 on 2024-07-15 shows `distance_m≈1.91 billion meters` (~1.9M km in a day) with `sog_max=16.7` — not caught by `stationary_position_suspect` because that flag only fires when `sog_max<=0.5`. The new flag is a **partial mitigation** covering the "reports near-zero speed but position jumps anyway" sub-case (correctly, per the exemplar and the 0-mismatch rule check), but a moving-vessel-reporting-nonzero-speed-with-a-glitch-leg is still silently unflagged and still inflates `distance_m`. This is the AIS-X-verified "sparse-fix index inflation" caveat (candidate c in the study's live registry work) — it is a raw-data/reception artifact, not something the six claims were ever scoped to fix, but it should NOT be read as resolved.
- **Sentinel encodings, unchanged and still year-constant.** `sog=102.3` (speed-not-available sentinel) appears only in 2024 samples (15,513–21,503 occurrences per sampled day, 0 in every 2025 sample); 2025 instead uses `sog IS NULL` (15,316–20,034 per day) for the same condition. Symmetrically, `heading=511` (not-available sentinel) appears only in 2024 (0 NULLs), while 2025 uses `heading IS NULL` (0 511s). Checked across 2024-07-15, 2024-01-15, 2025-01-15, 2025-05-22, 2025-07-15 — fully consistent, systematic by year, not day-to-day noise. This is the same provider-side year-constant encoding-shift pattern documented pre-regeneration; the rebuild did not (and was not claimed to) touch it.
- **Identity year-constancy / freeze in the broadcasts layer** — spot-checked (MMSI 367456350 across four 2024 months): `vessel_name` and `call_sign` each have exactly 1 distinct value across the year in broadcasts. Freeze mechanism is unchanged, still traced to broadcasts not the index.

**Not directly re-tested this session** (out of scope for the six claims, no reason from this session's evidence to suspect a change): centroid/position-blur caveats (m3-centroid-endpoints, m5-day-centroid-resolution), status-mostly-null, message-rate bias, Alaska-coverage footprint. These were untouched by the six claims and nothing observed here bears on them either way.

## Scope caveat for study consumers

**All existing M12/M13/M14 derived frames and every trial (AIS-X arms
A0/A1/A2, judge, measurer) evidence chain were computed against v1
data**, which no longer exists (overwritten in place). None of those
frames or chains have been re-verified against v2. Given claims 1, 2,
3, 4, and 6 are exact numeric/formula fixes (not distributional
changes) and claim 5's columns are additive, most prior *qualitative*
findings likely still hold, but any prior finding whose evidence
depended on raw `distance_m`, `base_date_time` string parsing, or
timestamp offset arithmetic should be treated as needing re-derivation
from v2, not merely re-cited.

## Discrepancies found

None. Every one of the six claims and both housekeeping claims
(file counts, total row counts) reproduced exactly or within
floating-point tolerance against independent recomputation. No
mismatches, no missing files, no row-count drift.

## Overall verdict: GO

All six claimed fixes verify mechanically against independent
recomputation, across both years, including boundary/DST days, the
named pathological exemplar, and additional self-selected stationary/
typical/extreme-glitch samples. File and row-count totals match the
claim exactly. Recommend:
1. **Switch study readers to the new data now** — the fixes are real, exact, and non-regressive on everything checked.
2. **Schedule the v2 production rebuild** (M12/M13/M14 frames + any distance_m/timestamp-dependent trial evidence) — required, not optional, since v1 no longer exists and this session found real behavioral differences (timestamp offset, base_date_time string shape, distance_m magnitude) that upstream frames encode.
3. **Do not treat this as closing the sparse-fix-inflation or sentinel-encoding caveats** — both remain live and should stay in the registry unchanged; the new `stationary_position_suspect` flag only covers one sub-case of the former.
