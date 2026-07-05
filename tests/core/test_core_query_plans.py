"""Split from test_doxabase_core.py (distillation Phase 2); tests verbatim."""

from tests.core.support_core import *  # noqa: F401,F403


def test_draft_query_plan_returns_review_gated_duckdb_plan(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    plan = db.draft_query_plan(
        "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"
    )

    assert plan.helper == "describe_query_context(plan_candidate=...)"
    assert plan.mode == "non_executed_review_draft"
    assert plan.handoff_kind == "metadata_review_required"
    assert plan.engine.name == "duckdb"
    assert plan.source_context.api == "DoxaBase.describe_query_context"
    assert plan.source_context.readiness == "needs_review"
    assert plan.source_context.selected_candidate_index == 0
    assert plan.source_context.query_target_decision.status == (
        "candidate_needs_review"
    )
    assert plan.selected_candidate is not None
    assert plan.selected_candidate.template_source == "partition_scheme"
    assert plan.scan.function == "read_parquet"
    assert plan.scan.uri_template == (
        "s3://ais-noaa/broadcasts/{year}/ais-{date}.parquet"
    )
    assert plan.scan.file_format == "Parquet"
    assert plan.scan.compression == "zstd"
    assert plan.scan.candidate_path_status == "orientation_only"
    assert plan.scan.template_source == "partition_scheme"
    assert plan.scan.template_source_resource is not None
    assert plan.scan.template_source_resource.iri == (
        "https://richcanopy.org/example/manifest/ais#daily_date_partition"
    )
    assert plan.scan.template_source_verification_status is not None
    assert plan.scan.template_source_verification_status.iri == (
        RC + "GeneratedFromManifestLayout"
    )
    assert plan.scan.template_source_verification_note is not None
    assert "verify against storage listing" in (
        plan.scan.template_source_verification_note
    )
    assert plan.scan.template_lineage is not None
    assert "partition_scheme daily_date_partition" in plan.scan.template_lineage
    assert plan.required_bindings == ["year", "date"]
    assert [binding.name for binding in plan.binding_requirements] == [
        "year",
        "date",
    ]
    assert plan.binding_requirements[0].source == "path_template_placeholder"
    assert plan.binding_requirements[0].source_text == (
        "s3://ais-noaa/broadcasts/{year}/ais-{date}.parquet"
    )
    assert plan.binding_requirements[0].required is True
    assert plan.binding_requirements[0].derivation_status == "not_inferred"
    assert "has not inferred" in plan.binding_requirements[0].derivation_note
    year_binding, date_binding = plan.binding_requirements
    assert year_binding.binding_kind == "partition_template_placeholder"
    assert year_binding.partition_scheme is not None
    assert year_binding.partition_scheme.iri == (
        "https://richcanopy.org/example/manifest/ais#daily_date_partition"
    )
    assert year_binding.partition_column is None
    assert year_binding.partition_granularity is not None
    assert year_binding.partition_granularity.iri == RC + "Daily"
    assert year_binding.candidate_column_matches == []
    assert year_binding.candidate_column_match_status == "none"
    assert date_binding.binding_kind == "partition_template_placeholder"
    assert date_binding.partition_scheme is not None
    assert date_binding.partition_scheme.iri == (
        "https://richcanopy.org/example/manifest/ais#daily_date_partition"
    )
    assert date_binding.partition_column is not None
    assert date_binding.partition_column.iri == (
        "https://richcanopy.org/example/manifest/ais#bc_date"
    )
    assert date_binding.partition_column.column_name == "date"
    assert date_binding.partition_granularity is not None
    assert date_binding.partition_granularity.iri == RC + "Daily"
    assert date_binding.candidate_column_matches == []
    assert date_binding.candidate_column_match_status == "not_applicable"
    assert "likely partition column date" in date_binding.derivation_note
    assert "partition scheme granularity" in date_binding.derivation_note
    assert "partition granularity" not in date_binding.derivation_note
    assert plan.storage_environment.bucket_name == "ais-noaa"
    assert plan.storage_environment.endpoint_profile == "local-minio"
    assert plan.storage_environment.credential_reference == "profile:ais-readonly"
    assert plan.storage_environment.path_style_access is True
    assert plan.storage_environment.runtime_resolution_required is True
    assert plan.storage_environment.duckdb_settings_from_context == [
        "s3_url_style=path",
        "s3_region=local",
    ]
    assert plan.review_gate.executable_without_review is False
    assert plan.review_gate.binding_values_required is True
    assert plan.review_gate.status == "candidate_needs_review"
    assert plan.review_gate.blocking_reason_codes == ["layout_needs_verification"]
    assert plan.review_gate.all_issue_codes == [
        "layout_needs_verification",
        "verification_status_not_recorded",
    ]
    assert plan.review_gate.reason_codes == ["layout_needs_verification"]
    assert any(issue.code == "layout_needs_verification" for issue in plan.issues)
    assert plan.caveats
    assert "not executable code" in plan.planning_notes[-1]


def test_draft_query_plan_carries_dataset_template_verification(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    root = tmp_path / "warehouse"
    dataset = "https://example.test/project#LocalEvents"
    template = str(root / "events/date={date}/part-*.parquet")
    verification_note = "Complete absolute path template matched the scratch layout."
    storage = db.record_map_storage_access(
        "https://example.test/project#local_events_storage",
        label="Local events storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(root),
        location_kind="directory",
        access_mode="rc:ReadOnlyAccess",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#local_events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Local events",
        is_table=True,
        path_templates=[template],
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByListingLayout",
        layout_verification_note=verification_note,
    )

    plan = db.draft_query_plan(dataset)

    assert plan.selected_candidate is not None
    assert plan.selected_candidate.template_source == "dataset"
    assert plan.scan.template_source == "dataset"
    assert plan.scan.template_source_resource is not None
    assert plan.scan.template_source_resource.iri == dataset
    assert plan.scan.template_source_verification_status is not None
    assert plan.scan.template_source_verification_status.iri == (
        RC + "VerifiedByListingLayout"
    )
    assert plan.scan.template_source_verification_note == verification_note
    assert plan.scan.dataset_verification_status is not None
    assert plan.scan.dataset_verification_status.iri == (
        RC + "VerifiedByListingLayout"
    )
    assert plan.scan.dataset_verification_note == verification_note
    assert plan.scan.template_lineage is not None
    assert "dataset Local events" in plan.scan.template_lineage
    assert verification_note in plan.scan.template_lineage
    date_column = "https://example.test/project#local_events__event_date"
    db.record_map_column(
        date_column,
        table_iri=dataset,
        column_name="event_date",
        physical_type="rc:Date",
    )
    plan = db.draft_query_plan(dataset)
    date_binding = plan.binding_requirements[0]
    assert date_binding.name == "date"
    assert len(date_binding.candidate_column_matches) == 1
    date_match = date_binding.candidate_column_matches[0]
    assert date_match.column.iri == date_column
    assert date_match.column.column_name == "event_date"
    assert date_match.match_kind == "suffix_name"
    assert date_match.matched_field == "column_name"
    assert date_match.matched_value == "event_date"
    assert date_match.confidence == "medium"
    assert date_binding.candidate_column_match_status == "single"
    assert "Candidate column hint(s): event_date" in date_binding.derivation_note
    assert plan.handoff_kind == "binding_values_required"
    assert plan.review_gate.executable_without_review is True
    assert plan.review_gate.binding_values_required is True
    assert plan.review_gate.ready_for_execution_attempt is False
    assert plan.review_gate.execution_attempt_blocking_reason_codes == [
        "binding_values_required",
    ]
    assert (
        plan.review_gate.primary_execution_attempt_blocking_reason_code
        == "binding_values_required"
    )
    assert plan.scan.execution_attempt_ready is False
    assert (
        plan.scan.primary_execution_attempt_blocking_reason_code
        == "binding_values_required"
    )
    assert plan.scan.execution_attempt_blocking_reason_codes == [
        "binding_values_required",
    ]


def test_draft_query_plan_hints_unmatched_partition_placeholders(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#PartitionOwnedEvents"
    event_date = "https://example.test/project#partition_events__event_date"
    event_year = "https://example.test/project#partition_events__year"
    event_home_region = "https://example.test/project#partition_events__home_region"
    event_ship_region = "https://example.test/project#partition_events__ship_region"
    storage = db.record_map_storage_access(
        "https://example.test/project#partition_events_storage",
        label="Partition events storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/warehouse",
        location_kind="directory",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#partition_events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    partition = db.record_map_partition_scheme(
        "https://example.test/project#partition_events_daily_partition",
        path_template="events/year={year}/region={region}/dt={date}/*.parquet",
        partition_columns=[event_date],
        granularity="rc:Daily",
        datasets=[dataset],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Partition-owned events",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    db.record_map_column(
        event_date,
        table_iri=dataset,
        column_name="event_date",
        physical_type="rc:Date",
    )
    db.record_map_column(
        event_year,
        table_iri=dataset,
        column_name="year",
        physical_type="rc:Integer",
    )
    db.record_map_column(
        event_home_region,
        table_iri=dataset,
        column_name="home_region",
    )
    db.record_map_column(
        event_ship_region,
        table_iri=dataset,
        column_name="ship_region",
    )

    context = db.describe_query_context(dataset)
    plan = db.draft_query_plan(dataset)

    query_action = next(
        action
        for action in context.suggested_next_actions
        if action.tool == "doxabase.describe_query_context"
        and "plan_candidate" in action.args
    )

    assert plan.selected_candidate is not None
    assert plan.selected_candidate.template_source == "partition_scheme"
    bindings_by_name = {
        binding.name: binding for binding in plan.binding_requirements
    }
    year_binding = bindings_by_name["year"]
    assert year_binding.binding_kind == "partition_template_placeholder"
    assert year_binding.partition_scheme is not None
    assert year_binding.partition_scheme.iri == partition.iri
    assert year_binding.partition_column is None
    assert year_binding.candidate_column_match_status == "single"
    assert [match.column.iri for match in year_binding.candidate_column_matches] == [
        event_year
    ]
    assert year_binding.candidate_column_matches[0].match_kind == "exact_name"
    assert year_binding.candidate_column_matches[0].confidence == "high"
    assert "Candidate column hint(s): year" in year_binding.derivation_note

    region_binding = bindings_by_name["region"]
    assert region_binding.binding_kind == "partition_template_placeholder"
    assert region_binding.partition_column is None
    assert region_binding.candidate_column_match_status == "ambiguous"
    assert [match.column.iri for match in region_binding.candidate_column_matches] == [
        event_home_region,
        event_ship_region,
    ]
    assert {
        match.match_kind for match in region_binding.candidate_column_matches
    } == {"suffix_name"}
    assert "Candidate column hint(s): home_region, ship_region" in (
        region_binding.derivation_note
    )
    assert "Multiple candidate columns matched this placeholder" in (
        region_binding.derivation_note
    )

    date_binding = bindings_by_name["date"]
    assert date_binding.partition_column is not None
    assert date_binding.partition_column.iri == event_date
    assert date_binding.candidate_column_matches == []
    assert date_binding.candidate_column_match_status == "not_applicable"


def test_draft_query_plan_hints_storage_template_placeholder_columns(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#HourlyEvents"
    event_date = "https://example.test/project#hourly_events__event_date"
    event_hour = "https://example.test/project#hourly_events__event_hour"
    storage = db.record_map_storage_access(
        "https://example.test/project#hourly_events_storage",
        label="Hourly events storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/warehouse",
        location_kind="directory",
        path_templates=[
            "events/event_date={event_date}/event_hour={event_hour}/*.parquet"
        ],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#hourly_events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Hourly events",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    db.record_map_column(
        event_date,
        table_iri=dataset,
        column_name="event_date",
        physical_type="rc:Date",
    )
    db.record_map_column(
        event_hour,
        table_iri=dataset,
        column_name="event_hour",
        physical_type="rc:Integer",
    )

    plan = db.draft_query_plan(dataset)

    assert plan.selected_candidate is not None
    assert plan.selected_candidate.template_source == "storage_access"
    assert plan.handoff_kind == "binding_values_required"
    assert plan.required_bindings == ["event_date", "event_hour"]
    matches_by_name = {
        binding.name: binding.candidate_column_matches
        for binding in plan.binding_requirements
    }
    statuses_by_name = {
        binding.name: binding.candidate_column_match_status
        for binding in plan.binding_requirements
    }
    assert [match.column.iri for match in matches_by_name["event_date"]] == [
        event_date
    ]
    assert matches_by_name["event_date"][0].match_kind == "exact_name"
    assert matches_by_name["event_date"][0].confidence == "high"
    assert statuses_by_name["event_date"] == "single"
    assert [match.column.iri for match in matches_by_name["event_hour"]] == [
        event_hour
    ]
    assert matches_by_name["event_hour"][0].match_kind == "exact_name"
    assert statuses_by_name["event_hour"] == "single"
    assert "Candidate column hint(s): event_date" in (
        plan.binding_requirements[0].derivation_note
    )


def test_draft_query_plan_marks_ambiguous_binding_column_matches(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#TenantEvents"
    db.record_map_dataset(
        dataset,
        label="Tenant events",
        is_table=True,
        path_templates=["events/tenant={tenant}/batch={batch}/*.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    billing_tenant = "https://example.test/project#tenant_events__billing_tenant"
    source_tenant = "https://example.test/project#tenant_events__source_tenant"
    db.record_map_column(
        billing_tenant,
        table_iri=dataset,
        column_name="billing_tenant",
    )
    db.record_map_column(
        source_tenant,
        table_iri=dataset,
        column_name="source_tenant",
    )

    plan = db.draft_query_plan(dataset)

    bindings_by_name = {
        binding.name: binding
        for binding in plan.binding_requirements
    }
    tenant_binding = bindings_by_name["tenant"]
    assert tenant_binding.candidate_column_match_status == "ambiguous"
    assert [match.column.iri for match in tenant_binding.candidate_column_matches] == [
        billing_tenant,
        source_tenant,
    ]
    assert all(
        match.match_kind == "suffix_name"
        for match in tenant_binding.candidate_column_matches
    )
    assert "Multiple candidate columns matched this placeholder" in (
        tenant_binding.derivation_note
    )
    assert bindings_by_name["batch"].candidate_column_match_status == "none"
    assert bindings_by_name["batch"].candidate_column_matches == []


def test_missing_storage_existing_candidates_expose_route_intent_indexes(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WarehouseOrders"
    archive = db.record_map_storage_access(
        "https://example.test/project#warehouse_orders_archive_storage",
        label="Warehouse orders archive",
        route_roles=["rc:ArchiveRoute"],
        storage_protocol="rc:S3CompatibleStorage",
        access_mode="rc:ReadOnlyAccess",
        storage_root="s3://archive/warehouse/orders",
        endpoint_profile="archive-minio",
        credential_reference="profile:archive-readonly",
        region="eu-west-2",
        path_style_access=True,
        layout_verification_status="rc:VerifiedByListingLayout",
        layout_verification_note="Reviewed archive listing.",
    )
    current = db.record_map_storage_access(
        "https://example.test/project#warehouse_orders_current_storage",
        label="Warehouse orders current",
        route_roles=["rc:ProductionRoute", "rc:CurrentRoute"],
        storage_protocol="rc:DatabaseStorage",
        storage_root="warehouse-prod",
        path_templates=["mart.orders_current"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(dataset, label="Warehouse orders", is_table=True)

    context = db.describe_query_context(dataset)
    missing_storage = next(
        issue for issue in context.issues if issue.code == "missing_storage_access"
    )

    assert missing_storage.details is not None
    repair_hint = missing_storage.details["repair_hint"]
    candidates = repair_hint["candidate_existing_storage_accesses"]
    candidate_iris = [candidate["storage_access_iri"] for candidate in candidates]
    archive_index = candidate_iris.index(archive.iri)
    current_index = candidate_iris.index(current.iri)
    archive_candidate = candidates[archive_index]
    assert archive_candidate["access_mode"]["iri"] == RC + "ReadOnlyAccess"
    assert archive_candidate["endpoint_profile"] == "archive-minio"
    assert archive_candidate["credential_reference"] == "profile:archive-readonly"
    assert archive_candidate["region"] == "eu-west-2"
    assert archive_candidate["path_style_access"] is True
    assert archive_candidate["layout_verification_note"] == "Reviewed archive listing."
    assert repair_hint[
        "candidate_existing_storage_access_route_intent_preferred_indexes"
    ] == [current_index]
    assert repair_hint[
        "first_candidate_existing_storage_access_route_intent_preferred_index"
    ] == current_index
    assert archive_index in repair_hint[
        "candidate_existing_storage_access_route_intent_caution_indexes"
    ]
    assert "CurrentRoute" in repair_hint[
        "candidate_existing_storage_access_route_intent_note"
    ]
    repair_group = context.suggested_repair_action_groups[0]
    assert repair_group.repair_context[
        "first_candidate_existing_storage_access_route_intent_preferred_index"
    ] == current_index


def test_describe_query_context_summarizes_fixture_target_candidates(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    db.import_trig(POLYMARKET_FIXTURE)

    tables = db.list_entities(type="rc:Table", graph="map", limit=20).entities
    assert len(tables) == 7
    seen_sources: set[str] = set()

    for table in tables:
        context = db.describe_query_context(table.iri)

        assert context.query_target_candidates
        for target in context.query_target_candidates:
            seen_sources.add(target.template_source)
            assert target.template_source in {
                "dataset",
                "partition_scheme",
                "storage_access",
            }
            assert target.source_resource.iri
            assert target.storage_access is not None
            assert target.candidate_path is not None
            assert "data/parquet/data/parquet" not in target.candidate_path
            assert "s3://ais-noaa/ais-noaa" not in target.candidate_path
            assert target.review_required is any(
                reason.severity in {"error", "warning"}
                for reason in target.review_reasons
            )

    assert {"dataset", "partition_scheme"} <= seen_sources


def test_query_target_candidates_surface_global_blockers(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    local_storage = db.record_map_storage_access(
        "https://example.test/project#orders_z_local_storage",
        label="Orders local access",
        route_roles=["rc:SampleRoute"],
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/warehouse",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    archive_storage = db.record_map_storage_access(
        "https://example.test/project#orders_zz_archive_storage",
        label="Orders archive local access",
        route_roles=["rc:ProductionRoute", "rc:CurrentRoute"],
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/warehouse-archive",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    stale_storage = db.record_map_storage_access(
        "https://example.test/project#orders_a_stale_s3_storage",
        label="Orders stale S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        bucket_name="old-orders",
        key_prefix="orders",
        credential_reference="profile:old-orders",
        layout_verification_status="rc:ContradictedLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#orders_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        path_templates=["orders/dt={date}.parquet"],
        storage_accesses=[local_storage.iri, archive_storage.iri, stale_storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "blocked_by_contradiction"
    local_index = next(
        index
        for index, target in enumerate(context.query_target_candidates)
        if target.storage_access is not None
        and target.storage_access.iri == local_storage.iri
    )
    local_target = next(
        target
        for target in context.query_target_candidates
        if target.storage_access is not None
        and target.storage_access.iri == local_storage.iri
    )
    archive_index = next(
        index
        for index, target in enumerate(context.query_target_candidates)
        if target.storage_access is not None
        and target.storage_access.iri == archive_storage.iri
    )
    archive_target = context.query_target_candidates[archive_index]
    assert local_target.review_required is True
    assert local_target.direct_review_required is False
    assert local_target.direct_review_reasons == []
    assert any(
        reason.code == "query_context_has_other_blockers"
        and reason.severity == "error"
        for reason in local_target.review_reasons
    )
    stale_index = next(
        index
        for index, target in enumerate(context.query_target_candidates)
        if target.storage_access is not None
        and target.storage_access.iri == stale_storage.iri
    )
    stale_target = next(
        target
        for target in context.query_target_candidates
        if target.storage_access is not None
        and target.storage_access.iri == stale_storage.iri
    )
    assert stale_index < local_index
    assert any(
        reason.code == "contradicted_layout"
        for reason in stale_target.review_reasons
    )
    assert stale_target.direct_review_required is True
    assert any(
        reason.code == "contradicted_layout"
        for reason in stale_target.direct_review_reasons
    )
    assert context.query_target_decision.status == "context_blocked"
    assert context.query_target_decision.candidate_index == local_index
    assert context.query_target_decision.candidate_path == local_target.candidate_path
    assert context.query_target_decision.candidate_path_status == "orientation_only"
    assert context.query_target_decision.direct_review_required is False
    assert context.query_target_decision.selected_candidate_direct_clean is True
    assert context.query_target_decision.reason_codes == [
        "query_context_has_other_blockers"
    ]
    assert context.query_target_decision.route_intent_review_candidate_indexes == [
        archive_index
    ]
    assert context.query_target_decision.route_intent_caution is not None
    assert "production/current/canonical route role intent" in (
        context.query_target_decision.route_intent_caution
    )
    assert context.query_target_decision.selection_caution == (
        context.query_target_decision.route_intent_caution
    )
    assert "route_intent_review_candidates_present" in (
        context.query_target_decision.selection_reason_codes
    )
    assert context.ready_candidate_indexes == []
    assert context.unselected_ready_candidate_indexes == []
    assert context.direct_clean_candidate_indexes == [
        local_index,
        archive_index,
    ]
    assert context.unselected_direct_clean_candidate_indexes == [archive_index]
    assert len(context.suggested_next_actions) == 2
    query_action = context.suggested_next_actions[0]
    local_selector = local_target.candidate_selector
    archive_selector = archive_target.candidate_selector
    assert query_action.tool == "doxabase.describe_query_context"
    assert "plan_candidate" in query_action.args
    assert query_action.args == {
        "iri": dataset,
        "plan_candidate": local_selector,
        "allow_context_blocked_candidate": True,
    }
    assert (
        f"Other direct-clean candidate indexes exist ({archive_index})"
        in query_action.reason
    )
    peer_action = context.suggested_next_actions[1]
    assert peer_action.tool == "doxabase.describe_query_context"
    assert "plan_candidate" in peer_action.args
    assert peer_action.args == {
        "iri": dataset,
        "plan_candidate": archive_selector,
        "allow_context_blocked_candidate": True,
    }
    assert "peer candidate has no direct warning or error" in peer_action.reason
    plan = db.draft_query_plan(dataset)
    assert plan.handoff_kind == "context_review_required"
    assert plan.source_context.selection_mode == "automatic"
    assert plan.source_context.requested_candidate_index is None
    assert plan.source_context.requested_storage_access_iri is None
    assert plan.source_context.selection_status == "automatic"
    assert plan.source_context.allow_context_blocked_candidate is False
    assert plan.source_context.ready_candidate_indexes == []
    assert plan.source_context.unselected_ready_candidate_indexes == []
    assert plan.source_context.direct_clean_candidate_indexes == [
        local_index,
        archive_index,
    ]
    assert plan.source_context.unselected_direct_clean_candidate_indexes == [
        archive_index
    ]
    assert plan.source_context.route_intent_review_candidate_indexes == [
        archive_index
    ]
    assert plan.source_context.route_intent_caution == (
        context.query_target_decision.route_intent_caution
    )
    assert plan.handoff_summary.route_intent_review_candidate_indexes == [
        archive_index
    ]
    assert plan.review_gate.selection_overridden is False
    assert plan.review_gate.context_blocked_candidate_allowed is False
    assert plan.review_gate.context_blocked_candidate_used is False
    assert plan.review_gate.direct_blocking_reason_codes == []
    assert plan.review_gate.context_blocking_reason_codes == [
        "query_context_has_other_blockers"
    ]
    assert plan.selected_candidate is not None
    assert plan.selected_candidate.candidate_path_status == "orientation_only"
    context_blocker = next(
        reason
        for reason in plan.selected_candidate.review_reasons
        if reason.code == "query_context_has_other_blockers"
    )
    assert context_blocker.details == {
        "excluded_blocker_count": 1,
        "excluded_blocker_codes": ["contradicted_layout"],
        "excluded_blocker_resource_iris": [stale_storage.iri],
    }

    automatic_allowed_plan = db.draft_query_plan(
        dataset,
        allow_context_blocked_candidate=True,
    )
    assert automatic_allowed_plan.handoff_kind == "context_review_required"
    assert automatic_allowed_plan.source_context.selection_mode == "automatic"
    assert automatic_allowed_plan.source_context.requested_candidate_index is None
    assert automatic_allowed_plan.source_context.allow_context_blocked_candidate is True
    assert (
        automatic_allowed_plan.review_gate.context_blocked_candidate_allowed is True
    )
    assert automatic_allowed_plan.review_gate.context_blocked_candidate_used is False
    assert automatic_allowed_plan.review_gate.selection_overridden is False
    assert automatic_allowed_plan.review_gate.direct_blocking_reason_codes == []
    assert automatic_allowed_plan.review_gate.context_blocking_reason_codes == [
        "query_context_has_other_blockers"
    ]
    assert automatic_allowed_plan.review_gate.blocking_reason_codes == [
        "query_context_has_other_blockers"
    ]
    assert automatic_allowed_plan.scan.uri_template is not None
    assert automatic_allowed_plan.scan.execution_attempt_ready is False
    assert automatic_allowed_plan.scan.execution_attempt_blocking_reason_codes == (
        automatic_allowed_plan.review_gate.execution_attempt_blocking_reason_codes
    )

    allowed_plan = db.draft_query_plan(
        dataset,
        candidate_index=local_index,
        allow_context_blocked_candidate=True,
    )
    assert allowed_plan.source_context.query_target_decision.status == (
        "context_blocked"
    )
    assert allowed_plan.source_context.selected_candidate_index == local_index
    assert allowed_plan.source_context.selection_mode == "candidate_index"
    assert allowed_plan.source_context.requested_candidate_index == local_index
    assert allowed_plan.source_context.selection_status == "matched"
    assert allowed_plan.source_context.allow_context_blocked_candidate is True
    assert "Selected candidate" in allowed_plan.source_context.selected_candidate_note
    assert "direct-clean binding values required" in (
        allowed_plan.source_context.selected_candidate_note
    )
    assert "contradicted_layout" in (
        allowed_plan.source_context.selected_candidate_note
    )
    assert "review_gate.all_issue_codes" in (
        allowed_plan.source_context.selected_candidate_note
    )
    assert allowed_plan.source_context.direct_clean_candidate_indexes == [
        local_index,
        archive_index,
    ]
    assert allowed_plan.source_context.unselected_direct_clean_candidate_indexes == [
        archive_index
    ]
    assert allowed_plan.source_context.route_intent_review_candidate_indexes == [
        archive_index
    ]
    assert allowed_plan.handoff_summary.route_intent_review_candidate_indexes == [
        archive_index
    ]
    assert allowed_plan.selected_candidate is not None
    assert allowed_plan.selected_candidate.storage_access is not None
    assert allowed_plan.selected_candidate.storage_access.iri == local_storage.iri
    assert allowed_plan.selected_candidate.candidate_path_status == "ready"
    assert allowed_plan.selected_candidate.review_required is False
    assert allowed_plan.selected_candidate.review_reasons == []
    assert allowed_plan.scan.candidate_path_status == "ready"
    assert allowed_plan.review_gate.status == "ready"
    assert allowed_plan.review_gate.selection_overridden is True
    assert allowed_plan.review_gate.context_blocked_candidate_allowed is True
    assert allowed_plan.review_gate.context_blocked_candidate_used is True
    assert allowed_plan.review_gate.direct_blocking_reason_codes == []
    assert allowed_plan.review_gate.context_blocking_reason_codes == [
        "query_context_has_other_blockers"
    ]
    assert allowed_plan.review_gate.blocking_reason_codes == []
    assert allowed_plan.review_gate.executable_without_review is True
    assert allowed_plan.review_gate.binding_values_required is True
    assert allowed_plan.review_gate.ready_for_execution_attempt is False
    assert allowed_plan.review_gate.execution_attempt_blocking_reason_codes == [
        "binding_values_required",
    ]
    assert allowed_plan.scan.execution_attempt_ready is False
    assert allowed_plan.scan.execution_attempt_blocking_reason_codes == [
        "binding_values_required",
    ]
    assert allowed_plan.handoff_kind == "binding_values_required"

    storage_selected_plan = db.draft_query_plan(
        dataset,
        storage_access_iri=local_storage.iri,
        allow_context_blocked_candidate=True,
    )
    assert storage_selected_plan.source_context.selection_mode == (
        "storage_access_iri"
    )
    assert storage_selected_plan.source_context.requested_storage_access_iri == (
        local_storage.iri
    )
    assert storage_selected_plan.source_context.selected_candidate_index == local_index
    assert storage_selected_plan.handoff_kind == "binding_values_required"

    direct_bad_plan = db.draft_query_plan(dataset, candidate_index=stale_index)
    assert direct_bad_plan.selected_candidate is not None
    assert direct_bad_plan.selected_candidate.storage_access is not None
    assert direct_bad_plan.selected_candidate.storage_access.iri == stale_storage.iri
    assert direct_bad_plan.review_gate.selection_overridden is True
    assert direct_bad_plan.review_gate.status == "candidate_needs_review"
    assert direct_bad_plan.review_gate.direct_blocking_reason_codes == [
        "contradicted_layout",
        "storage_protocol_location_mismatch",
    ]
    assert direct_bad_plan.review_gate.blocking_reason_codes == [
        "contradicted_layout",
        "storage_protocol_location_mismatch",
    ]


def test_draft_query_plan_rejects_ambiguous_or_invalid_candidate_selection(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_storage",
        label="Orders local access",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/warehouse",
        path_templates=[
            "orders/current/dt={date}.parquet",
            "orders/archive/dt={date}.parquet",
        ],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#orders_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.query_target_decision.candidate_index == 0
    assert context.query_target_decision.peer_ready_requires_intent_review is True
    assert "peer_ready_candidates_present" in (
        context.query_target_decision.selection_reason_codes
    )
    assert "automatic_candidate_rank" in (
        context.query_target_decision.selection_reason_codes
    )
    assert context.query_target_decision.selection_caution is not None
    assert "candidate_selector" in context.query_target_decision.selection_caution
    assert "Automatic selection uses DoxaBase precedence" in (
        context.query_target_decision.selection_caution
    )
    assert context.ready_candidate_indexes == [0, 1]
    assert context.unselected_ready_candidate_indexes == [1]
    assert "Other direct-ready candidate indexes exist (1)" in (
        context.suggested_next_actions[0].reason
    )
    selectors = [
        candidate.candidate_selector for candidate in context.query_target_candidates
    ]
    assert len(selectors) == len(set(selectors)) == 2
    assert all(selector.startswith("query-target:") for selector in selectors)
    assert context.suggested_next_actions[1].args == {
        "iri": dataset,
        "plan_candidate": selectors[1],
    }

    automatic_plan = db.draft_query_plan(dataset)

    assert automatic_plan.source_context.selected_candidate_index == 0
    assert automatic_plan.source_context.selected_candidate_selector == selectors[0]
    assert automatic_plan.source_context.requested_candidate_selector is None
    assert automatic_plan.source_context.candidate_count == 2
    assert automatic_plan.source_context.ready_candidate_indexes == [0, 1]
    assert automatic_plan.source_context.unselected_ready_candidate_indexes == [1]
    assert automatic_plan.source_context.peer_ready_requires_intent_review is True
    assert automatic_plan.source_context.selection_caution == (
        context.query_target_decision.selection_caution
    )
    assert "peer_ready_candidates_present" in (
        automatic_plan.source_context.selection_reason_codes
    )
    assert automatic_plan.handoff_summary.peer_ready_requires_intent_review is True
    assert automatic_plan.handoff_summary.selected_candidate_selector == selectors[0]
    assert automatic_plan.handoff_summary.selection_caution == (
        automatic_plan.source_context.selection_caution
    )

    explicit_plan = db.draft_query_plan(dataset, candidate_index=1)

    assert explicit_plan.source_context.selected_candidate_index == 1
    assert explicit_plan.source_context.selected_candidate_selector == selectors[1]
    assert explicit_plan.source_context.requested_candidate_selector is None
    assert explicit_plan.source_context.candidate_count == 2
    assert explicit_plan.source_context.ready_candidate_indexes == [0, 1]
    assert explicit_plan.source_context.unselected_ready_candidate_indexes == [0]
    assert explicit_plan.source_context.direct_clean_candidate_indexes == [0, 1]
    assert explicit_plan.source_context.unselected_direct_clean_candidate_indexes == [
        0
    ]
    assert explicit_plan.source_context.peer_ready_requires_intent_review is True
    assert "explicit_candidate_index_selection" in (
        explicit_plan.source_context.selection_reason_codes
    )
    assert "peer_ready_candidates_present" in (
        explicit_plan.source_context.selection_reason_codes
    )
    assert explicit_plan.source_context.selection_caution is not None
    assert "Explicit candidate_index selection used the caller selector" in (
        explicit_plan.source_context.selection_caution
    )
    assert explicit_plan.handoff_summary.peer_ready_requires_intent_review is True
    assert explicit_plan.handoff_summary.selection_caution == (
        explicit_plan.source_context.selection_caution
    )

    selector_plan = db.draft_query_plan(dataset, candidate_selector=selectors[1])

    assert selector_plan.source_context.selection_mode == "candidate_selector"
    assert selector_plan.source_context.selected_candidate_index == 1
    assert selector_plan.source_context.selected_candidate_selector == selectors[1]
    assert selector_plan.source_context.requested_candidate_selector == selectors[1]
    assert selector_plan.source_context.requested_candidate_index is None
    assert selector_plan.source_context.requested_storage_access_iri is None
    assert "explicit_candidate_selector_selection" in (
        selector_plan.source_context.selection_reason_codes
    )
    assert selector_plan.selected_candidate is not None
    assert selector_plan.selected_candidate.candidate_selector == selectors[1]
    assert selector_plan.selected_candidate.template == (
        context.query_target_candidates[1].template
    )
    assert selector_plan.handoff_summary.selected_candidate_selector == selectors[1]

    with pytest.raises(DoxaBaseError, match="Pass only one explicit"):
        db.draft_query_plan(
            dataset,
            candidate_index=0,
            storage_access_iri=storage.iri,
        )
    with pytest.raises(DoxaBaseError, match="Pass only one explicit"):
        db.draft_query_plan(
            dataset,
            candidate_index=0,
            candidate_selector=selectors[0],
        )
    with pytest.raises(DoxaBaseError, match="candidate_index must point"):
        db.draft_query_plan(dataset, candidate_index=2)
    with pytest.raises(DoxaBaseError, match="candidate_index must point"):
        db.draft_query_plan(dataset, candidate_index=-1)
    with pytest.raises(DoxaBaseError, match="candidate_selector must not be empty"):
        db.draft_query_plan(dataset, candidate_selector=" ")
    with pytest.raises(DoxaBaseError, match="candidate_selector did not match"):
        db.draft_query_plan(dataset, candidate_selector="query-target:missing")
    with pytest.raises(DoxaBaseError, match="did not match any"):
        db.draft_query_plan(
            dataset,
            storage_access_iri="https://example.test/project#missing_storage",
        )
    with pytest.raises(DoxaBaseError, match="matched multiple") as excinfo:
        db.draft_query_plan(dataset, storage_access_iri=storage.iri)
    error = str(excinfo.value)
    assert "candidate 0" in error
    assert "candidate_path=" in error
    assert "candidate 1" in error
    assert "candidate_selector=" in error
    assert "/warehouse/orders/current/dt={date}.parquet" in error
    assert "/warehouse/orders/archive/dt={date}.parquet" in error
    assert "template_source=storage_access" in error
    assert "storage='Orders local access'" in error
    assert "Pass candidate_selector for a stable selection" in error
    with pytest.raises(
        DoxaBaseError,
        match="physical_layout_iri was matched",
    ) as layout_excinfo:
        db.draft_query_plan(
            dataset,
            storage_access_iri=storage.iri,
            physical_layout_iri=layout.iri,
        )
    layout_error = str(layout_excinfo.value)
    assert "storage_access_iri still identifies multiple query target candidates" in (
        layout_error
    )
    assert "candidate_selector for the stable path/relation" in layout_error


def test_query_context_suggests_overlay_for_blocked_candidate_query_evidence(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        layout_verification_status="rc:CandidateLayout",
    )
    result = db.record_query_result(
        summary="Orders query was blocked before the reviewed CSV was bundled.",
        observed_asset=dataset,
        execution_status="blocked",
        engine="duckdb",
        query_source_path=str(tmp_path / "orders_status.sql"),
        result_sources=["stderr://missing-orders-csv"],
        scanned_source_paths=["warehouse/orders.csv"],
        failure_summary="The reviewed CSV was absent from this capsule.",
    )

    context = db.describe_query_context(dataset)

    assert "layout_needs_verification" in {issue.code for issue in context.issues}
    overlay_actions = [
        action
        for action in context.suggested_next_actions
        if (action.tool, action.args.get("kind"), action.args.get("dry_run")) == ("doxabase.stage_revision", "query_evidence_overlay", True)
    ]
    assert len(overlay_actions) == 1
    overlay_action = overlay_actions[0]
    assert overlay_action.args["spec"]["evidence_iri"] == result.evidence_iri


def test_object_root_candidate_stays_visible_with_partition_templates(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    event_date = db.record_map_column(
        "https://example.test/project#orders__event_date",
        column_name="event_date",
        table_iri=dataset,
    )
    storage_root = str(tmp_path / "orders.parquet")
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_local_storage",
        label="Orders exact object storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="object",
        storage_root=storage_root,
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#orders_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    partition = db.record_map_partition_scheme(
        "https://example.test/project#orders_daily_partition",
        path_template="orders/event_date={event_date}/*.parquet",
        partition_columns=[event_date.iri],
        granularity="rc:Daily",
        layout_verification_status="rc:VerifiedByListingLayout",
        datasets=[dataset],
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        columns=[event_date.iri],
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "needs_review"
    assert {issue.code for issue in context.issues} == {
        "storage_object_location_has_path_template"
    }
    root_target = next(
        target
        for target in context.query_target_candidates
        if target.template_source == "storage_access_location"
    )
    assert root_target.source_resource.iri == storage.iri
    assert root_target.candidate_path == storage_root
    assert root_target.candidate_path_status == "ready"
    assert root_target.review_required is False
    assert root_target.direct_review_required is False
    partition_target = next(
        target
        for target in context.query_target_candidates
        if target.source_resource.iri == partition.iri
    )
    assert partition_target.candidate_path == (
        f"{storage_root}/orders/event_date={{event_date}}/*.parquet"
    )
    assert partition_target.candidate_path_status == "orientation_only"
    assert partition_target.review_required is True
    assert partition_target.direct_review_required is True
    assert [reason.code for reason in partition_target.direct_review_reasons] == [
        "storage_object_location_has_path_template"
    ]
    assert context.query_target_decision.status == "ready"
    assert context.query_target_decision.candidate_path == storage_root
    assert context.ready_candidate_indexes == [
        context.query_target_decision.candidate_index
    ]
    assert context.suggested_next_actions[0].args == {
        "iri": dataset,
        "plan_candidate": root_target.candidate_selector,
        "allow_context_blocked_candidate": True,
    }

    automatic_plan = db.draft_query_plan(dataset)

    assert automatic_plan.handoff_kind == "context_review_required"
    assert automatic_plan.review_gate.context_blocked_candidate_used is False

    suggested_kwargs = dict(context.suggested_next_actions[0].args)
    suggested_kwargs["candidate_selector"] = suggested_kwargs.pop("plan_candidate")
    plan = db.draft_query_plan(**suggested_kwargs)

    assert plan.selected_candidate is not None
    assert plan.selected_candidate.template_source == "storage_access_location"
    assert plan.scan.uri_template == storage_root
    assert plan.review_gate.context_blocked_candidate_used is True
    assert plan.review_gate.ready_for_execution_attempt is True
    assert plan.handoff_summary.ready_for_execution_attempt is True
    assert plan.handoff_summary.context_blocked_candidate_allowed is True
    assert plan.handoff_summary.context_blocked_candidate_used is True
    assert plan.handoff_summary.direct_blocking_reason_codes == []
    assert plan.handoff_summary.context_blocking_reason_codes == [
        "query_context_has_other_blockers"
    ]
    assert plan.handoff_summary.all_issue_codes == [
        "storage_object_location_has_path_template"
    ]
    assert plan.handoff_kind == "execution_attempt_ready"


def test_draft_query_plan_blocks_selected_layout_path_extension_mismatch(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage_root = str(tmp_path / "orders.csv")
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_local_storage",
        label="Orders local object",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="object",
        storage_root=storage_root,
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    csv_layout = db.record_map_physical_layout(
        "https://example.test/project#orders_csv_layout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    parquet_layout = db.record_map_physical_layout(
        "https://example.test/project#orders_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[csv_layout.iri, parquet_layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)
    target = context.query_target_candidates[0]
    selection_actions = [
        action
        for action in context.suggested_next_actions
        if action.tool == "doxabase.describe_query_context"
        and "plan_candidate" in action.args
        and "physical_layout_iri" in action.args
    ]

    assert [issue.code for issue in context.issues] == ["ambiguous_physical_layout"]
    assert [action.args for action in selection_actions] == [
        {
            "iri": dataset,
            "plan_candidate": target.candidate_selector,
            "physical_layout_iri": csv_layout.iri,
        }
    ]

    csv_plan = db.draft_query_plan(
        dataset,
        physical_layout_iri=csv_layout.iri,
    )

    assert csv_plan.scan.function == "read_csv_auto"
    assert csv_plan.review_gate.ready_for_execution_attempt is True
    assert csv_plan.handoff_kind == "execution_attempt_ready"

    parquet_plan = db.draft_query_plan(
        dataset,
        physical_layout_iri=parquet_layout.iri,
    )

    assert parquet_plan.scan.function == "read_parquet"
    assert parquet_plan.scan.physical_layout is not None
    assert parquet_plan.scan.physical_layout.iri == parquet_layout.iri
    assert parquet_plan.selected_candidate is not None
    assert parquet_plan.selected_candidate.candidate_path_status == "orientation_only"
    assert parquet_plan.selected_candidate.direct_review_required is True
    assert [issue.code for issue in parquet_plan.issues] == [
        "physical_layout_path_extension_mismatch"
    ]
    mismatch = parquet_plan.issues[0]
    assert mismatch.details is not None
    assert mismatch.details["physical_layout_selection_basis"] == "caller_selected"
    assert mismatch.details["path_extension_format"] == "csv"
    assert mismatch.details["physical_layout_format_kind"] == "parquet"
    assert parquet_plan.review_gate.ready_for_execution_attempt is False
    assert parquet_plan.review_gate.blocking_reason_codes == [
        "physical_layout_path_extension_mismatch"
    ]
    assert parquet_plan.handoff_kind == "metadata_review_required"


def test_draft_query_plan_layout_selection_preserves_other_blockers(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Feeds"
    storage = db.record_map_storage_access(
        "https://example.test/project#feeds_https_storage",
        label="Feeds HTTPS access",
        storage_protocol="rc:HTTPSStorage",
        storage_root="https://cdn.example.test/lake",
        path_templates=[
            "feeds/clean/date={date}.parquet",
            "s3://wrong-bucket/feeds/*.parquet",
        ],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    csv_layout = db.record_map_physical_layout(
        "https://example.test/project#feeds_csv_layout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    parquet_layout = db.record_map_physical_layout(
        "https://example.test/project#feeds_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Feeds",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[csv_layout.iri, parquet_layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)
    clean_index = next(
        index
        for index, target in enumerate(context.query_target_candidates)
        if target.template == "feeds/clean/date={date}.parquet"
    )
    clean_selector = context.query_target_candidates[clean_index].candidate_selector

    assert context.readiness == "needs_review"
    assert {issue.code for issue in context.issues} == {
        "ambiguous_physical_layout",
        "storage_protocol_location_mismatch",
    }
    selection_actions = [
        action
        for action in context.suggested_next_actions
        if action.tool == "doxabase.describe_query_context"
        and "plan_candidate" in action.args
        and "physical_layout_iri" in action.args
    ]
    assert [action.args for action in selection_actions] == [
        {
            "iri": dataset,
            "plan_candidate": clean_selector,
            "physical_layout_iri": parquet_layout.iri,
            "allow_context_blocked_candidate": True,
        },
    ]
    assert "allow_context_blocked_candidate=True" in selection_actions[0].reason

    selected_plan = db.draft_query_plan(
        dataset,
        candidate_index=clean_index,
        physical_layout_iri=parquet_layout.iri,
    )

    assert selected_plan.source_context.requested_physical_layout_iri == (
        parquet_layout.iri
    )
    assert selected_plan.scan.physical_layout is not None
    assert selected_plan.scan.physical_layout.iri == parquet_layout.iri
    assert selected_plan.scan.function == "read_parquet"
    assert [issue.code for issue in selected_plan.issues] == [
        "storage_protocol_location_mismatch"
    ]
    assert "ambiguous_physical_layout" not in (
        selected_plan.review_gate.all_issue_codes
    )
    assert selected_plan.review_gate.status == "ready"
    assert selected_plan.review_gate.executable_without_review is False
    assert selected_plan.review_gate.direct_blocking_reason_codes == []
    assert selected_plan.review_gate.context_blocking_reason_codes == [
        "query_context_has_other_blockers"
    ]
    assert selected_plan.review_gate.blocking_reason_codes == [
        "query_context_has_other_blockers"
    ]
    assert selected_plan.review_gate.binding_values_required is True
    assert selected_plan.review_gate.ready_for_execution_attempt is False
    assert selected_plan.review_gate.execution_attempt_blocking_reason_codes == [
        "query_context_has_other_blockers",
        "binding_values_required",
    ]
    assert (
        selected_plan.review_gate.primary_execution_attempt_blocking_reason_code
        == "query_context_has_other_blockers"
    )
    assert (
        selected_plan.scan.primary_execution_attempt_blocking_reason_code
        == "query_context_has_other_blockers"
    )
    assert selected_plan.scan.execution_attempt_blocking_reason_codes == (
        selected_plan.review_gate.execution_attempt_blocking_reason_codes
    )
    assert selected_plan.scan.execution_attempt_ready is False
    assert selected_plan.handoff_kind == "context_review_required"

    selected_from_action_kwargs = dict(selection_actions[0].args)
    selected_from_action_kwargs["candidate_selector"] = (
        selected_from_action_kwargs.pop("plan_candidate")
    )
    selected_from_action = db.draft_query_plan(**selected_from_action_kwargs)

    assert selected_from_action.source_context.allow_context_blocked_candidate is True
    assert selected_from_action.review_gate.context_blocked_candidate_allowed is True
    assert selected_from_action.review_gate.context_blocked_candidate_used is True
    assert selected_from_action.review_gate.status == "ready"
    assert selected_from_action.review_gate.blocking_reason_codes == []
    assert selected_from_action.review_gate.context_blocking_reason_codes == [
        "query_context_has_other_blockers"
    ]
    assert selected_from_action.review_gate.binding_values_required is True
    assert selected_from_action.review_gate.execution_attempt_blocking_reason_codes == [
        "binding_values_required",
    ]
    assert (
        selected_from_action.review_gate.primary_execution_attempt_blocking_reason_code
        == "binding_values_required"
    )
    assert (
        selected_from_action.scan.primary_execution_attempt_blocking_reason_code
        == "binding_values_required"
    )
    assert selected_from_action.scan.execution_attempt_blocking_reason_codes == [
        "binding_values_required",
    ]
    assert selected_from_action.handoff_kind == "binding_values_required"


def test_draft_query_plan_layout_selection_preserves_runtime_resolution_gate(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    storage = db.record_map_storage_access(
        "https://example.test/project#events_s3_storage",
        label="Events S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        bucket_name="events-lake",
        key_prefix="warehouse",
        endpoint_profile="minio-prod",
        credential_reference="profile:events-readonly",
        path_templates=["events/current/*.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    csv_layout = db.record_map_physical_layout(
        "https://example.test/project#events_csv_layout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    parquet_layout = db.record_map_physical_layout(
        "https://example.test/project#events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Events",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[csv_layout.iri, parquet_layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "needs_review"
    assert {issue.code for issue in context.issues} == {
        "ambiguous_physical_layout",
    }

    selected_plan = db.draft_query_plan(
        dataset,
        physical_layout_iri=parquet_layout.iri,
    )

    assert selected_plan.issues == []
    assert selected_plan.scan.function == "read_parquet"
    assert selected_plan.review_gate.status == "ready"
    assert selected_plan.review_gate.executable_without_review is True
    assert selected_plan.review_gate.blocking_reason_codes == []
    assert selected_plan.review_gate.all_issue_codes == []
    assert selected_plan.review_gate.runtime_resolution_required is True
    assert selected_plan.storage_environment.runtime_resolution_required is True
    assert selected_plan.review_gate.ready_for_execution_attempt is False
    assert selected_plan.scan.execution_attempt_ready is False
    assert selected_plan.review_gate.execution_attempt_blocking_reason_codes == [
        "runtime_resolution_required",
    ]
    assert (
        selected_plan.review_gate.primary_execution_attempt_blocking_reason_code
        == "runtime_resolution_required"
    )
    assert selected_plan.scan.execution_attempt_blocking_reason_codes == [
        "runtime_resolution_required",
    ]
    assert (
        selected_plan.scan.primary_execution_attempt_blocking_reason_code
        == "runtime_resolution_required"
    )
    assert selected_plan.handoff_kind == "runtime_resolution_required"


def test_draft_query_plan_review_gates_database_backed_table_without_scan_function(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#VerifiedEvents"
    storage = db.record_map_storage_access(
        "https://example.test/project#verified_events_database_storage",
        label="Verified events database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="analytics-prod",
        path_templates=["public.verified_events"],
        endpoint_profile="warehouse-prod",
        credential_reference="profile:warehouse-readonly",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#verified_events_table_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Verified events",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "ready_for_query_planning"
    assert context.query_target_decision.status == "ready"
    assert context.query_target_decision.candidate_path == "public.verified_events"
    assert context.query_target_decision.reason_codes == []
    target = context.query_target_candidates[0]
    assert target.candidate_path == "public.verified_events"
    assert target.relation_identifier == "public.verified_events"
    assert target.connection_reference == "analytics-prod"
    assert target.composition == "database_connection_and_relation"

    plan = db.draft_query_plan(dataset)

    assert plan.selected_candidate is not None
    assert plan.selected_candidate.candidate_path == "public.verified_events"
    assert plan.selected_candidate.relation_identifier == "public.verified_events"
    assert plan.selected_candidate.connection_reference == "analytics-prod"
    assert plan.scan.function is None
    assert plan.scan.uri_template is None
    assert plan.scan.relation_identifier == "public.verified_events"
    assert plan.scan.connection_reference == "analytics-prod"
    assert plan.scan.composition == "database_connection_and_relation"
    assert "database endpoint profile" in (
        plan.storage_environment.runtime_resolution_note
    )
    assert "connection, schema, table, or source access" in (
        plan.storage_environment.runtime_resolution_note
    )
    assert plan.review_gate.executable_without_review is True
    assert plan.review_gate.ready_for_execution_attempt is False
    assert plan.review_gate.blocking_reason_codes == []
    assert plan.review_gate.execution_attempt_blocking_reason_codes == [
        "runtime_resolution_required",
    ]
    assert (
        plan.review_gate.primary_execution_attempt_blocking_reason_code
        == "runtime_resolution_required"
    )
    assert plan.scan.execution_attempt_ready is False
    assert plan.scan.execution_attempt_blocking_reason_codes == [
        "runtime_resolution_required",
    ]
    assert (
        plan.scan.primary_execution_attempt_blocking_reason_code
        == "runtime_resolution_required"
    )
    assert plan.review_gate.reason_codes == []
    assert plan.handoff_kind == "database_relation_handoff"
    assert "Selected candidate 0 is a direct-clean database relation handoff" in (
        plan.source_context.selected_candidate_note
    )
    assert "scan_function_not_inferred" not in (
        plan.source_context.selected_candidate_note
    )


def test_explicit_clean_candidate_can_ignore_sibling_database_template_mismatch(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#MixedEvents"
    dataset_template = "events/current/*.parquet"
    partition_template = "events/dt={date}/*.parquet"
    database_storage = db.record_map_storage_access(
        "https://example.test/project#mixed_events_database_storage",
        label="Mixed events database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="analytics-prod",
        path_templates=["mart.mixed_events"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    local_storage = db.record_map_storage_access(
        "https://example.test/project#mixed_events_local_storage",
        label="Mixed events local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="directory",
        storage_root=str(tmp_path / "lake"),
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#mixed_events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    event_date = db.record_map_column(
        "https://example.test/project#mixed_events__event_date",
        column_name="event_date",
        table_iri=dataset,
    )
    partition = db.record_map_partition_scheme(
        "https://example.test/project#mixed_events_partition_scheme",
        label="Mixed events file partitioning",
        path_template=partition_template,
        partition_columns=[event_date.iri],
        granularity="rc:Daily",
        layout_verification_status="rc:VerifiedByQueryLayout",
        datasets=[dataset],
    )
    db.record_map_dataset(
        dataset,
        label="Mixed events",
        is_table=True,
        path_templates=[dataset_template],
        storage_accesses=[database_storage.iri, local_storage.iri],
        physical_layouts=[layout.iri],
        columns=[event_date.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "ready_for_query_planning"
    assert context.query_target_decision.status == "ready"
    assert context.issues == []
    assert context.suggested_repair_action_group_count == 0
    assert context.suggested_repair_action_groups == []
    local_partition_index, local_partition = next(
        (index, target)
        for index, target in enumerate(context.query_target_candidates)
        if target.template_source == "partition_scheme"
        and target.storage_access is not None
        and target.storage_access.iri == local_storage.iri
    )
    database_relation_index = next(
        index
        for index, target in enumerate(context.query_target_candidates)
        if target.template_source == "storage_access"
        and target.storage_access is not None
        and target.storage_access.iri == database_storage.iri
    )
    assert local_partition.source_resource.iri == partition.iri
    assert local_partition.candidate_path_status == "ready"
    assert local_partition.direct_review_required is False
    assert local_partition.review_reasons == []
    assert context.ready_candidate_indexes == [
        context.query_target_decision.candidate_index,
        local_partition_index,
        database_relation_index,
    ]
    assert context.unselected_ready_candidate_indexes == [
        local_partition_index,
        database_relation_index,
    ]
    assert context.direct_clean_candidate_indexes == context.ready_candidate_indexes
    assert context.unselected_direct_clean_candidate_indexes == (
        context.unselected_ready_candidate_indexes
    )
    assert context.suggested_next_actions[0].tool == "doxabase.describe_query_context"
    assert "plan_candidate" in context.suggested_next_actions[0].args
    assert context.suggested_next_actions[0].args == {
        "iri": dataset,
        "plan_candidate": context.query_target_candidates[
            context.query_target_decision.candidate_index
        ].candidate_selector,
    }
    assert {
        action.tool.removeprefix("doxabase.") for action in context.suggested_next_actions
    } == {"describe_query_context"}
    assert all(
        "plan_candidate" in action.args for action in context.suggested_next_actions
    )
    peer_actions = context.suggested_next_actions[1:]
    assert [action.args for action in peer_actions] == [
        {
            "iri": dataset,
            "plan_candidate": local_partition.candidate_selector,
        },
        {
            "iri": dataset,
            "plan_candidate": context.query_target_candidates[
                database_relation_index
            ].candidate_selector,
        },
    ]
    assert all(
        "also direct-ready" in action.reason
        for action in peer_actions
    )

    partition_plan = db.draft_query_plan(
        dataset,
        candidate_index=local_partition_index,
    )

    assert partition_plan.handoff_kind == "binding_values_required"
    assert partition_plan.review_gate.context_blocked_candidate_used is False
    assert partition_plan.review_gate.context_blocking_reason_codes == []
    assert partition_plan.review_gate.blocking_reason_codes == []
    assert partition_plan.review_gate.executable_without_review is True
    assert partition_plan.review_gate.binding_values_required is True

    peer_action_kwargs = dict(peer_actions[0].args)
    peer_action_kwargs["candidate_selector"] = peer_action_kwargs.pop("plan_candidate")
    peer_action_plan = db.draft_query_plan(**peer_action_kwargs)

    assert peer_action_plan.review_gate.context_blocked_candidate_used is False
    assert peer_action_plan.review_gate.blocking_reason_codes == []
    assert peer_action_plan.handoff_kind == "binding_values_required"

    automatic_plan = db.draft_query_plan(dataset)

    assert automatic_plan.handoff_kind == "execution_attempt_ready"
    assert automatic_plan.source_context.selection_mode == "automatic"
    assert automatic_plan.source_context.allow_context_blocked_candidate is False
    assert automatic_plan.review_gate.context_blocked_candidate_used is False
    assert automatic_plan.review_gate.blocking_reason_codes == []
    assert automatic_plan.review_gate.ready_for_execution_attempt is True

    automatic_allowed_plan = db.draft_query_plan(
        dataset,
        allow_context_blocked_candidate=True,
    )

    assert automatic_allowed_plan.handoff_kind == "execution_attempt_ready"
    assert automatic_allowed_plan.source_context.selection_mode == "automatic"
    assert automatic_allowed_plan.source_context.selected_candidate_index == (
        context.query_target_decision.candidate_index
    )
    assert automatic_allowed_plan.review_gate.context_blocked_candidate_allowed is True
    assert automatic_allowed_plan.review_gate.context_blocked_candidate_used is False
    assert automatic_allowed_plan.review_gate.direct_blocking_reason_codes == []
    assert automatic_allowed_plan.review_gate.context_blocking_reason_codes == []
    assert automatic_allowed_plan.review_gate.blocking_reason_codes == []

    allowed_plan = db.draft_query_plan(
        dataset,
        candidate_index=local_partition_index,
        allow_context_blocked_candidate=True,
    )

    assert allowed_plan.selected_candidate is not None
    assert allowed_plan.selected_candidate.storage_access is not None
    assert allowed_plan.selected_candidate.storage_access.iri == local_storage.iri
    assert allowed_plan.selected_candidate.template_source == "partition_scheme"
    assert allowed_plan.selected_candidate.candidate_path_status == "ready"
    assert allowed_plan.selected_candidate.review_required is False
    assert allowed_plan.source_context.selected_candidate_index == local_partition_index
    assert allowed_plan.source_context.selection_mode == "candidate_index"
    assert allowed_plan.source_context.allow_context_blocked_candidate is True
    assert allowed_plan.review_gate.context_blocked_candidate_allowed is True
    assert allowed_plan.review_gate.context_blocked_candidate_used is False
    assert allowed_plan.review_gate.direct_blocking_reason_codes == []
    assert allowed_plan.review_gate.context_blocking_reason_codes == []
    assert allowed_plan.review_gate.all_issue_codes == []
    assert allowed_plan.review_gate.blocking_reason_codes == []
    assert allowed_plan.review_gate.executable_without_review is True
    assert allowed_plan.review_gate.binding_values_required is True
    assert allowed_plan.review_gate.ready_for_execution_attempt is False
    assert allowed_plan.required_bindings == ["date"]
    assert len(allowed_plan.binding_requirements) == 1
    date_binding = allowed_plan.binding_requirements[0]
    assert date_binding.binding_kind == "partition_template_placeholder"
    assert date_binding.partition_scheme is not None
    assert date_binding.partition_scheme.iri == partition.iri
    assert date_binding.partition_column is not None
    assert date_binding.partition_column.iri == event_date.iri
    assert date_binding.partition_column.column_name == "event_date"
    assert date_binding.partition_granularity is not None
    assert date_binding.partition_granularity.iri == RC + "Daily"
    assert "likely partition column event_date" in date_binding.derivation_note
    assert "partition scheme granularity" in date_binding.derivation_note
    assert allowed_plan.handoff_kind == "binding_values_required"


def test_query_target_candidates_expose_storage_route_roles(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    sample_storage = db.record_map_storage_access(
        "https://example.test/project#aaa_orders_sample_storage",
        label="Orders sample relation",
        route_roles=["rc:SampleRoute"],
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-dev",
        path_templates=["scratch.orders_sample"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    production_storage = db.record_map_storage_access(
        "https://example.test/project#zzz_orders_production_storage",
        label="Orders production relation",
        route_roles=["rc:ProductionRoute", "rc:CurrentRoute"],
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        path_templates=["mart.orders_current"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    table_layout = db.record_map_physical_layout(
        "https://example.test/project#orders_table_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        storage_accesses=[sample_storage.iri, production_storage.iri],
        physical_layouts=[table_layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    sample_candidate = next(
        candidate
        for candidate in context.query_target_candidates
        if candidate.storage_access is not None
        and candidate.storage_access.iri == sample_storage.iri
    )
    production_candidate = next(
        candidate
        for candidate in context.query_target_candidates
        if candidate.storage_access is not None
        and candidate.storage_access.iri == production_storage.iri
    )
    sample_access = next(
        access for access in context.storage_accesses if access.iri == sample_storage.iri
    )
    assert [role.iri for role in sample_access.route_roles] == [
        RC + "SampleRoute"
    ]
    assert [role.label for role in sample_candidate.route_roles] == ["sample route"]
    assert [role.iri for role in production_candidate.route_roles] == [
        RC + "CurrentRoute",
        RC + "ProductionRoute",
    ]
    assert context.query_target_decision.candidate_index is not None
    automatic_candidate = context.query_target_candidates[
        context.query_target_decision.candidate_index
    ]
    assert automatic_candidate.storage_access is not None
    assert automatic_candidate.storage_access.iri == sample_storage.iri
    assert context.query_target_decision.peer_ready_requires_intent_review is True
    assert context.query_target_decision.route_intent_review_candidate_indexes == [
        context.query_target_candidates.index(production_candidate)
    ]
    assert context.query_target_decision.route_intent_caution is not None
    assert "production/current/canonical route role intent" in (
        context.query_target_decision.route_intent_caution
    )
    assert "route_intent_review_candidates_present" in (
        context.query_target_decision.selection_reason_codes
    )
    assert any(
        action.tool == "doxabase.describe_query_context"
        and "plan_candidate" in action.args
        and action.args.get("plan_candidate")
        == production_candidate.candidate_selector
        for action in context.suggested_next_actions
    )

    production_plan = db.draft_query_plan(
        dataset,
        candidate_selector=production_candidate.candidate_selector,
    )

    assert production_plan.handoff_kind == "database_relation_handoff"
    assert production_plan.selected_candidate is not None
    assert production_plan.selected_candidate.route_roles == production_candidate.route_roles
    assert production_plan.source_context.selection_mode == "candidate_selector"
    assert production_plan.source_context.route_intent_review_candidate_indexes == []
    assert production_plan.handoff_summary.route_intent_review_candidate_indexes == []


def test_query_target_candidate_template_warnings_do_not_bleed_to_siblings(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    storage = db.record_map_storage_access(
        "https://example.test/project#events_local_storage",
        label="Events local access",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/warehouse",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    partition = db.record_map_partition_scheme(
        "https://example.test/project#events_verified_partition",
        label="Verified event partition",
        path_template="events/good/dt={date}.parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
        datasets=[dataset],
    )
    db.record_map_dataset(
        dataset,
        label="Events",
        is_table=True,
        path_templates=["s3://remote-bucket/events/bad/*.parquet"],
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "needs_review"
    assert any(
        issue.code == "storage_protocol_location_mismatch"
        and issue.resource is not None
        and issue.resource.iri == storage.iri
        and "path template from Events" in issue.message
        for issue in context.issues
    )

    dataset_target = next(
        target
        for target in context.query_target_candidates
        if target.template_source == "dataset"
    )
    assert dataset_target.candidate_path == "s3://remote-bucket/events/bad/*.parquet"
    assert dataset_target.candidate_path_status == "orientation_only"
    assert dataset_target.review_required is True
    assert dataset_target.direct_review_required is True
    assert any(
        reason.code == "storage_protocol_location_mismatch"
        and "path template from Events" in reason.message
        for reason in dataset_target.direct_review_reasons
    )

    partition_target = next(
        target
        for target in context.query_target_candidates
        if target.source_resource.iri == partition.iri
    )
    assert partition_target.candidate_path == "/warehouse/events/good/dt={date}.parquet"
    assert partition_target.candidate_path_status == "ready"
    assert partition_target.review_required is False
    assert partition_target.review_reasons == []
    assert partition_target.direct_review_required is False
    assert partition_target.direct_review_reasons == []


def test_query_target_candidates_scope_partition_blockers(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    storage = db.record_map_storage_access(
        "https://example.test/project#events_local_storage",
        label="Events local access",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/warehouse",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    verified_partition = db.record_map_partition_scheme(
        "https://example.test/project#events_verified_partition",
        label="Verified event partition",
        path_template="events/good/dt={date}.parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
        datasets=[dataset],
    )
    contradicted_partition = db.record_map_partition_scheme(
        "https://example.test/project#events_stale_partition",
        label="Stale event partition",
        path_template="events/stale/dt={date}.parquet",
        layout_verification_status="rc:ContradictedLayout",
        datasets=[dataset],
    )
    db.record_map_dataset(
        dataset,
        label="Events",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "blocked_by_contradiction"
    verified_target = next(
        target
        for target in context.query_target_candidates
        if target.source_resource.iri == verified_partition.iri
    )
    assert any(
        reason.code == "query_context_has_other_blockers"
        for reason in verified_target.review_reasons
    )
    assert verified_target.direct_review_required is False
    assert verified_target.direct_review_reasons == []
    assert not any(
        reason.code == "contradicted_layout"
        for reason in verified_target.review_reasons
    )

    contradicted_target = next(
        target
        for target in context.query_target_candidates
        if target.source_resource.iri == contradicted_partition.iri
    )
    assert any(
        reason.code == "contradicted_layout"
        for reason in contradicted_target.review_reasons
    )
    assert contradicted_target.direct_review_required is True
    assert any(
        reason.code == "contradicted_layout"
        for reason in contradicted_target.direct_review_reasons
    )

