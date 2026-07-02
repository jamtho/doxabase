from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from doxabase import DoxaBase
from doxabase.parquet_manifest import (
    ParquetColumnMetadata,
    ParquetFileMetadata,
    build_parquet_profile_manifest,
)
from doxabase.profile_manifest_merge import PROFILE_FACTS_FORMAT


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://example.test/profile-merge-cli#"


def test_profile_manifest_merge_cli_writes_applyable_manifest(
    tmp_path: Path,
) -> None:
    scaffold_path = tmp_path / "scaffold.json"
    facts_path = tmp_path / "external-profile-facts.json"
    output_path = tmp_path / "reviewed-profile-manifest.json"
    scaffold_path.write_text(
        json.dumps(_scaffold(tmp_path), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    facts_path.write_text(
        json.dumps(_profile_facts(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "doxabase.profile_manifest_merge",
            "--scaffold",
            str(scaffold_path),
            "--profile-facts",
            str(facts_path),
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["manifest_format"] == "doxabase.profile_to_capsule_manifest.v1"
    assert payload["output_path"] == str(output_path)
    assert payload["table_count"] == 1
    assert payload["caveat_count"] == 2
    assert payload["merged_column_count"] == 2
    assert str(output_path) in payload["next_step"]

    manifest = json.loads(output_path.read_text(encoding="utf-8"))
    table = manifest["tables"][0]
    assert str(facts_path) in table["evidence_sources"]
    assert table["caveats"] == [
        f"{BASE}messages/caveat/external-profile-facts"
    ]
    assert table["layout_verification_status"] == "rc:VerifiedByListingLayout"
    assert table["physical_layout_verification_status"] == (
        "rc:VerifiedByListingLayout"
    )

    with DoxaBase.create(tmp_path / "capsule.sqlite") as db:
        record = db.record_profile_to_capsule_manifest(manifest)
        validation = db.validate_graph(scope="all")
        context = db.describe_query_context(record.table_iris[0])

    assert validation.conforms, validation.report_text
    assert record.table_iris == [f"{BASE}messages"]
    assert record.profile_observation_count == 4
    assert record.query_readiness_counts == {"ready_for_query_planning": 1}
    assert context.readiness == "ready_for_query_planning"


def test_profile_manifest_merge_cli_rejects_wrong_facts_format(
    tmp_path: Path,
) -> None:
    scaffold_path = tmp_path / "scaffold.json"
    facts_path = tmp_path / "external-profile-facts.json"
    output_path = tmp_path / "reviewed-profile-manifest.json"
    scaffold_path.write_text(
        json.dumps(_scaffold(tmp_path), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    facts = _profile_facts()
    facts["format"] = "doxabase.profile_to_capsule_manifest.v1"
    facts_path.write_text(
        json.dumps(facts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "doxabase.profile_manifest_merge",
            "--scaffold",
            str(scaffold_path),
            "--profile-facts",
            str(facts_path),
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "profile_facts format must be" in result.stderr
    assert not output_path.exists()


def _scaffold(tmp_path: Path) -> dict[str, object]:
    parquet_path = tmp_path / "data" / "messages.parquet"

    def reader(path: Path) -> ParquetFileMetadata:
        return ParquetFileMetadata(
            path=path,
            row_count=8,
            compression_codec="rc:ZstdCompression",
            columns=[
                ParquetColumnMetadata("message_id", "string", nullable=False),
                ParquetColumnMetadata("sender_domain", "string", nullable=True),
                ParquetColumnMetadata("attachment_count", "int32", nullable=False),
            ],
        )

    return build_parquet_profile_manifest(
        [parquet_path],
        base_iri=BASE,
        storage_root=parquet_path.parent,
        metadata_reader=reader,
    )


def _profile_facts() -> dict[str, object]:
    return {
        "format": PROFILE_FACTS_FORMAT,
        "tables": [
            {
                "iri": f"{BASE}messages",
                "row_count": 8,
                "sample_scope": "All reviewed message rows.",
                "sample_method": "External profiler aggregate scan.",
                "layout_verification_status": "rc:VerifiedByListingLayout",
                "layout_verification_note": (
                    "Reviewer confirmed the dataset path template and footer "
                    "metadata."
                ),
                "physical_layout_verification_status": (
                    "rc:VerifiedByListingLayout"
                ),
                "physical_layout_verification_note": (
                    "Reviewer confirmed the Parquet physical layout metadata."
                ),
                "columns": {
                    "sender_domain": {
                        "null_count": 0,
                        "distinct_count": 3,
                    },
                    "attachment_count": {
                        "profile_metrics": [
                            {"metric": "rc:MeanValue", "value": 0.75},
                        ],
                    },
                },
            }
        ],
    }
