from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from doxabase import DoxaBase
from doxabase.parquet_manifest import (
    ParquetColumnMetadata,
    ParquetFileMetadata,
    build_parquet_profile_manifest,
)
from doxabase.profile_manifest_merge import merge_reviewed_profile_facts
from doxabase.profile_to_capsule import apply_manifest_file
from examples._runtime_paths import example_artifact, example_run_dir


RUN_DIR = example_run_dir(
    "rich-profile-manifest-smoke",
    "/tmp/doxabase-rich-profile-manifest-smoke",
)
CAPSULE = example_artifact(
    "rich-profile-manifest-smoke",
    "/tmp/doxabase-rich-profile-manifest-smoke/capsule.sqlite",
    filename="capsule.sqlite",
)
SCAFFOLD_PATH = example_artifact(
    "rich-profile-manifest-smoke",
    "/tmp/doxabase-rich-profile-manifest-smoke/scaffold.json",
    filename="scaffold.json",
)
PROFILE_FACTS_PATH = example_artifact(
    "rich-profile-manifest-smoke",
    "/tmp/doxabase-rich-profile-manifest-smoke/external-profile-facts.json",
    filename="external-profile-facts.json",
)
MANIFEST_PATH = example_artifact(
    "rich-profile-manifest-smoke",
    "/tmp/doxabase-rich-profile-manifest-smoke/reviewed-manifest.json",
    filename="reviewed-manifest.json",
)
DATA_DIR = RUN_DIR / "data"
PARQUET_PATH = DATA_DIR / "messages.parquet"
BASE = "https://example.test/rich-profile-manifest#"
AGENT = "urn:doxabase:rich-profile-manifest-smoke"


def main() -> None:
    _reset_run_dir()
    _write_placeholder_parquet_path()
    _write_external_profile_facts()

    scaffold = build_parquet_profile_manifest(
        [PARQUET_PATH],
        base_iri=BASE,
        observed_by=AGENT,
        storage_root=DATA_DIR,
        metadata_reader=_metadata_reader,
    )
    SCAFFOLD_PATH.write_text(
        json.dumps(scaffold, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    reviewed_manifest = merge_reviewed_profile_facts(
        scaffold,
        _external_profile_facts(),
        profile_facts_source=str(PROFILE_FACTS_PATH),
    )
    _add_reviewed_handoff_context(reviewed_manifest)
    MANIFEST_PATH.write_text(
        json.dumps(reviewed_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    applied = apply_manifest_file(
        capsule_path=CAPSULE,
        manifest_path=MANIFEST_PATH,
    )

    table_iri = applied["table_iris"][0]
    evidence_iri = applied["shared_evidence_iris"][0]
    view_iri = applied["analysis_view_iris"][0]
    domain_view_iri = applied["analysis_view_iris"][1]
    domain_evidence_iri = applied["domain_network_profile_evidence_iris"][0]
    with DoxaBase.open_readonly(CAPSULE) as db:
        dataset = db.describe_dataset(table_iri)
        profile_run = db.describe_profile_run(table_iri, evidence_iri)
        domain_profile_run = db.describe_profile_run(table_iri, domain_evidence_iri)
        draft = db.draft_profile_map_updates(table_iri, evidence_iri)
        query_context = db.describe_query_context(table_iri)
        view_context = db.describe_query_context(view_iri)
        analysis_view = db.describe_analysis_view(view_iri)
        domain_view = db.describe_analysis_view(domain_view_iri)
        validation = db.validate_graph(scope="all")

    print("# DoxaBase Rich Profile Manifest Smoke")
    print(f"Run directory: {RUN_DIR}")
    print(f"Scaffold tables: {len(scaffold['tables'])}")
    print(f"Reviewed manifest tables: {applied['table_count']}")
    print(f"Caveats: {applied['caveat_count']}")
    print(f"Profile observations: {applied['profile_observation_count']}")
    print(f"Analysis views: {applied['analysis_view_count']}")
    print(f"Domain network profiles: {applied['domain_network_profile_count']}")
    print(
        "Domain network observations: "
        f"{applied['domain_network_profile_observation_count']}"
    )
    print(f"Dataset columns: {len(dataset.columns)}")
    print(
        "Profile run returned: "
        f"{profile_run.returned_profile_count}/{profile_run.total_profile_count}"
    )
    print(
        "Domain profile run returned: "
        f"{domain_profile_run.returned_profile_count}/"
        f"{domain_profile_run.total_profile_count}"
    )
    print(f"Profile draft recommendations: {draft.recommendation_count}")
    print("Reviewed layout status: rc:VerifiedByListingLayout")
    print(f"Table query readiness: {query_context.readiness}")
    print(f"Table query issues: {[issue.code for issue in query_context.issues]}")
    print(f"Analysis view readiness: {view_context.readiness}")
    print(f"Analysis view snippets: {len(analysis_view.query_snippets)}")
    print(f"Domain view caveats: {len(domain_view.caveats)}")
    print(f"Validation conforms: {validation.conforms}")


def _reset_run_dir() -> None:
    if RUN_DIR.exists():
        shutil.rmtree(RUN_DIR)
    DATA_DIR.mkdir(parents=True)


def _write_placeholder_parquet_path() -> None:
    PARQUET_PATH.write_text(
        "placeholder path for reviewed metadata; not read by DoxaBase\n",
        encoding="utf-8",
    )


def _metadata_reader(path: Path) -> ParquetFileMetadata:
    return ParquetFileMetadata(
        path=path,
        row_count=12,
        compression_codec="rc:ZstdCompression",
        columns=[
            ParquetColumnMetadata("message_id", "string", nullable=False),
            ParquetColumnMetadata("sender_domain", "string", nullable=True),
            ParquetColumnMetadata("direction", "string", nullable=True),
            ParquetColumnMetadata("attachment_count", "int32", nullable=False),
            ParquetColumnMetadata(
                "sent_at",
                "timestamp[us, tz=UTC]",
                nullable=True,
            ),
        ],
    )


def _write_external_profile_facts() -> None:
    PROFILE_FACTS_PATH.write_text(
        json.dumps(_external_profile_facts(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _external_profile_facts() -> dict[str, object]:
    table_iri = f"{BASE}messages"
    return {
        "format": "doxabase.reviewed_profile_facts.v1",
        "tables": [
            {
                "iri": table_iri,
                "row_count": 12,
                "sample_scope": (
                    "All rows in the reviewed synthetic message snapshot."
                ),
                "sample_method": (
                    "External profiler full scan; DoxaBase recorded reviewed "
                    "aggregates and did no row I/O."
                ),
                "evidence_summary": (
                    "Reviewed external profiler facts for the synthetic "
                    "messages Parquet snapshot."
                ),
                "evidence_sources": [str(PROFILE_FACTS_PATH), PARQUET_PATH.as_uri()],
                "shared_evidence_iri": f"{BASE}messages_profile_evidence",
                "layout_verification_status": "rc:VerifiedByListingLayout",
                "layout_verification_note": (
                    "Reviewer confirmed the dataset-owned Parquet path "
                    "template and local footer metadata."
                ),
                "physical_layout_verification_status": (
                    "rc:VerifiedByListingLayout"
                ),
                "physical_layout_verification_note": (
                    "Reviewer confirmed the Parquet physical layout metadata."
                ),
                "columns": {
                    "message_id": {"null_count": 0, "distinct_count": 12},
                    "sender_domain": {
                        "null_count": 0,
                        "distinct_count": 4,
                        "value_frequencies": [
                            {"value": "enron.com", "frequency": 6},
                            {"value": "example.org", "frequency": 3},
                            {"value": "partner.test", "frequency": 2},
                            {"value": "vendor.test", "frequency": 1},
                        ],
                    },
                    "direction": {
                        "null_count": 0,
                        "distinct_count": 3,
                        "value_frequencies": [
                            {"value": "internal", "frequency": 5},
                            {"value": "outbound", "frequency": 4},
                            {"value": "inbound", "frequency": 3},
                        ],
                    },
                    "attachment_count": {
                        "null_count": 0,
                        "distinct_count": 4,
                        "profile_metrics": [
                            {"metric": "rc:MinimumValue", "value": 0},
                            {"metric": "rc:MaximumValue", "value": 5},
                            {"metric": "rc:MeanValue", "value": 1.25},
                        ],
                    },
                    "sent_at": {"null_count": 1, "distinct_count": 11},
                },
            }
        ],
    }


def _add_reviewed_handoff_context(manifest: dict[str, object]) -> None:
    table = manifest["tables"][0]
    if not isinstance(table, dict):
        raise RuntimeError("Expected scaffold table object")
    table_iri = str(table["iri"])
    view_iri = f"{BASE}external_domain_messages"
    domain_view_iri = f"{BASE}domain_network_profile_view"
    domain_caveat_iri = f"{BASE}domain_network_extractability_caveat"

    table.update(
        {
            "label": "Messages reviewed profile",
            "dataset_summary": (
                "Messages profile combines Parquet footer/schema metadata with "
                "reviewed external aggregate profile facts."
            ),
            "row_semantics": "rc:EventRow",
            "schema_stability": "rc:InferredSchema",
            "pattern_summary": (
                "Reviewed profile facts are complete enough for handoff."
            ),
            "pattern_text": (
                "The synthetic message table has reviewed schema, route, row "
                "count, column null/distinct counts, value frequencies, and a "
                "domain-analysis view plus network aggregates in one manifest."
            ),
            "pattern_rationale": (
                "The scaffold provides conservative storage/schema context; the "
                "external profiler sidecar supplies reviewed aggregate facts."
            ),
        }
    )

    manifest["analysis_views"] = [
        {
            "iri": view_iri,
            "label": "External domain messages",
            "source_datasets": [table_iri],
            "row_count_snapshot": 6,
            "denominator_description": (
                "Rows in the reviewed synthetic message snapshot whose "
                "direction is inbound or outbound."
            ),
            "query_snippets": [
                {
                    "label": "External domain message view",
                    "query_text": (
                        "select * from messages "
                        "where direction in ('inbound', 'outbound')"
                    ),
                    "query_language": "DuckDB SQL",
                    "query_engine": "duckdb",
                },
                {
                    "label": "External direction count check",
                    "query_text": (
                        "select direction, count(*) from messages "
                        "group by direction order by direction"
                    ),
                    "query_language": "DuckDB SQL",
                    "query_engine": "duckdb",
                },
            ],
        }
    ]
    manifest["domain_network_profiles"] = [
        {
            "dataset_iri": table_iri,
            "summary": "Domain extraction coverage for reviewed message rows.",
            "evidence_summary": (
                "Reviewed aggregate domain-network profile for the synthetic "
                "messages Parquet snapshot."
            ),
            "evidence_sources": [str(PROFILE_FACTS_PATH)],
            "evidence_iri": f"{BASE}domain_network_profile_evidence",
            "sample_size": 12,
            "sample_scope": "All rows in the reviewed synthetic message snapshot.",
            "sample_method": (
                "External aggregate over canonicalized sender-domain and "
                "direction fields."
            ),
            "extraction_method": (
                "Reviewed sender-domain extraction from the external profiler."
            ),
            "coverage_counts": [
                {"bucket": "sender_domain_extracted", "count": 12},
                {"bucket": "sender_domain_missing", "count": 0},
            ],
            "coverage_counts_exhaustive": True,
            "sender_domain_counts": [
                {"domain": "enron.com", "count": 6},
                {"domain": "example.org", "count": 3},
                {"domain": "partner.test", "count": 2},
                {"domain": "vendor.test", "count": 1},
            ],
            "recipient_domain_counts": [
                {"domain": "enron.com", "count": 5},
                {"domain": "example.org", "count": 4},
                {"domain": "partner.test", "count": 2},
                {"domain": "vendor.test", "count": 1},
            ],
            "domain_pair_counts": [
                {
                    "sender_domain": "enron.com",
                    "recipient_domain": "example.org",
                    "count": 5,
                },
                {
                    "sender_domain": "example.org",
                    "recipient_domain": "enron.com",
                    "count": 5,
                },
            ],
            "analysis_view_iri": domain_view_iri,
            "analysis_view_label": "Domain-network denominator rows",
            "analysis_view_description": (
                "Reviewed denominator for the aggregate sender-domain profile."
            ),
            "analysis_view_row_count_snapshot": 12,
            "analysis_view_query_text": (
                "select * from messages where sender_domain is not null"
            ),
            "analysis_view_query_language": "DuckDB SQL",
            "analysis_view_query_engine": "duckdb",
            "caveat_iri": domain_caveat_iri,
            "caveat_label": "Domain extraction caveat",
            "caveat_description": (
                "Domain-network interpretation is bounded by extraction "
                "coverage and reviewed aggregate counts."
            ),
            "pattern_summary": "Domain-network coverage must accompany graphs.",
            "pattern_text": (
                "The profile records sender-domain coverage and aggregate "
                "domain-pair counts before any network interpretation."
            ),
            "pattern_rationale": (
                "Aggregate network profiles are useful handoff context only "
                "when extraction coverage is preserved with them."
            ),
        }
    ]


if __name__ == "__main__":
    main()
