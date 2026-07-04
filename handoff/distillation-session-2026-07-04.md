# Distillation Session Handoff — 2026-07-04

**Author**: Claude (Fable), executing the Distillation Program at James's
request. **Audience**: whichever agent continues this work. James plans
Opus-4.8-max / GPT-5.5-xhigh-class implementers, so assume capability —
but the judgement calls are still written out so nothing rests on
re-deriving them. James wants fairly regular pushes to
`origin/codex/distillation-program` so he can follow, and welcomes longer
commit-message bodies.

## What this session is

James adopted the fresh-eyes review (`doxabase_design_docs/06-...md`) and the
Distillation Program (`doxabase_design_docs/07-distillation-program.md`) as
the project's active direction. This session executes the program from Phase 0
onward on branch `codex/distillation-program`. Doc 07 is the authority; the
Permanent Loop Rules are in `AGENTS.md`; progress log is
`docs/journal/waves.md` (read those three first, then this).

## State at last update (keep this section current)

- **Phase 0 — DONE** (commit `519f110`): scoreboard + budget tests + loop
  rules + journal. Gate 0 passed.
- **Phase 0.5 — DONE** (`150d726`): baseline battery T1/T2/T3 all succeeded
  at 60k/154k/85k tokens-to-outcome. Report:
  `docs/journal/trials/2026-07-baseline.md` (contains the numbers phase gates
  must beat and the method for rerunning like-for-like with Sonnet agents and
  a FastMCP-dispatch bridge).
- **Phase 1 — DONE** (`8a5061a`): hatchling build, `doxabase/_data` wheel
  data, dev-dep split, `doxabase-mcp` script, `tools/gate.sh` (full gate incl.
  clean-venv wheel smoke), CI workflow, rdflib <8 pin, WAL stance in
  ARCHITECTURE.md. Gate 1 passed.
- **Phase 2 — DONE** (`d9cb165`): `core.py` (74,667 lines) → `doxabase/core/`
  package (32 mixins + `_shared` + `_types`, largest 4,903 lines); test
  monoliths → `tests/core/` + `tests/mcp/`. Zero behavior change; 764 tests
  green; module ceilings ratcheted to 5,000. Gate 2 passed.
- **Phase 3 — PARTIALLY DONE**:
  - 3.1 envelope diet — DONE (`e8a6361`): `to_jsonable` omits None/[]/{}
    (convention in its docstring); tests updated. project_brief 100k→77k.
  - 3.2 RDF-first — DONE (`2963c13`): `get_context_graph` (renamed), TriG
    default, triple-JSON and dataset/pattern context inlines are now
    `doxabase_internal` fields (Python-only; a field-metadata convention in
    `to_jsonable`). Slice: 168,598 → 44,366 chars.
  - 3.3/3.4/3.5/3.6 NOT started. 3.4 was dispatched to a sub-agent that hit
    the account **spend limit** before writing anything (tree stayed clean);
    the full spec is in "Exact next steps" below and in the agent prompt
    pattern there. `docs/agent/response-conventions.md` (registered) states
    the target suggestion shape; update its "Suggestions" section to the
    exact `tool`/`args`/`reason` keys when 3.4 lands.
- **Phase 4 — mapping DONE, implementation NOT started**:
  `doxabase_design_docs/08-mcp-surface-v2.md` is the complete, authoritative
  89 → 25 tool mapping, including kind-dispatch conventions, the two
  baseline-trial trap fixes, chosen LATITUDE folds, and a 6-wave
  implementation order. Implement exactly from that doc.
- **Phases 5–7 — NOT started.**

## Exact next steps (in order)

1. ~~Finish 3.1~~ DONE (`e8a6361`).
2. ~~3.2 RDF-first context slices~~ DONE (`2963c13`).
2b. **3.4 SuggestedNextAction collapse** (moved before the brief rebuild is
   also fine — either order works; doing 3.4 first shrinks every response
   and the slice `resources` routes): replace the hierarchy in `_types.py`
   (base + 10 subclasses) with one frozen dataclass
   `SuggestedNextAction(tool: str, args: dict, reason: str)` where `tool`
   is the MCP tool name (old `mcp_tool_name`). Every construction site:
   keep old `mcp_tool_name`→`tool`, `arguments`→`args`, `reason`→`reason`;
   drop `action_label`, `tool_name`, `call`, and all subclass extras
   (fold genuinely load-bearing extra text — e.g. `unattended_caution` —
   into `reason`). Delete `suggested_next_calls` fields everywhere plus the
   call-string helpers (`brief._suggested_call_string`,
   `profile_review._suggested_call_string_for_arguments`) once unused.
   Update consumers reading `.mcp_tool_name`/`.arguments`/`.action_label`.
   Tests: rename asserted keys, delete assertions on removed fields, never
   weaken tool/args/reason value assertions. Out of scope:
   RevisionNextAction machinery, docs/, BUDGETS. Then cap suggestions ≤ 5
   per response and ratchet response ceilings. Update
   `response-conventions.md` "Suggestions" to the exact new keys.
3. **3.3 project_brief diet + 5.1 state-not-script**: these touch the same
   code (`doxabase/core/brief.py`, `_types.py` ProjectBrief*) and tests —
   do them as ONE rebuild (recorded deviation, journal it). Target dataclass
   design (replaces `ProjectBrief` and its 9 satellite classes entirely):

   ```python
   @dataclass(frozen=True)
   class ProjectBriefGate:
       gate: str          # "stale_seed_recovery" | "staged_revision_recovery"
                          # | "privacy_export_review" | "handoff_import_incomplete" | ...
       blocks: str        # "mutation" | "export" | "none"
       detail: str        # one sentence of STATE, not instruction
       details_call: str  # the one tool that inspects it

   @dataclass(frozen=True)
   class ProjectBriefQueue:
       name: str          # "staged_review", "profile_review", ...
       count: int
       example_iri: str | None

   @dataclass(frozen=True)
   class ProjectBriefDataset:
       iri: str
       label: str | None
       is_table: bool
       status: str        # one sentence, e.g. "profiled; storage access unverified"
       column_count: int
       caveat_count: int

   @dataclass(frozen=True)
   class ProjectBrief:
       key_counts: dict[str, int]      # from graph_overview
       dataset_count: int
       datasets: list[ProjectBriefDataset]   # ≤ limit
       gates: list[ProjectBriefGate]         # empty list = nothing blocked
       queues: list[ProjectBriefQueue]
       suggested_next_actions: list[SuggestedNextAction]  # ≤ 5
       limit: int
   ```

   Derivation: current `health_tasks` that block become `gates`
   (seed recovery, staged recovery, privacy/export, handoff import);
   `queue_counts`/`recommended_next_tasks` collapse into `queues` (count +
   one example IRI each); per-dataset `query`/`profile` sub-summaries are
   DELETED (that detail lives behind `describe_dataset`). DELETE the lanes:
   `safety_first_*`, `frontier_first_*`, `first_unattended_*`,
   `frontier_status` (incl. `must_rerun_call`), `next_best_expansion`,
   `full_frontier_expansion`, `limit_crowded_queue_types`, the
   `returned_*`/`omitted_*` count triplets (keep plain counts). Safety
   semantics live ONLY in `gates` — a blocking gate still blocks; what
   disappears is the prescribed action sequence. Do NOT call
   `describe_dataset` per dataset in the new builder (that inlining is the
   cost center); derive dataset one-liners from cheap graph queries.
4. **3.4 SuggestedNextAction collapse**: replace the hierarchy in
   `_types.py` (`SuggestedNextAction` + 10 subclasses) with one frozen
   dataclass: `tool` (MCP tool name), `args` (dict), `reason` (str). Delete
   `suggested_next_calls` everywhere (the parallel display strings). Cap
   suggestions at 5 per response. ~466 construction sites — mechanical;
   grep for `SuggestedNextAction(` subclasses and `action_label=`.
5. **3.5/3.6**: convert exact-envelope test assertions that churn into
   semantic assertions; then ratchet response ceilings in
   `tools/scoreboard.py` BUDGETS to end-state (project_brief ≤ 8,000 etc.)
   and rerun the battery (Gate 3) comparing with the baseline report.
6. **Phase 4**: implement `08-mcp-surface-v2.md` wave by wave.
7. **Phases 5.2/5.3, 6, 7** per doc 07.

## Facts a future agent will otherwise rediscover slowly

- **Gate**: `bash tools/gate.sh` is the whole pre-commit gate. Budget
  ceilings live ONLY in `tools/scoreboard.py` BUDGETS; they only move down.
- **The composed-facade quirk**: mixin methods that reference `DoxaBase` at
  runtime work because `doxabase/core/__init__.py` injects the class into
  every mixin module's globals after composition. If you add a module,
  add it to that loop. Rewriting call sites to `type(self)`/`cls` and
  deleting the loop is welcome cleanup in any Phase 3/4 wave.
- **Trial rig**: reusable bridge pattern in the baseline report — build a
  scratch capsule, dispatch through `server.call_tool` (byte-identical
  payloads), log char counts per call, charge the tool-registry JSON as a
  constant. Sonnet sub-agents, one per task, forbidden to read the repo.
- **Enron external material** (for Phase 7): `/tmp/enron-doxabase-handoff`
  (durable copy `/home/codex/enron-doxabase-handoff`). James's read on the
  original Enron session: the *client agent's* quality contributed as much
  as DoxaBase did — so run the Phase 7 case study with a strong client
  agent, and treat "how much does agent quality mask product friction?" as
  a question the study should answer, not noise.
- **Commits**: authored as James, rationale-focused subject+body, no AI
  attribution, on `codex/distillation-program`. Do not push without James.
- **The original core.py** (pre-split) is recoverable from git history at
  `d9cb165^`; the split was AST-generated, methods verbatim.
- `.doxybase.sqlite` (old spelling) at repo root is an old local capsule,
  untracked on purpose; the container path `/workspaces/doxybase` also keeps
  the old spelling. Tracked content uses DoxaBase/doxabase.

## Why (one paragraph, so the point survives)

The V1 loop optimized each commit's local legibility and destroyed the
system's global legibility; the fix is subtraction with instruments. When in
doubt: fewer tools, smaller responses, state-not-script, TriG-not-JSON,
delete-don't-deprecate, and the scoreboard decides arguments.
