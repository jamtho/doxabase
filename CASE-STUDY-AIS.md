# Case Study: Fourteen Sessions on the AIS Feed

*What it is like to work with DoxaBase, told through a real study.
(Interim version written by the project's resident agent; the
maintainer intends to rewrite it in his own voice. The underlying
records — session briefs, analyst journals, graded trial records, and
rendered capsule reports — are all in `docs/journal/`, and every claim
below links to them. For the full chapter-by-chapter narrative of all
fourteen sessions, see `docs/case-study-ais-full.md`.)*

---

## The setup

One domain expert (twenty years around vessel-tracking data). Two
years of NOAA AIS broadcasts — 92 million position reports — in an S3
bucket. A sequence of AI analyst sessions, most of them deliberately
*cold*: a fresh agent with no conversation history, no notes, and no
access to its predecessors' scratch files. The only thing allowed to
carry knowledge between them: a DoxaBase capsule.

The question the study was built to answer: **can hard-won analytical
understanding actually transfer between minds that never met — with
its evidence and its failure modes attached?**

## What happened, in brief

Fourteen sessions between 2026-07-05 and 2026-07-12. The capsule
started empty. By the end it held: descriptions of both datasets with
a deep caveat catalog (the feed lies in at least a dozen documented
ways); **twelve recorded methods** (M1–M12), each with executable SQL,
rationale, and known failure modes; a 25-term domain vocabulary
distilled from recorded cases and revised once against expert review;
formal behavioural contracts for the newest methods; and roughly 150
evidenced observations, including seven rounds of expert testimony.

Some moments that make the case:

- **The transfer test** (session 2, deliberately run on a *weaker*
  model): a cold agent inherited the capsule, applied its predecessor's
  co-movement method by IRI, reproduced its numbers exactly, dismissed
  false pairs using a recorded caveat — and then *invented a new
  method* (low-speed dwell detection) by composing three recorded
  pieces. The expert confirmed the invention as genuine tradecraft the
  stronger predecessor had missed. It also found a counterexample to
  an inherited method and recorded the gap as a caveat, so the next
  analyst inherits the method *and* its blind spot.
  (`docs/journal/trials/2026-07-ais-session-2.md`, and the
  human-facing walkthrough in `docs/worked-example.md`.)
- **A mistake transferred, not just knowledge** (session 6): a cold
  agent, never told the domain vocabulary existed, found it by plain
  orientation — and then read a *failed* revision and its repair in
  the capsule's history graph, and adopted the repaired convention
  with the words "I inherit the lesson rather than rediscovering it
  the hard way."
- **A ten-year question answered in an afternoon** (session 11): the
  expert had wanted a physical berth-vs-anchor discriminator for a
  decade. A session built one on three signals (anchor-swing ring
  geometry, heading weathervaning, crowd evidence) with a 30× margin
  on the showcase case — then a follow-up session surveyed 4,710
  stationary windows across the whole feed to validate the thresholds
  with plots, because a threshold humans are meant to trust deserves
  a survey. (`…session-11.md`, `…session-12.md`, plots in
  `docs/journal/ais-study/plots-s12/`.)
- **The honest negative** (session 9): 17 shuttle vessels had stopped
  running — the seed of a real-time economic indicator the expert
  hoped for. Verification resolved *all seventeen* as vessel-side
  (redeployments, departures, lay-ups): the indicator signal was
  empty, and the report said so plainly instead of manufacturing it.
  What remained is the verification checklist that will make any
  future positive believable.
- **Contracts that regenerate code** (session 14): the newest method
  was formalized as an RDF behavioural contract — invariants,
  evidenced parameters, the SQL as one labelled realization. A cold
  agent given *only the contract* (never the SQL) reimplemented the
  method at 99.8% agreement, the contract's invariants caught real
  non-determinism in the regenerated code, and the blind agent found
  a feed defect five sighted sessions had silently absorbed.
  (`…session-14.md`, design in `doxabase_design_docs/12-…`.)

## The expert channel

Between sessions, the expert reviewed outputs and spoke tradecraft —
which was immediately recorded as evidenced observations. Seven rounds
of this produced, among much else: the layering doctrine (physical
facts vs interpretations, each reading carrying its basis), the
identity-declaration threshold (an AIS-inferred vessel is a
*candidate* until a non-AIS record anchors it), the validation
doctrine (foundational measures get whole-dataset surveys and
threshold plots), and map-first information design. Sessions
commissioned directly from expert remarks turned them into methods
within hours. The knowledge flowed both ways: sessions found four real
defects in the expert's own ingest pipeline, each verified and queued
for him with evidence.

## What the product got out of it

The study is also how DoxaBase eats its own cooking. Field sessions
surfaced ten-plus product defects — from silent identity coercions to
a history-corruption bug — each fixed same-day with a regression test.
Larger lessons accumulated in a ledger and were acted on in batched
"distiller passes" rather than reflexive feature growth; the first
pass *removed* a response field and made errors state required vs
optional fields. Two open design documents (the capsule observatory
and the method-contract system) exist because the study demanded
them, with pilot evidence attached.

## The numbers, plainly

- 14 sessions; 12 methods; 2 vocabulary versions; ~150 evidenced
  observations; 7 expert rounds; 16 rendered capsule reports.
- Transfer: a cold weak model applied inherited methods correctly and
  extended them (session 2); a blind vocabulary transfer passed with
  zero hints (session 6); a blind reimplementation from contract alone
  hit −0.22% (session 14).
- Recall audit: day-granularity stop detection finds 52% of
  10–30-minute stops (rising to 99% multi-day) — measured, recorded,
  and now the foundation layer is event-level (session 13).
- Cost discipline: the 7.3M-window survey ran as ONE 90-second
  broadcast join; the whole shuttle census cost 3 index passes.

## If you want to see it rather than read about it

Open `docs/journal/ais-study/reports/ais-session11-report.html` in a
browser (the berth-vs-anchor session), or drop
`docs/journal/ais-study/port-stops-map.kml` into Google Earth and
toggle the classified-stop folders. Then read
`docs/worked-example.md` for the move-by-move version of the transfer
test. The capsule itself is the point: everything above traces to a
graph resource with its evidence one hop away.
