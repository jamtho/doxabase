"""Split from test_doxabase_core.py (distillation Phase 2); tests verbatim."""

from tests.core.support_core import *  # noqa: F401,F403


def test_immutable_seed_graphs_reject_normal_imports(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(ImmutableGraphError):
        db.import_turtle("@prefix ex: <https://example.test/> . ex:s ex:p ex:o .", graph="base_ontology")


def test_replace_graph_triples_updates_stale_incoming_link_and_search_index(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:Orders a rc:Dataset ;
            rc:hasColumn ex:CustomerV1 .

        ex:CustomerV1 a rc:Column ;
            rc:columnName "customer_id" ;
            rdfs:label "Customer feed v1" .
        """,
        graph="map",
    )
    before_digest = db._graph_content_digest("map")

    result = db.replace_graph_triples(
        "map",
        removals="""
            @prefix ex: <https://example.test/project#> .
            @prefix rc: <https://richcanopy.org/ns/rc#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            ex:Orders rc:hasColumn ex:CustomerV1 .

            ex:CustomerV1 a rc:Column ;
                rc:columnName "customer_id" ;
                rdfs:label "Customer feed v1" .
        """,
        additions="""
            @prefix ex: <https://example.test/project#> .
            @prefix rc: <https://richcanopy.org/ns/rc#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            ex:Orders rc:hasColumn ex:CustomerV2 .

            ex:CustomerV2 a rc:Column ;
                rc:columnName "customer_id" ;
                rdfs:label "Customer feed v2" .
        """,
        expected_count=5,
    )

    assert result.before_count == 5
    assert result.after_count == 5
    assert result.same_count is True
    assert result.triples_removed == 4
    assert result.triples_added == 4
    assert result.before_digest == before_digest
    assert result.after_digest != before_digest
    assert db.search("Customer feed v1", graph="map").matches == []
    assert len(db.search("Customer feed v2", graph="map").matches) == 1


def test_column_physical_type_same_slot_drift_suggests_replacement(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    column = "https://example.test/project#orders__amount"
    db.record_map_column(column, column_name="amount")
    source = db.stage_graph_revision(
        summary="Model amount as double",
        rationale="Original physical-type proposal before an intervening map edit.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:orders__amount rc:physicalType rc:Double .
                """,
            }
        ],
        revision_anchors=[column],
    )
    db.record_map_column(column, column_name="amount", physical_type="rc:Varchar")

    check = db.check_staged_revision_apply(source.revision_iri)

    assert check.status == "conflict"
    assert check.next_action is not None
    assert check.next_action.queue == "repair_or_replace"
    assert check.next_action.tool_name == "stage_revision"
    assert check.next_action.arguments.get("kind") == "map_assertion"
    assert check.recommended_resolution is not None
    assert "same single-valued map assertion slot" in check.recommended_resolution
    action = next(
        action
        for action in check.suggested_next_actions
        if (action.tool, action.args.get("kind")) == ("doxabase.stage_revision", "map_assertion")
    )
    assert action.args["spec"]["subject"] == column
    assert action.args["spec"]["predicate"] == RC + "physicalType"
    assert action.args["spec"]["object"] == RC + "Double"
    assert action.args["spec"]["object_kind"] == "iri"
    assert "physical type" in action.reason

    repair = db.stage_map_assertion_change(**action.args["spec"])
    assert db.check_staged_revision_apply(
        repair.staged_revision.revision_iri
    ).status == "ready"


def test_column_nullable_same_slot_drift_preserves_boolean_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    column = "https://example.test/project#orders__status"
    db.record_map_column(column, column_name="status")
    source = db.stage_graph_revision(
        summary="Model status as nullable",
        rationale="Original nullable proposal before an intervening map edit.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:orders__status rc:nullable true .
                """,
            }
        ],
        revision_anchors=[column],
    )
    db.record_map_column(column, column_name="status", nullable=False)

    check = db.check_staged_revision_apply(source.revision_iri)

    assert check.status == "conflict"
    assert check.next_action is not None
    assert check.next_action.queue == "repair_or_replace"
    action = next(
        action
        for action in check.suggested_next_actions
        if (action.tool, action.args.get("kind")) == ("doxabase.stage_revision", "map_assertion")
    )
    assert action.args["spec"]["predicate"] == RC + "nullable"
    assert action.args["spec"]["object"] == "true"
    assert action.args["spec"]["object_kind"] == "literal"
    assert action.args["spec"]["object_datatype"] == str(XSD.boolean)
    assert "nullable" in action.reason

    repair = db.stage_map_assertion_change(**action.args["spec"])
    assert db.check_staged_revision_apply(
        repair.staged_revision.revision_iri
    ).status == "ready"


def test_list_entities_returns_tables_from_map(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    db.import_trig(POLYMARKET_FIXTURE)

    result = db.list_entities(type="rc:Table", graph="map", limit=20)
    labels = {row.label for row in result.entities}

    assert "AIS Daily Broadcast Positions" in labels
    assert "AIS Daily Vessel Index" in labels
    assert "Gamma Market Snapshots" in labels
    assert "Trade Events" in labels


def test_list_entities_reports_pagination_metadata(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    for index in range(3):
        db.record_map_dataset(
            f"https://example.test/project#EntityPageDataset{index}",
            label=f"Entity page dataset {index}",
            description=f"EntityPageProbe marker {index}",
            is_table=True,
        )

    page = db.list_entities(
        type="rc:Dataset",
        graph="map",
        text="EntityPageProbe",
        limit=2,
    )

    assert page.returned_count == 2
    assert page.total_count == 3
    assert page.omitted_count == 1
    assert page.has_more is True
    assert page.next_offset == 2
    assert page.suggested_next_actions[0].tool == "doxabase.list_entities"
    assert page.suggested_next_actions[0].args == {
        "limit": 2,
        "offset": 2,
        "type": "rc:Dataset",
        "graph": "map",
        "text": "EntityPageProbe",
    }

    final_page = db.list_entities(
        type="rc:Dataset",
        graph="map",
        text="EntityPageProbe",
        limit=2,
        offset=2,
    )

    assert final_page.returned_count == 1
    assert final_page.total_count == 3
    assert final_page.omitted_count == 0
    assert final_page.has_more is False
    assert final_page.next_offset is None
    assert final_page.suggested_next_actions == []


def test_search_reports_pagination_metadata(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    for index in range(3):
        db.record_map_dataset(
            f"https://example.test/project#SearchPageDataset{index}",
            label=f"Search page dataset {index}",
            description=f"SearchPageProbe marker {index}",
            is_table=True,
        )

    page = db.search("SearchPageProbe", graph="map", limit=2)

    assert page.returned_count == 2
    assert page.total_count == 3
    assert page.omitted_count == 1
    assert page.has_more is True
    assert page.next_offset == 2
    assert page.suggested_next_actions[0].tool == "doxabase.search"
    assert page.suggested_next_actions[0].args == {
        "query": "SearchPageProbe",
        "limit": 2,
        "offset": 2,
        "graph": "map",
    }

    final_page = db.search("SearchPageProbe", graph="map", limit=2, offset=2)

    assert final_page.returned_count == 1
    assert final_page.total_count == 3
    assert final_page.omitted_count == 0
    assert final_page.has_more is False
    assert final_page.next_offset is None
    assert final_page.suggested_next_actions == []


def test_describe_dataset_returns_bounded_table_context(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    description = db.describe_dataset(
        "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"
    )

    assert description.label == "AIS Daily Broadcast Positions"
    assert "https://richcanopy.org/ns/rc#Table" in description.types
    assert description.row_semantics is not None
    assert description.row_semantics.iri == RC + "EventRow"
    assert description.schema_stability is not None
    assert description.schema_stability.iri == RC + "FixedSchema"
    assert description.layout_verification_status is None
    assert description.layout_verification_note is None
    assert description.path_templates == ["broadcasts/{year}/ais-{date}.parquet"]
    assert description.partition_schemes[0].layout_verification_status is not None
    assert description.partition_schemes[0].layout_verification_status.iri == (
        RC + "GeneratedFromManifestLayout"
    )
    assert description.partition_schemes[0].layout_verification_note is not None
    assert "verify against storage listing" in (
        description.partition_schemes[0].layout_verification_note
    )
    assert len(description.storage_accesses) == 1
    storage_access = description.storage_accesses[0]
    assert storage_access.storage_protocol is not None
    assert storage_access.storage_protocol.label == "S3-compatible object storage"
    assert storage_access.storage_root == "s3://ais-noaa/"
    assert storage_access.endpoint_profile == "local-minio"
    assert storage_access.bucket_name == "ais-noaa"
    assert storage_access.region == "local"
    assert storage_access.path_style_access is True
    assert storage_access.credential_reference == "profile:ais-readonly"
    assert storage_access.access_mode is not None
    assert storage_access.access_mode.label == "read-only"
    assert {column.column_name for column in description.columns} >= {
        "mmsi",
        "timestamp",
        "h3_res15",
    }
    mmsi = next(column for column in description.columns if column.column_name == "mmsi")
    assert mmsi.physical_type is not None
    assert mmsi.physical_type.label == "INTEGER"
    assert mmsi.value_type is not None
    assert mmsi.value_type.label == "Maritime Mobile Service Identity"
    assert mmsi.nullable is True
    caveat_text = " ".join(caveat.description or "" for caveat in description.caveats)
    assert "MMSI does not reliably identify a single vessel" in caveat_text
    assert any(caveat.severity is not None for caveat in description.caveats)
    assert description.upstream_caveats == []
    assert any(
        provenance.description
        and "NOAA Marine Cadastre AIS data" in provenance.description
        for provenance in description.provenance
    )
    assert any(
        relationship.relationship_kind == RC + "Derivation"
        and relationship.derived_columns
        and relationship.derived_columns[0].iri
        == "https://richcanopy.org/example/manifest/ais#bc_timestamp"
        and relationship.derived_columns[0].column_name == "timestamp"
        and relationship.derived_columns[0].owning_dataset_label
        == "AIS Daily Broadcast Positions"
        for relationship in description.relationships
    )
    aggregation = next(
        relationship
        for relationship in description.relationships
        if relationship.relationship_kind == RC + "Aggregation"
    )
    assert aggregation.target_dataset is not None
    assert aggregation.target_dataset.iri == (
        "https://richcanopy.org/example/manifest/ais#DailyIndex"
    )
    assert [column.column_name for column in aggregation.group_by_columns] == ["mmsi"]
    aggregate_mapping = next(
        mapping
        for mapping in aggregation.aggregated_columns
        if mapping.target_column is not None
        and mapping.target_column.column_name == "distance_m"
    )
    assert {column.column_name for column in aggregate_mapping.source_columns} == {
        "latitude",
        "longitude",
    }
    assert aggregate_mapping.aggregation_function is not None
    assert aggregate_mapping.aggregation_function.label == (
        "Haversine distance from first to last position"
    )
    assert aggregate_mapping.within_group_ordering is not None
    assert aggregate_mapping.within_group_ordering.column_name == "timestamp"
    assert any(
        caveat.description
        and "MMSI does not reliably identify a single vessel" in caveat.description
        for caveat in aggregation.source_caveats
    )
    assert any(
        related.iri == "https://richcanopy.org/example/manifest/ais#DailyIndex"
        and related.relationship == "source_of_aggregation"
        for related in description.related_datasets
    )

    index_description = db.describe_dataset(
        "https://richcanopy.org/example/manifest/ais#DailyIndex"
    )
    assert index_description.layout_verification_status is not None
    assert index_description.layout_verification_status.iri == RC + "UnverifiedLayout"
    assert index_description.layout_verification_note is not None
    assert "index/{year}/ais-{date}.parquet" in (
        index_description.layout_verification_note
    )
    assert any(
        warning.code == "layout_needs_verification"
        and warning.resource is not None
        and warning.resource.iri
        == "https://richcanopy.org/example/manifest/ais#DailyIndex"
        for warning in index_description.operational_warnings
    )
    assert index_description.caveats == []
    assert any(
        caveat.description
        and "MMSI does not reliably identify a single vessel" in caveat.description
        for caveat in index_description.upstream_caveats
    )
    broadcast_group = next(
        group
        for group in index_description.related_dataset_groups
        if group.iri == "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"
    )
    broadcast_reason = next(
        reason
        for reason in broadcast_group.reasons
        if reason.relationship == "aggregated_from"
    )
    assert any(
        caveat.impact and "Grouping by MMSI may conflate" in caveat.impact
        for caveat in broadcast_reason.source_caveats
    )

    wrong_predicate_support = db.describe_assertion_support(
        "https://richcanopy.org/example/manifest/ais#DailyIndex",
        "rc:hasPartitionScheme",
        "https://richcanopy.org/example/manifest/ais#daily_date_partition",
        object_kind="iri",
    )
    assert wrong_predicate_support.assertion_present is False
    assert wrong_predicate_support.absence_note is not None
    assert "the requested predicate is absent on this subject" in (
        wrong_predicate_support.absence_note
    )
    assert "Nearby predicates on the same subject include" in (
        wrong_predicate_support.absence_note
    )
    assert "rc:partitionedBy" in wrong_predicate_support.absence_note
    partition_hint = next(
        hint
        for hint in wrong_predicate_support.predicate_hints
        if hint.predicate == RC + "partitionedBy"
    )
    assert partition_hint.predicate_curie == "rc:partitionedBy"
    assert partition_hint.triple_count == 1
    assert partition_hint.sample_values[0].value == (
        "https://richcanopy.org/example/manifest/ais#daily_date_partition"
    )


def test_describe_dataset_reports_missing_dataset(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    with pytest.raises(DoxaBaseError, match="was not found"):
        db.describe_dataset("https://richcanopy.org/example/manifest/ais#MissingDataset")


def test_map_helpers_do_not_duplicate_column_links(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    table = "https://example.test/project#messages"
    column = "https://example.test/project#message_id"

    db.record_map_dataset(
        table,
        label="Messages",
        is_table=True,
        columns=[column],
    )
    db.record_map_column(
        column,
        table_iri=table,
        column_name="message_id",
    )

    description = db.describe_dataset(table)
    assert [item.iri for item in description.columns] == [column]
    assert db.triple_count("map") == 6


@pytest.mark.parametrize(
    ("call", "match"),
    [
        pytest.param(
            lambda db: db.record_map_dataset(
                "https://example.test/project#messages",
                label="Messages",
                row_semantics="One row per source message.",
            ),
            "row_semantics.*not prose",
            id="dataset-row-semantics",
        ),
        pytest.param(
            lambda db: db.record_map_dataset(
                "https://example.test/project#messages",
                label="Messages",
                columns=["plain doc id column"],
            ),
            "columns.*not prose",
            id="dataset-column-link",
        ),
        pytest.param(
            lambda db: db.record_map_dataset(
                "https://example.test/project#messages",
                label="Messages",
                caveats=["body caveat prose"],
            ),
            "caveats.*not prose",
            id="dataset-caveat-link",
        ),
        pytest.param(
            lambda db: db.record_map_dataset(
                "https://example.test/project#messages",
                label="Messages",
                storage_accesses=["local parquet access"],
            ),
            "storage_accesses.*not prose",
            id="dataset-storage-link",
        ),
        pytest.param(
            lambda db: db.record_map_dataset(
                "https://example.test/project#messages",
                label="Messages",
                physical_layouts=["parquet physical layout"],
            ),
            "physical_layouts.*not prose",
            id="dataset-layout-link",
        ),
        pytest.param(
            lambda db: db.record_map_dataset(
                "https://example.test/project#messages",
                label="Messages",
                companion_datasets=["attachment companion table"],
            ),
            "companion_datasets.*not prose",
            id="dataset-companion-link",
        ),
        pytest.param(
            lambda db: db.record_map_dataset(
                "https://example.test/project#messages",
                label="Messages",
                extra_types=["special table class"],
            ),
            "extra_types.*not prose",
            id="dataset-extra-type",
        ),
        pytest.param(
            lambda db: db.record_map_analysis_view(
                "https://example.test/project#sent_external_messages",
                source_datasets=["messages source table"],
            ),
            "source_datasets.*not prose",
            id="analysis-view-source-dataset",
        ),
        pytest.param(
            lambda db: db.record_map_analysis_view(
                "https://example.test/project#sent_external_messages",
                denominator_iri="external message denominator",
                denominator_description="One row per external sent message.",
            ),
            "denominator_iri.*not prose",
            id="analysis-view-denominator",
        ),
        pytest.param(
            lambda db: db.record_map_column(
                "https://example.test/project#messages__doc_id",
                column_name="doc_id",
                physical_type="plain varchar prose",
            ),
            "physical_type.*not prose",
            id="column-physical-type",
        ),
        pytest.param(
            lambda db: db.record_map_column(
                "https://example.test/project#messages__doc_id",
                table_iri="plain table prose",
                column_name="doc_id",
            ),
            "table_iri.*not prose",
            id="column-table",
        ),
        pytest.param(
            lambda db: db.record_map_caveat(
                "https://example.test/project#body_caveat",
                description="Body text is cleaned text, not raw source text.",
                severity="high confidence warning",
            ),
            "severity.*not prose",
            id="caveat-severity",
        ),
        pytest.param(
            lambda db: db.record_map_caveat(
                "https://example.test/project#body_caveat",
                description="Body text is cleaned text, not raw source text.",
                targets=["the messages table"],
            ),
            "targets.*not prose",
            id="caveat-target",
        ),
        pytest.param(
            lambda db: db.record_map_storage_access(
                "https://example.test/project#local_access",
                storage_protocol="local filesystem storage",
            ),
            "storage_protocol.*not prose",
            id="storage-protocol",
        ),
        pytest.param(
            lambda db: db.record_map_storage_access(
                "https://example.test/project#local_access",
                datasets=["the messages table"],
            ),
            "datasets.*not prose",
            id="storage-dataset",
        ),
        pytest.param(
            lambda db: db.record_map_physical_layout(
                "https://example.test/project#messages_layout",
                file_format="parquet files",
            ),
            "file_format.*not prose",
            id="layout-file-format",
        ),
        pytest.param(
            lambda db: db.record_map_physical_layout(
                "https://example.test/project#messages_layout",
                compression_codec="zstd",
            ),
            "compression_codec.*rc:ZstdCompression",
            id="layout-compression-codec",
        ),
        pytest.param(
            lambda db: db.record_map_partition_scheme(
                "https://example.test/project#messages_partitioning",
                partition_columns=["the date column"],
            ),
            "partition_columns.*not prose",
            id="partition-column",
        ),
        pytest.param(
            lambda db: db.record_map_relationship(
                "https://example.test/project#attachment_parent_fk",
                relationship_type="foreign_key",
                from_column="parent doc id column",
                to_column="https://example.test/project#messages__doc_id",
            ),
            "from_column.*not prose",
            id="relationship-foreign-key-column",
        ),
        pytest.param(
            lambda db: db.record_map_relationship(
                "https://example.test/project#attachment_count_rollup",
                relationship_type="aggregation",
                aggregated_columns=[
                    {
                        "target_column": "attachment count column",
                        "source_columns": [
                            "https://example.test/project#attachments__parent_doc_id",
                        ],
                    },
                ],
            ),
            r"aggregated_columns\[1\]\.target_column.*not prose",
            id="relationship-aggregate-target",
        ),
    ],
)
def test_map_helpers_reject_prose_for_resource_fields(
    tmp_path: Path,
    call: Callable[[DoxaBase], object],
    match: str,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match=match):
        call(db)


def test_deep_lore_context_slice_reports_absent_lore_layer(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#plain_table"
    db.record_map_dataset(
        dataset,
        label="Plain table",
        description="A table with map context but no recorded lore.",
        is_table=True,
        path_templates=["data/plain.parquet"],
    )

    context_slice = db.get_context_graph([dataset], profile="deep_lore")

    assert context_slice.pattern_contexts == []
    assert context_slice.route_counts["seed_dataset"] == 1
    assert context_slice.warnings == [
        "deep_lore found no claims, patterns, reconsiderations, "
        "evidence, or revision history beyond map context for these seeds."
    ]


def test_search_finds_fixture_literals_with_resource_context(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    results = db.search("MMSI vessel", graph="map", limit=10)

    assert results.query == "MMSI vessel"
    assert results.graph == "map"
    assert results.limit == 10
    match = next(
        result
        for result in results.matches
        if "MMSI does not reliably identify" in result.text
    )
    assert match.graph == "map"
    assert match.predicate == RC + "caveatDescription"
    assert "MMSI" in match.snippet


def test_unscoped_seed_heavy_search_suggests_project_graph_retries(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.record_map_storage_access(
        "https://example.test/project#OnlyStorageAccess",
        label="Only project storage access",
        description="Project storage access fact that should be easy to find.",
        storage_protocol="rc:S3CompatibleStorage",
        location_kind="prefix",
        storage_root="s3://example-project",
    )

    unscoped = db.search("storage", limit=5)

    assert unscoped.scope_hint is not None
    assert unscoped.scope_hint.status == "seed_heavy_unscoped_results"
    assert unscoped.scope_hint.seed_match_count > unscoped.scope_hint.project_match_count
    assert unscoped.scope_hint.seed_graphs == ["base_ontology", "base_shapes"]
    assert unscoped.scope_hint.suggested_graphs == [
        "map",
        "observations",
        "patterns",
        "evidence",
    ]
    assert [
        action.args for action in unscoped.scope_hint.suggested_next_actions
    ] == [
        {"query": "storage", "graph": "map", "limit": 5, "offset": 0},
        {"query": "storage", "graph": "observations", "limit": 5, "offset": 0},
        {"query": "storage", "graph": "patterns", "limit": 5, "offset": 0},
        {"query": "storage", "graph": "evidence", "limit": 5, "offset": 0},
    ]

    scoped = db.search("storage", graph="map", limit=5)
    assert scoped.scope_hint is None
    assert scoped.suggested_next_actions == []
    assert {match.graph for match in scoped.matches} == {"map"}


def test_zero_match_search_suggests_bounded_retrieval_fallbacks(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#ForeshoreMaskBundle"
    db.record_map_dataset(
        dataset,
        label="Foreshore confidence mask bundle",
        description=(
            "Derived raster masks for harbor-margin QA, produced from "
            "phase-normalized tide correction."
        ),
        is_table=False,
    )

    query = "derived harbor QA mask shifted inland water-level adjustment"
    result = db.search(query, limit=5)

    assert result.matches == []
    assert result.scope_hint is None
    assert [action.tool.removeprefix("doxabase.") for action in result.suggested_next_actions] == [
        "search",
        "search",
        "search",
        "list_entities",
        "search",
    ]
    assert [action.args for action in result.suggested_next_actions[:3]] == [
        {"query": "derived", "graph": "map", "limit": 5, "offset": 0},
        {"query": "harbor", "graph": "map", "limit": 5, "offset": 0},
        {"query": "qa", "graph": "map", "limit": 5, "offset": 0},
    ]
    assert result.suggested_next_actions[3].args == {
        "graph": "map",
        "text": "derived",
        "limit": 5,
        "offset": 0,
    }
    assert result.suggested_next_actions[4].args == {
        "query": query,
        "scope": "staged_patches",
        "graph": "history",
        "current_staged_work_only": True,
        "limit": 5,
        "offset": 0,
    }


def test_search_falls_back_to_same_dataset_co_mentions(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(POLYMARKET_FIXTURE)

    results = db.search("outcomes clobTokenIds", graph="map", limit=10)
    matched_iris = {match.iri for match in results.matches}

    assert (
        "https://richcanopy.org/example/manifest/polymarket#mkt_outcomes"
        in matched_iris
    )
    assert (
        "https://richcanopy.org/example/manifest/polymarket#mkt_clob_token_ids"
        in matched_iris
    )
    assert {match.graph for match in results.matches} == {"map"}


def test_search_index_survives_repeated_rebuilds_after_scratch_import(
    tmp_path: Path,
) -> None:
    capsule = tmp_path / "capsule.sqlite"
    db = DoxaBase.create(capsule)
    db.import_turtle(
        """
        @prefix ex: <https://example.test/> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:EnronEmails a rc:Dataset ;
            rdfs:label "Enron Emails" ;
            rc:summary "README-derived scratch map for the Enron email corpus." .
        """,
        graph="map",
    )
    db.record_observation(
        summary="Enron EML messages include body_top and reply depth fields.",
        evidence_summary="README EML pipeline section.",
        evidence_sources=["/home/james/github.com/jamtho/enron-emails/README.md"],
    )
    db.close()

    reopened = DoxaBase(capsule)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        record = reopened.record_observation(
            summary="Enron embeddings join to messages by doc_id.",
            evidence_summary="README embeddings section.",
            evidence_sources=[
                "/home/james/github.com/jamtho/enron-emails/README.md",
            ],
        )

    runtime_warnings = [
        warning
        for warning in caught
        if issubclass(warning.category, RuntimeWarning)
    ]
    assert runtime_warnings == []
    assert reopened.search("doc_id", graph="observations").matches[0].iri == (
        record.observation_iri
    )
    reopened.close()


def test_describe_resource_reports_counts_and_offsets(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    hub = "https://example.test/project#Hub"
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:Hub a rc:Dataset ;
            rdfs:label "Hub" ;
            ex:link ex:Item00, ex:Item01, ex:Item02, ex:Item03, ex:Item04,
                ex:Item05, ex:Item06, ex:Item07, ex:Item08, ex:Item09 .

        ex:Item00 ex:pointsTo ex:Hub .
        ex:Item01 ex:pointsTo ex:Hub .
        ex:Item02 ex:pointsTo ex:Hub .
        ex:Item03 ex:pointsTo ex:Hub .
        ex:Item04 ex:pointsTo ex:Hub .
        ex:Item05 ex:pointsTo ex:Hub .
        ex:Item06 ex:pointsTo ex:Hub .
        ex:Item07 ex:pointsTo ex:Hub .
        ex:Item08 ex:pointsTo ex:Hub .
        ex:Item09 ex:pointsTo ex:Hub .
        """,
        graph="map",
    )

    context = db.describe_resource(
        hub,
        graph="map",
        limit=3,
        outgoing_offset=2,
        incoming_offset=4,
    )

    assert context.outgoing_total_count == 12
    assert context.outgoing_returned_count == 3
    assert context.outgoing_omitted_count == 7
    assert context.outgoing_offset == 2
    assert len(context.outgoing) == 3
    assert context.incoming_total_count == 10
    assert context.incoming_returned_count == 3
    assert context.incoming_omitted_count == 3
    assert context.incoming_offset == 4
    assert len(context.incoming) == 3

    with pytest.raises(DoxaBaseError, match="outgoing_offset"):
        db.describe_resource(hub, outgoing_offset=-1)
    with pytest.raises(DoxaBaseError, match="incoming_offset"):
        db.describe_resource(hub, incoming_offset=-1)


def test_describe_resource_can_include_bounded_blank_node_closure(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    shape = "https://example.test/project#SignalShape"
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:SignalShape a sh:NodeShape ;
            rdfs:label "Signal shape" ;
            sh:targetClass ex:Signal ;
            sh:property [
                sh:path ex:score ;
                sh:datatype xsd:decimal ;
                sh:message "Score is decimal." ;
                sh:qualifiedValueShape [
                    sh:path ex:source ;
                    sh:datatype xsd:string
                ]
            ] ;
            sh:property [
                sh:path ex:status ;
                sh:datatype xsd:string ;
                sh:message "Status is text."
            ] .
        """,
        graph="shapes",
    )

    default_context = db.describe_resource(shape, graph="shapes")
    assert default_context.include_blank_node_closure is False
    assert default_context.blank_node_triples == []
    assert any(
        triple.predicate == "http://www.w3.org/ns/shacl#property"
        and triple.object_kind == "bnode"
        for triple in default_context.outgoing
    )

    context = db.describe_resource(
        shape,
        graph="shapes",
        include_blank_node_closure=True,
        blank_node_depth=2,
        blank_node_limit=4,
    )

    assert context.include_blank_node_closure is True
    assert context.blank_node_depth == 2
    assert context.blank_node_limit == 4
    assert context.blank_node_returned_count == 4
    assert context.blank_node_total_count > context.blank_node_returned_count
    assert context.blank_node_omitted_count == (
        context.blank_node_total_count - context.blank_node_returned_count
    )
    assert context.blank_node_depth_exhausted is False
    assert context.blank_node_unvisited_count == 0
    blank_node_predicates = {triple.predicate for triple in context.blank_node_triples}
    assert "http://www.w3.org/ns/shacl#path" in blank_node_predicates
    assert "http://www.w3.org/ns/shacl#datatype" in blank_node_predicates

    shallow_context = db.describe_resource(
        shape,
        graph="shapes",
        include_blank_node_closure=True,
        blank_node_depth=1,
    )
    assert shallow_context.blank_node_depth_exhausted is True
    assert shallow_context.blank_node_unvisited_count == 1

    with pytest.raises(DoxaBaseError, match="blank_node_depth"):
        db.describe_resource(shape, include_blank_node_closure=True, blank_node_depth=-1)
    with pytest.raises(DoxaBaseError, match="blank_node_limit"):
        db.describe_resource(shape, include_blank_node_closure=True, blank_node_limit=0)


def test_get_context_graph_warns_on_large_structured_context(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WideEvents"
    db.record_map_dataset(dataset, label="Wide events", is_table=True)
    for index in range(80):
        db.record_map_column(
            f"https://example.test/project#WideEventsColumn{index:02d}",
            table_iri=dataset,
            column_name=f"column_{index:02d}",
            physical_type="rc:Varchar",
        )

    context_slice = db.get_context_graph(
        dataset,
        profile="dataset_brief",
        max_triples=5,
    )

    assert context_slice.truncated is True
    assert context_slice.returned_triple_count == 5
    assert context_slice.dataset_contexts[0].iri == dataset
    assert len(context_slice.dataset_contexts[0].columns) == 80
    assert any(
        "structured contexts are still returned in full" in warning
        and "80 column(s)" in warning
        and "narrower column, profile, metric, or pattern seed" in warning
        for warning in context_slice.warnings
    )


def test_search_index_updates_after_graph_clear(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    assert db.search("downsampling", graph="map").matches

    db.clear_graph("map")

    assert db.search("downsampling", graph="map").matches == []


def test_search_rejects_invalid_queries(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match="Search query"):
        db.search("   ")
    with pytest.raises(DoxaBaseError, match="searchable token"):
        db.search("...")


def test_list_entities_rejects_unregistered_curie_type(tmp_path: Path) -> None:
    """An unexpanded CURIE type filter can never match stored full-IRI
    types; silent [] misled an agent querying a project vocabulary
    (AIS session 6). Full IRIs must keep working."""
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)

    with pytest.raises(DoxaBaseError, match="not a registered prefix"):
        db.list_entities(type="aisv:AisIdentity", graph="map")

    result = db.list_entities(
        type="https://richcanopy.org/ns/rc#Table", graph="map", limit=20
    )
    assert result.entities
