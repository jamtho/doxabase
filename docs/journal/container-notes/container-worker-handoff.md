# Container Worker Handoff

You are a Codex worker starting inside a disposable container with broad
authority inside the container. Continue DoxaBase development using the normal
build, trial, learn, implement, test, commit loop.

Do not treat this as permission to be careless. Treat it as permission to work
for a long time without interrupting the user when the next step is clear.

## Project Soul

DoxaBase is a local RDF memory capsule for data projects.

Its core bet is that useful dataset knowledge often begins as uncertain,
source-scoped, and conversational. A good handover includes not only hidden
facts, but also how to think about the dataset: caveats, hunches, failed ideas,
awkward history, and the rationale behind structure.

The workflow is:

1. record observations;
2. synthesize related observations into patterns;
3. systematise durable parts into map facts, ontology terms, shapes, caveats,
   and history.

Do not over-flatten this into a rigid approval process. DoxaBase should help
agents preserve bold but labelled hunches, compare alternative framings, and
revise their thinking without pretending every useful idea is proven.

## First Moves

Start from the repository root, expected to be `/work/doxabase` unless the
container builder chose a different path.

Run:

```bash
pwd
git status --short
git log --oneline -8
sed -n '1,220p' AGENTS.md
sed -n '1,220p' README.md
sed -n '1,260p' ARCHITECTURE.md
sed -n '1,240p' docs/agent/start-here.md
sed -n '1,320p' docs/agent/field-trials.md
```

Then establish the baseline:

```bash
uv sync
uv run pytest
uv run python tools/validate_rdf.py
```

If `uv` cache permissions are awkward inside nested trials, set a disposable
cache:

```bash
UV_CACHE_DIR=/tmp/doxabase-uv-cache uv run pytest
```

## Current Repository State

At handoff time, the tracked tree had been pushed through:

```text
52c0cd2 Record profile handoff retest outcome
```

Recent work included:

- profile handoff cues in `describe_dataset`;
- preserved source-level names for unmapped profile columns;
- query-planning versus analysis warning domains;
- clearer CURIE/IRI hints for resource fields;
- field-trial documentation of those retest results.

Known local untracked artifacts may exist and should not be committed unless the
user explicitly asks:

```text
.doxybase.sqlite
docs/agent/ais-duckdb-doxybase-observations.md
examples/session-observations/
handoff/
```

The `handoff/` files are operational notes for this container transition. They
are intentionally local and do not need to be committed.

## Operating Loop

Use this loop until you are blocked, out of useful work, or ready for a final
user review:

1. Choose a specific pressure point from the current product direction.
2. Run a field trial or inspect the code/docs enough to understand the gap.
3. Implement the smallest coherent improvement.
4. Add or update tests and docs.
5. Run focused tests first, then:

```bash
uv run pytest
uv run python tools/validate_rdf.py
git diff --check
```

6. Commit the coherent change with a rationale-rich commit message.
7. Decide whether another trial loop is now useful.
8. Push only at a natural final checkpoint, or when you cannot continue
   unattended and need the user to review remotely.

The user has wanted commits after coherent loops and has generally authorised
pushes for this repo, but also asked that pushes be deferred while useful
unattended work can continue. Do not stop just to push in the middle of a run.

## Good Next Work

The near-term product direction is to keep exercising DoxaBase with serious
agent trials and turn friction into product improvements.

Likely useful loops:

- deeper field trials around profile bundles, unmapped profile columns, query
  context, and profile handoff;
- trials where an agent inherits a scratch capsule and must understand what a
  previous agent learned;
- adversarial staged-revision trials that test whether stale proposals, failed
  validation, and alternative systematisations remain understandable;
- context-slice trials that ask whether a fresh agent can retrieve the right
  lore without reading the whole graph;
- ontology/API refinements for recurring claims such as row granularity, target
  granularity, coercion/usefulness, storage readiness, and assertion support;
- richer examples that show how observations, patterns, evidence, and map facts
  hang together.

Prefer evidence from fresh-agent trials over abstract polishing. If a trial
surfaces a sharp problem, fix that problem and retest.

## Running Field Trials

Use `docs/agent/field-trials.md` as the main playbook.

For a local smoke trial:

```bash
./.venv/bin/python examples/adversarial-field-trial.py
```

For a nested Codex trial inside the container, create a prompt and run:

```bash
codex exec \
  -C /work/doxabase \
  --dangerously-bypass-approvals-and-sandbox \
  --add-dir /tmp \
  --output-last-message /tmp/doxabase-trial-report.md \
  - < /tmp/doxabase-trial-prompt.md
```

If an explicit strong model is available for exploratory work, use it. If the
model alias is unavailable, continue with the configured strong Codex default.

Every non-trivial trial should leave:

- the prompt;
- the final report;
- any scratch capsule path;
- any exported RDF or Markdown review bundle;
- a short note in your own final report explaining what product signal you took
  from it.

Treat missing trial output as a trial failure, even if partial artifacts exist.

## Writing Changes

Follow `AGENTS.md`.

Important local conventions:

- `doxabase/core.py` owns storage and graph behavior.
- `doxabase/mcp_tools.py` owns testable MCP-callable business logic.
- `doxabase/mcp_server.py` should stay thin.
- `docs/agent/` contains short agent-facing docs; register committed docs in
  `doxabase/agent_docs.py`.
- `doxabase_design_docs/` and `ARCHITECTURE.md` hold broader direction.
- Use type hints generously.
- Prefer RDFLib, SQLite, and existing helpers over ad hoc parsing.
- Comments are welcome when they preserve useful graph or validation context.

Do not write ordinary project facts to immutable seed graphs:

```text
base_ontology
base_shapes
```

Use graph roles correctly:

- project vocabulary in `ontology`;
- current best data facts in `map`;
- tentative findings in `observations`;
- syntheses in `patterns`;
- support in `evidence`;
- project validation in `shapes`;
- change rationale and graph-count snapshots in `history`.

## Commit And Push Discipline

Commit after each coherent implementation loop. Commit messages should explain
why the change exists, not just which file changed.

Before committing, check:

```bash
git status --short
uv run pytest
uv run python tools/validate_rdf.py
git diff --check
```

Do not commit local capsules, credentials, run scratch directories, or these
handoff notes unless the user explicitly asks.

Push only when:

- you have reached a natural review checkpoint;
- you are blocked from continuing without user input;
- or the final report is ready.

If push credentials are absent or fail, keep working locally if useful and
report the push blocker in the final handoff.

## Safety

Do not read, print, or commit secrets.

Use scratch capsules under `/tmp` or `/runs`, not the user's main capsule.

For S3 or other external data:

- prefer read-only listings, schemas, row counts, and small samples;
- keep credential scope narrow;
- record access failures as product signal when appropriate;
- do not spend an entire product trial repairing infrastructure unless that was
  the trial goal.

## Final Report Shape

When you stop, write a concise but useful report, ideally both as the final
Codex message and as a file under `/runs`.

Include:

1. latest branch and commit;
2. commits made;
3. tests and validation run;
4. field trials run and what they showed;
5. product changes made in response;
6. remaining friction or open design questions;
7. whether anything was pushed;
8. exact paths to important reports, scratch capsules, and exports.

If you had to make a judgement call, explain the rationale. The point of
DoxaBase is to preserve the thinking, not only the final graph.

