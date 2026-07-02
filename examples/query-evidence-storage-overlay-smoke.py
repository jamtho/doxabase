from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from doxabase import DoxaBase
from examples._runtime_paths import example_run_dir


RUN_DIR = example_run_dir(
    "query-evidence-storage-overlay-smoke",
    "/tmp/doxabase-query-evidence-storage-overlay-smoke",
)
CAPSULE = RUN_DIR / "capsule.sqlite"
WAREHOUSE = RUN_DIR / "warehouse"
CSV_PATH = WAREHOUSE / "orders.csv"
QUERY_PATH = RUN_DIR / "orders_status_summary.sql"
RESULT_PATH = RUN_DIR / "orders_status_summary.result.json"
BASE = "https://example.test/query-evidence-storage-overlay-smoke#"


def main() -> None:
    if RUN_DIR.exists():
        shutil.rmtree(RUN_DIR)
    WAREHOUSE.mkdir(parents=True)

    _write_inputs()
    rows, header = _read_csv()
    _write_result(rows)

    db = DoxaBase.create(CAPSULE, overwrite=True)
    dataset_iri = _record_table_without_physical_metadata(db, header)

    baseline = db.describe_query_context(dataset_iri)
    query_result = db.record_query_result(
        summary="Orders status query scanned the reviewed local CSV.",
        observed_asset=dataset_iri,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path=str(QUERY_PATH),
        query_hash=f"sha256:{_sha256_text(QUERY_PATH.read_text(encoding='utf-8'))}",
        result_sources=[str(RESULT_PATH)],
        scanned_source_paths=[str(CSV_PATH)],
        sample_size=len(rows),
        sample_scope="All rows in the reviewed Orders CSV.",
        sample_method="External read-only aggregate query using Python csv.",
        row_count=len(rows),
    )

    evidence_context = db.describe_query_context(dataset_iri)
    profile_action = _single_action(evidence_context, "describe_profile_run")
    overlay_action = _single_action(
        evidence_context,
        "draft_query_evidence_storage_overlay",
    )
    route_candidate = overlay_action.evidence_storage_route_candidates[0]
    candidate_arguments = route_candidate[
        "draft_query_evidence_storage_overlay_candidate_arguments"
    ]

    draft = db.draft_query_evidence_storage_overlay(
        dataset_iri,
        query_result.evidence_iri,
        **candidate_arguments,
        storage_label="Reviewed Orders CSV storage route",
        physical_layout_label="Reviewed Orders CSV layout",
        route_roles=["rc:CurrentRoute"],
        layout_verification_note=(
            "Reviewed query evidence scanned warehouse/orders.csv."
        ),
    )
    still_before_apply = db.describe_query_context(dataset_iri)
    staged = db.stage_graph_revision(**draft.stage_arguments)
    check = db.check_staged_revision_apply(staged.revision_iri)
    applied = db.apply_staged_revision(staged.revision_iri)

    final_context = db.describe_query_context(dataset_iri)
    plan = db.draft_query_plan(dataset_iri)
    validation = db.validate_graph(scope="all")

    print("# DoxaBase Query Evidence Storage Overlay Smoke")
    print(f"Capsule: {CAPSULE}")
    print(f"CSV: {CSV_PATH}")
    print(f"Baseline readiness: {baseline.readiness}")
    print(f"Baseline candidates: {len(baseline.query_target_candidates)}")
    print(f"Recorded evidence status: {query_result.execution_status}")
    print(f"Profile inspection action: {profile_action.tool_name}")
    print(f"Overlay action required extras: {overlay_action.required_extra_arguments}")
    print(f"Route candidate kind: {route_candidate['candidate_kind']}")
    print(f"Candidate path templates: {candidate_arguments['path_templates']}")
    print(
        "Candidate argument keys: "
        f"{', '.join(sorted(candidate_arguments))}"
    )
    print(f"Draft result: {draft.result_kind}")
    print(f"Draft source readiness: {draft.source_query_context_readiness}")
    print(f"Draft validation conforms: {draft.validation_conforms}")
    print(f"Still before apply readiness: {still_before_apply.readiness}")
    print(f"Staged overlay check: {check.status} / {check.decision}")
    print(f"Applied overlay: {applied.patches_applied} patch")
    print(f"Final readiness: {final_context.readiness}")
    print(f"Draft handoff: {plan.handoff_kind}")
    print(f"Ready for execution: {plan.review_gate.ready_for_execution_attempt}")
    print(f"Scan function: {plan.scan.function}")
    print(f"URI template: {plan.scan.uri_template}")
    print(f"Validation conforms: {validation.conforms}")


def _write_inputs() -> None:
    CSV_PATH.write_text(
        "\n".join(
            [
                "order_id,status,amount_cents",
                "1,paid,1200",
                "2,pending,500",
                "3,paid,2500",
                "4,refunded,700",
                "",
            ]
        ),
        encoding="utf-8",
    )
    QUERY_PATH.write_text(
        "\n".join(
            [
                "select",
                "  status,",
                "  count(*) as order_count,",
                "  sum(amount_cents) as amount_cents",
                "from orders",
                "group by status",
                "order by status;",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _read_csv() -> tuple[list[dict[str, str]], list[str]]:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        header = list(reader.fieldnames or [])
    expected = ["order_id", "status", "amount_cents"]
    if header != expected:
        raise RuntimeError(f"Unexpected CSV header: {header}")
    return rows, header


def _write_result(rows: list[dict[str, str]]) -> None:
    by_status: dict[str, dict[str, int | str]] = {}
    for row in rows:
        status = row["status"]
        bucket = by_status.setdefault(
            status,
            {"status": status, "order_count": 0, "amount_cents": 0},
        )
        bucket["order_count"] = int(bucket["order_count"]) + 1
        bucket["amount_cents"] = int(bucket["amount_cents"]) + int(
            row["amount_cents"]
        )
    result_rows = [by_status[status] for status in sorted(by_status)]
    RESULT_PATH.write_text(
        json.dumps(result_rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _record_table_without_physical_metadata(
    db: DoxaBase,
    header: list[str],
) -> str:
    dataset_iri = f"{BASE}Orders"
    columns = [f"{BASE}Orders_{column}" for column in header]
    db.record_map_dataset(
        dataset_iri,
        label="Orders smoke table without physical metadata",
        is_table=True,
        columns=columns,
    )
    for column_iri, column_name in zip(columns, header):
        db.record_map_column(
            column_iri,
            table_iri=dataset_iri,
            column_name=column_name,
        )
    return dataset_iri


def _single_action(context, tool_name: str):
    matches = [
        action
        for action in context.suggested_next_actions
        if action.tool_name == tool_name
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {tool_name} action, got {len(matches)}")
    return matches[0]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    main()
