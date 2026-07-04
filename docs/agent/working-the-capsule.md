# Working The Capsule

How to work well in a DoxaBase capsule. This is guidance for a capable agent,
not a rule maze: the capsule reports state; you decide what to do. If a
situation here conflicts with what you observe, trust your observation and
say so in what you record.

## What you are working with

A capsule is one SQLite file of named RDF graphs — a project's durable memory
of its data: what is true (`map`), what was noticed (`observations`), what
those notices amount to (`patterns`), what supports all of it (`evidence`),
and how the map came to be this way (`history`). DoxaBase supplies mechanics:
storage, validation, staged change, privacy scanning. You supply semantic
judgement. DoxaBase never runs your queries and never calls an LLM.

## Orientation

`project_brief` is the state of play: counts, datasets, open queues, and —
most importantly — **gates**. `graph_overview` is the cheap structural view.
`search` + `describe_resource` answer most specific questions; prefer them
over reading every doc. When you do read docs, fetch sections
(`get_doc` with `section=`), not whole files.

## Gates

A gate is a condition that blocks a class of action until a human or a
deliberate agent decision clears it. Respect them in this order:

1. **Stale seed recovery** — the shipped ontology/shapes changed under
   existing project data. Until resolved, map validation and staged applies
   are unreliable. Inspect before any mutation.
2. **Staged revision recovery** — a previous session left staged work in a
   tangled or drifted state. Do not stage new work on top of a mid-flight
   recovery chain; inspect the plan first.
3. **Privacy / export review** — an export was requested or prepared.
   A clean sensitive-literal scan is a *review prompt*, not approval:
   scanner-clean means "nothing obviously secret-shaped", not "shareable".
   Only a human (or an explicit instruction) decides shareability.
4. **Incomplete handoff import** — someone handed this capsule state it has
   not fully absorbed. Finish or explicitly abandon the import before
   working the affected graphs.

Read-only inspection is always safe, gate or no gate. Mutation with a
blocking gate up is how capsules rot.

## The epistemic ladder

Record at the level of confidence you actually have; promote deliberately.

- **Observation**: a dated, evidenced notice ("sampled 200 rows on
  2026-07-04; `outcomes` holds JSON-encoded strings"). Always attach
  evidence with sources — validation requires it, and an unevidenced
  observation is gossip.
- **Pattern**: a synthesis over related observations/claims, with confidence
  and stability. Patterns say "this keeps being true", not "do X".
- **Map**: current-best fact. Map changes go through a **staged revision**
  with rationale, then conflict checks, then apply. Stage what the evidence
  supports, not everything mechanically ready: mechanically-ready and
  semantically-right are different judgements, and bundles often contain
  alternatives from which you must *choose one*, not apply all.
- **Reconsideration**: claims are weakened, contradicted, superseded, or
  refined — not deleted. The trail is the product.

`validate_graph` is a diagnostic you run when it will tell you something,
and always after applying map changes. Validation failures are information,
not punishment; fix the data or record why it is right anyway.

## Profiles

Profile evidence describes what a scan of the data actually found. Three
different things can follow, and they should not be conflated:

- ordinary **map drift** (a scalar changed; stage the update);
- a **vocabulary question** (the data wants a metric or value type the
  ontology lacks — that is a modelling decision, keep it reviewable);
- a **caveat** (the data misbehaves in a way future analysts must know —
  often the most valuable outcome of a profile).

## Query work

DoxaBase curates the metadata a query needs; something else executes it.
A good handoff has: relations/paths taken **only** from capsule assertions
(never invented, never "probably"), explicit bindings still unresolved,
the caveats that bear on interpretation, and the review gates a human must
clear before running it. Unverified layout metadata is a finding to record,
not a blank to fill creatively. Never echo anything credential-shaped;
storage access records carry non-secret handles only.

## Staged revisions in practice

- Check before apply; the check is free and names conflicts exactly.
- Drift since staging (the graph changed underneath) → restage rather than
  force; the snapshots make drift precise.
- If staged work has piled up ambiguously, plan a recovery session rather
  than resolving rows ad hoc — it keeps the rationale trail coherent.
- Rationale fields are for the next agent: write why, not what.

## Recording your own session

Leave the capsule the way you would want to find it: findings as evidenced
observations, syntheses as patterns, map changes staged-checked-applied,
dead ends as observations too ("looked, not there" saves the next agent an
hour). If you changed how future agents should work, that belongs in the
project's docs, not in the capsule.
