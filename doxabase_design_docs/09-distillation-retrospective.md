# Distillation Retrospective (V1 → V1.5)

**Date**: 2026-07-05. **Status**: program executed through Phase 7; this
document is the review James reads before feature development resumes
(doc 07 §7.4). Written by the executing agent; measurements are from
`tools/scoreboard.py` and the trial reports under `docs/journal/trials/`.

## Scoreboard: before → after

| Metric | Baseline (2026-07-04) | Now | End-state target |
|---|---|---|---|
| MCP tools | 89 | **25** | 25 ✓ |
| Schema chars per session | 138,353 | **35,136** | 25,000 (open item) |
| Largest source module | 74,667 lines (core.py) | 4,829 (staging.py) | 3,000 (open item) |
| Largest test module | 44,285 lines | 4,549 | 5,000 ✓ |
| `project_brief` | 100,462 chars | **4,598** (3,835 on the real Enron capsule) | 8,000 ✓ |
| `describe_dataset` | 30,023 | 15,355 | 12,000 (open) |
| `describe_query_context` | 31,454 | 14,732 | 12,000 (open) |
| Context graph (TriG **excluded** then) | 168,598 | **33,096 (TriG included)** | 32,000 (≈) |
| `graph_overview` | 14,187 | 5,692 | 8,000 ✓ |
| `search` | 6,870 | 6,221 | 8,000 ✓ |
| `list_entities` | 16,345 | 4,337 | 4,000 (≈) |
| `docs/agent/` | 1,484,446 bytes | **142,249** | 150,000 ✓ |
| `start-here.md` | 346 lines | 71 | 120 ✓ |
| Wheel installs + runs from clean venv | no | **yes, gate-enforced** | yes ✓ |
| Suite wall time | ~57 s | ~54 s | ≤120 s ✓ |

Structural: one 2.98 MB module → 34 modules composing the same facade; the
two test monoliths → 33 per-subsystem files; docs journal separated from
reference; `mcp-tools.md` generated from the registry with a drift test;
budgets enforced in every pytest run and only ratchetable downward.

## Trial batteries (like-for-like, Sonnet cold agents)

| Task | Baseline | Final | Δ cost | Notes |
|---|---|---|---|---|
| T1 lore recall | 60k tok, pass | **29.6k, pass** | −50% | under Gate 6's 60k budget with only `start_here` read; deeper answer (evidence provenance, ITU citation) |
| T2 record→pattern→stage→apply→validate | 154k, pass (1 error) | **88.9k, pass** (0 accidental errors) | −42% | probe calls eliminated by generated per-kind docs; independently declined a redundant caveat |
| T3 query handoff | 85k, pass (1 error) | **36.4k, pass** (0 errors) | −57% | caught the layout gate, refused un-asserted paths, read aggregation lineage to flag displacement ≠ path length |
| T4 wrong-hunch (Gate 5, new) | — | 58k, **pass** | — | found the recovery gate from `gates` + docs alone; left others' staged work untouched; flagged its interpretation |

Doc 07 hoped for ≥60% cost reduction; measured −42%…−57% with success and
answer quality strictly up and zero accidental dead-ends. The gap to 60% is
attributable to (a) the schema constant (35k vs 25k end-state, below) and
(b) elective deep doc reading that the agents themselves now rate ~90%
signal. My judgement: the intent of the gate is met; the number is not,
and the remaining levers are listed under Open Items rather than pursued
past the point of usefulness.

## External case study (Phase 7.2)

The study (report: `docs/journal/trials/2026-07-enron-case-study.md`): a
Sonnet agent inherited the **real 31 MB Enron capsule built by the old
loop** (1.2M-row corpus, 4 datasets, 112 observations, 22 claims, 19
patterns) plus the previous team's handoff notes — written against the
dead 89-tool surface — and worked it through an **installed wheel in a
clean venv**, never touching the repo.

Results: the capsule opened and validated cleanly under the new code
(storage schema untouched, as promised); `project_brief` read the real
project at 3,835 chars and surfaced two review queues the old README never
mentioned; the agent answered a population-selection question citing seven
capsule caveats/patterns by IRI; recorded a properly-evidenced
handoff-freshness observation (validation conforming after the write); and
produced a top-senders query handoff whose **six review gates — including
sender-field representativity and deduplication — came from the capsule's
own caveats and patterns**, with the analysis-view SQL correctly flagged
as evidence-cited rather than machine-checked.

Friction: ~20%, all of it translation overhead from the stale notes (old
Python-API examples, `describe_context_slice` → `get_context_graph`,
`draft_query_plan` now a parameter). The agent resolved every mismatch
from the live registry unaided, and found **zero contradictions between
the handoff's data claims and the live graph**. On James's
client-agent-quality question: the capsule's caveat/pattern layer did the
heavy lifting this time — the gates in the handoff are traceable to graph
facts, not agent improvisation, which is the division of labor the product
wants. Two more seeds: the drafted-plan response leaks the internal
`helper: "draft_query_plan"` name; one transient `describe_dataset` error
was flagged honestly and did not reproduce.

## Decisions taken under LATITUDE (the significant ones)

1. Trial agents are Sonnet-class, not frontier — cheaper and representative
   of post-Fable users; all battery comparisons are like-for-like.
2. Program items 3.3 and 5.1 executed as one rebuild (same code/tests).
3. Serialization-internal field metadata (`doxabase_internal`) is the
   mechanism for "Python keeps it, MCP doesn't ship it" — used for slice
   triples/routes, dataset relationship groups, query-context copies of
   dataset fields.
4. Doc 08 folds: `list_docs`→`get_doc`; `record_query_result`→
   `record_observation(kind)`; manifests→`record_map_fact` kinds;
   `load_example_fixtures`→`import_bundle`; **rejected** folding
   `describe_dataset` away (flagship read).
5. R3: `plan_profile_followthrough` served by dry-run spec-dispatch;
   `restage_staged_revision` dispatches single/batch on str|list;
   recovery-session override params default `None` so stored settings win;
   planners must not write (`restage_stale_revisions` rejected under
   dry_run).
6. R4/R5: `describe_revision(aspect="version_diff")` reads `iri` as the
   before-version; `export_preflight(kind="scan_only")` inherits limit 20;
   handoff/fixture imports reclassified as graph-writing (the old effect
   table untruthfully said no-effect).
7. `graph_overview`/`list_entities` default limit 25 with paging.
8. Docs pass: response-shapes/api-reference/workflow/observation-rdf
   deleted or folded; per-kind spec sections generated; the
   direct-record-vs-staged-change rule stated plainly.

## What got worse (honest list)

1. **MCP/Python surface divergence is now real**: the Python facade keeps
   `check_staged_revision_apply`, `draft_query_plan`, `export_kind=` etc.
   Docs label which surface they describe, but it is a new thing to know.
2. Explicit `repair_draft_limit=null` no longer means "unlimited" on the
   MCP door (Python unchanged).
3. Entity/overview listings default to 25 — full sweeps now page.
4. kind/spec tools have opaque JSON schemas by construction; discovery
   moved to generated docs + targeted errors (works, per T2, but a client
   that only reads schemas sees `{kind, spec}`).
5. Six response fields/representations that carried duplicate forms are
   gone; anyone who scripted against the old envelopes must migrate
   (pre-1.0, zero external users — but stated).
6. Old external artifacts (e.g. the Enron handoff notes) reference dead
   tool names; inherited-project sessions must trust the live registry
   (measured in the case study).

## Open items for James

1. **Schema chars 35,136 vs 25,000**: the remainder is anyOf inflation on
   four flat recording tools; closing it means moving their long-tail
   optional params into `spec` objects (doc 08, sweep row). Decide or
   drop the target.
2. **Response end-states**: `describe_dataset` 15.4k vs 12k and
   `describe_query_context` 14.7k vs 12k (relationship-endpoint triple
   representation is the remaining fat); `list_entities` 4.3k vs 4.0k
   (would require dropping `types` from listings — recommend dropping the
   target, not the field).
3. **`staging.py` 4,829 lines vs the 3,000 end-state module target** —
   next split candidate if the target stands.
4. **SPARQL spike (7.3)** — requires your approval; not attempted. The
   25-tool surface reduced the pressure that motivated it; recommend
   deferring until external usage data exists.
5. **Product seeds** from four trial rounds (details in
   `docs/journal/trials/2026-07-gates-5-6.md`): direct caveat→evidence
   link; CURIE-strictness documented for profile metric fields;
   review-reason triplication in draft plans; derivation notes surfaced on
   plan drafts (semantic-mismatch guard); caveat targeting convention
   stated in docs.
6. **The loop rules survive the program** (AGENTS.md): subtraction quota,
   tokens-to-outcome trials, no new routing fields, budget ratchet. The
   scoreboard is the counterweight doc 06 asked for; keep it blocking.

## Program verdict

The review's thesis held: same capability, a fraction of the surface. The
epistemology (observations → patterns → staged map change, reconsideration
not deletion, privacy as review prompts) came through untouched — every
guarantee doc 07 listed under "What Not To Change" still has its tests.
What changed is that a cold agent can now afford to be good at using it.
