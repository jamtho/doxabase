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
