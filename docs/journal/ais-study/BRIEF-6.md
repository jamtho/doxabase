# AIS Study — Session 6 Brief: Two Stories, Built to Last

You are the sixth analyst. Five predecessors and a domain expert built
the capsule: datasets mapped, methods recorded as patterns with
executable views, a deep caveat catalog, provider documentation
reconciled, and a corpus of vessel stories. Your job is depth and
durability: TWO new vessel stories, recorded so well that a future
*machine* analyst can consume them without reading any prose journal.

## Interfaces (as ever)

- Capsule ONLY via `venv/bin/python bridge.py tools` (once → tools6.json)
  and `venv/bin/python bridge.py call <tool> '<json>'`; for payloads with
  quotes/apostrophes write the JSON to a scratch file and pass
  `@args.json`. Orient FIRST and thoroughly: brief, docs, methods,
  caveats, expert observations, and the existing story conventions —
  match or beat their quality bar.
- Data ONLY via `venv/bin/python query.py "SQL" --max-rows 40`. Never
  echo credentials. Do not read predecessors' scratch files (JOURNAL-*.md,
  BRIEF-1..5, VOCAB-NOTE.md, tools1-5.json, expert-questions.md) or
  /workspaces/doxybase.

## Task

Two vessels, not already storied (verify via search), chosen from the
capsule's recorded views for maximum story value: prefer one
identity-complicated subject (reassignment / shared MMSI / rename) and
one operationally interesting subject (cargo cycles, seasonal pattern,
or a non-ship curiosity). Work each up properly: identity history with
real-timing assessment, physical claims, operating pattern, notable
events — every load-bearing statement evidenced, methods cited by IRI.

**The durability requirement**: record each story in the most precise,
machine-readable form the capsule supports. Before writing, survey what
the capsule itself offers for expressing vessel histories — use
everything the graph gives you, and note in your journal what you could
NOT express precisely. A future analyst should be able to answer "what
happened to this vessel, when, with what confidence?" from the graph
alone.

## Discipline

Budget queries (index first, broadcasts only for decisive checks). Keep
`JOURNAL-6.md`. Follow the capsule's own write rules — if a write path
demands review or staging, do it properly; validate the graph
(scope "all") at the end and leave it conforming with no orphaned
staged revisions.

## Final report

(1) which vessels and why; (2) the story of each in six lines; (3)
exactly HOW you recorded them — which graph resources, which types,
which properties, and why you chose that form; (4) what you could not
express precisely; (5) which recorded methods/caveats you used, by IRI;
(6) friction notes.
