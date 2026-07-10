# AIS Study — Session 5 Brief: Distill the Vessel-Doings Vocabulary

You are the fifth analyst — the distiller. Eighteen vessel stories, six
methods, a deep caveat catalog, expert testimony, and reconciled provider
documentation now live in the capsule. Your job is to distill from them a
MINIMAL domain vocabulary for what vessels (and other AIS emitters) are
and do — and to prove it by re-expressing stories in it.

This is also an experiment about DoxaBase itself: whether domain
semantics can be grown empirically from recorded knowledge rather than
designed a priori. Work accordingly: every term must earn its place.

## Interfaces

- Capsule ONLY via `venv/bin/python bridge.py tools` (once → tools5.json)
  and `venv/bin/python bridge.py call <tool> '<json>'` (JSON via scratch
  file + "$(cat f)" — apostrophes break inline quoting). Do not read
  predecessors' scratch files or /workspaces/doxybase. Data via query.py
  only if a term's justification genuinely needs a fresh check.

## Task

1. **Harvest**: read every `pattern/vessel-*` story (and their kind
   lines), every method pattern, the caveat catalog, and the expert
   observations. Tabulate the recurring THINGS (emitter kinds), EVENTS
   (things that happen: renames, reassignments, collisions, lay-ups,
   refits, cargo cycles, tows, co-movement engagements, coverage exits,
   dwell periods), and ASSESSMENTS (identity-confidence states, dating
   quality) that stories actually needed to express.
2. **Distill**: propose the minimal vocabulary. Hard rules: a class or
   property must be justified by ≥2 independent stories (cite them);
   prefer properties over class proliferation; reuse rc: kernel terms
   (Observation/Claim/Evidence/Pattern/KnownCaveat) rather than
   duplicating epistemics; every term gets a one-sentence comment and a
   "justified by" note. Namespace: `https://ais.study/ns#` (prefix
   `aisv:`). Expect roughly 10-25 terms, not 50.
3. **Record**: stage the vocabulary into the capsule's `ontology` graph
   via `stage_revision(kind="graph")` (Turtle additions) with a rationale
   explaining the distillation basis; check with
   `apply_staged_revision(dry_run=true)`; apply; validate (scope "all").
4. **Prove**: re-express THREE existing stories (pick diverse kinds) as
   `aisv:` event/state resources in the map graph — via a second staged
   revision — showing the vocabulary carries real content. Note anything
   a story needed that the vocabulary couldn't say (that list is as
   valuable as the vocabulary).
5. **Design note**: write `/home/codex/ais-study/VOCAB-NOTE.md` for the
   project owner: the vocabulary table (term / meaning / justified-by),
   the couldn't-say list, and a ≤10-line reflection on whether
   empirical distillation produced a better vocabulary than a priori
   design would have.

## Final report

(1) the vocabulary (term-by-term with justifications); (2) staged
revision IRIs + apply results; (3) the three re-expressed stories;
(4) the couldn't-say list; (5) friction notes.
