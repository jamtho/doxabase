from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_adversarial_field_trial_example_runs() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "examples" / "adversarial-field-trial.py")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    report_path = Path(result.stdout.strip())
    report = report_path.read_text(encoding="utf-8")

    assert report_path == Path("/tmp/doxabase-adversarial-field-trial-report.md")
    assert "Pattern-first hunch" in report
    assert "Premature map caveat candidate" in report
    assert "staged patches are not applied to the current graphs" in report
    assert "severity must be Minor, Moderate, or Severe" in report


def test_first_workflow_example_runs() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "examples" / "first-workflow.py")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    output = result.stdout

    assert "# DoxaBase First Workflow" in output
    assert "Loaded fixture triples:" in output
    assert "Key counts:" in output
    assert "Tables:" in output
    assert "Query decision:" in output
    assert "Next action: draft_query_plan(" in output
    assert "docs/agent/query-planning.md#ais-dailyindex-question-to-handoff-gap" in (
        output
    )
    assert "Search matches:" in output
    assert "Recorded observation:" in output
    assert "Validation conforms: True" in output


def test_profile_frontier_workflow_example_runs() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "examples" / "profile-frontier-workflow.py")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

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


def test_staged_semantic_repair_smoke_example_runs() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "staged-semantic-repair-smoke.py"),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    output = result.stdout

    assert "# DoxaBase Staged Semantic Repair Smoke" in output
    assert "Initial mutation frontier count: 3" in output
    assert "Initial requires recheck after each apply: True" in output
    assert "Post-apply recheck subset count: 2" in output
    assert "Recovery queues: {'repair_or_replace': 1, 'restage_after_review': 1}" in (
        output
    )
    assert "Helper mutation actions: ['stage_map_assertion_change']" in output
    assert "same_slot_replacement" in output
    assert "Independent successor status: ready" in output
    assert "Repair draft: drafted / same_slot_replacement" in output
    assert "Repair successor status: ready / Apply only after semantic review" in output
    assert "Alternative gate: alternative_to_applied_source" in output
    assert "Alternative semantic review required: True" in output
    assert "Final semantic review counts: {'apply_after_review': 1}" in output
    assert "Validation conforms: True" in output


def test_local_csv_query_smoke_example_runs() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "examples" / "local-csv-query-smoke.py")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

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


def test_ais_query_overlay_smoke_example_runs() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "examples" / "ais-query-overlay-smoke.py")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

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
