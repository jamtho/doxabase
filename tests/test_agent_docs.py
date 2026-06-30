from doxabase.agent_docs import get_agent_doc, list_agent_docs


def test_list_agent_docs_contains_operational_docs() -> None:
    docs = list_agent_docs()
    doc_ids = {doc["id"] for doc in docs}

    assert docs[0]["id"] == "start_here"
    assert "start_here" in doc_ids
    assert "overview" in doc_ids
    assert "graph_roles" in doc_ids
    assert "agent_workflow" in doc_ids
    assert "project_strategy" in doc_ids
    assert "mcp_tools" in doc_ids
    assert "response_shapes" in doc_ids
    assert "observation_recording" in doc_ids
    assert "observation_rdf" in doc_ids
    assert "patterns" in doc_ids
    assert "map_authoring" in doc_ids
    assert "profiling" in doc_ids
    assert "revisions" in doc_ids
    assert "staged_revisions" in doc_ids
    assert "systematisation" in doc_ids
    assert "lexical_search" in doc_ids
    assert "context_slicing" in doc_ids
    assert "executable_catalog" in doc_ids
    assert "query_planning" in doc_ids
    assert "field_trials" in doc_ids


def test_get_agent_doc_can_truncate_content() -> None:
    doc = get_agent_doc("overview", max_chars=20)

    assert doc["id"] == "overview"
    assert doc["truncated"] is True
    assert len(str(doc["content"])) == 20


def test_start_here_names_exact_discovery_tools() -> None:
    doc = get_agent_doc("start_here", max_chars=50_000)
    content = str(doc["content"])

    assert "exact discovery" in content
    assert "doxabase.get_doc" in content
    assert "doxabase.list_entities" in content
    assert "doxabase.describe_context_slice" in content
    assert "profiling" in content
    assert "systematisation" in content
    assert "Staged Handoff Recovery Cookbook" in content
    assert "project_strategy" in content


def test_project_strategy_names_broad_trial_priorities() -> None:
    doc = get_agent_doc("project_strategy", max_chars=50_000)
    content = str(doc["content"])

    assert doc["id"] == "project_strategy"
    assert "project_brief" in content
    assert "staged_conflict_rebase_versions" in content
    assert "profile_metrics_and_joint_writes" in content
    assert "storage_aware_query_planning" in content
    assert "Do not add these priorities to `project_brief.queue_counts`" in content


def test_revision_docs_include_handoff_recovery_cookbook() -> None:
    doc = get_agent_doc(
        "revisions",
        section="Staged Handoff Recovery Cookbook",
        max_chars=10_000,
    )
    content = str(doc["content"])

    assert doc["selected_section"]["heading"] == (
        "Staged Handoff Recovery Cookbook"
    )
    assert "export_preflight" in content
    assert "export_handoff_bundle" in content
    assert "export_staged_revisions" in content
    assert "import_trig" in content
    assert "import_revision_snapshots" in content
    assert "describe_revision_snapshot_evidence" in content
    assert "check_staged_revision_apply" in content
    assert "recovery_summary" in content
    assert "history_only_count_digest" in content
    assert "snapshot_rows_without_history" in content
    assert "history_plus_snapshot_rows" in content


def test_storage_access_docs_distinguish_protocol_from_location_kind() -> None:
    for doc_id in ("mcp_tools", "executable_catalog"):
        doc = get_agent_doc(doc_id, max_chars=80_000)
        content = str(doc["content"])

        assert "local_path" in content
        assert "storage_protocol" in content
        assert "rc:LocalFilesystemStorage" in content
        assert '"object"' in content or "`object`" in content
        assert '"directory"' in content or "`directory`" in content
        assert '"prefix"' in content or "`prefix`" in content
        assert '"connection"' in content or "`connection`" in content
        assert "rc:DatabaseStorage" in content
        assert "path_templates" in content
        assert "database relation identifiers" in content
        assert "storage_root" in content


def test_context_slicing_docs_explain_column_owner_query_routing() -> None:
    doc = get_agent_doc("context_slicing", max_chars=50_000)
    content = str(doc["content"])

    assert "mapped column seeds" in content
    assert "owning dataset" in content
    assert "describe_query_context" in content
    assert "owner table" in content


def test_context_slicing_docs_explain_revision_anchor_matches() -> None:
    doc = get_agent_doc("context_slicing", max_chars=50_000)
    content = str(doc["content"])

    assert "revision_anchor_match" in content
    assert "rc:revisionAnchor" in content
    assert "storage access" in content
    assert "physical/query metadata" in content


def test_high_value_sections_are_addressable_for_cold_start() -> None:
    mcp_doc = get_agent_doc(
        "mcp_tools",
        section="doxabase.draft_profile_map_updates",
        max_chars=2_000,
    )
    assert mcp_doc["selected_section"]["heading"] == (
        "doxabase.draft_profile_map_updates"
    )
    assert "profile_map_updates" in str(mcp_doc["content"])

    rebase_mcp_doc = get_agent_doc(
        "mcp_tools",
        section="doxabase.draft_staged_revision_rebase",
        max_chars=2_000,
    )
    assert rebase_mcp_doc["selected_section"]["heading"] == (
        "doxabase.draft_staged_revision_rebase"
    )
    assert "non_executed_review_draft" in str(rebase_mcp_doc["content"])

    recovery_mcp_doc = get_agent_doc(
        "mcp_tools",
        section="doxabase.plan_staged_revision_recovery",
        max_chars=2_000,
    )
    assert recovery_mcp_doc["selected_section"]["heading"] == (
        "doxabase.plan_staged_revision_recovery"
    )
    assert "read-only recovery routes" in str(recovery_mcp_doc["content"])

    profile_run_mcp_doc = get_agent_doc(
        "mcp_tools",
        section="doxabase.describe_profile_run",
        max_chars=2_000,
    )
    assert profile_run_mcp_doc["selected_section"]["heading"] == (
        "doxabase.describe_profile_run"
    )
    assert "profile_run_candidates" in str(profile_run_mcp_doc["content"])

    response_doc = get_agent_doc(
        "response_shapes",
        section="Profile Map Update Drafts",
        max_chars=3_000,
    )
    assert response_doc["selected_section"]["heading"] == (
        "Profile Map Update Drafts"
    )
    assert "draft.recommendations" in str(response_doc["content"])

    rebase_response_doc = get_agent_doc(
        "response_shapes",
        section="Staged Revision Rebase Draft",
        max_chars=4_000,
    )
    assert rebase_response_doc["selected_section"]["heading"] == (
        "Staged Revision Rebase Draft"
    )
    assert "draft.repair_candidates" in str(rebase_response_doc["content"])

    recovery_response_doc = get_agent_doc(
        "response_shapes",
        section="Staged Revision Recovery Plan",
        max_chars=4_000,
    )
    assert recovery_response_doc["selected_section"]["heading"] == (
        "Staged Revision Recovery Plan"
    )
    assert "plan.lanes" in str(recovery_response_doc["content"])

    profile_run_response_doc = get_agent_doc(
        "response_shapes",
        section="Describe Profile Run",
        max_chars=3_000,
    )
    assert profile_run_response_doc["selected_section"]["heading"] == (
        "Describe Profile Run"
    )
    assert "profile_run.returned_profile_count" in str(
        profile_run_response_doc["content"]
    )

    staged_response_doc = get_agent_doc(
        "response_shapes",
        section="Staged Revisions",
        max_chars=4_000,
    )
    assert staged_response_doc["selected_section"]["heading"] == (
        "Staged Revisions"
    )
    assert "systematisation_draft" in str(staged_response_doc["content"])

    query_context_doc = get_agent_doc(
        "response_shapes",
        section="Query Context",
        max_chars=30_000,
    )
    query_context_content = str(query_context_doc["content"])
    assert "repair_hint.actions[].required_extra_arguments" in (
        query_context_content
    )
    assert "query.suggested_repair_action_groups" in query_context_content
    assert "suggested_repair_action_group_count" in query_context_content
    assert "repair_group.repair_hint_path" in query_context_content
    assert "query_repair_review" in query_context_content
    assert "Do not concatenate this lane into `suggested_next_actions`" in (
        query_context_content
    )
    assert "repair_hint.actions[].placeholder_fields" in query_context_content
    assert "repair_hint.actions[].reviewed_value_fields" in query_context_content
    assert "repair_hint.actions[].arguments_template" in query_context_content
    assert "repair_hint.actions[].arguments" in query_context_content
    assert "duplicating it can create equivalent ready query candidates" in (
        query_context_content
    )
    assert "action_status=\"pending_review\"" in query_context_content


def test_profiling_doc_names_core_workflow_tools() -> None:
    doc = get_agent_doc("profiling", max_chars=20_000)
    content = str(doc["content"])

    assert "record_profile_bundle" in content
    assert "describe_profile_run" in content
    assert "draft_profile_map_updates" in content
    assert "plan_profile_followthrough" in content
    assert "stage_profile_map_updates" in content
    assert "profile_type_review" in content
    assert "profile_scalar_conflict_review" in content
    assert "do_not_bulk_apply" in content


def test_systematisation_doc_names_core_workflow_tools() -> None:
    doc = get_agent_doc("systematisation", max_chars=20_000)
    content = str(doc["content"])

    assert "stage_systematisation" in content
    assert "stage_pattern_promotion" in content
    assert "shared_additions" in content
    assert "alternative_to" in content
    assert "next_action_queue" in content
    assert "shared_semantic_context_applies_to_all_framings" in content
    assert 'response_shapes` section "Staged Revisions"' in content
    assert "Systematisation Drafts" not in content
