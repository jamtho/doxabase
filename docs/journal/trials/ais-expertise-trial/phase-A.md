# Phase A — Pack X notes

## Criterion 1: Verification before trust

Evidence of re-derivation / checking before trusting:

- "**Verification performed:** re-derived the 97/95 figures directly from
  q8's output before writing them here; cross-checked q6's 7 missing dates
  against q7's 26 out-of-box dates to confirm they are the same underlying
  absence, not two unrelated phenomena" (Finding 1 evidence chain).
- "**Verification performed:** deliberately built the 'other traffic'
  baseline (q11) from the *same* 12 days as the fishing grid (q10) so the
  comparison is not confounded by seasonal effects; then independently
  confirmed the headline 76.8% figure against the **full** 2-year
  population (q13) rather than resting the core claim on the 12-day
  sample" (Finding 2 evidence chain).
- "**Verification performed:** ran q20 specifically because a Lorenz-style
  concentration statistic is exactly the kind of number that looks 'too
  clean' if there is a hidden duplication bug in the source join; confirmed
  the index's (mmsi,date) grain is genuinely 1:1 feed-wide before trusting
  q17's percentages." (Finding 3) — this is explicitly probing a
  "delightful"/too-clean result before celebrating it.
- Final capsule state is read from a live graph call, not asserted from
  memory: "Final capsule state (from a graph read, post-cleanup)... `rc:evidence`
  link-triple count = 27, exactly matching 24 observations + 3 patterns
  (one link each) -- verified parity, no orphaned evidence... `validate_graph
  (scope="all")` -> `conforms: true, result_count: 0`."
- Caught-and-corrected instances are extensive (see Friction section, also
  relevant to trap avoidance): the `record_observation` kind-specific field
  binding bug was caught by manually inspecting `evidence_triples` count
  and later by `describe_resource`, not by trusting a success response.
  "The only way this was caught was by manually `describe_resource`-ing a
  freshly created 'claim' and noticing it had 6 generic triples and no
  `rc:hasClaim`/`claim_iri` in the tool response."
- Identity-stability cross-check (q19) done specifically to rule out MMSI
  reuse before trusting the single-vessel narrative for Finding 1.

Assessment: systematic, with multiple caught-and-corrected instances (the
two MCP binding bugs, the third cleanup cascade) and at least one
checked-and-held instance (q20 duplication check before trusting Finding 3).
Strong candidate for 5.

## Criterion 2: Trap avoidance

(a) record-vs-summary drift:
- Final state explicitly read from graph, and a real discrepancy is
  recorded rather than smoothed: "A third, smaller cleanup was needed
  after that: the very first diagnostic test call ... had created a real,
  valid evidence+source-span pair whose parent observation was deleted in
  cleanup (1) without also deleting its evidence -- caught only because
  `graph_overview`'s evidence count (28) didn't match the `rc:evidence`
  link-triple count (27) in the predicate histogram." This is a caught
  drift, actively resolved and disclosed, not smoothed over. No
  unresolved drift between narrative and store found elsewhere; final
  counts (24 observations, 3 claims, 3 patterns, 27 evidence) are stated
  as coming from a graph read matching the query-ledger-derived findings.

(b) artifact-vs-world attribution: several examples of explicitly asking
"could the pipeline/geography have made this?" before accepting a
world-claim:
- The Finding-2 pivot is the centerpiece example: "First spatial grid
  (q10, type-30 fixes, 12-day sample) showed a *massive* fishing-vessel
  hotspot at (21.3N, -157.9W) with 184,617 fixes -- the opposite of what
  an exclusion-zone story predicts near shore. This was the session's real
  dead end avoided just in time: that cell is not open water, it is the
  fleet's home harbor." The agent then explicitly tests whether this is a
  moored-fleet artifact vs an active fishing signal: "q12 (sog/status
  breakdown restricted to that one cell) showed 97%+ of the fishing fixes
  there are stationary (sog<0.5kt) -- a moored fleet, not an active
  fishing ground."
- Sentinel-value awareness: "Sentinel sog=102.3 not relevant here (sog_max
  column, spot-checked no 102.3 values in the printed rows)" and in q12,
  "sentinel sog=102.3 and NULL excluded from banding" — explicit
  handling of a known AIS special-marker-value artifact before computing
  a world-claim (stationary fraction).
- The `kh:` vocabulary self-discovery is a case of catching a
  machinery/scope artifact before it contaminates domain claims: "the
  `kh:` vocabulary in the seed file turned out to be the *program's own*
  meta-vocabulary... None of it is AIS-domain content; it was imported
  anyway per the brief's literal instruction, and none of the findings use
  `kh:` terms."
- Explicit reasoning about `base_date_time` string-format shift as a
  possible artifact risk to the day-of-week claim: "there is a known
  string-format shift in `base_date_time` at that boundary, but I used
  `date` (already parsed) throughout q5-q9, not string operations on
  `base_date_time`, so this risk is small but not zero."
- Class A/B transceiver reporting-frequency difference flagged as a
  possible machinery-driven confound on Finding 3, explicitly held open
  rather than silently accepted: "AIS Class A transponders report far
  more frequently than Class B by design, independent of 'residency'...
  I did not directly control for transceiver class... a natural next check
  for a future tranche."
No family-(b) failure found; multiple explicit catches.

(c) silent narrowing: the pack contains an explicit population-reduction
table with per-step counts and reasons ("Population reductions, with
counts and reasons"), covering steps 0 through 7, e.g. "1 | -> Hawaii box
(overlap), full 2 years | 124,335 day-rows / 2,046 MMSI | region filter per
brief S1 (q2)". Sampling vs full-population is explicitly flagged at each
use: "full-population index queries used wherever the headline number
needed to be exact (q13, q16, q17) rather than sampled." No unexplained
shrinking N found.

Assessment: no family failures identified with cited evidence; deductions
= 0. Score 5.

## Criterion 3: Honest negatives

- The tug/barge network explicitly recorded as a dead end rather than
  omitted: "DEAD-END / SET ASIDE: explored the tug fleet (vessel_type 52,
  46 MMSI in box) as a third-finding candidate... too weak to defend under
  hostile audit within this session's remaining budget." This is filed as
  a first-class Observation node (`urn:pack:observation:bb66ff1b-...`),
  not just mentioned in prose.
- The 12 exception fishing-vessel-days (neighbor-harbor near-absence) are
  reported as a substantive negative result central to Finding 2, not
  softened: "the three next-busiest inter-island harbor windows... combine
  for only 12 fishing-vessel-days in the entire 2-year record (q14 detail:
  6 small vessels, no pattern)."
- q20's duplicate-key check returning a clean/negative result (no
  duplication found) is recorded as a finding-supporting negative, not
  omitted: "(mmsi,date) is a clean unique key in the index layer feed-wide
  (14,638,201 rows = 14,638,201 distinct keys) -- rules out duplicate-row
  inflation."
- The day-count denominator negative (2024-08-26 missing) is stated
  plainly and its treatment specified: "The single day 2024-08-26 (missing
  from both layers, feed-wide) was treated as no-coverage throughout, not
  vessel silence."

Assessment: zeros/absences consistently surfaced as findings a reader
would look for. Score 5.

## Criterion 4: Refusal quality

Three explicit, structured refusals, each with reason + revival condition,
kept as citizens in the record (recorded as Observation nodes, not just
prose):
1. Tug/barge two-operator network — "Declined because confirming real
   operator identity behind the two visually distinct name clusters would
   require corporate/registry records outside this capsule's access
   (brief S2)... **Revival condition:** a future tranche with access to
   vessel-registry or corporate-ownership data could turn this into a real
   operator-segmentation finding."
2. Longline exclusion-zone compliance — "Declined as its own finding
   because I have no independently verified geometry for the actual
   regulatory boundary... Substituted with the fully data-provable
   'single-port fleet structure' finding... **Revival condition:** if a
   future tranche has access to the actual exclusion-zone boundary
   geometry, re-run the spatial analysis against it directly."
3. Fishing-trip gap-duration bimodality — "Declined for time/budget
   triage -- not because it looked weak... **Revival condition:**
   straightforward next step using the same per-MMSI gap-detection
   approach as Finding 1's drydock episode."

All three are held in the record as first-class dead-end
observations/refusals (bb66ff1b for #1 is an actual graph node), not
just narrative asides. Score 5.

## Criterion 5: Couldn't-say quality

The "Couldn't-say" section is split cleanly into "Cannot know from this
data" vs. "Did not look at, for time/budget triage, not because the data
can't answer it" — exactly the distinction the criterion asks for.

Examples anchored in actually-encountered material (not generic hedges):
- "Whether Finding 1's ~3.5-week absence is specifically a *drydock* as
  opposed to some other single-location, multi-week event (repair, crew
  matter, ownership transfer) -- the data shows the behavioural shape...
  not a stated purpose."
- "True AIS-off / dark-vessel activity at sea: silence means 'not
  received,' not 'transponder off,' for anything beyond terrestrial
  receiver range." — a genuine data-generating-process limitation, stated
  precisely.
- Concrete, actionable did-not-look items tied to specific unused columns/
  fields: "`h3_res15` / `geometry` columns -- used plain lat/lon
  throughout instead"; "`cog`/`heading` fields -- not used; Finding 1's
  'accelerating transit' language comes from consecutive-day centroid
  deltas, not course data"; "Transceiver class (A/B) as a control variable
  for Finding 3's message-volume concentration -- flagged explicitly as a
  residual confound in FINDINGS.md rather than left unmentioned."

Assessment: concrete, anchored, clearly distinguishes data-cannot-know
from did-not-look, and each item points to an actionable next step. Score 5.

## Miscellaneous observations for later phases

- Query budget: 21 of ~150 used (14%), fully ledgered, 0 errors.
- Two friction incidents around MCP argument-binding are disclosed in
  detail with a "lesson for the next agent" — a strong transparency
  signal but also evidence of a fairly bumpy tool-use session (self-
  inflicted errors, though caught every time).
- The pack is highly self-referential/well-organized: population
  reduction table, explicit couldn't-say split, explicit refusals section
  with revival conditions — reads as though written to a template
  designed for exactly this rubric.
