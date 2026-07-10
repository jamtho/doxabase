#!/usr/bin/env python3
"""Verify the Enron DoxaBase handoff bundle in a fresh capsule."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


RUN_DIR = Path(__file__).resolve().parent
DEFAULT_CHECKOUT_DIR = RUN_DIR / "doxabase"
SOURCE_CAPSULE = RUN_DIR / "enron-emails.doxabase.sqlite"
MANIFEST = RUN_DIR / "enron_knowledge_store_handoff_manifest.json"
DEFAULT_SUMMARY = RUN_DIR / "enron_handoff_verify_latest_summary.json"


def unique_capsule_path(base: Path) -> Path:
    if not base.exists():
        return base
    stem = base.stem
    suffix = base.suffix
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = base.with_name(f"{stem}-{timestamp}{suffix}")
    index = 1
    while candidate.exists():
        candidate = base.with_name(f"{stem}-{timestamp}-{index}{suffix}")
        index += 1
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import the Enron handoff manifest into a fresh DoxaBase capsule."
    )
    parser.add_argument(
        "--doxabase-dir",
        type=Path,
        default=Path(os.environ["DOXABASE_CHECKOUT"]).expanduser()
        if os.environ.get("DOXABASE_CHECKOUT")
        else DEFAULT_CHECKOUT_DIR,
        help=(
            "Path to a DoxaBase checkout. Defaults to ./doxabase next to this "
            "script, or DOXABASE_CHECKOUT if set. If the path is absent, the "
            "script tries an installed doxabase package."
        ),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=MANIFEST,
        help="Path to the handoff manifest JSON.",
    )
    parser.add_argument(
        "--source-capsule",
        type=Path,
        default=SOURCE_CAPSULE,
        help="Optional source capsule used for key-count comparison.",
    )
    parser.add_argument(
        "--output-capsule",
        type=Path,
        default=RUN_DIR / "enron-handoff-verify-latest.doxabase.sqlite",
        help="Fresh capsule path. A timestamp suffix is added if it exists.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=DEFAULT_SUMMARY,
        help="JSON summary output path.",
    )
    args = parser.parse_args()

    doxabase_import_path = None
    if args.doxabase_dir.exists():
        doxabase_import_path = str(args.doxabase_dir.resolve())
        sys.path.insert(0, doxabase_import_path)
    try:
        from doxabase import DoxaBase, to_dict  # noqa: PLC0415
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Could not import doxabase. Pass --doxabase-dir /path/to/doxabase "
            "or set DOXABASE_CHECKOUT to a checkout path."
        ) from exc

    output_capsule = unique_capsule_path(args.output_capsule)
    receiver = DoxaBase.create(output_capsule, overwrite=False)
    imported = receiver.import_handoff_bundle(args.manifest, validation_scope="all")
    imported_validation = to_dict(receiver.validate_graph(scope="all"))
    imported_brief = to_dict(
        receiver.project_brief(limit=100, profile_candidate_limit=50)
    )

    source_comparison = None
    if args.source_capsule.exists():
        source = DoxaBase(args.source_capsule)
        source_validation = to_dict(source.validate_graph(scope="all"))
        source_brief = to_dict(
            source.project_brief(limit=100, profile_candidate_limit=50)
        )
        source_comparison = {
            "source_validation_conforms": source_validation.get("conforms"),
            "source_key_counts": source_brief.get("key_counts"),
            "imported_key_counts": imported_brief.get("key_counts"),
            "key_counts_match": source_brief.get("key_counts")
            == imported_brief.get("key_counts"),
            "source_query_readiness": source_brief.get(
                "dataset_query_readiness_counts"
            ),
            "imported_query_readiness": imported_brief.get(
                "dataset_query_readiness_counts"
            ),
        }

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    summary = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "manifest": str(args.manifest),
        "doxabase_import_path": doxabase_import_path or "installed package",
        "output_capsule": str(output_capsule),
        "imported_revision_iris": to_dict(imported).get("revision_iris"),
        "imported_validation": {
            "conforms": imported_validation.get("conforms"),
            "result_count": imported_validation.get("result_count"),
        },
        "imported_key_counts": imported_brief.get("key_counts"),
        "imported_dataset_query_readiness_counts": imported_brief.get(
            "dataset_query_readiness_counts"
        ),
        "manifest_sensitive_literal_count": manifest.get("sensitive_literal_count"),
        "manifest_recovery_complete": manifest.get("recovery_complete"),
        "manifest_shareability_review_status": manifest.get(
            "shareability_review_status"
        ),
        "source_comparison": source_comparison,
    }
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))

    if not imported_validation.get("conforms"):
        return 1
    if source_comparison and not source_comparison["key_counts_match"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
