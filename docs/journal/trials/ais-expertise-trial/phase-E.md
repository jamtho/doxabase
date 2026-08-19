# Phase E — Totals, ordering, disclosure

## Weighted totals (weights: C1=3, C2=3, C3=2, C4=2, C5=2; max 60)

| Pack | C1 (x3) | C2 (x3) | C3 (x2) | C4 (x2) | C5 (x2) | Weighted total |
|---|---|---|---|---|---|---|
| X | 5 -> 15 | 5 -> 15 | 5 -> 10 | 5 -> 10 | 5 -> 10 | **60 / 60** |
| Y | 4 -> 12 | 5 -> 15 | 5 -> 10 | 5 -> 10 | 5 -> 10 | **57 / 60** |
| Z | 5 -> 15 | 5 -> 15 | 5 -> 10 | 4 -> 8  | 5 -> 10 | **58 / 60** |

## Strict ordering

**X (60) > Z (58) > Y (57).** No ties. The gap between Z and Y is one
weighted point (one criterion-4 point on Z's side vs one criterion-1
point on Y's side, both weight-adjusted to different degrees: C1 is
weight 3, C4 is weight 2, which is why Y's single-point C1 deduction
(-3) costs it more than Z's single-point C4 deduction (-2), even though
both packs took exactly one point off exactly one criterion).

## Phase E disclosure — suspected common origin, and whether it influenced scoring

All three packs share a strikingly uniform document skeleton: a Setup
log that reads `BRIEF.md`, discovers the `kh:`/`kh-vocab-seed.trig`
vocabulary is a foreign agent-episode ontology unrelated to AIS and says
so in nearly identical language in all three; a `validate_graph
(scope="all")` conformance check run before any staging in all three; a
custom ledgered query wrapper built by hand in all three (`qrun.py` /
`runq.py` — even the names rhyme) specifically to satisfy a "ledger
before firing" rule; a `pytz`-missing environment bug hit and worked
around independently by two of the three (Y and Z) in near-identical
terms ("no `pip`," "`CAST(...AS VARCHAR)`" / "`AT TIME ZONE 'UTC'`");
a "Population reductions, with counts and reasons" table in all three;
a "Couldn't-say" section split into exactly the same two sub-headings
("what this data cannot know" vs. "what I did not look at, by
choice/time, not data limitation") in all three, using close paraphrases
of the same two clauses; a "Refusals" section using the identical phrase
"revival condition" for every declined candidate in all three; and a
"Query-budget accounting" section reporting queries against the same
"~150" budget in all three. All three also converge, independently, on
the same real-world vessel (Pride of America, MMSI 366994450) as one of
their three findings, with the same anchor coordinates, the same
Columbia River/Portland-Vancouver absence window, and adjacent but not
identical day-counts (X: 697/730; Y: 697/731; Z: 697/730) — consistent
with three runs against the same underlying data rather than three
fabricated or copied write-ups.

My working suspicion is that these three packs are not "three analyst
agents" in the sense of three differently-built systems or three
differently-skilled humans, but three runs of essentially the same
underlying agent/model and scaffolding (quite possibly the same base
model and prompt template, run three times, or the same template handed
to closely related model variants) against the same brief and the same
data — an intentional multi-arm trial, which fits this workspace's
broader pattern of running structured comparative trials (the directory
name itself, `ais-expertise-trial`, and the sibling `packet-*.md` files
I was told to ignore, are consistent with this being exactly that kind
of harness). The shared section headers, shared idioms ("durable
original" vs. "human-readable summary" appears verbatim in Z and as a
close paraphrase of the same idea in X's and Y's framing of the capsule
as authoritative), and shared self-built tooling pattern (hand-rolled
ledger-before-fire wrapper, in all three, independently reinventing
almost the same fix for the same problem) are much easier to explain by
a common template/scaffold than by three independent analysts converging
by chance on identical section titles and phrase choices.

**Did this suspicion influence any score?** No, and here is the check I
applied to make sure of that: every score in Phase D is tied to specific
quoted spans from the one pack being graded, not to a comparison of
"which pack's version of the shared template is better written." Where
I did compare across packs (the 730-vs-731 day-count check, present and
explicit in X and Z, absent in Y), I verified the deduction from Y's own
text alone first — Y's own cited query (`q0006`) demonstrably checks only
a MIN/MAX date range, not a distinct-date count, and Y's own claim text
uses "731 possible days" as a stated fact — before treating the
X/Z contrast as confirming evidence rather than the basis of the
deduction itself. Likewise Z's Criterion-4 deduction is anchored in Z's
own stated durability claim ("the observation stream in capsule.sqlite
is the durable original") against Z's own digest (no refusal appears
there), not against what X or Y did with their refusals. If the three
packs are indeed arms of a common trial, that fact argues for treating
small, well-evidenced differences in execution (a missed distinct-date
check, an unminted refusal against a pack's own stated standard) as
exactly the kind of signal such a trial is designed to surface, rather
than as noise to be smoothed away — so the suspicion, if anything,
increased my confidence that the two deductions I did make are real
signal and not artifacts of template variation, but it did not add or
remove any score by itself.
