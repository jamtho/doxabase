# DoxaBase — Next Directions (post-distillation)

**Date**: 2026-07-05. **Status**: proposal for James, written at his request
after the Distillation Program closed. Nothing here is committed work; the
sequencing at the end is the recommendation.

## 1. The trial loop, rebuilt on James's insight

The V1 loop's failure was not running trials — the trials were the best
part — it was letting every trial write to the product immediately. The
replacement architecture, adopted as this project's standing practice:

- **Recorded trials, deferred action.** Trials (including long, real-work
  sessions) produce *records only*: full call logs with char accounting,
  the agent's own friction notes, and outcomes against a rubric. They go to
  `docs/journal/trials/` untouched.
- **A distiller pass, later and rarely.** A separate agent — explicitly
  tasked with preserving simplicity and conceptual clarity, reading the
  *whole* accumulated result set — proposes at most a handful of changes
  per pass, each justified across multiple trials, each obeying the
  subtraction quota. One distiller pass per N trials, not per trial.
- The scoreboard stays the arbiter between passes. Single-trial fixes are
  banned except for outright bugs.

This is what the Distillation Program itself did at project scale; the
proposal is simply to never again run the other kind of loop.

## 2. James's real-work sessions as field trials

The next product signal should come from real work, not fixtures. Protocol
for those sessions (cheap, mostly automatic):

- Run the capsule through the logged bridge (or an MCP client with
  logging); keep the per-call char log.
- The working agent keeps a **session journal**: what it wanted, what it
  called, what surprised it, where it hesitated — written for the
  distiller, not as instructions.
- At session end: one paragraph from James — what felt heavy, what felt
  invisible-in-a-good-way. Human friction is signal the agent can't emit.
- Nothing gets fixed mid-session unless it's a hard blocker.

## 3. Human visibility

Two distinct needs James named, both worth building:

**3a. Capsule report (dataviz).** A generator (`tools/capsule_report.py`
or `doxabase-report`) that renders one capsule to a single static HTML
file: dataset cards (columns, caveats, storage state), the observation →
pattern → map promotion lineage as a graph, revision/staged timeline,
queue and gate state, and graph counts over time from history snapshots.
Static single-file output keeps it inside the privacy posture (it is an
*export artifact*, so it goes through `export_preflight` and carries the
shareability banner). This is the highest-leverage humans-can-help move:
James reviewing a rendered capsule will find modelling smells no trial
agent reports.

**3b. Worked examples in docs.** We already possess the raw material: the
trial transcripts (battery runs, the Enron session) are exactly "an agent
using it, the MCP calls, the truncated data, the reasoning." Proposal: one
new doc, `docs/agent/worked-example.md` (budgeted like any other), built
from the strongest transcript — annotated call-by-call: *why this call,
what mattered in the response, what was ignored, what decision followed*.
Kept truthful by regenerating against the live surface when tools change
(the gen-docs drift-test pattern extends to it).

## 4. Generalisation beyond data projects

The epistemic kernel is already domain-neutral: observations, claims,
evidence with source spans, patterns, reconsideration, staged promotion
into a reviewed map. What is data-specific is the *descriptive* vocabulary
(Dataset/Column/StorageAccess/PhysicalLayout...) and the two workflows
built on it (profiling, query planning).

The generalisation path, when wanted, is **ontology packs**:

- Split `rc_core.ttl` conceptually into the epistemic kernel (stable,
  shared) and the data-domain pack (one of several).
- A pack = descriptive classes + SHACL shapes + (optionally) pack-specific
  helpers and doc pages. The recording/staging/validation/export machinery
  needs nothing new.
- Good early fits share three properties: durable artifacts worth
  describing, repeated observation of the same subjects over time, and
  high value on caveats/provenance. Candidates: codebase archaeology
  ("why is this module like this"), lab/experiment logs, operational
  incident knowledge, literature review.
- **Not yet.** Two real data projects should stress the current pack
  first; generalising from n=1 fixtures is how V1 grew wrong.

## 5. Recommended sequence

1. **Now**: James's real-work sessions with the recording protocol (§2) —
   several, without intervening fixes.
2. **Next**: capsule HTML report (§3a) — small, self-contained, improves
   every later step including James's own sessions.
3. **Then**: worked-example doc (§3b) from the best real-session
   transcript; first distiller pass (§1) over the accumulated records.
4. **Later**: ontology packs (§4), only after external-project evidence;
   revisit the deferred SPARQL question with the same evidence.
