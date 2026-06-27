from doxabase.agent_docs import get_agent_doc, list_agent_docs


def test_list_agent_docs_contains_operational_docs() -> None:
    docs = list_agent_docs()
    doc_ids = {doc["id"] for doc in docs}

    assert docs[0]["id"] == "start_here"
    assert "start_here" in doc_ids
    assert "overview" in doc_ids
    assert "graph_roles" in doc_ids
    assert "agent_workflow" in doc_ids
    assert "mcp_tools" in doc_ids
    assert "response_shapes" in doc_ids
    assert "observation_recording" in doc_ids
    assert "observation_rdf" in doc_ids
    assert "patterns" in doc_ids
    assert "map_authoring" in doc_ids
    assert "revisions" in doc_ids
    assert "staged_revisions" in doc_ids
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
