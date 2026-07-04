# Agent Field Trials

Use field trials to test whether DoxaBase actually helps an agent understand
and preserve dataset lore. A field trial is not a benchmark or a production
migration. It is a bounded conversation with the tool: ask an agent to use the
current DoxaBase surface on a real dataset, then treat its friction as product
signal.

## Trial Shape

Keep the first run small:

1. Use one dataset.
2. Use one scratch capsule under `/tmp`.
3. Give the agent a short mission and clear report sections.
4. Avoid code changes unless the trial explicitly asks for implementation work.
5. Preserve the agent's independent experience; do not over-brief around every
   expected problem.

Use a strong reasoning model for exploratory trials. The agent should be capable
enough to notice tradeoffs, report confusion, and suggest better workflows.

## Runtime

Prefer the repo virtualenv directly:

```bash
./.venv/bin/python
```

Run commands from the repository root:

```bash
pwd
```

For repository verification after implementing a trial-driven fix, prefer the
parallel full-suite gate:

```bash
uv run pytest -q -n 16
uv run python tools/validate_rdf.py
```

Serial pytest remains useful for a single focused test or debugging output, but
the full DoxaBase suite is integration-heavy enough that serial runs materially
slow the autonomous loop. On the June 2026 development container, `-n auto`
completed the full suite in about 37 seconds after parsed seed RDF caching,
versus about 46 seconds with `-n 8`.
On July 1, 2026, the rebuilt YOLO container exposed 24 CPUs, no cgroup CPU
quota, and no memory cap; `uv run pytest -q -n auto --durations=25` completed
the full suite in about 41 seconds, while serial `tests/test_mcp_tools.py` alone
took about 63 seconds. At that point, `-n auto` was the local full-gate default
unless a shared runner needed lower aggregate CPU use.
A later serial full-suite timing pass with
`uv run pytest -q --durations=25 --durations-min=0.1` took about 325 seconds.
The slowest individual test was about 7 seconds, and the slow tail was mostly
staged-revision, project-brief, and example integration coverage. Treat slow
serial pytest as expected suite breadth unless a future duration table shows a
new outlier.
A July 1 follow-up in the active YOLO container found 616 serial tests passing
in about 330 seconds, while `uv run pytest -q -n auto --maxprocesses=8` passed
in about 51 seconds. The container exposed 24 CPUs, no cgroup CPU quota, and no
memory cap, so future loop slowdowns should first check whether pytest was run
serially before changing container resources.
A later July 1 runtime trial with 644 collected tests measured collection at
about 4.5 seconds and found the slow tail spread across staged-revision,
profile, query, project-brief, and example coverage rather than one runaway
test. On this container, `uv run pytest -q -n 12` passed in about 52 seconds,
beating the 8-worker cap at about 76 seconds; `-n 16` regressed to about
58 seconds. At that point, 12 workers were fastest locally and the 8-worker cap
was only for preserving CPU headroom for concurrent agents.
A later July 1, 2026 remeasurement after example-run isolation collected 645
tests in about 0.8 seconds and found `uv run pytest -q -n 16` fastest among
tested full-suite settings: about 44 seconds, versus about 50 seconds for
`-n 12`, 56 seconds for `-n auto`, and 46 seconds for `-n 20`. Use `-n 16` as
the current full-gate default on this container; remeasure if container CPU
visibility, cgroup quotas, or test composition change.

Do not rely on `uv run` inside sub-agent trials unless the trial is explicitly
testing the developer environment. Sandboxed agents may not have access to the
user's uv cache. If import paths are unclear, set:

```bash
PYTHONPATH="$(pwd)"
```

Create or replace a scratch capsule with `DoxaBase.create(path, overwrite=True)`.
Reopen an existing capsule with `DoxaBase(path)` when normal schema, graph-role,
seed, and search-index maintenance is acceptable. Use
`DoxaBase.open_readonly(path)` for strict inspection of a live capsule; it skips
initialization writes and opens SQLite with `mode=ro`, so mutating helpers fail
at the database layer.

When a trial changes MCP docs or tool registrations, remember that existing
Codex-bound MCP server sessions are long-running Python processes. They may keep
the old `agent_docs.DOCS` registry and decorated tool set until a fresh MCP
session starts. Cross-check with a fresh local Python process before treating a
stale `doxabase.list_docs` or missing tool as evidence that the commit failed.
Distinguish stale sessions from calls that never executed: `user cancelled MCP
tool call` and sandbox setup failures such as a `bwrap` namespace error are
execution-environment failures, not evidence that the DoxaBase MCP schema or
docs registry is old.
`codex mcp list` only proves the server is registered and enabled; it does not
prove the stdio command can start, open the configured capsule, or complete a
handshake. If doc calls return `Transport closed`, inspect the configured `cd`
path, capsule filename, capsule permissions, and Python importability. The
DoxaBase MCP server should register `doxabase.list_docs` and `doxabase.get_doc`
without opening the capsule; graph tools still open the configured capsule on
first use.

When running a trial through Codex sub-agents, keep the harness explicit:

- require a final thread report and a backup report file under `/tmp`;
- give the agent a concrete task and artifact contract before broad
  exploration;
- close completed or failed sub-agents so they do not occupy agent slots;
- let long-running sub-agents finish unless there is evidence of looping,
  repeated command failure, or a real blocker. Silence can be genuine reasoning
  time on subtle graph-workflow trials;
- treat a missing final or backup report as a trial failure even if a scratch
  capsule exists; inspect the capsule for partial work, but record that the
  agent did not complete the handoff loop.

For a first successful local workflow, run the copyable example from the
repository root:

```bash
./.venv/bin/python examples/first-workflow.py
```

It creates a scratch capsule under `/tmp`, loads the bundled fixtures, prints
graph/table/search/query-readiness cues, prints the selected query-target
decision and first query-planning action, records one observation, and validates
the graph. To continue the local query handoff, reopen the scratch capsule,
call `describe_query_context()` for the selected table, follow the first
`draft_query_plan` action, and stop before any network/S3 access unless the
trial explicitly approves it.
When multiple agents or pytest runs may execute examples at the same time, set
`DOXABASE_EXAMPLE_RUN_ROOT=/tmp/doxabase-trial-$USER-$PID` (or another unique
scratch root) before running the scripts. The examples keep the stable
`/tmp/doxabase-*` paths only when that variable is unset.

For a small profile-frontier workflow, run:

```bash
./.venv/bin/python examples/profile-frontier-workflow.py
```

It creates a scratch capsule from bundled fixtures, records one synthetic
full-scan profile bundle, drafts and stages representative profile map updates,
runs `plan_staged_revision_recovery()` over the staged profile revision, and
validates the graph. Use this when you need a reproducible profile-derived
map-update frontier without relying on a preexisting local capsule.

For a local query-result capture trial, create a tiny CSV or Parquet file under
`/tmp`, model it with `record_map_dataset`, `record_map_column`,
`record_map_storage_access`, and `record_map_physical_layout`, then call
`describe_query_context` and `draft_query_plan`. If
`review_gate.ready_for_execution_attempt` is true, execute a read-only local
count or aggregate with an external runtime such as DuckDB. If DuckDB is not
available, a small Python CSV reader is an acceptable fallback for the trial as
long as `engine` and `sample_method` say what actually ran. Record successful
and failed attempts with `record_query_result`; include `query_source_path`,
`query_hash`, `scanned_source_paths`, and `result_sources` or a failure log so
later agents can inspect the evidence. Do not record profile count fields for
failed attempts.

For a more adversarial staging trial, run:

```bash
./.venv/bin/python examples/adversarial-field-trial.py
```

It creates a scratch capsule and report under `/tmp`, records an uncertain
identity hunch as a claim and pattern, stages competing systematisations, and
expects one deliberately premature map candidate to fail validation.

Interleave ordinary polish loops with broader expeditions. Local API-friction
trials are good at improving response shapes, repair hints, and staged-review
routing, but they can underexplore project-wide product questions. Read
`project_strategy` when choosing the next broad wave or when recent loops are
clustered around one helper family. Every few loops, aim a wave at one or more
of:

- MCP transport and schema parity, especially when a Python helper gained a
  useful argument or safety gate that may not be exposed by the decorated server
  wrapper yet;
- real-data pressure, such as an AIS or Polymarket question-to-handoff run;
- cold-start/onboarding, including the first successful workflow;
- architecture gaps that need a new primitive, such as durable graph versions
  or executable query/result capture;
- non-tabular assets, mixed arbitrary RDF, derived/aggregate relationships,
  privacy/export hygiene, and scale/truncation pressure;
- human-facing workflow shape, including project briefs, recovery narratives,
  CLI affordances, and review-bundle readability.

Treat those expedition reports as product signal even when they do not produce
an immediate code patch. The goal is to stop the loop from polishing only the
paths it already knows how to walk.

A local query-planning repair trial found a three-step repair sequence worth
preserving: after staging and applying reviewed storage-access and physical
layout repairs, rerun `describe_query_context` before drafting. If the selected
candidate uses a dataset-owned path template, the dataset itself may still carry
a stale `rc:CandidateLayout` copied from an earlier manifest or candidate
review. Once storage and physical layout metadata are verified, follow the
generated `replace_dataset_layout_verification_status` repair group rather than
hand-authoring a generic graph revision.

A non-tabular relationship trial found that asset-level derivations and
aggregations could be squeezed through column relationship fields by passing
dataset IRIs as if they were columns. That is now guarded against, and simple
endpoint-only asset relationships can be recorded with
`record_map_relationship(..., source_datasets=[...], target_datasets=[...])`
without column fields. The broader frontier remains richer asset relationship
semantics: input roles, transform functions, ordering, selection scope, and
competing RDF framings still need observations, patterns, staged
systematisation, or a future dedicated primitive.

A privacy/export review-artifact trial found that the safe unattended handoff
route is a matrix, not a single scanner result. If broad
`export_preflight(export_kind="handoff_bundle")` blocks on unrelated project
content, use `preflight_context_slice_export` / `export_context_slice` for
resource-scoped importable review context and keep `fail_on_sensitive=true`.
Do not treat a clean staged patch as automatically shareable Markdown: staged
review exports include live apply-check drift, so current graph content outside
the patch can still make the generated Markdown dirty.

A July 1, 2026 broad-wave trial found no immediate code gap across three
previously underexercised surfaces. `export_preflight` plus guarded handoff
exports blocked synthetic graph and revision-snapshot secrets before writing
files, while scanner-clean handoff bundles exported and imported cleanly but
still carried the required shareability-review warning. `project_brief` routed
a mixed scratch frontier to privacy/export safety first, then exposed staged,
query, profile, and non-tabular work after explicit frontier expansion instead
of getting stuck on one visible queue. `record_map_asset_transform` carried a
realistic non-tabular image/label/pose transform with ordered endpoints,
conditions, per-output formulas/functions, and dataset/expression tuple-grain
components through `describe_dataset`, `describe_context_slice`, export, and
reimport without fake columns. Treat those surfaces as recently validated; run
new trials there only when the workflow shape changes or a concrete failure
appears.

A later Enron analysis-packet packaging trial found that graph-native packets
can carry reviewed populations, query recipes, aggregate artifacts,
visualization outputs, and follow-up tasks into `project_brief` and
`resource_brief` cleanly. The useful retrieval gap was route-cap ordering:
large packets could crowd out views, recipes, or tasks with bulk artifact
links. Packet action predicates now win the first outgoing-reference page, but
artifact-heavy packets still need `describe_resource` paging for exhaustive
artifact review.
A follow-up graph-native Enron trial confirmed that locator-only sidecar
scaffolds still leave Markdown view semantics invisible. Use
`python -m doxabase.analysis_packet --init-manifest --extract-markdown-views`
when reviewed Markdown contains fenced `CREATE VIEW` definitions; it emits
candidate view specs and row-count snapshots for review without applying or
trusting inferred semantics.

## Safety

Use a scratch capsule, for example:

```text
/tmp/doxabase-field-trial.sqlite
```

For repeated sub-agent runs, prefer a fresh timestamped directory such as:

```text
/tmp/doxabase-field-trial/run-20260617T193000Z/
```

Do not start trials by deleting old scratch directories. If cleanup is blocked
or ambiguous, leave the old artifacts in place and create a new run directory.
Use `DoxaBase.create(path, overwrite=True)` for the capsule inside that run
directory.

Do not modify the main project capsule. Do not commit trial artifacts unless the
user explicitly wants them preserved in git, or they contain a distilled lesson
that future agents can usefully learn from. Prefer tracked summaries in docs
over raw scratch capsules, generated SQLite files, or routine run logs.

Avoid secrets by default:

- Do not read `.env` files.
- Do not read local credential notes.
- Do not print credentials.
- Do not use S3, MinIO, paid APIs, or large data downloads unless the trial is
  specifically about access and the user has approved that scope.

When testing access, prefer read-only object listings, schemas, row counts, and
small samples. Treat access failures as useful product feedback rather than
spending the whole trial on environment repair.

## What To Ask The Agent To Do

A useful trial usually asks the agent to:

- read the relevant DoxaBase agent docs;
- read the dataset handoff docs;
- create a scratch capsule under `/tmp`;
- use `record_observation` for simple evidence-backed notes;
- use `record_claim_observation` for common structured claims;
- use `record_pattern` when related findings should be synthesized before map
  updates;
- use `stage_graph_revision` when a hunch or candidate systematisation should
  be preserved without becoming durable map truth yet;
- use `stage_systematisation` when one modelling hunch has several plausible
  RDF framings, especially if the hunch may need pattern-first and
  ontology-first alternatives; pass anchors for the concrete resources the
  hunch is about, not as a substitute for support/evidence; use shared proposed
  context when several framings should lean on the same provisional vocabulary
  or assumptions, and include shared `shapes` when the trial needs temporary
  validation rules for the framings;
- use `stage_pattern_promotion` when existing patterns support a caller-authored
  map, ontology, shape, or other graph change that should remain reviewable;
- use `describe_pattern` when checking whether synthesized lore can be taught
  back compactly;
- use map authoring helpers when the trial asks for a current-best scratch map;
- use agent-authored RDF only for claims the helper cannot express cleanly;
- use `list_entities`, `describe_resource`, `search`, and `graph_overview` to
  verify retrieval;
- read `response_shapes` before assuming exact Python or MCP response fields;
- run `validate_graph(scope="all")`;
- use `export_trig` or `export_graph` when the trial should leave reviewable
  RDF artifacts under `/tmp`;
- use `record_graph_revision` when the exported bundle or map change should
  leave a durable rationale in `history`; keep `changed_graphs` limited to
  graph roles that actually changed, and use `included_graphs` for unchanged
  review context included in an export;
- use `describe_staged_revision` and `export_staged_revision` when testing
  staged patch proposals, use `export_staged_revisions` when alternatives should
  be reviewed as one bundle, and inspect `validation_results` when a proposal
  fails validation before inferring the cause from patch text;
- when staging competing systematisations, add `review_note` and
  `review_recommendation` fields so the grouped export carries the agent's
  provisional judgement alongside validation diagnostics;
- use `describe_graph_revision` to inspect the resulting history record;
- report what worked, what was awkward, and what should change next.

When running a sub-agent field trial under `codex exec`, set a scratch uv cache
inside the writable trial directory, for example
`UV_CACHE_DIR=/tmp/doxabase-trial/uv-cache uv run python ...`. This avoids
user-cache permission issues while keeping trial artifacts disposable.

For systematisation-helper trials, include at least one awkward systematisation
that does not fit neatly into current helper templates. The agent should be
allowed to propose a new project vocabulary term, an ontology extension, or
several alternative RDF framings. Treat it as a failure if the workflow pushes
the agent to choose only familiar map facts when a deeper graph concept would be
more natural. Include a deliberately incomplete shape-backed framing beside a
repaired sibling when the trial can support it; that checks whether validation
guides repair without forcing the agent into a single modelling template.

## Report Sections

Ask for a report with these sections:

1. Scratch capsule work performed
2. Observations recorded
3. Structured claims recorded
4. Patterns synthesized
5. Retrieval checks
6. Validation result
7. What worked
8. Remaining friction
9. Suggested next changes
10. Safety/access notes

Incomplete work is still useful. If the agent gets blocked, ask it to report the
blocker, what it had prepared, and what it would do next.

## Evaluation Heuristics

Look for these signals:

- Could the agent decide when to use a helper versus hand-authored RDF?
- Could the agent decide when related observations should become a pattern?
- Could the agent propose a concept that stretches the current ontology, rather
  than only filling existing helper templates?
- Did evidence stay source-backed and credential-free?
- Did validation catch real mistakes without becoming busywork?
- Could the agent retrieve typed resources without relying only on lexical
  search?
- Did the report suggest concrete API, ontology, shape, or doc changes?

Good trials create a loop: run the agent, absorb the product signal, improve the
tool, and run another bounded trial.

For ongoing workflow-improvement work, prefer several trials over speculation.
After a useful trial, implement the sensible smallest justified fix, update
tests and docs, run focused and full verification, commit the coherent change,
and continue. Small fixes are preferred, but a larger change is appropriate when
that is the practical way out of a pathological state.

## Past Trial Signals

The dated history of product signals from past trials lives in
`docs/journal/trial-signals-history.md` (not MCP-registered). Distilled,
still-true lessons belong in the topic reference docs, not here.
