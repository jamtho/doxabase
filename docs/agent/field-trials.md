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

```text
/home/james/github.com/jamtho/doxybase
```

Do not rely on `uv run` inside sub-agent trials unless the trial is explicitly
testing the developer environment. Sandboxed agents may not have access to the
user's uv cache. If import paths are unclear, set:

```bash
PYTHONPATH=/home/james/github.com/jamtho/doxybase
```

Create or replace a scratch capsule with `DoxaBase.create(path, overwrite=True)`.
Reopen an existing capsule with `DoxaBase(path)`. There is no `DoxaBase.open()`
helper in the current API.

When running a trial through Codex sub-agents, keep the harness explicit:

- require a final thread report and a backup report file under `/tmp`;
- give a tight timeout and a small, concrete task before broad exploration;
- close completed or failed sub-agents so they do not occupy agent slots;
- if a sub-agent appears silent, interrupt once and ask for immediate status
  before closing it;
- treat a missing final or backup report as a trial failure even if a scratch
  capsule exists; inspect the capsule for partial work, but record that the
  agent did not complete the handoff loop.

For a tiny local smoke trial, run the copyable example from the repository root:

```bash
./.venv/bin/python examples/adversarial-field-trial.py
```

It creates a scratch capsule and report under `/tmp`, records an uncertain
identity hunch as a claim and pattern, stages competing systematisations, and
expects one deliberately premature map candidate to fail validation.

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
user explicitly wants them preserved in git.

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
more natural.

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

## Product Signals From Recent Trials

The June 2026 cold-start, wrong-hunch, and AIS generalisation trials surfaced a
few useful gaps:

- Claim lifecycle needed first-class support. Agents could record an initial
  hunch and a later correction, but they needed an explicit
  `record_claim_reconsideration` move to mark the earlier claim as weakened,
  contradicted, superseded, or refined without deleting the exploratory trail.
- DoxaBase retrieval output sometimes serves as evidence. Use
  `rc:DoxaBaseAPISource` for source spans or evidence artifacts that come from
  `search`, `describe_dataset`, `describe_context_slice`, or similar API calls.
- `describe_dataset` should expose embedded structures, such as JSON arrays or
  coupled encoded fields, more directly. Agents otherwise fall back to lexical
  search or manual fixture inspection.
- `deep_lore` is most valuable once claims, patterns, history, or
  reconsiderations exist. When it has no extra lore beyond `dataset_brief`, the
  response should ideally say so.
- Derived and aggregate tables still need pressure testing. Aggregation
  relationships now expose grouping columns, per-target aggregate mappings, and
  source/upstream caveats, but agents should still check whether row-unit
  semantics and layout-verification status are easy enough to carry into staged
  map candidates.
- Relationship descriptions expose aggregation source/target columns, but
  cross-dataset partition/path ownership may still need clearer retrieval.
- Staged systematisation drafts with failed, repaired, and alternative framings
  should be exported with `export_staged_revisions` and an `executive_summary`
  when the comparison itself is the artifact under review.
- `stage_map_assertion_change` judgement panels helped agents avoid a tempting
  Polymarket `VARCHAR -> DOUBLE` cleanup, but a later AIS timestamp trial showed
  that physical-type reviews need explicit `rc:valueType` /
  `rc:requiredPhysicalType` context and weak labels for routes that only match
  generic shared values such as `rc:Varchar`.
- A deeper AIS takeover trial showed that `describe_dataset` needs to surface
  query-planning hazards even when callers do not switch to
  `describe_query_context`. Use `operational_warnings` for those issues, and
  inspect `predicate_hints` on assertion-support misses when a guessed predicate
  such as `rc:hasPartitionScheme` is absent but a nearby shape like
  `rc:partitionedBy` is present. A follow-up regression confirmed this route
  works and suggested adding `predicate_curie` plus sharper absence-note wording
  so agents can see the likely predicate shape without mentally compacting full
  IRIs.
- A follow-up predicate-CURIE trial confirmed that wrong-predicate recovery is
  learnable from the docs. It also showed two small recurrent frictions: agents
  may guess a nonexistent `DoxaBase.open()` helper, and query-context warnings
  must be documented under the actual `issues` field name.
- A profile-helper trial confirmed that `record_dataset_profile` and
  `record_column_profile` make profile observations, evidence, map context, and
  patterns discoverable through `describe_dataset`. It also showed that agents
  need explicit reminders to turn off map updates for scratch profile results,
  that helper-created patterns should show their profile evidence directly, and
  that assertion support should match common typed scalar literals supplied as
  plain strings.
- Later profile-scope trials showed that `sample_scope` and `sample_method`
  make full-scan versus sampled/top-N profile lore much easier to retrieve. They
  also confirmed the preferred guardrail workflow: record sampled observed
  values with `record_column_profile(update_map_column=false)`, add a caveat
  claim that the values are not a closed domain, then synthesize both with a
  pattern. Remaining profiling questions include whether dataset-level scalar
  metrics need explicit metric targets, and whether profile-only handoffs should
  de-emphasize expected storage/layout warnings.
- A profile-bundle trial confirmed that `record_profile_bundle` gives agents a
  natural way to record one profiling pass without manually repeating run
  metadata across every profile. It also showed that "shared evidence" must be
  explicit: shared evidence fields are only defaults, while `shared_evidence_iri`
  links the dataset profile and column profiles to one profiler-run evidence
  resource. Query-planning `error` issues in profile-only capsules should be
  read as missing physical metadata, not failed profile recording.
- A follow-up shared-evidence trial confirmed that agents can now record one
  profiler-run evidence resource across dataset, mapped-column, and
  unmapped-column profiles. It also showed that quick returned-profile counts
  on `describe_dataset` and top-level `shared_evidence_iri` on the bundle return
  make the retrieval check easier than inferring success from nested profiles.
  A tighter verification suggested rolling up returned profile evidence IRIs in
  `profile_summary` so shared-evidence handoffs can be checked without walking
  every nested profile.

Use later trials to check whether these gaps still matter after each change.
If a gap stops being useful, revise this section.
