"""Shared imports, constants, and helpers for doxabase.core."""
from __future__ import annotations

import copy

import hashlib

import json

import ntpath

import posixpath

import re

import sqlite3

import warnings

from collections.abc import Mapping as MappingABC

from contextlib import contextmanager

from dataclasses import dataclass, field, fields, is_dataclass, replace

from difflib import SequenceMatcher

from datetime import UTC, datetime

from pathlib import Path

from typing import Any, Iterable, Iterator, Literal as TypingLiteral, Mapping

from urllib.parse import urlparse

from uuid import uuid4

from pyshacl import validate

from rdflib import BNode, Dataset, Graph, Literal, URIRef

from rdflib.namespace import DCTERMS, RDF, RDFS, XSD

from rdflib.term import Identifier, Node

GraphName = TypingLiteral[
    "base_ontology",
    "base_shapes",
    "map",
    "ontology",
    "observations",
    "patterns",
    "evidence",
    "shapes",
    "history",
]

GraphStorageRow = tuple[str, str, str, str, str, str | None, str | None]

StagedApplyCheckCacheKey = tuple[str, str | None]

def _data_root() -> Path:
    """Root for shipped data: ontology seeds, agent docs, example fixtures.

    An installed wheel carries them under ``doxabase/_data/`` mirroring the
    repo-root layout (see pyproject force-include); a repo checkout uses the
    repo root itself, so relative data paths are identical in both.
    """
    package_dir = Path(__file__).resolve().parents[1]  # .../doxabase
    packaged = package_dir / "_data"
    if packaged.is_dir():
        return packaged
    return package_dir.parent

ROOT = _data_root()

BASE_ONTOLOGY_PATH = ROOT / "ontology" / "rc_core.ttl"

BASE_SHAPES_PATH = ROOT / "ontology" / "rc_shapes.ttl"

SeedGraphCacheKey = tuple[str, str, int, int]

_SEED_GRAPH_CACHE: dict[SeedGraphCacheKey, Graph] = {}

SEARCH_INDEX_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS literal_search USING fts5(
    graph UNINDEXED,
    subject UNINDEXED,
    subject_kind UNINDEXED,
    predicate UNINDEXED,
    text,
    tokenize = 'unicode61'
)
"""

RCG_PREFIX = "https://richcanopy.org/graph/"

PREFIXES = {
    "dcterms": "http://purl.org/dc/terms/",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rc": "https://richcanopy.org/ns/rc#",
    "rdf": str(RDF),
    "rdfs": str(RDFS),
    "sh": "http://www.w3.org/ns/shacl#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}

SENSITIVE_LITERAL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "private_key_header",
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.IGNORECASE),
    ),
    (
        "bearer_token",
        re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE),
    ),
    (
        "aws_access_key_id",
        re.compile(r"\bA(?:KIA|SIA)[0-9A-Z]{16}\b"),
    ),
    (
        "sk_secret_key",
        re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{12,}\b"),
    ),
    (
        "secret_parameter",
        re.compile(
            r"(?i)([?&]|\b)(access_token|api[_-]?key|password|passwd|pwd|secret|token|private[_-]?key)="
            r"[^\s&#;]{4,}"
        ),
    ),
    (
        "secret_assignment",
        re.compile(
            r"(?i)\b(access[_-]?key|api[_-]?key|password|passwd|pwd|secret|token|private[_-]?key)"
            r"\s*[:=]\s*[^\s,;]{4,}"
        ),
    ),
    (
        "fake_secret_marker",
        re.compile(r"\bFAKE_(?:SECRET|TOKEN|PASSWORD|API_KEY)[A-Z0-9_:-]*\b"),
    ),
)

SHAREABILITY_HINT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "absolute_local_home_path",
        re.compile(
            r"(?i)(^|[\s'\"=:(])(?:~[/\\]|/(?:Users|home)/[^\s'\"<>]+|[A-Z]:\\Users\\[^\s'\"<>]+)"
        ),
    ),
    (
        "absolute_local_runtime_path",
        re.compile(
            r"(?i)(^|[\s'\"=:(])(?:file://)?/(?:tmp|var/tmp|private/tmp|work|workspace|workspaces)(?:[/?#]|$)[^\s'\"<>]*"
        ),
    ),
)

SHAREABILITY_HINT_MESSAGES: dict[str, str] = {
    "absolute_local_home_path": (
        "Selected export content contains an absolute local home/private path. "
        "This is not a credential match, but the artifact should stay local "
        "until a shareability review decides whether that path is appropriate."
    ),
    "absolute_local_runtime_path": (
        "Selected export content contains an absolute local runtime/workspace "
        "path. This is not a credential match, but the artifact should stay "
        "local until a shareability review decides whether the receiver can "
        "interpret or reproduce that path."
    ),
}

DEFAULT_ARTIFACT_DISPOSITION = "local_only_pending_shareability_review"

DEFAULT_SHAREABILITY_HINT_MATCH_LIMIT = 20

PROFILE_TO_CAPSULE_MANIFEST_FORMAT = "doxabase.profile_to_capsule_manifest.v1"

MISSING_STORAGE_GENERIC_TOKENS = {
    "archive",
    "archives",
    "csv",
    "data",
    "dataset",
    "datasets",
    "file",
    "files",
    "json",
    "parquet",
    "snapshot",
    "snapshots",
    "table",
    "tables",
    "trial",
}

KNOWN_QUERY_FIXTURE_TABLE_GROUPS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "AIS",
        "https://richcanopy.org/example/manifest/ais#",
        ("DailyBroadcasts", "DailyIndex"),
    ),
    (
        "Polymarket",
        "https://richcanopy.org/example/manifest/polymarket#",
        (
            "MarketSnapshots",
            "OrderbookSnapshots",
            "Trades",
            "HolderSnapshots",
            "Markets",
            "PriceSnapshots",
            "TradeEvents",
            "OrderBookSnapshots",
            "MarketOutcomes",
        ),
    ),
)

SCHEMA_STABILITY_LEVELS = (
    "rc:FixedSchema",
    "rc:InferredSchema",
    "rc:VariableSchema",
)

ROW_SEMANTICS_TYPES = (
    "rc:EventRow",
    "rc:SnapshotRow",
    "rc:AggregateRow",
    "rc:DimensionRow",
)

LAYOUT_VERIFICATION_STATUSES = (
    "rc:UnverifiedLayout",
    "rc:GeneratedFromManifestLayout",
    "rc:CandidateLayout",
    "rc:VerifiedByListingLayout",
    "rc:VerifiedByQueryLayout",
    "rc:ContradictedLayout",
)

CAVEAT_SEVERITY_LEVELS = (
    "rc:Minor",
    "rc:Moderate",
    "rc:Severe",
)

PARTITION_GRANULARITIES = (
    "rc:Daily",
    "rc:Hourly",
    "rc:Monthly",
    "rc:ByValue",
)

DERIVATION_PROPERTIES = (
    "rc:Deterministic",
    "rc:Invertible",
    "rc:Lossy",
)

RELATIONSHIP_TYPE_IRIS = {
    "foreign_key": "rc:ForeignKey",
    "shared_identifier": "rc:SharedIdentifier",
    "derivation": "rc:Derivation",
    "aggregation": "rc:Aggregation",
}

RELATIONSHIP_TYPE_ALIASES = {
    token: token for token in RELATIONSHIP_TYPE_IRIS
} | {
    "ForeignKey": "foreign_key",
    "SharedIdentifier": "shared_identifier",
    "Derivation": "derivation",
    "Aggregation": "aggregation",
    "rc:ForeignKey": "foreign_key",
    "rc:SharedIdentifier": "shared_identifier",
    "rc:Derivation": "derivation",
    "rc:Aggregation": "aggregation",
    f"{PREFIXES['rc']}ForeignKey": "foreign_key",
    f"{PREFIXES['rc']}SharedIdentifier": "shared_identifier",
    f"{PREFIXES['rc']}Derivation": "derivation",
    f"{PREFIXES['rc']}Aggregation": "aggregation",
}

TRANSFORM_CONDITION_KINDS = (
    "rc:FilterCondition",
    "rc:SelectionCondition",
)

CONFIDENCE_LEVELS = (
    "rc:LowConfidence",
    "rc:MediumConfidence",
    "rc:HighConfidence",
)

PATTERN_OBSERVATION_STATUSES = (
    "rc:Tentative",
    "rc:Checked",
    "rc:Weakened",
    "rc:Contradicted",
    "rc:Superseded",
    "rc:Promoted",
)

PATTERN_STABILITY_LEVELS = (
    "rc:EmergingPattern",
    "rc:RepeatedPattern",
    "rc:InvariantPattern",
)

REQUIRED_STAGING_ONTOLOGY_TERMS = (
    "rc:GraphPatchRole",
    "rc:FramingPatch",
    "rc:SharedContextPatch",
)

REQUIRED_REVISION_STANCE_ONTOLOGY_TERMS = (
    "rc:RevisionStance",
    "rc:CandidateRevision",
)

STAGED_REVIEW_DECISIONS = {
    "accepted_elsewhere": "rc:AcceptedElsewhereDecision",
    "superseded": "rc:SupersededDecision",
    "discarded": "rc:DiscardedDecision",
    "no_effective_change": "rc:NoEffectiveChangeDecision",
}

REQUIRED_STAGED_REVIEW_DECISION_ONTOLOGY_TERMS = (
    "rc:StagedRevisionReviewDecision",
    *STAGED_REVIEW_DECISIONS.values(),
)

PROFILE_SCALAR_MAP_UPDATE_KINDS = frozenset(
    {
        "dataset_row_count_snapshot",
        "column_nullable",
    }
)

PROFILE_ROUTE_SOURCE_SCHEMA = "doxabase.profile_route_source.v1"

PROFILE_METRIC_PROMOTION_REVIEW_NOTE_MARKER = (
    "metric-vocabulary promotion skeleton from draft_profile_map_updates"
)

PROFILE_VALUE_TYPE_PROMOTION_REVIEW_NOTE_MARKER = (
    "value-type promotion skeleton from draft_profile_map_updates"
)

QUERY_REPAIR_PREDICATE_CURIES = frozenset(
    {
        "rc:hasStorageAccess",
        "rc:storageProtocol",
        "rc:accessMode",
        "rc:locationKind",
        "rc:storageRoot",
        "rc:endpointProfile",
        "rc:bucketName",
        "rc:keyPrefix",
        "rc:region",
        "rc:credentialReference",
        "rc:pathStyleAccess",
        "rc:pathTemplate",
        "rc:layoutVerificationStatus",
        "rc:layoutVerificationNote",
        "rc:hasPhysicalLayout",
        "rc:partitionedBy",
        "rc:partitionColumn",
        "rc:partitionGranularity",
        "rc:redundantPartitionKey",
        "rc:fileFormat",
        "rc:compressionCodec",
    }
)

STAGED_RECOVERY_MUTATING_TOOL_NAMES = frozenset(
    {
        "apply_staged_revision",
        "restage_staged_revision",
        "restage_staged_revisions",
        "stage_graph_revision",
        "stage_map_assertion_change",
        "stage_pattern_promotion",
        "stage_profile_map_updates",
        "stage_systematisation",
    }
)

STAGED_ACTION_HISTORY_WRITING_TOOL_NAMES = frozenset(
    {
        "apply_staged_revision",
        "record_staged_revision_review_decision",
        "restage_staged_revision",
        "restage_staged_revisions",
        "start_staged_revision_recovery_session",
        "stage_graph_revision",
        "stage_map_assertion_change",
        "stage_pattern_promotion",
        "stage_profile_map_updates",
        "stage_systematisation",
    }
)

STAGED_ACTION_PROJECT_GRAPH_MUTATING_TOOL_NAMES = frozenset(
    {
        "apply_staged_revision",
        "import_trig",
    }
)

STAGED_ACTION_FILE_WRITING_TOOL_NAMES = frozenset(
    {
        "export_staged_revision",
        "export_staged_revisions",
    }
)

STAGED_ACTION_STORAGE_WRITING_TOOL_NAMES = frozenset(
    {
        "import_revision_snapshots",
    }
)

def staged_action_effect_metadata(
    tool_name: str | None,
    arguments: MappingABC[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify the write effects of staged-revision workflow actions."""

    if tool_name is None:
        return {
            "mutation_scope": "none",
            "mutates_project_graph": False,
            "writes_history": False,
            "writes_files": False,
            "writes_storage": False,
        }

    action_arguments = arguments or {}
    if (
        tool_name == "restage_staged_revisions"
        and action_arguments.get("dry_run") is True
    ):
        return {
            "mutation_scope": "none",
            "mutates_project_graph": False,
            "writes_history": False,
            "writes_files": False,
            "writes_storage": False,
        }

    mutates_project_graph = (
        tool_name in STAGED_ACTION_PROJECT_GRAPH_MUTATING_TOOL_NAMES
    )
    writes_files = tool_name in STAGED_ACTION_FILE_WRITING_TOOL_NAMES
    writes_storage = tool_name in STAGED_ACTION_STORAGE_WRITING_TOOL_NAMES
    writes_history = tool_name in STAGED_ACTION_HISTORY_WRITING_TOOL_NAMES
    if tool_name == "import_trig":
        writes_history = True

    if tool_name == "apply_staged_revision":
        mutation_scope = "project_graph_and_history"
    elif mutates_project_graph:
        mutation_scope = "project_graph_import"
    elif writes_history:
        mutation_scope = "history"
    elif writes_storage:
        mutation_scope = "snapshot_storage"
    elif writes_files:
        mutation_scope = "file_export"
    else:
        mutation_scope = "none"

    return {
        "mutation_scope": mutation_scope,
        "mutates_project_graph": mutates_project_graph,
        "writes_history": writes_history,
        "writes_files": writes_files,
        "writes_storage": writes_storage,
    }

def to_jsonable(value: Any) -> Any:
    """Return a JSON-like plain-Python representation of DoxaBase API values."""
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: to_jsonable(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, MappingABC):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return value

def to_dict(value: Any) -> dict[str, Any]:
    """Return a dict representation of one DoxaBase dataclass-like API value."""
    result = to_jsonable(value)
    if not isinstance(result, dict):
        raise TypeError("to_dict() expects a DoxaBase dataclass or mapping value")
    return result

CLAIM_RECONSIDERATION_RELATIONS = {
    "weakens": ("rc:Weakening", "rc:weakens", "rc:Weakened"),
    "contradicts": ("rc:Contradiction", "rc:contradicts", "rc:Contradicted"),
    "supersedes": ("rc:Supersession", "rc:supersedes", "rc:Superseded"),
    "refines": ("rc:Refinement", "rc:refines", None),
}

DEFAULT_GRAPHS: tuple[tuple[str, str, bool, bool, Path | None], ...] = (
    (
        "base_ontology",
        "Immutable shipped Rich Canopy base ontology",
        False,
        True,
        BASE_ONTOLOGY_PATH,
    ),
    (
        "base_shapes",
        "Immutable shipped Rich Canopy SHACL shapes",
        False,
        True,
        BASE_SHAPES_PATH,
    ),
    ("map", "Current best project/data map", True, False, None),
    ("ontology", "Project-owned ontology extensions", True, False, None),
    ("observations", "Point-in-time observations and tentative findings", True, False, None),
    ("patterns", "Syntheses that connect observations to map facts", True, False, None),
    ("evidence", "Evidence supporting observations and map assertions", True, False, None),
    ("shapes", "Project-owned SHACL shapes", True, False, None),
    (
        "history",
        "Revision metadata, graph-count snapshots, and rationale",
        True,
        False,
        None,
    ),
)

EXPORT_PRESETS: dict[str, tuple[str, ...]] = {
    "workflow": ("map", "observations", "patterns", "evidence"),
    "review_bundle": ("map", "observations", "patterns", "evidence"),
    "project": (
        "ontology",
        "map",
        "observations",
        "patterns",
        "evidence",
        "shapes",
        "history",
    ),
    "all_with_seeds": tuple(graph[0] for graph in DEFAULT_GRAPHS),
}

SEED_GRAPH_NAMES = {
    name for name, _description, _mutable, system_seed, _source_path in DEFAULT_GRAPHS
    if system_seed
}

SEARCH_SCOPE_HINT_GRAPHS = ("map", "observations", "patterns", "evidence")

def _now() -> str:
    return datetime.now(UTC).isoformat()

def _fts_query(query: str) -> str:
    return _fts_query_from_tokens(_search_tokens(query))

def _fts_query_from_tokens(tokens: list[str]) -> str:
    return " AND ".join(f"{token.lower()}*" for token in tokens)

def _fts_or_query_from_tokens(tokens: list[str]) -> str:
    return " OR ".join(f"{token.lower()}*" for token in tokens)

def _existing_path(source: str | Path) -> Path | None:
    if isinstance(source, Path):
        return source if source.exists() else None
    if "\n" in source or "\r" in source:
        return None
    try:
        path = Path(source)
        return path if path.exists() else None
    except OSError:
        return None


__all__ = [
    "copy",
    "hashlib",
    "json",
    "ntpath",
    "posixpath",
    "re",
    "sqlite3",
    "warnings",
    "MappingABC",
    "contextmanager",
    "dataclass",
    "field",
    "fields",
    "is_dataclass",
    "replace",
    "SequenceMatcher",
    "UTC",
    "datetime",
    "Path",
    "Any",
    "Iterable",
    "Iterator",
    "TypingLiteral",
    "Mapping",
    "urlparse",
    "uuid4",
    "validate",
    "BNode",
    "Dataset",
    "Graph",
    "Literal",
    "URIRef",
    "DCTERMS",
    "RDF",
    "RDFS",
    "XSD",
    "Identifier",
    "Node",
    "GraphName",
    "GraphStorageRow",
    "StagedApplyCheckCacheKey",
    "_data_root",
    "ROOT",
    "BASE_ONTOLOGY_PATH",
    "BASE_SHAPES_PATH",
    "SeedGraphCacheKey",
    "_SEED_GRAPH_CACHE",
    "SEARCH_INDEX_SQL",
    "RCG_PREFIX",
    "PREFIXES",
    "SENSITIVE_LITERAL_PATTERNS",
    "SHAREABILITY_HINT_PATTERNS",
    "SHAREABILITY_HINT_MESSAGES",
    "DEFAULT_ARTIFACT_DISPOSITION",
    "DEFAULT_SHAREABILITY_HINT_MATCH_LIMIT",
    "PROFILE_TO_CAPSULE_MANIFEST_FORMAT",
    "MISSING_STORAGE_GENERIC_TOKENS",
    "KNOWN_QUERY_FIXTURE_TABLE_GROUPS",
    "SCHEMA_STABILITY_LEVELS",
    "ROW_SEMANTICS_TYPES",
    "LAYOUT_VERIFICATION_STATUSES",
    "CAVEAT_SEVERITY_LEVELS",
    "PARTITION_GRANULARITIES",
    "DERIVATION_PROPERTIES",
    "RELATIONSHIP_TYPE_IRIS",
    "RELATIONSHIP_TYPE_ALIASES",
    "TRANSFORM_CONDITION_KINDS",
    "CONFIDENCE_LEVELS",
    "PATTERN_OBSERVATION_STATUSES",
    "PATTERN_STABILITY_LEVELS",
    "REQUIRED_STAGING_ONTOLOGY_TERMS",
    "REQUIRED_REVISION_STANCE_ONTOLOGY_TERMS",
    "STAGED_REVIEW_DECISIONS",
    "REQUIRED_STAGED_REVIEW_DECISION_ONTOLOGY_TERMS",
    "PROFILE_SCALAR_MAP_UPDATE_KINDS",
    "PROFILE_ROUTE_SOURCE_SCHEMA",
    "PROFILE_METRIC_PROMOTION_REVIEW_NOTE_MARKER",
    "PROFILE_VALUE_TYPE_PROMOTION_REVIEW_NOTE_MARKER",
    "QUERY_REPAIR_PREDICATE_CURIES",
    "STAGED_RECOVERY_MUTATING_TOOL_NAMES",
    "STAGED_ACTION_HISTORY_WRITING_TOOL_NAMES",
    "STAGED_ACTION_PROJECT_GRAPH_MUTATING_TOOL_NAMES",
    "STAGED_ACTION_FILE_WRITING_TOOL_NAMES",
    "STAGED_ACTION_STORAGE_WRITING_TOOL_NAMES",
    "staged_action_effect_metadata",
    "to_jsonable",
    "to_dict",
    "CLAIM_RECONSIDERATION_RELATIONS",
    "DEFAULT_GRAPHS",
    "EXPORT_PRESETS",
    "SEED_GRAPH_NAMES",
    "SEARCH_SCOPE_HINT_GRAPHS",
    "_now",
    "_fts_query",
    "_fts_query_from_tokens",
    "_fts_or_query_from_tokens",
    "_existing_path",
]
