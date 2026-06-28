from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
        id="profiling",
        title="Profiling Workflows",
        description="How to record profile observations, inspect profile runs, and stage profile-derived map updates.",
        path=DOCS_DIR / "profiling.md",
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
        id="systematisation",
        title="Systematisation Workflows",
        description="How to stage reviewable RDF framings and pattern-supported graph promotions.",
        path=DOCS_DIR / "systematisation.md",
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
        id="query_planning",
        title="Query Planning",
        description="How to read query-context and draft-plan routing fields.",
        path=DOCS_DIR / "query-planning.md",
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


def list_agent_docs() -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for doc in DOCS:
        text = doc.path.read_text(encoding="utf-8")
        docs.append(
            {
                "id": doc.id,
                "title": doc.title,
                "description": doc.description,
                "size_chars": len(text),
                "sections": _doc_sections(text),
            }
        )
    return docs


def get_agent_doc(
    doc_id: str,
    *,
    max_chars: int = 12000,
    start_char: int = 0,
    section: str | None = None,
) -> dict[str, Any]:
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    doc = _doc_by_id(doc_id)
    text = doc.path.read_text(encoding="utf-8")
    sections = _doc_sections(text)
    selected_section: dict[str, Any] | None = None
    readable_end = len(text)
    if section is not None:
        selected_section = _find_doc_section(section, sections)
        start_char = selected_section["start_char"]
        readable_end = selected_section["end_char"]
    start_char = max(0, min(start_char, len(text)))
    if selected_section is None:
        selected_section = _containing_doc_section(start_char, sections)
    end_char = min(readable_end, start_char + max_chars)
    truncated = end_char < readable_end
    return {
        "id": doc.id,
        "title": doc.title,
        "description": doc.description,
        "content": text[start_char:end_char],
        "truncated": truncated,
        "start_char": start_char,
        "end_char": end_char,
        "total_chars": len(text),
        "max_chars": max_chars,
        "selected_section": selected_section,
        "sections": sections,
    }


def _doc_by_id(doc_id: str) -> AgentDoc:
    for doc in DOCS:
        if doc.id == doc_id:
            return doc
    available = ", ".join(doc.id for doc in DOCS)
    raise KeyError(f"Unknown doc_id '{doc_id}'. Available docs: {available}")


def _doc_sections(text: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    slug_counts: dict[str, int] = {}
    in_fence = False
    offset = 0
    for line_number, line in enumerate(text.splitlines(keepends=True), start=1):
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
        if not in_fence:
            match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line.rstrip("\n"))
            if match is not None:
                heading = match.group(2).strip()
                section = {
                    "heading": heading,
                    "level": len(match.group(1)),
                    "anchor": _heading_anchor(heading, slug_counts),
                    "line": line_number,
                    "start_char": offset,
                    "end_char": len(text),
                }
                while (
                    sections
                    and sections[-1]["end_char"] == len(text)
                    and sections[-1]["level"] >= section["level"]
                ):
                    sections[-1]["end_char"] = offset
                sections.append(section)
        offset += len(line)
    return sections


def _heading_anchor(heading: str, slug_counts: dict[str, int]) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")
    base = slug or "section"
    count = slug_counts.get(base, 0)
    slug_counts[base] = count + 1
    if count == 0:
        return base
    return f"{base}-{count}"


def _find_doc_section(
    section: str,
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    needle = section.strip()
    normalized_anchor = re.sub(r"[^a-z0-9]+", "-", needle.lower()).strip("-")
    normalized_heading = needle.lower()
    for item in sections:
        if item["anchor"] == normalized_anchor:
            return item
        if item["heading"].lower() == normalized_heading:
            return item
    available = ", ".join(item["anchor"] for item in sections)
    raise KeyError(f"Unknown section '{section}'. Available sections: {available}")


def _containing_doc_section(
    start_char: int,
    sections: list[dict[str, Any]],
) -> dict[str, Any] | None:
    matches = [
        section
        for section in sections
        if section["start_char"] <= start_char < section["end_char"]
    ]
    if not matches:
        return None
    return max(matches, key=lambda section: section["level"])
