# AIS Study — Session 3 Brief: Literature Onboarding

You are the third analyst on this project. Two predecessors built the
capsule from the data alone; a domain expert has answered questions into
it. YOUR session adds the official documentation layer — and the test is
reconciliation: where the provider's docs and the capsule's empirically
derived knowledge agree, disagree, or fill each other's gaps.

## Interfaces

- Capsule: ONLY via `venv/bin/python bridge.py tools` (once → tools3.json)
  and `venv/bin/python bridge.py call <tool> '<json>'`. Orient in the
  capsule FIRST — read its caveats, methods, and expert observations
  before opening any external doc.
- Data: ONLY via `venv/bin/python query.py "SQL" --max-rows 40`. Never
  echo credentials.
- Internet: you MAY fetch from hub.marinecadastre.gov and arcgis.com
  (venv has `requests` + `pypdf`; duckdb `spatial` reads gpkg). Download
  into `external/` (create it). Treat downloaded documents as claims by
  the provider, not ground truth — they get recorded WITH provenance,
  and where they contradict capsule evidence, the EVIDENCE decides.
- Do not read predecessors' scratch files (JOURNAL*.md, BRIEF*.md except
  this one, tools*.json, expert-questions.md) or /workspaces/doxybase.

## Tasks

1. **Documentation ingest**: from
   https://hub.marinecadastre.gov/pages/vesseltraffic find and read the
   key documents about this AIS product (data dictionary / FAQ / any PDF
   describing processing). Record what the provider CLAIMS about: field
   meanings and encodings, static-vs-positional message handling, any
   annual processing or identity canonicalization, placeholder/sentinel
   conventions, coverage. Each recorded claim carries its document +
   page/section provenance.
2. **Reconciliation**: for each capsule caveat that the docs speak to
   (identity-year-constant, placeholder-encoding-shift, sentinel values,
   message-type merging, timestamp semantics): does the documentation
   confirm, contradict, or stay silent? Strengthen, refine, or
   reconsider the capsule records accordingly — never silently overwrite
   empirical findings with doc claims.
3. **Coverage envelope**: the receiver/detector map lives at ArcGIS item
   8383640cd72e463caa77d230978c24bd (a zip containing a gpkg). Download,
   ingest, and record: receiver distribution, what coverage envelope it
   implies, and whether the expert's remembered "40-50 nm offshore" rule
   appears in any document. Then assess concretely: which of the
   capsule's silence-gap classifications (method M3) would change if
   coverage were taken into account? Record the assessment; upgrading M3
   itself is optional if time allows.

## Discipline

Keep `JOURNAL-3.md` as you go. Validate the graph (scope "all") at the
end. Downloaded files stay in `external/`; record their URLs + retrieval
date as evidence sources.

## Final report

(1) provider claims recorded (with IRIs); (2) the reconciliation table —
caveat by caveat: confirmed / contradicted / silent, and what you changed
in the capsule; (3) coverage findings and the M3 assessment; (4) anything
that surprised you; (5) friction notes.
