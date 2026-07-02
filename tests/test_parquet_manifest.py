from __future__ import annotations

import json
import subprocess
import sys
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
    assert "storage_path_templates" not in orders
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
        context = db.describe_query_context(record.table_iris[0])
        validation = db.validate_graph(scope="all")

    assert record.table_iris == ["https://example.test/profile-apply#orders"]
    assert record.caveat_count == 1
    assert record.profile_observation_count == 3
    assert len(context.query_target_candidates) == 1
    candidate = context.query_target_candidates[0]
    assert candidate.template == "orders.parquet"
    assert candidate.template_source == "dataset"
    assert candidate.candidate_path == str(path.resolve())
    assert validation.conforms, validation.report_text


def test_build_parquet_profile_manifest_records_s3_route_defaults(
    tmp_path: Path,
) -> None:
    local_copy_dir = tmp_path / "local-copy"
    path = local_copy_dir / "eml_messages.parquet"

    def reader(path_value: Path) -> ParquetFileMetadata:
        return ParquetFileMetadata(
            path=path_value,
            row_count=123,
            columns=[ParquetColumnMetadata("doc_id", "string", nullable=False)],
        )

    manifest = build_parquet_profile_manifest(
        [path],
        base_iri="https://example.test/enron#",
        local_footer_root=local_copy_dir,
        storage_protocol="rc:S3CompatibleStorage",
        location_kind="bucket",
        bucket_name="enron-emails",
        key_prefix="parquet",
        endpoint_profile="minio-local",
        region="us-east-1",
        path_style_access=True,
        credential_reference="external:intentionally-unrecorded",
        route_roles=["rc:SourceDataRoute"],
        metadata_reader=reader,
    )

    defaults = manifest["table_defaults"]
    assert defaults["storage_protocol"] == "rc:S3CompatibleStorage"
    assert defaults["location_kind"] == "bucket"
    assert defaults["storage_root"] == "s3://enron-emails/parquet"
    assert defaults["bucket_name"] == "enron-emails"
    assert defaults["key_prefix"] == "parquet"
    assert defaults["endpoint_profile"] == "minio-local"
    assert defaults["region"] == "us-east-1"
    assert defaults["path_style_access"] is True
    assert defaults["credential_reference"] == "external:intentionally-unrecorded"
    assert defaults["route_roles"] == ["rc:SourceDataRoute"]

    table = manifest["tables"][0]
    assert table["path_templates"] == ["eml_messages.parquet"]
    assert table["evidence_sources"] == ["local-footer-copy:eml_messages.parquet"]
    assert str(local_copy_dir) not in table["evidence_summary"]
    assert path.as_uri() not in table["evidence_sources"]


def test_s3_parquet_profile_manifest_omits_slash_only_key_prefix(
    tmp_path: Path,
) -> None:
    path = tmp_path / "orders.parquet"

    def reader(path_value: Path) -> ParquetFileMetadata:
        return ParquetFileMetadata(
            path=path_value,
            row_count=1,
            columns=[ParquetColumnMetadata("order_id", "int64", nullable=False)],
        )

    manifest = build_parquet_profile_manifest(
        [path],
        base_iri="https://example.test/orders#",
        storage_protocol="rc:S3CompatibleStorage",
        bucket_name="orders-lake",
        key_prefix=" / ",
        metadata_reader=reader,
    )

    defaults = manifest["table_defaults"]
    assert defaults["storage_root"] == "s3://orders-lake"
    assert "key_prefix" not in defaults


def test_s3_parquet_profile_manifest_applies_to_capsule_and_query_context(
    tmp_path: Path,
) -> None:
    local_copy_dir = tmp_path / "local-copy"
    path = local_copy_dir / "eml_messages.parquet"

    def reader(path_value: Path) -> ParquetFileMetadata:
        return ParquetFileMetadata(
            path=path_value,
            row_count=123,
            compression_codec="rc:ZstdCompression",
            columns=[
                ParquetColumnMetadata("doc_id", "string", nullable=False),
                ParquetColumnMetadata("sent_at", "timestamp[us]", nullable=True),
            ],
        )

    manifest = build_parquet_profile_manifest(
        [path],
        base_iri="https://example.test/enron#",
        local_footer_root=local_copy_dir,
        storage_protocol="rc:S3CompatibleStorage",
        location_kind="bucket",
        bucket_name="enron-emails",
        key_prefix="parquet",
        credential_reference="external:intentionally-unrecorded",
        metadata_reader=reader,
    )

    with DoxaBase.create(tmp_path / "capsule.sqlite") as db:
        record = db.record_profile_to_capsule_manifest(manifest)
        context = db.describe_query_context(record.table_iris[0])
        validation = db.validate_graph(scope="all")

    assert validation.conforms, validation.report_text
    assert record.table_iris == ["https://example.test/enron#eml_messages"]
    assert context.storage_accesses[0].storage_protocol is not None
    assert context.storage_accesses[0].storage_protocol.iri.endswith(
        "S3CompatibleStorage"
    )
    assert context.storage_accesses[0].location_kind == "prefix"
    assert context.storage_accesses[0].bucket_name == "enron-emails"
    assert context.storage_accesses[0].key_prefix == "parquet"
    assert context.storage_accesses[0].credential_reference == (
        "external:intentionally-unrecorded"
    )
    assert len(context.query_target_candidates) == 1
    candidate = context.query_target_candidates[0]
    assert candidate.template == "eml_messages.parquet"
    assert candidate.template_source == "dataset"
    assert candidate.candidate_path == "s3://enron-emails/parquet/eml_messages.parquet"
    assert "storage_protocol_location_mismatch" not in {
        reason.code for reason in candidate.review_reasons
    }


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


def test_parquet_manifest_cli_accepts_s3_route_options(tmp_path: Path) -> None:
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")

    local_copy_dir = tmp_path / "local-copy"
    local_copy_dir.mkdir()
    path = local_copy_dir / "orders.parquet"
    pq.write_table(pa.table({"order_id": [1, 2]}), path)
    output = tmp_path / "profile-manifest.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "doxabase.parquet_manifest",
            "--base-iri",
            "https://example.test/cli-s3#",
            "--output",
            str(output),
            "--local-footer-root",
            str(local_copy_dir),
            "--storage-protocol",
            "rc:S3CompatibleStorage",
            "--location-kind",
            "bucket",
            "--bucket-name",
            "orders-lake",
            "--key-prefix",
            "warehouse/orders",
            "--endpoint-profile",
            "minio-local",
            "--path-style-access",
            "--credential-reference",
            "external:intentionally-unrecorded",
            str(path),
        ],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert payload["table_count"] == 1
    assert manifest["table_defaults"]["storage_protocol"] == (
        "rc:S3CompatibleStorage"
    )
    assert manifest["table_defaults"]["storage_root"] == (
        "s3://orders-lake/warehouse/orders"
    )
    assert manifest["table_defaults"]["bucket_name"] == "orders-lake"
    assert manifest["table_defaults"]["key_prefix"] == "warehouse/orders"
    assert manifest["table_defaults"]["endpoint_profile"] == "minio-local"
    assert manifest["table_defaults"]["path_style_access"] is True
    assert manifest["table_defaults"]["credential_reference"] == (
        "external:intentionally-unrecorded"
    )
    assert manifest["tables"][0]["path_templates"] == ["orders.parquet"]
    assert manifest["tables"][0]["evidence_sources"] == [
        "local-footer-copy:orders.parquet"
    ]
