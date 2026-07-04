"""Split from test_mcp_tools.py (distillation Phase 2); tests verbatim."""

from tests.mcp.support_mcp import *  # noqa: F401,F403


def test_export_tools_write_review_artifacts(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)
    graph_path = tmp_path / "map.ttl"
    trig_path = tmp_path / "bundle.trig"

    graph_result = export_graph_tool(db, path=str(graph_path), graphs=["map"])
    trig_result = export_trig_tool(
        db,
        path=str(trig_path),
    )

    assert graph_result["path"] == str(graph_path)
    assert graph_result["format"] == "turtle"
    assert graph_result["graphs"] == ["map"]
    assert graph_result["graph_counts"] == {"map": db.triple_count("map")}
    assert graph_result["triples"] == db.triple_count("map")
    assert graph_result["sensitive_literal_count"] == 0
    assert graph_result["privacy_warnings"] == []
    assert graph_result["artifact_kind"] == "graph_rdf_export"
    assert graph_result["importable"] is True
    assert graph_result["recommended_import_tool"] == "DoxaBase.import_turtle"
    assert graph_result["recovery_complete"] is False
    assert graph_path.exists()

    assert trig_result["path"] == str(trig_path)
    assert trig_result["format"] == "trig"
    assert trig_result["graphs"] == [
        "ontology",
        "map",
        "observations",
        "patterns",
        "evidence",
        "shapes",
        "history",
    ]
    assert "base_ontology" not in trig_result["graphs"]
    assert trig_result["sensitive_literal_count"] == 0
    assert trig_result["privacy_warnings"] == []
    assert trig_result["artifact_kind"] == "project_trig"
    assert trig_result["importable"] is True
    assert trig_result["recommended_import_tool"] == "doxabase.import_trig"
    assert trig_result["recovery_complete"] is False
    assert trig_result["triples"] == sum(trig_result["graph_counts"].values())
    assert trig_path.exists()


def test_scan_sensitive_literals_tool_returns_redacted_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_123"
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#orders_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        storage_root=f"/tmp/{fake_secret}/orders",
        credential_reference=f"Bearer {fake_secret}",
    )
    record_map_dataset_tool(
        db,
        iri="https://example.test/project#Orders",
        label="Orders",
        is_table=True,
        storage_accesses=[storage["iri"]],
    )

    result = scan_sensitive_literals_tool(db, graphs=["map"], limit=5)

    assert result["graphs"] == ["map"]
    assert result["match_count"] >= 2
    assert result["sensitive_literal_count"] == result["match_count"]
    assert result["returned_match_count"] >= 2
    assert result["warnings"]
    assert fake_secret not in str(result["matches"])
    assert all("redacted_snippet" in match for match in result["matches"])
    assert all("term_position" in match for match in result["matches"])
    assert all("term_kind" in match for match in result["matches"])


def test_export_preflight_tool_returns_conservative_redacted_decision(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_PREFLIGHT_MCP"
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#orders_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=f"/tmp/{fake_secret}/orders",
    )
    record_map_dataset_tool(
        db,
        iri="https://example.test/project#Orders",
        label="Orders",
        is_table=True,
        storage_accesses=[storage["iri"]],
    )

    result = export_preflight_tool(
        db,
        export_kind="graph",
        graphs=["map"],
        limit=1,
    )

    assert result["export_kind"] == "graph"
    assert result["decision"] == "block"
    assert result["scanner_clean"] is False
    assert result["shareability_review_required"] is True
    assert result["shareability_review_status"] == "required_not_completed"
    assert result["would_block_sensitive_export"] is True
    assert result["graphs"] == ["map"]
    assert result["graph_sensitive_literal_count"] >= 1
    assert result["sensitive_literal_count"] >= 1
    assert result["returned_match_count"] == 1
    assert result["omitted_match_count"] == (
        result["sensitive_literal_count"] - result["returned_match_count"]
    )
    assert result["matches"][0]["match_id"].startswith("redacted-sha256:")
    assert result["suggested_next_actions"][0]["tool_name"] == "scan_sensitive_literals"
    assert result["suggested_next_actions"][-1]["tool_name"] == (
        "preflight_context_slice_export"
    )
    assert result["suggested_next_actions"][-1]["arguments"]["seed_iris"] == [
        "<target-resource-iri>"
    ]
    assert result["suggested_next_actions"][-1]["required_extra_arguments"] == [
        "seed_iris"
    ]
    assert result["suggested_next_actions"][-1]["placeholder_fields"] == [
        "seed_iris"
    ]
    assert result["suggested_next_actions"][-1]["reviewed_value_fields"] == [
        "seed_iris"
    ]
    assert not any(
        "Scanner-clean means" in warning for warning in result["warnings"]
    )
    assert fake_secret not in json.dumps(result)


def test_export_preflight_tool_reports_shareability_hints_for_home_paths(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#orders_home_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/Users/example/private/orders.csv",
    )
    record_map_dataset_tool(
        db,
        iri="https://example.test/project#Orders",
        label="Orders",
        is_table=True,
        storage_accesses=[storage["iri"]],
    )

    result = export_preflight_tool(db, export_kind="graph", graphs=["map"])

    assert result["decision"] == "clean_by_scanner_only"
    assert result["scanner_clean"] is True
    assert result["would_block_sensitive_export"] is False
    assert result["sensitive_literal_count"] == 0
    assert result["privacy_warnings"] == []
    assert result["shareability_hints"] == ["absolute_local_home_path"]
    assert result["shareability_hint_count"] == 1
    assert result["returned_shareability_hint_count"] == 1
    assert result["omitted_shareability_hint_count"] == 0
    assert result["shareability_hint_matches"][0]["export_part"] == "graphs"
    assert result["shareability_hint_matches"][0]["hint_code"] == (
        "absolute_local_home_path"
    )
    assert result["shareability_hint_matches"][0]["predicate"] == (
        RC + "storageRoot"
    )
    assert "/Users/example/private/orders.csv" not in json.dumps(
        result["shareability_hint_matches"]
    )
    assert result["artifact_disposition"] == (
        "local_only_pending_shareability_review"
    )
    assert result["git_safe"] is False
    assert any(
        "absolute local home/private path" in warning
        for warning in result["warnings"]
    )


def test_export_preflight_tool_reports_invalid_graph_gate(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rcg: <https://richcanopy.org/graph/> .

        rcg:observations {
            ex:obs_without_evidence a rc:Observation ;
                rc:summary "This observation should block MCP exports." .
        }
        """
    )

    result = export_preflight_tool(db, export_kind="handoff_bundle", limit=5)

    assert result["decision"] == "block"
    assert result["scanner_clean"] is True
    assert result["would_block_sensitive_export"] is False
    assert result["would_block_invalid_export"] is True
    assert result["validation_scope"] == "all"
    assert result["validation_conforms"] is False
    assert result["validation_result_count"] > 0
    assert result["validation_results"]
    assert result["suggested_next_actions"][0]["tool_name"] == "validate_graph"

    with pytest.raises(DoxaBaseError, match="fail_on_invalid=True"):
        export_trig_tool(db, str(tmp_path / "blocked-invalid.trig"))
    assert not (tmp_path / "blocked-invalid.trig").exists()

    override = export_trig_tool(
        db,
        str(tmp_path / "reviewed-invalid.trig"),
        fail_on_invalid=False,
    )

    assert override["validation_scope"] == "all"
    assert override["validation_conforms"] is False
    assert override["validation_result_count"] > 0
    assert override["would_block_invalid_export"] is True
    assert any(
        "Export validation failed" in warning for warning in override["warnings"]
    )


def test_export_preflight_tool_marks_handoff_path_placeholders(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    record_map_dataset_tool(
        db,
        iri="https://example.test/project#Orders",
        label="Orders",
        is_table=True,
    )

    result = export_preflight_tool(db, export_kind="handoff_bundle")

    assert result["decision"] == "clean_by_scanner_only"
    action = result["suggested_next_actions"][0]
    assert action["tool_name"] == "export_handoff_bundle"
    assert action["arguments"]["trig_path"] == "<project-handoff.trig>"
    assert action["arguments"]["revision_snapshot_path"] == (
        "<revision-snapshots.json>"
    )
    assert action["arguments"]["manifest_path"] == "<handoff-manifest.json>"
    assert action["required_extra_arguments"] == [
        "trig_path",
        "revision_snapshot_path",
        "manifest_path",
    ]
    assert action["placeholder_fields"] == [
        "trig_path",
        "revision_snapshot_path",
        "manifest_path",
    ]
    assert action["reviewed_value_fields"] == [
        "trig_path",
        "revision_snapshot_path",
        "manifest_path",
    ]


def test_mcp_export_tools_block_sensitive_predicate_iris(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_PREDICATE_MCP"
    predicate_iri = f"https://example.test/project#{fake_secret}"
    db.import_turtle(
        f"""
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:Orders a rc:Dataset ;
            <{predicate_iri}> "predicate-only MCP privacy probe" .
        """,
        graph="map",
    )
    revision = db.record_graph_revision(
        summary="Record predicate MCP privacy probe",
        rationale=(
            "Capture a map snapshot whose sensitive-looking term is only a "
            "predicate IRI."
        ),
        changed_graphs=["map"],
        included_graphs=["map"],
    )

    scan = scan_sensitive_literals_tool(db, graphs=["map"], limit=10)

    assert scan["match_count"] >= 1
    assert any(match["term_position"] == "predicate" for match in scan["matches"])
    assert fake_secret not in str(scan["matches"])

    graph_path = tmp_path / "blocked-predicate.ttl"
    with pytest.raises(DoxaBaseError) as graph_excinfo:
        export_graph_tool(
            db,
            path=str(graph_path),
            graphs=["map"],
            fail_on_sensitive=True,
        )
    assert "fail_on_sensitive=True" in str(graph_excinfo.value)
    assert fake_secret not in str(graph_excinfo.value)
    assert not graph_path.exists()

    snapshot_path = tmp_path / "blocked-predicate-snapshots.json"
    with pytest.raises(DoxaBaseError) as snapshot_excinfo:
        export_revision_snapshots_tool(
            db,
            path=str(snapshot_path),
            revision_iris=[revision.revision_iri],
            fail_on_sensitive=True,
        )
    assert "fail_on_sensitive=True" in str(snapshot_excinfo.value)
    assert fake_secret not in str(snapshot_excinfo.value)
    assert not snapshot_path.exists()


def test_export_tools_can_block_sensitive_literals_before_writing(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_MCP"
    record_map_storage_access_tool(
        db,
        iri="https://example.test/project#orders_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=f"/tmp/{fake_secret}/orders",
    )

    graph_path = tmp_path / "blocked.ttl"
    with pytest.raises(DoxaBaseError) as excinfo:
        export_graph_tool(
            db,
            path=str(graph_path),
            graphs=["map"],
            fail_on_sensitive=True,
        )
    assert "fail_on_sensitive=True" in str(excinfo.value)
    assert fake_secret not in str(excinfo.value)
    assert not graph_path.exists()

    trig_path = tmp_path / "blocked.trig"
    with pytest.raises(DoxaBaseError):
        export_trig_tool(
            db,
            path=str(trig_path),
            graphs=["map"],
            fail_on_sensitive=True,
        )
    assert not trig_path.exists()


def test_export_revision_snapshots_tool_reports_sensitive_literals(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_SNAPSHOT_MCP"
    record_map_storage_access_tool(
        db,
        iri="https://example.test/project#orders_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=f"/tmp/{fake_secret}/orders",
    )
    staged = stage_graph_revision_tool(
        db,
        summary="Stage snapshot probe",
        rationale="Create a revision snapshot over the map graph.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:OrdersSnapshotProbe a rc:Dataset .
                """,
            }
        ],
    )

    snapshot_path = tmp_path / "revision-snapshots.json"
    result = export_revision_snapshots_tool(
        db,
        path=str(snapshot_path),
        revision_iris=[staged["revision_iri"]],
    )

    assert result["sensitive_literal_count"] >= 1
    assert result["privacy_warnings"]
    assert fake_secret not in " ".join(result["privacy_warnings"])
    assert fake_secret in snapshot_path.read_text(encoding="utf-8")

    blocked_path = tmp_path / "blocked-revision-snapshots.json"
    with pytest.raises(DoxaBaseError) as excinfo:
        export_revision_snapshots_tool(
            db,
            path=str(blocked_path),
            revision_iris=[staged["revision_iri"]],
            fail_on_sensitive=True,
        )
    assert "fail_on_sensitive=True" in str(excinfo.value)
    assert fake_secret not in str(excinfo.value)
    assert not blocked_path.exists()


def test_export_handoff_bundle_tool_writes_importable_pair(tmp_path: Path) -> None:
    source = DoxaBase.create(tmp_path / "source.sqlite")
    receiver = DoxaBase.create(tmp_path / "receiver.sqlite")
    dataset = "https://example.test/project#HandoffOrders"
    source.record_map_dataset(dataset, label="Handoff orders", is_table=True)
    route_source = {
        "review_lane": "query_context_review",
        "route_group_key": "query-context:HandoffOrders:missing-storage",
        "route_step_key": "profile-route-step:handoff-storage-repair",
        "blocking_issue_codes": ["missing_storage_access"],
        "route_anchor_iris": [dataset],
    }
    staged = stage_query_storage_access_repair_tool(
        source,
        dataset_iri=dataset,
        storage_access_iri="https://example.test/project#HandoffOrdersStorage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root="/tmp/doxabase-handoff-orders",
        location_kind="directory",
        rationale="Create a project/history RDF and snapshot handoff pair.",
        summary="Stage handoff storage repair",
        profile_route_sources=[route_source],
    )
    trig_path = tmp_path / "project-handoff.trig"
    snapshot_path = tmp_path / "revision-snapshots.json"
    manifest_path = tmp_path / "handoff-manifest.json"
    session = source.start_staged_revision_recovery_session(
        [staged["revision_iri"]],
        summary="Handoff source recovery session",
        handoff_manifest_path=str(manifest_path),
        current_staged_work_only=False,
        created_at="2026-06-01T12:00:00+00:00",
    )

    result = export_handoff_bundle_tool(
        source,
        trig_path=str(trig_path),
        revision_snapshot_path=str(snapshot_path),
        manifest_path=str(manifest_path),
        revision_iris=[staged["revision_iri"]],
    )

    assert result["paths"] == {
        "trig": str(trig_path),
        "revision_snapshots": str(snapshot_path),
        "manifest": str(manifest_path),
    }
    assert result["trig"]["path"] == str(trig_path)
    assert result["revision_snapshots"]["path"] == str(snapshot_path)
    assert result["manifest_path"] == str(manifest_path)
    assert result["manifest_bytes_written"] == len(
        manifest_path.read_text(encoding="utf-8").encode("utf-8")
    )
    assert result["graph_roles"] == [
        "ontology",
        "map",
        "observations",
        "patterns",
        "evidence",
        "shapes",
        "history",
    ]
    assert result["revision_iris"] == [staged["revision_iri"]]
    assert result["snapshot_graph_roles"] == ["map"]
    assert result["decision"] == "clean_by_scanner_only"
    assert result["scanner_clean"] is True
    assert result["shareability_review_required"] is True
    assert result["shareability_review_status"] == "required_not_completed"
    assert result["would_block_sensitive_export"] is False
    assert result["sensitive_literal_count"] == 0
    assert result["graph_sensitive_literal_count"] == 0
    assert result["snapshot_sensitive_literal_count"] == 0
    assert result["privacy_warnings"] == []
    assert any("Scanner-clean means" in warning for warning in result["warnings"])
    assert result["artifact_kind"] == "handoff_bundle"
    assert result["importable"] is True
    assert result["recommended_import_tool"] == "doxabase.import_handoff_bundle"
    assert result["recovery_complete"] is True
    assert result["trig"]["artifact_kind"] == "handoff_trig"
    assert result["trig"]["recommended_import_tool"] == "doxabase.import_trig"
    assert result["trig"]["recovery_complete"] is False
    assert result["revision_snapshots"]["artifact_kind"] == (
        "revision_snapshot_bundle"
    )
    assert result["revision_snapshots"]["recommended_import_tool"] == (
        "doxabase.import_revision_snapshots"
    )
    assert result["revision_snapshots"]["recovery_complete"] is False
    assert trig_path.exists()
    assert snapshot_path.exists()
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest == result["manifest"]
    assert manifest["format"] == "doxabase.handoff_bundle.v1"
    assert manifest["artifact_kind"] == "handoff_bundle"
    assert manifest["importable"] is True
    assert manifest["recommended_import_tool"] == "doxabase.import_handoff_bundle"
    assert manifest["recovery_complete"] is True
    assert manifest["decision"] == "clean_by_scanner_only"
    assert manifest["scanner_clean"] is True
    assert manifest["shareability_review_required"] is True
    assert manifest["shareability_review_status"] == "required_not_completed"
    assert manifest["would_block_sensitive_export"] is False
    assert manifest["graph_sensitive_literal_count"] == 0
    assert manifest["snapshot_sensitive_literal_count"] == 0
    assert any("Scanner-clean means" in warning for warning in manifest["warnings"])
    assert manifest["artifacts"]["trig"]["path"] == str(trig_path)
    assert manifest["artifacts"]["trig"]["artifact_kind"] == "handoff_trig"
    assert manifest["artifacts"]["revision_snapshots"]["path"] == str(snapshot_path)
    assert manifest["artifacts"]["revision_snapshots"]["artifact_kind"] == (
        "revision_snapshot_bundle"
    )
    assert [
        step["tool_name"] for step in manifest["recommended_import_sequence"]
    ] == ["import_trig", "import_revision_snapshots"]
    assert [
        step["expected_snapshot_evidence_status"]
        for step in manifest["recommended_import_sequence"]
    ] == ["history_only_count_digest", "history_plus_snapshot_rows"]

    manifest_receiver = DoxaBase.create(tmp_path / "manifest-receiver.sqlite")
    dry_run = import_handoff_bundle_tool(
        manifest_receiver,
        manifest_path=str(manifest_path),
        dry_run=True,
    )
    assert dry_run["dry_run"] is True
    assert dry_run["paths"] == {
        "trig": str(trig_path),
        "revision_snapshots": str(snapshot_path),
        "manifest": str(manifest_path),
    }
    assert dry_run["trig_imported"] == {}
    assert dry_run["trig_total_imported"] == 0
    assert dry_run["revision_snapshots"] is None
    assert dry_run["recovery_plan"] is None
    assert dry_run["imported_recovery_session_iris"] == []
    assert dry_run["matching_recovery_session_iris"] == []
    assert dry_run["recovery_summary"]["result_kind"] == (
        "handoff_bundle_recovery_summary"
    )
    assert dry_run["recovery_summary"]["dry_run"] is True
    assert dry_run["recovery_summary"]["snapshot_evidence_complete"] is False
    assert dry_run["recovery_summary"]["snapshot_evidence_status_counts"] == {
        "history_missing": 1,
    }
    assert dry_run["recovery_summary"]["recovery_plan_available"] is False
    assert dry_run["recovery_summary"]["first_mutation_action"] is None
    assert (
        dry_run["recovery_summary"]["first_safe_review_or_mutation_action"]
        is None
    )
    assert dry_run["recovery_summary"]["first_safe_review_or_mutation_call"] is None
    assert dry_run["recovery_summary"]["first_safe_review_or_mutation_source"] is None
    assert dry_run["recovery_summary"]["recommended_next_step"] == (
        "run_import_handoff_bundle"
    )
    assert dry_run["recovery_summary"]["first_suggested_next_action"][
        "tool_name"
    ] == "import_handoff_bundle"
    assert {
        item["revision_iri"]: item["status"]
        for item in dry_run["pre_import_snapshot_evidence"]
    } == {staged["revision_iri"]: "history_missing"}
    assert dry_run["suggested_next_actions"][0]["tool_name"] == (
        "import_handoff_bundle"
    )
    assert any(
        "shareability review is still required" in warning
        for warning in dry_run["warnings"]
    )
    assert (
        manifest_receiver.describe_revision_snapshot_evidence(
            staged["revision_iri"]
        ).status
        == "history_missing"
    )

    manifest_import = import_handoff_bundle_tool(
        manifest_receiver,
        manifest_path=str(manifest_path),
        drift_detail="exact",
    )
    assert manifest_import["dry_run"] is False
    assert manifest_import["trig_total_imported"] > 0
    assert manifest_import["revision_snapshots"]["imported_snapshot_count"] == 1
    assert {
        item["revision_iri"]: item["status"]
        for item in manifest_import["post_trig_snapshot_evidence"]
    } == {staged["revision_iri"]: "history_only_count_digest"}
    assert {
        item["revision_iri"]: item["status"]
        for item in manifest_import["post_import_snapshot_evidence"]
    } == {staged["revision_iri"]: "history_plus_snapshot_rows"}
    assert manifest_import["recovery_summary"]["dry_run"] is False
    assert manifest_import["recovery_summary"]["revision_count"] == 1
    assert (
        manifest_import["recovery_summary"]["snapshot_evidence_complete"]
        is True
    )
    assert manifest_import["recovery_summary"][
        "snapshot_evidence_status_counts"
    ] == {"history_plus_snapshot_rows": 1}
    assert manifest_import["recovery_summary"]["imported_snapshot_count"] == 1
    assert (
        manifest_import["recovery_summary"]["matching_recovery_session_count"]
        == 1
    )
    assert manifest_import["recovery_summary"]["recovery_lane_counts"] == {
        "apply_after_review": 1,
    }
    assert manifest_import["recovery_summary"][
        "recovery_next_action_queue_item_counts"
    ] == {"apply_after_review": 1}
    assert manifest_import["recovery_summary"]["mutation_frontier_iris"] == [
        staged["revision_iri"]
    ]
    assert manifest_import["recovery_summary"]["first_mutation_action"] is None
    assert manifest_import["recovery_summary"][
        "first_safe_review_or_mutation_action"
    ]["tool_name"] == "describe_staged_revision_recovery_session"
    assert manifest_import["recovery_summary"][
        "first_safe_review_or_mutation_action"
    ]["mutation_scope"] == "none"
    assert (
        manifest_import["recovery_summary"][
            "first_safe_review_or_mutation_action"
        ]["mutates_project_graph"]
        is False
    )
    assert (
        manifest_import["recovery_summary"][
            "first_safe_review_or_mutation_action"
        ]["writes_history"]
        is False
    )
    assert (
        manifest_import["recovery_summary"][
            "first_safe_review_or_mutation_action"
        ]["writes_files"]
        is False
    )
    assert (
        manifest_import["recovery_summary"][
            "first_safe_review_or_mutation_action"
        ]["writes_storage"]
        is False
    )
    assert manifest_import["recovery_summary"][
        "first_safe_review_or_mutation_action"
    ]["arguments"]["session_iri"] == manifest_import[
        "matching_recovery_session_iris"
    ][0]
    assert manifest_import["recovery_summary"][
        "first_safe_review_or_mutation_action"
    ]["arguments"]["drift_detail"] == "exact"
    assert manifest_import["recovery_summary"][
        "first_safe_review_or_mutation_call"
    ] == manifest_import["recovery_summary"][
        "first_safe_review_or_mutation_action"
    ]["call"]
    assert manifest_import["recovery_summary"][
        "first_safe_review_or_mutation_source"
    ] == "imported_recovery_session"
    assert (
        manifest_import["recovery_summary"]["first_mutation_frontier_item"]
        is None
    )
    assert manifest_import["recovery_summary"]["profile_route_revision_count"] == 1
    assert manifest_import["recovery_summary"]["profile_route_group_count"] == 1
    assert manifest_import["recovery_summary"]["profile_route_keys"] == [
        route_source["route_group_key"]
    ]
    assert manifest_import["recovery_summary"]["recommended_next_step"] == (
        "continue_imported_recovery_session"
    )
    assert manifest_import["recovery_summary"]["first_suggested_next_action"][
        "tool_name"
    ] == "describe_staged_revision_recovery_session"
    assert "Continue the imported source recovery session" in (
        manifest_import["recovery_summary"]["note"]
    )
    assert manifest_import["recovery_plan"]["lane_counts"] == {
        "apply_after_review": 1
    }
    assert manifest_import["imported_recovery_session_iris"] == [
        session.session_iri
    ]
    assert manifest_import["matching_recovery_session_iris"] == [
        session.session_iri
    ]
    assert manifest_import["suggested_next_actions"][0]["tool_name"] == (
        "describe_staged_revision_recovery_session"
    )
    assert manifest_import["suggested_next_actions"][0]["mutation_scope"] == "none"
    assert (
        manifest_import["suggested_next_actions"][0]["mutates_project_graph"]
        is False
    )
    assert manifest_import["suggested_next_actions"][0]["writes_history"] is False
    assert manifest_import["suggested_next_actions"][0]["writes_files"] is False
    assert manifest_import["suggested_next_actions"][0]["writes_storage"] is False
    assert manifest_import["suggested_next_actions"][0]["arguments"] == {
        "session_iri": session.session_iri,
        "drift_detail": "exact",
    }
    described_session = describe_staged_revision_recovery_session_tool(
        manifest_receiver,
        session_iri=session.session_iri,
        drift_detail="exact",
    )
    assert described_session["handoff_manifest_path"] == str(manifest_path)
    assert described_session["source_revision_iris"] == [staged["revision_iri"]]
    assert described_session["current_plan"]["lane_counts"] == {
        "apply_after_review": 1
    }
    assert manifest_import["recovery_plan"]["next_action_queue"] == {
        "apply_after_review": [staged["revision_iri"]]
    }
    assert manifest_import["recovery_plan"]["lanes"][0]["next_action"][
        "tool_name"
    ] == "apply_staged_revision"
    assert any(
        "shareability review is still required" in warning
        for warning in manifest_import["warnings"]
    )

    relative_manifest_path = tmp_path / "relative-handoff-manifest.json"
    relative_manifest = json.loads(json.dumps(manifest))
    relative_manifest["artifacts"]["trig"]["path"] = trig_path.name
    relative_manifest["artifacts"]["revision_snapshots"]["path"] = snapshot_path.name
    relative_manifest["recommended_import_sequence"][0]["path"] = trig_path.name
    relative_manifest["recommended_import_sequence"][1]["path"] = snapshot_path.name
    relative_manifest_path.write_text(
        json.dumps(relative_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    relative_receiver = DoxaBase.create(tmp_path / "relative-receiver.sqlite")
    relative_import = import_handoff_bundle_tool(
        relative_receiver,
        manifest_path=str(relative_manifest_path),
    )
    assert relative_import["paths"]["trig"] == str(tmp_path / trig_path.name)
    assert relative_import["paths"]["revision_snapshots"] == str(
        tmp_path / snapshot_path.name
    )
    assert {
        item["revision_iri"]: item["status"]
        for item in relative_import["post_import_snapshot_evidence"]
    } == {staged["revision_iri"]: "history_plus_snapshot_rows"}

    import_trig_tool(receiver, path=str(trig_path))
    before_snapshots = describe_revision_snapshot_evidence_tool(
        receiver,
        iri=staged["revision_iri"],
    )
    assert before_snapshots["status"] == "history_only_count_digest"

    import_revision_snapshots_tool(receiver, path=str(snapshot_path))
    after_snapshots = describe_revision_snapshot_evidence_tool(
        receiver,
        iri=staged["revision_iri"],
    )
    assert after_snapshots["status"] == "history_plus_snapshot_rows"
    assert after_snapshots["exact_snapshot_graph_roles"] == ["map"]


def test_import_handoff_bundle_tool_suggests_receiver_session_without_source_session(
    tmp_path: Path,
) -> None:
    source = DoxaBase.create(tmp_path / "source.sqlite")
    staged = stage_graph_revision_tool(
        source,
        summary="Stage receiver-local recovery handoff",
        rationale="Exercise import guidance when source has no persisted session.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:ReceiverLocalOrders a rc:Dataset, rc:Table .
                """,
            }
        ],
    )
    trig_path = tmp_path / "project-handoff.trig"
    snapshot_path = tmp_path / "revision-snapshots.json"
    manifest_path = tmp_path / "handoff-manifest.json"
    export_handoff_bundle_tool(
        source,
        trig_path=str(trig_path),
        revision_snapshot_path=str(snapshot_path),
        manifest_path=str(manifest_path),
        revision_iris=[staged["revision_iri"]],
    )

    receiver = DoxaBase.create(tmp_path / "receiver.sqlite")
    imported = import_handoff_bundle_tool(
        receiver,
        manifest_path=str(manifest_path),
    )

    assert imported["imported_recovery_session_iris"] == []
    assert imported["matching_recovery_session_iris"] == []
    assert imported["recovery_summary"]["recommended_next_step"] == (
        "start_receiver_local_recovery_session"
    )
    assert imported["recovery_summary"]["mutation_frontier_iris"] == [
        staged["revision_iri"]
    ]
    assert imported["recovery_summary"]["first_mutation_action"] is None
    assert imported["recovery_summary"]["first_mutation_frontier_item"] is None
    assert imported["recovery_summary"][
        "first_safe_review_or_mutation_action"
    ]["tool_name"] == "start_staged_revision_recovery_session"
    assert imported["recovery_summary"][
        "first_safe_review_or_mutation_action"
    ]["mutation_scope"] == "history"
    assert (
        imported["recovery_summary"]["first_safe_review_or_mutation_action"][
            "mutates_project_graph"
        ]
        is False
    )
    assert (
        imported["recovery_summary"]["first_safe_review_or_mutation_action"][
            "writes_history"
        ]
        is True
    )
    assert (
        imported["recovery_summary"]["first_safe_review_or_mutation_action"][
            "writes_files"
        ]
        is False
    )
    assert (
        imported["recovery_summary"]["first_safe_review_or_mutation_action"][
            "writes_storage"
        ]
        is False
    )
    assert imported["recovery_summary"][
        "first_safe_review_or_mutation_action"
    ]["arguments"]["revision_iris"] == [staged["revision_iri"]]
    assert imported["recovery_summary"][
        "first_safe_review_or_mutation_source"
    ] == "receiver_local_recovery_session"
    assert imported["recovery_summary"]["first_suggested_next_action"][
        "tool_name"
    ] == "start_staged_revision_recovery_session"
    assert imported["recovery_summary"]["first_safe_review_or_mutation_call"] == (
        imported["suggested_next_calls"][0]
    )
    assert "Start a receiver-local recovery session" in (
        imported["recovery_summary"]["note"]
    )
    assert imported["recovery_plan"]["processed_revision_iris"] == [
        staged["revision_iri"]
    ]
    action = imported["suggested_next_actions"][0]
    assert action["tool_name"] == "start_staged_revision_recovery_session"
    assert action["mutation_scope"] == "history"
    assert action["mutates_project_graph"] is False
    assert action["writes_history"] is True
    assert action["writes_files"] is False
    assert action["writes_storage"] is False
    assert action["arguments"]["revision_iris"] == [staged["revision_iri"]]
    assert action["arguments"]["handoff_manifest_path"] == str(manifest_path)
    assert action["arguments"]["current_staged_work_only"] is False


def test_import_handoff_bundle_tool_accepts_empty_revision_snapshot_bundle(
    tmp_path: Path,
) -> None:
    source = DoxaBase.create(tmp_path / "source.sqlite")
    source.record_map_dataset(
        "https://example.test/project#Customers",
        label="Customers",
        is_table=True,
    )
    receiver = DoxaBase.create(tmp_path / "receiver.sqlite")
    trig_path = tmp_path / "project-handoff.trig"
    snapshot_path = tmp_path / "revision-snapshots.json"
    manifest_path = tmp_path / "handoff-manifest.json"

    export = export_handoff_bundle_tool(
        source,
        trig_path=str(trig_path),
        revision_snapshot_path=str(snapshot_path),
        manifest_path=str(manifest_path),
    )

    assert export["revision_iris"] == []
    assert export["revision_snapshots"]["snapshot_count"] == 0

    imported = import_handoff_bundle_tool(
        receiver,
        manifest_path=str(manifest_path),
    )

    assert imported["revision_iris"] == []
    assert imported["revision_snapshots"]["imported_snapshot_count"] == 0
    assert imported["recovery_plan"]["selection_mode"] == "explicit_revision_iris"
    assert imported["recovery_plan"]["requested_revision_iris"] == []
    assert imported["recovery_plan"]["lane_counts"] == {}
    assert imported["recovery_plan"]["mutation_allowed_after"] == (
        "no_mutation_frontier"
    )
    assert imported["recovery_summary"]["revision_count"] == 0
    assert imported["recovery_summary"]["snapshot_evidence_complete"] is True
    assert imported["recovery_summary"]["first_mutation_action"] is None
    assert imported["recovery_summary"]["recommended_next_step"] == (
        "resume_project_frontier"
    )
    assert imported["suggested_next_actions"][0]["tool_name"] == "project_brief"
    assert imported["suggested_next_actions"][0]["arguments"] == {}
    assert imported["suggested_next_calls"] == ["project_brief()"]
    assert receiver.describe_dataset(
        "https://example.test/project#Customers",
    ).label == "Customers"


def test_draft_query_plan_tool_returns_database_relation_handoff(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_database_storage",
        label="Orders database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        path_templates=["mart.orders"],
        endpoint_profile="warehouse-prod",
        credential_reference="profile:warehouse-readonly",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    layout = db.record_map_physical_layout(
        "https://example.test/project#orders_table_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    result = draft_query_plan_tool(db, iri=dataset)

    assert result["selected_candidate"]["candidate_path"] == "mart.orders"
    assert result["selected_candidate"]["relation_identifier"] == "mart.orders"
    assert result["selected_candidate"]["connection_reference"] == "warehouse-prod"
    assert result["selected_candidate"]["composition"] == (
        "database_connection_and_relation"
    )
    assert result["scan"]["function"] is None
    assert result["scan"]["uri_template"] is None
    assert result["scan"]["relation_identifier"] == "mart.orders"
    assert result["scan"]["connection_reference"] == "warehouse-prod"
    assert result["handoff_summary"]["relation_identifier"] == "mart.orders"
    assert result["handoff_summary"]["connection_reference"] == "warehouse-prod"
    assert result["scan"]["composition"] == "database_connection_and_relation"
    assert result["scan"]["execution_attempt_ready"] is False
    assert result["scan"]["execution_attempt_blocking_reason_codes"] == [
        "runtime_resolution_required",
    ]
    assert result["review_gate"]["blocking_reason_codes"] == []
    assert result["review_gate"]["primary_execution_attempt_blocking_reason_code"] == (
        "runtime_resolution_required"
    )
    assert result["review_gate"]["binding_values_required"] is False
    assert result["review_gate"]["ready_for_execution_attempt"] is False
    assert result["handoff_kind"] == "database_relation_handoff"


def test_describe_context_slice_tool_reports_sensitive_selected_triples(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_CONTEXT_SLICE_DESCRIBE"
    dataset = "https://example.test/project#SensitiveDescribeSlice"
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Sensitive describe slice",
        description=f"Synthetic fixture {fake_secret}.",
        is_table=True,
    )

    result = describe_context_slice_tool(
        db,
        seed_iris=[dataset],
        profile="dataset_brief",
        max_triples=100,
        include_trig=True,
        privacy_scan_limit=5,
    )

    assert result["sensitive_literal_count"] >= 1
    assert result["returned_match_count"] == len(result["matches"])
    assert result["omitted_match_count"] == (
        result["sensitive_literal_count"] - result["returned_match_count"]
    )
    assert result["privacy_scan_limit"] == 5
    assert result["privacy_warnings"]
    assert result["scanner_note"] in result["warnings"]
    assert fake_secret not in json.dumps(result["matches"])
    assert fake_secret not in " ".join(result["privacy_warnings"])
    assert fake_secret not in result["scanner_note"]
    assert fake_secret in json.dumps(result["triples"])
    assert fake_secret in result["trig"]

    privacy_action = result["suggested_next_actions"][0]
    assert privacy_action["tool_name"] == "preflight_context_slice_export"
    assert privacy_action["arguments"] == {
        "seed_iris": [dataset],
        "profile": "dataset_brief",
        "max_triples": 100,
        "include_seed_graphs": True,
        "limit": 5,
    }
    preflight = preflight_context_slice_export_tool(
        db,
        seed_iris=[dataset],
        profile="dataset_brief",
        max_triples=100,
        include_seed_graphs=True,
        limit=5,
    )
    assert preflight["sensitive_literal_count"] >= 1
    assert preflight["decision"] == "block"
    assert preflight["scanner_clean"] is False
    assert preflight["shareability_review_required"] is True
    assert preflight["shareability_review_status"] == "required_not_completed"
    assert preflight["would_block_sensitive_export"] is True
    assert preflight["handoff_fit"] == "resource_scoped_review_context"
    assert all(
        action["tool_name"] != "export_context_slice"
        for action in preflight["suggested_next_actions"]
    )
    assert fake_secret not in json.dumps(preflight["matches"])


def test_context_slice_export_tools_return_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#orders_storage",
        label="Orders storage",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        storage_root="/tmp/shareable/orders.parquet",
        location_kind="object",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Orders",
        is_table=True,
        storage_accesses=[storage["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    preflight = preflight_context_slice_export_tool(
        db,
        seed_iris=[dataset],
        profile="dataset_brief",
        max_triples=100,
    )

    assert preflight["path"] is None
    assert preflight["format"] == "trig"
    assert preflight["decision"] == "clean_by_scanner_only"
    assert preflight["scanner_clean"] is True
    assert preflight["shareability_review_required"] is True
    assert preflight["shareability_review_status"] == "required_not_completed"
    assert preflight["would_block_sensitive_export"] is False
    assert preflight["would_block_invalid_export"] is False
    assert preflight["validation_scope"] == "map"
    assert preflight["validation_conforms"] is True
    assert preflight["validation_result_count"] == 0
    assert preflight["validation_results"] == []
    assert preflight["handoff_fit"] == "resource_scoped_review_context"
    assert preflight["profile"] == "dataset_brief"
    assert preflight["seeds"][0]["iri"] == dataset
    assert preflight["graphs"] == ["map"]
    assert preflight["graph_counts"]["map"] > 0
    assert preflight["include_seed_graphs"] is False
    assert preflight["bytes_written"] == 0
    assert preflight["sensitive_literal_count"] == 0
    assert preflight["matches"] == []
    assert preflight["privacy_warnings"] == []
    assert preflight["artifact_kind"] == "context_slice_trig"
    assert preflight["importable"] is True
    assert preflight["recommended_import_tool"] == "doxabase.import_trig"
    assert preflight["recovery_complete"] is False
    assert preflight["scanner_note"] in preflight["warnings"]
    assert [
        action["tool_name"] for action in preflight["suggested_next_actions"]
    ] == ["export_context_slice"]
    action = preflight["suggested_next_actions"][0]
    assert action["mcp_tool_name"] == "doxabase.export_context_slice"
    assert action["arguments"]["seed_iris"] == [dataset]
    assert action["arguments"]["fail_on_sensitive"] is True
    assert action["arguments"]["fail_on_invalid"] is True
    assert action["arguments"]["validation_scope"] == "map"
    assert preflight["suggested_next_calls"] == [action["call"]]

    export_path = tmp_path / "orders-context-slice.trig"
    export = export_context_slice_tool(
        db,
        path=str(export_path),
        seed_iris=[dataset],
        profile="dataset_brief",
        max_triples=100,
        fail_on_sensitive=True,
    )

    assert export["path"] == str(export_path)
    assert export["decision"] == "clean_by_scanner_only"
    assert export["scanner_clean"] is True
    assert export["shareability_review_required"] is True
    assert export["shareability_review_status"] == "required_not_completed"
    assert export["would_block_sensitive_export"] is False
    assert export["would_block_invalid_export"] is False
    assert export["validation_scope"] == "map"
    assert export["validation_conforms"] is True
    assert export["validation_result_count"] == 0
    assert export["validation_results"] == []
    assert export["handoff_fit"] == "resource_scoped_review_context"
    assert export["bytes_written"] > 0
    assert export["sensitive_literal_count"] == 0
    assert export["artifact_kind"] == "context_slice_trig"
    assert export["importable"] is True
    assert export["recommended_import_tool"] == "doxabase.import_trig"
    assert export["recovery_complete"] is False
    assert export["suggested_next_actions"] == []
    assert export_path.exists()


def test_context_slice_export_can_bypass_unrelated_sensitive_graph_siblings(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_SCOPED_CONTEXT_EXPORT"
    record_map_storage_access_tool(
        db,
        iri="https://example.test/project#unrelated_dirty_storage",
        label="Unrelated dirty storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=f"/tmp/{fake_secret}/unrelated",
    )
    clean_storage = record_map_storage_access_tool(
        db,
        iri="https://example.test/project#orders_storage",
        label="Orders storage",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        storage_root="/tmp/shareable/orders.parquet",
        location_kind="object",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    dataset = "https://example.test/project#Orders"
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Orders",
        is_table=True,
        storage_accesses=[clean_storage["iri"]],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    observation = record_observation_tool(
        db,
        summary="Orders profile reviewed clean storage context.",
        observation_type="profile",
        observed_asset=dataset,
        evidence_summary="Synthetic scoped export regression evidence.",
        evidence_sources=["tests/test_mcp_tools.py"],
        sample_size=12,
        row_count=12,
    )
    record_pattern_tool(
        db,
        summary="Orders clean slice has linked context.",
        pattern_text="The orders handoff can carry map, observation, pattern, and evidence context without unrelated graph siblings.",
        rationale="The linked clean resources target the Orders dataset while the dirty storage node is unlinked.",
        pattern_targets=[dataset],
        supporting_observations=[observation["observation_iri"]],
        source_path="tests/test_mcp_tools.py",
        source_kind="rc:DocumentationSource",
    )

    broad_preflight = export_preflight_tool(
        db,
        export_kind="graph",
        graphs=["map"],
    )

    assert broad_preflight["decision"] == "block"
    assert broad_preflight["scanner_clean"] is False
    assert broad_preflight["would_block_sensitive_export"] is True
    assert broad_preflight["sensitive_literal_count"] >= 1
    assert all(
        action["tool_name"]
        not in {"export_graph", "export_trig", "export_handoff_bundle"}
        for action in broad_preflight["suggested_next_actions"]
    )
    assert [
        action["tool_name"]
        for action in broad_preflight["suggested_next_actions"]
    ] == ["scan_sensitive_literals", "preflight_context_slice_export"]

    blocked_path = tmp_path / "blocked-map.ttl"
    with pytest.raises(DoxaBaseError, match="fail_on_sensitive=True"):
        export_graph_tool(
            db,
            path=str(blocked_path),
            graphs=["map"],
            fail_on_sensitive=True,
        )
    assert not blocked_path.exists()

    scoped_preflight = preflight_context_slice_export_tool(
        db,
        seed_iris=[dataset],
        profile="dataset_brief",
        max_triples=200,
    )

    assert scoped_preflight["decision"] == "clean_by_scanner_only"
    assert scoped_preflight["scanner_clean"] is True
    assert scoped_preflight["shareability_review_required"] is True
    assert scoped_preflight["shareability_review_status"] == (
        "required_not_completed"
    )
    assert scoped_preflight["would_block_sensitive_export"] is False
    assert scoped_preflight["sensitive_literal_count"] == 0
    assert scoped_preflight["matches"] == []
    assert scoped_preflight["handoff_fit"] == "resource_scoped_review_context"
    assert set(scoped_preflight["graphs"]) >= {
        "map",
        "observations",
        "patterns",
        "evidence",
    }
    assert [
        action["tool_name"]
        for action in scoped_preflight["suggested_next_actions"]
    ] == ["export_context_slice"]
    assert fake_secret not in json.dumps(scoped_preflight)

    slice_path = tmp_path / "orders-clean-slice.trig"
    scoped_export = export_context_slice_tool(
        db,
        path=str(slice_path),
        seed_iris=[dataset],
        profile="dataset_brief",
        max_triples=200,
        fail_on_sensitive=True,
    )
    assert scoped_export["scanner_clean"] is True
    assert scoped_export["sensitive_literal_count"] == 0
    assert slice_path.exists()

    receiver = DoxaBase.create(tmp_path / "receiver.sqlite")
    imported = import_trig_tool(receiver, path=str(slice_path))
    assert imported["total_imported"] == scoped_export["triples"]
    assert set(imported["imported"]) >= {
        "map",
        "observations",
        "patterns",
        "evidence",
    }
    assert validate_graph_tool(receiver, scope="all")["conforms"] is True


def test_context_slice_export_tools_redact_sensitive_seed_descriptions(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_CONTEXT_SLICE_TOOL_SEED"
    dataset = "https://example.test/project#SensitiveToolSeed"
    record_map_dataset_tool(
        db,
        iri=dataset,
        label="Sensitive tool seed",
        description=f"Synthetic fixture {fake_secret}.",
        is_table=True,
    )

    preflight = preflight_context_slice_export_tool(
        db,
        seed_iris=[dataset],
        profile="dataset_brief",
        max_triples=100,
        limit=5,
    )

    assert preflight["sensitive_literal_count"] >= 1
    assert preflight["seeds"][0]["description"] == (
        "[REDACTED:fake_secret_marker]"
    )
    assert preflight["matches"][0]["redacted_snippet"] == (
        "[REDACTED:fake_secret_marker]"
    )
    assert fake_secret not in json.dumps(preflight)
    with pytest.raises(DoxaBaseError, match="fail_on_sensitive=True"):
        export_context_slice_tool(
            db,
            path=str(tmp_path / "sensitive-tool-seed-context.trig"),
            seed_iris=[dataset],
            profile="dataset_brief",
            max_triples=100,
            fail_on_sensitive=True,
        )

