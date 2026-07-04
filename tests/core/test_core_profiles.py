"""Split from test_doxabase_core.py (distillation Phase 2); tests verbatim."""

from tests.core.support_core import *  # noqa: F401,F403


def test_profile_privacy_orientation_payloads_redact_sensitive_evidence_summaries(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_PROFILE_ORIENTATION"
    redacted = "[REDACTED:fake_secret_marker]"
    dataset = "https://example.test/project#OrdersProfilePrivacy"
    evidence = "https://example.test/project#OrdersProfilePrivacyEvidence"

    db.record_dataset_profile(
        dataset,
        summary=f"Orders profile summary carried {fake_secret}.",
        evidence_summary=f"Orders profile evidence carried {fake_secret}.",
        evidence_sources=[f"test://profile/{fake_secret}/orders.json"],
        evidence_iri=evidence,
        sample_size=10,
        sample_scope=f"All rows in the profile fixture with {fake_secret}.",
        sample_method=f"Synthetic profiler run with {fake_secret}.",
        row_count=10,
        value_frequencies=[
            {"value": fake_secret, "frequency": 1},
            {"value": "ordinary", "frequency": 9},
        ],
        profile_metrics=[
            {
                "metric": "rc:MaximumValue",
                "value": f"metric value {fake_secret}",
            }
        ],
        map_label="Orders profile privacy",
        map_description=f"Dataset description carried {fake_secret}.",
        is_table=True,
    )

    profile_run = db.describe_profile_run(dataset, evidence)

    assert profile_run.dataset.description == redacted
    assert profile_run.evidence.summary == redacted
    assert profile_run.evidence.sources == [redacted]
    profile = profile_run.dataset_profile_observations[0]
    assert profile.summary == redacted
    assert profile.sample_scope == redacted
    assert profile.sample_method == redacted
    assert [item.value for item in profile.value_frequencies] == [
        "ordinary",
        redacted,
    ]
    assert redacted in {metric.value for metric in profile.profile_metrics}
    profile_run_payload = json.dumps(to_jsonable(profile_run), sort_keys=True)
    assert fake_secret not in profile_run_payload
    assert redacted in profile_run_payload

    query_context = db.describe_query_context(dataset)
    query_payload = json.dumps(
        to_jsonable(query_context.suggested_next_actions),
        sort_keys=True,
    )
    assert fake_secret not in query_payload
    assert redacted in query_payload

    review_bundle = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        tmp_path / "profile-review.md",
    )
    review_payload = json.dumps(to_jsonable(review_bundle), sort_keys=True)
    assert fake_secret not in review_payload
    assert redacted in review_payload

    route_dataset = "https://example.test/project#OrdersProfileRoutePrivacy"
    route_evidence = (
        "https://example.test/project#OrdersProfileRoutePrivacyEvidence"
    )
    project_metric = f"https://example.test/project#{fake_secret}"
    db.record_dataset_profile(
        route_dataset,
        summary="Orders profile route privacy.",
        evidence_summary="Orders profile route evidence.",
        evidence_sources=["test://profile/orders-route.json"],
        evidence_iri=route_evidence,
        row_count=10,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": project_metric,
                "value": "0.99",
                "datatype": "xsd:decimal",
            }
        ],
        map_label="Orders profile route privacy",
        is_table=True,
    )

    draft = db.draft_profile_map_updates(route_dataset, route_evidence)
    draft_payload = json.dumps(
        to_jsonable(draft.suggested_next_actions),
        sort_keys=True,
    )
    assert fake_secret in draft_payload

    brief = db.project_brief(limit=10, profile_candidate_limit=5)
    brief_payload = json.dumps(to_jsonable(brief), sort_keys=True)
    assert fake_secret not in brief_payload
    assert redacted in brief_payload


def test_record_profiled_parquet_table_records_map_and_profile_context(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/profiled-parquet#"
    table = f"{base}orders"

    result = db.record_profiled_parquet_table(
        table,
        label="Orders",
        description="Orders table from reviewed Parquet metadata.",
        dataset_summary="Orders Parquet profile captured reviewed aggregate counts.",
        evidence_summary="Reviewed no-I/O Parquet profile manifest.",
        evidence_sources=["scratch://orders-profile.json"],
        columns=[
            {
                "column_name": "order_id",
                "physical_type": "rc:Varchar",
                "nullable": False,
                "null_count": 0,
                "distinct_count": 12,
            },
            {
                "column_name": "status",
                "physical_type": "rc:Varchar",
                "null_count": 0,
                "distinct_count": 3,
                "value_frequencies": [
                    {"value": "paid", "frequency": 7},
                    {"value": "pending", "frequency": 5},
                ],
            },
        ],
        path_templates=["orders/current.parquet"],
        row_count=12,
        row_semantics="rc:EventRow",
        schema_stability="rc:FixedSchema",
        layout_verification_status="rc:VerifiedByQueryLayout",
        storage_access_iri=f"{base}orders_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        location_kind="object",
        storage_root=str(tmp_path / "orders.parquet"),
        storage_path_templates=["orders/current.parquet"],
        physical_layout_iri=f"{base}orders_layout",
        compression_codec="rc:ZstdCompression",
        physical_layout_verification_status="rc:VerifiedByQueryLayout",
        pattern_summary="Orders profile is reviewed aggregate evidence.",
        pattern_text=(
            "Orders map facts and profile observations come from the same "
            "reviewed Parquet profile manifest."
        ),
        pattern_rationale=(
            "Agents can inspect one shared profile run before promoting or "
            "questioning profile-derived findings."
        ),
    )

    assert result.dataset_iri == table
    assert result.shared_evidence_iri == f"{table}/profile-evidence/parquet"
    assert result.table_bundle.dataset.resource_type == RC + "Table"
    assert result.table_bundle.physical_layout is not None
    assert result.profile_observation_count == 3
    assert result.profile_bundle.handoff_entrypoints.profile_run_available is True
    assert result.profile_draft_recommendation_count == db.draft_profile_map_updates(
        table,
        result.shared_evidence_iri,
    ).recommendation_count
    assert result.query_readiness == db.describe_query_context(table).readiness
    assert "describe_query_context" in [
        action.tool_name for action in result.suggested_next_actions
    ]
    assert "describe_profile_run" in [
        action.tool_name for action in result.suggested_next_actions
    ]

    description = db.describe_dataset(table)
    assert description.row_count_snapshot == 12
    assert [column.column_name for column in description.columns] == [
        "order_id",
        "status",
    ]
    assert description.physical_layouts[0].file_format is not None
    assert description.physical_layouts[0].file_format.iri == RC + "Parquet"

    profile_run = db.describe_profile_run(
        table,
        result.shared_evidence_iri,
        limit=None,
    )
    assert profile_run.total_profile_count == 3
    assert {
        profile.observed_column_name
        for profile in profile_run.mapped_column_profile_observations
    } == {
        "order_id",
        "status",
    }
    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_record_profiled_parquet_table_preflights_without_mutation(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match="unsupported field"):
        db.record_profiled_parquet_table(
            "https://example.test/profiled-parquet#orders",
            dataset_summary="Orders Parquet profile.",
            evidence_summary="Reviewed no-I/O profile manifest.",
            columns=[
                {
                    "column_name": "order_id",
                    "unexpected": "not supported",
                }
            ],
            row_count=12,
        )

    assert _mutable_graph_counts(db) == before_counts


def test_record_profile_to_capsule_manifest_records_reviewed_tables_and_views(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/profile-manifest#"
    caveat = f"{base}reviewed_aggregate_caveat"
    orders = f"{base}orders"
    tickets = f"{base}tickets"
    paid_orders_view = f"{base}paid_orders_view"
    open_tickets_view = f"{base}open_tickets_view"

    result = db.record_profile_to_capsule_manifest(
        {
            "format": "doxabase.profile_to_capsule_manifest.v1",
            "table_defaults": {
                "observed_by": "urn:agent:profile-manifest-test",
                "sample_method": "Reviewed no-I/O aggregate manifest.",
                "row_semantics": "rc:EventRow",
                "schema_stability": "rc:FixedSchema",
                "layout_verification_status": "rc:VerifiedByQueryLayout",
                "storage_protocol": "rc:LocalFilesystemStorage",
                "access_mode": "rc:ReadOnlyAccess",
                "location_kind": "directory",
                "storage_root": str(tmp_path),
                "storage_layout_verification_status": "rc:VerifiedByListingLayout",
                "physical_layout_verification_status": "rc:VerifiedByQueryLayout",
                "caveats": [caveat],
            },
            "caveats": [
                {
                    "iri": caveat,
                    "label": "Reviewed aggregate caveat",
                    "description": (
                        "Manifest facts are reviewed aggregate metadata; "
                        "DoxaBase did no file I/O."
                    ),
                    "severity": "rc:Minor",
                    "targets": [orders, tickets],
                }
            ],
            "tables": [
                {
                    "table_iri": orders,
                    "label": "Orders",
                    "dataset_summary": "Orders profile captured reviewed counts.",
                    "evidence_summary": "Reviewed Orders profile manifest.",
                    "evidence_sources": ["scratch://profiles/orders.json"],
                    "path_templates": ["orders/current.parquet"],
                    "storage_path_templates": ["orders/current.parquet"],
                    "row_count": 6,
                    "columns": [
                        {
                            "column_name": "order_id",
                            "physical_type": "rc:Integer",
                            "null_count": 0,
                        },
                        {
                            "column_name": "status",
                            "physical_type": "rc:Varchar",
                            "null_count": 0,
                            "distinct_count": 3,
                        },
                    ],
                },
                {
                    "dataset_iri": tickets,
                    "label": "Tickets",
                    "dataset_summary": "Tickets profile captured reviewed counts.",
                    "evidence_summary": "Reviewed Tickets profile manifest.",
                    "evidence_sources": ["scratch://profiles/tickets.json"],
                    "path_templates": ["tickets/current.parquet"],
                    "storage_path_templates": ["tickets/current.parquet"],
                    "sample_method": "Reviewed ticket profiler output.",
                    "row_count": 4,
                    "columns": [
                        {
                            "column_name": "ticket_id",
                            "physical_type": "rc:Integer",
                            "null_count": 0,
                        }
                    ],
                },
            ],
            "analysis_views": [
                {
                    "view_iri": paid_orders_view,
                    "label": "Paid orders logical view",
                    "source_datasets": [orders],
                    "row_count_snapshot": 3,
                    "caveats": [caveat],
                    "denominator_label": "Paid orders denominator",
                    "denominator_description": "Rows from Orders where status is paid.",
                    "denominator_row_count_snapshot": 3,
                    "denominator_basis": "Reviewed manifest count.",
                    "query_snippets": [
                        {
                            "label": "View definition",
                            "query_text": "select * from orders where status = 'paid'",
                            "query_language": "DuckDB SQL",
                            "query_engine": "duckdb",
                        }
                    ],
                },
                {
                    "iri": open_tickets_view,
                    "label": "Open tickets logical view",
                    "source_datasets": [tickets],
                    "row_count_snapshot": 2,
                    "denominator_label": "Open tickets denominator",
                    "denominator_description": (
                        "Rows from Tickets where status is open."
                    ),
                    "denominator_row_count_snapshot": 2,
                    "denominator_basis": "Reviewed manifest count.",
                },
            ],
        }
    )

    assert result.manifest_format == "doxabase.profile_to_capsule_manifest.v1"
    assert result.caveat_iris == [caveat]
    assert result.table_iris == [orders, tickets]
    assert result.analysis_view_iris == [paid_orders_view, open_tickets_view]
    assert result.caveat_count == 1
    assert result.table_count == 2
    assert result.analysis_view_count == 2
    assert result.domain_network_profile_count == 0
    assert result.domain_network_profile_observation_count == 0
    assert result.domain_network_profile_records == []
    assert result.domain_network_profile_evidence_iris == []
    assert result.domain_network_pattern_iris == []
    assert result.profile_observation_count == 5
    assert result.query_readiness_counts == {"ready_for_query_planning": 2}
    assert result.analysis_view_bundle is not None
    assert result.analysis_view_bundle.query_snippet_count == 1
    assert {action.tool_name for action in result.suggested_next_actions} >= {
        "describe_dataset",
        "describe_profile_run",
        "describe_query_context",
    }

    orders_run = db.describe_profile_run(orders, result.shared_evidence_iris[0])
    assert orders_run.total_profile_count == 3
    assert db.describe_query_context(paid_orders_view).readiness == (
        "logical_analysis_view"
    )
    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_record_profile_to_capsule_manifest_replays_stable_pattern_iris(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/profile-manifest-replay#"
    messages = f"{base}messages"
    message_id_pattern = f"{base}pattern_message_id_identifier"
    manifest = {
        "format": "doxabase.profile_to_capsule_manifest.v1",
        "table_defaults": {
            "sample_method": "Reviewed no-I/O aggregate manifest.",
            "storage_protocol": "rc:LocalFilesystemStorage",
            "access_mode": "rc:ReadOnlyAccess",
            "location_kind": "directory",
            "storage_root": str(tmp_path),
            "layout_verification_status": "rc:VerifiedByListingLayout",
            "storage_layout_verification_status": "rc:VerifiedByListingLayout",
            "physical_layout_verification_status": "rc:VerifiedByListingLayout",
        },
        "tables": [
            {
                "iri": messages,
                "label": "Messages",
                "dataset_summary": "Messages profile captured reviewed counts.",
                "evidence_summary": "Reviewed Messages profile manifest.",
                "evidence_sources": ["scratch://profiles/messages.json"],
                "path_templates": ["messages/current.parquet"],
                "row_count": 12,
                "columns": [
                    {
                        "column_name": "message_id",
                        "physical_type": "rc:Varchar",
                        "null_count": 0,
                        "distinct_count": 12,
                        "pattern_iri": message_id_pattern,
                        "pattern_summary": "message_id behaves like an identifier.",
                        "pattern_text": (
                            "The reviewed profile sidecar reported no nulls "
                            "and full distinctness for message_id."
                        ),
                        "pattern_rationale": (
                            "Identifier-like columns should stay connected "
                            "to their supporting aggregate profile facts."
                        ),
                    }
                ],
            }
        ],
    }

    first = db.record_profile_to_capsule_manifest(manifest)
    second = db.record_profile_to_capsule_manifest(manifest)

    assert first.table_iris == [messages]
    assert second.table_iris == [messages]
    next_action_keys = [
        (action.tool_name, json.dumps(action.arguments, sort_keys=True))
        for action in second.suggested_next_actions
    ]
    assert len(next_action_keys) == len(set(next_action_keys))
    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text
    patterns = db.to_graph(["patterns"])
    assert (
        len(
            list(
                patterns.objects(
                    URIRef(message_id_pattern),
                    URIRef(RC + "synthesizedAt"),
                )
            )
        )
        == 1
    )
    pattern = db.describe_pattern(message_id_pattern)
    assert pattern.summary == "message_id behaves like an identifier."
    assert [target.iri for target in pattern.pattern_targets] == [
        f"{messages}__message_id"
    ]
    assert len(pattern.supporting_observations) == 1


def test_record_profile_to_capsule_manifest_records_domain_network_profiles(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/profile-manifest-domain#"
    messages = f"{base}messages"
    evidence = f"{base}domain_network_profile_evidence"
    view = f"{base}message_like_domain_network_view"
    caveat = f"{base}domain_network_extractability_caveat"

    result = db.record_profile_to_capsule_manifest(
        {
            "format": "doxabase.profile_to_capsule_manifest.v1",
            "table_defaults": {
                "sample_method": "Reviewed aggregate manifest.",
                "storage_protocol": "rc:LocalFilesystemStorage",
                "access_mode": "rc:ReadOnlyAccess",
                "location_kind": "directory",
                "storage_root": str(tmp_path),
                "layout_verification_status": "rc:VerifiedByQueryLayout",
                "storage_layout_verification_status": "rc:VerifiedByListingLayout",
                "physical_layout_verification_status": "rc:VerifiedByQueryLayout",
            },
            "tables": [
                {
                    "iri": messages,
                    "label": "Messages",
                    "dataset_summary": "Messages profile captured reviewed counts.",
                    "evidence_summary": "Reviewed Messages profile manifest.",
                    "evidence_sources": ["scratch://profiles/messages.json"],
                    "path_templates": ["messages/current.parquet"],
                    "row_count": 100,
                    "row_semantics": "rc:EventRow",
                    "columns": [
                        {
                            "column_name": "sender_domain",
                            "physical_type": "rc:Varchar",
                            "null_count": 15,
                        },
                        {
                            "column_name": "recipient_domain",
                            "physical_type": "rc:Varchar",
                            "null_count": 20,
                        },
                    ],
                }
            ],
            "domain_network_profiles": [
                {
                    "dataset_iri": messages,
                    "summary": "Domain extraction coverage for message-like rows.",
                    "evidence_summary": (
                        "Reviewed aggregate domain profile from a query result."
                    ),
                    "evidence_sources": ["scratch://profiles/domain-network.json"],
                    "evidence_iri": evidence,
                    "sample_size": 100,
                    "sample_scope": "All message-like rows in the reviewed snapshot.",
                    "sample_method": (
                        "DuckDB aggregate over canonicalized domain fields."
                    ),
                    "extraction_method": (
                        "Regex email extraction followed by lowercase domain parse."
                    ),
                    "coverage_counts": [
                        {"bucket": "sender_and_recipient_extracted", "count": 70},
                        {"bucket": "sender_only_extracted", "count": 10},
                        {"bucket": "recipient_only_extracted", "count": 5},
                        {"bucket": "neither_extracted", "count": 15},
                    ],
                    "coverage_counts_exhaustive": True,
                    "domain_pair_counts": [
                        {
                            "sender_domain": "example.test",
                            "recipient_domain": "vendor.test",
                            "count": 25,
                        },
                        {
                            "sender_domain": "vendor.test",
                            "recipient_domain": "example.test",
                            "count": 12,
                        },
                    ],
                    "sender_domain_counts": [
                        {"domain": "example.test", "count": 62},
                        {"domain": "vendor.test", "count": 18},
                    ],
                    "recipient_domain_counts": [
                        {"domain": "example.test", "count": 41},
                        {"domain": "vendor.test", "count": 37},
                    ],
                    "analysis_view_iri": view,
                    "analysis_view_label": "Message-like domain-network rows",
                    "analysis_view_row_count_snapshot": 100,
                    "analysis_view_query_text": (
                        "select * from messages where folder_family not in "
                        "('calendar', 'contacts')"
                    ),
                    "analysis_view_query_language": "DuckDB SQL",
                    "analysis_view_query_engine": "duckdb",
                    "caveat_iri": caveat,
                    "caveat_description": (
                        "Domain-network metrics are bounded by sender and "
                        "recipient extractability."
                    ),
                    "pattern_summary": (
                        "Network coverage must be reported with domain graphs."
                    ),
                    "pattern_text": (
                        "The reviewed aggregate profile records extraction "
                        "coverage before domain-pair counts."
                    ),
                    "pattern_rationale": (
                        "Missing sender or recipient domains are parser coverage "
                        "gaps, not proof of absent communication."
                    ),
                }
            ],
        }
    )

    assert result.table_iris == [messages]
    assert result.analysis_view_iris == [view]
    assert result.caveat_iris == [caveat]
    assert [record.iri for record in result.caveat_records] == [caveat]
    assert result.domain_network_profile_count == 1
    assert result.domain_network_profile_observation_count == 4
    assert result.domain_network_profile_evidence_iris == [evidence]
    assert len(result.domain_network_pattern_iris) == 1
    assert result.profile_observation_count == 7
    assert result.analysis_view_count == 1
    assert result.caveat_count == 1
    assert result.domain_network_profile_records[0].profile_observation_iris
    assert {action.tool_name for action in result.suggested_next_actions} >= {
        "describe_profile_run",
        "describe_analysis_view",
        "describe_pattern",
    }

    profile_run = db.describe_profile_run(messages, evidence, limit=None)
    assert profile_run.total_profile_count == 4
    assert db.describe_query_context(view).readiness == "logical_analysis_view"
    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_record_profile_to_capsule_manifest_preflights_all_tables_before_mutation(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_counts = _mutable_graph_counts(db)
    base = "https://example.test/profile-manifest-preflight#"

    with pytest.raises(DoxaBaseError, match="columns\\[1\\] has unsupported field"):
        db.record_profile_to_capsule_manifest(
            {
                "format": "doxabase.profile_to_capsule_manifest.v1",
                "table_defaults": {
                    "storage_protocol": "rc:LocalFilesystemStorage",
                    "access_mode": "rc:ReadOnlyAccess",
                    "location_kind": "directory",
                    "storage_root": str(tmp_path),
                },
                "tables": [
                    {
                        "iri": f"{base}orders",
                        "dataset_summary": "Orders profile captured reviewed counts.",
                        "evidence_summary": "Reviewed Orders profile manifest.",
                        "evidence_sources": ["scratch://profiles/orders.json"],
                        "row_count": 6,
                        "columns": [{"column_name": "order_id"}],
                    },
                    {
                        "iri": f"{base}tickets",
                        "dataset_summary": "Tickets profile captured reviewed counts.",
                        "evidence_summary": "Reviewed Tickets profile manifest.",
                        "evidence_sources": ["scratch://profiles/tickets.json"],
                        "row_count": 4,
                        "columns": [
                            {
                                "column_name": "ticket_id",
                                "unexpected": "caught by cloned preflight",
                            }
                        ],
                    },
                ],
            }
        )

    assert _mutable_graph_counts(db) == before_counts


def test_record_profile_to_capsule_manifest_preflights_domain_profiles(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_counts = _mutable_graph_counts(db)
    base = "https://example.test/profile-manifest-domain-preflight#"

    with pytest.raises(DoxaBaseError, match="individual address"):
        db.record_profile_to_capsule_manifest(
            {
                "format": "doxabase.profile_to_capsule_manifest.v1",
                "tables": [
                    {
                        "iri": f"{base}messages",
                        "dataset_summary": (
                            "Messages profile captured reviewed counts."
                        ),
                        "evidence_summary": "Reviewed Messages profile manifest.",
                        "evidence_sources": ["scratch://profiles/messages.json"],
                        "row_count": 10,
                        "columns": [{"column_name": "sender_domain"}],
                    }
                ],
                "domain_network_profiles": [
                    {
                        "dataset_iri": f"{base}messages",
                        "summary": "Unsafe domain profile.",
                        "evidence_summary": (
                            "Unsafe aggregate should fail before writes."
                        ),
                        "sample_size": 10,
                        "sample_scope": "All message-like rows.",
                        "sample_method": "Aggregate query.",
                        "extraction_method": "Regex extraction.",
                        "coverage_counts": [
                            {"bucket": "alice@example.test", "count": 10},
                        ],
                    }
                ],
            }
        )

    assert _mutable_graph_counts(db) == before_counts


def test_record_domain_network_profile_records_reviewed_aggregates(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/domain-network#"
    dataset = f"{base}messages"
    evidence = f"{base}domain_network_profile_evidence"
    analysis_view = f"{base}message_like_domain_network_view"
    caveat = f"{base}domain_network_extractability_caveat"

    db.record_map_table_bundle(
        dataset,
        label="Messages",
        columns=[
            {"column_name": "sender_domain", "physical_type": "rc:Varchar"},
            {"column_name": "recipient_domain", "physical_type": "rc:Varchar"},
        ],
        row_count_snapshot=100,
        row_semantics="rc:EventRow",
    )

    result = db.record_domain_network_profile(
        dataset,
        summary="Domain extraction coverage for message-like rows.",
        evidence_summary="Reviewed aggregate domain profile from a query result.",
        evidence_sources=["scratch://domain-network-profile.json"],
        evidence_iri=evidence,
        sample_size=100,
        sample_scope="All message-like rows in the reviewed snapshot.",
        sample_method="DuckDB aggregate over canonicalized domain fields.",
        extraction_method="Regex email extraction followed by lowercase domain parse.",
        coverage_counts=[
            {"bucket": "sender_and_recipient_extracted", "count": 70},
            {"bucket": "sender_only_extracted", "count": 10},
            {"bucket": "recipient_only_extracted", "count": 5},
            {"bucket": "neither_extracted", "count": 15},
        ],
        coverage_counts_exhaustive=True,
        domain_pair_counts=[
            {
                "sender_domain": "example.test",
                "recipient_domain": "vendor.test",
                "count": 25,
            },
            {
                "sender_domain": "vendor.test",
                "recipient_domain": "example.test",
                "count": 12,
            },
        ],
        sender_domain_counts=[
            {"domain": "example.test", "count": 62},
            {"domain": "vendor.test", "count": 18},
        ],
        recipient_domain_counts=[
            {"domain": "example.test", "count": 41},
            {"domain": "vendor.test", "count": 37},
        ],
        analysis_view_iri=analysis_view,
        analysis_view_label="Message-like domain-network rows",
        analysis_view_row_count_snapshot=100,
        analysis_view_query_text=(
            "select * from messages where folder_family not in "
            "('calendar', 'contacts')"
        ),
        analysis_view_query_language="DuckDB SQL",
        analysis_view_query_engine="duckdb",
        caveat_iri=caveat,
        caveat_description=(
            "Domain-network metrics are bounded by sender and recipient "
            "extractability."
        ),
        pattern_summary="Network coverage must be reported with domain graphs.",
        pattern_text=(
            "The reviewed aggregate profile records extraction coverage before "
            "domain-pair counts, so network interpretation should cite both."
        ),
        pattern_rationale=(
            "Missing sender or recipient domains are parser coverage gaps, not "
            "proof of absent communication."
        ),
    )

    assert result.evidence_iri == evidence
    assert result.analysis_view is not None
    assert result.analysis_view.iri == analysis_view
    assert result.caveat is not None
    assert result.caveat.iri == caveat
    assert result.pattern is not None
    assert len(result.profile_observation_iris) == 4
    assert [action.tool_name for action in result.suggested_next_actions] == [
        "describe_dataset",
        "describe_profile_run",
        "describe_analysis_view",
        "describe_pattern",
    ]

    profile_run = db.describe_profile_run(dataset, evidence, limit=None)
    assert profile_run.total_profile_count == 4
    assert set(profile_run.profile_observation_iris) == set(
        result.profile_observation_iris
    )
    coverage = next(
        observation
        for observation in profile_run.dataset_profile_observations
        if observation.summary == "Domain extraction coverage for message-like rows."
    )
    assert [(item.value, item.frequency) for item in coverage.value_frequencies] == [
        ("sender_and_recipient_extracted", 70),
        ("neither_extracted", 15),
        ("sender_only_extracted", 10),
        ("recipient_only_extracted", 5),
    ]
    pair_profile = next(
        observation
        for observation in profile_run.dataset_profile_observations
        if observation.summary == "Domain pair aggregate counts for network profiling."
    )
    assert pair_profile.value_frequencies[0].value == (
        "example.test -> vendor.test"
    )
    assert db.describe_query_context(analysis_view).readiness == "logical_analysis_view"
    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_record_domain_network_profile_preflights_private_values(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/domain-network#messages"
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match="individual address"):
        db.record_domain_network_profile(
            dataset,
            summary="Unsafe domain profile.",
            evidence_summary="Unsafe aggregate should fail before writes.",
            sample_size=10,
            sample_scope="All rows.",
            sample_method="Aggregate query.",
            extraction_method="Regex extraction.",
            coverage_counts=[
                {"bucket": "alice@example.test", "count": 10},
            ],
        )

    assert _mutable_graph_counts(db) == before_counts

    with pytest.raises(DoxaBaseError, match="below domain_pair_min_count"):
        db.record_domain_network_profile(
            dataset,
            summary="Low-frequency domain profile.",
            evidence_summary="Low-frequency aggregate should fail before writes.",
            sample_size=10,
            sample_scope="All rows.",
            sample_method="Aggregate query.",
            extraction_method="Regex extraction.",
            coverage_counts=[{"bucket": "sender_and_recipient_extracted", "count": 10}],
            domain_pair_counts=[
                {
                    "sender_domain": "example.test",
                    "recipient_domain": "vendor.test",
                    "count": 1,
                }
            ],
        )

    assert _mutable_graph_counts(db) == before_counts

    with pytest.raises(
        DoxaBaseError,
        match="pattern_summary, pattern_text, and pattern_rationale",
    ):
        db.record_domain_network_profile(
            dataset,
            summary="Partial-pattern domain profile.",
            evidence_summary="Partial pattern should fail before writes.",
            sample_size=10,
            sample_scope="All rows.",
            sample_method="Aggregate query.",
            extraction_method="Regex extraction.",
            coverage_counts=[{"bucket": "sender_and_recipient_extracted", "count": 10}],
            caveat_description="Domain graphs depend on extraction coverage.",
            pattern_summary="Missing supporting fields.",
        )

    assert _mutable_graph_counts(db) == before_counts


def test_get_context_graph_warns_when_seed_profile_mismatches(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Messages"
    db.record_map_dataset(dataset, label="Messages", is_table=True)
    pattern = db.record_pattern(
        summary="Messages have stable document identifiers.",
        pattern_text="Use document identifiers when joining message exports.",
        rationale="Exercise profile mismatch guidance for pattern seeds.",
        pattern_targets=[dataset],
        source_path="tests/test_doxabase_core.py",
        source_kind="rc:DocumentationSource",
    )

    dataset_slice = db.get_context_graph(
        pattern.pattern_iri,
        profile="dataset_brief",
    )

    assert dataset_slice.pattern_contexts == []
    assert any(
        "Seed is an rc:Pattern; rerun with profile='pattern_brief' or 'deep_lore'."
        in warning
        for warning in dataset_slice.warnings
    )

    pattern_slice = db.get_context_graph(
        pattern.pattern_iri,
        profile="pattern_brief",
    )
    assert [context.iri for context in pattern_slice.pattern_contexts] == [
        pattern.pattern_iri
    ]
    assert pattern_slice.warnings == []


def test_get_context_graph_invalid_profile_points_to_route_fields(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Messages"
    db.record_map_dataset(dataset, label="Messages", is_table=True)

    with pytest.raises(DoxaBaseError) as exc:
        db.get_context_graph(dataset, profile="route_explained")  # type: ignore[arg-type]

    error_message = str(exc.value)
    assert (
        "profile must be 'dataset_brief', 'pattern_brief', or 'deep_lore', "
        "or 'resource_brief'"
    ) in error_message
    assert "routes and route_legend" in error_message
    assert "'route_explained' profile" in error_message


def test_get_context_graph_includes_profile_observations_and_metrics(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    column = "https://example.test/project#orders__amount"
    metric_kind = "https://example.test/project#CompletenessRatio"
    db.record_map_dataset(dataset, label="Orders", is_table=True, columns=[column])
    db.record_map_column(
        column,
        table_iri=dataset,
        column_name="amount",
        physical_type="rc:Decimal",
    )
    dataset_profile = db.record_dataset_profile(
        dataset,
        summary="Orders were profiled for completeness.",
        evidence_summary="Dataset profile run.",
        evidence_sources=["test://orders-profile"],
        row_count=100,
        value_frequencies=[{"value": "present", "frequency": 98}],
        profile_metrics=[
            {"metric": metric_kind, "value": 0.98, "target": dataset},
        ],
        update_map_snapshot=False,
    )
    column_profile = db.record_column_profile(
        column,
        table_iri=dataset,
        column_name="amount",
        summary="Amount was profiled for mean value.",
        evidence_summary="Column profile run.",
        evidence_sources=["test://amount-profile"],
        profile_metrics=[{"metric": "rc:MeanValue", "value": 42.5}],
        update_map_column=False,
    )
    dataset_metric_iri = db._objects(
        ["observations"],
        dataset_profile.observation.observation_iri,
        "rc:observedProfileMetric",
    )[0]
    value_frequency_iri = db._objects(
        ["observations"],
        dataset_profile.observation.observation_iri,
        "rc:observedValueFrequency",
    )[0]

    context_slice = db.get_context_graph(
        dataset,
        profile="dataset_brief",
        max_triples=300,
    )

    resources = {resource.iri: resource for resource in context_slice.resources}
    assert dataset_profile.observation.observation_iri in resources
    assert column_profile.observation.observation_iri in resources
    assert dataset_metric_iri in resources
    assert value_frequency_iri in resources
    assert metric_kind in resources
    assert resources[metric_kind].referenced_only is True
    assert resources[metric_kind].surface_role == "referenced_only"
    assert dataset_profile.observation.evidence_iri in resources
    assert context_slice.route_counts["dataset_profile_observation"] == 1
    assert context_slice.route_counts["column_profile_observation"] == 1
    assert context_slice.route_counts["observed_profile_metric"] >= 2
    assert context_slice.route_counts["observed_value_frequency"] == 1
    assert context_slice.route_counts["profile_metric_kind"] >= 2


def test_context_slice_structures_seed_profile_outside_bounded_dataset_profiles(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    old_profile = db.record_dataset_profile(
        dataset,
        summary="Old one-off profile run.",
        observed_at="2026-01-01T00:00:00Z",
        evidence_summary="Old profile evidence.",
        evidence_sources=["test://orders-old-profile"],
        evidence_iri="https://example.test/project#OldProfileEvidence",
        row_count=10,
        update_map_snapshot=False,
    )
    for index in range(6):
        db.record_dataset_profile(
            dataset,
            summary=f"Newer profile run {index}.",
            observed_at=f"2026-02-{index + 1:02d}T00:00:00Z",
            evidence_summary=f"Newer profile evidence {index}.",
            evidence_sources=[f"test://orders-new-profile-{index}"],
            row_count=100 + index,
            update_map_snapshot=False,
        )

    context_slice = db.get_context_graph(
        old_profile.observation.observation_iri,
        profile="dataset_brief",
        max_triples=300,
    )

    dataset_context = context_slice.dataset_contexts[0]
    returned_profile_iris = {
        profile.iri for profile in dataset_context.profile_observations
    }
    assert old_profile.observation.observation_iri not in returned_profile_iris
    assert dataset_context.profile_summary.omitted_dataset_profile_count == 2
    assert old_profile.observation.evidence_iri not in (
        dataset_context.profile_summary.evidence_iris
    )

    assert [
        profile.iri for profile in context_slice.seed_profile_observations
    ] == [old_profile.observation.observation_iri]
    assert [
        evidence.iri
        for evidence in context_slice.seed_profile_observations[0].evidence
    ] == [old_profile.observation.evidence_iri]
    assert any("warnings" in step for step in context_slice.reading_order)
    assert any(
        "seed_profile_observations" in step
        for step in context_slice.reading_order
    )
    assert context_slice.route_counts["seed_profile_observation"] == 1
    resources = {resource.iri: resource for resource in context_slice.resources}
    assert old_profile.observation.observation_iri in resources
    assert old_profile.observation.evidence_iri in resources


def test_get_context_graph_expands_profile_metric_kind_seed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    metric_kind = "https://example.test/project#CompletenessRatio"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    profile = db.record_dataset_profile(
        dataset,
        summary="Orders were profiled for completeness.",
        evidence_summary="Dataset profile run.",
        evidence_sources=["test://orders-profile"],
        profile_metrics=[
            {"metric": metric_kind, "value": 0.98, "target": dataset},
        ],
        update_map_snapshot=False,
    )
    metric_iri = db._objects(
        ["observations"],
        profile.observation.observation_iri,
        "rc:observedProfileMetric",
    )[0]

    context_slice = db.get_context_graph(
        metric_kind,
        profile="dataset_brief",
        max_triples=200,
    )

    resources = {resource.iri: resource for resource in context_slice.resources}
    assert metric_kind in resources
    assert resources[metric_kind].referenced_only is True
    assert metric_iri in resources
    assert profile.observation.observation_iri in resources
    assert dataset in resources
    assert context_slice.dataset_contexts[0].iri == dataset
    assert context_slice.route_counts["seed_profile_metric_kind"] == 1
    assert context_slice.route_counts["observed_profile_metric"] >= 1
    assert context_slice.route_counts["profile_metric_observation"] == 1
    assert "profile-specific expansion did not apply" not in " ".join(
        context_slice.warnings
    )

    metric_context = db.get_context_graph(
        metric_iri,
        profile="dataset_brief",
        max_triples=200,
    )
    metric_resources = {resource.iri: resource for resource in metric_context.resources}
    assert metric_iri in metric_resources
    assert profile.observation.observation_iri in metric_resources
    assert dataset in metric_resources
    assert metric_context.route_counts["observed_profile_metric"] >= 1
    assert metric_context.route_counts["profile_metric_observation"] == 1

    observation_context = db.get_context_graph(
        profile.observation.observation_iri,
        profile="dataset_brief",
        max_triples=200,
    )
    observation_resources = {
        resource.iri: resource for resource in observation_context.resources
    }
    assert profile.observation.observation_iri in observation_resources
    assert metric_iri in observation_resources
    assert dataset in observation_resources
    assert observation_context.route_counts["seed_profile_observation"] == 1
    assert observation_context.route_counts["observed_profile_metric"] >= 1


def test_get_context_graph_caps_broad_profile_metric_kind_seed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    metric_kind = "rc:MeanValue"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    for index in range(27):
        db.record_dataset_profile(
            dataset,
            summary=f"Orders profile run {index}.",
            observed_at=f"2026-01-{index + 1:02d}T00:00:00+00:00",
            evidence_summary=f"Dataset profile run {index}.",
            evidence_sources=[f"test://orders-profile/{index}"],
            profile_metrics=[
                {"metric": metric_kind, "value": index, "target": dataset},
            ],
            update_map_snapshot=False,
        )

    context_slice = db.get_context_graph(
        metric_kind,
        profile="dataset_brief",
        max_triples=1000,
    )

    assert context_slice.route_counts["seed_profile_metric_kind"] == 1
    assert context_slice.route_counts["profile_metric_observation"] == 25
    assert any(
        "matched 27 observed profile metric(s); included 25 and omitted 2"
        in warning
        for warning in context_slice.warnings
    )


def test_search_finds_uri_object_terms_for_profile_metric_kinds(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    metric_kind = "https://example.test/project#CompletenessRatio"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_dataset_profile(
        dataset,
        summary="Orders completeness profile",
        profile_metrics=[
            {"metric": metric_kind, "value": 0.98, "target": dataset},
        ],
        update_map_snapshot=False,
    )

    results = db.search("CompletenessRatio", graph="observations")
    match = next(
        result
        for result in results.matches
        if result.predicate == RC + "profileMetricKind"
    )
    assert match.text == metric_kind
    assert match.types == [RC + "ObservedProfileMetric"]

    entities = db.list_entities(
        type="rc:ObservedProfileMetric",
        graph="observations",
        text="CompletenessRatio",
    ).entities
    assert [entity.iri for entity in entities] == [match.iri]

    described = db.describe_dataset(dataset)
    described_metric_iris = {
        metric.iri
        for profile in described.profile_observations
        for metric in profile.profile_metrics
    }
    assert match.iri in described_metric_iris


def test_record_query_result_aggregate_payloads_stay_observations_without_profile_fields(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(dataset, label="Orders", is_table=True)

    aggregate = db.record_query_result(
        summary="Orders status aggregate wrote grouped counts to JSON.",
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path="queries/orders_status_counts.sql",
        result_sources=["/tmp/orders-status-counts.json"],
        sample_scope=(
            "All source rows were scanned; grouped counts are in the result "
            "artifact."
        ),
        sample_method="External read-only grouped aggregate query.",
    )

    assert aggregate.observation_type == "observation"
    assert [action.tool_name for action in aggregate.suggested_next_actions] == [
        "get_context_graph",
        "describe_query_context"
    ]
    assert aggregate.suggested_next_actions[0].arguments == {
        "seed_iris": [aggregate.evidence_iri],
        "profile": "resource_brief",
    }
    assert aggregate.suggested_next_actions[1].arguments == {"iri": dataset}

    sampled_aggregate = db.record_query_result(
        summary="Orders status aggregate also recorded source rows scanned.",
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path="queries/orders_status_counts.sql",
        result_sources=["/tmp/orders-status-counts-with-source-count.json"],
        sample_size=6,
        sample_scope=(
            "All source rows were scanned, but the result artifact is a grouped "
            "aggregate."
        ),
        sample_method="External read-only grouped aggregate query.",
    )

    assert sampled_aggregate.observation_type == "profile"
    assert [
        action.tool_name for action in sampled_aggregate.suggested_next_actions
    ] == [
        "describe_profile_run",
        "get_context_graph",
        "describe_query_context",
    ]
    assert db.validate_graph(scope="all").conforms


def test_record_observation_rejects_unknown_rc_profile_metric_kind(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match="unknown rc: profile metric kind"):
        db.record_observation(
            summary="Profile used a mistyped rc metric kind.",
            observation_type="profile",
            observed_asset="https://example.test/project#Orders",
            profile_metrics=[{"metric": "rc:MinValue", "value": 1}],
        )


def test_record_observation_accepts_project_profile_metric_kind_iri(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    metric_kind = "https://example.test/project#CompletenessRatio"

    result = db.record_observation(
        summary="Profile used a project-specific metric kind.",
        observation_type="profile",
        observed_asset="https://example.test/project#Orders",
        profile_metrics=[
            {
                "metric_kind": metric_kind,
                "value": "0.98",
                "datatype": "xsd:decimal",
            }
        ],
    )

    observations = db.to_graph(["observations"])
    metric_iri = next(
        observations.objects(
            URIRef(result.observation_iri),
            URIRef(RC + "observedProfileMetric"),
        )
    )
    assert (
        metric_iri,
        URIRef(RC + "profileMetricKind"),
        URIRef(metric_kind),
    ) in observations


def test_record_dataset_profile_writes_observation_map_snapshot_and_pattern(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Messages"

    result = db.record_dataset_profile(
        dataset,
        summary="Messages were profiled for row and identity coverage.",
        observed_by="urn:doxabase:test-agent",
        evidence_summary="Synthetic profile output from a local DuckDB query.",
        evidence_sources=["test://messages-profile"],
        sample_size=123,
        sample_scope="All rows in the local Messages test table.",
        sample_method="DuckDB aggregate query over the full table.",
        row_count=123,
        distinct_count=120,
        value_frequencies=[
            {"value": "open", "frequency": 80},
            {"value": "closed", "frequency": 43},
        ],
        profile_metrics=[
            {"metric": "rc:MinimumValue", "value": 1, "target": dataset},
            {"metric": "rc:MaximumValue", "value": 123},
        ],
        map_label="Messages",
        is_table=True,
        pattern_summary="Messages profile is internally consistent.",
        pattern_text=(
            "The sampled Messages profile has a stable row count and near-row "
            "distinctness on the inspected identity field."
        ),
        pattern_rationale=(
            "Keeping the profile observation, map snapshot, and pattern linked "
            "makes later review cheaper."
        ),
    )

    assert result.dataset_iri == dataset
    assert result.observation.observation_type == "profile"
    assert result.observation.evidence_iri is not None
    assert result.map_dataset is not None
    assert result.map_dataset.iri == dataset
    assert result.pattern is not None

    description = db.describe_dataset(dataset)
    assert description.label == "Messages"
    assert description.row_count_snapshot == 123
    assert len(description.profile_observations) == 1
    assert description.profile_summary.returned_dataset_profile_count == 1
    assert description.profile_summary.returned_mapped_column_profile_count == 0
    assert description.profile_summary.returned_unmapped_column_profile_count == 0
    assert description.profile_summary.returned_profile_count == 1
    assert description.profile_summary.shared_evidence_iris == [
        result.observation.evidence_iri
    ]
    assert "Profile lore is observed evidence" in (
        description.profile_summary.handoff_note
    )
    assert "physical metadata gaps" in description.profile_summary.handoff_note
    profile = description.profile_observations[0]
    assert profile.iri == result.observation.observation_iri
    assert profile.sample_size == 123
    assert profile.sample_scope == "All rows in the local Messages test table."
    assert profile.sample_method == "DuckDB aggregate query over the full table."
    assert profile.row_count == 123
    assert profile.distinct_count == 120
    assert profile.null_count is None
    assert [(item.value, item.frequency) for item in profile.value_frequencies] == [
        ("open", 80),
        ("closed", 43),
    ]
    assert {
        (
            item.metric.iri,
            item.target.iri if item.target is not None else None,
            item.value,
            item.value_datatype,
        )
        for item in profile.profile_metrics
    } == {
        (RC + "MinimumValue", dataset, "1", str(XSD.integer)),
        (RC + "MaximumValue", None, "123", str(XSD.integer)),
    }
    assert profile.evidence[0].iri == result.observation.evidence_iri
    assert profile.evidence[0].sources == ["test://messages-profile"]

    pattern = db.describe_pattern(result.pattern.pattern_iri)
    assert [target.iri for target in pattern.pattern_targets] == [dataset]
    assert [target.iri for target in pattern.map_implications] == [dataset]
    assert [item.iri for item in pattern.supporting_observations] == [
        result.observation.observation_iri
    ]
    assert [item.iri for item in pattern.evidence] == [
        result.observation.evidence_iri
    ]

    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_record_dataset_profile_keeps_sampled_row_count_out_of_map_snapshot(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersSampleEvidence"
    override_dataset = "https://example.test/project#OrdersOverride"

    result = db.record_dataset_profile(
        dataset,
        summary="Orders were profiled from a sampled partition.",
        evidence_summary="Synthetic sampled profile output.",
        evidence_sources=["test://orders-sampled-profile"],
        evidence_iri=evidence,
        sample_size=25,
        sample_scope="Twenty-five sampled Orders rows.",
        sample_method="DuckDB sampled profile query.",
        row_count=1000,
        map_label="Orders",
        is_table=True,
    )

    assert result.map_dataset is not None
    description = db.describe_dataset(dataset)
    assert description.label == "Orders"
    assert description.row_count_snapshot is None
    assert description.profile_observations[0].row_count == 1000
    assert description.profile_summary.profile_run_candidates == []

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert [
        (
            recommendation.kind,
            recommendation.basis,
            recommendation.default_stageable,
        )
        for recommendation in draft.recommendations
    ] == [("dataset_row_count_snapshot", "sample", False)]

    db.record_dataset_profile(
        override_dataset,
        summary="Orders sampled count was explicitly accepted as durable scope.",
        evidence_summary="Synthetic sampled profile output.",
        evidence_sources=["test://orders-sampled-profile"],
        sample_size=25,
        sample_scope="Twenty-five sampled Orders rows.",
        sample_method="DuckDB sampled profile query.",
        row_count=1000,
        map_label="Orders override",
        is_table=True,
        allow_sampled_row_count_snapshot=True,
    )

    assert db.describe_dataset(override_dataset).row_count_snapshot == 1000


def test_describe_dataset_profile_without_value_frequencies_returns_empty_list(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"

    db.record_dataset_profile(
        dataset,
        summary="Orders were profiled before value-frequency capture existed.",
        evidence_summary="Synthetic profile output.",
        row_count=10,
        map_label="Orders",
        is_table=True,
    )

    description = db.describe_dataset(dataset)

    assert len(description.profile_observations) == 1
    assert description.profile_observations[0].value_frequencies == []


def test_record_dataset_profile_preflights_pattern_validation_without_mutation(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match="pattern_map_implications"):
        db.record_dataset_profile(
            dataset,
            summary="Invalid dataset profile pattern should not write.",
            evidence_summary="Synthetic profile output.",
            evidence_sources=["test://orders-profile"],
            row_count=10,
            update_map_snapshot=False,
            pattern_summary="Orders profile has an invalid implication.",
            pattern_text="This pattern is intentionally invalid.",
            pattern_rationale="The test uses a prose map implication.",
            pattern_map_implications=["plain implication"],
        )

    assert _mutable_graph_counts(db) == before_counts
    assert db.search("Invalid dataset profile pattern", graph="observations").matches == []
    assert db.search("Synthetic profile output", graph="evidence").matches == []


def test_record_column_profile_writes_observation_map_column_and_pattern(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Messages"
    column = "https://example.test/project#MessagesDocId"
    db.record_map_dataset(table, label="Messages", is_table=True)

    result = db.record_column_profile(
        column,
        column_name="doc_id",
        table_iri=table,
        summary="Messages doc_id was profiled for null and distinct counts.",
        evidence_summary="Synthetic column profile output.",
        evidence_sources=["test://messages-doc-id-profile"],
        sample_size=123,
        sample_scope="All doc_id values in the local Messages test table.",
        sample_method="DuckDB column aggregate query over the full table.",
        row_count=123,
        null_count=0,
        distinct_count=123,
        value_frequencies=[
            {"value": "doc-001", "frequency": 1},
            {"value": "doc-002", "frequency": 1},
        ],
        map_label="Messages.doc_id",
        physical_type="rc:Varchar",
        nullable=False,
        pattern_summary="doc_id behaves like a complete identifier.",
        pattern_text="The profiled doc_id column had no nulls and all values distinct.",
        pattern_rationale=(
            "A complete distinct profile is a useful hunch for later identity "
            "and join modelling."
        ),
    )

    assert result.column_iri == column
    assert result.table_iri == table
    assert result.observation.observation_type == "profile"
    assert result.map_column is not None
    assert result.map_column.iri == column
    assert result.pattern is not None
    pattern = db.describe_pattern(result.pattern.pattern_iri)
    assert [item.iri for item in pattern.evidence] == [
        result.observation.evidence_iri
    ]

    description = db.describe_dataset(table)
    assert [item.iri for item in description.columns] == [column]
    assert description.profile_observations == []
    assert description.columns[0].nullable is False
    assert description.columns[0].physical_type is not None
    assert description.columns[0].physical_type.iri == RC + "Varchar"
    assert len(description.columns[0].profile_observations) == 1
    profile = description.columns[0].profile_observations[0]
    assert profile.iri == result.observation.observation_iri
    assert profile.sample_size == 123
    assert profile.sample_scope == "All doc_id values in the local Messages test table."
    assert profile.sample_method == "DuckDB column aggregate query over the full table."
    assert profile.row_count == 123
    assert profile.null_count == 0
    assert profile.distinct_count == 123
    assert [(item.value, item.frequency) for item in profile.value_frequencies] == [
        ("doc-001", 1),
        ("doc-002", 1),
    ]
    assert profile.observed_asset is not None
    assert profile.observed_asset.iri == table
    assert profile.observed_column is not None
    assert profile.observed_column.iri == column
    assert profile.evidence[0].sources == ["test://messages-doc-id-profile"]

    pattern = db.describe_pattern(result.pattern.pattern_iri)
    assert [target.iri for target in pattern.pattern_targets] == [column]
    assert [target.iri for target in pattern.map_implications] == [column]
    assert [item.iri for item in pattern.supporting_observations] == [
        result.observation.observation_iri
    ]

    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_record_column_profile_preflights_pattern_validation_without_mutation(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Orders"
    column = "https://example.test/project#OrdersStatus"
    db.record_map_dataset(table, label="Orders", is_table=True)
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match="pattern_stability"):
        db.record_column_profile(
            column,
            column_name="status",
            table_iri=table,
            summary="Invalid column profile pattern should not write.",
            evidence_summary="Synthetic column profile output.",
            evidence_sources=["test://orders-status-profile"],
            update_map_column=False,
            pattern_summary="Status profile has an invalid stability.",
            pattern_text="This pattern is intentionally invalid.",
            pattern_rationale="The test uses an unknown stability value.",
            pattern_stability="rc:NotAStability",
        )

    assert _mutable_graph_counts(db) == before_counts
    assert db.search("Invalid column profile pattern", graph="observations").matches == []
    assert db.search("Synthetic column profile output", graph="evidence").matches == []


def test_describe_dataset_surfaces_unmapped_column_profile_observations(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Orders"
    column = "https://example.test/project#OrdersStatus"
    db.record_map_dataset(table, label="Orders", is_table=True)

    result = db.record_column_profile(
        column,
        column_name="status",
        table_iri=table,
        summary="Sampled status values were profiled without updating the map.",
        evidence_summary="Synthetic sampled top-N profile output.",
        evidence_sources=["test://orders-status-topn"],
        sample_size=50,
        sample_scope="Fifty sampled Orders rows.",
        sample_method="Top-N value-frequency query over a sample.",
        null_count=0,
        distinct_count=4,
        value_frequencies=[
            {"value": "fulfilled", "frequency": 38},
            {"value": "pending", "frequency": 8},
        ],
        update_map_column=False,
    )

    description = db.describe_dataset(table)

    assert description.columns == []
    assert description.profile_observations == []
    assert description.profile_summary.returned_dataset_profile_count == 0
    assert description.profile_summary.returned_mapped_column_profile_count == 0
    assert description.profile_summary.returned_unmapped_column_profile_count == 1
    assert description.profile_summary.returned_profile_count == 1
    assert description.profile_summary.shared_evidence_iris == [
        result.observation.evidence_iri
    ]
    assert "not mapped as current columns" in (
        description.profile_summary.handoff_note
    )
    assert len(description.unmapped_column_profile_observations) == 1
    profile = description.unmapped_column_profile_observations[0]
    assert profile.iri == result.observation.observation_iri
    assert profile.observed_asset is not None
    assert profile.observed_asset.iri == table
    assert profile.observed_column is not None
    assert profile.observed_column.iri == column
    assert profile.observed_column_name == "status"
    assert profile.observed_column.column_name == "status"
    assert profile.sample_scope == "Fifty sampled Orders rows."
    assert [(item.value, item.frequency) for item in profile.value_frequencies] == [
        ("fulfilled", 38),
        ("pending", 8),
    ]

    db.record_map_column(column, column_name="status", table_iri=table)

    description = db.describe_dataset(table)
    assert [item.iri for item in description.columns] == [column]
    assert description.unmapped_column_profile_observations == []
    assert description.profile_summary.returned_mapped_column_profile_count == 1
    assert description.profile_summary.returned_unmapped_column_profile_count == 0
    assert description.profile_summary.mapped_profiled_column_count == 1
    assert description.columns[0].profile_observations[0].iri == (
        result.observation.observation_iri
    )

    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_profile_summary_reports_bounded_profile_omissions(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#Orders"
    db.record_map_dataset(table, label="Orders", is_table=True)

    for index in range(7):
        db.record_column_profile(
            f"https://example.test/project#OrdersProfiledColumn{index}",
            column_name=f"profiled_{index}",
            table_iri=table,
            summary=f"Profiled Orders column {index}.",
            evidence_summary=f"Synthetic profile output {index}.",
            evidence_sources=[f"test://orders-profile-{index}"],
            sample_size=25,
            sample_scope="Sampled Orders rows.",
            sample_method="Synthetic profile query.",
            null_count=0,
            distinct_count=3,
            update_map_column=False,
        )

    description = db.describe_dataset(table)

    assert len(description.unmapped_column_profile_observations) == 5
    assert description.profile_summary.returned_dataset_profile_count == 0
    assert description.profile_summary.returned_mapped_column_profile_count == 0
    assert description.profile_summary.returned_unmapped_column_profile_count == 5
    assert description.profile_summary.returned_profile_count == 5
    assert description.profile_summary.total_dataset_profile_count == 0
    assert description.profile_summary.total_mapped_column_profile_count == 0
    assert description.profile_summary.total_unmapped_column_profile_count == 7
    assert description.profile_summary.total_profile_count == 7
    assert description.profile_summary.omitted_dataset_profile_count == 0
    assert description.profile_summary.omitted_mapped_column_profile_count == 0
    assert description.profile_summary.omitted_unmapped_column_profile_count == 2
    assert description.profile_summary.omitted_profile_count == 2
    assert "2 additional profile observation(s)" in (
        description.profile_summary.handoff_note
    )

    context_slice = db.get_context_graph([table], profile="deep_lore")

    assert context_slice.dataset_contexts[0].profile_summary.omitted_profile_count == 2


def test_record_profile_bundle_writes_dataset_and_column_profiles(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    amount_column = "https://example.test/project#OrdersAmount"
    shared_evidence = "https://example.test/project#OrdersProfileRunEvidence"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        physical_type="rc:Varchar",
    )

    result = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled with row count and column sketches.",
        observed_by="urn:doxabase:test-agent",
        evidence_summary="Synthetic DuckDB profiling pass.",
        evidence_sources=["test://orders-profile"],
        sample_size=100,
        sample_scope="All rows in the local Orders table.",
        sample_method="DuckDB full-table profiling query.",
        row_count=100,
        map_label="Orders",
        is_table=True,
        shared_evidence_iri=shared_evidence,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Top status values were observed in the profile.",
                "distinct_count": 3,
                "value_frequencies": [
                    {"value": "fulfilled", "frequency": 70},
                    {"value": "pending", "count": 20},
                ],
            },
            {
                "column_iri": amount_column,
                "column_name": "amount",
                "summary": "Order amount was profiled as a non-null decimal.",
                "null_count": 0,
                "profile_metrics": [{"metric": "rc:MeanValue", "value": 42.5}],
                "update_map_column": True,
                "physical_type": "rc:Decimal",
                "nullable": False,
            },
        ],
    )

    assert result.dataset_iri == dataset
    assert result.shared_evidence_iri == shared_evidence
    assert result.dataset_profile.observation.observation_type == "profile"
    assert result.dataset_profile.map_dataset is not None
    assert len(result.column_profiles) == 2
    assert result.column_profiles[0].map_column is None
    assert result.column_profiles[1].map_column is not None
    assert result.dataset_profile.observation.evidence_iri == shared_evidence
    assert {
        column_profile.observation.evidence_iri
        for column_profile in result.column_profiles
    } == {shared_evidence}
    assert result.handoff_entrypoints.dataset_iri == dataset
    assert result.handoff_entrypoints.shared_evidence_iri == shared_evidence
    assert result.handoff_entrypoints.dataset_profile_observation_iri == (
        result.dataset_profile.observation.observation_iri
    )
    profile_observation_iris = [
        result.dataset_profile.observation.observation_iri,
        *(
            column_profile.observation.observation_iri
            for column_profile in result.column_profiles
        ),
    ]
    assert set(result.handoff_entrypoints.profile_observation_iris) == {
        result.dataset_profile.observation.observation_iri,
        *(
            column_profile.observation.observation_iri
            for column_profile in result.column_profiles
        ),
    }
    assert result.handoff_entrypoints.map_dataset_recorded is True
    assert result.handoff_entrypoints.map_column_iris == [amount_column]
    assert result.handoff_entrypoints.updated_map_column_iris == [amount_column]
    assert result.handoff_entrypoints.mapped_profiled_column_iris == [
        status_column,
        amount_column,
    ]
    assert result.handoff_entrypoints.dataset_describe_available is True
    assert result.handoff_entrypoints.profile_run_available is True
    assert [
        action.tool_name for action in result.handoff_entrypoints.suggested_next_actions
    ] == [
        "describe_dataset",
        "describe_profile_run",
        "draft_profile_map_updates",
        "get_context_graph",
        "get_context_graph",
    ]
    assert result.handoff_entrypoints.suggested_next_actions[0].arguments == {
        "iri": dataset
    }
    assert result.handoff_entrypoints.suggested_next_actions[1].arguments == {
        "dataset_iri": dataset,
        "evidence_iri": shared_evidence,
    }
    assert result.handoff_entrypoints.suggested_next_actions[2].arguments == {
        "dataset_iri": dataset,
        "evidence_iri": shared_evidence,
    }
    assert result.handoff_entrypoints.suggested_next_actions[-1].arguments == {
        "seed_iris": profile_observation_iris,
        "profile": "dataset_brief",
    }
    assert result.handoff_entrypoints.suggested_next_calls[0] == (
        f"describe_dataset('{dataset}')"
    )
    assert result.handoff_entrypoints.suggested_next_calls[1] == (
        f"describe_profile_run('{dataset}', '{shared_evidence}')"
    )
    assert result.handoff_entrypoints.suggested_next_calls[2] == (
        f"draft_profile_map_updates('{dataset}', '{shared_evidence}')"
    )
    assert result.handoff_entrypoints.suggested_next_calls[-1] == (
        f"get_context_graph({profile_observation_iris!r}, "
        "profile='dataset_brief')"
    )

    description = db.describe_dataset(dataset)

    assert description.label == "Orders"
    assert description.row_count_snapshot == 100
    assert description.profile_summary.returned_dataset_profile_count == 1
    assert description.profile_summary.returned_mapped_column_profile_count == 2
    assert description.profile_summary.returned_unmapped_column_profile_count == 0
    assert description.profile_summary.returned_profile_count == 3
    assert description.profile_summary.mapped_profiled_column_count == 2
    assert description.profile_summary.evidence_iris == [shared_evidence]
    assert description.profile_summary.evidence_profile_counts == {
        shared_evidence: 3,
    }
    assert description.profile_summary.shared_evidence_iris == [shared_evidence]
    assert [
        candidate.evidence_iri
        for candidate in description.profile_summary.profile_run_candidates
    ] == [shared_evidence]
    assert set(
        description.profile_summary.profile_run_candidates[0].profile_observation_iris
    ) == {
        result.dataset_profile.observation.observation_iri,
        *(
            column_profile.observation.observation_iri
            for column_profile in result.column_profiles
        ),
    }
    assert (
        description.profile_summary.profile_run_candidates[0].returned_profile_count
        == 3
    )
    assert (
        description.profile_summary.profile_run_candidates[
            0
        ].dataset_profile_row_counts
        == [100]
    )
    assert (
        description.profile_summary.profile_run_candidates[
            0
        ].dataset_profile_row_count_bases
        == {"100": ["full_scan"]}
    )
    assert (
        description.profile_summary.profile_run_candidates[
            0
        ].row_count_snapshot_matches
        is True
    )
    assert (
        description.profile_summary.profile_run_candidates[
            0
        ].row_count_snapshot_basis
        == "full_scan"
    )
    assert (
        description.profile_summary.profile_run_candidates[
            0
        ].shared_by_all_returned_profiles
        is True
    )
    assert "3 profile observation(s)" in description.profile_summary.handoff_note
    assert "one profiler run" in description.profile_summary.handoff_note
    assert len(description.profile_observations) == 1
    dataset_profile = description.profile_observations[0]
    assert dataset_profile.sample_scope == "All rows in the local Orders table."
    assert dataset_profile.evidence[0].iri == shared_evidence
    assert dataset_profile.evidence[0].sources == ["test://orders-profile"]

    assert {column.iri for column in description.columns} == {
        status_column,
        amount_column,
    }
    amount_description = next(
        column for column in description.columns if column.iri == amount_column
    )
    amount_profile = amount_description.profile_observations[0]
    assert amount_profile.sample_method == "DuckDB full-table profiling query."
    assert amount_profile.null_count == 0
    assert amount_profile.profile_metrics[0].metric.iri == RC + "MeanValue"
    assert amount_description.nullable is False
    assert amount_description.physical_type is not None
    assert amount_description.physical_type.iri == RC + "Decimal"
    status_description = next(
        column for column in description.columns if column.iri == status_column
    )
    assert status_description.profile_observations[0].distinct_count == 3
    assert [
        (item.value, item.frequency)
        for item in status_description.profile_observations[0].value_frequencies
    ] == [
        ("fulfilled", 70),
        ("pending", 20),
    ]

    unmapped = description.unmapped_column_profile_observations
    assert unmapped == []

    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_record_profile_bundle_pattern_support_scope_all_profiles(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    amount_column = "https://example.test/project#OrdersAmount"
    shared_evidence = "https://example.test/project#OrdersProfileRunEvidence"

    result = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled with row count and column sketches.",
        evidence_summary="Synthetic DuckDB profiling pass.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=shared_evidence,
        row_count=100,
        map_label="Orders",
        is_table=True,
        pattern_summary="Orders profile pass supports a run-level synthesis.",
        pattern_text=(
            "The dataset profile and column profiles came from one Orders "
            "profiling pass."
        ),
        pattern_rationale=(
            "The row count, status distribution, and amount mean all link to "
            "the same shared run evidence."
        ),
        pattern_support_scope="all_profiles",
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Top status values were observed in the profile.",
                "distinct_count": 3,
            },
            {
                "column_iri": amount_column,
                "column_name": "amount",
                "summary": "Order amount was profiled.",
                "profile_metrics": [{"metric": "rc:MeanValue", "value": 42.5}],
            },
        ],
    )

    assert result.dataset_profile.pattern is not None
    pattern = db.describe_pattern(result.dataset_profile.pattern.pattern_iri)
    assert [target.iri for target in pattern.pattern_targets] == [dataset]
    assert [target.iri for target in pattern.map_implications] == [dataset]
    assert [evidence.iri for evidence in pattern.evidence] == [shared_evidence]
    assert {item.iri for item in pattern.supporting_observations} == {
        result.dataset_profile.observation.observation_iri,
        *[
            column_profile.observation.observation_iri
            for column_profile in result.column_profiles
        ],
    }

    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_record_profile_bundle_default_pattern_scope_is_dataset_profile(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"

    result = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled with row count and column sketches.",
        evidence_summary="Synthetic DuckDB profiling pass.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri="https://example.test/project#OrdersProfileRunEvidence",
        row_count=100,
        pattern_summary="Orders dataset profile supports a dataset synthesis.",
        pattern_text="The dataset profile row count came from the profile pass.",
        pattern_rationale=(
            "Default bundle pattern scope preserves the historical dataset-only "
            "support behavior."
        ),
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Top status values were observed in the profile.",
                "distinct_count": 3,
            }
        ],
    )

    assert result.dataset_profile.pattern is not None
    pattern = db.describe_pattern(result.dataset_profile.pattern.pattern_iri)
    assert [item.iri for item in pattern.supporting_observations] == [
        result.dataset_profile.observation.observation_iri
    ]


def test_record_profile_bundle_rejects_unknown_pattern_support_scope(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(
        DoxaBaseError,
        match="pattern_support_scope must be one of",
    ):
        db.record_profile_bundle(
            "https://example.test/project#Orders",
            dataset_summary="Orders were profiled.",
            pattern_support_scope="whole_run",
        )


def test_profile_summary_surfaces_run_candidates_in_mixed_profile_history(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    older_evidence = "https://example.test/project#OlderProfileEvidence"
    newer_evidence = "https://example.test/project#NewerProfileRunEvidence"

    db.record_dataset_profile(
        dataset,
        summary="Older dataset-only profile result.",
        evidence_summary="Older one-off profiling pass.",
        evidence_sources=["test://orders-profile-old"],
        evidence_iri=older_evidence,
        row_count=80,
        map_label="Orders",
        is_table=True,
    )
    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Newer profile bundle over dataset and columns.",
        evidence_summary="Newer shared profiling pass.",
        evidence_sources=["test://orders-profile-new"],
        shared_evidence_iri=newer_evidence,
        sample_size=100,
        sample_scope="All rows in the local Orders table.",
        sample_method="DuckDB full-table profiling query.",
        row_count=100,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": "https://example.test/project#OrdersStatus",
                "column_name": "status",
                "summary": "Status values were profiled.",
                "distinct_count": 3,
            },
            {
                "column_iri": "https://example.test/project#OrdersAmount",
                "column_name": "amount",
                "summary": "Amount values were profiled.",
                "null_count": 0,
            },
        ],
    )

    description = db.describe_dataset(dataset)

    assert description.profile_summary.returned_profile_count == 4
    assert description.profile_summary.evidence_profile_counts == {
        newer_evidence: 3,
        older_evidence: 1,
    }
    assert description.profile_summary.shared_evidence_iris == []
    assert [
        candidate.evidence_iri
        for candidate in description.profile_summary.profile_run_candidates
    ] == [newer_evidence]
    run_candidate = description.profile_summary.profile_run_candidates[0]
    assert run_candidate.returned_profile_count == 3
    assert run_candidate.dataset_profile_row_counts == [100]
    assert run_candidate.dataset_profile_row_count_bases == {"100": ["full_scan"]}
    assert run_candidate.row_count_snapshot_matches is False
    assert run_candidate.row_count_snapshot_basis is None
    assert set(run_candidate.profile_observation_iris) == {
        bundle.dataset_profile.observation.observation_iri,
        *(
            column_profile.observation.observation_iri
            for column_profile in bundle.column_profiles
        ),
    }
    assert run_candidate.shared_by_all_returned_profiles is False


def test_profile_run_candidates_are_count_ranked_and_ignore_singletons(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence_a = "https://example.test/project#EvidenceA"
    evidence_b = "https://example.test/project#EvidenceB"
    evidence_c = "https://example.test/project#EvidenceC"
    evidence_singleton = "https://example.test/project#EvidenceSingleton"
    status_column = "https://example.test/project#OrdersStatus"
    amount_column = "https://example.test/project#OrdersAmount"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(status_column, column_name="status", table_iri=dataset)
    db.record_map_column(amount_column, column_name="amount", table_iri=dataset)
    for index in range(3):
        db.record_observation(
            summary=f"A-backed profile {index}",
            observation_type="profile",
            observed_asset=dataset,
            evidence_summary="Profile pass A.",
            evidence_iri=evidence_a,
        )
    for index in range(2):
        db.record_observation(
            summary=f"B-backed profile {index}",
            observation_type="profile",
            observed_asset=dataset,
            observed_column=status_column,
            evidence_summary="Profile pass B.",
            evidence_iri=evidence_b,
        )
        db.record_observation(
            summary=f"C-backed profile {index}",
            observation_type="profile",
            observed_asset=dataset,
            observed_column=amount_column,
            evidence_summary="Profile pass C.",
            evidence_iri=evidence_c,
        )
    db.record_observation(
        summary="One-off singleton profile",
        observation_type="profile",
        observed_asset=dataset,
        evidence_summary="One-off profile.",
        evidence_iri=evidence_singleton,
    )

    candidates = db.describe_dataset(dataset).profile_summary.profile_run_candidates

    assert [
        (
            candidate.evidence_iri,
            candidate.returned_profile_count,
            candidate.dataset_profile_row_counts,
            candidate.dataset_profile_row_count_bases,
            candidate.row_count_snapshot_matches,
            candidate.row_count_snapshot_basis,
        )
        for candidate in candidates
    ] == [
        (evidence_a, 3, [], {}, False, None),
        (evidence_b, 2, [], {}, False, None),
        (evidence_c, 2, [], {}, False, None),
    ]
    assert all(
        not candidate.shared_by_all_returned_profiles for candidate in candidates
    )
    assert all(candidate.profile_observation_iris for candidate in candidates)


def test_profile_run_candidates_prefer_row_count_snapshot_match_on_ties(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    storage = "https://example.test/project#OrdersStorage"
    layout = "https://example.test/project#OrdersParquetLayout"
    old_evidence = "https://example.test/project#AOldProfileEvidence"
    matching_evidence = "https://example.test/project#ZMatchingProfileEvidence"

    db.record_map_storage_access(
        storage,
        label="Orders local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="directory",
        storage_root=str(tmp_path / "warehouse"),
        datasets=[dataset],
    )
    db.record_map_physical_layout(
        layout,
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
        datasets=[dataset],
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=120,
        path_templates=["orders/dt={date}.parquet"],
        storage_accesses=[storage],
        physical_layouts=[layout],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Older profile run with stale row count.",
        evidence_summary="Older profile evidence.",
        evidence_sources=["test://orders-profile-old"],
        shared_evidence_iri=old_evidence,
        row_count=80,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status was profiled in the older run.",
            }
        ],
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Matching profile run with current row count.",
        evidence_summary="Matching profile evidence.",
        evidence_sources=["test://orders-profile-current"],
        shared_evidence_iri=matching_evidence,
        row_count=120,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status was profiled in the matching run.",
            }
        ],
    )

    description = db.describe_dataset(dataset)

    assert [
        (
            candidate.evidence_iri,
            candidate.returned_profile_count,
            candidate.dataset_profile_row_counts,
            candidate.dataset_profile_row_count_bases,
            candidate.row_count_snapshot_matches,
            candidate.row_count_snapshot_basis,
        )
        for candidate in description.profile_summary.profile_run_candidates
    ] == [
        (matching_evidence, 2, [120], {"120": ["unknown"]}, True, "unknown"),
        (old_evidence, 2, [80], {"80": ["unknown"]}, False, None),
    ]

    context = db.describe_query_context(dataset)

    assert context.suggested_next_actions[0].tool_name == "describe_profile_run"
    assert context.suggested_next_actions[0].arguments == {
        "dataset_iri": dataset,
        "evidence_iri": matching_evidence,
    }
    assert [
        action.tool_name for action in context.suggested_next_actions[:3]
    ] == [
        "describe_profile_run",
        "describe_profile_run",
        "draft_query_plan",
    ]
    assert context.safe_inspection_action_indexes == [0, 1]
    assert context.first_safe_inspection_action_index == 0
    assert context.unattended_recommended_action_indexes == [2]
    assert context.first_unattended_action_index == 2
    assert context.suggested_next_actions[1].action_label == (
        "Inspect additional profile run evidence"
    )
    assert context.suggested_next_actions[1].arguments == {
        "dataset_iri": dataset,
        "evidence_iri": old_evidence,
    }
    assert "sampled, unknown, or mixed basis" in (
        context.suggested_next_actions[1].reason
    )
    matching_run = db.describe_profile_run(dataset, matching_evidence)
    old_run = db.describe_profile_run(dataset, old_evidence)
    assert matching_run.row_count_snapshot == 120
    assert matching_run.dataset_profile_row_counts == [120]
    assert matching_run.dataset_profile_row_count_bases == {"120": ["unknown"]}
    assert matching_run.row_count_snapshot_matches is True
    assert matching_run.row_count_snapshot_basis == "unknown"
    assert old_run.row_count_snapshot == 120
    assert old_run.dataset_profile_row_counts == [80]
    assert old_run.dataset_profile_row_count_bases == {"80": ["unknown"]}
    assert old_run.row_count_snapshot_matches is False
    assert old_run.row_count_snapshot_basis is None


def test_describe_profile_run_returns_wide_shared_evidence_run(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WideOrders"
    shared_evidence = "https://example.test/project#WideOrdersProfileRunEvidence"

    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Wide Orders dataset was profiled with many columns.",
        evidence_summary="Wide profile pass.",
        evidence_sources=["test://wide-orders-profile"],
        shared_evidence_iri=shared_evidence,
        row_count=100,
        map_label="Wide Orders",
        is_table=True,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": f"https://example.test/project#WideOrdersColumn{index}",
                "column_name": f"column_{index}",
                "summary": f"Wide Orders column {index} was profiled.",
                "distinct_count": index + 1,
            }
            for index in range(8)
        ],
    )

    bounded = db.describe_dataset(dataset)
    assert bounded.profile_summary.returned_profile_count == 6
    assert bounded.profile_summary.total_profile_count == 9
    assert bounded.profile_summary.omitted_profile_count == 3
    assert (
        bounded.profile_summary.profile_run_candidates[0].returned_profile_count
        == 6
    )

    profile_run = db.describe_profile_run(dataset, shared_evidence)

    assert profile_run.evidence_iri == shared_evidence
    assert profile_run.returned_dataset_profile_count == 1
    assert profile_run.returned_mapped_column_profile_count == 0
    assert profile_run.returned_unmapped_column_profile_count == 8
    assert profile_run.returned_profile_count == 9
    assert profile_run.total_profile_count == 9
    assert profile_run.omitted_profile_count == 0
    assert set(profile_run.profile_observation_iris) == {
        bundle.dataset_profile.observation.observation_iri,
        *(
            column_profile.observation.observation_iri
            for column_profile in bundle.column_profiles
        ),
    }
    assert "no separate persisted profile-run node" in profile_run.retrieval_note
    assert [action.tool_name for action in profile_run.suggested_next_actions] == [
        "draft_profile_map_updates"
    ]
    assert profile_run.suggested_next_actions[0].action_label == (
        "Inspect profile map-update status"
    )
    assert profile_run.suggested_next_actions[0].arguments == {
        "dataset_iri": dataset,
        "evidence_iri": shared_evidence,
    }
    assert profile_run.suggested_next_calls == [
        action.call for action in profile_run.suggested_next_actions
    ]

    capped = db.describe_profile_run(dataset, shared_evidence, limit=3)

    assert capped.returned_profile_count == 3
    assert capped.total_profile_count == 9
    assert capped.omitted_profile_count == 6
    assert len(capped.profile_observation_iris) == 3
    assert [action.tool_name for action in capped.suggested_next_actions] == [
        "describe_profile_run",
        "draft_profile_map_updates",
    ]
    assert capped.suggested_next_actions[0].arguments == {
        "dataset_iri": dataset,
        "evidence_iri": shared_evidence,
    }
    assert capped.suggested_next_actions[1].arguments == {
        "dataset_iri": dataset,
        "evidence_iri": shared_evidence,
    }


def test_describe_profile_run_works_for_observation_only_dataset(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#ObservationOnlyOrders"
    shared_evidence = "https://example.test/project#ObservationOnlyProfileRunEvidence"

    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Observation-only Orders profile.",
        evidence_summary="Observation-only profile pass.",
        evidence_sources=["test://observation-only-profile"],
        shared_evidence_iri=shared_evidence,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": "https://example.test/project#ObservationOnlyStatus",
                "column_name": "status",
                "summary": "Observation-only status profile.",
            }
        ],
    )

    assert bundle.handoff_entrypoints.map_dataset_recorded is False
    assert bundle.handoff_entrypoints.dataset_describe_available is False
    assert bundle.handoff_entrypoints.profile_run_available is True
    assert bundle.handoff_entrypoints.profile_observation_iris == [
        bundle.dataset_profile.observation.observation_iri,
        bundle.column_profiles[0].observation.observation_iri,
    ]
    assert bundle.handoff_entrypoints.suggested_next_calls[0] == (
        f"describe_profile_run('{dataset}', '{shared_evidence}')"
    )
    assert [
        action.tool_name for action in bundle.handoff_entrypoints.suggested_next_actions
    ] == [
        "describe_profile_run",
        "get_context_graph",
    ]
    assert bundle.handoff_entrypoints.suggested_next_actions[0].arguments == {
        "dataset_iri": dataset,
        "evidence_iri": shared_evidence,
    }
    assert bundle.handoff_entrypoints.suggested_next_actions[-1].arguments == {
        "seed_iris": bundle.handoff_entrypoints.profile_observation_iris,
        "profile": "dataset_brief",
    }
    assert bundle.handoff_entrypoints.suggested_next_calls[-1] == (
        "get_context_graph("
        f"{bundle.handoff_entrypoints.profile_observation_iris!r}, "
        "profile='dataset_brief')"
    )
    assert not any(
        call.startswith("describe_dataset")
        for call in bundle.handoff_entrypoints.suggested_next_calls
    )
    assert "No map dataset subject" in bundle.handoff_entrypoints.handoff_note

    with pytest.raises(DoxaBaseError, match="was not found") as exc_info:
        db.describe_dataset(dataset)
    error_message = str(exc_info.value)
    assert "profile observation(s) reference this dataset" in error_message
    assert "describe_profile_run" in error_message
    assert shared_evidence in error_message
    assert "seed get_context_graph" in error_message
    assert "record_map_dataset" in error_message

    profile_run = db.describe_profile_run(dataset, shared_evidence)

    assert profile_run.dataset.iri == dataset
    assert profile_run.returned_dataset_profile_count == 1
    assert profile_run.returned_unmapped_column_profile_count == 1
    assert profile_run.returned_profile_count == 2
    assert [action.tool_name for action in profile_run.suggested_next_actions] == [
        "draft_profile_map_updates"
    ]


def test_profile_bundle_handoff_distinguishes_existing_map_context_without_snapshot(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#ExistingMapOrders"
    status_column = "https://example.test/project#ExistingMapOrdersStatus"
    shared_evidence = "https://example.test/project#ExistingMapOrdersProfileEvidence"
    db.record_map_dataset(dataset, label="Existing Map Orders", is_table=True)

    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Existing map Orders profile stayed observation-only.",
        evidence_summary="Profile pass over existing map shell.",
        evidence_sources=["test://existing-map-orders-profile"],
        shared_evidence_iri=shared_evidence,
        row_count=120,
        update_map_snapshot=False,
        profile_metrics=[{"metric": "rc:MeanValue", "value": 4.5}],
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Existing map Orders status values were profiled.",
                "distinct_count": 3,
                "profile_metrics": [{"metric": "rc:MaximumValue", "value": 9}],
            }
        ],
    )

    assert bundle.dataset_profile.map_dataset is None
    assert bundle.handoff_entrypoints.map_dataset_recorded is False
    assert bundle.handoff_entrypoints.dataset_describe_available is True
    assert bundle.handoff_entrypoints.profile_run_available is True
    assert bundle.handoff_entrypoints.suggested_next_calls[:2] == [
        f"describe_dataset('{dataset}')",
        f"describe_profile_run('{dataset}', '{shared_evidence}')",
    ]
    assert bundle.handoff_entrypoints.suggested_next_calls[2] == (
        f"draft_profile_map_updates('{dataset}', '{shared_evidence}')"
    )
    assert "already existed" in bundle.handoff_entrypoints.handoff_note
    assert "did not write dataset map facts" in bundle.handoff_entrypoints.handoff_note
    assert "row-count snapshot" in bundle.handoff_entrypoints.handoff_note

    description = db.describe_dataset(dataset)
    assert description.row_count_snapshot is None
    assert description.profile_summary.returned_profile_count == 2

    profile_run = db.describe_profile_run(dataset, shared_evidence)
    assert profile_run.returned_profile_count == 2
    assert set(profile_run.profile_observation_iris) == set(
        bundle.handoff_entrypoints.profile_observation_iris
    )

    context_slice = db.get_context_graph(
        bundle.handoff_entrypoints.profile_observation_iris,
        profile="dataset_brief",
    )
    assert {
        profile.iri for profile in context_slice.seed_profile_observations
    } == set(bundle.handoff_entrypoints.profile_observation_iris)
    assert context_slice.route_counts["observed_profile_metric"] == 2


def test_profile_bundle_mixed_run_handoff_actions_route_without_guessing(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/handoff-trial#"
    mixed = f"{base}MixedOrders"
    amount = f"{base}MixedOrdersAmount"
    run_a = f"{base}MixedOrdersProfileRunA"
    run_b = f"{base}MixedOrdersProfileRunB"
    shadow = f"{base}ShadowEvents"
    shadow_run = f"{base}ShadowEventsObservationOnlyRun"

    def run_handoff_actions(actions) -> None:
        for action in actions:
            if action.tool_name == "describe_dataset":
                db.describe_dataset(**action.arguments)
            elif action.tool_name == "describe_profile_run":
                db.describe_profile_run(**action.arguments)
            elif action.tool_name == "draft_profile_map_updates":
                db.draft_profile_map_updates(**action.arguments)
            elif action.tool_name == "get_context_graph":
                db.get_context_graph(**action.arguments)
            else:
                raise AssertionError(f"Unexpected action {action.tool_name!r}")

    run_a_bundle = db.record_profile_bundle(
        mixed,
        dataset_summary="Mixed orders run A profile.",
        observed_at="2026-06-01T00:00:00Z",
        evidence_summary="Mixed orders profile run A.",
        evidence_sources=["test://mixed-orders/run-a"],
        shared_evidence_iri=run_a,
        row_count=1000,
        map_label="Mixed Orders",
        is_table=True,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": amount,
                "column_name": "amount",
                "summary": "Run A amount values were profiled.",
                "null_count": 0,
                "update_map_column": True,
                "physical_type": "rc:Decimal",
                "nullable": False,
            },
            *(
                {
                    "column_iri": f"{base}MixedOrdersRunAExtra{index}",
                    "column_name": f"run_a_extra_{index}",
                    "summary": f"Run A extra column {index} was profiled.",
                    "distinct_count": index + 1,
                }
                for index in range(4)
            ),
        ],
    )
    run_b_bundle = db.record_profile_bundle(
        mixed,
        dataset_summary="Mixed orders run B profile over existing map context.",
        observed_at="2026-06-02T00:00:00Z",
        evidence_summary="Mixed orders profile run B.",
        evidence_sources=["test://mixed-orders/run-b"],
        shared_evidence_iri=run_b,
        row_count=1200,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": amount,
                "column_name": "amount",
                "summary": "Run B amount values were profiled without map writes.",
                "null_count": 1,
            },
            *(
                {
                    "column_iri": f"{base}MixedOrdersRunBExtra{index}",
                    "column_name": f"run_b_extra_{index}",
                    "summary": f"Run B extra column {index} was profiled.",
                    "distinct_count": index + 2,
                }
                for index in range(3)
            ),
        ],
    )
    shadow_bundle = db.record_profile_bundle(
        shadow,
        dataset_summary="Shadow events profile stayed observation-only.",
        observed_at="2026-06-03T00:00:00Z",
        evidence_summary="Shadow events observation-only run.",
        evidence_sources=["test://shadow-events/profile"],
        shared_evidence_iri=shadow_run,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": f"{base}ShadowEventsKind",
                "column_name": "kind",
                "summary": "Shadow event kind was profiled.",
            },
            {
                "column_iri": f"{base}ShadowEventsPayload",
                "column_name": "payload",
                "summary": "Shadow event payload was profiled.",
            },
        ],
    )

    assert run_a_bundle.handoff_entrypoints.updated_map_column_iris == [amount]
    assert run_a_bundle.handoff_entrypoints.mapped_profiled_column_iris == [amount]
    assert run_b_bundle.handoff_entrypoints.updated_map_column_iris == []
    assert run_b_bundle.handoff_entrypoints.map_column_iris == []
    assert run_b_bundle.handoff_entrypoints.mapped_profiled_column_iris == [amount]
    assert shadow_bundle.handoff_entrypoints.dataset_describe_available is False
    assert [
        action.tool_name
        for action in shadow_bundle.handoff_entrypoints.suggested_next_actions
    ] == ["describe_profile_run", "get_context_graph"]

    all_actions = [
        *run_a_bundle.handoff_entrypoints.suggested_next_actions,
        *run_b_bundle.handoff_entrypoints.suggested_next_actions,
        *shadow_bundle.handoff_entrypoints.suggested_next_actions,
    ]
    assert len(all_actions) == 12
    run_handoff_actions(all_actions)

    description = db.describe_dataset(mixed)
    summary = description.profile_summary
    assert summary.total_profile_count == 11
    assert summary.returned_profile_count == 9
    assert summary.omitted_profile_count == 2
    assert summary.shared_evidence_iris == []
    candidates = {
        candidate.evidence_iri: candidate
        for candidate in summary.profile_run_candidates
    }
    assert set(candidates) == {run_a, run_b}
    assert candidates[run_b].returned_profile_count == 5
    assert candidates[run_a].returned_profile_count == 4
    assert all(
        candidate.shared_by_all_returned_profiles is False
        for candidate in candidates.values()
    )

    run_a_full = db.describe_profile_run(mixed, run_a)
    run_b_full = db.describe_profile_run(mixed, run_b)
    shadow_full = db.describe_profile_run(shadow, shadow_run)
    assert run_a_full.returned_profile_count == 6
    assert run_b_full.returned_profile_count == 5
    assert shadow_full.returned_profile_count == 3
    assert set(run_a_full.profile_observation_iris) == set(
        run_a_bundle.handoff_entrypoints.profile_observation_iris
    )
    assert set(run_b_full.profile_observation_iris) == set(
        run_b_bundle.handoff_entrypoints.profile_observation_iris
    )
    assert set(shadow_full.profile_observation_iris) == set(
        shadow_bundle.handoff_entrypoints.profile_observation_iris
    )


def test_generic_revision_list_surfaces_profile_gate_cautions(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/profile-generic-gate#Orders"
    status_column = "https://example.test/profile-generic-gate#OrdersStatus"
    value_type = "https://example.test/profile-generic-gate#CustomerStatusValue"
    evidence = "https://example.test/profile-generic-gate#OrdersProfileEvidence"

    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=8,
    )
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        physical_type="rc:Varchar",
    )
    profile_bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled with semantic type evidence.",
        evidence_summary="Synthetic profile output for generic gate routing.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        sample_size=10,
        sample_scope="All rows in the Orders table.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=10,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status carried a project value type.",
                "physical_type": "rc:Varchar",
                "value_type": value_type,
            }
        ],
    )
    profile = db.describe_profile_run(
        dataset,
        evidence,
    ).mapped_column_profile_observations[0]
    support = db.record_pattern(
        summary="Customer status value needs vocabulary.",
        pattern_text=(
            "Customer status value names the reviewed customer lifecycle "
            "domain before it becomes current map type context."
        ),
        rationale="The pattern and profile run share one evidence resource.",
        pattern_targets=[value_type],
        supporting_observations=[profile.iri],
        evidence_iri=evidence,
        map_implications=[value_type],
    )

    staged_map = db.stage_profile_map_updates(
        dataset,
        evidence,
        accepted_recommendation_indexes=[0],
    )
    draft = db.draft_profile_map_updates(dataset, evidence)
    promotion_action = next(
        action
        for action in draft.type_advisories[0].suggested_next_actions
        if action.tool_name == "stage_pattern_promotion"
    )
    promoted = db.stage_pattern_promotion(**promotion_action.arguments)
    promoted_iri = promoted.staged_revisions[0].revision_iri

    listing = db.list_graph_revisions(
        current_staged_work_only=True,
        include_apply_checks=True,
    )
    rows = {item.iri: item for item in listing.revisions}
    map_row = rows[staged_map.staged_revision.revision_iri]
    semantic_row = rows[promoted_iri]

    assert map_row.profile_route_keys
    assert map_row.profile_gate_label == "bulk_allowed_after_review"
    assert map_row.profile_generic_queue_caution == (
        "generic queues may be followed after profile review; "
        "rerun after mutation"
    )
    assert map_row.profile_safe_single_apply_candidate is True
    assert map_row.profile_bulk_apply_allowed is True
    assert semantic_row.profile_route_keys
    assert semantic_row.profile_semantic_apply_role == "profile_type_candidate"
    assert semantic_row.profile_gate_label == "blocked_by_profile_gate"
    assert semantic_row.profile_safe_single_apply_candidate is False
    assert semantic_row.profile_bulk_apply_allowed is False
    assert semantic_row.profile_generic_queue_caution == (
        "do not follow generic apply_after_review until profile gate is resolved"
    )
    queue_by_row = {item.row_iri: item for item in listing.next_action_queue_items}
    assert queue_by_row[promoted_iri].profile_gate_label == (
        "blocked_by_profile_gate"
    )
    assert queue_by_row[promoted_iri].profile_generic_queue_caution == (
        semantic_row.profile_generic_queue_caution
    )

    export_path = tmp_path / "generic-profile-gate-review.md"
    export = db.export_staged_revisions(
        [staged_map.staged_revision.revision_iri, promoted_iri],
        export_path,
    )
    export_queue_by_row = {
        item.row_iri: item for item in export.bundle_summary.next_action_queue_items
    }
    assert export_queue_by_row[promoted_iri].profile_gate_label == (
        "blocked_by_profile_gate"
    )
    exported = export_path.read_text(encoding="utf-8")
    assert "Generic queue caution" in exported
    assert "do not follow generic apply_after_review until profile gate is resolved" in (
        exported
    )
    assert support.pattern_iri in promotion_action.arguments["patterns"]
    assert profile_bundle.handoff_entrypoints.profile_observation_iris


def test_profile_type_review_stays_open_for_direct_map_undefined_value_type(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    amount_column = "https://example.test/project#OrdersAmount"
    money_value_type = "https://example.test/project#MoneyAmountValue"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled and amount was mapped directly.",
        evidence_summary="Synthetic amount profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        update_map_snapshot=False,
        column_profiles=[
            {
                "column_iri": amount_column,
                "column_name": "amount",
                "summary": "Amount was observed as decimal money.",
                "physical_type": "rc:Decimal",
                "value_type": money_value_type,
                "update_map_column": True,
            }
        ],
    )

    assert bundle.column_profiles[0].map_column is not None
    column = db.describe_dataset(dataset).columns[0]
    assert column.value_type is not None
    assert column.value_type.iri == money_value_type

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.recommendation_count == 0
    assert draft.type_advisory_count == 1
    assert draft.type_advisory_status_counts == {
        "type_finding_current_map_undefined_value_type": 1,
    }
    advisory = draft.type_advisories[0]
    assert advisory.observed_value_type is not None
    assert advisory.observed_value_type.iri == money_value_type
    assert advisory.current_value_type is not None
    assert advisory.current_value_type.iri == money_value_type
    assert advisory.promotion_pattern_count == 0
    assert "not defined as rc:ValueType" in advisory.rationale
    assert "not defined in ontology" in advisory.routing_note
    assert [
        action.tool_name for action in advisory.suggested_next_actions
    ] == [
        "get_context_graph",
        "record_pattern",
        "stage_systematisation",
    ]
    assert "profile_type_review" in draft.suggested_next_action_groups
    assert [
        action.tool_name
        for action in draft.suggested_next_action_groups["profile_type_review"]
    ] == [
        "get_context_graph",
        "record_pattern",
        "stage_systematisation",
    ]
    grouped_actions = draft.suggested_next_action_groups["profile_type_review"]
    context_action = grouped_actions[0]
    pattern_action = grouped_actions[1]
    assert "semantic_move" not in context_action.source_profile_advisory
    assert (
        "produces_result_bindings"
        not in pattern_action.source_profile_advisory
    )
    plan_by_move = {
        item.semantic_move: item for item in draft.advisory_followthrough_plan
    }
    assert set(plan_by_move) == {"caveat_fallback"}
    assert plan_by_move["caveat_fallback"].review_lane == "profile_type_review"


def test_profile_type_context_action_omits_undefined_value_type_seed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    status_value_type = "https://example.test/project#StatusCodeValue"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        physical_type="rc:Varchar",
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Orders profile with an undefined project value type.",
        evidence_summary="Synthetic type-finding profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status looked integer-coded in the profile.",
                "physical_type": "rc:Integer",
                "value_type": status_value_type,
            }
        ],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)
    advisory = draft.type_advisories[0]
    context_action = advisory.suggested_next_actions[0]
    pattern_action = advisory.suggested_next_actions[1]
    value_type_action = [
        action
        for action in advisory.suggested_next_actions
        if action.tool_name == "stage_map_assertion_change"
        and action.arguments["predicate"] == "rc:valueType"
    ][0]

    assert context_action.tool_name == "get_context_graph"
    assert context_action.arguments == {
        "seed_iris": [advisory.profile_observation_iri, status_column, RC + "Integer"],
        "profile": "dataset_brief",
    }
    assert status_value_type not in context_action.arguments["seed_iris"]
    context_slice = db.get_context_graph(**context_action.arguments)
    assert status_column in {resource.iri for resource in context_slice.resources}

    assert status_value_type in pattern_action.arguments["map_implications"]
    assert value_type_action.arguments["object"] == status_value_type


def test_profile_type_assertion_leaves_value_type_promotion_lane_open(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    status_value_type = "https://example.test/project#StatusCodeValue"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        physical_type="rc:Varchar",
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Orders profile with an undefined project value type.",
        evidence_summary="Synthetic type-finding profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status looked integer-coded in the profile.",
                "physical_type": "rc:Integer",
                "value_type": status_value_type,
            }
        ],
    )
    profile = db.describe_profile_run(
        dataset,
        evidence,
    ).mapped_column_profile_observations[0]
    target_pattern = db.record_pattern(
        summary="Status code value needs vocabulary.",
        pattern_text=(
            "Status code value means the reviewed order lifecycle domain, not "
            "only the integer storage representation."
        ),
        rationale="The pattern and profile run share the same evidence.",
        pattern_targets=[status_value_type],
        supporting_observations=[profile.iri],
        evidence_iri=evidence,
    )
    implication_pattern = db.record_pattern(
        summary="Orders status profile implies a value type.",
        pattern_text=(
            "The Orders status profile implies a reusable project value type "
            "before status codes are promoted into current map assertions."
        ),
        rationale="The pattern and profile run share the same evidence.",
        pattern_targets=[status_column],
        supporting_observations=[profile.iri],
        evidence_iri=evidence,
        map_implications=[status_value_type],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)
    advisory = draft.type_advisories[0]
    value_type_plan = next(
        item
        for item in draft.advisory_followthrough_plan
        if item.semantic_move == "define_value_type"
    )
    value_type_action = [
        action
        for action in advisory.suggested_next_actions
        if action.tool_name == "stage_map_assertion_change"
        and action.arguments["predicate"] == "rc:valueType"
    ][0]
    value_type_args = dict(value_type_action.arguments)
    value_type_args["supporting_patterns"] = [
        target_pattern.pattern_iri,
        implication_pattern.pattern_iri,
    ]

    staged_assertion = db.stage_map_assertion_change(**value_type_args)
    review = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        tmp_path / "orders-profile-type-assertion-first.md",
    )

    candidate = next(
        candidate
        for candidate in review.candidates
        if candidate.revision_iri == staged_assertion.revision_iri
    )
    route_group = {
        group["route_group_key"]: group for group in candidate.profile_route_groups
    }[value_type_plan.route_group_key]
    assert route_group["match_strength"] == "direct_action"
    assert route_group["closed_semantic_moves"] == ["assert_map_type"]
    assert "define_value_type" in route_group["remaining_semantic_moves"]
    assert "caveat_fallback" in route_group["semantic_moves"]

    open_lanes = {
        lane.review_lane: lane for lane in review.open_profile_review_lanes
    }
    assert set(open_lanes) == {"profile_type_review"}
    assert open_lanes["profile_type_review"].route_group_keys == [
        value_type_plan.route_group_key
    ]
    assert open_lanes["profile_type_review"].closed_semantic_moves == [
        "assert_map_type"
    ]
    assert open_lanes["profile_type_review"].remaining_semantic_moves == [
        "define_value_type"
    ]
    assert review.closed_semantic_moves == ["assert_map_type"]
    assert review.remaining_semantic_moves == ["define_value_type"]


def test_profile_type_review_lane_is_representative_action_queue(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    channel_column = "https://example.test/project#OrdersChannel"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"

    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
    )
    db.record_map_column(
        channel_column,
        table_iri=dataset,
        column_name="channel",
        physical_type="rc:Varchar",
    )

    def record_repeated_type_profile() -> None:
        db.record_profile_bundle(
            dataset,
            dataset_summary="Orders were profiled without changing the map.",
            evidence_summary="Repeated multi-column type-finding profile run.",
            evidence_sources=["test://orders-profile"],
            shared_evidence_iri=evidence,
            update_map_snapshot=False,
            column_defaults={"update_map_column": False},
            column_profiles=[
                {
                    "column_iri": status_column,
                    "column_name": "status",
                    "summary": "Status looked varchar in the profile.",
                    "physical_type": "rc:Varchar",
                },
                {
                    "column_iri": channel_column,
                    "column_name": "channel",
                    "summary": "Channel looked integer-coded in the profile.",
                    "physical_type": "rc:Integer",
                },
            ],
        )

    record_repeated_type_profile()
    record_repeated_type_profile()

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.recommendation_count == 0
    assert draft.type_advisory_count == 4
    assert draft.representative_type_advisory_indexes == [0, 1]
    assert draft.type_advisory_status_counts == {
        "type_finding_missing_map_type": 2,
        "type_finding_conflicts_current_map": 2,
    }
    groups: dict[str, list[int]] = {}
    for index, advisory in enumerate(draft.type_advisories):
        assert advisory.type_advisory_index == index
        groups.setdefault(advisory.duplicate_group_key, []).append(index)
    assert len(groups) == 2

    for group_key, indexes in groups.items():
        group = [draft.type_advisories[index] for index in indexes]
        group_observations = {
            advisory.profile_observation_iri for advisory in group
        }
        for advisory in group:
            assert advisory.duplicate_group_key == group_key
            assert advisory.duplicate_count == 2
            assert advisory.duplicate_advisory_indexes == indexes
            assert set(advisory.duplicate_profile_observation_iris) == (
                group_observations
            )
            assert [
                action.tool_name for action in advisory.suggested_next_actions
            ] == [
                "get_context_graph",
                "record_pattern",
                "stage_systematisation",
                "stage_map_assertion_change",
            ]
            record_action = advisory.suggested_next_actions[1]
            stage_action = advisory.suggested_next_actions[3]
            assert set(record_action.arguments["supporting_observations"]) == (
                group_observations
            )
            assert set(stage_action.arguments["supporting_observations"]) == (
                group_observations
            )

    profile_type_actions = draft.suggested_next_action_groups["profile_type_review"]
    profile_type_labels = [action.action_label for action in profile_type_actions]
    assert profile_type_labels.count("Inspect profile type context") == 2
    assert profile_type_labels.count("Record type-finding pattern") == 2
    assert profile_type_labels.count("Stage type-finding fallback") == 2
    assert profile_type_labels.count("Stage physical type assertion") == 2
    assert [
        action.tool_name for action in profile_type_actions
    ] == [
        "get_context_graph",
        "record_pattern",
        "stage_systematisation",
        "stage_map_assertion_change",
        "get_context_graph",
        "record_pattern",
        "stage_systematisation",
        "stage_map_assertion_change",
    ]
    assert [
        action.source_profile_advisory["advisory_kind"]
        for action in profile_type_actions
    ] == ["profile_type_review"] * 8
    assert [
        action.source_profile_advisory["index_field"]
        for action in profile_type_actions
    ] == ["type_advisory_index"] * 8
    assert [
        action.source_profile_advisory["advisory_indexes"]
        for action in profile_type_actions
    ] == [[0, 2], [0, 2], [0, 2], [0, 2], [1, 3], [1, 3], [1, 3], [1, 3]]
    assert [
        action.source_profile_advisory["duplicate_advisory_indexes"]
        for action in profile_type_actions
    ] == [[0, 2], [0, 2], [0, 2], [0, 2], [1, 3], [1, 3], [1, 3], [1, 3]]


def test_query_storage_repair_profile_route_sources_close_query_lane(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/profile-query-repair#"
    dataset = f"{base}SupportEvents"
    evidence = f"{base}SupportEventsProfileEvidence"

    db.record_map_dataset(
        dataset,
        label="Support Events",
        is_table=True,
        row_count_snapshot=3,
        path_templates=["support_events/current.csv"],
    )
    db.record_map_physical_layout(
        f"{base}SupportEventsCsvLayout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
        datasets=[dataset],
    )
    db.record_profile_bundle(
        dataset,
        dataset_summary="Support events full profile pass.",
        evidence_summary="Support events profile evidence.",
        evidence_sources=["test://support-events/full"],
        shared_evidence_iri=evidence,
        sample_size=4,
        sample_scope="All rows in the local support events table.",
        sample_method="DuckDB full-table profile.",
        row_count=4,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
    )

    draft = db.draft_profile_map_updates(dataset, evidence)
    query_action = draft.suggested_next_action_groups["query_context_review"][0]
    assert query_action.source_query_context["blocking_issue_codes"] == [
        "missing_storage_access"
    ]

    repair = db.stage_query_storage_access_repair(
        dataset,
        f"{base}SupportEventsStorage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(tmp_path / "warehouse"),
        location_kind="directory",
        rationale="Reviewed local storage root for the profile/query interlock.",
        profile_route_sources=[query_action.source_query_context],
    )
    described = db.describe_staged_revision(repair.revision_iri)
    assert len(described.profile_route_sources) == 1
    stored_source = described.profile_route_sources[0]
    assert stored_source["review_lane"] == "query_context_review"
    assert stored_source["direct_review_lane"] == "query_context_review"
    assert stored_source["route_group_key"] == (
        query_action.source_query_context["route_group_key"]
    )
    assert stored_source["route_step_key"] == (
        query_action.source_query_context["route_step_key"]
    )

    review = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        tmp_path / "profile-query-repair-review.md",
        revision_iris=[repair.revision_iri],
    )

    assert review.candidate_revision_iris == [repair.revision_iri]
    candidate = review.candidates[0]
    assert candidate.semantic_apply_role == "query_context_repair_candidate"
    route_groups = {
        group["review_lane"]: group for group in candidate.profile_route_groups
    }
    assert route_groups["query_context_review"]["match_strength"] == (
        "direct_action"
    )
    assert all(
        lane.review_lane != "query_context_review"
        for lane in review.open_profile_review_lanes
    )
    assert review.executor_decision_summary["candidate_roles"] == {
        "query_context_repair_candidate": 1
    }


def test_query_storage_repair_profile_route_sources_preserve_sample_caution(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/profile-query-sample#"
    dataset = f"{base}Tickets"
    column = f"{base}TicketsStatus"
    evidence = f"{base}TicketsSampleProfileEvidence"

    db.record_map_dataset(
        dataset,
        label="Tickets",
        is_table=True,
        row_count_snapshot=1000,
        path_templates=["tickets/current/*.csv"],
    )
    db.record_map_physical_layout(
        f"{base}TicketsCsvLayout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByListingLayout",
        datasets=[dataset],
    )
    db.record_map_column(column, table_iri=dataset, column_name="status")
    db.record_profile_bundle(
        dataset,
        dataset_summary="Tickets sampled profile pass.",
        evidence_summary="Tickets sampled profile evidence.",
        evidence_sources=["test://tickets/sample"],
        shared_evidence_iri=evidence,
        sample_size=40,
        sample_scope="Sampled partition rows; not the full Tickets table.",
        sample_method="DuckDB sampled partition profile.",
        row_count=40,
        update_map_snapshot=False,
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": column,
                "column_name": "status",
                "summary": "Status contained nulls in the sample.",
                "null_count": 3,
            }
        ],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)
    assert draft.sampled_evidence_caution is not None
    query_action = draft.suggested_next_action_groups["query_context_review"][0]
    assert query_action.source_query_context["profile_quality_summary"] == (
        draft.profile_quality_summary
    )
    assert query_action.source_query_context["sampled_evidence_caution"] == (
        draft.sampled_evidence_caution
    )

    repair = db.stage_query_storage_access_repair(
        dataset,
        f"{base}TicketsStorage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(tmp_path / "warehouse"),
        location_kind="directory",
        rationale="Reviewed storage route for sampled-profile query context.",
        profile_route_sources=[query_action.source_query_context],
    )
    generic_path = tmp_path / "sampled-query-repair-staged-review.md"
    generic = db.export_staged_revisions([repair.revision_iri], generic_path)
    route_group = generic.revision_summaries[0].profile_route_groups[0]
    assert route_group["review_lane"] == "query_context_review"
    assert route_group["profile_quality_summaries"] == [
        draft.profile_quality_summary
    ]
    assert route_group["sampled_evidence_cautions"] == [
        draft.sampled_evidence_caution
    ]
    generic_text = generic_path.read_text(encoding="utf-8")
    assert "## Profile Route Bridge" in generic_text
    assert "Mechanical readiness is not full-scan evidence" in generic_text
    assert db.validate_graph(scope="all").conforms


def test_profile_helper_pattern_defaults_include_project_metric_implications(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"
    project_metric = "https://example.test/project#CompletenessScore"
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=100,
    )

    profile = db.record_dataset_profile(
        dataset,
        summary="Orders profile with an undefined project metric.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        evidence_iri=evidence,
        row_count=100,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": project_metric,
                "value": "0.99",
                "datatype": "xsd:decimal",
            }
        ],
        pattern_summary="Orders completeness score needs vocabulary.",
        pattern_text=(
            "The Orders profile uses a reusable completeness score that needs "
            "a project metric definition before comparison."
        ),
        pattern_rationale=(
            "The helper-created profile pattern should point at the dataset "
            "and the project metric kind it interprets."
        ),
    )

    assert profile.pattern is not None
    pattern_description = db.describe_pattern(profile.pattern.pattern_iri)
    assert {item.iri for item in pattern_description.map_implications} == {
        dataset,
        project_metric,
    }

    draft = db.draft_profile_map_updates(dataset, evidence)

    assert draft.recommendation_count == 0
    advisory = draft.metric_advisories[0]
    assert advisory.advisory_status == "project_metric_undefined"
    assert advisory.promotion_pattern_count == 1
    assert [item.iri for item in advisory.promotion_patterns] == [
        profile.pattern.pattern_iri
    ]
    assert "stage_pattern_promotion" in [
        action.tool_name for action in advisory.suggested_next_actions
    ]


def test_column_profile_helper_pattern_defaults_include_project_value_type_implication(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    status_value_type = "https://example.test/project#StatusCodeValue"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        physical_type="rc:Varchar",
    )

    profile = db.record_column_profile(
        status_column,
        table_iri=dataset,
        column_name="status",
        summary="Status profile observed a project value type.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        evidence_iri=evidence,
        physical_type="rc:Varchar",
        value_type=status_value_type,
        update_map_column=False,
        pattern_summary="Status code value needs vocabulary.",
        pattern_text=(
            "StatusCodeValue names the reviewed order lifecycle domain and "
            "needs a project value type definition before map assertion."
        ),
        pattern_rationale=(
            "The helper-created column pattern should point at the profiled "
            "column and the project value type it interprets."
        ),
    )

    assert profile.pattern is not None
    pattern_iri = profile.pattern.pattern_iri
    pattern_description = db.describe_pattern(pattern_iri)
    assert {item.iri for item in pattern_description.map_implications} == {
        status_column,
        status_value_type,
    }

    draft = db.draft_profile_map_updates(dataset, evidence)
    advisory = draft.type_advisories[0]
    assert advisory.promotion_pattern_count == 1
    assert [item.iri for item in advisory.promotion_patterns] == [pattern_iri]
    assert "stage_pattern_promotion" in [
        action.tool_name for action in advisory.suggested_next_actions
    ]
    assert "define_value_type" in {
        item.semantic_move for item in draft.advisory_followthrough_plan
    }


def test_profile_bundle_all_profiles_pattern_defaults_include_column_metrics(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#OrdersStatus"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"
    completeness_metric = "https://example.test/project#CompletenessScore"
    entropy_metric = "https://example.test/project#StatusEntropy"
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=100,
    )

    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders profile with project metric outputs.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        row_count=100,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": completeness_metric,
                "value": "0.99",
                "datatype": "xsd:decimal",
            }
        ],
        pattern_summary="Orders profile metrics need vocabulary.",
        pattern_text=(
            "The Orders profiling pass uses reusable completeness and entropy "
            "metrics that need project metric definitions."
        ),
        pattern_rationale=(
            "The bundle-level synthesis should point at every project metric "
            "kind it interprets across the profiled dataset and columns."
        ),
        pattern_support_scope="all_profiles",
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status values were profiled.",
                "profile_metrics": [
                    {
                        "metric": entropy_metric,
                        "value": "1.4",
                        "datatype": "xsd:decimal",
                    }
                ],
            }
        ],
    )

    assert bundle.dataset_profile.pattern is not None
    pattern_iri = bundle.dataset_profile.pattern.pattern_iri
    pattern_description = db.describe_pattern(pattern_iri)
    assert {item.iri for item in pattern_description.map_implications} == {
        dataset,
        completeness_metric,
        entropy_metric,
    }

    draft = db.draft_profile_map_updates(dataset, evidence)
    advisories_by_metric = {
        advisory.metric.iri: advisory for advisory in draft.metric_advisories
    }

    assert set(advisories_by_metric) == {completeness_metric, entropy_metric}
    for metric_iri, advisory in advisories_by_metric.items():
        assert advisory.advisory_status == "project_metric_undefined"
        assert advisory.promotion_pattern_count == 1
        assert [item.iri for item in advisory.promotion_patterns] == [
            pattern_iri
        ]
        promotion_actions = [
            action
            for action in advisory.suggested_next_actions
            if action.tool_name == "stage_pattern_promotion"
        ]
        assert len(promotion_actions) == 1
        assert promotion_actions[0].arguments["patterns"] == [pattern_iri]
        assert promotion_actions[0].arguments["anchors"] == [metric_iri]
        assert promotion_actions[0].arguments["evidence"] == [evidence]


def test_applied_metric_promotion_closes_profile_review_lane(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"
    project_metric = "https://example.test/project#CompletenessScore"
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        row_count_snapshot=100,
    )
    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders profile with an undefined project metric.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        row_count=100,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": project_metric,
                "value": "0.99",
                "datatype": "xsd:decimal",
            }
        ],
        column_defaults={"update_map_column": False},
    )
    pattern = db.record_pattern(
        summary="Orders completeness score is reusable metric vocabulary.",
        pattern_text=(
            "CompletenessScore is the share of records with complete required "
            "fields and should be typed as reusable profile metric vocabulary."
        ),
        rationale="The pattern and profile run share one evidence resource.",
        pattern_targets=[project_metric],
        supporting_observations=(
            bundle.handoff_entrypoints.profile_observation_iris
        ),
        evidence_iri=evidence,
        map_implications=[project_metric],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)
    promotion_action = next(
        action
        for action in draft.suggested_next_action_groups["metric_vocabulary_review"]
        if action.tool_name == "stage_pattern_promotion"
    )
    assert promotion_action.source_profile_advisory["advisory_statuses"] == [
        "project_metric_undefined",
    ]
    assert promotion_action.arguments["profile_route_sources"] == [
        promotion_action.source_profile_advisory
    ]
    staged_promotion = db.stage_pattern_promotion(**promotion_action.arguments)
    staged_iri = staged_promotion.staged_revisions[0].revision_iri
    staged_review = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        tmp_path / "orders-profile-metric-staged-review.md",
    )
    assert staged_review.candidate_revision_iris == [staged_iri]
    assert staged_review.open_profile_review_lanes == []
    assert staged_review.closed_semantic_moves == ["define_metric"]
    assert staged_review.remaining_semantic_moves == []
    assert any(
        group["review_lane"] == "metric_vocabulary_review"
        and group["match_strength"] == "direct_action"
        and group["closed_semantic_moves"] == ["define_metric"]
        and group["remaining_semantic_moves"] == ["caveat_fallback"]
        for group in staged_review.candidates[0].profile_route_groups
    )

    assert db.apply_staged_revision(staged_iri).patches_applied == 1

    rerun = db.draft_profile_map_updates(dataset, evidence)
    assert rerun.metric_advisory_status_counts == {
        "project_metric_defined": 1,
    }
    defined_action = rerun.suggested_next_action_groups[
        "metric_vocabulary_review"
    ][0]
    assert defined_action.source_profile_advisory["advisory_statuses"] == [
        "project_metric_defined",
    ]

    review = db.export_profile_insight_review_bundle(
        dataset,
        evidence,
        tmp_path / "orders-profile-metric-review.md",
    )

    assert review.candidate_revision_iris == [staged_iri]
    assert review.open_profile_review_lanes == []
    assert review.closed_semantic_moves == ["define_metric"]
    assert review.remaining_semantic_moves == []
    assert review.semantic_move_closure_summary == (
        "Closed semantic moves: define_metric. No semantic moves remain open "
        "in the live draft lanes."
    )
    candidate = review.candidates[0]
    assert any(
        group["review_lane"] == "metric_vocabulary_review"
        and group["match_strength"] == "direct_action"
        and group["closed_semantic_moves"] == ["define_metric"]
        and group["remaining_semantic_moves"] == []
        for group in candidate.profile_route_groups
    )
    exported = (tmp_path / "orders-profile-metric-review.md").read_text(
        encoding="utf-8"
    )
    assert "### Semantic Move Closure" in exported
    assert "Closed semantic moves: define_metric" in exported
    assert "### Open Profile Review Lanes" not in exported


def test_describe_profile_run_rejects_invalid_limit(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match="limit must be a positive integer"):
        db.describe_profile_run(
            "https://example.test/project#Orders",
            "https://example.test/project#ProfileEvidence",
            limit=0,
        )


def test_record_profile_bundle_rejects_unknown_column_fields(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match="unsupported record_column_profile"):
        db.record_profile_bundle(
            "https://example.test/project#Orders",
            dataset_summary="Orders were profiled.",
            column_profiles=[
                {
                    "column_iri": "https://example.test/project#OrdersStatus",
                    "column_name": "status",
                    "summary": "Status was profiled.",
                    "allowed_values": ["fulfilled"],
                }
            ],
        )

    assert _mutable_graph_counts(db) == before_counts
    assert db.search("Orders were profiled", graph="observations").matches == []


def test_record_profile_bundle_rejects_invalid_column_values_without_mutation(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(
        DoxaBaseError,
        match=(
            "column_profiles\\[0\\]\\.value_frequencies\\[0\\]\\.frequency"
        ),
    ):
        db.record_profile_bundle(
            "https://example.test/project#Orders",
            dataset_summary="Orders were profiled.",
            evidence_summary="Shared profiler run.",
            evidence_sources=["test://profile-run"],
            column_profiles=[
                {
                    "column_iri": "https://example.test/project#OrdersStatus",
                    "column_name": "status",
                    "summary": "Status was profiled.",
                    "value_frequencies": [
                        {"value": "fulfilled", "frequency": -1},
                    ],
                }
            ],
        )

    assert _mutable_graph_counts(db) == before_counts
    assert db.search("Orders were profiled", graph="observations").matches == []
    assert db.search("Shared profiler run", graph="evidence").matches == []


def test_record_profile_bundle_rejects_conflicting_shared_evidence_summary(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    shared_evidence = "https://example.test/project#OrdersProfileRunEvidence"
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match="conflicting evidence_summary"):
        db.record_profile_bundle(
            "https://example.test/project#Orders",
            dataset_summary="Orders were profiled.",
            evidence_summary="Dataset-level profiler run summary.",
            evidence_sources=["test://profile-run"],
            shared_evidence_iri=shared_evidence,
            column_profiles=[
                {
                    "column_iri": "https://example.test/project#OrdersStatus",
                    "column_name": "status",
                    "summary": "Status was profiled.",
                    "evidence_summary": "Column-level conflicting summary.",
                }
            ],
        )

    assert _mutable_graph_counts(db) == before_counts
    assert db.search("Orders were profiled", graph="observations").matches == []
    assert db.search("Dataset-level profiler run", graph="evidence").matches == []


@pytest.mark.parametrize(
    ("column_overrides", "match"),
    [
        (
            {"profile_metrics": [{"metric": "rc:MeanValue", "value": []}]},
            "column_profiles\\[0\\]\\.profile_metrics\\[0\\]\\.value",
        ),
        (
            {"profile_metrics": [{"metric": "rc:MinValue", "value": 1}]},
            "column_profiles\\[0\\]\\.profile_metrics\\[0\\]\\.metric",
        ),
        ({"physical_type": "plain physical type"}, "physical_type"),
        ({"value_type": "plain value type"}, "value_type"),
        ({"table_iri": "plain table name"}, "table_iri"),
        ({"pattern_summary": "Status looks categorical."}, "provided together"),
        (
            {
                "pattern_summary": "Status looks categorical.",
                "pattern_text": "Status has a small observed domain.",
                "pattern_rationale": "The profiler saw only a few statuses.",
                "pattern_map_implications": ["plain implication"],
            },
            "pattern_map_implications",
        ),
    ],
)
def test_record_profile_bundle_preflights_column_validation_without_mutation(
    tmp_path: Path,
    column_overrides: dict[str, object],
    match: str,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_counts = _mutable_graph_counts(db)
    column_profile = {
        "column_iri": "https://example.test/project#OrdersStatus",
        "column_name": "status",
        "summary": "Status was profiled.",
        **column_overrides,
    }

    with pytest.raises(DoxaBaseError, match=match):
        db.record_profile_bundle(
            "https://example.test/project#Orders",
            dataset_summary="Orders were profiled.",
            evidence_summary="Shared profiler run.",
            evidence_sources=["test://profile-run"],
            column_profiles=[column_profile],
        )

    assert _mutable_graph_counts(db) == before_counts
    assert db.search("Orders were profiled", graph="observations").matches == []
    assert db.search("Shared profiler run", graph="evidence").matches == []

