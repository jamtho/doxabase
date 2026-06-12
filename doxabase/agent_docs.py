from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs" / "agent"


@dataclass(frozen=True)
class AgentDoc:
    id: str
    title: str
    description: str
    path: Path


DOCS: tuple[AgentDoc, ...] = (
    AgentDoc(
        id="start_here",
        title="Start Here",
        description="Cold-start and post-compaction route for agents.",
        path=DOCS_DIR / "start-here.md",
    ),
    AgentDoc(
        id="overview",
        title="DoxaBase Agent Overview",
        description="High-level purpose, current implementation status, and V1 limits.",
        path=DOCS_DIR / "overview.md",
    ),
    AgentDoc(
        id="graph_roles",
        title="Graph Roles",
        description="Where ontology, map, observations, evidence, shapes, and history facts belong.",
        path=DOCS_DIR / "graph-roles.md",
    ),
    AgentDoc(
        id="agent_workflow",
        title="Agent Workflow",
        description="Recommended first calls and graph placement rules for agents.",
        path=DOCS_DIR / "workflow.md",
    ),
    AgentDoc(
        id="ontology_primer",
        title="Ontology Primer",
        description="How to use rc: terms while keeping project-specific terms in project namespaces.",
        path=DOCS_DIR / "ontology-primer.md",
    ),
    AgentDoc(
        id="mcp_tools",
        title="MCP Tools",
        description="Available MCP tools and expected use.",
        path=DOCS_DIR / "mcp-tools.md",
    ),
    AgentDoc(
        id="response_shapes",
        title="Response Shape Examples",
        description="Common Python and MCP response fields agents need when scripting.",
        path=DOCS_DIR / "response-shapes.md",
    ),
    AgentDoc(
        id="observation_recording",
        title="Observation Recording",
        description="How to record point-in-time findings and linked evidence.",
        path=DOCS_DIR / "observation-recording.md",
    ),
    AgentDoc(
        id="observation_rdf",
        title="Agent-Authored Observation RDF",
        description="How to express nuanced observations, claims, and source spans as RDF.",
        path=DOCS_DIR / "observation-rdf.md",
    ),
    AgentDoc(
        id="patterns",
        title="Patterns",
        description="How to synthesize observations into patterns before systematising map facts.",
        path=DOCS_DIR / "patterns.md",
    ),
    AgentDoc(
        id="map_authoring",
        title="Map Authoring",
        description="How to write current-best dataset, column, caveat, storage, and relationship facts.",
        path=DOCS_DIR / "map-authoring.md",
    ),
    AgentDoc(
        id="revisions",
        title="Revision History",
        description="How to record graph revision metadata and review-bundle rationale.",
        path=DOCS_DIR / "revisions.md",
    ),
    AgentDoc(
        id="staged_revisions",
        title="Staged Revisions",
        description="How to propose reviewable graph changes without applying them.",
        path=DOCS_DIR / "staged-revisions.md",
    ),
    AgentDoc(
        id="lexical_search",
        title="Lexical Search",
        description="How search helps agents rediscover claims, caveats, observations, and evidence.",
        path=DOCS_DIR / "lexical-search.md",
    ),
    AgentDoc(
        id="context_slicing",
        title="Context Slicing",
        description="How to request bounded route-explained graph slices around datasets and patterns.",
        path=DOCS_DIR / "context-slicing.md",
    ),
    AgentDoc(
        id="executable_catalog",
        title="Executable Catalog Metadata",
        description="How to model non-secret storage access facts for query planning and handoff.",
        path=DOCS_DIR / "executable-catalog.md",
    ),
    AgentDoc(
        id="field_trials",
        title="Agent Field Trials",
        description="How to run bounded sub-agent trials and turn friction into product signal.",
        path=DOCS_DIR / "field-trials.md",
    ),
    AgentDoc(
        id="api_reference",
        title="API Reference",
        description="Small Python API reference for the current implementation.",
        path=DOCS_DIR / "api-reference.md",
    ),
    AgentDoc(
        id="fixture_notes",
        title="Fixture Notes",
        description="How the Manifest prototype RC fixtures are structured.",
        path=DOCS_DIR / "fixture-notes.md",
    ),
)


def list_agent_docs() -> list[dict[str, str]]:
    return [
        {
            "id": doc.id,
            "title": doc.title,
            "description": doc.description,
        }
        for doc in DOCS
    ]


def get_agent_doc(doc_id: str, *, max_chars: int = 12000) -> dict[str, str | bool | int]:
    doc = _doc_by_id(doc_id)
    text = doc.path.read_text(encoding="utf-8")
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars]
    return {
        "id": doc.id,
        "title": doc.title,
        "description": doc.description,
        "content": text,
        "truncated": truncated,
        "max_chars": max_chars,
    }


def _doc_by_id(doc_id: str) -> AgentDoc:
    for doc in DOCS:
        if doc.id == doc_id:
            return doc
    available = ", ".join(doc.id for doc in DOCS)
    raise KeyError(f"Unknown doc_id '{doc_id}'. Available docs: {available}")
