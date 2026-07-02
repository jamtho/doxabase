from __future__ import annotations

import json
from pathlib import Path

import pytest

from doxabase import DoxaBase, DoxaBaseError
from doxabase.parquet_manifest import (
    ParquetColumnMetadata,
    ParquetFileMetadata,
    build_parquet_profile_manifest,
    write_parquet_profile_manifest,
)


def test_build_parquet_profile_manifest_from_metadata_reader(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    paths = [data_dir / "orders.parquet", data_dir / "tickets.parquet"]

    def reader(path: Path) -> ParquetFileMetadata:
        if path.name == "orders.parquet":
            return ParquetFileMetadata(
                path=path,
                row_count=6,
                compression_codec="rc:ZstdCompression",
                columns=[
                    ParquetColumnMetadata("order_id", "int64", nullable=False),
                    ParquetColumnMetadata("status", "string", nullable=True),
                    ParquetColumnMetadata(
                        "updated_at",
                        "timestamp[us, tz=UTC]",
                        nullable=True,
                    ),
                ],
            )
        return ParquetFileMetadata(
            path=path,
            row_count=4,
            columns=[
                ParquetColumnMetadata("ticket_id", "int32", nullable=False),
                ParquetColumnMetadata("tags", "list<item: string>", nullable=True),
            ],
        )

    manifest = build_parquet_profile_manifest(
        paths,
        base_iri="https://example.test/profile-scaffold#",
        observed_by="urn:agent:parquet-scaffold-test",
        storage_root=data_dir,
        metadata_reader=reader,
    )

    assert manifest["format"] == "doxabase.profile_to_capsule_manifest.v1"
    assert manifest["table_defaults"]["storage_root"] == str(data_dir.resolve())
    assert manifest["table_defaults"]["schema_stability"] == "rc:InferredSchema"
    assert manifest["table_defaults"]["layout_verification_status"] == (
        "rc:CandidateLayout"
    )
    assert manifest["table_defaults"]["storage_layout_verification_status"] == (
        "rc:VerifiedByListingLayout"
    )
    assert manifest["caveats"][0]["targets"] == [
        "https://example.test/profile-scaffold#orders",
        "https://example.test/profile-scaffold#tickets",
    ]

    orders = manifest["tables"][0]
    assert orders["iri"] == "https://example.test/profile-scaffold#orders"
    assert orders["label"] == "Orders"
    assert orders["path_templates"] == ["orders.parquet"]
    assert orders["storage_path_templates"] == ["orders.parquet"]
    assert orders["row_count"] == 6
    assert orders["sample_size"] == 6
    assert orders["compression_codec"] == "rc:ZstdCompression"
    assert orders["observed_by"] == "urn:agent:parquet-scaffold-test"
    assert [
        (column["column_name"], column.get("physical_type"), column.get("nullable"))
        for column in orders["columns"]
    ] == [
        ("order_id", "rc:BigInt", False),
        ("status", "rc:Varchar", True),
        ("updated_at", "rc:TimestampTZ", True),
    ]
    tickets = manifest["tables"][1]
    assert tickets["columns"][1]["physical_type"] == "rc:VarcharList"


def test_parquet_profile_manifest_applies_to_capsule(
    tmp_path: Path,
) -> None:
    path = tmp_path / "profiles" / "orders.parquet"

    def reader(path_value: Path) -> ParquetFileMetadata:
        return ParquetFileMetadata(
            path=path_value,
            row_count=2,
            columns=[
                ParquetColumnMetadata("order_id", "int32", nullable=False),
                ParquetColumnMetadata("amount", "decimal128(12, 2)", nullable=True),
            ],
        )

    manifest = build_parquet_profile_manifest(
        [path],
        base_iri="https://example.test/profile-apply#",
        metadata_reader=reader,
    )

    with DoxaBase.create(tmp_path / "capsule.sqlite") as db:
        record = db.record_profile_to_capsule_manifest(manifest)
        validation = db.validate_graph(scope="all")

    assert record.table_iris == ["https://example.test/profile-apply#orders"]
    assert record.caveat_count == 1
    assert record.profile_observation_count == 3
    assert validation.conforms, validation.report_text


def test_write_parquet_profile_manifest_refuses_overwrite(tmp_path: Path) -> None:
    path = tmp_path / "orders.parquet"
    output = tmp_path / "profile-manifest.json"

    def reader(path_value: Path) -> ParquetFileMetadata:
        return ParquetFileMetadata(
            path=path_value,
            row_count=None,
            columns=[ParquetColumnMetadata("order_id", "int32")],
        )

    first_manifest = write_parquet_profile_manifest(
        output,
        [path],
        base_iri="https://example.test/profile-write#",
        metadata_reader=reader,
    )
    assert json.loads(output.read_text(encoding="utf-8")) == first_manifest

    with pytest.raises(DoxaBaseError, match="Output manifest already exists"):
        write_parquet_profile_manifest(
            output,
            [path],
            base_iri="https://example.test/profile-write#",
            metadata_reader=reader,
        )
