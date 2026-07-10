# AIS Study — Session Brief

You are the first analyst on a new project: building durable knowledge about
vessel behaviour from AIS (ship transponder) data. Your working memory is a
DoxaBase capsule — everything worth keeping goes into it, structured, so
future sessions (agent or human) start where you finish.

## The data

A local S3 bucket `ais-noaa` holds AIS broadcasts around the USA:

- `s3://ais-noaa/broadcasts/{year}/ais-YYYY-MM-DD.parquet` — one file per
  day, one row per received broadcast.
- `s3://ais-noaa/index/{year}/ais-YYYY-MM-DD.parquet` — one row per
  MMSI per day (a daily summary layer).

Query it with: `venv/bin/python query.py "SELECT ..." --max-rows 40`
(credentials are resolved from the environment — NEVER copy credentials,
endpoints, or secret-like values into the capsule, your journal, or any file).

## Your capsule

Interact with it ONLY via `venv/bin/python bridge.py tools` (registry — run
once, redirect to tools.json) and `venv/bin/python bridge.py call <tool>
'<json>'`. DoxaBase docs via the doxabase.get_doc tool. The capsule starts
empty: describing the datasets, storage, columns, and caveats in the map is
part of the work. Everything you learn that a future analyst would need —
record it: evidenced observations for findings, patterns for things that
recur, map facts for current-best structure, analysis views for named
reusable queries.

## Track A — vessel forensics

Pick 3 MMSIs that look interesting (your choice, justify it) and reconstruct
what you can of each vessel's story across the data: identity (names, IMO,
call sign — and any CHANGES over time), physical claims (dimensions, draft
changes), and behaviour (where it operates, notable periods). Record the
story as evidenced observations/claims per vessel; promote what is solid.

## Track B — methods

Invent ways to surface signal from vessel histories: events, behaviours,
relationships between vessels. This is open-ended and the harder track.
Every method you develop must be recorded in the capsule as: a pattern
(what it detects, why it works, confidence) + its failure modes as caveats
+ an analysis view with the executable SQL + at least one evidenced example
of it working on real data. Methods a future analyst can apply without
re-deriving them are the success criterion.

## Expert channel

A domain expert (a former practitioner) is available ASYNCHRONOUSLY: you may
leave AT MOST 3 questions in `expert-questions.md` (create it). Spend them
well — you will not get answers this session; they seed the next one.

## Session discipline

- Keep a running `JOURNAL.md`: what you tried, what surprised you, where
  you hesitated, what you'd tell the next analyst. Written for a reviewer,
  not as instructions.
- AIS data lies in specific ways. When you catch it lying, that is a
  finding — record it with evidence.
- Budget queries sensibly: daily files are large; the index layer is cheap.
- End the session by: validating the graph (scope "all"), generating
  nothing else — the reviewer runs the capsule report themselves.

## Final report

(1) capsule state summary (what you recorded, counts, key IRIs);
(2) your three vessel stories in brief; (3) each method you invented, one
paragraph each, with its pattern/view IRIs; (4) your 3 expert questions;
(5) honest friction notes about DoxaBase itself.
