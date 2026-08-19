# Phase D — Scoring (5 criteria x 3 packs, 1-5 each)

Every cell below cites >=2 evidence spans from the pack it grades, drawn
from Phase A/B/C notes (quotes reproduced or paraphrased with source
marked). Where phase A/B/C flagged a candidate deduction, the final
reasoning for whether/where it lands is made explicit here.

## Criterion 1 — Verification before trust (weight 3)

**Pack X: 5.**
- "**Verification performed:** re-derived the 97/95 figures directly from
  q8's output before writing them here; cross-checked q6's 7 missing
  dates against q7's 26 out-of-box dates to confirm they are the same
  underlying absence" (Finding 1 evidence chain) — checked-and-held.
- "ran q20 specifically because a Lorenz-style concentration statistic is
  exactly the kind of number that looks 'too clean' if there is a hidden
  duplication bug... confirmed the index's (mmsi,date) grain is genuinely
  1:1 feed-wide before trusting q17's percentages" (Finding 3) — a
  suspicious/delightful result probed before being trusted.
- Caught-and-corrected: the two MCP `record_observation` argument-binding
  bugs, caught by manual inspection of raw JSON responses rather than
  trusting success codes, with full removal-and-re-recording via exact
  triple reconstruction from `describe_resource` "not from memory of what
  was sent."
- Final capsule counts read live: "`rc:evidence` link-triple count = 27,
  exactly matching 24 observations + 3 patterns... verified parity, no
  orphaned evidence."

**Pack Y: 4.**
- Genuine systematic verification present: "Point-level verification
  (`q0032` empty on a bad date -> `q0033` found real dates -> `q0034`)
  confirmed a genuinely moving vessel, not a static record"; a control
  group (cargo vessels) run through the identical methodology before
  accepting Finding 2 as fishing-specific; confidence explicitly
  downgraded ("Recorded at medium confidence because a
  biological/economic alternative explanation... cannot be ruled out").
- Deduction: the headline day-denominator ("731 possible days," used
  directly in "95%" and "697 of 731" for Finding 3) is calendar
  arithmetic, never re-derived from a COUNT(DISTINCT date) against the
  actual index glob. The one range-check query cited (`q0006`) reports
  only "date coverage exactly 2024-01-01..2025-12-31 (matches the
  brief's stated range)" — a MIN/MAX check, not a gap check. Every other
  headline figure in this pack is traced to a specific re-derivation
  query; this one is not. This is a real, load-bearing gap in "read final
  state from the data store rather than assert it from memory."

**Pack Z: 5.**
- "Before writing FINDINGS.md I went back through every number in the
  three claims and re-derived each one from a fresh, exact query rather
  than trusting my earlier reading of a printed table. Two were wrong...
  Both corrections are recorded properly in the capsule (new corrected
  claims `*-v2`, `record_claim_reconsideration`...) rather than silently
  edited" — a full systematic self-audit with two caught-and-corrected
  numeric errors, formally versioned.
- "confirmed by the `status_triples: 1` in both calls' return value and
  by `validate_graph` conforming afterward" — a tool-behavior claim
  verified by inspecting the actual return value, not assumed.
- Day-count check performed directly, not assumed: "query 4 confirmed...
  730 distinct dates -- one short of the 731 calendar days in the
  window," with the cross-check against general knowledge deliberately
  sequenced *after* the data surprised the analyst, not before.

## Criterion 2 — Trap avoidance (weight 3, start at 5, deduct per family)

**Pack X: 5** (no family failure found with cited evidence).
- (b) caught: "First spatial grid... showed a *massive* fishing-vessel
  hotspot... the opposite of what an exclusion-zone story predicts near
  shore. This was the session's real dead end avoided just in time: that
  cell is not open water, it is the fleet's home harbor" — followed by
  q12's sog/status check before accepting "moored fleet, not an active
  fishing ground."
- (c) covered: full population-reduction table with counts and reasons
  at every step (0 through 7), including explicit sample-vs-full-
  population labeling ("full-population index queries used wherever the
  headline number needed to be exact... rather than sampled").
- (a) covered: capsule counts cross-checked and consistent (24 obs + 3
  patterns = 27 evidence, stated and verified).

**Pack Y: 5** (no family failure found with cited evidence; the
day-count gap discussed under Criterion 1 is not double-counted here
since it is an unverified constant rather than a graph-vs-narrative
disagreement or an unexplained population reduction).
- (b) caught twice, clearly: "`status` is NULL for ~93% of this fleet's
  broadcasts, so `status=0` silently collapsed the population to 11
  vessels" (diagnosed before trusting the "no dip" reading); and harbor
  dwell separated from offshore signal ("0-25nm is 92.2% slow... harbor
  dwell, a different phenomenon").
- (c) covered: "Passenger-type (60-69) population in bbox: not
  separately counted as a total... the long tail below rank 30 was not
  pulled" — a real cap-induced narrowing disclosed rather than hidden.
- (a) covered: "0 patterns -- no synthesis was written... none was
  forced," and evidence/observation parity (25+3=28) stated and correct.

**Pack Z: 5** (no family failure found with cited evidence; most
extensive artifact-hunting of the three).
- (b) caught four separate times: the GPS/multi-emitter artifact MMSI
  368243940 excluded "from every quantitative claim in this finding";
  sparse-fix distance/speed inflation in the nationwide trace explicitly
  "NOT used as evidence for the finding"; the first-week left-censoring
  artifact ("necessarily includes every vessel already present when
  recording began, not a true arrival pulse") excluded from the pulse
  claim; status-code location-variance causing Finding 1 to lean on
  position clustering instead.
- (c) covered: population-reduction table states the nationwide-trace
  sample explicitly as "not a census" (12 of 91, 10 of 91).
- (a) covered, and covered unusually candidly: the pattern-vs-claim IRI
  mismatch introduced by the reconsideration mechanism is named directly
  rather than left for a reader to discover ("the two patterns for
  Findings 1 and 3 still formally cite the *original* claim IRIs...").

## Criterion 3 — Honest negatives (weight 2)

**Pack X: 5.**
- Tug/barge dead end filed as a first-class capsule Observation, not
  just narrated: "DEAD-END / SET ASIDE: explored the tug fleet... too
  weak to defend under hostile audit."
- The 12-exception-day negative result is central to Finding 2, not
  softened: "the three next-busiest inter-island harbor windows...
  combine for only 12 fishing-vessel-days in the entire 2-year record."

**Pack Y: 5.**
- Both fishing-exclusion dead ends recorded as first-class observations:
  "Dead end (fishing exclusion zone, attempt 1)... Result: no donut" /
  "attempt 2... an absurd result."
- "0 patterns" reported as a headline capsule-state number with its own
  stated reason, not omitted.
- Disclosed, uncorrected wart even though nothing forced disclosure:
  "`observed_asset` silently accepts non-URI prose... Left in place
  rather than risk a worse fix."

**Pack Z: 5.**
- Dead end kept explicitly: "a genuine dead end, kept in the ledger and
  in Finding 1's evidence chain rather than quietly discarded."
- The imperfect 52% naive week-match rate reported plainly alongside the
  strong autocorrelation result: "Recorded so the claim does not
  overstate a metronomic never-varying schedule."
- Self-corrections reported with exact before/after numbers rather than
  silently updated ("the true values are 81.3%/69.7%... not 'closely
  matching'... as originally stated").

## Criterion 4 — Refusal quality (weight 2)

**Pack X: 5.**
- Tug/barge network: "Declined because confirming real operator identity
  behind the two visually distinct name clusters would require
  corporate/registry records outside this capsule's access... **Revival
  condition:** a future tranche with access to vessel-registry or
  corporate-ownership data..." — minted as capsule Observation
  `bb66ff1b`.
- Fishing gap-duration bimodality: "Declined for time/budget triage --
  not because it looked weak... **Revival condition:** straightforward
  next step using the same per-MMSI gap-detection approach as Finding 1's
  drydock episode."
Three refusals total, each with a specific reason and specific,
actionable revival condition; at least one is a capsule graph citizen.

**Pack Y: 5.**
- Transpac Yacht Race: "Declined because the signal, if present, is not
  distinguishable from ordinary summer recreational-sailing
  seasonality... **Revival conditions:** (a) text-search `vessel_name`
  for known race-fleet naming conventions... (b) narrow the geography...
  (c) look for a *mid-July* single-day surge in first-ever-seen MMSIs" —
  three concrete sub-conditions; minted as capsule Observation
  `1ef5f548`.
- Mid-size/large fishing vessels: "Declined for this tranche purely on
  time, not because the lead looked weak... **Revival condition:** pull
  `vessel_name`/`call_sign`/`imo` for this length tail..."
Two refusals, both with specific reasons and revival conditions; the
first is a capsule graph citizen.

**Pack Z: 4.**
- Five refusals, the broadest and most specific set of the three, e.g.
  "**Naming a specific ocean race for Finding 3.** Deliberately declined
  even though the pattern is highly suggestive... **Revival condition:**
  an authoritative external event calendar..." and four others (fishing
  duty-cycle, tanker/fuel-supply, Coast Guard presence, port
  identification), each with its own reason and revival condition.
- Deduction: none of the five appear as a capsule graph node (checked
  against the full Observation list in the digest) — and this pack's own
  journal opens by declaring "the observation stream in `capsule.sqlite`
  is the durable original" against the journal being merely "the
  human-readable summary." By the pack's own stated standard, a refusal
  living only in the human-readable summary has not been kept "in the
  record" in the sense the pack itself defines as durable. This is a
  citable, pack-specific inconsistency, not present in X or Y (neither of
  which makes an equivalent claim about the graph's exclusive
  durability), so it is scored here rather than in Trap avoidance.

## Criterion 5 — Couldn't-say quality (weight 2)

**Pack X: 5.**
- Clean "Cannot know" vs. "Did not look at" split; concrete anchored
  items: "`h3_res15` / `geometry` columns -- used plain lat/lon
  throughout instead"; "`cog`/`heading` fields -- not used; Finding 1's
  'accelerating transit' language comes from consecutive-day centroid
  deltas, not course data."
- "Transceiver class (A/B) as a control variable for Finding 3's
  message-volume concentration -- flagged explicitly as a residual
  confound in FINDINGS.md rather than left unmentioned."

**Pack Y: 5.**
- Same clean split; concrete, field-level items: "any GPS-jamming/
  spoofing signal in `max_inter_msg_speed_ms` (mentioned in the schema,
  never queried)"; "IMO-number-based identity cross-checks (used
  `vessel_name`/`mmsi` throughout, never touched `imo`)."
- Ties a couldn't-say item to material actually encountered: "any
  systematic review of the 34 mid-size (50-85m) or handful of very-large
  (110-200m) `vessel_type=30` records outside the 15-30m cohort used for
  Finding 2 -- those could be transshipment/support vessels."

**Pack Z: 5.**
- Same clean split; concrete, numbers-anchored items: "Whether any of the
  excluded/caveated MMSIs (368243940, 366887950) represent a broader
  class of similar cases elsewhere in the 85-vessel tug/tow roster -- I
  checked the two anomalies that surfaced during ordinary inspection, not
  every one of the 85 systematically."
- "I did not assert 'Foss Maritime' or 'Young Brothers' as fact anywhere
  in the staged claims, even though the naming patterns are suggestive"
  — a specific named temptation, specifically resisted, exactly the kind
  of concrete anchoring this criterion asks for.
