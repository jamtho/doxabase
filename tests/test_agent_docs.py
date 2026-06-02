from doxabase.agent_docs import get_agent_doc, list_agent_docs


def test_list_agent_docs_contains_operational_docs() -> None:
    docs = list_agent_docs()
    doc_ids = {doc["id"] for doc in docs}

    assert "overview" in doc_ids
    assert "graph_roles" in doc_ids
    assert "agent_workflow" in doc_ids
    assert "mcp_tools" in doc_ids
    assert "observation_recording" in doc_ids
    assert "observation_rdf" in doc_ids
    assert "patterns" in doc_ids
    assert "map_authoring" in doc_ids
    assert "revisions" in doc_ids
    assert "lexical_search" in doc_ids
    assert "executable_catalog" in doc_ids
    assert "field_trials" in doc_ids


def test_get_agent_doc_can_truncate_content() -> None:
    doc = get_agent_doc("overview", max_chars=20)

    assert doc["id"] == "overview"
    assert doc["truncated"] is True
    assert len(str(doc["content"])) == 20
