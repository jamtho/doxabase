# AIS Study — Session 4 Brief: The Story Corpus

You are the fourth analyst. Three predecessors and a domain expert built
the capsule: datasets mapped, five-plus methods recorded as patterns with
executable views, a deep caveat catalog, provider documentation
reconciled. Your job is breadth: a corpus of vessel stories that future
sessions will distill domain semantics from.

## Interfaces (as ever)

- Capsule ONLY via `venv/bin/python bridge.py tools` (once → tools4.json)
  and `venv/bin/python bridge.py call <tool> '<json>'`. Orient first:
  methods, caveats, expert observations, and the three existing vessel
  stories (pattern/vessel-*) — match their conventions and quality bar.
- Data ONLY via `venv/bin/python query.py "SQL" --max-rows 40`. Never
  echo credentials. Do not read predecessors' scratch files (JOURNAL*.md,
  BRIEF-1/2/3, tools1-3.json, expert-questions.md) or /workspaces/doxybase.

## Task

Produce ~15 compact, evidenced vessel stories (pattern/vessel-<mmsi> +
supporting claims/observations, following the existing story format).

**Selection is part of the work**: use the capsule's own recorded views
to build a candidate pool — suspected MMSI reassignments (M1 view),
multi-emitter MMSIs (M2 view), co-movement fleet members (M5 view),
draft-cycle workhorses (M4 view), plus a few high-mileage or unusual-type
vessels of your own choosing. Pick for DIVERSITY of story shape: at least
2 from each method-derived class, at least 2 non-ship objects if you can
find them (the expert says curiosities are where the value lies:
platforms, helicopters, buoys, dredges), and nothing already storied.
Record your selection rationale as an observation before starting.

**Each story** (compact — half the depth of the existing three is fine):
identity + changes (with real-timing assessment per the identity-freeze
caveat), physical claims, operating pattern, notable events (use the
recorded methods where they apply — cite their IRIs in your evidence),
and one line on what KIND of story this is (rename? reassignment?
shared-MMSI? fleet workhorse? seasonal trader? anomaly?). That kind-line
matters: a later session will distill vocabulary from it.

## Discipline

Budget queries (index first, broadcasts only for decisive checks). Keep
`JOURNAL-4.md`. Record stories as you complete them, not in a batch.
Validate the graph (scope "all") at the end.

## Final report

(1) the selection pool and rationale; (2) one line per story: MMSI, name,
kind, the single most interesting fact; (3) which recorded methods you
used, by IRI, and any new method gaps found; (4) friction notes.
