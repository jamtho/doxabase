"""Query context description, plan drafting, storage repair.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via QueryPlanningMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class QueryPlanningMixin:
    def describe_query_context(
        self,
        iri: str,
        graph: str | None = "map",
    ) -> QueryPlanningContext:
        dataset = self.describe_dataset(iri, graph=graph)
        data_graphs = self._expand_graphs([graph] if graph else None)
        dataset_summary = ResourceSummary(
            iri=dataset.iri,
            label=dataset.label or self._local_name(dataset.iri),
            description=dataset.description,
        )
        if self._dataset_description_is_analysis_view(dataset):
            return self._analysis_view_query_context(dataset, dataset_summary)
        if not self._dataset_description_is_table(dataset):
            return self._non_tabular_query_context(dataset, dataset_summary)
        direct_path_templates = self._objects(data_graphs, dataset.iri, "rc:pathTemplate")
        issues = self._sort_query_planning_issues(
            [
                *dataset.operational_warnings,
                *self._query_target_candidate_metadata_issues(
                    dataset,
                    dataset_summary=dataset_summary,
                    direct_path_templates=direct_path_templates,
                ),
            ]
        )
        analysis_warnings = self._query_analysis_warnings(dataset)
        readiness = self._query_planning_readiness(issues)
        query_target_candidates = self._query_target_candidates(
            dataset,
            dataset_summary=dataset_summary,
            direct_path_templates=direct_path_templates,
            issues=issues,
        )
        query_target_decision = self._query_target_decision(query_target_candidates)
        ready_candidate_indexes = self._query_ready_candidate_indexes(
            query_target_candidates
        )
        issues = self._query_context_repair_hinted_issues(
            issues,
            dataset=dataset,
            decision=query_target_decision,
            candidates=query_target_candidates,
        )
        issues = self._query_context_issues_with_pending_repair_actions(
            issues,
            dataset,
        )
        suggested_repair_action_groups = self._query_repair_action_groups(issues)
        unselected_ready_candidate_indexes = [
            index
            for index in ready_candidate_indexes
            if index != query_target_decision.candidate_index
        ]
        direct_clean_candidate_indexes = self._query_direct_clean_candidate_indexes(
            query_target_candidates
        )
        unselected_direct_clean_candidate_indexes = [
            index
            for index in direct_clean_candidate_indexes
            if index != query_target_decision.candidate_index
        ]
        pending_repair_groups_present = (
            self._query_repair_groups_have_pending_options(
                suggested_repair_action_groups
            )
        )
        suggested_next_actions = self._query_context_next_actions(
            dataset=dataset,
            graph=graph,
            readiness=readiness,
            issues=issues,
            decision=query_target_decision,
            candidates=query_target_candidates,
            pending_repair_groups_present=pending_repair_groups_present,
            unselected_ready_candidate_indexes=unselected_ready_candidate_indexes,
            unselected_direct_clean_candidate_indexes=(
                unselected_direct_clean_candidate_indexes
            ),
        )
        safe_inspection_action_indexes = (
            self._query_context_safe_inspection_action_indexes(
                suggested_next_actions
            )
        )
        return QueryPlanningContext(
            dataset=dataset_summary,
            readiness=readiness,
            readiness_note=self._query_readiness_note(
                readiness,
                issues=issues,
                analysis_warnings=analysis_warnings,
            ),
            issues=issues,
            analysis_warnings=analysis_warnings,
            suggested_repair_action_groups=suggested_repair_action_groups,
            suggested_repair_action_group_count=len(suggested_repair_action_groups),
            planning_notes=[
                (
                    "DoxaBase records non-secret planning metadata only; local "
                    "runtime configuration must resolve endpoint profiles, "
                    "credential references, and actual query execution."
                ),
                (
                    "Read caveats and verification notes before generating or "
                    "running a query, and record query results or failures as "
                    "evidence-backed observations."
                ),
            ],
            row_count_snapshot=dataset.row_count_snapshot,
            profile_summary=dataset.profile_summary,
            layout_verification_status=dataset.layout_verification_status,
            layout_verification_note=dataset.layout_verification_note,
            columns=dataset.columns,
            path_templates=dataset.path_templates,
            query_target_decision=query_target_decision,
            query_target_candidates=query_target_candidates,
            ready_candidate_indexes=ready_candidate_indexes,
            unselected_ready_candidate_indexes=unselected_ready_candidate_indexes,
            direct_clean_candidate_indexes=direct_clean_candidate_indexes,
            unselected_direct_clean_candidate_indexes=(
                unselected_direct_clean_candidate_indexes
            ),
            physical_layouts=dataset.physical_layouts,
            storage_accesses=dataset.storage_accesses,
            partition_schemes=dataset.partition_schemes,
            caveats=dataset.caveats,
            upstream_caveats=dataset.upstream_caveats,
            suggested_next_actions=suggested_next_actions,
            safe_inspection_action_indexes=safe_inspection_action_indexes,
            first_safe_inspection_action_index=(
                safe_inspection_action_indexes[0]
                if safe_inspection_action_indexes
                else None
            ),
        )
    def _non_tabular_query_context(
        self,
        dataset: DatasetDescription,
        dataset_summary: ResourceSummary,
    ) -> QueryPlanningContext:
        issue = QueryPlanningIssue(
            code="non_tabular_asset_query_not_applicable",
            severity="info",
            message=(
                "This map dataset is not typed as rc:Table, so DoxaBase will "
                "not treat it as a table query-planning target."
            ),
            resource=dataset_summary,
            details={
                "dataset_iri": dataset.iri,
                "is_table": False,
                "suggested_profile": "deep_lore",
                "query_readiness": "not_applicable_non_tabular_asset",
            },
        )
        suggested_next_actions = [
            self._project_brief_get_context_graph_action(dataset.iri)
        ]
        return QueryPlanningContext(
            dataset=dataset_summary,
            readiness="not_applicable_non_tabular_asset",
            readiness_note=(
                "This map dataset is not typed as rc:Table; use resource or "
                "context-slice handoffs unless an explicit queryable table "
                "route is modeled."
            ),
            issues=[issue],
            analysis_warnings=[],
            suggested_repair_action_groups=[],
            suggested_repair_action_group_count=0,
            planning_notes=[
                (
                    "DoxaBase does not draft table query plans for map assets "
                    "that are not typed as rc:Table."
                ),
                (
                    "Use get_context_graph or describe_resource to inspect "
                    "non-tabular map context, caveats, observations, patterns, "
                    "and evidence."
                ),
            ],
            row_count_snapshot=dataset.row_count_snapshot,
            profile_summary=dataset.profile_summary,
            layout_verification_status=dataset.layout_verification_status,
            layout_verification_note=dataset.layout_verification_note,
            columns=dataset.columns,
            path_templates=dataset.path_templates,
            query_target_decision=QueryTargetDecision(
                status="not_applicable_non_tabular_asset",
                summary=(
                    "Dataset is not typed as rc:Table; no query target "
                    "candidate is selected."
                ),
                candidate_index=None,
                candidate_path=None,
                candidate_path_status=None,
                direct_review_required=None,
                selected_candidate_direct_clean=None,
                reason_codes=[issue.code],
                selection_reason_codes=["not_applicable_non_tabular_asset"],
            ),
            query_target_candidates=[],
            ready_candidate_indexes=[],
            unselected_ready_candidate_indexes=[],
            direct_clean_candidate_indexes=[],
            unselected_direct_clean_candidate_indexes=[],
            physical_layouts=dataset.physical_layouts,
            storage_accesses=dataset.storage_accesses,
            partition_schemes=dataset.partition_schemes,
            caveats=dataset.caveats,
            upstream_caveats=dataset.upstream_caveats,
            suggested_next_actions=suggested_next_actions,
            safe_inspection_action_indexes=[0],
            first_safe_inspection_action_index=0,
        )
    @staticmethod
    def _query_context_safe_inspection_action_indexes(
        actions: Iterable[SuggestedNextAction],
    ) -> list[int]:
        safe_inspection_tools = {
            "doxabase.get_context_graph",
            "doxabase.describe_resource",
        }
        return [
            index
            for index, action in enumerate(actions)
            if action.tool in safe_inspection_tools
        ]
    def _layout_status_is_verified(self, status: ResourceSummary | None) -> bool:
        if status is None:
            return False
        return status.iri in {
            self.expand_iri("rc:VerifiedByListingLayout"),
            self.expand_iri("rc:VerifiedByQueryLayout"),
        }
    @staticmethod
    def _query_context_blocker_resource_iris(
        candidate: QueryTargetCandidate,
    ) -> list[str]:
        blocker_iris: list[str] = []
        for reason in candidate.review_reasons:
            if reason.code != "query_context_has_other_blockers":
                continue
            details = reason.details or {}
            values = details.get("excluded_blocker_resource_iris")
            if not isinstance(values, list):
                continue
            for value in values:
                iri = str(value)
                if iri not in blocker_iris:
                    blocker_iris.append(iri)
        return blocker_iris
    def _query_context_next_actions(
        self,
        *,
        dataset: DatasetDescription,
        graph: str | None,
        readiness: str,
        issues: list[QueryPlanningIssue],
        decision: QueryTargetDecision,
        candidates: list[QueryTargetCandidate],
        pending_repair_groups_present: bool,
        unselected_ready_candidate_indexes: list[int],
        unselected_direct_clean_candidate_indexes: list[int],
    ) -> list[SuggestedNextAction]:
        actions: list[SuggestedNextAction] = []
        dataset_iri = dataset.iri
        profile_summary = dataset.profile_summary
        ordinary_query_evidence_exclusions: set[str] = set()
        if profile_summary.profile_run_candidates:
            profile_candidates = profile_summary.profile_run_candidates
            for candidate_index, candidate_run in enumerate(
                profile_candidates
            ):
                if candidate_index > 0 and not (
                    self._query_context_should_inspect_profile_candidate(
                        profile_candidates[0],
                        candidate_run,
                        profile_candidates,
                    )
                ):
                    continue
                profile_arguments = {
                    "iri": dataset_iri,
                    "aspect": "profile_run",
                    "evidence_iri": candidate_run.evidence_iri,
                }
                if candidate_index == 0:
                    reason = (
                        "Inspect the profile observations behind the selected "
                        "row-count/profile handoff before relying on profiler "
                        "evidence in a query plan."
                    )
                else:
                    reason = (
                        "Multiple profile-run candidates carry different row "
                        "count evidence, or the selected snapshot-matching "
                        "candidate is sampled, unknown, or mixed basis. Inspect "
                        "this additional run before treating a profile-derived "
                        "row count as current."
                    )
                actions.append(
                    SuggestedNextAction(
                        tool="doxabase.describe_resource",
                        args=profile_arguments,
                        reason=reason,
                    )
                )
        elif profile_summary.evidence_iris:
            singleton_actions = self._query_context_singleton_profile_evidence_actions(
                dataset,
                profile_summary,
                issues=issues,
            )
            actions.extend(singleton_actions)
            ordinary_query_evidence_exclusions.update(
                action.args["evidence_iri"]
                for action in singleton_actions
                if action.tool == "doxabase.draft_query_evidence_storage_overlay"
                and isinstance(action.args.get("evidence_iri"), str)
            )
        actions.extend(
            self._query_context_ordinary_query_evidence_actions(
                dataset,
                profile_summary,
                issues=issues,
                exclude_evidence_iris=ordinary_query_evidence_exclusions,
            )
        )
        if (
            decision.candidate_index is None
            or decision.candidate_index < 0
            or decision.candidate_index >= len(candidates)
        ):
            return actions
        candidate = candidates[decision.candidate_index]
        arguments: dict[str, Any] = {
            "iri": dataset_iri,
            "candidate_selector": candidate.candidate_selector,
        }
        if graph is not None and graph != "map":
            arguments["graph"] = graph

        reason = (
            "Draft a non-executed query plan for the selected query target "
            "candidate, then read review_gate, scan, bindings, and issues."
        )
        if (
            readiness != "ready_for_query_planning"
            and candidate.direct_review_required is False
        ):
            arguments["allow_context_blocked_candidate"] = True
            reason = (
                "The selected candidate has no direct warning or error, but "
                "sibling or broader context blockers make the whole context "
                "review-required. Draft it with an explicit selector and "
                "allow_context_blocked_candidate=True while preserving the "
                "context issue audit."
            )
            if unselected_direct_clean_candidate_indexes:
                peers = ", ".join(
                    str(index)
                    for index in unselected_direct_clean_candidate_indexes
                )
                reason = (
                    f"{reason} Other direct-clean candidate indexes exist "
                    f"({peers}); inspect query_target_candidates and rerun "
                    "with an explicit candidate_selector if another route is "
                    "intended."
                )
        elif decision.status == "candidate_needs_review":
            reason = (
                "Draft a non-executed review plan for this candidate so the "
                "scan, relation, runtime, and blocking reason fields are "
                "available before repair or execution."
            )
        elif decision.status == "ready":
            reason = (
                "Draft the selected query target and inspect bindings, runtime "
                "resolution requirements, and analysis caveats before any "
                "execution attempt."
            )
            if unselected_ready_candidate_indexes:
                peers = ", ".join(
                    str(index) for index in unselected_ready_candidate_indexes
                )
                reason = (
                    f"{reason} Other direct-ready candidate indexes exist "
                    f"({peers}); inspect query_target_candidates and rerun with "
                    "an explicit candidate_selector if another route is intended."
                )

        selected_route_intent_peer_indexes = set(
            decision.route_intent_review_candidate_indexes
        )
        selected_caution = self._query_plan_action_caution(
            caution=(
                decision.route_intent_caution
                if (
                    selected_route_intent_peer_indexes
                    and decision.candidate_index
                    not in selected_route_intent_peer_indexes
                )
                else None
            ),
            pending_repair_groups_present=pending_repair_groups_present,
        )
        if selected_caution:
            reason = f"{reason} {selected_caution}"

        actions.append(
            SuggestedNextAction(
                tool="doxabase.draft_query_plan",
                args=arguments,
                reason=reason,
            )
        )
        peer_action_indexes: list[int] = []
        peer_action_allowance = False
        peer_action_needs_context_allowance = (
            readiness != "ready_for_query_planning"
            and candidate.direct_review_required is False
        )
        if decision.status == "ready":
            peer_action_indexes = unselected_ready_candidate_indexes
            peer_action_allowance = peer_action_needs_context_allowance
        elif (
            peer_action_needs_context_allowance
        ):
            peer_action_indexes = unselected_direct_clean_candidate_indexes
            peer_action_allowance = True
        for peer_index in peer_action_indexes:
            if peer_index < 0 or peer_index >= len(candidates):
                continue
            peer_candidate = candidates[peer_index]
            peer_arguments: dict[str, Any] = {
                "iri": dataset_iri,
                "candidate_selector": peer_candidate.candidate_selector,
            }
            if graph is not None and graph != "map":
                peer_arguments["graph"] = graph
            if peer_action_allowance and peer_candidate.direct_review_required is False:
                peer_arguments["allow_context_blocked_candidate"] = True
                peer_reason = (
                    "A peer candidate has no direct warning or error, but "
                    "sibling or broader context blockers make the whole context "
                    "review-required. Draft this reviewed peer with an explicit "
                    "candidate_selector and allow_context_blocked_candidate=True "
                    "instead of parsing peer indexes from prose."
                )
            else:
                peer_reason = (
                    "A peer candidate is also direct-ready. Draft this explicit "
                    "candidate_selector when candidate review shows this path or "
                    "relation is the intended handoff."
                )
            peer_caution = self._query_plan_action_caution(
                caution=(
                    decision.route_intent_caution
                    if peer_index in selected_route_intent_peer_indexes
                    else None
                ),
                pending_repair_groups_present=pending_repair_groups_present,
            )
            if peer_caution:
                peer_reason = f"{peer_reason} {peer_caution}"
            actions.append(
                SuggestedNextAction(
                    tool="doxabase.draft_query_plan",
                    args=peer_arguments,
                    reason=peer_reason,
                )
            )
        layout_action_indexes = [
            decision.candidate_index,
            *(
                index
                for index, candidate_item in enumerate(candidates)
                if index != decision.candidate_index
                and self._query_context_candidate_only_layout_blocked(
                    candidate_item
                )
            ),
        ]
        for layout_action_index in layout_action_indexes:
            layout_candidate = candidates[layout_action_index]
            actions.extend(
                self._query_context_physical_layout_selection_actions(
                    dataset_iri=dataset_iri,
                    graph=graph,
                    candidate_index=layout_action_index,
                    candidate=layout_candidate,
                    columns=dataset.columns,
                    partition_schemes=dataset.partition_schemes,
                    allow_context_blocked_candidate=(
                        self._query_context_layout_selection_needs_context_allowance(
                            candidate=layout_candidate,
                            issues=issues,
                        )
                    ),
                    pending_repair_groups_present=pending_repair_groups_present,
                    route_intent_review_candidate_indexes=(
                        selected_route_intent_peer_indexes
                    ),
                    route_intent_caution=decision.route_intent_caution,
                )
        )
        return actions
    @staticmethod
    def _query_value_looks_like_local_path(value: str) -> bool:
        stripped = value.strip()
        if not stripped:
            return False
        if "/" in stripped or "\\" in stripped:
            return True
        return DoxaBase._query_file_format_from_path(stripped) is not None
    @staticmethod
    def _query_path_prefix_before_leaf_or_glob(path: str) -> str | None:
        wildcard_indexes = [
            index for index in (path.find("*"), path.find("?"), path.find("["))
            if index >= 0
        ]
        prefix_source = path[: min(wildcard_indexes)] if wildcard_indexes else path
        if "/" not in prefix_source:
            return None
        return prefix_source.rsplit("/", 1)[0] + "/"
    @staticmethod
    def _query_file_format_from_path(path: str) -> str | None:
        clean = path.split("?", 1)[0].split("#", 1)[0].lower()
        for compression_suffix in (".gz", ".gzip", ".bz2", ".xz", ".zst", ".zip"):
            if clean.endswith(compression_suffix):
                clean = clean[: -len(compression_suffix)]
                break
        suffix_map = {
            ".parquet": "rc:Parquet",
            ".csv": "rc:CSV",
            ".tsv": "rc:TSV",
            ".orc": "rc:ORC",
            ".json": "rc:JSON",
            ".jsonl": "rc:JSONL",
            ".ndjson": "rc:NDJSON",
            ".txt": "rc:PlainText",
            ".md": "rc:Markdown",
        }
        for suffix, file_format in suffix_map.items():
            if clean.endswith(suffix):
                return file_format
        return None
    @staticmethod
    def _query_context_source_span_preview(
        span: SourceSpanDescription,
    ) -> dict[str, Any]:
        return {
            "iri": span.iri,
            "source_path": span.source_path,
            "source_section": span.source_section,
            "start_line": span.start_line,
            "end_line": span.end_line,
            "source_kind": span.source_kind,
            "source_kind_label": span.source_kind_label,
        }
    def _query_context_layout_selection_needs_context_allowance(
        self,
        *,
        candidate: QueryTargetCandidate,
        issues: list[QueryPlanningIssue],
    ) -> bool:
        if not self._query_context_candidate_only_layout_blocked(candidate):
            return False
        remaining_blockers = [
            reason
            for reason in self._query_target_blocking_reasons(issues)
            if reason.code != "ambiguous_physical_layout"
        ]
        if not remaining_blockers:
            return False
        return all(
            self._is_candidate_metadata_issue(reason)
            for reason in remaining_blockers
        )
    @staticmethod
    def _with_unique_query_issue(
        issues: list[QueryPlanningIssue],
        issue: QueryPlanningIssue,
    ) -> list[QueryPlanningIssue]:
        issue_resource_iri = issue.resource.iri if issue.resource is not None else None
        for existing in issues:
            existing_resource_iri = (
                existing.resource.iri if existing.resource is not None else None
            )
            if (
                existing.code == issue.code
                and existing_resource_iri == issue_resource_iri
            ):
                return issues
        return [*issues, issue]
    @staticmethod
    def _without_query_issue_code(
        issues: list[QueryPlanningIssue],
        code: str,
    ) -> list[QueryPlanningIssue]:
        return [issue for issue in issues if issue.code != code]
    def _first_binding_column_match(
        self,
        placeholder: str,
        column: ColumnDescription,
        candidates: list[tuple[str, str | None]],
        *,
        match_kind: str,
        confidence: str,
    ) -> DraftQueryPlanBindingColumnMatch | None:
        for matched_field, matched_value in candidates:
            normalized = self._normalized_binding_name(matched_value)
            if not normalized:
                continue
            if match_kind == "exact_name":
                matched = normalized == placeholder
            else:
                matched = self._binding_name_has_suffix(normalized, placeholder)
            if matched and matched_value is not None:
                return DraftQueryPlanBindingColumnMatch(
                    column=ResourceSummary(
                        iri=column.iri,
                        label=column.label
                        or column.column_name
                        or self._local_name(column.iri),
                        description=column.description,
                        column_name=column.column_name,
                    ),
                    match_kind=match_kind,
                    matched_field=matched_field,
                    matched_value=matched_value,
                    confidence=confidence,
                )
        return None
    @staticmethod
    def _normalized_binding_name(value: str | None) -> str:
        if value is None:
            return ""
        return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    @staticmethod
    def _binding_name_has_suffix(candidate: str, placeholder: str) -> bool:
        return bool(candidate and placeholder and candidate.endswith(f"_{placeholder}"))
    @staticmethod
    def _query_issue_codes(
        issues: Iterable[QueryPlanningIssue],
    ) -> list[str]:
        codes: list[str] = []
        seen: set[str] = set()
        for issue in issues:
            if issue.code in seen:
                continue
            seen.add(issue.code)
            codes.append(issue.code)
        return codes
    @staticmethod
    def _query_blocking_issue_codes(
        issues: Iterable[QueryPlanningIssue],
    ) -> list[str]:
        codes: list[str] = []
        seen: set[str] = set()
        for issue in issues:
            if issue.severity not in {"error", "warning"}:
                continue
            if issue.code in seen:
                continue
            seen.add(issue.code)
            codes.append(issue.code)
        return codes
    def _query_target_decision(
        self,
        candidates: list[QueryTargetCandidate],
    ) -> QueryTargetDecision:
        if not candidates:
            return QueryTargetDecision(
                status="no_candidate",
                summary=(
                    "No query target candidate is available; inspect issues and "
                    "record storage/path metadata before planning a query."
                ),
                candidate_index=None,
                candidate_path=None,
                candidate_path_status=None,
                direct_review_required=None,
                selected_candidate_direct_clean=None,
                reason_codes=[],
            )

        indexed_candidates = list(enumerate(candidates))
        ready_candidates = [
            item
            for item in indexed_candidates
            if item[1].candidate_path_status == "ready"
            and not item[1].review_required
        ]
        if ready_candidates:
            index, candidate = min(
                ready_candidates,
                key=self._query_target_candidate_decision_rank,
            )
            ready_candidate_indexes = [item_index for item_index, _ in ready_candidates]
            unselected_ready_candidate_indexes = [
                item_index
                for item_index in ready_candidate_indexes
                if item_index != index
            ]
            route_intent_review_candidate_indexes = (
                self._query_target_route_intent_review_candidate_indexes(
                    candidate,
                    candidates,
                    unselected_ready_candidate_indexes,
                )
            )
            return self._query_target_decision_for_candidate(
                candidate,
                index=index,
                status="ready",
                summary=(
                    f"Candidate {index} is ready for query planning; review "
                    "analysis_warnings and caveats before trusting results."
                ),
                selection_mode="automatic",
                peer_ready_requires_intent_review=bool(
                    unselected_ready_candidate_indexes
                ),
                selection_caution=self._query_target_selection_caution(
                    unselected_ready_candidate_indexes,
                    selection_mode="automatic",
                    route_intent_review_candidate_indexes=(
                        route_intent_review_candidate_indexes
                    ),
                ),
                route_intent_review_candidate_indexes=(
                    route_intent_review_candidate_indexes
                ),
            )

        context_blocked_candidates = [
            item
            for item in indexed_candidates
            if item[1].review_required and not item[1].direct_review_required
        ]
        if context_blocked_candidates:
            index, candidate = min(
                context_blocked_candidates,
                key=self._query_target_candidate_decision_rank,
            )
            direct_clean_candidate_indexes = (
                self._query_direct_clean_candidate_indexes(candidates)
            )
            unselected_direct_clean_candidate_indexes = [
                item_index
                for item_index in direct_clean_candidate_indexes
                if item_index != index
            ]
            route_intent_review_candidate_indexes = (
                self._query_target_route_intent_review_candidate_indexes(
                    candidate,
                    candidates,
                    unselected_direct_clean_candidate_indexes,
                )
            )
            return self._query_target_decision_for_candidate(
                candidate,
                index=index,
                status="context_blocked",
                summary=(
                    f"Candidate {index} has no direct warning or error, but "
                    "the overall query context has blockers elsewhere; inspect "
                    "issues before executing it."
                ),
                selection_mode="automatic",
                selection_caution=self._query_target_selection_caution(
                    [],
                    selection_mode="automatic",
                    route_intent_review_candidate_indexes=(
                        route_intent_review_candidate_indexes
                    ),
                ),
                route_intent_review_candidate_indexes=(
                    route_intent_review_candidate_indexes
                ),
            )

        index, candidate = min(
            indexed_candidates,
            key=self._query_target_candidate_decision_rank,
        )
        route_intent_review_candidate_indexes = (
            self._query_target_route_intent_review_candidate_indexes(
                candidate,
                candidates,
                [
                    item_index
                    for item_index, item_candidate in indexed_candidates
                    if item_index != index
                    and self._query_context_candidate_only_layout_blocked(
                        item_candidate
                    )
                ],
            )
        )
        return self._query_target_decision_for_candidate(
            candidate,
            index=index,
            status="candidate_needs_review",
            summary=(
                f"No candidate is ready; candidate {index} is the first "
                "review target to inspect before executable query use."
            ),
            selection_mode="automatic",
            selection_caution=self._query_target_selection_caution(
                [],
                selection_mode="automatic",
                route_intent_review_candidate_indexes=(
                    route_intent_review_candidate_indexes
                ),
            ),
            route_intent_review_candidate_indexes=(
                route_intent_review_candidate_indexes
            ),
        )
    @staticmethod
    def _query_target_selection_reason_codes(
        candidate: QueryTargetCandidate | None,
        *,
        status: str,
        selection_mode: str,
        peer_ready_requires_intent_review: bool,
        route_intent_review_candidate_indexes: list[int] | None = None,
    ) -> list[str]:
        codes: list[str] = []
        if selection_mode == "automatic":
            codes.append("automatic_candidate_rank")
        else:
            codes.append(f"explicit_{selection_mode}_selection")
        codes.append(f"decision_status_{status}")
        if candidate is not None:
            codes.append(f"template_source_{candidate.template_source}")
            if candidate.candidate_path_status is not None:
                codes.append(
                    f"candidate_path_status_{candidate.candidate_path_status}"
                )
        if peer_ready_requires_intent_review:
            codes.append("peer_ready_candidates_present")
        if route_intent_review_candidate_indexes:
            codes.append("route_intent_review_candidates_present")
        return codes
    def _query_target_selection_caution(
        self,
        unselected_ready_candidate_indexes: list[int],
        *,
        selection_mode: str,
        route_intent_review_candidate_indexes: list[int] | None = None,
    ) -> str | None:
        route_intent_caution = self._query_target_route_intent_caution(
            route_intent_review_candidate_indexes or []
        )
        if not unselected_ready_candidate_indexes:
            return route_intent_caution
        indexes = ", ".join(str(index) for index in unselected_ready_candidate_indexes)
        selection_note = (
            "Automatic selection uses DoxaBase precedence, not project intent"
            if selection_mode == "automatic"
            else f"Explicit {selection_mode} selection used the caller selector"
        )
        caution = (
            "Peer direct-ready query target candidate(s) exist. "
            f"{selection_note}; inspect "
            f"candidate card(s) {indexes} or pass an explicit candidate_selector "
            "before unattended execution."
        )
        if route_intent_caution is not None:
            caution = f"{caution} {route_intent_caution}"
        return caution
    @staticmethod
    def _query_target_route_intent_caution(
        candidate_indexes: Iterable[int],
    ) -> str | None:
        indexes = list(candidate_indexes)
        if not indexes:
            return None
        formatted = ", ".join(str(index) for index in indexes)
        return (
            "Candidate card(s) "
            f"{formatted} carry production/current/canonical route role intent "
            "that automatic precedence did not select; review route_roles and "
            "pass candidate_selector when that route is intended."
        )
    def _query_target_decision_reason_codes(
        self,
        candidate: QueryTargetCandidate,
        *,
        status: str,
    ) -> list[str]:
        if status == "context_blocked":
            reasons = [
                reason
                for reason in self._query_target_blocking_reasons(
                    candidate.review_reasons
                )
                if reason.code == "query_context_has_other_blockers"
            ]
        elif status == "candidate_needs_review":
            reasons = self._query_target_blocking_reasons(
                candidate.direct_review_reasons
            )
        else:
            reasons = self._query_target_blocking_reasons(candidate.review_reasons)
        if not reasons:
            reasons = self._query_target_blocking_reasons(candidate.review_reasons)

        codes: list[str] = []
        seen: set[str] = set()
        for reason in reasons:
            if reason.code in seen:
                continue
            seen.add(reason.code)
            codes.append(reason.code)
        return codes
    def _query_target_blocking_reasons(
        self,
        reasons: Iterable[QueryPlanningIssue],
    ) -> list[QueryPlanningIssue]:
        return [
            reason
            for reason in reasons
            if reason.severity in {"error", "warning"}
        ]
    def _query_target_blocking_severity_rank(
        self,
        reasons: list[QueryPlanningIssue],
    ) -> int:
        if any(reason.severity == "error" for reason in reasons):
            return 2
        if any(reason.severity == "warning" for reason in reasons):
            return 1
        return 0
    def _query_target_direct_review_reasons(
        self,
        review_reasons: list[QueryPlanningIssue],
    ) -> list[QueryPlanningIssue]:
        return [
            reason
            for reason in review_reasons
            if reason.code != "query_context_has_other_blockers"
        ]
    def _query_target_context_blocking_reasons(
        self,
        review_reasons: Iterable[QueryPlanningIssue],
    ) -> list[QueryPlanningIssue]:
        return [
            reason
            for reason in self._query_target_blocking_reasons(review_reasons)
            if reason.code == "query_context_has_other_blockers"
        ]
    def _query_database_relation_template_source_issue(
        self,
        *,
        template: str,
        template_source: str,
        source_resource: ResourceSummary,
        storage_access: StorageAccessDescription,
    ) -> QueryPlanningIssue | None:
        if not self._is_database_storage(storage_access.storage_protocol):
            return None
        if template_source in {"storage_access", "storage_access_location"}:
            return None
        source_label = source_resource.label or source_resource.iri
        return QueryPlanningIssue(
            code="database_relation_template_source_mismatch",
            severity="warning",
            message=(
                "Database storage candidate uses a path template from "
                f"{source_label}; dataset and partition path templates are "
                "file/object locations, not database relation identifiers. "
                "Record the database relation as a storage-access path_template "
                "before database handoff."
            ),
            resource=self._summary_from_description(storage_access),
            details={
                "template": template,
                "template_source": template_source,
                "template_source_resource_iri": source_resource.iri,
                "storage_access_iri": storage_access.iri,
                "storage_protocol_iri": (
                    storage_access.storage_protocol.iri
                    if storage_access.storage_protocol is not None
                    else None
                ),
                "allowed_relation_template_sources": ["storage_access"],
                "repair_hint": self._query_database_relation_template_repair_hint(
                    template=template,
                    template_source=template_source,
                    source_resource=source_resource,
                    storage_access=storage_access,
                ),
            },
        )
    def _query_layout_signature_path_extension_mismatch(
        self,
        candidate: QueryTargetCandidate,
        file_format_iri: str | None,
    ) -> bool:
        path_format = self._query_candidate_path_extension_format(
            candidate.candidate_path,
        )
        if path_format is None or file_format_iri is None:
            return False
        values = [
            file_format_iri,
            self._compact_iri(file_format_iri),
            self._local_name(file_format_iri),
        ]
        text = " ".join(value for value in values if value).lower()
        layout_format = None
        if "parquet" in text:
            layout_format = "parquet"
        elif "csv" in text:
            layout_format = "csv"
        return layout_format is not None and layout_format != path_format
    def _query_storage_object_location_template_issue(
        self,
        *,
        template: str,
        template_source: str,
        source_resource: ResourceSummary,
        storage_access: StorageAccessDescription,
    ) -> QueryPlanningIssue | None:
        if self._is_database_storage(storage_access.storage_protocol):
            return None
        if storage_access.location_kind != "object" or not storage_access.storage_root:
            return None
        if template_source == "storage_access_location":
            return None
        source_label = source_resource.label or source_resource.iri
        access_resource = self._summary_from_description(storage_access)
        return QueryPlanningIssue(
            code="storage_object_location_has_path_template",
            severity="warning",
            message=(
                "Storage access location_kind='object' says the storage root "
                "names the dataset object/location exactly, but a path template "
                f"from {source_label} would be appended to that object root. "
                "Use the storage_access_location candidate for the exact object "
                "route, or model the storage root as a directory/prefix if "
                "templates should be joined."
            ),
            resource=access_resource,
            details={
                "template": template,
                "template_source": template_source,
                "template_source_resource_iri": source_resource.iri,
                "storage_access_iri": storage_access.iri,
                "storage_root": storage_access.storage_root,
                "location_kind": storage_access.location_kind,
            },
        )
    def _query_database_relation_template_missing_issue(
        self,
        storage_access: StorageAccessDescription,
    ) -> QueryPlanningIssue:
        access_resource = self._summary_from_description(storage_access)
        return QueryPlanningIssue(
            code="database_relation_template_missing",
            severity="warning",
            message=(
                "Database storage root is the only candidate location, but no "
                "storage-access path_template records a relation identifier. "
                "Record the schema, table, or relation as a storage-access "
                "path_template before database handoff."
            ),
            resource=access_resource,
            details={
                "storage_access_iri": storage_access.iri,
                "storage_protocol_iri": (
                    storage_access.storage_protocol.iri
                    if storage_access.storage_protocol is not None
                    else None
                ),
                "storage_root": storage_access.storage_root,
                "location_kind": storage_access.location_kind,
                "allowed_relation_template_sources": ["storage_access"],
                "repair_hint": (
                    self._query_database_relation_template_missing_repair_hint(
                        storage_access
                    )
                ),
            },
        )
    def _query_target_review_reasons(
        self,
        dataset: DatasetDescription,
        issues: list[QueryPlanningIssue],
        *,
        source_resource: ResourceSummary,
        storage_access: ResourceSummary | None,
    ) -> list[QueryPlanningIssue]:
        related_iris = {dataset.iri, source_resource.iri}
        if storage_access is not None:
            related_iris.add(storage_access.iri)
        related_iris.update(layout.iri for layout in dataset.physical_layouts)
        repairable_layout_iris = {
            layout.iri
            for layout in dataset.physical_layouts
            if self._physical_layout_has_verified_matching_sibling(
                layout,
                dataset.physical_layouts,
            )
        }

        review_reasons: list[QueryPlanningIssue] = []
        seen: set[tuple[str, str | None]] = set()
        excluded_blockers: list[QueryPlanningIssue] = []
        for issue in issues:
            if self._is_candidate_metadata_issue(issue):
                continue
            resource_iri = issue.resource.iri if issue.resource is not None else None
            if (
                issue.code == "layout_needs_verification"
                and resource_iri in repairable_layout_iris
            ):
                if issue.severity in {"error", "warning"}:
                    excluded_blockers.append(issue)
                continue
            if resource_iri is not None and resource_iri not in related_iris:
                if issue.severity in {"error", "warning"}:
                    excluded_blockers.append(issue)
                continue
            key = (issue.code, resource_iri)
            if key in seen:
                continue
            seen.add(key)
            review_reasons.append(issue)
        if excluded_blockers:
            severity = (
                "error"
                if any(issue.severity == "error" for issue in excluded_blockers)
                else "warning"
            )
            excluded_resource_iris = [
                issue.resource.iri
                for issue in excluded_blockers
                if issue.resource is not None
            ]
            review_reasons.append(
                QueryPlanningIssue(
                    code="query_context_has_other_blockers",
                    severity=severity,
                    message=(
                        "Overall query context has "
                        f"{len(excluded_blockers)} blocking/review issue(s) "
                        "on other dataset metadata; inspect context.issues "
                        "before executing this candidate."
                    ),
                    resource=ResourceSummary(
                        iri=dataset.iri,
                        label=dataset.label or self._local_name(dataset.iri),
                        description=dataset.description,
                    ),
                    details={
                        "excluded_blocker_count": len(excluded_blockers),
                        "excluded_blocker_codes": self._query_issue_codes(
                            excluded_blockers
                        ),
                        "excluded_blocker_resource_iris": list(
                            dict.fromkeys(excluded_resource_iris)
                        ),
                    },
                )
            )
        return review_reasons
    def _query_file_format_layout_route_kind(
        self,
        file_format_iri: str | None,
    ) -> TypingLiteral["database", "file"] | None:
        if file_format_iri is None:
            return None
        file_format = self.expand_iri(file_format_iri)
        database_formats = {
            self.expand_iri("rc:PostgreSQLTable"),
            self.expand_iri("rc:SQLiteTable"),
            self.expand_iri("rc:MySQLTable"),
        }
        if file_format in database_formats:
            return "database"
        file_formats = {
            self.expand_iri("rc:CSV"),
            self.expand_iri("rc:Parquet"),
        }
        if file_format in file_formats:
            return "file"
        return None
    def _query_analysis_warnings(
        self,
        dataset: DatasetDescription,
    ) -> list[QueryPlanningIssue]:
        warnings: list[QueryPlanningIssue] = []
        seen: set[tuple[str, str]] = set()
        for scope, caveats in (
            ("direct", dataset.caveats),
            ("upstream", dataset.upstream_caveats),
        ):
            for caveat in caveats:
                key = (scope, caveat.iri)
                if key in seen:
                    continue
                seen.add(key)
                summary = self._summary_from_description(caveat)
                severity = self._analysis_caveat_severity(caveat.severity)
                label = (
                    caveat.label or caveat.description or caveat.iri
                ).strip()
                label = label.rstrip(".?!")
                message = (
                    f"{scope.capitalize()} caveat may affect query interpretation: "
                    f"{label}."
                )
                if caveat.impact:
                    message = f"{message} Impact: {caveat.impact}"
                warnings.append(
                    QueryPlanningIssue(
                        code=f"{scope}_analysis_caveat",
                        severity=severity,
                        message=message,
                        domain="analysis",
                        resource=summary,
                        details={
                            "scope": scope,
                            "caveat_iri": caveat.iri,
                            "caveat_label": caveat.label,
                            "caveat_description": caveat.description,
                            "caveat_impact": caveat.impact,
                            "caveat_severity_iri": (
                                caveat.severity.iri
                                if caveat.severity is not None
                                else None
                            ),
                            "caveat_severity_label": (
                                caveat.severity.label
                                if caveat.severity is not None
                                else None
                            ),
                        },
                    )
                )
        severity_rank = {"warning": 0, "info": 1}
        return sorted(
            warnings,
            key=lambda warning: (
                severity_rank.get(warning.severity, 2),
                warning.code,
                warning.resource.iri if warning.resource is not None else "",
            ),
        )
    def _query_readiness_note(
        self,
        readiness: str,
        *,
        issues: list[QueryPlanningIssue],
        analysis_warnings: list[QueryPlanningIssue],
    ) -> str:
        notes = {
            "ready_for_query_planning": (
                "Enough non-secret physical metadata is present to plan a query."
            ),
            "needs_review": (
                "Physical query planning is possible, but metadata warnings should "
                "be reviewed first."
            ),
            "insufficient_metadata": (
                "Required physical metadata is missing, so query planning is "
                "incomplete."
            ),
            "blocked_by_contradiction": (
                "A layout contradiction blocks physical query planning until it is "
                "resolved."
            ),
        }
        note = notes.get(readiness, "Query planning readiness is unknown.")
        if any(issue.severity == "info" for issue in issues):
            note = (
                f"{note} Informational physical metadata notes are present but "
                "do not block planning."
            )
        if analysis_warnings:
            note = (
                f"{note} Analysis warnings are separate caveats to review before "
                "trusting aggregations or interpretations."
            )
        return note
    def _add_layout_status_issue(
        self,
        issues: list[QueryPlanningIssue],
        *,
        status: ResourceSummary | None,
        note: str | None,
        resource: ResourceSummary,
        context: str,
        include_missing_status: bool = False,
    ) -> None:
        if status is None:
            if include_missing_status:
                message = (
                    f"No layout verification status is recorded for {context}; "
                    "treat the path/layout metadata as needing confirmation "
                    "before executable use."
                )
                if note:
                    message = f"{message} Note: {note}"
                issues.append(
                    QueryPlanningIssue(
                        code="verification_status_not_recorded",
                        severity="info",
                        message=message,
                        resource=resource,
                    )
                )
            return
        verified_statuses = {
            self.expand_iri("rc:VerifiedByListingLayout"),
            self.expand_iri("rc:VerifiedByQueryLayout"),
        }
        if status.iri in verified_statuses:
            return
        if status.iri == self.expand_iri("rc:ContradictedLayout"):
            severity = "error"
            code = "contradicted_layout"
            message = f"{context} is marked contradicted."
        else:
            severity = "warning"
            code = "layout_needs_verification"
            message = f"{context} has not been verified by listing or query."
        if note:
            message = f"{message} Note: {note}"
        issues.append(
            QueryPlanningIssue(
                code=code,
                severity=severity,
                message=message,
                resource=resource,
            )
        )
    @staticmethod
    def _query_execution_status(status: str) -> str:
        status_value = status.strip().lower()
        allowed = {"succeeded", "failed", "partial", "cancelled", "blocked"}
        if status_value not in allowed:
            allowed_display = ", ".join(sorted(allowed))
            raise DoxaBaseError(
                f"execution_status must be one of: {allowed_display}"
            )
        return status_value
    def _relationship_endpoint_values(
        self,
        plural_name: str,
        singular_value: str | None,
        plural_values: Iterable[str] | str | None,
    ) -> list[str]:
        values: list[str] = []
        if singular_value is not None:
            values.extend(self._string_values(plural_name, singular_value))
        values.extend(self._string_values(plural_name, plural_values))
        return list(dict.fromkeys(values))
    def _normalise_relationship_endpoint_specs(
        self,
        name: str,
        values: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
        *,
        relationship_iri: str,
        direction: TypingLiteral["source", "target"],
    ) -> list[dict[str, Any]]:
        if values is None:
            return []
        if isinstance(values, MappingABC):
            raw_values = [values]
        else:
            raw_values = list(values)
        specs: list[dict[str, Any]] = []
        for index, value in enumerate(raw_values, start=1):
            if not isinstance(value, MappingABC):
                raise DoxaBaseError(f"{name}[{index}] must be a mapping")
            dataset = value.get("dataset", value.get("dataset_iri"))
            if not isinstance(dataset, str) or not dataset:
                raise DoxaBaseError(
                    f"{name}[{index}] requires a non-empty dataset or dataset_iri"
                )
            role = value.get("role")
            if role is not None and not isinstance(role, str):
                raise DoxaBaseError(f"{name}[{index}].role must be a string")
            order_value = value.get("order", value.get("sequence_index", index))
            if not isinstance(order_value, int) or order_value < 1:
                raise DoxaBaseError(
                    f"{name}[{index}].order must be a positive integer"
                )
            endpoint_iri = value.get("iri")
            if endpoint_iri is not None and not isinstance(endpoint_iri, str):
                raise DoxaBaseError(f"{name}[{index}].iri must be a string")
            specs.append(
                {
                    "iri": (
                        self._required_iri(f"{name}[{index}].iri", endpoint_iri)
                        if endpoint_iri is not None
                        else f"{relationship_iri}/{direction}-endpoint/{index}"
                    ),
                    "field": f"{name}[{index}].dataset",
                    "dataset": dataset,
                    "direction": direction,
                    "role": role,
                    "order": order_value,
                }
            )
        return specs
    def _validate_relationship_column_resources(
        self,
        *,
        from_column: str | None,
        to_column: str | None,
        identifying_columns: Iterable[str],
        source_columns: Iterable[str],
        derived_columns: Iterable[str],
        group_by_columns: Iterable[str],
        aggregated_columns: Iterable[Mapping[str, Any]],
    ) -> None:
        fields: list[tuple[str, str]] = []
        if from_column is not None:
            fields.append(("from_column", from_column))
        if to_column is not None:
            fields.append(("to_column", to_column))
        fields.extend(("identifying_columns", value) for value in identifying_columns)
        fields.extend(("source_columns", value) for value in source_columns)
        fields.extend(("derived_columns", value) for value in derived_columns)
        fields.extend(("group_by_columns", value) for value in group_by_columns)
        for index, aggregated_column in enumerate(aggregated_columns, start=1):
            fields.append(
                (
                    f"aggregated_columns[{index}].target_column",
                    str(aggregated_column["target_column"]),
                )
            )
            fields.extend(
                (
                    f"aggregated_columns[{index}].source_columns",
                    str(value),
                )
                for value in aggregated_column["source_columns"]
            )
            ordering = aggregated_column["within_group_ordering"]
            if ordering is not None:
                fields.append(
                    (
                        f"aggregated_columns[{index}].within_group_ordering",
                        str(ordering),
                    )
                )

        for field_name, value in fields:
            self._validate_relationship_column_resource(field_name, value)
    def _validate_relationship_column_resource(
        self,
        field_name: str,
        value: str,
    ) -> None:
        column_iri = str(self._resource_ref(field_name, value))
        data_asset_types = {
            self.expand_iri("rc:DataAsset"),
            self.expand_iri("rc:Dataset"),
            self.expand_iri("rc:Table"),
        }
        resource_types = set(
            self._types_from_graphs(self._expand_graphs(["all"]), column_iri)
        )
        matching_types = sorted(resource_types & data_asset_types)
        if matching_types:
            type_labels = ", ".join(
                self._compact_iri(type_iri) for type_iri in matching_types
            )
            raise DoxaBaseError(
                f"{field_name} points to a data asset resource, not an rc:Column: "
                f"{column_iri} ({type_labels}). Use source_dataset/target_dataset "
                "for dataset endpoints, or record_map_asset_transform for asset-level "
                "transform conditions, formulas, and tuple grain."
            )
        column_type = self.expand_iri("rc:Column")
        if column_type in resource_types:
            return
        raise DoxaBaseError(
            f"{field_name} points to {column_iri}, which is not a recorded "
            "rc:Column. Record the column first with record_map_column, then "
            "reference the column IRI in relationship column fields."
        )
    def _delete_existing_relationship_endpoint_triples(
        self,
        relationship_iri: str,
    ) -> None:
        endpoint_iris = self._objects(
            ["map"],
            relationship_iri,
            "rc:hasRelationshipEndpoint",
        )
        if not endpoint_iris:
            return
        predicates = [
            str(RDF.type),
            self.expand_iri("rc:endpointDataset"),
            self.expand_iri("rc:endpointDirection"),
            self.expand_iri("rc:endpointRole"),
            self.expand_iri("rc:endpointOrder"),
        ]
        placeholders = ",".join("?" for _ in predicates)
        for endpoint_iri in endpoint_iris:
            self._conn.execute(
                f"""
                DELETE FROM quads
                WHERE graph = 'map'
                  AND subject = ?
                  AND predicate IN ({placeholders})
                """,
                [endpoint_iri, *predicates],
            )
        self._conn.commit()
    def _describe_query_snippet(
        self,
        snippet_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> QuerySnippetDescription:
        return QuerySnippetDescription(
            iri=snippet_iri,
            label=self._label_from_graphs(lookup_graphs, snippet_iri),
            description=self._description_from_graphs(lookup_graphs, snippet_iri),
            query_text=self._first_object(data_graphs, snippet_iri, "rc:queryText"),
            query_language=self._first_object(
                data_graphs,
                snippet_iri,
                "rc:queryLanguage",
            ),
            query_engine=self._first_object(data_graphs, snippet_iri, "rc:queryRuntime"),
        )
    def _describe_partition(
        self,
        partition_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> PartitionDescription:
        partition_columns = [
            self._resource_summary(lookup_graphs, partition_column)
            for partition_column in self._objects(
                data_graphs,
                partition_iri,
                "rc:partitionColumn",
            )
        ]
        granularity = self._first_object(data_graphs, partition_iri, "rc:partitionGranularity")
        redundant_partition_key = self._first_object(
            data_graphs,
            partition_iri,
            "rc:redundantPartitionKey",
        )
        return PartitionDescription(
            iri=partition_iri,
            label=self._label_from_graphs(lookup_graphs, partition_iri),
            description=self._description_from_graphs(lookup_graphs, partition_iri),
            partition_column=partition_columns[0] if partition_columns else None,
            partition_columns=partition_columns,
            granularity=(
                self._resource_summary(lookup_graphs, granularity)
                if granularity is not None
                else None
            ),
            path_template=self._first_object(data_graphs, partition_iri, "rc:pathTemplate"),
            redundant_partition_key=(
                self._resource_summary(lookup_graphs, redundant_partition_key)
                if redundant_partition_key is not None
                else None
            ),
            layout_verification_status=self._optional_resource_summary(
                lookup_graphs,
                self._first_object(
                    data_graphs,
                    partition_iri,
                    "rc:layoutVerificationStatus",
                ),
            ),
            layout_verification_note=self._first_object(
                data_graphs,
                partition_iri,
                "rc:layoutVerificationNote",
            ),
        )
    def _dataset_endpoint_relationship_direction(
        self,
        relationship_iri: str,
        lookup_graphs: list[str],
        *,
        source_side: bool,
    ) -> str:
        relationship_kind = self._first_matching_type(
            self._types_from_graphs(lookup_graphs, relationship_iri),
            [
                "rc:ForeignKey",
                "rc:SharedIdentifier",
                "rc:Derivation",
                "rc:Aggregation",
                "rc:Relationship",
            ],
        )
        if relationship_kind == self.expand_iri("rc:Derivation"):
            return "source_of_derivation" if source_side else "derived_from"
        if relationship_kind == self.expand_iri("rc:Aggregation"):
            return "source_of_aggregation" if source_side else "aggregated_from"
        return "source_of" if source_side else "target_of"
    def _related_datasets_from_column_relationship(
        self,
        dataset_iri: str,
        relationship: RelationshipDescription,
        lookup_graphs: list[str],
    ) -> list[RelatedDatasetDescription]:
        related: list[RelatedDatasetDescription] = []
        if relationship.foreign_key_from is not None and relationship.foreign_key_to is not None:
            from_dataset = relationship.foreign_key_from.owning_dataset_iri
            to_dataset = relationship.foreign_key_to.owning_dataset_iri
            if from_dataset == dataset_iri and to_dataset and to_dataset != dataset_iri:
                related.append(
                    self._related_dataset(
                        to_dataset,
                        "source_of",
                        relationship.iri,
                        lookup_graphs,
                    )
                )
            if to_dataset == dataset_iri and from_dataset and from_dataset != dataset_iri:
                related.append(
                    self._related_dataset(
                        from_dataset,
                        "target_of",
                        relationship.iri,
                        lookup_graphs,
                    )
                )

        shared_identifier_datasets = {
            column.owning_dataset_iri
            for column in relationship.identifying_columns
            if column.owning_dataset_iri is not None
        }
        if dataset_iri in shared_identifier_datasets:
            for related_dataset_iri in sorted(shared_identifier_datasets - {dataset_iri}):
                related.append(
                    self._related_dataset(
                        related_dataset_iri,
                        "shares_identifier_with",
                        relationship.iri,
                        lookup_graphs,
                    )
                )

        source_datasets = {
            column.owning_dataset_iri
            for column in relationship.source_columns
            if column.owning_dataset_iri is not None
        }
        source_datasets.update(
            dataset.iri for dataset in relationship.source_datasets
        )
        derived_datasets = {
            column.owning_dataset_iri
            for column in relationship.derived_columns
            if column.owning_dataset_iri is not None
        }
        derived_datasets.update(
            dataset.iri for dataset in relationship.target_datasets
        )
        if relationship.relationship_kind == self.expand_iri("rc:Derivation"):
            if dataset_iri in source_datasets:
                for related_dataset_iri in sorted(derived_datasets - {dataset_iri}):
                    related.append(
                        self._related_dataset(
                            related_dataset_iri,
                            "source_of_derivation",
                            relationship.iri,
                            lookup_graphs,
                        )
                    )
            if dataset_iri in derived_datasets:
                for related_dataset_iri in sorted(source_datasets - {dataset_iri}):
                    related.append(
                        self._related_dataset(
                            related_dataset_iri,
                            "derived_from",
                            relationship.iri,
                            lookup_graphs,
                        )
                    )

        aggregation_source_datasets: set[str] = set()
        aggregation_source_datasets.update(
            dataset.iri for dataset in relationship.source_datasets
        )
        for column in relationship.group_by_columns:
            if column.owning_dataset_iri is not None:
                aggregation_source_datasets.add(column.owning_dataset_iri)
        for aggregated_column in relationship.aggregated_columns:
            for column in aggregated_column.source_columns:
                if column.owning_dataset_iri is not None:
                    aggregation_source_datasets.add(column.owning_dataset_iri)
            if (
                aggregated_column.within_group_ordering is not None
                and aggregated_column.within_group_ordering.owning_dataset_iri is not None
            ):
                aggregation_source_datasets.add(
                    aggregated_column.within_group_ordering.owning_dataset_iri
                )

        aggregation_target_datasets: set[str] = set()
        aggregation_target_datasets.update(
            dataset.iri for dataset in relationship.target_datasets
        )
        for aggregated_column in relationship.aggregated_columns:
            if (
                aggregated_column.target_column is not None
                and aggregated_column.target_column.owning_dataset_iri is not None
            ):
                aggregation_target_datasets.add(
                    aggregated_column.target_column.owning_dataset_iri
                )

        if relationship.relationship_kind == self.expand_iri("rc:Aggregation"):
            if dataset_iri in aggregation_source_datasets:
                for related_dataset_iri in sorted(
                    aggregation_target_datasets - {dataset_iri}
                ):
                    related.append(
                        self._related_dataset(
                            related_dataset_iri,
                            "source_of_aggregation",
                            relationship.iri,
                            lookup_graphs,
                        )
                    )
            if dataset_iri in aggregation_target_datasets:
                for related_dataset_iri in sorted(
                    aggregation_source_datasets - {dataset_iri}
                ):
                    related.append(
                        self._related_dataset(
                            related_dataset_iri,
                            "aggregated_from",
                            relationship.iri,
                            lookup_graphs,
                        )
                    )
        return related
    def _relationship_kind_priority(self, relationship_kind: str | None) -> int:
        return {
            self.expand_iri("rc:ForeignKey"): 0,
            self.expand_iri("rc:SharedIdentifier"): 1,
            self.expand_iri("rc:Derivation"): 2,
            self.expand_iri("rc:Aggregation"): 3,
            self.expand_iri("rc:Relationship"): 4,
        }.get(relationship_kind, 99)
    def _relationship_columns_between_datasets(
        self,
        dataset_iri: str,
        related_dataset_iri: str,
        relationship: RelationshipDescription,
    ) -> list[ResourceSummary]:
        candidate_columns: list[ResourceSummary] = []
        for column in (
            relationship.foreign_key_from,
            relationship.foreign_key_to,
            *relationship.identifying_columns,
            *relationship.source_columns,
            *relationship.derived_columns,
            *relationship.group_by_columns,
            *[
                column
                for aggregated_column in relationship.aggregated_columns
                for column in (
                    aggregated_column.target_column,
                    *aggregated_column.source_columns,
                    aggregated_column.within_group_ordering,
                )
                if column is not None
            ],
        ):
            if column is not None and column.owning_dataset_iri in {
                dataset_iri,
                related_dataset_iri,
            }:
                candidate_columns.append(column)

        return list(
            {
                column.iri: column
                for column in sorted(
                    candidate_columns,
                    key=lambda item: (
                        item.owning_dataset_label or "",
                        item.column_name or "",
                        item.iri,
                    ),
                )
            }.values()
        )
    def _relationships_for_dataset(
        self,
        dataset_iri: str,
        column_iris: Iterable[str],
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> list[RelationshipDescription]:
        relationship_iris: set[str] = set()
        relationship_iris.update(
            self._subjects(data_graphs, "rc:sourceDataset", dataset_iri)
        )
        relationship_iris.update(
            self._subjects(data_graphs, "rc:targetDataset", dataset_iri)
        )
        for output_iri in self._subjects(data_graphs, "rc:outputDataset", dataset_iri):
            relationship_iris.update(
                self._subjects(data_graphs, "rc:hasTransformOutput", output_iri)
            )
        for condition_iri in self._subjects(
            data_graphs,
            "rc:appliesToDataset",
            dataset_iri,
        ):
            relationship_iris.update(
                self._subjects(
                    data_graphs,
                    "rc:hasTransformCondition",
                    condition_iri,
                )
            )
        for grain_iri in self._objects(data_graphs, dataset_iri, "rc:hasGrain"):
            for output_iri in self._subjects(data_graphs, "rc:outputGrain", grain_iri):
                relationship_iris.update(
                    self._subjects(data_graphs, "rc:hasTransformOutput", output_iri)
                )
        for column_iri in column_iris:
            for predicate in (
                "rc:foreignKeyFrom",
                "rc:foreignKeyTo",
                "rc:identifyingColumn",
                "rc:sourceColumn",
                "rc:derivedColumn",
                "rc:groupByColumn",
            ):
                relationship_iris.update(
                    self._subjects(data_graphs, predicate, column_iri)
                )
            for predicate in (
                "rc:targetColumn",
                "rc:aggregationSourceColumn",
                "rc:withinGroupOrdering",
            ):
                for aggregated_column_iri in self._subjects(
                    data_graphs,
                    predicate,
                    column_iri,
                ):
                    relationship_iris.update(
                        self._subjects(
                            data_graphs,
                            "rc:hasAggregatedColumn",
                            aggregated_column_iri,
                        )
                    )
            for component_iri in self._subjects(
                data_graphs,
                "rc:grainColumn",
                column_iri,
            ):
                for grain_iri in self._subjects(
                    data_graphs,
                    "rc:hasGrainComponent",
                    component_iri,
                ):
                    for output_iri in self._subjects(
                        data_graphs,
                        "rc:outputGrain",
                        grain_iri,
                    ):
                        relationship_iris.update(
                            self._subjects(
                                data_graphs,
                                "rc:hasTransformOutput",
                                output_iri,
                            )
                        )

        return [
            self._describe_relationship(relationship_iri, data_graphs, lookup_graphs)
            for relationship_iri in sorted(relationship_iris)
        ]
    def _relationship_endpoint_descriptions(
        self,
        relationship_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> list[RelationshipEndpointDescription]:
        endpoints = [
            self._describe_relationship_endpoint(
                endpoint_iri,
                data_graphs,
                lookup_graphs,
            )
            for endpoint_iri in self._objects(
                data_graphs,
                relationship_iri,
                "rc:hasRelationshipEndpoint",
            )
        ]
        direction_rank = {"source": 0, "target": 1}
        return sorted(
            endpoints,
            key=lambda endpoint: (
                direction_rank.get(endpoint.direction or "", 2),
                endpoint.order or 999999,
                endpoint.iri,
            ),
        )
    def _describe_relationship_endpoint(
        self,
        endpoint_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> RelationshipEndpointDescription:
        dataset_iri = self._first_object(
            data_graphs,
            endpoint_iri,
            "rc:endpointDataset",
        )
        direction_iri = self._first_object(
            data_graphs,
            endpoint_iri,
            "rc:endpointDirection",
        )
        direction = None
        if direction_iri == self.expand_iri("rc:SourceEndpoint"):
            direction = "source"
        elif direction_iri == self.expand_iri("rc:TargetEndpoint"):
            direction = "target"
        return RelationshipEndpointDescription(
            iri=endpoint_iri,
            dataset=self._optional_resource_summary(lookup_graphs, dataset_iri),
            direction=direction,
            direction_label=self._label_for_resource(direction_iri),
            role=self._first_object(data_graphs, endpoint_iri, "rc:endpointRole"),
            order=self._int_object(data_graphs, endpoint_iri, "rc:endpointOrder"),
        )
    @staticmethod
    def _relationship_dataset_iris_with_endpoint_order(
        dataset_iris: list[str],
        endpoints: list[RelationshipEndpointDescription],
    ) -> list[str]:
        ordered_endpoint_iris = [
            endpoint.dataset.iri
            for endpoint in endpoints
            if endpoint.dataset is not None
        ]
        return list(dict.fromkeys([*ordered_endpoint_iris, *dataset_iris]))
    def _describe_relationship(
        self,
        relationship_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> RelationshipDescription:
        types = self._types_from_graphs(data_graphs, relationship_iri)
        relationship_kind = self._first_matching_type(
            types,
            [
                "rc:ForeignKey",
                "rc:SharedIdentifier",
                "rc:Derivation",
                "rc:Aggregation",
                "rc:Relationship",
            ],
        )
        source_dataset_iris = self._objects(
            data_graphs,
            relationship_iri,
            "rc:sourceDataset",
        )
        target_dataset_iris = self._objects(
            data_graphs,
            relationship_iri,
            "rc:targetDataset",
        )
        endpoints = self._relationship_endpoint_descriptions(
            relationship_iri,
            data_graphs,
            lookup_graphs,
        )
        source_endpoints = [
            endpoint for endpoint in endpoints if endpoint.direction == "source"
        ]
        target_endpoints = [
            endpoint for endpoint in endpoints if endpoint.direction == "target"
        ]
        source_dataset_iris = self._relationship_dataset_iris_with_endpoint_order(
            source_dataset_iris,
            source_endpoints,
        )
        target_dataset_iris = self._relationship_dataset_iris_with_endpoint_order(
            target_dataset_iris,
            target_endpoints,
        )
        source_dataset = source_dataset_iris[0] if source_dataset_iris else None
        target_dataset = target_dataset_iris[0] if target_dataset_iris else None
        foreign_key_from = self._first_object(
            data_graphs,
            relationship_iri,
            "rc:foreignKeyFrom",
        )
        foreign_key_to = self._first_object(
            data_graphs,
            relationship_iri,
            "rc:foreignKeyTo",
        )
        referential_integrity = self._first_object(
            data_graphs,
            relationship_iri,
            "rc:referentialIntegrity",
        )
        derivation_function = self._first_object(
            data_graphs,
            relationship_iri,
            "rc:derivationFunction",
        )
        source_dataset_summary = self._optional_resource_summary(
            lookup_graphs,
            source_dataset,
        )
        target_dataset_summary = self._optional_resource_summary(
            lookup_graphs,
            target_dataset,
        )
        source_dataset_summaries = self._resource_summaries(
            lookup_graphs,
            source_dataset_iris,
        )
        target_dataset_summaries = self._resource_summaries(
            lookup_graphs,
            target_dataset_iris,
        )
        foreign_key_from_summary = self._optional_resource_summary(
            lookup_graphs,
            foreign_key_from,
        )
        foreign_key_to_summary = self._optional_resource_summary(
            lookup_graphs,
            foreign_key_to,
        )
        identifying_columns = self._resource_summaries(
            lookup_graphs,
            self._objects(data_graphs, relationship_iri, "rc:identifyingColumn"),
        )
        source_columns = self._resource_summaries(
            lookup_graphs,
            self._objects(data_graphs, relationship_iri, "rc:sourceColumn"),
        )
        derived_columns = self._resource_summaries(
            lookup_graphs,
            self._objects(data_graphs, relationship_iri, "rc:derivedColumn"),
        )
        group_by_columns = self._resource_summaries(
            lookup_graphs,
            self._objects(data_graphs, relationship_iri, "rc:groupByColumn"),
        )
        aggregated_columns = [
            self._describe_aggregated_column(
                aggregated_column_iri,
                data_graphs,
                lookup_graphs,
            )
            for aggregated_column_iri in self._objects(
                data_graphs,
                relationship_iri,
                "rc:hasAggregatedColumn",
            )
        ]
        transform_conditions = self._transform_condition_descriptions(
            relationship_iri,
            data_graphs,
            lookup_graphs,
        )
        transform_outputs = self._transform_output_descriptions(
            relationship_iri,
            transform_conditions,
            data_graphs,
            lookup_graphs,
        )
        return RelationshipDescription(
            iri=relationship_iri,
            label=self._display_label_from_graphs(lookup_graphs, relationship_iri),
            description=self._description_from_graphs(lookup_graphs, relationship_iri),
            types=types,
            relationship_kind=relationship_kind,
            relationship_kind_label=self._label_for_resource(relationship_kind),
            relationship_type=self._relationship_type_token(relationship_kind),
            source_dataset=source_dataset_summary,
            target_dataset=target_dataset_summary,
            source_datasets=source_dataset_summaries,
            target_datasets=target_dataset_summaries,
            endpoints=endpoints,
            source_endpoints=source_endpoints,
            target_endpoints=target_endpoints,
            foreign_key_from=foreign_key_from_summary,
            foreign_key_to=foreign_key_to_summary,
            referential_integrity=self._optional_resource_summary(
                lookup_graphs,
                referential_integrity,
            ),
            declared=self._bool_object(data_graphs, relationship_iri, "rc:declared"),
            identifying_columns=identifying_columns,
            source_columns=source_columns,
            derived_columns=derived_columns,
            derivation_function=self._optional_resource_summary(
                lookup_graphs,
                derivation_function,
            ),
            derivation_properties=self._resource_summaries(
                lookup_graphs,
                self._objects(
                    data_graphs,
                    relationship_iri,
                    "rc:hasDerivationProperty",
                ),
            ),
            group_by_columns=group_by_columns,
            aggregated_columns=aggregated_columns,
            transform_conditions=transform_conditions,
            transform_outputs=transform_outputs,
            source_caveats=self._relationship_source_caveats(
                data_graphs,
                lookup_graphs,
                source_dataset_summaries,
                foreign_key_from_summary,
                source_columns,
                group_by_columns,
                aggregated_columns,
            ),
        )
    def _transform_condition_descriptions(
        self,
        relationship_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> list[TransformConditionDescription]:
        conditions = [
            self._describe_transform_condition(
                condition_iri,
                data_graphs,
                lookup_graphs,
            )
            for condition_iri in self._objects(
                data_graphs,
                relationship_iri,
                "rc:hasTransformCondition",
            )
        ]
        return sorted(
            conditions,
            key=lambda condition: (condition.label or "", condition.iri),
        )
    def _transform_output_descriptions(
        self,
        relationship_iri: str,
        relationship_conditions: Iterable[TransformConditionDescription],
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> list[TransformOutputDescription]:
        conditions_by_iri = {
            condition.iri: condition for condition in relationship_conditions
        }
        outputs = [
            self._describe_transform_output(
                output_iri,
                conditions_by_iri,
                data_graphs,
                lookup_graphs,
            )
            for output_iri in self._objects(
                data_graphs,
                relationship_iri,
                "rc:hasTransformOutput",
            )
        ]
        return sorted(
            outputs,
            key=lambda output: (output.role or "", output.label or "", output.iri),
        )
    def _relationship_type_token(self, relationship_kind: str | None) -> str | None:
        return {
            self.expand_iri("rc:ForeignKey"): "foreign_key",
            self.expand_iri("rc:SharedIdentifier"): "shared_identifier",
            self.expand_iri("rc:Derivation"): "derivation",
            self.expand_iri("rc:Aggregation"): "aggregation",
        }.get(relationship_kind)
    def _normalise_relationship_type(
        self,
        relationship_type: str,
        *,
        allowed_tokens: Iterable[str] | None = None,
        context: str = "relationship_type",
    ) -> str:
        if not isinstance(relationship_type, str):
            raise DoxaBaseError(f"{context} must be a string")
        text = relationship_type.strip()
        allowed = tuple(allowed_tokens or RELATIONSHIP_TYPE_IRIS)
        allowed_set = set(allowed)
        token = RELATIONSHIP_TYPE_ALIASES.get(text)
        if token is None:
            token = RELATIONSHIP_TYPE_ALIASES.get(self.expand_iri(text))
        if token in allowed_set:
            return token
        token_list = ", ".join(f"'{value}'" for value in allowed)
        class_list = ", ".join(RELATIONSHIP_TYPE_IRIS[value] for value in allowed)
        raise DoxaBaseError(
            f"{context} must be one of: {token_list}; matching RDF classes are "
            f"also accepted: {class_list}"
        )
    def _first_matching_type(
        self,
        types: Iterable[str],
        candidates: Iterable[str],
    ) -> str | None:
        type_set = set(types)
        for candidate in candidates:
            expanded = self.expand_iri(candidate)
            if expanded in type_set:
                return expanded
        return None
    def _objects(self, graphs: list[str], subject: str, predicate: str) -> list[str]:
        graph_filter, params = self._graph_filter(graphs, alias="q")
        return [
            row["object"]
            for row in self._conn.execute(
                f"""
                SELECT DISTINCT q.object
                FROM quads q
                WHERE q.subject = ?
                  AND q.predicate = ?
                  {graph_filter}
                ORDER BY q.object
                """,
                [subject, self.expand_iri(predicate), *params],
            )
        ]
    def _synthesized_relationship_description_from_graphs(
        self,
        graphs: list[str],
        subject: str,
    ) -> str | None:
        types = self._types_from_graphs(graphs, subject)
        relationship_kind = self._first_matching_type(
            types,
            [
                "rc:ForeignKey",
                "rc:SharedIdentifier",
                "rc:Derivation",
                "rc:Aggregation",
                "rc:Relationship",
            ],
        )
        if relationship_kind == self.expand_iri("rc:ForeignKey"):
            from_column = self._first_object(graphs, subject, "rc:foreignKeyFrom")
            to_column = self._first_object(graphs, subject, "rc:foreignKeyTo")
            if from_column is None or to_column is None:
                return None
            detail = (
                "Foreign key from "
                f"{self._compact_resource_label(graphs, from_column)} to "
                f"{self._compact_resource_label(graphs, to_column)}"
            )
            integrity = self._first_object(graphs, subject, "rc:referentialIntegrity")
            if integrity is not None:
                detail += (
                    "; referential integrity: "
                    f"{self._compact_resource_label(graphs, integrity)}"
                )
            declared = self._bool_object(graphs, subject, "rc:declared")
            if declared is not None:
                detail += f"; declared: {str(declared).lower()}"
            return detail
        if relationship_kind == self.expand_iri("rc:SharedIdentifier"):
            columns = [
                self._compact_resource_label(graphs, column)
                for column in self._objects(graphs, subject, "rc:identifyingColumn")
            ]
            if not columns:
                return None
            return "Shared identifier across " + ", ".join(columns)
        if relationship_kind == self.expand_iri("rc:Derivation"):
            source_columns = [
                self._compact_resource_label(graphs, column)
                for column in self._objects(graphs, subject, "rc:sourceColumn")
            ]
            derived_columns = [
                self._compact_resource_label(graphs, column)
                for column in self._objects(graphs, subject, "rc:derivedColumn")
            ]
            if not source_columns or not derived_columns:
                return None
            detail = (
                "Derivation from "
                f"{', '.join(source_columns)} to {', '.join(derived_columns)}"
            )
            function_iri = self._first_object(graphs, subject, "rc:derivationFunction")
            if function_iri is not None:
                function_label = self._compact_resource_label(graphs, function_iri)
                detail += f"; function: {function_label}"
            return detail
        return None
    @staticmethod
    def _is_relationship_column_ref_name(name: str) -> bool:
        if name in {
            "from_column",
            "to_column",
            "identifying_columns",
            "source_columns",
            "derived_columns",
            "group_by_columns",
        }:
            return True
        return re.fullmatch(
            r"aggregated_columns\[\d+\]\."
            r"(?:target_column|source_columns|within_group_ordering)",
            name,
        ) is not None
