"""Staged revision recovery session persistence and description.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via RecoverySessionsMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class RecoverySessionsMixin:
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
            suggested_next_actions=current_plan.suggested_next_actions,
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
