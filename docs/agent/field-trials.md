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

When a trial changes MCP docs or tool registrations, remember that existing
Codex-bound MCP server sessions are long-running Python processes. They may keep
the old `agent_docs.DOCS` registry and decorated tool set until a fresh MCP
session starts. Cross-check with a fresh local Python process before treating a
stale `doxabase.list_docs` or missing tool as evidence that the commit failed.

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

For ongoing workflow-improvement work, prefer several trials over speculation.
After a useful trial, implement the sensible smallest justified fix, update
tests and docs, run focused and full verification, commit the coherent change,
and continue. Small fixes are preferred, but a larger change is appropriate when
that is the practical way out of a pathological state.

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
  `rc:Dataset`. Apply checks now use `broad_patch_object_overlap` for that weak
  case while preserving stronger object/anchor overlap labels. A validation
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
  `mapped_profiled_column_iris`.
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
  beside the live `validation_failed_revision_iris` queue.
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
  sibling candidate metadata. A follow-up binding trial showed that raw
  placeholders such as `{date}` were too detached from partition lore; draft
  plan binding rows now include partition scheme, likely partition column, and
  granularity hints when the selected template carries that metadata. A retest
  showed `draft_query_plan` was routeable enough through `handoff_kind` and
  `review_gate`, but `describe_query_context` needed a structured route into the
  documented allowance path; query contexts now include `suggested_next_actions`
  with explicit `candidate_index` and `allow_context_blocked_candidate=True`
  when a direct-clean candidate is blocked only by sibling context.
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

Use later trials to check whether these gaps still matter after each change.
If a gap stops being useful, revise this section.
