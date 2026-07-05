"""Handoff-bundle recovery summaries and import-time recovery plans.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via RecoveryHandoffMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class RecoveryHandoffMixin:
    def _handoff_bundle_recovery_session_manifest_entries(
        self,
        revision_iris: list[str],
    ) -> list[dict[str, Any]]:
        history_graphs = self._expand_graphs(["history"])
        session_iris = self._matching_recovery_session_iris(
            self._recovery_session_iris(history_graphs),
            revision_iris=revision_iris,
            history_graphs=history_graphs,
        )
        return [
            self._handoff_bundle_recovery_session_manifest_entry(
                session_iri,
                history_graphs=history_graphs,
            )
            for session_iri in session_iris
        ]
    def _handoff_bundle_recovery_session_manifest_entry(
        self,
        session_iri: str,
        *,
        history_graphs: list[str],
    ) -> dict[str, Any]:
        source_revision_iris = self._staged_recovery_session_source_revision_iris(
            session_iri,
            history_graphs=history_graphs,
        )
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
        resume_action = self._describe_imported_recovery_session_action(
            session_iri,
            include_drafts=include_drafts,
            validation_scope=validation_scope,
            drift_detail=drift_detail,
        )
        return {
            "session_iri": session_iri,
            "summary": self._first_object(history_graphs, session_iri, "rc:summary"),
            "created_at": self._first_object(
                history_graphs,
                session_iri,
                "rc:sessionCreatedAt",
            ),
            "created_by": self._first_object(
                history_graphs,
                session_iri,
                "rc:sessionCreatedBy",
            ),
            "handoff_manifest_path": self._first_object(
                history_graphs,
                session_iri,
                "rc:recoverySessionHandoffManifestPath",
            ),
            "source_revision_iris": source_revision_iris,
            "source_count": len(source_revision_iris),
            "current_staged_work_only": self._optional_bool_object(
                self._first_object(
                    history_graphs,
                    session_iri,
                    "rc:recoverySessionCurrentStagedWorkOnly",
                ),
                default=False,
            ),
            "include_drafts": include_drafts,
            "repair_draft_limit": self._first_object(
                history_graphs,
                session_iri,
                "rc:recoverySessionRepairDraftLimit",
            ),
            "validation_scope": validation_scope,
            "drift_detail": drift_detail,
            "initial_selection_mode": self._first_object(
                history_graphs,
                session_iri,
                "rc:recoverySessionInitialSelectionMode",
            ),
            "initial_lane_counts": self._json_object_literal(
                self._first_object(
                    history_graphs,
                    session_iri,
                    "rc:recoverySessionInitialLaneCounts",
                ),
            ),
            "resume_action": to_jsonable(resume_action),
        }
    def _handoff_bundle_recovery_summary(
        self,
        *,
        dry_run: bool,
        revision_iris: list[str],
        snapshot_evidence: list[RevisionSnapshotEvidenceStatus],
        trig_total_imported: int,
        revision_snapshots: RevisionSnapshotBundleImportRecord | None,
        imported_recovery_session_iris: list[str],
        matching_recovery_session_iris: list[str],
        recovery_plan: StagedRevisionRecoveryPlan | None,
        suggested_next_actions: list[SuggestedNextAction],
        privacy_review_required_before_recovery: bool = False,
        validation_review_required_before_recovery: bool = False,
    ) -> HandoffBundleRecoverySummary:
        snapshot_evidence = self._handoff_recovery_summary_snapshot_evidence(
            snapshot_evidence,
            recovery_plan=recovery_plan,
        )
        snapshot_status_counts: dict[str, int] = {}
        for evidence in snapshot_evidence:
            snapshot_status_counts[evidence.status] = (
                snapshot_status_counts.get(evidence.status, 0) + 1
            )
        incomplete_snapshot_revision_iris = [
            evidence.revision_iri
            for evidence in snapshot_evidence
            if evidence.status != "history_plus_snapshot_rows"
        ]
        recovery_preflight_required = (
            recovery_plan is not None
            and recovery_plan.mutation_allowed_after
            == "handoff_preflight_required_before_mutation"
        )
        first_action = suggested_next_actions[0] if suggested_next_actions else None
        receiver_session_start_required = (
            not dry_run
            and not matching_recovery_session_iris
            and first_action is not None
            and first_action.tool == "doxabase.plan_staged_revision_recovery"
            and first_action.args.get("start_session") is True
        )
        if privacy_review_required_before_recovery:
            recommended_next_step = "review_handoff_privacy_before_recovery"
        elif validation_review_required_before_recovery:
            recommended_next_step = "review_handoff_validation_before_recovery"
        elif recovery_preflight_required:
            recommended_next_step = (
                "complete_handoff_preflight_before_recovery_mutation"
            )
        elif dry_run:
            recommended_next_step = "run_import_handoff_bundle"
        elif matching_recovery_session_iris:
            recommended_next_step = "continue_imported_recovery_session"
        elif receiver_session_start_required:
            recommended_next_step = "start_receiver_local_recovery_session"
        elif recovery_plan is not None and recovery_plan.mutation_frontier_iris:
            recommended_next_step = "follow_recovery_plan_mutation_frontier"
        elif recovery_plan is not None and recovery_plan.processed_revision_iris:
            recommended_next_step = "inspect_recovery_plan"
        else:
            recommended_next_step = "resume_project_frontier"
        imported_session_continuation_required = (
            recommended_next_step == "continue_imported_recovery_session"
        )
        resume_recovery_session_action = None
        if imported_session_continuation_required:
            for action in suggested_next_actions:
                if (
                    action.tool == "doxabase.plan_staged_revision_recovery"
                    and isinstance(action.args.get("session_iri"), str)
                    and action.args.get("start_session") is not True
                ):
                    resume_recovery_session_action = action
                    break
        resume_recovery_session_iri = (
            resume_recovery_session_action.args.get("session_iri")
            if resume_recovery_session_action is not None
            and isinstance(
                resume_recovery_session_action.args.get("session_iri"),
                str,
            )
            else (
                matching_recovery_session_iris[0]
                if imported_session_continuation_required
                and matching_recovery_session_iris
                else None
            )
        )

        profile_route_keys: list[str] = []
        profile_route_revision_count = 0
        profile_route_group_count = 0
        mutation_frontier_items = (
            list(recovery_plan.mutation_frontier_items)
            if recovery_plan is not None
            else []
        )
        first_mutation_frontier_item = (
            mutation_frontier_items[0] if mutation_frontier_items else None
        )
        first_mutation_action = None
        if (
            not privacy_review_required_before_recovery
            and not validation_review_required_before_recovery
            and not recovery_preflight_required
            and not imported_session_continuation_required
            and not receiver_session_start_required
            and first_mutation_frontier_item is not None
        ):
            first_mutation_action = first_mutation_frontier_item.action
        first_safe_action: SuggestedNextAction | RevisionNextAction | None = None
        first_safe_action_source: str | None = None
        if privacy_review_required_before_recovery:
            if (
                first_action is not None
                and first_action.tool == "doxabase.export_preflight"
            ):
                first_safe_action = first_action
                first_safe_action_source = "handoff_import_privacy_review"
        elif validation_review_required_before_recovery:
            if (
                first_action is not None
                and first_action.tool == "doxabase.validate_graph"
            ):
                first_safe_action = first_action
                first_safe_action_source = "handoff_import_validation_review"
        elif imported_session_continuation_required:
            first_safe_action = (
                suggested_next_actions[0] if suggested_next_actions else None
            )
            first_safe_action_source = (
                "imported_recovery_session"
                if first_safe_action is not None
                else None
            )
        elif receiver_session_start_required:
            first_safe_action = first_action
            first_safe_action_source = "receiver_local_recovery_session"
        elif recovery_preflight_required and recovery_plan is not None:
            if recovery_plan.blocking_preflight_actions:
                first_safe_action = recovery_plan.blocking_preflight_actions[0]
                first_safe_action_source = "recovery_plan_blocking_preflight"
            elif recovery_plan.suggested_next_actions:
                first_safe_action = recovery_plan.suggested_next_actions[0]
                first_safe_action_source = "recovery_plan_suggested_next_action"
        elif (
            recovery_plan is not None
            and recovery_plan.mutation_allowed_after
            != "handoff_preflight_required_before_mutation"
        ):
            if first_mutation_action is not None:
                first_safe_action = first_mutation_action
                first_safe_action_source = "mutation_frontier"
            elif recovery_plan.helper_mutation_frontier_actions:
                first_safe_action = recovery_plan.helper_mutation_frontier_actions[0]
                first_safe_action_source = "helper_mutation_frontier"
            elif recovery_plan.suggested_next_actions:
                first_safe_action = recovery_plan.suggested_next_actions[0]
                first_safe_action_source = "recovery_plan_suggested_next_action"
        if recovery_plan is not None:
            for summary in recovery_plan.revision_summaries:
                if summary.profile_route_groups:
                    profile_route_revision_count += 1
                    profile_route_group_count += len(summary.profile_route_groups)
                for key in summary.profile_route_keys:
                    if key not in profile_route_keys:
                        profile_route_keys.append(key)

        snapshot_evidence_complete = not incomplete_snapshot_revision_iris
        manifest_revision_set = set(revision_iris)
        has_resolved_targets = any(
            evidence.revision_iri not in manifest_revision_set
            for evidence in snapshot_evidence
        )
        if not revision_iris:
            snapshot_note = "The manifest had no revision rows to recover."
        elif snapshot_evidence_complete:
            snapshot_subject = (
                "manifest revisions and resolved recovery targets"
                if has_resolved_targets
                else "manifest revisions"
            )
            snapshot_note = (
                f"All {snapshot_subject} have history RDF and exact stored "
                "snapshot rows."
            )
        else:
            snapshot_subject = (
                "manifest revisions or resolved recovery targets"
                if has_resolved_targets
                else "manifest revisions"
            )
            snapshot_note = (
                f"Some {snapshot_subject} still lack complete history/snapshot "
                "evidence; inspect post_import_snapshot_evidence and the "
                "recovery_plan lanes before relying on exact drift or "
                "applied-diff rows."
            )
        note = (
            f"{snapshot_note} recommended_next_step={recommended_next_step}."
        )
        if privacy_review_required_before_recovery:
            if dry_run:
                note = (
                    "The handoff manifest dry-run records sensitive-looking "
                    "artifact terms. The dry-run is the non-mutating manifest "
                    "privacy gate; run the real import only for local recovery, "
                    "then follow its export_preflight gate before any recovery "
                    f"or mutation actions. {note}"
                )
            else:
                note = (
                    "The imported handoff manifest records sensitive-looking "
                    "artifact terms; run the suggested export_preflight before "
                    f"following recovery or mutation actions. {note}"
                )
        elif validation_review_required_before_recovery:
            if dry_run:
                note = (
                    "The handoff manifest dry-run records failed export "
                    "validation. The dry-run is the non-mutating validation "
                    "gate; run the real import only for local recovery, then "
                    "follow its validate_graph gate before any recovery or "
                    f"mutation actions. {note}"
                )
            else:
                note = (
                    "The imported handoff manifest records failed export "
                    "validation; run the suggested validate_graph review before "
                    f"following recovery or mutation actions. {note}"
                )
        elif imported_session_continuation_required:
            note = (
                "Continue the imported source recovery session before following "
                f"receiver-local mutation-frontier actions. {note}"
            )
        elif receiver_session_start_required:
            note = (
                "Start a receiver-local recovery session before following "
                f"direct mutation-frontier actions. {note}"
            )
        return HandoffBundleRecoverySummary(
            result_kind="handoff_bundle_recovery_summary",
            dry_run=dry_run,
            revision_count=len(revision_iris),
            snapshot_evidence_complete=snapshot_evidence_complete,
            snapshot_evidence_status_counts=snapshot_status_counts,
            incomplete_snapshot_revision_iris=incomplete_snapshot_revision_iris,
            trig_total_imported=trig_total_imported,
            imported_snapshot_count=(
                revision_snapshots.imported_snapshot_count
                if revision_snapshots is not None
                else 0
            ),
            skipped_snapshot_count=(
                revision_snapshots.skipped_snapshot_count
                if revision_snapshots is not None
                else 0
            ),
            imported_recovery_session_count=len(imported_recovery_session_iris),
            imported_recovery_session_iris=list(imported_recovery_session_iris),
            matching_recovery_session_count=len(matching_recovery_session_iris),
            matching_recovery_session_iris=list(matching_recovery_session_iris),
            resume_recovery_session_iri=resume_recovery_session_iri,
            recovery_plan_available=recovery_plan is not None,
            recovery_lane_counts=(
                dict(recovery_plan.lane_counts)
                if recovery_plan is not None
                else {}
            ),
            recovery_next_action_queue_item_counts=(
                dict(recovery_plan.next_action_queue_item_counts)
                if recovery_plan is not None
                else {}
            ),
            mutation_frontier_iris=(
                list(recovery_plan.mutation_frontier_iris)
                if recovery_plan is not None
                else []
            ),
            mutation_frontier_count=(
                len(recovery_plan.mutation_frontier_iris)
                if recovery_plan is not None
                else 0
            ),
            first_mutation_frontier_item=(
                None
                if privacy_review_required_before_recovery
                or validation_review_required_before_recovery
                or recovery_preflight_required
                or imported_session_continuation_required
                or receiver_session_start_required
                else first_mutation_frontier_item
            ),
            first_mutation_action=first_mutation_action,
            first_safe_review_or_mutation_action=first_safe_action,
            first_safe_review_or_mutation_source=first_safe_action_source,
            profile_route_revision_count=profile_route_revision_count,
            profile_route_group_count=profile_route_group_count,
            profile_route_keys=profile_route_keys,
            first_suggested_next_action=first_action,
            recommended_next_step=recommended_next_step,
            note=note,
        )
    def _import_handoff_bundle_recovery_plan(
        self,
        recovery_plan: StagedRevisionRecoveryPlan,
        *,
        manifest_path: str | None,
        snapshot_path: str,
        revision_snapshots: RevisionSnapshotBundleImportRecord | None,
    ) -> StagedRevisionRecoveryPlan:
        if revision_snapshots is None:
            return recovery_plan
        missing_evidence = self._import_handoff_bundle_missing_resolved_snapshots(
            recovery_plan,
            bundled_snapshot_revision_iris=revision_snapshots.revision_iris,
        )
        if not missing_evidence:
            return recovery_plan
        replacement = self._import_handoff_bundle_broader_snapshot_action(
            missing_evidence,
            manifest_path=manifest_path,
            snapshot_path=snapshot_path,
            revision_snapshots=revision_snapshots,
        )

        def replace_actions(
            actions: list[SuggestedNextAction],
        ) -> list[SuggestedNextAction]:
            replaced = False
            values: list[SuggestedNextAction] = []
            for action in actions:
                if self._is_placeholder_snapshot_import_action(action):
                    if not replaced:
                        values.append(replacement)
                        replaced = True
                    continue
                values.append(action)
            return self._dedupe_suggested_next_actions(values)

        def replace_unattended_steps(
            steps: list[StagedRevisionRecoveryUnattendedStep],
        ) -> list[StagedRevisionRecoveryUnattendedStep]:
            replaced = False
            values: list[StagedRevisionRecoveryUnattendedStep] = []
            for step in steps:
                action = step.action
                if (
                    isinstance(action, SuggestedNextAction)
                    and self._is_placeholder_snapshot_import_action(action)
                ):
                    if not replaced:
                        values.append(
                            replace(
                                step,
                                action=replacement,
                                revision_iris=(
                                    self._suggested_action_revision_iris(
                                        replacement
                                    )
                                ),
                            )
                        )
                        replaced = True
                    continue
                values.append(step)
            return values

        blocking_preflight_actions = replace_actions(
            recovery_plan.blocking_preflight_actions
        )
        suggested_next_actions = replace_actions(recovery_plan.suggested_next_actions)
        recommended_unattended_steps = replace_unattended_steps(
            recovery_plan.recommended_unattended_steps
        )
        (
            first_mutation_action,
            first_safe_review_or_mutation_action,
            first_safe_review_or_mutation_source,
        ) = self._staged_recovery_first_actions(
            mutation_allowed_after=recovery_plan.mutation_allowed_after,
            blocking_preflight_actions=blocking_preflight_actions,
            mutation_frontier_items=recovery_plan.mutation_frontier_items,
            suggested_next_actions=suggested_next_actions,
        )
        return replace(
            recovery_plan,
            blocking_preflight_actions=blocking_preflight_actions,
            recommended_unattended_steps=recommended_unattended_steps,
            first_mutation_action=first_mutation_action,
            first_safe_review_or_mutation_action=(
                first_safe_review_or_mutation_action
            ),
            first_safe_review_or_mutation_source=(
                first_safe_review_or_mutation_source
            ),
            suggested_next_actions=suggested_next_actions,
        )
    def _import_handoff_bundle_privacy_gated_recovery_plan(
        self,
        recovery_plan: StagedRevisionRecoveryPlan,
        privacy_action: SuggestedNextAction,
    ) -> StagedRevisionRecoveryPlan:
        redacted_plan = self._privacy_redacted_api_value(recovery_plan)
        privacy_note = (
            "Imported handoff privacy review is required before following "
            "nested recovery or mutation actions."
        )

        def gated_note(note: str) -> str:
            return f"{privacy_note} {note}"

        def gated_batch_item(
            item: StagedGraphRevisionBatchRestageItem,
        ) -> StagedGraphRevisionBatchRestageItem:
            return replace(
                item,
                next_action_after=None,
                next_action_queue_item_after=None,
                suggested_next_actions_after=[privacy_action],
                note=gated_note(item.note),
            )

        def gated_lane(
            lane: StagedRevisionRecoveryLane,
        ) -> StagedRevisionRecoveryLane:
            return replace(
                lane,
                next_action=None,
                next_action_queue_item=None,
                repair_draft=None,
                repair_draft_deferred_reason="handoff_import_privacy_review_required",
                suggested_next_actions=[privacy_action],
                batch_item=gated_batch_item(lane.batch_item),
                note=gated_note(lane.note),
            )

        def gated_summary(
            summary: StagedGraphRevisionExportSummary,
        ) -> StagedGraphRevisionExportSummary:
            return replace(
                summary,
                next_action=None,
                suggested_next_actions=[privacy_action],
            )

        bundle_summary = redacted_plan.bundle_summary
        if bundle_summary is not None:
            bundle_summary = replace(
                bundle_summary,
                review_sequence=[],
                next_action_queue={},
                next_action_queue_items=[],
                next_action_queue_item_counts={},
                mutation_frontier_iris=[],
                warnings=[
                    privacy_note,
                    *bundle_summary.warnings,
                ],
            )

        privacy_step_revision_iris = (
            self._suggested_action_revision_iris(privacy_action)
            or list(redacted_plan.processed_revision_iris)
        )
        privacy_steps = [
            self._staged_recovery_unattended_step(
                step_kind="review_handoff_privacy",
                label="Review handoff privacy preflight",
                action=privacy_action,
                can_run_now=True,
                prerequisite=None,
                mutates=False,
                requires_replan_after_completion=True,
                stop_reason="rerun_plan_after_handoff_privacy_review",
                revision_iris=privacy_step_revision_iris,
                source_revision_iris=list(redacted_plan.processed_revision_iris),
                target_iris=[],
                note=(
                    "Run this privacy preflight review before following "
                    "imported recovery or mutation actions, then rerun the "
                    "recovery plan."
                ),
            )
        ]

        return replace(
            redacted_plan,
            lanes=[gated_lane(lane) for lane in redacted_plan.lanes],
            next_action_queue={},
            next_action_queue_items=[],
            next_action_queue_item_counts={},
            mutation_frontier_iris=[],
            mutation_frontier_items=[],
            first_mutation_action=None,
            first_safe_review_or_mutation_action=privacy_action,
            first_safe_review_or_mutation_source="handoff_import_privacy_review",
            helper_mutation_frontier_actions=[],
            mutation_allowed_after=(
                "handoff_import_privacy_review_required_before_recovery"
            ),
            blocking_preflight_actions=[privacy_action],
            recommended_unattended_steps=privacy_steps,
            revision_summaries=[
                gated_summary(summary)
                for summary in redacted_plan.revision_summaries
            ],
            bundle_summary=bundle_summary,
            suggested_next_actions=[privacy_action],
            warnings=[
                privacy_note,
                *redacted_plan.warnings,
            ],
            note=gated_note(redacted_plan.note),
        )
    def _import_handoff_bundle_session_gated_recovery_plan(
        self,
        recovery_plan: StagedRevisionRecoveryPlan,
        session_actions: list[SuggestedNextAction],
    ) -> StagedRevisionRecoveryPlan:
        session_actions = self._dedupe_suggested_next_actions(session_actions)
        if not session_actions:
            return recovery_plan
        session_action = session_actions[0]
        session_note = (
            "Continue the imported source recovery session before following "
            "nested recovery or mutation actions."
        )
        session_step_revision_iris = (
            self._suggested_action_revision_iris(session_action)
            or list(recovery_plan.processed_revision_iris)
        )
        session_steps = [
            self._staged_recovery_unattended_step(
                step_kind="continue_imported_recovery_session",
                label="Continue imported recovery session",
                action=session_action,
                can_run_now=True,
                prerequisite=None,
                mutates=False,
                requires_replan_after_completion=True,
                stop_reason="rerun_plan_after_imported_recovery_session",
                revision_iris=session_step_revision_iris,
                source_revision_iris=list(recovery_plan.processed_revision_iris),
                target_iris=[],
                note=(
                    "Describe the imported source recovery session first, then "
                    "rerun receiver-local recovery planning before applying any "
                    "mutation-frontier action."
                ),
            )
        ]
        suggested_next_actions = self._dedupe_suggested_next_actions(
            [
                *session_actions,
                *recovery_plan.suggested_next_actions,
            ]
        )
        return replace(
            recovery_plan,
            first_mutation_action=None,
            first_safe_review_or_mutation_action=session_action,
            first_safe_review_or_mutation_source="imported_recovery_session",
            helper_mutation_frontier_actions=[],
            mutation_allowed_after=(
                "imported_recovery_session_required_before_mutation"
            ),
            blocking_preflight_actions=session_actions,
            recommended_unattended_steps=session_steps,
            suggested_next_actions=suggested_next_actions,
            warnings=[
                session_note,
                *recovery_plan.warnings,
            ],
            note=f"{session_note} {recovery_plan.note}",
        )
    def _import_handoff_bundle_validation_gated_recovery_plan(
        self,
        recovery_plan: StagedRevisionRecoveryPlan,
        validation_action: SuggestedNextAction,
    ) -> StagedRevisionRecoveryPlan:
        validation_note = (
            "Imported handoff validation review is required before following "
            "nested recovery or mutation actions."
        )

        def gated_note(note: str) -> str:
            return f"{validation_note} {note}"

        def gated_batch_item(
            item: StagedGraphRevisionBatchRestageItem,
        ) -> StagedGraphRevisionBatchRestageItem:
            return replace(
                item,
                next_action_after=None,
                next_action_queue_item_after=None,
                suggested_next_actions_after=[validation_action],
                note=gated_note(item.note),
            )

        def gated_lane(
            lane: StagedRevisionRecoveryLane,
        ) -> StagedRevisionRecoveryLane:
            return replace(
                lane,
                next_action=None,
                next_action_queue_item=None,
                repair_draft=None,
                repair_draft_deferred_reason=(
                    "handoff_import_validation_review_required"
                ),
                suggested_next_actions=[validation_action],
                batch_item=gated_batch_item(lane.batch_item),
                note=gated_note(lane.note),
            )

        def gated_summary(
            summary: StagedGraphRevisionExportSummary,
        ) -> StagedGraphRevisionExportSummary:
            return replace(
                summary,
                next_action=None,
                suggested_next_actions=[validation_action],
            )

        bundle_summary = recovery_plan.bundle_summary
        if bundle_summary is not None:
            bundle_summary = replace(
                bundle_summary,
                review_sequence=[],
                next_action_queue={},
                next_action_queue_items=[],
                next_action_queue_item_counts={},
                mutation_frontier_iris=[],
                warnings=[
                    validation_note,
                    *bundle_summary.warnings,
                ],
            )

        validation_step_revision_iris = (
            self._suggested_action_revision_iris(validation_action)
            or list(recovery_plan.processed_revision_iris)
        )
        validation_steps = [
            self._staged_recovery_unattended_step(
                step_kind="review_handoff_validation",
                label="Review handoff validation failures",
                action=validation_action,
                can_run_now=True,
                prerequisite=None,
                mutates=False,
                requires_replan_after_completion=True,
                stop_reason="rerun_plan_after_handoff_validation_review",
                revision_iris=validation_step_revision_iris,
                source_revision_iris=list(recovery_plan.processed_revision_iris),
                target_iris=[],
                note=(
                    "Run this validation review before following imported "
                    "recovery or mutation actions, then rerun the recovery "
                    "plan."
                ),
            )
        ]

        return replace(
            recovery_plan,
            lanes=[gated_lane(lane) for lane in recovery_plan.lanes],
            next_action_queue={},
            next_action_queue_items=[],
            next_action_queue_item_counts={},
            mutation_frontier_iris=[],
            mutation_frontier_items=[],
            first_mutation_action=None,
            first_safe_review_or_mutation_action=validation_action,
            first_safe_review_or_mutation_source="handoff_import_validation_review",
            helper_mutation_frontier_actions=[],
            mutation_allowed_after=(
                "handoff_import_validation_review_required_before_recovery"
            ),
            blocking_preflight_actions=[validation_action],
            recommended_unattended_steps=validation_steps,
            revision_summaries=[
                gated_summary(summary)
                for summary in recovery_plan.revision_summaries
            ],
            bundle_summary=bundle_summary,
            suggested_next_actions=[validation_action],
            warnings=[
                validation_note,
                *recovery_plan.warnings,
            ],
            note=gated_note(recovery_plan.note),
        )
    @staticmethod
    def _handoff_recovery_summary_snapshot_evidence(
        snapshot_evidence: list[RevisionSnapshotEvidenceStatus],
        *,
        recovery_plan: StagedRevisionRecoveryPlan | None,
    ) -> list[RevisionSnapshotEvidenceStatus]:
        evidence_by_revision: dict[str, RevisionSnapshotEvidenceStatus] = {}
        revision_order: list[str] = []

        def add_evidence(evidence: RevisionSnapshotEvidenceStatus) -> None:
            if evidence.revision_iri not in evidence_by_revision:
                revision_order.append(evidence.revision_iri)
            evidence_by_revision[evidence.revision_iri] = evidence

        for evidence in snapshot_evidence:
            add_evidence(evidence)
        if recovery_plan is not None:
            for lane in recovery_plan.lanes:
                add_evidence(lane.source_snapshot_evidence)
                add_evidence(lane.current_snapshot_evidence)

        return [evidence_by_revision[revision_iri] for revision_iri in revision_order]
    def _import_handoff_bundle_recovery_session_actions(
        self,
        *,
        matching_recovery_session_iris: list[str],
        recovery_plan: StagedRevisionRecoveryPlan,
        manifest_path: str | None,
        include_drafts: bool,
        validation_scope: str | None,
        drift_detail: str,
    ) -> list[SuggestedNextAction]:
        if matching_recovery_session_iris:
            return [
                self._describe_imported_recovery_session_action(
                    session_iri,
                    include_drafts=include_drafts,
                    validation_scope=validation_scope,
                    drift_detail=drift_detail,
                )
                for session_iri in matching_recovery_session_iris
            ]
        if not recovery_plan.processed_revision_iris:
            return []
        return [
            self._start_receiver_recovery_session_action(
                recovery_plan.processed_revision_iris,
                manifest_path=manifest_path,
                include_drafts=include_drafts,
                validation_scope=validation_scope,
                drift_detail=drift_detail,
            )
        ]
    def _describe_imported_recovery_session_action(
        self,
        session_iri: str,
        *,
        include_drafts: bool,
        validation_scope: str | None,
        drift_detail: str,
    ) -> SuggestedNextAction:
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
                   reason="The handoff imported a persisted staged-revision recovery "
                "session whose source revisions overlap the manifest revisions. "
                "Describe it before starting a receiver-local session so source "
                "session provenance and live recovery state stay connected.",
               )
    def _start_receiver_recovery_session_action(
        self,
        revision_iris: list[str],
        *,
        manifest_path: str | None,
        include_drafts: bool,
        validation_scope: str | None,
        drift_detail: str,
    ) -> SuggestedNextAction:
        arguments: dict[str, Any] = {
            "revision_iris": revision_iris,
            "start_session": True,
            "current_staged_work_only": False,
            "include_drafts": include_drafts,
            "drift_detail": drift_detail,
        }
        if manifest_path is not None:
            arguments["handoff_manifest_path"] = manifest_path
        if validation_scope is not None:
            arguments["validation_scope"] = validation_scope
        return SuggestedNextAction(
                   tool="doxabase.plan_staged_revision_recovery",
                   args=arguments,
                   reason="No matching imported recovery session was found. Persist a "
                "receiver-local session for the imported manifest revisions so "
                "multi-step restage, repair, and apply work can be replanned "
                "from one stable session IRI.",
               )
