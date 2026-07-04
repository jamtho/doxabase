from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from doxabase import DoxaBase


ROOT = Path(__file__).resolve().parents[1]

PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
    "0000000c49444154789c6360600000000400010d0a2db40000000049454e44ae426082"
)


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
        context = db.get_context_graph([packet], profile="resource_brief")
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


def test_analysis_packet_cli_scaffolds_sidecar_manifest(tmp_path: Path) -> None:
    sidecar_dir = tmp_path / "handoff"
    visuals_dir = sidecar_dir / "visuals"
    visuals_dir.mkdir(parents=True)
    (sidecar_dir / "analysis_views.md").write_text(
        "# Views\n\nReviewed logical views.\n",
        encoding="utf-8",
    )
    (sidecar_dir / "topic_counts.json").write_text(
        json.dumps({"rows": 12}),
        encoding="utf-8",
    )
    (visuals_dir / "lane_chart.png").write_bytes(PNG_1X1)
    manifest_path = tmp_path / "analysis-packet-scaffold.json"
    packet_iri = "https://example.test/analysis-cli#packet"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "doxabase.analysis_packet",
            "--init-manifest",
            "--sidecar-dir",
            str(sidecar_dir),
            "--packet-iri",
            packet_iri,
            "--summary",
            "Reviewed sidecar scaffold for Enron analysis artifacts.",
            "--label",
            "Enron analysis sidecars",
            "--hash-artifacts",
            "--output",
            str(manifest_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    scaffold_summary = json.loads(result.stdout)
    assert scaffold_summary["manifest_path"] == str(manifest_path)
    assert scaffold_summary["artifact_count"] == 3
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["format"] == "doxabase.analysis_packet_manifest.v1"
    assert manifest["packet_iri"] == packet_iri
    assert manifest["analysis_views"] == []
    assert manifest["query_recipes"] == []
    assert manifest["followup_tasks"] == []
    artifacts = {artifact["source_path"]: artifact for artifact in manifest["artifacts"]}
    assert artifacts["analysis_views.md"]["media_type"] == "text/markdown"
    assert artifacts["topic_counts.json"]["media_type"] == "application/json"
    chart = artifacts["visuals/lane_chart.png"]
    assert chart["artifact_role"] == "visualization"
    assert chart["media_type"] == "image/png"
    assert chart["byte_size"] == len(PNG_1X1)
    assert chart["content_hash"].startswith("sha256:")
    assert chart["image_width"] == 1
    assert chart["image_height"] == 1

    capsule_path = tmp_path / "capsule.sqlite"
    apply_result = subprocess.run(
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
    applied = json.loads(apply_result.stdout)
    assert applied["packet_iri"] == packet_iri
    assert applied["artifact_count"] == 3
    assert applied["validation_conforms"] is True


def test_analysis_packet_cli_scaffold_handles_unknown_and_empty_sidecars(
    tmp_path: Path,
) -> None:
    sidecar_dir = tmp_path / "sidecars"
    sidecar_dir.mkdir()
    (sidecar_dir / "artifact.unknownext").write_text(
        "opaque sidecar",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "doxabase.analysis_packet",
            "--init-manifest",
            "--sidecar-dir",
            str(sidecar_dir),
            "--packet-iri",
            "https://example.test/analysis-cli#unknown_packet",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    manifest = json.loads(result.stdout)
    artifact = manifest["artifacts"][0]
    assert artifact["source_path"] == "artifact.unknownext"
    assert artifact["media_type"] == "application/octet-stream"
    assert artifact["artifact_role"] == "sidecar"
    assert "content_hash" not in artifact

    empty_dir = tmp_path / "empty-sidecars"
    empty_dir.mkdir()
    empty_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "doxabase.analysis_packet",
            "--init-manifest",
            "--sidecar-dir",
            str(empty_dir),
            "--packet-iri",
            "https://example.test/analysis-cli#empty_packet",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert empty_result.returncode == 1
    assert "No sidecar files found" in empty_result.stderr


def test_analysis_packet_cli_scaffold_extracts_markdown_create_views(
    tmp_path: Path,
) -> None:
    sidecar_dir = tmp_path / "handoff"
    sidecar_dir.mkdir()
    (sidecar_dir / "analysis_views.md").write_text(
        """
# Recommended Views

```sql
create or replace view eml_messages_plausible_1997_2004 as
select *
from eml_messages
where date >= timestamp '1997-01-01'
  and date < timestamp '2005-01-01';
```

Observed row count: 1,210,548.

```duckdb-sql
create view eml_messages_plausible_message_like as
select *
from eml_messages_plausible_1997_2004
where folder_family not in ('calendar', 'contacts', 'meetings');
```

Observed row count: 980,561.

```duckdb-sql
create or replace view eml_messages as
select *
from read_parquet('s3://example/eml_messages.parquet');
```

```python
print("not a view")
```
""".lstrip(),
        encoding="utf-8",
    )
    packet_iri = "https://example.test/analysis-cli#packet"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "doxabase.analysis_packet",
            "--init-manifest",
            "--sidecar-dir",
            str(sidecar_dir),
            "--packet-iri",
            packet_iri,
            "--extract-markdown-views",
            "--analysis-view-base-iri",
            "https://example.test/enron-analysis#",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    manifest = json.loads(result.stdout)
    assert [view["iri"] for view in manifest["analysis_views"]] == [
        "https://example.test/enron-analysis#eml_messages_plausible_1997_2004",
        "https://example.test/enron-analysis#eml_messages_plausible_message_like",
    ]
    assert [view["row_count_snapshot"] for view in manifest["analysis_views"]] == [
        1210548,
        980561,
    ]
    assert manifest["analysis_views"][0]["denominator_row_count_snapshot"] == 1210548
    first_snippet = manifest["analysis_views"][0]["query_snippets"][0]
    second_snippet = manifest["analysis_views"][1]["query_snippets"][0]
    assert "create or replace view eml_messages_plausible_1997_2004" in (
        first_snippet["query_text"]
    )
    assert first_snippet["query_language"] == "SQL"
    assert first_snippet["query_engine"] is None
    assert second_snippet["query_language"] == "DuckDB SQL"
    assert second_snippet["query_engine"] == "duckdb"
    assert "TODO: Review" in manifest["analysis_views"][0]["description"]

    capsule_path = tmp_path / "capsule.sqlite"
    manifest_path = tmp_path / "analysis-packet.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    blocked_apply = subprocess.run(
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
    assert blocked_apply.returncode == 1
    assert "review placeholder field" in blocked_apply.stderr
    assert "analysis_views[0].description" in blocked_apply.stderr

    apply_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "doxabase.analysis_packet",
            "--capsule",
            str(capsule_path),
            "--manifest",
            str(manifest_path),
            "--overwrite",
            "--allow-review-placeholders",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    applied = json.loads(apply_result.stdout)
    assert applied["analysis_view_count"] == 2
    assert applied["validation_conforms"] is True
