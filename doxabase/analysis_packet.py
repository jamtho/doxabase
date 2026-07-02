from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from doxabase import DoxaBase, DoxaBaseError


ANALYSIS_PACKET_MANIFEST_FORMAT = "doxabase.analysis_packet_manifest.v1"


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
        description="Apply a reviewed DoxaBase analysis-packet manifest JSON file.",
    )
    parser.add_argument(
        "--capsule",
        required=True,
        help="SQLite capsule path to create or update.",
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help=(
            "Path to a doxabase.analysis_packet_manifest.v1 JSON manifest. "
            "The command records reviewed locators and metadata only."
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
