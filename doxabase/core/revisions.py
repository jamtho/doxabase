"""Revision metadata, graph versions, lineage, snapshots.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via RevisionsMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class RevisionsMixin:
    def describe_graph_revision(
        self,
        iri: str,
        *,
        graph: str | None = "history",
    ) -> GraphRevisionDescription:
        revision_iri = self.expand_iri(iri)
        data_graphs = self._expand_graphs([graph] if graph else None)
        lookup_graphs = self._lookup_graphs(data_graphs)
        if not self._subject_exists(revision_iri, data_graphs):
            graph_label = graph if graph is not None else "all graphs"
            hint = self._missing_revision_snapshot_storage_hint(revision_iri)
            raise DoxaBaseError(
                f"Graph revision '{iri}' was not found in {graph_label}{hint}"
            )
        if self.expand_iri("rc:GraphRevision") not in self._types_from_graphs(
            data_graphs,
            revision_iri,
        ):
            raise DoxaBaseError(f"Resource '{iri}' is not an rc:GraphRevision")

        revision_type = self._first_object(data_graphs, revision_iri, "rc:revisionType")
        all_lookup_graphs = self._lookup_graphs(self._expand_graphs(["all"]))
        snapshots = self._graph_revision_snapshots(revision_iri, data_graphs)
        included_graphs = self._objects(data_graphs, revision_iri, "rc:includedGraph")
        if not included_graphs:
            included_graphs = [snapshot.graph_role for snapshot in snapshots]
        applies_staged_revision = self._first_object(
            data_graphs,
            revision_iri,
            "rc:appliesStagedRevision",
        )
        resolves_staged_revision = self._first_object(
            data_graphs,
            revision_iri,
            "rc:resolvesStagedRevision",
        )
        staged_review_decision = self._first_object(
            data_graphs,
            revision_iri,
            "rc:stagedRevisionReviewDecision",
        )
        patch_iris = self._objects(data_graphs, revision_iri, "rc:hasGraphPatch")
        patches = [
            self._describe_staged_graph_patch(patch_iri, data_graphs)
            for patch_iri in patch_iris
        ]
        patches.sort(key=self._staged_patch_sort_key)
        record_kind = self._graph_revision_record_kind(
            revision_type,
            has_patch_payload=bool(patch_iris),
            applies_staged_revision=applies_staged_revision,
        )
        snapshot_evidence = self._revision_snapshot_evidence_status(
            revision_iri,
            data_graphs,
        )
        suggested_next_actions = (
            self._applied_revision_event_suggested_actions(revision_iri)
            if applies_staged_revision is not None
            else []
        )
        suggested_next_actions = self._with_revision_snapshot_evidence_actions(
            suggested_next_actions,
            snapshot_evidence,
        )

        return GraphRevisionDescription(
            iri=revision_iri,
            graph=graph,
            label=self._display_label_from_graphs(lookup_graphs, revision_iri),
            summary=self._first_object(data_graphs, revision_iri, "rc:summary"),
            record_kind=record_kind,
            revision_type=revision_type,
            revision_type_label=(
                self._label_from_graphs(self._expand_graphs(["ontology"]), revision_type)
                if revision_type is not None
                else None
            ),
            rationale=self._first_object(data_graphs, revision_iri, "rc:revisionRationale"),
            changed_graphs=self._objects(data_graphs, revision_iri, "rc:changedGraph"),
            included_graphs=included_graphs,
            created_at=self._first_object(data_graphs, revision_iri, "rc:createdAt"),
            created_by=self._first_object(data_graphs, revision_iri, "rc:createdBy"),
            export_path=self._first_object(data_graphs, revision_iri, "rc:exportPath"),
            applies_staged_revision=applies_staged_revision,
            resolves_staged_revision=resolves_staged_revision,
            staged_review_decision=staged_review_decision,
            staged_review_decision_label=self._label_for_resource(
                staged_review_decision
            ),
            applied_source=(
                self._applied_staged_revision_source_summary(
                    applies_staged_revision
                )
                if applies_staged_revision is not None
                else None
            ),
            validation_scope=self._first_object(
                data_graphs,
                revision_iri,
                "rc:validationScope",
            ),
            validation_conforms=self._bool_object(
                data_graphs,
                revision_iri,
                "rc:validationConforms",
            ),
            validation_result_count=self._int_object(
                data_graphs,
                revision_iri,
                "rc:validationResultCount",
            ),
            validation_results=self._graph_revision_validation_results(
                revision_iri,
                data_graphs,
                patches=patches,
            ),
            graph_snapshots=snapshots,
            snapshot_evidence=snapshot_evidence,
            supporting_observations=self._resource_summaries(
                all_lookup_graphs,
                self._objects(
                    data_graphs,
                    revision_iri,
                    "rc:revisionSupportingObservation",
                ),
            ),
            supporting_claims=self._resource_summaries(
                all_lookup_graphs,
                self._objects(data_graphs, revision_iri, "rc:revisionSupportingClaim"),
            ),
            supporting_patterns=self._resource_summaries(
                all_lookup_graphs,
                self._objects(data_graphs, revision_iri, "rc:revisionSupportingPattern"),
            ),
            revision_anchors=self._resource_summaries(
                all_lookup_graphs,
                self._objects(data_graphs, revision_iri, "rc:revisionAnchor"),
            ),
            evidence=self._resource_summaries(
                all_lookup_graphs,
                self._objects(data_graphs, revision_iri, "rc:evidence"),
            ),
            suggested_next_actions=suggested_next_actions,
        )
    @staticmethod
    def _revision_next_action_from_suggested_action(
        action: SuggestedNextAction,
        *,
        action_type: str,
        queue: str,
        source: str,
    ) -> RevisionNextAction:
        return RevisionNextAction(
            action_type=action_type,
            queue=queue,
            action_label=action.tool.removeprefix("doxabase."),
            tool_name=action.tool.removeprefix("doxabase."),
            mcp_tool_name=action.tool,
            arguments=action.args,
            reason=action.reason,
            call=None,
            source=source,
        )
    def list_graph_revisions(
        self,
        *,
        revision_type: str | None = None,
        graph: str | None = "history",
        include_apply_checks: bool = False,
        drift_detail: TypingLiteral["summary", "exact"] = "summary",
        record_kind: str | None = None,
        application_status: str | None = None,
        staged_validation_status: str | None = None,
        stale_resolution_state: str | None = None,
        current_staged_work_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> GraphRevisionList:
        if drift_detail not in {"summary", "exact"}:
            raise DoxaBaseError("drift_detail must be 'summary' or 'exact'")
        self._ensure_non_negative("limit", limit)
        self._ensure_non_negative("offset", offset)
        record_kind_filter = record_kind
        application_status_filter = application_status
        staged_validation_status_filter = staged_validation_status
        if staged_validation_status_filter not in {
            None,
            "conforms",
            "failed",
            "not_recorded",
        }:
            raise DoxaBaseError(
                "staged_validation_status must be 'conforms', 'failed', or "
                "'not_recorded'"
            )
        stale_resolution_state_filter = stale_resolution_state
        include_apply_checks = include_apply_checks or (
            application_status_filter is not None
            or stale_resolution_state_filter is not None
            or current_staged_work_only
        )
        data_graphs = self._expand_graphs([graph] if graph else None)
        ontology_graphs = self._expand_graphs(["ontology"])
        revision_type_filter = (
            self.expand_iri(revision_type) if revision_type is not None else None
        )
        revision_iris = self._subjects(
            data_graphs,
            str(RDF.type),
            self.expand_iri("rc:GraphRevision"),
        )
        items: list[GraphRevisionListItem] = []
        for revision_iri in revision_iris:
            item_revision_type = self._first_object(
                data_graphs,
                revision_iri,
                "rc:revisionType",
            )
            if (
                revision_type_filter is not None
                and item_revision_type != revision_type_filter
            ):
                continue
            revision_stance = self._first_object(
                data_graphs,
                revision_iri,
                "rc:revisionStance",
            )
            patch_iris = self._objects(
                data_graphs,
                revision_iri,
                "rc:hasGraphPatch",
            )
            applies_staged_revision = self._first_object(
                data_graphs,
                revision_iri,
                "rc:appliesStagedRevision",
            )
            alternative_to = self._first_object(
                data_graphs,
                revision_iri,
                "rc:alternativeTo",
            )
            restaged_from = self._first_object(
                data_graphs,
                revision_iri,
                "rc:restagesRevision",
            )
            restaged_by = self._first_subject(
                data_graphs,
                "rc:restagesRevision",
                revision_iri,
            )
            current_restaged_by = self._current_restage_successor_iri(
                revision_iri,
                graphs=data_graphs,
            )
            review_resolution = (
                self._staged_review_resolution_for_staged_iri(
                    revision_iri,
                    graphs=data_graphs,
                )
                if patch_iris
                else None
            )

            item_record_kind = self._graph_revision_record_kind(
                item_revision_type,
                has_patch_payload=bool(patch_iris),
                applies_staged_revision=applies_staged_revision,
            )
            applied_by = self._first_subject(
                data_graphs,
                "rc:appliesStagedRevision",
                revision_iri,
            )
            is_current_staged_work = (
                item_record_kind == "staged_patch"
                and applied_by is None
                and current_restaged_by is None
                and review_resolution is None
            )
            not_current_staged_work_reason = (
                self._not_current_staged_work_reason(
                    record_kind=item_record_kind,
                    applied_by=applied_by,
                    current_restaged_by=current_restaged_by,
                    review_resolution=review_resolution,
                )
                if not is_current_staged_work
                else None
            )
            if (
                record_kind_filter is not None
                and item_record_kind != record_kind_filter
            ):
                continue
            if current_staged_work_only and not is_current_staged_work:
                continue
            staged_validation_conforms = self._bool_object(
                data_graphs,
                revision_iri,
                "rc:validationConforms",
            )
            staged_validation_result_count = self._int_object(
                data_graphs,
                revision_iri,
                "rc:validationResultCount",
            )
            item_staged_validation_status = self._staged_validation_status(
                conforms=staged_validation_conforms,
                result_count=staged_validation_result_count,
            )
            if (
                staged_validation_status_filter is not None
                and item_staged_validation_status != staged_validation_status_filter
            ):
                continue

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
            if include_apply_checks and patch_iris:
                try:
                    check = self.check_staged_revision_apply(revision_iri)
                except DoxaBaseError:
                    application_status = "not_available"
                    application_decision = "inspect_staged_revision"
                    application_can_apply = None
                else:
                    application_status = check.status
                    application_decision = check.decision
                    application_can_apply = check.can_apply
                    application_summary = check.summary
                    application_recommended_resolution = check.recommended_resolution
                    application_validation_skipped_reason = (
                        check.validation_skipped_reason
                    )
                    application_blocking_reasons = check.blocking_reasons
                    application_count_drifts = check.count_drifts
                    application_semantic_risk_level = check.semantic_risk_level
                    application_semantic_risk_reasons = check.semantic_risk_reasons
                    if drift_detail == "exact":
                        application_snapshot_drifts = check.snapshot_drifts
                    else:
                        application_snapshot_drifts = (
                            self._summary_snapshot_drifts(check.snapshot_drifts)
                        )
                    suggested_next_actions = check.suggested_next_actions

            if application_status is None and applies_staged_revision is not None:
                application_status = "applied_event"
            if item_record_kind == "applied_event":
                suggested_next_actions = (
                    self._applied_revision_event_suggested_actions(revision_iri)
                )
            if (
                application_status_filter is not None
                and application_status != application_status_filter
            ):
                continue
            item_stale_resolution_state = self._stale_resolution_state(
                status=application_status,
                has_patch_payload=bool(patch_iris),
                restaged_from=restaged_from,
                restaged_by=restaged_by,
            )
            if (
                stale_resolution_state_filter is not None
                and item_stale_resolution_state != stale_resolution_state_filter
            ):
                continue

            snapshot_evidence = self._revision_snapshot_evidence_status(
                revision_iri,
                data_graphs,
            )
            suggested_next_actions = self._with_revision_snapshot_evidence_actions(
                suggested_next_actions,
                snapshot_evidence,
            )
            next_action = self._revision_next_action(
                revision_iri,
                apply_status=application_status,
                apply_decision=application_decision,
                stale_resolution_state=item_stale_resolution_state,
                suggested_next_actions=suggested_next_actions,
                restaged_by=restaged_by,
                current_restaged_by=current_restaged_by,
                record_kind=item_record_kind,
                staged_validation_status=item_staged_validation_status,
            )
            profile_route_sources = self._stored_profile_insight_route_sources(
                revision_iri
            )
            profile_route_groups = (
                self._stored_profile_route_groups(
                    profile_route_sources,
                    direct_review_lane=(
                        self._profile_insight_direct_review_lane_from_review_note(
                            self._first_object(
                                data_graphs,
                                revision_iri,
                                "rc:reviewNote",
                            )
                        )
                    ),
                )
                if profile_route_sources
                else []
            )
            profile_route_keys = self._profile_route_keys_from_sources(
                profile_route_sources
            )
            profile_gate = self._profile_revision_gate_fields(
                profile_route_groups,
                application_status=application_status,
            )
            alternative_gate = self._staged_revision_alternative_gate(
                alternative_to,
                revision_iri=revision_iri,
                graphs=data_graphs,
            )
            items.append(
                GraphRevisionListItem(
                    iri=revision_iri,
                    record_kind=item_record_kind,
                    is_current_staged_work=is_current_staged_work,
                    not_current_staged_work_reason=(
                        not_current_staged_work_reason
                    ),
                    summary=self._first_object(data_graphs, revision_iri, "rc:summary"),
                    revision_type=item_revision_type,
                    revision_type_label=(
                        self._label_from_graphs(ontology_graphs, item_revision_type)
                        if item_revision_type is not None
                        else None
                    ),
                    revision_stance=revision_stance,
                    revision_stance_label=self._label_for_resource(revision_stance),
                    created_at=self._first_object(
                        data_graphs,
                        revision_iri,
                        "rc:createdAt",
                    ),
                    changed_graphs=self._objects(
                        data_graphs,
                        revision_iri,
                        "rc:changedGraph",
                    ),
                    validation_scope=self._first_object(
                        data_graphs,
                        revision_iri,
                        "rc:validationScope",
                    ),
                    validation_conforms=staged_validation_conforms,
                    validation_result_count=staged_validation_result_count,
                    staged_validation_status=item_staged_validation_status,
                    has_patch_payload=bool(patch_iris),
                    patch_count=len(patch_iris),
                    applied_by=applied_by,
                    applies_staged_revision=applies_staged_revision,
                    alternative_to=alternative_to,
                    current_alternative_to=alternative_gate.current_alternative_to,
                    alternative_gate=alternative_gate,
                    restaged_from=restaged_from,
                    restaged_by=restaged_by,
                    current_restaged_by=current_restaged_by,
                    review_resolution=review_resolution,
                    stale_resolution_state=item_stale_resolution_state,
                    application_status=application_status,
                    application_decision=application_decision,
                    application_can_apply=application_can_apply,
                    application_summary=application_summary,
                    application_recommended_resolution=(
                        application_recommended_resolution
                    ),
                    application_validation_skipped_reason=(
                        application_validation_skipped_reason
                    ),
                    application_blocking_reasons=application_blocking_reasons,
                    application_count_drifts=application_count_drifts,
                    application_snapshot_drifts=application_snapshot_drifts,
                    application_semantic_risk_level=(
                        application_semantic_risk_level
                    ),
                    application_semantic_risk_reasons=(
                        application_semantic_risk_reasons
                    ),
                    profile_route_keys=profile_route_keys,
                    profile_route_groups=profile_route_groups,
                    profile_gate_label=profile_gate["profile_gate_label"],
                    profile_generic_queue_caution=(
                        profile_gate["profile_generic_queue_caution"]
                    ),
                    profile_semantic_apply_role=(
                        profile_gate["profile_semantic_apply_role"]
                    ),
                    profile_apply_cardinality=(
                        profile_gate["profile_apply_cardinality"]
                    ),
                    profile_safe_single_apply_candidate=(
                        profile_gate["profile_safe_single_apply_candidate"]
                    ),
                    profile_bulk_apply_allowed=(
                        profile_gate["profile_bulk_apply_allowed"]
                    ),
                    profile_semantic_apply_gate_reason=(
                        profile_gate["profile_semantic_apply_gate_reason"]
                    ),
                    snapshot_evidence=snapshot_evidence,
                    next_action=next_action,
                    suggested_next_actions=suggested_next_actions,
                )
            )

        items.sort(
            key=lambda item: (
                item.created_at or "",
                item.summary or "",
                item.iri,
            ),
            reverse=True,
        )
        sliced_items = items[offset : offset + limit]
        returned_current_staged_work_items = [
            item for item in sliced_items if item.is_current_staged_work
        ]
        next_action_queue_items: list[RevisionNextActionQueueItem] = []
        for item in sliced_items:
            queue_item = self._revision_next_action_queue_item(
                row_iri=item.iri,
                next_action=item.next_action,
                record_kind=item.record_kind,
                application_status=item.application_status,
                application_decision=item.application_decision,
                stale_resolution_state=item.stale_resolution_state,
                staged_validation_status=item.staged_validation_status,
                semantic_risk_level=item.application_semantic_risk_level,
                semantic_risk_reasons=item.application_semantic_risk_reasons,
                profile_route_keys=item.profile_route_keys,
                profile_gate_label=item.profile_gate_label,
                profile_generic_queue_caution=item.profile_generic_queue_caution,
                profile_semantic_apply_role=item.profile_semantic_apply_role,
                profile_apply_cardinality=item.profile_apply_cardinality,
                profile_safe_single_apply_candidate=(
                    item.profile_safe_single_apply_candidate
                ),
                profile_bulk_apply_allowed=item.profile_bulk_apply_allowed,
                profile_semantic_apply_gate_reason=(
                    item.profile_semantic_apply_gate_reason
                ),
                alternative_gate=item.alternative_gate,
            )
            if queue_item is not None:
                next_action_queue_items.append(queue_item)
        next_action_queue_items = (
            self._revision_next_action_queue_items_with_alternative_sets(
                next_action_queue_items,
                (
                    (item.iri, item.alternative_to, item.current_alternative_to)
                    for item in sliced_items
                ),
            )
        )
        return GraphRevisionList(
            revisions=sliced_items,
            count=len(items),
            returned_count=len(sliced_items),
            total_count=len(items),
            limit=limit,
            offset=offset,
            revision_type=revision_type_filter,
            record_kind=record_kind_filter,
            application_status=application_status_filter,
            staged_validation_status=staged_validation_status_filter,
            stale_resolution_state=stale_resolution_state_filter,
            current_staged_work_only=current_staged_work_only,
            returned_application_status_counts=self._graph_revision_list_counts(
                sliced_items,
                "application_status",
            ),
            returned_current_staged_work_application_status_counts=(
                self._graph_revision_list_counts(
                    returned_current_staged_work_items,
                    "application_status",
                )
            ),
            returned_stale_resolution_state_counts=self._graph_revision_list_counts(
                sliced_items,
                "stale_resolution_state",
            ),
            returned_staged_validation_status_counts=self._graph_revision_list_counts(
                sliced_items,
                "staged_validation_status",
            ),
            next_action_queue=self._revision_next_action_queue(
                (item.iri, item.next_action) for item in sliced_items
            ),
            next_action_queue_items=next_action_queue_items,
            next_action_queue_item_counts=(
                self._revision_next_action_queue_item_counts(
                    next_action_queue_items
                )
            ),
            semantic_review_required_queue_counts=(
                self._semantic_review_required_queue_counts(
                    next_action_queue_items
                )
            ),
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,
        )
    @staticmethod
    def _graph_revision_list_counts(
        items: Iterable[GraphRevisionListItem],
        field_name: str,
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in items:
            value = getattr(item, field_name)
            if value is None:
                continue
            counts[value] = counts.get(value, 0) + 1
        return counts
    @staticmethod
    def _suggested_action_from_revision_next_action(
        next_action: RevisionNextAction | None,
    ) -> SuggestedNextAction | None:
        if (
            next_action is None
            or next_action.tool_name is None
            or next_action.mcp_tool_name is None
        ):
            return None
        return SuggestedNextAction(
                   tool=next_action.mcp_tool_name,
                   args=next_action.arguments,
                   reason=next_action.reason,
               )
    def _graph_revision_record_kind(
        self,
        revision_type: str | None,
        *,
        has_patch_payload: bool,
        applies_staged_revision: str | None,
    ) -> str:
        if applies_staged_revision is not None:
            return "applied_event"
        if has_patch_payload:
            return "staged_patch"
        if revision_type == self.expand_iri("rc:StagedRevisionReviewResolution"):
            return "staged_review_resolution"
        if revision_type == self.expand_iri("rc:ExportRevision"):
            return "export_record"
        if revision_type == self.expand_iri("rc:ImportRevision"):
            return "import_record"
        return "history_record"
    def _graph_revision_record_kind_for_iri(
        self,
        revision_iri: str | None,
    ) -> str | None:
        if revision_iri is None:
            return None
        data_graphs = self._expand_graphs(["history"])
        if self.expand_iri("rc:GraphRevision") not in self._types_from_graphs(
            data_graphs,
            revision_iri,
        ):
            return None
        revision_type = self._first_object(
            data_graphs,
            revision_iri,
            "rc:revisionType",
        )
        patch_iris = self._objects(data_graphs, revision_iri, "rc:hasGraphPatch")
        applies_staged_revision = self._first_object(
            data_graphs,
            revision_iri,
            "rc:appliesStagedRevision",
        )
        return self._graph_revision_record_kind(
            revision_type,
            has_patch_payload=bool(patch_iris),
            applies_staged_revision=applies_staged_revision,
        )
    def _add_revision_context_for_slice(
        self,
        resources: dict[str, list[ContextSliceRoute]],
        all_graphs: list[str],
        add_resource: Any,
        add_revision: Any,
    ) -> None:
        history_graphs = ["history"]
        support_predicates = (
            ("rc:revisionSupportingPattern", "revision_supporting_pattern"),
            ("rc:revisionSupportingClaim", "revision_supporting_claim"),
            ("rc:revisionSupportingObservation", "revision_supporting_observation"),
        )
        for resource_iri in list(resources):
            for predicate, route in support_predicates:
                for revision_iri in self._subjects(
                    history_graphs,
                    predicate,
                    resource_iri,
                ):
                    add_resource(
                        revision_iri,
                        route,
                        "supporting revision",
                        source_iri=resource_iri,
                        depth=3,
                    )
                    for evidence_iri in self._objects(
                        all_graphs,
                        revision_iri,
                        "rc:evidence",
                    ):
                        add_resource(
                            evidence_iri,
                            "revision_evidence",
                            "revision evidence",
                            source_iri=revision_iri,
                            depth=4,
                        )
            for revision_iri in self._subjects(
                history_graphs,
                "rc:revisionAnchor",
                resource_iri,
            ):
                add_revision(
                    revision_iri,
                    resource_iri,
                    3,
                    route="revision_anchor_match",
                    route_label="revision anchored to selected resource",
                )
    def record_graph_revision(
        self,
        summary: str,
        rationale: str,
        changed_graphs: Iterable[str] | str,
        *,
        revision_type: str = "rc:ManualRevision",
        included_graphs: Iterable[str] | str | None = None,
        revision_iri: str | None = None,
        created_at: datetime | str | None = None,
        created_by: str | None = None,
        supporting_observations: Iterable[str] | str | None = None,
        supporting_claims: Iterable[str] | str | None = None,
        supporting_patterns: Iterable[str] | str | None = None,
        revision_anchors: Iterable[str] | str | None = None,
        evidence: Iterable[str] | str | None = None,
        export_path: str | None = None,
        graph_counts: dict[str, int] | None = None,
        validation_scope: str | None = None,
        validation_conforms: bool | None = None,
        validation_result_count: int | None = None,
        validation_results: Iterable[ValidationDiagnostic] | None = None,
    ) -> GraphRevisionRecord:
        summary_value = summary.strip()
        if not summary_value:
            raise DoxaBaseError("summary must not be empty")
        rationale_value = rationale.strip()
        if not rationale_value:
            raise DoxaBaseError("rationale must not be empty")

        changed_graph_values = self._graph_names_for_export(changed_graphs)
        for graph in changed_graph_values:
            self._ensure_mutable(graph)

        if included_graphs is not None:
            included_graph_values = self._graph_names_for_export(included_graphs)
        else:
            included_graph_values = []
        for graph_name in graph_counts or {}:
            if graph_name not in included_graph_values:
                included_graph_values.append(graph_name)
        if not included_graph_values:
            included_graph_values = changed_graph_values

        revision_subject = (
            self._required_iri("revision_iri", revision_iri)
            if revision_iri is not None
            else self._mint_iri("graph-revision")
        )
        revision_type_iri = self.expand_iri(revision_type)
        supporting_observation_values = self._string_values(
            "supporting_observations",
            supporting_observations,
        )
        supporting_claim_values = self._string_values(
            "supporting_claims",
            supporting_claims,
        )
        supporting_pattern_values = self._string_values(
            "supporting_patterns",
            supporting_patterns,
        )
        revision_anchor_values = self._string_values(
            "revision_anchors",
            revision_anchors,
        )
        evidence_values = self._string_values("evidence", evidence)
        self._validate_resource_values(
            "supporting_observations",
            supporting_observation_values,
        )
        self._validate_resource_values("supporting_claims", supporting_claim_values)
        self._validate_resource_values("supporting_patterns", supporting_pattern_values)
        self._validate_resource_values("revision_anchors", revision_anchor_values)
        self._validate_resource_values("evidence", evidence_values)
        self._ensure_non_negative(
            "validation_result_count",
            validation_result_count,
        )
        validation_result_values = list(validation_results or [])
        for graph_name, count in (graph_counts or {}).items():
            self._ensure_non_negative(f"graph_counts[{graph_name}]", count)

        snapshot_counts = graph_counts or self._graph_counts(included_graph_values)
        unknown_count_graphs = [
            graph for graph in snapshot_counts if graph not in self._known_graph_names()
        ]
        if unknown_count_graphs:
            raise DoxaBaseError(
                f"Unknown graph role(s) in graph_counts: {', '.join(sorted(unknown_count_graphs))}"
            )

        snapshot_rows = {
            graph_name: self._graph_storage_rows(graph_name)
            for graph_name in snapshot_counts
        }
        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(revision_subject)
        graph.add((subject, RDF.type, URIRef(self.expand_iri("rc:GraphRevision"))))
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:revisionType")),
                URIRef(revision_type_iri),
            )
        )
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:summary")),
                Literal(summary_value),
            )
        )
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:revisionRationale")),
                Literal(rationale_value),
            )
        )
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:createdAt")),
                self._datetime_literal(created_at, name="created_at"),
            )
        )
        if created_by is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:createdBy")),
                    self._resource_or_literal(created_by),
                )
            )
        for graph_name in changed_graph_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:changedGraph")),
                    Literal(graph_name),
                )
            )
        for graph_name in included_graph_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:includedGraph")),
                    Literal(graph_name),
                )
            )
        for support in supporting_observation_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:revisionSupportingObservation")),
                    URIRef(self.expand_iri(support)),
                )
            )
        for support in supporting_claim_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:revisionSupportingClaim")),
                    URIRef(self.expand_iri(support)),
                )
            )
        for support in supporting_pattern_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:revisionSupportingPattern")),
                    URIRef(self.expand_iri(support)),
                )
            )
        for anchor in revision_anchor_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:revisionAnchor")),
                    URIRef(self.expand_iri(anchor)),
                )
            )
        for evidence_iri in evidence_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:evidence")),
                    URIRef(self.expand_iri(evidence_iri)),
                )
            )
        self._add_optional_literal(graph, subject, "rc:exportPath", export_path)
        self._add_optional_literal(graph, subject, "rc:validationScope", validation_scope)
        if validation_conforms is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:validationConforms")),
                    Literal(validation_conforms, datatype=XSD.boolean),
                )
            )
        if validation_result_count is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:validationResultCount")),
                    Literal(validation_result_count, datatype=XSD.integer),
                )
            )
        for index, result in enumerate(validation_result_values, start=1):
            result_subject = URIRef(
                result.iri or f"{revision_subject}/validation-result/{index}"
            )
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasValidationResult")),
                    result_subject,
                )
            )
            self._add_validation_diagnostic_triples(graph, result_subject, result)

        snapshot_digests = {
            graph_name: self._graph_content_digest(graph_name)
            for graph_name in snapshot_counts
        }
        for index, (graph_name, count) in enumerate(
            sorted(snapshot_counts.items()),
            start=1,
        ):
            snapshot = URIRef(f"{revision_subject}/snapshot/{index}")
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasGraphSnapshot")),
                    snapshot,
                )
            )
            graph.add((snapshot, RDF.type, URIRef(self.expand_iri("rc:GraphSnapshot"))))
            graph.add(
                (
                    snapshot,
                    URIRef(self.expand_iri("rc:graphRole")),
                    Literal(graph_name),
                )
            )
            graph.add(
                (
                    snapshot,
                    URIRef(self.expand_iri("rc:tripleCount")),
                    Literal(count, datatype=XSD.integer),
                )
            )
            graph.add(
                (
                    snapshot,
                    URIRef(self.expand_iri("rc:contentDigest")),
                    Literal(snapshot_digests[graph_name]),
                )
            )

        triples = self._insert_graph("history", graph)
        self._store_graph_snapshot_rows(
            revision_subject,
            snapshot_rows=snapshot_rows,
            snapshot_counts=snapshot_counts,
            snapshot_digests=snapshot_digests,
        )
        return GraphRevisionRecord(
            revision_iri=revision_subject,
            revision_type=revision_type_iri,
            graph="history",
            triples=triples,
        )
    @staticmethod
    def _suggested_action_references_any_revision(
        action: SuggestedNextAction,
        revision_iris: set[str],
    ) -> bool:
        for key in ("iri", "revision_iri"):
            value = action_arguments(action).get(key)
            if isinstance(value, str) and value in revision_iris:
                return True
        for key in (
            "revision_iris",
            "source_revision_iris",
            "missing_revision_iris",
        ):
            values = action_arguments(action).get(key)
            if not isinstance(values, list):
                continue
            if any(
                isinstance(value, str) and value in revision_iris
                for value in values
            ):
                return True
        return False
    @staticmethod
    def _suggested_action_revision_iris(
        action: SuggestedNextAction | RevisionNextAction | None,
    ) -> list[str]:
        if action is None:
            return []
        values: list[str] = []
        for key in (
            "iri",
            "revision_iri",
            "restages_revision",
            "source_revision_iri",
        ):
            value = action_arguments(action).get(key)
            if isinstance(value, str):
                values.append(value)
        for key in (
            "revision_iris",
            "source_revision_iris",
            "missing_revision_iris",
        ):
            list_value = action_arguments(action).get(key)
            if isinstance(list_value, list):
                values.extend(
                    value for value in list_value if isinstance(value, str)
                )
        return list(dict.fromkeys(values))
    def _revision_next_action(
        self,
        revision_iri: str,
        *,
        apply_status: str | None,
        apply_decision: str | None,
        stale_resolution_state: str | None,
        suggested_next_actions: list[SuggestedNextAction],
        restaged_by: str | None = None,
        current_restaged_by: str | None = None,
        record_kind: str | None = None,
        staged_validation_status: str | None = None,
    ) -> RevisionNextAction | None:
        if apply_status is None and not suggested_next_actions:
            return None

        def find_exact_action(
            *,
            tool_name: str | None = None,
            reason_contains: str | None = None,
            args_aspect: str | None = None,
        ) -> SuggestedNextAction | None:
            for action in suggested_next_actions:
                if (
                    tool_name is not None
                    and action.tool != f"doxabase.{tool_name}"
                ):
                    continue
                if (
                    args_aspect is not None
                    and action.args.get("aspect") != args_aspect
                ):
                    continue
                if (
                    reason_contains is not None
                    and reason_contains not in action.reason
                ):
                    continue
                return action
            return None

        def find_action(
            *,
            tool_name: str | None = None,
            reason_contains: str | None = None,
        ) -> SuggestedNextAction | None:
            found = find_exact_action(
                tool_name=tool_name,
                reason_contains=reason_contains,
            )
            if found is not None:
                return found
            return suggested_next_actions[0] if suggested_next_actions else None

        def successor_inspect_action(
            successor_iri: str,
            *,
            reason: str,
        ) -> SuggestedNextAction:
            exact_action = next(
                (
                    action
                    for action in suggested_next_actions
                    if action.tool == "doxabase.describe_staged_revision"
                    and action.args.get("iri") == successor_iri
                ),
                None,
            )
            if exact_action is not None:
                return exact_action
            return SuggestedNextAction(
                       tool="doxabase.describe_staged_revision",
                       args={"iri": successor_iri},
                       reason=reason,
                   )

        def applied_successor_action(
            applied_revision_iri: str,
            *,
            reason: str,
        ) -> SuggestedNextAction:
            exact_action = next(
                (
                    action
                    for action in suggested_next_actions
                    if action.tool == "doxabase.describe_graph_revision"
                    and action.args.get("iri") == applied_revision_iri
                ),
                None,
            )
            if exact_action is not None:
                return exact_action
            return SuggestedNextAction(
                       tool="doxabase.describe_graph_revision",
                       args={"iri": applied_revision_iri},
                       reason=reason,
                   )

        action_type = "inspect_staged_revision"
        queue = "informational"
        label = "Inspect staged revision"
        reason = "Inspect staged revision details before taking action."
        selected_action: SuggestedNextAction | None = None

        snapshot_next_action = self._snapshot_evidence_completion_next_action(
            suggested_next_actions
        )
        if snapshot_next_action is not None:
            return snapshot_next_action

        if record_kind == "applied_event" or apply_status == "applied_event":
            action_type = "inspect_applied_event"
            queue = "inspect_already_applied"
            label = "Inspect applied event"
            reason = "Inspect the applied revision event for durable history context."
            selected_action = SuggestedNextAction(
                                  tool="doxabase.describe_graph_revision",
                                  args={"iri": revision_iri},
                                  reason=reason,
                              )
        elif stale_resolution_state == "stale_handled_by_restage" or (
            apply_status == "conflict" and (current_restaged_by or restaged_by)
        ):
            successor_iri = current_restaged_by or restaged_by
            applied_successor_iri = self._applied_event_for_staged_revision(
                successor_iri
            )
            if applied_successor_iri is not None:
                action_type = "inspect_already_applied"
                queue = "inspect_already_applied"
                label = "Inspect applied restaged successor"
                reason = (
                    "This stale source has a refreshed successor that was "
                    "already applied; inspect the applied event instead of "
                    "restaging this row again."
                )
                selected_action = applied_successor_action(
                    applied_successor_iri,
                    reason=reason,
                )
            else:
                action_type = "inspect_current_successor"
                queue = "informational"
                label = "Inspect current refreshed successor"
                reason = (
                    "This stale source already has a refreshed successor; inspect "
                    "the current successor instead of restaging this row again."
                )
                selected_action = successor_inspect_action(
                    successor_iri or revision_iri,
                    reason=reason,
                )
        elif (
            apply_decision == "inspect_current_successor"
            or apply_status == "superseded_by_restage"
        ):
            successor_iri = current_restaged_by or restaged_by
            applied_successor_iri = self._applied_event_for_staged_revision(
                successor_iri
            )
            if applied_successor_iri is not None:
                action_type = "inspect_already_applied"
                queue = "inspect_already_applied"
                label = "Inspect applied restaged successor"
                reason = (
                    "This staged source has a refreshed successor that was "
                    "already applied; inspect the applied event instead of "
                    "applying this row."
                )
                selected_action = applied_successor_action(
                    applied_successor_iri,
                    reason=reason,
                )
            else:
                action_type = "inspect_current_successor"
                queue = "informational"
                label = "Inspect current refreshed successor"
                reason = (
                    "This staged source has a refreshed successor; inspect the "
                    "current successor instead of applying this row."
                )
                selected_action = successor_inspect_action(
                    successor_iri or revision_iri,
                    reason=reason,
                )
        elif apply_decision == "inspect_restaged_source_validation_failure":
            action_type = "repair_or_replace"
            queue = "repair_or_replace"
            label = "Repair or replace"
            reason = (
                "Inspect the restaged source validation diagnostics, then stage "
                "a repaired or alternative candidate before applying this row."
            )
            selected_action = find_action(tool_name="describe_staged_revision")
        elif staged_validation_status == "failed":
            action_type = "repair_or_replace"
            queue = "repair_or_replace"
            label = "Repair or replace"
            reason = (
                "Stored staged-time validation failed; inspect diagnostics, then "
                "stage a repaired or alternative candidate before restaging or "
                "applying this row."
            )
            selected_action = (
                find_exact_action(tool_name="draft_staged_revision_rebase")
                or find_action(tool_name="describe_staged_revision")
            )
        elif apply_decision == "review_then_apply" or apply_status == "ready":
            action_type = "apply_after_review"
            queue = "apply_after_review"
            label = "Apply after review"
            reason = (
                "Review the staged revision and apply only if the proposal is "
                "still desired."
            )
            selected_action = find_action(tool_name="apply_staged_revision")
            if (
                selected_action is not None
                and "semantic review" in selected_action.reason
            ):
                label = "Apply only after semantic review"
        elif apply_decision in {
            "inspect_validation_results",
            "inspect_patch_conflict",
        } or apply_status == "validation_failed":
            action_type = "repair_or_replace"
            queue = "repair_or_replace"
            label = "Repair or replace"
            reason = (
                "Inspect diagnostics, then stage a repaired or alternative "
                "candidate instead of applying this row."
            )
            selected_action = (
                find_exact_action(tool_name="draft_staged_revision_rebase")
                or find_action(tool_name="describe_staged_revision")
            )
        elif (
            apply_decision == "restage_against_current_graph"
            or apply_status == "conflict"
        ) and find_exact_action(
            tool_name="describe_staged_revision",
            reason_contains="no effective delta",
        ) is not None:
            action_type = "inspect_no_effective_change"
            queue = "informational"
            label = "Inspect already-effective stale source"
            reason = (
                "The target graph drifted, but the stored patch payload already "
                "has no effective delta; inspect before ignoring or replacing it."
            )
            selected_action = find_exact_action(
                tool_name="describe_staged_revision",
                reason_contains="no effective delta",
            )
        elif (
            apply_decision == "restage_against_current_graph"
            or apply_status == "conflict"
        ) and find_exact_action(tool_name="stage_map_assertion_change") is not None:
            action_type = "repair_or_replace"
            queue = "repair_or_replace"
            label = "Stage same-slot replacement"
            reason = (
                "Exact snapshot drift shows this stale proposal should be "
                "reviewed as a replacement of a current same-slot value."
            )
            selected_action = find_exact_action(tool_name="stage_map_assertion_change")
        elif (
            apply_decision == "restage_against_current_graph"
            or apply_status == "conflict"
        ) and find_exact_action(
            tool_name="describe_resource",
            args_aspect="assertion_support",
        ) is not None:
            action_type = "repair_or_replace"
            queue = "repair_or_replace"
            label = "Review ambiguous same-slot conflict"
            reason = (
                "Exact snapshot drift points at a single-valued map slot, but "
                "the current graph has multiple values. Inspect current "
                "assertion support before staging an explicit repair."
            )
            selected_action = find_exact_action(
                tool_name="describe_resource",
                args_aspect="assertion_support",
            )
        elif (
            apply_decision == "restage_against_current_graph"
            or apply_status == "conflict"
        ) and find_exact_action(
            tool_name="draft_staged_revision_rebase",
        ) is not None:
            action_type = "repair_or_replace"
            queue = "repair_or_replace"
            label = "Draft patch repair plan"
            reason = (
                "Patch-level repair planning found a semantic subpatch inside "
                "a larger stale staged revision. Inspect the read-only plan "
                "before authoring a complete repaired successor."
            )
            selected_action = find_exact_action(
                tool_name="draft_staged_revision_rebase",
            )
        elif (
            apply_decision == "restage_against_current_graph"
            or apply_status == "conflict"
        ):
            action_type = "restage_after_review"
            queue = "restage_after_review"
            label = "Restage after review"
            reason = (
                "Review the stale proposal, then restage it against the current "
                "graph if the patch intent is still desired."
            )
            selected_action = find_action(tool_name="restage_staged_revision")
        elif (
            apply_decision == "inspect_applied_revision"
            or apply_status == "already_applied"
        ):
            action_type = "inspect_already_applied"
            queue = "inspect_already_applied"
            label = "Inspect applied event"
            reason = "Inspect the applied revision event instead of applying again."
            selected_action = find_action(tool_name="describe_graph_revision")
        elif (
            apply_decision == "inspect_no_effective_change"
            or apply_status == "noop"
        ):
            action_type = "inspect_no_effective_change"
            queue = "informational"
            label = "Inspect no-op revision"
            reason = (
                "Patch replay validates but would not change graph triples; "
                "inspect before replacing or ignoring it."
            )
            selected_action = find_action(tool_name="describe_staged_revision")
        else:
            selected_action = find_action(tool_name="describe_staged_revision")

        if selected_action is not None:
            return RevisionNextAction(
                action_type=action_type,
                queue=queue,
                action_label=label,
                tool_name=selected_action.tool.removeprefix("doxabase."),
                mcp_tool_name=selected_action.tool,
                arguments=selected_action.args,
                reason=selected_action.reason or reason,
                call=None,
                source="suggested_next_actions",
            )
        return RevisionNextAction(
            action_type=action_type,
            queue=queue,
            action_label=label,
            tool_name=None,
            mcp_tool_name=None,
            arguments={},
            reason=reason,
            call=None,
            source="derived",
        )
    @staticmethod
    def _revision_next_action_queue(
        rows: Iterable[tuple[str, RevisionNextAction | None]],
    ) -> dict[str, list[str]]:
        queues: dict[str, list[str]] = {}
        for revision_iri, next_action in rows:
            if next_action is None:
                continue
            queue = queues.setdefault(next_action.queue, [])
            if revision_iri not in queue:
                queue.append(revision_iri)
        return queues
    @staticmethod
    def _revision_next_action_resolved_target_iri(
        next_action: RevisionNextAction,
    ) -> str | None:
        target_iri = next_action.arguments.get("iri")
        return target_iri if isinstance(target_iri, str) else None
    def _revision_next_action_queue_item(
        self,
        *,
        row_iri: str,
        next_action: RevisionNextAction | None,
        record_kind: str | None = None,
        application_status: str | None = None,
        application_decision: str | None = None,
        stale_resolution_state: str | None = None,
        staged_validation_status: str | None = None,
        semantic_risk_level: str | None = None,
        semantic_risk_reasons: Iterable[str] = (),
        profile_route_keys: Iterable[str] = (),
        profile_gate_label: str | None = None,
        profile_generic_queue_caution: str | None = None,
        profile_semantic_apply_role: str | None = None,
        profile_apply_cardinality: str | None = None,
        profile_safe_single_apply_candidate: bool | None = None,
        profile_bulk_apply_allowed: bool | None = None,
        profile_semantic_apply_gate_reason: str | None = None,
        alternative_gate: StagedRevisionAlternativeGate | None = None,
    ) -> RevisionNextActionQueueItem | None:
        if next_action is None:
            return None
        resolved_target_iri = self._revision_next_action_resolved_target_iri(
            next_action
        )
        return RevisionNextActionQueueItem(
            row_iri=row_iri,
            queue=next_action.queue,
            action_type=next_action.action_type,
            action_label=next_action.action_label,
            tool_name=next_action.tool_name,
            mcp_tool_name=next_action.mcp_tool_name,
            resolved_target_iri=resolved_target_iri,
            resolved_target_iri_source=(
                "next_action.arguments.iri"
                if resolved_target_iri is not None
                else None
            ),
            resolved_target_record_kind=(
                self._graph_revision_record_kind_for_iri(resolved_target_iri)
            ),
            row_is_target=resolved_target_iri == row_iri,
            call=next_action.call,
            source=next_action.source,
            record_kind=record_kind,
            application_status=application_status,
            application_decision=application_decision,
            stale_resolution_state=stale_resolution_state,
            staged_validation_status=staged_validation_status,
            semantic_risk_level=semantic_risk_level,
            semantic_risk_reasons=list(semantic_risk_reasons),
            profile_route_keys=list(profile_route_keys),
            profile_gate_label=profile_gate_label,
            profile_generic_queue_caution=profile_generic_queue_caution,
            profile_semantic_apply_role=profile_semantic_apply_role,
            profile_apply_cardinality=profile_apply_cardinality,
            profile_safe_single_apply_candidate=profile_safe_single_apply_candidate,
            profile_bulk_apply_allowed=profile_bulk_apply_allowed,
            profile_semantic_apply_gate_reason=profile_semantic_apply_gate_reason,
            alternative_gate_status=(
                alternative_gate.status if alternative_gate is not None else None
            ),
            alternative_semantic_review_required=(
                alternative_gate.semantic_review_required
                if alternative_gate is not None
                else False
            ),
            requires_semantic_review_before_mutation=(
                alternative_gate.semantic_review_required
                if alternative_gate is not None
                else None
            ),
            alternative_applied_source_iri=(
                alternative_gate.applied_source_iri
                if alternative_gate is not None
                else None
            ),
            alternative_applied_revision_iri=(
                alternative_gate.applied_revision_iri
                if alternative_gate is not None
                else None
            ),
            alternative_set_iris=[],
            alternative_set_source_iri=None,
            alternative_set_role=None,
        )
    @staticmethod
    def _revision_next_action_queue_items_with_alternative_sets(
        queue_items: list[RevisionNextActionQueueItem],
        rows: Iterable[tuple[str, str | None, str | None]],
    ) -> list[RevisionNextActionQueueItem]:
        memberships = DoxaBase._alternative_set_membership_by_iri(rows)
        if not memberships:
            return queue_items
        enriched: list[RevisionNextActionQueueItem] = []
        for item in queue_items:
            membership = memberships.get(item.row_iri)
            if membership is None:
                enriched.append(item)
                continue
            alternative_set_iris, source_iri, role = membership
            enriched.append(
                replace(
                    item,
                    alternative_set_iris=alternative_set_iris,
                    alternative_set_source_iri=source_iri,
                    alternative_set_role=role,
                )
            )
        return enriched
    @staticmethod
    def _revision_next_action_queue_item_counts(
        queue_items: Iterable[RevisionNextActionQueueItem],
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in queue_items:
            counts[item.queue] = counts.get(item.queue, 0) + 1
        return counts
    @staticmethod
    def _revision_next_action_queue_item_is_mutation_target(
        item: RevisionNextActionQueueItem,
    ) -> bool:
        if item.resolved_target_iri is None:
            return False
        if item.queue in {"apply_after_review", "restage_after_review"}:
            return True
        if item.queue != "repair_or_replace":
            return False
        return item.tool_name in STAGED_RECOVERY_MUTATING_TOOL_NAMES
    @staticmethod
    def _semantic_review_required_queue_counts(
        queue_items: Iterable[RevisionNextActionQueueItem],
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in queue_items:
            if not item.alternative_semantic_review_required:
                continue
            counts[item.queue] = counts.get(item.queue, 0) + 1
        return counts
    def _assertion_revision_anchors(
        self,
        support: AssertionSupportDescription,
    ) -> list[str]:
        anchors = [support.subject.iri]
        for triple in support.same_subject_predicate_triples:
            if (
                triple.object_kind == "uri"
                and not self._is_generic_shared_value_resource(triple.object)
            ):
                anchors.append(triple.object)
        if (
            support.requested_object is not None
            and support.requested_object.value_kind == "iri"
            and not self._is_generic_shared_value_resource(
                support.requested_object.value
            )
        ):
            anchors.append(support.requested_object.value)
        for caveat in support.nearby_caveats:
            anchors.append(caveat.iri)
        return list(dict.fromkeys(anchors))
    def _ensure_revision_stance(self, stance_iri: str) -> None:
        revision_stance_iri = self.expand_iri("rc:RevisionStance")
        ontology_graphs = self._expand_graphs(["ontology"])
        if revision_stance_iri in self._types_from_graphs(
            ontology_graphs,
            stance_iri,
        ):
            return
        missing_seed_terms = self._missing_base_ontology_terms(
            REQUIRED_REVISION_STANCE_ONTOLOGY_TERMS,
        )
        if missing_seed_terms:
            raise DoxaBaseError(
                "stance must be an rc:RevisionStance declared in base or "
                "project ontology. "
                + self._stale_seed_recovery_message(missing_seed_terms)
            )
        raise DoxaBaseError(
            "stance must be an rc:RevisionStance declared in base or project "
            "ontology. Use rc:CandidateRevision, another built-in revision "
            "stance, or a project term typed as rc:RevisionStance."
        )
    def _assertion_support_without_revision(
        self,
        support: AssertionSupportDescription,
        revision_iri: str,
    ) -> AssertionSupportDescription:
        filtered_routes = [
            route
            for route in support.related_routes
            if not (
                route.resource_kind == "revision"
                and route.resource.iri == revision_iri
            )
        ]
        filtered_route_summaries = self._assertion_related_route_summaries(
            filtered_routes,
            subject_iri=support.subject.iri,
        )
        return replace(
            support,
            related_revisions=[
                revision
                for revision in support.related_revisions
                if revision.iri != revision_iri
            ],
            related_routes=filtered_routes,
            related_route_summaries=filtered_route_summaries,
        )
    def _context_slice_history_revision_iris(
        self,
        triples: Iterable[ResourceTriple],
    ) -> list[str]:
        graph_revision_type = self.expand_iri("rc:GraphRevision")
        revision_iris: list[str] = []
        for triple in triples:
            if triple.graph != "history":
                continue
            if (
                graph_revision_type in triple.subject_types
                or (
                    triple.predicate == str(RDF.type)
                    and triple.object == graph_revision_type
                )
            ):
                revision_iris.append(triple.subject)
        return list(dict.fromkeys(revision_iris))
    def _bool_object(self, graphs: list[str], subject: str, predicate: str) -> bool | None:
        value = self._first_object(graphs, subject, predicate)
        if value is None:
            return None
        return value.lower() in {"1", "true"}
    def _graph_revision_validation_results(
        self,
        revision_iri: str,
        graphs: list[str],
        *,
        patches: list[StagedGraphPatchDescription] | None = None,
    ) -> list[ValidationDiagnostic]:
        sh = PREFIXES["sh"]
        diagnostics: list[ValidationDiagnostic] = []
        for result_iri in self._objects(graphs, revision_iri, "rc:hasValidationResult"):
            focus_node = self._first_object(graphs, result_iri, sh + "focusNode")
            result_path = self._first_object(graphs, result_iri, sh + "resultPath")
            value = self._first_object(graphs, result_iri, sh + "value")
            source_shape = self._first_object(graphs, result_iri, sh + "sourceShape")
            source_constraint_component = self._first_object(
                graphs,
                result_iri,
                sh + "sourceConstraintComponent",
            )
            severity = self._first_object(graphs, result_iri, sh + "resultSeverity")
            messages = self._objects(graphs, result_iri, sh + "resultMessage")
            diagnostics.append(
                ValidationDiagnostic(
                    iri=result_iri,
                    focus_node=focus_node,
                    focus_node_label=self._diagnostic_resource_label(focus_node),
                    result_path=result_path,
                    result_path_label=self._diagnostic_resource_label(result_path),
                    value=value,
                    source_shape=source_shape,
                    source_constraint_component=source_constraint_component,
                    source_constraint_component_label=self._diagnostic_resource_label(
                        source_constraint_component
                    ),
                    severity=severity,
                    severity_label=self._diagnostic_resource_label(severity),
                    messages=messages,
                    hint=self._validation_diagnostic_hint(
                        result_path=result_path,
                        source_constraint_component=source_constraint_component,
                        messages=messages,
                    ),
                )
            )
        diagnostics = self._enrich_staged_validation_hints(
            diagnostics,
            patches=patches or [],
            revision_has_support_metadata=bool(
                self._objects(
                    graphs,
                    revision_iri,
                    "rc:revisionSupportingObservation",
                )
                or self._objects(graphs, revision_iri, "rc:revisionSupportingClaim")
                or self._objects(graphs, revision_iri, "rc:revisionSupportingPattern")
                or self._objects(graphs, revision_iri, "rc:evidence")
            ),
        )
        return sorted(diagnostics, key=self._validation_diagnostic_sort_key)
