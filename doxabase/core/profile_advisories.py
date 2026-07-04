"""Profile advisory actions and vocabulary suggestions.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via ProfileAdvisoriesMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class ProfileAdvisoriesMixin:
    @staticmethod
    def _profile_advisory_semantic_move(
        action: SuggestedNextAction,
        source_profile_advisory: MappingABC[str, Any],
    ) -> str | None:
        explicit_move = source_profile_advisory.get("semantic_move")
        if isinstance(explicit_move, str):
            return explicit_move
        review_lane = source_profile_advisory.get("review_lane")
        if action.tool == "doxabase.stage_systematisation":
            return "caveat_fallback"
        if review_lane == "metric_vocabulary_review":
            return "define_metric"
        if review_lane != "profile_type_review":
            return None
        current_map_undefined_value_type_only = (
            DoxaBase._profile_advisory_status_set(source_profile_advisory)
            == {"type_finding_current_map_undefined_value_type"}
        )
        if action.tool == "doxabase.stage_pattern_promotion":
            return "define_value_type"
        if action.tool == "doxabase.describe_pattern":
            return "define_value_type"
        if action.tool == "doxabase.stage_map_assertion_change":
            return "assert_map_type"
        if action.tool == "doxabase.get_context_graph":
            if current_map_undefined_value_type_only:
                return None
            return "assert_map_type"
        if action.tool == "doxabase.record_pattern":
            return "caveat_fallback"
        return None
    @staticmethod
    def _profile_advisory_status_set(
        source_profile_advisory: MappingABC[str, Any],
    ) -> set[str]:
        statuses = source_profile_advisory.get("advisory_statuses")
        if not isinstance(statuses, list):
            return set()
        return {status for status in statuses if isinstance(status, str)}
    @staticmethod
    def _profile_scalar_conflict_suggested_actions(
        scalar_conflict_groups: list[ProfileScalarConflictGroup],
    ) -> list[SuggestedNextAction]:
        return [
            option.suggested_next_action
            for group in scalar_conflict_groups
            for option in group.options
        ]
    @staticmethod
    def _profile_scalar_conflict_route_source_items(
        scalar_conflict_groups: list[ProfileScalarConflictGroup],
    ) -> list[tuple[SuggestedNextAction, dict[str, Any]]]:
        items: list[tuple[SuggestedNextAction, dict[str, Any]]] = []
        for group in scalar_conflict_groups:
            route_group_key = DoxaBase._profile_route_group_key(
                "profile_scalar_conflict_review",
                {
                    "evidence_iri": group.evidence_iri,
                    "resource_iri": group.resource.iri,
                    "predicate": group.predicate,
                    "kind": group.kind,
                },
            )
            for option_index, option in enumerate(group.options):
                action = option.suggested_next_action
                selection_rule = (
                    "current_value_already_chosen_review_before_replacing"
                    if action.tool != "doxabase.stage_profile_map_updates"
                    else "choose_at_most_one_option_per_conflict_group"
                )
                route_source = DoxaBase._with_profile_route_step_key(
                    {
                        "review_lane": "profile_scalar_conflict_review",
                        "route_group_key": route_group_key,
                        "selection_rule": selection_rule,
                        "conflict_group_index": group.conflict_group_index,
                        "evidence_iri": group.evidence_iri,
                        "resource_iri": group.resource.iri,
                        "resource_label": group.resource.label,
                        "predicate": group.predicate,
                        "kind": group.kind,
                        "current_value": group.current_value,
                        "option_index": option_index,
                        "option_count": group.option_count,
                        "observed_value": option.observed_value,
                        "representative_recommendation_index": (
                            option.representative_recommendation_index
                        ),
                        "recommendation_indexes": (
                            option.recommendation_indexes
                        ),
                        "duplicate_recommendation_indexes": (
                            option.duplicate_recommendation_indexes
                        ),
                        "duplicate_profile_observation_iris": (
                            option.duplicate_profile_observation_iris
                        ),
                        "recommendation_contexts": to_jsonable(
                            option.recommendation_contexts
                        ),
                        "review_note": group.review_note,
                    },
                    action,
                )
                items.append((action, route_source))
        return items
    @staticmethod
    def _profile_scalar_conflict_staging_route_sources(
        draft: ProfileMapUpdateDraft,
        *,
        staged_indexes: list[int],
    ) -> list[dict[str, Any]]:
        staged_index_set = set(staged_indexes)
        sources: list[dict[str, Any]] = []
        for _, route_source in (
            DoxaBase._profile_scalar_conflict_route_source_items(
                draft.scalar_conflict_groups
            )
        ):
            option_index_set = {
                index
                for index in route_source.get("recommendation_indexes") or []
                if isinstance(index, int) and not isinstance(index, bool)
            }
            if not staged_index_set.intersection(option_index_set):
                continue
            route_source = dict(route_source)
            route_source["direct_review_lane"] = (
                "profile_scalar_conflict_review"
            )
            sources.append(route_source)
        return sources
    @staticmethod
    def _profile_advisory_representative_indexes(
        advisories: Iterable[
            ProfileMetricVocabularyAdvisory | ProfileTypeFindingAdvisory
        ],
    ) -> list[int]:
        representatives: list[int] = []
        seen_group_keys: set[str] = set()
        for index, advisory in enumerate(advisories):
            group_key = advisory.duplicate_group_key or f"advisory:{index}"
            if group_key in seen_group_keys:
                continue
            seen_group_keys.add(group_key)
            representatives.append(index)
        return representatives
    @staticmethod
    def _profile_update_scalar_conflict_skip_reasons(
        recommendations: list[ProfileMapUpdateRecommendation],
        *,
        selected_indexes: set[int] | None = None,
        current_equal_scalar_values: Mapping[
            tuple[str, str, str, str],
            Iterable[Any],
        ]
        | None = None,
    ) -> dict[int, str]:
        groups = DoxaBase._profile_update_scalar_conflict_value_groups(
            recommendations,
            selected_indexes=selected_indexes,
            current_equal_scalar_values=current_equal_scalar_values,
        )

        skip_reasons: dict[int, str] = {}
        for (_evidence_iri, resource_iri, predicate, _kind), value_groups in (
            groups.items()
        ):
            if len(value_groups) <= 1:
                continue
            value_labels = sorted(
                str(group["label"]) for group in value_groups.values()
            )
            has_current_equal_value = any(
                bool(group["current_equal_count"])
                for group in value_groups.values()
            )
            if has_current_equal_value:
                reason = (
                    "Same-evidence profile observations include conflicting "
                    f"values for scalar map assertion {predicate} on "
                    f"{resource_iri}: {', '.join(value_labels)}. One value "
                    "already matches the current map; review the profile "
                    "observations before staging another replacement."
                )
            else:
                reason = (
                    "Same-evidence profile recommendations propose conflicting "
                    f"values for scalar map assertion {predicate} on "
                    f"{resource_iri}: {', '.join(value_labels)}. Review the "
                    "profile observations and choose one observed value "
                    "explicitly before staging."
                )
            for group in value_groups.values():
                for recommendation in group["recommendations"]:
                    skip_reasons[recommendation.recommendation_index] = reason
        return skip_reasons
    @staticmethod
    def _profile_update_scalar_conflict_value_groups(
        recommendations: list[ProfileMapUpdateRecommendation],
        *,
        selected_indexes: set[int] | None = None,
        current_equal_scalar_values: Mapping[
            tuple[str, str, str, str],
            Iterable[Any],
        ]
        | None = None,
    ) -> dict[tuple[str, str, str, str], dict[str, dict[str, Any]]]:
        groups: dict[tuple[str, str, str, str], dict[str, dict[str, Any]]] = {}

        def add_value(
            group_key: tuple[str, str, str, str],
            observed_value: Any,
            *,
            recommendation: ProfileMapUpdateRecommendation | None = None,
            current_equal: bool = False,
        ) -> None:
            value_key = DoxaBase._profile_update_scalar_value_key(observed_value)
            value_group = groups.setdefault(group_key, {}).setdefault(
                value_key,
                {
                    "label": DoxaBase._profile_update_scalar_value_label(
                        observed_value
                    ),
                    "recommendations": [],
                    "current_equal_count": 0,
                },
            )
            if recommendation is not None:
                value_group["recommendations"].append(recommendation)
            if current_equal:
                value_group["current_equal_count"] += 1

        for recommendation in recommendations:
            if (
                selected_indexes is not None
                and recommendation.recommendation_index not in selected_indexes
            ):
                continue
            if recommendation.kind not in PROFILE_SCALAR_MAP_UPDATE_KINDS:
                continue
            group_key = (
                recommendation.evidence_iri,
                recommendation.resource.iri,
                recommendation.predicate,
                recommendation.kind,
            )
            add_value(
                group_key,
                recommendation.observed_value,
                recommendation=recommendation,
            )

        for group_key, observed_values in (
            current_equal_scalar_values or {}
        ).items():
            for observed_value in observed_values:
                add_value(group_key, observed_value, current_equal=True)

        return groups
    def _profile_update_scalar_conflict_groups(
        self,
        recommendations: list[ProfileMapUpdateRecommendation],
        *,
        dataset_iri: str,
        evidence_iri: str,
        current_equal_scalar_values: Mapping[
            tuple[str, str, str, str],
            Iterable[Any],
        ]
        | None = None,
    ) -> list[ProfileScalarConflictGroup]:
        groups = self._profile_update_scalar_conflict_value_groups(
            recommendations,
            current_equal_scalar_values=current_equal_scalar_values,
        )

        conflict_groups: list[ProfileScalarConflictGroup] = []
        for (_group_evidence_iri, _resource_iri, predicate, kind), value_groups in (
            groups.items()
        ):
            if len(value_groups) <= 1:
                continue
            visible_value_groups = [
                group
                for group in value_groups.values()
                if group["recommendations"]
            ]
            if not visible_value_groups:
                continue
            first_recommendation = visible_value_groups[0]["recommendations"][0]
            has_current_equal_value = any(
                bool(group["current_equal_count"])
                for group in value_groups.values()
            )
            options: list[ProfileScalarConflictOption] = []
            for value_group in sorted(
                visible_value_groups,
                key=lambda group: min(
                    recommendation.recommendation_index
                    for recommendation in group["recommendations"]
                ),
            ):
                recommendations_for_value = value_group["recommendations"]
                representative = recommendations_for_value[0]
                recommendation_indexes = [
                    recommendation.recommendation_index
                    for recommendation in recommendations_for_value
                ]
                duplicate_recommendation_indexes = list(
                    dict.fromkeys(
                        index
                        for recommendation in recommendations_for_value
                        for index in (
                            recommendation.duplicate_recommendation_indexes
                            or [recommendation.recommendation_index]
                        )
                    )
                )
                duplicate_profile_observation_iris = list(
                    dict.fromkeys(
                        observation_iri
                        for recommendation in recommendations_for_value
                        for observation_iri in (
                            recommendation.duplicate_profile_observation_iris
                            or [recommendation.profile_observation_iri]
                        )
                    )
                )
                recommendation_contexts = [
                    ProfileScalarConflictRecommendationContext(
                        recommendation_index=recommendation.recommendation_index,
                        profile_observation_iri=(
                            recommendation.profile_observation_iri
                        ),
                        observed_count=recommendation.observed_count,
                        sample_size=recommendation.sample_size,
                        sample_scope=recommendation.sample_scope,
                        sample_method=recommendation.sample_method,
                        profile_row_count=recommendation.profile_row_count,
                        basis=recommendation.basis,
                        confidence=recommendation.confidence,
                    )
                    for recommendation in recommendations_for_value
                ]
                if has_current_equal_value:
                    arguments = {
                        "dataset_iri": dataset_iri,
                        "evidence_iri": evidence_iri,
                    }
                    action = SuggestedNextAction(
                                 tool="doxabase.describe_profile_run",
                                 args=arguments,
                                 reason="A same-evidence scalar conflict has an option "
                            "that already matches the current map. Review the "
                            "profile run and route history before staging "
                            "another replacement.",
                             )
                else:
                    arguments = {
                        "dataset_iri": dataset_iri,
                        "evidence_iri": evidence_iri,
                        "accepted_recommendation_indexes": [
                            representative.recommendation_index
                        ],
                    }
                    action = SuggestedNextAction(
                                 tool="doxabase.stage_profile_map_updates",
                                 args=arguments,
                                 reason="This same-evidence scalar conflict is not "
                            "default-stageable. Use this action only after "
                            "reviewing the conflicting profile observations and "
                            "choosing this observed value for the current map "
                            "assertion.",
                             )
                options.append(
                    ProfileScalarConflictOption(
                        observed_value=representative.observed_value,
                        representative_recommendation_index=(
                            representative.recommendation_index
                        ),
                        recommendation_indexes=recommendation_indexes,
                        duplicate_recommendation_indexes=(
                            duplicate_recommendation_indexes
                        ),
                        duplicate_profile_observation_iris=(
                            duplicate_profile_observation_iris
                        ),
                        recommendation_contexts=recommendation_contexts,
                        suggested_next_action=action,
                    )
                )
            conflict_groups.append(
                ProfileScalarConflictGroup(
                    conflict_group_index=len(conflict_groups),
                    evidence_iri=evidence_iri,
                    resource=first_recommendation.resource,
                    predicate=predicate,
                    kind=kind,
                    current_value=first_recommendation.current_value,
                    option_count=len(options),
                    options=options,
                    review_note=(
                        (
                            "Same-evidence profile observations include "
                            "multiple values for this scalar map assertion, "
                            "and one value already matches the current map. "
                            "Do not stage another replacement until route "
                            "history and supporting observations have been "
                            "reviewed."
                        )
                        if has_current_equal_value
                        else (
                            "Same-evidence profile recommendations propose "
                            "multiple values for this scalar map assertion. "
                            "These options stay out of default "
                            "profile_map_updates; choose at most one option "
                            "after reviewing the supporting profile "
                            "observations."
                        )
                    ),
                )
            )
        return conflict_groups
    def _profile_metric_advisory_suggested_actions(
        self,
        metric_advisories: list[ProfileMetricVocabularyAdvisory],
    ) -> list[SuggestedNextAction]:
        return self._profile_advisory_suggested_actions(
            metric_advisories,
            advisory_kind="metric_vocabulary_review",
            index_field="metric_advisory_index",
        )
    def _profile_metric_advisories_with_source_actions(
        self,
        metric_advisories: list[ProfileMetricVocabularyAdvisory],
    ) -> list[ProfileMetricVocabularyAdvisory]:
        updated: list[ProfileMetricVocabularyAdvisory] = []
        for advisory in metric_advisories:
            actions = self._profile_advisory_row_suggested_actions(
                advisory,
                advisory_kind="metric_vocabulary_review",
                index_field="metric_advisory_index",
            )
            updated.append(
                replace(
                    advisory,
                    suggested_next_actions=actions,
                )
            )
        return updated
    @staticmethod
    def _profile_metric_advisory_status_counts(
        advisories: Iterable[ProfileMetricVocabularyAdvisory],
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for advisory in advisories:
            counts[advisory.advisory_status] = (
                counts.get(advisory.advisory_status, 0) + 1
            )
        return counts
    @staticmethod
    def _profile_type_advisory_status_counts(
        advisories: Iterable[ProfileTypeFindingAdvisory],
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for advisory in advisories:
            counts[advisory.advisory_status] = (
                counts.get(advisory.advisory_status, 0) + 1
            )
        return counts
    @staticmethod
    def _profile_metric_advisory_review_summary(
        advisory_count: int,
        status_counts: dict[str, int],
    ) -> str:
        if advisory_count == 0:
            return "none"
        status_summary = ", ".join(
            f"{status}={count}" for status, count in status_counts.items()
        )
        return f"{advisory_count} ({status_summary})"
    @staticmethod
    def _profile_type_advisory_review_summary(
        advisory_count: int,
        status_counts: dict[str, int],
    ) -> str:
        if advisory_count == 0:
            return "none"
        status_summary = ", ".join(
            f"{status}={count}" for status, count in status_counts.items()
        )
        return f"{advisory_count} ({status_summary})"
    def _query_repair_action_group_advisories(
        self,
        issue: QueryPlanningIssue,
    ) -> list[dict[str, Any]]:
        if issue.details is None:
            return []
        fixture_hint = issue.details.get("fixture_staleness_hint")
        if not isinstance(fixture_hint, MappingABC):
            return []
        hint_type = fixture_hint.get("hint_type")
        if hint_type != "known_fixture_tables_without_storage_accesses":
            return []
        project_brief_action = {
            "tool": "doxabase.project_brief",
            "args": {},
            "reason": (
                "Known AIS or Polymarket fixture tables are present without "
                "storage access metadata; review the grouped health task before "
                "staging individual query repairs."
            ),
        }
        return [
            {
                "code": "query_fixture_staleness_review",
                "severity": "warning",
                "source": "issue.details.fixture_staleness_hint",
                "hint_type": hint_type,
                "recommended_handling": "review_fixture_staleness_before_staging",
                "suppression_policy": "review_group_before_member_mutation",
                "reason": fixture_hint.get("message"),
                "suggested_next_action": project_brief_action,
                "fixture_names": list(fixture_hint.get("fixture_names") or []),
                "known_fixture_table_iris": list(
                    fixture_hint.get("known_fixture_table_iris") or []
                ),
                "dataset_matches_known_fixture": bool(
                    fixture_hint.get("dataset_matches_known_fixture")
                ),
                "storage_access_count": fixture_hint.get(
                    "global_storage_access_count"
                ),
            }
        ]
    def _profile_type_finding_advisories(
        self,
        profiles: list[ProfileObservationSummary],
        evidence_iri: str,
        *,
        columns_by_iri: dict[str, ColumnDescription],
        recommendations: list[ProfileMapUpdateRecommendation],
    ) -> list[ProfileTypeFindingAdvisory]:
        advisories: list[ProfileTypeFindingAdvisory] = []
        for profile in profiles:
            if profile.observed_column is None:
                continue
            if (
                profile.observed_physical_type is None
                and profile.observed_value_type is None
            ):
                continue
            column = columns_by_iri.get(profile.observed_column.iri)
            current_physical_type = column.physical_type if column is not None else None
            current_value_type = column.value_type if column is not None else None
            matches_current_map = (
                column is not None
                and self._profile_type_finding_matches_current_map(
                    profile,
                    current_physical_type=current_physical_type,
                    current_value_type=current_value_type,
                )
            )
            current_map_undefined_value_type = (
                matches_current_map
                and profile.observed_value_type is not None
                and self._profile_value_type_needs_ontology_skeleton(
                    profile.observed_value_type.iri
                )
            )
            if matches_current_map and not current_map_undefined_value_type:
                continue
            advisory_status = self._profile_type_advisory_status(
                profile,
                map_column_found=column is not None,
                current_physical_type=current_physical_type,
                current_value_type=current_value_type,
                current_map_undefined_value_type=(
                    current_map_undefined_value_type
                ),
            )
            related_recommendations = (
                self._profile_type_related_recommendations(
                    profile,
                    recommendations,
                    advisory_status=advisory_status,
                )
            )
            related_recommendation_indexes = [
                recommendation.recommendation_index
                for recommendation in related_recommendations
            ]
            related_recommendation_kinds = list(
                dict.fromkeys(
                    recommendation.kind for recommendation in related_recommendations
                )
            )
            value_type_promotion_pattern_iris = (
                self._profile_value_type_promotion_pattern_iris(
                    value_type_iri=profile.observed_value_type.iri,
                    evidence_iri=evidence_iri,
                )
                if profile.observed_value_type is not None
                and self._profile_value_type_needs_ontology_skeleton(
                    profile.observed_value_type.iri
                )
                else []
            )
            suggested_next_actions = self._profile_type_advisory_actions(
                profile=profile,
                evidence_iri=evidence_iri,
                advisory_status=advisory_status,
                map_column_found=column is not None,
                current_physical_type=current_physical_type,
                current_value_type=current_value_type,
                value_type_promotion_pattern_iris=(
                    value_type_promotion_pattern_iris
                ),
            )
            advisories.append(
                ProfileTypeFindingAdvisory(
                    profile_observation_iri=profile.iri,
                    type_advisory_index=len(advisories),
                    evidence_iri=evidence_iri,
                    observed_column=profile.observed_column,
                    observed_column_name=profile.observed_column_name,
                    observed_physical_type=profile.observed_physical_type,
                    observed_value_type=profile.observed_value_type,
                    map_column_found=column is not None,
                    current_physical_type=current_physical_type,
                    current_value_type=current_value_type,
                    promotion_patterns=self._resource_summaries(
                        self._lookup_graphs(["patterns"]),
                        value_type_promotion_pattern_iris,
                    ),
                    promotion_pattern_count=len(value_type_promotion_pattern_iris),
                    mixed_support_patterns=[],
                    mixed_support_pattern_count=0,
                    mixed_support_note=None,
                    advisory_status=advisory_status,
                    recommendation="review_profile_type_finding_before_map_update",
                    rationale=self._profile_type_advisory_rationale(
                        profile,
                        advisory_status=advisory_status,
                    ),
                    routing_note=self._profile_type_advisory_routing_note(
                        advisory_status,
                        related_recommendation_indexes=(
                            related_recommendation_indexes
                        ),
                        related_recommendation_kinds=related_recommendation_kinds,
                    ),
                    related_recommendation_indexes=related_recommendation_indexes,
                    related_recommendation_kinds=related_recommendation_kinds,
                    suggested_next_actions=suggested_next_actions,
                )
            )
        return self._with_profile_type_pending_staged_metadata(
            self._with_profile_type_advisory_duplicate_metadata(advisories)
        )
    @staticmethod
    def _profile_type_finding_matches_current_map(
        profile: ProfileObservationSummary,
        *,
        current_physical_type: ResourceSummary | None,
        current_value_type: ResourceSummary | None,
    ) -> bool:
        if (
            profile.observed_physical_type is not None
            and (
                current_physical_type is None
                or current_physical_type.iri != profile.observed_physical_type.iri
            )
        ):
            return False
        if (
            profile.observed_value_type is not None
            and (
                current_value_type is None
                or current_value_type.iri != profile.observed_value_type.iri
            )
        ):
            return False
        return True
    def _profile_type_advisory_status(
        self,
        profile: ProfileObservationSummary,
        *,
        map_column_found: bool,
        current_physical_type: ResourceSummary | None,
        current_value_type: ResourceSummary | None,
        current_map_undefined_value_type: bool = False,
    ) -> str:
        if not map_column_found:
            return "type_finding_unmapped_column"
        if current_map_undefined_value_type:
            return "type_finding_current_map_undefined_value_type"
        conflicts = False
        missing = False
        if profile.observed_physical_type is not None:
            if current_physical_type is None:
                missing = True
            elif current_physical_type.iri != profile.observed_physical_type.iri:
                conflicts = True
        if profile.observed_value_type is not None:
            if current_value_type is None:
                missing = True
            elif current_value_type.iri != profile.observed_value_type.iri:
                conflicts = True
        if conflicts:
            return "type_finding_conflicts_current_map"
        if missing:
            return "type_finding_missing_map_type"
        return "type_finding_needs_review"
    def _with_profile_type_advisory_duplicate_metadata(
        self,
        advisories: list[ProfileTypeFindingAdvisory],
    ) -> list[ProfileTypeFindingAdvisory]:
        groups: dict[str, list[tuple[int, ProfileTypeFindingAdvisory]]] = {}
        for index, advisory in enumerate(advisories):
            groups.setdefault(
                self._profile_type_advisory_duplicate_group_key(advisory),
                [],
            ).append((index, advisory))

        annotated: list[ProfileTypeFindingAdvisory] = []
        for index, advisory in enumerate(advisories):
            group_key = self._profile_type_advisory_duplicate_group_key(advisory)
            group = groups[group_key]
            duplicate_advisory_indexes = [group_index for group_index, _ in group]
            duplicate_profile_observation_iris = list(
                dict.fromkeys(item.profile_observation_iri for _, item in group)
            )
            related_recommendation_indexes = list(
                dict.fromkeys(
                    recommendation_index
                    for _, item in group
                    for recommendation_index in item.related_recommendation_indexes
                )
            )
            related_recommendation_kinds = list(
                dict.fromkeys(
                    recommendation_kind
                    for _, item in group
                    for recommendation_kind in item.related_recommendation_kinds
                )
            )
            suggested_next_actions = (
                self._profile_type_advisory_actions_with_duplicate_support(
                    advisory.suggested_next_actions,
                    duplicate_profile_observation_iris,
                )
            )
            annotated.append(
                replace(
                    advisory,
                    type_advisory_index=index,
                    duplicate_group_key=group_key,
                    duplicate_count=len(group),
                    duplicate_advisory_indexes=duplicate_advisory_indexes,
                    duplicate_profile_observation_iris=(
                        duplicate_profile_observation_iris
                    ),
                    related_recommendation_indexes=related_recommendation_indexes,
                    related_recommendation_kinds=related_recommendation_kinds,
                    routing_note=self._profile_type_advisory_routing_note(
                        advisory.advisory_status,
                        related_recommendation_indexes=(
                            related_recommendation_indexes
                        ),
                        related_recommendation_kinds=related_recommendation_kinds,
                    ),
                    suggested_next_actions=suggested_next_actions,
                )
            )
        return annotated
    def _profile_type_advisory_actions_with_duplicate_support(
        self,
        actions: list[SuggestedNextAction],
        duplicate_profile_observation_iris: list[str],
    ) -> list[SuggestedNextAction]:
        if not duplicate_profile_observation_iris:
            return actions
        updated_actions: list[SuggestedNextAction] = []
        for action in actions:
            arguments = dict(action.args)
            if action.tool == "doxabase.get_context_graph":
                seed_iris = list(arguments.get("seed_iris") or [])
                arguments["seed_iris"] = list(
                    dict.fromkeys(
                        [*duplicate_profile_observation_iris, *seed_iris]
                    )
                )
            elif action.tool in {
                "doxabase.record_pattern",
                "doxabase.stage_map_assertion_change",
                "doxabase.stage_systematisation",
            }:
                arguments["supporting_observations"] = (
                    duplicate_profile_observation_iris
                )
                if action.tool == "doxabase.stage_systematisation":
                    anchors = list(arguments.get("anchors") or [])
                    arguments["anchors"] = list(
                        dict.fromkeys(
                            [*duplicate_profile_observation_iris, *anchors]
                        )
                    )
                    framings = []
                    for framing in arguments.get("framings") or []:
                        if not isinstance(framing, MappingABC):
                            framings.append(framing)
                            continue
                        updated_framing = dict(framing)
                        content = updated_framing.get("content")
                        if isinstance(content, str):
                            updated_framing["content"] = (
                                self._profile_fallback_pattern_turtle_with_supporting_observations(
                                    content,
                                    duplicate_profile_observation_iris,
                                )
                            )
                        framings.append(updated_framing)
                    arguments["framings"] = framings
                if (
                    action.tool == "doxabase.stage_map_assertion_change"
                    and len(duplicate_profile_observation_iris) > 1
                ):
                    arguments["rationale"] = (
                        "Duplicate profile observations "
                        f"{', '.join(duplicate_profile_observation_iris)} "
                        f"recorded {arguments.get('predicate')} "
                        f"{arguments.get('object')} for "
                        f"{arguments.get('subject')}. Treat this as a "
                        "candidate map assertion and review current context "
                        "before applying."
                    )
            else:
                updated_actions.append(action)
                continue
            updated_actions.append(replace(action, args=arguments))
        return updated_actions
    @staticmethod
    def _profile_type_advisory_duplicate_group_key(
        advisory: ProfileTypeFindingAdvisory,
    ) -> str:
        payload = {
            "evidence_iri": advisory.evidence_iri,
            "observed_column_iri": advisory.observed_column.iri,
            "observed_column_name": advisory.observed_column_name,
            "observed_physical_type_iri": (
                advisory.observed_physical_type.iri
                if advisory.observed_physical_type is not None
                else None
            ),
            "observed_value_type_iri": (
                advisory.observed_value_type.iri
                if advisory.observed_value_type is not None
                else None
            ),
            "map_column_found": advisory.map_column_found,
            "current_physical_type_iri": (
                advisory.current_physical_type.iri
                if advisory.current_physical_type is not None
                else None
            ),
            "current_value_type_iri": (
                advisory.current_value_type.iri
                if advisory.current_value_type is not None
                else None
            ),
            "advisory_status": advisory.advisory_status,
            "related_recommendation_kinds": advisory.related_recommendation_kinds,
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:12]
        return f"profile-type-advisory:{digest}"
    def _profile_type_advisory_suggested_actions(
        self,
        advisories: list[ProfileTypeFindingAdvisory],
    ) -> list[SuggestedNextAction]:
        return self._profile_advisory_suggested_actions(
            advisories,
            advisory_kind="profile_type_review",
            index_field="type_advisory_index",
        )
    def _profile_type_advisories_with_source_actions(
        self,
        type_advisories: list[ProfileTypeFindingAdvisory],
    ) -> list[ProfileTypeFindingAdvisory]:
        updated: list[ProfileTypeFindingAdvisory] = []
        for advisory in type_advisories:
            actions = self._profile_advisory_row_suggested_actions(
                advisory,
                advisory_kind="profile_type_review",
                index_field="type_advisory_index",
            )
            updated.append(
                replace(
                    advisory,
                    suggested_next_actions=actions,
                )
            )
        return updated
    def _profile_type_advisory_actions(
        self,
        *,
        profile: ProfileObservationSummary,
        evidence_iri: str,
        advisory_status: str,
        map_column_found: bool,
        current_physical_type: ResourceSummary | None,
        current_value_type: ResourceSummary | None,
        value_type_promotion_pattern_iris: list[str],
    ) -> list[SuggestedNextAction]:
        assert profile.observed_column is not None
        actions: list[SuggestedNextAction] = []

        def add_action(
            tool_name: str,
            arguments: dict[str, Any],
            reason: str,
        ) -> None:
            actions.append(
                SuggestedNextAction(
                    tool=f"doxabase.{tool_name}",
                    args=arguments,
                    reason=reason,
                )
            )

        type_implication_iris = [
            profile.observed_column.iri,
            *(
                [profile.observed_physical_type.iri]
                if profile.observed_physical_type is not None
                else []
            ),
            *(
                [profile.observed_value_type.iri]
                if profile.observed_value_type is not None
                else []
            ),
        ]
        seed_iris = [
            profile.iri,
            profile.observed_column.iri,
            *self._profile_type_existing_type_seed_iris(profile),
        ]
        if advisory_status == "type_finding_current_map_undefined_value_type":
            context_reason = (
                "Load bounded lore around the profile observation, column, "
                "and current value-type resource before reviewing the "
                "undefined project value-type vocabulary."
            )
        else:
            context_reason = (
                "Load bounded lore around the profile observation, column, and "
                "observed type resources before turning the type finding into "
                "a current map assertion."
            )
        add_action(
            "get_context_graph",
            {
                "seed_iris": list(dict.fromkeys(seed_iris)),
                "profile": "dataset_brief",
            },
            context_reason,
        )
        column_label = (
            profile.observed_column.label
            or profile.observed_column.column_name
            or profile.observed_column_name
            or profile.observed_column.iri
        )
        add_action(
            "record_pattern",
            {
                "summary": f"Review profiled type for {column_label}",
                "pattern_text": (
                    f"Profile evidence observed type information for {column_label}. "
                    "Treat it as interpretation evidence until reviewed against "
                    "current map context and value-type semantics."
                ),
                "rationale": (
                    "Profile type findings are evidence, not automatic map "
                    "updates. Preserve the judgement before staging a map "
                    "assertion or systematisation."
                ),
                "pattern_targets": [profile.observed_column.iri],
                "supporting_observations": [profile.iri],
                "evidence_iri": evidence_iri,
                "map_implications": list(dict.fromkeys(type_implication_iris)),
            },
            (
                "Record a synthesis if this type finding needs semantic review "
                "before becoming a durable map assertion."
            ),
        )
        add_action(
            "stage_systematisation",
            self._profile_type_fallback_systematisation_arguments(
                profile=profile,
                evidence_iri=evidence_iri,
                type_implication_iris=type_implication_iris,
                column_label=column_label,
            ),
            (
                "Stage a reviewable pattern fallback if this type finding "
                "needs semantic review before any current map assertion."
            ),
        )
        pattern_carry_forward_note = (
            " If you used the suggested record_pattern action, add its returned "
            "pattern_iri to supporting_patterns on this staging call."
        )
        if value_type_promotion_pattern_iris:
            for pattern_iri in value_type_promotion_pattern_iris[:3]:
                add_action(
                    "describe_pattern",
                    {"iri": pattern_iri},
                    (
                        "Inspect the same-evidence pattern before promoting "
                        "this project value type into ontology vocabulary."
                    ),
                )
            add_action(
                "stage_pattern_promotion",
                self._profile_value_type_promotion_skeleton_arguments(
                    value_type_iri=profile.observed_value_type.iri,
                    pattern_iris=value_type_promotion_pattern_iris,
                    evidence_iri=evidence_iri,
                ),
                (
                    "Stage a reviewable ontology skeleton for this project "
                    "value type only after checking that the same-evidence "
                    "pattern captures its domain meaning and physical-type "
                    "expectations."
                ),
            )

        if map_column_found:
            if (
                profile.observed_physical_type is not None
                and (
                    current_physical_type is None
                    or current_physical_type.iri
                    != profile.observed_physical_type.iri
                )
            ):
                add_action(
                    "stage_map_assertion_change",
                    self._profile_type_assertion_action_arguments(
                        profile=profile,
                        evidence_iri=evidence_iri,
                        predicate="rc:physicalType",
                        object_iri=profile.observed_physical_type.iri,
                        advisory_status=advisory_status,
                    ),
                    (
                        "Stage a reviewable physical-type assertion only after "
                        "checking the profile evidence and value-type context."
                        f"{pattern_carry_forward_note}"
                    ),
                )
            if (
                profile.observed_value_type is not None
                and (
                    current_value_type is None
                    or current_value_type.iri != profile.observed_value_type.iri
                )
            ):
                value_type_supporting_patterns = (
                    value_type_promotion_pattern_iris
                )
                value_type_support_note = (
                    " Existing same-evidence value-type promotion patterns "
                    "are prefilled in supporting_patterns."
                    if value_type_supporting_patterns
                    else pattern_carry_forward_note
                )
                add_action(
                    "stage_map_assertion_change",
                    self._profile_type_assertion_action_arguments(
                        profile=profile,
                        evidence_iri=evidence_iri,
                        predicate="rc:valueType",
                        object_iri=profile.observed_value_type.iri,
                        advisory_status=advisory_status,
                        supporting_patterns=value_type_supporting_patterns,
                    ),
                    (
                        "Stage a reviewable value-type assertion only after "
                        "checking the profile evidence and domain semantics."
                        f"{value_type_support_note}"
                    ),
                )
        return actions
    @staticmethod
    def _profile_type_advisory_rationale(
        profile: ProfileObservationSummary,
        *,
        advisory_status: str,
    ) -> str:
        if profile.observed_column is not None:
            column_label = (
                profile.observed_column.label
                or profile.observed_column.column_name
                or profile.observed_column_name
                or profile.observed_column.iri
            )
        else:
            column_label = "the observed column"
        if advisory_status == "type_finding_unmapped_column":
            return (
                f"The profile observed type information for {column_label}, "
                "but the column is not a current map column. Preserve or stage "
                "the interpretation with a column shell or systematisation "
                "before recording current map type facts."
            )
        if advisory_status == "type_finding_conflicts_current_map":
            return (
                f"The profile observed type information for {column_label} that "
                "differs from current map type facts. Review semantic risk and "
                "value-type context before replacing current assertions."
            )
        if advisory_status == "type_finding_missing_map_type":
            return (
                f"The profile observed type information for {column_label} where "
                "the current map lacks one or more corresponding type facts. "
                "Review before recording them as durable map context."
            )
        if advisory_status == "type_finding_current_map_undefined_value_type":
            return (
                f"The profile observed a project value type for {column_label} "
                "that already matches the current map, but that value type is "
                "not defined as rc:ValueType in ontology. Review the vocabulary "
                "meaning before treating the map assertion as fully resolved."
            )
        return (
            f"The profile observed type information for {column_label}. Review "
            "the profile evidence and modelling intent before recording map "
            "type facts."
        )
    @staticmethod
    def _profile_type_advisory_routing_note(
        advisory_status: str,
        *,
        related_recommendation_indexes: list[int],
        related_recommendation_kinds: list[str],
    ) -> str:
        if advisory_status == "type_finding_unmapped_column":
            if related_recommendation_indexes:
                indexes = ", ".join(
                    str(index) for index in related_recommendation_indexes
                )
                kinds = ", ".join(related_recommendation_kinds)
                return (
                    f"Review the related {kinds} recommendation index(es) "
                    f"{indexes} first. Stage/apply the column shell if "
                    "appropriate, then rerun or review type assertions after "
                    "the column is map-present. When these indexes are a "
                    "duplicate group, following the representative "
                    "stage_profile_map_updates action is enough to stage the "
                    "shared shell before rerun."
                )
            return (
                "No related unmapped_profiled_column recommendation was found; "
                "preserve the type finding as observation/pattern lore until "
                "there is current map column context to review."
            )
        if advisory_status == "type_finding_conflicts_current_map":
            return (
                "Inspect current map context and value-type semantics before "
                "staging any replacement type assertion."
            )
        if advisory_status == "type_finding_missing_map_type":
            return (
                "Inspect current map context before staging missing type facts "
                "as durable map assertions."
            )
        if advisory_status == "type_finding_current_map_undefined_value_type":
            return (
                "The current map already carries the observed project value "
                "type, but the value type is not defined in ontology; keep the "
                "profile type review open until the vocabulary term is reviewed "
                "or promoted."
            )
        return (
            "Inspect the profile evidence and modelling intent before recording "
            "map type facts."
        )
    def _profile_metric_vocabulary_advisories(
        self,
        profiles: list[ProfileObservationSummary],
        evidence_iri: str,
    ) -> list[ProfileMetricVocabularyAdvisory]:
        advisories: list[ProfileMetricVocabularyAdvisory] = []
        ontology_graphs = self._expand_graphs(["ontology"])
        profile_metric_kind = self.expand_iri("rc:ProfileMetricKind")
        for profile in profiles:
            for metric in profile.profile_metrics:
                if metric.metric.iri.startswith(PREFIXES["rc"]):
                    continue
                metric_iri = metric.metric.iri
                definition_found = self._subject_exists(metric_iri, ontology_graphs)
                metric_types = self._types_from_graphs(ontology_graphs, metric_iri)
                definition = (
                    self._resource_summary(ontology_graphs, metric_iri)
                    if definition_found
                    else None
                )
                if profile_metric_kind in metric_types:
                    advisory_status = "project_metric_defined"
                elif definition_found:
                    advisory_status = "project_metric_definition_ambiguous"
                else:
                    advisory_status = "project_metric_undefined"
                promotion_pattern_iris = (
                    self._profile_metric_promotion_pattern_iris(
                        metric_iri=metric_iri,
                        evidence_iri=evidence_iri,
                    )
                    if advisory_status
                    in {
                        "project_metric_undefined",
                        "project_metric_definition_ambiguous",
                    }
                    else []
                )
                context_pattern_iris = (
                    self._profile_metric_context_pattern_iris(
                        metric_iri=metric_iri,
                        evidence_iri=evidence_iri,
                        exclude_pattern_iris=promotion_pattern_iris,
                    )
                    if advisory_status
                    in {
                        "project_metric_undefined",
                        "project_metric_definition_ambiguous",
                    }
                    else []
                )
                pending_staged_promotion_iris = (
                    self._pending_staged_metric_promotion_iris(
                        metric_iri=metric_iri,
                        evidence_iri=evidence_iri,
                        promotion_pattern_iris=promotion_pattern_iris,
                    )
                    if advisory_status
                    in {
                        "project_metric_undefined",
                        "project_metric_definition_ambiguous",
                    }
                    else []
                )
                suggested_next_actions = self._profile_metric_advisory_actions(
                    observed_metric_iri=metric.iri,
                    profile_observation_iri=profile.iri,
                    metric_iri=metric_iri,
                    advisory_status=advisory_status,
                    promotion_pattern_iris=promotion_pattern_iris,
                    context_pattern_iris=context_pattern_iris,
                    evidence_iri=evidence_iri,
                    pending_staged_promotion_iris=pending_staged_promotion_iris,
                )
                advisories.append(
                    ProfileMetricVocabularyAdvisory(
                        profile_observation_iri=profile.iri,
                        observed_metric_iri=metric.iri,
                        metric_advisory_index=len(advisories),
                        evidence_iri=evidence_iri,
                        metric=metric.metric,
                        target=metric.target,
                        value=metric.value,
                        value_datatype=metric.value_datatype,
                        value_lang=metric.value_lang,
                        advisory_status=advisory_status,
                        definition_found=definition_found,
                        definition=definition,
                        promotion_patterns=self._resource_summaries(
                            self._lookup_graphs(["patterns"]),
                            promotion_pattern_iris,
                        ),
                        promotion_pattern_count=len(promotion_pattern_iris),
                        mixed_support_patterns=[],
                        mixed_support_pattern_count=0,
                        mixed_support_note=None,
                        context_patterns=self._resource_summaries(
                            self._lookup_graphs(["patterns"]),
                            context_pattern_iris,
                        ),
                        context_pattern_count=len(context_pattern_iris),
                        pending_staged_promotion_iris=pending_staged_promotion_iris,
                        pending_staged_promotion_count=len(
                            pending_staged_promotion_iris
                        ),
                        recommendation="review_metric_vocabulary_before_reuse",
                        rationale=(
                            "Project-specific profile metric IRIs are valid "
                            "observation lore, but reusable comparison or map "
                            "policy should define the metric meaning, unit, and "
                            "calculation in project ontology or supporting lore."
                        ),
                        suggested_next_actions=suggested_next_actions,
                    )
                )
        return self._with_profile_metric_advisory_duplicate_metadata(advisories)
    def _with_profile_metric_advisory_duplicate_metadata(
        self,
        advisories: list[ProfileMetricVocabularyAdvisory],
    ) -> list[ProfileMetricVocabularyAdvisory]:
        groups: dict[str, list[tuple[int, ProfileMetricVocabularyAdvisory]]] = {}
        for index, advisory in enumerate(advisories):
            groups.setdefault(
                self._profile_metric_advisory_duplicate_group_key(advisory),
                [],
            ).append((index, advisory))

        annotated: list[ProfileMetricVocabularyAdvisory] = []
        for index, advisory in enumerate(advisories):
            group_key = self._profile_metric_advisory_duplicate_group_key(advisory)
            group = groups[group_key]
            annotated.append(
                replace(
                    advisory,
                    metric_advisory_index=index,
                    duplicate_group_key=group_key,
                    duplicate_count=len(group),
                    duplicate_advisory_indexes=[
                        group_index for group_index, _ in group
                    ],
                    duplicate_profile_observation_iris=list(
                        dict.fromkeys(
                            item.profile_observation_iri for _, item in group
                        )
                    ),
                )
            )
        return annotated
    @staticmethod
    def _profile_metric_advisory_duplicate_group_key(
        advisory: ProfileMetricVocabularyAdvisory,
    ) -> str:
        payload = {
            "evidence_iri": advisory.evidence_iri,
            "metric_iri": advisory.metric.iri,
            "target_iri": advisory.target.iri if advisory.target else None,
            "value": advisory.value,
            "value_datatype": advisory.value_datatype,
            "value_lang": advisory.value_lang,
            "advisory_status": advisory.advisory_status,
            "definition_found": advisory.definition_found,
            "definition_iri": advisory.definition.iri if advisory.definition else None,
            "promotion_pattern_iris": [
                pattern.iri for pattern in advisory.promotion_patterns
            ],
            "context_pattern_iris": [
                pattern.iri for pattern in advisory.context_patterns
            ],
            "recommendation": advisory.recommendation,
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:12]
        return f"profile-metric-advisory:{digest}"
    def _with_profile_advisory_mixed_support(
        self,
        metric_advisories: list[ProfileMetricVocabularyAdvisory],
        type_advisories: list[ProfileTypeFindingAdvisory],
    ) -> tuple[
        list[ProfileMetricVocabularyAdvisory],
        list[ProfileTypeFindingAdvisory],
    ]:
        metric_pattern_iris = {
            pattern.iri
            for advisory in metric_advisories
            for pattern in advisory.promotion_patterns
        }
        type_pattern_iris = {
            pattern.iri
            for advisory in type_advisories
            for pattern in advisory.promotion_patterns
        }
        mixed_pattern_iris = metric_pattern_iris & type_pattern_iris
        if not mixed_pattern_iris:
            return metric_advisories, type_advisories

        metric_note = self._profile_advisory_mixed_support_note(
            "metric_vocabulary_review",
        )
        type_note = self._profile_advisory_mixed_support_note(
            "profile_type_review",
        )

        def annotate(
            advisory: ProfileMetricVocabularyAdvisory | ProfileTypeFindingAdvisory,
            *,
            note: str,
        ) -> ProfileMetricVocabularyAdvisory | ProfileTypeFindingAdvisory:
            mixed_patterns = [
                pattern
                for pattern in advisory.promotion_patterns
                if pattern.iri in mixed_pattern_iris
            ]
            if not mixed_patterns:
                return advisory
            suggested_next_actions = (
                self._profile_advisory_actions_with_mixed_support(
                    advisory.suggested_next_actions,
                    mixed_pattern_iris=mixed_pattern_iris,
                    mixed_support_note=note,
                )
            )
            return replace(
                advisory,
                mixed_support_patterns=mixed_patterns,
                mixed_support_pattern_count=len(mixed_patterns),
                mixed_support_note=note,
                suggested_next_actions=suggested_next_actions,
            )

        annotated_metric_advisories = [
            annotate(advisory, note=metric_note) for advisory in metric_advisories
        ]
        annotated_type_advisories = [
            annotate(advisory, note=type_note) for advisory in type_advisories
        ]
        return annotated_metric_advisories, annotated_type_advisories
    @staticmethod
    def _profile_advisory_mixed_support_note(advisory_kind: str) -> str:
        other_lane = (
            "profile type review"
            if advisory_kind == "metric_vocabulary_review"
            else "metric vocabulary review"
        )
        return (
            "Mixed support: one or more same-evidence promotion patterns also "
            f"support {other_lane}. Inspect the shared pattern carefully before "
            "promoting or asserting this lane independently. Review or export "
            "the generated promotion or assertion drafts together before "
            "applying either lane independently."
        )
    def _profile_advisory_actions_with_mixed_support(
        self,
        actions: list[SuggestedNextAction],
        *,
        mixed_pattern_iris: set[str],
        mixed_support_note: str,
    ) -> list[SuggestedNextAction]:
        updated_actions: list[SuggestedNextAction] = []
        for action in actions:
            arguments = action.args
            reason = action.reason
            should_note = False
            if (
                action.tool == "doxabase.describe_pattern"
                and arguments.get("iri") in mixed_pattern_iris
            ):
                should_note = True
            elif (
                action.tool == "doxabase.stage_pattern_promotion"
                and set(arguments.get("patterns") or []) & mixed_pattern_iris
            ):
                should_note = True
            elif action.tool == "doxabase.stage_map_assertion_change":
                should_note = True
            elif action.tool == "doxabase.stage_systematisation":
                should_note = True

            if not should_note:
                updated_actions.append(action)
                continue

            updated_arguments = copy.deepcopy(arguments)
            if action.tool in {
                "doxabase.stage_pattern_promotion",
                "doxabase.stage_map_assertion_change",
                "doxabase.stage_systematisation",
            }:
                self._add_mixed_support_review_note(
                    updated_arguments,
                    mixed_support_note,
                )
            updated_actions.append(
                replace(
                    action,
                    args=updated_arguments,
                    reason=f"{reason} {mixed_support_note}",
                )
            )
        return updated_actions
    def _profile_advisory_suggested_actions(
        self,
        advisories: Iterable[
            ProfileMetricVocabularyAdvisory | ProfileTypeFindingAdvisory
        ],
        *,
        advisory_kind: str,
        index_field: str,
    ) -> list[SuggestedNextAction]:
        actions_by_key: dict[tuple[str, str], SuggestedNextAction] = {}
        source_by_key: dict[tuple[str, str], dict[str, Any]] = {}
        action_order: list[tuple[str, str]] = []

        for advisory in advisories:
            advisory_index = getattr(advisory, index_field)
            duplicate_advisory_indexes = (
                advisory.duplicate_advisory_indexes or [advisory_index]
            )
            duplicate_profile_observation_iris = (
                advisory.duplicate_profile_observation_iris
                or [advisory.profile_observation_iri]
            )
            for action in advisory.suggested_next_actions:
                key = suggested_action_key(action)
                if key not in actions_by_key:
                    actions_by_key[key] = action
                    action_order.append(key)
                    source_by_key[key] = {
                        "review_lane": advisory_kind,
                        "advisory_kind": advisory_kind,
                        "index_field": index_field,
                        "advisory_indexes": [],
                        "duplicate_group_keys": [],
                        "duplicate_advisory_indexes": [],
                        "duplicate_profile_observation_iris": [],
                        "route_anchor_iris": [],
                        "route_pattern_iris": [],
                        "advisory_statuses": [],
                    }
                source = source_by_key[key]
                DoxaBase._append_unique(source["advisory_indexes"], advisory_index)
                route_anchor_iris = source["route_anchor_iris"]
                for resource in DoxaBase._profile_advisory_route_resources(advisory):
                    DoxaBase._append_unique(route_anchor_iris, resource.iri)
                route_pattern_iris = source["route_pattern_iris"]
                for pattern in DoxaBase._profile_advisory_route_patterns(advisory):
                    DoxaBase._append_unique(route_pattern_iris, pattern.iri)
                mixed_support_patterns = getattr(
                    advisory,
                    "mixed_support_patterns",
                    [],
                )
                mixed_support_note = getattr(advisory, "mixed_support_note", None)
                if mixed_support_patterns:
                    mixed_support = source.setdefault(
                        "mixed_support",
                        {
                            "pattern_iris": [],
                            "pattern_count": 0,
                            "other_review_lanes": [],
                            "note": mixed_support_note,
                        },
                    )
                    other_lane = (
                        "profile_type_review"
                        if advisory_kind == "metric_vocabulary_review"
                        else "metric_vocabulary_review"
                    )
                    DoxaBase._append_unique(
                        mixed_support["other_review_lanes"],
                        other_lane,
                    )
                    for pattern in mixed_support_patterns:
                        DoxaBase._append_unique(
                            mixed_support["pattern_iris"],
                            pattern.iri,
                        )
                    mixed_support["pattern_count"] = len(
                        mixed_support["pattern_iris"]
                    )
                if advisory.duplicate_group_key:
                    DoxaBase._append_unique(
                        source["duplicate_group_keys"],
                        advisory.duplicate_group_key,
                    )
                for duplicate_index in duplicate_advisory_indexes:
                    DoxaBase._append_unique(
                        source["duplicate_advisory_indexes"],
                        duplicate_index,
                    )
                for observation_iri in duplicate_profile_observation_iris:
                    DoxaBase._append_unique(
                        source["duplicate_profile_observation_iris"],
                        observation_iri,
                    )
                advisory_status = getattr(advisory, "advisory_status", None)
                if isinstance(advisory_status, str):
                    DoxaBase._append_unique(
                        source["advisory_statuses"],
                        advisory_status,
                    )
                observed_metric_iri = getattr(advisory, "observed_metric_iri", None)
                if observed_metric_iri:
                    observed_metric_iris = source.setdefault(
                        "observed_metric_iris",
                        [],
                    )
                    DoxaBase._append_unique(
                        observed_metric_iris,
                        observed_metric_iri,
                    )
                if isinstance(advisory, ProfileMetricVocabularyAdvisory):
                    metric_iris = source.setdefault("metric_iris", [])
                    DoxaBase._append_unique(metric_iris, advisory.metric.iri)
                    target_iris = source.setdefault("target_iris", [])
                    if advisory.target is not None:
                        DoxaBase._append_unique(target_iris, advisory.target.iri)
                    observed_values = source.setdefault("observed_values", [])
                    DoxaBase._append_unique(observed_values, advisory.value)
                if isinstance(advisory, ProfileTypeFindingAdvisory):
                    observed_column_iris = source.setdefault(
                        "observed_column_iris",
                        [],
                    )
                    DoxaBase._append_unique(
                        observed_column_iris,
                        advisory.observed_column.iri,
                    )
                    observed_column_names = source.setdefault(
                        "observed_column_names",
                        [],
                    )
                    if advisory.observed_column_name:
                        DoxaBase._append_unique(
                            observed_column_names,
                            advisory.observed_column_name,
                        )
                    observed_physical_type_iris = source.setdefault(
                        "observed_physical_type_iris",
                        [],
                    )
                    if advisory.observed_physical_type is not None:
                        DoxaBase._append_unique(
                            observed_physical_type_iris,
                            advisory.observed_physical_type.iri,
                        )
                    observed_value_type_iris = source.setdefault(
                        "observed_value_type_iris",
                        [],
                    )
                    if advisory.observed_value_type is not None:
                        DoxaBase._append_unique(
                            observed_value_type_iris,
                            advisory.observed_value_type.iri,
                        )
                    current_physical_type_iris = source.setdefault(
                        "current_physical_type_iris",
                        [],
                    )
                    if advisory.current_physical_type is not None:
                        DoxaBase._append_unique(
                            current_physical_type_iris,
                            advisory.current_physical_type.iri,
                        )
                    current_value_type_iris = source.setdefault(
                        "current_value_type_iris",
                        [],
                    )
                    if advisory.current_value_type is not None:
                        DoxaBase._append_unique(
                            current_value_type_iris,
                            advisory.current_value_type.iri,
                        )
                pending_staged_promotion_iris = getattr(
                    advisory,
                    "pending_staged_promotion_iris",
                    [],
                )
                if pending_staged_promotion_iris:
                    pending_values = source.setdefault(
                        "pending_staged_promotion_iris",
                        [],
                    )
                    for staged_iri in pending_staged_promotion_iris:
                        DoxaBase._append_unique(pending_values, staged_iri)
                    source["pending_staged_promotion_count"] = len(
                        pending_values
                    )
                pending_staged_assertion_iris = getattr(
                    advisory,
                    "pending_staged_assertion_iris",
                    [],
                )
                if pending_staged_assertion_iris:
                    pending_values = source.setdefault(
                        "pending_staged_assertion_iris",
                        [],
                    )
                    for staged_iri in pending_staged_assertion_iris:
                        DoxaBase._append_unique(pending_values, staged_iri)
                    source["pending_staged_assertion_count"] = len(
                        pending_values
                    )

        actions: list[SuggestedNextAction] = []
        for key in action_order:
            action = actions_by_key[key]
            source = DoxaBase._profile_advisory_source_with_route_keys(
                source_by_key[key],
                action,
            )
            actions.extend(
                self._profile_advisory_pending_aware_suggested_actions(
                    action,
                    source_profile_advisory=source,
                )
            )
        return self._dedupe_suggested_next_actions(actions)
    def _profile_advisory_row_suggested_actions(
        self,
        advisory: ProfileMetricVocabularyAdvisory | ProfileTypeFindingAdvisory,
        *,
        advisory_kind: str,
        index_field: str,
    ) -> list[SuggestedNextAction]:
        actions: list[SuggestedNextAction] = []
        for action in advisory.suggested_next_actions:
            source = DoxaBase._profile_advisory_source_for_advisory(
                advisory,
                advisory_kind=advisory_kind,
                index_field=index_field,
            )
            actions.extend(
                self._profile_advisory_pending_aware_suggested_actions(
                    action,
                    source_profile_advisory=(
                        DoxaBase._profile_advisory_source_with_route_keys(
                            source,
                            action,
                        )
                    ),
                )
            )
        return self._dedupe_suggested_next_actions(actions)
    def _profile_advisory_pending_aware_suggested_actions(
        self,
        action: SuggestedNextAction,
        *,
        source_profile_advisory: dict[str, Any],
    ) -> list[SuggestedNextAction]:
        pending_fallback_iris = self._pending_staged_profile_fallback_iris(
            source_profile_advisory
        )
        if (
            action.tool in {
                "doxabase.record_pattern",
                "doxabase.stage_systematisation",
            }
            and source_profile_advisory.get("semantic_move") == "caveat_fallback"
            and pending_fallback_iris
        ):
            source = dict(source_profile_advisory)
            source["action_status"] = "already_pending"
            source["pending_staged_fallback_iris"] = list(pending_fallback_iris)
            source["pending_staged_fallback_count"] = len(pending_fallback_iris)
            return [
                DoxaBase._profile_advisory_suggested_action(
                    pending_action,
                    source_profile_advisory=source,
                )
                for pending_action in self._profile_pending_fallback_review_actions(
                    pending_fallback_iris
                )
            ]
        pending_value_type_promotion_iris = (
            DoxaBase._string_values_from_any(
                source_profile_advisory.get("pending_staged_promotion_iris")
            )
        )
        if (
            action.tool == "doxabase.stage_pattern_promotion"
            and source_profile_advisory.get("semantic_move") == "define_value_type"
        ):
            if not pending_value_type_promotion_iris:
                pending_value_type_promotion_iris = (
                    self._pending_staged_profile_route_iris(
                        source_profile_advisory,
                        semantic_move="define_value_type",
                    )
                )
            if pending_value_type_promotion_iris:
                source = dict(source_profile_advisory)
                source["action_status"] = "already_pending"
                source["pending_staged_promotion_iris"] = list(
                    pending_value_type_promotion_iris
                )
                source["pending_staged_promotion_count"] = len(
                    pending_value_type_promotion_iris
                )
                return [
                    DoxaBase._profile_advisory_suggested_action(
                        pending_action,
                        source_profile_advisory=source,
                    )
                    for pending_action in self._profile_pending_type_review_actions(
                        pending_value_type_promotion_iris,
                        semantic_move="define_value_type",
                    )
                ]
        pending_type_assertion_iris = DoxaBase._string_values_from_any(
            source_profile_advisory.get("pending_staged_assertion_iris")
        )
        if (
            action.tool == "doxabase.stage_map_assertion_change"
            and source_profile_advisory.get("semantic_move") == "assert_map_type"
        ):
            if not pending_type_assertion_iris:
                pending_type_assertion_iris = self._pending_staged_profile_route_iris(
                    source_profile_advisory,
                    semantic_move="assert_map_type",
                )
            if pending_type_assertion_iris:
                source = dict(source_profile_advisory)
                source["action_status"] = "already_pending"
                source["pending_staged_assertion_iris"] = list(
                    pending_type_assertion_iris
                )
                source["pending_staged_assertion_count"] = len(
                    pending_type_assertion_iris
                )
                return [
                    DoxaBase._profile_advisory_suggested_action(
                        pending_action,
                        source_profile_advisory=source,
                    )
                    for pending_action in self._profile_pending_type_review_actions(
                        pending_type_assertion_iris,
                        semantic_move="assert_map_type",
                    )
                ]
        return [
            DoxaBase._profile_advisory_suggested_action(
                action,
                source_profile_advisory=source_profile_advisory,
            )
        ]
    @staticmethod
    def _profile_advisory_source_for_advisory(
        advisory: ProfileMetricVocabularyAdvisory | ProfileTypeFindingAdvisory,
        *,
        advisory_kind: str,
        index_field: str,
    ) -> dict[str, Any]:
        advisory_index = getattr(advisory, index_field)
        duplicate_advisory_indexes = (
            advisory.duplicate_advisory_indexes or [advisory_index]
        )
        duplicate_profile_observation_iris = (
            advisory.duplicate_profile_observation_iris
            or [advisory.profile_observation_iri]
        )
        source: dict[str, Any] = {
            "review_lane": advisory_kind,
            "advisory_kind": advisory_kind,
            "index_field": index_field,
            "advisory_indexes": [advisory_index],
            "duplicate_group_keys": [],
            "duplicate_advisory_indexes": list(duplicate_advisory_indexes),
            "duplicate_profile_observation_iris": list(
                duplicate_profile_observation_iris
            ),
            "route_anchor_iris": list(
                dict.fromkeys(
                    resource.iri
                    for resource in DoxaBase._profile_advisory_route_resources(
                        advisory
                    )
                )
            ),
            "route_pattern_iris": list(
                dict.fromkeys(
                    pattern.iri
                    for pattern in DoxaBase._profile_advisory_route_patterns(
                        advisory
                    )
                )
            ),
            "advisory_statuses": [advisory.advisory_status],
        }
        if advisory.duplicate_group_key:
            source["duplicate_group_keys"] = [advisory.duplicate_group_key]
        if isinstance(advisory, ProfileMetricVocabularyAdvisory):
            source["observed_metric_iris"] = [advisory.observed_metric_iri]
            source["metric_iris"] = [advisory.metric.iri]
            source["target_iris"] = (
                [advisory.target.iri] if advisory.target is not None else []
            )
            source["observed_values"] = [advisory.value]
            if advisory.pending_staged_promotion_iris:
                source["pending_staged_promotion_iris"] = list(
                    advisory.pending_staged_promotion_iris
                )
                source["pending_staged_promotion_count"] = len(
                    advisory.pending_staged_promotion_iris
                )
        if isinstance(advisory, ProfileTypeFindingAdvisory):
            source["observed_column_iris"] = [advisory.observed_column.iri]
            source["observed_column_names"] = (
                [advisory.observed_column_name]
                if advisory.observed_column_name
                else []
            )
            source["observed_physical_type_iris"] = (
                [advisory.observed_physical_type.iri]
                if advisory.observed_physical_type is not None
                else []
            )
            source["observed_value_type_iris"] = (
                [advisory.observed_value_type.iri]
                if advisory.observed_value_type is not None
                else []
            )
            source["current_physical_type_iris"] = (
                [advisory.current_physical_type.iri]
                if advisory.current_physical_type is not None
                else []
            )
            source["current_value_type_iris"] = (
                [advisory.current_value_type.iri]
                if advisory.current_value_type is not None
                else []
            )
            if advisory.pending_staged_promotion_iris:
                source["pending_staged_promotion_iris"] = list(
                    advisory.pending_staged_promotion_iris
                )
                source["pending_staged_promotion_count"] = len(
                    advisory.pending_staged_promotion_iris
                )
            if advisory.pending_staged_assertion_iris:
                source["pending_staged_assertion_iris"] = list(
                    advisory.pending_staged_assertion_iris
                )
                source["pending_staged_assertion_count"] = len(
                    advisory.pending_staged_assertion_iris
                )
        if advisory.mixed_support_patterns:
            other_lane = (
                "profile_type_review"
                if advisory_kind == "metric_vocabulary_review"
                else "metric_vocabulary_review"
            )
            source["mixed_support"] = {
                "pattern_iris": list(
                    dict.fromkeys(
                        pattern.iri
                        for pattern in advisory.mixed_support_patterns
                    )
                ),
                "pattern_count": advisory.mixed_support_pattern_count,
                "other_review_lanes": [other_lane],
                "note": advisory.mixed_support_note,
            }
        return source
    @staticmethod
    def _profile_advisory_route_resources(
        advisory: ProfileMetricVocabularyAdvisory | ProfileTypeFindingAdvisory,
    ) -> list[ResourceSummary]:
        resources: list[ResourceSummary] = []
        for value in (
            getattr(advisory, "metric", None),
            getattr(advisory, "target", None),
            getattr(advisory, "observed_column", None),
            getattr(advisory, "observed_physical_type", None),
            getattr(advisory, "observed_value_type", None),
            getattr(advisory, "current_physical_type", None),
            getattr(advisory, "current_value_type", None),
        ):
            if isinstance(value, ResourceSummary):
                resources.append(value)
        observed_metric_iri = getattr(advisory, "observed_metric_iri", None)
        if observed_metric_iri:
            resources.append(
                ResourceSummary(
                    iri=observed_metric_iri,
                    label=None,
                    description=None,
                )
            )
        return resources
    @staticmethod
    def _profile_advisory_route_patterns(
        advisory: ProfileMetricVocabularyAdvisory | ProfileTypeFindingAdvisory,
    ) -> list[ResourceSummary]:
        patterns: list[ResourceSummary] = []
        for field_name in (
            "promotion_patterns",
            "mixed_support_patterns",
            "context_patterns",
        ):
            patterns.extend(getattr(advisory, field_name, []) or [])
        return patterns
    @staticmethod
    def _profile_advisory_source_with_route_keys(
        source_profile_advisory: dict[str, Any],
        action: SuggestedNextAction,
    ) -> dict[str, Any]:
        source = dict(source_profile_advisory)
        route_group_key = DoxaBase._profile_route_group_key(
            str(source["review_lane"]),
            source.get("duplicate_group_keys") or source.get("route_anchor_iris"),
        )
        source["route_group_key"] = route_group_key
        semantic_move = DoxaBase._profile_advisory_semantic_move(action, source)
        if semantic_move is not None:
            source["semantic_move"] = semantic_move
        source = DoxaBase._with_profile_route_step_key(source, action)
        DoxaBase._add_profile_advisory_action_bindings(source, action)
        return source
    @staticmethod
    def _add_profile_advisory_action_bindings(
        source_profile_advisory: dict[str, Any],
        action: SuggestedNextAction,
    ) -> None:
        if source_profile_advisory.get("review_lane") != "profile_type_review":
            return
        route_group_key = source_profile_advisory.get("route_group_key")
        if not isinstance(route_group_key, str):
            return
        if DoxaBase._profile_advisory_status_set(source_profile_advisory) == {
            "type_finding_current_map_undefined_value_type"
        }:
            return
        binding_key = f"{route_group_key}:profile-type-support-pattern"
        if action.tool == "doxabase.stage_map_assertion_change":
            supporting_patterns = action.args.get("supporting_patterns")
            if isinstance(supporting_patterns, list) and supporting_patterns:
                return
            source_profile_advisory["consumes_result_bindings"] = [
                {
                    "binding_key": binding_key,
                    "source_tool_name": "record_pattern",
                    "source_result_field": "pattern_iri",
                    "argument": "supporting_patterns",
                    "append": True,
                    "review_lane": "profile_type_review",
                    "route_group_key": route_group_key,
                    "source_semantic_move": "caveat_fallback",
                }
            ]
    @staticmethod
    def _profile_advisory_suggested_action(
        action: SuggestedNextAction,
        *,
        source_profile_advisory: dict[str, Any],
    ) -> SuggestedNextAction:
        arguments = copy.deepcopy(action.args)
        if action.tool in {
            "doxabase.stage_pattern_promotion",
            "doxabase.stage_map_assertion_change",
            "doxabase.stage_systematisation",
        }:
            arguments.setdefault(
                "profile_route_sources",
                [copy.deepcopy(source_profile_advisory)],
            )
        return SuggestedNextAction(
            tool=action.tool,
            args=arguments,
            reason=action.reason,
        )
    def _profile_metric_advisory_actions(
        self,
        *,
        observed_metric_iri: str | None,
        profile_observation_iri: str | None,
        metric_iri: str,
        advisory_status: str,
        promotion_pattern_iris: list[str] | None = None,
        context_pattern_iris: list[str] | None = None,
        evidence_iri: str | None = None,
        pending_staged_promotion_iris: list[str] | None = None,
    ) -> list[SuggestedNextAction]:
        actions: list[SuggestedNextAction] = []
        promotion_pattern_values = list(promotion_pattern_iris or [])
        context_pattern_values = list(context_pattern_iris or [])
        pending_staged_promotion_values = list(pending_staged_promotion_iris or [])
        focused_seed_iri = observed_metric_iri or profile_observation_iri or metric_iri

        def add_action(
            tool_name: str,
            arguments: dict[str, Any],
            reason: str,
        ) -> None:
            actions.append(
                SuggestedNextAction(
                    tool=f"doxabase.{tool_name}",
                    args=arguments,
                    reason=reason,
                )
            )

        add_action(
            "get_context_graph",
            {"seed_iris": [focused_seed_iri], "profile": "dataset_brief"},
            (
                "Load bounded lore around this observed profile metric before "
                "reusing its project-specific metric kind in comparison, map "
                "policy, or ontology."
            ),
        )
        if advisory_status in {
            "project_metric_defined",
            "project_metric_definition_ambiguous",
        }:
            add_action(
                "describe_resource",
                {"iri": metric_iri, "graph": "ontology"},
                (
                    "Inspect the existing project ontology definition before "
                    "using or repairing this metric in durable comparisons or "
                    "map policy."
                ),
            )
        if advisory_status != "project_metric_defined":
            add_action(
                "list_entities",
                {
                    "type": "rc:ProfileMetricKind",
                    "graph": "ontology",
                    "text": self._local_name(metric_iri),
                },
                (
                    "Look for nearby metric vocabulary before recording claims, "
                    "patterns, or a promoted ontology definition for this metric."
                ),
            )
            if profile_observation_iri is not None and evidence_iri is not None:
                add_action(
                    "stage_systematisation",
                    self._profile_metric_fallback_systematisation_arguments(
                        metric_iri=metric_iri,
                        observed_metric_iri=observed_metric_iri,
                        profile_observation_iri=profile_observation_iri,
                        evidence_iri=evidence_iri,
                    ),
                    (
                        "Stage a reviewable pattern fallback if this metric "
                        "needs semantic review before becoming project "
                        "ontology vocabulary."
                    ),
                )

        def add_context_pattern_actions() -> None:
            for pattern_iri in context_pattern_values[:3]:
                add_action(
                    "describe_pattern",
                    {"iri": pattern_iri},
                    (
                        "Inspect this same-evidence metric pattern as context. "
                        "It is not structurally tied to the metric as a target "
                        "or map implication, so it is not used as automatic "
                        "promotion support."
                    ),
                )

        if (
            advisory_status
            in {
                "project_metric_undefined",
                "project_metric_definition_ambiguous",
            }
            and promotion_pattern_values
        ):
            for pattern_iri in promotion_pattern_values[:3]:
                add_action(
                    "describe_pattern",
                    {"iri": pattern_iri},
                    (
                        "Inspect the same-evidence pattern before promoting this "
                        "project metric into ontology vocabulary."
                    ),
                )
            add_context_pattern_actions()
            if pending_staged_promotion_values:
                for staged_iri in pending_staged_promotion_values[:3]:
                    add_action(
                        "describe_staged_revision",
                        {
                            "iri": staged_iri,
                            "include_current_apply_check": True,
                        },
                        (
                            "A current staged metric vocabulary skeleton already "
                            "targets this metric with the same evidence and pattern "
                            "support. Inspect that staged revision before drafting "
                            "another duplicate skeleton."
                        ),
                    )
                add_action(
                    "export_staged_revisions",
                    {
                        "revision_iris": pending_staged_promotion_values,
                        "path": self._suggested_review_export_path(
                            "profile-metric-vocabulary-pending",
                            pending_staged_promotion_values,
                        ),
                        "fail_on_sensitive": True,
                    },
                    (
                        "Write a grouped review bundle for pending staged metric "
                        "vocabulary skeletons before deciding whether new metric "
                        "promotion work is still needed. The suggested call "
                        "blocks if scanner-matching content appears before "
                        "export."
                    ),
                )
            else:
                add_action(
                    "stage_pattern_promotion",
                    self._profile_metric_promotion_skeleton_arguments(
                        metric_iri=metric_iri,
                        pattern_iris=promotion_pattern_values,
                        evidence_iri=evidence_iri,
                    ),
                    (
                        "Stage a reviewable ontology skeleton for this project metric "
                        "only after checking that the same-evidence pattern captures "
                        "its calculation, unit, and comparison semantics."
                    ),
                )
        else:
            add_context_pattern_actions()
        return actions
