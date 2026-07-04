from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from doxabase import DoxaBase
from doxabase.analysis_packet import apply_manifest_file
from examples._runtime_paths import example_artifact, example_run_dir


RUN_DIR = example_run_dir(
    "analysis-packet-manifest-smoke",
    "/tmp/doxabase-analysis-packet-manifest-smoke",
)
CAPSULE = example_artifact(
    "analysis-packet-manifest-smoke",
    "/tmp/doxabase-analysis-packet-manifest-smoke/capsule.sqlite",
    filename="capsule.sqlite",
)
MANIFEST_PATH = example_artifact(
    "analysis-packet-manifest-smoke",
    "/tmp/doxabase-analysis-packet-manifest-smoke/analysis-packet.json",
    filename="analysis-packet.json",
)
ARTIFACT_DIR = RUN_DIR / "artifacts"
BASE = "https://example.test/analysis-packet-manifest#"


def main() -> None:
    _reset_run_dir()
    _write_sidecar_artifacts()

    with DoxaBase.create(CAPSULE, overwrite=True) as db:
        _record_source_table(db)
        source_before = db.describe_query_context(f"{BASE}orders")

    _write_manifest()
    applied = apply_manifest_file(
        capsule_path=CAPSULE,
        manifest_path=MANIFEST_PATH,
    )

    with DoxaBase.open_readonly(CAPSULE) as db:
        validation = db.validate_graph(scope="all")
        packet_slice = db.get_context_graph(
            [f"{BASE}paid_orders_packet"],
            profile="resource_brief",
        )
        view_iris = applied["analysis_view_iris"]
        view_readiness = [
            db.describe_query_context(view_iri).readiness for view_iri in view_iris
        ]
        view_query_snippet_counts = [
            len(db.describe_analysis_view(view_iri).query_snippets)
            for view_iri in view_iris
        ]
        source_after = db.describe_query_context(f"{BASE}orders")

    print("# DoxaBase Analysis Packet Manifest Smoke")
    print(f"Run directory: {RUN_DIR}")
    print(f"Source table before packet: {source_before.readiness}")
    print(f"Manifest format: {applied['manifest_format']}")
    print(f"Packet: {applied['packet_iri']}")
    print(f"Analysis views: {applied['analysis_view_count']}")
    print(f"Artifacts: {applied['artifact_count']}")
    print(f"Query recipes: {applied['query_recipe_count']}")
    print(f"Follow-up tasks: {applied['followup_task_count']}")
    print(f"Pattern recorded: {applied['pattern_iri'] is not None}")
    print(f"Packet slice resources: {len(packet_slice.resources)}")
    print(f"View readiness: {view_readiness}")
    print(f"View query snippets: {view_query_snippet_counts}")
    print(f"Source table after packet: {source_after.readiness}")
    print(f"Validation conforms: {validation.conforms}")


def _reset_run_dir() -> None:
    if RUN_DIR.exists():
        shutil.rmtree(RUN_DIR)
    ARTIFACT_DIR.mkdir(parents=True)


def _record_source_table(db: DoxaBase) -> None:
    (RUN_DIR / "orders.csv").write_text(
        "\n".join(
            [
                "order_id,status,amount_cents,order_date",
                "1,paid,1200,2026-06-01",
                "2,pending,500,2026-06-02",
                "3,paid,2500,2026-06-03",
                "4,refunded,700,2026-06-03",
                "",
            ]
        ),
        encoding="utf-8",
    )
    db.record_map_table_bundle(
        f"{BASE}orders",
        label="Orders reviewed source table",
        description="Synthetic order rows used by the packet manifest smoke.",
        columns=[
            {"column_name": "order_id", "physical_type": "rc:Integer"},
            {"column_name": "status", "physical_type": "rc:Varchar"},
            {"column_name": "amount_cents", "physical_type": "rc:Integer"},
            {"column_name": "order_date", "physical_type": "rc:Date"},
        ],
        path_templates=["orders.csv"],
        row_count_snapshot=4,
        row_semantics="rc:EventRow",
        schema_stability="rc:FixedSchema",
        layout_verification_status="rc:VerifiedByQueryLayout",
        layout_verification_note="Reviewed local CSV source table for the smoke.",
        storage_label="Orders local run directory",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        location_kind="directory",
        storage_root=str(RUN_DIR),
        route_roles=["rc:CurrentRoute"],
        storage_layout_verification_status="rc:VerifiedByListingLayout",
        storage_layout_verification_note=(
            "The example wrote orders.csv before recording the route."
        ),
        physical_layout_label="Orders CSV layout",
        file_format="rc:CSV",
        physical_layout_verification_status="rc:VerifiedByQueryLayout",
        physical_layout_verification_note=(
            "The example treats the CSV header as reviewed input."
        ),
    )


def _write_sidecar_artifacts() -> None:
    (ARTIFACT_DIR / "paid-orders-readout.md").write_text(
        "\n".join(
            [
                "# Paid Orders Readout",
                "",
                "Paid orders are a reviewed logical subpopulation.",
                "The result is locator-only evidence for this smoke example.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (ARTIFACT_DIR / "status-summary.json").write_text(
        json.dumps(
            {
                "paid_rows": 2,
                "open_rows": 1,
                "denominator": "orders.csv synthetic reviewed rows",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    # One transparent 1x1 PNG. The CLI records only the locator and dimensions.
    (ARTIFACT_DIR / "status-chart.png").write_bytes(
        bytes.fromhex(
            "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
            "1f15c4890000000d49444154789c6360000002000100ffff0300000600"
            "057bfab60000000049454e44ae426082"
        )
    )


def _write_manifest() -> None:
    packet = f"{BASE}paid_orders_packet"
    paid_view = f"{BASE}paid_orders_view"
    open_view = f"{BASE}open_orders_view"
    manifest = {
        "format": "doxabase.analysis_packet_manifest.v1",
        "packet_iri": packet,
        "label": "Paid orders analysis packet",
        "summary": (
            "Reviewed locator-only packet for paid and open order populations, "
            "starter query recipes, aggregate artifacts, and follow-up tasks."
        ),
        "evidence_sources": [
            str(ARTIFACT_DIR / "paid-orders-readout.md"),
            str(ARTIFACT_DIR / "status-summary.json"),
        ],
        "analysis_views": [
            {
                "iri": paid_view,
                "label": "Paid orders",
                "source_datasets": [f"{BASE}orders"],
                "row_count_snapshot": 2,
                "denominator_description": (
                    "Rows in the reviewed Orders table where status = 'paid'."
                ),
                "query_snippets": [
                    {
                        "label": "Paid orders view",
                        "query_text": "select * from orders where status = 'paid'",
                        "query_language": "DuckDB SQL",
                        "query_engine": "duckdb",
                    },
                    {
                        "label": "Paid orders count check",
                        "query_text": (
                            "select count(*) from orders where status = 'paid'"
                        ),
                        "query_language": "DuckDB SQL",
                        "query_engine": "duckdb",
                    },
                ],
            },
            {
                "iri": open_view,
                "label": "Open orders",
                "source_datasets": [f"{BASE}orders"],
                "row_count_snapshot": 1,
                "denominator_description": (
                    "Rows in the reviewed Orders table where status = 'pending'."
                ),
                "query_snippets": [
                    {
                        "label": "Open orders view",
                        "query_text": (
                            "select * from orders where status = 'pending'"
                        ),
                        "query_language": "DuckDB SQL",
                        "query_engine": "duckdb",
                    }
                ],
            },
        ],
        "query_recipes": [
            {
                "label": "Register source CSV",
                "query_text": (
                    "create view orders as select * from "
                    "read_csv_auto('orders.csv')"
                ),
                "query_language": "DuckDB SQL",
                "query_engine": "duckdb",
                "targets": [f"{BASE}orders"],
            },
            {
                "label": "Status rollup",
                "query_text": (
                    "select status, count(*) as row_count "
                    "from orders group by status order by status"
                ),
                "query_language": "DuckDB SQL",
                "query_engine": "duckdb",
                "targets": [paid_view, open_view],
            },
        ],
        "artifacts": [
            {
                "label": "Paid orders readout",
                "source_path": str(ARTIFACT_DIR / "paid-orders-readout.md"),
                "artifact_role": "report",
                "media_type": "text/markdown",
                "supports": [paid_view],
            },
            {
                "label": "Status summary JSON",
                "source_path": str(ARTIFACT_DIR / "status-summary.json"),
                "artifact_role": "aggregate_summary",
                "media_type": "application/json",
                "supports": [paid_view, open_view],
            },
            {
                "label": "Status chart",
                "source_path": str(ARTIFACT_DIR / "status-chart.png"),
                "artifact_role": "visualization",
                "media_type": "image/png",
                "image_width": 1,
                "image_height": 1,
                "supports": [paid_view, open_view],
            },
        ],
        "followup_tasks": [
            {
                "label": "Review status denominator",
                "task_text": (
                    "Confirm paid and open order counts before reporting a "
                    "conversion-rate denominator."
                ),
                "priority": "medium",
                "targets": [paid_view, open_view],
            },
            {
                "label": "Inspect artifact freshness",
                "task_text": (
                    "Check whether the locator-only Markdown, JSON, and PNG "
                    "sidecars match the latest reviewed source table."
                ),
                "priority": "low",
                "targets": [packet],
            },
        ],
        "pattern_summary": "Paid-order packet is a reusable analysis handoff.",
        "pattern_text": (
            "A packet seed lets future agents inspect the named denominators, "
            "recipes, artifacts, and follow-up tasks without rediscovering a "
            "sidecar folder by hand."
        ),
        "pattern_rationale": (
            "The packet links both logical views and all reviewed locator-only "
            "sidecars in one context-slice seed."
        ),
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
