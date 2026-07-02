from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from doxabase import DoxaBase


ROOT = Path(__file__).resolve().parents[1]


def test_profile_to_capsule_cli_applies_manifest_file(tmp_path: Path) -> None:
    capsule_path = tmp_path / "capsule.sqlite"
    manifest_path = tmp_path / "profile-manifest.json"
    base = "https://example.test/profile-cli#"
    table = f"{base}orders"
    view = f"{base}paid_orders"
    manifest_path.write_text(
        json.dumps(
            {
                "format": "doxabase.profile_to_capsule_manifest.v1",
                "table_defaults": {
                    "storage_protocol": "rc:LocalFilesystemStorage",
                    "access_mode": "rc:ReadOnlyAccess",
                    "location_kind": "directory",
                    "storage_root": str(tmp_path),
                    "layout_verification_status": "rc:VerifiedByQueryLayout",
                    "physical_layout_verification_status": (
                        "rc:VerifiedByQueryLayout"
                    ),
                    "sample_method": "Reviewed CLI manifest fixture.",
                },
                "tables": [
                    {
                        "iri": table,
                        "label": "Orders",
                        "dataset_summary": (
                            "Orders profile captured reviewed counts."
                        ),
                        "evidence_summary": "Reviewed Orders profile manifest.",
                        "evidence_sources": ["scratch://profiles/orders.json"],
                        "path_templates": ["orders/current.parquet"],
                        "storage_path_templates": ["orders/current.parquet"],
                        "row_count": 6,
                        "columns": [
                            {
                                "column_name": "order_id",
                                "physical_type": "rc:Integer",
                                "null_count": 0,
                            },
                            {
                                "column_name": "status",
                                "physical_type": "rc:Varchar",
                                "null_count": 0,
                                "distinct_count": 2,
                            },
                        ],
                    }
                ],
                "analysis_views": [
                    {
                        "iri": view,
                        "label": "Paid orders",
                        "source_datasets": [table],
                        "row_count_snapshot": 3,
                        "query_snippets": [
                            {
                                "query_text": (
                                    "select * from orders where status = 'paid'"
                                ),
                                "query_language": "DuckDB SQL",
                                "query_engine": "duckdb",
                            }
                        ],
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
            "doxabase.profile_to_capsule",
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
    assert payload["manifest_format"] == "doxabase.profile_to_capsule_manifest.v1"
    assert payload["table_iris"] == [table]
    assert payload["analysis_view_iris"] == [view]
    assert payload["table_count"] == 1
    assert payload["analysis_view_count"] == 1
    assert payload["domain_network_profile_count"] == 0
    assert payload["domain_network_profile_observation_count"] == 0
    assert payload["domain_network_profile_evidence_iris"] == []
    assert payload["domain_network_pattern_iris"] == []
    assert payload["profile_observation_count"] == 3
    assert payload["query_readiness_counts"] == {"ready_for_query_planning": 1}
    assert payload["validation_conforms"] is True
    assert payload["validation_result_count"] == 0

    with DoxaBase.open_readonly(capsule_path) as db:
        dataset = db.describe_dataset(table)
        assert len(dataset.columns) == 2
        assert db.describe_query_context(table).readiness == (
            "ready_for_query_planning"
        )
        assert db.describe_query_context(view).readiness == "logical_analysis_view"
