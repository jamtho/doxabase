"""Split from test_doxabase_core.py (distillation Phase 2); tests verbatim."""

from tests.core.support_core import *  # noqa: F401,F403


def test_import_trig_maps_graph_iris_to_roles(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    imported = db.import_trig(AIS_FIXTURE)

    assert imported == {
        "evidence": 3,
        "map": 223,
        "observations": 5,
        "ontology": 94,
    }
    assert db.triple_count("map") == 223
    assert db.triple_count("ontology") == 94


def test_import_trig_maps_patterns_graph_role(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    imported = db.import_trig(
        """
        @prefix ex:  <https://example.test/project#> .
        @prefix rc:  <https://richcanopy.org/ns/rc#> .
        @prefix rcg: <https://richcanopy.org/graph/> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        rcg:patterns {
            ex:body_top_pattern a rc:Pattern ;
                rc:summary "body_top behaves like cleaned top-level text." ;
                rc:patternText "Repeated source notes support treating body_top as cleaned message text." ;
                rc:rationale "The README and profile checks describe the same transformation." ;
                rc:patternTarget ex:body_top ;
                rc:evidence ex:body_top_pattern_evidence ;
                rc:synthesizedAt "2026-06-01T00:00:00Z"^^xsd:dateTime .
        }

        rcg:evidence {
            ex:body_top_pattern_evidence a rc:Evidence ;
                rc:summary "README body processing section." ;
                <http://purl.org/dc/terms/source> "tests/test_doxabase_core.py" .
        }
        """
    )

    assert imported["patterns"] > 0
    assert db.validate_graph(scope="all").conforms


def test_import_parse_errors_are_doxabase_errors(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    malformed_turtle = (
        "@prefix ex: <https://example.test/project#> .\n"
        "@prefix rc: <https://richcanopy.org/ns/rc#> .\n"
        "ex:Messages a rc:Dataset\n"
        "ex:Other a rc:Dataset ."
    )

    with pytest.raises(DoxaBaseError) as turtle_exc:
        db.import_turtle(malformed_turtle, graph="map")

    turtle_message = str(turtle_exc.value)
    assert "Could not parse import_turtle source as turtle" in turtle_message
    assert "at line" in turtle_message
    assert db.triple_count("map") == 0

    malformed_trig = """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rcg: <https://richcanopy.org/graph/> .

        rcg:map {
            ex:Messages a rc:Dataset
            ex:Other a rc:Dataset .
        }
    """

    with pytest.raises(DoxaBaseError) as trig_exc:
        db.import_trig(malformed_trig)

    trig_message = str(trig_exc.value)
    assert "Could not parse import_trig source as trig" in trig_message
    assert "at line" in trig_message
    assert db.triple_count("map") == 0


def test_import_trig_rejects_unknown_rich_canopy_graph_roles(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError) as exc_info:
        db.import_trig(
            """
            @prefix ex: <https://example.test/project#> .
            @prefix rc: <https://richcanopy.org/ns/rc#> .
            @prefix rcg: <https://richcanopy.org/graph/> .

            rcg:typo_map {
                ex:Messages a rc:Dataset .
            }
            """
        )

    message = str(exc_info.value)
    assert "Unknown Rich Canopy graph role" in message
    assert "typo_map" in message
    assert "typo_map" not in {
        graph.name for graph in db.graph_overview().named_graphs
    }


def test_import_trig_preflights_all_graphs_before_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    map_graph = Graph(identifier=URIRef("https://richcanopy.org/graph/map"))
    map_graph.add(
        (
            URIRef("https://example.test/project#Messages"),
            RDF.type,
            URIRef(f"{RC}Dataset"),
        )
    )
    seed_graph = Graph(identifier=URIRef("https://richcanopy.org/graph/base_ontology"))
    seed_graph.add(
        (
            URIRef("https://example.test/project#SeedTerm"),
            RDF.type,
            URIRef(f"{RC}Dataset"),
        )
    )

    class OrderedDataset:
        def graphs(self) -> list[Graph]:
            return [map_graph, seed_graph]

    monkeypatch.setattr(
        db,
        "_parse_rdf_dataset",
        lambda *args, **kwargs: OrderedDataset(),
    )
    before_counts = _mutable_graph_counts(db)

    with pytest.raises(ImmutableGraphError, match="base_ontology"):
        db.import_trig("ignored.trig")

    assert _mutable_graph_counts(db) == before_counts
    assert db.triple_count("map") == 0


def test_export_graph_writes_flattened_turtle(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    export_path = tmp_path / "map.ttl"

    result = db.export_graph(export_path, graphs="map")

    assert result.path == str(export_path)
    assert result.format == "turtle"
    assert result.graphs == ["map"]
    assert result.graph_counts == {"map": db.triple_count("map")}
    assert result.triples == db.triple_count("map")
    assert result.bytes_written == export_path.stat().st_size

    graph = Graph()
    graph.parse(export_path, format="turtle")
    assert len(graph) == db.triple_count("map")
    assert (
        URIRef("https://richcanopy.org/example/manifest/ais#DailyBroadcasts"),
        RDF.type,
        URIRef(RC + "Table"),
    ) in graph

    with pytest.raises(DoxaBaseError, match="already exists"):
        db.export_graph(export_path, graphs="map")


def test_sensitive_literal_scan_and_export_warnings(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    fake_secret = "FAKE_SECRET_DO_NOT_USE_123"
    private_key_body = "MII_FAKE_PRIVATE_BODY_SHOULD_NOT_LEAK"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_storage",
        description=(
            "Scratch credential paste: -----BEGIN PRIVATE KEY-----\n"
            f"{private_key_body}\n"
            "-----END PRIVATE KEY-----"
        ),
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        storage_root=f"/tmp/{fake_secret}/orders",
        credential_reference=f"Bearer {fake_secret}",
        datasets=[dataset],
    )
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        storage_accesses=[storage.iri],
    )

    scan = db.scan_sensitive_literals(graphs="map", limit=1)

    assert scan.match_count >= 2
    assert scan.sensitive_literal_count == scan.match_count
    assert scan.returned_match_count == 1
    assert scan.omitted_match_count >= 1
    assert scan.matches[0].graph == "map"
    assert scan.matches[0].match_kind in {
        "bearer_token",
        "fake_secret_marker",
        "private_key_header",
    }
    assert fake_secret not in scan.matches[0].redacted_snippet
    assert scan.warnings
    full_scan = db.scan_sensitive_literals(graphs="map", limit=20)
    assert private_key_body not in str(full_scan.matches)
    assert all(match.redacted_snippet.startswith("[REDACTED:") for match in full_scan.matches)
    with pytest.raises(DoxaBaseError, match="limit must be at least 1"):
        db.scan_sensitive_literals(graphs="map", limit=0)

    export_path = tmp_path / "map.ttl"
    export = db.export_graph(export_path, graphs="map")

    assert export.sensitive_literal_count == scan.match_count
    assert export.privacy_warnings
    assert fake_secret not in " ".join(export.privacy_warnings)
    assert private_key_body not in " ".join(export.privacy_warnings)
    assert fake_secret in export_path.read_text(encoding="utf-8")

    blocked_path = tmp_path / "blocked-map.ttl"
    with pytest.raises(DoxaBaseError) as excinfo:
        db.export_graph(blocked_path, graphs="map", fail_on_sensitive=True)
    blocked_message = str(excinfo.value)
    assert "fail_on_sensitive=True" in blocked_message
    assert fake_secret not in blocked_message
    assert private_key_body not in blocked_message
    assert not blocked_path.exists()

    existing_path = tmp_path / "existing-map.ttl"
    existing_path.write_text("keep me\n", encoding="utf-8")
    with pytest.raises(DoxaBaseError):
        db.export_graph(
            existing_path,
            graphs="map",
            overwrite=True,
            fail_on_sensitive=True,
        )
    assert existing_path.read_text(encoding="utf-8") == "keep me\n"

    blocked_trig_path = tmp_path / "blocked-project.trig"
    with pytest.raises(DoxaBaseError):
        db.export_trig(
            blocked_trig_path,
            graphs="project",
            fail_on_sensitive=True,
        )
    assert not blocked_trig_path.exists()


def test_privacy_exports_block_sensitive_subject_iris(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_SUBJECT_IRI"
    subject_iri = f"https://example.test/project#{fake_secret}"
    db.import_turtle(
        f"""
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        <{subject_iri}> a rc:Dataset ;
            rdfs:label "Subject-only privacy probe" .
        """,
        graph="map",
    )
    revision = db.record_graph_revision(
        summary="Record subject privacy probe",
        rationale="Capture a map snapshot whose sensitive-looking term is only a subject IRI.",
        changed_graphs=["map"],
        included_graphs=["map"],
    )

    scan = db.scan_sensitive_literals(graphs="map", limit=10)

    assert scan.match_count >= 1
    assert any(match.term_position == "subject" for match in scan.matches)
    assert any(match.term_kind == "uri" for match in scan.matches)
    assert fake_secret not in str(scan.matches)

    export_path = tmp_path / "subject-map.ttl"
    export = db.export_graph(export_path, graphs="map")
    assert export.sensitive_literal_count == scan.match_count
    assert fake_secret not in " ".join(export.privacy_warnings)
    assert fake_secret in export_path.read_text(encoding="utf-8")

    blocked_graph_path = tmp_path / "blocked-subject-map.ttl"
    with pytest.raises(DoxaBaseError) as graph_excinfo:
        db.export_graph(blocked_graph_path, graphs="map", fail_on_sensitive=True)
    assert "fail_on_sensitive=True" in str(graph_excinfo.value)
    assert fake_secret not in str(graph_excinfo.value)
    assert not blocked_graph_path.exists()

    snapshot_path = tmp_path / "subject-revision-snapshots.json"
    snapshot_export = db.export_revision_snapshots(
        snapshot_path,
        revision_iris=[revision.revision_iri],
    )
    assert snapshot_export.sensitive_literal_count >= 1
    assert fake_secret not in " ".join(snapshot_export.privacy_warnings)
    assert fake_secret in snapshot_path.read_text(encoding="utf-8")

    blocked_snapshot_path = tmp_path / "blocked-subject-revision-snapshots.json"
    with pytest.raises(DoxaBaseError) as snapshot_excinfo:
        db.export_revision_snapshots(
            blocked_snapshot_path,
            revision_iris=[revision.revision_iri],
            fail_on_sensitive=True,
        )
    assert "fail_on_sensitive=True" in str(snapshot_excinfo.value)
    assert fake_secret not in str(snapshot_excinfo.value)
    assert not blocked_snapshot_path.exists()

    blocked_trig_path = tmp_path / "blocked-subject-project.trig"
    blocked_handoff_snapshot_path = (
        tmp_path / "blocked-subject-handoff-revision-snapshots.json"
    )
    with pytest.raises(DoxaBaseError) as handoff_excinfo:
        db.export_handoff_bundle(
            blocked_trig_path,
            blocked_handoff_snapshot_path,
            revision_iris=[revision.revision_iri],
            fail_on_sensitive=True,
        )
    assert "fail_on_sensitive=True" in str(handoff_excinfo.value)
    assert fake_secret not in str(handoff_excinfo.value)
    assert not blocked_trig_path.exists()
    assert not blocked_handoff_snapshot_path.exists()


def test_privacy_exports_block_sensitive_predicate_iris(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_PREDICATE_IRI"
    predicate_iri = f"https://example.test/project#{fake_secret}"
    db.import_turtle(
        f"""
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .

        ex:Orders a rc:Dataset ;
            <{predicate_iri}> "predicate-only privacy probe" .
        """,
        graph="map",
    )
    revision = db.record_graph_revision(
        summary="Record predicate privacy probe",
        rationale=(
            "Capture a map snapshot whose sensitive-looking term is only a "
            "predicate IRI."
        ),
        changed_graphs=["map"],
        included_graphs=["map"],
    )

    scan = db.scan_sensitive_literals(graphs="map", limit=10)

    assert scan.match_count >= 1
    assert any(match.term_position == "predicate" for match in scan.matches)
    assert any(match.term_kind == "uri" for match in scan.matches)
    assert fake_secret not in str(scan.matches)

    export_path = tmp_path / "predicate-map.ttl"
    export = db.export_graph(export_path, graphs="map")
    assert export.sensitive_literal_count == scan.match_count
    assert fake_secret not in " ".join(export.privacy_warnings)
    assert fake_secret in export_path.read_text(encoding="utf-8")

    blocked_graph_path = tmp_path / "blocked-predicate-map.ttl"
    with pytest.raises(DoxaBaseError) as graph_excinfo:
        db.export_graph(blocked_graph_path, graphs="map", fail_on_sensitive=True)
    assert "fail_on_sensitive=True" in str(graph_excinfo.value)
    assert fake_secret not in str(graph_excinfo.value)
    assert not blocked_graph_path.exists()

    snapshot_path = tmp_path / "predicate-revision-snapshots.json"
    snapshot_export = db.export_revision_snapshots(
        snapshot_path,
        revision_iris=[revision.revision_iri],
    )
    assert snapshot_export.sensitive_literal_count >= 1
    assert fake_secret not in " ".join(snapshot_export.privacy_warnings)
    assert fake_secret in snapshot_path.read_text(encoding="utf-8")

    blocked_snapshot_path = tmp_path / "blocked-predicate-revision-snapshots.json"
    with pytest.raises(DoxaBaseError) as snapshot_excinfo:
        db.export_revision_snapshots(
            blocked_snapshot_path,
            revision_iris=[revision.revision_iri],
            fail_on_sensitive=True,
        )
    assert "fail_on_sensitive=True" in str(snapshot_excinfo.value)
    assert fake_secret not in str(snapshot_excinfo.value)
    assert not blocked_snapshot_path.exists()

    blocked_trig_path = tmp_path / "blocked-predicate-project.trig"
    blocked_handoff_snapshot_path = (
        tmp_path / "blocked-predicate-handoff-revision-snapshots.json"
    )
    with pytest.raises(DoxaBaseError) as handoff_excinfo:
        db.export_handoff_bundle(
            blocked_trig_path,
            blocked_handoff_snapshot_path,
            revision_iris=[revision.revision_iri],
            fail_on_sensitive=True,
        )
    assert "fail_on_sensitive=True" in str(handoff_excinfo.value)
    assert fake_secret not in str(handoff_excinfo.value)
    assert not blocked_trig_path.exists()
    assert not blocked_handoff_snapshot_path.exists()


def test_export_revision_snapshots_reports_sensitive_literals(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_SNAPSHOT"
    db.record_map_storage_access(
        "https://example.test/project#orders_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=f"/tmp/{fake_secret}/orders",
    )
    staged = db.stage_graph_revision(
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
    export = db.export_revision_snapshots(
        snapshot_path,
        revision_iris=[staged.revision_iri],
    )

    assert export.sensitive_literal_count >= 1
    assert export.privacy_warnings
    assert fake_secret not in " ".join(export.privacy_warnings)
    assert fake_secret in snapshot_path.read_text(encoding="utf-8")

    blocked_path = tmp_path / "blocked-revision-snapshots.json"
    with pytest.raises(DoxaBaseError) as excinfo:
        db.export_revision_snapshots(
            blocked_path,
            revision_iris=[staged.revision_iri],
            fail_on_sensitive=True,
        )
    assert "fail_on_sensitive=True" in str(excinfo.value)
    assert fake_secret not in str(excinfo.value)
    assert not blocked_path.exists()

    existing_path = tmp_path / "existing-revision-snapshots.json"
    existing_path.write_text("keep me\n", encoding="utf-8")
    with pytest.raises(DoxaBaseError):
        db.export_revision_snapshots(
            existing_path,
            revision_iris=[staged.revision_iri],
            overwrite=True,
            fail_on_sensitive=True,
        )
    assert existing_path.read_text(encoding="utf-8") == "keep me\n"


def test_export_handoff_bundle_blocks_sensitive_literals_before_writing(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_HANDOFF"
    db.record_map_storage_access(
        "https://example.test/project#orders_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=f"/tmp/{fake_secret}/orders",
    )
    staged = db.stage_graph_revision(
        summary="Stage handoff probe",
        rationale="Create a revision snapshot over the sensitive map graph.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:OrdersHandoffProbe a rc:Dataset .
                """,
            }
        ],
    )

    trig_path = tmp_path / "blocked-project.trig"
    snapshot_path = tmp_path / "blocked-revision-snapshots.json"
    with pytest.raises(DoxaBaseError) as excinfo:
        db.export_handoff_bundle(
            trig_path,
            snapshot_path,
            revision_iris=[staged.revision_iri],
            fail_on_sensitive=True,
        )

    message = str(excinfo.value)
    assert "fail_on_sensitive=True" in message
    assert fake_secret not in message
    assert not trig_path.exists()
    assert not snapshot_path.exists()

    existing_snapshot_path = tmp_path / "existing-revision-snapshots.json"
    existing_snapshot_path.write_text("keep me\n", encoding="utf-8")
    with pytest.raises(DoxaBaseError):
        db.export_handoff_bundle(
            tmp_path / "project.trig",
            existing_snapshot_path,
            revision_iris=[staged.revision_iri],
        )
    assert not (tmp_path / "project.trig").exists()
    assert existing_snapshot_path.read_text(encoding="utf-8") == "keep me\n"

    existing_manifest_path = tmp_path / "existing-handoff-manifest.json"
    existing_manifest_path.write_text("keep me\n", encoding="utf-8")
    with pytest.raises(DoxaBaseError):
        db.export_handoff_bundle(
            tmp_path / "manifest-project.trig",
            tmp_path / "manifest-revision-snapshots.json",
            manifest_path=existing_manifest_path,
            revision_iris=[staged.revision_iri],
        )
    assert not (tmp_path / "manifest-project.trig").exists()
    assert not (tmp_path / "manifest-revision-snapshots.json").exists()
    assert existing_manifest_path.read_text(encoding="utf-8") == "keep me\n"


def test_import_handoff_bundle_blocks_mutation_when_resolved_target_lacks_snapshots(
    tmp_path: Path,
) -> None:
    source = DoxaBase.create(tmp_path / "source.sqlite")
    staged = source.stage_graph_revision(
        summary="Stage orders handoff source",
        rationale="Create a stale source whose current successor needs snapshots.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:OrdersHandoffSource a rc:Dataset .
                """,
            }
        ],
    )
    source.record_map_dataset(
        "https://example.test/project#UnrelatedDrift",
        label="Unrelated drift",
        is_table=True,
    )
    restaged = source.restage_staged_revision(staged.revision_iri)
    trig_path = tmp_path / "narrow-project-handoff.trig"
    snapshot_path = tmp_path / "narrow-revision-snapshots.json"
    manifest_path = tmp_path / "narrow-handoff-manifest.json"
    exported = source.export_handoff_bundle(
        trig_path,
        snapshot_path,
        manifest_path=manifest_path,
        revision_iris=[staged.revision_iri],
        fail_on_sensitive=True,
    )

    assert exported.revision_iris == [staged.revision_iri]

    receiver = DoxaBase.create(tmp_path / "receiver.sqlite")
    imported = receiver.import_handoff_bundle(manifest_path)

    assert imported.post_import_snapshot_evidence[0].revision_iri == (
        staged.revision_iri
    )
    assert imported.post_import_snapshot_evidence[0].status == (
        "history_plus_snapshot_rows"
    )
    assert imported.recovery_plan is not None
    plan = imported.recovery_plan
    assert plan.mutation_allowed_after == (
        "handoff_preflight_required_before_mutation"
    )
    assert plan.lane_counts == {"complete_handoff_import": 1}
    assert plan.next_action_queue == {
        "complete_handoff_import": [restaged.revision_iri]
    }
    assert plan.mutation_frontier_iris == []
    assert plan.blocking_preflight_actions
    assert plan.blocking_preflight_actions[0].tool_name == (
        "import_revision_snapshots"
    )
    assert imported.suggested_next_actions[0] == plan.blocking_preflight_actions[0]
    first_action = imported.suggested_next_actions[0]
    assert first_action.action_label == "Import broader source snapshot bundle"
    assert first_action.arguments == {
        "path": "<broader-source-revision-snapshots.json>",
        "path_is_placeholder": True,
        "missing_revision_iris": [restaged.revision_iri],
        "already_imported_snapshot_path": str(snapshot_path),
        "handoff_manifest_path": str(manifest_path),
        "missing_graph_roles": ["map"],
    }
    assert "Re-importing the current manifest" in first_action.reason
    assert restaged.revision_iri in first_action.reason
    summary = imported.recovery_summary
    assert summary.recommended_next_step == (
        "complete_handoff_preflight_before_recovery_mutation"
    )
    assert summary.snapshot_evidence_complete is False
    assert summary.snapshot_evidence_status_counts == {
        "history_only_count_digest": 1,
        "history_plus_snapshot_rows": 1,
    }
    assert summary.incomplete_snapshot_revision_iris == [restaged.revision_iri]
    assert summary.mutation_frontier_iris == []
    assert summary.first_mutation_frontier_item is None
    assert summary.first_mutation_action is None
    assert (
        summary.first_safe_review_or_mutation_action
        == plan.blocking_preflight_actions[0]
    )
    assert summary.first_safe_review_or_mutation_source == (
        "recovery_plan_blocking_preflight"
    )
    assert summary.first_suggested_next_action == plan.blocking_preflight_actions[0]
    assert "resolved recovery targets" in summary.note


def test_export_preflight_blocks_sensitive_handoff_scope(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_PREFLIGHT"
    db.record_map_storage_access(
        "https://example.test/project#orders_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=f"/tmp/{fake_secret}/orders",
    )
    staged = db.stage_graph_revision(
        summary="Stage preflight probe",
        rationale="Create a revision snapshot over the sensitive map graph.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:OrdersPreflightProbe a rc:Dataset .
                """,
            }
        ],
    )

    preflight = db.export_preflight(
        export_kind="handoff_bundle",
        revision_iris=[staged.revision_iri],
        limit=1,
    )

    assert preflight.decision == "block"
    assert preflight.scanner_clean is False
    assert preflight.shareability_review_required is True
    assert preflight.shareability_review_status == "required_not_completed"
    assert preflight.would_block_sensitive_export is True
    assert preflight.graphs == [
        "ontology",
        "map",
        "observations",
        "patterns",
        "evidence",
        "shapes",
        "history",
    ]
    assert preflight.revision_iris == [staged.revision_iri]
    assert preflight.snapshot_graph_roles == ["map"]
    assert preflight.sensitive_literal_count >= 2
    assert preflight.graph_sensitive_literal_count >= 1
    assert preflight.snapshot_sensitive_literal_count >= 1
    assert preflight.returned_match_count == 1
    assert preflight.omitted_match_count == (
        preflight.sensitive_literal_count - preflight.returned_match_count
    )
    assert preflight.matches[0].match_id.startswith("redacted-sha256:")
    assert preflight.privacy_warnings
    assert preflight.scanner_note not in preflight.warnings
    assert not any("Scanner-clean means" in warning for warning in preflight.warnings)
    assert [
        action.tool_name for action in preflight.suggested_next_actions
    ] == [
        "scan_sensitive_literals",
        "export_preflight",
        "preflight_context_slice_export",
    ]
    snapshot_action = preflight.suggested_next_actions[1]
    assert snapshot_action.arguments == {
        "export_kind": "revision_snapshots",
        "revision_iris": [staged.revision_iri],
        "snapshot_graph_roles": ["map"],
        "limit": 20,
    }
    snapshot_followup = db.export_preflight(**snapshot_action.arguments)
    assert snapshot_followup.graph_sensitive_literal_count == 0
    assert snapshot_followup.snapshot_sensitive_literal_count >= 1
    assert snapshot_followup.matches
    assert {match.export_part for match in snapshot_followup.matches} == {
        "revision_snapshots"
    }
    slice_action = preflight.suggested_next_actions[-1]
    assert slice_action.arguments == {
        "seed_iris": ["<target-resource-iri>"],
        "profile": "dataset_brief",
        "max_triples": 500,
        "limit": 20,
    }
    assert slice_action.required_extra_arguments == ["seed_iris"]
    assert slice_action.placeholder_fields == ["seed_iris"]
    assert slice_action.reviewed_value_fields == ["seed_iris"]
    assert "review context" in slice_action.reason
    assert "not recovery-complete" in slice_action.reason
    assert fake_secret not in json.dumps(to_dict(preflight))


def test_export_preflight_returns_scanner_clean_export_action(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.record_map_dataset(
        "https://example.test/project#Orders",
        label="Orders",
        is_table=True,
    )

    preflight = db.export_preflight(export_kind="trig", graphs="workflow")

    assert preflight.decision == "clean_by_scanner_only"
    assert preflight.scanner_clean is True
    assert preflight.shareability_review_required is True
    assert preflight.shareability_review_status == "required_not_completed"
    assert preflight.would_block_sensitive_export is False
    assert preflight.sensitive_literal_count == 0
    assert preflight.matches == []
    assert preflight.privacy_warnings == []
    assert len(preflight.warnings) == 2
    assert "review context only" in preflight.warnings[0]
    assert "export_handoff_bundle" in preflight.warnings[0]
    assert preflight.warnings[1] == preflight.scanner_note
    assert [action.tool_name for action in preflight.suggested_next_actions] == [
        "export_trig"
    ]
    action = preflight.suggested_next_actions[0]
    assert action.arguments["graphs"] == [
        "map",
        "observations",
        "patterns",
        "evidence",
    ]
    assert action.arguments["fail_on_sensitive"] is True
    assert not (tmp_path / "<project-review-bundle.trig>").exists()

    workflow_export = db.export_trig(tmp_path / "workflow.trig", graphs="workflow")
    assert "review context only" in workflow_export.warnings[0]
    assert workflow_export.artifact_kind == "workflow_review_trig"
    assert workflow_export.importable is True
    assert workflow_export.recommended_import_tool == "doxabase.import_trig"
    assert workflow_export.recovery_complete is False

    project_preflight = db.export_preflight(export_kind="trig", graphs="project")
    assert project_preflight.warnings == [project_preflight.scanner_note]
    handoff_preflight = db.export_preflight(export_kind="handoff_bundle")
    assert handoff_preflight.warnings == [handoff_preflight.scanner_note]
    handoff_action = handoff_preflight.suggested_next_actions[0]
    assert handoff_action.tool_name == "export_handoff_bundle"
    assert handoff_action.required_extra_arguments == [
        "trig_path",
        "revision_snapshot_path",
        "manifest_path",
    ]
    assert handoff_action.placeholder_fields == [
        "trig_path",
        "revision_snapshot_path",
        "manifest_path",
    ]
    assert handoff_action.reviewed_value_fields == [
        "trig_path",
        "revision_snapshot_path",
        "manifest_path",
    ]
    assert handoff_action.arguments["manifest_path"] == "<handoff-manifest.json>"


def test_export_trig_preserves_graph_roles_for_round_trip(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    export_path = tmp_path / "bundle.trig"

    result = db.export_trig(export_path)

    assert result.format == "trig"
    assert result.graphs == [
        "ontology",
        "map",
        "observations",
        "patterns",
        "evidence",
        "shapes",
        "history",
    ]
    assert result.graph_counts == {
        graph: db.triple_count(graph) for graph in result.graphs
    }
    assert result.triples == sum(db.triple_count(graph) for graph in result.graphs)
    assert result.warnings == []

    dataset = Dataset()
    dataset.parse(export_path, format="trig")
    identifiers = {str(context.identifier) for context in dataset.graphs() if len(context)}
    assert "https://richcanopy.org/graph/base_ontology" not in identifiers
    assert "https://richcanopy.org/graph/map" in identifiers
    assert "https://richcanopy.org/graph/observations" in identifiers

    round_trip = DoxaBase.create(tmp_path / "round-trip.sqlite")
    imported = round_trip.import_trig(export_path)
    assert imported["map"] == db.triple_count("map")
    assert imported["observations"] == db.triple_count("observations")
    assert imported["evidence"] == db.triple_count("evidence")
    assert imported["ontology"] == db.triple_count("ontology")


def test_export_trig_all_with_seeds_requires_explicit_seed_import(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(AIS_FIXTURE)
    export_path = tmp_path / "all-with-seeds.trig"

    result = db.export_trig(export_path, graphs="all_with_seeds")

    assert result.graphs[:2] == ["base_ontology", "base_shapes"]
    assert result.graph_counts["base_ontology"] == db.triple_count("base_ontology")
    assert result.graph_counts["base_shapes"] == db.triple_count("base_shapes")

    round_trip = DoxaBase.create(tmp_path / "round-trip-with-seeds.sqlite")
    before_counts = _mutable_graph_counts(round_trip)
    with pytest.raises(ImmutableGraphError, match="base_(ontology|shapes)"):
        round_trip.import_trig(export_path)
    assert _mutable_graph_counts(round_trip) == before_counts


def test_context_slice_export_is_importable_and_resource_scoped(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    shareable = "https://example.test/project#ShareableOrders"
    shareable_storage = db.record_map_storage_access(
        "https://example.test/project#shareable_orders_storage",
        label="Shareable orders storage",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        storage_root="/tmp/shareable/orders.parquet",
        location_kind="object",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        shareable,
        label="Shareable orders",
        is_table=True,
        storage_accesses=[shareable_storage.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_column(
        "https://example.test/project#ShareableOrders__order_id",
        table_iri=shareable,
        column_name="order_id",
        physical_type="rc:Varchar",
    )
    fake_secret = "FAKE_SECRET_DO_NOT_USE_CONTEXT_SLICE_EXPORT"
    sensitive = "https://example.test/project#SensitivePayroll"
    sensitive_storage = db.record_map_storage_access(
        "https://example.test/project#sensitive_payroll_storage",
        label="Sensitive payroll storage",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        storage_root=f"/tmp/{fake_secret}/payroll.csv",
        location_kind="object",
    )
    db.record_map_dataset(
        sensitive,
        label="Sensitive payroll",
        is_table=True,
        storage_accesses=[sensitive_storage.iri],
    )

    map_preflight = db.export_preflight(
        export_kind="trig",
        graphs=["map"],
        limit=5,
    )
    assert map_preflight.sensitive_literal_count > 0

    preflight = db.preflight_context_slice_export(
        [shareable],
        profile="dataset_brief",
        max_triples=200,
        limit=5,
    )

    assert preflight.path is None
    assert preflight.decision == "clean_by_scanner_only"
    assert preflight.scanner_clean is True
    assert preflight.shareability_review_required is True
    assert preflight.shareability_review_status == "required_not_completed"
    assert preflight.would_block_sensitive_export is False
    assert preflight.handoff_fit == "resource_scoped_review_context"
    assert preflight.graphs == ["map"]
    assert preflight.graph_counts["map"] > 0
    assert preflight.sensitive_literal_count == 0
    assert preflight.matches == []
    assert preflight.include_seed_graphs is False
    assert any(
        "Immutable seed graph triples were omitted" in warning
        for warning in preflight.warnings
    )
    assert preflight.suggested_next_actions[0].tool_name == "export_context_slice"
    assert preflight.suggested_next_actions[0].arguments["fail_on_sensitive"] is True
    assert fake_secret not in json.dumps(to_dict(preflight))

    dirty_preflight = db.preflight_context_slice_export(
        [sensitive],
        profile="dataset_brief",
        max_triples=200,
        limit=5,
    )

    assert dirty_preflight.path is None
    assert dirty_preflight.decision == "block"
    assert dirty_preflight.scanner_clean is False
    assert dirty_preflight.would_block_sensitive_export is True
    assert dirty_preflight.sensitive_literal_count > 0
    assert [
        action.tool_name for action in dirty_preflight.suggested_next_actions
    ] == [
        "describe_context_slice",
        "export_preflight",
    ]
    assert dirty_preflight.suggested_next_actions[0].arguments == {
        "seed_iris": [sensitive],
        "profile": "dataset_brief",
        "max_triples": 200,
        "privacy_scan_limit": 5,
    }
    assert dirty_preflight.suggested_next_actions[1].arguments == {
        "export_kind": "handoff_bundle",
        "graphs": ["project"],
        "limit": 5,
    }
    assert all(
        action.tool_name != "export_context_slice"
        for action in dirty_preflight.suggested_next_actions
    )
    assert dirty_preflight.suggested_next_calls == [
        action.call for action in dirty_preflight.suggested_next_actions
    ]
    assert fake_secret not in json.dumps(to_dict(dirty_preflight))

    export_path = tmp_path / "shareable-context-slice.trig"
    export = db.export_context_slice(
        export_path,
        [shareable],
        profile="dataset_brief",
        max_triples=200,
        fail_on_sensitive=True,
    )
    export_text = export_path.read_text(encoding="utf-8")

    assert export.path == str(export_path)
    assert export.decision == "clean_by_scanner_only"
    assert export.scanner_clean is True
    assert export.shareability_review_required is True
    assert export.shareability_review_status == "required_not_completed"
    assert export.would_block_sensitive_export is False
    assert export.handoff_fit == "resource_scoped_review_context"
    assert export.bytes_written > 0
    assert export.sensitive_literal_count == 0
    assert export.suggested_next_actions == []
    assert "ShareableOrders" in export_text
    assert "SensitivePayroll" not in export_text
    assert fake_secret not in export_text

    dataset = Dataset()
    dataset.parse(export_path, format="trig")
    graph_iris = {
        str(context.identifier) for context in dataset.graphs() if len(context)
    }
    assert graph_iris == {"https://richcanopy.org/graph/map"}

    round_trip = DoxaBase.create(tmp_path / "round-trip-context.sqlite")
    imported = round_trip.import_trig(export_path)
    assert imported == {"map": export.triples}
    assert round_trip.search("Shareable orders", graph="map").matches
    assert round_trip.search("Sensitive payroll", graph="map").matches == []


def test_query_failure_evidence_slice_exports_when_broad_handoff_blocks_sensitive_unrelated_graph_content(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/query-failure-privacy#"
    dataset = f"{base}CleanOrders"
    fake_secret = "FAKE_SECRET_DO_NOT_USE_QUERY_FAILURE_PRIVACY"

    storage = db.record_map_storage_access(
        f"{base}clean_orders_storage",
        label="Clean orders database connection",
        storage_protocol="rc:DatabaseStorage",
        location_kind="connection",
        storage_root="warehouse-prod",
        path_templates=["mart.clean_orders"],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    layout = db.record_map_physical_layout(
        f"{base}clean_orders_layout",
        file_format="rc:PostgreSQLTable",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_dataset(
        dataset,
        label="Clean orders",
        is_table=True,
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.import_turtle(
        f"""
        @prefix ex: <{base}> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:UnrelatedSensitiveNote
            rdfs:comment "Synthetic unrelated marker {fake_secret}." .
        """,
        graph="map",
    )

    result = db.record_query_result(
        summary=(
            "Clean Orders status query was blocked by the external runtime "
            "before execution."
        ),
        observed_asset=dataset,
        execution_status="blocked",
        engine="external-postgres-client",
        query_source_path=str(tmp_path / "clean_orders_status.sql"),
        result_sources=[str(tmp_path / "blocked-query.log")],
        scanned_source_paths=["warehouse-prod:mart.clean_orders"],
        failure_summary="External runtime refused credentials before scanning.",
    )

    broad_preflight = db.export_preflight(
        export_kind="handoff_bundle",
        graphs=["project"],
        limit=20,
    )
    assert broad_preflight.decision == "block"
    assert broad_preflight.would_block_sensitive_export is True
    assert broad_preflight.sensitive_literal_count > 0
    assert fake_secret not in json.dumps(to_dict(broad_preflight))

    slice_preflight = db.preflight_context_slice_export(
        [result.evidence_iri],
        profile="resource_brief",
        max_triples=200,
        limit=20,
    )
    assert slice_preflight.decision == "clean_by_scanner_only"
    assert slice_preflight.scanner_clean is True
    assert slice_preflight.sensitive_literal_count == 0
    assert slice_preflight.would_block_sensitive_export is False
    assert slice_preflight.suggested_next_actions[0].tool_name == (
        "export_context_slice"
    )

    slice_path = tmp_path / "query-failure-evidence-slice.trig"
    export = db.export_context_slice(
        slice_path,
        [result.evidence_iri],
        profile="resource_brief",
        max_triples=200,
        fail_on_sensitive=True,
    )
    export_text = slice_path.read_text(encoding="utf-8")

    assert export.decision == "clean_by_scanner_only"
    assert export.sensitive_literal_count == 0
    assert result.evidence_iri in export_text
    assert "queryExecutionStatus" in export_text
    assert "blocked" in export_text
    assert fake_secret not in export_text

    blocked_trig_path = tmp_path / "blocked-project.trig"
    blocked_snapshot_path = tmp_path / "blocked-revision-snapshots.json"
    blocked_manifest_path = tmp_path / "blocked-handoff-manifest.json"
    with pytest.raises(DoxaBaseError) as excinfo:
        db.export_handoff_bundle(
            blocked_trig_path,
            blocked_snapshot_path,
            manifest_path=blocked_manifest_path,
            graphs=["project"],
            fail_on_sensitive=True,
        )
    assert "fail_on_sensitive=True" in str(excinfo.value)
    assert fake_secret not in str(excinfo.value)
    assert not blocked_trig_path.exists()
    assert not blocked_snapshot_path.exists()
    assert not blocked_manifest_path.exists()


def test_context_slice_export_preserves_relationship_endpoint_bodies(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/asset-context#"
    raw_images = f"{base}RawImages"
    ocr_documents = f"{base}OcrDocuments"
    review_packet = f"{base}ReviewPacket"
    relationship_iri = f"{base}ReviewPacketDerivation"

    db.record_map_dataset(
        raw_images,
        label="Raw images",
        is_table=False,
        extra_types=["rc:ImageFile"],
    )
    db.record_map_dataset(
        ocr_documents,
        label="OCR documents",
        is_table=False,
        extra_types=["rc:PDFFile"],
    )
    db.record_map_dataset(
        review_packet,
        label="Review packet",
        is_table=False,
        extra_types=["rc:DocumentCollection"],
    )
    db.record_map_relationship(
        relationship_iri,
        label="Review packet derivation",
        relationship_type="derivation",
        source_endpoints=[
            {
                "iri": f"{base}ReviewPacketDerivationRawImagesEndpoint",
                "dataset": raw_images,
                "role": "primary image input",
                "order": 10,
            },
            {
                "iri": f"{base}ReviewPacketDerivationOcrEndpoint",
                "dataset": ocr_documents,
                "role": "report text input",
                "order": 20,
            },
        ],
        target_endpoints=[
            {
                "iri": f"{base}ReviewPacketDerivationTargetEndpoint",
                "dataset": review_packet,
                "role": "human review packet output",
                "order": 1,
            }
        ],
    )
    assert db.validate_graph(scope="all").conforms

    context_slice = db.describe_context_slice(
        [review_packet],
        profile="dataset_brief",
        max_triples=300,
    )
    assert context_slice.route_counts["relationship_endpoint"] == 3
    assert context_slice.route_counts["relationship_endpoint_dataset"] == 3

    export_path = tmp_path / "review-packet-context.trig"
    export = db.export_context_slice(
        export_path,
        [review_packet],
        profile="dataset_brief",
        max_triples=300,
        fail_on_sensitive=True,
    )
    assert export.graph_counts == {"map": export.triples}
    assert export.triples == export.candidate_triple_count

    export_text = export_path.read_text(encoding="utf-8")
    assert "hasRelationshipEndpoint" in export_text
    assert "endpointDataset" in export_text
    assert "endpointDirection" in export_text
    assert "endpointRole" in export_text
    assert "endpointOrder" in export_text

    round_trip = DoxaBase.create(tmp_path / "round-trip-context.sqlite")
    imported = round_trip.import_trig(export_path)
    assert imported == {"map": export.triples}
    validation = round_trip.validate_graph(scope="all")
    assert validation.conforms, validation.report_text

    described = round_trip.describe_dataset(review_packet)
    derivation = next(
        item
        for item in described.relationships
        if item.iri == relationship_iri
    )
    assert [
        (
            endpoint.dataset.iri if endpoint.dataset else None,
            endpoint.role,
            endpoint.order,
            endpoint.direction,
        )
        for endpoint in derivation.source_endpoints
    ] == [
        (raw_images, "primary image input", 10, "source"),
        (ocr_documents, "report text input", 20, "source"),
    ]
    assert [
        (
            endpoint.dataset.iri if endpoint.dataset else None,
            endpoint.role,
            endpoint.order,
            endpoint.direction,
        )
        for endpoint in derivation.target_endpoints
    ] == [
        (review_packet, "human review packet output", 1, "target"),
    ]


def test_context_slice_export_redacts_sensitive_seed_descriptions(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_CONTEXT_SLICE_SEED"
    dataset = "https://example.test/project#SensitiveSeedSummary"
    db.record_map_dataset(
        dataset,
        label="Sensitive seed summary",
        description=f"Synthetic fixture {fake_secret}.",
        is_table=True,
    )

    preflight = db.preflight_context_slice_export(
        [dataset],
        profile="dataset_brief",
        max_triples=100,
        limit=5,
    )

    assert preflight.sensitive_literal_count >= 1
    assert preflight.decision == "block"
    assert preflight.scanner_clean is False
    assert preflight.shareability_review_required is True
    assert preflight.shareability_review_status == "required_not_completed"
    assert preflight.would_block_sensitive_export is True
    assert preflight.handoff_fit == "resource_scoped_review_context"
    assert preflight.seeds[0].description == (
        "[REDACTED:fake_secret_marker]"
    )
    assert preflight.matches[0].redacted_snippet == (
        "[REDACTED:fake_secret_marker]"
    )
    assert all(
        action.tool_name != "export_context_slice"
        for action in preflight.suggested_next_actions
    )
    assert fake_secret not in json.dumps(to_dict(preflight))
    with pytest.raises(DoxaBaseError, match="fail_on_sensitive=True"):
        db.export_context_slice(
            tmp_path / "sensitive-seed-context.trig",
            [dataset],
            profile="dataset_brief",
            max_triples=100,
            fail_on_sensitive=True,
        )


def test_context_slice_export_scans_history_validation_closure(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    fake_secret = "FAKE_SECRET_DO_NOT_USE_HISTORY_CLOSURE"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    staged = db.stage_graph_revision(
        summary="Stage Orders private comment",
        rationale="Exercise context-slice preflight scanning of selected patch payloads.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    <{dataset}> rdfs:comment "Synthetic marker {fake_secret}." .
                """,
            }
        ],
        revision_anchors=[dataset],
        included_graphs=["map"],
    )

    preflight = db.preflight_context_slice_export(
        staged.revision_iri,
        profile="deep_lore",
        max_triples=400,
        limit=5,
    )

    assert preflight.decision == "block"
    assert preflight.would_block_sensitive_export is True
    assert preflight.sensitive_literal_count >= 1
    assert any("patchContent" in match.predicate for match in preflight.matches)
    assert fake_secret not in json.dumps(to_dict(preflight))
    with pytest.raises(DoxaBaseError, match="fail_on_sensitive=True"):
        db.export_context_slice(
            tmp_path / "blocked-history-context.trig",
            staged.revision_iri,
            profile="deep_lore",
            max_triples=400,
            fail_on_sensitive=True,
        )


def test_shareability_hints_flag_scanner_clean_local_home_paths(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    local_path = "/Users/example/private/orders.csv"
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_storage",
        label="Orders local storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=local_path,
    )
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(
        dataset,
        label="Orders",
        is_table=True,
        storage_accesses=[storage.iri],
    )

    preflight = db.export_preflight(export_kind="graph", graphs=["map"])

    assert preflight.decision == "clean_by_scanner_only"
    assert preflight.scanner_clean is True
    assert preflight.would_block_sensitive_export is False
    assert preflight.sensitive_literal_count == 0
    assert preflight.privacy_warnings == []
    assert preflight.shareability_hints == ["absolute_local_home_path"]
    assert preflight.shareability_hint_count == 1
    assert preflight.returned_shareability_hint_count == 1
    assert preflight.omitted_shareability_hint_count == 0
    assert len(preflight.shareability_hint_matches) == 1
    preflight_hint = preflight.shareability_hint_matches[0]
    assert preflight_hint.match_id.startswith("shareability-sha256:")
    assert preflight_hint.export_part == "graphs"
    assert preflight_hint.hint_code == "absolute_local_home_path"
    assert preflight_hint.graph == "map"
    assert preflight_hint.subject == storage.iri
    assert preflight_hint.predicate == RC + "storageRoot"
    assert preflight_hint.term_position == "object"
    assert preflight_hint.term_kind == "literal"
    assert local_path not in json.dumps(to_jsonable(preflight_hint))
    assert preflight.artifact_disposition == (
        "local_only_pending_shareability_review"
    )
    assert preflight.git_safe is False
    assert any(
        "absolute local home/private path" in warning
        for warning in preflight.warnings
    )

    graph_export = db.export_graph(
        tmp_path / "orders-map.ttl",
        graphs=["map"],
        fail_on_sensitive=True,
    )
    assert graph_export.sensitive_literal_count == 0
    assert graph_export.shareability_hints == ["absolute_local_home_path"]
    assert graph_export.shareability_hint_matches[0].predicate == (
        RC + "storageRoot"
    )
    assert graph_export.artifact_disposition == (
        "local_only_pending_shareability_review"
    )
    assert graph_export.git_safe is False

    context = db.describe_context_slice(dataset, profile="resource_brief")
    assert context.sensitive_literal_count == 0
    assert context.shareability_hints == ["absolute_local_home_path"]
    assert context.shareability_hint_matches[0].export_part == "context_slice"
    assert context.shareability_hint_matches[0].subject == storage.iri
    assert any(
        "absolute local home/private path" in warning
        for warning in context.warnings
    )

    context_preflight = db.preflight_context_slice_export(
        dataset,
        profile="resource_brief",
    )
    assert context_preflight.scanner_clean is True
    assert context_preflight.shareability_hints == ["absolute_local_home_path"]
    assert context_preflight.shareability_hint_matches[0].export_part == (
        "context_slice_export"
    )
    assert context_preflight.git_safe is False

    context_export = db.export_context_slice(
        tmp_path / "orders-context.trig",
        dataset,
        profile="resource_brief",
        fail_on_sensitive=True,
    )
    assert context_export.scanner_clean is True
    assert context_export.shareability_hints == ["absolute_local_home_path"]
    assert context_export.shareability_hint_matches[0].export_part == (
        "context_slice_export"
    )
    assert context_export.artifact_disposition == (
        "local_only_pending_shareability_review"
    )

    handoff = db.export_handoff_bundle(
        tmp_path / "project-handoff.trig",
        tmp_path / "revision-snapshots.json",
        manifest_path=tmp_path / "handoff-manifest.json",
        fail_on_sensitive=True,
    )
    assert handoff.scanner_clean is True
    assert handoff.shareability_hints == ["absolute_local_home_path"]
    assert handoff.git_safe is False
    assert handoff.trig.shareability_hints == ["absolute_local_home_path"]
    assert handoff.shareability_hint_matches[0].predicate == RC + "storageRoot"
    assert handoff.manifest["shareability_hint_matches"][0]["predicate"] == (
        RC + "storageRoot"
    )
    assert handoff.revision_snapshots.shareability_hints == []
    assert handoff.manifest["shareability_hints"] == ["absolute_local_home_path"]
    assert handoff.manifest["artifact_disposition"] == (
        "local_only_pending_shareability_review"
    )
    assert handoff.manifest["git_safe"] is False
    assert handoff.manifest["artifacts"]["trig"]["shareability_hints"] == [
        "absolute_local_home_path"
    ]
    assert handoff.manifest["artifacts"]["trig"]["shareability_hint_matches"][0][
        "subject"
    ] == storage.iri

    staged = db.stage_graph_revision(
        summary="Add local path caveat",
        rationale="Review scanner-clean local path shareability hints.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders rc:hasCaveat [
                        a rc:KnownCaveat ;
                        rc:caveatDescription "Reviewed local path {local_path}." ;
                    ] .
                """,
            }
        ],
    )
    snapshot_preflight = db.export_preflight(
        export_kind="revision_snapshots",
        revision_iris=[staged.revision_iri],
    )
    assert snapshot_preflight.shareability_hints == ["absolute_local_home_path"]
    snapshot_hint = snapshot_preflight.shareability_hint_matches[0]
    assert snapshot_hint.export_part == "revision_snapshots"
    assert snapshot_hint.revision_iri == staged.revision_iri
    assert snapshot_hint.graph == "map"
    assert snapshot_hint.term_position == "object"
    assert local_path not in json.dumps(to_jsonable(snapshot_hint))

    single_path = tmp_path / "single-review.md"
    single_export = db.export_staged_revision(
        staged.revision_iri,
        single_path,
        fail_on_sensitive=True,
    )
    assert single_export.scanner_clean is True
    assert single_export.would_block_sensitive_export is False
    assert single_export.sensitive_literal_count == 0
    assert single_export.shareability_hints == ["absolute_local_home_path"]
    assert single_export.git_safe is False
    single_line = _line_number_containing(
        single_path.read_text(encoding="utf-8"),
        local_path,
    )
    assert single_export.shareability_hint_matches[0].export_part == (
        "staged_revision_markdown"
    )
    assert single_export.shareability_hint_matches[0].line_number == single_line
    assert local_path not in json.dumps(
        to_jsonable(single_export.shareability_hint_matches)
    )

    grouped_path = tmp_path / "grouped-review.md"
    grouped_export = db.export_staged_revisions(
        [staged.revision_iri],
        grouped_path,
        fail_on_sensitive=True,
    )
    assert grouped_export.scanner_clean is True
    assert grouped_export.shareability_hints == ["absolute_local_home_path"]
    grouped_line = _line_number_containing(
        grouped_path.read_text(encoding="utf-8"),
        local_path,
    )
    assert grouped_export.shareability_hint_matches[0].export_part == (
        "staged_revisions_markdown"
    )
    assert grouped_export.shareability_hint_matches[0].line_number == grouped_line
    assert grouped_export.artifact_disposition == (
        "local_only_pending_shareability_review"
    )


def test_grouped_export_marks_partial_snapshot_evidence(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = db.stage_graph_revision(
        summary="Stage map and ontology together",
        rationale="Exercise partial exact snapshot rows in grouped review.",
        additions=[
            {
                "graph": "ontology",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:ReviewTerm a rdfs:Class ;
                        rdfs:label "Review term" .
                """,
            },
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:ReviewDataset a rc:Dataset .
                """,
            },
        ],
    )
    project_path = tmp_path / "project.trig"
    map_only_snapshot_path = tmp_path / "map-only-snapshots.json"
    db.export_trig(project_path, graphs="project")
    db.export_revision_snapshots(
        map_only_snapshot_path,
        revision_iris=[staged.revision_iri],
        graph_roles=["map"],
    )
    partial = DoxaBase.create(tmp_path / "partial.sqlite")
    partial.import_trig(project_path)
    partial.import_revision_snapshots(map_only_snapshot_path)

    status = partial.describe_revision_snapshot_evidence(staged.revision_iri)
    assert status.status == "history_plus_snapshot_rows"
    assert status.exact_snapshot_graph_roles == ["map"]
    assert status.missing_snapshot_row_graph_roles == ["ontology"]
    grouped_export_path = tmp_path / "partial-multigraph-review.md"
    export = partial.export_staged_revisions(
        [staged.revision_iri],
        grouped_export_path,
    )
    grouped_export_text = grouped_export_path.read_text(encoding="utf-8")

    snapshot_summary = export.bundle_summary.snapshot_evidence
    assert snapshot_summary.complete is False
    assert snapshot_summary.total_revision_count == 1
    assert snapshot_summary.incomplete_revision_iris == [staged.revision_iri]
    assert snapshot_summary.status_counts == {"history_plus_snapshot_rows": 1}
    assert len(snapshot_summary.rows) == 1
    snapshot_row = snapshot_summary.rows[0]
    assert snapshot_row.row_index == 1
    assert snapshot_row.revision_iri == staged.revision_iri
    assert snapshot_row.status == "history_plus_snapshot_rows"
    assert snapshot_row.completeness == "partial"
    assert snapshot_row.rdf_snapshot_graph_roles == ["map", "ontology"]
    assert snapshot_row.stored_snapshot_graph_roles == ["map"]
    assert snapshot_row.exact_snapshot_graph_roles == ["map"]
    assert snapshot_row.missing_snapshot_row_graph_roles == ["ontology"]
    assert snapshot_row.suggested_next_actions[0].tool_name == (
        "import_revision_snapshots"
    )
    assert "## Snapshot Evidence" in grouped_export_text
    assert "history_plus_snapshot_rows: 1" in grouped_export_text
    assert "| 1 |" in grouped_export_text
    assert "history_plus_snapshot_rows | partial | map, ontology | map | map | ontology" in (
        grouped_export_text
    )
    assert "import_revision_snapshots" in grouped_export_text

    full_snapshot_path = tmp_path / "full-plus-extra-snapshots.json"
    db.export_revision_snapshots(
        full_snapshot_path,
        revision_iris=[staged.revision_iri],
    )
    full_snapshot_bundle = json.loads(full_snapshot_path.read_text(encoding="utf-8"))
    extra_snapshot = {
        "revision_iri": staged.revision_iri,
        "graph_role": "evidence",
        "stored_at": "2026-06-25T00:00:00+00:00",
        "triple_count": 0,
        "content_digest": "sha256:empty-extra-evidence",
        "quads": [],
    }
    full_snapshot_bundle["snapshots"].append(extra_snapshot)
    full_plus_extra = DoxaBase.create(tmp_path / "full-plus-extra.sqlite")
    full_plus_extra.import_trig(project_path)
    full_plus_extra.import_revision_snapshots(json.dumps(full_snapshot_bundle))

    extra_status = full_plus_extra.describe_revision_snapshot_evidence(
        staged.revision_iri
    )
    assert extra_status.missing_snapshot_row_graph_roles == []
    assert extra_status.orphan_snapshot_row_graph_roles == ["evidence"]
    extra_grouped_export_path = tmp_path / "partial-extra-snapshot-review.md"
    full_plus_extra.export_staged_revisions(
        [staged.revision_iri],
        extra_grouped_export_path,
    )
    extra_grouped_export_text = extra_grouped_export_path.read_text(
        encoding="utf-8"
    )

    assert "history_plus_snapshot_rows | partial-extra-rows" in (
        extra_grouped_export_text
    )
    assert "| evidence |" in extra_grouped_export_text


def test_stale_project_import_suggests_snapshot_json_before_restaging(
    tmp_path: Path,
) -> None:
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
    db.record_map_dataset(
        "https://example.test/project#DriftDataset",
        label="Drift Dataset",
        is_table=True,
    )

    project_path = tmp_path / "project.trig"
    db.export_trig(project_path, graphs="project")
    round_trip = DoxaBase.create(tmp_path / "round-trip.sqlite")
    round_trip.import_trig(project_path)

    check = round_trip.check_staged_revision_apply(staged.revision_iri)

    assert check.status == "conflict"
    assert check.blocking_reasons == ["target_count_drift"]
    assert check.snapshot_drifts
    assert check.snapshot_drifts[0].exact_changed_triples_available is False
    assert [action.tool_name for action in check.suggested_next_actions] == [
        "import_revision_snapshots",
        "describe_staged_revision",
        "export_staged_revision",
        "restage_staged_revision",
    ]
    assert check.suggested_next_actions[0].action_label == (
        "Import snapshot bundle if available"
    )
    assert check.suggested_next_actions[0].arguments == {
        "path": "/tmp/revision-snapshots.json",
        "path_is_placeholder": True,
    }


def test_import_revision_snapshots_validates_bundle_before_writing(
    tmp_path: Path,
) -> None:
    valid_db = DoxaBase.create(tmp_path / "valid.sqlite")
    valid_revision = "https://example.test/revision#valid"
    invalid_revision = "https://example.test/revision#invalid"
    valid_snapshot = {
        "revision_iri": valid_revision,
        "graph_role": "map",
        "stored_at": "2026-06-25T00:00:00+00:00",
        "triple_count": 1,
        "content_digest": "sha256:valid",
        "quads": [
            {
                "subject": "https://example.test/project#Thing",
                "subject_kind": "uri",
                "predicate": "https://example.test/project#note",
                "object": "",
                "object_kind": "literal",
                "datatype": str(XSD.string),
                "lang": None,
            }
        ],
    }

    imported = valid_db.import_revision_snapshots(
        json.dumps(
            {
                "format": "doxabase.revision_snapshot_bundle.v1",
                "snapshots": [valid_snapshot],
            }
        )
    )
    assert imported.imported_snapshot_count == 1
    assert len(imported.post_import_snapshot_evidence) == 1
    assert imported.post_import_snapshot_evidence[0].revision_iri == valid_revision
    assert imported.post_import_snapshot_evidence[0].status == (
        "snapshot_rows_without_history"
    )
    assert [
        action.tool_name
        for action in imported.post_import_snapshot_evidence[0].suggested_next_actions
    ] == ["import_trig"]
    assert valid_db._graph_snapshot_storage_rows(valid_revision, "map")[0][3] == ""
    snapshot_only = valid_db.describe_revision_graph_snapshot(
        valid_revision,
        "map",
        include_triples=True,
    )
    assert snapshot_only.snapshot_evidence.status == "snapshot_rows_without_history"
    assert snapshot_only.triple_count == 1
    assert snapshot_only.content_digest == "sha256:valid"
    assert snapshot_only.count_basis == "stored_snapshot_rows"
    assert snapshot_only.exact_snapshot_available is True
    assert snapshot_only.triples_included is True
    assert snapshot_only.triples_truncated is False
    assert len(snapshot_only.triples) == 1
    assert snapshot_only.triples[0].object == ""
    assert snapshot_only.triples[0].object_kind == "literal"
    with pytest.raises(DoxaBaseError) as lineage_excinfo:
        valid_db.describe_resource_revision_lineage(
            "https://example.test/project#Thing",
            valid_revision,
        )
    lineage_message = str(lineage_excinfo.value)
    assert "was not found in resource lineage" in lineage_message
    assert "Snapshot rows exist for this revision IRI" in lineage_message
    assert "Import the project/history RDF bundle" in lineage_message

    invalid_kind_db = DoxaBase.create(tmp_path / "invalid-kind.sqlite")
    with pytest.raises(DoxaBaseError, match="object_kind must be one of"):
        invalid_kind_db.import_revision_snapshots(
            json.dumps(
                {
                    "format": "doxabase.revision_snapshot_bundle.v1",
                    "snapshots": [
                        valid_snapshot,
                        {
                            "revision_iri": invalid_revision,
                            "graph_role": "map",
                            "stored_at": "2026-06-25T00:00:00+00:00",
                            "triple_count": 1,
                            "content_digest": "sha256:invalid",
                            "quads": [
                                {
                                    "subject": "https://example.test/project#Thing",
                                    "subject_kind": "uri",
                                    "predicate": "https://example.test/project#note",
                                    "object": "not a storage kind",
                                    "object_kind": "resource",
                                    "datatype": None,
                                    "lang": None,
                                }
                            ],
                        },
                    ],
                }
            )
        )

    assert not invalid_kind_db._graph_snapshot_storage_exists(valid_revision, "map")

    empty_uri_db = DoxaBase.create(tmp_path / "empty-uri.sqlite")
    with pytest.raises(DoxaBaseError, match="object must be non-empty"):
        empty_uri_db.import_revision_snapshots(
            json.dumps(
                {
                    "format": "doxabase.revision_snapshot_bundle.v1",
                    "snapshots": [
                        valid_snapshot,
                        {
                            "revision_iri": invalid_revision,
                            "graph_role": "map",
                            "stored_at": "2026-06-25T00:00:00+00:00",
                            "triple_count": 1,
                            "content_digest": "sha256:invalid",
                            "quads": [
                                {
                                    "subject": "https://example.test/project#Thing",
                                    "subject_kind": "uri",
                                    "predicate": "https://example.test/project#link",
                                    "object": "",
                                    "object_kind": "uri",
                                    "datatype": None,
                                    "lang": None,
                                }
                            ],
                        },
                    ],
                }
            )
        )

    assert not empty_uri_db._graph_snapshot_storage_exists(valid_revision, "map")

    empty_bnode_db = DoxaBase.create(tmp_path / "empty-bnode.sqlite")
    with pytest.raises(DoxaBaseError, match="object must be non-empty"):
        empty_bnode_db.import_revision_snapshots(
            json.dumps(
                {
                    "format": "doxabase.revision_snapshot_bundle.v1",
                    "snapshots": [
                        valid_snapshot,
                        {
                            "revision_iri": invalid_revision,
                            "graph_role": "map",
                            "stored_at": "2026-06-25T00:00:00+00:00",
                            "triple_count": 1,
                            "content_digest": "sha256:invalid",
                            "quads": [
                                {
                                    "subject": "https://example.test/project#Thing",
                                    "subject_kind": "uri",
                                    "predicate": "https://example.test/project#link",
                                    "object": "",
                                    "object_kind": "bnode",
                                    "datatype": None,
                                    "lang": None,
                                }
                            ],
                        },
                    ],
                }
            )
        )

    assert not empty_bnode_db._graph_snapshot_storage_exists(valid_revision, "map")


def test_import_revision_snapshots_wraps_malformed_json(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    malformed_path = tmp_path / "bad-snapshots.json"
    malformed_path.write_text(
        '{"format": "doxabase.revision_snapshot_bundle.v1", "snapshots": [',
        encoding="utf-8",
    )

    with pytest.raises(
        DoxaBaseError,
        match=(
            "Could not parse revision snapshot bundle JSON from <string>: "
            "Expecting value at line 1 column"
        ),
    ):
        db.import_revision_snapshots(
            '{"format": "doxabase.revision_snapshot_bundle.v1", "snapshots": ['
        )

    with pytest.raises(DoxaBaseError) as excinfo:
        db.import_revision_snapshots(malformed_path)

    message = str(excinfo.value)
    assert "Could not parse revision snapshot bundle JSON from" in message
    assert str(malformed_path) in message
    assert "Expecting value at line 1 column" in message


def test_local_csv_query_handoff_can_record_result_artifact(
    tmp_path: Path,
) -> None:
    csv_path = tmp_path / "orders.csv"
    csv_path.write_text(
        "order_id,status,amount_cents\n"
        "1,paid,1200\n"
        "2,pending,800\n"
        "3,paid,3100\n"
        "4,refunded,700\n",
        encoding="utf-8",
    )
    query_path = tmp_path / "orders_status_aggregate.sql"
    query_path.write_text(
        "select status, count(*) as row_count, "
        "sum(amount_cents) as amount_cents from orders group by status;\n",
        encoding="utf-8",
    )
    result_path = tmp_path / "orders_status_aggregate.result.json"
    result_path.write_text(
        json.dumps(
            {
                "row_count": 4,
                "status_counts": {
                    "paid": 2,
                    "pending": 1,
                    "refunded": 1,
                },
                "paid_amount_cents": 4300,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    columns = [
        db.record_map_column(
            f"https://example.test/project#orders__{name}",
            table_iri=dataset,
            column_name=name,
        )
        for name in ("order_id", "status", "amount_cents")
    ]
    storage = db.record_map_storage_access(
        "https://example.test/project#orders_csv_storage",
        label="Orders CSV storage",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        location_kind="object",
        storage_root=str(csv_path),
        layout_verification_status="rc:VerifiedByQueryLayout",
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
        row_count_snapshot=4,
        columns=[column.iri for column in columns],
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)
    plan = db.draft_query_plan(dataset)

    assert context.readiness == "ready_for_query_planning"
    assert context.issues == []
    assert plan.handoff_kind == "execution_attempt_ready"
    assert plan.scan.function == "read_csv_auto"
    assert plan.scan.uri_template == str(csv_path)
    assert plan.scan.execution_attempt_ready is True
    assert plan.review_gate.ready_for_execution_attempt is True

    result = db.record_query_result(
        summary=(
            "Orders CSV status aggregate ran with a Python CSV fallback after "
            "the draft query handoff."
        ),
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path=str(query_path),
        result_sources=[str(result_path)],
        sample_size=4,
        sample_scope="All rows in the reviewed local Orders CSV.",
        sample_method="External read-only aggregate after draft_query_plan.",
        row_count=4,
    )

    assert result.observation_type == "profile"
    assert result.execution_status == "succeeded"
    assert result.engine == "python-csv"
    assert result.result_sources == [str(result_path)]
    assert result.source_span_iri is not None
    observation = db.describe_resource(result.observation_iri, graph="observations")
    assert (
        RC + "rowCount",
        "4",
    ) in {(triple.predicate, triple.object) for triple in observation.outgoing}
    assert db.validate_graph(scope="all").conforms
    matches = db.search("Python CSV fallback", graph="observations")
    assert result.observation_iri in {match.iri for match in matches.matches}


def test_local_csv_directory_wildcard_handoff_records_generic_result(
    tmp_path: Path,
) -> None:
    warehouse = tmp_path / "warehouse"
    first_partition = warehouse / "orders" / "event_date=2026-06-29"
    second_partition = warehouse / "orders" / "event_date=2026-06-30"
    first_partition.mkdir(parents=True)
    second_partition.mkdir(parents=True)
    first_csv = first_partition / "orders.csv"
    second_csv = second_partition / "orders.csv"
    first_csv.write_text(
        "order_id,event_date,status,amount_cents\n"
        "1,2026-06-29,paid,1200\n"
        "2,2026-06-29,refunded,-300\n",
        encoding="utf-8",
    )
    second_csv.write_text(
        "order_id,event_date,status,amount_cents\n"
        "3,2026-06-30,paid,3100\n"
        "4,2026-06-30,pending,800\n",
        encoding="utf-8",
    )
    query_path = tmp_path / "paid_orders_by_day.sql"
    query_path.write_text(
        "select event_date, count(*) as paid_orders "
        "from orders where status = 'paid' group by event_date;\n",
        encoding="utf-8",
    )

    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/project#"
    dataset = f"{base}PartitionedOrders"
    columns = [
        db.record_map_column(
            f"{base}partitioned_orders__{name}",
            table_iri=dataset,
            column_name=name,
        )
        for name in ("order_id", "event_date", "status", "amount_cents")
    ]
    storage = db.record_map_storage_access(
        f"{base}partitioned_orders_storage",
        label="Partitioned orders storage",
        storage_protocol="rc:LocalFilesystemStorage",
        access_mode="rc:ReadOnlyAccess",
        location_kind="directory",
        storage_root=str(warehouse),
        path_templates=["orders/event_date=*/orders.csv"],
        layout_verification_status="rc:VerifiedByListingLayout",
    )
    layout = db.record_map_physical_layout(
        f"{base}partitioned_orders_csv_layout",
        file_format="rc:CSV",
        layout_verification_status="rc:VerifiedByQueryLayout",
    )
    db.record_map_caveat(
        f"{base}partitioned_orders_refund_caveat",
        label="Refund caveat",
        description=(
            "Refunded rows carry negative amount_cents; paid-revenue aggregates "
            "must filter deliberately."
        ),
        severity="rc:Moderate",
        targets=[dataset],
    )
    db.record_map_dataset(
        dataset,
        label="Partitioned orders",
        is_table=True,
        columns=[column.iri for column in columns],
        storage_accesses=[storage.iri],
        physical_layouts=[layout.iri],
        layout_verification_status="rc:VerifiedByQueryLayout",
    )

    context = db.describe_query_context(dataset)
    plan = db.draft_query_plan(dataset)

    assert context.readiness == "ready_for_query_planning"
    assert context.issues == []
    assert [warning.code for warning in context.analysis_warnings] == [
        "direct_analysis_caveat"
    ]
    assert plan.handoff_kind == "execution_attempt_ready"
    assert plan.scan.function == "read_csv_auto"
    assert plan.scan.uri_template == str(warehouse / "orders/event_date=*/orders.csv")
    assert plan.scan.execution_attempt_ready is True
    assert plan.review_gate.ready_for_execution_attempt is True

    paid_by_date: dict[str, int] = {}
    scanned_paths = sorted(
        str(path)
        for path in warehouse.glob("orders/event_date=*/orders.csv")
    )
    for path in scanned_paths:
        with Path(path).open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row["status"] == "paid":
                    paid_by_date[row["event_date"]] = (
                        paid_by_date.get(row["event_date"], 0) + 1
                    )
    result_path = tmp_path / "paid_orders_by_day.result.json"
    result_path.write_text(
        json.dumps(paid_by_date, sort_keys=True),
        encoding="utf-8",
    )

    result = db.record_query_result(
        summary=(
            "Partitioned Orders paid-count aggregate ran with a Python CSV "
            "fallback after the wildcard draft query handoff."
        ),
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path=str(query_path),
        result_sources=[str(result_path)],
        scanned_source_paths=scanned_paths,
    )

    assert result.observation_type == "observation"
    assert result.execution_status == "succeeded"
    assert result.scanned_source_paths == scanned_paths
    assert [action.tool_name for action in result.suggested_next_actions] == [
        "describe_context_slice",
        "describe_query_context",
    ]
    assert result.suggested_next_actions[0].arguments == {
        "seed_iris": [result.evidence_iri],
        "profile": "resource_brief",
    }

    result_slice = db.describe_context_slice(
        result.observation_iri,
        profile="deep_lore",
        max_triples=200,
    )
    assert result_slice.route_counts["seed_observation"] == 1
    assert result_slice.route_counts["observed_asset"] == 1
    assert result_slice.route_counts["evidence"] == 1
    assert result_slice.sensitive_literal_count == 0
    preflight = db.preflight_context_slice_export(
        result.observation_iri,
        profile="deep_lore",
        max_triples=200,
    )
    assert preflight.decision == "clean_by_scanner_only"
    assert preflight.shareability_review_required is True
    assert db.validate_graph(scope="all").conforms


def test_history_snapshot_only_handoff_routes_to_import_before_mutation(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "source.sqlite")
    dataset = "https://example.test/project#Messages"
    db.record_map_dataset(dataset, label="Messages", is_table=True)
    staged = db.stage_graph_revision(
        summary="Add message freshness caveat",
        rationale="Exercise history plus snapshots without current map import.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    <{dataset}> rc:hasCaveat <https://example.test/project#FreshnessCaveat> .
                """,
            }
        ],
        revision_anchors=[dataset],
        validation_scope="all",
    )

    history_path = tmp_path / "history-only.trig"
    snapshot_path = tmp_path / "revision-snapshots.json"
    db.export_trig(history_path, graphs="history")
    db.export_revision_snapshots(snapshot_path, revision_iris=[staged.revision_iri])

    snapshot_first = DoxaBase.create(tmp_path / "snapshot-first.sqlite")
    snapshot_first.import_revision_snapshots(snapshot_path)
    snapshot_only_evidence = snapshot_first.describe_revision_snapshot_evidence(
        staged.revision_iri
    )
    assert snapshot_only_evidence.status == "snapshot_rows_without_history"
    assert [action.tool_name for action in snapshot_only_evidence.suggested_next_actions] == [
        "import_trig"
    ]
    snapshot_first_plan = snapshot_first.plan_staged_revision_recovery(
        [staged.revision_iri],
        current_staged_work_only=False,
    )
    assert snapshot_first_plan.lane_counts == {"complete_handoff_import": 1}
    assert snapshot_first_plan.next_action_queue == {
        "complete_handoff_import": [staged.revision_iri]
    }
    assert snapshot_first_plan.not_restageable_revision_iris_by_reason == {
        "missing_history_graph": [staged.revision_iri]
    }
    assert snapshot_first_plan.suggested_next_actions[0].tool_name == "import_trig"
    assert snapshot_first_plan.mutation_allowed_after == (
        "handoff_preflight_required_before_mutation"
    )
    assert [
        action.tool_name
        for action in snapshot_first_plan.blocking_preflight_actions
    ] == ["import_trig"]
    assert snapshot_first_plan.first_mutation_action is None
    assert snapshot_first_plan.first_mutation_call is None
    assert (
        snapshot_first_plan.first_safe_review_or_mutation_action
        == snapshot_first_plan.blocking_preflight_actions[0]
    )
    assert (
        snapshot_first_plan.first_safe_review_or_mutation_call
        == snapshot_first_plan.blocking_preflight_actions[0].call
    )
    assert (
        snapshot_first_plan.first_safe_review_or_mutation_source
        == "blocking_preflight"
    )
    snapshot_first_lane = snapshot_first_plan.lanes[0]
    assert snapshot_first_lane.lane == "complete_handoff_import"
    assert snapshot_first_lane.batch_action == "skipped_snapshot_rows_without_history"
    assert snapshot_first_lane.not_restageable_reason == "missing_history_graph"
    assert snapshot_first_lane.source_snapshot_evidence.status == (
        "snapshot_rows_without_history"
    )
    assert snapshot_first_lane.next_action is not None
    assert snapshot_first_lane.next_action.tool_name == "import_trig"

    partial = DoxaBase.create(tmp_path / "history-snapshots-only.sqlite")
    partial.import_trig(history_path)
    partial.import_revision_snapshots(snapshot_path)

    assert partial.triple_count("map") == 0
    snapshot_evidence = partial.describe_revision_snapshot_evidence(
        staged.revision_iri
    )
    assert snapshot_evidence.status == "history_plus_snapshot_rows"
    assert snapshot_evidence.exact_snapshot_graph_roles == ["map"]
    assert snapshot_evidence.missing_current_graph_roles == ["map"]
    assert [action.tool_name for action in snapshot_evidence.suggested_next_actions] == [
        "import_trig"
    ]
    assert "complete project RDF bundle" in (
        snapshot_evidence.suggested_next_actions[0].reason
    )

    listing = partial.list_graph_revisions(
        revision_type="rc:StagedRevision",
        include_apply_checks=True,
    )
    assert listing.next_action_queue == {
        "complete_handoff_import": [staged.revision_iri]
    }
    assert listing.revisions[0].next_action is not None
    assert listing.revisions[0].next_action.queue == "complete_handoff_import"
    assert listing.revisions[0].next_action.tool_name == "import_trig"

    plan = partial.plan_staged_revision_recovery([staged.revision_iri])
    assert plan.lane_counts == {"complete_handoff_import": 1}
    assert plan.next_action_queue == {
        "complete_handoff_import": [staged.revision_iri]
    }
    assert plan.lanes[0].next_action is not None
    assert plan.lanes[0].next_action.tool_name == "import_trig"
    assert plan.mutation_allowed_after == (
        "handoff_preflight_required_before_mutation"
    )
    assert [action.tool_name for action in plan.blocking_preflight_actions] == [
        "import_trig"
    ]


def test_handoff_import_gates_nested_plan_when_source_session_matches(
    tmp_path: Path,
) -> None:
    source = DoxaBase.create(tmp_path / "source.sqlite")
    staged = source.stage_graph_revision(
        summary="Add Orders dataset",
        rationale="Stage a mechanically ready row for receiver handoff.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Orders a rc:Dataset .
                """,
            }
        ],
    )
    source_plan = source.plan_staged_revision_recovery(
        [staged.revision_iri],
        current_staged_work_only=False,
    )
    assert source_plan.first_mutation_action is not None
    assert source_plan.first_mutation_action.tool_name == "apply_staged_revision"

    manifest_path = tmp_path / "ready-handoff-manifest.json"
    trig_path = tmp_path / "ready-handoff.trig"
    snapshot_path = tmp_path / "ready-revision-snapshots.json"
    session = source.start_staged_revision_recovery_session(
        [staged.revision_iri],
        summary="Ready staged handoff recovery session",
        handoff_manifest_path=str(manifest_path),
        current_staged_work_only=False,
    )
    source.export_handoff_bundle(
        trig_path,
        snapshot_path,
        manifest_path=manifest_path,
        revision_iris=[staged.revision_iri],
    )

    receiver = DoxaBase.create(tmp_path / "receiver.sqlite")
    imported = receiver.import_handoff_bundle(manifest_path)

    assert imported.matching_recovery_session_iris == [session.session_iri]
    assert imported.recovery_summary.recommended_next_step == (
        "continue_imported_recovery_session"
    )
    assert imported.recovery_summary.first_mutation_action is None
    assert imported.recovery_summary.first_safe_review_or_mutation_action is not None
    assert imported.recovery_summary.first_safe_review_or_mutation_action.tool_name == (
        "describe_staged_revision_recovery_session"
    )
    assert imported.recovery_plan is not None
    assert imported.recovery_plan.mutation_frontier_iris == [staged.revision_iri]
    assert imported.recovery_plan.first_mutation_action is None
    assert imported.recovery_plan.first_mutation_call is None
    assert imported.recovery_plan.first_safe_review_or_mutation_action is not None
    assert imported.recovery_plan.first_safe_review_or_mutation_action.tool_name == (
        "describe_staged_revision_recovery_session"
    )
    assert imported.recovery_plan.first_safe_review_or_mutation_action.arguments == {
        "session_iri": session.session_iri,
        "drift_detail": "summary",
    }
    assert imported.recovery_plan.first_safe_review_or_mutation_source == (
        "imported_recovery_session"
    )
    assert imported.recovery_plan.mutation_allowed_after == (
        "imported_recovery_session_required_before_mutation"
    )
    assert [
        action.tool_name for action in imported.recovery_plan.blocking_preflight_actions
    ] == ["describe_staged_revision_recovery_session"]
    assert imported.recovery_plan.recommended_unattended_steps
    first_step = imported.recovery_plan.recommended_unattended_steps[0]
    assert first_step.step_kind == "continue_imported_recovery_session"
    assert first_step.mutates is False
    assert first_step.requires_replan_after_completion is True
    assert first_step.action is not None
    assert first_step.action.tool_name == "describe_staged_revision_recovery_session"
    assert "Continue the imported source recovery session" in (
        imported.recovery_plan.warnings[0]
    )
    assert "Continue the imported source recovery session" in (
        imported.recovery_plan.note
    )


def test_export_preflight_and_writes_gate_invalid_graphs(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_trig(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rcg: <https://richcanopy.org/graph/> .

        rcg:observations {
            ex:obs_without_evidence a rc:Observation ;
                rc:summary "This observation should block unattended export." .
        }
        """
    )

    preflight = db.export_preflight(export_kind="handoff_bundle", limit=5)

    assert preflight.decision == "block"
    assert preflight.scanner_clean is True
    assert preflight.would_block_sensitive_export is False
    assert preflight.would_block_invalid_export is True
    assert preflight.validation_scope == "all"
    assert preflight.validation_conforms is False
    assert preflight.validation_result_count > 0
    assert preflight.validation_results
    assert preflight.suggested_next_actions[0].tool_name == "validate_graph"
    assert preflight.suggested_next_actions[0].arguments == {
        "scope": "all",
        "limit_results": 20,
    }
    assert not any(
        action.tool_name == "export_handoff_bundle"
        for action in preflight.suggested_next_actions
    )

    blocked_graph_path = tmp_path / "invalid-observations.ttl"
    with pytest.raises(DoxaBaseError, match="fail_on_invalid=True"):
        db.export_graph(blocked_graph_path, graphs=["observations"])
    assert not blocked_graph_path.exists()

    blocked_trig_path = tmp_path / "invalid-project.trig"
    with pytest.raises(DoxaBaseError, match="fail_on_invalid=True"):
        db.export_trig(blocked_trig_path)
    assert not blocked_trig_path.exists()

    blocked_handoff_trig = tmp_path / "blocked-handoff.trig"
    blocked_handoff_snapshots = tmp_path / "blocked-snapshots.json"
    blocked_handoff_manifest = tmp_path / "blocked-manifest.json"
    with pytest.raises(DoxaBaseError, match="fail_on_invalid=True"):
        db.export_handoff_bundle(
            blocked_handoff_trig,
            blocked_handoff_snapshots,
            manifest_path=blocked_handoff_manifest,
        )
    assert not blocked_handoff_trig.exists()
    assert not blocked_handoff_snapshots.exists()
    assert not blocked_handoff_manifest.exists()

    override_path = tmp_path / "reviewed-invalid-project.trig"
    override = db.export_trig(override_path, fail_on_invalid=False)

    assert override_path.exists()
    assert override.validation_scope == "all"
    assert override.validation_conforms is False
    assert override.validation_result_count > 0
    assert override.would_block_invalid_export is True
    assert any("Export validation failed" in warning for warning in override.warnings)

    handoff_trig = tmp_path / "reviewed-invalid-handoff.trig"
    handoff_snapshots = tmp_path / "reviewed-invalid-snapshots.json"
    handoff_manifest = tmp_path / "reviewed-invalid-manifest.json"
    handoff = db.export_handoff_bundle(
        handoff_trig,
        handoff_snapshots,
        manifest_path=handoff_manifest,
        fail_on_invalid=False,
    )

    assert handoff_trig.exists()
    assert handoff_snapshots.exists()
    assert handoff_manifest.exists()
    assert handoff.decision == "block"
    assert handoff.would_block_invalid_export is True
    assert handoff.validation_scope == "all"
    assert handoff.validation_conforms is False
    assert handoff.validation_result_count > 0
    assert handoff.trig.validation_conforms is False
    manifest = json.loads(handoff_manifest.read_text(encoding="utf-8"))
    assert manifest["would_block_invalid_export"] is True
    assert manifest["validation_conforms"] is False
    assert manifest["validation_result_count"] == handoff.validation_result_count
    assert manifest["artifacts"]["trig"]["validation_conforms"] is False

    receiver = DoxaBase.create(tmp_path / "invalid-handoff-receiver.sqlite")
    imported = receiver.import_handoff_bundle(handoff_manifest)

    assert any(
        "failed export validation" in warning for warning in imported.warnings
    )
    assert imported.suggested_next_actions[0].tool_name == "validate_graph"
    assert imported.suggested_next_actions[0].arguments == {
        "scope": "all",
        "limit_results": min(max(handoff.validation_result_count, 20), 100),
    }
    assert (
        imported.recovery_summary.first_suggested_next_action.tool_name
        == "validate_graph"
    )
    assert receiver.validate_graph(scope="all").conforms is False


def test_context_slice_export_gates_invalid_graphs(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    observation_iri = "https://example.test/project#obs_without_evidence"
    db.import_trig(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rcg: <https://richcanopy.org/graph/> .

        rcg:observations {
            ex:obs_without_evidence a rc:Observation ;
                rc:summary "This observation should block context-slice export." .
        }
        """
    )

    preflight = db.preflight_context_slice_export(
        [observation_iri],
        profile="resource_brief",
        max_triples=50,
        limit=5,
    )

    assert preflight.decision == "block"
    assert preflight.scanner_clean is True
    assert preflight.would_block_sensitive_export is False
    assert preflight.would_block_invalid_export is True
    assert preflight.validation_scope == "patterns"
    assert preflight.validation_conforms is False
    assert preflight.validation_result_count > 0
    assert preflight.validation_results
    assert preflight.suggested_next_actions[0].tool_name == "validate_graph"
    assert preflight.suggested_next_actions[0].arguments == {
        "scope": "patterns",
        "limit_results": 20,
    }
    assert not any(
        action.tool_name == "export_context_slice"
        for action in preflight.suggested_next_actions
    )

    blocked_path = tmp_path / "blocked-invalid-context-slice.trig"
    with pytest.raises(DoxaBaseError, match="fail_on_invalid=True"):
        db.export_context_slice(
            blocked_path,
            [observation_iri],
            profile="resource_brief",
            max_triples=50,
        )
    assert not blocked_path.exists()

    reviewed_path = tmp_path / "reviewed-invalid-context-slice.trig"
    reviewed = db.export_context_slice(
        reviewed_path,
        [observation_iri],
        profile="resource_brief",
        max_triples=50,
        fail_on_invalid=False,
    )

    assert reviewed_path.exists()
    assert reviewed.decision == "block"
    assert reviewed.scanner_clean is True
    assert reviewed.validation_scope == "patterns"
    assert reviewed.validation_conforms is False
    assert reviewed.validation_result_count > 0
    assert reviewed.would_block_invalid_export is True
    assert any("Export validation failed" in warning for warning in reviewed.warnings)

    receiver = DoxaBase.create(tmp_path / "receiver.sqlite")
    receiver.import_trig(reviewed_path)
    receiver_validation = receiver.validate_graph(scope="patterns")
    assert receiver_validation.conforms is False


def test_query_result_context_preflight_flags_scanner_clean_local_runtime_paths(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    query_path = tmp_path / "orders_status.sql"
    result_path = tmp_path / "orders_status_result.json"

    result = db.record_query_result(
        summary="Orders status aggregate ran through an external Python CSV script.",
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path=str(query_path),
        result_sources=[str(result_path)],
        scanned_source_paths=["/work/local-data/orders.csv"],
        sample_scope="Grouped aggregate rows written to a local runtime artifact.",
        sample_method="External read-only aggregate query.",
    )

    context = db.describe_context_slice(
        [result.evidence_iri],
        profile="resource_brief",
    )
    assert context.sensitive_literal_count == 0
    assert "absolute_local_runtime_path" in context.shareability_hints
    assert any(
        match.hint_code == "absolute_local_runtime_path"
        and match.export_part == "context_slice"
        for match in context.shareability_hint_matches
    )

    preflight = db.preflight_context_slice_export(
        [result.evidence_iri],
        profile="resource_brief",
    )

    assert preflight.decision == "clean_by_scanner_only"
    assert preflight.scanner_clean is True
    assert preflight.would_block_sensitive_export is False
    assert preflight.sensitive_literal_count == 0
    assert "absolute_local_runtime_path" in preflight.shareability_hints
    assert preflight.shareability_hint_count >= 2
    assert preflight.git_safe is False
    assert any(
        match.hint_code == "absolute_local_runtime_path"
        and match.export_part == "context_slice_export"
        for match in preflight.shareability_hint_matches
    )
    assert str(query_path) not in json.dumps(
        to_jsonable(preflight.shareability_hint_matches)
    )
    assert str(result_path) not in json.dumps(
        to_jsonable(preflight.shareability_hint_matches)
    )

    exported = db.export_context_slice(
        tmp_path / "query-result-context.trig",
        [result.evidence_iri],
        profile="resource_brief",
        fail_on_sensitive=True,
    )
    assert exported.scanner_clean is True
    assert "absolute_local_runtime_path" in exported.shareability_hints
    assert exported.artifact_disposition == (
        "local_only_pending_shareability_review"
    )
    assert db.validate_graph(scope="all").conforms

