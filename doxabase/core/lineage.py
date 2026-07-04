"""Revision lineage, resource revisions, graph versions.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via LineageMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class LineageMixin:
    def list_graph_versions(
        self,
        graph_role: str,
        *,
        graph: str | None = "history",
        exact_only: bool = False,
        include_current: bool = True,
        include_apply_checks: bool = False,
        drift_detail: TypingLiteral["summary", "exact"] = "summary",
        record_kind: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> GraphVersionList:
        if graph_role not in self._known_graph_names():
            raise DoxaBaseError(f"Unknown graph role: {graph_role}")
        self._ensure_non_negative("limit", limit)
        self._ensure_non_negative("offset", offset)

        revision_list = self.list_graph_revisions(
            graph=graph,
            record_kind=record_kind,
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,
            limit=1_000_000,
        )
        revisions = revision_list.revisions
        queue_item_by_row = {
            item.row_iri: item for item in revision_list.next_action_queue_items
        }
        versions: list[GraphVersionListItem] = []
        for revision in revisions:
            snapshot = self._graph_version_snapshot_for_revision(
                revision,
                graph_role,
                graph=graph,
                include_apply_checks=include_apply_checks,
                next_action_queue_item=queue_item_by_row.get(revision.iri),
            )
            if snapshot is None:
                continue
            if exact_only and not snapshot.exact_snapshot_available:
                continue
            versions.append(snapshot)

        versions.sort(
            key=lambda item: (
                item.created_at or "",
                item.stored_at or "",
                item.summary or "",
                item.revision_iri,
            ),
            reverse=True,
        )
        sliced_versions = versions[offset : offset + limit]
        current_graph = (
            GraphSnapshotDescription(
                graph_role=graph_role,
                triple_count=self.triple_count(graph_role),
                content_digest=self._graph_content_digest(graph_role),
            )
            if include_current
            else None
        )
        return GraphVersionList(
            graph_role=graph_role,
            graph=graph,
            exact_only=exact_only,
            include_current=include_current,
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,
            record_kind=record_kind,
            limit=limit,
            offset=offset,
            count=len(versions),
            total_count=len(versions),
            returned_count=len(sliced_versions),
            current_graph=current_graph,
            snapshot_evidence_status_counts=self._graph_version_status_counts(
                versions,
            ),
            exact_snapshot_available_count=sum(
                1 for version in versions if version.exact_snapshot_available
            ),
            versions=sliced_versions,
            note=(
                "Graph versions are stored revision snapshots, not a temporal "
                "checkout engine. Staged revision snapshots are before-states; "
                "applied revision snapshots are after-states."
            ),
        )
    def describe_graph_version_diff(
        self,
        graph_role: str,
        before_revision_iri: str,
        *,
        after_revision_iri: str | None = None,
        compare_to_current: bool = True,
        graph: str | None = "history",
        include_triples: bool = False,
        max_triples: int = 500,
    ) -> GraphVersionDiffDescription:
        if graph_role not in self._known_graph_names():
            raise DoxaBaseError(f"Unknown graph role: {graph_role}")
        if max_triples < 1:
            raise DoxaBaseError("max_triples must be at least 1")
        effective_compare_to_current = after_revision_iri is None and compare_to_current
        if after_revision_iri is None and not effective_compare_to_current:
            raise DoxaBaseError(
                "after_revision_iri is required when compare_to_current is False"
            )

        before_snapshot = self.describe_revision_graph_snapshot(
            before_revision_iri,
            graph_role,
            graph=graph,
            include_triples=False,
        )
        before_rows: set[GraphStorageRow] | None = None
        after_rows: set[GraphStorageRow] | None = None
        after_snapshot: RevisionGraphSnapshotDescription | None = None
        current_graph: GraphSnapshotDescription | None = None
        after_triple_count: int | None
        after_content_digest: str | None
        after_target_kind: str

        if before_snapshot.exact_snapshot_available:
            before_rows = set(
                self._graph_snapshot_storage_rows(
                    before_snapshot.revision_iri,
                    graph_role,
                )
            )

        if after_revision_iri is None:
            after_target_kind = "current_graph"
            current_graph = GraphSnapshotDescription(
                graph_role=graph_role,
                triple_count=self.triple_count(graph_role),
                content_digest=self._graph_content_digest(graph_role),
            )
            after_triple_count = current_graph.triple_count
            after_content_digest = current_graph.content_digest
            after_rows = set(self._graph_storage_rows(graph_role))
        else:
            after_target_kind = "stored_revision_snapshot"
            after_snapshot = self.describe_revision_graph_snapshot(
                after_revision_iri,
                graph_role,
                graph=graph,
                include_triples=False,
            )
            after_triple_count = after_snapshot.triple_count
            after_content_digest = after_snapshot.content_digest
            if after_snapshot.exact_snapshot_available:
                after_rows = set(
                    self._graph_snapshot_storage_rows(
                        after_snapshot.revision_iri,
                        graph_role,
                    )
                )

        exact_available = before_rows is not None and after_rows is not None
        triples_added: list[GraphTripleDescription] = []
        triples_removed: list[GraphTripleDescription] = []
        triples_added_count: int | None = None
        triples_removed_count: int | None = None
        triples_added_truncated = False
        triples_removed_truncated = False
        exact_included = False
        changed_resource_count: int | None = None
        changed_resources_returned_count = 0
        changed_resources_omitted_count: int | None = None
        changed_resources: list[ChangedGraphResourceSummary] = []
        changed_resource_suggested_next_actions: list[SuggestedNextAction] = []
        before_patch_terms: _StagedRevisionDriftTerms | None = None
        before_source_revision_iri: str | None = None

        if self._graph_revision_record_kind_for_iri(before_snapshot.revision_iri) == (
            "staged_patch"
        ):
            try:
                before_staged = self.describe_staged_revision(
                    before_snapshot.revision_iri,
                    graph=graph,
                )
            except DoxaBaseError:
                before_staged = None
            if before_staged is not None:
                before_patch_terms = self._staged_revision_patch_terms_by_graph(
                    before_staged
                ).get(graph_role)
                before_source_revision_iri = before_staged.iri

        if exact_available:
            added_rows = self._sort_graph_storage_rows(after_rows - before_rows)
            removed_rows = self._sort_graph_storage_rows(before_rows - after_rows)
            triples_added_count = len(added_rows)
            triples_removed_count = len(removed_rows)
            added_descriptions = [
                self._graph_triple_description(row) for row in added_rows
            ]
            removed_descriptions = [
                self._graph_triple_description(row) for row in removed_rows
            ]
            (
                changed_resource_count,
                changed_resources_returned_count,
                changed_resources_omitted_count,
                changed_resources,
                changed_resource_suggested_next_actions,
            ) = self._changed_graph_resource_summary(
                triples_added=added_descriptions,
                triples_removed=removed_descriptions,
                patch_terms=before_patch_terms,
                source_revision_iri=before_source_revision_iri,
            )
            if include_triples:
                exact_included = True
                triples_added_truncated = triples_added_count > max_triples
                triples_removed_truncated = triples_removed_count > max_triples
                triples_added = added_descriptions[:max_triples]
                triples_removed = removed_descriptions[:max_triples]
                note = (
                    "Exact graph-version changed triples are included from "
                    "stored snapshot rows and the selected after target."
                )
                if triples_added_truncated or triples_removed_truncated:
                    note = (
                        "Exact graph-version changed triples are available and "
                        "included up to max_triples per added/removed array."
                    )
            else:
                triples_added_truncated = triples_added_count > 0
                triples_removed_truncated = triples_removed_count > 0
                note = (
                    "Exact graph-version changed triples are available but "
                    "omitted; call describe_graph_version_diff(..., "
                    "include_triples=True) to include arrays."
                )
        else:
            note = (
                "Exact graph-version changed triples are unavailable because "
                "one or both comparison points lack stored snapshot rows."
            )
            if after_target_kind == "current_graph":
                note = (
                    "Exact graph-version changed triples are unavailable "
                    "because the before revision lacks stored snapshot rows."
                )

        count_delta = (
            after_triple_count - before_snapshot.triple_count
            if after_triple_count is not None
            and before_snapshot.triple_count is not None
            else None
        )
        digest_changed = (
            after_content_digest != before_snapshot.content_digest
            if after_content_digest is not None
            and before_snapshot.content_digest is not None
            else None
        )
        revision_items = self.list_graph_revisions(
            graph=graph,
            include_apply_checks=True,
            drift_detail="summary",
            limit=1_000_000,
        ).revisions
        revision_by_iri = {item.iri: item for item in revision_items}
        before_revision_context = self._graph_version_revision_context(
            revision_by_iri.get(before_snapshot.revision_iri)
        )
        after_revision_context = (
            self._graph_version_revision_context(
                revision_by_iri.get(after_snapshot.revision_iri)
            )
            if after_snapshot is not None
            else None
        )
        related_revision_iris = self._graph_version_diff_related_revision_iris(
            before_revision_context,
            after_revision_context,
        )
        suggested_next_actions = self._with_revision_snapshot_evidence_actions(
            self._graph_version_diff_suggested_actions(
                graph_role=graph_role,
                before_revision_iri=before_snapshot.revision_iri,
                after_revision_iri=(
                    after_snapshot.revision_iri
                    if after_snapshot is not None
                    else None
                ),
                compare_to_current=effective_compare_to_current,
                exact_available=exact_available,
                include_triples=include_triples,
                has_changes=bool(triples_added_count or triples_removed_count),
                before_revision_context=before_revision_context,
                after_revision_context=after_revision_context,
            ),
            before_snapshot.snapshot_evidence,
            after_snapshot.snapshot_evidence if after_snapshot is not None else None,
        )
        return GraphVersionDiffDescription(
            graph_role=graph_role,
            graph=graph,
            before_revision_iri=before_snapshot.revision_iri,
            after_revision_iri=(
                after_snapshot.revision_iri if after_snapshot is not None else None
            ),
            compare_to_current=effective_compare_to_current,
            after_target_kind=after_target_kind,
            before_revision_context=before_revision_context,
            after_revision_context=after_revision_context,
            related_revision_iris=related_revision_iris,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            current_graph=current_graph,
            count_basis="target_graph_only",
            before_triple_count=before_snapshot.triple_count,
            after_triple_count=after_triple_count,
            count_delta=count_delta,
            before_content_digest=before_snapshot.content_digest,
            after_content_digest=after_content_digest,
            digest_changed=digest_changed,
            exact_changed_triples_available=exact_available,
            exact_changed_triples_included=exact_included,
            triples_added_count=triples_added_count,
            triples_removed_count=triples_removed_count,
            triples_added_truncated=triples_added_truncated,
            triples_removed_truncated=triples_removed_truncated,
            max_triples=max_triples,
            changed_resource_count=changed_resource_count,
            changed_resources_returned_count=changed_resources_returned_count,
            changed_resources_omitted_count=changed_resources_omitted_count,
            changed_resources=changed_resources,
            changed_resource_suggested_next_actions=(
                changed_resource_suggested_next_actions
            ),
            triples_added=triples_added,
            triples_removed=triples_removed,
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[
                action.call for action in suggested_next_actions
            ],
            note=note,
        )
    @staticmethod
    def _graph_version_included_graphs(
        revision: GraphRevisionListItem,
    ) -> list[str]:
        return list(
            dict.fromkeys(
                [
                    *revision.changed_graphs,
                    *revision.snapshot_evidence.rdf_snapshot_graph_roles,
                    *revision.snapshot_evidence.stored_snapshot_graph_roles,
                ]
            )
        )
    @staticmethod
    def _graph_version_status_counts(
        versions: Iterable[GraphVersionListItem],
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for version in versions:
            status = version.snapshot_evidence_status
            counts[status] = counts.get(status, 0) + 1
        return counts
    def _graph_version_revision_context(
        self,
        revision: GraphRevisionListItem | None,
    ) -> GraphVersionRevisionContext | None:
        if revision is None:
            return None
        related_revision_iris = list(
            dict.fromkeys(
                iri
                for iri in (
                    revision.applies_staged_revision,
                    revision.applied_by,
                    revision.restaged_from,
                    revision.restaged_by,
                    revision.current_restaged_by,
                )
                if iri is not None
            )
        )
        return GraphVersionRevisionContext(
            revision_iri=revision.iri,
            record_kind=revision.record_kind,
            snapshot_semantics=self._graph_version_snapshot_semantics(revision),
            summary=revision.summary,
            application_status=revision.application_status,
            application_decision=revision.application_decision,
            staged_validation_status=revision.staged_validation_status,
            is_current_staged_work=revision.is_current_staged_work,
            not_current_staged_work_reason=(
                revision.not_current_staged_work_reason
            ),
            review_resolution=revision.review_resolution,
            applies_staged_revision=revision.applies_staged_revision,
            applied_by=revision.applied_by,
            restaged_from=revision.restaged_from,
            restaged_by=revision.restaged_by,
            current_restaged_by=revision.current_restaged_by,
            alternative_gate_status=revision.alternative_gate.status,
            alternative_semantic_review_required=(
                revision.alternative_gate.semantic_review_required
            ),
            alternative_applied_source_iri=(
                revision.alternative_gate.applied_source_iri
            ),
            alternative_applied_revision_iri=(
                revision.alternative_gate.applied_revision_iri
            ),
            related_revision_iris=related_revision_iris,
        )
    @staticmethod
    def _graph_version_diff_related_revision_iris(
        before_revision_context: GraphVersionRevisionContext | None,
        after_revision_context: GraphVersionRevisionContext | None,
    ) -> list[str]:
        values: list[str] = []
        for context in (before_revision_context, after_revision_context):
            if context is None:
                continue
            values.extend(context.related_revision_iris)
        return list(dict.fromkeys(values))
    def _graph_version_diff_suggested_actions(
        self,
        *,
        graph_role: str,
        before_revision_iri: str,
        after_revision_iri: str | None,
        compare_to_current: bool,
        exact_available: bool,
        include_triples: bool,
        has_changes: bool,
        before_revision_context: GraphVersionRevisionContext | None,
        after_revision_context: GraphVersionRevisionContext | None,
    ) -> list[SuggestedNextAction]:
        actions = [
            SuggestedNextAction(
                action_label="Inspect before snapshot",
                tool_name="describe_revision_graph_snapshot",
                mcp_tool_name="doxabase.describe_revision_graph_snapshot",
                arguments={
                    "iri": before_revision_iri,
                    "graph_role": graph_role,
                },
                reason=(
                    "Inspect the stored before snapshot metadata or exact "
                    "triples for this graph role."
                ),
                call=self._suggested_call_string(
                    "describe_revision_graph_snapshot",
                    {
                        "iri": before_revision_iri,
                        "graph_role": graph_role,
                    },
                ),
            )
        ]
        if after_revision_iri is not None:
            actions.append(
                SuggestedNextAction(
                    action_label="Inspect after snapshot",
                    tool_name="describe_revision_graph_snapshot",
                    mcp_tool_name="doxabase.describe_revision_graph_snapshot",
                    arguments={
                        "iri": after_revision_iri,
                        "graph_role": graph_role,
                    },
                    reason=(
                        "Inspect the stored after snapshot metadata or exact "
                        "triples for this graph role."
                    ),
                    call=self._suggested_call_string(
                        "describe_revision_graph_snapshot",
                        {
                            "iri": after_revision_iri,
                            "graph_role": graph_role,
                        },
                    ),
                )
            )
        contexts = [
            ("before", before_revision_context),
            ("after", after_revision_context),
        ]
        seen_lineage_iris: set[str] = set()
        for label, context in contexts:
            if context is None or context.revision_iri in seen_lineage_iris:
                continue
            seen_lineage_iris.add(context.revision_iri)
            actions.append(
                SuggestedNextAction(
                    action_label=f"Trace {label} revision lineage",
                    tool_name="describe_revision_lineage",
                    mcp_tool_name="doxabase.describe_revision_lineage",
                    arguments={"iri": context.revision_iri},
                    reason=(
                        "Inspect staged/applied/restaged lineage before "
                        "using this graph-version diff as recovery context."
                    ),
                    call=self._suggested_call_string(
                        "describe_revision_lineage",
                        {"iri": context.revision_iri},
                    ),
                )
            )
        seen_applied_diff_iris: set[str] = set()
        for label, context in contexts:
            if (
                context is None
                or context.record_kind != "applied_event"
                or context.revision_iri in seen_applied_diff_iris
            ):
                continue
            seen_applied_diff_iris.add(context.revision_iri)
            actions.append(
                SuggestedNextAction(
                    action_label=f"Inspect {label} applied diff",
                    tool_name="describe_applied_revision_diff",
                    mcp_tool_name="doxabase.describe_applied_revision_diff",
                    arguments={"iri": context.revision_iri},
                    reason=(
                        "This comparison point is an applied revision event; "
                        "inspect its stored before/after diff to recover the "
                        "revision story behind the graph-version delta."
                    ),
                    call=self._suggested_call_string(
                        "describe_applied_revision_diff",
                        {"iri": context.revision_iri},
                    ),
                )
            )
        if exact_available and has_changes and not include_triples:
            arguments: dict[str, Any] = {
                "graph_role": graph_role,
                "before_revision_iri": before_revision_iri,
                "include_triples": True,
            }
            if after_revision_iri is not None:
                arguments["after_revision_iri"] = after_revision_iri
            elif compare_to_current:
                arguments["compare_to_current"] = True
            actions.append(
                SuggestedNextAction(
                    action_label="Include changed triples",
                    tool_name="describe_graph_version_diff",
                    mcp_tool_name="doxabase.describe_graph_version_diff",
                    arguments=arguments,
                    reason=(
                        "Exact changed triples are available; include them "
                        "when the diff content is safe and useful to inspect."
                    ),
                    call=self._suggested_call_string(
                        "describe_graph_version_diff",
                        arguments,
                    ),
                )
            )
        return actions
    def describe_revision_lineage(
        self,
        iri: str,
        *,
        graph: str | None = "history",
        include_apply_checks: bool = True,
        drift_detail: TypingLiteral["summary", "exact"] = "summary",
    ) -> RevisionLineageDescription:
        revision_iri = self._required_iri("iri", iri)
        listing = self.list_graph_revisions(
            graph=graph,
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,
            limit=1_000_000,
        )
        by_iri = {item.iri: item for item in listing.revisions}
        selected = by_iri.get(revision_iri)
        if selected is None:
            raise DoxaBaseError(
                f"Graph revision '{iri}' was not found in "
                f"{graph if graph is not None else 'all graphs'}"
                f"{self._missing_revision_snapshot_storage_hint(revision_iri)}"
            )

        seed: GraphRevisionListItem | None = selected
        warnings: list[str] = []
        if selected.record_kind == "applied_event":
            if selected.applies_staged_revision is None:
                seed = None
                warnings.append(
                    f"Applied revision event '{selected.iri}' does not name a "
                    "staged source revision."
                )
            elif selected.applies_staged_revision in by_iri:
                seed = by_iri[selected.applies_staged_revision]
            else:
                seed = None
                warnings.append(
                    f"Applied revision event '{selected.iri}' points to "
                    "missing staged source "
                    f"'{selected.applies_staged_revision}'."
                )

        if selected.applied_by is not None and selected.applied_by not in by_iri:
            warnings.append(
                f"Staged revision '{selected.iri}' points to missing applied "
                f"event '{selected.applied_by}'."
            )

        restage_chain: list[GraphRevisionListItem] = []
        if seed is not None:
            restage_chain, chain_warnings = self._revision_lineage_restage_chain(
                seed,
                by_iri,
            )
            warnings.extend(chain_warnings)
        current_staged_revision = next(
            (
                item
                for item in reversed(restage_chain)
                if item.is_current_staged_work
            ),
            None,
        )
        direct_applied_revision, direct_staged_revision = (
            self._revision_lineage_direct_pair(selected, by_iri)
        )
        chain_applied_source = self._revision_lineage_applied_source(
            selected,
            restage_chain,
        )
        chain_applied_revision = (
            by_iri.get(chain_applied_source.applied_by)
            if chain_applied_source is not None
            and chain_applied_source.applied_by is not None
            else None
        )
        applied_revision = (
            direct_applied_revision
            or chain_applied_revision
            or (selected if selected.record_kind == "applied_event" else None)
        )
        staged_revision = direct_staged_revision or (
            seed if seed is not None and seed.record_kind == "staged_patch" else None
        )
        paired_revision = None
        if selected.record_kind == "applied_event":
            paired_revision = direct_staged_revision
        elif selected.applied_by is not None:
            paired_revision = direct_applied_revision

        if applied_revision is not None:
            latest_revision = applied_revision
        elif current_staged_revision is not None:
            latest_revision = current_staged_revision
        else:
            latest_revision = restage_chain[-1] if restage_chain else selected
        next_action = latest_revision.next_action
        suggested_next_actions = list(latest_revision.suggested_next_actions)
        if not suggested_next_actions:
            derived_action = self._suggested_action_from_revision_next_action(
                next_action,
            )
            if derived_action is not None:
                suggested_next_actions = [derived_action]
        if (
            chain_applied_source is not None
            and chain_applied_source.iri != selected.iri
        ):
            arguments = {"iri": chain_applied_source.iri}
            if not any(
                action.tool_name == "describe_staged_revision"
                and action.arguments == arguments
                for action in suggested_next_actions
            ):
                suggested_next_actions.append(
                    SuggestedNextAction(
                        action_label="Inspect applied staged source",
                        tool_name="describe_staged_revision",
                        mcp_tool_name="doxabase.describe_staged_revision",
                        arguments=arguments,
                        reason=(
                            "Inspect the staged successor that was actually "
                            "applied for this lineage, rather than inferring it "
                            "from the restage chain."
                        ),
                        call=self._suggested_call_string(
                            "describe_staged_revision",
                            arguments,
                        ),
                    )
                )
        suggested_next_actions = self._with_revision_snapshot_evidence_actions(
            suggested_next_actions,
            selected.snapshot_evidence,
            paired_revision.snapshot_evidence if paired_revision is not None else None,
            latest_revision.snapshot_evidence,
            (
                current_staged_revision.snapshot_evidence
                if current_staged_revision is not None
                else None
            ),
            *(item.snapshot_evidence for item in restage_chain),
        )
        snapshot_next_action = self._snapshot_evidence_completion_next_action(
            suggested_next_actions
        )
        if snapshot_next_action is not None:
            next_action = snapshot_next_action
        next_action_queue_item = self._revision_next_action_queue_item(
            row_iri=selected.iri,
            next_action=next_action,
            record_kind=selected.record_kind,
            application_status=selected.application_status,
            application_decision=selected.application_decision,
            stale_resolution_state=selected.stale_resolution_state,
            staged_validation_status=selected.staged_validation_status,
            semantic_risk_level=selected.application_semantic_risk_level,
            semantic_risk_reasons=selected.application_semantic_risk_reasons,
            alternative_gate=selected.alternative_gate,
        )
        if next_action_queue_item is not None:
            next_action_queue_item = (
                self._revision_next_action_queue_items_with_alternative_sets(
                    [next_action_queue_item],
                    (
                        (
                            item.iri,
                            item.alternative_to,
                            item.current_alternative_to,
                        )
                        for item in listing.revisions
                    ),
                )[0]
            )
        alternative_revision_iris = self._revision_lineage_alternative_revision_iris(
            selected=selected,
            restage_chain=restage_chain,
            by_iri=by_iri,
        )
        warnings.extend(
            self._revision_lineage_snapshot_warnings(
                selected=selected,
                paired=paired_revision,
                latest=latest_revision,
                current_staged_revision=current_staged_revision,
                restage_chain=restage_chain,
            )
        )
        return RevisionLineageDescription(
            selected_revision=selected,
            selected_revision_iri=selected.iri,
            selected_role=self._revision_lineage_role(selected),
            paired_revision=paired_revision,
            paired_revision_iri=(
                paired_revision.iri if paired_revision is not None else None
            ),
            paired_role=(
                self._revision_lineage_role(paired_revision)
                if paired_revision is not None
                else None
            ),
            applied_revision_iri=(
                applied_revision.iri if applied_revision is not None else None
            ),
            staged_revision_iri=(
                staged_revision.iri if staged_revision is not None else None
            ),
            applied_source_revision_iri=(
                chain_applied_source.iri
                if chain_applied_source is not None
                else None
            ),
            current_staged_revision_iri=(
                current_staged_revision.iri
                if current_staged_revision is not None
                else None
            ),
            current_revision_iri=(
                current_staged_revision.iri
                if current_staged_revision is not None
                else None
            ),
            latest_revision_iri=latest_revision.iri,
            latest_role=self._revision_lineage_role(latest_revision),
            restage_chain=restage_chain,
            restage_chain_iris=[item.iri for item in restage_chain],
            alternative_revision_iris=alternative_revision_iris,
            related_revision_iris=self._revision_lineage_related_revision_iris(
                selected=selected,
                paired=paired_revision,
                restage_chain=restage_chain,
                current_staged_revision=current_staged_revision,
                applied_revision=applied_revision,
                staged_revision=staged_revision,
                latest_revision=latest_revision,
                alternative_revision_iris=alternative_revision_iris,
                alternative_revisions=[
                    by_iri[iri]
                    for iri in alternative_revision_iris
                    if iri in by_iri
                ],
                by_iri=by_iri,
            ),
            next_action=next_action,
            next_action_queue_item=next_action_queue_item,
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[
                action.call for action in suggested_next_actions
            ],
            warnings=warnings,
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,
        )
    @staticmethod
    def _revision_lineage_direct_pair(
        selected: GraphRevisionListItem,
        by_iri: dict[str, GraphRevisionListItem],
    ) -> tuple[GraphRevisionListItem | None, GraphRevisionListItem | None]:
        if selected.record_kind == "applied_event":
            staged = (
                by_iri.get(selected.applies_staged_revision)
                if selected.applies_staged_revision is not None
                else None
            )
            return selected, staged
        if selected.applied_by is not None:
            return by_iri.get(selected.applied_by), selected
        if selected.record_kind == "staged_patch":
            return None, selected
        return None, None
    @staticmethod
    def _revision_lineage_applied_source(
        selected: GraphRevisionListItem,
        restage_chain: list[GraphRevisionListItem],
    ) -> GraphRevisionListItem | None:
        if selected.record_kind == "applied_event":
            for item in restage_chain:
                if item.iri == selected.applies_staged_revision:
                    return item
            return None
        for item in reversed(restage_chain):
            if item.applied_by is not None:
                return item
        return selected if selected.applied_by is not None else None
    @staticmethod
    def _revision_lineage_role(item: GraphRevisionListItem) -> str:
        if item.record_kind == "applied_event":
            return "applied_event"
        if item.applied_by is not None:
            return "applied_source"
        if item.current_restaged_by is not None:
            return "restaged_source"
        if item.is_current_staged_work:
            return "current_staged_revision"
        if item.record_kind == "staged_patch":
            return "staged_revision"
        return item.record_kind
    @staticmethod
    def _revision_lineage_related_revision_iris(
        *,
        selected: GraphRevisionListItem,
        paired: GraphRevisionListItem | None,
        restage_chain: list[GraphRevisionListItem],
        current_staged_revision: GraphRevisionListItem | None,
        applied_revision: GraphRevisionListItem | None,
        staged_revision: GraphRevisionListItem | None,
        latest_revision: GraphRevisionListItem,
        alternative_revision_iris: list[str],
        alternative_revisions: list[GraphRevisionListItem],
        by_iri: dict[str, GraphRevisionListItem],
    ) -> list[str]:
        values: list[str | None] = [
            selected.iri,
            paired.iri if paired is not None else None,
            *(item.iri for item in restage_chain),
            current_staged_revision.iri
            if current_staged_revision is not None
            else None,
            applied_revision.iri if applied_revision is not None else None,
            staged_revision.iri if staged_revision is not None else None,
            latest_revision.iri,
            *alternative_revision_iris,
        ]
        for item in [selected, *restage_chain]:
            values.extend(
                [
                    item.applied_by,
                    item.applies_staged_revision,
                    item.restaged_from,
                    item.restaged_by,
                    item.current_restaged_by,
                    item.alternative_to,
                    item.current_alternative_to,
                ]
            )
        for item in alternative_revisions:
            values.extend(
                [
                    item.applied_by,
                    item.applies_staged_revision,
                    item.restaged_from,
                    item.restaged_by,
                    item.current_restaged_by,
                    item.alternative_to,
                    item.current_alternative_to,
                ]
            )
        for item in [selected, *restage_chain, *alternative_revisions]:
            for successor in DoxaBase._revision_lineage_visible_restage_successors(
                    item,
                    by_iri,
            ):
                values.extend(
                    [
                        successor.iri,
                        successor.applied_by,
                        successor.applies_staged_revision,
                        successor.restaged_from,
                        successor.restaged_by,
                        successor.current_restaged_by,
                        successor.alternative_to,
                        successor.current_alternative_to,
                    ]
                )
        return [value for value in dict.fromkeys(values) if value is not None]
    @staticmethod
    def _revision_lineage_alternative_revision_iris(
        *,
        selected: GraphRevisionListItem,
        restage_chain: list[GraphRevisionListItem],
        by_iri: dict[str, GraphRevisionListItem],
    ) -> list[str]:
        seed_iris = {selected.iri, *(item.iri for item in restage_chain)}
        values: list[str | None] = []
        for item in [selected, *restage_chain]:
            values.extend([item.alternative_to, item.current_alternative_to])
        for item in by_iri.values():
            if item.iri in seed_iris:
                continue
            if (
                item.alternative_to in seed_iris
                or item.current_alternative_to in seed_iris
            ):
                values.append(item.iri)
        return [value for value in dict.fromkeys(values) if value is not None]
    def list_resource_revisions(
        self,
        resource_iri: str,
        *,
        graph: str | None = "history",
        include_patch_mentions: bool = True,
        include_apply_checks: bool = True,
        drift_detail: TypingLiteral["summary", "exact"] = "summary",
        current_staged_work_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> ResourceRevisionList:
        if drift_detail not in {"summary", "exact"}:
            raise DoxaBaseError("drift_detail must be 'summary' or 'exact'")
        self._ensure_non_negative("limit", limit)
        self._ensure_non_negative("offset", offset)
        include_apply_checks = include_apply_checks or current_staged_work_only
        resource_value = self._required_iri("resource_iri", resource_iri)
        data_graphs = self._expand_graphs([graph] if graph else None)
        lookup_graphs = self._lookup_graphs(self._expand_graphs(["all"]))

        all_revisions = self.list_graph_revisions(
            graph=graph,
            include_apply_checks=False,
            drift_detail=drift_detail,
            current_staged_work_only=False,
            limit=1_000_000,
        )
        matched: list[ResourceRevisionListItem] = []
        staged_cache: dict[str, StagedGraphRevisionDescription | None] = {}
        unreadable_patch_iris: set[str] = set()
        unreadable_revision_iris: set[str] = set()
        omitted_match_risk = False
        for item in all_revisions.revisions:
            if current_staged_work_only and not item.is_current_staged_work:
                continue
            match_types: list[str] = []
            revision_anchor_match = resource_value in self._objects(
                data_graphs,
                item.iri,
                "rc:revisionAnchor",
            )
            if revision_anchor_match:
                match_types.append("revision_anchor")

            patch_mentions: list[ResourceRevisionPatchMention] = []
            patch_mentions_unreadable_count = 0
            if include_patch_mentions and item.has_patch_payload:
                staged = self._cached_staged_revision(
                    item.iri,
                    graph=graph,
                    cache=staged_cache,
                )
                if staged is not None:
                    patch_scan = self._resource_revision_patch_mentions(
                        staged,
                        resource_value,
                    )
                    patch_mentions = patch_scan.mentions
                    patch_mentions_unreadable_count = (
                        patch_scan.unreadable_patch_count
                    )
                    if patch_scan.unreadable_patch_iris:
                        unreadable_patch_iris.update(
                            patch_scan.unreadable_patch_iris
                        )
                        unreadable_revision_iris.add(item.iri)
                    match_types.extend(
                        self._resource_revision_patch_match_types(
                            patch_mentions,
                            prefix="patch",
                        )
                    )

            applied_source_revision_iri = item.applies_staged_revision
            applied_source_patch_mentions: list[ResourceRevisionPatchMention] = []
            applied_source_patch_mentions_unreadable_count = 0
            applied_source_match = False
            if applied_source_revision_iri is not None:
                staged = self._cached_staged_revision(
                    applied_source_revision_iri,
                    graph=graph,
                    cache=staged_cache,
                )
                if staged is not None:
                    source_anchor_match = resource_value in {
                        anchor.iri for anchor in staged.revision_anchors
                    }
                    if include_patch_mentions:
                        applied_source_scan = self._resource_revision_patch_mentions(
                            staged,
                            resource_value,
                        )
                        applied_source_patch_mentions = (
                            applied_source_scan.mentions
                        )
                        applied_source_patch_mentions_unreadable_count = (
                            applied_source_scan.unreadable_patch_count
                        )
                        if applied_source_scan.unreadable_patch_iris:
                            unreadable_patch_iris.update(
                                applied_source_scan.unreadable_patch_iris
                            )
                            unreadable_revision_iris.add(applied_source_revision_iri)
                        if applied_source_patch_mentions:
                            applied_source_match = True
                            match_types.extend(
                                self._resource_revision_patch_match_types(
                                    applied_source_patch_mentions,
                                    prefix="applied_source_patch",
                                )
                            )
                else:
                    source_anchor_match = resource_value in self._objects(
                        data_graphs,
                        applied_source_revision_iri,
                        "rc:revisionAnchor",
                    )
                if source_anchor_match:
                    applied_source_match = True
                    match_types.append("applied_source_revision_anchor")

            match_types = list(dict.fromkeys(match_types))
            patch_mention_match = bool(patch_mentions)
            if (
                not revision_anchor_match
                and not patch_mention_match
                and not applied_source_match
            ):
                if (
                    patch_mentions_unreadable_count > 0
                    or applied_source_patch_mentions_unreadable_count > 0
                ):
                    omitted_match_risk = True
                continue
            matched.append(
                ResourceRevisionListItem(
                    revision=item,
                    revision_iri=item.iri,
                    match_types=match_types,
                    revision_anchor_match=revision_anchor_match,
                    patch_mention_match=patch_mention_match,
                    applied_source_match=applied_source_match,
                    applied_source_revision_iri=applied_source_revision_iri,
                    patch_mentions=patch_mentions,
                    patch_mentions_incomplete=patch_mentions_unreadable_count > 0,
                    patch_mentions_unreadable_count=patch_mentions_unreadable_count,
                    applied_source_patch_mentions=applied_source_patch_mentions,
                    applied_source_patch_mentions_incomplete=(
                        applied_source_patch_mentions_unreadable_count > 0
                    ),
                    applied_source_patch_mentions_unreadable_count=(
                        applied_source_patch_mentions_unreadable_count
                    ),
                )
            )

        sliced = matched[offset : offset + limit]
        if include_apply_checks:
            sliced = [
                self._resource_revision_item_with_apply_check(
                    item,
                    drift_detail=drift_detail,
                )
                for item in sliced
            ]
        next_action_queue_items: list[RevisionNextActionQueueItem] = []
        for item in sliced:
            queue_item = self._revision_next_action_queue_item(
                row_iri=item.revision.iri,
                next_action=item.revision.next_action,
                record_kind=item.revision.record_kind,
                application_status=item.revision.application_status,
                application_decision=item.revision.application_decision,
                stale_resolution_state=item.revision.stale_resolution_state,
                staged_validation_status=item.revision.staged_validation_status,
                semantic_risk_level=item.revision.application_semantic_risk_level,
                semantic_risk_reasons=item.revision.application_semantic_risk_reasons,
                alternative_gate=item.revision.alternative_gate,
            )
            if queue_item is not None:
                next_action_queue_items.append(queue_item)
        next_action_queue_items = (
            self._revision_next_action_queue_items_with_alternative_sets(
                next_action_queue_items,
                (
                    (
                        item.revision.iri,
                        item.revision.alternative_to,
                        item.revision.current_alternative_to,
                    )
                    for item in sliced
                ),
            )
        )
        timeline = self._resource_revision_timeline_events(
            sliced,
            next_action_queue_items=next_action_queue_items,
        )
        return ResourceRevisionList(
            resource=self._resource_summary(lookup_graphs, resource_value),
            revisions=sliced,
            timeline=timeline,
            timeline_note=(
                "Timeline events summarize the returned page in chronological "
                "order. Increase limit or paginate when total_count is greater "
                "than returned_count."
            ),
            count=len(matched),
            returned_count=len(sliced),
            total_count=len(matched),
            limit=limit,
            offset=offset,
            current_staged_work_only=current_staged_work_only,
            include_patch_mentions=include_patch_mentions,
            patch_mention_scan=ResourceRevisionPatchMentionScanSummary(
                status=(
                    "not_requested"
                    if not include_patch_mentions
                    else "incomplete"
                    if unreadable_patch_iris
                    else "complete"
                ),
                unreadable_patch_count=(
                    len(unreadable_patch_iris) if include_patch_mentions else 0
                ),
                unreadable_revision_count=(
                    len(unreadable_revision_iris) if include_patch_mentions else 0
                ),
                omitted_match_risk=(
                    omitted_match_risk if include_patch_mentions else False
                ),
            ),
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,
            next_action_queue=self._revision_next_action_queue(
                (item.revision.iri, item.revision.next_action) for item in sliced
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
        )
    def _resource_revision_timeline_events(
        self,
        items: list[ResourceRevisionListItem],
        *,
        next_action_queue_items: list[RevisionNextActionQueueItem],
    ) -> list[ResourceRevisionTimelineEvent]:
        queue_by_row = {item.row_iri: item for item in next_action_queue_items}
        ordered = sorted(
            items,
            key=lambda item: (
                item.revision.created_at or "",
                item.revision.summary or "",
                item.revision.iri,
            ),
        )
        events: list[ResourceRevisionTimelineEvent] = []
        for event_index, item in enumerate(ordered, start=1):
            applied_revision_iri, staged_revision_iri = (
                self._resource_revision_applied_pair(item)
            )
            queue_item = queue_by_row.get(item.revision_iri)
            next_action = item.revision.next_action
            events.append(
                ResourceRevisionTimelineEvent(
                    event_index=event_index,
                    revision_iri=item.revision_iri,
                    record_kind=item.revision.record_kind,
                    timeline_role=self._resource_revision_lineage_role(item),
                    summary=item.revision.summary,
                    created_at=item.revision.created_at,
                    changed_graphs=item.revision.changed_graphs,
                    match_types=item.match_types,
                    application_status=item.revision.application_status,
                    stale_resolution_state=item.revision.stale_resolution_state,
                    not_current_staged_work_reason=(
                        item.revision.not_current_staged_work_reason
                    ),
                    applied_revision_iri=applied_revision_iri,
                    staged_revision_iri=staged_revision_iri,
                    applied_by=item.revision.applied_by,
                    applied_source_revision_iri=item.applied_source_revision_iri,
                    restaged_from=item.revision.restaged_from,
                    current_restaged_by=item.revision.current_restaged_by,
                    queue=(
                        queue_item.queue
                        if queue_item is not None
                        else next_action.queue
                        if next_action is not None
                        else None
                    ),
                    action_type=(
                        queue_item.action_type
                        if queue_item is not None
                        else next_action.action_type
                        if next_action is not None
                        else None
                    ),
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
                        queue_item.row_is_target if queue_item is not None else None
                    ),
                    next_action_call=(
                        queue_item.call
                        if queue_item is not None
                        else next_action.call
                        if next_action is not None
                        else None
                    ),
                )
            )
        return events
    def describe_resource_revision_lineage(
        self,
        resource_iri: str,
        revision_iri: str,
        *,
        graph: str | None = "history",
        include_patch_mentions: bool = True,
        include_apply_checks: bool = True,
        drift_detail: TypingLiteral["summary", "exact"] = "summary",
        include_applied_diff: bool = True,
        include_triples: bool = False,
        max_triples: int = 100,
    ) -> ResourceRevisionLineageDescription:
        if max_triples < 1:
            raise DoxaBaseError("max_triples must be at least 1")
        resource_value = self._required_iri("resource_iri", resource_iri)
        revision_value = self._required_iri("revision_iri", revision_iri)
        lineage = self.list_resource_revisions(
            resource_value,
            graph=graph,
            include_patch_mentions=include_patch_mentions,
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,
            limit=1_000_000,
        )
        by_iri = {item.revision.iri: item for item in lineage.revisions}
        selected = by_iri.get(revision_value)
        if selected is None:
            scan = lineage.patch_mention_scan
            scan_note = ""
            if scan.status == "incomplete" or scan.omitted_match_risk:
                scan_note = (
                    " Resource patch mention scan was "
                    f"{scan.status}; unreadable_patch_count="
                    f"{scan.unreadable_patch_count}; "
                    "unreadable_revision_count="
                    f"{scan.unreadable_revision_count}; "
                    f"omitted_match_risk={scan.omitted_match_risk}."
                )
            try:
                self.describe_graph_revision(revision_value, graph=graph)
            except DoxaBaseError:
                history_hint = self._missing_revision_snapshot_storage_hint(
                    revision_value
                )
            else:
                if include_patch_mentions:
                    history_hint = (
                        " Revision exists in history, but it is not linked to "
                        "this resource through revision anchors, patch "
                        "payloads, or applied-source patch context"
                    )
                else:
                    history_hint = (
                        " Revision exists in history, but patch payload "
                        "scanning was disabled for this lineage request. "
                        "Rerun with include_patch_mentions=True before "
                        "concluding that the revision is not linked through "
                        "patch payloads or applied-source patch context"
                    )
            raise DoxaBaseError(
                f"Revision '{revision_iri}' was not found in resource lineage "
                f"for '{resource_iri}'"
                f"{history_hint}."
                f"{scan_note}"
            )

        applied_revision_iri, staged_revision_iri = (
            self._resource_revision_applied_pair(selected)
        )
        paired_iri = (
            staged_revision_iri
            if selected.revision.iri == applied_revision_iri
            else applied_revision_iri
        )
        paired = by_iri.get(paired_iri) if paired_iri is not None else None
        current_staged_revision_iri = self._resource_lineage_current_staged_iri(
            selected,
            by_iri,
        )
        current_successor = (
            by_iri.get(selected.revision.current_restaged_by)
            if selected.revision.current_restaged_by is not None
            else None
        )
        current_successor_applied_revision_iri = (
            current_successor.revision.applied_by
            if current_successor is not None
            else None
        )
        graph_lineage = self.describe_revision_lineage(
            revision_value,
            graph=graph,
            include_apply_checks=include_apply_checks,
            drift_detail=drift_detail,
        )
        lineage_applied_revision_iri = applied_revision_iri
        lineage_staged_revision_iri = staged_revision_iri
        applied_diff_item = (
            selected if selected.revision.iri == applied_revision_iri else paired
        )
        if (
            lineage_applied_revision_iri is None
            and graph_lineage.latest_role == "applied_event"
            and graph_lineage.applied_revision_iri is not None
        ):
            lineage_applied_revision_iri = graph_lineage.applied_revision_iri
            if graph_lineage.restage_chain_iris:
                lineage_staged_revision_iri = graph_lineage.restage_chain_iris[-1]
            applied_diff_item = by_iri.get(lineage_applied_revision_iri)
        related_revision_iris = self._resource_lineage_related_revision_iris(
            selected,
            paired,
            applied_revision_iri=lineage_applied_revision_iri,
            staged_revision_iri=lineage_staged_revision_iri,
            current_staged_revision_iri=current_staged_revision_iri,
            current_successor_applied_revision_iri=(
                current_successor_applied_revision_iri
            ),
            graph_lineage_related_revision_iris=(
                graph_lineage.related_revision_iris
            ),
        )
        lineage_next_action, lineage_suggested_next_actions = (
            self._resource_lineage_next_actions(
                selected,
                current_successor_applied_revision_iri=(
                    current_successor_applied_revision_iri
                ),
            )
        )

        applied_diff_status = "not_applicable"
        applied_diff_note: str | None = (
            "No applied staged-revision event is linked to this resource revision."
        )
        applied_diff: ResourceAppliedRevisionDiffSummary | None = None
        if (
            lineage_applied_revision_iri is not None
            and lineage_staged_revision_iri is not None
        ):
            if include_applied_diff:
                applied_diff = self._resource_applied_revision_diff_summary(
                    resource_iri=resource_value,
                    applied_revision_iri=lineage_applied_revision_iri,
                    staged_revision_iri=lineage_staged_revision_iri,
                    graph=graph,
                    include_triples=include_triples,
                    max_triples=max_triples,
                    applied_item=applied_diff_item,
                )
                applied_diff_status = (
                    "available"
                    if any(
                        diff.exact_changed_triples_available
                        for diff in applied_diff.graph_diffs
                    )
                    else "unavailable"
                )
                applied_diff_note = (
                    "Resource-filtered applied diff summary is available."
                    if applied_diff_status == "available"
                    else (
                        "Applied event is linked, but exact before/after "
                        "snapshot rows are unavailable for the changed graphs."
                    )
                )
            else:
                applied_diff_status = "omitted"
                applied_diff_note = (
                    "Applied event is linked, but applied diff summary was "
                    "omitted by request."
                )
        lineage_suggested_next_actions = self._with_revision_snapshot_evidence_actions(
            lineage_suggested_next_actions,
            selected.revision.snapshot_evidence,
            paired.revision.snapshot_evidence if paired is not None else None,
            graph_lineage.selected_revision.snapshot_evidence,
            (
                graph_lineage.paired_revision.snapshot_evidence
                if graph_lineage.paired_revision is not None
                else None
            ),
            applied_diff.snapshot_evidence if applied_diff is not None else None,
            (
                applied_diff.source_snapshot_evidence
                if applied_diff is not None
                else None
            ),
        )
        snapshot_next_action = self._snapshot_evidence_completion_next_action(
            lineage_suggested_next_actions
        )
        if snapshot_next_action is not None:
            lineage_next_action = snapshot_next_action
        lineage_next_action_queue_item = self._revision_next_action_queue_item(
            row_iri=selected.revision.iri,
            next_action=lineage_next_action,
            record_kind=selected.revision.record_kind,
            application_status=selected.revision.application_status,
            application_decision=selected.revision.application_decision,
            stale_resolution_state=selected.revision.stale_resolution_state,
            staged_validation_status=selected.revision.staged_validation_status,
            semantic_risk_level=selected.revision.application_semantic_risk_level,
            semantic_risk_reasons=(
                selected.revision.application_semantic_risk_reasons
            ),
            alternative_gate=selected.revision.alternative_gate,
        )
        if lineage_next_action_queue_item is not None:
            lineage_next_action_queue_item = (
                self._revision_next_action_queue_items_with_alternative_sets(
                    [lineage_next_action_queue_item],
                    (
                        (
                            item.revision.iri,
                            item.revision.alternative_to,
                            item.revision.current_alternative_to,
                        )
                        for item in lineage.revisions
                    ),
                )[0]
            )

        return ResourceRevisionLineageDescription(
            resource=lineage.resource,
            selected_revision=selected,
            selected_revision_iri=selected.revision.iri,
            selected_role=self._resource_revision_lineage_role(selected),
            paired_revision=paired,
            paired_revision_iri=(
                paired.revision.iri if paired is not None else None
            ),
            paired_role=(
                self._resource_revision_lineage_role(paired)
                if paired is not None
                else None
            ),
            applied_revision_iri=lineage_applied_revision_iri,
            staged_revision_iri=lineage_staged_revision_iri,
            applied_source_revision_iri=(
                lineage_staged_revision_iri
                if lineage_applied_revision_iri is not None
                else None
            ),
            current_staged_revision_iri=current_staged_revision_iri,
            current_revision_iri=current_staged_revision_iri,
            latest_revision_iri=graph_lineage.latest_revision_iri,
            latest_role=graph_lineage.latest_role,
            restage_chain_iris=graph_lineage.restage_chain_iris,
            alternative_revision_iris=graph_lineage.alternative_revision_iris,
            related_revision_iris=related_revision_iris,
            warnings=graph_lineage.warnings,
            patch_mention_scan=lineage.patch_mention_scan,
            next_action=lineage_next_action,
            next_action_queue_item=lineage_next_action_queue_item,
            suggested_next_actions=lineage_suggested_next_actions,
            suggested_next_calls=[
                action.call for action in lineage_suggested_next_actions
            ],
            applied_diff_status=applied_diff_status,
            applied_diff_note=applied_diff_note,
            applied_diff=applied_diff,
        )
    def _resource_lineage_next_actions(
        self,
        selected: ResourceRevisionListItem,
        *,
        current_successor_applied_revision_iri: str | None,
    ) -> tuple[RevisionNextAction | None, list[SuggestedNextAction]]:
        if (
            selected.revision.current_restaged_by is None
            or current_successor_applied_revision_iri is None
        ):
            suggested_next_actions = list(selected.revision.suggested_next_actions)
            if not suggested_next_actions:
                derived_action = self._suggested_action_from_revision_next_action(
                    selected.revision.next_action,
                )
                if derived_action is not None:
                    suggested_next_actions = [derived_action]
            return (
                selected.revision.next_action,
                suggested_next_actions,
            )

        def action(
            *,
            action_label: str,
            tool_name: str,
            arguments: dict[str, Any],
            reason: str,
        ) -> SuggestedNextAction:
            return self._effect_annotated_suggested_next_action(
                action_label=action_label,
                tool_name=tool_name,
                arguments=arguments,
                reason=reason,
            )

        preferred_actions = [
            action(
                action_label="Inspect applied event",
                tool_name="describe_graph_revision",
                arguments={"iri": current_successor_applied_revision_iri},
                reason=(
                    "The refreshed successor has already been applied; inspect "
                    "the applied event before following the stale source or "
                    "successor hop."
                ),
            ),
            action(
                action_label="Inspect applied diff",
                tool_name="describe_applied_revision_diff",
                arguments={"iri": current_successor_applied_revision_iri},
                reason=(
                    "Inspect stored before/after graph snapshot counts and, "
                    "when needed, exact changed triples for the applied event."
                ),
            ),
        ]
        combined_actions: list[SuggestedNextAction] = []
        seen: set[tuple[str, str]] = set()
        for candidate in [
            *preferred_actions,
            *selected.revision.suggested_next_actions,
        ]:
            key = (candidate.tool_name, candidate.call)
            if key in seen:
                continue
            seen.add(key)
            combined_actions.append(candidate)
        first = preferred_actions[0]
        return (
            RevisionNextAction(
                action_type="inspect_applied_event",
                queue="inspect_already_applied",
                action_label=first.action_label,
                tool_name=first.tool_name,
                mcp_tool_name=first.mcp_tool_name,
                arguments=first.arguments,
                reason=first.reason,
                call=first.call,
                source="suggested_next_actions",
            ),
            combined_actions,
        )
    @staticmethod
    def _resource_revision_applied_pair(
        item: ResourceRevisionListItem,
    ) -> tuple[str | None, str | None]:
        if item.revision.record_kind == "applied_event":
            return item.revision.iri, item.applied_source_revision_iri
        if item.revision.applied_by is not None:
            return item.revision.applied_by, item.revision.iri
        if item.revision.record_kind == "staged_patch":
            return None, item.revision.iri
        return None, None
    @staticmethod
    def _resource_revision_lineage_role(item: ResourceRevisionListItem) -> str:
        if item.revision.record_kind == "applied_event":
            return "applied_event"
        if item.revision.applied_by is not None:
            return "applied_source"
        if item.revision.current_restaged_by is not None:
            return "restaged_source"
        if item.revision.is_current_staged_work:
            return "current_staged_revision"
        if item.revision.record_kind == "staged_patch":
            return "staged_revision"
        return "history_record"
    @staticmethod
    def _resource_lineage_related_revision_iris(
        selected: ResourceRevisionListItem,
        paired: ResourceRevisionListItem | None,
        *,
        applied_revision_iri: str | None,
        staged_revision_iri: str | None,
        current_staged_revision_iri: str | None,
        current_successor_applied_revision_iri: str | None,
        graph_lineage_related_revision_iris: list[str],
    ) -> list[str]:
        values = [
            selected.revision.iri,
            paired.revision.iri if paired is not None else None,
            applied_revision_iri,
            staged_revision_iri,
            current_staged_revision_iri,
            current_successor_applied_revision_iri,
            selected.revision.restaged_from,
            selected.revision.restaged_by,
            selected.revision.current_restaged_by,
            paired.revision.restaged_from if paired is not None else None,
            paired.revision.restaged_by if paired is not None else None,
            paired.revision.current_restaged_by if paired is not None else None,
            *graph_lineage_related_revision_iris,
        ]
        return [value for value in dict.fromkeys(values) if value is not None]
    def _resource_revision_patch_mentions(
        self,
        staged: StagedGraphRevisionDescription,
        resource_iri: str,
    ) -> _ResourceRevisionPatchMentionScan:
        mentions: list[ResourceRevisionPatchMention] = []
        unreadable_patch_iris: list[str] = []
        role_order = ("subject", "predicate", "object")
        for patch in staged.patches:
            if patch.content is None:
                unreadable_patch_iris.append(patch.iri)
                continue
            try:
                patch_graph = self._parse_staged_patch_description(patch)
            except DoxaBaseError:
                unreadable_patch_iris.append(patch.iri)
                continue
            matched_roles: set[str] = set()
            matched_triples = 0
            for subject, predicate, object_node in patch_graph:
                triple_matched = False
                if str(subject) == resource_iri:
                    matched_roles.add("subject")
                    triple_matched = True
                if str(predicate) == resource_iri:
                    matched_roles.add("predicate")
                    triple_matched = True
                if str(object_node) == resource_iri:
                    matched_roles.add("object")
                    triple_matched = True
                if triple_matched:
                    matched_triples += 1
            if matched_roles:
                mentions.append(
                    ResourceRevisionPatchMention(
                        patch_iri=patch.iri,
                        target_graph=patch.target_graph,
                        operation=patch.operation,
                        operation_label=patch.operation_label,
                        patch_role=patch.patch_role,
                        patch_role_label=patch.patch_role_label,
                        sequence_index=patch.sequence_index,
                        matched_term_roles=[
                            role for role in role_order if role in matched_roles
                        ],
                        matched_triples=matched_triples,
                        triple_count=patch.triple_count,
                    )
                )
        return _ResourceRevisionPatchMentionScan(
            mentions=mentions,
            unreadable_patch_count=len(unreadable_patch_iris),
            unreadable_patch_iris=unreadable_patch_iris,
        )
    @staticmethod
    def _resource_revision_patch_match_types(
        mentions: list[ResourceRevisionPatchMention],
        *,
        prefix: str,
    ) -> list[str]:
        return list(
            dict.fromkeys(
                f"{prefix}_{role}"
                for mention in mentions
                for role in mention.matched_term_roles
            )
        )
    @staticmethod
    def _draft_query_plan_template_lineage(
        selected_candidate: QueryTargetCandidate | None,
        *,
        verification_status: ResourceSummary | None,
        verification_note: str | None,
    ) -> str | None:
        if selected_candidate is None:
            return None
        source_label = (
            selected_candidate.source_resource.label
            or selected_candidate.source_resource.iri
        )
        if selected_candidate.template_source == "storage_access_location":
            lineage = f"Candidate storage root comes from storage access {source_label}."
        else:
            lineage = (
                f"Template comes from {selected_candidate.template_source} "
                f"{source_label}."
            )
        if verification_status is not None:
            status_label = verification_status.label or verification_status.iri
            lineage = f"{lineage} Verification status: {status_label}."
        if verification_note:
            lineage = f"{lineage} Verification note: {verification_note}"
        return lineage
