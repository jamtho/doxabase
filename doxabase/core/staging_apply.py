"""Staged revision apply checks and application.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via StagingApplyMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class StagingApplyMixin:
    @contextmanager
    def _scoped_staged_apply_check_cache(
        self,
        cache: dict[StagedApplyCheckCacheKey, StagedRevisionApplyCheck] | None = None,
    ) -> Iterator[dict[StagedApplyCheckCacheKey, StagedRevisionApplyCheck]]:
        if self._staged_apply_check_cache is not None:
            yield self._staged_apply_check_cache
            return
        previous_cache = self._staged_apply_check_cache
        active_cache: dict[StagedApplyCheckCacheKey, StagedRevisionApplyCheck] = (
            cache if cache is not None else {}
        )
        self._staged_apply_check_cache = active_cache
        try:
            yield active_cache
        finally:
            self._staged_apply_check_cache = previous_cache
    def describe_applied_revision_diff(
        self,
        iri: str,
        *,
        graph: str | None = "history",
        include_triples: bool = False,
        max_triples: int = 500,
    ) -> AppliedRevisionDiffDescription:
        if max_triples < 1:
            raise DoxaBaseError("max_triples must be at least 1")
        data_graphs = self._expand_graphs([graph] if graph else None)
        applied = self.describe_graph_revision(iri, graph=graph)
        staged_revision_iri = applied.applies_staged_revision
        if staged_revision_iri is None:
            raise DoxaBaseError(
                f"Graph revision '{iri}' is not an applied staged revision"
            )
        staged = self.describe_staged_revision(staged_revision_iri, graph=graph)
        before_snapshots = {
            snapshot.graph_role: snapshot for snapshot in staged.graph_snapshots
        }
        after_snapshots = {
            snapshot.graph_role: snapshot for snapshot in applied.graph_snapshots
        }
        graph_roles = list(dict.fromkeys(applied.changed_graphs))
        if not graph_roles:
            graph_roles = sorted(set(before_snapshots) | set(after_snapshots))
        snapshot_evidence = self._revision_snapshot_evidence_status(
            applied.iri,
            data_graphs,
        )
        source_snapshot_evidence = self._revision_snapshot_evidence_status(
            staged_revision_iri,
            data_graphs,
        )
        suggested_next_actions = self._with_revision_snapshot_evidence_actions(
            [],
            snapshot_evidence,
            source_snapshot_evidence,
        )

        return AppliedRevisionDiffDescription(
            applied_revision_iri=applied.iri,
            staged_revision_iri=staged_revision_iri,
            snapshot_evidence=snapshot_evidence,
            source_snapshot_evidence=source_snapshot_evidence,
            changed_graphs=graph_roles,
            include_triples=include_triples,
            max_triples=max_triples,
            graph_diffs=[
                self._applied_revision_graph_snapshot_diff(
                    graph_role=graph_role,
                    before_revision_iri=staged_revision_iri,
                    after_revision_iri=applied.iri,
                    before_snapshot=before_snapshots.get(graph_role),
                    after_snapshot=after_snapshots.get(graph_role),
                    include_triples=include_triples,
                    max_triples=max_triples,
                )
                for graph_role in graph_roles
            ],
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[
                action.call for action in suggested_next_actions
            ],
        )
    def _applied_revision_graph_snapshot_diff(
        self,
        *,
        graph_role: str,
        before_revision_iri: str,
        after_revision_iri: str,
        before_snapshot: GraphSnapshotDescription | None,
        after_snapshot: GraphSnapshotDescription | None,
        include_triples: bool,
        max_triples: int,
    ) -> AppliedRevisionGraphSnapshotDiff:
        exact_available = self._graph_snapshot_storage_exists(
            before_revision_iri,
            graph_role,
        ) and self._graph_snapshot_storage_exists(after_revision_iri, graph_role)
        triples_added: list[GraphTripleDescription] = []
        triples_removed: list[GraphTripleDescription] = []
        triples_added_count: int | None = None
        triples_removed_count: int | None = None
        triples_added_truncated = False
        triples_removed_truncated = False
        exact_included = False
        if exact_available:
            before_rows = set(
                self._graph_snapshot_storage_rows(before_revision_iri, graph_role)
            )
            after_rows = set(
                self._graph_snapshot_storage_rows(after_revision_iri, graph_role)
            )
            added_rows = self._sort_graph_storage_rows(after_rows - before_rows)
            removed_rows = self._sort_graph_storage_rows(before_rows - after_rows)
            triples_added_count = len(added_rows)
            triples_removed_count = len(removed_rows)
            if include_triples:
                exact_included = True
                triples_added_truncated = triples_added_count > max_triples
                triples_removed_truncated = triples_removed_count > max_triples
                triples_added = [
                    self._graph_triple_description(row)
                    for row in added_rows[:max_triples]
                ]
                triples_removed = [
                    self._graph_triple_description(row)
                    for row in removed_rows[:max_triples]
                ]
                if triples_added_truncated or triples_removed_truncated:
                    note = (
                        "Exact before/after snapshot triples are available and "
                        "included up to max_triples per added/removed array."
                    )
                else:
                    note = (
                        "Exact before/after snapshot triples are included from "
                        "stored revision snapshot rows."
                    )
            else:
                triples_added_truncated = triples_added_count > 0
                triples_removed_truncated = triples_removed_count > 0
                note = (
                    "Exact before/after snapshot triples are available but "
                    "omitted; call describe_applied_revision_diff(..., "
                    "include_triples=True) to include arrays."
                )
        else:
            note = self._missing_applied_snapshot_rows_note(
                before_snapshot=before_snapshot,
                after_snapshot=after_snapshot,
            )

        return AppliedRevisionGraphSnapshotDiff(
            graph_role=graph_role,
            count_basis="target_graph_only",
            before_revision_iri=before_revision_iri,
            after_revision_iri=after_revision_iri,
            before_triple_count=(
                before_snapshot.triple_count if before_snapshot is not None else None
            ),
            after_triple_count=(
                after_snapshot.triple_count if after_snapshot is not None else None
            ),
            before_content_digest=(
                before_snapshot.content_digest if before_snapshot is not None else None
            ),
            after_content_digest=(
                after_snapshot.content_digest if after_snapshot is not None else None
            ),
            exact_changed_triples_available=exact_available,
            exact_changed_triples_included=exact_included,
            triples_added_count=triples_added_count,
            triples_removed_count=triples_removed_count,
            triples_added_truncated=triples_added_truncated,
            triples_removed_truncated=triples_removed_truncated,
            max_triples=max_triples,
            triples_added=triples_added,
            triples_removed=triples_removed,
            note=note,
        )
    def _applied_revision_event_suggested_actions(
        self,
        revision_iri: str,
    ) -> list[SuggestedNextAction]:
        return [
            SuggestedNextAction(
                action_label="Inspect applied event",
                tool_name="describe_graph_revision",
                mcp_tool_name="doxabase.describe_graph_revision",
                arguments={"iri": revision_iri},
                reason=(
                    "Inspect the applied revision event for durable history "
                    "context."
                ),
                call=self._suggested_call_string(
                    "describe_graph_revision",
                    {"iri": revision_iri},
                ),
            ),
            SuggestedNextAction(
                action_label="Inspect applied diff",
                tool_name="describe_applied_revision_diff",
                mcp_tool_name="doxabase.describe_applied_revision_diff",
                arguments={"iri": revision_iri},
                reason=(
                    "Inspect stored before/after graph snapshot counts and, "
                    "when needed, exact changed triples for the applied event."
                ),
                call=self._suggested_call_string(
                    "describe_applied_revision_diff",
                    {"iri": revision_iri},
                ),
            ),
        ]
    def _resource_revision_item_with_apply_check(
        self,
        item: ResourceRevisionListItem,
        *,
        drift_detail: TypingLiteral["summary", "exact"],
    ) -> ResourceRevisionListItem:
        revision = item.revision
        if not revision.has_patch_payload:
            return item

        application_status: str | None = None
        application_decision: str | None = None
        application_can_apply: bool | None = None
        application_summary: str | None = None
        application_recommended_resolution: str | None = None
        application_validation_skipped_reason: str | None = None
        application_blocking_reasons: list[str] = []
        application_count_drifts: list[StagedGraphCountDrift] = []
        application_snapshot_drifts: list[StagedGraphSnapshotDrift] = []
        application_semantic_risk_level: str | None = None
        application_semantic_risk_reasons: list[str] = []
        suggested_next_actions: list[SuggestedNextAction] = []
        try:
            check = self.check_staged_revision_apply(revision.iri)
        except DoxaBaseError:
            application_status = "not_available"
            application_decision = "inspect_staged_revision"
        else:
            application_status = check.status
            application_decision = check.decision
            application_can_apply = check.can_apply
            application_summary = check.summary
            application_recommended_resolution = check.recommended_resolution
            application_validation_skipped_reason = check.validation_skipped_reason
            application_blocking_reasons = check.blocking_reasons
            application_count_drifts = check.count_drifts
            application_semantic_risk_level = check.semantic_risk_level
            application_semantic_risk_reasons = check.semantic_risk_reasons
            if drift_detail == "exact":
                application_snapshot_drifts = check.snapshot_drifts
            else:
                application_snapshot_drifts = self._summary_snapshot_drifts(
                    check.snapshot_drifts
                )
            suggested_next_actions = check.suggested_next_actions

        stale_resolution_state = self._stale_resolution_state(
            status=application_status,
            has_patch_payload=revision.has_patch_payload,
            restaged_from=revision.restaged_from,
            restaged_by=revision.restaged_by,
        )
        suggested_next_actions = self._with_revision_snapshot_evidence_actions(
            suggested_next_actions,
            revision.snapshot_evidence,
        )
        next_action = self._revision_next_action(
            revision.iri,
            apply_status=application_status,
            apply_decision=application_decision,
            stale_resolution_state=stale_resolution_state,
            suggested_next_actions=suggested_next_actions,
            restaged_by=revision.restaged_by,
            current_restaged_by=revision.current_restaged_by,
            record_kind=revision.record_kind,
            staged_validation_status=revision.staged_validation_status,
        )
        checked_revision = replace(
            revision,
            stale_resolution_state=stale_resolution_state,
            application_status=application_status,
            application_decision=application_decision,
            application_can_apply=application_can_apply,
            application_summary=application_summary,
            application_recommended_resolution=application_recommended_resolution,
            application_validation_skipped_reason=(
                application_validation_skipped_reason
            ),
            application_blocking_reasons=application_blocking_reasons,
            application_count_drifts=application_count_drifts,
            application_snapshot_drifts=application_snapshot_drifts,
            application_semantic_risk_level=application_semantic_risk_level,
            application_semantic_risk_reasons=application_semantic_risk_reasons,
            next_action=next_action,
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[action.call for action in suggested_next_actions],
        )
        return replace(item, revision=checked_revision)
    def _resource_applied_revision_diff_summary(
        self,
        *,
        resource_iri: str,
        applied_revision_iri: str,
        staged_revision_iri: str,
        graph: str | None,
        include_triples: bool,
        max_triples: int,
        applied_item: ResourceRevisionListItem | None,
    ) -> ResourceAppliedRevisionDiffSummary:
        data_graphs = self._expand_graphs([graph] if graph else None)
        before_snapshots = {
            snapshot.graph_role: snapshot
            for snapshot in self._graph_revision_snapshots(
                staged_revision_iri,
                data_graphs,
            )
        }
        after_snapshots = {
            snapshot.graph_role: snapshot
            for snapshot in self._graph_revision_snapshots(
                applied_revision_iri,
                data_graphs,
            )
        }
        changed_graphs = (
            list(applied_item.revision.changed_graphs)
            if applied_item is not None
            else self._objects(data_graphs, applied_revision_iri, "rc:changedGraph")
        )
        if not changed_graphs:
            changed_graphs = sorted(set(before_snapshots) | set(after_snapshots))
        return ResourceAppliedRevisionDiffSummary(
            applied_revision_iri=applied_revision_iri,
            staged_revision_iri=staged_revision_iri,
            snapshot_evidence=self._revision_snapshot_evidence_status(
                applied_revision_iri,
                data_graphs,
            ),
            source_snapshot_evidence=self._revision_snapshot_evidence_status(
                staged_revision_iri,
                data_graphs,
            ),
            changed_graphs=changed_graphs,
            include_triples=include_triples,
            max_triples=max_triples,
            graph_diffs=[
                self._resource_applied_revision_graph_diff_summary(
                    resource_iri=resource_iri,
                    graph_role=graph_role,
                    before_revision_iri=staged_revision_iri,
                    after_revision_iri=applied_revision_iri,
                    before_snapshot=before_snapshots.get(graph_role),
                    after_snapshot=after_snapshots.get(graph_role),
                    include_triples=include_triples,
                    max_triples=max_triples,
                )
                for graph_role in changed_graphs
            ],
        )
    def _resource_applied_revision_graph_diff_summary(
        self,
        *,
        resource_iri: str,
        graph_role: str,
        before_revision_iri: str,
        after_revision_iri: str,
        before_snapshot: GraphSnapshotDescription | None,
        after_snapshot: GraphSnapshotDescription | None,
        include_triples: bool,
        max_triples: int,
    ) -> ResourceAppliedRevisionGraphDiffSummary:
        exact_available = self._graph_snapshot_storage_exists(
            before_revision_iri,
            graph_role,
        ) and self._graph_snapshot_storage_exists(after_revision_iri, graph_role)
        resource_added_rows: list[GraphStorageRow] = []
        resource_removed_rows: list[GraphStorageRow] = []
        if exact_available:
            before_rows = set(
                self._graph_snapshot_storage_rows(before_revision_iri, graph_role)
            )
            after_rows = set(
                self._graph_snapshot_storage_rows(after_revision_iri, graph_role)
            )
            resource_added_rows = [
                row
                for row in self._sort_graph_storage_rows(after_rows - before_rows)
                if self._graph_storage_row_mentions_resource(row, resource_iri)
            ]
            resource_removed_rows = [
                row
                for row in self._sort_graph_storage_rows(before_rows - after_rows)
                if self._graph_storage_row_mentions_resource(row, resource_iri)
            ]

        added_count = len(resource_added_rows) if exact_available else None
        removed_count = len(resource_removed_rows) if exact_available else None
        added_truncated = bool(
            exact_available
            and added_count is not None
            and added_count > max_triples
        )
        removed_truncated = bool(
            exact_available
            and removed_count is not None
            and removed_count > max_triples
        )
        triples_included = exact_available and include_triples
        if exact_available:
            if include_triples:
                note = (
                    "Resource-filtered exact before/after snapshot triples are "
                    "included from stored revision snapshot rows."
                )
                if added_truncated or removed_truncated:
                    note = (
                        "Resource-filtered exact before/after snapshot triples "
                        "are included up to max_triples per added/removed array."
                    )
            else:
                note = (
                    "Resource-filtered exact before/after snapshot triple counts "
                    "are available; pass include_triples=True to include arrays."
                )
        else:
            note = self._missing_applied_snapshot_rows_note(
                before_snapshot=before_snapshot,
                after_snapshot=after_snapshot,
            )

        return ResourceAppliedRevisionGraphDiffSummary(
            graph_role=graph_role,
            count_basis="target_graph_only",
            before_revision_iri=before_revision_iri,
            after_revision_iri=after_revision_iri,
            before_triple_count=(
                before_snapshot.triple_count if before_snapshot is not None else None
            ),
            after_triple_count=(
                after_snapshot.triple_count if after_snapshot is not None else None
            ),
            before_content_digest=(
                before_snapshot.content_digest if before_snapshot is not None else None
            ),
            after_content_digest=(
                after_snapshot.content_digest if after_snapshot is not None else None
            ),
            exact_changed_triples_available=exact_available,
            exact_changed_triples_included=triples_included,
            resource_triples_added_count=added_count,
            resource_triples_removed_count=removed_count,
            resource_triples_added_truncated=added_truncated,
            resource_triples_removed_truncated=removed_truncated,
            max_triples=max_triples,
            resource_triples_added=(
                [
                    self._graph_triple_description(row)
                    for row in resource_added_rows[:max_triples]
                ]
                if triples_included
                else []
            ),
            resource_triples_removed=(
                [
                    self._graph_triple_description(row)
                    for row in resource_removed_rows[:max_triples]
                ]
                if triples_included
                else []
            ),
            note=note,
        )
    @staticmethod
    def _staged_apply_check_has_ambiguous_same_slot_review(
        check: StagedRevisionApplyCheck,
    ) -> bool:
        if (
            check.next_action is not None
            and check.next_action.action_label == "Review ambiguous same-slot conflict"
        ):
            return True
        return any(
            action.action_label == "Review ambiguous same-slot conflict"
            for action in check.suggested_next_actions
        )
    def check_staged_revision_apply(
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
    ) -> StagedRevisionApplyCheck:
        cache = self._staged_apply_check_cache
        revision_iri = self.expand_iri(iri)
        cache_key = (revision_iri, validation_scope)
        if cache is not None and cache_key in cache:
            return cache[cache_key]
        check = self._preview_staged_revision_application(
            iri,
            validation_scope=validation_scope,
        ).check
        if cache is not None:
            cache[cache_key] = check
        return check
    @staticmethod
    def _staged_apply_check_blocking_preflight_actions(
        snapshot_evidence: RevisionSnapshotEvidenceStatus,
    ) -> list[SuggestedNextAction]:
        if (
            snapshot_evidence.status == "history_plus_snapshot_rows"
            and not snapshot_evidence.missing_current_graph_roles
            and not snapshot_evidence.missing_snapshot_row_graph_roles
        ):
            return []
        return list(snapshot_evidence.suggested_next_actions)
    @staticmethod
    def _staged_apply_check_mutation_allowed_after(
        blocking_preflight_actions: list[SuggestedNextAction],
    ) -> str:
        if blocking_preflight_actions:
            return "handoff_preflight_required_before_mutation"
        return "direct_check_no_preflight"
    def _staged_apply_check_first_safe_next_action(
        self,
        next_action: RevisionNextAction | None,
        *,
        staged_revision_iri: str,
        suggested_next_actions: list[SuggestedNextAction],
        blocking_preflight_actions: list[SuggestedNextAction],
        alternative_gate: StagedRevisionAlternativeGate,
    ) -> RevisionNextAction | None:
        snapshot_next_action = self._snapshot_evidence_completion_next_action(
            blocking_preflight_actions
        )
        if snapshot_next_action is not None:
            return snapshot_next_action
        if alternative_gate.semantic_review_required:
            review_action = self._staged_apply_check_semantic_review_action(
                staged_revision_iri,
                suggested_next_actions,
            )
            return self._revision_next_action_from_suggested_action(
                review_action,
                action_type="semantic_review_required",
                queue="semantic_review_required",
                source="check_staged_revision_apply",
            )
        return next_action
    def _staged_apply_check_semantic_review_action(
        self,
        staged_revision_iri: str,
        suggested_next_actions: list[SuggestedNextAction],
    ) -> SuggestedNextAction:
        for tool_name in (
            "describe_staged_revision",
            "describe_revision_lineage",
            "export_staged_revision",
        ):
            for action in suggested_next_actions:
                if action.tool_name == tool_name:
                    return action
        return self._effect_annotated_suggested_next_action(
            action_label="Review semantic alternative",
            tool_name="describe_staged_revision",
            arguments={"iri": staged_revision_iri},
            reason=(
                "Semantic review is required before mutating this staged "
                "revision because it belongs to an unresolved or already-applied "
                "alternative set."
            ),
        )
    def _staged_apply_check_ordered_suggested_next_actions(
        self,
        *,
        blocking_preflight_actions: list[SuggestedNextAction],
        suggested_next_actions: list[SuggestedNextAction],
    ) -> list[SuggestedNextAction]:
        if not blocking_preflight_actions:
            return suggested_next_actions
        return self._dedupe_suggested_next_actions(
            [*blocking_preflight_actions, *suggested_next_actions]
        )
    def apply_staged_revision(
        self,
        iri: str,
        *,
        applied_revision_iri: str | None = None,
        created_at: datetime | str | None = None,
        created_by: str | None = None,
        allow_validation_failure: bool = False,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
    ) -> AppliedStagedRevisionRecord:
        preview = self._preview_staged_revision_application(
            iri,
            validation_scope=validation_scope,
        )
        staged = preview.staged
        check = preview.check
        if staged.review_resolution is not None:
            raise DoxaBaseError(
                "Staged revision cannot be applied because it has a recorded "
                "review resolution "
                f"'{staged.review_resolution.resolution_revision_iri}'."
            )
        if check.already_applied_by is not None:
            raise DoxaBaseError(
                f"Staged revision '{iri}' has already been applied by "
                f"'{check.already_applied_by}'"
            )
        if check.conflicts:
            raise DoxaBaseError(
                "Staged revision cannot be applied: " + "; ".join(check.conflicts)
            )
        if check.status == "superseded_by_restage":
            raise DoxaBaseError(
                "Staged revision cannot be applied because it has a refreshed "
                "successor; inspect the current successor instead."
            )
        if check.validation_conforms is False and not allow_validation_failure:
            inspect_call = (
                "describe_staged_revision("
                f"iri={staged.iri!r}, include_current_apply_check=True)"
            )
            raise DoxaBaseError(
                "Applying staged revision would fail validation; inspect "
                f"validation_results for staged revision '{staged.iri}' with "
                f"{inspect_call}, or pass allow_validation_failure=True."
            )
        if check.status == "noop":
            raise DoxaBaseError(
                "Staged revision cannot be applied because replay has no "
                "effective patch triples; inspect the staged revision and "
                "current graph state instead."
            )

        addition_operation = self.expand_iri("rc:AdditionPatch")
        triples_added = 0
        triples_removed = 0
        for patch, patch_graph in preview.parsed_patches:
            target_graph = self._required_staged_patch_target_graph(patch)
            operation = self._required_staged_patch_field(
                patch,
                "operation",
                patch.operation,
            )
            if operation == addition_operation:
                triples_added += self._insert_graph(target_graph, patch_graph)
            else:
                triples_removed += self._remove_graph_triples(target_graph, patch_graph)

        changed_graphs = check.changed_graphs
        graph_counts = {graph: self.triple_count(graph) for graph in changed_graphs}
        applied_subject = (
            self._required_iri("applied_revision_iri", applied_revision_iri)
            if applied_revision_iri is not None
            else self._mint_iri("applied-revision")
        )
        source_summary = staged.summary or staged.iri
        source_rationale = staged.rationale or "(No staged rationale recorded.)"
        revision_record = self.record_graph_revision(
            summary=f"Applied staged revision: {source_summary}",
            rationale=(
                f"Applied staged revision {staged.iri}.\n\n"
                f"Original staged rationale:\n{source_rationale}"
            ),
            changed_graphs=changed_graphs,
            revision_type="rc:AppliedStagedRevision",
            revision_iri=applied_subject,
            created_at=created_at,
            created_by=created_by,
            supporting_observations=[
                item.iri for item in staged.supporting_observations
            ],
            supporting_claims=[item.iri for item in staged.supporting_claims],
            supporting_patterns=[item.iri for item in staged.supporting_patterns],
            revision_anchors=[item.iri for item in staged.revision_anchors],
            evidence=[item.iri for item in staged.evidence],
            graph_counts=graph_counts,
            validation_scope=check.validation_scope,
            validation_conforms=bool(check.validation_conforms),
            validation_result_count=check.validation_result_count or 0,
            validation_results=check.validation_results,
        )
        metadata = Graph()
        self._bind_prefixes(metadata)
        metadata.add(
            (
                URIRef(applied_subject),
                URIRef(self.expand_iri("rc:appliesStagedRevision")),
                URIRef(staged.iri),
            )
        )
        extra_triples = self._insert_graph("history", metadata)
        post_apply_recheck_revisions = self._post_apply_recheck_revisions(
            staged_revision_iri=staged.iri,
            changed_graphs=changed_graphs,
        )
        post_apply_recheck_revision_iris = [
            item.iri for item in post_apply_recheck_revisions
        ]
        warnings = self._post_apply_warnings(post_apply_recheck_revision_iris)
        suggested_next_actions = self._post_apply_suggested_next_actions(
            post_apply_recheck_revisions
        )
        return AppliedStagedRevisionRecord(
            applied_revision_iri=applied_subject,
            staged_revision_iri=staged.iri,
            graph="history",
            triples=revision_record.triples + extra_triples,
            changed_graphs=changed_graphs,
            post_apply_recheck_revisions=post_apply_recheck_revisions,
            post_apply_recheck_revision_iris=post_apply_recheck_revision_iris,
            post_apply_recheck_is_partial_queue=True,
            warnings=warnings,
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[
                action.call for action in suggested_next_actions if action.call
            ],
            patches_applied=len(preview.parsed_patches),
            triples_added=triples_added,
            triples_removed=triples_removed,
            validation_scope=check.validation_scope,
            validation_conforms=bool(check.validation_conforms),
            validation_result_count=check.validation_result_count or 0,
            validation_results=check.validation_results,
        )
    @staticmethod
    def _post_apply_warnings(
        post_apply_recheck_revision_iris: list[str],
    ) -> list[str]:
        if not post_apply_recheck_revision_iris:
            return []
        recheck_list = ", ".join(post_apply_recheck_revision_iris)
        return [
            (
                "Applying this staged revision may have made sibling staged "
                "readiness stale. Recheck affected staged revisions before the "
                "next mutation: "
                f"{recheck_list}. post_apply_recheck_revision_iris is the "
                "affected-sibling subset, not the full remaining staged queue; "
                "rerun plan_staged_revision_recovery(current_staged_work_only=True) "
                "before applying another row."
            )
        ]
    def _post_apply_suggested_next_actions(
        self,
        post_apply_recheck_revisions: list[PostApplyRecheckRevision],
    ) -> list[SuggestedNextAction]:
        arguments: dict[str, Any] = {"current_staged_work_only": True}
        actions = [
            SuggestedNextAction(
                action_label="Replan current staged frontier",
                tool_name="plan_staged_revision_recovery",
                mcp_tool_name="doxabase.plan_staged_revision_recovery",
                arguments=arguments,
                reason=(
                    "Post-apply recheck rows are only the affected sibling "
                    "subset. Replan the current staged frontier before deciding "
                    "the next mutation so independent staged work is not dropped."
                ),
                call=self._suggested_call_string(
                    "plan_staged_revision_recovery",
                    arguments,
                ),
            )
        ]
        for recheck in post_apply_recheck_revisions:
            actions.extend(recheck.suggested_next_actions)
        return self._dedupe_suggested_next_actions(actions)
    def _post_apply_recheck_revisions(
        self,
        *,
        staged_revision_iri: str,
        changed_graphs: list[str],
    ) -> list[PostApplyRecheckRevision]:
        if not changed_graphs:
            return []
        data_graphs = self._expand_graphs(["history"])
        staged_revision_type = self.expand_iri("rc:StagedRevision")
        candidate_rows: list[tuple[str, str, str, PostApplyRecheckRevision]] = []
        revision_iris = self._subjects(
            data_graphs,
            str(RDF.type),
            self.expand_iri("rc:GraphRevision"),
        )
        for revision_iri in revision_iris:
            if revision_iri == staged_revision_iri:
                continue
            if (
                self._first_object(data_graphs, revision_iri, "rc:revisionType")
                != staged_revision_type
            ):
                continue
            if not self._objects(data_graphs, revision_iri, "rc:hasGraphPatch"):
                continue
            if (
                self._first_subject(
                    data_graphs,
                    "rc:appliesStagedRevision",
                    revision_iri,
                )
                is not None
            ):
                continue
            if (
                self._current_restage_successor_iri(
                    revision_iri,
                    graphs=data_graphs,
                )
                is not None
            ):
                continue
            candidate_changed_graphs = self._objects(
                data_graphs,
                revision_iri,
                "rc:changedGraph",
            )
            shared_changed_graphs = [
                graph for graph in changed_graphs if graph in candidate_changed_graphs
            ]
            validation_scope = (
                self._first_object(data_graphs, revision_iri, "rc:validationScope")
                or "all"
            )
            validation_dependency_graphs = (
                self._validation_dependency_graphs_for_scope(validation_scope)
            )
            validation_dependency_changed_graphs = [
                graph
                for graph in changed_graphs
                if graph in validation_dependency_graphs
                and graph not in shared_changed_graphs
            ]
            recheck_reasons = [
                *(f"shared_changed_graph:{graph}" for graph in shared_changed_graphs),
                *(
                    f"validation_dependency_graph:{graph}"
                    for graph in validation_dependency_changed_graphs
                ),
            ]
            if not recheck_reasons:
                continue
            apply_check = self.check_staged_revision_apply(revision_iri)
            next_action = self._revision_next_action(
                revision_iri,
                apply_status=apply_check.status,
                apply_decision=apply_check.decision,
                stale_resolution_state=None,
                suggested_next_actions=apply_check.suggested_next_actions,
                staged_validation_status=self._staged_validation_status(
                    conforms=self._bool_object(
                        data_graphs,
                        revision_iri,
                        "rc:validationConforms",
                    ),
                    result_count=self._int_object(
                        data_graphs,
                        revision_iri,
                        "rc:validationResultCount",
                    ),
                ),
            )
            routing_decision = self._staged_apply_check_routing_decision(
                apply_check.decision,
                next_action,
            )
            candidate_rows.append(
                (
                    self._first_object(data_graphs, revision_iri, "rc:createdAt")
                    or "",
                    self._first_object(data_graphs, revision_iri, "rc:summary")
                    or "",
                    revision_iri,
                    PostApplyRecheckRevision(
                        iri=revision_iri,
                        changed_graphs=candidate_changed_graphs,
                        shared_changed_graphs=shared_changed_graphs,
                        recheck_reasons=recheck_reasons,
                        application_status=apply_check.status,
                        decision=apply_check.decision,
                        routing_decision=routing_decision,
                        blocking_reasons=apply_check.blocking_reasons,
                        next_action=next_action,
                        suggested_next_actions=apply_check.suggested_next_actions,
                        suggested_next_calls=apply_check.suggested_next_calls,
                    ),
                )
            )
        candidate_rows.sort(key=lambda row: row[:3], reverse=True)
        return [item for _, _, _, item in candidate_rows]
    def _staged_apply_check_status(
        self,
        *,
        can_apply: bool,
        conflicts: list[str],
        validation_conforms: bool | None,
        has_effective_patch_triples: bool,
    ) -> str:
        if can_apply:
            return "ready"
        if conflicts:
            return "conflict"
        if validation_conforms is False:
            return "validation_failed"
        if validation_conforms is True and not has_effective_patch_triples:
            return "noop"
        return "not_ready"
    def _staged_apply_check_summary(
        self,
        *,
        status: str,
        conflicts: list[str],
        validation_result_count: int | None,
        changed_graphs: list[str],
        patches_checked: int,
        triples_to_add: int,
        triples_to_remove: int,
        already_applied_by: str | None,
        restaged_by: str | None = None,
        current_restaged_by: str | None = None,
        already_effective: bool = False,
    ) -> str:
        graph_text = ", ".join(changed_graphs) if changed_graphs else "(none)"
        if status == "ready":
            return (
                f"Ready to apply {patches_checked} patch(es) across {graph_text}: "
                f"+{triples_to_add} triple(s), -{triples_to_remove} triple(s)."
            )
        if status == "noop":
            return (
                f"Patch replay validates across {graph_text}, but has no "
                f"effective graph delta across {patches_checked} patch(es): "
                f"+{triples_to_add} triple(s), -{triples_to_remove} triple(s)."
            )
        if status == "already_applied":
            return f"Already applied by {already_applied_by}."
        if status == "superseded_by_restage":
            successor_iri = current_restaged_by or restaged_by
            applied_successor_iri = self._applied_event_for_staged_revision(
                successor_iri
            )
            if applied_successor_iri is not None:
                return (
                    "Superseded by a refreshed successor that was applied by "
                    f"{applied_successor_iri}; inspect the applied event."
                )
            return (
                "Superseded by a refreshed successor; inspect the current "
                "successor instead of applying this staged source."
            )
        if status == "conflict":
            first_conflict = conflicts[0] if conflicts else "(unknown conflict)"
            successor_iri = current_restaged_by or restaged_by
            if successor_iri is not None:
                applied_successor_iri = self._applied_event_for_staged_revision(
                    successor_iri
                )
                if applied_successor_iri is not None:
                    return (
                        "Handled by restage; refreshed successor "
                        f"{successor_iri} was applied by {applied_successor_iri}. "
                        "Stale source is still blocked by "
                        f"{len(conflicts)} conflict(s); first conflict: "
                        f"{first_conflict}"
                    )
                return (
                    "Handled by restage; inspect successor "
                    f"{successor_iri}. Stale source is still blocked by "
                    f"{len(conflicts)} conflict(s); first conflict: "
                    f"{first_conflict}"
                )
            if already_effective:
                return (
                    "Already-effective stale source; target graph drift blocks "
                    "raw replay, but the staged patch payload has no current "
                    f"effective delta across {patches_checked} patch(es). First "
                    f"conflict: {first_conflict}"
                )
            return (
                f"Blocked by {len(conflicts)} conflict(s); first conflict: "
                f"{first_conflict}"
            )
        if status == "validation_failed":
            result_count = validation_result_count or 0
            successor_iri = current_restaged_by or restaged_by
            if successor_iri is not None:
                applied_successor_iri = self._applied_event_for_staged_revision(
                    successor_iri
                )
                if applied_successor_iri is not None:
                    return (
                        "Handled by restage; refreshed successor "
                        f"{successor_iri} was applied by {applied_successor_iri}. "
                        "Stale source validation still fails with "
                        f"{result_count} result(s)."
                    )
                return (
                    "Handled by restage; inspect successor "
                    f"{successor_iri}. Stale source validation still fails "
                    f"with {result_count} result(s)."
                )
            return (
                "Patch counts replay cleanly, but preview validation failed with "
                f"{result_count} result(s)."
            )
        return "Not ready to apply; inspect patch checks and validation fields."
    def _staged_apply_check_decision(
        self,
        status: str,
        *,
        blocking_reasons: list[str] | None = None,
        restaged_source_validation_warning: str | None = None,
        restaged_successor_reuses_source_patch_payload: bool = True,
    ) -> str:
        if (
            status == "ready"
            and restaged_source_validation_warning is not None
            and restaged_successor_reuses_source_patch_payload
        ):
            return "inspect_restaged_source_validation_failure"
        if status == "conflict" and blocking_reasons is not None:
            if not self._staged_apply_check_is_restageable_conflict(
                blocking_reasons
            ):
                return "inspect_patch_conflict"
        decisions = {
            "ready": "review_then_apply",
            "noop": "inspect_no_effective_change",
            "already_applied": "inspect_applied_revision",
            "superseded_by_restage": "inspect_current_successor",
            "conflict": "restage_against_current_graph",
            "validation_failed": "inspect_validation_results",
        }
        return decisions.get(status, "inspect_staged_revision")
    def _staged_apply_check_review_recommended(
        self,
        status: str,
        *,
        semantic_risk_level: str = "none",
    ) -> bool:
        if status in {"ready", "conflict"}:
            return True
        if status == "noop":
            return True
        return status == "validation_failed" and semantic_risk_level != "none"
    def _staged_apply_check_validation_skipped_reason(
        self,
        status: str,
    ) -> str | None:
        reasons = {
            "already_applied": "already_applied",
            "conflict": "conflicts_present",
            "not_ready": "not_ready",
        }
        return reasons.get(status)
    def _staged_patch_triple_presence_status_from_apply_check(
        self,
        patch_check: StagedPatchApplyCheck,
    ) -> str | None:
        if patch_check.already_present_triples is None:
            return None
        if patch_check.triple_count is not None:
            patch_triples_checked = patch_check.triple_count
        elif patch_check.already_absent_triples is not None:
            patch_triples_checked = (
                patch_check.already_present_triples
                + patch_check.already_absent_triples
            )
        else:
            return None
        return self._patch_triple_presence_status(
            patch_triples_checked=patch_triples_checked,
            patch_triples_present=patch_check.already_present_triples,
        )
    def _staged_apply_check_blocking_reasons(
        self,
        *,
        status: str,
        conflicts: list[str],
    ) -> list[str]:
        if status == "ready":
            return []
        if status == "noop":
            return ["no_effective_patch_triples"]
        if status == "already_applied":
            return ["already_applied"]
        if status == "superseded_by_restage":
            return ["superseded_by_restage"]
        if status == "conflict":
            reasons = []
            if any(
                "expected" in conflict and "triples before patch" in conflict
                for conflict in conflicts
            ):
                reasons.append("target_count_drift")
            if any(
                "expected" in conflict and "triples after patch" in conflict
                for conflict in conflicts
            ):
                reasons.append("preview_count_mismatch")
            if any(
                "content digest changed since staging" in conflict
                for conflict in conflicts
            ):
                reasons.append("target_digest_drift")
            if not reasons:
                reasons.append("patch_conflict")
            return list(dict.fromkeys(reasons))
        if status == "validation_failed":
            return ["validation_failed"]
        return ["not_ready"]
    def _staged_apply_check_recommended_resolution(
        self,
        *,
        status: str,
        blocking_reasons: list[str],
        suggested_next_actions: list[SuggestedNextAction] | None = None,
        restaged_by: str | None = None,
        current_restaged_by: str | None = None,
        restaged_source_validation_warning: str | None = None,
        restaged_successor_reuses_source_patch_payload: bool = True,
    ) -> str | None:
        if status == "ready" and restaged_source_validation_warning is not None:
            if not restaged_successor_reuses_source_patch_payload:
                return (
                    f"{restaged_source_validation_warning} Inspect the source "
                    "validation diagnostics and the revised successor payload; "
                    "apply after review only if the repair is still desired."
                )
            return (
                f"{restaged_source_validation_warning} Inspect the source "
                "validation diagnostics and stage a repaired or alternative "
                "candidate before applying this restaged successor."
            )
        if status == "ready":
            return (
                "Review the staged revision, impacts, validation preview, and any "
                "judgement panel; apply only if the proposal is still desired."
            )
        if status == "noop":
            return (
                "Patch replay would not change any graph triples. Inspect the "
                "staged revision and current graph state instead of applying a "
                "no-op revision."
            )
        if status == "already_applied":
            return "Inspect the applied revision event; do not apply this staged revision again."
        if status == "superseded_by_restage":
            successor_iri = current_restaged_by or restaged_by
            applied_successor_iri = self._applied_event_for_staged_revision(
                successor_iri
            )
            if applied_successor_iri is not None:
                return (
                    "Inspect the applied revision event "
                    f"'{applied_successor_iri}'; do not apply this superseded "
                    "staged source."
                )
            return (
                "Inspect the current refreshed successor; do not apply this "
                "superseded staged source."
            )
        if status == "conflict" and (current_restaged_by or restaged_by):
            successor_iri = current_restaged_by or restaged_by
            applied_successor_iri = self._applied_event_for_staged_revision(
                successor_iri
            )
            if applied_successor_iri is not None:
                return (
                    "This stale source already has a refreshed successor that "
                    f"was applied by '{applied_successor_iri}'. Inspect the "
                    "applied event instead of restaging the source again."
                )
            return (
                "This stale source already has a refreshed successor. Inspect "
                f"'{successor_iri}' instead of restaging the source again."
            )
        if status == "conflict" and any(
            action.tool_name == "stage_map_assertion_change"
            for action in suggested_next_actions or []
        ):
            return (
                "Exact snapshot drift shows a different current value for the "
                "same single-valued map assertion slot. Stage the suggested "
                "stage_map_assertion_change replacement successor after review "
                "instead of mechanically restaging the stale source patch."
            )
        if status == "conflict" and any(
            action.action_label == "Review ambiguous same-slot conflict"
            for action in suggested_next_actions or []
        ):
            return (
                "Exact snapshot drift shows same-slot map assertion drift, but "
                "the current graph has multiple values for the single-valued "
                "slot. Inspect the current values and stage an explicit repair "
                "or replacement instead of mechanically restaging the stale "
                "source patch."
            )
        if status == "conflict" and any(
            action.action_label == "Draft patch repair plan"
            for action in suggested_next_actions or []
        ):
            return (
                "Patch-level repair planning found a semantic same-slot "
                "subpatch inside a larger stale staged revision. Inspect the "
                "read-only patch_repair_plan and author a complete repaired "
                "successor instead of mechanically restaging the mixed patch "
                "set."
            )
        if status == "conflict" and any(
            action.action_label == "Inspect already-effective stale source"
            for action in suggested_next_actions or []
        ):
            return (
                "The target graph drifted, but the staged patch payload already "
                "has no effective delta in current graph state. Inspect or export "
                "the stale source instead of mechanically restaging it just to "
                "create a no-op successor."
            )
        if (
            "target_count_drift" in blocking_reasons
            and "target_digest_drift" in blocking_reasons
        ):
            return (
                "Restage the proposal against the current graph state; at least "
                "one target graph count and at least one target graph content "
                "digest changed since staging."
            )
        if "target_count_drift" in blocking_reasons:
            return (
                "Restage the proposal against the current graph state; the target "
                "graph count has changed since staging."
            )
        if "target_digest_drift" in blocking_reasons:
            return (
                "Restage the proposal against the current graph state; the target "
                "graph content digest changed since staging even though counts may "
                "still match."
            )
        if "patch_conflict" in blocking_reasons:
            return (
                "Inspect patch_checks[].conflict and stage a repaired or "
                "alternative candidate; restage only handles count/digest drift."
            )
        if status == "conflict":
            return (
                "Inspect patch checks and stage a repaired or alternative "
                "candidate unless the conflict is count/digest drift."
            )
        if status == "validation_failed":
            if current_restaged_by or restaged_by:
                successor_iri = current_restaged_by or restaged_by
                applied_successor_iri = self._applied_event_for_staged_revision(
                    successor_iri
                )
                if applied_successor_iri is not None:
                    return (
                        "This failed staged source already has a refreshed "
                        "successor that was applied by "
                        f"'{applied_successor_iri}'. Preserve this row for "
                        "validation diagnostics and inspect the applied event "
                        "instead of repairing the old source again."
                    )
                return (
                    "This failed staged source already has a refreshed "
                    f"successor '{successor_iri}'. Preserve this row for "
                    "validation diagnostics and inspect the current successor "
                    "instead of repairing the old source again."
                )
            return (
                "Inspect validation_results and stage a repaired or alternative "
                "candidate. If validation failed after restaging an overlapping "
                "single assertion, repair with a removal+addition patch or "
                "stage_map_assertion_change replacement instead of restaging the "
                "same patch again."
            )
        return "Inspect staged revision details before taking action."
    def _staged_apply_check_next_actions(
        self,
        staged_revision_iri: str,
        *,
        status: str,
        staged: StagedGraphRevisionDescription | None = None,
        semantic_risk_level: str = "none",
        blocking_reasons: list[str] | None = None,
        already_applied_by: str | None,
        restaged_by: str | None,
        current_restaged_by: str | None,
        patch_checks: list[StagedPatchApplyCheck] | None = None,
        patch_repair_plan: list[StagedPatchRepairPlan] | None = None,
        snapshot_drifts: list[StagedGraphSnapshotDrift] | None = None,
        validation_scope: str | None = None,
        restaged_source_validation_warning: str | None = None,
        restaged_successor_reuses_source_patch_payload: bool = True,
    ) -> list[SuggestedNextAction]:
        actions: list[SuggestedNextAction] = []

        def add_action(
            tool_name: str,
            arguments: dict[str, Any],
            reason: str,
            action_label: str | None = None,
        ) -> None:
            if tool_name in {"export_staged_revision", "export_staged_revisions"}:
                arguments = {**arguments, "fail_on_sensitive": True}
                reason = (
                    f"{reason} The suggested call blocks if scanner-matching "
                    "content appears before export."
                )
            actions.append(
                self._effect_annotated_suggested_next_action(
                    action_label=action_label
                    or self._suggested_action_label(tool_name),
                    tool_name=tool_name,
                    arguments=arguments,
                    reason=reason,
                )
            )

        def add_applied_successor_actions(
            successor_iri: str | None,
        ) -> bool:
            applied_successor_iri = self._applied_event_for_staged_revision(
                successor_iri
            )
            if applied_successor_iri is None:
                return False
            add_action(
                "describe_graph_revision",
                {"iri": applied_successor_iri},
                (
                    "The refreshed successor has already been applied; inspect "
                    "the applied event instead of stopping at the staged source."
                ),
                action_label="Inspect applied restaged successor",
            )
            add_action(
                "describe_applied_revision_diff",
                {"iri": applied_successor_iri},
                (
                    "Inspect the applied diff for the refreshed successor when "
                    "exact before/after graph changes matter."
                ),
                action_label="Inspect applied successor diff",
            )
            return True

        if (
            status == "ready"
            and restaged_source_validation_warning is not None
            and restaged_successor_reuses_source_patch_payload
        ):
            add_action(
                "describe_staged_revision",
                {"iri": staged_revision_iri},
                (
                    f"{restaged_source_validation_warning} Inspect the "
                    "restaged successor and its source validation diagnostics "
                    "before deciding whether a repaired candidate is needed."
                ),
                action_label="Inspect restaged validation history",
            )
            add_action(
                "export_staged_revision",
                {
                    "iri": staged_revision_iri,
                    "path": self._suggested_review_export_path(
                        "staged-revision-restaged-validation-history",
                        [staged_revision_iri],
                    ),
                },
                (
                    "Write a Markdown review bundle that preserves the current "
                    "ready check alongside the source validation-failure history."
                ),
                action_label="Export restaged validation bundle",
            )
        elif status == "ready":
            alternative_gate = staged.alternative_gate if staged is not None else None
            alternative_semantic_review_required = (
                alternative_gate is not None
                and alternative_gate.semantic_review_required
            )
            semantic_review_required = (
                semantic_risk_level in {"attention", "high"}
                or alternative_semantic_review_required
            )
            if restaged_source_validation_warning is not None:
                review_reason = (
                    f"{restaged_source_validation_warning} Review the revised "
                    "successor payload, validation preview, impacts, support, "
                    "and any judgement panel before deciding to apply."
                )
                review_label = "Review repaired successor"
                export_slug = "staged-revision-repaired-successor"
                export_reason = (
                    "Write a Markdown review bundle that preserves the source "
                    "validation failure and the current ready repaired successor."
                )
                export_label = "Export repaired successor bundle"
            else:
                review_reason = (
                    "Review patches, validation, impacts, support, and any "
                    "judgement panel before deciding to apply."
                )
                review_label = "Review staged revision"
                export_slug = "staged-revision-review"
                export_reason = (
                    "Write a Markdown review bundle before applying if review is needed."
                )
                export_label = "Export review bundle"
            if (
                alternative_semantic_review_required
                and alternative_gate is not None
                and alternative_gate.applied_source_iri is not None
            ):
                semantic_review_note = (
                    " This row is alternative to already-applied staged source "
                    f"'{alternative_gate.applied_source_iri}'; inspect that "
                    "source before making both alternatives durable."
                )
                if alternative_gate.applied_revision_iri is not None:
                    semantic_review_note += (
                        " Applied revision "
                        f"'{alternative_gate.applied_revision_iri}' records "
                        "the durable event."
                    )
                review_reason += semantic_review_note
                export_reason += (
                    " Include the semantic alternative gate and applied-source "
                    "context in the review bundle."
                )
                if restaged_source_validation_warning is None:
                    review_label = "Review semantic alternative"
                    export_slug = "staged-revision-semantic-alternative-review"
                    export_label = "Export semantic alternative bundle"
            if (
                alternative_semantic_review_required
                and alternative_gate is not None
                and alternative_gate.applied_source_iri is not None
            ):
                apply_reason = (
                    "Apply this staged revision only after semantic review "
                    "confirms the alternative remains desired alongside the "
                    "already-applied staged source "
                    f"'{alternative_gate.applied_source_iri}'."
                )
                if alternative_gate.applied_revision_iri is not None:
                    apply_reason += (
                        " Inspect applied revision "
                        f"'{alternative_gate.applied_revision_iri}' before "
                        "making both alternatives durable."
                    )
            elif semantic_review_required:
                apply_reason = (
                    "Apply this staged revision only after semantic review "
                    "confirms the proposal is still desired."
                )
            else:
                apply_reason = (
                    "Apply this staged revision after review confirms the "
                    "proposal is still desired."
                )
            apply_label = (
                "Apply only after semantic review"
                if semantic_review_required
                else "Apply after review"
            )
            add_action(
                "describe_staged_revision",
                {"iri": staged_revision_iri},
                review_reason,
                action_label=review_label,
            )
            add_action(
                "export_staged_revision",
                {
                    "iri": staged_revision_iri,
                    "path": self._suggested_review_export_path(
                        export_slug,
                        [staged_revision_iri],
                    ),
                },
                export_reason,
                action_label=export_label,
            )
            add_action(
                "apply_staged_revision",
                {"iri": staged_revision_iri},
                apply_reason,
                action_label=apply_label,
            )
        elif status == "superseded_by_restage":
            successor_iri = current_restaged_by or restaged_by
            if not add_applied_successor_actions(successor_iri):
                add_action(
                    "describe_staged_revision",
                    {"iri": successor_iri or staged_revision_iri},
                    (
                        "This staged source already has a refreshed successor; "
                        "inspect the current successor instead of applying this row."
                    ),
                    action_label="Inspect current refreshed successor",
                )
        elif status == "noop":
            add_action(
                "describe_staged_revision",
                {"iri": staged_revision_iri},
                (
                    "Inspect the staged revision and current graph state; replay "
                    "validates but would not change graph triples."
                ),
                action_label="Inspect no-op revision",
            )
            add_action(
                "export_staged_revision",
                {
                    "iri": staged_revision_iri,
                    "path": self._suggested_review_export_path(
                        "staged-revision-noop",
                        [staged_revision_iri],
                    ),
                },
                "Write a Markdown review bundle before deciding whether to replace it.",
                action_label="Export no-op bundle",
            )
        elif status == "already_applied" and already_applied_by is not None:
            add_action(
                "describe_graph_revision",
                {"iri": already_applied_by},
                "Inspect the applied revision event instead of applying again.",
                action_label="Inspect applied event",
            )
            add_action(
                "describe_applied_revision_diff",
                {"iri": already_applied_by},
                (
                    "Inspect stored before/after graph snapshot counts and, when "
                    "needed, exact changed triples for the applied event."
                ),
                action_label="Inspect applied diff",
            )
        elif status == "conflict":
            is_restageable_conflict = (
                self._staged_apply_check_is_restageable_conflict(
                    blocking_reasons or []
                )
            )
            staged_validation_failed = (
                staged is not None and staged.validation_conforms is False
            )
            already_effective_stale = (
                is_restageable_conflict
                and self._patch_checks_have_no_effective_delta(patch_checks or [])
            )
            applied_successor_actions_added = False
            if restaged_by is not None:
                successor_iri = current_restaged_by or restaged_by
                applied_successor_actions_added = add_applied_successor_actions(
                    successor_iri
                )
                review_reason = (
                    "Inspect this stale source as prior context, then follow the "
                    f"current refreshed successor '{successor_iri}'."
                )
                review_label = "Inspect handled stale source"
                export_slug = "staged-revision-handled-stale"
                export_reason = (
                    "Write a review bundle that captures the handled stale source "
                    "and points at its refreshed successor."
                )
                export_label = "Export handled stale bundle"
            elif already_effective_stale:
                review_reason = (
                    "Review the stale source and current graph state; the "
                    "stored patch payload already has no effective delta, so "
                    "a mechanical restage would only create a no-op successor."
                )
                review_label = "Inspect already-effective stale source"
                export_slug = "staged-revision-already-effective"
                export_reason = (
                    "Write a review bundle that captures the stale no-effective "
                    "proposal and current patch-triple presence."
                )
                export_label = "Export already-effective stale bundle"
            elif is_restageable_conflict and staged_validation_failed:
                review_reason = (
                    "Inspect the staged-time validation diagnostics before "
                    "deciding how to repair this stale proposal; a mechanical "
                    "restage may only create another repair candidate."
                )
                review_label = "Review staged validation failure"
                export_slug = "staged-revision-validation-conflict"
                export_reason = (
                    "Write a review bundle that captures the stale proposal, "
                    "current conflict, and stored validation diagnostics."
                )
                export_label = "Export validation conflict bundle"
            elif is_restageable_conflict:
                review_reason = (
                    "Review the original patch payloads, count previews, "
                    "impacts, and support before deciding whether to restage "
                    "against current graph state."
                )
                review_label = "Review stale source"
                export_slug = "staged-revision-conflict"
                export_reason = (
                    "Write a review bundle that captures the blocked staged proposal."
                )
                export_label = "Export conflict bundle"
            else:
                review_reason = (
                    "Inspect the stored patch conflict, then stage a repaired "
                    "or alternative candidate instead of restaging this row."
                )
                review_label = "Review patch conflict"
                export_slug = "staged-revision-patch-conflict"
                export_reason = (
                    "Write a review bundle that captures the blocked staged proposal."
                )
                export_label = "Export conflict bundle"
            add_action(
                "describe_staged_revision",
                {"iri": staged_revision_iri, "include_current_apply_check": True},
                review_reason,
                action_label=review_label,
            )
            add_action(
                "export_staged_revision",
                {
                    "iri": staged_revision_iri,
                    "path": self._suggested_review_export_path(
                        export_slug,
                        [staged_revision_iri],
                    ),
                },
                export_reason,
                action_label=export_label,
            )
            if is_restageable_conflict and any(
                not drift.exact_changed_triples_available
                for drift in snapshot_drifts or []
            ) and not already_effective_stale and restaged_by is None:
                add_action(
                    "import_revision_snapshots",
                    {
                        "path": "/tmp/revision-snapshots.json",
                        "path_is_placeholder": True,
                    },
                    (
                        "Exact drift triples are unavailable for one or more "
                        "changed graphs. If this capsule came from an RDF "
                        "handoff, import the companion revision snapshot JSON "
                        "before deciding whether the stale patch should be "
                        "restaged."
                    ),
                    action_label="Import snapshot bundle if available",
                )
            same_slot_replacement_action = (
                self._staged_same_slot_replacement_action(
                    staged,
                    patch_checks=patch_checks or [],
                    snapshot_drifts=snapshot_drifts or [],
                    validation_scope=validation_scope,
                )
                if is_restageable_conflict
                and restaged_by is None
                and not already_effective_stale
                else None
            )
            if same_slot_replacement_action is not None:
                actions.append(same_slot_replacement_action)
            ambiguous_same_slot_review_action = None
            if same_slot_replacement_action is None:
                ambiguous_same_slot_review_action = (
                    self._staged_ambiguous_same_slot_review_action(
                        staged,
                        patch_checks=patch_checks or [],
                        snapshot_drifts=snapshot_drifts or [],
                    )
                )
            if ambiguous_same_slot_review_action is not None:
                actions.append(ambiguous_same_slot_review_action)
            patch_repair_plan_action = None
            if (
                same_slot_replacement_action is None
                and ambiguous_same_slot_review_action is None
                and self._staged_patch_repair_plan_has_semantic_repair(
                    patch_repair_plan
                )
            ):
                patch_repair_plan_action = (
                    self._staged_patch_repair_plan_action(
                        staged_revision_iri,
                        validation_scope=validation_scope,
                    )
                )
                actions.append(patch_repair_plan_action)
            if (
                restaged_by is None
                and is_restageable_conflict
                and staged_validation_failed
            ):
                draft_arguments: dict[str, Any] = {"iri": staged_revision_iri}
                if validation_scope is not None:
                    draft_arguments["validation_scope"] = validation_scope
                add_action(
                    "draft_staged_revision_rebase",
                    draft_arguments,
                    (
                        "Draft a repair/rebase plan from the stored validation "
                        "failure before creating another restaged successor."
                    ),
                    action_label="Draft repair plan",
                )
            elif (
                restaged_by is None
                and is_restageable_conflict
                and not already_effective_stale
                and same_slot_replacement_action is None
                and ambiguous_same_slot_review_action is None
                and patch_repair_plan_action is None
            ):
                add_action(
                    "restage_staged_revision",
                    {"iri": staged_revision_iri},
                    (
                        "Create a refreshed staged revision against current graph "
                        "counts if review confirms the patch intent is still desired."
                    ),
                    action_label="Restage stale source",
                )
            elif restaged_by is not None:
                successor_iri = current_restaged_by or restaged_by
                if not applied_successor_actions_added:
                    add_action(
                        "describe_staged_revision",
                        {"iri": successor_iri},
                        (
                            "Inspect the current refreshed successor instead of "
                            "restaging this stale source again."
                        ),
                        action_label="Inspect current refreshed successor",
                    )
        elif status == "validation_failed" and restaged_by is not None:
            successor_iri = current_restaged_by or restaged_by
            applied_successor_actions_added = add_applied_successor_actions(
                successor_iri
            )
            if not applied_successor_actions_added:
                add_action(
                    "describe_staged_revision",
                    {"iri": successor_iri},
                    (
                        "This failed staged source already has a refreshed "
                        "successor. Preserve this row's validation_results for "
                        "diagnostics, then inspect the current successor instead "
                        "of repairing the old source again."
                    ),
                    action_label="Inspect current refreshed successor",
                )
            add_action(
                "export_staged_revision",
                {
                    "iri": staged_revision_iri,
                    "path": self._suggested_review_export_path(
                        "staged-revision-handled-validation-failure",
                        [staged_revision_iri],
                    ),
                },
                (
                    "Write a Markdown diagnostic bundle for this handled failed "
                    "source while preserving the pointer to its current successor."
                ),
                action_label="Export handled validation bundle",
            )
        elif status == "validation_failed":
            draft_arguments: dict[str, Any] = {"iri": staged_revision_iri}
            if validation_scope is not None:
                draft_arguments["validation_scope"] = validation_scope
            add_action(
                "draft_staged_revision_rebase",
                draft_arguments,
                (
                    "Draft a read-only repair/rebase plan from this validation "
                    "failure before hand-authoring a repaired or alternative "
                    "successor."
                ),
                action_label="Draft repair plan",
            )
            add_action(
                "describe_staged_revision",
                {"iri": staged_revision_iri},
                (
                    "Inspect structured validation_results, then stage a repaired "
                    "or alternative candidate while preserving this failed revision "
                    "for comparison. For overlapping single-assertion failures, "
                    "repair with removal+addition or stage_map_assertion_change "
                    "replacement instead of restaging the same patch again."
                ),
                action_label="Inspect validation failure",
            )
            add_action(
                "export_staged_revision",
                {
                    "iri": staged_revision_iri,
                    "path": self._suggested_review_export_path(
                        "staged-revision-validation-failed",
                        [staged_revision_iri],
                    ),
                },
                (
                    "Write a review bundle with validation diagnostics before "
                    "staging a repaired candidate from validation_results."
                ),
                action_label="Export validation bundle",
            )
        else:
            add_action(
                "describe_staged_revision",
                {"iri": staged_revision_iri},
                "Inspect staged revision details to understand why apply is not ready.",
                action_label="Inspect staged revision",
            )
        return actions
    @staticmethod
    def _staged_apply_check_routing_decision(
        decision: str | None,
        next_action: RevisionNextAction | None,
    ) -> str | None:
        if next_action is None:
            return decision
        if next_action.tool_name == "stage_map_assertion_change":
            return "stage_same_slot_replacement"
        return next_action.action_type or decision
    def _staged_revision_apply_check_for_export(
        self,
        description: StagedGraphRevisionDescription,
    ) -> tuple[StagedRevisionApplyCheck | None, str | None]:
        try:
            return self.check_staged_revision_apply(description.iri), None
        except DoxaBaseError as exc:
            return None, str(exc)
    def _staged_revisions_post_apply_recheck_revision_iris(
        self,
        summaries: list[StagedGraphRevisionExportSummary],
    ) -> list[str]:
        candidates = [
            summary
            for summary in summaries
            if summary.apply_status in {"ready", "noop"} and summary.changed_graphs
        ]
        graphs_needing_recheck: set[str] = set()
        for graph in {graph for summary in candidates for graph in summary.changed_graphs}:
            graph_candidates = [
                summary for summary in candidates if graph in summary.changed_graphs
            ]
            if len(graph_candidates) <= 1:
                continue
            if any(
                summary.apply_decision == "review_then_apply"
                for summary in graph_candidates
            ):
                graphs_needing_recheck.add(graph)
        if not graphs_needing_recheck:
            return []
        return [
            summary.revision_iri
            for summary in candidates
            if any(graph in graphs_needing_recheck for graph in summary.changed_graphs)
        ]
    def _suggested_action_label(self, tool_name: str) -> str:
        labels = {
            "apply_staged_revision": "Apply staged revision",
            "describe_assertion_support": "Inspect assertion support",
            "describe_context_slice": "Load context slice",
            "describe_dataset": "Inspect dataset",
            "describe_graph_revision": "Inspect graph revision",
            "describe_resource": "Inspect resource",
            "describe_staged_revision": "Inspect staged revision",
            "export_staged_revision": "Export staged revision",
            "restage_staged_revision": "Restage staged revision",
            "search": "Search graph",
        }
        return labels.get(tool_name, tool_name.replace("_", " ").title())
    def _staged_apply_check_markdown(
        self,
        check: StagedRevisionApplyCheck | None,
        *,
        apply_check_error: str | None,
        alternative_to: ResourceSummary | None,
    ) -> list[str]:
        lines = ["## Current Apply Check", ""]
        if check is None:
            lines.append("- Status: unavailable")
            if apply_check_error:
                lines.append(f"- Error: {apply_check_error}")
            return lines
        delta_label = (
            "Replayable triple delta" if check.conflicts else "Triple delta"
        )
        delta_suffix = " (conflicted patches excluded)" if check.conflicts else ""

        lines.extend(
            [
                f"- Status: {check.status}",
                f"- Decision: {check.decision}",
                f"- Mechanically can apply: {check.can_apply}",
                f"- Review recommended: {check.review_recommended}",
                f"- Semantic risk: {check.semantic_risk_level}",
                f"- Summary: {check.summary}",
                f"- Changed graphs: {', '.join(check.changed_graphs) or '(none)'}",
                f"- Patches checked: {check.patches_checked}",
                (
                    f"- {delta_label}: +{check.triples_to_add}, "
                    f"-{check.triples_to_remove}{delta_suffix}"
                ),
            ]
        )
        if check.conflicts:
            lines.append(
                "- Patch replay note: conflicted patch triples are shown in "
                "Patch Replay; replayable delta excludes them."
            )
        if check.semantic_risk_reasons:
            lines.append("- Semantic risk reasons:")
            lines.extend(f"  - {reason}" for reason in check.semantic_risk_reasons)
        if check.blocking_reasons:
            lines.append(f"- Blocking reasons: {', '.join(check.blocking_reasons)}")
        if check.recommended_resolution:
            lines.append(f"- Recommended resolution: {check.recommended_resolution}")
        if check.already_applied_by:
            lines.append(f"- Already applied by: `{check.already_applied_by}`")
        validation_result_count = (
            "unknown"
            if check.validation_result_count is None
            else str(check.validation_result_count)
        )
        lines.append(
            f"- Validation: {check.validation_scope or 'unknown'} "
            f"conforms={check.validation_conforms} "
            f"results={validation_result_count}"
        )
        if check.validation_skipped_reason:
            lines.append(f"- Validation skipped: {check.validation_skipped_reason}")
        if check.alternative_gate.semantic_review_required:
            lines.append(
                "- Alternative gate: semantic review required; "
                f"{check.alternative_gate.note}"
            )
            if check.alternative_gate.applied_source_iri is not None:
                lines.append(
                    "- Applied alternative source: "
                    f"`{check.alternative_gate.applied_source_iri}`"
                )
            if check.alternative_gate.applied_revision_iri is not None:
                lines.append(
                    "- Applied alternative event: "
                    f"`{check.alternative_gate.applied_revision_iri}`"
                )
        elif alternative_to is not None and check.can_apply:
            label = alternative_to.label or alternative_to.iri
            lines.append(
                "- Alternative caution: this staged revision is marked as an "
                f"alternative to {label} (`{alternative_to.iri}`). Compare the "
                "related alternatives before applying one framing."
            )

        if check.conflicts:
            lines.extend(["", "### Conflicts", ""])
            lines.extend(f"- {conflict}" for conflict in check.conflicts)

        if check.count_drifts:
            lines.extend(
                [
                    "",
                    "### Count Drift",
                    "",
                    (
                        "| Patch | Sequence | Graph | Expected before | "
                        "Count basis | Expected basis | Current | Delta | Patch triples | "
                        "Status | Note |"
                    ),
                    "|---|---:|---|---:|---|---|---:|---:|---|---|---|",
                ]
            )
            for drift in check.count_drifts:
                if drift.patch_triples_checked is None:
                    patch_triples = "unknown"
                else:
                    present = drift.patch_triples_currently_present
                    absent = drift.patch_triples_currently_absent
                    patch_triples = (
                        f"{present}/{drift.patch_triples_checked} present"
                        if present is not None
                        else f"{drift.patch_triples_checked} checked"
                    )
                    if absent is not None:
                        patch_triples = f"{patch_triples}; {absent} absent"
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            self._markdown_table_cell(drift.patch_iri),
                            (
                                str(drift.patch_sequence_index)
                                if drift.patch_sequence_index is not None
                                else "unknown"
                            ),
                            self._markdown_table_cell(drift.target_graph),
                            str(drift.expected_before_triple_count),
                            self._markdown_table_cell(drift.count_basis),
                            self._markdown_table_cell(
                                drift.expected_before_basis
                            ),
                            str(drift.current_triple_count),
                            str(drift.delta),
                            self._markdown_table_cell(patch_triples),
                            self._markdown_table_cell(
                                drift.patch_triple_status or "unknown"
                            ),
                            self._markdown_table_cell(drift.note),
                        ]
                    )
                    + " |"
                )

        if check.snapshot_drifts:
            lines.extend(
                [
                    "",
                    "### Snapshot Drift",
                    "",
                    (
                        "| Graph | Snapshot stored count | Current count | "
                        "Snapshot digest | Current digest | Exact changed triples | "
                        "Added since snapshot | Removed since snapshot | "
                        "Drift relevance | Patch subject overlap | "
                        "Patch predicate overlap | Patch object overlap | "
                        "Revision anchor overlap | Note |"
                    ),
                    "|---|---:|---:|---|---|---|---:|---:|---|---|---|---|---|---|",
                ]
            )
            for drift in check.snapshot_drifts:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            self._markdown_table_cell(drift.graph_role),
                            str(drift.snapshot_triple_count),
                            str(drift.current_triple_count),
                            self._markdown_table_cell(
                                drift.snapshot_content_digest
                            ),
                            self._markdown_table_cell(drift.current_content_digest),
                            str(drift.exact_changed_triples_available),
                            self._markdown_optional_count(
                                drift.triples_added_since_snapshot_count
                            ),
                            self._markdown_optional_count(
                                drift.triples_removed_since_snapshot_count
                            ),
                            self._markdown_table_cell(drift.drift_relevance),
                            self._markdown_table_cell(
                                ", ".join(drift.patch_overlap_subjects)
                                or "(none)"
                            ),
                            self._markdown_table_cell(
                                ", ".join(drift.patch_overlap_predicates)
                                or "(none)"
                            ),
                            self._markdown_table_cell(
                                ", ".join(drift.patch_overlap_objects)
                                or "(none)"
                            ),
                            self._markdown_table_cell(
                                ", ".join(drift.revision_anchor_overlap)
                                or "(none)"
                            ),
                            self._markdown_table_cell(drift.note),
                        ]
                    )
                    + " |"
                )
            for drift in check.snapshot_drifts:
                lines.extend(self._snapshot_drift_changed_resources_markdown(drift))
            for drift in check.snapshot_drifts:
                lines.extend(self._snapshot_drift_triples_markdown(drift))

        if check.patch_checks:
            lines.extend(
                [
                    "",
                    "### Patch Replay",
                    "",
                    (
                        "| Patch | Graph | Operation | Recorded preview before | "
                        "Count basis | Current preview before | Recorded preview after | Current preview | "
                        "Effective + | Effective - | Already present | Already absent | "
                        "Mechanically can apply | Conflict |"
                    ),
                    "|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---|---|",
                ]
            )
            for patch in check.patch_checks:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            self._markdown_table_cell(patch.patch_iri),
                            self._markdown_table_cell(
                                patch.target_graph or "(unknown)"
                            ),
                            self._markdown_table_cell(
                                patch.operation_label
                                or patch.operation
                                or "(unknown)"
                            ),
                            self._markdown_optional_count(patch.before_triple_count),
                            self._markdown_table_cell(
                                patch.count_basis or "unknown"
                            ),
                            self._markdown_optional_count(patch.current_triple_count),
                            self._markdown_optional_count(patch.after_triple_count),
                            self._markdown_optional_count(patch.preview_triple_count),
                            self._markdown_optional_count(
                                patch.effective_triples_to_add
                            ),
                            self._markdown_optional_count(
                                patch.effective_triples_to_remove
                            ),
                            self._markdown_optional_count(
                                patch.already_present_triples
                            ),
                            self._markdown_optional_count(
                                patch.already_absent_triples
                            ),
                            str(patch.can_apply),
                            self._markdown_table_cell(patch.conflict or ""),
                        ]
                    )
                    + " |"
                )

        if check.suggested_next_actions:
            lines.extend(["", "### Suggested Next Calls", ""])
            for action in check.suggested_next_actions[:5]:
                note = ""
                if (
                    alternative_to is not None
                    and action.tool_name == "apply_staged_revision"
                ):
                    note = " (only after comparing alternatives)"
                lines.append(
                    f"- **{action.action_label}:** `{action.call}`{note}"
                )
                lines.append(f"  {action.reason}")
        return lines
    def _staged_apply_check_validation_cell(
        self,
        check: StagedRevisionApplyCheck | None,
        *,
        apply_check_error: str | None,
    ) -> str:
        if check is None:
            return f"unavailable: {apply_check_error or 'unknown'}"
        if check.validation_skipped_reason:
            return f"skipped: {check.validation_skipped_reason}"
        if check.validation_conforms is None:
            return "unknown"
        result_count = (
            "unknown"
            if check.validation_result_count is None
            else str(check.validation_result_count)
        )
        return f"{check.validation_conforms} ({result_count} result(s))"
    def _markdown_optional_count(self, value: int | None) -> str:
        if value is None:
            return ""
        return str(value)
