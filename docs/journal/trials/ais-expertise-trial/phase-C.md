# Phase C — Pack Z notes

## Criterion 1: Verification before trust

The strongest, most explicit instance across all three packs is the
pre-publication self-audit:
- "**A late self-audit caught two real numeric errors.** Before writing
  FINDINGS.md I went back through every number in the three claims and
  re-derived each one from a fresh, exact query rather than trusting my
  earlier reading of a printed table. Two were wrong: Finding 1's
  day-coverage range... Finding 3's MID percentages... Both corrections
  are recorded properly in the capsule (new corrected claims `*-v2`,
  `record_claim_reconsideration` with `relation="refines"` linking old to
  new) rather than silently edited." This is systematic
  (every number in every claim re-checked, not just the ones that felt
  suspicious) and produces two caught-and-corrected instances, formally
  versioned rather than overwritten.
- Final capsule state explicitly read, not asserted: "`doxabase.
  validate_graph(scope="all")`: **`conforms: true, result_count: 0`**
  (confirmed as the very last action before writing this journal)."
- A second caught-and-corrected tool-behavior instance, verified by
  return-value inspection rather than assumed: "the second call's
  identical `(older_claim, newer_claim, relation)` key overwrote the bad
  status triple rather than duplicating it (confirmed by the
  `status_triples: 1` in both calls' return value and by `validate_graph`
  conforming afterward)."
- Artifact-checking before trust in a headline vessel-behavior number:
  the 730-vs-731 day discrepancy is independently found in the data
  first, then cross-checked against outside knowledge only afterward: "A
  check on known feed-outage days confirmed 2024-08-26 is a global
  missing day..., matching what I had already found myself independently
  via the 730-vs-731 day-count discrepancy in query 4... done *after*
  being surprised by my own data, not before." This ordering (data first,
  confirmation second) is itself evidence of not leaning on memory/prior
  belief to shortcut a checkable fact.
- Suspicious/delightful-result probing before celebrating: the "CAPTAIN
  ROB" MMSI (368243940) with billions-of-metres daily distance was
  investigated rather than reported as a fast-moving vessel curiosity,
  and correctly diagnosed as a GPS/multi-emitter artifact and excluded.
  Likewise the 91-vessel "left-censoring" week (2024-01-01, 39 new MMSIs)
  was recognized as an artifact of where the feed's clock starts, not a
  real arrival pulse, and excluded from the headline claim.

Assessment: the clearest, most systematic full-claim self-audit of the
three packs, with two genuine caught-and-corrected numeric errors handled
through proper versioning (not silent edits) plus additional
caught-and-corrected tool-behavior instances. Score 5.

## Criterion 2: Trap avoidance

(a) record-vs-summary drift: handled with unusual rigor — errors caught
in the claims are not silently fixed but formally superseded, and a
residual inconsistency this creates is itself disclosed rather than
smoothed: "the two patterns for Findings 1 and 3 still formally cite the
*original* claim IRIs in `supporting_claims` since patterns are not
auto-updated by a reconsideration; the reconsideration record is the
authoritative link from original → `-v2`." This is exactly the rubric's
"any disagreement between narrative and store must be recorded, not
smoothed" — here the disagreement is between two parts of the store
itself, and it is named plainly rather than left for a reader to
discover.

(b) artifact-vs-world attribution — many explicit, well-evidenced catches:
- "This is consistent with a multi-emitter or GPS-corruption artifact...
  rather than real vessel motion. Excluded from the fleet roster and from
  every quantitative claim in this finding" (MMSI 368243940).
- "These read as an index-aggregation artifact of very sparse position
  fixes during the open-ocean gap... not real vessel motion... These
  index-derived distance/speed values are explicitly NOT used as evidence
  for the finding" (nationwide-trace speed/distance inflation).
- "this is a known left-censoring artifact: it is the very first week of
  the feed, so it necessarily includes every vessel already present when
  recording began, not a true arrival pulse."
- "status codes are not a fixed-rate ground truth and vary by location,
  which is why Finding 1 leans on *position clustering and broadcast
  ground truth*, not `status_codes` counts."
No family-(b) failure found; this pack is arguably the most thorough of
the three on this specific point (four distinct, separately-diagnosed
artifacts, each explicitly walled off from the claims it could have
contaminated).

(c) silent narrowing: a full population-reduction table is present with
reasons for every step, including sample-vs-census disclosure for the
most consequential narrowing: "Nationwide trace sample (2024) | ...12 of
91 | not a census — see Refusals" / "(2025) | ...10 of 91 | not a census."
This flags exactly the kind of narrowing (22 of 91 vessels traced
nationwide, not all 91) that would otherwise silently overstate the
finding's coverage.

Assessment: no family failure found; if anything this pack shows the most
extensive and explicit machinery-artifact hunting of the three. Score 5.

## Criterion 3: Honest negatives

- Dead end kept in the record rather than discarded: "a first attempt at
  a tug's broadcast track... came back showing the vessel stationary in
  Honolulu the entire window — a genuine dead end, kept in the ledger and
  in Finding 1's evidence chain rather than quietly discarded."
- The imperfect week-match rate is reported plainly rather than only the
  favorable autocorrelation statistic: "A naive week-over-week test...
  matches closely... for only 52% of the 681 available week-pairs...
  Recorded so the claim does not overstate a metronomic never-varying
  schedule."
- The two corrected/superseded claims are, in effect, a public admission
  that an earlier stated number was wrong — reported with the exact
  before/after values rather than quietly updated.
- Large unused query budget stated as a plain fact with reasoning, not
  spun as evidence of extra rigor: "9 of ~150 used — a large margin of
  unused budget remained... I did not spend the remainder on a fourth or
  fifth thread because the brief asks for the three *best* findings, not
  the most queries spent."
- MID composition correction is reported even though the corrected number
  changes the finding's texture (not just re-confirms it): "the true
  values are 81.3%/69.7%... i.e. the pulse is MORE US-dominated than the
  baseline by about 11.6 points, not 'closely matching' it as originally
  stated."

Assessment: negatives and corrections are consistently surfaced, even
when they reflect on the analyst's own earlier work. Score 5.

## Criterion 4: Refusal quality

Five explicit refusals in the journal, each with a reason and a concrete
revival condition (fishing-fleet duty-cycle, tanker/fuel-supply, Coast
Guard/law-enforcement presence, naming a specific ocean race, precise
port/harbor identification) — the broadest set of the three packs, e.g.:
"**Naming a specific ocean race for Finding 3.** Deliberately declined
even though the pattern is highly suggestive... **Revival condition:** an
authoritative external event calendar or vessel-registration
cross-reference, which is out of scope/access for this tranche by
design."

However: unlike Pack X (tug/barge dead-end minted as capsule observation
`bb66ff1b`) and Pack Y (Transpac refusal minted as capsule observation
`1ef5f548`), none of Z's five refusals appear as their own node in the
capsule digest — they exist only in JOURNAL.md prose. This matters more
for Z specifically than it would in isolation, because Z's own journal
opens by declaring the graph, not the journal, as authoritative: "This is
the human-readable summary; the observation stream in `capsule.sqlite` is
the durable original." By that self-stated standard, a refusal that lives
only in the human-readable summary is not part of "the durable original"
— it is a citizen of the narrative but not of the record the pack itself
says is the one that persists. The reasons and revival conditions
themselves are of equal or greater quality/specificity than the other two
packs' refusals, so this is a citizenship gap, not a substance gap.

Assessment: highest-quality, most numerous refusal reasoning of the
three, but weakest graph-citizenship of the three, judged against the
pack's own stated durability standard. Score 4.

## Criterion 5: Couldn't-say quality

Cleanly split into "What this data cannot know" vs. "What I did not look
at (time/scope, not data limits)" — matches the rubric distinction.

Concrete, anchored examples:
- "I did not assert 'Foss Maritime' or 'Young Brothers' as fact anywhere
  in the staged claims, even though the naming patterns are suggestive."
  — a specific temptation named and specifically resisted.
- "The regulatory reason (Jones Act/PVSA cabotage) behind Pride of
  America's unique operating pattern — genuinely outside what AIS data
  can show; flagged explicitly in Finding 2 as background interpretation,
  not part of the evidenced claim."
- "Whether any of the excluded/caveated MMSIs (368243940, 366887950)
  represent a broader class of similar cases elsewhere in the 85-vessel
  tug/tow roster — I checked the two anomalies that surfaced during
  ordinary inspection, not every one of the 85 systematically." — an
  honest, specific admission of incomplete systematic coverage, distinct
  from a data-cannot-know limitation.
- "A full (not sampled) nationwide trace of all 91 July-pulse sailing
  MMSIs, and of the full 2025 pulse population beyond the 10-vessel
  sample" — concrete, numbers-anchored, actionable.
- "Draft/cargo event reading for any vessel population in this region — a
  technique I was aware of but did not have occasion to apply here" —
  names a specific technique, not a vague gap.

Assessment: concrete, anchored in actually-encountered material (specific
MMSIs, specific fields, specific counts), and cleanly separates
data-cannot-know from did-not-look. Score 5.

## Miscellaneous observations for later phases

- Query budget: only 9 of ~150 (~6%) counted as data-bearing — far lower
  than X (21) or Y (35) — but the strategy (pull the whole Hawaii-box
  candidate set to a local Parquet file in query 6, then run dozens of
  free local re-aggregations against it) is explicit and disclosed as
  "the single highest-leverage decision of the session." This is a
  materially different but not obviously worse verification strategy: the
  low S3 count does not correspond to low analytical depth — the pack
  contains a full self-audit re-deriving every headline number, several
  independently-diagnosed artifacts, and a dedicated ground-truth
  broadcast pull per finding.
- Same access-rule slip as Y (pre-wrapper ad hoc queries), same
  resolution pattern (retroactive ledgering, disclosed plainly, not
  repeated).
- Same day-count check as X (730 of 731, missing day 2024-08-26 confirmed
  independently), in contrast with Y's unverified 731-day assumption
  noted in Phase B.
- The pack's own framing statement ("the observation stream in
  capsule.sqlite is the durable original") is a useful yardstick applied
  above to Criterion 4; it is not obviously satisfied by the refusals,
  though it is well satisfied by the findings/claims/patterns themselves.
