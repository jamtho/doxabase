# DoxaBase MCP Surface V2 (Phase 4 Mapping)

**Date**: 2026-07-04. **Status**: authoritative mapping for program Phase 4
(see `07-distillation-program.md`). Commit this mapping before the first tool
merge; update it in the same wave as any LATITUDE deviation.

Every one of the 89 pre-distillation tools maps to exactly one row below (or
to explicit removal). Old tools are **deleted the same wave** their
replacement lands — no aliases, no deprecation wrappers (Loop Rule 5).

## Conventions for the new surface

- **Kind dispatch**: family tools take a `kind` parameter plus a documented
  `spec` object per kind. Validation errors must name the missing/invalid
  fields *for that kind* (the targeted-error style of the old relationship
  column errors is the model).
- **`dry_run=True`** replaces every read-only `draft_*` / `check_*` planning
  call: same response shape as the real call, nothing written.
- **Docstrings ≤ 600 chars per tool**; total schema budget 25,000 chars.
- **Baseline-trial trap fixes** (from `docs/journal/trials/2026-07-baseline.md`):
  1. Joint constraints must be visible: `record_pattern`'s
     "evidence_summary requires evidence_sources or source_path" must appear
     in the parameter description AND fail with a targeted error naming both
     fields. Audit every tool for hidden joint constraints while merging.
  2. Argument naming is uniform: every describer takes `iri`; docs prose must
     use the exact schema names.
- All responses obey the Phase 3 envelope conventions (absent==null==empty;
  suggestions ≤ 5; graph content as TriG, not JSON triple arrays).

## Target surface (25 tools)

| # | Tool | Absorbs (old → how) |
|---|------|----------------------|
| 1 | `get_doc` | `list_docs` → call with no `doc_id` returns the doc list |
| 2 | `project_brief` | — (shrinks in Phase 5: gates/queues/one-liners) |
| 3 | `graph_overview` | — |
| 4 | `list_entities` | — |
| 5 | `search` | `search_staged_patch_payloads` → `scope="staged_patches"` |
| 6 | `describe_resource` | `describe_pattern`, `describe_profile_run`, `describe_analysis_view`, `describe_assertion_support` → auto-detect resource type; `aspect` param for support/profile-run views |
| 7 | `describe_dataset` | — (flagship; keeps its name) |
| 8 | `describe_query_context` | `draft_query_plan` → `plan_candidate=` selector params |
| 9 | `get_context_graph` | `describe_context_slice` → renamed in Phase 3.2; TriG payload default |
| 10 | `record_observation` | `record_claim_observation` → `kind="claim"`; `record_query_result` → `kind="query_result"` |
| 11 | `record_pattern` | — (fix trap 1) |
| 12 | `record_claim_reconsideration` | — |
| 13 | `record_profile` | `record_dataset_profile` → `kind="dataset"`; `record_column_profile` → `kind="column"`; `record_profile_bundle` → `kind="bundle"`; `record_domain_network_profile` → `kind="domain_network"` |
| 14 | `record_map_fact` | all 11 `record_map_*` → `kind="dataset"/"column"/"caveat"/"relationship"/"storage_access"/"physical_layout"/"partition_scheme"/"asset_transform"/"analysis_view"/"analysis_view_bundle"/"table_bundle"`; `record_analysis_packet` → `kind="analysis_packet"`; `record_profile_to_capsule_manifest` → `kind="profile_manifest"`; `record_profiled_parquet_table` → `kind="profiled_parquet_table"` (CLIs stay) |
| 15 | `record_graph_revision` | — |
| 16 | `stage_revision` | `stage_graph_revision` → `kind="graph"`; `stage_map_assertion_change` → `kind="map_assertion"`; `stage_systematisation` → `kind="systematisation"`; `stage_pattern_promotion` → `kind="pattern_promotion"`; `stage_profile_map_updates` → `kind="profile_map_updates"`; `stage_query_storage_access_repair` → `kind="query_storage_access_repair"`; `stage_query_physical_layout_repair` → `kind="query_physical_layout_repair"`; `record_staged_revision_review_decision` → `kind="review_decision"`. `dry_run=True` absorbs: `draft_map_assertion_change`, `draft_profile_map_updates`, `plan_profile_followthrough` (its advisory content joins the profile_map_updates dry-run response), `draft_systematisation_shared_context_rerun`, `draft_query_evidence_storage_overlay` (`kind="query_evidence_overlay"`) |
| 17 | `apply_staged_revision` | `check_staged_revision_apply` → `dry_run=True` |
| 18 | `restage_staged_revision` | `restage_staged_revisions` → list param (single IRI = list of one); `draft_staged_revision_rebase` → `dry_run=True` |
| 19 | `plan_staged_revision_recovery` | `start_staged_revision_recovery_session` → `start_session=True`; `describe_staged_revision_recovery_session` → `session_iri=` |
| 20 | `list_revisions` | `list_graph_revisions` → `kind="graph"`; `list_graph_versions` → `kind="versions"`; `list_resource_revisions` → `kind="resource"` |
| 21 | `describe_revision` | `describe_graph_revision` (default), `describe_staged_revision` → auto-detect staged IRIs; `describe_applied_revision_diff` → `aspect="applied_diff"`; `describe_graph_version_diff` → `aspect="version_diff"`; `describe_revision_lineage` → `aspect="lineage"`; `describe_resource_revision_lineage` → `aspect="resource_lineage"`; `describe_revision_snapshot_evidence` → `aspect="snapshot_evidence"`; `describe_revision_graph_snapshot` → `aspect="graph_snapshot"` |
| 22 | `export_preflight` | `scan_sensitive_literals` → `kind="scan_only"`; `preflight_context_slice_export` → `kind="context_slice"` |
| 23 | `export_bundle` | `export_trig` → `kind="trig"`; `export_graph` → `kind="graph"`; `export_context_slice` → `kind="context_slice"`; `export_staged_revision`/`export_staged_revisions` → `kind="staged_revisions"` (list param); `export_profile_insight_review_bundle` → `kind="profile_insight_review"`; `export_revision_snapshots` → `kind="revision_snapshots"`; `export_handoff_bundle` → `kind="handoff"` |
| 24 | `import_bundle` | `import_trig` → `kind="trig"`; `import_revision_snapshots` → `kind="revision_snapshots"`; `import_handoff_bundle` → `kind="handoff"`; `load_example_fixtures` → `kind="example_fixtures"` (scratch-capsule guard stays) |
| 25 | `validate_graph` | — |

**Removed from MCP entirely** (Python-only maintenance, program item 4.5):
`replace_graph_triples`. (`clear_graph` was already Python-only.)

## Decisions taken under LATITUDE (vs. doc 07's starting proposal)

Doc 07 sketched 29 rows and asked for folds to reach ≤ 25. Chosen folds:

1. `list_docs` → `get_doc` (no-arg call lists). Cheapest possible merge.
2. `record_query_result` → `record_observation(kind="query_result")`: it
   writes observation+evidence rows like its siblings; one recording door for
   point-in-time findings.
3. `record_manifest` (doc 07 #17) → `record_map_fact` kinds: manifests are
   bulk map+evidence writers; same door as single map facts, same review
   posture. CLIs (`python -m doxabase.parquet_manifest` etc.) are unaffected.
4. `load_example_fixtures` → `import_bundle(kind="example_fixtures")`.
5. **Rejected fold**: `describe_dataset` into `describe_resource`. The
   baseline trials leaned on `describe_dataset` as the flagship read; burying
   it costs discoverability worth more than one slot.
6. `export_preflight` stays its own tool (doc 07 hinted it could fold into
   `export_bundle`): the privacy posture ("scanner-clean is a review prompt")
   deserves a visible front door, and it absorbs the standalone scanner.

## Implementation order (waves)

Merge family by family, deleting old tools in the same wave, keeping the full
gate green each wave:

1. **DONE (2026-07-05)** Reads: `get_doc`, `search`, `describe_resource`
   (rows 1, 5, 6). 89 → 83 tools. Implementation notes: `describe_resource`
   gained `aspect` ("auto" type-detects patterns/analysis views;
   "profile_run" takes `evidence_iri`; "assertion_support" takes
   `predicate`/`object*`, iri = subject); suggestion emitters across core
   now produce the merged names, and `revisions.find_exact_action` matches
   on `args_aspect` rather than the old tool name.
2. **DONE (2026-07-05)** Recording: rows 10, 13, 14 (83 → 65 tools — the
   original "−22" estimate here was a miscount; schema
   chars 135,986 → 81,816). `_dispatch_kind` in `mcp_tools.py` is the
   generic kind-validator (targeted errors naming valid/missing fields per
   kind); absorbed `*_tool` functions remain as dispatch targets.
3. **DONE (2026-07-05)** Staging: rows 16–19 (65 → 48 tools — the "−13"
   estimate was a miscount; the rows absorb 18 registrations and add one
   door). LATITUDE notes: profile followthrough advisory content is served
   by `stage_revision(kind="profile_map_updates", dry_run=True)` dispatching
   on spec content; `restage_staged_revision` dispatches single/batch on
   str/list `revision_iris`; recovery-session override params default None
   so stored session settings win in describe mode; explicit
   `repair_draft_limit=null` no longer means unlimited on the MCP door
   (Python API unchanged). `query_evidence_overlay` is a dry_run-only kind.
4. Revisions reads: rows 20–21 (−9 tools).
5. Export/import: rows 22–24 (−12 tools).
6. Sweep (48 → 25 with rows 4/5): row 8 fold, removals, docstring budget pass, schema-char budget
   pass, scoreboard ceilings to ≤ 25 tools / ≤ 25,000 chars; battery rerun.

Each wave updates: `mcp_tools.py`, `mcp_server.py`, `tests/mcp/`, examples,
and every doc reference to a renamed tool.
