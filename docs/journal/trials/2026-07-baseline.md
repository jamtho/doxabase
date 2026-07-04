# Standard Trial Battery — Phase 0 Baseline (2026-07-04)

Baseline run of the battery from `doxabase_design_docs/07-distillation-program.md`
against the pre-distillation surface (89 tools, commit `519f110`). Every later
phase-gate rerun compares against these numbers. Measure-only: nothing found
here was fixed in this wave.

## Method (and deviations from the program's setup)

- Trial agents: **Claude Sonnet** sub-agents, cold, one per task.
  LATITUDE decision: the program imagined frontier trial agents; Sonnet-class
  agents are both cheaper and more representative of the post-Fable agents
  that will actually use DoxaBase. Reruns must also use Sonnet-class agents
  for like-for-like comparison.
- No MCP mount was available in-session, so agents used a bridge script that
  dispatches through FastMCP's own `call_tool` (payloads byte-identical to the
  MCP wire format) and logs per-call char sizes. Agents were forbidden to read
  the repo; docs only via `get_doc`. The full tool-registry JSON (138,353
  chars) is charged to every task as the MCP schema-injection constant.
- Capsules: fresh, both bundled fixtures loaded (805 triples), one per task.
- Context cost = schema constant + all bridge request/response chars, ÷4.
  Harness truncation of oversized shell output may have let agents *see* less
  than an MCP client would be forced to ingest; costs below use full sizes.

## Results

| Task | Success | Bridge calls | Errors | Doc chars | Response chars | Total context cost |
|---|---|---|---|---|---|---|
| T1 lore recall (MMSI) | **yes** | 12 | 0 | 44,461 | 56,514 | 239,749 chars ≈ **60k tokens** |
| T2 record & promote | **yes** (a–e all) | 28 | 1 | 153,849 | 312,871 | 617,714 chars ≈ **154k tokens** |
| T3 query handoff | **yes** | 10 | 1 | 65,985 | 135,178 | 340,031 chars ≈ **85k tokens** |

Success details: T1 cited `ais#caveat_mmsi_identity` + ontology `ais#MMSI`
(`rdfs:seeAlso` ITU-R M.585). T2 recorded 3 observations, 1 pattern, staged
`stage_pattern_promotion` (+10 triples, two new caveats), checked, applied,
`validate_graph(scope="all")` conforms — verified in the capsule. T3 produced
a correctly-provenance'd non-executed DuckDB handoff that caught the
`UnverifiedLayout` gate and refused the un-asserted `index/...` path.

## Friction observed (baseline product signal; for later phases, not fixes now)

1. **Answers arrive on call 1–2; cost arrives everywhere else.** T1's answer
   was in the first `search` response (~1.8k chars); the task still cost 60k
   tokens, dominated by schema injection + a 43KB `list_docs` + verbose
   `describe_resource` envelopes.
2. **Envelope noise quantified by the agents themselves:** T2 estimated 50–60%
   of received bytes were noise (null-padded dataset fields; staged-revision
   conflict/drift/alternative bookkeeping irrelevant to a clean apply). T1:
   ~40%. T3: ~30% (near-duplicate payloads between `describe_dataset` and
   `describe_query_context`, ~90% overlapping).
3. **Schema lies about a joint constraint** (Phase 4 input):
   `record_pattern` accepts `evidence_summary` and `evidence_sources` as
   independently-optional in the JSON schema, but the runtime rejects
   `evidence_summary` without `evidence_sources`/`source_path`. Cold-start trap;
   cost T2 one failed call.
4. **Param-name mismatch** (Phase 4 input): T3 called
   `describe_query_context(dataset_iri=...)` — natural guess, schema says
   `iri`, docs prose says "dataset_iri" informally. One wasted call.
5. **Right tool is findable but buried:** `stage_pattern_promotion` was
   correct and worked first try, but locating it required paging a ~54KB doc.
6. **Docs pay off when scoped:** `get_doc(section=...)` reads were high-signal;
   unscoped pulls (30KB `applying-staged-revisions`) were ~80% irrelevant to a
   clean apply.

## Baseline scoreboard (same commit)

89 tools / 138,353 schema chars; `project_brief` 100,462 chars;
context slice (DailyIndex, defaults) 168,598; `describe_dataset` 30,023;
`core.py` 74,667 lines; `docs/agent/` 1,484,446 bytes.

## Gate-3/4/6 comparison targets

Success ≥ 3/3 at materially lower cost. Program expectation: ≥ 60% reduction
in tokens-to-outcome (T1 ≤ ~24k, T2 ≤ ~62k, T3 ≤ ~34k) with zero increase in
failed calls.
