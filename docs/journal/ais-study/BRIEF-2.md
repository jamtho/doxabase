# AIS Study — Session 2 Brief (cold analyst)

You are a new analyst joining an ongoing maritime-data project. A previous
analyst worked this project before you; their knowledge lives in the
DoxaBase capsule. You have NOT met them and may not read their scratch
files — the capsule is your inheritance. Orient there first.

## Interfaces (identical rules to theirs)

- Capsule: ONLY via `venv/bin/python bridge.py tools` (once, redirect to
  tools2.json) and `venv/bin/python bridge.py call <tool> '<json>'`.
  DoxaBase docs via the doxabase.get_doc tool.
- Data: ONLY via `venv/bin/python query.py "SELECT ..." --max-rows 40`.
  Never echo credentials. Do not read JOURNAL.md, BRIEF.md, tools.json,
  expert-questions.md, or /workspaces/doxybase.

## Your tasks (forensics)

1. **Vessel story**: reconstruct what MMSI **367615990** has been up to
   across the data: identity (and any changes, with your best estimate of
   REAL timing), physical characteristics, operating areas, notable
   behaviour. Record it into the capsule as the previous analyst would.
2. **Associates**: which vessels has MMSI **369305000** worked with, in a
   commercial-relationship sense? Justify, with evidence.
3. **Port calls**: list the port/terminal visits of MMSI **338617000**
   during May 2024 — arrival/departure timing as best the data supports,
   and where. Record the method you use.

## Discipline

- Trust the capsule's recorded caveats and methods where they exist;
  verify anything load-bearing. If a recorded method applies, USE it (and
  say so); if it fails you, record that too.
- Keep `JOURNAL-2.md` as you go. End by validating the graph (scope "all").

## Final report

(1) the three answers with evidence; (2) which recorded capsule knowledge
(methods, caveats, views, expert notes) you used, by IRI, and which you
had to re-derive or invent; (3) anything the previous analyst got wrong;
(4) friction notes.
