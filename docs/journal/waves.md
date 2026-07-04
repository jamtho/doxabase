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
