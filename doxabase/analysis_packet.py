from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import struct
import sys
from pathlib import Path
from typing import Any, Mapping

from doxabase import DoxaBase, DoxaBaseError


ANALYSIS_PACKET_MANIFEST_FORMAT = "doxabase.analysis_packet_manifest.v1"

_EXTRA_MEDIA_TYPES = {
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".trig": "application/trig",
    ".ttl": "text/turtle",
    ".sqlite": "application/vnd.sqlite3",
    ".db": "application/vnd.sqlite3",
}


def apply_manifest_file(
    *,
    capsule_path: str | Path,
    manifest_path: str | Path,
    overwrite: bool = False,
    validation_scope: str = "all",
) -> dict[str, Any]:
    """Apply one reviewed analysis-packet manifest file."""

    capsule = Path(capsule_path)
    manifest_file = Path(manifest_path)
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DoxaBaseError(f"Manifest file does not exist: {manifest_file}") from exc
    except json.JSONDecodeError as exc:
        raise DoxaBaseError(
            "Could not parse analysis-packet manifest JSON from "
            f"{manifest_file}: {exc.msg} at line {exc.lineno} column {exc.colno}"
        ) from exc

    if capsule.parent != Path("."):
        capsule.parent.mkdir(parents=True, exist_ok=True)

    packet = _normalise_analysis_packet_manifest(manifest)
    with DoxaBase.create(capsule, overwrite=overwrite) as db:
        record = db.record_analysis_packet(**packet)
        validation = db.validate_graph(scope=validation_scope)
        return {
            "capsule_path": str(capsule),
            "manifest_path": str(manifest_file),
            "manifest_format": ANALYSIS_PACKET_MANIFEST_FORMAT,
            "packet_iri": record.packet_iri,
            "analysis_view_iris": record.analysis_view_iris,
            "artifact_iris": record.artifact_iris,
            "query_recipe_iris": record.query_recipe_iris,
            "followup_task_iris": record.followup_task_iris,
            "pattern_iri": record.pattern_iri,
            "analysis_view_count": len(record.analysis_view_iris),
            "artifact_count": len(record.artifact_iris),
            "query_recipe_count": len(record.query_recipe_iris),
            "followup_task_count": len(record.followup_task_iris),
            "suggested_next_calls": record.suggested_next_calls,
            "validation_scope": validation.scope,
            "validation_conforms": validation.conforms,
            "validation_result_count": validation.result_count,
        }


def scaffold_manifest_from_sidecars(
    *,
    sidecar_dir: str | Path,
    packet_iri: str,
    summary: str | None = None,
    label: str | None = None,
    source_prefix: str | None = None,
    hash_artifacts: bool = False,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a reviewable analysis-packet manifest skeleton from sidecar files."""

    sidecar_root = Path(sidecar_dir)
    if not sidecar_root.exists():
        raise DoxaBaseError(f"Sidecar directory does not exist: {sidecar_root}")
    if not sidecar_root.is_dir():
        raise DoxaBaseError(f"Sidecar path is not a directory: {sidecar_root}")

    resolved_output = Path(output_path).resolve() if output_path is not None else None
    sidecar_files = [
        path
        for path in sorted(
            (item for item in sidecar_root.rglob("*") if item.is_file()),
            key=lambda item: item.relative_to(sidecar_root).as_posix(),
        )
        if not _has_hidden_part(path.relative_to(sidecar_root))
        and (resolved_output is None or path.resolve() != resolved_output)
    ]
    if not sidecar_files:
        raise DoxaBaseError(f"No sidecar files found under: {sidecar_root}")

    artifacts = [
        _scaffold_artifact_spec(
            path,
            sidecar_root=sidecar_root,
            packet_iri=packet_iri,
            index=index,
            source_prefix=source_prefix,
            hash_artifacts=hash_artifacts,
        )
        for index, path in enumerate(sidecar_files, start=1)
    ]
    manifest = {
        "format": ANALYSIS_PACKET_MANIFEST_FORMAT,
        "packet_iri": packet_iri,
        "label": label,
        "summary": summary
        or (
            "TODO: Review these sidecar artifact locators and write a packet "
            "summary before applying this manifest."
        ),
        "evidence_sources": [],
        "analysis_views": [],
        "query_recipes": [],
        "artifacts": artifacts,
        "followup_tasks": [],
    }
    return {
        "manifest_format": ANALYSIS_PACKET_MANIFEST_FORMAT,
        "packet_iri": packet_iri,
        "sidecar_dir": str(sidecar_root),
        "artifact_count": len(artifacts),
        "hash_artifacts": hash_artifacts,
        "manifest": manifest,
    }


def _scaffold_artifact_spec(
    path: Path,
    *,
    sidecar_root: Path,
    packet_iri: str,
    index: int,
    source_prefix: str | None,
    hash_artifacts: bool,
) -> dict[str, Any]:
    relative_path = path.relative_to(sidecar_root)
    relative_source = relative_path.as_posix()
    source_path = (
        _join_source_prefix(source_prefix, relative_source)
        if source_prefix is not None
        else relative_source
    )
    media_type = _media_type_for_path(path)
    stat = path.stat()
    artifact_iri = (
        f"{packet_iri.rstrip('/')}/artifact/"
        f"{_artifact_slug(relative_source, index)}"
    )
    artifact = {
        "artifact_iri": artifact_iri,
        "label": _artifact_label(relative_path),
        "source_path": source_path,
        "artifact_role": _artifact_role(path, media_type),
        "media_type": media_type,
        "byte_size": stat.st_size,
    }
    if hash_artifacts:
        artifact["content_hash"] = _sha256_file(path)
    dimensions = _image_dimensions(path, media_type)
    if dimensions is not None:
        artifact["image_width"], artifact["image_height"] = dimensions
    return artifact


def _has_hidden_part(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def _join_source_prefix(source_prefix: str | None, relative_source: str) -> str:
    prefix = (source_prefix or "").strip()
    if not prefix:
        return relative_source
    if prefix.endswith(("/", "#")):
        return prefix + relative_source
    return prefix + "/" + relative_source


def _media_type_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in _EXTRA_MEDIA_TYPES:
        return _EXTRA_MEDIA_TYPES[suffix]
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def _artifact_role(path: Path, media_type: str) -> str:
    suffix = path.suffix.lower()
    if media_type.startswith("image/"):
        return "visualization"
    if suffix in {".md", ".markdown", ".txt"}:
        return "report"
    if suffix == ".json":
        return "structured data"
    if suffix in {".trig", ".ttl", ".rdf"}:
        return "rdf export"
    if suffix in {".sqlite", ".db"}:
        return "capsule"
    if suffix == ".py":
        return "verification script"
    return "sidecar"


def _artifact_label(relative_path: Path) -> str:
    stem = relative_path.stem or relative_path.name
    label = re.sub(r"[_-]+", " ", stem).strip()
    return label or relative_path.as_posix()


def _artifact_slug(relative_source: str, index: int) -> str:
    slug = re.sub(r"[^A-Za-z0-9._~-]+", "-", relative_source).strip("-._")
    return slug or str(index)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _image_dimensions(path: Path, media_type: str) -> tuple[int, int] | None:
    if media_type == "image/png":
        return _png_dimensions(path)
    if media_type == "image/jpeg":
        return _jpeg_dimensions(path)
    return None


def _png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
    except OSError:
        return None
    if (
        len(header) >= 24
        and header.startswith(b"\x89PNG\r\n\x1a\n")
        and header[12:16] == b"IHDR"
    ):
        width, height = struct.unpack(">II", header[16:24])
        if width > 0 and height > 0:
            return width, height
    return None


def _jpeg_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            if handle.read(2) != b"\xff\xd8":
                return None
            while True:
                marker_prefix = handle.read(1)
                if not marker_prefix:
                    return None
                if marker_prefix != b"\xff":
                    continue
                marker = handle.read(1)
                while marker == b"\xff":
                    marker = handle.read(1)
                if not marker or marker in {b"\x00", b"\x01"}:
                    continue
                if b"\xd0" <= marker <= b"\xd9":
                    continue
                length_bytes = handle.read(2)
                if len(length_bytes) != 2:
                    return None
                segment_length = int.from_bytes(length_bytes, "big")
                if segment_length < 2:
                    return None
                if marker in {
                    b"\xc0",
                    b"\xc1",
                    b"\xc2",
                    b"\xc3",
                    b"\xc5",
                    b"\xc6",
                    b"\xc7",
                    b"\xc9",
                    b"\xca",
                    b"\xcb",
                    b"\xcd",
                    b"\xce",
                    b"\xcf",
                }:
                    segment = handle.read(5)
                    if len(segment) != 5:
                        return None
                    height = int.from_bytes(segment[1:3], "big")
                    width = int.from_bytes(segment[3:5], "big")
                    if width > 0 and height > 0:
                        return width, height
                    return None
                handle.seek(segment_length - 2, 1)
    except OSError:
        return None


def _normalise_analysis_packet_manifest(manifest: Any) -> dict[str, Any]:
    if not isinstance(manifest, Mapping):
        raise DoxaBaseError("analysis-packet manifest must be an object")
    allowed_fields = {
        "format",
        "iri",
        "packet_iri",
        "summary",
        "label",
        "evidence_sources",
        "analysis_views",
        "analysis_view_iris",
        "query_recipes",
        "artifacts",
        "followup_tasks",
        "pattern_summary",
        "pattern_text",
        "pattern_rationale",
        "pattern_iri",
    }
    unknown_fields = sorted(set(manifest) - allowed_fields)
    if unknown_fields:
        raise DoxaBaseError(
            "analysis-packet manifest has unsupported field(s): "
            + ", ".join(unknown_fields)
        )
    if manifest.get("format") != ANALYSIS_PACKET_MANIFEST_FORMAT:
        raise DoxaBaseError(
            "analysis-packet manifest format must be "
            f"{ANALYSIS_PACKET_MANIFEST_FORMAT!r}"
        )

    packet_iri = manifest.get("packet_iri", manifest.get("iri"))
    if "iri" in manifest and "packet_iri" in manifest and manifest["iri"] != packet_iri:
        raise DoxaBaseError("analysis-packet manifest iri and packet_iri differ")
    packet = {
        "iri": packet_iri,
        "summary": manifest.get("summary"),
    }
    for field in (
        "label",
        "evidence_sources",
        "analysis_views",
        "analysis_view_iris",
        "query_recipes",
        "artifacts",
        "followup_tasks",
        "pattern_summary",
        "pattern_text",
        "pattern_rationale",
        "pattern_iri",
    ):
        if field in manifest:
            packet[field] = manifest[field]
    return packet


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Apply a reviewed DoxaBase analysis-packet manifest JSON file, or "
            "scaffold one from sidecar artifact locators."
        ),
    )
    parser.add_argument(
        "--init-manifest",
        action="store_true",
        help=(
            "Create a reviewable doxabase.analysis_packet_manifest.v1 skeleton "
            "from sidecar files instead of applying a manifest to a capsule."
        ),
    )
    parser.add_argument(
        "--capsule",
        help="SQLite capsule path to create or update.",
    )
    parser.add_argument(
        "--manifest",
        help=(
            "Path to a doxabase.analysis_packet_manifest.v1 JSON manifest. "
            "The command records reviewed locators and metadata only."
        ),
    )
    parser.add_argument(
        "--sidecar-dir",
        help=(
            "Directory of sidecar files to enumerate when --init-manifest is set."
        ),
    )
    parser.add_argument(
        "--packet-iri",
        help="Packet IRI to place in a scaffolded manifest.",
    )
    parser.add_argument(
        "--summary",
        help="Packet summary to place in a scaffolded manifest.",
    )
    parser.add_argument(
        "--label",
        help="Packet label to place in a scaffolded manifest.",
    )
    parser.add_argument(
        "--source-prefix",
        help=(
            "Optional prefix for scaffolded artifact source_path values; "
            "relative sidecar paths are used when omitted."
        ),
    )
    parser.add_argument(
        "--hash-artifacts",
        action="store_true",
        help="Include sha256:<hex> content_hash values in scaffolded artifacts.",
    )
    parser.add_argument(
        "--output",
        help=(
            "Write a scaffolded manifest to this path. When omitted, the "
            "manifest JSON is printed to stdout."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing capsule before applying the manifest.",
    )
    parser.add_argument(
        "--validation-scope",
        default="all",
        choices=["map", "ontology", "patterns", "shapes", "all"],
        help="Validation scope to run after applying the manifest.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.init_manifest:
            if not args.sidecar_dir:
                parser.error("--init-manifest requires --sidecar-dir")
            if not args.packet_iri:
                parser.error("--init-manifest requires --packet-iri")
            result = scaffold_manifest_from_sidecars(
                sidecar_dir=args.sidecar_dir,
                packet_iri=args.packet_iri,
                summary=args.summary,
                label=args.label,
                source_prefix=args.source_prefix,
                hash_artifacts=args.hash_artifacts,
                output_path=args.output,
            )
            manifest = result["manifest"]
            if args.output:
                output = Path(args.output)
                if output.parent != Path("."):
                    output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(
                    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                printed = dict(result)
                printed.pop("manifest", None)
                printed["manifest_path"] = str(output)
                print(json.dumps(printed, indent=2, sort_keys=True))
            else:
                print(json.dumps(manifest, indent=2, sort_keys=True))
            return 0

        if not args.capsule:
            parser.error("--capsule is required unless --init-manifest is set")
        if not args.manifest:
            parser.error("--manifest is required unless --init-manifest is set")
        result = apply_manifest_file(
            capsule_path=args.capsule,
            manifest_path=args.manifest,
            overwrite=args.overwrite,
            validation_scope=args.validation_scope,
        )
    except DoxaBaseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
