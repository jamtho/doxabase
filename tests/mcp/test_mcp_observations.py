"""Split from test_mcp_tools.py (distillation Phase 2); tests verbatim."""

from tests.mcp.support_mcp import *  # noqa: F401,F403


def test_record_observation_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    result = record_observation_tool(
        db,
        summary="MCP helper wrote a structured observation.",
        observed_by="urn:doxabase:test-agent",
        evidence_summary="Evidence written by the MCP helper test.",
        evidence_sources=["tests/test_mcp_tools.py"],
    )

    assert result["observation_iri"].startswith(
        "https://richcanopy.org/doxabase/generated/observation/"
    )
    assert result["observation_type"] == "observation"
    assert result["evidence_iri"] is not None
    assert result["observation_triples"] > 0
    assert result["evidence_triples"] > 0
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_record_claim_observation_tool_and_resource_context(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    result = record_claim_observation_tool(
        db,
        summary="MCP helper wrote a structured claim observation.",
        claim_text="The embeddings output joins to eml_messages by doc_id.",
        claim_kind="rc:JoinClaim",
        claim_targets=[
            "https://example.test/enron#eml_embeddings_body_top_doc_id",
            "https://example.test/enron#eml_messages_doc_id",
        ],
        evidence_summary="README embeddings section.",
        source_path="/home/james/github.com/jamtho/enron-emails/README.md",
        source_section="Embeddings",
        source_kind="rc:DocumentationSource",
        confidence="rc:HighConfidence",
        observation_status="rc:Checked",
    )
    claims = list_entities_tool(
        db,
        type="rc:Claim",
        graph="observations",
        text="doc_id",
    )
    context = describe_resource_tool(
        db,
        iri=result["claim_iri"],
        graph="observations",
    )

    assert result["claim_iri"] in {claim["iri"] for claim in claims["entities"]}
    assert context["label"] == "The embeddings output joins to eml_messages by doc_id."
    assert any(
        triple["predicate"] == "https://richcanopy.org/ns/rc#claimKind"
        for triple in context["outgoing"]
    )
    assert context["outgoing_total_count"] >= context["outgoing_returned_count"]
    assert context["incoming_total_count"] >= context["incoming_returned_count"]
    assert context["outgoing_offset"] == 0
    assert context["incoming_offset"] == 0
    assert context.get("blank_node_triples", []) == []
    assert context["blank_node_depth_exhausted"] is False
    assert context["blank_node_unvisited_count"] == 0
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_record_claim_reconsideration_tool_returns_json_like_payload(
    tmp_path: Path,
) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    older = record_claim_observation_tool(
        db,
        summary="Initial MMSI identity hunch.",
        claim_text="MMSI can be treated as the stable vessel identity key.",
        claim_kind="rc:InterpretationClaim",
        claim_targets=["https://example.test/ais#mmsi"],
        evidence_sources=["trial setup"],
    )
    newer = record_claim_observation_tool(
        db,
        summary="MMSI caveat check.",
        claim_text="MMSI is an operational grouping key, not proof of vessel identity.",
        claim_kind="rc:CaveatClaim",
        claim_targets=["https://example.test/ais#mmsi"],
        evidence_sources=["retrieved caveat"],
        observation_status="rc:Checked",
    )

    result = record_claim_reconsideration_tool(
        db,
        newer_claim=newer["claim_iri"],
        older_claim=older["claim_iri"],
        relation="weakens",
        rationale="The retrieved caveat makes the first hunch too strong.",
        evidence_sources=["DoxaBase search(\"MMSI vessel\")"],
        source_path="/tmp/doxabase-search-mmsi-vessel.json",
        spec={"source_kind": "rc:DoxaBaseAPISource"},
    )

    assert result["relation"] == "https://richcanopy.org/ns/rc#Weakening"
    assert result["older_claim_status"] == "https://richcanopy.org/ns/rc#Weakened"
    assert result["evidence_iri"] is not None
    assert result["source_span_iri"] is not None
    context = describe_resource_tool(
        db,
        iri=older["claim_iri"],
        graph="observations",
    )
    assert context["claim"]["lifecycle_summary"] == (
        "Current status: weakened. Later claims reconsider this claim: 1 weakening."
    )
    nested_reconsideration = context["claim"]["incoming_reconsiderations"][0]
    assert nested_reconsideration["evidence"][0]["sources"] == [
        'DoxaBase search("MMSI vessel")'
    ]
    assert nested_reconsideration["evidence"][0]["source_spans"][0]["source_path"] == (
        "/tmp/doxabase-search-mmsi-vessel.json"
    )
    assert nested_reconsideration["evidence"][0]["source_spans"][0]["source_kind"] == (
        "https://richcanopy.org/ns/rc#DoxaBaseAPISource"
    )
    assert validate_graph_tool(db, scope="all")["conforms"] is True


def test_record_pattern_tool_returns_json_like_payload(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    claim = record_claim_observation_tool(
        db,
        summary="MCP helper wrote a claim for pattern support.",
        claim_text="The child table joins to the parent table by parent_doc_id.",
        claim_kind="rc:JoinClaim",
        claim_targets=[
            "https://example.test/enron#eml_attachments_parent_doc_id",
            "https://example.test/enron#eml_messages_doc_id",
        ],
        evidence_summary="README attachments section.",
        source_path="/home/james/github.com/jamtho/enron-emails/README.md",
        source_kind="rc:DocumentationSource",
        confidence="rc:HighConfidence",
        observation_status="rc:Checked",
    )

    result = record_pattern_tool(
        db,
        summary="parent_doc_id behaves as the attachment-to-message join.",
        pattern_text="The structured claim and source docs support parent_doc_id as the join from attachments to messages.",
        rationale="The claim names both join columns, and the source span records where the handoff describes the relationship.",
        pattern_targets=["https://example.test/enron#eml_attachments_parent_doc_id"],
        supporting_claims=[claim["claim_iri"]],
        source_path="/home/james/github.com/jamtho/enron-emails/README.md",
        confidence="rc:HighConfidence",
        spec={"source_section": "Attachments", "source_kind": "rc:DocumentationSource", "pattern_status": "rc:Checked", "pattern_stability": "rc:RepeatedPattern"},
    )
    patterns = list_entities_tool(
        db,
        type="rc:Pattern",
        graph="patterns",
        text="attachment-to-message",
    )
    context = describe_resource_tool(
        db,
        iri=result["pattern_iri"],
        graph="patterns",
        aspect="resource",
    )
    pattern_description = describe_resource_tool(
        db, aspect="pattern", iri=result["pattern_iri"]
    )

    assert result["pattern_iri"] in {pattern["iri"] for pattern in patterns["entities"]}
    assert patterns["entities"][0]["label"] == (
        "parent_doc_id behaves as the attachment-to-message join."
    )
    assert context["label"] == "parent_doc_id behaves as the attachment-to-message join."
    assert any(
        triple["predicate"] == "https://richcanopy.org/ns/rc#supportingClaim"
        for triple in context["outgoing"]
    )
    assert pattern_description["summary"] == (
        "parent_doc_id behaves as the attachment-to-message join."
    )
    assert pattern_description["supporting_claims"][0]["claim_text"] == (
        "The child table joins to the parent table by parent_doc_id."
    )
    assert pattern_description["evidence"][0]["source_spans"][0]["source_section"] == (
        "Attachments"
    )
    assert validate_graph_tool(db, scope="all")["conforms"] is True



def test_dispatch_kind_errors_split_required_from_optional(tmp_path: Path) -> None:
    """Targeted errors must say which fields are mandatory, not just valid
    (AIS session 4: an agent could not see that spec.summary was required)."""
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError) as missing_error:
        record_observation_tool(db, kind="claim", spec={})
    message = str(missing_error.value)
    assert "missing required spec field(s)" in message
    assert (
        "required fields for this kind: "
        "['claim_kind', 'claim_targets', 'claim_text', 'summary']"
    ) in message
    assert "optional: [" in message

    with pytest.raises(DoxaBaseError) as unknown_error:
        record_observation_tool(
            db,
            kind="claim",
            summary="A claim with a stray field.",
            spec={"claim_text": "x", "bogus_field": 1},
        )
    message = str(unknown_error.value)
    assert "unknown spec field(s) ['bogus_field']" in message
    assert "required fields for this kind: [" in message
    assert "optional: [" in message


def test_merge_spec_error_marks_all_optional_fields(tmp_path: Path) -> None:
    db = DoxaBase.create(tmp_path / "capsule.sqlite")

    with pytest.raises(DoxaBaseError) as unknown_error:
        record_observation_tool(
            db,
            summary="An observation with a stray spec field.",
            evidence_summary="Evidence.",
            evidence_sources=["tests/mcp/test_mcp_observations.py"],
            spec={"bogus_field": 1},
        )
    message = str(unknown_error.value)
    assert "unknown spec field(s) ['bogus_field']" in message
    assert "valid spec fields (all optional): [" in message


def test_record_observation_claim_merges_flat_observed_column(
    tmp_path: Path,
) -> None:
    """Flat observed_column must reach kind='claim' instead of being
    silently dropped; kinds that reject it must say so."""
    db = DoxaBase.create(tmp_path / "capsule.sqlite")
    column_iri = "https://example.test/enron#eml_messages_doc_id"

    result = record_observation_tool(
        db,
        kind="claim",
        summary="Claim recorded with a flat observed_column.",
        observed_column=column_iri,
        evidence_summary="README join section.",
        evidence_sources=["README.md"],
        spec={
            "claim_text": "doc_id is the join column.",
            "claim_kind": "rc:JoinClaim",
            "claim_targets": [column_iri],
        },
    )
    context = describe_resource_tool(
        db, iri=result["observation_iri"], graph="observations"
    )
    assert any(
        triple["predicate"] == "https://richcanopy.org/ns/rc#observedColumn"
        and triple["object"] == column_iri
        for triple in context["outgoing"]
    )

    with pytest.raises(DoxaBaseError, match=r"unknown spec field\(s\) \['observed_column'\]"):
        record_observation_tool(
            db,
            kind="query_result",
            summary="Query result with an unsupported flat field.",
            observed_column=column_iri,
        )
