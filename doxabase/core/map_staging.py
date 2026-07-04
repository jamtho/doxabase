"""Map assertion change drafting and staging.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via MapStagingMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class MapStagingMixin:
    def _prepare_map_assertion_change(
        self,
        subject: str,
        predicate: str,
        object: str | None,
        rationale: str,
        *,
        change_kind: TypingLiteral["add", "remove", "replace"] = "replace",
        graph: TypingLiteral["map"] = "map",
        object_kind: TypingLiteral["auto", "iri", "uri", "literal"] = "auto",
        object_datatype: str | None = None,
        object_lang: str | None = None,
        summary: str | None = None,
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
        limit: int = 20,
    ) -> _MapAssertionChangePrepared:
        if graph != "map":
            raise DoxaBaseError("stage_map_assertion_change currently targets map only")
        kind = change_kind.strip().lower()
        if kind not in {"add", "remove", "replace"}:
            raise DoxaBaseError("change_kind must be one of 'add', 'remove', or 'replace'")
        rationale_value = rationale.strip()
        if not rationale_value:
            raise DoxaBaseError("rationale must not be empty")
        if kind in {"add", "replace"} and object is None:
            raise DoxaBaseError(f"change_kind '{kind}' requires an object")
        self._ensure_revision_stance(self.expand_iri(stance))
        new_revision_iri = (
            self._required_iri("revision_iri", revision_iri)
            if revision_iri is not None
            else "urn:doxabase:draft-map-assertion-change"
        )
        if restages_revision is not None:
            self._validated_restage_successor_source(
                restages_revision,
                new_revision_iri=new_revision_iri,
            )

        support = self.describe_assertion_support(
            subject,
            predicate,
            object,
            graph=graph,
            object_kind=object_kind,
            object_datatype=object_datatype,
            object_lang=object_lang,
            limit=limit,
        )
        subject_iri = support.subject.iri
        predicate_iri = support.predicate
        object_filter = self._assertion_object_filter(
            object,
            object_kind,
            object_datatype=object_datatype,
            object_lang=object_lang,
        )
        requested_node = (
            self._node_from_object_filter(object_filter)
            if object_filter is not None
            else None
        )

        addition_triples: list[tuple[Identifier, URIRef, Node]] = []
        removal_triples: list[ResourceTriple] = []
        if kind == "add":
            if support.assertion_present:
                raise DoxaBaseError(
                    "Exact assertion is already present; no add patch was staged"
                )
            if requested_node is None:
                raise DoxaBaseError("Internal assertion add missing object node")
            addition_triples.append((URIRef(subject_iri), URIRef(predicate_iri), requested_node))
        elif kind == "remove":
            removal_triples = (
                support.matching_triples
                if object_filter is not None
                else support.same_subject_predicate_triples
            )
            if not removal_triples:
                raise DoxaBaseError(
                    "No matching current assertion triples were found to remove"
                )
        else:
            removal_triples = [
                triple
                for triple in support.same_subject_predicate_triples
                if object_filter is None
                or not self._resource_triple_matches_filter(triple, object_filter)
            ]
            if requested_node is None:
                raise DoxaBaseError("Internal assertion replace missing object node")
            if not removal_triples and support.assertion_present:
                raise DoxaBaseError(
                    "Exact assertion is already the only current value; no replace patch was staged"
                )
            addition_triples.append((URIRef(subject_iri), URIRef(predicate_iri), requested_node))

        additions = (
            [
                {
                    "graph": graph,
                    "content": self._patch_content_from_triples(addition_triples),
                }
            ]
            if addition_triples
            else []
        )
        removals = (
            [
                {
                    "graph": graph,
                    "content": self._patch_content_from_resource_triples(removal_triples),
                }
            ]
            if removal_triples
            else []
        )
        summary_value = summary or self._map_assertion_change_summary(
            kind,
            support,
        )
        merged_review_note = self._map_assertion_change_review_note(
            support,
            change_kind=kind,
            user_review_note=review_note,
        )
        recommendation = review_recommendation or (
            "Review assertion support, caveat scopes, route summaries, and impact "
            "entries before applying this staged map assertion change."
        )
        anchors = self._merge_iri_values(
            revision_anchors,
            self._assertion_revision_anchors(support),
        )
        supporting_observation_values = self._merge_iri_values(
            supporting_observations,
            [item.iri for item in support.related_observations],
        )
        supporting_claim_values = self._merge_iri_values(
            supporting_claims,
            [item.iri for item in support.related_claims],
        )
        supporting_pattern_values = self._merge_iri_values(
            supporting_patterns,
            self._assertion_auto_supporting_pattern_iris(support),
        )
        evidence_values = self._merge_iri_values(
            evidence,
            [item.iri for item in support.related_evidence],
        )
        object_value = (
            support.requested_object.value
            if support.requested_object is not None
            else None
        )
        resolved_object_kind = (
            support.requested_object.value_kind
            if support.requested_object is not None
            else object_kind
        )
        resolved_object_datatype = (
            support.requested_object.datatype
            if support.requested_object is not None
            else None
        )
        resolved_object_lang = (
            support.requested_object.lang
            if support.requested_object is not None
            else None
        )
        stage_arguments = self._map_assertion_change_stage_arguments(
            subject=subject_iri,
            predicate=predicate_iri,
            object_value=object_value,
            rationale=rationale_value,
            change_kind=kind,
            graph=graph,
            object_kind=object_kind,
            object_datatype=resolved_object_datatype,
            object_lang=resolved_object_lang,
            summary=summary_value,
            stance=stance,
            revision_type=revision_type,
            included_graphs=included_graphs,
            revision_iri=revision_iri,
            created_at=created_at,
            created_by=created_by,
            supporting_observations=supporting_observation_values,
            supporting_claims=supporting_claim_values,
            supporting_patterns=supporting_pattern_values,
            revision_anchors=anchors,
            evidence=evidence_values,
            alternative_to=alternative_to,
            restages_revision=restages_revision,
            review_note=review_note,
            review_recommendation=review_recommendation,
            validation_scope=validation_scope,
            limit=limit,
        )

        return _MapAssertionChangePrepared(
            change_kind=kind,
            graph=graph,
            subject=subject_iri,
            predicate=predicate_iri,
            object_value=object_value,
            object_kind=resolved_object_kind,
            object_datatype=resolved_object_datatype,
            object_lang=resolved_object_lang,
            rationale=rationale_value,
            additions=additions,
            removals=removals,
            summary=summary_value,
            review_note=merged_review_note,
            review_recommendation=recommendation,
            assertion_support=support,
            assertion_present_before=support.assertion_present,
            current_values_before=support.same_subject_predicate_triples,
            supporting_observations=supporting_observation_values,
            supporting_claims=supporting_claim_values,
            supporting_patterns=supporting_pattern_values,
            revision_anchors=anchors,
            evidence=evidence_values,
            stage_arguments=stage_arguments,
        )
    def _map_assertion_change_stage_arguments(
        self,
        *,
        subject: str,
        predicate: str,
        object_value: str | None,
        rationale: str,
        change_kind: str,
        graph: str,
        object_kind: str,
        object_datatype: str | None,
        object_lang: str | None,
        summary: str,
        stance: str,
        revision_type: str,
        included_graphs: Iterable[str] | str | None,
        revision_iri: str | None,
        created_at: datetime | str | None,
        created_by: str | None,
        supporting_observations: list[str],
        supporting_claims: list[str],
        supporting_patterns: list[str],
        revision_anchors: list[str],
        evidence: list[str],
        alternative_to: str | None,
        restages_revision: str | None,
        review_note: str | None,
        review_recommendation: str | None,
        validation_scope: str,
        limit: int,
    ) -> dict[str, Any]:
        arguments: dict[str, Any] = {
            "subject": subject,
            "predicate": predicate,
            "object": object_value,
            "rationale": rationale,
            "change_kind": change_kind,
            "graph": graph,
            "object_kind": object_kind,
            "summary": summary,
            "validation_scope": validation_scope,
        }
        if object_datatype is not None:
            arguments["object_datatype"] = object_datatype
        if object_lang is not None:
            arguments["object_lang"] = object_lang
        if stance != "rc:CandidateRevision":
            arguments["stance"] = stance
        if revision_type != "rc:StagedRevision":
            arguments["revision_type"] = revision_type
        if included_graphs is not None:
            arguments["included_graphs"] = self._string_values(
                "included_graphs",
                included_graphs,
            )
        if revision_iri is not None:
            arguments["revision_iri"] = revision_iri
        if created_at is not None:
            arguments["created_at"] = (
                created_at.isoformat() if isinstance(created_at, datetime) else created_at
            )
        if created_by is not None:
            arguments["created_by"] = created_by
        if supporting_observations:
            arguments["supporting_observations"] = supporting_observations
        if supporting_claims:
            arguments["supporting_claims"] = supporting_claims
        if supporting_patterns:
            arguments["supporting_patterns"] = supporting_patterns
        if revision_anchors:
            arguments["revision_anchors"] = revision_anchors
        if evidence:
            arguments["evidence"] = evidence
        if alternative_to is not None:
            arguments["alternative_to"] = alternative_to
        if restages_revision is not None:
            arguments["restages_revision"] = restages_revision
        if review_note is not None:
            arguments["review_note"] = review_note
        if review_recommendation is not None:
            arguments["review_recommendation"] = review_recommendation
        if limit != 20:
            arguments["limit"] = limit
        return arguments
    def draft_map_assertion_change(
        self,
        subject: str,
        predicate: str,
        object: str | None,
        rationale: str,
        *,
        change_kind: TypingLiteral["add", "remove", "replace"] = "replace",
        graph: TypingLiteral["map"] = "map",
        object_kind: TypingLiteral["auto", "iri", "uri", "literal"] = "auto",
        object_datatype: str | None = None,
        object_lang: str | None = None,
        summary: str | None = None,
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
        limit: int = 20,
    ) -> DraftMapAssertionChangeRecord:
        prepared = self._prepare_map_assertion_change(
            subject=subject,
            predicate=predicate,
            object=object,
            rationale=rationale,
            change_kind=change_kind,
            graph=graph,
            object_kind=object_kind,
            object_datatype=object_datatype,
            object_lang=object_lang,
            summary=summary,
            stance=stance,
            revision_type=revision_type,
            included_graphs=included_graphs,
            revision_iri=revision_iri,
            created_at=created_at,
            created_by=created_by,
            supporting_observations=supporting_observations,
            supporting_claims=supporting_claims,
            supporting_patterns=supporting_patterns,
            revision_anchors=revision_anchors,
            evidence=evidence,
            alternative_to=alternative_to,
            restages_revision=restages_revision,
            review_note=review_note,
            review_recommendation=review_recommendation,
            validation_scope=validation_scope,
            limit=limit,
        )
        parsed_patches = self._parse_staged_patch_specs(
            additions=prepared.additions,
            removals=prepared.removals,
        )
        preview = self._preview_staged_graph_patches(
            parsed_patches,
            validation_scope=validation_scope,
            revision_has_support_metadata=bool(
                prepared.supporting_observations
                or prepared.supporting_claims
                or prepared.supporting_patterns
                or prepared.evidence
            ),
        )
        impacts = self._staged_revision_impacts(
            revision_iri="urn:doxabase:draft-map-assertion-change",
            patches=preview.patch_descriptions,
            lookup_graphs=self._lookup_graphs(self._expand_graphs(["all"])),
        )
        judgement_panel = self._map_assertion_change_judgement_panel(
            prepared.assertion_support,
            change_kind=prepared.change_kind,
            recommendation=prepared.review_recommendation,
            impacts=impacts,
        )
        suggested_next_actions = self._draft_map_assertion_change_next_actions(
            prepared,
            judgement_panel,
            limit=limit,
        )
        return DraftMapAssertionChangeRecord(
            result_kind="draft_map_assertion_change",
            change_kind=prepared.change_kind,
            graph=prepared.graph,
            subject=prepared.subject,
            predicate=prepared.predicate,
            object_value=prepared.object_value,
            object_kind=prepared.object_kind,
            object_datatype=prepared.object_datatype,
            object_lang=prepared.object_lang,
            assertion_present_before=prepared.assertion_present_before,
            current_values_before=prepared.current_values_before,
            additions=prepared.additions,
            removals=prepared.removals,
            changed_graphs=preview.changed_graphs,
            patches=preview.patch_descriptions,
            impacts=impacts,
            validation_scope=preview.validation.scope,
            validation_conforms=preview.validation.conforms,
            validation_result_count=preview.validation.result_count,
            validation_results=preview.validation.results,
            validation_report_text=preview.validation.report_text,
            assertion_support=prepared.assertion_support,
            judgement_panel=judgement_panel,
            review_note=prepared.review_note,
            review_recommendation=prepared.review_recommendation,
            stage_arguments=prepared.stage_arguments,
            suggested_next_actions=suggested_next_actions,
        )
    def _draft_map_assertion_change_next_actions(
        self,
        prepared: _MapAssertionChangePrepared,
        judgement_panel: MapAssertionJudgementPanel,
        *,
        limit: int,
    ) -> list[SuggestedNextAction]:
        stage_action = SuggestedNextAction(
                           tool="doxabase.stage_map_assertion_change",
                           args=prepared.stage_arguments,
                           reason="Stage this reviewed map assertion change only after the draft "
                "support, impacts, validation preview, and judgement panel still "
                "justify the write.",
                       )
        if not self._draft_map_assertion_change_requires_support_review(
            judgement_panel
        ):
            return [stage_action]

        review_arguments = self._draft_assertion_support_review_arguments(
            prepared,
            limit=limit,
        )
        review_action = SuggestedNextAction(
                            tool="doxabase.describe_resource",
                            args=review_arguments,
                            reason="This draft is high-risk or marked do-not-stage; inspect support "
                "routes, caveat scopes, and current-value rationale before any "
                "write. Mechanical validation means the patch can replay, not that "
                "the semantic change is good.",
                        )
        override_stage_action = replace(
            stage_action,
            reason=(
                "Override the draft review warning only after explicitly deciding "
                "the high-risk or do-not-stage judgement is outweighed by current "
                "project evidence."
            ),
        )
        return [review_action, override_stage_action]
    @staticmethod
    def _draft_map_assertion_change_requires_support_review(
        judgement_panel: MapAssertionJudgementPanel,
    ) -> bool:
        recommendation = (judgement_panel.recommendation or "").strip().lower()
        return judgement_panel.semantic_risk_level == "high" or recommendation in {
            "do_not_stage",
            "do-not-stage",
            "do not stage",
        }
    def stage_map_assertion_change(
        self,
        subject: str,
        predicate: str,
        object: str | None,
        rationale: str,
        *,
        change_kind: TypingLiteral["add", "remove", "replace"] = "replace",
        graph: TypingLiteral["map"] = "map",
        object_kind: TypingLiteral["auto", "iri", "uri", "literal"] = "auto",
        object_datatype: str | None = None,
        object_lang: str | None = None,
        summary: str | None = None,
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
        profile_route_sources: Iterable[Mapping[str, Any]]
        | Mapping[str, Any]
        | None = None,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ] = "all",
        limit: int = 20,
    ) -> StagedMapAssertionChangeRecord:
        profile_route_source_values = self._explicit_profile_route_sources(
            profile_route_sources
        )
        prepared = self._prepare_map_assertion_change(
            subject=subject,
            predicate=predicate,
            object=object,
            rationale=rationale,
            change_kind=change_kind,
            graph=graph,
            object_kind=object_kind,
            object_datatype=object_datatype,
            object_lang=object_lang,
            summary=summary,
            stance=stance,
            revision_type=revision_type,
            included_graphs=included_graphs,
            revision_iri=revision_iri,
            created_at=created_at,
            created_by=created_by,
            supporting_observations=supporting_observations,
            supporting_claims=supporting_claims,
            supporting_patterns=supporting_patterns,
            revision_anchors=revision_anchors,
            evidence=evidence,
            alternative_to=alternative_to,
            restages_revision=restages_revision,
            review_note=review_note,
            review_recommendation=review_recommendation,
            validation_scope=validation_scope,
            limit=limit,
        )
        staged = self.stage_graph_revision(
            summary=prepared.summary,
            rationale=prepared.rationale,
            additions=prepared.additions,
            removals=prepared.removals,
            stance=stance,
            revision_type=revision_type,
            included_graphs=included_graphs,
            revision_iri=revision_iri,
            created_at=created_at,
            created_by=created_by,
            supporting_observations=prepared.supporting_observations,
            supporting_claims=prepared.supporting_claims,
            supporting_patterns=prepared.supporting_patterns,
            revision_anchors=prepared.revision_anchors,
            evidence=prepared.evidence,
            alternative_to=alternative_to,
            restages_revision=restages_revision,
            review_note=prepared.review_note,
            review_recommendation=prepared.review_recommendation,
            validation_scope=validation_scope,
        )
        extra_route_source_triples = self._record_profile_insight_route_sources(
            staged.revision_iri,
            profile_route_source_values,
        )
        if extra_route_source_triples:
            staged = replace(
                staged,
                triples=staged.triples + extra_route_source_triples,
            )
        staged_description = self.describe_staged_revision(staged.revision_iri)
        judgement_panel = self._map_assertion_change_judgement_panel(
            prepared.assertion_support,
            change_kind=prepared.change_kind,
            recommendation=prepared.review_recommendation,
            impacts=staged_description.impacts,
        )
        return StagedMapAssertionChangeRecord(
            revision_iri=staged.revision_iri,
            change_kind=prepared.change_kind,
            graph=prepared.graph,
            subject=prepared.subject,
            predicate=prepared.predicate,
            object_value=prepared.object_value,
            object_kind=prepared.object_kind,
            object_datatype=prepared.object_datatype,
            object_lang=prepared.object_lang,
            assertion_present_before=prepared.assertion_present_before,
            current_values_before=prepared.current_values_before,
            additions=prepared.additions,
            removals=prepared.removals,
            assertion_support=prepared.assertion_support,
            staged_revision=staged,
            judgement_panel=judgement_panel,
            review_note=prepared.review_note,
            review_recommendation=prepared.review_recommendation,
            profile_route_source_count=len(profile_route_source_values),
        )
    def _map_assertion_change_summary(
        self,
        change_kind: str,
        support: AssertionSupportDescription,
    ) -> str:
        subject_label = (
            support.subject.label
            or support.subject.column_name
            or support.subject.iri
        )
        predicate_label = support.predicate_label or self._local_name(support.predicate)
        if support.requested_object is None:
            return f"{change_kind.title()} map assertion(s): {subject_label} {predicate_label}"
        object_label = (
            support.requested_object.value_label
            or self._local_name(support.requested_object.value)
            or support.requested_object.value
        )
        return (
            f"{change_kind.title()} map assertion: "
            f"{subject_label} {predicate_label} {object_label}"
        )
    def _map_assertion_change_review_note(
        self,
        support: AssertionSupportDescription,
        *,
        change_kind: str,
        user_review_note: str | None,
    ) -> str:
        judgement_current_values = [
            self._map_assertion_judgement_value_from_triple(triple)
            for triple in support.same_subject_predicate_triples
        ]
        judgement_proposed_value = (
            self._map_assertion_judgement_value_from_assertion_value(
                support.requested_object
            )
            if support.requested_object is not None
            else None
        )
        value_type_context = self._map_assertion_value_type_context(
            support,
            current_values=judgement_current_values,
            proposed_value=judgement_proposed_value,
        )
        current_value_rationale = self._map_assertion_current_value_rationale(
            support,
            value_type_context=value_type_context,
        )
        current_values = [
            triple.object_label or self._local_name(triple.object) or triple.object
            for triple in support.same_subject_predicate_triples
        ]
        route_notes = [
            self._map_assertion_review_route_note(support, summary)
            for summary in self._ranked_panel_route_summaries(support)[:5]
        ]
        caveat_notes = [
            (
                f"{link.caveat.label or link.caveat.iri} "
                f"[scope={link.scope}, via={link.via_resource.label or link.via_resource.iri}]"
            )
            for link in support.nearby_caveat_links[:5]
        ]
        context_values = [
            (
                f"{triple.subject_label or self._local_name(triple.subject) or triple.subject} "
                f"{triple.predicate_label or self._local_name(triple.predicate) or triple.predicate} "
                f"{triple.object_label or self._local_name(triple.object) or triple.object}"
            )
            for triple in support.nearby_context_triples[:5]
        ]
        lines = [
            f"Staged map assertion change kind: {change_kind}.",
            f"Exact assertion present before staging: {support.assertion_present}.",
            "Current same-subject/predicate value(s): "
            + (", ".join(current_values) if current_values else "(none)."),
        ]
        if support.absence_note:
            lines.append(f"Absence note: {support.absence_note}")
        if value_type_context:
            lines.append(
                "Value-type context: "
                + " | ".join(context.note for context in value_type_context[:5])
            )
        if current_value_rationale:
            lines.append(
                "Why current value may be intentional: "
                + " | ".join(current_value_rationale)
            )
        if caveat_notes:
            lines.append("Nearby caveats by scope: " + " | ".join(caveat_notes))
        if route_notes:
            lines.append("Related route summaries: " + " | ".join(route_notes))
        if context_values:
            lines.append("Nearby layout/path context: " + " | ".join(context_values))
        if user_review_note:
            lines.append(f"User/agent review note: {user_review_note.strip()}")
        return "\n".join(lines)
    def _map_assertion_review_route_note(
        self,
        support: AssertionSupportDescription,
        summary: AssertionSupportRouteSummary,
    ) -> str:
        note = f"{summary.rank}. {summary.route_note}"
        if self._map_assertion_route_is_generic_value_only(support, summary):
            note += " [weak: generic shared-value match only]"
        return note
    def _map_assertion_change_judgement_panel(
        self,
        support: AssertionSupportDescription,
        *,
        change_kind: str,
        recommendation: str | None,
        impacts: list[StagedRevisionImpact],
    ) -> MapAssertionJudgementPanel:
        current_values = [
            self._map_assertion_judgement_value_from_triple(triple)
            for triple in support.same_subject_predicate_triples
        ]
        proposed_value = (
            self._map_assertion_judgement_value_from_assertion_value(
                support.requested_object
            )
            if support.requested_object is not None
            else None
        )
        removed_value = None
        if change_kind == "remove":
            if support.matching_triples:
                removed_value = self._map_assertion_judgement_value_from_triple(
                    support.matching_triples[0]
                )
            else:
                removed_value = proposed_value
        value_type_context = self._map_assertion_value_type_context(
            support,
            current_values=current_values,
            proposed_value=proposed_value,
        )
        caveats = [
            self._map_assertion_judgement_caveat(link)
            for link in support.nearby_caveat_links[:5]
        ]
        strongest_routes = [
            self._map_assertion_judgement_route(support, summary)
            for summary in self._ranked_panel_route_summaries(support)[:5]
        ]
        judgement_impacts = [
            self._map_assertion_judgement_impact(impact)
            for impact in impacts[:5]
        ]
        why_current_value_may_be_intentional = (
            self._map_assertion_current_value_rationale(
                support,
                value_type_context=value_type_context,
            )
        )
        safety_notes = self._map_assertion_judgement_safety_notes(
            support,
            value_type_context=value_type_context,
            change_kind=change_kind,
            impacts=impacts,
        )
        semantic_risk_level, semantic_risk_reasons = (
            self._map_assertion_semantic_risk(
                support,
                value_type_context=value_type_context,
                impacts=impacts,
                why_current_value_may_be_intentional=(
                    why_current_value_may_be_intentional
                ),
                change_kind=change_kind,
            )
        )
        return MapAssertionJudgementPanel(
            headline=self._map_assertion_judgement_headline(
                support,
                change_kind=change_kind,
                current_values=current_values,
                proposed_value=proposed_value,
            ),
            recommendation=recommendation,
            assertion_present_before=support.assertion_present,
            current_values=current_values,
            proposed_value=proposed_value,
            target_value=proposed_value,
            removed_value=removed_value,
            absence_note=support.absence_note,
            semantic_risk_level=semantic_risk_level,
            semantic_risk_reasons=semantic_risk_reasons,
            value_type_context=value_type_context,
            why_current_value_may_be_intentional=why_current_value_may_be_intentional,
            caveats=caveats,
            strongest_routes=strongest_routes,
            impacts=judgement_impacts,
            safety_notes=safety_notes,
        )
    def _map_assertion_judgement_value_from_triple(
        self,
        triple: ResourceTriple,
    ) -> MapAssertionJudgementValue:
        return MapAssertionJudgementValue(
            value=triple.object,
            label=self._map_assertion_judgement_value_label(
                triple.object,
                triple.object_kind,
                triple.object_label,
            ),
            value_kind="iri" if triple.object_kind == "uri" else triple.object_kind,
            datatype=triple.object_datatype,
            lang=triple.object_lang,
        )
    def _map_assertion_judgement_value_from_assertion_value(
        self,
        value: AssertionValue,
    ) -> MapAssertionJudgementValue:
        return MapAssertionJudgementValue(
            value=value.value,
            label=self._map_assertion_judgement_value_label(
                value.value,
                value.value_kind,
                value.value_label,
            ),
            value_kind=value.value_kind,
            datatype=value.datatype,
            lang=value.lang,
            caveat=value.caveat,
        )
    def _map_assertion_judgement_value_from_impact_value(
        self,
        value: StagedRevisionImpactValue,
    ) -> MapAssertionJudgementValue:
        return MapAssertionJudgementValue(
            value=value.value,
            label=self._map_assertion_judgement_value_label(
                value.value,
                value.value_kind,
                value.value_label,
            ),
            value_kind=value.value_kind,
            caveat=value.caveat,
        )
    def _map_assertion_judgement_value_label(
        self,
        value: str,
        value_kind: str,
        label: str | None,
    ) -> str | None:
        if label is not None:
            return label
        if value_kind in {"iri", "uri"}:
            return self._local_name(value)
        return None
    def _map_assertion_value_type_context(
        self,
        support: AssertionSupportDescription,
        *,
        current_values: list[MapAssertionJudgementValue],
        proposed_value: MapAssertionJudgementValue | None,
    ) -> list[MapAssertionJudgementValueTypeContext]:
        physical_type_predicate = self.expand_iri("rc:physicalType")
        value_type_predicate = self.expand_iri("rc:valueType")
        if support.predicate not in {
            physical_type_predicate,
            value_type_predicate,
        }:
            return []
        lookup_graphs = self._lookup_graphs(self._expand_graphs(["all"]))
        if support.predicate == value_type_predicate:
            return self._map_assertion_value_type_replacement_context(
                support,
                current_values=current_values,
                proposed_value=proposed_value,
                lookup_graphs=lookup_graphs,
            )

        current_physical_type_values = {
            value.value
            for value in current_values
            if value.value_kind in {"iri", "uri"}
        }
        proposed_physical_type = (
            proposed_value.value
            if proposed_value is not None
            and proposed_value.value_kind in {"iri", "uri"}
            else None
        )
        contexts: list[MapAssertionJudgementValueTypeContext] = []
        for value_type_iri in self._objects(
            lookup_graphs,
            support.subject.iri,
            "rc:valueType",
        ):
            required_iri = self._first_object(
                lookup_graphs,
                value_type_iri,
                "rc:requiredPhysicalType",
            )
            required_value = (
                self._map_assertion_judgement_resource_value(
                    lookup_graphs,
                    required_iri,
                )
                if required_iri is not None
                else None
            )
            current_matches = (
                required_iri in current_physical_type_values
                if required_iri is not None
                else None
            )
            proposed_matches = (
                proposed_physical_type == required_iri
                if required_iri is not None and proposed_physical_type is not None
                else None
            )
            contexts.append(
                MapAssertionJudgementValueTypeContext(
                    value_type=self._resource_summary(
                        lookup_graphs,
                        value_type_iri,
                        display_label=True,
                    ),
                    required_physical_type=required_value,
                    current_physical_type_matches=current_matches,
                    proposed_physical_type_matches=proposed_matches,
                    note=self._map_assertion_value_type_note(
                        value_type_iri=value_type_iri,
                        required_physical_type=required_value,
                        current_matches=current_matches,
                        proposed_matches=proposed_matches,
                        context_kind="physical_type_change",
                        value_type_role="current",
                        lookup_graphs=lookup_graphs,
                    ),
                )
            )
        return contexts
    def _map_assertion_value_type_replacement_context(
        self,
        support: AssertionSupportDescription,
        *,
        current_values: list[MapAssertionJudgementValue],
        proposed_value: MapAssertionJudgementValue | None,
        lookup_graphs: list[str],
    ) -> list[MapAssertionJudgementValueTypeContext]:
        current_value_type_values = list(
            dict.fromkeys(
                value.value
                for value in current_values
                if value.value_kind in {"iri", "uri"}
            )
        )
        proposed_value_type = (
            proposed_value.value
            if proposed_value is not None
            and proposed_value.value_kind in {"iri", "uri"}
            else None
        )
        value_type_iris = list(current_value_type_values)
        if proposed_value_type is not None and proposed_value_type not in value_type_iris:
            value_type_iris.append(proposed_value_type)
        if not value_type_iris:
            return []

        current_physical_type_values = set(
            self._objects(lookup_graphs, support.subject.iri, "rc:physicalType")
        )
        contexts: list[MapAssertionJudgementValueTypeContext] = []
        for value_type_iri in value_type_iris:
            required_iri = self._first_object(
                lookup_graphs,
                value_type_iri,
                "rc:requiredPhysicalType",
            )
            required_value = (
                self._map_assertion_judgement_resource_value(
                    lookup_graphs,
                    required_iri,
                )
                if required_iri is not None
                else None
            )
            is_current = value_type_iri in current_value_type_values
            is_proposed = value_type_iri == proposed_value_type
            required_matches_current_physical_type = (
                required_iri in current_physical_type_values
                if required_iri is not None
                else None
            )
            contexts.append(
                MapAssertionJudgementValueTypeContext(
                    value_type=self._resource_summary(
                        lookup_graphs,
                        value_type_iri,
                        display_label=True,
                    ),
                    required_physical_type=required_value,
                    current_physical_type_matches=(
                        required_matches_current_physical_type
                        if is_current
                        else None
                    ),
                    proposed_physical_type_matches=(
                        required_matches_current_physical_type
                        if is_proposed
                        else None
                    ),
                    note=self._map_assertion_value_type_note(
                        value_type_iri=value_type_iri,
                        required_physical_type=required_value,
                        current_matches=(
                            required_matches_current_physical_type
                            if is_current
                            else None
                        ),
                        proposed_matches=(
                            required_matches_current_physical_type
                            if is_proposed
                            else None
                        ),
                        context_kind="value_type_change",
                        value_type_role=self._value_type_context_role(
                            is_current=is_current,
                            is_proposed=is_proposed,
                        ),
                        lookup_graphs=lookup_graphs,
                    ),
                )
            )
        return contexts
    def _map_assertion_judgement_resource_value(
        self,
        lookup_graphs: list[str],
        iri: str,
    ) -> MapAssertionJudgementValue:
        return MapAssertionJudgementValue(
            value=iri,
            label=self._display_label_from_graphs(lookup_graphs, iri)
            or self._local_name(iri),
            value_kind="iri",
        )
    def _map_assertion_value_type_note(
        self,
        *,
        value_type_iri: str,
        required_physical_type: MapAssertionJudgementValue | None,
        current_matches: bool | None,
        proposed_matches: bool | None,
        context_kind: str,
        value_type_role: str,
        lookup_graphs: list[str],
    ) -> str:
        value_type_label = (
            self._display_label_from_graphs(lookup_graphs, value_type_iri)
            or self._local_name(value_type_iri)
            or value_type_iri
        )
        if required_physical_type is None:
            return f"Value type {value_type_label} has no required physical type recorded."
        required_label = required_physical_type.label or required_physical_type.value
        if context_kind == "value_type_change":
            role_label = {
                "current": "Current value type",
                "proposed": "Proposed value type",
                "current_proposed": "Current/proposed value type",
            }.get(value_type_role, "Value type")
            if current_matches is True and proposed_matches is True:
                return (
                    f"{role_label} {value_type_label} requires physical type "
                    f"{required_label}, matching the column's current physical type."
                )
            if current_matches is True:
                return (
                    f"{role_label} {value_type_label} requires physical type "
                    f"{required_label}, matching the column's current physical type."
                )
            if proposed_matches is True:
                return (
                    f"{role_label} {value_type_label} requires physical type "
                    f"{required_label}, matching the column's current physical type."
                )
            if current_matches is False or proposed_matches is False:
                return (
                    f"{role_label} {value_type_label} requires physical type "
                    f"{required_label}, which does not match the column's "
                    "current physical type."
                )
            return (
                f"{role_label} {value_type_label} requires physical type "
                f"{required_label}; no current column physical type was available "
                "for comparison."
            )
        if current_matches is True:
            return (
                f"Value type {value_type_label} requires physical type "
                f"{required_label}, matching the current map value."
            )
        if proposed_matches is True:
            return (
                f"Value type {value_type_label} requires physical type "
                f"{required_label}, matching the proposed value rather than the "
                "current map value."
            )
        return (
            f"Value type {value_type_label} requires physical type "
            f"{required_label}, which does not directly explain the current or "
            "proposed physical type."
        )
    @staticmethod
    def _value_type_context_role(
        *,
        is_current: bool,
        is_proposed: bool,
    ) -> str:
        if is_current and is_proposed:
            return "current_proposed"
        if is_proposed:
            return "proposed"
        if is_current:
            return "current"
        return "related"
    def _map_assertion_judgement_caveat(
        self,
        link: AssertionSupportCaveatLink,
    ) -> MapAssertionJudgementCaveat:
        return MapAssertionJudgementCaveat(
            caveat_iri=link.caveat.iri,
            caveat_label=link.caveat.label,
            scope=link.scope,
            route_label=link.route_label,
            via_resource=link.via_resource,
            matched_resource=link.matched_resource,
            description=link.caveat.description,
            impact=link.caveat.impact,
            severity_label=(
                link.caveat.severity.label
                if link.caveat.severity is not None
                else None
            ),
        )
    def _map_assertion_judgement_route(
        self,
        support: AssertionSupportDescription,
        summary: AssertionSupportRouteSummary,
    ) -> MapAssertionJudgementRoute:
        generic_value_only = self._map_assertion_route_is_generic_value_only(
            support,
            summary,
        )
        return MapAssertionJudgementRoute(
            rank=summary.rank,
            resource_iri=summary.resource.iri,
            resource_label=summary.resource.label or summary.resource.column_name,
            resource_kind=summary.resource_kind,
            strongest_route_label=summary.strongest_route_label,
            route_count=summary.route_count,
            route_note=summary.route_note,
            matched_resources=summary.matched_resources,
            generic_value_only=generic_value_only,
            relevance_note=(
                "This route only matched a generic shared value such as a physical "
                "type or row semantics; treat it as weak context unless other "
                "routes tie it to the subject or owning dataset."
                if generic_value_only
                else None
            ),
        )
    def _ranked_panel_route_summaries(
        self,
        support: AssertionSupportDescription,
    ) -> list[AssertionSupportRouteSummary]:
        return sorted(
            support.related_route_summaries,
            key=lambda summary: (
                self._map_assertion_route_is_generic_value_only(support, summary),
                summary.rank,
            ),
        )
    def _map_assertion_route_is_generic_value_only(
        self,
        support: AssertionSupportDescription,
        summary: AssertionSupportRouteSummary,
    ) -> bool:
        if summary.generic_value_only:
            return True
        if not summary.matched_resources:
            return False
        if any(match.iri == support.subject.iri for match in summary.matched_resources):
            return False
        if not all(
            self._is_generic_shared_value_resource(match.iri)
            for match in summary.matched_resources
        ):
            return False
        return summary.resource_kind == "revision" or set(summary.route_types) <= {
            "revision_anchor",
        }
    def _map_assertion_judgement_impact(
        self,
        impact: StagedRevisionImpact,
    ) -> MapAssertionJudgementImpact:
        return MapAssertionJudgementImpact(
            impact_type=impact.impact_type,
            severity=impact.severity,
            message=impact.message,
            removed_values=[
                self._map_assertion_judgement_value_from_impact_value(value)
                for value in impact.removed_values
            ],
            added_values=[
                self._map_assertion_judgement_value_from_impact_value(value)
                for value in impact.added_values
            ],
        )
    def _map_assertion_current_value_rationale(
        self,
        support: AssertionSupportDescription,
        *,
        value_type_context: list[MapAssertionJudgementValueTypeContext],
    ) -> list[str]:
        notes: list[str] = []
        for context in value_type_context:
            if context.current_physical_type_matches is True:
                notes.append(context.note)
        for summary in self._ranked_panel_route_summaries(support):
            if self._map_assertion_route_is_generic_value_only(support, summary):
                continue
            if summary.resource_kind not in {"claim", "pattern", "observation"}:
                continue
            text = (
                summary.resource.label
                or summary.resource.description
                or summary.route_note
            )
            if text:
                notes.append(f"Related {summary.resource_kind}: {text}")
            if len(notes) >= 3:
                break
        if not notes:
            for caveat_link in support.nearby_caveat_links[:2]:
                text = (
                    caveat_link.caveat.label
                    or caveat_link.caveat.description
                    or caveat_link.caveat.iri
                )
                notes.append(
                    f"Nearby caveat ({caveat_link.scope}): {text}"
                )
        return list(dict.fromkeys(notes))[:3]
    def _map_assertion_judgement_headline(
        self,
        support: AssertionSupportDescription,
        *,
        change_kind: str,
        current_values: list[MapAssertionJudgementValue],
        proposed_value: MapAssertionJudgementValue | None,
    ) -> str:
        subject_label = (
            support.subject.label
            or support.subject.column_name
            or support.subject.iri
        )
        predicate_label = support.predicate_label or self._local_name(
            support.predicate
        ) or support.predicate
        current_label = ", ".join(
            value.label or value.value for value in current_values
        ) or "(none)"
        if change_kind == "remove":
            return (
                f"Remove {predicate_label} on {subject_label}: "
                f"current {current_label}"
            )
        if proposed_value is None:
            return f"{change_kind.title()} {predicate_label} on {subject_label}"
        proposed_label = proposed_value.label or proposed_value.value
        if change_kind == "replace":
            return (
                f"Replace {predicate_label} on {subject_label}: "
                f"{current_label} -> {proposed_label}"
            )
        return f"Add {predicate_label} on {subject_label}: {proposed_label}"
    def _map_assertion_judgement_safety_notes(
        self,
        support: AssertionSupportDescription,
        *,
        value_type_context: list[MapAssertionJudgementValueTypeContext],
        change_kind: str,
        impacts: list[StagedRevisionImpact],
    ) -> list[str]:
        notes: list[str] = []
        if not support.assertion_present and support.requested_object is not None:
            notes.append(
                "The exact requested assertion was absent before staging; compare "
                "the proposed value with current same-subject/predicate values."
            )
        if (
            support.same_subject_predicate_triples
            and change_kind in {"add", "replace"}
        ):
            notes.append(
                "The map already has value(s) for this subject/predicate, so this "
                "proposal may create or replace competing semantics."
            )
        if (
            change_kind == "replace"
            and support.assertion_present
            and len(support.same_subject_predicate_triples) > 1
        ):
            notes.append(
                "The requested replacement value is already present; the "
                "meaningful mutation is removal of other current values. Review "
                "support routes for the removed values before applying."
            )
        if any(link.scope == "owner_dataset" for link in support.nearby_caveat_links):
            notes.append(
                "At least one caveat comes from the owning dataset; treat it as "
                "dataset-level context unless other support narrows it."
            )
        elif support.nearby_caveat_links:
            notes.append(
                "Nearby caveats are present; check their scopes before treating "
                "the assertion as clean planning context."
            )
        if any(context.current_physical_type_matches for context in value_type_context):
            notes.append(
                "Current value-type context supports the current physical type; "
                "check that before normalising the assertion."
            )
        if any(
            context.proposed_physical_type_matches
            and not context.current_physical_type_matches
            for context in value_type_context
        ):
            notes.append(
                "Value-type context appears to support the proposed physical type; "
                "verify whether the current map is stale or preserving raw storage."
            )
        if support.related_route_summaries:
            notes.append(
                "Related observations, claims, patterns, or evidence are linked; "
                "read the strongest routes before treating the change as cleanup."
            )
        if any(
            self._map_assertion_route_is_generic_value_only(support, summary)
            for summary in support.related_route_summaries
        ):
            notes.append(
                "Some related routes only match generic shared values such as "
                "physical types; treat those as weak context."
            )
        if any(impact.severity == "attention" for impact in impacts):
            notes.append(
                "The staged revision has attention-level impacts; review impact "
                "messages and linked lore before applying."
            )
        if not notes:
            notes.append(
                "No caveats, related routes, or attention-level impacts were found "
                "in this compact panel; inspect full assertion support before "
                "treating that as broad absence of risk."
            )
        return notes
    def _map_assertion_semantic_risk(
        self,
        support: AssertionSupportDescription,
        *,
        value_type_context: list[MapAssertionJudgementValueTypeContext],
        impacts: list[StagedRevisionImpact],
        why_current_value_may_be_intentional: list[str],
        change_kind: str,
    ) -> tuple[str, list[str]]:
        reasons: list[str] = []
        replace_removes_other_values = (
            change_kind == "replace"
            and support.assertion_present
            and len(support.same_subject_predicate_triples) > 1
        )
        if replace_removes_other_values:
            reasons.append(
                "The requested replacement value is already present; applying "
                "would mainly remove other current values."
            )
        if why_current_value_may_be_intentional:
            reasons.append(
                "Related observations, claims, patterns, or value-type context "
                "explain why the current value may be intentional."
            )
        if support.nearby_caveat_links:
            reasons.append(
                "Nearby caveats are attached to the assertion subject, object, "
                "or owning dataset."
            )
        if support.related_route_summaries:
            reasons.append(
                "Related lore routes are present; review them before treating the "
                "change as cleanup."
            )
        if any(impact.severity == "attention" for impact in impacts):
            reasons.append(
                "The staged revision has attention-level impact entries."
            )
        if any(
            context.current_physical_type_matches
            and context.proposed_physical_type_matches is False
            for context in value_type_context
        ):
            reasons.append(
                "Value-type context supports the current physical type and not "
                "the proposed one."
            )
        if not reasons:
            return "none", []
        high_signal_count = sum(
            [
                bool(why_current_value_may_be_intentional),
                bool(support.related_route_summaries),
                any(impact.severity == "attention" for impact in impacts),
                any(
                    context.current_physical_type_matches
                    and context.proposed_physical_type_matches is False
                    for context in value_type_context
                ),
                replace_removes_other_values,
            ]
        )
        level = "high" if high_signal_count >= 2 else "attention"
        return level, reasons
    def _single_map_assertion_candidate(
        self,
        description: StagedGraphRevisionDescription,
    ) -> tuple[str, str, str | None, str, str | None, str | None, str] | None:
        addition_operation = self.expand_iri("rc:AdditionPatch")
        removal_operation = self.expand_iri("rc:RemovalPatch")
        additions: list[tuple[Identifier, URIRef, Node]] = []
        removals: list[tuple[Identifier, URIRef, Node]] = []
        for patch in description.patches:
            if patch.target_graph != "map" or patch.operation not in {
                addition_operation,
                removal_operation,
            }:
                return None
            try:
                patch_graph = self._parse_staged_patch_description(patch)
            except DoxaBaseError:
                return None
            triples = list(patch_graph)
            if patch.operation == addition_operation:
                additions.extend(triples)
            else:
                removals.extend(triples)
        all_triples = [*additions, *removals]
        if not all_triples:
            return None
        subjects = {triple[0] for triple in all_triples}
        predicates = {triple[1] for triple in all_triples}
        if len(subjects) != 1 or len(predicates) != 1:
            return None
        subject = next(iter(subjects))
        predicate = next(iter(predicates))
        if isinstance(subject, BNode) or not isinstance(predicate, URIRef):
            return None
        object_node = additions[0][2] if additions else removals[0][2]
        if isinstance(object_node, BNode):
            return None
        object_value, object_kind, object_datatype, object_lang = (
            self._object_filter_from_node(object_node)
        )
        if additions and removals:
            change_kind = "replace"
        elif additions:
            change_kind = "add"
        else:
            change_kind = "remove"
        return (
            str(subject),
            str(predicate),
            object_value,
            object_kind,
            object_datatype,
            object_lang,
            change_kind,
        )
    def _map_assertion_judgement_panel_markdown(
        self,
        panel: MapAssertionJudgementPanel,
    ) -> list[str]:
        lines = [
            f"- Headline: {panel.headline}",
            f"- Exact assertion present before staging: {panel.assertion_present_before}",
            f"- Semantic risk: {panel.semantic_risk_level}",
        ]
        if panel.semantic_risk_reasons:
            lines.append("- Semantic risk reasons:")
            lines.extend(f"  - {reason}" for reason in panel.semantic_risk_reasons)
        if panel.recommendation is not None:
            lines.append(f"- Recommendation: {panel.recommendation}")
        if panel.absence_note is not None:
            lines.append(f"- Absence note: {panel.absence_note}")
        lines.extend(["", "### Values", ""])
        lines.extend(
            [
                "| Role | Value | Kind |",
                "|---|---|---|",
            ]
        )
        if panel.current_values:
            for value in panel.current_values:
                lines.append(
                    "| Current | "
                    + self._markdown_table_cell(self._judgement_value_label(value))
                    + " | "
                    + self._markdown_table_cell(value.value_kind)
                    + " |"
                )
        else:
            lines.append("| Current | (none) |  |")
        if panel.removed_value is not None:
            lines.append(
                "| Removed | "
                + self._markdown_table_cell(
                    self._judgement_value_label(panel.removed_value)
                )
                + " | "
                + self._markdown_table_cell(panel.removed_value.value_kind)
                + " |"
            )
        elif panel.proposed_value is not None:
            lines.append(
                "| Proposed | "
                + self._markdown_table_cell(
                    self._judgement_value_label(panel.proposed_value)
                )
                + " | "
                + self._markdown_table_cell(panel.proposed_value.value_kind)
                + " |"
            )
        if panel.value_type_context:
            lines.extend(["", "### Value Type Context", ""])
            lines.extend(
                [
                    (
                        "| Value type | Required physical type | Current matches | "
                        "Proposed matches | Note |"
                    ),
                    "|---|---|---:|---:|---|",
                ]
            )
            for context in panel.value_type_context:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            self._markdown_table_cell(
                                context.value_type.label or context.value_type.iri
                            ),
                            self._markdown_table_cell(
                                self._judgement_value_label(
                                    context.required_physical_type
                                )
                                if context.required_physical_type is not None
                                else "(none)"
                            ),
                            str(context.current_physical_type_matches),
                            str(context.proposed_physical_type_matches),
                            self._markdown_table_cell(context.note),
                        ]
                    )
                    + " |"
                )
        if panel.why_current_value_may_be_intentional:
            lines.extend(["", "### Why Current Value May Be Intentional", ""])
            lines.extend(
                f"- {note}" for note in panel.why_current_value_may_be_intentional
            )
        lines.extend(["", "### Caveats", ""])
        if panel.caveats:
            for caveat in panel.caveats:
                label = caveat.caveat_label or caveat.caveat_iri
                lines.append(f"- {label} [{caveat.scope}]: {caveat.route_label}")
                if caveat.description is not None:
                    lines.append(f"  - Description: {caveat.description}")
                if caveat.impact is not None:
                    lines.append(f"  - Impact: {caveat.impact}")
        else:
            lines.append("- No caveats surfaced in the judgement panel.")
        lines.extend(["", "### Strongest Routes", ""])
        if panel.strongest_routes:
            for route in panel.strongest_routes:
                label = route.resource_label or route.resource_iri
                weak = " [weak generic-value match]" if route.generic_value_only else ""
                lines.append(f"- {route.rank}. {label} ({route.resource_kind}){weak}")
                lines.append(f"  - Route: {route.strongest_route_label}")
                lines.append(f"  - Note: {route.route_note}")
                if route.relevance_note is not None:
                    lines.append(f"  - Relevance: {route.relevance_note}")
        else:
            lines.append("- No strong related-lore routes surfaced in the judgement panel.")
        lines.extend(["", "### Safety Notes", ""])
        lines.extend(f"- {note}" for note in panel.safety_notes)
        return lines
    def _judgement_value_label(
        self,
        value: MapAssertionJudgementValue | None,
    ) -> str:
        if value is None:
            return "(none)"
        return value.label or value.value
