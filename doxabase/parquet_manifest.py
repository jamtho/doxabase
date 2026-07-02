from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from doxabase.core import DoxaBaseError, PROFILE_TO_CAPSULE_MANIFEST_FORMAT


@dataclass(frozen=True)
class ParquetColumnMetadata:
    name: str
    type_text: str
    nullable: bool | None = None


@dataclass(frozen=True)
class ParquetFileMetadata:
    path: Path
    row_count: int | None
    columns: list[ParquetColumnMetadata]
    compression_codec: str | None = None


@dataclass(frozen=True)
class ParquetManifestStorageRoute:
    storage_protocol: str
    access_mode: str
    location_kind: str
    storage_root: str
    bucket_name: str | None = None
    key_prefix: str | None = None
    endpoint_profile: str | None = None
    region: str | None = None
    path_style_access: bool | None = None
    credential_reference: str | None = None
    route_roles: tuple[str, ...] = ()
    records_local_footer_paths: bool = True


ParquetMetadataReader = Callable[[Path], ParquetFileMetadata]


def build_parquet_profile_manifest(
    paths: Iterable[str | Path],
    *,
    base_iri: str,
    observed_by: str | None = None,
    storage_root: str | Path | None = None,
    local_footer_root: str | Path | None = None,
    storage_protocol: str = "rc:LocalFilesystemStorage",
    access_mode: str = "rc:ReadOnlyAccess",
    location_kind: str | None = None,
    bucket_name: str | None = None,
    key_prefix: str | None = None,
    endpoint_profile: str | None = None,
    region: str | None = None,
    path_style_access: bool | None = None,
    credential_reference: str | None = None,
    route_roles: Iterable[str] | str | None = None,
    include_review_caveat: bool = True,
    metadata_reader: ParquetMetadataReader | None = None,
) -> dict[str, Any]:
    """Build a reviewed-profile manifest scaffold from Parquet file metadata."""

    path_values = [Path(path).expanduser() for path in paths]
    if not path_values:
        raise DoxaBaseError("at least one Parquet path is required")
    if not isinstance(base_iri, str) or not base_iri.strip():
        raise DoxaBaseError("base_iri must be a non-empty IRI base")

    absolute_paths = [path.resolve() for path in path_values]
    route = _parquet_manifest_storage_route(
        storage_protocol=storage_protocol,
        access_mode=access_mode,
        location_kind=location_kind,
        storage_root=storage_root,
        local_footer_root=local_footer_root,
        absolute_paths=absolute_paths,
        bucket_name=bucket_name,
        key_prefix=key_prefix,
        endpoint_profile=endpoint_profile,
        region=region,
        path_style_access=path_style_access,
        credential_reference=credential_reference,
        route_roles=route_roles,
    )
    footer_root = (
        Path(local_footer_root).expanduser().resolve()
        if local_footer_root is not None
        else (
            Path(storage_root).expanduser().resolve()
            if storage_root is not None and route.records_local_footer_paths
            else _common_parent(absolute_paths)
        )
    )
    reader = metadata_reader or _read_pyarrow_parquet_metadata
    table_entries: list[dict[str, Any]] = []
    used_slugs: set[str] = set()
    for path in absolute_paths:
        metadata = reader(path)
        table_entries.append(
            _manifest_table_entry(
                metadata,
                base_iri=base_iri,
                local_footer_root=footer_root,
                observed_by=observed_by,
                slug=_unique_slug(_slugify(path.stem), used_slugs),
                records_local_footer_paths=route.records_local_footer_paths,
            )
        )

    table_defaults = {
        **_route_table_defaults(route),
        "schema_stability": "rc:InferredSchema",
        "layout_verification_status": "rc:CandidateLayout",
        "layout_verification_note": (
            "Generated from local Parquet footer metadata; review before "
            "treating this as executable query-planning context."
        ),
        "storage_layout_verification_status": "rc:VerifiedByListingLayout",
        "storage_layout_verification_note": (
            "The scaffold generator resolved the local file path and read "
            "Parquet metadata; review path portability before sharing."
        )
        if route.records_local_footer_paths
        else (
            "The scaffold generator read local Parquet footer copies while "
            "recording the reviewed object-store route; review the bucket, "
            "prefix, and runtime access marker before treating it as executable."
        ),
        "physical_layout_verification_status": "rc:CandidateLayout",
        "physical_layout_verification_note": (
            "Schema and row-count facts came from Parquet metadata; DoxaBase "
            "did not scan raw rows or compute data-quality profiles."
        ),
        "sample_method": (
            "Parquet footer/schema scaffold generated for review; DoxaBase "
            "did no raw-row ingestion."
        ),
    }
    manifest: dict[str, Any] = {
        "format": PROFILE_TO_CAPSULE_MANIFEST_FORMAT,
        "table_defaults": table_defaults,
        "tables": table_entries,
    }
    if observed_by is not None:
        manifest["table_defaults"]["observed_by"] = observed_by
    if include_review_caveat:
        caveat_iri = _join_base_iri(base_iri, "parquet_manifest_review_caveat")
        manifest["table_defaults"]["caveats"] = [caveat_iri]
        manifest["caveats"] = [
            {
                "iri": caveat_iri,
                "label": "Parquet manifest scaffold requires review",
                "description": (
                    "This manifest was generated from local Parquet footer "
                    "metadata. Review table identity, storage paths, physical "
                    "types, row counts, and shareability before applying or "
                    "exporting the capsule."
                ),
                "severity": "rc:Minor",
                "targets": [entry["iri"] for entry in table_entries],
            }
        ]
    return manifest


def write_parquet_profile_manifest(
    output_path: str | Path,
    paths: Iterable[str | Path],
    *,
    base_iri: str,
    observed_by: str | None = None,
    storage_root: str | Path | None = None,
    local_footer_root: str | Path | None = None,
    storage_protocol: str = "rc:LocalFilesystemStorage",
    access_mode: str = "rc:ReadOnlyAccess",
    location_kind: str | None = None,
    bucket_name: str | None = None,
    key_prefix: str | None = None,
    endpoint_profile: str | None = None,
    region: str | None = None,
    path_style_access: bool | None = None,
    credential_reference: str | None = None,
    route_roles: Iterable[str] | str | None = None,
    overwrite: bool = False,
    include_review_caveat: bool = True,
    metadata_reader: ParquetMetadataReader | None = None,
) -> dict[str, Any]:
    manifest = build_parquet_profile_manifest(
        paths,
        base_iri=base_iri,
        observed_by=observed_by,
        storage_root=storage_root,
        local_footer_root=local_footer_root,
        storage_protocol=storage_protocol,
        access_mode=access_mode,
        location_kind=location_kind,
        bucket_name=bucket_name,
        key_prefix=key_prefix,
        endpoint_profile=endpoint_profile,
        region=region,
        path_style_access=path_style_access,
        credential_reference=credential_reference,
        route_roles=route_roles,
        include_review_caveat=include_review_caveat,
        metadata_reader=metadata_reader,
    )
    destination = Path(output_path)
    if destination.exists() and not overwrite:
        raise DoxaBaseError(
            f"Output manifest already exists: {destination}. Pass overwrite=True "
            "or --overwrite to replace it."
        )
    if destination.parent != Path("."):
        destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _manifest_table_entry(
    metadata: ParquetFileMetadata,
    *,
    base_iri: str,
    local_footer_root: Path,
    observed_by: str | None,
    slug: str,
    records_local_footer_paths: bool,
) -> dict[str, Any]:
    label = _label_from_slug(slug)
    metadata_path = metadata.path.resolve()
    relative_path = _relative_path(metadata_path, local_footer_root)
    table_iri = _join_base_iri(base_iri, slug)
    columns = [
        _manifest_column_entry(column)
        for column in metadata.columns
        if column.name.strip()
    ]
    row_count = metadata.row_count
    entry: dict[str, Any] = {
        "iri": table_iri,
        "label": label,
        "description": (
            f"Reviewable Parquet table scaffold generated from {relative_path}."
        ),
        "dataset_summary": (
            f"{label} schema and row-count scaffold generated from Parquet "
            "metadata for review."
        ),
        "path_templates": [relative_path],
        "sample_scope": (
            f"Parquet metadata for file {relative_path}; row count, when "
            "present, is the file metadata row count."
        ),
        "columns": columns,
    }
    if records_local_footer_paths:
        entry["evidence_summary"] = (
            "Parquet footer/schema metadata read from local file "
            f"{metadata_path}; no raw rows were preserved in DoxaBase."
        )
        entry["evidence_sources"] = [metadata_path.as_uri()]
    else:
        entry["evidence_summary"] = (
            "Parquet footer/schema metadata read from a local copy for reviewed "
            f"object-store path {relative_path}; no raw rows were preserved in "
            "DoxaBase."
        )
        entry["evidence_sources"] = [f"local-footer-copy:{relative_path}"]
    if row_count is not None:
        entry["row_count"] = row_count
        entry["sample_size"] = row_count
    if observed_by is not None:
        entry["observed_by"] = observed_by
    if metadata.compression_codec is not None:
        entry["compression_codec"] = metadata.compression_codec
    return entry


def _manifest_column_entry(column: ParquetColumnMetadata) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "column_name": column.name,
        "description": f"Parquet metadata type: {column.type_text}.",
        "summary": (
            f"{column.name} was present in the reviewed Parquet schema metadata."
        ),
    }
    physical_type = _physical_type_from_arrow_text(column.type_text)
    if physical_type is not None:
        entry["physical_type"] = physical_type
    if column.nullable is not None:
        entry["nullable"] = column.nullable
    return entry


def _read_pyarrow_parquet_metadata(path: Path) -> ParquetFileMetadata:
    try:
        import pyarrow.parquet as pq  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise DoxaBaseError(
            "Parquet manifest scaffolding requires optional dependency "
            "'pyarrow'. Install pyarrow in the environment or pass an explicit "
            "metadata_reader when using build_parquet_profile_manifest()."
        ) from exc

    try:
        parquet_file = pq.ParquetFile(path)
    except Exception as exc:  # pragma: no cover - exact pyarrow errors vary
        raise DoxaBaseError(f"Could not read Parquet metadata from {path}: {exc}") from exc

    schema = parquet_file.schema_arrow
    columns = [
        ParquetColumnMetadata(
            name=str(field.name),
            type_text=str(field.type),
            nullable=bool(field.nullable),
        )
        for field in schema
    ]
    metadata = parquet_file.metadata
    row_count = getattr(metadata, "num_rows", None)
    compression_codec = _compression_codec_from_metadata(metadata)
    return ParquetFileMetadata(
        path=path.resolve(),
        row_count=row_count if isinstance(row_count, int) else None,
        columns=columns,
        compression_codec=compression_codec,
    )


def _parquet_manifest_storage_route(
    *,
    storage_protocol: str,
    access_mode: str,
    location_kind: str | None,
    storage_root: str | Path | None,
    local_footer_root: str | Path | None,
    absolute_paths: list[Path],
    bucket_name: str | None,
    key_prefix: str | None,
    endpoint_profile: str | None,
    region: str | None,
    path_style_access: bool | None,
    credential_reference: str | None,
    route_roles: Iterable[str] | str | None,
) -> ParquetManifestStorageRoute:
    storage_protocol_value = _non_empty_string(
        storage_protocol,
        "storage_protocol",
    )
    access_mode_value = _non_empty_string(access_mode, "access_mode")
    records_local_footer_paths = _is_local_storage_protocol(storage_protocol_value)
    if records_local_footer_paths:
        object_store_fields = {
            "bucket_name": bucket_name,
            "key_prefix": key_prefix,
            "endpoint_profile": endpoint_profile,
            "region": region,
            "path_style_access": path_style_access,
        }
        supplied_object_store_fields = [
            name for name, value in object_store_fields.items() if value is not None
        ]
        if supplied_object_store_fields:
            raise DoxaBaseError(
                "object-store route field(s) require a non-local "
                "storage_protocol: "
                + ", ".join(supplied_object_store_fields)
            )
        root = (
            Path(storage_root).expanduser().resolve()
            if storage_root is not None
            else _common_parent(absolute_paths)
        )
        storage_root_value = str(root)
        location_kind_value = location_kind or "directory"
    else:
        if storage_root is None:
            storage_root_value = _default_remote_storage_root(
                storage_protocol_value=storage_protocol_value,
                bucket_name=bucket_name,
                key_prefix=key_prefix,
            )
        else:
            storage_root_value = _non_empty_string(str(storage_root), "storage_root")
        location_kind_value = location_kind or (
            "bucket" if bucket_name is not None else "prefix"
        )

    return ParquetManifestStorageRoute(
        storage_protocol=storage_protocol_value,
        access_mode=access_mode_value,
        location_kind=_non_empty_string(location_kind_value, "location_kind"),
        storage_root=storage_root_value,
        bucket_name=_optional_non_empty_string(bucket_name, "bucket_name"),
        key_prefix=_normalise_key_prefix(key_prefix),
        endpoint_profile=_optional_non_empty_string(
            endpoint_profile,
            "endpoint_profile",
        ),
        region=_optional_non_empty_string(region, "region"),
        path_style_access=path_style_access,
        credential_reference=_optional_non_empty_string(
            credential_reference,
            "credential_reference",
        ),
        route_roles=tuple(_string_values(route_roles, "route_roles")),
        records_local_footer_paths=records_local_footer_paths,
    )


def _route_table_defaults(route: ParquetManifestStorageRoute) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "storage_protocol": route.storage_protocol,
        "access_mode": route.access_mode,
        "location_kind": route.location_kind,
        "storage_root": route.storage_root,
    }
    for field in (
        "bucket_name",
        "key_prefix",
        "endpoint_profile",
        "region",
        "credential_reference",
    ):
        value = getattr(route, field)
        if value is not None:
            defaults[field] = value
    if route.path_style_access is not None:
        defaults["path_style_access"] = route.path_style_access
    if route.route_roles:
        defaults["route_roles"] = list(route.route_roles)
    return defaults


def _is_local_storage_protocol(value: str) -> bool:
    return value in {
        "rc:LocalFilesystemStorage",
        "https://richcanopy.org/ns/rc#LocalFilesystemStorage",
    }


def _default_remote_storage_root(
    *,
    storage_protocol_value: str,
    bucket_name: str | None,
    key_prefix: str | None,
) -> str:
    if storage_protocol_value in {
        "rc:S3CompatibleStorage",
        "https://richcanopy.org/ns/rc#S3CompatibleStorage",
    }:
        bucket = _optional_non_empty_string(bucket_name, "bucket_name")
        if bucket is None:
            raise DoxaBaseError(
                "bucket_name is required when storage_protocol is "
                "rc:S3CompatibleStorage and storage_root is omitted"
            )
        prefix = _normalise_key_prefix(key_prefix)
        return f"s3://{bucket}/{prefix}" if prefix else f"s3://{bucket}"
    raise DoxaBaseError(
        "storage_root is required when storage_protocol is not local "
        "filesystem storage and no object-store default can be inferred"
    )


def _normalise_key_prefix(value: str | None) -> str | None:
    prefix = _optional_non_empty_string(value, "key_prefix")
    if prefix is None:
        return None
    stripped = prefix.strip("/")
    return stripped or None


def _non_empty_string(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DoxaBaseError(f"{field} must be a non-empty string")
    return value.strip()


def _optional_non_empty_string(value: str | None, field: str) -> str | None:
    if value is None:
        return None
    return _non_empty_string(value, field)


def _string_values(value: Iterable[str] | str | None, field: str) -> list[str]:
    if value is None:
        return []
    values = [value] if isinstance(value, str) else list(value)
    result: list[str] = []
    for index, item in enumerate(values, start=1):
        if not isinstance(item, str) or not item.strip():
            raise DoxaBaseError(f"{field}[{index}] must be a non-empty string")
        result.append(item.strip())
    return result


def _compression_codec_from_metadata(metadata: Any) -> str | None:
    codec_values: set[str] = set()
    num_row_groups = getattr(metadata, "num_row_groups", 0)
    for row_group_index in range(num_row_groups):
        row_group = metadata.row_group(row_group_index)
        for column_index in range(row_group.num_columns):
            compression = getattr(row_group.column(column_index), "compression", None)
            if compression:
                codec_values.add(str(compression).lower())
    if len(codec_values) != 1:
        return None
    return {
        "snappy": "rc:SnappyCompression",
        "zstd": "rc:ZstdCompression",
        "gzip": "rc:GzipCompression",
        "uncompressed": "rc:Uncompressed",
    }.get(next(iter(codec_values)))


def _physical_type_from_arrow_text(type_text: str) -> str | None:
    text = type_text.lower()
    if text in {"bool", "boolean"}:
        return "rc:Boolean"
    if text in {"int8", "int16", "int32"}:
        return "rc:Integer"
    if text == "int64":
        return "rc:BigInt"
    if text.startswith("uint"):
        return "rc:UBigInt"
    if text in {"float", "float32", "halffloat"}:
        return "rc:Float"
    if text in {"double", "float64"}:
        return "rc:Double"
    if text.startswith("decimal"):
        return "rc:Decimal"
    if text in {"string", "large_string", "utf8", "large_utf8"}:
        return "rc:Varchar"
    if text == "date32[day]" or text.startswith("date"):
        return "rc:Date"
    if text.startswith("timestamp"):
        return "rc:TimestampTZ" if "tz=" in text else "rc:Timestamp"
    if text in {"binary", "large_binary"} or text.startswith("fixed_size_binary"):
        return "rc:Blob"
    if text.startswith("list<") or text.startswith("large_list<"):
        if "int" in text:
            return "rc:IntegerList"
        if "double" in text or "float" in text:
            return "rc:DoubleList"
        if "string" in text or "utf8" in text:
            return "rc:VarcharList"
    if text.startswith(("struct<", "map<")):
        return "rc:Struct"
    return None


def _common_parent(paths: list[Path]) -> Path:
    if len(paths) == 1:
        return paths[0].parent
    return Path(_common_path_string(paths))


def _common_path_string(paths: list[Path]) -> str:
    try:
        return os.path.commonpath([str(path.parent) for path in paths])
    except ValueError as exc:
        raise DoxaBaseError("Parquet paths must share a common filesystem root") from exc


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return Path(os.path.relpath(path, root)).as_posix()


def _join_base_iri(base_iri: str, slug: str) -> str:
    base = base_iri.strip()
    separator = "" if base.endswith(("#", "/", ":")) else "#"
    return f"{base}{separator}{slug}"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return slug or "table"


def _unique_slug(slug: str, used_slugs: set[str]) -> str:
    candidate = slug
    index = 2
    while candidate in used_slugs:
        candidate = f"{slug}_{index}"
        index += 1
    used_slugs.add(candidate)
    return candidate


def _label_from_slug(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.split("_") if part) or "Table"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a reviewable DoxaBase profile-to-capsule manifest scaffold "
            "from local Parquet footer metadata."
        )
    )
    parser.add_argument("paths", nargs="+", help="Parquet file paths to inspect.")
    parser.add_argument(
        "--base-iri",
        required=True,
        help="IRI base used to mint table and caveat IRIs.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path for the generated doxabase.profile_to_capsule_manifest.v1 JSON.",
    )
    parser.add_argument(
        "--storage-root",
        help=(
            "Reviewed storage root to record. Defaults to the common parent for "
            "local storage or to s3://bucket[/prefix] for S3-compatible storage."
        ),
    )
    parser.add_argument(
        "--local-footer-root",
        help=(
            "Local root used only to make input Parquet footer paths relative. "
            "Useful when recording an object-store route from local file copies."
        ),
    )
    parser.add_argument(
        "--storage-protocol",
        default="rc:LocalFilesystemStorage",
        help="Storage protocol IRI/CURIE to record.",
    )
    parser.add_argument(
        "--access-mode",
        default="rc:ReadOnlyAccess",
        help="Storage access mode IRI/CURIE to record.",
    )
    parser.add_argument(
        "--location-kind",
        help=(
            "Storage location kind to record. Defaults to directory for local "
            "storage and bucket/prefix for object-store routes."
        ),
    )
    parser.add_argument(
        "--bucket-name",
        help="Object-store bucket name to record.",
    )
    parser.add_argument(
        "--key-prefix",
        help="Object-store key prefix to record; table templates stay relative.",
    )
    parser.add_argument(
        "--endpoint-profile",
        help="Non-secret endpoint/runtime profile name to record.",
    )
    parser.add_argument(
        "--region",
        help="Object-store region to record.",
    )
    parser.add_argument(
        "--path-style-access",
        action="store_true",
        help="Record path-style object-store access.",
    )
    parser.add_argument(
        "--credential-reference",
        help=(
            "Non-secret credential marker such as profile:name, env:VAR, or "
            "external:intentionally-unrecorded."
        ),
    )
    parser.add_argument(
        "--route-role",
        dest="route_roles",
        action="append",
        help="Repeatable storage route role IRI/CURIE to record.",
    )
    parser.add_argument(
        "--observed-by",
        help="Optional agent or profiler IRI/name to store in table specs.",
    )
    parser.add_argument(
        "--no-review-caveat",
        action="store_true",
        help="Do not add the default generated-manifest review caveat.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing output manifest.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        manifest = write_parquet_profile_manifest(
            args.output,
            args.paths,
            base_iri=args.base_iri,
            observed_by=args.observed_by,
            storage_root=args.storage_root,
            local_footer_root=args.local_footer_root,
            storage_protocol=args.storage_protocol,
            access_mode=args.access_mode,
            location_kind=args.location_kind,
            bucket_name=args.bucket_name,
            key_prefix=args.key_prefix,
            endpoint_profile=args.endpoint_profile,
            region=args.region,
            path_style_access=True if args.path_style_access else None,
            credential_reference=args.credential_reference,
            route_roles=args.route_roles,
            overwrite=args.overwrite,
            include_review_caveat=not args.no_review_caveat,
        )
    except DoxaBaseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "path": str(Path(args.output)),
                "manifest_format": manifest["format"],
                "table_count": len(manifest["tables"]),
                "caveat_count": len(manifest.get("caveats", [])),
                "next_step": (
                    "Review the JSON, then apply with "
                    "python -m doxabase.profile_to_capsule --capsule ... "
                    f"--manifest {args.output}"
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
