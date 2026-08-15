# The Know-How Study: A Narrative

*A work-in-progress summary for human readers, ~1,000 words. The
detailed record lives in `doxabase_design_docs/15` and `16`, and
`docs/journal/knowhow-study/`. Last updated 2026-08-15.*

DoxaBase began as memory for data science: a small SQLite "capsule"
of RDF where agents record what a dataset means, what's broken about
it, and why anything was concluded — every claim carrying its
evidence, nothing deleted, only superseded. A months-long field study
on US maritime traffic data proved the mechanism on facts about the
world. This study asks a stranger question: **does the same mechanism
work for know-how** — the tacit competence people accumulate by
doing, the kind that normally evaporates when a person moves on?

The idea arrived on a dog walk. The project's owner noticed that his
own tradecraft — how he decides what to check before trusting a
number, when to stop polishing, what to do with a nagging doubt — was
being *absorbed* by the project's agents through ordinary
collaboration, and wondered whether that absorption could be made
deliberate, recorded, and transferable. The design rule that followed
was the same one that governed everything before it: **don't design
the vocabulary; grow it from cases.**

So we harvested cases. Archivist agents read the project's own
history — session transcripts, commits, the capsule's revision record
— and extracted **episodes**: moments where a way of working showed
itself. A decision with its reasoning. A wrong first instinct,
corrected. A habit of verification that caught a lie. From 249
episodes a vocabulary was distilled, with a rule borrowed from the
project's core: no term exists without at least two recorded
instances. A sealed blind trial then put the machinery to work — two
identical agents given a real design task, one with the distilled
capsule and one with the raw corpus. The capsule condition won, and
the decisive design move traced back to a harvested episode.

Then the owner changed the project's lens, and this was the pivotal
correction. Reviewing the early results, he observed that the episode
vocabulary was fixated on *decisions* — but "the real emphasis of
this project is the progressive build-up of understanding *before*
action is taken." A re-analysis of the whole corpus proved him right
in a way neither of us expected: the most important moment in the
project's public case study — a data anomaly whose pursuit reshaped
everything — had **no episode at all**, because an anomaly is not a
decision. Understanding turned out to have a shape of its own: an
**arc** that opens with an anomaly or a question, pivots on a
reframing, and ends not with a bang but with *automaticity* — the arc
is complete when its decisions stop being decisions. Thirteen arcs
were reconstructed from the record; all thirteen ended that way.
Decisions remained in the model, reframed by the owner's own words:
a decision is the adoption of a frame, "held weakly," with authority
taken for its consequences.

With the vocabulary rebuilt around arcs, we tested transfer. Three
foreign corpora, each in its own capsule, each chosen to break the
vocabulary differently: **year-2000 corporate email** (the Enron
record — compressed, outcome-heavy, formation mostly off-stage),
**Linux kernel patch review** (artifact-interleaved: every objection
answered by a revision that cites it), and **OpenStack code review**
(the same, with finer joins). The results were precise rather than
triumphant. The *spine* transferred everywhere — episodes, arcs,
pivots, the establishment gates. The *idioms* did not: the share of
episodes matching home-grown shapes fell with genre distance (76% at
home, 34% in kernel review, 14% in email), so shapes now carry their
corpus of origin like a dialect label. The foreign material also
taught things home never could: that a terminus is only assertable
when the record outlives the formation; that an applied decision can
*resume being a decision* (the reversal — refused as a term at one
witness, admitted at four); and that in 2026's engineering
communities, **AI participants are already first-class contributors
to formation** — reviewed, refuted, cited in changelogs like anyone
else — which our vocabulary could not say and now can.

The capstone was a benchmark with teeth. The Polymath project —
the famous 2009 experiment in which dozens of mathematicians proved a
theorem in blog comments — is understanding-formation preserved in
amber, in order, with the participants' own retrospectives written
afterward. We sealed an expected-arc registry built *only* from the
retrospectives, hashed it, and then sent a cold agent through the
~1,900 comments chronologically, eight sessions, capsule as its only
memory, every recorded statement anchored to a comment number. A
judge then compared — seal unseen until the agent's output was
frozen. **Verdict: pass.** Every high-confidence arc at least
partially recovered, all five expected dead-ends correctly recorded
as dead-ends, zero fabricated "settled" claims across 394
observations, and all 81 audited anchors verified against the live
2009 pages. The trial's honest boundary is stated in its protocol:
Polymath saturates model training data, so this does not prove
cold-corpus recovery — what it proves is that the machinery can carry
a story *with evidence attached*, across sessions, without ever
outrunning its record. The subtlest result cut against our own
instrument: the ingester found four genuine arcs — all about the
collaboration learning to govern itself — that the participants'
retrospectives never mentioned. The victors' history forgot how they
learned to work together; the chronological record remembered.

Where this stands: five capsules speak one vocabulary; ten heuristics
are promoted with their failure modes attached, and two more entered
by *revival* — refused for lack of evidence, then admitted when a
second corpus supplied the witness the graveyard entry had named. The
sensitivity rules that govern all of it are becoming capsule citizens
themselves. What's ahead: closing the loop, so the agents doing new
work are briefed *from* the know-how capsule and the gain is
measured; a second living contributor's corpus, under a consent
protocol written before his first file arrives; and the same
question, asked again at each step — not "can we store it?" but
"does it carry?"
