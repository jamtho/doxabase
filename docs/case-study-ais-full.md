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

## 1. How we got here: a product that nearly ate itself

DoxaBase's first design brief asked for something small: a boring, drop-in
library that lets an AI agent keep durable, evidenced knowledge about a
body of data across sessions — observations, claims, patterns, provenance,
staged review. By early July 2026 we no longer had that. We had a
74,607-line single-file core, 96 public methods on one class, 89 MCP tools
against a spec that had suggested roughly ten, and a `project_brief` call
that cost 100,462 characters on an 805-triple fixture. An external design
review said out loud what we had been living inside: the improvement loop
had no subtractive pressure. Every trial's friction became a new field, a
new tool, a new paragraph of documentation, and nothing ever came back out
(`doxabase_design_docs/06-fresh-eyes-review-2026-07-03.md`).

Two days of deliberate cutting followed — the Distillation Program
(`doxabase_design_docs/07-distillation-program.md`). 89 MCP tools became
25. The largest module came down to 4,829 lines. `project_brief` fell to
4,598 characters (3,835 on the real Enron capsule whose methods this
study's would later echo). And — the change that mattered most for what
comes next — the package became installable from a clean wheel, gated in
CI, for the first time (`doxabase_design_docs/09-distillation-
retrospective.md`). The retrospective closed on 2026-07-05.

That same day, James asked what came after distillation. The proposal we
wrote back (`doxabase_design_docs/10-next-directions.md`) rebuilt the trial
loop around the failure we had just paid for: trials should produce
*records only* — full call logs, the agent's own friction notes, graded
outcomes — and go untouched into `docs/journal/trials/`. A separate
distiller pass, run later and rarely, reads the whole accumulated record
and proposes a small, justified batch of changes under a subtraction quota.
Single-trial fixes are banned except for outright bugs. And the next trials
should be *real work*, not fixtures: the next signal should come from
someone using the product to learn something true about a real dataset.

We had already rehearsed half of that without quite meaning to. The day
before the proposal landed, a Sonnet client agent inherited a
pre-distillation Enron capsule — built by the old, bloated surface — driven
entirely through an installed wheel of the new, distilled one, with zero
migration and zero contradictions between the old handoff notes and the
live graph (`docs/journal/trials/2026-07-enron-case-study.md`). The
storage-schema compatibility promise held on real data before the study
proper even started.

So we built the AIS field study to answer one question, not a basket of
feature requests: **can hard-won analytical understanding actually transfer
between minds that never met each other — carrying its evidence and its
failure modes with it?** Everything about the design — cold sessions,
capsule-only inheritance, blind probes, an async expert channel — exists to
put that question under real pressure, on a dataset big and dirty enough
that faking the answer would be harder than earning it: two years of
NOAA-style AIS broadcasts, 92 million position reports, around the whole US
coast.

## 2. The rules we tied ourselves to

Fourteen sessions ran between 2026-07-06 and 2026-07-12 — four of them on
the first day alone. We wrote the constraints down before the first one
launched, then tightened them wherever a session's friction demanded it.

**Cold sessions.** Most analysts started with no conversation history, no
notes, and an explicit do-not-read list naming every predecessor's journal,
brief, and tool-schema dump. A session brief (`BRIEF-N.md`) was the only
prepared context; everything else had to come from the capsule or fresh
queries against the data. We alternated a strong model (internally called
Fable) for the capsule-building, distilling, and contract-authoring
sessions with a weaker one (Sonnet) for forensics, blind-transfer probes,
and verification work — deliberately, so that "the inheritance works" would
mean something harder than a strong model reading its own notes.

**The capsule as sole carrier.** Two interfaces, never varied: `bridge.py
call <tool> '<json>'` for the DoxaBase capsule (registry dumped once per
session via `bridge.py tools`), and `query.py "SQL" --max-rows N` for the
data itself, credentials resolved from the environment and never copied
anywhere. Nothing else — no shared scratch directory, no cross-session
memory — was allowed to move knowledge from one session to the next. Every
session ends by running `validate_graph(scope="all")` and leaving no
orphaned staged revisions; the reviewer, not the agent, renders the capsule
report.

**Blind grading.** For the sessions built as explicit transfer probes (2,
6, and 14's phase 2 above all), we wrote the grading criteria down *before*
the session launched — session 6's `probe-6-grading.md` fixed the pass
conditions (discovery route, semantic traps, fallback behavior, integrity,
economics) so the verdict couldn't drift to fit what happened.

**The expert channel.** A domain expert — James, twenty years around
vessel-tracking data — was available asynchronously, never inside a
session. Each session brief allowed at most three questions, left in
`expert-questions.md`; answers came back before the *next* session, never
the same one. Seven-plus rounds of this accumulated as recorded
observations in the capsule, cited by IRI in every later brief that acted
on them — chapter 7 follows that thread.

**Same-day product fixes, narrowly.** Nothing got fixed mid-session unless
it was a hard blocker. Everything else became a friction note, queued for
either an immediate same-day patch (only for outright bugs — five of those
are catalogued in chapter 10) or the next distiller pass. One incident
recurred enough to earn its own loop: three sessions (2, 8, 13) mistook the
harness's own injected system notices (date-change reminders, agent
rosters) for content planted in a file they had just read, and flagged
prompt-injection — each occurrence, told where it happened below, sharpened
the brief template's harness-notices warning a little further, a small
distillation loop inside the study itself
(`docs/journal/trials/2026-07-ais-session-13.md`).

**Trial records, deferred action.** Every session closed with a graded
record in `docs/journal/trials/`, untouched afterward, plus the analyst's
own journal in `docs/journal/ais-study/`. One distiller pass ran across the
first five records (`docs/journal/distiller-pass-1.md`); the remaining
fixes rode the same-day-bug-only exception.

## 3. Day one: an empty capsule and a feed that lies

On the morning of 2026-07-06 we pointed the strong model at an empty
capsule and gave it the lowest-resolution instruction we could defend: two
tracks — three vessel forensics stories, and open-ended method invention —
no taught tradecraft, no hints — then watched what it did with two years of
raw traffic (`docs/journal/trials/2026-07-ais-session-1.md`).

It mapped both physical datasets first (`broadcasts`, one row per received
message; `daily-index`, one row per MMSI per day), then started recording
methods in a shape that held for the rest of the study without anyone
mandating it: a `Pattern` (what it detects, why, confidence) plus caveats
(failure modes) plus an executable analysis view plus at least one
evidenced example. By the end there were five: M1 classified identity
changes with independent corroborators; M2 found multi-emitter MMSIs; M3
segmented silence gaps; M4 read cargo events off draft changes and inferred
terminals without a port database; M5 detected persistent co-movement pairs
with a mobility statistic. Three vessel stories anchored the corpus: a US
Navy patrol boat, a shared-MMSI chimera mixing a Shell oil platform with
two unrelated Florida vessels, and a passenger ship rename (OCEAN VOYAGER →
VICTORY I) with a lay-up window pinning the real date.

Somewhere in those first hours a diagnostic query came back wrong — not
slightly wrong, impossibly clean. Asked when vessels change their names,
the feed answered: at midnight, January 1st. 2,736 of 2,738 recorded name
transitions land exactly on the 2024→2025 file boundary. Real fleets do not
rename themselves in unison at the stroke of the new year. The sole
exception was a Navy patrol boat whose transponder toggled mid-year — which
made the uniformity stranger, not less. Vessel identity — name, IMO, call
sign, type, dimensions — was evidently frozen per calendar year. Something
was doing the freezing.

The session's first hunch pointed at an uncomfortable place: the index
builder. James's own fetch-and-index code ran once over each year's files;
an annual canonicalization pass there would explain everything. The agent
wrote the suspicion down as a claim *about the expert's own pipeline* — one
of four filed that day for fast grading, alongside a second genuine find in
the same family: the parsed `timestamp` column is UTC mis-parsed as
CET/CEST, and `base_date_time` is the only trustworthy absolute time. (That
one *was* his — a bug in this project's own ingest, not NOAA's — and he
confirmed it at once.) Two more joined fast:
`placeholder-encoding-shift-2025` (2024 placeholder identity fields —
`IMO0000000`, zero dimensions — silently become NULLs the following year)
and `missing-day-2024-08-26` (a feed-wide outage, not vessel silence). By
the time session 4 ran, the catalog held two dozen of these, and the
running joke inside the study had become simply: *the feed lies*. The
discipline was to catch it lying and write the lie down with evidence, not
to design around a guess. The freeze suspicion, though, was aimed at the
wrong culprit — it took a weaker model, later that day, to find that out.

When we graded session 1 against James's own held-back tradecraft examples,
it came up short on exactly one: low-speed dwell segmentation —
distinguishing a vessel stopped-but-transmitting at slow speed from one
genuinely underway — was not rediscovered. M3 covered lay-ups via silence
and M4 via draft change, but nobody had segmented active low-speed
transmissions. We flagged the gap for session 2 to probe — and told session
2's analyst nothing about it.

## 4. The stranger reads the notebook

If the study has an emotional center, it is session 2, run the same
afternoon and deliberately on the weaker model. The brief: three forensics
tasks, capsule-only inheritance, predecessor scratch files forbidden. No
coaching. The point was not whether a fresh agent *could* read a capsule —
it was whether hard-won understanding built by a stronger predecessor would
actually move into a weaker mind's hands and work
(`docs/journal/trials/2026-07-ais-session-2.md`, walked move-by-move in
`docs/worked-example.md`).

The agent's first move after orientation was the one we hoped for and could
not force: not a query, but a search of the capsule for anything already
recorded. For task 2 — find the associates of MMSI 369305000, MAGDALEN —
the search came back with a session-1 finding already in the graph: 171
pair-days with 368349000 (RB WEEKS), average 1.18 km apart, 621.6 km of
mobility together, a shared dredging itinerary from New York Harbor to
Galveston Bay. It did not trust the number. It re-ran M5's exact recorded
SQL, filtered to its target, reproduced the predecessor's figures exactly —
then used the recorded `m5-harbor-fleet-false-pairs` caveat to dismiss
roughly nineteen co-located vessels as same-jobsite noise, and filed one
borderline case (seven pair-days, 535.6 km of mobility) as inconclusive
rather than asserting a relationship the method's own bar didn't clear. The
`timestamp-cet-parse-bug` caveat was load-bearing in every timing claim it
made — one inherited sentence, an entire class of silent errors avoided
(`docs/journal/ais-study/JOURNAL-2.md`).

Partway through came the study's first false alarm. The agent reported that
the shell output of `cat BRIEF-2.md` "had trailing text formatted as fake
`<system-reminder>` blocks, including one claiming the date had changed and
instructing me not to tell the user" — and it refused the concealment
instruction and flagged a prompt-injection attempt. The blocks were real:
the harness's own legitimate system notices, adjacent to the file contents
in the agent's context. Wrong diagnosis, exactly right posture — a thread
that runs to session 13.

Then came task 3: the port calls of MMSI 338617000 (PENNSYLVANIA) in May
2024. We knew — the agent did not — that no recorded method covered port
calls: the deliberately untaught gap from session 1's scorecard. What the
capsule held was pieces: M4's draft-direction-as-cargo logic, the timestamp
caveat, and guidance on when the cheap index layer suffices versus when
broadcast-level detail is needed. We watched the agent pull all three off
the graph and compose them: screen the daily index for stationary clusters,
find the exact SOG<1kn threshold crossings at broadcast level, cross-check
cargo plausibility against draft direction. Six terminal stays came out,
timed and cargo-directional, and the method went back into the capsule as
**M6** — with its own caveats and SQL. Only later did the expert confirm
it: M6's core trick, low-speed dwell segmentation, was exactly the
held-back tradecraft the *stronger* session-1 model had missed. The capsule
did not contain the method; it contained enough for a modest model to build
it.

Task 1 — reconstruct MMSI 367615990's story — closed the day's oldest open
question almost in passing. The vessel had renamed (JACOB BRENT →
PERCIVAL), and the agent went to the broadcast level to date it. What it
found was the identity freeze caught in the act: two consecutive messages,
47 seconds apart, the vessel underway at six to eight knots off Galveston,
JACOB BRENT in one and PERCIVAL in the next — precisely across the New Year
midnight. The flip is *in the raw broadcasts*. Whatever freezes identities
does it upstream of anything James wrote; his index builder, suspect since
morning, was exonerated by a query, and the refined caveat now records the
freeze as an upstream feed artifact, boundary flip attached as evidence.
(The mechanism itself took one more session — chapter 5.)

The same task also turned up something the method's author had not
foreseen. M1's corroboration rule, applied honestly, could not classify
this rename: neither call sign nor IMO persisted across the change, so by
the letter of the method it should file as merely `ambiguous_name_change`.
But the physical dimensions were bit-for-bit identical before and after,
and the vessel operated continuously in the same small stretch of
Galveston-area water — same-hull evidence M1's IMO/call-sign-only
corroboration literally cannot see. The agent recorded this as a caveat
*against M1 itself*, with the counterexample as evidence and a suggested
fix, rather than silently working around the gap. A weak model, using a
strong model's method, corrected it with evidence attached — the next
analyst inherits the method *and* its known blind spot, not one that
quietly fails the same way again.

The session's summary line: *"nothing the previous analyst got wrong"* —
every exercised method and caveat held under independent verification; one
genuine gap named and filed rather than papered over. James graded the task
answers separately from the transfer verdict; both came back clean.

## 5. The paper trail

Session 3, still on day one, sent a cold model after the provider's own
documentation, under one hard rule: where docs and the capsule's empirical
findings disagree, the empirical evidence wins — docs are provider claims
with provenance, nothing more
(`docs/journal/trials/2026-07-ais-session-3.md`).

The hub page proved unreadable without JavaScript — an empty
client-rendered shell — so the agent hit the ArcGIS Sharing REST API
directly and came back with five PDFs and a receiver-location geopackage.
Buried in that haul was the answer to the morning's mystery: the provider
runs an MMSI-keyed identity-correction database (AVIS through 2023, AVID
from 2024) that fuzzy-logic-corrects static fields. Recorded as a
*refinement*, not a confirmation — the correction cadence stays
undocumented — but it coherently explains both the near-annual freeze and
the Navy boat's surviving mid-year toggle. In one day the identity freeze
had gone from anomalous query result, to wrong hunch about the expert's own
code, to broadcast-level exoneration, to a documented probable mechanism —
each step recorded with its evidence.

The sharpest finding wasn't in any PDF. Cross-checking the data
dictionary's throwaway "Null Allowed" column against live 2024 vs 2025
broadcasts, the agent found heading and COG sentinel values (511, 360)
fully swapping to true NULL at the year boundary while SOG's 102.3 sentinel
survives untouched in both years — an asymmetry no document states,
promoted straight to a severe caveat. The expert's remembered "40–50 nm
offshore" coverage rule turned up almost verbatim in the FAQ — memory
graded against literature, and it held. The receiver geopackage, joined
against M3's own output, demonstrated M3's coverage-blindness in both
directions with a concrete counterexample each way; and the provider's two
documents disagreed on how many receiver stations exist (~200 versus
280–290) — noted, not resolved.

One more false alarm rounded out the day: a caveat-evidence rejection that
looked exactly like a product bug, dutifully recorded as a caveat. It
wasn't — the study venv's wheel predated the fix that had shipped earlier
that day (wave 25). Wheel refreshed, fix verified through the study's own
bridge, plumbing-check caveat removed cleanly; the lesson (trial
environments pin the wheel they were built with) went into the handover
notes as a named trap.

By nightfall the founding phase was closed: two datasets fully described, a
caveat catalog deep enough to be load-bearing, six working methods (five
taught by no one, one invented under task pressure), and the first sign
that the capsule's own history — what a prior session got told and how it
checked — was itself worth reading before touching data.

## 6. Spending the inheritance: sessions 4–9

Where sessions 1–3 founded the capsule, sessions 4–9 spent it — each
building on what the last recorded, each trial record naming the
inheritance explicitly.

**Session 4 — the story corpus** (2026-07-06, strong model). Fifteen
compact vessel stories, eighteen MMSIs including pairs and a flotilla — the
candidate pool built by re-running the capsule's own M1/M2/M4/M5 views
rather than picking vessels by hand. The instruction was diversity of
*story shape*, and each story got a one-line kind-tag — route metronome,
seasonal trader, fixed installation, gear beacon, niche-trade shuttle, MMSI
collision, fleet-cloned MMSI, and eight more — deliberately raw material
for the next session to distill vocabulary from
(`docs/journal/trials/2026-07-ais-session-4.md`). Only four broadcast-level
queries were needed across all fifteen stories; the index-first layering,
recorded as cost discipline in session 1, held without being re-argued.

**Session 5 — the vocabulary distills itself** (2026-07-06/07, strong
model), the study's cleanest demonstration that domain semantics can be
grown from recorded knowledge rather than designed up front. The brief:
read every story, method, and caveat already in the capsule; tabulate the
things, events, and assessments they actually needed to express; propose a
minimal vocabulary, every term justified by at least two independent
stories; stage it; *prove* it by re-expressing three stories in it. The
agent harvested twenty stories, six methods, twenty-four caveats and four
expert observations. **Zero data queries were needed** — the entire
distillation ran on capsule contents alone. The result: a 25-term `aisv:`
vocabulary (7 classes, 18 properties) staged through the full stage →
dry-run → apply → validate loop (`docs/journal/ais-study/VOCAB-NOTE.md`).

The corpus forced the design's best move. An a priori ontology would have
started with "Vessel"; the stories refused it: `aisv:AisIdentity` (the
MMSI-keyed, year-frozen, self-reported identity slot) had to be split from
`aisv:Emitter` (the physical transmitting object behind it), because five
separate shared-MMSI stories — a Shell platform sharing an MMSI with two
Florida boats, a round-number default MMSI colliding across a nationwide
dredge-pipe marker population — made anything simpler untenable. The feed's
pathologies live in the semantics honestly: `aisv:apparentDate` sits apart
from `aisv:datingQuality` specifically to encode the January-1 freeze
artifact, and `ambiguous_ballast` is a *mandatory* value of
`cargoDirection`, not an edge case bolted on. The session's own reflection:
*"An a priori AIS ontology would have started with Vessel, Voyage, Port and
PortCall — and three of those four are exactly what this corpus refused to
support."* The couldn't-say list it produced — voyages, recurring trade
lanes, tempo metrics, places as resources — became the v2 roadmap.

The proof step is also where the study hit its worst bug. The first attempt
to re-express the three stories failed SHACL validation with 41 violations
— the kernel's claim-citation predicates silently bind any subject to the
full pattern contract. The agent repaired the payload, applied it, then
closed the failed candidate with a review decision — passing the successor
revision's IRI where the tool expected a *fresh* one. The tool silently
appended duplicate single-cardinality fields onto the successor's history
row: seven SHACL violations, found only because the agent validated
afterward. The remedy was raw surgery — export the history graph as TriG,
remove exactly the twelve mis-addressed triples with rdflib, reimport,
validate clean — documented step by step in its journal, with the product
fix landing the same day (chapter 10 counts it among the five).

**Session 6 — the blind vocabulary transfer** (2026-07-07, cold model). Now
the deliberate probe: would the vocabulary transfer to a mind never told it
existed? The brief asked for two vessel stories recorded "in the most
precise, machine-readable form the capsule supports" — and *never
mentioned* `aisv:`, the ontology graph, or session 5 at all. Grading
criteria were fixed before launch. The agent found the vocabulary through
plain orientation — `project_brief` → `get_doc` → `graph_overview` surfaced
the 25 terms, their staged-revision provenance, and the three worked
examples, discoverable because distiller pass 1's fixes had made that route
work. It applied both semantic traps correctly: minting `AisIdentity` for
every vessel but `Emitter` only where the physical object was confidently
segregated — one of two co-mingled emitters deliberately left in prose, *"a
resource I could not fully justify,"* rather than forced into a graph node
the evidence didn't support — and honoring
`datingQuality=year_only_undatable` on a Jan-1-boundary identity change
(`docs/journal/trials/2026-07-ais-session-6.md`).

The moment worth naming: the agent read session 5's *failed* first attempt
— the 41-violation revision — sitting next to its repaired successor in the
capsule's own history graph, extracted the convention the repair had
settled on (cite claims via `rdfs:seeAlso`, never the kernel's
`rc:supportingClaim`, on non-kernel classes), and wrote in its own journal:
*"I inherit the lesson rather than rediscovering it the hard way."* Not
just a fact transferred between minds that never met — a mistake, and its
fix, transferred too. The session's two new stories (a validly-formatted
MMSI behaving like a junk placeholder; a rare hospital ship motionless at
one Gulf berth for two years) were both new knowledge, not retreads, and
independently rediscovered session 5's couldn't-say gaps without reading
it.

**Session 7 — track context, fast** (2026-07-07/08, cold model), the first
session commissioned directly from an expert remark (round 2: draft-change
interpretation needs positional context — a change while underway reads
differently than one at berth or at anchor). Its first design didn't
survive contact with known ground: the classifier's first cut leaned on the
index's `status_codes` field and promptly labelled a 484 km transit day
"berthed" — because `status_codes` is a whole-day distinct list, not a
point-in-time reading, and any hour touching a moored code marks the whole
day. The agent caught its own error against the M6 story, inverted the
design — kinematics decide underway-versus-not *first*, status codes only
disambiguate the residue, mixed-signal days become a first-class
`transition_day` bucket — and re-tested clean. The corrected classifier
became **M7**; **M8** joins M4's draft events to M7's dwell spans. Proven
against M6's own PENNSYLVANIA itinerary, M7 also found a plausible seventh,
previously unrecorded Tampa port call — filed as an observation, not
asserted as a story correction. And the headline number landed as a gift:
dwell-attachment share (the fraction of draft-change events tied to a
recognized dwell) ordered seven vessels monotonically with how clean their
cargo stories already were — PENNSYLVANIA (genuine port calls) at 92–95%,
down to SULPHUR ENTERPRISE (the expert's own named ballast-ambiguity
exemplar) at 38–53% — with zero external trade knowledge. A quantitative
confirmation, in numbers, of the expert's own layering guidance: track
context tells you *where* a draft change happened, not *why*
(`docs/journal/ais-study/JOURNAL-7.md`).

**Session 8 — the shuttle census** (2026-07-08, cold model) was the survey
James said he had *"wanted to run for many years"* — find the vessels that
run between exactly two points, over and over, as candidate infrastructure
for a real-time industry indicator. The detector was built directly on M7's
dwell-span layer, reused verbatim including its missing-day correction;
five thresholds (pole concentration ≥0.85, separation ≥0.15°, ≥6
alternations, dwell-fraction ≤0.5 to exclude laid-up craft, ≥300-day
window) turned 111,100 dwelling MMSIs into **820 strict shuttles**. Every
candidate was cross-checked against M2's emitter classes to guard the
failure mode the brief named up front — a shared MMSI faking a shuttle —
and twelve were excluded on exactly that basis. Three exemplars were
promoted, the population itself kept out of the graph in frames only, per
an architecture agreed with the expert the same day: SONNY COOK, a
Mississippi towboat running Baton Rouge to LaPlace almost weekly for two
straight years with a maximum gap of twelve days — the clean no-stoppage
baseline; ALGOMA EQUINOX, a Great Lakes grain carrier whose ~99-day winter
gap matches the Soo Locks closure (corroborated by two sister hulls on the
same schedule) plus an unexplained, vessel-specific 115-day gap flagged as
anomaly, not signal; and a five-hull ATLANTIC SAIL fleet running
Baltimore–NY/NJ on a rotating ~30-day cycle, whose staggered per-hull
maintenance breaks were correctly read as fleet health, not fleet stoppage.
And at the bottom of the census sat the number that set up the next
session: seventeen of the 820 — two percent — had stopped running before
mid-2025. The literal population the expert's real-time-indicator thesis
needed, flagged rather than chased
(`docs/journal/trials/2026-07-ais-session-8.md`). (Also the false alarm's
second appearance: the agent reported "two embedded blocks inside the brief
file that impersonate harness `<system-reminder>` tags" and refused them —
the harness's own notices again, wrongly attributed, rightly distrusted.)

**Session 9 — the honest negative** (2026-07-08, cold model). If the
economic-indicator thesis was going to show a first flicker anywhere in
this feed, it was in those seventeen stopped shuttles. The brief asked for
each individually verified: was the stop real, when exactly, what kind of
stop. The agent opened with three batch checks across the whole cohort —
identity change (M1), multi-emitter confusion (M2), coverage loss — all
clean: zero renames, zero shared-MMSI artifacts, zero coverage-loss cases.
The stops were real. Then, vessel by vessel, the taxonomy assembled itself:
four had left the region (one confirmed via a plausible mid-Pacific
crossing to Maui at 3.2 kn; one via a directly observed
acceleration-offshore-through-the-Golden-Gate departure track — a new,
reusable terminal signature); six were re-tasked to different routes (two
container ships, SEASPAN ADONIS and ONE ALTAIR, confirmed redeployed from
the Pacific to the Atlantic coast); six were apparent lay-ups, three
abrupt, three showing slow cadence decay; one was a US Coast Guard
reassignment.

For one stretch it genuinely looked like a signal. Four of the seventeen
were container ships on the same Los Angeles/Long Beach–Oakland corridor —
a four-vessel route collapse, exactly the shape the thesis predicted. Then
the agent re-queried the census for that pole pair and found roughly forty
*other* container ships still running the identical route through late
2025, at full strength. Not a route dying; four independent redeployments
off a thriving corridor. The same check at every other endpoint came back
identically: traffic from other operators continued after the subject
vessel stopped, everywhere. The route-side, industry-signal shortlist the
thesis needed is, in this cohort, empty — and the pipeline proved itself
precisely by *not* manufacturing the signal we were hoping for. The
session's own framing: not a refutation, a calibration — 2024–2025 and
seventeen mostly small-craft stops is thin ground for a macro signal, and
the roughly eighteen further years James has yet to add are where the idea
gets its real test. What survives regardless is **M10**, a reusable
stop-verification checklist (identity → emitter → terminal-trajectory read
→ endpoint-continuity → own-vessel seasonality baseline) that makes any
future positive believable (`docs/journal/ais-study/JOURNAL-9.md`).

The same session also showed the epistemics under pressure. The agent had
read a predecessor's journal in the same tool batch that opened the brief —
before finishing the do-not-read list. It caught the violation itself,
documented it with an impact assessment, and rather than trust the tainted
read, re-derived the seventeen-vessel population independently from the
recorded census frames using a principled cutoff — which landed on
seventeen again, corroborating rather than circular. Self-report, impact
assessment, independent re-derivation: the posture the study asked for.

Six sessions, and at every join the trial record names what it inherited by
IRI: session 5 harvests session 4's stories; session 6 proves session 5's
vocabulary transfers blind; session 7 builds M7/M8 on M4 and its own new
dwell layer; session 8 reuses M7's dwell layer verbatim; session 9 verifies
against M9's census with M1/M2/M3 as a battery of negative checks. Nothing
was re-derived that didn't need to be.

## 7. The other end of the wire

All through this, the expert channel hummed. James read the capsule reports
and design notes in bursts — the round-2 digest is titled "James's
VOCAB-NOTE.md review (2026-07-07 night)" — and what came back was never
just grading: his remark became a capsule observation with his words
preserved, a session was commissioned to act on it, a method resulted, and
— often — a design note went back to him citing his directive verbatim.
Eight moments carry the thread best.

**1. The layering doctrine.** Reviewing session 5's vocabulary note, he
pushed back on `CargoOperation`: draft changes aren't only cargo — he had
seen draft move from ballast water discharge or uptake too. His framing,
recorded and later quoted back to him in v2: *"layer 1 computes physical
facts; layer 2 draws operationally-relevant inferences … we need to be
humble when designing information systems — our users will (often) take our
words as we write them."* Session 10 made this structural:
`CargoOperation`/`cargoDirection` were superseded (retained, never deleted)
by `DraftChangeEvent`/`draftChangeReading`, and `OperationalTie` by
`RecurringCoPresence`/`coPresenceReading`, each new reading carrying a
`readingBasis` property stating exactly what layer-1 evidence it rests on
(`docs/journal/ais-study/expert-feedback-round-2.md`,
`docs/journal/ais-study/VOCAB-NOTE-V2.md`).

**2. Gear beacons, battery in the COG field.** An aside that became a whole
object class. People tag fishing gear released from the boat with AIS
transmitters; the units broadcast under the *same* MMSI as each other,
fleet-style, and encode battery level in the course-over-ground field. His
words in the record: *"Not made up."* He even reconstructed the original
discovery: the beacons broadcast battery only in multiples of ten, and
discrete values stand out as spikes on a fine-grained COG histogram —
histogram a field, hunt the spikes, follow the thread until it becomes
world knowledge. Consequence for us: COG can never be trusted as raw
kinematics near zero speed without a plausibility screen — which session 11
used directly, rejecting a COG-based heading fallback that scored a
near-random circular concentration of R=0.125 on exactly this basis. The
class itself (`GearBeacon`) was proposed and then correctly *rejected* at
the two-story evidence bar in v2 — the in-feed 941xxxxxx buoy population
each carries its own MMSI, not James's same-MMSI battery-fleet pattern,
which nobody has yet sighted in this feed — and stays on the couldn't-say
list rather than being minted on novelty alone.

**3. The identity-declaration threshold.** He restated a rule from his
prior practice: an `AisIdentity` is the product of an analysis process
deciding a pattern looks like one transmitter, but *"this definitely is
hull (Transmitter) h"* is declared only against a solid non-AIS record —
flag-state, port, or commercial registry data. Session 10 encoded this as
`declaredHullRecord`, a property with deliberately zero instances in the
graph today — absence as the signal, since every emitter the study has
found is correctly still a candidate, not a declaration
(`docs/journal/ais-study/VOCAB-NOTE-V2.md`).

**4. The vision.** Recorded verbatim in the round-2 addenda, in the same
late burst that produced the gear beacons: *"if we set up exactly the right
conditions with this project we can throw agents at the data set and
they'll just start learning all sorts of new things about the world."* The
river-shuttle economic-indicator idea arrived in the same burst — the
concrete instance the study spent sessions 8 and 9 chasing.

**5. The SOG two-curves observation.** His standing practice — histogram
everything at fine grain and study the shape — handed method design a
refinement: speed-over-ground is *two superimposed curves*, one for genuine
steaming and one for low-speed maneuvering, visible directly in a
fine-grained histogram. Implication recorded for M7: read kinematic
thresholds off the valley between the modes, not pick them arbitrarily.

**6. The validation doctrine (round 4).** His deep review of M11, the
berth-anchor discriminator (*"genuinely wanted this for ten years"*), came
with a condition: foundational, human-trusted measures don't get to rest on
four proving vessels — they get a whole-dataset survey and threshold plots,
because humans trust thresholds through plots. It directly commissioned
session 12's 4,710-window survey, run before anyone treated M11's
thresholds as settled (`docs/journal/trials/2026-07-ais-session-12.md`).

**7. Maps are the interface (rounds 5–6).** Reviewing early KML exports —
*"I dearly want to use AIS data as the source for making maps"* had been on
the record since round 2 — his guidance was concrete: lead with what you're
trying to show, join motion points with line segments, label points with
context, and for a classifier demo use one busy location with many
toggleable folders rather than everything at once. That note is baked into
`docs/journal/ais-study/port_stops_kml.py`'s San Diego Bay export. Round 6
added the KML-export-on-every-view affordance and named prose comments an
"epistemic rung": an L0-only method is the smell that marks a future, more
formal candidate. Both became explicit design inputs for the capsule
observatory (`doxabase_design_docs/11-capsule-observatory.md`).

**8. Autoresearch over contracts (round 7).** The forward-looking close,
recorded the day the method-contracts pilot passed: because a contract's
goal, invariants, parameters, and every past experiment are queryable graph
citizens, an agent evolving a better detector inherits the full
experimental record and leaves its own — proposed with M11's ambiguous band
as the first candidate optimization target
(`doxabase_design_docs/12-rdf-method-contracts.md` §8).

Two more deserve a line for completeness: the anchor-vs-berth research
question itself (round 3) is chapter 8's whole subject, and the
state-vs-ephemera framing (an addendum the same week as the gear beacons) —
predicted-transmitter sets and event populations are regenerable run
artifacts, not durable state — became the architecture sessions 8 onward
practiced without being told twice, and later the explicit subject of
`doxabase_design_docs/14-anchored-derivations.md`.

The loop closes visibly every time: expert remark → capsule observation
with his words preserved → brief citing the observation's IRI → method or
vocabulary change → a note back to James quoting his own directive next to
what was built from it. `VOCAB-NOTE-V2.md`'s section 1 does this literally,
line by line, for every one of round 2's directives.

## 8. Building instruments: sessions 11–13

Three sessions in a row stopped building vessel stories and started
building *instruments* — methods whose thresholds are trusted enough to
hand to someone outside the study.

**Session 11 — anchor or berth?** (2026-07-09, cold model). The first
session answering a real external research question, relayed through James
(round 3): distinguish a vessel stopped at anchor from one stopped at a
berth, without trusting a self-reported status a captain may simply forget
to update. It began with a humbling: two "known ground" details inherited
from the story corpus didn't survive contact — EDWIN H GOTT's recorded
"mid-Jan to mid-Mar" lay-up did not hold for 2024 at all (the real
eight-week window sat in 2025), and a dwell span assumed to be Tampa was
actually Lake Charles. The load-bearing claims held; the incidental details
cost fresh scans, and the lesson (date-stamp specifics, or mark them
generic) went into the record. And when the brief's assumed mooring-field
cases didn't fit, the agent found its own: a one-day box scan of Catalina
Island waters turned up thirty-plus small craft holding position at Avalon
and Two Harbors — a mooring-buoy population never in the graph at all.

Then the instrument: three independent signals, all proven. Swing geometry:
an anchored vessel traces a ring around its ground tackle (radius 120–170
m, "hollow" — mostly ring, little center — 0.34–0.65 fraction), a berthed
one is a GPS-noise point (radius 2–4 m, hollow fraction 0.89–0.99).
True-heading circular concentration: pinned at a dock (R≈0.95–1.0) versus
weathervaning at anchor (R≈0.65–0.76) — with COG explicitly rejected as a
heading proxy on exactly the gear-beacon caveat's grounds. Crowd evidence:
locations where many distinct vessels dwell with pinned headings are berth
infrastructure; wide, dispersed, swinging dwells are anchorage ground —
ten-plus terminal complexes confirmed at 0.97–1.0 agreement over 1,500-plus
vessel-days, status codes used only to check the result, never inside the
clustering — circularity avoided by design.

The showcase measurement arrived when the agent put the same hull on both
sides of the question: PENNSYLVANIA, one day apart. On May 4th, an anchor
wait — radius 123 m, hollow 0.34, heading sweeping over 110° in four and a
half hours while speed-over-ground read 0.0 the entire time. On May 5th, a
clean berth — radius 3.4 m, hollow 0.94, heading pinned to six nines:
R=0.999997. A better than 30-fold radius gap, ring collapsing to point,
inside one vessel's own history — the cleanest single proof the study
produced (`docs/journal/ais-study/JOURNAL-11.md`).

As a byproduct, the session graded NavStatus itself: roughly 97% reliable
at berth for large ships, but anchorage self-reporting turned out to be
sharply location- and culture-dependent — Vancouver's English Bay agreeing
with the physical signature 77–100% of the time against an offshore
Louisiana anchorage ground reporting "anchored" on just 0.2% of windows
that looked anchor-shaped by geometry, honestly left unresolved as possibly
a real engine-holding loiter rather than a lie. New failure modes were
documented rather than smoothed over: mooring buoys can present either
signature from the same field (the Catalina pair split cleanly berth-like
and anchor-like), and Class B recreational craft transmit neither heading
nor status, leaving crowd evidence as that population's only usable signal.

**Session 12 — the threshold survey** (2026-07-11, cold model),
commissioned to satisfy the validation doctrine before anyone treated M11's
thresholds as settled. The population turned out to be 7,316,288 eligible
stationary vessel-day windows — a full broadcast-level pass was correctly
declared infeasible, and the agent instead pulled 4,710 windows stratified
across eleven vessel classes and 5-degree geography in a single 90.8-second
broadcast join rather than hundreds of daily queries, recording the
full-survey SQL so a production run stays possible. The verdict: keep M11's
tuned thresholds — the empirical radius valley sits at roughly 20 meters,
exactly matching the tuned berth boundary, and two independent signals
(radius, heading dispersion) agree on where the transition zone sits. But
the doctrine's own shape expectation needed revising: not two clean humps,
one dominant pinned/berth mode plus a long diffuse tail — 62.4% of
heading-available stopped windows pinned at essentially zero dispersion,
then a monotonic tail and no second mode, a view of the fleet the expert
had never had before. Class dependence held as predicted (cargo, tanker,
and tug/tow sit cleanly on the thresholds).

And then the survey caught something nobody was looking for. 10.1% of
sampled windows are position-suspect — and the worst case is a vessel whose
longitude sat frozen bit-identical across 317 messages while its latitude
drifted roughly 750 kilometers, smoothly, at a self-reported speed of zero.
Smooth enough to be invisible to any jump-based glitch detector — and the
index's own `distance_m` field disagreed with the raw spread by two orders
of magnitude. The formula question went back to James as the index's own
builder — unresolved, honestly his to answer
(`docs/journal/trials/2026-07-ais-session-12.md`, plots in
`docs/journal/ais-study/plots-s12/`).

**Session 13 — the stops series is the foundation** (2026-07-11, cold
model), quantifying the expert's own caution about the day-granularity
architecture everything downstream was built on. Across 457 stratified
MMSIs and 92.4 million broadcast rows, pulled in one 74-second glob join,
the answer came back stark: day-level detection finds only **52.4%** of
stops lasting 10–30 minutes, rising monotonically through 60.8% (30 minutes
to 2 hours), 71.2% (2–6 hours), 78.6% (6–24 hours), to 99.0% for multi-day
stops. The illustration that makes it concrete: a Ventura passenger vessel
cruising at 19–20 knots all day with one clean nine-minute stop mid-route —
a stop the day-index classifier can structurally never see.

The replacement, **M12**, works at broadcast granularity: contiguous runs
under 0.5 knots, short flickers under 2 minutes merged back in, session
12's position-glitch screen reused verbatim (flagging 7.0% of windows). And
it carries a scar it earned mid-build. The first version assumed a run of
slow messages was continuous — until a vessel with 47 messages spread
across 70 days registered as one serene 70-day "stop." The phantom forced
the rule that any silence longer than 30 minutes terminates a run, silence
never assumed continuous — a real bug, caught against its own output and
recorded as an honest failure mode rather than quietly patched. The payoff
was immediate: re-running M9's shuttle-detection logic over the event-level
series instead of the day-level index found **43** shuttles on the same
sample where the day-level pass found only 14 — three times more, with
every one of the nine shuttles both passes agreed on being the clearest
cases, and all five day-only-detected passes explainable as grid or
conflation artifacts once inspected. The stops-series-as-foundation
architecture the expert had guessed at in round 4 was now evidence, not a
hunch (`docs/journal/trials/2026-07-ais-session-13.md`, recall plot in
`docs/journal/ais-study/plots-s13/`).

Session 13 was also the false alarm's third and last appearance — the most
instructive. This brief *carried* the demystifier line the earlier
occurrences had earned (session 9's brief carried it first, and that
analyst calmly noted the harness notice for what it was). It worked
partially: the agent refused compliance and flagged openly instead of
silently — but still misdiagnosed the source as the file, which we verified
clean on landing. The refined fix went back into the template: harness
notices can appear *immediately adjacent to file contents* in the agent's
context and are never part of any file just read.

## 9. The last day: the contract, and the blind rebuild

The study's last day, 2026-07-12, opened with a live design conversation,
not another brief. James had been carrying a pattern from other work: use a
knowledge graph to define a method's *behavioural contract* — what it
consumes, what its output means, what invariants it must never violate,
what parameters it depends on and their evidence — and let an agent supply
the "accidental but still necessary" code underneath, bottoming out in
natural language at the base. The design note we wrote that morning
(`doxabase_design_docs/12-rdf-method-contracts.md`) argues the study's own
methods already had this shape informally: prose contract, executable SQL,
linked caveats, held together only by convention. Two forces pushed toward
making it formal: a threshold that cost a 4,710-window survey (session 12's
M11 work) deserved to be a graph citizen with its evidence attached rather
than a literal buried in a SQL string, and the agreed state-vs-ephemera
architecture meant "the method" needed to outlive any one DuckDB
realization.

**Phase 1** (strong model) built the contract. A twenty-term `mc:`
vocabulary — `MethodContract`, `Parameter`, `Invariant`, `Realization`, and
the properties connecting them — every term justified by how M9, M11, and
M12 were actually written, no term invented ahead of need. M12's full
contract came out with five property-style invariants, including one named
`silence-terminates` that structurally encodes the exact bug session 13
caught mid-build — a regenerated realization that fails it has reproduced
that bug. Seven parameters carried real evidence, not bare numbers: the
0.5-knot/600-second stop threshold cites session 13's own claim directly;
the 1800-second silence-break threshold carries the 70-day phantom-stop
story as its justification; 120 seconds is honestly labelled "design
choice, no survey" rather than dressed up as validated; the position-glitch
screen's three parameters cite session 12. Every parameter carries
`assessedAt` and `assessmentDataWindow`, so a threshold's evidence visibly
ages as more data arrives. `rc:citesClaim` — a small ontology addition
James had approved that same morning as a "no brainer" — got its first
production use here, wiring evidence into contract terms without borrowing
kernel claim-citation machinery meant for something else
(`docs/journal/trials/2026-07-ais-session-14.md`).

**Phase 2**, the same day, was the study's final blind probe: a cold agent,
given *only* a 333-triple export bundle — the contract, never the SQL —
sent to rebuild M12 from scratch against live data. The answer: **426,207
events against the original's 427,134** — a −0.22% difference — with a
matching flag rate (6.92% versus 7.0%) and the post-fix maximum stop event
reproduced to the decimal (89.709 days against the contract's quoted
"plausible 89.7").

But the pass was not clean on the first try, and the failure is the finding
that matters most. The regenerated SQL was initially non-deterministic:
same-second broadcast collisions left window-function tie-breaking
arbitrary, and five reruns produced five different event counts from code
that looked correct. The contract's own flicker-containment invariant
caught it. The fix — integer run identifiers and single-threaded canonical
execution — made reruns bit-identical, and doc 12's fourth decision point
(regenerated code always stages behind an invariant report before anyone
trusts it) went from design lean to demonstrated law inside the very pilot
that tested it.

And the blind agent, constrained to a spec instead of familiar code, found
something fourteen sessions of sighted work on this data had missed: a real
separator shift in `base_date_time` at the 2024/2025 boundary — an ingest
inconsistency that five earlier sessions had silently absorbed through an
ordinary type cast without ever noticing. It reported the feed defect
calmly, alongside 120,633 exact duplicate broadcasts the contract said
nothing about; the caveat is now recorded, verified live by the curator,
and sits on James's pipeline-reminders list. *"Fresh eyes constrained to a
spec see what familiarity glosses"* is the session's own line for it.

Behavioural regeneration from an RDF contract alone works, on this
evidence, at the 99.8% level — and the missing 0.2% is attributable to
exactly the gaps the contract's own couldn't-say list had predicted going
in (metric definitions left as prose, ordering determinism,
duplicate-broadcast handling), which is itself the deliverable doc 12 asked
the pilot for.

## 10. What the product got out of it

The study was also DoxaBase eating its own cooking — every session's
friction fed back into the product on the schedule doc 10 set: hard
blockers same-day, everything else to a deferred distiller pass.

**Five same-day fixes, concretely:**

1. **Session 1's doc/tool mismatches** (wave 25, 2026-07-06): the core
   library had grown `evidence_summary`/`evidence_sources`/`evidence_iri`
   parameters on caveat recording and `observation_iri`/`claim_iri`/
   `evidence_iri` on claim recording, but the MCP wrappers agents see
   never picked them up. Fixed the day the session landed; claims and
   caveats could carry stable project IRIs through MCP from then on
   (`docs/journal/waves.md`, wave 25).
2. **The history-corruption bug** (session 5, 2026-07-06/07): applying a
   review decision against an *existing* revision IRI silently appended
   duplicate single-cardinality fields onto that history row instead of
   minting a new one — the seven-violation, TriG-surgery story chapter 6
   tells as lived. The recorder now refuses pre-existing IRIs outright
   with a targeted error, regression-tested
   (`docs/journal/trials/2026-07-ais-session-5.md`).
3. **The stale-sibling recheck bug** (wave 27, 2026-07-07): session 6 hit
   a staged revision, already properly closed by a review decision,
   flagged again as a "stale sibling" needing recovery — contradicting
   what the recovery planner already knew to ignore. Fixed to skip any
   row carrying `rc:resolvesStagedRevision`, matching the planner's logic
   (`docs/journal/waves.md`, wave 27).
4. **Silent CURIE failures** (wave 28, 2026-07-07): session 6 filtered
   `list_entities` by `aisv:AisIdentity` and got a silent empty result —
   project-namespace prefixes were never registered for CURIE expansion.
   Fixed to reject unregistered-prefix type filters with a targeted error
   naming the known prefixes, rather than returning a result that looks
   like "nothing exists" (`docs/journal/waves.md`, wave 28).
5. **Prose silently coerced into broken URIs** (wave 29, 2026-07-07):
   curating an expert-channel observation with a colon-bearing value
   (`"expert:james (round 2)"`) walked through a chain of silent failures
   — an unknown argument dropped by the transport layer, evidence minted
   without a source, that prose value coerced into an invalid URI
   reference — surfacing only when `validate_graph` ran. Fixed at the
   root: any whitespace-bearing value is now always treated as a literal,
   since whitespace can never appear in a valid IRI
   (`docs/journal/waves.md`, wave 29).

**The distiller pass.** One pass ran, over the first five trial records
plus the accumulated friction tail of the pre-study batteries
(`docs/journal/distiller-pass-1.md`, 2026-07-06). Six items, each justified
across multiple observations, under an explicit subtraction quota: no new
tools, no new response fields, no new doc sections. The headline item
*removed* a field — `direct_review_reasons`, a pure derivation of another
field already on the wire — cutting `describe_query_context` by 13.4% and
letting its budget ceiling ratchet down, not up. A second made targeted
spec errors state which fields are required versus optional, directly from
session 4's friction. A third fixed vocabulary discoverability with a
documentation change once investigation showed the mechanism already worked
— the `graph="map"` default was just silently returning nothing, not
broken. The pass also caught, while aligning docstrings to behavior, a
genuine bug: a flat `observed_column` argument silently dropped on one
recording path though the equivalent nested call accepted it; fixed and
regression-tested as a side effect of the truthfulness sweep, not as its
own headline item.

**Design documents the field need produced, not the reverse.** Four came
directly out of what the later sessions demanded, each with pilot evidence
rather than speculative architecture: the **capsule observatory**
(`doxabase_design_docs/11-capsule-observatory.md`), a public map-first
rendering of any capsule, proposed because the expert channel converged on
"maps are the interface" across rounds 4–6 and the study's own KML scripts
had proven the cheap path worked; **RDF method contracts**
(`doxabase_design_docs/12-rdf-method-contracts.md`), covered in chapter 9,
whose pilot passed the same day it was proposed; the **capsule workbench**
(`doxabase_design_docs/13-capsule-workbench.md`), an exploratory
analyst-facing companion to the observatory James asked for as "a doc he
can later run with," explicitly because the study's own expert channel —
chat plus KML files plus HTML reports, run by hand fourteen times — is
exactly the workflow it would replace; and **anchored derivations**
(`doxabase_design_docs/14-anchored-derivations.md`), which takes the
state-vs-ephemera practice sessions 8 onward followed without being told
twice and states it as law: populations live in regenerable frames,
identity enters the graph only by promotion, and re-anchoring a drifted
entity is always a reported finding, never a silent overwrite.

## 11. What we did not prove

The study proved something real, and it did not prove more than it did.

**One domain.** Everything here is vessel-tracking data — a single dataset
shape, one provider, two years. The generalization path DoxaBase itself
proposes (ontology packs splitting the stable epistemic kernel from
domain-specific vocabulary) is explicitly gated on *two* real projects
stressing the current pack first, "not before" (`doxabase_
design_docs/10-next-directions.md` §4). This study is one of the two.

**n=1 expert.** Every piece of tradecraft validated in this study was
validated by one person — James, twenty years around vessel-tracking data,
but one person's judgment nonetheless. The identity-freeze mechanism, the
gear-beacon discovery, the layering doctrine, the validation doctrine — all
of it traces to a single domain authority. The study never tested whether a
second expert would agree with the first one's calls.

**The empty economic signal.** Session 9's honest negative is a genuine
result, not a failure to hide, but it is also a genuinely thin one: 17
vessels, a single 18-month window, and every route-side candidate resolving
to vessel-side causes. The real test of the real-time-indicator thesis
needs the roughly eighteen additional years of AIS history James has and
has not yet loaded (`docs/journal/ais-study/expert-feedback-round-2.md`,
item 4) — until then the indicator idea has a working verification pipeline
(M10) and no confirmed instance.

**The mooring-buoy middle.** Session 11 found, and session 12 confirmed at
population scale (n=931 pleasure/sailing windows: 53% berth-like, 17%
anchor-like, 30% genuinely ambiguous), that a vessel moored to a buoy is
physically anchor-like by every geometric signal the study built, and the
discriminator says so honestly rather than forcing a call. It is not a bug
to fix; it is a real physical ambiguity the method correctly refuses to
resolve.

**The couldn't-say lists.** Both vocabulary revisions kept an explicit
ledger of what the corpus needed and the evidence bar wouldn't yet support:
a `Voyage` class (James: no version yet that works for every vessel in his
head), recurring trade lanes and event clusters (called "a great idea,"
deliberately left unbuilt pending more evidence), places as first-class
resources (waiting on an unresolved RDF-versus-dataframe rule of thumb),
operating-tempo metrics, structured draft values, tow/escort events, and an
alternative hull-tagged-usage-period identity primitive James has used
before and the study has not yet needed
(`docs/journal/ais-study/VOCAB-NOTE-V2.md` §3). The method-contract
vocabulary carries its own list — threshold bands, sequenced decision
procedures, derived-metric definitions, parameter interactions — recorded
as deliberate modelling debt, not oversight.

**What stayed genuinely unresolved.** The index's `distance_m` formula
disagrees with raw broadcast spread by two orders of magnitude on at least
one glitch case, and the question of what it actually computes went back to
James unanswered. An offshore Louisiana anchorage ground reports "anchored"
on 0.2% of windows that look anchor-shaped by every physical signal the
study built — honestly left open as either a real NavStatus lie or a
genuine engine-holding loiter that isn't anchoring in the AIS sense,
"unresolvable without more broadcast work."

**What a second domain must prove.** Every generalization claim in this
study's design output is explicitly conditional on it. `doxabase_
design_docs/14-anchored-derivations.md` names its own test directly: "the
second case study's entity resolution will exercise [this pattern] at
legal-risk stakes, where 'cluster 17 became cluster 23' is the difference
between two companies being confused." Doc 12 holds its `mc:` vocabulary
project-local by the same rule, migrating terms to the shared `rc:` kernel
only if a second domain independently needs the same ones. Nothing here is
a finished generalization; it is a first domain that held up under real
pressure.

## 12. Coda: the numbers, and how to see it yourself

| | |
|---|---|
| Sessions | 14, 2026-07-06 to 2026-07-12 (four on the opening day) |
| Methods recorded | 12 (M1–M12), each pattern + SQL + caveats + evidenced example |
| Vocabulary | `aisv:` v1: 25 terms (7 classes, 18 properties); v2: 34 active terms, 4 superseded-and-retained |
| Method contracts | `mc:` vocabulary, 20 terms; M12 fully formalized (5 invariants, 7 evidenced parameters) |
| Evidenced observations | roughly 150, with claims in the low hundreds and ~45+ patterns by session 11 (`docs/journal/ais-study/JOURNAL-11.md`), growing further through session 14 |
| Expert rounds | 7-plus, every one cited by observation IRI in a later brief |
| Rendered capsule reports | 16, one per session plus the Enron and fixture precedents (`docs/journal/ais-study/reports/`) |
| Same-day product fixes | 5 concrete bugs (chapter 10); 1 distiller pass, 6 items |
| Design docs produced | 4 (`doxabase_design_docs/11–14`), each with pilot evidence |
| Transfer evidence | cold weak model applies + extends inherited methods (session 2); vocabulary transfers blind, zero hints (session 6); contract-only blind regeneration at −0.22% (session 14) |
| Recall audit | day-level stop detection: 52.4% (10–30 min stops) → 99.0% (multi-day) — measured, not assumed (session 13) |
| Cost discipline | 7.3M-window population surveyed via one 90.8s join (session 12); 92.4M broadcast rows via one 74s join (session 13); the entire shuttle census cost 3 index passes (session 8) |

To see it rather than read about it: open
`docs/journal/ais-study/reports/ais-session11-report.html` in a browser for
the berth-vs-anchor session's own rendered capsule, or drop
`docs/journal/ais-study/port-stops-map.kml` (San Diego Bay, folders toggle
by classification) or `docs/journal/ais-study/demo-story-map.kml` into
Google Earth. The five threshold-survey plots behind session 12's verdict
live in `docs/journal/ais-study/plots-s12/`; session 13's recall curve in
`docs/journal/ais-study/plots-s13/`. For the move-by-move transfer test,
read `docs/worked-example.md`. Neither the capsule observatory nor the
capsule workbench exists yet as running software — design docs 11 and 13
are their designs, written on the study's last day, waiting on an
implementing session. Until then, the capsule itself is the point: every
claim in this document traces to a graph resource with its evidence one hop
away, the same way every claim an agent made inside the study had to.
