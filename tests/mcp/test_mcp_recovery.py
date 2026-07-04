"""Split from test_mcp_tools.py (distillation Phase 2); tests verbatim."""

from tests.mcp.support_mcp import *  # noqa: F401,F403


def test_import_handoff_bundle_tool_gates_invalid_manifest_recovery(
    tmp_path: Path,
) -> None:
    source = DoxaBase.create(tmp_path / "source.sqlite")
    source.import_trig(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rcg: <https://richcanopy.org/graph/> .

        rcg:observations {
            ex:obs_without_evidence a rc:Observation ;
                rc:summary "This observation intentionally keeps the handoff invalid." .
        }
        """
    )
    staged = stage_graph_revision_tool(
        source,
        summary="Stage invalid handoff receiver MCP probe",
        rationale="Create a recoverable staged row in an invalid diagnostic handoff.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:InvalidMcpHandoffImportProbe a rc:Dataset .
                """,
            }
        ],
    )
    trig_path = tmp_path / "invalid-project-handoff.trig"
    snapshot_path = tmp_path / "invalid-revision-snapshots.json"
    manifest_path = tmp_path / "invalid-handoff-manifest.json"
    exported = export_handoff_bundle_tool(
        source,
        trig_path=str(trig_path),
        revision_snapshot_path=str(snapshot_path),
        manifest_path=str(manifest_path),
        revision_iris=[staged["revision_iri"]],
        fail_on_invalid=False,
    )
    assert exported["would_block_invalid_export"] is True
    assert exported["validation_conforms"] is False

    receiver = DoxaBase.create(tmp_path / "receiver.sqlite")
    imported = import_handoff_bundle_tool(
        receiver,
        manifest_path=str(manifest_path),
    )

    assert imported["recovery_plan"]["processed_revision_iris"] == [
        staged["revision_iri"]
    ]
    assert [action["tool_name"] for action in imported["suggested_next_actions"]] == [
        "validate_graph"
    ]
    validation_action = imported["suggested_next_actions"][0]
    assert validation_action["mutation_scope"] == "none"
    assert validation_action["mutates_project_graph"] is False
    assert validation_action["writes_history"] is False
    assert validation_action["writes_files"] is False
    assert validation_action["writes_storage"] is False
    assert imported["recovery_summary"]["recommended_next_step"] == (
        "review_handoff_validation_before_recovery"
    )
    assert imported["recovery_summary"].get("first_mutation_action") is None
    assert imported["recovery_summary"].get("first_mutation_frontier_item") is None
    assert imported["recovery_summary"][
        "first_safe_review_or_mutation_action"
    ] == validation_action
    assert imported["recovery_summary"][
        "first_safe_review_or_mutation_source"
    ] == "handoff_import_validation_review"
    assert imported["recovery_plan"]["mutation_allowed_after"] == (
        "handoff_import_validation_review_required_before_recovery"
    )
    assert imported["recovery_plan"].get("next_action_queue_items", []) == []
    assert imported["recovery_plan"].get("mutation_frontier_items", []) == []
    assert [
        step["step_kind"]
        for step in imported["recovery_plan"]["recommended_unattended_steps"]
    ] == ["review_handoff_validation"]
    assert imported["recovery_plan"]["recommended_unattended_steps"][0][
        "action"
    ] == validation_action
    assert "apply_staged_revision" not in json.dumps(
        imported["recovery_plan"],
        sort_keys=True,
    )


def test_plan_staged_revision_recovery_tool_accepts_empty_revision_list(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    result = plan_staged_revision_recovery_tool(
        db,
        revision_iris=[],
        current_staged_work_only=False,
        drift_detail="exact",
    )

    assert result["selection_mode"] == "explicit_revision_iris"
    assert result.get("requested_revision_iris", []) == []
    assert result.get("processed_revision_iris", []) == []
    assert result["current_staged_work_only"] is False
    assert result["drift_detail"] == "exact"
    assert result["count"] == 0
    assert result["returned_count"] == 0
    assert result["total_count"] == 0
    assert result.get("lane_counts", {}) == {}
    assert result.get("next_action_queue", {}) == {}
    assert result.get("next_action_queue_items", []) == []
    assert result.get("mutation_frontier_iris", []) == []
    assert result["mutation_allowed_after"] == "no_mutation_frontier"
    assert result.get("suggested_next_actions", []) == []


def test_draft_staged_revision_rebase_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    event_framing = db.stage_graph_revision(
        summary="Model Orders as event rows",
        rationale="First alternative for row-grain review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders a rc:Dataset, rc:Table ;
                        rc:rowSemantics rc:EventRow .
                """,
            }
        ],
        revision_anchors=[orders],
    )
    snapshot_framing = db.stage_graph_revision(
        summary="Model Orders as snapshot rows",
        rationale="Competing row-grain alternative.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders a rc:Dataset, rc:Table ;
                        rc:rowSemantics rc:SnapshotRow .
                """,
            }
        ],
        alternative_to=event_framing.revision_iri,
        revision_anchors=[orders],
    )
    db.record_map_dataset(
        "https://example.test/project#DriftDataset",
        label="Drift dataset",
    )
    event_successor = db.restage_staged_revision(event_framing.revision_iri)
    db.apply_staged_revision(event_successor.revision_iri)
    snapshot_successor = db.restage_staged_revision(snapshot_framing.revision_iri)

    result = draft_staged_revision_rebase_tool(
        db,
        iri=snapshot_successor.revision_iri,
    )

    assert result["helper"] == "draft_staged_revision_rebase"
    assert result["mode"] == "non_executed_review_draft"
    assert result["source_revision_iri"] == snapshot_successor.revision_iri
    assert result["draft_status"] == "drafted"
    assert result["draft_kind"] == "same_slot_replacement"
    assert result["apply_check"]["status"] == "validation_failed"
    assert result["lineage"]["alternative_gate_status"] == (
        "alternative_to_applied_source"
    )
    assert result["apply_check"]["first_safe_next_action"]["tool_name"] == (
        "describe_staged_revision"
    )
    assert result["apply_check"]["first_safe_next_action"]["queue"] == (
        "semantic_review_required"
    )
    assert result["apply_check"]["first_safe_next_action"]["mutation_scope"] == (
        "none"
    )
    assert result["repair_actions"][0]["tool_name"] == (
        "stage_map_assertion_change"
    )
    assert result["repair_actions"][0]["arguments"]["restages_revision"] == (
        snapshot_successor.revision_iri
    )
    assert result["repair_candidates"][0]["proposed_triples"][0]["object"] == (
        RC + "SnapshotRow"
    )
    assert result["next_action"]["source"] == "draft_staged_revision_rebase"
    assert result["next_action_queue_item"]["alternative_gate_status"] == (
        "alternative_to_applied_source"
    )
    assert (
        result["next_action_queue_item"][
            "requires_semantic_review_before_mutation"
        ]
        is True
    )


def test_plan_staged_revision_recovery_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = stage_graph_revision_tool(
        db,
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

    result = plan_staged_revision_recovery_tool(db)

    assert result["result_kind"] == "staged_revision_recovery_plan"
    assert result["helper"] == "plan_staged_revision_recovery"
    assert result["mode"] == "read_only_plan"
    assert result["selection_mode"] == "current_staged_work"
    assert result["processed_revision_iris"] == [staged["revision_iri"]]
    assert result["lane_counts"] == {"apply_after_review": 1}
    assert result.get("repair_or_replace_source_revision_iris", []) == []
    assert result["next_action_queue_item_counts"] == {
        "apply_after_review": 1
    }
    assert result["mutation_frontier_iris"] == [staged["revision_iri"]]
    assert (
        result["mutation_allowed_after"]
        == "semantic_review_required_before_mutation"
    )
    assert result.get("blocking_preflight_actions", []) == []
    assert result.get("blocking_preflight_calls", []) == []
    assert result["requires_recheck_after_each_apply"] is False
    lane = result["lanes"][0]
    assert lane["source_revision_iri"] == staged["revision_iri"]
    assert lane["row_iri"] == staged["revision_iri"]
    assert lane["lane"] == "apply_after_review"
    assert lane["effective_recovery_action"] == "apply_after_review"
    assert lane["batch_action"] == "skipped_not_restageable"
    assert lane["not_restageable_reason"] == "ready"
    assert lane.get("exact_drift_summary", []) == []
    assert lane["next_action"]["tool_name"] == "apply_staged_revision"
    assert lane["next_action"]["mutation_scope"] == "project_graph_and_history"
    assert lane["next_action"]["mutates_project_graph"] is True
    assert lane["next_action"]["writes_history"] is True
    assert lane["next_action"]["writes_files"] is False
    assert lane["next_action"]["writes_storage"] is False
    assert lane["next_action_queue_item"]["resolved_target_iri"] == (
        staged["revision_iri"]
    )
    assert (
        lane["next_action_queue_item"][
            "requires_semantic_review_before_mutation"
        ]
        is False
    )
    assert result["first_mutation_action"] == lane["next_action"]
    assert result["first_mutation_call"] == lane["next_action"]["call"]
    review_action = result["suggested_next_actions"][0]
    assert review_action["tool_name"] == "describe_staged_revision"
    assert review_action["mutation_scope"] == "none"
    assert review_action["mutates_project_graph"] is False
    assert review_action["writes_history"] is False
    assert review_action["writes_files"] is False
    assert review_action["writes_storage"] is False
    assert result["first_safe_review_or_mutation_action"] == review_action
    assert (
        result["first_safe_review_or_mutation_call"]
        == review_action["call"]
    )
    assert (
        result["first_safe_review_or_mutation_source"]
        == "suggested_review_action"
    )
    assert result["mutation_frontier_items"] == [
        {
            "item_kind": "revision_target",
            "queue": "apply_after_review",
            "target_iri": staged["revision_iri"],
            "target_record_kind": "staged_patch",
            "source_revision_iris": [staged["revision_iri"]],
            "row_iris": [staged["revision_iri"]],
            "action": lane["next_action"],
            "call": lane["next_action"]["call"],
            "semantic_risk_level": "none",
            "alternative_gate_statuses": ["not_applicable"],
            "requires_semantic_review_before_mutation": False,
            "reason": (
                "Resolved staged-revision mutation target. Review the row and "
                "action, then mutate this target before replanning if required."
            ),
        }
    ]
    steps = result["recommended_unattended_steps"]
    assert [step["step_kind"] for step in steps] == [
        "review_frontier_target",
        "mutate_one_frontier_target",
    ]
    assert steps[0]["action"] == review_action
    assert steps[0]["can_run_now"] is True
    assert steps[0]["mutates"] is False
    assert steps[0]["requires_replan_after_completion"] is False
    assert steps[0]["stop_reason"] == "review_frontier_target_before_mutation"
    assert steps[0]["revision_iris"] == [staged["revision_iri"]]
    assert steps[1]["action"] == lane["next_action"]
    assert steps[1]["can_run_now"] is False
    assert steps[1]["prerequisite"] == "after_reviewing_frontier_target"
    assert steps[1]["mutates"] is True
    assert steps[1]["requires_replan_after_completion"] is True
    assert steps[1]["stop_reason"] == "apply_at_most_one_then_replan"
    assert result["bundle_summary"]["next_action_queue"] == {
        "apply_after_review": [staged["revision_iri"]]
    }
    assert result["bundle_summary"]["mutation_frontier_iris"] == [
        staged["revision_iri"]
    ]
    assert result["bundle_summary"]["requires_recheck_after_each_apply"] is False
    assert result["note"].startswith("Read-only staged revision recovery plan")


def test_shared_systematisation_recovery_drafts_no_surgery_rerun(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    shared_ontology = """
        @prefix ex: <https://example.test/shared-recovery#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:ReviewScope a rdfs:Class ;
            rdfs:label "Review scope" .

        ex:requiredColumn a rdf:Property ;
            rdfs:label "required column" .

        ex:ReviewScopePattern a rdfs:Class ;
            rdfs:subClassOf rc:Pattern ;
            rdfs:label "Review scope pattern" .
    """
    shared_shape = """
        @prefix ex: <https://example.test/shared-recovery#> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .

        ex:ReviewScopeShape a sh:NodeShape ;
            sh:targetClass ex:ReviewScope ;
            sh:property [
                sh:path ex:requiredColumn ;
                sh:minCount 1 ;
                sh:nodeKind sh:IRI ;
                sh:message "Review scopes must name a required column."
            ] .
    """
    map_framing = """
        @prefix ex: <https://example.test/shared-recovery#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:orders_status_scope a ex:ReviewScope ;
            rdfs:label "Orders status review scope" ;
            ex:requiredColumn ex:orders_status .
    """
    pattern_framing = """
        @prefix ex: <https://example.test/shared-recovery#> .
        @prefix dcterms: <http://purl.org/dc/terms/> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:orders_status_scope_pattern a rc:Pattern, ex:ReviewScopePattern ;
            rdfs:label "Orders status review pattern" ;
            rc:summary "Orders status review needs semantic context." ;
            rc:patternText "Keep the status review as lore until more tables agree." ;
            rc:rationale "The pattern is a fallback to the map scope." ;
            rc:patternTarget ex:orders_status ;
            rc:evidence ex:orders_status_scope_evidence ;
            rc:patternStability rc:EmergingPattern .

        ex:orders_status_scope_evidence a rc:Evidence ;
            rc:summary "Synthetic support." ;
            dcterms:source "test://shared-recovery" .
    """

    draft = stage_systematisation_tool(
        db,
        summary="Recover shared review scope alternatives",
        intent="Probe shared context in recovery lanes.",
        shared_additions=[
            {"graph": "ontology", "content": shared_ontology},
            {"graph": "shapes", "content": shared_shape},
        ],
        framings=[
            {"label": "Map scope", "graph": "map", "content": map_framing},
            {
                "label": "Pattern fallback",
                "graph": "patterns",
                "content": pattern_framing,
            },
        ],
        validation_scope="all",
    )
    revision_iris = [
        revision["revision_iri"] for revision in draft["staged_revisions"]
    ]
    assert draft["next_action_queue_item_counts"] == {"apply_after_review": 2}
    assert draft["choose_one_group_count"] == 1
    assert draft["choose_one_groups"][0]["revision_iris"] == revision_iris
    assert draft["choose_one_groups"][0]["row_indexes"] == [1, 2]
    assert draft["choose_one_groups"][0]["source_row_index"] == 1
    assert draft["choose_one_groups"][0]["alternative_set_roles"] == [
        "source",
        "alternative",
    ]

    replace_graph_triples_tool(
        db,
        graph="ontology",
        additions="""
            @prefix ex: <https://example.test/shared-recovery#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            ex:UnrelatedRecoveryDriftTerm a rdfs:Class ;
                rdfs:label "Unrelated recovery drift term" .
        """,
        allow_count_change=True,
    )

    plan = plan_staged_revision_recovery_tool(
        db,
        revision_iris=revision_iris,
        drift_detail="exact",
    )

    assert plan["lane_counts"] == {"restage_after_review": 2}
    assert plan["bundle_summary"]["shared_context_graphs"] == [
        "ontology",
        "shapes",
    ]
    assert [
        summary["target_graph"]
        for summary in plan["bundle_summary"]["shared_context_patch_summaries"]
    ] == ["ontology", "shapes"]
    assert (
        plan["bundle_summary"][
            "fallback_revision_iris_with_shared_semantic_context"
        ]
        == revision_iris[1:]
    )
    assert [
        warning["warning_code"]
        for warning in plan["bundle_summary"]["shared_semantic_context_warnings"]
    ] == ["shared_semantic_context_applies_to_all_framings"]
    assert [
        (
            lane["lane"],
            lane["shared_context_applies"],
            lane["shared_context_patch_count"],
            lane["shared_context_graphs"],
        )
        for lane in plan["lanes"]
    ] == [
        ("restage_after_review", True, 2, ["ontology", "shapes"]),
        ("restage_after_review", True, 2, ["ontology", "shapes"]),
    ]

    rerun_draft = draft_systematisation_shared_context_rerun_tool(
        db,
        revision_iris=revision_iris,
        shared_context_target_revision_iris=[revision_iris[0]],
    )

    assert rerun_draft["result_kind"] == (
        "systematisation_shared_context_rerun_draft"
    )
    assert rerun_draft["mode"] == "read_only_draft"
    assert rerun_draft["shared_context_graphs"] == ["ontology", "shapes"]
    assert rerun_draft["shared_context_target_revision_iris"] == [
        revision_iris[0]
    ]
    assert [
        (
            framing["source_revision_iri"],
            framing["receives_shared_context"],
            framing["moved_shared_patch_count"],
        )
        for framing in rerun_draft["framings"]
    ] == [
        (revision_iris[0], True, 2),
        (revision_iris[1], False, 0),
    ]
    rerun_args = rerun_draft["stage_systematisation_arguments"]
    assert "shared_additions" not in rerun_args
    assert rerun_args["link_alternatives"] is False
    assert [framing["label"] for framing in rerun_args["framings"]] == [
        "Map scope",
        "Pattern fallback",
    ]
    assert rerun_args["framings"][1]["alternative_to_framing_index"] == 1
    assert [
        [patch["graph"] for patch in framing["additions"]]
        for framing in rerun_args["framings"]
    ] == [["ontology", "shapes", "map"], ["patterns"]]
    assert rerun_draft["suggested_next_actions"][0]["tool_name"] == (
        "stage_systematisation"
    )

    rerun = stage_systematisation_tool(db, **rerun_args)

    assert rerun["next_action_queue_item_counts"] == {"apply_after_review": 2}
    assert [
        warning["warning_code"] for warning in rerun.get("structured_warnings", [])
    ] == []
    rerun_revision_iris = [
        revision["revision_iri"] for revision in rerun["staged_revisions"]
    ]
    assert rerun["choose_one_group_count"] == 1
    assert rerun["choose_one_groups"][0]["revision_iris"] == rerun_revision_iris
    assert rerun["choose_one_groups"][0]["alternative_set_roles"] == [
        "source",
        "alternative",
    ]

    rerun_export_path = tmp_path / "shared-context-rerun-review.md"
    rerun_export = export_staged_revisions_tool(
        db,
        revision_iris=rerun_revision_iris,
        path=str(rerun_export_path),
        title="Shared context rerun alternatives",
    )
    rerun_exported = rerun_export_path.read_text(encoding="utf-8")

    assert rerun_export["bundle_summary"]["choose_one_groups"][0][
        "revision_iris"
    ] == rerun_revision_iris
    assert "- Choose-one groups:" in rerun_exported
    assert "- Choose-one groups: none" not in rerun_exported

    session = start_staged_revision_recovery_session_tool(
        db,
        revision_iris=revision_iris,
        drift_detail="exact",
    )
    assert [
        (
            lane["lane"],
            lane["shared_context_applies"],
            lane["shared_context_patch_count"],
            lane["shared_context_graphs"],
        )
        for lane in session["current_plan"]["lanes"]
    ] == [
        ("restage_after_review", True, 2, ["ontology", "shapes"]),
        ("restage_after_review", True, 2, ["ontology", "shapes"]),
    ]

    restaged = restage_staged_revisions_tool(db, revision_iris, dry_run=False)

    assert restaged["restaged_revision_iris"]
    assert restaged["bundle_summary"]["shared_context_graphs"] == [
        "ontology",
        "shapes",
    ]
    assert all(
        summary["shared_context_patch_count"] == 2
        and summary["shared_context_graphs"] == ["ontology", "shapes"]
        for summary in restaged["revision_summaries"]
    )


def test_staged_revision_recovery_session_tools_return_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = stage_graph_revision_tool(
        db,
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
    record_map_dataset_tool(
        db,
        iri="https://example.test/project#OtherDataset",
        label="Other dataset",
    )
    manifest_path = tmp_path / "handoff-manifest.json"

    session = start_staged_revision_recovery_session_tool(
        db,
        revision_iris=[staged["revision_iri"]],
        summary="MCP recovery session",
        handoff_manifest_path=str(manifest_path),
        drift_detail="exact",
    )

    assert session["result_kind"] == "staged_revision_recovery_session"
    assert session["helper"] == "start_staged_revision_recovery_session"
    assert session["mode"] == "recorded_session"
    assert session["session_status"] == "active"
    assert session["source_revision_iris"] == [staged["revision_iri"]]
    assert session["handoff_manifest_path"] == str(manifest_path)
    assert session["repair_draft_limit"] == 1
    assert session["current_plan"]["repair_draft_limit"] == 1
    assert session["current_plan"]["lane_counts"] == {"restage_after_review": 1}
    assert session["source_states"][0]["workflow_state"] == "active"
    assert session["source_states"][0]["effective_recovery_action"] == (
        "restage_after_review"
    )
    assert session["source_states"][0]["next_action_tool_name"] == (
        "restage_staged_revision"
    )

    restaged = restage_staged_revision_tool(db, staged["revision_iri"])
    described = describe_staged_revision_recovery_session_tool(
        db,
        session_iri=session["session_iri"],
        drift_detail="exact",
    )

    assert described["helper"] == "describe_staged_revision_recovery_session"
    assert described["mode"] == "read_only_description"
    assert described["repair_draft_limit"] == 1
    assert described["current_plan"]["repair_draft_limit"] == 1
    assert described["current_plan"]["lane_counts"] == {"apply_after_review": 1}
    assert described["source_states"][0]["current_revision_iri"] == (
        restaged["revision_iri"]
    )
    assert described["source_states"][0]["effective_recovery_action"] == (
        "apply_after_review"
    )
    assert described["source_states"][0]["next_action_tool_name"] == (
        "apply_staged_revision"
    )


def test_plan_staged_revision_recovery_tool_promotes_handoff_snapshot_import(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "source.sqlite")
    staged = stage_graph_revision_tool(
        db,
        summary="Stage live messages table",
        rationale="Exercise RDF-only handoff planning through the MCP wrapper.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:LiveMessages a rc:Dataset .
                """,
            }
        ],
    )
    project_path = tmp_path / "project.trig"
    export_trig_tool(db, path=str(project_path), graphs="project")
    imported = DoxaBase.create(tmp_path / "rdf-only.sqlite")
    imported.import_trig(project_path)

    result = plan_staged_revision_recovery_tool(
        imported,
        revision_iris=[staged["revision_iri"]],
    )

    assert result["lane_counts"] == {"complete_handoff_import": 1}
    assert result["next_action_queue"] == {
        "complete_handoff_import": [staged["revision_iri"]]
    }
    assert result["bundle_summary"]["snapshot_evidence"]["complete"] is False
    assert result["suggested_next_actions"][0]["tool_name"] == (
        "import_revision_snapshots"
    )
    assert result["mutation_allowed_after"] == (
        "handoff_preflight_required_before_mutation"
    )
    assert result["blocking_preflight_actions"][0]["tool_name"] == (
        "import_revision_snapshots"
    )
    assert result["blocking_preflight_calls"] == [
        result["suggested_next_actions"][0]["call"]
    ]
    assert result.get("first_mutation_action") is None
    assert result.get("first_mutation_call") is None
    assert (
        result["first_safe_review_or_mutation_action"]
        == result["blocking_preflight_actions"][0]
    )
    assert (
        result["first_safe_review_or_mutation_call"]
        == result["blocking_preflight_calls"][0]
    )
    assert result["first_safe_review_or_mutation_source"] == "blocking_preflight"
    assert result["lanes"][0]["lane"] == "complete_handoff_import"
    assert result["lanes"][0]["next_action"]["tool_name"] == (
        "import_revision_snapshots"
    )
    assert result["lanes"][0]["suggested_next_actions"][0]["tool_name"] == (
        "import_revision_snapshots"
    )
    assert any(
        action["tool_name"] == "apply_staged_revision"
        for action in result["lanes"][0]["suggested_next_actions"][1:]
    )
    assert "Snapshot evidence is incomplete" in result["warnings"][0]


def test_plan_staged_revision_recovery_tool_suggests_batch_restage_dry_run(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = stage_graph_revision_tool(
        db,
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
    record_map_dataset_tool(
        db,
        iri="https://example.test/project#Drift",
        label="Drift",
    )

    result = plan_staged_revision_recovery_tool(
        db,
        revision_iris=[staged["revision_iri"]],
    )

    assert result["would_restage_revision_iris"] == [staged["revision_iri"]]
    lane = result["lanes"][0]
    assert len(lane["exact_drift_summary"]) == 1
    summary = lane["exact_drift_summary"][0]
    assert summary["graph_role"] == "map"
    assert summary["blocking_reasons"] == ["target_count_drift"]
    assert summary["has_count_drift"] is True
    assert summary["has_snapshot_digest_drift"] is True
    assert summary["count_drift_count"] == 1
    assert summary["count_drift_deltas"] == [2]
    assert summary["patch_triple_status_counts"] == {
        "all_patch_triples_absent": 1
    }
    assert summary["snapshot_triple_count"] == 0
    assert summary["current_triple_count"] == 2
    assert summary["triples_added_since_snapshot_count"] == 2
    assert summary["triples_removed_since_snapshot_count"] == 0
    assert summary["exact_changed_triples_available"] is True
    assert summary["exact_changed_triples_included"] is False
    assert summary["drift_relevance"] == "broad_patch_object_overlap"
    assert summary["changed_resource_count"] == 2
    assert summary["changed_resources_returned_count"] == 2
    assert summary["changed_resources_omitted_count"] == 0
    assert summary["changed_resources"][0]["resource"]["iri"] == (
        "https://richcanopy.org/ns/rc#Dataset"
    )
    assert summary["changed_resources"][0]["matched_by"] == [
        "patch_object",
        "changed_object",
    ]
    assert summary["changed_resources"][1]["resource"]["iri"] == (
        "https://example.test/project#Drift"
    )
    assert summary["changed_resources"][1]["matched_by"] == ["changed_subject"]
    assert [
        action["tool_name"]
        for action in summary["changed_resource_suggested_next_actions"]
    ] == ["describe_resource_revision_lineage", "list_resource_revisions"]
    assert summary["note"] == (
        "Count drift summarizes patch-level count checks for this graph. "
        "Snapshot drift summarizes graph-level count/digest drift; raw "
        "changed triples are intentionally omitted from this compact "
        "recovery-lane field."
    )
    assert lane["batch_item"]["exact_drift_summary_before"] == (
        lane["exact_drift_summary"]
    )
    assert lane["batch_item"]["exact_drift_summary_after"] == (
        lane["exact_drift_summary"]
    )
    batch_action = result["suggested_next_actions"][0]
    assert batch_action["tool_name"] == "restage_staged_revisions"
    assert batch_action["mcp_tool_name"] == "doxabase.restage_staged_revisions"
    assert batch_action["arguments"] == {
        "revision_iris": [staged["revision_iri"]],
        "dry_run": True,
    }
    assert batch_action["mutation_scope"] == "none"
    assert batch_action["mutates_project_graph"] is False
    assert batch_action["writes_history"] is False
    assert batch_action["writes_files"] is False
    assert batch_action["writes_storage"] is False
    steps = result["recommended_unattended_steps"]
    assert [step["step_kind"] for step in steps[:2]] == [
        "dry_run_mechanical_restage",
        "run_reviewed_mechanical_restage",
    ]
    assert steps[0]["action"] == batch_action
    assert steps[0]["can_run_now"] is True
    assert steps[0]["mutates"] is False
    assert steps[0]["requires_replan_after_completion"] is False
    assert steps[0]["revision_iris"] == [staged["revision_iri"]]
    assert steps[1]["action"]["tool_name"] == "restage_staged_revisions"
    assert steps[1]["action"]["arguments"] == {
        "revision_iris": [staged["revision_iri"]],
        "dry_run": False,
    }
    assert steps[1]["can_run_now"] is False
    assert steps[1]["prerequisite"] == "after_reviewing_matching_dry_run"
    assert steps[1]["mutates"] is True
    assert steps[1]["requires_replan_after_completion"] is True
    assert steps[1]["stop_reason"] == "rerun_plan_after_restage"
    assert result["first_mutation_action"] == result["mutation_frontier_items"][0][
        "action"
    ]
    assert result["first_mutation_call"] == result["mutation_frontier_items"][0][
        "call"
    ]
    assert result["first_safe_review_or_mutation_action"] == batch_action
    assert result["first_safe_review_or_mutation_call"] == batch_action["call"]
    assert (
        result["first_safe_review_or_mutation_source"]
        == "suggested_review_action"
    )
    assert any(
        action["tool_name"] == "restage_staged_revision"
        and action["arguments"] == {"iri": staged["revision_iri"]}
        for action in result["suggested_next_actions"]
    )


def test_plan_staged_revision_recovery_tool_uses_embedded_no_repair_draft_route(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    record_map_dataset_tool(db, iri=orders, label="Orders", is_table=True)
    staged = stage_graph_revision_tool(
        db,
        summary="Model Orders with invalid row-semantics object",
        rationale="The invalid object should require manual repair review.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders rc:rowSemantics "snapshot" .
                """,
            }
        ],
        revision_anchors=[orders],
    )
    record_map_dataset_tool(db, iri=orders, row_semantics="rc:EventRow")

    result = plan_staged_revision_recovery_tool(
        db,
        revision_iris=[staged["revision_iri"]],
    )

    assert result["repair_first_revision_iris"] == [staged["revision_iri"]]
    assert result["repair_or_replace_source_revision_iris"] == [
        staged["revision_iri"]
    ]
    assert result["repair_draft_limit"] == 1
    assert result["repair_draft_attempted_count"] == 1
    assert result["repair_drafts_included_count"] == 1
    assert result["repair_drafts_deferred_count"] == 0
    lane = result["lanes"][0]
    assert lane["repair_draft"]["draft_kind"] == "validation_repair_needed"
    assert lane.get("repair_draft_deferred_reason") is None
    assert lane["next_action"]["tool_name"] != "draft_staged_revision_rebase"
    assert all(
        action["tool_name"] != "draft_staged_revision_rebase"
        for action in lane["suggested_next_actions"]
    )
    assert all(
        action["tool_name"] != "draft_staged_revision_rebase"
        for action in result["suggested_next_actions"]
    )

    zero_draft_result = plan_staged_revision_recovery_tool(
        db,
        revision_iris=[staged["revision_iri"]],
        repair_draft_limit=0,
    )
    assert zero_draft_result["repair_draft_limit"] == 0
    assert zero_draft_result["repair_draft_attempted_count"] == 0
    assert zero_draft_result["repair_drafts_included_count"] == 0
    assert zero_draft_result["repair_drafts_deferred_count"] == 1
    zero_lane = zero_draft_result["lanes"][0]
    assert zero_lane.get("repair_draft") is None
    assert zero_lane["repair_draft_deferred_reason"] == (
        "repair_draft_limit_reached"
    )
    assert zero_lane["next_action"]["tool_name"] == "draft_staged_revision_rebase"
    assert any(
        "repair_draft_limit=0" in warning
        for warning in zero_draft_result["warnings"]
    )


def test_stage_systematisation_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    observation = db.record_observation(
        "Message-like rows repeatedly require identity reasoning.",
        evidence_summary="Synthetic test note backing the staged systematisation.",
        evidence_sources=["test://identity-ladder"],
    )
    ontology_framing = """
    @prefix ex: <https://example.test/project#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:IdentityLadder a rdfs:Class ;
        rdfs:label "Identity ladder" .
    """
    pattern_framing = f"""
    @prefix ex: <https://example.test/project#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:IdentityLadderPattern a rc:Pattern ;
        rdfs:label "Identity ladder pattern" ;
        rc:summary "Identity hints become stronger as more columns agree." ;
        rc:patternText "Repeated message-like rows appear to form a ladder of identity hints." ;
        rc:rationale "This keeps the idea exploratory without forcing a single key model." ;
        rc:patternTarget ex:Messages ;
        rc:supportingObservation <{observation.observation_iri}> ;
        rc:patternStability rc:EmergingPattern .
    """
    map_framing = """
    @prefix ex: <https://example.test/project#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:Messages a rc:Dataset, rc:Table ;
        rdfs:label "Messages" .
    """

    result = stage_systematisation_tool(
        db,
        summary="Explore identity-ladder modelling",
        intent="Preserve two possible RDF shapes for the same modelling hunch.",
        anchors=[observation.observation_iri],
        shared_additions=[{"graph": "ontology", "content": ontology_framing}],
        shared_context_summary="Define provisional identity-ladder vocabulary once.",
        framings=[
            {
                "label": "Pattern first",
                "graph": "patterns",
                "content": pattern_framing,
                "review_note": "The pattern framing keeps the idea tentative.",
                "review_recommendation": "Preferred until the map vocabulary settles.",
            },
            {
                "label": "Map candidate",
                "graph": "map",
                "content": map_framing,
                "stance": "rc:CandidateRevision",
                "reviewNote": "This is reviewable but slightly too early.",
                "reviewRecommendation": "Keep as a concrete alternative.",
            },
        ],
    )

    assert result["result_kind"] == "systematisation_draft"
    assert result["summary"] == "Explore identity-ladder modelling"
    assert result["anchors"] == [observation.observation_iri]
    assert result["profile_route_source_count"] == 0
    assert len(result["framings"]) == 2
    assert len(result["staged_revisions"]) == 2
    revision_iris = [
        revision["revision_iri"] for revision in result["staged_revisions"]
    ]
    assert [
        (revision["framing_index"], revision["framing_label"])
        for revision in result["staged_revisions"]
    ] == [(1, "Pattern first"), (2, "Map candidate")]
    assert [
        (framing["revision_iri"], framing["label"])
        for framing in result["framings"]
    ] == [
        (revision_iris[0], "Pattern first"),
        (revision_iris[1], "Map candidate"),
    ]
    assert result["next_action_queue"] == {"apply_after_review": revision_iris}
    assert result["next_action_queue_item_counts"] == {"apply_after_review": 2}
    assert result.get("semantic_review_required_queue_counts", {}) == {}
    assert len(result["structured_warnings"]) == 1
    shared_warning = result["structured_warnings"][0]
    assert shared_warning["warning_code"] == (
        "shared_semantic_context_applies_to_all_framings"
    )
    assert shared_warning["message"] == result["warnings"][-1]
    assert shared_warning["affected_revision_iris"] == revision_iris
    assert shared_warning["suggested_action"] == (
        "rerun_with_shared_semantic_context_moved_to_framings"
    )
    assert shared_warning["suggested_rerun_arguments"] == {
        "move_shared_patch_graphs_into_framing_patches": ["ontology"],
        "shared_patch_sources_to_move": [
            {
                "source_argument": "shared_additions",
                "source_index": 0,
                "operation": "addition",
                "graph": "ontology",
            }
        ],
        "target_framing_selection_required": True,
        "target_framing_selection_note": (
            "Choose which framings should receive the moved ontology/shapes "
            "patches. fallback_revision_iris_with_shared_semantic_context is "
            "an inspection subset of later framings currently carrying shared "
            "context, not an automatic drop list."
        ),
    }
    assert shared_warning["fallback_revision_iris_with_shared_semantic_context"] == [
        revision_iris[1]
    ]
    assert shared_warning["shared_patch_summaries"] == [
        {
            "target_graph": "ontology",
            "operation": RC + "AdditionPatch",
            "operation_label": "addition patch",
            "patch_role": RC + "SharedContextPatch",
            "patch_role_label": "shared context patch",
            "sequence_index": 1,
            "triple_count": 2,
            "count_basis": "target_graph_plus_base_ontology",
            "format": "turtle",
        }
    ]
    assert [
        item["row_iri"] for item in result["next_action_queue_items"]
    ] == revision_iris
    assert [
        item["resolved_target_iri"] for item in result["next_action_queue_items"]
    ] == revision_iris
    assert all(item["row_is_target"] for item in result["next_action_queue_items"])
    assert [
        item["alternative_set_iris"] for item in result["next_action_queue_items"]
    ] == [revision_iris, revision_iris]
    assert [
        item["alternative_set_source_iri"]
        for item in result["next_action_queue_items"]
    ] == [revision_iris[0], revision_iris[0]]
    assert [
        item["alternative_set_role"] for item in result["next_action_queue_items"]
    ] == ["source", "alternative"]
    assert result["suggested_next_actions"][0]["tool_name"] == (
        "export_staged_revisions"
    )
    assert result["suggested_next_actions"][0]["arguments"]["revision_iris"] == (
        revision_iris
    )
    assert (
        result["suggested_next_actions"][0]["arguments"]["fail_on_sensitive"]
        is True
    )
    assert result["suggested_next_actions"][0]["arguments"]["path"].startswith(
        "/tmp/systematisation-review-"
    )
    assert result["suggested_next_actions"][0]["arguments"]["path"].endswith(".md")
    assert [
        action["arguments"]
        for action in result["suggested_next_actions"]
        if action["tool_name"] == "check_staged_revision_apply"
    ] == [{"iri": revision_iri} for revision_iri in revision_iris]
    assert result["staged_revisions"][0]["summary"] == (
        "Explore identity-ladder modelling: Pattern first"
    )
    assert result["staged_revisions"][0]["review_note"] == (
        "The pattern framing keeps the idea tentative."
    )
    assert result["staged_revisions"][0]["review_recommendation"] == (
        "Preferred until the map vocabulary settles."
    )
    assert result["staged_revisions"][1]["summary"] == (
        "Explore identity-ladder modelling: Map candidate"
    )
    assert result["staged_revisions"][1]["review_note"] == (
        "This is reviewable but slightly too early."
    )
    assert result["staged_revisions"][1]["review_recommendation"] == (
        "Keep as a concrete alternative."
    )
    assert result["framings"][0]["target_graphs"] == ["ontology", "patterns"]
    assert result["framings"][1]["target_graphs"] == ["ontology", "map"]
    assert result["framings"][0]["validation_conforms"] is True
    assert result["framings"][1]["validation_conforms"] is True
    assert result["framings"][0]["review_note"] == (
        "The pattern framing keeps the idea tentative."
    )
    assert result["framings"][1]["review_recommendation"] == (
        "Keep as a concrete alternative."
    )

    first_iri = result["staged_revisions"][0]["revision_iri"]
    second = describe_staged_revision_tool(
        db,
        result["staged_revisions"][1]["revision_iri"],
    )
    assert second["alternative_to"]["iri"] == first_iri
    assert second["revision_anchors"][0]["iri"] == observation.observation_iri
    assert second["patches"][0]["patch_role_label"] == "shared context patch"
    assert second["patches"][1]["patch_role_label"] == "framing patch"
    assert "Systematisation intent:" in second["rationale"]

    export_path = tmp_path / "identity-ladder-review.md"
    export = export_staged_revisions_tool(
        db,
        revision_iris=revision_iris,
        path=str(export_path),
        title="Identity ladder MCP bundle",
        executive_summary="Pattern-first is preferred, but both framings remain useful.",
    )
    exported = export_path.read_text(encoding="utf-8")
    assert export["revision_iris"] == [
        revision["revision_iri"] for revision in result["staged_revisions"]
    ]
    assert export["revision_count"] == 2
    assert export["bundle_summary"]["shared_context_graphs"] == ["ontology"]
    assert export["bundle_summary"][
        "fallback_revision_iris_with_shared_semantic_context"
    ] == [revision_iris[1]]
    assert export["bundle_summary"]["shared_context_patch_summaries"] == [
        {
            "target_graph": "ontology",
            "operation": RC + "AdditionPatch",
            "operation_label": "addition patch",
            "patch_role": RC + "SharedContextPatch",
            "patch_role_label": "shared context patch",
            "sequence_index": 1,
            "triple_count": 2,
            "count_basis": "target_graph_plus_base_ontology",
            "format": "turtle",
        }
    ]
    assert len(export["bundle_summary"]["shared_semantic_context_warnings"]) == 1
    assert export["bundle_summary"]["shared_semantic_context_warnings"][0][
        "warning_code"
    ] == "shared_semantic_context_applies_to_all_framings"
    assert [
        summary["shared_context_patch_count"]
        for summary in export["revision_summaries"]
    ] == [1, 1]
    assert [
        summary["shared_context_graphs"] for summary in export["revision_summaries"]
    ] == [["ontology"], ["ontology"]]
    assert exported.startswith("# Identity ladder MCP bundle\n")
    assert "## Review Summary" in exported
    assert "Pattern-first is preferred" in exported
    assert "Shared ontology or shapes context patches are present" in exported
    assert export["bundle_summary"]["changed_graph_counts"] == {
        "ontology": 2,
        "patterns": 1,
        "map": 1,
    }
    assert export["bundle_summary"]["choose_one_groups"] == [
        {
            "group_index": 1,
            "row_indexes": [1, 2],
            "revision_iris": revision_iris,
            "summaries": [
                "Explore identity-ladder modelling: Pattern first",
                "Explore identity-ladder modelling: Map candidate",
            ],
            "alternative_set_source_iri": revision_iris[0],
            "source_row_index": 1,
            "source_summary": "Explore identity-ladder modelling: Pattern first",
            "alternative_set_roles": ["source", "alternative"],
        }
    ]
    assert "## At A Glance" in exported
    assert "- Choose-one groups:" in exported
    assert (
        "  - Rows 1 and 2: apply at most one "
        "(Explore identity-ladder modelling: Pattern first, "
        "Explore identity-ladder modelling: Map candidate)."
    ) in exported
    assert "## Reviewer Decision Matrix" in exported
    assert "Rows 1 and 2 are competing alternatives" in exported
    assert "Authored recommendation" in exported
    assert "Preferred until the map vocabulary settles." in exported
    assert "The pattern framing keeps the idea tentative." in exported
    assert "## Summary" in exported
    assert "Pattern first" in exported
    assert "Map candidate" in exported


def test_stage_systematisation_tool_warns_when_first_anchor_fails(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    shared_shape = """
    @prefix ex: <https://example.test/project#> .
    @prefix sh: <http://www.w3.org/ns/shacl#> .

    ex:ThingShape a sh:NodeShape ;
        sh:targetClass ex:Thing ;
        sh:property [
            sh:path ex:required ;
            sh:minCount 1
        ] .
    """
    incomplete_map = """
    @prefix ex: <https://example.test/project#> .

    ex:Thing1 a ex:Thing .
    """
    complete_map = """
    @prefix ex: <https://example.test/project#> .

    ex:Thing1 a ex:Thing ;
        ex:required ex:Value .
    """
    complementary_map = """
    @prefix ex: <https://example.test/project#> .

    ex:Thing1 a ex:Thing ;
        ex:required ex:OtherValue .
    """

    result = stage_systematisation_tool(
        db,
        summary="Compare thing framings",
        intent="Keep a diagnostic invalid framing beside valid map framings.",
        shared_additions=[{"graph": "shapes", "content": shared_shape}],
        framings=[
            {
                "label": "Diagnostic incomplete thing",
                "graph": "map",
                "content": incomplete_map,
            },
            {
                "label": "Complete thing",
                "graph": "map",
                "content": complete_map,
            },
            {
                "label": "Complementary complete thing",
                "graph": "map",
                "content": complementary_map,
            },
        ],
    )

    revision_iris = [
        revision["revision_iri"] for revision in result["staged_revisions"]
    ]
    assert result["next_action_queue"] == {
        "repair_or_replace": [revision_iris[0]],
        "apply_after_review": [revision_iris[1], revision_iris[2]],
    }
    assert any(
        "First framing 'Diagnostic incomplete thing'" in warning
        and "failed staged validation" in warning
        and revision_iris[0] in warning
        and "link_alternatives=False" in warning
        for warning in result["warnings"]
    )
    assert len(result["structured_warnings"]) == 2
    shared_warning = result["structured_warnings"][0]
    assert shared_warning["warning_code"] == (
        "shared_semantic_context_applies_to_all_framings"
    )
    assert shared_warning["message"] == result["warnings"][-2]
    assert shared_warning["affected_revision_iris"] == revision_iris
    assert shared_warning["suggested_action"] == (
        "rerun_with_shared_semantic_context_moved_to_framings"
    )
    assert shared_warning["suggested_rerun_arguments"] == {
        "move_shared_patch_graphs_into_framing_patches": ["shapes"],
        "shared_patch_sources_to_move": [
            {
                "source_argument": "shared_additions",
                "source_index": 0,
                "operation": "addition",
                "graph": "shapes",
            }
        ],
        "target_framing_selection_required": True,
        "target_framing_selection_note": (
            "Choose which framings should receive the moved ontology/shapes "
            "patches. fallback_revision_iris_with_shared_semantic_context is "
            "an inspection subset of later framings currently carrying shared "
            "context, not an automatic drop list."
        ),
    }
    assert shared_warning["fallback_revision_iris_with_shared_semantic_context"] == [
        revision_iris[1],
        revision_iris[2],
    ]
    assert shared_warning["shared_patch_summaries"] == [
        {
            "target_graph": "shapes",
            "operation": RC + "AdditionPatch",
            "operation_label": "addition patch",
            "patch_role": RC + "SharedContextPatch",
            "patch_role_label": "shared context patch",
            "sequence_index": 1,
            "triple_count": 5,
            "count_basis": "target_graph_plus_base_shapes",
            "format": "turtle",
        }
    ]
    anchor_warning = result["structured_warnings"][1]
    assert anchor_warning == {
        "warning_code": "first_alternative_anchor_not_ready",
        "message": result["warnings"][-1],
        "affected_revision_iris": revision_iris,
        "suggested_action": "rerun_with_explicit_alternative_routing",
        "suggested_rerun_arguments": {"link_alternatives": False},
    }
    rerun_action = result["suggested_next_actions"][0]
    assert rerun_action["tool_name"] == "stage_systematisation"
    assert rerun_action["action_label"] == (
        "Rerun with explicit alternative routing"
    )
    assert rerun_action["arguments"]["summary"] == "Compare thing framings"
    assert rerun_action["arguments"]["link_alternatives"] is False
    assert rerun_action["arguments"]["shared_additions"] == [
        {"graph": "shapes", "content": shared_shape}
    ]
    assert [
        framing["label"] for framing in rerun_action["arguments"]["framings"]
    ] == [
        "Diagnostic incomplete thing",
        "Complete thing",
        "Complementary complete thing",
    ]
    assert "link_alternatives=False" in rerun_action["reason"]
    assert result["suggested_next_actions"][1]["tool_name"] == (
        "export_staged_revisions"
    )
    export_path = tmp_path / "invalid-first-review.md"
    export = export_staged_revisions_tool(
        db,
        revision_iris=revision_iris,
        path=str(export_path),
        title="Invalid first framing review",
    )
    assert export["bundle_summary"]["next_action_queue"] == {
        "repair_or_replace": [revision_iris[0]],
        "apply_after_review": [revision_iris[1], revision_iris[2]],
    }
    exported = export_path.read_text(encoding="utf-8")
    assert "## Review Queues" in exported
    assert "Diagnostic incomplete thing" in exported
    assert "Complementary complete thing" in exported


def test_stage_systematisation_tool_suppresses_anchor_warning_for_explicit_sibling_alternatives(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    explicit_target = db.stage_graph_revision(
        summary="Existing comparison anchor",
        rationale="A staged source revision that explicit alternatives can target.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .

                    ex:PreferredComparisonAnchor ex:note "Anchor revision." .
                """,
            }
        ],
    ).revision_iri
    shared_shape = """
    @prefix ex: <https://example.test/project#> .
    @prefix sh: <http://www.w3.org/ns/shacl#> .

    ex:ThingShape a sh:NodeShape ;
        sh:targetClass ex:Thing ;
        sh:property [
            sh:path ex:required ;
            sh:minCount 1
        ] .
    """
    incomplete_map = """
    @prefix ex: <https://example.test/project#> .

    ex:Thing1 a ex:Thing .
    """
    complete_map = """
    @prefix ex: <https://example.test/project#> .

    ex:Thing1 a ex:Thing ;
        ex:required ex:Value .
    """
    complementary_map = """
    @prefix ex: <https://example.test/project#> .

    ex:Thing1 a ex:Thing ;
        ex:required ex:OtherValue .
    """

    result = stage_systematisation_tool(
        db,
        summary="Compare explicitly routed thing framings",
        intent=(
            "Keep a diagnostic invalid framing beside valid framings that use "
            "their own comparison anchor."
        ),
        shared_additions=[{"graph": "shapes", "content": shared_shape}],
        framings=[
            {
                "label": "Diagnostic incomplete thing",
                "graph": "map",
                "content": incomplete_map,
            },
            {
                "label": "Complete thing",
                "graph": "map",
                "content": complete_map,
                "alternative_to": explicit_target,
            },
            {
                "label": "Complementary complete thing",
                "graph": "map",
                "content": complementary_map,
                "alternative_to": explicit_target,
            },
        ],
    )

    revision_iris = [
        revision["revision_iri"] for revision in result["staged_revisions"]
    ]
    assert result["next_action_queue"] == {
        "repair_or_replace": [revision_iris[0]],
        "apply_after_review": [revision_iris[1], revision_iris[2]],
    }
    assert len(result["structured_warnings"]) == 1
    shared_warning = result["structured_warnings"][0]
    assert shared_warning["warning_code"] == (
        "shared_semantic_context_applies_to_all_framings"
    )
    assert shared_warning["message"] == result["warnings"][-1]
    assert shared_warning["affected_revision_iris"] == revision_iris
    assert shared_warning["suggested_action"] == (
        "rerun_with_shared_semantic_context_moved_to_framings"
    )
    assert shared_warning["suggested_rerun_arguments"] == {
        "move_shared_patch_graphs_into_framing_patches": ["shapes"],
        "shared_patch_sources_to_move": [
            {
                "source_argument": "shared_additions",
                "source_index": 0,
                "operation": "addition",
                "graph": "shapes",
            }
        ],
        "target_framing_selection_required": True,
        "target_framing_selection_note": (
            "Choose which framings should receive the moved ontology/shapes "
            "patches. fallback_revision_iris_with_shared_semantic_context is "
            "an inspection subset of later framings currently carrying shared "
            "context, not an automatic drop list."
        ),
    }
    assert shared_warning["fallback_revision_iris_with_shared_semantic_context"] == [
        revision_iris[1],
        revision_iris[2],
    ]
    assert shared_warning["shared_patch_summaries"] == [
        {
            "target_graph": "shapes",
            "operation": RC + "AdditionPatch",
            "operation_label": "addition patch",
            "patch_role": RC + "SharedContextPatch",
            "patch_role_label": "shared context patch",
            "sequence_index": 1,
            "triple_count": 5,
            "count_basis": "target_graph_plus_base_shapes",
            "format": "turtle",
        }
    ]
    assert not any(
        "First framing 'Diagnostic incomplete thing'" in warning
        for warning in result["warnings"]
    )
    assert not any(
        "linked as an alternative to the first" in warning
        or "linked as alternatives to the first" in warning
        for warning in result["warnings"]
    )
    assert result["staged_revisions"][0].get("alternative_to") is None
    assert result["staged_revisions"][1]["alternative_to"] == explicit_target
    assert result["staged_revisions"][2]["alternative_to"] == explicit_target


def test_context_slice_export_tool_warns_history_not_recovery_handoff(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    record_map_dataset_tool(db, dataset, label="Orders", is_table=True)
    staged = stage_graph_revision_tool(
        db,
        summary="Stage Orders MCP caveat",
        rationale="Create history-backed staged work for context-slice export.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:OrdersMcpCaveat a rc:KnownCaveat ;
                        rdfs:label "Orders MCP caveat" ;
                        rc:caveatDescription "Synthetic caveat for MCP export routing." .
                """,
            }
        ],
        revision_anchors=[dataset],
        included_graphs=["map"],
    )

    preflight = preflight_context_slice_export_tool(
        db,
        seed_iris=[staged["revision_iri"]],
        profile="deep_lore",
        max_triples=400,
    )

    assert "history" in preflight["graphs"]
    assert any(
        "not a recovery-complete revision handoff" in warning
        for warning in preflight["warnings"]
    )
    assert [
        action["tool_name"] for action in preflight["suggested_next_actions"]
    ] == [
        "export_context_slice",
        "export_handoff_bundle",
    ]
    handoff_action = preflight["suggested_next_actions"][1]
    assert handoff_action["mcp_tool_name"] == "doxabase.export_handoff_bundle"
    assert handoff_action["arguments"]["revision_iris"] == [staged["revision_iri"]]
    assert handoff_action["arguments"]["manifest_path"] == (
        "<handoff-manifest.json>"
    )
    assert handoff_action["required_extra_arguments"] == [
        "trig_path",
        "revision_snapshot_path",
        "manifest_path",
    ]
    assert handoff_action["placeholder_fields"] == [
        "trig_path",
        "revision_snapshot_path",
        "manifest_path",
    ]
    assert handoff_action["reviewed_value_fields"] == [
        "trig_path",
        "revision_snapshot_path",
        "manifest_path",
    ]

    export_path = tmp_path / "revision-context.trig"
    export = export_context_slice_tool(
        db,
        path=str(export_path),
        seed_iris=[staged["revision_iri"]],
        profile="deep_lore",
        max_triples=400,
        fail_on_sensitive=True,
    )

    assert export["path"] == str(export_path)
    assert "history" in export["graphs"]
    assert [
        action["tool_name"] for action in export["suggested_next_actions"]
    ] == ["export_handoff_bundle"]
    assert export["suggested_next_actions"][0]["arguments"]["revision_iris"] == [
        staged["revision_iri"]
    ]
    assert export["suggested_next_actions"][0]["arguments"]["manifest_path"] == (
        "<handoff-manifest.json>"
    )
    assert export["suggested_next_actions"][0]["placeholder_fields"] == [
        "trig_path",
        "revision_snapshot_path",
        "manifest_path",
    ]

