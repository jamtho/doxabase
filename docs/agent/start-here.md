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
   specific map assertion or caveat link is present. If your requested object is
   absent, check `same_subject_predicate_triples` and `absence_note` before
   proposing a cleanup. For column assertions, follow owner-dataset suggested
   actions when table-level lore may matter. For layout, partition, or storage
   assertions, check `nearby_context_triples` for verification notes before
   treating the assertion as executable planning context. Prefer
   `suggested_next_actions` over parsing display call strings, and scan
   `related_route_summaries` before raw `related_routes` when there is a lot of
   lore attached. Check `nearby_caveat_links.scope` before treating an
   owner-dataset caveat as a direct caveat on one column.
8. Call `doxabase.describe_query_context` when the task is physical query
   planning and you need storage/layout/path/caveat readiness. For
   database-backed storage, prefer candidate or draft-plan
   `relation_identifier` plus `connection_reference` over treating
   `candidate_path` as a file URI.
9. Call `doxabase.describe_context_slice` when you need a route-explained slice
   around a dataset, pattern, or lore thread. Use `profile="dataset_brief"` for
   dataset/table/profile/metric handoffs, `profile="pattern_brief"` for pattern
   handoffs, and `profile="deep_lore"` when revision/history links or broader
   lore may matter.
10. Call `doxabase.list_entities(type="rc:Pattern", graph="patterns")` and
   `doxabase.describe_pattern` when the map points to synthesized lore.
11. Use the smallest write helper that fits the work, then validate before
   finishing.

If the MCP docs tools are not exposed in the current session, follow the same
route by reading the matching files in `docs/agent/` directly.

If you are scripting directly against the Python API, read `response_shapes`
before assuming returned field names. Large docs expose section headings through
`doxabase.list_docs`; use `doxabase.get_doc(section="...")` or `start_char` to
jump past the default prefix.

## If You Are Resuming After Compaction

Recover the thread of work before making new graph changes.

1. Re-read the user's latest request and `AGENTS.md`.
2. Check `git status` so you know what is already changed locally.
3. Read this doc, then use `graph_overview`, `search`, `describe_dataset`,
   `describe_query_context`, and `describe_context_slice` to reload only the
   relevant graph context.
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
- Single map assertion add/remove/replace that should be reviewed with nearby
  lore before apply: use `stage_map_assertion_change`.
- One modelling hunch with several plausible RDF framings: use
  `stage_systematisation`.
- Pattern-supported graph change that should be reviewed before becoming
  durable state: use `stage_pattern_promotion`.
- Generic reviewable graph patch: use `stage_graph_revision`.
- Staged patch that may be ready to apply: use `check_staged_revision_apply`
  before `apply_staged_revision`.
- Staged patch blocked by count drift or digest drift but still semantically
  useful: use `restage_staged_revision`, then check and review the refreshed
  proposal.
- Several stale staged patches: use `restage_staged_revisions(dry_run=True)`
  first to classify the batch without creating successors, then run the real
  batch restage for rows you still want to refresh.
- Grouped staged review: use `bundle_summary.next_action_queue` for current
  mechanical routing, but also read each row's staged-time validation fields;
  current drift can hide why a candidate was invalid when it was first staged.
- Unknown staged/applied/history record: use `list_graph_revisions`, then
  inspect a specific result with `describe_graph_revision` or
  `describe_staged_revision`.
- Meaningful graph change or exported review bundle: use `record_graph_revision`
  so later agents know what changed and why.

## Runtime Gotchas

For normal repository development, use:

```bash
uv run pytest
uv run python tools/validate_rdf.py
```

Before a query-planning fixture trial against the active MCP capsule, check
`graph_overview.key_counts` for storage access counts. If AIS or Polymarket
tables are present but `storage_accesses` is zero, treat that capsule as stale
or intentionally reduced; use a fresh scratch fixture load before drawing
product conclusions about query-target behavior.

For Codex sub-agent field trials, prefer the repo virtualenv directly:

```bash
./.venv/bin/python
```

When running a scratch script from `/tmp` or `.codex-runs/...`, set:

```bash
PYTHONPATH="$(pwd)"
```

In Python, use `DoxaBase.create(path, overwrite=True)` to create or replace a
scratch capsule, and `DoxaBase(path)` to reopen an existing capsule. There is no
`DoxaBase.open()` helper in the current API.

MCP doc IDs use underscores, for example `staged_revisions` and
`query_planning`; their on-disk files usually use hyphens, for example
`docs/agent/staged-revisions.md` and `docs/agent/query-planning.md`.

Already-running MCP server sessions keep the Python modules and decorated tool
set they imported at startup. If `doxabase.list_docs` or the available MCP tool
list lags recent code changes, verify the registry in a fresh local Python
process or start a fresh MCP session before concluding the repo state is wrong.
Known doc content is read from disk by `doxabase.get_doc`, so file-content edits
can appear live even when newly registered docs or tools do not.

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
- `executable_catalog` and `query_planning`: physical metadata and draft query
  handoff routing.
- `field_trials`: how to test DoxaBase with sub-agents and turn friction into
  product signal.
- `response_shapes`, `api_reference`, and `mcp_tools`: exact Python and MCP
  surfaces, including common returned field names.
