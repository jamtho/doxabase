from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Literal as TypingLiteral

from pyshacl import validate
from rdflib import BNode, Dataset, Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS
from rdflib.term import Identifier, Node

GraphName = TypingLiteral[
    "base_ontology",
    "base_shapes",
    "map",
    "ontology",
    "observations",
    "evidence",
    "shapes",
    "history",
]

ROOT = Path(__file__).resolve().parents[1]
BASE_ONTOLOGY_PATH = ROOT / "ontology" / "rc_core.ttl"
BASE_SHAPES_PATH = ROOT / "ontology" / "rc_shapes.ttl"

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
    ("evidence", "Evidence supporting observations and map assertions", True, False, None),
    ("shapes", "Project-owned SHACL shapes", True, False, None),
    ("history", "Versions, revisions, diffs, and rationale", True, False, None),
)


class DoxyBaseError(Exception):
    """Base exception for DoxyBase runtime errors."""


class ImmutableGraphError(DoxyBaseError):
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


@dataclass(frozen=True)
class DatasetDescription:
    iri: str
    graph: str | None
    label: str | None
    description: str | None
    types: list[str]
    columns: list[ColumnDescription]
    path_templates: list[str]
    physical_layouts: list[PhysicalLayoutDescription]
    partition_schemes: list[PartitionDescription]
    caveats: list[ResourceSummary]
    provenance: list[ResourceSummary]
    related_datasets: list[RelatedDatasetDescription]


@dataclass(frozen=True)
class ValidationResult:
    conforms: bool
    report_text: str
    result_count: int
    scope: str


class DoxyBase:
    """A small SQLite-backed RDF memory capsule.

    V1 stores RDF terms as strings in a simple quad table. RDFLib handles
    parsing/serialization and pySHACL handles explicit validation.
    """

    def __init__(
        self,
        path: str | Path = ".doxybase.sqlite",
        *,
        initialize: bool = True,
        seed: bool = True,
    ) -> None:
        self.path = Path(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        if initialize:
            self._ensure_schema()
            self._ensure_default_graphs()
            if seed:
                self.seed_base_graphs()

    @classmethod
    def create(
        cls,
        path: str | Path = ".doxybase.sqlite",
        *,
        overwrite: bool = False,
        seed: bool = True,
    ) -> "DoxyBase":
        db_path = Path(path)
        if overwrite and db_path.exists():
            db_path.unlink()
        return cls(db_path, initialize=True, seed=seed)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "DoxyBase":
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
                          AND ql.predicate = ?
                          AND lower(ql.object) LIKE ?
                    )
                )
            """
            needle = f"%{text.lower()}%"
            params.extend([needle, str(RDFS.label), needle])

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
                label=self._label(row["graph"], row["subject"]),
                types=self._types(row["graph"], row["subject"]),
                graph=row["graph"],
            )
            for row in rows
        ]
        return EntityList(entities=entities, limit=limit, offset=offset)

    def describe_dataset(self, iri: str, graph: str | None = "map") -> DatasetDescription:
        dataset_iri = self.expand_iri(iri)
        data_graphs = self._expand_graphs([graph] if graph else None)
        lookup_graphs = self._lookup_graphs(data_graphs)
        if not self._subject_exists(dataset_iri, data_graphs):
            graph_label = graph if graph is not None else "all graphs"
            raise DoxyBaseError(f"Dataset '{iri}' was not found in {graph_label}")

        columns = [
            self._describe_column(column_iri, data_graphs, lookup_graphs)
            for column_iri in self._objects(data_graphs, dataset_iri, "rc:hasColumn")
        ]
        columns.sort(key=lambda column: (column.column_name or "", column.iri))

        physical_layouts = [
            self._describe_physical_layout(layout_iri, data_graphs, lookup_graphs)
            for layout_iri in self._objects(data_graphs, dataset_iri, "rc:hasPhysicalLayout")
        ]
        partition_schemes = [
            self._describe_partition(partition_iri, data_graphs, lookup_graphs)
            for partition_iri in self._objects(data_graphs, dataset_iri, "rc:partitionedBy")
        ]
        direct_path_templates = self._objects(data_graphs, dataset_iri, "rc:pathTemplate")
        partition_path_templates = [
            partition.path_template
            for partition in partition_schemes
            if partition.path_template is not None
        ]
        path_templates = list(dict.fromkeys(direct_path_templates + partition_path_templates))

        return DatasetDescription(
            iri=dataset_iri,
            graph=graph,
            label=self._label_from_graphs(lookup_graphs, dataset_iri),
            description=self._description_from_graphs(lookup_graphs, dataset_iri),
            types=self._types_from_graphs(data_graphs, dataset_iri),
            columns=columns,
            path_templates=path_templates,
            physical_layouts=physical_layouts,
            partition_schemes=partition_schemes,
            caveats=[
                self._resource_summary(
                    lookup_graphs,
                    caveat_iri,
                    description_predicate="rc:caveatDescription",
                )
                for caveat_iri in self._objects(
                    data_graphs,
                    dataset_iri,
                    "rc:hasKnownCaveat",
                )
            ],
            provenance=[
                self._resource_summary(
                    lookup_graphs,
                    provenance_iri,
                    description_predicate="rc:sourceDescription",
                )
                for provenance_iri in self._objects(data_graphs, dataset_iri, "rc:hasProvenance")
            ],
            related_datasets=self._related_datasets(dataset_iri, data_graphs, lookup_graphs),
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

    def clear_graph(self, graph: str, *, allow_immutable: bool = False) -> None:
        self._ensure_mutable(graph, allow_immutable=allow_immutable)
        self._conn.execute("DELETE FROM quads WHERE graph = ?", (graph,))
        self._conn.commit()

    def validate_graph(
        self,
        scope: TypingLiteral["map", "ontology", "shapes", "all"] = "map",
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

    def to_graph(self, graphs: Iterable[str] | None = None) -> Graph:
        rdf_graph = Graph()
        for prefix, namespace in PREFIXES.items():
            rdf_graph.bind(prefix, namespace)
        graph_names = self._expand_graphs(list(graphs) if graphs is not None else None)
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
        self._conn.commit()

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
        return self.triple_count(graph) - before

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

    def _graphs_for_validation_scope(self, scope: str) -> list[str]:
        if scope == "map":
            return self._expand_graphs(["ontology"]) + ["map"]
        if scope == "ontology":
            return self._expand_graphs(["ontology"])
        if scope == "shapes":
            return self._expand_graphs(["shapes"])
        if scope == "all":
            return ["base_ontology", "ontology", "map", "observations", "evidence", "history"]
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
        return PhysicalLayoutDescription(
            iri=layout_iri,
            label=self._label_from_graphs(lookup_graphs, layout_iri),
            description=self._description_from_graphs(lookup_graphs, layout_iri),
            file_format=(
                self._resource_summary(lookup_graphs, file_format)
                if file_format is not None
                else None
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
        )

    def _related_datasets(
        self,
        dataset_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
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

    def _related_dataset(
        self,
        iri: str,
        relationship: str,
        relationship_iri: str | None,
        lookup_graphs: list[str],
    ) -> RelatedDatasetDescription:
        summary = self._resource_summary(lookup_graphs, iri)
        return RelatedDatasetDescription(
            iri=summary.iri,
            label=summary.label,
            description=summary.description,
            relationship=relationship,
            relationship_iri=relationship_iri,
        )

    def _resource_summary(
        self,
        graphs: list[str],
        iri: str,
        *,
        description_predicate: str = "rdfs:comment",
    ) -> ResourceSummary:
        return ResourceSummary(
            iri=iri,
            label=self._label_from_graphs(graphs, iri),
            description=(
                self._first_object(graphs, iri, description_predicate)
                or self._description_from_graphs(graphs, iri)
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

    def _bool_object(self, graphs: list[str], subject: str, predicate: str) -> bool | None:
        value = self._first_object(graphs, subject, predicate)
        if value is None:
            return None
        return value.lower() in {"1", "true"}

    def _label_from_graphs(self, graphs: list[str], subject: str) -> str | None:
        return self._first_object(graphs, subject, str(RDFS.label))

    def _description_from_graphs(self, graphs: list[str], subject: str) -> str | None:
        return self._first_object(graphs, subject, str(RDFS.comment))

    def _types_from_graphs(self, graphs: list[str], subject: str) -> list[str]:
        return self._objects(graphs, subject, str(RDF.type))

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
