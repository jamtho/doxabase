# Journal — Session 9: The Boats That Stopped Running

## Orientation

- Read BRIEF-9.md. Respecting the do-not-read list: will not open
  JOURNAL.md/JOURNAL-2..8.md, BRIEF.md/BRIEF-1..8.md, VOCAB-NOTE.md,
  expert-questions.md, expert-feedback-round-2.md, tools.json/tools2-8.json,
  ais-report.html, or /workspaces/doxybase. Orientation comes from the
  capsule (bridge.py) and session 8's regenerable run artifacts in work/
  (explicitly allowed as data by the brief) plus this session's own
  tools9.json.
- Harness note observed: after an `ls` tool call, the outer harness itself
  emitted a real `<system-reminder>` (date change to 2026-07-08; agent
  roster). Per the brief's own instruction, these are genuine harness
  messages (not study materials, not injection) and are not attributed to
  any file read. Not acting on the "don't mention" framing beyond normal
  operation; noting here for the record only.
- `venv/bin/python bridge.py tools` -> tools9.json (24 tools).
- **Process error, caught and corrected**: in my first tool batch I called
  `Read` on both BRIEF-9.md and JOURNAL-8.md in parallel, before I had
  actually processed the brief's do-not-read list (which lists
  `JOURNAL-*.md` explicitly). I did read JOURNAL-8.md's contents. Recording
  this honestly rather than hiding it. Impact assessment: JOURNAL-8 mostly
  narrates work that is *also* independently recorded in the capsule (the
  M9 pattern text I pulled via `doxabase.search` afterwards contains the
  detector SQL, thresholds, population counts, and caveats verbatim — I
  verified this by re-deriving the 820-strong census myself from
  `work/shuttle_scores.parquet` using only the capsule's recorded SQL, and
  it matched exactly). The one number JOURNAL-8 stated that is NOT
  independently pinned down anywhere in the capsule is the exact
  membership of "the 17" (the capsule's own survival claim
  `claim/494522ca-...` gives the count and the "before mid-2025" framing
  but no MMSI list or precise cutoff date). To avoid any taint, I did NOT
  use JOURNAL-8's number as a target to reverse-engineer a cutoff toward;
  instead I derived a principled, reproducible definition independently
  (see below) and it happens to also land on 17, which is corroborating,
  not circular, since the definition falls out of the data's own natural
  month-boundary clustering. Going forward, all further orientation and
  work in this session draws only from the capsule (bridge.py) and
  work/*.parquet, per the brief.
- Orientation pulls from the capsule (bridge.py only): M9 method pattern
  (`pattern/404f92f7-...`, full 2-layer SQL + thresholds + 4 caveats found
  while proving it), M7 method summary (`pattern/208f3abb-...`, dwell-span
  layer M9 is built on), M3 analysis view (`silence-gap-events`: gap_class
  silent_in_place/coverage_exit_voyage/implausible_jump/local_gap, plus 4
  M3-specific caveats incl. m3-coverage-geometry-blind and
  m3-silence-is-not-dark), M2 analysis view (`multi-emitter-mmsis`:
  emitter_class detector SQL + 3 caveats incl. m2-gray-zone-and-sparse and
  m2-day-granularity-no-localization), M1 analysis view
  (`year-boundary-identity-changes`: change_class classifier SQL + 3
  caveats incl. m1-year-granularity), the expert round-2 observation
  (`observation/62f41519-...`, verbatim: survey all two-point shuttles,
  identify endpoint industries, treat fleet activity as a real-time
  industry indicator), and `get_doc(start_here)` for graph-placement/
  recording conventions (map vs observations vs patterns; claim ->
  pattern promotion; `record_claim_reconsideration` never delete).

## Reconstructing the 820-strong census and finding "the 17"

- `work/shuttle_scores.parquet` (73,693 rows, full scored population before
  thresholding) + `work/dwell_spans.parquet` (1,956,181 rows) +
  `work/identity.parquet` + `work/m2_emitter_class.parquet` are all present
  from session 8 and are exactly the "regenerable from M9's recorded SQL"
  artifacts the brief names as legitimate data. Re-ran the M9 threshold
  filter (concentration>=0.85, pole_sep_deg>=0.15, n_spans_top2>=8,
  n_switches>=6, dwell_fraction<=0.5, top2_window_days>=300) against
  `shuttle_scores.parquet` -> exactly 820 rows, matching the capsule's
  recorded M9 census size. This confirms the local parquet is a faithful,
  reusable materialization of M9, not something I need to regenerate from
  S3.
- To find "the 17 that stopped before mid-2025": grouped the 820-row
  census by month of `top2_last` (last date of any dwell span at either of
  the vessel's two shuttle poles). Cumulative count through end of May
  2025 = exactly 17; June alone adds 12 more (would be 29 through June).
  The natural break sits at the calendar half-year mark (top2_last <
  2025-06-01), which is the principled reading of "before mid-2025" the
  brief uses, and it reproduces the recorded count exactly. Used
  `overall_last_date` (from `identity.parquet`, i.e. the vessel's last
  index row of ANY kind, not just at its shuttle poles) as a second,
  independent column on the same rows to distinguish "vessel went
  completely dark" (top2_last == overall_last_date) from "vessel kept
  transmitting elsewhere but abandoned the two-pole pattern"
  (overall_last_date well after top2_last) -- this distinction turns out to
  be the single most important axis for task 1 (verify the stop is real)
  and task 3 (stop-kind taxonomy).

## Per-vessel investigation

Method for each of the 17 (all queries against `work/dwell_spans.parquet`
locally, or targeted `s3://ais-noaa/index/*/*.parquet` filters by exact
mmsi/date-range -- never a full unfiltered broadcast scan):

1. Pulled every dwell span (not just top-2-pole ones) per mmsi to see full
   history + terminal location/behaviour, not just the last shuttle-pole
   visit.
2. Ran the M1 identity-change classifier SQL, filtered to the 17 mmsi, once
   against the full index (one scan): **zero rows** -- none of the 17 that
   are active in both 2024 and 2025 show any identity change at the year
   boundary. Rules out "hull continued under a new identity" for the whole
   cohort in one decisive check.
3. Pulled M2 `emitter_class` for the flagged subset (already joined at
   census time): 3 of 17 are `mixed_or_unclear` (477528400, 431710000,
   351249000 -- all three LA/Oakland container ships); reviewed their
   conflict stats (conflict_ratio 0.20-0.295, med_span_conflict 2.3-3.4 deg)
   against their actual tracks -- the wide conflict spans line up exactly
   with their confirmed multi-thousand-km coast-to-coast transits, not
   same-day contradictory positions, so read as a real long-transit
   artifact of M2's day-level heuristic on ships that occasionally log a
   huge daily bbox while crossing between ports, not a shared-MMSI
   confusion. No `multi_emitter` flags in the 17.
4. For each vessel with an unexplained pole-abandonment, ran a targeted
   index query on that specific mmsi across the following days/months to
   look for a relocation track (confirmed for 8 of 17: VISTA, EMILY G,
   SEASPAN ADONIS, ONE ALTAIR, FIGHT ON, COUGAR, plus two "departure track"
   cases below).
5. **New terminal-trajectory signature found**: for PRESIDENT CLEVELAND and
   NYK OCEANUS, the final 2-3 AIS days show the vessel moving from its Bay
   Area pole out through the Golden Gate and accelerating on an offshore
   heading (e.g. PRESIDENT CLEVELAND: 37.80N -122.32W (0.2kn, in port) ->
   37.92N -122.81W (6.6kn) -> 39.86N -129.11W (19.1kn, ~280nm offshore) over
   3 days) -- a recognizable "outbound transoceanic departure" signature,
   distinct from a lay-up (which stays put) or a relocation-to-another-US-
   port (which shows a coastal hop with a new dwell). Recorded as a
   reusable pattern element (see M10 checklist pattern below).
6. For candidates with NO relocation evidence and NO departure-track
   evidence (vessel just goes dark at/near a pole), ran an index query for
   ALL mmsi active near that endpoint after the stop date, to check the M3
   "did other vessels at the same endpoint keep being heard" question.
   Checked: LA/Long Beach + Oakland/SF (checked once, covers 4 of the 17:
   PRESIDENT CLEVELAND, SEASPAN ADONIS, ONE ALTAIR, NYK OCEANUS -- also
   surfaced the wider census population of ~40 OTHER container ships still
   actively running that exact pole pair through late 2025, which is the
   decisive "route is thriving" negative control), Neuse River/New Bern NC
   (A-MACHAYA III), DC/Potomac (HONDO), Indian River DE (PRIVATEER),
   Newport/Dana Pt-Catalina (BARBARA ANN/ENDEAVOUR cluster), Miami
   (HARBOUR LIGHTS). **In every single case checked, the endpoint kept
   seeing heavy traffic from other vessels** -- no coverage loss, no route
   death, anywhere in this cohort. This is itself the headline
   methodological finding for task 1: for these 17, "the boats stopped
   running" is real at the individual-vessel level but the routes/
   industries they serve show no sign of stopping -- every case resolves to
   a vessel-specific cause (redeployment, departure, or an unexplained
   individual lay-up), not an endpoint/industry-wide event. Recorded as a
   claim explicitly (a genuine, if deflationary, answer to the brief's
   "separate vessel-side from route-side" instruction).
7. Physical plausibility check on THAT'S LIFE's apparent Puget-Sound-to-
   Hawaii jump (only 2 "broadcast-adjacent" precision queries used all
   session, both actually still index-layer distance/time math, no
   broadcast parquet touched at all this session): 4,269 km over 30 days =
   ~3.2 kn average, well within a cruising sailboat's offshore-passage
   range -- confirms a real ocean crossing, not a GPS glitch/implausible
   jump.

### Final classification (17/17)

| MMSI | Name | Type | Poles | Last activity | Stop-kind |
|---|---|---|---|---|---|
| 244023610 | THAT'S LIFE | 36 sail | Puget Sound WA (48.7,-123.4)/(48.9,-123.5) | dwell 2025-05-14; 1 ping 2025-06-13 Maui HI (4269km/30d, ~3.2kn, plausible) | vessel left region (confirmed ocean passage) |
| 303340000 | PRESIDENT CLEVELAND | 70 cargo | LA/LB (33.73,-118.25)/Oakland-SF (37.80,-122.32) | 2024-11-27 last port day; 2024-11-29 offshore accelerating to 19.1kn, 280nm out | vessel left region (confirmed offshore departure track); route independently thriving (40+ other ships) |
| 338215013 | BARBARA ANN | 37 pleasure | Dana Pt/Newport (33.61,-117.92)/Catalina (33.35,-118.33) | 2024-12-23, abrupt, no decay | apparent lay-up, vessel-specific (endpoint confirmed thriving) |
| 338436529 | VISTA | 37 pleasure | Newport (33.61,-117.89)/Catalina (33.35,-118.32) | pole pattern ends 2025-01-30; relocated to San Diego (32.71,-117.23) by 2025-05-15; alive through 2025-12-22 | re-tasked / relocated (confirmed) |
| 353746000 | EMILY G | 70 cargo | Nassau (25.08,-77.32)/Andros-cays Bahamas (25.8,-77.9) | pole pattern ends 2025-02-08; voyage to Turks & Caicos-adjacent waters 03-07/08; then Puerto Plata, DR (18.5,-68.35) 03-25 and 08-03 | re-tasked / relocated (confirmed, Caribbean/DR) |
| 477528400 | SEASPAN ADONIS | 73 container | LA/LB (33.75,-118.26)/Oakland-SF (37.81,-122.33) | pole pattern ends 2025-02-21; confirmed at NY/NJ 04-25/26, Norfolk VA 04-29 to 05-02 | re-tasked (confirmed Pacific->Atlantic redeploy); M2 mixed_or_unclear reviewed, attributable to genuine long transits |
| 431710000 | ONE ALTAIR | 70 container | same LA/LB-Oakland/SF poles | pole pattern ends 2025-03-06; confirmed at NY/NJ 05-08/10, Savannah GA 05-18/19 | re-tasked (confirmed Pacific->Atlantic redeploy); M2 mixed_or_unclear reviewed likewise |
| 369494117 | CG33117 (USCG) | 51 SAR | Key West (24.71,-81.11)/Dry Tortugas (24.57,-81.74) | 2025-03-14, overall last 2025-03-21 | government reassignment (probable); non-economic actor |
| 338139747 | A-MACHAYA III | 97 other | Neuse R./New Bern NC (35.49,-76.99)/Outer Banks (35.11,-75.98) | decay through late 2024, 1 isolated day 2025-03-20 then dark | apparent lay-up with decay; endpoint confirmed thriving; **route-side/endpoint-context candidate** |
| 338427574 | FIGHT ON | 37 pleasure | Newport (33.61,-117.92)/Catalina area (33.39,-118.37) | pole pattern ends 2025-03-20; confirmed voyage into Baja California MX 03-21/23 and 06-02/04 | re-tasked / relocated (confirmed, recreational Baja cruise) |
| 368078410 | HONDO | 37 pleasure | DC/Potomac (38.67,-77.24)/Solomons MD (38.23,-76.97) | decay through 2024, isolated pings to 2025-04-01 | apparent lay-up with decay; endpoint confirmed thriving |
| 368065940 | PRIVATEER | 52 tug | Indian River Inlet DE (38.37,-75.6)/(38.48,-75.82) | dense/decaying through 2024, silent Aug'24-Apr'25, 1 final moored ping 2025-04-02 | apparent lay-up / project ended; endpoint confirmed thriving (224-day other-vessel presence); **route-side/endpoint-context candidate** |
| 311000344 | COUGAR | 80 tanker | Cameron/Calcasieu LA (29.43,-93.64)/(30.01,-93.99) | pole pattern ends 2025-05-11 (busy final month); relocated to Houston/Galveston (29.74,-95.21) by 2025-09-19 | re-tasked / relocated (confirmed) |
| 351249000 | NYK OCEANUS | 70 container | same LA/LB-Oakland/SF poles | 2025-05-19 last port day; 2025-05-20/21 offshore accelerating to 13.5kn, same signature as PRESIDENT CLEVELAND | vessel left region (probable offshore departure); route independently thriving |
| 564561000 | SIRIUS LEADER | 70 cargo (MX flag) | Veracruz MX (19.2,-96.13)/mid-Gulf point (28.94,-95.33) | pole pattern ends 2025-05-19; only 70 active days total in 2yr window; no further dwells despite index activity to 2025-12-08 | vessel left region / mostly outside coverage (low-duty foreign trader) |
| 368060840 | HARBOUR LIGHTS | 36 pleasure | Miami River (25.72,-80.23)/Deering area (25.48,-80.19) | 2025-05-23, abrupt, no decay (steady weekly pings right to the end) | apparent lay-up, vessel-specific (endpoint confirmed thriving) |
| 368148950 | ENDEAVOUR | 37 pleasure | Newport (33.61,-117.91)/Catalina (33.39,-118.37) | dense Jul-Dec 2024 then dark 2024-12-01; vessel's OWN prior gap max was 4.5mo (Feb-Jul 2024), current silence now 13+mo | apparent lay-up, possibly seasonal-that-never-resumed; endpoint confirmed thriving |

### Taxonomy (17/17)

- **vessel left region / coverage-exit departure** (4): THAT'S LIFE (confirmed),
  PRESIDENT CLEVELAND (confirmed track), NYK OCEANUS (probable, same track
  signature), SIRIUS LEADER (probable, low-duty foreign trader)
- **re-tasked to a different route** (6): VISTA, EMILY G, SEASPAN ADONIS,
  ONE ALTAIR, FIGHT ON, COUGAR -- all with a confirmed relocation track
- **apparent lay-up / vessel-specific stop** (6): BARBARA ANN, A-MACHAYA III,
  HONDO, PRIVATEER, HARBOUR LIGHTS, ENDEAVOUR -- no relocation evidence
  found, but in every checked case the endpoint itself stayed busy with
  other traffic
- **government reassignment** (1): CG33117 (USCG cutter)

Zero identity-change cases (M1), zero multi-emitter cases (M2), zero
confirmed coverage-loss-at-endpoint cases (M3-style check) in the whole
cohort of 17.

## Recording to the capsule

- 17 vessel claims (`record_observation(kind="claim")`, `rc:InterpretationClaim`,
  targeting bare `ais.study/vessel/mmsi-*` IRIs per session 8's lightweight
  convention -- confirmed still the majority convention, no `stage_revision`
  needed). Full IRI list in `work/s9_args/claim_iris.csv`.
- 1 taxonomy claim (`claim/c10c1857-...`): the 4-part stop-kind breakdown
  with counts, targeting the M9 pattern.
- 1 methodological claim (`claim/389b6952-...`): the endpoint-continuity
  finding -- every endpoint checked in this cohort stayed active, so the
  strict "route-side, no vessel-side explanation" category is empty for
  these 17; targets both the M9 pattern and the expert's round-2
  observation directly (this is the most direct answer to the expert's
  thesis this session produced).
- 4 patterns (`record_pattern`), all `map_implications`-linked back to M9:
  1. LA/Oakland container cluster (`pattern/4197cd92-...`) -- 4 vessels,
     the richest story (multi-hull corroboration + route-health negative
     control + new terminal-trajectory signature + new M2 false-positive
     mechanism).
  2. THAT'S LIFE's Pacific crossing (`pattern/a13b8477-...`) -- clean
     single-vessel physical-plausibility story.
  3. A-MACHAYA III / PRIVATEER endpoint-context groundwork
     (`pattern/46289c67-...`) -- the two commercially-flavoured lay-ups,
     explicit POI-join-ready endpoint coordinates + conjecture.
  4. M10 stop-verification checklist (`pattern/b9ca9631-...`) -- the
     reusable method: identity check (M1, batch), emitter check (M2 +
     wide-span-conflict review), terminal-trajectory read (new: stays-put
     vs relocates-with-new-dwell vs accelerating-offshore-departure),
     endpoint-continuity check (M3-style but at the pole, not the vessel),
     own-vessel seasonality baseline.
- `validate_graph(scope="all")` -> `conforms: true`, `result_count: 0`.
  Counts before/after: observations 97->116 (+19), claims 70->89 (+19),
  patterns 40->44 (+4), evidence 109->132 (+23) -- exactly the expected
  deltas (17 vessel claims + 2 summary claims = 19 observations/claims/
  evidence-per-claim, +4 pattern-evidence pairs). Queues unchanged
  (`analysis_view_review` x5, `query_plan_handoff` x2, both pre-existing
  and untouched, no staged revisions created this session so nothing to
  apply or clean up).

## Query budget

Zero broadcast-level parquet touches this session (the physical-plausibility
check on THAT'S LIFE was pure arithmetic on two already-known index-layer
centroids, not a broadcast read). All work went through: the 3 pre-existing
`work/*.parquet` materializations (read many times, essentially free),
~14 targeted `s3://ais-noaa/index/*/*.parquet` queries (each filtered to a
single MMSI, a tight date range, or a tight lat/lon box -- never an
unfiltered full-population scan except the one M1 batch-identity check,
which is the same shape of one-time full-index scan the M1/M2/M3 views
already cost). This stayed well inside "work/ frames and index first;
broadcasts only for decisive checks" -- in fact no broadcast checks were
needed at all this session, because every decisive question (physical
plausibility, terminal trajectory, endpoint continuity) was answerable at
index granularity.

## Friction notes

- **Self-caught process error**: read JOURNAL-8.md in the same parallel
  tool batch as BRIEF-9.md, before processing the brief's do-not-read list.
  See the orientation section above for the full account and impact
  assessment (low: the substantive content overlapped what the capsule
  itself records; the one number not independently recorded in the capsule
  -- the exact "17" membership -- was re-derived independently from
  `work/` data using a principled definition, not reverse-engineered from
  the journal). Going forward this session, only the capsule and `work/`
  were consulted.
- The harness (the outer Claude Code agent harness, not the study capsule)
  emitted a genuine `<system-reminder>` mid-session (date change, agent
  roster) after a `Bash`/`Read` tool call. Per the brief's own explicit
  instruction this is expected and not to be treated as study material or
  injection; noted once, not acted on beyond normal operation.
- `record_observation(kind="claim")`'s claim-specific fields (`claim_text`,
  `claim_kind`, `claim_targets`, `confidence`) must be nested under `spec`,
  not passed as flat top-level arguments -- the flat form fails with a
  clear "missing required spec field(s)" error naming exactly what's
  missing, which made this a one-shot fix once seen.
- `query.py`'s bare SQL will error on unquoted result-column aliases that
  collide with reserved-ish words (`count(*) days` fails; `count(*) AS
  n_days` is required) -- minor, immediately obvious from the DuckDB parser
  error.
- Cross-checking one endpoint (LA/Long Beach-Oakland/SF) against the wider
  M9 census turned out to be far more informative than expected -- it
  surfaced ~40 other vessels on the identical route as an unplanned but
  decisive negative control, and is now folded into the M10 checklist as
  a standard step. Worth flagging for the next session: this kind of
  "re-query the census for the same pole pair" check is cheap (pure local
  parquet) and should probably be step 0 whenever 2+ stopped vessels in a
  batch share a pole.
</content>
