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
uv run pytest -q -n auto
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
took about 63 seconds. Keep `-n auto` as the local full-gate default unless a
shared runner needs lower aggregate CPU use.
A later serial full-suite timing pass with
`uv run pytest -q --durations=25 --durations-min=0.1` took about 325 seconds.
The slowest individual test was about 7 seconds, and the slow tail was mostly
staged-revision, project-brief, and example integration coverage. Treat slow
serial pytest as expected suite breadth unless a future duration table shows a
new outlier.

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

## Product Signals From Recent Trials

The June 2026 cold-start, wrong-hunch, and AIS generalisation trials surfaced a
few useful gaps:

- MCP wrapper parity can lag Python helper behavior because most behavioral
  tests exercise `doxabase.mcp_tools` directly. When helper arguments carry a
  safety gate or semantic option, inspect the actual FastMCP input schema and
  add server-boundary regression coverage, not only direct helper tests.
- A privacy/export hygiene trial with fake credential-like values showed that
  caller-authored literals travel through search, retrieval, and exports once
  recorded. Use `scan_sensitive_literals` and export `privacy_warnings` before
  sharing bundles; warnings are redacted audit signals, not automatic RDF
  redaction or proof that the graph is secret-free. For unattended or shareable
  RDF exports, use `fail_on_sensitive=True` to block before creating or
  overwriting an artifact when selected graph roles scan dirty.
- A resource-scoped handoff trial showed graph-level exports are too coarse
  when one shareable dataset shares `map` with unrelated sensitive or noisy
  siblings. Use `preflight_context_slice_export` and `export_context_slice`
  for selected resource neighborhoods: they scan only selected triples and omit
  immutable seed graphs by default so the resulting TriG can import into a
  fresh capsule. Treat `describe_context_slice(include_trig=true)` as
  inspection text, not an import/recovery bundle.
  A later privacy handoff trial confirmed graph-level and recovery-complete
  exports block on unrelated sensitive-looking graph siblings, while
  resource-scoped context exports can stay clean and round-trip. Context-slice
  export records now expose explicit `decision`, `scanner_clean`, shareability
  review, and `handoff_fit` fields so agents do not infer the route from counts.
- A human-review artifact trial showed grouped staged-revision Markdown was
  mechanically complete but too technical at the top. `export_staged_revisions`
  now opens with a `Reviewer Decision Matrix` that gives row numbers, plain
  human actions, reasons, authored review recommendations, and a warning when
  bundled rows are competing alternatives.
- A mixed-queue `project_brief` trial showed low limits can hide an active queue
  type even though `queue_counts` and `omitted_queue_counts` preserve the
  evidence. `project_brief` now returns `active_queue_type_count`,
  `returned_queue_type_count`, and `limit_crowded_queue_types`; when crowding is
  reported, rerun with a higher limit before deciding the next loop frontier.
  A later frontier-routing trial showed the fields worked but distracted agents
  could still act on the first visible task and skip expansion. Use
  `first_unattended_action` for the canonical first hop and
  `frontier_status` for the compact safety/frontier/mutation gate.
- A profile/pattern frontier trial showed agents could stage profile map
  updates, metric vocabulary proposals, and caveat alternatives, but had to
  manually stitch the related staged revisions into one review bundle. Use
  `export_profile_insight_review_bundle` after staging the related lanes; it
  discovers current staged revisions connected by profile observations,
  profile-derived anchors, and related support patterns.
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
- A derived/aggregate relationship trial confirmed raw-to-derived-to-aggregate
  chains can carry grouping columns, aggregate mappings, shared identifiers,
  query-planning metadata, and source/upstream caveats through
  `describe_dataset` and context slices. Remaining modeling pressure is around
  composite row grain, conditional aggregate filters, and per-output derivation
  formulas; use descriptions, caveats, claims, and patterns rather than forcing
  those into misleading single-column `entityKey` or prose-valued map fields.
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
  `describe_query_context`. Use `operational_warnings` for dataset-owned
  physical metadata issues, but switch to `describe_query_context` for
  candidate-derived path/composition issues and direct candidate review
  reasons. A follow-up query-planning trial found the active MCP capsule can lag
  fixture files; if AIS/Polymarket tables are present but `storage_accesses` is
  zero, mark that run as stale/reduced or reload fixtures into a scratch
  capsule before drawing product conclusions. Inspect `predicate_hints` on
  assertion-support misses when a guessed
  predicate such as `rc:hasPartitionScheme` is absent but a nearby shape like
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
  pattern. Profile metrics now support optional targets for scalars that are
  about a narrower resource than the profile as a whole.
- A profile-bundle trial confirmed that `record_profile_bundle` gives agents a
  natural way to record one profiling pass without manually repeating run
  metadata across every profile. It also showed that "shared evidence" must be
  explicit: shared evidence fields are only defaults, while `shared_evidence_iri`
  links the dataset profile and column profiles to one profiler-run evidence
  resource. Query-planning `error` issues in profile-only capsules should be
  read as missing physical metadata, not failed profile recording. Later
  synthesis trials showed that the default bundle pattern should remain
  dataset-profile-only for compatibility, but run-level syntheses are common
  enough to justify `pattern_support_scope="all_profiles"` when the free-text
  pattern should be supported by the dataset and every bundled column profile.
  A later mixed-run profile trial showed bundle handoff strings were less
  ergonomic than the structured routes elsewhere; `handoff_entrypoints` now
  carries `suggested_next_actions` while preserving `suggested_next_calls`.
- A follow-up shared-evidence trial confirmed that agents can now record one
  profiler-run evidence resource across dataset, mapped-column, and
  unmapped-column profiles. It also showed that quick returned-profile counts
  on `describe_dataset` and top-level `shared_evidence_iri` on the bundle return
  make the retrieval check easier than inferring success from nested profiles.
  A tighter verification suggested rolling up returned profile evidence IRIs in
  `profile_summary` so shared-evidence handoffs can be checked without walking
  every nested profile; later candidates also expose grouped
  `profile_observation_iris` so a receiving agent can inspect the run directly.
- A profile-only handoff trial confirmed that `profile_summary.handoff_note`
  helps fresh agents separate successful profile recording from expected
  missing physical query-planning metadata. The same trial exposed that unmapped
  column profiles needed to preserve the supplied source-level column name
  without promoting the column into the map; use `observed_column_name` and the
  `observed_column.column_name` fallback for that handoff. Query-planning issues
  and analysis warnings now carry a `domain` field so agents can read severity
  in the right lane. A retest confirmed the new affordances and also showed
  that plain resource-field names should error with a concrete CURIE/IRI hint.
- Staged-revision trial loops in the rebuilt yolo container confirmed that
  patient sub-agent runs can surface real product signal. One account-segment
  trial showed that restaged revisions needed a compact `restage_reason` in
  `describe_staged_revision` and Markdown exports. A same-count ontology drift
  trial then showed that drift relevance also needed patch-object and
  revision-anchor overlap fields, because a changed superclass/anchor can be
  semantically relevant even when staged patch subjects are untouched. A
  follow-up export-readability trial showed that the compact restage reason also
  needs to appear early in Markdown review bundles, not only under the later
  `Restaged From` section. A stale-original follow-up showed that the old source
  export also needs an early `Restaged by` pointer when a refreshed sibling
  already exists. A same-count replacement-helper trial then showed that public
  APIs could produce digest drift only through full export, RDFLib editing, and
  replace-import; `replace_graph_triples` now gives agents a direct guarded
  helper that returns before/after counts and content digests. A stale
  alternatives recovery trial showed that grouped Markdown exports were helpful
  for comparing stale, ready, and restaged proposals, but scripts still had to
  rebuild the same status table with separate apply-check calls; grouped export
  records now include `revision_summaries` with current apply status, blockers,
  validation state, restage links, recommendations, and suggested next actions.
  A follow-up all-stale recovery trial confirmed those rows were enough to find
  the unresolved stale proposal, but preserving alternative grouping still
  required a separate revision-list call and stale originals with successors
  still suggested another restage; summaries now carry `alternative_to`, and
  suggested actions point at `restaged_by` successors when they already exist.
  Retests on several stale proposals showed that agents could recover from the
  grouped rows but still hand-counted unresolved stale sources, handled stale
  sources, and ready successors; list/export rows now include
  `stale_resolution_state`, exports include `bundle_summary`, and
  `current_alternative_to` follows refreshed successors while preserving stored
  provenance.
  A drift-overlap detail trial showed that `drift_detail="summary"` already
  carries `drift_relevance` plus patch subject/predicate/object and
  revision-anchor overlaps, so no intermediate `drift_detail="overlap"` mode is
  needed. Summary rows now also carry added/removed exact-change counts while
  still omitting the heavy changed-triple arrays unless exact detail is
  requested.
  A post-apply lineage trial showed that list rows stayed clear after recovered
  successors were applied, but detail views needed the same links and grouped
  recommendations needed to distinguish mutation review from applied-event
  inspection. Applied graph-revision descriptions now expose
  `applies_staged_revision`; staged descriptions expose `applied_by` and
  `application_status` once applied; grouped bundle summaries split
  `recommended_mutation_review_iris` from `recommended_applied_inspection_iris`.
  A current-alternative Markdown trial showed that JSON exposed a refreshed
  comparison target but Markdown-only reviewers had to reconstruct it manually;
  grouped exports now include `Alternative Context` when a stored alternative
  target has been restaged.
  A validation-repair trial showed that agents could diagnose a
  `validation_failed` revision but needed a stronger repair branch hint. Failed
  validation checks now suggest exporting diagnostics before staging a repaired
  or alternative candidate, and grouped bundle summaries list
  `validation_failed_revision_iris` directly.
  A larger 10-successor recovery trial showed that one-by-one restage plus
  export required too much glue while batch apply was still too broad. Batch
  restage now skips already-handled stale sources, restages unresolved
  conflicted rows, preserves review order, returns old-to-current mappings and
  bundle summaries, and can write the grouped review export without applying.
  A deeper restage-chain trial showed direct `restaged_by` remains good
  provenance but is not enough for action routing; list rows, staged
  descriptions, export summaries, suggested actions, and batch restage now expose
  `current_restaged_by` for the latest known successor.
  A mixed batch-restage retest found that ready, already-applied,
  validation-failed, and stored-patch-conflict rows all shared
  `skipped_not_restageable`, leaving recovery scripts to infer why each row was
  skipped. Batch restage now keeps that action for compatibility while adding
  per-row `not_restageable_reason` and grouped
  `not_restageable_revision_iris_by_reason` values for triage.
  A successor-chain trial then showed the single restage helper could mint
  parallel successors from the same stale source, hiding one successor from
  ordinary `restaged_by` routing and inviting no-op apply noise later. The
  helper now refuses to restage a source that already has a refreshed successor;
  agents should inspect or restage `current_restaged_by` instead.
  A caller-authored repair trial showed that `alternative_to` was too weak for a
  repaired successor: it preserved a competing framing, not a replacement for
  stale work. Staging helpers now accept `restages_revision` so an agent can
  author a revised patch, record the same restage provenance, and keep successor
  routing pointed at the repaired candidate.
  A retread found a ready source could also be caller-superseded, but direct
  apply checks still suggested applying the old source. Such sources now report
  `status="superseded_by_restage"` and point at the current successor instead.
  A no-op replay trial showed that stale patches can be restaged after another
  route has already realized all or part of the payload. Apply checks now report
  effective add/remove counts, already-present/absent payload triples, and a
  `noop` status with `no_effective_patch_triples` when replay validates but
  would not mutate graph state.
  A post-apply history trial showed the documented two-hop recipe worked but
  repeated detail calls for basic source context. Applied graph-revision
  descriptions now include compact `applied_source` cards while leaving patch
  content and full diagnostics on `describe_staged_revision`. A later
  apply-one-and-repair-sibling trial showed fresh agents can complete the
  recovery workflow, but the apply result itself needs to make stale sibling
  readiness hard to miss. Read `apply_staged_revision().warnings` and
  `post_apply_recheck_revision_iris`, then rerun
  `plan_staged_revision_recovery(current_staged_work_only=True)` before the
  next mutation.
- A post-rebuild trial wave found several places where structurally correct
  payloads were still easy for agents to misread. Query target metadata warnings
  for one dataset-level complete template, or for one storage-owned path
  template, could bleed onto clean sibling candidates sharing the same storage
  access; candidate review reasons now scope template/storage mismatches to the
  exact candidate while the overall context still remains conservative. Batch
  restage trials showed
  `action="restaged"` is only a creation event, not an apply-ready signal:
  restaged successors may be ready, validation-failed, no-op, or stale again.
  Batch items now include `status_after`, `decision_after`,
  `stale_resolution_state_after`, blockers, and effective triple deltas for
  `current_revision_iri`, and bundle summaries include validation-failed
  successors by current apply status. A chain trial then showed that an
  already-handled source can point to a current successor that is itself stale;
  this now reports `restaged_successor_stale_unresolved` and routes mutation
  review to the current successor. Export readability trials also showed that
  repeated bare `describe_staged_revision(...)` calls hid the difference
  between "review stale source" and "inspect current refreshed successor";
  suggested actions now carry `action_label`, and Markdown renders those labels
  while keeping `suggested_next_calls` as back-compatible call strings.
- A temp-capsule apply trial confirmed that ready staged revisions are not an
  unordered apply queue: applying one map revision can stale sibling ready or
  no-op revisions, including ordinary ready proposals as well as restaged
  successors. Grouped bundle summaries now carry `warnings` for that sequencing
  hazard plus `post_apply_recheck_revision_iris` for scripts, and split the
  broad mutation-review queue into
  `recommended_apply_or_restage_review_iris` and
  `recommended_repair_review_iris`. Grouped Markdown now mirrors those buckets
  in `Review Queues` for human reviewers.
- A cold-start MCP trial confirmed that live MCP mutation tools operate on the
  configured server capsule, not a caller-selected scratch path. For disposable
  scratch trials, use Python MCP helper functions against
  `DoxaBase.create(path, overwrite=True)`, or start a fresh MCP server with an
  explicit `--capsule /tmp/...` before calling mutable tools. The same trial
  found that `describe_context_slice` route summaries are already present as
  `reading_order`, `route_counts`, and `route_legend`; do not look for a separate
  `route_summaries` field.
- A second post-rebuild staged-revision wave confirmed that the recovery
  mechanics work, including same-count digest drift, stale alternatives,
  dry-run batch restage, successor routing, and post-apply sibling staleness.
  The remaining friction was mostly operational: agents needed one concrete
  grouped review recipe, a scratch-capsule Python example with exact helper
  parameter names, and a reminder that list/export relation fields are IRI
  strings while detailed staged descriptions use resource summaries. A separate
  post-apply history trial confirmed the two-hop recovery path from applied
  event to staged source, and showed enough private snapshot-row support for a
  narrow public `describe_applied_revision_diff` helper rather than broader
  durable graph-version browsing. A follow-up size probe showed that exact
  applied-diff arrays can become large quickly, so the helper returns counts by
  default and requires `include_triples=True` for capped changed-triple arrays.
- A staged-drift readability trial showed that `patch_object_overlap` can sound
  stronger than it is when the only object overlap is broad vocabulary such as
  `rc:Dataset` or `rc:Table`. Apply checks now use
  `broad_patch_object_overlap` for that weak case while preserving stronger
  object/anchor overlap labels. A validation
  wording check found no need to rename API fields or Markdown headings:
  `validation_results` remains the JSON field, and docs clarify that prose
  "diagnostics" means those same SHACL result records.
- Query/context smoke trials found two handoff traps. A storage access whose
  `storage_root` is itself the dataset location now surfaces a
  `storage_access_location` query target candidate instead of only reporting a
  missing path template. A follow-up storage trial showed that root-only
  candidates are too ambiguous without a storage-location kind: record
  `location_kind="object"` only for exact dataset objects/locations, and expect
  directory, prefix, connection, or unspecified roots to remain review-only
  until a path template narrows them. Context slices also now warn with a
  concrete rerun profile when a seed type does not match the chosen profile,
  for example an `rc:Pattern` seed sent through `dataset_brief`.
- A query-planning storage trial showed that verified graph metadata can still
  combine into a bad execution hint when an exact object path has one extension
  but the single linked physical layout records another file format, for
  example `.csv` with `rc:Parquet`. `describe_query_context` now surfaces
  `physical_layout_path_extension_mismatch` as a candidate metadata blocker so
  `draft_query_plan` stays metadata-review-required instead of becoming an
  execution-attempt-ready `read_parquet` handoff.
- A context-slice/profile-seed trial showed that a directly seeded old profile
  observation can be outside a dataset context's bounded recent profile lists,
  even though the resource and evidence are present in the slice. Context slices
  now expose `seed_profile_observations` for explicit profile-observation seeds
  and profile observations reached from profile-metric seeds, preserving the
  exact handoff row without inflating default `describe_dataset()` profile
  lists or mutating `profile_summary` evidence rollups.
- A profile-metric-target trial confirmed that optional `target` values let one
  dataset-level profile carry both whole-profile scalar metrics and narrower
  column-targeted metrics without promoting either into map facts or
  constraints. The same trial exposed a SQLite/RDF edge case: linking a column
  through both dataset and column helpers inserted repeated `rc:hasColumn`
  edges because SQL uniqueness does not treat `NULL` datatype/lang values as
  equal. Quad insertion now uses explicit RDF-style existence checks, response
  reads de-duplicate repeated objects, and the profile docs show `target=None`
  versus a narrower metric target.
- A wide profile-run retrieval trial showed that `describe_dataset()` can
  identify a shared-evidence run while omitting some profile observations from
  its bounded profile lists. Use `describe_profile_run` with the dataset IRI and
  shared evidence IRI when a receiver needs the whole run. The same docs-guided
  trial showed that bundle-created patterns support only the dataset profile
  observation; for a synthesis over dataset and column profiles together, call
  `record_pattern` after the bundle with all returned profile observation IRIs
  and the shared `evidence_iri`.
- A profile metric-kind ergonomics trial showed that unknown `rc:` metric kinds
  such as `rc:MinValue` could previously validate as arbitrary IRIs. Recording
  now rejects undefined `rc:` profile metric kinds while still allowing full
  project-specific metric IRIs; agents should use
  `list_entities(type="rc:ProfileMetricKind", graph="base_ontology")` before
  choosing a base kind.
- A profile-metric promotion/apply trial confirmed that project metric kinds
  can be recorded as full IRIs, explained with a claim and pattern, promoted
  through `stage_pattern_promotion`, applied to `ontology`, and retrieved by a
  metric-seeded context slice. It also showed that
  `list_entities(type="rc:ProfileMetricKind", graph="ontology")` is an
  effective-ontology lookup: project-local checks need to filter returned
  entities by `graph == "ontology"` because built-in `base_ontology` metric
  kinds are included too.
- A deeper mini-handoff trial on the Polymarket fixture recorded four claim
  observations plus one synthesis pattern around snapshot/event grain,
  condition-ID versus CLOB-token-ID join lanes, embedded JSON/string payloads,
  and the raw CLOB price payload boundary. The resulting capsule validated and
  the lore was retrievable through `describe_pattern`, `describe_dataset`,
  `describe_context_slice`, and targeted search terms. It also showed practical
  friction: direct Python scripts needed an obvious serializer for response
  dataclasses, broad lexical searches can miss useful lore when terms are split
  across literals, and `ready_for_query_planning` can sound stronger than
  intended when caveats still make aggregation analytically risky. The first
  two API follow-ups were public `to_dict` / `to_jsonable` helpers and
  query-context `analysis_warnings` plus `readiness_note`.
- A follow-up query-readiness trial confirmed that fresh agents can use the
  public serializers and read the readiness/caveat split. It also showed that
  missing layout verification status should not be silent: query context now
  returns info-level `verification_status_not_recorded` issues for usable
  path/layout metadata without explicit verification status, the executable
  catalog doc includes a direct Python serialization example, and analysis
  warning messages avoid doubled punctuation before impact text. A retest found
  the split clear and suggested exposing dataset-level verification status
  directly in query context for a complete compact inventory.
- A profile-bundle metrics handoff trial confirmed shared evidence, scalar
  metrics, unmapped column profiles, run-level patterns, `describe_profile_run`,
  and profile-seeded context slices now line up. It also showed that
  `update_map_snapshot=false` suppresses the bundle's dataset map write; create
  a map shell first when the next agent should start from `describe_dataset`
  while keeping the profile row count observation-only. Handoff notes now call
  out the mixed case where map context already existed but the bundle did not
  write dataset map facts.
- A follow-up profile metric/map-facts trial confirmed project metric IRIs,
  awkward unmapped-column metrics, shared evidence, and ontology promotion work
  together, but showed that an observation-only column IRI failed as a
  `describe_context_slice` seed. Dataset/deep-lore slices now accept IRIs that
  appear only as `rc:observedColumn` objects and expand through the matching
  profile observation(s) with `seed_observed_column` and
  `seed_profile_observation` routes.
- A profile metric semantics trial confirmed the observed-column seed fix and
  showed that common ratio metrics and awkward integer metrics need a compact
  authoring recipe. The observation-recording guide now shows decimal ratio
  metrics with `target`, integer suppressed-bucket metrics, value-frequency
  evidence, and the `pattern_support_scope` support-vs-target distinction.
- A staged restage workflow trial confirmed batch dry-run, grouped export,
  successor routing, apply-one-then-recheck, and applied-source inspection work
  as documented. It also exposed that staged patches targeting `history` become
  immediately stale because staging metadata is recorded in `history`; staged
  patch creation now rejects `history` targets and points agents to
  `record_graph_revision` for durable history notes.
- A query-planning metadata trial confirmed complete local paths, root-only
  object locations, broad root review gates, S3 protocol/template mismatches,
  and analysis caveats work as intended. It exposed one draft-plan bug:
  unresolved S3-compatible access was review-gated but
  `storage_environment.runtime_resolution_required` was false. Draft plans now
  mark runtime resolution required when the selected S3 candidate lacks endpoint,
  credential, and region metadata.
- A query catalog boilerplate trial showed the existing map helpers can model a
  realistic small executable catalog without a new mega-helper, but agents need a
  copyable recipe for dataset, columns, storage, layout, partition, caveat, and
  inspection calls. The same trial exposed that draft query plans only carried
  partition-scheme template verification into `plan.scan`; storage-access-owned
  templates now preserve their verification status and note too.
- A query storage-selection trial confirmed that DoxaBase keeps physical
  query-planning gaps separate from semantic caveats and flips
  `storage_environment.runtime_resolution_required` only when the selected
  candidate needs runtime S3 resolution. It also showed that a selected local
  candidate can remain `orientation_only` because sibling S3 or stale partition
  hints block the overall context; read `query_target_decision.status` and
  `direct_review_required` before concluding the local route itself is bad.
  Follow-up trials led to explicit `draft_query_plan` selectors and
  `allow_context_blocked_candidate=True`, so agents can draft a direct-clean
  route while preserving the sibling-blocker audit trail. A selection retest
  found automatic drafts were too quiet when multiple ready candidates existed;
  `source_context` now reports ready and unselected-ready candidate indexes so
  agents know when to rerun with explicit selectors.
- A query storage-metadata matrix trial covered local file/object roots,
  directory roots, S3 bucket/prefix/template combinations, HTTPS roots, and
  database-backed table-like storage. It confirmed MCP/Python parity and
  surfaced three draft-plan handoff gaps: sibling-only storage-template
  warnings could make `executable_without_review=false` with no blocking code,
  verified database storage could look executable despite `scan.function=None`,
  and local/HTTPS plans used an over-broad runtime-resolution note. Draft plans
  now add review-gate codes for sibling blockers and missing scan functions,
  and local non-secret paths get a narrower note.
- A database/non-file query-plan trial confirmed `scan_function_not_inferred`
  is the right safety gate for verified database tables and unsupported file
  formats in the current review-only workflow. Database-backed storage still
  uses the generic draft-plan shape, but runtime notes now say to verify
  connection, schema, table, or source access rather than object access, and
  query target candidates plus `plan.scan` now expose database-shaped
  `relation_identifier` and `connection_reference` fields instead of a
  file-like joined connection path.
- A follow-up database/query-handoff trial confirmed
  `ready_for_execution_attempt` is the only execution-attempt gate:
  `executable_without_review=true` can still require runtime resolution or
  binding values. Downstream routing should use
  `review_gate.execution_attempt_blocking_reason_codes` when the ready gate is
  false. For database handoffs, only `scan.relation_identifier` means a relation
  can be passed onward; `scan.connection_reference` without a relation identifier
  is repair/review context for mismatched or incomplete storage metadata.
- A scan-gating query-plan trial found both `scan.uri_template` and
  `scan.relation_identifier` can be present in non-ready plans, including
  `context_review_required` and metadata-review/database-relation cases. The
  scan card now mirrors the review gate as `scan.execution_attempt_ready` and
  `scan.execution_attempt_blocking_reason_codes`, so consumers that start from
  scan fields still see the execution-attempt gate locally.
- A claim-reconsideration slice trial confirmed lifecycle mechanics and pattern
  routes work, but showed that column-only seeds were too narrow for column
  lore. `describe_context_slice` now treats mapped `rc:Column` seeds as valid
  dataset/deep-lore entry points and expands to owning dataset, direct
  claims/patterns, observations, and reconsiderations.
- A catalog round-trip trial confirmed executable-catalog map, profile, query
  context, and draft-plan handoffs survive TriG export/import/reopen. Empty
  mutable graph roles appear in the export record but not as zero-triple TriG
  graph blocks; import into a fresh seeded capsule recreates role metadata.
- A batch restage routing trial confirmed dry-run/real batch, applied
  inspection, stale successor, and repair queues work together. It also showed
  that stale drift can temporarily mask a staged-time validation failure until
  a refreshed successor is checked, so repair queues should be read after
  restage as well as before it. A mixed batch apply follow-up confirmed
  `restaged_revision_iris` is only a creation list; use
  `ready_restage_successor_revision_iris`, then feed
  `apply_staged_revision().post_apply_recheck_revision_iris` into the next
  check/export/restage pass.
- A profile-metric vocabulary trial confirmed project-specific metric IRIs work
  before ontology terms exist, while patterns and claims are the best low-commitment
  place to explain awkward metrics. When the metric meaning should become shared
  vocabulary, stage a pattern-supported ontology promotion rather than directly
  importing terms without review context. A profile-only recipe probe confirmed
  that metric-seeded context slices preserve the profile row in
  `seed_profile_observations`, but `dataset_contexts` may stay empty until a map
  dataset shell exists.
- A profile/catalog workflow-import trial confirmed workflow exports preserve
  map, profile, shared-evidence, query-context, and draft-plan handoffs after
  import/reopen. It also confirmed the expected boundary: workflow exports omit
  `ontology`, so project metric-kind labels/comments/types require the default
  export or another ontology-bearing bundle.
- A column-seed MCP parity trial confirmed mapped column seeds work through the
  wrapper JSON surface. It also showed that profile-only unmapped column IRIs
  are object references, not seedable subjects; seed the profile observation
  when `update_map_column=false` was used.
- A controlled replacement-history trial confirmed `replace_graph_triples`
  handles same-count drift cleanly and stale staged snapshots surface
  `target_digest_drift`. Exact changed triples remain mechanically available
  through staged snapshots/apply checks or explicit before/after exports; plain
  revision history needs authored rationale/metadata if that exact diff matters.
- A partial-storage query-planning trial confirmed root-only object, directory,
  prefix, connection, S3 runtime, and contradicted-partition status pairings are
  mostly clear. It exposed that dataset-owned templates did not copy dataset
  verification into `plan.scan.template_source_verification_*`; draft plans now
  mirror dataset verification there. The same trial reinforced that
  `review_gate.executable_without_review=true` is physical metadata readiness,
  not proof that runtime S3 profiles, credentials, regions, or objects are
  resolved. A query-context contract trial later added
  `review_gate.ready_for_execution_attempt` as the stricter handoff boolean
  that also requires no recorded runtime resolution to remain.
- A query-verification trial confirmed dataset-, storage-, and
  partition-owned templates now carry source verification into draft plans. It
  exposed one wording gap for root-only `storage_access_location` candidates:
  `template_lineage` talked about a template even though the storage root itself
  was the candidate. Draft plans now describe those as storage-root candidates
  from a storage access.
- A staged-revision recovery trial confirmed count/digest drift, restage,
  successor apply, applied diffs, patch-conflict classification, and grouped
  exports work together. It also showed that mixed batch dry-runs can report
  handled stale sources and ready successors as skipped/not-restageable while
  grouped export queues still identify active apply and repair review rows; read
  the queue fields before assuming there is no next action.
- A pattern-promotion trial confirmed `stage_pattern_promotion` can carry shared
  project ontology and project SHACL shapes with several pattern-supported
  framings. A complete framing applied cleanly, while an intentionally
  incomplete sibling stayed useful as a validation diagnostic. After one ready
  alternative is applied, stale sibling live checks should be read alongside
  their original staged validation diagnostics. A later awkward-temporal trial
  exercised one validation-failed map framing plus two ready alternatives and
  confirmed grouped `next_action_queue` and Markdown `Review Queues` keep repair
  and apply-after-review work separated.
- An MCP/Python parity trial compared query context, draft query plans,
  deep-lore slices, staged revision checks/descriptions, dry-run restage, and
  applied diffs across Python and wrapper helpers. All compared payloads were
  JSON-serializable and exactly equal; use dry-run for parity checks where a
  real call would mint a successor.
- A context import/slice trial confirmed RDF project exports preserve enough
  history metadata for dataset, column, pattern, and claim seeds to recover
  useful deep-lore routes after import/reopen. It exposed that revision seeds
  themselves were not deep-lore entry points; `describe_context_slice` now
  expands `rc:GraphRevision` seeds to support, evidence, anchors, application,
  restage, and alternative links. The same trial confirmed a current limit:
  RDF export/import does not preserve SQLite stored snapshot rows for exact
  stale/apply diffs.
- A profile-bundle handoff trial confirmed realistic wide profile bundles,
  shared evidence, run-level patterns, capped `describe_profile_run`, and
  workflow/default export imports work together. It exposed that
  `handoff_entrypoints.map_column_iris` sounded like all mapped profiled
  columns but only listed columns whose map facts were written by the bundle;
  bundles now also expose `updated_map_column_iris` and
  `mapped_profiled_column_iris`. A later mixed-run handoff trial confirmed
  two profiler runs on one dataset can leave `shared_evidence_iris` empty while
  `profile_run_candidates` still routes each run to `describe_profile_run`;
  `handoff_entrypoints.suggested_next_actions` should execute directly, including
  observation-only bundles that have no `describe_dataset` route. A profile-map
  update trial then showed the bundle handoff should route directly into
  `draft_profile_map_updates` when both map context and a shared evidence run
  are available.
- A validation-repair JSON trial confirmed validation-failed, patch-conflict,
  and ready staged revisions stay separated in JSON-like apply checks, grouped
  queues, suggested actions, and dry-run restage classifications. No code change
  was justified; agents should keep reading compact status/decision/queue fields
  before long row-level recommendation prose.
- A staged validation-history trial showed that stored staged validation
  diagnostics are preserved after graph drift, but live replay status can change
  from `validation_failed` to `conflict`. `list_graph_revisions` now supports
  `staged_validation_status="failed"` for staged-time validation failures, and
  grouped export summaries expose `staged_validation_failed_revision_iris`
  beside the live `validation_failed_revision_iris` queue. A later masked
  validation-failure trial showed batch restage item consumers still had to join
  row state back to summaries; batch items now carry source/current
  staged-validation status and result counts directly.
- A conflict/restage queue trial showed that the revision surfaces had enough
  raw signal but made agents join status, stale state, recommendations, and
  suggested actions to choose the next move. Revision lists and grouped exports
  now expose per-row `next_action` plus `next_action_queue`; grouped Markdown
  also prefers current mechanical guidance over older authored review prose in
  the summary recommendation column. A systematisation trial also confirmed that
  immediate restage returns should carry `restaged_from`, `restage_reason`,
  `alternative_to`, and `current_restaged_by` for handoffs.
- An assertion-judgement trial confirmed `stage_map_assertion_change` handles
  physical type, semantic type, row semantics, path template, and caveat
  add/remove/replace cases with useful judgement panels and impact spotlights.
  It exposed that remove panels read awkwardly when only legacy
  `proposed_value` carried the object being removed; judgement panels now also
  expose `target_value` and `removed_value`, and Markdown exports label remove
  values as removed. A later literal-edge trial found that agents also need
  precise typed and language-tagged literal targeting; use `object_datatype` or
  `object_lang` on `describe_assertion_support` and
  `stage_map_assertion_change` for typed boolean/decimal replacements and exact
  language-tagged removals. Exact remove panels now prefer the matched graph
  triple for `removed_value`, preserving datatype or language tag context.
- A stale row-semantics replacement trial showed that raw restage can turn a
  stale single-triple `rc:rowSemantics` add into a validation failure when the
  current map has since added a different row-semantics value for the same
  dataset. Apply checks now use exact snapshot rows to detect that narrow
  same-slot case and suggest
  `stage_map_assertion_change(change_kind="replace", restages_revision=...)`,
  routing compact `next_action` to `repair_or_replace` while leaving ordinary
  count/digest drift on the restage route. A follow-up batch trial showed the
  batch restage helper also needed to respect that route; it now skips those
  rows with `not_restageable_reason="same_slot_replacement"` instead of creating
  the mechanically restaged validation-failure successor. A guarded singleton
  expansion trial then confirmed the same repair route for column
  `rc:physicalType`, column `rc:nullable` with typed boolean payloads, and
  data-asset `rc:schemaStability`, while keeping `rdfs:label` and
  `rc:rowCountSnapshot` out of automatic replacement routing. A stale authored
  replacement trial showed the route must also handle source patches that
  already contain add+remove replacement payloads, not only add-only proposals.
- A controlled replacement/import trial confirmed same-count
  `replace_graph_triples`, revision metadata, default/workflow export
  boundaries, and revision-seed deep-lore expansion. It reinforced the current
  RDF-only handoff boundary: graph snapshot summaries survive default import,
  but SQLite snapshot rows for exact drift do not. A later version-browsing
  trial added `export_revision_snapshots` / `import_revision_snapshots` as the
  opt-in JSON companion for exact applied-diff or stale-drift triple
  reconstruction after RDF import. A follow-up applied-diff export trial found
  `revision_iris=[applied_event]` preserved only the after-snapshot; applied
  event filters now also include the staged source snapshot rows needed for
  exact before/after diff reconstruction.
- A four-agent loop after snapshot-bundle publication confirmed the main
  multi-graph handoff path, stale drift/restage/apply queues, query-planning
  readiness split, and awkward profile/systematisation flow. The snapshot trial
  exposed that empty object strings should only be valid for literal snapshot
  rows, which import validation now enforces. The stale-drift trial reinforced
  `next_action_queue` as the fast routing surface, and the query-planning trial
  added a `query_planning` doc because fresh agents looked for one before
  discovering the executable-catalog details.
- A profile/query-context trial confirmed profile metrics, row-count snapshots,
  shared evidence, and profile-created patterns stay separate from physical
  query readiness: `describe_query_context` and `draft_query_plan` should keep
  using storage/layout/partition facts as blockers. The useful next product
  shape is a review-oriented profile-to-map recommendation surface, not
  automatic promotion of profile metrics into map facts.
- A hard staged-conflict trial confirmed mixed removal+addition patches,
  already-present/absent patch triples, same-count digest drift, alternatives,
  batch restage, applied diffs, and post-apply rechecks work together. It found
  that patch conflicts were wrongly routed to `restage_after_review`; compact
  queues now put `inspect_patch_conflict` and validation failures in
  `repair_or_replace`, while count/digest drift remains `restage_after_review`.
- A query handoff routing trial confirmed `draft_query_plan.handoff_kind` is a
  good queue key, but found that `ready_for_execution_attempt` was too easy to
  over-read when URI-template bindings were still required. The review gate now
  exposes `binding_values_required`, and execution-attempt readiness is false
  until required binding placeholders are gone.
- A profile-to-map draft trial found that explicit sampled wording must beat a
  `sample_size == row_count` heuristic; otherwise a single sampled partition can
  look like a high-confidence full scan. Profile map recommendations now carry
  sample metadata and treat explicit sampled evidence conservatively.
- A snapshot evidence recovery trial showed that workflow RDF plus snapshot
  JSON creates an orphan state: SQLite snapshot rows import successfully, but
  normal revision helpers cannot use them without RDF `history` records.
  `describe_revision_snapshot_evidence` now classifies history-only,
  history-plus-rows, missing-history, and rows-without-history cases. A later
  recovery retest showed project-only RDF imports left stale checks and applied
  diffs with useful prose but no machine-readable recovery route. Snapshot
  evidence now carries structured import actions, applied diffs expose applied
  and source snapshot evidence, and stale checks with missing exact drift rows
  suggest importing the companion snapshot JSON before restaging. A retest
  showed snapshot JSON imported before history RDF was still silent at the
  import boundary; `import_revision_snapshots` now returns
  `post_import_snapshot_evidence` with the same structured `import_trig`
  recovery action.
- A lineage/version-boundary trial confirmed restage/apply chains are
  recoverable from existing list/detail/diff calls, but resource-centric history
  remains scattered, especially for unanchored staged patch touches. Consider a
  future `list_resource_revisions` or lineage helper rather than relying on
  every agent to parse patch payloads by hand.
- A follow-up resource-revision API trial showed a first useful version should
  not return full patch content or only patch subjects. `list_resource_revisions`
  now uses exact RDF parsing on demand to return anchor matches, role-aware
  patch mention flags, applied-source matches, matched triple counts, and the
  existing revision routing row without a storage migration.
- A profile recommendation application trial showed that direct
  `helper_arguments` are smooth for immediate map mutation, but review-gated
  profile updates need helper-equivalent staged patches. Scalar row-count and
  nullable recommendations can be expressed as assertion changes, while missing
  dataset and unmapped column shells require grouped multi-triple patches.
  `stage_profile_map_updates` now groups accepted draft recommendation indexes
  into one staged revision, preserves profile observation/evidence support, can
  carry caller claim/pattern support and extra anchors, and skips sampled
  row-count recommendations by default. A follow-up trial showed agents read
  this most reliably when the response carries `status_counts` and docs say
  accepted indexes can still route to `skipped`.
  A profile-advisory routing trial showed map-update recommendation rows were
  routeable, but metric advisories were prose-only and could not distinguish
  defined from undefined project metrics. Metric advisories now carry
  `advisory_status`, definition state, and structured next actions. A retest
  showed agents also need queue-level counts, so draft/staging responses now
  expose `metric_advisory_count` and `metric_advisory_status_counts`; staging
  review notes preserve the same summary for later reviewers. A later profile
  routing trial found draft responses still made agents infer whether to stage
  or only inspect metric vocabulary; drafts now carry `recommendation_count`,
  stable `recommendation_index` values, and top-level suggested actions/calls.
  An end-to-end profile-bundle retest found staging itself should hand off to
  the read-only apply check; staging responses now suggest
  `check_staged_revision_apply` when a grouped revision is created.
  Another helper-pattern trial found profile-created patterns were still
  structurally prose-only for project-specific metric kinds unless the caller
  manually supplied `pattern_map_implications`. Helper-created profile patterns
  now default their map implications to the profiled dataset or column plus
  project-specific metric kind IRIs from `profile_metrics`, while built-in
  `rc:` metric kinds remain evidence-only.
  A broader workflow trial found undefined metric advisories still left agents
  to bridge manually from metric review to pattern promotion. When a
  same-evidence pattern names the metric as a target or map implication, metric
  advisories now name `promotion_patterns` and suggest a reviewable
  `stage_pattern_promotion` ontology skeleton.
- A resource-revision stress trial confirmed `list_resource_revisions` handles
  anchors, exact patch roles, pagination after filtering, restage chains, and
  applied-source patch mentions, but found two import/repair edges. Applied
  events now recover `applied_source_revision_anchor` from source revision
  anchors even when imported history lacks the staged source patch payload.
  Patch mention scans now report incomplete/unreadable patch payloads and flag
  omitted-match risk when unanchored patch-only matches may have been filtered
  out. Treat unreadable revision counts as distinct pre-pagination source or
  staged revisions, and `omitted_match_risk` as a coarse absence-risk signal.
  A follow-up lineage trial showed agents still had to join selected resource
  rows back to paired staged/applied events and applied diffs manually.
  `describe_resource_revision_lineage` now returns that compact card, including
  resource-filtered applied diff summaries, while avoiding hard dependencies on
  full staged patch payloads for imported partial history.
- A priority query-planning trial found database storage could accidentally
  compose dataset or partition file templates into `relation_identifier`.
  Database relations now come only from storage-access-owned templates;
  dataset/partition templates paired with database storage are review-only
  candidates with `database_relation_template_source_mismatch`.
  A retest confirmed the guard holds for dataset-owned and partition-owned
  templates and that MCP payloads preserve the mismatch details and absent
  relation fields. A root-only database storage trial then found
  `location_kind="object"` could make a bare database connection look ready;
  root-only database candidates now carry `database_relation_template_missing`
  until a storage-access relation template is recorded.
- A staged workflow trial found batch-restage rows made agents join back to
  revision listings to route the current post-batch successor. Batch items now
  carry `next_action_after` and `suggested_next_actions_after` for their
  `current_revision_iri`. A follow-up apply-loop trial found
  `post_apply_recheck_revisions` had the affected sibling IRIs but not their
  live route after the mutation. Apply results now include fresh
  `application_status`, `next_action`, `suggested_next_actions`, and
  `suggested_next_calls` on each post-apply recheck row, so automation can
  restage/repair/inspect without joining back to revision listings first.
- A mixed local/database query-planning retest confirmed explicit
  `candidate_index` plus `allow_context_blocked_candidate=True` now routes a
  direct-clean local partition candidate to `binding_values_required` while
  preserving sibling database-template mismatch audit fields. The same trial
  showed selectorless automatic calls with the allowance can be misread:
  agents should pair the allowance with an explicit selector when the blocker is
  sibling candidate metadata. A later retest found selectorless allowance could
  still clear one direct-clean automatic route; `draft_query_plan` now keeps the
  context review gate active unless the allowance is paired with an explicit
  `candidate_index` or `storage_access_iri`. A follow-up binding trial showed
  that raw placeholders such as `{date}` were too detached from partition lore;
  draft plan binding rows now include partition scheme, likely partition column,
  and granularity hints when the selected template carries that metadata. A retest
  showed `draft_query_plan` was routeable enough through `handoff_kind` and
  `review_gate`, but `describe_query_context` needed a structured route into the
  documented allowance path; query contexts now include `suggested_next_actions`
  with explicit `candidate_index` and `allow_context_blocked_candidate=True`
  when a direct-clean candidate is blocked only by sibling context. A later
  messy-candidate trial found the route executable but the cue subtle;
  `query_target_decision.selected_candidate_direct_clean` now marks that the
  selected candidate has no direct blocker even when the wider context is
  blocked. A broader storage-access trial found ambiguous selector errors were
  useful but collapsed database connection references into `path=...`; candidate
  snippets now label `candidate_path`, `relation_identifier`,
  `connection_reference`, and `template` separately.
- A profile-update staging trial confirmed accepted draft indexes can still be
  skipped by guardrails. In a sampled profile run, accepting a sampled row-count
  replacement and two column recommendations staged only the column updates by
  default; read `status_counts`, `staged_recommendation_indexes`, and
  `skipped_recommendation_indexes` before assuming every accepted index became a
  patch.
- A staged-revision recovery retest confirmed conflict detection, batch
  restage, grouped export routing, apply-one-then-recheck, and applied snapshot
  diff reconstruction work coherently. It exposed one final routing asymmetry:
  direct `check_staged_revision_apply` responses had rich
  `suggested_next_actions` but no compact `next_action`; apply checks now carry
  that route directly, matching revision lists, grouped exports, batch restage
  items, and post-apply recheck rows. Later staged-revision and mixed-bundle
  trials found the same gap in
  `describe_staged_revision(include_current_apply_check=True)`; the embedded
  `current_apply_check` summary now carries `next_action` too, so a cold
  one-revision inspection has the same compact routing surface.
- A staged-map recipe trial confirmed `record_map_dataset` rejects prose
  `row_semantics` early, while generic staged Turtle records validation-failed
  review objects. Staged validation diagnostics now add a row-semantics hint:
  use `rc:EventRow`, `rc:SnapshotRow`, `rc:AggregateRow`, or
  `rc:DimensionRow`, and put prose row-grain details in comments, caveats,
  observations, or patterns. A later awkward-temporal trial showed
  `schema_stability="rc:EvolvingSchema"` was syntactically accepted before
  failing SHACL; map helpers now preflight known schema-stability and
  layout-verification terms before writing map triples.
- A mixed retrieval handoff trial over map context, profile observations,
  claims, patterns, and revision history found the route clear but the raw
  `describe_context_slice` resource rows still made agents infer trust from
  graph lists. Context-slice resources now include `surface_role`, a compact cue
  for current map context, observation context, pattern synthesis, evidence
  support, revision history, vocabulary context, mixed context, or
  referenced-only objects.
- A physical-metadata authoring trial confirmed `compression_codec="zstd"` is a
  plain-name error, not a reason to accept arbitrary bare codec strings. The
  executable-catalog example now uses canonical `rc:ZstdCompression`, and the
  `compression_codec` preflight message suggests compression-specific CURIEs.
- A staged recovery route trial found single restage and batch restage naming
  routeable, provided scripts follow the structured action arguments. Docs now
  say to use `next_action_after.arguments["iri"]` or `current_revision_iri`
  after batch restage, while single restage `revision_iri` is the created
  successor.
- A direct restage recovery trial found `restage_staged_revision()` created a
  successor with provenance but no immediate route, so unattended agents had to
  remember to re-check the successor before applying. Direct restage responses
  now include `status_after`, `routing_decision_after`, `next_action_after`,
  `next_action_queue_item_after`, and `suggested_next_actions_after` from a
  fresh apply check on the created successor.
- A profile-bundle handoff trial showed two `describe_context_slice` actions in
  map-present bundles are useful, not accidental duplication: the dataset seed
  loads current map context, while profile-observation seeds carry the direct
  run handoff. Docs now tell agents to distinguish them by `action_label` and
  `arguments`.
- A profile-map staging shape trial found automation could identify
  `stage_profile_map_updates` results only by field constellation.
  `ProfileMapUpdateStagingRecord` now carries
  `result_kind="profile_map_update_staging"` as a semantic discriminator.
- Awkward systematisation and pattern-promotion trials confirmed grouped exports
  route mixed ready/failed alternatives well, but the initial staging response
  still made agents discover that route later. `stage_systematisation` and
  `stage_pattern_promotion` now return `result_kind="systematisation_draft"`,
  a draft-level `next_action_queue`, a grouped `export_staged_revisions`
  suggested action, and per-revision `check_staged_revision_apply` suggested
  actions.
- A staged-version recovery trial confirmed post-apply recheck rows, grouped
  review queues, batch restage `current_revision_iri`, and snapshot lineage are
  enough for autonomous routing. The remaining friction was naming: resource
  lineage used only `current_staged_revision_iri`. It now also exposes
  `current_revision_iri` with the same current staged successor value so scripts
  can share batch-restage current-row handling.
- A profile-bundle and metric-promotion trial found map-update staging, metric
  advisories, pattern-supported ontology promotion, and validation all routed
  correctly, but generic suggested export paths were awkward for concurrent
  scratch runs. Suggested staged-revision export actions now include
  revision-derived slugs and short hashes in `/tmp` paths; agents can still
  override them with run-directory paths.
- A revision snapshot handoff trial confirmed RDF-only, snapshot-only, and
  RDF-plus-snapshot imports route correctly, but snapshot-evidence suggested
  actions used executable-looking generic paths. Those actions now mark their
  `path` arguments with `path_is_placeholder=True` and tell agents to substitute
  the real handoff artifact path before importing.
- A profile-map and metric-vocabulary trial found that mixed staging preserved
  metric advisories, but the top-level next-action lane only showed the staged
  map apply check. `ProfileMapUpdateStagingRecord` now keeps that map lane in
  `suggested_next_actions` and exposes a separate
  `metric_advisory_suggested_next_actions` lane, plus
  `metric_vocabulary_review_required`, so queue-following agents do not mistake
  a staged map patch for resolved project metric vocabulary.
- A query-planning trial confirmed the relation/path snippet split works for
  ambiguous database candidates and explicit context-blocked selections. The
  remaining gotcha is RDF-shaped candidate order: multiple ready candidates are
  not an authoring-preference list. Treat `candidate_index` as a pointer into the
  returned response and inspect `unselected_ready_candidate_indexes` before
  deciding which ready relation or path to draft.
- Staged-revision recovery trials found that a source framing that failed
  staged-time validation can later restage as mechanically ready if current graph
  state supplies the missing semantics. Apply checks preserve that history with
  `decision="inspect_restaged_source_validation_failure"` and route same-payload
  successors through `repair_or_replace`; caller-authored revised successors keep
  the warning but can route to `apply_after_review` when they validate.
  Direct checks on the old failed source preserve `validation_failed`
  diagnostics but route compact `next_action` to `current_restaged_by` once a
  repaired successor exists.
- A staged-revision recovery trial found grouped exports had useful status
  counts but `list_graph_revisions` required scripts to recompute them from row
  data. Revision lists now expose returned-page application, stale-resolution,
  and staged-validation status counts alongside `next_action_queue`.
- A repeated profile-bundle trial found that accepting one representative
  profile-map recommendation staged the same RDF patch as accepting all duplicate
  rows, but lost sibling profile-observation support. Profile map drafts now
  expose duplicate groups for recommendations and metric advisories, and
  representative staging preserves all grouped observation support on the staged
  revision. A follow-up trial found the default staging action still suggested
  every duplicate sibling; drafts now expose `representative_recommendation_indexes`
  so agents can review one index per duplicate group.
- A no-op successor trial found post-apply recheck routing was correct but less
  self-contained than a direct apply check. Recheck rows now include the live
  `decision` and `blocking_reasons`, so a no-op successor made stale by a sibling
  apply can be routed to restage without an immediate extra check just to learn
  why.
- A query-planning storage-access trial found partition-owned path templates gave
  useful binding hints, while dataset/storage-access-owned placeholders made
  agents infer likely source columns from names. Non-partition binding rows now
  include best-effort `candidate_column_matches` with match kind and confidence;
  these are handoff hints, not inferred runtime binding values.
- A follow-up query-planning trial found multiple plausible placeholder/column
  matches were visible only by list length. Binding rows now expose
  `candidate_column_match_status` so ambiguous column hints are explicit and
  review-gated.
- A mixed-storage query-planning trial found `draft_query_plan.source_context`
  exposed peer ready candidates, but `describe_query_context` did not. Query
  contexts now carry `ready_candidate_indexes` and
  `unselected_ready_candidate_indexes`, and ready suggested actions mention peer
  ready candidates before automation follows response-local candidate order.
- A profile recommendation trial found sampled row-count recommendations were
  present in `representative_recommendation_indexes` even though default staging
  skips them. Draft recommendation rows now expose `default_stageable` and
  `default_skip_reason` so agents can see default staging guardrails before
  calling `stage_profile_map_updates`.
- A follow-up profile trial found sampled-only drafts still advertised a
  default staging action that would become a no-op. The top-level
  `stage_profile_map_updates` action now includes only representative rows with
  `default_stageable=True`; sampled row-count overrides must be explicit.
- A profile metrics gap trial found same-evidence full-scan profile observations
  can disagree on scalar map facts, such as dataset row count or column
  nullability. These recommendations now stay reviewable but are not
  default-stageable, and `stage_profile_map_updates` skips an accepted conflict
  set unless the caller chooses one observed value explicitly. A follow-up
  scalar-only conflict trial found that safe choose-one staging was too hidden;
  `draft_profile_map_updates.scalar_conflict_groups` now exposes per-value
  representative indexes, grouped observation support, and explicit option
  stage actions outside the default `profile_map_updates` lane. A later
  queue-following trial found conflict-only drafts still looked actionless to
  agents that read only grouped lanes, so those option actions now also appear
  in `profile_scalar_conflict_review` with `source_scalar_conflict` metadata,
  while remaining out of the flat `suggested_next_actions` list. A later
  exported-review trial found those lanes still forced agents to rejoin against
  the live recommendation list before comparing sample/full-scan support, so
  scalar conflict options and lane sources now include
  `recommendation_contexts[]` with profile observation, sample, basis,
  observed-count, profile-row-count, and confidence fields.
- A profile action-queue trial found mixed map, metric, and type follow-ups were
  mechanically followable but noisy when flattened together. Draft profile-map
  responses now expose `suggested_next_action_groups` and
  `suggested_next_call_groups` with separate `profile_map_updates`,
  `profile_scalar_conflict_review`, `metric_vocabulary_review`, and
  `profile_type_review` lanes while preserving the flat `suggested_next_actions`
  compatibility list.
- A staged-revision recovery trial followed
  `post_apply_recheck_revisions[].next_action.arguments["iri"]` into
  `restage_staged_revision`, checked the successor, applied it, and ended with
  no current staged work. The product route was adequate; regression coverage now
  locks that autonomous recovery path.
- A same-subject staged-alternative trial confirmed that applying one
  `rc:rowSemantics` framing can make the competing framing restage into a
  `validation_failed` max-count repair queue rather than an apply queue. Treat
  that as correct: the repair should be a replacement/removal+addition, and
  `current_staged_work_only=True` should show only the active repair item.
- A validation-dependency staged-revision trial found that applying a project
  shape could invalidate an otherwise ready map candidate without a shared patch
  target. Post-apply queues now include validation-dependency rechecks and expose
  `recheck_reasons` so agents can see whether a row was queued by a shared target
  graph or by a changed validation dependency such as `shapes`.
- A wide-context slice trial found that `max_triples` only capped raw RDF, while
  structured dataset summaries still returned all selected columns. Truncated
  broad slices now warn when structured context remains large and suggest a
  narrower column, profile, metric, or pattern seed.
- A profile type-review follow-through trial found that optional
  `record_pattern` synthesis was useful but not obviously carried into later
  staged assertions. Type-review staging suggestions now include an empty
  `supporting_patterns` slot and a carry-forward note for the returned
  `pattern_iri`.
- A profile metric-promotion follow-through trial found that single Markdown
  exports showed support counts and selected patterns but not the rolled-up
  profile observations or evidence IRIs. Single staged-revision exports now add a
  generic `Linked Support` section for stored support links.
- A query-planning storage trial confirmed context-blocked clean candidates and
  storage-access ambiguity behaved well. Docs now call out that
  `storage_access_iri` can still be ambiguous when partition/template candidates
  share that access; use `candidate_index` to select the exact relation.
- A revision snapshot import/export trial confirmed RDF-only handoffs recover
  lineage and count/digest context, while companion snapshot JSON restores exact
  diffs. Stale apply-check snapshot-import suggestions now mark the example
  `/tmp/revision-snapshots.json` path as a placeholder, matching
  `describe_revision_snapshot_evidence`.
- An import/validation boundary trial found malformed Turtle/TriG and malformed
  project SHACL shapes could leak raw parser/pySHACL exceptions, while a
  `rcg:` typo such as `rcg:typo_map` silently created an out-of-scope graph.
  Imports and validation now wrap those failures as `DoxaBaseError`, and Rich
  Canopy graph IRIs must name known roles unless explicitly mapped by
  `graph_map`.
- A query-planning storage-selection trial found globally blocked contexts can
  leave `ready_candidate_indexes` empty even when several candidates have no
  direct warning or error and can be drafted with
  `allow_context_blocked_candidate=True`. Query context and draft source context
  now expose direct-clean candidate indexes separately from stricter ready
  indexes.
- A cold-start ergonomics trial found broad deferred-tool searches may still
  under-return central route helpers. In lazy environments, search exact MCP
  names such as `doxabase.get_doc`, `doxabase.list_entities`, and
  `doxabase.describe_context_slice` before treating them as missing.
- A profile type-review follow-through trial confirmed staged type assertions
  preserve profile observation/evidence support and also merge related
  assertion-support patterns. Expect the final revision to carry nearby column
  lore in addition to the specific pattern you just recorded.
- An awkward systematisation trial confirmed caller-authored competing framings,
  shared shapes, validation failures, support roll-up, and grouped exports worked.
  The runtime now warns when later framings are linked as alternatives to a
  first framing that did not route to `apply_after_review`, and docs remind
  agents that intentionally invalid probes should not be first unless that is
  the desired comparison anchor. A follow-up pattern-promotion trial found that
  prose alone made automation parse the warning; these drafts now also return a
  `first_alternative_anchor_not_ready` structured warning with
  `suggested_rerun_arguments={"link_alternatives": False}`.
- A staged-lineage/rebase trial found agents naturally tried to include an
  applied event IRI in a grouped staged-review export. Grouped staged exports now
  fail with a route-specific message: pass staged patch IRIs, and inspect
  applied events with graph revision, lineage, or applied-diff helpers.
- A stale-alternative recovery trial found agents could follow
  `current_restaged_by`, handled-stale summaries, and grouped queues after
  applying one alternative and restaging a sibling, but a ready successor that
  remains an alternative to an already-applied source still needs semantic
  gating. Bundle summaries now list those rows in
  `ready_restage_successor_alternative_to_applied_source_iris` and warn that
  mechanical readiness is not approval to make both alternatives durable. A
  follow-up scratch trial confirmed grouped export was clear but single-row
  checks, descriptions, and lists still required inference; those payloads now
  expose `alternative_gate` with `alternative_to_applied_source`,
  `semantic_review_required`, `applied_source_iri`, and `applied_revision_iri`.
  A later trial found the compact apply action could still look ordinary when
  the generic semantic risk was `none`; ready alternatives gated only by
  `alternative_gate` now keep the `apply_after_review` queue but label and
  explain the review/export/apply actions as semantic-review-only.
- A grouped snapshot-evidence trial found JSON list/lineage helpers made mixed
  RDF-only and exact snapshot recovery clear, while grouped Markdown hid the
  status split in scattered drift notes. Grouped staged-review Markdown now adds
  a `Snapshot Evidence` panel: a compact complete-state confirmation when every
  included row has exact snapshot rows, and a detailed import-action table when
  rows are incomplete. A batch-restage follow-up found scripts still had to
  cross-check that panel before trusting dry-run rows; batch items now carry
  source/current `snapshot_evidence` plus completeness labels directly.
- A resource-lineage recovery trial found snapshot exports seeded only by an
  applied event restore the applied event and its direct staged source, but not
  older restage ancestors. Generic revision lineage now warns when any visible
  restage-chain row has RDF count/digest metadata but lacks stored snapshot rows.
- A resource-lineage count-basis retest found resource-filtered applied diffs
  work across map, ontology, and shapes once exact snapshot rows are restored,
  but wrong-resource lineage requests for an existing revision sounded like
  missing history. Those errors now distinguish "revision exists, but not for
  this resource" from genuine missing RDF history.
- A context-slice linked-support trial found `route_explained` is an attractive
  but invalid profile name, and plain `rc:Observation` seeds were too thin for
  handoff work. Route explanations live in `routes`, `route_legend`, and
  `route_counts` on every valid profile; dataset/deep-lore slices now expand
  ordinary observation seeds through observed resources and support.
- A profile followthrough trial confirmed a mixed capsule can safely handle
  duplicate full-profile map updates, same-evidence metric promotion, manual
  type-advisory pattern handoff, and sampled-row guardrails in sequence. Accept
  representative duplicate indexes for map staging, then handle metric/type
  advisories as separate review lanes.
- A profile/query-planning trial confirmed storage/layout/partition metadata,
  caveats, profile evidence, metric advisories, and draft query planning compose
  cleanly. It also caught a docs-shape trap: `describe_pattern.evidence` is a
  list, even when exactly one evidence resource is linked.
- A profile-bundle trial confirmed observation-only profile bundles, profile
  map-update drafts, metric advisories, type advisories, and staged profile map
  updates compose cleanly. It also found that undefined project metric IRIs can
  appear as `referenced_only` in context slices; use
  `draft_profile_map_updates.metric_advisories` for vocabulary status.
- A query-planning/profile handoff trial found `describe_query_context` used
  profile-derived row-count snapshots but did not expose the evidence/run
  entrypoint behind them. Query contexts now carry `profile_summary` beside
  `row_count_snapshot`. A retest confirmed the normal shared-evidence route and
  added a `describe_profile_run` suggested action so mixed profile histories are
  easier to check before drafting a query plan.
- A multi-patch staged-revision trial found count drift rows for the same graph
  can show different expected counts because each patch records its own staged
  replay point. Count-drift rows now expose `patch_sequence_index` and
  `expected_before_basis`; exports show the same cue.
- An applied diff/version-browsing trial found staged preview counts for
  `ontology` and `shapes` include immutable seed context, while applied snapshot
  evidence remains role-local. Patch rows, apply checks, count drifts, applied
  source summaries, and exports now expose `count_basis` so agents can compare
  those counts intentionally.
- A version-recovery trial found handled stale sources had correct successor
  routing but summaries still led with generic conflict wording. Direct
  apply-check summaries now start with handled-by-restage wording when
  `current_restaged_by` exists, while preserving historical conflict status.
- A query-planning metadata trial found `redundant_partition_key` is easy to
  mistake for a literal path placeholder. It must be a resource reference,
  usually the partition column IRI/CURIE; placeholder strings stay in
  `path_template`.
- A staged-revision list-routing trial confirmed full revision lists can show
  historical handled rows as `application_status="conflict"`. Treat
  `is_current_staged_work=False` with
  `stale_resolution_state="stale_handled_by_restage"` as informational, and use
  `current_staged_work_only=True` for mutation queues. When keeping the full
  returned history page, read
  `returned_current_staged_work_application_status_counts` for current-work
  status and reserve `returned_application_status_counts` for page/history
  status.
- A handled-stale export trial found stale-only review bundles could hide the
  refreshed successor behind stale-source labels or a restage recommendation.
  Direct apply checks now expose `restaged_by`, `current_restaged_by`, and
  `stale_resolution_state`; handled stale rows point compact `next_action` at the
  current successor, and grouped Markdown includes `Recommended review` rows.
  A follow-up stale-restage-apply trial found direct apply checks and revision
  list rows still stopped at that successor after it was applied, even though
  lineage routes reached the applied event. Handled stale rows now preserve
  `current_restaged_by` as the staged successor while routing `next_action` and
  leading suggested actions to the applied event when the successor has landed.
- A docs retrieval trial found large MCP docs hid deep sections behind the
  default prefix. Doc listings now expose section headings and `get_doc` accepts
  `section` or `start_char` for bounded navigation.
- A query-planning storage-metadata trial found S3/database/runtime metadata
  handoffs were conservative, but multiple linked physical layouts could make
  the draft infer a scan function from the first layout. Distinct layout
  signatures now produce `ambiguous_physical_layout`, block execution-readiness,
  and leave `scan.function` unset until the intended layout is modeled or
  selected. A follow-up mixed local/S3/database mirror trial showed that agents
  need a per-draft escape hatch before DoxaBase has candidate-scoped layout
  modeling; `draft_query_plan(physical_layout_iri=...)` now records the reviewed
  layout choice and clears that layout ambiguity only for the selected draft.
- A cold-agent MCP-docs trial found lazy/deferred tool discovery can hide named
  DoxaBase tools until the exact tool name is searched. `start_here` now reminds
  agents to search exact `doxabase.*` names before assuming a documented tool is
  unavailable, and clarifies that `doxabase.search` searches capsule RDF rather
  than agent docs.
- A grouped staged-export trial found duplicate input IRIs inflated status
  counts, next-action queues, and post-apply recheck hazards. Grouped exports now
  normalize revision inputs to first-seen unique order before building summaries.
- The same export trial found source-only handled-stale bundles could recommend a
  refreshed successor that was not included in the bundle. Bundle warnings now
  name recommended review IRIs outside the artifact so agents export or describe
  the successor before acting.
- A query-planning sibling-blocker trial found `describe_query_context` could
  select a direct-clean candidate while overall context stayed review-gated by
  bad sibling metadata, but the suggested `draft_query_plan` call omitted
  `allow_context_blocked_candidate=True`. Suggested actions now include the
  allowance whenever the selected candidate is direct-clean and broader readiness
  is not `ready_for_query_planning`.
- A direct-clean database-relation trial found the explicit allowance route was
  correct but still easy to overread when sibling copied-file metadata left the
  source context blocked. Draft source contexts now include
  `selected_candidate_note`, summarizing the selected candidate, handoff route,
  and sibling/context blocker codes that still remain in
  `review_gate.all_issue_codes`.
- A follow-up query-plan consumer trial confirmed `selected_candidate_note`
  helps humans, but machine consumers must still route on `handoff_kind`,
  `review_gate.ready_for_execution_attempt`, `context_blocked_candidate_used`,
  and execution blocking codes rather than scan fields that can look usable
  under review-gated plans.
- A follow-up query-planning handoff trial confirmed ambiguous layouts,
  candidate selection errors, S3 runtime blockers, and database relation cards
  route conservatively. It also clarified that downstream agents must gate any
  execution attempt on `review_gate.ready_for_execution_attempt`, not
  `handoff_kind` alone; partition binding notes now say the recorded
  granularity belongs to the partition scheme.
- A downstream query-plan consumer trial confirmed the fields are sufficient for
  a careful non-executing router, but easy to misuse if clients treat
  `executable_without_review`, empty `blocking_reason_codes`, or
  `database_relation_handoff` as execution permission. Consumer recipes now
  route first on `ready_for_execution_attempt`, then database relation handoff,
  runtime resolution, binding values, and remaining issue codes.
- A follow-up docs-navigation trial confirmed fresh agents can use doc sizes,
  section anchors, `get_doc(section=...)`, and offset slices with
  `selected_section`. Its remaining friction was environmental: cancelled MCP
  calls and read-only `bwrap` sandbox setup failures should be diagnosed as
  tool-execution failures, not stale DoxaBase schemas.
- A longer staged-lineage trial found batch restage top-level
  `current_revision_by_source` could point a stale ancestor at an intermediate
  successor that the same batch later restaged. Real batch runs now recompute
  the top-level current map after processing the whole batch; row
  `current_revision_iri` still records the route observed for that item.
- A profile/systematisation trial confirmed representative default staging,
  duplicate support preservation, metric advisory routing, and pattern-promotion
  skeletons work together. It also found type findings are easy to over-expect:
  profile-recorded `physical_type` / `value_type` facts should not become
  current map facts without review. Observation-only type findings are now
  persisted on profile observations and surfaced as profile-map type advisories;
  follow those review actions before recording or staging map type assertions.
- A profile-type handoff trial found unmapped type advisories were mechanically
  correct but did not explain the column-shell sequence. They now carry
  `related_recommendation_indexes` / `related_recommendation_kinds` and a routing
  note that points agents at the matching `unmapped_profiled_column`
  recommendation before reviewing type assertions.
- A repeated profile-type advisory trial found duplicate grouping alone was not
  enough because staged assertion calls still carried per-profile rationale.
  Type advisory suggested actions now collapse duplicate top-level calls while
  preserving every grouped profile observation as pattern/staged-assertion
  support.
- A systematisation/pattern-promotion trial confirmed grouped exports preserve
  pattern-first, ontology-first, concrete map, and intentionally invalid
  diagnostic framings side by side. Validation on an incomplete shape-backed
  sibling gave useful repair guidance while the repaired sibling stayed
  reviewable.
- A generic staged-lineage design trial found agents could reconstruct
  restage/apply chains from list rows, staged details, applied details, and
  resource lineage, but the join was too much ceremony when the handoff started
  with only a revision IRI. `describe_revision_lineage` now provides a read-only
  graph-level lineage card with selected/pair roles, restage chain, alternatives,
  current/latest pointers, warnings, and next-action routing while leaving patch
  content and applied diffs to the existing focused helpers.
- Follow-up lineage trials confirmed the helper routes normal restage/apply
  recovery and RDF-only import boundaries, but agents expected one consistent
  suggested-call field and an obvious signal when exact snapshot rows were
  absent. Lineage now derives a suggested action from `next_action` when the
  latest row has no list/check suggestions, includes applied events reached from
  alternative staged rows in `related_revision_iris`, and warns at top level
  when selected/paired/latest/current rows only have count/digest history or
  orphan snapshot rows.
- An imported odd-history lineage trial found manually authored
  `rc:restagesRevision` links could put non-staged records into restage chains,
  parallel restage successors were silently collapsed to the lexically first
  route, and applied events with missing staged sources mislabeled themselves as
  the staged revision. Lineage now warns for those integrity hazards, includes
  all visible parallel successors and their applied events in
  `related_revision_iris`, and leaves `staged_revision_iri=None` when an
  applied event's source is absent. A grouped-export follow-up found the
  non-followed successor may itself already be applied; export summaries now
  recommend inspecting that applied event and warn with the source, successor,
  and applied route before agents follow the current branch.
- A resource-first import recovery trial confirmed history-bearing imports route
  applied/source pairs and resource-filtered diffs well, but a one-row resource
  lineage card still hid sibling alternatives unless the caller made a separate
  generic lineage call. Resource lineage now mirrors graph lineage
  `restage_chain_iris` and `alternative_revision_iris`, and merges generic
  related revision IRIs into its local resource route. A follow-up
  resource-first parallel-branch trial found the related IRIs alone were too
  quiet; resource lineage now also carries graph-lineage warnings so applied
  sibling branches and other imported oddities are visible in the resource card.
- A mixed staged-work queue trial confirmed current-work queues classify ready,
  stale, validation-failed, and already-applied rows correctly, but found that
  staged-time validation failures could drift into live `conflict` and lose
  their repair route in compact next actions and grouped repair lists. Compact
  routing now preserves failed staged-validation rows as `repair_or_replace`,
  including post-apply recheck rows, and docs clarify that
  `suggested_next_actions` are the review-first sequence while `next_action` is
  the row route.
- An already-effective stale-source trial showed agents could be routed into a
  mechanical restage even when patch checks already showed the target payload
  had zero effective current delta, producing only a no-op successor. Stale
  count/digest conflicts now keep their drift status but route compact
  `next_action` to informational `inspect_no_effective_change`, and batch
  restage skips them with `not_restageable_reason="already_effective"` instead
  of manufacturing a no-op. The direct restage helper now rejects the same route
  for future calls. This is deliberately not `already_applied`; only an applied
  revision event records durable review lineage.
- A follow-up stale/no-op closure trial showed that informational rows can still
  trap unattended agents in repeated inspect/export loops if review intent has
  nowhere durable to land. `record_staged_revision_review_decision` now records
  a history-only disposition such as `no_effective_change`, keeps the staged row
  visible in full history with `review_resolution`, and removes it from
  `current_staged_work_only=True` frontiers. It refuses apply/restage/repair
  mutation targets unless an explicit override records that review decided to
  close the proposal without mutating.
- A query-repair routing trial showed the fixture-staleness warning worked in
  project brief and issue details, but could still be missed by agents that
  drove repairs directly from `suggested_repair_action_groups`. Repair groups
  now expose `group_advisories` with the same `query_fixture_staleness_review`
  anti-loop cue before scripts stage repeated missing-storage repairs for stale
  AIS or Polymarket fixture capsules.
- Post-rebuild workflow trials found four handoff polish points. Query contexts
  with both profile-run evidence and a real query target now have regression
  coverage for the intended action order: inspect `describe_profile_run` before
  drafting the selected query plan. Systematisation drafts now warn about an
  invalid first alternative anchor only when a later framing actually
  default-linked to it; per-framing `alternative_to` is the route for ready
  siblings that should point elsewhere. Resource lineage misses now tell callers
  when `include_patch_mentions=False` prevented patch-payload discovery. Grouped
  staged-revision Markdown now includes `Count Basis Context` for mixed or
  seed-expanded patch bases so reviewers see that ontology/shape preview counts
  include seed graphs while revision snapshots remain role-local.
- Follow-up staged workflow trials confirmed the count-basis panel is quiet for
  simple map-only bundles and useful for mixed ontology/shapes/map bundles; test
  coverage now pins both cases. A staged conflict/rebase trial found the core
  recovery loop sound but resource-first lineage still made agents infer the
  latest applied version after a current successor was applied; resource lineage
  now exposes `latest_revision_iri` and `latest_role` from graph lineage. A
  profile workflow trial found agents following only the `profile_map_updates`
  lane could miss same-evidence profile-pattern support; default
  `stage_profile_map_updates` suggestions now prefill overlapping
  `supporting_patterns` while keeping metric and type advisories review-only.
- Further retests found the profile support selector correctly ignores
  unrelated same-evidence patterns, and query-planning gates around explicit
  candidate allowance already behave coherently. Applied revision browsing had
  one remaining ceremony gap: agents could see before/after diffs but not the
  full contents of one stored snapshot without exporting JSON by hand.
  `describe_revision_graph_snapshot` now exposes one role-local stored snapshot
  with bounded triples, while `describe_applied_revision_diff` remains the
  before/after changed-triple helper.
- An awkward profile workflow trial found auto-carrying every same-evidence
  profile-observation pattern into `stage_profile_map_updates` could pull
  metric-vocabulary rationale into a map patch. Default profile map staging now
  auto-passes only same-evidence patterns that target or imply the dataset or
  recommended map resources; metric-only and type-only patterns stay in their
  review lanes unless explicitly supplied as support.
- Follow-up query, revision, profile, and systematisation trials confirmed the
  new layout selector, snapshot helper, and profile support selector behavior.
  They added three small handoff lessons: applied-event rows now suggest
  `describe_applied_revision_diff`, profile map-staging docs now match the
  dataset/recommended-resource support rule, and systematisation docs warn that
  shared additions attach to every framing while transitive evidence is not
  direct staged-revision evidence unless passed or linked directly.
- A further trial wave found three small agent-facing gaps. Same-evidence
  profile metric promotion now seeds the ontology skeleton comment from the
  supporting pattern so the draft is less empty while still requiring review.
  `draft_query_plan(storage_access_iri=..., physical_layout_iri=...)` now says
  when the layout matched but the storage selector is still path/relation
  ambiguous. Same-slot replacement conflicts now keep the mutation route clean:
  suggested actions omit mechanical restage, batch restage skips them, and
  direct `restage_staged_revision()` rejects them so agents follow
  `stage_map_assertion_change(..., restages_revision=...)`.
- The next four-way trial wave found three small polish points worth keeping.
  Ambiguous physical-layout query contexts now add concrete
  `draft_query_plan(candidate_index=..., physical_layout_iri=...)` actions for
  each layout signature. A later peer-candidate retest found those actions were
  selected-candidate-only; query contexts now emit the same reviewed
  candidate/layout pairs for peer candidates whose only direct blocker is
  `ambiguous_physical_layout`. Profile value-frequency inputs accept `count` as
  a profiler-output alias while responses keep `frequency`. Pattern-promotion
  evidence placement is now pinned in tests/docs: supporting-claim evidence is
  reachable through context slices but is not direct staged-revision evidence
  unless passed explicitly or linked directly on the pattern. A staged-revision
  trial also confirmed restage/apply/snapshot lineage works on realistic stale
  caveat proposals; validation-blocked `apply_staged_revision` errors now name
  the staged IRI and exact inspect call.
- Post-rebuild metric and query-planning trials found three scriptability gaps
  that are now pinned. Ambiguous project metric definitions can surface the same
  pattern-backed `stage_pattern_promotion` repair skeleton as undefined
  metrics, while still inspecting the existing ontology definition first.
  Same-evidence prose patterns that only mention a project profile metric now
  appear as context-only metric advisory patterns with `describe_pattern`
  actions, not promotion support. Physical-layout selection actions now include
  `allow_context_blocked_candidate=True` when resolving layout leaves a
  direct-clean candidate and the remaining blockers belong to sibling candidate
  metadata, so scripts do not need an extra retry to reach the next execution
  gate.
- Query-planning execution-blocker trials found agents could route from the
  ordered `execution_attempt_blocking_reason_codes` list, but simple automation
  still had to pick its own headline blocker. Draft query plans now expose
  `primary_execution_attempt_blocking_reason_code` on both `review_gate` and
  `scan` as the first ordered blocker, or `None` when no execution-attempt
  blocker remains. Treat it as a compact queue key while preserving the full
  ordered list for review detail.
- Staged-revision recovery trials confirmed the public routing fields are
  enough for both ordinary count-drift restage/apply/snapshot browsing and
  same-slot replacement repair via the suggested `stage_map_assertion_change`
  payload. The main follow-up is regression confidence and docs fidelity:
  response-shape docs should list the live `current_apply_check` and
  snapshot-evidence fields scripts actually route from, and grouped snapshot
  completeness labels should include `partial-extra-rows` for imported bundles
  with extra stored snapshot roles.
- Profile-to-query and systematisation trials confirmed recent handoffs compose
  without a behavior fix: staged profile map updates can leave profile metric
  and type-review lanes for separate follow-up, query context can still route
  through profile evidence before `draft_query_plan`, and mixed
  `stage_pattern_promotion` alternatives expose usable routing queues. Treat
  `next_action_queue` as next-move grouping, not preference order among ready
  alternatives.
- A query-planning profile-history trial found count-ranked profile run
  candidates needed one more freshness cue: when candidates tie on returned
  profile count, prefer evidence whose returned dataset-profile `row_count`
  matches the map `row_count_snapshot`. Candidates now expose
  `dataset_profile_row_counts` and `row_count_snapshot_matches` so agents can
  see the tie-break and still inspect `describe_profile_run` before treating a
  profile-derived count as current.
- A sampled-profile query-planning trial found `update_map_snapshot=true` could
  promote sampled row counts straight into durable `rc:rowCountSnapshot`,
  bypassing the sampled row-count staging guardrail. Profile recording now
  writes row-count snapshots only for full-scan-looking profile bases by
  default; sampled or unknown-scope counts stay as profile evidence unless the
  caller explicitly opts into `allow_sampled_row_count_snapshot`. Profile-run
  candidates also expose row-count basis fields so query planners can tell when
  a matching count is not full-scan evidence.
- Handoff recovery and context-lineage trials found the existing recovery
  mechanics mostly held up. RDF-only imports route to companion snapshot JSON
  when exact triples are unavailable, and full RDF+snapshot imports recover
  applied diffs and resource lineage. Grouped Markdown's `Snapshot Evidence`
  panel now gives positive complete-state confirmation for human reviewers; use
  `describe_revision_snapshot_evidence` or JSON `snapshot_evidence` fields for
  row-local script checks. Truncated column-seeded `deep_lore` slices can still
  answer subtle promotion questions through structured resources and route
  counts; they now expose `suggested_next_actions` that narrow to linked
  `pattern_brief` slices before offering a higher-`max_triples` raw RDF retry.
- Storage/query handoff trials found peer ready candidates were visible through
  index lists, but scripts still had to parse prose or storage-selector
  ambiguity errors to draft them. `describe_query_context.suggested_next_actions`
  now includes explicit `draft_query_plan(candidate_selector=...)` actions for peer
  ready and peer context-blocked direct-clean candidates, including
  `allow_context_blocked_candidate=True` where needed.
- Follow-up staged-revision and query-planning trials found two small
  documentation/payload gaps. Resource-first lineage on an old stale source now
  follows an applied restaged successor for `applied_revision_iri` and
  resource-filtered `applied_diff`, while keeping the original route in
  `restage_chain_iris`. Query-planning repair for database relation metadata
  may still live in `issues[].details` rather than in a dedicated suggested
  repair action; suggested actions focus on reviewed draft-plan routing.
- A profile-helper systematisation trial found type-review context actions
  could seed an undefined observed project value type and fail before the agent
  reached the pattern/staging route. Type advisories now omit missing type
  resources from `describe_context_slice` seeds while preserving them in
  `record_pattern` map implications and `stage_map_assertion_change` payloads.
- A follow-up value-type advisory trial found that same-evidence patterns could
  structurally target or imply an undefined observed `rc:ValueType` without a
  direct ontology route. Type advisories now add a `stage_pattern_promotion`
  value-type skeleton when that structural pattern support exists, keeping the
  map assertion route separate from the vocabulary-definition review.
- A metric-promotion skeleton trial found structurally supported patterns could
  lend broad or sibling-metric prose to an ontology `rdfs:comment`. Metric
  promotion skeletons now borrow pattern prose only when it names the metric IRI,
  local name, or normalized local-name phrase; otherwise they use the generic
  review-first comment.
- Storage-access setup trials confirmed `local_path` should stay invalid for
  `location_kind`: local filesystem belongs in `storage_protocol`, while
  `location_kind` is only the root shape (`object`, `directory`, `prefix`, or
  `connection`). Keep errors and docs explicit so agents choose exact file/object
  roots versus local folders deliberately.
- Query-planning partition-template trials found agents could miss likely runtime
  handoff columns when a partition-owned placeholder was not one of the declared
  partition columns. Draft binding requirements now keep matched partition
  columns as `candidate_column_match_status="not_applicable"`, but unmatched
  partition placeholders fall back to the same best-effort column-name hints used
  for dataset and storage templates.
- A profile/systematisation trial found automation had to enumerate
  `metric_advisories[]` and `type_advisories[]` manually even though top-level
  representative advisory index lists already existed. Advisory rows now carry
  row-local `metric_advisory_index` or `type_advisory_index`, matching
  recommendation rows' `recommendation_index` pattern.
- A staged-revision routing trial found same-slot replacement and
  already-effective stale conflicts still reported
  `decision="restage_against_current_graph"` while `next_action` correctly
  routed away from mechanical restage. Apply checks and batch restage items now
  expose `routing_decision` fields as the effective next route while preserving
  `decision` as the replay/status explanation.
- A stale-delta field trial found agents could misread `triples_to_add=0` on a
  conflicted stale row as no-op, even when the blocked patch still had effective
  payload if restaged. Apply checks now expose `effective_delta_summary`, which
  separates replayable deltas from blocked conflicted-patch deltas and flags
  truly already-effective stale sources.
- An AIS query-planning pressure test found the documented DailyIndex overlay
  was useful but not executable as a workflow check. The maintained
  `examples/ais-query-overlay-smoke.py` scratch example now loads the reduced
  AIS fixture, records reviewed index storage/layout metadata, follows the
  stale partition-link repair, and confirms the non-executed DuckDB handoff.
- A profile-promotion field trial found agents could complete metric
  vocabulary promotion, apply it, and still see `metric_vocabulary_review` as
  open because rerun `project_metric_defined` inspection actions created a fresh
  route key. Profile advisory route sources now carry `advisory_statuses`, and
  defined-metric inspection routes do not count as open review lanes.
- A profile/systematisation follow-up trial found grouped metric/type review
  lanes were mechanically correct but made agents cross-reference repeated
  action labels back to advisory rows. Grouped profile advisory actions now
  carry `source_profile_advisory`, naming the advisory kind, row-local index
  field, represented advisory indexes, duplicate groups, and duplicate
  profile-observation support.
- A database query-planning trial found
  `database_relation_template_source_mismatch` gave enough details for a human
  repair but no structured repair route. Mismatch issues now include
  `details.repair_hint` with a review-gated move: add the reviewed
  schema/table/relation to the storage access, then remove the misplaced
  dataset or partition template only if review confirms it was relation
  metadata rather than a real file/object path. A follow-up repair trial found
  the route works end-to-end but the action templates needed to say that
  `stage_map_assertion_change` still requires caller-supplied rationale; repair
  actions now declare that required extra argument.
- A response-shape docs audit found agents had to infer several nested payload
  fields from dataclasses or tests. `response-shapes` now spells out common
  nested rows for assertion hints and judgement panels, dataset storage and
  related-pattern handoffs, query-plan source/scan/runtime cards, staged
  patch/snapshot diagnostics, and validation diagnostics.
- A cold-start docs follow-up found those nested response-shape fields were
  present but hard to land on through bounded MCP section reads. The long
  `response-shapes` doc now has route subheadings for dataset storage, linked
  pattern reasons, query context, draft query plans, staged apply checks, and
  validation diagnostics.
- A query-planning capsule-staleness retest confirmed the active local MCP
  capsule can contain AIS/Polymarket tables but no storage access facts while
  fresh fixture imports have the expected storage metadata. Keep the
  `graph_overview.key_counts` sanity check in the query-planning path, not only
  in cold-start/runtime gotchas.
- Follow-up profile, revision, and query-context trials found three script-facing
  polish gaps. Profile-run docs now have addressable `mcp_tools` and
  `response_shapes` sections. Revision list payloads keep legacy `count` while
  also exposing explicit `returned_count` and `total_count` aliases for generic
  pagination scripts. Query analysis caveat warnings now preserve the original
  caveat severity in `details.caveat_severity_iri` and
  `details.caveat_severity_label`; route severe caveats as semantic review even
  when the query target is mechanically plan-ready.
- A grouped profile-advisory retest confirmed `source_profile_advisory` is
  sufficient for routing duplicate metric/type lanes. It also showed an
  authoring nuance: metric-vocabulary patterns that target the dataset can be
  pulled into profile map patches, so advisory-only metric patterns should
  target or imply the metric IRI instead.
- A staged-revision routing trial found same-slot replacement suggestions were
  routeable but could drop the source row's `alternative_to` provenance when a
  competing alternative target had already been applied. Repaired successors
  should preserve both `restages_revision` and the source alternative link so
  the semantic alternative gate remains visible.
- A staged-revision lineage trial found list rows intentionally expose
  validation status/counts but not full `validation_results`, and diagnostics
  use `messages[]` rather than a singular `message`. Agents needing exact SHACL
  rows should open detail/export instead of inferring fields from list rows.
- A profile advisory duplicate-shell trial found unmapped type advisories were
  technically routeable but could make agents restage the same duplicate column
  shell repeatedly. Routing notes now say that for duplicate groups, following
  the representative `stage_profile_map_updates` action is enough to stage the
  shared shell before rerun.
- A query-planning peer-action trial found selected ready candidates could carry
  `allow_context_blocked_candidate=True` while peer ready actions omitted it,
  causing agents to hit `query_context_has_other_blockers` again when following
  the peer action verbatim. Peer ready actions now include the allowance when
  sibling candidate metadata is the only broader blocker. The same trial found
  root-only database candidates with `database_relation_template_missing` needed
  a structured repair path; missing-template issues now include a reviewed
  storage-access `rc:pathTemplate` add action, and missing-storage repair hints
  name `storage_root` to match the API template.
- A query-routing retest confirmed those repair hints and peer actions are now
  executable from structured fields. The remaining naming nuance is that
  `ready_candidate_indexes` means candidate-local direct readiness, so it can be
  non-empty while top-level `readiness == "needs_review"` because sibling
  candidate metadata still blocks the whole context.
- A profile/systematisation trial confirmed duplicate unmapped column shells
  and advisory-only metric/type lanes now route well. The remaining mixed
  support risk is independent review of coupled metric/type ontology drafts from
  the same pattern; mixed-support notes now tell agents to review or export the
  generated drafts together before applying either lane independently.
- A staged-revision lineage trial found list/detail parity friction: list rows
  exposed `record_kind`, but `describe_graph_revision()` detail required agents
  to infer applied events from `revision_type_label` and `applied_source`.
  Graph-revision detail now exposes the same `record_kind` for direct routing.
- A revision snapshot handoff trial found RDF-only and snapshot-only imports
  were correctly diagnosed, but the repair action was nested under
  `snapshot_evidence` while top-level lineage/list routing still pointed at
  diff inspection. Snapshot-evidence import actions are now promoted into
  list/detail/lineage `suggested_next_actions`, and list/lineage `next_action`
  routes them through `complete_handoff_import`.
- A batch restage/export queue trial confirmed grouped Markdown queues are
  mostly followable across ready, stale, validation-failed, already-applied, and
  same-slot replacement rows. The main friction was that queues name row IRIs
  while the concrete follow-up target can differ for handled stale/applied rows.
  List, resource-revision, and grouped bundle summaries now add
  `next_action_queue_items` with row IRI, status, next tool, resolved target
  IRI, `resolved_target_record_kind`, and `row_is_target` while preserving the
  old queue map.
- A semantic-alternative gate trial confirmed ready restaged successors whose
  alternative target was already applied preserve
  `alternative_gate.status == "alternative_to_applied_source"` and
  `semantic_review_required=True`. Queue-only scanning remains intentionally
  coarse because `next_action_queue.apply_after_review` can include these gated
  successors, so summaries now expose
  `semantic_review_required_queue_counts` and queue-item alternative-gate fields
  beside the queue.
- Follow-up trials found the same queue-item companion useful in two adjacent
  places: `stage_systematisation()` now returns draft-level queue items so
  semantic gates are visible before exporting, and batch-restage items now
  expose `next_action_queue_item_after` scoped to `current_revision_iri` so
  item-local consumers do not have to join bundle queue items manually.
- A query-planning ready-index retest confirmed the current structured actions
  are sufficient when `readiness == "needs_review"` but
  `ready_candidate_indexes` is non-empty. The lasting lesson is naming: treat
  those indexes as candidate-local readiness, and follow
  `suggested_next_actions` when they provide `candidate_index` plus
  `allow_context_blocked_candidate=True`.
- A profile/advisory routing trial found grouped metric/type actions and
  `source_profile_advisory` remain mechanically sufficient for duplicate and
  mixed-support lanes. It also found a workflow nuance: after applying duplicate
  unmapped column shells, rerun profile-map drafting because the now-map-present
  column may produce ordinary recommendations before the draft becomes
  advisory-only.
- A resource-lineage routing trial confirmed resource-first list/detail helpers
  are sufficient across stale, applied, and current successor families and after
  RDF-only then snapshot JSON handoff imports. The remaining ergonomic friction
  is payload size: resource lists omit patch `content`, but rich per-row routing
  can still be large; use queue items first when only live work matters.
- A resource-list payload trial showed `include_patch_mentions=False` can hide
  unanchored patch-only live work, so it is not a safe way to shrink a
  resource-first mutation queue. `list_resource_revisions()` now has
  `current_staged_work_only=True` to mirror the graph-list live-work filter
  while preserving patch mention discovery before pagination.
- A query-storage helper trial confirmed suggested query-plan handoffs and
  database relation repair hints are scriptable, but
  `storage_protocol_location_mismatch` still needed issue-specific repair code.
  Those issues now carry `details.repair_hint.actions` for reviewed protocol,
  root, bucket, prefix, and exact path-template staged repairs.
- A staged conflict/rebase trial found current helpers route same-slot repair,
  mechanical restage, lineage inspection, and current-work queues well enough
  for a multi-step recovery. The remaining small routing gap was lineage
  row-vs-target clarity, so graph and resource lineage responses now expose a
  `next_action_queue_item` companion for their selected row.
- A profile metrics/map trial confirmed full-scan profile findings, sampled
  row-count guardrails, defined/undefined metric advisories, and mixed-support
  warnings are routing well. The durable review lesson is that staged revision
  `supporting_patterns` are direct support, while `impacts[].related_patterns`
  may include nearby metric/type advisory lore.
- Post-fix retests confirmed the recent storage, resource-list, lineage, and
  profile-support changes held up. Storage protocol/location repair hints were
  scriptable across non-S3 bucket/prefix metadata, root-scheme mismatch,
  path-template scheme mismatch, S3 bucket/prefix conflict, and repeated
  key-prefix cases; templated protocol/location actions now expose
  `placeholder_fields` and `reviewed_value_fields` so generic repair scripts
  know which argument needs the reviewed value. The resource current-work
  filter still depends on `include_patch_mentions=True`: a noisy resource
  family with applied events, handled stale ancestors, patch-only live work, a
  semantic-gated alternative, and a newer manual history row should return only
  the live patch-only rows with `current_staged_work_only=True`, while
  `include_patch_mentions=False` remains unsafe for unanchored patch-only
  mutation queues. Lineage `next_action_queue_item` resolved the row-vs-target
  ambiguity after a staged alternative lost the race to an applied branch. A
  follow-up restage/apply lineage trial found graph lineage still made agents
  infer the actually applied staged successor from `restage_chain_iris[-1]`;
  `describe_revision_lineage.applied_source_revision_iri` now names it
  directly and suggested actions include `describe_staged_revision` for that
  row when it differs from the selected stale source. The
  next larger staged-revision gap is a read-first
  `draft_staged_revision_rebase(...)` helper for validation-failed or stale
  overlapping alternatives, not another list/join tweak. Profile support versus
  impact routing still looks right: `supporting_patterns` stays direct, while
  `impacts[].related_patterns` carries broader metric/type review context.
- A follow-up staged-rebase design pass reproduced the validation-failed
  alternative case and found the smallest useful helper is read-only:
  `draft_staged_revision_rebase()` now composes live apply-check routing,
  compact lineage, and reviewed repair actions without staging anything. Its
  first concrete repair draft covers recognizable singleton-slot replacements,
  including the `rc:rowSemantics` max-count case where a mechanically restaged
  alternative should replace the now-current value instead of replaying the same
  additive patch again. Keep future expansion focused on additional safe,
  reviewable repair candidates rather than making restage silently semantic.
- An adversarial retest of that helper found it was too willing to draft
  replacement actions for ambiguous or invalid row-semantics payloads. The
  helper now requires exactly one current same-subject/predicate value before
  drafting a same-slot repair, limits `rowSemantics`, `physicalType`, and
  `schemaStability` repairs to IRI objects, preserves the typed-boolean
  `nullable` path, and treats blank-node/free-text row-semantics cases as
  manual validation repair work. If the selected source already failed
  staged-time validation and no safe repair candidate is recognized,
  `draft_staged_revision_rebase()` now reports `validation_repair_needed`
  instead of presenting mechanical restage as the main route.
- A query workflow gap trial found profile workflows had top-level action
  lanes while query metadata repairs were complete but nested under
  `issues[].details.repair_hint.actions[]`. `describe_query_context()` now
  exposes `suggested_repair_action_groups`, a read-only
  `query_repair_review` lane that lifts existing repair hints with issue
  index/code/resource, copied repair context, and ordered action templates. This
  is intentionally separate from flat `suggested_next_actions`: repair rows may
  contain placeholders and required rationale, so automation should use the lane
  for discovery and still review/fill the template before mutating the graph.
- A follow-up missing-storage repair loop showed the optional
  `record_map_storage_access.path_templates` placeholder can nudge agents to
  duplicate a dataset-owned file/object template onto the new storage access,
  producing equivalent ready candidates. The repair hint now carries a condition
  beside that optional field: omit it when the dataset or partition already owns
  the reviewed file/object path template, while still recording database
  relation identifiers as storage-access-owned templates.
- A systematisation/pattern-promotion trial showed shared ontology and shape
  patches are sometimes semantically too strong for fallback alternatives:
  pattern-first fallbacks still carried provisional map vocabulary and preview
  shapes because `shared_additions` intentionally applies to every staged
  framing. Multi-framing drafts with shared `ontology` or `shapes` patches now
  expose `shared_semantic_context_applies_to_all_framings` in
  `structured_warnings`, with suggested rerun arguments naming the shared graph
  roles to move into per-framing patches when fallback framings should avoid
  that context.
- A staged rebase/versioning trial showed batch dry-runs can still classify a
  validation-failed stale source as `would_restage` even when the effective
  next route is repair-first. This remains intentionally permissive because
  later graph state can sometimes fill a source validation gap, but batch items
  now expose `repair_first_warning` when the source failed staged-time
  validation and `routing_decision_after="repair_or_replace"`. A follow-up
  trial showed prose was not enough for scripts that use
  `would_restage_revision_iris` as a worklist, so repair-first dry-run sources
  are now withheld from that safe mechanical-restage list and reported in
  `repair_first_revision_iris`. Treat that warning/lane as stronger than
  `would_restage`: inspect validation diagnostics or call
  `draft_staged_revision_rebase()` before creating another same-payload
  successor. A later rebase probe confirmed real batch restage still operates
  on the caller's supplied IRIs, so run dry-run first and pass only
  `would_restage_revision_iris` when you want a purely mechanical batch.
- A profile/query integration trial showed a draft with scalar conflicts and a
  default-stageable unmapped column could still put the profile map-update
  action first while query context had a hard `missing_storage_access` blocker.
  Profile drafts now add a leading `query_context_review` lane when the dataset
  already has physical-query intent recorded, such as a path template or
  layout, but `describe_query_context` reports blocking physical metadata
  issues. Treat that lane as a priority cue before using profile-derived map
  updates for query-planning work; it does not discard the profile
  recommendations. A logical/profile-only retest confirmed the inverse:
  insufficient physical query metadata alone should not add that lane unless the
  map already records physical-query intent.
- Follow-up trials found no product-code fix in three harder workflow slices,
  but left useful regression targets. Mixed local, S3, and database query
  candidates proved that automatic selection can choose a direct-clean local
  route while sibling metadata still keeps the global context review-gated; use
  the explicit `candidate_selector` and `allow_context_blocked_candidate` actions
  instead of treating automatic selection as execution-ready. Staged-revision
  handoff retests confirmed TriG-only imports should route exact diffs to
  `import_revision_snapshots` before snapshot JSON import restores exact
  triples. Profile metric/type retests confirmed mixed-support patterns belong
  in both advisory lanes while `stage_profile_map_updates` keeps metric and
  type vocabulary IRIs out of `map`. A cold-start docs trial showed the compact
  profiling and query-planning docs should spell out bundled column-profile
  `physical_type` / `value_type` fields and link missing-storage repair back to
  the executable-catalog recipe.
- A mini-project/product-gap wave found the main profile friction was after
  staging unmapped column shells: the review note told agents to rerun
  `draft_profile_map_updates`, but the response lacked a structured action.
  `stage_profile_map_updates()` now appends that rerun action after the staged
  revision apply-check action when a staged item is an
  `unmapped_profiled_column`. The same wave found two doc-only issues:
  systematisation docs pointed at a non-addressable response-shapes section,
  and query-planning docs implied `row_count_snapshot_basis` was top-level
  instead of under `profile_summary.profile_run_candidates[]`.
- A four-trial routing wave found two places where the right next move existed
  but was too easy for automation to skip. Query contexts now add extra
  `describe_profile_run` actions before drafting a plan when profile-run row
  counts disagree, or when the snapshot-matching run is sampled, unknown, or
  mixed basis. Systematisation drafts with an invalid first alternative anchor
  now surface a complete `stage_systematisation(..., link_alternatives=False)`
  rerun action before export/check actions. The same wave confirmed revision
  count aliases and caveat severity details are clear, and added docs crib notes
  for lineage/list/apply field names such as `applied_revision_iri`,
  `application_decision`, and `next_action_queue_items[].resolved_target_iri`.
- A retest wave after those routing changes confirmed the profile-run and
  systematisation actions are executable in practice. `describe_profile_run`
  now carries run-level row-count snapshot and basis fields so the sampled,
  unknown, or mixed warning survives the handoff from query context to the
  profile-run inspection step. Grouped staged-revision Markdown now includes a
  `Resolved Targets` table mirroring `bundle_summary.next_action_queue_items`,
  which gives Markdown-only reviewers the same row-vs-target routing cue that
  JSON automation already had. The same wave confirmed query repair action
  groups work end-to-end from missing storage to ready database relation
  metadata; broader direct-repair rationale and protocol-aware database path
  guidance remain later design follow-ups rather than this checkpoint.
- A follow-up routing wave found three small autonomy hazards rather than a
  broad workflow break. Profile map-update rerun actions now carry
  `preconditions.staged_revision_applied` so agents do not rerun before the
  staged unmapped-column shell is durable. Missing-storage repair templates now
  spell out database-storage relation-template follow-up and direct-write
  rationale guidance. `draft_staged_revision_rebase()` no longer points
  no-repair drafts back at itself; validation-failed stale work should follow
  the remaining inspection/export route or manual repair path, with
  `apply_check.routing_decision`, `draft_kind`, `next_action.queue`, and batch
  `repair_first_revision_iris` overriding broad restage wording.
- A retest-heavy follow-up confirmed those fixes and found two smaller routing
  refinements. Metric advisory context actions now seed the specific
  `observed_metric_iri` rather than the broad project metric kind, so a
  same-metric multi-dataset project does not pull unrelated profile runs into
  the first handoff. Database relation mismatch repair hints now put
  `remove_misplaced_source_template` first and mark the add action
  `already_satisfied` when the storage access already has the reviewed relation
  template. Same-slot rebase drafts also filter out inherited
  `draft_staged_revision_rebase` suggestions when a concrete repair action is
  already available.
- A later retest wave found the product behavior held up in direct trials: the
  observed-metric handoff stays dataset-local while the broad metric-kind slice
  still finds same-metric peers, direct database-relation repair reaches
  `ready_for_query_planning` after the ordered removal, and applied metric
  promotions rerun as `project_metric_defined` without duplicate vocabulary
  suggestions. The remaining hazard was documentation and automation clarity,
  not graph behavior. Agent docs now name grouped
  `source_profile_advisory.observed_metric_iris`, spell out the
  already-on-storage repair exception, and point successful metric-promotion
  follow-up at `deep_lore` when agents need to rediscover the support trail.
  The already-satisfied relation-template add action also carries
  `skip_when_already_satisfied=true` for scripts that should follow the ordered
  remove action without parsing prose.
- A storage-metadata trial found one real query-planning bug in mixed physical
  routes: a non-database storage access with `location_kind="object"` can name
  the exact dataset object even when older dataset or partition templates still
  exist as review context. `describe_query_context()` now keeps the exact
  `storage_access_location` candidate visible for that route and marks
  candidates that append templates to the object root as review-only with
  `storage_object_location_has_path_template`. Use the explicit
  `candidate_index` plus `allow_context_blocked_candidate=True` action when the
  exact object candidate is direct-clean but sibling template metadata keeps the
  whole context in review.
- A broader expedition wave confirmed that autonomous loops will not reliably
  reach every project area by time alone; they need seeded trials outside the
  current high-friction surface. The first fix from that wave was
  `project_brief()`, a read-only orientation helper over dataset query
  readiness, profile draft lanes, staged review queues, and recommended next
  tasks. A follow-up field trial found two steering hazards: singleton profile
  evidence could draft useful map updates without appearing as a profile-run
  candidate, and low limits could let one queue type crowd out staged or
  profile work. `project_brief()` now drafts from singleton/shared profile
  evidence, reports profile and task queue counts across scanned datasets,
  keeps returned readiness counts separate from project-wide readiness counts,
  and reserves recommended task slots by queue type when the limit allows.
  The same expedition ranked query execution/result capture, ontology/SHACL
  evolution outside profile metrics, generic RDF slicing, non-tabular assets,
  and large-slice pressure as areas that should be deliberately trialed rather
  than expected to emerge from staged-revision polish.
- A seeded ontology/SHACL trial confirmed that systematisation helpers can
  carry project ontology and shape patches, including an intentionally invalid
  diagnostic framing, but agents need the shared-context warning in hand before
  drafting. Put provisional ontology and shape patches in per-framing additions
  when a fallback should remain pattern-first or map-only, and use
  `link_alternatives=False` when the first framing is diagnostic rather than
  the preferred comparison anchor.
- A non-tabular asset trial showed that `record_map_dataset(is_table=False)`
  plus project `extra_types`, caveats, evidence, observations, and patterns is
  enough to model API or document-like assets without table columns. Start
  retrieval from `describe_resource()` or `describe_context_slice()` unless the
  trial is explicitly about table/storage query execution.
- A bounded-retrieval trial showed that broad deep-lore slices can still find
  the right lore while suggesting unhelpful broad filler patterns first.
  Truncated pattern-narrowing suggestions now rank linked patterns by structured
  relevance tiers from dataset context. Agents should still seed a search-found
  pattern directly with `profile="pattern_brief"` when lexical search has
  already identified the synthesis they need.
- A semantic rebase trial confirmed that staged-revision recovery mechanics
  work across map and ontology drift, including batch dry-run, real restage,
  grouped export, apply-one-and-recheck, same-slot rebase drafting, and reviewed
  repair via `stage_map_assertion_change(restages_revision=...)`. The useful
  follow-up was mostly doc steering: read item-local post-batch actions, apply
  at most one ready successor, and recheck siblings because a single apply can
  stale or no-op the rest of a bundle.
- A generic RDF retrieval trial confirmed that `list_entities`, `search`,
  `describe_resource(include_incoming=True)`, validation, and graph exports can
  recover arbitrary ontology, evidence, source-span, and shape resources, but
  `describe_context_slice` is still profile-based rather than a generic RDF
  neighborhood browser. SHACL blank-node property shapes and arbitrary
  ontology/domain-range neighborhoods still need manual stitching or export
  until a future generic slice helper exists.
- A non-tabular project-brief trial confirmed that API/document-like assets are
  modelable with `record_map_dataset(is_table=False)`, project `extra_types`,
  caveats, evidence, claims, and patterns. It also showed that `project_brief`
  should not steer those assets into query repair: non-table datasets now carry
  `is_table=false`, `not_applicable_non_tabular_asset` query readiness, and a
  `non_tabular_asset_review` task pointing at a context-slice handoff.
- Two generic-RDF API-shape probes found that a full route-explained generic
  slice helper is still the likely long-term answer, but the immediate
  high-value fix was smaller: `describe_resource` now reports outgoing and
  incoming total/returned/omitted counts with offsets, and can optionally return
  bounded blank-node closure triples for SHACL/property-shape handoffs. Use that
  local card before reaching for graph export; keep the future generic slice for
  durable multi-resource handoffs that need routes and cross-graph context.
- A retest showed that counted `describe_resource` is enough for single-resource
  handoffs, but mixed arbitrary resources still need route explanation across
  graph roles. `describe_context_slice(profile="resource_brief")` now gives a
  bounded seed-centered handoff for ontology terms, SHACL shapes, evidence,
  source spans, non-dataset map resources, incoming references, blank-node
  owners, and predicate usage without becoming a recursive graph crawler.
- Resource-brief retests found that lexical search may land on a SHACL
  blank-node property shape rather than the named node shape an agent should
  inspect. `resource_brief` now climbs from blank-node seeds to named URI owners,
  including nested blank-node shape fragments, but route-cap ordering and common
  predicate seeds still need separate trials before changing behavior.
- A profile/query frontier trial found that `project_brief` routed non-tabular
  assets correctly, but direct `describe_query_context` and `draft_query_plan`
  could still draft a review-gated file handoff for an `is_table=false`
  document asset with storage metadata. Direct query helpers now return
  `not_applicable_non_tabular_asset` for non-table map datasets, and
  `draft_profile_map_updates` leaves their profile row counts as evidence
  instead of proposing table `rc:rowCountSnapshot` map updates.
- An AIS query-handoff trial showed the corrected wildcard DailyIndex route was
  reachable only by explicit candidate selection: automatic planning preferred
  a partition template with `{year}`/`{date}` bindings over a verified
  storage-access-owned wildcard. Query target selection now ranks otherwise
  ready candidates by fewer template bindings and route-specific storage access
  before falling back to returned order.
- A local query-result capture trial showed the plan-to-result loop works with
  a tiny `/tmp` CSV: `draft_query_plan` can reach
  `execution_attempt_ready`, an external local aggregate can be recorded with
  `record_query_result`, and a deliberate missing-path failure can be preserved
  as ordinary observation evidence. DuckDB was not installed in that trial, so a
  Python CSV fallback was acceptable because the recorded `engine`,
  `sample_method`, query artifact, result artifact, and failure log made the
  actual runtime clear. The main product signal was docs/onboarding, not a new
  query engine: DoxaBase plans and records; it still does not execute queries
  itself. A follow-up query-result semantics trial found one recurring trap:
  passing profile-shaped fields such as `sample_size` or `row_count` for a
  filtered or grouped aggregate makes the result look like profile evidence and
  can surface profile-review work. Keep arbitrary aggregate counts in
  `result_sources` unless the value is genuinely population-profile evidence.
  A later query-result handoff trial found that singleton profile evidence from
  `record_query_result` was visible in `profile_summary.evidence_iris` but did
  not produce a `profile_run_candidates[]` row or suggested profile action.
  `describe_query_context` now inserts a bounded singleton
  `describe_profile_run` action before `draft_query_plan`; its
  `source_profile_evidence` preview carries the evidence summary, short profile
  summary, result sources, query-source paths, and parsed execution
  status/engine/query hash when the standard evidence summary is present.
- An ontology/SHACL frontier trial for late-arriving snapshot corrections
  confirmed that pattern-only, map-only, and complete ontology+shape framings
  can be staged side by side, while an intentionally incomplete shape-backed
  sibling routes to `repair_or_replace` with a precise SHACL min-count
  diagnostic. The key limitation is retrieval, not staging: proposed shapes
  inside staged patch Turtle are not ordinary graph resources until applied, so
  `resource_brief` and `describe_resource(include_blank_node_closure=True)`
  cannot inspect their blank-node property constraints. Use
  `describe_staged_revision` or grouped staged exports for proposed shape
  review, and pause before adding preview-resource inspection APIs.
- A profile route-identity trial found that duplicate groups and advisory
  grouping worked, but agents had to reverse-join grouped actions back to draft
  rows and profile insight bundles back to draft lanes. Grouped profile action
  source blocks now carry stable `route_group_key` and `route_step_key` fields;
  profile map-update actions expose `source_profile_map_update`; metric/type
  actions keep `source_profile_advisory` with route keys; and profile insight
  bundle candidates plus Markdown expose a `Profile Route Bridge` so reviewers
  can see which draft route produced or motivated each staged row. A later
  review-artifact trial showed that broad support overlaps could make related
  lanes look implemented; profile route groups now include `match_strength`
  (`direct_action`, `strong_support`, or `related_support`) and Markdown renders
  the strength beside each lane.
- A post-apply route trial found `export_profile_insight_review_bundle()` could
  rediscover already-applied profile-map and query-repair staged sources, but
  their original direct route lane disappeared once the live draft no longer
  emitted that action. New `stage_profile_map_updates` revisions persist their
  profile route source in history, and profile exports merge stored sources with
  live draft sources. Generated query-planning repair review notes such as
  `missing_storage_access query planning guidance` also synthesize a
  `query_context_review` direct-action route when the repair has already been
  applied.
- A profile follow-up route trial found the merge could then over-correct:
  after applying an unmapped-column profile update, a fresh live nullable update
  on the same column was labelled `profile_map_updates (direct_action)` for the
  applied source. Profile route merging now tracks candidate-local source
  provenance, so stored/generated sources can remain direct for applied rows
  while fresh same-lane live follow-ups are support until staged separately.
- A Profile Route Bridge usability trial found Markdown-only reviewers could see
  lane keys and revision IRIs, but still had to reverse-map them to the grouped
  bundle rows. The bridge now carries the same row number and candidate summary
  used by the later review matrix and revision sections; use that row number
  when moving from a route lane to detailed patch review.
- A follow-up project-brief pass found a remaining bridge gap for
  `query_context_review`: the draft action had route keys, but no route anchor,
  so a staged dataset-anchored storage/query repair could enter a profile
  insight bundle without connecting back to the query-context lane.
  `source_query_context.route_anchor_iris` now names the dataset, and the
  Profile Route Bridge can show the query-context route for those repairs.
- A query-planning project-brief trial found a first-hop routing mismatch:
  `query_repair_review` tasks could point at `draft_query_plan`, sending agents
  toward another review-gated plan before they inspected the lifted repair
  templates. Project brief repair tasks now point to `describe_query_context`
  so the repair lane is explicit before plan drafting.
- A staged-recovery trial found that mixed recovery plans exposed same-slot
  repair lanes correctly in `lanes[]` and queue items, but top-level
  `repair_first_revision_iris` could be empty for `repair_or_replace` routes.
  `plan_staged_revision_recovery()` now also returns
  `repair_or_replace_source_revision_iris` as the broad source-row worklist for
  repair/replacement lanes.
- A privacy/export trial confirmed staged Markdown and profile insight exports
  detect sensitive-looking patch literals and keep warning text redacted, but
  warning examples used pre-insertion line numbers. Markdown privacy warning
  examples now report final artifact line numbers, after the inserted warning
  block, so reviewers can jump directly to the preserved patch literal.
- An import/export handoff trial found that an all-with-seeds TriG bundle could
  partially populate mutable project graphs before a later protected seed graph
  raised `ImmutableGraphError`. `import_trig()` now preflights every non-empty
  named graph before clearing, creating, or inserting graph storage, so failed
  normal imports for immutable seeds or unknown Rich Canopy roles leave target
  graph counts unchanged.
- A claim-reconsideration retrieval trial showed that direct claim resource
  cards exposed lifecycle links but nested reconsideration evidence appeared
  empty when the caller scoped `describe_resource()` to `observations`.
  Reconsideration descriptions now hydrate their evidence details from the
  `evidence` graph too, so the direct claim card shows the source strings and
  source spans behind the reconsideration.
- A high-degree `resource_brief` trial showed route-cap warnings could be
  mistaken for raw triple truncation. `resource_brief` now says explicitly that
  raising `max_triples` does not recover route-capped resources, adds recovery
  actions for paged direct references and blank-node closure, and points
  predicate-usage caps at graph export/narrowing until a paged predicate browser
  exists. Pattern seeds also warn when `resource_brief` should be replaced by
  `pattern_brief` or `deep_lore` for support/evidence routes.
- A query-planning frontier trial found `project_brief` could keep routing a
  dataset to `query_repair_review` even after the reviewed cleanup had already
  been staged for the same dataset. Staged review rows now expose
  `revision_anchor_iris`; query repair tasks with matching pending staged work
  include `pending_staged_repair_iris` and are sorted behind `staged_review` so
  agents review the pending mutation before staging a duplicate repair.
- A profile frontier trial found repeated profile observations could produce two
  default-stageable `unmapped_profiled_column` shell rows for the same helper
  mutation when sample/null details differed. Profile map-update duplicate keys
  now group unmapped shells by their helper mutation, while preserving all
  supporting profile observations on the accepted representative.
- A staged-recovery frontier trial found grouped queues still made agents work
  backward from row IRIs to current mutation targets, especially when handled
  stale rows pointed at refreshed successors or applied events. Grouped exports
  and recovery plans now expose `mutation_frontier_iris` for deduped resolved
  apply/restage/repair targets plus `requires_recheck_after_each_apply` as the
  boolean apply-one-then-recheck hazard.
- A query/storage frontier trial confirmed non-table assets, database relation
  handoffs, missing-storage repair candidates, and pending staged query repairs
  route correctly through MCP wrappers. The durable lesson is operational:
  `candidate_existing_storage_accesses` are review candidates, not permission to
  auto-link the first storage access, and `pending_staged_repair_iris` should
  stop agents from staging duplicate query repairs.
- A project-brief frontier trial found that profile-review tasks could still
  recommend duplicate `stage_profile_map_updates` while current staged profile
  work for the same dataset/evidence was waiting. `project_brief` now emits a
  `staged_frontier_review` task pointing to `plan_staged_revision_recovery` when
  current staged work exists, and profile tasks with matching pending staged
  profile updates fall back to read-only `draft_profile_map_updates`.
- A review/export/privacy trial confirmed grouped Markdown and RDF exports are
  faithful artifacts: privacy warnings redact warning text and point at final
  artifact line numbers, but patch literals remain unredacted in Markdown,
  history exports, and default project TriG. Use workflow/no-history exports
  when staged patch payloads are not needed, and follow `resolved_target_iri` or
  `mutation_frontier_iris` instead of row IRIs when automating from exports.
- A path-hygiene/privacy trial showed non-secret local paths, object-store URIs,
  endpoint URLs, and relative paths do not trigger `scan_sensitive_literals`,
  export `privacy_warnings`, `fail_on_sensitive`, or `project_brief` privacy
  health tasks. Treat path and endpoint shareability as a separate review from
  credential-like sensitive-literal scanning.
- A query-repair chain trial showed `project_brief` is clear once queue names
  are read strictly: `query_repair_review` means
  `describe_query_context.suggested_repair_action_groups` contains reviewed
  metadata repair templates, while `query_context_review` can mean the dataset
  has layout, verification, runtime, or binding blockers but no repair template.
- A human-review artifact chain trial showed grouped Markdown and project TriG
  handoffs were self-contained enough for fresh review, but the grouped decision
  matrix labelled only the linked alternative row as choose-one. The matrix now
  labels every row in an included alternative pair or group as a choose-one
  candidate so source rows are not overread as independently ready to apply.
- A privacy/export follow-up found `project_brief` could treat arbitrary
  same-dataset/same-evidence staged work as a pending profile-map update.
  Pending profile gating now requires the staged revision generated by
  `stage_profile_map_updates`; unrelated same-evidence staged work remains in
  the staged frontier without suppressing the profile review lane.
- A staged-recovery follow-up confirmed recovery planning, dry-run restage,
  lineage, and applied-diff surfaces behave coherently, but mixed frontiers need
  a strict script recipe: plan, dry-run restage only mechanical rows, apply at
  most one ready row, then replan before the next mutation.
- A profile/systematisation trial confirmed scalar conflict recommendations
  fail closed when over-staged, while metric vocabulary and type-advisory lanes
  remain separate from profile map patches. For complementary caveat plus
  vocabulary framings, set `link_alternatives=False` instead of accepting the
  default alternative-linking behavior.
- A profile-frontier review trial found grouped Markdown identified competing
  alternatives symmetrically, but queue-only automation saw only the child row's
  row-local `alternative_to` gate. Queue items now add `alternative_set_iris`,
  `alternative_set_source_iri`, and `alternative_set_role` for every returned
  member of an unresolved alternative set.
- A profile fixture/frontier trial reproduced that bundled AIS/Polymarket
  fixtures have zero profile queues after `load_example_fixtures(replace=True)`.
  Use `examples/profile-frontier-workflow.py` when a scratch run needs
  deterministic profile-derived map-update recommendations, staging, and
  recovery planning without changing fixture RDF.
- A query/storage ranking follow-up found complete-but-unrelated storage access
  candidates could outrank a nearby dataset-specific access. Missing-storage
  candidate ranking now splits weak generic tokens such as `data`, `parquet`,
  `snapshot`, and `trial` from project-specific token matches, and always
  surfaces `linked_to_other_dataset` with `linked_dataset_iris`, while still
  requiring reviewed selection.
- A revision-snapshot handoff trial confirmed project TriG alone correctly
  routes imported rows through `complete_handoff_import` until companion
  snapshot JSON is imported. Grouped review export JSON now exposes
  `bundle_summary.snapshot_evidence` so unattended consumers can see the same
  snapshot import gate as the Markdown `Snapshot Evidence` panel without parsing
  Markdown or changing review/apply queue semantics.
- A review/export handoff follow-up found agents could still follow the top
  staged-recovery route into `apply_after_review` without noticing RDF-only
  snapshot evidence. Recovery plans and grouped review bundle warnings now repeat
  the snapshot-import preflight before mutation queues while keeping
  `next_action_queue` as the post-preflight route.
- An assertion-support/caveat trial confirmed that support routes correctly pull
  direct and owner-dataset caveats plus mixed supporting and contradictory lore,
  but related claims/patterns are contextual, not endorsement. Read claim text,
  reconsiderations, caveat scopes, and route explanations before staging or
  applying assertion changes. The same trial found `record_map_caveat` should
  fail closed on severity: use only `rc:Minor`, `rc:Moderate`, or `rc:Severe`.
- A revision snapshot lineage handoff trial confirmed project TriG plus full
  revision snapshot JSON preserves exact applied diffs, staged/applied pairing,
  resource lineage, and restage-chain lineage. Exporting snapshots with only an
  applied event includes that event and its direct staged source, which is enough
  for exact applied diff reconstruction; use a full snapshot export or explicit
  older restage-chain ancestor IRIs when exact full-chain recovery matters.
- A query-repair direct-storage trial confirmed `record_map_storage_access`
  clears `missing_storage_access` and produces a review-gated plan when storage
  is still only candidate-verified. It also showed that group-level
  `pending_required_extra_arguments` was too ambiguous for choose-one repair
  groups, so query repair groups now expose `choice_mode` and
  `pending_action_options` for per-action routing while preserving the legacy
  union field.
- A later Polymarket query-repair trial found missing-storage repairs still
  required direct map writes when no existing storage candidate could be linked.
  `missing_storage_access` now exposes a staged
  `stage_query_storage_access_repair` option for reviewed new storage access
  metadata, while keeping `record_map_storage_access` as an intentional direct
  write fallback and `stage_existing_storage_access_link` for existing access
  resources.
- A staged storage-link trial showed `project_brief` correctly routes pending
  query repairs behind staged frontier review, but raw `describe_query_context`
  could still hand out a duplicate staged-link template for the same
  dataset/storage pair. Missing-storage candidates now expose
  `pending_staged_repair_iris`, and the staged existing-link action is marked
  `already_pending` when every visible reviewed candidate already has a current
  staged link.
- A follow-up active query-repair trial showed the multiple-candidate case needs
  a softer signal: the group-level existing-link action should remain pending
  while non-pending alternatives exist, but scripts need to see which candidates
  already have staged links. Missing-storage repair hints now expose
  `already_pending_candidate_count`, `already_pending_storage_access_iris`, and
  `pending_staged_repair_iris` on the repair context and compact
  stage-existing-link option.
- A review/export handoff trial confirmed grouped staged Markdown and profile
  insight bridges are self-contained for decision matrices and resolved targets,
  but Markdown-only handoffs should not be expected to carry every query-context
  candidate summary. When pending query repairs matter, include
  `describe_query_context` output or default project TriG plus revision snapshot
  JSON with the Markdown bundle.
- A review-artifact frontier trial found grouped staged Markdown gave strong
  warnings when snapshot evidence was incomplete, but gave no positive
  confirmation when all included rows had exact snapshot rows. Grouped Markdown
  now emits a compact `Snapshot Evidence` confirmation for complete bundles
  while keeping the detailed import-action table for incomplete handoffs.
- A context-slice frontier trial showed `resource_brief` high-degree incoming
  references can hide business-critical columns behind generic references when
  capped. Incoming-reference caps now rank resources with direct claims,
  caveats, patterns, profile observations, staged revisions, or dataset/column
  roles ahead of plain generic references, while still pointing exhaustive
  review to paged `describe_resource`.
- A profile/query-blocker handoff trial confirmed the intended route:
  `missing_storage_access` keeps DailyIndex profile review on query-context
  repair first; after storage repair, profile tasks point to
  `draft_profile_map_updates`; after staging profile work, `project_brief`
  points first to staged frontier recovery and avoids duplicate same
  dataset/evidence staging.
- Stale-seed compatibility trials confirmed copied older capsules can have
  non-empty immutable seed graphs that predate current staging vocabulary.
  `seed_base_graphs()` does not refresh those graphs. Staging now reports a
  clear stale-`base_ontology` recovery message when required patch-role or
  default revision-stance terms are missing: export mutable project graphs,
  create a fresh seeded capsule, and import the project bundle there. A broader
  read-only seed freshness/status helper remains a future hardening task.
- A profile metric-promotion rerun trial found `draft_profile_map_updates` could
  propose a duplicate `stage_pattern_promotion` skeleton after the first
  metric-vocabulary skeleton was staged but not applied. Metric advisories now
  detect matching current staged skeletons by metric anchor, same evidence, and
  supporting promotion pattern, expose `pending_staged_promotion_iris`, and route
  to inspect/export pending staged work instead of creating another duplicate.
- A staged version-browser trial found grouped Markdown decision matrices could
  label already-effective stale rows as "Restage or replace" even though the
  structured route was informational `inspect_no_effective_change`. Grouped
  exports now use the compact next-action label "Inspect already-effective stale
  source" for those rows.
- A project-brief frontier trial found
  `_project_brief_pending_staged_repair_iris()` treated any non-informational
  staged row anchored to a dataset as a pending query repair. Unrelated staged
  caveats and staged profile updates could therefore lower reachable
  `missing_storage_access` repair tasks behind staged review. Pending query
  repairs are now filtered to staged rows that change query-planning metadata
  such as storage links, path templates, storage fields, layout fields, or
  partition metadata.
- A follow-up project-brief frontier trial found location-blocked query contexts
  with no lifted repair group could still expose a review-gated
  `draft_query_plan` action as the first top-level `query_context_review` task.
  `project_brief` now routes those blocked task rows through
  `describe_query_context`; the dataset query summary can still keep the draft
  action for agents that need plan-specific scan and runtime fields after the
  context review.
- A privacy/export frontier trial found `export_revision_snapshots()` preserved
  raw SQLite-side snapshot quads but did not surface the privacy warning/blocking
  affordances available on RDF exports. Snapshot JSON exports now report
  `sensitive_literal_count` and redacted `privacy_warnings`, and
  `fail_on_sensitive=True` blocks before creating or overwriting the artifact.
  A follow-up export-handoff loop added `export_handoff_bundle()` so project
  TriG plus revision snapshot JSON can be written with combined path and privacy
  preflight before either file is created. The retest found cold receivers still
  needed a durable pairing artifact, so `manifest_path` can now persist
  artifact paths and the expected `import_trig` / `import_revision_snapshots`
  sequence.
- A later privacy/export trial found the redacted scanner only checked literal
  or URI objects, so a credential-like identifier embedded in an RDF subject IRI
  could pass `scan_sensitive_literals`, `export_revision_snapshots`, and
  `export_handoff_bundle(fail_on_sensitive=True)`. The scan now covers subject
  URI terms as well as object URI/literal terms, and match payloads include
  `term_position` / `term_kind` so agents can review whether the hit came from
  an identifier or an object value.
- A predicate-only privacy/export trial found the same leak shape for
  credential-like RDF predicate IRIs: graph scans, revision snapshot JSON, and
  handoff exports could pass when the sentinel appeared only in the predicate.
  Sensitive-term scans now include predicate URI terms in live graph roles and
  stored snapshot quads, so `fail_on_sensitive=True` blocks before writing those
  faithful artifacts.
- A query/storage frontier trial found database-backed routes could have storage
  and relation metadata modeled correctly but no structured repair lane for
  `missing_physical_layout`. Once storage is linked, that issue now exposes a
  reviewed `record_or_stage_physical_layout` repair group with a staged
  `stage_query_physical_layout_repair` option, a direct
  `record_map_physical_layout` fallback, and database table-layout guidance such
  as `rc:PostgreSQLTable`, `rc:SQLiteTable`, or `rc:MySQLTable`.
- A staged-recovery frontier trial found `plan_staged_revision_recovery()`
  exposed `would_restage_revision_iris` correctly but top-level suggestions still
  nudged agents toward individual restage calls. Plans with restageable stale rows
  now start `suggested_next_actions` with a batch
  `restage_staged_revisions(..., dry_run=True)` action over that worklist.
- A staged version-frontier trial found explicit recovery handoffs can include a
  stale source and the source's current successor, inflating per-source lane and
  queue counts even though there is one current target. Recovery plans now expose
  `resolved_target_groups[]` and `resolved_target_group_counts`: keep `lanes[]`
  for source provenance, but use resolved-target groups for the deduped
  target-family worklist before mutation decisions.
- A grouped review-sequence frontier trial found mixed staged bundles had enough
  queue and resolved-target data, but no single ordered cross-lane worklist.
  Grouped exports now include `bundle_summary.review_sequence` and Markdown
  `Review Sequence`, ordering queued rows through inspect-redirect, repair,
  restage, review/apply, and recheck phases before the lower-level queue buckets.
- A profile post-apply handoff trial found implicit profile insight exports
  recovered current related staged work but missed the already-applied
  profile-map source row unless callers passed `revision_iris` explicitly.
  Profile insight review exports now scan already-applied staged sources by the
  same profile evidence/observation/pattern/anchor routes, with an opt-out flag
  for current-staged-only bundles.
- Staged grouped apply/recheck trials confirmed `Review Sequence` gives a clear
  apply-one-then-recheck route, but `apply_staged_revision()` could still be
  misread as returning the whole remaining queue. Apply responses now mark
  `post_apply_recheck_is_partial_queue=true` and start their top-level
  suggestions with `plan_staged_revision_recovery(current_staged_work_only=True)`
  so independent staged siblings remain visible.
- A mixed recovery routing trial found applied event IRIs failed safely in
  recovery planning and batch restage dry-runs, but with a generic no-patch
  message. `describe_staged_revision()` now identifies applied events and points
  callers to inspect the event or retry with its staged source IRI, matching
  grouped export guidance.
- A query/storage context-slice trial found dataset briefs routed seed tables to
  `describe_query_context` only when `dataset_contexts[].operational_warnings`
  already carried a physical metadata warning. Query-only repair groups such as
  `database_relation_template_source_mismatch` could be invisible from the
  slice. Seed-table context slices now inspect query-context repair groups too,
  so `suggested_next_actions` points to `describe_query_context` before agents
  draft or run queries.
- A project-brief query-repair entrypoint trial found no additional product gap
  after that fix: `project_brief.recommended_next_tasks` routed the synthetic
  database relation mismatch to `describe_query_context`, and dataset context
  slices did the same. The lower-level `project_brief.datasets[].query` summary
  can still preserve review-gated `draft_query_plan` actions after the context
  route; use the top-level task queue for autonomous ordering.
- A database relation repair staging trial showed the add-then-remove workflow
  reaches a clean database handoff, but after applying the reviewed storage
  relation the remaining mismatch still suggested another placeholder add.
  Relation-mismatch repair hints now expose existing storage-access relation
  templates and mark the add action `already_satisfied` whenever the storage
  access already carries relation template(s), so the remaining ordered action is
  the reviewed removal of the misplaced dataset or partition template. Rerun
  `describe_query_context` after each applied query metadata repair.
- A privacy/export query-planning trial confirmed DoxaBase's scanner blocks fake
  secret-shaped RDF terms in exports with `fail_on_sensitive=true` and warns in
  Markdown review bundles. Markdown staged/profile review exports now also
  accept `fail_on_sensitive=true` to raise before writing generated review bundles
  with secret-shaped literals. Query-planning surfaces intentionally echo
  non-secret handles and paths such as endpoint profile names,
  credential-reference handles, source/result paths, URI templates, relation
  identifiers, and connection references. Treat raw helper payloads as
  collaborator-visible planning metadata; summarize or redact unexpected
  local/runtime references in reports.
- A project-brief frontier trial found `pending_staged_profile_update_iris`
  correctly prevented duplicate profile-map staging, but also demoted the whole
  `profile_review` task when metric vocabulary, type advisory, or scalar conflict
  lanes remained open. Project brief priority now only demotes pure map-update
  reruns; open advisory/conflict lanes keep profile review at normal priority and
  the task reason names the remaining lanes.
- A human-review artifact trial confirmed grouped staged export JSON is
  sufficient for autonomous routing across alternatives, restage lineage,
  snapshot evidence, resolved targets, and review sequence. Markdown was mostly
  self-contained, but `Resolved Targets` hid `semantic_risk_level` and
  `alternative_gate_status`. Grouped Markdown now includes semantic risk and
  alternative gate columns in `Resolved Targets` so Markdown-only reviewers can
  scan row-vs-target routing and semantic gates together.
- A staged-systematisation shared-context trial showed that the draft-level
  `shared_semantic_context_applies_to_all_framings` warning was useful, but
  graph roles alone were ambiguous and grouped exports lost the warning after
  handoff. Structured warnings now include parsed shared patch summaries,
  fallback revision IRIs, and original shared patch source selectors; grouped
  exports reconstruct shared ontology/shapes context from stored patch roles so
  export-only agents can inspect or restage fallback alternatives before apply.
- A query-planning repair-option audit found the compact
  `pending_action_options[]` route was the right scripting entrypoint, but it
  dropped safety text from the full action templates. Compact pending options
  now carry available `reason`, `condition`, and `review_rationale_guidance` so
  agents can choose branches without losing review gates. The same audit found
  `record_map_storage_access(path_templates=...)` is easy to misread for
  database storage: for `rc:DatabaseStorage`, path templates are reviewed
  storage-owned relation identifiers such as `schema.table`, while
  `storage_root` is the connection reference.
- A column-seeded context-slice trial found mapped column seeds expanded to the
  owning table but skipped query-repair routing because the owner table was not
  itself a literal seed. Dataset/deep-lore slices now treat seed-reached owner
  tables like table seeds for `describe_query_context` suggestions, so column
  handoffs surface owner-table repair groups such as
  `database_relation_template_source_mismatch`.
- An applied query-repair history trial found dataset `deep_lore` slices could
  show current storage/layout/partition map resources but miss the staged and
  applied revisions that changed them when those revisions were anchor-only.
  Deep-lore slices now reverse-follow `rc:revisionAnchor` from selected
  resources through `revision_anchor_match`, so dataset/storage/layout/partition
  handoffs can show staged or applied query-metadata repairs even without
  supporting claim, observation, or pattern links.
- A query-repair lifecycle trial found the database-relation remove flow already
  cleared routing after apply: `describe_query_context` became ready,
  `project_brief` queues emptied, and a dataset context slice stopped suggesting
  repair actions. Keep that as a regression when changing staged query repairs so
  pending staged repair IRIs do not survive after the reviewed repair is applied.
- A follow-up query-repair lifecycle trial found staged repairs on linked storage
  access resources, such as database relation-template adds or storage protocol
  replacements, were not counted as pending repairs for the owning dataset.
  Project brief pending repair detection now associates dataset query contexts
  with linked storage, layout, partition, and column resources, and
  `describe_query_context` marks exact matching repair actions as
  `already_pending` so agents do not stage duplicate metadata repairs.
- A project-brief frontier trial found pending query repairs and profile-map
  updates could disappear when the matching staged row was outside the bounded
  `staged_review.items` slice. Project brief still keeps displayed staged rows
  limited, but pending query/profile detection now scans the current staged work
  set so hidden staged rows can still lower duplicate repair/staging tasks.
- A storage-seeded handoff trial found `resource_brief` showed an owning dataset
  through `incoming_reference` but left agents to infer the
  `describe_query_context` follow-up manually. Resource briefs now treat
  directly seed-reached owner tables like table handoffs for query-context
  suggestions, so storage access, layout, partition, and column seeds can route
  to repair groups such as `missing_physical_layout` without changing the slice
  into a dataset brief.
- A privacy/export staged Markdown trial confirmed bearer-style warnings,
  line labels, `fail_on_sensitive=True`, and source-span linked support worked
  after the export-support changes, but found bare `sk_` live/test style keys
  were not matched by the shared scanner. Sensitive graph-term and Markdown
  scans now include that key family; treat the scanner as a conservative
  guardrail, not a complete replacement for human export review.
- A profile-insight frontier trial confirmed awkward project metric and value
  type workflows can record profile bundles, stage map updates, stage metric
  vocabulary promotions, detect pending duplicate metric promotions, and export
  related profile insight review bundles. The trial found profile route bridge
  Markdown could repeat the same review lane several times when one project
  metric appeared across multiple profile observations. Markdown now groups
  repeated lane labels with a route-group count while preserving full route keys
  in JSON.
- A profile-insight lane visibility trial staged only the default map update
  from a profile run that still had row-count scalar conflicts plus metric and
  type advisory lanes. The route bridge correctly linked the staged map row to
  metric/type support, but the unresolved scalar lane was invisible in the
  export. Profile insight bundles now expose `open_profile_review_lanes` and an
  `Open Profile Review Lanes` Markdown table for live draft route groups that
  lack a direct-action candidate.
- A project-brief frontier trial showed low `limit` omissions were already
  visible through `omitted_queue_counts`, `limit_crowded_queue_types`, and
  `health_tasks`, but low `profile_candidate_limit` could hide profile evidence
  before drafts entered `queue_counts`. Project brief now reports per-dataset
  `profile_candidate_omitted_count`, top-level
  `profile_queue_counts["profile_candidate_omitted"]`, and an
  `expand_profile_candidate_limit` health task.
- A staged-recovery workflow trial exercised two stale rows plus one ready row
  through recovery planning, dry-run batch restage, real batch restage/export,
  apply-one-then-replan, sibling restage, and exact applied diff inspection. The
  workflow behaved as intended. The main scripting reminder is field naming:
  direct apply checks expose `decision`, while list rows expose
  `application_decision`.
- An AIS query-planning workflow trial confirmed the documented DailyIndex
  overlay route: a fresh scratch capsule moved from stale broadcast layout
  review to a wildcard daily-index handoff after applying the reviewed stale
  partition-scheme removal. No query-planning code change was justified. The
  active MCP capsule may lag fixture state; sanity-check `graph_overview`
  counts when a long-lived capsule reports unexpectedly sparse storage metadata.
- A profile-derived systematisation trial confirmed profile bundles, map-update
  staging, caveat claims/patterns, pattern promotions, and profile insight
  exports can stay connected across ambiguous semantic choices. It also found
  `record_pattern(confidence=...)` accepted unsupported confidence terms and
  only failed later under SHACL. `record_pattern()` now preflights pattern
  confidence, status, and stability controlled values before writing RDF, and
  `record_claim_observation()` preflights claim confidence values.
- A context-slice handoff trial found `deep_lore` on a storage-access seed
  included the seed but did not route to the owner table, while
  `resource_brief` did. Storage/layout/partition seeds that mismatch
  `deep_lore` now get a `Retry with resource brief` action so agents can reach
  owner-table `incoming_reference` routes and then `describe_query_context`.
- A staged same-slot repair trial confirmed the repair route works, but showed
  `mutation_frontier_iris` can be empty before a successor exists. For those
  lanes, follow `lane.next_action.arguments` or
  `lane.repair_draft.preferred_action.arguments` instead of treating the empty
  frontier as no actionable repair.
- A cold handoff/import trial found applied-diff snapshot recovery actions stay
  nested under `snapshot_evidence.suggested_next_actions` and
  `source_snapshot_evidence.suggested_next_actions`. Do not expect a top-level
  `describe_applied_revision_diff().suggested_next_actions` promotion.
- A staged-review Markdown trial found that warnings about omitted recommended
  review targets could appear after the `Reviewer Decision Matrix`, letting a
  Markdown-only reviewer act before seeing that a refreshed successor was
  outside the bundle. Grouped staged exports now put `Bundle Warnings` before
  the decision matrix so missing imports, omitted targets, and sequencing
  hazards are visible first.
- A query-planning project-brief trial found that unrelated fresh repair tasks
  could appear before the visible `staged_review` item even though the brief
  already advertised `staged_frontier_review`. Project brief now orders returned
  staged-review rows ahead of fresh query/profile mutation tasks; omitted fresh
  queues remain visible through `omitted_queue_counts` and `health_tasks`.
- A cold-start context-slice trial found an undefined observed value type from a
  profile run errored as a missing seed. Dataset/deep-lore slices now accept
  IRIs referenced only through `rc:observedValueType`, expand through matching
  profile observations, and preserve the exact rows in
  `seed_profile_observations`.
- A profile-systematisation trial confirmed profile route bridge rows preserve
  every route key, but surfaced two response-shape traps: `profile_route_groups`
  rows are dicts, and `stage_profile_map_updates.status_counts` covers the full
  draft even for one-option scalar conflict calls. The agent docs now make both
  shapes explicit.
- A physical-layout repair trial found a dataset with one verified layout and
  one stale candidate layout could leave the otherwise direct-clean query route
  blocked without a repair group. `describe_query_context` now treats stale
  same-signature physical-layout links as context blockers when a verified
  sibling layout remains, and exposes a reviewed
  `remove_stale_physical_layout_link` staging action that removes the stale
  `rc:hasPhysicalLayout` assertion.
- A cold-start search trial found unscoped lexical searches for generic terms
  such as "storage" and "row count" can return mostly immutable seed graph hits,
  hiding current project facts. `search(graph=None)` now adds
  `scope_hint.status="seed_heavy_unscoped_results"` plus scoped retry actions
  when the returned page is seed-heavy; follow `graph="map"` and the other
  project graph retries before treating a project fact as absent.
- A staged-export omitted-successor trial confirmed direct exports should stay
  caller-scoped even when a stale source's current successor is outside the
  bundle. `bundle_summary.external_recommended_review_iris` now exposes those
  omitted current review targets structurally while `mutation_frontier_iris`
  remains limited to included rows.
- A follow-up physical-layout trial confirmed same-signature stale layout links
  now repair cleanly, while distinct-signature ambiguity still needs explicit
  review. Do not treat verified Parquet plus candidate CSV as automatic stale
  cleanup; select the intended layout for drafting, then verify or remove the
  non-selected layout through a reviewed graph change.
- A project-brief frontier trial confirmed `next_best_expansion` prevents a
  low-limit brief from hiding query/profile/non-tabular work, but mixed
  `limit` and `profile_candidate_limit` constraints can still require several
  reruns. The later `full_frontier_expansion` affordance collapses those steps
  when an unattended agent wants one deliberate full-frontier rerun.
- A query-handoff trial found ready query plans were discoverable inside
  `datasets[].query.suggested_next_actions` but absent from
  `recommended_next_tasks`, so queue-following agents could miss ready physical
  handoffs. Project brief now emits low-priority `query_plan_handoff` tasks for
  `ready_for_query_planning` datasets, and `draft_query_plan` includes
  `handoff_summary` for compact non-executed handoff reports.
- A staged review-bundle handoff trial confirmed same-capsule staged Markdown
  exports are compact and actionable, but cross-capsule TriG/snapshot handoffs
  can produce false `target_digest_drift` conflicts when blank node identifiers
  change across export/import. Treat blank-node-canonical graph digests or
  RDF-isomorphism-aware drift checks as a project-level follow-up before relying
  on fixture-heavy cross-capsule apply/rebase handoffs.
- A privacy/export trial found `privacy_export_review`, redacted scans, export
  warnings, and `fail_on_sensitive=True` block paths work without exposing
  planted sensitive-looking values. The main remaining affordance gap is a
  first-class export preflight decision helper that distinguishes `block`,
  scanner-clean-only, and broader shareability-review states.
- The follow-up preflight loop added `export_preflight` for graph, TriG,
  revision-snapshot, and handoff-bundle exports. Use it when an agent needs a
  read-only export decision before choosing paths: `decision="block"` means a
  blocking export would fail, while `decision="clean_by_scanner_only"` still
  requires separate shareability review for paths, endpoints, history payloads,
  and project facts.
- A profile-to-map promotion trial confirmed awkward profile evidence can move
  through normal map recommendations, metric/type advisory lanes, pattern
  support, systematisation alternatives, and grouped staged exports without a
  new code helper. The main agent friction is advisory follow-through: after
  `record_pattern`, copy the returned `pattern_iri` into later
  `stage_map_assertion_change(... supporting_patterns=[...])` calls when the
  staged assertion should carry pattern support.
- A staged recovery and handoff trial confirmed count drift, same-count digest
  drift, blank-node drift details, restage/apply flow, and cross-capsule
  RDF-plus-snapshot handoff all work. RDF-only import leaves exact applied diffs
  unavailable by design; import the companion `export_revision_snapshots` JSON
  before expecting exact changed triples.
- A project-brief frontier reproduction showed following only
  `next_best_expansion` can require several reruns when both `limit` and
  `profile_candidate_limit` hide work. `project_brief.full_frontier_expansion`
  now provides a deliberate one-call rerun that expands both bounds enough to
  expose all currently counted task payloads and hidden profile draft candidates.
- A broader project-brief frontier trial confirmed the low-limit brief is still
  a trap for unattended loops if the agent repeats visible staged-review work.
  Treat `full_frontier_expansion` and `health_tasks` as mandatory before
  repeating visible tasks when `full_frontier_expansion` is non-null; it exposed
  hidden query repair, profile, non-tabular, ready-query, and privacy/export
  work in one rerun.
- A storage/query-planning trial with local files, partitioned CSV, and multiple
  database relations confirmed ready handoffs are discoverable, but also showed
  agents can follow candidate 0 too literally when it is an archive relation.
  `query_plan_handoff` tasks now carry `query_plan_handoff_summary` so the brief
  itself surfaces selected relation/URI, handoff kind, execution blockers,
  required bindings, and unselected ready/direct-clean candidate indexes.
- A non-tabular/context-slice trial confirmed API endpoints, document
  collections, and message streams do not need table-shaped fake columns. Model
  them with `record_map_dataset(is_table=False, extra_types=[...])`, use
  `describe_resource` or `describe_context_slice(profile="deep_lore")` for
  handoff context, and treat `describe_query_context` status
  `not_applicable_non_tabular_asset` as expected unless a separate queryable
  table route has been modeled.
- An ontology/systematisation trial confirmed the systematisation flow works for
  awkward shared vocabulary proposals, but agents still trip on SHACL result
  shape. Staged-revision diagnostics live in `validation_results[]`, and the
  diagnostic text field is `messages[]`, not singular `message`.
- An assertion-lineage trial showed `stage_map_assertion_change` gave the right
  judgement panel but was too write-oriented for "should I change this?" review.
  Use `draft_map_assertion_change` first when evaluating a single assertion:
  it returns support, patch, validation, impact, semantic-risk, and stage-action
  previews without writing `history`.
- A four-way workflow trial wave retested assertion judgement, staged drift
  recovery, profile-to-query handoff, and storage-aware query planning. The main
  workflows all completed end-to-end. The follow-up fixes were steering, not new
  workflow machinery: high-risk or do-not-stage assertion drafts now put support
  review before the explicit stage override; database relation mismatch repair
  groups/options expose first-class misplaced-template source fields; docs now
  distinguish stale-source replay status from lineage resolution and note that
  post-apply profile follow-up can remain queued while a ready query handoff is
  still independently useful.
- A broad query/systematisation/handoff/version wave confirmed agents can carry
  query evidence through claim, pattern, staged assertion, and apply; preserve
  awkward cross-table modelling as systematisation alternatives; and move staged
  work across capsules with TriG plus revision-snapshot JSON. The concrete
  follow-up was guardrail and recipe work: claim observations now reject
  unsupported status terms before writing RDF; local CSV query trials should use
  verified layout status after checking the path/header; and cross-capsule
  staged handoffs should spell out preflight, TriG import, snapshot-evidence
  check, snapshot JSON import, and staged-revision inspection.
- A second broad wave checked staged-payload discovery, grouped review-bundle
  readability, local CSV query smoke flow, and MCP/API parity. It found no MCP
  runtime gap, but did surface review-handoff scan friction: grouped staged
  exports now expose `decision_headline`, `changed_graph_counts`, and
  `choose_one_groups`, and the Markdown starts with an `At A Glance` rollup.
  A follow-up staged-discovery fix added
  `search_staged_patch_payloads`, so remembered staged-only labels and comments
  route to owning revisions instead of appearing only as generic
  `rc:patchContent` history hits. Remaining larger follow-ups are a tracked
  local CSV query smoke example and refreshing README/ARCHITECTURE status
  lists.
- A follow-up local CSV smoke trial completed end-to-end with exact local object
  storage, verified CSV layout, `draft_query_plan` reaching
  `execution_attempt_ready`, Python CSV fallback execution, `record_query_result`,
  and SHACL validation. The runtime gap was not query planning itself:
  custom `evidence_summary` text could hide execution status, engine, and query
  hash from later `describe_query_context` handoffs. Query-result evidence now
  stores those fields structurally, and `examples/local-csv-query-smoke.py`
  preserves the exact scratch workflow as a tracked smoke example.
- A privacy/export trial confirmed scanner warnings and `fail_on_sensitive=True`
  block paths behave consistently without leaking synthetic canaries. The
  remaining risk is over-reading scanner-clean exports as shareable; export
  preflight now carries `shareability_review_status="required_not_completed"`
  alongside `clean_by_scanner_only`.
- A cross-session staged recovery trial confirmed TriG-only handoffs correctly
  route to `complete_handoff_import` with `history_only_count_digest`, then to
  `restage_after_review` with `history_plus_snapshot_rows` after importing
  revision snapshot JSON. Snapshot evidence made real source-side drift
  distinguishable from handoff damage; no implementation change was needed.
- A project-brief frontier trial with simultaneous staged, query, profile,
  non-tabular, query-handoff, and export-health queues confirmed low-limit
  briefs can hide work but expose enough expansion hints. In read-only trials,
  after classifying a staged frontier you cannot mutate, continue through
  `full_frontier_expansion`, `health_tasks`, and non-mutating routes such as
  `draft_profile_map_updates(profile_evidence_iri=...)` instead of repeatedly
  inspecting the same staged row.
- A staged repair/rebase trial confirmed same-slot replacements route to
  repair helper actions while unrelated stale additions route to mechanical
  restage. Planner warnings now call out that helper repair mutations live in
  `helper_mutation_frontier_actions`, not `mutation_frontier_iris`, so
  unattended scripts do not treat the IRI frontier as complete.
- Non-tabular and staged-only discovery trials confirmed the important
  boundaries stayed intact: APIs and other non-table assets did not get forced
  into row-count map updates or query plans, and staged-only resources stayed
  out of live context slices. The follow-up guidance is failure-path routing:
  zero-candidate profile insight exports write no Markdown artifact, and empty
  live-resource/context lookups for remembered proposal IRIs should route to
  `list_resource_revisions(include_patch_mentions=True)` or
  `search_staged_patch_payloads` before declaring the resource absent.
- A partial handoff hygiene trial showed most incomplete imports route safely,
  but history-plus-snapshot-only capsules were misleading: exact snapshot rows
  were present while current project graphs were absent, so recovery planning
  could propose mutation routes against an incomplete capsule. Snapshot evidence
  now reports `missing_current_graph_roles` and promotes `import_trig` /
  `complete_handoff_import` before apply, restage, or repair planning in that
  state.
- A storage/query planning trial confirmed local CSV directory storage and
  database relation handoffs stay distinct. Misplaced database-looking
  dataset/partition templates remain repair inventory with
  `database_relation_template_source_mismatch`; only storage-access-owned
  templates become `relation_identifier` handoffs, even when the misplaced text
  already looks like `schema.table`.
- A staged recovery frontier trial confirmed agents can avoid bad bulk moves by
  following recovery lanes, `would_restage_revision_iris`, helper mutation
  calls, and post-apply replans. The only durable confusion was terminology:
  list rows use compact `record_kind` values such as `staged_patch`, not
  `staged_revision`.
- A profile/systematisation trial confirmed awkward profile evidence can move
  through profile map updates, pattern promotion, systematisation alternatives,
  staged recovery, and profile insight exports. The concrete gap was direct
  route closure for caller-authored query repairs: `stage_systematisation` now
  accepts `profile_route_sources`, so agents can pass
  `query_action.source_query_context` and let the profile review bundle mark the
  lane as `direct_action`. The draft returns `profile_route_source_count` and
  warns when supplied input normalises to zero usable route sources, which helps
  unattended agents catch passing the whole action instead of its source block.
- A richer profile-metrics trial showed metric/type advisory lanes could remain
  open even after related staged promotions or systematisations existed, because
  agents had to mentally regroup many advisory actions. `draft_profile_map_updates`
  now returns `advisory_followthrough_plan`, grouping metric/type actions by
  semantic move: define metric, define value type, assert map type, or record a
  caveat/pattern fallback.
- A follow-up profile plan trial confirmed that agents can complete this route
  end to end. The remaining gap was consistency: plan primary calls often use
  `stage_pattern_promotion`, so that helper now forwards `profile_route_sources`
  just like `stage_systematisation`.
- A recovery/export trial confirmed project TriG plus revision-snapshot JSON
  is enough for unattended recovery, while workflow/review TriG alone is only
  review context. `export_preflight` and `export_trig` now warn when a TriG
  export omits history and snapshot rows so agents do not mistake review bundles
  for recovery bundles.
- A broader profile-metrics trial showed `advisory_followthrough_plan` could
  still be misused by scripts that selected only `semantic_move`: a lane such
  as `define_metric` may have inspect-context rows and a separate staging row.
  Followthrough items now expose `primary_action_kind` and
  `primary_action_writes_graph`; scripts should match both the semantic move
  and intended action kind before staging or recording changes.
- A staged conflict/version trial confirmed the full recovery and version
  browsing path works across stale sources, mechanical restage successors,
  same-slot repair, one-row apply, post-apply replan, lineage, applied diffs,
  and graph snapshots. The remaining risk was doc hopping, so
  `staged-revisions.md` now has a compact cookbook: plan, complete imports,
  dry-run, restage only `would_restage_revision_iris`, check/apply one row,
  rerun the planner, and handle repair lanes through explicit helper actions.
- An export/privacy handoff trial confirmed scanner-clean context slices can be
  imported from dirty capsules, while staged/profile Markdown exports are
  review-only and workflow TriG is importable but not a complete recovery
  handoff. Export records now expose `artifact_kind`, `importable`,
  `recommended_import_tool`, and `recovery_complete` so agents can route these
  artifact classes mechanically.
- A profile advisory grouping trial found that broad same-lane evidence could
  make sibling type routes look directly closed when only one assertion or
  promotion had actually been selected. `stage_map_assertion_change` now accepts
  `profile_route_sources`, matching `stage_pattern_promotion` and
  `stage_systematisation`; profile insight bundles reserve `direct_action` for
  persisted route sources and leave live draft overlap as support-only context.
  A follow-up profile/systematisation trial showed generated mutating advisory
  actions should be executable directly, so their arguments now include the
  selected `profile_route_sources`. Use plan item source blocks when staging
  caller-authored alternatives, and check `profile_route_source_count` before
  treating an advisory lane as closed.
- A profile metric/type fallback trial found generated advisory routes still
  pushed awkward evidence toward inspection or direct pattern recording before
  making a reviewable graph-change option obvious. Profile metric and type
  lanes now generate pattern-only `stage_systematisation` fallback actions with
  `profile_route_sources`; `caveat_fallback` plan items prefer that staged
  review path over direct `record_pattern` writes.
- A query-evidence overlay trial found that `record_query_result` made source
  paths, result artifacts, execution status, and query hashes visible, but an
  agent still had to hand-author RDF before that evidence could repair missing
  storage/path/layout query-planning metadata. Use
  `draft_query_evidence_storage_overlay` after reviewing the actual source
  storage values; it drafts a non-mutating staged overlay with the query/profile
  observation and evidence attached, then agents can check/apply and rerun
  `describe_query_context`.
- A project-brief frontier trial confirmed low-limit briefs can initially show
  only staged work, but `health_tasks`, `next_best_expansion`, and
  `full_frontier_expansion` route agents to hidden query repair, profile,
  non-tabular, privacy, and ready-query queues. The same trial found the
  privacy health count must match the handoff-bundle preflight it recommends,
  because revision snapshots can contain additional sensitive-looking terms
  beyond current project graphs.
- A privacy/export handoff trial confirmed the scanner and fail-on-sensitive
  guards work for graph/TriG/snapshot/handoff, context-slice, staged-review, and
  profile-review artifacts, but agents need a compact route matrix to choose
  the right preflight/write helper under pressure. Use the `mcp_tools`
  privacy/export matrix before writing handoff artifacts.
- A review-bundle portability trial confirmed full project/history TriG plus
  revision snapshot JSON is enough for exact recovery, while workflow TriG,
  Markdown review bundles, and context-slice TriG remain review artifacts. A
  context slice can include selected `history`/`rc:GraphRevision` triples and
  still lack SQLite-side snapshot rows, so history-bearing context-slice exports
  now warn and point to `export_handoff_bundle` for recovery-complete handoffs.
- A storage-metadata-assisted query-planning trial confirmed database relation,
  S3 prefix/runtime, exact local object, ambiguous-layout, and query-evidence
  overlay routes reach safe non-executed handoffs or repair gates. It also found
  query-evidence overlays could fail validation when a dataset already had
  `rc:CandidateLayout`; `draft_query_evidence_storage_overlay` now carries
  replacement removals for old dataset layout verification status/note values
  so reviewed query overlays stage cleanly.
- A follow-up four-way frontier trial found the right next workflow step could
  still be split across separate advanced surfaces. `project_brief` now exposes
  `frontier_first_action` as the canonical first hop, query contexts with
  singleton query/profile evidence plus physical blockers can suggest a reviewed
  `draft_query_evidence_storage_overlay` skeleton, and staged recovery plans
  expose `mutation_frontier_items` so same-slot helper actions and existing
  revision targets share one unattended mutation worklist.
- A broader privacy/query/non-tabular/systematisation wave confirmed the revised
  goal reaches less-polished project areas. Privacy/export preflights and write
  gates blocked correctly, but context-slice export `seeds[]` and
  `project_brief` resource descriptions could echo planted fake-secret display
  text; those response summaries now redact scanner-matching labels and
  descriptions while faithful RDF exports still require `fail_on_sensitive` to
  block. The same wave found database relation template repair options were
  executable but label-light; `add_reviewed_relation_template` now carries an
  `action_label` through pending action options.
- The same wave found no immediate non-tabular or ontology/SHACL correctness
  fix. Non-tabular assets stayed visible outside query-planning lanes, but tight
  context-slice exports could make graph-role loss easy to miss. Systematisation
  preserved awkward shape-backed alternatives, but a future helper action could
  generate the rerun that moves shared ontology/shapes patches into selected
  framing patches.
- A follow-up context-slice export trial reproduced the graph-role loss:
  truncated preflights could return `graphs=["map"]` while structured slice
  resources included pattern, observation, evidence, and vocabulary roles.
  Context-slice exports now warn that `graphs`/`graph_counts` describe only
  capped raw triples, name omitted roles, and put a full-cap preflight action
  before the write action. A shared-context rerun trial clarified that
  `fallback_revision_iris_with_shared_semantic_context` is an inspection subset,
  not an automatic drop list; target framing selection still requires semantic
  judgement.
- The same follow-up wave found profile-to-map review/apply mechanics can close
  scalar, query, metric, and type lanes cleanly, but `project_brief` could
  surface a context-only `project_metric_defined` advisory as `profile_review`
  after `export_profile_insight_review_bundle` reported `open_lane_count=0`.
  Project brief now treats all-`project_metric_defined` metric advisories as
  context handoffs: they stay visible in profile draft summaries and raw queue
  counts, but do not create `profile_review` tasks without map updates, scalar
  conflicts, open metric vocabulary, or type findings.
- A broad post-fix wave passed across staged recovery, storage query planning,
  review-bundle/export hygiene, and project-brief frontier selection. Staged
  recovery handled same-count digest drift, batch restage, sequential
  post-apply recheck, handoff bundle import, and exact applied diffs in a cold
  capsule. Storage query planning reached a database relation handoff through
  missing storage/layout repair, moving a relation template onto storage, and
  removing the misplaced dataset template; `ready_for_execution_attempt=false`
  remained correct because runtime execution was still external. Review/export
  hygiene blocked staged/profile/handoff artifacts with strict scanner gates
  and confirmed that scanner-clean context slices only cover selected triples.
  Mixed `project_brief` frontiers routed to `full_frontier_expansion` and the
  defined-metric context-only draft no longer created `profile_review`.
- A resource/version browsing trial confirmed the new resource-lineage
  `applied_source_revision_iri` alias helps cold agents name the staged source
  that actually applied, but only when an applied event exists. Resource lineage
  now matches graph lineage and returns `None` for unapplied stale or
  still-current staged rows; use `current_staged_revision_iri` for those live
  staged targets.
- The next broad wave passed profile metric/type followthrough, and found two
  remaining rough edges worth carrying forward. Profile bundles preserve metric
  implications, but project value-type findings may need an explicit targeted
  pattern before type-review assertions have the same support trail.
  Shared-context systematisation recovery is possible from patch roles without
  Turtle surgery, but export-only recovery still requires a documented rerun
  recipe and semantic target-framing choice. Mixed object/database query
  planning now avoids pairing dataset or partition file templates with database
  storage when the same template already forms a clean non-database candidate;
  if a database relation mismatch remains, treat it as a true database-route
  review signal rather than object-route noise.
- A four-frontier retest confirmed the updated autonomous goal is reaching
  broad project surfaces rather than only local helper polish: project brief
  expansion exposed staged, query, profile, and ready-handoff queues together;
  staged recovery handled both count drift and same-count digest drift; privacy
  export gates blocked planted scanner hits while raw context slices remained a
  report-leak risk if pasted; review bundles preserved awkward alternatives but
  could use stronger modelling-choice summaries. Recovery lanes now carry
  `exact_drift_summary` so cold agents can report count/digest drift evidence
  before drilling into full apply-check payloads.
- A follow-up four-trial frontier wave confirmed that broader steering keeps
  surfacing independent workflow gaps. Context-slice privacy trials showed raw
  `describe_context_slice` payloads can expose planted scanner hits even when
  export/preflight surfaces redact correctly; context slices now return redacted
  scanner metadata and a privacy preflight action, while raw triples/TriG remain
  faithful inspection content. Profile value-type trials found
  `export_profile_insight_review_bundle` can over-close a shared route group
  after staging only a value-type vocabulary promotion, leaving the map
  `rc:valueType` assertion open in the live draft; profile route groups now
  track direct semantic moves so `define_value_type` does not close
  `assert_map_type`. Project-brief onboarding trials showed low-limit briefs
  expand correctly but profile-review tasks needed a read-only hop when their
  primary suggestion is mutating; `profile_review` tasks now expose
  `inspection_next_action` for `draft_profile_map_updates`. Grouped
  review-bundle trials showed awkward modelling choices need stronger
  top-level decision summaries, structured framing roles, and common support
  rollups; grouped staged exports now return modelling-choice summary rows for
  repair diagnostics, map candidates, vocabulary/shape candidates, and
  pattern-first alternatives.
- A staged-recovery frontier trial successfully completed digest-drift and
  count-drift recovery through batch restage, sequential apply/recheck, lineage,
  and applied-diff inspection. The remaining unattended-loop risk was missing a
  nested grouped-bundle sequencing hazard after a real batch restage; batch
  restage responses now mirror `requires_recheck_after_each_apply` and
  `sequential_apply_recheck_candidate_iris` at top level.
- A profile-to-map promotion trial confirmed query review, profile map updates,
  metric vocabulary, and value-type vocabulary can travel together in one review
  bundle, but vocabulary definition closure was still too indirect. Profile
  insight review bundles now expose semantic move closure rollups so agents can
  see, for example, `define_value_type` closed while `assert_map_type` remains
  open.
- A storage-metadata query-planning trial confirmed mixed object-store and
  database storage routes can both be drafted correctly when selected
  explicitly, and that similarly named storage linked to another dataset stays a
  review candidate rather than an automatic target. The remaining friction was
  selector ergonomics: `storage_access_iri` can still match several candidate
  paths, so the query-planning doc now gives the maintained
  `candidate_index` + `physical_layout_iri` selector route for mixed storage.
- A cross-capsule staged handoff trial confirmed the TriG-first recovery path
  can recover exact stale drift, batch restage successors, apply one row, and
  replan siblings in a cold capsule. The remaining reversed-order gap was
  snapshot JSON imported before project/history RDF: explicit recovery planning
  now routes those `snapshot_rows_without_history` rows to
  `complete_handoff_import` with an `import_trig` action instead of raising.
- A query-result follow-up trial confirmed the storage-metadata-to-execution
  handoff can close through an external Python CSV fallback, `record_query_result`,
  `describe_profile_run`, profile map update drafting, and project-brief queues.
  The older post-write routing gap is now closed: `record_query_result` returns
  follow-up actions for `describe_profile_run` when the result is profile-shaped
  and `describe_query_context` whenever `observed_asset` is supplied.
- A staged version/rebase frontier trial confirmed snapshot-first explicit
  recovery now queues `complete_handoff_import`, and the same capsule can then
  proceed through history import, exact drift detection, same-slot replacement
  drafting, repair successor staging, apply, lineage, and exact applied diff.
  The broader frontier remains first-class handoff-manifest import/recovery and
  a durable rebase/version session object that groups source rows, selected
  repair choices, successors, applied events, and snapshot evidence.
- A follow-up staged version/rebase trial found the manifest half of that
  frontier was the next unattended blocker: receivers still had to translate
  paired artifact paths from the manifest into separate `import_trig` and
  `import_revision_snapshots` calls. `import_handoff_bundle` now consumes the
  manifest directly, dry-runs receiver paths, imports TriG before snapshot rows,
  returns snapshot evidence at each phase, and hands back a staged recovery plan.
- A broader staged revision frontier trial then confirmed manifest import,
  count-drift restage/apply, same-slot repair/apply, lineage, and exact applied
  diffs all work across scratch handoffs. The remaining autonomy gap was
  session-level continuity: agents had to keep the imported bundle, source
  revisions, selected lane, successor, apply event, and replan checkpoints in
  local notes. `start_staged_revision_recovery_session` now persists the ordered
  source set and planning parameters, while
  `describe_staged_revision_recovery_session` recomputes the live plan and
  source states after each mutation.
- A project-brief/privacy trial confirmed low-limit briefs still expose staged,
  query-repair, profile-review, and expansion frontiers while export preflight
  blocks scanner-positive handoff/profile artifacts with redacted snippets. The
  gap was first-hop salience: privacy/export review lived only in `health_tasks`,
  so `project_brief` now exposes `safety_first_action` for blocking
  `privacy_export_review` before the normal `frontier_first_action`.
- A profile-frontier trial confirmed agents can keep map updates, metric
  vocabulary, value-type assertions, and alternative systematisations in one
  review bundle, but mixed-support comparisons were too easy to miss before
  staging. `draft_profile_map_updates` now exposes
  `mixed_support_review_groups` so shared support patterns, review lanes,
  semantic moves, and suggested calls are visible together before applying any
  one lane.
- A project-brief/query-repair frontier pass on an older local capsule found a
  stale immutable seed graph could leave `query_repair_review` and
  `profile_review` tasks visible even though staging-oriented follow-up helpers
  would fail on missing staging vocabulary. `project_brief` now routes
  `seed_recovery_review` through `safety_first_action` /
  `first_unattended_action` before frontier expansion or mutation work, while
  privacy/export review still takes precedence when both are present.
- A privacy/handoff trial with fake sensitive-looking scratch data confirmed
  cautious agents can avoid leaks by running `export_preflight` and keeping
  `fail_on_sensitive=True`; structured responses stayed redacted while faithful
  local Markdown, TriG, and snapshot JSON preserved the fake value. The
  manifest handoff route was clear, but the export result still pointed generic
  routers at the lower-level import sequence. Handoff exports that write a
  manifest now set top-level `recommended_import_tool` to
  `doxabase.import_handoff_bundle` while retaining the detailed
  `recommended_import_sequence`.
- A query-storage frontier trial confirmed clean local filesystem metadata can
  reach `execution_attempt_ready`, object-store metadata produces a useful
  runtime-gated DuckDB handoff, and database metadata should be consumed through
  `relation_identifier` plus `connection_reference` rather than file-scan
  fields. Future storage-aware planner work should turn that route into an
  executable contract test covering `record_query_result` evidence,
  `draft_query_evidence_storage_overlay`, local execution-ready planning, and
  mixed file/database explicit candidate selection.
- A profile-promotion trial confirmed the profile pipeline can carry row-count,
  nullable-column, unmapped-column, metric vocabulary, and value-type ontology
  work into staged review. The remaining semantic-judgement gap is ergonomic:
  vocabulary promotion has concrete staged skeletons, while caveat or
  systematisation fallbacks for awkward metric/value advisories still require
  more caller-authored RDF.
- A semantic same-slot rebase trial confirmed the recovery workflow can
  distinguish ordinary stale drift from a competing same-slot replacement after
  one alternative has been applied. Use `would_restage_revision_iris` only for
  mechanical restage work, route `same_slot_replacement` rows through the
  helper `stage_map_assertion_change(..., restages_revision=...)`, and stop at
  `alternative_to_applied_source` even when the repaired successor is
  mechanically ready. `examples/staged-semantic-repair-smoke.py` now exercises
  this repair-first loop in a scratch capsule.
- An MCP transport diagnostic showed that an enabled `codex mcp list` entry can
  still produce `Transport closed` when the command path, capsule filename, or
  capsule startup fails. `build_server()` now lazy-opens the capsule so
  `doxabase.list_docs` and `doxabase.get_doc` remain available before SQLite
  initialization; graph tools still surface capsule startup failures on first
  actual graph use.
- A privacy/frontier retest confirmed redacted preflights and
  `first_unattended_action` correctly put export safety before expansion or
  mutation. The subtle state is after expanding a sensitive capsule:
  `frontier_status.is_complete` can be true while
  `mutation_allowed_after` still blocks frontier or mutation work for safety
  review. Treat `first_unattended_action` and `mutation_allowed_after` as
  authoritative.
- A storage-metadata query trial confirmed the profile-like
  `record_query_result` to `draft_query_evidence_storage_overlay` path works
  from a cold capsule: record result, follow `describe_query_context`, fill the
  reviewed overlay placeholders, stage/check/apply, rerun context, then draft a
  plan. The weak spot was discoverability, not code behavior.
- A profile value-type support-trail trial confirmed targeted patterns can
  support vocabulary promotion first and a map value-type assertion second.
  `caveat_fallback` is an alternative route for unresolved type evidence, not a
  mandatory extra lane once the direct `assert_map_type` route closes the group.
- A non-tabular asset trial confirmed API, document, and object assets stay out
  of query-repair queues while preserving storage, layout, caveat, observation,
  evidence, and pattern context. Candidate-layout warnings on non-tabular assets
  are context-review signals, not instructions to force a query-planning repair.
- A shared ontology/shapes systematisation recovery trial confirmed grouped
  exports preserve shared-context warnings, but lane-first recovery and manual
  rerun reconstruction were still weak spots. Recovery lanes now surface
  `shared_context_applies`, `shared_context_patch_count`, and
  `shared_context_graphs`; use
  `draft_systematisation_shared_context_rerun` after semantic review selects
  which framings should keep the provisional ontology or shape context.
- A storage-overlay handoff trial showed agents could execute a scratch query
  and repair storage metadata, but had to infer the scanned input path from
  prose or local runtime context. `record_query_result` now accepts
  `scanned_source_paths`, stores them as `rc:DataSampleSource` spans, and
  exposes them in singleton query-context and storage-overlay previews.
- A profile-to-map promotion trial showed the type-review route was semantically
  sound but still required hand glue between the suggested `record_pattern`
  action and later `stage_map_assertion_change` calls. Profile type-review
  actions now carry route-scoped result-binding metadata: match
  `binding_key`, read the produced `pattern_iri`, and append it to
  `supporting_patterns` on the paired staged assertion action.
- A privacy/handoff trial confirmed dirty handoff exports block before writing
  artifacts and clean scanner output imports successfully, but the clean
  manifest did not preserve that scanner-clean is not shareability approval.
  `export_handoff_bundle` now writes preflight-style `decision`,
  `scanner_clean`, sensitive-count, and `shareability_review_status` metadata
  into both the result and manifest; `import_handoff_bundle` warns receivers
  when shareability review remains incomplete.
- A profile insight closure trial found the candidate rows preserved partial
  semantic-move state, but the top-level open-lane rollup could still
  whole-route-close a type-review group after `assert_map_type`. The rollup now
  closes only the direct semantic move, keeps `define_value_type` open when its
  vocabulary promotion is not staged, and suppresses only the fallback
  alternative after a direct map assertion.
- A mixed storage/query-planning trial with local CSV and database relation
  routes showed `ambiguous_physical_layout` actions were forming a Cartesian
  product between every candidate and every layout. The planner now filters
  layout-selection actions by route kind: file/object routes use file layouts
  such as `rc:CSV` or `rc:Parquet`, database routes use table layouts such as
  `rc:PostgreSQLTable`, `rc:SQLiteTable`, or `rc:MySQLTable`. Explicit
  cross-route selections remain inspectable but are blocked with
  `physical_layout_storage_protocol_mismatch` and stay
  `metadata_review_required`.
- Staged-version and handoff/import trials confirmed `describe_graph_version_diff`
  works for staged-before to applied-after, stored-version to current graph, and
  RDF+snapshot imports. The weak unattended path was calling direct snapshot or
  diff helpers too early after RDF-only or snapshot-only imports. Direct
  snapshot, applied-diff, and graph-version-diff helpers now promote
  snapshot-evidence import actions such as `import_revision_snapshots` or
  `import_trig` into top-level `suggested_next_actions`.
- A project-brief/frontier recovery trial found that
  `plan_staged_revision_recovery()` exposed apply/restage mutation frontier
  items even when imported handoff evidence still needed `import_trig` or
  `import_revision_snapshots` first. The plan now reports
  `mutation_allowed_after="handoff_preflight_required_before_mutation"` plus
  `blocking_preflight_actions` / `blocking_preflight_calls`; unattended agents
  should complete those imports and rerun the planner before using
  `mutation_frontier_items`.
- A privacy/export workflow trial found that `fail_on_sensitive=True` correctly
  blocked shareable exports, but profile orientation payloads could still carry
  scanner-matching dataset descriptions, profile summaries, evidence summaries,
  or evidence source strings into unattended reports. Profile/evidence
  orientation responses now redact scanner-matching display text in
  `describe_profile_run`, query-context `source_profile_evidence`,
  `project_brief`, and `export_profile_insight_review_bundle` return payloads.
  This is response hygiene only; RDF and Markdown artifacts remain faithful and
  should still use `fail_on_sensitive=True` when they need to block.
- A profile-to-map/systematisation trial showed that multi-framing
  `stage_systematisation()` calls could overstate direct profile route closure:
  top-level `profile_route_sources` were recorded on every framing, so a
  pattern-only fallback could look like it directly closed the same semantic
  moves as an ontology+map framing. Framing objects now accept
  `profile_route_sources` / `profileRouteSources` so alternatives can carry
  route sources only for the semantic move they actually close. Keep top-level
  sources for common routes that genuinely apply to every framing.
- A context-slicing/privacy frontier trial confirmed export preflights blocked
  dirty graph and review artifacts correctly, but `project_brief` could still
  leak scanner-matching metric terms through copied profile advisory action
  arguments, call strings, and `source_profile_advisory` route metadata.
  `project_brief` now recursively redacts embedded profile draft actions for
  orientation safety. Direct `draft_profile_map_updates` responses still retain
  raw executable action payloads for local mutation review.
- A staged conflict/rebase/version trial showed the recovery planner correctly
  handled mechanical restage, apply-one-then-replan, graph-version diffs, and
  handoff import gates, but `mutation_frontier_iris` could still include a
  validation-repair row whose next concrete action was diagnostic inspection.
  Repair lanes with only inspection or read-only repair-draft actions now stay
  visible in `lanes` and `next_action_queue` but are excluded from
  `mutation_frontier_iris` / `mutation_frontier_items`, with
  `mutation_allowed_after="repair_inspection_required_before_mutation"`.
- A broad unattended workflow wave retested stale-seed recovery,
  profile-to-map promotion, storage-metadata query planning, and staged
  revision handoff. Stale-seed recovery was the live blocker: no-staged-row
  capsules previously routed agents to docs and `import_handoff_bundle()` failed
  on empty revision lists. `project_brief` now points stale-seed health tasks to
  handoff preflight even when `current_staged_revision_count=0`, and empty
  snapshot bundles import with an empty recovery plan. The storage/query and
  staged-recovery workflows passed. Profile promotion passed but exposed stale
  direct-call same-pair staging noise: `stage_profile_map_updates` now rejects
  pending same dataset/evidence staged profile updates by default and requires
  `allow_pending_profile_updates=true` only after review confirms another staged
  update is intentional.
- A follow-up storage/query trial showed the existing bundled fixtures were
  either review-gated or already metadata-ready, so agents had to fault-inject
  missing storage/layout to practice the intended repair flow. The maintained
  `examples/missing-metadata-query-repair-smoke.py` now starts from a table with
  columns but no physical metadata, stages `missing_storage_access` repair,
  reruns context, stages `missing_physical_layout` repair, and drafts a ready
  local CSV handoff.
- A staged-revision handoff ergonomics trial showed that source capsules can
  already contain useful `rc:StagedRevisionRecoverySession` history. Receivers
  could discover those sessions manually, but `import_handoff_bundle()` nudged
  agents toward raw mutation actions or a duplicate receiver-local session. The
  import result now exposes `imported_recovery_session_iris` and
  `matching_recovery_session_iris`; when a matching session exists, its first
  suggested action is `describe_staged_revision_recovery_session`. Only start a
  receiver-local session when no matching imported source session is available.
- A profile/review-bundle handoff trial showed that full profile insight
  bundles preserved route keys well, but generic staged revision inspection and
  grouped staged Markdown hid `rc:profileInsightRouteSource` details. Generic
  `describe_staged_revision()` now exposes stored `profile_route_sources`,
  `profile_route_keys`, and `profile_route_groups`; `export_staged_revisions()`
  includes a compact `Profile Route Bridge` when any row carries those sources.
  Use this for receiver-side staged review handoffs when the full profile
  insight bundle is unavailable or when a generic staged bundle mixes profile
  and non-profile rows.
- A follow-up profile route bridge trial found staged direct metric promotion
  could close `define_metric` while still leaving only `caveat_fallback` open,
  even though applying the staged promotion cleared the lane. Profile insight
  review now treats direct `define_metric` satisfaction like direct
  `assert_map_type` satisfaction for same-route fallback closure: the fallback
  remains visible in route-group metadata, but it no longer appears as an open
  review lane when the direct metric move is staged.
- A project-brief performance trial found `project_brief()` was recomputing
  staged apply checks inside each profile draft while also building the staged
  review frontier. `project_brief` now reuses its staged review summary for
  profile pending detection, which cut the 16-row expanded frontier trial from
  about 32 seconds to about 7 seconds. A follow-up recovery-planner pass made
  `plan_staged_revision_recovery()` select current staged rows without an
  apply-check listing and reuse the checks already computed during dry-run
  planning; the same 20-row recovery plan dropped from about 19 seconds to
  about 10 seconds.
- An MCP surface audit found `doxabase.project_brief` and
  `doxabase.export_preflight` were registered and test-covered, but Codex lazy
  tool discovery could miss bare underscore searches such as `export_preflight`.
  Search exact dotted names before treating documented MCP tools as absent; the
  server instructions and start-here route now name these high-priority tools
  explicitly.
- A stale-seed recovery handoff trial on the local capsule confirmed the
  documented `project_brief` -> `export_preflight` -> handoff export/import
  route works without user input when run on `/tmp` copies. The fresh receiver
  capsule had current seed graph counts, matching mutable project counts, no
  remaining `seed_recovery_review`, and conforming validation. For trials that
  must be strictly non-mutating, use `DoxaBase.open_readonly(path)` or a copy;
  normal open paths can perform SQLite maintenance even when graph facts are not
  intentionally changed.
- An AIS DailyIndex overlay trial showed `describe_query_context` and singleton
  evidence inspection were mostly self-guiding, but a stale-seed source capsule
  blocks `draft_query_evidence_storage_overlay` before stage arguments can be
  returned. Follow the seed-recovery safety route first. On a fresh recovered
  capsule the overlay draft succeeded; `reviewed_overlay` now echoes optional
  non-secret storage and orientation fields so agents can audit the reviewed S3
  route without parsing the Turtle patch.
- A graph-version/resource-lineage trial confirmed stale -> restaged -> applied
  recovery survives handoff when source, successor, applied events, and snapshot
  rows are exported together. Existing resource revision queue items already
  expose resolved action targets, so the remaining gap was answer shape rather
  than correctness: `list_resource_revisions()` now includes a page-scoped
  chronological `timeline` for first-pass resource-history answers before
  opening lineage or diff cards.
- A privacy/resource-scope trial confirmed full project handoff preflight can
  correctly block on an unrelated dirty sibling while
  `preflight_context_slice_export` / `export_context_slice` still safely
  round-trip clean resource-scoped review context. Blocked broad preflight
  responses now suggest context-slice preflight with a target-resource
  placeholder so agents do not treat the block as all-or-nothing or weaken
  `fail_on_sensitive`.
- A multi-revision recovery trial confirmed the normal drift path is
  self-guiding through `plan_staged_revision_recovery`,
  `mutation_frontier_items`, dry-run batch restage, real batch restage, apply,
  and session replan. Same-slot repair actions already appear as
  `mutation_frontier_items[]` with `item_kind="helper_action"`; unattended
  scripts must not use `mutation_frontier_iris` as the complete executor queue.
- A project-brief frontier trial found `project_brief` is a strong local
  frontier guard: it avoids low-limit traps, surfaces hidden query/profile
  queues, and keeps stale-seed recovery ahead of mutation. It is not a strategic
  ambition engine for multi-day repo work; the outer loop still needs a
  deliberate build-priority selector or a future strategic-frontier helper.
- A non-tabular asset workflow trial confirmed current helpers can model image
  or document bundles without fake tables or columns using non-tabular
  datasets, storage/layout facts, asset-level relationships, observations,
  patterns, and context slices. Base vocabulary now includes common
  image/document `rc:FileFormat` terms (`rc:JPEG`, `rc:PNG`, `rc:TIFF`,
  `rc:GeoTIFF`, and `rc:PDF`), so agents do not need project-local terms for
  those formats. `record_map_relationship()` now accepts `source_endpoints` and
  `target_endpoints` for optional endpoint role/order metadata while preserving
  compatibility `sourceDataset` / `targetDataset` edges; use that route instead
  of `derivation_properties` for endpoint roles.
- A follow-up endpoint role/order trial found dataset-seeded
  `dataset_brief` context slices preserved relationship links but omitted the
  structured endpoint node bodies, so import lost endpoint role/order and failed
  SHACL validation. Dataset relationship routes now include
  `relationship_endpoint` and `relationship_endpoint_dataset` resources, so
  `export_context_slice(profile="dataset_brief")` round-trips endpoint
  `rdf:type`, `endpointDataset`, `endpointDirection`, `endpointRole`, and
  `endpointOrder` triples.
- A storage-aware query-planning strategy trial confirmed the happy path for
  local directory storage with a wildcard CSV template: the dataset can reach
  `ready_for_query_planning`, `draft_query_plan` can return
  `execution_attempt_ready`, an external Python CSV fallback can record a
  generic aggregate result with `record_query_result`, and observation/evidence
  seeded `deep_lore` context slices carry the result evidence while dataset
  slices stay focused on executable-catalog map facts. Scanner-clean preflights
  still require shareability review because local paths are preserved.
- A pytest timing pass showed the profile insight review export test was slow
  because current-work discovery, profile draft duplicate checks, and markdown
  rendering could all preview the same staged revisions. Those previews run
  SHACL, so repeated read-only checks are expensive. Profile insight review
  export now shares a scoped apply-check cache across those read-only phases;
  keep mutating apply paths on fresh previews.
- A profile apply-gate scratch trial staged an ordinary profile map update,
  metric vocabulary promotion, value-type promotion, map type assertion, and
  systematisation fallbacks from one mixed-support profile run. Every staged row
  was mechanically ready, but the profile insight bundle correctly reported
  `bulk_apply_allowed=false`, no safe-single candidates, and role-separated
  semantic candidates. Use the semantic apply-gate fields, not
  `check_staged_revision_apply().status`, `apply_after_review`, closed semantic
  moves, or changed graph roles, to decide whether unattended apply is allowed.
- A privacy/export handoff trial confirmed broad dirty handoff preflight blocks
  both graph terms and staged snapshot rows, while a clean context-slice export
  for the target remains usable. A local-only dirty handoff manifest can still
  be imported for recovery when `fail_on_sensitive=false`; the receiver sees the
  manifest block/shareability status, imports snapshot evidence to
  `history_plus_snapshot_rows`, follows the recovered session, and can apply the
  staged row with exact diff context. Do not reshare artifacts whose manifest
  still says `decision="block"` or shareability review is incomplete.
- A database-backed query-planning trial confirmed the repair loop from
  misplaced/root-only relation metadata to storage-access-owned relation
  identifier works: after staged repairs, `draft_query_plan` produced
  `handoff_kind="database_relation_handoff"` with a relation identifier and
  connection reference but no executable scan function, and
  `record_query_result` preserved an external relation handle as evidence.
  Evidence-seeded `resource_brief` slices preserve the source spans. Docs and a
  regression now make explicit that `scanned_source_paths` can carry a reviewed
  database relation handle such as `warehouse-prod:mart.orders`, not only a
  filesystem path.
- A project-brief frontier-selection trial confirmed the local unattended route
  is explicit enough when agents follow the structured fields. With low limits,
  hidden query/profile/non-tabular queues and omitted profile candidates surface
  through `frontier_status`, `health_tasks`, and expansion calls. Privacy and
  stale-seed safety gates keep `first_unattended_action` on
  `export_preflight(...)` and block mutation; a clean expanded frontier routes
  next to `plan_staged_revision_recovery(current_staged_work_only=True)`.
  `project_strategy` remains the separate guide for choosing the broader repo
  workflow axis after local safety/frontier work is clear.
- A mixed staged cold-receiver handoff trial found no runtime gap for a queue
  containing a stale/conflicted source, restaged successor, already-effective
  row, and ready alternative candidate. The receiver imported exact snapshot
  rows, recovered the source session, routed stale work through the current
  successor, kept the already-effective row informational, applied the ready
  successor, wrote applied-event snapshot rows, and updated original lineage to
  the applied event. A future regression can lock this combined scenario down,
  but current routing fields exposed the row-vs-target distinction clearly.
- An AIS fixture query-overlay trial found no new runtime gap: the reduced AIS
  fixture can be overlaid with reviewed storage/layout metadata, stale
  partition-link friction is surfaced and repairable, and the resulting DuckDB
  plan remains a reviewed external handoff rather than hidden DoxaBase query
  execution.
- A query-failure privacy/export trial showed broad project handoff preflight
  can block on unrelated dirty map content while an evidence-seeded
  `resource_brief` context slice for the recorded query failure is scanner-clean
  and importable. Seed scoped query-result exports from
  `record_query_result.evidence_iri`; keep treating scanner-clean slices as
  requiring shareability review.
- A repeated profile scalar-conflict trial found that, after applying one
  same-evidence row-count/nullable option, the sibling value could reappear as a
  default profile-map update and even look safe-single in a profile insight
  bundle. Drafting now remembers current-equal scalar conflict siblings, skips
  unattended sibling replacement staging, and treats
  `profile_scalar_conflict_review` as semantic apply-gate context.
- A profile joint-writes trial confirmed that full-scan profile map drift,
  project metric vocabulary, type-review advisories, caveat alternatives, and
  sampled profile evidence can be kept separate through staged review. The main
  friction was executor ergonomics: agents had to combine several apply-gate
  fields to decide what to do next. Profile insight bundles now include
  `executor_decision_summary` as the compact first-pass routing object.
- A staged version/handoff trial confirmed recovery-complete import, exact graph
  version browsing, resource timelines, lineage inspection, stale/no-op routing,
  and semantic alternative gating work across capsules. The post-import manifest
  recovery plan is intentionally broad, so cold receivers should rerun
  `plan_staged_revision_recovery(current_staged_work_only=True)` before
  choosing a live mutation.
- A storage-aware query handoff trial confirmed the database path from missing
  metadata through staged `rc:DatabaseStorage` and `rc:SQLiteTable` repairs to a
  non-executed `database_relation_handoff`, external SQLite result recording,
  evidence source spans, scanned relation handles, and scanner-clean context
  exports. The safe loop is two-stage when storage and layout are both missing:
  apply reviewed storage, rerun context, apply reviewed layout, then draft.
- A frontier-routing trial on the active capsule found `project_brief` chose the
  right immediate order: stale-seed export preflight, hidden-frontier expansion,
  then query/profile inspection. The remaining trap was broad query-repair
  looping in stale/reduced AIS or Polymarket capsules where fixture tables exist
  but `storage_accesses` is zero. `project_brief.health_tasks[]` now surfaces
  `query_fixture_staleness_review` with fixture names, table IRIs, storage
  access count, and a representative `describe_query_context` action before
  agents stage repeated missing-storage repairs.
- MCP onboarding, privacy-scoped handoff, and awkward systematisation/pattern
  promotion trials in the same wave found no core runtime gap. Exact dotted MCP
  discovery worked for a cold subagent; broad handoff preflight blocked
  snapshot-only fake-sensitive staged content while a clean context slice stayed
  importable; grouped systematisation exports preserved shared-context warnings
  and choose-one semantics.
- A profile/query interlock trial confirmed `draft_profile_map_updates` puts
  `query_context_review` ahead of profile map updates when storage is missing,
  and `executor_decision_summary` blocks bulk apply while that lane is open. The
  concrete friction was that dedicated storage/layout query repair helpers could
  not persist the profile route source, so a staged repair was only supporting
  context until applied and rerun. `stage_query_storage_access_repair` and
  `stage_query_physical_layout_repair` now accept `profile_route_sources`; pass
  `profile_route_sources=[query_action.source_query_context]` from the draft
  action so profile insight bundles can mark the repair as a direct
  `query_context_review` action.
- A stale-seed recovery handoff trial confirmed the safety-first route works:
  stale source `project_brief` routes to scanner-clean handoff preflight/export,
  a fresh receiver imports the manifest plus snapshot rows, and receiver-local
  `project_brief` / `plan_staged_revision_recovery(current_staged_work_only=True)`
  expose the staged frontier without source-local state.
- A recovery-session handoff trial confirmed the receiver can continue from a
  persisted `start_staged_revision_recovery_session` after import and after one
  mutation. `describe_staged_revision_recovery_session` recomputed
  completed/active source lists, `mutation_frontier_items`, and recheck
  warnings after the apply. Continue to prefer `mutation_frontier_items` over
  `mutation_frontier_iris` alone, because repair/helper lanes may not have a
  concrete staged target IRI yet.
- A recovered-frontier trial on the active capsule confirmed stale-seed recovery
  drops the seed safety gate in the fresh receiver. The receiver brief moved to
  query/profile frontier work, retained `query_fixture_staleness_review` for the
  reduced AIS/Polymarket storage state, and explicit `revision_iris=[]` recovery
  planning returned a harmless empty no-frontier plan.
- A Polymarket query-handoff trial showed `pm:Trades` can reach a credible
  non-executed DuckDB `read_parquet` handoff from fixture metadata, but an honest
  manifest-derived overlay should remain review-blocked by
  `layout_needs_verification` and required `{date,hour}` bindings. Do not mark
  fixture paths `VerifiedByListingLayout` or `VerifiedByQueryLayout` without real
  listing/query evidence; record blocked handoff evidence instead.
- A positive profile apply/rerun trial confirmed the safe ordinary path:
  one full-scan profile map update produced one
  `safe_single_apply_candidate_revision_iris`, the ready apply check allowed one
  reviewed mutation, rerunning the draft closed the current profile-review lane,
  and applied-source exports/context slices still recovered the review trail.
  Unattended scripts should require safe-list cardinality plus a ready apply
  check before applying even when the decision label says bulk apply.
- A four-trial broad workflow wave found repeated friction in history-bearing
  context-slice handoffs: query-evidence overlays, controlled graph replacement,
  and non-tabular deep-lore slices imported into fresh receivers but failed
  `validate_graph(scope="all")` when selected `history` triples referenced
  partial `rc:GraphPatch` or `rc:GraphSnapshot` resources. Context-slice export
  now adds the direct patch/snapshot/validation-result triples needed for
  receiver validation and scans that closure, while still warning that SQLite
  revision snapshot rows are absent and `export_handoff_bundle` is required for
  exact recovery.
- A follow-up profile/query/staged/privacy wave found profile-frontier and
  staged rebase/version flows handled broad workflows without repo changes. The
  query-frontier run confirmed fixture staleness is visible but still advisory
  when full frontier expansion is pending, so agents must read
  `health_tasks[]` before staging repeated fixture storage repairs. The privacy
  handoff run exposed one real defect: recovery-complete handoff manifests can
  include ordinary non-staged `rc:GraphRevision` snapshot rows. Import now keeps
  those rows as informational recovery lanes instead of sending them through
  staged-patch restage/apply planning.
- A confirmation wave after the non-staged handoff fix found no new repo change.
  Active stale-seed handoff from the local capsule exported zero revision rows
  and a fresh receiver moved past seed recovery to query/profile frontier work.
  Mixed graph-version maintenance handoffs preserved ordinary revision
  snapshots as informational while leaving one current staged patch actionable.
  Storage/query/profile and awkward systematisation trials both round-tripped
  cleanly, preserving reviewed source handles, profile evidence links,
  semantic alternatives, and apply-one-then-recheck gates without inventing
  secrets or collapsing ambiguous lore into one template.
- A subsequent broad wave confirmed the stale-seed recovery path works end to
  end but exposed one automation gap: empty-revision
  `import_handoff_bundle()` imports succeeded with no staged recovery lanes and
  no structured next call. Empty handoff imports now return `project_brief()` as
  the post-import follow-up so a receiver can resume safety/frontier routing
  without relying on prose memory. The same wave found storage/query,
  profile/systematisation, and staged handoff/privacy flows broadly passing;
  remaining profile apply-gate and mixed-plan display frictions are semantic
  workflow candidates for later trials rather than this narrow import fix.
- A follow-up wave turned three of those frictions into additive routing
  metadata. Staged recovery lanes now expose `effective_recovery_action` so
  agents can prefer the route over batch-restage classifier provenance such as
  `skipped_not_restageable`. Query repair tasks affected by known fixture
  staleness now carry `task_advisories` and `task_group` metadata instead of
  relying only on `health_tasks[]`. Profile insight bundles can mark one ready
  full-scan map update as a safe single even when metric/type/fallback lanes
  remain open, while scalar conflicts, query blockers, and already-applied rows
  remain blocked.
- A handoff/export recovery trial confirmed manifest import, recovery-session
  continuation, route-source preservation, apply-one-then-restage, and receiver
  validation all work end to end, but the PASS/FAIL proof required stitching
  together import, snapshot evidence, session, plan, and restage responses.
  `import_handoff_bundle().recovery_summary` now gives unattended agents the
  compact smoke-check fields first: snapshot completeness, matching sessions,
  lane/queue counts, mutation frontier, preserved profile route keys, and the
  first suggested next action.
- A project-brief frontier trial confirmed `first_unattended_action` correctly
  routes stale-seed capsules to handoff preflight before hidden frontier or
  query/profile work. Because `export_preflight` is stateless, read-only agents
  should report recovery-complete handoff required after a clean stale-seed
  preflight instead of rerunning it or polishing visible queues. A paired
  context-slice import trial showed history-bearing slices validate in fresh
  receivers but still lack exact SQLite snapshot rows until the companion JSON
  is imported; `import_trig` now surfaces bounded
  `post_import_snapshot_evidence` and promoted import-recovery actions so the
  receiver does not need to know to call `describe_revision_snapshot_evidence`
  immediately after every history import.
- A four-trial workflow wave retested that TriG import affordance, staged
  same-slot conflict recovery, privacy/export gates, and profile-to-query
  follow-through. All passed, but each exposed small unattended routing gaps:
  snapshot-missing imports need to say when to request a recovery-complete
  handoff bundle, mechanically ready semantic alternatives need a direct
  mutation-frontier review flag, blocked context-slice preflights should not
  suggest a doomed write action, and profile query-bridge lanes depend on some
  existing physical-query cue such as a path template or layout.
- A storage/query trial then found a subtler candidate-selection gap: when a
  file route has multiple direct-ready candidates, automatic ranking can choose
  the storage-access route while a dataset or partition route is also ready.
  Query decisions, draft source context, and handoff summaries now expose
  `selection_reason_codes`, `peer_ready_requires_intent_review`, and
  `selection_caution` so unattended agents can distinguish precedence from
  project intent and pass `candidate_index` deliberately.
- A meaning-first retrieval trial seeded a scratch capsule with lore split
  across map caveats, observations, evidence, patterns, ontology, shapes, and
  staged proposals. Cold agents could recover the answer once they found a seed,
  and `dataset_brief` / `pattern_brief` preserved the support chain well. The
  weak point was the first no-hit natural-language search: terms such as
  "inland" and "water-level adjustment" did not bridge to stored wording such
  as "landward" and "phase-normalized tide correction." Empty `search()`
  results now return bounded recovery actions for shorter scoped searches, map
  entity browsing, and current staged-payload search instead of leaving agents
  at an empty dead end.
- A rich transform/grain trial over non-tabular sonar/image assets confirmed
  `record_map_dataset(is_table=False)` and ordered relationship endpoints can
  model asset lineage without fake columns, and dataset/deep-lore slices recover
  supporting observations, patterns, and staged anchors. It also found helper
  validation lag: project-specific `derivation_properties` could be written even
  though SHACL only accepts `rc:Deterministic`, `rc:Invertible`, and `rc:Lossy`;
  the map helper now rejects those upfront. The follow-up
  `record_map_asset_transform` helper now covers reviewed transform conditions,
  per-output formulas/functions, and tuple grain without fake columns; future
  trials should test whether this is enough for awkward non-tabular and
  mixed-asset workflow handoffs before adding more shape-specific fields. A
  follow-up smoke trial using MCP-callable Python wrappers on a scratch capsule
  passed for non-tabular aggregation assets with ordered endpoints, a selection
  condition, output formula/function, tuple grain, `describe_dataset`, context
  slicing, and SHACL validation; the only observed friction was response-shape
  convention clarity, now noted in `response-shapes.md`.
- Three broad staged-revision trials passed for conflict/drift recovery,
  cold version browsing after apply, and recovery-complete handoff import/apply.
  The mechanics were sound: recovery planning routed stale rows to restage,
  handoff bundles preserved exact snapshot evidence, and revision/version
  helpers reconstructed applied diffs and resource lineage. The remaining
  friction was cold-agent affordance: scripts guessed mutation-frontier keys,
  direct Python callers needed `to_jsonable()` guidance, and handoff imports
  put recovery-session suggestions ahead of the simple apply action. Response
  docs now show a serialized `mutation_frontier_items[]` example, revision docs
  include a cold version-browsing recipe, and handoff import summaries expose
  `first_safe_review_or_mutation_action` separately from session suggestions.
- Profile, storage-query, and onboarding trials after that passed across
  scratch capsules and the active capsule. Cold agents could complete
  full-scan/sampled profile review lanes, storage/layout repair to a query
  handoff, query-result evidence capture, privacy preflights, and
  project-strategy routing away from staged-only polish. The useful frictions
  were affordance-level: profile follow-through needed top-level
  `missing_binding_keys`, profile review exports needed clearer strict-filter
  documentation, and query repair docs needed a compact reminder that
  `suggested_repair_action_groups` is the metadata mutation lane even when
  `suggested_next_actions` also exposes review-gated `draft_query_plan`.
- Follow-up mixed-asset, query-overlay/privacy, and profile-export trials
  passed. Non-tabular transform/grain handoffs preserved tuple grain through
  describe/context-slice/export/import and kept query planning
  `not_applicable_non_tabular_asset`; profile follow-through/export strict
  filtering worked after the binding-key change. The query-overlay trial found
  a real gap: blocked query-result evidence can carry reviewed source handles
  without profile rows. `draft_query_evidence_storage_overlay` now accepts
  linked ordinary query evidence and exposes `source_query_evidence` while
  retaining `source_profile_evidence` as a compatibility alias.
- Active-frontier trials confirmed the stale-seed handoff and fixture-staleness
  guards are working. A scanner-clean recovery-complete handoff from the active
  capsule imported into a fresh receiver, cleared `seed_recovery_review`, and
  routed to query/profile frontier work. A fresh fixture load removed
  `query_fixture_staleness_review` once storage metadata existed; Polymarket
  reached query-plan handoff, while AIS DailyIndex still stayed
  `needs_review` for its intentional inherited broadcast-layout gap. A timing
  trial found no container CPU/memory cap and no test-performance code change
  worth making: `-n auto` remained the fastest local full-suite gate.
- Awkward systematisation/pattern-promotion and assertion-cleanup trials passed
  end to end on scratch capsules, including cold readonly reopen, grouped
  review export, apply checks, and stale same-slot replacement repair. The
  useful product signal was response-shape affordance, not broken mechanics:
  systematisation drafts now expose top-level `choose_one_groups`, and
  assertion route summaries expose `relevance_tier` / `generic_value_only` so
  generic controlled values such as `rc:SnapshotRow` do not look like strong
  resource-specific support.
- A scoped privacy/export trial confirmed broad graph and recovery-complete
  exports still block on unrelated sensitive-looking graph siblings while a
  clean resource-scoped `preflight_context_slice_export` /
  `export_context_slice` path can stay scanner-clean, review-gated, importable,
  and SHACL-valid in a fresh receiver. Keep using context-slice exports for
  clean resource neighborhoods instead of weakening `fail_on_sensitive` on
  broader exports.
- Conflict/rebase/version, profile-followthrough, and storage-aware query
  trials passed on scratch capsules. The latest small fixes are response
  affordances: `stage_systematisation` / `stage_pattern_promotion` staged rows
  now carry `framing_index` and `framing_label`, and
  `record_dataset_profile` can reuse an explicit `evidence_iri` through the MCP
  wrapper. A follow-up route-intent trial found `candidate_index` was too
  brittle for unattended reruns when one storage access or dataset produced
  several candidate paths. Query target cards and generated draft actions now
  carry `candidate_selector`, a stable selector over the candidate's modeled
  template/source/storage identity. The larger remaining storage-query design
  issue is durable route intent: a local sample route can still outrank the
  intended production database route unless the caller chooses a selector or
  storage access deliberately. A later route-intent pass added storage-access
  `route_roles`, so agents should now inspect those reviewed roles and pass an
  explicit `candidate_selector` in ambiguous multi-route capsules.
- A broad query-result, MCP-parity, lineage, and profile-systematisation wave
  passed on scratch capsules. Polymarket query planning could reach a reviewed
  DuckDB handoff and correctly record a blocked result when fixture data was not
  bundled; dataset context slices now reverse-follow recent ordinary
  `rc:observedAsset` observations so blocked/failed query-result evidence is
  recoverable from the dataset seed. MCP runtime parity was sound when launched
  from the repo cwd or with `PYTHONPATH` and an absolute capsule path. Revision
  lineage inspection was sufficient for stale/restaged/applied chains, but
  lineage queue items now carry `alternative_set_*` fields so choose-one source
  and alternative rows do not require a separate list/export join. The
  profile-systematisation trial confirmed that review bundles correctly leave
  lanes open when a caller-authored combined value-type definition and map
  assertion omits one of the matching `profile_route_sources`; carry both
  `define_value_type` and `assert_map_type` route sources when one staged framing
  intentionally closes both moves.
- A cold handoff receiver and project-brief frontier wave passed without code
  changes: recovery-complete handoff import, stale/restaged/applied lineage,
  grouped choose-one exports, safety-first `project_brief`, low-limit broadening,
  privacy preflight blocks, staged recovery, query repair, and profile advisory
  lanes all routed a cold unattended agent to safe next actions. The route-intent
  pressure trial exposed the concrete remaining storage-query gap: mechanically
  ready candidates could not tell a cold agent which route was production-current
  versus sample/archive/backfill. Storage access records now accept `route_roles`
  such as `rc:ProductionRoute`, `rc:CurrentRoute`, `rc:SampleRoute`,
  `rc:ArchiveRoute`, `rc:BackfillRoute`, and `rc:CanonicalRoute`; query target
  candidates inherit those role summaries for reviewed `candidate_selector`
  selection without changing automatic precedence.
- Route-role, profile-followthrough, and mixed staged-revision trials passed on
  scratch capsules. Route roles were sufficient for a cold agent to choose the
  intended production/current/canonical database route, but database relation
  handoffs should be read as runtime-resolution work rather than missing DuckDB
  file-scan inference. Mixed staged-revision recovery showed that executors need
  choose-one context on `mutation_frontier_items`, not only
  `next_action_queue_items`; frontier revision-target items now copy grouped
  semantic-risk and alternative-set fields. The profile-followthrough trial
  completed full-scan/sample/advisory lanes and safe map apply; direct
  `stage_profile_map_updates` results now expose the same top-level
  `revision_iri` alias as the MCP wrapper for staged and all-skipped outcomes.
- A follow-up four-trial wave covered storage query followthrough,
  project-brief/privacy frontier routing, staged-revision alternative recovery,
  and profile review-bundle handoff. Storage query planning still should not
  change automatic precedence, but when precedence skips ready
  production/current/canonical route roles the decision now exposes
  `route_intent_review_candidate_indexes` / `route_intent_caution` so a cold
  agent can select the intended `candidate_selector`. Staged recovery now carries
  applied-source alternative IRIs on `mutation_frontier_items`, so scripts using
  the mutation worklist can see both the semantic-review gate and the already
  applied competing source. Profile handoff held after the alias fix. Remaining
  lower-priority affordances to retest later include a possible
  `scanned_source_handles` naming alias for query results, a `safety_gate` flag
  on project-brief health tasks, and suggested scrub/review actions for blocked
  context-slice preflights.
- The next broad wave retested those fixes against harder context. Project brief
  is steering well: privacy-bearing capsules still route first to
  `export_preflight`, while clean low-limit briefs prefer full frontier
  expansion before staged/profile/query mutation. Two workflow gaps remained and
  were fixed. Route intent now uses direct-clean peers when a broken sibling
  makes the whole query context review-required, so production/current/canonical
  intent stays visible even when `ready_candidate_indexes` is empty. Blocked
  `preflight_context_slice_export` responses now include read-only recovery
  actions instead of an empty action list. Staged helper-action frontier items
  also carry applied-source alternative context, so an executor can explain the
  semantic gate before staging a repair successor.
- A four-agent broad wave over staged semantic recovery, profile-to-map
  promotion, storage-metadata query planning, and post-safety frontier routing
  found no broken core workflow. Staged recovery separated mechanical restage
  from semantic same-slot repair and preserved applied-alternative context;
  profile-to-map preserved semantic judgement across full-scan, sampled, metric,
  and type-review lanes; and project brief could resume safely after privacy
  review using existing `frontier_first_action` / `must_rerun_call` cues. The
  concrete query-planning friction was terminology: database relation handles
  worked through `scanned_source_paths`, but that name made cold agents infer a
  filesystem-only field. `record_query_result` now accepts the preferred
  `scanned_source_handles` alias, returns both names, and exposes the alias in
  downstream query-context evidence previews. Docs now state that post-safety
  frontier resumption is read-only until `mutation_allowed_after` clears.
- A follow-up profile/version/query/privacy wave kept the same broad workflows
  under pressure. Privacy/frontier routing and `scanned_source_handles`
  downstream previews held. The highest-priority gap was staged-version
  navigation: `describe_graph_version_diff` explained count/triple deltas but
  not the staged/applied/restaged lineage, so a zero staged-before/current diff
  could hide a ready or semantically gated staged row. Graph-version diffs now
  include compact before/after revision contexts, `related_revision_iris`, and
  suggested lineage/applied-diff follow-ups. A follow-up profile patch addressed
  the sampled-profile caution: drafts, profile review bundles, candidates,
  executor summaries, and Markdown apply-gate tables now surface profile basis
  counts, sampled default-stageable indexes, sample scopes/methods, and
  sampled-evidence caution. Remaining useful affordances for later waves: route
  cards on query-planning peer actions, partition binding examples, and clearer
  validation behavior when query-evidence storage overlays reuse existing
  storage/layout IRIs.
- The storage-metadata query-planning follow-up addressed the route-card and
  partition-binding affordances from that wave. `describe_query_context`
  `draft_query_plan` actions now carry `route_card` with the candidate selector,
  storage label, route roles, path/relation handles, direct issue codes,
  required bindings, and illustrative partition binding examples; layout
  selection actions mirror the reviewed `physical_layout_iri` in the same card.
  Use those fields instead of parsing action prose when choosing production,
  sample, archive, peer, or layout-specific routes. A direct overlay validation
  trial then confirmed that reusing existing `storage_access_iri` or
  `physical_layout_iri` could leave old verification status/note triples in
  place and fail max-count SHACL checks. `draft_query_evidence_storage_overlay`
  now removes replaced verification status/note values from reused dataset,
  storage access, and physical layout resources before staging. A sampled-profile
  caution trial then found the dedicated profile review bundle guarded sampled
  evidence correctly, but the generic staged Markdown did not repeat that caution;
  `export_staged_revisions()` now renders sampled evidence cautions in its
  Profile Route Bridge. A staged recovery scout then found that batch restage
  was clear at the item level but awkward for top-level-action-only executors.
  Batch restage responses now expose top-level `suggested_next_actions`: dry
  runs promote the reviewed real batch restage call for
  `would_restage_revision_iris`, while real batches promote deduped item-local
  continuation actions for current successors.
- A profile-to-query bridge trial confirmed that full profile insight bundles
  correctly close query-context repair lanes, but generic staged exports lost
  sampled evidence cautions for storage/layout repairs staged from
  `query_action.source_query_context`. Query-context route sources now carry
  the draft profile quality summary and sampled-evidence caution, so generic
  Profile Route Bridge rows warn about sampled profile scope for those repairs
  too.

Use later trials to check whether these gaps still matter after each change.
If a gap stops being useful, revise this section.
