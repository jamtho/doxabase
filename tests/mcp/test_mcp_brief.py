"""project_brief MCP envelope tests (ProjectBrief v2: state, not script)."""

from tests.mcp.support_mcp import *  # noqa: F401,F403


def test_project_brief_tool_returns_state_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)

    result = project_brief_tool(db)

    assert set(result).issubset(
        {
            "key_counts",
            "dataset_count",
            "datasets",
            "gates",
            "queues",
            "suggested_next_actions",
            "limit",
        }
    )
    assert result["limit"] == 20
    assert result["dataset_count"] == 7
    assert len(result["datasets"]) == 7
    for dataset in result["datasets"]:
        assert set(dataset).issubset(
            {
                "iri",
                "label",
                "is_table",
                "status",
                "column_count",
                "caveat_count",
            }
        )
        assert dataset["status"]
    # Clean fixture capsule: no gates, so the key is omitted entirely
    # (absent == null == empty).
    assert result.get("gates") is None
    assert result["queues"]
    for queue in result["queues"]:
        assert queue["count"] >= 1
    actions = result["suggested_next_actions"]
    assert 1 <= len(actions) <= 5
    for action in actions:
        assert set(action) == {"tool", "args", "reason"}
        assert action["tool"].startswith("doxabase.")
    assert result == to_dict(db.project_brief(limit=20))


def test_project_brief_tool_respects_limit(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    load_example_fixtures_tool(db)

    result = project_brief_tool(db, limit=3)

    assert result["limit"] == 3
    assert len(result["datasets"]) == 3
    assert result["dataset_count"] == 7


def test_project_brief_tool_serializes_gates_without_secrets(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    fake_secret = "FAKE_SECRET_TOKEN_MCP_BRIEF"
    record_map_dataset_tool(
        db,
        iri="https://example.test/project#CredentialNotes",
        label="Credential notes",
        description=f"Synthetic fixture {fake_secret}.",
    )

    result = project_brief_tool(db)

    gate = next(
        g for g in result["gates"] if g["gate"] == "privacy_export_review"
    )
    assert gate["blocks"] == "export"
    assert gate["detail"]
    assert gate["details_call"] == "doxabase.export_preflight"
    assert fake_secret not in json.dumps(result)
    preflight_action = result["suggested_next_actions"][0]
    assert preflight_action["tool"] == "doxabase.export_preflight"
    assert preflight_action["args"] == {
        "export_kind": "handoff_bundle",
        "graphs": ["project"],
        "limit": 20,
    }
