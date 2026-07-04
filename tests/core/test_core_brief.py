"""Split from test_doxabase_core.py (distillation Phase 2); tests verbatim."""

from tests.core.support_core import *  # noqa: F401,F403






































































def test_recovery_first_safe_action_prefers_semantic_frontier_over_informational(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    already_effective = "https://example.test/project#AlreadyEffective"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    event_source = db.stage_graph_revision(
        summary="Model Orders as event rows",
        rationale="Choose event-row framing for Orders.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix ex: <https://example.test/project#> .

                    <{orders}> a ex:EventRow .
                """,
            }
        ],
        revision_anchors=[orders],
        validation_scope="all",
    )
    db.apply_staged_revision(event_source.revision_iri)
    informational_source = db.stage_graph_revision(
        summary="Stage already-effective table",
        rationale="This staged source will already be current map state.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    <{already_effective}> a rc:Dataset .
                """,
            }
        ],
    )
    db.record_map_dataset(already_effective, label="Already effective")
    semantic_alternative = db.stage_systematisation(
        summary="Review aggregate row alternative",
        intent=(
            "Keep the aggregate-row alternative visible after the event-row "
            "source was applied."
        ),
        anchors=[orders],
        framings=[
            {
                "label": "Aggregate row alternative",
                "graph": "map",
                "content": f"""
                    @prefix ex: <https://example.test/project#> .

                    <{orders}> a ex:AggregateRow .
                """,
                "alternative_to": event_source.revision_iri,
            }
        ],
        validation_scope="all",
    )
    semantic_iri = semantic_alternative.staged_revisions[0].revision_iri
    revision_iris = [informational_source.revision_iri, semantic_iri]

    plan = db.plan_staged_revision_recovery(
        revision_iris,
        current_staged_work_only=False,
        drift_detail="exact",
    )

    assert plan.lane_counts == {"informational": 1, "apply_after_review": 1}
    assert plan.would_restage_revision_iris == []
    assert plan.mutation_allowed_after == (
        "semantic_review_required_before_mutation"
    )
    assert plan.first_mutation_action is None
    assert plan.first_safe_review_or_mutation_action is not None
    assert plan.first_safe_review_or_mutation_action.tool == (
        "doxabase.describe_revision"
    )
    assert plan.first_safe_review_or_mutation_action.args == {
        "iri": semantic_iri
    }
    assert plan.first_safe_review_or_mutation_source == "semantic_frontier_review"

    session = db.start_staged_revision_recovery_session(
        revision_iris,
        summary="Semantic frontier with informational source first",
        current_staged_work_only=False,
        drift_detail="exact",
    )
    described = db.describe_staged_revision_recovery_session(
        session.session_iri,
        drift_detail="exact",
    )

    assert described.current_plan.first_safe_review_or_mutation_action == (
        plan.first_safe_review_or_mutation_action
    )
    assert described.current_plan.first_safe_review_or_mutation_source == (
        "semantic_frontier_review"
    )




def test_resource_brief_packet_outgoing_refs_prioritize_action_links_over_artifacts(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/analysis-packet-priority#"
    source = f"{base}messages"
    packet = f"{base}packet"
    view = f"{base}z_review_view"
    recipe = f"{base}z_query_recipe"
    task = f"{base}z_followup_task"
    artifacts = [
        {
            "iri": f"{base}a_artifact_{index:02d}",
            "label": f"Bulk artifact {index:02d}",
            "summary": "Bulk visualization or aggregate output.",
            "source_path": f"scratch://bulk-artifact-{index:02d}.json",
            "artifact_role": "bulk output",
            "media_type": "application/json",
            "supports": [view],
        }
        for index in range(40)
    ]

    db.record_map_dataset(source, label="Messages", is_table=True)
    result = db.record_analysis_packet(
        packet,
        summary="Packet with many artifacts and a few action links.",
        analysis_views=[
            {
                "iri": view,
                "label": "Reviewed message population",
                "source_datasets": [source],
                "denominator_description": "Reviewed message rows.",
            },
        ],
        artifacts=artifacts,
        query_recipes=[
            {
                "iri": recipe,
                "label": "Review query",
                "query_text": "select * from messages where reviewed",
                "query_language": "DuckDB SQL",
                "query_engine": "duckdb",
                "targets": [view],
            }
        ],
        followup_tasks=[
            {
                "iri": task,
                "label": "Inspect reviewed population",
                "task_text": "Read the packet view before bulk artifacts.",
                "targets": [view],
            }
        ],
    )

    slice_obj = db.get_context_graph([packet], profile="resource_brief")
    context = to_dict(slice_obj)
    outgoing_iris = {
        resource.iri
        for resource in slice_obj.resources
        if any(
            route.route == "outgoing_reference" and route.source_iri == packet
            for route in resource.routes
        )
    }

    assert context["route_counts"]["outgoing_reference"] == 25
    assert result.artifact_iris[-1] not in outgoing_iris
    assert {view, recipe, task}.issubset(outgoing_iris)
    assert any(
        action["tool"] == "doxabase.describe_resource"
        and action["args"].get("aspect") == "analysis_view"
        and action["args"]["iri"] == view
        for action in context["suggested_next_actions"]
    )
    assert any(
        "omitted" in warning and "outgoing reference" in warning
        for warning in context["warnings"]
    )


def test_get_context_graph_returns_route_explained_dataset_brief(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/enron#"
    messages = f"{base}eml_messages"
    doc_id = f"{base}eml_messages__doc_id"
    claim = f"{base}claim_doc_id_join"

    db.record_map_dataset(
        messages,
        label="EML messages",
        description="Parsed email message records.",
        is_table=True,
        path_templates=["data/messages.parquet"],
        layout_verification_status="rc:CandidateLayout",
        layout_verification_note="Path pattern is plausible but not verified.",
    )
    db.record_map_column(
        doc_id,
        table_iri=messages,
        column_name="doc_id",
        physical_type="rc:Varchar",
    )
    claim_result = db.record_claim_observation(
        summary="doc_id behaves as the message entity key.",
        claim_text="doc_id behaves as the message entity key.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=[doc_id],
        claim_iri=claim,
        evidence_summary="Unit test evidence.",
        source_path="tests/test_doxabase_core.py",
        source_kind="rc:DocumentationSource",
    )
    pattern_result = db.record_pattern(
        summary="doc_id is the stable message identity handle.",
        pattern_text="Use doc_id as the stable message identity handle.",
        rationale="A claim about the table column supports this reader protocol.",
        pattern_targets=[messages],
        supporting_claims=[claim_result.claim_iri],
    )

    context_slice = db.get_context_graph(
        [messages],
        profile="dataset_brief",
        include_trig=True,
        max_triples=200,
    )

    assert context_slice.profile == "dataset_brief"
    assert context_slice.seeds[0].iri == messages
    assert context_slice.dataset_contexts[0].iri == messages
    assert context_slice.pattern_contexts[0].iri == pattern_result.pattern_iri
    assert context_slice.truncated is False
    assert context_slice.truncation_scope == "triples_only"
    assert context_slice.resource_count == len(context_slice.resources)
    assert context_slice.triple_count <= 200
    assert context_slice.returned_triple_count == context_slice.triple_count
    assert context_slice.candidate_triple_count == context_slice.triple_count
    assert context_slice.omitted_triple_count == 0
    assert context_slice.graph_counts["map"] >= 1
    assert context_slice.graph_counts["patterns"] >= 1
    assert context_slice.graph_counts["observations"] >= 1
    assert context_slice.graph_counts["evidence"] >= 1
    assert context_slice.route_counts["dataset_column"] == 1
    assert context_slice.route_counts["layout_verification_status"] == 1
    assert context_slice.route_counts["linked_pattern"] == 1
    assert context_slice.route_counts["supporting_claim"] >= 1
    assert context_slice.reading_order[0].startswith("Start with seeds")
    route_legend = {row.route: row for row in context_slice.route_legend}
    assert route_legend["seed"].count == 1
    assert route_legend["seed"].priority == 0
    assert route_legend["seed"].meaning == (
        "The resource the caller asked about directly."
    )
    assert route_legend["dataset_column"].count == 1
    assert route_legend["layout_verification_status"].meaning == (
        "A verification-status term attached to dataset, layout, storage, or partition path metadata."
    )

    resources = {resource.iri: resource for resource in context_slice.resources}
    assert messages in resources
    assert doc_id in resources
    assert RC + "CandidateLayout" in resources
    assert pattern_result.pattern_iri in resources
    assert claim_result.claim_iri in resources
    assert claim_result.evidence_iri in resources
    assert resources[messages].referenced_only is False
    assert resources[messages].surface_role == "current_map_context"
    assert resources[messages].primary_route == resources[messages].routes[0]
    assert resources[messages].primary_route.route == "seed"
    assert any(route.route == "seed" for route in resources[messages].routes)
    assert resources[doc_id].surface_role == "current_map_context"
    assert resources[RC + "CandidateLayout"].surface_role == "vocabulary_context"
    assert resources[pattern_result.pattern_iri].surface_role == "pattern_synthesis"
    assert resources[claim_result.claim_iri].surface_role == "observation_context"
    assert resources[claim_result.evidence_iri].surface_role == "evidence_support"
    assert any(route.route == "dataset_column" for route in resources[doc_id].routes)
    assert any(
        route.route == "layout_verification_status"
        for route in resources[RC + "CandidateLayout"].routes
    )
    assert any(
        route.route == "linked_pattern"
        for route in resources[pattern_result.pattern_iri].routes
    )

    assert context_slice.trig is not None
    dataset = Dataset()
    dataset.parse(data=context_slice.trig, format="trig")
    graph_iris = {str(graph.identifier) for graph in dataset.graphs() if len(graph)}
    assert "https://richcanopy.org/graph/map" in graph_iris
    assert "https://richcanopy.org/graph/patterns" in graph_iris


def test_resource_brief_context_slice_expands_shape_and_predicate_routes(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    shape = "https://example.test/project#SignalShape"
    score = "https://example.test/project#score"
    reading = "https://example.test/project#Reading"
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        ex:score a rdf:Property ;
            rdfs:label "score" ;
            rdfs:range xsd:decimal .
        """,
        graph="ontology",
    )
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
                sh:datatype xsd:decimal
            ] .
        """,
        graph="shapes",
    )
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        ex:Reading ex:score "0.91"^^xsd:decimal .
        """,
        graph="map",
    )

    shape_slice = db.get_context_graph(
        shape,
        profile="resource_brief",
        max_triples=50,
    )

    assert shape_slice.profile == "resource_brief"
    assert shape_slice.dataset_contexts == []
    assert shape_slice.pattern_contexts == []
    assert shape_slice.route_counts["seed"] == 1
    assert shape_slice.route_counts["resource_type"] == 1
    assert shape_slice.route_counts["blank_node_reference"] >= 2
    resources = {resource.iri: resource for resource in shape_slice.resources}
    assert resources[shape].surface_role == "validation_shape_context"
    assert score in resources
    assert any(
        triple.graph == "shapes"
        and triple.subject_kind == "bnode"
        and triple.predicate == "http://www.w3.org/ns/shacl#path"
        and triple.object == score
        for triple in shape_slice.triples
    )

    score_slice = db.get_context_graph(
        score,
        profile="resource_brief",
        max_triples=50,
    )

    score_routes = {
        route.route
        for resource in score_slice.resources
        if resource.iri == shape
        for route in resource.routes
    }
    assert "incoming_blank_node_owner" in score_routes
    reading_routes = {
        route.route
        for resource in score_slice.resources
        if resource.iri == reading
        for route in resource.routes
    }
    assert "predicate_usage_subject" in reading_routes


def test_resource_brief_context_slice_suggests_route_cap_recovery(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    outgoing_triples = "\n".join(
        f"ex:Hub ex:linksTo ex:Outgoing{index:02d} ."
        for index in range(30)
    )
    predicate_usage_triples = "\n".join(
        f"ex:Use{index:02d} ex:stressPredicate ex:Value{index:02d} ."
        for index in range(30)
    )
    db.import_turtle(
        f"""
        @prefix ex: <https://example.test/project#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

        ex:stressPredicate a rdf:Property .
        {outgoing_triples}
        {predicate_usage_triples}
        """,
        graph="map",
    )

    hub = "https://example.test/project#Hub"
    hub_slice = db.get_context_graph(
        hub,
        profile="resource_brief",
        max_triples=1000,
    )

    assert hub_slice.truncated is False
    assert any(
        "omitted 5 outgoing reference(s)" in warning
        and "Raising max_triples does not recover route-capped resources" in warning
        for warning in hub_slice.warnings
    )
    outgoing_action = next(
        action
        for action in hub_slice.suggested_next_actions
        if action.tool == "doxabase.describe_resource"
        and action.args.get("include_incoming") is False
    )
    assert outgoing_action.tool == "doxabase.describe_resource"
    assert outgoing_action.args == {
        "iri": hub,
        "include_incoming": False,
        "limit": 25,
        "outgoing_offset": 25,
    }

    predicate = "https://example.test/project#stressPredicate"
    predicate_slice = db.get_context_graph(
        predicate,
        profile="resource_brief",
        max_triples=1000,
    )

    assert predicate_slice.truncated is False
    assert any(
        "omitted 5 predicate usage subject(s)" in warning
        and "no paged predicate-usage browser" in warning
        for warning in predicate_slice.warnings
    )
    predicate_action = next(
        action
        for action in predicate_slice.suggested_next_actions
        if action.tool == "doxabase.export_bundle"
        and action.args.get("kind") == "graph"
    )
    assert predicate_action.args["spec"]["graphs"] == "project"
    assert "predicate-usage" in predicate_action.args["spec"]["path"]


def test_resource_brief_incoming_cap_prioritizes_lore_rich_references(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    value_type = "https://example.test/project#ConfidenceBand"
    useful_column = "https://example.test/project#zz_confidence_code"
    auxiliary_columns = "\n".join(
        (
            f"ex:aux_confidence_{index:02d} a rc:Column ; "
            f'rdfs:label "Aux confidence {index:02d}" ; '
            "rc:valueType ex:ConfidenceBand ."
        )
        for index in range(30)
    )
    db.import_turtle(
        f"""
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:ConfidenceBand a rdfs:Class ;
            rdfs:label "Confidence band" .

        {auxiliary_columns}

        ex:zz_confidence_code a rc:Column ;
            rdfs:label "ZZ confidence code" ;
            rc:valueType ex:ConfidenceBand .
        """,
        graph="map",
    )
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:confidence_code_claim a rc:InterpretationClaim ;
            rc:claimText "Confidence code controls calibration decisions." ;
            rc:claimTarget ex:zz_confidence_code .
        """,
        graph="observations",
    )

    context_slice = db.get_context_graph(
        value_type,
        profile="resource_brief",
        max_triples=1000,
    )

    resource_iris = {resource.iri for resource in context_slice.resources}
    assert useful_column in resource_iris
    assert "https://example.test/project#aux_confidence_29" not in resource_iris
    assert context_slice.route_counts["incoming_reference"] == 25
    assert any(
        "omitted 6 incoming reference(s)" in warning
        for warning in context_slice.warnings
    )


def test_resource_brief_context_slice_suggests_blank_node_closure_on_route_cap(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    property_blocks = "\n".join(
        (
            "            sh:property [ "
            f"sh:path ex:path{index:02d}; "
            "sh:datatype xsd:string "
            "] ;"
        )
        for index in range(30)
    )
    db.import_turtle(
        f"""
        @prefix ex: <https://example.test/project#> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        ex:WideShape a sh:NodeShape ;
{property_blocks}
            sh:targetClass ex:WideThing .
        """,
        graph="shapes",
    )

    shape = "https://example.test/project#WideShape"
    context_slice = db.get_context_graph(
        shape,
        profile="resource_brief",
        max_triples=1000,
    )

    assert context_slice.truncated is False
    assert any(
        "blank-node reference(s)" in warning
        and "inspect blank-node closure" in warning
        for warning in context_slice.warnings
    )
    closure_action = next(
        action
        for action in context_slice.suggested_next_actions
        if action.tool == "doxabase.describe_resource"
        and action.args.get("include_blank_node_closure") is True
    )
    assert closure_action.tool == "doxabase.describe_resource"
    assert closure_action.args == {
        "iri": shape,
        "include_blank_node_closure": True,
        "blank_node_depth": 4,
        "blank_node_limit": 100,
    }


def test_resource_brief_context_slice_warns_for_pattern_seed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    pattern = db.record_pattern(
        summary="Messages preserve document identity.",
        pattern_text="Message exports carry document identifiers through joins.",
        rationale="Exercise resource-brief guidance for pattern seeds.",
        pattern_targets=["https://example.test/project#Messages"],
        evidence_sources=["test://pattern"],
    )

    context_slice = db.get_context_graph(
        pattern.pattern_iri,
        profile="resource_brief",
        max_triples=100,
    )

    assert any(
        "Seed is an rc:Pattern; resource_brief gives a generic resource card."
        in warning
        for warning in context_slice.warnings
    )
    pattern_action = next(
        action
        for action in context_slice.suggested_next_actions
        if action.tool == "doxabase.get_context_graph"
        and action.args.get("profile") == "pattern_brief"
    )
    assert pattern_action.tool == "doxabase.get_context_graph"
    assert pattern_action.args == {
        "seed_iris": [pattern.pattern_iri],
        "profile": "pattern_brief",
        "max_triples": 100,
    }


def test_resource_brief_context_slice_finds_owner_for_blank_node_seed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    shape = "https://example.test/project#NestedShape"
    inner_path = "https://example.test/project#innerPath"
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:NestedShape a sh:NodeShape ;
            rdfs:label "Nested shape" ;
            sh:property [
                sh:path ex:outerPath ;
                sh:qualifiedValueShape [
                    sh:path ex:innerPath ;
                    sh:datatype xsd:string ;
                    sh:message "Inner path is text."
                ]
            ] .
        """,
        graph="shapes",
    )
    matches = db.search("Inner path", graph="shapes")
    blank_node_seed = next(
        match.iri
        for match in matches.matches
        if match.types == []
    )

    context_slice = db.get_context_graph(
        blank_node_seed,
        profile="resource_brief",
        max_triples=50,
    )

    shape_resource = next(
        resource for resource in context_slice.resources if resource.iri == shape
    )
    assert any(
        route.route == "blank_node_seed_owner"
        for route in shape_resource.routes
    )
    assert inner_path in {resource.iri for resource in context_slice.resources}
    assert "blank_node_seed_owner" in context_slice.route_counts
    assert not any("owner lookup" in warning for warning in context_slice.warnings)


def test_resource_brief_context_slice_routes_storage_seed_to_query_context(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WarehouseOrders"
    storage = db.record_map_storage_access(
        "https://example.test/project#warehouse_orders_storage",
        label="Warehouse orders database",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        path_templates=["public.orders"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Warehouse orders",
        is_table=True,
        storage_accesses=[storage.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context_slice = db.get_context_graph(
        storage.iri,
        profile="resource_brief",
    )

    dataset_resource = next(
        resource for resource in context_slice.resources if resource.iri == dataset
    )
    assert any(
        route.route == "incoming_reference"
        for route in dataset_resource.routes
    )
    query_actions = [
        action
        for action in context_slice.suggested_next_actions
        if action.tool == "doxabase.describe_query_context"
    ]
    assert len(query_actions) == 1
    assert query_actions[0].args == {"iri": dataset}
    assert "missing_physical_layout" in query_actions[0].reason
    query_context = db.describe_query_context(**query_actions[0].args)
    assert query_context.suggested_repair_action_groups[0].issue_code == (
        "missing_physical_layout"
    )


def test_resource_brief_storage_seed_suggests_clean_owner_query_context(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_storage",
        label="Orders object storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="object",
        storage_root=str(tmp_path / "orders.parquet"),
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#orders_layout",
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

    context_slice = db.get_context_graph(
        storage.iri,
        profile="resource_brief",
    )

    dataset_resource = next(
        resource for resource in context_slice.resources if resource.iri == dataset
    )
    assert any(
        route.route == "incoming_reference"
        for route in dataset_resource.routes
    )
    query_actions = [
        action
        for action in context_slice.suggested_next_actions
        if action.tool == "doxabase.describe_query_context"
    ]
    assert len(query_actions) == 1
    assert query_actions[0].args == {"iri": dataset}
    assert "single queryable owner table" in query_actions[0].reason
    query_context = db.describe_query_context(**query_actions[0].args)
    assert query_context.readiness == "ready_for_query_planning"
    assert query_context.suggested_repair_action_groups == []


def test_resource_brief_storage_seed_suggests_multiple_clean_owner_query_contexts(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    storage = db.record_map_storage_access(
        "https://example.test/project#shared_local_storage",
        label="Shared local object storage",
        storage_protocol="rc:LocalFilesystemStorage",
        location_kind="prefix",
        storage_root=str(tmp_path / "warehouse"),
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#warehouse_parquet_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    owners = [
        ("https://example.test/project#Orders", "orders"),
        ("https://example.test/project#Refunds", "refunds"),
    ]
    for dataset, relation in owners:
        db.record_map_dataset(
            dataset,
            label=relation.title(),
            is_table=True,
            path_templates=[f"{relation}/part-*.parquet"],
            storage_accesses=[storage.iri],
            physical_layouts=[layout.iri],
            layout_verification_status="rc:VerifiedByQueryLayout",
        )

    context_slice = db.get_context_graph(
        storage.iri,
        profile="resource_brief",
    )

    assert {
        resource.iri
        for resource in context_slice.resources
        if any(route.route == "incoming_reference" for route in resource.routes)
    } >= {dataset for dataset, _ in owners}
    query_actions = [
        action
        for action in context_slice.suggested_next_actions
        if action.tool == "doxabase.describe_query_context"
    ]
    assert [action.args for action in query_actions] == [
        {"iri": dataset} for dataset, _ in owners
    ]
    assert all(
        "multiple queryable owner tables" in action.reason
        for action in query_actions
    )
    assert [
        db.describe_query_context(**action.args).readiness
        for action in query_actions
    ] == [
        "ready_for_query_planning",
        "ready_for_query_planning",
    ]


def test_resource_brief_query_context_action_separates_repairs_from_warnings(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    layout = db.record_map_physical_layout(
        "https://example.test/project#orders_layout",
        file_format="rc:Parquet",
        layout_verification_status="rc:CandidateLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        physical_layouts=[layout.iri],
        layout_verification_status="rc:CandidateLayout",
    )

    context_slice = db.get_context_graph(
        layout.iri,
        profile="resource_brief",
    )

    query_actions = [
        action
        for action in context_slice.suggested_next_actions
        if action.tool == "doxabase.describe_query_context"
    ]
    assert len(query_actions) == 1
    reason = query_actions[0].reason
    assert "query-planning repair group(s): missing_storage_access" in reason
    assert (
        "operational query-planning warning(s): "
        "layout_needs_verification, missing_path_template"
    ) in reason
    assert "repair group(s): layout_needs_verification" not in reason
    query_context = db.describe_query_context(**query_actions[0].args)
    assert [group.issue_code for group in query_context.suggested_repair_action_groups] == [
        "missing_storage_access"
    ]


def test_deep_lore_storage_seed_suggests_resource_brief_retry(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WarehouseOrders"
    storage = db.record_map_storage_access(
        "https://example.test/project#warehouse_orders_storage",
        label="Warehouse orders database",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        path_templates=["public.orders"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Warehouse orders",
        is_table=True,
        storage_accesses=[storage.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    deep_slice = db.get_context_graph(
        storage.iri,
        profile="deep_lore",
        max_triples=75,
    )

    assert any(
        "Seed is an rc:StorageAccess; rerun with profile='resource_brief'"
        in warning
        for warning in deep_slice.warnings
    )
    retry_action = next(
        action
        for action in deep_slice.suggested_next_actions
        if action.tool == "doxabase.get_context_graph"
        and action.args.get("profile") == "resource_brief"
    )
    assert retry_action.tool == "doxabase.get_context_graph"
    assert retry_action.args == {
        "seed_iris": [storage.iri],
        "profile": "resource_brief",
        "max_triples": 75,
    }

    resource_slice = db.get_context_graph(**retry_action.args)
    assert any(resource.iri == dataset for resource in resource_slice.resources)
    query_action = next(
        action
        for action in resource_slice.suggested_next_actions
        if action.tool == "doxabase.describe_query_context"
    )
    assert query_action.args == {"iri": dataset}
    assert "missing_physical_layout" in query_action.reason


def test_resource_brief_context_slice_finds_owner_for_nested_predicate_seed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    shape = "https://example.test/project#NestedShape"
    inner_path = "https://example.test/project#innerPath"
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:NestedShape a sh:NodeShape ;
            rdfs:label "Nested shape" ;
            sh:property [
                sh:path ex:outerPath ;
                sh:qualifiedValueShape [
                    sh:path ex:innerPath ;
                    sh:datatype xsd:string ;
                    sh:message "Inner path is text."
                ]
            ] .
        """,
        graph="shapes",
    )

    context_slice = db.get_context_graph(
        inner_path,
        profile="resource_brief",
        max_triples=50,
    )

    shape_resource = next(
        resource for resource in context_slice.resources if resource.iri == shape
    )
    assert any(
        route.route == "incoming_blank_node_owner"
        for route in shape_resource.routes
    )
    assert context_slice.route_counts["incoming_blank_node_owner"] == 1


def test_resource_brief_context_slice_expands_evidence_handoff(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Messages"
    claim_record = db.record_claim_observation(
        summary="Messages need source-backed review.",
        claim_text="The message export should be checked against its source notes.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=[dataset],
        evidence_summary="Synthetic source note.",
        source_path="/tmp/messages-source-note.md",
        source_kind="rc:DocumentationSource",
    )

    context_slice = db.get_context_graph(
        claim_record.evidence_iri,
        profile="resource_brief",
    )

    assert context_slice.route_counts["seed"] == 1
    assert context_slice.route_counts["outgoing_reference"] >= 1
    assert context_slice.route_counts["incoming_reference"] >= 1
    assert claim_record.source_span_iri in {
        resource.iri for resource in context_slice.resources
    }
    assert claim_record.observation_iri in {
        resource.iri for resource in context_slice.resources
    }
    route_legend = {row.route: row for row in context_slice.route_legend}
    assert route_legend["incoming_reference"].meaning == (
        "A URI subject that directly references a resource-brief seed."
    )


def test_resource_brief_evidence_seed_routes_observed_asset_to_query_context(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WarehouseOrders"
    storage = db.record_map_storage_access(
        "https://example.test/project#warehouse_orders_storage",
        label="Warehouse orders database",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        path_templates=["public.orders"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Warehouse orders",
        is_table=True,
        storage_accesses=[storage.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    observation = db.record_observation(
        summary="Warehouse orders were checked from source docs.",
        observed_asset=dataset,
        evidence_summary="Synthetic warehouse source note.",
        evidence_sources=["test://warehouse-orders-source"],
    )

    context_slice = db.get_context_graph(
        observation.evidence_iri,
        profile="resource_brief",
    )

    resources = {resource.iri: resource for resource in context_slice.resources}
    assert observation.observation_iri in resources
    assert dataset in resources
    assert any(
        route.route == "observed_asset"
        and route.source_iri == observation.observation_iri
        for route in resources[dataset].routes
    )
    query_actions = [
        action
        for action in context_slice.suggested_next_actions
        if action.tool == "doxabase.describe_query_context"
    ]
    assert len(query_actions) == 1
    assert query_actions[0].args == {"iri": dataset}
    assert "missing_physical_layout" in query_actions[0].reason


def test_resource_brief_profile_evidence_seed_suggests_profile_run(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WarehouseOrders"
    db.record_map_dataset(dataset, label="Warehouse orders", is_table=True)
    profile = db.record_dataset_profile(
        dataset,
        summary="Warehouse orders were profiled.",
        evidence_summary="Warehouse orders profiler output.",
        evidence_sources=["test://warehouse-orders-profile"],
        row_count=42,
        update_map_snapshot=False,
    )

    context_slice = db.get_context_graph(
        profile.observation.evidence_iri,
        profile="resource_brief",
    )

    resources = {resource.iri: resource for resource in context_slice.resources}
    assert profile.observation.observation_iri in resources
    assert dataset in resources
    profile_run_actions = [
        action
        for action in context_slice.suggested_next_actions
        if action.tool == "doxabase.describe_resource"
        and action.args.get("aspect") == "profile_run"
    ]
    assert len(profile_run_actions) == 1
    assert profile_run_actions[0].args == {
        "iri": dataset,
        "aspect": "profile_run",
        "evidence_iri": profile.observation.evidence_iri,
    }


def test_evidence_seed_wrong_profile_suggests_resource_brief_before_export(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WarehouseOrders"
    db.record_map_dataset(dataset, label="Warehouse orders", is_table=True)
    profile = db.record_dataset_profile(
        dataset,
        summary="Warehouse orders were profiled.",
        evidence_summary="Warehouse orders profiler output.",
        evidence_sources=["test://warehouse-orders-profile"],
        row_count=42,
        update_map_snapshot=False,
    )

    context_slice = db.get_context_graph(
        profile.observation.evidence_iri,
        profile="dataset_brief",
    )

    assert context_slice.route_counts == {"seed": 1}
    assert any(
        "Seed is an rc:Evidence; rerun with profile='resource_brief'"
        in warning
        for warning in context_slice.warnings
    )
    assert context_slice.suggested_next_actions[0].tool == (
        "doxabase.get_context_graph"
    )
    assert context_slice.suggested_next_actions[0].args == {
        "seed_iris": [profile.observation.evidence_iri],
        "profile": "resource_brief",
        "max_triples": 500,
    }

    preflight = db.preflight_context_slice_export(
        profile.observation.evidence_iri,
        profile="dataset_brief",
    )

    assert preflight.suggested_next_actions[0].tool == (
        "doxabase.export_preflight"
    )
    assert preflight.suggested_next_actions[0].args["kind"] == "context_slice"
    assert preflight.suggested_next_actions[0].args == {
        "kind": "context_slice",
        "seed_iris": [profile.observation.evidence_iri],
        "profile": "resource_brief",
        "max_triples": 500,
        "include_seed_graphs": False,
        "limit": 20,
    }
    assert any(
        action.tool == "doxabase.export_bundle"
        and action.args.get("kind") == "context_slice"
        for action in preflight.suggested_next_actions[1:]
    )





# ---------------------------------------------------------------------------
# ProjectBrief v2 (state, not script): gates, queues, dataset one-liners.
# ---------------------------------------------------------------------------


def test_project_brief_reports_capsule_state_shape(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    db.import_trig(POLYMARKET_FIXTURE)

    brief = db.project_brief(limit=10)

    assert brief.limit == 10
    assert brief.dataset_count == 7
    assert len(brief.datasets) == 7
    for dataset in brief.datasets:
        assert dataset.iri.startswith("https://")
        assert isinstance(dataset.is_table, bool)
        assert dataset.status
        assert dataset.column_count >= 0
        assert dataset.caveat_count >= 0
    assert brief.key_counts["datasets"] == 7
    # A clean fixture capsule has storage accesses recorded, so no gates.
    assert [gate.gate for gate in brief.gates] == []
    assert brief.queues
    for queue in brief.queues:
        assert queue.count >= 1
    assert 1 <= len(brief.suggested_next_actions) <= 5
    seen = set()
    for action in brief.suggested_next_actions:
        assert action.tool.startswith("doxabase.")
        assert action.reason
        key = (action.tool, json.dumps(to_jsonable(action.args), sort_keys=True))
        assert key not in seen
        seen.add(key)


def test_project_brief_limit_bounds_dataset_rows_not_counts(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    db.import_trig(POLYMARKET_FIXTURE)

    brief = db.project_brief(limit=2)

    assert len(brief.datasets) == 2
    assert brief.dataset_count == 7


def test_project_brief_gate_stale_seed_recovery(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    _delete_base_ontology_seed_terms(
        db,
        ["rc:GraphPatchRole", "rc:CandidateRevision"],
    )

    brief = db.project_brief(limit=5)

    gate = next(g for g in brief.gates if g.gate == "stale_seed_recovery")
    assert gate.blocks == "mutation"
    assert gate.details_call == "doxabase.export_preflight"
    assert "immutable base_ontology is missing current staging vocabulary" in (
        gate.detail
    )
    first_action = brief.suggested_next_actions[0]
    assert first_action.tool == "doxabase.export_preflight"
    assert first_action.args == {
        "kind": "handoff_bundle",
        "graphs": ["project"],
        "limit": 20,
        "validation_scope": "map",
    }


def test_project_brief_gate_privacy_export_review_redacts(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_TOKEN_PROJECT_BRIEF"
    db.record_map_dataset(
        "https://example.test/project#CredentialNotes",
        label="Credential notes",
        description=f"Synthetic fixture {fake_secret}.",
    )

    brief = db.project_brief(limit=5)

    gate = next(g for g in brief.gates if g.gate == "privacy_export_review")
    assert gate.blocks == "export"
    assert gate.details_call == "doxabase.export_preflight"
    assert brief.datasets[0].label == "Credential notes"
    assert fake_secret not in json.dumps(to_dict(brief))


def test_project_brief_gate_export_validation_review(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rcg: <https://richcanopy.org/graph/> .

        rcg:observations {
            ex:obs_without_evidence a rc:Observation ;
                rc:summary "Scanner-clean invalid observation." .
        }
        """
    )

    brief = db.project_brief(limit=5)

    gate = next(g for g in brief.gates if g.gate == "export_validation_review")
    assert gate.blocks == "export"
    assert gate.details_call == "doxabase.validate_graph"
    validate_action = next(
        action
        for action in brief.suggested_next_actions
        if action.tool == "doxabase.validate_graph"
    )
    assert validate_action.args == {"scope": "all", "limit_results": 20}


def test_project_brief_gates_order_privacy_before_export_validation(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_TOKEN_ORDERING"
    db.record_map_dataset(
        "https://example.test/project#CredentialNotes",
        label="Credential notes",
        description=f"Synthetic fixture {fake_secret}.",
    )
    db.import_trig(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rcg: <https://richcanopy.org/graph/> .

        rcg:observations {
            ex:obs_without_evidence a rc:Observation ;
                rc:summary "Scanner-clean invalid observation." .
        }
        """
    )

    brief = db.project_brief(limit=5)

    gate_names = [gate.gate for gate in brief.gates]
    assert gate_names.index("privacy_export_review") < gate_names.index(
        "export_validation_review"
    )


def test_project_brief_gate_fixture_staleness_clears_with_storage(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://richcanopy.org/example/manifest/ais#DailyBroadcasts"
    db.record_map_dataset(
        dataset,
        label="AIS Daily Broadcast Positions",
        is_table=True,
    )

    brief = db.project_brief(limit=5)

    gate = next(g for g in brief.gates if g.gate == "query_fixture_staleness")
    assert gate.blocks == "none"
    assert gate.details_call == "doxabase.describe_query_context"
    assert "zero rc:StorageAccess" in gate.detail
    assert any(
        queue.name == "query_repair_review" for queue in brief.queues
    )

    db.record_map_storage_access(
        "https://example.test/project#ais_storage",
        datasets=[dataset],
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/tmp/ais-fixture",
    )
    repaired = db.project_brief(limit=5)
    assert all(
        gate.gate != "query_fixture_staleness" for gate in repaired.gates
    )


def test_project_brief_gate_staged_recovery_session(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = db.stage_graph_revision(
        summary="Stage messages table",
        rationale="Messages should become durable map context after review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Messages a rc:Dataset .
                """,
            }
        ],
    )
    session = db.start_staged_revision_recovery_session(
        [staged.revision_iri],
        summary="Recovery for staged messages table",
    )

    brief = db.project_brief(limit=5)

    gate = next(g for g in brief.gates if g.gate == "staged_revision_recovery")
    assert gate.blocks == "mutation"
    assert gate.details_call == (
        "doxabase.plan_staged_revision_recovery"
    )
    first_action = brief.suggested_next_actions[0]
    assert first_action.tool == (
        "doxabase.plan_staged_revision_recovery"
    )
    assert first_action.args["session_iri"] == session.session_iri
    frontier_queue = next(
        queue
        for queue in brief.queues
        if queue.name == "staged_frontier_review"
    )
    assert frontier_queue.example_iri == session.session_iri
    assert any(queue.name == "staged_review" for queue in brief.queues)


def test_project_brief_queue_examples_point_at_resources(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(dataset, label="Orders", is_table=True)

    brief = db.project_brief(limit=5)

    context_queue = next(
        queue
        for queue in brief.queues
        if queue.name in {"query_context_review", "query_repair_review"}
    )
    assert context_queue.example_iri == dataset
    assert brief.datasets[0].iri == dataset
    assert brief.datasets[0].is_table is True
