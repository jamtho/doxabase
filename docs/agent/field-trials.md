# Agent Field Trials

A field trial tests whether DoxaBase actually helps an agent understand and
preserve dataset lore. It is not a benchmark or a production migration: give
an agent a bounded mission against the current surface, then treat its
friction as product signal. Dated results and timing history belong in
`docs/journal/`, never here.

## Trial Shape

1. One dataset, one scratch capsule under `/tmp`.
2. A short mission and clear report sections, agreed before broad
   exploration.
3. No code changes unless the trial explicitly asks for implementation work.
4. Preserve the agent's independent experience — do not over-brief around
   every expected problem.
5. Use a strong reasoning model for exploratory trials; the agent should be
   able to notice tradeoffs and suggest better workflows.

Primary metrics: task success against the rubric, and tokens-to-outcome
(schema chars + doc chars fetched + response chars consumed, ÷4). A fix that
removes a confusion but raises cold-start cost is a regression.

## Safety

- Scratch capsules only (`DoxaBase.create(path, overwrite=True)` in a fresh
  timestamped run directory). Never modify the main project capsule; never
  start by deleting old scratch directories.
- No secrets: do not read `.env` or credential notes, do not print
  credentials, no S3/paid APIs/large downloads unless the trial is
  explicitly about access and that scope is approved. Prefer read-only
  listings, schemas, and small samples; treat access failures as product
  feedback, not environment repair work.
- Do not commit trial artifacts unless the user wants them preserved or
  they contain a distilled lesson; tracked summaries beat raw capsules.

## Runtime Notes

Reopen an existing capsule with `DoxaBase(path)`;
`DoxaBase.open_readonly(path)` gives strict read-only inspection. For
sub-agent runs, keep the harness explicit: a concrete artifact contract, a
final report plus a backup report file under `/tmp`, and a missing report
counts as a trial failure even when the capsule shows partial work. When
several agents may run examples concurrently, set
`DOXABASE_EXAMPLE_RUN_ROOT` to a unique scratch root. Remember that a
long-running MCP server keeps its registered docs/tools until restarted —
cross-check with a fresh process before treating a stale registry as a bug.

Maintained executable entry points (repo root, `./.venv/bin/python`):

- `examples/first-workflow.py` — fixtures, search, query-readiness, one
  observation, validation.
- `examples/profile-frontier-workflow.py` — profile bundle → draft → staged
  map updates → recovery plan.
- `examples/adversarial-field-trial.py` — competing systematisations with a
  deliberately premature candidate that fails validation.
- `examples/ais-query-overlay-smoke.py`,
  `examples/missing-metadata-query-repair-smoke.py`,
  `examples/query-evidence-storage-overlay-smoke.py`,
  `examples/staged-semantic-repair-smoke.py` — the query-repair and staged
  drift walkthroughs.

## What To Ask The Agent To Do

Reading (`get_doc`), orientation (`project_brief`, `graph_overview`,
`search`, `list_entities`, `describe_resource`), then the ladder: evidenced
observations (`record_observation`, including `kind="claim"`), syntheses
(`record_pattern`), current-best facts (`record_map_fact`), reviewable moves
(`stage_revision` — include at least one awkward systematisation that does
not fit helper templates), checks and applies
(`apply_staged_revision(dry_run=true)` then apply), review artifacts
(`export_bundle` after `export_preflight`), and
`validate_graph(scope="all")`. Ask for a report: work performed, what
worked, remaining friction, suggested next changes, safety notes. Incomplete
work is still useful if the blocker is reported.

## Evaluation Heuristics

- Could the agent decide when to use a helper versus hand-authored RDF, and
  when related observations should become a pattern?
- Could it propose a concept that stretches the ontology, rather than only
  filling existing templates? (If the workflow pushes agents toward familiar
  map facts when a deeper graph concept is more natural, that is a failure.)
- Did evidence stay source-backed and credential-free?
- Did validation catch real mistakes without becoming busywork?
- Did retrieval work without relying only on lexical search?
- Did the report suggest concrete API, ontology, shape, or doc changes?

Good trials create a loop: run the agent, absorb the signal, make the
smallest justified fix (or a structural one when structure is the problem),
verify, and run another bounded trial. Interleave polish trials with broader
expeditions — real-data pressure, cold starts, privacy/export hygiene,
non-tabular assets — so the loop does not only polish paths it already knows.
