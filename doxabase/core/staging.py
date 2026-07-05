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
            raise DoxaBaseError(
                "staging a graph revision requires at least one patch "
                "(additions or removals)"
            )

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
                     tool="doxabase.stage_revision",
                     args={"kind": "map_assertion", "spec": arguments},
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
                recommended_action_kind = "stage_revision_map_assertion"
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
                     tool="doxabase.stage_revision",
                     args={"kind": "map_assertion", "spec": arguments},
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
        arguments: dict[str, Any] = {
            "revision_iris": staged_revision_iri,
            "dry_run": True,
        }
        if validation_scope is not None:
            arguments["validation_scope"] = validation_scope
        return SuggestedNextAction(
                   tool="doxabase.restage_staged_revision",
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
                   tool="doxabase.stage_revision",
                   args={"kind": "map_assertion", "spec": arguments},
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
                else "stage_revision"
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
                "patch or stage_revision map_assertion replacement if the "
                "staged value should replace the current value."
            )
        if added_values:
            return (
                "rc:rowSemantics allows one value; this staged patch adds "
                f"{self._compact_value_list(added_values)}, but the candidate "
                "graph has multiple rowSemantics values. Choose one row "
                "framing and use a removal+addition patch or "
                "stage_revision map_assertion replacement when changing an "
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
