"""Profile description and summaries.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via ProfilesMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class ProfilesMixin:
    def _pending_staged_profile_update_iris(
        self,
        dataset_iri: str,
        evidence_iri: str,
    ) -> list[str]:
        dataset_value = self.expand_iri(dataset_iri)
        evidence_value = self.expand_iri(evidence_iri)
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
            if dataset_value not in self._objects(
                ["history"],
                revision.iri,
                "rc:revisionAnchor",
            ):
                continue
            if evidence_value not in self._objects(
                ["history"],
                revision.iri,
                "rc:evidence",
            ):
                continue
            if not self._staged_revision_is_profile_map_update(revision.iri):
                continue
            pending.append(revision.iri)
        return pending
    def _context_slice_profile_mismatch_warning(
        self,
        seed: str,
        *,
        profile: str,
        seed_types: set[str],
        metric_kind_metric_iris: list[str],
        observed_value_type_profile_observation_iris: list[str],
    ) -> str:
        base = (
            f"Seed '{seed}' was included directly; profile-specific expansion "
            "did not apply."
        )
        dataset_profiles = "profile='dataset_brief' or 'deep_lore'"
        pattern_profiles = "profile='pattern_brief' or 'deep_lore'"
        if self.expand_iri("rc:Pattern") in seed_types:
            return f"{base} Seed is an rc:Pattern; rerun with {pattern_profiles}."
        if self.expand_iri("rc:Claim") in seed_types:
            return f"{base} Seed is an rc:Claim; rerun with {pattern_profiles}."
        if self.expand_iri("rc:Dataset") in seed_types:
            return f"{base} Seed is an rc:Dataset; rerun with {dataset_profiles}."
        if self.expand_iri("rc:Table") in seed_types:
            return f"{base} Seed is an rc:Table; rerun with {dataset_profiles}."
        if self.expand_iri("rc:ProfileObservation") in seed_types:
            return (
                f"{base} Seed is an rc:ProfileObservation; rerun with "
                f"{dataset_profiles}."
            )
        if self.expand_iri("rc:ObservedProfileMetric") in seed_types:
            return (
                f"{base} Seed is an rc:ObservedProfileMetric; rerun with "
                f"{dataset_profiles}."
            )
        if self.expand_iri("rc:Evidence") in seed_types:
            return (
                f"{base} Seed is an rc:Evidence; rerun with "
                "profile='resource_brief' to recover incoming observation, "
                "profile-run, and source-span routes."
            )
        if self.expand_iri("rc:StorageAccess") in seed_types:
            return (
                f"{base} Seed is an rc:StorageAccess; rerun with "
                "profile='resource_brief' to recover owner-table routes."
            )
        if self.expand_iri("rc:PhysicalLayout") in seed_types:
            return (
                f"{base} Seed is an rc:PhysicalLayout; rerun with "
                "profile='resource_brief' to recover owner-table routes."
            )
        if self.expand_iri("rc:PartitionScheme") in seed_types:
            return (
                f"{base} Seed is an rc:PartitionScheme; rerun with "
                "profile='resource_brief' to recover owner-table routes."
            )
        if self.expand_iri("rc:GraphRevision") in seed_types:
            return (
                f"{base} Seed is an rc:GraphRevision; rerun with "
                "profile='deep_lore'."
            )
        if metric_kind_metric_iris:
            return (
                f"{base} Seed is used as an rc:profileMetricKind; rerun with "
                f"{dataset_profiles}."
            )
        if observed_value_type_profile_observation_iris:
            return (
                f"{base} Seed is used as an rc:observedValueType; rerun with "
                f"{dataset_profiles}."
            )
        return base
    def describe_profile_run(
        self,
        dataset_iri: str,
        evidence_iri: str,
        *,
        graph: str | None = "map",
        limit: int | None = None,
    ) -> ProfileRunDescription:
        if limit is not None and limit < 1:
            raise DoxaBaseError("limit must be a positive integer or None")
        dataset_value = self._required_iri("dataset_iri", dataset_iri)
        evidence_value = self._required_iri("evidence_iri", evidence_iri)
        data_graphs = self._expand_graphs([graph] if graph else None)
        lookup_graphs = self._lookup_graphs(data_graphs)
        evidence_graphs = ["evidence"]
        column_iris = self._objects(data_graphs, dataset_value, "rc:hasColumn")

        dataset_profiles = self._profiles_with_evidence(
            self._profile_observations_for_target(
                target_iri=dataset_value,
                target_predicate="rc:observedAsset",
                exclude_observed_column=True,
                limit=None,
            ),
            evidence_value,
        )
        mapped_column_profiles = self._profiles_with_evidence(
            [
                profile
                for column_iri in column_iris
                for profile in self._profile_observations_for_target(
                    target_iri=column_iri,
                    target_predicate="rc:observedColumn",
                    limit=None,
                )
            ],
            evidence_value,
        )
        unmapped_column_profiles = self._profiles_with_evidence(
            self._unmapped_column_profile_observations_for_dataset(
                dataset_value,
                mapped_column_iris=column_iris,
                limit=None,
            ),
            evidence_value,
        )

        categorized_profiles = [
            *[("dataset", profile) for profile in dataset_profiles],
            *[("mapped", profile) for profile in mapped_column_profiles],
            *[("unmapped", profile) for profile in unmapped_column_profiles],
        ]
        categorized_profiles.sort(
            key=lambda item: self._profile_observation_sort_key(item[1]),
            reverse=True,
        )
        returned_profiles = (
            categorized_profiles[:limit] if limit is not None else categorized_profiles
        )
        returned_dataset_profiles = [
            profile for category, profile in returned_profiles if category == "dataset"
        ]
        returned_mapped_column_profiles = [
            profile for category, profile in returned_profiles if category == "mapped"
        ]
        returned_unmapped_column_profiles = [
            profile for category, profile in returned_profiles if category == "unmapped"
        ]
        total_dataset_profile_count = len(dataset_profiles)
        total_mapped_column_profile_count = len(mapped_column_profiles)
        total_unmapped_column_profile_count = len(unmapped_column_profiles)
        total_profile_count = len(categorized_profiles)
        returned_profile_count = len(returned_profiles)
        omitted_dataset_profile_count = (
            total_dataset_profile_count - len(returned_dataset_profiles)
        )
        omitted_mapped_column_profile_count = (
            total_mapped_column_profile_count - len(returned_mapped_column_profiles)
        )
        omitted_unmapped_column_profile_count = (
            total_unmapped_column_profile_count - len(returned_unmapped_column_profiles)
        )
        omitted_profile_count = total_profile_count - returned_profile_count
        row_count_snapshot = self._int_object(
            data_graphs,
            dataset_value,
            "rc:rowCountSnapshot",
        )
        dataset_profile_row_count_bases: dict[int, set[str]] = {}
        for profile in dataset_profiles:
            if profile.row_count is None:
                continue
            dataset_profile_row_count_bases.setdefault(
                profile.row_count,
                set(),
            ).add(self._profile_observation_basis(profile))
        suggested_next_actions = self._describe_profile_run_suggested_actions(
            dataset_iri=dataset_value,
            evidence_iri=evidence_value,
            graph=graph,
            limit=limit,
            omitted_profile_count=omitted_profile_count,
        )

        return ProfileRunDescription(
            dataset=self._privacy_redacted_resource_summary(
                self._resource_summary(lookup_graphs, dataset_value)
            ),
            evidence=self._describe_evidence(
                evidence_value,
                evidence_graphs,
                lookup_graphs,
            ),
            evidence_iri=evidence_value,
            row_count_snapshot=row_count_snapshot,
            dataset_profile_row_counts=sorted(dataset_profile_row_count_bases),
            dataset_profile_row_count_bases={
                str(row_count): sorted(bases)
                for row_count, bases in sorted(
                    dataset_profile_row_count_bases.items()
                )
            },
            row_count_snapshot_matches=(
                row_count_snapshot is not None
                and row_count_snapshot in dataset_profile_row_count_bases
            ),
            row_count_snapshot_basis=self._profile_row_count_snapshot_basis(
                row_count_snapshot,
                dataset_profile_row_count_bases,
            ),
            returned_dataset_profile_count=len(returned_dataset_profiles),
            returned_mapped_column_profile_count=len(returned_mapped_column_profiles),
            returned_unmapped_column_profile_count=len(
                returned_unmapped_column_profiles
            ),
            returned_profile_count=returned_profile_count,
            total_dataset_profile_count=total_dataset_profile_count,
            total_mapped_column_profile_count=total_mapped_column_profile_count,
            total_unmapped_column_profile_count=total_unmapped_column_profile_count,
            total_profile_count=total_profile_count,
            omitted_dataset_profile_count=omitted_dataset_profile_count,
            omitted_mapped_column_profile_count=omitted_mapped_column_profile_count,
            omitted_unmapped_column_profile_count=omitted_unmapped_column_profile_count,
            omitted_profile_count=omitted_profile_count,
            profile_observation_iris=[profile.iri for _, profile in returned_profiles],
            dataset_profile_observations=returned_dataset_profiles,
            mapped_column_profile_observations=returned_mapped_column_profiles,
            unmapped_column_profile_observations=returned_unmapped_column_profiles,
            retrieval_note=(
                "Profile run membership is inferred from returned profile "
                "observations for this dataset that link to the requested evidence "
                "IRI; no separate persisted profile-run node is implied."
            ),
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[
                action.call for action in suggested_next_actions
            ],
        )
    def _describe_profile_run_suggested_actions(
        self,
        *,
        dataset_iri: str,
        evidence_iri: str,
        graph: str | None,
        limit: int | None,
        omitted_profile_count: int,
    ) -> list[SuggestedNextAction]:
        actions: list[SuggestedNextAction] = []
        graph_argument = graph if graph != "map" else None
        if limit is not None and omitted_profile_count > 0:
            arguments: dict[str, Any] = {
                "dataset_iri": dataset_iri,
                "evidence_iri": evidence_iri,
            }
            if graph_argument is not None or graph is None:
                arguments["graph"] = graph
            actions.append(
                SuggestedNextAction(
                    action_label="Expand full profile run",
                    tool_name="describe_profile_run",
                    mcp_tool_name="doxabase.describe_profile_run",
                    arguments=arguments,
                    reason=(
                        "This response was capped and omitted profile "
                        "observations. Expand the full shared-evidence run "
                        "before drafting map updates or advisory follow-through."
                    ),
                    call=self._suggested_call_string(
                        "describe_profile_run",
                        arguments,
                    ),
                )
            )

        draft_arguments: dict[str, Any] = {
            "dataset_iri": dataset_iri,
            "evidence_iri": evidence_iri,
        }
        if graph_argument is not None or graph is None:
            draft_arguments["graph"] = graph
        actions.append(
            SuggestedNextAction(
                action_label="Inspect profile map-update status",
                tool_name="draft_profile_map_updates",
                mcp_tool_name="doxabase.draft_profile_map_updates",
                arguments=draft_arguments,
                reason=(
                    "Compare this shared-evidence profile run with current map "
                    "facts and inspect whether map updates, scalar conflicts, "
                    "metric vocabulary, type findings, or query-context review "
                    "lanes remain before staging changes."
                ),
                call=self._suggested_call_string(
                    "draft_profile_map_updates",
                    draft_arguments,
                ),
            )
        )
        return actions
    def _profile_type_assertion_batch_plan(
        self,
        action_resolutions: list[ProfileFollowthroughActionResolution],
    ) -> dict[str, Any]:
        batches: dict[tuple[str, str], dict[str, Any]] = {}
        batch_order: list[tuple[str, str]] = []
        skipped_status_counts: dict[str, int] = {}
        skipped_reason_counts: dict[str, int] = {}
        skipped_reasons: list[dict[str, Any]] = []

        for resolution in action_resolutions:
            if resolution.tool_name != "stage_map_assertion_change":
                continue
            source = getattr(resolution.action, "source_profile_advisory", None)
            if not isinstance(source, MappingABC):
                continue
            if source.get("review_lane") != "profile_type_review":
                continue
            if source.get("semantic_move") != "assert_map_type":
                continue
            source_statuses = self._profile_advisory_status_set(source)
            for status in source_statuses or {"unknown"}:
                skipped_status_counts.setdefault(status, 0)
            reason = self._profile_type_assertion_batch_skip_reason(
                resolution,
                source,
                source_statuses=source_statuses,
            )
            if reason is not None:
                for status in source_statuses or {"unknown"}:
                    skipped_status_counts[status] += 1
                skipped_reason_counts[reason] = (
                    skipped_reason_counts.get(reason, 0) + 1
                )
                skipped_reasons.append(
                    self._profile_type_assertion_batch_skip_record(
                        resolution,
                        source,
                        reason=reason,
                        source_statuses=source_statuses,
                    )
                )
                continue

            predicate = str(resolution.action.arguments["predicate"])
            object_value = str(resolution.action.arguments["object"])
            key = (predicate, object_value)
            if key not in batches:
                batch_key = self._profile_type_assertion_batch_key(
                    predicate,
                    object_value,
                )
                batches[key] = {
                    "batch_key": batch_key,
                    "semantic_move": "assert_map_type",
                    "review_lane": "profile_type_review",
                    "advisory_status": "type_finding_missing_map_type",
                    "predicate": predicate,
                    "object": object_value,
                    "items": [],
                    "item_count": 0,
                    "type_advisory_indexes": [],
                    "duplicate_advisory_indexes": [],
                    "duplicate_group_keys": [],
                    "route_group_keys": [],
                    "route_step_keys": [],
                }
                batch_order.append(key)
            batch = batches[key]
            item = self._profile_type_assertion_batch_item(resolution, source)
            batch["items"].append(item)
            batch["item_count"] = len(batch["items"])
            for field_name in (
                "type_advisory_indexes",
                "duplicate_advisory_indexes",
                "duplicate_group_keys",
                "route_group_keys",
                "route_step_keys",
            ):
                for value in item[field_name]:
                    self._append_unique(batch[field_name], value)

        ordered_batches = [batches[key] for key in batch_order]
        eligible_action_count = sum(
            int(batch["item_count"]) for batch in ordered_batches
        )
        skipped_action_count = len(skipped_reasons)
        return {
            "result_kind": "profile_type_assertion_batch_plan",
            "policy": "safe_missing_physical_type",
            "eligible_action_count": eligible_action_count,
            "skipped_action_count": skipped_action_count,
            "batch_count": len(ordered_batches),
            "batches": ordered_batches,
            "skipped_status_counts": {
                key: value
                for key, value in sorted(skipped_status_counts.items())
                if value
            },
            "skipped_reason_counts": dict(sorted(skipped_reason_counts.items())),
            "skipped_reasons": skipped_reasons,
            "note": (
                "This is a read-only batching aid for call-ready profile type "
                "assertions. It only groups missing-map physical type assertions "
                "whose result bindings are already resolved; review and stage "
                "each returned action explicitly."
            ),
        }
    @staticmethod
    def _profile_type_assertion_batch_skip_reason(
        resolution: ProfileFollowthroughActionResolution,
        source_profile_advisory: MappingABC[str, Any],
        *,
        source_statuses: set[str],
    ) -> str | None:
        if source_statuses != {"type_finding_missing_map_type"}:
            return "unsupported_advisory_status"
        if resolution.binding_status == "missing_bindings":
            return "requires_result_binding"
        if resolution.binding_status not in {"resolved", "not_applicable"}:
            return f"unsupported_binding_status:{resolution.binding_status}"
        if source_profile_advisory.get("pending_staged_assertion_iris"):
            return "pending_staged_assertion"
        predicate = resolution.action.arguments.get("predicate")
        if predicate != "rc:physicalType":
            return "unsupported_predicate"
        for required_field in ("subject", "object"):
            if not isinstance(resolution.action.arguments.get(required_field), str):
                return f"missing_{required_field}"
        route_group_key = source_profile_advisory.get("route_group_key")
        route_step_key = source_profile_advisory.get("route_step_key")
        if not isinstance(route_group_key, str) or not isinstance(
            route_step_key,
            str,
        ):
            return "missing_route_keys"
        return None
    @staticmethod
    def _profile_type_assertion_batch_skip_record(
        resolution: ProfileFollowthroughActionResolution,
        source_profile_advisory: MappingABC[str, Any],
        *,
        reason: str,
        source_statuses: set[str],
    ) -> dict[str, Any]:
        return {
            "reason": reason,
            "action_group": resolution.action_group,
            "action_index": resolution.action_index,
            "tool_name": resolution.tool_name,
            "binding_status": resolution.binding_status,
            "missing_binding_keys": list(resolution.missing_binding_keys),
            "route_group_key": source_profile_advisory.get("route_group_key"),
            "route_step_key": source_profile_advisory.get("route_step_key"),
            "advisory_statuses": sorted(source_statuses),
            "type_advisory_indexes": DoxaBase._int_values(
                source_profile_advisory.get("advisory_indexes"),
            ),
            "duplicate_advisory_indexes": DoxaBase._int_values(
                source_profile_advisory.get("duplicate_advisory_indexes"),
            ),
            "predicate": resolution.action.arguments.get("predicate"),
            "object": resolution.action.arguments.get("object"),
        }
    @staticmethod
    def _profile_type_assertion_batch_item(
        resolution: ProfileFollowthroughActionResolution,
        source_profile_advisory: MappingABC[str, Any],
    ) -> dict[str, Any]:
        route_group_key = str(source_profile_advisory["route_group_key"])
        route_step_key = str(source_profile_advisory["route_step_key"])
        type_advisory_indexes = DoxaBase._int_values(
            source_profile_advisory.get("advisory_indexes"),
        )
        duplicate_advisory_indexes = DoxaBase._int_values(
            source_profile_advisory.get("duplicate_advisory_indexes"),
        )
        duplicate_group_keys = DoxaBase._string_values_from_any(
            source_profile_advisory.get("duplicate_group_keys"),
        )
        return {
            "action_group": resolution.action_group,
            "action_index": resolution.action_index,
            "route_group_key": route_group_key,
            "route_step_key": route_step_key,
            "type_advisory_indexes": type_advisory_indexes,
            "duplicate_advisory_indexes": duplicate_advisory_indexes,
            "duplicate_group_keys": duplicate_group_keys,
            "route_group_keys": [route_group_key],
            "route_step_keys": [route_step_key],
            "subject": resolution.action.arguments["subject"],
            "predicate": resolution.action.arguments["predicate"],
            "object": resolution.action.arguments["object"],
            "supporting_observations": list(
                resolution.action.arguments.get("supporting_observations", [])
            ),
            "supporting_patterns": list(
                resolution.action.arguments.get("supporting_patterns", [])
            ),
            "action": resolution.action,
            "call": resolution.action.call,
        }
    @staticmethod
    def _profile_type_assertion_batch_key(
        predicate: str,
        object_value: str,
    ) -> str:
        payload = {"predicate": predicate, "object": object_value}
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
        return f"profile-type-assertion-batch:{digest}"
    @staticmethod
    def _profile_action_route_summary_groups(
        suggested_next_action_groups: Mapping[str, list[SuggestedNextAction]],
    ) -> dict[str, list[ProfileActionRouteSummary]]:
        return {
            group_name: [
                DoxaBase._profile_action_route_summary(
                    action,
                    action_group=group_name,
                    action_index=action_index,
                )
                for action_index, action in enumerate(actions)
            ]
            for group_name, actions in suggested_next_action_groups.items()
        }
    @staticmethod
    def _profile_action_route_summaries_from_groups(
        summary_groups: Mapping[str, list[ProfileActionRouteSummary]],
    ) -> list[ProfileActionRouteSummary]:
        return [
            summary
            for summaries in summary_groups.values()
            for summary in summaries
        ]
    @staticmethod
    def _profile_action_route_summary(
        action: SuggestedNextAction,
        *,
        action_group: str,
        action_index: int,
    ) -> ProfileActionRouteSummary:
        source_kind, source = DoxaBase._profile_action_route_source(action)
        review_lane = DoxaBase._string_field(
            getattr(action, "review_lane", None),
        ) or DoxaBase._string_field(source.get("review_lane"))
        semantic_move = DoxaBase._string_field(
            getattr(action, "semantic_move", None),
        ) or DoxaBase._string_field(source.get("semantic_move"))
        route_group_key = DoxaBase._string_field(
            getattr(action, "route_group_key", None),
        ) or DoxaBase._string_field(source.get("route_group_key"))
        route_step_key = DoxaBase._string_field(
            getattr(action, "route_step_key", None),
        ) or DoxaBase._string_field(source.get("route_step_key"))
        unattended_choice_role = DoxaBase._string_field(
            getattr(action, "unattended_choice_role", None),
        ) or DoxaBase._string_field(source.get("unattended_choice_role"))
        unattended_recommended_value = getattr(
            action,
            "unattended_recommended",
            source.get("unattended_recommended"),
        )
        consumes_binding_keys = DoxaBase._profile_route_binding_keys(
            source.get("consumes_result_bindings")
        )
        produces_binding_keys = DoxaBase._profile_route_binding_keys(
            source.get("produces_result_bindings")
        )
        action_kind = DoxaBase._profile_followthrough_primary_action_kind(
            action.tool_name
        )
        return ProfileActionRouteSummary(
            action_group=action_group,
            action_index=action_index,
            tool_name=action.tool_name,
            mcp_tool_name=action.mcp_tool_name,
            action_label=action.action_label,
            action_kind=action_kind,
            writes_graph=action_kind
            in {"stage_reviewable_change", "direct_graph_write"},
            review_lane=review_lane,
            semantic_move=semantic_move,
            route_group_key=route_group_key,
            route_step_key=route_step_key,
            source_kind=source_kind,
            advisory_indexes=DoxaBase._int_values(source.get("advisory_indexes")),
            recommendation_indexes=(
                DoxaBase._profile_route_recommendation_indexes(source)
            ),
            duplicate_group_keys=DoxaBase._string_values_from_any(
                source.get("duplicate_group_keys"),
            ),
            route_anchor_iris=DoxaBase._string_values_from_any(
                source.get("route_anchor_iris"),
            ),
            route_pattern_iris=DoxaBase._string_values_from_any(
                source.get("route_pattern_iris"),
            ),
            consumes_binding_keys=consumes_binding_keys,
            produces_binding_keys=produces_binding_keys,
            requires_result_bindings=(
                bool(consumes_binding_keys)
                and action_group
                not in {"ready_resolved_actions", "ready_resolved_mutations"}
            ),
            produces_result_bindings=bool(produces_binding_keys),
            unattended_choice_role=unattended_choice_role,
            unattended_recommended=bool(unattended_recommended_value),
            argument_keys=sorted(str(key) for key in action.arguments),
            has_arguments=bool(action.arguments),
            has_call=bool(action.call),
        )
    @staticmethod
    def _profile_action_route_source(
        action: SuggestedNextAction,
    ) -> tuple[str | None, MappingABC[str, Any]]:
        for source_kind, attr_name in (
            ("profile_advisory", "source_profile_advisory"),
            ("profile_map_update", "source_profile_map_update"),
            ("profile_scalar_conflict", "source_scalar_conflict"),
        ):
            source = getattr(action, attr_name, None)
            if isinstance(source, MappingABC):
                return source_kind, source
        return None, {}
    @staticmethod
    def _profile_route_binding_keys(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        binding_keys: list[str] = []
        for item in value:
            if not isinstance(item, MappingABC):
                continue
            binding_key = item.get("binding_key")
            if isinstance(binding_key, str):
                DoxaBase._append_unique(binding_keys, binding_key)
        return binding_keys
    @staticmethod
    def _profile_route_recommendation_indexes(
        source: MappingABC[str, Any],
    ) -> list[int]:
        indexes: list[int] = []
        for field_name in (
            "recommendation_indexes",
            "duplicate_recommendation_indexes",
            "representative_recommendation_indexes",
            "accepted_recommendation_indexes",
        ):
            for index in DoxaBase._int_values(source.get(field_name)):
                DoxaBase._append_unique(indexes, index)
        return indexes
    def _profile_mixed_support_review_groups(
        self,
        suggested_next_action_groups: Mapping[str, list[SuggestedNextAction]],
    ) -> list[ProfileMixedSupportReviewGroup]:
        grouped: dict[tuple[str, ...], dict[str, Any]] = {}
        group_order: list[tuple[str, ...]] = []
        for review_lane in ("metric_vocabulary_review", "profile_type_review"):
            for action in suggested_next_action_groups.get(review_lane, []):
                source = getattr(action, "source_profile_advisory", None)
                if not isinstance(source, MappingABC):
                    continue
                mixed_support = source.get("mixed_support")
                if not isinstance(mixed_support, MappingABC):
                    continue
                pattern_iris = tuple(
                    self._string_values_from_any(
                        mixed_support.get("pattern_iris")
                    )
                )
                if not pattern_iris:
                    continue
                if pattern_iris not in grouped:
                    grouped[pattern_iris] = {
                        "pattern_iris": list(pattern_iris),
                        "review_lanes": [],
                        "semantic_moves": [],
                        "route_group_keys": [],
                        "route_step_keys": [],
                        "route_anchor_iris": [],
                        "route_pattern_iris": [],
                        "tool_names": [],
                        "action_labels": [],
                        "suggested_next_calls": [],
                        "metric_advisory_indexes": [],
                        "type_advisory_indexes": [],
                        "duplicate_group_keys": [],
                        "duplicate_advisory_indexes": [],
                        "duplicate_profile_observation_iris": [],
                        "source_profile_advisories": [],
                    }
                    group_order.append(pattern_iris)
                item = grouped[pattern_iris]
                self._append_unique(item["review_lanes"], review_lane)
                semantic_move = self._profile_advisory_semantic_move(
                    action,
                    source,
                )
                if semantic_move is not None:
                    self._append_unique(item["semantic_moves"], semantic_move)
                route_group_key = source.get("route_group_key")
                if isinstance(route_group_key, str):
                    self._append_unique(
                        item["route_group_keys"],
                        route_group_key,
                    )
                self._append_unique(item["tool_names"], action.tool_name)
                self._append_unique(item["action_labels"], action.action_label)
                if action.call:
                    self._append_unique(item["suggested_next_calls"], action.call)
                self._append_profile_followthrough_source_fields(item, source)

        return [
            self._profile_mixed_support_review_group(
                group_index=group_index,
                item=grouped[key],
            )
            for group_index, key in enumerate(group_order)
        ]
    @staticmethod
    def _profile_mixed_support_review_group(
        *,
        group_index: int,
        item: Mapping[str, Any],
    ) -> ProfileMixedSupportReviewGroup:
        pattern_iris = list(item["pattern_iris"])
        review_lanes = list(item["review_lanes"])
        semantic_moves = list(item["semantic_moves"])
        note = (
            "Shared profile support pattern(s) feed multiple review lanes. "
            "Compare the grouped actions before applying, exporting, or "
            "treating any one lane as settled."
        )
        if review_lanes:
            note = f"{note} Review lanes: {', '.join(review_lanes)}."
        if semantic_moves:
            note = f"{note} Semantic moves: {', '.join(semantic_moves)}."
        return ProfileMixedSupportReviewGroup(
            group_index=group_index,
            pattern_iris=pattern_iris,
            pattern_count=len(pattern_iris),
            review_lanes=review_lanes,
            semantic_moves=semantic_moves,
            route_group_keys=list(item["route_group_keys"]),
            route_step_keys=list(item["route_step_keys"]),
            route_anchor_iris=list(item["route_anchor_iris"]),
            route_pattern_iris=list(item["route_pattern_iris"]),
            action_count=(
                len(item["route_step_keys"])
                or len(item["action_labels"])
                or len(item["suggested_next_calls"])
            ),
            tool_names=list(item["tool_names"]),
            action_labels=list(item["action_labels"]),
            suggested_next_calls=list(item["suggested_next_calls"]),
            metric_advisory_indexes=list(item["metric_advisory_indexes"]),
            type_advisory_indexes=list(item["type_advisory_indexes"]),
            duplicate_group_keys=list(item["duplicate_group_keys"]),
            duplicate_advisory_indexes=list(item["duplicate_advisory_indexes"]),
            duplicate_profile_observation_iris=list(
                item["duplicate_profile_observation_iris"]
            ),
            source_profile_advisories=list(item["source_profile_advisories"]),
            note=note,
        )
    @staticmethod
    def _string_values_from_any(values: Any) -> list[str]:
        if not isinstance(values, list):
            return []
        return [value for value in values if isinstance(value, str)]
    def _profile_query_context_review_actions(
        self,
        dataset: DatasetDescription,
        *,
        graph: str | None,
        evidence_iri: str,
        profile_quality_summary: Mapping[str, Any],
        sampled_evidence_caution: str | None,
    ) -> list[SuggestedNextAction]:
        if not self._profile_query_context_has_physical_intent(dataset):
            return []
        context = self.describe_query_context(dataset.iri, graph=graph)
        if context.readiness not in {
            "insufficient_metadata",
            "blocked_by_contradiction",
        }:
            return []
        blocking_issues = [
            issue
            for issue in context.issues
            if issue.severity == "error" or issue.code == "contradicted_layout"
        ]
        if not blocking_issues:
            return []
        issue_codes = self._query_issue_codes(blocking_issues)
        arguments: dict[str, Any] = {"iri": dataset.iri}
        if graph is not None and graph != "map":
            arguments["graph"] = graph
        issue_summary = ", ".join(issue_codes)
        reason = (
            "Query context has blocking physical metadata issue(s) "
            f"({issue_summary}) and readiness "
            f"'{context.readiness}'. Review or repair query context before "
            "treating profile-derived map updates as query-ready context."
        )
        route_group_key = self._profile_route_group_key(
            "query_context_review",
            {
                "dataset_iri": dataset.iri,
                "evidence_iri": evidence_iri,
                "readiness": context.readiness,
                "blocking_issue_codes": issue_codes,
            },
        )
        action = SuggestedNextAction(
            action_label="Review query context blockers",
            tool_name="describe_query_context",
            mcp_tool_name="doxabase.describe_query_context",
            arguments=arguments,
            reason=reason,
            call=self._suggested_call_string(
                "describe_query_context",
                arguments,
            ),
        )
        return [
            ProfileQueryContextSuggestedNextAction(
                action_label=action.action_label,
                tool_name=action.tool_name,
                mcp_tool_name=action.mcp_tool_name,
                arguments=action.arguments,
                reason=action.reason,
                call=action.call,
                source_query_context=self._with_profile_route_step_key(
                    {
                        "review_lane": "query_context_review",
                        "route_group_key": route_group_key,
                        "evidence_iri": evidence_iri,
                        "profile_evidence_iri": evidence_iri,
                        "route_anchor_iris": [dataset.iri],
                        "readiness": context.readiness,
                        "readiness_note": context.readiness_note,
                        "blocking_issue_codes": issue_codes,
                        "issue_codes": self._query_issue_codes(context.issues),
                        "suggested_repair_action_group_count": (
                            context.suggested_repair_action_group_count
                        ),
                        "profile_quality_summary": dict(profile_quality_summary),
                        "sampled_evidence_caution": sampled_evidence_caution,
                    },
                    action,
                ),
            )
        ]
    @staticmethod
    def _profile_query_context_has_physical_intent(
        dataset: DatasetDescription,
    ) -> bool:
        return bool(
            dataset.path_templates
            or dataset.physical_layouts
            or dataset.storage_accesses
            or dataset.partition_schemes
        )
    @staticmethod
    def _profile_quality_summary(
        recommendations: Iterable[ProfileMapUpdateRecommendation],
        *,
        metric_advisory_count: int = 0,
        type_advisory_count: int = 0,
    ) -> dict[str, Any]:
        recommendation_list = list(recommendations)
        basis_counts: dict[str, int] = {}
        default_stageable_basis_counts: dict[str, int] = {}
        sampled_recommendation_indexes: list[int] = []
        sampled_default_stageable_recommendation_indexes: list[int] = []
        sampled_row_count_recommendation_indexes: list[int] = []
        sample_scopes: list[str] = []
        sample_methods: list[str] = []
        for recommendation in recommendation_list:
            basis_counts[recommendation.basis] = (
                basis_counts.get(recommendation.basis, 0) + 1
            )
            if recommendation.default_stageable:
                default_stageable_basis_counts[recommendation.basis] = (
                    default_stageable_basis_counts.get(recommendation.basis, 0)
                    + 1
                )
            if recommendation.basis == "sample":
                sampled_recommendation_indexes.append(
                    recommendation.recommendation_index
                )
                if recommendation.default_stageable:
                    sampled_default_stageable_recommendation_indexes.append(
                        recommendation.recommendation_index
                    )
                if recommendation.kind == "dataset_row_count_snapshot":
                    sampled_row_count_recommendation_indexes.append(
                        recommendation.recommendation_index
                    )
                if recommendation.sample_scope:
                    DoxaBase._append_unique(sample_scopes, recommendation.sample_scope)
                if recommendation.sample_method:
                    DoxaBase._append_unique(
                        sample_methods,
                        recommendation.sample_method,
                    )
        return {
            "recommendation_count": len(recommendation_list),
            "basis_counts": basis_counts,
            "default_stageable_basis_counts": default_stageable_basis_counts,
            "sampled_recommendation_indexes": sampled_recommendation_indexes,
            "sampled_recommendation_count": len(sampled_recommendation_indexes),
            "sampled_default_stageable_recommendation_indexes": (
                sampled_default_stageable_recommendation_indexes
            ),
            "sampled_default_stageable_recommendation_count": len(
                sampled_default_stageable_recommendation_indexes
            ),
            "sampled_row_count_recommendation_indexes": (
                sampled_row_count_recommendation_indexes
            ),
            "sample_scopes": sample_scopes,
            "sample_methods": sample_methods,
            "metric_advisory_count": metric_advisory_count,
            "type_advisory_count": type_advisory_count,
        }
    @staticmethod
    def _profile_sampled_evidence_caution(
        profile_quality_summary: Mapping[str, Any],
    ) -> str | None:
        sampled_count = DoxaBase._profile_summary_count(
            profile_quality_summary.get("sampled_recommendation_count")
        )
        if sampled_count <= 0:
            return None
        sampled_stageable_count = DoxaBase._profile_summary_count(
            profile_quality_summary.get(
                "sampled_default_stageable_recommendation_count",
            )
        )
        row_count_indexes = DoxaBase._int_values(
            profile_quality_summary.get("sampled_row_count_recommendation_indexes")
        )
        if sampled_stageable_count:
            return (
                "Sampled profile evidence has default-stageable map "
                "recommendations. Mechanical readiness is not full-scan "
                "evidence; review sample_scope and sample_method before applying."
            )
        if row_count_indexes:
            return (
                "Sampled row-count profile recommendations are present and are "
                "skipped by default unless explicitly allowed after scope review."
            )
        return (
            "Sampled profile evidence is present. Review sample_scope and "
            "sample_method before treating recommendations as durable map facts."
        )
    @staticmethod
    def _profile_quality_summary_from_route_groups(
        groups: Iterable[MappingABC[str, Any]],
    ) -> dict[str, Any]:
        summaries: list[MappingABC[str, Any]] = []
        for group in groups:
            for summary in group.get("profile_quality_summaries") or []:
                if isinstance(summary, MappingABC):
                    summaries.append(summary)
        if not summaries:
            return {}

        basis_counts: dict[str, int] = {}
        default_stageable_basis_counts: dict[str, int] = {}
        sampled_recommendation_indexes: list[int] = []
        sampled_default_stageable_recommendation_indexes: list[int] = []
        sampled_row_count_recommendation_indexes: list[int] = []
        sample_scopes: list[str] = []
        sample_methods: list[str] = []
        recommendation_count = 0
        metric_advisory_count = 0
        type_advisory_count = 0

        def summary_count(value: Any) -> int:
            return DoxaBase._profile_summary_count(value)

        def merge_counts(target: dict[str, int], value: Any) -> None:
            if not isinstance(value, MappingABC):
                return
            for key, count in value.items():
                count_value = summary_count(count)
                if isinstance(key, str) and count_value:
                    target[key] = target.get(key, 0) + count_value

        for summary in summaries:
            recommendation_count += summary_count(
                summary.get("recommendation_count")
            )
            metric_advisory_count += summary_count(
                summary.get("metric_advisory_count")
            )
            type_advisory_count += summary_count(
                summary.get("type_advisory_count")
            )
            merge_counts(basis_counts, summary.get("basis_counts"))
            merge_counts(
                default_stageable_basis_counts,
                summary.get("default_stageable_basis_counts"),
            )
            for index in DoxaBase._int_values(
                summary.get("sampled_recommendation_indexes")
            ):
                DoxaBase._append_unique(sampled_recommendation_indexes, index)
            for index in DoxaBase._int_values(
                summary.get("sampled_default_stageable_recommendation_indexes")
            ):
                DoxaBase._append_unique(
                    sampled_default_stageable_recommendation_indexes,
                    index,
                )
            for index in DoxaBase._int_values(
                summary.get("sampled_row_count_recommendation_indexes")
            ):
                DoxaBase._append_unique(
                    sampled_row_count_recommendation_indexes,
                    index,
                )
            for scope in DoxaBase._string_values_from_any(
                summary.get("sample_scopes")
            ):
                DoxaBase._append_unique(sample_scopes, scope)
            for method in DoxaBase._string_values_from_any(
                summary.get("sample_methods")
            ):
                DoxaBase._append_unique(sample_methods, method)

        return {
            "recommendation_count": recommendation_count,
            "basis_counts": basis_counts,
            "default_stageable_basis_counts": default_stageable_basis_counts,
            "sampled_recommendation_indexes": sampled_recommendation_indexes,
            "sampled_recommendation_count": len(sampled_recommendation_indexes),
            "sampled_default_stageable_recommendation_indexes": (
                sampled_default_stageable_recommendation_indexes
            ),
            "sampled_default_stageable_recommendation_count": len(
                sampled_default_stageable_recommendation_indexes
            ),
            "sampled_row_count_recommendation_indexes": (
                sampled_row_count_recommendation_indexes
            ),
            "sample_scopes": sample_scopes,
            "sample_methods": sample_methods,
            "metric_advisory_count": metric_advisory_count,
            "type_advisory_count": type_advisory_count,
        }
    @staticmethod
    def _profile_route_key(prefix: str, payload: Any) -> str:
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:12]
        return f"{prefix}:{digest}"
    @staticmethod
    def _profile_route_group_key(review_lane: str, stable_parts: Any) -> str:
        return DoxaBase._profile_route_key(
            review_lane,
            {
                "review_lane": review_lane,
                "stable_parts": stable_parts,
            },
        )
    @staticmethod
    def _profile_route_step_argument_identity(
        arguments: MappingABC[str, Any],
    ) -> dict[str, Any]:
        identity: dict[str, Any] = {}
        for key in (
            "iri",
            "seed_iris",
            "dataset_iri",
            "evidence_iri",
            "accepted_recommendation_indexes",
            "supporting_patterns",
            "patterns",
            "anchors",
            "graph",
            "type",
            "text",
            "predicate",
            "change_kind",
            "profile",
            "revision_iris",
        ):
            if key in arguments:
                identity[key] = arguments[key]
        framings = arguments.get("framings")
        if isinstance(framings, list):
            identity["framings"] = [
                {
                    key: framing[key]
                    for key in ("label", "graph")
                    if key in framing
                }
                for framing in framings
                if isinstance(framing, MappingABC)
            ]
        return identity
    @staticmethod
    def _profile_route_step_key(
        route_group_key: str,
        action: SuggestedNextAction,
    ) -> str:
        arguments = action.arguments
        payload = {
            "route_group_key": route_group_key,
            "tool_name": action.tool_name,
            "action_label": action.action_label,
            "arguments": DoxaBase._profile_route_step_argument_identity(arguments),
        }
        return DoxaBase._profile_route_key("profile-route-step", payload)
    @staticmethod
    def _with_profile_route_step_key(
        source: dict[str, Any],
        action: SuggestedNextAction,
    ) -> dict[str, Any]:
        route_source = dict(source)
        route_group_key = str(route_source["route_group_key"])
        route_source["route_step_key"] = DoxaBase._profile_route_step_key(
            route_group_key,
            action,
        )
        return route_source
    def _profile_update_staging_actions(
        self,
        staged_revision: StagedGraphRevisionRecord | None,
        *,
        items: list[ProfileMapUpdateStagingItem],
        dataset_iri: str,
        evidence_iri: str,
    ) -> list[SuggestedNextAction]:
        actions: list[SuggestedNextAction] = []
        if staged_revision is None:
            return actions
        arguments = {"iri": staged_revision.revision_iri}
        actions.append(
            SuggestedNextAction(
                action_label="Check staged profile map updates",
                tool_name="check_staged_revision_apply",
                mcp_tool_name="doxabase.check_staged_revision_apply",
                arguments=arguments,
                reason=(
                    "Run the read-only apply check before reviewing, exporting, "
                    "or applying the grouped profile-derived map revision."
                ),
                call=self._suggested_call_string(
                    "check_staged_revision_apply",
                    arguments,
                ),
            )
        )
        export_arguments = {
            "dataset_iri": dataset_iri,
            "evidence_iri": evidence_iri,
            "path": self._suggested_review_export_path(
                "profile-insight-review",
                [staged_revision.revision_iri],
            ),
            "revision_iris": [staged_revision.revision_iri],
            "overwrite": True,
        }
        actions.append(
            SuggestedNextAction(
                action_label="Export profile insight review bundle",
                tool_name="export_profile_insight_review_bundle",
                mcp_tool_name="doxabase.export_profile_insight_review_bundle",
                arguments=export_arguments,
                reason=(
                    "Export a grouped review bundle for staged revisions tied "
                    "to this profile run. Re-run this export after staging any "
                    "related metric vocabulary, type-review, or caveat "
                    "alternatives so the bundle can compare the lanes together."
                ),
                call=self._suggested_call_string(
                    "export_profile_insight_review_bundle",
                    export_arguments,
                ),
            )
        )
        if any(
            item.status == "staged" and item.kind == "unmapped_profiled_column"
            for item in items
        ):
            rerun_arguments = {
                "dataset_iri": dataset_iri,
                "evidence_iri": evidence_iri,
            }
            actions.append(
                ProfileMapUpdateRerunSuggestedNextAction(
                    action_label="Rerun profile map update draft",
                    tool_name="draft_profile_map_updates",
                    mcp_tool_name="doxabase.draft_profile_map_updates",
                    arguments=rerun_arguments,
                    reason=(
                        "After reviewing and applying the staged unmapped "
                        "column shell(s), rerun the profile map-update draft "
                        "for the same dataset and evidence so type advisories "
                        "and follow-up map recommendations can reclassify "
                        "against map-present columns."
                    ),
                    call=self._suggested_call_string(
                        "draft_profile_map_updates",
                        rerun_arguments,
                    ),
                    preconditions={
                        "staged_revision_applied": staged_revision.revision_iri,
                        "why": (
                            "The rerun only reflects the newly mapped column "
                            "after the staged profile map-update revision has "
                            "been reviewed and applied."
                        ),
                    },
                )
            )
        return actions
    @staticmethod
    def _profile_update_representative_indexes(
        recommendations: list[ProfileMapUpdateRecommendation],
    ) -> list[int]:
        representatives: list[int] = []
        seen_group_keys: set[str] = set()
        for recommendation in recommendations:
            group_key = (
                recommendation.duplicate_group_key
                or f"recommendation:{recommendation.recommendation_index}"
            )
            if group_key in seen_group_keys:
                continue
            seen_group_keys.add(group_key)
            representatives.append(recommendation.recommendation_index)
        return representatives
    @staticmethod
    def _profile_update_scalar_value_key(value: Any) -> str:
        payload = {
            "type": type(value).__name__,
            "value": to_jsonable(value),
        }
        return json.dumps(payload, sort_keys=True, default=str)
    @staticmethod
    def _profile_update_scalar_value_label(value: Any) -> str:
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, str):
            return repr(value)
        return str(value)
    @staticmethod
    def _profile_update_add_scalar_observed_value(
        value_groups: dict[tuple[str, str, str, str], list[Any]],
        *,
        evidence_iri: str,
        resource_iri: str,
        predicate: str,
        kind: str,
        observed_value: Any,
    ) -> None:
        group_key = (evidence_iri, resource_iri, predicate, kind)
        value_groups.setdefault(group_key, []).append(observed_value)
    @staticmethod
    def _profile_update_current_equal_conflict_skip_reason(reason: str | None) -> bool:
        return bool(
            reason
            and reason.startswith(
                "Same-evidence profile observations include conflicting values"
            )
        )
    def _with_profile_update_default_staging_metadata(
        self,
        recommendations: list[ProfileMapUpdateRecommendation],
        *,
        current_equal_scalar_values: Mapping[
            tuple[str, str, str, str],
            Iterable[Any],
        ]
        | None = None,
    ) -> list[ProfileMapUpdateRecommendation]:
        conflict_skip_reasons = self._profile_update_scalar_conflict_skip_reasons(
            recommendations,
            current_equal_scalar_values=current_equal_scalar_values,
        )
        annotated: list[ProfileMapUpdateRecommendation] = []
        for recommendation in recommendations:
            default_skip_reason = conflict_skip_reasons.get(
                recommendation.recommendation_index
            )
            if default_skip_reason is None:
                default_skip_reason = self._profile_update_skip_reason(
                    recommendation,
                    allow_sampled_row_count_updates=False,
                )
            annotated.append(
                replace(
                    recommendation,
                    default_stageable=default_skip_reason is None,
                    default_skip_reason=default_skip_reason,
                )
            )
        return annotated
    def _with_profile_update_duplicate_metadata(
        self,
        recommendations: list[ProfileMapUpdateRecommendation],
    ) -> list[ProfileMapUpdateRecommendation]:
        groups: dict[str, list[ProfileMapUpdateRecommendation]] = {}
        for recommendation in recommendations:
            groups.setdefault(
                self._profile_update_duplicate_group_key(recommendation),
                [],
            ).append(recommendation)

        annotated: list[ProfileMapUpdateRecommendation] = []
        for recommendation in recommendations:
            group_key = self._profile_update_duplicate_group_key(recommendation)
            group = groups[group_key]
            annotated.append(
                replace(
                    recommendation,
                    duplicate_group_key=group_key,
                    duplicate_count=len(group),
                    duplicate_recommendation_indexes=[
                        item.recommendation_index for item in group
                    ],
                    duplicate_profile_observation_iris=list(
                        dict.fromkeys(item.profile_observation_iri for item in group)
                    ),
                )
            )
        return annotated
    @staticmethod
    def _profile_update_duplicate_group_key(
        recommendation: ProfileMapUpdateRecommendation,
    ) -> str:
        if recommendation.kind == "unmapped_profiled_column":
            payload = {
                "kind": recommendation.kind,
                "action": recommendation.action,
                "resource_iri": recommendation.resource.iri,
                "predicate": recommendation.predicate,
                "helper_name": recommendation.helper_name,
                "helper_arguments": recommendation.helper_arguments,
            }
        else:
            payload = {
                "kind": recommendation.kind,
                "action": recommendation.action,
                "resource_iri": recommendation.resource.iri,
                "predicate": recommendation.predicate,
                "current_value": recommendation.current_value,
                "observed_value": recommendation.observed_value,
                "observed_count": recommendation.observed_count,
                "sample_size": recommendation.sample_size,
                "sample_scope": recommendation.sample_scope,
                "sample_method": recommendation.sample_method,
                "profile_row_count": recommendation.profile_row_count,
                "evidence_iri": recommendation.evidence_iri,
                "basis": recommendation.basis,
                "confidence": recommendation.confidence,
                "helper_name": recommendation.helper_name,
                "helper_arguments": recommendation.helper_arguments,
            }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:12]
        return f"profile-map-update:{digest}"
    def _profile_update_accepted_indexes(
        self,
        accepted_recommendation_indexes: Iterable[int] | None,
    ) -> list[int]:
        if accepted_recommendation_indexes is None:
            raise DoxaBaseError(
                "accepted_recommendation_indexes must name at least one "
                "accepted draft recommendation"
            )
        indexes: list[int] = []
        for value in accepted_recommendation_indexes:
            if isinstance(value, bool) or not isinstance(value, int):
                raise DoxaBaseError(
                    "accepted_recommendation_indexes values must be integers"
                )
            if value < 0:
                raise DoxaBaseError(
                    "accepted_recommendation_indexes values must be non-negative"
                )
            indexes.append(value)
        indexes = list(dict.fromkeys(indexes))
        if not indexes:
            raise DoxaBaseError(
                "accepted_recommendation_indexes must name at least one "
                "accepted draft recommendation"
            )
        return indexes
    @staticmethod
    def _profile_update_status_counts(
        items: list[ProfileMapUpdateStagingItem],
    ) -> dict[str, int]:
        counts = {"staged": 0, "skipped": 0, "not_selected": 0}
        for item in items:
            counts[item.status] = counts.get(item.status, 0) + 1
        return counts
    def _profile_update_skip_reason(
        self,
        recommendation: ProfileMapUpdateRecommendation,
        *,
        allow_sampled_row_count_updates: bool,
    ) -> str | None:
        if (
            recommendation.kind == "dataset_row_count_snapshot"
            and recommendation.basis != "full_scan"
            and not allow_sampled_row_count_updates
        ):
            return (
                "Sampled or unknown-scope row-count recommendations are not "
                "staged by default; set allow_sampled_row_count_updates=True "
                "only when the profile scope is the intended durable "
                "population."
            )
        return None
    def _profile_update_revision_anchors(
        self,
        recommendation: ProfileMapUpdateRecommendation,
        *,
        dataset_iri: str,
    ) -> list[str]:
        return list(dict.fromkeys([dataset_iri, recommendation.resource.iri]))
    def _profile_update_staging_review_note(
        self,
        items: list[ProfileMapUpdateStagingItem],
        *,
        staged_indexes: list[int],
        skipped_indexes: list[int],
        status_counts: dict[str, int],
        metric_advisory_count: int,
        metric_advisory_status_counts: dict[str, int],
        type_advisory_count: int,
        type_advisory_status_counts: dict[str, int],
        allow_sampled_row_count_updates: bool,
    ) -> str:
        staged_summary = ", ".join(str(index) for index in staged_indexes) or "none"
        skipped_summary = ", ".join(str(index) for index in skipped_indexes) or "none"
        status_summary = ", ".join(
            f"{status}={count}" for status, count in status_counts.items()
        )
        metric_advisory_summary = self._profile_metric_advisory_review_summary(
            metric_advisory_count,
            metric_advisory_status_counts,
        )
        type_advisory_summary = self._profile_type_advisory_review_summary(
            type_advisory_count,
            type_advisory_status_counts,
        )
        type_followthrough_note = ""
        if type_advisory_status_counts.get(
            "type_finding_unmapped_column",
            0,
        ) and any(
            item.status == "staged" and item.kind == "unmapped_profiled_column"
            for item in items
        ):
            type_followthrough_note = (
                " After applying staged unmapped column shells, rerun "
                "draft_profile_map_updates for the same dataset and evidence "
                "so related profile type advisories can reclassify against "
                "map-present columns."
            )
        evidence_summary = "; ".join(
            (
                f"{item.recommendation_index}:{item.kind}:"
                f"{item.status}:basis={item.basis}:confidence={item.confidence}"
            )
            for item in items
        )
        return (
            "Generated by stage_profile_map_updates. Staged recommendation "
            f"indexes: {staged_summary}. Skipped accepted indexes: "
            f"{skipped_summary}. Status counts: {status_summary}. "
            "allow_sampled_row_count_updates="
            f"{allow_sampled_row_count_updates}. Review sample scope, evidence, "
            "caveats, and project modelling intent before applying. "
            "Metric vocabulary advisories (review separately; not staged as map "
            f"patches): {metric_advisory_summary}. Profile type advisories "
            "(review separately; not staged as map patches): "
            f"{type_advisory_summary}.{type_followthrough_note} "
            f"Items: {evidence_summary}"
        )
    def _add_profile_update_patch_triples(
        self,
        recommendation: ProfileMapUpdateRecommendation,
        *,
        dataset_iri: str,
        map_dataset_found: bool,
        additions_graph: Graph,
        removals_graph: Graph,
    ) -> None:
        if recommendation.kind == "dataset_row_count_snapshot":
            if not isinstance(recommendation.observed_value, int):
                raise DoxaBaseError(
                    "dataset_row_count_snapshot recommendations require an "
                    "integer observed value"
                )
            subject = URIRef(dataset_iri)
            if map_dataset_found:
                self._add_profile_update_current_triples_to_graph(
                    removals_graph,
                    subject=dataset_iri,
                    predicate="rc:rowCountSnapshot",
                )
            else:
                additions_graph.add(
                    (
                        subject,
                        RDF.type,
                        URIRef(self.expand_iri("rc:Dataset")),
                    )
                )
            additions_graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:rowCountSnapshot")),
                    Literal(recommendation.observed_value, datatype=XSD.integer),
                )
            )
            return

        if recommendation.kind == "column_nullable":
            if not isinstance(recommendation.observed_value, bool):
                raise DoxaBaseError(
                    "column_nullable recommendations require a boolean observed value"
                )
            self._add_profile_update_current_triples_to_graph(
                removals_graph,
                subject=recommendation.resource.iri,
                predicate="rc:nullable",
            )
            additions_graph.add(
                (
                    URIRef(recommendation.resource.iri),
                    URIRef(self.expand_iri("rc:nullable")),
                    Literal(recommendation.observed_value, datatype=XSD.boolean),
                )
            )
            return

        if recommendation.kind == "unmapped_profiled_column":
            column_name = str(recommendation.observed_value).strip()
            if not column_name:
                raise DoxaBaseError(
                    "unmapped_profiled_column recommendations require a column name"
                )
            dataset_ref = URIRef(dataset_iri)
            column_ref = URIRef(recommendation.resource.iri)
            if not map_dataset_found:
                additions_graph.add(
                    (
                        dataset_ref,
                        RDF.type,
                        URIRef(self.expand_iri("rc:Dataset")),
                    )
                )
            additions_graph.add(
                (
                    column_ref,
                    RDF.type,
                    URIRef(self.expand_iri("rc:Column")),
                )
            )
            additions_graph.add(
                (
                    column_ref,
                    URIRef(self.expand_iri("rc:columnName")),
                    Literal(column_name),
                )
            )
            additions_graph.add(
                (
                    dataset_ref,
                    URIRef(self.expand_iri("rc:hasColumn")),
                    column_ref,
                )
            )
            return

        raise DoxaBaseError(
            f"Unsupported profile map update recommendation kind: {recommendation.kind}"
        )
    def _add_profile_update_current_triples_to_graph(
        self,
        target_graph: Graph,
        *,
        subject: str,
        predicate: str,
    ) -> None:
        for triple in self._assertion_triples(
            ["map"],
            subject=self.expand_iri(subject),
            predicate=self.expand_iri(predicate),
            object_filter=None,
            limit=1000,
        ):
            target_graph.add(
                (
                    self._subject_node_from_resource_triple(triple),
                    URIRef(triple.predicate),
                    self._object_node_from_resource_triple(triple),
                )
            )
    def _query_context_singleton_profile_evidence_actions(
        self,
        dataset: DatasetDescription,
        profile_summary: ProfileSummary,
        *,
        issues: list[QueryPlanningIssue],
    ) -> list[SuggestedNextAction]:
        evidence_iris = [
            evidence_iri
            for evidence_iri in profile_summary.evidence_iris
            if profile_summary.evidence_profile_counts.get(evidence_iri, 0) > 0
        ]
        if not evidence_iris:
            return []
        profiles_by_evidence = self._query_context_profiles_by_evidence(dataset)
        action_limit = 3
        actions: list[SuggestedNextAction] = []
        for action_index, evidence_iri in enumerate(evidence_iris[:action_limit]):
            arguments = {
                "dataset_iri": dataset.iri,
                "evidence_iri": evidence_iri,
            }
            omitted_count = 0
            if action_index == action_limit - 1:
                omitted_count = max(len(evidence_iris) - action_limit, 0)
            omitted_note = (
                f" {omitted_count} additional singleton profile evidence IRI(s) "
                "are listed in profile_summary.evidence_iris."
                if omitted_count
                else ""
            )
            source_profile_evidence = self._query_context_source_profile_evidence(
                evidence_iri,
                profiles_by_evidence.get(evidence_iri, []),
            )
            actions.append(
                ProfileEvidenceSuggestedNextAction(
                    action_label="Inspect singleton profile evidence",
                    tool_name="describe_profile_run",
                    mcp_tool_name="doxabase.describe_profile_run",
                    arguments=arguments,
                    reason=(
                        "This query context has profile evidence, but no "
                        "multi-observation profile_run_candidates. Inspect this "
                        "singleton evidence before draft_query_plan; it may be a "
                        "recorded external query result or another one-observation "
                        "profile handoff."
                        f"{omitted_note}"
                    ),
                    call=self._suggested_call_string(
                        "describe_profile_run",
                        arguments,
                    ),
                    source_profile_evidence=source_profile_evidence,
                )
            )
            if self._query_context_should_suggest_evidence_storage_overlay(
                issues
            ):
                actions.append(
                    self._query_context_evidence_storage_overlay_action(
                        dataset_iri=dataset.iri,
                        evidence_iri=evidence_iri,
                        source_profile_evidence=source_profile_evidence,
                    )
                )
        return actions
    def _query_context_profiles_by_evidence(
        self,
        dataset: DatasetDescription,
    ) -> dict[str, list[ProfileObservationSummary]]:
        profiles = [
            *dataset.profile_observations,
            *dataset.unmapped_column_profile_observations,
            *(
                profile
                for column in dataset.columns
                for profile in column.profile_observations
            ),
        ]
        profiles_by_evidence: dict[str, dict[str, ProfileObservationSummary]] = {}
        for profile in profiles:
            for evidence in profile.evidence:
                profiles_by_evidence.setdefault(evidence.iri, {})[profile.iri] = profile
        return {
            evidence_iri: list(profile_by_iri.values())
            for evidence_iri, profile_by_iri in profiles_by_evidence.items()
        }
    def _query_context_source_profile_evidence(
        self,
        evidence_iri: str,
        profiles: list[ProfileObservationSummary],
        *,
        evidence: EvidenceDescription | None = None,
    ) -> dict[str, Any]:
        evidence = evidence or self._profile_evidence_description(
            evidence_iri,
            profiles,
        )
        evidence_summary = evidence.summary if evidence is not None else None
        metadata = self._query_result_metadata_from_evidence(evidence)
        result_sources = evidence.sources if evidence is not None else []
        source_spans = evidence.source_spans if evidence is not None else []
        query_source_kind = self.expand_iri("rc:QuerySource")
        scanned_source_kind = self.expand_iri("rc:DataSampleSource")
        query_source_spans = [
            span for span in source_spans if span.source_kind == query_source_kind
        ]
        scanned_source_spans = [
            span for span in source_spans if span.source_kind == scanned_source_kind
        ]
        preview_span_by_iri = {
            span.iri: span for span in [*query_source_spans, *scanned_source_spans]
        }
        preview_spans = list(preview_span_by_iri.values()) or source_spans
        result_source_limit = 5
        span_limit = 3
        profile_limit = 3
        query_source_paths = [
            span.source_path for span in query_source_spans if span.source_path
        ]
        scanned_source_paths = [
            span.source_path for span in scanned_source_spans if span.source_path
        ]
        scanned_source_handles = (
            list(dict.fromkeys(evidence.scanned_source_handles))
            if evidence is not None
            else []
        )
        if not scanned_source_handles:
            scanned_source_handles = list(dict.fromkeys(scanned_source_paths))
        return {
            "evidence_iri": evidence_iri,
            "profile_observation_count": len(profiles),
            "profile_observation_iris": [profile.iri for profile in profiles],
            "profile_summaries": [
                self._query_context_profile_summary_preview(profile)
                for profile in profiles[:profile_limit]
            ],
            "omitted_profile_summary_count": max(len(profiles) - profile_limit, 0),
            "evidence_summary": evidence_summary,
            "execution_status": metadata["execution_status"],
            "engine": metadata["engine"],
            "query_hash": metadata["query_hash"],
            "result_sources": result_sources[:result_source_limit],
            "omitted_result_source_count": max(
                len(result_sources) - result_source_limit,
                0,
            ),
            "query_source_paths": query_source_paths[:span_limit],
            "scanned_source_paths": scanned_source_paths[:result_source_limit],
            "scanned_source_handles": scanned_source_handles[:result_source_limit],
            "query_source_spans": [
                self._query_context_source_span_preview(span)
                for span in preview_spans[:span_limit]
            ],
            "omitted_query_source_span_count": max(
                len(preview_spans) - span_limit,
                0,
            ),
            "omitted_scanned_source_path_count": max(
                len(scanned_source_paths) - result_source_limit,
                0,
            ),
            "omitted_scanned_source_handle_count": max(
                len(scanned_source_handles) - result_source_limit,
                0,
            ),
            "handoff_note": (
                "Singleton profile evidence is not a profile_run_candidate because "
                "it is attached to one returned profile observation; use "
                "describe_profile_run for the full bounded handoff."
                if profiles
                else (
                    "Query evidence is linked to the dataset without profile "
                    "observation rows; use it as reviewed query provenance, not "
                    "as profile-derived map truth."
                )
            ),
        }
    @staticmethod
    def _profile_evidence_description(
        evidence_iri: str,
        profiles: list[ProfileObservationSummary],
    ) -> EvidenceDescription | None:
        for profile in profiles:
            for evidence in profile.evidence:
                if evidence.iri == evidence_iri:
                    return evidence
        return None
    def _profile_observations_for_target(
        self,
        *,
        target_iri: str,
        target_predicate: str,
        exclude_observed_column: bool = False,
        limit: int | None = 5,
    ) -> list[ProfileObservationSummary]:
        lookup_graphs = self._lookup_graphs(self._expand_graphs(["all"]))
        observation_iris = self._profile_observation_iris_for_target(
            target_iri=target_iri,
            target_predicate=target_predicate,
            exclude_observed_column=exclude_observed_column,
        )
        summaries = [
            self._profile_observation_summary(observation_iri, lookup_graphs)
            for observation_iri in observation_iris
        ]
        summaries.sort(
            key=self._profile_observation_sort_key,
            reverse=True,
        )
        return summaries if limit is None else summaries[:limit]
    def _profile_observation_sort_key(
        self,
        profile: ProfileObservationSummary,
    ) -> tuple[str, str, str]:
        return (
            profile.observed_at or "",
            profile.summary or "",
            profile.iri,
        )
    def _missing_dataset_profile_hint(
        self,
        dataset_iri: str,
        display_iri: str,
    ) -> str:
        profile_observation_iris = self._profile_observation_iris_for_target(
            target_iri=dataset_iri,
            target_predicate="rc:observedAsset",
        )
        if not profile_observation_iris:
            return ""
        evidence_counts: dict[str, int] = {}
        for observation_iri in profile_observation_iris:
            for evidence_iri in self._objects(
                ["observations"],
                observation_iri,
                "rc:evidence",
            ):
                evidence_counts[evidence_iri] = evidence_counts.get(evidence_iri, 0) + 1
        hint = (
            f"; {len(profile_observation_iris)} profile observation(s) reference "
            "this dataset in the observations graph. "
        )
        if evidence_counts:
            evidence_iri = sorted(
                evidence_counts,
                key=lambda item: (-evidence_counts[item], item),
            )[0]
            hint += (
                "For a profile-only handoff, try "
                f"describe_profile_run({display_iri!r}, {evidence_iri!r}) or "
            )
        else:
            hint += "For a profile-only handoff, "
        return (
            hint
            + "seed get_context_graph from the profile observation IRIs. "
            "Record map dataset context with record_map_dataset before using "
            "describe_dataset."
        )
    def _profile_observation_iris_for_target(
        self,
        *,
        target_iri: str,
        target_predicate: str,
        exclude_observed_column: bool = False,
    ) -> list[str]:
        observation_graphs = ["observations"]
        profile_type = self.expand_iri("rc:ProfileObservation")
        return [
            observation_iri
            for observation_iri in self._subjects(
                observation_graphs,
                target_predicate,
                target_iri,
            )
            if profile_type
            in self._types_from_graphs(observation_graphs, observation_iri)
            and (
                not exclude_observed_column
                or self._first_object(
                    observation_graphs,
                    observation_iri,
                    "rc:observedColumn",
                )
                is None
            )
        ]
    def _profile_observation_count_for_target(
        self,
        *,
        target_iri: str,
        target_predicate: str,
        exclude_observed_column: bool = False,
    ) -> int:
        return len(
            self._profile_observation_iris_for_target(
                target_iri=target_iri,
                target_predicate=target_predicate,
                exclude_observed_column=exclude_observed_column,
            )
        )
    def _unmapped_column_profile_observations_for_dataset(
        self,
        dataset_iri: str,
        *,
        mapped_column_iris: Iterable[str],
        limit: int | None = 5,
    ) -> list[ProfileObservationSummary]:
        mapped_columns = set(mapped_column_iris)
        profile_observations = self._profile_observations_for_target(
            target_iri=dataset_iri,
            target_predicate="rc:observedAsset",
            limit=None,
        )
        return [
            profile
            for profile in profile_observations
            if profile.observed_column is not None
            and profile.observed_column.iri not in mapped_columns
        ][:limit]
    def _profiles_with_evidence(
        self,
        profiles: Iterable[ProfileObservationSummary],
        evidence_iri: str,
    ) -> list[ProfileObservationSummary]:
        return [
            profile
            for profile in profiles
            if any(evidence.iri == evidence_iri for evidence in profile.evidence)
        ]
    def _unmapped_column_profile_observation_count_for_dataset(
        self,
        dataset_iri: str,
        *,
        mapped_column_iris: Iterable[str],
    ) -> int:
        mapped_columns = set(mapped_column_iris)
        observation_graphs = ["observations"]
        return sum(
            1
            for observation_iri in self._profile_observation_iris_for_target(
                target_iri=dataset_iri,
                target_predicate="rc:observedAsset",
            )
            if (
                observed_column := self._first_object(
                    observation_graphs,
                    observation_iri,
                    "rc:observedColumn",
                )
            )
            is not None
            and observed_column not in mapped_columns
        )
    @staticmethod
    def _profile_row_count_snapshot_basis(
        row_count_snapshot: int | None,
        row_count_bases: dict[int, set[str]],
    ) -> str | None:
        if row_count_snapshot is None or row_count_snapshot not in row_count_bases:
            return None
        bases = sorted(row_count_bases[row_count_snapshot])
        if len(bases) == 1:
            return bases[0]
        return "mixed"
    def _profile_observation_basis(self, profile: ProfileObservationSummary) -> str:
        return self._profile_observation_basis_from_values(
            sample_size=profile.sample_size,
            sample_scope=profile.sample_scope,
            sample_method=profile.sample_method,
            row_count=profile.row_count,
        )
    @staticmethod
    def _profile_observation_basis_from_values(
        *,
        sample_size: int | None,
        sample_scope: str | None,
        sample_method: str | None,
        row_count: int | None,
    ) -> str:
        text = " ".join(
            value.lower()
            for value in (sample_method, sample_scope)
            if value
        )
        sample_markers = ("sample", "sampled", "sampling")
        if any(marker in text for marker in sample_markers):
            return "sample"
        full_scan_markers = (
            "full scan",
            "full-table",
            "full table",
            "complete scan",
            "all rows",
            "all records",
            "entire table",
            "whole table",
        )
        if (
            any(marker in text for marker in full_scan_markers)
            or (
                sample_size is not None
                and row_count is not None
                and sample_size == row_count
            )
        ):
            return "full_scan"
        if sample_size is not None or "sample" in text:
            return "sample"
        return "unknown"
    def _profile_map_column_name(
        self,
        column: ColumnDescription,
        profile: ProfileObservationSummary,
    ) -> str:
        return (
            column.column_name
            or profile.observed_column_name
            or (profile.observed_column.column_name if profile.observed_column else None)
            or (profile.observed_column.label if profile.observed_column else None)
            or column.iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]
        )
    def _profile_observed_column_name(
        self,
        profile: ProfileObservationSummary,
    ) -> str | None:
        if profile.observed_column is None:
            return None
        return (
            profile.observed_column_name
            or profile.observed_column.column_name
            or profile.observed_column.label
            or profile.observed_column.iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]
        )
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
            inspect_label = "Inspect pending value type vocabulary promotion"
            export_label = "Export pending value type vocabulary promotions"
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
            inspect_label = "Inspect pending profile type assertion"
            export_label = "Export pending profile type assertions"
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
                    action_label=inspect_label,
                    tool_name="describe_staged_revision",
                    mcp_tool_name="doxabase.describe_staged_revision",
                    arguments=arguments,
                    reason=inspect_reason,
                    call=self._suggested_call_string(
                        "describe_staged_revision",
                        arguments,
                    ),
                )
            )
        arguments = {
            "revision_iris": list(pending_staged_iris),
            "path": self._suggested_review_export_path(
                export_slug,
                pending_staged_iris,
            ),
            "fail_on_sensitive": True,
        }
        actions.append(
            SuggestedNextAction(
                action_label=export_label,
                tool_name="export_staged_revisions",
                mcp_tool_name="doxabase.export_staged_revisions",
                arguments=arguments,
                reason=export_reason,
                call=self._suggested_call_string(
                    "export_staged_revisions",
                    arguments,
                ),
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
                    action_label="Inspect pending profile fallback",
                    tool_name="describe_staged_revision",
                    mcp_tool_name="doxabase.describe_staged_revision",
                    arguments=arguments,
                    reason=(
                        "A current staged profile fallback already covers this "
                        "route. Inspect it before drafting another fallback for "
                        "the same advisory."
                    ),
                    call=self._suggested_call_string(
                        "describe_staged_revision",
                        arguments,
                    ),
                )
            )
        arguments = {
            "revision_iris": list(pending_staged_fallback_iris),
            "path": self._suggested_review_export_path(
                "profile-fallback-pending",
                pending_staged_fallback_iris,
            ),
            "fail_on_sensitive": True,
        }
        actions.append(
            SuggestedNextAction(
                action_label="Export pending profile fallbacks",
                tool_name="export_staged_revisions",
                mcp_tool_name="doxabase.export_staged_revisions",
                arguments=arguments,
                reason=(
                    "Write a grouped review bundle for the pending staged "
                    "profile fallback(s) before deciding whether more fallback "
                    "work is needed. The export blocks if scanner-matching "
                    "content appears before export."
                ),
                call=self._suggested_call_string(
                    "export_staged_revisions",
                    arguments,
                ),
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
    def _append_unique(values: list[Any], value: Any) -> None:
        if value not in values:
            values.append(value)
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
    def _profile_handoff_note(
        self,
        *,
        returned_profile_count: int,
        unmapped_column_profile_count: int,
        shared_evidence_count: int,
        omitted_profile_count: int,
    ) -> str:
        if returned_profile_count == 0:
            return (
                "No profile observations are included in this bounded dataset "
                "description; do not treat that as evidence that profiling has "
                "never been run."
            )
        note = (
            f"This bounded dataset description includes {returned_profile_count} "
            "profile observation(s). Profile lore is observed evidence, not "
            "physical query-planning metadata; storage/path/layout warnings "
            "remain physical metadata gaps rather than profile-recording failures."
        )
        if unmapped_column_profile_count:
            note += (
                f" {unmapped_column_profile_count} returned column profile(s) "
                "are not mapped as current columns."
            )
        if shared_evidence_count:
            note += (
                " At least one evidence resource is shared by every returned "
                "profile observation, which usually indicates one profiler run."
            )
        if omitted_profile_count:
            note += (
                f" {omitted_profile_count} additional profile observation(s) "
                "exist beyond this bounded response."
            )
        return note
    def _profile_observation_summary(
        self,
        observation_iri: str,
        lookup_graphs: list[str],
    ) -> ProfileObservationSummary:
        observation_graphs = ["observations"]
        evidence_graphs = ["evidence"]
        observed_asset = self._first_object(
            observation_graphs,
            observation_iri,
            "rc:observedAsset",
        )
        observed_column = self._first_object(
            observation_graphs,
            observation_iri,
            "rc:observedColumn",
        )
        observed_column_name = self._first_object(
            observation_graphs,
            observation_iri,
            "rc:observedColumnName",
        )
        observed_physical_type = self._first_object(
            observation_graphs,
            observation_iri,
            "rc:observedPhysicalType",
        )
        observed_value_type = self._first_object(
            observation_graphs,
            observation_iri,
            "rc:observedValueType",
        )
        redacted_observed_column_name = self._redact_sensitive_optional_text(
            observed_column_name
        )
        return ProfileObservationSummary(
            iri=observation_iri,
            summary=self._redact_sensitive_optional_text(
                self._first_object(observation_graphs, observation_iri, "rc:summary")
            ),
            observed_at=self._redact_sensitive_optional_text(
                self._first_object(
                    observation_graphs,
                    observation_iri,
                    "rc:observedAt",
                )
            ),
            observed_by=self._redact_sensitive_optional_text(
                self._first_object(
                    observation_graphs,
                    observation_iri,
                    "rc:observedBy",
                )
            ),
            observed_asset=(
                self._privacy_redacted_resource_summary(
                    self._resource_summary(lookup_graphs, observed_asset)
                )
                if observed_asset is not None
                else None
            ),
            observed_column=(
                self._privacy_redacted_resource_summary(
                    self._profile_observed_column_summary(
                        lookup_graphs,
                        observed_column,
                        observed_column_name=redacted_observed_column_name,
                    )
                )
                if observed_column is not None
                else None
            ),
            observed_column_name=redacted_observed_column_name,
            observed_physical_type=self._privacy_redacted_optional_resource_summary(
                self._optional_resource_summary(
                    lookup_graphs,
                    observed_physical_type,
                )
            ),
            observed_value_type=self._privacy_redacted_optional_resource_summary(
                self._optional_resource_summary(
                    lookup_graphs,
                    observed_value_type,
                )
            ),
            sample_size=self._int_object(
                observation_graphs,
                observation_iri,
                "rc:sampleSize",
            ),
            sample_scope=self._redact_sensitive_optional_text(
                self._first_object(
                    observation_graphs,
                    observation_iri,
                    "rc:sampleScope",
                )
            ),
            sample_method=self._redact_sensitive_optional_text(
                self._first_object(
                    observation_graphs,
                    observation_iri,
                    "rc:sampleMethod",
                )
            ),
            row_count=self._int_object(
                observation_graphs,
                observation_iri,
                "rc:rowCount",
            ),
            null_count=self._int_object(
                observation_graphs,
                observation_iri,
                "rc:nullCount",
            ),
            distinct_count=self._int_object(
                observation_graphs,
                observation_iri,
                "rc:distinctCount",
            ),
            value_frequencies=self._observed_value_frequency_summaries(
                observation_graphs,
                observation_iri,
            ),
            profile_metrics=self._observed_profile_metric_summaries(
                observation_graphs,
                lookup_graphs,
                observation_iri,
            ),
            evidence=[
                self._describe_evidence(evidence_iri, evidence_graphs, lookup_graphs)
                for evidence_iri in self._objects(
                    observation_graphs,
                    observation_iri,
                    "rc:evidence",
                )
            ],
        )
    def _profile_observed_column_summary(
        self,
        lookup_graphs: list[str],
        observed_column: str,
        *,
        observed_column_name: str | None,
    ) -> ResourceSummary:
        summary = self._resource_summary(lookup_graphs, observed_column)
        if summary.column_name is not None or observed_column_name is None:
            return summary
        return replace(
            summary,
            label=observed_column_name,
            column_name=observed_column_name,
        )
    def _observed_profile_metric_summaries(
        self,
        graphs: list[str],
        lookup_graphs: list[str],
        observation_iri: str,
    ) -> list[ObservedProfileMetricSummary]:
        summaries: list[ObservedProfileMetricSummary] = []
        for metric_iri in self._objects(
            graphs,
            observation_iri,
            "rc:observedProfileMetric",
        ):
            metric_kind = self._first_object(
                graphs,
                metric_iri,
                "rc:profileMetricKind",
            )
            value_row = self._first_object_row(
                graphs,
                metric_iri,
                "rc:profileMetricValue",
            )
            target_iri = self._first_object(
                graphs,
                metric_iri,
                "rc:profileMetricTarget",
            )
            if metric_kind is None or value_row is None:
                continue
            summaries.append(
                ObservedProfileMetricSummary(
                    iri=metric_iri,
                    metric=self._privacy_redacted_resource_summary(
                        self._resource_summary(lookup_graphs, metric_kind)
                    ),
                    target=self._privacy_redacted_optional_resource_summary(
                        self._optional_resource_summary(lookup_graphs, target_iri)
                    ),
                    value=self._redact_sensitive_context_value(value_row["object"]),
                    value_datatype=value_row["datatype"],
                    value_lang=value_row["lang"],
                )
            )
        return sorted(
            summaries,
            key=lambda item: (
                item.metric.label or item.metric.iri,
                item.value,
                item.iri,
            ),
        )
    def _profile_row_count_snapshot_value(
        self,
        *,
        row_count: int | None,
        sample_size: int | None,
        sample_scope: str | None,
        sample_method: str | None,
        allow_sampled_row_count_snapshot: bool,
    ) -> int | None:
        if row_count is None:
            return None
        basis = self._profile_observation_basis_from_values(
            sample_size=sample_size,
            sample_scope=sample_scope,
            sample_method=sample_method,
            row_count=row_count,
        )
        if basis == "full_scan" or allow_sampled_row_count_snapshot:
            return row_count
        return None
    def _record_optional_domain_network_profile(
        self,
        dataset_iri: str,
        *,
        summary: str,
        observed_at: datetime | str | None,
        observed_by: str | None,
        evidence_summary: str,
        evidence_sources: Iterable[str] | str | None,
        evidence_iri: str,
        sample_size: int,
        sample_scope: str,
        sample_method: str,
        value_frequencies: list[dict[str, Any]],
    ) -> DatasetProfileRecord | None:
        if not value_frequencies:
            return None
        return self.record_dataset_profile(
            dataset_iri,
            summary=summary,
            observed_at=observed_at,
            observed_by=observed_by,
            evidence_summary=evidence_summary,
            evidence_sources=evidence_sources,
            evidence_iri=evidence_iri,
            sample_size=sample_size,
            sample_scope=sample_scope,
            sample_method=sample_method,
            value_frequencies=value_frequencies,
            update_map_snapshot=False,
        )
    def _preflight_profile_pattern(
        self,
        *,
        primary_resource_iri: str,
        pattern_map_implications: Iterable[str] | str | None,
        profile_metric_sets: Iterable[
            tuple[str, Iterable[Mapping[str, Any]] | None]
        ],
        profile_value_type_fields: Iterable[tuple[str, str | None]] = (),
        pattern_confidence: str | None,
        pattern_status: str | None,
        pattern_stability: str | None,
    ) -> list[str]:
        implication_values = self._profile_pattern_map_implications(
            primary_resource_iri,
            pattern_map_implications,
            profile_metric_sets=profile_metric_sets,
            profile_value_type_fields=profile_value_type_fields,
        )
        self._validate_resource_values(
            "pattern_map_implications",
            implication_values,
        )
        if pattern_confidence is not None and pattern_confidence.strip():
            self._controlled_resource_ref(
                "pattern_confidence",
                pattern_confidence,
                CONFIDENCE_LEVELS,
            )
        if pattern_status is not None and pattern_status.strip():
            self._controlled_resource_ref(
                "pattern_status",
                pattern_status,
                PATTERN_OBSERVATION_STATUSES,
            )
        if pattern_stability is not None and pattern_stability.strip():
            self._controlled_resource_ref(
                "pattern_stability",
                pattern_stability,
                PATTERN_STABILITY_LEVELS,
            )
        return implication_values
    def _profile_pattern_requested(
        self,
        pattern_summary: str | None,
        pattern_text: str | None,
        pattern_rationale: str | None,
    ) -> bool:
        pattern_fields = [pattern_summary, pattern_text, pattern_rationale]
        has_pattern_field = any(
            field is not None and field.strip() for field in pattern_fields
        )
        has_complete_pattern = all(
            field is not None and field.strip() for field in pattern_fields
        )
        if has_pattern_field and not has_complete_pattern:
            raise DoxaBaseError(
                "pattern_summary, pattern_text, and pattern_rationale must be "
                "provided together"
            )
        return has_complete_pattern
    @staticmethod
    def _explicit_profile_route_sources(
        sources: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
    ) -> list[dict[str, Any]]:
        if sources is None:
            return []
        if isinstance(sources, MappingABC):
            source_values = [sources]
        else:
            source_values = list(sources)
        route_sources: list[dict[str, Any]] = []
        for source in source_values:
            if not isinstance(source, MappingABC):
                raise DoxaBaseError("profile_route_sources entries must be objects")
            route_source = dict(source)
            review_lane = route_source.get("review_lane")
            if (
                isinstance(review_lane, str)
                and "direct_review_lane" not in route_source
            ):
                route_source["direct_review_lane"] = review_lane
            route_sources.append(route_source)
        return DoxaBase._dedupe_profile_route_sources(route_sources)
    @staticmethod
    def _dedupe_profile_route_sources(
        sources: Iterable[MappingABC[str, Any]],
    ) -> list[dict[str, Any]]:
        deduped: list[dict[str, Any]] = []
        seen: set[str] = set()
        for source in sources:
            route_group_key = source.get("route_group_key")
            route_step_key = source.get("route_step_key")
            if not isinstance(route_group_key, str) or not isinstance(
                route_step_key,
                str,
            ):
                continue
            dedupe_key = route_step_key
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            deduped.append(dict(source))
        return deduped
    @staticmethod
    def _merge_profile_route_sources(
        *source_groups: Iterable[MappingABC[str, Any]],
    ) -> list[dict[str, Any]]:
        merged: list[MappingABC[str, Any]] = []
        for group in source_groups:
            merged.extend(group)
        return DoxaBase._dedupe_profile_route_sources(merged)
    @staticmethod
    def _profile_route_keys_from_sources(
        sources: Iterable[MappingABC[str, Any]],
    ) -> list[str]:
        route_keys: list[str] = []
        for source in sources:
            route_group_key = source.get("route_group_key")
            if isinstance(route_group_key, str):
                DoxaBase._append_unique(route_keys, route_group_key)
        return route_keys
    def _stored_profile_route_groups(
        self,
        profile_route_sources: list[dict[str, Any]],
        *,
        direct_review_lane: str | None,
    ) -> list[dict[str, Any]]:
        enriched_sources = [
            self._profile_insight_candidate_route_source(
                source,
                source_origin="stored_revision",
                direct_allowed=True,
            )
            for source in profile_route_sources
        ]
        observations, patterns, anchors = (
            self._profile_route_source_support_iris(profile_route_sources)
        )
        return self._profile_insight_candidate_route_groups(
            matched_profile_observation_iris=observations,
            matched_supporting_pattern_iris=patterns,
            matched_revision_anchor_iris=anchors,
            profile_route_sources=enriched_sources,
            direct_review_lane=direct_review_lane,
        )
    @staticmethod
    def _profile_route_source_support_iris(
        sources: Iterable[MappingABC[str, Any]],
    ) -> tuple[list[str], list[str], list[str]]:
        observations: list[str] = []
        patterns: list[str] = []
        anchors: list[str] = []

        def append_strings(target: list[str], values: Any) -> None:
            if not isinstance(values, list):
                return
            for value in values:
                if isinstance(value, str):
                    DoxaBase._append_unique(target, value)

        for source in sources:
            append_strings(
                observations,
                source.get("duplicate_profile_observation_iris"),
            )
            append_strings(observations, source.get("profile_observation_iris"))
            append_strings(
                observations,
                source.get("supporting_profile_observation_iris"),
            )
            append_strings(patterns, source.get("route_pattern_iris"))
            mixed_support = source.get("mixed_support")
            if isinstance(mixed_support, MappingABC):
                append_strings(patterns, mixed_support.get("pattern_iris"))
            append_strings(anchors, source.get("route_anchor_iris"))
        return observations, patterns, anchors
    @staticmethod
    def _profile_route_match_strength_rank(match_strength: str) -> int:
        return {
            "direct_action": 0,
            "strong_support": 1,
            "related_support": 2,
        }.get(match_strength, 3)
    @staticmethod
    def _stronger_profile_route_match_strength(
        current: str,
        candidate: str,
    ) -> str:
        if DoxaBase._profile_route_match_strength_rank(
            candidate
        ) < DoxaBase._profile_route_match_strength_rank(current):
            return candidate
        return current
    @staticmethod
    def _profile_route_source_requires_open_lane(
        source: MappingABC[str, Any],
    ) -> bool:
        review_lane = source.get("review_lane")
        if review_lane != "metric_vocabulary_review":
            return True
        advisory_statuses = set(
            DoxaBase._string_values_from_any(source.get("advisory_statuses"))
        )
        if advisory_statuses and advisory_statuses <= {"project_metric_defined"}:
            return False
        return True
    @staticmethod
    def _profile_revision_gate_fields(
        profile_route_groups: Iterable[MappingABC[str, Any]],
        *,
        application_status: str | None,
    ) -> dict[str, Any]:
        groups = [dict(group) for group in profile_route_groups]
        if not groups:
            return {
                "profile_gate_label": None,
                "profile_generic_queue_caution": None,
                "profile_semantic_apply_role": None,
                "profile_apply_cardinality": None,
                "profile_safe_single_apply_candidate": None,
                "profile_bulk_apply_allowed": None,
                "profile_semantic_apply_gate_reason": None,
            }
        gate = DoxaBase._profile_insight_candidate_apply_gate(
            groups,
            application_status=application_status,
        )
        bulk_apply_allowed = bool(gate["bulk_apply_allowed"])
        safe_single_apply_candidate = bool(gate["safe_single_apply_candidate"])
        return {
            "profile_gate_label": DoxaBase._profile_gate_label_from_flags(
                bulk_apply_allowed=bulk_apply_allowed,
                safe_single_apply_candidate=safe_single_apply_candidate,
            ),
            "profile_generic_queue_caution": (
                DoxaBase._profile_generic_queue_caution_from_flags(
                    bulk_apply_allowed=bulk_apply_allowed,
                    safe_single_apply_candidate=safe_single_apply_candidate,
                )
            ),
            "profile_semantic_apply_role": gate["semantic_apply_role"],
            "profile_apply_cardinality": gate["apply_cardinality"],
            "profile_safe_single_apply_candidate": safe_single_apply_candidate,
            "profile_bulk_apply_allowed": bulk_apply_allowed,
            "profile_semantic_apply_gate_reason": (
                gate["semantic_apply_gate_reason"]
            ),
        }
    @staticmethod
    def _profile_gate_label_from_flags(
        *,
        bulk_apply_allowed: bool,
        safe_single_apply_candidate: bool,
    ) -> str:
        if bulk_apply_allowed:
            return "bulk_allowed_after_review"
        if safe_single_apply_candidate:
            return "safe_single_after_review"
        return "blocked_by_profile_gate"
    @staticmethod
    def _profile_generic_queue_caution_from_flags(
        *,
        bulk_apply_allowed: bool,
        safe_single_apply_candidate: bool,
    ) -> str:
        if bulk_apply_allowed:
            return (
                "generic queues may be followed after profile review; "
                "rerun after mutation"
            )
        if safe_single_apply_candidate:
            return (
                "apply at most this row after profile review; "
                "rerun after mutation"
            )
        return (
            "do not follow generic apply_after_review until profile gate is "
            "resolved"
        )
    @staticmethod
    def _profile_quality_basis_markdown(
        profile_quality_summary: Mapping[str, Any],
    ) -> str:
        basis_counts = profile_quality_summary.get("basis_counts")
        if not isinstance(basis_counts, MappingABC) or not basis_counts:
            return "none"
        parts = [
            f"{basis}: {count}"
            for basis, count in sorted(basis_counts.items())
            if isinstance(basis, str) and isinstance(count, int)
        ]
        return ", ".join(parts) or "none"
    def _staged_revisions_profile_route_bridge_markdown(
        self,
        summaries: list[StagedGraphRevisionExportSummary],
    ) -> list[str]:
        if not any(summary.profile_route_groups for summary in summaries):
            return []
        lines = [
            (
                "| Row | Candidate | Revision | Profile route keys | "
                "Review lanes | Semantic moves | Generic queue caution | "
                "Evidence cautions |"
            ),
            "|---:|---|---|---|---|---|---|---|",
        ]
        for index, summary in enumerate(summaries, start=1):
            if not summary.profile_route_groups:
                continue
            profile_gate = self._profile_revision_gate_fields(
                summary.profile_route_groups,
                application_status=summary.apply_status,
            )
            route_keys = ", ".join(
                f"`{key}`" for key in summary.profile_route_keys
            )
            review_lanes = ", ".join(
                self._profile_insight_route_bridge_lane_cells(
                    summary.profile_route_groups
                )
            )
            semantic_moves = self._staged_revisions_profile_route_move_cell(
                summary.profile_route_groups
            )
            generic_queue_caution = (
                profile_gate["profile_generic_queue_caution"] or "none"
            )
            evidence_cautions = (
                self._staged_revisions_profile_route_caution_cell(
                    summary.profile_route_groups
                )
            )
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(index),
                        self._markdown_table_cell(
                            summary.summary or summary.revision_iri
                        ),
                        self._markdown_table_cell(
                            f"`{summary.revision_iri}`"
                        ),
                        self._markdown_table_cell(route_keys),
                        self._markdown_table_cell(review_lanes),
                        self._markdown_table_cell(semantic_moves),
                        self._markdown_table_cell(generic_queue_caution),
                        self._markdown_table_cell(evidence_cautions),
                    ]
                )
                + " |"
            )
        return lines
    @staticmethod
    def _staged_revisions_profile_route_move_cell(
        groups: Iterable[dict[str, Any]],
    ) -> str:
        cells: list[str] = []
        for group in groups:
            review_lane = str(group.get("review_lane") or "profile route")
            closed = [
                str(move)
                for move in group.get("closed_semantic_moves") or []
                if isinstance(move, str)
            ]
            remaining = [
                str(move)
                for move in group.get("remaining_semantic_moves") or []
                if isinstance(move, str)
            ]
            all_moves = [
                str(move)
                for move in group.get("semantic_moves") or []
                if isinstance(move, str)
            ]
            if closed or remaining:
                cells.append(
                    f"{review_lane}: closed {', '.join(closed) or 'none'}; "
                    f"remaining {', '.join(remaining) or 'none'}"
                )
            else:
                cells.append(
                    f"{review_lane}: {', '.join(all_moves) or 'unspecified'}"
                )
        return "; ".join(cells)
    @staticmethod
    def _staged_revisions_profile_route_caution_cell(
        groups: Iterable[dict[str, Any]],
    ) -> str:
        cautions: list[str] = []
        for group in groups:
            for caution in group.get("sampled_evidence_cautions") or []:
                if isinstance(caution, str):
                    DoxaBase._append_unique(cautions, caution)
        return "; ".join(cautions) or "none"
    def _first_object_row(
        self,
        graphs: list[str],
        subject: str,
        predicate: str,
    ) -> sqlite3.Row | None:
        graph_filter, params = self._graph_filter(graphs, alias="q")
        return self._conn.execute(
            f"""
            SELECT q.object, q.object_kind, q.datatype, q.lang
            FROM quads q
            WHERE q.subject = ?
              AND q.predicate = ?
              {graph_filter}
            ORDER BY q.object
            LIMIT 1
            """,
            [subject, self.expand_iri(predicate), *params],
        ).fetchone()
    def _normalise_profile_manifest_domain_network_profiles(
        self,
        profiles: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
    ) -> list[dict[str, Any]]:
        profile_values = self._normalise_manifest_object_list(
            "domain_network_profiles",
            profiles,
        )
        allowed_fields = {
            "dataset_iri",
            "summary",
            "evidence_summary",
            "sample_size",
            "sample_scope",
            "sample_method",
            "extraction_method",
            "coverage_counts",
            "observed_at",
            "observed_by",
            "evidence_sources",
            "evidence_iri",
            "coverage_counts_exhaustive",
            "domain_pair_counts",
            "sender_domain_counts",
            "recipient_domain_counts",
            "domain_pair_min_count",
            "allow_low_frequency_domain_pairs",
            "analysis_view_iri",
            "analysis_view_label",
            "analysis_view_description",
            "analysis_view_row_count_snapshot",
            "analysis_view_query_text",
            "analysis_view_query_language",
            "analysis_view_query_engine",
            "caveat_iri",
            "caveat_label",
            "caveat_description",
            "caveat_severity",
            "pattern_summary",
            "pattern_text",
            "pattern_rationale",
            "pattern_confidence",
            "pattern_status",
            "pattern_stability",
        }
        specs: list[dict[str, Any]] = []
        for index, item in enumerate(profile_values, start=1):
            unknown_fields = sorted(set(item) - allowed_fields)
            if unknown_fields:
                raise DoxaBaseError(
                    f"domain_network_profiles[{index}] has unsupported field(s): "
                    + ", ".join(unknown_fields)
                )
            spec = copy.deepcopy(dict(item))
            dataset_value = spec.get("dataset_iri")
            if not isinstance(dataset_value, str) or not dataset_value.strip():
                raise DoxaBaseError(
                    "domain_network_profiles"
                    f"[{index}].dataset_iri must be a non-empty IRI or CURIE string"
                )
            spec["dataset_iri"] = str(
                self._resource_ref(
                    f"domain_network_profiles[{index}].dataset_iri",
                    dataset_value,
                )
            )
            for field in ("evidence_iri", "analysis_view_iri", "caveat_iri"):
                value = spec.get(field)
                if value is not None:
                    if not isinstance(value, str) or not value.strip():
                        raise DoxaBaseError(
                            f"domain_network_profiles[{index}].{field} must be a "
                            "non-empty IRI or CURIE string"
                        )
                    spec[field] = str(
                        self._resource_ref(
                            f"domain_network_profiles[{index}].{field}",
                            value,
                        )
                    )
            specs.append(spec)
        return specs
    @staticmethod
    def _profile_manifest_domain_network_created_iris(
        spec: Mapping[str, Any],
    ) -> list[tuple[str, str]]:
        created: list[tuple[str, str]] = []
        caveat_requested = (
            spec.get("caveat_description") is not None
            or spec.get("caveat_iri") is not None
        )
        if caveat_requested:
            created.append(
                (
                    "caveat_iri",
                    str(
                        spec.get("caveat_iri")
                        or f"{spec['dataset_iri']}/domain-network-caveat"
                    ),
                )
            )
        analysis_view_requested = any(
            spec.get(field) is not None
            for field in (
                "analysis_view_iri",
                "analysis_view_label",
                "analysis_view_description",
                "analysis_view_row_count_snapshot",
                "analysis_view_query_text",
                "analysis_view_query_language",
                "analysis_view_query_engine",
            )
        )
        if analysis_view_requested:
            created.append(
                (
                    "analysis_view_iri",
                    str(
                        spec.get("analysis_view_iri")
                        or f"{spec['dataset_iri']}/domain-network-analysis-view"
                    ),
                )
            )
        return created
    def _normalise_profile_manifest_caveats(
        self,
        caveats: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
    ) -> list[dict[str, Any]]:
        caveat_values = self._normalise_manifest_object_list(
            "caveats",
            caveats,
        )
        allowed_fields = {
            "iri",
            "label",
            "description",
            "impact",
            "severity",
            "targets",
        }
        specs: list[dict[str, Any]] = []
        seen_iris: set[str] = set()
        for index, item in enumerate(caveat_values, start=1):
            unknown_fields = sorted(set(item) - allowed_fields)
            if unknown_fields:
                raise DoxaBaseError(
                    f"caveats[{index}] has unsupported field(s): "
                    + ", ".join(unknown_fields)
                )
            iri_value = item.get("iri")
            if not isinstance(iri_value, str) or not iri_value.strip():
                raise DoxaBaseError(
                    f"caveats[{index}].iri must be a non-empty IRI or CURIE string"
                )
            caveat_iri = str(self._resource_ref(f"caveats[{index}].iri", iri_value))
            if caveat_iri in seen_iris:
                raise DoxaBaseError(f"caveats[{index}].iri duplicates {caveat_iri}")
            seen_iris.add(caveat_iri)
            spec = {field: copy.deepcopy(item[field]) for field in item}
            spec["iri"] = caveat_iri
            specs.append(spec)
        return specs
    def _normalise_profile_manifest_tables(
        self,
        tables: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
        *,
        table_defaults: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        default_unknown_fields = sorted(
            set(table_defaults) - self._profile_manifest_table_fields()
        )
        if default_unknown_fields:
            raise DoxaBaseError(
                "table_defaults has unsupported field(s): "
                + ", ".join(default_unknown_fields)
            )
        default_identity_fields = (
            {"iri", "table_iri", "dataset_iri"} & set(table_defaults)
        )
        if default_identity_fields:
            raise DoxaBaseError(
                "table_defaults cannot include table identity field(s): "
                + ", ".join(sorted(default_identity_fields))
            )
        table_values = self._normalise_manifest_object_list(
            "tables",
            tables,
            required=True,
        )
        specs: list[dict[str, Any]] = []
        seen_iris: set[str] = set()
        allowed_fields = self._profile_manifest_table_fields()
        for index, item in enumerate(table_values, start=1):
            unknown_fields = sorted(set(item) - allowed_fields)
            if unknown_fields:
                raise DoxaBaseError(
                    f"tables[{index}] has unsupported field(s): "
                    + ", ".join(unknown_fields)
                )
            spec = copy.deepcopy(dict(table_defaults))
            spec.update(copy.deepcopy(dict(item)))
            table_iri = self._profile_manifest_table_iri(spec, index=index)
            if table_iri in seen_iris:
                raise DoxaBaseError(f"tables[{index}].iri duplicates {table_iri}")
            seen_iris.add(table_iri)
            spec.pop("table_iri", None)
            spec.pop("dataset_iri", None)
            spec["iri"] = table_iri
            specs.append(spec)
        return specs
    @staticmethod
    def _profile_manifest_table_fields() -> set[str]:
        return {
            "iri",
            "table_iri",
            "dataset_iri",
            "dataset_summary",
            "evidence_summary",
            "columns",
            "label",
            "description",
            "path_templates",
            "row_count",
            "sample_size",
            "sample_scope",
            "sample_method",
            "observed_at",
            "observed_by",
            "evidence_sources",
            "shared_evidence_iri",
            "null_count",
            "distinct_count",
            "value_frequencies",
            "profile_metrics",
            "row_semantics",
            "entity_key",
            "schema_stability",
            "layout_verification_status",
            "layout_verification_note",
            "caveats",
            "companion_datasets",
            "extra_types",
            "storage_access_iri",
            "storage_label",
            "storage_description",
            "route_roles",
            "storage_protocol",
            "access_mode",
            "location_kind",
            "storage_root",
            "endpoint_profile",
            "bucket_name",
            "key_prefix",
            "region",
            "path_style_access",
            "credential_reference",
            "storage_path_templates",
            "storage_layout_verification_status",
            "storage_layout_verification_note",
            "physical_layout_iri",
            "physical_layout_label",
            "physical_layout_description",
            "compression_codec",
            "physical_layout_verification_status",
            "physical_layout_verification_note",
            "pattern_summary",
            "pattern_text",
            "pattern_rationale",
            "pattern_confidence",
            "pattern_status",
            "pattern_stability",
            "pattern_map_implications",
            "pattern_support_scope",
        }
    def _profile_manifest_table_iri(
        self,
        spec: Mapping[str, Any],
        *,
        index: int,
    ) -> str:
        identity_fields = [
            field for field in ("iri", "table_iri", "dataset_iri") if field in spec
        ]
        if not identity_fields:
            raise DoxaBaseError(
                f"tables[{index}].iri must be a non-empty IRI or CURIE string"
            )
        expanded_values: list[str] = []
        for field in identity_fields:
            value = spec.get(field)
            if not isinstance(value, str) or not value.strip():
                raise DoxaBaseError(
                    f"tables[{index}].{field} must be a non-empty IRI or CURIE string"
                )
            expanded_values.append(
                str(self._resource_ref(f"tables[{index}].{field}", value))
            )
        unique_values = list(dict.fromkeys(expanded_values))
        if len(unique_values) > 1:
            raise DoxaBaseError(
                f"tables[{index}] identity fields disagree: "
                + ", ".join(unique_values)
            )
        return unique_values[0]
    @staticmethod
    def _profiled_table_suggested_next_actions(
        *action_groups: Iterable[SuggestedNextAction],
    ) -> list[SuggestedNextAction]:
        actions: list[SuggestedNextAction] = []
        seen: set[str] = set()
        for group in action_groups:
            for action in group:
                key = json.dumps(
                    [action.tool_name, action.arguments],
                    sort_keys=True,
                    default=str,
                )
                if key in seen:
                    continue
                seen.add(key)
                actions.append(action)
        return actions
    def _profile_value_frequency_values(
        self,
        value_frequencies: Iterable[Mapping[str, Any]] | None,
        *,
        field_name: str = "value_frequencies",
    ) -> list[tuple[Any, int]]:
        values: list[tuple[Any, int]] = []
        for index, item in enumerate(value_frequencies or []):
            item_name = f"{field_name}[{index}]"
            if not isinstance(item, MappingABC):
                raise DoxaBaseError(f"{item_name} must be an object")
            if "value" not in item:
                raise DoxaBaseError(f"{item_name} must include a value")
            frequency_field = "frequency"
            if "frequency" in item:
                frequency = item.get("frequency")
            elif "count" in item:
                frequency = item.get("count")
                frequency_field = "count"
            else:
                frequency = None
            if not isinstance(frequency, int) or isinstance(frequency, bool):
                raise DoxaBaseError(
                    f"{item_name}.{frequency_field} must be an integer"
                )
            self._ensure_non_negative(
                f"{item_name}.{frequency_field}",
                frequency,
            )
            values.append((item["value"], frequency))
        return values
    def _profile_metric_values(
        self,
        profile_metrics: Iterable[Mapping[str, Any]] | None,
        *,
        field_name: str = "profile_metrics",
    ) -> list[tuple[str, Any, str | None, str | None, str | None]]:
        values: list[tuple[str, Any, str | None, str | None, str | None]] = []
        for index, item in enumerate(profile_metrics or []):
            item_name = f"{field_name}[{index}]"
            if not isinstance(item, MappingABC):
                raise DoxaBaseError(f"{item_name} must be an object")
            metric = item.get("metric") or item.get("metric_kind")
            if not isinstance(metric, str) or not metric.strip():
                raise DoxaBaseError(
                    f"{item_name} must include a metric IRI or CURIE"
                )
            if "value" not in item:
                raise DoxaBaseError(f"{item_name} must include a value")
            value = item["value"]
            if value is None or isinstance(value, (list, tuple, dict)):
                raise DoxaBaseError(f"{item_name}.value must be a scalar value")
            datatype = item.get("datatype")
            lang = item.get("lang")
            if datatype is not None and (
                not isinstance(datatype, str) or not datatype.strip()
            ):
                raise DoxaBaseError(f"{item_name}.datatype must be an IRI or CURIE")
            if lang is not None and (not isinstance(lang, str) or not lang.strip()):
                raise DoxaBaseError(f"{item_name}.lang must be a non-empty string")
            if datatype is not None and lang is not None:
                raise DoxaBaseError(f"{item_name} cannot set both datatype and lang")
            target = item.get(
                "target",
                item.get("metric_target", item.get("target_iri")),
            )
            if target is not None and (
                not isinstance(target, str) or not target.strip()
            ):
                raise DoxaBaseError(f"{item_name}.target must be an IRI or CURIE")
            metric_iri = str(self._resource_ref(f"{item_name}.metric", metric))
            self._ensure_known_rc_profile_metric_kind(
                f"{item_name}.metric",
                metric_iri,
            )
            datatype_iri = (
                str(
                    self._resource_ref(
                        f"{item_name}.datatype",
                        datatype,
                    )
                )
                if datatype is not None
                else None
            )
            target_iri = (
                str(
                    self._resource_ref(
                        f"{item_name}.target",
                        target,
                    )
                )
                if target is not None
                else None
            )
            values.append(
                (
                    metric_iri,
                    value,
                    datatype_iri,
                    lang.strip() if lang else None,
                    target_iri,
                )
            )
        return values
    def _ensure_known_rc_profile_metric_kind(
        self,
        field_name: str,
        metric_iri: str,
    ) -> None:
        rc_namespace = PREFIXES["rc"]
        if not metric_iri.startswith(rc_namespace):
            return
        profile_metric_kind = self.expand_iri("rc:ProfileMetricKind")
        if profile_metric_kind in self._types_from_graphs(
            self._expand_graphs(["ontology"]),
            metric_iri,
        ):
            return
        base_metric_kinds = [
            self._compact_iri(metric_kind) or metric_kind
            for metric_kind in self._subjects(
                ["base_ontology"],
                str(RDF.type),
                profile_metric_kind,
            )
        ]
        raise DoxaBaseError(
            f"{field_name} uses unknown rc: profile metric kind "
            f"{metric_iri!r}. Use one of {', '.join(base_metric_kinds)} or a "
            "project-specific full IRI."
        )
    def _profile_pattern_map_implications(
        self,
        primary_resource_iri: str,
        pattern_map_implications: Iterable[str] | str | None,
        *,
        profile_metric_sets: Iterable[
            tuple[str, Iterable[Mapping[str, Any]] | None]
        ],
        profile_value_type_fields: Iterable[tuple[str, str | None]] = (),
    ) -> list[str]:
        explicit_implications = self._string_values(
            "pattern_map_implications",
            pattern_map_implications,
        )
        if explicit_implications:
            return explicit_implications

        implications = [primary_resource_iri]
        seen = {primary_resource_iri}
        for field_name, profile_metrics in profile_metric_sets:
            for metric_iri, *_ in self._profile_metric_values(
                profile_metrics,
                field_name=field_name,
            ):
                if metric_iri.startswith(PREFIXES["rc"]):
                    continue
                if metric_iri in seen:
                    continue
                implications.append(metric_iri)
                seen.add(metric_iri)
        for field_name, value_type in profile_value_type_fields:
            if value_type is None:
                continue
            value_type_iri = str(self._resource_ref(field_name, value_type))
            if value_type_iri.startswith(PREFIXES["rc"]):
                continue
            if value_type_iri in seen:
                continue
            implications.append(value_type_iri)
            seen.add(value_type_iri)
        return implications
