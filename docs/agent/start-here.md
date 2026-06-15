# Start Here

DoxaBase is a local RDF memory capsule for data projects. It exists to preserve
the handover conversation you wish came with a complex dataset: not only field
names and storage paths, but caveats, hunches, rationale, awkward history, and
the mindset behind the data.

Agents supply semantic judgement. DoxaBase supplies storage, named graph
mechanics, retrieval affordances, parsing, and explicit validation.

## The Shape Of The Work

Useful dataset knowledge usually arrives before it is fully systematised. Do
not force every noticing into durable map truth too early.

Use the graph as a working memory with several layers:

1. Record point-in-time or source-scoped noticings as observations.
2. Gather related observations, claims, and evidence into patterns.
3. Promote the useful parts into map facts, project ontology terms, shapes, and
   history when they are ready.

Uncertainty is first-class here. Hunches, competing framings, and bold but
lightly-held ideas are useful when they are labelled clearly, linked to support,
and easy to revisit.

## First Ten Minutes

When arriving cold, use this route before reading every reference doc.

1. Call `doxabase.list_docs`.
2. Read this doc with `doxabase.get_doc(doc_id="start_here")`.
3. Call `doxabase.graph_overview` to see graph roles, counts, classes, and
   predicates.
4. Call `doxabase.search` for remembered terms, dataset names, caveats, source
   notes, columns, or question-shaped keywords.
5. Call `doxabase.list_entities` for likely entry points, usually
   `type="rc:Dataset"` or `type="rc:Table"` in `graph="map"`.
6. Call `doxabase.describe_dataset` for a bounded view of one table or dataset.
7. Call `doxabase.describe_assertion_support` when you need to ask why a
   specific map assertion or caveat link is present.
8. Call `doxabase.describe_context_slice` when you need a route-explained slice
   around a dataset, pattern, or lore thread.
9. Call `doxabase.list_entities(type="rc:Pattern", graph="patterns")` and
   `doxabase.describe_pattern` when the map points to synthesized lore.
10. Use the smallest write helper that fits the work, then validate before
   finishing.

If the MCP docs tools are not exposed in the current session, follow the same
route by reading the matching files in `docs/agent/` directly.

If you are scripting directly against the Python API, read `response_shapes`
before assuming returned field names.

## If You Are Resuming After Compaction

Recover the thread of work before making new graph changes.

1. Re-read the user's latest request and `AGENTS.md`.
2. Check `git status` so you know what is already changed locally.
3. Read this doc, then use `graph_overview`, `search`, `describe_dataset`, and
   `describe_context_slice` to reload only the relevant graph context.
4. If a previous agent or sub-agent left a report under `/tmp`, read that report
   before rerunning the same trial.
5. State uncertainty plainly if the compacted context does not contain enough
   detail to justify a durable map change.

## Graph Placement Cheat Sheet

- Put project vocabulary/model terms in `ontology`.
- Put current-best project and data facts in `map`.
- Put point-in-time or tentative findings in `observations`.
- Put syntheses over related observations, claims, or evidence in `patterns`.
- Put source/query/hash/sample support in `evidence`.
- Put project SHACL extensions in `shapes`.
- Put graph-change rationale, review-bundle metadata, and graph-count snapshots
  in `history`.

Do not write ordinary user or project facts to immutable package seed graphs:
`base_ontology` and `base_shapes`.

## Choosing The Right Move

- Simple evidence-backed noticing: use `record_observation`.
- Common observation plus claim, evidence, and source span: use
  `record_claim_observation`.
- Nuanced claim that the helper cannot express cleanly: write agent-authored
  observation RDF using the `observation_rdf` conventions.
- Several related noticings that seem to point at something more durable: use
  `record_pattern`.
- Current-best dataset, column, storage, caveat, layout, partition, or
  relationship fact: use the map authoring helpers.
- One modelling hunch with several plausible RDF framings: use
  `stage_systematisation`.
- Pattern-supported graph change that should be reviewed before becoming
  durable state: use `stage_pattern_promotion`.
- Generic reviewable graph patch: use `stage_graph_revision`.
- Staged patch that may be ready to apply: use `check_staged_revision_apply`
  before `apply_staged_revision`.
- Meaningful graph change or exported review bundle: use `record_graph_revision`
  so later agents know what changed and why.

## Runtime Gotchas

For normal repository development, use:

```bash
uv run pytest
uv run python tools/validate_rdf.py
```

For Codex sub-agent field trials, prefer the repo virtualenv directly:

```bash
./.venv/bin/python
```

Sandboxed sub-agents may not have access to the user's uv cache. Do not rely on
`uv run` inside a sub-agent trial unless the trial is explicitly testing the
developer environment. Require a final thread report and, for non-trivial
trials, a backup report under `/tmp`.

## What To Read Next

- `graph_roles`: graph placement rules in more detail.
- `agent_workflow`: the fuller operational sequence.
- `observation_recording`, `observation_rdf`, and `patterns`: how to preserve
  noticings, claims, evidence, and hunches.
- `map_authoring`, `staged_revisions`, and `revisions`: how useful lore becomes
  durable structure or reviewable graph changes.
- `context_slicing` and `lexical_search`: retrieval and handoff routes.
- `field_trials`: how to test DoxaBase with sub-agents and turn friction into
  product signal.
- `response_shapes`, `api_reference`, and `mcp_tools`: exact Python and MCP
  surfaces, including common returned field names.
