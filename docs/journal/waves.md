# Distillation Wave Journal

Working log for the V1 → V1.5 Distillation Program
(`doxabase_design_docs/07-distillation-program.md`). One entry per wave,
newest last, ≤ 15 lines each: what changed, measured scoreboard effect, next
item. Phase-gate reports (≤ 1 page) also live here. Nothing in `docs/journal/`
is MCP-registered or agent-reference material.

Historical note (once, per program item 0.6): the project was created as
"DoxyBase" (first commit, 2026-05-30) and renamed to "DoxaBase" early on. The
container path `/workspaces/doxybase` and the local capsule `.doxybase.sqlite`
keep the old spelling; tracked files should use DoxaBase / doxabase.

## Wave 1 — 2026-07-04 — Phase 0: freeze and instrument

- Adopted docs 06/07 as active direction (commit on `codex/distillation-program`).
- Built `tools/scoreboard.py` (BUDGETS dict, `--check`) and `tests/test_budgets.py`;
  initial ceilings = 2026-07-04 actuals +≤5%. All green at baseline.
- Baseline actuals: 89 tools / 138,353 schema chars; core.py 74,667 lines;
  test_doxabase_core.py 44,285 lines; project_brief 100,462 chars;
  context slice (DailyIndex, defaults) 168,598; docs/agent 1,484,446 bytes.
- Deviations from doc 07 measured values (different seeds; ours are pinned in
  scoreboard.py): describe_dataset 30,023 not 43,005; slice 168,598 not
  260,768; list_entities 16,345 not 1,714 (limit=100 on map graph).
- Suite wall time and wheel-smoke are gate concerns (`tools/gate.sh`, Phase 1),
  not scoreboard metrics — recorded here as the intended small deviation.
- AGENTS.md now carries the Permanent Loop Rules; project-strategy.md axes
  suspended. Created `docs/journal/` (this file, `trials/`).
- External signal: `/tmp/enron-doxabase-handoff` still exists (review believed
  it deleted); copied to `/home/codex/enron-doxabase-handoff` for durability.
- Next: Phase 0.5 baseline trial battery, then Phase 1 packaging.

## Wave 2 — 2026-07-04 — Phase 0.5: baseline battery + Phase 1.6 stance

- Ran the Standard Trial Battery cold on the 89-tool surface with Sonnet
  sub-agents via a FastMCP-dispatch bridge (details + LATITUDE notes in
  `trials/2026-07-baseline.md`). All three tasks succeeded.
- Tokens-to-outcome: T1 ≈ 60k, T2 ≈ 154k, T3 ≈ 85k. Agents self-reported
  40–60% of received bytes as noise; two API traps found (record_pattern
  joint constraint invisible in schema; describe_query_context arg naming).
- ARCHITECTURE.md now records the single-writer/WAL-off concurrency stance
  (Phase 1.6): WAL sidecars would break one-file capsule handoff.
- RDFLib deprecations traced to rdflib 7.6.0 internals (Dataset.parse →
  default_context), not our call sites → Phase 1 pins rdflib <8 + filters.
- Scoreboard unchanged. Next: Phase 1 packaging (build-system, dev deps,
  entry point, gate.sh with wheel install smoke).

## Wave 3 — 2026-07-04 — Phase 1: make it shippable

- pyproject: hatchling build-system; version 0.2.0.dev0; pytest/xdist to dev
  group; pyarrow behind `doxabase[parquet]`; rdflib pinned <8 (deprecations
  are rdflib-internal; targeted pytest filters added); `doxabase-mcp` script.
- Runtime data ships as `doxabase/_data/` via force-include mirroring the
  repo layout; `core._data_root()` prefers it, so repo and wheel resolve
  identically. `mcp_tools._resolve_path` now resolves user paths against cwd
  (was repo ROOT) — 2 tests updated from ROOT-monkeypatch to chdir.
- tools/gate.sh = full gate incl. `uv build` + clean-venv install smoke
  (tools/install_smoke.py; smoke needed evidence on its observation — shapes
  require observations link evidence). `.github/workflows/ci.yml` runs it.
- Gate 1 PASSED: smoke loads 805 triples from packaged `_data`, 89 tools.
- Scoreboard unchanged. Next: Phase 2 monolith split.

## Wave 4 — 2026-07-04 — Phase 2: monolith split (zero behavior change)

- `doxabase/core.py` (74,667 lines) → `doxabase/core/` package: `_shared.py`
  (prelude), `_types.py` (all 244 dataclasses, 4.1k lines), and 32 mixin
  modules composing `DoxaBase` in `__init__.py`. Largest module now 4,903
  lines (staging.py). Every name re-exported; no import site changed.
- Split was script-generated (AST-based, methods verbatim): name-rule buckets
  + majority-caller attribution for private helpers. Deviation from 2.1: the
  decomposition table was iterated empirically against module-size reports
  rather than fixed before moving code; final layout is the module list in
  `doxabase/core/`. Splitter + original core.py preserved in session scratch.
- Two mechanical fixes the split exposed: `_data_root()`/test-header ROOT
  needed one more `parents[..]` level; runtime `DoxaBase._static(...)` and
  `object.__new__(DoxaBase)` references need the facade bound into mixin
  module globals post-composition (transitional loop in core/__init__.py —
  Phase 3/4 should rewrite those call sites and delete it).
- Tests: `test_doxabase_core.py` → `tests/core/` (15 files + support_core),
  `test_mcp_tools.py` → `tests/mcp/` (16 files + support_mcp), tests verbatim.
- Ceilings tightened: largest module and largest test module ≤ 5,000.
- Gate 2 PASSED: 764 passed, wheel smoke green, all budgets green.
- Next: Phase 3 token diet (to_jsonable envelope, RDF-first slices,
  project_brief diet, SuggestedNextAction collapse).

## Wave 5 — 2026-07-04 — Phase 3.1: envelope diet + doc 08 + journal extraction

- `to_jsonable` now omits None/[]/{} entries (absent==null==empty convention,
  documented in its docstring); hand-built envelopes in mcp_tools routed
  through it. ~90 tests/mcp envelope assertions updated by sub-agent under
  no-semantic-weakening rules; two judgement calls reviewed and accepted
  (handoff manifest comparison normalized through to_dict — the on-disk
  manifest keeps explicit nulls, it's a file format not a context payload;
  blanket per-task field-presence checks in the brief test removed).
- Scoreboard effect: project_brief 100,462→76,764; describe_dataset
  30,023→23,017; describe_query_context 31,454→24,259; context slice
  168,598→140,116. Ceilings ratcheted to actuals +≈5%.
- Phase 4.1 mapping committed early: doxabase_design_docs/08-mcp-surface-v2.md
  (89→25, all absorptions + trap fixes + wave order).
- Phase 6.1 partial: 4,600-line trial journal extracted from field-trials.md
  to docs/journal/trial-signals-history.md (4,995→401 lines).
- Phase 5.2 done early (zero-conflict while tests were being fixed):
  docs/agent/working-the-capsule.md written and registered.
- Session continuation doc: handoff/distillation-session-2026-07-04.md
  (includes the ProjectBrief v2 spec for the 3.3+5.1 rebuild).
- Gate green (764 passed + wheel smoke). Next: 3.2 RDF-first context graph.

## Wave 6 — 2026-07-04 — Phase 3.2: RDF-first context graph

- `describe_context_slice` → `get_context_graph` (design doc 02's name),
  renamed across code, tests, docs, examples. TriG on by default.
- Graph content no longer ships as JSON: ContextSlice.triples,
  dataset_contexts, pattern_contexts are marked `doxabase_internal` (a new
  field-metadata convention in to_jsonable) — Python callers (export path)
  keep them; MCP envelopes don't. Measured: same graph content = 86KB as
  JSON triples vs 13.6KB as TriG.
- Redundant include_trig suggestion-template args removed.
- Scoreboard: context_slice 140,116 → 44,366 chars (baseline was 168,598;
  3.8x down, end-state 32,000 within reach once routes shrink in 3.4).
  Ceiling ratcheted to 46,500. Gate green (764 passed + smoke).
- Next: 3.3+5.1 project_brief rebuild per spec in
  handoff/distillation-session-2026-07-04.md, then 3.4 collapse.

## Wave 7 — 2026-07-04 — response conventions doc; 3.4 attempt blocked

- docs/agent/response-conventions.md written and registered (the eventual
  replacement for response-shapes.md, which is retired in Phase 6): envelope
  rules, truncation family, suggestion semantics, error style, privacy
  posture. Deliberately key-name-loose on suggestions until 3.4 lands.
- Phase 3.4 (SuggestedNextAction collapse) was dispatched to a sub-agent
  which hit the account monthly spend limit before writing anything; the
  working tree stayed clean. Full implementation spec preserved in
  handoff/distillation-session-2026-07-04.md step 2b.
- Session likely ends here on budget. Next agent: read the handoff; the
  order is 3.4 → 3.3+5.1 brief rebuild → 3.5/3.6 → Phase 4 per doc 08.

## Wave 8 — 2026-07-04 — Phase 3.4: SuggestedNextAction collapsed

- One frozen dataclass (tool, args, reason) replaces the base + 10
  subclasses; ~184 construction sites rewritten (sub-agent execution, spec
  in the handoff; independently re-gated before landing). All display-string
  fields (suggested_next_calls and the ~30 *_call variants), route-summary
  mirrors, and unattended-recommendation indexes deleted; load-bearing
  caution/placeholder text folded into reason. Net −4,247 lines.
- Structural judgement call (reviewed, accepted): profile route-source
  ride-alongs now travel only as a real staging-tool argument
  (args["profile_route_sources"]); insight-bundle lanes reconstruct live
  sources from state.
- One whole test deleted with its helper (mixed-support review grouping);
  everything else 763 passed + 1 skipped.
- Scoreboard: project_brief 76,764 → 28,035 (baseline 100,462);
  describe_query_context 24,259 → 20,601; slice 44,366 → 44,053; largest
  module 4,903 → 4,817. Ceilings ratcheted.
- ≤5 suggestion cap deferred (no clean choke point; ~70 builder sites) —
  fold into the 3.3+5.1 brief rebuild for the brief itself and revisit
  globally in Phase 4's per-family merges.
- response-conventions.md now states the exact tool/args/reason shape.
- Next: 3.3+5.1 project_brief rebuild (spec in handoff step 3).

## Wave 9 — 2026-07-04/05 — Phases 3.3 + 5.1: project_brief is state, not script

- ProjectBrief rebuilt as the v2 shape from the handoff spec: key_counts,
  dataset_count, dataset one-liners (iri/label/is_table/status/column_count/
  caveat_count), gates (gate/blocks/detail/details_call), queues
  (name/count/example_iri), ≤5 deduped suggestions, limit. DELETED: the
  safety/frontier/unattended lanes, frontier_status + mutation_allowed_after,
  expansion machinery, returned/omitted count triplets, per-dataset inlined
  query/profile summaries, profile_candidate_limit parameter.
- Gates derive from the proven health builders: stale_seed_recovery
  (mutation), staged_revision_recovery (mutation, from overlapping recovery
  sessions), privacy_export_review (export), export_validation_review
  (export), query_fixture_staleness (none). Gate actions lead suggestions.
- Recorded deviation: 3.3 and 5.1 executed as one rebuild (same code/tests);
  internal derivations still call describe_dataset per dataset — the cost
  center was inlined content, not compute; simplify later if profiling says.
- brief.py 2,880 → 2,146 lines. Tests: 36 old core-brief machinery tests
  deleted, 9 v2 tests written (all gate conditions covered incl. ordering
  and clearing); mcp brief file rewritten (3 envelope tests); 11 scattered
  assertions across recovery/restage/staging/query/map/profiles rewritten
  to gates/queues semantics. Suite: 726 passed.
- Scoreboard: project_brief 28,035 → 4,592 chars — under the 8,000 end-state
  (baseline 100,462: a 22x reduction). Ceiling ratcheted to 4,850.
- Next: 5.3 start-here rewrite (now truthful), then 3.5/3.6 + Gate 3 battery.

## Wave 10 — 2026-07-05 — Phase 5.3: start-here rewritten

- start-here.md: 346 → 69 lines, written fresh against the v2 surface:
  what DoxaBase is, five first calls, gates posture, graph placement cheat
  sheet, recording rules (incl. the record_pattern joint constraint),
  topic-doc pointers. No timing diaries, no routing chains.
- Content test rewritten to assert the on-ramp properties (≤120 lines,
  first calls present, no dated journal material). start_here_lines
  ceiling ratcheted 350 → 120.
- Next: Phase 4 tool consolidation per doc 08 (wave R1: reads).

## Wave 11 — 2026-07-05 — Phase 4 wave R1: read-family merges (89 → 83 tools)

- Per doc 08 rows 1/5/6: list_docs → get_doc (no-arg lists); staged-patch
  search → search(scope="staged_patches"); describe_pattern /
  describe_analysis_view / describe_profile_run / describe_assertion_support
  → describe_resource with aspect (auto type-detects patterns and analysis
  views; profile_run takes evidence_iri; assertion_support takes predicate
  with iri as subject). Old tools deleted same-wave, no aliases.
- Every core suggestion emitter migrated to the merged names; the tricky
  finds (by the reconciliation sub-agent): find_exact_action matching in
  revisions (now matches args aspect), string-based add_action helpers,
  and three arg-dict shapes my first sweep missed. Lesson recorded: batch
  regex over tests lost to per-site edits — the sub-agent's precise pass
  fixed what my regex over-matched.
- Suite 726 passed; gate + wheel smoke green; ceilings ratcheted to
  83 tools / 142,000 schema chars.
- Next: wave R2, recording family (rows 10/13/14, −22 tools) via the
  kind-dispatch pattern with targeted per-kind validation errors.

## Wave 12 — 2026-07-05 — Phase 4 wave R2: recording family (83 → 65 tools)

- Doc 08 rows 10/13/14. New `record_profile` (kinds: dataset/column/bundle/
  domain_network) and `record_map_fact` (14 kinds incl. analysis_packet,
  profile_manifest, profiled_parquet_table); `record_observation` gained
  kind= (claim/query_result dispatch via spec; observation/profile keep the
  flat ergonomic fields). Twenty registrations deleted same-wave.
- Mechanism: a generic `_dispatch_kind` validates spec against the handler
  signature and raises targeted errors naming the valid and missing fields
  for that kind — the trial-trap fix pattern from doc 08, tested behaviorally
  (the sampled-snapshot gate test now asserts the error names the field).
- The old `*_tool` functions survive as dispatch targets and for Python-side
  tests; only the MCP doors merged. Repair-hint arguments_templates in
  query_repair now emit {"kind": ..., "spec": {...}}.
- Schema cost: 135,986 → 81,816 chars (the fattest schemas were all here).
  Ceilings ratcheted: 65 tools / 86,000 chars. Suite 726 passed; gate green.
- Next: R3 staging family (rows 16–19, −13), R4 revisions reads (rows
  20–21, −9), R5 export/import (rows 22–24, −12), sweep (row 8 fold +
  removals + docstring budget).

## Wave 13 — 2026-07-04 — Phase 4 wave R3: staging family (65 → 48 tools)

- Doc 08 rows 16–19. New `stage_revision` (kinds: graph/map_assertion/
  systematisation/pattern_promotion/profile_map_updates/query_storage_
  access_repair/query_physical_layout_repair/review_decision; dry_run=True
  keeps the draft response shapes for map_assertion, profile_map_updates —
  followthrough spec fields switch to the followthrough plan —
  systematisation rerun, and dry-run-only query_evidence_overlay).
  `apply_staged_revision` dry_run=True is the apply check;
  `restage_staged_revision` takes revision_iris str|list (str+dry_run=True
  is the rebase draft, list+dry_run the batch preview);
  `plan_staged_revision_recovery` gained start_session=/session_iri= modes.
  Eighteen registrations deleted same-wave; count 48 (doc 08's "−13"
  estimate was miscounted — the rows enumerate 18 absorptions + 1 new door).
- Effect classification became args-aware (staged_action_effect_metadata,
  staged_rebase_draft_action, stage_revision_action_kind/spec); fixed
  _revision_next_action_resolved_target_iri to also read string
  revision_iris so restage targets keep resolving. Suite 726 passed;
  gate green; schema 50,543 chars (≤ 86,000 ceiling, untouched).
- Next: R4 revisions reads (rows 20–21), then R5 export/import, then sweep.

## Wave 14 — 2026-07-04 — Phase 4 wave R4: revisions reads (48 → 39 tools)

- Doc 08 rows 20–21. New `list_revisions` (kind=graph/versions/resource;
  union params, kind-invalid params fail with targeted errors naming the
  kind's valid fields; include_apply_checks defaults True only for
  kind=resource, matching the old doors) and `describe_revision`
  (aspect=auto detects staged patch rows via record kind — explicit
  include_current_apply_check forces the staged door; aspects
  applied_diff/version_diff/lineage/resource_lineage/snapshot_evidence/
  graph_snapshot; version_diff reads iri as the before version and takes
  graph_role/after_revision_iri/compare_to_current; resource_lineage takes
  resource_iri; max_triples defaults 500 except resource_lineage's 100).
  Eleven registrations deleted same-wave; count 39; schema 45,849 chars.
- Matchers migrated aspect-aware: find_exact_action normalizes omitted
  aspect to 'auto'; new describe_revision_action_aspect helper; brief's
  two review_tool_order maps became one _staged_review_action_rank (the
  old staged-vs-graph describe rank distinction collapses to aspect=auto).
- Suite 729 passed (3 added targeted-error/auto-detect tests), gate green.

## Wave 15 — 2026-07-04 — Phase 4 wave R5: export/import (39 → 27 tools)

- Doc 08 rows 22–24. `export_preflight` gained kind= (renamed from
  export_kind on the MCP door only; scan_only absorbs the standalone
  scanner, context_slice the slice preflight; kind-invalid params fail
  with targeted errors). New `export_bundle(kind, spec)` (trig/graph/
  context_slice/staged_revisions — str|list revision_iris, grouped-only
  title/executive_summary — profile_insight_review/revision_snapshots/
  handoff) and `import_bundle(kind, spec)` (trig/revision_snapshots/
  handoff/example_fixtures with its scratch-capsule guard) dispatch
  through _dispatch_kind. Fourteen registrations deleted same-wave;
  count 27; schema 36,322 chars.
- Effect classification is now kind-aware (export_bundle writes files;
  import_bundle kinds mutate graph/history/storage; handoff dry_run is
  none); action_staging_arguments covers all kind/spec doors;
  recommended_import_tool strings became call-shaped and manifest
  import-sequence steps carry kind. Suite 732 passed (6 tests added
  across R4/R5), gate + wheel smoke green. Next: Phase 4 sweep (row 8
  fold, replace_graph_triples removal, docstring/schema budget pass).

## Wave 14 — 2026-07-05 — Phase 4 sweep: 25 tools

- draft_query_plan folded into describe_query_context(plan_candidate=
  "auto"|selector|index) with planning params valid only alongside it;
  replace_graph_triples left MCP (Python method survives; orphaned tool
  function deleted). Plan-drafting suggestions are describe_query_context
  actions with plan_candidate in args (_is_plan_action in _shared).
- 44 test reconciliations by sub-agent (plan filters strengthened to
  require plan_candidate so context vs plan assertions can't cross-match).
- **Phase 4 tool-count target reached: 89 → 25.** Suite 732 passed; gate
  green. Ceilings: 25 tools / 36,500 chars.
- Open item (escalated to James in doc 08): schema chars 35,136 vs 25,000
  end-state — the remainder is anyOf inflation on four flat recording
  tools; closing it needs the tail-params→spec structural decision.
- Next: Phase 3.6 response diets, then the Gate-3/4 battery rerun.
