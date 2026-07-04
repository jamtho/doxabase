"""Observation, claim, reconsideration, and pattern recording.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via ObservationsMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class ObservationsMixin:
    def _assertion_supporting_claim_targets_resource(
        self,
        summary: AssertionSupportRouteSummary,
        target_iris: set[str],
    ) -> bool:
        all_graphs = self._expand_graphs(["all"])
        for matched in summary.matched_resources:
            claim_targets = set(
                self._objects(all_graphs, matched.iri, "rc:claimTarget")
            )
            if claim_targets & target_iris:
                return True
        return False
    def _assertion_auto_supporting_pattern_iris(
        self,
        support: AssertionSupportDescription,
    ) -> list[str]:
        target_iris = {resource.iri for resource in support.target_resources}
        summary_by_iri = {
            summary.resource.iri: summary
            for summary in support.related_route_summaries
            if summary.resource_kind == "pattern"
        }
        direct_route_types = {"target_resource", "pattern_target", "map_implication"}
        selected: list[str] = []
        for pattern in support.related_patterns:
            summary = summary_by_iri.get(pattern.iri)
            if summary is None:
                continue
            route_types = set(summary.route_types)
            if route_types & direct_route_types:
                selected.append(pattern.iri)
                continue
            if (
                "supporting_claim" in route_types
                and self._assertion_supporting_claim_targets_resource(
                    summary,
                    target_iris,
                )
            ):
                selected.append(pattern.iri)
        return list(dict.fromkeys(selected))
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
    def _context_slice_pattern_action_key(
        self,
        pattern_context: PatternDescription,
        *,
        resources: Mapping[str, list[ContextSliceRoute]],
        lookup_graphs: list[str],
        linked_pattern_relevance_ranks: Mapping[str, int],
    ) -> tuple[int, int, int, str, str]:
        routes = resources.get(pattern_context.iri, [])
        if not routes:
            return (
                999,
                999,
                999,
                pattern_context.summary or pattern_context.iri,
                pattern_context.iri,
            )
        best_route_key = min(
            self._context_slice_pattern_action_route_key(route) for route in routes
        )
        if pattern_context.iri in linked_pattern_relevance_ranks:
            best_route_key = min(
                best_route_key,
                (
                    linked_pattern_relevance_ranks[pattern_context.iri],
                    best_route_key[1],
                    best_route_key[2],
                ),
            )
        return (
            *best_route_key,
            self._display_label_from_graphs(lookup_graphs, pattern_context.iri)
            or pattern_context.summary
            or "",
            pattern_context.iri,
        )
    def _context_slice_pattern_action_route_key(
        self,
        route: ContextSliceRoute,
    ) -> tuple[int, int, int]:
        if route.route == "seed":
            return (-1, route.depth, self._context_slice_route_priority(route.route))
        if route.route.startswith("linked_pattern_"):
            relevance_tier = route.route.removeprefix("linked_pattern_")
            return (
                self._linked_pattern_relevance_rank(relevance_tier),
                route.depth,
                self._context_slice_route_priority(route.route),
            )
        if route.route == "linked_pattern":
            return (50, route.depth, self._context_slice_route_priority(route.route))
        return (
            100 + self._context_slice_route_priority(route.route),
            route.depth,
            self._context_slice_route_priority(route.route),
        )
    def _context_slice_linked_pattern_relevance_ranks(
        self,
        dataset_contexts: Iterable[DatasetDescription],
    ) -> dict[str, int]:
        ranks: dict[str, int] = {}
        for dataset in dataset_contexts:
            for reason in dataset.linked_pattern_reasons:
                if not reason.match_groups:
                    continue
                rank = min(
                    self._linked_pattern_relevance_rank(group.relevance_tier)
                    for group in reason.match_groups
                )
                current_rank = ranks.get(reason.pattern_iri)
                if current_rank is None or rank < current_rank:
                    ranks[reason.pattern_iri] = rank
        return ranks
    def _ordinary_observation_iris_for_target(
        self,
        *,
        target_iri: str,
        target_predicate: str,
    ) -> list[str]:
        observation_graphs = ["observations"]
        observation_type = self.expand_iri("rc:Observation")
        profile_type = self.expand_iri("rc:ProfileObservation")
        observation_iris = [
            observation_iri
            for observation_iri in self._subjects(
                observation_graphs,
                target_predicate,
                target_iri,
            )
            if observation_type
            in self._types_from_graphs(observation_graphs, observation_iri)
            and profile_type
            not in self._types_from_graphs(observation_graphs, observation_iri)
        ]
        observation_iris.sort(key=self._ordinary_observation_sort_key, reverse=True)
        return observation_iris
    def _ordinary_observation_sort_key(self, observation_iri: str) -> tuple[str, str, str]:
        observation_graphs = ["observations"]
        return (
            self._first_object(observation_graphs, observation_iri, "rc:observedAt")
            or "",
            self._first_object(observation_graphs, observation_iri, "rc:summary")
            or "",
            observation_iri,
        )
    def _observed_value_frequency_summaries(
        self,
        graphs: list[str],
        observation_iri: str,
    ) -> list[ObservedValueFrequencySummary]:
        summaries: list[ObservedValueFrequencySummary] = []
        for value_frequency_iri in self._objects(
            graphs,
            observation_iri,
            "rc:observedValueFrequency",
        ):
            value = self._first_object(
                graphs,
                value_frequency_iri,
                "rc:observedValue",
            )
            frequency = self._int_object(
                graphs,
                value_frequency_iri,
                "rc:valueFrequency",
            )
            if value is None or frequency is None:
                continue
            summaries.append(
                ObservedValueFrequencySummary(
                    iri=value_frequency_iri,
                    value=self._redact_sensitive_context_value(value),
                    frequency=frequency,
                )
            )
        return sorted(
            summaries,
            key=lambda item: (-item.frequency, item.value, item.iri),
        )
    def record_observation(
        self,
        summary: str,
        *,
        observation_type: TypingLiteral["observation", "profile"] = "observation",
        observed_asset: str | None = None,
        observed_column: str | None = None,
        observed_column_name: str | None = None,
        observed_at: datetime | str | None = None,
        observed_by: str | None = None,
        evidence_summary: str | None = None,
        evidence_sources: Iterable[str] | None = None,
        sample_size: int | None = None,
        sample_scope: str | None = None,
        sample_method: str | None = None,
        row_count: int | None = None,
        null_count: int | None = None,
        distinct_count: int | None = None,
        value_frequencies: Iterable[Mapping[str, Any]] | None = None,
        profile_metrics: Iterable[Mapping[str, Any]] | None = None,
        observed_physical_type: str | None = None,
        observed_value_type: str | None = None,
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
        value_frequency_values = self._profile_value_frequency_values(
            value_frequencies
        )
        profile_metric_values = self._profile_metric_values(profile_metrics)
        observed_physical_type_ref = (
            self._resource_ref("observed_physical_type", observed_physical_type)
            if observed_physical_type is not None
            else None
        )
        observed_value_type_ref = (
            self._resource_ref("observed_value_type", observed_value_type)
            if observed_value_type is not None
            else None
        )
        if (
            observed_physical_type_ref is not None
            or observed_value_type_ref is not None
        ):
            if observation_type != "profile":
                raise DoxaBaseError(
                    "observed_physical_type and observed_value_type require "
                    "observation_type='profile'"
                )
            if observed_column is None:
                raise DoxaBaseError(
                    "observed type findings require observed_column"
                )

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
        if evidence_subject is not None:
            self._preflight_evidence_summary_reuse(
                str(evidence_subject),
                evidence_summary,
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
        if observed_column_name is not None:
            if observed_column is None:
                raise DoxaBaseError(
                    "observed_column_name requires observed_column"
                )
            column_name_value = observed_column_name.strip()
            if not column_name_value:
                raise DoxaBaseError("observed_column_name must not be empty")
            observation_graph.add(
                (
                    observation_subject,
                    URIRef(self.expand_iri("rc:observedColumnName")),
                    Literal(column_name_value),
                )
            )
        if observed_physical_type_ref is not None:
            observation_graph.add(
                (
                    observation_subject,
                    URIRef(self.expand_iri("rc:observedPhysicalType")),
                    observed_physical_type_ref,
                )
            )
        if observed_value_type_ref is not None:
            observation_graph.add(
                (
                    observation_subject,
                    URIRef(self.expand_iri("rc:observedValueType")),
                    observed_value_type_ref,
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
        self._add_optional_literal(
            observation_graph,
            observation_subject,
            "rc:sampleScope",
            sample_scope,
        )
        self._add_optional_literal(
            observation_graph,
            observation_subject,
            "rc:sampleMethod",
            sample_method,
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
        for observed_value, frequency in value_frequency_values:
            value_frequency_subject = URIRef(
                self._mint_iri("observed-value-frequency")
            )
            observation_graph.add(
                (
                    observation_subject,
                    URIRef(self.expand_iri("rc:observedValueFrequency")),
                    value_frequency_subject,
                )
            )
            observation_graph.add(
                (
                    value_frequency_subject,
                    RDF.type,
                    URIRef(self.expand_iri("rc:ObservedValueFrequency")),
                )
            )
            observation_graph.add(
                (
                    value_frequency_subject,
                    URIRef(self.expand_iri("rc:observedValue")),
                    Literal(observed_value),
                )
            )
            observation_graph.add(
                (
                    value_frequency_subject,
                    URIRef(self.expand_iri("rc:valueFrequency")),
                    Literal(frequency, datatype=XSD.integer),
                )
            )
        for (
            metric_kind,
            metric_value,
            datatype,
            lang,
            metric_target,
        ) in profile_metric_values:
            metric_subject = URIRef(self._mint_iri("observed-profile-metric"))
            observation_graph.add(
                (
                    observation_subject,
                    URIRef(self.expand_iri("rc:observedProfileMetric")),
                    metric_subject,
                )
            )
            observation_graph.add(
                (
                    metric_subject,
                    RDF.type,
                    URIRef(self.expand_iri("rc:ObservedProfileMetric")),
                )
            )
            observation_graph.add(
                (
                    metric_subject,
                    URIRef(self.expand_iri("rc:profileMetricKind")),
                    URIRef(self.expand_iri(metric_kind)),
                )
            )
            if metric_target is not None:
                observation_graph.add(
                    (
                        metric_subject,
                        URIRef(self.expand_iri("rc:profileMetricTarget")),
                        URIRef(metric_target),
                    )
                )
            literal = (
                Literal(str(metric_value), lang=lang)
                if lang is not None
                else Literal(
                    metric_value,
                    datatype=URIRef(self.expand_iri(datatype)) if datatype else None,
                )
            )
            observation_graph.add(
                (
                    metric_subject,
                    URIRef(self.expand_iri("rc:profileMetricValue")),
                    literal,
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
        if confidence_value is not None:
            self._controlled_resource_ref(
                "confidence",
                confidence_value,
                CONFIDENCE_LEVELS,
            )
        if observation_status_value is not None:
            self._controlled_resource_ref(
                "observation_status",
                observation_status_value,
                PATTERN_OBSERVATION_STATUSES,
            )
        if not evidence_source_values and source_path_value is None:
            raise DoxaBaseError(
                "record_claim_observation requires evidence_sources or source_path"
            )
        for name, value in {"start_line": start_line, "end_line": end_line}.items():
            if value is not None and value < 1:
                raise DoxaBaseError(f"{name} must be a positive one-based line number")
        if source_path_value is not None:
            self._preflight_source_span_reuse(
                source_span_iri=source_span_iri,
                source_path=source_path_value,
                source_section=source_section_value,
                start_line=start_line,
                end_line=end_line,
                source_kind=source_kind_value,
            )

        observation_subject = URIRef(observation_iri or self._mint_iri("observation"))
        claim_subject = URIRef(claim_iri or self._mint_iri("claim"))
        evidence_subject = URIRef(evidence_iri or self._mint_iri("evidence"))
        self._preflight_evidence_summary_reuse(
            str(evidence_subject),
            evidence_summary,
        )
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
        if confidence_value is not None:
            self._controlled_resource_ref(
                "confidence",
                confidence_value,
                CONFIDENCE_LEVELS,
            )
        if pattern_status_value is not None:
            self._controlled_resource_ref(
                "pattern_status",
                pattern_status_value,
                PATTERN_OBSERVATION_STATUSES,
            )
        if pattern_stability_value is not None:
            self._controlled_resource_ref(
                "pattern_stability",
                pattern_stability_value,
                PATTERN_STABILITY_LEVELS,
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
        if source_path_value is not None:
            self._preflight_source_span_reuse(
                source_span_iri=source_span_iri,
                source_path=source_path_value,
                source_section=source_section_value,
                start_line=start_line,
                end_line=end_line,
                source_kind=source_kind_value,
            )

        pattern_subject = URIRef(pattern_iri or self._mint_iri("pattern"))
        evidence_subject = (
            URIRef(evidence_iri_value)
            if evidence_iri_value is not None
            else URIRef(self._mint_iri("evidence"))
            if evidence_source_values or source_path_value
            else None
        )
        if evidence_subject is not None:
            self._preflight_evidence_summary_reuse(
                str(evidence_subject),
                evidence_summary,
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

        pattern_triples = self._write_pattern_graph(
            pattern_subject,
            pattern_graph,
            replace_existing=pattern_iri is not None,
        )
        return PatternRecord(
            pattern_iri=str(pattern_subject),
            evidence_iri=str(evidence_subject) if evidence_subject is not None else None,
            source_span_iri=(
                str(source_span_subject) if source_span_subject is not None else None
            ),
            pattern_triples=pattern_triples,
            evidence_triples=evidence_triples,
        )
    def _write_pattern_graph(
        self,
        pattern_subject: URIRef,
        pattern_graph: Graph,
        *,
        replace_existing: bool,
    ) -> int:
        if not replace_existing:
            return self._insert_graph("patterns", pattern_graph)
        return self._replace_subject_triples(
            "patterns",
            str(pattern_subject),
            [
                str(RDF.type),
                self.expand_iri("rc:summary"),
                self.expand_iri("rc:patternText"),
                self.expand_iri("rc:rationale"),
                self.expand_iri("rc:synthesizedAt"),
                self.expand_iri("rc:synthesizedBy"),
                self.expand_iri("rc:patternTarget"),
                self.expand_iri("rc:supportingObservation"),
                self.expand_iri("rc:supportingClaim"),
                self.expand_iri("rc:evidence"),
                self.expand_iri("rc:confidence"),
                self.expand_iri("rc:observationStatus"),
                self.expand_iri("rc:patternStability"),
                self.expand_iri("rc:mapImplication"),
            ],
            pattern_graph,
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
        explicit_status_value = (
            older_claim_status.strip()
            if older_claim_status and older_claim_status.strip()
            else None
        )
        status_value = explicit_status_value or default_status
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
        if source_path_value is not None:
            self._preflight_source_span_reuse(
                source_span_iri=source_span_iri,
                source_path=source_path_value,
                source_section=source_section_value,
                start_line=start_line,
                end_line=end_line,
                source_kind=source_kind_value,
            )

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
        if evidence_subject is not None:
            self._preflight_evidence_summary_reuse(
                str(evidence_subject),
                evidence_summary,
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
        effective_status_value = status_value
        if status_value is not None:
            effective_status_value = (
                self._claim_reconsideration_effective_status(
                    older_claim_iri=older_claim_iri,
                    requested_status=status_value,
                    explicit=explicit_status_value is not None,
                )
            )
        if status_value is not None and effective_status_value == status_value:
            status_graph = Graph()
            self._bind_prefixes(status_graph)
            status_graph.add(
                (
                    URIRef(older_claim_iri),
                    URIRef(self.expand_iri("rc:observationStatus")),
                    URIRef(self.expand_iri(effective_status_value)),
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
                self.expand_iri(effective_status_value)
                if effective_status_value is not None
                else None
            ),
            evidence_iri=str(evidence_subject) if evidence_subject is not None else None,
            source_span_iri=(
                str(source_span_subject) if source_span_subject is not None else None
            ),
            reconsideration_triples=reconsideration_triples,
            evidence_triples=evidence_triples,
            status_triples=status_triples,
        )
    def _claim_reconsideration_effective_status(
        self,
        *,
        older_claim_iri: str,
        requested_status: str,
        explicit: bool,
    ) -> str:
        if explicit:
            return requested_status
        requested_status_iri = self.expand_iri(requested_status)
        if requested_status_iri != self.expand_iri("rc:Weakened"):
            return requested_status
        terminal_statuses = {
            self.expand_iri("rc:Superseded"),
            self.expand_iri("rc:Contradicted"),
        }
        for current_status in self._objects(
            ["observations"],
            older_claim_iri,
            "rc:observationStatus",
        ):
            if current_status in terminal_statuses:
                return current_status
        return requested_status
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
        profile_route_sources: Iterable[Mapping[str, Any]]
        | Mapping[str, Any]
        | None = None,
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
            profile_route_sources=profile_route_sources,
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
    def _enrich_staged_pattern_support_validation_hints(
        self,
        diagnostics: list[ValidationDiagnostic],
        *,
        patches: list[StagedGraphPatchDescription],
        revision_has_support_metadata: bool,
    ) -> list[ValidationDiagnostic]:
        if not diagnostics or not patches or not revision_has_support_metadata:
            return diagnostics
        pattern_shape = self.expand_iri("rc:PatternShape")
        or_constraint = PREFIXES["sh"] + "OrConstraintComponent"
        missing_support_focus_nodes = {
            diagnostic.focus_node
            for diagnostic in diagnostics
            if diagnostic.focus_node is not None
            and diagnostic.source_shape == pattern_shape
            and diagnostic.source_constraint_component == or_constraint
            and any(
                "supported by observations, claims, or evidence" in message
                for message in diagnostic.messages
            )
        }
        if not missing_support_focus_nodes:
            return diagnostics
        staged_focus_nodes = self._staged_pattern_support_patch_focus_nodes(
            patches,
            focus_nodes=missing_support_focus_nodes,
        )
        if not staged_focus_nodes:
            return diagnostics
        hint = (
            "Revision-level support metadata does not satisfy support "
            "requirements for a newly staged rc:Pattern resource. Add at least "
            "one rc:supportingObservation, rc:supportingClaim, or rc:evidence "
            "triple inside the pattern framing Turtle itself."
        )
        enriched: list[ValidationDiagnostic] = []
        for diagnostic in diagnostics:
            if (
                diagnostic.focus_node in staged_focus_nodes
                and diagnostic.source_shape == pattern_shape
                and diagnostic.source_constraint_component == or_constraint
                and diagnostic.hint is None
            ):
                enriched.append(replace(diagnostic, hint=hint))
            else:
                enriched.append(diagnostic)
        return enriched
    def _staged_pattern_support_patch_focus_nodes(
        self,
        patches: list[StagedGraphPatchDescription],
        *,
        focus_nodes: set[str],
    ) -> set[str]:
        addition_operation = self.expand_iri("rc:AdditionPatch")
        found: set[str] = set()
        for patch in patches:
            try:
                operation = self._required_staged_patch_field(
                    patch,
                    "operation",
                    patch.operation,
                )
                if operation != addition_operation:
                    continue
                patch_graph = self._parse_staged_patch_description(patch)
            except DoxaBaseError:
                continue
            for focus_node in focus_nodes:
                focus_ref = URIRef(focus_node)
                if any(patch_graph.triples((focus_ref, None, None))):
                    found.add(focus_node)
        return found
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
                self._describe_evidence(
                    evidence_iri,
                    self._evidence_detail_graphs(graphs),
                    lookup_graphs,
                )
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
