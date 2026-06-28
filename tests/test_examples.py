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
