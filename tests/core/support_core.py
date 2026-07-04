"""Shared imports, constants, and helpers for the split test_doxabase_core.py suite."""

import csv

import json

import os

import sqlite3

import warnings

from collections.abc import Callable

from pathlib import Path

import pytest

from rdflib import Dataset, Graph, Literal, URIRef

from rdflib.namespace import DCTERMS, RDF, XSD

from doxabase import (
    DoxaBase,
    DoxaBaseError,
    ImmutableGraphError,
    ProfileInsightReviewCandidate,
    to_dict,
    to_jsonable,
)

from doxabase.core import (
    ProfileScalarConflictRecommendationContext,
    ProjectBriefRecommendedTask,
    RevisionNextActionQueueItem,
)

ROOT = Path(__file__).resolve().parents[2]

AIS_FIXTURE = ROOT / "examples" / "manifest-prototype-rc" / "ais.trig"

POLYMARKET_FIXTURE = ROOT / "examples" / "manifest-prototype-rc" / "polymarket.trig"

RC = "https://richcanopy.org/ns/rc#"

MUTABLE_GRAPHS = (
    "map",
    "ontology",
    "observations",
    "patterns",
    "evidence",
    "shapes",
    "history",
)

def _mutable_graph_counts(db: DoxaBase) -> dict[str, int]:
    return {graph: db.triple_count(graph) for graph in MUTABLE_GRAPHS}

def _line_number_containing(text: str, needle: str) -> int:
    for line_number, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return line_number
    raise AssertionError(f"Expected text to contain {needle!r}")

def _assert_repair_action_option(
    option: dict[str, object],
    *,
    action_index: int,
    action_type: str,
    tool_name: str,
    mcp_tool_name: str,
    action_label: str,
    required_extra_arguments: list[str],
    placeholder_fields: list[str],
    reviewed_value_fields: list[str],
    action_status: str = "pending_review",
) -> None:
    assert option["action_index"] == action_index
    assert option["action_type"] == action_type
    assert option["tool_name"] == tool_name
    assert option["mcp_tool_name"] == mcp_tool_name
    assert option["action_label"] == action_label
    assert option["action_status"] == action_status
    assert option["required_extra_arguments"] == required_extra_arguments
    assert option["placeholder_fields"] == placeholder_fields
    assert option["reviewed_value_fields"] == reviewed_value_fields

def _corrupt_staged_patch_target_graph(
    db: DoxaBase,
    patch_iri: str,
    target_graph: str,
) -> None:
    db._conn.execute(
        """
        UPDATE quads
        SET object = ?
        WHERE graph = 'history'
          AND subject = ?
          AND predicate = ?
        """,
        (target_graph, patch_iri, RC + "targetGraph"),
    )
    db._conn.commit()

def _corrupt_staged_patch_content(
    db: DoxaBase,
    patch_iri: str,
    content: str,
) -> None:
    db._conn.execute(
        """
        UPDATE quads
        SET object = ?
        WHERE graph = 'history'
          AND subject = ?
          AND predicate = ?
        """,
        (content, patch_iri, RC + "patchContent"),
    )
    db._conn.commit()

def _delete_base_ontology_seed_terms(db: DoxaBase, terms: list[str]) -> None:
    for term in terms:
        iri = db.expand_iri(term)
        db._conn.execute(
            """
            DELETE FROM quads
            WHERE graph = 'base_ontology'
              AND (subject = ? OR object = ?)
            """,
            (iri, iri),
        )
    db._conn.commit()


__all__ = [
    "csv",
    "json",
    "os",
    "sqlite3",
    "warnings",
    "Callable",
    "Path",
    "pytest",
    "Dataset",
    "Graph",
    "Literal",
    "URIRef",
    "DCTERMS",
    "RDF",
    "XSD",
    "DoxaBase",
    "DoxaBaseError",
    "ImmutableGraphError",
    "ProfileInsightReviewCandidate",
    "to_dict",
    "to_jsonable",
    "ProfileScalarConflictRecommendationContext",
    "ProjectBriefRecommendedTask",
    "RevisionNextActionQueueItem",
    "ROOT",
    "AIS_FIXTURE",
    "POLYMARKET_FIXTURE",
    "RC",
    "MUTABLE_GRAPHS",
    "_mutable_graph_counts",
    "_line_number_containing",
    "_assert_repair_action_option",
    "_corrupt_staged_patch_target_graph",
    "_corrupt_staged_patch_content",
    "_delete_base_ontology_seed_terms",
]
