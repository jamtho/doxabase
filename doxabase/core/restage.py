"""Restaging staged revisions after drift.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via RestageMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class RestageMixin:
    def _revision_lineage_restage_chain(
        self,
        seed: GraphRevisionListItem,
        by_iri: dict[str, GraphRevisionListItem],
    ) -> tuple[list[GraphRevisionListItem], list[str]]:
        ancestors: list[GraphRevisionListItem] = []
        seen = {seed.iri}
        warnings: list[str] = []
        current = seed
        while current.restaged_from is not None:
            if current.restaged_from not in by_iri:
                warnings.append(
                    "Restage lineage points to missing source "
                    f"'{current.restaged_from}'."
                )
                break
            if current.restaged_from in seen:
                warnings.append(
                    "Restage lineage cycle detected at "
                    f"'{current.restaged_from}'."
                )
                break
            current = by_iri[current.restaged_from]
            ancestors.append(current)
            seen.add(current.iri)
        chain = list(reversed(ancestors)) + [seed]
        current = seed
        while current.restaged_by is not None:
            if current.restaged_by not in by_iri:
                warnings.append(
                    "Restage lineage points to missing successor "
                    f"'{current.restaged_by}'."
                )
                break
            if current.restaged_by in seen:
                warnings.append(
                    "Restage lineage cycle detected at "
                    f"'{current.restaged_by}'."
                )
                break
            current = by_iri[current.restaged_by]
            chain.append(current)
            seen.add(current.iri)
        for item in chain:
            if item.record_kind != "staged_patch":
                warnings.append(
                    "Restage lineage includes non-staged revision "
                    f"'{item.iri}' with record_kind='{item.record_kind}'."
                )
            successors = self._revision_lineage_visible_restage_successors(
                item,
                by_iri,
            )
            if len(successors) > 1:
                followed = item.restaged_by or successors[0].iri
                warnings.append(
                    "Restage lineage has multiple visible successors for "
                    f"'{item.iri}': "
                    f"{', '.join(successor.iri for successor in successors)}. "
                    f"The current route follows '{followed}'."
                )
        return chain, warnings
    @staticmethod
    def _revision_lineage_visible_restage_successors(
        source: GraphRevisionListItem,
        by_iri: dict[str, GraphRevisionListItem],
    ) -> list[GraphRevisionListItem]:
        return sorted(
            (
                item
                for item in by_iri.values()
                if item.restaged_from == source.iri
            ),
            key=lambda item: item.iri,
        )
    def _current_restage_successor_iri(
        self,
        iri: str,
        *,
        graphs: list[str] | None = None,
    ) -> str | None:
        lookup_graphs = graphs or self._expand_graphs(["history"])
        seen = {iri}
        current_iri = iri
        latest_successor: str | None = None
        while True:
            successor = self._first_subject(
                lookup_graphs,
                "rc:restagesRevision",
                current_iri,
            )
            if successor is None or successor in seen:
                return latest_successor
            latest_successor = successor
            current_iri = successor
            seen.add(successor)
    def _stale_resolution_state(
        self,
        *,
        status: str | None,
        has_patch_payload: bool,
        restaged_from: str | None,
        restaged_by: str | None,
    ) -> str | None:
        if not has_patch_payload:
            return None
        if restaged_by is not None:
            return "stale_handled_by_restage"
        if status == "conflict":
            if restaged_from is not None and restaged_by is None:
                return "restaged_successor_stale_unresolved"
            return (
                "stale_handled_by_restage"
                if restaged_by is not None
                else "stale_unresolved"
            )
        if status == "superseded_by_restage":
            return "stale_handled_by_restage"
        if restaged_from is not None:
            if status == "ready":
                return "restaged_successor_ready"
            if status == "noop":
                return "restaged_successor_noop"
            if status == "already_applied":
                return "restaged_successor_already_applied"
            return "restaged_successor_not_ready"
        if status in {
            "ready",
            "noop",
            "already_applied",
            "validation_failed",
            "not_ready",
            "not_available",
        }:
            return status
        return None
    def _staged_revision_restage_reason(
        self,
        *,
        restaged_from: ResourceSummary | None,
        rationale: str | None,
    ) -> str | None:
        if restaged_from is None:
            return None
        source_label = restaged_from.label or restaged_from.iri
        fallback = f"Restaged from {source_label}; see rationale for details."
        if not rationale:
            return fallback

        lines = [line.strip() for line in rationale.splitlines()]
        status = self._restage_rationale_field(lines, "- status:")
        decision = self._restage_rationale_field(lines, "- decision:")
        blockers = self._restage_rationale_field(lines, "- blocking reasons:")
        summary = self._restage_rationale_field(lines, "- summary:")

        if not any([status, decision, blockers, summary]):
            first_line = next((line for line in lines if line), None)
            if first_line:
                return self._compact_restage_reason(first_line)
            return fallback

        parts = [f"Restaged from {source_label}"]
        if status:
            parts.append(f"after prior status {status}")
        if decision:
            parts.append(f"decision {decision}")
        if blockers and blockers != "(none)":
            parts.append(f"blockers {blockers}")
        reason = "; ".join(parts) + "."
        if summary:
            reason = f"{reason} {summary}"
        return self._compact_restage_reason(reason)
    @staticmethod
    def _restage_rationale_field(lines: Iterable[str], prefix: str) -> str | None:
        for line in lines:
            if line.startswith(prefix):
                value = line[len(prefix) :].strip()
                return value or None
        return None
    @staticmethod
    def _compact_restage_reason(reason: str, *, limit: int = 420) -> str:
        compact = " ".join(reason.split())
        if len(compact) <= limit:
            return compact
        return compact[: limit - 3].rstrip() + "..."
    def _validated_restage_successor_source(
        self,
        restages_revision: str,
        *,
        new_revision_iri: str,
    ) -> str:
        source_iri = self._required_iri("restages_revision", restages_revision)
        if source_iri == new_revision_iri:
            raise DoxaBaseError("restages_revision cannot point to the new revision")
        source = self.describe_staged_revision(source_iri)
        existing_successor = source.current_restaged_by or source.restaged_by
        if existing_successor is not None:
            raise DoxaBaseError(
                "Cannot stage a repaired successor for a staged revision that "
                "already has a refreshed successor; inspect or target the "
                f"current successor '{existing_successor.iri}' instead."
            )
        if source.applied_by is not None:
            raise DoxaBaseError(
                "Cannot stage a repaired successor for a staged revision that "
                f"has already been applied by '{source.applied_by.iri}'."
            )
        if source.review_resolution is not None:
            raise DoxaBaseError(
                "Cannot stage a repaired successor for a staged revision that "
                "has a recorded review resolution "
                f"'{source.review_resolution.resolution_revision_iri}'."
            )
        return source.iri
    def restage_staged_revision(
        self,
        iri: str,
        *,
        summary: str | None = None,
        rationale: str | None = None,
        created_at: datetime | str | None = None,
        created_by: str | None = None,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
    ) -> RestagedGraphRevisionRecord:
        source = self.describe_staged_revision(iri)
        existing_successor = source.current_restaged_by or source.restaged_by
        if existing_successor is not None:
            raise DoxaBaseError(
                "restage_staged_revision cannot restage a source that already "
                "has a refreshed restaged successor; inspect or restage the "
                f"current successor '{existing_successor.iri}' instead."
            )
        check = self.check_staged_revision_apply(
            source.iri,
            validation_scope=validation_scope,
        )
        if check.status != "conflict":
            raise DoxaBaseError(
                "restage_staged_revision only restages conflicted staged "
                f"revisions; current status is '{check.status}'."
            )
        if not self._staged_apply_check_is_restageable_conflict(
            check.blocking_reasons
        ):
            raise DoxaBaseError(
                "restage_staged_revision only handles count/digest drift; "
                "inspect patch checks and stage a repaired or alternative "
                "candidate for unreplayable patch conflicts."
            )
        if (
            check.next_action is not None
            and check.next_action.tool_name == "stage_map_assertion_change"
        ):
            raise DoxaBaseError(
                "restage_staged_revision will not create a mechanical restage "
                "for a same-slot replacement conflict. Follow the suggested "
                "stage_map_assertion_change replacement with restages_revision "
                "so the refreshed proposal replaces the current value."
            )
        if self._staged_apply_check_has_ambiguous_same_slot_review(check):
            raise DoxaBaseError(
                "restage_staged_revision will not create a mechanical restage "
                "for an ambiguous same-slot conflict. Inspect current assertion "
                "support and stage an explicit repair or replacement instead."
            )
        if (
            check.next_action is not None
            and check.next_action.action_label == "Draft patch repair plan"
        ):
            raise DoxaBaseError(
                "restage_staged_revision will not create a mechanical restage "
                "for a mixed patch repair-plan conflict. Inspect "
                "draft_staged_revision_rebase().apply_check.patch_repair_plan "
                "and stage a complete repaired successor instead."
            )
        if (
            check.next_action is not None
            and check.next_action.action_type == "inspect_no_effective_change"
        ):
            raise DoxaBaseError(
                "restage_staged_revision will not create a no-op successor for "
                "an already-effective stale source. Inspect or export the stale "
                "revision, or stage a repaired replacement with restages_revision "
                "if semantic work remains."
            )

        ordered_patch_specs = self._ordered_staged_patch_specs_from_descriptions(
            source.patches
        )

        source_summary = self._restage_source_summary(source.summary) or source.iri
        restage_summary = (
            summary.strip()
            if summary is not None and summary.strip()
            else f"Restage stale revision: {source_summary}"
        )
        restage_rationale = (
            rationale.strip()
            if rationale is not None and rationale.strip()
            else self._restage_rationale(source, check)
        )
        staged = self.stage_graph_revision(
            summary=restage_summary,
            rationale=restage_rationale,
            stance=source.revision_stance or "rc:CandidateRevision",
            revision_type=source.revision_type or "rc:StagedRevision",
            included_graphs=source.included_graphs,
            created_at=created_at,
            created_by=created_by,
            supporting_observations=[
                item.iri for item in source.supporting_observations
            ],
            supporting_claims=[item.iri for item in source.supporting_claims],
            supporting_patterns=[item.iri for item in source.supporting_patterns],
            revision_anchors=[item.iri for item in source.revision_anchors],
            evidence=[item.iri for item in source.evidence],
            alternative_to=(
                source.alternative_to.iri if source.alternative_to is not None else None
            ),
            restages_revision=source.iri,
            review_note=source.review_note,
            review_recommendation=source.review_recommendation,
            validation_scope=validation_scope or source.validation_scope or "all",
            _ordered_patch_specs=ordered_patch_specs,
        )
        extra_triples = self._record_profile_insight_route_sources(
            staged.revision_iri,
            self._stored_profile_insight_route_sources(source.iri),
        )
        if extra_triples:
            staged = replace(staged, triples=staged.triples + extra_triples)
        staged_description = self.describe_staged_revision(staged.revision_iri)
        post_restage_check = self.check_staged_revision_apply(
            staged.revision_iri,
            validation_scope=validation_scope,
        )
        base_record = replace(
            staged,
            alternative_to=(
                staged_description.alternative_to.iri
                if staged_description.alternative_to is not None
                else None
            ),
            restaged_from=source.iri,
            restage_reason=staged_description.restage_reason,
            current_restaged_by=(
                staged_description.current_restaged_by.iri
                if staged_description.current_restaged_by is not None
                else None
            ),
        )
        current_direct_restaged_by = (
            staged_description.restaged_by.iri
            if staged_description.restaged_by is not None
            else None
        )
        stale_resolution_state_after = self._stale_resolution_state(
            status=post_restage_check.status,
            has_patch_payload=bool(staged_description.patches),
            restaged_from=source.iri,
            restaged_by=current_direct_restaged_by,
        )
        current_staged_validation_status = self._staged_validation_status(
            conforms=staged_description.validation_conforms,
            result_count=staged_description.validation_result_count,
        )
        next_action_after = self._revision_next_action(
            staged.revision_iri,
            apply_status=post_restage_check.status,
            apply_decision=post_restage_check.decision,
            stale_resolution_state=stale_resolution_state_after,
            suggested_next_actions=post_restage_check.suggested_next_actions,
            restaged_by=current_direct_restaged_by,
            staged_validation_status=current_staged_validation_status,
        )
        routing_decision_after = self._staged_apply_check_routing_decision(
            post_restage_check.decision,
            next_action_after,
        )
        next_action_queue_item_after = self._revision_next_action_queue_item(
            row_iri=staged.revision_iri,
            next_action=next_action_after,
            record_kind=self._graph_revision_record_kind_for_iri(
                staged.revision_iri
            ),
            application_status=post_restage_check.status,
            application_decision=post_restage_check.decision,
            stale_resolution_state=stale_resolution_state_after,
            staged_validation_status=current_staged_validation_status,
            semantic_risk_level=post_restage_check.semantic_risk_level,
            semantic_risk_reasons=post_restage_check.semantic_risk_reasons,
            alternative_gate=post_restage_check.alternative_gate,
        )
        return RestagedGraphRevisionRecord(
            **{
                record_field.name: getattr(base_record, record_field.name)
                for record_field in fields(StagedGraphRevisionRecord)
            },
            status_after=post_restage_check.status,
            decision_after=post_restage_check.decision,
            routing_decision_after=routing_decision_after,
            stale_resolution_state_after=stale_resolution_state_after,
            blocking_reasons_after=post_restage_check.blocking_reasons,
            current_staged_validation_status=current_staged_validation_status,
            next_action_after=next_action_after,
            next_action_queue_item_after=next_action_queue_item_after,
            suggested_next_actions_after=post_restage_check.suggested_next_actions,
        )
    def _restage_source_summary(self, summary: str | None) -> str | None:
        if summary is None:
            return None
        restage_prefix = "Restage stale revision:"
        normalized = summary.strip()
        while normalized.startswith(restage_prefix):
            normalized = normalized[len(restage_prefix) :].strip()
        return normalized or summary.strip()
    @staticmethod
    def _batch_restage_repair_first_warning(
        *,
        source_staged_validation_status: str,
        routing_decision_after: str,
        source_revision_iri: str,
        current_revision_iri: str,
    ) -> str | None:
        if (
            source_staged_validation_status != "failed"
            or routing_decision_after != "repair_or_replace"
        ):
            return None
        if current_revision_iri == source_revision_iri:
            current_note = "the selected source revision"
        else:
            current_note = f"current revision {current_revision_iri}"
        return (
            "Repair-first warning: the source failed staged-time validation "
            f"and {current_note} routes to repair_or_replace. Inspect "
            "validation_results or call draft_staged_revision_rebase before "
            "restaging or applying; a same-payload mechanical restage may only "
            "produce another repair candidate."
        )
    def restage_staged_revisions(
        self,
        revision_iris: Iterable[str] | str,
        *,
        path: str | Path | None = None,
        title: str | None = None,
        executive_summary: str | None = None,
        format: TypingLiteral["markdown"] = "markdown",
        overwrite: bool = False,
        created_at: datetime | str | None = None,
        created_by: str | None = None,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
        dry_run: bool = False,
    ) -> StagedGraphRevisionBatchRestageRecord:
        requested_revision_iris = self._string_values(
            "revision_iris",
            revision_iris,
            required=True,
        )
        processed_revision_iris = list(dict.fromkeys(requested_revision_iris))
        would_restage_revision_iris: list[str] = []
        repair_first_revision_iris: list[str] = []
        restaged_revision_iris: list[str] = []
        skipped_revision_iris: list[str] = []
        already_handled_revision_iris: list[str] = []
        not_restageable_revision_iris: list[str] = []
        not_restageable_revision_iris_by_reason: dict[str, list[str]] = {}
        restaged_revision_by_source: dict[str, str] = {}
        current_revision_by_source: dict[str, str] = {}
        review_revision_iris: list[str] = []
        items: list[StagedGraphRevisionBatchRestageItem] = []
        history_graphs = self._expand_graphs(["history"])
        apply_check_by_iri: dict[
            str,
            tuple[StagedRevisionApplyCheck | None, str | None],
        ] = {}

        def add_review_revision(iri: str | None) -> None:
            if iri is not None and iri not in review_revision_iris:
                review_revision_iris.append(iri)

        def record_apply_check(check: StagedRevisionApplyCheck) -> None:
            apply_check_by_iri[check.revision_iri] = (check, None)

        def apply_check_for_review(
            description: StagedGraphRevisionDescription,
        ) -> tuple[StagedRevisionApplyCheck | None, str | None]:
            cached = apply_check_by_iri.get(description.iri)
            if cached is not None:
                return cached
            return self._staged_revision_apply_check_for_export(description)

        for source_iri in processed_revision_iris:
            source = self.describe_staged_revision(source_iri)
            source_snapshot_evidence = self._revision_snapshot_evidence_status(
                source.iri,
                history_graphs,
            )
            source_staged_validation_status = self._staged_validation_status(
                conforms=source.validation_conforms,
                result_count=source.validation_result_count,
            )
            check = self.check_staged_revision_apply(
                source.iri,
                validation_scope=validation_scope,
            )
            record_apply_check(check)
            restaged_by = (
                source.restaged_by.iri if source.restaged_by is not None else None
            )
            restaged_from = (
                source.restaged_from.iri
                if source.restaged_from is not None
                else None
            )
            current_restaged_by = (
                source.current_restaged_by.iri
                if source.current_restaged_by is not None
                else None
            )
            stale_resolution_state = self._stale_resolution_state(
                status=check.status,
                has_patch_payload=bool(source.patches),
                restaged_from=restaged_from,
                restaged_by=restaged_by,
            )
            restaged_revision_iri: str | None = None
            current_revision_iri = current_restaged_by or source.iri
            not_restageable_reason: str | None = None

            is_restageable_conflict = (
                check.status == "conflict"
                and self._staged_apply_check_is_restageable_conflict(
                    check.blocking_reasons
                )
            )
            repair_route = (
                check.next_action
                if (
                    check.next_action is not None
                    and check.next_action.tool_name
                    == "stage_map_assertion_change"
                )
                else None
            )
            ambiguous_same_slot_route = (
                self._staged_apply_check_has_ambiguous_same_slot_review(check)
            )
            patch_repair_plan_route = (
                check.next_action is not None
                and check.next_action.action_label == "Draft patch repair plan"
            )
            already_effective_route = (
                check.next_action is not None
                and check.next_action.action_type == "inspect_no_effective_change"
            )
            if (
                is_restageable_conflict
                and restaged_by is None
                and repair_route is None
                and not ambiguous_same_slot_route
                and not patch_repair_plan_route
                and not already_effective_route
            ):
                if dry_run:
                    action = "would_restage"
                    note = (
                        "Dry run: would create a refreshed staged revision "
                        "against current graph state; no graph mutation was "
                        "performed."
                    )
                else:
                    restaged = self.restage_staged_revision(
                        source.iri,
                        created_at=created_at,
                        created_by=created_by,
                        validation_scope=validation_scope,
                    )
                    restaged_revision_iri = restaged.revision_iri
                    current_restaged_by = restaged.revision_iri
                    current_revision_iri = restaged.revision_iri
                    restaged_revision_iris.append(restaged.revision_iri)
                    restaged_revision_by_source[source.iri] = restaged.revision_iri
                    action = "restaged"
                    note = (
                        "Created a refreshed staged revision against current graph "
                        "state; review it before applying."
                    )
            elif (
                is_restageable_conflict
                and restaged_by is None
                and (
                    repair_route is not None
                    or ambiguous_same_slot_route
                    or patch_repair_plan_route
                    or already_effective_route
                )
            ):
                skipped_revision_iris.append(source.iri)
                not_restageable_revision_iris.append(source.iri)
                not_restageable_reason = (
                    self._batch_restage_not_restageable_reason(check)
                )
                not_restageable_revision_iris_by_reason.setdefault(
                    not_restageable_reason,
                    [],
                ).append(source.iri)
                action = "skipped_not_restageable"
                route_label = (
                    "inspection"
                    if already_effective_route
                    else (
                        "ambiguous same-slot review"
                        if ambiguous_same_slot_route
                        else (
                            "patch repair planning"
                            if patch_repair_plan_route
                            else "repair or replacement"
                        )
                    )
                )
                note = (
                    "Skipped because the current apply check recommends "
                    f"{route_label} instead of mechanical restage "
                    f"(reason='{not_restageable_reason}', "
                    f"status='{check.status}', "
                    f"blocking_reasons={check.blocking_reasons})."
                )
            elif is_restageable_conflict and restaged_by is not None:
                skipped_revision_iris.append(source.iri)
                already_handled_revision_iris.append(source.iri)
                action = "skipped_already_handled"
                note = (
                    "Skipped because this stale source already points to a "
                    "refreshed restaged_by successor."
                )
            else:
                skipped_revision_iris.append(source.iri)
                not_restageable_revision_iris.append(source.iri)
                not_restageable_reason = (
                    self._batch_restage_not_restageable_reason(check)
                )
                not_restageable_revision_iris_by_reason.setdefault(
                    not_restageable_reason,
                    [],
                ).append(source.iri)
                action = "skipped_not_restageable"
                note = (
                    "Skipped because the current apply state is not restageable "
                    f"(reason='{not_restageable_reason}', "
                    f"status='{check.status}', "
                    f"blocking_reasons={check.blocking_reasons})."
                )

            current_revision_by_source[source.iri] = current_revision_iri
            add_review_revision(source.iri)
            if current_revision_iri != source.iri:
                add_review_revision(current_revision_iri)
                current_description = self.describe_staged_revision(
                    current_revision_iri
                )
                current_check = self.check_staged_revision_apply(
                    current_revision_iri,
                    validation_scope=validation_scope,
                )
                record_apply_check(current_check)
            else:
                current_description = source
                current_check = check
            current_staged_validation_status = self._staged_validation_status(
                conforms=current_description.validation_conforms,
                result_count=current_description.validation_result_count,
            )
            current_snapshot_evidence = self._revision_snapshot_evidence_status(
                current_revision_iri,
                history_graphs,
            )
            current_restaged_from = (
                current_description.restaged_from.iri
                if current_description.restaged_from is not None
                else None
            )
            current_direct_restaged_by = (
                current_description.restaged_by.iri
                if current_description.restaged_by is not None
                else None
            )
            stale_resolution_state_after = self._stale_resolution_state(
                status=current_check.status,
                has_patch_payload=bool(current_description.patches),
                restaged_from=current_restaged_from,
                restaged_by=current_direct_restaged_by,
            )
            suggested_next_actions_after = current_check.suggested_next_actions
            next_action_after = self._revision_next_action(
                current_revision_iri,
                apply_status=current_check.status,
                apply_decision=current_check.decision,
                stale_resolution_state=stale_resolution_state_after,
                suggested_next_actions=suggested_next_actions_after,
                restaged_by=current_direct_restaged_by,
                staged_validation_status=current_staged_validation_status,
            )
            routing_decision_after = self._staged_apply_check_routing_decision(
                current_check.decision,
                next_action_after,
            )
            repair_first_warning = (
                self._batch_restage_repair_first_warning(
                    source_staged_validation_status=(
                        source_staged_validation_status
                    ),
                    routing_decision_after=routing_decision_after,
                    source_revision_iri=source.iri,
                    current_revision_iri=current_revision_iri,
                )
            )
            next_action_queue_item_after = self._revision_next_action_queue_item(
                row_iri=current_revision_iri,
                next_action=next_action_after,
                record_kind=self._graph_revision_record_kind_for_iri(
                    current_revision_iri
                ),
                application_status=current_check.status,
                application_decision=current_check.decision,
                stale_resolution_state=stale_resolution_state_after,
                staged_validation_status=current_staged_validation_status,
                semantic_risk_level=current_check.semantic_risk_level,
                semantic_risk_reasons=current_check.semantic_risk_reasons,
                alternative_gate=current_check.alternative_gate,
            )
            if (
                action == "skipped_already_handled"
                and stale_resolution_state_after
                == "restaged_successor_stale_unresolved"
            ):
                note = (
                    note
                    + " The current successor is itself stale; inspect or "
                    "restage current_revision_iri before applying anything."
                )
            if current_check.status == "validation_failed":
                note = (
                    note
                    + " The current revision fails validation; inspect "
                    "validation_results and stage a repaired or alternative "
                    "candidate. For overlapping single-assertion failures, use "
                    "a removal+addition patch or stage_map_assertion_change "
                    "replacement instead of restaging the same patch again."
                )
            if (
                current_check.decision
                == "inspect_restaged_source_validation_failure"
            ):
                note = (
                    note
                    + " The current revision is mechanically ready, but its "
                    "source failed staged-time validation; inspect source "
                    "validation diagnostics and repair or replace the framing "
                    "before applying."
                )
            if repair_first_warning is not None:
                note = f"{note} {repair_first_warning}"
                if action == "would_restage":
                    repair_first_revision_iris.append(source.iri)
            elif action == "would_restage":
                would_restage_revision_iris.append(source.iri)
            items.append(
                StagedGraphRevisionBatchRestageItem(
                    source_revision_iri=source.iri,
                    summary=source.summary,
                    status_before=check.status,
                    decision_before=check.decision,
                    routing_decision_before=check.routing_decision,
                    stale_resolution_state_before=stale_resolution_state,
                    blocking_reasons_before=check.blocking_reasons,
                    exact_drift_summary_before=(
                        self._staged_revision_exact_drift_summary(check)
                    ),
                    source_staged_validation_status=(
                        source_staged_validation_status
                    ),
                    source_validation_result_count=source.validation_result_count,
                    source_snapshot_evidence=source_snapshot_evidence,
                    source_snapshot_evidence_completeness=(
                        self._snapshot_evidence_completeness_label(
                            source_snapshot_evidence
                        )
                    ),
                    status_after=current_check.status,
                    decision_after=current_check.decision,
                    routing_decision_after=routing_decision_after,
                    stale_resolution_state_after=stale_resolution_state_after,
                    blocking_reasons_after=current_check.blocking_reasons,
                    exact_drift_summary_after=(
                        self._staged_revision_exact_drift_summary(current_check)
                    ),
                    current_staged_validation_status=(
                        current_staged_validation_status
                    ),
                    current_validation_result_count=(
                        current_description.validation_result_count
                    ),
                    current_snapshot_evidence=current_snapshot_evidence,
                    current_snapshot_evidence_completeness=(
                        self._snapshot_evidence_completeness_label(
                            current_snapshot_evidence
                        )
                    ),
                    triples_to_add_after=current_check.triples_to_add,
                    triples_to_remove_after=current_check.triples_to_remove,
                    action=action,
                    not_restageable_reason=not_restageable_reason,
                    restaged_from=restaged_from,
                    restaged_revision_iri=restaged_revision_iri,
                    current_restaged_by=current_restaged_by,
                    current_revision_iri=current_revision_iri,
                    next_action_after=next_action_after,
                    next_action_queue_item_after=next_action_queue_item_after,
                    suggested_next_actions_after=suggested_next_actions_after,
                    repair_first_warning=repair_first_warning,
                    note=note,
                )
            )

        current_revision_by_source = {
            source_iri: (
                self._current_restage_successor_iri(source_iri) or source_iri
            )
            for source_iri in processed_revision_iris
        }
        for current_revision_iri in current_revision_by_source.values():
            add_review_revision(current_revision_iri)

        export_record: StagedGraphRevisionsExportRecord | None = None
        if path is not None:
            export_record = self.export_staged_revisions(
                review_revision_iris,
                path,
                title=title,
                executive_summary=executive_summary,
                format=format,
                overwrite=overwrite,
            )
            revision_summaries = export_record.revision_summaries
            bundle_summary = export_record.bundle_summary
        else:
            review_descriptions = [
                self.describe_staged_revision(iri) for iri in review_revision_iris
            ]
            review_apply_checks = [
                apply_check_for_review(description)
                for description in review_descriptions
            ]
            revision_summaries = self._staged_revisions_export_summaries(
                review_descriptions,
                apply_checks=review_apply_checks,
            )
            bundle_summary = self._staged_revisions_bundle_summary(
                revision_summaries,
                descriptions=review_descriptions,
                snapshot_evidence=(
                    self._staged_revisions_snapshot_evidence_summary(
                        review_descriptions
                    )
                ),
            )

        suggested_next_actions = self._batch_restage_suggested_next_actions(
            dry_run=dry_run,
            would_restage_revision_iris=would_restage_revision_iris,
            items=items,
            validation_scope=validation_scope,
        )
        repair_or_replace_source_revision_iris = list(
            dict.fromkeys(
                item.source_revision_iri
                for item in items
                if item.next_action_after is not None
                and item.next_action_after.queue == "repair_or_replace"
            )
        )
        return StagedGraphRevisionBatchRestageRecord(
            requested_revision_iris=requested_revision_iris,
            processed_revision_iris=processed_revision_iris,
            dry_run=dry_run,
            would_restage_revision_iris=would_restage_revision_iris,
            repair_first_revision_iris=repair_first_revision_iris,
            repair_or_replace_source_revision_iris=(
                repair_or_replace_source_revision_iris
            ),
            restaged_revision_iris=restaged_revision_iris,
            skipped_revision_iris=skipped_revision_iris,
            already_handled_revision_iris=already_handled_revision_iris,
            not_restageable_revision_iris=not_restageable_revision_iris,
            not_restageable_revision_iris_by_reason=(
                not_restageable_revision_iris_by_reason
            ),
            restaged_revision_by_source=restaged_revision_by_source,
            current_revision_by_source=current_revision_by_source,
            review_revision_iris=review_revision_iris,
            items=items,
            revision_summaries=revision_summaries,
            bundle_summary=bundle_summary,
            requires_recheck_after_each_apply=(
                bundle_summary.requires_recheck_after_each_apply
            ),
            sequential_apply_recheck_candidate_iris=(
                bundle_summary.sequential_apply_recheck_candidate_iris
            ),
            export_record=export_record,
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[
                action.call for action in suggested_next_actions
            ],
        )
    def _batch_restage_suggested_next_actions(
        self,
        *,
        dry_run: bool,
        would_restage_revision_iris: list[str],
        items: list[StagedGraphRevisionBatchRestageItem],
        validation_scope: str | None,
    ) -> list[SuggestedNextAction]:
        actions: list[SuggestedNextAction] = []
        if dry_run and would_restage_revision_iris:
            arguments: dict[str, Any] = {
                "revision_iris": list(would_restage_revision_iris),
                "dry_run": False,
            }
            if validation_scope is not None:
                arguments["validation_scope"] = validation_scope
            actions.append(
                SuggestedNextAction(
                    action_label="Run reviewed batch restage",
                    tool_name="restage_staged_revisions",
                    mcp_tool_name="doxabase.restage_staged_revisions",
                    arguments=arguments,
                    reason=(
                        "The dry run identified stale staged revisions that can "
                        "be mechanically restaged. Run the real batch after "
                        "reviewing classifications and repair-first warnings; "
                        "the action omits the dry-run export path to avoid "
                        "overwriting the review artifact."
                    ),
                    call=self._suggested_call_string(
                        "restage_staged_revisions",
                        arguments,
                    ),
                )
            )
        if dry_run and actions:
            return actions
        for item in items:
            action = self._suggested_action_from_revision_next_action(
                item.next_action_after
            )
            if action is not None:
                actions.append(action)
        return self._dedupe_suggested_next_actions(actions)
    def _batch_restage_not_restageable_reason(
        self,
        check: StagedRevisionApplyCheck,
    ) -> str:
        if (
            check.next_action is not None
            and check.next_action.tool_name == "stage_map_assertion_change"
        ):
            return "same_slot_replacement"
        if self._staged_apply_check_has_ambiguous_same_slot_review(check):
            return "ambiguous_same_slot"
        if (
            check.next_action is not None
            and check.next_action.action_label == "Draft patch repair plan"
        ):
            return "patch_repair_plan"
        if (
            check.next_action is not None
            and check.next_action.action_type == "inspect_no_effective_change"
        ):
            return "already_effective"
        if check.decision == "inspect_restaged_source_validation_failure":
            return check.decision
        if "patch_conflict" in check.blocking_reasons:
            return "patch_conflict"
        if check.status == "conflict":
            return "conflict"
        return check.status
    def _restage_rationale(
        self,
        source: StagedGraphRevisionDescription,
        check: StagedRevisionApplyCheck,
    ) -> str:
        lines = [
            f"Restaged stale revision {source.iri} against current graph state.",
            "",
            "Apply-check status before restaging:",
            f"- status: {check.status}",
            f"- decision: {check.decision}",
            f"- blocking reasons: {', '.join(check.blocking_reasons) or '(none)'}",
            f"- summary: {check.summary}",
        ]
        if check.recommended_resolution:
            lines.append(f"- recommended resolution: {check.recommended_resolution}")
        if check.count_drifts:
            lines.extend(["", "Count drift details:"])
            for drift in check.count_drifts:
                lines.append(
                    "- "
                    f"{drift.target_graph} patch "
                    f"{drift.patch_sequence_index or 'unknown'}: expected "
                    f"{drift.expected_before_triple_count}, current "
                    f"{drift.current_triple_count}, delta {drift.delta}; "
                    f"{drift.expected_before_basis}; "
                    f"patch triples {drift.patch_triple_status or 'unknown'}."
                )
        if check.snapshot_drifts:
            lines.extend(["", "Snapshot drift details:"])
            for drift in check.snapshot_drifts:
                lines.append(
                    "- "
                    f"{drift.graph_role}: snapshot count "
                    f"{drift.snapshot_triple_count}, current count "
                    f"{drift.current_triple_count}, exact triples available "
                    f"{drift.exact_changed_triples_available}."
                )
                lines.extend(
                    self._restage_rationale_triple_diff_lines(
                        "Added since snapshot",
                        drift.triples_added_since_snapshot,
                    )
                )
                lines.extend(
                    self._restage_rationale_triple_diff_lines(
                        "Removed since snapshot",
                        drift.triples_removed_since_snapshot,
                    )
                )
        lines.extend(
            [
                "",
                "Original staged rationale:",
                source.rationale or "(No original rationale recorded.)",
            ]
        )
        return "\n".join(lines)
    def _restage_rationale_triple_diff_lines(
        self,
        label: str,
        triples: list[GraphTripleDescription],
        *,
        limit: int = 5,
    ) -> list[str]:
        if not triples:
            return [f"  - {label}: none"]
        lines = [f"  - {label}:"]
        for triple in triples[:limit]:
            lines.append(
                "    - "
                f"{triple.subject_display} {triple.predicate_display} "
                f"{triple.object_display}"
            )
        omitted = len(triples) - limit
        if omitted > 0:
            lines.append(f"    - ... {omitted} more")
        return lines
    def _restaged_source_validation_context(
        self,
        staged: StagedGraphRevisionDescription,
    ) -> tuple[str | None, bool]:
        if staged.restaged_from is None:
            return None, False
        source = self.describe_staged_revision(staged.restaged_from.iri)
        reuses_source_patch_payload = (
            self._staged_revision_patch_payload_signature(staged)
            == self._staged_revision_patch_payload_signature(source)
        )
        source_status = self._staged_validation_status(
            conforms=source.validation_conforms,
            result_count=source.validation_result_count,
        )
        if source_status != "failed":
            return None, reuses_source_patch_payload
        result_text = (
            f" with {source.validation_result_count} result(s)"
            if source.validation_result_count is not None
            else ""
        )
        if not reuses_source_patch_payload:
            return (
                "The restaged source failed staged-time validation"
                f"{result_text}; this successor uses a revised patch payload, "
                "so compare it with the source diagnostics before applying.",
                reuses_source_patch_payload,
            )
        return (
            "The restaged source failed staged-time validation"
            f"{result_text}; current validation may pass because intervening "
            "graph state supplied semantics that the source framing originally "
            "omitted.",
            reuses_source_patch_payload,
        )
    def _restaged_source_validation_warning(
        self,
        staged: StagedGraphRevisionDescription,
    ) -> str | None:
        warning, _ = self._restaged_source_validation_context(staged)
        return warning
    def _staged_apply_check_is_restageable_conflict(
        self,
        blocking_reasons: list[str],
    ) -> bool:
        restageable_reasons = {"target_count_drift", "target_digest_drift"}
        return any(reason in restageable_reasons for reason in blocking_reasons)
    def _parallel_applied_restage_successor_events(
        self,
        summary: StagedGraphRevisionExportSummary,
    ) -> list[tuple[str, str, str]]:
        history_graphs = self._expand_graphs(["history"])
        followed_successors = {
            iri
            for iri in (summary.restaged_by, summary.current_restaged_by)
            if iri is not None
        }
        events: list[tuple[str, str, str]] = []
        for successor_iri in self._subjects(
            history_graphs,
            "rc:restagesRevision",
            summary.revision_iri,
        ):
            if successor_iri in followed_successors:
                continue
            applied_iri = self._first_subject(
                history_graphs,
                "rc:appliesStagedRevision",
                successor_iri,
            )
            if applied_iri is not None:
                events.append((summary.revision_iri, successor_iri, applied_iri))
        return events
    def _ready_restage_successor_alternative_to_applied_source_iris(
        self,
        summaries: list[StagedGraphRevisionExportSummary],
    ) -> list[str]:
        affected: list[str] = []
        for summary in summaries:
            if summary.stale_resolution_state != "restaged_successor_ready":
                continue
            if summary.alternative_gate.semantic_review_required:
                affected.append(summary.revision_iri)
        return affected
