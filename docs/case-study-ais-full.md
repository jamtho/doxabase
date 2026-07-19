# The AIS Field Study: A Full Account

*Long-form companion to `CASE-STUDY-AIS.md` (the short version this piece
supersedes in detail but not in fact). Interim draft written by the
project's resident agent; the maintainer intends to rewrite it in his own
voice. Every claim below points at a file — session briefs and journals in
`docs/journal/ais-study/`, graded trial records in `docs/journal/trials/`,
product waves in `docs/journal/waves.md`, design decisions in
`doxabase_design_docs/`. Read this if you want to know whether the way of
working is real; the pointers are there so you don't have to take the
narrative's word for it.*

---

## 1. Prehistory: why a field study, not more features

DoxaBase's first design brief asked for something small: a boring,
drop-in library that lets an AI agent keep durable, evidenced knowledge
about a body of data across sessions — observations, claims, patterns,
provenance, staged review. By early July 2026 the implementation had
grown into something else. An external design review (`06-fresh-eyes-
review-2026-07-03.md`) found a 74,607-line single-file core, 96 public
methods on one class, 89 MCP tools against a spec that had suggested
roughly ten, and a `project_brief` call that cost 100,462 characters on
an 805-triple fixture. The root cause the review named: the improvement
loop had no subtractive pressure. Every trial's friction became a new
field, a new tool, a new paragraph of documentation, and nothing ever
came back out (`doxabase_design_docs/06-fresh-eyes-review-2026-07-03.md`).

The Distillation Program that followed (`doxabase_design_docs/07-
distillation-program.md`) spent two days cutting the surface back down:
89 MCP tools to 25, the largest module to 4,829 lines, `project_brief` to
4,598 characters (3,835 on the real Enron capsule this study's methods
would later echo), and — the number that matters most for what comes
next — the package became installable from a clean wheel, gated in CI,
for the first time (`doxabase_design_docs/09-distillation-retrospective.
md`). The retrospective closed on 2026-07-05.

That same day, James asked for a proposal on what came after distillation.
The answer (`doxabase_design_docs/10-next-directions.md`) rebuilt the
trial loop on an insight from the failure just fixed: trials should
produce *records only* — full call logs, the agent's own friction notes,
graded outcomes — and go untouched into `docs/journal/trials/`. A
separate distiller pass, run later and rarely, reads the whole
accumulated record and proposes a small, justified batch of changes,
obeying a subtraction quota. Single-trial fixes are banned except for
outright bugs. And the next trials should be *real work*, not fixtures:
the product's next signal should come from someone actually using it to
learn something true about a real dataset.

The day before that proposal landed, a rehearsal had already proven half
of it. A Sonnet client agent inherited a pre-distillation Enron capsule —
built by the old, bloated surface — driven entirely through an installed
wheel of the new, distilled one, with zero migration and zero
contradictions between the old handoff notes and the live graph
(`docs/journal/trials/2026-07-enron-case-study.md`). The storage-schema
compatibility promise held on real data before the study proper even
started.

So the AIS field study was built to answer one question, not a basket of
feature requests: **can hard-won analytical understanding actually
transfer between minds that never met each other — carrying its evidence
and its failure modes with it?** Everything about the study's design —
cold sessions, capsule-only inheritance, blind probes, an async expert
channel — exists to put that question under real pressure, on a dataset
big and dirty enough that faking the answer would be harder than earning
it: two years of NOAA-style AIS broadcasts, 92 million position reports,
around the whole US coast.

## 2. The rules of the game

Fourteen sessions ran between 2026-07-06 and 2026-07-12 — four of them on
the first day alone. Every session obeyed the same constraints, tightened
where the previous session's friction demanded it.

**Cold sessions.** Most analysts started with no conversation history, no
notes, and an explicit do-not-read list naming every predecessor's
journal, brief, and tool-schema dump. A session brief (`BRIEF-N.md`) was
the only prepared context; everything else had to come from the capsule
or, for the sessions that needed it, fresh queries against the data. The
study alternated a strong model (internally called Fable) for the
capsule-building, distilling, and contract-authoring sessions with a
weaker one (Sonnet) for forensics, blind-transfer probes, and
verification work — deliberately, so that "the inheritance works" would
mean something harder than a strong model reading its own notes.

**The capsule as sole carrier.** Two interfaces, never varied: `bridge.py
call <tool> '<json>'` for the DoxaBase capsule (registry dumped once per
session via `bridge.py tools`), and `query.py "SQL" --max-rows N` for the
data itself, credentials resolved from the environment and never copied
anywhere. Nothing else — no shared scratch directory, no cross-session
memory — was allowed to move knowledge from one session to the next.
Every session ends by running `validate_graph(scope="all")` and leaving
no orphaned staged revisions; the reviewer, not the agent, renders the
capsule report.

**Blind grading.** For the sessions built as explicit transfer probes
(2, 6, and 14's phase 2 above all), grading criteria were written down
*before* the session launched — session 6's `probe-6-grading.md` fixed
the pass conditions (discovery route, semantic traps, fallback behavior,
integrity, economics) ahead of time so the verdict couldn't drift to fit
what happened.

**The expert channel.** A domain expert — James, twenty years around
vessel-tracking data — was available asynchronously, never inside a
session. Each session brief allowed at most three questions, left in
`expert-questions.md`; answers came back before the *next* session, never
the same one. Seven-plus rounds of this accumulated as recorded
observations in the capsule, cited by IRI in every later brief that acted
on them — chapter 6 below follows that thread on its own.

**Same-day product fixes, narrowly.** Nothing got fixed mid-session
unless it was a hard blocker. Everything else became a friction note,
queued for either an immediate same-day patch (only for outright bugs —
five of those are catalogued in chapter 9) or the next distiller pass.
The one deliberate exception to "nothing mid-session": three separate
sessions (2, 8, 13) misattributed the agent harness's own injected system
notices (date-change reminders, agent-roster lists) to a file they had
just read, and flagged them as prompt-injection attempts. The posture —
distrust instruction-bearing content, refuse silent compliance, report
plainly — was exactly right every time; only the diagnosis was wrong, and
each occurrence sharpened the brief template's harness-notices warning a
little further, a small distillation loop running inside the study
itself (`docs/journal/trials/2026-07-ais-session-13.md`).

**Trial records, deferred action.** Every session closed with a graded
record in `docs/journal/trials/`, untouched afterward, plus the analyst's
own journal in `docs/journal/ais-study/`. One distiller pass ran across
the first five records (`docs/journal/distiller-pass-1.md`); the
remaining fixes rode the same-day-bug-only exception.

## 3. Sessions 1–3: the founding

**Session 1** (2026-07-06, strong model, empty capsule) got the lowest
possible instruction: two tracks — three vessel forensics stories, and
open-ended method invention — no taught tradecraft, no hints. It mapped
both physical datasets (`broadcasts`, one row per received message;
`daily-index`, one row per MMSI per day), and by the end had recorded
five methods as the pattern that would hold for the rest of the study:
a `Pattern` (what it detects, why, confidence) plus caveats (failure
modes) plus an executable analysis view plus at least one evidenced
example. M1 classified identity changes with independent corroborators;
M2 found multi-emitter MMSIs; M3 segmented silence gaps; M4 read cargo
events off draft changes and inferred terminals without a port database;
M5 detected persistent co-movement pairs with a mobility statistic. Three
vessel stories anchored the corpus: a US Navy patrol boat, a shared-MMSI
chimera mixing a Shell oil platform with two unrelated Florida vessels,
and a passenger ship rename (OCEAN VOYAGER → VICTORY I) with a lay-up
window pinning the real date (`docs/journal/trials/2026-07-ais-
session-1.md`).

The session also produced the caveat that would organize everything after
it. Vessel identity — name, IMO, call sign, type, dimensions — turned out
to be frozen per calendar year: 2,736 of 2,738 recorded name transitions
land exactly on the 2024→2025 file boundary, the sole exception a Navy
patrol boat whose transponder toggled mid-year. Three more joined it fast:
`timestamp-cet-parse-bug` (the parsed `timestamp` column is UTC
mis-parsed as CET/CEST; `base_date_time` is the only trustworthy
absolute time — a bug in this project's own ingest, not NOAA's),
`placeholder-encoding-shift-2025` (2024 placeholder identity fields —
`IMO0000000`, zero dimensions — silently become NULLs the following
year), and `missing-day-2024-08-26` (a feed-wide outage, not vessel
silence). By the time session 4 ran, the catalog held two dozen of these
— the running joke inside the study became simply: *the feed lies*, and
the discipline was to catch it lying and write the lie down with
evidence, not to design around a guess.

Graded against James's own held-back tradecraft examples, session 1 came
up short on exactly one: low-speed dwell segmentation — distinguishing a
vessel stopped-but-transmitting at slow speed from one genuinely underway
— was not rediscovered. M3 covered lay-ups via silence and M4 via draft
change, but nobody had segmented active low-speed transmissions. That gap
was flagged explicitly for session 2 to probe — the first thread this
study pulls on deliberately, and the subject of chapter 4.

**Session 3** (still 2026-07-06, cold model) added the official
documentation layer, with one hard rule: where the provider's docs and
the capsule's empirical findings disagree, the empirical evidence wins.
It found the hub page unreadable without JavaScript, worked around it by
hitting the ArcGIS Sharing REST API directly, and downloaded five PDFs
and a receiver-location geopackage. Two results stand out. First, a
probable mechanism for the identity freeze: the provider runs an
MMSI-keyed identity-correction database (AVIS through 2023, AVID from
2024) that fuzzy-logic-corrects static fields — recorded as a
*refinement*, not a confirmation, since the correction cadence stays
undocumented, but it coherently explains both the near-annual freeze and
the Navy boat's surviving mid-year toggle. Second, a sharper caveat found
by cross-checking a document against live data rather than reading either
alone: the data dictionary's throwaway "Null Allowed" column, checked
against 2024 vs 2025 broadcasts, showed heading and COG sentinel values
(511, 360) fully swapping to true NULL at the year boundary while SOG's
102.3 sentinel survives untouched in both years — an asymmetry no
document states (`docs/journal/trials/2026-07-ais-session-3.md`). The
expert's own remembered "40–50 nm offshore" coverage rule, meanwhile,
turned up almost verbatim in the FAQ — memory graded against literature,
and it held.

Together, sessions 1–3 close the founding phase: two datasets fully
described, a caveat catalog deep enough to be load-bearing, five working
methods, and the first sign that the capsule's own history — the record
of what a prior session got told and how it checked — was itself worth
reading before touching data.

## 4. The transfer proof (session 2)

If the study has an emotional center, it is session 2, run the same day
as session 1 and deliberately on a weaker model. The brief: three
forensics tasks, capsule-only inheritance, predecessor scratch files
forbidden. No coaching. The point was not whether a fresh agent *could*
read a capsule — it was whether hard-won understanding built by a
stronger predecessor would actually move into a weaker mind's hands and
work (`docs/journal/trials/2026-07-ais-session-2.md`, walked move-by-move
in `docs/worked-example.md`).

**Retrieval over re-derivation, with citations.** The agent's first move
after orientation was not to start querying — it was to search the
capsule for anything already recorded. For task 2 (associates of MMSI
369305000, MAGDALEN), the capsule already held a session-1 finding: 171
pair-days with 368349000 (RB WEEKS), average 1.18 km apart, 621.6 km of
mobility together, a shared dredging itinerary from New York Harbor to
Galveston Bay. Rather than trust the number, the agent re-ran M5's exact
recorded SQL, filtered to its target, and reproduced the predecessor's
figures exactly — then used the recorded `m5-harbor-fleet-false-pairs`
caveat to dismiss roughly nineteen other co-located vessels as
same-jobsite noise, and filed one borderline case (seven pair-days,
535.6 km of mobility) as inconclusive rather than asserting a
relationship the method's own bar didn't clear. The `timestamp-cet-parse-
bug` caveat was load-bearing in every timing claim the session made — one
inherited sentence, an entire class of silent errors avoided
(`docs/journal/ais-study/JOURNAL-2.md`).

**The untaught gap emerged anyway.** Task 3 asked for the port calls of
MMSI 338617000 (PENNSYLVANIA) in May 2024 — a question no recorded method
covered. The capsule held the pieces: M4's draft-direction-as-cargo logic,
the timestamp caveat, and guidance on when the cheap index layer suffices
versus when broadcast-level detail is needed. The agent composed them:
screen the daily index for stationary clusters, find the exact SOG<1kn
threshold crossings at broadcast level, cross-check cargo plausibility
against draft direction. Six terminal stays came out, timed and
cargo-directional, and the method got recorded back as **M6** — with its
own caveats and SQL — exactly the low-speed dwell segmentation trick
James's held-back tradecraft had flagged, and that the *stronger*
session-1 model had missed. The domain expert later confirmed M6's core
trick as genuine tradecraft. The capsule did not contain the method; it
contained enough for a modest model to build it.

**The group improved its own memory, not just its stock of facts.** Task
1 — reconstruct MMSI 367615990's story — surfaced a rename (JACOB BRENT →
PERCIVAL) that M1's own corroboration rule, applied honestly, could not
classify: neither the call sign nor the IMO persisted across the change,
so by the letter of the method this should file as merely
`ambiguous_name_change`. But the physical dimensions were bit-for-bit
identical before and after, and the vessel operated continuously in the
same small stretch of Galveston-area water — same-hull evidence M1's
IMO/call-sign-only corroboration literally cannot see. The agent recorded
this as a caveat *against M1 itself*, with the counterexample as evidence
and a suggested fix, rather than silently working around the gap. A weak
model, using a strong model's method, corrected the method with evidence
attached — the epistemics working exactly as designed, and the next
analyst inherits the method *and* its known blind spot, not a method that
quietly fails the same way again.

The session's own summary line: *"nothing the previous analyst got
wrong"* — every exercised method and caveat held under independent
verification, and one genuine gap got named and filed rather than
papered over. James graded the three task answers separately from the
transfer verdict; both came back clean.

## 5. The middle game: sessions 4–9

Where sessions 1–3 founded the capsule, sessions 4–9 spent it — each one
explicitly building on what the previous session recorded, and each trial
record naming the inheritance rather than leaving it implicit.

**Session 4 — the story corpus** (2026-07-06, strong model). Fifteen
compact vessel stories, eighteen MMSIs including pairs and a flotilla,
selected by re-running the capsule's own M1/M2/M4/M5 views to build a
candidate pool rather than picking vessels by hand. The instruction was
diversity of *story shape*, and each story got a one-line kind-tag —
route metronome, seasonal trader, fixed installation, gear beacon,
niche-trade shuttle, MMSI collision, fleet-cloned MMSI, and eight more —
deliberately raw material for the next session to distill vocabulary
from (`docs/journal/trials/2026-07-ais-session-4.md`). Only four
broadcast-level queries were needed across all fifteen stories; the
index-first layering, recorded as cost discipline in session 1, held
without being re-argued.

**Session 5 — the vocabulary distills itself** (2026-07-06/07, strong
model). This is the study's cleanest demonstration that domain semantics
can be grown from recorded knowledge rather than designed up front. The
brief: read every story, method, and caveat already in the capsule; tabulate
the things, events, and assessments they actually needed to express;
propose a minimal vocabulary where every term is justified by at least
two independent stories; stage it; then *prove* it by re-expressing three
stories in it. **Zero data queries were needed** — the entire
distillation ran on capsule contents alone. The result was a 25-term
`aisv:` vocabulary (7 classes, 18 properties) staged through the
capsule's full stage → dry-run → apply → validate loop
(`docs/journal/ais-study/VOCAB-NOTE.md`).

The corpus forced the design's best move. An a priori ontology would
almost certainly have started with "Vessel." The stories refused it:
`aisv:AisIdentity` (the MMSI-keyed, year-frozen, self-reported identity
slot) had to be split from `aisv:Emitter` (the physical transmitting
object behind it), because five separate shared-MMSI stories — a Shell
platform sharing an MMSI with two Florida boats, a round-number default
MMSI colliding across a nationwide dredge-pipe marker population — made
anything simpler untenable. The feed's pathologies live in the semantics
honestly: `aisv:apparentDate` sits apart from `aisv:datingQuality`
specifically to encode the January-1 freeze artifact, and
`ambiguous_ballast` is a *mandatory* value of `cargoDirection`, not an
edge case bolted on. The session's own reflection: *"An a priori AIS
ontology would have started with Vessel, Voyage, Port and PortCall — and
three of those four are exactly what this corpus refused to support."*
The couldn't-say list it produced — voyages, recurring trade lanes,
tempo metrics, places as resources — became the v2 roadmap
(`docs/journal/ais-study/VOCAB-NOTE.md`).

The session also found and fixed a real bug the hard way: applying a
review decision with an *existing* revision IRI silently appended
duplicate single-cardinality fields onto that history row, producing
seven SHACL violations. The agent hand-repaired the corrupted history via
careful TriG surgery, documented the repair, and the product got a fix
same day — chapter 9 covers it in full.

**Session 6 — the blind vocabulary transfer** (2026-07-07, cold model).
The deliberate probe: a brief asking for two vessel stories recorded "in
the most precise, machine-readable form the capsule supports" that
*never mentions* `aisv:`, the ontology graph, or session 5 at all.
Grading criteria were fixed before launch. The agent found the
vocabulary through plain orientation — `project_brief` → `get_doc` →
`graph_overview` surfaced the 25 terms, their staged-revision provenance,
and the three worked examples, discoverable specifically because
distiller pass 1's fixes had made that route work. It applied both
semantic traps correctly: minting `AisIdentity` for every vessel but
`Emitter` only where the physical object was confidently segregated (one
of two co-mingled emitters was deliberately left in prose — *"a resource
I could not fully justify"* — rather than forced into a graph node the
evidence didn't support), and honoring `datingQuality=year_only_
undatable` on a Jan-1-boundary identity change (`docs/journal/trials/
2026-07-ais-session-6.md`).

The moment worth naming directly: the agent read session 5's *failed*
first attempt to re-express a story — 41 SHACL violations — sitting next
to its repaired successor in the capsule's own history graph, extracted
the convention the repair had settled on (cite claims via `rdfs:seeAlso`,
never the kernel's `rc:supportingClaim`, on non-kernel classes), and
wrote in its own journal: *"I inherit the lesson rather than
rediscovering it the hard way."* Not just a fact transferred between
minds that never met — a mistake, and its fix, transferred too. The
session's two new stories (a validly-formatted MMSI behaving like a junk
placeholder; a rare hospital ship motionless at one Gulf berth for two
years) were both new knowledge, not retreads, and both independently
rediscovered gaps from session 5's couldn't-say list without having read
it.

**Session 7 — track context, fast** (2026-07-07/08, cold model), the
first session commissioned directly from an expert remark (round 2:
draft-change interpretation needs positional context — a change while
underway reads differently than one at berth or at anchor). Built two
methods on top of what already existed: **M7** classifies each
vessel-day as underway, berthed, anchored, or a first-class
`transition_day` bucket from kinematics first and self-reported status
codes second — a design decision forced by catching its own first
attempt over-labelling a 484 km transit day as "berthed," because the
index's `status_codes` field is a whole-day distinct list, not a
point-in-time reading. **M8** joins M4's draft events to M7's dwell spans.
Proven against known ground (M6's own PENNSYLVANIA itinerary), M7 also
found a plausible seventh, previously unrecorded Tampa port call — filed
as an observation, not asserted as a story correction. The headline
number: dwell-attachment share (the fraction of draft-change events tied
to a recognized dwell) ordered seven vessels monotonically with how
clean their cargo stories already were — PENNSYLVANIA (genuine port
calls) at 92–95%, down to SULPHUR ENTERPRISE (the expert's own named
ballast-ambiguity exemplar) at 38–53% — obtained with zero external trade
knowledge. That is a quantitative confirmation, in numbers, of the
expert's own layering guidance: track context tells you *where* a draft
change happened, not *why* (`docs/journal/ais-study/JOURNAL-7.md`).

**Session 8 — the shuttle census** (2026-07-08, cold model), the survey
James said he had "wanted to run for many years": find vessels that run
between exactly two points, over and over, as candidate infrastructure
for a real-time industry indicator. Built directly on M7's dwell-span
layer, reused verbatim including its missing-day correction. The
detector's five thresholds (pole concentration ≥0.85, separation ≥0.15°,
≥6 alternations, dwell-fraction ≤0.5 to exclude laid-up craft,
≥300-day window) turned 111,100 dwelling MMSIs into **820 strict
shuttles**. Every candidate was cross-checked against M2's emitter
classes specifically to guard the failure mode the brief named up front
— a shared MMSI faking a shuttle — and twelve were excluded on exactly
that basis. Three exemplars were promoted with the population itself
kept out of the graph, in frames only, per an architecture agreed with
the expert the same day: SONNY COOK, a Mississippi towboat running Baton
Rouge to LaPlace almost weekly for two straight years with a maximum gap
of twelve days — the clean no-stoppage baseline; ALGOMA EQUINOX, a Great
Lakes grain carrier whose ~99-day winter gap matches the Soo Locks
closure (corroborated by two sister hulls on the same schedule) plus an
unexplained, vessel-specific 115-day gap flagged as anomaly, not signal;
and a five-hull ATLANTIC SAIL fleet running Baltimore–NY/NJ on a rotating
~30-day cycle, whose staggered per-hull maintenance breaks were correctly
read as fleet health, not fleet stoppage. Seventeen of the 820 — two
percent — had stopped running before mid-2025: the literal population the
expert's real-time-indicator thesis needed, flagged for the next session
rather than chased this one (`docs/journal/trials/2026-07-ais-
session-8.md`).

**Session 9 — the honest negative** (2026-07-08, cold model). All
seventeen stopped shuttles, individually verified: was the stop real
(ruled out coverage loss, identity change, and multi-emitter confusion
for the whole cohort in three batch checks, all clean), when exactly, and
what kind of stop. The taxonomy that came out: four vessels left the
region (one confirmed via a plausible mid-Pacific crossing to Maui at
3.2 kn, one via a directly observed acceleration-offshore-through-the-
Golden-Gate departure track — a new, reusable terminal signature); six
were re-tasked to different routes (two container ships, SEASPAN ADONIS
and ONE ALTAIR, confirmed redeployed from the Pacific to the Atlantic
coast); six were apparent lay-ups, three abrupt and three showing a slow
cadence decay; one was a US Coast Guard reassignment. Zero renames, zero
multi-emitter artifacts, zero coverage-loss cases in the whole cohort.
And then the finding that actually mattered: for every endpoint checked —
including a Los Angeles/Long Beach–Oakland container corridor that looked
like a four-vessel route collapse — traffic from *other* operators
continued at full strength after the subject vessel stopped. The
route-side, industry-signal shortlist the expert's thesis needed is, in
this cohort, empty. The session's own framing: not a refutation, a
calibration — 2024–2025 and seventeen mostly small-craft stops is thin
ground for a macro signal, and the roughly eighteen further years of
history James has yet to add are where the idea gets its real test. What
the session actually built, and what survives regardless of the verdict,
is **M10**, a reusable stop-verification checklist (identity → emitter →
terminal-trajectory read → endpoint-continuity → own-vessel seasonality
baseline) that makes any future positive believable
(`docs/journal/ais-study/JOURNAL-9.md`). The session also self-reported a
process error mid-run — it had read a predecessor's journal in the same
tool batch that opened the brief, before finishing the do-not-read list —
assessed the contamination risk as low, and independently re-derived its
key number rather than trust the tainted read. Self-report, impact
assessment, independent re-derivation: the posture the study asked for,
demonstrated under real pressure.

Six sessions, and at every join the trial record names what it inherited
by IRI: session 5 harvests session 4's stories; session 6 proves session
5's vocabulary transfers blind; session 7 builds M7/M8 on M4's method and
its own new dwell layer; session 8 reuses M7's dwell layer verbatim;
session 9 verifies against M9's census using M1/M2/M3 as a battery of
negative checks. Nothing here was re-derived that didn't need to be.

## 6. The expert channel

The expert channel ran asynchronously and left its own thread through the
whole study: a remark from James, recorded as a capsule observation with
his own words preserved, a session commissioned to act on it, a method
that resulted, and — often — a design note written back to him citing his
directive verbatim. Eight moments carry the thread best.

**1. The layering doctrine (round 2).** Reviewing session 5's vocabulary
note, James pushed back on `CargoOperation`: draft changes aren't only
cargo — he had seen draft move from ballast water discharge or uptake
too. His framing, recorded and later quoted back to him in v2: *"layer 1
computes physical facts; layer 2 draws operationally-relevant inferences
… we need to be humble when designing information systems — our users
will (often) take our words as we write them."* Session 10 made this
structural: `CargoOperation`/`cargoDirection` were superseded (retained,
never deleted) by `DraftChangeEvent`/`draftChangeReading`, and
`OperationalTie` by `RecurringCoPresence`/`coPresenceReading`, each new
reading carrying a `readingBasis` property stating exactly what layer-1
evidence it rests on (`docs/journal/ais-study/expert-feedback-
round-2.md`, `docs/journal/ais-study/VOCAB-NOTE-V2.md`).

**2. Gear beacons, battery in the COG field.** An aside that became a
whole object class: people tag fishing gear released from the boat with
AIS transmitters; the units broadcast under the *same* MMSI as each
other, fleet-style, and encode battery level in the course-over-ground
field. James's own words: *"Not made up."* Consequence: COG can never be
trusted as raw kinematics near zero speed without a plausibility screen —
which session 11 built and used directly, rejecting a COG-based heading
fallback that scored a near-random circular concentration of R=0.125 on
exactly this basis. The class itself (`GearBeacon`) was proposed and then
correctly *rejected* at the two-story evidence bar in v2 — the in-feed
941xxxxxx buoy population each carries its own MMSI, not James's
same-MMSI battery-fleet pattern, which nobody has yet sighted in this
feed — and stays on the couldn't-say list rather than being minted on
novelty alone (`docs/journal/ais-study/expert-feedback-
round-2.md` addendum 2).

**3. The identity-declaration threshold.** James restated a rule from his
prior practice: an `AisIdentity` is the product of an analysis process
deciding a pattern looks like one transmitter, but *"this definitely is
hull (Transmitter) h"* is declared only against a solid non-AIS record —
flag-state, port, or commercial registry data. Session 10 encoded this as
`declaredHullRecord`, a property with deliberately zero instances in the
graph today — absence as the signal, since every emitter the study has
found is correctly still a candidate, not a declaration
(`docs/journal/ais-study/VOCAB-NOTE-V2.md`).

**4. The vision.** Recorded verbatim in the addenda to round 2, after the
gear-beacon discovery: *"if we set up exactly the right conditions with
this project we can throw agents at the data set and they'll just start
learning all sorts of new things about the world."* The river-shuttle
economic-indicator idea, in the same burst, is the concrete instance the
study spent sessions 8 and 9 chasing.

**5. The SOG two-curves observation.** James's standing practice —
histogram everything at fine grain and study the shape — produced a
concrete refinement handed straight to method design: speed-over-ground
is *two superimposed curves*, one for genuine steaming and one for
low-speed maneuvering, visible directly in a fine-grained histogram.
Implication recorded for M7: kinematic thresholds can be read off the
valley between the modes rather than picked arbitrarily
(`docs/journal/ais-study/expert-feedback-round-2.md` addendum 4).

**6. The validation doctrine (round 4).** Foundational, human-trusted
measures don't get to rest on four proving vessels — they get a
whole-dataset survey and threshold plots, because humans trust thresholds
through plots. This directly commissioned session 12's 4,710-window
survey, run before anyone treated M11's thresholds as settled
(`docs/journal/trials/2026-07-ais-session-12.md`).

**7. Maps are the interface (rounds 5–6).** Reviewing early KML exports,
James's guidance was concrete: lead with what you're trying to show, join
motion points with line segments, label points with context, and for a
classifier demo use one busy location with many toggleable folders rather
than everything at once — the design note baked directly into
`docs/journal/ais-study/port_stops_kml.py`'s San Diego Bay export. Round 6
added the KML-export-on-every-view affordance and named prose comments an
"epistemic rung": an L0-only method is the smell that marks a future,
more formal candidate. Both became explicit design inputs for the
capsule observatory (`doxabase_design_docs/11-capsule-observatory.md`).

**8. Autoresearch over contracts (round 7).** The forward-looking close,
recorded the day the method-contracts pilot passed: because a contract's
goal, invariants, parameters, and every past experiment are queryable
graph citizens, an agent evolving a better detector inherits the full
experimental record and leaves its own — proposed with M11's ambiguous
band as the first candidate optimization target
(`doxabase_design_docs/12-rdf-method-contracts.md` §8).

Two more deserve a line each for completeness: the anchor-vs-berth
research question itself (round 3) is chapter 7's whole subject, and the
state-vs-ephemera framing (an addendum the same week as the gear-beacon
finding) — that predicted-transmitter sets and event populations are
regenerable run artifacts, not durable state — became the architecture
sessions 8 onward practiced without being told twice, and later the
explicit subject of `doxabase_design_docs/14-anchored-derivations.md`.

The loop closes visibly every time: an expert remark becomes a capsule
observation with his words preserved; a session brief cites the
observation's IRI; a method or vocabulary change results; a note goes
back to James quoting his own directive next to what was built from it.
`VOCAB-NOTE-V2.md`'s section 1 does this literally, line by line, for
every one of round 2's directives.

## 7. The instrument turn: sessions 11–13

Three sessions in a row that stopped building vessel stories and started
building *instruments* — methods whose thresholds are trusted enough to
hand to someone outside the study.

**Session 11 — anchor or berth?** (2026-07-09, cold model). The first
session answering a real external research question, relayed through
James (round 3): distinguish a vessel stopped at anchor from one stopped
at a berth, without trusting the self-reported navigation status a
captain may simply forget to update. The session built three independent
signals and proved all three. Swing geometry: an anchored vessel traces a
ring around its ground tackle (radius 120–170 m, "hollow" — mostly ring,
little center — 0.34–0.65 fraction), a berthed one is a GPS-noise point
(radius 2–4 m, hollow fraction 0.89–0.99). True-heading circular
concentration: pinned at a dock (R≈0.95–1.0) versus weathervaning at
anchor (R≈0.65–0.76) — with COG explicitly rejected as a heading proxy on
exactly the gear-beacon caveat's grounds. Crowd evidence: locations where
many distinct vessels dwell with pinned headings are berth
infrastructure; wide, dispersed, swinging dwells are anchorage ground —
ten-plus terminal complexes confirmed at 0.97–1.0 agreement over 1,500-
plus vessel-days, with status codes used only to check the result, never
inside the clustering itself, to avoid circularity. The showcase
measurement: PENNSYLVANIA, the same hull, one day apart — an anchor wait
(radius 123 m, hollow 0.34, heading sweeping over 110° at zero speed)
followed by a clean berth (radius 3.4 m, hollow 0.94, heading pinned to
six nines: R=0.999997). A better than 30-fold radius gap, ring collapsing
to point, inside one vessel's own history — the cleanest single proof the
study produced (`docs/journal/ais-study/JOURNAL-11.md`).

As a byproduct, the session graded NavStatus itself: roughly 97% reliable
at berth for large ships, but anchorage self-reporting turned out to be
sharply location- and culture-dependent — Vancouver's English Bay
agreeing with the physical signature 77–100% of the time against an
offshore Louisiana anchorage ground reporting "anchored" on just 0.2% of
windows that looked anchor-shaped by geometry, honestly left unresolved
as possibly a real engine-holding loiter rather than a lie. New failure
modes were documented rather than smoothed over: mooring buoys can
present either signature from the same field (a Catalina Island mooring
pair split cleanly berth-like and anchor-like), and Class B recreational
craft transmit neither heading nor status, leaving crowd evidence as the
only usable signal for that whole population.

**Session 12 — the threshold survey** (2026-07-11, cold model),
commissioned specifically to satisfy the validation doctrine before
anyone treated M11's thresholds as trustworthy. A full broadcast-level
pass over the 7,316,288 eligible stationary vessel-day windows was
correctly declared infeasible; the session instead pulled 4,710 windows
stratified across eleven vessel classes and 5-degree geography, fetched
in a single 90.8-second broadcast join rather than hundreds of separate
daily queries — and recorded the full-survey SQL so a production run
remains possible later. The verdict: keep M11's tuned thresholds — the
empirical radius valley sits at roughly 20 meters, exactly matching the
tuned berth boundary, and two independent signals (radius, heading
dispersion) agree on where the transition zone sits. But the doctrine's
own shape expectation needed revising: the population is not two clean
humps, it's one dominant pinned/berth mode plus a long diffuse tail —
population-validated now, not just inferred from four proving vessels.
Class dependence held as predicted (cargo, tanker, and tug/tow classes
sit cleanly on the thresholds), and the survey caught something nobody
was looking for: 10.1% of sampled windows are position-suspect, the worst
case a vessel whose longitude sat frozen bit-identical across 317
messages while its latitude drifted roughly 750 kilometers — smooth
enough to be invisible to any jump-based glitch detector, and disagreeing
with the index's own `distance_m` field by two orders of magnitude
(`docs/journal/trials/2026-07-ais-session-12.md`, plots in
`docs/journal/ais-study/plots-s12/`). That formula question went straight
back to James as the index's own builder — unresolved, and honestly
flagged as his to answer.

**Session 13 — the stops series is the foundation** (2026-07-11, cold
model), the session that quantified the expert's own caution about the
day-granularity architecture everything downstream had been built on.
Across 457 stratified MMSIs and 92.4 million broadcast rows, pulled in
one 74-second glob join, day-level detection finds only **52.4%** of
stops lasting 10–30 minutes, rising monotonically through 60.8% (30
minutes to 2 hours), 71.2% (2–6 hours), 78.6% (6–24 hours), to 99.0% for
multi-day stops. The single illustration that makes the number concrete:
a Ventura passenger vessel cruising at 19–20 knots all day with one clean
nine-minute stop mid-route — a stop the day-index classifier can
structurally never see. **M12**, the event-level stops-series extractor
this session recorded, works at broadcast granularity instead: contiguous
runs under 0.5 knots, broken by any silence longer than 30 minutes (never
assumed continuous — a real bug caught mid-build, where 47 messages spread
across 70 days had briefly registered as one 70-day "stop" before the
silence check was added), short flickers under 2 minutes merged back in,
and session 12's position-glitch screen reused verbatim, flagging 7.0% of
windows. The payoff was immediate: re-running M9's shuttle-detection logic
over the event-level series instead of the day-level index found **43**
shuttles on the same sample where the day-level pass found only 14 — three
times more, with every one of the nine shuttles both passes agreed on
being the clearest cases, and all five day-only-detected passes
explainable as grid or conflation artifacts once inspected. The
stops-series-as-foundation architecture the expert had guessed at in
round 4 is now evidence, not a hunch (`docs/journal/trials/2026-07-ais-
session-13.md`, recall plot in `docs/journal/ais-study/plots-s13/`).

## 8. The contracts finale: session 14 and doc 12

The study's last day opened with a live design conversation, not another
brief. James had been carrying a pattern from other work: use a knowledge
graph to define a method's *behavioural contract* — what it consumes,
what its output means, what invariants it must never violate, what
parameters it depends on and their evidence — and let an agent supply the
"accidental but still necessary" code underneath, bottoming out in
natural language at the base. The design note
(`doxabase_design_docs/12-rdf-method-contracts.md`) argues the field
study's own methods already had this shape informally: prose contract,
executable SQL, linked caveats, held together only by convention. Two
forces pushed toward making it formal — a threshold that cost a
4,710-window survey (session 12's M11 work) deserved to be a graph
citizen with its evidence attached rather than a literal buried in a SQL
string, and the state-vs-ephemera architecture already agreed with the
expert meant "the method" needed to outlive any one DuckDB realization of
it.

**Phase 1** (2026-07-12, strong model) built the contract. A twenty-term
`mc:` vocabulary — `MethodContract`, `Parameter`, `Invariant`,
`Realization`, and the properties connecting them — every term justified
by how M9, M11, and M12 were actually written, no term invented ahead of
need. M12's full contract came out with five property-style invariants,
including one named `silence-terminates` that structurally encodes the
exact bug session 13 caught mid-build: a regenerated realization that
fails this invariant has reproduced that bug. Seven parameters carried
real evidence, not bare numbers: the 0.5-knot/600-second stop threshold
cites session 13's own claim directly; the 1800-second silence-break
threshold carries the 70-day phantom-stop story as its justification;
120 seconds is honestly labelled "design choice, no survey" rather than
dressed up as validated; the position-glitch screen's three parameters
cite session 12. Every parameter carries `assessedAt` and
`assessmentDataWindow`, so a threshold's evidence visibly ages as more
data arrives. `rc:citesClaim` — a small ontology addition James had
approved that same morning as a "no brainer" — got its first production
use here, wiring evidence into contract terms without borrowing the
kernel's claim-citation machinery meant for something else
(`docs/journal/trials/2026-07-ais-session-14.md`).

**Phase 2**, the same day: a cold agent, given *only* a 333-triple
export bundle — the contract, never the SQL — rebuilt M12 from scratch
against live data. It produced **426,207 events against the original's
427,134** — a −0.22% difference — with a matching flag rate (6.92% versus
7.0%) and the post-fix maximum stop event reproduced to the decimal
(89.709 days against the contract's quoted "plausible 89.7"). All five
invariants passed — but not on the first try, and that failure is the
finding that matters most: the regenerated SQL was initially
non-deterministic, because same-second broadcast collisions left
window-function tie-breaking arbitrary, and five reruns produced five
different event counts. The invariant checker caught it. The fix —
integer run identifiers and single-threaded canonical execution — made
reruns bit-identical, and doc 12's fourth decision point (regenerated
code always stages behind an invariant report before anyone trusts it)
went from a design lean to demonstrated law inside the pilot that tested
it. And the blind agent, constrained to a spec instead of familiar code,
found something no sighted session had: a real separator shift in
`base_date_time` at the 2024/2025 boundary that five earlier sessions had
silently absorbed through an ordinary type cast without ever noticing —
now a recorded caveat, verified live by the curator, and a fresh pipeline
reminder for James. *"Fresh eyes constrained to a spec see what
familiarity glosses"* is the session's own line for it
(`docs/journal/trials/2026-07-ais-session-14.md`). Behavioural
regeneration from an RDF contract alone works, on this evidence, at the
99.8% level — and the missing 0.2% is attributable to exactly the gaps
the contract's own couldn't-say list had predicted going in (metric
definitions left as prose, ordering determinism, duplicate-broadcast
handling), which is itself the deliverable doc 12 asked the pilot for.

## 9. What the product got out of it

The study was also DoxaBase eating its own cooking — every session's
friction fed back into the product it was built to test, on the schedule
doc 10 set: hard blockers same-day, everything else to a deferred
distiller pass.

**Five same-day fixes, concretely:**

1. **Session 1's doc/tool mismatches** (wave 25, 2026-07-06): the core
   library had grown `evidence_summary`/`evidence_sources`/`evidence_iri`
   parameters on caveat recording and `observation_iri`/`claim_iri`/
   `evidence_iri` on claim recording, but the MCP wrappers exposed to
   agents never picked them up. Fixed the same day the session landed;
   claims and caveats could carry stable project IRIs through MCP from
   then on (`docs/journal/waves.md`, wave 25).
2. **A history-corruption bug** (session 5, 2026-07-06/07): applying a
   review decision against an *existing* revision IRI silently appended
   duplicate single-cardinality fields onto that history row instead of
   minting a new one — seven SHACL violations, discovered only because the
   agent happened to validate afterward. It hand-repaired the corrupted
   history via careful TriG surgery and documented the repair; the
   recorder now refuses pre-existing IRIs outright with a targeted error,
   regression-tested (`docs/journal/trials/2026-07-ais-session-5.md`).
3. **The stale-sibling recheck bug** (wave 27, 2026-07-07): session 6 hit
   a staged revision, already properly closed by a review decision, being
   flagged again as a "stale sibling" needing recovery — contradicting
   what the recovery planner itself already knew to ignore. Fixed to skip
   any row carrying `rc:resolvesStagedRevision`, matching the planner's
   own logic (`docs/journal/waves.md`, wave 27).
4. **Silent CURIE failures** (wave 28, 2026-07-07): session 6 filtered
   `list_entities` by `aisv:AisIdentity` and got a silent empty result,
   because project-namespace prefixes were never registered for CURIE
   expansion. Fixed to reject unregistered-prefix type filters with a
   targeted error naming the known prefixes, rather than returning a
   result that looks like "nothing exists" (`docs/journal/waves.md`, wave
   28).
5. **Prose silently coerced into broken URIs** (wave 29, 2026-07-07):
   curating an expert-channel observation with a colon-bearing value
   (`"expert:james (round 2)"`) walked through a chain of silent failures
   — an unknown argument dropped by the transport layer, evidence minted
   without a source, and finally that prose value coerced into an invalid
   URI reference — surfacing only when `validate_graph` ran. Fixed at the
   root: any whitespace-bearing value is now always treated as a literal,
   since whitespace can never appear in a valid IRI (`docs/journal/
   waves.md`, wave 29).

**The distiller pass.** One pass ran, over the first five trial records
plus the accumulated friction tail of the pre-study batteries
(`docs/journal/distiller-pass-1.md`, 2026-07-06). Six items, each
justified across multiple observations, under an explicit subtraction
quota: no new tools, no new response fields, no new doc sections allowed
in. The headline item *removed* a field — `direct_review_reasons`, a pure
derivation of another field already on the wire — cutting
`describe_query_context` by 13.4% and letting its budget ceiling ratchet
down, not up. A second item made targeted spec errors state which fields
are required versus optional, directly from session 4's friction. A third
fixed vocabulary discoverability with a documentation change once the
investigation showed the underlying mechanism already worked — the
`graph="map"` default was just silently returning nothing, not broken.
The pass also caught, while aligning docstrings to behavior, a genuine
bug: a flat `observed_column` argument was being silently dropped on one
recording path though the equivalent nested call accepted it; fixed and
regression-tested as a side effect of the truthfulness sweep, not as its
own headline item.

**Design documents the field need produced, not the reverse.** Four
design docs came directly out of what the study's later sessions
demanded, each with pilot evidence attached rather than speculative
architecture: the **capsule observatory** (`doxabase_design_docs/11-
capsule-observatory.md`), a public map-first rendering of any capsule,
proposed because the expert channel converged on "maps are the interface"
across rounds 4–6 and the study's own KML scripts had already proven the
cheap path worked; **RDF method contracts** (`doxabase_design_docs/12-
rdf-method-contracts.md`), covered in full in chapter 8, whose pilot
passed the same day it was proposed; the **capsule workbench**
(`doxabase_design_docs/13-capsule-workbench.md`), an exploratory
analyst-facing companion to the observatory that James asked for as "a
doc he can later run with," explicitly because the study's own expert
channel — chat plus KML files plus HTML reports, run by hand fourteen
times — is exactly the workflow it would replace; and **anchored
derivations** (`doxabase_design_docs/14-anchored-derivations.md`), which
takes the state-vs-ephemera practice sessions 8 onward followed without
being told twice and states it as law: populations live in regenerable
frames, identity enters the graph only by promotion, and re-anchoring a
drifted entity is always a reported finding, never a silent overwrite.

## 10. Honest limits

The study proved something real, and it did not prove more than it did.

**One domain.** Everything here is vessel-tracking data — a single
dataset shape, one provider, two years. The generalization path DoxaBase
itself proposes (ontology packs splitting the stable epistemic kernel
from domain-specific vocabulary) is explicitly gated on *two* real
projects stressing the current pack first, "not before" (`doxabase_
design_docs/10-next-directions.md` §4). This study is one of the two.

**n=1 expert.** Every piece of tradecraft validated in this study was
validated by one person — James, twenty years around vessel-tracking
data, but one person's judgment nonetheless. The identity-freeze
mechanism, the gear-beacon discovery, the layering doctrine, the
validation doctrine — all of it traces to a single domain authority. The
study never tested whether a second expert would agree with the first
one's calls.

**The empty economic signal.** Session 9's honest negative is a genuine
result, not a failure to hide, but it is also a genuinely thin one: 17
vessels, a single 18-month window, and every route-side candidate
resolving to vessel-side causes. The real test of the real-time-indicator
thesis needs the roughly eighteen additional years of AIS history James
has and has not yet loaded (`docs/journal/ais-study/expert-feedback-
round-2.md`, item 4) — until then the indicator idea has a working
verification pipeline (M10) and no confirmed instance.

**The mooring-buoy middle.** Session 11 found, and session 12 confirmed
at population scale (n=931 pleasure/sailing windows: 53% berth-like, 17%
anchor-like, 30% genuinely ambiguous), that a vessel moored to a buoy is
physically anchor-like by every geometric signal the study built, and the
discriminator says so honestly rather than forcing a call. It is not a
bug to fix; it is a real physical ambiguity the method correctly refuses
to resolve.

**The couldn't-say lists.** Both vocabulary revisions kept an explicit
ledger of what the corpus needed and the evidence bar wouldn't yet
support: a `Voyage` class (James: no version yet that works for every
vessel in his head), recurring trade lanes and event clusters (called "a
great idea," deliberately left unbuilt pending more evidence), places as
first-class resources (waiting on an unresolved RDF-versus-dataframe rule
of thumb), operating-tempo metrics, structured draft values, tow/escort
events, and an alternative hull-tagged-usage-period identity primitive
James has used before and the study has not yet needed
(`docs/journal/ais-study/VOCAB-NOTE-V2.md` §3). The method-contract
vocabulary carries its own list — threshold bands, sequenced decision
procedures, derived-metric definitions, parameter interactions — recorded
as deliberate modelling debt, not oversight.

**What stayed genuinely unresolved.** The index's `distance_m` formula
disagrees with raw broadcast spread by two orders of magnitude on at
least one glitch case, and the question of what it actually computes went
back to James unanswered. An offshore Louisiana anchorage ground reports
"anchored" on 0.2% of windows that look anchor-shaped by every physical
signal the study built — honestly left open as either a real NavStatus
lie or a genuine engine-holding loiter that isn't anchoring in the AIS
sense, "unresolvable without more broadcast work."

**What a second domain must prove.** Every generalization claim in this
study's design output is explicitly conditional on it. `doxabase_
design_docs/14-anchored-derivations.md` names its own test directly: "the
second case study's entity resolution will exercise [this pattern] at
legal-risk stakes, where 'cluster 17 became cluster 23' is the difference
between two companies being confused." Doc 12 holds its `mc:` vocabulary
project-local by the same rule, migrating terms to the shared `rc:`
kernel only if a second domain independently needs the same ones. Nothing
here is a finished generalization; it is a first domain that held up
under real pressure.

## 11. Coda: the numbers, and how to see it yourself

| | |
|---|---|
| Sessions | 14, 2026-07-06 to 2026-07-12 (four on the opening day) |
| Methods recorded | 12 (M1–M12), each pattern + SQL + caveats + evidenced example |
| Vocabulary | `aisv:` v1: 25 terms (7 classes, 18 properties); v2: 34 active terms, 4 superseded-and-retained |
| Method contracts | `mc:` vocabulary, 20 terms; M12 fully formalized (5 invariants, 7 evidenced parameters) |
| Evidenced observations | roughly 150, with claims in the low hundreds and ~45+ patterns by session 11 (`docs/journal/ais-study/JOURNAL-11.md`), growing further through session 14 |
| Expert rounds | 7-plus, every one cited by observation IRI in a later brief |
| Rendered capsule reports | 16, one per session plus the Enron and fixture precedents (`docs/journal/ais-study/reports/`) |
| Same-day product fixes | 5 concrete bugs (chapter 9); 1 distiller pass, 6 items |
| Design docs produced | 4 (`doxabase_design_docs/11–14`), each with pilot evidence |
| Transfer evidence | cold weak model applies + extends inherited methods (session 2); vocabulary transfers blind, zero hints (session 6); contract-only blind regeneration at −0.22% (session 14) |
| Recall audit | day-level stop detection: 52.4% (10–30 min stops) → 99.0% (multi-day) — measured, not assumed (session 13) |
| Cost discipline | 7.3M-window population surveyed via one 90.8s join (session 12); 92.4M broadcast rows via one 74s join (session 13); the entire shuttle census cost 3 index passes (session 8) |

To see it rather than read about it: open
`docs/journal/ais-study/reports/ais-session11-report.html` in a browser
for the berth-vs-anchor session's own rendered capsule, or drop
`docs/journal/ais-study/port-stops-map.kml` (San Diego Bay, folders
toggle by classification) or `docs/journal/ais-study/demo-story-map.kml`
into Google Earth. The five threshold-survey plots that back session 12's
verdict live in `docs/journal/ais-study/plots-s12/`; the recall curve
behind session 13's headline number is in `docs/journal/ais-study/
plots-s13/`. For the move-by-move version of the transfer test, read
`docs/worked-example.md`. Neither the capsule observatory nor the
capsule workbench exist yet as running software — `doxabase_design_docs/
11-capsule-observatory.md` and `13-capsule-workbench.md` are the designs
for them, written the last day of this study, waiting on an implementing
session. Until then, the capsule itself is the point: every claim in this
document traces to a graph resource with its evidence one hop away, the
same way every claim an agent made inside the study had to.
