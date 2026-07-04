"""Analysis packets and analysis views.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via AnalysisViewsMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class AnalysisViewsMixin:
    def _dataset_description_is_analysis_view(
        self,
        dataset: DatasetDescription,
    ) -> bool:
        return self.expand_iri("rc:AnalysisView") in dataset.types
    def describe_analysis_view(
        self,
        iri: str,
        graph: str | None = "map",
    ) -> AnalysisViewDescription:
        view_iri = self.expand_iri(iri)
        data_graphs = self._expand_graphs([graph] if graph else None)
        lookup_graphs = self._lookup_graphs(data_graphs)
        if not self._subject_exists(view_iri, data_graphs):
            graph_label = graph if graph is not None else "all graphs"
            raise DoxaBaseError(f"Analysis view '{iri}' was not found in {graph_label}")
        types = self._types_from_graphs(data_graphs, view_iri)
        if self.expand_iri("rc:AnalysisView") not in types:
            raise DoxaBaseError(f"Resource '{iri}' is not typed as rc:AnalysisView")

        source_iris = self._objects(data_graphs, view_iri, "rc:sourceDataset")
        caveat_iris = self._objects(data_graphs, view_iri, "rc:hasKnownCaveat")
        denominator_iri = self._first_object(
            data_graphs,
            view_iri,
            "rc:hasAnalysisDenominator",
        )
        suggested_next_actions = [
            SuggestedNextAction(
                tool="doxabase.describe_query_context",
                args={"iri": view_iri},
                reason="Inspect this analysis view as a logical query context. "
                    "DoxaBase will not treat the view itself as a physical "
                    "storage route.",
            )
        ]
        return AnalysisViewDescription(
            iri=view_iri,
            graph=graph,
            label=self._label_from_graphs(lookup_graphs, view_iri),
            description=self._description_from_graphs(lookup_graphs, view_iri),
            types=types,
            source_datasets=[
                self._resource_summary(lookup_graphs, source_iri)
                for source_iri in source_iris
            ],
            denominator=(
                self._describe_analysis_denominator(
                    denominator_iri,
                    data_graphs,
                    lookup_graphs,
                )
                if denominator_iri is not None
                else None
            ),
            query_snippets=[
                self._describe_query_snippet(
                    snippet_iri,
                    data_graphs,
                    lookup_graphs,
                )
                for snippet_iri in self._objects(data_graphs, view_iri, "rc:hasQuerySnippet")
            ],
            caveats=[
                self._describe_caveat(caveat_iri, data_graphs, lookup_graphs)
                for caveat_iri in caveat_iris
            ],
            source_caveats=[
                self._describe_caveat(caveat_iri, data_graphs, lookup_graphs)
                for caveat_iri in self._analysis_view_source_caveat_iris(
                    source_iris,
                    direct_caveat_iris=caveat_iris,
                    data_graphs=data_graphs,
                )
            ],
            row_count_snapshot=self._int_object(
                data_graphs,
                view_iri,
                "rc:rowCountSnapshot",
            ),
            suggested_next_actions=suggested_next_actions,
        )
    def _analysis_view_source_caveat_iris(
        self,
        source_iris: Iterable[str],
        *,
        direct_caveat_iris: Iterable[str],
        data_graphs: list[str],
    ) -> list[str]:
        direct_caveat_set = set(direct_caveat_iris)
        source_caveat_iris: dict[str, None] = {}
        for source_iri in source_iris:
            for caveat_iri in self._objects(
                data_graphs,
                source_iri,
                "rc:hasKnownCaveat",
            ):
                if caveat_iri not in direct_caveat_set:
                    source_caveat_iris.setdefault(caveat_iri, None)
        return sorted(source_caveat_iris)
    def _analysis_view_query_context(
        self,
        dataset: DatasetDescription,
        dataset_summary: ResourceSummary,
    ) -> QueryPlanningContext:
        view = self.describe_analysis_view(dataset.iri, graph=dataset.graph)
        issue = QueryPlanningIssue(
            code="logical_analysis_view_not_physical_route",
            severity="info",
            message=(
                "This resource is an rc:AnalysisView: a named logical analysis "
                "population or query recipe, not a physical storage route."
            ),
            resource=dataset_summary,
            details={
                "dataset_iri": dataset.iri,
                "query_readiness": "logical_analysis_view",
                "source_dataset_iris": [
                    source.iri for source in view.source_datasets
                ],
                "denominator_iri": (
                    view.denominator.iri if view.denominator is not None else None
                ),
                "query_snippet_count": len(view.query_snippets),
                "suggested_profile": "deep_lore",
            },
        )
        describe_view_action = SuggestedNextAction(
                                   tool="doxabase.describe_analysis_view",
                                   args={"iri": dataset.iri},
                                   reason="Read the logical view denominator, source datasets, caveats, "
                "and query snippet metadata before deciding whether to query "
                "the source datasets or materialize a new physical route.",
                               )
        suggested_next_actions = [
            describe_view_action,
            self._project_brief_get_context_graph_action(dataset.iri),
        ]
        return QueryPlanningContext(
            dataset=dataset_summary,
            readiness="logical_analysis_view",
            readiness_note=(
                "This resource is a logical analysis view. Use its source "
                "datasets, denominator, caveats, and query snippets as reviewed "
                "analysis context; do not repair it as missing physical storage "
                "unless a materialized route is intentionally modeled."
            ),
            issues=[issue],
            analysis_warnings=[],
            suggested_repair_action_groups=[],
            suggested_repair_action_group_count=0,
            planning_notes=[
                (
                    "Analysis views preserve denominator and query-recipe context "
                    "for interpretation; DoxaBase does not execute them."
                ),
                (
                    "Use describe_analysis_view for the logical definition, then "
                    "inspect source datasets with describe_query_context when an "
                    "executable handoff is needed."
                ),
            ],
            row_count_snapshot=dataset.row_count_snapshot,
            profile_summary=dataset.profile_summary,
            layout_verification_status=dataset.layout_verification_status,
            layout_verification_note=dataset.layout_verification_note,
            columns=dataset.columns,
            path_templates=dataset.path_templates,
            query_target_decision=QueryTargetDecision(
                status="logical_analysis_view",
                summary=(
                    "Analysis view is logical context, not a physical query "
                    "target candidate."
                ),
                candidate_index=None,
                candidate_path=None,
                candidate_path_status=None,
                direct_review_required=None,
                selected_candidate_direct_clean=None,
                reason_codes=[issue.code],
                selection_reason_codes=["logical_analysis_view"],
            ),
            query_target_candidates=[],
            ready_candidate_indexes=[],
            unselected_ready_candidate_indexes=[],
            direct_clean_candidate_indexes=[],
            unselected_direct_clean_candidate_indexes=[],
            physical_layouts=dataset.physical_layouts,
            storage_accesses=dataset.storage_accesses,
            partition_schemes=dataset.partition_schemes,
            caveats=dataset.caveats,
            upstream_caveats=dataset.upstream_caveats,
            suggested_next_actions=suggested_next_actions,
            safe_inspection_action_indexes=[0, 1],
            first_safe_inspection_action_index=0,
        )
    def record_map_analysis_view(
        self,
        iri: str,
        *,
        label: str | None = None,
        description: str | None = None,
        source_datasets: Iterable[str] | str | None = None,
        row_count_snapshot: int | None = None,
        caveats: Iterable[str] | str | None = None,
        denominator_iri: str | None = None,
        denominator_label: str | None = None,
        denominator_description: str | None = None,
        denominator_row_count_snapshot: int | None = None,
        denominator_basis: str | None = None,
        query_snippet_iri: str | None = None,
        query_snippet_label: str | None = None,
        query_snippet_description: str | None = None,
        query_text: str | None = None,
        query_language: str | None = None,
        query_engine: str | None = None,
        query_snippets: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    ) -> MapResourceRecord:
        view_iri = self._required_iri("iri", iri)
        self._ensure_non_negative("row_count_snapshot", row_count_snapshot)
        self._ensure_non_negative(
            "denominator_row_count_snapshot",
            denominator_row_count_snapshot,
        )
        legacy_query_fields_supplied = any(
            value is not None
            for value in (
                query_snippet_iri,
                query_snippet_label,
                query_snippet_description,
                query_text,
                query_language,
                query_engine,
            )
        )
        if query_snippets is not None and legacy_query_fields_supplied:
            raise DoxaBaseError(
                "query_snippets cannot be combined with legacy single-snippet "
                "query_snippet_* or query_text/query_language/query_engine fields"
            )
        if query_snippets is not None:
            query_snippet_specs = self._normalise_analysis_view_query_snippets(
                view_iri,
                query_snippets,
            )
        elif legacy_query_fields_supplied:
            query_snippet_specs = self._normalise_analysis_view_query_snippets(
                view_iri,
                {
                    "iri": query_snippet_iri,
                    "label": query_snippet_label,
                    "description": query_snippet_description,
                    "query_text": query_text,
                    "query_language": query_language,
                    "query_engine": query_engine,
                },
            )
        else:
            query_snippet_specs = []
        query_snippets_supplied = query_snippets is not None
        source_dataset_values = self._string_values(
            "source_datasets",
            source_datasets,
        )
        caveat_values = self._string_values("caveats", caveats)
        source_dataset_refs = [
            self._resource_ref("source_datasets", dataset)
            for dataset in source_dataset_values
        ]
        caveat_refs = [self._resource_ref("caveats", caveat) for caveat in caveat_values]

        view_graph = Graph()
        self._bind_prefixes(view_graph)
        subject = URIRef(view_iri)
        for type_iri in (
            "rc:Dataset",
            "rc:Table",
            "rc:AnalysisView",
        ):
            view_graph.add((subject, RDF.type, URIRef(self.expand_iri(type_iri))))
        self._add_optional_literal(view_graph, subject, str(RDFS.label), label)
        self._add_optional_literal(view_graph, subject, str(RDFS.comment), description)
        if row_count_snapshot is not None:
            view_graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:rowCountSnapshot")),
                    Literal(row_count_snapshot, datatype=XSD.integer),
                )
            )
        for dataset_ref in source_dataset_refs:
            view_graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:sourceDataset")),
                    dataset_ref,
                )
            )
        for caveat_ref in caveat_refs:
            view_graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasKnownCaveat")),
                    caveat_ref,
                )
            )

        denominator_fields_supplied = any(
            value is not None
            for value in (
                denominator_iri,
                denominator_label,
                denominator_description,
                denominator_row_count_snapshot,
                denominator_basis,
            )
        )
        denominator_value = (
            str(self._resource_ref("denominator_iri", denominator_iri))
            if denominator_iri is not None
            else f"{view_iri}/denominator"
        )
        denominator_graph = Graph()
        self._bind_prefixes(denominator_graph)
        if denominator_fields_supplied:
            denominator_ref = URIRef(denominator_value)
            view_graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasAnalysisDenominator")),
                    denominator_ref,
                )
            )
            denominator_graph.add(
                (
                    denominator_ref,
                    RDF.type,
                    URIRef(self.expand_iri("rc:AnalysisDenominator")),
                )
            )
            self._add_optional_literal(
                denominator_graph,
                denominator_ref,
                str(RDFS.label),
                denominator_label,
            )
            self._add_optional_literal(
                denominator_graph,
                denominator_ref,
                "rc:denominatorDescription",
                denominator_description,
            )
            if denominator_row_count_snapshot is not None:
                denominator_graph.add(
                    (
                        denominator_ref,
                        URIRef(self.expand_iri("rc:denominatorRowCountSnapshot")),
                        Literal(
                            denominator_row_count_snapshot,
                            datatype=XSD.integer,
                        ),
                    )
                )
            self._add_optional_literal(
                denominator_graph,
                denominator_ref,
                "rc:denominatorBasis",
                denominator_basis,
            )

        snippet_graph = Graph()
        self._bind_prefixes(snippet_graph)
        for snippet_spec in query_snippet_specs:
            snippet_ref = URIRef(snippet_spec["iri"])
            view_graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasQuerySnippet")),
                    snippet_ref,
                )
            )
            snippet_graph.add(
                (
                    snippet_ref,
                    RDF.type,
                    URIRef(self.expand_iri("rc:ExecutableQuerySnippet")),
                )
            )
            snippet_graph.add(
                (
                    snippet_ref,
                    URIRef(self.expand_iri("rc:forAnalysisView")),
                    subject,
                )
            )
            self._add_optional_literal(
                snippet_graph,
                snippet_ref,
                str(RDFS.label),
                snippet_spec["label"],
            )
            self._add_optional_literal(
                snippet_graph,
                snippet_ref,
                str(RDFS.comment),
                snippet_spec["description"],
            )
            self._add_optional_literal(
                snippet_graph,
                snippet_ref,
                "rc:queryText",
                snippet_spec["query_text"],
            )
            self._add_optional_literal(
                snippet_graph,
                snippet_ref,
                "rc:queryLanguage",
                snippet_spec["query_language"],
            )
            self._add_optional_literal(
                snippet_graph,
                snippet_ref,
                "rc:queryRuntime",
                snippet_spec["query_engine"],
            )

        predicates: list[str] = [str(RDF.type)]
        if label is not None:
            predicates.append(str(RDFS.label))
        if description is not None:
            predicates.append(str(RDFS.comment))
        if row_count_snapshot is not None:
            predicates.append(self.expand_iri("rc:rowCountSnapshot"))
        if source_datasets is not None:
            predicates.append(self.expand_iri("rc:sourceDataset"))
        if caveats is not None:
            predicates.append(self.expand_iri("rc:hasKnownCaveat"))
        if denominator_fields_supplied:
            predicates.append(self.expand_iri("rc:hasAnalysisDenominator"))
        if query_snippets_supplied or query_snippet_specs:
            predicates.append(self.expand_iri("rc:hasQuerySnippet"))
        triples = self._replace_subject_triples(
            "map",
            view_iri,
            predicates,
            view_graph,
        )

        if denominator_fields_supplied:
            triples += self._replace_subject_triples(
                "map",
                denominator_value,
                [
                    str(RDF.type),
                    str(RDFS.label),
                    self.expand_iri("rc:denominatorDescription"),
                    self.expand_iri("rc:denominatorRowCountSnapshot"),
                    self.expand_iri("rc:denominatorBasis"),
                ],
                denominator_graph,
            )
        for snippet_spec in query_snippet_specs:
            triples += self._replace_subject_triples(
                "map",
                snippet_spec["iri"],
                [
                    str(RDF.type),
                    self.expand_iri("rc:forAnalysisView"),
                    str(RDFS.label),
                    str(RDFS.comment),
                    self.expand_iri("rc:queryText"),
                    self.expand_iri("rc:queryLanguage"),
                    self.expand_iri("rc:queryRuntime"),
                ],
                snippet_graph,
            )
        return MapResourceRecord(
            iri=view_iri,
            resource_type=self.expand_iri("rc:AnalysisView"),
            graph="map",
            triples=triples,
        )
    def record_map_analysis_view_bundle(
        self,
        views: Iterable[Mapping[str, Any]] | Mapping[str, Any],
    ) -> AnalysisViewBundleRecord:
        view_specs = self._normalise_analysis_view_bundle_specs(views)
        records: list[MapResourceRecord] = []
        analysis_views: list[AnalysisViewDescription] = []
        for view_spec in view_specs:
            record = self.record_map_analysis_view(**view_spec)
            records.append(record)
            analysis_views.append(self.describe_analysis_view(record.iri))

        suggested_next_actions = self._dedupe_suggested_next_actions(
            action
            for analysis_view in analysis_views
            for action in analysis_view.suggested_next_actions
        )
        return AnalysisViewBundleRecord(
            records=records,
            analysis_views=analysis_views,
            view_iris=[record.iri for record in records],
            view_count=len(records),
            query_snippet_count=sum(
                len(analysis_view.query_snippets) for analysis_view in analysis_views
            ),
            suggested_next_actions=suggested_next_actions,
        )
    def record_analysis_packet(
        self,
        iri: str,
        *,
        summary: str,
        label: str | None = None,
        evidence_sources: Iterable[str] | str | None = None,
        analysis_views: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None = None,
        analysis_view_iris: Iterable[str] | str | None = None,
        query_recipes: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None = None,
        artifacts: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None = None,
        followup_tasks: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None = None,
        pattern_summary: str | None = None,
        pattern_text: str | None = None,
        pattern_rationale: str | None = None,
        pattern_iri: str | None = None,
    ) -> AnalysisPacketRecord:
        if self.read_only:
            raise DoxaBaseError(
                "record_analysis_packet requires a writable capsule; "
                "open read-only capsules with DoxaBase.open_readonly(path) for "
                "inspection only"
            )
        spec = self._normalise_analysis_packet(
            iri=iri,
            summary=summary,
            label=label,
            evidence_sources=evidence_sources,
            analysis_views=analysis_views,
            analysis_view_iris=analysis_view_iris,
            query_recipes=query_recipes,
            artifacts=artifacts,
            followup_tasks=followup_tasks,
            pattern_summary=pattern_summary,
            pattern_text=pattern_text,
            pattern_rationale=pattern_rationale,
            pattern_iri=pattern_iri,
        )
        with self._preflight_clone() as clone:
            clone._apply_analysis_packet(spec)
        return self._apply_analysis_packet(spec)
    def _apply_analysis_packet(
        self,
        spec: Mapping[str, Any],
    ) -> AnalysisPacketRecord:
        analysis_view_bundle = (
            self.record_map_analysis_view_bundle(spec["analysis_views"])
            if spec["analysis_views"]
            else None
        )
        analysis_view_iris = list(spec["analysis_view_iris"])
        if analysis_view_bundle is not None:
            analysis_view_iris = list(
                dict.fromkeys([*analysis_view_iris, *analysis_view_bundle.view_iris])
            )

        artifact_records = self._record_analysis_packet_artifacts(
            packet_iri=spec["iri"],
            artifacts=spec["artifacts"],
        )
        query_recipe_records = self._record_analysis_packet_query_recipes(
            packet_iri=spec["iri"],
            query_recipes=spec["query_recipes"],
        )
        followup_task_records = self._record_analysis_packet_followup_tasks(
            packet_iri=spec["iri"],
            followup_tasks=spec["followup_tasks"],
        )
        packet_triples = self._record_analysis_packet_resource(
            packet_iri=spec["iri"],
            label=spec["label"],
            summary=spec["summary"],
            evidence_sources=spec["evidence_sources"],
            analysis_view_iris=analysis_view_iris,
            artifact_iris=[record.iri for record in artifact_records],
            query_recipe_iris=[record.iri for record in query_recipe_records],
            followup_task_iris=[record.iri for record in followup_task_records],
        )
        pattern = None
        if spec["pattern"] is not None:
            pattern_spec = spec["pattern"]
            pattern = self.record_pattern(
                pattern_spec["summary"],
                pattern_text=pattern_spec["pattern_text"],
                rationale=pattern_spec["rationale"],
                pattern_targets=list(
                    dict.fromkeys(
                        [
                            spec["iri"],
                            *analysis_view_iris,
                            *[record.iri for record in query_recipe_records],
                        ]
                    )
                ),
                evidence_iri=spec["iri"],
                map_implications=analysis_view_iris,
                pattern_iri=pattern_spec["iri"],
            )
        suggested_next_actions = self._dedupe_suggested_next_actions(
            [
                SuggestedNextAction(
                    tool="doxabase.get_context_graph",
                    args={
                        "seed_iris": [spec["iri"]],
                        "profile": "resource_brief",
                    },
                    reason="Inspect the packet, linked analysis views, artifacts, "
                        "query recipes, follow-up tasks, and supporting "
                        "evidence as a bounded resource handoff.",
                ),
                *(
                    analysis_view_bundle.suggested_next_actions
                    if analysis_view_bundle is not None
                    else []
                ),
            ]
        )
        return AnalysisPacketRecord(
            packet_iri=spec["iri"],
            evidence_iri=spec["iri"],
            graph="evidence",
            packet_triples=packet_triples,
            analysis_view_bundle=analysis_view_bundle,
            analysis_view_iris=analysis_view_iris,
            artifact_records=artifact_records,
            artifact_iris=[record.iri for record in artifact_records],
            query_recipe_records=query_recipe_records,
            query_recipe_iris=[record.iri for record in query_recipe_records],
            followup_task_records=followup_task_records,
            followup_task_iris=[record.iri for record in followup_task_records],
            pattern=pattern,
            pattern_iri=pattern.pattern_iri if pattern is not None else None,
            suggested_next_actions=suggested_next_actions,
        )
    def _normalise_analysis_view_query_snippets(
        self,
        view_iri: str,
        query_snippets: Iterable[Mapping[str, Any]] | Mapping[str, Any],
    ) -> list[dict[str, str | None]]:
        if isinstance(query_snippets, MappingABC):
            snippet_values = [query_snippets]
        else:
            snippet_values = list(query_snippets)
        allowed_fields = {
            "iri",
            "query_snippet_iri",
            "label",
            "query_snippet_label",
            "description",
            "query_snippet_description",
            "query_text",
            "query_language",
            "query_engine",
        }
        specs: list[dict[str, str | None]] = []
        seen_iris: set[str] = set()
        for index, item in enumerate(snippet_values, start=1):
            if not isinstance(item, MappingABC):
                raise DoxaBaseError(f"query_snippets[{index}] must be an object")
            unknown_fields = sorted(set(item) - allowed_fields)
            if unknown_fields:
                raise DoxaBaseError(
                    f"query_snippets[{index}] has unsupported field(s): "
                    + ", ".join(unknown_fields)
                )

            def optional_string(*fields: str) -> str | None:
                for field in fields:
                    value = item.get(field)
                    if value is None:
                        continue
                    if not isinstance(value, str):
                        raise DoxaBaseError(
                            f"query_snippets[{index}].{field} must be a string"
                        )
                    return value
                return None

            snippet_iri_value = optional_string("iri", "query_snippet_iri")
            snippet_iri = (
                str(
                    self._resource_ref(
                        f"query_snippets[{index}].iri",
                        snippet_iri_value,
                    )
                )
                if snippet_iri_value is not None
                else f"{view_iri}/query-snippet/{index}"
            )
            if snippet_iri in seen_iris:
                raise DoxaBaseError(
                    f"query_snippets[{index}].iri duplicates {snippet_iri}"
                )
            seen_iris.add(snippet_iri)
            query_text = optional_string("query_text")
            if query_text is not None and not query_text.strip():
                raise DoxaBaseError(
                    f"query_snippets[{index}].query_text must not be empty"
                )
            specs.append(
                {
                    "iri": snippet_iri,
                    "label": optional_string("label", "query_snippet_label"),
                    "description": optional_string(
                        "description",
                        "query_snippet_description",
                    ),
                    "query_text": query_text,
                    "query_language": optional_string("query_language"),
                    "query_engine": optional_string("query_engine"),
                }
            )
        return specs
    def _normalise_analysis_view_bundle_specs(
        self,
        views: Iterable[Mapping[str, Any]] | Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        if isinstance(views, MappingABC):
            view_values = [views]
        elif isinstance(views, str):
            raise DoxaBaseError("views must be an object or a list of objects")
        else:
            view_values = list(views)
        if not view_values:
            raise DoxaBaseError("views must contain at least one analysis view")
        allowed_fields = {
            "iri",
            "view_iri",
            "label",
            "description",
            "source_datasets",
            "row_count_snapshot",
            "caveats",
            "denominator_iri",
            "denominator_label",
            "denominator_description",
            "denominator_row_count_snapshot",
            "denominator_basis",
            "query_snippet_iri",
            "query_snippet_label",
            "query_snippet_description",
            "query_text",
            "query_language",
            "query_engine",
            "query_snippets",
        }
        specs: list[dict[str, Any]] = []
        seen_iris: set[str] = set()
        for index, item in enumerate(view_values, start=1):
            if not isinstance(item, MappingABC):
                raise DoxaBaseError(f"views[{index}] must be an object")
            unknown_fields = sorted(set(item) - allowed_fields)
            if unknown_fields:
                raise DoxaBaseError(
                    f"views[{index}] has unsupported field(s): "
                    + ", ".join(unknown_fields)
                )

            iri_value = item.get("iri", item.get("view_iri"))
            if not isinstance(iri_value, str) or not iri_value.strip():
                raise DoxaBaseError(
                    f"views[{index}].iri must be a non-empty IRI or CURIE string"
                )
            view_iri = str(self._resource_ref(f"views[{index}].iri", iri_value))
            if view_iri in seen_iris:
                raise DoxaBaseError(f"views[{index}].iri duplicates {view_iri}")
            seen_iris.add(view_iri)

            spec = {
                field: item[field]
                for field in allowed_fields
                if field in item and field != "view_iri"
            }
            spec["iri"] = view_iri
            specs.append(spec)
        return specs
    def _normalise_analysis_packet(
        self,
        *,
        iri: str,
        summary: str,
        label: str | None,
        evidence_sources: Iterable[str] | str | None,
        analysis_views: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
        analysis_view_iris: Iterable[str] | str | None,
        query_recipes: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
        artifacts: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
        followup_tasks: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
        pattern_summary: str | None,
        pattern_text: str | None,
        pattern_rationale: str | None,
        pattern_iri: str | None,
    ) -> dict[str, Any]:
        packet_iri = self._required_iri("iri", iri)
        if not isinstance(summary, str) or not summary.strip():
            raise DoxaBaseError("summary must be a non-empty string")
        self._preflight_optional_string("label", label)
        source_values = self._string_values("evidence_sources", evidence_sources)
        analysis_view_values = (
            self._normalise_manifest_object_list("analysis_views", analysis_views)
            if analysis_views is not None
            else []
        )
        view_specs = (
            self._normalise_analysis_view_bundle_specs(analysis_view_values)
            if analysis_view_values
            else []
        )
        existing_view_iris = [
            str(self._resource_ref("analysis_view_iris", view_iri))
            for view_iri in self._string_values("analysis_view_iris", analysis_view_iris)
        ]
        created_view_iris = {view_spec["iri"] for view_spec in view_specs}
        for view_iri in existing_view_iris:
            if view_iri in created_view_iris:
                continue
            if (
                not self._subject_exists(view_iri, ["map"])
                or self.expand_iri("rc:AnalysisView")
                not in self._types_from_graphs(["map"], view_iri)
            ):
                raise DoxaBaseError(
                    "analysis_view_iris must name existing rc:AnalysisView "
                    f"resources unless they are also supplied in analysis_views: {view_iri}"
                )
        query_recipe_specs = self._normalise_analysis_packet_query_recipes(
            packet_iri,
            query_recipes,
        )
        artifacts_specs = self._normalise_analysis_packet_artifacts(
            packet_iri,
            artifacts,
        )
        task_specs = self._normalise_analysis_packet_followup_tasks(
            packet_iri,
            followup_tasks,
        )
        artifact_sources = [artifact["source_path"] for artifact in artifacts_specs]
        source_values = list(dict.fromkeys([*source_values, *artifact_sources]))
        if not source_values:
            raise DoxaBaseError(
                "record_analysis_packet requires evidence_sources or at least "
                "one artifact source_path"
            )
        pattern_spec = None
        if self._profile_pattern_requested(
            pattern_summary,
            pattern_text,
            pattern_rationale,
        ):
            pattern_iri_value = (
                str(self._resource_ref("pattern_iri", pattern_iri))
                if pattern_iri is not None
                else None
            )
            pattern_spec = {
                "iri": pattern_iri_value,
                "summary": pattern_summary,
                "pattern_text": pattern_text,
                "rationale": pattern_rationale,
            }
        used_iris = {packet_iri}
        for collection_name, specs in (
            ("analysis_views", view_specs),
            ("query_recipes", query_recipe_specs),
            ("artifacts", artifacts_specs),
            ("followup_tasks", task_specs),
        ):
            for item in specs:
                item_iri = item["iri"]
                if item_iri in used_iris:
                    raise DoxaBaseError(
                        f"{collection_name} contains duplicate packet resource IRI: "
                        f"{item_iri}"
                    )
                used_iris.add(item_iri)
        return {
            "iri": packet_iri,
            "summary": summary.strip(),
            "label": label,
            "evidence_sources": source_values,
            "analysis_views": view_specs,
            "analysis_view_iris": existing_view_iris,
            "query_recipes": query_recipe_specs,
            "artifacts": artifacts_specs,
            "followup_tasks": task_specs,
            "pattern": pattern_spec,
        }
    def _normalise_analysis_packet_query_recipes(
        self,
        packet_iri: str,
        query_recipes: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
    ) -> list[dict[str, Any]]:
        recipe_values = self._normalise_manifest_object_list(
            "query_recipes",
            query_recipes,
        )
        allowed_fields = {
            "iri",
            "query_recipe_iri",
            "label",
            "query_recipe_label",
            "description",
            "query_recipe_description",
            "query_text",
            "query_language",
            "query_engine",
            "targets",
        }
        specs: list[dict[str, Any]] = []
        seen_iris: set[str] = set()
        for index, item in enumerate(recipe_values, start=1):
            unknown_fields = sorted(set(item) - allowed_fields)
            if unknown_fields:
                raise DoxaBaseError(
                    f"query_recipes[{index}] has unsupported field(s): "
                    + ", ".join(unknown_fields)
                )
            query_text = self._analysis_packet_required_string(
                item,
                index=index,
                item_name="query_recipes",
                fields=("query_text",),
            )
            iri_value = item.get("iri", item.get("query_recipe_iri"))
            recipe_iri = (
                str(self._resource_ref(f"query_recipes[{index}].iri", iri_value))
                if isinstance(iri_value, str) and iri_value.strip()
                else f"{packet_iri}/query-recipe/{index}"
            )
            if recipe_iri in seen_iris:
                raise DoxaBaseError(
                    f"query_recipes[{index}].iri duplicates {recipe_iri}"
                )
            seen_iris.add(recipe_iri)
            targets = [
                str(self._resource_ref(f"query_recipes[{index}].targets", value))
                for value in self._string_values("targets", item.get("targets"))
            ]
            specs.append(
                {
                    "iri": recipe_iri,
                    "label": self._analysis_packet_optional_string(
                        item,
                        index=index,
                        item_name="query_recipes",
                        field="label",
                        aliases=("query_recipe_label",),
                    ),
                    "description": self._analysis_packet_optional_string(
                        item,
                        index=index,
                        item_name="query_recipes",
                        field="description",
                        aliases=("query_recipe_description",),
                    ),
                    "query_text": query_text,
                    "query_language": self._analysis_packet_optional_string(
                        item,
                        index=index,
                        item_name="query_recipes",
                        field="query_language",
                    ),
                    "query_engine": self._analysis_packet_optional_string(
                        item,
                        index=index,
                        item_name="query_recipes",
                        field="query_engine",
                    ),
                    "targets": targets,
                }
            )
        return specs
    def _normalise_analysis_packet_artifacts(
        self,
        packet_iri: str,
        artifacts: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
    ) -> list[dict[str, Any]]:
        artifact_values = self._normalise_manifest_object_list(
            "artifacts",
            artifacts,
        )
        allowed_fields = {
            "iri",
            "artifact_iri",
            "label",
            "summary",
            "source_path",
            "path",
            "artifact_role",
            "role",
            "media_type",
            "content_hash",
            "byte_size",
            "image_width",
            "image_height",
            "supports",
        }
        specs: list[dict[str, Any]] = []
        seen_iris: set[str] = set()
        for index, item in enumerate(artifact_values, start=1):
            unknown_fields = sorted(set(item) - allowed_fields)
            if unknown_fields:
                raise DoxaBaseError(
                    f"artifacts[{index}] has unsupported field(s): "
                    + ", ".join(unknown_fields)
                )
            source_path = self._analysis_packet_required_string(
                item,
                index=index,
                item_name="artifacts",
                fields=("source_path", "path"),
            )
            iri_value = item.get("iri", item.get("artifact_iri"))
            artifact_iri = (
                str(self._resource_ref(f"artifacts[{index}].iri", iri_value))
                if isinstance(iri_value, str) and iri_value.strip()
                else f"{packet_iri}/artifact/{index}"
            )
            if artifact_iri in seen_iris:
                raise DoxaBaseError(
                    f"artifacts[{index}].iri duplicates {artifact_iri}"
                )
            seen_iris.add(artifact_iri)
            for field in ("byte_size", "image_width", "image_height"):
                value = item.get(field)
                if value is not None:
                    minimum = 1 if field in {"image_width", "image_height"} else 0
                    if not isinstance(value, int) or value < minimum:
                        raise DoxaBaseError(
                            f"artifacts[{index}].{field} must be "
                            f"{'positive' if minimum == 1 else 'non-negative'} "
                            "integer"
                        )
            supports = [
                str(self._resource_ref(f"artifacts[{index}].supports", value))
                for value in self._string_values("supports", item.get("supports"))
            ]
            specs.append(
                {
                    "iri": artifact_iri,
                    "label": self._analysis_packet_optional_string(
                        item,
                        index=index,
                        item_name="artifacts",
                        field="label",
                    ),
                    "summary": self._analysis_packet_optional_string(
                        item,
                        index=index,
                        item_name="artifacts",
                        field="summary",
                    ),
                    "source_path": source_path,
                    "artifact_role": self._analysis_packet_optional_string(
                        item,
                        index=index,
                        item_name="artifacts",
                        field="artifact_role",
                        aliases=("role",),
                    ),
                    "media_type": self._analysis_packet_optional_string(
                        item,
                        index=index,
                        item_name="artifacts",
                        field="media_type",
                    ),
                    "content_hash": self._analysis_packet_optional_string(
                        item,
                        index=index,
                        item_name="artifacts",
                        field="content_hash",
                    ),
                    "byte_size": item.get("byte_size"),
                    "image_width": item.get("image_width"),
                    "image_height": item.get("image_height"),
                    "supports": supports,
                }
            )
        return specs
    def _normalise_analysis_packet_followup_tasks(
        self,
        packet_iri: str,
        followup_tasks: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
    ) -> list[dict[str, Any]]:
        task_values = self._normalise_manifest_object_list(
            "followup_tasks",
            followup_tasks,
        )
        allowed_fields = {
            "iri",
            "task_iri",
            "label",
            "task_text",
            "text",
            "priority",
            "targets",
        }
        specs: list[dict[str, Any]] = []
        seen_iris: set[str] = set()
        for index, item in enumerate(task_values, start=1):
            unknown_fields = sorted(set(item) - allowed_fields)
            if unknown_fields:
                raise DoxaBaseError(
                    f"followup_tasks[{index}] has unsupported field(s): "
                    + ", ".join(unknown_fields)
                )
            task_text = self._analysis_packet_required_string(
                item,
                index=index,
                item_name="followup_tasks",
                fields=("task_text", "text"),
            )
            iri_value = item.get("iri", item.get("task_iri"))
            task_iri = (
                str(self._resource_ref(f"followup_tasks[{index}].iri", iri_value))
                if isinstance(iri_value, str) and iri_value.strip()
                else f"{packet_iri}/followup-task/{index}"
            )
            if task_iri in seen_iris:
                raise DoxaBaseError(
                    f"followup_tasks[{index}].iri duplicates {task_iri}"
                )
            seen_iris.add(task_iri)
            targets = [
                str(self._resource_ref(f"followup_tasks[{index}].targets", value))
                for value in self._string_values("targets", item.get("targets"))
            ]
            specs.append(
                {
                    "iri": task_iri,
                    "label": self._analysis_packet_optional_string(
                        item,
                        index=index,
                        item_name="followup_tasks",
                        field="label",
                    ),
                    "task_text": task_text,
                    "priority": self._analysis_packet_optional_string(
                        item,
                        index=index,
                        item_name="followup_tasks",
                        field="priority",
                    ),
                    "targets": targets,
                }
            )
        return specs
    @staticmethod
    def _analysis_packet_required_string(
        item: Mapping[str, Any],
        *,
        index: int,
        item_name: str,
        fields: tuple[str, ...],
    ) -> str:
        for field in fields:
            value = item.get(field)
            if value is None:
                continue
            if not isinstance(value, str) or not value.strip():
                raise DoxaBaseError(
                    f"{item_name}[{index}].{field} must be a non-empty string"
                )
            return value.strip()
        raise DoxaBaseError(
            f"{item_name}[{index}].{fields[0]} must be a non-empty string"
        )
    @staticmethod
    def _analysis_packet_optional_string(
        item: Mapping[str, Any],
        *,
        index: int,
        item_name: str,
        field: str,
        aliases: tuple[str, ...] = (),
    ) -> str | None:
        for name in (field, *aliases):
            value = item.get(name)
            if value is None:
                continue
            if not isinstance(value, str):
                raise DoxaBaseError(f"{item_name}[{index}].{name} must be a string")
            return value.strip() or None
        return None
    def _record_analysis_packet_resource(
        self,
        *,
        packet_iri: str,
        label: str | None,
        summary: str,
        evidence_sources: Iterable[str],
        analysis_view_iris: Iterable[str],
        artifact_iris: Iterable[str],
        query_recipe_iris: Iterable[str],
        followup_task_iris: Iterable[str],
    ) -> int:
        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(packet_iri)
        graph.add((subject, RDF.type, URIRef(self.expand_iri("rc:Evidence"))))
        graph.add((subject, RDF.type, URIRef(self.expand_iri("rc:AnalysisPacket"))))
        self._add_optional_literal(graph, subject, str(RDFS.label), label)
        graph.add((subject, URIRef(self.expand_iri("rc:summary")), Literal(summary)))
        for source in evidence_sources:
            graph.add((subject, DCTERMS.source, Literal(source)))
        for view_iri in analysis_view_iris:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:packetAnalysisView")),
                    URIRef(view_iri),
                )
            )
        for artifact_iri in artifact_iris:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasAnalysisArtifact")),
                    URIRef(artifact_iri),
                )
            )
        for query_recipe_iri in query_recipe_iris:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasQueryRecipe")),
                    URIRef(query_recipe_iri),
                )
            )
        for task_iri in followup_task_iris:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasFollowupTask")),
                    URIRef(task_iri),
                )
            )
        return self._replace_subject_triples(
            "evidence",
            packet_iri,
            [
                str(RDF.type),
                str(RDFS.label),
                self.expand_iri("rc:summary"),
                str(DCTERMS.source),
                self.expand_iri("rc:packetAnalysisView"),
                self.expand_iri("rc:hasAnalysisArtifact"),
                self.expand_iri("rc:hasQueryRecipe"),
                self.expand_iri("rc:hasFollowupTask"),
            ],
            graph,
        )
    def _record_analysis_packet_artifacts(
        self,
        *,
        packet_iri: str,
        artifacts: Iterable[Mapping[str, Any]],
    ) -> list[AnalysisArtifactRecord]:
        records: list[AnalysisArtifactRecord] = []
        for artifact in artifacts:
            graph = Graph()
            self._bind_prefixes(graph)
            subject = URIRef(artifact["iri"])
            graph.add((subject, RDF.type, URIRef(self.expand_iri("rc:Evidence"))))
            graph.add(
                (subject, RDF.type, URIRef(self.expand_iri("rc:AnalysisArtifact")))
            )
            graph.add((subject, DCTERMS.source, Literal(artifact["source_path"])))
            self._add_optional_literal(graph, subject, str(RDFS.label), artifact["label"])
            self._add_optional_literal(
                graph,
                subject,
                "rc:summary",
                artifact["summary"],
            )
            self._add_optional_literal(
                graph,
                subject,
                "rc:artifactRole",
                artifact["artifact_role"],
            )
            self._add_optional_literal(
                graph,
                subject,
                "rc:mediaType",
                artifact["media_type"],
            )
            self._add_optional_literal(
                graph,
                subject,
                "rc:contentHash",
                artifact["content_hash"],
            )
            for predicate, value in (
                ("rc:byteSize", artifact["byte_size"]),
                ("rc:imageWidth", artifact["image_width"]),
                ("rc:imageHeight", artifact["image_height"]),
            ):
                if value is not None:
                    graph.add(
                        (
                            subject,
                            URIRef(self.expand_iri(predicate)),
                            Literal(value, datatype=XSD.integer),
                        )
                    )
            graph.add((subject, URIRef(self.expand_iri("rc:supports")), URIRef(packet_iri)))
            for target in artifact["supports"]:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:supports")),
                        URIRef(target),
                    )
                )
            triples = self._replace_subject_triples(
                "evidence",
                artifact["iri"],
                [
                    str(RDF.type),
                    str(RDFS.label),
                    str(DCTERMS.source),
                    self.expand_iri("rc:summary"),
                    self.expand_iri("rc:artifactRole"),
                    self.expand_iri("rc:mediaType"),
                    self.expand_iri("rc:contentHash"),
                    self.expand_iri("rc:byteSize"),
                    self.expand_iri("rc:imageWidth"),
                    self.expand_iri("rc:imageHeight"),
                    self.expand_iri("rc:supports"),
                ],
                graph,
            )
            records.append(
                AnalysisArtifactRecord(
                    iri=artifact["iri"],
                    graph="evidence",
                    triples=triples,
                )
            )
        return records
    def _record_analysis_packet_query_recipes(
        self,
        *,
        packet_iri: str,
        query_recipes: Iterable[Mapping[str, Any]],
    ) -> list[AnalysisQueryRecipeRecord]:
        records: list[AnalysisQueryRecipeRecord] = []
        for recipe in query_recipes:
            graph = Graph()
            self._bind_prefixes(graph)
            subject = URIRef(recipe["iri"])
            graph.add(
                (
                    subject,
                    RDF.type,
                    URIRef(self.expand_iri("rc:ExecutableQuerySnippet")),
                )
            )
            self._add_optional_literal(graph, subject, str(RDFS.label), recipe["label"])
            self._add_optional_literal(
                graph,
                subject,
                str(RDFS.comment),
                recipe["description"],
            )
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:queryText")),
                    Literal(recipe["query_text"]),
                )
            )
            self._add_optional_literal(
                graph,
                subject,
                "rc:queryLanguage",
                recipe["query_language"],
            )
            self._add_optional_literal(
                graph,
                subject,
                "rc:queryRuntime",
                recipe["query_engine"],
            )
            graph.add((subject, URIRef(self.expand_iri("rc:supports")), URIRef(packet_iri)))
            for target in recipe["targets"]:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:supports")),
                        URIRef(target),
                    )
                )
            triples = self._replace_subject_triples(
                "evidence",
                recipe["iri"],
                [
                    str(RDF.type),
                    str(RDFS.label),
                    str(RDFS.comment),
                    self.expand_iri("rc:queryText"),
                    self.expand_iri("rc:queryLanguage"),
                    self.expand_iri("rc:queryRuntime"),
                    self.expand_iri("rc:supports"),
                ],
                graph,
            )
            records.append(
                AnalysisQueryRecipeRecord(
                    iri=recipe["iri"],
                    graph="evidence",
                    triples=triples,
                )
            )
        return records
    def _record_analysis_packet_followup_tasks(
        self,
        *,
        packet_iri: str,
        followup_tasks: Iterable[Mapping[str, Any]],
    ) -> list[AnalysisFollowupTaskRecord]:
        records: list[AnalysisFollowupTaskRecord] = []
        for task in followup_tasks:
            graph = Graph()
            self._bind_prefixes(graph)
            subject = URIRef(task["iri"])
            graph.add(
                (
                    subject,
                    RDF.type,
                    URIRef(self.expand_iri("rc:AnalysisFollowupTask")),
                )
            )
            self._add_optional_literal(graph, subject, str(RDFS.label), task["label"])
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:taskText")),
                    Literal(task["task_text"]),
                )
            )
            self._add_optional_literal(
                graph,
                subject,
                "rc:taskPriority",
                task["priority"],
            )
            for target in task["targets"]:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:taskTarget")),
                        URIRef(target),
                    )
                )
            triples = self._replace_subject_triples(
                "evidence",
                task["iri"],
                [
                    str(RDF.type),
                    str(RDFS.label),
                    self.expand_iri("rc:taskText"),
                    self.expand_iri("rc:taskPriority"),
                    self.expand_iri("rc:taskTarget"),
                ],
                graph,
            )
            records.append(
                AnalysisFollowupTaskRecord(
                    iri=task["iri"],
                    graph="evidence",
                    triples=triples,
                )
            )
        return records
