# DoxaBase — Fresh-Eyes Design Review (2026-07-03)

**Provenance**: External review commissioned by James, performed by a reviewer
(Claude) with no prior exposure to the project, at repository state `eea3b83`
("Cover domain profiles in profile manifest smoke"). Method: full read of the
design docs, `README.md`, `ARCHITECTURE.md`, `AGENTS.md`, and agent docs;
structural analysis of the package; git-history analysis; full test-suite run
(750 passed, 1 skipped, ~57 s at `-n 16`); execution of the bundled examples;
and direct measurement of MCP response sizes on the bundled fixture capsule.

This document is the review as delivered, lightly formatted. It is the
motivating context for `07-distillation-program.md`.

---

## TL;DR

The problem DoxaBase attacks is real and well-chosen, and the intellectual
core of the design — the epistemology of observations, patterns, claims,
evidence, reconsiderations, and staged promotion into a durable map — is
genuinely novel and worth pursuing. The storage layer is small and sane. The
test discipline is excellent.

But the implementation has drifted a long way from the project's own founding
principles, and the drift has a clear mechanical cause: an autonomous
improvement loop whose every iteration adds surface area and whose fitness
function contains no subtractive term. Five weeks and 928 commits in, the
"deliberately small" V1 is a 74,607-line single-file core with 96 public
methods on one class, 89 MCP tools (the spec suggested ~8–10), a 357 KB
document that exists solely to describe the API's own response shapes — and no
way to `pip install` it. The orientation call the docs tell every fresh agent
to make first returns ~25,000 tokens *on an 805-triple fixture*. The system
built to solve agent cold-start has itself become too large for an agent to
cold-start into.

Verdict: useful problem, right core bets, wrong trajectory. The single
highest-leverage change is not to the code — it's to the loop that writes the
code.

---

## Is it solving a useful problem? Yes — emphatically

Three things establish this is a real gap and not a solution in search of a
problem:

**The "handover conversation" framing is the right product idea.** Data work
has enormous amounts of unwritten lore — caveats, quirks, failed assumptions,
"the MMSI column lies sometimes," why a join that looks right is wrong. Today
that lore lives in people's heads and dies in chat scrollback. Making it cheap
to record *with evidence and confidence attached*, and cheap for the next
agent or human to retrieve, is a genuinely valuable target that neither data
catalogs (too schema-rigid, too enterprise) nor agent memory products
(unstructured prose blobs) currently serve.

**The epistemic model is a real contribution.** Observation → pattern →
systematisation, with claims that can be *weakened, contradicted, superseded,
or refined* rather than deleted (`record_claim_reconsideration`), evidence
resources with source spans, and staged revisions carrying rationale — this
treats uncertainty as first-class without letting it rot into noise. Most
memory systems have nothing like this. The name (doxa → episteme) is earned.

**The foundational bets are right-sized.** Local single-file SQLite capsule;
no LLM inside the library; agents supply judgement, library supplies
mechanics; RDF as the medium because frontier models are unexpectedly good at
it; SHACL as an explicit diagnostic rather than a commit gate; immutable seed
graphs vs. mutable project graphs. Each of these is defensible and several are
quietly clever (the `ontology = base_ontology + ontology` logical include;
read-only open mode; row-level staged snapshots for exact drift reporting; the
privacy posture that "scanner-clean is a review prompt, not export approval").

The goals are good, and the design brief in `doxabase_design_docs/01` is one
of the better-written briefs around — clear thesis, explicit non-goals, design
slogans that are actually testable. That is exactly why the current state
deserves a hard look, because the implementation now violates most of those
slogans.

## Is it doing so in a useful way? Partly — and decreasingly

The design brief's stated intent against what exists today:

| Design brief (May 30) | Repo today (July 3) |
|---|---|
| "Keep V1 boring, small, and buildable" | `core.py`: 74,607 lines / 2.98 MB, one class, 1,321 methods, 244 module-level dataclasses |
| MCP surface of ~8–10 tools; "Do not create one MCP tool per tiny graph operation" | **89 MCP tools** |
| ~8 public methods sketched in the API spec | **96 public methods** on `DoxaBase` |
| "Return bounded graph slices, not opaque answers" — Turtle fragments | `describe_context_slice` on one table: **~65,000 tokens** of JSON; the RDF (TriG) rendering is off by default |
| "The API should curate RDF, not hide RDF" | The spec's `get_context_graph` / `preview_context_graph` / `submit_graph_revision` were never built; agents get bespoke JSON describers instead |
| "No call should… fill the agent's context" | `project_brief` (the documented *first* orientation call): ~25,000 tokens on the 805-triple fixture capsule |
| "Easy to drop into a project" | No `[build-system]` in pyproject → not installable; no CI; `pytest` is a runtime dependency |

### 1. The interface inverted: from "curated RDF" to a bespoke JSON operating system

The founding bet was that frontier agents are good at RDF, so the library
should hand them bounded RDF fragments and accept RDF back. What actually got
built is the opposite: an enormous family of `describe_*` / `draft_*` /
`stage_*` / `record_*` endpoints, each returning a deeply nested, hand-designed
JSON dataclass. The RDF is still in there — but it's behind the curtain, and
the JSON in front of it is now so elaborate that it needs its own 7,957-line
`response-shapes.md` just to tell agents what the field names mean. When your
API's response-shape documentation is larger than most codebases, the response
shapes are the problem, not the documentation.

The cost is concrete, measured on the fixture capsule (7 tables, 805 triples —
a *toy*):

- `project_brief`: 100 KB JSON (~25k tokens), 63 KB of which is inlined
  per-dataset summaries and 33 KB "recommended next tasks."
- `describe_dataset` on one 6-column table: 43 KB (~11k tokens), containing
  382 `null` values and 63 empty lists — the envelope ships every field always.
- `describe_context_slice(profile="dataset_brief")`, defaults: 261 KB (~65k
  tokens), of which 162 KB is triples *encoded as verbose JSON objects*. The
  same triples as TriG would be roughly a tenth of that — and TriG is the
  representation the design said agents are good at.

Meanwhile the genuinely well-behaved calls — `list_entities` (~430 tokens),
`search` (~1.7k), `graph_overview` (~3.5k) — are the ones closest to the
original spec. That's not a coincidence.

There's also a fixed overhead nobody is measuring: mounting an 89-tool MCP
server injects on the order of 10–20k tokens of tool schemas into every
session before the first call is made.

The limits framework exists everywhere (good — the brief demanded it), but it
bounds *triple counts and list lengths*, not the thing that actually matters
to the consumer: **tokens**. Every response should be designed and
regression-tested against a token budget the way the brief demanded limits.

### 2. The API has started scripting the agent — against the project's own thesis

The thesis is "agents supply semantic judgement; DoxaBase supplies graph
mechanics." But look at what `project_brief` has become:
`first_unattended_action`, `frontier_first_action`, `mutation_allowed_after`,
`frontier_status.must_rerun_call`, `inspection_next_action` vs.
`suggested_next_action` lanes… plus a `SuggestedNextAction` hierarchy with
eight subclasses, attached to nearly every response (466 references in
core.py). `start-here.md` — nominally the fast on-ramp — is 345 lines of dense
conditional routing rules for following these fields correctly.

This is a workflow engine growing inside a memory library. Each routing field
was added because some trial agent got lost, and each is locally reasonable.
But collectively they replace the agent's judgement with a rule-maze, and the
rule-maze itself now generates the confusion it was meant to cure (the docs
contain multiple paragraphs clarifying how the routing fields interact with
each other). `ARCHITECTURE.md` has the right warning: *"If the helper only
makes familiar map facts easy, it is suppressing the agent's knowledge-graph
reasoning rather than supporting it."* That warning now applies to the
orientation layer, not just promotion helpers.

A memory capsule should tell an agent *what is true and what is pending* —
state, queues, gates — and let the model decide what to do. If a fresh
frontier model can't figure out the next action from honestly-presented state,
the fix is better state presentation, not another `*_next_action` field.

### 3. The monolith and the docs are now hostile to their only audience

The audience for this codebase is agents (humans have plainly stopped reading
`core.py` — nobody reads a 3 MB file). But agents are *also* context-bounded,
which makes file size a first-order engineering constraint here, more than for
human-maintained code:

- `core.py` cannot be read; it can only be grepped. Single methods run to
  1,840 lines (`describe_context_slice`). Duplication is low (~7% by 6-line
  shingle analysis) — so this is 75k lines of genuinely distinct, interwoven
  logic, which is worse than copy-paste: there is no cheap consolidation.
- `field-trials.md` is 4,883 lines, ~4,500 of which are an append-only journal
  of past trials — valuable history, wrong location. It's registered as an
  agent-facing MCP doc.
- `start-here.md` embeds a multi-day lab notebook of pytest timing
  measurements ("On July 1, 2026, the rebuilt YOLO container…"). README and
  AGENTS.md carry the same trivia. Operational archaeology has colonized the
  reference docs.
- The growth rate at peak was ~170 KB/day of core.py. On the current
  trajectory the repo's context cost doubles roughly monthly.

### 4. It still can't be used by anyone else

For a project whose stated purpose is to be dropped into other projects, this
is the most surprising gap: there is no `[build-system]` section, so the
package cannot be built or installed — it only works run from the repo root
under `uv`. `pytest` and `pytest-xdist` are declared as *runtime*
dependencies; `pyarrow` is an undeclared optional. There is no CI, no
lint/type-check config (despite disciplined type hints), no versioning or
changelog beyond `0.1.0`. And all product signal to date comes from
self-authored fixtures and self-run trials — the one external pressure test
(the Enron handoff) clearly produced the best recent feedback, and its
directory is already gone.

928 commits of polish on internal workflows, zero commits on making it
installable, is a portfolio badly out of balance.

## The root cause: the loop's fitness function, not any single decision

This is the most important observation, because everything above is a symptom.

The commit history shows the shape: ~5–15 commits/day of human-paced work
through mid-June, then the autonomous loop engages and holds ~87–114
commits/day for a week. The loop, as encoded in `AGENTS.md` and
`docs/agent/project-strategy.md`, is: run a field trial → find friction →
"implement the sensible smallest justified fix" → update tests and docs →
commit. Every step is individually sound. But observe what the loop *can* and
*cannot* produce:

- A trial agent gets confused → the fix is a new field, a new gate, a new doc
  paragraph, occasionally a new tool. **Additive.**
- The strategy doc's axes (staged revisions, profiling, query planning) are
  all build-out axes. **Additive.**
- "Smallest justified fix" biases toward local patches over structural moves.
  **Additive, and fragmenting.**
- Nothing in the loop ever asks: which tool should be merged away? Which
  response field has never been read by any trial agent? Which doc has
  negative value? There is **no subtractive pressure anywhere**, and no budget
  metric (tokens per response, tool count, doc bytes, file size) that a commit
  could regress.

The result is a ratchet. Each fresh trial agent faces a slightly bigger
surface, generates slightly more confusion, which generates more guidance,
which grows the surface. The loop is, in a very literal sense, optimizing
agent-legibility *of the current commit* while destroying agent-legibility
*of the system*. It is also self-referential: the trials run on fixtures the
loop wrote, judged by criteria the loop wrote, verified by tests the loop
wrote. It's a closed epistemic loop — ironic, for a project about epistemic
hygiene.

None of this means autonomous loops can't build this project. It means the
loop needs a fitness function with negative terms, and periodic
externally-forced distillation.

## Suggestions

### For the humans steering the project

1. **Declare a feature freeze and run a distillation phase.** Past V1 scope in
   every direction; nothing valuable is lost by stopping build-out for a
   while. The distillation goal: same capability, a fraction of the surface.
   Set hard numeric budgets and put them in a tracked scoreboard the loop must
   not regress — e.g.: ≤ 25 MCP tools; `project_brief` ≤ 2k tokens on the
   fixture capsule; `describe_dataset` ≤ 3k; any context slice ≤ 8k at
   defaults; no module over ~3k lines; `start-here.md` ≤ 100 lines. The
   specific numbers matter less than their existence and enforcement.

2. **Make token cost a tested invariant.** Add regression tests that serialize
   each major tool's response on the fixture capsule and assert a byte/token
   ceiling. This turns the brief's "no call should fill the agent's context"
   from a slogan into a gate, and gives the loop something to optimize
   *downward*.

3. **Return RDF by default; make JSON the envelope, not the payload.** Kill
   the JSON-triple-array representation (or make it opt-in) and return
   Turtle/TriG for graph content, with a compact JSON wrapper for counts,
   warnings, and truncation flags. This is simultaneously the founding thesis
   and a ~10x token saving. Consider actually building the spec's
   `get_context_graph`/`preview_context_graph` pair — the cleanest artifacts
   in the whole design — and letting several `describe_*` variants collapse
   into policies of it.

4. **Collapse the tool surface into parameterized families.** The 89 tools are
   largely one family per noun: `describe(kind=...)`, `record(kind=...)`,
   `stage(kind=...)`, `list(kind=...)`, `export(kind=...)`. The API spec
   warned about exactly this. Fewer tools also directly cuts the per-session
   MCP schema overhead.

5. **Reconsider bounded read-only SPARQL sooner than "later."** The V1 "no
   SPARQL" rule was right for bootstrapping, but the 89-tool surface is the
   classic symptom of accessor proliferation in the absence of a query
   language. A SELECT-only, LIMIT-enforced, timeout-bounded SPARQL tool would
   replace dozens of bespoke describers at near-zero marginal maintenance
   cost — and "frontier agents are good at SPARQL" is the *same bet* the
   project already made about RDF. The bespoke describers should be the
   curated fast paths for the top five workflows, not the only doors.

6. **Ship it.** Add `[build-system]`, move test deps to a dev group, declare
   the `pyarrow` extra, add CI (pytest + `validate_rdf.py` + ruff/mypy), tag a
   version. Then put it into two or three real projects that are not fixture
   theater and let *external* friction drive the next hundred commits. The
   Enron exercise visibly produced the best recent signal; institutionalize
   that.

7. **Re-examine the workflow-engine drift.** Decide explicitly: is DoxaBase a
   memory substrate, or an agent-orchestration framework? If the former (which
   this review argues), `project_brief` should shrink to honest state —
   queues, gates, counts, pointers — and the
   `first_unattended_action`/`mutation_allowed_after` behavioral programming
   should move into docs or a thin optional layer. If the latter, that's a big
   scope decision that deserves a design doc, not accretion.

8. **Split `core.py`.** Storage/quads, search, revisions/staging, profiles,
   query planning, slicing/description, brief — behind a `DoxaBase` facade.
   For an agent-maintained codebase, module size *is* an API-ergonomics
   decision, not aesthetics.

9. **Separate reference from journal.** Trial history goes to `docs/journal/`
   (or git notes), reference docs get rewritten for the current system, and
   timing trivia leaves `start-here.md`/README entirely. Also worth generating
   `api-reference.md` and `response-shapes.md` from code instead of
   hand-maintaining 500 KB of Markdown that can silently drift — or better,
   simplifying shapes until most of it isn't needed.

10. Small hygiene items: the handoff still references `/work/doxybase` and
    `.doxybase.sqlite` (pre-rename spelling — the first commit says
    "DoxyBase"); RDFLib deprecation warnings (398 per test run) should be
    addressed before an RDFLib upgrade turns them into breakage; single-writer
    SQLite deserves an explicit documented stance (and probably WAL mode).

### For the agents running the loop

Rules to add to `AGENTS.md`/`project-strategy.md`:

- **Every improvement wave must nominate at least one deletion, merge, or
  shrink** — a tool to fold into a family, a field no trial has ever read, a
  doc section to retire. A wave with no defensible subtraction candidate
  should say so explicitly and why.
- **One-in-one-out for tools and response fields** until the budget caps are
  met. A new routing field must demonstrate that a documentation fix or an
  improvement to an *existing* field could not close the same gap.
- **Measure trials in tokens-to-outcome**, not just task completion: how many
  tokens did the cold agent consume, across tool schemas + doc reads +
  responses, before its first correct action? A fix that adds guidance but
  raises that number is a regression even if the confused behavior
  disappeared.
- **Stop appending; start rewriting.** When a trial lesson changes how agents
  should work, rewrite the relevant doc section to be true *now*, and move the
  narrative of how you learned it to the journal.
- **Treat file and response size as budgets you are spending**, the same way
  privacy gates are already treated as blocking. The scoreboard metrics belong
  in the pre-commit checklist next to `pytest` and `validate_rdf.py`.

## What NOT to change

Worth protecting: the graph-role model; the
observation/pattern/claim/evidence/reconsideration epistemology; staged
revisions with rationale, snapshots, and drift detection; SHACL-as-diagnostic;
the privacy preflight posture; the immutable seed graphs and the restrained,
well-commented `rc:` ontology (which, notably, *stayed* small — 1,242 triples —
proving the discipline is achievable); the no-LLM-inside rule;
SQLite-single-file; docs-exposed-through-MCP as a mechanism; and the
trial-driven development method itself, which produced genuinely sharp product
insights — it just needs a counterweight.

## Closing verdict

Useful problem: yes, one of the better agent-infrastructure ideas around, with
a real epistemological core rather than a gimmick. Useful way: the foundations
yes, the current trajectory no — the project is being buried by an
additive-only autonomous loop, and its interface has quietly inverted from
"curate RDF for agents" into "bespoke JSON workflow engine too large for
agents." The fix is less code and better loop incentives, not more capability.
Freeze, distill against explicit token/surface budgets, make it installable,
and hand it to real outside projects — the idea has earned that chance.

---

## Appendix: measurements at `eea3b83` (2026-07-03)

All response sizes are `len(json.dumps(...))` on a fresh capsule with both
bundled fixtures loaded (805 triples), default arguments. Tokens estimated at
~4 chars/token (JSON typically tokenizes worse, so these are conservative).

| Measurement | Value |
|---|---|
| `doxabase/core.py` | 74,607 lines / 2.98 MB, 244 top-level classes, `DoxaBase` with 96 public methods / 1,321 total |
| MCP tools registered | 89 |
| `tests/test_doxabase_core.py` | 44,245 lines |
| `docs/agent/response-shapes.md` | 7,957 lines / 357 KB |
| `docs/agent/field-trials.md` | 4,883 lines (~4,486 of append-only trial journal) |
| `docs/agent/mcp-tools.md` | 3,143 lines / 203 KB |
| `project_brief` response | 100,462 chars (~25k tokens) |
| `describe_dataset` response (one 6-column table) | 43,005 chars (382 nulls, 63 empty lists) |
| `describe_query_context` response | 32,408 chars |
| `describe_context_slice` response (dataset_brief, defaults) | 260,768 chars; triples-as-JSON portion 161,673 chars |
| `graph_overview` / `search` / `list_entities` | 14,187 / 6,870 / 1,714 chars |
| Test suite | 750 passed, 1 skipped, ~57 s at `-n 16` |
| Commits | 928 total (2026-05-30 → 2026-07-03); peak ~100–114/day June 26 – July 1 |
| 6-line shingle duplication in core.py | ~7.3% |
| Packaging | no `[build-system]`; `pytest`/`pytest-xdist` in runtime deps; no CI |
