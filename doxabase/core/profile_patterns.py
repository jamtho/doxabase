"""Profile promotion pattern IRIs, skeleton arguments, and review actions.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via ProfilePatternsMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class ProfilePatternsMixin:
    @staticmethod
    def _profile_type_related_recommendations(
        profile: ProfileObservationSummary,
        recommendations: list[ProfileMapUpdateRecommendation],
        *,
        advisory_status: str,
    ) -> list[ProfileMapUpdateRecommendation]:
        if (
            advisory_status != "type_finding_unmapped_column"
            or profile.observed_column is None
        ):
            return []
        return [
            recommendation
            for recommendation in recommendations
            if recommendation.kind == "unmapped_profiled_column"
            and recommendation.profile_observation_iri == profile.iri
            and recommendation.resource.iri == profile.observed_column.iri
        ]
    def _with_profile_type_pending_staged_metadata(
        self,
        advisories: list[ProfileTypeFindingAdvisory],
    ) -> list[ProfileTypeFindingAdvisory]:
        updated: list[ProfileTypeFindingAdvisory] = []
        for advisory in advisories:
            pending_staged_promotion_iris: list[str] = []
            pending_staged_assertion_iris: list[str] = []
            source = DoxaBase._profile_advisory_source_for_advisory(
                advisory,
                advisory_kind="profile_type_review",
                index_field="type_advisory_index",
            )
            for action in advisory.suggested_next_actions:
                action_source = DoxaBase._profile_advisory_source_with_route_keys(
                    source,
                    action,
                )
                semantic_move = action_source.get("semantic_move")
                if semantic_move == "define_value_type":
                    for staged_iri in self._pending_staged_profile_route_iris(
                        action_source,
                        semantic_move="define_value_type",
                    ):
                        DoxaBase._append_unique(
                            pending_staged_promotion_iris,
                            staged_iri,
                        )
                elif semantic_move == "assert_map_type":
                    for staged_iri in self._pending_staged_profile_route_iris(
                        action_source,
                        semantic_move="assert_map_type",
                    ):
                        DoxaBase._append_unique(
                            pending_staged_assertion_iris,
                            staged_iri,
                        )
            updated.append(
                replace(
                    advisory,
                    pending_staged_promotion_iris=pending_staged_promotion_iris,
                    pending_staged_promotion_count=len(
                        pending_staged_promotion_iris
                    ),
                    pending_staged_assertion_iris=pending_staged_assertion_iris,
                    pending_staged_assertion_count=len(
                        pending_staged_assertion_iris
                    ),
                )
            )
        return updated
    def _profile_value_type_needs_ontology_skeleton(
        self,
        value_type_iri: str,
    ) -> bool:
        if value_type_iri.startswith(PREFIXES["rc"]):
            return False
        ontology_graphs = self._expand_graphs(["ontology"])
        value_type_class = self.expand_iri("rc:ValueType")
        return value_type_class not in self._types_from_graphs(
            ontology_graphs,
            value_type_iri,
        )
    def _profile_value_type_promotion_pattern_iris(
        self,
        *,
        value_type_iri: str,
        evidence_iri: str,
    ) -> list[str]:
        pattern_graphs = ["patterns"]
        same_evidence = set(self._subjects(pattern_graphs, "rc:evidence", evidence_iri))
        if not same_evidence:
            return []
        value_type_related = set(
            self._subjects(pattern_graphs, "rc:patternTarget", value_type_iri)
        )
        value_type_related.update(
            self._subjects(pattern_graphs, "rc:mapImplication", value_type_iri)
        )
        return sorted(same_evidence & value_type_related)
    def _profile_value_type_promotion_skeleton_arguments(
        self,
        *,
        value_type_iri: str,
        pattern_iris: list[str],
        evidence_iri: str | None,
    ) -> dict[str, Any]:
        value_type_label = self._local_name(value_type_iri) or value_type_iri
        semantic_hint = self._profile_value_type_promotion_semantic_hint(
            value_type_iri=value_type_iri,
            pattern_iris=pattern_iris,
        )
        comment = (
            f"Project-specific value type observed in profile evidence: "
            f"{semantic_hint}"
            if semantic_hint is not None
            else (
                "Project-specific value type observed in profile evidence; "
                "review and sharpen its domain meaning, allowed values, and "
                "physical-type expectations before applying this vocabulary "
                "definition."
            )
        )
        content = (
            "@prefix rc: <https://richcanopy.org/ns/rc#> .\n"
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n\n"
            f"<{value_type_iri}> a rc:ValueType ;\n"
            f"    rdfs:label {Literal(value_type_label).n3()} ;\n"
            "    rdfs:comment " + Literal(comment).n3() + " ."
        )
        arguments: dict[str, Any] = {
            "patterns": pattern_iris,
            "summary": f"Define {value_type_label} value type",
            "intent": (
                "Stage project ontology vocabulary for a value type that "
                "already has same-evidence pattern support."
            ),
            "rationale": (
                "The type advisory found a project-specific value type that is "
                "undefined or not yet typed as rc:ValueType, plus an existing "
                "pattern tied to the same evidence. Keep this as a staged "
                "ontology proposal until domain meaning and physical-type "
                "expectations have been reviewed."
            ),
            "framings": [
                {
                    "label": "Value type definition",
                    "graph": "ontology",
                    "content": content,
                    "review_note": (
                        "Generated as a "
                        f"{PROFILE_VALUE_TYPE_PROMOTION_REVIEW_NOTE_MARKER}; "
                        "review wording before applying."
                    ),
                    "review_recommendation": (
                        "Apply only after the value type's domain meaning, "
                        "allowed values, and physical-type expectations are "
                        "explicit enough for reuse."
                    ),
                }
            ],
            "anchors": [value_type_iri],
            "validation_scope": "all",
        }
        if evidence_iri is not None:
            arguments["evidence"] = [evidence_iri]
        return arguments
    def _profile_value_type_promotion_semantic_hint(
        self,
        *,
        value_type_iri: str,
        pattern_iris: list[str],
    ) -> str | None:
        for pattern_iri in pattern_iris:
            try:
                pattern = self.describe_pattern(pattern_iri)
            except DoxaBaseError:
                continue
            for value in (pattern.pattern_text, pattern.rationale, pattern.summary):
                if value is None:
                    continue
                if not self._profile_metric_text_mentions_metric(
                    value,
                    metric_iri=value_type_iri,
                ):
                    continue
                hint = self._compact_restage_reason(value, limit=260)
                if hint:
                    return hint
        return None
    def _profile_type_existing_type_seed_iris(
        self,
        profile: ProfileObservationSummary,
    ) -> list[str]:
        all_graphs = self._expand_graphs(["all"])
        seed_iris: list[str] = []
        for observed_type in (
            profile.observed_physical_type,
            profile.observed_value_type,
        ):
            if observed_type is None:
                continue
            if self._subject_exists(observed_type.iri, all_graphs):
                seed_iris.append(observed_type.iri)
        return seed_iris
    def _profile_type_assertion_action_arguments(
        self,
        *,
        profile: ProfileObservationSummary,
        evidence_iri: str,
        predicate: str,
        object_iri: str,
        advisory_status: str,
        supporting_patterns: list[str] | None = None,
    ) -> dict[str, Any]:
        assert profile.observed_column is not None
        column_label = (
            profile.observed_column.label
            or profile.observed_column.column_name
            or profile.observed_column_name
            or profile.observed_column.iri
        )
        supporting_pattern_values = list(dict.fromkeys(supporting_patterns or []))
        if supporting_pattern_values:
            review_note = (
                "Generated from a profile type-finding advisory; profile type "
                "findings are evidence, not automatic map updates. "
                "Same-evidence type-review patterns were prefilled in "
                "supporting_patterns; review that support before staging."
            )
        else:
            review_note = (
                "Generated from a profile type-finding advisory; profile type "
                "findings are evidence, not automatic map updates. If the "
                "suggested type-finding pattern was recorded first, add its "
                "pattern_iri to supporting_patterns before staging."
            )
        return {
            "subject": profile.observed_column.iri,
            "predicate": predicate,
            "object": object_iri,
            "object_kind": "iri",
            "change_kind": "replace",
            "rationale": (
                f"Profile observation {profile.iri} recorded {predicate} "
                f"{object_iri} for {column_label}. Treat this as a candidate "
                "map assertion and review current context before applying."
            ),
            "supporting_observations": [profile.iri],
            "supporting_patterns": supporting_pattern_values,
            "evidence": [evidence_iri],
            "revision_anchors": [profile.observed_column.iri, object_iri],
            "review_note": review_note,
            "review_recommendation": (
                "Apply only if the profile evidence and current map/value-type "
                f"context support replacing or recording this assertion "
                f"(advisory_status={advisory_status})."
            ),
            "validation_scope": "all",
        }
    def _profile_pending_type_review_actions(
        self,
        pending_staged_iris: list[str],
        *,
        semantic_move: str,
    ) -> list[SuggestedNextAction]:
        if semantic_move == "define_value_type":
            export_slug = "profile-value-type-vocabulary-pending"
            inspect_reason = (
                "A current staged value-type vocabulary skeleton already "
                "covers this profile type route. Inspect it before drafting "
                "another duplicate skeleton."
            )
            export_reason = (
                "Write a grouped review bundle for pending staged value-type "
                "vocabulary skeletons before deciding whether more value-type "
                "promotion work is needed. The export blocks if "
                "scanner-matching content appears before export."
            )
        else:
            export_slug = "profile-type-assertion-pending"
            inspect_reason = (
                "A current staged profile type assertion already covers this "
                "type advisory route. Inspect it before drafting another "
                "duplicate assertion."
            )
            export_reason = (
                "Write a grouped review bundle for pending staged profile type "
                "assertions before deciding whether more type assertion work is "
                "needed. The export blocks if scanner-matching content appears "
                "before export."
            )
        actions: list[SuggestedNextAction] = []
        for staged_iri in pending_staged_iris[:3]:
            arguments = {
                "iri": staged_iri,
                "include_current_apply_check": True,
            }
            actions.append(
                SuggestedNextAction(
                    tool="doxabase.describe_revision",
                    args=arguments,
                    reason=inspect_reason,
                )
            )
        spec = {
            "revision_iris": list(pending_staged_iris),
            "path": self._suggested_review_export_path(
                export_slug,
                pending_staged_iris,
            ),
            "fail_on_sensitive": True,
        }
        actions.append(
            SuggestedNextAction(
                tool="doxabase.export_bundle",
                args={"kind": "staged_revisions", "spec": spec},
                reason=export_reason,
            )
        )
        return actions
    def _profile_pending_fallback_review_actions(
        self,
        pending_staged_fallback_iris: list[str],
    ) -> list[SuggestedNextAction]:
        actions: list[SuggestedNextAction] = []
        for staged_iri in pending_staged_fallback_iris[:3]:
            arguments = {
                "iri": staged_iri,
                "include_current_apply_check": True,
            }
            actions.append(
                SuggestedNextAction(
                    tool="doxabase.describe_revision",
                    args=arguments,
                    reason="A current staged profile fallback already covers this "
                        "route. Inspect it before drafting another fallback for "
                        "the same advisory.",
                )
            )
        spec = {
            "revision_iris": list(pending_staged_fallback_iris),
            "path": self._suggested_review_export_path(
                "profile-fallback-pending",
                pending_staged_fallback_iris,
            ),
            "fail_on_sensitive": True,
        }
        actions.append(
            SuggestedNextAction(
                tool="doxabase.export_bundle",
                args={"kind": "staged_revisions", "spec": spec},
                reason="Write a grouped review bundle for the pending staged "
                    "profile fallback(s) before deciding whether more fallback "
                    "work is needed. The export blocks if scanner-matching "
                    "content appears before export.",
            )
        )
        return actions
    def _pending_staged_profile_fallback_iris(
        self,
        source_profile_advisory: MappingABC[str, Any],
    ) -> list[str]:
        if source_profile_advisory.get("semantic_move") != "caveat_fallback":
            return []
        return self._pending_staged_profile_route_iris(
            source_profile_advisory,
            semantic_move="caveat_fallback",
        )
    def _pending_staged_profile_route_iris(
        self,
        source_profile_advisory: MappingABC[str, Any],
        *,
        semantic_move: str,
    ) -> list[str]:
        review_lane = source_profile_advisory.get("review_lane")
        route_group_key = source_profile_advisory.get("route_group_key")
        if not isinstance(review_lane, str) or not isinstance(
            route_group_key,
            str,
        ):
            return []
        listing = self.list_graph_revisions(
            current_staged_work_only=True,
            include_apply_checks=True,
            limit=200,
        )
        if listing.count > listing.returned_count:
            listing = self.list_graph_revisions(
                current_staged_work_only=True,
                include_apply_checks=True,
                limit=listing.count,
            )
        queue_by_row = {
            item.row_iri: item for item in listing.next_action_queue_items
        }
        ignored_queues = {
            None,
            "informational",
            "inspect_already_applied",
        }
        pending: list[str] = []
        for revision in listing.revisions:
            queue_item = queue_by_row.get(revision.iri)
            queue = (
                queue_item.queue
                if queue_item is not None
                else revision.next_action.queue
                if revision.next_action is not None
                else None
            )
            if queue in ignored_queues:
                continue
            if not revision.suggested_next_actions and queue_item is None:
                continue
            for stored_source in self._stored_profile_insight_route_sources(
                revision.iri
            ):
                if stored_source.get("semantic_move") != semantic_move:
                    continue
                if stored_source.get("review_lane") != review_lane:
                    continue
                if stored_source.get("route_group_key") != route_group_key:
                    continue
                DoxaBase._append_unique(pending, revision.iri)
                break
        return pending
    @staticmethod
    def _profile_fallback_pattern_iri(
        kind: str,
        payload: Mapping[str, Any],
    ) -> str:
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:16]
        return f"https://richcanopy.org/doxabase/generated/{kind}/{digest}"
    @staticmethod
    def _profile_fallback_pattern_turtle(
        *,
        pattern_iri: str,
        summary: str,
        pattern_text: str,
        rationale: str,
        pattern_targets: list[str],
        supporting_observations: list[str],
        evidence_iri: str,
        map_implications: list[str],
    ) -> str:
        lines = [
            "@prefix rc: <https://richcanopy.org/ns/rc#> .",
            "",
            f"<{pattern_iri}> a rc:Pattern ;",
            f"    rc:summary {Literal(summary).n3()} ;",
            f"    rc:patternText {Literal(pattern_text).n3()} ;",
            f"    rc:rationale {Literal(rationale).n3()} ;",
            *DoxaBase._profile_fallback_turtle_iri_lines(
                "rc:patternTarget",
                pattern_targets,
            ),
            *DoxaBase._profile_fallback_turtle_iri_lines(
                "rc:supportingObservation",
                supporting_observations,
            ),
            f"    rc:evidence <{evidence_iri}> ;",
        ]
        implication_lines = DoxaBase._profile_fallback_turtle_iri_lines(
            "rc:mapImplication",
            map_implications,
        )
        if implication_lines:
            lines.extend(implication_lines)
        lines.append("    rc:patternStability rc:EmergingPattern .")
        return "\n".join(lines)
    @staticmethod
    def _profile_fallback_pattern_turtle_with_supporting_observations(
        content: str,
        supporting_observations: list[str],
    ) -> str:
        replacement_lines = DoxaBase._profile_fallback_turtle_iri_lines(
            "rc:supportingObservation",
            supporting_observations,
        )
        if not replacement_lines:
            return content
        replacement = replacement_lines[0]
        lines = content.splitlines()
        for index, line in enumerate(lines):
            if line.strip().startswith("rc:supportingObservation "):
                lines[index] = replacement
                return "\n".join(lines)
        for index, line in enumerate(lines):
            if line.strip().startswith("rc:evidence "):
                lines.insert(index, replacement)
                return "\n".join(lines)
        if lines:
            lines.insert(max(len(lines) - 1, 0), replacement)
            return "\n".join(lines)
        return replacement
    @staticmethod
    def _profile_fallback_turtle_iri_lines(
        predicate: str,
        values: list[str],
    ) -> list[str]:
        unique_values = list(dict.fromkeys(values))
        if not unique_values:
            return []
        objects = ", ".join(f"<{value}>" for value in unique_values)
        return [f"    {predicate} {objects} ;"]
    def _profile_metric_promotion_pattern_iris(
        self,
        *,
        metric_iri: str,
        evidence_iri: str,
    ) -> list[str]:
        pattern_graphs = ["patterns"]
        same_evidence = set(self._subjects(pattern_graphs, "rc:evidence", evidence_iri))
        if not same_evidence:
            return []
        metric_related = set(
            self._subjects(pattern_graphs, "rc:patternTarget", metric_iri)
        )
        metric_related.update(
            self._subjects(pattern_graphs, "rc:mapImplication", metric_iri)
        )
        return sorted(same_evidence & metric_related)
    def _profile_metric_context_pattern_iris(
        self,
        *,
        metric_iri: str,
        evidence_iri: str,
        exclude_pattern_iris: Iterable[str] = (),
    ) -> list[str]:
        pattern_graphs = ["patterns"]
        same_evidence = set(self._subjects(pattern_graphs, "rc:evidence", evidence_iri))
        if not same_evidence:
            return []
        excluded = set(exclude_pattern_iris)
        local_name = self._local_name(metric_iri)
        matches: list[str] = []
        for pattern_iri in sorted(same_evidence - excluded):
            text_parts = [
                value
                for value in (
                    self._first_object(pattern_graphs, pattern_iri, "rc:patternText"),
                    self._first_object(pattern_graphs, pattern_iri, "rc:rationale"),
                    self._first_object(pattern_graphs, pattern_iri, "rc:summary"),
                )
                if value
            ]
            haystack = "\n".join(text_parts).lower()
            if metric_iri.lower() in haystack or (
                local_name and local_name.lower() in haystack
            ):
                matches.append(pattern_iri)
        return matches
    def _profile_metric_promotion_skeleton_arguments(
        self,
        *,
        metric_iri: str,
        pattern_iris: list[str],
        evidence_iri: str | None,
    ) -> dict[str, Any]:
        metric_label = self._local_name(metric_iri) or metric_iri
        semantic_hint = self._profile_metric_promotion_semantic_hint(
            metric_iri=metric_iri,
            pattern_iris=pattern_iris,
        )
        comment = (
            f"Project-specific profile metric observed in profile evidence: "
            f"{semantic_hint}"
            if semantic_hint is not None
            else (
                "Project-specific profile metric observed in profile evidence; "
                "review and sharpen its calculation, unit, and comparison "
                "semantics before applying this vocabulary definition."
            )
        )
        content = (
            "@prefix rc: <https://richcanopy.org/ns/rc#> .\n"
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n\n"
            f"<{metric_iri}> a rc:ProfileMetricKind ;\n"
            f"    rdfs:label {Literal(metric_label).n3()} ;\n"
            "    rdfs:comment " + Literal(comment).n3() + " ."
        )
        arguments: dict[str, Any] = {
            "patterns": pattern_iris,
            "summary": f"Define {metric_label} profile metric",
            "intent": (
                "Stage project ontology vocabulary for a profile metric that "
                "already has same-evidence pattern support."
            ),
            "rationale": (
                "The metric advisory found a project-specific profile metric "
                "that is undefined or not yet typed as rc:ProfileMetricKind, "
                "plus an existing pattern tied to the same evidence. Keep this "
                "as a staged ontology proposal until calculation, unit, and "
                "comparison semantics have been reviewed."
            ),
            "framings": [
                {
                    "label": "Profile metric kind definition",
                    "graph": "ontology",
                    "content": content,
                    "review_note": (
                        "Generated as a "
                        f"{PROFILE_METRIC_PROMOTION_REVIEW_NOTE_MARKER}; "
                        "review wording before applying."
                    ),
                    "review_recommendation": (
                        "Apply only after the metric calculation, unit, and "
                        "comparison semantics are explicit enough for reuse."
                    ),
                }
            ],
            "anchors": [metric_iri],
            "validation_scope": "all",
        }
        if evidence_iri is not None:
            arguments["evidence"] = [evidence_iri]
        return arguments
    def _profile_metric_promotion_semantic_hint(
        self,
        *,
        metric_iri: str,
        pattern_iris: list[str],
    ) -> str | None:
        for pattern_iri in pattern_iris:
            try:
                pattern = self.describe_pattern(pattern_iri)
            except DoxaBaseError:
                continue
            for value in (pattern.pattern_text, pattern.rationale, pattern.summary):
                if value is None:
                    continue
                if not self._profile_metric_text_mentions_metric(
                    value,
                    metric_iri=metric_iri,
                ):
                    continue
                hint = self._compact_restage_reason(value, limit=260)
                if hint:
                    return hint
        return None
    def _profile_metric_text_mentions_metric(
        self,
        text: str,
        *,
        metric_iri: str,
    ) -> bool:
        text_lower = text.lower()
        if metric_iri.lower() in text_lower:
            return True
        local_name = self._local_name(metric_iri)
        if not local_name:
            return False
        if self._contains_name_like_token(text_lower, local_name.lower()):
            return True
        phrase = self._profile_metric_local_name_phrase(local_name)
        return bool(phrase and self._contains_name_like_token(text_lower, phrase))
    @staticmethod
    def _profile_metric_local_name_phrase(local_name: str) -> str:
        spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", local_name)
        return " ".join(
            token.lower()
            for token in re.findall(r"[A-Za-z0-9]+", spaced)
        )
