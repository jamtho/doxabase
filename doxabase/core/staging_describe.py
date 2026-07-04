"""Staged revision description and previews.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via StagingDescribeMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class StagingDescribeMixin:
    def describe_staged_revision(
        self,
        iri: str,
        *,
        graph: str | None = "history",
        include_current_apply_check: bool = False,
    ) -> StagedGraphRevisionDescription:
        revision_iri = self.expand_iri(iri)
        data_graphs = self._expand_graphs([graph] if graph else None)
        lookup_graphs = self._lookup_graphs(data_graphs)
        if not self._subject_exists(revision_iri, data_graphs):
            graph_label = graph if graph is not None else "all graphs"
            hint = self._missing_revision_snapshot_storage_hint(revision_iri)
            raise DoxaBaseError(
                f"Staged graph revision '{iri}' was not found in {graph_label}{hint}"
            )
        if self.expand_iri("rc:GraphRevision") not in self._types_from_graphs(
            data_graphs,
            revision_iri,
        ):
            raise DoxaBaseError(f"Resource '{iri}' is not an rc:GraphRevision")

        patch_iris = self._objects(data_graphs, revision_iri, "rc:hasGraphPatch")
        if not patch_iris:
            applies_staged_revision = self._first_object(
                data_graphs,
                revision_iri,
                "rc:appliesStagedRevision",
            )
            if applies_staged_revision is not None:
                raise DoxaBaseError(
                    f"Graph revision '{iri}' is an applied revision event, "
                    "not a staged patch revision. Inspect it with "
                    "describe_revision (default or aspect='applied_diff'), "
                    "or pass the applied event's staged source IRI "
                    f"'{applies_staged_revision}'."
                )
            raise DoxaBaseError(f"Graph revision '{iri}' has no staged patch entries")

        revision_type = self._first_object(data_graphs, revision_iri, "rc:revisionType")
        revision_stance = self._first_object(
            data_graphs,
            revision_iri,
            "rc:revisionStance",
        )
        alternative_to_iri = self._first_object(
            data_graphs,
            revision_iri,
            "rc:alternativeTo",
        )
        restaged_from_iri = self._first_object(
            data_graphs,
            revision_iri,
            "rc:restagesRevision",
        )
        all_lookup_graphs = self._lookup_graphs(self._expand_graphs(["all"]))
        restaged_from = (
            self._resource_summary(all_lookup_graphs, restaged_from_iri)
            if restaged_from_iri is not None
            else None
        )
        restaged_by_iri = self._first_subject(
            data_graphs,
            "rc:restagesRevision",
            revision_iri,
        )
        restaged_by = (
            self._resource_summary(all_lookup_graphs, restaged_by_iri)
            if restaged_by_iri is not None
            else None
        )
        current_restaged_by_iri = self._current_restage_successor_iri(
            revision_iri,
            graphs=data_graphs,
        )
        current_restaged_by = (
            self._resource_summary(all_lookup_graphs, current_restaged_by_iri)
            if current_restaged_by_iri is not None
            else None
        )
        applied_by_iri = self._first_subject(
            data_graphs,
            "rc:appliesStagedRevision",
            revision_iri,
        )
        applied_by = (
            self._resource_summary(all_lookup_graphs, applied_by_iri)
            if applied_by_iri is not None
            else None
        )
        rationale = self._first_object(
            data_graphs,
            revision_iri,
            "rc:revisionRationale",
        )
        snapshots = self._graph_revision_snapshots(revision_iri, data_graphs)
        included_graphs = self._objects(data_graphs, revision_iri, "rc:includedGraph")
        if not included_graphs:
            included_graphs = [snapshot.graph_role for snapshot in snapshots]
        patches = [
            self._describe_staged_graph_patch(patch_iri, data_graphs)
            for patch_iri in patch_iris
        ]
        patches.sort(key=self._staged_patch_sort_key)
        impacts = self._staged_revision_impacts(
            revision_iri=revision_iri,
            patches=patches,
            lookup_graphs=all_lookup_graphs,
        )
        profile_route_sources = self._stored_profile_insight_route_sources(
            revision_iri
        )

        description = StagedGraphRevisionDescription(
            iri=revision_iri,
            graph=graph,
            label=self._display_label_from_graphs(lookup_graphs, revision_iri),
            summary=self._first_object(data_graphs, revision_iri, "rc:summary"),
            revision_type=revision_type,
            revision_type_label=(
                self._label_from_graphs(self._expand_graphs(["ontology"]), revision_type)
                if revision_type is not None
                else None
            ),
            revision_stance=revision_stance,
            revision_stance_label=self._label_for_resource(revision_stance),
            rationale=rationale,
            review_note=self._first_object(data_graphs, revision_iri, "rc:reviewNote"),
            review_recommendation=self._first_object(
                data_graphs,
                revision_iri,
                "rc:reviewRecommendation",
            ),
            alternative_to=(
                self._resource_summary(all_lookup_graphs, alternative_to_iri)
                if alternative_to_iri is not None
                else None
            ),
            alternative_gate=self._staged_revision_alternative_gate(
                alternative_to_iri,
                revision_iri=revision_iri,
                graphs=all_lookup_graphs,
            ),
            restaged_from=restaged_from,
            restaged_by=restaged_by,
            current_restaged_by=current_restaged_by,
            applied_by=applied_by,
            review_resolution=self._staged_review_resolution_for_staged_iri(
                revision_iri,
                graphs=data_graphs,
            ),
            application_status="already_applied" if applied_by is not None else None,
            restage_reason=self._staged_revision_restage_reason(
                restaged_from=restaged_from,
                rationale=rationale,
            ),
            changed_graphs=self._objects(data_graphs, revision_iri, "rc:changedGraph"),
            included_graphs=included_graphs,
            created_at=self._first_object(data_graphs, revision_iri, "rc:createdAt"),
            created_by=self._first_object(data_graphs, revision_iri, "rc:createdBy"),
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
            patches=patches,
            impacts=impacts,
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
            profile_route_sources=profile_route_sources,
            profile_route_keys=self._profile_route_keys_from_sources(
                profile_route_sources
            ),
            profile_route_groups=[],
        )
        if profile_route_sources:
            description = replace(
                description,
                profile_route_groups=self._stored_profile_route_groups(
                    profile_route_sources,
                    direct_review_lane=(
                        self._profile_insight_candidate_direct_review_lane(
                            description
                        )
                    ),
                ),
            )
        judgement_panel = self._staged_revision_judgement_panel(description)
        if judgement_panel is not None:
            description = replace(description, judgement_panel=judgement_panel)
        else:
            stored_review_context = self._staged_revision_stored_review_context(
                description
            )
            if stored_review_context is not None:
                description = replace(
                    description,
                    stored_review_context=stored_review_context,
                )
        if include_current_apply_check:
            description = replace(
                description,
                current_apply_check=self._staged_revision_apply_summary(
                    description,
                ),
            )
        return description
    def _preview_staged_revision_application(
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
        staged: StagedGraphRevisionDescription | None = None,
    ) -> _StagedRevisionApplicationPreview:
        staged = staged or self.describe_staged_revision(iri)
        changed_graphs = list(
            dict.fromkeys(
                patch.target_graph for patch in staged.patches if patch.target_graph
            )
        )
        validation_scope_value = validation_scope or staged.validation_scope or "all"
        try:
            self._graphs_for_validation_scope(validation_scope_value)
        except ValueError as exc:
            raise DoxaBaseError(str(exc)) from exc
        existing_applied = self._subjects(
            self._expand_graphs(["history"]),
            "rc:appliesStagedRevision",
            staged.iri,
        )
        semantic_risk_level, semantic_risk_reasons = (
            self._staged_revision_semantic_risk(staged)
        )
        (
            restaged_source_validation_warning,
            restaged_successor_reuses_source_patch_payload,
        ) = self._restaged_source_validation_context(staged)
        if restaged_source_validation_warning is not None and not (
            restaged_successor_reuses_source_patch_payload
        ):
            semantic_risk_reasons = [
                *semantic_risk_reasons,
                (
                    "The staged successor revises a source that failed "
                    "staged-time validation."
                ),
            ]
        if restaged_source_validation_warning is not None:
            semantic_risk_reasons = list(
                dict.fromkeys(
                    [
                        *semantic_risk_reasons,
                        restaged_source_validation_warning,
                    ]
                )
            )
            semantic_risk_level = (
                "high" if semantic_risk_level != "none" else "attention"
            )
        snapshot_drifts = self._staged_revision_snapshot_drifts(
            staged,
            changed_graphs,
        )
        snapshot_evidence = self._revision_snapshot_evidence_status(
            staged.iri,
            self._expand_graphs(["history"]),
        )
        blocking_preflight_actions = (
            self._staged_apply_check_blocking_preflight_actions(snapshot_evidence)
        )
        snapshot_drift_by_graph = {
            drift.graph_role: drift for drift in snapshot_drifts
        }
        restaged_by_iri = (
            staged.restaged_by.iri if staged.restaged_by is not None else None
        )
        current_restaged_by_iri = (
            staged.current_restaged_by.iri
            if staged.current_restaged_by is not None
            else None
        )
        restaged_from_iri = (
            staged.restaged_from.iri if staged.restaged_from is not None else None
        )
        if existing_applied:
            status = "already_applied"
            effective_delta_summary = self._staged_apply_effective_delta_summary(
                [],
                replayable_triples_to_add=0,
                replayable_triples_to_remove=0,
            )
            stale_resolution_state = self._stale_resolution_state(
                status=status,
                has_patch_payload=bool(staged.patches),
                restaged_from=restaged_from_iri,
                restaged_by=restaged_by_iri,
            )
            summary = self._staged_apply_check_summary(
                status=status,
                conflicts=[
                    "Staged revision has already been applied by "
                    f"'{existing_applied[0]}'"
                ],
                validation_result_count=None,
                changed_graphs=changed_graphs,
                patches_checked=0,
                triples_to_add=0,
                triples_to_remove=0,
                already_applied_by=existing_applied[0],
                restaged_by=restaged_by_iri,
                current_restaged_by=current_restaged_by_iri,
            )
            suggested_next_actions = self._staged_apply_check_next_actions(
                staged.iri,
                status=status,
                staged=staged,
                semantic_risk_level=semantic_risk_level,
                blocking_reasons=["already_applied"],
                already_applied_by=existing_applied[0],
                restaged_by=restaged_by_iri,
                current_restaged_by=current_restaged_by_iri,
            )
            blocking_reasons = self._staged_apply_check_blocking_reasons(
                status=status,
                conflicts=[],
            )
            decision = self._staged_apply_check_decision(
                status,
                blocking_reasons=blocking_reasons,
            )
            next_action = self._revision_next_action(
                staged.iri,
                apply_status=status,
                apply_decision=decision,
                stale_resolution_state=stale_resolution_state,
                suggested_next_actions=suggested_next_actions,
                restaged_by=restaged_by_iri,
                current_restaged_by=current_restaged_by_iri,
                staged_validation_status=self._staged_validation_status(
                    conforms=staged.validation_conforms,
                    result_count=staged.validation_result_count,
                ),
            )
            routing_decision = self._staged_apply_check_routing_decision(
                decision,
                next_action,
            )
            first_safe_next_action = (
                self._staged_apply_check_first_safe_next_action(
                    next_action,
                    staged_revision_iri=staged.iri,
                    suggested_next_actions=suggested_next_actions,
                    blocking_preflight_actions=blocking_preflight_actions,
                    alternative_gate=staged.alternative_gate,
                )
            )
            suggested_next_actions = (
                self._staged_apply_check_ordered_suggested_next_actions(
                    blocking_preflight_actions=blocking_preflight_actions,
                    suggested_next_actions=suggested_next_actions,
                )
            )
            check = StagedRevisionApplyCheck(
                staged_revision_iri=staged.iri,
                revision_iri=staged.iri,
                can_apply=False,
                status=status,
                decision=decision,
                routing_decision=routing_decision,
                summary=summary,
                review_recommended=self._staged_apply_check_review_recommended(
                    status,
                    semantic_risk_level=semantic_risk_level,
                ),
                semantic_risk_level=semantic_risk_level,
                semantic_risk_reasons=semantic_risk_reasons,
                blocking_reasons=blocking_reasons,
                recommended_resolution=(
                    self._staged_apply_check_recommended_resolution(
                        status=status,
                        blocking_reasons=blocking_reasons,
                        suggested_next_actions=suggested_next_actions,
                        restaged_by=restaged_by_iri,
                        current_restaged_by=current_restaged_by_iri,
                        restaged_source_validation_warning=(
                            restaged_source_validation_warning
                        ),
                    )
                ),
                already_applied_by=existing_applied[0],
                restaged_by=restaged_by_iri,
                current_restaged_by=current_restaged_by_iri,
                stale_resolution_state=stale_resolution_state,
                alternative_gate=staged.alternative_gate,
                changed_graphs=changed_graphs,
                patch_checks=[],
                patch_repair_plan=[],
                count_drifts=[],
                snapshot_drifts=[],
                conflicts=[
                    "Staged revision has already been applied by "
                    f"'{existing_applied[0]}'"
                ],
                validation_scope=validation_scope_value,
                validation_conforms=None,
                validation_skipped_reason=(
                    self._staged_apply_check_validation_skipped_reason(status)
                ),
                validation_result_count=None,
                validation_results=[],
                patches_checked=0,
                triples_to_add=0,
                triples_to_remove=0,
                effective_delta_summary=effective_delta_summary,
                next_action=next_action,
                suggested_next_actions=suggested_next_actions,
                snapshot_evidence=snapshot_evidence,
                snapshot_evidence_completeness=(
                    self._snapshot_evidence_completeness_label(snapshot_evidence)
                ),
                blocking_preflight_actions=blocking_preflight_actions,
                mutation_allowed_after=(
                    self._staged_apply_check_mutation_allowed_after(
                        blocking_preflight_actions
                    )
                ),
                first_safe_next_action=first_safe_next_action,
            )
            return _StagedRevisionApplicationPreview(
                staged=staged,
                check=check,
                parsed_patches=[],
                preview_graphs={},
            )

        preview_graphs: dict[str, Graph] = {}
        parsed_patches: list[tuple[StagedGraphPatchDescription, Graph]] = []
        patch_checks: list[StagedPatchApplyCheck] = []
        count_drifts: list[StagedGraphCountDrift] = []
        conflicts: list[str] = []
        triples_to_add = 0
        triples_to_remove = 0
        addition_operation = self.expand_iri("rc:AdditionPatch")
        removal_operation = self.expand_iri("rc:RemovalPatch")

        for patch in staged.patches:
            target_graph: str | None = None
            count_basis: str | None = None
            operation: str | None = None
            current_count: int | None = None
            preview_count: int | None = None
            effective_triples_to_add: int | None = None
            effective_triples_to_remove: int | None = None
            already_present_triples: int | None = None
            already_absent_triples: int | None = None
            conflict: str | None = None
            patch_graph: Graph | None = None
            try:
                target_graph = self._required_staged_patch_target_graph(patch)
                count_basis = patch.count_basis or self._staged_patch_count_basis(
                    target_graph
                )
                operation = self._required_staged_patch_field(
                    patch,
                    "operation",
                    patch.operation,
                )
                current_preview = preview_graphs.setdefault(
                    target_graph,
                    self.to_graph([target_graph]),
                )
                current_count = len(current_preview)
                patch_graph = self._parse_staged_patch_description(patch)
                already_present_triples = sum(
                    1 for triple in patch_graph if triple in current_preview
                )
                already_absent_triples = len(patch_graph) - already_present_triples
                if operation == addition_operation:
                    effective_triples_to_add = already_absent_triples
                    effective_triples_to_remove = 0
                elif operation == removal_operation:
                    effective_triples_to_add = 0
                    effective_triples_to_remove = already_present_triples
                if (
                    patch.before_triple_count is not None
                    and current_count != patch.before_triple_count
                ):
                    snapshot_drift = snapshot_drift_by_graph.get(target_graph)
                    exact_graph_diff_available = (
                        snapshot_drift.exact_changed_triples_available
                        if snapshot_drift is not None
                        else False
                    )
                    if exact_graph_diff_available:
                        count_drift_note = (
                            "DoxaBase can report staged/current graph counts and "
                            "whether the staged patch triples are present in the "
                            "current graph. Exact target graph additions and "
                            "removals since the staged snapshot are available in "
                            "snapshot_drifts."
                        )
                    else:
                        count_drift_note = (
                            "DoxaBase can report staged/current graph counts "
                            "and whether the staged patch triples are present "
                            "in the current graph, but exact unrelated changed "
                            "triples need graph snapshot storage for this "
                            "revision."
                        )
                    count_drifts.append(
                        StagedGraphCountDrift(
                            patch_iri=patch.iri,
                            patch_sequence_index=patch.sequence_index,
                            target_graph=target_graph,
                            count_basis=count_basis or "unknown",
                            expected_before_triple_count=patch.before_triple_count,
                            expected_before_basis=(
                                self._count_drift_expected_before_basis(
                                    patch.sequence_index
                                )
                            ),
                            current_triple_count=current_count,
                            delta=current_count - patch.before_triple_count,
                            exact_changed_triples_available=exact_graph_diff_available,
                            patch_operation=operation,
                            patch_operation_label=patch.operation_label,
                            patch_triples_checked=len(patch_graph),
                            patch_triples_currently_present=already_present_triples,
                            patch_triples_currently_absent=already_absent_triples,
                            patch_triple_status=self._patch_triple_presence_status(
                                patch_triples_checked=len(patch_graph),
                                patch_triples_present=already_present_triples,
                            ),
                            note=count_drift_note,
                        )
                    )
                    conflict = (
                        f"graph '{target_graph}' expected "
                        f"{patch.before_triple_count} triples before patch, "
                        f"found {current_count}"
                    )
                if conflict is None and target_graph in snapshot_drift_by_graph:
                    drift = snapshot_drift_by_graph[target_graph]
                    conflict = (
                        f"graph '{target_graph}' content digest changed since "
                        f"staging: expected {drift.snapshot_content_digest}, "
                        f"found {drift.current_content_digest}"
                    )
                candidate_preview = self._clone_graph(current_preview)
                if operation == addition_operation:
                    for triple in patch_graph:
                        candidate_preview.add(triple)
                elif operation == removal_operation:
                    for triple in patch_graph:
                        candidate_preview.remove(triple)
                else:
                    conflict = f"unsupported staged patch operation '{operation}'"
                preview_count = len(candidate_preview)
                if (
                    conflict is None
                    and patch.after_triple_count is not None
                    and preview_count != patch.after_triple_count
                ):
                    conflict = (
                        f"graph '{target_graph}' expected "
                        f"{patch.after_triple_count} triples after patch, "
                        f"preview produced {preview_count}"
                    )
                if conflict is None:
                    preview_graphs[target_graph] = candidate_preview
                    parsed_patches.append((patch, patch_graph))
                    if operation == addition_operation:
                        triples_to_add += effective_triples_to_add or 0
                    elif operation == removal_operation:
                        triples_to_remove += effective_triples_to_remove or 0
            except DoxaBaseError as exc:
                conflict = str(exc)

            can_apply_patch = conflict is None
            if conflict is not None:
                conflicts.append(f"{patch.iri}: {conflict}")
            patch_checks.append(
                StagedPatchApplyCheck(
                    patch_iri=patch.iri,
                    target_graph=target_graph or patch.target_graph,
                    count_basis=(
                        count_basis
                        or self._staged_patch_count_basis(
                            target_graph or patch.target_graph
                        )
                    ),
                    operation=operation or patch.operation,
                    operation_label=patch.operation_label,
                    patch_role=patch.patch_role,
                    patch_role_label=patch.patch_role_label,
                    triple_count=patch.triple_count,
                    before_triple_count=patch.before_triple_count,
                    current_triple_count=current_count,
                    after_triple_count=patch.after_triple_count,
                    preview_triple_count=preview_count,
                    effective_triples_to_add=effective_triples_to_add,
                    effective_triples_to_remove=effective_triples_to_remove,
                    already_present_triples=already_present_triples,
                    already_absent_triples=already_absent_triples,
                    can_apply=can_apply_patch,
                    conflict=conflict,
                )
            )

        validation_conforms: bool | None = None
        validation_result_count: int | None = None
        validation_results: list[ValidationDiagnostic] = []
        if not conflicts:
            validation = self._validate_graph_preview(
                validation_scope_value,  # type: ignore[arg-type]
                preview_graphs=preview_graphs,
            )
            validation_conforms = validation.conforms
            validation_result_count = validation.result_count
            validation_results = self._enrich_staged_validation_hints(
                validation.results,
                patches=[patch for patch, _ in parsed_patches],
                revision_has_support_metadata=bool(
                    staged.supporting_observations
                    or staged.supporting_claims
                    or staged.supporting_patterns
                    or staged.evidence
                ),
            )

        has_effective_patch_triples = (triples_to_add + triples_to_remove) > 0
        effective_delta_summary = self._staged_apply_effective_delta_summary(
            patch_checks,
            replayable_triples_to_add=triples_to_add,
            replayable_triples_to_remove=triples_to_remove,
        )
        patch_repair_plan = self._staged_patch_repair_plan(
            staged,
            patch_checks=patch_checks,
            snapshot_drifts=snapshot_drifts,
            validation_scope=validation_scope_value,
        )
        can_apply = (
            not conflicts
            and validation_conforms is True
            and has_effective_patch_triples
        )
        status = self._staged_apply_check_status(
            can_apply=can_apply,
            conflicts=conflicts,
            validation_conforms=validation_conforms,
            has_effective_patch_triples=has_effective_patch_triples,
        )
        if status in {"ready", "noop"} and staged.restaged_by is not None:
            can_apply = False
            status = "superseded_by_restage"
        stale_resolution_state = self._stale_resolution_state(
            status=status,
            has_patch_payload=bool(staged.patches),
            restaged_from=restaged_from_iri,
            restaged_by=restaged_by_iri,
        )
        summary = self._staged_apply_check_summary(
            status=status,
            conflicts=conflicts,
            validation_result_count=validation_result_count,
            changed_graphs=changed_graphs,
            patches_checked=len(patch_checks),
            triples_to_add=triples_to_add,
            triples_to_remove=triples_to_remove,
            already_applied_by=None,
            restaged_by=restaged_by_iri,
            current_restaged_by=current_restaged_by_iri,
            already_effective=(
                status == "conflict" and effective_delta_summary.already_effective
            ),
        )
        blocking_reasons = self._staged_apply_check_blocking_reasons(
            status=status,
            conflicts=conflicts,
        )
        suggested_next_actions = self._staged_apply_check_next_actions(
            staged.iri,
            status=status,
            staged=staged,
            semantic_risk_level=semantic_risk_level,
            blocking_reasons=blocking_reasons,
            already_applied_by=None,
            restaged_by=restaged_by_iri,
            current_restaged_by=current_restaged_by_iri,
            patch_checks=patch_checks,
            patch_repair_plan=patch_repair_plan,
            snapshot_drifts=snapshot_drifts,
            validation_scope=validation_scope_value,
            restaged_source_validation_warning=(
                restaged_source_validation_warning
            ),
            restaged_successor_reuses_source_patch_payload=(
                restaged_successor_reuses_source_patch_payload
            ),
        )
        decision = self._staged_apply_check_decision(
            status,
            blocking_reasons=blocking_reasons,
            restaged_source_validation_warning=(
                restaged_source_validation_warning
            ),
            restaged_successor_reuses_source_patch_payload=(
                restaged_successor_reuses_source_patch_payload
            ),
        )
        next_action = self._revision_next_action(
            staged.iri,
            apply_status=status,
            apply_decision=decision,
            stale_resolution_state=stale_resolution_state,
            suggested_next_actions=suggested_next_actions,
            restaged_by=restaged_by_iri,
            current_restaged_by=current_restaged_by_iri,
            staged_validation_status=self._staged_validation_status(
                conforms=staged.validation_conforms,
                result_count=staged.validation_result_count,
            ),
        )
        routing_decision = self._staged_apply_check_routing_decision(
            decision,
            next_action,
        )
        first_safe_next_action = self._staged_apply_check_first_safe_next_action(
            next_action,
            staged_revision_iri=staged.iri,
            suggested_next_actions=suggested_next_actions,
            blocking_preflight_actions=blocking_preflight_actions,
            alternative_gate=staged.alternative_gate,
        )
        suggested_next_actions = (
            self._staged_apply_check_ordered_suggested_next_actions(
                blocking_preflight_actions=blocking_preflight_actions,
                suggested_next_actions=suggested_next_actions,
            )
        )
        check = StagedRevisionApplyCheck(
            staged_revision_iri=staged.iri,
            revision_iri=staged.iri,
            can_apply=can_apply,
            status=status,
            decision=decision,
            routing_decision=routing_decision,
            summary=summary,
            review_recommended=self._staged_apply_check_review_recommended(
                status,
                semantic_risk_level=semantic_risk_level,
            ),
            semantic_risk_level=semantic_risk_level,
            semantic_risk_reasons=semantic_risk_reasons,
            blocking_reasons=blocking_reasons,
            recommended_resolution=self._staged_apply_check_recommended_resolution(
                status=status,
                blocking_reasons=blocking_reasons,
                suggested_next_actions=suggested_next_actions,
                restaged_by=restaged_by_iri,
                current_restaged_by=current_restaged_by_iri,
                restaged_source_validation_warning=(
                    restaged_source_validation_warning
                ),
                restaged_successor_reuses_source_patch_payload=(
                    restaged_successor_reuses_source_patch_payload
                ),
            ),
            already_applied_by=None,
            restaged_by=restaged_by_iri,
            current_restaged_by=current_restaged_by_iri,
            stale_resolution_state=stale_resolution_state,
            alternative_gate=staged.alternative_gate,
            changed_graphs=changed_graphs,
            patch_checks=patch_checks,
            patch_repair_plan=patch_repair_plan,
            count_drifts=count_drifts,
            snapshot_drifts=snapshot_drifts,
            conflicts=conflicts,
            validation_scope=validation_scope_value,
            validation_conforms=validation_conforms,
            validation_skipped_reason=(
                self._staged_apply_check_validation_skipped_reason(status)
            ),
            validation_result_count=validation_result_count,
            validation_results=validation_results,
            patches_checked=len(patch_checks),
            triples_to_add=triples_to_add,
            triples_to_remove=triples_to_remove,
            effective_delta_summary=effective_delta_summary,
            next_action=next_action,
            suggested_next_actions=suggested_next_actions,
            snapshot_evidence=snapshot_evidence,
            snapshot_evidence_completeness=(
                self._snapshot_evidence_completeness_label(snapshot_evidence)
            ),
            blocking_preflight_actions=blocking_preflight_actions,
            mutation_allowed_after=(
                self._staged_apply_check_mutation_allowed_after(
                    blocking_preflight_actions
                )
            ),
            first_safe_next_action=first_safe_next_action,
        )
        return _StagedRevisionApplicationPreview(
            staged=staged,
            check=check,
            parsed_patches=parsed_patches,
            preview_graphs=preview_graphs,
        )
    @staticmethod
    def _count_drift_expected_before_basis(
        patch_sequence_index: int | None,
    ) -> str:
        if patch_sequence_index is None:
            return (
                "expected_before_triple_count is the count recorded for this "
                "patch's staged replay point"
            )
        if patch_sequence_index <= 1:
            return (
                "expected_before_triple_count is the original staged graph "
                "snapshot before patch 1"
            )
        return (
            "expected_before_triple_count is the staged replay count before "
            f"patch {patch_sequence_index} for this patch's target graph, after "
            "any earlier patches that affected that target graph"
        )
    @staticmethod
    def _semantic_risk_queue_counts(
        summaries: Iterable[StagedGraphRevisionExportSummary],
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for summary in summaries:
            if summary.semantic_risk_level not in {"attention", "high"}:
                continue
            if summary.next_action is None:
                continue
            counts[summary.next_action.queue] = (
                counts.get(summary.next_action.queue, 0) + 1
            )
        return counts
    def _staged_revisions_bundle_summary(
        self,
        summaries: list[StagedGraphRevisionExportSummary],
        *,
        descriptions: list[StagedGraphRevisionDescription],
        snapshot_evidence: StagedGraphRevisionSnapshotEvidenceSummary,
    ) -> StagedGraphRevisionBundleSummary:
        apply_status_counts: dict[str, int] = {}
        state_counts: dict[str, int] = {}
        unresolved_stale: list[str] = []
        handled_stale: list[str] = []
        ready_successors: list[str] = []
        validation_failed: list[str] = []
        staged_validation_failed: list[str] = []
        recommended_review: list[str] = []
        recommended_mutation_review: list[str] = []
        recommended_apply_or_restage_review: list[str] = []
        recommended_repair_review: list[str] = []
        recommended_applied_inspection: list[str] = []
        parallel_applied_restage_successors: list[tuple[str, str, str]] = []

        def increment(counts: dict[str, int], key: str | None) -> None:
            if key is None:
                return
            counts[key] = counts.get(key, 0) + 1

        def recommend(iri: str | None) -> None:
            if iri is not None and iri not in recommended_review:
                recommended_review.append(iri)

        def recommend_mutation(iri: str | None) -> None:
            recommend(iri)
            if iri is not None and iri not in recommended_mutation_review:
                recommended_mutation_review.append(iri)

        def recommend_mutation_by_decision(
            summary: StagedGraphRevisionExportSummary,
        ) -> None:
            if (
                summary.next_action is not None
                and summary.next_action.action_type
                == "inspect_no_effective_change"
            ):
                recommend(summary.revision_iri)
            elif (
                summary.next_action is not None
                and summary.next_action.queue == "repair_or_replace"
            ):
                recommend_repair(summary.revision_iri)
            elif summary.staged_validation_conforms is False:
                recommend_repair(summary.revision_iri)
            elif summary.apply_decision in {
                "review_then_apply",
                "restage_against_current_graph",
            }:
                recommend_apply_or_restage(summary.revision_iri)
            elif summary.apply_decision in {
                "inspect_validation_results",
                "inspect_patch_conflict",
                "inspect_restaged_source_validation_failure",
            }:
                recommend_repair(summary.revision_iri)
            else:
                recommend_mutation(summary.revision_iri)

        def recommend_apply_or_restage(iri: str | None) -> None:
            recommend_mutation(iri)
            if iri is not None and iri not in recommended_apply_or_restage_review:
                recommended_apply_or_restage_review.append(iri)

        def recommend_repair(iri: str | None) -> None:
            recommend_mutation(iri)
            if iri is not None and iri not in recommended_repair_review:
                recommended_repair_review.append(iri)

        def recommend_applied_inspection(iri: str | None) -> None:
            recommend(iri)
            if iri is not None and iri not in recommended_applied_inspection:
                recommended_applied_inspection.append(iri)

        def track_validation_failed(iri: str | None) -> None:
            if iri is not None and iri not in validation_failed:
                validation_failed.append(iri)

        def track_staged_validation_failed(iri: str | None) -> None:
            if iri is not None and iri not in staged_validation_failed:
                staged_validation_failed.append(iri)

        def track_parallel_applied_restage_successor(
            source_iri: str,
            successor_iri: str,
            applied_iri: str,
        ) -> None:
            route = (source_iri, successor_iri, applied_iri)
            if route not in parallel_applied_restage_successors:
                parallel_applied_restage_successors.append(route)
            recommend_applied_inspection(applied_iri)

        for summary in summaries:
            increment(apply_status_counts, summary.apply_status)
            state = summary.stale_resolution_state
            increment(state_counts, state)
            if summary.apply_status == "validation_failed":
                track_validation_failed(summary.revision_iri)
            if summary.staged_validation_conforms is False:
                track_staged_validation_failed(summary.revision_iri)
            for (
                source_iri,
                successor_iri,
                applied_iri,
            ) in self._parallel_applied_restage_successor_events(summary):
                track_parallel_applied_restage_successor(
                    source_iri,
                    successor_iri,
                    applied_iri,
                )

            if state in {"stale_unresolved", "restaged_successor_stale_unresolved"}:
                unresolved_stale.append(summary.revision_iri)
                recommend_mutation_by_decision(summary)
            elif state == "stale_handled_by_restage":
                handled_stale.append(summary.revision_iri)
                recommend(summary.current_restaged_by or summary.restaged_by)
            elif state == "restaged_successor_ready":
                ready_successors.append(summary.revision_iri)
                recommend_mutation_by_decision(summary)
            elif state == "validation_failed":
                track_validation_failed(summary.revision_iri)
                recommend_mutation_by_decision(summary)
            elif state in {"noop", "restaged_successor_noop"}:
                recommend(summary.revision_iri)
            elif state in {
                "ready",
                "not_ready",
                "not_available",
                "restaged_successor_not_ready",
            }:
                recommend_mutation_by_decision(summary)
            elif state == "restaged_successor_already_applied":
                recommend_applied_inspection(summary.revision_iri)
            elif state == "already_applied":
                recommend_applied_inspection(summary.revision_iri)

        post_apply_recheck = self._staged_revisions_post_apply_recheck_revision_iris(
            summaries
        )
        ready_applied_alternative_successors = (
            self._ready_restage_successor_alternative_to_applied_source_iris(
                summaries
            )
        )
        bundled_revision_iris = {summary.revision_iri for summary in summaries}
        external_recommended_review = [
            iri for iri in recommended_review if iri not in bundled_revision_iris
        ]
        next_action_queue_items: list[RevisionNextActionQueueItem] = []
        for summary in summaries:
            profile_gate = self._profile_revision_gate_fields(
                summary.profile_route_groups,
                application_status=summary.apply_status,
            )
            queue_item = self._revision_next_action_queue_item(
                row_iri=summary.revision_iri,
                next_action=summary.next_action,
                record_kind="staged_patch",
                application_status=summary.apply_status,
                application_decision=summary.apply_decision,
                stale_resolution_state=summary.stale_resolution_state,
                staged_validation_status=self._staged_validation_status(
                    conforms=summary.staged_validation_conforms,
                    result_count=summary.staged_validation_result_count,
                ),
                semantic_risk_level=summary.semantic_risk_level,
                semantic_risk_reasons=summary.semantic_risk_reasons,
                profile_route_keys=summary.profile_route_keys,
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
                alternative_gate=summary.alternative_gate,
            )
            if queue_item is not None:
                next_action_queue_items.append(queue_item)
        next_action_queue_items = (
            self._revision_next_action_queue_items_with_alternative_sets(
                next_action_queue_items,
                (
                    (
                        summary.revision_iri,
                        summary.alternative_to,
                        summary.current_alternative_to,
                    )
                    for summary in summaries
                ),
            )
        )
        mutation_frontier_iris = self._revision_mutation_frontier_iris(
            next_action_queue_items
        )
        review_sequence = self._staged_revisions_review_sequence(
            summaries=summaries,
            next_action_queue_items=next_action_queue_items,
            post_apply_recheck_revision_iris=post_apply_recheck,
        )
        changed_graph_counts = self._staged_revisions_changed_graph_counts(
            summaries
        )
        choose_one_groups = self._staged_revisions_choose_one_groups(summaries)
        modelling_choice_rows = self._staged_revisions_modelling_choice_rows(
            summaries=summaries,
            descriptions=descriptions,
            choose_one_groups=choose_one_groups,
            next_action_queue_items=next_action_queue_items,
        )
        modelling_choice_summary = self._staged_revisions_modelling_choice_summary(
            modelling_choice_rows,
            choose_one_groups=choose_one_groups,
        )
        next_action_queue_item_counts = (
            self._revision_next_action_queue_item_counts(
                next_action_queue_items
            )
        )
        shared_context_patch_summaries = (
            self._staged_revisions_shared_semantic_context_patch_summaries(
                descriptions
            )
        )
        shared_context_graphs = sorted(
            {
                graph
                for summary in summaries
                for graph in summary.shared_context_graphs
            }
        )
        shared_context_revision_iris = [
            summary.revision_iri
            for summary in summaries
            if summary.shared_context_patch_count > 0
        ]
        fallback_shared_context_iris = (
            shared_context_revision_iris[1:]
            if len(shared_context_revision_iris) > 1
            else []
        )
        shared_semantic_context_warnings = (
            self._staged_revisions_shared_semantic_context_warnings(
                affected_revision_iris=shared_context_revision_iris,
                shared_context_graphs=shared_context_graphs,
                shared_context_patch_summaries=shared_context_patch_summaries,
                fallback_revision_iris=fallback_shared_context_iris,
            )
        )
        return StagedGraphRevisionBundleSummary(
            total_revisions=len(summaries),
            decision_headline=self._staged_revisions_decision_headline(
                total_revisions=len(summaries),
                next_action_queue_item_counts=next_action_queue_item_counts,
                changed_graph_counts=changed_graph_counts,
                choose_one_group_count=len(choose_one_groups),
                snapshot_evidence=snapshot_evidence,
                requires_recheck_after_each_apply=bool(post_apply_recheck),
            ),
            apply_status_counts=apply_status_counts,
            stale_resolution_state_counts=state_counts,
            changed_graph_counts=changed_graph_counts,
            choose_one_groups=choose_one_groups,
            modelling_choice_summary=modelling_choice_summary,
            modelling_choice_rows=modelling_choice_rows,
            unresolved_stale_revision_iris=unresolved_stale,
            stale_handled_by_restage_revision_iris=handled_stale,
            ready_restage_successor_revision_iris=ready_successors,
            ready_restage_successor_alternative_to_applied_source_iris=(
                ready_applied_alternative_successors
            ),
            post_apply_recheck_revision_iris=post_apply_recheck,
            sequential_apply_recheck_candidate_iris=post_apply_recheck,
            warnings=[
                *self._staged_revisions_bundle_warnings(
                    post_apply_recheck,
                    snapshot_evidence=snapshot_evidence,
                    external_recommended_review_iris=external_recommended_review,
                    ready_restage_successor_alternative_to_applied_source_iris=(
                        ready_applied_alternative_successors
                    ),
                    parallel_applied_restage_successors=(
                        parallel_applied_restage_successors
                    ),
                ),
                *(
                    warning.message
                    for warning in shared_semantic_context_warnings
                ),
            ],
            validation_failed_revision_iris=validation_failed,
            staged_validation_failed_revision_iris=staged_validation_failed,
            recommended_review_iris=recommended_review,
            external_recommended_review_iris=external_recommended_review,
            recommended_mutation_review_iris=recommended_mutation_review,
            recommended_apply_or_restage_review_iris=(
                recommended_apply_or_restage_review
            ),
            recommended_repair_review_iris=recommended_repair_review,
            recommended_applied_inspection_iris=recommended_applied_inspection,
            review_sequence=review_sequence,
            next_action_queue=self._revision_next_action_queue(
                (summary.revision_iri, summary.next_action) for summary in summaries
            ),
            next_action_queue_items=next_action_queue_items,
            next_action_queue_item_counts=next_action_queue_item_counts,
            snapshot_evidence=snapshot_evidence,
            mutation_frontier_iris=mutation_frontier_iris,
            requires_recheck_after_each_apply=bool(post_apply_recheck),
            semantic_risk_queue_counts=self._semantic_risk_queue_counts(summaries),
            semantic_review_required_queue_counts=(
                self._semantic_review_required_queue_counts(
                    next_action_queue_items
                )
            ),
            shared_context_graphs=shared_context_graphs,
            shared_context_patch_summaries=shared_context_patch_summaries,
            fallback_revision_iris_with_shared_semantic_context=(
                fallback_shared_context_iris
            ),
            shared_semantic_context_warnings=shared_semantic_context_warnings,
        )
    def _staged_revisions_bundle_warnings(
        self,
        post_apply_recheck_revision_iris: list[str],
        *,
        snapshot_evidence: StagedGraphRevisionSnapshotEvidenceSummary | None = None,
        external_recommended_review_iris: list[str] | None = None,
        ready_restage_successor_alternative_to_applied_source_iris: (
            list[str] | None
        ) = None,
        parallel_applied_restage_successors: (
            list[tuple[str, str, str]] | None
        ) = None,
    ) -> list[str]:
        warnings: list[str] = []
        if (
            snapshot_evidence is not None
            and snapshot_evidence.rows
            and not snapshot_evidence.complete
        ):
            warnings.append(
                "Snapshot evidence is incomplete for staged review row(s): "
                f"{', '.join(snapshot_evidence.incomplete_revision_iris)}. "
                "Import companion revision snapshot JSON before relying on exact "
                "applied-diff or stale-drift triples; Review Queues and Resolved "
                "Targets remain post-preflight mutation routes."
            )
        if post_apply_recheck_revision_iris:
            warnings.append(
                "Ready/no-op staged revisions sharing a changed graph are "
                "sequential review targets: applying one ready revision can "
                "change graph state and make sibling ready or no-op revisions "
                "stale. Re-run apply_staged_revision with dry_run=true or "
                "export_bundle(kind='staged_revisions') after each apply."
            )
        if external_recommended_review_iris:
            warnings.append(
                "Recommended review includes revision(s) outside this bundle: "
                f"{', '.join(external_recommended_review_iris)}. Export or "
                "describe them before acting on this review bundle."
            )
        if ready_restage_successor_alternative_to_applied_source_iris:
            affected = ", ".join(
                ready_restage_successor_alternative_to_applied_source_iris
            )
            warnings.append(
                "Ready restage successor(s) are mechanically apply-ready but "
                "remain alternatives to already-applied staged source(s): "
                f"{affected}. "
                "Treat them as semantic review targets before applying; inspect "
                "each row's current_alternative_to/applied source before making "
                "both alternatives durable."
            )
        if parallel_applied_restage_successors:
            routes = "; ".join(
                f"{source_iri} -> {successor_iri} -> {applied_iri}"
                for (
                    source_iri,
                    successor_iri,
                    applied_iri,
                ) in parallel_applied_restage_successors
            )
            warnings.append(
                "Parallel restage successor branch(es) already have applied "
                "events outside the followed current route: "
                f"{routes}. Inspect the applied event(s) before following the "
                "current successor route."
            )
        return warnings
    def _staged_revision_impacts(
        self,
        *,
        revision_iri: str,
        patches: list[StagedGraphPatchDescription],
        lookup_graphs: list[str],
    ) -> list[StagedRevisionImpact]:
        addition_operation = self.expand_iri("rc:AdditionPatch")
        removal_operation = self.expand_iri("rc:RemovalPatch")
        tracked_predicates: dict[str, tuple[str, str]] = {
            self.expand_iri("rc:physicalType"): (
                "changed_physical_type",
                "physical type",
            ),
            self.expand_iri("rc:valueType"): ("changed_value_type", "value type"),
            self.expand_iri("rc:nullable"): ("changed_nullable", "nullable flag"),
            self.expand_iri("rc:rowSemantics"): (
                "changed_row_semantics",
                "row semantics",
            ),
            self.expand_iri("rc:entityKey"): ("changed_row_key", "entity key"),
            self.expand_iri("rc:snapshotTimestamp"): (
                "changed_row_key",
                "snapshot timestamp",
            ),
            self.expand_iri("rc:groupByColumn"): (
                "changed_grouping",
                "group-by column",
            ),
            self.expand_iri("rc:pathTemplate"): (
                "changed_layout_or_path",
                "path template",
            ),
            self.expand_iri("rc:locationKind"): (
                "changed_layout_or_path",
                "storage location kind",
            ),
            self.expand_iri("rc:layoutVerificationStatus"): (
                "changed_layout_or_path",
                "layout verification status",
            ),
            self.expand_iri("rc:layoutVerificationNote"): (
                "changed_layout_or_path",
                "layout verification note",
            ),
            self.expand_iri("rc:hasStorageAccess"): (
                "changed_layout_or_path",
                "storage access",
            ),
            self.expand_iri("rc:hasPhysicalLayout"): (
                "changed_layout_or_path",
                "physical layout",
            ),
            self.expand_iri("rc:hasRelationship"): (
                "changed_relationship",
                "relationship link",
            ),
            self.expand_iri("rc:foreignKeyFrom"): (
                "changed_relationship",
                "foreign-key source column",
            ),
            self.expand_iri("rc:foreignKeyTo"): (
                "changed_relationship",
                "foreign-key target column",
            ),
            self.expand_iri("rc:sourceDataset"): (
                "changed_relationship",
                "source dataset",
            ),
            self.expand_iri("rc:targetDataset"): (
                "changed_relationship",
                "target dataset",
            ),
        }
        documentation_predicates: dict[str, tuple[str, str]] = {
            str(RDFS.comment): ("changed_documentation", "documentation comment"),
            str(DCTERMS.description): ("changed_documentation", "description"),
        }
        caveat_predicate = self.expand_iri("rc:hasKnownCaveat")
        changes: dict[
            tuple[str, Node, Node],
            dict[str, list[Node]],
        ] = {}

        for patch in patches:
            operation = patch.operation
            if operation is None:
                continue
            try:
                target_graph = self._required_staged_patch_target_graph(patch)
                patch_graph = self._parse_staged_patch_description(patch)
            except DoxaBaseError:
                continue
            change_key = "added" if operation == addition_operation else "removed"
            if operation not in {addition_operation, removal_operation}:
                continue
            for subject, predicate, value in patch_graph:
                bucket = changes.setdefault(
                    (target_graph, subject, predicate),
                    {"removed": [], "added": []},
                )
                if value not in bucket[change_key]:
                    bucket[change_key].append(value)

        impacts: list[StagedRevisionImpact] = []
        semantic_change_subjects = {
            (changed_graph, subject)
            for (changed_graph, subject, predicate), values in changes.items()
            if (
                values["removed"]
                or values["added"]
            )
            and (
                str(predicate) == caveat_predicate
                or str(predicate) in tracked_predicates
            )
        }
        for (changed_graph, subject, predicate), values in sorted(
            changes.items(),
            key=lambda item: (
                item[0][0],
                str(item[0][1]),
                str(item[0][2]),
            ),
        ):
            removed_values = values["removed"]
            added_values = values["added"]
            if not removed_values and not added_values:
                continue
            if str(predicate) == caveat_predicate:
                for caveat_value in removed_values:
                    impacts.append(
                        self._staged_revision_impact(
                            impact_type="removed_caveat",
                            severity="attention",
                            changed_graph=changed_graph,
                            subject=subject,
                            predicate=predicate,
                            removed_values=[caveat_value],
                            added_values=[],
                            lookup_graphs=lookup_graphs,
                            revision_iri=revision_iri,
                            message_template=(
                                "Removes known caveat {removed} from {subject}. "
                                "Review related observations, claims, patterns, and "
                                "evidence before treating this as cleanup."
                            ),
                        )
                    )
                for caveat_value in added_values:
                    impacts.append(
                        self._staged_revision_impact(
                            impact_type="added_caveat",
                            severity="context",
                            changed_graph=changed_graph,
                            subject=subject,
                            predicate=predicate,
                            removed_values=[],
                            added_values=[caveat_value],
                            lookup_graphs=lookup_graphs,
                            revision_iri=revision_iri,
                            message_template=(
                                "Adds known caveat {added} to {subject}. Related lore "
                                "may explain why this fence is being installed."
                            ),
                        )
                    )
                continue

            predicate_info = tracked_predicates.get(str(predicate))
            if predicate_info is None:
                predicate_info = documentation_predicates.get(str(predicate))
                if (
                    predicate_info is None
                    or (changed_graph, subject) not in semantic_change_subjects
                ):
                    continue
            impact_type, predicate_label = predicate_info
            if removed_values and added_values:
                message_template = (
                    f"Changes {predicate_label} on {{subject}} from "
                    "{removed} to {added}. Review attached lore before assuming "
                    "the new framing is merely tidier."
                )
                severity = "attention"
            elif removed_values:
                message_template = (
                    f"Removes {predicate_label} {{removed}} from {{subject}}. "
                    "Check whether related lore depended on that assertion."
                )
                severity = "attention"
            else:
                message_template = (
                    f"Adds {predicate_label} {{added}} to {{subject}}. "
                    "Check whether related lore changes how this should be read."
                )
                severity = "context"
            impacts.append(
                self._staged_revision_impact(
                    impact_type=impact_type,
                    severity=severity,
                    changed_graph=changed_graph,
                    subject=subject,
                    predicate=predicate,
                    removed_values=removed_values,
                    added_values=added_values,
                    lookup_graphs=lookup_graphs,
                    revision_iri=revision_iri,
                    message_template=message_template,
                )
            )

        return impacts
    def _staged_revision_related_lore(
        self,
        target_iris: Iterable[str],
        *,
        exclude_revision_iri: str | None = None,
    ) -> dict[str, list[ResourceSummary]]:
        targets = [
            iri
            for iri in dict.fromkeys(target_iris)
            if iri and not iri.startswith("_:")
        ]
        all_graphs = self._expand_graphs(["all"])
        pattern_graphs = self._expand_graphs(["patterns"])
        history_graphs = self._expand_graphs(["history"])
        lookup_graphs = self._lookup_graphs(all_graphs)

        observation_iris: set[str] = set()
        claim_iris: set[str] = set()
        pattern_iris: set[str] = set()
        evidence_iris: set[str] = set()
        revision_iris: set[str] = set()

        observation_type = self.expand_iri("rc:Observation")
        claim_type = self.expand_iri("rc:Claim")
        pattern_type = self.expand_iri("rc:Pattern")
        evidence_type = self.expand_iri("rc:Evidence")

        for target_iri in targets:
            target_types = set(self._types_from_graphs(all_graphs, target_iri))
            if observation_type in target_types:
                observation_iris.add(target_iri)
            if claim_type in target_types:
                claim_iris.add(target_iri)
            if pattern_type in target_types:
                pattern_iris.add(target_iri)
            if evidence_type in target_types:
                evidence_iris.add(target_iri)

            for predicate in ("rc:observedAsset", "rc:observedColumn"):
                observation_iris.update(
                    self._subjects(all_graphs, predicate, target_iri)
                )
            claim_iris.update(self._subjects(all_graphs, "rc:claimTarget", target_iri))
            pattern_iris.update(
                self._subjects(pattern_graphs, "rc:patternTarget", target_iri)
            )
            pattern_iris.update(
                self._subjects(pattern_graphs, "rc:mapImplication", target_iri)
            )
            revision_iris.update(
                self._subjects(history_graphs, "rc:revisionAnchor", target_iri)
            )
            evidence_iris.update(self._objects(all_graphs, target_iri, "rc:evidence"))

        for observation_iri in list(observation_iris):
            claim_iris.update(self._objects(all_graphs, observation_iri, "rc:hasClaim"))
            evidence_iris.update(
                self._objects(all_graphs, observation_iri, "rc:evidence")
            )
            pattern_iris.update(
                self._subjects(
                    pattern_graphs,
                    "rc:supportingObservation",
                    observation_iri,
                )
            )
            revision_iris.update(
                self._subjects(
                    history_graphs,
                    "rc:revisionSupportingObservation",
                    observation_iri,
                )
            )

        for claim_iri in list(claim_iris):
            evidence_iris.update(self._objects(all_graphs, claim_iri, "rc:evidence"))
            pattern_iris.update(
                self._subjects(pattern_graphs, "rc:supportingClaim", claim_iri)
            )
            revision_iris.update(
                self._subjects(
                    history_graphs,
                    "rc:revisionSupportingClaim",
                    claim_iri,
                )
            )

        for pattern_iri in list(pattern_iris):
            evidence_iris.update(self._objects(all_graphs, pattern_iri, "rc:evidence"))
            revision_iris.update(
                self._subjects(
                    history_graphs,
                    "rc:revisionSupportingPattern",
                    pattern_iri,
                )
            )

        for evidence_iri in list(evidence_iris):
            revision_iris.update(
                self._subjects(history_graphs, "rc:evidence", evidence_iri)
            )

        if exclude_revision_iri is not None:
            revision_iris.discard(exclude_revision_iri)

        return {
            "observations": self._resource_summaries(
                lookup_graphs,
                sorted(observation_iris),
                description_predicate="rc:summary",
            ),
            "claims": self._resource_summaries(
                lookup_graphs,
                sorted(claim_iris),
                description_predicate="rc:claimText",
            ),
            "patterns": self._resource_summaries(
                lookup_graphs,
                sorted(pattern_iris),
                description_predicate="rc:patternText",
            ),
            "evidence": self._resource_summaries(
                lookup_graphs,
                sorted(evidence_iris),
                description_predicate="rc:summary",
            ),
            "revisions": self._resource_summaries(
                lookup_graphs,
                sorted(revision_iris),
                description_predicate="rc:summary",
            ),
        }
    def _preview_staged_graph_patches(
        self,
        parsed_patches: list[dict[str, Any]],
        *,
        validation_scope: str,
        revision_has_support_metadata: bool,
    ) -> _StagedGraphPatchPreview:
        changed_graphs = list(
            dict.fromkeys(str(patch["target_graph"]) for patch in parsed_patches)
        )
        for graph_name in changed_graphs:
            self._ensure_mutable(graph_name)

        preview_graphs: dict[str, Graph] = {
            graph_name: self.to_graph([graph_name])
            for graph_name in changed_graphs
        }
        patch_records: list[StagedGraphPatchRecord] = []
        for sequence_index, patch in enumerate(parsed_patches, start=1):
            target_graph = str(patch["target_graph"])
            patch_graph = patch["graph"]
            if not isinstance(patch_graph, Graph):
                raise DoxaBaseError("Internal staged patch parse error")
            preview = preview_graphs[target_graph]
            before_count = len(preview)
            if patch["operation"] == self.expand_iri("rc:AdditionPatch"):
                for triple in patch_graph:
                    preview.add(triple)
            else:
                for triple in patch_graph:
                    preview.remove(triple)
            after_count = len(preview)
            patch_records.append(
                StagedGraphPatchRecord(
                    patch_iri=str(patch["patch_iri"]),
                    operation=str(patch["operation"]),
                    target_graph=target_graph,
                    count_basis=self._staged_patch_count_basis(target_graph),
                    format=str(patch["format"]),
                    patch_role=str(patch["patch_role"]),
                    sequence_index=sequence_index,
                    triple_count=len(patch_graph),
                    before_triple_count=before_count,
                    after_triple_count=after_count,
                )
            )

        validation = self._validate_graph_preview(
            validation_scope,
            preview_graphs=preview_graphs,
        )
        patch_descriptions = [
            StagedGraphPatchDescription(
                iri=patch_record.patch_iri,
                operation=patch_record.operation,
                operation_label=self._label_for_resource(patch_record.operation),
                target_graph=patch_record.target_graph,
                count_basis=patch_record.count_basis,
                format=patch_record.format,
                patch_role=patch_record.patch_role,
                patch_role_label=self._label_for_resource(patch_record.patch_role),
                sequence_index=patch_record.sequence_index,
                triple_count=patch_record.triple_count,
                before_triple_count=patch_record.before_triple_count,
                after_triple_count=patch_record.after_triple_count,
                content=str(patch["content"]),
            )
            for patch, patch_record in zip(
                parsed_patches,
                patch_records,
                strict=True,
            )
        ]
        validation = replace(
            validation,
            results=self._enrich_staged_validation_hints(
                validation.results,
                patches=patch_descriptions,
                revision_has_support_metadata=revision_has_support_metadata,
            ),
        )
        return _StagedGraphPatchPreview(
            changed_graphs=changed_graphs,
            patch_records=patch_records,
            patch_descriptions=patch_descriptions,
            validation=validation,
        )
    def _staged_revision_markdown(
        self,
        description: StagedGraphRevisionDescription,
        *,
        apply_check: StagedRevisionApplyCheck | None = None,
        apply_check_error: str | None = None,
        include_heading: bool = True,
    ) -> str:
        lines: list[str] = []
        if include_heading:
            lines.extend(
                [
                    f"# {description.summary or 'Staged graph revision'}",
                    "",
                ]
            )
        semantic_warning = self._semantic_review_warning_markdown(
            description.judgement_panel,
            apply_check=apply_check,
        )
        if semantic_warning:
            semantic_warning.append("")
        stored_review_context = self._staged_revision_stored_review_context_markdown(
            description.stored_review_context
        )
        if stored_review_context:
            stored_review_context.append("")
        metadata_lines = [
            f"- Revision: `{description.iri}`",
            (
                "- Stance: "
                f"{description.revision_stance_label or description.revision_stance or 'unknown'}"
            ),
            (
                "- Type: "
                f"{description.revision_type_label or description.revision_type or 'unknown'}"
            ),
            f"- Changed graphs: {', '.join(description.changed_graphs)}",
            (
                f"- Validation: {description.validation_scope or 'unknown'} "
                f"conforms={description.validation_conforms} "
                f"results={description.validation_result_count}"
            ),
        ]
        if description.restaged_by is not None:
            metadata_lines.append(
                "- Restaged by: "
                f"{description.restaged_by.label or description.restaged_by.iri} "
                f"(`{description.restaged_by.iri}`)"
            )
            if (
                description.current_restaged_by is not None
                and description.current_restaged_by.iri != description.restaged_by.iri
            ):
                current_label = (
                    description.current_restaged_by.label
                    or description.current_restaged_by.iri
                )
                metadata_lines.append(
                    "- Current restaged by: "
                    f"{current_label} "
                    f"(`{description.current_restaged_by.iri}`)"
                )
        if description.restage_reason is not None:
            metadata_lines.append(f"- Restage headline: {description.restage_reason}")
        lines.extend(
            [
                *metadata_lines,
                "",
                *semantic_warning,
                *stored_review_context,
                *self._staged_apply_check_markdown(
                    apply_check,
                    apply_check_error=apply_check_error,
                    alternative_to=description.alternative_to,
                ),
                "",
                "## Rationale",
                "",
                description.rationale or "",
            ]
        )
        if description.review_note is not None:
            lines.extend(["", "## Review Note", "", description.review_note])
        if description.review_recommendation is not None:
            lines.extend(
                [
                    "",
                    "## Review Recommendation",
                    "",
                    description.review_recommendation,
                ]
            )
        if description.judgement_panel is not None:
            lines.extend(["", "## Judgement Panel", ""])
            lines.extend(
                self._map_assertion_judgement_panel_markdown(
                    description.judgement_panel
                )
            )
        if description.impacts:
            lines.extend(["", "## Impact Review", ""])
            for impact in description.impacts:
                lines.extend(self._staged_revision_impact_markdown(impact))
        linked_support = self._staged_revision_linked_support_markdown(description)
        if linked_support:
            lines.extend(["", "## Linked Support", "", *linked_support])
        if description.alternative_to is not None:
            lines.extend(
                [
                    "",
                    "## Alternative To",
                    "",
                    (
                        f"- {description.alternative_to.label or description.alternative_to.iri} "
                        f"(`{description.alternative_to.iri}`)"
                    ),
                ]
            )
        if description.restaged_from is not None:
            lines.extend(
                [
                    "",
                    "## Restaged From",
                    "",
                    (
                        f"- {description.restaged_from.label or description.restaged_from.iri} "
                        f"(`{description.restaged_from.iri}`)"
                    ),
                ]
            )
            if description.restage_reason is not None:
                lines.append(f"- Reason: {description.restage_reason}")
        if description.revision_anchors:
            lines.extend(["", "## Revision Anchors", ""])
            for anchor in description.revision_anchors:
                lines.append(f"- {anchor.label or anchor.iri} (`{anchor.iri}`)")
        if description.validation_results:
            lines.extend(["", "## Validation Results", ""])
            for index, result in enumerate(description.validation_results, start=1):
                lines.extend(
                    [
                        f"### Result {index}",
                        "",
                        f"- IRI: `{result.iri}`",
                    ]
                )
                if result.focus_node is not None:
                    lines.append(
                        "- Focus node: "
                        + self._diagnostic_markdown_resource(
                            result.focus_node,
                            result.focus_node_label,
                        )
                    )
                if result.result_path is not None:
                    lines.append(
                        "- Result path: "
                        + self._diagnostic_markdown_resource(
                            result.result_path,
                            result.result_path_label,
                        )
                    )
                if result.value is not None:
                    lines.append(f"- Value: `{result.value}`")
                if result.source_constraint_component is not None:
                    lines.append(
                        "- Constraint: "
                        + self._diagnostic_markdown_resource(
                            result.source_constraint_component,
                            result.source_constraint_component_label,
                        )
                    )
                if result.severity is not None:
                    lines.append(
                        "- Severity: "
                        + self._diagnostic_markdown_resource(
                            result.severity,
                            result.severity_label,
                        )
                    )
                if result.source_shape is not None:
                    lines.append(f"- Source shape: `{result.source_shape}`")
                for message in result.messages:
                    lines.append(f"- Message: {message}")
                if result.hint is not None:
                    lines.append(f"- Hint: {result.hint}")
                lines.append("")
        lines.extend(["", "## Patches", ""])
        for index, patch in enumerate(description.patches, start=1):
            lines.extend(
                [
                    f"### Patch {index}: {patch.operation_label or patch.operation}",
                    "",
                    f"- IRI: `{patch.iri}`",
                    f"- Target graph: `{patch.target_graph}`",
                    f"- Count basis: `{patch.count_basis or 'unknown'}`",
                    f"- Format: `{patch.format}`",
                    f"- Role: {patch.patch_role_label or patch.patch_role or 'unknown'}",
                    f"- Sequence: {patch.sequence_index or 'unknown'}",
                    f"- Triples: {patch.triple_count}",
                    (
                        f"- Count preview: {patch.before_triple_count} -> "
                        f"{patch.after_triple_count}"
                    ),
                    "",
                    f"```{patch.format or 'turtle'}",
                    patch.content or "",
                    "```",
                    "",
                ]
            )
        return "\n".join(lines).rstrip() + "\n"
    def _semantic_review_warning_markdown(
        self,
        panel: MapAssertionJudgementPanel | None,
        *,
        apply_check: StagedRevisionApplyCheck | None = None,
    ) -> list[str]:
        if panel is not None and panel.semantic_risk_level != "none":
            level = panel.semantic_risk_level
            reasons = panel.semantic_risk_reasons
            source_note = None
        elif apply_check is not None and apply_check.semantic_risk_level != "none":
            level = apply_check.semantic_risk_level
            reasons = apply_check.semantic_risk_reasons
            if apply_check.status == "conflict":
                source_note = (
                    "The compact judgement panel is unavailable because this "
                    "staged revision cannot currently replay cleanly; this "
                    "warning is reconstructed from stored review context."
                )
            else:
                source_note = (
                    "The compact judgement panel is unavailable; this warning "
                    "is reconstructed from stored review context."
                )
        else:
            return []
        lines = [
            "## Semantic Review Warning",
            "",
            f"- Level: {level}",
            (
                "- Meaning: mechanical replay or validation status is not "
                "semantic approval; nearby or stored lore says this staged "
                "revision needs semantic review."
            ),
        ]
        if source_note:
            lines.append(f"- Source: {source_note}")
        if reasons:
            lines.append("- Reasons:")
            lines.extend(f"  - {reason}" for reason in reasons)
        return lines
    def _staged_revisions_markdown(
        self,
        descriptions: list[StagedGraphRevisionDescription],
        *,
        apply_checks: list[tuple[StagedRevisionApplyCheck | None, str | None]],
        revision_summaries: list[StagedGraphRevisionExportSummary],
        bundle_summary: StagedGraphRevisionBundleSummary,
        snapshot_evidence_summary: StagedGraphRevisionSnapshotEvidenceSummary,
        title: str | None,
        executive_summary: str | None,
    ) -> str:
        title_text = title.strip() if title and title.strip() else "Staged revision bundle"
        lines = [
            f"# {title_text}",
            "",
        ]
        executive_summary_text = (
            executive_summary.strip() if executive_summary is not None else None
        )
        if executive_summary_text:
            lines.extend(["## Review Summary", "", executive_summary_text, ""])
        at_a_glance = self._staged_revisions_at_a_glance_markdown(bundle_summary)
        if at_a_glance:
            lines.extend(["## At A Glance", ""])
            lines.extend(at_a_glance)
            lines.append("")
        modelling_choices = self._staged_revisions_modelling_choice_markdown(
            bundle_summary
        )
        if modelling_choices:
            lines.extend(["## Modelling Choice Summary", ""])
            lines.extend(modelling_choices)
            lines.append("")
        if bundle_summary.warnings:
            lines.extend(["## Bundle Warnings", ""])
            lines.extend(f"- {warning}" for warning in bundle_summary.warnings)
            lines.append("")
        decision_matrix = self._staged_revisions_reviewer_decision_matrix_markdown(
            descriptions,
            revision_summaries,
        )
        if decision_matrix:
            lines.extend(["## Reviewer Decision Matrix", ""])
            lines.extend(decision_matrix)
            lines.append("")
        lines.extend(
            [
                "## Summary",
                "",
                (
                    "| # | Summary | Stance | Changed graphs | Apply status | "
                    "Decision | Current validation | Staged validation | "
                    "Staged results | Diagnostics | Recommendation |"
                ),
                "|---|---|---|---|---|---|---|---|---:|---|---|",
            ]
        )
        for index, description in enumerate(descriptions, start=1):
            apply_check, apply_check_error = apply_checks[index - 1]
            summary = revision_summaries[index - 1]
            apply_status = (
                apply_check.status
                if apply_check is not None
                else f"unavailable: {apply_check_error or 'unknown'}"
            )
            apply_decision = apply_check.decision if apply_check is not None else ""
            current_validation = self._staged_apply_check_validation_cell(
                apply_check,
                apply_check_error=apply_check_error,
            )
            recommendation = summary.summary_recommendation
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(index),
                        self._markdown_table_cell(description.summary or description.iri),
                        self._markdown_table_cell(
                            description.revision_stance_label
                            or description.revision_stance
                            or "unknown"
                        ),
                        self._markdown_table_cell(
                            ", ".join(description.changed_graphs) or "none"
                        ),
                        self._markdown_table_cell(apply_status),
                        self._markdown_table_cell(apply_decision),
                        self._markdown_table_cell(current_validation),
                        self._markdown_table_cell(
                            self._staged_description_validation_cell(description)
                        ),
                        str(description.validation_result_count),
                        self._markdown_table_cell(
                            self._validation_diagnostic_headline(description)
                        ),
                        self._markdown_table_cell(recommendation),
                    ]
                )
                + " |"
            )
        count_basis_context = self._staged_revisions_count_basis_markdown(
            descriptions
        )
        if count_basis_context:
            lines.extend(["", "## Count Basis Context", ""])
            lines.extend(count_basis_context)
        snapshot_evidence = self._staged_revisions_snapshot_evidence_markdown(
            snapshot_evidence_summary
        )
        if snapshot_evidence:
            lines.extend(["", "## Snapshot Evidence", ""])
            lines.extend(snapshot_evidence)
        review_sequence = self._staged_revisions_review_sequence_markdown(
            bundle_summary
        )
        if review_sequence:
            lines.extend(["", "## Review Sequence", ""])
            lines.extend(review_sequence)
        profile_route_bridge = self._staged_revisions_profile_route_bridge_markdown(
            revision_summaries
        )
        if profile_route_bridge:
            lines.extend(["", "## Profile Route Bridge", ""])
            lines.extend(profile_route_bridge)
        review_queues = self._staged_revisions_review_queues_markdown(bundle_summary)
        if review_queues:
            lines.extend(["", "## Review Queues", ""])
            lines.extend(review_queues)
        resolved_targets = self._staged_revisions_resolved_targets_markdown(
            bundle_summary,
        )
        if resolved_targets:
            lines.extend(["", "## Resolved Targets", ""])
            lines.extend(resolved_targets)
        restage_context = []
        for index, description in enumerate(descriptions, start=1):
            if description.restage_reason is not None:
                label = description.summary or description.iri
                if description.restaged_from is not None:
                    source = (
                        description.restaged_from.label
                        or description.restaged_from.iri
                    )
                    restage_context.append(
                        (
                            f"{index}. {label}: Restaged from {source} "
                            f"(`{description.restaged_from.iri}`); "
                            "prior/source apply-check context: "
                            f"{description.restage_reason}"
                        )
                    )
                else:
                    restage_context.append(
                        f"{index}. {label}: {description.restage_reason}"
                    )
            elif description.restaged_from is not None:
                label = description.summary or description.iri
                source = description.restaged_from.label or description.restaged_from.iri
                restage_context.append(
                    (
                        f"{index}. {label}: Restaged from {source} "
                        f"(`{description.restaged_from.iri}`); see rationale for details."
                    )
                )
        if restage_context:
            lines.extend(["", "## Restage Context", ""])
            lines.extend(restage_context)
        alternative_context = self._staged_revisions_alternative_context_markdown(
            descriptions,
            revision_summaries,
        )
        if alternative_context:
            lines.extend(["", "## Alternative Context", ""])
            lines.extend(alternative_context)
        if any(description.review_note for description in descriptions):
            lines.extend(["", "## Review Notes", ""])
            for index, description in enumerate(descriptions, start=1):
                if description.review_note:
                    label = description.summary or description.iri
                    lines.append(f"{index}. {label}: {description.review_note}")
        if any(description.impacts for description in descriptions):
            lines.extend(["", "## Impact Review", ""])
            for index, description in enumerate(descriptions, start=1):
                if not description.impacts:
                    continue
                label = description.summary or description.iri
                lines.append(f"### {index}. {label}")
                lines.append("")
                for impact in description.impacts:
                    lines.append(f"- {impact.message}")
        lines.extend(["", "## Revisions", ""])
        for index, description in enumerate(descriptions, start=1):
            lines.extend(
                [
                    f"## Revision {index}: {description.summary or description.iri}",
                    "",
                    self._staged_revision_markdown(
                        description,
                        apply_check=apply_checks[index - 1][0],
                        apply_check_error=apply_checks[index - 1][1],
                        include_heading=False,
                    ).strip(),
                    "",
                ]
        )
        return "\n".join(lines).rstrip() + "\n"
    def _describe_staged_graph_patch(
        self,
        patch_iri: str,
        graphs: list[str],
    ) -> StagedGraphPatchDescription:
        operation = self._first_object(graphs, patch_iri, "rc:patchOperation")
        patch_role = self._first_object(graphs, patch_iri, "rc:patchRole")
        target_graph = self._first_object(graphs, patch_iri, "rc:targetGraph")
        return StagedGraphPatchDescription(
            iri=patch_iri,
            operation=operation,
            operation_label=self._label_for_resource(operation),
            target_graph=target_graph,
            count_basis=self._staged_patch_count_basis(target_graph),
            format=self._first_object(graphs, patch_iri, "rc:patchFormat"),
            patch_role=patch_role,
            patch_role_label=self._label_for_resource(patch_role),
            sequence_index=self._int_object(graphs, patch_iri, "rc:patchSequence"),
            triple_count=self._int_object(graphs, patch_iri, "rc:patchTripleCount"),
            before_triple_count=self._int_object(
                graphs,
                patch_iri,
                "rc:beforeTripleCount",
            ),
            after_triple_count=self._int_object(
                graphs,
                patch_iri,
                "rc:afterTripleCount",
            ),
            content=self._first_object(graphs, patch_iri, "rc:patchContent"),
        )
