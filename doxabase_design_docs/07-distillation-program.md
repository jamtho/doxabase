# DoxaBase Distillation Program (V1 → V1.5)

**Date**: 2026-07-03.
**Commissioned by**: James, following the external design review in
`06-fresh-eyes-review-2026-07-03.md`. Read that review first; this program
exists to execute its conclusions.
**Audience**: the implementing agents (Codex, autonomous loop) and James.

**Authority**: until this program's exit criteria are met, this document
supersedes the build priorities in `docs/agent/project-strategy.md`,
`AGENTS.md`, `ARCHITECTURE.md`, and `README.md`. Where they conflict, this
document wins. The collaboration posture in `AGENTS.md` (surface tradeoffs,
raise concerns to the user, no silent workarounds) remains fully in force.

## How To Follow This Document

- Execute phases **in order**. Do not begin a phase before the previous
  phase's gate passes.
- Items marked **LATITUDE** allow implementation judgement within the stated
  constraint. Everything else is to be followed as written.
- If repository reality contradicts this document — an item is already done, a
  number here is stale, a budget is provably unreachable without losing a
  semantic guarantee — do not silently improvise and do not silently comply.
  Record the discrepancy in the wave journal, take the smallest deviation that
  preserves the item's intent, and flag it in the next phase-gate report. If
  the deviation is structural, stop and escalate to James.
- The Prime Directive and the Loop Rules apply from the first wave and remain
  in force permanently after the program ends.

## Why This Program Exists

Condensed from the review (doc 06):

1. The V1 design brief demanded a small, boring, drop-in library. The repo now
   has a 74,607-line single-file core, 96 public methods on one class, and 89
   MCP tools against a spec that suggested ~10.
2. The interface inverted: instead of curated RDF fragments, agents get
   bespoke JSON. A context slice of one table costs ~65k tokens with defaults;
   `project_brief` costs ~25k tokens on an 805-triple fixture.
3. The API increasingly scripts agent behavior (`first_unattended_action`,
   `mutation_allowed_after`, eight `SuggestedNextAction` subclasses), against
   the project thesis that agents supply judgement.
4. Reference docs have become archaeology: ~1.4 MB under `docs/agent/`,
   including a 4,900-line trial journal and pytest timing diaries.
5. The package cannot be installed (no `[build-system]`), has no CI, and has
   never been used outside its own fixtures.
6. Root cause: the improvement loop has no subtractive pressure and no budget
   metric a commit could regress. Every trial friction became a new field,
   tool, or doc paragraph. This program adds the missing counterweight.

## Prime Directive

**Distill, don't extend.** The goal state is the same capability at a small
fraction of today's surface and context cost. "Better" is measured, not
asserted: a fresh agent completes the standard trial tasks at equal or higher
success with materially fewer tokens.

For the duration of the program: **no new MCP tools, no new response fields,
no new agent-doc sections, no new helpers** — except where a phase item below
explicitly creates one. Bug fixes are allowed and follow the Loop Rules.

## The Scoreboard And Hard Budgets

Mechanics (built in Phase 0):

- `tools/scoreboard.py` computes every metric below and prints a table.
  A single `BUDGETS` dict at the top of that file is the only place ceilings
  are defined. `--check` exits non-zero on any violation.
- `tests/test_budgets.py` asserts the same ceilings via pytest so the ordinary
  gate catches regressions.
- Response-size metrics are `len(json.dumps(...))` in characters, measured on
  the **standard fixture capsule** (fresh capsule, both bundled TriG fixtures
  loaded, default arguments), so they are deterministic. Rule of thumb:
  4 chars ≈ 1 token, and JSON usually tokenizes worse, so ceilings are
  conservative.
- **Ratchet rule**: ceilings only ever move toward the end-state targets.
  Phase items say when to tighten them. Loosening any ceiling requires James.

| Metric | 2026-07-03 actual | End-state budget |
|---|---|---|
| MCP tool count | 89 | ≤ 25 |
| Sum of MCP tool description/schema chars | measure in Phase 0 | ≤ 25,000 |
| Largest module in `doxabase/` (lines) | 74,607 | ≤ 3,000 |
| Largest test module (lines) | 44,245 | ≤ 5,000 |
| `project_brief` response (chars) | 100,462 | ≤ 8,000 |
| `describe_dataset` response (chars) | 43,005 | ≤ 12,000 |
| `describe_query_context` response (chars) | 32,408 | ≤ 12,000 |
| Context slice, `dataset_brief`, defaults (chars) | 260,768 | ≤ 32,000 (TriG included) |
| `graph_overview` response (chars) | 14,187 | ≤ 8,000 |
| `search` (limit=20) response (chars) | 6,870 | ≤ 8,000 |
| `list_entities` response (chars) | 1,714 | ≤ 4,000 |
| `docs/agent/` total bytes (reference docs only) | ~1.4 MB | ≤ 150 KB |
| `start-here.md` lines | 345 | ≤ 120 |
| Full suite wall time (`-n 16`, current container) | ~57 s | ≤ 120 s |
| Wheel installs and runs in a clean venv | no | yes |

**LATITUDE**: public methods on the `DoxaBase` Python facade — target ≤ 60
(from 96) via the same family-folding as the MCP surface, but this is a soft
target: the Python API may stay somewhat richer than MCP where that genuinely
helps library users. The MCP cap is hard.

## Permanent Loop Rules

These amend the loop from wave one and survive the program. Phase 0 writes
them into `AGENTS.md`.

1. **Scoreboard gate.** The pre-commit gate is now:
   `uv run pytest -q -n 16`, `uv run python tools/validate_rdf.py`,
   `uv run python tools/scoreboard.py --check`, `git diff --check`.
   A scoreboard regression blocks the commit. Intentional budget changes
   require James.
2. **Wave shape.** Every wave: pick the next phase item → implement → full
   gate → wave-journal entry (≤ 15 lines: what changed, measured effect on the
   scoreboard, next item). Journal entries go in `docs/journal/waves.md`,
   never in reference docs.
3. **Subtraction quota.** During the program, every wave must leave the
   scoreboard net-equal-or-better. After the program: any wave that adds a
   tool, response field, or doc section must remove or shrink something
   comparable (one-in-one-out), and must first show that improving an existing
   field or doc could not close the same gap.
4. **Trials measure tokens-to-outcome.** A trial's primary metrics are
   (a) task success against its rubric and (b) total context cost: tool-schema
   chars + doc chars fetched + response chars consumed, ÷4. A fix that removes
   a confusion but raises cold-start cost is a regression.
5. **No compatibility shims.** Pre-1.0 with zero external users: delete old
   names outright — no aliases, no deprecation wrappers, no dual code paths.
   If an external user ever exists, James will say so explicitly.
6. **No new routing fields.** When a trial agent gets lost, the allowed fixes
   are, in order: better state presentation in an existing field; a rewritten
   doc sentence; a merged/simplified response. Adding a new field requires
   that it replace at least one old field.
7. **Docs are reference, never journal.** No dated entries, no timing
   measurements, no trial narratives, no "a later trial showed…" in
   `docs/agent/`. That material goes to `docs/journal/`.
8. **Escalate to James** (pause the loop, write a handoff): storage schema
   changes; `rc:` ontology semantic changes; any budget loosening; a phase
   gate failing twice; anything that would weaken privacy/validation/staged
   conflict guarantees; anything irreversible.

**Named anti-patterns** — self-check each wave; naming them makes them
visible in review:

- *The Additive Reflex*: fixing trial friction by adding rather than
  simplifying.
- *The Routing-Field Reflex*: encoding workflow decisions as response fields
  instead of presenting state.
- *The Doc-Append Reflex*: appending a clarifying paragraph instead of
  rewriting the section to be true now.
- *The Compat-Shim Reflex*: keeping old names "just in case."
- *The Self-Referential Trial*: validating only against fixtures and tests the
  loop itself wrote.
- *The Smallest-Fix Trap*: a local patch where the structure is the problem.

## What Not To Change

- The observation → pattern → systematisation model and its RDF vocabulary
  semantics: claims, evidence, source spans, reconsiderations
  (weakens/contradicts/supersedes/refines).
- Graph roles; immutable seed graphs; `ontology/rc_core.ttl` and
  `ontology/rc_shapes.ttl` content (typo-level fixes only).
- The SQLite storage schema (`named_graphs`, `quads`, snapshot tables, FTS),
  except where Phase 1 packaging requires path-resolution changes.
- Staged-revision semantics: staging, conservative conflict checks, row-level
  drift snapshots, apply/restage behavior. Their *surface* consolidates in
  Phase 4; their *guarantees* must not weaken.
- The privacy/export posture: scanner-clean is a review prompt, not export
  approval; preflight before shareable artifacts.
- Parse validation always; SHACL as explicit diagnostic, not commit gate.
- Test-before-commit discipline; rationale-focused commit messages authored as
  James with no AI attribution; `codex/...` branch workflow.

---

## Phase 0 — Freeze And Instrument

Goal: the loop cannot regress what it cannot measure. Estimated 1–2 waves.

- **0.1** Write `tools/scoreboard.py`: computes every table metric (tool count
  via introspecting `build_server()`; description chars from the FastMCP tool
  registry; module/test line counts; response sizes on a freshly built
  standard fixture capsule; docs byte totals; wheel-installability as a
  boolean read from the latest CI/gate artifact or skipped with a warning
  until Phase 1). `--check` mode enforces the `BUDGETS` dict. Initial ceilings
  = current actuals (rounded up ≤ 5%), so the ratchet starts immediately
  without failing.
- **0.2** Write `tests/test_budgets.py` asserting the same ceilings through
  the scoreboard's functions.
- **0.3** Amend `AGENTS.md`: replace the "Autonomous Trial Loop" section's
  additive posture with the Permanent Loop Rules and anti-pattern list above,
  and point to this document as the active program. Amend
  `docs/agent/project-strategy.md`: mark the three build axes **suspended
  until the Distillation Program exits**, and state that this doc governs.
- **0.4** Create `docs/journal/` (plain files, NOT registered in
  `doxabase/agent_docs.py`): `waves.md` for wave entries, `trials/` for trial
  reports. Reference docs stay where they are until Phase 6.
- **0.5** Baseline trials: run the Standard Trial Battery (defined below) once
  against the **current** surface, recording tokens-to-outcome per task in
  `docs/journal/trials/2026-07-baseline.md`. Every later phase gate compares
  against this baseline. Do not fix anything found; this wave only measures.
- **0.6** Hygiene: update `handoff/codex-upgrade-continuation-2026-07-03.md`
  status or supersede it with a pointer here; fix remaining `doxybase`
  spellings in tracked files; note the DoxyBase→DoxaBase rename once in
  `docs/journal/waves.md`.

**Gate 0**: scoreboard runs and `--check` passes at initial ceilings;
`tests/test_budgets.py` green in the full suite; `AGENTS.md` and
`project-strategy.md` amended; baseline trial report exists.

## Phase 1 — Make It Shippable

Goal: `pip install doxabase` works and CI holds the line. Estimated 1–2 waves.

- **1.1** Add `[build-system]` (hatchling). Package the runtime data: the
  ontology seeds, the agent docs, and the example fixtures must be importable
  resources (move them under the package or use build-config includes —
  **LATITUDE** on mechanism). Replace repo-root-relative `ROOT` path
  assumptions in `core.py`/`agent_docs.py`/`mcp_tools.py` with
  `importlib.resources`-based access so an installed wheel works outside the
  repo.
- **1.2** Dependency hygiene: move `pytest`/`pytest-xdist` to a dev dependency
  group; declare `pyarrow` as an optional extra (e.g. `doxabase[parquet]`);
  keep runtime deps to `mcp`, `rdflib`, `pyshacl`.
- **1.3** Add a console entry point `doxabase-mcp` for the stdio server.
- **1.4** CI: if `git remote -v` shows GitHub, add
  `.github/workflows/ci.yml`; otherwise add `tools/gate.sh` and run it as the
  local gate. Either way it runs: `uv sync`, full pytest, `validate_rdf.py`,
  `scoreboard.py --check`, `uv build`, then an **install smoke**: install the
  built wheel into a clean venv in a temp dir outside the repo and run a
  script that creates a capsule, loads the packaged fixtures, searches,
  records an observation, validates, and starts the MCP server long enough to
  list tools.
- **1.5** Resolve the RDFLib deprecation warnings (use the non-deprecated
  Dataset APIs) or pin RDFLib with a one-line note in `ARCHITECTURE.md`.
- **1.6** Document the concurrency stance in `ARCHITECTURE.md`: single-writer
  SQLite, what happens on concurrent open, and an explicit recorded decision
  on WAL mode (**LATITUDE**: enabling WAL is optional; deciding and
  documenting is not).

**Gate 1**: install smoke passes from a clean venv; CI (or gate script) green;
scoreboard unchanged or better; version bumped to `0.2.0.dev0`.

## Phase 2 — Split The Monolith

Goal: no module a context-bounded agent cannot read whole. Mechanical only —
**zero behavior change**. Estimated 2–4 waves.

- **2.1** Write the decomposition plan as a short table in
  `docs/journal/waves.md` before moving code: target modules and which method
  families go where. Suggested boundaries (**LATITUDE** on exact cut lines):
  `storage` (SQLite, schema, quads, seeds, import/export/serialization, FTS),
  `search`, `entities` (overview/list/describe_resource),
  `datasets` (describe_dataset, relationships), `slices`, `profiles`,
  `query_planning`, `observations` (record_* observation/claim/pattern),
  `map_authoring`, `revisions` (record/list/describe),
  `staging` (stage/check/apply/restage), `recovery`, `exports_privacy`,
  `brief`, `validation`, plus shared `types` modules colocated per subsystem.
- **2.2** Convert `doxabase/core.py` into a `doxabase/core/` package. Keep the
  public `DoxaBase` class intact by composing per-subsystem mixin classes
  (`class DoxaBase(StorageMixin, SearchMixin, ...)`) so every call site,
  including `mcp_tools.py` and all tests, is untouched except imports.
  Watch for private-helper name collisions when splitting; resolve by
  moving helpers with their only caller, or renaming.
- **2.3** Split `tests/test_doxabase_core.py` and `tests/test_mcp_tools.py`
  into per-subsystem files mirroring the module layout.
- **2.4** Tighten ceilings: largest module ≤ 5,000 lines; largest test module
  ≤ 5,000 lines. (End-state 3,000 for source comes in Phase 4 after the diet
  shrinks things.)

**Gate 2**: full suite green with no assertion changes (import paths only);
no MCP or Python behavior change; `core.py` is gone or a ≤ 50-line re-export
shim; module ceilings hold.

## Phase 3 — Token Diet And RDF-First Payloads

Goal: responses an agent can afford to read. This phase realizes the founding
bet: graph content travels as RDF text, JSON is only the envelope.
Estimated 3–5 waves.

- **3.1** Envelope diet: the MCP serialization layer (`to_jsonable`) omits
  `None` values and empty lists/dicts. Write the rule once in a short
  "Response Conventions" section (the seed of Phase 6's conventions doc):
  *absent, null, and empty are equivalent; consumers must not distinguish
  them.* Audit for any field where presence-vs-absence currently carries
  meaning and give it an explicit value instead.
- **3.2** RDF-first: rename `describe_context_slice` to `get_context_graph`
  (honoring design doc 02). TriG payload on by default; the JSON triple-array
  representation (`ResourceTriple` lists) becomes opt-in for programmatic
  callers or is deleted (**LATITUDE**) — the default response must not
  contain per-triple JSON objects. Apply the same rule to every other
  triple-array emitter (resource contexts, applied-diff exact triples stay
  opt-in as they already are). The envelope keeps: seeds, reading order,
  route legend + counts, truncation info, privacy summary, warnings.
- **3.3** `project_brief` diet: dataset entries become one line each (IRI,
  label, one-sentence status, counts) — full detail lives behind
  `describe_dataset`. `recommended_next_tasks` ≤ 10 compact rows. Inline
  duplication of per-dataset profile/query summaries is removed.
- **3.4** Collapse the `SuggestedNextAction` hierarchy to a single dataclass
  (`tool`, `args`, `reason`), delete the eight subclasses, delete the parallel
  `suggested_next_calls` display strings (exactly one machine-usable form
  survives). Cap suggestions at ≤ 5 per response.
- **3.5** Test posture: where exact-envelope assertions churn, rewrite them to
  assert semantics (counts, IRIs, decisions, gate outcomes) plus the budget
  ceilings — not full-dict equality. Semantic assertions stay strict.
- **3.6** Tighten response ceilings to end-state targets (`project_brief`
  ≤ 8,000 chars; `describe_dataset` ≤ 12,000; `describe_query_context`
  ≤ 12,000; context graph ≤ 32,000; `graph_overview` ≤ 8,000).

**Gate 3**: end-state response budgets green; rerun the Standard Trial
Battery — success rate ≥ baseline and tokens-to-outcome down materially
(expect ≥ 60% reduction; if a task got *harder*, that is a gate failure to
diagnose, not a number to explain away).

## Phase 4 — Consolidate The MCP Surface

Goal: ≤ 25 tools with no capability loss. Estimated 3–5 waves.

- **4.1** Before touching code, write
  `doxabase_design_docs/08-mcp-surface-v2.md`: a complete mapping of all
  current tools → target tools, including the spec-shape for each
  kind-dispatched family. The table below is the starting proposal
  (**LATITUDE**: adjust groupings where implementation reveals better seams,
  provided the count stays ≤ 25 and no capability is dropped). Commit the
  mapping doc before the first tool merge.
- **4.2** Implement family by family. Old tools are deleted the same wave
  their replacement lands (Loop Rule 5: no aliases). Docstrings ≤ 600 chars
  per tool; parameter descriptions count against the 25,000-char schema
  budget.
- **4.3** Kind-dispatched tools take a documented `spec` object per kind;
  validation errors must name the missing/invalid fields *for that kind* (the
  existing targeted-error style for relationship columns is the model).
- **4.4** `draft_*` read-only planning calls disappear into their staging
  counterparts as `dry_run=True` (the codebase already has this precedent in
  `restage_staged_revisions(dry_run=True)`).
  `check_staged_revision_apply` becomes `apply_staged_revision(dry_run=True)`.
- **4.5** Dangerous maintenance operations (`clear_graph`,
  `replace_graph_triples`) leave the MCP surface; they remain Python-only.
- **4.6** Update examples, tests, and every doc reference; tighten scoreboard
  ceilings: tool count ≤ 25, schema chars ≤ 25,000, largest module ≤ 3,000
  (post-diet code should now fit).

Starting proposal for the target surface (~25):

| # | Tool | Absorbs |
|---|---|---|
| 1 | `list_docs` | — |
| 2 | `get_doc` | — |
| 3 | `graph_overview` | — |
| 4 | `project_brief` | — |
| 5 | `list_entities` | — |
| 6 | `search` | `search_staged_patch_payloads` (via `scope="staged_patches"`) |
| 7 | `describe_resource` | `describe_pattern`, `describe_profile_run`, `describe_analysis_view`, `describe_assertion_support` (kind/aspect param; auto-detect type) |
| 8 | `describe_dataset` | — (flagship; keeps its name) |
| 9 | `describe_query_context` | `draft_query_plan` (via `plan_candidate=...`) |
| 10 | `get_context_graph` | `describe_context_slice` (renamed, Phase 3) |
| 11 | `record_observation` | `record_claim_observation` (structured claim params) |
| 12 | `record_query_result` | — |
| 13 | `record_pattern` | — |
| 14 | `record_profile` | `record_dataset_profile`, `record_column_profile`, `record_profile_bundle`, `record_domain_network_profile` (kind param) |
| 15 | `record_map_fact` | all 11 `record_map_*` helpers (kind param) |
| 16 | `record_claim_reconsideration` | — |
| 17 | `record_manifest` | `record_profile_to_capsule_manifest`, `record_profiled_parquet_table`, analysis-packet apply (kind param; CLIs stay) |
| 18 | `record_graph_revision` | — |
| 19 | `stage_revision` | `stage_graph_revision`, `stage_map_assertion_change`, `stage_systematisation`, `stage_pattern_promotion`, `stage_profile_map_updates`, `stage_query_storage_access_repair`, `stage_query_physical_layout_repair`, review decisions; `dry_run=True` absorbs the corresponding `draft_*` calls |
| 20 | `apply_staged_revision` | `check_staged_revision_apply` (`dry_run=True`) |
| 21 | `restage_staged_revision` | batch restage (list param + `dry_run`) |
| 22 | `plan_staged_revision_recovery` | recovery session start/describe (session params) |
| 23 | `list_revisions` | `list_graph_revisions`, `list_graph_versions`, `list_resource_revisions` (kind/filter params) |
| 24 | `describe_revision` | `describe_graph_revision`, `describe_staged_revision`, `describe_applied_revision_diff`, `describe_graph_version_diff`, `describe_revision_lineage`, `describe_resource_revision_lineage`, snapshot-evidence/graph-snapshot describers (aspect param) |
| 25 | `export_preflight` | `scan_sensitive_literals` (`kind="scan_only"`), context-slice preflight |
| 26 | `export_bundle` | `export_trig`, `export_graph`, `export_context_slice`, `export_staged_revisions`, `export_profile_insight_review_bundle`, `export_revision_snapshots`, `export_handoff_bundle` (kind param) |
| 27 | `import_bundle` | `import_turtle`, `import_trig`, `import_revision_snapshots`, `import_handoff_bundle` (kind param) |
| 28 | `validate_graph` | — |
| 29 | `load_example_fixtures` | — (scratch-capsule guard stays) |

That lists 29; the cap is 25. **LATITUDE** on which final folds close the gap —
candidates: fold 8 into 7; fold 29 into 27 (`kind="example_fixtures"`); fold
18 into 19; fold 25 into 26 (`preflight_only=True`). Choose the folds that
read most naturally in trials, and record the decision in doc 08.

**Gate 4**: tool count ≤ 25; schema budget met; doc 08 accurate; full battery
rerun passes on the new surface at ≥ baseline success.

## Phase 5 — State, Not Script

Goal: `project_brief` reports; the agent decides. Estimated 2–3 waves.

- **5.1** Rebuild `project_brief` output as: capsule identity/counts; a
  `gates` list (each: `gate`, what it `blocks` — mutation/export/none — and
  the one `details_call` to inspect it); a `queues` list (each: name, count,
  one representative IRI); dataset one-liners; ≤ 5 suggestions. Delete
  `first_unattended_action`, `frontier_first_action`, `must_rerun_call`,
  `mutation_allowed_after`, `inspection_next_action`-vs-`suggested_next_action`
  lanes, and the frontier rerun protocol. Safety semantics are preserved by
  the `gates` list: a blocking gate is still blocking; what disappears is the
  prescribed action *sequence*, not the constraint.
- **5.2** Write `docs/agent/working-the-capsule.md` (≤ 200 lines): the
  judgement that used to live in routing fields — how to sequence safety
  gates, staged recovery, profile review, and frontier expansion — written as
  guidance for a capable agent, not as a rule maze.
- **5.3** Rewrite `docs/agent/start-here.md` ≤ 120 lines: what DoxaBase is,
  the first five calls, graph placement cheat sheet, pointers. No timing
  diaries, no conditional routing chains.

**Gate 5**: budgets hold; run a **wrong-hunch trial** (agent given a plausible
but incorrect first task on a capsule with a blocking gate) — the agent must
find and respect the gate from `gates` + docs alone. If it cannot, fix the
*state presentation*, not by re-adding routing fields.

## Phase 6 — Docs Distillation

Goal: reference docs an agent can actually read. Estimated 2–3 waves.

- **6.1** Move all journal content out of `docs/agent/`: the "Product Signals
  From Recent Trials" history, timing measurements, dated narratives — into
  `docs/journal/`. Nothing in `docs/journal/` is MCP-registered.
- **6.2** Rewrite the reference docs against the Phase 4/5 surface, with
  per-doc caps: `start-here` ≤ 120 lines (done in 5.3); `graph-roles` ≤ 100;
  `working-the-capsule` ≤ 200; each topic doc (`observation-recording`,
  `patterns`, `map-authoring`, `profiling`, `systematisation`,
  `query-planning`, `staged-revisions`, `revisions`, `context-slicing`,
  `lexical-search`, `executable-catalog`, `field-trials` playbook,
  `analysis-packets`) ≤ 400 lines.
- **6.3** Replace `response-shapes.md` with `response-conventions.md`
  (≤ 600 lines): the envelope conventions (absent==null==empty, truncation
  fields, budget guarantees, suggestion shape) plus the key fields per tool
  family. Generate `mcp-tools.md` from the registered tools' schemas via a
  small `tools/gen_docs.py`, or delete it in favor of the MCP schemas
  themselves (**LATITUDE**). Delete `api-reference.md` if module split +
  docstrings make it redundant, else generate it.
- **6.4** Refresh `README.md` and `ARCHITECTURE.md`: honest current status,
  the distilled surface, no timing journal, updated direction ("what V2 might
  add" pulls from doc 04 plus this program's retrospective).
- **6.5** Tighten ceilings: `docs/agent/` ≤ 150 KB.

**Gate 6**: docs budgets green; cold-start trial in which the agent may read
at most `start-here` + 2 further docs and must complete battery task T1 within
a 60k-token total budget.

## Phase 7 — Prove It From The Outside

Goal: external signal before feature work resumes. Ongoing.

- **7.1** Write `doxabase_design_docs/09-distillation-retrospective.md`:
  scoreboard before/after table, trial-battery deltas vs. the Phase 0
  baseline, decisions taken under LATITUDE, and the honest list of what got
  worse.
- **7.2** External case study: from an **installed wheel** in a clean venv
  (not the repo checkout), run a full workflow against real or realistic
  external data — the Enron-style corpus if available in the container,
  otherwise the richest non-fixture data readable there. Record
  tokens-to-outcome. Product friction found here is the seed list for
  post-program work.
- **7.3** **Requires James's approval before implementation**: a bounded
  read-only SPARQL spike — SELECT-only, enforced `LIMIT` ≤ 500, query timeout,
  read-only connection — measuring which of the remaining describers it could
  subsume. Deliver a report with measurements; do not mass-delete describers
  on this evidence alone.
- **7.4** Tag `v0.2.0`. Feature development resumes only after James reviews
  the retrospective. The Loop Rules remain in force permanently.

---

## Standard Trial Battery

Used for the Phase 0 baseline and every phase-gate rerun. Each task runs as a
fresh cold sub-agent with MCP access to a scratch capsule (fixtures loaded)
plus the agent docs, and nothing else. Record per task: success against
rubric, total context cost (tool schemas + docs fetched + responses, chars ÷ 4),
and turns to first correct action. Reports go in `docs/journal/trials/`.

- **T1 — Lore recall.** "What should an analyst know before trusting MMSI as
  a vessel identity key, and what is the evidence?" Success: cites the MMSI
  caveat and its evidence/source resources by IRI.
- **T2 — Record and promote.** Given three synthetic findings about the
  Polymarket fixture (supplied in the trial prompt), record them as
  observations, synthesize a pattern, stage the map implication, and apply it
  after checks. Success: observation(s) + pattern + staged revision + clean
  apply + `validate_graph(scope="all")` conforms.
- **T3 — Query handoff.** Produce a non-executed DuckDB query handoff for an
  AIS DailyIndex question. Success: a draft plan with correct
  path/relation provenance and explicit review gates; no invented paths.

Comparison discipline: batteries are only compared like-for-like (same tasks,
same capsule contents, same rubric). When the surface changes names, update
the trial *prompts* minimally and note it in the report.

## Escalation And Reporting

Stop the loop and write a handoff for James when: a phase gate fails twice; a
budget appears unreachable without weakening a semantic guarantee; a LATITUDE
decision feels like it changes product direction; storage schema or ontology
semantics would need to change; or external signal contradicts this program's
assumptions.

At every phase gate, append a ≤ 1-page report to `docs/journal/waves.md`:
scoreboard before/after, battery results vs. baseline, LATITUDE decisions
taken, open questions. James reads these between phases; a fresh outside
review at Gates 3 and 6 is recommended.

## Design Slogans (Distillation Edition)

- Subtract, then verify.
- Tokens are the unit of cost; budgets are tests, not aspirations.
- TriG is the payload; JSON is the envelope.
- State, not script: the agent supplies judgement.
- Delete, don't deprecate — pre-1.0 freedom expires; spend it now.
- The journal remembers so the docs can instruct.
- A fresh agent's first hour is the product.
- Keep V1.5 boring, small, and shippable.
