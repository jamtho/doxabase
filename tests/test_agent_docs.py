from doxabase.agent_docs import get_agent_doc, list_agent_docs


def test_list_agent_docs_contains_operational_docs() -> None:
    docs = list_agent_docs()
    doc_ids = {doc["id"] for doc in docs}

    assert docs[0]["id"] == "start_here"
    assert doc_ids >= {
        "start_here",
        "overview",
        "graph_roles",
        "working_the_capsule",
        "response_conventions",
        "project_strategy",
        "ontology_primer",
        "mcp_tools",
        "observation_recording",
        "patterns",
        "map_authoring",
        "profiling",
        "analysis_packets",
        "revisions",
        "staged_revisions",
        "systematisation",
        "lexical_search",
        "context_slicing",
        "executable_catalog",
        "query_planning",
        "field_trials",
        "fixture_notes",
    }
    # Retired mega-docs must stay retired (superseded by response_conventions,
    # the generated mcp_tools doc, module docstrings, and the topic docs).
    assert not doc_ids & {
        "response_shapes",
        "api_reference",
        "agent_workflow",
        "observation_rdf",
    }


def test_get_agent_doc_can_truncate_content() -> None:
    doc = get_agent_doc("overview", max_chars=20)

    assert doc["id"] == "overview"
    assert doc["truncated"] is True
    assert len(str(doc["content"])) == 20


def test_start_here_is_a_short_true_on_ramp() -> None:
    doc = get_agent_doc("start_here", max_chars=50_000)
    content = str(doc["content"])

    assert content.count("\n") <= 120
    assert "doxabase.project_brief" in content
    assert "doxabase.search" in content
    assert "doxabase.get_context_graph" in content
    assert "Graph Placement Cheat Sheet" in content
    assert "working_the_capsule" in content
    assert "response_conventions" in content
    # the live spelling of the check step, not the retired tool name
    assert "apply_staged_revision(dry_run=true)" in content
    assert "check_staged_revision_apply" not in content
    assert "record_claim_observation" not in content
    # journal material must not colonize the on-ramp
    assert "2026-" not in content
    assert "pytest" not in content


def test_project_strategy_names_broad_trial_priorities() -> None:
    doc = get_agent_doc("project_strategy", max_chars=50_000)
    content = str(doc["content"])

    assert doc["id"] == "project_strategy"
    assert "SUSPENDED" in content
    assert "project_brief" in content
    assert "staged_conflict_rebase_versions" in content
    assert "profile_metrics_and_joint_writes" in content
    assert "storage_aware_query_planning" in content
    assert "Do not add these priorities to `project_brief`" in content


def test_staged_revisions_doc_teaches_the_live_flow() -> None:
    doc = get_agent_doc("staged_revisions", max_chars=80_000)
    content = str(doc["content"])

    assert "stage_revision" in content
    assert "apply_staged_revision(iri, dry_run=true)" in content
    assert "target_count_drift" in content
    assert "restage_staged_revision" in content
    assert "plan_staged_revision_recovery" in content
    assert "session_iri" in content
    assert 'kind="review_decision"' in content
    # retired tool names must not resurface as MCP guidance
    assert "doxabase.check_staged_revision_apply" not in content
    assert "draft_staged_revision_rebase(" not in content


def test_revisions_doc_includes_handoff_recovery_route() -> None:
    doc = get_agent_doc(
        "revisions",
        section="Snapshot Evidence And Handoffs",
        max_chars=10_000,
    )
    content = str(doc["content"])

    assert doc["selected_section"]["heading"] == "Snapshot Evidence And Handoffs"
    assert 'export_preflight(kind="handoff_bundle")' in content
    assert 'export_bundle(kind="handoff"' in content
    assert 'import_bundle(kind="trig"' in content
    assert 'import_bundle(kind="revision_snapshots"' in content
    assert "history_plus_snapshot_rows" in content
    assert "history_only_count_digest" in content
    assert "snapshot_rows_without_history" in content


def test_storage_docs_distinguish_protocol_from_location_kind() -> None:
    doc = get_agent_doc("executable_catalog", max_chars=80_000)
    content = str(doc["content"])

    assert "local_path" in content
    assert "storage_protocol" in content
    assert "rc:LocalFilesystemStorage" in content
    assert "`object`" in content
    assert "`directory`" in content
    assert "`prefix`" in content
    assert "`connection`" in content
    assert "rc:DatabaseStorage" in content
    assert "path_templates" in content
    assert "relation identifiers" in content
    assert "storage_root" in content
    assert 'location_kind="bucket"' in content
    assert "external:intentionally-unrecorded" in content
    assert "rc:S3CompatibleStorage" in content


def test_map_authoring_doc_states_direct_versus_staged_rule() -> None:
    doc = get_agent_doc("map_authoring", max_chars=80_000)
    content = str(doc["content"])

    assert "record_map_fact` writes directly" in content
    assert "NEW facts" in content
    assert "stage_revision` proposes reviewed CHANGES" in content
    assert "source_columns" in content
    assert "derived_columns" in content
    assert "rc:Deterministic" in content


def test_query_planning_doc_keeps_ais_gap_and_live_names() -> None:
    doc = get_agent_doc("query_planning", max_chars=80_000)
    content = str(doc["content"])

    assert "plan_candidate" in content
    assert "ais:DailyIndex" in content
    assert "index/*/*.parquet" in content
    assert "ready_for_execution_attempt" in content
    assert 'kind="query_storage_access_repair"' in content
    assert 'kind="query_evidence_overlay"' in content
    # the standalone drafting tool is Python-only now
    assert "doxabase.draft_query_plan" not in content


def test_profiling_doc_routes_through_stage_revision() -> None:
    doc = get_agent_doc("profiling", max_chars=80_000)
    content = str(doc["content"])

    assert "record_profile" in content
    assert 'aspect="profile_run"' in content
    assert 'kind="profile_map_updates"' in content
    assert "dry_run=true" in content
    assert "accepted_recommendation_indexes" in content
    assert 'kind="profile_insight_review"' in content
    assert "sample_scope" in content


def test_analysis_packet_doc_names_the_packet_kind_and_cli() -> None:
    doc = get_agent_doc("analysis_packets", max_chars=20_000)
    content = str(doc["content"])

    assert 'record_map_fact(kind="analysis_packet")' in content
    assert "query_recipes" in content
    assert "analysis_views" in content
    assert "Markdown sidecars remain locator evidence" in content
    assert "--init-manifest" in content
    assert "--sidecar-dir" in content


def test_systematisation_doc_names_core_workflow() -> None:
    doc = get_agent_doc("systematisation", max_chars=20_000)
    content = str(doc["content"])

    assert 'kind="systematisation"' in content
    assert 'kind="pattern_promotion"' in content
    assert "shared_additions" in content
    assert "alternative_to" in content
    assert "link_alternatives" in content


def test_observation_recording_doc_covers_all_kinds_and_rdf_lane() -> None:
    doc = get_agent_doc("observation_recording", max_chars=80_000)
    content = str(doc["content"])

    assert 'kind="claim"' in content
    assert 'kind="query_result"' in content
    assert "record_claim_reconsideration" in content
    assert "rc:SourceSpan" in content
    assert "rcg:observations" in content  # hand-authored RDF lane folded in
    assert 'import_bundle(kind="trig")' in content
