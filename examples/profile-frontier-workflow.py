from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from doxabase import DoxaBase
from doxabase.mcp_tools import load_example_fixtures_tool
from examples._runtime_paths import example_artifact, example_run_dir, reset_file


RUN_DIR = example_run_dir(
    "profile-frontier-workflow",
    "/tmp/doxabase-profile-frontier-workflow",
)
CAPSULE = example_artifact(
    "profile-frontier-workflow",
    "/tmp/doxabase-profile-frontier-workflow.sqlite",
    filename="capsule.sqlite",
)
BASE = "https://example.test/profile-frontier-workflow#"


def main() -> None:
    reset_file(CAPSULE)

    db = DoxaBase.create(CAPSULE, overwrite=True)
    loaded = load_example_fixtures_tool(db, replace=True)

    baseline = db.project_brief(limit=10, profile_candidate_limit=2)
    dataset_iri, evidence_iri = _record_synthetic_profile_run(db)
    after_profile = db.project_brief(limit=10, profile_candidate_limit=2)
    profile_run = db.describe_profile_run(dataset_iri, evidence_iri, limit=None)
    draft = db.draft_profile_map_updates(dataset_iri, evidence_iri)
    staged = db.stage_profile_map_updates(
        dataset_iri,
        evidence_iri,
        accepted_recommendation_indexes=draft.representative_recommendation_indexes,
    )
    staged_iri = staged.staged_revision.revision_iri
    after_stage = db.project_brief(limit=10, profile_candidate_limit=2)
    recovery = db.plan_staged_revision_recovery([staged_iri])
    validation = db.validate_graph(scope="all")

    print("# DoxaBase Profile Frontier Workflow")
    print(f"Capsule: {CAPSULE}")
    print(f"Loaded fixture triples: {loaded['total_imported']}")
    print(f"Baseline profile queues: {baseline.profile_queue_counts}")
    print(f"Profile dataset: {dataset_iri}")
    print(f"Profile evidence: {evidence_iri}")
    print(f"Profile observations: {profile_run.total_profile_count}")
    print(f"Profile draft recommendations: {draft.recommendation_count}")
    print(f"Representative recommendations: {draft.representative_recommendation_indexes}")
    print(f"After-profile queues: {after_profile.profile_queue_counts}")
    print(f"Staged profile revision: {staged_iri}")
    print(f"Staged recommendation indexes: {staged.staged_recommendation_indexes}")
    print(f"After-stage profile queues: {after_stage.profile_queue_counts}")
    print(f"Recovery queue counts: {recovery.next_action_queue_item_counts}")
    print(f"Mutation frontier: {recovery.mutation_frontier_iris}")
    print(f"Validation conforms: {validation.conforms}")


def _record_synthetic_profile_run(db: DoxaBase) -> tuple[str, str]:
    dataset_iri = f"{BASE}Orders"
    evidence_iri = f"{BASE}OrdersProfileEvidence"
    storage_iri = f"{BASE}OrdersLocalStorage"
    layout_iri = f"{BASE}OrdersCsvLayout"
    status_column_iri = f"{BASE}OrdersStatus"
    settlement_column_iri = f"{BASE}OrdersSettlementMethod"

    db.record_map_storage_access(
        storage_iri,
        label="Orders local scratch storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="directory",
        storage_root=str(RUN_DIR / "warehouse"),
        path_templates=["orders/current.csv"],
        layout_verification_status="rc:VerifiedByListingLayout",
        datasets=[dataset_iri],
    )
    db.record_map_physical_layout(
        layout_iri,
        label="Orders CSV layout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
        datasets=[dataset_iri],
    )
    db.record_map_dataset(
        dataset_iri,
        label="Orders profile-frontier workflow table",
        is_table=True,
        row_count_snapshot=10,
        storage_accesses=[storage_iri],
        physical_layouts=[layout_iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_column(
        status_column_iri,
        table_iri=dataset_iri,
        column_name="status",
        nullable=False,
    )

    db.record_profile_bundle(
        dataset_iri,
        dataset_summary="Orders was profiled with a synthetic full-table scan.",
        evidence_summary="Synthetic full-scan profile output for frontier coverage.",
        evidence_sources=["scratch://profile-frontier-workflow/orders-profile.json"],
        shared_evidence_iri=evidence_iri,
        sample_size=12,
        sample_scope="All rows in the scratch Orders table.",
        sample_method="Synthetic full-table aggregate profile.",
        row_count=12,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column_iri,
                "column_name": "status",
                "summary": "Status had nulls in the synthetic full scan.",
                "null_count": 2,
                "distinct_count": 3,
            },
            {
                "column_iri": settlement_column_iri,
                "column_name": "settlement_method",
                "summary": "Settlement method was observed but is not mapped yet.",
                "null_count": 0,
                "distinct_count": 2,
            },
        ],
    )
    return dataset_iri, evidence_iri


if __name__ == "__main__":
    main()
