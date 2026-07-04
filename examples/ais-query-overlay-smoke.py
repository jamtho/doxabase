from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from doxabase import DoxaBase
from examples._runtime_paths import example_run_dir


RUN_DIR = example_run_dir(
    "ais-query-overlay-smoke",
    "/tmp/doxabase-ais-query-overlay-smoke",
)
CAPSULE = RUN_DIR / "capsule.sqlite"
AIS_FIXTURE = ROOT / "examples" / "manifest-prototype-rc" / "ais.trig"
AIS = "https://richcanopy.org/example/manifest/ais#"
DAILY_INDEX = AIS + "DailyIndex"


def main() -> None:
    if RUN_DIR.exists():
        shutil.rmtree(RUN_DIR)
    RUN_DIR.mkdir(parents=True)

    db = DoxaBase.create(CAPSULE, overwrite=True)
    db.import_trig(AIS_FIXTURE)

    baseline_context = db.describe_query_context(DAILY_INDEX)
    _record_reviewed_daily_index_overlay(db)

    overlay_context = db.describe_query_context(DAILY_INDEX)
    repair_group = _single_stale_partition_repair_group(overlay_context)
    repair_action = repair_group.actions[0]
    staged = db.stage_map_assertion_change(
        **repair_action["args"]["spec"],
        rationale=(
            "Reviewed DailyIndex wildcard storage as the intended query route; "
            "the inherited broadcast partition link is stale for DailyIndex."
        ),
    )
    repair_check = db.check_staged_revision_apply(staged.staged_revision.revision_iri)
    applied = db.apply_staged_revision(staged.staged_revision.revision_iri)

    repaired_context = db.describe_query_context(DAILY_INDEX)
    plan = db.draft_query_plan(DAILY_INDEX)
    validation = db.validate_graph(scope="all")

    print("# DoxaBase AIS Query Overlay Smoke")
    print(f"Capsule: {CAPSULE}")
    print(f"Baseline readiness: {baseline_context.readiness}")
    print(f"Baseline decision: {baseline_context.query_target_decision.status}")
    print(
        "Overlay repair: "
        f"{repair_group.repair_action_type} "
        f"({repair_group.pending_action_count} pending)"
    )
    print(f"Staged repair check: {repair_check.status} / {repair_check.decision}")
    print(
        "Applied repair: "
        f"{applied.patches_applied} patch, "
        f"{applied.triples_removed} triple removed"
    )
    print(f"Repaired readiness: {repaired_context.readiness}")
    print(f"Selected candidate index: {plan.source_context.selected_candidate_index}")
    print(f"Draft handoff: {plan.handoff_kind}")
    print(f"Ready for execution: {plan.review_gate.ready_for_execution_attempt}")
    print(f"Scan function: {plan.scan.function}")
    print(f"URI template: {plan.scan.uri_template}")
    print(f"Required bindings: {plan.required_bindings}")
    print(
        "Execution blockers: "
        f"{plan.review_gate.execution_attempt_blocking_reason_codes}"
    )
    print(f"Validation conforms: {validation.conforms}")


def _record_reviewed_daily_index_overlay(db: DoxaBase) -> None:
    db.record_map_column(
        AIS + "ix_vessel_names",
        table_iri=DAILY_INDEX,
        column_name="vessel_names",
        physical_type="rc:VarcharList",
    )
    db.record_map_storage_access(
        AIS + "daily_index_object_store_access",
        label="AIS DailyIndex object-store access",
        storage_protocol="rc:S3CompatibleStorage",
        storage_root="s3://ais-noaa/",
        endpoint_profile="local-minio",
        bucket_name="ais-noaa",
        region="local",
        path_style_access=True,
        credential_reference="profile:ais-readonly",
        access_mode="rc:ReadOnlyAccess",
        path_templates=["index/*/*.parquet"],
        layout_verification_status="rc:VerifiedByQueryLayout",
        layout_verification_note=(
            "Reviewed DuckDB/listing evidence identified the DailyIndex "
            "wildcard route."
        ),
        datasets=[DAILY_INDEX],
    )
    db.record_map_partition_scheme(
        AIS + "daily_index_date_partition",
        path_template="index/{year}/ais-{date}.parquet",
        partition_columns=[AIS + "ix_date"],
        granularity="rc:Daily",
        layout_verification_status="rc:VerifiedByQueryLayout",
        layout_verification_note=(
            "Reviewed DailyIndex partition route from observed index layout."
        ),
        datasets=[DAILY_INDEX],
    )
    layout = db.record_map_physical_layout(
        AIS + "daily_index_parquet_layout",
        file_format="rc:Parquet",
        compression_codec="rc:ZstdCompression",
        layout_verification_status="rc:VerifiedByQueryLayout",
        layout_verification_note=(
            "DuckDB verified DailyIndex Parquet layout in the reviewed handoff."
        ),
    )
    db.record_map_dataset(
        DAILY_INDEX,
        layout_verification_status="rc:VerifiedByQueryLayout",
        layout_verification_note=(
            "DuckDB verified the DailyIndex schema and "
            "s3://ais-noaa/index/*/*.parquet route."
        ),
        physical_layouts=[layout.iri],
    )


def _single_stale_partition_repair_group(context):
    repair_groups = [
        group
        for group in context.suggested_repair_action_groups
        if group.repair_action_type == "remove_stale_partition_scheme_link"
    ]
    if len(repair_groups) != 1:
        raise RuntimeError(
            "Expected one stale partition repair group, got "
            f"{len(repair_groups)}"
        )
    group = repair_groups[0]
    if group.pending_action_count != 1 or len(group.actions) != 1:
        raise RuntimeError(
            "Expected one pending stale partition repair action, got "
            f"{group.pending_action_count} pending and {len(group.actions)} actions"
        )
    return group


if __name__ == "__main__":
    main()
