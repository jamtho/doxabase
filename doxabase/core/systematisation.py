"""Systematisation drafting and shared-context reruns.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via SystematisationMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class SystematisationMixin:
    def _profile_type_fallback_systematisation_arguments(
        self,
        *,
        profile: ProfileObservationSummary,
        evidence_iri: str,
        type_implication_iris: list[str],
        column_label: str,
    ) -> dict[str, Any]:
        assert profile.observed_column is not None
        pattern_iri = self._profile_fallback_pattern_iri(
            "profile-type-fallback-pattern",
            {
                "observed_column_iri": profile.observed_column.iri,
                "observed_physical_type_iri": (
                    profile.observed_physical_type.iri
                    if profile.observed_physical_type is not None
                    else None
                ),
                "observed_value_type_iri": (
                    profile.observed_value_type.iri
                    if profile.observed_value_type is not None
                    else None
                ),
                "evidence_iri": evidence_iri,
            },
        )
        pattern_text = (
            f"Profile evidence observed type information for {column_label}. "
            "Keep this as a reviewable interpretation pattern until current "
            "map context and value-type semantics justify a durable assertion."
        )
        rationale = (
            "Profile type findings are evidence, not automatic map updates. "
            "A staged pattern fallback preserves the judgement without applying "
            "physical or value type map facts."
        )
        content = self._profile_fallback_pattern_turtle(
            pattern_iri=pattern_iri,
            summary=f"Review profiled type for {column_label}",
            pattern_text=pattern_text,
            rationale=rationale,
            pattern_targets=[profile.observed_column.iri],
            supporting_observations=[profile.iri],
            evidence_iri=evidence_iri,
            map_implications=list(dict.fromkeys(type_implication_iris)),
        )
        return {
            "summary": f"Review profiled type fallback for {column_label}",
            "intent": (
                "Stage a pattern-only fallback for profile type evidence that "
                "is not ready to become current map type assertions."
            ),
            "rationale": rationale,
            "framings": [
                {
                    "label": "Pattern fallback",
                    "graph": "patterns",
                    "content": content,
                    "review_note": (
                        "Generated from a profile type-finding advisory; review "
                        "whether this fallback should stay as pattern lore or "
                        "be followed by a map assertion."
                    ),
                    "review_recommendation": (
                        "Prefer this fallback when the profile type finding is "
                        "ambiguous or needs value-type/domain review before "
                        "map mutation."
                    ),
                }
            ],
            "anchors": list(
                dict.fromkeys(
                    [
                        profile.iri,
                        profile.observed_column.iri,
                        *type_implication_iris,
                    ]
                )
            ),
            "supporting_observations": [profile.iri],
            "evidence": [evidence_iri],
            "validation_scope": "all",
        }
    def _profile_metric_fallback_systematisation_arguments(
        self,
        *,
        metric_iri: str,
        observed_metric_iri: str | None,
        profile_observation_iri: str,
        evidence_iri: str,
    ) -> dict[str, Any]:
        metric_label = self._local_name(metric_iri) or metric_iri
        pattern_iri = self._profile_fallback_pattern_iri(
            "profile-metric-fallback-pattern",
            {
                "metric_iri": metric_iri,
                "observed_metric_iri": observed_metric_iri,
                "profile_observation_iri": profile_observation_iri,
                "evidence_iri": evidence_iri,
            },
        )
        pattern_text = (
            f"Profile evidence used the project metric {metric_label}. Keep "
            "the metric as reviewable interpretation lore until calculation, "
            "unit, denominator, and comparison semantics are explicit enough "
            "for reusable ontology vocabulary."
        )
        rationale = (
            "Project-specific profile metric IRIs are valid observation lore, "
            "but reusable comparison or map policy needs reviewed semantics. "
            "A staged pattern fallback preserves the finding without minting "
            "an ontology definition."
        )
        content = self._profile_fallback_pattern_turtle(
            pattern_iri=pattern_iri,
            summary=f"Review {metric_label} profile metric",
            pattern_text=pattern_text,
            rationale=rationale,
            pattern_targets=[metric_iri],
            supporting_observations=[profile_observation_iri],
            evidence_iri=evidence_iri,
            map_implications=[metric_iri],
        )
        anchors = [profile_observation_iri, metric_iri]
        if observed_metric_iri is not None:
            anchors.append(observed_metric_iri)
        return {
            "summary": f"Review {metric_label} metric fallback",
            "intent": (
                "Stage a pattern-only fallback for profile metric evidence "
                "that is not ready to become project ontology vocabulary."
            ),
            "rationale": rationale,
            "framings": [
                {
                    "label": "Pattern fallback",
                    "graph": "patterns",
                    "content": content,
                    "review_note": (
                        "Generated from a profile metric advisory; review "
                        "whether this fallback should stay as pattern lore or "
                        "be followed by a metric vocabulary definition."
                    ),
                    "review_recommendation": (
                        "Prefer this fallback when metric semantics are too "
                        "thin for reusable ontology vocabulary."
                    ),
                }
            ],
            "anchors": list(dict.fromkeys(anchors)),
            "supporting_observations": [profile_observation_iri],
            "evidence": [evidence_iri],
            "validation_scope": "all",
        }
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
        shared_semantic_context_graphs = sorted(
            {
                str(spec["graph"])
                for spec in [*shared_addition_specs, *shared_removal_specs]
                if str(spec.get("graph") or "") in {"ontology", "shapes"}
            }
        )
        shared_context_summary_value = (
            shared_context_summary.strip()
            if shared_context_summary is not None
            else None
        )
        profile_route_source_values = self._explicit_profile_route_sources(
            profile_route_sources
        )

        warnings: list[str] = []
        structured_warnings: list[SystematisationWarningRecord] = []
        if profile_route_sources is not None and not profile_route_source_values:
            warnings.append(
                "profile_route_sources was provided, but no usable profile "
                "route source objects were found. Pass route source objects, "
                "for example entries from a suggested action's "
                "args['profile_route_sources'], rather than the whole "
                "suggested action object."
            )
        if not anchor_values:
            warnings.append(
                "No anchors were supplied; future reviewers may have less context."
            )
        if shared_patch_count:
            warnings.append(
                "Shared proposed context patches are included in every staged framing preview and patch bundle."
            )
        staged_revisions: list[StagedGraphRevisionRecord] = []
        framing_records: list[SystematisationFramingRecord] = []
        first_revision_iri: str | None = None
        first_anchor_default_linked_revision_iris: list[str] = []
        recorded_profile_route_sources: list[dict[str, Any]] = []
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
            framing_route_sources_provided = any(
                key in framing
                for key in ("profile_route_sources", "profileRouteSources")
            )
            framing_profile_route_source_values = (
                self._explicit_profile_route_sources(
                    framing.get("profile_route_sources")
                    if "profile_route_sources" in framing
                    else framing.get("profileRouteSources")
                )
                if framing_route_sources_provided
                else []
            )
            if (
                framing_route_sources_provided
                and not framing_profile_route_source_values
            ):
                warnings.append(
                    "profile_route_sources was provided for framing "
                    f"{label!r}, but no usable profile route source objects were "
                    "found. Pass route source objects, for example entries "
                    "from a suggested action's args['profile_route_sources'], "
                    "rather than the whole suggested action object."
                )
            framing_effective_profile_route_sources = (
                self._merge_profile_route_sources(
                    profile_route_source_values,
                    framing_profile_route_source_values,
                )
            )
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
            framing_alternative_to_index = (
                framing.get("alternative_to_framing_index")
                if "alternative_to_framing_index" in framing
                else framing.get("alternativeToFramingIndex")
            )
            if isinstance(framing_alternative_to_index, str):
                framing_alternative_to_index = (
                    framing_alternative_to_index.strip() or None
                )
            if framing_alternative_to and framing_alternative_to_index is not None:
                raise DoxaBaseError(
                    "framing alternative_to and alternative_to_framing_index "
                    "are mutually exclusive"
                )
            default_linked_to_first = False
            if framing_alternative_to_index is not None:
                if isinstance(framing_alternative_to_index, bool):
                    raise DoxaBaseError(
                        "alternative_to_framing_index must be a 1-based integer"
                    )
                try:
                    relative_index = int(framing_alternative_to_index)
                except (TypeError, ValueError) as exc:
                    raise DoxaBaseError(
                        "alternative_to_framing_index must be a 1-based integer"
                    ) from exc
                if relative_index < 1 or relative_index >= index:
                    raise DoxaBaseError(
                        "alternative_to_framing_index must reference an earlier "
                        "framing in the same stage_systematisation call"
                    )
                alternative_target = staged_revisions[relative_index - 1].revision_iri
            elif framing_alternative_to:
                alternative_target = framing_alternative_to
            elif index == 1:
                alternative_target = alternative_to
            elif link_alternatives:
                alternative_target = first_revision_iri
                default_linked_to_first = first_revision_iri is not None
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
            staged = replace(
                staged,
                framing_index=index,
                framing_label=label,
            )
            self._record_profile_insight_route_sources(
                staged.revision_iri,
                framing_effective_profile_route_sources,
            )
            recorded_profile_route_sources = self._merge_profile_route_sources(
                recorded_profile_route_sources,
                framing_effective_profile_route_sources,
            )
            if first_revision_iri is None:
                first_revision_iri = staged.revision_iri
            staged_revisions.append(staged)
            if default_linked_to_first:
                first_anchor_default_linked_revision_iris.append(staged.revision_iri)
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

        bundle_summary, suggested_next_actions = (
            self._systematisation_draft_routing(staged_revisions)
        )
        warning_suggested_actions: list[SuggestedNextAction] = []
        next_action_queue = bundle_summary.next_action_queue
        if first_anchor_default_linked_revision_iris:
            warnings.append(
                "Multiple framings were staged; at least one later revision "
                "was linked as an alternative to the first."
            )
        if len(staged_revisions) > 1 and shared_semantic_context_graphs:
            shared_graph_summary = ", ".join(shared_semantic_context_graphs)
            shared_patch_summaries = (
                self._systematisation_shared_patch_summaries(staged_revisions)
            )
            shared_patch_sources_to_move = (
                self._systematisation_shared_patch_sources_to_move(
                    shared_addition_specs,
                    shared_removal_specs,
                    shared_semantic_context_graphs,
                )
            )
            fallback_revision_iris = [
                revision.revision_iri for revision in staged_revisions[1:]
            ]
            warning_message = (
                "Shared ontology or shapes context patches are included in "
                "every staged framing preview and patch bundle, including "
                f"fallback framings. Shared graph roles: {shared_graph_summary}. "
                "Move those patches into per-framing additions or removals "
                "when only some alternatives should carry provisional "
                "vocabulary or validation shapes. Choose the target framings "
                "semantically; fallback_revision_iris_with_shared_semantic_context "
                "lists later framings that currently received the shared context, "
                "not the exact framings that should drop it."
            )
            warnings.append(warning_message)
            structured_warnings.append(
                SystematisationWarningRecord(
                    warning_code="shared_semantic_context_applies_to_all_framings",
                    message=warning_message,
                    affected_revision_iris=[
                        revision.revision_iri for revision in staged_revisions
                    ],
                    suggested_action=(
                        "rerun_with_shared_semantic_context_moved_to_framings"
                    ),
                    suggested_rerun_arguments={
                        "move_shared_patch_graphs_into_framing_patches": (
                            shared_semantic_context_graphs
                        ),
                        "shared_patch_sources_to_move": shared_patch_sources_to_move,
                        "target_framing_selection_required": True,
                        "target_framing_selection_note": (
                            "Choose which framings should receive the moved "
                            "ontology/shapes patches. "
                            "fallback_revision_iris_with_shared_semantic_context "
                            "is an inspection subset of later framings currently "
                            "carrying shared context, not an automatic drop list."
                        ),
                    },
                    shared_patch_summaries=shared_patch_summaries,
                    fallback_revision_iris_with_shared_semantic_context=(
                        fallback_revision_iris
                    ),
                )
            )
        if (
            len(staged_revisions) > 1
            and link_alternatives
            and first_revision_iri
            and first_anchor_default_linked_revision_iris
        ):
            first_queue = next(
                (
                    queue
                    for queue, revision_iris in next_action_queue.items()
                    if first_revision_iri in revision_iris
                ),
                "unrouted",
            )
            if first_queue != "apply_after_review":
                first_framing = framing_records[0]
                if first_framing.validation_conforms:
                    status_note = f"routed to {first_queue}"
                else:
                    status_note = (
                        "failed staged validation"
                        f" with {first_framing.validation_result_count} result(s)"
                    )
                warning_message = (
                    "First framing "
                    f"'{first_framing.label}' ({first_revision_iri}) "
                    f"{status_note}; later framings were linked as alternatives "
                    "to it. Pass alternative_to=... or link_alternatives=False "
                    "when the first framing is diagnostic or complementary "
                    "rather than the intended comparison anchor."
                )
                warnings.append(warning_message)
                structured_warnings.append(
                    SystematisationWarningRecord(
                        warning_code="first_alternative_anchor_not_ready",
                        message=warning_message,
                        affected_revision_iris=[
                            first_revision_iri,
                            *first_anchor_default_linked_revision_iris,
                        ],
                        suggested_action="rerun_with_explicit_alternative_routing",
                        suggested_rerun_arguments={"link_alternatives": False},
                    )
                )
                rerun_arguments = self._systematisation_rerun_arguments(
                    summary=summary_value,
                    intent=intent_value,
                    framings=framing_values,
                    anchors=anchor_values,
                    rationale=rationale_value,
                    shared_additions=shared_addition_specs,
                    shared_removals=shared_removal_specs,
                    shared_context_summary=shared_context_summary_value,
                    default_stance=default_stance,
                    revision_type=revision_type,
                    included_graphs=included_graphs,
                    created_at=created_at,
                    created_by=created_by,
                    supporting_observations=supporting_observations,
                    supporting_claims=supporting_claims,
                    supporting_patterns=supporting_patterns,
                    evidence=evidence,
                    alternative_to=alternative_to,
                    profile_route_sources=profile_route_source_values,
                    validation_scope=validation_scope,
                )
                warning_suggested_actions.append(
                    SuggestedNextAction(
                        tool="doxabase.stage_systematisation",
                        args=rerun_arguments,
                        reason="The first framing did not route to apply review, "
                            "but later framings default-linked to it as "
                            "alternatives. Rerun with link_alternatives=False "
                            "so diagnostic and ready framings can be reviewed "
                            "without anchoring ready siblings to a failed first "
                            "framing.",
                    )
                )
        suggested_next_actions = [
            *warning_suggested_actions,
            *suggested_next_actions,
        ]
        return SystematisationDraftRecord(
            result_kind="systematisation_draft",
            summary=summary_value,
            intent=intent_value,
            anchors=anchor_values,
            profile_route_source_count=len(recorded_profile_route_sources),
            warnings=warnings,
            structured_warnings=structured_warnings,
            framings=framing_records,
            staged_revisions=staged_revisions,
            next_action_queue=next_action_queue,
            next_action_queue_items=bundle_summary.next_action_queue_items,
            next_action_queue_item_counts=(
                bundle_summary.next_action_queue_item_counts
            ),
            choose_one_groups=bundle_summary.choose_one_groups,
            choose_one_group_count=len(bundle_summary.choose_one_groups),
            semantic_review_required_queue_counts=(
                bundle_summary.semantic_review_required_queue_counts
            ),
            suggested_next_actions=suggested_next_actions,
        )
    def _systematisation_shared_patch_summaries(
        self,
        staged_revisions: list[StagedGraphRevisionRecord],
    ) -> list[SystematisationSharedPatchSummary]:
        if not staged_revisions:
            return []
        shared_role = self.expand_iri("rc:SharedContextPatch")
        summaries: list[SystematisationSharedPatchSummary] = []
        for patch in staged_revisions[0].patches:
            if (
                patch.patch_role != shared_role
                or patch.target_graph not in {"ontology", "shapes"}
            ):
                continue
            summaries.append(
                SystematisationSharedPatchSummary(
                    target_graph=patch.target_graph,
                    operation=patch.operation,
                    operation_label=self._label_for_resource(patch.operation),
                    patch_role=patch.patch_role,
                    patch_role_label=self._label_for_resource(patch.patch_role),
                    sequence_index=patch.sequence_index,
                    triple_count=patch.triple_count,
                    count_basis=patch.count_basis,
                    format=patch.format,
                )
            )
        return summaries
    def _systematisation_shared_patch_sources_to_move(
        self,
        shared_additions: list[dict[str, str]],
        shared_removals: list[dict[str, str]],
        shared_semantic_context_graphs: list[str],
    ) -> list[dict[str, Any]]:
        semantic_graphs = set(shared_semantic_context_graphs)
        sources: list[dict[str, Any]] = []
        for source_argument, operation, specs in (
            ("shared_additions", "addition", shared_additions),
            ("shared_removals", "removal", shared_removals),
        ):
            for source_index, spec in enumerate(specs):
                graph_value = str(
                    spec.get("graph")
                    or spec.get("target_graph")
                    or spec.get("targetGraph")
                    or ""
                ).strip()
                graph_names = self._graph_names_for_export([graph_value])
                if len(graph_names) != 1:
                    continue
                graph = graph_names[0]
                if graph not in semantic_graphs:
                    continue
                sources.append(
                    {
                        "source_argument": source_argument,
                        "source_index": source_index,
                        "operation": operation,
                        "graph": graph,
                    }
                )
        return sources
    def _systematisation_rerun_arguments(
        self,
        *,
        summary: str,
        intent: str,
        framings: Iterable[Mapping[str, Any]],
        anchors: list[str],
        rationale: str | None,
        shared_additions: Iterable[Mapping[str, str]],
        shared_removals: Iterable[Mapping[str, str]],
        shared_context_summary: str | None,
        default_stance: str,
        revision_type: str,
        included_graphs: Iterable[str] | str | None,
        created_at: datetime | str | None,
        created_by: str | None,
        supporting_observations: Iterable[str] | str | None,
        supporting_claims: Iterable[str] | str | None,
        supporting_patterns: Iterable[str] | str | None,
        evidence: Iterable[str] | str | None,
        alternative_to: str | None,
        profile_route_sources: Iterable[Mapping[str, Any]],
        validation_scope: str,
    ) -> dict[str, Any]:
        arguments: dict[str, Any] = {
            "summary": summary,
            "intent": intent,
            "framings": [copy.deepcopy(dict(framing)) for framing in framings],
            "link_alternatives": False,
            "validation_scope": validation_scope,
        }
        if anchors:
            arguments["anchors"] = anchors
        if rationale is not None:
            arguments["rationale"] = rationale
        if shared_additions:
            arguments["shared_additions"] = [
                self._rerun_patch_arguments(spec) for spec in shared_additions
            ]
        if shared_removals:
            arguments["shared_removals"] = [
                self._rerun_patch_arguments(spec) for spec in shared_removals
            ]
        if shared_context_summary is not None:
            arguments["shared_context_summary"] = shared_context_summary
        if default_stance != "rc:ExploratoryHunch":
            arguments["default_stance"] = default_stance
        if revision_type != "rc:StagedRevision":
            arguments["revision_type"] = revision_type
        if included_graphs is not None:
            arguments["included_graphs"] = self._string_values(
                "included_graphs",
                included_graphs,
            )
        if created_at is not None:
            arguments["created_at"] = (
                created_at.isoformat()
                if isinstance(created_at, datetime)
                else created_at
            )
        if created_by is not None:
            arguments["created_by"] = created_by
        if supporting_observations is not None:
            arguments["supporting_observations"] = self._string_values(
                "supporting_observations",
                supporting_observations
            )
        if supporting_claims is not None:
            arguments["supporting_claims"] = self._string_values(
                "supporting_claims",
                supporting_claims,
            )
        if supporting_patterns is not None:
            arguments["supporting_patterns"] = self._string_values(
                "supporting_patterns",
                supporting_patterns,
            )
        if evidence is not None:
            arguments["evidence"] = self._string_values("evidence", evidence)
        if alternative_to is not None:
            arguments["alternative_to"] = alternative_to
        if profile_route_sources:
            arguments["profile_route_sources"] = [
                copy.deepcopy(dict(source)) for source in profile_route_sources
            ]
        return arguments
    @staticmethod
    def _rerun_patch_arguments(spec: Mapping[str, str]) -> dict[str, str]:
        return {
            str(key): str(value)
            for key, value in spec.items()
            if key != "patch_role"
        }
    def _systematisation_draft_routing(
        self,
        staged_revisions: list[StagedGraphRevisionRecord],
    ) -> tuple[StagedGraphRevisionBundleSummary, list[SuggestedNextAction]]:
        revision_iris = [revision.revision_iri for revision in staged_revisions]
        descriptions = [
            self.describe_staged_revision(revision_iri)
            for revision_iri in revision_iris
        ]
        apply_checks = [
            self._staged_revision_apply_check_for_export(description)
            for description in descriptions
        ]
        revision_summaries = self._staged_revisions_export_summaries(
            descriptions,
            apply_checks=apply_checks,
        )
        bundle_summary = self._staged_revisions_bundle_summary(
            revision_summaries,
            descriptions=descriptions,
            snapshot_evidence=(
                self._staged_revisions_snapshot_evidence_summary(descriptions)
            ),
        )
        return (
            bundle_summary,
            self._systematisation_draft_next_actions(revision_iris),
        )
    def _systematisation_draft_next_actions(
        self,
        revision_iris: list[str],
    ) -> list[SuggestedNextAction]:
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

        add_action(
            "export_staged_revisions",
            {
                "revision_iris": revision_iris,
                "path": self._suggested_review_export_path(
                    "systematisation-review",
                    revision_iris,
                ),
                "fail_on_sensitive": True,
            },
            (
                "Write a grouped Markdown review bundle before choosing among "
                "the staged framings. The suggested call blocks if "
                "scanner-matching content appears before export."
            ),
        )
        for revision_iri in revision_iris:
            add_action(
                "check_staged_revision_apply",
                {"iri": revision_iri},
                (
                    "Recheck live apply status and follow the returned "
                    "next_action before applying, repairing, or restaging."
                ),
            )
        return actions
    def _staged_description_shared_semantic_context_patch_summaries(
        self,
        description: StagedGraphRevisionDescription,
    ) -> list[SystematisationSharedPatchSummary]:
        shared_role = self.expand_iri("rc:SharedContextPatch")
        summaries: list[SystematisationSharedPatchSummary] = []
        for patch in description.patches:
            if (
                patch.patch_role != shared_role
                or patch.target_graph not in {"ontology", "shapes"}
                or patch.operation is None
                or patch.count_basis is None
                or patch.format is None
                or patch.sequence_index is None
                or patch.triple_count is None
            ):
                continue
            summaries.append(
                SystematisationSharedPatchSummary(
                    target_graph=patch.target_graph,
                    operation=patch.operation,
                    operation_label=patch.operation_label,
                    patch_role=patch.patch_role,
                    patch_role_label=patch.patch_role_label,
                    sequence_index=patch.sequence_index,
                    triple_count=patch.triple_count,
                    count_basis=patch.count_basis,
                    format=patch.format,
                )
            )
        return summaries
    def _staged_revisions_shared_semantic_context_patch_summaries(
        self,
        descriptions: list[StagedGraphRevisionDescription],
    ) -> list[SystematisationSharedPatchSummary]:
        seen: set[tuple[str, str, str, int, int, str, str]] = set()
        summaries: list[SystematisationSharedPatchSummary] = []
        for description in descriptions:
            for summary in (
                self._staged_description_shared_semantic_context_patch_summaries(
                    description
                )
            ):
                key = (
                    summary.target_graph,
                    summary.operation,
                    summary.patch_role,
                    summary.sequence_index,
                    summary.triple_count,
                    summary.count_basis,
                    summary.format,
                )
                if key in seen:
                    continue
                seen.add(key)
                summaries.append(summary)
        return summaries
    def _staged_revisions_shared_semantic_context_warnings(
        self,
        *,
        affected_revision_iris: list[str],
        shared_context_graphs: list[str],
        shared_context_patch_summaries: list[SystematisationSharedPatchSummary],
        fallback_revision_iris: list[str],
    ) -> list[SharedSemanticContextBundleWarning]:
        if (
            len(affected_revision_iris) < 2
            or not shared_context_graphs
            or not fallback_revision_iris
        ):
            return []
        shared_graph_summary = ", ".join(shared_context_graphs)
        message = (
            "Shared ontology or shapes context patches are present across this "
            "staged bundle, including fallback alternatives. Shared graph roles: "
            f"{shared_graph_summary}. Inspect the shared context before applying "
            "or restage alternatives without shared semantic context when only "
            "some framings should carry provisional vocabulary or validation shapes."
        )
        return [
            SharedSemanticContextBundleWarning(
                warning_code="shared_semantic_context_applies_to_all_framings",
                message=message,
                affected_revision_iris=affected_revision_iris,
                shared_context_graphs=shared_context_graphs,
                shared_context_patch_summaries=shared_context_patch_summaries,
                fallback_revision_iris_with_shared_semantic_context=(
                    fallback_revision_iris
                ),
                suggested_action=(
                    "inspect_shared_context_before_apply_or_restage_fallbacks"
                ),
            )
        ]
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
    def draft_systematisation_shared_context_rerun(
        self,
        revision_iris: Iterable[str] | str,
        shared_context_target_revision_iris: Iterable[str] | str,
        *,
        summary: str | None = None,
        intent: str | None = None,
        rationale: str | None = None,
        link_alternatives: bool = False,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
    ) -> SystematisationSharedContextRerunDraft:
        source_iris = list(
            dict.fromkeys(
                self._string_values("revision_iris", revision_iris, required=True)
            )
        )
        target_iris = list(
            dict.fromkeys(
                self._string_values(
                    "shared_context_target_revision_iris",
                    shared_context_target_revision_iris,
                    required=True,
                )
            )
        )
        source_set = set(source_iris)
        unknown_targets = [iri for iri in target_iris if iri not in source_set]
        if unknown_targets:
            raise DoxaBaseError(
                "shared_context_target_revision_iris must be a subset of "
                "revision_iris; unknown target(s): "
                + ", ".join(unknown_targets)
            )

        descriptions = [self.describe_staged_revision(iri) for iri in source_iris]
        alternative_memberships = self._alternative_set_membership_by_iri(
            (
                (
                    description.iri,
                    (
                        description.alternative_to.iri
                        if description.alternative_to is not None
                        else None
                    ),
                    description.alternative_gate.current_alternative_to,
                )
                for description in descriptions
            )
        )
        if alternative_memberships:
            description_by_iri = {
                description.iri: description for description in descriptions
            }
            ordered_descriptions: list[StagedGraphRevisionDescription] = []
            seen_description_iris: set[str] = set()
            for description in descriptions:
                if description.iri in seen_description_iris:
                    continue
                membership = alternative_memberships.get(description.iri)
                if membership is None:
                    ordered_descriptions.append(description)
                    seen_description_iris.add(description.iri)
                    continue
                member_iris, source_iri, _ = membership
                ordered_member_iris = [
                    source_iri,
                    *(iri for iri in member_iris if iri != source_iri),
                ]
                for member_iri in ordered_member_iris:
                    if member_iri in seen_description_iris:
                        continue
                    member_description = description_by_iri.get(member_iri)
                    if member_description is None:
                        continue
                    ordered_descriptions.append(member_description)
                    seen_description_iris.add(member_iri)
            descriptions = ordered_descriptions
            alternative_memberships = self._alternative_set_membership_by_iri(
                (
                    (
                        description.iri,
                        (
                            description.alternative_to.iri
                            if description.alternative_to is not None
                            else None
                        ),
                        description.alternative_gate.current_alternative_to,
                    )
                    for description in descriptions
                )
            )
        shared_role = self.expand_iri("rc:SharedContextPatch")
        semantic_shared_graphs = {"ontology", "shapes"}
        shared_patch_keys: set[tuple[str, str, str, str]] = set()
        shared_patch_summaries = (
            self._staged_revisions_shared_semantic_context_patch_summaries(
                descriptions
            )
        )
        shared_shapes_context = any(
            summary.target_graph == "shapes" for summary in shared_patch_summaries
        )
        for description in descriptions:
            for patch in description.patches:
                if (
                    patch.patch_role == shared_role
                    and patch.target_graph in semantic_shared_graphs
                ):
                    shared_patch_keys.add(self._staged_patch_identity(patch))
        if not shared_patch_keys:
            raise DoxaBaseError(
                "Selected revisions do not contain shared ontology/shapes "
                "context patches."
            )

        summary_value = (
            summary.strip()
            if summary is not None and summary.strip()
            else self._systematisation_summary_from_descriptions(descriptions)
        )
        intent_value = (
            intent.strip()
            if intent is not None and intent.strip()
            else self._common_systematisation_rationale_field(
                descriptions,
                "Systematisation intent:",
            )
            or (
                "Rerun staged systematisation with shared semantic context "
                "moved into selected framing patches."
            )
        )
        rationale_value = (
            rationale.strip()
            if rationale is not None and rationale.strip()
            else self._common_systematisation_rationale_field(
                descriptions,
                "Overall rationale:",
            )
        )
        validation_scope_value = (
            validation_scope
            or self._common_systematisation_validation_scope(descriptions)
            or "all"
        )

        stage_args: dict[str, Any] = {
            "summary": summary_value,
            "intent": intent_value,
            "framings": [],
            "link_alternatives": link_alternatives,
            "validation_scope": validation_scope_value,
        }
        anchors = self._ordered_resource_summary_iris(
            summary
            for description in descriptions
            for summary in description.revision_anchors
        )
        if anchors:
            stage_args["anchors"] = anchors
        if rationale_value:
            stage_args["rationale"] = rationale_value
        supporting_observations = self._ordered_resource_summary_iris(
            summary
            for description in descriptions
            for summary in description.supporting_observations
        )
        supporting_claims = self._ordered_resource_summary_iris(
            summary
            for description in descriptions
            for summary in description.supporting_claims
        )
        supporting_patterns = self._ordered_resource_summary_iris(
            summary
            for description in descriptions
            for summary in description.supporting_patterns
        )
        evidence = self._ordered_resource_summary_iris(
            summary for description in descriptions for summary in description.evidence
        )
        if supporting_observations:
            stage_args["supporting_observations"] = supporting_observations
        if supporting_claims:
            stage_args["supporting_claims"] = supporting_claims
        if supporting_patterns:
            stage_args["supporting_patterns"] = supporting_patterns
        if evidence:
            stage_args["evidence"] = evidence

        target_set = set(target_iris)
        source_framing_index_by_iri = {
            description.iri: index
            for index, description in enumerate(descriptions, start=1)
        }
        framing_records: list[SystematisationSharedContextRerunFraming] = []
        framing_args: list[dict[str, Any]] = []
        warnings: list[str] = []
        for description in descriptions:
            receives_shared_context = description.iri in target_set
            if (
                shared_shapes_context
                and not receives_shared_context
                and description.validation_conforms is False
            ):
                warnings.append(
                    f"Source revision {description.iri} had staged validation "
                    "failures and is not receiving moved shared shapes; the "
                    "rerun may become mechanically ready because that validation "
                    "context was removed. Omit it from the rerun or record an "
                    "explicit discarded review decision if it was only a "
                    "diagnostic framing."
                )
            additions: list[dict[str, str]] = []
            removals: list[dict[str, str]] = []
            moved_shared_patch_count = 0
            framing_patch_count = 0
            for patch in description.patches:
                is_semantic_shared_patch = (
                    patch.patch_role == shared_role
                    and patch.target_graph in semantic_shared_graphs
                    and self._staged_patch_identity(patch) in shared_patch_keys
                )
                if is_semantic_shared_patch and not receives_shared_context:
                    continue
                if is_semantic_shared_patch:
                    moved_shared_patch_count += 1
                else:
                    framing_patch_count += 1
                self._append_patch_description_spec(
                    patch,
                    additions=additions,
                    removals=removals,
                )
            label = self._systematisation_framing_label(description)
            framing: dict[str, Any] = {"label": label}
            membership = alternative_memberships.get(description.iri)
            if not link_alternatives and membership is not None:
                _, source_iri, role = membership
                source_framing_index = source_framing_index_by_iri.get(source_iri)
                current_framing_index = len(framing_args) + 1
                if (
                    role != "source"
                    and source_framing_index is not None
                    and source_framing_index < current_framing_index
                ):
                    framing["alternative_to_framing_index"] = source_framing_index
            if additions:
                framing["additions"] = additions
            if removals:
                framing["removals"] = removals
            if description.revision_stance:
                framing["stance"] = description.revision_stance
            framing_rationale = self._systematisation_rationale_field(
                description.rationale,
                "Framing rationale:",
            )
            if framing_rationale:
                framing["rationale"] = framing_rationale
            if description.review_note:
                framing["review_note"] = description.review_note
            if description.review_recommendation:
                framing["review_recommendation"] = description.review_recommendation
            if (
                description.validation_scope
                and description.validation_scope != validation_scope_value
            ):
                framing["validation_scope"] = description.validation_scope
            framing_args.append(framing)
            framing_records.append(
                SystematisationSharedContextRerunFraming(
                    source_revision_iri=description.iri,
                    label=label,
                    receives_shared_context=receives_shared_context,
                    moved_shared_patch_count=moved_shared_patch_count,
                    framing_patch_count=framing_patch_count,
                    target_graphs=sorted(set(description.changed_graphs)),
                    validation_scope=description.validation_scope,
                )
            )

        stage_args["framings"] = framing_args
        if len(target_iris) == len(source_iris):
            warnings.append(
                "All source framings were selected to keep shared semantic "
                "context. The generated rerun removes the shared patch role, "
                "but ontology/shapes context will still be present on every "
                "framing."
            )
        action = SuggestedNextAction(
                     tool="doxabase.stage_systematisation",
                     args=stage_args,
                     reason="Read-only draft: rerun the systematisation with shared "
                "ontology/shapes patches copied into only the selected framing "
                "patches, avoiding manual Turtle reconstruction.",
                 )
        return SystematisationSharedContextRerunDraft(
            result_kind="systematisation_shared_context_rerun_draft",
            helper="draft_systematisation_shared_context_rerun",
            mode="read_only_draft",
            source_revision_iris=source_iris,
            shared_context_target_revision_iris=target_iris,
            shared_context_graphs=sorted(
                {summary.target_graph for summary in shared_patch_summaries}
            ),
            shared_context_patch_summaries=shared_patch_summaries,
            framings=framing_records,
            stage_systematisation_arguments=stage_args,
            suggested_next_actions=[action],
            warnings=warnings,
            note=(
                "Review the selected target framings semantically before "
                "calling stage_systematisation. This helper drafts arguments "
                "only; it does not stage, restage, apply, or edit RDF."
            ),
        )
    def _append_patch_description_spec(
        self,
        patch: StagedGraphPatchDescription,
        *,
        additions: list[dict[str, str]],
        removals: list[dict[str, str]],
    ) -> None:
        addition_operation = self.expand_iri("rc:AdditionPatch")
        removal_operation = self.expand_iri("rc:RemovalPatch")
        spec = {
            "graph": self._required_staged_patch_target_graph(patch),
            "content": self._required_staged_patch_field(
                patch,
                "content",
                patch.content,
            ),
            "format": self._required_staged_patch_field(
                patch,
                "format",
                patch.format,
            ),
        }
        operation = self._required_staged_patch_field(
            patch,
            "operation",
            patch.operation,
        )
        if operation == addition_operation:
            additions.append(spec)
            return
        if operation == removal_operation:
            removals.append(spec)
            return
        raise DoxaBaseError(
            f"Cannot draft systematisation rerun for unsupported patch "
            f"operation '{operation}'"
        )
    @staticmethod
    def _systematisation_rationale_field(
        rationale: str | None,
        field_prefix: str,
    ) -> str | None:
        if not rationale:
            return None
        for line in rationale.splitlines():
            stripped = line.strip()
            if stripped.startswith(field_prefix):
                return stripped[len(field_prefix) :].strip() or None
        return None
    def _common_systematisation_rationale_field(
        self,
        descriptions: Iterable[StagedGraphRevisionDescription],
        field_prefix: str,
    ) -> str | None:
        values = [
            value
            for value in (
                self._systematisation_rationale_field(
                    description.rationale,
                    field_prefix,
                )
                for description in descriptions
            )
            if value
        ]
        if not values:
            return None
        first = values[0]
        if all(value == first for value in values):
            return first
        return None
    @staticmethod
    def _common_systematisation_validation_scope(
        descriptions: Iterable[StagedGraphRevisionDescription],
    ) -> str | None:
        scopes = [
            description.validation_scope
            for description in descriptions
            if description.validation_scope
        ]
        if not scopes:
            return None
        first = scopes[0]
        if all(scope == first for scope in scopes):
            return first
        return None
    def _systematisation_framing_label(
        self,
        description: StagedGraphRevisionDescription,
    ) -> str:
        label = self._systematisation_rationale_field(
            description.rationale,
            "Framing:",
        )
        if label:
            return label
        if description.summary and ": " in description.summary:
            return description.summary.rsplit(": ", 1)[1]
        return description.summary or description.iri
    @staticmethod
    def _systematisation_summary_from_descriptions(
        descriptions: list[StagedGraphRevisionDescription],
    ) -> str:
        prefixes = [
            description.summary.rsplit(": ", 1)[0]
            for description in descriptions
            if description.summary and ": " in description.summary
        ]
        if prefixes:
            first = prefixes[0]
            if len(prefixes) == len(descriptions) and all(
                prefix == first for prefix in prefixes
            ):
                return first
        if descriptions and descriptions[0].summary:
            return f"{descriptions[0].summary} shared-context rerun"
        return "Shared-context systematisation rerun"
