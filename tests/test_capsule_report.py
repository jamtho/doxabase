"""The capsule HTML report: one self-contained file, escaped, banner-carrying."""

from __future__ import annotations

from pathlib import Path

from doxabase.core import DoxaBase
from doxabase.mcp_tools import load_example_fixtures_tool
from doxabase.report import build_capsule_report


def test_report_renders_fixture_capsule(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)
    report = build_capsule_report(db, capsule_name="fixtures")

    assert report.startswith("<!DOCTYPE html>")
    assert "Local-only pending shareability review" in report
    assert "No gates" in report
    assert "AIS Daily Vessel Index" in report
    assert "Patterns" in report
    # self-contained: no external fetches
    assert "http-equiv" not in report
    assert "src=" not in report
    assert 'href="http' not in report


def test_report_escapes_graph_literals(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.record_map_dataset(
        "https://example.test/p#Evil",
        label="<script>alert(1)</script>",
        is_table=True,
    )
    report = build_capsule_report(db)
    assert "<script>alert(1)</script>" not in report
    assert "&lt;script&gt;" in report


def test_report_shows_gates_when_blocked(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_TOKEN_REPORT"
    db.record_map_dataset(
        "https://example.test/p#CredentialNotes",
        label="Credential notes",
        description=f"Synthetic fixture {fake_secret}.",
    )
    report = build_capsule_report(db)
    assert "privacy export review" in report
    assert "blocks export" in report
    assert fake_secret not in report
