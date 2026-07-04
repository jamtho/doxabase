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

# Merged-door staging kinds whose stage_revision(kind=...) calls belong to the
# recovery mutating family. review_decision and the query repair kinds keep
# their pre-merge classification (their old registrations were never members).
STAGE_REVISION_RECOVERY_MUTATING_KINDS = frozenset(
    {
        "graph",
        "map_assertion",
        "pattern_promotion",
        "profile_map_updates",
        "systematisation",
    }
)

# stage_revision kinds that write a history row when dry_run is not set.
STAGE_REVISION_HISTORY_WRITING_KINDS = frozenset(
    {
        *STAGE_REVISION_RECOVERY_MUTATING_KINDS,
        "review_decision",
    }
)

STAGED_ACTION_HISTORY_WRITING_TOOL_NAMES = frozenset(
    {
        "apply_staged_revision",
        "restage_staged_revision",
        "stage_revision",
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

def action_tool_name(action: Any) -> str | None:
    """Short tool name for a SuggestedNextAction or RevisionNextAction."""

    tool = getattr(action, "tool", None)
    if isinstance(tool, str):
        return tool.removeprefix("doxabase.")
    tool_name = getattr(action, "tool_name", None)
    return tool_name if isinstance(tool_name, str) else None


def action_arguments(action: Any) -> MappingABC[str, Any]:
    """Arguments mapping for a SuggestedNextAction or RevisionNextAction."""

    for attr in ("args", "arguments"):
        value = getattr(action, attr, None)
        if isinstance(value, MappingABC):
            return value
    return {}


def suggested_action_key(action: Any) -> tuple[str, str]:
    """Stable identity key for a suggested next action (tool + canonical args)."""

    return (
        action.tool,
        json.dumps(to_jsonable(action.args), sort_keys=True, default=str),
    )


def stage_revision_action_kind(action: Any) -> str | None:
    """Staging kind for a writing stage_revision action; None otherwise.

    Dry-run planner calls return None so matchers for real staged writes do
    not treat the read-only drafts as staging actions.
    """

    if action_tool_name(action) != "stage_revision":
        return None
    arguments = action_arguments(action)
    if arguments.get("dry_run") is True:
        return None
    kind = arguments.get("kind")
    return kind if isinstance(kind, str) else None


def stage_revision_action_spec(action: Any) -> MappingABC[str, Any]:
    """spec mapping carried by a stage_revision action (empty when absent)."""

    spec = action_arguments(action).get("spec")
    return spec if isinstance(spec, MappingABC) else {}


def action_staging_arguments(action: Any) -> MappingABC[str, Any]:
    """Effective call fields: the spec for stage_revision actions, else args."""

    if action_tool_name(action) == "stage_revision":
        return stage_revision_action_spec(action)
    return action_arguments(action)


def staged_rebase_draft_action(action: Any) -> bool:
    """True for the single-IRI dry-run restage (the rebase-draft planner).

    The read-only rebase draft shares the restage_staged_revision door with
    the writing restage paths; dry_run=True on one IRI string is the planner,
    dry_run=True on a list is the batch would-restage preview.
    """

    if action_tool_name(action) != "restage_staged_revision":
        return False
    arguments = action_arguments(action)
    return (
        arguments.get("dry_run") is True
        and isinstance(arguments.get("revision_iris"), str)
    )


def staged_action_effect_metadata(
    tool_name: str | None,
    arguments: MappingABC[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify the write effects of staged-revision workflow actions."""

    no_effect = {
        "mutation_scope": "none",
        "mutates_project_graph": False,
        "writes_history": False,
        "writes_files": False,
        "writes_storage": False,
    }
    if tool_name is None:
        return no_effect

    action_arguments = arguments or {}
    if action_arguments.get("dry_run") is True and tool_name in {
        "apply_staged_revision",
        "restage_staged_revision",
        "stage_revision",
    }:
        return no_effect
    if tool_name == "stage_revision" and (
        action_arguments.get("kind") not in STAGE_REVISION_HISTORY_WRITING_KINDS
    ):
        return no_effect

    mutates_project_graph = (
        tool_name in STAGED_ACTION_PROJECT_GRAPH_MUTATING_TOOL_NAMES
    )
    writes_files = tool_name in STAGED_ACTION_FILE_WRITING_TOOL_NAMES
    writes_storage = tool_name in STAGED_ACTION_STORAGE_WRITING_TOOL_NAMES
    writes_history = tool_name in STAGED_ACTION_HISTORY_WRITING_TOOL_NAMES
    if tool_name == "import_trig":
        writes_history = True
    if tool_name == "plan_staged_revision_recovery":
        writes_history = action_arguments.get("start_session") is True

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
    """Return a JSON-like plain-Python representation of DoxaBase API values.

    Envelope convention (distillation Phase 3.1): ``None`` values and empty
    lists/dicts are omitted from serialized dataclasses and mappings. Absent,
    null, and empty are equivalent; consumers must not distinguish them. Any
    field where presence itself carries meaning must carry an explicit value
    instead.
    """
    if is_dataclass(value) and not isinstance(value, type):
        result = {}
        for f in fields(value):
            if f.metadata.get("doxabase_internal"):
                # Python-API-only field (e.g. ContextSlice.triples feeds the
                # export path); graph content travels to MCP clients as TriG.
                continue
            item = to_jsonable(getattr(value, f.name))
            if item is None or item == [] or item == {}:
                continue
            result[f.name] = item
        return result
    if isinstance(value, MappingABC):
        result = {}
        for key, item in value.items():
            item = to_jsonable(item)
            if item is None or item == [] or item == {}:
                continue
            result[str(key)] = item
        return result
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
    "STAGE_REVISION_RECOVERY_MUTATING_KINDS",
    "STAGE_REVISION_HISTORY_WRITING_KINDS",
    "STAGED_ACTION_HISTORY_WRITING_TOOL_NAMES",
    "STAGED_ACTION_PROJECT_GRAPH_MUTATING_TOOL_NAMES",
    "STAGED_ACTION_FILE_WRITING_TOOL_NAMES",
    "STAGED_ACTION_STORAGE_WRITING_TOOL_NAMES",
    "stage_revision_action_kind",
    "stage_revision_action_spec",
    "action_staging_arguments",
    "staged_rebase_draft_action",
    "staged_action_effect_metadata",
    "suggested_action_key",
    "action_tool_name",
    "action_arguments",
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
