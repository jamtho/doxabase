from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from doxabase import DoxaBase


ROOT = Path(__file__).resolve().parents[1]


def test_analysis_packet_cli_applies_manifest_file(tmp_path: Path) -> None:
    capsule_path = tmp_path / "capsule.sqlite"
    manifest_path = tmp_path / "analysis-packet.json"
    base = "https://example.test/analysis-cli#"
    packet = f"{base}western_power_packet"
    view = f"{base}western_power_policy"
    artifact = f"{base}western_power_chart"
    recipe = f"{base}attachment_join_recipe"

    manifest_path.write_text(
        json.dumps(
            {
                "format": "doxabase.analysis_packet_manifest.v1",
                "packet_iri": packet,
                "label": "Western power policy packet",
                "summary": (
                    "Reviewed analysis packet for named populations, query "
                    "recipes, artifacts, and follow-up tasks."
                ),
                "evidence_sources": ["scratch://western_power_policy_analysis.md"],
                "analysis_views": [
                    {
                        "iri": view,
                        "label": "Western power policy subcorpus",
                        "row_count_snapshot": 107510,
                        "denominator_description": (
                            "Reviewed message-like rows matching Western power "
                            "policy terms."
                        ),
                        "query_snippets": [
                            {
                                "label": "Subcorpus definition",
                                "query_text": (
                                    "select * from eml_messages "
                                    "where western_policy_match"
                                ),
                                "query_language": "DuckDB SQL",
                                "query_engine": "duckdb",
                            }
                        ],
                    }
                ],
                "query_recipes": [
                    {
                        "iri": recipe,
                        "label": "Join messages to attachments",
                        "query_text": (
                            "select * from eml_messages m "
                            "left join eml_attachments a "
                            "on a.parent_doc_id = m.doc_id"
                        ),
                        "query_language": "DuckDB SQL",
                        "query_engine": "duckdb",
                        "targets": [view],
                    }
                ],
                "artifacts": [
                    {
                        "iri": artifact,
                        "label": "Western power lane chart",
                        "source_path": "scratch://visuals/western_power_policy.png",
                        "artifact_role": "visualization",
                        "media_type": "image/png",
                        "image_width": 1200,
                        "image_height": 800,
                        "supports": [view],
                    }
                ],
                "followup_tasks": [
                    {
                        "label": "Inspect Western power policy lane",
                        "task_text": (
                            "Trace the reviewed Western power lane from the "
                            "packet artifacts before reporting counts."
                        ),
                        "priority": "high",
                        "targets": [view],
                    }
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "doxabase.analysis_packet",
            "--capsule",
            str(capsule_path),
            "--manifest",
            str(manifest_path),
            "--overwrite",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["manifest_format"] == "doxabase.analysis_packet_manifest.v1"
    assert payload["packet_iri"] == packet
    assert payload["analysis_view_iris"] == [view]
    assert payload["artifact_iris"] == [artifact]
    assert payload["query_recipe_iris"] == [recipe]
    assert payload["analysis_view_count"] == 1
    assert payload["artifact_count"] == 1
    assert payload["query_recipe_count"] == 1
    assert payload["followup_task_count"] == 1
    assert payload["validation_conforms"] is True
    assert payload["validation_result_count"] == 0

    with DoxaBase.open_readonly(capsule_path) as db:
        assert db.describe_query_context(view).readiness == "logical_analysis_view"
        context = db.describe_context_slice([packet], profile="resource_brief")
        assert view in {resource.iri for resource in context.resources}
        assert recipe in {resource.iri for resource in context.resources}


def test_analysis_packet_cli_rejects_wrong_manifest_format(tmp_path: Path) -> None:
    capsule_path = tmp_path / "capsule.sqlite"
    manifest_path = tmp_path / "analysis-packet.json"
    manifest_path.write_text(
        json.dumps(
            {
                "format": "doxabase.profile_to_capsule_manifest.v1",
                "packet_iri": "https://example.test/analysis-cli#packet",
                "summary": "Wrong manifest type.",
                "evidence_sources": ["scratch://packet.md"],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "doxabase.analysis_packet",
            "--capsule",
            str(capsule_path),
            "--manifest",
            str(manifest_path),
            "--overwrite",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "analysis-packet manifest format must be" in result.stderr
    assert not capsule_path.exists()
