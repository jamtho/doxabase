from __future__ import annotations

import re
import sqlite3
import warnings
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Literal as TypingLiteral
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
class GraphSnapshotDescription:
    graph_role: str
    triple_count: int


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
    graph_snapshots: list[GraphSnapshotDescription]
    supporting_observations: list[ResourceSummary]
    supporting_claims: list[ResourceSummary]
    supporting_patterns: list[ResourceSummary]
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


@dataclass(frozen=True)
class PartitionDescription:
    iri: str
    label: str | None
    description: str | None
    partition_column: ResourceSummary | None
    granularity: ResourceSummary | None
    path_template: str | None
    redundant_partition_key: ResourceSummary | None


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
    columns: list[ColumnDescription]
    path_templates: list[str]
    physical_layouts: list[PhysicalLayoutDescription]
    storage_accesses: list[StorageAccessDescription]
    partition_schemes: list[PartitionDescription]
    caveats: list[CaveatDescription]
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
    resources: list[ContextSliceResource]
    resource_count: int
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
        return ResourceContext(
            iri=resource_iri,
            graph=graph,
            label=self._display_label_from_graphs(lookup_graphs, resource_iri),
            description=self._description_from_graphs(lookup_graphs, resource_iri),
            types=self._types_from_graphs(graphs, resource_iri),
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
                        f"linked pattern {group.relevance_tier}",
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

        return ContextSlice(
            profile=profile,
            seeds=[
                self._resource_summary(all_lookup_graphs, seed, display_label=True)
                for seed in seeds
            ],
            resources=[
                self._context_slice_resource(iri, routes, all_lookup_graphs)
                for iri, routes in self._context_slice_ordered_resources(
                    resources,
                    all_lookup_graphs,
                )
            ],
            resource_count=len(resources),
            route_counts=self._context_slice_route_counts(resources),
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
            "supporting_observation": 11,
            "evidence": 12,
            "source_span": 13,
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

        fts_query = _fts_query(query)
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
            columns=columns,
            path_templates=path_templates,
            physical_layouts=physical_layouts,
            storage_accesses=storage_accesses,
            partition_schemes=partition_schemes,
            caveats=[
                self._describe_caveat(caveat_iri, data_graphs, lookup_graphs)
                for caveat_iri in caveat_iris
            ],
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

    def record_map_relationship(
        self,
        iri: str,
        *,
        relationship_type: TypingLiteral[
            "foreign_key",
            "shared_identifier",
            "derivation",
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
        derivation_property_values = self._string_values(
            "derivation_properties",
            derivation_properties,
        )
        type_map = {
            "foreign_key": "rc:ForeignKey",
            "shared_identifier": "rc:SharedIdentifier",
            "derivation": "rc:Derivation",
        }
        resource_type = type_map.get(relationship_type)
        if resource_type is None:
            raise DoxaBaseError(
                "relationship_type must be 'foreign_key', 'shared_identifier', or 'derivation'"
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
        ]
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
        evidence: Iterable[str] | str | None = None,
        export_path: str | None = None,
        graph_counts: dict[str, int] | None = None,
        validation_scope: str | None = None,
        validation_conforms: bool | None = None,
        validation_result_count: int | None = None,
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
        evidence_values = self._string_values("evidence", evidence)
        self._validate_resource_values(
            "supporting_observations",
            supporting_observation_values,
        )
        self._validate_resource_values("supporting_claims", supporting_claim_values)
        self._validate_resource_values("supporting_patterns", supporting_pattern_values)
        self._validate_resource_values("evidence", evidence_values)
        self._ensure_non_negative(
            "validation_result_count",
            validation_result_count,
        )
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
        result_count = sum(1 for _ in report_graph.subjects(RDF.type, URIRef(PREFIXES["sh"] + "ValidationResult")))
        if result_count > limit_results:
            report_text = f"{report_text}\n\nResult output limited by caller to {limit_results} results."
        return ValidationResult(
            conforms=bool(conforms),
            report_text=str(report_text),
            result_count=result_count,
            scope=scope,
        )

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
            ):
                relationship_iris.update(
                    self._subjects(data_graphs, predicate, column_iri)
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
        return RelationshipDescription(
            iri=relationship_iri,
            label=self._display_label_from_graphs(lookup_graphs, relationship_iri),
            description=self._description_from_graphs(lookup_graphs, relationship_iri),
            types=types,
            relationship_kind=relationship_kind,
            relationship_kind_label=self._label_for_resource(relationship_kind),
            source_dataset=self._optional_resource_summary(
                lookup_graphs,
                source_dataset,
            ),
            target_dataset=self._optional_resource_summary(
                lookup_graphs,
                target_dataset,
            ),
            foreign_key_from=self._optional_resource_summary(
                lookup_graphs,
                foreign_key_from,
            ),
            foreign_key_to=self._optional_resource_summary(
                lookup_graphs,
                foreign_key_to,
            ),
            referential_integrity=self._optional_resource_summary(
                lookup_graphs,
                referential_integrity,
            ),
            declared=self._bool_object(data_graphs, relationship_iri, "rc:declared"),
            identifying_columns=self._resource_summaries(
                lookup_graphs,
                self._objects(data_graphs, relationship_iri, "rc:identifyingColumn"),
            ),
            source_columns=self._resource_summaries(
                lookup_graphs,
                self._objects(data_graphs, relationship_iri, "rc:sourceColumn"),
            ),
            derived_columns=self._resource_summaries(
                lookup_graphs,
                self._objects(data_graphs, relationship_iri, "rc:derivedColumn"),
            ),
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
        )

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
    tokens = re.findall(r"[A-Za-z0-9]+", query)
    if not tokens:
        raise DoxaBaseError("Search query must contain at least one searchable token")
    return " AND ".join(f"{token.lower()}*" for token in tokens)


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
