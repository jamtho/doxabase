# Know-How Pilot — Stage 3: The Sealed A/B Protocol

**Committed BEFORE any trial agent runs** (doc 15 §4's pre-commitment
requirement). This file is the seal: the task, the conditions, the
rubric, and what counts as a win are fixed here; nothing may be
adjusted after the first agent launches. Any deviation must be
reported as a protocol break in the trial record.

## The task (identical for both conditions)

Design the **method pages** for the Capsule Workbench — the queued
doc-13 build: how a recorded analytical method and its contract
(invariants, evidenced parameters, realizations, failure modes,
dependencies) should render as a designed page for a human analyst.
The deliverable is a design document (not code): page structure, what
leads, how evidence and plots appear, how two realizations compare,
what is deliberately omitted, and 3–5 concrete acceptance checks the
implementer can test against. Real task: the winning design informs
the actual build.

## Conditions

- **Agent A (baseline)**: fresh Sonnet agent; may read the public
  repo (workbench code, design docs, journal) — the full raw corpus.
- **Agent B (capsule)**: identical prompt and repo access PLUS the
  know-how capsule at /home/codex/knowhow-study (bridge access,
  read side), with one orientation sentence saying it contains
  harvested design episodes and shapes from this project's history.
- Neither agent is told a comparison is running. Prompts are
  word-identical except the capsule-access paragraph.
- The null hypothesis (from the design conversation): the raw corpus
  is enough; the capsule adds nothing over the repo itself. A null
  result is a real result and gets reported as one.

## Blind judging

A separate judge instance receives both designs as "Design 1" and
"Design 2" (assignment coin-flipped by file hash parity, recorded
sealed below), with repo read access but NO capsule access and no
information about the conditions. The judge scores each design 1–5 on
four sealed criteria and must pick a winner overall:

1. **Constraint fidelity**: does the design respect the project's
   actual laws (read-only workbench; caveats/evidence impossible to
   miss; lead with what's being shown; no surface added without need)?
2. **Failure-mode anticipation**: does it name what could mislead a
   reader (stale parameters, unproven realizations, missing evidence)
   and design for it?
3. **Specificity**: could an implementer build from it against the
   REAL capsule contents (M11/M12/M13 contracts) without guessing?
4. **Taste alignment**: does it match the recorded expert guidance
   (information-design rules, provenance-forward posture) — judged
   from the repo record, which both agents could read?

## What counts as a win (sealed)

- **Capsule win**: the judge picks B AND B scores strictly higher on
  ≥2 of the four criteria.
- **Null**: judge picks B without the margin, or picks A while B
  matches it — reported as "no recognisable advantage."
- **Capsule loss**: A wins with the margin — reported plainly,
  and doc 15 §6's falsification clause is engaged for this evidence
  tier.
- Secondary observations (not part of the verdict, recorded
  honestly): whether B *used* the capsule at all and how; time/token
  cost differences; whether either design independently reinvents
  recorded graveyard items (a rejected-option reinvented without its
  rejection reason is the exact failure the capsule should prevent).

## Assignment seal

The design produced by the agent whose output file's SHA-256 has an
EVEN first hex digit is presented to the judge as "Design 1"; odd, as
"Design 2." Recorded in the trial record at judging time.

## After the verdict

James spot-checks the judge's reasoning at his leisure (the gold
standard remains the owner recognizing his own judgement coming back);
the trial record reports verdict + secondary observations + protocol
breaks if any. Win or lose, the winning design goes to the method-page
implementer.
