from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def _run_example(script_name: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["DOXABASE_EXAMPLE_RUN_ROOT"] = str(tmp_path / "example-runs")
    return subprocess.run(
        [sys.executable, str(ROOT / "examples" / script_name)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


def test_adversarial_field_trial_example_runs(tmp_path: Path) -> None:
    result = _run_example("adversarial-field-trial.py", tmp_path)
    report_path = Path(result.stdout.strip())
    report = report_path.read_text(encoding="utf-8")

    assert report_path == (
        tmp_path / "example-runs" / "doxabase-adversarial-field-trial" / "report.md"
    )
    assert "Pattern-first hunch" in report
    assert "Premature map caveat candidate" in report
    assert "staged patches are not applied to the current graphs" in report
    assert "severity must be Minor, Moderate, or Severe" in report


def test_first_workflow_example_runs(tmp_path: Path) -> None:
    result = _run_example("first-workflow.py", tmp_path)
    output = result.stdout

    assert "# DoxaBase First Workflow" in output
    assert "Loaded fixture triples:" in output
    assert "Key counts:" in output
    assert "Tables:" in output
    assert "Query decision:" in output
    assert "Next action: doxabase.draft_query_plan" in output
    assert "docs/agent/query-planning.md#ais-dailyindex-question-to-handoff-gap" in (
        output
    )
    assert "Search matches:" in output
    assert "Recorded observation:" in output
    assert "Validation conforms: True" in output


def test_profile_frontier_workflow_example_runs(tmp_path: Path) -> None:
    result = _run_example("profile-frontier-workflow.py", tmp_path)
    output = result.stdout

    assert "# DoxaBase Profile Frontier Workflow" in output
    assert "Loaded fixture triples:" in output
    assert (
        "Baseline profile queues: {'profile_observations': 0, "
        "'profile_evidence': 0"
        in output
    )
    assert "Profile observations: 3" in output
    assert "Profile draft recommendations: 3" in output
    assert "Representative recommendations: [0, 1, 2]" in output
    assert "Staged profile revision:" in output
    assert "Recovery queue counts: {'apply_after_review': 1}" in output
    assert "Validation conforms: True" in output


def test_profile_to_capsule_cookbook_example_runs(tmp_path: Path) -> None:
    result = _run_example("profile-to-capsule-cookbook.py", tmp_path)
    output = result.stdout

    assert "# DoxaBase Profile-To-Capsule Cookbook" in output
    assert "Table bundle columns: 5" in output
    assert "Profile observations: 6" in output
    assert "Profile draft recommendations: 4" in output
    assert "Analysis view readiness: logical_analysis_view" in output
    assert "Table query readiness: ready_for_query_planning" in output
    assert "Source validation conforms: True" in output
    assert "Export preflight decision: clean_by_scanner_only" in output
    assert "Handoff scanner clean: True" in output
    assert "Handoff shareability status: required_not_completed" in output
    assert "Revision snapshots exported: 7" in output
    assert "Readonly source counts match: True" in output
    assert "Imported snapshot evidence complete: True" in output
    assert "Receiver validation conforms: True" in output
    assert "Receiver counts match source: True" in output
    assert "Receiver table readiness: ready_for_query_planning" in output
    assert "Receiver analysis view readiness: logical_analysis_view" in output


def test_analysis_packet_manifest_smoke_example_runs(tmp_path: Path) -> None:
    result = _run_example("analysis-packet-manifest-smoke.py", tmp_path)
    output = result.stdout

    assert "# DoxaBase Analysis Packet Manifest Smoke" in output
    assert "Source table before packet: ready_for_query_planning" in output
    assert "Manifest format: doxabase.analysis_packet_manifest.v1" in output
    assert "Analysis views: 2" in output
    assert "Artifacts: 3" in output
    assert "Query recipes: 2" in output
    assert "Follow-up tasks: 2" in output
    assert "Pattern recorded: True" in output
    assert "View readiness: ['logical_analysis_view', 'logical_analysis_view']" in (
        output
    )
    assert "View query snippets: [2, 1]" in output
    assert "Source table after packet: ready_for_query_planning" in output
    assert "Validation conforms: True" in output


def test_rich_profile_manifest_smoke_example_runs(tmp_path: Path) -> None:
    result = _run_example("rich-profile-manifest-smoke.py", tmp_path)
    output = result.stdout

    assert "# DoxaBase Rich Profile Manifest Smoke" in output
    assert "Scaffold tables: 1" in output
    assert "Reviewed manifest tables: 1" in output
    assert "Caveats: 3" in output
    assert "Profile observations: 10" in output
    assert "Analysis views: 2" in output
    assert "Domain network profiles: 1" in output
    assert "Domain network observations: 4" in output
    assert "Dataset columns: 5" in output
    assert "Profile run returned: 6/6" in output
    assert "Domain profile run returned: 4/4" in output
    assert "Profile draft recommendations: 2" in output
    assert "Reviewed layout status: rc:VerifiedByListingLayout" in output
    assert "Table query readiness: ready_for_query_planning" in output
    assert "Table query issues: []" in output
    assert "Analysis view readiness: logical_analysis_view" in output
    assert "Analysis view snippets: 2" in output
    assert "Domain view caveats: 1" in output
    assert "Validation conforms: True" in output


def test_staged_semantic_repair_smoke_example_runs(tmp_path: Path) -> None:
    result = _run_example("staged-semantic-repair-smoke.py", tmp_path)
    output = result.stdout

    assert "# DoxaBase Staged Semantic Repair Smoke" in output
    assert "Initial mutation frontier count: 3" in output
    assert "Initial requires recheck after each apply: True" in output
    assert "Post-apply recheck subset count: 2" in output
    assert "Recovery queues: {'repair_or_replace': 1, 'restage_after_review': 1}" in (
        output
    )
    assert "Helper mutation actions: ['doxabase.stage_map_assertion_change']" in output
    assert "same_slot_replacement" in output
    assert "Independent successor status: ready" in output
    assert "Repair draft: drafted / same_slot_replacement" in output
    assert "Repair successor status: ready / Apply only after semantic review" in output
    assert "Alternative gate: alternative_to_applied_source" in output
    assert "Alternative semantic review required: True" in output
    assert "Final semantic review counts: {'apply_after_review': 1}" in output
    assert "Validation conforms: True" in output


def test_local_csv_query_smoke_example_runs(tmp_path: Path) -> None:
    result = _run_example("local-csv-query-smoke.py", tmp_path)
    output = result.stdout

    assert "# DoxaBase Local CSV Query Smoke" in output
    assert "Rows checked: 6" in output
    assert (
        "Header checked: order_id, status, amount_cents, customer_state, order_date"
        in output
    )
    assert "Query readiness: ready_for_query_planning" in output
    assert "Draft handoff: execution_attempt_ready" in output
    assert "Ready for execution: True" in output
    assert "Scan function: read_csv_auto" in output
    assert "Engine used: python-csv" in output
    assert "Evidence status: succeeded" in output
    assert "Evidence engine: python-csv" in output
    assert "Validation conforms: True" in output


def test_missing_metadata_query_repair_smoke_example_runs(tmp_path: Path) -> None:
    result = _run_example("missing-metadata-query-repair-smoke.py", tmp_path)
    output = result.stdout

    assert "# DoxaBase Missing Metadata Query Repair Smoke" in output
    assert "Baseline readiness: insufficient_metadata" in output
    assert "Baseline repair group: missing_storage_access" in output
    assert "Storage staged check: ready / review_then_apply" in output
    assert "After storage readiness: needs_review" in output
    assert "Next repair group: missing_physical_layout" in output
    assert "Layout staged check: ready / review_then_apply" in output
    assert "Final readiness: ready_for_query_planning" in output
    assert "Draft handoff: execution_attempt_ready" in output
    assert "Ready for execution: True" in output
    assert "Scan function: read_csv_auto" in output
    assert "Validation conforms: True" in output


def test_query_evidence_storage_overlay_smoke_example_runs(tmp_path: Path) -> None:
    result = _run_example("query-evidence-storage-overlay-smoke.py", tmp_path)
    output = result.stdout

    assert "# DoxaBase Query Evidence Storage Overlay Smoke" in output
    assert "Baseline readiness: insufficient_metadata" in output
    assert "Baseline candidates: 0" in output
    assert "Recorded evidence status: succeeded" in output
    assert "Profile inspection action: doxabase.describe_profile_run" in output
    assert (
        "Overlay action tool: doxabase.draft_query_evidence_storage_overlay"
        in output
    )
    assert "Route candidate kind: local_path_from_query_evidence" in output
    assert "Candidate path templates: ['orders.csv']" in output
    assert (
        "Candidate argument keys: "
        "file_format, location_kind, path_templates, storage_protocol, storage_root"
        in output
    )
    assert "Draft result: query_evidence_storage_overlay_draft" in output
    assert "Draft source readiness: insufficient_metadata" in output
    assert "Draft validation conforms: True" in output
    assert "Still before apply readiness: insufficient_metadata" in output
    assert "Staged overlay check: ready / review_then_apply" in output
    assert "Applied overlay: 1 patch" in output
    assert "Final readiness: ready_for_query_planning" in output
    assert "Draft handoff: execution_attempt_ready" in output
    assert "Ready for execution: True" in output
    assert "Scan function: read_csv_auto" in output
    assert "Validation conforms: True" in output


def test_ais_query_overlay_smoke_example_runs(tmp_path: Path) -> None:
    result = _run_example("ais-query-overlay-smoke.py", tmp_path)
    output = result.stdout

    assert "# DoxaBase AIS Query Overlay Smoke" in output
    assert "Baseline readiness: needs_review" in output
    assert "Overlay repair: remove_stale_partition_scheme_link (1 pending)" in output
    assert "Staged repair check: ready / review_then_apply" in output
    assert "Applied repair: 1 patch, 1 triple removed" in output
    assert "Repaired readiness: ready_for_query_planning" in output
    assert "Draft handoff: runtime_resolution_required" in output
    assert "Ready for execution: False" in output
    assert "Scan function: read_parquet" in output
    assert "URI template: s3://ais-noaa/index/*/*.parquet" in output
    assert "Required bindings: []" in output
    assert "Execution blockers: ['runtime_resolution_required']" in output
    assert "Validation conforms: True" in output
