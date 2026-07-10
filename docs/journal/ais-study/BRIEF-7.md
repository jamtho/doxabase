# AIS Study — Session 7 Brief: Track Context, Fast

You are the seventh analyst. The domain expert's latest guidance (in the
capsule: search for "expert round 2" observations) says draft-change
interpretation needs positional track context — a draft change while
underway at speed reads differently (ballast shift, crew reset) than one
at a berth or at anchor — and suggests prototyping SQL views that make
track analysis fast, storing the good ones in the capsule.

## Interfaces (as ever)

- Capsule ONLY via `venv/bin/python bridge.py tools` (once → tools7.json)
  and `venv/bin/python bridge.py call <tool> '<json>'`; payloads with
  quotes via scratch file: `@args.json`. Orient FIRST: methods M1–M6,
  caveats, the expert round-2 observations, existing vessel stories.
- Data ONLY via `venv/bin/python query.py "SQL" --max-rows 40`. Never
  echo credentials. Do not read predecessors' scratch files (JOURNAL-*.md,
  BRIEF-1..6, VOCAB-NOTE.md, expert-*.md, tools1-6.json) or
  /workspaces/doxybase.

## Task

Prototype kinematic-context primitives as DuckDB views, then prove them:

1. **A track-state classifier**: per MMSI per time window, label
   underway / anchored / berthed (or your better taxonomy) from SOG,
   position dispersion, and dwell overlap. Index layer first; broadcast
   level only where decisive. Mind the recorded caveats (timestamp
   column, static-vs-positional message provenance, placeholder rules).
2. **Draft-change contextualizer**: join draft transitions against
   track state so each change carries its kinematic context. The expert
   expects: at-berth changes ↔ cargo work; at-anchor ↔ ambiguous
   (ballast/lightering); underway ↔ ballast or data artifact.
3. **Prove on known ground**: run them over vessels the capsule already
   stories (find them via list_entities/search) and check the outputs
   against the recorded stories; then run on 2–3 fresh vessels and spot
   check at broadcast level.

**Record what earns its keep**: the views that survive proving go into
the capsule the M-method way — pattern (what/why/failure modes) + the
executable SQL + caveats discovered while proving. Views that fail get a
one-line observation saying why (that is knowledge too). Do not record
bulk outputs; record methods.

## Discipline

Budget queries. Keep `JOURNAL-7.md`. Validate the graph (scope "all")
at the end; leave no orphaned staged rows.

## Final report

(1) the taxonomy you chose and why; (2) each view: what it does, how it
was proven, verdict; (3) what the proving revealed about draft-change
interpretation (with numbers); (4) methods/caveats used by IRI; (5)
friction notes.
