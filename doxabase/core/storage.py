"""Capsule lifecycle, SQLite schema, named-graph and quad storage.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via StorageMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class StorageMixin:
    def __init__(
        self,
        path: str | Path = ".doxabase.sqlite",
        *,
        initialize: bool = True,
        seed: bool = True,
        read_only: bool = False,
    ) -> None:
        self.path = Path(path)
        self.read_only = read_only
        if read_only:
            if initialize:
                raise DoxaBaseError(
                    "Read-only DoxaBase connections cannot initialize or seed a "
                    "capsule; use DoxaBase.open_readonly(path) for existing "
                    "capsules."
                )
            uri = f"{self.path.resolve().as_uri()}?mode=ro"
            self._conn = sqlite3.connect(uri, uri=True)
        else:
            self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._search_index_error: str | None = None
        self._staged_apply_check_cache: (
            dict[StagedApplyCheckCacheKey, StagedRevisionApplyCheck] | None
        ) = None
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
    @classmethod
    def open_readonly(cls, path: str | Path) -> "DoxaBase":
        """Open an existing capsule through a SQLite read-only connection."""

        return cls(path, initialize=False, seed=False, read_only=True)
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
                self._ensure_mutable(name, allow_immutable=True)
                self._ensure_graph(name)
                self._insert_graph(name, self._seed_graph_for_path(source_path))
    def _seed_graph_for_path(self, source_path: Path) -> Graph:
        source_path = Path(source_path)
        stat = source_path.stat()
        cache_key = (
            str(source_path.resolve()),
            "turtle",
            stat.st_mtime_ns,
            stat.st_size,
        )
        cached = _SEED_GRAPH_CACHE.get(cache_key)
        if cached is None:
            cached = self._parse_rdf_payload(
                source_path,
                format="turtle",
                payload_name="source",
                parser_context="import_turtle",
            )
            _SEED_GRAPH_CACHE[cache_key] = cached
        return cached
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
            "analysis_views": self._count_type("rc:AnalysisView"),
            "analysis_packets": self._count_type("rc:AnalysisPacket"),
            "analysis_artifacts": self._count_type("rc:AnalysisArtifact"),
            "analysis_followup_tasks": self._count_type(
                "rc:AnalysisFollowupTask"
            ),
            "executable_query_snippets": self._count_type(
                "rc:ExecutableQuerySnippet"
            ),
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
    def _current_alternative_to_iri(
        self,
        alternative_to: str | None,
        *,
        graphs: list[str] | None = None,
    ) -> str | None:
        if alternative_to is None:
            return None
        successor = self._current_restage_successor_iri(
            alternative_to,
            graphs=graphs,
        )
        return successor or alternative_to
    def _is_blank_node_subject(self, graphs: list[str], subject: str) -> bool:
        graph_filter, graph_params = self._graph_filter(graphs, alias="q")
        row = self._conn.execute(
            f"""
            SELECT 1
            FROM quads q
            WHERE q.subject = ?
              AND q.subject_kind = 'bnode'
              {graph_filter}
            LIMIT 1
            """,
            [subject, *graph_params],
        ).fetchone()
        return row is not None
    def _recursive_blank_node_uri_owners(
        self,
        graphs: list[str],
        *,
        blank_nodes: Iterable[str],
        max_depth: int = 4,
    ) -> tuple[set[str], bool]:
        frontier = list(dict.fromkeys(blank_nodes))
        visited: set[str] = set()
        owners: set[str] = set()
        for _depth in range(max_depth):
            if not frontier:
                break
            next_frontier: list[str] = []
            for current_blank_node in frontier:
                if current_blank_node in visited:
                    continue
                visited.add(current_blank_node)
                uri_owners, blank_node_owners = self._blank_node_subject_owners(
                    graphs,
                    blank_node=current_blank_node,
                )
                owners.update(uri_owners)
                for owner in blank_node_owners:
                    if owner not in visited and owner not in next_frontier:
                        next_frontier.append(owner)
            frontier = next_frontier
        depth_exhausted = bool(frontier)
        return owners, depth_exhausted
    def _blank_node_subject_owners(
        self,
        graphs: list[str],
        *,
        blank_node: str,
    ) -> tuple[list[str], list[str]]:
        graph_filter, graph_params = self._graph_filter(graphs, alias="q")
        rows = self._conn.execute(
            f"""
            SELECT DISTINCT q.subject, q.subject_kind
            FROM quads q
            WHERE q.object = ?
              AND q.object_kind = 'bnode'
              {graph_filter}
            ORDER BY q.subject
            """,
            [blank_node, *graph_params],
        ).fetchall()
        uri_owners = [
            row["subject"] for row in rows if row["subject_kind"] == "uri"
        ]
        blank_node_owners = [
            row["subject"] for row in rows if row["subject_kind"] == "bnode"
        ]
        return uri_owners, blank_node_owners
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
    @staticmethod
    def _string_field(value: Any) -> str | None:
        return value if isinstance(value, str) else None
    @staticmethod
    def _int_values(values: Any) -> list[int]:
        if not isinstance(values, list):
            return []
        return [
            value
            for value in values
            if isinstance(value, int) and not isinstance(value, bool)
        ]
    @staticmethod
    def _optional_string_field(
        values: MappingABC[str, Any],
        field_name: str,
    ) -> str | None:
        value = values.get(field_name)
        return value if isinstance(value, str) else None
    def _insert_evidence_source_span(
        self,
        *,
        evidence_iri: str,
        source_path: str,
        source_section: str | None = None,
        start_line: int | None = None,
        end_line: int | None = None,
        source_kind: str | None = None,
        source_span_iri: str | None = None,
    ) -> tuple[str, int]:
        self._preflight_source_span_reuse(
            source_span_iri=source_span_iri,
            source_path=source_path,
            source_section=source_section,
            start_line=start_line,
            end_line=end_line,
            source_kind=source_kind,
        )
        source_span_subject = URIRef(
            source_span_iri or self._mint_iri("source-span")
        )
        evidence_subject = URIRef(evidence_iri)
        evidence_graph = Graph()
        self._bind_prefixes(evidence_graph)
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
                Literal(source_path),
            )
        )
        if source_section:
            evidence_graph.add(
                (
                    source_span_subject,
                    URIRef(self.expand_iri("rc:sourceSection")),
                    Literal(source_section),
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
        if source_kind is not None:
            evidence_graph.add(
                (
                    source_span_subject,
                    URIRef(self.expand_iri("rc:sourceKind")),
                    URIRef(self.expand_iri(source_kind)),
                )
            )
        return str(source_span_subject), self._insert_graph("evidence", evidence_graph)
    @staticmethod
    def _json_object_literal(value: str | None) -> dict[str, Any]:
        if value is None:
            return {}
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    def _patch_triple_presence_status(
        self,
        *,
        patch_triples_checked: int,
        patch_triples_present: int,
    ) -> str:
        if patch_triples_checked == 0:
            return "empty_patch"
        if patch_triples_present == 0:
            return "all_patch_triples_absent"
        if patch_triples_present == patch_triples_checked:
            return "all_patch_triples_present"
        return "mixed_patch_triples_present"
    @staticmethod
    def _alternative_set_membership_by_iri(
        rows: Iterable[tuple[str, str | None, str | None]],
    ) -> dict[str, tuple[list[str], str, str]]:
        row_list = list(rows)
        row_order = {iri: index for index, (iri, _, _) in enumerate(row_list)}
        row_iris = set(row_order)
        alternatives_by_source: dict[str, list[str]] = {}
        for iri, alternative_to, current_alternative_to in row_list:
            source_iri = current_alternative_to or alternative_to
            if (
                source_iri is None
                or source_iri == iri
                or source_iri not in row_iris
            ):
                continue
            alternatives_by_source.setdefault(source_iri, []).append(iri)

        memberships: dict[str, tuple[list[str], str, str]] = {}
        for source_iri, alternative_iris in alternatives_by_source.items():
            member_iris = sorted(
                {source_iri, *alternative_iris},
                key=lambda iri: row_order[iri],
            )
            for member_iri in member_iris:
                role = "source" if member_iri == source_iri else "alternative"
                existing = memberships.get(member_iri)
                if existing is None:
                    memberships[member_iri] = (member_iris, source_iri, role)
                    continue
                existing_iris, existing_source, existing_role = existing
                merged_iris = sorted(
                    {*existing_iris, *member_iris},
                    key=lambda iri: row_order[iri],
                )
                merged_source = min(
                    [existing_source, source_iri],
                    key=lambda iri: row_order[iri],
                )
                merged_role = (
                    existing_role
                    if existing_role == role
                    else "source_and_alternative"
                )
                memberships[member_iri] = (
                    merged_iris,
                    merged_source,
                    merged_role,
                )
        return memberships
    def _node_from_object_filter(
        self,
        object_filter: tuple[str, str, str | None, str | None],
    ) -> Node:
        value, value_kind, datatype, lang = object_filter
        if value_kind == "uri":
            return URIRef(value)
        if value_kind == "bnode":
            return BNode(value)
        if value_kind == "literal":
            return Literal(
                value,
                datatype=URIRef(datatype) if datatype is not None else None,
                lang=lang,
            )
        raise DoxaBaseError(f"Unsupported assertion object kind '{value_kind}'")
    def _patch_content_from_triples(
        self,
        triples: Iterable[tuple[Identifier, URIRef, Node]],
    ) -> str:
        graph = Graph()
        self._bind_prefixes(graph)
        for subject, predicate, object_node in triples:
            graph.add((subject, predicate, object_node))
        return graph.serialize(format="turtle").strip()
    def _merge_iri_values(
        self,
        user_values: Iterable[str] | str | None,
        discovered_values: Iterable[str],
    ) -> list[str]:
        values = [
            self.expand_iri(value)
            for value in self._string_values("user_values", user_values)
        ]
        values.extend(self.expand_iri(value) for value in discovered_values)
        return list(dict.fromkeys(values))
    def _ensure_graph_patch_role(self, patch_role_iri: str) -> None:
        graph_patch_role_iri = self.expand_iri("rc:GraphPatchRole")
        ontology_graphs = self._expand_graphs(["ontology"])
        if graph_patch_role_iri in self._types_from_graphs(
            ontology_graphs,
            patch_role_iri,
        ):
            return
        missing_seed_terms = self._missing_base_ontology_terms(
            REQUIRED_STAGING_ONTOLOGY_TERMS,
        )
        if missing_seed_terms:
            raise DoxaBaseError(
                "patch_role must be an rc:GraphPatchRole declared in base or "
                "project ontology. "
                + self._stale_seed_recovery_message(missing_seed_terms)
            )
        raise DoxaBaseError(
            "patch_role must be an rc:GraphPatchRole declared in base or "
            "project ontology. Use rc:FramingPatch, rc:SharedContextPatch, or "
            "a project term typed as rc:GraphPatchRole."
        )
    def _missing_base_ontology_terms(
        self,
        terms: Iterable[str],
    ) -> list[str]:
        base_graphs = self._expand_graphs(["base_ontology"])
        return [
            term
            for term in terms
            if not self._subject_exists(self.expand_iri(term), base_graphs)
        ]
    def _object_filter_from_node(
        self,
        node: Node,
    ) -> tuple[str, str, str | None, str | None]:
        if isinstance(node, URIRef):
            return str(node), "iri", None, None
        if isinstance(node, Literal):
            return (
                str(node),
                "literal",
                str(node.datatype) if node.datatype is not None else None,
                node.language,
            )
        return str(node), "literal", None, None
    @staticmethod
    def _markdown_graph_role_list(values: list[str]) -> str:
        return ", ".join(values) if values else "(none)"
    def _markdown_iri_list(self, iris: list[str]) -> str:
        if not iris:
            return "(none)"
        return ", ".join(f"`{iri}`" for iri in iris)
    @staticmethod
    def _source_span_line_label(source_span: SourceSpanDescription) -> str | None:
        if source_span.start_line is not None and source_span.end_line is not None:
            if source_span.start_line == source_span.end_line:
                return f"line {source_span.start_line}"
            return f"lines {source_span.start_line}-{source_span.end_line}"
        if source_span.start_line is not None:
            return f"starts at line {source_span.start_line}"
        if source_span.end_line is not None:
            return f"ends at line {source_span.end_line}"
        return None
    def replace_graph_triples(
        self,
        graph: str,
        *,
        removals: str | Path | Graph | None = None,
        additions: str | Path | Graph | None = None,
        format: str = "turtle",
        expected_count: int | None = None,
        allow_count_change: bool = False,
        allow_immutable: bool = False,
    ) -> GraphTripleReplacementRecord:
        self._ensure_mutable(graph, allow_immutable=allow_immutable)
        self._ensure_graph(graph)
        if expected_count is not None and expected_count < 0:
            raise DoxaBaseError("expected_count must be non-negative")

        removal_graph = self._parse_rdf_payload(
            removals,
            format=format,
            payload_name="removals",
        )
        addition_graph = self._parse_rdf_payload(
            additions,
            format=format,
            payload_name="additions",
        )
        if len(removal_graph) == 0 and len(addition_graph) == 0:
            raise DoxaBaseError(
                "replace_graph_triples requires at least one removal or addition triple"
            )

        before_rows = set(self._graph_storage_rows(graph))
        before_count = len(before_rows)
        before_digest = self._graph_content_digest(graph)
        if expected_count is not None and before_count != expected_count:
            raise DoxaBaseError(
                "replace_graph_triples expected "
                f"{expected_count} triples before replacement, found {before_count}"
            )

        removal_rows = set(self._rdf_graph_storage_rows(removal_graph))
        addition_rows = set(self._rdf_graph_storage_rows(addition_graph))
        rows_to_remove = before_rows.intersection(removal_rows)
        rows_after_removal = before_rows.difference(rows_to_remove)
        rows_to_add = addition_rows.difference(rows_after_removal)
        predicted_after_rows = rows_after_removal.union(addition_rows)
        predicted_after_count = len(predicted_after_rows)
        count_delta = predicted_after_count - before_count
        if not allow_count_change and count_delta != 0:
            raise DoxaBaseError(
                "replace_graph_triples would change graph "
                f"'{graph}' count from {before_count} to {predicted_after_count}; "
                "pass allow_count_change=True to permit this"
            )

        self._apply_graph_triple_replacement(
            graph,
            removals=rows_to_remove,
            additions=rows_to_add,
        )
        after_count = self.triple_count(graph)
        after_digest = self._graph_content_digest(graph)
        return GraphTripleReplacementRecord(
            graph=graph,
            format=format,
            before_count=before_count,
            after_count=after_count,
            count_delta=after_count - before_count,
            before_digest=before_digest,
            after_digest=after_digest,
            digest_changed=before_digest != after_digest,
            removal_triples=len(removal_rows),
            addition_triples=len(addition_rows),
            triples_removed=len(rows_to_remove),
            triples_added=len(rows_to_add),
            same_count=before_count == after_count,
            expected_count=expected_count,
            allow_count_change=allow_count_change,
        )
    def clear_graph(self, graph: str, *, allow_immutable: bool = False) -> None:
        self._ensure_mutable(graph, allow_immutable=allow_immutable)
        self._conn.execute("DELETE FROM quads WHERE graph = ?", (graph,))
        self._conn.commit()
        self._rebuild_search_index(raise_on_failure=False)
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
    def _compact_iri(self, iri: str) -> str | None:
        for prefix, namespace in sorted(
            PREFIXES.items(),
            key=lambda item: len(item[1]),
            reverse=True,
        ):
            if iri.startswith(namespace):
                local = iri[len(namespace) :]
                if local and re.match(r"^[A-Za-z_][A-Za-z0-9._-]*$", local):
                    return f"{prefix}:{local}"
        return None
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

            CREATE TABLE IF NOT EXISTS graph_snapshot_storage (
                revision_iri TEXT NOT NULL,
                graph_role TEXT NOT NULL,
                stored_at TEXT NOT NULL,
                triple_count INTEGER NOT NULL,
                content_digest TEXT NOT NULL,
                PRIMARY KEY (revision_iri, graph_role)
            );

            CREATE TABLE IF NOT EXISTS graph_snapshot_quads (
                revision_iri TEXT NOT NULL,
                graph_role TEXT NOT NULL,
                subject TEXT NOT NULL,
                subject_kind TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                object_kind TEXT NOT NULL,
                datatype TEXT,
                lang TEXT,
                created_at TEXT NOT NULL,
                UNIQUE (
                    revision_iri,
                    graph_role,
                    subject,
                    subject_kind,
                    predicate,
                    object,
                    object_kind,
                    datatype,
                    lang
                )
            );

            CREATE INDEX IF NOT EXISTS graph_snapshot_quads_revision_graph
                ON graph_snapshot_quads(revision_iri, graph_role);

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
        rows_to_insert = []
        seen: set[tuple[str, str, str, str, str, str, str | None, str | None]] = set()
        for row in rows:
            key = row[:8]
            if key in seen:
                continue
            seen.add(key)
            exists = self._conn.execute(
                """
                SELECT 1
                FROM quads
                WHERE graph = ?
                  AND subject = ?
                  AND subject_kind = ?
                  AND predicate = ?
                  AND object = ?
                  AND object_kind = ?
                  AND datatype IS ?
                  AND lang IS ?
                LIMIT 1
                """,
                key,
            ).fetchone()
            if exists is None:
                rows_to_insert.append(row)
        self._conn.executemany(
            """
            INSERT INTO quads
                (graph, subject, subject_kind, predicate, object, object_kind, datatype, lang, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows_to_insert,
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
    def _parse_rdf_payload(
        self,
        source: str | Path | Graph | None,
        *,
        format: str,
        payload_name: str,
        parser_context: str = "replace_graph_triples",
    ) -> Graph:
        if source is None:
            return Graph()
        if isinstance(source, Graph):
            return self._clone_graph(source)
        if isinstance(source, str) and not source.strip():
            return Graph()
        rdf_graph = Graph()
        self._bind_prefixes(rdf_graph)
        path = _existing_path(source)
        try:
            if path is not None:
                rdf_graph.parse(path, format=format)
            else:
                rdf_graph.parse(data=str(source), format=format)
        except Exception as exc:
            detail = self._rdf_parse_error_detail(exc)
            raise DoxaBaseError(
                f"Could not parse {parser_context} {payload_name} as "
                f"{format}: {detail}"
            ) from exc
        return rdf_graph
    def _rdf_graph_storage_rows(self, rdf_graph: Graph) -> list[GraphStorageRow]:
        rows: list[GraphStorageRow] = []
        for subject, predicate, obj in rdf_graph:
            subject_value, subject_kind = self._term_to_storage(subject)
            object_value, object_kind, datatype, lang = self._object_to_storage(obj)
            rows.append(
                (
                    subject_value,
                    subject_kind,
                    str(predicate),
                    object_value,
                    object_kind,
                    datatype,
                    lang,
                )
            )
        return rows
    def _apply_graph_triple_replacement(
        self,
        graph: str,
        *,
        removals: set[GraphStorageRow],
        additions: set[GraphStorageRow],
    ) -> None:
        try:
            with self._conn:
                if removals:
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
                        [(graph, *row) for row in sorted(removals)],
                    )
                if additions:
                    created_at = _now()
                    self._conn.executemany(
                        """
                        INSERT INTO quads
                            (graph, subject, subject_kind, predicate, object, object_kind, datatype, lang, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        [(graph, *row, created_at) for row in sorted(additions)],
                    )
        except sqlite3.Error as exc:
            raise DoxaBaseError(
                f"Could not replace triples in graph '{graph}'"
            ) from exc
        self._rebuild_search_index(raise_on_failure=False)
    def _clone_graph(self, source: Graph) -> Graph:
        graph = Graph()
        self._bind_prefixes(graph)
        for triple in source:
            graph.add(triple)
        return graph
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
    def _known_graph_names(self) -> set[str]:
        return {row["name"] for row in self._conn.execute("SELECT name FROM named_graphs")}
    def _graph_counts(self, graphs: Iterable[str]) -> dict[str, int]:
        return {graph: self.triple_count(graph) for graph in graphs}
    def _graph_content_digest(self, graph: str) -> str:
        digest = hashlib.sha256()
        for row in self._graph_storage_rows(graph):
            for value in row:
                digest.update((value or "").encode("utf-8"))
                digest.update(b"\x1f")
            digest.update(b"\n")
        return f"sha256:{digest.hexdigest()}"
    def _graph_storage_rows(self, graph: str) -> list[GraphStorageRow]:
        rows = self._conn.execute(
            """
            SELECT
                subject,
                subject_kind,
                predicate,
                object,
                object_kind,
                datatype,
                lang
            FROM quads
            WHERE graph = ?
            ORDER BY
                subject,
                subject_kind,
                predicate,
                object,
                object_kind,
                COALESCE(datatype, ''),
                COALESCE(lang, '')
            """,
            (graph,),
        ).fetchall()
        return [
            (
                row["subject"],
                row["subject_kind"],
                row["predicate"],
                row["object"],
                row["object_kind"],
                row["datatype"],
                row["lang"],
            )
            for row in rows
        ]
    def _sort_graph_storage_rows(
        self,
        rows: Iterable[GraphStorageRow],
    ) -> list[GraphStorageRow]:
        return sorted(
            rows,
            key=lambda row: tuple(value or "" for value in row),
        )
    def _graph_triple_description(
        self,
        row: GraphStorageRow,
    ) -> GraphTripleDescription:
        subject, subject_kind, predicate, object_value, object_kind, datatype, lang = row
        subject_curie = self._compact_iri(subject) if subject_kind == "uri" else None
        predicate_curie = self._compact_iri(predicate)
        object_curie = (
            self._compact_iri(object_value) if object_kind == "uri" else None
        )
        return GraphTripleDescription(
            subject=subject,
            subject_kind=subject_kind,
            subject_curie=subject_curie,
            subject_display=self._graph_term_display(
                subject,
                subject_kind,
                curie=subject_curie,
            ),
            predicate=predicate,
            predicate_curie=predicate_curie,
            predicate_display=self._graph_term_display(
                predicate,
                "uri",
                curie=predicate_curie,
            ),
            object=object_value,
            object_kind=object_kind,
            object_curie=object_curie,
            object_display=self._graph_term_display(
                object_value,
                object_kind,
                curie=object_curie,
            ),
            datatype=datatype,
            lang=lang,
        )
    def _graph_term_display(
        self,
        value: str,
        kind: str,
        *,
        curie: str | None,
    ) -> str:
        if kind == "literal":
            return value
        return curie or self._local_name(value) or value
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
    def _local_graph_name(
        self,
        identifier: str,
        graph_map: dict[str, str] | None,
    ) -> str:
        if graph_map and identifier in graph_map:
            return graph_map[identifier]
        if identifier.startswith(RCG_PREFIX):
            graph_name = identifier.removeprefix(RCG_PREFIX)
            if graph_name not in self._known_graph_names():
                raise DoxaBaseError(
                    "Unknown Rich Canopy graph role in TriG import: "
                    f"{identifier!r}. Pass graph_map to map this named graph "
                    "explicitly, or use a known graph role."
                )
            return graph_name
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
    def _lookup_graphs(self, data_graphs: list[str]) -> list[str]:
        return list(dict.fromkeys(data_graphs + self._expand_graphs(["ontology"])))
    def _label_from_graphs(self, graphs: list[str], subject: str) -> str | None:
        return self._first_object(graphs, subject, str(RDFS.label))
    def _description_from_graphs(self, graphs: list[str], subject: str) -> str | None:
        return self._first_object(graphs, subject, str(RDFS.comment))
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
    def _evidence_detail_graphs(self, graphs: list[str]) -> list[str]:
        return list(dict.fromkeys([*graphs, *self._expand_graphs(["evidence"])]))
    def _mint_iri(self, kind: str) -> str:
        return f"https://richcanopy.org/doxabase/generated/{kind}/{uuid4()}"
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
    def _required_iri(self, name: str, value: str) -> str:
        if not isinstance(value, str):
            raise DoxaBaseError(f"{name} must be a non-empty IRI or CURIE string")
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
