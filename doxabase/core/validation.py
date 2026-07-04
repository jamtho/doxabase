"""Parse and SHACL validation.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via ValidationMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class ValidationMixin:
    def _validate_transform_output_condition_refs(
        self,
        condition_specs: Iterable[Mapping[str, Any]],
        output_specs: Iterable[Mapping[str, Any]],
    ) -> None:
        supplied_condition_iris = {
            str(condition["iri"]) for condition in condition_specs
        }
        transform_condition_type = self.expand_iri("rc:TransformCondition")
        all_graphs = self._expand_graphs(["all"])
        for output_index, output in enumerate(output_specs, start=1):
            for condition in output["conditions"]:
                condition_iri = str(
                    self._resource_ref(
                        f"outputs[{output_index}].conditions",
                        condition,
                    )
                )
                if condition_iri in supplied_condition_iris:
                    continue
                if transform_condition_type in self._types_from_graphs(
                    all_graphs,
                    condition_iri,
                ):
                    continue
                raise DoxaBaseError(
                    f"outputs[{output_index}].conditions references "
                    f"{condition_iri!r}, which is not a supplied or existing "
                    "rc:TransformCondition"
                )
    def _validation_dependency_graphs_for_scope(self, scope: str) -> list[str]:
        return list(
            dict.fromkeys(
                [
                    *self._graphs_for_validation_scope(scope),
                    *self._expand_graphs(["shapes"]),
                ]
            )
        )
    def _exception_type_and_message(self, exc: Exception) -> str:
        message = str(exc).strip().split(" at ^ in", 1)[0]
        if message:
            return f"{exc.__class__.__name__}: {message[:500]}"
        return exc.__class__.__name__
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
    def _diagnostic_markdown_resource(self, iri: str, label: str | None) -> str:
        if label and label != iri:
            return f"{label} (`{iri}`)"
        return f"`{iri}`"
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
        conforms, report_graph, report_text = self._run_shacl_validation(
            data,
            shapes,
            context=f"scope '{scope}'",
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
        conforms, report_graph, report_text = self._run_shacl_validation(
            data,
            shapes,
            context=f"preview scope '{scope}'",
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
    def _run_shacl_validation(
        self,
        data: Graph,
        shapes: Graph,
        *,
        context: str,
    ) -> tuple[bool, Graph, str]:
        try:
            conforms, report_graph, report_text = validate(
                data_graph=data,
                shacl_graph=shapes,
                inference="rdfs",
                advanced=False,
            )
        except Exception as exc:
            detail = self._exception_type_and_message(exc)
            raise DoxaBaseError(
                f"Could not run SHACL validation for {context}: {detail}"
            ) from exc
        return bool(conforms), report_graph, str(report_text)
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
            hint=self._validation_diagnostic_hint(
                result_path=result_path,
                source_constraint_component=source_constraint_component,
                messages=messages,
            ),
        )
    def _validation_diagnostic_hint(
        self,
        *,
        result_path: str | None,
        source_constraint_component: str | None,
        messages: Iterable[str],
    ) -> str | None:
        if result_path == self.expand_iri("rc:rowSemantics") or any(
            "rowSemantics" in message for message in messages
        ):
            if (
                source_constraint_component
                == PREFIXES["sh"] + "MaxCountConstraintComponent"
            ):
                return (
                    "Keep exactly one of rc:EventRow, rc:SnapshotRow, "
                    "rc:AggregateRow, or rc:DimensionRow for rc:rowSemantics. "
                    "When changing an existing row-grain framing, use a "
                    "removal+addition patch or stage_revision map_assertion "
                    "replacement rather than adding a second value."
                )
            return (
                "Use one of rc:EventRow, rc:SnapshotRow, rc:AggregateRow, or "
                "rc:DimensionRow for rc:rowSemantics; put prose row-grain "
                "details in rdfs:comment, descriptions, caveats, observations, "
                "or patterns."
            )
        return None
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
    def _validate_resource_values(self, name: str, values: Iterable[str]) -> None:
        for value in values:
            self._resource_ref(name, value)
    @staticmethod
    def _validation_failure_summary(validation: ValidationResult) -> str:
        messages = [
            message
            for result in validation.results
            for message in result.messages
            if message
        ]
        if messages:
            first_message = messages[0]
        elif validation.results:
            first_result = validation.results[0]
            first_message = (
                first_result.result_path_label
                or first_result.result_path
                or first_result.focus_node_label
                or first_result.focus_node
                or "validation result"
            )
        else:
            first_message = "validation failed"
        remaining = max(validation.result_count - 1, 0)
        if remaining:
            return f"{first_message} (+{remaining} more)"
        return first_message
