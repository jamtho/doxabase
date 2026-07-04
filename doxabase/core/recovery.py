"""Staged revision recovery planning and sessions.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via RecoveryMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class RecoveryMixin:
    def draft_staged_revision_rebase(
        self,
        iri: str,
        *,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
    ) -> StagedRevisionRebaseDraft:
        source = self.describe_staged_revision(iri)
        check = self.check_staged_revision_apply(
            source.iri,
            validation_scope=validation_scope,
        )
        source_staged_validation_status = self._staged_validation_status(
            conforms=source.validation_conforms,
            result_count=source.validation_result_count,
        )
        repair_actions = [
            action
            for action in check.suggested_next_actions
            if action.tool_name == "stage_map_assertion_change"
        ]
        repair_candidates = [
            candidate
            for action in repair_actions
            if (
                candidate := self._staged_rebase_candidate_from_action(
                    check,
                    action,
                    validation_results=check.validation_results,
                )
            )
            is not None
        ]
        validation_repair_candidates = (
            self._staged_validation_same_slot_rebase_candidates(
                source,
                check,
                validation_scope=validation_scope or check.validation_scope,
            )
            if check.status == "validation_failed"
            else []
        )
        for candidate in validation_repair_candidates:
            if all(
                candidate.action.arguments != existing.arguments
                for existing in repair_actions
            ):
                repair_candidates.append(candidate)
                repair_actions.append(candidate.action)

        preferred_action = repair_actions[0] if repair_actions else None
        action_candidates = [*repair_actions, *check.suggested_next_actions]
        if any(
            action.tool_name != "draft_staged_revision_rebase"
            for action in action_candidates
        ):
            action_candidates = [
                action
                for action in action_candidates
                if action.tool_name != "draft_staged_revision_rebase"
            ]
        suggested_next_actions = self._dedupe_suggested_next_actions(
            action_candidates
        )
        draft_next_action = (
            self._revision_next_action_from_rebase_repair(preferred_action)
            if preferred_action is not None
            else self._revision_next_action_from_rebase_fallback(
                check,
                suggested_next_actions,
            )
        )
        current_revision_iri = self._staged_rebase_current_revision_iri(source)
        next_action_queue_item = self._revision_next_action_queue_item(
            row_iri=source.iri,
            next_action=draft_next_action,
            record_kind=self._graph_revision_record_kind_for_iri(source.iri),
            application_status=check.status,
            application_decision=check.decision,
            stale_resolution_state=check.stale_resolution_state,
            staged_validation_status=source_staged_validation_status,
            semantic_risk_level=check.semantic_risk_level,
            semantic_risk_reasons=check.semantic_risk_reasons,
            alternative_gate=check.alternative_gate,
        )
        draft_status, draft_kind, reason_codes, note = (
            self._staged_rebase_draft_route(
                source,
                check,
                repair_actions=repair_actions,
                source_staged_validation_status=source_staged_validation_status,
            )
        )
        return StagedRevisionRebaseDraft(
            result_kind="staged_revision_rebase_draft",
            helper="draft_staged_revision_rebase",
            mode="non_executed_review_draft",
            source_revision_iri=source.iri,
            current_revision_iri=current_revision_iri,
            draft_status=draft_status,
            draft_kind=draft_kind,
            reason_codes=reason_codes,
            source_staged_validation_status=source_staged_validation_status,
            apply_check=check,
            lineage=self._staged_rebase_lineage_context(
                source.iri,
                alternative_gate=check.alternative_gate,
            ),
            validation_results=check.validation_results or source.validation_results,
            repair_candidates=repair_candidates,
            repair_actions=repair_actions,
            preferred_action=preferred_action,
            next_action=draft_next_action,
            next_action_queue_item=next_action_queue_item,
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[
                action.call for action in suggested_next_actions
            ],
            note=note,
        )
    def _staged_rebase_draft_route(
        self,
        source: StagedGraphRevisionDescription,
        check: StagedRevisionApplyCheck,
        *,
        repair_actions: list[SuggestedNextAction],
        source_staged_validation_status: str,
    ) -> tuple[str, str, list[str], str]:
        if source.applied_by is not None:
            return (
                "redirect",
                "already_applied",
                ["already_applied"],
                (
                    "The selected staged revision has already been applied; "
                    "follow the applied-event inspection route instead of "
                    "drafting a repair."
                ),
            )
        if source.current_restaged_by is not None or source.restaged_by is not None:
            return (
                "redirect",
                "already_handled",
                ["already_has_restage_successor"],
                (
                    "The selected staged revision already has a refreshed "
                    "successor; inspect that current successor before drafting "
                    "another repair."
                ),
            )
        if repair_actions:
            return (
                "drafted",
                "same_slot_replacement",
                ["same_slot_replacement"],
                (
                    "Drafted a reviewed stage_map_assertion_change replacement "
                    "candidate. The helper did not stage or apply it."
                ),
            )
        if self._staged_apply_check_has_ambiguous_same_slot_review(check):
            return (
                "not_drafted",
                "ambiguous_same_slot",
                list(dict.fromkeys(["ambiguous_same_slot", *check.blocking_reasons])),
                (
                    "Exact snapshot drift points at a single-valued map slot, "
                    "but the current graph has multiple values. Inspect the "
                    "current assertions and stage an explicit repair or "
                    "replacement; this helper will not draft a mechanical "
                    "same-slot replacement."
                ),
            )
        if self._staged_patch_repair_plan_has_semantic_repair(
            check.patch_repair_plan
        ):
            return (
                "not_drafted",
                "patch_repair_plan",
                list(dict.fromkeys(["patch_repair_plan", *check.blocking_reasons])),
                (
                    "Patch-level repair planning found a semantic same-slot "
                    "subpatch inside a larger stale revision. Inspect "
                    "apply_check.patch_repair_plan and author a complete "
                    "repaired successor; the helper did not stage or apply it."
                ),
            )
        if source_staged_validation_status == "failed":
            reason_codes = list(
                dict.fromkeys(["staged_validation_failed", *check.blocking_reasons])
            )
            return (
                "not_drafted",
                "validation_repair_needed",
                reason_codes,
                (
                    "The selected staged revision already had staged-time "
                    "validation failures, and this helper did not recognize a "
                    "safe single-slot replacement candidate. Inspect stored "
                    "validation_results before restaging or authoring a repair."
                ),
            )
        if check.status == "conflict" and self._staged_apply_check_is_restageable_conflict(
            check.blocking_reasons
        ):
            return (
                "not_drafted",
                "mechanical_restage_available",
                check.blocking_reasons,
                (
                    "This looks like ordinary count/digest drift; review the "
                    "source and use restage_staged_revision if the patch intent "
                    "is still desired."
                ),
            )
        if check.status == "validation_failed":
            return (
                "not_drafted",
                "validation_repair_needed",
                check.blocking_reasons,
                (
                    "Validation failed, but this helper did not recognize a "
                    "safe single-slot replacement candidate. Inspect "
                    "validation_results and stage a reviewed repair manually."
                ),
            )
        if check.status == "noop":
            return (
                "not_drafted",
                "already_effective",
                check.blocking_reasons,
                (
                    "The staged patch has no effective graph delta; inspect the "
                    "current graph state before replacing or ignoring it."
                ),
            )
        if check.status == "ready":
            return (
                "not_drafted",
                "already_ready",
                [],
                "The staged revision is already apply-ready; review before applying.",
            )
        if check.status == "already_applied":
            return (
                "redirect",
                "already_applied",
                check.blocking_reasons,
                "The staged revision is already applied; inspect the applied event.",
            )
        return (
            "not_drafted",
            "patch_conflict_repair_needed",
            check.blocking_reasons or ["not_ready"],
            "Inspect patch checks and validation details before staging a repair.",
        )
    def _staged_rebase_current_revision_iri(
        self,
        source: StagedGraphRevisionDescription,
    ) -> str:
        if source.current_restaged_by is not None:
            return source.current_restaged_by.iri
        if source.restaged_by is not None:
            return source.restaged_by.iri
        if source.applied_by is not None:
            return source.applied_by.iri
        return source.iri
    def _staged_rebase_lineage_context(
        self,
        revision_iri: str,
        *,
        alternative_gate: StagedRevisionAlternativeGate,
    ) -> StagedRevisionRebaseLineageContext:
        lineage = self.describe_revision_lineage(
            revision_iri,
            include_apply_checks=True,
        )
        return StagedRevisionRebaseLineageContext(
            selected_revision_iri=lineage.selected_revision.iri,
            current_staged_revision_iri=lineage.current_staged_revision_iri,
            current_revision_iri=lineage.current_revision_iri,
            latest_revision_iri=lineage.latest_revision_iri,
            latest_role=lineage.latest_role,
            restage_chain_iris=lineage.restage_chain_iris,
            alternative_revision_iris=lineage.alternative_revision_iris,
            related_revision_iris=lineage.related_revision_iris,
            alternative_to=alternative_gate.alternative_to,
            current_alternative_to=alternative_gate.current_alternative_to,
            alternative_gate_status=alternative_gate.status,
            alternative_semantic_review_required=(
                alternative_gate.semantic_review_required
            ),
            alternative_applied_source_iri=alternative_gate.applied_source_iri,
            alternative_applied_revision_iri=(
                alternative_gate.applied_revision_iri
            ),
        )
    @staticmethod
    def _dedupe_suggested_next_actions(
        actions: Iterable[SuggestedNextAction],
    ) -> list[SuggestedNextAction]:
        deduped: list[SuggestedNextAction] = []
        seen: set[tuple[str, str, str]] = set()
        for action in actions:
            key = (
                action.tool_name,
                action.call,
                json.dumps(action.arguments, sort_keys=True, default=str),
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(action)
        return deduped
    @staticmethod
    def _revision_next_action_from_rebase_repair(
        action: SuggestedNextAction | None,
    ) -> RevisionNextAction | None:
        if action is None:
            return None
        return RevisionNextAction(
            action_type="repair_or_replace",
            queue="repair_or_replace",
            action_label=action.action_label,
            tool_name=action.tool_name,
            mcp_tool_name=action.mcp_tool_name,
            arguments=action.arguments,
            reason=action.reason,
            call=action.call,
            source="draft_staged_revision_rebase",
        )
    @staticmethod
    def _revision_next_action_from_rebase_fallback(
        check: StagedRevisionApplyCheck,
        suggested_next_actions: list[SuggestedNextAction],
    ) -> RevisionNextAction | None:
        if (
            check.next_action is not None
            and check.next_action.tool_name != "draft_staged_revision_rebase"
        ):
            return check.next_action
        selected_action = next(
            (
                action
                for action in suggested_next_actions
                if action.tool_name
                in {
                    "describe_staged_revision",
                    "export_staged_revision",
                    "export_staged_revisions",
                    "describe_revision_lineage",
                }
            ),
            suggested_next_actions[0] if suggested_next_actions else None,
        )
        action_type = (
            check.next_action.action_type
            if check.next_action is not None
            else "repair_or_replace"
        )
        queue = (
            check.next_action.queue
            if check.next_action is not None
            else "repair_or_replace"
        )
        if selected_action is not None:
            return RevisionNextAction(
                action_type=action_type,
                queue=queue,
                action_label=selected_action.action_label,
                tool_name=selected_action.tool_name,
                mcp_tool_name=selected_action.mcp_tool_name,
                arguments=selected_action.arguments,
                reason=selected_action.reason,
                call=selected_action.call,
                source="draft_staged_revision_rebase",
            )
        return RevisionNextAction(
            action_type=action_type,
            queue=queue,
            action_label="Inspect manual repair",
            tool_name=None,
            mcp_tool_name=None,
            arguments={},
            reason=(
                "This rebase draft did not recognize a safe automatic repair; "
                "inspect validation and patch diagnostics before authoring a "
                "manual repair or replacement."
            ),
            call=None,
            source="draft_staged_revision_rebase",
        )
    def _staged_rebase_candidate_from_action(
        self,
        check: StagedRevisionApplyCheck,
        action: SuggestedNextAction,
        *,
        validation_results: list[ValidationDiagnostic],
    ) -> StagedRevisionRebaseCandidate | None:
        arguments = action.arguments
        subject = arguments.get("subject")
        predicate = arguments.get("predicate")
        object_value = arguments.get("object")
        graph = arguments.get("graph", "map")
        object_kind = arguments.get("object_kind", "auto")
        if (
            not isinstance(subject, str)
            or not isinstance(predicate, str)
            or not isinstance(object_kind, str)
            or graph != "map"
            or object_value is not None
            and not isinstance(object_value, str)
        ):
            return None
        object_datatype = arguments.get("object_datatype")
        object_lang = arguments.get("object_lang")
        if object_datatype is not None and not isinstance(object_datatype, str):
            object_datatype = None
        if object_lang is not None and not isinstance(object_lang, str):
            object_lang = None
        support = self.describe_assertion_support(
            subject=subject,
            predicate=predicate,
            object=object_value,
            graph="map",
            object_kind=object_kind,  # type: ignore[arg-type]
            object_datatype=object_datatype,
            object_lang=object_lang,
        )
        proposed_triples = []
        if object_value is not None:
            proposed_triple = self._rebase_action_proposed_triple(
                subject,
                predicate,
                object_value,
                object_kind=object_kind,
                object_datatype=object_datatype,
                object_lang=object_lang,
            )
            if proposed_triple is not None:
                proposed_triples.append(proposed_triple)
        note = (
            "This candidate preserves restage provenance and replaces current "
            "same-subject/predicate map values after review."
        )
        if check.alternative_gate.semantic_review_required:
            note += (
                " The selected revision is gated as a semantic alternative to "
                "an already-applied staged source; review both alternatives "
                "before applying any repaired successor."
            )
        return StagedRevisionRebaseCandidate(
            candidate_kind="same_slot_replacement",
            candidate_status="ready_to_stage",
            graph="map",
            subject=support.subject.iri,
            predicate=support.predicate,
            object=(
                support.requested_object.value
                if support.requested_object is not None
                else object_value
            ),
            object_kind=(
                support.requested_object.value_kind
                if support.requested_object is not None
                else object_kind
            ),
            object_datatype=(
                support.requested_object.datatype
                if support.requested_object is not None
                else object_datatype
            ),
            object_lang=(
                support.requested_object.lang
                if support.requested_object is not None
                else object_lang
            ),
            current_same_subject_predicate_triples=(
                support.same_subject_predicate_triples
            ),
            proposed_triples=proposed_triples,
            validation_results=validation_results,
            action=action,
            note=note,
        )
    def _rebase_action_proposed_triple(
        self,
        subject: str,
        predicate: str,
        object_value: str,
        *,
        object_kind: str,
        object_datatype: str | None = None,
        object_lang: str | None = None,
    ) -> GraphTripleDescription | None:
        object_filter = self._assertion_object_filter(
            object_value,
            object_kind,
            object_datatype=object_datatype,
            object_lang=object_lang,
        )
        if object_filter is None:
            return None
        stored_object, stored_kind, stored_datatype, stored_lang = object_filter
        return self._graph_triple_description(
            (
                self.expand_iri(subject),
                "uri",
                self.expand_iri(predicate),
                stored_object,
                stored_kind,
                stored_datatype,
                stored_lang,
            )
        )
    def _staged_validation_same_slot_rebase_candidates(
        self,
        source: StagedGraphRevisionDescription,
        check: StagedRevisionApplyCheck,
        *,
        validation_scope: str,
    ) -> list[StagedRevisionRebaseCandidate]:
        candidates: list[StagedRevisionRebaseCandidate] = []
        max_count_component = PREFIXES["sh"] + "MaxCountConstraintComponent"
        for diagnostic in check.validation_results:
            if (
                diagnostic.focus_node is None
                or diagnostic.result_path is None
                or diagnostic.source_constraint_component != max_count_component
            ):
                continue
            replacement_label = self._staged_same_slot_replacement_label(
                diagnostic.focus_node,
                diagnostic.result_path,
            )
            if replacement_label is None:
                continue
            candidate = self._staged_validation_same_slot_candidate_for_diagnostic(
                source,
                diagnostic,
                replacement_label=replacement_label,
                validation_scope=validation_scope,
            )
            if candidate is not None:
                candidates.append(candidate)
        return candidates
    def plan_staged_revision_recovery(
        self,
        revision_iris: Iterable[str] | str | None = None,
        *,
        current_staged_work_only: bool = True,
        include_drafts: bool = True,
        repair_draft_limit: int | None = 1,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
        drift_detail: TypingLiteral["summary", "exact"] = "summary",
        limit: int = 50,
        offset: int = 0,
    ) -> StagedRevisionRecoveryPlan:
        if drift_detail not in {"summary", "exact"}:
            raise DoxaBaseError("drift_detail must be 'summary' or 'exact'")
        self._ensure_non_negative("limit", limit)
        self._ensure_non_negative("offset", offset)
        if repair_draft_limit is not None:
            self._ensure_non_negative("repair_draft_limit", repair_draft_limit)
        effective_repair_draft_limit = repair_draft_limit if include_drafts else 0
        selection_mode: str
        requested_revision_iris: list[str] | None
        total_count: int
        selected_revision_iris: list[str]
        if revision_iris is None:
            selection_mode = (
                "current_staged_work"
                if current_staged_work_only
                else "listed_staged_revisions"
            )
            requested_revision_iris = None
            listing = self.list_graph_revisions(
                revision_type="rc:StagedRevision",
                include_apply_checks=False,
                drift_detail=drift_detail,
                current_staged_work_only=False,
                limit=1_000_000 if current_staged_work_only else limit,
                offset=0 if current_staged_work_only else offset,
            )
            if current_staged_work_only:
                current_items = [
                    item for item in listing.revisions if item.is_current_staged_work
                ]
                selected_revision_iris = [
                    item.iri for item in current_items[offset : offset + limit]
                ]
                total_count = len(current_items)
            else:
                selected_revision_iris = [item.iri for item in listing.revisions]
                total_count = listing.total_count
        else:
            selection_mode = "explicit_revision_iris"
            requested_revision_iris = list(
                dict.fromkeys(
                    self._string_values(
                        "revision_iris",
                        revision_iris,
                    )
                )
            )
            total_count = len(requested_revision_iris)
            selected_revision_iris = requested_revision_iris[offset : offset + limit]

        if not selected_revision_iris:
            return self._empty_staged_revision_recovery_plan(
                selection_mode=selection_mode,
                requested_revision_iris=requested_revision_iris,
                current_staged_work_only=current_staged_work_only,
                include_drafts=include_drafts,
                repair_draft_limit=effective_repair_draft_limit,
                validation_scope=validation_scope,
                drift_detail=drift_detail,
                limit=limit,
                offset=offset,
                total_count=total_count,
            )

        history_graphs = self._expand_graphs(["history"])
        (
            restage_revision_iris,
            patchless_staged_history_iris,
            non_staged_history_iris,
            snapshot_only_revision_iris,
            applied_event_iris,
        ) = self._staged_recovery_split_non_patch_inputs(
            selected_revision_iris,
            history_graphs=history_graphs,
        )

        if restage_revision_iris:
            batch = self.restage_staged_revisions(
                restage_revision_iris,
                dry_run=True,
                validation_scope=validation_scope,
            )
        else:
            batch = self._empty_staged_recovery_batch(
                selected_revision_iris,
            )
        summary_by_iri = {
            summary.revision_iri: summary for summary in batch.revision_summaries
        }
        warnings = list(batch.bundle_summary.warnings)
        lanes: list[StagedRevisionRecoveryLane] = []
        repair_draft_attempted_count = 0
        repair_drafts_included_count = 0
        repair_drafts_deferred_count = 0
        for item in batch.items:
            remaining_repair_drafts = (
                None
                if effective_repair_draft_limit is None
                else max(effective_repair_draft_limit - repair_draft_attempted_count, 0)
            )
            (
                lane,
                warning,
                repair_draft_attempted,
                repair_draft_deferred,
            ) = self._staged_recovery_lane_from_batch_item(
                item,
                summary_by_iri=summary_by_iri,
                include_drafts=include_drafts,
                repair_drafts_remaining=remaining_repair_drafts,
                validation_scope=validation_scope,
            )
            lanes.append(lane)
            if repair_draft_attempted:
                repair_draft_attempted_count += 1
            if lane.repair_draft is not None:
                repair_drafts_included_count += 1
            if repair_draft_deferred:
                repair_drafts_deferred_count += 1
            if warning is not None:
                warnings.append(warning)

        patchless_batch_items = [
            self._patchless_staged_history_recovery_item(
                revision_iri,
                history_graphs=history_graphs,
            )
            for revision_iri in patchless_staged_history_iris
        ]
        non_staged_history_items = [
            self._non_staged_history_recovery_item(
                revision_iri,
                history_graphs=history_graphs,
            )
            for revision_iri in non_staged_history_iris
        ]
        snapshot_only_batch_items = [
            self._snapshot_only_recovery_item(
                revision_iri,
                history_graphs=history_graphs,
            )
            for revision_iri in snapshot_only_revision_iris
        ]
        applied_event_batch_items = [
            self._applied_event_recovery_item(
                revision_iri,
                history_graphs=history_graphs,
            )
            for revision_iri in applied_event_iris
        ]
        for item in patchless_batch_items:
            lane, warning, _, _ = self._staged_recovery_lane_from_batch_item(
                item,
                summary_by_iri=summary_by_iri,
                include_drafts=False,
                repair_drafts_remaining=0,
                validation_scope=validation_scope,
            )
            lanes.append(lane)
            if warning is not None:
                warnings.append(warning)
            warnings.append(
                "Recovery selection includes staged revision history "
                f"metadata without patch payload: {item.source_revision_iri}. "
                "It cannot be applied or restaged until a project/history RDF "
                "bundle with patch entries is imported; valid staged patch rows "
                "in the same request were still planned."
            )
        for item in non_staged_history_items:
            lane, warning, _, _ = self._staged_recovery_lane_from_batch_item(
                item,
                summary_by_iri=summary_by_iri,
                include_drafts=False,
                repair_drafts_remaining=0,
                validation_scope=validation_scope,
            )
            lanes.append(lane)
            if warning is not None:
                warnings.append(warning)
            warnings.append(
                "Recovery selection includes non-staged graph-revision history "
                f"context: {item.source_revision_iri}. It is available for "
                "inspection and snapshot evidence, but is not an apply/restage "
                "target."
            )
        for item in snapshot_only_batch_items:
            lane, warning, _, _ = self._staged_recovery_lane_from_batch_item(
                item,
                summary_by_iri=summary_by_iri,
                include_drafts=False,
                repair_drafts_remaining=0,
                validation_scope=validation_scope,
            )
            lanes.append(lane)
            if warning is not None:
                warnings.append(warning)
            warnings.append(
                "Recovery selection includes snapshot rows without RDF history "
                f"metadata: {item.source_revision_iri}. Import the "
                "project/history RDF bundle before applying, restaging, or "
                "repairing this revision."
            )
        for item in applied_event_batch_items:
            lane, warning, _, _ = self._staged_recovery_lane_from_batch_item(
                item,
                summary_by_iri=summary_by_iri,
                include_drafts=False,
                repair_drafts_remaining=0,
                validation_scope=validation_scope,
            )
            lanes.append(lane)
            if warning is not None:
                warnings.append(warning)

        lanes = self._staged_recovery_order_lanes(
            lanes,
            selected_revision_iris=selected_revision_iris,
        )

        if batch.bundle_summary.sequential_apply_recheck_candidate_iris:
            warnings.append(
                "Plan includes staged revisions that share changed graphs; "
                "apply at most one ready row, then rerun "
                "plan_staged_revision_recovery before taking the next mutation."
            )
        lane_counts = self._staged_recovery_lane_counts(lanes)
        queue_items = [
            lane.next_action_queue_item
            for lane in lanes
            if lane.next_action_queue_item is not None
        ]
        queue_items = self._revision_next_action_queue_items_with_alternative_sets(
            queue_items,
            (
                (
                    lane.row_iri,
                    (
                        lane.alternative_gate.alternative_to
                        if lane.alternative_gate is not None
                        else None
                    ),
                    (
                        lane.alternative_gate.current_alternative_to
                        if lane.alternative_gate is not None
                        else None
                    ),
                )
                for lane in lanes
            ),
        )
        enriched_queue_item_by_row = {item.row_iri: item for item in queue_items}
        lanes = [
            replace(
                lane,
                next_action_queue_item=enriched_queue_item_by_row.get(
                    lane.row_iri,
                    lane.next_action_queue_item,
                ),
            )
            if lane.next_action_queue_item is not None
            else lane
            for lane in lanes
        ]
        mutation_frontier_iris = self._revision_mutation_frontier_iris(queue_items)
        helper_mutation_frontier_actions = (
            self._staged_recovery_helper_mutation_frontier_actions(lanes)
        )
        if helper_mutation_frontier_actions:
            warnings.append(
                "Plan includes repair helper actions that are required before "
                "a concrete successor exists; these helper mutations are listed "
                "in helper_mutation_frontier_actions and are not represented by "
                "mutation_frontier_iris."
            )
        repair_inspection_required = (
            self._staged_recovery_repair_inspection_required(lanes)
        )
        if repair_drafts_deferred_count:
            warnings.append(
                "Plan deferred "
                f"{repair_drafts_deferred_count} embedded repair draft(s) "
                f"because repair_draft_limit={effective_repair_draft_limit}. "
                "All repair lanes remain visible; call "
                "draft_staged_revision_rebase for a deferred lane or rerun the "
                "planner with a larger repair_draft_limit when deeper embedded "
                "drafts are needed."
            )
        if repair_inspection_required:
            warnings.append(
                "Plan includes repair_or_replace lanes whose selected action is "
                "diagnostic inspection or a read-only repair draft; these rows "
                "remain in lanes and next_action_queue but are not represented "
                "by mutation_frontier_iris or mutation_frontier_items until a "
                "concrete repair mutation is chosen."
            )
        resolved_target_groups = self._staged_recovery_resolved_target_groups(
            lanes,
            requested_revision_iris=requested_revision_iris,
        )
        mutation_frontier_items = (
            self._staged_recovery_mutation_frontier_items(
                resolved_target_groups,
                lanes=lanes,
                helper_mutation_frontier_actions=(
                    helper_mutation_frontier_actions
                ),
            )
        )
        requires_recheck_after_each_apply = bool(
            batch.bundle_summary.sequential_apply_recheck_candidate_iris
        )
        suggested_next_actions = self._staged_recovery_suggested_next_actions(
            lanes,
            would_restage_revision_iris=batch.would_restage_revision_iris,
        )
        blocking_preflight_actions = (
            self._staged_recovery_blocking_preflight_actions(
                suggested_next_actions
            )
        )
        mutation_allowed_after = (
            self._staged_recovery_mutation_allowed_after(
                blocking_preflight_actions=blocking_preflight_actions,
                mutation_frontier_items=mutation_frontier_items,
                repair_inspection_required=repair_inspection_required,
            )
        )
        (
            first_mutation_action,
            first_safe_review_or_mutation_action,
            first_safe_review_or_mutation_source,
        ) = self._staged_recovery_first_actions(
            mutation_allowed_after=mutation_allowed_after,
            blocking_preflight_actions=blocking_preflight_actions,
            mutation_frontier_items=mutation_frontier_items,
            suggested_next_actions=suggested_next_actions,
        )
        recommended_unattended_steps = (
            self._staged_recovery_recommended_unattended_steps(
                blocking_preflight_actions=blocking_preflight_actions,
                would_restage_revision_iris=batch.would_restage_revision_iris,
                helper_mutation_frontier_actions=(
                    helper_mutation_frontier_actions
                ),
                mutation_frontier_items=mutation_frontier_items,
                suggested_next_actions=suggested_next_actions,
                requires_recheck_after_each_apply=(
                    requires_recheck_after_each_apply
                ),
            )
        )
        processed_revision_iris = list(dict.fromkeys(selected_revision_iris))
        current_revision_by_source = {
            **batch.current_revision_by_source,
            **{
                revision_iri: revision_iri
                for revision_iri in [
                    *patchless_staged_history_iris,
                    *non_staged_history_iris,
                    *snapshot_only_revision_iris,
                    *applied_event_iris,
                ]
            },
        }
        review_revision_iris = list(
            dict.fromkeys(
                [
                    *batch.review_revision_iris,
                    *patchless_staged_history_iris,
                    *non_staged_history_iris,
                    *snapshot_only_revision_iris,
                    *applied_event_iris,
                ]
            )
        )
        not_restageable_revision_iris_by_reason = {
            key: list(values)
            for key, values in batch.not_restageable_revision_iris_by_reason.items()
        }
        if patchless_staged_history_iris:
            not_restageable_revision_iris_by_reason.setdefault(
                "missing_patch_payload",
                [],
            ).extend(patchless_staged_history_iris)
        if non_staged_history_iris:
            not_restageable_revision_iris_by_reason.setdefault(
                "non_staged_history_record",
                [],
            ).extend(non_staged_history_iris)
        if snapshot_only_revision_iris:
            not_restageable_revision_iris_by_reason.setdefault(
                "missing_history_graph",
                [],
            ).extend(snapshot_only_revision_iris)
        if applied_event_iris:
            not_restageable_revision_iris_by_reason.setdefault(
                "applied_event_record",
                [],
            ).extend(applied_event_iris)
        return StagedRevisionRecoveryPlan(
            result_kind="staged_revision_recovery_plan",
            helper="plan_staged_revision_recovery",
            mode="read_only_plan",
            selection_mode=selection_mode,
            requested_revision_iris=requested_revision_iris,
            processed_revision_iris=processed_revision_iris,
            current_staged_work_only=current_staged_work_only,
            include_drafts=include_drafts,
            repair_draft_limit=effective_repair_draft_limit,
            repair_draft_attempted_count=repair_draft_attempted_count,
            repair_drafts_included_count=repair_drafts_included_count,
            repair_drafts_deferred_count=repair_drafts_deferred_count,
            validation_scope=validation_scope,
            drift_detail=drift_detail,
            limit=limit,
            offset=offset,
            count=total_count,
            returned_count=len(processed_revision_iris),
            total_count=total_count,
            lanes=lanes,
            lane_counts=lane_counts,
            next_action_queue=self._revision_next_action_queue(
                (lane.row_iri, lane.next_action) for lane in lanes
            ),
            next_action_queue_items=queue_items,
            next_action_queue_item_counts=(
                self._revision_next_action_queue_item_counts(queue_items)
            ),
            resolved_target_groups=resolved_target_groups,
            resolved_target_group_counts=(
                self._staged_recovery_resolved_target_group_counts(
                    resolved_target_groups
                )
            ),
            mutation_frontier_iris=mutation_frontier_iris,
            mutation_frontier_items=mutation_frontier_items,
            helper_mutation_frontier_actions=helper_mutation_frontier_actions,
            helper_mutation_frontier_calls=[
                action.call
                for action in helper_mutation_frontier_actions
                if action.call
            ],
            mutation_allowed_after=mutation_allowed_after,
            first_mutation_action=first_mutation_action,
            first_mutation_call=(
                first_mutation_action.call
                if first_mutation_action is not None
                else None
            ),
            first_safe_review_or_mutation_action=(
                first_safe_review_or_mutation_action
            ),
            first_safe_review_or_mutation_call=(
                first_safe_review_or_mutation_action.call
                if first_safe_review_or_mutation_action is not None
                else None
            ),
            first_safe_review_or_mutation_source=(
                first_safe_review_or_mutation_source
            ),
            blocking_preflight_actions=blocking_preflight_actions,
            blocking_preflight_calls=[
                action.call for action in blocking_preflight_actions if action.call
            ],
            recommended_unattended_steps=recommended_unattended_steps,
            requires_recheck_after_each_apply=requires_recheck_after_each_apply,
            semantic_review_required_queue_counts=(
                self._semantic_review_required_queue_counts(queue_items)
            ),
            would_restage_revision_iris=batch.would_restage_revision_iris,
            repair_first_revision_iris=batch.repair_first_revision_iris,
            repair_or_replace_source_revision_iris=[
                lane.source_revision_iri
                for lane in lanes
                if lane.lane == "repair_or_replace"
            ],
            not_restageable_revision_iris_by_reason=(
                not_restageable_revision_iris_by_reason
            ),
            current_revision_by_source=current_revision_by_source,
            review_revision_iris=review_revision_iris,
            recommended_review_iris=list(
                dict.fromkeys(
                    [
                        *batch.bundle_summary.recommended_review_iris,
                        *patchless_staged_history_iris,
                        *non_staged_history_iris,
                        *snapshot_only_revision_iris,
                        *applied_event_iris,
                    ]
                )
            ),
            recommended_mutation_review_iris=(
                batch.bundle_summary.recommended_mutation_review_iris
            ),
            recommended_apply_or_restage_review_iris=(
                batch.bundle_summary.recommended_apply_or_restage_review_iris
            ),
            recommended_repair_review_iris=(
                batch.bundle_summary.recommended_repair_review_iris
            ),
            recommended_applied_inspection_iris=list(
                dict.fromkeys(
                    [
                        *batch.bundle_summary.recommended_applied_inspection_iris,
                        *applied_event_iris,
                    ]
                )
            ),
            sequential_apply_recheck_candidate_iris=(
                batch.bundle_summary.sequential_apply_recheck_candidate_iris
            ),
            revision_summaries=batch.revision_summaries,
            bundle_summary=batch.bundle_summary,
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[
                action.call for action in suggested_next_actions if action.call
            ],
            warnings=list(dict.fromkeys(warnings)),
            note=(
                "Read-only staged revision recovery plan. It did not stage, "
                "restage, apply, export, or otherwise mutate graph state."
            ),
        )
    def start_staged_revision_recovery_session(
        self,
        revision_iris: Iterable[str] | str | None = None,
        *,
        session_iri: str | None = None,
        summary: str | None = None,
        handoff_manifest_path: str | None = None,
        current_staged_work_only: bool = True,
        include_drafts: bool = True,
        repair_draft_limit: int | None = 1,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
        drift_detail: TypingLiteral["summary", "exact"] = "summary",
        limit: int = 50,
        offset: int = 0,
        created_at: datetime | str | None = None,
        created_by: str | None = None,
    ) -> StagedRevisionRecoverySessionDescription:
        plan = self.plan_staged_revision_recovery(
            revision_iris,
            current_staged_work_only=current_staged_work_only,
            include_drafts=include_drafts,
            repair_draft_limit=repair_draft_limit,
            validation_scope=validation_scope,
            drift_detail=drift_detail,
            limit=limit,
            offset=offset,
        )
        source_revision_iris = list(plan.processed_revision_iris)
        session_subject = (
            self._required_iri("session_iri", session_iri)
            if session_iri is not None
            else self._mint_iri("staged-revision-recovery-session")
        )
        if self._subject_exists(session_subject, self._expand_graphs(["history"])):
            raise DoxaBaseError(
                f"Staged revision recovery session already exists: {session_subject}"
            )
        summary_value = (
            summary.strip()
            if summary is not None and summary.strip()
            else (
                "Staged revision recovery session for "
                f"{len(source_revision_iris)} source revision(s)."
            )
        )
        created_literal = self._datetime_literal(
            created_at,
            name="created_at",
        )
        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(session_subject)
        graph.add(
            (
                subject,
                RDF.type,
                URIRef(self.expand_iri("rc:StagedRevisionRecoverySession")),
            )
        )
        graph.add((subject, URIRef(self.expand_iri("rc:summary")), Literal(summary_value)))
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:sessionCreatedAt")),
                created_literal,
            )
        )
        if created_by is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:sessionCreatedBy")),
                    self._resource_or_literal(created_by),
                )
            )
        if handoff_manifest_path is not None and handoff_manifest_path.strip():
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:recoverySessionHandoffManifestPath")),
                    Literal(handoff_manifest_path.strip()),
                )
            )
        for revision_iri in source_revision_iris:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:recoverySessionSourceRevision")),
                    URIRef(self.expand_iri(revision_iri)),
                )
            )
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:recoverySessionSourceRevisionList")),
                Literal(json.dumps(source_revision_iris)),
            )
        )
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:recoverySessionSourceCount")),
                Literal(len(source_revision_iris), datatype=XSD.integer),
            )
        )
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:recoverySessionInitialSelectionMode")),
                Literal(plan.selection_mode),
            )
        )
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:recoverySessionCurrentStagedWorkOnly")),
                Literal(current_staged_work_only, datatype=XSD.boolean),
            )
        )
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:recoverySessionIncludeDrafts")),
                Literal(include_drafts, datatype=XSD.boolean),
            )
        )
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:recoverySessionRepairDraftLimit")),
                (
                    Literal("unbounded")
                    if repair_draft_limit is None
                    else Literal(repair_draft_limit, datatype=XSD.integer)
                ),
            )
        )
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:recoverySessionDriftDetail")),
                Literal(drift_detail),
            )
        )
        if validation_scope is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:recoverySessionValidationScope")),
                    Literal(validation_scope),
                )
            )
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:recoverySessionInitialLaneCounts")),
                Literal(json.dumps(plan.lane_counts, sort_keys=True)),
            )
        )
        created_triples = self._insert_graph("history", graph)
        description = self.describe_staged_revision_recovery_session(
            session_subject,
            include_drafts=include_drafts,
            repair_draft_limit=repair_draft_limit,
            validation_scope=validation_scope,
            drift_detail=drift_detail,
            created_triples=created_triples,
        )
        return replace(
            description,
            helper="start_staged_revision_recovery_session",
        )
    def describe_staged_revision_recovery_session(
        self,
        session_iri: str,
        *,
        include_drafts: bool | None = None,
        repair_draft_limit: int | None = None,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
        drift_detail: TypingLiteral["summary", "exact"] | None = None,
        created_triples: int | None = None,
    ) -> StagedRevisionRecoverySessionDescription:
        session_subject = self._required_iri("session_iri", session_iri)
        history_graphs = self._expand_graphs(["history"])
        if not self._subject_exists(session_subject, history_graphs):
            raise DoxaBaseError(
                f"Staged revision recovery session not found: {session_subject}"
            )
        if (
            self.expand_iri("rc:StagedRevisionRecoverySession")
            not in self._types_from_graphs(history_graphs, session_subject)
        ):
            raise DoxaBaseError(
                f"Resource '{session_subject}' is not an rc:StagedRevisionRecoverySession"
            )
        source_revision_iris = self._staged_recovery_session_source_revision_iris(
            session_subject,
            history_graphs=history_graphs,
        )
        stored_include_drafts = self._optional_bool_object(
            self._first_object(
                history_graphs,
                session_subject,
                "rc:recoverySessionIncludeDrafts",
            ),
            default=True,
        )
        effective_include_drafts = (
            stored_include_drafts if include_drafts is None else include_drafts
        )
        stored_repair_draft_limit = self._optional_repair_draft_limit_object(
            self._first_object(
                history_graphs,
                session_subject,
                "rc:recoverySessionRepairDraftLimit",
            ),
            default=1,
        )
        effective_repair_draft_limit = (
            stored_repair_draft_limit
            if repair_draft_limit is None
            else repair_draft_limit
        )
        stored_validation_scope = self._first_object(
            history_graphs,
            session_subject,
            "rc:recoverySessionValidationScope",
        )
        effective_validation_scope = (
            stored_validation_scope
            if validation_scope is None
            else validation_scope
        )
        stored_drift_detail = self._first_object(
            history_graphs,
            session_subject,
            "rc:recoverySessionDriftDetail",
        )
        effective_drift_detail = (
            stored_drift_detail if drift_detail is None else drift_detail
        )
        if effective_drift_detail not in {"summary", "exact"}:
            raise DoxaBaseError("drift_detail must be 'summary' or 'exact'")
        stored_current_only = self._optional_bool_object(
            self._first_object(
                history_graphs,
                session_subject,
                "rc:recoverySessionCurrentStagedWorkOnly",
            ),
            default=False,
        )
        current_plan = self.plan_staged_revision_recovery(
            source_revision_iris,
            current_staged_work_only=stored_current_only,
            include_drafts=effective_include_drafts,
            repair_draft_limit=effective_repair_draft_limit,
            validation_scope=effective_validation_scope,  # type: ignore[arg-type]
            drift_detail=effective_drift_detail,  # type: ignore[arg-type]
        )
        source_states, state_warnings = self._staged_recovery_session_source_states(
            source_revision_iris,
            current_plan=current_plan,
            drift_detail=effective_drift_detail,
        )
        completed_source_revision_iris = [
            state.source_revision_iri
            for state in source_states
            if state.workflow_state == "applied"
        ]
        active_source_revision_iris = [
            state.source_revision_iri
            for state in source_states
            if state.workflow_state in {"active", "needs_review"}
        ]
        applied_event_iris = list(
            dict.fromkeys(
                state.applied_revision_iri
                for state in source_states
                if state.applied_revision_iri is not None
            )
        )
        initial_lane_counts = self._json_object_literal(
            self._first_object(
                history_graphs,
                session_subject,
                "rc:recoverySessionInitialLaneCounts",
            ),
        )
        session_status = self._staged_recovery_session_status(
            source_revision_iris=source_revision_iris,
            source_states=source_states,
            current_plan=current_plan,
        )
        warnings = list(
            dict.fromkeys(
                [
                    *current_plan.warnings,
                    *state_warnings,
                ]
            )
        )
        return StagedRevisionRecoverySessionDescription(
            result_kind="staged_revision_recovery_session",
            helper="describe_staged_revision_recovery_session",
            mode=(
                "recorded_session"
                if created_triples is not None
                else "read_only_description"
            ),
            session_iri=session_subject,
            summary=self._first_object(history_graphs, session_subject, "rc:summary"),
            created_at=self._first_object(
                history_graphs,
                session_subject,
                "rc:sessionCreatedAt",
            ),
            created_by=self._first_object(
                history_graphs,
                session_subject,
                "rc:sessionCreatedBy",
            ),
            handoff_manifest_path=self._first_object(
                history_graphs,
                session_subject,
                "rc:recoverySessionHandoffManifestPath",
            ),
            source_revision_iris=source_revision_iris,
            source_count=len(source_revision_iris),
            session_status=session_status,
            current_staged_work_only=stored_current_only,
            include_drafts=effective_include_drafts,
            repair_draft_limit=current_plan.repair_draft_limit,
            validation_scope=effective_validation_scope,
            drift_detail=effective_drift_detail,
            initial_selection_mode=self._first_object(
                history_graphs,
                session_subject,
                "rc:recoverySessionInitialSelectionMode",
            ),
            initial_lane_counts={
                key: value
                for key, value in initial_lane_counts.items()
                if isinstance(key, str) and isinstance(value, int)
            },
            current_plan=current_plan,
            source_states=source_states,
            completed_source_revision_iris=completed_source_revision_iris,
            active_source_revision_iris=active_source_revision_iris,
            applied_event_iris=applied_event_iris,
            current_revision_by_source=current_plan.current_revision_by_source,
            mutation_frontier_iris=current_plan.mutation_frontier_iris,
            helper_mutation_frontier_calls=current_plan.helper_mutation_frontier_calls,
            suggested_next_actions=current_plan.suggested_next_actions,
            suggested_next_calls=current_plan.suggested_next_calls,
            warnings=warnings,
            note=(
                "Recovery sessions persist source revisions and planning "
                "parameters in history; current_plan and source_states are "
                "recomputed from live revision state each time this helper runs."
            ),
            created_triples=created_triples,
        )
    def _staged_recovery_session_source_states(
        self,
        source_revision_iris: list[str],
        *,
        current_plan: StagedRevisionRecoveryPlan,
        drift_detail: str,
    ) -> tuple[list[StagedRevisionRecoverySessionSourceState], list[str]]:
        lanes_by_source = {
            lane.source_revision_iri: lane for lane in current_plan.lanes
        }
        states: list[StagedRevisionRecoverySessionSourceState] = []
        warnings: list[str] = []
        for source_revision_iri in source_revision_iris:
            lane = lanes_by_source.get(source_revision_iri)
            lineage: RevisionLineageDescription | None = None
            lineage_error: str | None = None
            try:
                lineage = self.describe_revision_lineage(
                    source_revision_iri,
                    include_apply_checks=True,
                    drift_detail=drift_detail,  # type: ignore[arg-type]
                )
            except DoxaBaseError as exc:
                lineage_error = str(exc)
                warnings.append(
                    "Could not describe recovery-session source lineage for "
                    f"{source_revision_iri}: {exc}"
                )
            if lineage is not None and lineage.applied_revision_iri is not None:
                workflow_state = "applied"
            elif lane is None:
                workflow_state = "missing"
            elif lane.lane in {
                "apply_after_review",
                "restage_after_review",
                "repair_or_replace",
            }:
                workflow_state = "active"
            elif lane.lane in {"inspect_already_applied", "informational"}:
                workflow_state = "informational"
            else:
                workflow_state = "needs_review"
            next_action = lane.next_action if lane is not None else None
            states.append(
                StagedRevisionRecoverySessionSourceState(
                    source_revision_iri=source_revision_iri,
                    lane=lane.lane if lane is not None else None,
                    effective_recovery_action=(
                        lane.effective_recovery_action
                        if lane is not None
                        else None
                    ),
                    batch_action=lane.batch_action if lane is not None else None,
                    current_revision_iri=(
                        lane.current_revision_iri
                        if lane is not None
                        else (
                            lineage.current_revision_iri
                            if lineage is not None
                            else None
                        )
                    ),
                    resolved_target_iri=(
                        lane.resolved_target_iri if lane is not None else None
                    ),
                    resolved_target_record_kind=(
                        lane.resolved_target_record_kind
                        if lane is not None
                        else None
                    ),
                    next_action_queue=(
                        lane.next_action_queue_item.queue
                        if lane is not None
                        and lane.next_action_queue_item is not None
                        else None
                    ),
                    next_action_tool_name=(
                        next_action.tool_name if next_action is not None else None
                    ),
                    applied_revision_iri=(
                        lineage.applied_revision_iri
                        if lineage is not None
                        else None
                    ),
                    current_staged_revision_iri=(
                        lineage.current_staged_revision_iri
                        if lineage is not None
                        else None
                    ),
                    latest_revision_iri=(
                        lineage.latest_revision_iri
                        if lineage is not None
                        else None
                    ),
                    latest_role=(
                        lineage.latest_role if lineage is not None else None
                    ),
                    restage_chain_iris=(
                        lineage.restage_chain_iris
                        if lineage is not None
                        else []
                    ),
                    snapshot_status=(
                        lane.current_snapshot_evidence.status
                        if lane is not None
                        else None
                    ),
                    workflow_state=(
                        "missing" if lineage_error is not None else workflow_state
                    ),
                )
            )
        return states, warnings
    @staticmethod
    def _staged_recovery_session_status(
        *,
        source_revision_iris: list[str],
        source_states: list[StagedRevisionRecoverySessionSourceState],
        current_plan: StagedRevisionRecoveryPlan,
    ) -> str:
        if not source_revision_iris:
            return "empty"
        if current_plan.mutation_frontier_items:
            return "active"
        if any(
            state.workflow_state in {"active", "needs_review"}
            for state in source_states
        ):
            return "active"
        if all(state.workflow_state == "applied" for state in source_states):
            return "complete"
        if any(state.workflow_state == "missing" for state in source_states):
            return "incomplete"
        return "review_or_inspect"
    def _staged_recovery_session_source_revision_iris(
        self,
        session_iri: str,
        *,
        history_graphs: list[str],
    ) -> list[str]:
        ordered_literal = self._first_object(
            history_graphs,
            session_iri,
            "rc:recoverySessionSourceRevisionList",
        )
        if ordered_literal is not None:
            try:
                parsed = json.loads(ordered_literal)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                values = [
                    self.expand_iri(value)
                    for value in parsed
                    if isinstance(value, str) and value.strip()
                ]
                if values:
                    return list(dict.fromkeys(values))
        return self._objects(
            history_graphs,
            session_iri,
            "rc:recoverySessionSourceRevision",
        )
    @staticmethod
    def _optional_bool_object(value: str | None, *, default: bool) -> bool:
        if value is None:
            return default
        normalized = value.strip().lower()
        if normalized in {"true", "1"}:
            return True
        if normalized in {"false", "0"}:
            return False
        return default
    def _staged_recovery_split_non_patch_inputs(
        self,
        revision_iris: Iterable[str],
        *,
        history_graphs: list[str],
    ) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
        restage_revision_iris: list[str] = []
        patchless_staged_history_iris: list[str] = []
        non_staged_history_iris: list[str] = []
        snapshot_only_revision_iris: list[str] = []
        applied_event_iris: list[str] = []
        staged_revision_type = self.expand_iri("rc:StagedRevision")
        graph_revision_type = self.expand_iri("rc:GraphRevision")
        for revision_iri in revision_iris:
            revision_value = self.expand_iri(revision_iri)
            is_graph_revision = (
                self._subject_exists(revision_value, history_graphs)
                and graph_revision_type
                in self._types_from_graphs(history_graphs, revision_value)
            )
            revision_type = self._first_object(
                history_graphs,
                revision_value,
                "rc:revisionType",
            )
            has_patch_payload = bool(
                self._objects(history_graphs, revision_value, "rc:hasGraphPatch")
            )
            applies_staged_revision = self._first_object(
                history_graphs,
                revision_value,
                "rc:appliesStagedRevision",
            )
            if is_graph_revision and applies_staged_revision is not None:
                applied_event_iris.append(revision_value)
            elif (
                is_graph_revision
                and revision_type == staged_revision_type
                and not has_patch_payload
                and applies_staged_revision is None
            ):
                patchless_staged_history_iris.append(revision_value)
            elif (
                is_graph_revision
                and not has_patch_payload
                and applies_staged_revision is None
            ):
                non_staged_history_iris.append(revision_value)
            elif (
                self._revision_snapshot_evidence_status(
                    revision_value,
                    history_graphs,
                ).status
                == "snapshot_rows_without_history"
            ):
                snapshot_only_revision_iris.append(revision_value)
            else:
                restage_revision_iris.append(revision_iri)
        return (
            restage_revision_iris,
            patchless_staged_history_iris,
            non_staged_history_iris,
            snapshot_only_revision_iris,
            applied_event_iris,
        )
    def _empty_staged_recovery_batch(
        self,
        requested_revision_iris: list[str],
    ) -> StagedGraphRevisionBatchRestageRecord:
        snapshot_evidence = self._staged_revisions_snapshot_evidence_summary([])
        return StagedGraphRevisionBatchRestageRecord(
            requested_revision_iris=requested_revision_iris,
            processed_revision_iris=[],
            dry_run=True,
            would_restage_revision_iris=[],
            repair_first_revision_iris=[],
            repair_or_replace_source_revision_iris=[],
            restaged_revision_iris=[],
            skipped_revision_iris=[],
            already_handled_revision_iris=[],
            not_restageable_revision_iris=[],
            not_restageable_revision_iris_by_reason={},
            restaged_revision_by_source={},
            current_revision_by_source={},
            review_revision_iris=[],
            items=[],
            revision_summaries=[],
            bundle_summary=self._staged_revisions_bundle_summary(
                [],
                descriptions=[],
                snapshot_evidence=snapshot_evidence,
            ),
            requires_recheck_after_each_apply=False,
            sequential_apply_recheck_candidate_iris=[],
            export_record=None,
        )
    def _snapshot_only_recovery_item(
        self,
        revision_iri: str,
        *,
        history_graphs: list[str],
    ) -> StagedGraphRevisionBatchRestageItem:
        revision_value = self.expand_iri(revision_iri)
        snapshot_evidence = self._revision_snapshot_evidence_status(
            revision_value,
            history_graphs,
        )
        snapshot_completeness = self._snapshot_evidence_completeness_label(
            snapshot_evidence
        )
        next_action = self._snapshot_evidence_completion_next_action(
            snapshot_evidence.suggested_next_actions
        )
        if next_action is None:
            arguments = {"path": "/tmp/project.trig", "path_is_placeholder": True}
            next_action = RevisionNextAction(
                action_type="complete_handoff_import",
                queue="complete_handoff_import",
                action_label="Import project/history RDF bundle",
                tool_name="import_trig",
                mcp_tool_name="doxabase.import_trig",
                arguments=arguments,
                reason=(
                    "Snapshot rows exist for this revision, but the RDF history "
                    "record is missing. Import the project/history RDF bundle at "
                    "its real handoff path before using normal revision helpers."
                ),
                call=self._suggested_call_string("import_trig", arguments),
                source="snapshot_evidence",
            )
        suggested_next_actions = snapshot_evidence.suggested_next_actions or [
            SuggestedNextAction(
                action_label=next_action.action_label,
                tool_name=next_action.tool_name or "import_trig",
                mcp_tool_name=next_action.mcp_tool_name or "doxabase.import_trig",
                arguments=next_action.arguments,
                reason=next_action.reason,
                call=next_action.call or "",
            )
        ]
        queue_item = self._revision_next_action_queue_item(
            row_iri=revision_value,
            next_action=next_action,
            record_kind=None,
            application_status="history_missing",
            application_decision="complete_handoff_import",
            staged_validation_status="not_recorded",
        )
        return StagedGraphRevisionBatchRestageItem(
            source_revision_iri=revision_value,
            summary=None,
            status_before="history_missing",
            decision_before="complete_handoff_import",
            routing_decision_before="complete_handoff_import",
            stale_resolution_state_before=None,
            blocking_reasons_before=["missing_history_graph"],
            exact_drift_summary_before=[],
            source_staged_validation_status="not_recorded",
            source_validation_result_count=None,
            source_snapshot_evidence=snapshot_evidence,
            source_snapshot_evidence_completeness=snapshot_completeness,
            status_after="history_missing",
            decision_after="complete_handoff_import",
            routing_decision_after="complete_handoff_import",
            stale_resolution_state_after=None,
            blocking_reasons_after=["missing_history_graph"],
            exact_drift_summary_after=[],
            current_staged_validation_status="not_recorded",
            current_validation_result_count=None,
            current_snapshot_evidence=snapshot_evidence,
            current_snapshot_evidence_completeness=snapshot_completeness,
            triples_to_add_after=0,
            triples_to_remove_after=0,
            action="skipped_snapshot_rows_without_history",
            not_restageable_reason="missing_history_graph",
            restaged_from=None,
            restaged_revision_iri=None,
            current_restaged_by=None,
            current_revision_iri=revision_value,
            next_action_after=next_action,
            next_action_queue_item_after=queue_item,
            suggested_next_actions_after=suggested_next_actions,
            repair_first_warning=None,
            note=(
                "Skipped because exact snapshot rows exist for this revision IRI "
                "but the RDF history record is missing. Import the matching "
                "project/history RDF bundle before applying, restaging, or "
                "repairing staged revisions."
            ),
        )
    def _patchless_staged_history_recovery_item(
        self,
        revision_iri: str,
        *,
        history_graphs: list[str],
    ) -> StagedGraphRevisionBatchRestageItem:
        revision = self.describe_graph_revision(revision_iri)
        snapshot_evidence = self._revision_snapshot_evidence_status(
            revision.iri,
            history_graphs,
        )
        snapshot_completeness = self._snapshot_evidence_completeness_label(
            snapshot_evidence
        )
        staged_validation_status = self._staged_validation_status(
            conforms=revision.validation_conforms,
            result_count=revision.validation_result_count,
        )
        arguments = {"iri": revision.iri, "graph": "history"}
        next_action = RevisionNextAction(
            action_type="inspect_missing_patch_payload",
            queue="informational",
            action_label="Inspect patchless staged metadata",
            tool_name="describe_graph_revision",
            mcp_tool_name="doxabase.describe_graph_revision",
            arguments=arguments,
            reason=(
                "This explicit recovery input is staged revision history metadata "
                "without rc:hasGraphPatch entries, so it cannot be applied or "
                "restaged as a staged patch. Inspect the graph revision and import "
                "the complete staged handoff if patch payloads are expected."
            ),
            call=self._suggested_call_string("describe_graph_revision", arguments),
            source="plan_staged_revision_recovery",
        )
        suggested_action = SuggestedNextAction(
            action_label=next_action.action_label,
            tool_name=next_action.tool_name or "describe_graph_revision",
            mcp_tool_name=next_action.mcp_tool_name
            or "doxabase.describe_graph_revision",
            arguments=arguments,
            reason=next_action.reason,
            call=next_action.call or "",
        )
        queue_item = self._revision_next_action_queue_item(
            row_iri=revision.iri,
            next_action=next_action,
            record_kind="history_record",
            application_status="not_available",
            application_decision="missing_patch_payload",
            staged_validation_status=staged_validation_status,
        )
        return StagedGraphRevisionBatchRestageItem(
            source_revision_iri=revision.iri,
            summary=revision.summary,
            status_before="not_available",
            decision_before="missing_patch_payload",
            routing_decision_before="inspect_missing_patch_payload",
            stale_resolution_state_before=None,
            blocking_reasons_before=["missing_patch_payload"],
            exact_drift_summary_before=[],
            source_staged_validation_status=staged_validation_status,
            source_validation_result_count=revision.validation_result_count,
            source_snapshot_evidence=snapshot_evidence,
            source_snapshot_evidence_completeness=snapshot_completeness,
            status_after="not_available",
            decision_after="missing_patch_payload",
            routing_decision_after="inspect_missing_patch_payload",
            stale_resolution_state_after=None,
            blocking_reasons_after=["missing_patch_payload"],
            exact_drift_summary_after=[],
            current_staged_validation_status=staged_validation_status,
            current_validation_result_count=revision.validation_result_count,
            current_snapshot_evidence=snapshot_evidence,
            current_snapshot_evidence_completeness=snapshot_completeness,
            triples_to_add_after=0,
            triples_to_remove_after=0,
            action="skipped_missing_patch_payload",
            not_restageable_reason="missing_patch_payload",
            restaged_from=None,
            restaged_revision_iri=None,
            current_restaged_by=None,
            current_revision_iri=revision.iri,
            next_action_after=next_action,
            next_action_queue_item_after=queue_item,
            suggested_next_actions_after=[suggested_action],
            repair_first_warning=None,
            note=(
                "Skipped because this explicit recovery input is an "
                "rc:StagedRevision history record without staged patch entries. "
                "It is useful as metadata, but cannot be applied or mechanically "
                "restaged until patch payloads are imported."
            ),
        )
    def _non_staged_history_recovery_item(
        self,
        revision_iri: str,
        *,
        history_graphs: list[str],
    ) -> StagedGraphRevisionBatchRestageItem:
        revision = self.describe_graph_revision(revision_iri)
        snapshot_evidence = self._revision_snapshot_evidence_status(
            revision.iri,
            history_graphs,
        )
        snapshot_completeness = self._snapshot_evidence_completeness_label(
            snapshot_evidence
        )
        staged_validation_status = self._staged_validation_status(
            conforms=revision.validation_conforms,
            result_count=revision.validation_result_count,
        )
        arguments = {"iri": revision.iri, "graph": "history"}
        next_action = RevisionNextAction(
            action_type="inspect_non_staged_history_record",
            queue="informational",
            action_label="Inspect non-staged history record",
            tool_name="describe_graph_revision",
            mcp_tool_name="doxabase.describe_graph_revision",
            arguments=arguments,
            reason=(
                "This explicit recovery input is ordinary graph-revision "
                "history or snapshot context, not a staged patch. Inspect it as "
                "history instead of applying or restaging it."
            ),
            call=self._suggested_call_string("describe_graph_revision", arguments),
            source="plan_staged_revision_recovery",
        )
        suggested_action = SuggestedNextAction(
            action_label=next_action.action_label,
            tool_name=next_action.tool_name or "describe_graph_revision",
            mcp_tool_name=next_action.mcp_tool_name
            or "doxabase.describe_graph_revision",
            arguments=arguments,
            reason=next_action.reason,
            call=next_action.call or "",
        )
        queue_item = self._revision_next_action_queue_item(
            row_iri=revision.iri,
            next_action=next_action,
            record_kind=revision.record_kind,
            application_status="not_available",
            application_decision="non_staged_history_record",
            staged_validation_status=staged_validation_status,
        )
        return StagedGraphRevisionBatchRestageItem(
            source_revision_iri=revision.iri,
            summary=revision.summary,
            status_before="not_available",
            decision_before="non_staged_history_record",
            routing_decision_before="inspect_non_staged_history_record",
            stale_resolution_state_before=None,
            blocking_reasons_before=["non_staged_history_record"],
            exact_drift_summary_before=[],
            source_staged_validation_status=staged_validation_status,
            source_validation_result_count=revision.validation_result_count,
            source_snapshot_evidence=snapshot_evidence,
            source_snapshot_evidence_completeness=snapshot_completeness,
            status_after="not_available",
            decision_after="non_staged_history_record",
            routing_decision_after="inspect_non_staged_history_record",
            stale_resolution_state_after=None,
            blocking_reasons_after=["non_staged_history_record"],
            exact_drift_summary_after=[],
            current_staged_validation_status=staged_validation_status,
            current_validation_result_count=revision.validation_result_count,
            current_snapshot_evidence=snapshot_evidence,
            current_snapshot_evidence_completeness=snapshot_completeness,
            triples_to_add_after=0,
            triples_to_remove_after=0,
            action="skipped_non_staged_history_record",
            not_restageable_reason="non_staged_history_record",
            restaged_from=None,
            restaged_revision_iri=None,
            current_restaged_by=None,
            current_revision_iri=revision.iri,
            next_action_after=next_action,
            next_action_queue_item_after=queue_item,
            suggested_next_actions_after=[suggested_action],
            repair_first_warning=None,
            note=(
                "Skipped because this explicit recovery input is not a staged "
                "patch revision. It remains available as history/snapshot "
                "context but is not an apply or mechanical-restage target."
            ),
        )
    def _applied_event_recovery_item(
        self,
        revision_iri: str,
        *,
        history_graphs: list[str],
    ) -> StagedGraphRevisionBatchRestageItem:
        revision = self.describe_graph_revision(revision_iri)
        snapshot_evidence = self._revision_snapshot_evidence_status(
            revision.iri,
            history_graphs,
        )
        snapshot_completeness = self._snapshot_evidence_completeness_label(
            snapshot_evidence
        )
        staged_validation_status = self._staged_validation_status(
            conforms=revision.validation_conforms,
            result_count=revision.validation_result_count,
        )
        arguments = {"iri": revision.iri}
        next_action = RevisionNextAction(
            action_type="inspect_applied_event",
            queue="inspect_already_applied",
            action_label="Inspect applied event",
            tool_name="describe_graph_revision",
            mcp_tool_name="doxabase.describe_graph_revision",
            arguments=arguments,
            reason=(
                "This recovery input is an applied revision event rather than "
                "a staged patch. Inspect the durable event or its applied diff "
                "instead of applying or restaging it."
            ),
            call=self._suggested_call_string("describe_graph_revision", arguments),
            source="plan_staged_revision_recovery",
        )
        queue_item = self._revision_next_action_queue_item(
            row_iri=revision.iri,
            next_action=next_action,
            record_kind=revision.record_kind,
            application_status="applied_event",
            application_decision="inspect_applied_revision",
            staged_validation_status=staged_validation_status,
        )
        suggested_next_actions = (
            revision.suggested_next_actions
            or [
                SuggestedNextAction(
                    action_label=next_action.action_label,
                    tool_name=next_action.tool_name or "describe_graph_revision",
                    mcp_tool_name=(
                        next_action.mcp_tool_name
                        or "doxabase.describe_graph_revision"
                    ),
                    arguments=arguments,
                    reason=next_action.reason,
                    call=next_action.call or "",
                )
            ]
        )
        return StagedGraphRevisionBatchRestageItem(
            source_revision_iri=revision.iri,
            summary=revision.summary,
            status_before="applied_event",
            decision_before="inspect_applied_revision",
            routing_decision_before="inspect_applied_event",
            stale_resolution_state_before=None,
            blocking_reasons_before=["applied_event_record"],
            exact_drift_summary_before=[],
            source_staged_validation_status=staged_validation_status,
            source_validation_result_count=revision.validation_result_count,
            source_snapshot_evidence=snapshot_evidence,
            source_snapshot_evidence_completeness=snapshot_completeness,
            status_after="applied_event",
            decision_after="inspect_applied_revision",
            routing_decision_after="inspect_applied_event",
            stale_resolution_state_after=None,
            blocking_reasons_after=["applied_event_record"],
            exact_drift_summary_after=[],
            current_staged_validation_status=staged_validation_status,
            current_validation_result_count=revision.validation_result_count,
            current_snapshot_evidence=snapshot_evidence,
            current_snapshot_evidence_completeness=snapshot_completeness,
            triples_to_add_after=0,
            triples_to_remove_after=0,
            action="skipped_applied_event",
            not_restageable_reason="applied_event_record",
            restaged_from=None,
            restaged_revision_iri=None,
            current_restaged_by=None,
            current_revision_iri=revision.iri,
            next_action_after=next_action,
            next_action_queue_item_after=queue_item,
            suggested_next_actions_after=suggested_next_actions,
            repair_first_warning=None,
            note=(
                "Skipped because this recovery input is an applied revision "
                "event. It is durable history, not a staged patch payload, so "
                "the planner routed it to applied-event inspection."
            ),
        )
    def _empty_staged_revision_recovery_plan(
        self,
        *,
        selection_mode: str,
        requested_revision_iris: list[str] | None,
        current_staged_work_only: bool,
        include_drafts: bool,
        repair_draft_limit: int | None,
        validation_scope: str | None,
        drift_detail: str,
        limit: int,
        offset: int,
        total_count: int,
    ) -> StagedRevisionRecoveryPlan:
        return StagedRevisionRecoveryPlan(
            result_kind="staged_revision_recovery_plan",
            helper="plan_staged_revision_recovery",
            mode="read_only_plan",
            selection_mode=selection_mode,
            requested_revision_iris=requested_revision_iris,
            processed_revision_iris=[],
            current_staged_work_only=current_staged_work_only,
            include_drafts=include_drafts,
            repair_draft_limit=repair_draft_limit,
            repair_draft_attempted_count=0,
            repair_drafts_included_count=0,
            repair_drafts_deferred_count=0,
            validation_scope=validation_scope,
            drift_detail=drift_detail,
            limit=limit,
            offset=offset,
            count=total_count,
            returned_count=0,
            total_count=total_count,
            lanes=[],
            lane_counts={},
            next_action_queue={},
            next_action_queue_items=[],
            next_action_queue_item_counts={},
            resolved_target_groups=[],
            resolved_target_group_counts={},
            mutation_frontier_iris=[],
            mutation_frontier_items=[],
            helper_mutation_frontier_actions=[],
            helper_mutation_frontier_calls=[],
            mutation_allowed_after="no_mutation_frontier",
            first_mutation_action=None,
            first_mutation_call=None,
            first_safe_review_or_mutation_action=None,
            first_safe_review_or_mutation_call=None,
            first_safe_review_or_mutation_source=None,
            blocking_preflight_actions=[],
            blocking_preflight_calls=[],
            recommended_unattended_steps=[],
            requires_recheck_after_each_apply=False,
            semantic_review_required_queue_counts={},
            would_restage_revision_iris=[],
            repair_first_revision_iris=[],
            repair_or_replace_source_revision_iris=[],
            not_restageable_revision_iris_by_reason={},
            current_revision_by_source={},
            review_revision_iris=[],
            recommended_review_iris=[],
            recommended_mutation_review_iris=[],
            recommended_apply_or_restage_review_iris=[],
            recommended_repair_review_iris=[],
            recommended_applied_inspection_iris=[],
            sequential_apply_recheck_candidate_iris=[],
            revision_summaries=[],
            bundle_summary=None,
            suggested_next_actions=[],
            suggested_next_calls=[],
            warnings=[],
            note=(
                "No staged revisions matched the recovery-plan selection. "
                "No graph state was changed."
            ),
        )
    def _staged_recovery_resolved_target_groups(
        self,
        lanes: list[StagedRevisionRecoveryLane],
        *,
        requested_revision_iris: list[str] | None,
    ) -> list[StagedRevisionResolvedTargetGroup]:
        requested = set(requested_revision_iris or [])
        groups: dict[tuple[str, str], dict[str, Any]] = {}
        group_order: list[tuple[str, str]] = []

        def add_unique(values: list[str], value: str | None) -> None:
            if value is not None:
                self._append_unique(values, value)

        risk_rank = {None: 0, "none": 1, "attention": 2, "high": 3}

        def higher_risk(
            current: str | None,
            candidate: str | None,
        ) -> str | None:
            if risk_rank.get(candidate, 0) > risk_rank.get(current, 0):
                return candidate
            return current

        for lane in lanes:
            item = lane.next_action_queue_item
            queue = item.queue if item is not None else lane.lane
            action_type = (
                item.action_type
                if item is not None
                else lane.action_type
            )
            action_label = (
                item.action_label
                if item is not None
                else lane.action_label
            )
            resolved_target_iri = (
                item.resolved_target_iri
                if item is not None
                else lane.resolved_target_iri
            )
            resolved_target_record_kind = (
                item.resolved_target_record_kind
                if item is not None
                else lane.resolved_target_record_kind
            )
            row_is_target = (
                item.row_is_target if item is not None else lane.row_is_target
            )
            group_key = (
                resolved_target_iri
                or lane.row_iri
                or lane.current_revision_iri
                or lane.source_revision_iri
            )
            key = (queue, group_key)
            if key not in groups:
                groups[key] = {
                    "group_key": group_key,
                    "queue": queue,
                    "action_type": action_type,
                    "action_label": action_label,
                    "resolved_target_iri": resolved_target_iri,
                    "resolved_target_record_kind": resolved_target_record_kind,
                    "lane_count": 0,
                    "row_iris": [],
                    "source_revision_iris": [],
                    "requested_revision_iris": [],
                    "current_revision_iris": [],
                    "latest_revision_iris": [],
                    "restage_chain_iris": [],
                    "applied_event_iris": [],
                    "row_is_target_all": True,
                    "row_is_target_any": False,
                    "semantic_risk_level": None,
                    "semantic_risk_reasons": [],
                    "alternative_set_iris": [],
                    "alternative_set_source_iri": None,
                    "alternative_set_roles": [],
                    "alternative_gate_statuses": [],
                    "alternative_applied_source_iris": [],
                    "alternative_applied_revision_iris": [],
                    "alternative_semantic_review_required": False,
                }
                group_order.append(key)
            group = groups[key]
            group["lane_count"] += 1
            add_unique(group["row_iris"], lane.row_iri)
            add_unique(group["source_revision_iris"], lane.source_revision_iri)
            if requested_revision_iris is None or lane.source_revision_iri in requested:
                add_unique(
                    group["requested_revision_iris"],
                    lane.source_revision_iri,
                )
            add_unique(group["current_revision_iris"], lane.current_revision_iri)
            add_unique(
                group["latest_revision_iris"],
                resolved_target_iri or lane.current_revision_iri,
            )
            for restage_iri in (
                lane.restaged_from,
                lane.source_revision_iri,
                lane.restaged_revision_iri,
                lane.current_restaged_by,
                lane.current_revision_iri,
            ):
                add_unique(group["restage_chain_iris"], restage_iri)
            if resolved_target_record_kind == "applied_event":
                add_unique(group["applied_event_iris"], resolved_target_iri)
            if item is not None:
                add_unique(
                    group["applied_event_iris"],
                    item.alternative_applied_revision_iri,
                )
                add_unique(
                    group["alternative_applied_source_iris"],
                    item.alternative_applied_source_iri,
                )
                add_unique(
                    group["alternative_applied_revision_iris"],
                    item.alternative_applied_revision_iri,
                )
                group["semantic_risk_level"] = higher_risk(
                    group["semantic_risk_level"],
                    item.semantic_risk_level,
                )
                for reason in item.semantic_risk_reasons:
                    add_unique(group["semantic_risk_reasons"], reason)
                for alternative_iri in item.alternative_set_iris:
                    add_unique(group["alternative_set_iris"], alternative_iri)
                if group["alternative_set_source_iri"] is None:
                    group["alternative_set_source_iri"] = (
                        item.alternative_set_source_iri
                    )
                add_unique(
                    group["alternative_set_roles"],
                    item.alternative_set_role,
                )
                group["alternative_semantic_review_required"] = (
                    group["alternative_semantic_review_required"]
                    or item.alternative_semantic_review_required
                )
            if lane.alternative_gate is not None:
                add_unique(
                    group["alternative_gate_statuses"],
                    lane.alternative_gate.status,
                )
                add_unique(
                    group["applied_event_iris"],
                    lane.alternative_gate.applied_revision_iri,
                )
                add_unique(
                    group["alternative_applied_source_iris"],
                    lane.alternative_gate.applied_source_iri,
                )
                add_unique(
                    group["alternative_applied_revision_iris"],
                    lane.alternative_gate.applied_revision_iri,
                )
                if lane.alternative_gate.status != "not_applicable":
                    add_unique(
                        group["alternative_set_iris"],
                        lane.alternative_gate.current_alternative_to,
                    )
                    add_unique(group["alternative_set_iris"], lane.row_iri)
                    if group["alternative_set_source_iri"] is None:
                        group["alternative_set_source_iri"] = (
                            lane.alternative_gate.current_alternative_to
                        )
                    add_unique(group["alternative_set_roles"], "alternative")
                group["alternative_semantic_review_required"] = (
                    group["alternative_semantic_review_required"]
                    or lane.alternative_gate.semantic_review_required
                )
            group["row_is_target_all"] = (
                group["row_is_target_all"] and row_is_target
            )
            group["row_is_target_any"] = group["row_is_target_any"] or row_is_target

        return [
            StagedRevisionResolvedTargetGroup(
                group_key=group["group_key"],
                queue=group["queue"],
                action_type=group["action_type"],
                action_label=group["action_label"],
                resolved_target_iri=group["resolved_target_iri"],
                resolved_target_record_kind=group["resolved_target_record_kind"],
                lane_count=group["lane_count"],
                row_iris=group["row_iris"],
                source_revision_iris=group["source_revision_iris"],
                requested_revision_iris=group["requested_revision_iris"],
                current_revision_iris=group["current_revision_iris"],
                latest_revision_iris=group["latest_revision_iris"],
                restage_chain_iris=group["restage_chain_iris"],
                applied_event_iris=group["applied_event_iris"],
                row_is_target_all=group["row_is_target_all"],
                row_is_target_any=group["row_is_target_any"],
                semantic_risk_level=group["semantic_risk_level"],
                semantic_risk_reasons=group["semantic_risk_reasons"],
                alternative_set_iris=group["alternative_set_iris"],
                alternative_set_source_iri=group["alternative_set_source_iri"],
                alternative_set_roles=group["alternative_set_roles"],
                alternative_gate_statuses=group["alternative_gate_statuses"],
                alternative_applied_source_iris=group[
                    "alternative_applied_source_iris"
                ],
                alternative_applied_revision_iris=group[
                    "alternative_applied_revision_iris"
                ],
                alternative_semantic_review_required=group[
                    "alternative_semantic_review_required"
                ],
            )
            for key in group_order
            for group in [groups[key]]
        ]
    @staticmethod
    def _staged_recovery_resolved_target_group_counts(
        groups: Iterable[StagedRevisionResolvedTargetGroup],
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for group in groups:
            counts[group.queue] = counts.get(group.queue, 0) + 1
        return counts
    def _staged_recovery_lane_from_batch_item(
        self,
        item: StagedGraphRevisionBatchRestageItem,
        *,
        summary_by_iri: dict[str, StagedGraphRevisionExportSummary],
        include_drafts: bool,
        repair_drafts_remaining: int | None,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None,
    ) -> tuple[StagedRevisionRecoveryLane, str | None, bool, bool]:
        queue_item = item.next_action_queue_item_after
        next_action = item.next_action_after
        lane = (
            queue_item.queue
            if queue_item is not None
            else next_action.queue
            if next_action is not None
            else "informational"
        )
        row_iri = (
            queue_item.row_iri
            if queue_item is not None
            else item.current_revision_iri
        )
        current_summary = summary_by_iri.get(item.current_revision_iri)
        changed_graphs = (
            current_summary.changed_graphs
            if current_summary is not None
            else []
        )
        shared_context_patch_count = (
            current_summary.shared_context_patch_count
            if current_summary is not None
            else 0
        )
        shared_context_graphs = (
            current_summary.shared_context_graphs
            if current_summary is not None
            else []
        )
        repair_draft: StagedRevisionRebaseDraft | None = None
        repair_draft_error: str | None = None
        repair_draft_deferred_reason: str | None = None
        warning: str | None = None
        repair_draft_attempted = False
        repair_draft_should_run = include_drafts and self._staged_recovery_should_draft_repair(
            item,
            lane=lane,
        )
        if repair_draft_should_run and repair_drafts_remaining == 0:
            repair_draft_deferred_reason = "repair_draft_limit_reached"
        elif repair_draft_should_run:
            repair_draft_attempted = True
            try:
                repair_draft = self.draft_staged_revision_rebase(
                    item.current_revision_iri,
                    validation_scope=validation_scope,
                )
            except DoxaBaseError as exc:
                repair_draft_error = str(exc)
                warning = (
                    "Could not draft staged revision repair for "
                    f"'{item.current_revision_iri}': {exc}"
                )
        suggested_next_actions = self._with_revision_snapshot_evidence_actions(
            item.suggested_next_actions_after,
            item.source_snapshot_evidence,
            item.current_snapshot_evidence,
        )
        if self._staged_recovery_should_use_embedded_draft_route(repair_draft):
            if repair_draft.next_action is not None:
                next_action = repair_draft.next_action
            if repair_draft.next_action_queue_item is not None:
                queue_item = repair_draft.next_action_queue_item
            suggested_next_actions = self._with_revision_snapshot_evidence_actions(
                repair_draft.suggested_next_actions,
                item.source_snapshot_evidence,
                item.current_snapshot_evidence,
            )
            lane = (
                queue_item.queue
                if queue_item is not None
                else next_action.queue
                if next_action is not None
                else lane
            )
            row_iri = (
                queue_item.row_iri
                if queue_item is not None
                else item.current_revision_iri
            )
        snapshot_next_action = self._snapshot_evidence_completion_next_action(
            suggested_next_actions
        )
        missing_current_graph_import = bool(
            item.source_snapshot_evidence.missing_current_graph_roles
            or item.current_snapshot_evidence.missing_current_graph_roles
        )
        if snapshot_next_action is not None and missing_current_graph_import:
            next_action = snapshot_next_action
            queue_item = self._revision_next_action_queue_item(
                row_iri=item.current_revision_iri,
                next_action=next_action,
                record_kind=self._graph_revision_record_kind_for_iri(
                    item.current_revision_iri
                ),
                application_status=item.status_after,
                application_decision=item.decision_after,
                stale_resolution_state=item.stale_resolution_state_after,
                staged_validation_status=item.current_staged_validation_status,
                alternative_gate=(
                    current_summary.alternative_gate
                    if current_summary is not None
                    else None
                ),
            )
            lane = queue_item.queue if queue_item is not None else next_action.queue
            row_iri = (
                queue_item.row_iri
                if queue_item is not None
                else item.current_revision_iri
            )
        return (
            StagedRevisionRecoveryLane(
                row_iri=row_iri,
                source_revision_iri=item.source_revision_iri,
                current_revision_iri=item.current_revision_iri,
                resolved_target_iri=(
                    queue_item.resolved_target_iri
                    if queue_item is not None
                    else None
                ),
                resolved_target_record_kind=(
                    queue_item.resolved_target_record_kind
                    if queue_item is not None
                    else None
                ),
                row_is_target=(
                    queue_item.row_is_target if queue_item is not None else True
                ),
                lane=lane,
                effective_recovery_action=lane,
                action_type=next_action.action_type if next_action is not None else None,
                action_label=next_action.action_label if next_action is not None else None,
                batch_action=item.action,
                not_restageable_reason=item.not_restageable_reason,
                summary=item.summary,
                changed_graphs=changed_graphs,
                shared_context_applies=bool(
                    shared_context_patch_count or shared_context_graphs
                ),
                shared_context_patch_count=shared_context_patch_count,
                shared_context_graphs=shared_context_graphs,
                status_before=item.status_before,
                decision_before=item.decision_before,
                routing_decision_before=item.routing_decision_before,
                stale_resolution_state_before=item.stale_resolution_state_before,
                blocking_reasons_before=item.blocking_reasons_before,
                exact_drift_summary=(
                    item.exact_drift_summary_before
                    or item.exact_drift_summary_after
                ),
                status_after=item.status_after,
                decision_after=item.decision_after,
                routing_decision_after=item.routing_decision_after,
                stale_resolution_state_after=item.stale_resolution_state_after,
                blocking_reasons_after=item.blocking_reasons_after,
                source_staged_validation_status=(
                    item.source_staged_validation_status
                ),
                source_validation_result_count=item.source_validation_result_count,
                current_staged_validation_status=(
                    item.current_staged_validation_status
                ),
                current_validation_result_count=item.current_validation_result_count,
                source_snapshot_evidence=item.source_snapshot_evidence,
                source_snapshot_evidence_completeness=(
                    item.source_snapshot_evidence_completeness
                ),
                current_snapshot_evidence=item.current_snapshot_evidence,
                current_snapshot_evidence_completeness=(
                    item.current_snapshot_evidence_completeness
                ),
                triples_to_add_after=item.triples_to_add_after,
                triples_to_remove_after=item.triples_to_remove_after,
                restaged_from=item.restaged_from,
                restaged_revision_iri=item.restaged_revision_iri,
                current_restaged_by=item.current_restaged_by,
                alternative_gate=(
                    current_summary.alternative_gate
                    if current_summary is not None
                    else None
                ),
                next_action=next_action,
                next_action_queue_item=queue_item,
                repair_draft=repair_draft,
                repair_draft_error=repair_draft_error,
                repair_draft_deferred_reason=repair_draft_deferred_reason,
                suggested_next_actions=suggested_next_actions,
                suggested_next_calls=[
                    action.call
                    for action in suggested_next_actions
                    if action.call
                ],
                batch_item=item,
                note=item.note,
            ),
            warning,
            repair_draft_attempted,
            repair_draft_deferred_reason is not None,
        )
    @staticmethod
    def _staged_recovery_should_use_embedded_draft_route(
        repair_draft: StagedRevisionRebaseDraft | None,
    ) -> bool:
        if repair_draft is None or repair_draft.preferred_action is not None:
            return False
        if any(
            action.tool_name == "draft_staged_revision_rebase"
            for action in repair_draft.suggested_next_actions
        ):
            return False
        return bool(repair_draft.next_action or repair_draft.suggested_next_actions)
    @staticmethod
    def _staged_recovery_should_draft_repair(
        item: StagedGraphRevisionBatchRestageItem,
        *,
        lane: str,
    ) -> bool:
        return (
            lane == "repair_or_replace"
            or item.routing_decision_after == "stage_same_slot_replacement"
            or item.not_restageable_reason
            in {
                "same_slot_replacement",
                "ambiguous_same_slot",
                "patch_repair_plan",
                "validation_failed",
                "patch_conflict",
                "inspect_restaged_source_validation_failure",
            }
        )
    @staticmethod
    def _staged_recovery_lane_counts(
        lanes: Iterable[StagedRevisionRecoveryLane],
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for lane in lanes:
            counts[lane.lane] = counts.get(lane.lane, 0) + 1
        return counts
    @staticmethod
    def _staged_recovery_action_is_mutating(
        action: SuggestedNextAction | RevisionNextAction | None,
    ) -> bool:
        if action is None:
            return False
        return action.tool_name in STAGED_RECOVERY_MUTATING_TOOL_NAMES
    @staticmethod
    def _staged_recovery_action_is_safe_review(
        action: SuggestedNextAction | RevisionNextAction | None,
    ) -> bool:
        if action is None:
            return False
        if getattr(action, "mutation_scope", None) == "none":
            return True
        return not DoxaBase._staged_recovery_action_is_mutating(action)
    @staticmethod
    def _staged_recovery_action_is_batch_restage_dry_run(
        action: SuggestedNextAction | RevisionNextAction | None,
    ) -> bool:
        return (
            action is not None
            and action.tool_name == "restage_staged_revisions"
            and action.arguments.get("dry_run") is True
            and DoxaBase._staged_recovery_action_is_safe_review(action)
        )
    @staticmethod
    def _staged_recovery_repair_inspection_required(
        lanes: Iterable[StagedRevisionRecoveryLane],
    ) -> bool:
        for lane in lanes:
            if lane.lane != "repair_or_replace":
                continue
            if DoxaBase._staged_recovery_action_is_mutating(lane.next_action):
                continue
            preferred_action = (
                lane.repair_draft.preferred_action
                if lane.repair_draft is not None
                else None
            )
            if DoxaBase._staged_recovery_action_is_mutating(preferred_action):
                continue
            return True
        return False
    def _staged_recovery_suggested_next_actions(
        self,
        lanes: Iterable[StagedRevisionRecoveryLane],
        *,
        would_restage_revision_iris: list[str],
    ) -> list[SuggestedNextAction]:
        handoff_preflight_actions: list[SuggestedNextAction] = []
        review_first_actions: list[SuggestedNextAction] = []
        mutation_actions: list[SuggestedNextAction] = []
        if would_restage_revision_iris:
            review_first_actions.append(
                self._staged_recovery_batch_restage_dry_run_action(
                    would_restage_revision_iris
                )
            )
        for lane in lanes:
            for action in lane.suggested_next_actions:
                if action.tool_name in {
                    "import_revision_snapshots",
                    "import_trig",
                }:
                    handoff_preflight_actions.append(action)
                elif action.tool_name in {
                    "describe_staged_revision",
                    "export_staged_revision",
                    "export_staged_revisions",
                    "describe_revision_lineage",
                    "describe_graph_revision",
                    "describe_applied_revision_diff",
                    "draft_staged_revision_rebase",
                }:
                    review_first_actions.append(action)
                else:
                    mutation_actions.append(action)
        return self._dedupe_suggested_next_actions(
            [*handoff_preflight_actions, *review_first_actions, *mutation_actions]
        )
    @staticmethod
    def _staged_recovery_blocking_preflight_actions(
        suggested_next_actions: Iterable[SuggestedNextAction],
    ) -> list[SuggestedNextAction]:
        return [
            action
            for action in suggested_next_actions
            if action.tool_name in {"import_revision_snapshots", "import_trig"}
        ]
    @staticmethod
    def _staged_recovery_mutation_allowed_after(
        *,
        blocking_preflight_actions: list[SuggestedNextAction],
        mutation_frontier_items: list[StagedRevisionMutationFrontierItem],
        repair_inspection_required: bool = False,
    ) -> str:
        if blocking_preflight_actions:
            return "handoff_preflight_required_before_mutation"
        if mutation_frontier_items:
            return "semantic_review_required_before_mutation"
        if repair_inspection_required:
            return "repair_inspection_required_before_mutation"
        return "no_mutation_frontier"
    @staticmethod
    def _staged_recovery_first_actions(
        *,
        mutation_allowed_after: str,
        blocking_preflight_actions: list[SuggestedNextAction],
        mutation_frontier_items: list[StagedRevisionMutationFrontierItem],
        suggested_next_actions: list[SuggestedNextAction],
    ) -> tuple[
        SuggestedNextAction | RevisionNextAction | None,
        SuggestedNextAction | RevisionNextAction | None,
        str | None,
    ]:
        first_mutation_action = None
        first_safe_action: SuggestedNextAction | RevisionNextAction | None = None
        first_safe_source: str | None = None
        if mutation_allowed_after == "handoff_preflight_required_before_mutation":
            if blocking_preflight_actions:
                first_safe_action = blocking_preflight_actions[0]
                first_safe_source = "blocking_preflight"
            elif suggested_next_actions:
                first_safe_action = suggested_next_actions[0]
                first_safe_source = "suggested_next_action"
            return first_mutation_action, first_safe_action, first_safe_source
        review_action = next(
            (
                action
                for action in suggested_next_actions
                if DoxaBase._staged_recovery_action_is_safe_review(action)
            ),
            None,
        )
        if review_action is not None:
            first_safe_action = review_action
            first_safe_source = "suggested_review_action"
        if any(
            item.requires_semantic_review_before_mutation
            for item in mutation_frontier_items
        ):
            semantic_review_action = (
                DoxaBase._staged_recovery_semantic_frontier_review_action(
                    mutation_frontier_items,
                    suggested_next_actions,
                )
            )
            if semantic_review_action is not None and (
                first_safe_action is None
                or not DoxaBase._staged_recovery_action_is_batch_restage_dry_run(
                    first_safe_action
                )
            ):
                first_safe_action = semantic_review_action
                first_safe_source = "semantic_frontier_review"
            if first_safe_action is None and suggested_next_actions:
                first_safe_action = suggested_next_actions[0]
                first_safe_source = "suggested_next_action"
            return first_mutation_action, first_safe_action, first_safe_source
        first_ungated_mutation_item = next(
            (
                item
                for item in mutation_frontier_items
                if not item.requires_semantic_review_before_mutation
            ),
            None,
        )
        if first_ungated_mutation_item is not None:
            first_mutation_action = first_ungated_mutation_item.action
            if first_safe_action is None:
                first_safe_action = first_mutation_action
                first_safe_source = "mutation_frontier"
        elif suggested_next_actions:
            if first_safe_action is None:
                first_safe_action = suggested_next_actions[0]
                first_safe_source = "suggested_next_action"
        return first_mutation_action, first_safe_action, first_safe_source
    def _staged_recovery_recommended_unattended_steps(
        self,
        *,
        blocking_preflight_actions: list[SuggestedNextAction],
        would_restage_revision_iris: list[str],
        helper_mutation_frontier_actions: list[SuggestedNextAction],
        mutation_frontier_items: list[StagedRevisionMutationFrontierItem],
        suggested_next_actions: list[SuggestedNextAction],
        requires_recheck_after_each_apply: bool,
    ) -> list[StagedRevisionRecoveryUnattendedStep]:
        steps: list[StagedRevisionRecoveryUnattendedStep] = []
        for action in blocking_preflight_actions:
            steps.append(
                self._staged_recovery_unattended_step(
                    step_kind="complete_handoff_preflight",
                    label="Complete handoff preflight",
                    action=action,
                    can_run_now=True,
                    prerequisite=None,
                    mutates=False,
                    requires_replan_after_completion=True,
                    stop_reason="rerun_plan_after_handoff_preflight",
                    revision_iris=self._suggested_action_revision_iris(action),
                    source_revision_iris=[],
                    target_iris=[],
                    note=(
                        "Run this blocking import/preflight action before any "
                        "staged recovery mutation, then rerun the planner."
                    ),
                )
            )
        if blocking_preflight_actions:
            return steps

        if would_restage_revision_iris:
            dry_run_action = self._staged_recovery_batch_restage_dry_run_action(
                would_restage_revision_iris
            )
            steps.append(
                self._staged_recovery_unattended_step(
                    step_kind="dry_run_mechanical_restage",
                    label="Dry-run mechanical restage worklist",
                    action=dry_run_action,
                    can_run_now=True,
                    prerequisite=None,
                    mutates=False,
                    requires_replan_after_completion=False,
                    stop_reason=None,
                    revision_iris=list(would_restage_revision_iris),
                    source_revision_iris=list(would_restage_revision_iris),
                    target_iris=[],
                    note=(
                        "Classify exactly would_restage_revision_iris before "
                        "creating restaged successors."
                    ),
                )
            )
            real_action = self._staged_recovery_batch_restage_real_action(
                would_restage_revision_iris
            )
            steps.append(
                self._staged_recovery_unattended_step(
                    step_kind="run_reviewed_mechanical_restage",
                    label="Run reviewed mechanical restage worklist",
                    action=real_action,
                    can_run_now=False,
                    prerequisite="after_reviewing_matching_dry_run",
                    mutates=True,
                    requires_replan_after_completion=True,
                    stop_reason="rerun_plan_after_restage",
                    revision_iris=list(would_restage_revision_iris),
                    source_revision_iris=list(would_restage_revision_iris),
                    target_iris=[],
                    note=(
                        "After the dry-run classifications still match review, "
                        "restage only this mechanical worklist, then rerun "
                        "recovery planning before applying successors."
                    ),
                )
            )

        helper_items_by_call = {
            item.call: item
            for item in mutation_frontier_items
            if item.item_kind == "helper_action" and item.call
        }
        for action in helper_mutation_frontier_actions:
            item = helper_items_by_call.get(action.call)
            requires_semantic_review = (
                bool(item.requires_semantic_review_before_mutation)
                if item is not None
                else False
            )
            blocked_by_mechanical_restage = bool(would_restage_revision_iris)
            prerequisite = None
            stop_reason = "rerun_plan_after_repair_staging"
            if blocked_by_mechanical_restage:
                prerequisite = "after_mechanical_restage_replan_if_still_current"
                stop_reason = "mechanical_restage_first"
            elif requires_semantic_review:
                prerequisite = "after_semantic_review"
                stop_reason = "semantic_review_required_before_repair"
            source_revision_iris = (
                list(item.source_revision_iris)
                if item is not None
                else self._suggested_action_revision_iris(action)
            )
            steps.append(
                self._staged_recovery_unattended_step(
                    step_kind="stage_repair_successor",
                    label="Stage repair successor",
                    action=action,
                    can_run_now=(
                        not blocked_by_mechanical_restage
                        and not requires_semantic_review
                    ),
                    prerequisite=prerequisite,
                    mutates=True,
                    requires_replan_after_completion=True,
                    stop_reason=stop_reason,
                    revision_iris=self._suggested_action_revision_iris(action),
                    source_revision_iris=source_revision_iris,
                    target_iris=[],
                    note=(
                        "Run the repair helper to create a concrete successor, "
                        "then check the successor and rerun recovery planning "
                        "before applying it."
                    ),
                )
            )

        blocked_by_prior_restage = bool(would_restage_revision_iris)
        for item in mutation_frontier_items:
            if item.item_kind != "revision_target":
                continue
            review_prerequisite = (
                "after_mechanical_restage_replan_if_still_current"
                if blocked_by_prior_restage
                else None
            )
            if item.requires_semantic_review_before_mutation:
                review_action = (
                    self._staged_recovery_semantic_frontier_review_action(
                        [item],
                        suggested_next_actions,
                    )
                    or item.action
                )
                steps.append(
                    self._staged_recovery_unattended_step(
                        step_kind="review_semantic_frontier",
                        label="Review semantic-gated mutation target",
                        action=review_action,
                        can_run_now=not blocked_by_prior_restage,
                        prerequisite=review_prerequisite,
                        mutates=False,
                        requires_replan_after_completion=False,
                        stop_reason="semantic_review_required_before_mutation",
                        revision_iris=list(item.row_iris),
                        source_revision_iris=list(item.source_revision_iris),
                        target_iris=[
                            value
                            for value in [item.target_iri]
                            if value is not None
                        ],
                        note=(
                            "Do not run the post-review mutation unattended "
                            "until this semantic gate is resolved."
                        ),
                    )
                )
                continue
            review_action = self._staged_recovery_frontier_review_action(
                item,
                suggested_next_actions,
            )
            if review_action is not None:
                steps.append(
                    self._staged_recovery_unattended_step(
                        step_kind="review_frontier_target",
                        label="Review mutation frontier target",
                        action=review_action,
                        can_run_now=not blocked_by_prior_restage,
                        prerequisite=review_prerequisite,
                        mutates=False,
                        requires_replan_after_completion=False,
                        stop_reason="review_frontier_target_before_mutation",
                        revision_iris=list(item.row_iris),
                        source_revision_iris=list(item.source_revision_iris),
                        target_iris=[
                            value
                            for value in [item.target_iri]
                            if value is not None
                        ],
                        note=(
                            "Inspect this frontier target before running the "
                            "post-review mutation step."
                        ),
                    )
                )
            steps.append(
                self._staged_recovery_unattended_step(
                    step_kind="mutate_one_frontier_target",
                    label="Mutate one reviewed frontier target",
                    action=item.action,
                    can_run_now=False,
                    prerequisite=(
                        "after_mechanical_restage_replan_if_still_current"
                        if blocked_by_prior_restage
                        else "after_reviewing_frontier_target"
                    ),
                    mutates=item.action is not None,
                    requires_replan_after_completion=True,
                    stop_reason=(
                        "apply_at_most_one_then_replan"
                        if (
                            requires_recheck_after_each_apply
                            or item.queue == "apply_after_review"
                        )
                        else "rerun_plan_after_mutation"
                    ),
                    revision_iris=list(item.row_iris),
                    source_revision_iris=list(item.source_revision_iris),
                    target_iris=[
                        value for value in [item.target_iri] if value is not None
                    ],
                    note=(
                        "Run at most one reviewed mutation target from this "
                        "plan, then rerun recovery planning before the next "
                        "mutation."
                    ),
                )
            )

        if not steps:
            review_action = next(
                (
                    action
                    for action in suggested_next_actions
                    if self._staged_recovery_action_is_safe_review(action)
                ),
                None,
            )
            if review_action is not None:
                steps.append(
                    self._staged_recovery_unattended_step(
                        step_kind="inspect_frontier",
                        label="Inspect recovery frontier",
                        action=review_action,
                        can_run_now=True,
                        prerequisite=None,
                        mutates=False,
                        requires_replan_after_completion=False,
                        stop_reason="no_unattended_mutation_frontier",
                        revision_iris=self._suggested_action_revision_iris(
                            review_action
                        ),
                        source_revision_iris=[],
                        target_iris=[],
                        note=(
                            "No unattended mutation frontier is currently "
                            "available; follow the inspection route."
                        ),
                    )
                )
        return steps
    @staticmethod
    def _staged_recovery_unattended_step(
        *,
        step_kind: str,
        label: str,
        action: SuggestedNextAction | RevisionNextAction | None,
        can_run_now: bool,
        prerequisite: str | None,
        mutates: bool,
        requires_replan_after_completion: bool,
        stop_reason: str | None,
        revision_iris: Iterable[str],
        source_revision_iris: Iterable[str],
        target_iris: Iterable[str],
        note: str,
    ) -> StagedRevisionRecoveryUnattendedStep:
        return StagedRevisionRecoveryUnattendedStep(
            step_kind=step_kind,
            label=label,
            action=action,
            call=action.call if action is not None else None,
            can_run_now=can_run_now,
            prerequisite=prerequisite,
            mutates=mutates,
            requires_replan_after_completion=requires_replan_after_completion,
            stop_reason=stop_reason,
            revision_iris=list(dict.fromkeys(revision_iris)),
            source_revision_iris=list(dict.fromkeys(source_revision_iris)),
            target_iris=list(dict.fromkeys(target_iris)),
            note=note,
        )
    @staticmethod
    def _staged_recovery_order_lanes(
        lanes: list[StagedRevisionRecoveryLane],
        *,
        selected_revision_iris: list[str],
    ) -> list[StagedRevisionRecoveryLane]:
        first_index_by_iri = {
            revision_iri: index
            for index, revision_iri in enumerate(selected_revision_iris)
        }
        return sorted(
            lanes,
            key=lambda lane: first_index_by_iri.get(
                lane.source_revision_iri,
                len(first_index_by_iri),
            ),
        )
    def _staged_recovery_batch_restage_dry_run_action(
        self,
        revision_iris: list[str],
    ) -> SuggestedNextAction:
        arguments: dict[str, Any] = {
            "revision_iris": list(revision_iris),
            "dry_run": True,
        }
        return EffectAnnotatedSuggestedNextAction(
            action_label="Dry-run batch restage",
            tool_name="restage_staged_revisions",
            mcp_tool_name="doxabase.restage_staged_revisions",
            arguments=arguments,
            reason=(
                "Planner found mechanically restageable stale revisions. Run a "
                "batch dry-run over would_restage_revision_iris before creating "
                "successors, then restage only the reviewed worklist."
            ),
            call=self._suggested_call_string(
                "restage_staged_revisions",
                arguments,
            ),
            mutation_scope="none",
            mutates_project_graph=False,
            writes_history=False,
            writes_files=False,
        )
    def _staged_recovery_batch_restage_real_action(
        self,
        revision_iris: list[str],
    ) -> SuggestedNextAction:
        arguments: dict[str, Any] = {
            "revision_iris": list(revision_iris),
            "dry_run": False,
        }
        return EffectAnnotatedSuggestedNextAction(
            action_label="Run reviewed batch restage",
            tool_name="restage_staged_revisions",
            mcp_tool_name="doxabase.restage_staged_revisions",
            arguments=arguments,
            reason=(
                "Run the real batch restage only after the dry-run "
                "classification has been reviewed and still matches the "
                "mechanical worklist."
            ),
            call=self._suggested_call_string(
                "restage_staged_revisions",
                arguments,
            ),
            mutation_scope="history",
            mutates_project_graph=False,
            writes_history=True,
            writes_files=False,
        )
    @staticmethod
    def _stale_seed_recovery_message(missing_seed_terms: Iterable[str]) -> str:
        missing_text = ", ".join(missing_seed_terms)
        return (
            "This capsule's immutable base_ontology is missing current staging "
            f"vocabulary ({missing_text}), which usually means it was created "
            "with an older DoxaBase seed. Reopening the capsule or calling "
            "seed_base_graphs() only seeds empty immutable graphs and will not "
            "update stale seed graphs. Preflight a recovery-complete handoff, "
            "export the project/history TriG plus companion revision snapshot "
            "JSON, then import that manifest into a fresh DoxaBase.create(...) "
            "capsule. The snapshot bundle may be empty when no revision rows "
            "exist; otherwise import_handoff_bundle() returns the staged "
            "recovery plan to follow before further mutation."
        )
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
            "resume_call": resume_action.call,
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
            and first_action.tool_name == "start_staged_revision_recovery_session"
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
                    action.tool_name
                    == "describe_staged_revision_recovery_session"
                ):
                    resume_recovery_session_action = action
                    break
        resume_recovery_session_iri = (
            resume_recovery_session_action.arguments.get("session_iri")
            if resume_recovery_session_action is not None
            and isinstance(
                resume_recovery_session_action.arguments.get("session_iri"),
                str,
            )
            else (
                matching_recovery_session_iris[0]
                if imported_session_continuation_required
                and matching_recovery_session_iris
                else None
            )
        )
        resume_recovery_session_call = (
            resume_recovery_session_action.call
            if resume_recovery_session_action is not None
            else None
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
                and first_action.tool_name == "export_preflight"
            ):
                first_safe_action = first_action
                first_safe_action_source = "handoff_import_privacy_review"
        elif validation_review_required_before_recovery:
            if (
                first_action is not None
                and first_action.tool_name == "validate_graph"
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
            resume_recovery_session_call=resume_recovery_session_call,
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
            first_safe_review_or_mutation_call=(
                first_safe_action.call if first_safe_action is not None else None
            ),
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
                                call=replacement.call,
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
            blocking_preflight_calls=[
                action.call for action in blocking_preflight_actions if action.call
            ],
            recommended_unattended_steps=recommended_unattended_steps,
            first_mutation_action=first_mutation_action,
            first_mutation_call=(
                first_mutation_action.call
                if first_mutation_action is not None
                else None
            ),
            first_safe_review_or_mutation_action=(
                first_safe_review_or_mutation_action
            ),
            first_safe_review_or_mutation_call=(
                first_safe_review_or_mutation_action.call
                if first_safe_review_or_mutation_action is not None
                else None
            ),
            first_safe_review_or_mutation_source=(
                first_safe_review_or_mutation_source
            ),
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[
                action.call for action in suggested_next_actions if action.call
            ],
        )
    def _import_handoff_bundle_privacy_gated_recovery_plan(
        self,
        recovery_plan: StagedRevisionRecoveryPlan,
        privacy_action: SuggestedNextAction,
    ) -> StagedRevisionRecoveryPlan:
        redacted_plan = self._privacy_redacted_api_value(recovery_plan)
        privacy_calls = [privacy_action.call] if privacy_action.call else []
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
                suggested_next_calls=privacy_calls,
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
                suggested_next_calls=privacy_calls,
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
            first_mutation_call=None,
            first_safe_review_or_mutation_action=privacy_action,
            first_safe_review_or_mutation_call=privacy_action.call,
            first_safe_review_or_mutation_source="handoff_import_privacy_review",
            helper_mutation_frontier_actions=[],
            helper_mutation_frontier_calls=[],
            mutation_allowed_after=(
                "handoff_import_privacy_review_required_before_recovery"
            ),
            blocking_preflight_actions=[privacy_action],
            blocking_preflight_calls=privacy_calls,
            recommended_unattended_steps=privacy_steps,
            revision_summaries=[
                gated_summary(summary)
                for summary in redacted_plan.revision_summaries
            ],
            bundle_summary=bundle_summary,
            suggested_next_actions=[privacy_action],
            suggested_next_calls=privacy_calls,
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
        session_calls = [action.call for action in session_actions if action.call]
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
            first_mutation_call=None,
            first_safe_review_or_mutation_action=session_action,
            first_safe_review_or_mutation_call=session_action.call,
            first_safe_review_or_mutation_source="imported_recovery_session",
            helper_mutation_frontier_actions=[],
            helper_mutation_frontier_calls=[],
            mutation_allowed_after=(
                "imported_recovery_session_required_before_mutation"
            ),
            blocking_preflight_actions=session_actions,
            blocking_preflight_calls=session_calls,
            recommended_unattended_steps=session_steps,
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[
                action.call for action in suggested_next_actions if action.call
            ],
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
        validation_calls = (
            [validation_action.call] if validation_action.call else []
        )
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
                suggested_next_calls=validation_calls,
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
                suggested_next_calls=validation_calls,
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
            first_mutation_call=None,
            first_safe_review_or_mutation_action=validation_action,
            first_safe_review_or_mutation_call=validation_action.call,
            first_safe_review_or_mutation_source="handoff_import_validation_review",
            helper_mutation_frontier_actions=[],
            helper_mutation_frontier_calls=[],
            mutation_allowed_after=(
                "handoff_import_validation_review_required_before_recovery"
            ),
            blocking_preflight_actions=[validation_action],
            blocking_preflight_calls=validation_calls,
            recommended_unattended_steps=validation_steps,
            revision_summaries=[
                gated_summary(summary)
                for summary in recovery_plan.revision_summaries
            ],
            bundle_summary=bundle_summary,
            suggested_next_actions=[validation_action],
            suggested_next_calls=validation_calls,
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
    def _recovery_session_iris(self, history_graphs: list[str]) -> list[str]:
        return self._subjects(
            history_graphs,
            str(RDF.type),
            self.expand_iri("rc:StagedRevisionRecoverySession"),
        )
    def _matching_recovery_session_iris(
        self,
        session_iris: list[str],
        *,
        revision_iris: list[str],
        history_graphs: list[str],
    ) -> list[str]:
        requested = {self.expand_iri(iri) for iri in revision_iris}
        if not requested:
            return []
        matching: list[str] = []
        for session_iri in session_iris:
            source_revision_iris = (
                self._staged_recovery_session_source_revision_iris(
                    session_iri,
                    history_graphs=history_graphs,
                )
            )
            if requested.intersection(source_revision_iris):
                matching.append(session_iri)
        return matching
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
        return self._effect_annotated_suggested_next_action(
            action_label="Continue imported recovery session",
            tool_name="describe_staged_revision_recovery_session",
            arguments=arguments,
            reason=(
                "The handoff imported a persisted staged-revision recovery "
                "session whose source revisions overlap the manifest revisions. "
                "Describe it before starting a receiver-local session so source "
                "session provenance and live recovery state stay connected."
            ),
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
            "current_staged_work_only": False,
            "include_drafts": include_drafts,
            "drift_detail": drift_detail,
        }
        if manifest_path is not None:
            arguments["handoff_manifest_path"] = manifest_path
        if validation_scope is not None:
            arguments["validation_scope"] = validation_scope
        return self._effect_annotated_suggested_next_action(
            action_label="Start receiver-local recovery session",
            tool_name="start_staged_revision_recovery_session",
            arguments=arguments,
            reason=(
                "No matching imported recovery session was found. Persist a "
                "receiver-local session for the imported manifest revisions so "
                "multi-step restage, repair, and apply work can be replanned "
                "from one stable session IRI."
            ),
        )
    def _subject_exists(self, subject: str, graphs: list[str]) -> bool:
        graph_filter, params = self._graph_filter(graphs)
        row = self._conn.execute(
            f"""
            SELECT 1
            FROM quads
            WHERE subject = ?
              {graph_filter}
            LIMIT 1
            """,
            [subject, *params],
        ).fetchone()
        return row is not None
