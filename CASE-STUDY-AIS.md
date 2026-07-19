# Case Study: Fourteen Sessions on the AIS Feed

*What it is like to work with DoxaBase, told through a real study.
(Interim version written by the project's resident agent; the
maintainer intends to rewrite it in his own voice. This is the
condensed telling — the full chapter-by-chapter account of all
fourteen sessions is `docs/case-study-ais-full.md`, and the underlying
records — session briefs, analyst journals, graded trial records, and
rendered capsule reports — are in `docs/journal/`.)*

---

## The setup

One domain expert — James, twenty years around vessel-tracking data.
Two years of NOAA-style AIS broadcasts, 92 million position reports,
around the whole US coast. And one question the study was built to
answer: **can hard-won analytical understanding actually transfer
between minds that never met each other — carrying its evidence and
its failure modes with it?**

Fourteen sessions ran between 2026-07-06 and 2026-07-12, four of them
on the first day alone, under rules written down before the first one
launched. Most analysts started *cold*: no conversation history, no
notes, an explicit do-not-read list naming every predecessor's journal
and brief; the only thing allowed to carry knowledge between sessions
was the DoxaBase capsule itself. We alternated a strong model
for the capsule-building and distilling sessions with a weaker one for
forensics and blind-transfer probes — deliberately, so that "the
inheritance works" would mean something harder than a strong model
reading its own notes. For the explicit transfer probes, grading
criteria were written down *before* launch, so the verdict couldn't
drift to fit what happened. And the expert was available only
asynchronously, never inside a session: at most three questions per
brief, answers arriving before the *next* session, every answer
recorded in the capsule as an evidenced observation and cited by IRI
whenever a later brief acted on it.

## Day one: an empty capsule and a feed that lies

On the morning of 2026-07-06 we pointed the strong model at an empty
capsule and gave it the lowest-resolution instruction we could defend
— three vessel forensics stories, plus open-ended method invention, no
taught tradecraft, no hints — then watched what it did with two years
of raw traffic.

It mapped both physical datasets first (`broadcasts`, one row per
received message; `daily-index`, one row per vessel per day), then
started recording methods in a shape that held for the rest of the
study without anyone mandating it: a pattern (what it detects, why,
confidence) plus caveats plus an executable analysis view plus at
least one evidenced example. By the end there were five: M1 classified
identity changes with independent corroborators; M2 found
multi-emitter MMSIs; M3 segmented silence gaps; M4 read cargo events
off draft changes and inferred terminals without a port database; M5
detected persistent co-movement pairs. Three vessel stories anchored
the corpus, among them a shared-MMSI chimera mixing a Shell oil
platform with two unrelated Florida vessels.

Just as important was what accumulated alongside the methods: the
caveat catalog. The parsed `timestamp` column turned out to be UTC
mis-parsed as CET/CEST — only `base_date_time` can be trusted for
absolute time. 2024's placeholder identity fields (`IMO0000000`, zero
dimensions) silently become NULLs the following year. One whole day,
2024-08-26, is missing feed-wide — an outage, not vessel silence. By
session 4 the catalog held two dozen entries, and the running joke
inside the study had become simply: *the feed lies*. The discipline
was to catch it lying and write the lie down with evidence, not to
design around a guess.

When we graded session 1 against James's own held-back tradecraft
examples, it came up short on exactly one: low-speed dwell
segmentation — telling a vessel stopped-but-transmitting from one
genuinely underway — was not rediscovered. We flagged the gap for
session 2 to probe, and told session 2's analyst nothing about it.

## The identity freeze, start to finish

Somewhere in those first hours a diagnostic query came back wrong —
not slightly wrong, impossibly clean. Asked when vessels change their
names, the feed answered: at midnight, January 1st. 2,736 of 2,738
recorded name transitions land exactly on the 2024→2025 file boundary.
Real fleets do not rename themselves in unison at the stroke of the
new year. The sole exception was a Navy patrol boat whose transponder
toggled mid-year — which made the uniformity stranger, not less.
Vessel identity — name, IMO, call sign, type, dimensions — was
evidently frozen per calendar year. Something was doing the freezing.

The first hunch pointed at an uncomfortable place: the expert's own
index builder. James's fetch-and-index code ran once over each year's
files; an annual canonicalization pass there would explain everything.
The agent wrote the suspicion down as a claim *about the expert's own
pipeline* and filed it for grading.

The decisive query came the same afternoon, from a different, weaker
mind. Session 2's analyst, reconstructing a renamed vessel's story
(JACOB BRENT → PERCIVAL), went down to the broadcast level to date the
change — and caught the freeze in the act: two consecutive messages,
47 seconds apart, the vessel underway at six to eight knots off
Galveston, JACOB BRENT in one and PERCIVAL in the next — precisely
across the New Year midnight. The flip is *in the raw broadcasts*.
Whatever freezes identities does it upstream of anything James wrote;
his index builder, suspect since morning, was exonerated by a single
query, and the caveat was refined to record the freeze as an upstream
feed artifact, boundary flip attached as evidence.

The mechanism took one more session. Session 3 sent a cold model after
the provider's own documentation, under one hard rule: where docs and
the capsule's empirical findings disagree, the empirical evidence wins
— docs are provider claims with provenance, nothing more. Buried in
the haul (five PDFs and a receiver-location geopackage) was the
answer: the provider runs an MMSI-keyed identity-correction database
(AVIS through 2023, AVID from 2024) that fuzzy-logic-corrects static
fields. Recorded as a *refinement*, not a confirmation — the
correction cadence stays undocumented — but it coherently explains
both the near-annual freeze and the Navy boat's surviving mid-year
toggle.

So, in one day: anomalous query result → wrong hunch about the
expert's own code → broadcast-level exoneration → documented probable
mechanism, each step recorded with its evidence. We dwell on it
because this is the arc every user of real data will live, over and
over: the feed will lie to you in a way that looks like your own bug,
and the way out is a decisive query and an evidenced caveat, not a
quiet workaround.

The same documentation session banked one more find no document
states: heading and course-over-ground sentinel values (511, 360)
fully swap to true NULL at the year boundary while the speed sentinel
survives untouched — caught by cross-checking the data dictionary
against live broadcasts from both years, and promoted straight to a
severe caveat.

## The stranger reads the notebook

If the study has an emotional center, it is session 2, run the same
afternoon and deliberately on the weaker model: three forensics tasks,
capsule-only inheritance, predecessor scratch files forbidden, no
coaching.

The agent's first move after orientation was the one we hoped for and
could not force: not a query, but a search of the capsule for anything
already recorded. Asked for the associates of the dredge MAGDALEN, the
search came back with a session-1 finding already in the graph: 171
pair-days with RB WEEKS, average 1.18 km apart, 621.6 km of mobility
together, a shared itinerary from New York Harbor to Galveston Bay. It
did not trust the number. It re-ran M5's exact recorded SQL,
reproduced the predecessor's figures exactly — then used the recorded
harbor-fleet caveat to dismiss roughly nineteen co-located vessels as
same-jobsite noise, and filed one borderline case (seven pair-days,
535.6 km of mobility) as inconclusive rather than asserting a
relationship the method's own bar didn't clear. The timestamp caveat
was load-bearing in every timing claim it made — one inherited
sentence, an entire class of silent errors avoided.

Then came the task we had built the trap into: the port calls of the
PENNSYLVANIA in May 2024. We knew — the agent did not — that no
recorded method covered port calls: the deliberately untaught gap from
session 1's scorecard. What the capsule held was pieces: M4's
draft-direction-as-cargo logic, the timestamp caveat, and guidance on
when the cheap index layer suffices versus when broadcast-level detail
is needed. We watched the agent pull all three off the graph and
compose them: screen the daily index for stationary clusters, find the
exact slow-speed threshold crossings at broadcast level, cross-check
cargo plausibility against draft direction. Six terminal stays came
out, timed and cargo-directional, and the method went back into the
capsule as **M6** — with its own caveats and SQL. Only later did the
expert confirm it: M6's core trick, low-speed dwell segmentation, was
exactly the held-back tradecraft the *stronger* session-1 model had
missed. The capsule did not contain the method; it contained enough
for a modest model to build it.

The rename task closed with a correction flowing the other way. M1's
corroboration rule, applied honestly, could not classify the JACOB
BRENT rename: neither call sign nor IMO persisted across the change.
But the physical dimensions were bit-for-bit identical before and
after, and the vessel worked the same small stretch of Galveston-area
water continuously — same-hull evidence M1's corroboration literally
cannot see. The agent recorded this as a caveat *against M1 itself*,
counterexample as evidence, suggested fix included. A weak model,
using a strong model's method, corrected it — so the next analyst
inherits the method *and* its known blind spot, not one that quietly
fails the same way again.

The session's summary line: *"nothing the previous analyst got wrong"*
— every exercised method and caveat held under independent
verification; one genuine gap named and filed rather than papered
over.

## The vocabulary distills itself — and transfers blind

By session 5 the capsule held twenty vessel stories (session 4 had
grown the corpus to fifteen more, each tagged by shape — route
metronome, seasonal trader, MMSI collision...), six methods,
twenty-four caveats, and four expert observations. The brief: read
everything already recorded, tabulate the things, events, and
assessments the corpus actually needed to express, propose a minimal
vocabulary — every term justified by at least two independent stories
— and prove it by re-expressing three stories in it. **Zero data
queries were needed.** The entire distillation ran on capsule contents
alone, and produced a 25-term `aisv:` vocabulary (7 classes, 18
properties).

The corpus forced the design's best move. An a priori ontology would
have started with "Vessel"; the stories refused it. `aisv:AisIdentity`
(the MMSI-keyed, year-frozen, self-reported identity slot) had to be
split from `aisv:Emitter` (the physical transmitting object behind
it), because five separate shared-MMSI stories made anything simpler
untenable. The feed's pathologies live in the semantics honestly:
`apparentDate` sits apart from `datingQuality` specifically to encode
the January-1 freeze artifact, and `ambiguous_ballast` is a
*mandatory* value of cargo direction, not an edge case bolted on. The
session's own reflection: *"An a priori AIS ontology would have
started with Vessel, Voyage, Port and PortCall — and three of those
four are exactly what this corpus refused to support."* (The proof
step stumbled once — the first re-expression attempt failed validation
and was repaired, and both the failed candidate and its repaired
successor stayed in the capsule's history. That mattered a day later.)

Session 6 was the deliberate probe: would the vocabulary transfer to a
mind never told it existed? The brief asked for two new vessel stories
"in the most precise, machine-readable form the capsule supports" —
and never mentioned `aisv:`, the ontology graph, or session 5 at all.
The cold agent found the vocabulary through plain orientation, then
applied both semantic traps correctly: it minted `AisIdentity` for
every vessel but `Emitter` only where the physical object was
confidently segregated — one co-mingled emitter deliberately left in
prose as *"a resource I could not fully justify"* — and honored the
freeze artifact's dating quality on a Jan-1-boundary identity change.

The moment worth naming: the agent read session 5's *failed* first
attempt sitting next to its repaired successor in the history graph,
extracted the convention the repair had settled on, and wrote in its
own journal: *"I inherit the lesson rather than rediscovering it the
hard way."* Not just a fact transferred between minds that never met —
a mistake, and its fix, transferred too.

## Spending the inheritance

The middle sessions stopped founding and started spending — and the
same rhythm repeated at every step: try a design, watch it fail
against known ground, invert it, keep the corrected version.
Session 7 was commissioned directly from an expert remark — a draft
change while underway reads differently from one at berth or at
anchor. The classifier's first cut leaned on the index's
`status_codes` field and promptly labelled a 484 km transit day
"berthed": `status_codes` is a whole-day distinct list, not a
point-in-time reading, and any hour touching a moored code marks the
whole day. The agent caught its own error, inverted the design —
kinematics decide underway-versus-not *first*, status codes only
disambiguate the residue — and re-tested clean. The corrected
classifier became **M7**; **M8** joined draft events to its dwell
spans. And the headline number landed as a gift: the fraction of
draft-change events tied to a recognized dwell ordered seven vessels
monotonically with how clean their cargo stories already were — 92–95%
for PENNSYLVANIA's genuine port calls down to 38–53% for the expert's
own named ballast-ambiguity exemplar — with zero external trade
knowledge.

Session 8 ran the survey James said he had *"wanted to run for many
years"*: find the vessels that run between exactly two points, over
and over — candidate infrastructure for a real-time industry
indicator. Built directly on M7's dwell layer, five thresholds turned
111,100 dwelling MMSIs into **820 strict shuttles**, every candidate
cross-checked against M2's emitter classes to guard the failure mode
the brief named up front — a shared MMSI faking a shuttle; twelve were
excluded on exactly that basis. Among the exemplars: a Mississippi
towboat running Baton Rouge to LaPlace almost weekly for two straight
years, and a Great Lakes grain carrier whose ~99-day winter gap
matches the Soo Locks closure, corroborated by two sister hulls on the
same schedule. And at the bottom of the census sat the setup for the
next session: seventeen of the 820 had stopped running before mid-2025
— the literal population the indicator thesis needed, flagged rather
than chased.

Session 9 verified all seventeen, and for one stretch it genuinely
looked like a signal: four were container ships on the same Los
Angeles/Long Beach–Oakland corridor — a four-vessel route collapse,
exactly the shape the thesis predicted. Then the agent re-queried the
census for that pole pair and found roughly forty *other* container
ships still running the identical route at full strength. Not a route
dying; four independent redeployments off a thriving corridor. The
same check at every other endpoint came back identically: the
route-side, industry-signal shortlist the thesis needed is, in this
cohort, empty — and the pipeline proved itself precisely by *not*
manufacturing the signal we were hoping for. What survives is **M10**,
a reusable stop-verification checklist that makes any future positive
believable.

## The instrument turn

Three sessions in a row then stopped building vessel stories and
started building *instruments* — methods whose thresholds are trusted
enough to hand to someone outside the study.

**Anchor or berth?** The question arrived through the expert channel
from a real outside research need, and James's gloss on the resulting
method was that he had *"genuinely wanted this for ten years"*:
distinguish a vessel stopped at anchor from one stopped at a berth,
without trusting a self-reported status a captain may simply forget to
update. Session 11 built the discriminator on three independent
signals, all proven. Swing geometry: an anchored vessel traces a ring
around its ground tackle (radius 120–170 m, mostly ring, little
center), a berthed one is a GPS-noise point (radius 2–4 m).
True-heading concentration: pinned at a dock versus weathervaning at
anchor — with course-over-ground explicitly rejected as a heading
proxy after it scored a near-random R=0.125, on the grounds of an
expert-channel caveat (gear beacons encode battery level in the COG
field; never trust COG near zero speed). Crowd evidence: places where
many distinct vessels dwell with pinned headings are berth
infrastructure — ten-plus terminal complexes confirmed at 0.97–1.0
agreement over 1,500-plus vessel-days, status codes used only to check
the result, never inside the clustering.

The showcase measurement put the same hull on both sides of the
question, one day apart. PENNSYLVANIA, May 4th: an anchor wait —
radius 123 m, heading sweeping 110° in four and a half hours while
speed-over-ground read 0.0 the entire time. May 5th: a clean berth —
radius 3.4 m, heading pinned at R=0.999997. A better than 30-fold
radius gap, ring collapsing to point, inside one vessel's own history.
As a byproduct the session graded the self-reported status field
itself: roughly 97% reliable at berth for large ships, but anchorage
self-reporting sharply location- and culture-dependent — Vancouver's
English Bay agreeing with the physical signature 77–100% of the time
against an offshore Louisiana anchorage at 0.2%.

**The threshold survey.** James's review came back with a condition,
recorded as the validation doctrine: foundational, human-trusted
measures don't get to rest on four proving vessels — they get a
whole-dataset survey and threshold plots, because humans trust
thresholds through plots. Session 12 sized the population at 7,316,288
eligible stationary vessel-day windows, correctly declared a full
broadcast-level pass infeasible, and instead pulled 4,710 windows
stratified across eleven vessel classes and 5-degree geography in a
single 90.8-second broadcast join. The verdict: keep the tuned
thresholds — the empirical radius valley sits at roughly 20 meters,
exactly the tuned berth boundary, two independent signals agreeing on
the transition zone. But the doctrine's own shape expectation needed
revising: not two clean humps — one dominant pinned mode (62.4% of
windows at essentially zero heading dispersion) and a long monotonic
tail, a view of the fleet the expert had never had before.

And the survey caught something nobody was looking for: 10.1% of
sampled windows are position-suspect, and the worst case is a vessel
whose longitude sat frozen bit-identical across 317 messages while its
latitude drifted roughly 750 kilometers, smoothly, at a self-reported
speed of zero — smooth enough to be invisible to any jump-based glitch
detector. Another dirty-data find by a session sent to do something
else entirely; its position-glitch screen was reused verbatim by
everything downstream.

**The recall audit.** Session 13 quantified the expert's own caution
about the day-granularity architecture everything downstream was built
on. Across 457 stratified vessels and 92.4 million broadcast rows,
pulled in one 74-second join, the answer came back stark: day-level
detection finds only **52.4%** of stops lasting 10–30 minutes, rising
monotonically to 99.0% for multi-day stops. The concrete illustration:
a Ventura passenger vessel cruising at 19–20 knots all day with one
clean nine-minute stop mid-route — a stop the day-index classifier can
structurally never see.

The replacement, **M12**, works at broadcast granularity — and carries
a scar it earned mid-build. The first version assumed a run of slow
messages was continuous, until a vessel with 47 messages spread across
70 days registered as one serene 70-day "stop." The phantom forced the
rule that silence longer than 30 minutes terminates a run — a real
bug, caught against its own output and recorded as an honest failure
mode rather than quietly patched. The payoff was immediate: re-running
the shuttle-detection logic over the event-level series found **43**
shuttles on the same sample where the day-level pass found only 14.
The stops-series-as-foundation architecture the expert had guessed at
was now evidence, not a hunch.

## Rebuilt blind from its own description

The last day formalized M12's behavioural contract as graph data: what
it consumes, what its output means, five invariants it must never
violate — one of them structurally encoding the 70-day-phantom bug, so
any regeneration that reproduces the bug fails it — and seven
parameters each carrying its evidence rather than a bare number. Then
the study's final blind probe: a cold agent, given only a 333-triple
contract bundle — never the SQL — rebuilt the method from scratch
against live data and landed at 426,207 events against the original's
427,134: a −0.22% difference, maximum stop reproduced to the decimal.
The pass wasn't clean on the first try — the regenerated code was
non-deterministic, five reruns giving five different event counts, and
the contract's own invariant caught it. And the blind agent,
constrained to a spec instead of familiar code, found a feed defect
fourteen sessions of sighted work had missed: a separator shift in the
timestamp column at the 2024/2025 boundary that five earlier sessions
had silently absorbed through an ordinary type cast. *"Fresh eyes
constrained to a spec see what familiarity glosses"* is the session's
own line for it. That is the capability: a method whose meaning lives
in the capsule can be re-derived by a stranger, checked against its
own invariants — and find new dirt in the data on the way through.

A word on the product: the study's session friction also drove real
DoxaBase fixes, a batched distiller pass, and four design documents —
DoxaBase eating its own cooking. That thread is deliberately not told
here; the full version (`docs/case-study-ais-full.md`) carries it,
with the trial records as receipts.

## What we did not prove

**One domain.** Everything here is vessel-tracking data — a single
dataset shape, one provider, two years. Generalization is explicitly
gated on a second real project stressing the same machinery.

**n=1 expert.** Every piece of tradecraft was validated by one person
— twenty years around vessel-tracking data, but one person's judgment
nonetheless. The study never tested whether a second expert would
agree with the first one's calls.

**The empty economic signal.** Session 9's honest negative is a
genuine result, but a thin one: seventeen mostly small-craft stops in
a single 18-month window. The real test of the indicator thesis needs
the roughly eighteen additional years of AIS history not yet loaded;
until then the idea has a working verification pipeline (M10) and no
confirmed instance.

**The mooring-buoy middle.** A vessel moored to a buoy is physically
anchor-like by every geometric signal the study built — at population
scale, 53% of pleasure/sailing windows read berth-like, 17%
anchor-like, 30% genuinely ambiguous — and the discriminator says so
honestly rather than forcing a call. Not a bug; a real physical
ambiguity the method correctly refuses to resolve.

**What stayed genuinely unresolved.** The index's `distance_m` formula
disagrees with raw broadcast spread by two orders of magnitude on at
least one glitch case — the question went back to the index's own
builder, unanswered. That Louisiana anchorage is honestly left open as
either a real status lie or a genuine engine-holding loiter. And both
vocabulary revisions keep an explicit couldn't-say ledger — `Voyage`,
recurring trade lanes, places as first-class resources — of what the
corpus needed and the evidence bar wouldn't yet support.

## How to see it yourself

Open `docs/journal/ais-study/reports/ais-session11-report.html` in a
browser for the berth-vs-anchor session's own rendered capsule, or
drop `docs/journal/ais-study/port-stops-map.kml` (San Diego Bay,
folders toggle by classification) into Google Earth. The threshold
plots behind the survey verdict live in
`docs/journal/ais-study/plots-s12/`, the recall curve in `plots-s13/`.
For the move-by-move transfer test, read `docs/worked-example.md`. The
capsule workbench — the analyst-facing companion that would replace
the by-hand expert channel — exists so far only as a design doc. Until
it runs, the capsule itself is the point: every claim in this document
traces to a graph resource with its evidence one hop away, the same
way every claim an agent made inside the study had to.
