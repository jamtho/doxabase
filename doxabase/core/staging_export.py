"""Staged revision export payloads and reviewer summary markdown.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via StagingExportMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class StagingExportMixin:
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
                "Staged revision review exports only accept staged patch "
                f"revisions; '{iri}' is an applied revision event. Use "
                "describe_revision (default or aspect='lineage') for the "
                "applied event, or pass the applied event's staged source IRI "
                f"'{applied_source}'."
            )
        raise DoxaBaseError(
            "Staged revision review exports only accept staged patch "
            f"revisions; graph revision '{iri}' has no staged patch entries. "
            "Use describe_revision for revision metadata instead."
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
