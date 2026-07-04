"""Staged revision creation.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via StagingMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class StagingMixin:
    def _applied_staged_revision_source_summary(
        self,
        staged_revision_iri: str,
    ) -> AppliedStagedRevisionSourceSummary:
        source = self.describe_staged_revision(staged_revision_iri)
        return AppliedStagedRevisionSourceSummary(
            iri=source.iri,
            summary=source.summary,
            revision_type=source.revision_type,
            revision_type_label=source.revision_type_label,
            revision_stance=source.revision_stance,
            revision_stance_label=source.revision_stance_label,
            review_note=source.review_note,
            review_recommendation=source.review_recommendation,
            alternative_to=(
                source.alternative_to.iri
                if source.alternative_to is not None
                else None
            ),
            restaged_from=(
                source.restaged_from.iri
                if source.restaged_from is not None
                else None
            ),
            restaged_by=(
                source.restaged_by.iri if source.restaged_by is not None else None
            ),
            current_restaged_by=(
                source.current_restaged_by.iri
                if source.current_restaged_by is not None
                else None
            ),
            restage_reason=source.restage_reason,
            created_at=source.created_at,
            created_by=source.created_by,
            validation_scope=source.validation_scope,
            validation_conforms=source.validation_conforms,
            validation_result_count=source.validation_result_count,
            changed_graphs=source.changed_graphs,
            included_graphs=source.included_graphs,
            graph_snapshots=source.graph_snapshots,
            patch_count=len(source.patches),
            patches=[
                AppliedStagedRevisionSourcePatchSummary(
                    operation=patch.operation,
                    operation_label=patch.operation_label,
                    target_graph=patch.target_graph,
                    count_basis=patch.count_basis,
                    patch_role=patch.patch_role,
                    patch_role_label=patch.patch_role_label,
                    sequence_index=patch.sequence_index,
                    triple_count=patch.triple_count,
                    before_triple_count=patch.before_triple_count,
                    after_triple_count=patch.after_triple_count,
                )
                for patch in source.patches
            ],
            supporting_observation_count=len(source.supporting_observations),
            supporting_claim_count=len(source.supporting_claims),
            supporting_pattern_count=len(source.supporting_patterns),
            evidence_count=len(source.evidence),
            revision_anchor_count=len(source.revision_anchors),
        )
    @staticmethod
    def _resource_lineage_current_staged_iri(
        selected: ResourceRevisionListItem,
        by_iri: dict[str, ResourceRevisionListItem],
    ) -> str | None:
        if selected.revision.is_current_staged_work:
            return selected.revision.iri
        successor_iri = selected.revision.current_restaged_by
        if successor_iri is None:
            return None
        successor = by_iri.get(successor_iri)
        if successor is not None and successor.revision.is_current_staged_work:
            return successor_iri
        return None
    def _cached_staged_revision(
        self,
        iri: str,
        *,
        graph: str | None,
        cache: dict[str, StagedGraphRevisionDescription | None],
    ) -> StagedGraphRevisionDescription | None:
        if iri not in cache:
            try:
                cache[iri] = self.describe_staged_revision(iri, graph=graph)
            except DoxaBaseError:
                cache[iri] = None
        return cache[iri]
    def _staged_revision_alternative_gate(
        self,
        alternative_to: str | None,
        *,
        revision_iri: str | None = None,
        graphs: list[str] | None = None,
    ) -> StagedRevisionAlternativeGate:
        if alternative_to is None:
            return StagedRevisionAlternativeGate(
                status="not_applicable",
                alternative_to=None,
                current_alternative_to=None,
                applied_source_iri=None,
                applied_revision_iri=None,
                semantic_review_required=False,
                note="This staged revision is not marked as an alternative.",
            )
        lookup_graphs = graphs or self._expand_graphs(["history"])
        current_alternative_to = (
            self._current_alternative_to_iri(alternative_to, graphs=lookup_graphs)
            or alternative_to
        )
        applied_revision_iri = self._first_subject(
            lookup_graphs,
            "rc:appliesStagedRevision",
            current_alternative_to,
        )
        if applied_revision_iri is not None:
            return StagedRevisionAlternativeGate(
                status="alternative_to_applied_source",
                alternative_to=alternative_to,
                current_alternative_to=current_alternative_to,
                applied_source_iri=current_alternative_to,
                applied_revision_iri=applied_revision_iri,
                semantic_review_required=True,
                note=(
                    "The current alternative target has already been applied. "
                    "Mechanical readiness is not approval to make both alternatives "
                    "durable; inspect the applied source before applying this row."
                ),
            )
        applied_set_member = self._applied_alternative_set_member(
            revision_iri,
            current_alternative_to=current_alternative_to,
            graphs=lookup_graphs,
        )
        if applied_set_member is not None:
            applied_source_iri, applied_revision_iri = applied_set_member
            return StagedRevisionAlternativeGate(
                status="alternative_set_member_applied",
                alternative_to=alternative_to,
                current_alternative_to=current_alternative_to,
                applied_source_iri=applied_source_iri,
                applied_revision_iri=applied_revision_iri,
                semantic_review_required=True,
                note=(
                    "A sibling member of this alternative set has already been "
                    "applied. Mechanical readiness is not approval to make both "
                    "alternatives durable; inspect the applied set member before "
                    "applying this row."
                ),
            )
        return StagedRevisionAlternativeGate(
            status="alternative_to_unapplied_source",
            alternative_to=alternative_to,
            current_alternative_to=current_alternative_to,
            applied_source_iri=None,
            applied_revision_iri=None,
            semantic_review_required=False,
            note=(
                "This staged revision is an alternative; compare related "
                "alternatives before applying one framing."
            ),
        )
    def _applied_alternative_set_member(
        self,
        revision_iri: str | None,
        *,
        current_alternative_to: str,
        graphs: list[str],
    ) -> tuple[str, str] | None:
        if revision_iri is None:
            return None
        membership = self._staged_revision_alternative_set_membership(
            revision_iri,
            graphs=graphs,
        )
        if membership is None:
            return None
        member_iris, _, _ = membership
        for member_iri in member_iris:
            if member_iri == revision_iri:
                continue
            candidate_source_iri = (
                self._current_restage_successor_iri(member_iri, graphs=graphs)
                or member_iri
            )
            if candidate_source_iri in {revision_iri, current_alternative_to}:
                continue
            applied_revision_iri = self._applied_event_for_staged_revision(
                candidate_source_iri,
                graphs=graphs,
            )
            if applied_revision_iri is not None:
                return candidate_source_iri, applied_revision_iri
        return None
    def _staged_revision_alternative_set_membership(
        self,
        revision_iri: str,
        *,
        graphs: list[str],
    ) -> tuple[list[str], str, str] | None:
        staged_revision_type = self.expand_iri("rc:StagedRevision")
        row_iris = [
            iri
            for iri in self._subjects(
                graphs,
                str(RDF.type),
                self.expand_iri("rc:GraphRevision"),
            )
            if (
                self._first_object(graphs, iri, "rc:revisionType")
                == staged_revision_type
            )
            and self._objects(graphs, iri, "rc:hasGraphPatch")
        ]
        rows: list[tuple[str, str | None, str | None]] = []
        for row_iri in row_iris:
            row_alternative_to = self._first_object(
                graphs,
                row_iri,
                "rc:alternativeTo",
            )
            rows.append(
                (
                    row_iri,
                    row_alternative_to,
                    (
                        self._current_alternative_to_iri(
                            row_alternative_to,
                            graphs=graphs,
                        )
                        if row_alternative_to is not None
                        else None
                    ),
                )
            )
        return self._alternative_set_membership_by_iri(rows).get(revision_iri)
    @staticmethod
    def _staged_validation_status(
        *,
        conforms: bool | None,
        result_count: int | None,
    ) -> str:
        if conforms is True:
            return "conforms"
        if conforms is False:
            return "failed"
        if result_count is not None and result_count > 0:
            return "failed"
        return "not_recorded"
    @staticmethod
    def _not_current_staged_work_reason(
        *,
        record_kind: str,
        applied_by: str | None,
        current_restaged_by: str | None,
        review_resolution: StagedRevisionReviewResolutionSummary | None = None,
    ) -> str:
        if record_kind == "staged_patch":
            if applied_by is not None:
                return "already_applied_source"
            if current_restaged_by is not None:
                return "superseded_by_restage"
            if review_resolution is not None:
                return "review_resolved"
            return "not_current_staged_patch"
        if record_kind == "applied_event":
            return "applied_event_record"
        return record_kind
    def _staged_review_resolution_for_staged_iri(
        self,
        staged_revision_iri: str,
        *,
        graphs: list[str] | None = None,
    ) -> StagedRevisionReviewResolutionSummary | None:
        summaries = self._staged_review_resolution_summaries_for_staged_iri(
            staged_revision_iri,
            graphs=graphs,
        )
        return summaries[0] if summaries else None
    def _staged_review_resolution_summaries_for_staged_iri(
        self,
        staged_revision_iri: str,
        *,
        graphs: list[str] | None = None,
    ) -> list[StagedRevisionReviewResolutionSummary]:
        staged_revision_value = self.expand_iri(staged_revision_iri)
        data_graphs = graphs or self._expand_graphs(["history"])
        decision_by_iri = {
            self.expand_iri(value): key
            for key, value in STAGED_REVIEW_DECISIONS.items()
        }
        summaries: list[StagedRevisionReviewResolutionSummary] = []
        for resolution_iri in self._subjects(
            data_graphs,
            "rc:resolvesStagedRevision",
            staged_revision_value,
        ):
            decision_iri = self._first_object(
                data_graphs,
                resolution_iri,
                "rc:stagedRevisionReviewDecision",
            )
            summaries.append(
                StagedRevisionReviewResolutionSummary(
                    resolution_revision_iri=resolution_iri,
                    decision=(
                        decision_by_iri.get(decision_iri)
                        if decision_iri is not None
                        else None
                    )
                    or "unknown",
                    decision_iri=decision_iri,
                    decision_label=self._label_for_resource(decision_iri),
                    summary=self._first_object(
                        data_graphs,
                        resolution_iri,
                        "rc:summary",
                    ),
                    rationale=self._first_object(
                        data_graphs,
                        resolution_iri,
                        "rc:revisionRationale",
                    ),
                    created_at=self._first_object(
                        data_graphs,
                        resolution_iri,
                        "rc:createdAt",
                    ),
                    created_by=self._first_object(
                        data_graphs,
                        resolution_iri,
                        "rc:createdBy",
                    ),
                )
            )
        summaries.sort(
            key=lambda item: (
                item.created_at or "",
                item.resolution_revision_iri,
            ),
            reverse=True,
        )
        return summaries
    def _staged_revision_apply_summary(
        self,
        staged: StagedGraphRevisionDescription,
    ) -> StagedRevisionApplySummary:
        try:
            check = self._preview_staged_revision_application(
                staged.iri,
                staged=staged,
            ).check
        except DoxaBaseError as exc:
            return StagedRevisionApplySummary(
                staged_revision_iri=staged.iri,
                status="not_available",
                decision="inspect_staged_revision",
                routing_decision="inspect_staged_revision",
                can_apply=None,
                summary=None,
                review_recommended=None,
                semantic_risk_level=None,
                semantic_risk_reasons=[],
                blocking_reasons=[],
                recommended_resolution=None,
                already_applied_by=None,
                restaged_by=(
                    staged.restaged_by.iri if staged.restaged_by is not None else None
                ),
                current_restaged_by=(
                    staged.current_restaged_by.iri
                    if staged.current_restaged_by is not None
                    else None
                ),
                stale_resolution_state=None,
                alternative_gate=staged.alternative_gate,
                changed_graphs=staged.changed_graphs,
                validation_scope=staged.validation_scope,
                validation_conforms=None,
                validation_skipped_reason=None,
                validation_result_count=None,
                patches_checked=None,
                triples_to_add=None,
                triples_to_remove=None,
                effective_delta_summary=None,
                count_drifts=[],
                snapshot_drifts=[],
                next_action=None,
                suggested_next_actions=[],
                error=str(exc),
            )
        return StagedRevisionApplySummary(
            staged_revision_iri=check.staged_revision_iri,
            status=check.status,
            decision=check.decision,
            routing_decision=check.routing_decision,
            can_apply=check.can_apply,
            summary=check.summary,
            review_recommended=check.review_recommended,
            semantic_risk_level=check.semantic_risk_level,
            semantic_risk_reasons=check.semantic_risk_reasons,
            blocking_reasons=check.blocking_reasons,
            recommended_resolution=check.recommended_resolution,
            already_applied_by=check.already_applied_by,
            restaged_by=check.restaged_by,
            current_restaged_by=check.current_restaged_by,
            stale_resolution_state=check.stale_resolution_state,
            alternative_gate=check.alternative_gate,
            changed_graphs=check.changed_graphs,
            validation_scope=check.validation_scope,
            validation_conforms=check.validation_conforms,
            validation_skipped_reason=check.validation_skipped_reason,
            validation_result_count=check.validation_result_count,
            patches_checked=check.patches_checked,
            triples_to_add=check.triples_to_add,
            triples_to_remove=check.triples_to_remove,
            effective_delta_summary=check.effective_delta_summary,
            count_drifts=check.count_drifts,
            snapshot_drifts=self._summary_snapshot_drifts(check.snapshot_drifts),
            next_action=check.next_action,
            suggested_next_actions=check.suggested_next_actions,
            error=None,
        )
    def search_staged_patch_payloads(
        self,
        query: str,
        *,
        graph: str | None = "history",
        current_staged_work_only: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> StagedPatchPayloadSearchResults:
        if not query.strip():
            raise DoxaBaseError("Search query must not be empty")
        if limit < 1:
            raise DoxaBaseError("Search limit must be at least 1")
        if offset < 0:
            raise DoxaBaseError("Search offset must be non-negative")

        search_tokens = _search_tokens(query)
        fts_query = _fts_query_from_tokens(search_tokens)
        graphs = self._expand_graphs([graph] if graph else None)
        graph_filter, graph_params = self._graph_filter(graphs)
        patch_content_predicate = self.expand_iri("rc:patchContent")
        rows = self._conn.execute(
            f"""
            SELECT
                graph,
                subject,
                predicate,
                text,
                snippet(literal_search, 4, '[', ']', ' ... ', 18) AS snippet
            FROM literal_search
            WHERE literal_search MATCH ?
              AND predicate = ?
              {graph_filter}
            ORDER BY bm25(literal_search), graph, subject
            """,
            [fts_query, patch_content_predicate, *graph_params],
        ).fetchall()
        revision_items = self.list_graph_revisions(
            graph=graph,
            include_apply_checks=True,
            current_staged_work_only=False,
            limit=1_000_000,
        )
        revision_by_iri = {item.iri: item for item in revision_items.revisions}
        staged_cache: dict[str, StagedGraphRevisionDescription | None] = {}
        matches: list[StagedPatchPayloadSearchMatch] = []
        for row in rows:
            patch_iri = row["subject"]
            revision_iri = self._first_subject(
                graphs,
                "rc:hasGraphPatch",
                patch_iri,
            )
            if revision_iri is None:
                continue
            revision_item = revision_by_iri.get(revision_iri)
            if (
                current_staged_work_only
                and revision_item is not None
                and not revision_item.is_current_staged_work
            ):
                continue
            staged = self._cached_staged_revision(
                revision_iri,
                graph=graph,
                cache=staged_cache,
            )
            if staged is None:
                continue
            patch = next(
                (candidate for candidate in staged.patches if candidate.iri == patch_iri),
                None,
            )
            if patch is None:
                continue
            matches.append(
                self._staged_patch_payload_search_match(
                    row=row,
                    staged=staged,
                    patch=patch,
                    revision_item=revision_item,
                    search_tokens=search_tokens,
                )
            )

        sliced = matches[offset : offset + limit]
        suggested_next_actions: list[SuggestedNextAction] = []
        seen_action_keys: set[tuple[str, str]] = set()
        for match in sliced:
            for action in match.suggested_next_actions:
                action_key = (
                    action.tool,
                    json.dumps(to_jsonable(action.args), sort_keys=True),
                )
                if action_key in seen_action_keys:
                    continue
                seen_action_keys.add(action_key)
                suggested_next_actions.append(action)
        return StagedPatchPayloadSearchResults(
            query=query,
            graph=graph,
            current_staged_work_only=current_staged_work_only,
            matches=sliced,
            count=len(matches),
            returned_count=len(sliced),
            total_count=len(matches),
            limit=limit,
            offset=offset,
            suggested_next_actions=suggested_next_actions,
        )
    def _staged_patch_payload_search_match(
        self,
        *,
        row: sqlite3.Row,
        staged: StagedGraphRevisionDescription,
        patch: StagedGraphPatchDescription,
        revision_item: GraphRevisionListItem | None,
        search_tokens: list[str],
    ) -> StagedPatchPayloadSearchMatch:
        (
            matched_roles,
            patch_subject_iris,
            parsed_resource_iris,
            parse_error,
        ) = self._staged_patch_payload_parsed_terms(
            patch,
            search_tokens=search_tokens,
        )
        actions = [
            SuggestedNextAction(
                tool="doxabase.describe_staged_revision",
                args={
                    "iri": staged.iri,
                    "include_current_apply_check": True,
                },
                reason="Inspect the staged revision that owns this matching "
                    "patch payload before treating the hit as live graph fact.",
            ),
            SuggestedNextAction(
                tool="doxabase.export_staged_revisions",
                args={
                    "revision_iris": [staged.iri],
                    "path": self._staged_patch_payload_search_export_path(
                        staged.iri
                    ),
                    "fail_on_sensitive": True,
                },
                reason="Export the owning staged revision as a review artifact "
                    "with full Turtle payload and current apply routing. The "
                    "suggested call blocks if scanner-matching content appears "
                    "before export.",
            ),
        ]
        if patch_subject_iris:
            actions.append(
                SuggestedNextAction(
                    tool="doxabase.list_resource_revisions",
                    args={
                        "resource_iri": patch_subject_iris[0],
                        "current_staged_work_only": True,
                        "include_patch_mentions": True,
                    },
                    reason="Use resource-centric patch mention discovery for the "
                        "first proposed subject in this staged payload.",
                )
            )
        return StagedPatchPayloadSearchMatch(
            revision_iri=staged.iri,
            revision_summary=staged.summary,
            revision_application_status=(
                revision_item.application_status
                if revision_item is not None
                else None
            ),
            revision_is_current_staged_work=(
                revision_item.is_current_staged_work
                if revision_item is not None
                else None
            ),
            patch_iri=patch.iri,
            graph=row["graph"],
            target_graph=patch.target_graph,
            operation=patch.operation,
            operation_label=patch.operation_label,
            patch_role=patch.patch_role,
            patch_role_label=patch.patch_role_label,
            sequence_index=patch.sequence_index,
            triple_count=patch.triple_count,
            text=row["text"],
            snippet=row["snippet"],
            matched_term_roles=matched_roles,
            patch_subject_iris=patch_subject_iris,
            parsed_resource_iris=parsed_resource_iris,
            parsed_resource_count=len(parsed_resource_iris),
            parse_error=parse_error,
            suggested_next_actions=actions,
        )
    def _staged_patch_payload_parsed_terms(
        self,
        patch: StagedGraphPatchDescription,
        *,
        search_tokens: list[str],
    ) -> tuple[list[str], list[str], list[str], str | None]:
        try:
            graph = self._parse_staged_patch_description(patch)
        except DoxaBaseError as exc:
            return [], [], [], str(exc)

        matched_roles: set[str] = set()
        subject_iris: set[str] = set()
        resource_iris: set[str] = set()

        def matches_token(value: str) -> bool:
            lowered = value.lower()
            return any(token in lowered for token in search_tokens)

        for subject, predicate, object_node in graph:
            if isinstance(subject, URIRef):
                subject_text = str(subject)
                subject_iris.add(subject_text)
                resource_iris.add(subject_text)
                if matches_token(subject_text):
                    matched_roles.add("subject")
            predicate_text = str(predicate)
            resource_iris.add(predicate_text)
            if matches_token(predicate_text):
                matched_roles.add("predicate")
            if isinstance(object_node, URIRef):
                object_text = str(object_node)
                resource_iris.add(object_text)
                if matches_token(object_text):
                    matched_roles.add("object")
            elif isinstance(object_node, Literal) and matches_token(str(object_node)):
                matched_roles.add("literal")

        role_order = ["subject", "predicate", "object", "literal"]
        return (
            [role for role in role_order if role in matched_roles],
            sorted(subject_iris),
            sorted(resource_iris),
            None,
        )
    def _staged_patch_payload_search_export_path(self, revision_iri: str) -> str:
        local = self._local_name(revision_iri) or "revision"
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", local).strip("-") or "revision"
        return f"/tmp/staged-payload-search-{safe}.md"
    def _search_no_match_staged_payload_action(
        self,
        *,
        query: str,
        limit: int,
    ) -> SuggestedNextAction:
        arguments = {
            "query": query,
            "scope": "staged_patches",
            "graph": "history",
            "current_staged_work_only": True,
            "limit": limit,
            "offset": 0,
        }
        return SuggestedNextAction(
                   tool="doxabase.search",
                   args=arguments,
                   reason="The term may exist only inside a current staged proposal. "
                "Search patch payloads before treating proposed ontology, shape, "
                "or map resources as absent.",
               )
    def _current_staged_query_repair_patch_rows(
        self,
        dataset: DatasetDescription,
    ) -> list[dict[str, str]]:
        anchor_iris = self._dataset_query_repair_anchor_iris(dataset.iri, dataset)
        query_repair_predicates = {
            self.expand_iri(predicate) for predicate in QUERY_REPAIR_PREDICATE_CURIES
        }
        history_graphs = self._expand_graphs(["history"])
        addition_operation = self.expand_iri("rc:AdditionPatch")
        removal_operation = self.expand_iri("rc:RemovalPatch")
        rows: list[dict[str, str]] = []
        for revision_iri in self._subjects(
            history_graphs,
            str(RDF.type),
            self.expand_iri("rc:GraphRevision"),
        ):
            if self._first_subject(
                history_graphs,
                "rc:appliesStagedRevision",
                revision_iri,
            ) is not None:
                continue
            if (
                self._current_restage_successor_iri(
                    revision_iri,
                    graphs=history_graphs,
                )
                is not None
            ):
                continue
            revision_anchors = set(
                self._objects(history_graphs, revision_iri, "rc:revisionAnchor")
            )
            if not (anchor_iris & revision_anchors):
                continue
            try:
                staged = self.describe_staged_revision(revision_iri)
            except DoxaBaseError:
                continue
            for patch in staged.patches:
                if patch.target_graph != "map":
                    continue
                if patch.operation == addition_operation:
                    operation = "add"
                elif patch.operation == removal_operation:
                    operation = "remove"
                else:
                    continue
                try:
                    patch_graph = self._parse_staged_patch_description(patch)
                except DoxaBaseError:
                    continue
                for row in self._rdf_graph_storage_rows(patch_graph):
                    if row[2] not in query_repair_predicates:
                        continue
                    rows.append(
                        {
                            "revision_iri": revision_iri,
                            "operation": operation,
                            "subject": row[0],
                            "predicate": row[2],
                            "object": row[3],
                            "object_kind": row[4],
                        }
                    )
        return rows
    def stage_query_physical_layout_repair(
        self,
        dataset_iri: str,
        layout_iri: str,
        *,
        file_format: str,
        rationale: str,
        label: str | None = None,
        description: str | None = None,
        compression_codec: str | None = None,
        layout_verification_status: str | None = None,
        layout_verification_note: str | None = None,
        allow_existing_physical_layouts: bool = False,
        summary: str | None = None,
        review_note: str | None = None,
        review_recommendation: str | None = None,
        profile_route_sources: Iterable[Mapping[str, Any]] | None = None,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ] = "all",
    ) -> StagedGraphRevisionRecord:
        dataset_value = self._required_iri("dataset_iri", dataset_iri)
        layout_value = self._required_iri("layout_iri", layout_iri)
        if not allow_existing_physical_layouts:
            dataset = self.describe_dataset(dataset_value)
            if dataset.physical_layouts:
                existing = ", ".join(
                    layout.iri for layout in dataset.physical_layouts[:3]
                )
                raise DoxaBaseError(
                    "stage_query_physical_layout_repair is intended for "
                    "missing_physical_layout repair groups; dataset already "
                    f"has physical layout(s): {existing}. Pass "
                    "allow_existing_physical_layouts=True only after reviewing "
                    "that an additional layout will not create ambiguous query "
                    "targets."
                )
        rationale_value = rationale.strip()
        if not rationale_value:
            raise DoxaBaseError("rationale must not be empty")
        file_format_ref = self._resource_ref("file_format", file_format)
        compression_codec_ref = (
            self._resource_ref("compression_codec", compression_codec)
            if compression_codec is not None
            else None
        )
        layout_verification_status_ref = (
            self._controlled_resource_ref(
                "layout_verification_status",
                layout_verification_status,
                LAYOUT_VERIFICATION_STATUSES,
            )
            if layout_verification_status is not None
            else None
        )
        profile_route_source_values = self._explicit_profile_route_sources(
            profile_route_sources or []
        )
        if profile_route_sources is not None and not profile_route_source_values:
            raise DoxaBaseError(
                "profile_route_sources was provided, but no usable profile "
                "route source entries were found"
            )

        graph_payload = self._query_physical_layout_repair_graph(
            dataset_iri=dataset_value,
            layout_iri=layout_value,
            label=label,
            description=description,
            file_format=file_format_ref,
            compression_codec=compression_codec_ref,
            layout_verification_status=layout_verification_status_ref,
            layout_verification_note=layout_verification_note,
        )
        additions = [
            {
                "graph": "map",
                "format": "turtle",
                "content": graph_payload.serialize(format="turtle"),
            }
        ]
        dataset_label = self._local_name(dataset_value) or dataset_value
        summary_value = (
            summary.strip()
            if summary is not None and summary.strip()
            else f"Stage physical layout repair for {dataset_label}"
        )
        review_note_value = (
            review_note
            if review_note is not None
            else (
                "Generated by stage_query_physical_layout_repair from reviewed "
                "query-planning repair inputs. The helper staged the physical "
                "layout resource and dataset link together instead of writing "
                "current-best map facts directly."
            )
        )
        review_recommendation_value = (
            review_recommendation
            if review_recommendation is not None
            else (
                "Apply only after confirming the layout IRI, file format, and "
                "verification status describe the source data needed for query "
                "planning."
            )
        )
        staged = self.stage_graph_revision(
            summary=summary_value,
            rationale=rationale_value,
            additions=additions,
            revision_anchors=[dataset_value, layout_value],
            included_graphs=["map"],
            review_note=review_note_value,
            review_recommendation=review_recommendation_value,
            validation_scope=validation_scope,
        )
        self._record_profile_insight_route_sources(
            staged.revision_iri,
            profile_route_source_values,
        )
        return staged
    def stage_query_storage_access_repair(
        self,
        dataset_iri: str,
        storage_access_iri: str,
        *,
        storage_protocol: str,
        storage_root: str,
        rationale: str,
        label: str | None = None,
        description: str | None = None,
        route_roles: Iterable[str] | str | None = None,
        access_mode: str | None = None,
        location_kind: str | None = None,
        endpoint_profile: str | None = None,
        bucket_name: str | None = None,
        key_prefix: str | None = None,
        region: str | None = None,
        path_style_access: bool | None = None,
        credential_reference: str | None = None,
        path_templates: Iterable[str] | str | None = None,
        layout_verification_status: str | None = None,
        layout_verification_note: str | None = None,
        allow_existing_storage_accesses: bool = False,
        summary: str | None = None,
        review_note: str | None = None,
        review_recommendation: str | None = None,
        profile_route_sources: Iterable[Mapping[str, Any]] | None = None,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ] = "all",
    ) -> StagedGraphRevisionRecord:
        dataset_value = self._required_iri("dataset_iri", dataset_iri)
        access_value = self._required_iri("storage_access_iri", storage_access_iri)
        if not allow_existing_storage_accesses:
            dataset = self.describe_dataset(dataset_value)
            if dataset.storage_accesses:
                existing = ", ".join(
                    access.iri for access in dataset.storage_accesses[:3]
                )
                raise DoxaBaseError(
                    "stage_query_storage_access_repair is intended for "
                    "missing_storage_access repair groups; dataset already "
                    f"has storage access resource(s): {existing}. Pass "
                    "allow_existing_storage_accesses=True only after reviewing "
                    "that an additional storage route will not create duplicate "
                    "query target candidates."
                )
        storage_root_value = storage_root.strip()
        if not storage_root_value:
            raise DoxaBaseError("storage_root must not be empty")
        rationale_value = rationale.strip()
        if not rationale_value:
            raise DoxaBaseError("rationale must not be empty")
        route_role_values = self._string_values("route_roles", route_roles)
        path_template_values = self._string_values("path_templates", path_templates)
        location_kind_value = self._storage_location_kind(location_kind)
        storage_protocol_ref = self._resource_ref(
            "storage_protocol",
            storage_protocol,
        )
        access_mode_ref = (
            self._resource_ref("access_mode", access_mode)
            if access_mode is not None
            else None
        )
        layout_verification_status_ref = (
            self._controlled_resource_ref(
                "layout_verification_status",
                layout_verification_status,
                LAYOUT_VERIFICATION_STATUSES,
            )
            if layout_verification_status is not None
            else None
        )
        profile_route_source_values = self._explicit_profile_route_sources(
            profile_route_sources or []
        )
        if profile_route_sources is not None and not profile_route_source_values:
            raise DoxaBaseError(
                "profile_route_sources was provided, but no usable profile "
                "route source entries were found"
            )

        graph_payload = self._query_storage_access_repair_graph(
            dataset_iri=dataset_value,
            storage_access_iri=access_value,
            label=label,
            description=description,
            route_roles=route_role_values,
            storage_protocol=storage_protocol_ref,
            access_mode=access_mode_ref,
            location_kind=location_kind_value,
            storage_root=storage_root_value,
            endpoint_profile=endpoint_profile,
            bucket_name=bucket_name,
            key_prefix=key_prefix,
            region=region,
            path_style_access=path_style_access,
            credential_reference=credential_reference,
            path_templates=path_template_values,
            layout_verification_status=layout_verification_status_ref,
            layout_verification_note=layout_verification_note,
        )
        additions = [
            {
                "graph": "map",
                "format": "turtle",
                "content": graph_payload.serialize(format="turtle"),
            }
        ]
        dataset_label = self._local_name(dataset_value) or dataset_value
        summary_value = (
            summary.strip()
            if summary is not None and summary.strip()
            else f"Stage storage access repair for {dataset_label}"
        )
        review_note_value = (
            review_note
            if review_note is not None
            else (
                "Generated by stage_query_storage_access_repair from reviewed "
                "query-planning repair inputs. The helper staged the storage "
                "access resource and dataset link together instead of writing "
                "current-best map facts directly."
            )
        )
        review_recommendation_value = (
            review_recommendation
            if review_recommendation is not None
            else (
                "Apply only after confirming the storage protocol, non-secret "
                "location, and path or relation templates describe the intended "
                "source data for query planning."
            )
        )
        staged = self.stage_graph_revision(
            summary=summary_value,
            rationale=rationale_value,
            additions=additions,
            revision_anchors=[dataset_value, access_value],
            included_graphs=["map"],
            review_note=review_note_value,
            review_recommendation=review_recommendation_value,
            validation_scope=validation_scope,
        )
        self._record_profile_insight_route_sources(
            staged.revision_iri,
            profile_route_source_values,
        )
        return staged
    def _pending_staged_storage_access_links(
        self,
        dataset_iri: str,
    ) -> dict[str, list[str]]:
        history_graphs = self._expand_graphs(["history"])
        dataset_ref = URIRef(self.expand_iri(dataset_iri))
        predicate_ref = URIRef(self.expand_iri("rc:hasStorageAccess"))
        addition_operation = self.expand_iri("rc:AdditionPatch")
        pending_by_storage: dict[str, list[str]] = {}
        for revision_iri in self._subjects(
            history_graphs,
            str(RDF.type),
            self.expand_iri("rc:GraphRevision"),
        ):
            patch_iris = self._objects(
                history_graphs,
                revision_iri,
                "rc:hasGraphPatch",
            )
            if not patch_iris:
                continue
            item_revision_type = self._first_object(
                history_graphs,
                revision_iri,
                "rc:revisionType",
            )
            applies_staged_revision = self._first_object(
                history_graphs,
                revision_iri,
                "rc:appliesStagedRevision",
            )
            if (
                self._graph_revision_record_kind(
                    item_revision_type,
                    has_patch_payload=True,
                    applies_staged_revision=applies_staged_revision,
                )
                != "staged_patch"
            ):
                continue
            if self._first_subject(
                history_graphs,
                "rc:appliesStagedRevision",
                revision_iri,
            ) is not None:
                continue
            if (
                self._current_restage_successor_iri(
                    revision_iri,
                    graphs=history_graphs,
                )
                is not None
            ):
                continue
            try:
                staged = self.describe_staged_revision(revision_iri)
            except DoxaBaseError:
                continue
            for patch in staged.patches:
                if patch.operation != addition_operation:
                    continue
                if patch.target_graph != "map":
                    continue
                try:
                    patch_graph = self._parse_staged_patch_description(patch)
                except DoxaBaseError:
                    continue
                for subject, predicate, object_node in patch_graph:
                    if subject != dataset_ref or predicate != predicate_ref:
                        continue
                    if not isinstance(object_node, URIRef):
                        continue
                    pending_by_storage.setdefault(str(object_node), []).append(
                        revision_iri
                    )
        return {
            storage_iri: list(dict.fromkeys(revision_iris))
            for storage_iri, revision_iris in pending_by_storage.items()
        }
    def _pending_staged_metric_promotion_iris(
        self,
        *,
        metric_iri: str,
        evidence_iri: str,
        promotion_pattern_iris: Iterable[str],
    ) -> list[str]:
        data_graphs = self._expand_graphs(["history"])
        metric_value = self.expand_iri(metric_iri)
        evidence_value = self.expand_iri(evidence_iri)
        promotion_pattern_values = {
            self.expand_iri(pattern_iri) for pattern_iri in promotion_pattern_iris
        }
        if not promotion_pattern_values:
            return []

        candidates: list[tuple[str, str]] = []
        for revision_iri in self._subjects(
            data_graphs,
            "rc:revisionAnchor",
            metric_value,
        ):
            if self._first_subject(
                data_graphs,
                "rc:appliesStagedRevision",
                revision_iri,
            ):
                continue
            if self._current_restage_successor_iri(revision_iri, graphs=data_graphs):
                continue
            if not self._objects(data_graphs, revision_iri, "rc:hasGraphPatch"):
                continue
            review_note = self._first_object(
                data_graphs,
                revision_iri,
                "rc:reviewNote",
            )
            if (
                PROFILE_METRIC_PROMOTION_REVIEW_NOTE_MARKER
                not in (review_note or "")
            ):
                continue
            if evidence_value not in self._objects(
                data_graphs,
                revision_iri,
                "rc:evidence",
            ):
                continue
            supporting_patterns = set(
                self._objects(
                    data_graphs,
                    revision_iri,
                    "rc:revisionSupportingPattern",
                )
            )
            if not promotion_pattern_values & supporting_patterns:
                continue
            created_at = (
                self._first_object(data_graphs, revision_iri, "rc:createdAt") or ""
            )
            candidates.append((created_at, revision_iri))
        return [
            revision_iri
            for _, revision_iri in sorted(
                candidates,
                key=lambda item: (item[0], item[1]),
                reverse=True,
            )
        ]
    def stage_graph_revision(
        self,
        summary: str,
        rationale: str,
        *,
        additions: Iterable[Mapping[str, str]] | None = None,
        removals: Iterable[Mapping[str, str]] | None = None,
        stance: str = "rc:CandidateRevision",
        revision_type: str = "rc:StagedRevision",
        included_graphs: Iterable[str] | str | None = None,
        revision_iri: str | None = None,
        created_at: datetime | str | None = None,
        created_by: str | None = None,
        supporting_observations: Iterable[str] | str | None = None,
        supporting_claims: Iterable[str] | str | None = None,
        supporting_patterns: Iterable[str] | str | None = None,
        revision_anchors: Iterable[str] | str | None = None,
        evidence: Iterable[str] | str | None = None,
        alternative_to: str | None = None,
        restages_revision: str | None = None,
        review_note: str | None = None,
        review_recommendation: str | None = None,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ] = "all",
        _ordered_patch_specs: list[dict[str, Any]] | None = None,
    ) -> StagedGraphRevisionRecord:
        parsed_patches = (
            list(_ordered_patch_specs)
            if _ordered_patch_specs is not None
            else self._parse_staged_patch_specs(
                additions=additions,
                removals=removals,
            )
        )
        if not parsed_patches:
            raise DoxaBaseError("stage_graph_revision requires at least one patch")

        stance_iri = self.expand_iri(stance)
        self._ensure_revision_stance(stance_iri)
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
        evidence_values = self._string_values("evidence", evidence)

        preview = self._preview_staged_graph_patches(
            parsed_patches,
            validation_scope=validation_scope,
            revision_has_support_metadata=bool(
                supporting_observation_values
                or supporting_claim_values
                or supporting_pattern_values
                or evidence_values
            ),
        )
        changed_graph_values = preview.changed_graphs
        patch_records = preview.patch_records
        patch_descriptions = preview.patch_descriptions
        validation = preview.validation
        revision_subject = (
            self._required_iri("revision_iri", revision_iri)
            if revision_iri is not None
            else self._mint_iri("staged-revision")
        )
        restages_revision_value = (
            self._validated_restage_successor_source(
                restages_revision,
                new_revision_iri=revision_subject,
            )
            if restages_revision is not None
            else None
        )
        effective_alternative_to = alternative_to
        if effective_alternative_to is None and restages_revision_value is not None:
            effective_alternative_to = self._first_object(
                self._expand_graphs(["history"]),
                restages_revision_value,
                "rc:alternativeTo",
            )
        graph_counts = {
            graph_name: self.triple_count(graph_name)
            for graph_name in changed_graph_values
        }
        revision_record = self.record_graph_revision(
            summary=summary,
            rationale=rationale,
            changed_graphs=changed_graph_values,
            revision_type=revision_type,
            included_graphs=included_graphs,
            revision_iri=revision_subject,
            created_at=created_at,
            created_by=created_by,
            supporting_observations=supporting_observation_values,
            supporting_claims=supporting_claim_values,
            supporting_patterns=supporting_pattern_values,
            revision_anchors=revision_anchors,
            evidence=evidence_values,
            graph_counts=graph_counts,
            validation_scope=validation.scope,
            validation_conforms=validation.conforms,
            validation_result_count=validation.result_count,
            validation_results=validation.results,
        )

        metadata = Graph()
        self._bind_prefixes(metadata)
        subject = URIRef(revision_subject)
        metadata.add(
            (
                subject,
                URIRef(self.expand_iri("rc:revisionStance")),
                URIRef(stance_iri),
            )
        )
        self._add_optional_literal(metadata, subject, "rc:reviewNote", review_note)
        self._add_optional_literal(
            metadata,
            subject,
            "rc:reviewRecommendation",
            review_recommendation,
        )
        if effective_alternative_to is not None:
            metadata.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:alternativeTo")),
                    URIRef(self.expand_iri(effective_alternative_to)),
                )
            )
        if restages_revision_value is not None:
            metadata.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:restagesRevision")),
                    URIRef(restages_revision_value),
                )
            )
        for patch, patch_record in zip(parsed_patches, patch_records, strict=True):
            patch_subject = URIRef(patch_record.patch_iri)
            metadata.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasGraphPatch")),
                    patch_subject,
                )
            )
            metadata.add(
                (
                    patch_subject,
                    RDF.type,
                    URIRef(self.expand_iri("rc:GraphPatch")),
                )
            )
            metadata.add(
                (
                    patch_subject,
                    URIRef(self.expand_iri("rc:patchOperation")),
                    URIRef(patch_record.operation),
                )
            )
            metadata.add(
                (
                    patch_subject,
                    URIRef(self.expand_iri("rc:targetGraph")),
                    Literal(patch_record.target_graph),
                )
            )
            metadata.add(
                (
                    patch_subject,
                    URIRef(self.expand_iri("rc:patchFormat")),
                    Literal(patch_record.format),
                )
            )
            metadata.add(
                (
                    patch_subject,
                    URIRef(self.expand_iri("rc:patchRole")),
                    URIRef(patch_record.patch_role),
                )
            )
            metadata.add(
                (
                    patch_subject,
                    URIRef(self.expand_iri("rc:patchSequence")),
                    Literal(patch_record.sequence_index, datatype=XSD.integer),
                )
            )
            metadata.add(
                (
                    patch_subject,
                    URIRef(self.expand_iri("rc:patchContent")),
                    Literal(str(patch["content"])),
                )
            )
            metadata.add(
                (
                    patch_subject,
                    URIRef(self.expand_iri("rc:patchTripleCount")),
                    Literal(patch_record.triple_count, datatype=XSD.integer),
                )
            )
            metadata.add(
                (
                    patch_subject,
                    URIRef(self.expand_iri("rc:beforeTripleCount")),
                    Literal(patch_record.before_triple_count, datatype=XSD.integer),
                )
            )
            metadata.add(
                (
                    patch_subject,
                    URIRef(self.expand_iri("rc:afterTripleCount")),
                    Literal(patch_record.after_triple_count, datatype=XSD.integer),
                )
            )

        extra_triples = self._insert_graph("history", metadata)
        staged_description = (
            self.describe_staged_revision(revision_subject)
            if restages_revision_value is not None
            else None
        )
        return StagedGraphRevisionRecord(
            revision_iri=revision_subject,
            revision_type=revision_record.revision_type,
            revision_stance=stance_iri,
            summary=summary,
            rationale=rationale,
            review_note=review_note,
            review_recommendation=review_recommendation,
            graph="history",
            triples=revision_record.triples + extra_triples,
            changed_graphs=changed_graph_values,
            patches=patch_records,
            validation_scope=validation.scope,
            validation_conforms=validation.conforms,
            validation_result_count=validation.result_count,
            validation_results=validation.results,
            alternative_to=(
                self.expand_iri(effective_alternative_to)
                if effective_alternative_to is not None
                else None
            ),
            restaged_from=restages_revision_value,
            restage_reason=(
                staged_description.restage_reason
                if staged_description is not None
                else None
            ),
            current_restaged_by=(
                staged_description.current_restaged_by.iri
                if staged_description is not None
                and staged_description.current_restaged_by is not None
                else None
            ),
        )
    def _staged_validation_same_slot_candidate_for_diagnostic(
        self,
        source: StagedGraphRevisionDescription,
        diagnostic: ValidationDiagnostic,
        *,
        replacement_label: str,
        validation_scope: str,
    ) -> StagedRevisionRebaseCandidate | None:
        assert diagnostic.focus_node is not None
        assert diagnostic.result_path is not None
        proposed_rows: list[GraphStorageRow] = []
        addition_operation = self.expand_iri("rc:AdditionPatch")
        for patch in source.patches:
            try:
                target_graph = self._required_staged_patch_target_graph(patch)
                operation = self._required_staged_patch_field(
                    patch,
                    "operation",
                    patch.operation,
                )
            except DoxaBaseError:
                return None
            if target_graph != "map" or operation != addition_operation:
                continue
            try:
                patch_graph = self._parse_staged_patch_description(patch)
            except DoxaBaseError:
                return None
            for row in self._rdf_graph_storage_rows(patch_graph):
                if (
                    row[0] == diagnostic.focus_node
                    and row[2] == diagnostic.result_path
                ):
                    proposed_rows.append(row)
        proposed_rows = self._sort_graph_storage_rows(set(proposed_rows))
        if len(proposed_rows) != 1:
            return None

        proposed_row = proposed_rows[0]
        object_value, object_kind, object_datatype, object_lang = (
            proposed_row[3],
            "iri" if proposed_row[4] == "uri" else proposed_row[4],
            proposed_row[5],
            proposed_row[6],
        )
        if not self._staged_same_slot_replacement_object_allowed(
            diagnostic.result_path,
            object_kind,
            object_datatype,
        ):
            return None
        current_triples = self._assertion_triples(
            ["map"],
            subject=diagnostic.focus_node,
            predicate=diagnostic.result_path,
            object_filter=None,
            limit=10,
        )
        if len(current_triples) != 1:
            return None
        current = current_triples[0]
        if (
            current.object == proposed_row[3]
            and current.object_kind == proposed_row[4]
            and current.object_datatype == proposed_row[5]
            and current.object_lang == proposed_row[6]
        ):
            return None
        rationale = (
            f"Repair staged revision {source.iri} by replacing the current "
            f"{replacement_label} value instead of adding a second value after "
            "validation failed."
        )
        arguments: dict[str, Any] = {
            "subject": diagnostic.focus_node,
            "predicate": diagnostic.result_path,
            "object": object_value,
            "rationale": rationale,
            "change_kind": "replace",
            "graph": "map",
            "object_kind": object_kind,
            "restages_revision": source.iri,
            "validation_scope": validation_scope,
        }
        if source.alternative_to is not None:
            arguments["alternative_to"] = source.alternative_to.iri
        if object_datatype is not None:
            arguments["object_datatype"] = object_datatype
        if object_lang is not None:
            arguments["object_lang"] = object_lang
        action = SuggestedNextAction(
                     tool="doxabase.stage_map_assertion_change",
                     args=arguments,
                     reason=f"Validation failed because {replacement_label} is "
                "single-valued and the current graph has a different value. "
                "Stage a reviewed replacement successor instead of replaying "
                "the same addition patch.",
                 )
        return StagedRevisionRebaseCandidate(
            candidate_kind="same_slot_replacement",
            candidate_status="ready_to_stage",
            graph="map",
            subject=diagnostic.focus_node,
            predicate=diagnostic.result_path,
            object=object_value,
            object_kind=object_kind,
            object_datatype=object_datatype,
            object_lang=object_lang,
            current_same_subject_predicate_triples=current_triples,
            proposed_triples=[self._graph_triple_description(proposed_row)],
            validation_results=[diagnostic],
            action=action,
            note=(
                "Recognized a validation-failed single-slot addition where the "
                "current graph has exactly one different value. Review the "
                "semantic alternative context before staging this repair."
            ),
        )
    @staticmethod
    def _staged_revision_exact_drift_summary(
        check: StagedRevisionApplyCheck,
    ) -> list[StagedRevisionExactDriftSummary]:
        count_drifts_by_graph: dict[str, list[StagedGraphCountDrift]] = {}
        for drift in check.count_drifts:
            count_drifts_by_graph.setdefault(drift.target_graph, []).append(drift)
        snapshot_drift_by_graph = {
            drift.graph_role: drift for drift in check.snapshot_drifts
        }
        graph_roles = list(
            dict.fromkeys(
                [
                    *count_drifts_by_graph.keys(),
                    *snapshot_drift_by_graph.keys(),
                ]
            )
        )
        summaries: list[StagedRevisionExactDriftSummary] = []
        for graph_role in graph_roles:
            count_drifts = count_drifts_by_graph.get(graph_role, [])
            snapshot_drift = snapshot_drift_by_graph.get(graph_role)
            patch_triple_status_counts: dict[str, int] = {}
            for drift in count_drifts:
                if drift.patch_triple_status is None:
                    continue
                patch_triple_status_counts[drift.patch_triple_status] = (
                    patch_triple_status_counts.get(drift.patch_triple_status, 0)
                    + 1
                )
            has_snapshot_digest_drift = (
                snapshot_drift is not None
                and snapshot_drift.snapshot_content_digest
                != snapshot_drift.current_content_digest
            )
            note_parts: list[str] = []
            if count_drifts:
                note_parts.append(
                    "Count drift summarizes patch-level count checks for this graph."
                )
            if snapshot_drift is not None:
                note_parts.append(
                    "Snapshot drift summarizes graph-level count/digest drift; "
                    "raw changed triples are intentionally omitted from this "
                    "compact recovery-lane field."
                )
            summaries.append(
                StagedRevisionExactDriftSummary(
                    graph_role=graph_role,
                    blocking_reasons=check.blocking_reasons,
                    has_count_drift=bool(count_drifts),
                    has_snapshot_digest_drift=has_snapshot_digest_drift,
                    count_drift_count=len(count_drifts),
                    count_drift_deltas=[
                        drift.delta for drift in count_drifts
                    ],
                    patch_triple_status_counts=patch_triple_status_counts,
                    snapshot_triple_count=(
                        snapshot_drift.snapshot_triple_count
                        if snapshot_drift is not None
                        else None
                    ),
                    current_triple_count=(
                        snapshot_drift.current_triple_count
                        if snapshot_drift is not None
                        else None
                    ),
                    triples_added_since_snapshot_count=(
                        snapshot_drift.triples_added_since_snapshot_count
                        if snapshot_drift is not None
                        else None
                    ),
                    triples_removed_since_snapshot_count=(
                        snapshot_drift.triples_removed_since_snapshot_count
                        if snapshot_drift is not None
                        else None
                    ),
                    exact_changed_triples_available=(
                        snapshot_drift.exact_changed_triples_available
                        if snapshot_drift is not None
                        else any(
                            drift.exact_changed_triples_available
                            for drift in count_drifts
                        )
                    ),
                    exact_changed_triples_included=False,
                    drift_relevance=(
                        snapshot_drift.drift_relevance
                        if snapshot_drift is not None
                        else None
                    ),
                    changed_resource_count=(
                        snapshot_drift.changed_resource_count
                        if snapshot_drift is not None
                        else None
                    ),
                    changed_resources_returned_count=(
                        snapshot_drift.changed_resources_returned_count
                        if snapshot_drift is not None
                        else 0
                    ),
                    changed_resources_omitted_count=(
                        snapshot_drift.changed_resources_omitted_count
                        if snapshot_drift is not None
                        else None
                    ),
                    changed_resources=(
                        snapshot_drift.changed_resources
                        if snapshot_drift is not None
                        else []
                    ),
                    changed_resource_suggested_next_actions=(
                        snapshot_drift.changed_resource_suggested_next_actions
                        if snapshot_drift is not None
                        else []
                    ),
                    note=" ".join(note_parts),
                )
            )
        return summaries
    @staticmethod
    def _staged_revision_patch_payload_signature(
        staged: StagedGraphRevisionDescription,
    ) -> list[
        tuple[int | None, str | None, str | None, str | None, str | None, str | None]
    ]:
        return [
            (
                patch.sequence_index,
                patch.operation,
                patch.target_graph,
                patch.patch_role,
                patch.format,
                patch.content,
            )
            for patch in staged.patches
        ]
    def _staged_revision_semantic_risk(
        self,
        staged: StagedGraphRevisionDescription,
    ) -> tuple[str, list[str]]:
        if staged.judgement_panel is None:
            reasons: list[str] = []
            review_note = staged.review_note or ""
            if "Why current value may be intentional:" in review_note:
                reasons.append(
                    "Stored review context explains why the current value may "
                    "be intentional."
                )
            if "Related route summaries:" in review_note:
                reasons.append(
                    "Stored review context includes related lore routes."
                )
            if (
                staged.supporting_observations
                or staged.supporting_claims
                or staged.supporting_patterns
                or staged.evidence
            ):
                reasons.append(
                    "The staged revision has linked observations, claims, "
                    "patterns, or evidence."
                )
            if any(impact.severity == "attention" for impact in staged.impacts):
                reasons.append(
                    "The staged revision has attention-level impact entries."
                )
            reasons = list(dict.fromkeys(reasons))
            if not reasons:
                return "none", []
            high_signal_count = sum(
                [
                    "Why current value may be intentional:" in review_note,
                    "Related route summaries:" in review_note,
                    bool(
                        staged.supporting_observations
                        or staged.supporting_claims
                        or staged.supporting_patterns
                        or staged.evidence
                    ),
                    any(impact.severity == "attention" for impact in staged.impacts),
                ]
            )
            level = "high" if high_signal_count >= 2 else "attention"
            return level, reasons
        return (
            staged.judgement_panel.semantic_risk_level,
            staged.judgement_panel.semantic_risk_reasons,
        )
    def _staged_revision_stored_review_context(
        self,
        staged: StagedGraphRevisionDescription,
    ) -> StagedRevisionStoredReviewContext | None:
        if staged.judgement_panel is not None:
            return None
        review_note = staged.review_note or ""
        signals = StagedRevisionStoredReviewNoteSignals(
            has_value_type_context="Value-type context:" in review_note,
            has_current_value_rationale=(
                "Why current value may be intentional:" in review_note
            ),
            has_caveat_context="Nearby caveats by scope:" in review_note,
            has_related_routes="Related route summaries:" in review_note,
            has_user_review_note="User/agent review note:" in review_note,
        )
        support_counts = StagedRevisionStoredReviewSupportCounts(
            observations=len(staged.supporting_observations),
            claims=len(staged.supporting_claims),
            patterns=len(staged.supporting_patterns),
            evidence=len(staged.evidence),
            revision_anchors=len(staged.revision_anchors),
        )
        attention_impacts = [
            impact for impact in staged.impacts if impact.severity == "attention"
        ]
        semantic_risk_level, semantic_risk_reasons = (
            self._staged_revision_semantic_risk(staged)
        )
        has_review_note_signal = any(
            [
                signals.has_value_type_context,
                signals.has_current_value_rationale,
                signals.has_caveat_context,
                signals.has_related_routes,
                signals.has_user_review_note,
            ]
        )
        has_linked_support = any(
            [
                support_counts.observations,
                support_counts.claims,
                support_counts.patterns,
                support_counts.evidence,
            ]
        )
        if (
            semantic_risk_level == "none"
            and not has_review_note_signal
            and not staged.review_recommendation
            and not has_linked_support
            and not attention_impacts
        ):
            return None
        source_fields: list[str] = []
        if staged.review_note:
            source_fields.append("review_note")
        if staged.review_recommendation:
            source_fields.append("review_recommendation")
        if staged.supporting_observations:
            source_fields.append("supporting_observations")
        if staged.supporting_claims:
            source_fields.append("supporting_claims")
        if staged.supporting_patterns:
            source_fields.append("supporting_patterns")
        if staged.evidence:
            source_fields.append("evidence")
        if staged.revision_anchors:
            source_fields.append("revision_anchors")
        if staged.impacts:
            source_fields.append("impacts")
        if staged.patches:
            source_fields.append("patches")
        return StagedRevisionStoredReviewContext(
            source_fields=source_fields,
            semantic_risk_level=semantic_risk_level,
            semantic_risk_reasons=semantic_risk_reasons,
            review_recommendation=staged.review_recommendation,
            review_note_signals=signals,
            linked_support_counts=support_counts,
            attention_impacts=attention_impacts,
        )
    def _staged_revision_snapshot_drifts(
        self,
        staged: StagedGraphRevisionDescription,
        changed_graphs: list[str],
    ) -> list[StagedGraphSnapshotDrift]:
        snapshot_by_graph = {
            snapshot.graph_role: snapshot for snapshot in staged.graph_snapshots
        }
        patch_terms_by_graph = self._staged_revision_patch_terms_by_graph(staged)
        drifts: list[StagedGraphSnapshotDrift] = []
        for graph_role in changed_graphs:
            snapshot = snapshot_by_graph.get(graph_role)
            if snapshot is None or snapshot.content_digest is None:
                continue
            current_digest = self._graph_content_digest(graph_role)
            if current_digest == snapshot.content_digest:
                continue
            diff = self._snapshot_triple_diff(staged.iri, graph_role)
            if diff is None:
                triples_added_since_snapshot: list[GraphTripleDescription] = []
                triples_removed_since_snapshot: list[GraphTripleDescription] = []
                exact_changed_triples_available = False
                changed_resource_count = None
                changed_resources_returned_count = 0
                changed_resources_omitted_count = None
                changed_resources: list[ChangedGraphResourceSummary] = []
                changed_resource_suggested_next_actions: list[SuggestedNextAction] = []
                note = (
                    "The graph content digest changed since this revision was "
                    "staged. DoxaBase can detect that the graph state is not "
                    "identical, but this revision has no stored snapshot rows for "
                    "exact changed-triple reporting."
                )
            else:
                triples_added_since_snapshot, triples_removed_since_snapshot = diff
                exact_changed_triples_available = True
                (
                    changed_resource_count,
                    changed_resources_returned_count,
                    changed_resources_omitted_count,
                    changed_resources,
                    changed_resource_suggested_next_actions,
                ) = self._changed_graph_resource_summary(
                    triples_added=triples_added_since_snapshot,
                    triples_removed=triples_removed_since_snapshot,
                    patch_terms=patch_terms_by_graph.get(graph_role),
                    source_revision_iri=staged.iri,
                )
                note = (
                    "The graph content digest changed since this revision was "
                    "staged. Exact triples added to and removed from the target "
                    "graph since the stored snapshot are included."
                )
            (
                drift_relevance,
                patch_overlap_subjects,
                patch_overlap_predicates,
                patch_overlap_objects,
                revision_anchor_overlap,
                relevance_note,
            ) = self._staged_snapshot_drift_relevance(
                exact_changed_triples_available=exact_changed_triples_available,
                triples_added_since_snapshot=triples_added_since_snapshot,
                triples_removed_since_snapshot=triples_removed_since_snapshot,
                patch_terms=patch_terms_by_graph.get(graph_role),
            )
            note = f"{note} {relevance_note}"
            drifts.append(
                StagedGraphSnapshotDrift(
                    graph_role=graph_role,
                    snapshot_triple_count=snapshot.triple_count,
                    current_triple_count=self.triple_count(graph_role),
                    snapshot_content_digest=snapshot.content_digest,
                    current_content_digest=current_digest,
                    exact_changed_triples_available=exact_changed_triples_available,
                    exact_changed_triples_included=(
                        exact_changed_triples_available
                    ),
                    triples_added_since_snapshot_count=(
                        len(triples_added_since_snapshot)
                        if exact_changed_triples_available
                        else None
                    ),
                    triples_removed_since_snapshot_count=(
                        len(triples_removed_since_snapshot)
                        if exact_changed_triples_available
                        else None
                    ),
                    drift_relevance=drift_relevance,
                    patch_overlap_subjects=patch_overlap_subjects,
                    patch_overlap_predicates=patch_overlap_predicates,
                    patch_overlap_objects=patch_overlap_objects,
                    revision_anchor_overlap=revision_anchor_overlap,
                    changed_resource_count=changed_resource_count,
                    changed_resources_returned_count=changed_resources_returned_count,
                    changed_resources_omitted_count=changed_resources_omitted_count,
                    changed_resources=changed_resources,
                    changed_resource_suggested_next_actions=(
                        changed_resource_suggested_next_actions
                    ),
                    triples_added_since_snapshot=triples_added_since_snapshot,
                    triples_removed_since_snapshot=triples_removed_since_snapshot,
                    note=note,
                )
            )
        return drifts
    def _staged_revision_patch_terms_by_graph(
        self,
        staged: StagedGraphRevisionDescription,
    ) -> dict[str, _StagedRevisionDriftTerms]:
        terms_by_graph: dict[str, _StagedRevisionDriftTerms] = {}
        revision_anchors = {anchor.iri for anchor in staged.revision_anchors}
        for patch in staged.patches:
            if patch.target_graph is None:
                continue
            try:
                target_graph = self._required_staged_patch_target_graph(patch)
                patch_graph = self._parse_staged_patch_description(patch)
            except DoxaBaseError:
                continue
            graph_terms = terms_by_graph.setdefault(
                target_graph,
                _StagedRevisionDriftTerms(
                    patch_subjects=set(),
                    patch_predicates=set(),
                    patch_objects=set(),
                    revision_anchors=set(revision_anchors),
                ),
            )
            for subject, predicate, object_node in patch_graph:
                graph_terms.patch_subjects.add(str(subject))
                graph_terms.patch_predicates.add(str(predicate))
                graph_terms.patch_objects.add(str(object_node))
        return terms_by_graph
    def _staged_snapshot_drift_relevance(
        self,
        *,
        exact_changed_triples_available: bool,
        triples_added_since_snapshot: list[GraphTripleDescription],
        triples_removed_since_snapshot: list[GraphTripleDescription],
        patch_terms: _StagedRevisionDriftTerms | None,
    ) -> tuple[str, list[str], list[str], list[str], list[str], str]:
        if not exact_changed_triples_available:
            return (
                "unknown_no_exact_diff",
                [],
                [],
                [],
                [],
                "Drift relevance to the staged patch cannot be classified "
                "because exact changed triples are unavailable.",
            )
        if patch_terms is None:
            return (
                "unknown_no_patch_terms",
                [],
                [],
                [],
                [],
                "Drift relevance to the staged patch cannot be classified "
                "because patch terms were unavailable.",
            )

        changed_triples = [
            *triples_added_since_snapshot,
            *triples_removed_since_snapshot,
        ]
        changed_subjects = {triple.subject for triple in changed_triples}
        changed_predicates = {triple.predicate for triple in changed_triples}
        changed_objects = {triple.object for triple in changed_triples}
        changed_terms = changed_subjects | changed_predicates | changed_objects
        subject_overlap = sorted(patch_terms.patch_subjects & changed_subjects)
        predicate_overlap = sorted(patch_terms.patch_predicates & changed_predicates)
        object_overlap = sorted(patch_terms.patch_objects & changed_terms)
        anchor_overlap = sorted(patch_terms.revision_anchors & changed_terms)
        if subject_overlap and predicate_overlap:
            return (
                "patch_subject_and_predicate_overlap",
                subject_overlap,
                predicate_overlap,
                object_overlap,
                anchor_overlap,
                "Exact drift overlaps the staged patch subjects and predicates; "
                "review carefully before restaging.",
            )
        if subject_overlap:
            return (
                "patch_subject_overlap",
                subject_overlap,
                predicate_overlap,
                object_overlap,
                anchor_overlap,
                "Exact drift overlaps the staged patch subjects; review "
                "carefully before restaging.",
            )
        if object_overlap and anchor_overlap:
            return (
                "patch_object_and_anchor_overlap",
                [],
                predicate_overlap,
                object_overlap,
                anchor_overlap,
                "Exact drift does not touch staged patch subjects, but it does "
                "touch staged patch objects and revision anchors; review "
                "semantic relevance before restaging.",
            )
        if object_overlap:
            if self._is_broad_snapshot_drift_object_overlap(object_overlap):
                return (
                    "broad_patch_object_overlap",
                    [],
                    predicate_overlap,
                    object_overlap,
                    anchor_overlap,
                    "Exact drift does not touch staged patch subjects, and its "
                    "only staged patch object overlap is broad vocabulary such as "
                    "a shared class/type term; treat this as a weak relevance "
                    "hint and review semantic relevance before restaging.",
                )
            return (
                "patch_object_overlap",
                [],
                predicate_overlap,
                object_overlap,
                anchor_overlap,
                "Exact drift does not touch staged patch subjects, but it does "
                "touch objects used by the staged patch; review semantic "
                "relevance before restaging.",
            )
        if anchor_overlap:
            return (
                "revision_anchor_overlap",
                [],
                predicate_overlap,
                object_overlap,
                anchor_overlap,
                "Exact drift does not touch staged patch subjects, but it does "
                "touch revision anchors; review semantic relevance before "
                "restaging.",
            )
        return (
            "no_patch_subject_overlap",
            [],
            predicate_overlap,
            [],
            [],
            "Exact drift does not touch staged patch subjects. Predicate "
            "overlap is reported separately, even when empty, and may "
            "reflect broad schema activity; DoxaBase still blocks apply "
            "until the proposal is reviewed and restaged.",
        )
    def _applied_event_for_staged_revision(
        self,
        staged_revision_iri: str | None,
        *,
        graphs: Iterable[str] | None = None,
    ) -> str | None:
        if staged_revision_iri is None:
            return None
        lookup_graphs = list(graphs) if graphs is not None else self._expand_graphs(
            ["history"]
        )
        return self._first_subject(
            lookup_graphs,
            "rc:appliesStagedRevision",
            staged_revision_iri,
        )
    @staticmethod
    def _staged_patch_count_basis(target_graph: str | None) -> str | None:
        if target_graph is None:
            return None
        if target_graph == "ontology":
            return "target_graph_plus_base_ontology"
        if target_graph == "shapes":
            return "target_graph_plus_base_shapes"
        return "target_graph_only"
    @staticmethod
    def _patch_checks_have_no_effective_delta(
        patch_checks: list[StagedPatchApplyCheck],
    ) -> bool:
        if not patch_checks:
            return False
        return all(
            patch_check.effective_triples_to_add == 0
            and patch_check.effective_triples_to_remove == 0
            for patch_check in patch_checks
        )
    def _staged_apply_effective_delta_summary(
        self,
        patch_checks: list[StagedPatchApplyCheck],
        *,
        replayable_triples_to_add: int,
        replayable_triples_to_remove: int,
    ) -> StagedRevisionEffectiveDeltaSummary:
        blocked_triples_to_add = 0
        blocked_triples_to_remove = 0
        has_conflicted_patches = False
        patch_triple_status_counts: dict[str, int] = {}
        for patch_check in patch_checks:
            if patch_check.conflict is not None:
                has_conflicted_patches = True
                blocked_triples_to_add += patch_check.effective_triples_to_add or 0
                blocked_triples_to_remove += (
                    patch_check.effective_triples_to_remove or 0
                )
            patch_triple_status = (
                self._staged_patch_triple_presence_status_from_apply_check(
                    patch_check
                )
            )
            if patch_triple_status is not None:
                patch_triple_status_counts[patch_triple_status] = (
                    patch_triple_status_counts.get(patch_triple_status, 0) + 1
                )

        if not patch_checks:
            basis = "no_patch_checks"
            note = "No staged patch replay was inspected for this apply check."
        elif has_conflicted_patches:
            basis = "conflicted_patches_excluded"
            note = (
                "Replayable deltas exclude conflicted patches. Use "
                "blocked_patch_triples_to_add/remove to see the current effective "
                "payload of patches that could not be replayed directly."
            )
        else:
            basis = "all_patches_replayable"
            note = (
                "All inspected patches replayed mechanically; replayable deltas "
                "cover the full current effective payload."
            )

        return StagedRevisionEffectiveDeltaSummary(
            replayable_triples_to_add=replayable_triples_to_add,
            replayable_triples_to_remove=replayable_triples_to_remove,
            blocked_patch_triples_to_add=blocked_triples_to_add,
            blocked_patch_triples_to_remove=blocked_triples_to_remove,
            total_effective_triples_to_add=(
                replayable_triples_to_add + blocked_triples_to_add
            ),
            total_effective_triples_to_remove=(
                replayable_triples_to_remove + blocked_triples_to_remove
            ),
            already_effective=self._patch_checks_have_no_effective_delta(
                patch_checks
            ),
            has_conflicted_patches=has_conflicted_patches,
            patch_triple_status_counts=patch_triple_status_counts,
            basis=basis,
            note=note,
        )
    def _staged_patch_repair_plan(
        self,
        staged: StagedGraphRevisionDescription,
        *,
        patch_checks: list[StagedPatchApplyCheck],
        snapshot_drifts: list[StagedGraphSnapshotDrift],
        validation_scope: str,
    ) -> list[StagedPatchRepairPlan]:
        if not staged.patches:
            return []
        if len(staged.patches) != len(patch_checks):
            return []

        plan: list[StagedPatchRepairPlan] = []
        for patch, patch_check in zip(staged.patches, patch_checks, strict=True):
            patch_triple_status = (
                self._staged_patch_triple_presence_status_from_apply_check(
                    patch_check
                )
            )
            effect_class, recommended_action_kind, note = (
                self._staged_patch_repair_default_classification(
                    patch_check,
                    patch_triple_status=patch_triple_status,
                )
            )
            action: SuggestedNextAction | None = None
            current_same_slot_triples: list[ResourceTriple] = []
            proposed_triples: list[GraphTripleDescription] = []
            try:
                same_slot_details = (
                    self._staged_patch_same_slot_replacement_details(
                        staged,
                        patch,
                        snapshot_drifts=snapshot_drifts,
                        validation_scope=validation_scope,
                    )
                )
            except DoxaBaseError:
                same_slot_details = None
            if same_slot_details is not None:
                action, current_same_slot_triples, proposed_triples = (
                    same_slot_details
                )
                effect_class = "same_slot_replace"
                recommended_action_kind = "stage_map_assertion_change"
                note = (
                    "This single-triple subpatch targets a guarded "
                    "single-valued map slot whose current value changed since "
                    "the staged snapshot. Stage the suggested replacement "
                    "after reviewing whether the staged value should supersede "
                    "the current value; split or restage any independent "
                    "patches separately."
                )

            plan.append(
                StagedPatchRepairPlan(
                    patch_iri=patch.iri,
                    patch_sequence_index=patch.sequence_index,
                    target_graph=patch_check.target_graph,
                    operation=patch_check.operation,
                    operation_label=patch_check.operation_label,
                    patch_role=patch_check.patch_role,
                    patch_role_label=patch_check.patch_role_label,
                    triple_count=patch_check.triple_count,
                    patch_triple_status=patch_triple_status,
                    effect_class=effect_class,
                    recommended_action_kind=recommended_action_kind,
                    action=action,
                    current_same_subject_predicate_triples=(
                        current_same_slot_triples
                    ),
                    proposed_triples=proposed_triples,
                    note=note,
                )
            )
        return plan
    def _staged_patch_repair_default_classification(
        self,
        patch_check: StagedPatchApplyCheck,
        *,
        patch_triple_status: str | None,
    ) -> tuple[str, str, str]:
        effective_add = patch_check.effective_triples_to_add or 0
        effective_remove = patch_check.effective_triples_to_remove or 0
        effective_delta = effective_add + effective_remove
        addition_operation = self.expand_iri("rc:AdditionPatch")
        removal_operation = self.expand_iri("rc:RemovalPatch")
        if (
            patch_check.operation == addition_operation
            and patch_triple_status == "all_patch_triples_present"
        ):
            return (
                "already_effective_drop_or_inspect",
                "inspect_or_drop_from_repaired_successor",
                (
                    "All triples in this addition patch are already present in "
                    "the current graph. A repaired successor usually should not "
                    "add them again; inspect before dropping if the duplicate "
                    "presence carries semantic meaning."
                ),
            )
        if (
            patch_check.operation == removal_operation
            and patch_triple_status == "all_patch_triples_absent"
        ):
            return (
                "removal_already_absent",
                "inspect_or_drop_from_repaired_successor",
                (
                    "All triples in this removal patch are already absent in "
                    "the current graph. A repaired successor usually should "
                    "drop this no-op removal after review."
                ),
            )
        if patch_check.conflict is None:
            if effective_delta == 0:
                return (
                    "already_effective_drop_or_inspect",
                    "inspect_or_drop_from_repaired_successor",
                    (
                        "This patch replays cleanly but has no effective graph "
                        "delta in current state; inspect before dropping it."
                    ),
                )
            return (
                "keep_effective",
                "keep_in_repaired_successor",
                (
                    "This patch replays cleanly and still has an effective "
                    "graph delta."
                ),
            )
        if effective_delta > 0:
            return (
                "blocked_keep_or_repair",
                "review_before_restage_or_repair",
                (
                    "This patch is blocked by graph drift but still has an "
                    "effective payload. Review whether to restage it unchanged "
                    "or author a repaired subpatch."
                ),
            )
        return (
            "needs_review",
            "inspect_patch",
            (
                "This patch is blocked and DoxaBase did not recognize a safe "
                "mechanical subpatch repair."
            ),
        )
    def _staged_patch_same_slot_replacement_details(
        self,
        staged: StagedGraphRevisionDescription,
        patch: StagedGraphPatchDescription,
        *,
        snapshot_drifts: list[StagedGraphSnapshotDrift],
        validation_scope: str,
    ) -> tuple[SuggestedNextAction, list[ResourceTriple], list[GraphTripleDescription]] | None:
        if patch.target_graph != "map":
            return None
        addition_operation = self.expand_iri("rc:AdditionPatch")
        if patch.operation != addition_operation:
            return None
        patch_graph = self._parse_staged_patch_description(patch)
        rows = self._sort_graph_storage_rows(self._rdf_graph_storage_rows(patch_graph))
        if len(rows) != 1:
            return None
        row = rows[0]
        subject, subject_kind, predicate, object_value, object_kind, datatype, lang = row
        if subject_kind != "uri" or object_kind == "bnode":
            return None
        normalized_object_kind = "iri" if object_kind == "uri" else object_kind
        replacement_label = self._staged_same_slot_replacement_label(
            subject,
            predicate,
        )
        if replacement_label is None:
            return None
        if not self._staged_same_slot_replacement_object_allowed(
            predicate,
            normalized_object_kind,
            datatype,
        ):
            return None
        drift = next(
            (
                item
                for item in snapshot_drifts
                if item.graph_role == "map"
                and item.exact_changed_triples_available
                and item.exact_changed_triples_included
            ),
            None,
        )
        if drift is None:
            return None
        same_slot_added = [
            triple
            for triple in drift.triples_added_since_snapshot
            if triple.subject == subject
            and triple.predicate == predicate
            and not self._graph_triple_object_matches_assertion_candidate(
                triple,
                object_value=object_value,
                object_kind=normalized_object_kind,
                object_datatype=datatype,
                object_lang=lang,
            )
        ]
        if not same_slot_added:
            return None
        current_same_slot_triples = self._assertion_triples(
            ["map"],
            subject=subject,
            predicate=predicate,
            object_filter=None,
            limit=10,
        )
        if len(current_same_slot_triples) != 1:
            return None
        current = current_same_slot_triples[0]
        if (
            current.object == object_value
            and current.object_kind == object_kind
            and current.object_datatype == datatype
            and current.object_lang == lang
        ):
            return None
        rationale = (
            f"Repair patch {patch.sequence_index or 'unknown'} of staged "
            f"revision {staged.iri} by replacing the current "
            f"{replacement_label} value instead of mechanically restaging a "
            "multi-patch row that would add a competing value."
        )
        arguments: dict[str, Any] = {
            "subject": subject,
            "predicate": predicate,
            "object": object_value,
            "rationale": rationale,
            "change_kind": "replace",
            "graph": "map",
            "object_kind": normalized_object_kind,
            "restages_revision": staged.iri,
            "validation_scope": validation_scope,
        }
        if staged.alternative_to is not None:
            arguments["alternative_to"] = staged.alternative_to.iri
        if datatype is not None:
            arguments["object_datatype"] = datatype
        if lang is not None:
            arguments["object_lang"] = lang
        action = SuggestedNextAction(
                     tool="doxabase.stage_map_assertion_change",
                     args=arguments,
                     reason="Patch-level repair planning found a guarded single-valued "
                f"{replacement_label} subpatch inside a larger staged row. "
                "Stage this replacement only after deciding how to preserve, "
                "drop, or separately restage the other patches.",
                 )
        return (
            action,
            current_same_slot_triples,
            [self._graph_triple_description(row)],
        )
    @staticmethod
    def _staged_patch_repair_plan_has_semantic_repair(
        patch_repair_plan: Iterable[StagedPatchRepairPlan] | None,
    ) -> bool:
        return any(
            item.effect_class == "same_slot_replace"
            for item in patch_repair_plan or []
        )
    def _staged_patch_repair_plan_action(
        self,
        staged_revision_iri: str,
        *,
        validation_scope: str | None,
    ) -> SuggestedNextAction:
        arguments: dict[str, Any] = {"iri": staged_revision_iri}
        if validation_scope is not None:
            arguments["validation_scope"] = validation_scope
        return SuggestedNextAction(
                   tool="doxabase.draft_staged_revision_rebase",
                   args=arguments,
                   reason="Patch-level repair planning found at least one semantic "
                "same-slot subpatch inside a larger stale revision. Inspect the "
                "read-only patch_repair_plan before choosing which subpatches "
                "to replace, drop, or restage.",
               )
    def _staged_same_slot_replacement_action(
        self,
        staged: StagedGraphRevisionDescription | None,
        *,
        patch_checks: list[StagedPatchApplyCheck],
        snapshot_drifts: list[StagedGraphSnapshotDrift],
        validation_scope: str | None,
    ) -> SuggestedNextAction | None:
        if staged is None:
            return None
        if (
            staged.applied_by is not None
            or staged.restaged_by is not None
            or staged.current_restaged_by is not None
        ):
            return None

        candidate = self._single_map_assertion_candidate(staged)
        if candidate is None:
            return None
        (
            subject,
            predicate,
            object_value,
            object_kind,
            object_datatype,
            object_lang,
            change_kind,
        ) = candidate
        if change_kind not in {"add", "replace"} or object_value is None:
            return None
        replacement_label = self._staged_same_slot_replacement_label(
            subject,
            predicate,
        )
        if replacement_label is None:
            return None
        if not self._staged_same_slot_replacement_object_allowed(
            predicate,
            object_kind,
            object_datatype,
        ):
            return None

        addition_operation = self.expand_iri("rc:AdditionPatch")
        removal_operation = self.expand_iri("rc:RemovalPatch")
        if len(staged.patches) != len(patch_checks):
            return None
        patch_operations = [patch.operation for patch in staged.patches]
        if patch_operations.count(addition_operation) != 1:
            return None
        if change_kind == "add" and len(staged.patches) != 1:
            return None
        if (
            change_kind == "replace"
            and (
                len(staged.patches) != 2
                or patch_operations.count(removal_operation) != 1
            )
        ):
            return None
        addition_check: StagedPatchApplyCheck | None = None
        for patch, patch_check in zip(staged.patches, patch_checks, strict=True):
            if (
                patch.target_graph != "map"
                or patch.triple_count != 1
                or patch.operation not in {addition_operation, removal_operation}
                or patch_check.target_graph != "map"
                or patch_check.operation != patch.operation
                or patch_check.triple_count != 1
            ):
                return None
            if patch.operation == addition_operation:
                addition_check = patch_check
        if (
            addition_check is None
            or addition_check.already_present_triples != 0
            or addition_check.already_absent_triples != 1
        ):
            return None

        drift = next(
            (
                item
                for item in snapshot_drifts
                if item.graph_role == "map"
                and item.exact_changed_triples_available
                and item.exact_changed_triples_included
            ),
            None,
        )
        if drift is None:
            return None

        same_slot_added = [
            triple
            for triple in drift.triples_added_since_snapshot
            if triple.subject == subject
            and triple.predicate == predicate
            and not self._graph_triple_object_matches_assertion_candidate(
                triple,
                object_value=object_value,
                object_kind=object_kind,
                object_datatype=object_datatype,
                object_lang=object_lang,
            )
        ]
        if not same_slot_added:
            return None
        current_same_slot_triples = self._assertion_triples(
            ["map"],
            subject=subject,
            predicate=predicate,
            object_filter=None,
            limit=10,
        )
        if len(current_same_slot_triples) != 1:
            return None
        current = current_same_slot_triples[0]
        normalized_object_kind = "uri" if object_kind == "iri" else object_kind
        if (
            current.object == object_value
            and current.object_kind == normalized_object_kind
            and current.object_datatype == object_datatype
            and current.object_lang == object_lang
        ):
            return None

        rationale = (
            "Exact snapshot drift shows the current map now has a different "
            f"{replacement_label} value for this same resource. Stage a replacement "
            "successor that preserves restage provenance instead of replaying "
            "the stale source patch as-is."
        )
        arguments: dict[str, Any] = {
            "subject": subject,
            "predicate": predicate,
            "object": object_value,
            "rationale": rationale,
            "change_kind": "replace",
            "graph": "map",
            "object_kind": object_kind,
            "restages_revision": staged.iri,
            "validation_scope": validation_scope or "all",
        }
        if staged.alternative_to is not None:
            arguments["alternative_to"] = staged.alternative_to.iri
        if object_datatype is not None:
            arguments["object_datatype"] = object_datatype
        if object_lang is not None:
            arguments["object_lang"] = object_lang
        reason = (
            "Exact snapshot rows show a different current value for the same "
            f"single-valued {replacement_label} slot. Stage a reviewable replacement "
            "successor instead of a raw restage that would add a competing "
            f"{replacement_label} value."
        )
        return SuggestedNextAction(
                   tool="doxabase.stage_map_assertion_change",
                   args=arguments,
                   reason=reason,
               )
    def _staged_ambiguous_same_slot_review_action(
        self,
        staged: StagedGraphRevisionDescription | None,
        *,
        patch_checks: list[StagedPatchApplyCheck],
        snapshot_drifts: list[StagedGraphSnapshotDrift],
    ) -> SuggestedNextAction | None:
        if staged is None:
            return None
        if (
            staged.applied_by is not None
            or staged.restaged_by is not None
            or staged.current_restaged_by is not None
        ):
            return None

        candidate = self._single_map_assertion_candidate(staged)
        if candidate is None:
            return None
        (
            subject,
            predicate,
            object_value,
            object_kind,
            object_datatype,
            object_lang,
            change_kind,
        ) = candidate
        if change_kind not in {"add", "replace"} or object_value is None:
            return None
        replacement_label = self._staged_same_slot_replacement_label(
            subject,
            predicate,
        )
        if replacement_label is None:
            return None
        if not self._staged_same_slot_replacement_object_allowed(
            predicate,
            object_kind,
            object_datatype,
        ):
            return None

        addition_operation = self.expand_iri("rc:AdditionPatch")
        removal_operation = self.expand_iri("rc:RemovalPatch")
        if len(staged.patches) != len(patch_checks):
            return None
        patch_operations = [patch.operation for patch in staged.patches]
        if patch_operations.count(addition_operation) != 1:
            return None
        if change_kind == "add" and len(staged.patches) != 1:
            return None
        if (
            change_kind == "replace"
            and (
                len(staged.patches) != 2
                or patch_operations.count(removal_operation) != 1
            )
        ):
            return None
        addition_check: StagedPatchApplyCheck | None = None
        for patch, patch_check in zip(staged.patches, patch_checks, strict=True):
            if (
                patch.target_graph != "map"
                or patch.triple_count != 1
                or patch.operation not in {addition_operation, removal_operation}
                or patch_check.target_graph != "map"
                or patch_check.operation != patch.operation
                or patch_check.triple_count != 1
            ):
                return None
            if patch.operation == addition_operation:
                addition_check = patch_check
        if (
            addition_check is None
            or addition_check.already_present_triples != 0
            or addition_check.already_absent_triples != 1
        ):
            return None

        drift = next(
            (
                item
                for item in snapshot_drifts
                if item.graph_role == "map"
                and item.exact_changed_triples_available
                and item.exact_changed_triples_included
            ),
            None,
        )
        if drift is None:
            return None

        same_slot_added = [
            triple
            for triple in drift.triples_added_since_snapshot
            if triple.subject == subject
            and triple.predicate == predicate
            and not self._graph_triple_object_matches_assertion_candidate(
                triple,
                object_value=object_value,
                object_kind=object_kind,
                object_datatype=object_datatype,
                object_lang=object_lang,
            )
        ]
        if not same_slot_added:
            return None
        current_same_slot_triples = self._assertion_triples(
            ["map"],
            subject=subject,
            predicate=predicate,
            object_filter=None,
            limit=10,
        )
        if len(current_same_slot_triples) <= 1:
            return None

        arguments: dict[str, Any] = {
            "iri": subject,
            "aspect": "assertion_support",
            "predicate": predicate,
            "object": object_value,
            "graph": "map",
            "object_kind": object_kind,
            "limit": 20,
        }
        if object_datatype is not None:
            arguments["object_datatype"] = object_datatype
        if object_lang is not None:
            arguments["object_lang"] = object_lang
        reason = (
            "Exact snapshot rows show same-slot drift for this stale source, "
            f"but the current map has {len(current_same_slot_triples)} "
            f"{replacement_label} values. Inspect the assertion support and "
            "stage an explicit repair or replacement instead of mechanically "
            "restaging the stale patch."
        )
        return SuggestedNextAction(
                   tool="doxabase.describe_resource",
                   args=arguments,
                   reason=reason,
               )
    def _staged_same_slot_replacement_label(
        self,
        subject: str,
        predicate: str,
    ) -> str | None:
        rules_without_type_guard = {
            self.expand_iri("rc:rowSemantics"): "row-semantics",
        }
        if predicate in rules_without_type_guard:
            return rules_without_type_guard[predicate]

        subject_types = set(self._types_from_graphs(["map"], subject))
        column_rules = {
            self.expand_iri("rc:physicalType"): "physical type",
            self.expand_iri("rc:nullable"): "nullable",
        }
        if (
            predicate in column_rules
            and self.expand_iri("rc:Column") in subject_types
        ):
            return column_rules[predicate]

        asset_types = {
            self.expand_iri("rc:DataAsset"),
            self.expand_iri("rc:Dataset"),
            self.expand_iri("rc:Table"),
            self.expand_iri("rc:Database"),
            self.expand_iri("rc:DataFile"),
            self.expand_iri("rc:DataFrame"),
        }
        if (
            predicate == self.expand_iri("rc:schemaStability")
            and subject_types & asset_types
        ):
            return "schema stability"
        return None
    def _staged_same_slot_replacement_object_allowed(
        self,
        predicate: str,
        object_kind: str,
        object_datatype: str | None,
    ) -> bool:
        normalized_kind = "iri" if object_kind == "uri" else object_kind
        iri_slots = {
            self.expand_iri("rc:rowSemantics"),
            self.expand_iri("rc:physicalType"),
            self.expand_iri("rc:schemaStability"),
        }
        if predicate in iri_slots:
            return normalized_kind == "iri"
        if predicate == self.expand_iri("rc:nullable"):
            return (
                normalized_kind == "literal"
                and object_datatype == str(XSD.boolean)
            )
        return False
    def export_staged_revision(
        self,
        iri: str,
        path: str | Path,
        *,
        format: TypingLiteral["markdown"] = "markdown",
        overwrite: bool = False,
        fail_on_sensitive: bool = False,
    ) -> StagedGraphRevisionExportRecord:
        if format != "markdown":
            raise DoxaBaseError("Only markdown staged revision exports are supported")
        description = self.describe_staged_revision(iri)
        apply_check, apply_check_error = self._staged_revision_apply_check_for_export(
            description
        )
        data = self._staged_revision_markdown(
            description,
            apply_check=apply_check,
            apply_check_error=apply_check_error,
        )
        sensitive_literal_count, privacy_warnings = (
            self._markdown_export_privacy_warnings(
                data,
                final_privacy_warning_line_numbers=True,
            )
        )
        shareability_hint_count, shareability_hint_matches = (
            self._shareability_hint_matches_for_markdown(
                data,
                export_part="staged_revision_markdown",
                final_privacy_warning_line_numbers=bool(privacy_warnings),
            )
        )
        shareability_hints = self._shareability_hints_for_markdown(data)
        self._raise_if_markdown_sensitive_export_blocked(
            fail_on_sensitive=fail_on_sensitive,
            sensitive_literal_count=sensitive_literal_count,
            privacy_warnings=privacy_warnings,
        )
        data = self._markdown_with_privacy_warning(data, privacy_warnings)
        bytes_written = self._write_export(path, data, overwrite=overwrite)
        return StagedGraphRevisionExportRecord(
            path=str(path),
            format=format,
            revision_iri=description.iri,
            bytes_written=bytes_written,
            sensitive_literal_count=sensitive_literal_count,
            privacy_warnings=privacy_warnings,
            decision=(
                "block"
                if sensitive_literal_count
                else "clean_by_scanner_only"
            ),
            scanner_clean=sensitive_literal_count == 0,
            would_block_sensitive_export=sensitive_literal_count > 0,
            shareability_hints=shareability_hints,
            shareability_hint_count=shareability_hint_count,
            returned_shareability_hint_count=len(shareability_hint_matches),
            omitted_shareability_hint_count=max(
                0,
                shareability_hint_count - len(shareability_hint_matches),
            ),
            shareability_hint_matches=shareability_hint_matches,
        )
    def export_staged_revisions(
        self,
        revision_iris: Iterable[str] | str,
        path: str | Path,
        *,
        title: str | None = None,
        executive_summary: str | None = None,
        format: TypingLiteral["markdown"] = "markdown",
        overwrite: bool = False,
        fail_on_sensitive: bool = False,
    ) -> StagedGraphRevisionsExportRecord:
        if format != "markdown":
            raise DoxaBaseError("Only markdown staged revision exports are supported")
        revision_values = self._string_values(
            "revision_iris",
            revision_iris,
            required=True,
        )
        revision_values = list(dict.fromkeys(revision_values))
        for revision_iri in revision_values:
            self._ensure_staged_revision_exportable(revision_iri)
        descriptions = [
            self.describe_staged_revision(revision_iri)
            for revision_iri in revision_values
        ]
        with self._scoped_staged_apply_check_cache():
            apply_checks = [
                self._staged_revision_apply_check_for_export(description)
                for description in descriptions
            ]
        revision_summaries = self._staged_revisions_export_summaries(
            descriptions,
            apply_checks=apply_checks,
        )
        snapshot_evidence_summary = (
            self._staged_revisions_snapshot_evidence_summary(descriptions)
        )
        bundle_summary = self._staged_revisions_bundle_summary(
            revision_summaries,
            descriptions=descriptions,
            snapshot_evidence=snapshot_evidence_summary,
        )
        data = self._staged_revisions_markdown(
            descriptions,
            apply_checks=apply_checks,
            revision_summaries=revision_summaries,
            bundle_summary=bundle_summary,
            snapshot_evidence_summary=snapshot_evidence_summary,
            title=title,
            executive_summary=executive_summary,
        )
        sensitive_literal_count, privacy_warnings = (
            self._markdown_export_privacy_warnings(
                data,
                final_privacy_warning_line_numbers=True,
            )
        )
        shareability_hint_count, shareability_hint_matches = (
            self._shareability_hint_matches_for_markdown(
                data,
                export_part="staged_revisions_markdown",
                final_privacy_warning_line_numbers=bool(privacy_warnings),
            )
        )
        shareability_hints = self._shareability_hints_for_markdown(data)
        self._raise_if_markdown_sensitive_export_blocked(
            fail_on_sensitive=fail_on_sensitive,
            sensitive_literal_count=sensitive_literal_count,
            privacy_warnings=privacy_warnings,
        )
        data = self._markdown_with_privacy_warning(data, privacy_warnings)
        bytes_written = self._write_export(path, data, overwrite=overwrite)
        return StagedGraphRevisionsExportRecord(
            path=str(path),
            format=format,
            revision_iris=[description.iri for description in descriptions],
            revision_count=len(descriptions),
            bytes_written=bytes_written,
            revision_summaries=revision_summaries,
            bundle_summary=bundle_summary,
            sensitive_literal_count=sensitive_literal_count,
            privacy_warnings=privacy_warnings,
            decision=(
                "block"
                if sensitive_literal_count
                else "clean_by_scanner_only"
            ),
            scanner_clean=sensitive_literal_count == 0,
            would_block_sensitive_export=sensitive_literal_count > 0,
            shareability_hints=shareability_hints,
            shareability_hint_count=shareability_hint_count,
            returned_shareability_hint_count=len(shareability_hint_matches),
            omitted_shareability_hint_count=max(
                0,
                shareability_hint_count - len(shareability_hint_matches),
            ),
            shareability_hint_matches=shareability_hint_matches,
        )
    def _ensure_staged_revision_exportable(self, iri: str) -> None:
        revision_iri = self.expand_iri(iri)
        data_graphs = self._expand_graphs(["history"])
        if not self._subject_exists(revision_iri, data_graphs):
            return
        if self.expand_iri("rc:GraphRevision") not in self._types_from_graphs(
            data_graphs,
            revision_iri,
        ):
            return
        if self._objects(data_graphs, revision_iri, "rc:hasGraphPatch"):
            return
        applied_source = self._first_object(
            data_graphs,
            revision_iri,
            "rc:appliesStagedRevision",
        )
        if applied_source is not None:
            raise DoxaBaseError(
                "export_staged_revisions only accepts staged patch revisions; "
                f"'{iri}' is an applied revision event. Use "
                "describe_graph_revision or describe_revision_lineage for the "
                "applied event, or pass the applied event's staged source IRI "
                f"'{applied_source}'."
            )
        raise DoxaBaseError(
            "export_staged_revisions only accepts staged patch revisions; "
            f"graph revision '{iri}' has no staged patch entries. Use "
            "describe_graph_revision for revision metadata instead."
        )
    def _staged_revisions_export_summaries(
        self,
        descriptions: list[StagedGraphRevisionDescription],
        *,
        apply_checks: list[tuple[StagedRevisionApplyCheck | None, str | None]],
    ) -> list[StagedGraphRevisionExportSummary]:
        summaries: list[StagedGraphRevisionExportSummary] = []
        for description, (apply_check, apply_check_error) in zip(
            descriptions,
            apply_checks,
            strict=True,
        ):
            restaged_from = (
                description.restaged_from.iri
                if description.restaged_from is not None
                else None
            )
            restaged_by = (
                description.restaged_by.iri
                if description.restaged_by is not None
                else None
            )
            current_restaged_by = (
                description.current_restaged_by.iri
                if description.current_restaged_by is not None
                else None
            )
            stale_resolution_state = self._stale_resolution_state(
                status=apply_check.status if apply_check is not None else None,
                has_patch_payload=bool(description.patches),
                restaged_from=restaged_from,
                restaged_by=restaged_by,
            )
            apply_recommended_resolution = (
                apply_check.recommended_resolution
                if apply_check is not None
                else None
            )
            suggested_next_actions = (
                apply_check.suggested_next_actions if apply_check is not None else []
            )
            staged_validation_status = self._staged_validation_status(
                conforms=description.validation_conforms,
                result_count=description.validation_result_count,
            )
            next_action = self._revision_next_action(
                description.iri,
                apply_status=apply_check.status if apply_check is not None else None,
                apply_decision=(
                    apply_check.decision if apply_check is not None else None
                ),
                stale_resolution_state=stale_resolution_state,
                suggested_next_actions=suggested_next_actions,
                restaged_by=restaged_by,
                current_restaged_by=current_restaged_by,
                staged_validation_status=staged_validation_status,
            )
            summary_recommendation = (
                self._staged_revisions_effective_recommendation(
                    review_recommendation=description.review_recommendation,
                    stale_resolution_state=stale_resolution_state,
                    restaged_by=restaged_by,
                    current_restaged_by=current_restaged_by,
                    apply_status=(
                        apply_check.status if apply_check is not None else None
                    ),
                    apply_decision=(
                        apply_check.decision if apply_check is not None else None
                    ),
                    apply_recommended_resolution=apply_recommended_resolution,
                    staged_validation_status=staged_validation_status,
                    next_action=next_action,
                )
            )
            summary_recommendation_source = (
                self._staged_revisions_effective_recommendation_source(
                    review_recommendation=description.review_recommendation,
                    stale_resolution_state=stale_resolution_state,
                    apply_status=(
                        apply_check.status if apply_check is not None else None
                    ),
                    apply_decision=(
                        apply_check.decision if apply_check is not None else None
                    ),
                    apply_recommended_resolution=apply_recommended_resolution,
                    staged_validation_status=staged_validation_status,
                    next_action=next_action,
                )
            )
            shared_context_patch_summaries = (
                self._staged_description_shared_semantic_context_patch_summaries(
                    description
                )
            )
            summaries.append(
                StagedGraphRevisionExportSummary(
                    revision_iri=description.iri,
                    summary=description.summary,
                    revision_stance=description.revision_stance,
                    revision_stance_label=description.revision_stance_label,
                    alternative_to=(
                        description.alternative_to.iri
                        if description.alternative_to is not None
                        else None
                    ),
                    current_alternative_to=(
                        description.alternative_gate.current_alternative_to
                    ),
                    alternative_gate=description.alternative_gate,
                    changed_graphs=description.changed_graphs,
                    apply_status=apply_check.status if apply_check is not None else None,
                    apply_decision=(
                        apply_check.decision if apply_check is not None else None
                    ),
                    apply_can_apply=(
                        apply_check.can_apply if apply_check is not None else None
                    ),
                    apply_summary=(
                        apply_check.summary if apply_check is not None else None
                    ),
                    apply_recommended_resolution=apply_recommended_resolution,
                    apply_recommendation_scope=(
                        self._staged_revisions_apply_recommendation_scope(
                            stale_resolution_state=stale_resolution_state,
                            apply_recommended_resolution=(
                                apply_recommended_resolution
                            ),
                        )
                    ),
                    apply_blocking_reasons=(
                        apply_check.blocking_reasons
                        if apply_check is not None
                        else []
                    ),
                    apply_validation_conforms=(
                        apply_check.validation_conforms
                        if apply_check is not None
                        else None
                    ),
                    apply_validation_skipped_reason=(
                        apply_check.validation_skipped_reason
                        if apply_check is not None
                        else None
                    ),
                    apply_validation_result_count=(
                        apply_check.validation_result_count
                        if apply_check is not None
                        else None
                    ),
                    apply_check_error=apply_check_error,
                    semantic_risk_level=(
                        apply_check.semantic_risk_level
                        if apply_check is not None
                        else None
                    ),
                    semantic_risk_reasons=(
                        apply_check.semantic_risk_reasons
                        if apply_check is not None
                        else []
                    ),
                    current_validation=self._staged_apply_check_validation_cell(
                        apply_check,
                        apply_check_error=apply_check_error,
                    ),
                    staged_validation=self._staged_description_validation_cell(
                        description
                    ),
                    staged_validation_conforms=description.validation_conforms,
                    staged_validation_result_count=description.validation_result_count,
                    validation_diagnostic_headline=(
                        self._validation_diagnostic_headline(description)
                    ),
                    review_recommendation=description.review_recommendation,
                    summary_recommendation=summary_recommendation,
                    summary_recommendation_source=summary_recommendation_source,
                    active_recommendation_field="summary_recommendation",
                    restaged_from=restaged_from,
                    restaged_by=restaged_by,
                    current_restaged_by=current_restaged_by,
                    stale_resolution_state=stale_resolution_state,
                    shared_context_patch_count=len(shared_context_patch_summaries),
                    shared_context_graphs=sorted(
                        {
                            summary.target_graph
                            for summary in shared_context_patch_summaries
                        }
                    ),
                    profile_route_keys=description.profile_route_keys,
                    profile_route_groups=description.profile_route_groups,
                    next_action=next_action,
                    suggested_next_actions=suggested_next_actions,
                )
            )
        return summaries
    @staticmethod
    def _staged_revisions_changed_graph_counts(
        summaries: Iterable[StagedGraphRevisionExportSummary],
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for summary in summaries:
            for graph in summary.changed_graphs:
                counts[graph] = counts.get(graph, 0) + 1
        return dict(sorted(counts.items()))
    @staticmethod
    def _staged_revisions_modelling_role(
        summary: StagedGraphRevisionExportSummary,
        *,
        queue: str | None,
        alternative_set_role: str | None,
    ) -> tuple[str, str, str]:
        changed_graphs = set(summary.changed_graphs)
        if (
            queue == "repair_or_replace"
            or summary.staged_validation_conforms is False
            or summary.apply_status == "validation_failed"
        ):
            return (
                "repair_diagnostic",
                "validation",
                (
                    "Validation failed or repair is queued; use this row as "
                    "diagnostic input before applying a replacement."
                ),
            )
        if "patterns" in changed_graphs and "map" not in changed_graphs:
            return (
                "pattern_first_alternative",
                "changed_graphs",
                (
                    "Touches patterns without map changes; keep the hunch "
                    "tentative while comparing alternatives."
                ),
            )
        if "map" in changed_graphs:
            return (
                "map_candidate",
                "changed_graphs",
                (
                    "Touches the map graph; review as a candidate current "
                    "project/data fact."
                ),
            )
        if {"ontology", "shapes"} & changed_graphs:
            return (
                "vocabulary_or_shape_candidate",
                "changed_graphs",
                (
                    "Touches ontology or shapes; review the modelling "
                    "vocabulary or validation surface before promotion."
                ),
            )
        if alternative_set_role is not None:
            return (
                "alternative_candidate",
                "alternative_set",
                "Competing alternative; compare with the choose-one set.",
            )
        if summary.stale_resolution_state in {
            "already_applied",
            "restaged_successor_already_applied",
            "noop",
            "restaged_successor_noop",
        }:
            return (
                "reference_row",
                "apply_status",
                "Useful for inspection or provenance rather than direct apply.",
            )
        return (
            "review_candidate",
            "queue",
            "Review the current queue and recommendation before acting.",
        )
    def _staged_revisions_decision_headline(
        self,
        *,
        total_revisions: int,
        next_action_queue_item_counts: dict[str, int],
        changed_graph_counts: dict[str, int],
        choose_one_group_count: int,
        snapshot_evidence: StagedGraphRevisionSnapshotEvidenceSummary,
        requires_recheck_after_each_apply: bool,
    ) -> str:
        parts = [f"Review {total_revisions} staged revision row(s)"]
        if next_action_queue_item_counts:
            parts.append(
                "queues: "
                + self._staged_revisions_count_summary(
                    next_action_queue_item_counts
                )
            )
        if changed_graph_counts:
            parts.append(
                "changed graphs: "
                + self._staged_revisions_count_summary(changed_graph_counts)
            )
        if choose_one_group_count:
            parts.append(f"{choose_one_group_count} choose-one group(s)")
        if requires_recheck_after_each_apply:
            parts.append("recheck siblings after each apply")
        if snapshot_evidence.rows:
            snapshot_state = "complete" if snapshot_evidence.complete else "incomplete"
            parts.append(
                f"snapshot evidence {snapshot_state} for "
                f"{snapshot_evidence.total_revision_count} row(s)"
            )
        return "; ".join(parts) + "."
    def _staged_revision_impact(
        self,
        *,
        impact_type: str,
        severity: str,
        changed_graph: str,
        subject: Node,
        predicate: Node,
        removed_values: list[Node],
        added_values: list[Node],
        lookup_graphs: list[str],
        revision_iri: str,
        message_template: str,
    ) -> StagedRevisionImpact:
        subject_summary = self._impact_resource_summary(lookup_graphs, subject)
        value_targets = [
            str(value)
            for value in [*removed_values, *added_values]
            if isinstance(value, URIRef)
        ]
        related = self._staged_revision_related_lore(
            [str(subject), *value_targets],
            exclude_revision_iri=revision_iri,
        )
        related_context_note = None
        if not any(related.values()):
            related_context_note = (
                "No linked observations, claims, patterns, evidence, or prior "
                "revisions were found for this impact's subject or changed values."
            )
        removed = [
            self._impact_value_summary(lookup_graphs, value)
            for value in removed_values
        ]
        added = [
            self._impact_value_summary(lookup_graphs, value)
            for value in added_values
        ]
        message = message_template.format(
            subject=self._impact_subject_label(subject_summary, subject),
            removed=self._impact_values_label(removed),
            added=self._impact_values_label(added),
        )
        return StagedRevisionImpact(
            impact_type=impact_type,
            severity=severity,
            changed_graph=changed_graph,
            subject=subject_summary,
            predicate=str(predicate),
            predicate_label=self._label_for_resource(str(predicate)),
            message=message,
            removed_values=removed,
            added_values=added,
            related_observations=related["observations"],
            related_claims=related["claims"],
            related_patterns=related["patterns"],
            related_evidence=related["evidence"],
            related_revisions=related["revisions"],
            related_context_note=related_context_note,
        )
    def _impact_value_summary(
        self,
        lookup_graphs: list[str],
        node: Node,
    ) -> StagedRevisionImpactValue:
        if isinstance(node, URIRef):
            return StagedRevisionImpactValue(
                value=str(node),
                value_label=self._display_label_from_graphs(lookup_graphs, str(node))
                or self._local_name(str(node)),
                value_kind="iri",
                caveat=self._impact_caveat_description(lookup_graphs, str(node)),
            )
        if isinstance(node, Literal):
            return StagedRevisionImpactValue(
                value=str(node),
                value_label=None,
                value_kind="literal",
            )
        return StagedRevisionImpactValue(
            value=str(node),
            value_label=None,
            value_kind="blank_node",
        )
    def _impact_subject_label(
        self,
        summary: ResourceSummary | None,
        fallback: Node,
    ) -> str:
        if summary is None:
            return str(fallback)
        return summary.label or summary.column_name or summary.iri
    def _impact_values_label(
        self,
        values: list[StagedRevisionImpactValue],
    ) -> str:
        if not values:
            return "(none)"
        labels = [value.value_label or value.value for value in values]
        return ", ".join(labels)
    def _parse_staged_patch_specs(
        self,
        *,
        additions: Iterable[Mapping[str, str]] | None,
        removals: Iterable[Mapping[str, str]] | None,
    ) -> list[dict[str, Any]]:
        parsed: list[dict[str, Any]] = []
        for operation, specs in (
            (self.expand_iri("rc:AdditionPatch"), additions),
            (self.expand_iri("rc:RemovalPatch"), removals),
        ):
            for spec in specs or []:
                graph_value = str(
                    spec.get("graph")
                    or spec.get("target_graph")
                    or spec.get("targetGraph")
                    or ""
                ).strip()
                if not graph_value:
                    raise DoxaBaseError("Each staged patch must name a graph")
                graph_names = self._graph_names_for_export([graph_value])
                if len(graph_names) != 1:
                    raise DoxaBaseError(
                        "Each staged patch must target exactly one concrete graph role"
                    )
                target_graph = graph_names[0]
                self._ensure_staged_patch_target_graph(target_graph)
                patch_format = str(spec.get("format") or "turtle").strip()
                content = str(spec.get("content") or spec.get("turtle") or "").strip()
                if not content:
                    raise DoxaBaseError("Each staged patch must include RDF content")
                patch_graph = Graph()
                self._bind_prefixes(patch_graph)
                try:
                    patch_graph.parse(data=content, format=patch_format)
                except Exception as exc:
                    detail = self._rdf_parse_error_detail(exc)
                    raise DoxaBaseError(
                        f"Could not parse staged patch for graph '{target_graph}' "
                        f"as {patch_format}: {detail}"
                    ) from exc
                if len(patch_graph) == 0:
                    raise DoxaBaseError("Staged patch content must contain triples")
                patch_role = str(
                    spec.get("patch_role")
                    or spec.get("patchRole")
                    or spec.get("role")
                    or "rc:FramingPatch"
                ).strip()
                patch_role_iri = self.expand_iri(patch_role)
                self._ensure_graph_patch_role(patch_role_iri)
                parsed.append(
                    {
                        "patch_iri": self._mint_iri("graph-patch"),
                        "operation": operation,
                        "target_graph": target_graph,
                        "format": patch_format,
                        "patch_role": patch_role_iri,
                        "content": content,
                        "graph": patch_graph,
                    }
                )
        return parsed
    def _ordered_staged_patch_specs_from_descriptions(
        self,
        patches: list[StagedGraphPatchDescription],
    ) -> list[dict[str, Any]]:
        addition_operation = self.expand_iri("rc:AdditionPatch")
        removal_operation = self.expand_iri("rc:RemovalPatch")
        parsed: list[dict[str, Any]] = []
        for patch in patches:
            operation = self._required_staged_patch_field(
                patch,
                "operation",
                patch.operation,
            )
            if operation not in {addition_operation, removal_operation}:
                raise DoxaBaseError(
                    f"Cannot restage unsupported patch operation '{operation}'"
                )
            target_graph = self._required_staged_patch_target_graph(patch)
            patch_format = self._required_staged_patch_field(
                patch,
                "format",
                patch.format,
            )
            content = self._required_staged_patch_field(
                patch,
                "content",
                patch.content,
            )
            patch_role = patch.patch_role or "rc:FramingPatch"
            patch_role_iri = self.expand_iri(patch_role)
            self._ensure_graph_patch_role(patch_role_iri)
            parsed.append(
                {
                    "patch_iri": self._mint_iri("graph-patch"),
                    "operation": operation,
                    "target_graph": target_graph,
                    "format": patch_format,
                    "patch_role": patch_role_iri,
                    "content": content,
                    "graph": self._parse_staged_patch_description(patch),
                }
            )
        return parsed
    def _parse_staged_patch_description(
        self,
        patch: StagedGraphPatchDescription,
    ) -> Graph:
        patch_format = self._required_staged_patch_field(
            patch,
            "format",
            patch.format,
        )
        content = self._required_staged_patch_field(
            patch,
            "content",
            patch.content,
        ).strip()
        if not content:
            raise DoxaBaseError(f"Staged patch '{patch.iri}' has empty content")
        patch_graph = Graph()
        self._bind_prefixes(patch_graph)
        try:
            patch_graph.parse(data=content, format=patch_format)
        except Exception as exc:
            target_graph = patch.target_graph or "(unknown graph)"
            detail = self._rdf_parse_error_detail(exc)
            raise DoxaBaseError(
                f"Could not parse staged patch '{patch.iri}' for graph "
                f"'{target_graph}' as {patch_format}: {detail}"
            ) from exc
        if len(patch_graph) == 0:
            raise DoxaBaseError(f"Staged patch '{patch.iri}' content has no triples")
        return patch_graph
    def _rdf_parse_error_detail(self, exc: Exception) -> str:
        lines = [line.strip() for line in str(exc).splitlines() if line.strip()]
        if not lines:
            return exc.__class__.__name__
        if lines[0].startswith("at line") and len(lines) > 1:
            reason = lines[1].split(" at ^ in", 1)[0]
            return f"{lines[0]}: {reason}"
        return lines[0].split(" at ^ in", 1)[0][:500]
    def _required_staged_patch_target_graph(
        self,
        patch: StagedGraphPatchDescription,
    ) -> str:
        target_graph = self._required_staged_patch_field(
            patch,
            "target_graph",
            patch.target_graph,
        )
        try:
            graph_names = self._graph_names_for_export([target_graph])
        except DoxaBaseError as exc:
            raise DoxaBaseError(
                f"Staged patch '{patch.iri}' targets unknown graph role "
                f"'{target_graph}'"
            ) from exc
        if len(graph_names) != 1 or graph_names[0] != target_graph:
            raise DoxaBaseError(
                f"Staged patch '{patch.iri}' must target exactly one concrete "
                f"graph role, not '{target_graph}'"
            )
        self._ensure_staged_patch_target_graph(target_graph, patch_iri=patch.iri)
        return target_graph
    def _ensure_staged_patch_target_graph(
        self,
        target_graph: str,
        *,
        patch_iri: str | None = None,
    ) -> None:
        self._ensure_mutable(target_graph)
        if target_graph == "history":
            prefix = (
                f"Staged patch '{patch_iri}'"
                if patch_iri is not None
                else "stage_graph_revision"
            )
            raise DoxaBaseError(
                f"{prefix} cannot target 'history' because staged revision "
                "metadata is itself recorded in history; use record_graph_revision "
                "for durable history notes or stage the project graph change the "
                "history note describes."
            )
    def _required_staged_patch_field(
        self,
        patch: StagedGraphPatchDescription,
        field_name: str,
        value: str | None,
    ) -> str:
        if value is None or not value.strip():
            raise DoxaBaseError(
                f"Staged patch '{patch.iri}' is missing required {field_name}"
            )
        return value.strip()
    @staticmethod
    def _staged_patch_identity(
        patch: StagedGraphPatchDescription,
    ) -> tuple[str, str, str, str]:
        return (
            patch.operation or "",
            patch.target_graph or "",
            patch.format or "",
            patch.content or "",
        )
    def _staged_revision_stored_review_context_markdown(
        self,
        context: StagedRevisionStoredReviewContext | None,
    ) -> list[str]:
        if context is None:
            return []
        signal_labels = []
        if context.review_note_signals.has_value_type_context:
            signal_labels.append("value type context")
        if context.review_note_signals.has_current_value_rationale:
            signal_labels.append("current value rationale")
        if context.review_note_signals.has_caveat_context:
            signal_labels.append("caveat context")
        if context.review_note_signals.has_related_routes:
            signal_labels.append("related routes")
        if context.review_note_signals.has_user_review_note:
            signal_labels.append("user/agent review note")
        counts = context.linked_support_counts
        lines = [
            "## Stored Review Context",
            "",
            (
                "- Source: Derived from persisted review/support metadata; "
                "this is not a replayed judgement panel."
            ),
            f"- Semantic risk: {context.semantic_risk_level}",
            "- Source fields: " + ", ".join(context.source_fields),
            (
                "- Review note signals: "
                + (", ".join(signal_labels) if signal_labels else "none")
            ),
            (
                "- Linked support counts: "
                f"observations={counts.observations}, claims={counts.claims}, "
                f"patterns={counts.patterns}, evidence={counts.evidence}, "
                f"revision_anchors={counts.revision_anchors}"
            ),
        ]
        if context.review_recommendation:
            lines.append(f"- Review recommendation: {context.review_recommendation}")
        if context.semantic_risk_reasons:
            lines.append("- Semantic risk reasons:")
            lines.extend(f"  - {reason}" for reason in context.semantic_risk_reasons)
        if context.attention_impacts:
            lines.append("- Attention impacts:")
            lines.extend(
                f"  - {impact.impact_type}: {impact.message}"
                for impact in context.attention_impacts[:5]
            )
        return lines
    def _staged_revision_judgement_panel(
        self,
        description: StagedGraphRevisionDescription,
    ) -> MapAssertionJudgementPanel | None:
        if not self._staged_revision_patch_counts_match(description):
            return None
        candidate = self._single_map_assertion_candidate(description)
        if candidate is None:
            return None
        (
            subject,
            predicate,
            object_value,
            object_kind,
            object_datatype,
            object_lang,
            change_kind,
        ) = candidate
        support = self.describe_assertion_support(
            subject,
            predicate,
            object_value,
            graph="map",
            object_kind=object_kind,  # type: ignore[arg-type]
            object_datatype=object_datatype,
            object_lang=object_lang,
        )
        support = self._assertion_support_without_revision(support, description.iri)
        return self._map_assertion_change_judgement_panel(
            support,
            change_kind=change_kind,
            recommendation=description.review_recommendation,
            impacts=description.impacts,
        )
    def _staged_revision_patch_counts_match(
        self,
        description: StagedGraphRevisionDescription,
    ) -> bool:
        existing_applied = self._subjects(
            self._expand_graphs(["history"]),
            "rc:appliesStagedRevision",
            description.iri,
        )
        if existing_applied:
            return False
        addition_operation = self.expand_iri("rc:AdditionPatch")
        removal_operation = self.expand_iri("rc:RemovalPatch")
        preview_graphs: dict[str, Graph] = {}
        for patch in description.patches:
            operation = patch.operation
            if operation is None:
                return False
            if operation not in {addition_operation, removal_operation}:
                return False
            try:
                target_graph = self._required_staged_patch_target_graph(patch)
                current_preview = preview_graphs.setdefault(
                    target_graph,
                    self.to_graph([target_graph]),
                )
                if (
                    patch.before_triple_count is not None
                    and len(current_preview) != patch.before_triple_count
                ):
                    return False
                patch_graph = self._parse_staged_patch_description(patch)
            except DoxaBaseError:
                return False
            candidate_preview = self._clone_graph(current_preview)
            if operation == addition_operation:
                for triple in patch_graph:
                    candidate_preview.add(triple)
            else:
                for triple in patch_graph:
                    candidate_preview.remove(triple)
            if (
                patch.after_triple_count is not None
                and len(candidate_preview) != patch.after_triple_count
            ):
                return False
            preview_graphs[target_graph] = candidate_preview
        return True
    def _staged_revisions_at_a_glance_markdown(
        self,
        bundle_summary: StagedGraphRevisionBundleSummary,
    ) -> list[str]:
        if bundle_summary.total_revisions == 0:
            return []
        lines = [
            f"- Decision: {bundle_summary.decision_headline}",
            f"- Rows: {bundle_summary.total_revisions}",
            (
                "- Apply status counts: "
                + self._staged_revisions_count_summary(
                    bundle_summary.apply_status_counts
                )
            ),
            (
                "- Review queue counts: "
                + self._staged_revisions_count_summary(
                    bundle_summary.next_action_queue_item_counts
                )
            ),
            (
                "- Changed graphs: "
                + self._staged_revisions_count_summary(
                    bundle_summary.changed_graph_counts
                )
            ),
        ]
        if bundle_summary.snapshot_evidence.rows:
            snapshot_state = (
                "complete"
                if bundle_summary.snapshot_evidence.complete
                else "incomplete"
            )
            lines.append(
                "- Snapshot evidence: "
                f"{snapshot_state} for "
                f"{bundle_summary.snapshot_evidence.total_revision_count} row(s)"
            )
        if bundle_summary.choose_one_groups:
            lines.append("- Choose-one groups:")
            for group in bundle_summary.choose_one_groups:
                rows = self._staged_revisions_row_list(group.row_indexes)
                labels = ", ".join(
                    label or iri
                    for label, iri in zip(
                        group.summaries,
                        group.revision_iris,
                        strict=True,
                    )
                )
                lines.append(
                    f"  - Rows {rows}: apply at most one ({labels})."
                )
        else:
            lines.append("- Choose-one groups: none")
        if bundle_summary.requires_recheck_after_each_apply:
            lines.append("- Sequencing: recheck sibling rows after each apply.")
        return lines
    def _staged_revisions_reviewer_decision_matrix_markdown(
        self,
        descriptions: list[StagedGraphRevisionDescription],
        summaries: list[StagedGraphRevisionExportSummary],
    ) -> list[str]:
        if not descriptions:
            return []
        lines: list[str] = []
        alternative_groups = self._staged_revisions_alternative_row_groups(
            summaries
        )
        for group in alternative_groups:
            rows = self._staged_revisions_row_list(group)
            lines.append(
                f"Rows {rows} are competing alternatives. Apply at most one "
                "before regenerating or rechecking the bundle."
            )
        alternative_row_indexes = {
            row_index for group in alternative_groups for row_index in group
        }
        if alternative_groups:
            lines.append("")
        lines.extend(
            [
                (
                    "| Row | Candidate | Suggested human action | Why | "
                    "Authored recommendation |"
                ),
                "|---:|---|---|---|---|",
            ]
        )
        for index, (description, summary) in enumerate(
            zip(descriptions, summaries, strict=True),
            start=1,
        ):
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(index),
                        self._markdown_table_cell(
                            description.summary or description.iri
                        ),
                        self._markdown_table_cell(
                            self._staged_revisions_human_action(
                                summary,
                                included_alternative_row=(
                                    index in alternative_row_indexes
                                ),
                            )
                        ),
                        self._markdown_table_cell(
                            self._staged_revisions_human_action_reason(
                                summary,
                                included_alternative_row=(
                                    index in alternative_row_indexes
                                ),
                            )
                        ),
                        self._markdown_table_cell(
                            summary.review_recommendation or "(none)"
                        ),
                    ]
                )
                + " |"
            )
        return lines
    @staticmethod
    def _staged_revisions_alternative_row_groups(
        summaries: list[StagedGraphRevisionExportSummary],
    ) -> list[list[int]]:
        row_by_iri = {
            summary.revision_iri: index
            for index, summary in enumerate(summaries, start=1)
        }
        grouped: list[list[int]] = []
        seen: set[tuple[int, ...]] = set()
        for index, summary in enumerate(summaries, start=1):
            target = summary.current_alternative_to or summary.alternative_to
            if target is None or target not in row_by_iri:
                continue
            group = tuple(sorted({index, row_by_iri[target]}))
            if group not in seen:
                seen.add(group)
                grouped.append(list(group))
        return grouped
    @staticmethod
    def _staged_revisions_row_list(rows: list[int]) -> str:
        values = [str(row) for row in rows]
        if len(values) <= 2:
            return " and ".join(values)
        return ", ".join(values[:-1]) + f", and {values[-1]}"
    @staticmethod
    def _staged_revisions_count_summary(counts: MappingABC[str, int]) -> str:
        if not counts:
            return "none"
        return ", ".join(f"{key}: {counts[key]}" for key in sorted(counts))
    @staticmethod
    def _staged_revisions_human_action(
        summary: StagedGraphRevisionExportSummary,
        *,
        included_alternative_row: bool = False,
    ) -> str:
        if (
            summary.next_action is not None
            and summary.next_action.action_type == "inspect_no_effective_change"
        ):
            return summary.next_action.action_label
        if summary.next_action is not None and summary.next_action.queue == (
            "repair_or_replace"
        ):
            return "Repair or discard"
        if summary.staged_validation_conforms is False:
            return "Repair before applying"
        if summary.apply_status == "validation_failed":
            return "Repair before applying"
        if summary.stale_resolution_state in {
            "stale_unresolved",
            "restaged_successor_stale_unresolved",
        }:
            return "Restage or replace"
        if summary.apply_status == "conflict":
            return "Restage or inspect conflict"
        if summary.stale_resolution_state in {
            "already_applied",
            "restaged_successor_already_applied",
        }:
            return "Inspect applied event"
        if summary.stale_resolution_state in {"noop", "restaged_successor_noop"}:
            return "Review no-op"
        if (
            included_alternative_row
            or summary.alternative_gate.semantic_review_required
            or summary.current_alternative_to is not None
            or summary.alternative_to is not None
        ):
            return "Choose only if this alternative is preferred"
        if summary.apply_decision == "review_then_apply":
            return "Apply after semantic review"
        if summary.next_action is not None:
            return summary.next_action.action_label
        return "Review before acting"
    @staticmethod
    def _staged_revisions_human_action_reason(
        summary: StagedGraphRevisionExportSummary,
        *,
        included_alternative_row: bool = False,
    ) -> str:
        diagnostic = summary.validation_diagnostic_headline.strip()
        if diagnostic and diagnostic != "none":
            return diagnostic
        if (
            summary.alternative_gate.semantic_review_required
            or summary.current_alternative_to is not None
            or summary.alternative_to is not None
        ):
            return summary.alternative_gate.note or "Competing alternative in this bundle."
        if included_alternative_row:
            return "Competing alternative in this bundle."
        if summary.apply_summary:
            return summary.apply_summary
        return summary.summary_recommendation
    def _staged_revisions_snapshot_evidence_summary(
        self,
        descriptions: list[StagedGraphRevisionDescription],
    ) -> StagedGraphRevisionSnapshotEvidenceSummary:
        history_graphs = self._expand_graphs(["history"])
        rows: list[StagedGraphRevisionSnapshotEvidenceRow] = []
        status_counts: dict[str, int] = {}
        incomplete_revision_iris: list[str] = []
        for index, description in enumerate(descriptions, start=1):
            evidence = self._revision_snapshot_evidence_status(
                description.iri,
                history_graphs,
            )
            completeness = self._snapshot_evidence_completeness_label(evidence)
            status_counts[evidence.status] = (
                status_counts.get(evidence.status, 0) + 1
            )
            if completeness != "complete":
                incomplete_revision_iris.append(description.iri)
            rows.append(
                StagedGraphRevisionSnapshotEvidenceRow(
                    row_index=index,
                    revision_iri=description.iri,
                    summary=description.summary,
                    status=evidence.status,
                    completeness=completeness,
                    rdf_snapshot_graph_roles=evidence.rdf_snapshot_graph_roles,
                    stored_snapshot_graph_roles=(
                        evidence.stored_snapshot_graph_roles
                    ),
                    exact_snapshot_graph_roles=evidence.exact_snapshot_graph_roles,
                    missing_snapshot_row_graph_roles=(
                        evidence.missing_snapshot_row_graph_roles
                    ),
                    orphan_snapshot_row_graph_roles=(
                        evidence.orphan_snapshot_row_graph_roles
                    ),
                    note=evidence.note,
                    suggested_next_actions=evidence.suggested_next_actions,
                )
            )
        return StagedGraphRevisionSnapshotEvidenceSummary(
            complete=not incomplete_revision_iris,
            total_revision_count=len(rows),
            incomplete_revision_iris=incomplete_revision_iris,
            status_counts=status_counts,
            rows=rows,
        )
    def _staged_revisions_snapshot_evidence_markdown(
        self,
        snapshot_evidence: StagedGraphRevisionSnapshotEvidenceSummary,
    ) -> list[str]:
        if not snapshot_evidence.rows:
            return []

        status_order = [
            "history_plus_snapshot_rows",
            "history_only_count_digest",
            "snapshot_rows_without_history",
            "history_missing",
        ]
        count_text = ", ".join(
            f"{status}: {snapshot_evidence.status_counts[status]}"
            for status in status_order
            if status in snapshot_evidence.status_counts
        )
        if snapshot_evidence.complete:
            exact_graph_roles = sorted(
                {
                    graph_role
                    for row in snapshot_evidence.rows
                    for graph_role in row.exact_snapshot_graph_roles
                }
            )
            return [
                (
                    "- Snapshot evidence complete for "
                    f"{snapshot_evidence.total_revision_count}/"
                    f"{snapshot_evidence.total_revision_count} revision row(s)."
                ),
                f"- Status counts: {count_text}",
                (
                    "- Exact rows available for graph role(s): "
                    f"{self._markdown_graph_role_list(exact_graph_roles)}"
                ),
            ]
        lines = [
            f"- Status counts: {count_text}",
            (
                "- Exact stale drift triples and applied diffs require "
                "`history_plus_snapshot_rows`; import companion revision "
                "snapshot JSON when rows remain history-only or partial."
            ),
            "",
            (
                "| # | Revision | Summary | Status | Completeness | RDF graphs | "
                "Stored rows | Exact rows | Missing rows | Orphan rows | "
                "Suggested next calls |"
            ),
            "|---:|---|---|---|---|---|---|---|---|---|---|",
        ]
        for row in snapshot_evidence.rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(row.row_index),
                        self._markdown_table_cell(f"`{row.revision_iri}`"),
                        self._markdown_table_cell(row.summary or row.revision_iri),
                        self._markdown_table_cell(row.status),
                        self._markdown_table_cell(row.completeness),
                        self._markdown_table_cell(
                            self._markdown_graph_role_list(
                                row.rdf_snapshot_graph_roles
                            )
                        ),
                        self._markdown_table_cell(
                            self._markdown_graph_role_list(
                                row.stored_snapshot_graph_roles
                            )
                        ),
                        self._markdown_table_cell(
                            self._markdown_graph_role_list(
                                row.exact_snapshot_graph_roles
                            )
                        ),
                        self._markdown_table_cell(
                            self._markdown_graph_role_list(
                                row.missing_snapshot_row_graph_roles
                            )
                        ),
                        self._markdown_table_cell(
                            self._markdown_graph_role_list(
                                row.orphan_snapshot_row_graph_roles
                            )
                        ),
                        self._markdown_table_cell(
                            "; ".join(
                                action.tool
                                for action in row.suggested_next_actions
                            )
                            or "(none)"
                        ),
                    ]
                )
                + " |"
        )
        return lines
    def _staged_revisions_count_basis_markdown(
        self,
        descriptions: list[StagedGraphRevisionDescription],
    ) -> list[str]:
        patch_rows: list[
            tuple[int, StagedGraphRevisionDescription, StagedGraphPatchDescription]
        ] = []
        count_bases: set[str] = set()
        changed_graphs: set[str] = set()
        for index, description in enumerate(descriptions, start=1):
            for patch in description.patches:
                if patch.target_graph is None:
                    continue
                patch_rows.append((index, description, patch))
                changed_graphs.add(patch.target_graph)
                if patch.count_basis is not None:
                    count_bases.add(patch.count_basis)

        if not patch_rows:
            return []
        if count_bases == {"target_graph_only"} and len(changed_graphs) <= 1:
            return []

        history_graphs = self._expand_graphs(["history"])
        snapshot_evidence_by_iri = {
            description.iri: self._revision_snapshot_evidence_status(
                description.iri,
                history_graphs,
            )
            for _, description, _ in patch_rows
        }
        snapshot_counts_by_iri = {
            description.iri: {
                snapshot.graph_role: snapshot.triple_count
                for snapshot in description.graph_snapshots
            }
            for _, description, _ in patch_rows
        }
        lines = [
            (
                "- Patch preview before/after counts use each row's "
                "`count_basis`. `ontology` and `shapes` previews include their "
                "immutable seed graphs; stored revision snapshots are "
                "role-local graph counts."
            ),
            (
                "- Compare preview counts with snapshot counts only after "
                "checking the basis and snapshot evidence for that graph."
            ),
            "",
            (
                "| # | Graph | Patch | Count basis | Staged before | "
                "Staged after | Snapshot count | Snapshot evidence |"
            ),
            "|---:|---|---:|---|---:|---:|---:|---|",
        ]
        for index, description, patch in patch_rows:
            graph_role = patch.target_graph or "unknown"
            snapshot_count = snapshot_counts_by_iri.get(description.iri, {}).get(
                graph_role
            )
            evidence = snapshot_evidence_by_iri[description.iri]
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(index),
                        self._markdown_table_cell(graph_role),
                        str(patch.sequence_index or ""),
                        self._markdown_table_cell(patch.count_basis or "unknown"),
                        self._markdown_optional_int_cell(
                            patch.before_triple_count
                        ),
                        self._markdown_optional_int_cell(patch.after_triple_count),
                        self._markdown_optional_int_cell(snapshot_count),
                        self._markdown_table_cell(
                            self._snapshot_evidence_graph_label(
                                evidence,
                                graph_role,
                            )
                        ),
                    ]
                )
                + " |"
            )
        return lines
    @staticmethod
    def _markdown_optional_int_cell(value: int | None) -> str:
        return "unknown" if value is None else str(value)
    @staticmethod
    def _staged_revisions_effective_recommendation(
        *,
        review_recommendation: str | None,
        stale_resolution_state: str | None,
        restaged_by: str | None,
        current_restaged_by: str | None,
        apply_status: str | None,
        apply_decision: str | None,
        apply_recommended_resolution: str | None,
        staged_validation_status: str,
        next_action: RevisionNextAction | None,
    ) -> str:
        if stale_resolution_state == "stale_handled_by_restage":
            successor_iri = current_restaged_by or restaged_by
            if successor_iri is not None:
                return (
                    "Handled by refreshed successor; follow Review Queues or "
                    f"inspect `{successor_iri}`."
            )
            return "Handled by refreshed successor; follow Review Queues."
        if (
            staged_validation_status == "failed"
            and next_action is not None
            and next_action.queue == "repair_or_replace"
            and apply_status == "conflict"
            and apply_decision == "restage_against_current_graph"
        ):
            return (
                "Stored staged-time validation failed; inspect validation "
                "diagnostics and stage a repaired or alternative proposal before "
                "restaging or applying this row."
            )
        if apply_recommended_resolution:
            return apply_recommended_resolution
        if review_recommendation:
            return review_recommendation
        return ""
    @staticmethod
    def _staged_revisions_effective_recommendation_source(
        *,
        review_recommendation: str | None,
        stale_resolution_state: str | None,
        apply_status: str | None,
        apply_decision: str | None,
        apply_recommended_resolution: str | None,
        staged_validation_status: str,
        next_action: RevisionNextAction | None,
    ) -> str:
        if stale_resolution_state == "stale_handled_by_restage":
            return "stale_resolution_redirect"
        if (
            staged_validation_status == "failed"
            and next_action is not None
            and next_action.queue == "repair_or_replace"
            and apply_status == "conflict"
            and apply_decision == "restage_against_current_graph"
        ):
            return "staged_validation_repair_route"
        if apply_recommended_resolution:
            return "apply_recommended_resolution"
        if review_recommendation:
            return "review_recommendation"
        return "none"
    @staticmethod
    def _staged_revisions_apply_recommendation_scope(
        *,
        stale_resolution_state: str | None,
        apply_recommended_resolution: str | None,
    ) -> str | None:
        if apply_recommended_resolution is None:
            return None
        if stale_resolution_state == "stale_handled_by_restage":
            return "prior_source_apply_check_context"
        return "current_apply_check"
    def _staged_revisions_review_queues_markdown(
        self,
        bundle_summary: StagedGraphRevisionBundleSummary,
    ) -> list[str]:
        next_action_labels = [
            ("Next action - apply after review", "apply_after_review"),
            ("Next action - restage after review", "restage_after_review"),
            ("Next action - repair or replace", "repair_or_replace"),
            ("Next action - inspect already applied", "inspect_already_applied"),
            ("Next action - informational", "informational"),
        ]
        queues = [
            ("Recommended review", bundle_summary.recommended_review_iris),
            (
                "Recommended mutation review",
                bundle_summary.recommended_mutation_review_iris,
            ),
            ("Mutation frontier", bundle_summary.mutation_frontier_iris),
            *(
                (label, bundle_summary.next_action_queue.get(queue, []))
                for label, queue in next_action_labels
            ),
            (
                "Apply/restage review",
                bundle_summary.recommended_apply_or_restage_review_iris,
            ),
            ("Repair review", bundle_summary.recommended_repair_review_iris),
            (
                "Applied inspection",
                bundle_summary.recommended_applied_inspection_iris,
            ),
            (
                "Sequential apply recheck candidates",
                bundle_summary.post_apply_recheck_revision_iris,
            ),
        ]
        if not any(iris for _, iris in queues):
            return []
        notes = [
            (
                "Queue values are returned row IRIs; read each row's "
                "`next_action.arguments` for the actual follow-up target. "
                "`Mutation frontier` lists deduped resolved targets for "
                "apply/restage/repair queues."
            )
        ]
        if bundle_summary.requires_recheck_after_each_apply:
            notes.append(
                "This bundle requires rechecking the remaining ready candidates "
                "after each apply."
            )
        return [
            *notes,
            "",
            *(
                f"- {label}: {self._markdown_iri_list(iris)}"
                for label, iris in queues
            ),
        ]
    def _staged_revisions_resolved_targets_markdown(
        self,
        bundle_summary: StagedGraphRevisionBundleSummary,
    ) -> list[str]:
        if not bundle_summary.next_action_queue_items:
            return []
        lines = [
            (
                "| Queue | Row | Action | Resolved target | Target kind | "
                "Row is target | Semantic risk | Alternative gate |"
            ),
            "|---|---|---|---|---|---|---|---|",
        ]
        for item in bundle_summary.next_action_queue_items:
            row = f"`{item.row_iri}`"
            target = (
                f"`{item.resolved_target_iri}`"
                if item.resolved_target_iri is not None
                else "(none)"
            )
            lines.append(
                "| "
                + " | ".join(
                    [
                        self._markdown_table_cell(item.queue),
                        self._markdown_table_cell(row),
                        self._markdown_table_cell(item.action_label),
                        self._markdown_table_cell(target),
                        self._markdown_table_cell(
                            item.resolved_target_record_kind or "(none)"
                        ),
                        str(item.row_is_target),
                        self._markdown_table_cell(
                            item.semantic_risk_level or "(none)"
                        ),
                        self._markdown_table_cell(
                            item.alternative_gate_status or "(none)"
                        ),
                    ]
                )
                + " |"
            )
        return lines
    def _staged_revisions_alternative_context_markdown(
        self,
        descriptions: list[StagedGraphRevisionDescription],
        revision_summaries: list[StagedGraphRevisionExportSummary],
    ) -> list[str]:
        index_by_iri = {
            description.iri: index
            for index, description in enumerate(descriptions, start=1)
        }
        label_by_iri = {
            description.iri: description.summary or description.iri
            for description in descriptions
        }

        def reference(iri: str) -> str:
            label = label_by_iri.get(iri)
            index = index_by_iri.get(iri)
            if index is None:
                return f"`{iri}`"
            return f"Revision {index}: {label} (`{iri}`)"

        lines: list[str] = []
        for index, summary in enumerate(revision_summaries, start=1):
            if (
                summary.alternative_to is None
                or summary.current_alternative_to is None
                or summary.current_alternative_to == summary.alternative_to
            ):
                continue
            label = summary.summary or summary.revision_iri
            lines.append(
                (
                    f"{index}. {label}: Stored alternative to "
                    f"{reference(summary.alternative_to)}; current alternative to "
                    f"{reference(summary.current_alternative_to)} after restage."
                )
            )
        return lines
    def _staged_description_validation_cell(
        self,
        description: StagedGraphRevisionDescription,
    ) -> str:
        if description.validation_conforms is None:
            return "unknown"
        result_count = (
            "unknown"
            if description.validation_result_count is None
            else str(description.validation_result_count)
        )
        return f"{description.validation_conforms} ({result_count} result(s))"
    def _staged_revision_linked_support_markdown(
        self,
        description: StagedGraphRevisionDescription,
    ) -> list[str]:
        sections = [
            ("Supporting observations", description.supporting_observations),
            ("Supporting claims", description.supporting_claims),
            ("Supporting patterns", description.supporting_patterns),
        ]
        lines: list[str] = []
        for label, resources in sections:
            if not resources:
                continue
            lines.append(f"- {label}:")
            for resource in resources:
                lines.append(f"  - {resource.label or resource.iri} (`{resource.iri}`)")
        if description.evidence:
            lines.append("- Evidence:")
            for resource in description.evidence:
                lines.extend(self._staged_revision_evidence_support_markdown(resource))
        return lines
    def _staged_revision_evidence_support_markdown(
        self,
        resource: ResourceSummary,
    ) -> list[str]:
        lookup_graphs = self._lookup_graphs(self._expand_graphs(["all"]))
        evidence = self._describe_evidence(
            resource.iri,
            self._evidence_detail_graphs(self._expand_graphs(["history"])),
            lookup_graphs,
        )
        label = evidence.label or resource.label or evidence.summary or resource.iri
        lines = [f"  - {label} (`{resource.iri}`)"]
        if evidence.summary and evidence.summary != label:
            lines.append(f"    - Summary: {evidence.summary}")
        for source in evidence.sources:
            lines.append(f"    - Source: `{source}`")
        for source_span in evidence.source_spans:
            lines.append(
                "    - Source span: "
                f"{self._source_span_description_markdown(source_span)}"
            )
        return lines
    @staticmethod
    def _source_span_description_markdown(
        source_span: SourceSpanDescription,
    ) -> str:
        label = (
            f"`{source_span.source_path}`"
            if source_span.source_path is not None
            else f"`{source_span.iri}`"
        )
        details: list[str] = []
        if source_span.source_section is not None:
            details.append(f'section "{source_span.source_section}"')
        line_label = DoxaBase._source_span_line_label(source_span)
        if line_label is not None:
            details.append(line_label)
        source_kind = source_span.source_kind_label or source_span.source_kind
        if source_kind is not None:
            details.append(f"kind {source_kind}")
        if not details:
            return label
        return f"{label} ({'; '.join(details)})"
    def _staged_revision_impact_markdown(
        self,
        impact: StagedRevisionImpact,
    ) -> list[str]:
        lines = [
            f"### {impact.impact_type.replace('_', ' ').title()}",
            "",
            f"- Severity: {impact.severity}",
            f"- Message: {impact.message}",
        ]
        if impact.changed_graph is not None:
            lines.append(f"- Changed graph: `{impact.changed_graph}`")
        if impact.subject is not None:
            lines.append(
                "- Subject: "
                f"{impact.subject.label or impact.subject.iri} (`{impact.subject.iri}`)"
            )
        if impact.predicate is not None:
            lines.append(
                "- Predicate: "
                f"{impact.predicate_label or impact.predicate} (`{impact.predicate}`)"
            )
        if impact.removed_values:
            lines.append(
                "- Removed values: "
                + ", ".join(
                    self._impact_markdown_value(value)
                    for value in impact.removed_values
                )
            )
        if impact.added_values:
            lines.append(
                "- Added values: "
                + ", ".join(
                    self._impact_markdown_value(value)
                    for value in impact.added_values
                )
            )
        for value in [*impact.removed_values, *impact.added_values]:
            if value.caveat is None:
                continue
            caveat_label = value.caveat.label or value.caveat.iri
            lines.append(f"- Caveat details for {caveat_label}:")
            if value.caveat.description is not None:
                lines.append(f"  - Description: {value.caveat.description}")
            if value.caveat.impact is not None:
                lines.append(f"  - Impact: {value.caveat.impact}")
            if value.caveat.severity is not None:
                lines.append(
                    "  - Severity: "
                    f"{value.caveat.severity.label or value.caveat.severity.iri}"
                    f" (`{value.caveat.severity.iri}`)"
                )
        related_sections = [
            ("Related observations", impact.related_observations),
            ("Related claims", impact.related_claims),
            ("Related patterns", impact.related_patterns),
            ("Related evidence", impact.related_evidence),
            ("Related revisions", impact.related_revisions),
        ]
        for label, resources in related_sections:
            if resources:
                lines.append(f"- {label}:")
                for resource in resources:
                    lines.append(
                        f"  - {resource.label or resource.iri} (`{resource.iri}`)"
                    )
        if impact.related_context_note is not None:
            lines.append(f"- Related context: {impact.related_context_note}")
        lines.append("")
        return lines
    def _impact_markdown_value(
        self,
        value: StagedRevisionImpactValue,
    ) -> str:
        if value.value_kind == "iri":
            return f"{value.value_label or value.value} (`{value.value}`)"
        return f"`{value.value}`"
    def _enrich_staged_validation_hints(
        self,
        diagnostics: list[ValidationDiagnostic],
        *,
        patches: list[StagedGraphPatchDescription],
        revision_has_support_metadata: bool,
    ) -> list[ValidationDiagnostic]:
        diagnostics = self._enrich_staged_row_semantics_validation_hints(
            diagnostics,
            patches=patches,
        )
        return self._enrich_staged_pattern_support_validation_hints(
            diagnostics,
            patches=patches,
            revision_has_support_metadata=revision_has_support_metadata,
        )
    def _enrich_staged_row_semantics_validation_hints(
        self,
        diagnostics: list[ValidationDiagnostic],
        *,
        patches: list[StagedGraphPatchDescription],
    ) -> list[ValidationDiagnostic]:
        if not diagnostics or not patches:
            return diagnostics
        row_semantics = self.expand_iri("rc:rowSemantics")
        max_count_component = PREFIXES["sh"] + "MaxCountConstraintComponent"
        focus_nodes = {
            diagnostic.focus_node
            for diagnostic in diagnostics
            if diagnostic.focus_node is not None
            and diagnostic.result_path == row_semantics
            and diagnostic.source_constraint_component == max_count_component
        }
        if not focus_nodes:
            return diagnostics

        added_values, removed_values, target_graphs = (
            self._staged_row_semantics_patch_value_context(
                patches,
                focus_nodes=focus_nodes,
            )
        )
        if not added_values and not removed_values:
            return diagnostics
        current_values = self._current_row_semantics_values(
            focus_nodes=focus_nodes,
            target_graphs=target_graphs,
        )
        enriched: list[ValidationDiagnostic] = []
        for diagnostic in diagnostics:
            if (
                diagnostic.focus_node is None
                or diagnostic.result_path != row_semantics
                or diagnostic.source_constraint_component != max_count_component
            ):
                enriched.append(diagnostic)
                continue
            hint = self._staged_row_semantics_max_count_hint(
                current_values=current_values.get(diagnostic.focus_node, set()),
                added_values=added_values.get(diagnostic.focus_node, set()),
                removed_values=removed_values.get(diagnostic.focus_node, set()),
            )
            enriched.append(replace(diagnostic, hint=hint or diagnostic.hint))
        return enriched
    def _staged_row_semantics_patch_value_context(
        self,
        patches: list[StagedGraphPatchDescription],
        *,
        focus_nodes: set[str],
    ) -> tuple[dict[str, set[str]], dict[str, set[str]], set[str]]:
        row_semantics = URIRef(self.expand_iri("rc:rowSemantics"))
        addition_operation = self.expand_iri("rc:AdditionPatch")
        removal_operation = self.expand_iri("rc:RemovalPatch")
        added_values: dict[str, set[str]] = {}
        removed_values: dict[str, set[str]] = {}
        target_graphs: set[str] = set()
        for patch in patches:
            try:
                target_graph = self._required_staged_patch_target_graph(patch)
                operation = self._required_staged_patch_field(
                    patch,
                    "operation",
                    patch.operation,
                )
                patch_graph = self._parse_staged_patch_description(patch)
            except DoxaBaseError:
                continue
            target_graphs.add(target_graph)
            if operation == addition_operation:
                value_bucket = added_values
            elif operation == removal_operation:
                value_bucket = removed_values
            else:
                continue
            for subject, _, value in patch_graph.triples((None, row_semantics, None)):
                subject_iri = str(subject)
                if subject_iri not in focus_nodes:
                    continue
                value_bucket.setdefault(subject_iri, set()).add(str(value))
        return added_values, removed_values, target_graphs
    def _current_row_semantics_values(
        self,
        *,
        focus_nodes: set[str],
        target_graphs: set[str],
    ) -> dict[str, set[str]]:
        row_semantics = URIRef(self.expand_iri("rc:rowSemantics"))
        values_by_focus: dict[str, set[str]] = {focus: set() for focus in focus_nodes}
        for target_graph in sorted(target_graphs):
            try:
                current_graph = self.to_graph([target_graph])
            except DoxaBaseError:
                continue
            for focus_node in focus_nodes:
                values_by_focus[focus_node].update(
                    str(value)
                    for value in current_graph.objects(
                        URIRef(focus_node),
                        row_semantics,
                    )
                )
        return values_by_focus
    def _staged_row_semantics_max_count_hint(
        self,
        *,
        current_values: set[str],
        added_values: set[str],
        removed_values: set[str],
    ) -> str | None:
        if current_values and added_values:
            return (
                "rc:rowSemantics allows one value; the current graph already "
                f"has {self._compact_value_list(current_values)} and this "
                f"staged patch adds {self._compact_value_list(added_values)}. "
                "Choose the intended row framing and use a removal+addition "
                "patch or stage_map_assertion_change replacement if the staged "
                "value should replace the current value."
            )
        if added_values:
            return (
                "rc:rowSemantics allows one value; this staged patch adds "
                f"{self._compact_value_list(added_values)}, but the candidate "
                "graph has multiple rowSemantics values. Choose one row "
                "framing and use a removal+addition patch or "
                "stage_map_assertion_change replacement when changing an "
                "existing value."
            )
        if current_values and removed_values:
            return (
                "rc:rowSemantics allows one value; the current graph has "
                f"{self._compact_value_list(current_values)} and the staged "
                f"patch removes {self._compact_value_list(removed_values)}, "
                "but the candidate graph still has multiple rowSemantics "
                "values. Choose one row framing and repair the staged patch."
            )
        return None
    def _compact_value_list(self, values: Iterable[str]) -> str:
        compact_values = [
            self._compact_iri(value) or self._local_name(value) or value
            for value in sorted(values)
        ]
        return ", ".join(compact_values)
    def _subjects(self, graphs: list[str], predicate: str, object_value: str) -> list[str]:
        graph_filter, params = self._graph_filter(graphs, alias="q")
        return [
            row["subject"]
            for row in self._conn.execute(
                f"""
                SELECT DISTINCT q.subject
                FROM quads q
                WHERE q.predicate = ?
                  AND q.object = ?
                  {graph_filter}
                ORDER BY q.subject
                """,
                [self.expand_iri(predicate), object_value, *params],
            )
        ]
    def _first_subject(
        self,
        graphs: list[str],
        predicate: str,
        object_value: str,
    ) -> str | None:
        subjects = self._subjects(graphs, predicate, object_value)
        return subjects[0] if subjects else None
    def _staged_patch_sort_key(
        self,
        patch: StagedGraphPatchDescription,
    ) -> tuple[int, int, str, str]:
        if patch.sequence_index is not None:
            return (0, patch.sequence_index, patch.target_graph or "", patch.iri)
        shared_role = self.expand_iri("rc:SharedContextPatch")
        role_rank = 0 if patch.patch_role == shared_role else 1
        return (1, role_rank, patch.target_graph or "", patch.iri)
