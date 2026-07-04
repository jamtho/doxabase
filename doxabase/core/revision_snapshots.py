"""Revision snapshot storage, drift, and evidence.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via RevisionSnapshotsMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class RevisionSnapshotsMixin:
    def describe_revision_snapshot_evidence(
        self,
        iri: str,
        *,
        graph: str | None = "history",
    ) -> RevisionSnapshotEvidenceStatus:
        revision_iri = self.expand_iri(iri)
        data_graphs = self._expand_graphs([graph] if graph else None)
        return self._revision_snapshot_evidence_status(revision_iri, data_graphs)
    def describe_revision_graph_snapshot(
        self,
        iri: str,
        graph_role: str,
        *,
        graph: str | None = "history",
        include_triples: bool = False,
        max_triples: int = 500,
    ) -> RevisionGraphSnapshotDescription:
        if max_triples < 1:
            raise DoxaBaseError("max_triples must be at least 1")
        if graph_role not in self._known_graph_names():
            raise DoxaBaseError(f"Unknown graph role: {graph_role}")

        revision_iri = self.expand_iri(iri)
        data_graphs = self._expand_graphs([graph] if graph else None)
        snapshot_evidence = self._revision_snapshot_evidence_status(
            revision_iri,
            data_graphs,
        )
        rdf_snapshots = {
            snapshot.graph_role: snapshot
            for snapshot in self._graph_revision_snapshots(revision_iri, data_graphs)
        }
        rdf_snapshot = rdf_snapshots.get(graph_role)
        stored_metadata = self._graph_snapshot_storage_metadata(
            revision_iri,
            graph_role,
        )

        triples: list[GraphTripleDescription] = []
        triples_included = False
        triples_truncated = False
        stored_at: str | None = None
        if stored_metadata is not None:
            triple_count = int(stored_metadata["triple_count"])
            content_digest = stored_metadata["content_digest"]
            stored_at = stored_metadata["stored_at"]
            count_basis = "stored_snapshot_rows"
            exact_snapshot_available = True
            if include_triples:
                rows = self._graph_snapshot_storage_rows(revision_iri, graph_role)
                triples_included = True
                triples_truncated = len(rows) > max_triples
                triples = [
                    self._graph_triple_description(row)
                    for row in rows[:max_triples]
                ]
                if triples_truncated:
                    note = (
                        "Exact stored snapshot rows are included up to "
                        "max_triples for this revision and graph role."
                    )
                else:
                    note = (
                        "Exact stored snapshot rows are included for this "
                        "revision and graph role."
                    )
            else:
                note = (
                    "Exact stored snapshot rows are available for this revision "
                    "and graph role; pass include_triples=True to include them."
                )
        elif rdf_snapshot is not None:
            triple_count = rdf_snapshot.triple_count
            content_digest = rdf_snapshot.content_digest
            count_basis = "rdf_history_graph_snapshot"
            exact_snapshot_available = False
            note = (
                "RDF history count/digest metadata is present for this revision "
                "and graph role, but exact stored snapshot rows are absent. "
                "Import a companion revision snapshot JSON bundle before relying "
                "on exact snapshot triples."
            )
        else:
            triple_count = None
            content_digest = None
            count_basis = "unavailable"
            exact_snapshot_available = False
            note = (
                "No RDF graph snapshot metadata or stored snapshot rows were "
                "found for this revision and graph role."
            )

        suggested_next_actions = self._with_revision_snapshot_evidence_actions(
            [],
            snapshot_evidence,
        )
        return RevisionGraphSnapshotDescription(
            revision_iri=revision_iri,
            graph_role=graph_role,
            snapshot_evidence=snapshot_evidence,
            triple_count=triple_count,
            content_digest=content_digest,
            count_basis=count_basis,
            stored_at=stored_at,
            exact_snapshot_available=exact_snapshot_available,
            include_triples=include_triples,
            triples_included=triples_included,
            triples_truncated=triples_truncated,
            max_triples=max_triples,
            triples=triples,
            suggested_next_actions=suggested_next_actions,
            note=note,
        )
    def _revision_snapshot_evidence_status(
        self,
        revision_iri: str,
        graphs: list[str],
    ) -> RevisionSnapshotEvidenceStatus:
        history_revision_found = (
            self._subject_exists(revision_iri, graphs)
            and self.expand_iri("rc:GraphRevision")
            in self._types_from_graphs(graphs, revision_iri)
        )
        rdf_snapshot_graph_roles = [
            snapshot.graph_role
            for snapshot in self._graph_revision_snapshots(revision_iri, graphs)
        ]
        stored_snapshot_graph_roles = self._graph_snapshot_storage_graph_roles(
            revision_iri
        )
        stored_role_set = set(stored_snapshot_graph_roles)
        rdf_role_set = set(rdf_snapshot_graph_roles)
        exact_snapshot_graph_roles = [
            role for role in rdf_snapshot_graph_roles if role in stored_role_set
        ]
        missing_snapshot_row_graph_roles = [
            role for role in rdf_snapshot_graph_roles if role not in stored_role_set
        ]
        orphan_snapshot_row_graph_roles = [
            role for role in stored_snapshot_graph_roles if role not in rdf_role_set
        ]
        missing_current_graph_roles = (
            self._revision_snapshot_missing_current_graph_roles(
                revision_iri,
                exact_snapshot_graph_roles,
            )
        )

        if not history_revision_found:
            if stored_snapshot_graph_roles:
                status = "snapshot_rows_without_history"
                note = (
                    "SQLite snapshot rows exist for this revision IRI, but the "
                    "RDF history revision record is missing. Import the project "
                    "or history RDF bundle before using normal revision helpers; "
                    "workflow RDF exports do not include history."
                )
            else:
                status = "history_missing"
                note = (
                    "No RDF history revision record or SQLite snapshot rows were "
                    "found for this revision IRI."
                )
        elif not stored_snapshot_graph_roles:
            status = "history_only_count_digest"
            note = (
                "RDF history metadata and count/digest graph snapshots are "
                "present, but SQLite snapshot rows for exact changed-triple "
                "inspection are absent. Import a companion revision snapshot "
                "JSON bundle when exact applied diffs or stale drift triples are "
                "needed."
            )
        else:
            status = "history_plus_snapshot_rows"
            note = (
                "RDF history metadata and SQLite snapshot rows are present. "
                "Exact changed-triple inspection is available for graph roles "
                "listed in exact_snapshot_graph_roles."
            )
            if missing_snapshot_row_graph_roles:
                note = (
                    f"{note} Some RDF snapshot graph roles lack stored rows: "
                    f"{', '.join(missing_snapshot_row_graph_roles)}."
                )
            if orphan_snapshot_row_graph_roles:
                note = (
                    f"{note} Some stored snapshot rows have no matching RDF "
                    "snapshot metadata in the selected history graph: "
                    f"{', '.join(orphan_snapshot_row_graph_roles)}."
                )
            if missing_current_graph_roles:
                note = (
                    f"{note} Current project graph role(s) appear empty even "
                    "though imported snapshot rows for those roles are non-empty: "
                    f"{', '.join(missing_current_graph_roles)}. Import the "
                    "complete project RDF bundle before mutation recovery."
                )

        suggested_next_actions = self._revision_snapshot_evidence_next_actions(
            status=status,
            revision_iri=revision_iri,
            missing_snapshot_row_graph_roles=missing_snapshot_row_graph_roles,
            orphan_snapshot_row_graph_roles=orphan_snapshot_row_graph_roles,
            missing_current_graph_roles=missing_current_graph_roles,
        )
        return RevisionSnapshotEvidenceStatus(
            revision_iri=revision_iri,
            status=status,
            history_revision_found=history_revision_found,
            rdf_snapshot_graph_roles=rdf_snapshot_graph_roles,
            stored_snapshot_graph_roles=stored_snapshot_graph_roles,
            exact_snapshot_graph_roles=exact_snapshot_graph_roles,
            missing_snapshot_row_graph_roles=missing_snapshot_row_graph_roles,
            orphan_snapshot_row_graph_roles=orphan_snapshot_row_graph_roles,
            missing_current_graph_roles=missing_current_graph_roles,
            note=note,
            suggested_next_actions=suggested_next_actions,
        )
    def _revision_snapshot_missing_current_graph_roles(
        self,
        revision_iri: str,
        exact_snapshot_graph_roles: Iterable[str],
    ) -> list[str]:
        missing_roles: list[str] = []
        for role in exact_snapshot_graph_roles:
            metadata = self._graph_snapshot_storage_metadata(revision_iri, role)
            if metadata is None or int(metadata["triple_count"]) <= 0:
                continue
            if self.triple_count(role) == 0:
                missing_roles.append(role)
        return missing_roles
    def _revision_snapshot_evidence_next_actions(
        self,
        *,
        status: str,
        revision_iri: str,
        missing_snapshot_row_graph_roles: list[str],
        orphan_snapshot_row_graph_roles: list[str],
        missing_current_graph_roles: list[str],
    ) -> list[SuggestedNextAction]:
        actions: list[SuggestedNextAction] = []

        def add_action(
            tool_name: str,
            arguments: dict[str, Any],
            reason: str,
        ) -> None:
            actions.append(
                SuggestedNextAction(
                    tool=f"doxabase.{tool_name}",
                    args=arguments,
                    reason=reason,
                )
            )

        if status == "history_only_count_digest" or missing_snapshot_row_graph_roles:
            add_action(
                "import_bundle",
                {
                    "kind": "revision_snapshots",
                    "spec": {
                        "path": "/tmp/revision-snapshots.json",
                        "path_is_placeholder": True,
                    },
                },
                (
                    "RDF history metadata is present for "
                    f"'{revision_iri}', but exact snapshot rows are missing for "
                    "one or more graph roles. Import the companion snapshot JSON "
                    "bundle at its real handoff path before relying on exact "
                    "applied-diff or stale-drift triple inspection. If the "
                    "snapshot JSON is not available, request a "
                    "recovery-complete export_bundle(kind='handoff') from "
                    "the source capsule."
                )
            )
        if status == "snapshot_rows_without_history" or (
            orphan_snapshot_row_graph_roles and status != "history_plus_snapshot_rows"
        ):
            add_action(
                "import_bundle",
                {
                    "kind": "trig",
                    "spec": {
                        "path": "/tmp/project.trig",
                        "path_is_placeholder": True,
                    },
                },
                (
                    "Snapshot rows exist for this revision, but the RDF history "
                    "record is missing. Import the project/history RDF bundle at "
                    "its real handoff path before using normal revision helpers."
                )
            )
        if missing_current_graph_roles:
            add_action(
                "import_bundle",
                {
                    "kind": "trig",
                    "spec": {
                        "path": "/tmp/project.trig",
                        "path_is_placeholder": True,
                    },
                },
                (
                    "RDF history metadata and exact snapshot rows are present "
                    f"for '{revision_iri}', but current project graph role(s) "
                    "appear empty despite non-empty stored snapshot rows: "
                    f"{', '.join(missing_current_graph_roles)}. Import the "
                    "complete project RDF bundle at its real handoff path before "
                    "planning apply, restage, or repair mutations."
                )
            )
        return actions
    @staticmethod
    def _with_revision_snapshot_evidence_actions(
        actions: list[SuggestedNextAction],
        *snapshot_evidence_items: RevisionSnapshotEvidenceStatus | None,
    ) -> list[SuggestedNextAction]:
        promoted_actions: list[SuggestedNextAction] = []
        for evidence in snapshot_evidence_items:
            if evidence is None:
                continue
            promoted_actions.extend(evidence.suggested_next_actions)
        if not promoted_actions:
            return actions
        combined: list[SuggestedNextAction] = []
        seen: set[tuple[str, str]] = set()
        for action in [*promoted_actions, *actions]:
            key = suggested_action_key(action)
            if key in seen:
                continue
            seen.add(key)
            combined.append(action)
        return combined
    @staticmethod
    def _snapshot_evidence_completion_next_action(
        actions: Iterable[SuggestedNextAction],
    ) -> RevisionNextAction | None:
        for action in actions:
            if import_bundle_action_kind(action) not in {
                "revision_snapshots",
                "trig",
            }:
                continue
            return RevisionNextAction(
                action_type="complete_handoff_import",
                queue="complete_handoff_import",
                action_label=action.tool.removeprefix("doxabase."),
                tool_name=action.tool.removeprefix("doxabase."),
                mcp_tool_name=action.tool,
                arguments=action.args,
                reason=action.reason,
                call=None,
                source="snapshot_evidence",
            )
        return None
    def _missing_revision_snapshot_storage_hint(self, revision_iri: str) -> str:
        stored_graph_roles = self._graph_snapshot_storage_graph_roles(revision_iri)
        if not stored_graph_roles:
            return ""
        return (
            ". Snapshot rows exist for this revision IRI in graph roles "
            f"{stored_graph_roles}, but the RDF history record is missing. "
            "Import the project/history RDF bundle before using normal revision "
            "helpers; workflow RDF exports do not include history."
        )
    @staticmethod
    def _missing_applied_snapshot_rows_note(
        *,
        before_snapshot: GraphSnapshotDescription | None,
        after_snapshot: GraphSnapshotDescription | None,
    ) -> str:
        note = (
            "Exact before/after snapshot triples are unavailable because "
            "one or both revision snapshots lack stored rows."
        )
        if before_snapshot is not None or after_snapshot is not None:
            note += (
                " If this capsule was populated from an RDF project/history "
                "handoff, import the companion JSON bundle with "
                "import_bundle(kind='revision_snapshots') after "
                "import_bundle(kind='trig')."
            )
        return note
    def _graph_version_snapshot_for_revision(
        self,
        revision: GraphRevisionListItem,
        graph_role: str,
        *,
        graph: str | None,
        include_apply_checks: bool,
        next_action_queue_item: RevisionNextActionQueueItem | None,
    ) -> GraphVersionListItem | None:
        snapshot = self.describe_revision_graph_snapshot(
            revision.iri,
            graph_role,
            graph=graph,
            include_triples=False,
        )
        if snapshot.triple_count is None:
            return None
        suggested_next_actions = [
            SuggestedNextAction(
                tool="doxabase.describe_revision",
                args={
                    "iri": revision.iri,
                    "aspect": "graph_snapshot",
                    "graph_role": graph_role,
                },
                reason="Inspect this stored graph snapshot; pass "
                    "include_triples=True only when exact historical triples "
                    "are needed and safe to review.",
            )
        ]
        if include_apply_checks or any(
            value is not None
            for value in (
                revision.applies_staged_revision,
                revision.applied_by,
                revision.restaged_from,
                revision.restaged_by,
                revision.current_restaged_by,
            )
        ):
            suggested_next_actions.append(
                SuggestedNextAction(
                    tool="doxabase.describe_revision",
                    args={"iri": revision.iri, "aspect": "lineage"},
                    reason="Inspect this row's staged/apply/restage lineage "
                        "before deciding whether the version row is current "
                        "work, superseded, or already applied.",
                )
            )
        if snapshot.exact_snapshot_available:
            suggested_next_actions.append(
                SuggestedNextAction(
                    tool="doxabase.describe_revision",
                    args={
                        "iri": revision.iri,
                        "aspect": "version_diff",
                        "graph_role": graph_role,
                        "compare_to_current": True,
                    },
                    reason="Compare this stored graph version with the current "
                        "live graph, including exact changed triples when "
                        "include_triples=True is safe and useful.",
                )
            )
        suggested_next_actions = self._with_revision_snapshot_evidence_actions(
            suggested_next_actions,
            snapshot.snapshot_evidence,
        )
        return GraphVersionListItem(
            revision_iri=revision.iri,
            graph_role=graph_role,
            record_kind=revision.record_kind,
            snapshot_semantics=self._graph_version_snapshot_semantics(revision),
            summary=revision.summary,
            revision_type=revision.revision_type,
            revision_type_label=revision.revision_type_label,
            created_at=revision.created_at,
            changed_graphs=revision.changed_graphs,
            included_graphs=self._graph_version_included_graphs(revision),
            applies_staged_revision=revision.applies_staged_revision,
            applied_by=revision.applied_by,
            restaged_from=revision.restaged_from,
            restaged_by=revision.restaged_by,
            current_restaged_by=revision.current_restaged_by,
            is_current_staged_work=revision.is_current_staged_work,
            not_current_staged_work_reason=(
                revision.not_current_staged_work_reason
            ),
            review_resolution=revision.review_resolution,
            staged_validation_status=revision.staged_validation_status,
            stale_resolution_state=revision.stale_resolution_state,
            application_status=revision.application_status,
            application_decision=revision.application_decision,
            application_can_apply=revision.application_can_apply,
            application_blocking_reasons=revision.application_blocking_reasons,
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
            triple_count=snapshot.triple_count,
            content_digest=snapshot.content_digest,
            count_basis=snapshot.count_basis,
            stored_at=snapshot.stored_at,
            exact_snapshot_available=snapshot.exact_snapshot_available,
            snapshot_evidence_status=snapshot.snapshot_evidence.status,
            snapshot_evidence=snapshot.snapshot_evidence,
            next_action=revision.next_action,
            next_action_queue_item=next_action_queue_item,
            suggested_next_actions=suggested_next_actions,
        )
    @staticmethod
    def _graph_version_snapshot_semantics(
        revision: GraphRevisionListItem,
    ) -> str:
        if revision.record_kind == "staged_patch":
            return "staged_before_graph"
        if revision.record_kind == "applied_event":
            return "applied_after_graph"
        return "recorded_graph_snapshot"
    @staticmethod
    def _revision_lineage_snapshot_warnings(
        *,
        selected: GraphRevisionListItem,
        paired: GraphRevisionListItem | None,
        latest: GraphRevisionListItem,
        current_staged_revision: GraphRevisionListItem | None,
        restage_chain: list[GraphRevisionListItem] | None = None,
    ) -> list[str]:
        rows = [
            ("selected", selected),
            ("paired", paired),
            ("latest", latest),
            ("current", current_staged_revision),
            *(
                (f"restage-chain ancestor {index}", item)
                for index, item in enumerate(restage_chain or [], start=1)
            ),
        ]
        warnings: list[str] = []
        seen: set[tuple[str, str]] = set()
        for role, row in rows:
            if row is None:
                continue
            status = row.snapshot_evidence.status
            if status == "history_plus_snapshot_rows":
                continue
            key = (row.iri, status)
            if key in seen:
                continue
            seen.add(key)
            if status == "history_only_count_digest":
                evidence_label = (
                    "RDF count/digest snapshot metadata"
                    if row.snapshot_evidence.rdf_snapshot_graph_roles
                    else "RDF history metadata"
                )
                warnings.append(
                    f"{role} revision '{row.iri}' has {evidence_label} but "
                    "no stored snapshot rows; import a "
                    "companion revision snapshot JSON bundle before expecting "
                    "exact applied diffs or stale drift triples."
                )
            elif status == "snapshot_rows_without_history":
                warnings.append(
                    f"{role} revision '{row.iri}' has stored snapshot rows but "
                    "no visible RDF history record; import the project/history "
                    "RDF bundle before using normal revision helpers."
                )
            elif status == "history_missing":
                warnings.append(
                    f"{role} revision '{row.iri}' has no visible RDF history "
                    "record or stored snapshot rows."
                )
        return warnings
    def _summary_snapshot_drifts(
        self,
        drifts: Iterable[StagedGraphSnapshotDrift],
    ) -> list[StagedGraphSnapshotDrift]:
        summary_drifts: list[StagedGraphSnapshotDrift] = []
        for drift in drifts:
            if drift.exact_changed_triples_available:
                note = (
                    "The graph content digest changed since this revision was "
                    "staged. Exact changed triples are available but omitted "
                    "from this summary response; call "
                    "apply_staged_revision(dry_run=true) or "
                    "list_revisions(drift_detail='exact') for them."
                )
            else:
                note = drift.note
            summary_drifts.append(
                StagedGraphSnapshotDrift(
                    graph_role=drift.graph_role,
                    snapshot_triple_count=drift.snapshot_triple_count,
                    current_triple_count=drift.current_triple_count,
                    snapshot_content_digest=drift.snapshot_content_digest,
                    current_content_digest=drift.current_content_digest,
                    exact_changed_triples_available=(
                        drift.exact_changed_triples_available
                    ),
                    exact_changed_triples_included=False,
                    triples_added_since_snapshot_count=(
                        drift.triples_added_since_snapshot_count
                    ),
                    triples_removed_since_snapshot_count=(
                        drift.triples_removed_since_snapshot_count
                    ),
                    drift_relevance=drift.drift_relevance,
                    patch_overlap_subjects=drift.patch_overlap_subjects,
                    patch_overlap_predicates=drift.patch_overlap_predicates,
                    patch_overlap_objects=drift.patch_overlap_objects,
                    revision_anchor_overlap=drift.revision_anchor_overlap,
                    changed_resource_count=drift.changed_resource_count,
                    changed_resources_returned_count=(
                        drift.changed_resources_returned_count
                    ),
                    changed_resources_omitted_count=(
                        drift.changed_resources_omitted_count
                    ),
                    changed_resources=drift.changed_resources,
                    changed_resource_suggested_next_actions=(
                        drift.changed_resource_suggested_next_actions
                    ),
                    triples_added_since_snapshot=[],
                    triples_removed_since_snapshot=[],
                    note=note,
                )
            )
        return summary_drifts
    def _is_broad_snapshot_drift_object_overlap(
        self,
        object_overlap: list[str],
    ) -> bool:
        return bool(object_overlap) and all(
            self._is_broad_snapshot_drift_object_term(term)
            for term in object_overlap
        )
    def _is_broad_snapshot_drift_object_term(self, term: str) -> bool:
        return term in {
            str(RDF.type),
            str(RDFS.Class),
            PREFIXES["owl"] + "Class",
            PREFIXES["rdf"] + "Property",
            PREFIXES["rc"] + "Dataset",
            PREFIXES["rc"] + "Table",
            PREFIXES["rc"] + "Field",
            PREFIXES["rc"] + "PhysicalLayout",
            PREFIXES["rc"] + "StorageAccess",
            PREFIXES["rc"] + "Pattern",
        }
    def _snapshot_drift_changed_resources_markdown(
        self,
        drift: StagedGraphSnapshotDrift,
        *,
        action_limit: int = 5,
    ) -> list[str]:
        if drift.changed_resource_count is None or not drift.changed_resources:
            return []
        lines = [
            "",
            f"#### Snapshot Drift Changed Resources: {drift.graph_role}",
            "",
            (
                "| Resource | Changed triples | Added | Removed | Matched by | "
                "Predicates |"
            ),
            "|---|---:|---:|---:|---|---|",
        ]
        for item in drift.changed_resources:
            label = item.resource.label or self._local_name(item.resource.iri)
            lines.append(
                "| "
                + " | ".join(
                    [
                        self._markdown_table_cell(label or item.resource.iri),
                        str(item.changed_triple_count),
                        str(item.added_triple_count),
                        str(item.removed_triple_count),
                        self._markdown_table_cell(", ".join(item.matched_by)),
                        self._markdown_table_cell(
                            ", ".join(item.predicate_displays)
                        ),
                    ]
                )
                + " |"
            )
        if drift.changed_resources_omitted_count:
            lines.append(
                "| ... | "
                f"{drift.changed_resources_omitted_count} more omitted | | | | |"
            )
        if drift.changed_resource_suggested_next_actions:
            lines.extend(["", "Suggested changed-resource review actions:", ""])
            for action in drift.changed_resource_suggested_next_actions[:action_limit]:
                args_text = json.dumps(
                    to_jsonable(action.args),
                    sort_keys=True,
                    default=str,
                )
                lines.append(f"- **{action.tool}** `{args_text}`")
        return lines
    def _snapshot_drift_triples_markdown(
        self,
        drift: StagedGraphSnapshotDrift,
        *,
        limit: int = 25,
    ) -> list[str]:
        if not drift.exact_changed_triples_available:
            return []
        lines = [
            "",
            f"#### Snapshot Drift Triples: {drift.graph_role}",
            "",
            (
                "Display values use CURIEs or local names when possible; exact "
                "raw RDF terms remain available in the apply-check payload."
            ),
            "",
        ]
        for title, triples in (
            ("Added since snapshot", drift.triples_added_since_snapshot),
            ("Removed since snapshot", drift.triples_removed_since_snapshot),
        ):
            lines.extend(
                [
                    title,
                    "",
                    "| Subject | Predicate | Object | Object kind | Datatype | Lang |",
                    "|---|---|---|---|---|---|",
                ]
            )
            if triples:
                for triple in triples[:limit]:
                    lines.append(
                        "| "
                        + " | ".join(
                            [
                                self._markdown_table_cell(triple.subject_display),
                                self._markdown_table_cell(triple.predicate_display),
                                self._markdown_table_cell(triple.object_display),
                                self._markdown_table_cell(triple.object_kind),
                                self._markdown_table_cell(triple.datatype or ""),
                                self._markdown_table_cell(triple.lang or ""),
                            ]
                        )
                        + " |"
                    )
                omitted = len(triples) - limit
                if omitted > 0:
                    lines.append(f"| ... | ... | {omitted} more omitted | | | |")
            else:
                lines.append("| (none) | | | | | |")
            lines.append("")
        return lines
    @staticmethod
    def _snapshot_evidence_graph_label(
        evidence: RevisionSnapshotEvidenceStatus,
        graph_role: str,
    ) -> str:
        if graph_role in evidence.exact_snapshot_graph_roles:
            return "complete"
        if graph_role in evidence.missing_snapshot_row_graph_roles:
            return "history-only"
        if graph_role in evidence.orphan_snapshot_row_graph_roles:
            return "snapshot-only"
        if graph_role in evidence.rdf_snapshot_graph_roles:
            return "rdf-history"
        if graph_role in evidence.stored_snapshot_graph_roles:
            return "snapshot-row-only"
        return "not recorded"
    @staticmethod
    def _snapshot_evidence_completeness_label(
        evidence: RevisionSnapshotEvidenceStatus,
    ) -> str:
        if evidence.status == "history_plus_snapshot_rows":
            if evidence.missing_snapshot_row_graph_roles:
                return "partial"
            if evidence.orphan_snapshot_row_graph_roles:
                return "partial-extra-rows"
            return "complete"
        if evidence.status == "history_only_count_digest":
            return "history-only"
        if evidence.status == "snapshot_rows_without_history":
            return "snapshot-only"
        return "missing"
    def _revision_snapshot_sensitive_matches(
        self,
        entries: list[dict[str, Any]],
        *,
        limit: int,
    ) -> tuple[int, list[ExportPreflightMatch]]:
        if limit < 0:
            raise DoxaBaseError("limit must be non-negative")
        match_count = 0
        matches: list[ExportPreflightMatch] = []
        for entry in entries:
            graph_role = str(entry["graph_role"])
            revision_iri = str(entry["revision_iri"])
            for quad in entry["quads"]:
                subject = self._redact_sensitive_context_value(str(quad["subject"]))
                predicate = self._redact_sensitive_context_value(str(quad["predicate"]))
                object_kind = str(quad.get("object_kind") or "")
                for term_position, term_kind, term_value in (
                    ("subject", "uri", quad.get("subject")),
                    ("predicate", "uri", quad.get("predicate")),
                    ("object", quad.get("object_kind"), quad.get("object")),
                ):
                    if term_kind not in {"literal", "uri"} or term_value is None:
                        continue
                    match_kind, redacted_snippet = self._sensitive_literal_match(
                        str(term_value)
                    )
                    if match_kind is None or redacted_snippet is None:
                        continue
                    match_count += 1
                    if len(matches) >= limit:
                        continue
                    matches.append(
                        ExportPreflightMatch(
                            export_part="revision_snapshots",
                            match_id=self._export_preflight_match_id(
                                export_part="revision_snapshots",
                                graph=graph_role,
                                subject=subject,
                                predicate=predicate,
                                object_kind=object_kind,
                                term_position=term_position,
                                term_kind=str(term_kind),
                                match_kind=match_kind,
                                redacted_snippet=redacted_snippet,
                                revision_iri=revision_iri,
                            ),
                            graph=graph_role,
                            subject=subject,
                            predicate=predicate,
                            object_kind=object_kind,
                            term_position=term_position,
                            term_kind=str(term_kind),
                            match_kind=match_kind,
                            redacted_snippet=redacted_snippet,
                            revision_iri=revision_iri,
                        )
                    )
        return match_count, matches
    def _shareability_hints_for_snapshot_entries(
        self,
        entries: Iterable[Mapping[str, Any]],
    ) -> list[str]:
        values: list[str] = []
        for entry in entries:
            for quad in entry.get("quads", []):
                if not isinstance(quad, MappingABC):
                    continue
                for key in ("subject", "predicate", "object"):
                    value = quad.get(key)
                    if value is not None:
                        values.append(str(value))
        return self._shareability_hints_for_values(values)
    def _shareability_hint_matches_for_snapshot_entries(
        self,
        entries: Iterable[Mapping[str, Any]],
        *,
        limit: int = DEFAULT_SHAREABILITY_HINT_MATCH_LIMIT,
    ) -> tuple[int, list[ShareabilityHintMatch]]:
        matches: list[ShareabilityHintMatch] = []
        match_count = 0
        for entry in entries:
            graph_role = str(entry.get("graph_role") or "")
            revision_iri = str(entry.get("revision_iri") or "")
            for quad in entry.get("quads", []):
                if not isinstance(quad, MappingABC):
                    continue
                subject = self._redact_sensitive_context_value(
                    str(quad.get("subject") or "")
                )
                predicate = self._redact_sensitive_context_value(
                    str(quad.get("predicate") or "")
                )
                object_kind = str(quad.get("object_kind") or "")
                for term_position, term_kind, term_value in (
                    ("subject", "uri", quad.get("subject")),
                    ("predicate", "uri", quad.get("predicate")),
                    ("object", quad.get("object_kind"), quad.get("object")),
                ):
                    if term_kind not in {"literal", "uri"} or term_value is None:
                        continue
                    for hint_code in self._shareability_hint_codes_for_value(
                        str(term_value)
                    ):
                        match_count += 1
                        if len(matches) >= limit:
                            continue
                        matches.append(
                            ShareabilityHintMatch(
                                export_part="revision_snapshots",
                                match_id=self._shareability_hint_match_id(
                                    export_part="revision_snapshots",
                                    hint_code=hint_code,
                                    graph=graph_role,
                                    subject=subject,
                                    predicate=predicate,
                                    object_kind=object_kind,
                                    term_position=term_position,
                                    term_kind=str(term_kind),
                                    revision_iri=revision_iri,
                                ),
                                hint_code=hint_code,
                                graph=graph_role,
                                subject=subject,
                                predicate=predicate,
                                object_kind=object_kind,
                                term_position=term_position,
                                term_kind=str(term_kind),
                                revision_iri=revision_iri,
                            )
                        )
        return match_count, matches
    def _snapshot_bundle_graph_roles(
        self,
        graph_roles: Iterable[str] | str | None,
    ) -> list[str]:
        roles = self._string_values("graph_roles", graph_roles)
        unknown = sorted(set(roles) - self._known_graph_names())
        if unknown:
            raise DoxaBaseError(
                f"Unknown graph role(s) in graph_roles: {', '.join(unknown)}"
            )
        return roles
    def _graph_snapshot_bundle_entries(
        self,
        *,
        revision_iris: list[str] | None,
        graph_roles: list[str] | None,
    ) -> list[dict[str, Any]]:
        revision_filter = set(revision_iris or [])
        graph_filter = set(graph_roles or [])
        rows = self._conn.execute(
            """
            SELECT revision_iri, graph_role, stored_at, triple_count, content_digest
            FROM graph_snapshot_storage
            ORDER BY revision_iri, graph_role
            """
        ).fetchall()
        entries: list[dict[str, Any]] = []
        for row in rows:
            revision_iri = row["revision_iri"]
            graph_role = row["graph_role"]
            if revision_filter and revision_iri not in revision_filter:
                continue
            if graph_filter and graph_role not in graph_filter:
                continue
            entries.append(
                {
                    "revision_iri": revision_iri,
                    "graph_role": graph_role,
                    "stored_at": row["stored_at"],
                    "triple_count": int(row["triple_count"]),
                    "content_digest": row["content_digest"],
                    "quads": [
                        {
                            "subject": subject,
                            "subject_kind": subject_kind,
                            "predicate": predicate,
                            "object": object_value,
                            "object_kind": object_kind,
                            "datatype": datatype,
                            "lang": lang,
                        }
                        for (
                            subject,
                            subject_kind,
                            predicate,
                            object_value,
                            object_kind,
                            datatype,
                            lang,
                        ) in self._graph_snapshot_storage_rows(
                            revision_iri,
                            graph_role,
                        )
                    ],
                }
            )
        return entries
    def _normalize_snapshot_bundle_entry(
        self,
        raw_snapshot: Any,
        *,
        index: int,
    ) -> dict[str, Any]:
        if not isinstance(raw_snapshot, MappingABC):
            raise DoxaBaseError(f"snapshots[{index}] must be an object")
        revision_iri = self._required_bundle_string(
            raw_snapshot,
            "revision_iri",
            index=index,
        )
        graph_role = self._required_bundle_string(
            raw_snapshot,
            "graph_role",
            index=index,
        )
        if graph_role not in self._known_graph_names():
            raise DoxaBaseError(
                f"snapshots[{index}].graph_role uses unknown graph role "
                f"{graph_role!r}"
            )
        stored_at = self._required_bundle_string(
            raw_snapshot,
            "stored_at",
            index=index,
        )
        content_digest = self._required_bundle_string(
            raw_snapshot,
            "content_digest",
            index=index,
        )
        triple_count = self._snapshot_bundle_non_negative_int(
            raw_snapshot,
            "triple_count",
            index=index,
        )
        raw_quads = raw_snapshot.get("quads")
        if not isinstance(raw_quads, list):
            raise DoxaBaseError(f"snapshots[{index}].quads must be a list")
        quads: list[dict[str, str | None]] = []
        for quad_index, raw_quad in enumerate(raw_quads, start=1):
            if not isinstance(raw_quad, MappingABC):
                raise DoxaBaseError(
                    f"snapshots[{index}].quads[{quad_index}] must be an object"
                )
            object_kind = self._snapshot_bundle_quad_kind(
                raw_quad,
                "object_kind",
                allowed={"uri", "bnode", "literal"},
                index=index,
                quad_index=quad_index,
            )
            quads.append(
                {
                    "subject": self._required_bundle_string(
                        raw_quad,
                        "subject",
                        index=index,
                        quad_index=quad_index,
                        strip=False,
                    ),
                    "subject_kind": self._snapshot_bundle_quad_kind(
                        raw_quad,
                        "subject_kind",
                        allowed={"uri", "bnode"},
                        index=index,
                        quad_index=quad_index,
                    ),
                    "predicate": self._required_bundle_string(
                        raw_quad,
                        "predicate",
                        index=index,
                        quad_index=quad_index,
                        strip=False,
                    ),
                    "object": self._snapshot_bundle_object_value(
                        raw_quad,
                        object_kind=object_kind,
                        index=index,
                        quad_index=quad_index,
                    ),
                    "object_kind": object_kind,
                    "datatype": self._optional_bundle_string(
                        raw_quad,
                        "datatype",
                        index=index,
                        quad_index=quad_index,
                    ),
                    "lang": self._optional_bundle_string(
                        raw_quad,
                        "lang",
                        index=index,
                        quad_index=quad_index,
                    ),
                }
            )
        if len(quads) != triple_count:
            raise DoxaBaseError(
                f"snapshots[{index}] triple_count is {triple_count}, "
                f"but quads has {len(quads)} row(s)"
            )
        return {
            "revision_iri": revision_iri,
            "graph_role": graph_role,
            "stored_at": stored_at,
            "triple_count": triple_count,
            "content_digest": content_digest,
            "quads": quads,
        }
    @staticmethod
    def _required_bundle_string(
        mapping: MappingABC[str, Any],
        field_name: str,
        *,
        index: int,
        quad_index: int | None = None,
        allow_empty: bool = False,
        strip: bool = True,
    ) -> str:
        value = mapping.get(field_name)
        cleaned = value.strip() if isinstance(value, str) and strip else value
        if not isinstance(value, str) or (not allow_empty and not cleaned):
            prefix = f"snapshots[{index}]"
            if quad_index is not None:
                prefix = f"{prefix}.quads[{quad_index}]"
            raise DoxaBaseError(f"{prefix}.{field_name} must be a non-empty string")
        return cleaned
    @staticmethod
    def _snapshot_bundle_quad_kind(
        mapping: MappingABC[str, Any],
        field_name: str,
        *,
        allowed: set[str],
        index: int,
        quad_index: int,
    ) -> str:
        value = DoxaBase._required_bundle_string(
            mapping,
            field_name,
            index=index,
            quad_index=quad_index,
        )
        if value not in allowed:
            allowed_values = "', '".join(sorted(allowed))
            raise DoxaBaseError(
                f"snapshots[{index}].quads[{quad_index}].{field_name} "
                f"must be one of '{allowed_values}'"
            )
        return value
    @staticmethod
    def _snapshot_bundle_object_value(
        mapping: MappingABC[str, Any],
        *,
        object_kind: str,
        index: int,
        quad_index: int,
    ) -> str:
        value = DoxaBase._required_bundle_string(
            mapping,
            "object",
            index=index,
            quad_index=quad_index,
            allow_empty=True,
            strip=False,
        )
        if object_kind != "literal" and not value.strip():
            raise DoxaBaseError(
                f"snapshots[{index}].quads[{quad_index}].object must be "
                f"non-empty when object_kind is '{object_kind}'"
            )
        return value
    @staticmethod
    def _optional_bundle_string(
        mapping: MappingABC[str, Any],
        field_name: str,
        *,
        index: int,
        quad_index: int,
    ) -> str | None:
        value = mapping.get(field_name)
        if value is None:
            return None
        if not isinstance(value, str):
            raise DoxaBaseError(
                f"snapshots[{index}].quads[{quad_index}].{field_name} "
                "must be a string or null"
            )
        return value
    @staticmethod
    def _snapshot_bundle_non_negative_int(
        mapping: MappingABC[str, Any],
        field_name: str,
        *,
        index: int,
    ) -> int:
        value = mapping.get(field_name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise DoxaBaseError(
                f"snapshots[{index}].{field_name} must be a non-negative integer"
            )
        return value
    def _insert_graph_snapshot_bundle_entry(
        self,
        snapshot: dict[str, Any],
        *,
        replace: bool,
    ) -> None:
        revision_iri = snapshot["revision_iri"]
        graph_role = snapshot["graph_role"]
        if replace:
            self._conn.execute(
                """
                DELETE FROM graph_snapshot_storage
                WHERE revision_iri = ? AND graph_role = ?
                """,
                (revision_iri, graph_role),
            )
        self._conn.execute(
            """
            DELETE FROM graph_snapshot_quads
            WHERE revision_iri = ? AND graph_role = ?
            """,
            (revision_iri, graph_role),
        )
        self._conn.execute(
            """
            INSERT OR REPLACE INTO graph_snapshot_storage
                (revision_iri, graph_role, stored_at, triple_count, content_digest)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                revision_iri,
                graph_role,
                snapshot["stored_at"],
                snapshot["triple_count"],
                snapshot["content_digest"],
            ),
        )
        self._conn.executemany(
            """
            INSERT OR IGNORE INTO graph_snapshot_quads
                (
                    revision_iri,
                    graph_role,
                    subject,
                    subject_kind,
                    predicate,
                    object,
                    object_kind,
                    datatype,
                    lang,
                    created_at
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    revision_iri,
                    graph_role,
                    quad["subject"],
                    quad["subject_kind"],
                    quad["predicate"],
                    quad["object"],
                    quad["object_kind"],
                    quad["datatype"],
                    quad["lang"],
                    snapshot["stored_at"],
                )
                for quad in snapshot["quads"]
            ],
        )
    def _store_graph_snapshot_rows(
        self,
        revision_iri: str,
        *,
        snapshot_rows: dict[str, list[GraphStorageRow]],
        snapshot_counts: dict[str, int],
        snapshot_digests: dict[str, str],
    ) -> None:
        stored_at = _now()
        for graph_role, rows in snapshot_rows.items():
            self._conn.execute(
                """
                DELETE FROM graph_snapshot_quads
                WHERE revision_iri = ? AND graph_role = ?
                """,
                (revision_iri, graph_role),
            )
            self._conn.execute(
                """
                INSERT OR REPLACE INTO graph_snapshot_storage
                    (revision_iri, graph_role, stored_at, triple_count, content_digest)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    revision_iri,
                    graph_role,
                    stored_at,
                    snapshot_counts[graph_role],
                    snapshot_digests[graph_role],
                ),
            )
            self._conn.executemany(
                """
                INSERT OR IGNORE INTO graph_snapshot_quads
                    (
                        revision_iri,
                        graph_role,
                        subject,
                        subject_kind,
                        predicate,
                        object,
                        object_kind,
                        datatype,
                        lang,
                        created_at
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        revision_iri,
                        graph_role,
                        subject,
                        subject_kind,
                        predicate,
                        object,
                        object_kind,
                        datatype,
                        lang,
                        stored_at,
                    )
                    for (
                        subject,
                        subject_kind,
                        predicate,
                        object,
                        object_kind,
                        datatype,
                        lang,
                    ) in rows
                ],
            )
        self._conn.commit()
    def _snapshot_triple_diff(
        self,
        revision_iri: str,
        graph_role: str,
    ) -> tuple[list[GraphTripleDescription], list[GraphTripleDescription]] | None:
        if not self._graph_snapshot_storage_exists(revision_iri, graph_role):
            return None
        snapshot_rows = set(self._graph_snapshot_storage_rows(revision_iri, graph_role))
        current_rows = set(self._graph_storage_rows(graph_role))
        added_rows = self._sort_graph_storage_rows(current_rows - snapshot_rows)
        removed_rows = self._sort_graph_storage_rows(snapshot_rows - current_rows)
        return (
            [self._graph_triple_description(row) for row in added_rows],
            [self._graph_triple_description(row) for row in removed_rows],
        )
    def _graph_snapshot_storage_exists(self, revision_iri: str, graph_role: str) -> bool:
        row = self._conn.execute(
            """
            SELECT 1
            FROM graph_snapshot_storage
            WHERE revision_iri = ? AND graph_role = ?
            """,
            (revision_iri, graph_role),
        ).fetchone()
        return row is not None
    def _graph_snapshot_storage_metadata(
        self,
        revision_iri: str,
        graph_role: str,
    ) -> dict[str, Any] | None:
        row = self._conn.execute(
            """
            SELECT stored_at, triple_count, content_digest
            FROM graph_snapshot_storage
            WHERE revision_iri = ? AND graph_role = ?
            """,
            (revision_iri, graph_role),
        ).fetchone()
        if row is None:
            return None
        return {
            "stored_at": row["stored_at"],
            "triple_count": int(row["triple_count"]),
            "content_digest": row["content_digest"],
        }
    def _graph_snapshot_storage_graph_roles(self, revision_iri: str) -> list[str]:
        rows = self._conn.execute(
            """
            SELECT graph_role
            FROM graph_snapshot_storage
            WHERE revision_iri = ?
            ORDER BY graph_role
            """,
            (revision_iri,),
        ).fetchall()
        return [row["graph_role"] for row in rows]
    def _graph_snapshot_storage_rows(
        self,
        revision_iri: str,
        graph_role: str,
    ) -> list[GraphStorageRow]:
        rows = self._conn.execute(
            """
            SELECT
                subject,
                subject_kind,
                predicate,
                object,
                object_kind,
                datatype,
                lang
            FROM graph_snapshot_quads
            WHERE revision_iri = ? AND graph_role = ?
            ORDER BY
                subject,
                subject_kind,
                predicate,
                object,
                object_kind,
                COALESCE(datatype, ''),
                COALESCE(lang, '')
            """,
            (revision_iri, graph_role),
        ).fetchall()
        return [
            (
                row["subject"],
                row["subject_kind"],
                row["predicate"],
                row["object"],
                row["object_kind"],
                row["datatype"],
                row["lang"],
            )
            for row in rows
        ]
    def _graph_revision_snapshots(
        self,
        revision_iri: str,
        graphs: list[str],
    ) -> list[GraphSnapshotDescription]:
        snapshots: list[GraphSnapshotDescription] = []
        for snapshot_iri in self._objects(graphs, revision_iri, "rc:hasGraphSnapshot"):
            graph_role = self._first_object(graphs, snapshot_iri, "rc:graphRole")
            triple_count = self._int_object(graphs, snapshot_iri, "rc:tripleCount")
            content_digest = self._first_object(
                graphs,
                snapshot_iri,
                "rc:contentDigest",
            )
            if graph_role is None or triple_count is None:
                continue
            snapshots.append(
                GraphSnapshotDescription(
                    graph_role=graph_role,
                    triple_count=triple_count,
                    content_digest=content_digest,
                )
            )
        return sorted(snapshots, key=lambda snapshot: snapshot.graph_role)
