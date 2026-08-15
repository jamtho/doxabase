# Design Doc 17: The Capsule as Long-Term Memory

**Date**: 2026-08-16
**Status**: Design from a live owner-curator discussion (both rounds
recorded in the know-how capsule), written while the ideas are fresh
and explicitly subject to the program's usual law: the designs below
get tested, and the tests are allowed to kill them.
**The thesis (the owner's, quoted)**: put "a bunch of rather fuzzy
but fundamentally well-shaped in aggregate information in an agent's
context window [and] it's going to be able immediately to take
decisions that make excellent sense in the domain that context
covers... Like humans, LLMs can find the shape of sense in a bunch of
messy but fundamentally sound information." The context window cannot
hold all the useful background — so the graph structure is the
answer: "like a human brain that recovers a series of memories
through connection, the second by its relation to the first... the
graph lookup machinery we offer the agent lets it pull into context
at least a decent approximation to what's useful and relevant."
Implication, his: **we are storing far too little in the capsules.**

---

## 1. Evidence already in hand

Three of the program's own results support the thesis before any new
work:

1. **The A/B trial** gave two agents the same information in two
   shapes; the capsule shape won, and the decisive move traced to a
   harvested episode. Structure, not volume, was the active
   ingredient — retrievability-along-relations is what the graph
   buys.
2. **The Polymath ingest** ran nine sessions over a corpus no context
   window could hold, with the capsule as the only continuity, and
   passed a sealed benchmark. Working memory vs long-term memory,
   already demonstrated in production.
3. **The consumption trial's brief was the associative walk done by
   hand**: a protocol author selected 11 heuristics and 5
   task-relevant arcs from the graph for the moment at hand. The
   verdict (null with a pointed signal) showed the *gated* behaviours
   are already enforced by the platform — the value concentrated
   exactly where no gate reaches: the agent's live judgement. That is
   the surface retrieval feeds.

And one quiet corroboration: humans consolidate — re-encoding
episodes into semantics offline. The program built that organ before
having the theory: the distillers are the sleep cycle. An analogy
that retro-predicts architecture grown independently from cases is
probably load-bearing.

## 2. Design commitment 1 — liberalize the observation tier

The storage deficit is tier-specific. The vocabulary tier is
correctly starved (the ≥2 rule, refusals, the graveyard — that
discipline is why the map stays trustworthy) and nothing changes
there. The under-populated tier is **observations**: cheap,
append-only, individually unremarkable, valuable in
aggregate-plus-retrievable. The ≥2 rule gates terms, never records.

Concretely:

- Harvest and working briefs drop their implicit volume restraint:
  a session that would have recorded 50 observations records what the
  material actually holds — 200, 400. Dense agent-written prose in
  literal values is welcome; that compression is a feature (the owner:
  the detail is often more useful than the formal output, especially
  while a project is young).
- Working agents journal INTO the capsule as they go, not only into
  markdown. The journal file remains the human-readable render;
  the observation stream is the durable, retrievable original.
  (The consumption trial's decisive failure was a journal
  contradicting its own graph — this commitment dissolves the gap by
  making the graph the journal's source.)
- The quarantine principle (doc: concurrent-capsule thinking) bounds
  the move: volume flows into the observation tier; agents ORIENT on
  the promoted map; the deep store surfaces only through retrieval.
  Promotion gates unchanged. Indexicality discipline (assessedAt,
  windows) matters MORE at volume, not less.

## 3. Design commitment 2 — retrieval as the product surface

Under the thesis, retrieval stops being a convenience and becomes the
product's main surface — and the friction ledger already knew: nine
sightings of history-rows-outranking-live-nodes, literal-only search,
no graph filter. The target capability:

**Budgeted working-memory assembly**: given a task description and a
token budget, walk the graph from the best entry points and return
the neighborhood that matters. The ladder supplies the relevance
machinery for free — tier weights (map > patterns > observations),
supersession-awareness (the reconsidered is excluded or flagged,
never silently served), assessedAt decay, and typed edges
(citesEpisode, showsFormationOf, supportingObservation, leadsTo) as
the associations the walk follows.

Per the owner's instinct, build it twice:

- **v0 — the simple version (days, no product surface change)**: a
  convention plus a helper script. Entry points from k search calls;
  one-hop typed expansion; ladder-weighted trim to budget; render.
  Runs bridge-side today. Its job is to make the live-retrieval trial
  possible NOW and to generate the usage data the proper version
  needs.
- **v1 — the proper version (product work, budgeted)**: a capsule
  tool (`assemble_context` or similar) doing typed-edge spreading
  activation with tier weights, decay, and two parameters:
  `budget` (tokens) and `provenance_mode`. It subsumes several
  ledgered search complaints and is the natural headline of the next
  product batch.
- **Provenance is a parameter, not a decision** (the owner's call):
  `digest` (clean prose, fastest to read), `handles` (every item
  carries its IRI so the agent can pull the thread — the curator's
  prior), `full` (evidence chains inline). Which mode wins is decided
  experimentally, per trial, exactly like vocabulary distillation —
  different trial arms are instructed to use different modes.

## 4. Design commitment 3 — re-contextualization (the owner's new idea)

Humans alter memories as "proper salience of elements becomes more
apparent with later wisdom." The capsule must get the benefit without
the human bug: **observations stay immutable; salience lives in a
relink layer above them.**

- **Relink edges**: later-minted links between observations (and from
  map/pattern nodes down into old observations), added as the map
  evolves — "this old record matters for X, seen only now." The arc
  machinery already did this once: ARCS-1 typed 41 prose
  cross-references into edges years of subjective time after the
  records were written. Generalize that act into a standing practice.
- **Resalience observations**: annotation records ABOUT older
  observations ("with the v3 vocabulary this 2026-07 record reads as
  an onset"), append-only like everything else. The original is never
  rewritten — reconsolidation without falsification. Supersession
  already implements this pattern for claims; this extends the same
  move to significance.
- **Who mints them**: the distillers, as part of every pass (they are
  the sleep cycle; re-indexing the deep store is consolidation), and
  eventually the retrieval layer itself — a walk that surfaced an old
  observation which then proved decisive is evidence of salience
  worth recording. (Retrieval-frequency as edge strength is the
  obvious signal and carries an obvious popularity-bias risk; noted
  as an unknown, not adopted.)

## 5. The falsification test

The next-diameter consumption trial doubles as this doc's acceptance
test: **static render vs live retrieval**, on a task family the
heuristics were NOT distilled from (closing the prior trial's
narrowest-diameter caveat), with:

- the v0 assembler as the live arm's mechanism;
- `provenance_mode` as a trial parameter (the owner's experimental
  answer to the interface question);
- **retrieval precision** measured: of what the walk pulled into
  context, how much was actually used (cited, echoed, acted on)?
  Pulled-but-unused is the walk's noise floor; needed-but-unpulled
  (visible in the agent's own searches after assembly) is its recall
  gap. Both are numbers, not aesthetics.

The thesis predicts live retrieval wins where relevance shifts
mid-task. A null here would say the assembly can be done as well
statically at briefing time — also worth knowing, and cheaper.

## 6. Honest unknowns

Relevance-weight ground truth (the ladder gives priors, not answers);
when relink edges become noise rather than signal (the graveyard may
need a salience analogue); whether observation-tier volume degrades
the workbench's human legibility (probably needs tier-aware views);
SQLite's ceiling under order-of-magnitude growth (fine for a while;
the concurrent-capsule postgres path exists when it isn't); and the
deepest one — whether "well-shaped in aggregate" survives volume, or
whether unpromoted bulk eventually drowns the shape it is supposed to
carry. The quarantine principle is the design answer; the trials are
the test.

## 7. Immediate steps

1. Liberalized recording language goes into the next harvest and
   working briefs (cheap, reversible, effective immediately).
2. The v0 assembler script (bridge-side, days).
3. The live-retrieval trial protocol, sealed in the house style, once
   v0 exists.
4. The next distiller pass mints relink/resalience records as part of
   its normal work — consolidation becomes an explicit duty of the
   organ that was already doing it implicitly.
