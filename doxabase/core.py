from __future__ import annotations

import re
import sqlite3
import warnings
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Literal as TypingLiteral, Mapping
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

ROOT = Path(__file__).resolve().parents[1]
BASE_ONTOLOGY_PATH = ROOT / "ontology" / "rc_core.ttl"
BASE_SHAPES_PATH = ROOT / "ontology" / "rc_shapes.ttl"

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


class DoxaBaseError(Exception):
    """Base exception for DoxaBase runtime errors."""


class ImmutableGraphError(DoxaBaseError):
    """Raised when a caller tries to mutate an immutable graph."""


@dataclass(frozen=True)
class NamedGraphInfo:
    name: str
    description: str | None
    mutable: bool
    system_seed: bool
    source_path: str | None
    triple_count: int


@dataclass(frozen=True)
class GraphOverview:
    named_graphs: list[NamedGraphInfo]
    class_counts: list[tuple[str, int]]
    predicate_counts: list[tuple[str, int]]
    key_counts: dict[str, int]
    namespaces: dict[str, str]


@dataclass(frozen=True)
class GraphExportRecord:
    path: str
    format: str
    graphs: list[str]
    graph_counts: dict[str, int]
    triples: int
    bytes_written: int


@dataclass(frozen=True)
class GraphRevisionRecord:
    revision_iri: str
    revision_type: str
    graph: str
    triples: int


@dataclass(frozen=True)
class StagedGraphPatchRecord:
    patch_iri: str
    operation: str
    target_graph: str
    format: str
    patch_role: str
    triple_count: int
    before_triple_count: int
    after_triple_count: int


@dataclass(frozen=True)
class ValidationDiagnostic:
    iri: str | None
    focus_node: str | None
    focus_node_label: str | None
    result_path: str | None
    result_path_label: str | None
    value: str | None
    source_shape: str | None
    source_constraint_component: str | None
    source_constraint_component_label: str | None
    severity: str | None
    severity_label: str | None
    messages: list[str]


@dataclass(frozen=True)
class StagedGraphRevisionRecord:
    revision_iri: str
    revision_type: str
    revision_stance: str
    graph: str
    triples: int
    changed_graphs: list[str]
    patches: list[StagedGraphPatchRecord]
    validation_scope: str
    validation_conforms: bool
    validation_result_count: int
    validation_results: list[ValidationDiagnostic]


@dataclass(frozen=True)
class StagedPatchApplyCheck:
    patch_iri: str
    target_graph: str | None
    operation: str | None
    operation_label: str | None
    patch_role: str | None
    patch_role_label: str | None
    triple_count: int | None
    before_triple_count: int | None
    current_triple_count: int | None
    after_triple_count: int | None
    preview_triple_count: int | None
    can_apply: bool
    conflict: str | None


@dataclass(frozen=True)
class StagedRevisionApplyCheck:
    staged_revision_iri: str
    can_apply: bool
    already_applied_by: str | None
    changed_graphs: list[str]
    patch_checks: list[StagedPatchApplyCheck]
    conflicts: list[str]
    validation_scope: str
    validation_conforms: bool | None
    validation_result_count: int | None
    validation_results: list[ValidationDiagnostic]
    patches_checked: int
    triples_to_add: int
    triples_to_remove: int


@dataclass(frozen=True)
class SystematisationFramingRecord:
    label: str
    rationale: str | None
    review_note: str | None
    review_recommendation: str | None
    target_graphs: list[str]
    stance: str
    revision_iri: str
    patch_count: int
    triple_count: int
    validation_scope: str
    validation_conforms: bool
    validation_result_count: int
    validation_results: list[ValidationDiagnostic]


@dataclass(frozen=True)
class SystematisationDraftRecord:
    summary: str
    intent: str
    anchors: list[str]
    warnings: list[str]
    framings: list[SystematisationFramingRecord]
    staged_revisions: list[StagedGraphRevisionRecord]


@dataclass(frozen=True)
class AppliedStagedRevisionRecord:
    applied_revision_iri: str
    staged_revision_iri: str
    graph: str
    triples: int
    changed_graphs: list[str]
    patches_applied: int
    triples_added: int
    triples_removed: int
    validation_scope: str
    validation_conforms: bool
    validation_result_count: int
    validation_results: list[ValidationDiagnostic]


@dataclass(frozen=True)
class StagedGraphRevisionExportRecord:
    path: str
    format: str
    revision_iri: str
    bytes_written: int


@dataclass(frozen=True)
class StagedGraphRevisionsExportRecord:
    path: str
    format: str
    revision_iris: list[str]
    bytes_written: int


@dataclass(frozen=True)
class _StagedRevisionApplicationPreview:
    staged: StagedGraphRevisionDescription
    check: StagedRevisionApplyCheck
    parsed_patches: list[tuple[StagedGraphPatchDescription, Graph]]
    preview_graphs: dict[str, Graph]


@dataclass(frozen=True)
class GraphSnapshotDescription:
    graph_role: str
    triple_count: int


@dataclass(frozen=True)
class StagedGraphPatchDescription:
    iri: str
    operation: str
    operation_label: str | None
    target_graph: str | None
    format: str | None
    patch_role: str | None
    patch_role_label: str | None
    triple_count: int | None
    before_triple_count: int | None
    after_triple_count: int | None
    content: str | None


@dataclass(frozen=True)
class GraphRevisionDescription:
    iri: str
    graph: str | None
    label: str | None
    summary: str | None
    revision_type: str | None
    revision_type_label: str | None
    rationale: str | None
    changed_graphs: list[str]
    included_graphs: list[str]
    created_at: str | None
    created_by: str | None
    export_path: str | None
    validation_scope: str | None
    validation_conforms: bool | None
    validation_result_count: int | None
    validation_results: list[ValidationDiagnostic]
    graph_snapshots: list[GraphSnapshotDescription]
    supporting_observations: list[ResourceSummary]
    supporting_claims: list[ResourceSummary]
    supporting_patterns: list[ResourceSummary]
    revision_anchors: list[ResourceSummary]
    evidence: list[ResourceSummary]


@dataclass(frozen=True)
class StagedGraphRevisionDescription:
    iri: str
    graph: str | None
    label: str | None
    summary: str | None
    revision_type: str | None
    revision_type_label: str | None
    revision_stance: str | None
    revision_stance_label: str | None
    rationale: str | None
    review_note: str | None
    review_recommendation: str | None
    alternative_to: ResourceSummary | None
    changed_graphs: list[str]
    included_graphs: list[str]
    created_at: str | None
    created_by: str | None
    validation_scope: str | None
    validation_conforms: bool | None
    validation_result_count: int | None
    validation_results: list[ValidationDiagnostic]
    graph_snapshots: list[GraphSnapshotDescription]
    patches: list[StagedGraphPatchDescription]
    supporting_observations: list[ResourceSummary]
    supporting_claims: list[ResourceSummary]
    supporting_patterns: list[ResourceSummary]
    revision_anchors: list[ResourceSummary]
    evidence: list[ResourceSummary]


@dataclass(frozen=True)
class EntityRow:
    iri: str
    label: str | None
    types: list[str]
    graph: str


@dataclass(frozen=True)
class EntityList:
    entities: list[EntityRow]
    limit: int
    offset: int


@dataclass(frozen=True)
class ResourceSummary:
    iri: str
    label: str | None
    description: str | None
    column_name: str | None = None
    owning_dataset_iri: str | None = None
    owning_dataset_label: str | None = None


@dataclass(frozen=True)
class ColumnDescription:
    iri: str
    label: str | None
    description: str | None
    column_name: str | None
    physical_type: ResourceSummary | None
    value_type: ResourceSummary | None
    nullable: bool | None


@dataclass(frozen=True)
class PhysicalLayoutDescription:
    iri: str
    label: str | None
    description: str | None
    file_format: ResourceSummary | None
    compression_codec: ResourceSummary | None
    layout_verification_status: ResourceSummary | None
    layout_verification_note: str | None


@dataclass(frozen=True)
class StorageAccessDescription:
    iri: str
    label: str | None
    description: str | None
    storage_protocol: ResourceSummary | None
    access_mode: ResourceSummary | None
    storage_root: str | None
    endpoint_profile: str | None
    bucket_name: str | None
    key_prefix: str | None
    region: str | None
    path_style_access: bool | None
    credential_reference: str | None
    path_templates: list[str]
    layout_verification_status: ResourceSummary | None
    layout_verification_note: str | None


@dataclass(frozen=True)
class PartitionDescription:
    iri: str
    label: str | None
    description: str | None
    partition_column: ResourceSummary | None
    granularity: ResourceSummary | None
    path_template: str | None
    redundant_partition_key: ResourceSummary | None
    layout_verification_status: ResourceSummary | None
    layout_verification_note: str | None


@dataclass(frozen=True)
class RelatedDatasetDescription:
    iri: str
    label: str | None
    description: str | None
    relationship: str
    relationship_iri: str | None
    relationship_label: str | None
    relationship_kind: str | None
    relationship_kind_label: str | None


@dataclass(frozen=True)
class RelatedDatasetReasonTag:
    relationship: str
    relationship_iri: str | None
    relationship_label: str | None
    relationship_kind: str | None
    relationship_kind_label: str | None
    declared: bool | None
    referential_integrity: ResourceSummary | None


@dataclass(frozen=True)
class RelatedDatasetReason:
    relationship: str
    relationship_iri: str | None
    relationship_label: str | None
    relationship_kind: str | None
    relationship_kind_label: str | None
    columns: list[ResourceSummary]
    current_dataset_columns: list[ResourceSummary]
    related_dataset_columns: list[ResourceSummary]
    declared: bool | None
    referential_integrity: ResourceSummary | None
    source_caveats: list[CaveatDescription]
    relationship_tags: list[RelatedDatasetReasonTag]


@dataclass(frozen=True)
class RelatedDatasetGroup:
    iri: str
    label: str | None
    description: str | None
    reasons: list[RelatedDatasetReason]


@dataclass(frozen=True)
class LinkedPatternMatch:
    match_type: str
    matched_resource: ResourceSummary
    supporting_claim: ResourceSummary | None
    supporting_observation: ResourceSummary | None


@dataclass(frozen=True)
class LinkedPatternMatchGroup:
    matched_resource: ResourceSummary
    matched_resource_types: list[str]
    matched_resource_kind: str | None
    relevance_tier: str
    route_types: list[str]
    route_labels: list[str]
    supporting_claims: list[ResourceSummary]
    supporting_observations: list[ResourceSummary]


@dataclass(frozen=True)
class LinkedPatternReason:
    iri: str
    pattern_iri: str
    label: str | None
    pattern_text: str | None
    rationale: str | None
    match_group_count: int
    raw_match_count: int
    relevance_tier_counts: dict[str, int]
    match_groups: list[LinkedPatternMatchGroup]
    matches: list[LinkedPatternMatch]


@dataclass(frozen=True)
class CaveatDescription:
    iri: str
    label: str | None
    description: str | None
    impact: str | None
    severity: ResourceSummary | None


@dataclass(frozen=True)
class TransformationDescription:
    iri: str
    label: str | None
    description: str | None
    transformation_type: str | None
    transformation_description: str | None


@dataclass(frozen=True)
class AggregatedColumnDescription:
    iri: str
    target_column: ResourceSummary | None
    source_columns: list[ResourceSummary]
    aggregation_function: ResourceSummary | None
    within_group_ordering: ResourceSummary | None


@dataclass(frozen=True)
class RelationshipDescription:
    iri: str
    label: str | None
    description: str | None
    types: list[str]
    relationship_kind: str | None
    relationship_kind_label: str | None
    source_dataset: ResourceSummary | None
    target_dataset: ResourceSummary | None
    foreign_key_from: ResourceSummary | None
    foreign_key_to: ResourceSummary | None
    referential_integrity: ResourceSummary | None
    declared: bool | None
    identifying_columns: list[ResourceSummary]
    source_columns: list[ResourceSummary]
    derived_columns: list[ResourceSummary]
    derivation_function: ResourceSummary | None
    derivation_properties: list[ResourceSummary]
    group_by_columns: list[ResourceSummary]
    aggregated_columns: list[AggregatedColumnDescription]
    source_caveats: list[CaveatDescription]


@dataclass(frozen=True)
class DatasetDescription:
    iri: str
    graph: str | None
    label: str | None
    description: str | None
    types: list[str]
    row_semantics: ResourceSummary | None
    entity_key: ResourceSummary | None
    snapshot_timestamp: ResourceSummary | None
    schema_stability: ResourceSummary | None
    row_count_snapshot: int | None
    layout_verification_status: ResourceSummary | None
    layout_verification_note: str | None
    columns: list[ColumnDescription]
    path_templates: list[str]
    physical_layouts: list[PhysicalLayoutDescription]
    storage_accesses: list[StorageAccessDescription]
    partition_schemes: list[PartitionDescription]
    caveats: list[CaveatDescription]
    upstream_caveats: list[CaveatDescription]
    provenance: list[ResourceSummary]
    transformations: list[TransformationDescription]
    related_datasets: list[RelatedDatasetDescription]
    related_dataset_groups: list[RelatedDatasetGroup]
    relationships: list[RelationshipDescription]
    linked_patterns: list[ResourceSummary]
    linked_pattern_reasons: list[LinkedPatternReason]


@dataclass(frozen=True)
class ObservationRecord:
    observation_iri: str
    observation_type: str
    evidence_iri: str | None
    observation_triples: int
    evidence_triples: int


@dataclass(frozen=True)
class ClaimObservationRecord:
    observation_iri: str
    claim_iri: str
    evidence_iri: str
    source_span_iri: str | None
    observation_triples: int
    evidence_triples: int


@dataclass(frozen=True)
class PatternRecord:
    pattern_iri: str
    evidence_iri: str | None
    source_span_iri: str | None
    pattern_triples: int
    evidence_triples: int


@dataclass(frozen=True)
class ClaimReconsiderationRecord:
    reconsideration_iri: str
    newer_claim_iri: str
    older_claim_iri: str
    relation: str
    relation_label: str | None
    direct_predicate: str
    older_claim_status: str | None
    evidence_iri: str | None
    source_span_iri: str | None
    reconsideration_triples: int
    evidence_triples: int
    status_triples: int


@dataclass(frozen=True)
class SourceSpanDescription:
    iri: str
    source_path: str | None
    source_section: str | None
    start_line: int | None
    end_line: int | None
    source_kind: str | None
    source_kind_label: str | None


@dataclass(frozen=True)
class EvidenceDescription:
    iri: str
    label: str | None
    summary: str | None
    sources: list[str]
    source_spans: list[SourceSpanDescription]


@dataclass(frozen=True)
class ClaimReconsiderationDescription:
    iri: str
    label: str | None
    summary: str | None
    rationale: str | None
    relation: str | None
    relation_label: str | None
    newer_claim: ResourceSummary | None
    older_claim: ResourceSummary | None
    evidence: list[EvidenceDescription]
    reconsidered_at: str | None
    reconsidered_by: str | None


@dataclass(frozen=True)
class ClaimDescription:
    iri: str
    label: str | None
    claim_text: str | None
    claim_kind: str | None
    claim_kind_label: str | None
    claim_targets: list[ResourceSummary]
    confidence: str | None
    confidence_label: str | None
    observation_status: str | None
    observation_status_label: str | None
    proposed_assertions: list[ResourceSummary]
    lifecycle_summary: str | None
    outgoing_reconsiderations: list[ClaimReconsiderationDescription]
    incoming_reconsiderations: list[ClaimReconsiderationDescription]


@dataclass(frozen=True)
class PatternDescription:
    iri: str
    graph: str | None
    label: str | None
    summary: str | None
    pattern_text: str | None
    rationale: str | None
    pattern_targets: list[ResourceSummary]
    supporting_observations: list[ResourceSummary]
    supporting_claims: list[ClaimDescription]
    evidence: list[EvidenceDescription]
    confidence: str | None
    confidence_label: str | None
    observation_status: str | None
    observation_status_label: str | None
    pattern_stability: str | None
    pattern_stability_label: str | None
    map_implications: list[ResourceSummary]


@dataclass(frozen=True)
class MapResourceRecord:
    iri: str
    resource_type: str
    graph: str
    triples: int


@dataclass(frozen=True)
class ResourceTriple:
    graph: str
    subject: str
    subject_kind: str
    subject_label: str | None
    subject_types: list[str]
    predicate: str
    predicate_label: str | None
    object: str
    object_kind: str
    object_label: str | None
    object_types: list[str]
    object_datatype: str | None
    object_lang: str | None


@dataclass(frozen=True)
class ResourceContext:
    iri: str
    graph: str | None
    label: str | None
    description: str | None
    types: list[str]
    claim: ClaimDescription | None
    outgoing: list[ResourceTriple]
    incoming: list[ResourceTriple]
    limit: int


@dataclass(frozen=True)
class ContextSliceRoute:
    route: str
    route_label: str
    source_iri: str | None
    source_label: str | None
    depth: int


@dataclass(frozen=True)
class ContextSliceRouteLegend:
    route: str
    route_label: str
    meaning: str
    priority: int
    count: int


@dataclass(frozen=True)
class ContextSliceResource:
    iri: str
    label: str | None
    description: str | None
    types: list[str]
    graphs: list[str]
    referenced_only: bool
    primary_route: ContextSliceRoute
    routes: list[ContextSliceRoute]


@dataclass(frozen=True)
class ContextSlice:
    profile: str
    seeds: list[ResourceSummary]
    reading_order: list[str]
    resources: list[ContextSliceResource]
    resource_count: int
    route_legend: list[ContextSliceRouteLegend]
    route_counts: dict[str, int]
    graph_counts: dict[str, int]
    triples: list[ResourceTriple]
    triple_count: int
    returned_triple_count: int
    candidate_triple_count: int
    omitted_triple_count: int
    max_triples: int
    truncated: bool
    truncation_scope: str
    trig: str | None
    dataset_contexts: list[DatasetDescription]
    pattern_contexts: list[PatternDescription]
    warnings: list[str]


@dataclass(frozen=True)
class SearchMatch:
    iri: str
    graph: str
    label: str | None
    types: list[str]
    predicate: str
    predicate_label: str | None
    text: str
    snippet: str


@dataclass(frozen=True)
class SearchResults:
    query: str
    graph: str | None
    matches: list[SearchMatch]
    limit: int
    offset: int


@dataclass(frozen=True)
class ValidationResult:
    conforms: bool
    report_text: str
    result_count: int
    scope: str
    results: list[ValidationDiagnostic]


class DoxaBase:
    """A small SQLite-backed RDF memory capsule.

    V1 stores RDF terms as strings in a simple quad table. RDFLib handles
    parsing/serialization and pySHACL handles explicit validation.
    """

    def __init__(
        self,
        path: str | Path = ".doxabase.sqlite",
        *,
        initialize: bool = True,
        seed: bool = True,
    ) -> None:
        self.path = Path(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._search_index_error: str | None = None
        if initialize:
            self._ensure_schema()
            self._ensure_default_graphs()
            if seed:
                self.seed_base_graphs()

    @classmethod
    def create(
        cls,
        path: str | Path = ".doxabase.sqlite",
        *,
        overwrite: bool = False,
        seed: bool = True,
    ) -> "DoxaBase":
        db_path = Path(path)
        if overwrite and db_path.exists():
            db_path.unlink()
        return cls(db_path, initialize=True, seed=seed)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "DoxaBase":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def seed_base_graphs(self) -> None:
        for name, _, _, system_seed, source_path in DEFAULT_GRAPHS:
            if not system_seed or source_path is None:
                continue
            if self.triple_count(name) == 0:
                self.import_turtle(source_path, graph=name, replace=True, allow_immutable=True)

    def graph_overview(self, limit: int = 100) -> GraphOverview:
        graph_rows = self._conn.execute(
            """
            SELECT
                ng.name,
                ng.description,
                ng.mutable,
                ng.system_seed,
                ng.source_path,
                COUNT(q.subject) AS triple_count
            FROM named_graphs ng
            LEFT JOIN quads q ON q.graph = ng.name
            GROUP BY ng.name
            ORDER BY ng.system_seed DESC, ng.name
            """
        ).fetchall()
        named_graphs = [
            NamedGraphInfo(
                name=row["name"],
                description=row["description"],
                mutable=bool(row["mutable"]),
                system_seed=bool(row["system_seed"]),
                source_path=row["source_path"],
                triple_count=int(row["triple_count"]),
            )
            for row in graph_rows
        ]

        class_counts = self._count_objects(str(RDF.type), limit=limit)
        predicate_counts = [
            (row["predicate"], int(row["count"]))
            for row in self._conn.execute(
                """
                SELECT predicate, COUNT(*) AS count
                FROM quads
                GROUP BY predicate
                ORDER BY count DESC, predicate
                LIMIT ?
                """,
                (limit,),
            )
        ]
        key_counts = {
            "datasets": self._count_type("rc:Dataset"),
            "tables": self._count_type("rc:Table"),
            "columns": self._count_type("rc:Column"),
            "observations": self._count_type("rc:Observation")
            + self._count_type("rc:ProfileObservation"),
            "claims": self._count_type("rc:Claim"),
            "patterns": self._count_type("rc:Pattern"),
            "evidence": self._count_type("rc:Evidence"),
            "source_spans": self._count_type("rc:SourceSpan"),
            "graph_revisions": self._count_type("rc:GraphRevision"),
            "graph_patches": self._count_type("rc:GraphPatch"),
            "graph_snapshots": self._count_type("rc:GraphSnapshot"),
            "storage_accesses": self._count_type("rc:StorageAccess"),
            "shapes": self._count_type("sh:NodeShape"),
        }
        return GraphOverview(
            named_graphs=named_graphs,
            class_counts=class_counts,
            predicate_counts=predicate_counts,
            key_counts=key_counts,
            namespaces=PREFIXES.copy(),
        )

    def list_entities(
        self,
        type: str | None = None,
        graph: str | None = "map",
        text: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> EntityList:
        graphs = self._expand_graphs([graph] if graph else None)
        params: list[Any] = []
        graph_filter = ""
        if graphs:
            graph_filter = f"AND q.graph IN ({','.join('?' for _ in graphs)})"
            params.extend(graphs)

        type_filter = ""
        if type:
            type_filter = """
                AND EXISTS (
                    SELECT 1
                    FROM quads qt
                    WHERE qt.graph = q.graph
                      AND qt.subject = q.subject
                      AND qt.predicate = ?
                      AND qt.object = ?
                )
            """
            params.extend([str(RDF.type), self.expand_iri(type)])

        text_filter = ""
        if text:
            text_filter = """
                AND (
                    lower(q.subject) LIKE ?
                    OR EXISTS (
                        SELECT 1
                        FROM quads ql
                        WHERE ql.graph = q.graph
                          AND ql.subject = q.subject
                          AND ql.object_kind = 'literal'
                          AND lower(ql.object) LIKE ?
                    )
                )
            """
            needle = f"%{text.lower()}%"
            params.extend([needle, needle])

        params.extend([limit, offset])
        rows = self._conn.execute(
            f"""
            SELECT q.graph, q.subject
            FROM quads q
            WHERE q.subject_kind IN ('uri', 'bnode')
              {graph_filter}
              {type_filter}
              {text_filter}
            GROUP BY q.graph, q.subject
            ORDER BY q.subject
            LIMIT ? OFFSET ?
            """,
            params,
        ).fetchall()

        entities = [
            EntityRow(
                iri=row["subject"],
                label=self._display_label_from_graphs(
                    self._lookup_graphs([row["graph"]]),
                    row["subject"],
                ),
                types=self._types(row["graph"], row["subject"]),
                graph=row["graph"],
            )
            for row in rows
        ]
        return EntityList(entities=entities, limit=limit, offset=offset)

    def describe_resource(
        self,
        iri: str,
        *,
        graph: str | None = None,
        include_incoming: bool = True,
        limit: int = 100,
    ) -> ResourceContext:
        if limit < 1:
            raise DoxaBaseError("Resource context limit must be at least 1")
        resource_iri = self.expand_iri(iri)
        graphs = self._expand_graphs([graph] if graph else None)
        lookup_graphs = self._lookup_graphs(graphs)
        types = self._types_from_graphs(graphs, resource_iri)
        claim = (
            self._describe_claim(resource_iri, graphs, lookup_graphs)
            if self.expand_iri("rc:Claim") in types
            else None
        )
        return ResourceContext(
            iri=resource_iri,
            graph=graph,
            label=self._display_label_from_graphs(lookup_graphs, resource_iri),
            description=self._description_from_graphs(lookup_graphs, resource_iri),
            types=types,
            claim=claim,
            outgoing=self._resource_triples(
                graphs,
                subject=resource_iri,
                limit=limit,
            ),
            incoming=(
                self._resource_triples(
                    graphs,
                    object_value=resource_iri,
                    object_kind="uri",
                    limit=limit,
                )
                if include_incoming
                else []
            ),
            limit=limit,
        )

    def describe_graph_revision(
        self,
        iri: str,
        *,
        graph: str | None = "history",
    ) -> GraphRevisionDescription:
        revision_iri = self.expand_iri(iri)
        data_graphs = self._expand_graphs([graph] if graph else None)
        lookup_graphs = self._lookup_graphs(data_graphs)
        if not self._subject_exists(revision_iri, data_graphs):
            graph_label = graph if graph is not None else "all graphs"
            raise DoxaBaseError(f"Graph revision '{iri}' was not found in {graph_label}")
        if self.expand_iri("rc:GraphRevision") not in self._types_from_graphs(
            data_graphs,
            revision_iri,
        ):
            raise DoxaBaseError(f"Resource '{iri}' is not an rc:GraphRevision")

        revision_type = self._first_object(data_graphs, revision_iri, "rc:revisionType")
        all_lookup_graphs = self._lookup_graphs(self._expand_graphs(["all"]))
        snapshots = self._graph_revision_snapshots(revision_iri, data_graphs)
        included_graphs = self._objects(data_graphs, revision_iri, "rc:includedGraph")
        if not included_graphs:
            included_graphs = [snapshot.graph_role for snapshot in snapshots]

        return GraphRevisionDescription(
            iri=revision_iri,
            graph=graph,
            label=self._display_label_from_graphs(lookup_graphs, revision_iri),
            summary=self._first_object(data_graphs, revision_iri, "rc:summary"),
            revision_type=revision_type,
            revision_type_label=(
                self._label_from_graphs(self._expand_graphs(["ontology"]), revision_type)
                if revision_type is not None
                else None
            ),
            rationale=self._first_object(data_graphs, revision_iri, "rc:revisionRationale"),
            changed_graphs=self._objects(data_graphs, revision_iri, "rc:changedGraph"),
            included_graphs=included_graphs,
            created_at=self._first_object(data_graphs, revision_iri, "rc:createdAt"),
            created_by=self._first_object(data_graphs, revision_iri, "rc:createdBy"),
            export_path=self._first_object(data_graphs, revision_iri, "rc:exportPath"),
            validation_scope=self._first_object(
                data_graphs,
                revision_iri,
                "rc:validationScope",
            ),
            validation_conforms=self._bool_object(
                data_graphs,
                revision_iri,
                "rc:validationConforms",
            ),
            validation_result_count=self._int_object(
                data_graphs,
                revision_iri,
                "rc:validationResultCount",
            ),
            validation_results=self._graph_revision_validation_results(
                revision_iri,
                data_graphs,
            ),
            graph_snapshots=snapshots,
            supporting_observations=self._resource_summaries(
                all_lookup_graphs,
                self._objects(
                    data_graphs,
                    revision_iri,
                    "rc:revisionSupportingObservation",
                ),
            ),
            supporting_claims=self._resource_summaries(
                all_lookup_graphs,
                self._objects(data_graphs, revision_iri, "rc:revisionSupportingClaim"),
            ),
            supporting_patterns=self._resource_summaries(
                all_lookup_graphs,
                self._objects(data_graphs, revision_iri, "rc:revisionSupportingPattern"),
            ),
            revision_anchors=self._resource_summaries(
                all_lookup_graphs,
                self._objects(data_graphs, revision_iri, "rc:revisionAnchor"),
            ),
            evidence=self._resource_summaries(
                all_lookup_graphs,
                self._objects(data_graphs, revision_iri, "rc:evidence"),
            ),
        )

    def describe_staged_revision(
        self,
        iri: str,
        *,
        graph: str | None = "history",
    ) -> StagedGraphRevisionDescription:
        revision_iri = self.expand_iri(iri)
        data_graphs = self._expand_graphs([graph] if graph else None)
        lookup_graphs = self._lookup_graphs(data_graphs)
        if not self._subject_exists(revision_iri, data_graphs):
            graph_label = graph if graph is not None else "all graphs"
            raise DoxaBaseError(
                f"Staged graph revision '{iri}' was not found in {graph_label}"
            )
        if self.expand_iri("rc:GraphRevision") not in self._types_from_graphs(
            data_graphs,
            revision_iri,
        ):
            raise DoxaBaseError(f"Resource '{iri}' is not an rc:GraphRevision")

        patch_iris = self._objects(data_graphs, revision_iri, "rc:hasGraphPatch")
        if not patch_iris:
            raise DoxaBaseError(f"Graph revision '{iri}' has no staged patch entries")

        revision_type = self._first_object(data_graphs, revision_iri, "rc:revisionType")
        revision_stance = self._first_object(
            data_graphs,
            revision_iri,
            "rc:revisionStance",
        )
        alternative_to_iri = self._first_object(
            data_graphs,
            revision_iri,
            "rc:alternativeTo",
        )
        all_lookup_graphs = self._lookup_graphs(self._expand_graphs(["all"]))
        snapshots = self._graph_revision_snapshots(revision_iri, data_graphs)
        included_graphs = self._objects(data_graphs, revision_iri, "rc:includedGraph")
        if not included_graphs:
            included_graphs = [snapshot.graph_role for snapshot in snapshots]
        patches = [
            self._describe_staged_graph_patch(patch_iri, data_graphs)
            for patch_iri in patch_iris
        ]
        patches.sort(key=self._staged_patch_sort_key)

        return StagedGraphRevisionDescription(
            iri=revision_iri,
            graph=graph,
            label=self._display_label_from_graphs(lookup_graphs, revision_iri),
            summary=self._first_object(data_graphs, revision_iri, "rc:summary"),
            revision_type=revision_type,
            revision_type_label=(
                self._label_from_graphs(self._expand_graphs(["ontology"]), revision_type)
                if revision_type is not None
                else None
            ),
            revision_stance=revision_stance,
            revision_stance_label=self._label_for_resource(revision_stance),
            rationale=self._first_object(data_graphs, revision_iri, "rc:revisionRationale"),
            review_note=self._first_object(data_graphs, revision_iri, "rc:reviewNote"),
            review_recommendation=self._first_object(
                data_graphs,
                revision_iri,
                "rc:reviewRecommendation",
            ),
            alternative_to=(
                self._resource_summary(all_lookup_graphs, alternative_to_iri)
                if alternative_to_iri is not None
                else None
            ),
            changed_graphs=self._objects(data_graphs, revision_iri, "rc:changedGraph"),
            included_graphs=included_graphs,
            created_at=self._first_object(data_graphs, revision_iri, "rc:createdAt"),
            created_by=self._first_object(data_graphs, revision_iri, "rc:createdBy"),
            validation_scope=self._first_object(
                data_graphs,
                revision_iri,
                "rc:validationScope",
            ),
            validation_conforms=self._bool_object(
                data_graphs,
                revision_iri,
                "rc:validationConforms",
            ),
            validation_result_count=self._int_object(
                data_graphs,
                revision_iri,
                "rc:validationResultCount",
            ),
            validation_results=self._graph_revision_validation_results(
                revision_iri,
                data_graphs,
            ),
            graph_snapshots=snapshots,
            patches=patches,
            supporting_observations=self._resource_summaries(
                all_lookup_graphs,
                self._objects(
                    data_graphs,
                    revision_iri,
                    "rc:revisionSupportingObservation",
                ),
            ),
            supporting_claims=self._resource_summaries(
                all_lookup_graphs,
                self._objects(data_graphs, revision_iri, "rc:revisionSupportingClaim"),
            ),
            supporting_patterns=self._resource_summaries(
                all_lookup_graphs,
                self._objects(data_graphs, revision_iri, "rc:revisionSupportingPattern"),
            ),
            revision_anchors=self._resource_summaries(
                all_lookup_graphs,
                self._objects(data_graphs, revision_iri, "rc:revisionAnchor"),
            ),
            evidence=self._resource_summaries(
                all_lookup_graphs,
                self._objects(data_graphs, revision_iri, "rc:evidence"),
            ),
        )

    def describe_pattern(
        self,
        iri: str,
        *,
        graph: str | None = "patterns",
    ) -> PatternDescription:
        pattern_iri = self.expand_iri(iri)
        data_graphs = self._expand_graphs([graph] if graph else None)
        lookup_graphs = self._lookup_graphs(data_graphs)
        all_graphs = self._expand_graphs(["all"])
        all_lookup_graphs = self._lookup_graphs(all_graphs)
        if not self._subject_exists(pattern_iri, data_graphs):
            graph_label = graph if graph is not None else "all graphs"
            raise DoxaBaseError(f"Pattern '{iri}' was not found in {graph_label}")
        if self.expand_iri("rc:Pattern") not in self._types_from_graphs(
            data_graphs,
            pattern_iri,
        ):
            raise DoxaBaseError(f"Resource '{iri}' is not an rc:Pattern")

        confidence = self._first_object(data_graphs, pattern_iri, "rc:confidence")
        observation_status = self._first_object(
            data_graphs,
            pattern_iri,
            "rc:observationStatus",
        )
        pattern_stability = self._first_object(
            data_graphs,
            pattern_iri,
            "rc:patternStability",
        )

        return PatternDescription(
            iri=pattern_iri,
            graph=graph,
            label=self._display_label_from_graphs(lookup_graphs, pattern_iri),
            summary=self._first_object(data_graphs, pattern_iri, "rc:summary"),
            pattern_text=self._first_object(data_graphs, pattern_iri, "rc:patternText"),
            rationale=self._first_object(data_graphs, pattern_iri, "rc:rationale"),
            pattern_targets=self._resource_summaries(
                all_lookup_graphs,
                self._objects(data_graphs, pattern_iri, "rc:patternTarget"),
            ),
            supporting_observations=self._resource_summaries(
                all_lookup_graphs,
                self._objects(data_graphs, pattern_iri, "rc:supportingObservation"),
            ),
            supporting_claims=[
                self._describe_claim(claim_iri, all_graphs, all_lookup_graphs)
                for claim_iri in self._objects(
                    data_graphs,
                    pattern_iri,
                    "rc:supportingClaim",
                )
            ],
            evidence=[
                self._describe_evidence(evidence_iri, all_graphs, all_lookup_graphs)
                for evidence_iri in self._objects(data_graphs, pattern_iri, "rc:evidence")
            ],
            confidence=confidence,
            confidence_label=self._label_for_resource(confidence),
            observation_status=observation_status,
            observation_status_label=self._label_for_resource(observation_status),
            pattern_stability=pattern_stability,
            pattern_stability_label=self._label_for_resource(pattern_stability),
            map_implications=self._resource_summaries(
                all_lookup_graphs,
                self._objects(data_graphs, pattern_iri, "rc:mapImplication"),
            ),
        )

    def describe_context_slice(
        self,
        seed_iris: Iterable[str] | str,
        *,
        profile: TypingLiteral[
            "dataset_brief",
            "pattern_brief",
            "deep_lore",
        ] = "dataset_brief",
        max_triples: int = 500,
        include_trig: bool = False,
        graph_iri_prefix: str = RCG_PREFIX,
    ) -> ContextSlice:
        if max_triples < 1:
            raise DoxaBaseError("max_triples must be at least 1")
        if profile not in {"dataset_brief", "pattern_brief", "deep_lore"}:
            raise DoxaBaseError(
                "profile must be 'dataset_brief', 'pattern_brief', or 'deep_lore'"
            )

        seeds = [
            self.expand_iri(seed)
            for seed in self._string_values("seed_iris", seed_iris, required=True)
        ]
        all_graphs = self._expand_graphs(["all"])
        all_lookup_graphs = self._lookup_graphs(all_graphs)
        resources: dict[str, list[ContextSliceRoute]] = {}
        dataset_contexts: dict[str, DatasetDescription] = {}
        pattern_contexts: dict[str, PatternDescription] = {}
        described_datasets: set[str] = set()
        described_patterns: set[str] = set()
        described_claims: set[str] = set()
        described_observations: set[str] = set()
        described_evidence: set[str] = set()
        warnings: list[str] = []

        def add_resource(
            iri: str | None,
            route: str,
            route_label: str,
            *,
            source_iri: str | None = None,
            depth: int = 0,
        ) -> None:
            if iri is None:
                return
            expanded_iri = self.expand_iri(iri)
            source_label = (
                self._display_label_from_graphs(all_lookup_graphs, source_iri)
                if source_iri is not None
                else None
            )
            route_record = ContextSliceRoute(
                route=route,
                route_label=route_label,
                source_iri=source_iri,
                source_label=source_label,
                depth=depth,
            )
            existing = resources.setdefault(expanded_iri, [])
            route_key = (
                route_record.route,
                route_record.source_iri,
                route_record.depth,
            )
            if not any(
                (item.route, item.source_iri, item.depth) == route_key
                for item in existing
            ):
                existing.append(route_record)

        def add_summary(
            summary: ResourceSummary | None,
            route: str,
            route_label: str,
            *,
            source_iri: str | None = None,
            depth: int = 0,
        ) -> None:
            if summary is not None:
                add_resource(
                    summary.iri,
                    route,
                    route_label,
                    source_iri=source_iri,
                    depth=depth,
                )

        def add_claim(claim_iri: str, source_iri: str | None, depth: int) -> None:
            if claim_iri in described_claims:
                add_resource(
                    claim_iri,
                    "supporting_claim",
                    "supporting claim",
                    source_iri=source_iri,
                    depth=depth,
                )
                return
            described_claims.add(claim_iri)
            add_resource(
                claim_iri,
                "supporting_claim",
                "supporting claim",
                source_iri=source_iri,
                depth=depth,
            )
            claim = self._describe_claim(claim_iri, all_graphs, all_lookup_graphs)
            for target in claim.claim_targets:
                add_summary(
                    target,
                    "claim_target",
                    "claim target",
                    source_iri=claim_iri,
                    depth=depth + 1,
                )
            for proposed in claim.proposed_assertions:
                add_summary(
                    proposed,
                    "proposed_assertion",
                    "proposed assertion",
                    source_iri=claim_iri,
                    depth=depth + 1,
                )
            for reconsideration in claim.outgoing_reconsiderations:
                add_resource(
                    reconsideration.iri,
                    "claim_reconsideration",
                    "claim reconsideration",
                    source_iri=claim_iri,
                    depth=depth + 1,
                )
                add_summary(
                    reconsideration.older_claim,
                    "reconsidered_claim",
                    "reconsidered claim",
                    source_iri=reconsideration.iri,
                    depth=depth + 2,
                )
                for evidence in reconsideration.evidence:
                    add_evidence(evidence.iri, reconsideration.iri, depth + 2)
            for reconsideration in claim.incoming_reconsiderations:
                add_resource(
                    reconsideration.iri,
                    "incoming_claim_reconsideration",
                    "incoming claim reconsideration",
                    source_iri=claim_iri,
                    depth=depth + 1,
                )
                add_summary(
                    reconsideration.newer_claim,
                    "reconsidering_claim",
                    "reconsidering claim",
                    source_iri=reconsideration.iri,
                    depth=depth + 2,
                )
                for evidence in reconsideration.evidence:
                    add_evidence(evidence.iri, reconsideration.iri, depth + 2)
            for observation_iri in self._subjects(
                all_graphs,
                "rc:hasClaim",
                claim_iri,
            ):
                add_observation(observation_iri, claim_iri, depth + 1)

        def add_evidence(evidence_iri: str, source_iri: str | None, depth: int) -> None:
            if evidence_iri in described_evidence:
                add_resource(
                    evidence_iri,
                    "evidence",
                    "evidence",
                    source_iri=source_iri,
                    depth=depth,
                )
                return
            described_evidence.add(evidence_iri)
            add_resource(
                evidence_iri,
                "evidence",
                "evidence",
                source_iri=source_iri,
                depth=depth,
            )
            for span_iri in self._objects(all_graphs, evidence_iri, "rc:sourceSpan"):
                add_resource(
                    span_iri,
                    "source_span",
                    "source span",
                    source_iri=evidence_iri,
                    depth=depth + 1,
                )

        def add_observation(
            observation_iri: str,
            source_iri: str | None,
            depth: int,
        ) -> None:
            if observation_iri in described_observations:
                add_resource(
                    observation_iri,
                    "supporting_observation",
                    "supporting observation",
                    source_iri=source_iri,
                    depth=depth,
                )
                return
            described_observations.add(observation_iri)
            add_resource(
                observation_iri,
                "supporting_observation",
                "supporting observation",
                source_iri=source_iri,
                depth=depth,
            )
            for predicate, route, label in (
                ("rc:observedAsset", "observed_asset", "observed asset"),
                ("rc:observedColumn", "observed_column", "observed column"),
            ):
                for observed_iri in self._objects(all_graphs, observation_iri, predicate):
                    add_resource(
                        observed_iri,
                        route,
                        label,
                        source_iri=observation_iri,
                        depth=depth + 1,
                    )
            for claim_iri in self._objects(all_graphs, observation_iri, "rc:hasClaim"):
                add_claim(claim_iri, observation_iri, depth + 1)
            for evidence_iri in self._objects(all_graphs, observation_iri, "rc:evidence"):
                add_evidence(evidence_iri, observation_iri, depth + 1)

        def add_pattern(pattern_iri: str, source_iri: str | None, depth: int) -> None:
            if pattern_iri in described_patterns:
                add_resource(
                    pattern_iri,
                    "linked_pattern",
                    "linked pattern",
                    source_iri=source_iri,
                    depth=depth,
                )
                return
            described_patterns.add(pattern_iri)
            add_resource(
                pattern_iri,
                "linked_pattern",
                "linked pattern",
                source_iri=source_iri,
                depth=depth,
            )
            try:
                pattern = self.describe_pattern(pattern_iri, graph="patterns")
            except DoxaBaseError as exc:
                warnings.append(str(exc))
                return
            pattern_contexts[pattern.iri] = pattern
            for target in pattern.pattern_targets:
                add_summary(
                    target,
                    "pattern_target",
                    "pattern target",
                    source_iri=pattern_iri,
                    depth=depth + 1,
                )
                add_owner_dataset_for_column(target.iri, pattern_iri, depth + 2)
            for implication in pattern.map_implications:
                add_summary(
                    implication,
                    "map_implication",
                    "map implication",
                    source_iri=pattern_iri,
                    depth=depth + 1,
                )
            for observation in pattern.supporting_observations:
                add_observation(observation.iri, pattern_iri, depth + 1)
            for claim in pattern.supporting_claims:
                add_claim(claim.iri, pattern_iri, depth + 1)
            for evidence in pattern.evidence:
                add_evidence(evidence.iri, pattern_iri, depth + 1)

        def add_owner_dataset_for_column(
            iri: str,
            source_iri: str | None,
            depth: int,
        ) -> None:
            owner = self._first_owner_dataset_iri(all_graphs, iri)
            if owner is not None:
                add_resource(
                    owner,
                    "owning_dataset",
                    "owning dataset",
                    source_iri=source_iri,
                    depth=depth,
                )

        def add_relationship(relationship: RelationshipDescription, depth: int) -> None:
            add_resource(
                relationship.iri,
                "dataset_relationship",
                "dataset relationship",
                source_iri=relationship.iri,
                depth=depth,
            )
            for summary in (
                relationship.source_dataset,
                relationship.target_dataset,
                relationship.foreign_key_from,
                relationship.foreign_key_to,
                relationship.referential_integrity,
                relationship.derivation_function,
            ):
                add_summary(
                    summary,
                    "relationship_resource",
                    "relationship resource",
                    source_iri=relationship.iri,
                    depth=depth + 1,
                )
            for collection in (
                relationship.identifying_columns,
                relationship.source_columns,
                relationship.derived_columns,
                relationship.derivation_properties,
            ):
                for summary in collection:
                    add_summary(
                        summary,
                        "relationship_resource",
                        "relationship resource",
                        source_iri=relationship.iri,
                        depth=depth + 1,
                    )

        def add_dataset(dataset_iri: str, source_iri: str | None, depth: int) -> None:
            add_resource(
                dataset_iri,
                "seed_dataset" if source_iri is None else "related_dataset",
                "seed dataset" if source_iri is None else "related dataset",
                source_iri=source_iri,
                depth=depth,
            )
            if dataset_iri in described_datasets:
                return
            described_datasets.add(dataset_iri)
            try:
                dataset = self.describe_dataset(dataset_iri, graph="map")
            except DoxaBaseError as exc:
                warnings.append(str(exc))
                return
            dataset_contexts[dataset.iri] = dataset
            for summary in (
                dataset.row_semantics,
                dataset.entity_key,
                dataset.snapshot_timestamp,
                dataset.schema_stability,
            ):
                add_summary(
                    summary,
                    "dataset_semantic_term",
                    "dataset semantic term",
                    source_iri=dataset_iri,
                    depth=depth + 1,
                )
            add_summary(
                dataset.layout_verification_status,
                "layout_verification_status",
                "layout verification status",
                source_iri=dataset_iri,
                depth=depth + 1,
            )
            for column in dataset.columns:
                add_resource(
                    column.iri,
                    "dataset_column",
                    "dataset column",
                    source_iri=dataset_iri,
                    depth=depth + 1,
                )
                add_summary(
                    column.physical_type,
                    "column_type",
                    "column type",
                    source_iri=column.iri,
                    depth=depth + 2,
                )
                add_summary(
                    column.value_type,
                    "column_type",
                    "column type",
                    source_iri=column.iri,
                    depth=depth + 2,
                )
            for layout in dataset.physical_layouts:
                add_resource(
                    layout.iri,
                    "physical_layout",
                    "physical layout",
                    source_iri=dataset_iri,
                    depth=depth + 1,
                )
                add_summary(
                    layout.file_format,
                    "layout_term",
                    "layout term",
                    source_iri=layout.iri,
                    depth=depth + 2,
                )
                add_summary(
                    layout.compression_codec,
                    "layout_term",
                    "layout term",
                    source_iri=layout.iri,
                    depth=depth + 2,
                )
                add_summary(
                    layout.layout_verification_status,
                    "layout_verification_status",
                    "layout verification status",
                    source_iri=layout.iri,
                    depth=depth + 2,
                )
            for access in dataset.storage_accesses:
                add_resource(
                    access.iri,
                    "storage_access",
                    "storage access",
                    source_iri=dataset_iri,
                    depth=depth + 1,
                )
                add_summary(
                    access.storage_protocol,
                    "storage_term",
                    "storage term",
                    source_iri=access.iri,
                    depth=depth + 2,
                )
                add_summary(
                    access.access_mode,
                    "storage_term",
                    "storage term",
                    source_iri=access.iri,
                    depth=depth + 2,
                )
                add_summary(
                    access.layout_verification_status,
                    "layout_verification_status",
                    "layout verification status",
                    source_iri=access.iri,
                    depth=depth + 2,
                )
            for partition in dataset.partition_schemes:
                add_resource(
                    partition.iri,
                    "partition_scheme",
                    "partition scheme",
                    source_iri=dataset_iri,
                    depth=depth + 1,
                )
                add_summary(
                    partition.partition_column,
                    "partition_resource",
                    "partition resource",
                    source_iri=partition.iri,
                    depth=depth + 2,
                )
                add_summary(
                    partition.granularity,
                    "partition_resource",
                    "partition resource",
                    source_iri=partition.iri,
                    depth=depth + 2,
                )
                add_summary(
                    partition.redundant_partition_key,
                    "partition_resource",
                    "partition resource",
                    source_iri=partition.iri,
                    depth=depth + 2,
                )
                add_summary(
                    partition.layout_verification_status,
                    "layout_verification_status",
                    "layout verification status",
                    source_iri=partition.iri,
                    depth=depth + 2,
                )
            for caveat in dataset.caveats:
                add_resource(
                    caveat.iri,
                    "known_caveat",
                    "known caveat",
                    source_iri=dataset_iri,
                    depth=depth + 1,
                )
                add_summary(
                    caveat.severity,
                    "caveat_severity",
                    "caveat severity",
                    source_iri=caveat.iri,
                    depth=depth + 2,
                )
            for provenance in dataset.provenance:
                add_summary(
                    provenance,
                    "provenance",
                    "provenance",
                    source_iri=dataset_iri,
                    depth=depth + 1,
                )
            for transformation in dataset.transformations:
                add_resource(
                    transformation.iri,
                    "transformation",
                    "transformation",
                    source_iri=dataset_iri,
                    depth=depth + 1,
                )
            for related in dataset.related_dataset_groups:
                add_resource(
                    related.iri,
                    "related_dataset",
                    "related dataset",
                    source_iri=dataset_iri,
                    depth=depth + 1,
                )
                for reason in related.reasons:
                    if reason.relationship_iri is not None:
                        add_resource(
                            reason.relationship_iri,
                            "related_dataset_reason",
                            "related dataset reason",
                            source_iri=related.iri,
                            depth=depth + 2,
                        )
                    for column in reason.columns:
                        add_summary(
                            column,
                            "related_dataset_column",
                            "related dataset column",
                            source_iri=related.iri,
                            depth=depth + 2,
                        )
            for relationship in dataset.relationships:
                add_relationship(relationship, depth + 1)
            for reason in dataset.linked_pattern_reasons:
                for group in reason.match_groups:
                    add_summary(
                        group.matched_resource,
                        f"linked_pattern_{group.relevance_tier}",
                        f"linked pattern {group.relevance_tier.replace('_', ' ')}",
                        source_iri=reason.iri,
                        depth=depth + 2,
                    )
            for linked_pattern in dataset.linked_patterns:
                add_pattern(linked_pattern.iri, dataset_iri, depth + 1)

        for seed in seeds:
            if not self._subject_exists(seed, all_graphs):
                raise DoxaBaseError(f"Seed resource '{seed}' was not found")
            add_resource(seed, "seed", "seed resource", depth=0)
            seed_types = self._types_from_graphs(all_graphs, seed)
            if (
                profile in {"dataset_brief", "deep_lore"}
                and (
                    self.expand_iri("rc:Dataset") in seed_types
                    or self.expand_iri("rc:Table") in seed_types
                )
            ):
                add_dataset(seed, None, 0)
            elif (
                profile in {"pattern_brief", "deep_lore"}
                and self.expand_iri("rc:Pattern") in seed_types
            ):
                add_pattern(seed, None, 0)
            elif (
                profile in {"pattern_brief", "deep_lore"}
                and self.expand_iri("rc:Claim") in seed_types
            ):
                add_claim(seed, None, 0)
            else:
                warnings.append(
                    f"Seed '{seed}' was included directly; profile-specific expansion did not apply."
                )

        if profile == "deep_lore":
            self._add_revision_context_for_slice(resources, all_graphs, add_resource)

        resource_iris = self._context_slice_resource_order(resources, all_lookup_graphs)
        triples, candidate_triple_count = self._context_slice_triples(
            self._context_slice_graphs(),
            resource_iris,
            max_triples=max_triples,
        )
        omitted_triple_count = max(candidate_triple_count - len(triples), 0)
        truncated = omitted_triple_count > 0
        trig = (
            self._context_slice_trig(triples, graph_iri_prefix=graph_iri_prefix)
            if include_trig
            else None
        )
        graph_counts: dict[str, int] = {}
        for triple in triples:
            graph_counts[triple.graph] = graph_counts.get(triple.graph, 0) + 1
        route_counts = self._context_slice_route_counts(resources)
        if profile == "deep_lore" and not self._context_slice_has_lore_routes(
            route_counts,
        ):
            warnings.append(
                "deep_lore found no claims, patterns, reconsiderations, "
                "evidence, or revision history beyond map context for these seeds."
            )

        return ContextSlice(
            profile=profile,
            seeds=[
                self._resource_summary(all_lookup_graphs, seed, display_label=True)
                for seed in seeds
            ],
            reading_order=self._context_slice_reading_order(),
            resources=[
                self._context_slice_resource(iri, routes, all_lookup_graphs)
                for iri, routes in self._context_slice_ordered_resources(
                    resources,
                    all_lookup_graphs,
                )
            ],
            resource_count=len(resources),
            route_legend=self._context_slice_route_legend(resources, route_counts),
            route_counts=route_counts,
            graph_counts=graph_counts,
            triples=triples,
            triple_count=len(triples),
            returned_triple_count=len(triples),
            candidate_triple_count=candidate_triple_count,
            omitted_triple_count=omitted_triple_count,
            max_triples=max_triples,
            truncated=truncated,
            truncation_scope="triples_only",
            trig=trig,
            dataset_contexts=list(dataset_contexts.values()),
            pattern_contexts=list(pattern_contexts.values()),
            warnings=warnings,
        )

    def _add_revision_context_for_slice(
        self,
        resources: dict[str, list[ContextSliceRoute]],
        all_graphs: list[str],
        add_resource: Any,
    ) -> None:
        history_graphs = ["history"]
        support_predicates = (
            ("rc:revisionSupportingPattern", "revision_supporting_pattern"),
            ("rc:revisionSupportingClaim", "revision_supporting_claim"),
            ("rc:revisionSupportingObservation", "revision_supporting_observation"),
        )
        for resource_iri in list(resources):
            for predicate, route in support_predicates:
                for revision_iri in self._subjects(
                    history_graphs,
                    predicate,
                    resource_iri,
                ):
                    add_resource(
                        revision_iri,
                        route,
                        "supporting revision",
                        source_iri=resource_iri,
                        depth=3,
                    )
                    for evidence_iri in self._objects(
                        all_graphs,
                        revision_iri,
                        "rc:evidence",
                    ):
                        add_resource(
                            evidence_iri,
                            "revision_evidence",
                            "revision evidence",
                            source_iri=revision_iri,
                            depth=4,
                        )

    def _context_slice_graphs(self) -> list[str]:
        return [
            "base_ontology",
            "ontology",
            "map",
            "observations",
            "patterns",
            "evidence",
            "history",
        ]

    def _context_slice_resource(
        self,
        iri: str,
        routes: list[ContextSliceRoute],
        lookup_graphs: list[str],
    ) -> ContextSliceResource:
        summary = self._resource_summary(lookup_graphs, iri, display_label=True)
        sorted_routes = self._context_slice_sorted_routes(routes)
        graphs = self._graphs_for_subject(self._context_slice_graphs(), iri)
        return ContextSliceResource(
            iri=iri,
            label=summary.label,
            description=summary.description,
            types=self._types_from_graphs(lookup_graphs, iri),
            graphs=graphs,
            referenced_only=not graphs,
            primary_route=sorted_routes[0],
            routes=sorted_routes,
        )

    def _context_slice_resource_order(
        self,
        resources: dict[str, list[ContextSliceRoute]],
        lookup_graphs: list[str],
    ) -> list[str]:
        return [
            iri
            for iri, _routes in self._context_slice_ordered_resources(
                resources,
                lookup_graphs,
            )
        ]

    def _context_slice_ordered_resources(
        self,
        resources: dict[str, list[ContextSliceRoute]],
        lookup_graphs: list[str],
    ) -> list[tuple[str, list[ContextSliceRoute]]]:
        return sorted(
            resources.items(),
            key=lambda item: (
                min(self._context_slice_route_priority(route.route) for route in item[1]),
                min(route.depth for route in item[1]),
                self._display_label_from_graphs(lookup_graphs, item[0]) or "",
                item[0],
            ),
        )

    def _context_slice_sorted_routes(
        self,
        routes: Iterable[ContextSliceRoute],
    ) -> list[ContextSliceRoute]:
        return sorted(
            routes,
            key=lambda route: (
                self._context_slice_route_priority(route.route),
                route.depth,
                route.source_iri or "",
                route.route,
            ),
        )

    def _context_slice_route_priority(self, route: str) -> int:
        exact = {
            "seed": 0,
            "seed_dataset": 1,
            "linked_pattern": 2,
            "pattern_target": 3,
            "map_implication": 4,
            "dataset_column": 5,
            "known_caveat": 6,
            "dataset_relationship": 7,
            "related_dataset_reason": 8,
            "related_dataset": 9,
            "supporting_claim": 10,
            "claim_reconsideration": 11,
            "incoming_claim_reconsideration": 11,
            "reconsidered_claim": 12,
            "reconsidering_claim": 12,
            "supporting_observation": 13,
            "evidence": 14,
            "source_span": 15,
        }
        if route in exact:
            return exact[route]
        if route.startswith("linked_pattern_"):
            return 2
        if route.startswith("revision_"):
            return 14
        if route.endswith("_term"):
            return 20
        return 30

    def _context_slice_route_counts(
        self,
        resources: dict[str, list[ContextSliceRoute]],
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for routes in resources.values():
            for route in routes:
                counts[route.route] = counts.get(route.route, 0) + 1
        return counts

    def _context_slice_has_lore_routes(self, route_counts: Mapping[str, int]) -> bool:
        lore_routes = {
            "linked_pattern",
            "supporting_claim",
            "claim_reconsideration",
            "incoming_claim_reconsideration",
            "reconsidered_claim",
            "reconsidering_claim",
            "supporting_observation",
            "evidence",
            "source_span",
        }
        return any(
            route in lore_routes or route.startswith(("linked_pattern_", "revision_"))
            for route, count in route_counts.items()
            if count > 0
        )

    def _context_slice_reading_order(self) -> list[str]:
        return [
            "Start with seeds to confirm the requested entry points.",
            "Read dataset_contexts and pattern_contexts for compact domain context.",
            "Scan route_counts and route_legend to understand why resources were included.",
            "Read resources in order, using primary_route before secondary routes.",
            "Inspect triples or trig only when exact RDF statements or graph roles matter.",
        ]

    def _context_slice_route_legend(
        self,
        resources: dict[str, list[ContextSliceRoute]],
        route_counts: dict[str, int],
    ) -> list[ContextSliceRouteLegend]:
        labels: dict[str, str] = {}
        for routes in resources.values():
            for route in routes:
                labels.setdefault(route.route, route.route_label)
        return [
            ContextSliceRouteLegend(
                route=route,
                route_label=labels.get(route, route.replace("_", " ")),
                meaning=self._context_slice_route_meaning(route),
                priority=self._context_slice_route_priority(route),
                count=count,
            )
            for route, count in sorted(
                route_counts.items(),
                key=lambda item: (self._context_slice_route_priority(item[0]), item[0]),
            )
        ]

    def _context_slice_route_meaning(self, route: str) -> str:
        meanings = {
            "seed": "The resource the caller asked about directly.",
            "seed_dataset": "A seed resource expanded as a dataset or table.",
            "linked_pattern": (
                "A selected or dataset-linked pattern included for surrounding lore."
            ),
            "pattern_target": "A resource the selected pattern is about.",
            "map_implication": "A map resource or assertion the selected pattern may affect.",
            "dataset_column": "A column belonging to a selected dataset.",
            "known_caveat": "A caveat attached to a selected dataset.",
            "dataset_relationship": "A relationship attached to a selected dataset.",
            "related_dataset_reason": (
                "A relationship or shared identifier explaining a related dataset."
            ),
            "related_dataset": "Another dataset connected to a selected dataset.",
            "related_dataset_column": "A column involved in a related-dataset reason.",
            "relationship_resource": "A resource referenced by a selected dataset relationship.",
            "supporting_claim": "A claim supporting a selected pattern or observation.",
            "claim_target": "A resource a supporting claim is about.",
            "proposed_assertion": "A tentative assertion linked from a supporting claim.",
            "claim_reconsideration": (
                "A reconsideration recorded by the selected claim about an earlier claim."
            ),
            "incoming_claim_reconsideration": (
                "A later reconsideration that weakens, contradicts, supersedes, or refines the selected claim."
            ),
            "reconsidered_claim": "An earlier claim named by a reconsideration.",
            "reconsidering_claim": "A later claim that reconsiders the selected claim.",
            "supporting_observation": "An observation supporting a selected pattern or claim.",
            "observed_asset": "A dataset or asset named by a selected observation.",
            "observed_column": "A column named by a selected observation.",
            "evidence": "Evidence linked to a selected observation, claim, pattern, or revision.",
            "source_span": "A source span attached to selected evidence.",
            "owning_dataset": "The dataset that owns a selected column.",
            "dataset_semantic_term": "A semantic term attached to a selected dataset.",
            "column_type": "A type resource attached to a selected column.",
            "physical_layout": "Physical layout metadata for a selected dataset.",
            "layout_term": "A term used inside selected physical layout metadata.",
            "storage_access": "Storage access metadata for a selected dataset.",
            "storage_term": "A term used inside selected storage metadata.",
            "partition_scheme": "Partition metadata for a selected dataset.",
            "partition_resource": "A resource referenced by selected partition metadata.",
            "layout_verification_status": (
                "A verification-status term attached to dataset, layout, storage, or partition path metadata."
            ),
            "caveat_severity": "A severity term attached to a selected caveat.",
            "provenance": "Provenance metadata attached to a selected dataset.",
            "transformation": "Transformation metadata attached to a selected dataset.",
        }
        if route in meanings:
            return meanings[route]
        if route.startswith("linked_pattern_"):
            tier = route.removeprefix("linked_pattern_").replace("_", " ")
            return f"A resource matched through a linked-pattern relevance route: {tier}."
        if route.startswith("revision_"):
            return "Revision-history metadata connected to selected lore resources."
        if route.endswith("_term"):
            return "A vocabulary term referenced by selected structured context."
        return "A resource included by this profile-specific context route."

    def _context_slice_triples(
        self,
        graphs: list[str],
        resource_iris: Iterable[str],
        *,
        max_triples: int,
    ) -> tuple[list[ResourceTriple], int]:
        triples: list[ResourceTriple] = []
        queue = list(dict.fromkeys(resource_iris))
        seen_subjects: set[str] = set()
        seen_triples: set[
            tuple[str, str, str, str, str, str | None, str | None]
        ] = set()
        candidate_triple_count = 0

        while queue:
            subject = queue.pop(0)
            if subject in seen_subjects:
                continue
            seen_subjects.add(subject)
            subject_count = self._subject_triple_count(graphs, subject)
            for triple in self._resource_triples(
                graphs,
                subject=subject,
                limit=max(subject_count, 1),
            ):
                triple_key = (
                    triple.graph,
                    triple.subject,
                    triple.predicate,
                    triple.object,
                    triple.object_kind,
                    triple.object_datatype,
                    triple.object_lang,
                )
                if triple_key in seen_triples:
                    continue
                seen_triples.add(triple_key)
                candidate_triple_count += 1
                if triple.object_kind == "bnode" and triple.object not in seen_subjects:
                    queue.append(triple.object)
                if len(triples) < max_triples:
                    triples.append(triple)
        return triples, candidate_triple_count

    def _subject_triple_count(self, graphs: list[str], subject: str) -> int:
        graph_filter, params = self._graph_filter(graphs, alias="q")
        row = self._conn.execute(
            f"""
            SELECT COUNT(*) AS count
            FROM quads q
            WHERE q.subject = ?
              {graph_filter}
            """,
            [subject, *params],
        ).fetchone()
        return int(row["count"])

    def _context_slice_trig(
        self,
        triples: Iterable[ResourceTriple],
        *,
        graph_iri_prefix: str,
    ) -> str:
        dataset = Dataset()
        for prefix, namespace in PREFIXES.items():
            dataset.bind(prefix, namespace)
        dataset.bind("rcg", graph_iri_prefix)
        for triple in triples:
            context = dataset.graph(
                URIRef(self._export_graph_identifier(triple.graph, graph_iri_prefix))
            )
            context.add(
                (
                    self._term_from_row(triple.subject, triple.subject_kind),
                    URIRef(triple.predicate),
                    self._resource_triple_object_term(triple),
                )
            )
        return dataset.serialize(format="trig")

    def _resource_triple_object_term(self, triple: ResourceTriple) -> Identifier:
        if triple.object_kind == "uri":
            return URIRef(triple.object)
        if triple.object_kind == "bnode":
            return BNode(triple.object)
        if triple.object_kind == "literal":
            return Literal(
                triple.object,
                lang=triple.object_lang,
                datatype=triple.object_datatype,
            )
        raise TypeError(f"Unsupported object kind: {triple.object_kind}")

    def search(
        self,
        query: str,
        *,
        graph: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> SearchResults:
        if not query.strip():
            raise DoxaBaseError("Search query must not be empty")
        if limit < 1:
            raise DoxaBaseError("Search limit must be at least 1")
        if offset < 0:
            raise DoxaBaseError("Search offset must be non-negative")

        search_tokens = _search_tokens(query)
        fts_query = _fts_query_from_tokens(search_tokens)
        graphs = self._expand_graphs([graph] if graph else None)
        graph_filter, graph_params = self._graph_filter(graphs)
        rows = self._conn.execute(
            f"""
            SELECT
                graph,
                subject,
                predicate,
                text,
                snippet(literal_search, 4, '[', ']', ' ... ', 18) AS snippet
            FROM literal_search
            WHERE literal_search MATCH ?
              {graph_filter}
            ORDER BY bm25(literal_search), graph, subject, predicate
            LIMIT ? OFFSET ?
            """,
            [fts_query, *graph_params, limit, offset],
        ).fetchall()
        if not rows and len(search_tokens) > 1:
            rows = self._co_mentioned_search_rows(
                search_tokens,
                graphs,
                limit=limit,
                offset=offset,
            )

        ontology_graphs = self._expand_graphs(["ontology"])
        matches = [
            SearchMatch(
                iri=row["subject"],
                graph=row["graph"],
                label=self._display_label_from_graphs(
                    self._lookup_graphs([row["graph"]]),
                    row["subject"],
                ),
                types=self._types(row["graph"], row["subject"]),
                predicate=row["predicate"],
                predicate_label=self._label_from_graphs(
                    ontology_graphs,
                    row["predicate"],
                ),
                text=row["text"],
                snippet=row["snippet"],
            )
            for row in rows
        ]
        return SearchResults(
            query=query,
            graph=graph,
            matches=matches,
            limit=limit,
            offset=offset,
        )

    def _co_mentioned_search_rows(
        self,
        tokens: list[str],
        graphs: list[str],
        *,
        limit: int,
        offset: int,
    ) -> list[sqlite3.Row]:
        graph_filter, graph_params = self._graph_filter(graphs)
        fts_query = _fts_or_query_from_tokens(tokens)
        candidate_limit = max((limit + offset) * 20, 100)
        rows = self._conn.execute(
            f"""
            SELECT
                graph,
                subject,
                predicate,
                text,
                snippet(literal_search, 4, '[', ']', ' ... ', 18) AS snippet
            FROM literal_search
            WHERE literal_search MATCH ?
              {graph_filter}
            ORDER BY graph, subject, predicate
            LIMIT ?
            """,
            [fts_query, *graph_params, candidate_limit],
        ).fetchall()
        grouped: dict[str, tuple[set[str], list[sqlite3.Row]]] = {}
        for row in rows:
            matched_tokens = {
                token for token in tokens if token in row["text"].lower()
            }
            if not matched_tokens:
                continue
            context_key = self._search_context_key(graphs, row["subject"])
            token_set, grouped_rows = grouped.setdefault(context_key, (set(), []))
            token_set.update(matched_tokens)
            grouped_rows.append(row)

        required_tokens = set(tokens)
        selected_rows: list[sqlite3.Row] = []
        seen: set[tuple[str, str, str, str]] = set()
        for context_key, (token_set, grouped_rows) in sorted(grouped.items()):
            if not required_tokens.issubset(token_set):
                continue
            for row in grouped_rows:
                row_key = (
                    row["graph"],
                    row["subject"],
                    row["predicate"],
                    row["text"],
                )
                if row_key in seen:
                    continue
                seen.add(row_key)
                selected_rows.append(row)
        return selected_rows[offset : offset + limit]

    def _search_context_key(self, graphs: list[str], subject: str) -> str:
        return self._first_owner_dataset_iri(graphs, subject) or subject

    def describe_dataset(self, iri: str, graph: str | None = "map") -> DatasetDescription:
        dataset_iri = self.expand_iri(iri)
        data_graphs = self._expand_graphs([graph] if graph else None)
        lookup_graphs = self._lookup_graphs(data_graphs)
        if not self._subject_exists(dataset_iri, data_graphs):
            graph_label = graph if graph is not None else "all graphs"
            raise DoxaBaseError(f"Dataset '{iri}' was not found in {graph_label}")

        columns = [
            self._describe_column(column_iri, data_graphs, lookup_graphs)
            for column_iri in self._objects(data_graphs, dataset_iri, "rc:hasColumn")
        ]
        columns.sort(key=lambda column: (column.column_name or "", column.iri))
        column_iris = [column.iri for column in columns]

        physical_layouts = [
            self._describe_physical_layout(layout_iri, data_graphs, lookup_graphs)
            for layout_iri in self._objects(data_graphs, dataset_iri, "rc:hasPhysicalLayout")
        ]
        storage_accesses = [
            self._describe_storage_access(access_iri, data_graphs, lookup_graphs)
            for access_iri in self._objects(data_graphs, dataset_iri, "rc:hasStorageAccess")
        ]
        partition_schemes = [
            self._describe_partition(partition_iri, data_graphs, lookup_graphs)
            for partition_iri in self._objects(data_graphs, dataset_iri, "rc:partitionedBy")
        ]
        direct_path_templates = self._objects(data_graphs, dataset_iri, "rc:pathTemplate")
        access_path_templates = [
            path_template
            for storage_access in storage_accesses
            for path_template in storage_access.path_templates
        ]
        partition_path_templates = [
            partition.path_template
            for partition in partition_schemes
            if partition.path_template is not None
        ]
        path_templates = list(
            dict.fromkeys(
                direct_path_templates + partition_path_templates + access_path_templates
            )
        )
        caveat_iris = self._objects(data_graphs, dataset_iri, "rc:hasKnownCaveat")
        provenance_iris = self._objects(data_graphs, dataset_iri, "rc:hasProvenance")
        relationships = self._relationships_for_dataset(
            dataset_iri,
            column_iris,
            data_graphs,
            lookup_graphs,
        )
        linked_pattern_targets = [
            dataset_iri,
            *column_iris,
            *caveat_iris,
            *(relationship.iri for relationship in relationships),
        ]
        related_datasets = self._related_datasets(
            dataset_iri,
            data_graphs,
            lookup_graphs,
            relationships=relationships,
        )
        linked_pattern_reasons = self._linked_pattern_reasons_for_dataset(
            linked_pattern_targets,
        )
        caveats = [
            self._describe_caveat(caveat_iri, data_graphs, lookup_graphs)
            for caveat_iri in caveat_iris
        ]

        return DatasetDescription(
            iri=dataset_iri,
            graph=graph,
            label=self._label_from_graphs(lookup_graphs, dataset_iri),
            description=self._description_from_graphs(lookup_graphs, dataset_iri),
            types=self._types_from_graphs(data_graphs, dataset_iri),
            row_semantics=self._optional_resource_summary(
                lookup_graphs,
                self._first_object(data_graphs, dataset_iri, "rc:rowSemantics"),
            ),
            entity_key=self._optional_resource_summary(
                lookup_graphs,
                self._first_object(data_graphs, dataset_iri, "rc:entityKey"),
            ),
            snapshot_timestamp=self._optional_resource_summary(
                lookup_graphs,
                self._first_object(data_graphs, dataset_iri, "rc:snapshotTimestamp"),
            ),
            schema_stability=self._optional_resource_summary(
                lookup_graphs,
                self._first_object(data_graphs, dataset_iri, "rc:schemaStability"),
            ),
            row_count_snapshot=self._int_object(
                data_graphs,
                dataset_iri,
                "rc:rowCountSnapshot",
            ),
            layout_verification_status=self._optional_resource_summary(
                lookup_graphs,
                self._first_object(
                    data_graphs,
                    dataset_iri,
                    "rc:layoutVerificationStatus",
                ),
            ),
            layout_verification_note=self._first_object(
                data_graphs,
                dataset_iri,
                "rc:layoutVerificationNote",
            ),
            columns=columns,
            path_templates=path_templates,
            physical_layouts=physical_layouts,
            storage_accesses=storage_accesses,
            partition_schemes=partition_schemes,
            caveats=caveats,
            upstream_caveats=self._upstream_caveats_for_dataset(
                caveat_iris,
                relationships,
            ),
            provenance=[
                self._resource_summary(
                    lookup_graphs,
                    provenance_iri,
                    description_predicate="rc:sourceDescription",
                )
                for provenance_iri in provenance_iris
            ],
            transformations=self._transformations_for_provenance(
                provenance_iris,
                data_graphs,
                lookup_graphs,
            ),
            related_datasets=related_datasets,
            related_dataset_groups=self._related_dataset_groups(
                dataset_iri,
                related_datasets,
                relationships,
            ),
            relationships=relationships,
            linked_patterns=self._linked_patterns_for_dataset(
                linked_pattern_targets,
            ),
            linked_pattern_reasons=linked_pattern_reasons,
        )

    def _upstream_caveats_for_dataset(
        self,
        direct_caveat_iris: Iterable[str],
        relationships: Iterable[RelationshipDescription],
    ) -> list[CaveatDescription]:
        direct_caveat_set = set(direct_caveat_iris)
        upstream_by_iri: dict[str, CaveatDescription] = {}
        for relationship in relationships:
            for caveat in relationship.source_caveats:
                if caveat.iri not in direct_caveat_set:
                    upstream_by_iri.setdefault(caveat.iri, caveat)
        return sorted(
            upstream_by_iri.values(),
            key=lambda caveat: (caveat.label or "", caveat.iri),
        )

    def record_observation(
        self,
        summary: str,
        *,
        observation_type: TypingLiteral["observation", "profile"] = "observation",
        observed_asset: str | None = None,
        observed_column: str | None = None,
        observed_at: datetime | str | None = None,
        observed_by: str | None = None,
        evidence_summary: str | None = None,
        evidence_sources: Iterable[str] | None = None,
        sample_size: int | None = None,
        row_count: int | None = None,
        null_count: int | None = None,
        distinct_count: int | None = None,
        observation_iri: str | None = None,
        evidence_iri: str | None = None,
    ) -> ObservationRecord:
        if not summary.strip():
            raise DoxaBaseError("Observation summary must not be empty")
        observation_class = {
            "observation": "rc:Observation",
            "profile": "rc:ProfileObservation",
        }.get(observation_type)
        if observation_class is None:
            raise DoxaBaseError(
                "observation_type must be either 'observation' or 'profile'"
            )
        for name, value in {
            "sample_size": sample_size,
            "row_count": row_count,
            "null_count": null_count,
            "distinct_count": distinct_count,
        }.items():
            self._ensure_non_negative(name, value)

        evidence_source_values = (
            [evidence_sources]
            if isinstance(evidence_sources, str)
            else list(evidence_sources or [])
        )
        should_write_evidence = bool(
            evidence_summary or evidence_source_values or evidence_iri
        )
        observation_subject = URIRef(observation_iri or self._mint_iri("observation"))
        evidence_subject = (
            URIRef(evidence_iri or self._mint_iri("evidence"))
            if should_write_evidence
            else None
        )

        observation_graph = Graph()
        self._bind_prefixes(observation_graph)
        observation_graph.add(
            (observation_subject, RDF.type, URIRef(self.expand_iri(observation_class)))
        )
        observation_graph.add(
            (observation_subject, URIRef(self.expand_iri("rc:summary")), Literal(summary))
        )
        observation_graph.add(
            (
                observation_subject,
                URIRef(self.expand_iri("rc:observedAt")),
                self._datetime_literal(observed_at),
            )
        )
        if observed_asset is not None:
            observation_graph.add(
                (
                    observation_subject,
                    URIRef(self.expand_iri("rc:observedAsset")),
                    URIRef(self.expand_iri(observed_asset)),
                )
            )
        if observed_column is not None:
            observation_graph.add(
                (
                    observation_subject,
                    URIRef(self.expand_iri("rc:observedColumn")),
                    URIRef(self.expand_iri(observed_column)),
                )
            )
        if observed_by is not None:
            observation_graph.add(
                (
                    observation_subject,
                    URIRef(self.expand_iri("rc:observedBy")),
                    self._resource_or_literal(observed_by),
                )
            )
        for predicate, value in (
            ("rc:sampleSize", sample_size),
            ("rc:rowCount", row_count),
            ("rc:nullCount", null_count),
            ("rc:distinctCount", distinct_count),
        ):
            if value is not None:
                observation_graph.add(
                    (
                        observation_subject,
                        URIRef(self.expand_iri(predicate)),
                        Literal(value, datatype=XSD.integer),
                    )
                )
        if evidence_subject is not None:
            observation_graph.add(
                (
                    observation_subject,
                    URIRef(self.expand_iri("rc:evidence")),
                    evidence_subject,
                )
            )

        evidence_triples = 0
        if evidence_subject is not None:
            evidence_graph = Graph()
            self._bind_prefixes(evidence_graph)
            evidence_graph.add(
                (
                    evidence_subject,
                    RDF.type,
                    URIRef(self.expand_iri("rc:Evidence")),
                )
            )
            if evidence_summary:
                evidence_graph.add(
                    (
                        evidence_subject,
                        URIRef(self.expand_iri("rc:summary")),
                        Literal(evidence_summary),
                    )
                )
            for source in evidence_source_values:
                evidence_graph.add((evidence_subject, DCTERMS.source, Literal(source)))
            evidence_triples = self._insert_graph("evidence", evidence_graph)

        observation_triples = self._insert_graph("observations", observation_graph)
        return ObservationRecord(
            observation_iri=str(observation_subject),
            observation_type=observation_type,
            evidence_iri=str(evidence_subject) if evidence_subject is not None else None,
            observation_triples=observation_triples,
            evidence_triples=evidence_triples,
        )

    def record_claim_observation(
        self,
        summary: str,
        *,
        claim_text: str,
        claim_kind: str,
        claim_targets: Iterable[str] | str,
        observed_asset: str | None = None,
        observed_column: str | None = None,
        observed_at: datetime | str | None = None,
        observed_by: str | None = None,
        evidence_summary: str | None = None,
        evidence_sources: Iterable[str] | str | None = None,
        source_path: str | None = None,
        source_section: str | None = None,
        start_line: int | None = None,
        end_line: int | None = None,
        source_kind: str | None = None,
        confidence: str | None = "rc:MediumConfidence",
        observation_status: str | None = "rc:Tentative",
        proposed_assertions: Iterable[str] | str | None = None,
        observation_iri: str | None = None,
        claim_iri: str | None = None,
        evidence_iri: str | None = None,
        source_span_iri: str | None = None,
    ) -> ClaimObservationRecord:
        if not summary.strip():
            raise DoxaBaseError("Observation summary must not be empty")
        if not claim_text.strip():
            raise DoxaBaseError("Claim text must not be empty")
        claim_kind_value = claim_kind.strip()
        if not claim_kind_value:
            raise DoxaBaseError("claim_kind must not be empty")
        confidence_value = (
            confidence.strip()
            if confidence and confidence.strip()
            else None
        )
        observation_status_value = (
            observation_status.strip()
            if observation_status and observation_status.strip()
            else None
        )
        source_kind_value = (
            source_kind.strip()
            if source_kind and source_kind.strip()
            else None
        )
        claim_target_values = self._string_values(
            "claim_targets",
            claim_targets,
            required=True,
        )
        evidence_source_values = self._string_values(
            "evidence_sources",
            evidence_sources,
        )
        source_path_value = (
            source_path.strip()
            if source_path and source_path.strip()
            else None
        )
        source_section_value = (
            source_section.strip()
            if source_section and source_section.strip()
            else None
        )
        proposed_assertion_values = self._string_values(
            "proposed_assertions",
            proposed_assertions,
        )
        self._validate_resource_values("claim_targets", claim_target_values)
        self._validate_resource_values(
            "proposed_assertions",
            proposed_assertion_values,
        )
        if not evidence_source_values and source_path_value is None:
            raise DoxaBaseError(
                "record_claim_observation requires evidence_sources or source_path"
            )
        for name, value in {"start_line": start_line, "end_line": end_line}.items():
            if value is not None and value < 1:
                raise DoxaBaseError(f"{name} must be a positive one-based line number")

        observation_subject = URIRef(observation_iri or self._mint_iri("observation"))
        claim_subject = URIRef(claim_iri or self._mint_iri("claim"))
        evidence_subject = URIRef(evidence_iri or self._mint_iri("evidence"))
        source_span_subject = (
            URIRef(source_span_iri or self._mint_iri("source-span"))
            if source_path_value is not None
            else None
        )

        observation_graph = Graph()
        self._bind_prefixes(observation_graph)
        observation_graph.add(
            (observation_subject, RDF.type, URIRef(self.expand_iri("rc:Observation")))
        )
        observation_graph.add(
            (observation_subject, URIRef(self.expand_iri("rc:summary")), Literal(summary))
        )
        observation_graph.add(
            (
                observation_subject,
                URIRef(self.expand_iri("rc:observedAt")),
                self._datetime_literal(observed_at),
            )
        )
        observation_graph.add(
            (
                observation_subject,
                URIRef(self.expand_iri("rc:evidence")),
                evidence_subject,
            )
        )
        observation_graph.add(
            (
                observation_subject,
                URIRef(self.expand_iri("rc:hasClaim")),
                claim_subject,
            )
        )
        if observation_status_value is not None:
            observation_graph.add(
                (
                    observation_subject,
                    URIRef(self.expand_iri("rc:observationStatus")),
                    URIRef(self.expand_iri(observation_status_value)),
                )
            )
        if observed_asset is not None:
            observation_graph.add(
                (
                    observation_subject,
                    URIRef(self.expand_iri("rc:observedAsset")),
                    URIRef(self.expand_iri(observed_asset)),
                )
            )
        if observed_column is not None:
            observation_graph.add(
                (
                    observation_subject,
                    URIRef(self.expand_iri("rc:observedColumn")),
                    URIRef(self.expand_iri(observed_column)),
                )
            )
        if observed_by is not None:
            observation_graph.add(
                (
                    observation_subject,
                    URIRef(self.expand_iri("rc:observedBy")),
                    self._resource_or_literal(observed_by),
                )
            )

        observation_graph.add(
            (claim_subject, RDF.type, URIRef(self.expand_iri("rc:Claim")))
        )
        observation_graph.add(
            (
                claim_subject,
                URIRef(self.expand_iri("rc:claimKind")),
                URIRef(self.expand_iri(claim_kind_value)),
            )
        )
        observation_graph.add(
            (
                claim_subject,
                URIRef(self.expand_iri("rc:claimText")),
                Literal(claim_text),
            )
        )
        for target in claim_target_values:
            observation_graph.add(
                (
                    claim_subject,
                    URIRef(self.expand_iri("rc:claimTarget")),
                    URIRef(self.expand_iri(target)),
                )
            )
        if confidence_value is not None:
            observation_graph.add(
                (
                    claim_subject,
                    URIRef(self.expand_iri("rc:confidence")),
                    URIRef(self.expand_iri(confidence_value)),
                )
            )
        if observation_status_value is not None:
            observation_graph.add(
                (
                    claim_subject,
                    URIRef(self.expand_iri("rc:observationStatus")),
                    URIRef(self.expand_iri(observation_status_value)),
                )
            )
        for assertion in proposed_assertion_values:
            observation_graph.add(
                (
                    claim_subject,
                    URIRef(self.expand_iri("rc:proposedAssertion")),
                    URIRef(self.expand_iri(assertion)),
                )
            )

        evidence_graph = Graph()
        self._bind_prefixes(evidence_graph)
        evidence_graph.add(
            (evidence_subject, RDF.type, URIRef(self.expand_iri("rc:Evidence")))
        )
        if evidence_summary:
            evidence_graph.add(
                (
                    evidence_subject,
                    URIRef(self.expand_iri("rc:summary")),
                    Literal(evidence_summary),
                )
            )
        for source in evidence_source_values:
            evidence_graph.add((evidence_subject, DCTERMS.source, Literal(source)))
        if source_path_value is not None:
            assert source_span_subject is not None
            evidence_graph.add(
                (
                    evidence_subject,
                    URIRef(self.expand_iri("rc:sourceSpan")),
                    source_span_subject,
                )
            )
            evidence_graph.add(
                (
                    source_span_subject,
                    RDF.type,
                    URIRef(self.expand_iri("rc:SourceSpan")),
                )
            )
            evidence_graph.add(
                (
                    source_span_subject,
                    URIRef(self.expand_iri("rc:sourcePath")),
                    Literal(source_path_value),
                )
            )
            if source_section_value:
                evidence_graph.add(
                    (
                        source_span_subject,
                        URIRef(self.expand_iri("rc:sourceSection")),
                        Literal(source_section_value),
                    )
                )
            if start_line is not None:
                evidence_graph.add(
                    (
                        source_span_subject,
                        URIRef(self.expand_iri("rc:startLine")),
                        Literal(start_line, datatype=XSD.integer),
                    )
                )
            if end_line is not None:
                evidence_graph.add(
                    (
                        source_span_subject,
                        URIRef(self.expand_iri("rc:endLine")),
                        Literal(end_line, datatype=XSD.integer),
                    )
                )
            if source_kind_value is not None:
                evidence_graph.add(
                    (
                        source_span_subject,
                        URIRef(self.expand_iri("rc:sourceKind")),
                        URIRef(self.expand_iri(source_kind_value)),
                    )
                )

        evidence_triples = self._insert_graph("evidence", evidence_graph)
        observation_triples = self._insert_graph("observations", observation_graph)
        return ClaimObservationRecord(
            observation_iri=str(observation_subject),
            claim_iri=str(claim_subject),
            evidence_iri=str(evidence_subject),
            source_span_iri=(
                str(source_span_subject) if source_span_subject is not None else None
            ),
            observation_triples=observation_triples,
            evidence_triples=evidence_triples,
        )

    def record_pattern(
        self,
        summary: str,
        *,
        pattern_text: str,
        rationale: str,
        pattern_targets: Iterable[str] | str,
        supporting_observations: Iterable[str] | str | None = None,
        supporting_claims: Iterable[str] | str | None = None,
        synthesized_at: datetime | str | None = None,
        synthesized_by: str | None = None,
        evidence_summary: str | None = None,
        evidence_sources: Iterable[str] | str | None = None,
        source_path: str | None = None,
        source_section: str | None = None,
        start_line: int | None = None,
        end_line: int | None = None,
        source_kind: str | None = None,
        confidence: str | None = "rc:MediumConfidence",
        pattern_status: str | None = "rc:Tentative",
        pattern_stability: str | None = "rc:EmergingPattern",
        map_implications: Iterable[str] | str | None = None,
        pattern_iri: str | None = None,
        evidence_iri: str | None = None,
        source_span_iri: str | None = None,
    ) -> PatternRecord:
        if not summary.strip():
            raise DoxaBaseError("Pattern summary must not be empty")
        if not pattern_text.strip():
            raise DoxaBaseError("pattern_text must not be empty")
        if not rationale.strip():
            raise DoxaBaseError("rationale must not be empty")

        pattern_target_values = self._string_values(
            "pattern_targets",
            pattern_targets,
            required=True,
        )
        supporting_observation_values = self._string_values(
            "supporting_observations",
            supporting_observations,
        )
        supporting_claim_values = self._string_values(
            "supporting_claims",
            supporting_claims,
        )
        evidence_source_values = self._string_values(
            "evidence_sources",
            evidence_sources,
        )
        map_implication_values = self._string_values(
            "map_implications",
            map_implications,
        )
        self._validate_resource_values("pattern_targets", pattern_target_values)
        self._validate_resource_values(
            "supporting_observations",
            supporting_observation_values,
        )
        self._validate_resource_values("supporting_claims", supporting_claim_values)
        self._validate_resource_values("map_implications", map_implication_values)
        source_path_value = (
            source_path.strip()
            if source_path and source_path.strip()
            else None
        )
        source_section_value = (
            source_section.strip()
            if source_section and source_section.strip()
            else None
        )
        source_kind_value = (
            source_kind.strip()
            if source_kind and source_kind.strip()
            else None
        )
        confidence_value = (
            confidence.strip()
            if confidence and confidence.strip()
            else None
        )
        pattern_status_value = (
            pattern_status.strip()
            if pattern_status and pattern_status.strip()
            else None
        )
        pattern_stability_value = (
            pattern_stability.strip()
            if pattern_stability and pattern_stability.strip()
            else None
        )
        evidence_iri_value = (
            evidence_iri.strip()
            if evidence_iri and evidence_iri.strip()
            else None
        )

        if (
            not supporting_observation_values
            and not supporting_claim_values
            and not evidence_source_values
            and source_path_value is None
            and evidence_iri_value is None
        ):
            raise DoxaBaseError(
                "record_pattern requires supporting_observations, "
                "supporting_claims, evidence_sources, source_path, or evidence_iri"
            )
        if evidence_summary and not evidence_source_values and source_path_value is None:
            raise DoxaBaseError(
                "evidence_summary requires evidence_sources or source_path"
            )
        for name, value in {"start_line": start_line, "end_line": end_line}.items():
            if value is not None and value < 1:
                raise DoxaBaseError(f"{name} must be a positive one-based line number")

        pattern_subject = URIRef(pattern_iri or self._mint_iri("pattern"))
        evidence_subject = (
            URIRef(evidence_iri_value)
            if evidence_iri_value is not None
            else URIRef(self._mint_iri("evidence"))
            if evidence_source_values or source_path_value
            else None
        )
        source_span_subject = (
            URIRef(source_span_iri or self._mint_iri("source-span"))
            if source_path_value is not None
            else None
        )

        pattern_graph = Graph()
        self._bind_prefixes(pattern_graph)
        pattern_graph.add(
            (pattern_subject, RDF.type, URIRef(self.expand_iri("rc:Pattern")))
        )
        pattern_graph.add(
            (pattern_subject, URIRef(self.expand_iri("rc:summary")), Literal(summary))
        )
        pattern_graph.add(
            (
                pattern_subject,
                URIRef(self.expand_iri("rc:patternText")),
                Literal(pattern_text),
            )
        )
        pattern_graph.add(
            (
                pattern_subject,
                URIRef(self.expand_iri("rc:rationale")),
                Literal(rationale),
            )
        )
        pattern_graph.add(
            (
                pattern_subject,
                URIRef(self.expand_iri("rc:synthesizedAt")),
                self._datetime_literal(synthesized_at),
            )
        )
        if synthesized_by is not None:
            pattern_graph.add(
                (
                    pattern_subject,
                    URIRef(self.expand_iri("rc:synthesizedBy")),
                    self._resource_or_literal(synthesized_by),
                )
            )
        for target in pattern_target_values:
            pattern_graph.add(
                (
                    pattern_subject,
                    URIRef(self.expand_iri("rc:patternTarget")),
                    URIRef(self.expand_iri(target)),
                )
            )
        for observation in supporting_observation_values:
            pattern_graph.add(
                (
                    pattern_subject,
                    URIRef(self.expand_iri("rc:supportingObservation")),
                    URIRef(self.expand_iri(observation)),
                )
            )
        for claim in supporting_claim_values:
            pattern_graph.add(
                (
                    pattern_subject,
                    URIRef(self.expand_iri("rc:supportingClaim")),
                    URIRef(self.expand_iri(claim)),
                )
            )
        if evidence_subject is not None:
            pattern_graph.add(
                (
                    pattern_subject,
                    URIRef(self.expand_iri("rc:evidence")),
                    evidence_subject,
                )
            )
        if confidence_value is not None:
            pattern_graph.add(
                (
                    pattern_subject,
                    URIRef(self.expand_iri("rc:confidence")),
                    URIRef(self.expand_iri(confidence_value)),
                )
            )
        if pattern_status_value is not None:
            pattern_graph.add(
                (
                    pattern_subject,
                    URIRef(self.expand_iri("rc:observationStatus")),
                    URIRef(self.expand_iri(pattern_status_value)),
                )
            )
        if pattern_stability_value is not None:
            pattern_graph.add(
                (
                    pattern_subject,
                    URIRef(self.expand_iri("rc:patternStability")),
                    URIRef(self.expand_iri(pattern_stability_value)),
                )
            )
        for implication in map_implication_values:
            pattern_graph.add(
                (
                    pattern_subject,
                    URIRef(self.expand_iri("rc:mapImplication")),
                    URIRef(self.expand_iri(implication)),
                )
            )

        evidence_triples = 0
        if evidence_subject is not None and (evidence_source_values or source_path_value):
            evidence_graph = Graph()
            self._bind_prefixes(evidence_graph)
            evidence_graph.add(
                (evidence_subject, RDF.type, URIRef(self.expand_iri("rc:Evidence")))
            )
            if evidence_summary:
                evidence_graph.add(
                    (
                        evidence_subject,
                        URIRef(self.expand_iri("rc:summary")),
                        Literal(evidence_summary),
                    )
                )
            for source in evidence_source_values:
                evidence_graph.add((evidence_subject, DCTERMS.source, Literal(source)))
            if source_path_value is not None:
                assert source_span_subject is not None
                evidence_graph.add(
                    (
                        evidence_subject,
                        URIRef(self.expand_iri("rc:sourceSpan")),
                        source_span_subject,
                    )
                )
                evidence_graph.add(
                    (
                        source_span_subject,
                        RDF.type,
                        URIRef(self.expand_iri("rc:SourceSpan")),
                    )
                )
                evidence_graph.add(
                    (
                        source_span_subject,
                        URIRef(self.expand_iri("rc:sourcePath")),
                        Literal(source_path_value),
                    )
                )
                if source_section_value:
                    evidence_graph.add(
                        (
                            source_span_subject,
                            URIRef(self.expand_iri("rc:sourceSection")),
                            Literal(source_section_value),
                        )
                    )
                if start_line is not None:
                    evidence_graph.add(
                        (
                            source_span_subject,
                            URIRef(self.expand_iri("rc:startLine")),
                            Literal(start_line, datatype=XSD.integer),
                        )
                    )
                if end_line is not None:
                    evidence_graph.add(
                        (
                            source_span_subject,
                            URIRef(self.expand_iri("rc:endLine")),
                            Literal(end_line, datatype=XSD.integer),
                        )
                    )
                if source_kind_value is not None:
                    evidence_graph.add(
                        (
                            source_span_subject,
                            URIRef(self.expand_iri("rc:sourceKind")),
                            URIRef(self.expand_iri(source_kind_value)),
                        )
                    )
            evidence_triples = self._insert_graph("evidence", evidence_graph)

        pattern_triples = self._insert_graph("patterns", pattern_graph)
        return PatternRecord(
            pattern_iri=str(pattern_subject),
            evidence_iri=str(evidence_subject) if evidence_subject is not None else None,
            source_span_iri=(
                str(source_span_subject) if source_span_subject is not None else None
            ),
            pattern_triples=pattern_triples,
            evidence_triples=evidence_triples,
        )

    def record_claim_reconsideration(
        self,
        *,
        newer_claim: str,
        older_claim: str,
        relation: TypingLiteral[
            "weakens",
            "contradicts",
            "supersedes",
            "refines",
        ]
        | str,
        rationale: str,
        summary: str | None = None,
        reconsidered_at: datetime | str | None = None,
        reconsidered_by: str | None = None,
        evidence_summary: str | None = None,
        evidence_sources: Iterable[str] | str | None = None,
        source_path: str | None = None,
        source_section: str | None = None,
        start_line: int | None = None,
        end_line: int | None = None,
        source_kind: str | None = None,
        older_claim_status: str | None = None,
        reconsideration_iri: str | None = None,
        evidence_iri: str | None = None,
        source_span_iri: str | None = None,
    ) -> ClaimReconsiderationRecord:
        if not rationale.strip():
            raise DoxaBaseError("reconsideration rationale must not be empty")
        newer_claim_iri = str(self._resource_ref("newer_claim", newer_claim))
        older_claim_iri = str(self._resource_ref("older_claim", older_claim))
        if newer_claim_iri == older_claim_iri:
            raise DoxaBaseError("newer_claim and older_claim must be different")
        relation_iri, direct_predicate, default_status = (
            self._claim_reconsideration_relation(relation)
        )
        status_value = (
            older_claim_status.strip()
            if older_claim_status and older_claim_status.strip()
            else default_status
        )
        self._ensure_claim_resource("newer_claim", newer_claim_iri)
        self._ensure_claim_resource("older_claim", older_claim_iri)
        if status_value is not None:
            self._resource_ref("older_claim_status", status_value)

        evidence_source_values = self._string_values(
            "evidence_sources",
            evidence_sources,
        )
        source_path_value = (
            source_path.strip()
            if source_path and source_path.strip()
            else None
        )
        source_section_value = (
            source_section.strip()
            if source_section and source_section.strip()
            else None
        )
        source_kind_value = (
            source_kind.strip()
            if source_kind and source_kind.strip()
            else None
        )
        evidence_iri_value = (
            evidence_iri.strip()
            if evidence_iri and evidence_iri.strip()
            else None
        )
        if evidence_summary and not (
            evidence_source_values or source_path_value or evidence_iri_value
        ):
            raise DoxaBaseError(
                "evidence_summary requires evidence_sources, source_path, or evidence_iri"
            )
        for name, value in {"start_line": start_line, "end_line": end_line}.items():
            if value is not None and value < 1:
                raise DoxaBaseError(f"{name} must be a positive one-based line number")

        reconsideration_subject = URIRef(
            reconsideration_iri or self._mint_iri("claim-reconsideration")
        )
        evidence_subject = (
            URIRef(evidence_iri_value)
            if evidence_iri_value is not None
            else URIRef(self._mint_iri("evidence"))
            if evidence_source_values or source_path_value
            else None
        )
        source_span_subject = (
            URIRef(source_span_iri or self._mint_iri("source-span"))
            if source_path_value is not None
            else None
        )
        summary_text = (
            summary.strip()
            if summary and summary.strip()
            else f"{self._label_for_resource(relation_iri) or relation} claim reconsideration"
        )

        reconsideration_graph = Graph()
        self._bind_prefixes(reconsideration_graph)
        reconsideration_graph.add(
            (
                reconsideration_subject,
                RDF.type,
                URIRef(self.expand_iri("rc:ClaimReconsideration")),
            )
        )
        reconsideration_graph.add(
            (
                reconsideration_subject,
                URIRef(self.expand_iri("rc:summary")),
                Literal(summary_text),
            )
        )
        reconsideration_graph.add(
            (
                reconsideration_subject,
                URIRef(self.expand_iri("rc:reconsideringClaim")),
                URIRef(newer_claim_iri),
            )
        )
        reconsideration_graph.add(
            (
                reconsideration_subject,
                URIRef(self.expand_iri("rc:reconsideredClaim")),
                URIRef(older_claim_iri),
            )
        )
        reconsideration_graph.add(
            (
                reconsideration_subject,
                URIRef(self.expand_iri("rc:reconsiderationRelation")),
                URIRef(relation_iri),
            )
        )
        reconsideration_graph.add(
            (
                reconsideration_subject,
                URIRef(self.expand_iri("rc:reconsiderationRationale")),
                Literal(rationale),
            )
        )
        reconsideration_graph.add(
            (
                reconsideration_subject,
                URIRef(self.expand_iri("rc:reconsideredAt")),
                self._datetime_literal(reconsidered_at, name="reconsidered_at"),
            )
        )
        reconsideration_graph.add(
            (
                URIRef(newer_claim_iri),
                URIRef(self.expand_iri(direct_predicate)),
                URIRef(older_claim_iri),
            )
        )
        if reconsidered_by is not None:
            reconsideration_graph.add(
                (
                    reconsideration_subject,
                    URIRef(self.expand_iri("rc:reconsideredBy")),
                    self._resource_or_literal(reconsidered_by),
                )
            )
        if evidence_subject is not None:
            reconsideration_graph.add(
                (
                    reconsideration_subject,
                    URIRef(self.expand_iri("rc:evidence")),
                    evidence_subject,
                )
            )

        evidence_triples = 0
        if evidence_subject is not None and (
            evidence_source_values or source_path_value
        ):
            evidence_graph = Graph()
            self._bind_prefixes(evidence_graph)
            evidence_graph.add(
                (evidence_subject, RDF.type, URIRef(self.expand_iri("rc:Evidence")))
            )
            if evidence_summary:
                evidence_graph.add(
                    (
                        evidence_subject,
                        URIRef(self.expand_iri("rc:summary")),
                        Literal(evidence_summary),
                    )
                )
            for source in evidence_source_values:
                evidence_graph.add((evidence_subject, DCTERMS.source, Literal(source)))
            if source_path_value is not None:
                assert source_span_subject is not None
                evidence_graph.add(
                    (
                        evidence_subject,
                        URIRef(self.expand_iri("rc:sourceSpan")),
                        source_span_subject,
                    )
                )
                evidence_graph.add(
                    (
                        source_span_subject,
                        RDF.type,
                        URIRef(self.expand_iri("rc:SourceSpan")),
                    )
                )
                evidence_graph.add(
                    (
                        source_span_subject,
                        URIRef(self.expand_iri("rc:sourcePath")),
                        Literal(source_path_value),
                    )
                )
                if source_section_value:
                    evidence_graph.add(
                        (
                            source_span_subject,
                            URIRef(self.expand_iri("rc:sourceSection")),
                            Literal(source_section_value),
                        )
                    )
                if start_line is not None:
                    evidence_graph.add(
                        (
                            source_span_subject,
                            URIRef(self.expand_iri("rc:startLine")),
                            Literal(start_line, datatype=XSD.integer),
                        )
                    )
                if end_line is not None:
                    evidence_graph.add(
                        (
                            source_span_subject,
                            URIRef(self.expand_iri("rc:endLine")),
                            Literal(end_line, datatype=XSD.integer),
                        )
                    )
                if source_kind_value is not None:
                    evidence_graph.add(
                        (
                            source_span_subject,
                            URIRef(self.expand_iri("rc:sourceKind")),
                            URIRef(self.expand_iri(source_kind_value)),
                        )
                    )
            evidence_triples = self._insert_graph("evidence", evidence_graph)

        reconsideration_triples = self._insert_graph(
            "observations",
            reconsideration_graph,
        )
        status_triples = 0
        if status_value is not None:
            status_graph = Graph()
            self._bind_prefixes(status_graph)
            status_graph.add(
                (
                    URIRef(older_claim_iri),
                    URIRef(self.expand_iri("rc:observationStatus")),
                    URIRef(self.expand_iri(status_value)),
                )
            )
            status_triples = self._replace_subject_triples(
                "observations",
                older_claim_iri,
                [self.expand_iri("rc:observationStatus")],
                status_graph,
            )

        return ClaimReconsiderationRecord(
            reconsideration_iri=str(reconsideration_subject),
            newer_claim_iri=newer_claim_iri,
            older_claim_iri=older_claim_iri,
            relation=relation_iri,
            relation_label=self._label_for_resource(relation_iri),
            direct_predicate=self.expand_iri(direct_predicate),
            older_claim_status=(
                self.expand_iri(status_value) if status_value is not None else None
            ),
            evidence_iri=str(evidence_subject) if evidence_subject is not None else None,
            source_span_iri=(
                str(source_span_subject) if source_span_subject is not None else None
            ),
            reconsideration_triples=reconsideration_triples,
            evidence_triples=evidence_triples,
            status_triples=status_triples,
        )

    def record_map_dataset(
        self,
        iri: str,
        *,
        label: str | None = None,
        description: str | None = None,
        is_table: bool | None = None,
        columns: Iterable[str] | str | None = None,
        path_templates: Iterable[str] | str | None = None,
        row_count_snapshot: int | None = None,
        row_semantics: str | None = None,
        entity_key: str | None = None,
        schema_stability: str | None = None,
        layout_verification_status: str | None = None,
        layout_verification_note: str | None = None,
        caveats: Iterable[str] | str | None = None,
        storage_accesses: Iterable[str] | str | None = None,
        physical_layouts: Iterable[str] | str | None = None,
        companion_datasets: Iterable[str] | str | None = None,
        extra_types: Iterable[str] | str | None = None,
    ) -> MapResourceRecord:
        dataset_iri = self._required_iri("iri", iri)
        self._ensure_non_negative("row_count_snapshot", row_count_snapshot)
        column_values = self._string_values("columns", columns)
        path_template_values = self._string_values("path_templates", path_templates)
        caveat_values = self._string_values("caveats", caveats)
        storage_access_values = self._string_values("storage_accesses", storage_accesses)
        physical_layout_values = self._string_values("physical_layouts", physical_layouts)
        companion_values = self._string_values("companion_datasets", companion_datasets)
        extra_type_values = self._string_values("extra_types", extra_types)

        dataset_type = self.expand_iri("rc:Dataset")
        table_type = self.expand_iri("rc:Table")
        expanded_extra_types = [
            self.expand_iri(type_value) for type_value in extra_type_values
        ]
        current_types = set(self._types("map", dataset_iri))
        dataset_is_table = is_table is True or (
            is_table is None
            and (table_type in current_types or table_type in expanded_extra_types)
        )

        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(dataset_iri)
        graph.add((subject, RDF.type, URIRef(dataset_type)))
        if dataset_is_table:
            graph.add((subject, RDF.type, URIRef(table_type)))
        for type_value in expanded_extra_types:
            graph.add((subject, RDF.type, URIRef(type_value)))
        self._add_optional_literal(graph, subject, str(RDFS.label), label)
        self._add_optional_literal(graph, subject, str(RDFS.comment), description)
        for column in column_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasColumn")),
                    URIRef(self.expand_iri(column)),
                )
            )
        for path_template in path_template_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:pathTemplate")),
                    Literal(path_template),
                )
            )
        if row_count_snapshot is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:rowCountSnapshot")),
                    Literal(row_count_snapshot, datatype=XSD.integer),
                )
            )
        if row_semantics is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:rowSemantics")),
                    URIRef(self.expand_iri(row_semantics)),
                )
            )
        if entity_key is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:entityKey")),
                    URIRef(self.expand_iri(entity_key)),
                )
            )
        if schema_stability is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:schemaStability")),
                    URIRef(self.expand_iri(schema_stability)),
                )
            )
        if layout_verification_status is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:layoutVerificationStatus")),
                    URIRef(self.expand_iri(layout_verification_status)),
                )
            )
        self._add_optional_literal(
            graph,
            subject,
            "rc:layoutVerificationNote",
            layout_verification_note,
        )
        for caveat in caveat_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasKnownCaveat")),
                    URIRef(self.expand_iri(caveat)),
                )
            )
        for access in storage_access_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasStorageAccess")),
                    URIRef(self.expand_iri(access)),
                )
            )
        for layout in physical_layout_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasPhysicalLayout")),
                    URIRef(self.expand_iri(layout)),
                )
            )
        for companion in companion_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:companionOf")),
                    URIRef(self.expand_iri(companion)),
                )
            )

        predicates: list[str] = []
        if is_table is not None or not current_types:
            predicates.append(str(RDF.type))
        if label is not None:
            predicates.append(str(RDFS.label))
        if description is not None:
            predicates.append(str(RDFS.comment))
        if columns is not None:
            predicates.append(self.expand_iri("rc:hasColumn"))
        if path_templates is not None:
            predicates.append(self.expand_iri("rc:pathTemplate"))
        if row_count_snapshot is not None:
            predicates.append(self.expand_iri("rc:rowCountSnapshot"))
        if row_semantics is not None:
            predicates.append(self.expand_iri("rc:rowSemantics"))
        if entity_key is not None:
            predicates.append(self.expand_iri("rc:entityKey"))
        if schema_stability is not None:
            predicates.append(self.expand_iri("rc:schemaStability"))
        if layout_verification_status is not None:
            predicates.append(self.expand_iri("rc:layoutVerificationStatus"))
        if layout_verification_note is not None:
            predicates.append(self.expand_iri("rc:layoutVerificationNote"))
        if caveats is not None:
            predicates.append(self.expand_iri("rc:hasKnownCaveat"))
        if storage_accesses is not None:
            predicates.append(self.expand_iri("rc:hasStorageAccess"))
        if physical_layouts is not None:
            predicates.append(self.expand_iri("rc:hasPhysicalLayout"))
        if companion_datasets is not None:
            predicates.append(self.expand_iri("rc:companionOf"))
        triples = self._replace_subject_triples("map", dataset_iri, predicates, graph)
        resource_type = table_type if dataset_is_table else dataset_type
        return MapResourceRecord(
            iri=dataset_iri,
            resource_type=resource_type,
            graph="map",
            triples=triples,
        )

    def record_map_column(
        self,
        iri: str,
        *,
        column_name: str,
        table_iri: str | None = None,
        label: str | None = None,
        description: str | None = None,
        physical_type: str | None = None,
        value_type: str | None = None,
        nullable: bool | None = None,
    ) -> MapResourceRecord:
        column_iri = self._required_iri("iri", iri)
        column_name_value = column_name.strip()
        if not column_name_value:
            raise DoxaBaseError("column_name must not be empty")

        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(column_iri)
        graph.add((subject, RDF.type, URIRef(self.expand_iri("rc:Column"))))
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:columnName")),
                Literal(column_name_value),
            )
        )
        self._add_optional_literal(graph, subject, str(RDFS.label), label)
        self._add_optional_literal(graph, subject, str(RDFS.comment), description)
        if physical_type is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:physicalType")),
                    URIRef(self.expand_iri(physical_type)),
                )
            )
        if value_type is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:valueType")),
                    URIRef(self.expand_iri(value_type)),
                )
            )
        if nullable is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:nullable")),
                    Literal(nullable, datatype=XSD.boolean),
                )
            )

        predicates = [
            str(RDF.type),
            self.expand_iri("rc:columnName"),
        ]
        if label is not None:
            predicates.append(str(RDFS.label))
        if description is not None:
            predicates.append(str(RDFS.comment))
        if physical_type is not None:
            predicates.append(self.expand_iri("rc:physicalType"))
        if value_type is not None:
            predicates.append(self.expand_iri("rc:valueType"))
        if nullable is not None:
            predicates.append(self.expand_iri("rc:nullable"))
        triples = self._replace_subject_triples("map", column_iri, predicates, graph)
        if table_iri is not None:
            table_subject = self._required_iri("table_iri", table_iri)
            link_graph = Graph()
            self._bind_prefixes(link_graph)
            link_graph.add(
                (
                    URIRef(table_subject),
                    URIRef(self.expand_iri("rc:hasColumn")),
                    subject,
                )
            )
            triples += self._insert_graph("map", link_graph)
        return MapResourceRecord(
            iri=column_iri,
            resource_type=self.expand_iri("rc:Column"),
            graph="map",
            triples=triples,
        )

    def record_map_caveat(
        self,
        iri: str,
        *,
        description: str,
        label: str | None = None,
        impact: str | None = None,
        severity: str | None = None,
        targets: Iterable[str] | str | None = None,
    ) -> MapResourceRecord:
        caveat_iri = self._required_iri("iri", iri)
        description_value = description.strip()
        if not description_value:
            raise DoxaBaseError("description must not be empty")
        target_values = self._string_values("targets", targets)

        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(caveat_iri)
        graph.add((subject, RDF.type, URIRef(self.expand_iri("rc:KnownCaveat"))))
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:caveatDescription")),
                Literal(description_value),
            )
        )
        self._add_optional_literal(graph, subject, str(RDFS.label), label)
        self._add_optional_literal(graph, subject, "rc:impact", impact)
        if severity is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:severity")),
                    URIRef(self.expand_iri(severity)),
                )
            )

        predicates = [
            str(RDF.type),
            self.expand_iri("rc:caveatDescription"),
        ]
        if label is not None:
            predicates.append(str(RDFS.label))
        if impact is not None:
            predicates.append(self.expand_iri("rc:impact"))
        if severity is not None:
            predicates.append(self.expand_iri("rc:severity"))
        triples = self._replace_subject_triples("map", caveat_iri, predicates, graph)
        if target_values:
            link_graph = Graph()
            self._bind_prefixes(link_graph)
            for target in target_values:
                link_graph.add(
                    (
                        URIRef(self.expand_iri(target)),
                        URIRef(self.expand_iri("rc:hasKnownCaveat")),
                        subject,
                    )
                )
            triples += self._insert_graph("map", link_graph)
        return MapResourceRecord(
            iri=caveat_iri,
            resource_type=self.expand_iri("rc:KnownCaveat"),
            graph="map",
            triples=triples,
        )

    def record_map_storage_access(
        self,
        iri: str,
        *,
        label: str | None = None,
        description: str | None = None,
        storage_protocol: str | None = None,
        access_mode: str | None = None,
        storage_root: str | None = None,
        endpoint_profile: str | None = None,
        bucket_name: str | None = None,
        key_prefix: str | None = None,
        region: str | None = None,
        path_style_access: bool | None = None,
        credential_reference: str | None = None,
        path_templates: Iterable[str] | str | None = None,
        layout_verification_status: str | None = None,
        layout_verification_note: str | None = None,
        datasets: Iterable[str] | str | None = None,
    ) -> MapResourceRecord:
        access_iri = self._required_iri("iri", iri)
        path_template_values = self._string_values("path_templates", path_templates)
        dataset_values = self._string_values("datasets", datasets)

        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(access_iri)
        graph.add((subject, RDF.type, URIRef(self.expand_iri("rc:StorageAccess"))))
        self._add_optional_literal(graph, subject, str(RDFS.label), label)
        self._add_optional_literal(graph, subject, str(RDFS.comment), description)
        if storage_protocol is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:storageProtocol")),
                    URIRef(self.expand_iri(storage_protocol)),
                )
            )
        if access_mode is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:accessMode")),
                    URIRef(self.expand_iri(access_mode)),
                )
            )
        for predicate, value in (
            ("rc:storageRoot", storage_root),
            ("rc:endpointProfile", endpoint_profile),
            ("rc:bucketName", bucket_name),
            ("rc:keyPrefix", key_prefix),
            ("rc:region", region),
            ("rc:credentialReference", credential_reference),
        ):
            self._add_optional_literal(graph, subject, predicate, value)
        if path_style_access is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:pathStyleAccess")),
                    Literal(path_style_access, datatype=XSD.boolean),
                )
            )
        for path_template in path_template_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:pathTemplate")),
                    Literal(path_template),
                )
            )
        if layout_verification_status is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:layoutVerificationStatus")),
                    URIRef(self.expand_iri(layout_verification_status)),
                )
            )
        self._add_optional_literal(
            graph,
            subject,
            "rc:layoutVerificationNote",
            layout_verification_note,
        )

        predicates = [str(RDF.type)]
        if label is not None:
            predicates.append(str(RDFS.label))
        if description is not None:
            predicates.append(str(RDFS.comment))
        if storage_protocol is not None:
            predicates.append(self.expand_iri("rc:storageProtocol"))
        if access_mode is not None:
            predicates.append(self.expand_iri("rc:accessMode"))
        if storage_root is not None:
            predicates.append(self.expand_iri("rc:storageRoot"))
        if endpoint_profile is not None:
            predicates.append(self.expand_iri("rc:endpointProfile"))
        if bucket_name is not None:
            predicates.append(self.expand_iri("rc:bucketName"))
        if key_prefix is not None:
            predicates.append(self.expand_iri("rc:keyPrefix"))
        if region is not None:
            predicates.append(self.expand_iri("rc:region"))
        if credential_reference is not None:
            predicates.append(self.expand_iri("rc:credentialReference"))
        if path_style_access is not None:
            predicates.append(self.expand_iri("rc:pathStyleAccess"))
        if path_templates is not None:
            predicates.append(self.expand_iri("rc:pathTemplate"))
        if layout_verification_status is not None:
            predicates.append(self.expand_iri("rc:layoutVerificationStatus"))
        if layout_verification_note is not None:
            predicates.append(self.expand_iri("rc:layoutVerificationNote"))
        triples = self._replace_subject_triples("map", access_iri, predicates, graph)
        if dataset_values:
            link_graph = Graph()
            self._bind_prefixes(link_graph)
            for dataset in dataset_values:
                link_graph.add(
                    (
                        URIRef(self.expand_iri(dataset)),
                        URIRef(self.expand_iri("rc:hasStorageAccess")),
                        subject,
                    )
                )
            triples += self._insert_graph("map", link_graph)
        return MapResourceRecord(
            iri=access_iri,
            resource_type=self.expand_iri("rc:StorageAccess"),
            graph="map",
            triples=triples,
        )

    def record_map_physical_layout(
        self,
        iri: str,
        *,
        label: str | None = None,
        description: str | None = None,
        file_format: str | None = None,
        compression_codec: str | None = None,
        layout_verification_status: str | None = None,
        layout_verification_note: str | None = None,
        datasets: Iterable[str] | str | None = None,
    ) -> MapResourceRecord:
        layout_iri = self._required_iri("iri", iri)
        dataset_values = self._string_values("datasets", datasets)

        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(layout_iri)
        graph.add((subject, RDF.type, URIRef(self.expand_iri("rc:PhysicalLayout"))))
        self._add_optional_literal(graph, subject, str(RDFS.label), label)
        self._add_optional_literal(graph, subject, str(RDFS.comment), description)
        if file_format is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:fileFormat")),
                    URIRef(self.expand_iri(file_format)),
                )
            )
        if compression_codec is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:compressionCodec")),
                    URIRef(self.expand_iri(compression_codec)),
                )
            )
        if layout_verification_status is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:layoutVerificationStatus")),
                    URIRef(self.expand_iri(layout_verification_status)),
                )
            )
        self._add_optional_literal(
            graph,
            subject,
            "rc:layoutVerificationNote",
            layout_verification_note,
        )

        predicates = [str(RDF.type)]
        if label is not None:
            predicates.append(str(RDFS.label))
        if description is not None:
            predicates.append(str(RDFS.comment))
        if file_format is not None:
            predicates.append(self.expand_iri("rc:fileFormat"))
        if compression_codec is not None:
            predicates.append(self.expand_iri("rc:compressionCodec"))
        if layout_verification_status is not None:
            predicates.append(self.expand_iri("rc:layoutVerificationStatus"))
        if layout_verification_note is not None:
            predicates.append(self.expand_iri("rc:layoutVerificationNote"))
        triples = self._replace_subject_triples("map", layout_iri, predicates, graph)
        if dataset_values:
            link_graph = Graph()
            self._bind_prefixes(link_graph)
            for dataset in dataset_values:
                link_graph.add(
                    (
                        URIRef(self.expand_iri(dataset)),
                        URIRef(self.expand_iri("rc:hasPhysicalLayout")),
                        subject,
                    )
                )
            triples += self._insert_graph("map", link_graph)
        return MapResourceRecord(
            iri=layout_iri,
            resource_type=self.expand_iri("rc:PhysicalLayout"),
            graph="map",
            triples=triples,
        )

    def record_map_partition_scheme(
        self,
        iri: str,
        *,
        label: str | None = None,
        description: str | None = None,
        partition_columns: Iterable[str] | str | None = None,
        granularity: str | None = None,
        path_template: str | None = None,
        redundant_partition_key: str | None = None,
        layout_verification_status: str | None = None,
        layout_verification_note: str | None = None,
        datasets: Iterable[str] | str | None = None,
    ) -> MapResourceRecord:
        partition_iri = self._required_iri("iri", iri)
        partition_column_values = self._string_values(
            "partition_columns",
            partition_columns,
        )
        dataset_values = self._string_values("datasets", datasets)

        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(partition_iri)
        graph.add((subject, RDF.type, URIRef(self.expand_iri("rc:PartitionScheme"))))
        self._add_optional_literal(graph, subject, str(RDFS.label), label)
        self._add_optional_literal(graph, subject, str(RDFS.comment), description)
        for partition_column in partition_column_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:partitionColumn")),
                    URIRef(self.expand_iri(partition_column)),
                )
            )
        if granularity is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:partitionGranularity")),
                    URIRef(self.expand_iri(granularity)),
                )
            )
        self._add_optional_literal(graph, subject, "rc:pathTemplate", path_template)
        if redundant_partition_key is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:redundantPartitionKey")),
                    URIRef(self.expand_iri(redundant_partition_key)),
                )
            )
        if layout_verification_status is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:layoutVerificationStatus")),
                    URIRef(self.expand_iri(layout_verification_status)),
                )
            )
        self._add_optional_literal(
            graph,
            subject,
            "rc:layoutVerificationNote",
            layout_verification_note,
        )

        predicates = [str(RDF.type)]
        if label is not None:
            predicates.append(str(RDFS.label))
        if description is not None:
            predicates.append(str(RDFS.comment))
        if partition_columns is not None:
            predicates.append(self.expand_iri("rc:partitionColumn"))
        if granularity is not None:
            predicates.append(self.expand_iri("rc:partitionGranularity"))
        if path_template is not None:
            predicates.append(self.expand_iri("rc:pathTemplate"))
        if redundant_partition_key is not None:
            predicates.append(self.expand_iri("rc:redundantPartitionKey"))
        if layout_verification_status is not None:
            predicates.append(self.expand_iri("rc:layoutVerificationStatus"))
        if layout_verification_note is not None:
            predicates.append(self.expand_iri("rc:layoutVerificationNote"))
        triples = self._replace_subject_triples("map", partition_iri, predicates, graph)
        if dataset_values:
            link_graph = Graph()
            self._bind_prefixes(link_graph)
            for dataset in dataset_values:
                link_graph.add(
                    (
                        URIRef(self.expand_iri(dataset)),
                        URIRef(self.expand_iri("rc:partitionedBy")),
                        subject,
                    )
                )
            triples += self._insert_graph("map", link_graph)
        return MapResourceRecord(
            iri=partition_iri,
            resource_type=self.expand_iri("rc:PartitionScheme"),
            graph="map",
            triples=triples,
        )

    def record_map_relationship(
        self,
        iri: str,
        *,
        relationship_type: TypingLiteral[
            "foreign_key",
            "shared_identifier",
            "derivation",
            "aggregation",
        ],
        label: str | None = None,
        description: str | None = None,
        source_dataset: str | None = None,
        target_dataset: str | None = None,
        from_column: str | None = None,
        to_column: str | None = None,
        identifying_columns: Iterable[str] | str | None = None,
        source_columns: Iterable[str] | str | None = None,
        derived_columns: Iterable[str] | str | None = None,
        group_by_columns: Iterable[str] | str | None = None,
        aggregated_columns: (
            Iterable[Mapping[str, Any]] | Mapping[str, Any] | None
        ) = None,
        declared: bool | None = None,
        referential_integrity: str | None = None,
        derivation_function: str | None = None,
        derivation_properties: Iterable[str] | str | None = None,
    ) -> MapResourceRecord:
        relationship_iri = self._required_iri("iri", iri)
        identifying_column_values = self._string_values(
            "identifying_columns",
            identifying_columns,
        )
        source_column_values = self._string_values("source_columns", source_columns)
        derived_column_values = self._string_values("derived_columns", derived_columns)
        group_by_column_values = self._string_values(
            "group_by_columns",
            group_by_columns,
        )
        aggregated_column_values = self._normalise_aggregated_column_specs(
            aggregated_columns,
        )
        derivation_property_values = self._string_values(
            "derivation_properties",
            derivation_properties,
        )
        type_map = {
            "foreign_key": "rc:ForeignKey",
            "shared_identifier": "rc:SharedIdentifier",
            "derivation": "rc:Derivation",
            "aggregation": "rc:Aggregation",
        }
        resource_type = type_map.get(relationship_type)
        if resource_type is None:
            raise DoxaBaseError(
                "relationship_type must be 'foreign_key', 'shared_identifier', "
                "'derivation', or 'aggregation'"
            )
        if relationship_type == "foreign_key" and (from_column is None or to_column is None):
            raise DoxaBaseError(
                "foreign_key relationships require from_column and to_column"
            )
        if relationship_type == "shared_identifier" and len(identifying_column_values) < 2:
            raise DoxaBaseError(
                "shared_identifier relationships require at least two identifying_columns"
            )
        if relationship_type == "derivation" and (
            not source_column_values or not derived_column_values
        ):
            raise DoxaBaseError(
                "derivation relationships require source_columns and derived_columns"
            )
        if relationship_type == "aggregation" and not aggregated_column_values:
            raise DoxaBaseError(
                "aggregation relationships require at least one aggregated_columns entry"
            )

        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(relationship_iri)
        graph.add((subject, RDF.type, URIRef(self.expand_iri(resource_type))))
        self._add_optional_literal(graph, subject, str(RDFS.label), label)
        self._add_optional_literal(graph, subject, str(RDFS.comment), description)
        if source_dataset is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:sourceDataset")),
                    URIRef(self.expand_iri(source_dataset)),
                )
            )
        if target_dataset is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:targetDataset")),
                    URIRef(self.expand_iri(target_dataset)),
                )
            )
        if relationship_type == "foreign_key":
            assert from_column is not None
            assert to_column is not None
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:foreignKeyFrom")),
                    URIRef(self.expand_iri(from_column)),
                )
            )
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:foreignKeyTo")),
                    URIRef(self.expand_iri(to_column)),
                )
            )
            if declared is not None:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:declared")),
                        Literal(declared, datatype=XSD.boolean),
                    )
                )
            if referential_integrity is not None:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:referentialIntegrity")),
                        URIRef(self.expand_iri(referential_integrity)),
                    )
                )
        if relationship_type == "shared_identifier":
            for column in identifying_column_values:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:identifyingColumn")),
                        URIRef(self.expand_iri(column)),
                    )
                )
        if relationship_type == "derivation":
            for column in source_column_values:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:sourceColumn")),
                        URIRef(self.expand_iri(column)),
                    )
                )
            for column in derived_column_values:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:derivedColumn")),
                        URIRef(self.expand_iri(column)),
                    )
                )
            if derivation_function is not None:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:derivationFunction")),
                        URIRef(self.expand_iri(derivation_function)),
                    )
                )
            for derivation_property in derivation_property_values:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:hasDerivationProperty")),
                        URIRef(self.expand_iri(derivation_property)),
                    )
                )

        if relationship_type == "aggregation":
            for column in group_by_column_values:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:groupByColumn")),
                        URIRef(self.expand_iri(column)),
                    )
                )
            for index, aggregated_column in enumerate(aggregated_column_values, start=1):
                mapping_subject = (
                    URIRef(self.expand_iri(aggregated_column["iri"]))
                    if aggregated_column["iri"] is not None
                    else URIRef(f"{relationship_iri}/aggregated-column/{index}")
                )
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:hasAggregatedColumn")),
                        mapping_subject,
                    )
                )
                graph.add(
                    (
                        mapping_subject,
                        RDF.type,
                        URIRef(self.expand_iri("rc:AggregatedColumn")),
                    )
                )
                graph.add(
                    (
                        mapping_subject,
                        URIRef(self.expand_iri("rc:targetColumn")),
                        URIRef(self.expand_iri(aggregated_column["target_column"])),
                    )
                )
                for column in aggregated_column["source_columns"]:
                    graph.add(
                        (
                            mapping_subject,
                            URIRef(self.expand_iri("rc:aggregationSourceColumn")),
                            URIRef(self.expand_iri(column)),
                        )
                    )
                if aggregated_column["aggregation_function"] is not None:
                    graph.add(
                        (
                            mapping_subject,
                            URIRef(self.expand_iri("rc:aggregationFunction")),
                            URIRef(
                                self.expand_iri(
                                    aggregated_column["aggregation_function"]
                                )
                            ),
                        )
                    )
                if aggregated_column["within_group_ordering"] is not None:
                    graph.add(
                        (
                            mapping_subject,
                            URIRef(self.expand_iri("rc:withinGroupOrdering")),
                            URIRef(
                                self.expand_iri(
                                    aggregated_column["within_group_ordering"]
                                )
                            ),
                        )
                    )

        predicates = [
            str(RDF.type),
            str(RDFS.label),
            str(RDFS.comment),
            self.expand_iri("rc:sourceDataset"),
            self.expand_iri("rc:targetDataset"),
            self.expand_iri("rc:foreignKeyFrom"),
            self.expand_iri("rc:foreignKeyTo"),
            self.expand_iri("rc:declared"),
            self.expand_iri("rc:referentialIntegrity"),
            self.expand_iri("rc:identifyingColumn"),
            self.expand_iri("rc:sourceColumn"),
            self.expand_iri("rc:derivedColumn"),
            self.expand_iri("rc:derivationFunction"),
            self.expand_iri("rc:hasDerivationProperty"),
            self.expand_iri("rc:groupByColumn"),
            self.expand_iri("rc:hasAggregatedColumn"),
        ]
        self._delete_existing_aggregated_column_triples(relationship_iri)
        triples = self._replace_subject_triples(
            "map",
            relationship_iri,
            predicates,
            graph,
        )
        return MapResourceRecord(
            iri=relationship_iri,
            resource_type=self.expand_iri(resource_type),
            graph="map",
            triples=triples,
        )

    def _normalise_aggregated_column_specs(
        self,
        value: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
    ) -> list[dict[str, Any]]:
        if value is None:
            return []
        if isinstance(value, Mapping):
            raw_items = [value]
        elif isinstance(value, str):
            raise DoxaBaseError(
                "aggregated_columns must be an object or list of objects"
            )
        else:
            raw_items = list(value)

        normalised: list[dict[str, Any]] = []
        for index, item in enumerate(raw_items, start=1):
            if not isinstance(item, Mapping):
                raise DoxaBaseError("aggregated_columns entries must be objects")
            target_column = str(
                item.get("target_column")
                or item.get("targetColumn")
                or ""
            ).strip()
            if not target_column:
                raise DoxaBaseError(
                    f"aggregated_columns[{index}] requires target_column"
                )
            source_columns = self._string_values(
                f"aggregated_columns[{index}].source_columns",
                item.get("source_columns")
                or item.get("sourceColumns")
                or item.get("aggregation_source_columns")
                or item.get("aggregationSourceColumns")
                or item.get("source_column")
                or item.get("aggregationSourceColumn"),
            )
            if not source_columns:
                raise DoxaBaseError(
                    f"aggregated_columns[{index}] requires source_columns"
                )
            normalised.append(
                {
                    "iri": str(item.get("iri") or item.get("id") or "").strip()
                    or None,
                    "target_column": target_column,
                    "source_columns": source_columns,
                    "aggregation_function": str(
                        item.get("aggregation_function")
                        or item.get("aggregationFunction")
                        or item.get("function")
                        or ""
                    ).strip()
                    or None,
                    "within_group_ordering": str(
                        item.get("within_group_ordering")
                        or item.get("withinGroupOrdering")
                        or item.get("ordering")
                        or ""
                    ).strip()
                    or None,
                }
            )
        return normalised

    def _delete_existing_aggregated_column_triples(self, relationship_iri: str) -> None:
        mapping_iris = self._objects(["map"], relationship_iri, "rc:hasAggregatedColumn")
        if not mapping_iris:
            return
        predicates = [
            str(RDF.type),
            self.expand_iri("rc:targetColumn"),
            self.expand_iri("rc:aggregationSourceColumn"),
            self.expand_iri("rc:aggregationFunction"),
            self.expand_iri("rc:withinGroupOrdering"),
        ]
        placeholders = ",".join("?" for _ in predicates)
        for mapping_iri in mapping_iris:
            self._conn.execute(
                f"""
                DELETE FROM quads
                WHERE graph = ?
                  AND subject = ?
                  AND predicate IN ({placeholders})
                """,
                ["map", mapping_iri, *predicates],
            )
        self._conn.commit()

    def record_graph_revision(
        self,
        summary: str,
        rationale: str,
        changed_graphs: Iterable[str] | str,
        *,
        revision_type: str = "rc:ManualRevision",
        included_graphs: Iterable[str] | str | None = None,
        revision_iri: str | None = None,
        created_at: datetime | str | None = None,
        created_by: str | None = None,
        supporting_observations: Iterable[str] | str | None = None,
        supporting_claims: Iterable[str] | str | None = None,
        supporting_patterns: Iterable[str] | str | None = None,
        revision_anchors: Iterable[str] | str | None = None,
        evidence: Iterable[str] | str | None = None,
        export_path: str | None = None,
        graph_counts: dict[str, int] | None = None,
        validation_scope: str | None = None,
        validation_conforms: bool | None = None,
        validation_result_count: int | None = None,
        validation_results: Iterable[ValidationDiagnostic] | None = None,
    ) -> GraphRevisionRecord:
        summary_value = summary.strip()
        if not summary_value:
            raise DoxaBaseError("summary must not be empty")
        rationale_value = rationale.strip()
        if not rationale_value:
            raise DoxaBaseError("rationale must not be empty")

        changed_graph_values = self._graph_names_for_export(changed_graphs)
        for graph in changed_graph_values:
            self._ensure_mutable(graph)

        if included_graphs is not None:
            included_graph_values = self._graph_names_for_export(included_graphs)
        else:
            included_graph_values = []
        for graph_name in graph_counts or {}:
            if graph_name not in included_graph_values:
                included_graph_values.append(graph_name)
        if not included_graph_values:
            included_graph_values = changed_graph_values

        revision_subject = (
            self._required_iri("revision_iri", revision_iri)
            if revision_iri is not None
            else self._mint_iri("graph-revision")
        )
        revision_type_iri = self.expand_iri(revision_type)
        supporting_observation_values = self._string_values(
            "supporting_observations",
            supporting_observations,
        )
        supporting_claim_values = self._string_values(
            "supporting_claims",
            supporting_claims,
        )
        supporting_pattern_values = self._string_values(
            "supporting_patterns",
            supporting_patterns,
        )
        revision_anchor_values = self._string_values(
            "revision_anchors",
            revision_anchors,
        )
        evidence_values = self._string_values("evidence", evidence)
        self._validate_resource_values(
            "supporting_observations",
            supporting_observation_values,
        )
        self._validate_resource_values("supporting_claims", supporting_claim_values)
        self._validate_resource_values("supporting_patterns", supporting_pattern_values)
        self._validate_resource_values("revision_anchors", revision_anchor_values)
        self._validate_resource_values("evidence", evidence_values)
        self._ensure_non_negative(
            "validation_result_count",
            validation_result_count,
        )
        validation_result_values = list(validation_results or [])
        for graph_name, count in (graph_counts or {}).items():
            self._ensure_non_negative(f"graph_counts[{graph_name}]", count)

        snapshot_counts = graph_counts or self._graph_counts(included_graph_values)
        unknown_count_graphs = [
            graph for graph in snapshot_counts if graph not in self._known_graph_names()
        ]
        if unknown_count_graphs:
            raise DoxaBaseError(
                f"Unknown graph role(s) in graph_counts: {', '.join(sorted(unknown_count_graphs))}"
            )

        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(revision_subject)
        graph.add((subject, RDF.type, URIRef(self.expand_iri("rc:GraphRevision"))))
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:revisionType")),
                URIRef(revision_type_iri),
            )
        )
        graph.add((subject, URIRef(self.expand_iri("rc:summary")), Literal(summary_value)))
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:revisionRationale")),
                Literal(rationale_value),
            )
        )
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:createdAt")),
                self._datetime_literal(created_at, name="created_at"),
            )
        )
        if created_by is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:createdBy")),
                    self._resource_or_literal(created_by),
                )
            )
        for graph_name in changed_graph_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:changedGraph")),
                    Literal(graph_name),
                )
            )
        for graph_name in included_graph_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:includedGraph")),
                    Literal(graph_name),
                )
            )
        for support in supporting_observation_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:revisionSupportingObservation")),
                    URIRef(self.expand_iri(support)),
                )
            )
        for support in supporting_claim_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:revisionSupportingClaim")),
                    URIRef(self.expand_iri(support)),
                )
            )
        for support in supporting_pattern_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:revisionSupportingPattern")),
                    URIRef(self.expand_iri(support)),
                )
            )
        for anchor in revision_anchor_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:revisionAnchor")),
                    URIRef(self.expand_iri(anchor)),
                )
            )
        for evidence_iri in evidence_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:evidence")),
                    URIRef(self.expand_iri(evidence_iri)),
                )
            )
        self._add_optional_literal(graph, subject, "rc:exportPath", export_path)
        self._add_optional_literal(graph, subject, "rc:validationScope", validation_scope)
        if validation_conforms is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:validationConforms")),
                    Literal(validation_conforms, datatype=XSD.boolean),
                )
            )
        if validation_result_count is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:validationResultCount")),
                    Literal(validation_result_count, datatype=XSD.integer),
                )
            )
        for index, result in enumerate(validation_result_values, start=1):
            result_subject = URIRef(
                result.iri or f"{revision_subject}/validation-result/{index}"
            )
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasValidationResult")),
                    result_subject,
                )
            )
            self._add_validation_diagnostic_triples(graph, result_subject, result)

        for index, (graph_name, count) in enumerate(sorted(snapshot_counts.items()), start=1):
            snapshot = URIRef(f"{revision_subject}/snapshot/{index}")
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasGraphSnapshot")),
                    snapshot,
                )
            )
            graph.add((snapshot, RDF.type, URIRef(self.expand_iri("rc:GraphSnapshot"))))
            graph.add(
                (
                    snapshot,
                    URIRef(self.expand_iri("rc:graphRole")),
                    Literal(graph_name),
                )
            )
            graph.add(
                (
                    snapshot,
                    URIRef(self.expand_iri("rc:tripleCount")),
                    Literal(count, datatype=XSD.integer),
                )
            )

        triples = self._insert_graph("history", graph)
        return GraphRevisionRecord(
            revision_iri=revision_subject,
            revision_type=revision_type_iri,
            graph="history",
            triples=triples,
        )

    def stage_graph_revision(
        self,
        summary: str,
        rationale: str,
        *,
        additions: Iterable[Mapping[str, str]] | None = None,
        removals: Iterable[Mapping[str, str]] | None = None,
        stance: str = "rc:CandidateRevision",
        revision_type: str = "rc:StagedRevision",
        included_graphs: Iterable[str] | str | None = None,
        revision_iri: str | None = None,
        created_at: datetime | str | None = None,
        created_by: str | None = None,
        supporting_observations: Iterable[str] | str | None = None,
        supporting_claims: Iterable[str] | str | None = None,
        supporting_patterns: Iterable[str] | str | None = None,
        revision_anchors: Iterable[str] | str | None = None,
        evidence: Iterable[str] | str | None = None,
        alternative_to: str | None = None,
        review_note: str | None = None,
        review_recommendation: str | None = None,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ] = "all",
    ) -> StagedGraphRevisionRecord:
        parsed_patches = self._parse_staged_patch_specs(
            additions=additions,
            removals=removals,
        )
        if not parsed_patches:
            raise DoxaBaseError("stage_graph_revision requires at least one patch")

        stance_iri = self.expand_iri(stance)
        if self.expand_iri("rc:RevisionStance") not in self._types_from_graphs(
            self._expand_graphs(["ontology"]),
            stance_iri,
        ):
            raise DoxaBaseError(
                "stance must be an rc:RevisionStance declared in base or project ontology"
            )

        changed_graph_values = list(
            dict.fromkeys(patch["target_graph"] for patch in parsed_patches)
        )
        for graph_name in changed_graph_values:
            self._ensure_mutable(str(graph_name))

        preview_graphs: dict[str, Graph] = {
            graph_name: self.to_graph([graph_name])
            for graph_name in changed_graph_values
        }
        patch_records: list[StagedGraphPatchRecord] = []
        for patch in parsed_patches:
            target_graph = str(patch["target_graph"])
            patch_graph = patch["graph"]
            if not isinstance(patch_graph, Graph):
                raise DoxaBaseError("Internal staged patch parse error")
            preview = preview_graphs[target_graph]
            before_count = len(preview)
            if patch["operation"] == self.expand_iri("rc:AdditionPatch"):
                for triple in patch_graph:
                    preview.add(triple)
            else:
                for triple in patch_graph:
                    preview.remove(triple)
            after_count = len(preview)
            patch_role = str(patch["patch_role"])
            patch_records.append(
                StagedGraphPatchRecord(
                    patch_iri=str(patch["patch_iri"]),
                    operation=str(patch["operation"]),
                    target_graph=target_graph,
                    format=str(patch["format"]),
                    patch_role=patch_role,
                    triple_count=len(patch_graph),
                    before_triple_count=before_count,
                    after_triple_count=after_count,
                )
            )

        validation = self._validate_graph_preview(
            validation_scope,
            preview_graphs=preview_graphs,
        )
        revision_subject = (
            self._required_iri("revision_iri", revision_iri)
            if revision_iri is not None
            else self._mint_iri("staged-revision")
        )
        graph_counts = {
            graph_name: self.triple_count(graph_name)
            for graph_name in changed_graph_values
        }
        revision_record = self.record_graph_revision(
            summary=summary,
            rationale=rationale,
            changed_graphs=changed_graph_values,
            revision_type=revision_type,
            included_graphs=included_graphs,
            revision_iri=revision_subject,
            created_at=created_at,
            created_by=created_by,
            supporting_observations=supporting_observations,
            supporting_claims=supporting_claims,
            supporting_patterns=supporting_patterns,
            revision_anchors=revision_anchors,
            evidence=evidence,
            graph_counts=graph_counts,
            validation_scope=validation.scope,
            validation_conforms=validation.conforms,
            validation_result_count=validation.result_count,
            validation_results=validation.results,
        )

        metadata = Graph()
        self._bind_prefixes(metadata)
        subject = URIRef(revision_subject)
        metadata.add(
            (
                subject,
                URIRef(self.expand_iri("rc:revisionStance")),
                URIRef(stance_iri),
            )
        )
        self._add_optional_literal(metadata, subject, "rc:reviewNote", review_note)
        self._add_optional_literal(
            metadata,
            subject,
            "rc:reviewRecommendation",
            review_recommendation,
        )
        if alternative_to is not None:
            metadata.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:alternativeTo")),
                    URIRef(self.expand_iri(alternative_to)),
                )
            )
        for patch, patch_record in zip(parsed_patches, patch_records, strict=True):
            patch_subject = URIRef(patch_record.patch_iri)
            metadata.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasGraphPatch")),
                    patch_subject,
                )
            )
            metadata.add(
                (
                    patch_subject,
                    RDF.type,
                    URIRef(self.expand_iri("rc:GraphPatch")),
                )
            )
            metadata.add(
                (
                    patch_subject,
                    URIRef(self.expand_iri("rc:patchOperation")),
                    URIRef(patch_record.operation),
                )
            )
            metadata.add(
                (
                    patch_subject,
                    URIRef(self.expand_iri("rc:targetGraph")),
                    Literal(patch_record.target_graph),
                )
            )
            metadata.add(
                (
                    patch_subject,
                    URIRef(self.expand_iri("rc:patchFormat")),
                    Literal(patch_record.format),
                )
            )
            metadata.add(
                (
                    patch_subject,
                    URIRef(self.expand_iri("rc:patchRole")),
                    URIRef(patch_record.patch_role),
                )
            )
            metadata.add(
                (
                    patch_subject,
                    URIRef(self.expand_iri("rc:patchContent")),
                    Literal(str(patch["content"])),
                )
            )
            metadata.add(
                (
                    patch_subject,
                    URIRef(self.expand_iri("rc:patchTripleCount")),
                    Literal(patch_record.triple_count, datatype=XSD.integer),
                )
            )
            metadata.add(
                (
                    patch_subject,
                    URIRef(self.expand_iri("rc:beforeTripleCount")),
                    Literal(patch_record.before_triple_count, datatype=XSD.integer),
                )
            )
            metadata.add(
                (
                    patch_subject,
                    URIRef(self.expand_iri("rc:afterTripleCount")),
                    Literal(patch_record.after_triple_count, datatype=XSD.integer),
                )
            )

        extra_triples = self._insert_graph("history", metadata)
        return StagedGraphRevisionRecord(
            revision_iri=revision_subject,
            revision_type=revision_record.revision_type,
            revision_stance=stance_iri,
            graph="history",
            triples=revision_record.triples + extra_triples,
            changed_graphs=changed_graph_values,
            patches=patch_records,
            validation_scope=validation.scope,
            validation_conforms=validation.conforms,
            validation_result_count=validation.result_count,
            validation_results=validation.results,
        )

    def stage_systematisation(
        self,
        summary: str,
        intent: str,
        framings: Iterable[Mapping[str, Any]],
        *,
        anchors: Iterable[str] | str | None = None,
        rationale: str | None = None,
        shared_additions: Iterable[Mapping[str, str]] | Mapping[str, str] | None = None,
        shared_removals: Iterable[Mapping[str, str]] | Mapping[str, str] | None = None,
        shared_context_summary: str | None = None,
        default_stance: str = "rc:ExploratoryHunch",
        revision_type: str = "rc:StagedRevision",
        included_graphs: Iterable[str] | str | None = None,
        created_at: datetime | str | None = None,
        created_by: str | None = None,
        supporting_observations: Iterable[str] | str | None = None,
        supporting_claims: Iterable[str] | str | None = None,
        supporting_patterns: Iterable[str] | str | None = None,
        evidence: Iterable[str] | str | None = None,
        alternative_to: str | None = None,
        link_alternatives: bool = True,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ] = "all",
    ) -> SystematisationDraftRecord:
        summary_value = summary.strip()
        if not summary_value:
            raise DoxaBaseError("summary must not be empty")
        intent_value = intent.strip()
        if not intent_value:
            raise DoxaBaseError("intent must not be empty")
        rationale_value = rationale.strip() if rationale is not None else None
        anchor_values = self._string_values("anchors", anchors)
        self._validate_resource_values("anchors", anchor_values)
        framing_values = list(framings)
        if not framing_values:
            raise DoxaBaseError("stage_systematisation requires at least one framing")
        shared_addition_specs = self._patch_specs_with_role(
            self._normalise_patch_spec_list("shared_additions", shared_additions) or [],
            "rc:SharedContextPatch",
        )
        shared_removal_specs = self._patch_specs_with_role(
            self._normalise_patch_spec_list("shared_removals", shared_removals) or [],
            "rc:SharedContextPatch",
        )
        shared_patch_count = len(shared_addition_specs) + len(shared_removal_specs)
        shared_context_summary_value = (
            shared_context_summary.strip()
            if shared_context_summary is not None
            else None
        )

        warnings: list[str] = []
        if not anchor_values:
            warnings.append(
                "No anchors were supplied; future reviewers may have less context."
            )
        if shared_patch_count:
            warnings.append(
                "Shared proposed context patches are included in every staged framing preview and patch bundle."
            )
        if len(framing_values) > 1 and link_alternatives:
            warnings.append(
                "Multiple framings were staged; later revisions are linked as alternatives to the first."
            )

        staged_revisions: list[StagedGraphRevisionRecord] = []
        framing_records: list[SystematisationFramingRecord] = []
        first_revision_iri: str | None = None
        for index, framing in enumerate(framing_values, start=1):
            if not isinstance(framing, Mapping):
                raise DoxaBaseError("framings entries must be objects")
            label = str(
                framing.get("label") or framing.get("name") or f"Framing {index}"
            ).strip()
            if not label:
                raise DoxaBaseError("framing label must not be empty")
            framing_rationale = str(framing.get("rationale") or "").strip() or None
            framing_review_note = (
                str(
                    framing.get("review_note")
                    or framing.get("reviewNote")
                    or framing.get("note")
                    or ""
                ).strip()
                or None
            )
            framing_review_recommendation = (
                str(
                    framing.get("review_recommendation")
                    or framing.get("reviewRecommendation")
                    or framing.get("recommendation")
                    or ""
                ).strip()
                or None
            )
            stance = str(framing.get("stance") or default_stance).strip()
            if not stance:
                raise DoxaBaseError("framing stance must not be empty")
            additions, removals = self._systematisation_patch_specs(framing)
            addition_specs = self._patch_specs_with_role(
                additions or [],
                "rc:FramingPatch",
            )
            removal_specs = self._patch_specs_with_role(
                removals or [],
                "rc:FramingPatch",
            )
            framing_scope = str(
                framing.get("validation_scope") or validation_scope
            ).strip()
            if not framing_scope:
                raise DoxaBaseError("validation_scope must not be empty")
            revision_summary = (
                f"{summary_value}: {label}"
                if len(framing_values) > 1
                else summary_value
            )
            revision_rationale = self._systematisation_rationale(
                intent=intent_value,
                anchors=anchor_values,
                overall_rationale=rationale_value,
                shared_context_summary=shared_context_summary_value,
                shared_patch_count=shared_patch_count,
                framing_label=label,
                framing_rationale=framing_rationale,
            )
            framing_alternative_to = str(framing.get("alternative_to") or "").strip()
            if framing_alternative_to:
                alternative_target = framing_alternative_to
            elif index == 1:
                alternative_target = alternative_to
            elif link_alternatives:
                alternative_target = first_revision_iri
            else:
                alternative_target = alternative_to

            staged = self.stage_graph_revision(
                summary=revision_summary,
                rationale=revision_rationale,
                additions=[*shared_addition_specs, *addition_specs],
                removals=[*shared_removal_specs, *removal_specs],
                stance=stance,
                revision_type=revision_type,
                included_graphs=included_graphs,
                created_at=created_at,
                created_by=created_by,
                supporting_observations=supporting_observations,
                supporting_claims=supporting_claims,
                supporting_patterns=supporting_patterns,
                revision_anchors=anchor_values,
                evidence=evidence,
                alternative_to=alternative_target,
                review_note=framing_review_note,
                review_recommendation=framing_review_recommendation,
                validation_scope=framing_scope,  # type: ignore[arg-type]
            )
            if first_revision_iri is None:
                first_revision_iri = staged.revision_iri
            staged_revisions.append(staged)
            framing_records.append(
                SystematisationFramingRecord(
                    label=label,
                    rationale=framing_rationale,
                    review_note=framing_review_note,
                    review_recommendation=framing_review_recommendation,
                    target_graphs=staged.changed_graphs,
                    stance=staged.revision_stance,
                    revision_iri=staged.revision_iri,
                    patch_count=len(staged.patches),
                    triple_count=sum(patch.triple_count for patch in staged.patches),
                    validation_scope=staged.validation_scope,
                    validation_conforms=staged.validation_conforms,
                    validation_result_count=staged.validation_result_count,
                    validation_results=staged.validation_results,
                )
            )

        return SystematisationDraftRecord(
            summary=summary_value,
            intent=intent_value,
            anchors=anchor_values,
            warnings=warnings,
            framings=framing_records,
            staged_revisions=staged_revisions,
        )

    def stage_pattern_promotion(
        self,
        patterns: Iterable[str] | str,
        framings: Iterable[Mapping[str, Any]],
        *,
        summary: str | None = None,
        intent: str | None = None,
        rationale: str | None = None,
        anchors: Iterable[str] | str | None = None,
        shared_additions: Iterable[Mapping[str, str]] | Mapping[str, str] | None = None,
        shared_removals: Iterable[Mapping[str, str]] | Mapping[str, str] | None = None,
        shared_context_summary: str | None = None,
        default_stance: str = "rc:CandidateRevision",
        revision_type: str = "rc:StagedRevision",
        included_graphs: Iterable[str] | str | None = None,
        created_at: datetime | str | None = None,
        created_by: str | None = None,
        supporting_observations: Iterable[str] | str | None = None,
        supporting_claims: Iterable[str] | str | None = None,
        evidence: Iterable[str] | str | None = None,
        alternative_to: str | None = None,
        link_alternatives: bool = True,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ] = "all",
    ) -> SystematisationDraftRecord:
        pattern_values = self._string_values("patterns", patterns, required=True)
        self._validate_resource_values("patterns", pattern_values)
        pattern_descriptions = [
            self.describe_pattern(pattern_iri) for pattern_iri in pattern_values
        ]
        pattern_iris = [description.iri for description in pattern_descriptions]
        explicit_anchor_values = self._string_values("anchors", anchors)
        auto_anchor_values = [
            *pattern_iris,
            *(
                target.iri
                for description in pattern_descriptions
                for target in description.pattern_targets
            ),
            *(
                implication.iri
                for description in pattern_descriptions
                for implication in description.map_implications
            ),
        ]
        promotion_anchors = list(
            dict.fromkeys([*auto_anchor_values, *explicit_anchor_values])
        )
        auto_observation_values = [
            observation.iri
            for description in pattern_descriptions
            for observation in description.supporting_observations
        ]
        auto_claim_values = [
            claim.iri
            for description in pattern_descriptions
            for claim in description.supporting_claims
        ]
        auto_evidence_values = [
            evidence_item.iri
            for description in pattern_descriptions
            for evidence_item in description.evidence
        ]
        promotion_observations = list(
            dict.fromkeys(
                [
                    *auto_observation_values,
                    *self._string_values(
                        "supporting_observations",
                        supporting_observations,
                    ),
                ]
            )
        )
        promotion_claims = list(
            dict.fromkeys(
                [
                    *auto_claim_values,
                    *self._string_values("supporting_claims", supporting_claims),
                ]
            )
        )
        promotion_evidence = list(
            dict.fromkeys(
                [*auto_evidence_values, *self._string_values("evidence", evidence)]
            )
        )
        summary_value = (
            summary.strip()
            if summary is not None and summary.strip()
            else "Stage pattern-supported graph promotion"
        )
        intent_value = (
            intent.strip()
            if intent is not None and intent.strip()
            else "Stage one or more graph changes supported by selected patterns."
        )
        promotion_rationale = self._pattern_promotion_rationale(
            pattern_descriptions,
            rationale,
        )
        return self.stage_systematisation(
            summary=summary_value,
            intent=intent_value,
            framings=framings,
            anchors=promotion_anchors,
            rationale=promotion_rationale,
            shared_additions=shared_additions,
            shared_removals=shared_removals,
            shared_context_summary=shared_context_summary,
            default_stance=default_stance,
            revision_type=revision_type,
            included_graphs=included_graphs,
            created_at=created_at,
            created_by=created_by,
            supporting_observations=promotion_observations,
            supporting_claims=promotion_claims,
            supporting_patterns=pattern_iris,
            evidence=promotion_evidence,
            alternative_to=alternative_to,
            link_alternatives=link_alternatives,
            validation_scope=validation_scope,
        )

    def _pattern_promotion_rationale(
        self,
        pattern_descriptions: Iterable[PatternDescription],
        rationale: str | None,
    ) -> str:
        lines = ["Selected pattern support:"]
        for description in pattern_descriptions:
            pattern_summary = (
                description.summary
                or description.pattern_text
                or description.label
                or description.iri
            )
            lines.append(f"- {description.iri}: {pattern_summary}")
            if description.pattern_text:
                lines.append(f"  Pattern: {description.pattern_text}")
            if description.rationale:
                lines.append(f"  Rationale: {description.rationale}")
        rationale_value = rationale.strip() if rationale is not None else ""
        if rationale_value:
            lines.extend(["", "Promotion rationale:", rationale_value])
        return "\n".join(lines)

    def check_staged_revision_apply(
        self,
        iri: str,
        *,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
    ) -> StagedRevisionApplyCheck:
        return self._preview_staged_revision_application(
            iri,
            validation_scope=validation_scope,
        ).check

    def apply_staged_revision(
        self,
        iri: str,
        *,
        applied_revision_iri: str | None = None,
        created_at: datetime | str | None = None,
        created_by: str | None = None,
        allow_validation_failure: bool = False,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
    ) -> AppliedStagedRevisionRecord:
        preview = self._preview_staged_revision_application(
            iri,
            validation_scope=validation_scope,
        )
        staged = preview.staged
        check = preview.check
        if check.already_applied_by is not None:
            raise DoxaBaseError(
                f"Staged revision '{iri}' has already been applied by "
                f"'{check.already_applied_by}'"
            )
        if check.conflicts:
            raise DoxaBaseError(
                "Staged revision cannot be applied: " + "; ".join(check.conflicts)
            )
        if check.validation_conforms is False and not allow_validation_failure:
            raise DoxaBaseError(
                "Applying staged revision would fail validation; inspect "
                "validation_results or pass allow_validation_failure=True."
            )

        addition_operation = self.expand_iri("rc:AdditionPatch")
        triples_added = 0
        triples_removed = 0
        for patch, patch_graph in preview.parsed_patches:
            target_graph = self._required_staged_patch_field(
                patch,
                "target_graph",
                patch.target_graph,
            )
            operation = self._required_staged_patch_field(
                patch,
                "operation",
                patch.operation,
            )
            if operation == addition_operation:
                triples_added += self._insert_graph(target_graph, patch_graph)
            else:
                triples_removed += self._remove_graph_triples(target_graph, patch_graph)

        changed_graphs = check.changed_graphs
        graph_counts = {graph: self.triple_count(graph) for graph in changed_graphs}
        applied_subject = (
            self._required_iri("applied_revision_iri", applied_revision_iri)
            if applied_revision_iri is not None
            else self._mint_iri("applied-revision")
        )
        source_summary = staged.summary or staged.iri
        source_rationale = staged.rationale or "(No staged rationale recorded.)"
        revision_record = self.record_graph_revision(
            summary=f"Applied staged revision: {source_summary}",
            rationale=(
                f"Applied staged revision {staged.iri}.\n\n"
                f"Original staged rationale:\n{source_rationale}"
            ),
            changed_graphs=changed_graphs,
            revision_type="rc:AppliedStagedRevision",
            revision_iri=applied_subject,
            created_at=created_at,
            created_by=created_by,
            supporting_observations=[
                item.iri for item in staged.supporting_observations
            ],
            supporting_claims=[item.iri for item in staged.supporting_claims],
            supporting_patterns=[item.iri for item in staged.supporting_patterns],
            revision_anchors=[item.iri for item in staged.revision_anchors],
            evidence=[item.iri for item in staged.evidence],
            graph_counts=graph_counts,
            validation_scope=check.validation_scope,
            validation_conforms=bool(check.validation_conforms),
            validation_result_count=check.validation_result_count or 0,
            validation_results=check.validation_results,
        )
        metadata = Graph()
        self._bind_prefixes(metadata)
        metadata.add(
            (
                URIRef(applied_subject),
                URIRef(self.expand_iri("rc:appliesStagedRevision")),
                URIRef(staged.iri),
            )
        )
        extra_triples = self._insert_graph("history", metadata)
        return AppliedStagedRevisionRecord(
            applied_revision_iri=applied_subject,
            staged_revision_iri=staged.iri,
            graph="history",
            triples=revision_record.triples + extra_triples,
            changed_graphs=changed_graphs,
            patches_applied=len(preview.parsed_patches),
            triples_added=triples_added,
            triples_removed=triples_removed,
            validation_scope=check.validation_scope,
            validation_conforms=bool(check.validation_conforms),
            validation_result_count=check.validation_result_count or 0,
            validation_results=check.validation_results,
        )

    def _preview_staged_revision_application(
        self,
        iri: str,
        *,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
    ) -> _StagedRevisionApplicationPreview:
        staged = self.describe_staged_revision(iri)
        changed_graphs = list(
            dict.fromkeys(
                patch.target_graph for patch in staged.patches if patch.target_graph
            )
        )
        validation_scope_value = validation_scope or staged.validation_scope or "all"
        try:
            self._graphs_for_validation_scope(validation_scope_value)
        except ValueError as exc:
            raise DoxaBaseError(str(exc)) from exc
        existing_applied = self._subjects(
            self._expand_graphs(["history"]),
            "rc:appliesStagedRevision",
            staged.iri,
        )
        if existing_applied:
            check = StagedRevisionApplyCheck(
                staged_revision_iri=staged.iri,
                can_apply=False,
                already_applied_by=existing_applied[0],
                changed_graphs=changed_graphs,
                patch_checks=[],
                conflicts=[
                    "Staged revision has already been applied by "
                    f"'{existing_applied[0]}'"
                ],
                validation_scope=validation_scope_value,
                validation_conforms=None,
                validation_result_count=None,
                validation_results=[],
                patches_checked=0,
                triples_to_add=0,
                triples_to_remove=0,
            )
            return _StagedRevisionApplicationPreview(
                staged=staged,
                check=check,
                parsed_patches=[],
                preview_graphs={},
            )

        preview_graphs: dict[str, Graph] = {}
        parsed_patches: list[tuple[StagedGraphPatchDescription, Graph]] = []
        patch_checks: list[StagedPatchApplyCheck] = []
        conflicts: list[str] = []
        triples_to_add = 0
        triples_to_remove = 0
        addition_operation = self.expand_iri("rc:AdditionPatch")
        removal_operation = self.expand_iri("rc:RemovalPatch")

        for patch in staged.patches:
            target_graph: str | None = None
            operation: str | None = None
            current_count: int | None = None
            preview_count: int | None = None
            conflict: str | None = None
            patch_graph: Graph | None = None
            try:
                target_graph = self._required_staged_patch_field(
                    patch,
                    "target_graph",
                    patch.target_graph,
                )
                operation = self._required_staged_patch_field(
                    patch,
                    "operation",
                    patch.operation,
                )
                self._ensure_mutable(target_graph)
                current_preview = preview_graphs.setdefault(
                    target_graph,
                    self.to_graph([target_graph]),
                )
                current_count = len(current_preview)
                if (
                    patch.before_triple_count is not None
                    and current_count != patch.before_triple_count
                ):
                    conflict = (
                        f"graph '{target_graph}' expected "
                        f"{patch.before_triple_count} triples before patch, "
                        f"found {current_count}"
                    )
                patch_graph = self._parse_staged_patch_description(patch)
                candidate_preview = self._clone_graph(current_preview)
                if operation == addition_operation:
                    for triple in patch_graph:
                        candidate_preview.add(triple)
                elif operation == removal_operation:
                    for triple in patch_graph:
                        candidate_preview.remove(triple)
                else:
                    conflict = f"unsupported staged patch operation '{operation}'"
                preview_count = len(candidate_preview)
                if (
                    conflict is None
                    and patch.after_triple_count is not None
                    and preview_count != patch.after_triple_count
                ):
                    conflict = (
                        f"graph '{target_graph}' expected "
                        f"{patch.after_triple_count} triples after patch, "
                        f"preview produced {preview_count}"
                    )
                if conflict is None:
                    preview_graphs[target_graph] = candidate_preview
                    parsed_patches.append((patch, patch_graph))
                    if operation == addition_operation:
                        triples_to_add += len(patch_graph)
                    elif operation == removal_operation:
                        triples_to_remove += len(patch_graph)
            except DoxaBaseError as exc:
                conflict = str(exc)

            can_apply_patch = conflict is None
            if conflict is not None:
                conflicts.append(f"{patch.iri}: {conflict}")
            patch_checks.append(
                StagedPatchApplyCheck(
                    patch_iri=patch.iri,
                    target_graph=target_graph or patch.target_graph,
                    operation=operation or patch.operation,
                    operation_label=patch.operation_label,
                    patch_role=patch.patch_role,
                    patch_role_label=patch.patch_role_label,
                    triple_count=patch.triple_count,
                    before_triple_count=patch.before_triple_count,
                    current_triple_count=current_count,
                    after_triple_count=patch.after_triple_count,
                    preview_triple_count=preview_count,
                    can_apply=can_apply_patch,
                    conflict=conflict,
                )
            )

        validation_conforms: bool | None = None
        validation_result_count: int | None = None
        validation_results: list[ValidationDiagnostic] = []
        if not conflicts:
            validation = self._validate_graph_preview(
                validation_scope_value,  # type: ignore[arg-type]
                preview_graphs=preview_graphs,
            )
            validation_conforms = validation.conforms
            validation_result_count = validation.result_count
            validation_results = validation.results

        check = StagedRevisionApplyCheck(
            staged_revision_iri=staged.iri,
            can_apply=(not conflicts and validation_conforms is True),
            already_applied_by=None,
            changed_graphs=changed_graphs,
            patch_checks=patch_checks,
            conflicts=conflicts,
            validation_scope=validation_scope_value,
            validation_conforms=validation_conforms,
            validation_result_count=validation_result_count,
            validation_results=validation_results,
            patches_checked=len(patch_checks),
            triples_to_add=triples_to_add,
            triples_to_remove=triples_to_remove,
        )
        return _StagedRevisionApplicationPreview(
            staged=staged,
            check=check,
            parsed_patches=parsed_patches,
            preview_graphs=preview_graphs,
        )

    def export_staged_revision(
        self,
        iri: str,
        path: str | Path,
        *,
        format: TypingLiteral["markdown"] = "markdown",
        overwrite: bool = False,
    ) -> StagedGraphRevisionExportRecord:
        if format != "markdown":
            raise DoxaBaseError("Only markdown staged revision exports are supported")
        description = self.describe_staged_revision(iri)
        data = self._staged_revision_markdown(description)
        bytes_written = self._write_export(path, data, overwrite=overwrite)
        return StagedGraphRevisionExportRecord(
            path=str(path),
            format=format,
            revision_iri=description.iri,
            bytes_written=bytes_written,
        )

    def export_staged_revisions(
        self,
        revision_iris: Iterable[str] | str,
        path: str | Path,
        *,
        title: str | None = None,
        executive_summary: str | None = None,
        format: TypingLiteral["markdown"] = "markdown",
        overwrite: bool = False,
    ) -> StagedGraphRevisionsExportRecord:
        if format != "markdown":
            raise DoxaBaseError("Only markdown staged revision exports are supported")
        revision_values = self._string_values(
            "revision_iris",
            revision_iris,
            required=True,
        )
        descriptions = [
            self.describe_staged_revision(revision_iri)
            for revision_iri in revision_values
        ]
        data = self._staged_revisions_markdown(
            descriptions,
            title=title,
            executive_summary=executive_summary,
        )
        bytes_written = self._write_export(path, data, overwrite=overwrite)
        return StagedGraphRevisionsExportRecord(
            path=str(path),
            format=format,
            revision_iris=[description.iri for description in descriptions],
            bytes_written=bytes_written,
        )

    def _parse_staged_patch_specs(
        self,
        *,
        additions: Iterable[Mapping[str, str]] | None,
        removals: Iterable[Mapping[str, str]] | None,
    ) -> list[dict[str, Any]]:
        parsed: list[dict[str, Any]] = []
        for operation, specs in (
            (self.expand_iri("rc:AdditionPatch"), additions),
            (self.expand_iri("rc:RemovalPatch"), removals),
        ):
            for spec in specs or []:
                graph_value = str(
                    spec.get("graph")
                    or spec.get("target_graph")
                    or spec.get("targetGraph")
                    or ""
                ).strip()
                if not graph_value:
                    raise DoxaBaseError("Each staged patch must name a graph")
                graph_names = self._graph_names_for_export([graph_value])
                if len(graph_names) != 1:
                    raise DoxaBaseError(
                        "Each staged patch must target exactly one concrete graph role"
                    )
                target_graph = graph_names[0]
                self._ensure_mutable(target_graph)
                patch_format = str(spec.get("format") or "turtle").strip()
                content = str(spec.get("content") or spec.get("turtle") or "").strip()
                if not content:
                    raise DoxaBaseError("Each staged patch must include RDF content")
                patch_graph = Graph()
                self._bind_prefixes(patch_graph)
                try:
                    patch_graph.parse(data=content, format=patch_format)
                except Exception as exc:
                    raise DoxaBaseError(
                        f"Could not parse staged patch for graph '{target_graph}' "
                        f"as {patch_format}"
                    ) from exc
                if len(patch_graph) == 0:
                    raise DoxaBaseError("Staged patch content must contain triples")
                patch_role = str(
                    spec.get("patch_role")
                    or spec.get("patchRole")
                    or spec.get("role")
                    or "rc:FramingPatch"
                ).strip()
                patch_role_iri = self.expand_iri(patch_role)
                if self.expand_iri("rc:GraphPatchRole") not in self._types_from_graphs(
                    self._expand_graphs(["ontology"]),
                    patch_role_iri,
                ):
                    raise DoxaBaseError(
                        "patch_role must be an rc:GraphPatchRole declared in base or project ontology"
                    )
                parsed.append(
                    {
                        "patch_iri": self._mint_iri("graph-patch"),
                        "operation": operation,
                        "target_graph": target_graph,
                        "format": patch_format,
                        "patch_role": patch_role_iri,
                        "content": content,
                        "graph": patch_graph,
                    }
                )
        return parsed

    def _parse_staged_patch_description(
        self,
        patch: StagedGraphPatchDescription,
    ) -> Graph:
        patch_format = self._required_staged_patch_field(
            patch,
            "format",
            patch.format,
        )
        content = self._required_staged_patch_field(
            patch,
            "content",
            patch.content,
        ).strip()
        if not content:
            raise DoxaBaseError(f"Staged patch '{patch.iri}' has empty content")
        patch_graph = Graph()
        self._bind_prefixes(patch_graph)
        try:
            patch_graph.parse(data=content, format=patch_format)
        except Exception as exc:
            target_graph = patch.target_graph or "(unknown graph)"
            raise DoxaBaseError(
                f"Could not parse staged patch '{patch.iri}' for graph "
                f"'{target_graph}' as {patch_format}"
            ) from exc
        if len(patch_graph) == 0:
            raise DoxaBaseError(f"Staged patch '{patch.iri}' content has no triples")
        return patch_graph

    def _required_staged_patch_field(
        self,
        patch: StagedGraphPatchDescription,
        field_name: str,
        value: str | None,
    ) -> str:
        if value is None or not value.strip():
            raise DoxaBaseError(
                f"Staged patch '{patch.iri}' is missing required {field_name}"
            )
        return value.strip()

    def _systematisation_patch_specs(
        self,
        framing: Mapping[str, Any],
    ) -> tuple[list[dict[str, str]] | None, list[dict[str, str]] | None]:
        additions = self._normalise_patch_spec_list(
            "additions",
            framing.get("additions"),
        )
        removals = self._normalise_patch_spec_list(
            "removals",
            framing.get("removals"),
        )
        if additions is not None or removals is not None:
            return additions, removals

        graph_value = (
            framing.get("graph")
            or framing.get("target_graph")
            or framing.get("targetGraph")
            or ""
        )
        content_value = framing.get("content") or framing.get("turtle") or ""
        patch_format = str(framing.get("format") or "turtle").strip()
        return [
            {
                "graph": str(graph_value),
                "content": str(content_value),
                "format": patch_format,
            }
        ], None

    def _normalise_patch_spec_list(
        self,
        name: str,
        value: Any,
    ) -> list[dict[str, str]] | None:
        if value is None:
            return None
        if isinstance(value, Mapping):
            raw_items = [value]
        elif isinstance(value, str):
            raise DoxaBaseError(f"{name} must be a patch object or list of patches")
        else:
            raw_items = list(value)
        normalised: list[dict[str, str]] = []
        for item in raw_items:
            if not isinstance(item, Mapping):
                raise DoxaBaseError(f"{name} entries must be patch objects")
            normalised.append(
                {
                    str(key): str(item_value)
                    for key, item_value in item.items()
                    if item_value is not None
                }
            )
        return normalised

    def _patch_specs_with_role(
        self,
        specs: Iterable[Mapping[str, str]],
        patch_role: str,
    ) -> list[dict[str, str]]:
        return [
            {
                **{str(key): str(value) for key, value in spec.items()},
                "patch_role": patch_role,
            }
            for spec in specs
        ]

    def _systematisation_rationale(
        self,
        *,
        intent: str,
        anchors: list[str],
        overall_rationale: str | None,
        shared_context_summary: str | None,
        shared_patch_count: int,
        framing_label: str,
        framing_rationale: str | None,
    ) -> str:
        lines = [
            f"Systematisation intent: {intent}",
            "",
            f"Framing: {framing_label}",
        ]
        if framing_rationale:
            lines.extend(["", f"Framing rationale: {framing_rationale}"])
        if overall_rationale:
            lines.extend(["", f"Overall rationale: {overall_rationale}"])
        if shared_patch_count:
            shared_text = (
                shared_context_summary
                or "Shared proposed context is included in each framing preview."
            )
            lines.extend(
                [
                    "",
                    f"Shared proposed context ({shared_patch_count} patch(es)): {shared_text}",
                ]
            )
        if anchors:
            lines.extend(["", "Anchors:"])
            lines.extend(f"- {anchor}" for anchor in anchors)
        lines.extend(
            [
                "",
                (
                    "DoxaBase preserved caller-authored RDF and previewed validation; "
                    "the ontology shape was chosen by the agent."
                ),
            ]
        )
        return "\n".join(lines)

    def _staged_revision_markdown(
        self,
        description: StagedGraphRevisionDescription,
    ) -> str:
        lines = [
            f"# {description.summary or 'Staged graph revision'}",
            "",
            f"- Revision: `{description.iri}`",
            f"- Stance: {description.revision_stance_label or description.revision_stance or 'unknown'}",
            f"- Type: {description.revision_type_label or description.revision_type or 'unknown'}",
            f"- Changed graphs: {', '.join(description.changed_graphs)}",
            (
                f"- Validation: {description.validation_scope or 'unknown'} "
                f"conforms={description.validation_conforms} "
                f"results={description.validation_result_count}"
            ),
            "",
            "## Rationale",
            "",
            description.rationale or "",
        ]
        if description.review_note is not None:
            lines.extend(["", "## Review Note", "", description.review_note])
        if description.review_recommendation is not None:
            lines.extend(
                [
                    "",
                    "## Review Recommendation",
                    "",
                    description.review_recommendation,
                ]
            )
        if description.alternative_to is not None:
            lines.extend(
                [
                    "",
                    "## Alternative To",
                    "",
                    (
                        f"- {description.alternative_to.label or description.alternative_to.iri} "
                        f"(`{description.alternative_to.iri}`)"
                    ),
                ]
            )
        if description.revision_anchors:
            lines.extend(["", "## Revision Anchors", ""])
            for anchor in description.revision_anchors:
                lines.append(f"- {anchor.label or anchor.iri} (`{anchor.iri}`)")
        if description.validation_results:
            lines.extend(["", "## Validation Results", ""])
            for index, result in enumerate(description.validation_results, start=1):
                lines.extend(
                    [
                        f"### Result {index}",
                        "",
                        f"- IRI: `{result.iri}`",
                    ]
                )
                if result.focus_node is not None:
                    lines.append(
                        "- Focus node: "
                        + self._diagnostic_markdown_resource(
                            result.focus_node,
                            result.focus_node_label,
                        )
                    )
                if result.result_path is not None:
                    lines.append(
                        "- Result path: "
                        + self._diagnostic_markdown_resource(
                            result.result_path,
                            result.result_path_label,
                        )
                    )
                if result.value is not None:
                    lines.append(f"- Value: `{result.value}`")
                if result.source_constraint_component is not None:
                    lines.append(
                        "- Constraint: "
                        + self._diagnostic_markdown_resource(
                            result.source_constraint_component,
                            result.source_constraint_component_label,
                        )
                    )
                if result.severity is not None:
                    lines.append(
                        "- Severity: "
                        + self._diagnostic_markdown_resource(
                            result.severity,
                            result.severity_label,
                        )
                    )
                if result.source_shape is not None:
                    lines.append(f"- Source shape: `{result.source_shape}`")
                for message in result.messages:
                    lines.append(f"- Message: {message}")
                lines.append("")
        lines.extend(["", "## Patches", ""])
        for index, patch in enumerate(description.patches, start=1):
            lines.extend(
                [
                    f"### Patch {index}: {patch.operation_label or patch.operation}",
                    "",
                    f"- IRI: `{patch.iri}`",
                    f"- Target graph: `{patch.target_graph}`",
                    f"- Format: `{patch.format}`",
                    f"- Role: {patch.patch_role_label or patch.patch_role or 'unknown'}",
                    f"- Triples: {patch.triple_count}",
                    (
                        f"- Count preview: {patch.before_triple_count} -> "
                        f"{patch.after_triple_count}"
                    ),
                    "",
                    f"```{patch.format or 'turtle'}",
                    patch.content or "",
                    "```",
                    "",
                ]
            )
        return "\n".join(lines).rstrip() + "\n"

    def _staged_revisions_markdown(
        self,
        descriptions: list[StagedGraphRevisionDescription],
        *,
        title: str | None,
        executive_summary: str | None,
    ) -> str:
        title_text = title.strip() if title and title.strip() else "Staged revision bundle"
        lines = [
            f"# {title_text}",
            "",
        ]
        executive_summary_text = (
            executive_summary.strip() if executive_summary is not None else None
        )
        if executive_summary_text:
            lines.extend(["## Review Summary", "", executive_summary_text, ""])
        lines.extend(
            [
            "## Summary",
            "",
            "| # | Summary | Stance | Changed graphs | Validation | Results | Diagnostics | Recommendation |",
            "|---|---|---|---|---|---:|---|---|",
            ]
        )
        for index, description in enumerate(descriptions, start=1):
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(index),
                        self._markdown_table_cell(description.summary or description.iri),
                        self._markdown_table_cell(
                            description.revision_stance_label
                            or description.revision_stance
                            or "unknown"
                        ),
                        self._markdown_table_cell(
                            ", ".join(description.changed_graphs) or "none"
                        ),
                        str(description.validation_conforms),
                        str(description.validation_result_count),
                        self._markdown_table_cell(
                            self._validation_diagnostic_headline(description)
                        ),
                        self._markdown_table_cell(
                            description.review_recommendation or ""
                        ),
                    ]
                )
                + " |"
            )
        if any(description.review_note for description in descriptions):
            lines.extend(["", "## Review Notes", ""])
            for index, description in enumerate(descriptions, start=1):
                if description.review_note:
                    label = description.summary or description.iri
                    lines.append(f"{index}. {label}: {description.review_note}")
        lines.extend(["", "## Revisions", ""])
        for index, description in enumerate(descriptions, start=1):
            lines.extend(
                [
                    f"## Revision {index}: {description.summary or description.iri}",
                    "",
                    self._staged_revision_markdown(description).strip(),
                    "",
                ]
            )
        return "\n".join(lines).rstrip() + "\n"

    def _validation_diagnostic_headline(
        self,
        description: StagedGraphRevisionDescription,
    ) -> str:
        if not description.validation_results:
            return ""
        messages = [
            message
            for result in description.validation_results
            for message in result.messages
            if message
        ]
        if messages:
            first_message = messages[0]
        else:
            first_result = description.validation_results[0]
            first_message = (
                first_result.result_path_label
                or first_result.result_path
                or first_result.focus_node_label
                or first_result.focus_node
                or "Validation result"
            )
        remaining = len(description.validation_results) - 1
        if remaining > 0:
            return f"{first_message} (+{remaining} more)"
        return first_message

    def _markdown_table_cell(self, value: str) -> str:
        return value.replace("|", "\\|").replace("\n", " ")

    def _diagnostic_markdown_resource(self, iri: str, label: str | None) -> str:
        if label and label != iri:
            return f"{label} (`{iri}`)"
        return f"`{iri}`"

    def import_turtle(
        self,
        source: str | Path,
        *,
        graph: str = "map",
        format: str = "turtle",
        replace: bool = False,
        allow_immutable: bool = False,
    ) -> int:
        self._ensure_mutable(graph, allow_immutable=allow_immutable)
        rdf_graph = Graph()
        path = _existing_path(source)
        if path is not None:
            rdf_graph.parse(path, format=format)
        else:
            rdf_graph.parse(data=str(source), format=format)
        if replace:
            self.clear_graph(graph, allow_immutable=allow_immutable)
        self._ensure_graph(graph)
        return self._insert_graph(graph, rdf_graph)

    def import_trig(
        self,
        source: str | Path,
        *,
        graph_map: dict[str, str] | None = None,
        replace: bool = False,
        allow_immutable: bool = False,
    ) -> dict[str, int]:
        dataset = Dataset()
        path = _existing_path(source)
        if path is not None:
            dataset.parse(path, format="trig")
        else:
            dataset.parse(data=str(source), format="trig")

        imported: dict[str, int] = {}
        for context in dataset.graphs():
            if len(context) == 0:
                continue
            graph_name = self._local_graph_name(str(context.identifier), graph_map)
            self._ensure_mutable(graph_name, allow_immutable=allow_immutable)
            if replace:
                self.clear_graph(graph_name, allow_immutable=allow_immutable)
            self._ensure_graph(graph_name)
            imported[graph_name] = imported.get(graph_name, 0) + self._insert_graph(
                graph_name,
                context,
            )
        return imported

    def export_graph(
        self,
        path: str | Path,
        *,
        graphs: Iterable[str] | str | None = "map",
        format: str = "turtle",
        overwrite: bool = False,
    ) -> GraphExportRecord:
        graph_names = self._graph_names_for_export(graphs)
        rdf_graph = self._to_graph_roles(graph_names)
        data = rdf_graph.serialize(format=format)
        bytes_written = self._write_export(path, data, overwrite=overwrite)
        return GraphExportRecord(
            path=str(path),
            format=format,
            graphs=graph_names,
            graph_counts=self._graph_counts(graph_names),
            triples=len(rdf_graph),
            bytes_written=bytes_written,
        )

    def export_trig(
        self,
        path: str | Path,
        *,
        graphs: Iterable[str] | str | None = None,
        overwrite: bool = False,
        graph_iri_prefix: str = RCG_PREFIX,
    ) -> GraphExportRecord:
        graph_names = self._graph_names_for_export(graphs, default_preset="project")
        dataset = self.to_dataset(graph_names, graph_iri_prefix=graph_iri_prefix)
        data = dataset.serialize(format="trig")
        bytes_written = self._write_export(path, data, overwrite=overwrite)
        return GraphExportRecord(
            path=str(path),
            format="trig",
            graphs=graph_names,
            graph_counts=self._graph_counts(graph_names),
            triples=len(dataset),
            bytes_written=bytes_written,
        )

    def clear_graph(self, graph: str, *, allow_immutable: bool = False) -> None:
        self._ensure_mutable(graph, allow_immutable=allow_immutable)
        self._conn.execute("DELETE FROM quads WHERE graph = ?", (graph,))
        self._conn.commit()
        self._rebuild_search_index(raise_on_failure=False)

    def validate_graph(
        self,
        scope: TypingLiteral["map", "ontology", "patterns", "shapes", "all"] = "map",
        *,
        limit_results: int = 100,
    ) -> ValidationResult:
        data_graphs = self._graphs_for_validation_scope(scope)
        shape_graphs = self._expand_graphs(["shapes"])
        data = self.to_graph(data_graphs)
        shapes = self.to_graph(shape_graphs)
        conforms, report_graph, report_text = validate(
            data_graph=data,
            shacl_graph=shapes,
            inference="rdfs",
            advanced=False,
        )
        diagnostics = self._validation_diagnostics_from_report_graph(
            report_graph,
            limit_results=limit_results,
        )
        result_count = self._validation_result_count(report_graph)
        if result_count > limit_results:
            report_text = f"{report_text}\n\nResult output limited by caller to {limit_results} results."
        return ValidationResult(
            conforms=bool(conforms),
            report_text=str(report_text),
            result_count=result_count,
            scope=scope,
            results=diagnostics,
        )

    def _validate_graph_preview(
        self,
        scope: str,
        *,
        preview_graphs: Mapping[str, Graph],
        limit_results: int = 100,
    ) -> ValidationResult:
        try:
            data_graphs = self._graphs_for_validation_scope(scope)
        except ValueError as exc:
            raise DoxaBaseError(str(exc)) from exc
        shape_graphs = self._expand_graphs(["shapes"])
        data = Graph()
        for prefix, namespace in PREFIXES.items():
            data.bind(prefix, namespace)
        for graph_name in data_graphs:
            source = preview_graphs.get(graph_name)
            if source is None:
                source = self.to_graph([graph_name])
            for triple in source:
                data.add(triple)
        shapes = Graph()
        for prefix, namespace in PREFIXES.items():
            shapes.bind(prefix, namespace)
        for graph_name in shape_graphs:
            source = preview_graphs.get(graph_name)
            if source is None:
                source = self.to_graph([graph_name])
            for triple in source:
                shapes.add(triple)
        conforms, report_graph, report_text = validate(
            data_graph=data,
            shacl_graph=shapes,
            inference="rdfs",
            advanced=False,
        )
        diagnostics = self._validation_diagnostics_from_report_graph(
            report_graph,
            limit_results=limit_results,
        )
        result_count = self._validation_result_count(report_graph)
        if result_count > limit_results:
            report_text = (
                f"{report_text}\n\nResult output limited by caller to "
                f"{limit_results} results."
            )
        return ValidationResult(
            conforms=bool(conforms),
            report_text=str(report_text),
            result_count=result_count,
            scope=scope,
            results=diagnostics,
        )

    def _validation_result_count(self, report_graph: Graph) -> int:
        return sum(
            1
            for _ in report_graph.subjects(
                RDF.type,
                URIRef(PREFIXES["sh"] + "ValidationResult"),
            )
        )

    def _validation_diagnostics_from_report_graph(
        self,
        report_graph: Graph,
        *,
        limit_results: int,
    ) -> list[ValidationDiagnostic]:
        result_type = URIRef(PREFIXES["sh"] + "ValidationResult")
        result_iris = sorted(
            report_graph.subjects(RDF.type, result_type),
            key=lambda node: str(node),
        )
        diagnostics = [
            self._validation_diagnostic_from_report_graph(report_graph, result_node)
            for result_node in result_iris[:limit_results]
        ]
        return sorted(diagnostics, key=self._validation_diagnostic_sort_key)

    def _validation_diagnostic_from_report_graph(
        self,
        report_graph: Graph,
        result_node: Node,
    ) -> ValidationDiagnostic:
        sh = PREFIXES["sh"]
        focus_node = self._first_report_value(
            report_graph,
            result_node,
            URIRef(sh + "focusNode"),
        )
        result_path = self._first_report_value(
            report_graph,
            result_node,
            URIRef(sh + "resultPath"),
        )
        value = self._first_report_value(
            report_graph,
            result_node,
            URIRef(sh + "value"),
        )
        source_shape = self._first_report_value(
            report_graph,
            result_node,
            URIRef(sh + "sourceShape"),
        )
        source_constraint_component = self._first_report_value(
            report_graph,
            result_node,
            URIRef(sh + "sourceConstraintComponent"),
        )
        severity = self._first_report_value(
            report_graph,
            result_node,
            URIRef(sh + "resultSeverity"),
        )
        messages = sorted(
            str(message)
            for message in report_graph.objects(
                result_node,
                URIRef(sh + "resultMessage"),
            )
        )
        return ValidationDiagnostic(
            iri=None if isinstance(result_node, BNode) else str(result_node),
            focus_node=focus_node,
            focus_node_label=self._diagnostic_resource_label(focus_node),
            result_path=result_path,
            result_path_label=self._diagnostic_resource_label(result_path),
            value=value,
            source_shape=source_shape,
            source_constraint_component=source_constraint_component,
            source_constraint_component_label=self._diagnostic_resource_label(
                source_constraint_component
            ),
            severity=severity,
            severity_label=self._diagnostic_resource_label(severity),
            messages=messages,
        )

    def _first_report_value(
        self,
        report_graph: Graph,
        subject: Node,
        predicate: URIRef,
    ) -> str | None:
        values = sorted(report_graph.objects(subject, predicate), key=lambda node: str(node))
        return str(values[0]) if values else None

    def _diagnostic_resource_label(self, value: str | None) -> str | None:
        if value is None:
            return None
        return self._label_for_resource(value)

    def _validation_diagnostic_sort_key(
        self,
        diagnostic: ValidationDiagnostic,
    ) -> tuple[str, str, str]:
        return (
            diagnostic.focus_node or "",
            diagnostic.result_path or "",
            " ".join(diagnostic.messages),
        )

    def _add_validation_diagnostic_triples(
        self,
        graph: Graph,
        subject: URIRef,
        diagnostic: ValidationDiagnostic,
    ) -> None:
        sh = PREFIXES["sh"]
        graph.add((subject, RDF.type, URIRef(sh + "ValidationResult")))
        self._add_optional_validation_node(
            graph,
            subject,
            URIRef(sh + "focusNode"),
            diagnostic.focus_node,
        )
        self._add_optional_validation_node(
            graph,
            subject,
            URIRef(sh + "resultPath"),
            diagnostic.result_path,
        )
        self._add_optional_validation_node(
            graph,
            subject,
            URIRef(sh + "value"),
            diagnostic.value,
        )
        self._add_optional_validation_node(
            graph,
            subject,
            URIRef(sh + "sourceShape"),
            diagnostic.source_shape,
        )
        self._add_optional_validation_node(
            graph,
            subject,
            URIRef(sh + "sourceConstraintComponent"),
            diagnostic.source_constraint_component,
        )
        self._add_optional_validation_node(
            graph,
            subject,
            URIRef(sh + "resultSeverity"),
            diagnostic.severity,
        )
        for message in diagnostic.messages:
            graph.add((subject, URIRef(sh + "resultMessage"), Literal(message)))

    def _add_optional_validation_node(
        self,
        graph: Graph,
        subject: URIRef,
        predicate: URIRef,
        value: str | None,
    ) -> None:
        if value is None:
            return
        graph.add((subject, predicate, self._validation_node(value)))

    def _validation_node(self, value: str) -> Identifier:
        if "://" in value or value.startswith("urn:"):
            return URIRef(value)
        return Literal(value)

    def to_graph(self, graphs: Iterable[str] | str | None = None) -> Graph:
        graph_names = self._expand_graphs(self._requested_graphs(graphs))
        return self._to_graph_roles(graph_names)

    def _to_graph_roles(self, graph_names: list[str]) -> Graph:
        rdf_graph = Graph()
        for prefix, namespace in PREFIXES.items():
            rdf_graph.bind(prefix, namespace)
        params: list[Any] = []
        graph_filter = ""
        if graph_names:
            graph_filter = f"WHERE graph IN ({','.join('?' for _ in graph_names)})"
            params.extend(graph_names)
        for row in self._conn.execute(
            f"""
            SELECT subject, subject_kind, predicate, object, object_kind, datatype, lang
            FROM quads
            {graph_filter}
            """,
            params,
        ):
            rdf_graph.add(
                (
                    self._term_from_row(row["subject"], row["subject_kind"]),
                    URIRef(row["predicate"]),
                    self._object_from_row(row),
                )
            )
        return rdf_graph

    def to_dataset(
        self,
        graphs: Iterable[str] | str | None = None,
        *,
        graph_iri_prefix: str = RCG_PREFIX,
    ) -> Dataset:
        dataset = Dataset()
        for prefix, namespace in PREFIXES.items():
            dataset.bind(prefix, namespace)
        dataset.bind("rcg", graph_iri_prefix)
        graph_names = self._graph_names_for_export(
            graphs,
            default_preset="all_with_seeds",
        )
        params: list[Any] = []
        graph_filter = ""
        if graph_names:
            graph_filter = f"WHERE graph IN ({','.join('?' for _ in graph_names)})"
            params.extend(graph_names)
        for row in self._conn.execute(
            f"""
            SELECT graph, subject, subject_kind, predicate, object, object_kind, datatype, lang
            FROM quads
            {graph_filter}
            """,
            params,
        ):
            context = dataset.graph(
                URIRef(self._export_graph_identifier(row["graph"], graph_iri_prefix))
            )
            context.add(
                (
                    self._term_from_row(row["subject"], row["subject_kind"]),
                    URIRef(row["predicate"]),
                    self._object_from_row(row),
                )
            )
        return dataset

    def triple_count(self, graph: str | None = None) -> int:
        if graph is None:
            row = self._conn.execute("SELECT COUNT(*) AS count FROM quads").fetchone()
        else:
            row = self._conn.execute(
                "SELECT COUNT(*) AS count FROM quads WHERE graph = ?",
                (graph,),
            ).fetchone()
        return int(row["count"])

    def expand_iri(self, value: str) -> str:
        if "://" in value or value.startswith("urn:"):
            return value
        if ":" not in value:
            return value
        prefix, local = value.split(":", 1)
        namespace = PREFIXES.get(prefix)
        if namespace is None:
            return value
        return namespace + local

    def _ensure_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS named_graphs (
                name TEXT PRIMARY KEY,
                description TEXT,
                mutable INTEGER NOT NULL DEFAULT 1,
                system_seed INTEGER NOT NULL DEFAULT 0,
                source_path TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quads (
                graph TEXT NOT NULL,
                subject TEXT NOT NULL,
                subject_kind TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                object_kind TEXT NOT NULL,
                datatype TEXT,
                lang TEXT,
                created_at TEXT NOT NULL,
                UNIQUE (graph, subject, predicate, object, object_kind, datatype, lang)
            );

            CREATE INDEX IF NOT EXISTS quads_spo ON quads(subject, predicate, object);
            CREATE INDEX IF NOT EXISTS quads_pos ON quads(predicate, object, subject);
            CREATE INDEX IF NOT EXISTS quads_gspo ON quads(graph, subject, predicate, object);
            CREATE INDEX IF NOT EXISTS quads_graph ON quads(graph);

            """
        )
        self._create_search_index()
        self._conn.commit()
        self._rebuild_search_index()

    def _ensure_default_graphs(self) -> None:
        for name, description, mutable, system_seed, source_path in DEFAULT_GRAPHS:
            self._ensure_graph(
                name,
                description=description,
                mutable=mutable,
                system_seed=system_seed,
                source_path=str(source_path.relative_to(ROOT)) if source_path else None,
            )

    def _ensure_graph(
        self,
        name: str,
        *,
        description: str | None = None,
        mutable: bool = True,
        system_seed: bool = False,
        source_path: str | None = None,
    ) -> None:
        self._conn.execute(
            """
            INSERT OR IGNORE INTO named_graphs
                (name, description, mutable, system_seed, source_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                description,
                int(mutable),
                int(system_seed),
                source_path,
                _now(),
            ),
        )
        self._conn.commit()

    def _ensure_mutable(self, graph: str, *, allow_immutable: bool = False) -> None:
        row = self._conn.execute(
            "SELECT mutable FROM named_graphs WHERE name = ?",
            (graph,),
        ).fetchone()
        if row is not None and not bool(row["mutable"]) and not allow_immutable:
            raise ImmutableGraphError(f"Graph '{graph}' is immutable")

    def _insert_graph(self, graph: str, rdf_graph: Graph) -> int:
        rows = []
        for subject, predicate, obj in rdf_graph:
            subject_value, subject_kind = self._term_to_storage(subject)
            object_value, object_kind, datatype, lang = self._object_to_storage(obj)
            rows.append(
                (
                    graph,
                    subject_value,
                    subject_kind,
                    str(predicate),
                    object_value,
                    object_kind,
                    datatype,
                    lang,
                    _now(),
                )
            )
        before = self.triple_count(graph)
        self._conn.executemany(
            """
            INSERT OR IGNORE INTO quads
                (graph, subject, subject_kind, predicate, object, object_kind, datatype, lang, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self._conn.commit()
        inserted = self.triple_count(graph) - before
        self._rebuild_search_index(raise_on_failure=False)
        return inserted

    def _remove_graph_triples(self, graph: str, rdf_graph: Graph) -> int:
        self._ensure_mutable(graph)
        before = self.triple_count(graph)
        rows = []
        for subject, predicate, obj in rdf_graph:
            subject_value, subject_kind = self._term_to_storage(subject)
            object_value, object_kind, datatype, lang = self._object_to_storage(obj)
            rows.append(
                (
                    graph,
                    subject_value,
                    subject_kind,
                    str(predicate),
                    object_value,
                    object_kind,
                    datatype,
                    lang,
                )
            )
        self._conn.executemany(
            """
            DELETE FROM quads
            WHERE graph = ?
              AND subject = ?
              AND subject_kind = ?
              AND predicate = ?
              AND object = ?
              AND object_kind = ?
              AND datatype IS ?
              AND lang IS ?
            """,
            rows,
        )
        self._conn.commit()
        removed = before - self.triple_count(graph)
        self._rebuild_search_index(raise_on_failure=False)
        return removed

    def _clone_graph(self, source: Graph) -> Graph:
        graph = Graph()
        self._bind_prefixes(graph)
        for triple in source:
            graph.add(triple)
        return graph

    def _create_search_index(self) -> None:
        self._conn.execute(SEARCH_INDEX_SQL)

    def _rebuild_search_index(self, *, raise_on_failure: bool = True) -> None:
        try:
            self._rebuild_search_index_once()
            self._search_index_error = None
        except sqlite3.Error as exc:
            self._conn.rollback()
            self._search_index_error = str(exc)
            message = (
                "DoxaBase search index rebuild failed; graph data was preserved, "
                "but lexical search may be stale or unavailable."
            )
            if raise_on_failure:
                raise DoxaBaseError(message) from exc
            warnings.warn(message, RuntimeWarning, stacklevel=2)

    def _rebuild_search_index_once(self) -> None:
        self._conn.execute("DROP TABLE IF EXISTS literal_search")
        self._create_search_index()
        self._conn.execute(
            """
            INSERT INTO literal_search
                (rowid, graph, subject, subject_kind, predicate, text)
            SELECT rowid, graph, subject, subject_kind, predicate, object
            FROM quads
            WHERE object_kind = 'literal'
            """
        )
        self._conn.commit()

    def _expand_graphs(self, graphs: list[str | None] | None) -> list[str]:
        if graphs is None:
            return [row["name"] for row in self._conn.execute("SELECT name FROM named_graphs")]
        expanded: list[str] = []
        for graph in graphs:
            if graph is None:
                continue
            if graph == "ontology":
                expanded.extend(["base_ontology", "ontology"])
            elif graph == "shapes":
                expanded.extend(["base_shapes", "shapes"])
            elif graph == "all":
                expanded.extend(
                    row["name"] for row in self._conn.execute("SELECT name FROM named_graphs")
                )
            else:
                expanded.append(graph)
        return list(dict.fromkeys(expanded))

    def _requested_graphs(
        self,
        graphs: Iterable[str] | str | None,
    ) -> list[str | None] | None:
        if graphs is None:
            return None
        if isinstance(graphs, str):
            return [graphs]
        return list(graphs)

    def _graph_names_for_export(
        self,
        graphs: Iterable[str] | str | None,
        *,
        default_preset: str | None = None,
    ) -> list[str]:
        requested_graphs = self._requested_graphs(graphs)
        if requested_graphs is None and default_preset is not None:
            requested_graphs = [default_preset]
        graph_names: list[str] = []
        for graph in requested_graphs or []:
            if graph is None:
                continue
            if graph == "all":
                graph_names.extend(self._graph_names_for_export("all_with_seeds"))
                continue
            preset = EXPORT_PRESETS.get(graph)
            if preset is not None:
                graph_names.extend(preset)
            else:
                graph_names.append(graph)
        graph_names = list(dict.fromkeys(graph_names))
        if not graph_names:
            raise DoxaBaseError("graphs must contain at least one graph role")
        known_graphs = {
            row["name"] for row in self._conn.execute("SELECT name FROM named_graphs")
        }
        unknown_graphs = [graph for graph in graph_names if graph not in known_graphs]
        if unknown_graphs:
            raise DoxaBaseError(
                f"Unknown graph role(s): {', '.join(sorted(unknown_graphs))}"
            )
        return graph_names

    def _known_graph_names(self) -> set[str]:
        return {row["name"] for row in self._conn.execute("SELECT name FROM named_graphs")}

    def _graph_counts(self, graphs: Iterable[str]) -> dict[str, int]:
        return {graph: self.triple_count(graph) for graph in graphs}

    def _graphs_for_subject(self, graphs: list[str], subject: str) -> list[str]:
        graph_filter, params = self._graph_filter(graphs, alias="q")
        return [
            row["graph"]
            for row in self._conn.execute(
                f"""
                SELECT DISTINCT q.graph
                FROM quads q
                WHERE q.subject = ?
                  {graph_filter}
                ORDER BY q.graph
                """,
                [subject, *params],
            )
        ]

    def _graphs_for_validation_scope(self, scope: str) -> list[str]:
        if scope == "map":
            return self._expand_graphs(["ontology"]) + ["map"]
        if scope == "ontology":
            return self._expand_graphs(["ontology"])
        if scope == "patterns":
            return [
                "base_ontology",
                "ontology",
                "observations",
                "patterns",
                "evidence",
            ]
        if scope == "shapes":
            return self._expand_graphs(["shapes"])
        if scope == "all":
            return [
                "base_ontology",
                "ontology",
                "map",
                "observations",
                "patterns",
                "evidence",
                "history",
            ]
        raise ValueError(f"Unsupported validation scope: {scope}")

    def _local_graph_name(
        self,
        identifier: str,
        graph_map: dict[str, str] | None,
    ) -> str:
        if graph_map and identifier in graph_map:
            return graph_map[identifier]
        if identifier.startswith(RCG_PREFIX):
            return identifier.removeprefix(RCG_PREFIX)
        return identifier

    def _export_graph_identifier(self, graph: str, graph_iri_prefix: str) -> str:
        if "://" in graph or graph.startswith("urn:"):
            return graph
        return f"{graph_iri_prefix}{graph}"

    def _count_objects(self, predicate: str, *, limit: int) -> list[tuple[str, int]]:
        return [
            (row["object"], int(row["count"]))
            for row in self._conn.execute(
                """
                SELECT object, COUNT(*) AS count
                FROM quads
                WHERE predicate = ?
                GROUP BY object
                ORDER BY count DESC, object
                LIMIT ?
                """,
                (predicate, limit),
            )
        ]

    def _count_type(self, type_iri: str) -> int:
        row = self._conn.execute(
            """
            SELECT COUNT(DISTINCT graph || ':' || subject) AS count
            FROM quads
            WHERE predicate = ? AND object = ?
            """,
            (str(RDF.type), self.expand_iri(type_iri)),
        ).fetchone()
        return int(row["count"])

    def _label(self, graph: str, subject: str) -> str | None:
        row = self._conn.execute(
            """
            SELECT object
            FROM quads
            WHERE graph = ? AND subject = ? AND predicate = ? AND object_kind = 'literal'
            ORDER BY object
            LIMIT 1
            """,
            (graph, subject, str(RDFS.label)),
        ).fetchone()
        return row["object"] if row else None

    def _types(self, graph: str, subject: str) -> list[str]:
        return [
            row["object"]
            for row in self._conn.execute(
                """
                SELECT object
                FROM quads
                WHERE graph = ? AND subject = ? AND predicate = ?
                ORDER BY object
                """,
                (graph, subject, str(RDF.type)),
            )
        ]

    def _lookup_graphs(self, data_graphs: list[str]) -> list[str]:
        return list(dict.fromkeys(data_graphs + self._expand_graphs(["ontology"])))

    def _subject_exists(self, subject: str, graphs: list[str]) -> bool:
        graph_filter, params = self._graph_filter(graphs)
        row = self._conn.execute(
            f"""
            SELECT 1
            FROM quads
            WHERE subject = ?
              {graph_filter}
            LIMIT 1
            """,
            [subject, *params],
        ).fetchone()
        return row is not None

    def _describe_column(
        self,
        column_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> ColumnDescription:
        physical_type = self._first_object(data_graphs, column_iri, "rc:physicalType")
        value_type = self._first_object(data_graphs, column_iri, "rc:valueType")
        return ColumnDescription(
            iri=column_iri,
            label=self._label_from_graphs(lookup_graphs, column_iri),
            description=self._description_from_graphs(lookup_graphs, column_iri),
            column_name=self._first_object(data_graphs, column_iri, "rc:columnName"),
            physical_type=(
                self._resource_summary(lookup_graphs, physical_type)
                if physical_type is not None
                else None
            ),
            value_type=(
                self._resource_summary(lookup_graphs, value_type)
                if value_type is not None
                else None
            ),
            nullable=self._bool_object(data_graphs, column_iri, "rc:nullable"),
        )

    def _describe_physical_layout(
        self,
        layout_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> PhysicalLayoutDescription:
        file_format = self._first_object(data_graphs, layout_iri, "rc:fileFormat")
        compression_codec = self._first_object(
            data_graphs,
            layout_iri,
            "rc:compressionCodec",
        )
        return PhysicalLayoutDescription(
            iri=layout_iri,
            label=self._label_from_graphs(lookup_graphs, layout_iri),
            description=self._description_from_graphs(lookup_graphs, layout_iri),
            file_format=(
                self._resource_summary(lookup_graphs, file_format)
                if file_format is not None
                else None
            ),
            compression_codec=(
                self._resource_summary(lookup_graphs, compression_codec)
                if compression_codec is not None
                else None
            ),
            layout_verification_status=self._optional_resource_summary(
                lookup_graphs,
                self._first_object(
                    data_graphs,
                    layout_iri,
                    "rc:layoutVerificationStatus",
                ),
            ),
            layout_verification_note=self._first_object(
                data_graphs,
                layout_iri,
                "rc:layoutVerificationNote",
            ),
        )

    def _describe_storage_access(
        self,
        access_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> StorageAccessDescription:
        storage_protocol = self._first_object(data_graphs, access_iri, "rc:storageProtocol")
        access_mode = self._first_object(data_graphs, access_iri, "rc:accessMode")
        return StorageAccessDescription(
            iri=access_iri,
            label=self._label_from_graphs(lookup_graphs, access_iri),
            description=self._description_from_graphs(lookup_graphs, access_iri),
            storage_protocol=(
                self._resource_summary(lookup_graphs, storage_protocol)
                if storage_protocol is not None
                else None
            ),
            access_mode=(
                self._resource_summary(lookup_graphs, access_mode)
                if access_mode is not None
                else None
            ),
            storage_root=self._first_object(data_graphs, access_iri, "rc:storageRoot"),
            endpoint_profile=self._first_object(data_graphs, access_iri, "rc:endpointProfile"),
            bucket_name=self._first_object(data_graphs, access_iri, "rc:bucketName"),
            key_prefix=self._first_object(data_graphs, access_iri, "rc:keyPrefix"),
            region=self._first_object(data_graphs, access_iri, "rc:region"),
            path_style_access=self._bool_object(
                data_graphs,
                access_iri,
                "rc:pathStyleAccess",
            ),
            credential_reference=self._first_object(
                data_graphs,
                access_iri,
                "rc:credentialReference",
            ),
            path_templates=self._objects(data_graphs, access_iri, "rc:pathTemplate"),
            layout_verification_status=self._optional_resource_summary(
                lookup_graphs,
                self._first_object(
                    data_graphs,
                    access_iri,
                    "rc:layoutVerificationStatus",
                ),
            ),
            layout_verification_note=self._first_object(
                data_graphs,
                access_iri,
                "rc:layoutVerificationNote",
            ),
        )

    def _describe_partition(
        self,
        partition_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> PartitionDescription:
        partition_column = self._first_object(data_graphs, partition_iri, "rc:partitionColumn")
        granularity = self._first_object(data_graphs, partition_iri, "rc:partitionGranularity")
        redundant_partition_key = self._first_object(
            data_graphs,
            partition_iri,
            "rc:redundantPartitionKey",
        )
        return PartitionDescription(
            iri=partition_iri,
            label=self._label_from_graphs(lookup_graphs, partition_iri),
            description=self._description_from_graphs(lookup_graphs, partition_iri),
            partition_column=(
                self._resource_summary(lookup_graphs, partition_column)
                if partition_column is not None
                else None
            ),
            granularity=(
                self._resource_summary(lookup_graphs, granularity)
                if granularity is not None
                else None
            ),
            path_template=self._first_object(data_graphs, partition_iri, "rc:pathTemplate"),
            redundant_partition_key=(
                self._resource_summary(lookup_graphs, redundant_partition_key)
                if redundant_partition_key is not None
                else None
            ),
            layout_verification_status=self._optional_resource_summary(
                lookup_graphs,
                self._first_object(
                    data_graphs,
                    partition_iri,
                    "rc:layoutVerificationStatus",
                ),
            ),
            layout_verification_note=self._first_object(
                data_graphs,
                partition_iri,
                "rc:layoutVerificationNote",
            ),
        )

    def _related_datasets(
        self,
        dataset_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
        *,
        relationships: Iterable[RelationshipDescription] = (),
    ) -> list[RelatedDatasetDescription]:
        related: list[RelatedDatasetDescription] = []
        for companion_iri in self._objects(data_graphs, dataset_iri, "rc:companionOf"):
            related.append(
                self._related_dataset(
                    companion_iri,
                    "companion",
                    None,
                    lookup_graphs,
                )
            )
        for companion_iri in self._subjects(data_graphs, "rc:companionOf", dataset_iri):
            related.append(
                self._related_dataset(
                    companion_iri,
                    "companion",
                    None,
                    lookup_graphs,
                )
            )

        for relationship_iri in self._subjects(data_graphs, "rc:sourceDataset", dataset_iri):
            for target_iri in self._objects(data_graphs, relationship_iri, "rc:targetDataset"):
                related.append(
                    self._related_dataset(
                        target_iri,
                        "source_of",
                        relationship_iri,
                        lookup_graphs,
                    )
                )
        for relationship_iri in self._subjects(data_graphs, "rc:targetDataset", dataset_iri):
            for source_iri in self._objects(data_graphs, relationship_iri, "rc:sourceDataset"):
                related.append(
                    self._related_dataset(
                        source_iri,
                        "target_of",
                        relationship_iri,
                        lookup_graphs,
                    )
                )
        for relationship in relationships:
            related.extend(
                self._related_datasets_from_column_relationship(
                    dataset_iri,
                    relationship,
                    lookup_graphs,
                )
            )
        return list(
            {
                (
                    item.iri,
                    item.relationship,
                    item.relationship_iri,
                ): item
                for item in related
            }.values()
        )

    def _related_datasets_from_column_relationship(
        self,
        dataset_iri: str,
        relationship: RelationshipDescription,
        lookup_graphs: list[str],
    ) -> list[RelatedDatasetDescription]:
        related: list[RelatedDatasetDescription] = []
        if relationship.foreign_key_from is not None and relationship.foreign_key_to is not None:
            from_dataset = relationship.foreign_key_from.owning_dataset_iri
            to_dataset = relationship.foreign_key_to.owning_dataset_iri
            if from_dataset == dataset_iri and to_dataset and to_dataset != dataset_iri:
                related.append(
                    self._related_dataset(
                        to_dataset,
                        "source_of",
                        relationship.iri,
                        lookup_graphs,
                    )
                )
            if to_dataset == dataset_iri and from_dataset and from_dataset != dataset_iri:
                related.append(
                    self._related_dataset(
                        from_dataset,
                        "target_of",
                        relationship.iri,
                        lookup_graphs,
                    )
                )

        shared_identifier_datasets = {
            column.owning_dataset_iri
            for column in relationship.identifying_columns
            if column.owning_dataset_iri is not None
        }
        if dataset_iri in shared_identifier_datasets:
            for related_dataset_iri in sorted(shared_identifier_datasets - {dataset_iri}):
                related.append(
                    self._related_dataset(
                        related_dataset_iri,
                        "shares_identifier_with",
                        relationship.iri,
                        lookup_graphs,
                    )
                )

        source_datasets = {
            column.owning_dataset_iri
            for column in relationship.source_columns
            if column.owning_dataset_iri is not None
        }
        derived_datasets = {
            column.owning_dataset_iri
            for column in relationship.derived_columns
            if column.owning_dataset_iri is not None
        }
        if dataset_iri in source_datasets:
            for related_dataset_iri in sorted(derived_datasets - {dataset_iri}):
                related.append(
                    self._related_dataset(
                        related_dataset_iri,
                        "source_of_derivation",
                        relationship.iri,
                        lookup_graphs,
                    )
                )
        if dataset_iri in derived_datasets:
            for related_dataset_iri in sorted(source_datasets - {dataset_iri}):
                related.append(
                    self._related_dataset(
                        related_dataset_iri,
                        "derived_from",
                        relationship.iri,
                        lookup_graphs,
                    )
                )

        aggregation_source_datasets: set[str] = set()
        if relationship.source_dataset is not None:
            aggregation_source_datasets.add(relationship.source_dataset.iri)
        for column in relationship.group_by_columns:
            if column.owning_dataset_iri is not None:
                aggregation_source_datasets.add(column.owning_dataset_iri)
        for aggregated_column in relationship.aggregated_columns:
            for column in aggregated_column.source_columns:
                if column.owning_dataset_iri is not None:
                    aggregation_source_datasets.add(column.owning_dataset_iri)
            if (
                aggregated_column.within_group_ordering is not None
                and aggregated_column.within_group_ordering.owning_dataset_iri is not None
            ):
                aggregation_source_datasets.add(
                    aggregated_column.within_group_ordering.owning_dataset_iri
                )

        aggregation_target_datasets: set[str] = set()
        if relationship.target_dataset is not None:
            aggregation_target_datasets.add(relationship.target_dataset.iri)
        for aggregated_column in relationship.aggregated_columns:
            if (
                aggregated_column.target_column is not None
                and aggregated_column.target_column.owning_dataset_iri is not None
            ):
                aggregation_target_datasets.add(
                    aggregated_column.target_column.owning_dataset_iri
                )

        if dataset_iri in aggregation_source_datasets:
            for related_dataset_iri in sorted(
                aggregation_target_datasets - {dataset_iri}
            ):
                related.append(
                    self._related_dataset(
                        related_dataset_iri,
                        "source_of_aggregation",
                        relationship.iri,
                        lookup_graphs,
                    )
                )
        if dataset_iri in aggregation_target_datasets:
            for related_dataset_iri in sorted(
                aggregation_source_datasets - {dataset_iri}
            ):
                related.append(
                    self._related_dataset(
                        related_dataset_iri,
                        "aggregated_from",
                        relationship.iri,
                        lookup_graphs,
                    )
                )
        return related

    def _related_dataset(
        self,
        iri: str,
        relationship: str,
        relationship_iri: str | None,
        lookup_graphs: list[str],
    ) -> RelatedDatasetDescription:
        summary = self._resource_summary(lookup_graphs, iri)
        relationship_types = (
            self._types_from_graphs(lookup_graphs, relationship_iri)
            if relationship_iri is not None
            else []
        )
        relationship_kind = self._first_matching_type(
            relationship_types,
            [
                "rc:ForeignKey",
                "rc:SharedIdentifier",
                "rc:Derivation",
                "rc:Aggregation",
                "rc:Relationship",
            ],
        )
        return RelatedDatasetDescription(
            iri=summary.iri,
            label=summary.label,
            description=summary.description,
            relationship=relationship,
            relationship_iri=relationship_iri,
            relationship_label=(
                self._display_label_from_graphs(lookup_graphs, relationship_iri)
                if relationship_iri is not None
                else None
            ),
            relationship_kind=relationship_kind,
            relationship_kind_label=self._label_for_resource(relationship_kind),
        )

    def _related_dataset_groups(
        self,
        dataset_iri: str,
        related_datasets: Iterable[RelatedDatasetDescription],
        relationships: Iterable[RelationshipDescription],
    ) -> list[RelatedDatasetGroup]:
        relationships_by_iri = {
            relationship.iri: relationship
            for relationship in relationships
        }
        groups: dict[str, RelatedDatasetDescription] = {}
        reasons_by_group: dict[
            str,
            dict[tuple[tuple[str, ...], tuple[str, ...]], list[RelatedDatasetReasonTag]],
        ] = {}
        columns_by_reason: dict[
            tuple[str, tuple[tuple[str, ...], tuple[str, ...]]],
            tuple[list[ResourceSummary], list[ResourceSummary], list[ResourceSummary]],
        ] = {}
        source_caveats_by_reason: dict[
            tuple[str, tuple[tuple[str, ...], tuple[str, ...]]],
            dict[str, CaveatDescription],
        ] = {}
        seen_tags: set[tuple[str, str, str | None]] = set()

        for related in related_datasets:
            groups.setdefault(related.iri, related)
            reasons_by_group.setdefault(related.iri, {})

            tag_key = (related.iri, related.relationship, related.relationship_iri)
            if tag_key in seen_tags:
                continue
            seen_tags.add(tag_key)
            relationship = (
                relationships_by_iri.get(related.relationship_iri)
                if related.relationship_iri is not None
                else None
            )
            columns = (
                self._relationship_columns_between_datasets(
                    dataset_iri,
                    related.iri,
                    relationship,
                )
                if relationship is not None
                else []
            )
            current_columns = [
                column
                for column in columns
                if column.owning_dataset_iri == dataset_iri
            ]
            related_columns = [
                column
                for column in columns
                if column.owning_dataset_iri == related.iri
            ]
            reason_key = (
                tuple(column.iri for column in current_columns),
                tuple(column.iri for column in related_columns),
            )
            reasons_by_group[related.iri].setdefault(reason_key, [])
            columns_by_reason[(related.iri, reason_key)] = (
                columns,
                current_columns,
                related_columns,
            )
            source_caveats_by_reason.setdefault((related.iri, reason_key), {})
            if relationship is not None:
                source_caveats_by_reason[(related.iri, reason_key)].update(
                    {
                        caveat.iri: caveat
                        for caveat in relationship.source_caveats
                    }
                )
            reasons_by_group[related.iri][reason_key].append(
                RelatedDatasetReasonTag(
                    relationship=related.relationship,
                    relationship_iri=related.relationship_iri,
                    relationship_label=related.relationship_label,
                    relationship_kind=related.relationship_kind,
                    relationship_kind_label=related.relationship_kind_label,
                    declared=relationship.declared if relationship is not None else None,
                    referential_integrity=(
                        relationship.referential_integrity
                        if relationship is not None
                        else None
                    ),
                )
            )

        return [
            RelatedDatasetGroup(
                iri=related.iri,
                label=related.label,
                description=related.description,
                reasons=sorted(
                    [
                        self._related_dataset_reason(
                            reason_tags,
                            *columns_by_reason[(related.iri, reason_key)],
                            list(
                                source_caveats_by_reason[
                                    (related.iri, reason_key)
                                ].values()
                            ),
                        )
                        for reason_key, reason_tags in reasons_by_group[
                            related.iri
                        ].items()
                    ],
                    key=self._related_dataset_reason_sort_key,
                ),
            )
            for related in sorted(
                groups.values(),
                key=lambda item: (item.label or "", item.iri),
            )
        ]

    def _related_dataset_reason(
        self,
        tags: list[RelatedDatasetReasonTag],
        columns: list[ResourceSummary],
        current_dataset_columns: list[ResourceSummary],
        related_dataset_columns: list[ResourceSummary],
        source_caveats: list[CaveatDescription],
    ) -> RelatedDatasetReason:
        sorted_tags = sorted(tags, key=self._related_dataset_reason_tag_sort_key)
        primary = sorted_tags[0]
        return RelatedDatasetReason(
            relationship=primary.relationship,
            relationship_iri=primary.relationship_iri,
            relationship_label=primary.relationship_label,
            relationship_kind=primary.relationship_kind,
            relationship_kind_label=primary.relationship_kind_label,
            columns=columns,
            current_dataset_columns=current_dataset_columns,
            related_dataset_columns=related_dataset_columns,
            declared=primary.declared,
            referential_integrity=primary.referential_integrity,
            source_caveats=sorted(
                source_caveats,
                key=lambda caveat: (caveat.label or "", caveat.iri),
            ),
            relationship_tags=sorted_tags,
        )

    def _related_dataset_reason_sort_key(
        self,
        reason: RelatedDatasetReason,
    ) -> tuple[int, str, str]:
        return (
            self._relationship_kind_priority(reason.relationship_kind),
            reason.relationship_label or "",
            reason.relationship,
        )

    def _related_dataset_reason_tag_sort_key(
        self,
        tag: RelatedDatasetReasonTag,
    ) -> tuple[int, str, str]:
        return (
            self._relationship_kind_priority(tag.relationship_kind),
            tag.relationship_label or "",
            tag.relationship,
        )

    def _relationship_kind_priority(self, relationship_kind: str | None) -> int:
        return {
            self.expand_iri("rc:ForeignKey"): 0,
            self.expand_iri("rc:SharedIdentifier"): 1,
            self.expand_iri("rc:Derivation"): 2,
            self.expand_iri("rc:Aggregation"): 3,
            self.expand_iri("rc:Relationship"): 4,
        }.get(relationship_kind, 99)

    def _relationship_columns_between_datasets(
        self,
        dataset_iri: str,
        related_dataset_iri: str,
        relationship: RelationshipDescription,
    ) -> list[ResourceSummary]:
        candidate_columns: list[ResourceSummary] = []
        for column in (
            relationship.foreign_key_from,
            relationship.foreign_key_to,
            *relationship.identifying_columns,
            *relationship.source_columns,
            *relationship.derived_columns,
            *relationship.group_by_columns,
            *[
                column
                for aggregated_column in relationship.aggregated_columns
                for column in (
                    aggregated_column.target_column,
                    *aggregated_column.source_columns,
                    aggregated_column.within_group_ordering,
                )
                if column is not None
            ],
        ):
            if column is not None and column.owning_dataset_iri in {
                dataset_iri,
                related_dataset_iri,
            }:
                candidate_columns.append(column)

        return list(
            {
                column.iri: column
                for column in sorted(
                    candidate_columns,
                    key=lambda item: (
                        item.owning_dataset_label or "",
                        item.column_name or "",
                        item.iri,
                    ),
                )
            }.values()
        )

    def _optional_resource_summary(
        self,
        graphs: list[str],
        iri: str | None,
    ) -> ResourceSummary | None:
        if iri is None:
            return None
        return self._resource_summary(graphs, iri)

    def _describe_caveat(
        self,
        caveat_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> CaveatDescription:
        severity = self._first_object(data_graphs, caveat_iri, "rc:severity")
        return CaveatDescription(
            iri=caveat_iri,
            label=self._display_label_from_graphs(lookup_graphs, caveat_iri),
            description=self._first_object(data_graphs, caveat_iri, "rc:caveatDescription")
            or self._description_from_graphs(lookup_graphs, caveat_iri),
            impact=self._first_object(data_graphs, caveat_iri, "rc:impact"),
            severity=self._optional_resource_summary(lookup_graphs, severity),
        )

    def _transformations_for_provenance(
        self,
        provenance_iris: Iterable[str],
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> list[TransformationDescription]:
        transformation_iris: list[str] = []
        for provenance_iri in provenance_iris:
            transformation_iris.extend(
                self._objects(data_graphs, provenance_iri, "rc:hasTransformation")
            )
        return [
            self._describe_transformation(transformation_iri, data_graphs, lookup_graphs)
            for transformation_iri in dict.fromkeys(transformation_iris)
        ]

    def _describe_transformation(
        self,
        transformation_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> TransformationDescription:
        return TransformationDescription(
            iri=transformation_iri,
            label=self._display_label_from_graphs(lookup_graphs, transformation_iri),
            description=self._description_from_graphs(lookup_graphs, transformation_iri),
            transformation_type=self._first_object(
                data_graphs,
                transformation_iri,
                "rc:transformationType",
            ),
            transformation_description=self._first_object(
                data_graphs,
                transformation_iri,
                "rc:transformationDescription",
            ),
        )

    def _relationships_for_dataset(
        self,
        dataset_iri: str,
        column_iris: Iterable[str],
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> list[RelationshipDescription]:
        relationship_iris: set[str] = set()
        relationship_iris.update(
            self._subjects(data_graphs, "rc:sourceDataset", dataset_iri)
        )
        relationship_iris.update(
            self._subjects(data_graphs, "rc:targetDataset", dataset_iri)
        )
        for column_iri in column_iris:
            for predicate in (
                "rc:foreignKeyFrom",
                "rc:foreignKeyTo",
                "rc:identifyingColumn",
                "rc:sourceColumn",
                "rc:derivedColumn",
                "rc:groupByColumn",
            ):
                relationship_iris.update(
                    self._subjects(data_graphs, predicate, column_iri)
                )
            for predicate in (
                "rc:targetColumn",
                "rc:aggregationSourceColumn",
                "rc:withinGroupOrdering",
            ):
                for aggregated_column_iri in self._subjects(
                    data_graphs,
                    predicate,
                    column_iri,
                ):
                    relationship_iris.update(
                        self._subjects(
                            data_graphs,
                            "rc:hasAggregatedColumn",
                            aggregated_column_iri,
                        )
                    )

        return [
            self._describe_relationship(relationship_iri, data_graphs, lookup_graphs)
            for relationship_iri in sorted(relationship_iris)
        ]

    def _describe_relationship(
        self,
        relationship_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> RelationshipDescription:
        types = self._types_from_graphs(data_graphs, relationship_iri)
        relationship_kind = self._first_matching_type(
            types,
            [
                "rc:ForeignKey",
                "rc:SharedIdentifier",
                "rc:Derivation",
                "rc:Aggregation",
                "rc:Relationship",
            ],
        )
        source_dataset = self._first_object(
            data_graphs,
            relationship_iri,
            "rc:sourceDataset",
        )
        target_dataset = self._first_object(
            data_graphs,
            relationship_iri,
            "rc:targetDataset",
        )
        foreign_key_from = self._first_object(
            data_graphs,
            relationship_iri,
            "rc:foreignKeyFrom",
        )
        foreign_key_to = self._first_object(
            data_graphs,
            relationship_iri,
            "rc:foreignKeyTo",
        )
        referential_integrity = self._first_object(
            data_graphs,
            relationship_iri,
            "rc:referentialIntegrity",
        )
        derivation_function = self._first_object(
            data_graphs,
            relationship_iri,
            "rc:derivationFunction",
        )
        source_dataset_summary = self._optional_resource_summary(
            lookup_graphs,
            source_dataset,
        )
        target_dataset_summary = self._optional_resource_summary(
            lookup_graphs,
            target_dataset,
        )
        foreign_key_from_summary = self._optional_resource_summary(
            lookup_graphs,
            foreign_key_from,
        )
        foreign_key_to_summary = self._optional_resource_summary(
            lookup_graphs,
            foreign_key_to,
        )
        identifying_columns = self._resource_summaries(
            lookup_graphs,
            self._objects(data_graphs, relationship_iri, "rc:identifyingColumn"),
        )
        source_columns = self._resource_summaries(
            lookup_graphs,
            self._objects(data_graphs, relationship_iri, "rc:sourceColumn"),
        )
        derived_columns = self._resource_summaries(
            lookup_graphs,
            self._objects(data_graphs, relationship_iri, "rc:derivedColumn"),
        )
        group_by_columns = self._resource_summaries(
            lookup_graphs,
            self._objects(data_graphs, relationship_iri, "rc:groupByColumn"),
        )
        aggregated_columns = [
            self._describe_aggregated_column(
                aggregated_column_iri,
                data_graphs,
                lookup_graphs,
            )
            for aggregated_column_iri in self._objects(
                data_graphs,
                relationship_iri,
                "rc:hasAggregatedColumn",
            )
        ]
        return RelationshipDescription(
            iri=relationship_iri,
            label=self._display_label_from_graphs(lookup_graphs, relationship_iri),
            description=self._description_from_graphs(lookup_graphs, relationship_iri),
            types=types,
            relationship_kind=relationship_kind,
            relationship_kind_label=self._label_for_resource(relationship_kind),
            source_dataset=source_dataset_summary,
            target_dataset=target_dataset_summary,
            foreign_key_from=foreign_key_from_summary,
            foreign_key_to=foreign_key_to_summary,
            referential_integrity=self._optional_resource_summary(
                lookup_graphs,
                referential_integrity,
            ),
            declared=self._bool_object(data_graphs, relationship_iri, "rc:declared"),
            identifying_columns=identifying_columns,
            source_columns=source_columns,
            derived_columns=derived_columns,
            derivation_function=self._optional_resource_summary(
                lookup_graphs,
                derivation_function,
            ),
            derivation_properties=self._resource_summaries(
                lookup_graphs,
                self._objects(
                    data_graphs,
                    relationship_iri,
                    "rc:hasDerivationProperty",
                ),
            ),
            group_by_columns=group_by_columns,
            aggregated_columns=aggregated_columns,
            source_caveats=self._relationship_source_caveats(
                data_graphs,
                lookup_graphs,
                source_dataset_summary,
                foreign_key_from_summary,
                source_columns,
                group_by_columns,
                aggregated_columns,
            ),
        )

    def _describe_aggregated_column(
        self,
        aggregated_column_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> AggregatedColumnDescription:
        target_column = self._first_object(
            data_graphs,
            aggregated_column_iri,
            "rc:targetColumn",
        )
        aggregation_function = self._first_object(
            data_graphs,
            aggregated_column_iri,
            "rc:aggregationFunction",
        )
        within_group_ordering = self._first_object(
            data_graphs,
            aggregated_column_iri,
            "rc:withinGroupOrdering",
        )
        return AggregatedColumnDescription(
            iri=aggregated_column_iri,
            target_column=self._optional_resource_summary(
                lookup_graphs,
                target_column,
            ),
            source_columns=self._resource_summaries(
                lookup_graphs,
                self._objects(
                    data_graphs,
                    aggregated_column_iri,
                    "rc:aggregationSourceColumn",
                ),
            ),
            aggregation_function=self._optional_resource_summary(
                lookup_graphs,
                aggregation_function,
            ),
            within_group_ordering=self._optional_resource_summary(
                lookup_graphs,
                within_group_ordering,
            ),
        )

    def _relationship_source_caveats(
        self,
        data_graphs: list[str],
        lookup_graphs: list[str],
        source_dataset: ResourceSummary | None,
        foreign_key_from: ResourceSummary | None,
        source_columns: list[ResourceSummary],
        group_by_columns: list[ResourceSummary],
        aggregated_columns: list[AggregatedColumnDescription],
    ) -> list[CaveatDescription]:
        source_resources: list[str] = []
        if source_dataset is not None:
            source_resources.append(source_dataset.iri)
        if foreign_key_from is not None:
            source_resources.append(foreign_key_from.iri)
            if foreign_key_from.owning_dataset_iri is not None:
                source_resources.append(foreign_key_from.owning_dataset_iri)
        for column in (*source_columns, *group_by_columns):
            source_resources.append(column.iri)
            if column.owning_dataset_iri is not None:
                source_resources.append(column.owning_dataset_iri)
        for aggregated_column in aggregated_columns:
            for column in aggregated_column.source_columns:
                source_resources.append(column.iri)
                if column.owning_dataset_iri is not None:
                    source_resources.append(column.owning_dataset_iri)
            if aggregated_column.within_group_ordering is not None:
                source_resources.append(aggregated_column.within_group_ordering.iri)
                if (
                    aggregated_column.within_group_ordering.owning_dataset_iri
                    is not None
                ):
                    source_resources.append(
                        aggregated_column.within_group_ordering.owning_dataset_iri
                    )

        caveat_iris: list[str] = []
        for resource_iri in dict.fromkeys(source_resources):
            caveat_iris.extend(
                self._objects(data_graphs, resource_iri, "rc:hasKnownCaveat")
            )
        return [
            self._describe_caveat(caveat_iri, data_graphs, lookup_graphs)
            for caveat_iri in sorted(set(caveat_iris))
        ]

    def _linked_patterns_for_dataset(
        self,
        target_iris: Iterable[str],
    ) -> list[ResourceSummary]:
        targets = list(dict.fromkeys(target_iris))
        pattern_graphs = self._expand_graphs(["patterns"])
        all_graphs = self._expand_graphs(["all"])
        all_lookup_graphs = self._lookup_graphs(all_graphs)
        pattern_iris: set[str] = set()

        for target_iri in targets:
            pattern_iris.update(
                self._subjects(pattern_graphs, "rc:patternTarget", target_iri)
            )
            pattern_iris.update(
                self._subjects(pattern_graphs, "rc:mapImplication", target_iri)
            )
            for claim_iri in self._subjects(all_graphs, "rc:claimTarget", target_iri):
                pattern_iris.update(
                    self._subjects(pattern_graphs, "rc:supportingClaim", claim_iri)
                )
            for observation_predicate in ("rc:observedAsset", "rc:observedColumn"):
                for observation_iri in self._subjects(
                    all_graphs,
                    observation_predicate,
                    target_iri,
                ):
                    pattern_iris.update(
                        self._subjects(
                            pattern_graphs,
                            "rc:supportingObservation",
                            observation_iri,
                        )
                    )

        return self._resource_summaries(
            all_lookup_graphs,
            sorted(pattern_iris),
            description_predicate="rc:patternText",
        )

    def _linked_pattern_reasons_for_dataset(
        self,
        target_iris: Iterable[str],
    ) -> list[LinkedPatternReason]:
        targets = list(dict.fromkeys(target_iris))
        pattern_graphs = self._expand_graphs(["patterns"])
        all_graphs = self._expand_graphs(["all"])
        all_lookup_graphs = self._lookup_graphs(all_graphs)
        matches_by_pattern: dict[str, list[LinkedPatternMatch]] = {}
        seen_matches: set[tuple[str, str, str, str | None, str | None]] = set()

        def add_match(
            pattern_iri: str,
            match_type: str,
            matched_iri: str,
            *,
            supporting_claim_iri: str | None = None,
            supporting_observation_iri: str | None = None,
        ) -> None:
            match_key = (
                pattern_iri,
                match_type,
                matched_iri,
                supporting_claim_iri,
                supporting_observation_iri,
            )
            if match_key in seen_matches:
                return
            seen_matches.add(match_key)
            matches_by_pattern.setdefault(pattern_iri, []).append(
                LinkedPatternMatch(
                    match_type=match_type,
                    matched_resource=self._resource_summary(
                        all_lookup_graphs,
                        matched_iri,
                        display_label=True,
                    ),
                    supporting_claim=(
                        self._resource_summary(
                            all_lookup_graphs,
                            supporting_claim_iri,
                            display_label=True,
                        )
                        if supporting_claim_iri is not None
                        else None
                    ),
                    supporting_observation=(
                        self._resource_summary(
                            all_lookup_graphs,
                            supporting_observation_iri,
                            display_label=True,
                        )
                        if supporting_observation_iri is not None
                        else None
                    ),
                )
            )

        for target_iri in targets:
            for pattern_iri in self._subjects(
                pattern_graphs,
                "rc:patternTarget",
                target_iri,
            ):
                add_match(pattern_iri, "pattern_target", target_iri)
            for pattern_iri in self._subjects(
                pattern_graphs,
                "rc:mapImplication",
                target_iri,
            ):
                add_match(pattern_iri, "map_implication", target_iri)
            for claim_iri in self._subjects(all_graphs, "rc:claimTarget", target_iri):
                for pattern_iri in self._subjects(
                    pattern_graphs,
                    "rc:supportingClaim",
                    claim_iri,
                ):
                    add_match(
                        pattern_iri,
                        "supporting_claim_target",
                        target_iri,
                        supporting_claim_iri=claim_iri,
                    )
            for observation_predicate, match_type in (
                ("rc:observedAsset", "supporting_observation_asset"),
                ("rc:observedColumn", "supporting_observation_column"),
            ):
                for observation_iri in self._subjects(
                    all_graphs,
                    observation_predicate,
                    target_iri,
                ):
                    for pattern_iri in self._subjects(
                        pattern_graphs,
                        "rc:supportingObservation",
                        observation_iri,
                    ):
                        add_match(
                            pattern_iri,
                            match_type,
                            target_iri,
                            supporting_observation_iri=observation_iri,
                        )

        linked_pattern_reasons: list[LinkedPatternReason] = []
        for pattern_iri, matches in sorted(
            matches_by_pattern.items(),
            key=lambda item: (
                self._display_label_from_graphs(all_lookup_graphs, item[0]) or "",
                item[0],
            ),
        ):
            match_groups = self._linked_pattern_match_groups(
                matches,
                all_graphs,
            )
            linked_pattern_reasons.append(
                LinkedPatternReason(
                    iri=pattern_iri,
                    pattern_iri=pattern_iri,
                    label=self._display_label_from_graphs(
                        all_lookup_graphs,
                        pattern_iri,
                    ),
                    pattern_text=self._first_object(
                        all_graphs,
                        pattern_iri,
                        "rc:patternText",
                    ),
                    rationale=self._first_object(
                        all_graphs,
                        pattern_iri,
                        "rc:rationale",
                    ),
                    match_group_count=len(match_groups),
                    raw_match_count=len(matches),
                    relevance_tier_counts=self._linked_pattern_relevance_tier_counts(
                        match_groups
                    ),
                    match_groups=match_groups,
                    matches=sorted(
                        matches,
                        key=lambda match: (
                            match.match_type,
                            match.matched_resource.label or "",
                            match.matched_resource.iri,
                        ),
                    ),
                ),
            )
        return linked_pattern_reasons

    def _linked_pattern_match_groups(
        self,
        matches: Iterable[LinkedPatternMatch],
        all_graphs: list[str],
    ) -> list[LinkedPatternMatchGroup]:
        grouped: dict[str, list[LinkedPatternMatch]] = {}
        for match in matches:
            grouped.setdefault(match.matched_resource.iri, []).append(match)

        groups: list[LinkedPatternMatchGroup] = []
        for group_matches in sorted(
            grouped.values(),
            key=lambda group_matches: (
                self._linked_pattern_relevance_rank(
                    self._linked_pattern_relevance_tier(group_matches)
                ),
                group_matches[0].matched_resource.label or "",
                group_matches[0].matched_resource.iri,
            ),
        ):
            matched_resource = group_matches[0].matched_resource
            route_types = sorted(
                {match.match_type for match in group_matches},
                key=self._linked_pattern_match_type_priority,
            )
            groups.append(
                LinkedPatternMatchGroup(
                    matched_resource=matched_resource,
                    matched_resource_types=self._types_from_graphs(
                        all_graphs,
                        matched_resource.iri,
                    ),
                    matched_resource_kind=self._matched_resource_kind(
                        all_graphs,
                        matched_resource.iri,
                    ),
                    relevance_tier=self._linked_pattern_relevance_tier(group_matches),
                    route_types=route_types,
                    route_labels=[
                        self._linked_pattern_match_type_label(match_type)
                        for match_type in route_types
                    ],
                    supporting_claims=self._unique_optional_summaries(
                        match.supporting_claim for match in group_matches
                    ),
                    supporting_observations=self._unique_optional_summaries(
                        match.supporting_observation for match in group_matches
                    ),
                )
            )
        return groups

    def _linked_pattern_match_type_label(self, match_type: str) -> str:
        return {
            "pattern_target": "direct pattern target",
            "map_implication": "map implication",
            "supporting_claim_target": "via supporting claim target",
            "supporting_observation_asset": "via supporting observation asset",
            "supporting_observation_column": "via supporting observation column",
        }.get(match_type, match_type.replace("_", " "))

    def _linked_pattern_match_type_priority(self, match_type: str) -> int:
        return {
            "pattern_target": 0,
            "map_implication": 1,
            "supporting_claim_target": 2,
            "supporting_observation_asset": 3,
            "supporting_observation_column": 4,
        }.get(match_type, 99)

    def _linked_pattern_relevance_tier(
        self,
        matches: Iterable[LinkedPatternMatch],
    ) -> str:
        match_types = {match.match_type for match in matches}
        if "pattern_target" in match_types:
            return "direct"
        if "map_implication" in match_types:
            return "map_implication"
        if "supporting_claim_target" in match_types:
            return "claim_supported"
        if any(
            match_type.startswith("supporting_observation_")
            for match_type in match_types
        ):
            return "observation_supported"
        return "background"

    def _linked_pattern_relevance_rank(self, relevance_tier: str) -> int:
        return {
            "direct": 0,
            "map_implication": 1,
            "claim_supported": 2,
            "observation_supported": 3,
            "background": 4,
        }.get(relevance_tier, 99)

    def _linked_pattern_relevance_tier_counts(
        self,
        match_groups: Iterable[LinkedPatternMatchGroup],
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for match_group in match_groups:
            counts[match_group.relevance_tier] = (
                counts.get(match_group.relevance_tier, 0) + 1
            )
        return counts

    def _matched_resource_kind(self, graphs: list[str], iri: str) -> str | None:
        matched_type = self._first_matching_type(
            self._types_from_graphs(graphs, iri),
            [
                "rc:Table",
                "rc:Dataset",
                "rc:Column",
                "rc:KnownCaveat",
                "rc:ForeignKey",
                "rc:SharedIdentifier",
                "rc:Derivation",
                "rc:Claim",
                "rc:Observation",
                "rc:ProfileObservation",
                "rc:Evidence",
                "rc:SourceSpan",
            ],
        )
        return self._label_for_resource(matched_type)

    def _unique_optional_summaries(
        self,
        summaries: Iterable[ResourceSummary | None],
    ) -> list[ResourceSummary]:
        return list(
            {
                summary.iri: summary
                for summary in summaries
                if summary is not None
            }.values()
        )

    def _first_matching_type(
        self,
        types: Iterable[str],
        candidates: Iterable[str],
    ) -> str | None:
        type_set = set(types)
        for candidate in candidates:
            expanded = self.expand_iri(candidate)
            if expanded in type_set:
                return expanded
        return None

    def _resource_summary(
        self,
        graphs: list[str],
        iri: str,
        *,
        description_predicate: str = "rdfs:comment",
        display_label: bool = False,
    ) -> ResourceSummary:
        column_name = self._first_object(graphs, iri, "rc:columnName")
        owning_dataset_iri = self._first_owner_dataset_iri(graphs, iri)
        label = (
            self._display_label_from_graphs(graphs, iri)
            if display_label
            else self._label_from_graphs(graphs, iri)
        )
        return ResourceSummary(
            iri=iri,
            label=label or column_name or self._local_name(iri),
            description=self._resource_description_from_graphs(
                graphs,
                iri,
                description_predicate=description_predicate,
            ),
            column_name=column_name,
            owning_dataset_iri=owning_dataset_iri,
            owning_dataset_label=(
                self._display_label_from_graphs(graphs, owning_dataset_iri)
                if owning_dataset_iri is not None
                else None
            ),
        )

    def _objects(self, graphs: list[str], subject: str, predicate: str) -> list[str]:
        graph_filter, params = self._graph_filter(graphs, alias="q")
        return [
            row["object"]
            for row in self._conn.execute(
                f"""
                SELECT q.object
                FROM quads q
                WHERE q.subject = ?
                  AND q.predicate = ?
                  {graph_filter}
                ORDER BY q.object
                """,
                [subject, self.expand_iri(predicate), *params],
            )
        ]

    def _subjects(self, graphs: list[str], predicate: str, object_value: str) -> list[str]:
        graph_filter, params = self._graph_filter(graphs, alias="q")
        return [
            row["subject"]
            for row in self._conn.execute(
                f"""
                SELECT q.subject
                FROM quads q
                WHERE q.predicate = ?
                  AND q.object = ?
                  {graph_filter}
                ORDER BY q.subject
                """,
                [self.expand_iri(predicate), object_value, *params],
            )
        ]

    def _first_object(self, graphs: list[str], subject: str, predicate: str) -> str | None:
        objects = self._objects(graphs, subject, predicate)
        return objects[0] if objects else None

    def _first_subject(
        self,
        graphs: list[str],
        predicate: str,
        object_value: str,
    ) -> str | None:
        subjects = self._subjects(graphs, predicate, object_value)
        return subjects[0] if subjects else None

    def _bool_object(self, graphs: list[str], subject: str, predicate: str) -> bool | None:
        value = self._first_object(graphs, subject, predicate)
        if value is None:
            return None
        return value.lower() in {"1", "true"}

    def _int_object(self, graphs: list[str], subject: str, predicate: str) -> int | None:
        value = self._first_object(graphs, subject, predicate)
        return int(value) if value is not None else None

    def _label_from_graphs(self, graphs: list[str], subject: str) -> str | None:
        return self._first_object(graphs, subject, str(RDFS.label))

    def _description_from_graphs(self, graphs: list[str], subject: str) -> str | None:
        return self._first_object(graphs, subject, str(RDFS.comment))

    def _resource_description_from_graphs(
        self,
        graphs: list[str],
        subject: str,
        *,
        description_predicate: str = "rdfs:comment",
    ) -> str | None:
        predicates = dict.fromkeys(
            [
                description_predicate,
                str(RDFS.comment),
                str(DCTERMS.description),
                "rc:caveatDescription",
                "rc:transformationDescription",
                "rc:sourceDescription",
                "rc:impact",
            ]
        )
        for predicate in predicates:
            description = self._first_object(graphs, subject, predicate)
            if description is not None:
                return description
        return self._synthesized_relationship_description_from_graphs(graphs, subject)

    def _synthesized_relationship_description_from_graphs(
        self,
        graphs: list[str],
        subject: str,
    ) -> str | None:
        types = self._types_from_graphs(graphs, subject)
        relationship_kind = self._first_matching_type(
            types,
            [
                "rc:ForeignKey",
                "rc:SharedIdentifier",
                "rc:Derivation",
                "rc:Aggregation",
                "rc:Relationship",
            ],
        )
        if relationship_kind == self.expand_iri("rc:ForeignKey"):
            from_column = self._first_object(graphs, subject, "rc:foreignKeyFrom")
            to_column = self._first_object(graphs, subject, "rc:foreignKeyTo")
            if from_column is None or to_column is None:
                return None
            detail = (
                "Foreign key from "
                f"{self._compact_resource_label(graphs, from_column)} to "
                f"{self._compact_resource_label(graphs, to_column)}"
            )
            integrity = self._first_object(graphs, subject, "rc:referentialIntegrity")
            if integrity is not None:
                detail += (
                    "; referential integrity: "
                    f"{self._compact_resource_label(graphs, integrity)}"
                )
            declared = self._bool_object(graphs, subject, "rc:declared")
            if declared is not None:
                detail += f"; declared: {str(declared).lower()}"
            return detail
        if relationship_kind == self.expand_iri("rc:SharedIdentifier"):
            columns = [
                self._compact_resource_label(graphs, column)
                for column in self._objects(graphs, subject, "rc:identifyingColumn")
            ]
            if not columns:
                return None
            return "Shared identifier across " + ", ".join(columns)
        if relationship_kind == self.expand_iri("rc:Derivation"):
            source_columns = [
                self._compact_resource_label(graphs, column)
                for column in self._objects(graphs, subject, "rc:sourceColumn")
            ]
            derived_columns = [
                self._compact_resource_label(graphs, column)
                for column in self._objects(graphs, subject, "rc:derivedColumn")
            ]
            if not source_columns or not derived_columns:
                return None
            detail = (
                "Derivation from "
                f"{', '.join(source_columns)} to {', '.join(derived_columns)}"
            )
            function_iri = self._first_object(graphs, subject, "rc:derivationFunction")
            if function_iri is not None:
                function_label = self._compact_resource_label(graphs, function_iri)
                detail += f"; function: {function_label}"
            return detail
        return None

    def _compact_resource_label(self, graphs: list[str], subject: str) -> str:
        return (
            self._display_label_from_graphs(graphs, subject)
            or self._first_object(graphs, subject, "rc:columnName")
            or self._local_name(subject)
        )

    def _display_label_from_graphs(self, graphs: list[str], subject: str) -> str | None:
        return (
            self._label_from_graphs(graphs, subject)
            or self._first_object(graphs, subject, "rc:summary")
            or self._first_object(graphs, subject, "rc:patternText")
            or self._first_object(graphs, subject, "rc:claimText")
            or self._description_from_graphs(graphs, subject)
        )

    def _types_from_graphs(self, graphs: list[str], subject: str) -> list[str]:
        return self._objects(graphs, subject, str(RDF.type))

    def _resource_summaries(
        self,
        graphs: list[str],
        iris: Iterable[str],
        *,
        description_predicate: str = "rdfs:comment",
    ) -> list[ResourceSummary]:
        return [
            self._resource_summary(
                graphs,
                iri,
                description_predicate=description_predicate,
                display_label=True,
            )
            for iri in iris
        ]

    def _first_owner_dataset_iri(self, graphs: list[str], iri: str) -> str | None:
        return self._first_subject(graphs, "rc:hasColumn", iri)

    def _describe_claim(
        self,
        claim_iri: str,
        graphs: list[str],
        lookup_graphs: list[str],
    ) -> ClaimDescription:
        claim_kind = self._first_object(graphs, claim_iri, "rc:claimKind")
        confidence = self._first_object(graphs, claim_iri, "rc:confidence")
        observation_status = self._first_object(
            graphs,
            claim_iri,
            "rc:observationStatus",
        )
        outgoing_reconsiderations = self._claim_reconsiderations_for_claim(
            claim_iri,
            graphs,
            lookup_graphs,
            direction="outgoing",
        )
        incoming_reconsiderations = self._claim_reconsiderations_for_claim(
            claim_iri,
            graphs,
            lookup_graphs,
            direction="incoming",
        )
        return ClaimDescription(
            iri=claim_iri,
            label=self._display_label_from_graphs(lookup_graphs, claim_iri),
            claim_text=self._first_object(graphs, claim_iri, "rc:claimText"),
            claim_kind=claim_kind,
            claim_kind_label=self._label_for_resource(claim_kind),
            claim_targets=self._resource_summaries(
                lookup_graphs,
                self._objects(graphs, claim_iri, "rc:claimTarget"),
            ),
            confidence=confidence,
            confidence_label=self._label_for_resource(confidence),
            observation_status=observation_status,
            observation_status_label=self._label_for_resource(observation_status),
            proposed_assertions=self._resource_summaries(
                lookup_graphs,
                self._objects(graphs, claim_iri, "rc:proposedAssertion"),
            ),
            lifecycle_summary=self._claim_lifecycle_summary(
                observation_status,
                outgoing_reconsiderations,
                incoming_reconsiderations,
            ),
            outgoing_reconsiderations=outgoing_reconsiderations,
            incoming_reconsiderations=incoming_reconsiderations,
        )

    def _claim_lifecycle_summary(
        self,
        observation_status: str | None,
        outgoing_reconsiderations: list[ClaimReconsiderationDescription],
        incoming_reconsiderations: list[ClaimReconsiderationDescription],
    ) -> str | None:
        parts: list[str] = []
        status_label = self._label_for_resource(observation_status)
        if status_label is not None:
            parts.append(f"Current status: {status_label}.")
        if incoming_reconsiderations:
            parts.append(
                "Later claims reconsider this claim: "
                f"{self._reconsideration_count_summary(incoming_reconsiderations)}."
            )
        if outgoing_reconsiderations:
            parts.append(
                "This claim reconsiders earlier claims: "
                f"{self._reconsideration_count_summary(outgoing_reconsiderations)}."
            )
        return " ".join(parts) if parts else None

    def _reconsideration_count_summary(
        self,
        reconsiderations: Iterable[ClaimReconsiderationDescription],
    ) -> str:
        counts: dict[str, int] = {}
        for reconsideration in reconsiderations:
            label = reconsideration.relation_label or "reconsideration"
            counts[label] = counts.get(label, 0) + 1
        return ", ".join(
            f"{count} {label}{'' if count == 1 else 's'}"
            for label, count in sorted(counts.items())
        )

    def _claim_reconsiderations_for_claim(
        self,
        claim_iri: str,
        graphs: list[str],
        lookup_graphs: list[str],
        *,
        direction: TypingLiteral["outgoing", "incoming"],
    ) -> list[ClaimReconsiderationDescription]:
        predicate = (
            "rc:reconsideringClaim"
            if direction == "outgoing"
            else "rc:reconsideredClaim"
        )
        reconsideration_iris = self._subjects(graphs, predicate, claim_iri)
        return [
            self._describe_claim_reconsideration(
                reconsideration_iri,
                graphs,
                lookup_graphs,
            )
            for reconsideration_iri in reconsideration_iris
        ]

    def _describe_claim_reconsideration(
        self,
        reconsideration_iri: str,
        graphs: list[str],
        lookup_graphs: list[str],
    ) -> ClaimReconsiderationDescription:
        relation = self._first_object(
            graphs,
            reconsideration_iri,
            "rc:reconsiderationRelation",
        )
        newer_claim = self._first_object(
            graphs,
            reconsideration_iri,
            "rc:reconsideringClaim",
        )
        older_claim = self._first_object(
            graphs,
            reconsideration_iri,
            "rc:reconsideredClaim",
        )
        return ClaimReconsiderationDescription(
            iri=reconsideration_iri,
            label=self._display_label_from_graphs(lookup_graphs, reconsideration_iri),
            summary=self._first_object(graphs, reconsideration_iri, "rc:summary"),
            rationale=self._first_object(
                graphs,
                reconsideration_iri,
                "rc:reconsiderationRationale",
            ),
            relation=relation,
            relation_label=self._label_for_resource(relation),
            newer_claim=(
                self._resource_summary(
                    lookup_graphs,
                    newer_claim,
                    description_predicate="rc:claimText",
                    display_label=True,
                )
                if newer_claim is not None
                else None
            ),
            older_claim=(
                self._resource_summary(
                    lookup_graphs,
                    older_claim,
                    description_predicate="rc:claimText",
                    display_label=True,
                )
                if older_claim is not None
                else None
            ),
            evidence=[
                self._describe_evidence(evidence_iri, graphs, lookup_graphs)
                for evidence_iri in self._objects(
                    graphs,
                    reconsideration_iri,
                    "rc:evidence",
                )
            ],
            reconsidered_at=self._first_object(
                graphs,
                reconsideration_iri,
                "rc:reconsideredAt",
            ),
            reconsidered_by=self._first_object(
                graphs,
                reconsideration_iri,
                "rc:reconsideredBy",
            ),
        )

    def _describe_evidence(
        self,
        evidence_iri: str,
        graphs: list[str],
        lookup_graphs: list[str],
    ) -> EvidenceDescription:
        return EvidenceDescription(
            iri=evidence_iri,
            label=self._display_label_from_graphs(lookup_graphs, evidence_iri),
            summary=self._first_object(graphs, evidence_iri, "rc:summary"),
            sources=self._objects(graphs, evidence_iri, str(DCTERMS.source)),
            source_spans=[
                self._describe_source_span(span_iri, graphs)
                for span_iri in self._objects(graphs, evidence_iri, "rc:sourceSpan")
            ],
        )

    def _describe_source_span(
        self,
        source_span_iri: str,
        graphs: list[str],
    ) -> SourceSpanDescription:
        source_kind = self._first_object(graphs, source_span_iri, "rc:sourceKind")
        return SourceSpanDescription(
            iri=source_span_iri,
            source_path=self._first_object(graphs, source_span_iri, "rc:sourcePath"),
            source_section=self._first_object(
                graphs,
                source_span_iri,
                "rc:sourceSection",
            ),
            start_line=self._int_object(graphs, source_span_iri, "rc:startLine"),
            end_line=self._int_object(graphs, source_span_iri, "rc:endLine"),
            source_kind=source_kind,
            source_kind_label=self._label_for_resource(source_kind),
        )

    def _describe_staged_graph_patch(
        self,
        patch_iri: str,
        graphs: list[str],
    ) -> StagedGraphPatchDescription:
        operation = self._first_object(graphs, patch_iri, "rc:patchOperation")
        patch_role = self._first_object(graphs, patch_iri, "rc:patchRole")
        return StagedGraphPatchDescription(
            iri=patch_iri,
            operation=operation,
            operation_label=self._label_for_resource(operation),
            target_graph=self._first_object(graphs, patch_iri, "rc:targetGraph"),
            format=self._first_object(graphs, patch_iri, "rc:patchFormat"),
            patch_role=patch_role,
            patch_role_label=self._label_for_resource(patch_role),
            triple_count=self._int_object(graphs, patch_iri, "rc:patchTripleCount"),
            before_triple_count=self._int_object(
                graphs,
                patch_iri,
                "rc:beforeTripleCount",
            ),
            after_triple_count=self._int_object(
                graphs,
                patch_iri,
                "rc:afterTripleCount",
            ),
            content=self._first_object(graphs, patch_iri, "rc:patchContent"),
        )

    def _staged_patch_sort_key(
        self,
        patch: StagedGraphPatchDescription,
    ) -> tuple[int, str, str]:
        shared_role = self.expand_iri("rc:SharedContextPatch")
        role_rank = 0 if patch.patch_role == shared_role else 1
        return (role_rank, patch.target_graph or "", patch.iri)

    def _label_for_resource(self, iri: str | None) -> str | None:
        if iri is None:
            return None
        return self._label_from_graphs(
            self._expand_graphs(["ontology"]),
            iri,
        ) or self._local_name(iri)

    def _local_name(self, iri: str) -> str | None:
        if "#" in iri:
            return iri.rsplit("#", 1)[1]
        if "/" in iri:
            return iri.rstrip("/").rsplit("/", 1)[1]
        return None

    def _graph_revision_snapshots(
        self,
        revision_iri: str,
        graphs: list[str],
    ) -> list[GraphSnapshotDescription]:
        snapshots: list[GraphSnapshotDescription] = []
        for snapshot_iri in self._objects(graphs, revision_iri, "rc:hasGraphSnapshot"):
            graph_role = self._first_object(graphs, snapshot_iri, "rc:graphRole")
            triple_count = self._int_object(graphs, snapshot_iri, "rc:tripleCount")
            if graph_role is None or triple_count is None:
                continue
            snapshots.append(
                GraphSnapshotDescription(
                    graph_role=graph_role,
                    triple_count=triple_count,
                )
            )
        return sorted(snapshots, key=lambda snapshot: snapshot.graph_role)

    def _graph_revision_validation_results(
        self,
        revision_iri: str,
        graphs: list[str],
    ) -> list[ValidationDiagnostic]:
        sh = PREFIXES["sh"]
        diagnostics: list[ValidationDiagnostic] = []
        for result_iri in self._objects(graphs, revision_iri, "rc:hasValidationResult"):
            focus_node = self._first_object(graphs, result_iri, sh + "focusNode")
            result_path = self._first_object(graphs, result_iri, sh + "resultPath")
            value = self._first_object(graphs, result_iri, sh + "value")
            source_shape = self._first_object(graphs, result_iri, sh + "sourceShape")
            source_constraint_component = self._first_object(
                graphs,
                result_iri,
                sh + "sourceConstraintComponent",
            )
            severity = self._first_object(graphs, result_iri, sh + "resultSeverity")
            diagnostics.append(
                ValidationDiagnostic(
                    iri=result_iri,
                    focus_node=focus_node,
                    focus_node_label=self._diagnostic_resource_label(focus_node),
                    result_path=result_path,
                    result_path_label=self._diagnostic_resource_label(result_path),
                    value=value,
                    source_shape=source_shape,
                    source_constraint_component=source_constraint_component,
                    source_constraint_component_label=self._diagnostic_resource_label(
                        source_constraint_component
                    ),
                    severity=severity,
                    severity_label=self._diagnostic_resource_label(severity),
                    messages=self._objects(graphs, result_iri, sh + "resultMessage"),
                )
            )
        return sorted(diagnostics, key=self._validation_diagnostic_sort_key)

    def _mint_iri(self, kind: str) -> str:
        return f"https://richcanopy.org/doxabase/generated/{kind}/{uuid4()}"

    def _bind_prefixes(self, graph: Graph) -> None:
        for prefix, namespace in PREFIXES.items():
            graph.bind(prefix, namespace)

    def _datetime_literal(
        self,
        value: datetime | str | None,
        *,
        name: str = "observed_at",
    ) -> Literal:
        if value is None:
            dt = datetime.now(UTC)
        elif isinstance(value, datetime):
            dt = value
        else:
            text = value.strip()
            if text.endswith("Z"):
                text = f"{text[:-1]}+00:00"
            try:
                dt = datetime.fromisoformat(text)
            except ValueError as exc:
                raise DoxaBaseError(
                    f"{name} must be an ISO 8601 datetime"
                ) from exc
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return Literal(dt.astimezone(UTC).isoformat(), datatype=XSD.dateTime)

    def _resource_or_literal(self, value: str) -> Identifier:
        expanded = self.expand_iri(value)
        if "://" in expanded or expanded.startswith("urn:") or ":" in value:
            return URIRef(expanded)
        return Literal(value)

    def _validate_resource_values(self, name: str, values: Iterable[str]) -> None:
        for value in values:
            self._resource_ref(name, value)

    def _resource_ref(self, name: str, value: str) -> URIRef:
        text = value.strip()
        if not text:
            raise DoxaBaseError(f"{name} values must not be empty")
        if re.search(r"\s", text):
            raise DoxaBaseError(
                f"{name} values must be IRIs or CURIEs, not prose: {value!r}"
            )
        expanded = self.expand_iri(text)
        if "://" not in expanded and not expanded.startswith("urn:") and ":" not in text:
            raise DoxaBaseError(
                f"{name} values must be IRIs or CURIEs, not plain names: {value!r}"
            )
        return URIRef(expanded)

    def _write_export(
        self,
        path: str | Path,
        data: str,
        *,
        overwrite: bool,
    ) -> int:
        output_path = Path(path)
        if output_path.exists() and not overwrite:
            raise DoxaBaseError(
                f"Export path already exists: {output_path}. Use overwrite=True to replace it."
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(data, encoding="utf-8")
        return len(data.encode("utf-8"))

    def _required_iri(self, name: str, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise DoxaBaseError(f"{name} must not be empty")
        return self.expand_iri(cleaned)

    def _claim_reconsideration_relation(
        self,
        relation: str,
    ) -> tuple[str, str, str | None]:
        text = relation.strip()
        if not text:
            raise DoxaBaseError("relation must not be empty")
        expanded = self.expand_iri(text)
        for name, (relation_iri, predicate, status) in (
            CLAIM_RECONSIDERATION_RELATIONS.items()
        ):
            expanded_relation = self.expand_iri(relation_iri)
            if text == name or expanded == expanded_relation:
                return expanded_relation, predicate, status
        allowed = ", ".join(CLAIM_RECONSIDERATION_RELATIONS)
        raise DoxaBaseError(f"relation must be one of: {allowed}")

    def _ensure_claim_resource(self, name: str, iri: str) -> None:
        graphs = self._expand_graphs(["all"])
        if self.expand_iri("rc:Claim") not in self._types_from_graphs(graphs, iri):
            raise DoxaBaseError(f"{name} must identify an existing rc:Claim")

    def _add_optional_literal(
        self,
        graph: Graph,
        subject: URIRef,
        predicate: str,
        value: str | None,
    ) -> None:
        if value is not None and value.strip():
            graph.add((subject, URIRef(self.expand_iri(predicate)), Literal(value.strip())))

    def _ensure_non_negative(self, name: str, value: int | None) -> None:
        if value is not None and value < 0:
            raise DoxaBaseError(f"{name} must be non-negative")

    def _string_values(
        self,
        name: str,
        value: Iterable[str] | str | None,
        *,
        required: bool = False,
    ) -> list[str]:
        if value is None:
            values: list[str] = []
        elif isinstance(value, str):
            values = [value]
        else:
            values = list(value)
        cleaned = [item.strip() for item in values if item.strip()]
        if required and not cleaned:
            raise DoxaBaseError(f"{name} must contain at least one non-empty value")
        return cleaned

    def _replace_subject_triples(
        self,
        graph: str,
        subject: str,
        predicates: Iterable[str],
        rdf_graph: Graph,
    ) -> int:
        self._ensure_mutable(graph)
        predicate_values = list(dict.fromkeys(predicates))
        if predicate_values:
            placeholders = ",".join("?" for _ in predicate_values)
            self._conn.execute(
                f"""
                DELETE FROM quads
                WHERE graph = ?
                  AND subject = ?
                  AND predicate IN ({placeholders})
                """,
                [graph, subject, *predicate_values],
            )
            self._conn.commit()
        return self._insert_graph(graph, rdf_graph)

    def _resource_triples(
        self,
        graphs: list[str],
        *,
        subject: str | None = None,
        object_value: str | None = None,
        object_kind: str | None = None,
        limit: int = 100,
    ) -> list[ResourceTriple]:
        graph_filter, graph_params = self._graph_filter(graphs, alias="q")
        filters: list[str] = []
        params: list[Any] = []
        if subject is not None:
            filters.append("q.subject = ?")
            params.append(subject)
        if object_value is not None:
            filters.append("q.object = ?")
            params.append(object_value)
        if object_kind is not None:
            filters.append("q.object_kind = ?")
            params.append(object_kind)
        if not filters:
            raise DoxaBaseError("Resource triple lookup requires subject or object")
        where = " AND ".join(filters)
        rows = self._conn.execute(
            f"""
            SELECT
                q.graph,
                q.subject,
                q.subject_kind,
                q.predicate,
                q.object,
                q.object_kind,
                q.datatype,
                q.lang
            FROM quads q
            WHERE {where}
              {graph_filter}
            ORDER BY q.graph, q.subject, q.predicate, q.object
            LIMIT ?
            """,
            [*params, *graph_params, limit],
        ).fetchall()
        return [self._resource_triple_from_row(row) for row in rows]

    def _resource_triple_from_row(self, row: sqlite3.Row) -> ResourceTriple:
        lookup_graphs = self._lookup_graphs([row["graph"]])
        object_is_resource = row["object_kind"] in {"uri", "bnode"}
        return ResourceTriple(
            graph=row["graph"],
            subject=row["subject"],
            subject_kind=row["subject_kind"],
            subject_label=self._display_label_from_graphs(
                lookup_graphs,
                row["subject"],
            ),
            subject_types=self._types_from_graphs(lookup_graphs, row["subject"]),
            predicate=row["predicate"],
            predicate_label=self._label_from_graphs(
                self._expand_graphs(["ontology"]),
                row["predicate"],
            ),
            object=row["object"],
            object_kind=row["object_kind"],
            object_label=(
                self._display_label_from_graphs(lookup_graphs, row["object"])
                if object_is_resource
                else None
            ),
            object_types=(
                self._types_from_graphs(lookup_graphs, row["object"])
                if object_is_resource
                else []
            ),
            object_datatype=row["datatype"],
            object_lang=row["lang"],
        )

    def _graph_filter(self, graphs: list[str], *, alias: str | None = None) -> tuple[str, list[str]]:
        if not graphs:
            return "", []
        column = f"{alias}.graph" if alias else "graph"
        return f"AND {column} IN ({','.join('?' for _ in graphs)})", graphs.copy()

    def _term_to_storage(self, term: Node) -> tuple[str, str]:
        if isinstance(term, URIRef):
            return str(term), "uri"
        if isinstance(term, BNode):
            return str(term), "bnode"
        raise TypeError(f"Unsupported subject term: {term!r}")

    def _object_to_storage(self, term: Node) -> tuple[str, str, str | None, str | None]:
        if isinstance(term, URIRef):
            return str(term), "uri", None, None
        if isinstance(term, BNode):
            return str(term), "bnode", None, None
        if isinstance(term, Literal):
            return str(term), "literal", str(term.datatype) if term.datatype else None, term.language
        raise TypeError(f"Unsupported object term: {term!r}")

    def _term_from_row(self, value: str, kind: str) -> Identifier:
        if kind == "uri":
            return URIRef(value)
        if kind == "bnode":
            return BNode(value)
        raise TypeError(f"Unsupported subject kind: {kind}")

    def _object_from_row(self, row: sqlite3.Row) -> Identifier:
        if row["object_kind"] == "uri":
            return URIRef(row["object"])
        if row["object_kind"] == "bnode":
            return BNode(row["object"])
        if row["object_kind"] == "literal":
            return Literal(row["object"], lang=row["lang"], datatype=row["datatype"])
        raise TypeError(f"Unsupported object kind: {row['object_kind']}")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _fts_query(query: str) -> str:
    return _fts_query_from_tokens(_search_tokens(query))


def _search_tokens(query: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9]+", query)
    if not tokens:
        raise DoxaBaseError("Search query must contain at least one searchable token")
    return [token.lower() for token in tokens]


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
