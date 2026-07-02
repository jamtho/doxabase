from __future__ import annotations

import json
from pathlib import Path

import pytest

from doxabase import DoxaBase, DoxaBaseError
from doxabase.parquet_manifest import (
    ParquetColumnMetadata,
    ParquetFileMetadata,
    build_parquet_profile_manifest,
)
from doxabase.profile_manifest_merge import (
    PROFILE_FACTS_FORMAT,
    merge_reviewed_profile_facts,
    write_merged_profile_manifest,
)


BASE = "https://example.test/profile-merge#"


def test_merge_reviewed_profile_facts_builds_applyable_manifest(
    tmp_path: Path,
) -> None:
    scaffold = _scaffold(tmp_path)
    facts_path = tmp_path / "external-profile-facts.json"
    facts = _profile_facts()

    merged = merge_reviewed_profile_facts(
        scaffold,
        facts,
        profile_facts_source=str(facts_path),
    )

    assert not any(key.startswith("_") for key in merged)
    table = merged["tables"][0]
    assert table["row_count"] == 12
    assert table["sample_size"] == 12
    assert table["sample_scope"] == "All rows in the reviewed message snapshot."
    assert table["sample_method"] == "External profiler full-table aggregate scan."
    assert str(facts_path) in table["evidence_sources"]
    assert merged["table_defaults"]["layout_verification_status"] == (
        "rc:CandidateLayout"
    )
    assert merged["table_defaults"]["physical_layout_verification_status"] == (
        "rc:CandidateLayout"
    )
    assert merged["table_defaults"]["caveats"] == [
        f"{BASE}parquet_manifest_review_caveat"
    ]
    assert table["caveats"] == [
        f"{BASE}messages/caveat/external-profile-facts"
    ]
    assert len(merged["caveats"]) == 2

    sender_column = _column(table, "sender_domain")
    assert sender_column["null_count"] == 0
    assert sender_column["distinct_count"] == 4
    assert sender_column["value_frequencies"] == [
        {"value": "enron.com", "frequency": 6},
        {"value": "example.org", "frequency": 3},
    ]
    attachment_column = _column(table, "attachment_count")
    assert attachment_column["profile_metrics"] == [
        {"metric": "rc:MinimumValue", "value": 0},
        {"metric": "rc:MeanValue", "value": 1.25},
    ]
    assert "null_count" not in _column(table, "sent_at")

    with DoxaBase.create(tmp_path / "capsule.sqlite") as db:
        record = db.record_profile_to_capsule_manifest(merged)
        validation = db.validate_graph(scope="all")
        profile_run = db.describe_profile_run(
            f"{BASE}messages",
            record.shared_evidence_iris[0],
        )
        description = db.describe_dataset(f"{BASE}messages")

    assert validation.conforms, validation.report_text
    assert record.profile_observation_count == 6
    assert profile_run.total_profile_count == 6
    sender_description = next(
        column
        for column in description.columns
        if column.column_name == "sender_domain"
    )
    sender_profile = sender_description.profile_observations[0]
    assert [(item.value, item.frequency) for item in sender_profile.value_frequencies] == [
        ("enron.com", 6),
        ("example.org", 3),
    ]
    attachment_description = next(
        column
        for column in description.columns
        if column.column_name == "attachment_count"
    )
    attachment_profile = attachment_description.profile_observations[0]
    assert {metric.metric.iri for metric in attachment_profile.profile_metrics} == {
        "https://richcanopy.org/ns/rc#MinimumValue",
        "https://richcanopy.org/ns/rc#MeanValue",
    }


def test_merge_reviewed_profile_facts_preserves_profile_patterns(
    tmp_path: Path,
) -> None:
    facts = _profile_facts(
        columns={
            "message_id": {
                "null_count": 0,
                "distinct_count": 12,
                "pattern_summary": "message_id behaves like an identifier.",
                "pattern_text": (
                    "The reviewed profile sidecar reported no nulls and full "
                    "distinctness for message_id."
                ),
                "pattern_rationale": (
                    "Identifier-like columns should stay connected to their "
                    "supporting aggregate profile facts."
                ),
                "pattern_map_implications": [f"{BASE}messages__message_id"],
                "pattern_iri": f"{BASE}pattern_message_id_identifier",
            }
        }
    )
    facts["tables"][0].update(
        {
            "pattern_summary": "Messages profile is reviewed aggregate evidence.",
            "pattern_text": (
                "The reviewed sidecar links table and column profile facts "
                "into one documented profiler run."
            ),
            "pattern_rationale": (
                "Later agents need the profiler synthesis as graph-native lore, "
                "not only as external Markdown."
            ),
            "pattern_support_scope": "dataset_profile",
        }
    )

    merged = merge_reviewed_profile_facts(_scaffold(tmp_path), facts)
    table = merged["tables"][0]

    assert table["pattern_summary"] == (
        "Messages profile is reviewed aggregate evidence."
    )
    message_id_column = _column(table, "message_id")
    assert message_id_column["pattern_iri"] == (
        f"{BASE}pattern_message_id_identifier"
    )
    assert message_id_column["pattern_map_implications"] == [
        f"{BASE}messages__message_id"
    ]

    with DoxaBase.create(tmp_path / "capsule.sqlite") as db:
        record = db.record_profile_to_capsule_manifest(merged)
        validation = db.validate_graph(scope="all")
        table_record = record.table_records[0]
        dataset_pattern_record = (
            table_record.profile_bundle.dataset_profile.pattern
        )
        assert dataset_pattern_record is not None
        dataset_pattern = db.describe_pattern(dataset_pattern_record.pattern_iri)
        column_pattern = db.describe_pattern(
            f"{BASE}pattern_message_id_identifier"
        )

    assert validation.conforms, validation.report_text
    assert dataset_pattern.summary == (
        "Messages profile is reviewed aggregate evidence."
    )
    assert [target.iri for target in dataset_pattern.pattern_targets] == [
        f"{BASE}messages"
    ]
    assert column_pattern.summary == "message_id behaves like an identifier."
    assert [target.iri for target in column_pattern.pattern_targets] == [
        f"{BASE}messages__message_id"
    ]
    assert [target.iri for target in column_pattern.map_implications] == [
        f"{BASE}messages__message_id"
    ]


def test_merge_rejects_unknown_table_iri(tmp_path: Path) -> None:
    facts = _profile_facts(table_iri=f"{BASE}missing")

    with pytest.raises(DoxaBaseError, match="does not match a scaffold table"):
        merge_reviewed_profile_facts(_scaffold(tmp_path), facts)


def test_merge_rejects_unknown_column_name(tmp_path: Path) -> None:
    facts = _profile_facts()
    facts["tables"][0]["columns"]["missing_column"] = {"null_count": 0}

    with pytest.raises(DoxaBaseError, match="does not match a scaffold column"):
        merge_reviewed_profile_facts(_scaffold(tmp_path), facts)


def test_merge_rejects_row_count_mismatch(tmp_path: Path) -> None:
    facts = _profile_facts(row_count=13)

    with pytest.raises(DoxaBaseError, match="does not match scaffold row_count=12"):
        merge_reviewed_profile_facts(_scaffold(tmp_path), facts)


def test_merge_allows_partial_column_facts(tmp_path: Path) -> None:
    facts = _profile_facts(
        columns={
            "message_id": {"null_count": 0, "distinct_count": 12},
        }
    )

    merged = merge_reviewed_profile_facts(_scaffold(tmp_path), facts)
    table = merged["tables"][0]

    assert _column(table, "message_id")["distinct_count"] == 12
    assert "null_count" not in _column(table, "sender_domain")
    assert len(table["columns"]) == 5


def test_merge_allows_empty_column_facts_with_row_count(tmp_path: Path) -> None:
    facts = _profile_facts(columns={})

    merged = merge_reviewed_profile_facts(_scaffold(tmp_path), facts)
    table = merged["tables"][0]

    assert table["row_count"] == 12
    assert table["sample_size"] == 12
    assert "null_count" not in _column(table, "message_id")


def test_merge_allows_reviewed_layout_verification_fields(
    tmp_path: Path,
) -> None:
    facts = _profile_facts(columns={})
    table_facts = facts["tables"][0]
    table_facts.update(
        {
            "layout_verification_status": "rc:VerifiedByListingLayout",
            "layout_verification_note": (
                "Reviewer confirmed the dataset path template and Parquet "
                "footer metadata."
            ),
            "physical_layout_verification_status": "rc:VerifiedByListingLayout",
            "physical_layout_verification_note": (
                "Reviewer confirmed the Parquet physical layout metadata."
            ),
        }
    )

    merged = merge_reviewed_profile_facts(_scaffold(tmp_path), facts)
    table = merged["tables"][0]

    assert table["layout_verification_status"] == "rc:VerifiedByListingLayout"
    assert table["physical_layout_verification_status"] == (
        "rc:VerifiedByListingLayout"
    )
    assert merged["table_defaults"]["layout_verification_status"] == (
        "rc:CandidateLayout"
    )

    with DoxaBase.create(tmp_path / "capsule.sqlite") as db:
        record = db.record_profile_to_capsule_manifest(merged)
        context = db.describe_query_context(record.table_iris[0])
        validation = db.validate_graph(scope="all")

    assert validation.conforms, validation.report_text
    assert record.query_readiness_counts == {"ready_for_query_planning": 1}
    assert context.readiness == "ready_for_query_planning"
    assert context.issues == []


def test_merge_rejects_empty_column_facts_without_row_count(tmp_path: Path) -> None:
    facts = _profile_facts(columns={})
    del facts["tables"][0]["row_count"]

    with pytest.raises(DoxaBaseError, match="can be empty only when row_count"):
        merge_reviewed_profile_facts(_scaffold(tmp_path), facts)


def test_merge_rejects_unknown_fact_fields(tmp_path: Path) -> None:
    facts = _profile_facts()
    facts["unexpected"] = True

    with pytest.raises(DoxaBaseError, match="profile_facts has unsupported field"):
        merge_reviewed_profile_facts(_scaffold(tmp_path), facts)

    facts = _profile_facts()
    facts["tables"][0]["physical_type"] = "rc:Varchar"
    with pytest.raises(
        DoxaBaseError,
        match="profile_facts.tables\\[1\\] has unsupported field",
    ):
        merge_reviewed_profile_facts(_scaffold(tmp_path), facts)

    facts = _profile_facts()
    facts["tables"][0]["columns"]["message_id"]["physical_type"] = "rc:Varchar"
    with pytest.raises(
        DoxaBaseError,
        match="profile_facts.tables\\[1\\].columns.message_id has unsupported field",
    ):
        merge_reviewed_profile_facts(_scaffold(tmp_path), facts)


def test_write_merged_profile_manifest_refuses_overwrite(tmp_path: Path) -> None:
    scaffold_path = tmp_path / "scaffold.json"
    facts_path = tmp_path / "facts.json"
    output_path = tmp_path / "reviewed-manifest.json"
    scaffold_path.write_text(
        json.dumps(_scaffold(tmp_path), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    facts_path.write_text(
        json.dumps(_profile_facts(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    first = write_merged_profile_manifest(
        output_path,
        scaffold_path=scaffold_path,
        profile_facts_path=facts_path,
    )
    assert json.loads(output_path.read_text(encoding="utf-8")) == first
    with pytest.raises(DoxaBaseError, match="Output manifest already exists"):
        write_merged_profile_manifest(
            output_path,
            scaffold_path=scaffold_path,
            profile_facts_path=facts_path,
        )


def _scaffold(tmp_path: Path) -> dict[str, object]:
    parquet_path = tmp_path / "data" / "messages.parquet"

    def reader(path: Path) -> ParquetFileMetadata:
        return ParquetFileMetadata(
            path=path,
            row_count=12,
            compression_codec="rc:ZstdCompression",
            columns=[
                ParquetColumnMetadata("message_id", "string", nullable=False),
                ParquetColumnMetadata("sender_domain", "string", nullable=True),
                ParquetColumnMetadata("direction", "string", nullable=True),
                ParquetColumnMetadata("attachment_count", "int32", nullable=False),
                ParquetColumnMetadata("sent_at", "timestamp[us]", nullable=True),
            ],
        )

    return build_parquet_profile_manifest(
        [parquet_path],
        base_iri=BASE,
        storage_root=parquet_path.parent,
        metadata_reader=reader,
    )


def _profile_facts(
    *,
    table_iri: str = f"{BASE}messages",
    row_count: int = 12,
    columns: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "format": PROFILE_FACTS_FORMAT,
        "tables": [
            {
                "iri": table_iri,
                "row_count": row_count,
                "sample_scope": "All rows in the reviewed message snapshot.",
                "sample_method": "External profiler full-table aggregate scan.",
                "evidence_sources": ["scratch://external-profile.json"],
                "columns": columns
                if columns is not None
                else {
                    "message_id": {"null_count": 0, "distinct_count": 12},
                    "sender_domain": {
                        "null_count": 0,
                        "distinct_count": 4,
                        "value_frequencies": [
                            {"value": "enron.com", "count": 6},
                            {"value": "example.org", "frequency": 3},
                        ],
                    },
                    "attachment_count": {
                        "null_count": 0,
                        "distinct_count": 4,
                        "profile_metrics": [
                            {"metric_kind": "rc:MinimumValue", "value": 0},
                            {"metric": "rc:MeanValue", "value": 1.25},
                        ],
                    },
                },
            }
        ],
    }


def _column(table: dict[str, object], name: str) -> dict[str, object]:
    columns = table["columns"]
    assert isinstance(columns, list)
    for column in columns:
        assert isinstance(column, dict)
        if column.get("column_name") == name:
            return column
    raise AssertionError(f"column not found: {name}")
