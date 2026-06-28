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

Do not rely on `uv run` inside sub-agent trials unless the trial is explicitly
testing the developer environment. Sandboxed agents may not have access to the
user's uv cache. If import paths are unclear, set:

```bash
PYTHONPATH="$(pwd)"
```

Create or replace a scratch capsule with `DoxaBase.create(path, overwrite=True)`.
Reopen an existing capsule with `DoxaBase(path)`. There is no `DoxaBase.open()`
helper in the current API.

When a trial changes MCP docs or tool registrations, remember that existing
Codex-bound MCP server sessions are long-running Python processes. They may keep
the old `agent_docs.DOCS` registry and decorated tool set until a fresh MCP
session starts. Cross-check with a fresh local Python process before treating a
stale `doxabase.list_docs` or missing tool as evidence that the commit failed.
Distinguish stale sessions from calls that never executed: `user cancelled MCP
tool call` and sandbox setup failures such as a `bwrap` namespace error are
execution-environment failures, not evidence that the DoxaBase MCP schema or
docs registry is old.

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

For a local query-result capture trial, create a tiny CSV or Parquet file under
`/tmp`, model it with `record_map_dataset`, `record_map_column`,
`record_map_storage_access`, and `record_map_physical_layout`, then call
`describe_query_context` and `draft_query_plan`. If
`review_gate.ready_for_execution_attempt` is true, execute a read-only local
count or aggregate with an external runtime such as DuckDB. If DuckDB is not
available, a small Python CSV reader is an acceptable fallback for the trial as
long as `engine` and `sample_method` say what actually ran. Record successful
and failed attempts with `record_query_result`; include `query_source_path`,
`query_hash`, and `result_sources` or a failure log so later agents can inspect
the evidence. Do not record profile count fields for failed attempts.

For a more adversarial staging trial, run:

```bash
./.venv/bin/python examples/adversarial-field-trial.py
```

It creates a scratch capsule and report under `/tmp`, records an uncertain
identity hunch as a claim and pattern, stages competing systematisations, and
expects one deliberately premature map candidate to fail validation.

Interleave ordinary polish loops with broader expeditions. Local API-friction
trials are good at improving response shapes, repair hints, and staged-review
routing, but they can underexplore project-wide product questions. Every few
loops, aim a wave at one or more of:

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
  redaction or proof that the graph is secret-free.
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
  content and full diagnostics on `describe_staged_revision`.
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
  agents know when to rerun with explicit `candidate_index`.
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
  while remaining out of the flat `suggested_next_actions` list.
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
  a `Snapshot Evidence` panel whenever included rows are not all fully recovered
  with exact snapshot rows. A batch-restage follow-up found scripts still had to
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
  panel is warning-oriented and can be absent when evidence is complete; use
  `describe_revision_snapshot_evidence` or JSON `snapshot_evidence` fields for
  positive script checks. Truncated column-seeded `deep_lore` slices can still
  answer subtle promotion questions through structured resources and route
  counts; they now expose `suggested_next_actions` that narrow to linked
  `pattern_brief` slices before offering a higher-`max_triples` raw RDF retry.
- Storage/query handoff trials found peer ready candidates were visible through
  index lists, but scripts still had to parse prose or storage-selector
  ambiguity errors to draft them. `describe_query_context.suggested_next_actions`
  now includes explicit `draft_query_plan(candidate_index=...)` actions for peer
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
  the explicit `candidate_index` and `allow_context_blocked_candidate` actions
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
  can see which draft route produced or motivated each staged row.
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

Use later trials to check whether these gaps still matter after each change.
If a gap stops being useful, revise this section.
