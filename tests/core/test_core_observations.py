"""Split from test_doxabase_core.py (distillation Phase 2); tests verbatim."""

from tests.core.support_core import *  # noqa: F401,F403


def test_describe_dataset_links_relevant_patterns(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/enron#"
    messages = f"{base}eml_messages"
    doc_id = f"{base}eml_messages__doc_id"
    caveat = f"{base}eml_messages_id_caveat"
    claim = f"{base}claim_doc_id_join"

    db.record_map_dataset(
        messages,
        label="EML messages",
        is_table=True,
        path_templates=["data/messages.parquet"],
    )
    db.record_map_column(
        doc_id,
        table_iri=messages,
        column_name="doc_id",
        physical_type="rc:Varchar",
    )
    db.record_map_caveat(
        caveat,
        description="Message identifiers are stable within this source but not globally.",
        targets=[messages],
    )
    claim_result = db.record_claim_observation(
        summary="doc_id behaves as the message entity key.",
        claim_text="doc_id behaves as the message entity key.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=[doc_id],
        claim_iri=claim,
        evidence_summary="Unit test evidence.",
        evidence_sources=["tests/test_doxabase_core.py"],
    )
    pattern_result = db.record_pattern(
        summary="doc_id is the stable message identity handle.",
        pattern_text="Use doc_id as the stable message identity handle.",
        rationale="A claim about the table column supports this reader protocol.",
        pattern_targets=[messages, caveat],
        supporting_claims=[claim_result.claim_iri],
    )

    description = db.describe_dataset(messages)

    assert [pattern.iri for pattern in description.linked_patterns] == [
        pattern_result.pattern_iri
    ]
    assert description.linked_patterns[0].label == (
        "doc_id is the stable message identity handle."
    )
    assert description.linked_patterns[0].description == (
        "Use doc_id as the stable message identity handle."
    )
    assert len(description.linked_pattern_reasons) == 1
    pattern_reason = description.linked_pattern_reasons[0]
    assert pattern_reason.iri == pattern_result.pattern_iri
    assert pattern_reason.pattern_iri == pattern_result.pattern_iri
    assert pattern_reason.pattern_text == (
        "Use doc_id as the stable message identity handle."
    )
    assert pattern_reason.rationale == (
        "A claim about the table column supports this reader protocol."
    )
    assert {
        (match.match_type, match.matched_resource.iri)
        for match in pattern_reason.matches
    } == {
        ("pattern_target", caveat),
        ("pattern_target", messages),
        ("supporting_claim_target", doc_id),
    }
    assert pattern_reason.match_group_count == 3
    assert pattern_reason.raw_match_count == 3
    assert pattern_reason.relevance_tier_counts == {
        "direct": 2,
        "claim_supported": 1,
    }
    assert {
        (group.relevance_tier, group.matched_resource.iri)
        for group in pattern_reason.match_groups
    } == {
        ("direct", caveat),
        ("direct", messages),
        ("claim_supported", doc_id),
    }
    caveat_group = next(
        group
        for group in pattern_reason.match_groups
        if group.matched_resource.iri == caveat
    )
    assert caveat_group.matched_resource_kind == "KnownCaveat"
    assert caveat_group.matched_resource.description == (
        "Message identifiers are stable within this source but not globally."
    )
    direct_group = next(
        group
        for group in pattern_reason.match_groups
        if group.matched_resource.iri == messages
    )
    assert direct_group.matched_resource_kind == "Table"
    assert direct_group.route_labels == ["direct pattern target"]
    claim_group = next(
        group
        for group in pattern_reason.match_groups
        if group.matched_resource.iri == doc_id
    )
    assert claim_group.matched_resource_kind == "Column"
    assert claim_group.route_labels == ["via supporting claim target"]
    assert claim_group.supporting_claims[0].iri == claim_result.claim_iri
    claim_match = next(
        match
        for match in pattern_reason.matches
        if match.match_type == "supporting_claim_target"
    )
    assert claim_match.supporting_claim is not None
    assert claim_match.supporting_claim.iri == claim_result.claim_iri
    assert claim_match.matched_resource.column_name == "doc_id"
    assert description.path_templates == ["data/messages.parquet"]


def test_describe_context_slice_expands_unmapped_observed_column_seed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    promo_column = "https://example.test/project#orders__promo_code"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled for redacted promo-code metrics.",
        evidence_summary="Orders profile run.",
        evidence_sources=["test://orders-profile"],
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": promo_column,
                "column_name": "promo_code",
                "summary": "Sampled redacted promo-code metrics.",
                "profile_metrics": [
                    {
                        "metric": "https://example.test/project#SuppressedValueBucketCount",
                        "value": 3,
                    }
                ],
            }
        ],
    )

    context_slice = db.describe_context_slice(
        [promo_column],
        profile="dataset_brief",
        max_triples=300,
    )

    profile_observation_iri = bundle.column_profiles[0].observation.observation_iri
    resources = {resource.iri: resource for resource in context_slice.resources}
    assert promo_column in resources
    assert resources[promo_column].referenced_only is True
    assert resources[promo_column].primary_route.route == "seed"
    assert any(
        route.route == "seed_observed_column"
        for route in resources[promo_column].routes
    )
    assert profile_observation_iri in resources
    assert dataset in resources
    assert context_slice.dataset_contexts[0].iri == dataset
    assert [
        profile.iri for profile in context_slice.seed_profile_observations
    ] == [profile_observation_iri]
    assert context_slice.route_counts["seed_observed_column"] == 1
    assert context_slice.route_counts["seed_profile_observation"] == 1
    assert context_slice.route_counts["observed_column"] == 1
    assert "Seed resource" not in " ".join(context_slice.warnings)


def test_describe_context_slice_expands_unmapped_observed_column_after_workflow_import(
    tmp_path: Path,
) -> None:
    source = DoxaBase.create(tmp_path / "source.sqlite")
    dataset = "https://example.test/project#Orders"
    promo_column = "https://example.test/project#orders__promo_code"
    source.record_map_dataset(dataset, label="Orders", is_table=True)
    bundle = source.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled for redacted promo-code metrics.",
        evidence_summary="Orders profile run.",
        evidence_sources=["test://orders-profile"],
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": promo_column,
                "column_name": "promo_code",
                "summary": "Sampled redacted promo-code metrics.",
                "profile_metrics": [
                    {
                        "metric": "https://example.test/project#SuppressedValueBucketCount",
                        "value": 3,
                    }
                ],
            }
        ],
    )
    export_path = tmp_path / "workflow.trig"

    export_result = source.export_trig(export_path, graphs="workflow")
    imported = DoxaBase.create(tmp_path / "workflow-import.sqlite")
    import_counts = imported.import_trig(export_path)
    context_slice = imported.describe_context_slice(
        [promo_column],
        profile="dataset_brief",
        max_triples=300,
    )

    assert "ontology" not in export_result.graphs
    assert import_counts["observations"] == source.triple_count("observations")
    profile_observation_iri = bundle.column_profiles[0].observation.observation_iri
    resources = {resource.iri: resource for resource in context_slice.resources}
    assert promo_column in resources
    assert resources[promo_column].referenced_only is True
    assert any(
        route.route == "seed_observed_column"
        for route in resources[promo_column].routes
    )
    assert profile_observation_iri in resources
    assert dataset in resources
    assert [
        profile.iri for profile in context_slice.seed_profile_observations
    ] == [profile_observation_iri]
    assert context_slice.route_counts["seed_observed_column"] == 1
    assert context_slice.route_counts["seed_profile_observation"] == 1
    assert context_slice.route_counts["observed_column"] == 1
    assert "Seed resource" not in " ".join(context_slice.warnings)


def test_describe_context_slice_expands_observed_value_type_seed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    status_column = "https://example.test/project#orders__status"
    status_value_type = "https://example.test/project#OrderStatus"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders were profiled for status code types.",
        evidence_summary="Orders profile run.",
        evidence_sources=["test://orders-profile"],
        column_defaults={"update_map_column": False},
        column_profiles=[
            {
                "column_iri": status_column,
                "column_name": "status",
                "summary": "Status looked like a project status-code value type.",
                "physical_type": "rc:Varchar",
                "value_type": status_value_type,
            }
        ],
    )

    context_slice = db.describe_context_slice(
        [status_value_type],
        profile="dataset_brief",
        max_triples=300,
    )

    profile_observation_iri = bundle.column_profiles[0].observation.observation_iri
    resources = {resource.iri: resource for resource in context_slice.resources}
    assert status_value_type in resources
    assert resources[status_value_type].referenced_only is True
    assert any(
        route.route == "seed_observed_value_type"
        for route in resources[status_value_type].routes
    )
    assert profile_observation_iri in resources
    assert dataset in resources
    assert context_slice.dataset_contexts[0].iri == dataset
    assert [
        profile.iri for profile in context_slice.seed_profile_observations
    ] == [profile_observation_iri]
    assert context_slice.route_counts["seed_observed_value_type"] == 1
    assert context_slice.route_counts["seed_profile_observation"] == 1
    assert "Seed resource" not in " ".join(context_slice.warnings)
    assert "profile-specific expansion did not apply" not in " ".join(
        context_slice.warnings
    )


def test_deep_lore_context_slice_expands_plain_observation_seed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/payments#payments"
    status_column = "https://example.test/payments#payments__status"
    db.record_map_dataset(dataset, label="Payments", is_table=True)
    db.record_map_column(
        status_column,
        table_iri=dataset,
        column_name="status",
        physical_type="rc:Varchar",
    )
    claim = db.record_claim_observation(
        summary="Payment status mixes processor and settlement semantics.",
        claim_text=(
            "payment status combines processor state with settlement lifecycle "
            "and should not be treated as a simple closed enum."
        ),
        claim_kind="rc:CaveatClaim",
        claim_targets=[dataset, status_column],
        observed_asset=dataset,
        observed_column=status_column,
        evidence_sources=["scratch://payments-status-review.json"],
    )
    assert claim.evidence_iri is not None
    pattern = db.record_pattern(
        summary="Payment status needs lifecycle caveats.",
        pattern_text=(
            "Status mappings should preserve processor and settlement lifecycle "
            "caveats."
        ),
        rationale="The claim observes the dataset and status column directly.",
        pattern_targets=[dataset],
        supporting_observations=[claim.observation_iri],
        supporting_claims=[claim.claim_iri],
        evidence_iri=claim.evidence_iri,
    )
    staged = db.stage_graph_revision(
        summary="Draft payment status caveat",
        rationale="Exercise revision support for plain observation context slices.",
        supporting_observations=[claim.observation_iri],
        supporting_patterns=[pattern.pattern_iri],
        revision_anchors=[dataset],
        evidence=[claim.evidence_iri],
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix pay: <https://example.test/payments#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    <{dataset}> rc:hasKnownCaveat pay:status_lifecycle_caveat .
                    pay:status_lifecycle_caveat a rc:KnownCaveat ;
                        rc:caveatDescription "Status mixes processor and settlement lifecycle." ;
                        rc:severity rc:Moderate .
                """,
            }
        ],
    )

    context_slice = db.describe_context_slice(
        claim.observation_iri,
        profile="deep_lore",
        max_triples=400,
    )

    resources = {resource.iri: resource for resource in context_slice.resources}
    assert not context_slice.warnings
    assert claim.observation_iri in resources
    assert dataset in resources
    assert status_column in resources
    assert claim.claim_iri in resources
    assert claim.evidence_iri in resources
    assert pattern.pattern_iri in resources
    assert staged.revision_iri in resources
    assert context_slice.dataset_contexts[0].iri == dataset
    assert [context.iri for context in context_slice.pattern_contexts] == [
        pattern.pattern_iri
    ]
    assert context_slice.route_counts["seed_observation"] == 1
    assert context_slice.route_counts["observed_asset"] == 1
    assert context_slice.route_counts["observed_column"] == 1
    assert context_slice.route_counts["supporting_claim"] >= 1
    assert context_slice.route_counts["evidence"] >= 1
    assert context_slice.route_counts["linked_pattern"] >= 1
    assert context_slice.route_counts["revision_supporting_observation"] == 1
    route_legend = {row.route: row for row in context_slice.route_legend}
    assert route_legend["seed_observation"].meaning == (
        "A seed resource expanded as an ordinary observation."
    )


def test_search_finds_recorded_observation_and_evidence(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    record = db.record_observation(
        summary="Handover lore says this hidden join relies on source ordering.",
        evidence_summary="Notebook evidence captured during dataset takeover.",
        evidence_sources=["tests/test_doxabase_core.py"],
    )

    observations = db.search("hidden join", graph="observations")
    evidence = db.search("notebook takeover", graph="evidence")

    assert observations.matches[0].iri == record.observation_iri
    assert observations.matches[0].label == (
        "Handover lore says this hidden join relies on source ordering."
    )
    assert observations.matches[0].types == [RC + "Observation"]
    assert evidence.matches[0].iri == record.evidence_iri
    assert evidence.matches[0].graph == "evidence"


def test_scratch_capsule_observation_write_recovers_search_index(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "doxabase-enron-fieldtrial.sqlite")
    db._conn.execute("DROP TABLE literal_search_data")
    db._conn.commit()

    record = db.record_observation(
        summary="Enron EML messages are the richer analyst-facing table.",
        evidence_summary="README documents EML parsing as including bodies and reply analysis.",
        evidence_sources=[
            "/home/james/github.com/jamtho/enron-emails/README.md",
        ],
    )

    assert record.evidence_iri is not None
    assert db.search("richer analyst", graph="observations").matches[0].iri == (
        record.observation_iri
    )
    assert db.search("reply analysis", graph="evidence").matches[0].iri == (
        record.evidence_iri
    )


def test_agent_authored_observation_rdf_imports_and_validates(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    imported = db.import_trig(
        """
        @prefix enron: <https://example.test/enron#> .
        @prefix rc:    <https://richcanopy.org/ns/rc#> .
        @prefix rcg:   <https://richcanopy.org/graph/> .
        @prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .

        rcg:map {
            enron:eml_messages a rc:Table ;
                rdfs:label "eml_messages.parquet" .

            enron:body_top a rc:Column ;
                rc:columnName "body_top" .
        }

        rcg:observations {
            enron:obs_body_top_transformation a rc:Observation ;
                rc:summary "body_top is cleaned message text, not raw email text." ;
                rc:observedAt "2026-05-31T00:00:00Z"^^xsd:dateTime ;
                rc:observedAsset enron:eml_messages ;
                rc:observationStatus rc:Checked ;
                rc:evidence enron:evidence_readme_body_processing ;
                rc:hasClaim enron:claim_body_top_transformation .

            enron:claim_body_top_transformation a rc:Claim ;
                rc:claimKind rc:TransformationClaim ;
                rc:claimTarget enron:body_top ;
                rc:claimText "The body_top column stores text above reply separators after footer stripping." ;
                rc:confidence rc:HighConfidence ;
                rc:observationStatus rc:Checked ;
                rc:proposedAssertion enron:body_top_transformation_caveat .
        }

        rcg:evidence {
            enron:evidence_readme_body_processing a rc:Evidence ;
                rc:summary "Enron README body processing section." ;
                rc:sourceSpan enron:span_readme_body_processing .

            enron:span_readme_body_processing a rc:SourceSpan ;
                rc:sourceKind rc:DocumentationSource ;
                rc:sourcePath "/home/james/github.com/jamtho/enron-emails/README.md" ;
                rc:sourceSection "Body processing" ;
                rc:startLine 186 ;
                rc:endLine 191 .
        }
        """
    )

    assert imported["observations"] > 0
    assert imported["evidence"] > 0
    assert db.validate_graph(scope="all").conforms
    assert db.search("reply separators", graph="observations").matches
    assert db.search("Body processing", graph="evidence").matches


def test_agent_authored_observation_rdf_requires_evidence(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(
        """
        @prefix enron: <https://example.test/enron#> .
        @prefix rc:    <https://richcanopy.org/ns/rc#> .
        @prefix rcg:   <https://richcanopy.org/graph/> .

        rcg:observations {
            enron:obs_without_evidence a rc:Observation ;
                rc:summary "This observation should fail stricter observation validation." .
        }
        """
    )

    validation = db.validate_graph(scope="all")

    assert not validation.conforms
    assert "Observation resources should link to at least one named Evidence" in (
        validation.report_text
    )


def test_record_claim_observation_writes_common_rdf_pattern(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    result = db.record_claim_observation(
        summary="The Enron body_top column is transformed message text.",
        claim_text="body_top stores text above reply separators after footer stripping.",
        claim_kind="rc:TransformationClaim",
        claim_targets=["https://example.test/enron#eml_messages_body_top"],
        observed_asset="https://example.test/enron#eml_messages",
        observed_at="2026-05-31T00:00:00Z",
        observed_by="urn:doxabase:test-agent",
        evidence_summary="README body processing section.",
        source_path="/home/james/github.com/jamtho/enron-emails/README.md",
        source_section="Body processing",
        start_line=186,
        end_line=191,
        source_kind="rc:DocumentationSource",
        confidence="rc:HighConfidence",
        observation_status="rc:Checked",
        proposed_assertions=[
            "https://example.test/enron#body_top_transformation_caveat",
        ],
    )

    assert result.claim_iri.startswith(
        "https://richcanopy.org/doxabase/generated/claim/"
    )
    assert result.source_span_iri is not None
    assert result.observation_triples > 0
    assert result.evidence_triples > 0
    assert db.validate_graph(scope="all").conforms

    claims = db.list_entities(
        type="rc:Claim",
        graph="observations",
        text="reply separators",
    )
    assert [claim.iri for claim in claims.entities] == [result.claim_iri]
    assert claims.entities[0].label == (
        "body_top stores text above reply separators after footer stripping."
    )

    context = db.describe_resource(result.claim_iri, graph="observations")
    outgoing_predicates = {triple.predicate for triple in context.outgoing}

    assert context.label == (
        "body_top stores text above reply separators after footer stripping."
    )
    assert "https://richcanopy.org/ns/rc#claimKind" in outgoing_predicates
    assert "https://richcanopy.org/ns/rc#claimTarget" in outgoing_predicates
    assert any(
        triple.subject == result.observation_iri
        and triple.predicate == "https://richcanopy.org/ns/rc#hasClaim"
        for triple in context.incoming
    )

    evidence_context = db.describe_resource(result.evidence_iri, graph="evidence")
    assert any(
        triple.predicate == "https://richcanopy.org/ns/rc#sourceSpan"
        and triple.object == result.source_span_iri
        for triple in evidence_context.outgoing
    )


def test_dataset_context_slice_includes_query_result_observation_evidence(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    query_path = tmp_path / "orders_status_by_hour.sql"
    query_path.write_text(
        "select status, count(*) from orders group by status;\n",
        encoding="utf-8",
    )

    result = db.record_query_result(
        summary=(
            "Orders status-by-hour aggregate was blocked because the local "
            "partition files were not bundled."
        ),
        observed_asset=dataset,
        observed_at="2026-07-01T12:00:00+00:00",
        execution_status="blocked",
        engine="duckdb",
        query_source_path=str(query_path),
        scanned_source_paths=[
            "warehouse/orders/dt=2026-06-30/hour=12/orders.parquet"
        ],
        failure_summary="The reviewed Parquet path was absent from this capsule.",
    )

    context_slice = db.describe_context_slice(
        dataset,
        profile="deep_lore",
        max_triples=250,
    )

    resources = {resource.iri: resource for resource in context_slice.resources}
    assert result.observation_iri in resources
    assert result.evidence_iri in resources
    assert result.source_span_iri in resources
    assert result.scanned_source_span_iris[0] in resources
    assert context_slice.route_counts["dataset_observation"] == 1
    assert context_slice.route_counts["evidence"] == 1
    assert context_slice.route_counts["source_span"] == 2
    assert any(
        route.route == "dataset_observation"
        for route in resources[result.observation_iri].routes
    )
    route_legend = {row.route: row for row in context_slice.route_legend}
    assert route_legend["dataset_observation"].meaning == (
        "A bounded ordinary observation that names a selected dataset as its observed asset."
    )
    assert any(
        triple.subject == result.evidence_iri
        and triple.predicate == RC + "queryExecutionStatus"
        and triple.object == "blocked"
        for triple in context_slice.triples
    )
    assert db.validate_graph(scope="all").conforms


def test_record_query_result_records_failures_as_observations(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    result = db.record_query_result(
        summary="Orders CSV query failed because DuckDB was unavailable.",
        execution_status="failed",
        engine="duckdb",
        query_source_path="queries/orders.sql",
        result_sources=["stderr://duckdb-not-installed"],
        failure_summary="ModuleNotFoundError: duckdb",
    )

    assert result.observation_type == "observation"
    assert result.execution_status == "failed"
    assert result.failure_summary == "ModuleNotFoundError: duckdb"
    assert result.source_span_iri is not None
    assert [action.tool_name for action in result.suggested_next_actions] == [
        "describe_context_slice"
    ]
    assert result.suggested_next_actions[0].arguments == {
        "seed_iris": [result.evidence_iri],
        "profile": "resource_brief",
    }
    assert db.validate_graph(scope="all").conforms


def test_record_claim_reconsideration_links_claim_lifecycle(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    older = db.record_claim_observation(
        summary="Initial MMSI identity hunch.",
        claim_text="MMSI can be treated as the stable vessel identity key.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=["https://example.test/ais#mmsi"],
        evidence_sources=["trial setup"],
    )
    newer = db.record_claim_observation(
        summary="MMSI caveat check.",
        claim_text="MMSI is an operational grouping key, not proof of vessel identity.",
        claim_kind="rc:CaveatClaim",
        claim_targets=["https://example.test/ais#mmsi"],
        evidence_sources=["retrieved caveat"],
        observation_status="rc:Checked",
    )

    reconsideration = db.record_claim_reconsideration(
        newer_claim=newer.claim_iri,
        older_claim=older.claim_iri,
        relation="weakens",
        summary="MMSI identity hunch weakened.",
        rationale=(
            "The retrieved caveat shows MMSI remains useful for operational "
            "grouping but is too weak for durable vessel identity."
        ),
        evidence_sources=["DoxaBase search(\"MMSI vessel\")"],
        source_path="/tmp/doxabase-search-mmsi-vessel.json",
        source_kind="rc:DoxaBaseAPISource",
    )

    assert reconsideration.relation == RC + "Weakening"
    assert reconsideration.direct_predicate == RC + "weakens"
    assert reconsideration.older_claim_status == RC + "Weakened"
    assert reconsideration.source_span_iri is not None
    assert reconsideration.status_triples == 1
    assert db.validate_graph(scope="all").conforms

    older_context = db.describe_resource(older.claim_iri, graph="observations")
    assert older_context.claim is not None
    assert older_context.claim.lifecycle_summary is not None
    assert "Current status: weakened." in older_context.claim.lifecycle_summary
    assert "1 weakening." in older_context.claim.lifecycle_summary
    nested_reconsideration = older_context.claim.incoming_reconsiderations[0]
    assert nested_reconsideration.evidence[0].sources == [
        'DoxaBase search("MMSI vessel")'
    ]
    assert nested_reconsideration.evidence[0].source_spans[0].source_path == (
        "/tmp/doxabase-search-mmsi-vessel.json"
    )
    assert nested_reconsideration.evidence[0].source_spans[0].source_kind == (
        RC + "DoxaBaseAPISource"
    )
    older_statuses = [
        triple.object
        for triple in older_context.outgoing
        if triple.predicate == RC + "observationStatus"
    ]
    assert older_statuses == [RC + "Weakened"]

    newer_context = db.describe_resource(newer.claim_iri, graph="observations")
    assert any(
        triple.predicate == RC + "weakens" and triple.object == older.claim_iri
        for triple in newer_context.outgoing
    )

    pattern = db.record_pattern(
        summary="MMSI hunch should be read as operational, not identity-level.",
        pattern_text=(
            "The later caveat claim weakens the earlier vessel-identity hunch "
            "without making MMSI useless for grouping."
        ),
        rationale="The reconsideration preserves both the tempting hunch and the correction.",
        pattern_targets=["https://example.test/ais#mmsi"],
        supporting_claims=[older.claim_iri],
        evidence_sources=["claim reconsideration test"],
    )
    description = db.describe_pattern(pattern.pattern_iri)

    incoming = description.supporting_claims[0].incoming_reconsiderations
    assert description.supporting_claims[0].lifecycle_summary is not None
    assert "Later claims reconsider this claim: 1 weakening." in (
        description.supporting_claims[0].lifecycle_summary
    )
    assert [item.iri for item in incoming] == [reconsideration.reconsideration_iri]
    assert incoming[0].newer_claim is not None
    assert incoming[0].newer_claim.iri == newer.claim_iri
    assert incoming[0].relation_label == "weakening"

    context_slice = db.describe_context_slice(
        [older.claim_iri],
        profile="deep_lore",
    )
    assert context_slice.route_counts["incoming_claim_reconsideration"] == 1
    assert context_slice.route_counts["reconsidering_claim"] == 1

    pattern_context_slice = db.describe_context_slice(
        [pattern.pattern_iri],
        profile="pattern_brief",
    )
    assert pattern_context_slice.route_counts["incoming_claim_reconsideration"] == 1
    assert pattern_context_slice.route_counts["reconsidering_claim"] == 1
    assert [context.iri for context in pattern_context_slice.pattern_contexts] == [
        pattern.pattern_iri
    ]


def test_record_claim_reconsideration_default_weakening_keeps_terminal_status(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    older = db.record_claim_observation(
        summary="Initial merchant category hunch.",
        claim_text="merchant_category can be treated as a closed domain.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=["https://example.test/project#merchant_category"],
        evidence_sources=["trial setup"],
    )
    superseding = db.record_claim_observation(
        summary="Merchant category hunch replaced.",
        claim_text="merchant_category should use a source-maintained domain.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=["https://example.test/project#merchant_category"],
        evidence_sources=["domain review"],
    )
    weakening = db.record_claim_observation(
        summary="Merchant category hunch softened.",
        claim_text="merchant_category is useful but not closed.",
        claim_kind="rc:CaveatClaim",
        claim_targets=["https://example.test/project#merchant_category"],
        evidence_sources=["quality review"],
    )

    supersession = db.record_claim_reconsideration(
        newer_claim=superseding.claim_iri,
        older_claim=older.claim_iri,
        relation="supersedes",
        rationale="The source-maintained domain replaces the closed-domain hunch.",
    )
    later_weakening = db.record_claim_reconsideration(
        newer_claim=weakening.claim_iri,
        older_claim=older.claim_iri,
        relation="weakens",
        rationale=(
            "The quality review also weakens the old hunch, but should not "
            "downgrade the terminal superseded status."
        ),
    )

    assert supersession.older_claim_status == RC + "Superseded"
    assert supersession.status_triples == 1
    assert later_weakening.older_claim_status == RC + "Superseded"
    assert later_weakening.status_triples == 0

    older_context = db.describe_resource(older.claim_iri, graph="observations")
    assert older_context.claim is not None
    assert older_context.claim.lifecycle_summary is not None
    assert "Current status: superseded." in older_context.claim.lifecycle_summary
    assert "1 supersession" in older_context.claim.lifecycle_summary
    assert "1 weakening" in older_context.claim.lifecycle_summary
    older_statuses = [
        triple.object
        for triple in older_context.outgoing
        if triple.predicate == RC + "observationStatus"
    ]
    assert older_statuses == [RC + "Superseded"]

    explicit = db.record_claim_observation(
        summary="Merchant category explicit weakening.",
        claim_text="An explicit reviewer can still change the lifecycle status.",
        claim_kind="rc:CaveatClaim",
        claim_targets=["https://example.test/project#merchant_category"],
        evidence_sources=["manual lifecycle override"],
    )
    explicit_weakening = db.record_claim_reconsideration(
        newer_claim=explicit.claim_iri,
        older_claim=older.claim_iri,
        relation="weakens",
        rationale="Manual override intentionally softens the older claim status.",
        older_claim_status="rc:Weakened",
    )
    assert explicit_weakening.older_claim_status == RC + "Weakened"
    assert explicit_weakening.status_triples == 1


def test_context_slice_column_seed_expands_claim_reconsideration_lore(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/payments#transactions"
    column = "https://example.test/payments#transactions__merchant_category"
    db.record_map_dataset(
        dataset,
        label="Payments transactions",
        is_table=True,
    )
    db.record_map_column(
        column,
        table_iri=dataset,
        column_name="merchant_category",
        physical_type="rc:Varchar",
    )
    older = db.record_claim_observation(
        summary="Merchant category looked like a stable domain.",
        claim_text="merchant_category appeared to be a stable merchant domain.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=[column],
        evidence_sources=["scratch://merchant-category-profile.json"],
    )
    newer = db.record_claim_observation(
        summary="Merchant category needs acquirer-specific caveats.",
        claim_text=(
            "merchant_category is acquirer-normalized and should not be treated "
            "as a universal closed domain."
        ),
        claim_kind="rc:CaveatClaim",
        claim_targets=[column],
        evidence_sources=["scratch://merchant-category-review.json"],
        observation_status="rc:Checked",
    )
    db.record_claim_reconsideration(
        newer_claim=newer.claim_iri,
        older_claim=older.claim_iri,
        relation="weakens",
        rationale="Later review shows the original domain claim was too broad.",
        evidence_sources=["scratch://merchant-category-reconsideration.json"],
    )
    followup = db.record_pattern(
        summary="Merchant category claims require acquirer caveats.",
        pattern_text=(
            "Use the checked caveat claim before reusing the earlier merchant "
            "category domain hunch."
        ),
        rationale="Both claims target the same mapped column.",
        pattern_targets=[column],
        supporting_claims=[older.claim_iri, newer.claim_iri],
    )

    context_slice = db.describe_context_slice([column], profile="deep_lore")

    assert not context_slice.warnings
    assert context_slice.dataset_contexts[0].iri == dataset
    assert followup.pattern_iri in [
        pattern_context.iri for pattern_context in context_slice.pattern_contexts
    ]
    assert context_slice.route_counts["seed_column"] == 1
    assert context_slice.route_counts["related_dataset"] == 1
    assert context_slice.route_counts["supporting_claim"] >= 2
    assert context_slice.route_counts["claim_target"] >= 2
    assert context_slice.route_counts["incoming_claim_reconsideration"] == 1
    assert context_slice.route_counts["reconsidering_claim"] == 1
    route_legend = {row.route: row for row in context_slice.route_legend}
    assert route_legend["seed_column"].meaning == (
        "A seed resource expanded as a mapped column."
    )


def test_context_slice_truncation_suggests_pattern_narrowing(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/payments#transactions"
    column = "https://example.test/payments#transactions__merchant_category"
    db.record_map_dataset(dataset, label="Payments transactions", is_table=True)
    db.record_map_column(
        column,
        table_iri=dataset,
        column_name="merchant_category",
        physical_type="rc:Varchar",
    )
    claim = db.record_claim_observation(
        summary="Merchant category needs acquirer-specific caveats.",
        claim_text=(
            "merchant_category is acquirer-normalized and should not be treated "
            "as a universal closed domain."
        ),
        claim_kind="rc:CaveatClaim",
        claim_targets=[column],
        evidence_sources=["scratch://merchant-category-review.json"],
    )
    pattern = db.record_pattern(
        summary="Merchant category claims require acquirer caveats.",
        pattern_text="Use the caveat claim before reusing merchant category.",
        rationale="The claim targets the mapped column.",
        pattern_targets=[column],
        supporting_claims=[claim.claim_iri],
    )

    context_slice = db.describe_context_slice(
        [column],
        profile="deep_lore",
        max_triples=5,
    )

    assert context_slice.truncated is True
    assert context_slice.pattern_contexts[0].iri == pattern.pattern_iri
    assert any(
        "suggested_next_actions" in warning
        for warning in context_slice.warnings
    )
    assert [
        action.action_label for action in context_slice.suggested_next_actions
    ] == [
        "Inspect query-planning context",
        "Narrow to pattern context",
        "Return full raw RDF for slice",
    ]
    assert context_slice.suggested_next_actions[0].arguments == {"iri": dataset}
    assert "missing_storage_access" in context_slice.suggested_next_actions[0].reason
    assert context_slice.suggested_next_actions[1].arguments == {
        "seed_iris": [pattern.pattern_iri],
        "profile": "pattern_brief",
        "max_triples": 5,
    }
    assert context_slice.suggested_next_actions[2].arguments == {
        "seed_iris": [column],
        "profile": "deep_lore",
        "max_triples": context_slice.candidate_triple_count,
    }
    assert context_slice.suggested_next_calls == [
        action.call for action in context_slice.suggested_next_actions
    ]

    preflight = db.preflight_context_slice_export(
        [column],
        profile="deep_lore",
        max_triples=5,
    )

    assert preflight.truncated is True
    role_loss_warning = next(
        warning
        for warning in preflight.warnings
        if "Context-slice export is truncated" in warning
    )
    assert "graphs and graph_counts describe only capped raw triples" in (
        role_loss_warning
    )
    assert "pattern_synthesis" in role_loss_warning
    assert "Omitted graph roles:" in role_loss_warning
    assert [
        action.tool_name for action in preflight.suggested_next_actions[:2]
    ] == [
        "preflight_context_slice_export",
        "export_context_slice",
    ]
    assert preflight.suggested_next_actions[0].arguments == {
        "seed_iris": [column],
        "profile": "deep_lore",
        "max_triples": preflight.candidate_triple_count,
        "include_seed_graphs": False,
        "limit": 20,
    }


def test_context_slice_truncation_ranks_linked_patterns_before_filler(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/bounded#Events"
    column = "https://example.test/bounded#EventsStatus"
    db.record_map_dataset(
        dataset,
        label="Bounded events",
        is_table=True,
        columns=[column],
    )
    db.record_map_column(
        column,
        table_iri=dataset,
        column_name="status",
        physical_type="rc:Varchar",
    )
    for index in range(4):
        db.record_pattern(
            summary=f"AAA filler pattern {index}",
            pattern_text="Filler lore should not outrank directly linked lore.",
            rationale="This is broad support noise for truncation ordering.",
            pattern_targets=[f"https://example.test/bounded#Filler{index}"],
            map_implications=[dataset],
            evidence_sources=[f"test://filler-{index}"],
        )
    key_claim = db.record_claim_observation(
        summary="Rare status failure claim.",
        claim_text="LORE-ANCHOR rare_delta_failure means status replay.",
        claim_kind="rc:CaveatClaim",
        claim_targets=[column],
        evidence_sources=["test://rare-delta-failure"],
    )
    key_pattern = db.record_pattern(
        summary="ZZZ key rare-delta pattern",
        pattern_text="LORE-ANCHOR rare_delta_failure requires status replay checks.",
        rationale="This pattern directly targets the seed dataset column.",
        pattern_targets=[column],
        supporting_claims=[key_claim.claim_iri],
        evidence_sources=["test://rare-delta-failure-pattern"],
    )

    context_slice = db.describe_context_slice(
        dataset,
        profile="deep_lore",
        max_triples=8,
    )

    assert context_slice.truncated is True
    narrow_actions = [
        action
        for action in context_slice.suggested_next_actions
        if action.action_label == "Narrow to pattern context"
    ]
    assert narrow_actions
    assert narrow_actions[0].arguments == {
        "seed_iris": [key_pattern.pattern_iri],
        "profile": "pattern_brief",
        "max_triples": 8,
    }


def test_truncated_pattern_context_slice_does_not_suggest_self_narrowing(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    pattern_targets = [
        f"https://example.test/project#Resource{index:02d}"
        for index in range(20)
    ]
    for target in pattern_targets:
        db.record_map_dataset(target, label=target.rsplit("#", 1)[-1])
    pattern = db.record_pattern(
        summary="Wide pattern for truncation routing.",
        pattern_text="A deliberately wide pattern touches many resources.",
        rationale="Exercise pattern_brief truncation actions without self-looping.",
        pattern_targets=pattern_targets,
        evidence_sources=["test://wide-pattern"],
    )

    context_slice = db.describe_context_slice(
        [pattern.pattern_iri],
        profile="pattern_brief",
        max_triples=5,
    )

    assert context_slice.truncated is True
    assert [
        action.action_label for action in context_slice.suggested_next_actions
    ] == ["Return full raw RDF for slice"]
    assert context_slice.suggested_next_actions[0].arguments == {
        "seed_iris": [pattern.pattern_iri],
        "profile": "pattern_brief",
        "max_triples": context_slice.candidate_triple_count,
    }


def test_record_pattern_links_observations_claims_evidence_and_targets(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    observation = db.record_observation(
        summary="body_top was populated in the inspected local parquet profile.",
        evidence_summary="Synthetic profile evidence.",
        evidence_sources=["tests/test_doxabase_core.py"],
    )
    claim = db.record_claim_observation(
        summary="body_top transformation claim.",
        claim_text="body_top is cleaned top-level message text.",
        claim_kind="rc:TransformationClaim",
        claim_targets=["https://example.test/enron#eml_messages__body_top"],
        evidence_summary="README body processing section.",
        source_path="/home/james/github.com/jamtho/enron-emails/README.md",
        source_section="Body processing",
        source_kind="rc:DocumentationSource",
        confidence="rc:HighConfidence",
        observation_status="rc:Checked",
    )

    result = db.record_pattern(
        summary="body_top behaves like cleaned top-level message text.",
        pattern_text=(
            "Documentation, a profile observation, and the transformation claim "
            "all support treating body_top as cleaned sender-new text."
        ),
        rationale=(
            "The supporting observation says the field is populated, while the "
            "claim and source span explain the reply-splitting transformation."
        ),
        pattern_targets=["https://example.test/enron#eml_messages__body_top"],
        supporting_observations=[observation.observation_iri],
        supporting_claims=[claim.claim_iri],
        source_path="/home/james/github.com/jamtho/enron-emails/README.md",
        source_section="Body processing",
        start_line=186,
        end_line=191,
        source_kind="rc:DocumentationSource",
        confidence="rc:HighConfidence",
        pattern_status="rc:Checked",
        pattern_stability="rc:RepeatedPattern",
        map_implications=["https://example.test/enron#caveat_body_processing_lossy"],
    )

    assert result.pattern_iri.startswith(
        "https://richcanopy.org/doxabase/generated/pattern/"
    )
    assert result.evidence_iri is not None
    assert result.source_span_iri is not None
    assert result.pattern_triples > 0
    assert result.evidence_triples > 0
    assert db.graph_overview().key_counts["patterns"] == 1
    assert db.validate_graph(scope="patterns").conforms
    assert db.validate_graph(scope="all").conforms

    patterns = db.list_entities(
        type="rc:Pattern",
        graph="patterns",
        text="sender-new",
    )
    assert [pattern.iri for pattern in patterns.entities] == [result.pattern_iri]
    assert patterns.entities[0].label == (
        "body_top behaves like cleaned top-level message text."
    )

    context = db.describe_resource(result.pattern_iri, graph="patterns")
    outgoing_predicates = {triple.predicate for triple in context.outgoing}

    assert context.label == "body_top behaves like cleaned top-level message text."
    assert "https://richcanopy.org/ns/rc#supportingObservation" in outgoing_predicates
    assert "https://richcanopy.org/ns/rc#supportingClaim" in outgoing_predicates
    assert "https://richcanopy.org/ns/rc#mapImplication" in outgoing_predicates
    assert db.search("sender-new", graph="patterns").matches[0].iri == (
        result.pattern_iri
    )

    description = db.describe_pattern(result.pattern_iri)
    assert description.summary == "body_top behaves like cleaned top-level message text."
    assert description.pattern_text is not None
    assert "sender-new text" in description.pattern_text
    assert description.rationale is not None
    assert description.confidence == RC + "HighConfidence"
    assert description.confidence_label == "high confidence"
    assert description.observation_status == RC + "Checked"
    assert description.observation_status_label == "checked"
    assert description.pattern_stability == RC + "RepeatedPattern"
    assert description.pattern_stability_label == "repeated pattern"
    assert [target.iri for target in description.pattern_targets] == [
        "https://example.test/enron#eml_messages__body_top"
    ]
    assert [support.iri for support in description.supporting_observations] == [
        observation.observation_iri
    ]
    assert description.supporting_observations[0].label == (
        "body_top was populated in the inspected local parquet profile."
    )
    assert [support.iri for support in description.supporting_claims] == [
        claim.claim_iri
    ]
    assert description.supporting_claims[0].claim_text == (
        "body_top is cleaned top-level message text."
    )
    assert description.evidence[0].source_spans[0].source_section == "Body processing"
    assert description.evidence[0].source_spans[0].start_line == 186
    assert [implication.iri for implication in description.map_implications] == [
        "https://example.test/enron#caveat_body_processing_lossy"
    ]


def test_record_pattern_requires_support_or_source(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match="supporting_observations"):
        db.record_pattern(
            summary="Unsupported synthesis.",
            pattern_text="This pattern has no support.",
            rationale="A pattern should not be a free-floating hunch.",
            pattern_targets=["https://example.test/enron#eml_messages"],
        )
    with pytest.raises(DoxaBaseError, match="evidence_summary requires"):
        db.record_pattern(
            summary="Evidence summary without a source.",
            pattern_text="This pattern has support but no evidence source.",
            rationale="Evidence summaries should not create source-less evidence.",
            pattern_targets=["https://example.test/enron#eml_messages"],
            supporting_observations=["https://example.test/enron#obs"],
            evidence_summary="This summary has no source.",
        )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (
            {"confidence": "rc:ModerateConfidence"},
            "confidence must be one of",
        ),
        (
            {"pattern_status": "rc:Archived"},
            "pattern_status must be one of",
        ),
        (
            {"pattern_stability": "rc:MediumConfidence"},
            "pattern_stability must be one of",
        ),
    ],
)
def test_record_pattern_rejects_unsupported_controlled_values_without_mutating(
    tmp_path: Path,
    kwargs: dict[str, str],
    message: str,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match=message):
        db.record_pattern(
            summary="Unsupported pattern controlled value.",
            pattern_text="This pattern should be rejected before RDF is written.",
            rationale="Controlled values should match the SHACL enumeration.",
            pattern_targets=["https://example.test/project#Orders"],
            evidence_sources=["test://pattern-controlled-value"],
            **kwargs,
        )

    assert _mutable_graph_counts(db) == before_counts
    assert db.validate_graph(scope="all").conforms


def test_record_pattern_rejects_prose_map_implications(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match="map_implications values"):
        db.record_pattern(
            summary="Prose map implication.",
            pattern_text="This pattern should fail before TriG export.",
            rationale="Map implications should point at map resources.",
            pattern_targets=["https://example.test/enron#eml_messages"],
            supporting_observations=["https://example.test/enron#obs"],
            map_implications=[
                "Map remains unchanged in this run; review rationale is in history.",
            ],
        )


def test_agent_authored_pattern_rdf_requires_rationale(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(
        """
        @prefix ex:  <https://example.test/project#> .
        @prefix rc:  <https://richcanopy.org/ns/rc#> .
        @prefix rcg: <https://richcanopy.org/graph/> .

        rcg:patterns {
            ex:unsupported_pattern a rc:Pattern ;
                rc:summary "A pattern without rationale should fail." ;
                rc:patternText "This pattern skips rationale." ;
                rc:patternTarget ex:eml_messages ;
                rc:evidence ex:evidence .
        }

        rcg:evidence {
            ex:evidence a rc:Evidence ;
                <http://purl.org/dc/terms/source> "tests/test_doxabase_core.py" .
        }
        """
    )

    validation = db.validate_graph(scope="all")

    assert not validation.conforms
    assert "Pattern resources must have exactly one string rationale" in (
        validation.report_text
    )


def test_record_claim_observation_requires_source(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match="evidence_sources or source_path"):
        db.record_claim_observation(
            summary="Missing evidence source.",
            claim_text="This claim should be rejected before RDF is written.",
            claim_kind="rc:CaveatClaim",
            claim_targets=["https://example.test/enron#eml_messages"],
            evidence_summary="Summary alone is not enough for source-backed evidence.",
        )


def test_record_claim_observation_rejects_unsupported_confidence_without_mutating(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match="confidence must be one of"):
        db.record_claim_observation(
            summary="Unsupported claim confidence.",
            claim_text="The claim should be rejected before RDF is written.",
            claim_kind="rc:CaveatClaim",
            claim_targets=["https://example.test/project#Orders"],
            evidence_sources=["test://claim-confidence"],
            confidence="rc:ModerateConfidence",
        )

    assert _mutable_graph_counts(db) == before_counts
    assert db.validate_graph(scope="all").conforms


def test_record_claim_observation_rejects_unsupported_status_without_mutating(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match="observation_status must be one of"):
        db.record_claim_observation(
            summary="Unsupported observation status.",
            claim_text="The claim should be rejected before RDF is written.",
            claim_kind="rc:CaveatClaim",
            claim_targets=["https://example.test/project#Orders"],
            evidence_sources=["test://claim-status"],
            observation_status="rc:ConfirmedObservation",
        )

    assert _mutable_graph_counts(db) == before_counts
    assert db.validate_graph(scope="all").conforms


def test_record_claim_observation_rejects_prose_proposed_assertions(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match="proposed_assertions values"):
        db.record_claim_observation(
            summary="Prose proposed assertion.",
            claim_text="This claim should fail before TriG export.",
            claim_kind="rc:CaveatClaim",
            claim_targets=["https://example.test/enron#eml_messages"],
            evidence_sources=["tests/test_doxabase_core.py"],
            proposed_assertions=[
                "Map remains unchanged in this run; review rationale is in history.",
            ],
        )


def test_record_observation_writes_observation_and_evidence_graphs(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    before = db.graph_overview().key_counts["observations"]
    observed_asset = "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"

    result = db.record_observation(
        summary="AIS daily broadcasts were sampled for row coverage.",
        observation_type="profile",
        observed_asset=observed_asset,
        observed_at="2026-05-31T12:00:00Z",
        observed_by="urn:doxabase:test-agent",
        evidence_summary="Synthetic test evidence for the observation writer.",
        evidence_sources=["tests/test_doxabase_core.py"],
        sample_size=100,
        sample_scope="Full synthetic AIS fixture used by the test.",
        sample_method="DuckDB full-table aggregate profile.",
        row_count=123,
        distinct_count=45,
        value_frequencies=[
            {"value": "open", "frequency": 70},
            {"value": "closed", "frequency": 53},
        ],
        profile_metrics=[
            {"metric": "rc:MinimumValue", "value": 1.5, "target": observed_asset},
            {"metric": "rc:MaximumValue", "value": "9.25", "datatype": "xsd:decimal"},
        ],
    )

    assert result.observation_type == "profile"
    assert result.evidence_iri is not None
    assert result.observation_triples > 0
    assert result.evidence_triples > 0
    assert db.graph_overview().key_counts["observations"] == before + 1

    observations = db.to_graph(["observations"])
    evidence = db.to_graph(["evidence"])
    observation_iri = URIRef(result.observation_iri)
    evidence_iri = URIRef(result.evidence_iri)

    assert (observation_iri, RDF.type, URIRef(RC + "ProfileObservation")) in observations
    assert (
        observation_iri,
        URIRef(RC + "sampleSize"),
        Literal(100),
    ) in observations
    assert (
        observation_iri,
        URIRef(RC + "sampleScope"),
        Literal("Full synthetic AIS fixture used by the test."),
    ) in observations
    assert (
        observation_iri,
        URIRef(RC + "sampleMethod"),
        Literal("DuckDB full-table aggregate profile."),
    ) in observations
    assert (
        observation_iri,
        URIRef(RC + "rowCount"),
        Literal(123),
    ) in observations
    assert (
        observation_iri,
        URIRef(RC + "evidence"),
        evidence_iri,
    ) in observations
    value_frequency_iris = list(
        observations.objects(observation_iri, URIRef(RC + "observedValueFrequency"))
    )
    assert len(value_frequency_iris) == 2
    assert {
        (
            str(observations.value(value_iri, URIRef(RC + "observedValue"))),
            int(str(observations.value(value_iri, URIRef(RC + "valueFrequency")))),
        )
        for value_iri in value_frequency_iris
    } == {("open", 70), ("closed", 53)}
    assert all(
        (value_iri, RDF.type, URIRef(RC + "ObservedValueFrequency")) in observations
        for value_iri in value_frequency_iris
    )
    metric_iris = list(
        observations.objects(observation_iri, URIRef(RC + "observedProfileMetric"))
    )
    assert len(metric_iris) == 2
    assert {
        (
            str(observations.value(metric_iri, URIRef(RC + "profileMetricKind"))),
            str(observations.value(metric_iri, URIRef(RC + "profileMetricValue"))),
        )
        for metric_iri in metric_iris
    } == {
        (RC + "MinimumValue", "1.5"),
        (RC + "MaximumValue", "9.25"),
    }
    assert any(
        (
            metric_iri,
            URIRef(RC + "profileMetricTarget"),
            URIRef(observed_asset),
        )
        in observations
        for metric_iri in metric_iris
    )
    assert all(
        (metric_iri, RDF.type, URIRef(RC + "ObservedProfileMetric")) in observations
        for metric_iri in metric_iris
    )
    assert (evidence_iri, RDF.type, URIRef(RC + "Evidence")) in evidence
    assert (
        evidence_iri,
        DCTERMS.source,
        Literal("tests/test_doxabase_core.py"),
    ) in evidence

    validation = db.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_metric_promotion_skeleton_uses_generic_comment_for_broad_pattern(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"
    project_metric = "https://example.test/project#BroadNoMentionCompletenessScore"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders profile with a broad project metric pattern.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": project_metric,
                "value": "0.92",
                "datatype": "xsd:decimal",
            }
        ],
        column_defaults={"update_map_column": False},
    )
    pattern = db.record_pattern(
        summary="Orders quality gates need vocabulary.",
        pattern_text=(
            "The profile run suggests the Orders feed should have reusable "
            "quality gates before downstream comparison."
        ),
        rationale="The pattern and profile run share one evidence resource.",
        pattern_targets=[dataset],
        supporting_observations=(
            bundle.handoff_entrypoints.profile_observation_iris
        ),
        evidence_iri=evidence,
        map_implications=[project_metric],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)
    advisory = draft.metric_advisories[0]
    promotion_action = [
        action
        for action in advisory.suggested_next_actions
        if action.tool_name == "stage_pattern_promotion"
    ][0]
    framing_content = promotion_action.arguments["framings"][0]["content"]

    assert [item.iri for item in advisory.promotion_patterns] == [
        pattern.pattern_iri
    ]
    assert "review and sharpen its calculation" in framing_content
    assert "quality gates" not in framing_content


def test_metric_promotion_skeleton_uses_metric_specific_pattern_hint(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    evidence = "https://example.test/project#OrdersProfileRunEvidence"
    completeness_metric = "https://example.test/project#CompletenessScore"
    freshness_metric = "https://example.test/project#FreshnessLagDays"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    bundle = db.record_profile_bundle(
        dataset,
        dataset_summary="Orders profile with two project metric outputs.",
        evidence_summary="Synthetic profile run.",
        evidence_sources=["test://orders-profile"],
        shared_evidence_iri=evidence,
        update_map_snapshot=False,
        profile_metrics=[
            {
                "metric": completeness_metric,
                "value": "0.92",
                "datatype": "xsd:decimal",
            },
            {
                "metric": freshness_metric,
                "value": "3",
                "datatype": "xsd:integer",
            },
        ],
        column_defaults={"update_map_column": False},
    )
    pattern = db.record_pattern(
        summary="CompletenessScore needs metric vocabulary.",
        pattern_text=(
            "CompletenessScore is non-null values divided by row count and is "
            "a unitless ratio for comparing full-table profile runs. The same "
            "run also surfaced another project metric for later vocabulary "
            "review."
        ),
        rationale="The pattern and profile run share one evidence resource.",
        pattern_targets=[dataset],
        supporting_observations=(
            bundle.handoff_entrypoints.profile_observation_iris
        ),
        evidence_iri=evidence,
        map_implications=[completeness_metric, freshness_metric],
    )

    draft = db.draft_profile_map_updates(dataset, evidence)
    advisories_by_metric = {
        advisory.metric.iri: advisory for advisory in draft.metric_advisories
    }

    assert set(advisories_by_metric) == {
        completeness_metric,
        freshness_metric,
    }
    for advisory in advisories_by_metric.values():
        assert [item.iri for item in advisory.promotion_patterns] == [
            pattern.pattern_iri
        ]

    completeness_action = [
        action
        for action in advisories_by_metric[
            completeness_metric
        ].suggested_next_actions
        if action.tool_name == "stage_pattern_promotion"
    ][0]
    freshness_action = [
        action
        for action in advisories_by_metric[freshness_metric].suggested_next_actions
        if action.tool_name == "stage_pattern_promotion"
    ][0]
    completeness_content = completeness_action.arguments["framings"][0]["content"]
    freshness_content = freshness_action.arguments["framings"][0]["content"]

    assert "CompletenessScore is non-null values" in completeness_content
    assert "review and sharpen its calculation" in freshness_content
    assert "CompletenessScore is non-null values" not in freshness_content


def test_record_observation_rejects_invalid_inputs(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError, match="summary"):
        db.record_observation("   ")
    with pytest.raises(DoxaBaseError, match="row_count"):
        db.record_observation("Bad count", row_count=-1)
    with pytest.raises(DoxaBaseError, match="value_frequencies"):
        db.record_observation(
            "Bad value frequency",
            observation_type="profile",
            value_frequencies=[{"value": "open", "frequency": -1}],
        )
    with pytest.raises(DoxaBaseError, match="observation_type"):
        db.record_observation("Bad type", observation_type="note")  # type: ignore[arg-type]
    with pytest.raises(DoxaBaseError, match="observed_column_name requires"):
        db.record_observation("Bad column name", observed_column_name="status")
    with pytest.raises(DoxaBaseError, match="observed_column_name must not be empty"):
        db.record_observation(
            "Bad empty column name",
            observed_column="https://example.test/project#OrdersStatus",
            observed_column_name=" ",
        )


def test_record_observation_rejects_conflicting_reused_evidence_summary(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    evidence_iri = "https://example.test/project#ProfileRunEvidence"
    db.record_observation(
        "First profile note.",
        observation_type="profile",
        observed_asset="https://example.test/project#Orders",
        evidence_summary="Shared profiler run.",
        evidence_sources=["test://profile-run"],
        evidence_iri=evidence_iri,
    )
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(DoxaBaseError, match="conflicts with existing summary"):
        db.record_observation(
            "Second profile note.",
            observation_type="profile",
            observed_asset="https://example.test/project#Orders",
            evidence_summary="Different profiler run summary.",
            evidence_sources=["test://profile-run/second"],
            evidence_iri=evidence_iri,
        )

    assert _mutable_graph_counts(db) == before_counts
    assert db.search("Second profile note", graph="observations").matches == []
    assert db.validate_graph(scope="all").conforms

