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


RUN_DIR = Path("/tmp/doxabase-local-csv-query-smoke")
CAPSULE = RUN_DIR / "capsule.sqlite"
CSV_PATH = RUN_DIR / "orders.csv"
QUERY_PATH = RUN_DIR / "orders_status_summary.sql"
RESULT_PATH = RUN_DIR / "orders_status_summary.result.json"
BASE = "https://example.test/local-csv-query-smoke#"


def main() -> None:
    if RUN_DIR.exists():
        shutil.rmtree(RUN_DIR)
    RUN_DIR.mkdir(parents=True)

    _write_inputs()
    rows, header = _read_csv()
    result_payload = _status_summary(rows)
    RESULT_PATH.write_text(
        json.dumps(result_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    db = DoxaBase.create(CAPSULE, overwrite=True)
    dataset_iri = _record_catalog(db, header)
    query_context = db.describe_query_context(dataset_iri)
    plan = db.draft_query_plan(dataset_iri)
    query_hash = _sha256_text(QUERY_PATH.read_text(encoding="utf-8"))
    query_result = db.record_query_result(
        summary="Orders status summary grouped the reviewed local CSV.",
        observed_asset=dataset_iri,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path=str(QUERY_PATH),
        query_hash=f"sha256:{query_hash}",
        result_sources=[str(RESULT_PATH)],
        evidence_summary="Reviewed Python CSV aggregate over the local Orders CSV.",
        sample_size=len(rows),
        sample_scope="All rows in the reviewed local Orders CSV.",
        sample_method="External read-only full scan using Python csv.",
    )
    profile_run = db.describe_profile_run(dataset_iri, query_result.evidence_iri)
    validation = db.validate_graph(scope="all")

    print("# DoxaBase Local CSV Query Smoke")
    print(f"Capsule: {CAPSULE}")
    print(f"CSV: {CSV_PATH}")
    print(f"Rows checked: {len(rows)}")
    print(f"Header checked: {', '.join(header)}")
    print(f"Query readiness: {query_context.readiness}")
    print(f"Draft handoff: {plan.handoff_kind}")
    print(f"Ready for execution: {plan.review_gate.ready_for_execution_attempt}")
    print(f"Scan function: {plan.scan.function}")
    print(f"Engine used: {query_result.engine}")
    print(f"Query hash: {query_result.query_hash}")
    print(f"Result source: {query_result.result_sources[0]}")
    print(f"Recorded query result: {query_result.observation_iri}")
    print(f"Evidence status: {profile_run.evidence.query_execution_status}")
    print(f"Evidence engine: {profile_run.evidence.query_engine}")
    print(f"Evidence query hash: {profile_run.evidence.query_hash}")
    print(f"Validation conforms: {validation.conforms}")


def _write_inputs() -> None:
    CSV_PATH.write_text(
        "\n".join(
            [
                "order_id,status,amount_cents,customer_state,order_date",
                "1,paid,1200,CA,2026-01-02",
                "2,pending,500,WA,2026-01-03",
                "3,paid,2500,CA,2026-01-03",
                "4,refunded,700,OR,2026-01-04",
                "5,paid,3200,WA,2026-01-04",
                "6,pending,450,CA,2026-01-05",
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
    if header != ["order_id", "status", "amount_cents", "customer_state", "order_date"]:
        raise RuntimeError(f"Unexpected CSV header: {header}")
    return rows, header


def _status_summary(rows: list[dict[str, str]]) -> list[dict[str, int | str]]:
    totals: dict[str, dict[str, int | str]] = {}
    for row in rows:
        status = row["status"]
        bucket = totals.setdefault(
            status,
            {"status": status, "order_count": 0, "amount_cents": 0},
        )
        bucket["order_count"] = int(bucket["order_count"]) + 1
        bucket["amount_cents"] = int(bucket["amount_cents"]) + int(
            row["amount_cents"]
        )
    return [totals[status] for status in sorted(totals)]


def _record_catalog(db: DoxaBase, header: list[str]) -> str:
    dataset_iri = f"{BASE}Orders"
    storage_iri = f"{BASE}OrdersLocalCsvStorage"
    layout_iri = f"{BASE}OrdersCsvLayout"
    column_iris = [f"{BASE}Orders_{column}" for column in header]

    db.record_map_storage_access(
        storage_iri,
        label="Orders local CSV object",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        location_kind="object",
        storage_root=str(CSV_PATH),
        layout_verification_status="rc:VerifiedByListingLayout",
        layout_verification_note="Example script checked the local CSV path and header.",
        datasets=[dataset_iri],
    )
    db.record_map_physical_layout(
        layout_iri,
        label="Orders CSV layout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByListingLayout",
        layout_verification_note="Header was read from the local CSV before planning.",
        datasets=[dataset_iri],
    )
    db.record_map_dataset(
        dataset_iri,
        label="Orders local CSV smoke table",
        is_table=True,
        columns=column_iris,
        row_semantics="rc:EventRow",
        schema_stability="rc:FixedSchema",
        storage_accesses=[storage_iri],
        physical_layouts=[layout_iri],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    for column_iri, column_name in zip(column_iris, header):
        db.record_map_column(
            column_iri,
            table_iri=dataset_iri,
            column_name=column_name,
        )
    return dataset_iri


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    main()
