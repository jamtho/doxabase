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


ParquetMetadataReader = Callable[[Path], ParquetFileMetadata]


def build_parquet_profile_manifest(
    paths: Iterable[str | Path],
    *,
    base_iri: str,
    observed_by: str | None = None,
    storage_root: str | Path | None = None,
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
    root = (
        Path(storage_root).expanduser().resolve()
        if storage_root is not None
        else _common_parent(absolute_paths)
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
                storage_root=root,
                observed_by=observed_by,
                slug=_unique_slug(_slugify(path.stem), used_slugs),
            )
        )

    manifest: dict[str, Any] = {
        "format": PROFILE_TO_CAPSULE_MANIFEST_FORMAT,
        "table_defaults": {
            "storage_protocol": "rc:LocalFilesystemStorage",
            "access_mode": "rc:ReadOnlyAccess",
            "location_kind": "directory",
            "storage_root": str(root),
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
        },
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
    overwrite: bool = False,
    include_review_caveat: bool = True,
    metadata_reader: ParquetMetadataReader | None = None,
) -> dict[str, Any]:
    manifest = build_parquet_profile_manifest(
        paths,
        base_iri=base_iri,
        observed_by=observed_by,
        storage_root=storage_root,
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
    storage_root: Path,
    observed_by: str | None,
    slug: str,
) -> dict[str, Any]:
    label = _label_from_slug(slug)
    metadata_path = metadata.path.resolve()
    relative_path = _relative_path(metadata_path, storage_root)
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
            f"{label} schema and row-count scaffold generated from local Parquet "
            "metadata for review."
        ),
        "evidence_summary": (
            "Parquet footer/schema metadata read from local file "
            f"{metadata_path}; no raw rows were preserved in DoxaBase."
        ),
        "evidence_sources": [metadata_path.as_uri()],
        "path_templates": [relative_path],
        "sample_scope": (
            f"Parquet metadata for local file {relative_path}; row count, when "
            "present, is the file metadata row count."
        ),
        "columns": columns,
    }
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
        help="Reviewed storage root to record. Defaults to the common parent.",
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
