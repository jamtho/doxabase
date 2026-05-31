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
        id="overview",
        title="DoxyBase Agent Overview",
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
        id="observation_recording",
        title="Observation Recording",
        description="How to record point-in-time findings and linked evidence.",
        path=DOCS_DIR / "observation-recording.md",
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
