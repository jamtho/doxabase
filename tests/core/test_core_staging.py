"""Split from test_doxabase_core.py (distillation Phase 2); tests verbatim."""

from tests.core.support_core import *  # noqa: F401,F403


def test_stage_graph_revision_reports_stale_seed_patch_role_vocabulary(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    _delete_base_ontology_seed_terms(
        db,
        ["rc:GraphPatchRole", "rc:FramingPatch", "rc:SharedContextPatch"],
    )

    with pytest.raises(DoxaBaseError) as excinfo:
        db.stage_graph_revision(
            summary="Stage stale-seed sample",
            rationale="Exercise compatibility diagnostics for stale seed graphs.",
            additions=[
                {
                    "graph": "map",
                    "content": """
                    @prefix ex: <https://example.test/project#> .
                    ex:s ex:p ex:o .
                    """,
                }
            ],
        )

    message = str(excinfo.value)
    assert "immutable base_ontology is missing current staging vocabulary" in message
    assert "rc:GraphPatchRole" in message
    assert "rc:FramingPatch" in message
    assert "seed_base_graphs() only seeds empty immutable graphs" in message
    assert "fresh DoxaBase.create(...) capsule" in message


def test_stage_graph_revision_reports_stale_seed_revision_stance_vocabulary(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    _delete_base_ontology_seed_terms(db, ["rc:CandidateRevision"])

    with pytest.raises(DoxaBaseError) as excinfo:
        db.stage_graph_revision(
            summary="Stage stale-stance sample",
            rationale="Exercise compatibility diagnostics for stale stance terms.",
            additions=[
                {
                    "graph": "map",
                    "content": """
                    @prefix ex: <https://example.test/project#> .
                    ex:s ex:p ex:o .
                    """,
                }
            ],
        )

    message = str(excinfo.value)
    assert "stance must be an rc:RevisionStance" in message
    assert "immutable base_ontology is missing current staging vocabulary" in message
    assert "rc:CandidateRevision" in message
    assert "seed_base_graphs() only seeds empty immutable graphs" in message
    assert "fresh DoxaBase.create(...) capsule" in message


def test_import_handoff_bundle_routes_non_staged_revision_context(
    tmp_path: Path,
) -> None:
    source = DoxaBase.create(tmp_path / "source.sqlite")
    source.record_map_dataset(
        "https://example.test/project#Orders",
        label="Orders",
        is_table=True,
    )
    manual = source.record_graph_revision(
        summary="Manual map review",
        rationale="Record non-staged review history with exact map snapshots.",
        changed_graphs=["map"],
        included_graphs=["map"],
    )
    staged = source.stage_graph_revision(
        summary="Stage shipment table",
        rationale="Create a staged patch alongside ordinary history context.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:Shipments a rc:Dataset, rc:Table .
                """,
            }
        ],
    )
    trig_path = tmp_path / "project-handoff.trig"
    snapshot_path = tmp_path / "revision-snapshots.json"
    manifest_path = tmp_path / "handoff-manifest.json"
    source.export_handoff_bundle(
        trig_path,
        snapshot_path,
        manifest_path=manifest_path,
        revision_iris=[manual.revision_iri, staged.revision_iri],
        fail_on_sensitive=True,
    )

    receiver = DoxaBase.create(tmp_path / "receiver.sqlite")
    imported = receiver.import_handoff_bundle(manifest_path)

    assert imported.revision_iris == [manual.revision_iri, staged.revision_iri]
    assert imported.recovery_plan is not None
    plan = imported.recovery_plan
    assert plan.processed_revision_iris == [manual.revision_iri, staged.revision_iri]
    assert plan.next_action_queue_item_counts == {
        "apply_after_review": 1,
        "informational": 1,
    }
    lanes_by_source = {lane.source_revision_iri: lane for lane in plan.lanes}
    manual_lane = lanes_by_source[manual.revision_iri]
    assert manual_lane.batch_action == "skipped_non_staged_history_record"
    assert manual_lane.next_action is not None
    assert manual_lane.next_action.tool_name == "describe_graph_revision"
    assert plan.not_restageable_revision_iris_by_reason[
        "non_staged_history_record"
    ] == [manual.revision_iri]
    evidence_by_iri = {
        row.revision_iri: row for row in imported.post_import_snapshot_evidence
    }
    assert evidence_by_iri[manual.revision_iri].status == "history_plus_snapshot_rows"
    assert evidence_by_iri[staged.revision_iri].status == "history_plus_snapshot_rows"
    validation = receiver.validate_graph(scope="all")
    assert validation.conforms, validation.report_text


def test_privacy_handoff_fallback_keeps_clean_slice_when_staged_markdown_is_dirty(
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
    staged = db.stage_graph_revision(
        summary="Stage clean review row",
        rationale="Clean staged row for export-time drift privacy coverage.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:CleanReviewProbe a rc:Dataset .
                """,
            }
        ],
    )
    fake_secret = "FAKE_SECRET_DO_NOT_USE_REVIEW_ARTIFACT_DRIFT"
    db.record_map_storage_access(
        "https://example.test/project#dirty_storage",
        label="Dirty storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=f"/tmp/{fake_secret}/dirty.csv",
        location_kind="object",
    )

    handoff_preflight = db.export_preflight(
        export_kind="handoff_bundle",
        revision_iris=[staged.revision_iri],
        limit=5,
    )
    assert handoff_preflight.decision == "block"
    assert handoff_preflight.would_block_sensitive_export is True
    assert handoff_preflight.graph_sensitive_literal_count >= 1
    assert handoff_preflight.snapshot_sensitive_literal_count == 0
    assert "preflight_context_slice_export" in [
        action.tool.removeprefix("doxabase.") for action in handoff_preflight.suggested_next_actions
    ]
    assert fake_secret not in json.dumps(to_dict(handoff_preflight))

    slice_preflight = db.preflight_context_slice_export(
        [shareable],
        profile="dataset_brief",
        max_triples=200,
        limit=5,
    )
    assert slice_preflight.decision == "clean_by_scanner_only"
    assert slice_preflight.scanner_clean is True
    assert slice_preflight.would_block_sensitive_export is False
    assert slice_preflight.shareability_review_status == "required_not_completed"

    slice_path = tmp_path / "shareable-context-slice.trig"
    slice_export = db.export_context_slice(
        slice_path,
        [shareable],
        profile="dataset_brief",
        max_triples=200,
        fail_on_sensitive=True,
    )
    slice_text = slice_path.read_text(encoding="utf-8")
    assert slice_export.importable is True
    assert slice_export.recovery_complete is False
    assert "ShareableOrders" in slice_text
    assert "dirty_storage" not in slice_text
    assert fake_secret not in slice_text

    receiver = DoxaBase.create(tmp_path / "receiver.sqlite")
    assert receiver.import_trig(slice_path) == {"map": slice_export.triples}

    staged_description = db.describe_staged_revision(staged.revision_iri)
    assert fake_secret not in (staged_description.patches[0].content or "")

    grouped_path = tmp_path / "clean-staged-after-dirty-drift.md"
    grouped_export = db.export_staged_revisions([staged.revision_iri], grouped_path)
    grouped_text = grouped_path.read_text(encoding="utf-8")
    assert grouped_export.sensitive_literal_count >= 1
    assert grouped_export.privacy_warnings
    assert fake_secret not in " ".join(grouped_export.privacy_warnings)
    assert fake_secret in grouped_text
    assert "target_count_drift" in grouped_text

    blocked_grouped_path = tmp_path / "blocked-clean-staged-after-drift.md"
    with pytest.raises(DoxaBaseError, match="fail_on_sensitive=True") as excinfo:
        db.export_staged_revisions(
            [staged.revision_iri],
            blocked_grouped_path,
            fail_on_sensitive=True,
        )
    assert fake_secret not in str(excinfo.value)
    assert not blocked_grouped_path.exists()


def test_stage_graph_revision_records_reviewable_patch_without_mutating_map(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_map_count = db.triple_count("map")
    addition = """
    @prefix ex: <https://example.test/project#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ex:Messages a rc:Dataset, rc:Table ;
        rdfs:label "Messages" .
    """

    staged = db.stage_graph_revision(
        summary="Try messages table framing",
        rationale=(
            "Exploratory hunch: treating messages as the map anchor should make "
            "later join reasoning easier."
        ),
        additions=[{"graph": "map", "content": addition}],
        stance="rc:ExploratoryHunch",
        validation_scope="all",
    )

    assert staged.revision_type == RC + "StagedRevision"
    assert staged.revision_stance == RC + "ExploratoryHunch"
    assert staged.summary == "Try messages table framing"
    assert staged.rationale == (
        "Exploratory hunch: treating messages as the map anchor should make "
        "later join reasoning easier."
    )
    assert staged.review_note is None
    assert staged.review_recommendation is None
    assert staged.changed_graphs == ["map"]
    assert staged.validation_conforms is True
    assert staged.validation_result_count == 0
    assert staged.patches[0].operation == RC + "AdditionPatch"
    assert staged.patches[0].target_graph == "map"
    assert staged.patches[0].patch_role == RC + "FramingPatch"
    assert staged.patches[0].sequence_index == 1
    assert staged.patches[0].triple_count == 3
    assert staged.patches[0].count_basis == "target_graph_only"
    assert staged.patches[0].before_triple_count == before_map_count
    assert staged.patches[0].after_triple_count == before_map_count + 3
    assert db.triple_count("map") == before_map_count

    description = db.describe_staged_revision(staged.revision_iri)
    assert description.revision_stance_label == "exploratory hunch"
    assert description.revision_type_label == "staged revision"
    assert description.validation_conforms is True
    assert description.patches[0].patch_role_label == "framing patch"
    assert description.patches[0].sequence_index == 1
    assert description.patches[0].count_basis == "target_graph_only"
    assert description.patches[0].content is not None
    assert "ex:Messages" in description.patches[0].content
    overview = db.graph_overview()
    assert overview.key_counts["graph_revisions"] == 1
    assert overview.key_counts["graph_patches"] == 1
    assert db.validate_graph(scope="all").conforms

    export_path = tmp_path / "staged-review.md"
    export = db.export_staged_revision(staged.revision_iri, export_path)
    assert export.path == str(export_path)
    assert export.format == "markdown"
    assert export.shareability_review_required is True
    assert export.shareability_review_status == "required_not_completed"
    assert export.sensitive_literal_count == 0
    assert export.privacy_warnings == []
    export_text = export_path.read_text()
    assert "exploratory hunch" in export_text
    assert "ex:Messages" in export_text


def test_staged_markdown_exports_warn_about_sensitive_patch_literals(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_DO_NOT_USE_456"
    secret_text = f"Bearer {fake_secret}"
    staged = db.stage_graph_revision(
        summary="Stage credential caveat",
        rationale="The export should warn while preserving patch content.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:CredentialCaveat a rc:KnownCaveat ;
                        rdfs:label "Credential caveat" ;
                        rc:caveatDescription "{secret_text}" .
                """,
            }
        ],
    )

    single_path = tmp_path / "single.md"
    single_export = db.export_staged_revision(staged.revision_iri, single_path)
    single_text = single_path.read_text(encoding="utf-8")

    assert single_export.sensitive_literal_count == 1
    assert single_export.shareability_review_required is True
    assert single_export.shareability_review_status == "required_not_completed"
    assert single_export.privacy_warnings
    assert fake_secret not in " ".join(single_export.privacy_warnings)
    assert secret_text in single_text
    assert "## Privacy Warning" in single_text
    assert single_text.index("## Privacy Warning") < single_text.index(
        "## Current Apply Check"
    )
    single_secret_line = _line_number_containing(single_text, secret_text)
    assert f"line {single_secret_line} " in " ".join(
        single_export.privacy_warnings
    )
    single_warning_prefix = single_text.split("## Current Apply Check", 1)[0]
    assert fake_secret not in single_warning_prefix

    grouped_path = tmp_path / "grouped.md"
    grouped_export = db.export_staged_revisions(
        [staged.revision_iri],
        grouped_path,
    )
    grouped_text = grouped_path.read_text(encoding="utf-8")

    assert grouped_export.sensitive_literal_count == 1
    assert grouped_export.shareability_review_required is True
    assert grouped_export.shareability_review_status == "required_not_completed"
    assert grouped_export.privacy_warnings
    assert fake_secret not in " ".join(grouped_export.privacy_warnings)
    assert secret_text in grouped_text
    assert "## Privacy Warning" in grouped_text
    assert grouped_text.index("## Privacy Warning") < grouped_text.index(
        "## Reviewer Decision Matrix"
    )
    grouped_secret_line = _line_number_containing(grouped_text, secret_text)
    assert f"line {grouped_secret_line} " in " ".join(
        grouped_export.privacy_warnings
    )
    grouped_warning_prefix = grouped_text.split(
        "## Reviewer Decision Matrix",
        1,
    )[0]
    assert fake_secret not in grouped_warning_prefix

    blocked_single_path = tmp_path / "blocked-single.md"
    with pytest.raises(DoxaBaseError, match="fail_on_sensitive=True"):
        db.export_staged_revision(
            staged.revision_iri,
            blocked_single_path,
            fail_on_sensitive=True,
        )
    assert not blocked_single_path.exists()

    blocked_grouped_path = tmp_path / "blocked-grouped.md"
    with pytest.raises(DoxaBaseError, match="fail_on_sensitive=True"):
        db.export_staged_revisions(
            [staged.revision_iri],
            blocked_grouped_path,
            fail_on_sensitive=True,
        )
    assert not blocked_grouped_path.exists()


@pytest.mark.parametrize(
    "key_mode",
    [
        "live",
        "test",
    ],
)
def test_staged_markdown_exports_block_sk_style_secret_keys(
    tmp_path: Path,
    key_mode: str,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    synthetic_key = "sk_" + key_mode + "_" + "abcdefghijklmnopqrstuvwx"
    staged = db.stage_graph_revision(
        summary="Stage credential caveat",
        rationale="The export should block secret-key-shaped patch content.",
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:SecretKeyCaveat a rc:KnownCaveat ;
                        rdfs:label "Secret key caveat" ;
                        rc:caveatDescription "{synthetic_key}" .
                """,
            }
        ],
    )
    history_scan = db.scan_sensitive_literals(graphs="history", limit=10)

    assert "sk_secret_key" in {match.match_kind for match in history_scan.matches}
    assert synthetic_key not in str(history_scan.matches)

    single_path = tmp_path / "single-sk.md"
    single_export = db.export_staged_revision(staged.revision_iri, single_path)
    single_text = single_path.read_text(encoding="utf-8")

    assert single_export.sensitive_literal_count == 1
    assert single_export.privacy_warnings
    assert synthetic_key not in " ".join(single_export.privacy_warnings)
    assert synthetic_key in single_text
    assert "## Privacy Warning" in single_text
    secret_line = _line_number_containing(single_text, synthetic_key)
    assert f"line {secret_line} " in " ".join(single_export.privacy_warnings)

    grouped_path = tmp_path / "grouped-sk.md"
    grouped_export = db.export_staged_revisions(
        [staged.revision_iri],
        grouped_path,
    )
    grouped_text = grouped_path.read_text(encoding="utf-8")

    assert grouped_export.sensitive_literal_count == 1
    assert grouped_export.privacy_warnings
    assert synthetic_key not in " ".join(grouped_export.privacy_warnings)
    assert synthetic_key in grouped_text
    grouped_secret_line = _line_number_containing(grouped_text, synthetic_key)
    assert f"line {grouped_secret_line} " in " ".join(
        grouped_export.privacy_warnings
    )

    blocked_single_path = tmp_path / "blocked-single-sk.md"
    with pytest.raises(DoxaBaseError) as single_excinfo:
        db.export_staged_revision(
            staged.revision_iri,
            blocked_single_path,
            fail_on_sensitive=True,
        )
    assert "fail_on_sensitive=True" in str(single_excinfo.value)
    assert synthetic_key not in str(single_excinfo.value)
    assert not blocked_single_path.exists()

    blocked_grouped_path = tmp_path / "blocked-grouped-sk.md"
    with pytest.raises(DoxaBaseError) as grouped_excinfo:
        db.export_staged_revisions(
            [staged.revision_iri],
            blocked_grouped_path,
            fail_on_sensitive=True,
        )
    assert "fail_on_sensitive=True" in str(grouped_excinfo.value)
    assert synthetic_key not in str(grouped_excinfo.value)
    assert not blocked_grouped_path.exists()


def test_stage_graph_revision_exposes_seed_expanded_count_basis(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    staged = db.stage_graph_revision(
        summary="Stage vocabulary and map anchors",
        rationale=(
            "Expose whether staged preview counts are role-local or include "
            "seed context."
        ),
        additions=[
            {
                "graph": "ontology",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:SeedAwareClass a rdfs:Class ;
                        rdfs:label "Seed-aware class" .
                """,
            },
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:SeedAwareThing rdfs:label "Seed-aware thing" .
                """,
            },
            {
                "graph": "shapes",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix sh: <http://www.w3.org/ns/shacl#> .

                    ex:SeedAwareThingShape a sh:NodeShape ;
                        sh:targetNode ex:SeedAwareThing .
                """,
            },
        ],
        validation_scope="all",
    )

    patches_by_graph = {patch.target_graph: patch for patch in staged.patches}
    ontology_patch = patches_by_graph["ontology"]
    map_patch = patches_by_graph["map"]
    shapes_patch = patches_by_graph["shapes"]
    assert ontology_patch.count_basis == "target_graph_plus_base_ontology"
    assert map_patch.count_basis == "target_graph_only"
    assert shapes_patch.count_basis == "target_graph_plus_base_shapes"
    assert ontology_patch.before_triple_count == (
        db.triple_count("base_ontology") + db.triple_count("ontology")
    )
    assert map_patch.before_triple_count == db.triple_count("map")
    assert shapes_patch.before_triple_count == (
        db.triple_count("base_shapes") + db.triple_count("shapes")
    )

    description = db.describe_staged_revision(staged.revision_iri)
    description_patches = {patch.target_graph: patch for patch in description.patches}
    assert (
        description_patches["ontology"].count_basis
        == "target_graph_plus_base_ontology"
    )
    assert description_patches["map"].count_basis == "target_graph_only"
    assert (
        description_patches["shapes"].count_basis == "target_graph_plus_base_shapes"
    )

    check = db.check_staged_revision_apply(staged.revision_iri)
    check_patches = {patch.target_graph: patch for patch in check.patch_checks}
    assert (
        check_patches["ontology"].count_basis
        == "target_graph_plus_base_ontology"
    )
    assert check_patches["map"].count_basis == "target_graph_only"
    assert check_patches["shapes"].count_basis == "target_graph_plus_base_shapes"

    export_path = tmp_path / "staged-review.md"
    db.export_staged_revision(staged.revision_iri, export_path)
    export_text = export_path.read_text()
    assert "- Count basis: `target_graph_plus_base_ontology`" in export_text
    assert "- Count basis: `target_graph_plus_base_shapes`" in export_text
    assert "| Count basis |" in export_text

    grouped_export_path = tmp_path / "grouped-staged-review.md"
    db.export_staged_revisions([staged.revision_iri], grouped_export_path)
    grouped_export_text = grouped_export_path.read_text()
    assert "## Count Basis Context" in grouped_export_text
    assert "stored revision snapshots are role-local graph counts" in grouped_export_text
    assert (
        "| 1 | ontology | 1 | target_graph_plus_base_ontology |"
        in grouped_export_text
    )
    assert "| 1 | map | 2 | target_graph_only |" in grouped_export_text
    assert "| 1 | shapes | 3 | target_graph_plus_base_shapes |" in grouped_export_text

    map_only = db.stage_graph_revision(
        summary="Stage map-only role-local patch",
        rationale="Grouped exports should stay quiet for simple role-local patches.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:RoleLocalThing rdfs:label "Role-local thing" .
                """,
            }
        ],
        validation_scope="all",
    )
    map_only_export_path = tmp_path / "map-only-grouped-review.md"
    db.export_staged_revisions([map_only.revision_iri], map_only_export_path)
    map_only_export_text = map_only_export_path.read_text()
    assert "## Count Basis Context" not in map_only_export_text


def test_stage_graph_revision_parse_errors_include_parser_detail(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    malformed_patch = (
        "@prefix ex: <https://example.test/project#> .\n"
        "@prefix rc: <https://richcanopy.org/ns/rc#> .\n"
        "\n"
        "ex:Messages a rc:Dataset\n"
        "ex:Other a rc:Dataset ."
    )

    with pytest.raises(DoxaBaseError) as exc_info:
        db.stage_graph_revision(
            summary="Stage malformed patch",
            rationale="Malformed RDF should report parser detail.",
            additions=[
                {
                    "graph": "map",
                    "content": malformed_patch,
                }
            ],
        )

    message = str(exc_info.value)
    assert "Could not parse staged patch for graph 'map' as turtle" in message
    assert "at line" in message
    assert "expected '.'" in message
    assert "at ^ in" not in message


def test_stored_staged_patch_unknown_target_graph_blocks_apply_without_mutation(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = db.stage_graph_revision(
        summary="Stage messages table",
        rationale="Exercise stored target graph validation.",
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
    assert db.check_staged_revision_apply(staged.revision_iri).status == "ready"
    before_counts = _mutable_graph_counts(db)
    unknown_graph = "not_a_graph_role"
    assert db.triple_count(unknown_graph) == 0

    _corrupt_staged_patch_target_graph(
        db,
        staged.patches[0].patch_iri,
        unknown_graph,
    )

    description = db.describe_staged_revision(staged.revision_iri)
    assert description.patches[0].target_graph == unknown_graph
    check = db.check_staged_revision_apply(staged.revision_iri)
    assert check.can_apply is False
    assert check.status == "conflict"
    assert check.decision == "inspect_patch_conflict"
    assert check.blocking_reasons == ["patch_conflict"]
    assert check.recommended_resolution is not None
    assert "stage a repaired or alternative candidate" in check.recommended_resolution
    assert check.validation_conforms is None
    assert check.validation_skipped_reason == "conflicts_present"
    assert [action.tool.removeprefix("doxabase.") for action in check.suggested_next_actions] == [
        "describe_staged_revision",
        "export_staged_revision",
    ]
    assert check.suggested_next_actions[1].args["fail_on_sensitive"] is True
    assert check.patch_checks[0].target_graph == unknown_graph
    assert check.patch_checks[0].can_apply is False
    assert check.patch_checks[0].conflict is not None
    assert "targets unknown graph role" in check.patch_checks[0].conflict
    assert "targets unknown graph role" in check.conflicts[0]

    with pytest.raises(DoxaBaseError, match="targets unknown graph role"):
        db.apply_staged_revision(staged.revision_iri)
    with pytest.raises(DoxaBaseError, match="only handles count/digest drift"):
        db.restage_staged_revision(staged.revision_iri)

    batch = db.restage_staged_revisions([staged.revision_iri], dry_run=True)
    assert batch.would_restage_revision_iris == []
    assert batch.not_restageable_revision_iris == [staged.revision_iri]
    assert batch.not_restageable_revision_iris_by_reason == {
        "patch_conflict": [staged.revision_iri],
    }
    assert batch.items[0].action == "skipped_not_restageable"
    assert batch.items[0].not_restageable_reason == "patch_conflict"
    assert batch.items[0].decision_before == "inspect_patch_conflict"
    assert batch.bundle_summary.recommended_mutation_review_iris == [
        staged.revision_iri
    ]
    assert batch.bundle_summary.recommended_apply_or_restage_review_iris == []
    assert batch.bundle_summary.recommended_repair_review_iris == [
        staged.revision_iri
    ]
    assert batch.bundle_summary.next_action_queue == {
        "repair_or_replace": [staged.revision_iri],
    }

    assert _mutable_graph_counts(db) == before_counts
    assert db.triple_count(unknown_graph) == 0


def test_stored_malformed_staged_patch_conflict_includes_parser_detail(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    malformed_patch = (
        "@prefix ex: <https://example.test/project#> .\n"
        "@prefix rc: <https://richcanopy.org/ns/rc#> .\n"
        "\n"
        "ex:Messages a rc:Dataset\n"
        "ex:Other a rc:Dataset ."
    )
    staged = db.stage_graph_revision(
        summary="Stage messages table",
        rationale="Exercise stored patch parse diagnostics.",
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
    before_counts = _mutable_graph_counts(db)
    _corrupt_staged_patch_content(
        db,
        staged.patches[0].patch_iri,
        malformed_patch,
    )

    check = db.check_staged_revision_apply(staged.revision_iri)
    assert check.can_apply is False
    assert check.status == "conflict"
    assert check.decision == "inspect_patch_conflict"
    assert check.blocking_reasons == ["patch_conflict"]
    assert all(
        action.tool != "doxabase.restage_staged_revision"
        for action in check.suggested_next_actions
    )
    assert check.patch_checks[0].conflict is not None
    assert "Could not parse staged patch" in check.patch_checks[0].conflict
    assert "at line" in check.patch_checks[0].conflict
    assert "expected '.'" in check.patch_checks[0].conflict
    assert "at ^ in" not in check.patch_checks[0].conflict

    with pytest.raises(DoxaBaseError, match="expected '\\.'"):
        db.apply_staged_revision(staged.revision_iri)

    assert _mutable_graph_counts(db) == before_counts


def test_mixed_staged_revision_uses_recorded_patch_sequence_for_apply_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rc: <https://richcanopy.org/ns/rc#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:Messages a rc:Dataset, rc:Table ;
            rdfs:label "Messages" .
        """,
        graph="map",
    )

    minted_patch_iris = iter(
        [
            "https://example.test/generated/graph-patch/z-addition",
            "https://example.test/generated/graph-patch/a-removal",
            "https://example.test/generated/staged-revision/sequence-test",
        ]
    )

    def mint_iri(kind: str) -> str:
        if kind in {"graph-patch", "staged-revision"}:
            return next(minted_patch_iris)
        return f"https://example.test/generated/{kind}/fallback"

    monkeypatch.setattr(db, "_mint_iri", mint_iri)

    staged = db.stage_graph_revision(
        summary="Swap message label for comment",
        rationale=(
            "Regression test: the removal patch has a lexically earlier IRI than "
            "the addition patch, but apply checks must use recorded preview order."
        ),
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Messages rdfs:comment "Staged explanatory comment." .
                """,
            }
        ],
        removals=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Messages rdfs:label "Messages" .
                """,
            }
        ],
        validation_scope="all",
    )

    description = db.describe_staged_revision(staged.revision_iri)
    assert [patch.sequence_index for patch in description.patches] == [1, 2]
    assert [patch.operation for patch in description.patches] == [
        RC + "AdditionPatch",
        RC + "RemovalPatch",
    ]
    assert description.patches[0].before_triple_count == 3
    assert description.patches[0].after_triple_count == 4
    assert description.patches[1].before_triple_count == 4
    assert description.patches[1].after_triple_count == 3

    check = db.check_staged_revision_apply(staged.revision_iri)
    assert check.can_apply is True
    assert check.conflicts == []
    assert [patch.current_triple_count for patch in check.patch_checks] == [3, 4]

    db.record_map_dataset(
        "https://example.test/project#OtherDataset",
        label="Other dataset",
    )
    stale_check = db.check_staged_revision_apply(staged.revision_iri)

    assert stale_check.blocking_reasons == ["target_count_drift"]
    assert [drift.patch_sequence_index for drift in stale_check.count_drifts] == [
        1,
        2,
    ]
    assert stale_check.count_drifts[0].expected_before_basis == (
        "expected_before_triple_count is the original staged graph snapshot "
        "before patch 1"
    )
    assert stale_check.count_drifts[1].expected_before_basis == (
        "expected_before_triple_count is the staged replay count before patch 2 "
        "for this patch's target graph, after any earlier patches that affected "
        "that target graph"
    )


def test_export_staged_revisions_dedupes_duplicate_inputs(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = db.stage_graph_revision(
        summary="Stage messages dataset",
        rationale="Exercise duplicate grouped export routing.",
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

    export = db.export_staged_revisions(
        [staged.revision_iri, staged.revision_iri],
        tmp_path / "duplicate-review.md",
    )

    assert export.revision_iris == [staged.revision_iri]
    assert [item.revision_iri for item in export.revision_summaries] == [
        staged.revision_iri
    ]
    assert export.bundle_summary.total_revisions == 1
    assert export.bundle_summary.apply_status_counts == {"ready": 1}
    assert export.bundle_summary.stale_resolution_state_counts == {"ready": 1}
    assert export.bundle_summary.next_action_queue == {
        "apply_after_review": [staged.revision_iri]
    }
    assert export.bundle_summary.post_apply_recheck_revision_iris == []
    assert export.bundle_summary.warnings == []


def test_authored_repair_for_staged_validation_failure_can_apply_after_review(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    scope = "https://example.test/project#DispatchTemporalScope"
    clock = "https://example.test/project#dispatch_events__event_local_time"
    timezone = "https://example.test/project#dispatch_events__timezone_hint"
    db.import_turtle(
        """
        @prefix ft: <https://example.test/project/systematisation#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ft:TemporalInterpretationScope a rdfs:Class ;
            rdfs:label "Temporal interpretation scope" .

        ft:clockColumn a rdf:Property ;
            rdfs:label "clock column" .

        ft:timezoneEvidenceColumn a rdf:Property ;
            rdfs:label "timezone evidence column" .
        """,
        graph="ontology",
    )
    db.import_turtle(
        """
        @prefix ft: <https://example.test/project/systematisation#> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .

        ft:TemporalInterpretationScopeShape a sh:NodeShape ;
            sh:targetClass ft:TemporalInterpretationScope ;
            sh:property [
                sh:path ft:timezoneEvidenceColumn ;
                sh:minCount 1 ;
                sh:nodeKind sh:IRI ;
                sh:message "Temporal scopes must name timezone evidence."
            ] .
        """,
        graph="shapes",
    )
    source = db.stage_graph_revision(
        summary="Stage incomplete temporal scope",
        rationale=(
            "Regression test: this source failed staged-time validation because "
            "the framing omitted timezone evidence."
        ),
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix ft: <https://example.test/project/systematisation#> .

                    <{scope}> a ft:TemporalInterpretationScope ;
                        ft:clockColumn <{clock}> .
                """,
            }
        ],
        validation_scope="all",
    )
    assert source.validation_conforms is False

    repair = db.stage_graph_revision(
        summary="Repair temporal scope framing",
        rationale=(
            "Caller-authored repair adds the missing timezone evidence named by "
            "the source validation diagnostics."
        ),
        additions=[
            {
                "graph": "map",
                "content": f"""
                    @prefix ft: <https://example.test/project/systematisation#> .

                    <{scope}> a ft:TemporalInterpretationScope ;
                        ft:clockColumn <{clock}> ;
                        ft:timezoneEvidenceColumn <{timezone}> .
                """,
            }
        ],
        restages_revision=source.revision_iri,
        validation_scope="all",
    )
    assert repair.validation_conforms is True

    check = db.check_staged_revision_apply(repair.revision_iri)

    warning = (
        "The restaged source failed staged-time validation with 1 result(s)"
    )
    assert check.status == "ready"
    assert check.can_apply is True
    assert check.validation_conforms is True
    assert check.decision == "review_then_apply"
    assert any(warning in reason for reason in check.semantic_risk_reasons)
    assert check.recommended_resolution is not None
    assert warning in check.recommended_resolution
    assert "revised successor payload" in check.recommended_resolution
    assert check.next_action is not None
    assert check.next_action.action_type == "apply_after_review"
    assert check.next_action.queue == "apply_after_review"
    assert check.next_action.tool_name == "apply_staged_revision"
    assert any(
        action.tool == "doxabase.apply_staged_revision"
        for action in check.suggested_next_actions
    )

    source_check = db.check_staged_revision_apply(source.revision_iri)
    assert source_check.status == "validation_failed"
    assert source_check.decision == "inspect_validation_results"
    assert source_check.restaged_by == repair.revision_iri
    assert source_check.current_restaged_by == repair.revision_iri
    assert source_check.stale_resolution_state == "stale_handled_by_restage"
    assert source_check.summary.startswith("Handled by restage; inspect successor")
    assert source_check.next_action is not None
    assert source_check.next_action.action_type == "inspect_current_successor"
    assert source_check.next_action.queue == "informational"
    assert source_check.next_action.tool_name == "describe_staged_revision"
    assert source_check.next_action.arguments == {"iri": repair.revision_iri}
    assert [action.tool.removeprefix("doxabase.") for action in source_check.suggested_next_actions] == [
        "describe_staged_revision",
        "export_staged_revision",
    ]
    assert source_check.suggested_next_actions[0].args == {
        "iri": repair.revision_iri,
    }
    assert source_check.suggested_next_actions[1].args["iri"] == (
        source.revision_iri
    )
    assert "handled-validation-failure" in (
        source_check.suggested_next_actions[1].args["path"]
    )
    assert source_check.recommended_resolution is not None
    assert "already has a refreshed successor" in (
        source_check.recommended_resolution
    )
    assert source_check.validation_result_count == 1
    source_description = db.describe_staged_revision(
        source.revision_iri,
        include_current_apply_check=True,
    )
    assert source_description.current_apply_check is not None
    assert source_description.current_apply_check.stale_resolution_state == (
        "stale_handled_by_restage"
    )
    assert source_description.current_apply_check.next_action is not None
    assert source_description.current_apply_check.next_action.arguments == {
        "iri": repair.revision_iri,
    }

    current_work = db.list_graph_revisions(
        revision_type="rc:StagedRevision",
        current_staged_work_only=True,
    )
    assert [item.iri for item in current_work.revisions] == [repair.revision_iri]
    listing = db.list_graph_revisions(
        revision_type="rc:StagedRevision",
        include_apply_checks=True,
    )
    by_iri = {item.iri: item for item in listing.revisions}
    assert by_iri[source.revision_iri].stale_resolution_state == (
        "stale_handled_by_restage"
    )
    assert by_iri[source.revision_iri].next_action is not None
    assert by_iri[source.revision_iri].next_action.arguments == {
        "iri": repair.revision_iri,
    }
    assert listing.next_action_queue == {
        "informational": [source.revision_iri],
        "apply_after_review": [repair.revision_iri],
    }

    export = db.export_staged_revisions(
        [source.revision_iri, repair.revision_iri],
        tmp_path / "authored-repair-review.md",
    )
    assert export.bundle_summary.apply_status_counts == {
        "validation_failed": 1,
        "ready": 1,
    }
    assert export.bundle_summary.stale_resolution_state_counts == {
        "stale_handled_by_restage": 1,
        "restaged_successor_ready": 1,
    }
    assert export.bundle_summary.validation_failed_revision_iris == [
        source.revision_iri,
    ]
    assert export.bundle_summary.staged_validation_failed_revision_iris == [
        source.revision_iri,
    ]
    assert export.bundle_summary.recommended_repair_review_iris == []
    assert export.bundle_summary.recommended_apply_or_restage_review_iris == [
        repair.revision_iri,
    ]
    assert export.bundle_summary.next_action_queue == {
        "informational": [source.revision_iri],
        "apply_after_review": [repair.revision_iri],
    }

    applied = db.apply_staged_revision(repair.revision_iri)
    assert applied.staged_revision_iri == repair.revision_iri
    assert applied.validation_conforms is True


def test_list_graph_versions_can_include_staged_apply_checks(
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
        created_at="2026-06-01T10:00:00Z",
    )
    db.record_map_dataset(
        "https://example.test/project#UnrelatedDrift",
        label="Unrelated drift dataset",
        is_table=True,
    )

    versions = db.list_graph_versions(
        "map",
        exact_only=True,
        include_apply_checks=True,
        drift_detail="exact",
    )

    assert versions.include_apply_checks is True
    assert versions.drift_detail == "exact"
    assert [item.revision_iri for item in versions.versions] == [
        staged.revision_iri
    ]
    row = versions.versions[0]
    assert row.is_current_staged_work is True
    assert row.application_status == "conflict"
    assert row.application_decision == "restage_against_current_graph"
    assert row.application_can_apply is False
    assert row.application_blocking_reasons == ["target_count_drift"]
    assert row.stale_resolution_state == "stale_unresolved"
    assert row.next_action is not None
    assert row.next_action.queue == "restage_after_review"
    assert row.next_action.arguments == {"iri": staged.revision_iri}
    assert row.next_action_queue_item is not None
    assert row.next_action_queue_item.queue == "restage_after_review"
    assert row.next_action_queue_item.resolved_target_iri == staged.revision_iri
    assert [
        action.tool.removeprefix("doxabase.") for action in row.suggested_next_actions[:3]
    ] == [
        "describe_revision_graph_snapshot",
        "describe_revision_lineage",
        "describe_graph_version_diff",
    ]


def test_graph_versions_surface_review_resolved_staged_rows(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    messages = "https://example.test/project#Messages"
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
        created_at="2026-06-01T10:00:00Z",
    )
    db.record_map_dataset(messages)
    resolution = db.record_staged_revision_review_decision(
        staged.revision_iri,
        decision="no_effective_change",
        rationale=(
            "Reviewed the stale source and confirmed the same fact already "
            "exists in the current map."
        ),
        created_at="2026-06-01T10:01:00Z",
    )

    versions = db.list_graph_versions(
        "map",
        record_kind="staged_patch",
        include_current=False,
    )

    assert [item.revision_iri for item in versions.versions] == [
        staged.revision_iri
    ]
    version = versions.versions[0]
    assert version.is_current_staged_work is False
    assert version.not_current_staged_work_reason == "review_resolved"
    assert version.review_resolution is not None
    assert version.review_resolution.decision == "no_effective_change"
    assert (
        version.review_resolution.resolution_revision_iri
        == resolution.resolution_revision_iri
    )

    diff = db.describe_graph_version_diff("map", staged.revision_iri)

    assert diff.before_revision_context is not None
    assert diff.before_revision_context.application_status == "conflict"
    assert diff.before_revision_context.application_decision == (
        "restage_against_current_graph"
    )
    assert diff.before_revision_context.is_current_staged_work is False
    assert (
        diff.before_revision_context.not_current_staged_work_reason
        == "review_resolved"
    )
    assert diff.before_revision_context.review_resolution is not None
    assert (
        diff.before_revision_context.review_resolution.decision
        == "no_effective_change"
    )
    assert (
        diff.before_revision_context.review_resolution.resolution_revision_iri
        == resolution.resolution_revision_iri
    )


def test_list_resource_revisions_filters_current_staged_work_before_pagination(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    orders = "https://example.test/project#Orders"
    db.record_map_dataset(orders, label="Orders", is_table=True)
    stale = db.stage_graph_revision(
        summary="Add Orders stewardship note",
        rationale="Patch-only source exercises resource live-work filtering.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Orders rdfs:comment "Owned by the operations team." .
                """,
            }
        ],
        created_at="2026-06-01T10:00:00Z",
    )
    db.record_map_dataset(
        "https://example.test/project#DriftMaker",
        label="Drift maker",
    )
    restaged = db.restage_staged_revision(
        stale.revision_iri,
        created_at="2026-06-01T10:01:00Z",
    )

    full_listing = db.list_resource_revisions(
        orders,
        include_apply_checks=True,
        limit=1,
        offset=0,
    )
    assert full_listing.count == 2
    assert len(full_listing.revisions) == 1
    assert full_listing.revisions[0].revision.iri == restaged.revision_iri

    live_listing = db.list_resource_revisions(
        orders,
        include_apply_checks=False,
        current_staged_work_only=True,
        limit=1,
        offset=0,
    )

    assert live_listing.current_staged_work_only is True
    assert live_listing.include_apply_checks is True
    assert live_listing.count == 1
    assert [item.revision.iri for item in live_listing.revisions] == [
        restaged.revision_iri
    ]
    assert live_listing.revisions[0].revision.is_current_staged_work is True
    assert live_listing.revisions[0].revision.application_status == "ready"
    assert live_listing.next_action_queue == {
        "apply_after_review": [restaged.revision_iri]
    }

    stale_lineage = db.describe_resource_revision_lineage(
        orders,
        stale.revision_iri,
    )
    assert stale_lineage.current_revision_iri == restaged.revision_iri
    assert stale_lineage.latest_revision_iri == restaged.revision_iri
    assert stale_lineage.latest_role == "current_staged_revision"

    hidden_patch_only_live_work = db.list_resource_revisions(
        orders,
        include_patch_mentions=False,
        current_staged_work_only=True,
    )
    assert hidden_patch_only_live_work.count == 0
    assert hidden_patch_only_live_work.patch_mention_scan.status == "not_requested"


def test_staged_row_semantics_validation_hint_guides_clean_recipe(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    bad = db.stage_graph_revision(
        summary="Stage prose row semantics",
        rationale="The review payload should explain how to repair row semantics.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:Orders a rc:Dataset, rc:Table ;
                        rdfs:label "Orders" ;
                        rc:rowSemantics "one row per order event" .
                """,
            }
        ],
        validation_scope="all",
    )

    check = db.check_staged_revision_apply(bad.revision_iri)

    assert check.status == "validation_failed"
    assert check.validation_results
    diagnostic = check.validation_results[0]
    assert diagnostic.result_path == RC + "rowSemantics"
    assert diagnostic.hint is not None
    assert "rc:EventRow" in diagnostic.hint
    assert "rdfs:comment" in diagnostic.hint
    description = db.describe_staged_revision(bad.revision_iri)
    assert description.validation_results[0].hint == diagnostic.hint
    export_path = tmp_path / "bad-row-semantics.md"
    db.export_staged_revision(bad.revision_iri, export_path)
    assert "Hint: Use one of rc:EventRow" in export_path.read_text()

    clean = db.stage_graph_revision(
        summary="Stage controlled row semantics",
        rationale="Use controlled row semantics and keep row-grain prose in a comment.",
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:CleanOrders a rc:Dataset, rc:Table ;
                        rdfs:label "Clean orders" ;
                        rdfs:comment "One row per order event." ;
                        rc:rowSemantics rc:EventRow ;
                        rc:schemaStability rc:FixedSchema .
                """,
            }
        ],
        validation_scope="all",
    )

    clean_check = db.check_staged_revision_apply(clean.revision_iri)

    assert clean.validation_conforms is True
    assert clean_check.status == "ready"


def test_staged_pattern_support_hint_distinguishes_revision_metadata(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Tickets"
    supported_pattern = "https://example.test/project#SupportedWorkflowPattern"
    db.record_map_dataset(dataset, label="Tickets", is_table=True)
    observation = db.record_observation(
        summary="Tickets profile showed workflow-state ambiguity.",
        observed_asset=dataset,
        evidence_sources=["test://tickets/profile"],
    )
    unsupported = db.stage_graph_revision(
        summary="Stage unsupported workflow pattern",
        rationale=(
            "The staged revision has support metadata, but the pattern Turtle "
            "itself omits support triples."
        ),
        additions=[
            {
                "graph": "patterns",
                "content": f"""
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:WorkflowPattern a rc:Pattern ;
                        rc:summary "Workflow-state ambiguity pattern" ;
                        rc:patternText "Workflow state interpretation varies." ;
                        rc:rationale "Observed in profile evidence." ;
                        rc:patternTarget <{dataset}> ;
                        rc:patternStability rc:EmergingPattern .
                """,
            }
        ],
        supporting_observations=[observation.observation_iri],
        evidence=[observation.evidence_iri],
        validation_scope="all",
    )

    assert unsupported.validation_conforms is False
    staged_diagnostic = unsupported.validation_results[0]
    assert staged_diagnostic.source_shape == RC + "PatternShape"
    assert staged_diagnostic.hint is not None
    assert "Revision-level support metadata does not satisfy" in (
        staged_diagnostic.hint
    )
    assert "rc:supportingObservation" in staged_diagnostic.hint
    assert "pattern framing Turtle" in staged_diagnostic.hint

    check = db.check_staged_revision_apply(unsupported.revision_iri)
    description = db.describe_staged_revision(unsupported.revision_iri)
    assert check.validation_results[0].hint == staged_diagnostic.hint
    assert description.validation_results[0].hint == staged_diagnostic.hint
    export_path = tmp_path / "unsupported-pattern.md"
    db.export_staged_revision(unsupported.revision_iri, export_path)
    assert "Hint: Revision-level support metadata" in export_path.read_text()

    repaired = db.stage_graph_revision(
        summary="Stage supported workflow pattern",
        rationale="The pattern Turtle carries the support required by PatternShape.",
        additions=[
            {
                "graph": "patterns",
                "content": f"""
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:SupportedWorkflowPattern a rc:Pattern ;
                        rc:summary "Workflow-state ambiguity pattern" ;
                        rc:patternText "Workflow state interpretation varies." ;
                        rc:rationale "Observed in profile evidence." ;
                        rc:patternTarget <{dataset}> ;
                        rc:supportingObservation <{observation.observation_iri}> ;
                        rc:evidence <{observation.evidence_iri}> ;
                        rc:patternStability rc:EmergingPattern .
                """,
            }
        ],
        supporting_observations=[observation.observation_iri],
        evidence=[observation.evidence_iri],
        revision_anchors=[supported_pattern],
        validation_scope="all",
    )

    assert repaired.validation_conforms is True
    assert db.check_staged_revision_apply(repaired.revision_iri).status == "ready"


def test_list_graph_revisions_filters_staged_validation_after_live_conflict(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = db.stage_graph_revision(
        summary="Stage invalid value type",
        rationale="Exercise stored validation diagnostics after target drift.",
        additions=[
            {
                "graph": "ontology",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:BadValueType a rc:ValueType ;
                        rc:requiredPhysicalType "VARCHAR" .
                """,
            }
        ],
        validation_scope="all",
    )

    before_drift = db.list_graph_revisions(
        application_status="validation_failed",
        staged_validation_status="failed",
    )

    assert before_drift.include_apply_checks is True
    assert before_drift.application_status == "validation_failed"
    assert before_drift.staged_validation_status == "failed"
    assert [item.iri for item in before_drift.revisions] == [staged.revision_iri]
    assert before_drift.revisions[0].staged_validation_status == "failed"

    db.import_turtle(
        """
        @prefix ex: <https://example.test/project#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:BenignOntologyTerm a rdfs:Class ;
            rdfs:label "Benign ontology term" .
        """,
        graph="ontology",
    )

    live_validation_failed = db.list_graph_revisions(
        application_status="validation_failed",
    )
    stored_validation_failed = db.list_graph_revisions(
        staged_validation_status="failed",
    )
    conflicted_stored_validation_failed = db.list_graph_revisions(
        application_status="conflict",
        staged_validation_status="failed",
    )

    assert live_validation_failed.count == 0
    assert stored_validation_failed.staged_validation_status == "failed"
    assert [item.iri for item in stored_validation_failed.revisions] == [
        staged.revision_iri
    ]
    stored_row = stored_validation_failed.revisions[0]
    assert stored_row.application_status is None
    assert stored_row.validation_conforms is False
    assert stored_row.validation_result_count == 1
    assert stored_row.staged_validation_status == "failed"
    assert conflicted_stored_validation_failed.include_apply_checks is True
    assert [item.iri for item in conflicted_stored_validation_failed.revisions] == [
        staged.revision_iri
    ]
    conflict_row = conflicted_stored_validation_failed.revisions[0]
    assert conflict_row.application_status == "conflict"
    assert conflict_row.stale_resolution_state == "stale_unresolved"
    assert conflict_row.application_validation_skipped_reason == "conflicts_present"
    assert conflict_row.next_action is not None
    assert conflict_row.next_action.action_type == "repair_or_replace"
    assert conflict_row.next_action.queue == "repair_or_replace"
    assert conflict_row.next_action.tool_name == "draft_staged_revision_rebase"

    export = db.export_staged_revisions(
        [staged.revision_iri],
        tmp_path / "validation-after-drift.md",
    )

    assert export.bundle_summary.validation_failed_revision_iris == []
    assert export.bundle_summary.staged_validation_failed_revision_iris == [
        staged.revision_iri
    ]
    assert export.bundle_summary.recommended_repair_review_iris == [
        staged.revision_iri
    ]
    assert export.bundle_summary.next_action_queue == {
        "repair_or_replace": [staged.revision_iri]
    }


def test_stage_graph_revision_rejects_immutable_seed_targets(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(ImmutableGraphError, match="base_ontology"):
        db.stage_graph_revision(
            summary="Invalid staged seed patch",
            rationale="Project-level staged revisions must not target shipped seeds.",
            additions=[
                {
                    "graph": "base_ontology",
                    "content": (
                        "@prefix ex: <https://example.test/> . "
                        "ex:s ex:p ex:o ."
                    ),
                }
            ],
        )


def test_stage_graph_revision_rejects_history_target_without_metadata_write(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    before_history_count = db.triple_count("history")

    with pytest.raises(
        DoxaBaseError,
        match="cannot target 'history'.*record_graph_revision",
    ):
        db.stage_graph_revision(
            summary="Invalid staged history patch",
            rationale="Staged patch metadata is itself written to history.",
            additions=[
                {
                    "graph": "history",
                    "content": (
                        "@prefix ex: <https://example.test/> . "
                        "ex:review ex:note \"Manual review note\" ."
                    ),
                }
            ],
        )

    assert db.triple_count("history") == before_history_count


def test_stage_pattern_promotion_rolls_pattern_support_into_staged_revision(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/ais#"
    mmsi_column = f"{base}broadcasts__mmsi"
    caveat = f"{base}mmsi_operational_identity_caveat"
    observation = db.record_observation(
        "MMSI appears repeatedly as a useful but imperfect grouping key.",
        observed_column=mmsi_column,
        evidence_summary="Synthetic profile note for pattern promotion.",
        evidence_sources=["test://mmsi-profile"],
    )
    claim = db.record_claim_observation(
        summary="MMSI identity caveat.",
        claim_text="MMSI is useful for grouping broadcasts but is not stable vessel identity.",
        claim_kind="rc:CaveatClaim",
        claim_targets=[mmsi_column],
        evidence_sources=["test://mmsi-caveat"],
    )
    pattern = db.record_pattern(
        summary="MMSI is operational identity, not vessel identity.",
        pattern_text=(
            "Repeated checks support treating MMSI as an operational grouping key "
            "with identity caveats."
        ),
        rationale=(
            "The observation and claim agree that MMSI is useful but should not "
            "be promoted as a stable vessel identifier."
        ),
        pattern_targets=[mmsi_column],
        supporting_observations=[observation.observation_iri],
        supporting_claims=[claim.claim_iri],
        evidence_iri=claim.evidence_iri,
        map_implications=[caveat],
        confidence="rc:HighConfidence",
        pattern_stability="rc:RepeatedPattern",
    )
    before_map_count = db.triple_count("map")
    before_ontology_count = db.triple_count("ontology")

    draft = db.stage_pattern_promotion(
        patterns=[pattern.pattern_iri],
        summary="Promote MMSI caveat from pattern",
        intent="Preserve the MMSI hunch as current map caveat plus a project term.",
        rationale=(
            "This is a cautious promotion: the strong pattern becomes a caveat, "
            "not a hard identity-key assertion."
        ),
        shared_additions=[
            {
                "graph": "ontology",
                "content": """
                    @prefix ais: <https://example.test/ais#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ais:OperationalIdentityCaveat a rdfs:Class ;
                        rdfs:subClassOf rc:KnownCaveat ;
                        rdfs:label "Operational identity caveat" .
                """,
            }
        ],
        framings=[
            {
                "label": "Map caveat",
                "graph": "map",
                "content": f"""
                    @prefix ais: <https://example.test/ais#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ais:mmsi_operational_identity_caveat
                        a rc:KnownCaveat, ais:OperationalIdentityCaveat ;
                        rdfs:label "MMSI operational identity caveat" ;
                        rdfs:comment "MMSI can group broadcasts but should not be treated as stable vessel identity." ;
                        rc:caveatDescription "MMSI can group broadcasts but should not be treated as stable vessel identity." ;
                        rc:impact "Identity-level analysis should avoid assuming one MMSI equals one vessel." ;
                        rc:severity rc:Moderate .

                    <{mmsi_column}> rc:hasKnownCaveat ais:mmsi_operational_identity_caveat .
                """,
                "review_note": "Pattern support is strong, but the map change remains staged.",
            }
        ],
        validation_scope="all",
    )

    assert draft.summary == "Promote MMSI caveat from pattern"
    assert draft.intent == (
        "Preserve the MMSI hunch as current map caveat plus a project term."
    )
    assert draft.anchors == [pattern.pattern_iri, mmsi_column, caveat]
    assert draft.framings[0].target_graphs == ["ontology", "map"]
    assert draft.framings[0].validation_conforms is True
    assert db.triple_count("map") == before_map_count
    assert db.triple_count("ontology") == before_ontology_count

    staged = db.describe_staged_revision(draft.staged_revisions[0].revision_iri)
    assert staged.revision_stance == RC + "CandidateRevision"
    assert staged.rationale is not None
    assert "Selected pattern support" in staged.rationale
    assert "Promotion rationale" in staged.rationale
    assert {pattern_summary.iri for pattern_summary in staged.supporting_patterns} == {
        pattern.pattern_iri
    }
    assert {
        observation_summary.iri
        for observation_summary in staged.supporting_observations
    } == {observation.observation_iri}
    assert {claim_summary.iri for claim_summary in staged.supporting_claims} == {
        claim.claim_iri
    }
    assert {evidence_summary.iri for evidence_summary in staged.evidence} == {
        claim.evidence_iri
    }
    assert {anchor.iri for anchor in staged.revision_anchors} == {
        pattern.pattern_iri,
        mmsi_column,
        caveat,
    }


def test_stage_pattern_promotion_keeps_claim_evidence_indirect_unless_passed(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/profile#"
    dataset = f"{base}Orders"
    metric = f"{base}CompletenessRatio"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    claim = db.record_claim_observation(
        summary="Completeness ratio was reviewed.",
        claim_text=(
            "The Orders completeness ratio is meaningful only after excluding "
            "synthetic heartbeat rows."
        ),
        claim_kind="rc:MetricClaim",
        claim_targets=[metric],
        evidence_sources=["test://orders-completeness-review"],
    )
    assert claim.evidence_iri is not None
    pattern = db.record_pattern(
        summary="Completeness ratio needs project vocabulary.",
        pattern_text=(
            "Orders profiles reuse a completeness ratio with project-specific "
            "denominator semantics."
        ),
        rationale="The supporting claim carries the source evidence.",
        pattern_targets=[dataset],
        supporting_claims=[claim.claim_iri],
        map_implications=[metric],
    )
    framing = {
        "label": "Metric vocabulary",
        "graph": "ontology",
        "content": f"""
            @prefix rc: <https://richcanopy.org/ns/rc#> .
            @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

            <{metric}> a rc:ProfileMetricKind ;
                rdfs:label "Completeness ratio" .
        """,
    }

    indirect = db.stage_pattern_promotion(
        patterns=[pattern.pattern_iri],
        summary="Promote metric without direct evidence",
        intent="Show that claim evidence stays indirect unless selected.",
        framings=[framing],
        validation_scope="all",
    )

    indirect_staged = db.describe_staged_revision(
        indirect.staged_revisions[0].revision_iri
    )
    assert {item.iri for item in indirect_staged.supporting_claims} == {
        claim.claim_iri
    }
    assert indirect_staged.evidence == []

    explicit = db.stage_pattern_promotion(
        patterns=[pattern.pattern_iri],
        summary="Promote metric with explicit evidence",
        intent="Show how callers promote claim evidence into direct revision evidence.",
        framings=[framing],
        evidence=[claim.evidence_iri],
        validation_scope="all",
    )

    explicit_staged = db.describe_staged_revision(
        explicit.staged_revisions[0].revision_iri
    )
    assert {item.iri for item in explicit_staged.supporting_claims} == {
        claim.claim_iri
    }
    assert {item.iri for item in explicit_staged.evidence} == {claim.evidence_iri}


def test_stage_pattern_promotion_mixed_alternatives_group_review_queues(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    base = "https://example.test/awkward-temporal#"
    ft = "https://example.test/awkward-temporal/systematisation#"
    dataset = f"{base}dispatch_events"
    clock = f"{base}dispatch_events__event_local_time"
    timezone = f"{base}dispatch_events__source_timezone_hint"
    normalized = f"{base}dispatch_events__event_utc"
    partition = f"{base}dispatch_events__ingest_partition_date"
    temporal_scope = f"{ft}dispatch_event_temporal_scope_v1"
    caveat = f"{ft}temporal_interpretation_caveat"
    observation = db.record_observation(
        "Raw local clock text is not an event instant.",
        observed_column=clock,
        evidence_summary=(
            "Synthetic temporal sample mixed offset-bearing, naive, and "
            "placeholder local clock values."
        ),
        evidence_sources=["test://awkward-temporal-profile"],
    )
    claim = db.record_claim_observation(
        summary="Temporal interpretation needs timezone evidence.",
        claim_text=(
            "event_local_time should be preserved as source-local text unless "
            "source_timezone_hint can support event_utc normalization."
        ),
        claim_kind="rc:SchemaClaim",
        claim_targets=[clock, timezone, normalized],
        evidence_sources=["test://awkward-temporal-claim"],
    )
    pattern = db.record_pattern(
        summary="Temporal meaning spans raw clock, timezone hint, and UTC.",
        pattern_text=(
            "Dispatch event time cannot be represented as a simple column "
            "helper fact: raw local clock text, timezone evidence, nullable "
            "normalized UTC, and ingest partition date each carry different "
            "semantics."
        ),
        rationale=(
            "A durable model needs an explicit interpretation scope or a "
            "pattern-level caveat, not just a changed physical type."
        ),
        pattern_targets=[dataset, clock, timezone, normalized, partition],
        supporting_observations=[observation.observation_iri],
        supporting_claims=[claim.claim_iri],
        evidence_iri=claim.evidence_iri,
        map_implications=[temporal_scope, caveat],
    )
    shared_ontology = """
    @prefix ft: <https://example.test/awkward-temporal/systematisation#> .
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ft:TemporalInterpretationScope a rdfs:Class ;
        rdfs:label "Temporal interpretation scope" .

    ft:TemporalInterpretationPattern a rdfs:Class ;
        rdfs:subClassOf rc:Pattern ;
        rdfs:label "Temporal interpretation pattern" .

    ft:clockColumn a rdf:Property ;
        rdfs:label "clock column" .

    ft:timezoneEvidenceColumn a rdf:Property ;
        rdfs:label "timezone evidence column" .

    ft:normalizedInstantColumn a rdf:Property ;
        rdfs:label "normalized instant column" .

    ft:partitionColumn a rdf:Property ;
        rdfs:label "partition column" .
    """
    shared_shape = """
    @prefix ft: <https://example.test/awkward-temporal/systematisation#> .
    @prefix sh: <http://www.w3.org/ns/shacl#> .

    ft:TemporalInterpretationScopeShape a sh:NodeShape ;
        sh:targetClass ft:TemporalInterpretationScope ;
        sh:property [
            sh:path ft:timezoneEvidenceColumn ;
            sh:minCount 1 ;
            sh:nodeKind sh:IRI ;
            sh:message "Temporal scopes must name the timezone evidence column."
        ] .
    """
    incomplete_map_framing = f"""
    @prefix ft: <https://example.test/awkward-temporal/systematisation#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    <{dataset}> a rc:Dataset ;
        rdfs:label "Dispatch Events" ;
        rc:hasKnownCaveat <{caveat}> .

    <{caveat}> a rc:KnownCaveat ;
        rdfs:label "Temporal interpretation caveat" ;
        rc:caveatDescription "Raw event time, timezone hints, UTC, and partition dates are related but not interchangeable." .

    <{temporal_scope}> a ft:TemporalInterpretationScope ;
        rdfs:label "Dispatch event temporal scope" ;
        ft:clockColumn <{clock}> ;
        ft:normalizedInstantColumn <{normalized}> ;
        ft:partitionColumn <{partition}> .
    """
    repaired_map_framing = f"""
    @prefix ft: <https://example.test/awkward-temporal/systematisation#> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    <{dataset}> a rc:Dataset ;
        rdfs:label "Dispatch Events" ;
        rc:hasKnownCaveat <{caveat}> .

    <{caveat}> a rc:KnownCaveat ;
        rdfs:label "Temporal interpretation caveat" ;
        rc:caveatDescription "Raw event time, timezone hints, UTC, and partition dates are related but not interchangeable." .

    <{temporal_scope}> a ft:TemporalInterpretationScope ;
        rdfs:label "Dispatch event temporal scope" ;
        ft:clockColumn <{clock}> ;
        ft:timezoneEvidenceColumn <{timezone}> ;
        ft:normalizedInstantColumn <{normalized}> ;
        ft:partitionColumn <{partition}> .
    """
    pattern_first_framing = f"""
    @prefix ft: <https://example.test/awkward-temporal/systematisation#> .
    @prefix dcterms: <http://purl.org/dc/terms/> .
    @prefix rc: <https://richcanopy.org/ns/rc#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

    ft:temporal_interpretation_pattern
        a rc:Pattern, ft:TemporalInterpretationPattern ;
        rdfs:label "Temporal interpretation pattern" ;
        rc:summary "Temporal meaning spans raw clock, timezone hint, and UTC." ;
        rc:patternText "Preserve the cross-column temporal judgement without promoting a current-best map scope yet." ;
        rc:rationale "The pattern framing keeps the semantic caveat visible while map vocabulary is still settling." ;
        rc:patternTarget <{clock}>, <{timezone}>, <{normalized}>, <{partition}> ;
        rc:evidence ft:temporal_interpretation_evidence ;
        rc:patternStability rc:EmergingPattern .

    ft:temporal_interpretation_evidence a rc:Evidence ;
        rc:summary "Synthetic support for the temporal interpretation pattern." ;
        dcterms:source "tests/test_doxabase_core.py" .
    """

    draft = db.stage_pattern_promotion(
        patterns=[pattern.pattern_iri],
        summary="Promote temporal interpretation alternatives",
        intent=(
            "Stage alternative RDF framings for temporal semantics that do not "
            "fit a simple dataset or column map helper."
        ),
        shared_additions=[
            {"graph": "ontology", "content": shared_ontology},
            {"graph": "shapes", "content": shared_shape},
        ],
        framings=[
            {
                "label": "Incomplete map scope without timezone evidence",
                "graph": "map",
                "content": incomplete_map_framing,
                "review_note": (
                    "Intentionally omits timezoneEvidenceColumn so validation "
                    "can show the missing semantic dependency."
                ),
                "review_recommendation": (
                    "Do not apply; use this as the repair diagnostic."
                ),
            },
            {
                "label": "Repaired map scope with timezone evidence",
                "graph": "map",
                "content": repaired_map_framing,
                "review_recommendation": (
                    "Ready after semantic review; compare with the "
                    "pattern-first alternative."
                ),
            },
            {
                "label": "Pattern-first temporal lore",
                "graph": "patterns",
                "content": pattern_first_framing,
                "stance": "rc:AlternativeSystematisation",
                "review_recommendation": (
                    "Keep as the primary handoff unless more datasets confirm "
                    "the scope model."
                ),
            },
        ],
        validation_scope="all",
    )

    revision_iris = [revision.revision_iri for revision in draft.staged_revisions]
    assert draft.result_kind == "systematisation_draft"
    assert [framing.validation_conforms for framing in draft.framings] == [
        False,
        True,
        True,
    ]
    assert [framing.validation_result_count for framing in draft.framings] == [
        1,
        0,
        0,
    ]
    assert draft.next_action_queue == {
        "repair_or_replace": [revision_iris[0]],
        "apply_after_review": [revision_iris[1], revision_iris[2]],
    }
    assert draft.next_action_queue_item_counts == {
        "repair_or_replace": 1,
        "apply_after_review": 2,
    }
    assert draft.semantic_review_required_queue_counts == {}
    assert [
        item.application_status for item in draft.next_action_queue_items
    ] == [
        "validation_failed",
        "ready",
        "ready",
    ]
    assert any(
        "First framing 'Incomplete map scope without timezone evidence'" in warning
        and "failed staged validation" in warning
        and revision_iris[0] in warning
        and "link_alternatives=False" in warning
        for warning in draft.warnings
    )
    assert [
        warning.warning_code for warning in draft.structured_warnings
    ] == [
        "shared_semantic_context_applies_to_all_framings",
        "first_alternative_anchor_not_ready",
    ]
    shared_warning = draft.structured_warnings[0]
    assert shared_warning.message in draft.warnings
    assert shared_warning.affected_revision_iris == revision_iris
    assert (
        shared_warning.suggested_action
        == "rerun_with_shared_semantic_context_moved_to_framings"
    )
    assert shared_warning.suggested_rerun_arguments == {
        "move_shared_patch_graphs_into_framing_patches": ["ontology", "shapes"],
        "shared_patch_sources_to_move": [
            {
                "source_argument": "shared_additions",
                "source_index": 0,
                "operation": "addition",
                "graph": "ontology",
            },
            {
                "source_argument": "shared_additions",
                "source_index": 1,
                "operation": "addition",
                "graph": "shapes",
            },
        ],
        "target_framing_selection_required": True,
        "target_framing_selection_note": (
            "Choose which framings should receive the moved ontology/shapes "
            "patches. fallback_revision_iris_with_shared_semantic_context is "
            "an inspection subset of later framings currently carrying shared "
            "context, not an automatic drop list."
        ),
    }
    assert (
        shared_warning.fallback_revision_iris_with_shared_semantic_context
        == revision_iris[1:]
    )
    assert [
        (summary.target_graph, summary.triple_count, summary.count_basis)
        for summary in shared_warning.shared_patch_summaries
    ] == [
        ("ontology", 13, "target_graph_plus_base_ontology"),
        ("shapes", 7, "target_graph_plus_base_shapes"),
    ]
    assert all(
        summary.operation == RC + "AdditionPatch"
        and summary.operation_label == "addition patch"
        and summary.patch_role == RC + "SharedContextPatch"
        and summary.patch_role_label == "shared context patch"
        and summary.format == "turtle"
        for summary in shared_warning.shared_patch_summaries
    )
    structured_warning = draft.structured_warnings[1]
    assert structured_warning.warning_code == "first_alternative_anchor_not_ready"
    assert structured_warning.message in draft.warnings
    assert structured_warning.affected_revision_iris == revision_iris
    assert (
        structured_warning.suggested_action
        == "rerun_with_explicit_alternative_routing"
    )
    assert structured_warning.suggested_rerun_arguments == {
        "link_alternatives": False
    }
    rerun_action = draft.suggested_next_actions[0]
    assert rerun_action.tool == "doxabase.stage_systematisation"
    assert rerun_action.args["summary"] == (
        "Promote temporal interpretation alternatives"
    )
    assert rerun_action.args["intent"] == (
        "Stage alternative RDF framings for temporal semantics that do not "
        "fit a simple dataset or column map helper."
    )
    assert rerun_action.args["link_alternatives"] is False
    assert rerun_action.args["shared_additions"] == [
        {"graph": "ontology", "content": shared_ontology},
        {"graph": "shapes", "content": shared_shape},
    ]
    assert [framing["label"] for framing in rerun_action.args["framings"]] == [
        "Incomplete map scope without timezone evidence",
        "Repaired map scope with timezone evidence",
        "Pattern-first temporal lore",
    ]
    assert "link_alternatives=False" in rerun_action.reason
    export_action = draft.suggested_next_actions[1]
    assert export_action.tool == "doxabase.export_staged_revisions"
    assert export_action.args["revision_iris"] == revision_iris
    assert export_action.args["path"].startswith(
        "/tmp/systematisation-review-"
    )
    assert export_action.args["path"].endswith(".md")
    assert [
        action.args
        for action in draft.suggested_next_actions
        if action.tool == "doxabase.check_staged_revision_apply"
    ] == [{"iri": revision_iri} for revision_iri in revision_iris]
    export_path = tmp_path / "temporal-interpretation-review.md"
    export = db.export_staged_revisions(
        revision_iris,
        export_path,
        title="Temporal interpretation alternatives",
    )
    exported = export_path.read_text(encoding="utf-8")

    assert export.bundle_summary.next_action_queue == {
        "repair_or_replace": [revision_iris[0]],
        "apply_after_review": [revision_iris[1], revision_iris[2]],
    }
    assert export.bundle_summary.semantic_risk_queue_counts == {
        "repair_or_replace": 1,
        "apply_after_review": 2,
    }
    assert export.bundle_summary.semantic_review_required_queue_counts == {}
    assert export.bundle_summary.shared_context_graphs == ["ontology", "shapes"]
    assert (
        export.bundle_summary.fallback_revision_iris_with_shared_semantic_context
        == revision_iris[1:]
    )
    assert [
        (summary.target_graph, summary.triple_count, summary.count_basis)
        for summary in export.bundle_summary.shared_context_patch_summaries
    ] == [
        ("ontology", 13, "target_graph_plus_base_ontology"),
        ("shapes", 7, "target_graph_plus_base_shapes"),
    ]
    assert len(export.bundle_summary.shared_semantic_context_warnings) == 1
    bundle_shared_warning = export.bundle_summary.shared_semantic_context_warnings[0]
    assert bundle_shared_warning.warning_code == (
        "shared_semantic_context_applies_to_all_framings"
    )
    assert bundle_shared_warning.affected_revision_iris == revision_iris
    assert bundle_shared_warning.shared_context_graphs == ["ontology", "shapes"]
    assert (
        bundle_shared_warning.fallback_revision_iris_with_shared_semantic_context
        == revision_iris[1:]
    )
    assert any(
        "Shared ontology or shapes context patches are present across this staged bundle"
        in warning
        for warning in export.bundle_summary.warnings
    )
    assert export.bundle_summary.recommended_repair_review_iris == [
        revision_iris[0]
    ]
    assert export.bundle_summary.recommended_apply_or_restage_review_iris == [
        revision_iris[1],
        revision_iris[2],
    ]
    assert export.bundle_summary.modelling_choice_summary is not None
    assert "repair_diagnostic: 1" in export.bundle_summary.modelling_choice_summary
    assert "map_candidate: 1" in export.bundle_summary.modelling_choice_summary
    assert (
        "pattern_first_alternative: 1"
        in export.bundle_summary.modelling_choice_summary
    )
    assert [
        row.modelling_role
        for row in export.bundle_summary.modelling_choice_rows
    ] == [
        "repair_diagnostic",
        "map_candidate",
        "pattern_first_alternative",
    ]
    assert [
        row.queue for row in export.bundle_summary.modelling_choice_rows
    ] == [
        "repair_or_replace",
        "apply_after_review",
        "apply_after_review",
    ]
    assert [
        row.shared_context_graphs
        for row in export.bundle_summary.modelling_choice_rows
    ] == [["ontology", "shapes"], ["ontology", "shapes"], ["ontology", "shapes"]]
    assert all(
        row.shared_context_applies
        for row in export.bundle_summary.modelling_choice_rows
    )
    assert [
        row.support_counts["patterns"]
        for row in export.bundle_summary.modelling_choice_rows
    ] == [1, 1, 1]
    assert [summary.apply_status for summary in export.revision_summaries] == [
        "validation_failed",
        "ready",
        "ready",
    ]
    assert [
        summary.semantic_risk_level for summary in export.revision_summaries
    ] == [
        "attention",
        "attention",
        "attention",
    ]
    assert [
        summary.shared_context_patch_count for summary in export.revision_summaries
    ] == [2, 2, 2]
    assert [
        summary.shared_context_graphs for summary in export.revision_summaries
    ] == [["ontology", "shapes"], ["ontology", "shapes"], ["ontology", "shapes"]]
    assert [
        item.semantic_risk_level
        for item in export.bundle_summary.next_action_queue_items
    ] == [
        "attention",
        "attention",
        "attention",
    ]
    assert all(
        summary.semantic_risk_reasons for summary in export.revision_summaries
    )
    assert "## Modelling Choice Summary" in exported
    assert "repair_diagnostic" in exported
    assert "pattern_first_alternative" in exported
    assert "Shared ontology/shapes context applies to 3 row(s)" in exported
    assert "## Review Queues" in exported
    assert "Shared ontology or shapes context patches are present" in exported
    assert (
        "- Next action - apply after review: "
        f"`{revision_iris[1]}`, `{revision_iris[2]}`"
    ) in exported
    assert (
        f"- Next action - repair or replace: `{revision_iris[0]}`"
    ) in exported
    assert f"- Repair review: `{revision_iris[0]}`" in exported
    assert "Temporal scopes must name the timezone evidence column." in exported


def test_stage_query_physical_layout_repair_rejects_existing_layout_by_default(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#WarehouseOrders"
    existing_layout = db.record_map_physical_layout(
        "https://example.test/project#warehouse_orders_existing_layout",
        file_format="rc:PostgreSQLTable",
        datasets=[dataset],
    )
    db.record_map_dataset(
        dataset,
        label="Warehouse orders",
        is_table=True,
        physical_layouts=[existing_layout.iri],
    )

    with pytest.raises(DoxaBaseError, match="missing_physical_layout"):
        db.stage_query_physical_layout_repair(
            dataset_iri=dataset,
            layout_iri="https://example.test/project#warehouse_orders_new_layout",
            file_format="rc:PostgreSQLTable",
            rationale="Reviewed an alternate warehouse relation layout.",
        )

    staged = db.stage_query_physical_layout_repair(
        dataset_iri=dataset,
        layout_iri="https://example.test/project#warehouse_orders_new_layout",
        file_format="rc:PostgreSQLTable",
        rationale="Reviewed an alternate warehouse relation layout.",
        allow_existing_physical_layouts=True,
    )

    assert staged.validation_conforms is True


def test_stage_query_storage_access_repair_unblocks_missing_storage(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Messages"
    storage_access = "https://example.test/project#messages_storage"
    db.record_map_dataset(
        dataset,
        label="Messages",
        is_table=True,
        path_templates=["messages/current/*.jsonl"],
    )

    before = db.describe_query_context(dataset)
    assert "missing_storage_access" in {issue.code for issue in before.issues}

    staged = db.stage_query_storage_access_repair(
        dataset_iri=dataset,
        storage_access_iri=storage_access,
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(tmp_path / "warehouse"),
        rationale="Reviewed the local warehouse route for Messages.",
        route_roles=["rc:CurrentRoute"],
        location_kind="directory",
        path_templates=["messages/current/*.jsonl"],
        layout_verification_status="rc:VerifiedByListingLayout",
        layout_verification_note="Reviewed from local warehouse listing.",
    )

    assert staged.validation_conforms is True
    assert db.check_staged_revision_apply(staged.revision_iri).status == "ready"
    db.apply_staged_revision(staged.revision_iri)

    repaired = db.describe_query_context(dataset)
    assert "missing_storage_access" not in {issue.code for issue in repaired.issues}
    assert repaired.storage_accesses[0].iri == storage_access
    assert repaired.storage_accesses[0].storage_root == str(tmp_path / "warehouse")
    assert [role.iri for role in repaired.storage_accesses[0].route_roles] == [
        RC + "CurrentRoute"
    ]


def test_stage_query_storage_access_repair_rejects_existing_storage_by_default(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Messages"
    existing_storage = db.record_map_storage_access(
        "https://example.test/project#messages_existing_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(tmp_path / "warehouse"),
        datasets=[dataset],
    )
    db.record_map_dataset(
        dataset,
        label="Messages",
        is_table=True,
        storage_accesses=[existing_storage.iri],
    )

    with pytest.raises(DoxaBaseError, match="missing_storage_access"):
        db.stage_query_storage_access_repair(
            dataset_iri=dataset,
            storage_access_iri="https://example.test/project#messages_new_storage",
            storage_protocol="rc:LocalFilesystemStorage",
            storage_root=str(tmp_path / "warehouse-v2"),
            rationale="Reviewed an alternate storage route.",
        )

    staged = db.stage_query_storage_access_repair(
        dataset_iri=dataset,
        storage_access_iri="https://example.test/project#messages_new_storage",
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(tmp_path / "warehouse-v2"),
        rationale="Reviewed an alternate storage route.",
        allow_existing_storage_accesses=True,
    )

    assert staged.validation_conforms is True


def test_query_evidence_storage_overlay_drafts_reviewed_stage_args(
    tmp_path: Path,
) -> None:
    warehouse = tmp_path / "warehouse"
    warehouse.mkdir()
    csv_path = warehouse / "orders.csv"
    csv_path.write_text(
        "order_id,status,amount_cents\n"
        "1,paid,1200\n"
        "2,pending,800\n"
        "3,paid,3100\n",
        encoding="utf-8",
    )
    query_path = tmp_path / "orders_status.sql"
    query_path.write_text("select count(*) from read_csv_auto(?);\n", encoding="utf-8")
    result_path = tmp_path / "orders_status.result.json"
    result_path.write_text('{"row_count": 3}\n', encoding="utf-8")

    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    dataset = "https://example.test/project#Orders"
    db.record_map_dataset(dataset, label="Orders", is_table=True)
    db.record_map_column(
        "https://example.test/project#orders__status",
        table_iri=dataset,
        column_name="status",
    )
    result = db.record_query_result(
        summary="Orders status query scanned the reviewed local CSV.",
        observed_asset=dataset,
        execution_status="succeeded",
        engine="python-csv",
        query_source_path=str(query_path),
        query_hash="sha256:orders-status",
        result_sources=[str(result_path)],
        scanned_source_paths=[str(csv_path)],
        sample_size=3,
        sample_scope="All rows in the reviewed Orders CSV.",
        sample_method="External read-only aggregate query.",
        row_count=3,
    )
    before_counts = _mutable_graph_counts(db)
    before_context = db.describe_query_context(dataset)

    assert before_context.readiness == "insufficient_metadata"
    assert before_context.query_target_candidates == []
    assert [
        action.tool.removeprefix("doxabase.") for action in before_context.suggested_next_actions
    ] == [
        "describe_profile_run",
        "draft_query_evidence_storage_overlay",
    ]
    assert before_context.safe_inspection_action_indexes == [0]
    assert before_context.first_safe_inspection_action_index == 0
    overlay_action = before_context.suggested_next_actions[1]
    assert overlay_action.args["dataset_iri"] == dataset
    assert overlay_action.args["evidence_iri"] == result.evidence_iri
    assert overlay_action.args["storage_protocol"] == (
        "REVIEWED_STORAGE_PROTOCOL"
    )
    assert "reviewed values" in overlay_action.reason
    local_candidate = next(
        candidate
        for issue in before_context.issues
        if issue.details is not None
        and isinstance(issue.details.get("repair_hint"), dict)
        for candidate in (
            issue.details["repair_hint"].get(
                "evidence_storage_route_candidates"
            )
            or []
        )
    )
    assert local_candidate["candidate_kind"] == "local_path_from_query_evidence"
    assert local_candidate["source_field"] == "scanned_source_paths"
    assert local_candidate["source_value"] == str(csv_path)
    assert local_candidate["storage_protocol"] == "rc:LocalFilesystemStorage"
    assert local_candidate["storage_root"] == str(warehouse)
    assert local_candidate["location_kind"] == "directory"
    assert local_candidate["path_templates"] == ["orders.csv"]
    assert local_candidate["file_format"] == "rc:CSV"
    assert local_candidate[
        "draft_query_evidence_storage_overlay_candidate_arguments"
    ] == {
        "storage_protocol": "rc:LocalFilesystemStorage",
        "storage_root": str(warehouse),
        "location_kind": "directory",
        "path_templates": ["orders.csv"],
        "file_format": "rc:CSV",
    }

    draft = db.draft_query_evidence_storage_overlay(
        dataset,
        result.evidence_iri,
        storage_protocol="rc:LocalFilesystemStorage",
        storage_root=str(warehouse),
        location_kind="directory",
        storage_label="Reviewed Orders storage route",
        physical_layout_label="Reviewed Orders CSV layout",
        route_roles=["rc:CurrentRoute"],
        path_templates=["orders.csv"],
        file_format="rc:CSV",
        layout_verification_note=(
            "Reviewed query-result evidence scanned warehouse/orders.csv."
        ),
    )

    assert _mutable_graph_counts(db) == before_counts
    assert draft.result_kind == "query_evidence_storage_overlay_draft"
    assert draft.mode == "non_mutating_stage_arguments"
    assert draft.source_profile_evidence["execution_status"] == "succeeded"
    assert draft.source_profile_evidence["query_hash"] == "sha256:orders-status"
    assert draft.source_profile_evidence["result_sources"] == [str(result_path)]
    assert draft.source_profile_evidence["query_source_paths"] == [str(query_path)]
    assert draft.source_profile_evidence["scanned_source_paths"] == [str(csv_path)]
    assert draft.source_profile_evidence["scanned_source_handles"] == [str(csv_path)]
    assert draft.reviewed_overlay["storage_access_iri"] == draft.storage_access_iri
    assert draft.reviewed_overlay["physical_layout_iri"] == draft.physical_layout_iri
    assert draft.reviewed_overlay["storage_label"] == "Reviewed Orders storage route"
    assert draft.reviewed_overlay["physical_layout_label"] == (
        "Reviewed Orders CSV layout"
    )
    assert draft.reviewed_overlay["storage_root"] == str(warehouse)
    assert draft.reviewed_overlay["route_roles"] == [RC + "CurrentRoute"]
    assert draft.reviewed_overlay["access_mode"] == RC + "ReadOnlyAccess"
    assert draft.reviewed_overlay["location_kind"] == "directory"
    assert draft.reviewed_overlay["endpoint_profile"] is None
    assert draft.reviewed_overlay["bucket_name"] is None
    assert draft.reviewed_overlay["key_prefix"] is None
    assert draft.reviewed_overlay["region"] is None
    assert draft.reviewed_overlay["path_style_access"] is None
    assert draft.reviewed_overlay["credential_reference"] is None
    assert draft.reviewed_overlay["path_templates"] == ["orders.csv"]
    assert draft.reviewed_overlay["file_format"] == RC + "CSV"
    assert draft.reviewed_overlay["layout_verification_status"] == (
        RC + "VerifiedByQueryLayout"
    )
    assert draft.validation_conforms is True
    assert draft.changed_graphs == ["map"]
    assert draft.stage_arguments["supporting_observations"] == [
        result.observation_iri
    ]
    assert draft.stage_arguments["evidence"] == [result.evidence_iri]
    assert draft.suggested_next_actions[0].tool == "doxabase.stage_graph_revision"
    assert draft.suggested_next_actions[0].args == draft.stage_arguments

    staged = db.stage_graph_revision(**draft.stage_arguments)
    assert staged.validation_conforms is True
    check = db.check_staged_revision_apply(staged.revision_iri)
    assert check.status == "ready"
    applied = db.apply_staged_revision(staged.revision_iri)
    assert applied.patches_applied == 1

    repaired_context = db.describe_query_context(dataset)
    assert repaired_context.readiness == "ready_for_query_planning"
    plan = db.draft_query_plan(dataset)
    assert plan.handoff_kind == "execution_attempt_ready"
    assert plan.scan.function == "read_csv_auto"
    assert plan.scan.uri_template == str(csv_path)
    assert plan.review_gate.ready_for_execution_attempt is True
    assert db.validate_graph(scope="all").conforms


def test_database_relation_repair_hint_templates_stage_and_apply(
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

    issue = next(
        issue
        for issue in db.describe_query_context(dataset).issues
        if issue.code == "database_relation_template_source_mismatch"
    )
    assert issue.details is not None
    add_action, _ = issue.details["repair_hint"]["actions"]

    assert add_action["required_extra_arguments"] == ["object", "rationale"]
    assert add_action["placeholder_fields"] == ["object"]
    assert add_action["reviewed_value_fields"] == ["object"]
    add_arguments = dict(add_action["arguments_template"])
    add_arguments["object"] = "mart.events"
    add_arguments["rationale"] = "Reviewed mart.events as the database relation."
    add_revision = db.stage_map_assertion_change(**add_arguments)
    assert db.check_staged_revision_apply(add_revision.revision_iri).status == "ready"

    pending_context = db.describe_query_context(dataset)
    pending_group = next(
        group
        for group in pending_context.suggested_repair_action_groups
        if group.issue_code == "database_relation_template_source_mismatch"
    )
    pending_action_by_type = {
        action["action_type"]: action for action in pending_group.actions
    }
    assert pending_group.action_status_counts == {
        "already_pending": 1,
        "pending_review": 1,
    }
    assert pending_group.pending_action_count == 1
    assert pending_group.skippable_action_count == 1
    assert pending_group.pending_required_extra_arguments == ["rationale"]
    assert [
        option["action_type"] for option in pending_group.pending_action_options
    ] == ["remove_misplaced_source_template"]
    pending_remove_option = pending_group.pending_action_options[0]
    assert pending_remove_option["source_subject_iri"] == dataset
    assert pending_remove_option["misplaced_template_subject_iri"] == dataset
    assert pending_remove_option["misplaced_template_source"] == "dataset"
    assert pending_remove_option["misplaced_template"] == dataset_template
    pending_add = pending_action_by_type["add_reviewed_relation_template"]
    assert pending_add["action_status"] == "already_pending"
    assert pending_add["skip_when_already_pending"] is True
    assert pending_add["pending_staged_repair_iris"] == [add_revision.revision_iri]

    pending_brief = db.project_brief(limit=3)
    assert any(
        queue.name == "query_repair_review" and queue.count >= 1
        for queue in pending_brief.queues
    )

    db.apply_staged_revision(add_revision.revision_iri)

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

    issue = next(
        issue
        for issue in add_only_context.issues
        if issue.code == "database_relation_template_source_mismatch"
    )
    assert issue.details is not None
    repair_hint = issue.details["repair_hint"]
    assert repair_hint["candidate_relation_identifier"][
        "storage_access_relation_templates"
    ] == ["mart.events"]
    assert repair_hint["actions"][1]["action_status"] == "already_satisfied"
    assert repair_hint["actions"][1][
        "existing_storage_access_relation_templates"
    ] == ["mart.events"]
    remove_action = repair_hint["actions"][0]
    assert remove_action["required_extra_arguments"] == ["rationale"]
    remove_arguments = dict(remove_action["args"])
    remove_arguments["rationale"] = (
        "Reviewed dataset path template as misplaced database relation metadata."
    )
    remove_revision = db.stage_map_assertion_change(**remove_arguments)
    assert db.check_staged_revision_apply(remove_revision.revision_iri).status == (
        "ready"
    )
    db.apply_staged_revision(remove_revision.revision_iri)

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


def test_staged_revision_apply_check_rejects_unmapped_relationship_columns(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    staged = db.stage_graph_revision(
        summary="Stage unrecorded column derivation",
        rationale=(
            "Exercise generic staged validation for relationship column slots "
            "whose objects are only inferred as columns from predicate ranges."
        ),
        additions=[
            {
                "graph": "map",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rc: <https://richcanopy.org/ns/rc#> .

                    ex:messages a rc:Dataset, rc:Table .
                    ex:body_preview_derivation a rc:Derivation ;
                        rc:sourceColumn ex:messages__body ;
                        rc:derivedColumn ex:messages__body_top .
                """,
            }
        ],
        validation_scope="all",
    )

    assert staged.validation_conforms is False
    assert staged.validation_result_count >= 2
    assert any(
        "columnName evidence" in message
        for diagnostic in staged.validation_results
        for message in diagnostic.messages
    )

    check = db.check_staged_revision_apply(staged.revision_iri)

    assert check.can_apply is False
    assert check.status == "validation_failed"
    assert check.decision == "inspect_validation_results"
    assert check.blocking_reasons == ["validation_failed"]
    assert check.validation_conforms is False
    assert check.validation_result_count is not None
    assert check.validation_result_count >= 2
    assert any(
        "columnName evidence" in message
        for diagnostic in check.validation_results
        for message in diagnostic.messages
    )


def test_search_staged_patch_payloads_routes_staged_only_terms(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    term = "https://example.test/project#CohortCompletenessLens"
    staged = db.stage_graph_revision(
        summary="Define cohort completeness lens",
        rationale="The term should remain reviewable before it becomes ontology.",
        additions=[
            {
                "graph": "ontology",
                "content": f"""
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    <{term}> a rdfs:Class ;
                        rdfs:label "Cohort completeness lens" ;
                        rdfs:comment "A staged-only modelling lens." .
                """,
            }
        ],
        validation_scope="all",
    )

    assert db.search("cohort completeness", graph="ontology").matches == []

    results = db.search_staged_patch_payloads("cohort completeness")

    assert results.count == 1
    assert results.returned_count == 1
    match = results.matches[0]
    assert match.revision_iri == staged.revision_iri
    assert match.revision_summary == "Define cohort completeness lens"
    assert match.revision_application_status == "ready"
    assert match.revision_is_current_staged_work is True
    assert match.patch_iri == staged.patches[0].patch_iri
    assert match.target_graph == "ontology"
    assert match.patch_subject_iris == [term]
    assert term in match.parsed_resource_iris
    assert "literal" in match.matched_term_roles
    assert match.parse_error is None
    assert [action.tool.removeprefix("doxabase.") for action in match.suggested_next_actions] == [
        "describe_staged_revision",
        "export_staged_revisions",
        "list_resource_revisions",
    ]
    assert (
        match.suggested_next_actions[1].args["fail_on_sensitive"] is True
    )
    assert results.suggested_next_actions[0].args == {
        "iri": staged.revision_iri,
        "include_current_apply_check": True,
    }

    with pytest.raises(DoxaBaseError) as exc_info:
        db.get_context_graph(term, profile="resource_brief")
    missing_seed_message = str(exc_info.value)
    assert "staged patch payloads" in missing_seed_message
    assert "list_resource_revisions" in missing_seed_message
    assert "include_patch_mentions=True" in missing_seed_message
    assert "search_staged_patch_payloads" in missing_seed_message

    db.apply_staged_revision(staged.revision_iri)

    assert db.search_staged_patch_payloads("cohort completeness").matches == []
    historical = db.search_staged_patch_payloads(
        "cohort completeness",
        current_staged_work_only=False,
    )
    assert historical.count == 1
    assert historical.matches[0].revision_is_current_staged_work is False


def test_export_staged_revision_linked_support_includes_evidence_source_spans(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    query_result = db.record_query_result(
        "Lifecycle query found terminal states in the orders sample.",
        observed_asset="https://example.test/project#Orders",
        engine="duckdb",
        query_source_path="analysis/orders_lifecycle.sql",
        query_source_section="terminal_state_cte",
        start_line=12,
        end_line=20,
        result_sources=["duckdb://orders/lifecycle-sample"],
    )
    staged = db.stage_graph_revision(
        summary="Define lifecycle-state class",
        rationale=(
            "The query result supports preserving lifecycle-state semantics as "
            "project vocabulary before map assertions consume it."
        ),
        additions=[
            {
                "graph": "ontology",
                "content": """
                    @prefix ex: <https://example.test/project#> .
                    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

                    ex:LifecycleState a rdfs:Class ;
                        rdfs:label "Lifecycle state" .
                """,
            }
        ],
        supporting_observations=[query_result.observation_iri],
        evidence=[query_result.evidence_iri],
        validation_scope="all",
    )

    export_path = tmp_path / "lifecycle-state-review.md"
    db.export_staged_revision(staged.revision_iri, export_path)
    export_text = export_path.read_text()

    assert "## Linked Support" in export_text
    assert query_result.evidence_iri in export_text
    assert "Source: `duckdb://orders/lifecycle-sample`" in export_text
    assert "Source span: `analysis/orders_lifecycle.sql`" in export_text
    assert 'section "terminal_state_cte"' in export_text
    assert "lines 12-20" in export_text

