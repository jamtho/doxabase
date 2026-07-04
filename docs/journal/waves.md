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
