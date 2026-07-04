# External Case Study — Inherited Enron Capsule, Installed Wheel (2026-07-05)

Program Phase 7.2. A Sonnet client agent inherited the real Enron analysis
project produced by the pre-distillation loop: the 31 MB capsule
(1.2M-row corpus; 4 datasets, 60 columns, 112 observations, 22 claims,
19 patterns, 58 evidence resources) plus the previous team's handoff notes
(`/home/codex/enron-doxabase-handoff`, durable copy) — notes written
against the dead 89-tool surface. The capsule was driven exclusively
through an **installed wheel in a clean venv** via the logged bridge; the
agent could read the handoff notes freely but never the repo.

## Session goals and outcomes (all achieved)

1. **Orientation**: `project_brief` (3,835 chars on this real capsule)
   plus `validate_graph(scope="all")` (conforms, before and after the
   session's write), zero staged work/drift, scanner-clean. The brief
   surfaced two non-blocking queues (`profile_review: 4`,
   `query_plan_handoff: 4`) that the old README's snapshot never
   mentioned — the state surface catching real backlog.
2. **Lore question** (which table for time-series; date pitfalls):
   answered with seven capsule resources cited by IRI (date-plausibility
   caveat and outlier claims, the calendar-spike caveat + stratification
   pattern, message-like population caveat + pattern, parallel-
   representations caveat, EML-only subset caveat).
3. **Write-back**: recorded a properly-evidenced handoff-freshness
   observation (`.../observation/eadcc0c0-...`), evidence citing the
   README, the capsule, and the five verification calls; validation
   conformed after the write.
4. **Query handoff** (top-10 senders, Oct 2001, recommended population):
   non-executed DuckDB draft against the capsule-asserted
   `s3://enron-emails/eml_messages.parquet` candidate, with **six explicit
   review gates** — provenance of view-SQL (evidence-cited, not
   machine-checked), runtime endpoint/credentials, candidate-intent review
   (4 ready peers), sender-field representativity (`from_email` fill-rate
   caveats, with the XML alternative named), deduplication (dedup-cluster
   caveat/pattern), and human sign-off. Gates G3/G4 came from the
   capsule's own caveats and patterns — graph facts, not agent
   improvisation.

## Old-notes vs live-surface friction (the measured question)

~20% of session effort was translation overhead; ~80% signal. Every
mismatch was resolved from the live registry unaided:

- README quick-start assumed the Python API and a dead checkout path →
  agent used the MCP surface (same names, different transport).
- `describe_context_slice` (notes) → `get_context_graph` (live).
- "call `describe_query_context` and `draft_query_plan`" (notes) → one
  tool with `plan_candidate=`; the agent confirmed the mapping by calling
  both modes.
- **Zero contradictions** between the notes' data claims (row counts,
  caveats, populations, storage facts) and the live graph.

On the client-agent-quality confound James raised: this run suggests the
capsule now carries more of the weight — the handoff's review gates trace
to recorded caveats/patterns rather than agent judgement alone, which is
the intended division of labor.

## Compatibility result

The pre-distillation capsule opened, validated, queried, and accepted
writes under the post-distillation wheel with no migration — the storage
schema promise of doc 07 held end-to-end on real data.

## New seeds

- Drafted-plan responses leak the internal `helper: "draft_query_plan"`
  label (cosmetic; rename with the next envelope touch).
- One transient `describe_dataset` failure (46-char error between two
  identical successes) — not reproduced; watch for recurrence under
  process-per-call bridges.
- The code-owner feedback items in the old notes (relationship enum
  ergonomics, export-validation gate) remain open per those notes; not
  re-verified this session.
