# V2 production rebuild -- journal

Run date: 2026-08-19. Purpose: re-derive the M12/M13/M14 derived frames
against the regenerated (v2) s3://ais-noaa bucket, per era anchor claim
`4291460c-d2ac-467d-a751-dcbb9bc28da8` and derived-frames era flag claim
`375caa59-6620-4713-9584-1f4a8f3041af` (both recorded earlier today by the
verification/era-flagging session; not re-litigated here). This is a
DELIBERATE NEW RUN, not an overwrite: every v1 artifact under `work/`
(stops_series_full/, feed_outages.parquet, stop_boundary_reasons.parquet,
m14_segments/, m14_placeholder_census.parquet, etc.) stays byte-identical;
all v2 outputs land at new `work/v2/...` paths.

## Spec sources read before starting

- `/workspaces/doxybase/docs/journal/ais-study/V2-VERIFICATION.md` -- the
  independent read-only verification report (GO verdict, 6 confirmed
  fixes, sentinel/identity caveats still live).
- Capsule claims `4291460c` (era anchor: what changed, six fixes, era
  rule) and `375caa59` (derived-frames era flag: which v1 frames exist,
  why cross-checking v1 vs v2 live is invalid, requirement that
  re-derivation run as new runs).
- `production/stage1_extract.py` / `stage2_build_stops.py` /
  `stage3_finalize.py` and `work/production-run-1.md` -- the proven v1
  M12 production realization (recorded SQL + the phase2/LOG.md
  determinism fix), used as the exact template for the v2 run.
- `work/m13/build_feed_outages.py`, `work/m13/build_boundary_reasons.py`
  -- the proven M13 realization.
- `work/m14/build_placeholder_census.py`, `extract_broadcasts.py`,
  `segregate.py`, `build_candidate_emitters.py` -- the proven M14
  realization.

## Era-appropriate deltas identified before running (all JOURNALED here,
none required an SQL change to the recorded M12 pattern)

1. **2024 = 366 observed days.** The restored day 2024-08-26 joins the
   population automatically: stage 1's monthly S3 glob
   (`s3://ais-noaa/broadcasts/2024/ais-2024-08-*.parquet`) picks up
   whatever files exist for that month with zero code change. No special
   case needed or added.
2. **base_date_time CASTs still fine.** `CAST(base_date_time AS
   TIMESTAMP)` is unchanged in every v2 script. V2-VERIFICATION.md claim 1
   confirms the string is now normalized to a single `'YYYY-MM-DD
   HH:MM:SS'` shape in both years, which `CAST` already parsed correctly
   under the old year-dependent-separator regime -- so this is a
   no-risk carry-forward, not a new assumption.
3. **sog sentinel, defensively 102.3-OR-NULL.** The recorded M12 validity
   filter is `sog IS NOT NULL AND sog <> 102.3`. This was ALREADY
   defensive against both encodings (`IS NOT NULL` catches a NULL
   sentinel, `<> 102.3` catches a literal sentinel) and matches the M12
   contract's own text ("non-null ... and not the 102.3 sentinel")
   verbatim -- so no SQL change was made. Confirmed empirically same-day,
   before running stage 1, against the live v2 bucket:
   - 2024-07-15: `sog=102.3` on 21,503 rows, `sog IS NULL` on 0 rows.
   - 2025-07-15: `sog=102.3` on 0 rows, `sog IS NULL` on 20,034 rows.
   This exactly reproduces the split V2-VERIFICATION.md's sentinel bullet
   and capsule observation `af58128d-7b6a-491b-a6c5-ddec6557ee8d` record
   (the curator's open sog-2025-NULL question): 2024 still uses the
   literal 102.3 sentinel, 2025 has switched to NULL. **"Which I saw":
   both, exactly year-split as reported, on every one of the 24 stage-1
   monthly runs** (per-month sog_1023/sog_null counts are logged in
   `production/v2/logs/stage1.log` and confirm 2024 months are 100%
   sog_1023/0% sog_null and 2025 months are the reverse).
4. **Timestamps: confirmed, not assumed.** Every v2 script (stage1,
   extract_broadcasts) uses `base_date_time`, never the `timestamp`
   column, matching the recorded M12 contract and the v1 realization
   exactly -- read from the actual script text before running, not
   assumed from memory.

## Stage log

### Stage 1 (filter + dedup + mmsi-bucket) -- COMPLETE

- Script: `production/v2/stage1_extract.py <year> <month>`, 24 months,
  4-way process parallelism (`xargs -P4`), each with its own
  `temp_directory` (stage1 docstring lesson from v1, reapplied).
- Ran as a detached background OS process (nohup+disown) since the full
  job exceeds a single foreground command's timeout; progress was
  monitored both via an async Monitor watch and, after a coordinator
  check-in, via direct foreground re-verification.
- **Verified complete and correct via independent re-query (not just log
  trust)**: `production/v2/stage1/` (the actual output location -- NOT
  `work/v2/`, which only holds prepared scripts and empty output dirs at
  this point in the run) contains 126GB across exactly 24 `ym=` partition
  dirs; `stage1.log` has all 24 monthly lines + `DONE_STAGE1`; directly
  querying the on-disk parquet files with a fresh DuckDB connection for
  both 2024-01 and 2025-12 returned row counts (221,490,672 /
  255,227,518) that exactly match the log. No stage1_extract processes
  remain running, which is the expected post-completion state (the
  driver's processes exit after each writes its result and the trailing
  `echo DONE_STAGE1` fires), not a crash signature.
- One false-positive incident during this stage: a coordinator message
  asserted the background driver was "dead" based on `work/v2/` staying
  static at 388K. That directory was never the data output path (it's
  `production/v2/stage1/`), so the check was against the wrong location;
  re-verification (above) confirmed the run was healthy and had in fact
  already finished by the time of the claim. No restart was performed;
  restarting would have discarded 126GB of already-complete, independently
  re-verified work.
- Per-month row counts (24/24, all succeeded, 0 tracebacks in stage1.err):
  2024-01 221,490,672; 2024-02 225,327,781; 2024-03 234,850,367; 2024-04
  245,649,132; 2024-05 288,139,243; 2024-06 288,997,247; 2024-07
  298,782,774; **2024-08 308,337,499** (v1's 2024-08 was 298,490,962 --
  the +9,846,537-row delta is the restored 2024-08-26 file flowing
  through, consistent with the verification report's 9,870,901 raw
  broadcast rows for that day minus the validity/dedup filter's usual
  ~0.4% shrinkage); 2024-09 269,302,257; 2024-10 263,706,253; 2024-11
  237,547,441; 2024-12 230,658,071; 2025-01 214,189,500; 2025-02
  203,323,577; 2025-03 238,968,641; 2025-04 242,109,630; 2025-05
  268,050,967; 2025-06 268,726,531; 2025-07 286,309,533; 2025-08
  273,785,954; 2025-09 249,200,127; 2025-10 254,080,316; 2025-11
  250,664,489; 2025-12 255,227,518.
- **Sentinel diagnostic (era delta #3, "which you saw"), recorded for
  every one of the 24 months**: every 2024 month shows sog_1023>0 /
  sog_null=0; every 2025 month shows sog_1023=0 / sog_null>0. Exactly the
  year-split V2-VERIFICATION.md and capsule observation
  `af58128d-7b6a-491b-a6c5-ddec6557ee8d` describe, confirmed at full-month
  scale (not just spot-check days) for the first time.
- All other v1-untouched paths and production/v2 outputs otherwise as
  planned; no code changes were needed to the recorded M12 SQL for any of
  the four era deltas.

### Stage 2 (per-bucket stop extraction) -- FIRST ATTEMPT FAILED (OOM), retrying at reduced concurrency

- First attempt: 64 buckets, 16-way parallelism (matching v1's proven
  pattern exactly, incl. `PRAGMA threads=1` / `memory_limit=8GB` per
  process). This box currently carries more concurrent baseline load
  than the v1 run did (other sessions/services observed at session start:
  ~27GB already in use before this run). Result: severe memory pressure
  (122/125GB used, swap climbing to 3.4/4GB) and 6 worker processes
  OOM-killed by the kernel within the first ~10 minutes; **zero buckets
  reached a valid completion** -- every one of the 22 `bucket=N.parquet`
  files present on disk after killing the job was a truncated stub
  (DuckDB creates the destination file before streaming content; a
  process killed mid-COPY leaves a file "too small to be a Parquet
  file", confirmed by attempting `read_parquet` on all 22 and getting
  that exact DuckDB error on every one). Caught before any file was
  trusted as real: validated every present output by re-reading it with
  a fresh DuckDB connection rather than trusting the driver's own log
  (which had also not printed a single success line yet). All stub files
  deleted, stale per-bucket temp dirs cleared, restarting clean --
  **never partially-trusted, no bucket silently short-populates the
  final frame.**
- Retry: same script, same SQL, **8-way parallelism** instead of 16
  (halves peak concurrent memory to fit this box's actual current
  headroom), plus a post-wave validation pass (every `bucket=N.parquet`
  re-read fresh before being accepted) with automatic retry of any
  bucket that is missing or fails to read, run to a fixed point (all 64
  valid) rather than trusting driver exit status alone.
- **Retry succeeded**: 64/64 buckets completed, 0 kills, 0 errors in
  `stage2.err`, memory stayed healthy throughout (60-113GB available,
  climbing as later waves had fewer concurrent buckets). Wall time ~58
  min (02:37-03:35 UTC) -- slower than v1's ~42 min at 16-way, the
  expected cost of halving concurrency for safety on a busier box.
  Independently re-validated (not just log-trusted): all 64
  `bucket=N.parquet` files re-read fresh, 6 spot-checked individually,
  full 64-file glob summed to 30,114,062 pre-finalize stop events.
- Two more false "stage-1 is dead, restart from scratch" coordinator
  messages arrived during/after this stage (repeating the same
  wrong-directory check). Not acted on for the same reason as the first:
  directly contradicted by fresh, independent verification performed
  moments before and after each message.

### Stage 3 (finalize: global stop_id + partition) -- COMPLETE

- `production/v2/stage3_finalize.py`, single foreground pass, 5.4s.
- **30,114,062 stop events**, 91,980 distinct MMSIs (v1: 30,080,069
  events / 91,977 MMSIs), start_ts/end_ts range 2024-01-01 00:00:00 ..
  2025-12-31 23:59:59, 24 `start_year_month` partitions (2024-01..2025-12,
  no gap), written to `work/v2/stops_series_full/`. 2.5GB on disk.
  Independently re-verified via a fresh DuckDB glob read (not the
  script's own printed count).
- **M12 v2 production run is DONE.** work/stops_series_full/ (v1) was
  never opened for writing at any point in this stage.
- Mid-run v1-untouched spot-check: work/stops_series_full/'s directory
  mtime (1784507238) still matches the pre-run baseline exactly.

## M13 v2 (feed outages + boundary attribution) -- COMPLETE

- `work/v2/build_feed_outages.py`: 6,021 raw stop_start islands (446
  qualify at vessels_affected>=200), 2,781 raw stop_end islands (408
  qualify). **854 total outage rows (446 stop_start + 408 stop_end) --
  an EXACT match to v1's 854**, despite the input series growing by
  +34K events. Consistent with M13's method being dominated by systemic,
  population-wide reception events (same-second collision clustering),
  not sensitive to small per-event deltas from the restored day or minor
  structural differences. vessels_affected range 200-12,044 (v2) vs
  v1's 200-12,044 (identical range). Build time 52.8s. Written to
  `work/v2/feed_outages.parquet`, independently re-verified (854 rows,
  fresh read).
- `work/v2/build_boundary_reasons.py`: 60,228,124 rows (exactly
  2x30,114,062 stop events), 7.1s. Reason-class shape closely tracks v1:
  movement 33.06% (v1 33.0%), silence_gap 63.88% (v1 63.9%), feed_outage
  2.75% (v1 2.8%), series_edge 0.31% (v1 0.3%). Written to
  `work/v2/stop_boundary_reasons.parquet`, independently re-verified
  (row count matches 2x the v2 stop count exactly).
- v1's `work/feed_outages.parquet` and `work/stop_boundary_reasons.parquet`
  were never opened for writing.

## M14 v2 (placeholder census + segregation) -- COMPLETE

- `work/v2/build_placeholder_census.py` against `work/v2/stops_series_full/`:
  35 rows (7 known + 28 newly screened), 18,255 total stop events across
  the census (v1: 18,246), 7,152 for the known-7 alone (v1: 7,146).
  **Top-3 by stop count are the SAME MMSIs as v1**: 444444444 (3,796
  stops, v1 3,794), 982000000 (2,352, v1 2,349), 310000000 (2,153, v1
  2,152) -- confirms the census composition is stable across the era
  boundary, not just coincidentally similar in size.
- `work/v2/extract_broadcasts.py 444444444,982000000,310000000`:
  204,121 / 148,668 / 190,213 deduped rows (v1: 203,969 / 148,326 /
  189,838) -- small, consistent increases, same shape as every other v2
  delta so far.
- `work/v2/segregate.py` (same MMSIS): **track counts identical to v1**
  -- 444444444 -> 2 tracks, 982000000 -> 3 tracks, 310000000 -> 27
  tracks. Confirms the greedy segregation result is not just similar but
  structurally the same population of physical objects, era over era.
- `work/v2/build_candidate_emitters.py`: 32 candidate-emitter rows
  (matches v1's 32 exactly), same names_seen/callsigns_seen singleton
  pattern (M/Y CASUAL, RBS11, UNFORGETTABLEOF), same transceiver-class
  split behavior noted in v1 (444444444 track 0: ['B'] only; track 1:
  ['A','B']).
- **m14-feasibility-respected invariant verified directly on the v2
  output**: 543,002 total segment-message rows (v1: 542,133), **0**
  rows with `assign_speed_ms > 50` -- 0 violations, matching v1's
  recorded 0-violation verification.
- v1's `work/m14_segments/`, `work/m14_placeholder_census.parquet` were
  never opened for writing; all v2 M14 outputs under `work/v2/m14/raw/`
  and `work/v2/m14_segments/`.

## Capsule recording

- `work/v2/record_deltas.py`: 2 observations recorded (M12 stops delta:
  v2 30,114,062 vs v1 30,080,069, +33,993/+0.1130%, with the restored
  day's own contribution -- 58,222 events touch 2024-08-26, 45,622 of
  which START that day -- called out explicitly since v1 could not
  contain any by construction; M13 outages delta: v2 854 vs v1 854, +0,
  explained as expected given M13's method depends only on
  stops_series_full's own start_ts/end_ts island-clustering, which the
  restored day's ~34K extra events did not shift past any threshold).
  One retry needed: `rc:AbsoluteDelta`/`rc:RelativeDelta` are not valid
  `rc:` profile-metric kinds (targeted error named the five valid kinds
  -- MaximumValue/MeanValue/MedianValue/MinimumValue/
  StandardDeviationValue -- and that a project-specific full IRI is also
  accepted); fixed by dropping profile_metrics and keeping the deltas in
  prose (summary/evidence_summary), which the schema fully supports.
- `work/v2/record_datasets.py`: 6 new v2 sibling dataset nodes recorded
  (`stops-series-full-v2`, `feed-outages-v2`, `stop-boundary-reasons-v2`,
  `m14-placeholder-census-v2`, `m14-candidate-emitters-v2`,
  `m14-segment-messages-v2`), none superseding their v1 counterparts.
  Columns inherited by reference (schemas identical to v1; no new
  rc:Column facts needed since the recorded SQL is byte-identical to
  v1's). Provenance: a staged graph revision (conforms=true, 0 results)
  added `rc:citesClaim` to both the era anchor (4291460c) and the era
  flag claim (375caa59) plus `rdfs:seeAlso` to each v1 sibling and its
  M12/M13/M14 contract+pattern, on all 6 new datasets (35 triples,
  applied cleanly: staged
  `.../staged-revision/dc99f497-d8a5-4963-beea-b244ba267e54`, applied
  `.../applied-revision/15bf2521-bd77-4fd7-a2a3-849a9d436265`).
- Final `validate_graph(scope="all")` -> conforms=true, 0 results.
  `list_revisions(current_staged_work_only=true)` -> 0 rows. No staged
  debt at any point in the run (checked after every staged-revision
  apply, not just at the end).

## v1-untouched verification (final)

`/tmp/v2run/verify_v1_untouched.sh`, run at the very end against the
pre-run baseline captured before any v2 work began: every v1 artifact's
mtime AND a full-tree md5 of (mtime, path) pairs for the two directory
frames (`work/stops_series_full/`, `work/m14_segments/`) are **byte-
identical** to the baseline (`diff` on the data lines, excluding only
the timestamp in each run's own header line, is empty). v1 was never
opened for writing at any point in this run.

## Friction summary (for the final report)

1. **Naming collision risk avoided**: `work/v2/` already existed as an
   unrelated directory from an earlier (2026-07-08) "ontology v2"
   revision session -- a different meaning of "v2" entirely. New v2
   production files were added as new subpaths/filenames inside it
   without touching any pre-existing file there.
2. **Stage-1 sentinel diagnostic roughly doubled stage-1's per-month
   wall time** (an extra full-month scan before the COPY) -- a
   deliberate cost for a permanent, per-month "which you saw" record
   rather than a single spot check; worth it for six sessions running
   this pipeline again on future data eras.
3. **Stage-2 OOM at the proven v1 concurrency (16-way)**: this box
   carries more concurrent baseline load now than during the v1 run;
   16-way exhausted memory and silently produced 22 truncated stub
   `bucket=N.parquet` files (DuckDB creates the destination file before
   streaming rows, so a killed process leaves a "file too small to be
   Parquet" stub, not a missing file). Caught by validating every output
   with a fresh independent read rather than trusting the driver log;
   none were used. Fixed by halving concurrency to 8-way (clean 64/64
   run, 0 kills) -- costs ~16 more minutes of wall time for zero
   correctness risk.
4. **Repeated false "process is dead, restart from scratch" coordinator
   messages** (at least 3 across the run) all traced to the same
   checking mistake: inspecting `work/v2/` (scripts only) instead of the
   actual data paths (`production/v2/stage1/`, `production/v2/stage2/`).
   Each time, independent fresh-query verification (row counts against
   the real files, not log text) directly contradicted the claim before
   any restart was performed; no compute was discarded on an unverified
   report. Switched from async Monitor-based waiting to foreground
   bounded polling loops after the first such message, which is a
   genuine improvement (keeps verification in the same command as the
   wait, and every stage from stage 2 onward was independently spot-
   checked immediately after its driver reported done).
5. **`rc:AbsoluteDelta`/`rc:RelativeDelta` are not valid profile-metric
   kinds** (see Capsule recording above) -- one-call fix, no retry loop
   needed.

## Reproduction

1. `venv/bin/python production/v2/stage1_extract.py <year> <month>` for
   each of the 24 months (parallelize modestly -- 8-way was the safe
   level on this box at run time; 16-way OOM'd).
2. `venv/bin/python production/v2/stage2_build_stops.py <bucket>` for
   buckets 0..63 (8-way parallel; validate every output file with a
   fresh read before trusting it).
3. `venv/bin/python production/v2/stage3_finalize.py`
4. `venv/bin/python work/v2/build_feed_outages.py` then
   `venv/bin/python work/v2/build_boundary_reasons.py`.
5. `venv/bin/python work/v2/build_placeholder_census.py`, note its
   printed `TOP3_FOR_SEGREGATION` line, then
   `venv/bin/python work/v2/extract_broadcasts.py <top3-csv>`,
   `venv/bin/python work/v2/segregate.py <top3-csv>`,
   `venv/bin/python work/v2/build_candidate_emitters.py <top3-csv>`.
6. `venv/bin/python work/v2/summary_stats.py`,
   `venv/bin/python work/v2/record_deltas.py`,
   `venv/bin/python work/v2/record_datasets.py`.
Intermediates (`production/v2/stage1/` 126GB, `production/v2/stage2/`
2.3GB) are regenerable and may be deleted; the deliverables are
`work/v2/stops_series_full/`, `work/v2/feed_outages.parquet`,
`work/v2/stop_boundary_reasons.parquet`, `work/v2/m14_placeholder_census.parquet`,
`work/v2/m14_segments/`.

## Headline v2-vs-v1 numbers (final)

| Frame | v1 | v2 | delta |
|---|---|---|---|
| M12 stop events | 30,080,069 | 30,114,062 | +33,993 (+0.113%) |
| M12 distinct MMSIs with a stop | 91,977 | 91,980 | +3 |
| M13 outage rows | 854 | 854 | +0 |
| M13 boundary-reason rows | 60,160,138 | 60,228,124 | +67,986 (=2x the stop delta) |
| M14 placeholder census rows | 35 | 35 | +0 (same MMSI set) |
| M14 candidate emitters | 32 | 32 | +0 (same track counts per MMSI) |
| M14 segment messages | 542,133 | 543,002 | +869 |
| Restored day 2024-08-26 (v2 only) | n/a | 58,222 events touch it, 45,622 start on it, 19,717 distinct MMSIs | v1 structurally cannot contain any |
