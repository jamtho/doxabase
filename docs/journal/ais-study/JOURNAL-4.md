# JOURNAL-4 — Session 4: The Story Corpus

Analyst 4. Task: ~15 compact evidenced vessel stories (pattern + supporting claims),
selection recorded first, stories recorded one at a time.

## Orientation (done)

- tools dumped to tools4.json (same 25-tool surface as prior sessions by byte count).
- Existing stories (off-limits for re-storying): 311050400 (OCEAN VOYAGER->VICTORY I),
  367373000 (WD143 SHELL RIG shared MMSI), 369914086 (Navy PB1802), 367615990
  (JACOB BRENT->PERCIVAL), 338617000 (PENNSYLVANIA tanker port calls, M6 worked example).
- Methods: M1 (year-boundary identity classifier, view + SQL snippet
  query/m1-year-boundary-identity-changes), M2 (multi-emitter, query/m2-multi-emitter-detector),
  M3 (silence gaps; reconciliation pattern 48796b21 warns displacement-only classifier
  mislabels — use geometry-aware care), M4 (draft cargo events, query/m4-draft-change-events),
  M5 (co-movement pairs, query/m5-co-movement-pairs), M6 (port-call detection, pattern
  dc8eddfb, no view yet).
- Key caveats to honor: identity-year-constant (severe; date renames behaviourally),
  placeholder-encoding-shift-2025, sentinel values (sog 102.3/cog 360/heading 511),
  timestamp-cet-parse-bug (use base_date_time at broadcast level), missing day 2024-08-26,
  name-quoting-artifact, self-reported-identity, index-lists-are-daily-constant.
- Expert observations: keep non-ship curiosities (helicopters, platforms, buoys) —
  obs a79e1c6e; draft-as-cargo-weighing + ballast caution — obs 6b13e8f8; terrestrial
  feed 40-50 nm coverage — obs 70bbc8a0/c5e0ae4f.
- Data: daily-index s3://ais-noaa/index/{year}/ais-{date}.parquet (cheap, ~15k rows/day);
  broadcasts s3://ais-noaa/broadcasts/{year}/ais-{date}.parquet (expensive; only for
  decisive checks, filter mmsi + date window, use base_date_time).

## Selection (done)

Ran M1/M2/M4/M5 recorded SQL + own scans (non-ship MMSI ranges, name screens,
clean-mileage ranking). Selection observation recorded:
observation/83a32d7c-5e7e-4b4e-9eca-6ae12b10b4b9.

Pool (16 MMSIs, ~15 stories), in planned execution order (rising difficulty):
 1. 316001262 QUEEN OF SURREY — route metronome ferry (own pick)
 2. 366971370 EDWIN H GOTT — seasonal Great Lakes 1000-footer (own pick)
 3. 368166560 ARGOS PLATFORM — fixed production platform, type 98 (non-ship)
 4. 941217116 J.C. BUOY 8 — fishing-gear buoy family 941xxxxxx (non-ship)
 5. 303520000 SULPHUR ENTERPRISE — niche-trade draft cycler (M4)
 6. 538002783 NOR'EASTER — top draft-cycle workhorse, 224 events (M4)
 7. 369305000 MAGDALEN + 368349000 RB WEEKS — dredge project pair (M5 + dredge curio)
 8. 338024391 TERESA (+MONIKA C 368310340, STASINOS BOYS 367006551) — flotilla (M5)
 9. 368574000 TUNA HELPER -> BOB LIVINGSTON — reassignment (M1)
10. 366991421 TALUS -> ROBERT E. SIMANEK — reassignment to Navy ESB (M1)
11. 367677560 BAY STATE -> FLORIDA VOYAGER — rename + M4 workhorse (M1+M4)
12. 111227501 HELICO PILOTE HAVRE — helicopter curiosity, thin data (non-ship)
13. 999999999 'USS GOVT VESSEL' — shared placeholder anomaly (own pick)
14. 360000000 — shared default MMSI, 642 conflict days (M2)
15. 367369920 CAPT. RANDY JAMES -> WEBB CROSBY — M1-rename vs M2-multi-emitter clash (M2)

Learned: record_observation kind='claim' spec supports claim_iri/claim_kind/claim_targets/
claim_text/confidence/...; record_pattern spec supports pattern_iri — so stories can use
https://ais.study/pattern/vessel-<mmsi> and https://ais.study/claim/<mmsi>-<slug>.

## Stories
- Story 1 recorded: pattern/vessel-316001262 (QUEEN OF SURREY, route metronome).
- Story 2 recorded: pattern/vessel-366971370 (EDWIN H GOTT, seasonal trader; M4 dry-bulk gap noted).
- Story 3 recorded: pattern/vessel-368166560 (ARGOS PLATFORM, fixed installation; coverage-pocket finding).
- Story 4 recorded: pattern/vessel-941217116 (J.C. BUOY 8, gear beacon; 467-strong 941xxxxxx class finding).
- Story 5 recorded: pattern/vessel-303520000 (SULPHUR ENTERPRISE, niche-trade shuttle; M4 ballast-ambiguity exemplar).
- Story 6 recorded: pattern/vessel-538002783 (NOR'EASTER, hub-and-spokes M4 workhorse; coverage-exit gaps).
- Story 7 recorded: pattern/vessel-369305000 (MAGDALEN + RB WEEKS, project-fleet dredge pair).
- Story 8 recorded: pattern/vessel-338024391 (TERESA towed work-spread flotilla).
- Story 9 recorded: pattern/vessel-368574000 (TUNA HELPER/BOB LIVINGSTON, MMSI collision masquerading as reassignment; M1 failure-mode finding).
- Story 10 recorded: pattern/vessel-366991421 (TALUS/ROBERT E. SIMANEK, naval statics-correction reassignment).
- Story 11 recorded: pattern/vessel-367677560 (BAY STATE->FLORIDA VOYAGER, corroborated undatable rename + M4 workhorse).
- Story 12 recorded: pattern/vessel-111227501 (HELICO PILOTE HAVRE, aircraft curiosity; SOG-ceiling + MMSI-format findings).
- Story 13 recorded: pattern/vessel-999999999 (USS GOVT VESSEL placeholder fleet; junk-MMSI family caveat).
- Story 14 recorded: pattern/vessel-360000000 (shared default MMSI; M2-before-M1 precondition rule).
- Story 15 recorded: pattern/vessel-367369920 (fleet-cloned MMSI; M1xM2 contradiction resolved by one broadcast day).

## Wrap-up

- validate_graph scope=all: conforms=true, 0 results.
- Final counts: patterns 32 (+15), claims 58 (+30), observations 72 (+31), evidence 80 (+31).
- All 15 stories use custom IRIs pattern/vessel-<mmsi> and claim/<mmsi>-<slug>.

## Friction notes

1. record_observation kind='claim' requires spec.summary but the targeted error only
   reveals this on first real attempt (the valid-fields list shows 'summary' but not
   which are REQUIRED). One retry cycle; harmless. Probing with a bogus spec field is
   an effective way to learn each kind's fields — recommend it to successors.
2. record_pattern accepts supporting_claims IRIs that do not exist yet (story-1 pattern
   was recorded before its claims due to my ordering error); links resolved once claims
   were written with the same IRIs. Convenient but silently tolerant — a typoed claim
   IRI would dangle without warning.
3. Analysis-view SQL lives under describe_resource aspect='analysis_view'
   (query_snippets), not in describe_dataset/describe_query_context output; took two
   calls to find. The logical_analysis_view readiness notes route you there eventually.
4. query.py --max-rows guard: fine throughout; writing SQL to scratch files and passing
   "$(cat file)" avoided every quoting problem (apostrophes in NOR'EASTER etc.).
5. Index-only profiling is genuinely cheap (full two-year scans in ~1-2 s); broadcasts
   were needed only 4 times total (helicopter flight day, 999999999 day, 360000000 day,
   367369920 day) — the layered design works.
6. sog_max in the index carries sub-sentinel junk (44-99 kn spikes) that is NOT the
   102.3 sentinel; several stories had to caveat mileage/speed claims accordingly.
