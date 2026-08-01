# Design Doc 15: The Know-How Generalization

**Date**: 2026-08-01
**Status**: Research direction with a pilot underway. Grew out of a
recorded design conversation (2026-08-01) and this repo's field-study
evidence; stated here at its honest strength.
**The thesis**: the mechanism DoxaBase built for data-project memory —
the epistemic ladder, evidence-linked mess kept with status, staged
review before durability — generalizes to a memory system for
*know-how*: the tacit, instinctive competence people acquire by doing
and can rarely write down. Fact-memory systems for agents are common;
know-how is the part apprenticeship transmits and books cannot.

---

## 1. Why this is less speculative than it sounds

Two economics changed at once: the writer of the record is an agent
(capture cost near zero) and the reader is an agent (read diligence
total). Every prior know-how capture regime — lessons-learned
databases, wikis, after-action reviews — died on exactly those two
costs.

And the mechanism is not conjecture; this repo has already run it for
a restricted class of know-how. What transferred blind between agents
in the AIS field study was not facts:

- **methods with failure modes attached** — including one invented by
  a weaker agent from inherited pieces and later confirmed as real
  tradecraft the stronger predecessor had missed;
- **a convention learned from a failed attempt** — a cold agent read a
  failed revision and its repair in the history graph and adopted the
  repaired convention unprompted: apprenticeship by graveyard;
- **elicited human tacit knowledge** — nine expert-channel rounds
  converting a domain expert's instinct (field-encoding traps,
  layering doctrine, information-design rules) into recorded,
  evidence-linked guidance that later sessions applied and extended;
- **taste made falsifiable** — thresholds that cite the validation
  surveys justifying them; design judgements stated with acceptance
  tests.

So the honest partition: **the write side, transfer side, and
anti-poisoning machinery (staged review, stance, supersession) are
demonstrated for know-how that transits an agent.** The new bet is the
*capture* side for know-how that does not — the judgement exercised in
a phone call, the noticing that never reaches any context window.

## 2. The existential problem, named

**Sampling bias.** What flows through a working agent is documents,
messages, and the questions its human cannot answer alone — which
skews toward what the human is weakest at, not what they are best at.
Left alone, the system learns the agent's know-how about *supporting*
the human, not the human's own craft. Example, deliberately abstract:
someone excellent at enterprise sales plays three suppliers against
each other by phone, instinctively; nothing of that transits the
agent. The only channel to the good stuff is **sparing, well-timed
elicitation adjacent to events** ("you went with B — what tipped
it?"), rationed hard because human attention is the binding
constraint. This repo's expert channel is nine rounds of exactly that
drip, working; the generalization must make the drip a designed
surface, not a lucky habit. A second extraction runs alongside the
explicit world-model: the **attention model** — what this person
treats as signal, mined from revealed behaviour (what they answer
fast, forward, ignore).

## 3. Design commitments (each inherited from proven practice)

1. **Distill the vocabulary, never design it.** Episode-and-decision
   terms (whatever they turn out to be) get distilled from recorded
   cases with the ≥2-case rule, exactly as the domain vocabulary and
   the method-contract vocabulary were. The project's own history —
   sixteen analyst journals, the expert-channel file, the design docs'
   decision points, full session transcripts — is the first corpus,
   and it already exists. ("I could never have designed this project;
   we had to grow it." — the project owner, on the only method that
   works.)
2. **Skills already have a working form.** The mc: method contracts
   are promoted skills with provenance: behavioural statement,
   evidenced parameters, failure modes, realizations, staged revision
   when wrong. The know-how layer extends this pattern to
   non-executable skills — heuristics whose invariants are judgement
   tests rather than generated checks. (Far-future note: a mode
   serializing a capsule's point-in-time skill set to plain skill
   files for locked-down deployment.)
3. **Worker/archivist split.** The working agent just works; an
   offline archivist harvests transcripts afterwards into staged,
   evidence-linked episode observations. Bootstrap is the same
   archivist run once over the backlog instead of nightly — one
   pipeline, one review gate, one capsule.
4. **The archive role reuses the frames machinery.** Transcripts,
   mailboxes, and document piles are big immutable non-semantic
   assets: exactly what the described-dataset + SourceSpan +
   anchored-derivations stack (docs 13/14) already manages. Immutable
   sources, immutable inferences, later passes superseding earlier
   ones with lineage — the reconsideration machinery applied to an
   archive.
5. **Interview design is a graph query.** Elicitation minutes are the
   scarcest resource, so the questions are computed: contradictions
   the corpus surfaced, load-bearing inferences (literally
   high-in-degree claims), and a calibration spot-check. Present
   claims to confirm or correct, not open questions — a
   confidently-stated slightly-wrong claim provokes the correction
   that carries the tacit reasoning. The interview validates the map,
   not the pile; the pile is allowed to be wrong in places.
6. **Legibility of learning is a product feature.** A junior earns
   patience by visibly learning; so does this system — questions that
   reference last month's answers, a visibly growing map, "you told
   me X and I have now seen it play out in Y." Conversation style
   adapts per person (some review long documents in bursts; some want
   a weekly five-minute drip); agents are good at that.

## 4. The pilot (underway)

Subject: this project's own design history — product-design know-how,
one step removed from the instrument (the capsule under test is a
fresh, separate one; the tool is merely the harvest target's subject
matter). Stages: (1) archivist harvest of the existing corpus into
evidence-linked episode observations, free-form first; (2) vocabulary
distilled from the harvested episodes once they exist in numbers;
(3) a pre-committed evaluation — fresh agent with the know-how capsule
vs without, on design tasks from the demo-app build, criteria sealed
before the trial, blind judging by a separate instance. The trial
protocol is the field-study protocol, unchanged. Success is the same
bar as ever: the human who owns the know-how recognizes their own
judgement coming back at them, applied correctly to a case they never
discussed.

## 5. Relationship to the demo applications

The public demonstration applications (doc 11's observatory line) are
both the attention strategy and the forward corpus: building them
generates design episodes (what made an interface feel fast, what a
five-minute visitor engages with vs a two-hour user) with hallway
testing as external ground truth. Their operating principle doubles as
this document's epistemics in public form: every rendered analytic
carries its "how this is known" panel — the app asserts what the
evidence supports, shows provenance, and leaves conclusions to the
reader. Bounded monthly cost is decided before building, per app.

## 6. What would falsify this

If the pilot's A/B shows no recognizable advantage; if elicitation
cannot be made cheap enough that the human sustains it; if the
attention model proves unminable from behavioural residue; or if
sampling bias resists the drip — then the honest conclusion is that
the mechanism is domain-memory only, and this doc gets superseded the
way anything else here does: with its evidence attached.
