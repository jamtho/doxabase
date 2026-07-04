"""Profile map-update drafting, planning, and staging.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via ProfilePromotionMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class ProfilePromotionMixin:
    def draft_profile_map_updates(
        self,
        dataset_iri: str,
        evidence_iri: str,
        *,
        graph: str | None = "map",
        known_pending_staged_profile_update_iris: Iterable[str] | None = None,
    ) -> ProfileMapUpdateDraft:
        dataset_value = self._required_iri("dataset_iri", dataset_iri)
        evidence_value = self._required_iri("evidence_iri", evidence_iri)
        data_graphs = self._expand_graphs([graph] if graph else None)
        map_dataset_found = self._subject_exists(dataset_value, data_graphs)
        dataset_description = (
            self.describe_dataset(dataset_value, graph=graph)
            if map_dataset_found
            else None
        )
        profile_run = self.describe_profile_run(
            dataset_value,
            evidence_value,
            graph=graph,
        )
        columns_by_iri = (
            {column.iri: column for column in dataset_description.columns}
            if dataset_description is not None
            else {}
        )

        recommendations: list[ProfileMapUpdateRecommendation] = []
        current_equal_scalar_values: dict[
            tuple[str, str, str, str],
            list[Any],
        ] = {}
        for profile in profile_run.dataset_profile_observations:
            if profile.row_count is None:
                continue
            if (
                dataset_description is not None
                and not self._dataset_description_is_table(dataset_description)
            ):
                continue
            current_row_count = (
                dataset_description.row_count_snapshot
                if dataset_description is not None
                else None
            )
            if current_row_count == profile.row_count:
                self._profile_update_add_scalar_observed_value(
                    current_equal_scalar_values,
                    evidence_iri=evidence_value,
                    resource_iri=profile_run.dataset.iri,
                    predicate="rc:rowCountSnapshot",
                    kind="dataset_row_count_snapshot",
                    observed_value=profile.row_count,
                )
                continue
            basis = self._profile_observation_basis(profile)
            action = (
                "record_map_value"
                if current_row_count is None
                else "replace_map_value"
            )
            recommendations.append(
                ProfileMapUpdateRecommendation(
                    recommendation_index=len(recommendations),
                    kind="dataset_row_count_snapshot",
                    action=action,
                    resource=profile_run.dataset,
                    predicate="rc:rowCountSnapshot",
                    current_value=current_row_count,
                    observed_value=profile.row_count,
                    observed_count=profile.row_count,
                    sample_size=profile.sample_size,
                    sample_scope=profile.sample_scope,
                    sample_method=profile.sample_method,
                    profile_row_count=profile.row_count,
                    profile_observation_iri=profile.iri,
                    evidence_iri=evidence_value,
                    basis=basis,
                    confidence="high" if basis == "full_scan" else "medium",
                    helper_name="record_map_dataset",
                    helper_arguments={
                        "iri": dataset_value,
                        "row_count_snapshot": profile.row_count,
                    },
                    rationale=(
                        "Profile row_count differs from the current map "
                        "row-count snapshot; review before recording the "
                        "profile value as current map context."
                        if map_dataset_found
                        else "No current map dataset was found; review the "
                        "profile scope before recording this intentionally "
                        "thin dataset shell with a row-count snapshot."
                    ),
                )
            )

        for profile in profile_run.mapped_column_profile_observations:
            if profile.null_count is None or profile.observed_column is None:
                continue
            column = columns_by_iri.get(profile.observed_column.iri)
            if column is None:
                continue
            observed_nullable = profile.null_count > 0
            basis = self._profile_observation_basis(profile)
            if not observed_nullable and basis != "full_scan":
                continue
            if column.nullable == observed_nullable:
                self._profile_update_add_scalar_observed_value(
                    current_equal_scalar_values,
                    evidence_iri=evidence_value,
                    resource_iri=profile.observed_column.iri,
                    predicate="rc:nullable",
                    kind="column_nullable",
                    observed_value=observed_nullable,
                )
                continue
            column_name = self._profile_map_column_name(column, profile)
            action = (
                "record_map_value"
                if column.nullable is None
                else "replace_map_value"
            )
            recommendations.append(
                ProfileMapUpdateRecommendation(
                    recommendation_index=len(recommendations),
                    kind="column_nullable",
                    action=action,
                    resource=profile.observed_column,
                    predicate="rc:nullable",
                    current_value=column.nullable,
                    observed_value=observed_nullable,
                    observed_count=profile.null_count,
                    sample_size=profile.sample_size,
                    sample_scope=profile.sample_scope,
                    sample_method=profile.sample_method,
                    profile_row_count=profile.row_count,
                    profile_observation_iri=profile.iri,
                    evidence_iri=evidence_value,
                    basis=basis,
                    confidence=(
                        "high" if basis == "full_scan" else "medium"
                    ),
                    helper_name="record_map_column",
                    helper_arguments={
                        "iri": column.iri,
                        "table_iri": dataset_value,
                        "column_name": column_name,
                        "nullable": observed_nullable,
                    },
                    rationale=(
                        "Profile null_count implies a different nullable "
                        "value than the current map column. Sampled zero-null "
                        "profiles are not promoted; positive null findings and "
                        "full-scan zero-null findings are review candidates."
                    ),
                )
            )

        for profile in profile_run.unmapped_column_profile_observations:
            if profile.observed_column is None:
                continue
            column_name = self._profile_observed_column_name(profile)
            if not column_name:
                continue
            basis = self._profile_observation_basis(profile)
            recommendations.append(
                ProfileMapUpdateRecommendation(
                    recommendation_index=len(recommendations),
                    kind="unmapped_profiled_column",
                    action="add_map_column_shell",
                    resource=profile.observed_column,
                    predicate="rc:hasColumn",
                    current_value=None,
                    observed_value=column_name,
                    observed_count=profile.row_count,
                    sample_size=profile.sample_size,
                    sample_scope=profile.sample_scope,
                    sample_method=profile.sample_method,
                    profile_row_count=profile.row_count,
                    profile_observation_iri=profile.iri,
                    evidence_iri=evidence_value,
                    basis=basis,
                    confidence="medium" if basis == "full_scan" else "low",
                    helper_name="record_map_column",
                    helper_arguments={
                        "iri": profile.observed_column.iri,
                        "table_iri": dataset_value,
                        "column_name": column_name,
                    },
                    rationale=(
                        "The profile run observed a column that is not mapped "
                        "as a current column. The draft only proposes a column "
                        "shell because observed type findings need separate "
                        "semantic review before becoming map type facts."
                        if map_dataset_found
                        else "No current map dataset was found; this draft "
                        "proposes only a thin column shell under the profiled "
                        "asset because observed type findings need separate "
                        "semantic review before becoming map type facts."
                    ),
                )
            )

        all_profiles = [
            *profile_run.dataset_profile_observations,
            *profile_run.mapped_column_profile_observations,
            *profile_run.unmapped_column_profile_observations,
        ]
        metric_advisories = self._profile_metric_vocabulary_advisories(
            all_profiles,
            evidence_value,
        )
        type_advisories = self._profile_type_finding_advisories(
            all_profiles,
            evidence_value,
            columns_by_iri=columns_by_iri,
            recommendations=recommendations,
        )
        metric_advisories, type_advisories = (
            self._with_profile_advisory_mixed_support(
                metric_advisories,
                type_advisories,
            )
        )
        recommendations = self._with_profile_update_default_staging_metadata(
            recommendations,
            current_equal_scalar_values=current_equal_scalar_values,
        )
        recommendations = self._with_profile_update_duplicate_metadata(
            recommendations
        )
        profile_quality_summary = self._profile_quality_summary(
            recommendations,
            metric_advisory_count=len(metric_advisories),
            type_advisory_count=len(type_advisories),
        )
        sampled_evidence_caution = self._profile_sampled_evidence_caution(
            profile_quality_summary
        )
        representative_recommendation_indexes = (
            self._profile_update_representative_indexes(recommendations)
        )
        representative_metric_advisory_indexes = (
            self._profile_advisory_representative_indexes(metric_advisories)
        )
        representative_type_advisory_indexes = (
            self._profile_advisory_representative_indexes(type_advisories)
        )
        default_stageable_representative_indexes = [
            index
            for index in representative_recommendation_indexes
            if recommendations[index].default_stageable
        ]
        metric_advisory_status_counts = (
            self._profile_metric_advisory_status_counts(metric_advisories)
        )
        type_advisory_status_counts = self._profile_type_advisory_status_counts(
            type_advisories
        )
        scalar_conflict_groups = self._profile_update_scalar_conflict_groups(
            recommendations,
            dataset_iri=dataset_value,
            evidence_iri=evidence_value,
            current_equal_scalar_values=current_equal_scalar_values,
        )
        profile_supporting_pattern_iris = (
            self._profile_map_update_supporting_pattern_iris(
                profile_run,
                recommendations=recommendations,
                type_advisories=type_advisories,
            )
        )
        query_context_review_actions = (
            self._profile_query_context_review_actions(
                dataset_description,
                graph=graph,
                evidence_iri=evidence_value,
                profile_quality_summary=profile_quality_summary,
                sampled_evidence_caution=sampled_evidence_caution,
            )
            if dataset_description is not None
            else []
        )
        pending_staged_profile_update_iris = (
            list(known_pending_staged_profile_update_iris)
            if known_pending_staged_profile_update_iris is not None
            else self._pending_staged_profile_update_iris(
                dataset_value,
                evidence_value,
            )
        )
        pending_staged_profile_update_count = len(
            pending_staged_profile_update_iris
        )
        suggested_next_action_groups = (
            self._profile_map_update_draft_action_groups(
                dataset_iri=dataset_value,
                evidence_iri=evidence_value,
                query_context_review_actions=query_context_review_actions,
                pending_staged_profile_update_iris=(
                    pending_staged_profile_update_iris
                ),
                recommendations=recommendations,
                default_stageable_representative_indexes=(
                    default_stageable_representative_indexes
                ),
                scalar_conflict_groups=scalar_conflict_groups,
                supporting_patterns=profile_supporting_pattern_iris,
                metric_advisories=metric_advisories,
                type_advisories=type_advisories,
            )
        )
        metric_advisories = self._profile_metric_advisories_with_source_actions(
            metric_advisories
        )
        type_advisories = self._profile_type_advisories_with_source_actions(
            type_advisories
        )
        suggested_next_actions = (
            self._profile_map_update_draft_actions_from_groups(
                suggested_next_action_groups
            )
        )
        status = self._profile_map_update_draft_status(
            pending_staged_profile_update_count=(
                pending_staged_profile_update_count
            ),
            recommendation_count=len(recommendations),
            scalar_conflict_group_count=len(scalar_conflict_groups),
            metric_advisory_count=len(metric_advisories),
            metric_advisory_status_counts=metric_advisory_status_counts,
            type_advisory_count=len(type_advisories),
        )
        return ProfileMapUpdateDraft(
            dataset=profile_run.dataset,
            evidence=profile_run.evidence,
            evidence_iri=evidence_value,
            map_dataset_found=map_dataset_found,
            status=status,
            pending_staged_profile_update_iris=(
                pending_staged_profile_update_iris
            ),
            pending_staged_profile_update_count=(
                pending_staged_profile_update_count
            ),
            profile_observation_iris=profile_run.profile_observation_iris,
            recommendations=recommendations,
            recommendation_count=len(recommendations),
            representative_recommendation_indexes=representative_recommendation_indexes,
            profile_quality_summary=profile_quality_summary,
            sampled_evidence_caution=sampled_evidence_caution,
            scalar_conflict_groups=scalar_conflict_groups,
            scalar_conflict_group_count=len(scalar_conflict_groups),
            metric_advisories=metric_advisories,
            metric_advisory_count=len(metric_advisories),
            representative_metric_advisory_indexes=(
                representative_metric_advisory_indexes
            ),
            metric_advisory_status_counts=metric_advisory_status_counts,
            type_advisories=type_advisories,
            type_advisory_count=len(type_advisories),
            representative_type_advisory_indexes=(
                representative_type_advisory_indexes
            ),
            type_advisory_status_counts=type_advisory_status_counts,
            suggested_next_actions=suggested_next_actions,
            suggested_next_action_groups=suggested_next_action_groups,
            review_note=(
                self._profile_map_update_draft_review_note(
                    query_context_review_actions=query_context_review_actions,
                    pending_staged_profile_update_iris=(
                        pending_staged_profile_update_iris
                    ),
                )
            ),
        )
    def plan_profile_followthrough(
        self,
        dataset_iri: str,
        evidence_iri: str,
        *,
        graph: str | None = "map",
        result_bindings: Mapping[str, Any] | None = None,
        staged_revision_iris: Iterable[str] | str | None = None,
        restage_stale_revisions: bool = False,
    ) -> ProfileFollowthroughPlan:
        draft = self.draft_profile_map_updates(
            dataset_iri=dataset_iri,
            evidence_iri=evidence_iri,
            graph=graph,
        )
        binding_values = {
            str(key): value for key, value in dict(result_bindings or {}).items()
        }
        action_resolutions: list[ProfileFollowthroughActionResolution] = []
        binding_resolutions: list[ProfileFollowthroughBindingResolution] = []

        for group_name, actions in draft.suggested_next_action_groups.items():
            for action_index, action in enumerate(actions):
                (
                    resolved_action,
                    action_binding_resolutions,
                ) = self._profile_followthrough_resolve_action_bindings(
                    action,
                    result_bindings=binding_values,
                    action_group=group_name,
                    action_index=action_index,
                )
                binding_resolutions.extend(action_binding_resolutions)
                applied_binding_keys = [
                    resolution.binding_key
                    for resolution in action_binding_resolutions
                    if resolution.status == "resolved"
                ]
                missing_binding_keys = [
                    resolution.binding_key
                    for resolution in action_binding_resolutions
                    if resolution.status == "missing"
                ]
                if missing_binding_keys:
                    binding_status = "missing_bindings"
                elif applied_binding_keys:
                    binding_status = "resolved"
                else:
                    binding_status = "not_applicable"
                semantic_move = self._profile_action_semantic_move(action)
                action_resolutions.append(
                    ProfileFollowthroughActionResolution(
                        action_group=group_name,
                        action_index=action_index,
                        tool=resolved_action.tool,
                        semantic_move=semantic_move,
                        binding_status=binding_status,
                        applied_binding_keys=applied_binding_keys,
                        missing_binding_keys=missing_binding_keys,
                        action=resolved_action,
                    )
                )

        revision_checks = self._profile_followthrough_revision_checks(
            staged_revision_iris,
            restage_stale_revisions=restage_stale_revisions,
        )
        restaged_revision_iris = [
            check.restaged_revision_iri
            for check in revision_checks
            if check.restaged_revision_iri is not None
        ]
        action_resolution_groups = (
            self._profile_followthrough_action_resolution_groups(
                action_resolutions,
                pending_map_update_iris=(
                    draft.pending_staged_profile_update_iris
                ),
            )
        )
        suggested_next_action_groups = (
            self._profile_followthrough_suggested_next_action_groups(
                action_resolutions,
                revision_checks=revision_checks,
                pending_map_update_iris=(
                    draft.pending_staged_profile_update_iris
                ),
            )
        )
        suggested_next_actions = [
            resolution.action
            for resolution in action_resolutions
            if resolution.binding_status != "missing_bindings"
            and not self._profile_followthrough_pending_map_update_review(
                resolution,
                pending_map_update_iris=(
                    draft.pending_staged_profile_update_iris
                ),
            )
        ]
        for check in revision_checks:
            suggested_next_actions.extend(check.suggested_next_actions)
        profile_type_assertion_batch_plan = (
            self._profile_type_assertion_batch_plan(action_resolutions)
        )
        missing_binding_keys = sorted(
            {
                resolution.binding_key
                for resolution in binding_resolutions
                if resolution.status == "missing"
            }
        )
        return ProfileFollowthroughPlan(
            result_kind="profile_followthrough_plan",
            dataset=draft.dataset,
            evidence=draft.evidence,
            evidence_iri=draft.evidence_iri,
            graph=graph,
            draft=draft,
            result_binding_keys=sorted(binding_values),
            binding_resolution_count=len(binding_resolutions),
            binding_resolutions=binding_resolutions,
            action_resolutions=action_resolutions,
            action_resolution_groups=action_resolution_groups,
            resolved_action_count=sum(
                1
                for resolution in action_resolutions
                if resolution.binding_status == "resolved"
            ),
            missing_binding_keys=missing_binding_keys,
            missing_binding_action_count=sum(
                1
                for resolution in action_resolutions
                if resolution.binding_status == "missing_bindings"
            ),
            revision_checks=revision_checks,
            revision_check_count=len(revision_checks),
            restage_stale_revisions=restage_stale_revisions,
            restaged_revision_iris=restaged_revision_iris,
            suggested_next_actions=suggested_next_actions,
            suggested_next_action_groups=suggested_next_action_groups,
            profile_type_assertion_batch_plan=profile_type_assertion_batch_plan,
            review_note=(
                "Rerun the profile map-update draft through this coordinator after "
                "recording profile-support patterns or applying related staged "
                "revisions. It resolves route-scoped result bindings into "
                "structured action arguments and can recheck/restage supplied "
                "sibling staged revisions, but it does not apply reviewable "
                "graph changes."
            ),
        )
    def stage_profile_map_updates(
        self,
        dataset_iri: str,
        evidence_iri: str,
        *,
        accepted_recommendation_indexes: Iterable[int] | None,
        graph: TypingLiteral["map"] = "map",
        allow_sampled_row_count_updates: bool = False,
        allow_pending_profile_updates: bool = False,
        summary: str | None = None,
        rationale: str | None = None,
        created_at: datetime | str | None = None,
        created_by: str | None = None,
        supporting_claims: Iterable[str] | str | None = None,
        supporting_patterns: Iterable[str] | str | None = None,
        revision_anchors: Iterable[str] | str | None = None,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ] = "all",
    ) -> ProfileMapUpdateStagingRecord:
        if graph != "map":
            raise DoxaBaseError(
                "stage_revision kind='profile_map_updates' currently targets "
                "map only"
            )
        accepted_indexes = self._profile_update_accepted_indexes(
            accepted_recommendation_indexes,
        )
        draft = self.draft_profile_map_updates(
            dataset_iri=dataset_iri,
            evidence_iri=evidence_iri,
            graph=graph,
        )
        if (
            draft.pending_staged_profile_update_iris
            and not allow_pending_profile_updates
        ):
            pending = ", ".join(draft.pending_staged_profile_update_iris[:3])
            raise DoxaBaseError(
                "stage_revision kind='profile_map_updates' found pending "
                "staged profile map update(s) for the same dataset/evidence "
                "pair: "
                f"{pending}. Review them with plan_staged_revision_recovery "
                "or pass allow_pending_profile_updates=True only after "
                "confirming another staged profile update is intentional."
            )
        supporting_pattern_values = self._string_values(
            "supporting_patterns",
            supporting_patterns,
        )
        recommendations = draft.recommendations
        out_of_range = [
            index for index in accepted_indexes if index >= len(recommendations)
        ]
        if out_of_range:
            raise DoxaBaseError(
                "accepted_recommendation_indexes out of range: "
                + ", ".join(str(index) for index in out_of_range)
            )

        accepted_index_set = set(accepted_indexes)
        selected_conflict_skip_reasons = (
            self._profile_update_scalar_conflict_skip_reasons(
                recommendations,
                selected_indexes=accepted_index_set,
            )
        )
        additions_graph = Graph()
        removals_graph = Graph()
        self._bind_prefixes(additions_graph)
        self._bind_prefixes(removals_graph)
        staged_indexes: list[int] = []
        skipped_indexes: list[int] = []
        not_selected_indexes: list[int] = []
        items: list[ProfileMapUpdateStagingItem] = []
        support_observations: list[str] = []
        profile_revision_anchors: list[str] = [draft.dataset.iri]

        for index, recommendation in enumerate(recommendations):
            status = "not_selected"
            reason: str | None = "Recommendation index was not accepted by caller."
            supporting_profile_observation_iris = (
                recommendation.duplicate_profile_observation_iris
                or [recommendation.profile_observation_iri]
            )
            if index in accepted_index_set:
                reason = selected_conflict_skip_reasons.get(index)
                if (
                    reason is None
                    and self._profile_update_current_equal_conflict_skip_reason(
                        recommendation.default_skip_reason
                    )
                ):
                    reason = recommendation.default_skip_reason
                if reason is None:
                    reason = self._profile_update_skip_reason(
                        recommendation,
                        allow_sampled_row_count_updates=(
                            allow_sampled_row_count_updates
                        ),
                    )
                if reason is None:
                    self._add_profile_update_patch_triples(
                        recommendation,
                        dataset_iri=draft.dataset.iri,
                        map_dataset_found=draft.map_dataset_found,
                        additions_graph=additions_graph,
                        removals_graph=removals_graph,
                    )
                    status = "staged"
                    staged_indexes.append(index)
                    support_observations.extend(supporting_profile_observation_iris)
                    for anchor in self._profile_update_revision_anchors(
                        recommendation,
                        dataset_iri=draft.dataset.iri,
                    ):
                        profile_revision_anchors.append(anchor)
                else:
                    status = "skipped"
                    skipped_indexes.append(index)
            else:
                not_selected_indexes.append(index)

            items.append(
                ProfileMapUpdateStagingItem(
                    recommendation_index=index,
                    kind=recommendation.kind,
                    action=recommendation.action,
                    resource=recommendation.resource,
                    status=status,
                    reason=reason,
                    basis=recommendation.basis,
                    confidence=recommendation.confidence,
                    sample_size=recommendation.sample_size,
                    sample_scope=recommendation.sample_scope,
                    sample_method=recommendation.sample_method,
                    profile_observation_iri=recommendation.profile_observation_iri,
                    supporting_profile_observation_iris=(
                        supporting_profile_observation_iris
                    ),
                )
            )

        status_counts = self._profile_update_status_counts(items)
        additions: list[dict[str, str]] = []
        removals: list[dict[str, str]] = []
        if len(additions_graph) > 0:
            additions.append(
                {
                    "graph": "map",
                    "content": additions_graph.serialize(format="turtle").strip(),
                }
            )
        if len(removals_graph) > 0:
            removals.append(
                {
                    "graph": "map",
                    "content": removals_graph.serialize(format="turtle").strip(),
                }
            )

        staged_revision: StagedGraphRevisionRecord | None = None
        if additions or removals:
            dataset_label = draft.dataset.label or self._local_name(draft.dataset.iri)
            staged_revision = self.stage_graph_revision(
                summary=summary
                or f"Stage profile map updates for {dataset_label}",
                rationale=rationale
                or (
                    "Accepted profile map-update recommendations from "
                    "the profile map-update draft and grouped them into one "
                    "reviewable map revision so helper-equivalent shells and "
                    "scalar updates can be applied together after review."
                ),
                additions=additions,
                removals=removals,
                created_at=created_at,
                created_by=created_by,
                supporting_observations=list(dict.fromkeys(support_observations)),
                supporting_claims=self._merge_iri_values(supporting_claims, []),
                supporting_patterns=self._merge_iri_values(
                    supporting_pattern_values,
                    [],
                ),
                evidence=[draft.evidence_iri],
                revision_anchors=self._merge_iri_values(
                    revision_anchors,
                    profile_revision_anchors,
                ),
                review_note=self._profile_update_staging_review_note(
                    items,
                    staged_indexes=staged_indexes,
                    skipped_indexes=skipped_indexes,
                    status_counts=status_counts,
                    metric_advisory_count=draft.metric_advisory_count,
                    metric_advisory_status_counts=(
                        draft.metric_advisory_status_counts
                    ),
                    type_advisory_count=draft.type_advisory_count,
                    type_advisory_status_counts=draft.type_advisory_status_counts,
                    allow_sampled_row_count_updates=allow_sampled_row_count_updates,
                ),
                review_recommendation=(
                    "Review staged profile-derived map changes, especially "
                    "sample scope, before applying; review any metric "
                    "vocabulary advisories separately before reusing them."
                ),
                validation_scope=validation_scope,
            )
            route_sources = self._profile_map_update_staging_route_sources(
                draft,
                staged_indexes=staged_indexes,
                supporting_patterns=supporting_pattern_values,
            )
            extra_triples = self._record_profile_insight_route_sources(
                staged_revision.revision_iri,
                route_sources,
            )
            if extra_triples:
                staged_revision = replace(
                    staged_revision,
                    triples=staged_revision.triples + extra_triples,
                )

        suggested_next_actions = self._profile_update_staging_actions(
            staged_revision,
            items=items,
            dataset_iri=draft.dataset.iri,
            evidence_iri=draft.evidence_iri,
        )
        metric_advisory_suggested_next_actions = (
            self._profile_metric_advisory_suggested_actions(
                draft.metric_advisories,
            )
        )
        type_advisory_suggested_next_actions = (
            self._profile_type_advisory_suggested_actions(
                draft.type_advisories,
            )
        )
        return ProfileMapUpdateStagingRecord(
            result_kind="profile_map_update_staging",
            dataset=draft.dataset,
            evidence=draft.evidence,
            evidence_iri=draft.evidence_iri,
            map_dataset_found=draft.map_dataset_found,
            recommendation_count=len(recommendations),
            accepted_recommendation_indexes=accepted_indexes,
            staged_recommendation_indexes=staged_indexes,
            skipped_recommendation_indexes=skipped_indexes,
            not_selected_recommendation_indexes=not_selected_indexes,
            status_counts=status_counts,
            items=items,
            metric_advisories=draft.metric_advisories,
            metric_advisory_count=draft.metric_advisory_count,
            metric_advisory_status_counts=draft.metric_advisory_status_counts,
            metric_vocabulary_review_required=bool(
                metric_advisory_suggested_next_actions
            ),
            metric_advisory_suggested_next_actions=(
                metric_advisory_suggested_next_actions
            ),
            type_advisories=draft.type_advisories,
            type_advisory_count=draft.type_advisory_count,
            type_advisory_status_counts=draft.type_advisory_status_counts,
            type_review_required=bool(type_advisory_suggested_next_actions),
            type_advisory_suggested_next_actions=(
                type_advisory_suggested_next_actions
            ),
            revision_iri=(
                staged_revision.revision_iri
                if staged_revision is not None
                else None
            ),
            staged_revision=staged_revision,
            suggested_next_actions=suggested_next_actions,
            review_note=self._profile_update_staging_review_note(
                items,
                staged_indexes=staged_indexes,
                skipped_indexes=skipped_indexes,
                status_counts=status_counts,
                metric_advisory_count=draft.metric_advisory_count,
                metric_advisory_status_counts=draft.metric_advisory_status_counts,
                type_advisory_count=draft.type_advisory_count,
                type_advisory_status_counts=draft.type_advisory_status_counts,
                allow_sampled_row_count_updates=allow_sampled_row_count_updates,
            ),
        )
    def _profile_map_update_draft_profile_map_actions(
        self,
        *,
        dataset_iri: str,
        evidence_iri: str,
        recommendations: list[ProfileMapUpdateRecommendation],
        default_stageable_representative_indexes: list[int],
        supporting_patterns: list[str],
        pending_staged_profile_update_iris: list[str],
    ) -> list[SuggestedNextAction]:
        actions: list[SuggestedNextAction] = []
        if pending_staged_profile_update_iris:
            actions.append(
                self._profile_map_update_pending_staged_action(
                    dataset_iri=dataset_iri,
                    evidence_iri=evidence_iri,
                    recommendations=recommendations,
                    recommendation_indexes=default_stageable_representative_indexes,
                    supporting_patterns=supporting_patterns,
                    pending_staged_profile_update_iris=(
                        pending_staged_profile_update_iris
                    ),
                )
            )
        if (
            default_stageable_representative_indexes
            and not pending_staged_profile_update_iris
        ):
            action = self._profile_map_update_stage_action(
                dataset_iri=dataset_iri,
                evidence_iri=evidence_iri,
                recommendation_indexes=default_stageable_representative_indexes,
                supporting_patterns=supporting_patterns,
                pending_staged_profile_update_iris=(
                    pending_staged_profile_update_iris
                ),
            )
            actions.append(action)

        return actions
