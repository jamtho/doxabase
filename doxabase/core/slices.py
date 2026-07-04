"""Bounded context-slice assembly and rendering.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via SlicesMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class SlicesMixin:
    def get_context_graph(
        self,
        seed_iris: Iterable[str] | str,
        *,
        profile: TypingLiteral[
            "dataset_brief",
            "pattern_brief",
            "deep_lore",
            "resource_brief",
        ] = "dataset_brief",
        max_triples: int = 500,
        include_trig: bool = True,
        graph_iri_prefix: str = RCG_PREFIX,
        privacy_scan_limit: int = 20,
    ) -> ContextSlice:
        if max_triples < 1:
            raise DoxaBaseError("max_triples must be at least 1")
        if privacy_scan_limit < 1:
            raise DoxaBaseError("privacy_scan_limit must be at least 1")
        if profile not in {
            "dataset_brief",
            "pattern_brief",
            "deep_lore",
            "resource_brief",
        }:
            raise DoxaBaseError(
                "profile must be 'dataset_brief', 'pattern_brief', or "
                "'deep_lore', or 'resource_brief'; route explanations are "
                "returned as routes and route_legend on every valid profile, not as a "
                "'route_explained' profile"
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
        seed_profile_observations: dict[str, ProfileObservationSummary] = {}
        described_datasets: set[str] = set()
        described_patterns: set[str] = set()
        described_claims: set[str] = set()
        described_observations: set[str] = set()
        described_evidence: set[str] = set()
        described_revisions: set[str] = set()
        warnings: list[str] = []
        resource_brief_recovery_actions: dict[tuple[str, str], SuggestedNextAction] = {}
        resource_brief_profile_run_actions: dict[
            tuple[str, str],
            SuggestedNextAction,
        ] = {}
        resource_brief_graphs = self._context_slice_graphs(profile="resource_brief")
        resource_brief_route_limit = 25
        dataset_observation_route_limit = 5

        def resource_brief_export_path(seed_iri: str, suffix: str) -> str:
            label = re.sub(r"[^A-Za-z0-9]+", "-", self._local_name(seed_iri))
            label = label.strip("-").lower() or "resource"
            digest = hashlib.sha256(seed_iri.encode("utf-8")).hexdigest()[:12]
            return f"/tmp/doxabase-resource-brief-{label[:40]}-{suffix}-{digest}.ttl"

        def add_resource_brief_recovery_action(
            key: tuple[str, str],
            *,
            action_label: str,
            tool_name: str,
            arguments: dict[str, Any],
            reason: str,
        ) -> None:
            if key in resource_brief_recovery_actions:
                return
            resource_brief_recovery_actions[key] = SuggestedNextAction(
                action_label=action_label,
                tool_name=tool_name,
                mcp_tool_name=f"doxabase.{tool_name}",
                arguments=arguments,
                reason=reason,
                call=self._suggested_call_string(tool_name, arguments),
            )

        def add_resource_brief_profile_run_action(
            dataset_iri: str,
            evidence_iri: str,
            *,
            profile_observation_iri: str,
        ) -> None:
            key = (dataset_iri, evidence_iri)
            if key in resource_brief_profile_run_actions:
                return
            arguments = {
                "dataset_iri": dataset_iri,
                "evidence_iri": evidence_iri,
            }
            resource_brief_profile_run_actions[key] = SuggestedNextAction(
                action_label="Inspect profile run",
                tool_name="describe_profile_run",
                mcp_tool_name="doxabase.describe_profile_run",
                arguments=arguments,
                reason=(
                    "The evidence seed is linked from profile observation "
                    f"'{profile_observation_iri}' for this dataset. "
                    "describe_profile_run returns the shared-evidence profile "
                    "run before drafting map updates or exporting a handoff."
                ),
                call=self._suggested_call_string("describe_profile_run", arguments),
            )

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

        def add_evidence(
            evidence_iri: str,
            source_iri: str | None,
            depth: int,
            *,
            route: str = "evidence",
            route_label: str = "evidence",
        ) -> None:
            if evidence_iri in described_evidence:
                add_resource(
                    evidence_iri,
                    route,
                    route_label,
                    source_iri=source_iri,
                    depth=depth,
                )
                return
            described_evidence.add(evidence_iri)
            add_resource(
                evidence_iri,
                route,
                route_label,
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

        def add_profile_metric(
            metric_iri: str,
            source_iri: str | None,
            depth: int,
            *,
            include_parent_observations: bool = True,
        ) -> None:
            add_resource(
                metric_iri,
                "observed_profile_metric",
                "observed profile metric",
                source_iri=source_iri,
                depth=depth,
            )
            for metric_kind_iri in self._objects(
                all_graphs,
                metric_iri,
                "rc:profileMetricKind",
            ):
                add_resource(
                    metric_kind_iri,
                    "profile_metric_kind",
                    "profile metric kind",
                    source_iri=metric_iri,
                    depth=depth + 1,
                )
            for metric_target_iri in self._objects(
                all_graphs,
                metric_iri,
                "rc:profileMetricTarget",
            ):
                add_resource(
                    metric_target_iri,
                    "profile_metric_target",
                    "profile metric target",
                    source_iri=metric_iri,
                    depth=depth + 1,
                )
            if include_parent_observations:
                for observation_iri in self._subjects(
                    all_graphs,
                    "rc:observedProfileMetric",
                    metric_iri,
                ):
                    add_observation(
                        observation_iri,
                        metric_iri,
                        depth + 1,
                        route="profile_metric_observation",
                        route_label="profile metric observation",
                        expand_observed_dataset=True,
                    )

        def add_observation(
            observation_iri: str,
            source_iri: str | None,
            depth: int,
            *,
            route: str = "supporting_observation",
            route_label: str = "supporting observation",
            expand_observed_dataset: bool = False,
        ) -> None:
            should_track_seed_profile = route in {
                "seed_profile_observation",
                "profile_metric_observation",
            }
            if observation_iri in described_observations:
                add_resource(
                    observation_iri,
                    route,
                    route_label,
                    source_iri=source_iri,
                    depth=depth,
                )
                if should_track_seed_profile:
                    seed_profile_observations.setdefault(
                        observation_iri,
                        self._profile_observation_summary(
                            observation_iri,
                            all_lookup_graphs,
                        ),
                    )
                return
            described_observations.add(observation_iri)
            add_resource(
                observation_iri,
                route,
                route_label,
                source_iri=source_iri,
                depth=depth,
            )
            if should_track_seed_profile:
                seed_profile_observations.setdefault(
                    observation_iri,
                    self._profile_observation_summary(
                        observation_iri,
                        all_lookup_graphs,
                    ),
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
                    if (
                        expand_observed_dataset
                        and predicate == "rc:observedAsset"
                    ):
                        observed_types = self._types_from_graphs(
                            all_graphs,
                            observed_iri,
                        )
                        if (
                            self.expand_iri("rc:Dataset") in observed_types
                            or self.expand_iri("rc:Table") in observed_types
                        ):
                            add_dataset(observed_iri, observation_iri, depth + 2)
            for claim_iri in self._objects(all_graphs, observation_iri, "rc:hasClaim"):
                add_claim(claim_iri, observation_iri, depth + 1)
            for evidence_iri in self._objects(all_graphs, observation_iri, "rc:evidence"):
                add_evidence(evidence_iri, observation_iri, depth + 1)
            for value_frequency_iri in self._objects(
                all_graphs,
                observation_iri,
                "rc:observedValueFrequency",
            ):
                add_resource(
                    value_frequency_iri,
                    "observed_value_frequency",
                    "observed value frequency",
                    source_iri=observation_iri,
                    depth=depth + 1,
                )
            for metric_iri in self._objects(
                all_graphs,
                observation_iri,
                "rc:observedProfileMetric",
            ):
                add_profile_metric(
                    metric_iri,
                    observation_iri,
                    depth + 1,
                    include_parent_observations=False,
                )

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

        def add_revision(
            revision_iri: str,
            source_iri: str | None,
            depth: int,
            *,
            route: str = "seed_revision",
            route_label: str = "seed revision",
        ) -> None:
            if revision_iri in described_revisions:
                add_resource(
                    revision_iri,
                    route,
                    route_label,
                    source_iri=source_iri,
                    depth=depth,
                )
                return
            described_revisions.add(revision_iri)
            add_resource(
                revision_iri,
                route,
                route_label,
                source_iri=source_iri,
                depth=depth,
            )
            for evidence_iri in self._objects(all_graphs, revision_iri, "rc:evidence"):
                add_evidence(
                    evidence_iri,
                    revision_iri,
                    depth + 1,
                    route="revision_evidence",
                    route_label="revision evidence",
                )
            for pattern_iri in self._objects(
                all_graphs,
                revision_iri,
                "rc:revisionSupportingPattern",
            ):
                add_pattern(pattern_iri, revision_iri, depth + 1)
            for claim_iri in self._objects(
                all_graphs,
                revision_iri,
                "rc:revisionSupportingClaim",
            ):
                add_claim(claim_iri, revision_iri, depth + 1)
            for observation_iri in self._objects(
                all_graphs,
                revision_iri,
                "rc:revisionSupportingObservation",
            ):
                add_observation(observation_iri, revision_iri, depth + 1)
            for anchor_iri in self._objects(
                all_graphs,
                revision_iri,
                "rc:revisionAnchor",
            ):
                add_resource(
                    anchor_iri,
                    "revision_anchor",
                    "revision anchor",
                    source_iri=revision_iri,
                    depth=depth + 1,
                )
                anchor_types = self._types_from_graphs(all_graphs, anchor_iri)
                if (
                    self.expand_iri("rc:Dataset") in anchor_types
                    or self.expand_iri("rc:Table") in anchor_types
                ):
                    add_dataset(anchor_iri, revision_iri, depth + 2)
                elif self.expand_iri("rc:Column") in anchor_types:
                    add_column(anchor_iri, revision_iri, depth + 2)
            for staged_iri in self._objects(
                all_graphs,
                revision_iri,
                "rc:appliesStagedRevision",
            ):
                add_revision(
                    staged_iri,
                    revision_iri,
                    depth + 1,
                    route="applies_staged_revision",
                    route_label="applies staged revision",
                )
            for applied_iri in self._subjects(
                all_graphs,
                "rc:appliesStagedRevision",
                revision_iri,
            ):
                add_revision(
                    applied_iri,
                    revision_iri,
                    depth + 1,
                    route="applied_revision",
                    route_label="applied revision",
                )
            for source_revision_iri in self._objects(
                all_graphs,
                revision_iri,
                "rc:restagesRevision",
            ):
                add_revision(
                    source_revision_iri,
                    revision_iri,
                    depth + 1,
                    route="restaged_from_revision",
                    route_label="restaged from revision",
                )
            for successor_revision_iri in self._subjects(
                all_graphs,
                "rc:restagesRevision",
                revision_iri,
            ):
                add_revision(
                    successor_revision_iri,
                    revision_iri,
                    depth + 1,
                    route="restaged_by_revision",
                    route_label="restaged by revision",
                )
            for alternative_iri in self._objects(
                all_graphs,
                revision_iri,
                "rc:alternativeTo",
            ):
                add_revision(
                    alternative_iri,
                    revision_iri,
                    depth + 1,
                    route="alternative_revision",
                    route_label="alternative revision",
                )
            for alternative_iri in self._subjects(
                all_graphs,
                "rc:alternativeTo",
                revision_iri,
            ):
                add_revision(
                    alternative_iri,
                    revision_iri,
                    depth + 1,
                    route="alternative_revision",
                    route_label="alternative revision",
                )

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

        def add_column(column_iri: str, source_iri: str | None, depth: int) -> None:
            add_resource(
                column_iri,
                "seed_column" if source_iri is None else "related_column",
                "seed column" if source_iri is None else "related column",
                source_iri=source_iri,
                depth=depth,
            )
            owner = self._first_owner_dataset_iri(all_graphs, column_iri)
            if owner is not None:
                add_dataset(owner, column_iri, depth + 1)
            for pattern_iri in self._subjects(
                all_graphs,
                "rc:patternTarget",
                column_iri,
            ):
                add_pattern(pattern_iri, column_iri, depth + 1)
            for pattern_iri in self._subjects(
                all_graphs,
                "rc:mapImplication",
                column_iri,
            ):
                add_pattern(pattern_iri, column_iri, depth + 1)
            for claim_iri in self._subjects(all_graphs, "rc:claimTarget", column_iri):
                add_claim(claim_iri, column_iri, depth + 1)
            for observation_iri in self._subjects(
                all_graphs,
                "rc:observedColumn",
                column_iri,
            ):
                add_observation(observation_iri, column_iri, depth + 1)

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
            for endpoint in relationship.endpoints:
                add_resource(
                    endpoint.iri,
                    "relationship_endpoint",
                    "relationship endpoint",
                    source_iri=relationship.iri,
                    depth=depth + 1,
                )
                add_summary(
                    endpoint.dataset,
                    "relationship_endpoint_dataset",
                    "relationship endpoint dataset",
                    source_iri=endpoint.iri,
                    depth=depth + 2,
                )
            for condition in relationship.transform_conditions:
                add_resource(
                    condition.iri,
                    "transform_condition",
                    "transform condition",
                    source_iri=relationship.iri,
                    depth=depth + 1,
                )
                add_summary(
                    condition.condition_kind,
                    "transform_condition_kind",
                    "transform condition kind",
                    source_iri=condition.iri,
                    depth=depth + 2,
                )
                for summary in (
                    *condition.applies_to_datasets,
                    *condition.applies_to_endpoints,
                ):
                    add_summary(
                        summary,
                        "transform_condition_scope",
                        "transform condition scope",
                        source_iri=condition.iri,
                        depth=depth + 2,
                    )
            for output in relationship.transform_outputs:
                add_resource(
                    output.iri,
                    "transform_output",
                    "transform output",
                    source_iri=relationship.iri,
                    depth=depth + 1,
                )
                for summary in (output.target_dataset, output.function):
                    add_summary(
                        summary,
                        "transform_output_resource",
                        "transform output resource",
                        source_iri=output.iri,
                        depth=depth + 2,
                    )
                for condition in output.conditions:
                    add_resource(
                        condition.iri,
                        "transform_output_condition",
                        "transform output condition",
                        source_iri=output.iri,
                        depth=depth + 2,
                    )
                if output.tuple_grain is not None:
                    add_resource(
                        output.tuple_grain.iri,
                        "tuple_grain",
                        "tuple grain",
                        source_iri=output.iri,
                        depth=depth + 2,
                    )
                    for component in output.tuple_grain.components:
                        add_resource(
                            component.iri,
                            "grain_component",
                            "grain component",
                            source_iri=output.tuple_grain.iri,
                            depth=depth + 3,
                        )
                        for summary in (component.column, component.dataset):
                            add_summary(
                                summary,
                                "grain_component_resource",
                                "grain component resource",
                                source_iri=component.iri,
                                depth=depth + 4,
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
                for profile_observation in column.profile_observations:
                    add_observation(
                        profile_observation.iri,
                        column.iri,
                        depth + 2,
                        route="column_profile_observation",
                        route_label="column profile observation",
                    )
            for profile_observation in dataset.profile_observations:
                add_observation(
                    profile_observation.iri,
                    dataset_iri,
                    depth + 1,
                    route="dataset_profile_observation",
                    route_label="dataset profile observation",
                )
            for profile_observation in dataset.unmapped_column_profile_observations:
                add_observation(
                    profile_observation.iri,
                    dataset_iri,
                    depth + 1,
                    route="unmapped_column_profile_observation",
                    route_label="unmapped column profile observation",
                )
            dataset_observation_iris = self._ordinary_observation_iris_for_target(
                target_iri=dataset_iri,
                target_predicate="rc:observedAsset",
            )
            selected_dataset_observation_iris = dataset_observation_iris[
                :dataset_observation_route_limit
            ]
            omitted_dataset_observation_count = len(dataset_observation_iris) - len(
                selected_dataset_observation_iris
            )
            if omitted_dataset_observation_count > 0:
                warnings.append(
                    "Dataset "
                    f"'{dataset_iri}' has {len(dataset_observation_iris)} ordinary "
                    "observed-asset observation(s); included "
                    f"{len(selected_dataset_observation_iris)} and omitted "
                    f"{omitted_dataset_observation_count}. Seed a returned "
                    "observation or search the observations graph when older "
                    "query-result attempts matter."
                )
            for observation_iri in selected_dataset_observation_iris:
                add_observation(
                    observation_iri,
                    dataset_iri,
                    depth + 1,
                    route="dataset_observation",
                    route_label="dataset observation",
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
                for partition_column in partition.partition_columns:
                    add_summary(
                        partition_column,
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
            for grain in dataset.tuple_grains:
                add_resource(
                    grain.iri,
                    "tuple_grain",
                    "tuple grain",
                    source_iri=dataset_iri,
                    depth=depth + 1,
                )
                for component in grain.components:
                    add_resource(
                        component.iri,
                        "grain_component",
                        "grain component",
                        source_iri=grain.iri,
                        depth=depth + 2,
                    )
                    for summary in (component.column, component.dataset):
                        add_summary(
                            summary,
                            "grain_component_resource",
                            "grain component resource",
                            source_iri=component.iri,
                            depth=depth + 3,
                        )
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

        def add_resource_brief(seed_iri: str) -> None:
            for type_iri in self._types_from_graphs(resource_brief_graphs, seed_iri):
                add_resource(
                    type_iri,
                    "resource_type",
                    "resource type",
                    source_iri=seed_iri,
                    depth=1,
                )

            outgoing_refs, outgoing_total = self._resource_brief_outgoing_references(
                resource_brief_graphs,
                subject=seed_iri,
                limit=resource_brief_route_limit,
            )
            for resource_iri in outgoing_refs:
                add_resource(
                    resource_iri,
                    "outgoing_reference",
                    "outgoing reference",
                    source_iri=seed_iri,
                    depth=1,
                )
            if outgoing_total > len(outgoing_refs):
                warnings.append(
                    "resource_brief omitted "
                    f"{outgoing_total - len(outgoing_refs)} outgoing reference(s) "
                    f"for '{seed_iri}' after the route cap of "
                    f"{resource_brief_route_limit}. Raising max_triples does not "
                    "recover route-capped resources; page direct resource triples "
                    "with describe_resource when exact direct references matter."
                )
                add_resource_brief_recovery_action(
                    ("outgoing_reference", seed_iri),
                    action_label="Page outgoing resource references",
                    tool_name="describe_resource",
                    arguments={
                        "iri": seed_iri,
                        "include_incoming": False,
                        "limit": resource_brief_route_limit,
                        "outgoing_offset": len(outgoing_refs),
                    },
                    reason=(
                        "resource_brief capped outgoing references for this seed. "
                        "describe_resource supports offset paging over direct "
                        "resource triples; increasing context-slice max_triples "
                        "will not include omitted route-capped resources."
                    ),
                )

            (
                blank_node_refs,
                blank_node_total,
                blank_node_depth_exhausted,
            ) = self._resource_brief_blank_node_references(
                resource_brief_graphs,
                subject=seed_iri,
                limit=resource_brief_route_limit,
            )
            for resource_iri in blank_node_refs:
                add_resource(
                    resource_iri,
                    "blank_node_reference",
                    "blank-node reference",
                    source_iri=seed_iri,
                    depth=2,
                )
            if blank_node_total > len(blank_node_refs):
                warnings.append(
                    "resource_brief omitted "
                    f"{blank_node_total - len(blank_node_refs)} blank-node "
                    f"reference(s) for '{seed_iri}' after the route cap of "
                    f"{resource_brief_route_limit}. Raising max_triples does not "
                    "recover route-capped resources; inspect blank-node closure "
                    "with describe_resource when exact shape or nested RDF "
                    "details matter."
                )
                add_resource_brief_recovery_action(
                    ("blank_node_reference", seed_iri),
                    action_label="Inspect blank-node closure",
                    tool_name="describe_resource",
                    arguments={
                        "iri": seed_iri,
                        "include_blank_node_closure": True,
                        "blank_node_depth": 4,
                        "blank_node_limit": max(
                            blank_node_total,
                            resource_brief_route_limit * 4,
                        ),
                    },
                    reason=(
                        "resource_brief capped references found through blank "
                        "nodes. describe_resource with blank-node closure is the "
                        "direct recovery route for exact nested shape/RDF details."
                    ),
                )
            if blank_node_depth_exhausted:
                warnings.append(
                    "resource_brief blank-node expansion for "
                    f"'{seed_iri}' reached the bounded depth. Use "
                    "describe_resource(..., include_blank_node_closure=True) "
                    "with a larger blank_node_depth when exact shape closure "
                    "is needed."
                )
                add_resource_brief_recovery_action(
                    ("blank_node_depth", seed_iri),
                    action_label="Inspect deeper blank-node closure",
                    tool_name="describe_resource",
                    arguments={
                        "iri": seed_iri,
                        "include_blank_node_closure": True,
                        "blank_node_depth": 4,
                        "blank_node_limit": max(
                            blank_node_total,
                            resource_brief_route_limit * 4,
                        ),
                    },
                    reason=(
                        "resource_brief reached its bounded blank-node depth. "
                        "describe_resource exposes explicit blank_node_depth and "
                        "blank_node_limit controls."
                    ),
                )

            incoming_refs, incoming_total = self._resource_brief_incoming_subjects(
                resource_brief_graphs,
                object_iri=seed_iri,
                limit=resource_brief_route_limit,
            )
            for resource_iri in incoming_refs:
                add_resource(
                    resource_iri,
                    "incoming_reference",
                    "incoming reference",
                    source_iri=seed_iri,
                    depth=1,
                )
                resource_types = set(
                    self._types_from_graphs(resource_brief_graphs, resource_iri)
                )
                if resource_types & {
                    self.expand_iri("rc:Observation"),
                    self.expand_iri("rc:ProfileObservation"),
                }:
                    is_profile_observation = (
                        self.expand_iri("rc:ProfileObservation") in resource_types
                    )
                    evidence_seeded_profile_observation = (
                        is_profile_observation
                        and seed_iri
                        in self._objects(
                            resource_brief_graphs,
                            resource_iri,
                            "rc:evidence",
                        )
                    )
                    for observed_asset_iri in self._objects(
                        resource_brief_graphs,
                        resource_iri,
                        "rc:observedAsset",
                    ):
                        add_resource(
                            observed_asset_iri,
                            "observed_asset",
                            "observed asset",
                            source_iri=resource_iri,
                            depth=2,
                        )
                        if not evidence_seeded_profile_observation:
                            continue
                        observed_asset_types = set(
                            self._types_from_graphs(
                                resource_brief_graphs,
                                observed_asset_iri,
                            )
                        )
                        if observed_asset_types & {
                            self.expand_iri("rc:Dataset"),
                            self.expand_iri("rc:Table"),
                        }:
                            add_resource_brief_profile_run_action(
                                observed_asset_iri,
                                seed_iri,
                                profile_observation_iri=resource_iri,
                            )
            if incoming_total > len(incoming_refs):
                warnings.append(
                    "resource_brief omitted "
                    f"{incoming_total - len(incoming_refs)} incoming reference(s) "
                    f"for '{seed_iri}' after the route cap of "
                    f"{resource_brief_route_limit}. Raising max_triples does not "
                    "recover route-capped resources; page direct incoming triples "
                    "with describe_resource when exact inbound references matter."
                )
                add_resource_brief_recovery_action(
                    ("incoming_reference", seed_iri),
                    action_label="Page incoming resource references",
                    tool_name="describe_resource",
                    arguments={
                        "iri": seed_iri,
                        "limit": resource_brief_route_limit,
                        "incoming_offset": len(incoming_refs),
                    },
                    reason=(
                        "resource_brief capped incoming references for this seed. "
                        "describe_resource supports offset paging over direct "
                        "incoming triples; increasing context-slice max_triples "
                        "will not include omitted route-capped resources."
                    ),
                )

            (
                blank_node_owners,
                blank_node_owner_total,
            ) = self._resource_brief_incoming_blank_node_owners(
                resource_brief_graphs,
                object_iri=seed_iri,
                limit=resource_brief_route_limit,
            )
            for resource_iri in blank_node_owners:
                add_resource(
                    resource_iri,
                    "incoming_blank_node_owner",
                    "incoming blank-node owner",
                    source_iri=seed_iri,
                    depth=2,
                )
            if blank_node_owner_total > len(blank_node_owners):
                warnings.append(
                    "resource_brief omitted "
                    f"{blank_node_owner_total - len(blank_node_owners)} incoming "
                    f"blank-node owner(s) for '{seed_iri}' after the route cap of "
                    f"{resource_brief_route_limit}. There is no paged blank-node "
                    "owner browser yet; export or narrow the graph when exact "
                    "owner recovery matters."
                )
                add_resource_brief_recovery_action(
                    ("incoming_blank_node_owner", seed_iri),
                    action_label="Export graph for blank-node owner scan",
                    tool_name="export_graph",
                    arguments={
                        "path": resource_brief_export_path(
                            seed_iri,
                            "blank-node-owners",
                        ),
                        "graphs": "shapes",
                    },
                    reason=(
                        "resource_brief capped incoming blank-node owners. DoxaBase "
                        "does not yet expose paged blank-node owner browsing, so "
                        "export the likely shape graph or narrow from a known owner."
                    ),
                )
            if self._is_blank_node_subject(resource_brief_graphs, seed_iri):
                (
                    seed_blank_node_owners,
                    seed_blank_node_owner_total,
                    seed_blank_node_depth_exhausted,
                ) = self._resource_brief_blank_node_seed_owners(
                    resource_brief_graphs,
                    blank_node=seed_iri,
                    limit=resource_brief_route_limit,
                )
                for resource_iri in seed_blank_node_owners:
                    add_resource(
                        resource_iri,
                        "blank_node_seed_owner",
                        "blank-node seed owner",
                        source_iri=seed_iri,
                        depth=1,
                    )
                if seed_blank_node_owner_total > len(seed_blank_node_owners):
                    warnings.append(
                        "resource_brief omitted "
                        f"{seed_blank_node_owner_total - len(seed_blank_node_owners)} "
                        f"blank-node seed owner(s) for '{seed_iri}' after the "
                        f"route cap of {resource_brief_route_limit}. There is no "
                        "paged blank-node owner browser yet; export or narrow the "
                        "graph when exact owner recovery matters."
                    )
                    add_resource_brief_recovery_action(
                        ("blank_node_seed_owner", seed_iri),
                        action_label="Export graph for blank-node seed owner scan",
                        tool_name="export_graph",
                        arguments={
                            "path": resource_brief_export_path(
                                seed_iri,
                                "blank-node-seed-owners",
                            ),
                            "graphs": "shapes",
                        },
                        reason=(
                            "resource_brief capped owners for a blank-node seed. "
                            "DoxaBase does not yet expose paged blank-node owner "
                            "browsing, so export the likely shape graph or narrow "
                            "from a known owner."
                        ),
                    )
                if seed_blank_node_depth_exhausted:
                    warnings.append(
                        "resource_brief owner lookup for blank-node seed "
                        f"'{seed_iri}' reached the bounded depth. Use graph "
                        "export when exact nested blank-node ownership is needed."
                    )

            (
                predicate_users,
                predicate_user_total,
            ) = self._resource_brief_predicate_usage_subjects(
                resource_brief_graphs,
                predicate_iri=seed_iri,
                limit=resource_brief_route_limit,
            )
            for resource_iri in predicate_users:
                add_resource(
                    resource_iri,
                    "predicate_usage_subject",
                    "predicate usage subject",
                    source_iri=seed_iri,
                    depth=1,
                )
            if predicate_user_total > len(predicate_users):
                warnings.append(
                    "resource_brief omitted "
                    f"{predicate_user_total - len(predicate_users)} predicate "
                    f"usage subject(s) for '{seed_iri}' after the route cap of "
                    f"{resource_brief_route_limit}. There is no paged predicate-"
                    "usage browser yet; raising max_triples does not recover "
                    "route-capped predicate users."
                )
                add_resource_brief_recovery_action(
                    ("predicate_usage_subject", seed_iri),
                    action_label="Export project graph for predicate scan",
                    tool_name="export_graph",
                    arguments={
                        "path": resource_brief_export_path(seed_iri, "predicate-usage"),
                        "graphs": "project",
                    },
                    reason=(
                        "resource_brief capped subjects using this resource as a "
                        "predicate. There is no paged predicate-usage browser yet; "
                        "export project RDF or narrow from a known subject/search "
                        "hit when exact usage matters."
                    ),
                )

        profile_seed_limit = 25
        for seed in seeds:
            seed_is_subject = self._subject_exists(seed, all_graphs)
            metric_kind_metric_iris = self._subjects(
                all_graphs,
                "rc:profileMetricKind",
                seed,
            )
            observed_column_profile_observation_iris = self._subjects(
                all_graphs,
                "rc:observedColumn",
                seed,
            )
            observed_value_type_profile_observation_iris = self._subjects(
                all_graphs,
                "rc:observedValueType",
                seed,
            )
            seed_is_resource_brief_target = (
                profile == "resource_brief"
                and self._resource_brief_seed_exists(resource_brief_graphs, seed)
            )
            seed_is_observed_column_only = (
                profile in {"dataset_brief", "deep_lore"}
                and not seed_is_subject
                and bool(observed_column_profile_observation_iris)
            )
            if (
                not seed_is_subject
                and not metric_kind_metric_iris
                and not seed_is_observed_column_only
                and not observed_value_type_profile_observation_iris
                and not seed_is_resource_brief_target
            ):
                raise DoxaBaseError(
                    f"Seed resource '{seed}' was not found in visible RDF "
                    "triples. If this IRI may exist only inside staged patch "
                    "payloads, call list_resource_revisions(resource_iri=..., "
                    "include_patch_mentions=True) or search_staged_patch_payloads "
                    "before concluding it is absent."
                )
            add_resource(seed, "seed", "seed resource", depth=0)
            seed_types = self._types_from_graphs(all_graphs, seed)
            if profile == "resource_brief":
                if self.expand_iri("rc:Pattern") in seed_types:
                    warnings.append(
                        "Seed is an rc:Pattern; resource_brief gives a generic "
                        "resource card. Rerun with profile='pattern_brief' or "
                        "'deep_lore' to recover support, evidence, and pattern "
                        "routes."
                    )
                    add_resource_brief_recovery_action(
                        ("pattern_profile", seed),
                        action_label="Rerun as pattern brief",
                        tool_name="get_context_graph",
                        arguments={
                            "seed_iris": [seed],
                            "profile": "pattern_brief",
                            "max_triples": max_triples,
                        },
                        reason=(
                            "The seed is an rc:Pattern. resource_brief is useful "
                            "for a generic resource card, but pattern_brief exposes "
                            "pattern support, evidence, and implication routes."
                        ),
                    )
                add_resource_brief(seed)
            elif (
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
            elif (
                profile in {"dataset_brief", "deep_lore"}
                and self.expand_iri("rc:Column") in seed_types
            ):
                add_column(seed, None, 0)
            elif (
                profile in {"dataset_brief", "deep_lore"}
                and self.expand_iri("rc:ProfileObservation") in seed_types
            ):
                add_observation(
                    seed,
                    None,
                    0,
                    route="seed_profile_observation",
                    route_label="seed profile observation",
                    expand_observed_dataset=True,
                )
            elif (
                profile in {"dataset_brief", "deep_lore"}
                and self.expand_iri("rc:Observation") in seed_types
            ):
                add_observation(
                    seed,
                    None,
                    0,
                    route="seed_observation",
                    route_label="seed observation",
                    expand_observed_dataset=True,
                )
            elif (
                profile in {"dataset_brief", "deep_lore"}
                and self.expand_iri("rc:ObservedProfileMetric") in seed_types
            ):
                add_profile_metric(seed, None, 0)
            elif seed_is_observed_column_only:
                add_resource(
                    seed,
                    "seed_observed_column",
                    "seed observed column",
                    depth=0,
                )
                for observation_iri in observed_column_profile_observation_iris:
                    add_observation(
                        observation_iri,
                        seed,
                        1,
                        route="seed_profile_observation",
                        route_label="seed profile observation",
                        expand_observed_dataset=True,
                    )
            elif (
                profile in {"dataset_brief", "deep_lore"}
                and observed_value_type_profile_observation_iris
            ):
                add_resource(
                    seed,
                    "seed_observed_value_type",
                    "seed observed value type",
                    depth=0,
                )
                selected_observation_iris = (
                    observed_value_type_profile_observation_iris[:profile_seed_limit]
                )
                omitted_observation_count = len(
                    observed_value_type_profile_observation_iris
                ) - len(selected_observation_iris)
                if omitted_observation_count > 0:
                    warnings.append(
                        "Observed-value-type seed "
                        f"'{seed}' matched "
                        f"{len(observed_value_type_profile_observation_iris)} "
                        "profile observation(s); included "
                        f"{len(selected_observation_iris)} and omitted "
                        f"{omitted_observation_count}. Use a dataset, profile "
                        "observation, or observed column seed for a narrower "
                        "complete handoff."
                    )
                for observation_iri in selected_observation_iris:
                    add_observation(
                        observation_iri,
                        seed,
                        1,
                        route="seed_profile_observation",
                        route_label="seed profile observation",
                        expand_observed_dataset=True,
                    )
            elif (
                profile == "deep_lore"
                and self.expand_iri("rc:GraphRevision") in seed_types
            ):
                add_revision(seed, None, 0)
            elif profile in {"dataset_brief", "deep_lore"} and metric_kind_metric_iris:
                add_resource(
                    seed,
                    "seed_profile_metric_kind",
                    "seed profile metric kind",
                    depth=0,
                )
                selected_metric_iris = metric_kind_metric_iris[:profile_seed_limit]
                omitted_metric_count = len(metric_kind_metric_iris) - len(
                    selected_metric_iris
                )
                if omitted_metric_count > 0:
                    warnings.append(
                        "Metric-kind seed "
                        f"'{seed}' matched {len(metric_kind_metric_iris)} observed "
                        "profile metric(s); included "
                        f"{len(selected_metric_iris)} and omitted "
                        f"{omitted_metric_count}. Use a narrower dataset, profile, "
                        "or observed metric seed for a complete handoff."
                    )
                for metric_iri in selected_metric_iris:
                    add_profile_metric(metric_iri, seed, 1)
            else:
                warnings.append(
                    self._context_slice_profile_mismatch_warning(
                        seed,
                        profile=profile,
                        seed_types=seed_types,
                        metric_kind_metric_iris=metric_kind_metric_iris,
                        observed_value_type_profile_observation_iris=(
                            observed_value_type_profile_observation_iris
                        ),
                    )
                )
                resource_brief_seed_types = {
                    self.expand_iri("rc:Evidence"),
                    self.expand_iri("rc:StorageAccess"),
                    self.expand_iri("rc:PhysicalLayout"),
                    self.expand_iri("rc:PartitionScheme"),
                }
                if (
                    profile != "resource_brief"
                    and set(seed_types) & resource_brief_seed_types
                ):
                    arguments: dict[str, Any] = {
                        "seed_iris": [seed],
                        "profile": "resource_brief",
                        "max_triples": max_triples,
                    }
                    if self.expand_iri("rc:Evidence") in seed_types:
                        action_label = "Retry evidence resource brief"
                        reason = (
                            "The seed is evidence rather than a dataset, "
                            "pattern, claim, observation, or revision. "
                            "resource_brief follows incoming observation and "
                            "profile-observation routes, then can suggest "
                            "describe_profile_run or describe_query_context "
                            "when the evidence belongs to a broader workflow."
                        )
                    else:
                        action_label = "Retry with resource brief"
                        reason = (
                            "The seed is physical/query metadata rather than a "
                            "dataset, pattern, claim, observation, or revision. "
                            "resource_brief follows incoming owner-table routes "
                            "and can then suggest describe_query_context when "
                            "query-planning repair context exists."
                        )
                    add_resource_brief_recovery_action(
                        ("resource_brief_retry", seed),
                        action_label=action_label,
                        tool_name="get_context_graph",
                        arguments=arguments,
                        reason=reason,
                    )

        if profile == "deep_lore":
            self._add_revision_context_for_slice(
                resources,
                all_graphs,
                add_resource,
                add_revision,
            )

        resource_iris = self._context_slice_resource_order(resources, all_lookup_graphs)
        triples, candidate_triple_count = self._context_slice_triples(
            self._context_slice_graphs(profile=profile),
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
        sensitive_literal_count, matches, omitted_match_count = (
            self._context_slice_sensitive_matches(
                triples,
                limit=privacy_scan_limit,
            )
        )
        shareability_hint_count, shareability_hint_matches = (
            self._shareability_hint_matches_for_context_triples(triples)
        )
        shareability_hints = self._shareability_hints_for_context_triples(triples)
        privacy_warnings = self._sensitive_literal_warnings(
            match_count=sensitive_literal_count,
            omitted_match_count=omitted_match_count,
        )
        scanner_note = (
            "Context-slice privacy scan covers only the returned raw triples. "
            "This get_context_graph payload may still contain unredacted "
            "raw triples, TriG, labels, summaries, and project facts; use "
            "preflight_context_slice_export or export_preflight before sharing "
            "or writing handoff artifacts."
            if sensitive_literal_count
            else None
        )
        route_counts = self._context_slice_route_counts(resources)
        if profile == "deep_lore" and not self._context_slice_has_lore_routes(
            route_counts,
        ):
            warnings.append(
                "deep_lore found no claims, patterns, reconsiderations, "
                "evidence, or revision history beyond map context for these seeds."
            )
        warnings.extend(
            self._context_slice_structured_context_warnings(
                resource_count=len(resources),
                dataset_contexts=dataset_contexts.values(),
                truncated=truncated,
            )
        )
        warnings.extend(self._shareability_hint_warnings(shareability_hints))
        warnings.extend(privacy_warnings)
        if scanner_note is not None:
            warnings.append(scanner_note)
        suggested_next_actions = [
            *self._context_slice_privacy_next_actions(
                seed_iris=seeds,
                profile=profile,
                max_triples=max(candidate_triple_count, max_triples)
                if truncated
                else max_triples,
                privacy_scan_limit=privacy_scan_limit,
                sensitive_literal_count=sensitive_literal_count,
                truncated=truncated,
            ),
            *resource_brief_recovery_actions.values(),
            *resource_brief_profile_run_actions.values(),
            *self._context_slice_next_actions(
                seed_iris=seeds,
                profile=profile,
                max_triples=max_triples,
                include_trig=include_trig,
                candidate_triple_count=candidate_triple_count,
                truncated=truncated,
                dataset_contexts=dataset_contexts.values(),
                pattern_contexts=pattern_contexts.values(),
                resources=resources,
                lookup_graphs=all_lookup_graphs,
            ),
        ]

        return ContextSlice(
            profile=profile,
            seeds=[
                self._resource_summary(all_lookup_graphs, seed, display_label=True)
                for seed in seeds
            ],
            reading_order=self._context_slice_reading_order(),
            resources=[
                self._context_slice_resource(
                    iri,
                    routes,
                    all_lookup_graphs,
                    profile=profile,
                )
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
            sensitive_literal_count=sensitive_literal_count,
            returned_match_count=len(matches),
            omitted_match_count=omitted_match_count,
            privacy_scan_limit=privacy_scan_limit,
            matches=matches,
            privacy_warnings=privacy_warnings,
            scanner_note=scanner_note,
            shareability_hints=shareability_hints,
            shareability_hint_count=shareability_hint_count,
            returned_shareability_hint_count=len(shareability_hint_matches),
            omitted_shareability_hint_count=max(
                0,
                shareability_hint_count - len(shareability_hint_matches),
            ),
            shareability_hint_matches=shareability_hint_matches,
            seed_profile_observations=list(seed_profile_observations.values()),
            dataset_contexts=list(dataset_contexts.values()),
            pattern_contexts=list(pattern_contexts.values()),
            warnings=warnings,
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[
                action.call for action in suggested_next_actions
            ],
        )
    def _context_slice_privacy_next_actions(
        self,
        *,
        seed_iris: list[str],
        profile: str,
        max_triples: int,
        privacy_scan_limit: int,
        sensitive_literal_count: int,
        truncated: bool,
    ) -> list[SuggestedNextAction]:
        if sensitive_literal_count == 0:
            return []
        arguments = {
            "seed_iris": seed_iris,
            "profile": profile,
            "max_triples": max_triples,
            "include_seed_graphs": True,
            "limit": privacy_scan_limit,
        }
        truncation_note = (
            " The current slice is truncated, so this action uses the full "
            "candidate triple cap rather than the returned cap."
            if truncated
            else ""
        )
        return [
            SuggestedNextAction(
                action_label="Preflight context-slice privacy",
                tool_name="preflight_context_slice_export",
                mcp_tool_name="doxabase.preflight_context_slice_export",
                arguments=arguments,
                reason=(
                    "Selected raw context-slice triples matched the sensitive-term "
                    "scanner. Use the redacted export preflight before sharing "
                    "slice content or writing an importable handoff artifact."
                    f"{truncation_note}"
                ),
                call=self._suggested_call_string(
                    "preflight_context_slice_export",
                    arguments,
                ),
            )
        ]
    def _context_slice_next_actions(
        self,
        *,
        seed_iris: list[str],
        profile: str,
        max_triples: int,
        include_trig: bool,
        candidate_triple_count: int,
        truncated: bool,
        dataset_contexts: Iterable[DatasetDescription],
        pattern_contexts: Iterable[PatternDescription],
        resources: Mapping[str, list[ContextSliceRoute]],
        lookup_graphs: list[str],
    ) -> list[SuggestedNextAction]:
        actions: list[SuggestedNextAction] = []
        dataset_context_list = list(dataset_contexts)
        dataset_context_by_iri = {
            dataset.iri: dataset for dataset in dataset_context_list
        }

        def add_slice_action(
            arguments: dict[str, Any],
            reason: str,
            *,
            action_label: str,
        ) -> None:
            actions.append(
                SuggestedNextAction(
                    action_label=action_label,
                    tool_name="get_context_graph",
                    mcp_tool_name="doxabase.get_context_graph",
                    arguments=arguments,
                    reason=reason,
                    call=self._suggested_call_string(
                        "get_context_graph",
                        arguments,
                    ),
                )
            )

        seed_iris_set = set(seed_iris)

        def resource_reached_from_seed(
            resource_iri: str,
            routes: Iterable[ContextSliceRoute],
        ) -> bool:
            if resource_iri in seed_iris_set:
                return True
            route_list = list(routes)
            if any(route.source_iri in seed_iris_set for route in route_list):
                return True
            if profile != "resource_brief":
                return False
            return any(
                route.route == "observed_asset"
                and route.source_iri is not None
                and any(
                    observation_route.source_iri in seed_iris_set
                    for observation_route in resources.get(route.source_iri, ())
                )
                for route in route_list
            )

        if profile == "resource_brief":
            dataset_type_iris = {
                self.expand_iri("rc:Dataset"),
                self.expand_iri("rc:Table"),
            }
            for resource_iri, routes in resources.items():
                if resource_iri in dataset_context_by_iri:
                    continue
                if not resource_reached_from_seed(resource_iri, routes):
                    continue
                if not (
                    set(self._types_from_graphs(lookup_graphs, resource_iri))
                    & dataset_type_iris
                ):
                    continue
                try:
                    dataset_context_by_iri[resource_iri] = self.describe_dataset(
                        resource_iri
                    )
                except DoxaBaseError:
                    continue
            dataset_context_list = list(dataset_context_by_iri.values())

        analysis_view_type_iri = self.expand_iri("rc:AnalysisView")
        if profile == "resource_brief":
            seen_analysis_view_iris: set[str] = set()
            for resource_iri, routes in resources.items():
                if resource_iri in seen_analysis_view_iris:
                    continue
                if not resource_reached_from_seed(resource_iri, routes):
                    continue
                if (
                    analysis_view_type_iri
                    not in self._types_from_graphs(lookup_graphs, resource_iri)
                ):
                    continue
                seen_analysis_view_iris.add(resource_iri)
                arguments = {"iri": resource_iri}
                actions.append(
                    SuggestedNextAction(
                        action_label="Inspect analysis view",
                        tool_name="describe_analysis_view",
                        mcp_tool_name="doxabase.describe_analysis_view",
                        arguments=arguments,
                        reason=(
                            "resource_brief reached this rc:AnalysisView from "
                            "the seed. describe_analysis_view exposes its "
                            "logical denominator, source datasets, caveats, and "
                            "query snippets before treating it as a physical "
                            "query route."
                        ),
                        call=self._suggested_call_string(
                            "describe_analysis_view",
                            arguments,
                        ),
                    )
                )

        def dataset_reached_from_seed(dataset_iri: str) -> bool:
            return resource_reached_from_seed(
                dataset_iri,
                resources.get(dataset_iri, ()),
            )

        queryable_owner_iris: set[str] = {
            dataset.iri
            for dataset in dataset_context_list
            if self.expand_iri("rc:Table") in dataset.types
            and dataset_reached_from_seed(dataset.iri)
        }
        metadata_seed_type_iris = {
            self.expand_iri("rc:StorageAccess"),
            self.expand_iri("rc:PhysicalLayout"),
            self.expand_iri("rc:PartitionScheme"),
            self.expand_iri("rc:CompositePartitionScheme"),
        }
        metadata_seed_has_queryable_owner = (
            profile == "resource_brief"
            and any(
                set(self._types_from_graphs(lookup_graphs, seed_iri))
                & metadata_seed_type_iris
                for seed_iri in seed_iris
            )
            and bool(queryable_owner_iris)
        )

        seen_dataset_iris: set[str] = set()
        for dataset in dataset_context_list:
            if not dataset_reached_from_seed(dataset.iri):
                continue
            if dataset.iri in seen_dataset_iris:
                continue
            if self.expand_iri("rc:Table") not in dataset.types:
                continue
            operational_issue_codes = sorted(
                {
                    issue.code
                    for issue in dataset.operational_warnings
                    if issue.severity in {"error", "warning"}
                }
            )
            query_context = self.describe_query_context(dataset.iri)
            repair_issue_codes = sorted(
                {
                    group.issue_code
                    for group in query_context.suggested_repair_action_groups
                }
            )
            issue_codes = sorted(
                {*operational_issue_codes, *repair_issue_codes}
            )
            owner_route_without_issues = (
                metadata_seed_has_queryable_owner
                and dataset.iri in queryable_owner_iris
            )
            if not issue_codes and not owner_route_without_issues:
                continue
            seen_dataset_iris.add(dataset.iri)
            arguments = {"iri": dataset.iri}
            warning_issue_codes = sorted(
                set(operational_issue_codes) - set(repair_issue_codes)
            )
            issue_reason_parts: list[str] = []
            if repair_issue_codes:
                issue_reason_parts.append(
                    "query-planning repair group(s): "
                    f"{', '.join(repair_issue_codes)}"
                )
            if warning_issue_codes:
                issue_reason_parts.append(
                    "operational query-planning warning(s): "
                    f"{', '.join(warning_issue_codes)}"
                )
            if not issue_reason_parts:
                if owner_route_without_issues:
                    owner_count_label = (
                        "a single queryable owner table"
                        if len(queryable_owner_iris) == 1
                        else "multiple queryable owner tables"
                    )
                    issue_reason_parts.append(
                        f"{owner_count_label} reached from storage, layout, "
                        "or partition metadata"
                    )
                else:
                    issue_reason_parts.append(
                        "operational query-planning warning(s): "
                        f"{', '.join(operational_issue_codes)}"
                    )
            actions.append(
                SuggestedNextAction(
                    action_label="Inspect query-planning context",
                    tool_name="describe_query_context",
                    mcp_tool_name="doxabase.describe_query_context",
                    arguments=arguments,
                    reason=(
                        "The seed dataset has "
                        f"{' and '.join(issue_reason_parts)}. "
                        "describe_query_context exposes readiness, target "
                        "candidates, and repair hints before drafting or "
                        "running queries."
                    ),
                    call=self._suggested_call_string(
                        "describe_query_context",
                        arguments,
                    ),
                )
            )

        if not truncated:
            return actions

        seen_pattern_iris: set[str] = set()
        pattern_action_count = 0
        linked_pattern_relevance_ranks = (
            self._context_slice_linked_pattern_relevance_ranks(dataset_context_list)
        )
        sorted_pattern_contexts = sorted(
            pattern_contexts,
            key=lambda pattern_context: self._context_slice_pattern_action_key(
                pattern_context,
                resources=resources,
                lookup_graphs=lookup_graphs,
                linked_pattern_relevance_ranks=linked_pattern_relevance_ranks,
            ),
        )
        for pattern_context in sorted_pattern_contexts:
            if pattern_context.iri in seen_pattern_iris:
                continue
            seen_pattern_iris.add(pattern_context.iri)
            if profile == "pattern_brief":
                continue
            arguments: dict[str, Any] = {
                "seed_iris": [pattern_context.iri],
                "profile": "pattern_brief",
                "max_triples": max_triples,
            }
            add_slice_action(
                arguments,
                (
                    "Raw triples were truncated, but this linked pattern has "
                    "structured context. Rerun around the pattern for a smaller "
                    "pattern-focused handoff before raising max_triples."
                ),
                action_label="Narrow to pattern context",
            )
            pattern_action_count += 1
            if pattern_action_count >= 3:
                break

        full_triple_cap = max(candidate_triple_count, max_triples)
        arguments = {
            "seed_iris": seed_iris,
            "profile": profile,
            "max_triples": full_triple_cap,
        }
        add_slice_action(
            arguments,
            (
                "Use this only when exact raw RDF triples are needed; "
                "structured resources, route counts, and context summaries are "
                "already complete despite the raw triple cap."
            ),
            action_label="Return full raw RDF for slice",
        )
        return actions
    @staticmethod
    def _context_slice_structured_context_warnings(
        *,
        resource_count: int,
        dataset_contexts: Iterable[DatasetDescription],
        truncated: bool,
    ) -> list[str]:
        if not truncated:
            return []
        wide_datasets = [
            dataset
            for dataset in dataset_contexts
            if len(dataset.columns) >= 50
        ]
        details: list[str] = []
        if resource_count >= 100:
            details.append(f"{resource_count} selected resource(s)")
        if wide_datasets:
            dataset_notes = [
                f"{dataset.label or dataset.iri} has {len(dataset.columns)} column(s)"
                for dataset in wide_datasets[:3]
            ]
            if len(wide_datasets) > 3:
                dataset_notes.append(f"{len(wide_datasets) - 3} more wide dataset(s)")
            details.append("; ".join(dataset_notes))
        detail_text = f" ({'; '.join(details)})" if details else ""
        return [
            "Context slice raw RDF was truncated by max_triples, but structured "
            "contexts are still returned in full"
            f"{detail_text}. Use a narrower column, profile, metric, or pattern "
            "seed for a smaller handoff; suggested_next_actions names concrete "
            "pattern seeds when available and raises max_triples only when exact "
            "raw RDF is needed."
        ]
    def _context_slice_graphs(self, *, profile: str | None = None) -> list[str]:
        graphs = [
            "base_ontology",
            "ontology",
            "map",
            "observations",
            "patterns",
            "evidence",
            "history",
        ]
        if profile == "resource_brief":
            graphs.insert(1, "base_shapes")
            graphs.insert(3, "shapes")
        return graphs
    def _context_slice_resource(
        self,
        iri: str,
        routes: list[ContextSliceRoute],
        lookup_graphs: list[str],
        *,
        profile: str | None = None,
    ) -> ContextSliceResource:
        summary = self._resource_summary(lookup_graphs, iri, display_label=True)
        sorted_routes = self._context_slice_sorted_routes(routes)
        graphs = self._graphs_for_subject(
            self._context_slice_graphs(profile=profile),
            iri,
        )
        return ContextSliceResource(
            iri=iri,
            label=summary.label,
            description=summary.description,
            types=self._types_from_graphs(lookup_graphs, iri),
            graphs=graphs,
            surface_role=self._context_slice_surface_role(graphs),
            referenced_only=not graphs,
            primary_route=sorted_routes[0],
            routes=sorted_routes,
        )
    @staticmethod
    def _context_slice_surface_role(graphs: Iterable[str]) -> str:
        role_by_graph = DoxaBase._context_slice_surface_role_by_graph()
        roles = {
            role_by_graph[graph]
            for graph in graphs
            if graph in role_by_graph
        }
        if not roles:
            return "referenced_only"
        if len(roles) == 1:
            return next(iter(roles))
        return "mixed_context"
    @staticmethod
    def _context_slice_surface_role_by_graph() -> dict[str, str]:
        return {
            "base_ontology": "vocabulary_context",
            "base_shapes": "validation_shape_context",
            "ontology": "vocabulary_context",
            "shapes": "validation_shape_context",
            "map": "current_map_context",
            "observations": "observation_context",
            "patterns": "pattern_synthesis",
            "evidence": "evidence_support",
            "history": "revision_history",
        }
    @staticmethod
    def _context_slice_surface_roles_for_graphs(
        graphs: Iterable[str],
    ) -> list[str]:
        role_by_graph = DoxaBase._context_slice_surface_role_by_graph()
        return sorted(
            {
                role_by_graph[graph]
                for graph in graphs
                if graph in role_by_graph
            }
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
            "seed_column": 2,
            "seed_observed_column": 2,
            "seed_observed_value_type": 2,
            "seed_revision": 2,
            "linked_pattern": 2,
            "resource_type": 3,
            "outgoing_reference": 4,
            "blank_node_reference": 5,
            "incoming_reference": 6,
            "incoming_blank_node_owner": 7,
            "blank_node_seed_owner": 7,
            "predicate_usage_subject": 8,
            "pattern_target": 3,
            "map_implication": 4,
            "dataset_column": 5,
            "known_caveat": 6,
            "dataset_relationship": 7,
            "relationship_endpoint": 8,
            "relationship_endpoint_dataset": 9,
            "related_dataset_reason": 8,
            "related_dataset": 9,
            "related_column": 9,
            "supporting_claim": 10,
            "claim_reconsideration": 11,
            "incoming_claim_reconsideration": 11,
            "reconsidered_claim": 12,
            "reconsidering_claim": 12,
            "supporting_observation": 13,
            "dataset_observation": 13,
            "dataset_profile_observation": 13,
            "column_profile_observation": 13,
            "unmapped_column_profile_observation": 13,
            "seed_observation": 13,
            "seed_profile_observation": 13,
            "profile_metric_observation": 13,
            "observed_profile_metric": 14,
            "observed_value_frequency": 14,
            "applied_revision": 14,
            "applies_staged_revision": 14,
            "restaged_from_revision": 14,
            "restaged_by_revision": 14,
            "alternative_revision": 14,
            "revision_anchor": 14,
            "revision_anchor_match": 14,
            "profile_metric_kind": 15,
            "profile_metric_target": 15,
            "seed_profile_metric_kind": 15,
            "evidence": 16,
            "source_span": 17,
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
            "dataset_observation",
            "dataset_profile_observation",
            "column_profile_observation",
            "unmapped_column_profile_observation",
            "seed_observation",
            "seed_profile_observation",
            "profile_metric_observation",
            "observed_profile_metric",
            "observed_value_frequency",
            "seed_revision",
            "applied_revision",
            "applies_staged_revision",
            "restaged_from_revision",
            "restaged_by_revision",
            "alternative_revision",
            "revision_anchor",
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
            "Check warnings for caps, broad seeds, or missing lore before relying on the slice.",
            (
                "Read dataset_contexts, pattern_contexts, and "
                "seed_profile_observations for compact structured context."
            ),
            "Scan route_counts and route_legend to understand why resources were included.",
            (
                "Use reading_order, route_counts, and route_legend as the route "
                "summary surface; there is no separate route_summaries field."
            ),
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
            "seed_column": "A seed resource expanded as a mapped column.",
            "seed_observed_column": (
                "A seed IRI found only as an observed column in profile observations."
            ),
            "seed_observed_value_type": (
                "A seed IRI found as an observed value type in profile observations."
            ),
            "seed_revision": "A seed resource expanded as revision-history metadata.",
            "resource_type": "A direct rdf:type resource attached to a resource-brief seed.",
            "outgoing_reference": "A URI resource directly referenced by a resource-brief seed.",
            "blank_node_reference": (
                "A URI resource reached through bounded outgoing blank-node closure from a resource-brief seed."
            ),
            "incoming_reference": "A URI subject that directly references a resource-brief seed.",
            "incoming_blank_node_owner": (
                "A URI subject that owns a blank node which references a resource-brief seed."
            ),
            "blank_node_seed_owner": (
                "A URI subject reached by walking from a blank-node resource-brief seed through parent blank nodes."
            ),
            "predicate_usage_subject": "A URI subject using a resource-brief seed as an RDF predicate.",
            "related_column": (
                "A column reached from a selected column seed or lore route."
            ),
            "linked_pattern": (
                "A selected or dataset-linked pattern included for surrounding lore."
            ),
            "pattern_target": "A resource the selected pattern is about.",
            "map_implication": "A map resource or assertion the selected pattern may affect.",
            "dataset_column": "A column belonging to a selected dataset.",
            "known_caveat": "A caveat attached to a selected dataset.",
            "dataset_relationship": "A relationship attached to a selected dataset.",
            "relationship_endpoint": (
                "A structured source or target endpoint attached to a selected dataset relationship."
            ),
            "relationship_endpoint_dataset": (
                "A dataset named by a structured relationship endpoint."
            ),
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
            "dataset_observation": (
                "A bounded ordinary observation that names a selected dataset as its observed asset."
            ),
            "seed_observation": "A seed resource expanded as an ordinary observation.",
            "dataset_profile_observation": (
                "A bounded dataset-level profile observation returned by the selected dataset context."
            ),
            "column_profile_observation": (
                "A bounded column-level profile observation returned by the selected dataset context."
            ),
            "unmapped_column_profile_observation": (
                "A bounded profile observation for a column not currently mapped on the selected dataset."
            ),
            "seed_profile_observation": "A seed resource expanded as a profile observation.",
            "profile_metric_observation": (
                "A profile observation reached from a selected observed profile metric."
            ),
            "observed_asset": "A dataset or asset named by a selected observation.",
            "observed_column": "A column named by a selected observation.",
            "observed_profile_metric": "A scalar metric node attached to a selected profile observation.",
            "observed_value_frequency": "An observed value-frequency node attached to a selected profile observation.",
            "profile_metric_kind": "The metric-kind IRI used by an observed profile metric.",
            "profile_metric_target": "The narrower target resource named by an observed profile metric.",
            "seed_profile_metric_kind": "A seed IRI used as a profile metric kind.",
            "applied_revision": (
                "An applied revision event that applied a selected staged revision."
            ),
            "applies_staged_revision": (
                "The staged revision applied by a selected applied revision event."
            ),
            "restaged_from_revision": (
                "The earlier staged revision replayed by a selected restaged revision."
            ),
            "restaged_by_revision": (
                "A later staged revision that restages a selected stale revision."
            ),
            "alternative_revision": "A revision recorded as an alternative to a selected revision.",
            "revision_anchor": "A resource named as an anchor for a selected revision.",
            "revision_anchor_match": (
                "A revision reached because a selected resource is one of its anchors."
            ),
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
    def _context_slice_sensitive_matches(
        self,
        triples: Iterable[ResourceTriple],
        *,
        limit: int,
    ) -> tuple[int, list[SensitiveLiteralMatch], int]:
        matches: list[SensitiveLiteralMatch] = []
        omitted = 0
        for triple in triples:
            term_values: list[tuple[str, str, str]] = []
            if triple.subject_kind == "uri":
                term_values.append(("subject", triple.subject_kind, triple.subject))
            term_values.append(("predicate", "uri", triple.predicate))
            if triple.object_kind in {"literal", "uri"}:
                term_values.append(("object", triple.object_kind, triple.object))
            for term_position, term_kind, value in term_values:
                match_kind, redacted_snippet = self._sensitive_literal_match(value)
                if match_kind is None or redacted_snippet is None:
                    continue
                if len(matches) < limit:
                    matches.append(
                        SensitiveLiteralMatch(
                            graph=triple.graph,
                            subject=self._redact_sensitive_context_value(
                                triple.subject
                            ),
                            predicate=self._redact_sensitive_context_value(
                                triple.predicate
                            ),
                            object_kind=triple.object_kind,
                            term_position=term_position,
                            term_kind=term_kind,
                            match_kind=match_kind,
                            redacted_snippet=redacted_snippet,
                        )
                    )
                else:
                    omitted += 1
        return len(matches) + omitted, matches, omitted
