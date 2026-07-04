"""Project brief: capsule state, queues, and gates.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via BriefMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class BriefMixin:
    def project_brief(self, *, limit: int = 20) -> ProjectBrief:
        """Report capsule state: counts, dataset one-liners, gates, queues.

        State, not script: gates name what is currently blocked (mutation,
        export, or nothing) and the one call that inspects each blocker;
        queues report pending work with counts and an example IRI; the agent
        decides what to do next.
        """
        if limit < 1:
            raise DoxaBaseError("limit must be at least 1")
        if self._staged_apply_check_cache is None:
            with self._scoped_staged_apply_check_cache():
                return self.project_brief(limit=limit)

        overview = self.graph_overview(limit=limit)
        entity_scan_limit = max(
            limit,
            overview.key_counts.get("datasets", 0),
            overview.key_counts.get("tables", 0),
        )
        dataset_entities = self._project_brief_dataset_entities(entity_scan_limit)

        staged_review = self._project_brief_staged_review(limit=limit)
        pending_detection_staged_review = staged_review
        if staged_review.omitted_count:
            pending_detection_staged_review = self._project_brief_staged_review(
                limit=staged_review.count
            )

        tasks: list[ProjectBriefRecommendedTask] = []
        staged_frontier_task = self._project_brief_staged_frontier_task(
            staged_review
        )
        if staged_frontier_task is not None:
            tasks.append(staged_frontier_task)

        datasets: list[ProjectBriefDataset] = []
        for entity in dataset_entities:
            description = self.describe_dataset(entity.iri)
            is_table = self._dataset_description_is_table(description)
            query_summary = (
                self._project_brief_query_summary(description.iri)
                if is_table
                else self._project_brief_non_tabular_query_summary()
            )
            profile_summary = self._project_brief_profile_summary(
                description,
                profile_candidate_limit=2,
                staged_review=pending_detection_staged_review,
            )
            dataset_summary = ProjectBriefDatasetSummary(
                dataset=self._privacy_redacted_resource_summary(
                    ResourceSummary(
                        iri=description.iri,
                        label=description.label,
                        description=description.description,
                    )
                ),
                is_table=is_table,
                query=query_summary,
                profile=profile_summary,
            )
            tasks.extend(
                self._project_brief_dataset_tasks(
                    dataset_summary,
                    staged_review=pending_detection_staged_review,
                )
            )
            if len(datasets) < limit:
                datasets.append(
                    ProjectBriefDataset(
                        iri=dataset_summary.dataset.iri,
                        label=dataset_summary.dataset.label,
                        is_table=is_table,
                        status=self._project_brief_dataset_status(
                            is_table=is_table,
                            query=query_summary,
                            profile=profile_summary,
                        ),
                        column_count=len(description.columns),
                        caveat_count=len(description.caveats),
                    )
                )

        tasks.extend(self._project_brief_staged_tasks(staged_review))
        tasks.extend(
            self._project_brief_analysis_packet_tasks(
                overview.key_counts.get("analysis_packets", 0)
            )
        )
        tasks.sort(key=lambda task: (task.priority, task.task_type))

        queue_counts = self._project_brief_task_type_counts(tasks)
        if staged_review.count:
            queue_counts["staged_review"] = max(
                staged_review.count,
                queue_counts.get("staged_review", 0),
            )
        gates, gate_actions = self._project_brief_gates(
            staged_frontier_task=staged_frontier_task,
            staged_review=staged_review,
            queue_counts=queue_counts,
            storage_access_count=overview.key_counts.get("storage_accesses", 0),
        )
        brief = ProjectBrief(
            key_counts=overview.key_counts,
            dataset_count=max(
                overview.key_counts.get("datasets", 0),
                overview.key_counts.get("tables", 0),
                len(dataset_entities),
            ),
            datasets=datasets,
            gates=gates,
            queues=self._project_brief_queues(tasks, queue_counts),
            suggested_next_actions=self._project_brief_suggestions(
                gate_actions, tasks
            ),
            limit=limit,
        )
        return self._privacy_redacted_api_value(brief)

    def _project_brief_gates(
        self,
        *,
        staged_frontier_task: ProjectBriefRecommendedTask | None,
        staged_review: ProjectBriefStagedReviewSummary,
        queue_counts: dict[str, int],
        storage_access_count: int,
    ) -> tuple[list[ProjectBriefGate], list[SuggestedNextAction]]:
        """Derive gates plus the inspection actions behind them.

        A gate reports state; its details_call is the one tool that inspects
        the blocker. Blocking semantics: a "mutation" gate should be
        inspected before staging or applying project-graph changes; an
        "export" gate before writing shareable artifacts; "none" gates are
        capsule-health signals worth knowing about.
        """
        gates: list[ProjectBriefGate] = []
        actions: list[SuggestedNextAction] = []

        def add(task, gate: str, blocks: str) -> None:
            if task is None:
                return
            action = task.suggested_next_action
            gates.append(
                ProjectBriefGate(
                    gate=gate,
                    blocks=blocks,
                    detail=task.reason,
                    details_call=action.tool if action is not None else "",
                )
            )
            if action is not None:
                actions.append(action)

        add(
            self._project_brief_seed_recovery_health_task(
                current_staged_revision_count=staged_review.count
            ),
            "stale_seed_recovery",
            "mutation",
        )
        if (
            staged_frontier_task is not None
            and staged_frontier_task.source == "staged_revision_recovery_session"
        ):
            add(staged_frontier_task, "staged_revision_recovery", "mutation")
        export_arguments, export_preflight = (
            self._project_brief_default_handoff_preflight()
        )
        add(
            self._project_brief_privacy_health_task(
                export_arguments, export_preflight
            ),
            "privacy_export_review",
            "export",
        )
        add(
            self._project_brief_export_validation_health_task(export_preflight),
            "export_validation_review",
            "export",
        )
        add(
            self._project_brief_fixture_storage_health_task(
                queue_counts=queue_counts,
                storage_access_count=storage_access_count,
            ),
            "query_fixture_staleness",
            "none",
        )
        return gates, actions

    @staticmethod
    def _project_brief_queues(
        tasks: list[ProjectBriefRecommendedTask],
        queue_counts: dict[str, int],
    ) -> list[ProjectBriefQueue]:
        example_by_type: dict[str, str] = {}
        for task in tasks:
            if task.resource is not None:
                example_by_type.setdefault(task.task_type, task.resource.iri)
        return [
            ProjectBriefQueue(
                name=name,
                count=count,
                example_iri=example_by_type.get(name),
            )
            for name, count in sorted(queue_counts.items())
        ]

    @staticmethod
    def _project_brief_suggestions(
        gate_actions: list[SuggestedNextAction],
        tasks: list[ProjectBriefRecommendedTask],
    ) -> list[SuggestedNextAction]:
        """At most five suggestions: gate inspections first, then top tasks."""
        suggestions: list[SuggestedNextAction] = []
        seen: set[str] = set()

        def add(action: SuggestedNextAction | None) -> None:
            if action is None or len(suggestions) >= 5:
                return
            key = suggested_action_key(action)
            if key in seen:
                return
            seen.add(key)
            suggestions.append(action)

        for action in gate_actions:
            add(action)
        for task in tasks:
            add(task.suggested_next_action)
        return suggestions

    @staticmethod
    def _project_brief_dataset_status(
        *,
        is_table: bool,
        query: ProjectBriefDatasetQuerySummary,
        profile: ProjectBriefDatasetProfileSummary,
    ) -> str:
        if not is_table:
            return "non-tabular asset; inspect context rather than query lanes"
        parts = [query.readiness]
        if query.issue_codes:
            parts.append(f"query issues: {', '.join(query.issue_codes[:3])}")
        if profile.review_draft_count:
            parts.append(
                f"{profile.review_draft_count} profile draft(s) await review"
            )
        elif profile.profile_evidence_count == 0:
            parts.append("no profile evidence recorded")
        return "; ".join(parts)

    def _project_brief_dataset_entities(self, limit: int) -> list[EntityRow]:
        entities_by_iri: dict[str, EntityRow] = {}
        for type_iri in ("rc:Table", "rc:Dataset"):
            for entity in self.list_entities(
                type=type_iri,
                graph="map",
                limit=limit,
            ).entities:
                entities_by_iri.setdefault(entity.iri, entity)
        return sorted(
            entities_by_iri.values(),
            key=lambda entity: (entity.label or entity.iri, entity.iri),
        )
    def _project_brief_query_summary(
        self,
        dataset_iri: str,
    ) -> ProjectBriefDatasetQuerySummary:
        query_context = self.describe_query_context(dataset_iri)
        return ProjectBriefDatasetQuerySummary(
            readiness=query_context.readiness,
            readiness_note=query_context.readiness_note,
            issue_codes=self._query_issue_codes(query_context.issues),
            repair_action_group_count=(
                query_context.suggested_repair_action_group_count
            ),
            candidate_count=len(query_context.query_target_candidates),
            ready_candidate_indexes=query_context.ready_candidate_indexes,
            direct_clean_candidate_indexes=(
                query_context.direct_clean_candidate_indexes
            ),
            suggested_next_actions=query_context.suggested_next_actions[:3],
        )
    @staticmethod
    def _project_brief_non_tabular_query_summary() -> ProjectBriefDatasetQuerySummary:
        return ProjectBriefDatasetQuerySummary(
            readiness="not_applicable_non_tabular_asset",
            readiness_note=(
                "This map dataset is not typed as rc:Table; use resource or "
                "context-slice handoffs unless an explicit queryable table "
                "route is modeled."
            ),
            issue_codes=[],
            repair_action_group_count=0,
            candidate_count=0,
            ready_candidate_indexes=[],
            direct_clean_candidate_indexes=[],
            suggested_next_actions=[],
        )
    def _project_brief_profile_summary(
        self,
        dataset: DatasetDescription,
        *,
        profile_candidate_limit: int,
        staged_review: ProjectBriefStagedReviewSummary,
    ) -> ProjectBriefDatasetProfileSummary:
        profile_summary = dataset.profile_summary
        candidates = profile_summary.profile_run_candidates
        draft_evidence_iris = self._project_brief_profile_draft_evidence_iris(
            profile_summary
        )
        selected_draft_evidence_iris = draft_evidence_iris[:profile_candidate_limit]
        omitted_draft_evidence_iris = draft_evidence_iris[profile_candidate_limit:]
        drafts: list[ProjectBriefProfileDraftSummary] = []
        for evidence_iri in selected_draft_evidence_iris:
            pending_staged_profile_update_iris = (
                self._project_brief_pending_staged_profile_update_iris(
                    dataset.iri,
                    evidence_iri,
                    staged_review,
                )
            )
            draft = self.draft_profile_map_updates(
                dataset.iri,
                evidence_iri,
                known_pending_staged_profile_update_iris=(
                    pending_staged_profile_update_iris
                ),
            )
            suggested_next_actions = [
                self._privacy_redacted_suggested_next_action(action)
                for action in draft.suggested_next_actions[:3]
            ]
            pending_staged_advisory_actions = (
                self._project_brief_pending_staged_profile_advisory_actions(
                    draft,
                )
            )
            pending_staged_advisory_iris = (
                self._project_brief_pending_staged_profile_advisory_iris(
                    draft,
                )
            )
            task_advisories = (
                self._project_brief_profile_task_advisories(
                    draft,
                    pending_staged_advisory_actions,
                )
            )
            draft_summary = ProjectBriefProfileDraftSummary(
                evidence_iri=evidence_iri,
                status=self._project_brief_profile_draft_status(draft),
                requires_review=False,
                profile_observation_count=len(draft.profile_observation_iris),
                recommendation_count=draft.recommendation_count,
                scalar_conflict_group_count=draft.scalar_conflict_group_count,
                metric_advisory_count=draft.metric_advisory_count,
                metric_advisory_status_counts=draft.metric_advisory_status_counts,
                type_advisory_count=draft.type_advisory_count,
                type_advisory_status_counts=draft.type_advisory_status_counts,
                action_group_names=list(draft.suggested_next_action_groups),
                pending_staged_profile_advisory_iris=pending_staged_advisory_iris,
                pending_staged_profile_advisory_count=len(
                    pending_staged_advisory_iris
                ),
                pending_staged_profile_advisory_actions=(
                    pending_staged_advisory_actions[:3]
                ),
                task_advisories=task_advisories,
                suggested_next_actions=suggested_next_actions,
            )
            drafts.append(
                replace(
                    draft_summary,
                    requires_review=self._project_brief_profile_draft_requires_review(
                        draft_summary,
                    ),
                )
            )
        draft_status_counts: dict[str, int] = {}
        for draft in drafts:
            draft_status_counts[draft.status] = draft_status_counts.get(
                draft.status,
                0,
            ) + 1
        review_draft_count = sum(1 for draft in drafts if draft.requires_review)
        return ProjectBriefDatasetProfileSummary(
            total_profile_count=profile_summary.total_profile_count,
            returned_profile_count=profile_summary.returned_profile_count,
            omitted_profile_count=profile_summary.omitted_profile_count,
            profile_evidence_count=len(profile_summary.evidence_iris),
            profile_evidence_iris=profile_summary.evidence_iris,
            profile_run_candidate_count=len(candidates),
            profile_run_evidence_iris=[
                candidate.evidence_iri for candidate in candidates
            ],
            draft_candidate_count=len(draft_evidence_iris),
            profile_candidate_omitted_count=len(omitted_draft_evidence_iris),
            omitted_draft_evidence_iris=omitted_draft_evidence_iris,
            draft_count=len(drafts),
            review_draft_count=review_draft_count,
            completed_draft_count=len(drafts) - review_draft_count,
            draft_status_counts=draft_status_counts,
            draft_evidence_iris=[draft.evidence_iri for draft in drafts],
            drafts=drafts,
        )
    def _project_brief_pending_staged_profile_advisory_actions(
        self,
        draft: ProfileMapUpdateDraft,
    ) -> list[SuggestedNextAction]:
        pending_set = set(
            self._project_brief_pending_staged_profile_advisory_iris(draft)
        )
        if not pending_set:
            return []
        actions: list[SuggestedNextAction] = []
        for group_name in ("metric_vocabulary_review", "profile_type_review"):
            for action in draft.suggested_next_action_groups.get(group_name, []):
                referenced: set[str] = set()
                iri = action.args.get("iri")
                if isinstance(iri, str):
                    referenced.add(iri)
                for value in action.args.get("revision_iris") or []:
                    if isinstance(value, str):
                        referenced.add(value)
                if referenced & pending_set:
                    actions.append(
                        self._privacy_redacted_suggested_next_action(action)
                    )
        return self._dedupe_suggested_next_actions(actions)
    @staticmethod
    def _project_brief_pending_staged_profile_advisory_iris(
        draft: ProfileMapUpdateDraft,
    ) -> list[str]:
        pending_iris: list[str] = []
        for advisory in [*draft.metric_advisories, *draft.type_advisories]:
            for field_name in (
                "pending_staged_promotion_iris",
                "pending_staged_assertion_iris",
            ):
                for iri in getattr(advisory, field_name, None) or []:
                    DoxaBase._append_unique(pending_iris, iri)
        return pending_iris
    def _project_brief_profile_task_advisories(
        self,
        draft: ProfileMapUpdateDraft,
        pending_staged_advisory_actions: list[SuggestedNextAction],
    ) -> list[dict[str, Any]]:
        advisories: list[dict[str, Any]] = []
        seen_keys: set[tuple[Any, ...]] = set()
        entries = [
            (
                "metric_vocabulary_review",
                "define_metric",
                "pending_staged_promotion_iris",
                draft.metric_advisories,
            ),
            (
                "profile_type_review",
                "define_value_type",
                "pending_staged_promotion_iris",
                draft.type_advisories,
            ),
            (
                "profile_type_review",
                "assert_map_type",
                "pending_staged_assertion_iris",
                draft.type_advisories,
            ),
        ]
        for review_lane, semantic_move, field_name, advisory_rows in entries:
            for advisory_row in advisory_rows:
                pending_iris = [
                    iri
                    for iri in getattr(advisory_row, field_name, None) or []
                    if isinstance(iri, str)
                ]
                if not pending_iris:
                    continue
                key = (review_lane, semantic_move, tuple(pending_iris))
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                pending_set = set(pending_iris)
                matching_action = next(
                    (
                        action
                        for action in pending_staged_advisory_actions
                        if pending_set
                        & {
                            value
                            for value in [
                                action.args.get("iri"),
                                *(action.args.get("revision_iris") or []),
                            ]
                            if isinstance(value, str)
                        }
                    ),
                    None,
                )
                advisories.append(
                    {
                        "code": "pending_staged_profile_advisory_review",
                        "severity": "warning",
                        "source": "draft_profile_map_updates",
                        "recommended_handling": (
                            "inspect_pending_staged_revision_before_restaging"
                        ),
                        "reason": (
                            "A profile advisory route already has pending "
                            "staged work; inspect that staged revision before "
                            "staging duplicate advisory follow-through."
                        ),
                        "review_lane": review_lane,
                        "semantic_move": semantic_move,
                        "pending_staged_revision_iris": pending_iris,
                        "pending_staged_promotion_iris": (
                            pending_iris
                            if field_name == "pending_staged_promotion_iris"
                            else []
                        ),
                        "pending_staged_assertion_iris": (
                            pending_iris
                            if field_name == "pending_staged_assertion_iris"
                            else []
                        ),
                        "suggested_next_action": (
                            to_jsonable(matching_action)
                            if matching_action is not None
                            else None
                        ),
                    }
                )
        return advisories
    @staticmethod
    def _project_brief_profile_draft_status(
        draft: ProfileMapUpdateDraft,
    ) -> str:
        return draft.status
    def _project_brief_profile_draft_evidence_iris(
        self,
        profile_summary: ProfileSummary,
    ) -> list[str]:
        evidence_iris: list[str] = []
        for candidate in profile_summary.profile_run_candidates:
            evidence_iris.append(candidate.evidence_iri)
        evidence_iris.extend(profile_summary.shared_evidence_iris)
        evidence_iris.extend(profile_summary.evidence_iris)
        return list(dict.fromkeys(evidence_iris))
    def _project_brief_staged_frontier_task(
        self,
        staged_review: ProjectBriefStagedReviewSummary,
    ) -> ProjectBriefRecommendedTask | None:
        if staged_review.count <= 0:
            return None
        session_task = self._project_brief_recovery_session_frontier_task(
            staged_review
        )
        if session_task is not None:
            return session_task
        action = self._project_brief_plan_staged_revision_recovery_action()
        return ProjectBriefRecommendedTask(
            priority=5,
            task_type="staged_frontier_review",
            source="plan_staged_revision_recovery",
            resource=None,
            reason=(
                "Current staged work exists; inspect the staged mutation frontier "
                "and apply-one-then-recheck hazards before staging duplicate "
                "profile or query repair work."
            ),
            suggested_next_action=action,
        )
    def _project_brief_recovery_session_frontier_task(
        self,
        staged_review: ProjectBriefStagedReviewSummary,
    ) -> ProjectBriefRecommendedTask | None:
        revision_iris = self._project_brief_current_staged_revision_iris(
            staged_review
        )
        if not revision_iris:
            return None
        history_graphs = self._expand_graphs(["history"])
        matching_session_iris = self._project_brief_matching_recovery_session_iris(
            revision_iris,
            history_graphs=history_graphs,
        )
        if not matching_session_iris:
            return None
        ordered_session_iris = self._project_brief_order_recovery_session_iris(
            matching_session_iris,
            history_graphs=history_graphs,
        )
        session_iri = ordered_session_iris[0]
        session_summary = self._first_object(
            history_graphs,
            session_iri,
            "rc:summary",
        )
        action = self._project_brief_describe_recovery_session_action(
            session_iri,
            history_graphs=history_graphs,
        )
        return ProjectBriefRecommendedTask(
            priority=5,
            task_type="staged_frontier_review",
            source="staged_revision_recovery_session",
            resource=ResourceSummary(
                iri=session_iri,
                label=session_summary,
                description=None,
            ),
            reason=(
                "A persisted staged-revision recovery session overlaps current "
                "staged work; continue that session before starting a generic "
                "frontier plan so multi-step handoff or recovery provenance is "
                "preserved."
            ),
            suggested_next_action=action,
            task_group={
                "matching_recovery_session_count": len(matching_session_iris),
                "matching_recovery_session_iris": ordered_session_iris,
                "current_staged_revision_count": len(revision_iris),
            },
        )
    def _project_brief_matching_recovery_session_iris(
        self,
        current_staged_revision_iris: list[str],
        *,
        history_graphs: list[str],
    ) -> list[str]:
        current_staged = {
            self.expand_iri(revision_iri)
            for revision_iri in current_staged_revision_iris
        }
        if not current_staged:
            return []
        matching: list[str] = []
        for session_iri in self._recovery_session_iris(history_graphs):
            source_revision_iris = (
                self._staged_recovery_session_source_revision_iris(
                    session_iri,
                    history_graphs=history_graphs,
                )
            )
            live_revision_iris = set(source_revision_iris)
            try:
                description = self.describe_staged_revision_recovery_session(
                    session_iri,
                )
            except DoxaBaseError:
                description = None
            if description is not None:
                live_revision_iris.update(
                    description.current_revision_by_source.values()
                )
                live_revision_iris.update(description.mutation_frontier_iris)
                live_revision_iris.update(
                    description.active_source_revision_iris
                )
            if current_staged.intersection(live_revision_iris):
                matching.append(session_iri)
        return matching
    def _project_brief_current_staged_revision_iris(
        self,
        staged_review: ProjectBriefStagedReviewSummary,
    ) -> list[str]:
        if staged_review.omitted_count <= 0:
            return [item.revision_iri for item in staged_review.items]
        listing = self.list_graph_revisions(
            current_staged_work_only=True,
            include_apply_checks=True,
            limit=staged_review.count,
        )
        return [revision.iri for revision in listing.revisions]
    def _project_brief_order_recovery_session_iris(
        self,
        session_iris: list[str],
        *,
        history_graphs: list[str],
    ) -> list[str]:
        return sorted(
            session_iris,
            key=lambda session_iri: (
                self._first_object(
                    history_graphs,
                    session_iri,
                    "rc:sessionCreatedAt",
                )
                or "",
                session_iri,
            ),
            reverse=True,
        )
    def _project_brief_describe_recovery_session_action(
        self,
        session_iri: str,
        *,
        history_graphs: list[str],
    ) -> SuggestedNextAction:
        include_drafts = self._optional_bool_object(
            self._first_object(
                history_graphs,
                session_iri,
                "rc:recoverySessionIncludeDrafts",
            ),
            default=True,
        )
        validation_scope = self._first_object(
            history_graphs,
            session_iri,
            "rc:recoverySessionValidationScope",
        )
        drift_detail = (
            self._first_object(
                history_graphs,
                session_iri,
                "rc:recoverySessionDriftDetail",
            )
            or "summary"
        )
        arguments: dict[str, Any] = {
            "session_iri": session_iri,
            "drift_detail": drift_detail,
        }
        if include_drafts is not True:
            arguments["include_drafts"] = include_drafts
        if validation_scope is not None:
            arguments["validation_scope"] = validation_scope
        return SuggestedNextAction(
                   tool="doxabase.plan_staged_revision_recovery",
                   args=arguments,
                   reason="A persisted staged-revision recovery session overlaps current "
                "staged work. Describe it so live recovery state, imported "
                "session provenance, and apply-one-then-recheck hazards stay "
                "connected.",
               )
    def _project_brief_plan_staged_revision_recovery_action(
        self,
    ) -> SuggestedNextAction:
        arguments = {"current_staged_work_only": True}
        return SuggestedNextAction(
                   tool="doxabase.plan_staged_revision_recovery",
                   args=arguments,
                   reason="Inspect current staged work, mutation_frontier_iris, and "
                "requires_recheck_after_each_apply before taking another graph "
                "mutation.",
               )
    def _project_brief_fixture_storage_health_task(
        self,
        *,
        queue_counts: dict[str, int],
        storage_access_count: int,
    ) -> ProjectBriefHealthTask | None:
        if queue_counts.get("query_repair_review", 0) <= 0:
            return None
        hint = self._known_fixture_tables_without_storage_access_hint(
            storage_access_count=storage_access_count
        )
        if hint is None:
            return None
        known_fixture_table_iris = list(hint["known_fixture_table_iris"])
        representative_dataset_iri = known_fixture_table_iris[0]
        if storage_access_count == 0:
            reason = (
                "Known query-planning fixture tables are present while the "
                "capsule has zero rc:StorageAccess resources. Treat the capsule "
                "as stale or intentionally reduced for storage-aware query "
                "trials until a representative query context is reviewed or "
                "fresh fixtures are loaded into scratch."
            )
            action_reason = (
                "Known AIS or Polymarket fixture tables are present but the "
                "capsule has no rc:StorageAccess resources; inspect one "
                "representative query context before staging repeated "
                "missing-storage repairs."
            )
        else:
            reason = (
                "Known query-planning fixture tables are present without linked "
                "rc:StorageAccess resources, even though unrelated storage "
                "accesses exist elsewhere in the capsule. Treat those fixture "
                "tables as stale or intentionally reduced for storage-aware "
                "query trials until a representative query context is reviewed "
                "or fresh fixtures are loaded into scratch."
            )
            action_reason = (
                "Known AIS or Polymarket fixture tables are present without "
                "linked rc:StorageAccess resources; inspect one representative "
                "query context before staging repeated missing-storage repairs."
            )
        arguments = {"iri": representative_dataset_iri}
        action = SuggestedNextAction(
                     tool="doxabase.describe_query_context",
                     args=arguments,
                     reason=action_reason,
                 )
        return ProjectBriefHealthTask(
            priority=15,
            task_type="query_fixture_staleness_review",
            source="fixture_storage_access_check",
            reason=reason,
            suggested_next_action=action,
            queue_types=["query_repair_review"],
            fixture_names=list(hint["fixture_names"]),
            known_fixture_table_iris=known_fixture_table_iris,
            storage_access_count=storage_access_count,
        )
    @staticmethod
    def _project_brief_default_handoff_preflight_arguments() -> dict[str, Any]:
        return {
            "export_kind": "handoff_bundle",
            "graphs": ["project"],
            "limit": 20,
        }
    def _project_brief_default_handoff_preflight(
        self,
    ) -> tuple[dict[str, Any], ExportPreflightRecord]:
        arguments = self._project_brief_default_handoff_preflight_arguments()
        return arguments, self.export_preflight(**arguments)
    def _project_brief_privacy_health_task(
        self,
        arguments: dict[str, Any],
        preflight: ExportPreflightRecord,
    ) -> ProjectBriefHealthTask | None:
        if preflight.sensitive_literal_count == 0:
            return None
        action = SuggestedNextAction(
                     tool="doxabase.export_preflight",
                     args=arguments,
                     reason="Run a redacted export preflight before sharing RDF or handoff "
                "exports; follow its blocking export action when the scanner is "
                "clean.",
                 )
        return ProjectBriefHealthTask(
            priority=16,
            task_type="privacy_export_review",
            source="export_preflight",
            reason=(
                "The default handoff-bundle export scope contains potential "
                "sensitive graph or revision-snapshot terms; project_brief "
                "reports only the count and a redacted export preflight route."
            ),
            suggested_next_action=action,
            sensitive_literal_count=preflight.sensitive_literal_count,
        )
    def _project_brief_export_validation_health_task(
        self,
        preflight: ExportPreflightRecord,
    ) -> ProjectBriefHealthTask | None:
        if not preflight.would_block_invalid_export:
            return None
        action = next(
            (
                candidate
                for candidate in preflight.suggested_next_actions
                if candidate.tool == "doxabase.validate_graph"
            ),
            None,
        )
        if action is None and preflight.validation_scope is not None:
            arguments = {
                "scope": preflight.validation_scope,
                "limit_results": max(preflight.limit, 20),
            }
            action = SuggestedNextAction(
                         tool="doxabase.validate_graph",
                         args=arguments,
                         reason="The live graph validation gate failed for this export "
                    "scope. Inspect SHACL diagnostics and repair the graph "
                    "before writing a recovery or share artifact.",
                     )
        return ProjectBriefHealthTask(
            priority=18,
            task_type="export_validation_review",
            source="export_preflight",
            reason=(
                "The default handoff-bundle export scope fails live graph "
                "validation; inspect SHACL diagnostics before writing recovery "
                "or share artifacts."
            ),
            suggested_next_action=action,
            would_block_invalid_export=preflight.would_block_invalid_export,
            validation_scope=preflight.validation_scope,
            validation_conforms=preflight.validation_conforms,
            validation_result_count=preflight.validation_result_count,
        )
    def _project_brief_seed_recovery_health_task(
        self,
        *,
        current_staged_revision_count: int,
    ) -> ProjectBriefHealthTask | None:
        required_terms = list(
            dict.fromkeys(
                [
                    *REQUIRED_STAGING_ONTOLOGY_TERMS,
                    *REQUIRED_REVISION_STANCE_ONTOLOGY_TERMS,
                ]
            )
        )
        missing_seed_terms = self._missing_base_ontology_terms(required_terms)
        if not missing_seed_terms:
            return None
        arguments = self._stale_seed_handoff_preflight_arguments()
        if current_staged_revision_count > 0:
            action = SuggestedNextAction(
                         tool="doxabase.export_preflight",
                         args=arguments,
                         reason="Current staged graph revision rows exist; preflight a "
                    "project/history plus revision snapshots handoff with map "
                    "validation before recovering into a fresh seeded capsule.",
                     )
            queue_types = ["staged_review"]
            staged_count: int | None = current_staged_revision_count
        else:
            action = SuggestedNextAction(
                         tool="doxabase.export_preflight",
                         args=arguments,
                         reason="The immutable base_ontology is missing current staging seed "
                    "terms; preflight a project/history handoff with map "
                    "validation before recovering into a fresh seeded capsule. "
                    "The companion revision snapshot bundle may be empty.",
                     )
            queue_types = []
            staged_count = 0
        return ProjectBriefHealthTask(
            priority=5,
            task_type="seed_recovery_review",
            source="base_ontology_seed_check",
            reason=self._stale_seed_recovery_message(missing_seed_terms),
            suggested_next_action=action,
            queue_types=queue_types,
            missing_seed_terms=missing_seed_terms,
            current_staged_revision_count=staged_count,
        )
    def _project_brief_staged_review(
        self,
        *,
        limit: int,
    ) -> ProjectBriefStagedReviewSummary:
        listing = self.list_graph_revisions(
            current_staged_work_only=True,
            include_apply_checks=True,
            limit=limit,
        )
        queue_by_row = {
            item.row_iri: item for item in listing.next_action_queue_items
        }
        items: list[ProjectBriefStagedReviewItem] = []
        for revision in listing.revisions:
            queue_item = queue_by_row.get(revision.iri)
            items.append(
                ProjectBriefStagedReviewItem(
                    revision_iri=revision.iri,
                    summary=revision.summary,
                    record_kind=revision.record_kind,
                    application_status=revision.application_status,
                    queue=queue_item.queue if queue_item is not None else None,
                    resolved_target_iri=(
                        queue_item.resolved_target_iri
                        if queue_item is not None
                        else None
                    ),
                    revision_anchor_iris=self._objects(
                        ["history"],
                        revision.iri,
                        "rc:revisionAnchor",
                    ),
                    evidence_iris=self._objects(
                        ["history"],
                        revision.iri,
                        "rc:evidence",
                    ),
                    suggested_next_action=(
                        revision.suggested_next_actions[0]
                        if revision.suggested_next_actions
                        else None
                    ),
                )
            )
        return ProjectBriefStagedReviewSummary(
            count=listing.count,
            returned_count=listing.returned_count,
            omitted_count=max(0, listing.count - listing.returned_count),
            application_status_counts=(
                listing.returned_application_status_counts
            ),
            next_action_queue_item_counts=(
                listing.next_action_queue_item_counts
            ),
            items=items,
        )
    def _project_brief_dataset_tasks(
        self,
        dataset: ProjectBriefDatasetSummary,
        *,
        staged_review: ProjectBriefStagedReviewSummary,
    ) -> list[ProjectBriefRecommendedTask]:
        tasks: list[ProjectBriefRecommendedTask] = []
        if not dataset.is_table:
            action = self._project_brief_get_context_graph_action(
                dataset.dataset.iri,
            )
            tasks.append(
                ProjectBriefRecommendedTask(
                    priority=25,
                    task_type="non_tabular_asset_review",
                    source="get_context_graph",
                    resource=dataset.dataset,
                    reason=(
                        "Dataset is not typed as rc:Table; inspect map context, "
                        "caveats, patterns, observations, and evidence instead "
                        "of query-planning repair lanes."
                    ),
                    suggested_next_action=action,
                )
            )
        else:
            if dataset.query.repair_action_group_count:
                repair_action = self._project_brief_describe_query_context_action(
                    dataset.dataset.iri
                )
                pending_staged_repair_iris = (
                    self._project_brief_pending_staged_repair_iris(
                        dataset.dataset.iri,
                        staged_review,
                    )
                )
                pending_note = (
                    " Pending staged repair(s) already anchor this dataset; "
                    "review the staged work before staging a duplicate repair."
                    if pending_staged_repair_iris
                    else ""
                )
                tasks.append(
                    ProjectBriefRecommendedTask(
                        priority=45 if pending_staged_repair_iris else 10,
                        task_type="query_repair_review",
                        source="describe_query_context",
                        resource=dataset.dataset,
                        reason=(
                            "Dataset query context exposes reviewed repair "
                            f"action groups.{pending_note}"
                        ),
                        suggested_next_action=repair_action,
                        pending_staged_repair_iris=pending_staged_repair_iris,
                    )
                )
            elif dataset.query.readiness == "logical_analysis_view":
                review_action = self._project_brief_describe_analysis_view_action(
                    dataset.dataset.iri,
                    query_summary=dataset.query,
                )
                tasks.append(
                    ProjectBriefRecommendedTask(
                        priority=65,
                        task_type="analysis_view_review",
                        source="describe_analysis_view",
                        resource=dataset.dataset,
                        reason=(
                            "Dataset is a logical analysis view: inspect the "
                            "denominator, source datasets, caveats, and query "
                            "snippets without treating it as missing physical "
                            "query metadata."
                        ),
                        suggested_next_action=review_action,
                    )
                )
            elif dataset.query.readiness not in {
                "ready_for_query_planning",
                "ready",
            }:
                review_action = self._project_brief_describe_query_context_action(
                    dataset.dataset.iri
                )
                tasks.append(
                    ProjectBriefRecommendedTask(
                        priority=20,
                        task_type="query_context_review",
                        source="describe_query_context",
                        resource=dataset.dataset,
                        reason=(
                            "Dataset query context is not ready for planning: "
                            f"{dataset.query.readiness}."
                        ),
                        suggested_next_action=review_action,
                    )
                )
            else:
                handoff_action = self._project_brief_query_plan_handoff_action(
                    dataset
                )
                handoff_summary = self._project_brief_query_plan_handoff_summary(
                    handoff_action
                )
                tasks.append(
                    ProjectBriefRecommendedTask(
                        priority=60,
                        task_type="query_plan_handoff",
                        source=handoff_action.tool.removeprefix("doxabase."),
                        resource=dataset.dataset,
                        reason=(
                            "Dataset query context is ready for a non-executed "
                            "query-plan handoff; draft or inspect the handoff "
                            "before treating ready query work as exhausted."
                        ),
                        suggested_next_action=handoff_action,
                        query_plan_handoff_summary=handoff_summary,
                    )
                )

        for draft in dataset.profile.drafts:
            if draft.requires_review:
                inspection_action = self._project_brief_draft_profile_action(
                    dataset.dataset.iri,
                    draft.evidence_iri,
                )
                pending_staged_profile_update_iris = (
                    self._project_brief_pending_staged_profile_update_iris(
                        dataset.dataset.iri,
                        draft.evidence_iri,
                        staged_review,
                    )
                )
                open_profile_advisory_count = (
                    draft.scalar_conflict_group_count
                    + self._project_brief_metric_advisory_review_count(draft)
                    + draft.type_advisory_count
                )
                if pending_staged_profile_update_iris:
                    action = inspection_action
                elif draft.pending_staged_profile_advisory_actions:
                    action = draft.pending_staged_profile_advisory_actions[0]
                else:
                    action = (
                        draft.suggested_next_actions[0]
                        if draft.suggested_next_actions
                        else inspection_action
                    )
                if pending_staged_profile_update_iris and open_profile_advisory_count:
                    pending_note = (
                        " Pending staged profile update(s) already anchor this "
                        "dataset/evidence, but profile advisory/conflict lanes "
                        "remain open; review the profile draft before assuming "
                        "staged work covers it."
                    )
                elif pending_staged_profile_update_iris:
                    pending_note = (
                        " Pending staged profile update(s) already anchor this "
                        "dataset/evidence; review staged frontier work before "
                        "staging another profile update."
                    )
                else:
                    pending_note = ""
                if draft.pending_staged_profile_advisory_count:
                    pending_note += (
                        " Pending staged profile advisory follow-through "
                        "already exists for this dataset/evidence; inspect "
                        "the staged advisory revision(s) before staging "
                        "duplicate advisory work."
                    )
                tasks.append(
                    ProjectBriefRecommendedTask(
                        priority=(
                            55
                            if (
                                (
                                    pending_staged_profile_update_iris
                                    and not open_profile_advisory_count
                                )
                                or draft.pending_staged_profile_advisory_count
                            )
                            else 30
                        ),
                        task_type="profile_review",
                        source="draft_profile_map_updates",
                        resource=dataset.dataset,
                        reason=self._project_brief_profile_review_reason(
                            draft,
                            pending_note=pending_note,
                        ),
                        suggested_next_action=action,
                        inspection_next_action=inspection_action,
                        profile_evidence_iri=draft.evidence_iri,
                        pending_staged_profile_update_iris=(
                            pending_staged_profile_update_iris
                        ),
                        task_advisories=draft.task_advisories,
                    )
                )
        return tasks
    @staticmethod
    def _project_brief_profile_review_reason(
        draft: ProjectBriefProfileDraftSummary,
        *,
        pending_note: str,
    ) -> str:
        review_parts: list[str] = []
        if draft.recommendation_count:
            review_parts.append(
                f"map recommendation count={draft.recommendation_count}"
            )
        if draft.scalar_conflict_group_count:
            review_parts.append(
                "scalar conflict group count="
                f"{draft.scalar_conflict_group_count}"
            )
        metric_review_count = DoxaBase._project_brief_metric_advisory_review_count(
            draft
        )
        if metric_review_count:
            review_parts.append(
                f"metric vocabulary advisory count={metric_review_count}"
            )
        if draft.type_advisory_count:
            status_counts = ", ".join(
                f"{status}={count}"
                for status, count in sorted(draft.type_advisory_status_counts.items())
            )
            review_parts.append(
                "profile type advisory count="
                f"{draft.type_advisory_count}"
                + (f" ({status_counts})" if status_counts else "")
            )
        detail = "; ".join(review_parts)
        if draft.recommendation_count:
            return f"Profile evidence has {detail} to review.{pending_note}"
        return (
            "Profile evidence has no pending map recommendations; review "
            f"{detail}.{pending_note}"
        )
    @staticmethod
    def _project_brief_profile_draft_requires_review(
        draft: ProjectBriefProfileDraftSummary,
    ) -> bool:
        return bool(
            draft.recommendation_count
            or draft.scalar_conflict_group_count
            or DoxaBase._project_brief_metric_advisory_review_count(draft)
            or draft.type_advisory_count
        )
    @staticmethod
    def _project_brief_metric_advisory_review_count(
        draft: ProjectBriefProfileDraftSummary,
    ) -> int:
        context_only_count = draft.metric_advisory_status_counts.get(
            "project_metric_defined",
            0,
        )
        return max(0, draft.metric_advisory_count - context_only_count)
    def _project_brief_get_context_graph_action(
        self,
        dataset_iri: str,
    ) -> SuggestedNextAction:
        arguments = {
            "seed_iris": [dataset_iri],
            "profile": "deep_lore",
        }
        return SuggestedNextAction(
                   tool="doxabase.get_context_graph",
                   args=arguments,
                   reason="Inspect the non-tabular asset's map context, caveats, "
                "patterns, observations, and evidence without treating it as a "
                "table query target.",
               )
    def _project_brief_describe_analysis_view_action(
        self,
        dataset_iri: str,
        *,
        query_summary: ProjectBriefDatasetQuerySummary,
    ) -> SuggestedNextAction:
        for action in query_summary.suggested_next_actions:
            if action.args.get("aspect") == "analysis_view":
                return action
        arguments = {"iri": dataset_iri, "aspect": "analysis_view"}
        return SuggestedNextAction(
                   tool="doxabase.describe_resource",
                   args=arguments,
                   reason="Read the logical view denominator, source datasets, caveats, "
                "and query snippet metadata before deciding whether to query "
                "the source datasets or materialize a new physical route.",
               )
    def _project_brief_analysis_packet_tasks(
        self,
        analysis_packet_count: int,
    ) -> list[ProjectBriefRecommendedTask]:
        if analysis_packet_count <= 0:
            return []
        packets = self.list_entities(
            type="rc:AnalysisPacket",
            graph="evidence",
            limit=analysis_packet_count,
        ).entities
        tasks: list[ProjectBriefRecommendedTask] = []
        for packet in packets:
            action = self._project_brief_describe_analysis_packet_action(
                packet.iri
            )
            tasks.append(
                ProjectBriefRecommendedTask(
                    priority=70,
                    task_type="analysis_packet_review",
                    source="get_context_graph",
                    resource=ResourceSummary(
                        iri=packet.iri,
                        label=packet.label,
                        description=self._first_object(
                            ["evidence"],
                            packet.iri,
                            "rc:summary",
                        ),
                    ),
                    reason=(
                        "Evidence includes an analysis packet with linked "
                        "logical views, cookbook recipes, artifact locators, or "
                        "follow-up tasks; inspect the packet context before "
                        "assuming analysis handoff work is exhausted."
                    ),
                    suggested_next_action=action,
                )
            )
        return tasks
    def _project_brief_describe_analysis_packet_action(
        self,
        packet_iri: str,
    ) -> SuggestedNextAction:
        arguments = {
            "seed_iris": [packet_iri],
            "profile": "resource_brief",
        }
        return SuggestedNextAction(
                   tool="doxabase.get_context_graph",
                   args=arguments,
                   reason="Inspect the packet, linked analysis views, artifact locators, "
                "query recipes, follow-up tasks, and supporting patterns as one "
                "bounded handoff context.",
               )
    def _project_brief_describe_query_context_action(
        self,
        dataset_iri: str,
    ) -> SuggestedNextAction:
        arguments = {"iri": dataset_iri}
        return SuggestedNextAction(
                   tool="doxabase.describe_query_context",
                   args=arguments,
                   reason="Inspect the dataset query context before choosing a repair or plan.",
               )
    def _project_brief_query_plan_handoff_action(
        self,
        dataset: ProjectBriefDatasetSummary,
    ) -> SuggestedNextAction:
        for action in dataset.query.suggested_next_actions:
            if action.tool == "doxabase.draft_query_plan":
                return action

        query_context = self.describe_query_context(dataset.dataset.iri)
        for action in query_context.suggested_next_actions:
            if action.tool == "doxabase.draft_query_plan":
                return action

        arguments = {"iri": dataset.dataset.iri}
        candidate_indexes = (
            dataset.query.ready_candidate_indexes
            or dataset.query.direct_clean_candidate_indexes
        )
        if candidate_indexes:
            arguments["candidate_index"] = candidate_indexes[0]
        return SuggestedNextAction(
                   tool="doxabase.draft_query_plan",
                   args=arguments,
                   reason="Draft a non-executed query-plan handoff for a dataset whose "
                "query context is ready for planning.",
               )
    def _project_brief_query_plan_handoff_summary(
        self,
        action: SuggestedNextAction,
    ) -> DraftQueryPlanHandoffSummary | None:
        if action.tool != "doxabase.draft_query_plan":
            return None
        try:
            return self.draft_query_plan(**action.args).handoff_summary
        except DoxaBaseError:
            return None
    @staticmethod
    def _project_brief_task_type_counts(
        tasks: list[ProjectBriefRecommendedTask],
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for task in tasks:
            counts[task.task_type] = counts.get(task.task_type, 0) + 1
        return counts
    def _project_brief_pending_staged_repair_iris(
        self,
        dataset_iri: str,
        staged_review: ProjectBriefStagedReviewSummary,
    ) -> list[str]:
        query_repair_anchor_iris = self._dataset_query_repair_anchor_iris(
            dataset_iri
        )
        ignored_queues = {
            None,
            "informational",
            "inspect_already_applied",
        }
        return [
            item.revision_iri
            for item in staged_review.items
            if item.suggested_next_action is not None
            and item.queue not in ignored_queues
            and query_repair_anchor_iris & set(item.revision_anchor_iris)
            and self._project_brief_staged_item_is_query_repair(item)
        ]
    def _project_brief_staged_item_is_query_repair(
        self,
        item: ProjectBriefStagedReviewItem,
    ) -> bool:
        history_graphs = self._expand_graphs(["history"])
        review_note = self._first_object(
            history_graphs,
            item.revision_iri,
            "rc:reviewNote",
        )
        if review_note and "query planning guidance" in review_note:
            return True

        query_repair_predicates = {
            self.expand_iri(predicate) for predicate in QUERY_REPAIR_PREDICATE_CURIES
        }
        try:
            staged = self.describe_staged_revision(item.revision_iri)
        except DoxaBaseError:
            return False
        for patch in staged.patches:
            if patch.target_graph != "map":
                continue
            try:
                patch_graph = self._parse_staged_patch_description(patch)
            except DoxaBaseError:
                continue
            if any(
                str(predicate) in query_repair_predicates
                for _, predicate, _ in patch_graph
            ):
                return True
        return False
    def _project_brief_pending_staged_profile_update_iris(
        self,
        dataset_iri: str,
        evidence_iri: str,
        staged_review: ProjectBriefStagedReviewSummary,
    ) -> list[str]:
        dataset_value = self.expand_iri(dataset_iri)
        evidence_value = self.expand_iri(evidence_iri)
        ignored_queues = {
            None,
            "informational",
            "inspect_already_applied",
        }
        return [
            item.revision_iri
            for item in staged_review.items
            if item.suggested_next_action is not None
            and item.queue not in ignored_queues
            and dataset_value in item.revision_anchor_iris
            and evidence_value in item.evidence_iris
            and self._project_brief_staged_item_is_profile_map_update(item)
        ]
    def _project_brief_staged_item_is_profile_map_update(
        self,
        item: ProjectBriefStagedReviewItem,
    ) -> bool:
        return self._staged_revision_is_profile_map_update(item.revision_iri)
    def _project_brief_staged_tasks(
        self,
        staged_review: ProjectBriefStagedReviewSummary,
    ) -> list[ProjectBriefRecommendedTask]:
        tasks: list[ProjectBriefRecommendedTask] = []
        for item in staged_review.items:
            if item.suggested_next_action is None:
                continue
            tasks.append(
                ProjectBriefRecommendedTask(
                    priority=8,
                    task_type="staged_review",
                    source="list_graph_revisions",
                    resource=ResourceSummary(
                        iri=item.revision_iri,
                        label=item.summary,
                        description=None,
                    ),
                    reason=(
                        "Current staged work has a review, repair, restage, "
                        "or apply follow-up."
                    ),
                    suggested_next_action=item.suggested_next_action,
                )
            )
        return tasks
    def _project_brief_draft_profile_action(
        self,
        dataset_iri: str,
        evidence_iri: str,
    ) -> SuggestedNextAction:
        arguments = {
            "dataset_iri": dataset_iri,
            "evidence_iri": evidence_iri,
        }
        return SuggestedNextAction(
                   tool="doxabase.stage_revision",
                   args={
                       "kind": "profile_map_updates",
                       "dry_run": True,
                       "spec": arguments,
                   },
                   reason="Review profile-derived map updates and advisory lanes.",
               )
    def _resource_brief_seed_exists(self, graphs: list[str], seed: str) -> bool:
        return (
            self._subject_exists(seed, graphs)
            or self._resource_triple_count(
                graphs,
                object_value=seed,
                object_kind="uri",
            )
            > 0
            or self._resource_brief_predicate_usage_count(
                graphs,
                predicate_iri=seed,
            )
            > 0
        )
    def _resource_brief_outgoing_references(
        self,
        graphs: list[str],
        *,
        subject: str,
        limit: int,
    ) -> tuple[list[str], int]:
        graph_filter, graph_params = self._graph_filter(graphs, alias="q")
        packet_action_predicates = (
            self.expand_iri("rc:packetAnalysisView"),
            self.expand_iri("rc:hasQueryRecipe"),
            self.expand_iri("rc:hasFollowupTask"),
        )
        priority_case = """
            CASE q.predicate
                WHEN ? THEN 0
                WHEN ? THEN 1
                WHEN ? THEN 2
                ELSE 100
            END
        """
        base_query = f"""
            SELECT q.object AS iri, MIN({priority_case}) AS priority
            FROM quads q
            WHERE q.subject = ?
              AND q.object_kind = 'uri'
              AND q.predicate != ?
              {graph_filter}
            GROUP BY q.object
        """
        params: list[Any] = [
            *packet_action_predicates,
            subject,
            str(RDF.type),
            *graph_params,
        ]
        rows = self._conn.execute(
            f"""
            {base_query}
            ORDER BY priority, iri
            LIMIT ?
            """,
            [*params, limit],
        ).fetchall()
        count_row = self._conn.execute(
            f"SELECT COUNT(*) AS count FROM ({base_query})",
            params,
        ).fetchone()
        return [row["iri"] for row in rows], int(count_row["count"])
    def _resource_brief_incoming_subjects(
        self,
        graphs: list[str],
        *,
        object_iri: str,
        limit: int,
    ) -> tuple[list[str], int]:
        graph_filter, graph_params = self._graph_filter(graphs, alias="q")
        rows = self._conn.execute(
            f"""
            SELECT DISTINCT q.subject AS iri
            FROM quads q
            WHERE q.object = ?
              AND q.object_kind = 'uri'
              AND q.subject_kind = 'uri'
              {graph_filter}
            """,
            [object_iri, *graph_params],
        ).fetchall()
        iris = [str(row["iri"]) for row in rows]
        lookup_graphs = self._lookup_graphs(graphs)
        ordered = sorted(
            iris,
            key=lambda iri: (
                -self._resource_brief_incoming_usefulness_score(graphs, iri),
                self._display_label_from_graphs(lookup_graphs, iri) or "",
                iri,
            ),
        )
        return ordered[:limit], len(ordered)
    def _resource_brief_incoming_usefulness_score(
        self,
        graphs: list[str],
        iri: str,
    ) -> int:
        score = 0
        types = set(self._types_from_graphs(graphs, iri))
        if self.expand_iri("rc:Column") in types:
            score += 12
        if (
            self.expand_iri("rc:Dataset") in types
            or self.expand_iri("rc:Table") in types
        ):
            score += 8
        if self._subjects(graphs, "rc:revisionAnchor", iri):
            score += 70
        if self._subjects(graphs, "rc:claimTarget", iri):
            score += 60
        if self._subjects(graphs, "rc:patternTarget", iri):
            score += 50
        if self._subjects(graphs, "rc:mapImplication", iri):
            score += 45
        if self._subjects(graphs, "rc:observedColumn", iri):
            score += 40
        if self._subjects(graphs, "rc:observedAsset", iri):
            score += 30
        if self._objects(graphs, iri, "rc:hasKnownCaveat"):
            score += 35
        if self._objects(graphs, iri, "rc:caveatDescription"):
            score += 20
        if self._subjects(graphs, "rc:hasColumn", iri):
            score += 10
        return score
    def _resource_brief_predicate_usage_subjects(
        self,
        graphs: list[str],
        *,
        predicate_iri: str,
        limit: int,
    ) -> tuple[list[str], int]:
        graph_filter, graph_params = self._graph_filter(graphs, alias="q")
        where = """
            q.predicate = ?
            AND q.subject_kind = 'uri'
        """
        params: list[Any] = [predicate_iri, *graph_params]
        return self._resource_brief_distinct_iris(
            where,
            params,
            graph_filter=graph_filter,
            select_column="q.subject",
            limit=limit,
        )
    def _resource_brief_predicate_usage_count(
        self,
        graphs: list[str],
        *,
        predicate_iri: str,
    ) -> int:
        graph_filter, graph_params = self._graph_filter(graphs, alias="q")
        row = self._conn.execute(
            f"""
            SELECT COUNT(DISTINCT q.subject) AS count
            FROM quads q
            WHERE q.predicate = ?
              AND q.subject_kind = 'uri'
              {graph_filter}
            """,
            [predicate_iri, *graph_params],
        ).fetchone()
        return int(row["count"])
    def _resource_brief_incoming_blank_node_owners(
        self,
        graphs: list[str],
        *,
        object_iri: str,
        limit: int,
    ) -> tuple[list[str], int]:
        graph_filter, graph_params = self._graph_filter(graphs, alias="q")
        rows = self._conn.execute(
            f"""
            SELECT DISTINCT q.subject AS blank_node
            FROM quads q
            WHERE q.object = ?
              AND q.object_kind = 'uri'
              AND q.subject_kind = 'bnode'
              {graph_filter}
            ORDER BY q.subject
            """,
            [object_iri, *graph_params],
        ).fetchall()
        owners, _depth_exhausted = self._recursive_blank_node_uri_owners(
            graphs,
            blank_nodes=[row["blank_node"] for row in rows],
        )
        ordered_owners = sorted(owners)
        return ordered_owners[:limit], len(ordered_owners)
    def _resource_brief_blank_node_seed_owners(
        self,
        graphs: list[str],
        *,
        blank_node: str,
        limit: int,
        max_depth: int = 4,
    ) -> tuple[list[str], int, bool]:
        owners, depth_exhausted = self._recursive_blank_node_uri_owners(
            graphs,
            blank_nodes=[blank_node],
            max_depth=max_depth,
        )
        ordered_owners = sorted(owners)
        return ordered_owners[:limit], len(ordered_owners), depth_exhausted
    def _resource_brief_blank_node_references(
        self,
        graphs: list[str],
        *,
        subject: str,
        limit: int,
    ) -> tuple[list[str], int, bool]:
        closure_triples, _total_count, depth_exhausted, _unvisited_count = (
            self._resource_blank_node_closure(
                graphs,
                subject=subject,
                max_depth=2,
                limit=max(limit * 20, 100),
            )
        )
        refs = sorted(
            {
                triple.object
                for triple in closure_triples
                if triple.object_kind == "uri"
            }
        )
        return refs[:limit], len(refs), depth_exhausted
    def _resource_brief_distinct_iris(
        self,
        where: str,
        params: list[Any],
        *,
        graph_filter: str,
        select_column: str,
        limit: int,
    ) -> tuple[list[str], int]:
        base_query = f"""
            SELECT DISTINCT {select_column} AS iri
            FROM quads q
            WHERE {where}
              {graph_filter}
        """
        rows = self._conn.execute(
            f"""
            {base_query}
            ORDER BY iri
            LIMIT ?
            """,
            [*params, limit],
        ).fetchall()
        count_row = self._conn.execute(
            f"SELECT COUNT(*) AS count FROM ({base_query})",
            params,
        ).fetchone()
        return [row["iri"] for row in rows], int(count_row["count"])
    @staticmethod
    def _staged_recovery_helper_frontier_context(
        lane: StagedRevisionRecoveryLane | None,
    ) -> dict[str, Any]:
        context: dict[str, Any] = {
            "row_iris": [],
            "semantic_risk_level": None,
            "semantic_risk_reasons": [],
            "alternative_set_iris": [],
            "alternative_set_source_iri": None,
            "alternative_set_roles": [],
            "alternative_gate_statuses": [],
            "alternative_applied_source_iris": [],
            "alternative_applied_revision_iris": [],
            "requires_semantic_review_before_mutation": False,
        }
        if lane is None:
            return context

        def add_unique(key: str, value: str | None) -> None:
            if value is not None:
                DoxaBase._append_unique(context[key], value)

        add_unique("row_iris", lane.row_iri)
        item = lane.next_action_queue_item
        if item is not None:
            context["semantic_risk_level"] = item.semantic_risk_level
            context["semantic_risk_reasons"] = list(item.semantic_risk_reasons)
            context["alternative_set_iris"] = list(item.alternative_set_iris)
            context["alternative_set_source_iri"] = item.alternative_set_source_iri
            add_unique("alternative_set_roles", item.alternative_set_role)
            add_unique("alternative_gate_statuses", item.alternative_gate_status)
            add_unique(
                "alternative_applied_source_iris",
                item.alternative_applied_source_iri,
            )
            add_unique(
                "alternative_applied_revision_iris",
                item.alternative_applied_revision_iri,
            )
            context["requires_semantic_review_before_mutation"] = (
                item.alternative_semantic_review_required
            )

        if lane.alternative_gate is not None:
            gate = lane.alternative_gate
            add_unique("alternative_gate_statuses", gate.status)
            add_unique("alternative_applied_source_iris", gate.applied_source_iri)
            add_unique(
                "alternative_applied_revision_iris",
                gate.applied_revision_iri,
            )
            if gate.status != "not_applicable":
                add_unique("alternative_set_iris", gate.current_alternative_to)
                add_unique("alternative_set_iris", lane.row_iri)
                if context["alternative_set_source_iri"] is None:
                    context["alternative_set_source_iri"] = (
                        gate.current_alternative_to
                    )
                add_unique("alternative_set_roles", "alternative")
            context["requires_semantic_review_before_mutation"] = (
                context["requires_semantic_review_before_mutation"]
                or gate.semantic_review_required
            )

        return context
    @staticmethod
    def _staged_recovery_mutation_frontier_items(
        groups: Iterable[StagedRevisionResolvedTargetGroup],
        *,
        lanes: Iterable[StagedRevisionRecoveryLane],
        helper_mutation_frontier_actions: Iterable[SuggestedNextAction],
    ) -> list[StagedRevisionMutationFrontierItem]:
        mutation_queues = {
            "apply_after_review",
            "restage_after_review",
            "repair_or_replace",
        }
        action_by_target: dict[tuple[str, str], RevisionNextAction] = {}
        lane_list = list(lanes)
        for lane in lane_list:
            item = lane.next_action_queue_item
            queue = item.queue if item is not None else lane.lane
            target_iri = (
                item.resolved_target_iri
                if item is not None
                else lane.resolved_target_iri
            )
            if queue not in mutation_queues or target_iri is None:
                continue
            if (
                queue == "repair_or_replace"
                and not DoxaBase._staged_recovery_action_is_mutating(
                    lane.next_action
                )
            ):
                continue
            if lane.next_action is None:
                continue
            action_by_target.setdefault((queue, target_iri), lane.next_action)

        items: list[StagedRevisionMutationFrontierItem] = []
        for group in groups:
            if (
                group.queue not in mutation_queues
                or group.resolved_target_iri is None
            ):
                continue
            action = action_by_target.get(
                (group.queue, group.resolved_target_iri)
            )
            if (
                group.queue == "repair_or_replace"
                and not DoxaBase._staged_recovery_action_is_mutating(action)
            ):
                continue
            items.append(
                StagedRevisionMutationFrontierItem(
                    item_kind="revision_target",
                    queue=group.queue,
                    target_iri=group.resolved_target_iri,
                    target_record_kind=group.resolved_target_record_kind,
                    source_revision_iris=list(group.source_revision_iris),
                    row_iris=list(group.row_iris),
                    action=action,
                    semantic_risk_level=group.semantic_risk_level,
                    semantic_risk_reasons=list(group.semantic_risk_reasons),
                    alternative_set_iris=list(group.alternative_set_iris),
                    alternative_set_source_iri=group.alternative_set_source_iri,
                    alternative_set_roles=list(group.alternative_set_roles),
                    alternative_gate_statuses=list(group.alternative_gate_statuses),
                    alternative_applied_source_iris=list(
                        group.alternative_applied_source_iris
                    ),
                    alternative_applied_revision_iris=list(
                        group.alternative_applied_revision_iris
                    ),
                    requires_semantic_review_before_mutation=(
                        group.alternative_semantic_review_required
                    ),
                    reason=(
                        (
                            "Resolved staged-revision mutation target, but "
                            "semantic review is required before mutation. "
                            "Review the row, alternative gate, and action; do "
                            "not mutate unattended until that semantic choice "
                            "is resolved."
                        )
                        if group.alternative_semantic_review_required
                        else (
                            "Resolved staged-revision mutation target. Review "
                            "the row and action, then mutate this target before "
                            "replanning if required."
                        )
                    ),
                )
            )

        helper_context_by_source = {
            lane.source_revision_iri: (
                DoxaBase._staged_recovery_helper_frontier_context(lane)
            )
            for lane in lane_list
            if lane.lane == "repair_or_replace"
        }
        for action in helper_mutation_frontier_actions:
            restages_revision = action_staging_arguments(action).get(
                "restages_revision"
            )
            source_revision_iris = (
                [restages_revision] if isinstance(restages_revision, str) else []
            )
            context = helper_context_by_source.get(
                restages_revision if isinstance(restages_revision, str) else None,
                DoxaBase._staged_recovery_helper_frontier_context(None),
            )
            items.append(
                StagedRevisionMutationFrontierItem(
                    item_kind="helper_action",
                    queue="repair_or_replace",
                    target_iri=None,
                    target_record_kind=None,
                    source_revision_iris=source_revision_iris,
                    row_iris=list(context["row_iris"]),
                    action=action,
                    semantic_risk_level=context["semantic_risk_level"],
                    semantic_risk_reasons=list(context["semantic_risk_reasons"]),
                    alternative_set_iris=list(context["alternative_set_iris"]),
                    alternative_set_source_iri=context[
                        "alternative_set_source_iri"
                    ],
                    alternative_set_roles=list(context["alternative_set_roles"]),
                    alternative_gate_statuses=list(
                        context["alternative_gate_statuses"]
                    ),
                    alternative_applied_source_iris=list(
                        context["alternative_applied_source_iris"]
                    ),
                    alternative_applied_revision_iris=list(
                        context["alternative_applied_revision_iris"]
                    ),
                    requires_semantic_review_before_mutation=context[
                        "requires_semantic_review_before_mutation"
                    ],
                    reason=(
                        (
                            "Repair helper mutation for a staged recovery lane "
                            "that does not have a concrete successor IRI yet, "
                            "but semantic review is required before mutation. "
                            "Review the alternative gate; do not mutate "
                            "unattended before running this helper."
                        )
                        if context["requires_semantic_review_before_mutation"]
                        else (
                            "Repair helper mutation for a staged recovery lane "
                            "that does not have a concrete successor IRI yet."
                        )
                    ),
                )
            )
        return items
    def _staged_recovery_helper_mutation_frontier_actions(
        self,
        lanes: Iterable[StagedRevisionRecoveryLane],
    ) -> list[SuggestedNextAction]:
        actions: list[SuggestedNextAction] = []
        for lane in lanes:
            if lane.lane != "repair_or_replace":
                continue
            if (
                lane.repair_draft is not None
                and lane.repair_draft.preferred_action is not None
            ):
                actions.append(lane.repair_draft.preferred_action)
        return self._dedupe_suggested_next_actions(actions)
    @staticmethod
    def _staged_recovery_semantic_frontier_review_action(
        mutation_frontier_items: Iterable[StagedRevisionMutationFrontierItem],
        suggested_next_actions: list[SuggestedNextAction],
    ) -> SuggestedNextAction | None:
        review_tool_order = {
            "describe_staged_revision": 0,
            "describe_revision_lineage": 1,
            "export_staged_revision": 2,
            "export_staged_revisions": 3,
            "describe_graph_revision": 4,
            "describe_applied_revision_diff": 5,
            "restage_staged_revision": 6,
        }
        semantic_target_iris: list[str] = []
        for item in mutation_frontier_items:
            if not item.requires_semantic_review_before_mutation:
                continue
            for value in (
                item.target_iri,
                *item.row_iris,
                *item.source_revision_iris,
                item.alternative_set_source_iri,
                *item.alternative_set_iris,
                *item.alternative_applied_source_iris,
                *item.alternative_applied_revision_iris,
            ):
                if value is not None and value not in semantic_target_iris:
                    semantic_target_iris.append(value)
        if not semantic_target_iris:
            return None

        semantic_target_set = set(semantic_target_iris)
        matching_actions = [
            action
            for action in suggested_next_actions
            if action_tool_name(action) in review_tool_order
            and (
                action_tool_name(action) != "restage_staged_revision"
                or staged_rebase_draft_action(action)
            )
            and DoxaBase._staged_recovery_action_is_safe_review(action)
            and DoxaBase._suggested_action_references_any_revision(
                action,
                semantic_target_set,
            )
        ]
        return min(
            matching_actions,
            key=lambda action: review_tool_order[action_tool_name(action)],
            default=None,
        )
    def _staged_recovery_frontier_review_action(
        self,
        item: StagedRevisionMutationFrontierItem,
        suggested_next_actions: list[SuggestedNextAction],
    ) -> SuggestedNextAction | None:
        review_tool_order = {
            "describe_staged_revision": 0,
            "describe_revision_lineage": 1,
            "export_staged_revision": 2,
            "export_staged_revisions": 3,
            "describe_graph_revision": 4,
            "describe_applied_revision_diff": 5,
            "restage_staged_revision": 6,
        }
        target_iris = [
            value
            for value in [
                item.target_iri,
                *item.row_iris,
                *item.source_revision_iris,
            ]
            if value is not None
        ]
        target_set = set(target_iris)
        matching_actions = [
            action
            for action in suggested_next_actions
            if action_tool_name(action) in review_tool_order
            and (
                action_tool_name(action) != "restage_staged_revision"
                or staged_rebase_draft_action(action)
            )
            and DoxaBase._staged_recovery_action_is_safe_review(action)
            and DoxaBase._suggested_action_references_any_revision(
                action,
                target_set,
            )
        ]
        if matching_actions:
            return min(
                matching_actions,
                key=lambda action: review_tool_order[action_tool_name(action)],
            )
        review_iri = next(iter(target_iris), None)
        if review_iri is None:
            return None
        arguments = {"iri": review_iri, "include_current_apply_check": True}
        return SuggestedNextAction(
                   tool="doxabase.describe_staged_revision",
                   args=arguments,
                   reason="Inspect the staged revision before running its mutation "
                "frontier action.",
               )
    @staticmethod
    def _revision_mutation_frontier_iris(
        queue_items: Iterable[RevisionNextActionQueueItem],
    ) -> list[str]:
        frontier: list[str] = []
        for item in queue_items:
            if not DoxaBase._revision_next_action_queue_item_is_mutation_target(
                item
            ):
                continue
            DoxaBase._append_unique(frontier, item.resolved_target_iri)
        return frontier
    def _suggested_call_string(
        self,
        tool_name: str,
        arguments: Mapping[str, Any],
    ) -> str:
        arg_text = ", ".join(
            f"{key}={value!r}"
            for key, value in arguments.items()
        )
        return f"{tool_name}({arg_text})"
    def _post_handoff_import_project_brief_action(self) -> SuggestedNextAction:
        arguments: dict[str, Any] = {}
        return SuggestedNextAction(
                   tool="doxabase.project_brief",
                   args=arguments,
                   reason="The handoff import had no revision rows to recover. Rerun the "
                "receiving capsule's project brief so the next agent resumes "
                "from its current safety gates, frontier expansion, or project "
                "work queue.",
               )
