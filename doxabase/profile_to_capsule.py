from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from doxabase import DoxaBase, DoxaBaseError


def apply_manifest_file(
    *,
    capsule_path: str | Path,
    manifest_path: str | Path,
    overwrite: bool = False,
    validation_scope: str = "all",
) -> dict[str, Any]:
    """Apply one reviewed profile-to-capsule manifest file."""

    capsule = Path(capsule_path)
    manifest_file = Path(manifest_path)
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DoxaBaseError(f"Manifest file does not exist: {manifest_file}") from exc
    except json.JSONDecodeError as exc:
        raise DoxaBaseError(
            "Could not parse profile-to-capsule manifest JSON from "
            f"{manifest_file}: {exc.msg} at line {exc.lineno} column {exc.colno}"
        ) from exc

    if capsule.parent != Path("."):
        capsule.parent.mkdir(parents=True, exist_ok=True)

    with DoxaBase.create(capsule, overwrite=overwrite) as db:
        record = db.record_profile_to_capsule_manifest(manifest)
        validation = db.validate_graph(scope=validation_scope)
        return {
            "capsule_path": str(capsule),
            "manifest_path": str(manifest_file),
            "manifest_format": record.manifest_format,
            "table_iris": record.table_iris,
            "shared_evidence_iris": record.shared_evidence_iris,
            "analysis_view_iris": record.analysis_view_iris,
            "domain_network_profile_evidence_iris": (
                record.domain_network_profile_evidence_iris
            ),
            "domain_network_pattern_iris": record.domain_network_pattern_iris,
            "caveat_iris": record.caveat_iris,
            "table_count": record.table_count,
            "analysis_view_count": record.analysis_view_count,
            "domain_network_profile_count": record.domain_network_profile_count,
            "domain_network_profile_observation_count": (
                record.domain_network_profile_observation_count
            ),
            "caveat_count": record.caveat_count,
            "profile_observation_count": record.profile_observation_count,
            "query_readiness_counts": record.query_readiness_counts,
            "query_issue_code_counts": record.query_issue_code_counts,
            "suggested_next_calls": record.suggested_next_calls,
            "validation_scope": validation.scope,
            "validation_conforms": validation.conforms,
            "validation_result_count": validation.result_count,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Apply a reviewed DoxaBase profile-to-capsule manifest JSON file."
        ),
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
            "Path to a doxabase.profile_to_capsule_manifest.v1 JSON manifest. "
            "The command records reviewed metadata/aggregate profiles only and "
            "performs no Parquet I/O or address parsing."
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
