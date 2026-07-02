from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from doxabase import DoxaBase
from examples._runtime_paths import example_artifact, example_run_dir


RUN_DIR = example_run_dir(
    "profile-to-capsule-cookbook",
    "/tmp/doxabase-profile-to-capsule-cookbook",
)
CAPSULE = example_artifact(
    "profile-to-capsule-cookbook",
    "/tmp/doxabase-profile-to-capsule-cookbook/source.sqlite",
    filename="source.sqlite",
)
RECEIVER_CAPSULE = example_artifact(
    "profile-to-capsule-cookbook",
    "/tmp/doxabase-profile-to-capsule-cookbook/receiver.sqlite",
    filename="receiver.sqlite",
)
TRIG_PATH = example_artifact(
    "profile-to-capsule-cookbook",
    "/tmp/doxabase-profile-to-capsule-cookbook/handoff.trig",
    filename="handoff.trig",
)
SNAPSHOT_PATH = example_artifact(
    "profile-to-capsule-cookbook",
    "/tmp/doxabase-profile-to-capsule-cookbook/revision-snapshots.json",
    filename="revision-snapshots.json",
)
MANIFEST_PATH = example_artifact(
    "profile-to-capsule-cookbook",
    "/tmp/doxabase-profile-to-capsule-cookbook/handoff-manifest.json",
    filename="handoff-manifest.json",
)
BASE = "https://example.test/profile-to-capsule#"
AGENT = "urn:doxabase:profile-to-capsule-cookbook"


def main() -> None:
    _reset_run_dir()

    with DoxaBase.create(CAPSULE, overwrite=True) as db:
        bundle = _record_reviewed_capsule(db)
        source_validation = db.validate_graph(scope="all")
        revision = db.record_graph_revision(
            summary="Profile-to-capsule cookbook recorded reviewed context",
            rationale=(
                "The cookbook records table schema, profile evidence, and a "
                "logical analysis view before exporting a recovery-complete "
                "handoff bundle."
            ),
            changed_graphs=["map", "observations", "patterns", "evidence"],
            included_graphs="project",
            revision_type="rc:ExportRevision",
            supporting_observations=bundle["profile_observation_iris"],
            supporting_patterns=bundle["supporting_pattern_iris"],
            revision_anchors=[bundle["dataset_iri"], bundle["analysis_view_iri"]],
            evidence=[bundle["profile_evidence_iri"]],
            validation_scope=source_validation.scope,
            validation_conforms=source_validation.conforms,
            validation_result_count=source_validation.result_count,
        )
        preflight = db.export_preflight(
            export_kind="handoff_bundle",
            graphs="project",
            revision_iris=[revision.revision_iri],
            validation_scope="all",
        )
        handoff = db.export_handoff_bundle(
            TRIG_PATH,
            SNAPSHOT_PATH,
            manifest_path=MANIFEST_PATH,
            revision_iris=[revision.revision_iri],
            overwrite=True,
            fail_on_sensitive=True,
            validation_scope="all",
        )
        source_counts = _selected_counts(db.graph_overview().key_counts)

    with DoxaBase.open_readonly(CAPSULE) as source:
        readonly_counts_match = source_counts == _selected_counts(
            source.graph_overview().key_counts,
        )

    with DoxaBase.create(RECEIVER_CAPSULE, overwrite=True) as receiver:
        imported = receiver.import_handoff_bundle(
            MANIFEST_PATH,
            validation_scope="all",
        )
        receiver_validation = receiver.validate_graph(scope="all")
        receiver_counts = _selected_counts(receiver.graph_overview().key_counts)
        receiver_dataset = receiver.describe_dataset(bundle["dataset_iri"])
        receiver_table_context = receiver.describe_query_context(bundle["dataset_iri"])
        receiver_view_context = receiver.describe_query_context(
            bundle["analysis_view_iri"],
        )

    print("# DoxaBase Profile-To-Capsule Cookbook")
    print(f"Run directory: {RUN_DIR}")
    print(f"Source capsule: {CAPSULE}")
    print(f"Receiver capsule: {RECEIVER_CAPSULE}")
    print(f"Table bundle columns: {len(bundle['table_column_iris'])}")
    print(f"Profile observations: {bundle['profile_observation_count']}")
    print(f"Profile draft recommendations: {bundle['profile_draft_count']}")
    print(f"Analysis view readiness: {bundle['analysis_view_readiness']}")
    print(f"Table query readiness: {bundle['table_query_readiness']}")
    print(f"Source validation conforms: {source_validation.conforms}")
    print(f"Export preflight decision: {preflight.decision}")
    print(f"Handoff scanner clean: {handoff.scanner_clean}")
    print(f"Handoff shareability status: {handoff.shareability_review_status}")
    print(f"Manifest path: {handoff.manifest_path}")
    print(f"Revision snapshots exported: {handoff.revision_snapshots.snapshot_count}")
    print(f"Readonly source counts match: {readonly_counts_match}")
    print(
        "Imported snapshot evidence complete: "
        f"{imported.recovery_summary.snapshot_evidence_complete}"
    )
    print(
        "Imported recovery next step: "
        f"{imported.recovery_summary.recommended_next_step}"
    )
    print(f"Receiver validation conforms: {receiver_validation.conforms}")
    print(f"Receiver counts match source: {receiver_counts == source_counts}")
    print(f"Receiver table columns: {len(receiver_dataset.columns)}")
    print(f"Receiver table readiness: {receiver_table_context.readiness}")
    print(f"Receiver analysis view readiness: {receiver_view_context.readiness}")


def _record_reviewed_capsule(db: DoxaBase) -> dict[str, Any]:
    dataset_iri = f"{BASE}orders"
    analysis_view_iri = f"{BASE}paid_orders_view"
    evidence_iri = f"{BASE}orders_profile_evidence"
    columns = [
        {
            "column_name": "order_id",
            "physical_type": "rc:Integer",
            "nullable": False,
            "summary": "order_id was populated in every reviewed row.",
            "null_count": 0,
            "distinct_count": 6,
        },
        {
            "column_name": "status",
            "physical_type": "rc:Varchar",
            "summary": "status had three reviewed values.",
            "null_count": 0,
            "distinct_count": 3,
            "value_frequencies": [
                {"value": "paid", "frequency": 3},
                {"value": "pending", "frequency": 2},
                {"value": "refunded", "frequency": 1},
            ],
        },
        {
            "column_name": "amount_cents",
            "physical_type": "rc:Integer",
            "summary": "amount_cents was populated in every reviewed row.",
            "null_count": 0,
            "distinct_count": 6,
        },
        {
            "column_name": "customer_state",
            "physical_type": "rc:Varchar",
            "summary": "customer_state had three reviewed values.",
            "null_count": 0,
            "distinct_count": 3,
        },
        {
            "column_name": "order_date",
            "physical_type": "rc:Date",
            "summary": "order_date covered four reviewed order dates.",
            "null_count": 0,
            "distinct_count": 4,
        },
    ]
    caveat = db.record_map_caveat(
        f"{BASE}profile_cookbook_caveat",
        label="Profile cookbook aggregate caveat",
        description=(
            "Counts and profiles in this example are reviewed aggregate facts, "
            "not rows read by DoxaBase."
        ),
        severity="rc:Minor",
        targets=[dataset_iri],
    )
    profiled_table = db.record_profiled_parquet_table(
        dataset_iri,
        label="Orders reviewed table",
        description="Synthetic reviewed order table used by the cookbook.",
        dataset_summary="Orders table profile captured reviewed aggregate counts.",
        evidence_summary=(
            "Reviewed synthetic profiler output for the profile-to-capsule "
            "cookbook."
        ),
        evidence_sources=["scratch://profile-to-capsule/orders-profile.json"],
        shared_evidence_iri=evidence_iri,
        observed_by=AGENT,
        columns=columns,
        path_templates=["orders/current.parquet"],
        row_count=6,
        sample_size=6,
        sample_scope="All rows in the reviewed synthetic Orders snapshot.",
        sample_method="Caller-supplied aggregate profile; DoxaBase did no I/O.",
        row_semantics="rc:EventRow",
        schema_stability="rc:FixedSchema",
        layout_verification_status="rc:VerifiedByQueryLayout",
        layout_verification_note=(
            "The example treats the schema and row count as pre-reviewed input."
        ),
        caveats=[caveat.iri],
        storage_access_iri=f"{BASE}orders_storage",
        storage_label="Orders local Parquet object",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        location_kind="directory",
        storage_root=str(RUN_DIR),
        storage_path_templates=["orders/current.parquet"],
        storage_layout_verification_status="rc:VerifiedByListingLayout",
        storage_layout_verification_note=(
            "Route shape is reviewed input; the cookbook does not read the file."
        ),
        physical_layout_iri=f"{BASE}orders_parquet_layout",
        physical_layout_label="Orders Parquet layout",
        compression_codec="rc:ZstdCompression",
        physical_layout_verification_status="rc:VerifiedByQueryLayout",
        pattern_summary="Orders cookbook profile is a full reviewed aggregate.",
        pattern_text=(
            "The table schema, row count, column profiles, and paid-order "
            "analysis view all come from the same reviewed synthetic snapshot."
        ),
        pattern_rationale=(
            "A future agent can start from the profile run and analysis view "
            "without rediscovering the denominator."
        ),
        pattern_support_scope="all_profiles",
    )
    table_bundle = profiled_table.table_bundle
    profile_bundle = profiled_table.profile_bundle
    analysis_view = db.record_map_analysis_view(
        analysis_view_iri,
        label="Paid orders logical view",
        description="Logical population for paid orders in the reviewed snapshot.",
        source_datasets=[dataset_iri],
        row_count_snapshot=3,
        caveats=[caveat.iri],
        denominator_label="Paid orders denominator",
        denominator_description=(
            "Rows from Orders where status is paid in the reviewed snapshot."
        ),
        denominator_row_count_snapshot=3,
        denominator_basis="status = 'paid' over the reviewed Orders snapshot",
        query_snippet_label="Paid orders DuckDB query",
        query_text=(
            "select *\n"
            "from orders\n"
            "where status = 'paid';\n"
        ),
        query_language="SQL",
        query_engine="DuckDB",
    )
    profile_run = db.describe_profile_run(dataset_iri, evidence_iri, limit=None)
    profile_draft = db.draft_profile_map_updates(dataset_iri, evidence_iri)
    table_context = db.describe_query_context(dataset_iri)
    view_context = db.describe_query_context(analysis_view_iri)
    profile_observation_iris = [
        profile_bundle.dataset_profile.observation.observation_iri,
        *[
            column_profile.observation.observation_iri
            for column_profile in profile_bundle.column_profiles
        ],
    ]
    supporting_pattern_iris = (
        [profile_bundle.dataset_profile.pattern.pattern_iri]
        if profile_bundle.dataset_profile.pattern is not None
        else []
    )
    return {
        "dataset_iri": dataset_iri,
        "analysis_view_iri": analysis_view.iri,
        "profile_evidence_iri": evidence_iri,
        "table_column_iris": table_bundle.column_iris,
        "profile_observation_iris": profile_observation_iris,
        "profile_observation_count": profile_run.total_profile_count,
        "profile_draft_count": profile_draft.recommendation_count,
        "supporting_pattern_iris": supporting_pattern_iris,
        "analysis_view_readiness": view_context.readiness,
        "table_query_readiness": table_context.readiness,
    }


def _selected_counts(key_counts: dict[str, int]) -> dict[str, int]:
    keys = [
        "datasets",
        "tables",
        "columns",
        "storage_accesses",
        "observations",
        "patterns",
        "evidence",
        "graph_revisions",
        "graph_snapshots",
    ]
    return {key: key_counts.get(key, 0) for key in keys}


def _reset_run_dir() -> None:
    if RUN_DIR.exists():
        shutil.rmtree(RUN_DIR)
    RUN_DIR.mkdir(parents=True)


if __name__ == "__main__":
    main()
