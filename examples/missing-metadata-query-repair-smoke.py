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
    "missing-metadata-query-repair-smoke",
    "/tmp/doxabase-missing-metadata-query-repair-smoke",
)
CAPSULE = RUN_DIR / "capsule.sqlite"
CSV_PATH = RUN_DIR / "orders.csv"
BASE = "https://example.test/missing-metadata-query-repair-smoke#"


def main() -> None:
    if RUN_DIR.exists():
        shutil.rmtree(RUN_DIR)
    RUN_DIR.mkdir(parents=True)
    _write_csv()

    db = DoxaBase.create(CAPSULE, overwrite=True)
    dataset_iri = _record_table_without_physical_metadata(db)

    baseline = db.describe_query_context(dataset_iri)
    storage_group = _single_repair_group(baseline, "missing_storage_access")
    storage_stage = db.stage_query_storage_access_repair(
        dataset_iri=dataset_iri,
        storage_access_iri=f"{BASE}OrdersCsvStorage",
        label="Orders CSV storage",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        location_kind="object",
        storage_root=str(CSV_PATH),
        layout_verification_status="rc:VerifiedByListingLayout",
        layout_verification_note=(
            "Example smoke checked the local CSV path before staging storage."
        ),
        rationale=(
            "The reviewed local CSV is the intended physical source for the "
            "Orders smoke table."
        ),
    )
    storage_check = db.check_staged_revision_apply(storage_stage.revision_iri)
    db.apply_staged_revision(storage_stage.revision_iri)

    after_storage = db.describe_query_context(dataset_iri)
    layout_group = _single_repair_group(after_storage, "missing_physical_layout")
    layout_stage = db.stage_query_physical_layout_repair(
        dataset_iri=dataset_iri,
        layout_iri=f"{BASE}OrdersCsvLayout",
        label="Orders CSV layout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByListingLayout",
        layout_verification_note=(
            "Example smoke checked the local CSV header before staging layout."
        ),
        rationale=(
            "The reviewed local source is a CSV file, so query planning needs a "
            "CSV physical layout linked to the Orders table."
        ),
    )
    layout_check = db.check_staged_revision_apply(layout_stage.revision_iri)
    db.apply_staged_revision(layout_stage.revision_iri)

    repaired = db.describe_query_context(dataset_iri)
    plan = db.draft_query_plan(dataset_iri)
    validation = db.validate_graph(scope="all")

    print("# DoxaBase Missing Metadata Query Repair Smoke")
    print(f"Capsule: {CAPSULE}")
    print(f"CSV: {CSV_PATH}")
    print(f"Baseline readiness: {baseline.readiness}")
    print(f"Baseline repair group: {storage_group.issue_code}")
    print(f"Storage staged check: {storage_check.status} / {storage_check.decision}")
    print(f"After storage readiness: {after_storage.readiness}")
    print(f"Next repair group: {layout_group.issue_code}")
    print(f"Layout staged check: {layout_check.status} / {layout_check.decision}")
    print(f"Final readiness: {repaired.readiness}")
    print(f"Draft handoff: {plan.handoff_kind}")
    print(f"Ready for execution: {plan.review_gate.ready_for_execution_attempt}")
    print(f"Scan function: {plan.scan.function}")
    print(f"URI template: {plan.scan.uri_template}")
    print(f"Validation conforms: {validation.conforms}")


def _write_csv() -> None:
    CSV_PATH.write_text(
        "\n".join(
            [
                "order_id,status,amount_cents",
                "1,paid,1200",
                "2,pending,500",
                "3,paid,2500",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _record_table_without_physical_metadata(db: DoxaBase) -> str:
    dataset_iri = f"{BASE}Orders"
    columns = [
        f"{BASE}Orders_order_id",
        f"{BASE}Orders_status",
        f"{BASE}Orders_amount_cents",
    ]
    db.record_map_dataset(
        dataset_iri,
        label="Orders smoke table without physical metadata",
        is_table=True,
        columns=columns,
    )
    for column_iri, column_name in zip(
        columns,
        ["order_id", "status", "amount_cents"],
    ):
        db.record_map_column(
            column_iri,
            table_iri=dataset_iri,
            column_name=column_name,
        )
    return dataset_iri


def _single_repair_group(context, issue_code: str):
    groups = [
        group
        for group in context.suggested_repair_action_groups
        if group.issue_code == issue_code
    ]
    if len(groups) != 1:
        raise RuntimeError(
            f"Expected one {issue_code} repair group, got {len(groups)}"
        )
    return groups[0]


if __name__ == "__main__":
    main()
