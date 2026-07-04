"""Split from test_doxabase_core.py (distillation Phase 2); tests verbatim."""

from tests.core.support_core import *  # noqa: F401,F403


def test_context_slice_skips_query_context_action_for_non_tabular_seed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    api = "https://example.test/project#RiskSignalsAPI"
    storage = "https://example.test/project#RiskSignalsHTTPSAccess"
    layout = "https://example.test/project#RiskSignalsJSONLayout"

    db.record_map_storage_access(
        storage,
        label="Risk signals HTTPS access",
        storage_protocol="rc:HTTPSStorage",
        location_kind="object",
        storage_root="https://api.example.test/risk/signals",
        path_templates=["latest.json"],
        layout_verification_status="rc:CandidateLayout",
    )
    db.record_map_physical_layout(
        layout,
        file_format="https://example.test/project#JSONDocument",
        layout_verification_status="rc:CandidateLayout",
    )
    db.record_map_dataset(
        api,
        label="Risk signals API",
        is_table=False,
        path_templates=["risk/signals/latest.json"],
        storage_accesses=[storage],
        physical_layouts=[layout],
        layout_verification_status="rc:CandidateLayout",
    )

    context = db.describe_query_context(api)
    slice_context = db.get_context_graph([api], profile="deep_lore")
    brief = db.project_brief(limit=5)

    assert context.readiness == "not_applicable_non_tabular_asset"
    assert {
        issue.code
        for dataset in slice_context.dataset_contexts
        for issue in dataset.operational_warnings
    } == {"layout_needs_verification"}
    assert [
        action.tool.removeprefix("doxabase.") for action in slice_context.suggested_next_actions
    ] == []
    assert brief.queue_counts == {"non_tabular_asset_review": 1}
    assert "query_repair_review" not in brief.queue_counts
    assert "query_context_review" not in brief.queue_counts


def test_describe_assertion_support_suggests_dataset_context_for_relationships(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/orders#"
    orders = f"{base}Orders"
    customers = f"{base}Customers"
    customer_id = f"{base}orders__customer_id"
    customer_pk = f"{base}customers__id"
    relationship = f"{base}orders_customer_fk"
    caveat = f"{base}orders_customer_fk_caveat"

    db.record_map_dataset(
        orders,
        label="Orders",
        is_table=True,
        path_templates=["warehouse/orders/*.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
        layout_verification_note="Orders layout matched the warehouse listing.",
    )
    db.record_map_dataset(customers, label="Customers", is_table=True)
    db.record_map_column(
        customer_id,
        table_iri=orders,
        column_name="customer_id",
        physical_type="rc:Varchar",
    )
    db.record_map_column(
        customer_pk,
        table_iri=customers,
        column_name="id",
        physical_type="rc:Varchar",
    )
    db.record_map_caveat(
        caveat,
        label="Orders customer identifier caveat",
        description="Some historical orders use migrated customer identifiers.",
        severity="rc:Moderate",
        targets=[orders],
    )
    db.record_map_relationship(
        relationship,
        relationship_type="foreign_key",
        label="orders customer fk",
        from_column=customer_id,
        to_column=customer_pk,
        declared=False,
    )

    relationship_support = db.describe_assertion_support(
        relationship,
        "rc:foreignKeyFrom",
        customer_id,
    )

    assert relationship_support.assertion_present is True
    assert relationship_support.owner_dataset is None
    assert any(
        triple.subject == orders
        and triple.predicate == RC + "pathTemplate"
        and triple.object == "warehouse/orders/*.parquet"
        for triple in relationship_support.nearby_context_triples
    )
    assert any(
        link.scope == "owner_dataset"
        and link.via_resource.iri == orders
        and link.matched_resource.iri == customer_id
        for link in relationship_support.nearby_caveat_links
    )
    assert relationship_support.suggested_next_actions[0].args["seed_iris"][
        :3
    ] == [
        orders,
        relationship,
        customer_id,
    ]
    assert any(
        action.tool == "doxabase.describe_dataset"
        and action.args["iri"] == orders
        for action in relationship_support.suggested_next_actions
    )

    guessed_dataset_relationship = db.describe_assertion_support(
        orders,
        "rc:hasRelationship",
        relationship,
    )

    assert guessed_dataset_relationship.assertion_present is False
    assert guessed_dataset_relationship.owner_dataset is None
    assert any(
        action.tool == "doxabase.describe_dataset"
        and action.args["iri"] == orders
        for action in guessed_dataset_relationship.suggested_next_actions
    )
    assert "Dataset-context suggested actions" in (
        guessed_dataset_relationship.support_scope_note
    )

    relationship_replacements = [
        ("rc:foreignKeyFrom", customer_pk),
        ("rc:foreignKeyTo", customer_id),
        ("rc:sourceDataset", customers),
        ("rc:targetDataset", orders),
    ]
    for predicate, replacement in relationship_replacements:
        staged = db.stage_map_assertion_change(
            relationship,
            predicate,
            replacement,
            change_kind="replace",
            rationale=(
                "Exercise relationship review impact routing for staged "
                f"{predicate} changes."
            ),
        )

        assert any(
            impact.impact_type == "changed_relationship"
            for impact in staged.judgement_panel.impacts
        )
        description = db.describe_staged_revision(
            staged.staged_revision.revision_iri
        )
        assert any(
            impact.impact_type == "changed_relationship"
            for impact in description.impacts
        )


def test_describe_query_context_reports_planning_metadata_and_issues(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    context = db.describe_query_context(
        "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"
    )

    assert context.dataset.label == "AIS Daily Broadcast Positions"
    assert context.readiness == "needs_review"
    assert context.path_templates == ["broadcasts/{year}/ais-{date}.parquet"]
    assert len(context.query_target_candidates) == 1
    target = context.query_target_candidates[0]
    assert target.template == "broadcasts/{year}/ais-{date}.parquet"
    assert target.template_source == "partition_scheme"
    assert target.storage_root == "s3://ais-noaa/"
    assert target.bucket_name == "ais-noaa"
    assert target.candidate_path == "s3://ais-noaa/broadcasts/{year}/ais-{date}.parquet"
    assert target.composition == "storage_root_joined"
    assert target.access_mode is not None
    assert target.access_mode.iri == RC + "ReadOnlyAccess"
    assert target.endpoint_profile == "local-minio"
    assert target.region == "local"
    assert target.requires_endpoint_profile is True
    assert target.credential_reference == "profile:ais-readonly"
    assert target.path_style_access is True
    assert target.required_bindings == ["year", "date"]
    assert target.required_binding_details[1]["partition_column"].iri == (
        "https://richcanopy.org/example/manifest/ais#bc_date"
    )
    assert target.binding_example == (
        "year='2026', date='2026-06-30' -> "
        "s3://ais-noaa/broadcasts/2026/ais-2026-06-30.parquet"
    )
    assert target.binding_examples[1]["binding"] == "date"
    assert target.review_required is True
    assert any(reason.code == "layout_needs_verification" for reason in target.review_reasons)
    assert context.storage_accesses[0].endpoint_profile == "local-minio"
    assert context.storage_accesses[0].credential_reference == "profile:ais-readonly"
    assert {column.column_name for column in context.columns} >= {
        "mmsi",
        "timestamp",
    }
    query_action = next(
        action
        for action in context.suggested_next_actions
        if action.tool == "doxabase.draft_query_plan"
    )
    assert any(
        issue.code == "layout_needs_verification"
        and issue.domain == "query_planning"
        and issue.severity == "warning"
        and issue.resource is not None
        and issue.resource.iri
        == "https://richcanopy.org/example/manifest/ais#daily_date_partition"
        and "verify against storage listing" in issue.message
        for issue in context.issues
    )
    assert "non-secret planning metadata" in context.planning_notes[0]


def test_describe_query_context_reports_missing_planning_metadata(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Messages"
    db.record_map_dataset(dataset, label="Messages", is_table=True)

    context = db.describe_query_context(dataset)

    assert context.readiness == "insufficient_metadata"
    assert {issue.code for issue in context.issues} >= {
        "missing_path_template",
        "missing_storage_access",
        "missing_physical_layout",
    }
    missing_storage = next(
        issue for issue in context.issues if issue.code == "missing_storage_access"
    )
    assert missing_storage.details is not None
    assert missing_storage.details["dataset_iri"] == dataset
    assert missing_storage.details["global_storage_access_count"] == 0
    assert missing_storage.details["repair_hint"]["action_type"] == (
        "record_or_link_storage_access"
    )
    assert missing_storage.details["repair_hint"]["choice_mode"] == "choose_one"
    assert missing_storage.details["repair_hint"][
        "candidate_existing_storage_accesses"
    ] == []
    assert missing_storage.details["repair_hint"][
        "candidate_existing_storage_access_count"
    ] == 0
    assert missing_storage.details["repair_hint"][
        "candidate_existing_storage_access_total_count"
    ] == 0
    assert missing_storage.details["repair_hint"][
        "candidate_existing_storage_accesses_truncated"
    ] is False
    repair_actions = missing_storage.details["repair_hint"]["actions"]
    optional_storage_fields = [
        "endpoint_profile",
        "bucket_name",
        "key_prefix",
        "region",
        "path_style_access",
        "credential_reference",
    ]
    assert [action["action_type"] for action in repair_actions] == [
        "stage_reviewed_storage_access",
        "record_reviewed_storage_access",
        "stage_existing_storage_access_link",
    ]
    assert [action["tool"].removeprefix("doxabase.") for action in repair_actions] == [
        "stage_query_storage_access_repair",
        "record_map_storage_access",
        "stage_map_assertion_change",
    ]
    assert repair_actions[0]["required_extra_arguments"] == [
        "storage_access_iri",
        "storage_protocol",
        "storage_root",
        "rationale",
    ]
    assert repair_actions[0]["arguments_template"]["dataset_iri"] == dataset
    assert repair_actions[0]["arguments_template"]["storage_access_iri"] == (
        "<reviewed storage access IRI>"
    )
    assert repair_actions[0]["placeholder_fields"] == [
        "storage_access_iri",
        "storage_protocol",
        "storage_root",
        *optional_storage_fields,
        "rationale",
        "location_kind",
        "path_templates",
        "layout_verification_status",
        "layout_verification_note",
    ]
    assert "stage_query_storage_access_repair records a reviewable" in (
        repair_actions[0]["review_rationale_guidance"]
    )
    assert repair_actions[1]["required_extra_arguments"] == [
        "iri",
        "storage_protocol",
        "storage_root",
    ]
    assert repair_actions[1]["arguments_template"]["datasets"] == [dataset]
    assert repair_actions[1]["placeholder_fields"] == [
        *optional_storage_fields,
        "path_templates",
    ]
    assert repair_actions[1]["reviewed_value_fields"] == [
        *optional_storage_fields,
        "path_templates",
    ]
    assert "Omit this optional field" in repair_actions[1]["condition"]
    assert "duplicating it can create equivalent query target candidates" in (
        repair_actions[1]["condition"]
    )
    assert "Database relation identifiers" in repair_actions[1]["condition"]
    assert "database_relation_template_source_mismatch" in (
        repair_actions[1]["condition"]
    )
    assert repair_actions[1]["protocol_guidance"][
        "file_or_object_storage"
    ].startswith("Omit storage-owned path_templates")
    assert "database relation identifiers" in repair_actions[1][
        "protocol_guidance"
    ]["rc:DatabaseStorage"]
    assert "record_map_storage_access writes current-best map facts directly" in (
        repair_actions[1]["review_rationale_guidance"]
    )
    assert repair_actions[2]["arguments_template"]["subject"] == dataset
    assert repair_actions[2]["arguments_template"]["predicate"] == (
        "rc:hasStorageAccess"
    )
    assert repair_actions[2]["placeholder_fields"] == ["object"]
    assert repair_actions[2]["reviewed_value_fields"] == ["object"]
    assert "revision_anchors" not in repair_actions[2]["arguments_template"]
    assert context.suggested_repair_action_group_count == 1
    repair_group = context.suggested_repair_action_groups[0]
    assert repair_group.group_name == "query_repair_review"
    assert repair_group.issue_code == "missing_storage_access"
    assert repair_group.issue_resource is not None
    assert repair_group.issue_resource.iri == dataset
    assert repair_group.repair_action_type == "record_or_link_storage_access"
    assert repair_group.choice_mode == "choose_one"
    assert repair_group.repair_hint_path == (
        f"issues[{repair_group.issue_index}].details.repair_hint"
    )
    assert repair_group.repair_context["choice_mode"] == "choose_one"
    assert repair_group.repair_context[
        "candidate_existing_storage_accesses"
    ] == []
    assert repair_group.action_count == 3
    assert repair_group.action_status_counts == {"pending_review": 3}
    assert repair_group.pending_action_count == 3
    assert repair_group.skippable_action_count == 0
    assert repair_group.already_satisfied_action_count == 0
    assert repair_group.pending_required_extra_arguments == [
        "storage_access_iri",
        "storage_protocol",
        "storage_root",
        "rationale",
        "iri",
        "object",
    ]
    assert len(repair_group.pending_action_options) == 3
    staged_storage_option = repair_group.pending_action_options[0]
    _assert_repair_action_option(
        staged_storage_option,
        action_index=0,
        action_type="stage_reviewed_storage_access",
        tool="doxabase.stage_query_storage_access_repair",
        required_extra_arguments=[
            "storage_access_iri",
            "storage_protocol",
            "storage_root",
            "rationale",
        ],
        placeholder_fields=[
            "storage_access_iri",
            "storage_protocol",
            "storage_root",
            *optional_storage_fields,
            "rationale",
            "location_kind",
            "path_templates",
            "layout_verification_status",
            "layout_verification_note",
        ],
        reviewed_value_fields=[
            "storage_access_iri",
            "storage_protocol",
            "storage_root",
            *optional_storage_fields,
            "rationale",
            "location_kind",
            "path_templates",
            "layout_verification_status",
            "layout_verification_note",
        ],
    )
    assert "staged-revision rationale" in staged_storage_option["reason"]
    storage_option = repair_group.pending_action_options[1]
    _assert_repair_action_option(
        storage_option,
        action_index=1,
        action_type="record_reviewed_storage_access",
        tool="doxabase.record_map_storage_access",
        required_extra_arguments=[
            "iri",
            "storage_protocol",
            "storage_root",
        ],
        placeholder_fields=[*optional_storage_fields, "path_templates"],
        reviewed_value_fields=[*optional_storage_fields, "path_templates"],
    )
    assert "non-secret storage protocol" in storage_option["reason"]
    assert "Database relation identifiers" in storage_option["condition"]
    assert "record_map_storage_access writes current-best map facts directly" in (
        storage_option["review_rationale_guidance"]
    )
    link_option = repair_group.pending_action_options[2]
    _assert_repair_action_option(
        link_option,
        action_index=2,
        action_type="stage_existing_storage_access_link",
        tool="doxabase.stage_map_assertion_change",
        required_extra_arguments=["object", "rationale"],
        placeholder_fields=["object"],
        reviewed_value_fields=["object"],
    )
    assert "suitable storage access resource already exists" in link_option["reason"]
    assert [action["action_type"] for action in repair_group.actions] == [
        "stage_reviewed_storage_access",
        "record_reviewed_storage_access",
        "stage_existing_storage_access_link",
    ]
    assert [action["tool"].removeprefix("doxabase.") for action in repair_group.actions] == [
        "stage_query_storage_access_repair",
        "record_map_storage_access",
        "stage_map_assertion_change",
    ]
    assert repair_group.actions[0]["arguments_template"]["dataset_iri"] == dataset
    assert repair_group.actions[1]["arguments_template"]["datasets"] == [dataset]
    assert repair_group.actions[2]["arguments_template"]["predicate"] == (
        "rc:hasStorageAccess"
    )
    assert repair_group.actions[2]["placeholder_fields"] == ["object"]
    assert repair_group.actions[2]["reviewed_value_fields"] == ["object"]
    assert "revision_anchors" not in repair_group.actions[2]["arguments_template"]
    assert [issue.severity for issue in context.issues[:2]] == ["error", "error"]
    assert {issue.domain for issue in context.issues} == {"query_planning"}
    assert context.query_target_decision.status == "no_candidate"
    assert context.query_target_decision.candidate_index is None
    assert context.query_target_decision.candidate_path is None
    assert context.query_target_decision.candidate_path_status is None
    assert context.query_target_decision.direct_review_required is None
    assert context.query_target_decision.selected_candidate_direct_clean is None
    assert context.query_target_decision.reason_codes == []


def test_describe_query_context_marks_non_tabular_asset_not_applicable(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    asset = "https://example.test/project#SalesReadme"
    storage = db.record_map_storage_access(
        "https://example.test/project#sales_readme_storage",
        label="Sales README storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="object",
        storage_root=str(tmp_path / "sales-readme.md"),
        layout_verification_status="rc:CandidateLayout",
    )
    db.record_map_dataset(
        asset,
        label="Sales README",
        is_table=False,
        storage_accesses=[storage.iri],
        layout_verification_status="rc:CandidateLayout",
    )

    context = db.describe_query_context(asset)

    assert context.readiness == "not_applicable_non_tabular_asset"
    assert context.query_target_candidates == []
    assert context.ready_candidate_indexes == []
    assert context.suggested_repair_action_groups == []
    assert context.query_target_decision.status == (
        "not_applicable_non_tabular_asset"
    )
    assert context.query_target_decision.reason_codes == [
        "non_tabular_asset_query_not_applicable"
    ]
    assert [issue.code for issue in context.issues] == [
        "non_tabular_asset_query_not_applicable"
    ]
    assert context.issues[0].severity == "info"
    assert context.storage_accesses[0].iri == storage.iri
    assert context.suggested_repair_action_group_count == 0
    assert context.suggested_next_actions[0].tool == "doxabase.get_context_graph"

    plan = db.draft_query_plan(asset)

    assert plan.handoff_kind == "not_applicable_non_tabular_asset"
    assert plan.source_context.readiness == "not_applicable_non_tabular_asset"
    assert plan.source_context.selection_mode == "not_applicable"
    assert plan.selected_candidate is None
    assert plan.scan.function is None
    assert plan.scan.uri_template is None
    assert plan.review_gate.status == "not_applicable_non_tabular_asset"
    assert plan.review_gate.ready_for_execution_attempt is False
    assert plan.review_gate.primary_execution_attempt_blocking_reason_code == (
        "non_tabular_asset_query_not_applicable"
    )
    assert plan.issues[0].code == "non_tabular_asset_query_not_applicable"


def test_describe_query_context_flags_known_fixture_without_linked_storage(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"
    unrelated = "https://example.test/project#UnrelatedOrders"
    db.record_map_dataset(dataset, label="AIS Daily Broadcast Positions", is_table=True)
    db.record_map_dataset(unrelated, label="Unrelated orders", is_table=True)
    db.record_map_storage_access(
        "https://example.test/project#unrelated_storage",
        datasets=[unrelated],
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/tmp/unrelated",
    )

    context = db.describe_query_context(dataset)
    missing_storage = next(
        issue for issue in context.issues if issue.code == "missing_storage_access"
    )

    assert missing_storage.details is not None
    fixture_hint = missing_storage.details["fixture_staleness_hint"]
    assert fixture_hint["fixture_names"] == ["AIS"]
    assert fixture_hint["global_storage_access_count"] == 1
    assert fixture_hint["dataset_matches_known_fixture"] is True
    assert dataset in fixture_hint["known_fixture_table_iris"]
    assert "without linked rc:StorageAccess" in fixture_hint["message"]

    advisory = context.suggested_repair_action_groups[0].group_advisories[0]
    assert advisory["code"] == "query_fixture_staleness_review"
    assert advisory["storage_access_count"] == 1
    assert advisory["dataset_matches_known_fixture"] is True
    assert dataset in advisory["known_fixture_table_iris"]


def test_describe_query_context_matches_current_polymarket_fixture_names(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    namespace = "https://richcanopy.org/example/manifest/polymarket#"
    table_names = [
        "MarketSnapshots",
        "PriceSnapshots",
        "OrderbookSnapshots",
        "Trades",
        "HolderSnapshots",
    ]
    for table_name in table_names:
        db.record_map_dataset(
            f"{namespace}{table_name}",
            label=table_name,
            is_table=True,
        )

    for table_name in table_names:
        dataset = f"{namespace}{table_name}"
        context = db.describe_query_context(dataset)
        missing_storage = next(
            issue for issue in context.issues if issue.code == "missing_storage_access"
        )

        assert missing_storage.details is not None
        fixture_hint = missing_storage.details["fixture_staleness_hint"]
        assert fixture_hint["fixture_names"] == ["Polymarket"]
        assert fixture_hint["global_storage_access_count"] == 0
        assert fixture_hint["dataset_matches_known_fixture"] is True
        assert dataset in fixture_hint["known_fixture_table_iris"]


def test_describe_query_context_advises_s3_credential_marker_when_omitted(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_s3_storage",
        label="Orders S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        bucket_name="orders",
        key_prefix="warehouse",
        endpoint_profile="orders-prod",
        region="us-test-1",
        path_templates=["orders/*.parquet"],
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

    assert context.readiness == "ready_for_query_planning"
    advisory = next(
        issue
        for issue in context.issues
        if issue.code == "s3_credential_reference_not_recorded"
    )
    assert advisory.severity == "info"
    assert advisory.resource is not None
    assert advisory.resource.iri == storage.iri
    assert advisory.details is not None
    assert advisory.details["recommended_omitted_marker"] == (
        "external:intentionally-unrecorded"
    )
    target = context.query_target_candidates[0]
    assert target.candidate_path == "s3://orders/warehouse/orders/*.parquet"
    assert target.candidate_path_status == "ready"
    assert target.review_required is False
    assert target.direct_review_required is False
    assert [
        reason.code for reason in target.review_reasons
    ] == ["s3_credential_reference_not_recorded"]
    assert [
        reason.code for reason in target.direct_review_reasons
    ] == ["s3_credential_reference_not_recorded"]
    assert context.query_target_decision.status == "ready"
    assert context.query_target_decision.reason_codes == []

    draft_action = next(
        action
        for action in context.suggested_next_actions
        if action.tool == "doxabase.draft_query_plan"
    )

    plan = db.draft_query_plan(dataset)
    assert plan.review_gate.all_issue_codes == [
        "s3_credential_reference_not_recorded"
    ]
    assert plan.review_gate.blocking_reason_codes == []
    assert plan.review_gate.status == "ready"
    assert plan.handoff_kind == "runtime_resolution_required"


def test_query_target_decision_prefers_dataset_template_over_shared_storage_peer(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/project#"
    storage = db.record_map_storage_access(
        f"{base}shared_enron_storage",
        label="Shared Enron object-store access",
        storage_protocol="rc:S3CompatibleStorage",
        storage_root="s3://enron-emails/",
        location_kind="prefix",
        bucket_name="enron-emails",
        endpoint_profile="local-minio",
        credential_reference="profile:enron-readonly",
        path_templates=["eml_attachments.parquet", "eml_messages.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        f"{base}parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    messages = f"{base}eml_messages"
    attachments = f"{base}eml_attachments"
    db.record_map_dataset(
        messages,
        label="EML messages",
        is_table=True,
        path_templates=["eml_messages.parquet"],
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    db.record_map_dataset(
        attachments,
        label="EML attachments",
        is_table=True,
        path_templates=["eml_attachments.parquet"],
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByListingLayout",
    )

    messages_context = db.describe_query_context(messages)
    messages_index = messages_context.query_target_decision.candidate_index
    assert messages_index is not None
    messages_candidate = messages_context.query_target_candidates[messages_index]
    assert messages_candidate.template_source == "dataset"
    assert messages_candidate.source_resource.iri == messages
    assert messages_candidate.candidate_path == "s3://enron-emails/eml_messages.parquet"
    assert messages_context.query_target_decision.status == "ready"
    assert set(messages_context.unselected_ready_candidate_indexes) == {1, 2}

    messages_plan = db.draft_query_plan(messages)
    assert messages_plan.selected_candidate is not None
    assert messages_plan.selected_candidate.template_source == "dataset"
    assert messages_plan.scan.uri_template == "s3://enron-emails/eml_messages.parquet"

    attachments_context = db.describe_query_context(attachments)
    attachments_index = attachments_context.query_target_decision.candidate_index
    assert attachments_index is not None
    attachments_candidate = attachments_context.query_target_candidates[
        attachments_index
    ]
    assert attachments_candidate.template_source == "dataset"
    assert attachments_candidate.source_resource.iri == attachments
    assert attachments_candidate.candidate_path == (
        "s3://enron-emails/eml_attachments.parquet"
    )


def test_query_target_decision_prefers_ready_wildcard_without_bindings(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#DailyIndex"
    date_column = db.record_map_column(
        "https://example.test/project#daily_index__date",
        table_iri=dataset,
        column_name="date",
    )
    shared_storage = db.record_map_storage_access(
        "https://example.test/project#shared_object_store_access",
        label="Shared object-store access",
        storage_protocol="rc:S3CompatibleStorage",
        storage_root="s3://ais-noaa/",
        endpoint_profile="local-minio",
        credential_reference="profile:ais-readonly",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    index_storage = db.record_map_storage_access(
        "https://example.test/project#daily_index_object_store_access",
        label="Daily index object-store access",
        storage_protocol="rc:S3CompatibleStorage",
        storage_root="s3://ais-noaa/",
        endpoint_profile="local-minio",
        credential_reference="profile:ais-readonly",
        path_templates=["index/*/*.parquet"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    partition = db.record_map_partition_scheme(
        "https://example.test/project#daily_index_date_partition",
        path_template="index/{year}/ais-{date}.parquet",
        partition_columns=[date_column.iri],
        granularity="rc:Daily",
        layout_verification_status="rc:VerifiedByQueryLayout",
        datasets=[dataset],
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#daily_index_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Daily index",
        is_table=True,
        columns=[date_column.iri],
        storage_accesses=[shared_storage.iri, index_storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    wildcard_index, wildcard_candidate = next(
        (index, target)
        for index, target in enumerate(context.query_target_candidates)
        if target.template_source == "storage_access"
        and target.storage_access is not None
        and target.storage_access.iri == index_storage.iri
    )
    partition_indexes = [
        index
        for index, target in enumerate(context.query_target_candidates)
        if target.source_resource.iri == partition.iri
    ]
    assert partition_indexes
    assert wildcard_candidate.candidate_path == "s3://ais-noaa/index/*/*.parquet"
    assert wildcard_candidate.candidate_path_status == "ready"
    assert wildcard_candidate.review_required is False
    assert context.query_target_decision.status == "ready"
    assert context.query_target_decision.candidate_index == wildcard_index
    assert context.ready_candidate_indexes == [
        *partition_indexes,
        wildcard_index,
    ]
    assert context.unselected_ready_candidate_indexes == partition_indexes

    plan = db.draft_query_plan(dataset)

    assert plan.selected_candidate is not None
    assert plan.selected_candidate.template_source == "storage_access"
    assert plan.scan.uri_template == "s3://ais-noaa/index/*/*.parquet"
    assert plan.required_bindings == []
    assert plan.review_gate.binding_values_required is False
    assert plan.review_gate.execution_attempt_blocking_reason_codes == [
        "runtime_resolution_required"
    ]
    summary = plan.handoff_summary
    assert summary.handoff_kind == "runtime_resolution_required"
    assert summary.selected_candidate_index == wildcard_index
    assert summary.scan_function == "read_parquet"
    assert summary.uri_template == "s3://ais-noaa/index/*/*.parquet"
    assert summary.required_bindings == []
    assert summary.executable_without_review is True
    assert summary.ready_for_execution_attempt is False
    assert summary.primary_execution_attempt_blocking_reason_code == (
        "runtime_resolution_required"
    )
    assert summary.runtime_resolution_required is True
    assert summary.binding_values_required is False


def test_describe_query_context_warns_on_protocol_location_mismatch(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Snapshots"
    storage = db.record_map_storage_access(
        "https://example.test/project#snapshots_https_storage",
        label="Snapshots HTTPS access",
        storage_protocol="rc:HTTPSStorage",
        bucket_name="public",
        key_prefix="snapshots",
        path_templates=["dt={date}.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#snapshots_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Snapshots",
        is_table=True,
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
        for issue in context.issues
    )
    target = context.query_target_candidates[0]
    assert target.review_required is True
    assert target.candidate_path_status == "orientation_only"
    mismatch = next(
        reason
        for reason in target.review_reasons
        if reason.code == "storage_protocol_location_mismatch"
    )
    assert mismatch.details is not None
    assert mismatch.details["storage_access_iri"] == storage.iri
    assert mismatch.details["storage_protocol_iri"] == RC + "HTTPSStorage"
    assert mismatch.details["bucket_name"] == "public"
    assert mismatch.details["key_prefix"] == "snapshots"
    assert any(
        "bucket/prefix" in reason
        for reason in mismatch.details["mismatch_reasons"]
    )
    repair_hint = mismatch.details["repair_hint"]
    assert repair_hint["action_type"] == "repair_storage_protocol_location_mismatch"
    assert repair_hint["requires_review"] is True
    assert repair_hint["storage_access"]["storage_access_iri"] == storage.iri
    assert context.suggested_repair_action_group_count == 1
    repair_group = context.suggested_repair_action_groups[0]
    assert repair_group.group_name == "query_repair_review"
    assert repair_group.issue_code == "storage_protocol_location_mismatch"
    assert repair_group.issue_severity == "warning"
    assert repair_group.issue_resource is not None
    assert repair_group.issue_resource.iri == storage.iri
    assert repair_group.repair_hint_path == (
        f"issues[{repair_group.issue_index}].details.repair_hint"
    )
    assert context.issues[repair_group.issue_index].details is not None
    assert (
        context.issues[repair_group.issue_index].details["repair_hint"]
        == repair_hint
    )
    assert repair_group.repair_action_type == (
        "repair_storage_protocol_location_mismatch"
    )
    assert repair_group.requires_review is True
    assert repair_group.repair_context["storage_access"]["storage_access_iri"] == (
        storage.iri
    )
    assert "actions" not in repair_group.repair_context
    assert repair_group.action_count == len(repair_hint["actions"])
    action_by_type = {
        action["action_type"]: action for action in repair_hint["actions"]
    }
    grouped_action_by_type = {
        action["action_type"]: action for action in repair_group.actions
    }
    assert grouped_action_by_type == action_by_type
    assert action_by_type["set_reviewed_storage_protocol"]["arguments_template"] == {
        "subject": storage.iri,
        "predicate": "rc:storageProtocol",
        "object": "<reviewed_rc_storage_protocol_iri>",
        "object_kind": "iri",
        "change_kind": "replace",
        "graph": "map",
    }
    assert action_by_type["set_reviewed_storage_protocol"]["placeholder_fields"] == [
        "object"
    ]
    assert action_by_type["set_reviewed_storage_protocol"][
        "reviewed_value_fields"
    ] == ["object"]
    assert action_by_type["set_reviewed_storage_root"]["placeholder_fields"] == [
        "object"
    ]
    assert "set_reviewed_bucket_name" not in action_by_type
    assert "set_reviewed_key_prefix" not in action_by_type
    assert action_by_type["remove_conflicting_bucket_name"]["args"] == {
        "subject": storage.iri,
        "predicate": "rc:bucketName",
        "object": "public",
        "object_kind": "literal",
        "change_kind": "remove",
        "graph": "map",
    }
    assert action_by_type["remove_conflicting_key_prefix"]["args"] == {
        "subject": storage.iri,
        "predicate": "rc:keyPrefix",
        "object": "snapshots",
        "object_kind": "literal",
        "change_kind": "remove",
        "graph": "map",
    }

    protocol_arguments = dict(
        action_by_type["set_reviewed_storage_protocol"]["arguments_template"]
    )
    protocol_arguments["object"] = "rc:S3CompatibleStorage"
    protocol_arguments["rationale"] = (
        "Reviewed snapshots storage as S3-compatible object storage."
    )
    staged_protocol = db.stage_map_assertion_change(**protocol_arguments)

    pending_context = db.describe_query_context(dataset)
    pending_group = pending_context.suggested_repair_action_groups[0]
    pending_action_by_type = {
        action["action_type"]: action for action in pending_group.actions
    }
    assert pending_group.action_status_counts == {
        "already_pending": 1,
        "pending_review": 3,
    }
    assert pending_group.pending_action_count == 3
    assert pending_group.skippable_action_count == 1
    assert pending_action_by_type["set_reviewed_storage_protocol"][
        "action_status"
    ] == "already_pending"
    assert pending_action_by_type["set_reviewed_storage_protocol"][
        "pending_staged_repair_iris"
    ] == [staged_protocol.revision_iri]
    assert "set_reviewed_storage_protocol" not in {
        option["action_type"] for option in pending_group.pending_action_options
    }

    pending_brief = db.project_brief(limit=3)
    pending_query_task = next(
        task
        for task in pending_brief.recommended_next_tasks
        if task.task_type == "query_repair_review"
    )
    assert pending_query_task.pending_staged_repair_iris == [
        staged_protocol.revision_iri
    ]


def test_describe_query_context_warns_on_non_s3_bucket_prefix(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    storage = db.record_map_storage_access(
        "https://example.test/project#events_local_storage",
        label="Events local access",
        storage_protocol="rc:LocalFilesystemStorage",
        bucket_name="ignored-bucket",
        key_prefix="local-shaped-prefix",
        path_templates=["events/dt={date}.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
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

    assert context.readiness == "needs_review"
    target = context.query_target_candidates[0]
    assert target.candidate_path == "local-shaped-prefix/events/dt={date}.parquet"
    assert target.candidate_path_status == "orientation_only"
    assert target.review_required is True
    assert any(
        reason.code == "storage_protocol_location_mismatch"
        and "bucket/prefix" in reason.message
        for reason in target.review_reasons
    )


@pytest.mark.parametrize(
    ("protocol", "storage_root", "expected_path"),
    [
        (
            "rc:S3CompatibleStorage",
            "/lake/not-s3",
            "/lake/not-s3/events/dt={date}.parquet",
        ),
        (
            "rc:HTTPSStorage",
            "s3://public-bucket/not-https",
            "s3://public-bucket/not-https/events/dt={date}.parquet",
        ),
    ],
)
def test_describe_query_context_warns_on_storage_root_protocol_mismatch(
    tmp_path: Path,
    protocol: str,
    storage_root: str,
    expected_path: str,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    storage = db.record_map_storage_access(
        "https://example.test/project#events_storage",
        label="Events access",
        storage_protocol=protocol,
        storage_root=storage_root,
        path_templates=["events/dt={date}.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
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

    assert context.readiness == "needs_review"
    target = context.query_target_candidates[0]
    assert target.candidate_path == expected_path
    assert target.candidate_path_status == "orientation_only"
    assert target.review_required is True
    assert any(
        reason.code == "storage_protocol_location_mismatch"
        and "storage_root" in reason.message
        for reason in target.review_reasons
    )
    mismatch = next(
        reason
        for reason in target.review_reasons
        if reason.code == "storage_protocol_location_mismatch"
    )
    assert mismatch.details is not None
    action_types = {
        action["action_type"]
        for action in mismatch.details["repair_hint"]["actions"]
    }
    if protocol == "rc:S3CompatibleStorage":
        assert "set_reviewed_bucket_name" in action_types
        assert "set_reviewed_key_prefix" in action_types
    else:
        assert "set_reviewed_bucket_name" not in action_types
        assert "set_reviewed_key_prefix" not in action_types


def test_describe_query_context_warns_on_unresolved_s3_access(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_s3_storage",
        label="Orders S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        bucket_name="orders",
        key_prefix="warehouse",
        path_templates=["dt={date}.parquet"],
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

    assert context.readiness == "needs_review"
    target = context.query_target_candidates[0]
    assert target.candidate_path == "s3://orders/warehouse/dt={date}.parquet"
    assert target.review_required is True
    assert any(
        reason.code == "s3_access_resolution_unrecorded"
        for reason in target.review_reasons
    )
    plan = db.draft_query_plan(dataset)
    assert plan.review_gate.executable_without_review is False
    assert plan.review_gate.blocking_reason_codes == ["s3_access_resolution_unrecorded"]
    assert plan.storage_environment.bucket_name == "orders"
    assert plan.storage_environment.key_prefix == "warehouse"
    assert plan.storage_environment.endpoint_profile is None
    assert plan.storage_environment.credential_reference is None
    assert plan.storage_environment.region is None
    assert plan.storage_environment.runtime_resolution_required is True
    assert plan.handoff_kind == "runtime_resolution_required"
    assert "Record or resolve the S3 endpoint profile" in (
        plan.storage_environment.runtime_resolution_note
    )


def test_describe_query_context_warns_on_complete_s3_template_without_runtime_resolution(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_s3_storage",
        label="Orders S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        path_templates=["s3://orders-bucket/warehouse/orders/*.parquet"],
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

    assert context.readiness == "needs_review"
    assert any(
        issue.code == "s3_access_resolution_unrecorded"
        and issue.resource is not None
        and issue.resource.iri == storage.iri
        for issue in context.issues
    )
    target = context.query_target_candidates[0]
    assert target.candidate_path == "s3://orders-bucket/warehouse/orders/*.parquet"
    assert target.composition == "template_as_returned"
    assert target.candidate_path_status == "orientation_only"
    assert target.review_required is True
    assert any(
        reason.code == "s3_access_resolution_unrecorded"
        for reason in target.review_reasons
    )


def test_describe_query_context_warns_on_complete_template_protocol_mismatch(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Snapshots"
    storage = db.record_map_storage_access(
        "https://example.test/project#snapshots_https_storage",
        label="Snapshots HTTPS access",
        storage_protocol="rc:HTTPSStorage",
        path_templates=["s3://public-bucket/snapshots/*.parquet"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#snapshots_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Snapshots",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "needs_review"
    target = context.query_target_candidates[0]
    assert target.candidate_path == "s3://public-bucket/snapshots/*.parquet"
    assert target.candidate_path_status == "orientation_only"
    assert target.review_required is True
    assert any(
        reason.code == "storage_protocol_location_mismatch"
        and "path template" in reason.message
        for reason in target.review_reasons
    )
    mismatch = next(
        reason
        for reason in target.review_reasons
        if reason.code == "storage_protocol_location_mismatch"
    )
    assert mismatch.details is not None
    repair_hint = mismatch.details["repair_hint"]
    assert repair_hint["source"] == {
        "subject_iri": storage.iri,
        "predicate": "rc:pathTemplate",
        "template": "s3://public-bucket/snapshots/*.parquet",
    }
    action_by_type = {
        action["action_type"]: action for action in repair_hint["actions"]
    }
    assert action_by_type["add_reviewed_path_template"]["arguments_template"] == {
        "subject": storage.iri,
        "predicate": "rc:pathTemplate",
        "object": "<reviewed_protocol_appropriate_path_template>",
        "object_kind": "literal",
        "change_kind": "add",
        "graph": "map",
    }
    assert action_by_type["add_reviewed_path_template"]["placeholder_fields"] == [
        "object"
    ]
    assert action_by_type["add_reviewed_path_template"][
        "reviewed_value_fields"
    ] == ["object"]
    assert action_by_type["remove_conflicting_path_template"]["args"] == {
        "subject": storage.iri,
        "predicate": "rc:pathTemplate",
        "object": "s3://public-bucket/snapshots/*.parquet",
        "object_kind": "literal",
        "change_kind": "remove",
        "graph": "map",
    }


def test_describe_query_context_warns_on_s3_template_bucket_prefix_conflict(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_s3_storage",
        label="Orders S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        bucket_name="orders-a",
        key_prefix="warehouse",
        path_templates=["s3://orders-b/raw/orders/*.parquet"],
        credential_reference="profile:orders-readonly",
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

    assert context.readiness == "needs_review"
    target = context.query_target_candidates[0]
    assert target.candidate_path == "s3://orders-b/raw/orders/*.parquet"
    assert target.candidate_path_status == "orientation_only"
    assert any(
        reason.code == "storage_protocol_location_mismatch"
        and "bucket_name" in reason.message
        and "key_prefix" in reason.message
        for reason in target.review_reasons
    )


def test_describe_query_context_warns_on_key_prefix_repeated_in_template(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_s3_storage",
        label="Orders S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        bucket_name="lake",
        key_prefix="warehouse",
        path_templates=["warehouse/orders/dt={date}.parquet"],
        credential_reference="profile:orders-readonly",
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

    assert context.readiness == "needs_review"
    target = context.query_target_candidates[0]
    assert target.candidate_path == (
        "s3://lake/warehouse/warehouse/orders/dt={date}.parquet"
    )
    assert target.candidate_path_status == "orientation_only"
    assert any(
        reason.code == "storage_protocol_location_mismatch"
        and "repeat recorded key_prefix" in reason.message
        for reason in target.review_reasons
    )


def test_describe_query_context_surfaces_storage_root_only_location(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage_root = str(tmp_path / "orders.parquet")
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_local_storage",
        label="Orders local storage",
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
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "ready_for_query_planning"
    assert "missing_path_template" not in {issue.code for issue in context.issues}
    assert context.path_templates == []
    assert len(context.query_target_candidates) == 1
    target = context.query_target_candidates[0]
    assert target.template == storage_root
    assert target.template_source == "storage_access_location"
    assert target.source_resource.iri == storage.iri
    assert target.storage_access is not None
    assert target.storage_access.iri == storage.iri
    assert target.location_kind == "object"
    assert target.candidate_path == storage_root
    assert target.composition == "storage_root_as_candidate"
    assert target.candidate_path_status == "ready"
    assert target.review_required is False
    assert target.review_reasons == []
    assert context.storage_accesses[0].location_kind == "object"
    plan = db.draft_query_plan(dataset)
    assert plan.scan.template_lineage is not None
    assert (
        "Candidate storage root comes from storage access Orders local storage."
        in plan.scan.template_lineage
    )
    assert "Template comes from storage_access_location" not in plan.scan.template_lineage
    assert plan.storage_environment.runtime_resolution_required is False
    assert plan.review_gate.executable_without_review is True
    assert plan.review_gate.runtime_resolution_required is False
    assert plan.review_gate.binding_values_required is False
    assert plan.review_gate.ready_for_execution_attempt is True
    assert plan.scan.execution_attempt_ready is True
    assert plan.handoff_summary.ready_for_execution_attempt is True
    assert plan.handoff_summary.primary_execution_attempt_blocking_reason_code is None
    assert plan.handoff_summary.uri_template == storage_root
    assert plan.review_gate.primary_execution_attempt_blocking_reason_code is None
    assert plan.scan.primary_execution_attempt_blocking_reason_code is None
    assert plan.scan.execution_attempt_blocking_reason_codes == []
    assert plan.handoff_kind == "execution_attempt_ready"
    assert "No endpoint or credential profile is recorded or required" in (
        plan.storage_environment.runtime_resolution_note
    )


def test_query_evidence_storage_overlay_returns_stale_seed_blocker(
    tmp_path: Path,
) -> None:
    warehouse = tmp_path / "warehouse"
    warehouse.mkdir()
    csv_path = warehouse / "orders.csv"
    csv_path.write_text("order_id,status\n1,paid\n", encoding="utf-8")

    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    result = db.record_query_result(
        summary="Orders query scanned the reviewed local CSV.",
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path=str(tmp_path / "orders_status.sql"),
        query_hash="sha256:stale-seed-overlay",
        scanned_source_paths=[str(csv_path)],
        row_count=1,
    )
    _delete_base_ontology_seed_terms(
        db,
        ["rc:GraphPatchRole", "rc:FramingPatch", "rc:SharedContextPatch"],
    )

    blocker = db.draft_query_evidence_storage_overlay(
        dataset,
        result.evidence_iri,
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(warehouse),
        location_kind="directory",
        path_templates=["orders.csv"],
        file_format="rc:CSV",
    )

    assert blocker.result_kind == "query_evidence_storage_overlay_blocker"
    assert blocker.mode == "blocked_stale_seed_recovery_required"
    assert blocker.missing_seed_terms == [
        "rc:GraphPatchRole",
        "rc:FramingPatch",
        "rc:SharedContextPatch",
    ]
    assert blocker.mutation_allowed_after == (
        "stale_seed_recovery_required_before_staging"
    )
    assert "immutable base_ontology is missing current staging vocabulary" in (
        blocker.note
    )
    assert blocker.suggested_next_actions[0].tool == "doxabase.export_preflight"
    assert blocker.suggested_next_actions[0].args == {
        "export_kind": "handoff_bundle",
        "graphs": ["project"],
        "limit": 20,
        "validation_scope": "map",
    }


def test_query_context_suggests_overlay_for_ordinary_query_evidence(
    tmp_path: Path,
) -> None:
    warehouse = tmp_path / "warehouse"
    warehouse.mkdir()
    csv_path = warehouse / "orders.csv"
    csv_path.write_text("order_id,status\n1,paid\n2,pending\n", encoding="utf-8")
    result_path = tmp_path / "orders_status.result.json"
    result_path.write_text('{"paid": 1}\n', encoding="utf-8")

    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    result = db.record_query_result(
        summary="Orders status aggregate scanned the reviewed local CSV.",
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path=str(tmp_path / "orders_status.sql"),
        query_hash="sha256:ordinary-query-evidence",
        result_sources=[str(result_path)],
        scanned_source_paths=[str(csv_path)],
    )

    context = db.describe_query_context(dataset)

    overlay_actions = [
        action
        for action in context.suggested_next_actions
        if action.tool == "doxabase.draft_query_evidence_storage_overlay"
    ]
    assert len(overlay_actions) == 1
    overlay_action = overlay_actions[0]
    assert overlay_action.args["dataset_iri"] == dataset
    assert overlay_action.args["evidence_iri"] == result.evidence_iri


def test_query_evidence_storage_overlay_echoes_optional_storage_fields(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    result = db.record_query_result(
        summary="Orders query scanned reviewed S3-compatible Parquet objects.",
        observed_asset=dataset,
        execution_status="succeeded",
        engine="duckdb",
        query_hash="sha256:orders-s3-overlay",
        result_sources=["s3://orders-reviewed/results/orders-summary.json"],
        scanned_source_paths=["s3://orders-reviewed/warehouse/orders/*.parquet"],
        sample_size=12,
        sample_scope="Reviewed S3-compatible Orders prefix.",
        sample_method="External read-only DuckDB aggregate query.",
        row_count=12,
    )
    context = db.describe_query_context(dataset)
    overlay_action = next(
        action
        for action in context.suggested_next_actions
        if action.tool == "doxabase.draft_query_evidence_storage_overlay"
    )
    s3_candidate = next(
        candidate
        for issue in context.issues
        if issue.details is not None
        and isinstance(issue.details.get("repair_hint"), dict)
        for candidate in (
            issue.details["repair_hint"].get(
                "evidence_storage_route_candidates"
            )
            or []
        )
        if candidate["candidate_kind"] == "s3_path_from_query_evidence"
    )
    assert s3_candidate["candidate_kind"] == "s3_path_from_query_evidence"
    assert s3_candidate["source_field"] == "scanned_source_paths"
    assert s3_candidate["source_value"] == (
        "s3://orders-reviewed/warehouse/orders/*.parquet"
    )
    assert s3_candidate["storage_protocol"] == "rc:S3CompatibleStorage"
    assert s3_candidate["storage_root"] == "s3://orders-reviewed"
    assert s3_candidate["location_kind"] == "prefix"
    assert s3_candidate["bucket_name"] == "orders-reviewed"
    assert s3_candidate["key_prefix"] == "warehouse/orders/"
    assert s3_candidate["path_templates"] == ["warehouse/orders/*.parquet"]
    assert s3_candidate["file_format"] == "rc:Parquet"
    assert s3_candidate[
        "draft_query_evidence_storage_overlay_candidate_arguments"
    ] == {
        "storage_protocol": "rc:S3CompatibleStorage",
        "storage_root": "s3://orders-reviewed",
        "location_kind": "prefix",
        "bucket_name": "orders-reviewed",
        "key_prefix": "warehouse/orders/",
        "path_templates": ["warehouse/orders/*.parquet"],
        "file_format": "rc:Parquet",
    }

    draft = db.draft_query_evidence_storage_overlay(
        dataset,
        result.evidence_iri,
        storage_protocol="rc:S3CompatibleStorage",
        storage_root="s3://orders-reviewed",
        location_kind="prefix",
        storage_access_iri="https://example.test/project#orders_s3_access",
        physical_layout_iri="https://example.test/project#orders_parquet_layout",
        storage_label="Reviewed Orders S3-compatible route",
        physical_layout_label="Reviewed Orders Parquet layout",
        endpoint_profile="local-minio",
        bucket_name="orders-reviewed",
        key_prefix="warehouse/orders/",
        region="us-east-1",
        path_style_access=True,
        credential_reference="env:ORDERS_READONLY",
        path_templates=["warehouse/orders/*.parquet"],
        file_format="rc:Parquet",
        compression_codec="rc:SnappyCompression",
        layout_verification_note=(
            "Reviewed query evidence scanned the S3-compatible Orders prefix."
        ),
    )

    overlay = draft.reviewed_overlay
    assert overlay["storage_access_iri"] == (
        "https://example.test/project#orders_s3_access"
    )
    assert overlay["physical_layout_iri"] == (
        "https://example.test/project#orders_parquet_layout"
    )
    assert overlay["storage_label"] == "Reviewed Orders S3-compatible route"
    assert overlay["physical_layout_label"] == "Reviewed Orders Parquet layout"
    assert overlay["storage_protocol"] == RC + "S3CompatibleStorage"
    assert overlay["storage_root"] == "s3://orders-reviewed"
    assert overlay["access_mode"] == RC + "ReadOnlyAccess"
    assert overlay["location_kind"] == "prefix"
    assert overlay["endpoint_profile"] == "local-minio"
    assert overlay["bucket_name"] == "orders-reviewed"
    assert overlay["key_prefix"] == "warehouse/orders/"
    assert overlay["region"] == "us-east-1"
    assert overlay["path_style_access"] is True
    assert overlay["credential_reference"] == "env:ORDERS_READONLY"
    assert overlay["path_templates"] == ["warehouse/orders/*.parquet"]
    assert overlay["file_format"] == RC + "Parquet"
    assert overlay["compression_codec"] == RC + "SnappyCompression"
    assert draft.validation_conforms is True
    assert "orders-reviewed" in draft.additions[0]["content"]


def test_query_evidence_storage_overlay_replaces_dataset_layout_status(
    tmp_path: Path,
) -> None:
    warehouse = tmp_path / "warehouse"
    warehouse.mkdir()
    csv_path = warehouse / "orders.csv"
    csv_path.write_text(
        "order_id,status\n1,paid\n2,pending\n",
        encoding="utf-8",
    )
    query_path = tmp_path / "orders_status.sql"
    query_path.write_text("select count(*) from orders;\n", encoding="utf-8")
    result_path = tmp_path / "orders_status.result.json"
    result_path.write_text('{"row_count": 2}\n', encoding="utf-8")

    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        layout_verification_status="rc:CandidateLayout",
        layout_verification_note="Candidate manifest metadata before query review.",
    )
    result = db.record_query_result(
        summary="Orders query scanned a reviewed local CSV.",
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path=str(query_path),
        query_hash="sha256:orders-status-replace",
        result_sources=[str(result_path)],
        sample_size=2,
        sample_scope="All rows in the reviewed Orders CSV.",
        sample_method="External read-only aggregate query.",
        row_count=2,
    )
    before_counts = _mutable_graph_counts(db)

    draft = db.draft_query_evidence_storage_overlay(
        dataset,
        result.evidence_iri,
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(warehouse),
        location_kind="directory",
        path_templates=["orders.csv"],
        file_format="rc:CSV",
        layout_verification_note=(
            "Reviewed query evidence scanned warehouse/orders.csv."
        ),
    )

    assert _mutable_graph_counts(db) == before_counts
    assert draft.validation_conforms is True
    assert "removals" in draft.stage_arguments
    removal_content = draft.stage_arguments["removals"][0]["content"]
    assert "CandidateLayout" in removal_content
    assert "Candidate manifest metadata before query review" in removal_content
    assert draft.reviewed_overlay[
        "replaced_dataset_layout_verification_statuses"
    ] == [RC + "CandidateLayout"]
    assert draft.reviewed_overlay["replaced_dataset_layout_verification_notes"] == [
        "Candidate manifest metadata before query review."
    ]
    assert [
        patch.operation for patch in draft.patches
    ] == [
        RC + "AdditionPatch",
        RC + "RemovalPatch",
    ]

    staged = db.stage_graph_revision(**draft.stage_arguments)
    assert staged.validation_conforms is True
    assert db.check_staged_revision_apply(staged.revision_iri).status == "ready"
    db.apply_staged_revision(staged.revision_iri)

    assert db.validate_graph(scope="all").conforms
    context = db.describe_query_context(dataset)
    assert context.layout_verification_status is not None
    assert context.layout_verification_status.iri == RC + "VerifiedByQueryLayout"
    assert context.layout_verification_note == (
        "Reviewed query evidence scanned warehouse/orders.csv."
    )
    plan = db.draft_query_plan(dataset)
    assert plan.handoff_kind == "execution_attempt_ready"
    assert plan.scan.uri_template == str(csv_path)


def test_query_evidence_storage_overlay_replaces_reused_resource_verification(
    tmp_path: Path,
) -> None:
    warehouse = tmp_path / "warehouse"
    warehouse.mkdir()
    csv_path = warehouse / "orders.csv"
    csv_path.write_text("order_id,status\n1,paid\n2,pending\n", encoding="utf-8")

    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage_iri = "https://example.test/project#orders_reviewed_storage"
    layout_iri = "https://example.test/project#orders_reviewed_layout"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_storage_access(
        storage_iri,
        label="Orders reviewed storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(warehouse),
        location_kind="directory",
        datasets=[dataset],
        layout_verification_status="rc:CandidateLayout",
        layout_verification_note="Storage metadata imported before query review.",
    )
    db.record_map_physical_layout(
        layout_iri,
        label="Orders reviewed CSV layout",
        file_format="rc:CSV",
        datasets=[dataset],
        layout_verification_status="rc:CandidateLayout",
        layout_verification_note="Layout metadata imported before query review.",
    )
    result = db.record_query_result(
        summary="Orders query scanned a reviewed local CSV.",
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_hash="sha256:orders-reused-overlay",
        result_sources=[str(tmp_path / "orders.result.json")],
        scanned_source_paths=[str(csv_path)],
        sample_size=2,
        sample_scope="All rows in the reviewed Orders CSV.",
        sample_method="External read-only aggregate query.",
        row_count=2,
    )
    before_counts = _mutable_graph_counts(db)

    draft = db.draft_query_evidence_storage_overlay(
        dataset,
        result.evidence_iri,
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(warehouse),
        location_kind="directory",
        storage_access_iri=storage_iri,
        physical_layout_iri=layout_iri,
        storage_label="Orders reviewed storage",
        physical_layout_label="Orders reviewed CSV layout",
        path_templates=["orders.csv"],
        file_format="rc:CSV",
        layout_verification_note="Reviewed query evidence scanned orders.csv.",
    )

    assert _mutable_graph_counts(db) == before_counts
    assert draft.validation_conforms is True
    assert draft.reviewed_overlay[
        "replaced_storage_access_layout_verification_statuses"
    ] == [RC + "CandidateLayout"]
    assert draft.reviewed_overlay[
        "replaced_storage_access_layout_verification_notes"
    ] == ["Storage metadata imported before query review."]
    assert draft.reviewed_overlay[
        "replaced_physical_layout_verification_statuses"
    ] == [RC + "CandidateLayout"]
    assert draft.reviewed_overlay[
        "replaced_physical_layout_verification_notes"
    ] == ["Layout metadata imported before query review."]
    assert "removals" in draft.stage_arguments
    removal_content = draft.stage_arguments["removals"][0]["content"]
    assert "Storage metadata imported before query review" in removal_content
    assert "Layout metadata imported before query review" in removal_content

    staged = db.stage_graph_revision(**draft.stage_arguments)
    assert staged.validation_conforms is True
    check = db.check_staged_revision_apply(staged.revision_iri)
    assert check.status == "ready"
    applied = db.apply_staged_revision(staged.revision_iri)
    assert applied.patches_applied == 2

    assert db.validate_graph(scope="all").conforms
    context = db.describe_query_context(dataset)
    assert context.readiness == "ready_for_query_planning"
    storage = next(
        access
        for access in context.storage_accesses
        if access.iri == storage_iri
    )
    layout = next(
        physical_layout
        for physical_layout in context.physical_layouts
        if physical_layout.iri == layout_iri
    )
    assert storage.layout_verification_status is not None
    assert storage.layout_verification_status.iri == RC + "VerifiedByQueryLayout"
    assert storage.layout_verification_note == (
        "Reviewed query evidence scanned orders.csv."
    )
    assert layout.layout_verification_status is not None
    assert layout.layout_verification_status.iri == RC + "VerifiedByQueryLayout"
    assert layout.layout_verification_note == (
        "Reviewed query evidence scanned orders.csv."
    )


def test_query_context_blocks_path_extension_layout_mismatch(
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

    assert context.readiness == "needs_review"
    assert [issue.code for issue in context.issues] == [
        "physical_layout_path_extension_mismatch"
    ]
    issue = context.issues[0]
    assert issue.severity == "warning"
    assert issue.resource is not None
    assert issue.resource.iri == layout.iri
    assert issue.details is not None
    assert issue.details["candidate_path"] == storage_root
    assert issue.details["path_extension_format"] == "csv"
    assert issue.details["physical_layout_format_kind"] == "parquet"

    target = context.query_target_candidates[0]
    assert target.template_source == "storage_access_location"
    assert target.candidate_path == storage_root
    assert target.candidate_path_status == "orientation_only"
    assert target.direct_review_required is True
    assert [reason.code for reason in target.direct_review_reasons] == [
        "physical_layout_path_extension_mismatch"
    ]
    assert context.query_target_decision.status == "candidate_needs_review"
    assert context.query_target_decision.reason_codes == [
        "physical_layout_path_extension_mismatch"
    ]

    plan = db.draft_query_plan(dataset)

    assert plan.scan.uri_template == storage_root
    assert plan.scan.file_format == "Parquet"
    assert plan.scan.function == "read_parquet"
    assert plan.review_gate.ready_for_execution_attempt is False
    assert plan.review_gate.blocking_reason_codes == [
        "physical_layout_path_extension_mismatch"
    ]
    assert plan.review_gate.execution_attempt_blocking_reason_codes == [
        "physical_layout_path_extension_mismatch"
    ]
    assert plan.scan.execution_attempt_ready is False
    assert plan.handoff_kind == "metadata_review_required"


def test_query_context_allows_matching_csv_extension_and_layout(
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
    layout = db.record_map_physical_layout(
        "https://example.test/project#orders_csv_layout",
        file_format="rc:CSV",
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

    assert context.readiness == "ready_for_query_planning"
    assert context.issues == []
    target = context.query_target_candidates[0]
    assert target.candidate_path == storage_root
    assert target.candidate_path_status == "ready"
    assert target.review_reasons == []

    plan = db.draft_query_plan(dataset)

    assert plan.scan.uri_template == storage_root
    assert plan.scan.file_format == "CSV"
    assert plan.scan.function == "read_csv_auto"
    assert plan.review_gate.ready_for_execution_attempt is True
    assert plan.handoff_kind == "execution_attempt_ready"


def test_describe_query_context_suggests_peer_layout_selection_actions(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    evidence = "https://example.test/project#EventsProfileEvidence"
    local_storage = db.record_map_storage_access(
        "https://example.test/project#events_local_storage",
        label="Events local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="directory",
        storage_root=str(tmp_path / "lake"),
        path_templates=["events/current/*.csv"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    database_storage = db.record_map_storage_access(
        "https://example.test/project#events_database_storage",
        label="Events database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="analytics-prod",
        path_templates=["mart.events"],
        endpoint_profile="warehouse-prod",
        credential_reference="profile:warehouse-readonly",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    csv_layout = db.record_map_physical_layout(
        "https://example.test/project#events_csv_layout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    table_layout = db.record_map_physical_layout(
        "https://example.test/project#events_table_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Events",
        is_table=True,
        storage_accesses=[local_storage.iri, database_storage.iri],
        physical_layouts=[csv_layout.iri, table_layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_dataset_profile(
        dataset,
        summary="Events were profiled before physical planning review.",
        evidence_summary="Synthetic profile evidence for mixed storage routes.",
        evidence_sources=["test://events-profile"],
        evidence_iri=evidence,
        sample_size=12,
        sample_scope="All Events rows.",
        sample_method="Synthetic profile query.",
        row_count=12,
        update_map_snapshot=False,
    )

    context = db.describe_query_context(dataset)
    local_index, local_candidate = next(
        (index, target)
        for index, target in enumerate(context.query_target_candidates)
        if target.storage_access is not None
        and target.storage_access.iri == local_storage.iri
    )
    database_index, database_candidate = next(
        (index, target)
        for index, target in enumerate(context.query_target_candidates)
        if target.storage_access is not None
        and target.storage_access.iri == database_storage.iri
    )

    assert local_candidate.candidate_path_status == "orientation_only"
    assert database_candidate.candidate_path_status == "orientation_only"
    assert [reason.code for reason in database_candidate.direct_review_reasons] == [
        "ambiguous_physical_layout"
    ]

    selection_actions = [
        action
        for action in context.suggested_next_actions
        if action.tool == "doxabase.draft_query_plan"
        and "physical_layout_iri" in action.args
    ]
    profile_actions = [
        action
        for action in context.suggested_next_actions
        if action.tool == "doxabase.describe_profile_run"
    ]

    assert profile_actions
    assert profile_actions[0].args == {
        "dataset_iri": dataset,
        "evidence_iri": evidence,
    }

    assert {
        (
            action.args["candidate_selector"],
            action.args["physical_layout_iri"],
        )
        for action in selection_actions
    } == {
        (local_candidate.candidate_selector, csv_layout.iri),
        (database_candidate.candidate_selector, table_layout.iri),
    }
    assert all(
        not (
            action.args["candidate_selector"] == local_candidate.candidate_selector
            and action.args["physical_layout_iri"] == table_layout.iri
        )
        for action in selection_actions
    )
    assert all(
        not (
            action.args["candidate_selector"]
            == database_candidate.candidate_selector
            and action.args["physical_layout_iri"] == csv_layout.iri
        )
        for action in selection_actions
    )

    database_action = next(
        action
        for action in selection_actions
        if action.args["candidate_selector"] == database_candidate.candidate_selector
        and action.args["physical_layout_iri"] == table_layout.iri
    )
    database_plan = db.draft_query_plan(**database_action.args)

    assert database_plan.selected_candidate is not None
    assert database_plan.selected_candidate.storage_access is not None
    assert database_plan.selected_candidate.storage_access.iri == database_storage.iri
    assert database_plan.selected_candidate.direct_review_required is False
    assert database_plan.scan.relation_identifier == "mart.events"
    assert database_plan.scan.connection_reference == "analytics-prod"
    assert database_plan.scan.physical_layout is not None
    assert database_plan.scan.physical_layout.iri == table_layout.iri
    assert "ambiguous_physical_layout" not in (
        database_plan.review_gate.all_issue_codes
    )
    assert "physical_layout_storage_protocol_mismatch" not in (
        database_plan.review_gate.all_issue_codes
    )
    assert database_plan.handoff_kind == "database_relation_handoff"

    database_csv_plan = db.draft_query_plan(
        dataset,
        candidate_index=database_index,
        physical_layout_iri=csv_layout.iri,
    )

    assert database_csv_plan.selected_candidate is not None
    assert database_csv_plan.selected_candidate.direct_review_required is True
    assert database_csv_plan.scan.physical_layout is not None
    assert database_csv_plan.scan.physical_layout.iri == csv_layout.iri
    assert database_csv_plan.scan.file_format == "CSV"
    assert database_csv_plan.review_gate.blocking_reason_codes == [
        "physical_layout_storage_protocol_mismatch"
    ]
    assert database_csv_plan.review_gate.direct_blocking_reason_codes == [
        "physical_layout_storage_protocol_mismatch"
    ]
    assert database_csv_plan.handoff_kind == "metadata_review_required"

    local_table_plan = db.draft_query_plan(
        dataset,
        candidate_index=local_index,
        physical_layout_iri=table_layout.iri,
    )

    assert local_table_plan.selected_candidate is not None
    assert local_table_plan.selected_candidate.direct_review_required is True
    assert local_table_plan.scan.physical_layout is not None
    assert local_table_plan.scan.physical_layout.iri == table_layout.iri
    assert local_table_plan.review_gate.blocking_reason_codes == [
        "physical_layout_storage_protocol_mismatch"
    ]
    assert local_table_plan.handoff_kind == "metadata_review_required"


def test_database_storage_does_not_treat_partition_template_as_relation(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    partition_template = "events/dt={date}/region={region}/*.parquet"
    storage = db.record_map_storage_access(
        "https://example.test/project#events_database_storage",
        label="Events database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="analytics-prod",
        path_templates=["mart.events", "mart.events_archive"],
        endpoint_profile="warehouse-prod",
        credential_reference="profile:warehouse-readonly",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#events_table_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    partition = db.record_map_partition_scheme(
        "https://example.test/project#events_partition_scheme",
        label="Events file partitioning",
        path_template=partition_template,
        layout_verification_status="rc:VerifiedByQueryLayout",
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

    assert context.readiness == "needs_review"
    issue = next(
        issue
        for issue in context.issues
        if issue.code == "database_relation_template_source_mismatch"
    )
    assert issue.resource is not None
    assert issue.resource.iri == storage.iri
    assert context.suggested_repair_action_group_count == 1
    repair_group = context.suggested_repair_action_groups[0]
    assert repair_group.issue_index == context.issues.index(issue)
    assert repair_group.issue_code == "database_relation_template_source_mismatch"
    assert repair_group.issue_resource is not None
    assert repair_group.issue_resource.iri == storage.iri
    assert repair_group.repair_action_type == (
        "move_database_relation_template_to_storage_access"
    )
    assert repair_group.repair_context["source"]["subject_iri"] == partition.iri
    assert repair_group.repair_context["target"]["storage_access_iri"] == storage.iri
    assert [action["action_type"] for action in repair_group.actions] == [
        "remove_misplaced_source_template",
        "add_reviewed_relation_template",
    ]
    assert repair_group.action_status_counts == {
        "pending_review": 1,
        "already_satisfied": 1,
    }
    assert repair_group.actions[0]["required_extra_arguments"] == ["rationale"]
    assert repair_group.actions[1]["required_extra_arguments"] == [
        "object",
        "rationale",
    ]
    assert repair_group.actions[1]["action_status"] == "already_satisfied"
    assert repair_group.actions[1]["placeholder_fields"] == ["object"]
    assert repair_group.actions[1]["reviewed_value_fields"] == ["object"]
    assert repair_group.pending_required_extra_arguments == ["rationale"]
    partition_target_index, partition_target = next(
        (index, target)
        for index, target in enumerate(context.query_target_candidates)
        if target.template_source == "partition_scheme"
    )
    assert partition_target.source_resource.iri == partition.iri
    assert partition_target.storage_access is not None
    assert partition_target.storage_access.iri == storage.iri
    assert partition_target.template == partition_template
    assert partition_target.candidate_path is None
    assert partition_target.relation_identifier is None
    assert partition_target.connection_reference == "analytics-prod"
    assert partition_target.composition == "unresolved"
    assert partition_target.candidate_path_status == "unresolved"
    assert partition_target.direct_review_required is True
    assert [reason.code for reason in partition_target.direct_review_reasons] == [
        "database_relation_template_source_mismatch"
    ]

    relation_target_index, relation_target = next(
        (index, target)
        for index, target in enumerate(context.query_target_candidates)
        if target.template_source == "storage_access"
        and target.relation_identifier == "mart.events"
    )
    assert relation_target.source_resource.iri == storage.iri
    assert relation_target.candidate_path == "mart.events"
    assert relation_target.relation_identifier == "mart.events"
    assert relation_target.connection_reference == "analytics-prod"
    assert relation_target.composition == "database_connection_and_relation"
    assert relation_target.candidate_path_status == "ready"
    assert relation_target.review_required is False
    assert relation_target.direct_review_required is False
    assert context.query_target_decision.candidate_index == relation_target_index
    flat_tools = {action.tool.removeprefix("doxabase.") for action in context.suggested_next_actions}
    assert "record_map_storage_access" not in flat_tools
    assert "stage_map_assertion_change" not in flat_tools
    assert flat_tools == {"draft_query_plan"}

    plan = db.draft_query_plan(dataset)

    assert plan.selected_candidate is not None
    assert plan.selected_candidate.template_source == "storage_access"
    assert plan.scan.relation_identifier == "mart.events"
    assert plan.scan.uri_template is None
    assert plan.review_gate.all_issue_codes == [
        "database_relation_template_source_mismatch"
    ]
    assert "query_context_has_other_blockers" in plan.review_gate.blocking_reason_codes
    assert plan.handoff_summary.primary_repair_issue_index == context.issues.index(
        issue
    )
    assert plan.handoff_summary.primary_repair_issue_code == (
        "database_relation_template_source_mismatch"
    )
    assert plan.handoff_summary.primary_repair_group_action_type == (
        "move_database_relation_template_to_storage_access"
    )
    assert plan.handoff_summary.primary_repair_action_index == 0
    assert plan.handoff_summary.primary_repair_action_type == (
        "remove_misplaced_source_template"
    )
    assert plan.handoff_summary.primary_repair_tool == (
        "doxabase.stage_map_assertion_change"
    )
    assert plan.handoff_summary.primary_repair_required_extra_arguments == [
        "rationale"
    ]
    assert partition_template not in {
        plan.selected_candidate.candidate_path,
        plan.scan.relation_identifier,
    }

    explicit_bad_plan = db.draft_query_plan(
        dataset,
        candidate_index=partition_target_index,
    )

    assert explicit_bad_plan.selected_candidate is not None
    assert explicit_bad_plan.selected_candidate.template_source == "partition_scheme"
    assert explicit_bad_plan.selected_candidate.relation_identifier is None
    assert explicit_bad_plan.scan.relation_identifier is None
    assert explicit_bad_plan.scan.connection_reference == "analytics-prod"
    assert explicit_bad_plan.scan.candidate_path_status == "unresolved"
    assert explicit_bad_plan.review_gate.status == "candidate_needs_review"
    assert explicit_bad_plan.review_gate.blocking_reason_codes == [
        "database_relation_template_source_mismatch"
    ]
    assert explicit_bad_plan.handoff_kind == "metadata_review_required"

    with pytest.raises(DoxaBaseError, match="matched multiple") as excinfo:
        db.draft_query_plan(dataset, storage_access_iri=storage.iri)
    error = str(excinfo.value)
    assert "connection_reference='analytics-prod'" in error
    assert "relation_identifier='mart.events'" in error
    assert "relation_identifier='mart.events_archive'" in error
    assert "candidate_path='analytics-prod'" not in error


def test_review_gated_query_target_decision_flags_unselected_route_intent(
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
    postgres_layout = db.record_map_physical_layout(
        "https://example.test/project#orders_postgres_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    sqlite_layout = db.record_map_physical_layout(
        "https://example.test/project#orders_sqlite_layout",
        file_format="rc:SQLiteTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        storage_accesses=[sample_storage.iri, production_storage.iri],
        physical_layouts=[postgres_layout.iri, sqlite_layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    production_candidate = next(
        candidate
        for candidate in context.query_target_candidates
        if candidate.storage_access is not None
        and candidate.storage_access.iri == production_storage.iri
    )
    production_index = context.query_target_candidates.index(production_candidate)
    assert context.query_target_decision.candidate_index is not None
    automatic_candidate = context.query_target_candidates[
        context.query_target_decision.candidate_index
    ]
    assert automatic_candidate.storage_access is not None
    assert automatic_candidate.storage_access.iri == sample_storage.iri
    assert context.query_target_decision.status == "candidate_needs_review"
    assert context.query_target_decision.route_intent_review_candidate_indexes == [
        production_index
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


def test_database_storage_does_not_treat_dataset_template_as_relation(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    dataset_template = "events/current/*.parquet"
    storage = db.record_map_storage_access(
        "https://example.test/project#events_database_storage",
        label="Events database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="analytics-prod",
        endpoint_profile="warehouse-prod",
        credential_reference="profile:warehouse-readonly",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#events_table_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Events",
        is_table=True,
        path_templates=[dataset_template],
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "needs_review"
    target = context.query_target_candidates[0]
    issue = context.issues[0]
    assert issue.details is not None
    repair_hint = issue.details["repair_hint"]
    assert repair_hint["source_subject_iri"] == dataset
    assert repair_hint["misplaced_template_subject_iri"] == dataset
    assert repair_hint["misplaced_template_source"] == "dataset"
    assert repair_hint["misplaced_template"] == dataset_template
    assert repair_hint["source"] == {
        "subject_iri": dataset,
        "template_source": "dataset",
        "predicate": "rc:pathTemplate",
        "template": dataset_template,
    }
    assert repair_hint["target"] == {
        "storage_access_iri": storage.iri,
        "predicate": "rc:pathTemplate",
        "required_template_source": "storage_access",
    }
    assert repair_hint["actions"][0]["arguments_template"] == {
        "subject": storage.iri,
        "predicate": "rc:pathTemplate",
        "object": "<reviewed_database_relation_identifier>",
        "object_kind": "literal",
        "change_kind": "add",
        "graph": "map",
    }
    assert repair_hint["actions"][0]["source_subject_iri"] == dataset
    assert repair_hint["actions"][0]["misplaced_template_subject_iri"] == dataset
    assert repair_hint["actions"][0]["misplaced_template"] == dataset_template
    assert repair_hint["actions"][0]["required_extra_arguments"] == [
        "object",
        "rationale",
    ]
    assert repair_hint["actions"][0]["placeholder_fields"] == ["object"]
    assert repair_hint["actions"][0]["reviewed_value_fields"] == ["object"]
    assert repair_hint["actions"][0]["rationale_template"] == (
        f"Reviewed database relation identifier for {storage.iri}."
    )
    assert repair_hint["actions"][1]["args"] == {
        "subject": dataset,
        "predicate": "rc:pathTemplate",
        "object": dataset_template,
        "object_kind": "literal",
        "change_kind": "remove",
        "graph": "map",
    }
    assert repair_hint["actions"][1]["source_subject_iri"] == dataset
    assert repair_hint["actions"][1]["misplaced_template_subject_iri"] == dataset
    assert repair_hint["actions"][1]["misplaced_template"] == dataset_template
    assert repair_hint["actions"][1]["required_extra_arguments"] == ["rationale"]
    assert repair_hint["actions"][1]["rationale_template"] == (
        "Reviewed source template as misplaced database relation metadata."
    )
    assert target.template_source == "dataset"
    assert target.candidate_path is None
    assert target.relation_identifier is None
    assert target.connection_reference == "analytics-prod"
    assert target.composition == "unresolved"
    assert target.candidate_path_status == "unresolved"
    assert [reason.code for reason in target.direct_review_reasons] == [
        "database_relation_template_source_mismatch"
    ]
    assert [action.tool.removeprefix("doxabase.") for action in context.suggested_next_actions] == [
        "draft_query_plan",
    ]

    plan = db.draft_query_plan(dataset)

    assert plan.selected_candidate is not None
    assert plan.selected_candidate.template_source == "dataset"
    assert plan.scan.uri_template is None
    assert plan.scan.relation_identifier is None
    assert plan.scan.connection_reference == "analytics-prod"
    assert plan.review_gate.blocking_reason_codes == [
        "database_relation_template_source_mismatch"
    ]
    assert plan.handoff_kind == "metadata_review_required"

    db.record_map_storage_access(storage.iri, path_templates=["mart.events"])
    add_only_context = db.describe_query_context(dataset)
    assert any(
        issue.code == "database_relation_template_source_mismatch"
        for issue in add_only_context.issues
    )
    assert any(
        candidate.template_source == "storage_access"
        and candidate.relation_identifier == "mart.events"
        for candidate in add_only_context.query_target_candidates
    )

    db.record_map_dataset(dataset, path_templates=[])
    repaired_context = db.describe_query_context(dataset)
    assert not any(
        issue.code == "database_relation_template_source_mismatch"
        for issue in repaired_context.issues
    )
    assert any(
        candidate.template_source == "storage_access"
        and candidate.relation_identifier == "mart.events"
        and candidate.direct_review_required is False
        for candidate in repaired_context.query_target_candidates
    )


@pytest.mark.parametrize("location_kind", ["object", "connection"])
def test_database_root_only_storage_requires_relation_template(
    tmp_path: Path,
    location_kind: str,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_database_storage",
        label="Orders database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind=location_kind,
        storage_root="warehouse-prod",
        endpoint_profile="warehouse-prod",
        credential_reference="profile:warehouse-readonly",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#orders_table_layout",
        file_format="rc:PostgreSQLTable",
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

    assert context.readiness == "needs_review"
    assert context.issues[0].code == "database_relation_template_missing"
    details = context.issues[0].details
    assert details is not None
    assert {
        key: details[key]
        for key in [
            "storage_access_iri",
            "storage_protocol_iri",
            "storage_root",
            "location_kind",
            "allowed_relation_template_sources",
        ]
    } == {
        "storage_access_iri": storage.iri,
        "storage_protocol_iri": RC + "DatabaseStorage",
        "storage_root": "warehouse-prod",
        "location_kind": location_kind,
        "allowed_relation_template_sources": ["storage_access"],
    }
    repair_hint = details["repair_hint"]
    assert repair_hint["action_type"] == "record_database_relation_template"
    assert repair_hint["requires_review"] is True
    assert context.suggested_repair_action_group_count == 1
    repair_group = context.suggested_repair_action_groups[0]
    assert repair_group.issue_index == 0
    assert repair_group.issue_code == "database_relation_template_missing"
    assert repair_group.issue_resource is not None
    assert repair_group.issue_resource.iri == storage.iri
    assert repair_group.repair_action_type == "record_database_relation_template"
    assert repair_group.repair_context["source"]["storage_access_iri"] == storage.iri
    assert repair_group.repair_context["target"]["required_template_source"] == (
        "storage_access"
    )
    assert [action["action_type"] for action in repair_group.actions] == [
        "add_reviewed_relation_template"
    ]
    assert {
        action.tool.removeprefix("doxabase.") for action in context.suggested_next_actions
    } == {"draft_query_plan"}
    assert repair_hint["source"] == {
        "storage_access_iri": storage.iri,
        "storage_root": "warehouse-prod",
        "location_kind": location_kind,
    }
    assert repair_hint["target"] == {
        "storage_access_iri": storage.iri,
        "predicate": "rc:pathTemplate",
        "required_template_source": "storage_access",
    }
    assert repair_hint["candidate_relation_identifier"]["requires_review"] is True
    add_action = repair_hint["actions"][0]
    assert add_action["tool"] == "doxabase.stage_map_assertion_change"
    assert add_action["tool"] == "doxabase.stage_map_assertion_change"
    assert add_action["required_extra_arguments"] == ["object", "rationale"]
    assert add_action["placeholder_fields"] == ["object"]
    assert add_action["reviewed_value_fields"] == ["object"]
    assert add_action["arguments_template"] == {
        "subject": storage.iri,
        "predicate": "rc:pathTemplate",
        "object": "<reviewed_database_relation_identifier>",
        "object_kind": "literal",
        "change_kind": "add",
        "graph": "map",
    }
    target = context.query_target_candidates[0]
    assert target.template_source == "storage_access_location"
    assert target.location_kind == location_kind
    assert target.candidate_path == "warehouse-prod"
    assert target.relation_identifier is None
    assert target.connection_reference == "warehouse-prod"
    assert target.composition == "database_connection_as_candidate"
    assert target.candidate_path_status == "orientation_only"
    assert target.direct_review_required is True
    assert [reason.code for reason in target.direct_review_reasons] == [
        "database_relation_template_missing"
    ]
    assert context.query_target_decision.status == "candidate_needs_review"
    assert context.query_target_decision.candidate_path_status == "orientation_only"
    assert context.query_target_decision.selected_candidate_direct_clean is False
    assert context.query_target_decision.reason_codes == [
        "database_relation_template_missing"
    ]

    plan = db.draft_query_plan(dataset)

    assert plan.scan.uri_template is None
    assert plan.scan.relation_identifier is None
    assert plan.scan.connection_reference == "warehouse-prod"
    assert plan.review_gate.blocking_reason_codes == [
        "database_relation_template_missing"
    ]
    assert plan.handoff_kind == "metadata_review_required"


@pytest.mark.parametrize("location_kind", [None, "directory", "prefix", "connection"])
def test_describe_query_context_demotes_non_object_root_only_location(
    tmp_path: Path,
    location_kind: str | None,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage_root = str(tmp_path / "orders")
    storage_kwargs = {
        "label": "Orders local storage",
        "storage_protocol": "rc:LocalFilesystemStorage",
        "storage_root": storage_root,
        "layout_verification_status": "rc:VerifiedByListingLayout",
    }
    if location_kind is not None:
        storage_kwargs["location_kind"] = location_kind
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_local_storage",
        **storage_kwargs,
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

    assert context.readiness == "needs_review"
    assert {issue.code for issue in context.issues} == {
        "storage_location_kind_needs_path_template"
    }
    details = context.issues[0].details
    assert details is not None
    assert {
        key: details[key]
        for key in [
            "storage_access_iri",
            "storage_protocol_iri",
            "storage_root",
            "location_kind",
            "allowed_template_sources",
        ]
    } == {
        "storage_access_iri": storage.iri,
        "storage_protocol_iri": RC + "LocalFilesystemStorage",
        "storage_root": storage_root,
        "location_kind": location_kind,
        "allowed_template_sources": ["storage_access"],
    }
    repair_hint = details["repair_hint"]
    assert repair_hint["action_type"] == (
        "record_file_object_path_template_or_exact_root"
    )
    assert repair_hint["choice_mode"] == "choose_one"
    assert repair_hint["requires_review"] is True
    assert repair_hint["source"] == {
        "storage_access_iri": storage.iri,
        "storage_root": storage_root,
        "location_kind": location_kind,
    }
    assert repair_hint["target"] == {
        "storage_access_iri": storage.iri,
        "predicate": "rc:pathTemplate",
        "required_template_source": "storage_access",
    }
    assert [action["action_type"] for action in repair_hint["actions"]] == [
        "add_reviewed_path_template",
        "set_root_as_exact_object_location",
    ]
    add_action = repair_hint["actions"][0]
    assert add_action["tool"] == "doxabase.stage_map_assertion_change"
    assert add_action["arguments_template"] == {
        "subject": storage.iri,
        "predicate": "rc:pathTemplate",
        "object": "<reviewed_relative_path_template>",
        "object_kind": "literal",
        "change_kind": "add",
        "graph": "map",
    }
    assert add_action["required_extra_arguments"] == ["object", "rationale"]
    assert add_action["placeholder_fields"] == ["object"]
    assert add_action["reviewed_value_fields"] == ["object"]
    exact_root_action = repair_hint["actions"][1]
    assert exact_root_action["args"] == {
        "subject": storage.iri,
        "predicate": "rc:locationKind",
        "object": "object",
        "object_kind": "literal",
        "change_kind": "add" if location_kind is None else "replace",
        "graph": "map",
    }
    assert context.suggested_repair_action_group_count == 1
    repair_group = context.suggested_repair_action_groups[0]
    assert repair_group.issue_index == 0
    assert repair_group.issue_code == "storage_location_kind_needs_path_template"
    assert repair_group.issue_resource is not None
    assert repair_group.issue_resource.iri == storage.iri
    assert repair_group.repair_action_type == (
        "record_file_object_path_template_or_exact_root"
    )
    assert repair_group.choice_mode == "choose_one"
    assert [action["action_type"] for action in repair_group.actions] == [
        "add_reviewed_path_template",
        "set_root_as_exact_object_location",
    ]
    assert context.storage_accesses[0].location_kind == location_kind
    target = context.query_target_candidates[0]
    assert target.template_source == "storage_access_location"
    assert target.location_kind == location_kind
    assert target.candidate_path == storage_root
    assert target.candidate_path_status == "orientation_only"
    assert target.review_required is True
    assert target.direct_review_required is True
    assert [reason.code for reason in target.review_reasons] == [
        "storage_location_kind_needs_path_template"
    ]
    assert [reason.code for reason in target.direct_review_reasons] == [
        "storage_location_kind_needs_path_template"
    ]
    assert context.query_target_decision.status == "candidate_needs_review"
    assert context.query_target_decision.candidate_index == 0
    assert context.query_target_decision.candidate_path == storage_root
    assert context.query_target_decision.candidate_path_status == "orientation_only"
    assert context.query_target_decision.direct_review_required is True
    assert context.query_target_decision.selected_candidate_direct_clean is False
    assert context.query_target_decision.reason_codes == [
        "storage_location_kind_needs_path_template"
    ]
    plan = db.draft_query_plan(dataset)
    assert plan.scan.template_lineage is not None
    assert (
        "Candidate storage root comes from storage access Orders local storage."
        in plan.scan.template_lineage
    )
    assert "Template comes from storage_access_location" not in plan.scan.template_lineage


def test_query_target_storage_owned_template_warnings_do_not_bleed_to_siblings(
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
    layout = db.record_map_physical_layout(
        "https://example.test/project#feeds_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Feeds",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "needs_review"
    assert any(
        issue.code == "storage_protocol_location_mismatch"
        and "path template from Feeds HTTPS access" in issue.message
        for issue in context.issues
    )
    clean_target = next(
        target
        for target in context.query_target_candidates
        if target.template == "feeds/clean/date={date}.parquet"
    )
    assert clean_target.candidate_path == (
        "https://cdn.example.test/lake/feeds/clean/date={date}.parquet"
    )
    assert clean_target.candidate_path_status == "ready"
    assert clean_target.review_required is False
    assert clean_target.review_reasons == []
    assert clean_target.direct_review_required is False
    assert clean_target.direct_review_reasons == []

    bad_target = next(
        target
        for target in context.query_target_candidates
        if target.template == "s3://wrong-bucket/feeds/*.parquet"
    )
    assert bad_target.candidate_path_status == "orientation_only"
    assert any(
        reason.code == "storage_protocol_location_mismatch"
        and "path template from Feeds HTTPS access" in reason.message
        for reason in bad_target.review_reasons
    )


def test_query_target_s3_storage_owned_template_warnings_do_not_bleed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Fleet"
    storage = db.record_map_storage_access(
        "https://example.test/project#fleet_s3_storage",
        label="Fleet S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        bucket_name="fleet-lake",
        key_prefix="warehouse",
        path_templates=[
            "fleet/storage-ok/dt={date}.parquet",
            "s3://wrong-bucket/raw/fleet/*.parquet",
            "warehouse/fleet/repeated/dt={date}.parquet",
        ],
        credential_reference="profile:fleet-readonly",
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#fleet_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Fleet",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)

    assert context.readiness == "needs_review"
    clean_target = next(
        target
        for target in context.query_target_candidates
        if target.template == "fleet/storage-ok/dt={date}.parquet"
    )
    assert clean_target.candidate_path == (
        "s3://fleet-lake/warehouse/fleet/storage-ok/dt={date}.parquet"
    )
    assert clean_target.candidate_path_status == "ready"
    assert clean_target.review_required is False
    assert clean_target.review_reasons == []

    wrong_bucket = next(
        target
        for target in context.query_target_candidates
        if target.template == "s3://wrong-bucket/raw/fleet/*.parquet"
    )
    assert wrong_bucket.candidate_path_status == "orientation_only"
    assert wrong_bucket.direct_review_required is True
    assert any(
        reason.code == "storage_protocol_location_mismatch"
        and "bucket_name" in reason.message
        for reason in wrong_bucket.direct_review_reasons
    )
    repeated_prefix = next(
        target
        for target in context.query_target_candidates
        if target.template == "warehouse/fleet/repeated/dt={date}.parquet"
    )
    assert repeated_prefix.candidate_path_status == "orientation_only"
    assert repeated_prefix.direct_review_required is True
    assert any(
        reason.code == "storage_protocol_location_mismatch"
        and "repeat recorded key_prefix" in reason.message
        for reason in repeated_prefix.direct_review_reasons
    )

    plan = db.draft_query_plan(dataset)
    assert plan.selected_candidate is not None
    assert plan.selected_candidate.template == "fleet/storage-ok/dt={date}.parquet"
    assert plan.review_gate.executable_without_review is False
    assert plan.review_gate.blocking_reason_codes == [
        "query_context_has_other_blockers"
    ]
    assert plan.review_gate.reason_codes == ["query_context_has_other_blockers"]
    assert plan.handoff_kind == "context_review_required"
    assert context.suggested_next_actions[0].tool == "doxabase.draft_query_plan"
    assert context.suggested_next_actions[0].args == {
        "iri": dataset,
        "candidate_selector": context.query_target_candidates[
            context.query_target_decision.candidate_index
        ].candidate_selector,
        "allow_context_blocked_candidate": True,
    }


def test_describe_query_context_warns_when_s3_root_conflicts_with_bucket_prefix(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_s3_storage",
        label="Orders S3 access",
        storage_protocol="rc:S3CompatibleStorage",
        storage_root="s3://orders-lake/raw/orders",
        bucket_name="events-lake",
        key_prefix="curated",
        credential_reference="profile:orders-readonly",
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

    assert context.readiness == "needs_review"
    issue = next(
        issue
        for issue in context.issues
        if issue.code == "storage_protocol_location_mismatch"
        and issue.resource is not None
        and issue.resource.iri == storage.iri
    )
    assert issue.details is not None
    assert issue.details["storage_root"] == "s3://orders-lake/raw/orders"
    assert issue.details["bucket_name"] == "events-lake"
    assert issue.details["key_prefix"] == "curated"
    mismatch_reasons = issue.details["mismatch_reasons"]
    assert any(
        "storage_root bucket does not match recorded bucket_name" in reason
        for reason in mismatch_reasons
    )
    assert any(
        "storage_root key does not start with recorded key_prefix" in reason
        for reason in mismatch_reasons
    )
    action_types = {
        action["action_type"]
        for action in issue.details["repair_hint"]["actions"]
    }
    assert {
        "set_reviewed_storage_root",
        "set_reviewed_bucket_name",
        "set_reviewed_key_prefix",
    } <= action_types


def test_validation_rejects_data_assets_in_relationship_column_predicates(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:raw_files a rc:Dataset ;
            rc:columnName "raw_files" .
        ex:clean_files__filename a rc:Column ;
            rc:columnName "filename" .
        ex:bad_asset_derivation a rc:Derivation ;
            rc:sourceColumn ex:raw_files ;
            rc:derivedColumn ex:clean_files__filename .
        """,
        graph="map",
    )

    validation = db.validate_graph(scope="all")

    assert not validation.conforms
    assert "not data asset resources" in validation.report_text


def test_validation_rejects_unmapped_relationship_column_predicates(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:messages a rc:Dataset, rc:Table .
        ex:body_preview_derivation a rc:Derivation ;
            rc:sourceColumn ex:messages__body ;
            rc:derivedColumn ex:messages__body_top .
        """,
        graph="map",
    )

    validation = db.validate_graph(scope="all")

    assert not validation.conforms
    assert validation.result_count >= 2
    assert "columnName evidence" in validation.report_text


def test_describe_dataset_returns_all_partition_columns(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/project#"
    table = f"{base}orders"
    order_date = f"{base}orders__order_date"
    region = f"{base}orders__region"
    partition_scheme = f"{base}orders_daily_region_partitioning"

    db.record_map_dataset(table, label="Orders", is_table=True)
    db.record_map_column(
        order_date,
        table_iri=table,
        column_name="order_date",
        physical_type="rc:Date",
    )
    db.record_map_column(
        region,
        table_iri=table,
        column_name="region",
        physical_type="rc:Varchar",
    )
    db.record_map_partition_scheme(
        partition_scheme,
        partition_columns=[region, order_date],
        granularity="rc:Daily",
        datasets=[table],
    )

    partition_description = db.describe_dataset(table).partition_schemes[0]

    assert {column.iri for column in partition_description.partition_columns} == {
        order_date,
        region,
    }
    assert partition_description.partition_column is not None
    assert partition_description.partition_column.iri in {order_date, region}


def test_record_query_result_writes_query_source_evidence(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(dataset, label="Orders", is_table=True)

    result = db.record_query_result(
        summary="Orders paid-count query returned two rows.",
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path="queries/orders_paid_count.sql",
        query_source_section="paid-count aggregate",
        start_line=3,
        end_line=5,
        query_hash="sha256:abc123",
        result_sources=["/tmp/orders-paid-count.json"],
        scanned_source_paths=["warehouse/orders.csv"],
        sample_size=3,
        sample_scope="All rows in the scratch Orders CSV.",
        sample_method="External read-only aggregate query.",
        row_count=2,
        profile_metrics=[
            {
                "metric": "rc:MaximumValue",
                "value": "31.75",
                "datatype": "xsd:decimal",
            }
        ],
    )

    assert result.observation_type == "profile"
    assert result.execution_status == "succeeded"
    assert result.engine == "python-csv"
    assert result.query_hash == "sha256:abc123"
    assert result.source_span_iri is not None
    assert result.scanned_source_paths == ["warehouse/orders.csv"]
    assert len(result.scanned_source_span_iris) == 1
    assert result.evidence_triples > result.source_span_triples > 0
    assert [action.tool.removeprefix("doxabase.") for action in result.suggested_next_actions] == [
        "describe_profile_run",
        "get_context_graph",
        "describe_query_context",
    ]
    assert result.suggested_next_actions[0].args == {
        "dataset_iri": dataset,
        "evidence_iri": result.evidence_iri,
    }
    assert result.suggested_next_actions[1].args == {
        "seed_iris": [result.evidence_iri],
        "profile": "resource_brief",
    }
    assert result.suggested_next_actions[2].args == {"iri": dataset}
    assert db.validate_graph(scope="all").conforms

    evidence = db.describe_resource(result.evidence_iri, graph="evidence")
    assert any(
        triple.predicate == RC + "sourceSpan"
        and triple.object == result.source_span_iri
        for triple in evidence.outgoing
    )
    assert any(
        triple.predicate == RC + "sourceSpan"
        and triple.object == result.scanned_source_span_iris[0]
        for triple in evidence.outgoing
    )
    outgoing = {(triple.predicate, triple.object) for triple in evidence.outgoing}
    assert (RC + "queryExecutionStatus", "succeeded") in outgoing
    assert (RC + "queryEngine", "python-csv") in outgoing
    assert (RC + "queryHash", "sha256:abc123") in outgoing
    source_span = db.describe_resource(result.source_span_iri, graph="evidence")
    span_outgoing = {
        (triple.predicate, triple.object) for triple in source_span.outgoing
    }
    assert (RC + "sourcePath", "queries/orders_paid_count.sql") in span_outgoing
    assert (RC + "sourceKind", RC + "QuerySource") in span_outgoing
    scanned_span = db.describe_resource(
        result.scanned_source_span_iris[0],
        graph="evidence",
    )
    scanned_span_outgoing = {
        (triple.predicate, triple.object) for triple in scanned_span.outgoing
    }
    assert (RC + "sourcePath", "warehouse/orders.csv") in scanned_span_outgoing
    assert (RC + "sourceKind", RC + "DataSampleSource") in scanned_span_outgoing

    matches = db.search("paid-count", graph="observations")
    assert result.observation_iri in {match.iri for match in matches.matches}


def test_record_query_result_preserves_database_relation_source_handle(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WarehouseOrders"
    storage = db.record_map_storage_access(
        "https://example.test/project#warehouse_orders_database_storage",
        label="Warehouse orders database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        path_templates=["mart.orders"],
        endpoint_profile="warehouse-prod",
        credential_reference="profile:warehouse-readonly",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#warehouse_orders_table_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Warehouse orders",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    plan = db.draft_query_plan(dataset)

    assert plan.handoff_kind == "database_relation_handoff"
    assert plan.scan.relation_identifier == "mart.orders"
    assert plan.scan.connection_reference == "warehouse-prod"
    assert plan.scan.uri_template is None

    relation_handle = (
        f"{plan.scan.connection_reference}:{plan.scan.relation_identifier}"
    )
    result = db.record_query_result(
        summary=(
            "Warehouse Orders status aggregate ran through an external "
            "database client after the database relation handoff."
        ),
        observed_asset=dataset,
        execution_status="succeeded",
        engine="external-postgres-client",
        query_source_path=str(tmp_path / "orders_status_summary.sql"),
        result_sources=[str(tmp_path / "orders_status_summary.result.json")],
        scanned_source_handles=[relation_handle],
    )

    assert result.observation_type == "observation"
    assert result.scanned_source_paths == []
    assert result.scanned_source_handles == [relation_handle]
    assert result.scanned_source_span_iris == []
    assert [action.tool.removeprefix("doxabase.") for action in result.suggested_next_actions] == [
        "get_context_graph",
        "describe_query_context",
    ]
    assert result.suggested_next_actions[0].args == {
        "seed_iris": [result.evidence_iri],
        "profile": "resource_brief",
    }
    evidence = db.describe_resource(result.evidence_iri, graph="evidence")
    evidence_outgoing = {
        (triple.predicate, triple.object) for triple in evidence.outgoing
    }
    assert (RC + "scannedSourceHandle", relation_handle) in evidence_outgoing
    evidence_slice = db.get_context_graph(
        **result.suggested_next_actions[0].args,
        max_triples=80,
    )
    assert result.evidence_iri in {
        resource.iri for resource in evidence_slice.resources
    }
    assert any(
        triple.predicate == RC + "scannedSourceHandle"
        and triple.object == relation_handle
        for triple in evidence_slice.triples
    )
    assert db.validate_graph(scope="all").conforms


def test_record_query_result_rejects_conflicting_source_span_reuse_without_mutation(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    source_span = "https://example.test/evidence#orders-paid-count-query-span"
    db.record_map_dataset(dataset, label="Orders", is_table=True)

    first = db.record_query_result(
        summary="Orders paid-count query returned two rows.",
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path="queries/orders_paid_count.sql",
        query_source_section="paid-count aggregate",
        start_line=3,
        end_line=5,
        result_sources=["/tmp/orders-paid-count.json"],
        source_span_iri=source_span,
    )
    assert first.source_span_iri == source_span
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match="source_span_iri.*conflicting"):
        db.record_query_result(
            summary="Orders paid-count rerun used a different query file.",
            observed_asset=dataset,
            execution_status="succeeded",
            engine="python-csv",
            query_source_path="queries/orders_paid_count_v2.sql",
            query_source_section="paid-count aggregate",
            start_line=3,
            end_line=5,
            result_sources=["/tmp/orders-paid-count-v2.json"],
            source_span_iri=source_span,
        )

    assert _mutable_graph_counts(db) == before_counts
    assert db.validate_graph(scope="all").conforms

    reused = db.record_query_result(
        summary="Orders paid-count query reran from the same source range.",
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path="queries/orders_paid_count.sql",
        query_source_section="paid-count aggregate",
        start_line=3,
        end_line=5,
        result_sources=["/tmp/orders-paid-count-repeat.json"],
        source_span_iri=source_span,
    )

    assert reused.source_span_iri == source_span
    assert db.validate_graph(scope="all").conforms


def test_record_query_result_rejects_unsourced_or_fake_failure_counts(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(
        DoxaBaseError,
        match=(
            "result_sources, query_source_path, scanned_source_paths, "
            "or scanned_source_handles"
        ),
    ):
        db.record_query_result(
            summary="Unsourced query result should not be recorded.",
        )
    with pytest.raises(DoxaBaseError, match="profile result fields"):
        db.record_query_result(
            summary="Failed query should not create profile counts.",
            execution_status="failed",
            query_source_path="queries/orders.sql",
            row_count=10,
        )

    assert _mutable_graph_counts(db) == before_counts


def test_context_slice_suggests_query_context_for_seed_operational_warnings(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Events"
    layout = db.record_map_physical_layout(
        "https://example.test/project#events_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Events",
        is_table=True,
        path_templates=["events/date={date}/*.parquet"],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context_slice = db.get_context_graph(dataset, profile="dataset_brief")

    assert context_slice.truncated is False
    assert context_slice.warnings == []
    assert context_slice.dataset_contexts[0].operational_warnings[0].code == (
        "missing_storage_access"
    )
    assert [action.tool.removeprefix("doxabase.") for action in context_slice.suggested_next_actions] == [
        "describe_query_context"
    ]
    action = context_slice.suggested_next_actions[0]
    assert action.tool == "doxabase.describe_query_context"
    assert action.args == {"iri": dataset}
    assert "missing_storage_access" in action.reason
    assert "repair hints" in action.reason

    query_context = db.describe_query_context(**action.args)
    assert query_context.readiness == "insufficient_metadata"
    assert query_context.issues[0].code == "missing_storage_access"

