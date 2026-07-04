"""Staged revision review bundles and decisions.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via StagingReviewMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class StagingReviewMixin:
    def record_staged_revision_review_decision(
        self,
        iri: str,
        decision: str,
        rationale: str,
        *,
        summary: str | None = None,
        resolution_revision_iri: str | None = None,
        created_at: datetime | str | None = None,
        created_by: str | None = None,
        review_note: str | None = None,
        review_recommendation: str | None = None,
        allow_mutation_target: bool = False,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
    ) -> StagedRevisionReviewDecisionRecord:
        staged = self.describe_staged_revision(iri)
        existing_resolution = self._staged_review_resolution_for_staged_iri(
            staged.iri
        )
        if existing_resolution is not None:
            raise DoxaBaseError(
                "Staged revision already has a review resolution recorded by "
                f"'{existing_resolution.resolution_revision_iri}'."
            )
        was_current_staged_work = (
            staged.applied_by is None and staged.current_restaged_by is None
        )
        normalized_decision = self._normalize_staged_review_decision(decision)
        decision_iri = self.expand_iri(STAGED_REVIEW_DECISIONS[normalized_decision])
        self._ensure_staged_review_decision(decision_iri)
        check = self.check_staged_revision_apply(
            staged.iri,
            validation_scope=validation_scope,
        )
        if not allow_mutation_target and self._staged_review_decision_targets_mutation(
            staged,
            check,
        ):
            raise DoxaBaseError(
                "Refusing to record a staged review decision for a current "
                "mutation-target row. Review/apply, restage, or repair it, or "
                "pass allow_mutation_target=True when a human or agent has "
                "explicitly decided to close this staged proposal without a "
                "graph mutation."
            )

        rationale_value = rationale.strip()
        if not rationale_value:
            raise DoxaBaseError("rationale must not be empty")
        summary_value = (
            summary.strip()
            if summary is not None and summary.strip()
            else self._staged_review_decision_default_summary(
                staged,
                normalized_decision,
            )
        )
        included_graphs = list(dict.fromkeys(["history", *staged.changed_graphs]))
        revision_record = self.record_graph_revision(
            summary=summary_value,
            rationale=rationale_value,
            changed_graphs=["history"],
            revision_type="rc:StagedRevisionReviewResolution",
            included_graphs=included_graphs,
            revision_iri=resolution_revision_iri,
            created_at=created_at,
            created_by=created_by,
            revision_anchors=[staged.iri],
            validation_scope=check.validation_scope,
            validation_conforms=check.validation_conforms,
            validation_result_count=check.validation_result_count,
            validation_results=check.validation_results,
        )

        metadata = Graph()
        self._bind_prefixes(metadata)
        subject = URIRef(revision_record.revision_iri)
        metadata.add(
            (
                subject,
                URIRef(self.expand_iri("rc:resolvesStagedRevision")),
                URIRef(staged.iri),
            )
        )
        metadata.add(
            (
                subject,
                URIRef(self.expand_iri("rc:stagedRevisionReviewDecision")),
                URIRef(decision_iri),
            )
        )
        self._add_optional_literal(metadata, subject, "rc:reviewNote", review_note)
        self._add_optional_literal(
            metadata,
            subject,
            "rc:reviewRecommendation",
            review_recommendation,
        )
        extra_triples = self._insert_graph("history", metadata)
        suggested_next_actions = self._staged_review_decision_next_actions(
            staged.iri,
            revision_record.revision_iri,
        )
        return StagedRevisionReviewDecisionRecord(
            resolution_revision_iri=revision_record.revision_iri,
            staged_revision_iri=staged.iri,
            decision=normalized_decision,
            decision_iri=decision_iri,
            graph="history",
            triples=revision_record.triples + extra_triples,
            current_application_status=check.status,
            current_stale_resolution_state=check.stale_resolution_state,
            current_next_action=check.next_action,
            closes_current_staged_work=was_current_staged_work,
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[
                action.call for action in suggested_next_actions if action.call
            ],
        )
    def _staged_review_decision_targets_mutation(
        self,
        staged: StagedGraphRevisionDescription,
        check: StagedRevisionApplyCheck,
    ) -> bool:
        if staged.applied_by is not None or staged.current_restaged_by is not None:
            return False
        if check.next_action is None:
            return False
        return check.next_action.queue in {
            "apply_after_review",
            "restage_after_review",
            "repair_or_replace",
        }
    def _staged_review_decision_default_summary(
        self,
        staged: StagedGraphRevisionDescription,
        decision: str,
    ) -> str:
        label = decision.replace("_", " ")
        staged_summary = staged.summary or staged.iri
        return f"Recorded staged revision review decision: {label} - {staged_summary}"
    def _staged_review_decision_next_actions(
        self,
        staged_revision_iri: str,
        resolution_revision_iri: str,
    ) -> list[SuggestedNextAction]:
        actions = [
            SuggestedNextAction(
                action_label="Inspect review decision",
                tool_name="describe_graph_revision",
                mcp_tool_name="doxabase.describe_graph_revision",
                arguments={"iri": resolution_revision_iri},
                reason=(
                    "Inspect the durable history event that recorded the staged "
                    "review decision."
                ),
                call=self._suggested_call_string(
                    "describe_graph_revision",
                    {"iri": resolution_revision_iri},
                ),
            ),
            SuggestedNextAction(
                action_label="Inspect resolved staged revision",
                tool_name="describe_staged_revision",
                mcp_tool_name="doxabase.describe_staged_revision",
                arguments={
                    "iri": staged_revision_iri,
                    "include_current_apply_check": True,
                },
                reason=(
                    "Inspect the resolved staged row with its live apply check "
                    "and review_resolution summary."
                ),
                call=self._suggested_call_string(
                    "describe_staged_revision",
                    {
                        "iri": staged_revision_iri,
                        "include_current_apply_check": True,
                    },
                ),
            ),
            SuggestedNextAction(
                action_label="Replan current staged frontier",
                tool_name="plan_staged_revision_recovery",
                mcp_tool_name="doxabase.plan_staged_revision_recovery",
                arguments={"current_staged_work_only": True},
                reason=(
                    "The resolved staged row is no longer current staged work; "
                    "replan before choosing the next unattended mutation."
                ),
                call=self._suggested_call_string(
                    "plan_staged_revision_recovery",
                    {"current_staged_work_only": True},
                ),
            ),
        ]
        return actions
    def export_profile_insight_review_bundle(
        self,
        dataset_iri: str,
        evidence_iri: str,
        path: str | Path,
        *,
        revision_iris: Iterable[str] | str | None = None,
        include_current_staged_work: bool = True,
        current_staged_work_limit: int = 100,
        include_applied_staged_sources: bool = True,
        applied_staged_source_limit: int = 100,
        title: str | None = None,
        executive_summary: str | None = None,
        format: TypingLiteral["markdown"] = "markdown",
        overwrite: bool = False,
        fail_on_sensitive: bool = False,
    ) -> ProfileInsightReviewBundleRecord:
        if format != "markdown":
            raise DoxaBaseError(
                "Only markdown profile insight review exports are supported"
            )
        if current_staged_work_limit < 1:
            raise DoxaBaseError("current_staged_work_limit must be at least 1")
        if applied_staged_source_limit < 1:
            raise DoxaBaseError("applied_staged_source_limit must be at least 1")
        apply_check_cache: dict[
            StagedApplyCheckCacheKey,
            StagedRevisionApplyCheck,
        ] = {}
        profile = self.describe_profile_run(
            dataset_iri=dataset_iri,
            evidence_iri=evidence_iri,
            limit=None,
        )
        with self._scoped_staged_apply_check_cache(apply_check_cache):
            draft = self.draft_profile_map_updates(
                dataset_iri=dataset_iri,
                evidence_iri=evidence_iri,
            )
        evidence_value = self.expand_iri(evidence_iri)
        profile_observation_iris = list(dict.fromkeys(profile.profile_observation_iris))
        profile_observation_set = set(profile_observation_iris)
        anchor_seed_iris = self._profile_insight_anchor_seed_iris(profile, draft)
        related_pattern_iris = self._profile_insight_related_pattern_iris(
            profile_observation_set,
            anchor_seed_iris,
            draft,
        )
        related_pattern_set = set(related_pattern_iris)
        profile_route_sources = self._profile_insight_route_sources(draft)

        candidates: list[ProfileInsightReviewCandidate] = []
        seen_revision_iris: set[str] = set()

        with self._scoped_staged_apply_check_cache(apply_check_cache):
            for revision_iri in self._string_values("revision_iris", revision_iris):
                description = self.describe_staged_revision(revision_iri)
                candidate = self._profile_insight_review_candidate(
                    description,
                    evidence_iri=evidence_value,
                    profile_observation_iris=profile_observation_set,
                    related_pattern_iris=related_pattern_set,
                    anchor_seed_iris=anchor_seed_iris,
                    profile_route_sources=profile_route_sources,
                    explicit=True,
                )
                candidates.append(candidate)
                seen_revision_iris.add(candidate.revision_iri)

        warnings: list[str] = []
        if include_current_staged_work:
            with self._scoped_staged_apply_check_cache(apply_check_cache):
                listing = self.list_graph_revisions(
                    current_staged_work_only=True,
                    limit=current_staged_work_limit,
                )
            if listing.total_count > listing.returned_count:
                warnings.append(
                    "Only the first "
                    f"{listing.returned_count} of {listing.total_count} current "
                    "staged revisions were scanned; rerun with a higher "
                    "current_staged_work_limit if profile-related revisions may "
                    "have been omitted."
                )
            with self._scoped_staged_apply_check_cache(apply_check_cache):
                for item in listing.revisions:
                    if item.iri in seen_revision_iris or not item.has_patch_payload:
                        continue
                    description = self.describe_staged_revision(item.iri)
                    candidate = self._profile_insight_review_candidate(
                        description,
                        evidence_iri=evidence_value,
                        profile_observation_iris=profile_observation_set,
                        related_pattern_iris=related_pattern_set,
                        anchor_seed_iris=anchor_seed_iris,
                        profile_route_sources=profile_route_sources,
                        explicit=False,
                    )
                    if not candidate.relation_reasons:
                        continue
                    candidates.append(candidate)
                    seen_revision_iris.add(candidate.revision_iri)

        if include_applied_staged_sources:
            applied_source_iris = self._profile_insight_applied_source_candidate_iris(
                evidence_iri=evidence_value,
                profile_observation_iris=profile_observation_set,
                related_pattern_iris=related_pattern_set,
                anchor_seed_iris=anchor_seed_iris,
            )
            if len(applied_source_iris) > applied_staged_source_limit:
                warnings.append(
                    "Only the first "
                    f"{applied_staged_source_limit} of {len(applied_source_iris)} "
                    "matched already-applied staged sources were scanned; rerun with a "
                    "higher applied_staged_source_limit if older profile-related "
                    "applied sources may have been omitted."
                )
            with self._scoped_staged_apply_check_cache(apply_check_cache):
                for applied_source_iri in applied_source_iris[
                    :applied_staged_source_limit
                ]:
                    if applied_source_iri in seen_revision_iris:
                        continue
                    description = self.describe_staged_revision(applied_source_iri)
                    candidate = self._profile_insight_review_candidate(
                        description,
                        evidence_iri=evidence_value,
                        profile_observation_iris=profile_observation_set,
                        related_pattern_iris=related_pattern_set,
                        anchor_seed_iris=anchor_seed_iris,
                        profile_route_sources=profile_route_sources,
                        explicit=False,
                    )
                    if not candidate.relation_reasons:
                        continue
                    candidates.append(candidate)
                    seen_revision_iris.add(candidate.revision_iri)

        candidate_revision_iris = [candidate.revision_iri for candidate in candidates]
        open_profile_review_lanes = self._profile_insight_open_review_lanes(
            profile_route_sources,
            candidates,
        )
        candidates = self._profile_insight_demote_safe_candidates_for_open_lanes(
            candidates,
            open_profile_review_lanes,
        )
        (
            closed_semantic_moves,
            remaining_semantic_moves,
            semantic_move_closure_summary,
        ) = self._profile_insight_semantic_move_closure(
            candidates,
            open_profile_review_lanes,
        )
        (
            closed_route_step_keys,
            remaining_route_step_keys,
        ) = self._profile_insight_route_step_closure(
            candidates,
            open_profile_review_lanes,
        )
        (
            semantic_apply_gate_summary,
            bulk_apply_allowed,
            safe_single_apply_candidate_revision_iris,
            semantic_apply_gate_counts,
            semantic_apply_gate_blocking_reasons,
        ) = self._profile_insight_semantic_apply_gate_summary(
            candidates,
            open_profile_review_lanes,
        )
        executor_decision_summary = (
            self._profile_insight_executor_decision_summary(
                candidates=candidates,
                open_profile_review_lanes=open_profile_review_lanes,
                semantic_apply_gate_summary=semantic_apply_gate_summary,
                bulk_apply_allowed=bulk_apply_allowed,
                safe_single_apply_candidate_revision_iris=(
                    safe_single_apply_candidate_revision_iris
                ),
                semantic_apply_gate_counts=semantic_apply_gate_counts,
                semantic_apply_gate_blocking_reasons=(
                    semantic_apply_gate_blocking_reasons
                ),
            )
        )
        export: StagedGraphRevisionsExportRecord | None = None
        if candidate_revision_iris:
            with self._scoped_staged_apply_check_cache(apply_check_cache):
                export = self.export_staged_revisions(
                    candidate_revision_iris,
                    path,
                    title=title
                    or self._profile_insight_review_title(profile.dataset),
                    executive_summary=self._profile_insight_review_executive_summary(
                        profile.dataset,
                        evidence_value,
                        candidates,
                        open_profile_review_lanes=open_profile_review_lanes,
                        closed_semantic_moves=closed_semantic_moves,
                        remaining_semantic_moves=remaining_semantic_moves,
                        closed_route_step_keys=closed_route_step_keys,
                        remaining_route_step_keys=remaining_route_step_keys,
                        semantic_move_closure_summary=(
                            semantic_move_closure_summary
                        ),
                        semantic_apply_gate_summary=(
                            semantic_apply_gate_summary
                        ),
                        executive_summary=executive_summary,
                    ),
                    format=format,
                    overwrite=overwrite,
                    fail_on_sensitive=fail_on_sensitive,
                )
        else:
            warnings.append(
                "No staged revisions linked to this profile run were found; "
                "stage profile map updates, metric promotions, or caveat "
                "alternatives before exporting a profile insight review bundle."
            )

        return ProfileInsightReviewBundleRecord(
            result_kind="profile_insight_review_bundle",
            dataset=profile.dataset,
            evidence=profile.evidence,
            evidence_iri=evidence_value,
            profile_observation_iris=profile_observation_iris,
            related_pattern_iris=related_pattern_iris,
            candidate_revision_iris=candidate_revision_iris,
            candidate_count=len(candidates),
            candidates=candidates,
            open_profile_review_lanes=open_profile_review_lanes,
            open_profile_review_lane_count=len(open_profile_review_lanes),
            closed_semantic_moves=closed_semantic_moves,
            remaining_semantic_moves=remaining_semantic_moves,
            closed_route_step_keys=closed_route_step_keys,
            remaining_route_step_keys=remaining_route_step_keys,
            semantic_move_closure_summary=semantic_move_closure_summary,
            export=export,
            warnings=warnings,
            review_note=(
                "Export groups current staged revisions and already-applied "
                "staged sources connected to the profile run by evidence, profile "
                "observations, supporting patterns, or profile-derived anchors. "
                "Follow remaining draft advisory or conflict lanes separately if "
                "expected scalar conflict, metric, or type review revisions are "
                "not staged yet."
            ),
            profile_quality_summary=draft.profile_quality_summary,
            sampled_evidence_caution=draft.sampled_evidence_caution,
            semantic_apply_gate_summary=semantic_apply_gate_summary,
            bulk_apply_allowed=bulk_apply_allowed,
            safe_single_apply_candidate_revision_iris=(
                safe_single_apply_candidate_revision_iris
            ),
            semantic_apply_gate_counts=semantic_apply_gate_counts,
            semantic_apply_gate_blocking_reasons=(
                semantic_apply_gate_blocking_reasons
            ),
            executor_decision_summary=executor_decision_summary,
            decision=(
                export.decision if export is not None else "clean_by_scanner_only"
            ),
            scanner_clean=export.scanner_clean if export is not None else True,
            would_block_sensitive_export=(
                export.would_block_sensitive_export if export is not None else False
            ),
            sensitive_literal_count=(
                export.sensitive_literal_count if export is not None else 0
            ),
            privacy_warnings=(
                export.privacy_warnings if export is not None else []
            ),
            shareability_hints=(
                export.shareability_hints if export is not None else []
            ),
            shareability_hint_count=(
                export.shareability_hint_count if export is not None else 0
            ),
            returned_shareability_hint_count=(
                export.returned_shareability_hint_count
                if export is not None
                else 0
            ),
            omitted_shareability_hint_count=(
                export.omitted_shareability_hint_count
                if export is not None
                else 0
            ),
            shareability_hint_matches=(
                export.shareability_hint_matches if export is not None else []
            ),
            artifact_disposition=(
                export.artifact_disposition
                if export is not None
                else DEFAULT_ARTIFACT_DISPOSITION
            ),
            git_safe=export.git_safe if export is not None else False,
        )
    def _profile_insight_review_candidate(
        self,
        description: StagedGraphRevisionDescription,
        *,
        evidence_iri: str,
        profile_observation_iris: set[str],
        related_pattern_iris: set[str],
        anchor_seed_iris: set[str],
        profile_route_sources: list[dict[str, Any]],
        explicit: bool,
    ) -> ProfileInsightReviewCandidate:
        matched_evidence = sorted(
            {item.iri for item in description.evidence} & {evidence_iri}
        )
        matched_observations = sorted(
            {item.iri for item in description.supporting_observations}
            & profile_observation_iris
        )
        matched_patterns = sorted(
            {item.iri for item in description.supporting_patterns}
            & related_pattern_iris
        )
        matched_anchors = sorted(
            {item.iri for item in description.revision_anchors} & anchor_seed_iris
        )
        relation_reasons: list[str] = []
        if explicit:
            relation_reasons.append("explicit_revision_iri")
        if matched_evidence:
            relation_reasons.append("shared_profile_evidence")
        if matched_observations:
            relation_reasons.append("supporting_profile_observation")
        if matched_patterns:
            relation_reasons.append("supporting_related_pattern")
        if matched_anchors:
            relation_reasons.append("profile_derived_anchor")
        direct_review_lane = self._profile_insight_candidate_direct_review_lane(
            description
        )
        live_route_sources = [
            self._profile_insight_candidate_route_source(
                source,
                source_origin="live_draft",
                direct_allowed=False,
            )
            for source in profile_route_sources
        ]
        stored_route_sources = [
            self._profile_insight_candidate_route_source(
                source,
                source_origin="stored_revision",
                direct_allowed=True,
            )
            for source in self._stored_profile_insight_route_sources(
                description.iri
            )
        ]
        generated_route_sources = [
            self._profile_insight_candidate_route_source(
                source,
                source_origin="generated_revision",
                direct_allowed=True,
            )
            for source in self._profile_insight_generated_route_sources(
                description,
                evidence_iri=evidence_iri,
                matched_revision_anchor_iris=matched_anchors,
                direct_review_lane=direct_review_lane,
            )
        ]
        candidate_route_sources = self._merge_profile_route_sources(
            stored_route_sources,
            generated_route_sources,
            live_route_sources,
        )
        profile_route_groups = self._profile_insight_candidate_route_groups(
            matched_profile_observation_iris=matched_observations,
            matched_supporting_pattern_iris=matched_patterns,
            matched_revision_anchor_iris=matched_anchors,
            profile_route_sources=candidate_route_sources,
            direct_review_lane=direct_review_lane,
        )
        apply_gate = self._profile_insight_candidate_apply_gate(
            profile_route_groups,
            application_status=(
                self._profile_insight_candidate_application_status(description)
            ),
        )
        return ProfileInsightReviewCandidate(
            revision_iri=description.iri,
            summary=description.summary,
            changed_graphs=description.changed_graphs,
            relation_reasons=relation_reasons,
            profile_route_keys=[
                group["route_group_key"] for group in profile_route_groups
            ],
            profile_route_groups=profile_route_groups,
            matched_evidence_iris=matched_evidence,
            matched_profile_observation_iris=matched_observations,
            matched_supporting_pattern_iris=matched_patterns,
            matched_revision_anchor_iris=matched_anchors,
            explicit=explicit,
            **apply_gate,
        )
    @staticmethod
    def _profile_insight_review_title(dataset: ResourceSummary) -> str:
        label = dataset.label or dataset.iri
        return f"Profile insight review: {label}"
    def _profile_insight_review_executive_summary(
        self,
        dataset: ResourceSummary,
        evidence_iri: str,
        candidates: list[ProfileInsightReviewCandidate],
        *,
        open_profile_review_lanes: list[ProfileInsightOpenReviewLane],
        closed_semantic_moves: list[str],
        remaining_semantic_moves: list[str],
        closed_route_step_keys: list[str],
        remaining_route_step_keys: list[str],
        semantic_move_closure_summary: str,
        semantic_apply_gate_summary: str,
        executive_summary: str | None = None,
    ) -> str:
        label = dataset.label or dataset.iri
        summary = (
            executive_summary.strip()
            if executive_summary is not None and executive_summary.strip()
            else (
                f"Review staged revisions linked to profile evidence "
                f"`{evidence_iri}` for {label}. This bundle is intended to "
                "compare profile map updates, metric vocabulary proposals, "
                "type/caveat alternatives, and other already-staged "
                "profile-derived graph changes before applying any one lane."
            )
        )
        sections: list[str] = []
        closure_markdown = self._profile_insight_semantic_move_closure_markdown(
            closed_semantic_moves=closed_semantic_moves,
            remaining_semantic_moves=remaining_semantic_moves,
            closed_route_step_keys=closed_route_step_keys,
            remaining_route_step_keys=remaining_route_step_keys,
            semantic_move_closure_summary=semantic_move_closure_summary,
            open_profile_review_lanes=open_profile_review_lanes,
        )
        if closure_markdown:
            sections.append(
                f"### Semantic Move Closure\n\n{closure_markdown}"
            )
        apply_gate_markdown = self._profile_insight_apply_gate_markdown(
            candidates,
            semantic_apply_gate_summary=semantic_apply_gate_summary,
        )
        if apply_gate_markdown:
            sections.append(f"### Semantic Apply Gate\n\n{apply_gate_markdown}")
        open_lanes_markdown = self._profile_insight_open_review_lanes_markdown(
            open_profile_review_lanes
        )
        if open_lanes_markdown:
            sections.append(
                f"### Open Profile Review Lanes\n\n{open_lanes_markdown}"
            )
        route_bridge = self._profile_insight_route_bridge_markdown(candidates)
        if route_bridge:
            sections.append(f"### Profile Route Bridge\n\n{route_bridge}")
        if sections:
            return f"{summary}\n\n" + "\n\n".join(sections)
        return summary
    @staticmethod
    def _staged_revisions_choose_one_groups(
        summaries: list[StagedGraphRevisionExportSummary],
    ) -> list[StagedGraphRevisionChooseOneGroup]:
        memberships = DoxaBase._alternative_set_membership_by_iri(
            (
                (
                    summary.revision_iri,
                    summary.alternative_to,
                    summary.current_alternative_to,
                )
                for summary in summaries
            )
        )
        if not memberships:
            return []

        row_by_iri = {
            summary.revision_iri: index
            for index, summary in enumerate(summaries, start=1)
        }
        summary_by_iri = {summary.revision_iri: summary for summary in summaries}
        grouped_keys: list[tuple[str, ...]] = []
        seen: set[tuple[str, ...]] = set()
        for summary in summaries:
            membership = memberships.get(summary.revision_iri)
            if membership is None:
                continue
            member_iris, _, _ = membership
            key = tuple(member_iris)
            if key in seen:
                continue
            seen.add(key)
            grouped_keys.append(key)

        groups: list[StagedGraphRevisionChooseOneGroup] = []
        for group_index, member_iris in enumerate(grouped_keys, start=1):
            source_iri = memberships[member_iris[0]][1]
            source_summary = summary_by_iri.get(source_iri)
            groups.append(
                StagedGraphRevisionChooseOneGroup(
                    group_index=group_index,
                    row_indexes=[
                        row_by_iri[iri] for iri in member_iris if iri in row_by_iri
                    ],
                    revision_iris=list(member_iris),
                    summaries=[
                        summary_by_iri[iri].summary
                        if iri in summary_by_iri
                        else None
                        for iri in member_iris
                    ],
                    alternative_set_source_iri=source_iri,
                    source_row_index=row_by_iri.get(source_iri),
                    source_summary=(
                        source_summary.summary
                        if source_summary is not None
                        else None
                    ),
                    alternative_set_roles=[
                        memberships[iri][2] if iri in memberships else None
                        for iri in member_iris
                    ],
                )
            )
        return groups
    def _staged_revisions_modelling_choice_rows(
        self,
        *,
        summaries: list[StagedGraphRevisionExportSummary],
        descriptions: list[StagedGraphRevisionDescription],
        choose_one_groups: list[StagedGraphRevisionChooseOneGroup],
        next_action_queue_items: list[RevisionNextActionQueueItem],
    ) -> list[StagedGraphRevisionModellingChoiceRow]:
        if not summaries:
            return []
        queue_item_by_row_iri = {
            item.row_iri: item for item in next_action_queue_items
        }
        row_index_by_iri = {
            summary.revision_iri: index
            for index, summary in enumerate(summaries, start=1)
        }
        alternative_role_by_row_index: dict[int, str | None] = {}
        for group in choose_one_groups:
            for revision_iri, role in zip(
                group.revision_iris,
                group.alternative_set_roles,
                strict=True,
            ):
                row_index = row_index_by_iri.get(revision_iri)
                if row_index is not None:
                    alternative_role_by_row_index[row_index] = role

        rows: list[StagedGraphRevisionModellingChoiceRow] = []
        for row_index, (summary, description) in enumerate(
            zip(summaries, descriptions, strict=True),
            start=1,
        ):
            queue_item = queue_item_by_row_iri.get(summary.revision_iri)
            alternative_set_role = (
                queue_item.alternative_set_role
                if queue_item is not None
                else alternative_role_by_row_index.get(row_index)
            ) or alternative_role_by_row_index.get(row_index)
            included_alternative_row = row_index in alternative_role_by_row_index
            modelling_role, role_source, role_reason = (
                self._staged_revisions_modelling_role(
                    summary,
                    queue=queue_item.queue if queue_item is not None else None,
                    alternative_set_role=alternative_set_role,
                )
            )
            support_counts = {
                "observations": len(description.supporting_observations),
                "claims": len(description.supporting_claims),
                "patterns": len(description.supporting_patterns),
                "evidence": len(description.evidence),
                "anchors": len(description.revision_anchors),
            }
            present_support_counts = {
                key: count for key, count in support_counts.items() if count
            }
            support_note = (
                "Support links: "
                + self._staged_revisions_count_summary(present_support_counts)
                if present_support_counts
                else "No linked support or anchors."
            )
            rows.append(
                StagedGraphRevisionModellingChoiceRow(
                    row_index=row_index,
                    revision_iri=summary.revision_iri,
                    summary=summary.summary,
                    modelling_role=modelling_role,
                    role_source=role_source,
                    role_reason=role_reason,
                    queue=queue_item.queue if queue_item is not None else None,
                    apply_status=summary.apply_status,
                    apply_decision=summary.apply_decision,
                    current_validation=summary.current_validation,
                    staged_validation=summary.staged_validation,
                    changed_graphs=summary.changed_graphs,
                    alternative_set_role=alternative_set_role,
                    shared_context_applies=bool(
                        summary.shared_context_patch_count
                        or summary.shared_context_graphs
                    ),
                    shared_context_graphs=summary.shared_context_graphs,
                    support_counts=support_counts,
                    support_note=support_note,
                    recommended_human_action=self._staged_revisions_human_action(
                        summary,
                        included_alternative_row=included_alternative_row,
                    ),
                )
            )
        return rows
    def _staged_revisions_modelling_choice_summary(
        self,
        rows: list[StagedGraphRevisionModellingChoiceRow],
        *,
        choose_one_groups: list[StagedGraphRevisionChooseOneGroup],
    ) -> str | None:
        if not rows:
            return None
        role_counts: dict[str, int] = {}
        shared_context_row_count = 0
        for row in rows:
            role_counts[row.modelling_role] = (
                role_counts.get(row.modelling_role, 0) + 1
            )
            if row.shared_context_applies:
                shared_context_row_count += 1
        parts = [
            (
                f"Review {len(rows)} staged row(s) as modelling choices: "
                + self._staged_revisions_count_summary(role_counts)
                + "."
            )
        ]
        if choose_one_groups:
            parts.append(
                f"Compare {len(choose_one_groups)} choose-one group(s) before "
                "applying candidates."
            )
        if shared_context_row_count:
            parts.append(
                "Shared ontology/shapes context applies to "
                f"{shared_context_row_count} row(s); inspect whether fallback "
                "framings should carry that context before applying."
            )
        return " ".join(parts)
    def _staged_revisions_review_sequence(
        self,
        *,
        summaries: list[StagedGraphRevisionExportSummary],
        next_action_queue_items: list[RevisionNextActionQueueItem],
        post_apply_recheck_revision_iris: list[str],
    ) -> list[StagedGraphRevisionReviewSequenceItem]:
        summary_by_iri = {summary.revision_iri: summary for summary in summaries}
        row_index_by_iri = {
            summary.revision_iri: index
            for index, summary in enumerate(summaries, start=1)
        }
        post_apply_recheck = set(post_apply_recheck_revision_iris)
        phase_order = {
            "inspect_redirects": 0,
            "repair_blockers": 1,
            "restage_stale": 2,
            "review_apply": 3,
            "recheck_after_apply": 4,
            "review_other": 5,
        }
        sequence: list[StagedGraphRevisionReviewSequenceItem] = []

        for item in next_action_queue_items:
            summary = summary_by_iri.get(item.row_iri)
            row_index = row_index_by_iri.get(item.row_iri, 0)
            phase, phase_label = self._staged_revisions_review_sequence_phase(
                item,
                summary,
            )
            sequence.append(
                StagedGraphRevisionReviewSequenceItem(
                    phase=phase,
                    phase_label=phase_label,
                    row_index=row_index,
                    row_iri=item.row_iri,
                    summary=summary.summary if summary is not None else None,
                    queue=item.queue,
                    resolved_target_iri=item.resolved_target_iri,
                    resolved_target_record_kind=item.resolved_target_record_kind,
                    tool_name=item.tool_name,
                    mcp_tool_name=item.mcp_tool_name,
                    action_label=item.action_label,
                    reason=self._staged_revisions_review_sequence_reason(
                        item,
                        summary,
                        post_apply_recheck=post_apply_recheck,
                    ),
                )
            )

        for revision_iri in post_apply_recheck_revision_iris:
            summary = summary_by_iri.get(revision_iri)
            if summary is None:
                continue
            sequence.append(
                StagedGraphRevisionReviewSequenceItem(
                    phase="recheck_after_apply",
                    phase_label="Recheck after apply",
                    row_index=row_index_by_iri.get(revision_iri, 0),
                    row_iri=revision_iri,
                    summary=summary.summary,
                    queue="sequential_apply_recheck_candidate",
                    resolved_target_iri=revision_iri,
                    resolved_target_record_kind=(
                        self._graph_revision_record_kind_for_iri(revision_iri)
                    ),
                    tool_name="export_staged_revisions",
                    mcp_tool_name="doxabase.export_staged_revisions",
                    action_label="Recheck remaining bundle",
                    reason=(
                        "After applying one ready row in this changed-graph or "
                        "validation-dependency set, rerun apply checks or "
                        "export before acting on siblings."
                    ),
                )
            )

        return sorted(
            sequence,
            key=lambda item: (phase_order.get(item.phase, 99), item.row_index),
        )
    @staticmethod
    def _staged_revisions_review_sequence_phase(
        item: RevisionNextActionQueueItem,
        summary: StagedGraphRevisionExportSummary | None,
    ) -> tuple[str, str]:
        state = summary.stale_resolution_state if summary is not None else None
        if item.queue in {"inspect_already_applied", "informational"} or state in {
            "already_applied",
            "restaged_successor_already_applied",
            "noop",
            "restaged_successor_noop",
        }:
            return "inspect_redirects", "Inspect redirects"
        if (
            item.queue == "repair_or_replace"
            or item.application_status == "validation_failed"
            or item.staged_validation_status == "failed"
        ):
            return "repair_blockers", "Repair blockers"
        if item.queue == "restage_after_review" or state in {
            "stale_unresolved",
            "restaged_successor_stale_unresolved",
        }:
            return "restage_stale", "Restage stale"
        if item.queue == "apply_after_review":
            return "review_apply", "Review/apply ready"
        return "review_other", "Review remaining"
    @staticmethod
    def _staged_revisions_review_sequence_reason(
        item: RevisionNextActionQueueItem,
        summary: StagedGraphRevisionExportSummary | None,
        *,
        post_apply_recheck: set[str],
    ) -> str:
        if item.queue in {"inspect_already_applied", "informational"}:
            reason = (
                "Resolve applied, no-op, or informational redirects before "
                "mutating current staged rows."
            )
        elif (
            item.queue == "repair_or_replace"
            or item.application_status == "validation_failed"
            or item.staged_validation_status == "failed"
        ):
            reason = (
                "Repair validation or replacement blockers before restage/apply "
                "work."
            )
        elif item.queue == "restage_after_review":
            reason = (
                "Refresh stale or conflicting rows against the current graph "
                "before applying."
            )
        elif item.queue == "apply_after_review":
            reason = "Review semantic context, then apply if the row is still preferred."
        else:
            reason = item.source or item.action_label

        if summary is not None and summary.revision_iri in post_apply_recheck:
            reason += (
                " Apply at most one row in this changed-graph set before "
                "rechecking the remaining candidates."
            )
        return reason
    @staticmethod
    def _normalize_staged_review_decision(decision: str) -> str:
        normalized = decision.strip().lower().replace("-", "_")
        if normalized not in STAGED_REVIEW_DECISIONS:
            allowed = ", ".join(sorted(STAGED_REVIEW_DECISIONS))
            raise DoxaBaseError(
                "decision must be one of: " + allowed
            )
        return normalized
    def _ensure_staged_review_decision(self, decision_iri: str) -> None:
        decision_class_iri = self.expand_iri("rc:StagedRevisionReviewDecision")
        ontology_graphs = self._expand_graphs(["ontology"])
        if decision_class_iri in self._types_from_graphs(
            ontology_graphs,
            decision_iri,
        ):
            return
        missing_seed_terms = self._missing_base_ontology_terms(
            REQUIRED_STAGED_REVIEW_DECISION_ONTOLOGY_TERMS,
        )
        if missing_seed_terms:
            raise DoxaBaseError(
                "decision must be an rc:StagedRevisionReviewDecision declared "
                "in base or project ontology. "
                + self._stale_seed_recovery_message(missing_seed_terms)
            )
        raise DoxaBaseError(
            "decision must be an rc:StagedRevisionReviewDecision declared in "
            "base or project ontology. Use accepted_elsewhere, superseded, "
            "discarded, no_effective_change, or a project term typed as "
            "rc:StagedRevisionReviewDecision."
        )
    def _staged_revisions_modelling_choice_markdown(
        self,
        bundle_summary: StagedGraphRevisionBundleSummary,
    ) -> list[str]:
        if not bundle_summary.modelling_choice_rows:
            return []
        lines: list[str] = []
        if bundle_summary.modelling_choice_summary is not None:
            lines.extend([bundle_summary.modelling_choice_summary, ""])
        lines.extend(
            [
                (
                    "| Row | Role | Candidate | Queue | Validation | Support | "
                    "Shared context | Recommended action | Why |"
                ),
                "|---:|---|---|---|---|---|---|---|---|",
            ]
        )
        for row in bundle_summary.modelling_choice_rows:
            validation = (
                f"current: {row.apply_status or 'unknown'}; "
                f"staged: {row.staged_validation}"
            )
            shared_context = (
                ", ".join(row.shared_context_graphs)
                if row.shared_context_applies
                else "no"
            )
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(row.row_index),
                        self._markdown_table_cell(row.modelling_role),
                        self._markdown_table_cell(row.summary or row.revision_iri),
                        self._markdown_table_cell(row.queue or "(none)"),
                        self._markdown_table_cell(validation),
                        self._markdown_table_cell(row.support_note),
                        self._markdown_table_cell(shared_context),
                        self._markdown_table_cell(row.recommended_human_action),
                        self._markdown_table_cell(row.role_reason),
                    ]
                )
                + " |"
            )
        return lines
    def _staged_revisions_review_sequence_markdown(
        self,
        bundle_summary: StagedGraphRevisionBundleSummary,
    ) -> list[str]:
        if not bundle_summary.review_sequence:
            return []
        lines = [
            (
                "| Phase | Row | Candidate | Queue | Resolved target | Tool | Why |"
            ),
            "|---|---:|---|---|---|---|---|",
        ]
        for item in bundle_summary.review_sequence:
            target = self._staged_revisions_review_sequence_target_cell(item)
            tool = item.mcp_tool_name or item.tool_name or "(none)"
            lines.append(
                "| "
                + " | ".join(
                    [
                        self._markdown_table_cell(item.phase_label),
                        str(item.row_index),
                        self._markdown_table_cell(item.summary or item.row_iri),
                        self._markdown_table_cell(item.queue),
                        self._markdown_table_cell(target),
                        self._markdown_table_cell(tool),
                        self._markdown_table_cell(item.reason),
                    ]
                )
                + " |"
            )
        return lines
    @staticmethod
    def _staged_revisions_review_sequence_target_cell(
        item: StagedGraphRevisionReviewSequenceItem,
    ) -> str:
        if item.resolved_target_iri is None:
            return "(none)"
        if item.resolved_target_iri == item.row_iri:
            return "(same row)"
        record_kind = (
            f" ({item.resolved_target_record_kind})"
            if item.resolved_target_record_kind is not None
            else ""
        )
        return f"`{item.resolved_target_iri}`{record_kind}"
