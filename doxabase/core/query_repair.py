"""Storage access and physical layout repair staging.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via QueryRepairMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class QueryRepairMixin:
    def _dataset_query_repair_anchor_iris(
        self,
        dataset_iri: str,
        dataset: DatasetDescription | None = None,
    ) -> set[str]:
        if dataset is None:
            try:
                dataset = self.describe_dataset(dataset_iri)
            except DoxaBaseError:
                return {self.expand_iri(dataset_iri)}
        anchors = {self.expand_iri(dataset.iri)}
        anchors.update(access.iri for access in dataset.storage_accesses)
        anchors.update(layout.iri for layout in dataset.physical_layouts)
        anchors.update(partition.iri for partition in dataset.partition_schemes)
        anchors.update(column.iri for column in dataset.columns)
        for partition in dataset.partition_schemes:
            anchors.update(column.iri for column in partition.partition_columns)
        return anchors
    @staticmethod
    def _query_repair_groups_have_pending_options(
        groups: Iterable[QueryRepairActionGroup],
    ) -> bool:
        return any(group.pending_action_options for group in groups)
    def _query_repair_action_groups(
        self,
        issues: list[QueryPlanningIssue],
    ) -> list[QueryRepairActionGroup]:
        groups: list[QueryRepairActionGroup] = []
        for issue_index, issue in enumerate(issues):
            if issue.details is None:
                continue
            repair_hint = issue.details.get("repair_hint")
            if not isinstance(repair_hint, MappingABC):
                continue
            actions = repair_hint.get("actions")
            if not isinstance(actions, list) or not actions:
                continue
            repair_context = {
                str(key): copy.deepcopy(value)
                for key, value in repair_hint.items()
                if key != "actions"
            }
            action_type = repair_hint.get("action_type")
            (
                action_status_counts,
                pending_action_count,
                skippable_action_count,
                already_satisfied_action_count,
                pending_required_extra_arguments,
                pending_action_options,
            ) = self._query_repair_action_group_summary(actions)
            choice_mode = repair_hint.get("choice_mode")
            groups.append(
                QueryRepairActionGroup(
                    group_name="query_repair_review",
                    issue_index=issue_index,
                    issue_code=issue.code,
                    issue_severity=issue.severity,
                    issue_message=issue.message,
                    issue_resource=issue.resource,
                    repair_hint_path=f"issues[{issue_index}].details.repair_hint",
                    repair_action_type=(
                        str(action_type) if action_type is not None else None
                    ),
                    requires_review=repair_hint.get("requires_review") is not False,
                    repair_context=repair_context,
                    choice_mode=(
                        str(choice_mode)
                        if choice_mode is not None
                        else "review_all_applicable"
                    ),
                    actions=copy.deepcopy(actions),
                    action_count=len(actions),
                    action_status_counts=action_status_counts,
                    pending_action_count=pending_action_count,
                    skippable_action_count=skippable_action_count,
                    already_satisfied_action_count=(
                        already_satisfied_action_count
                    ),
                    pending_required_extra_arguments=(
                        pending_required_extra_arguments
                    ),
                    pending_action_options=pending_action_options,
                    group_advisories=(
                        self._query_repair_action_group_advisories(issue)
                    ),
                )
            )
        return groups
    def _query_context_issues_with_pending_repair_actions(
        self,
        issues: list[QueryPlanningIssue],
        dataset: DatasetDescription,
    ) -> list[QueryPlanningIssue]:
        pending_rows = self._current_staged_query_repair_patch_rows(dataset)
        if not pending_rows:
            return issues
        updated_issues: list[QueryPlanningIssue] = []
        for issue in issues:
            if issue.details is None:
                updated_issues.append(issue)
                continue
            repair_hint = issue.details.get("repair_hint")
            if not isinstance(repair_hint, MappingABC):
                updated_issues.append(issue)
                continue
            actions = repair_hint.get("actions")
            if not isinstance(actions, list) or not actions:
                updated_issues.append(issue)
                continue
            changed = False
            updated_actions: list[Any] = []
            for action in actions:
                if not isinstance(action, MappingABC):
                    updated_actions.append(action)
                    continue
                if action.get("action_status") not in {None, "pending_review"}:
                    updated_actions.append(action)
                    continue
                if action.get("already_pending_candidate_count") is not None:
                    updated_actions.append(action)
                    continue
                pending_iris = self._pending_query_repair_iris_for_action(
                    action,
                    pending_rows,
                )
                if not pending_iris:
                    updated_actions.append(action)
                    continue
                changed = True
                updated_action = dict(action)
                updated_action["action_status"] = "already_pending"
                updated_action["skip_when_already_pending"] = True
                updated_action["pending_staged_repair_iris"] = pending_iris
                pending_note = (
                    "Current staged repair(s) already propose this query "
                    "metadata change: "
                    f"{', '.join(pending_iris)}. Review the staged work before "
                    "staging a duplicate."
                )
                condition = updated_action.get("condition")
                updated_action["condition"] = (
                    f"{condition} {pending_note}"
                    if isinstance(condition, str) and condition.strip()
                    else pending_note
                )
                updated_actions.append(updated_action)
            if not changed:
                updated_issues.append(issue)
                continue
            updated_repair_hint = dict(repair_hint)
            updated_repair_hint["actions"] = updated_actions
            updated_details = dict(issue.details)
            updated_details["repair_hint"] = updated_repair_hint
            updated_issues.append(
                QueryPlanningIssue(
                    code=issue.code,
                    severity=issue.severity,
                    message=issue.message,
                    domain=issue.domain,
                    resource=issue.resource,
                    details=updated_details,
                )
            )
        return updated_issues
    def _pending_query_repair_iris_for_action(
        self,
        action: MappingABC[str, Any],
        pending_rows: list[dict[str, str]],
    ) -> list[str]:
        action_arguments = action.get("args")
        if not isinstance(action_arguments, MappingABC):
            action_arguments = action.get("arguments_template")
        if not isinstance(action_arguments, MappingABC):
            return []
        spec = action_arguments.get("spec")
        if isinstance(spec, MappingABC):
            action_arguments = spec
        graph = action_arguments.get("graph", "map")
        subject = action_arguments.get("subject")
        predicate = action_arguments.get("predicate")
        change_kind = action_arguments.get("change_kind")
        if (
            graph != "map"
            or not isinstance(subject, str)
            or not isinstance(predicate, str)
            or not isinstance(change_kind, str)
        ):
            return []
        operations = {
            "add": {"add"},
            "remove": {"remove"},
            "replace": {"add", "remove"},
        }.get(change_kind)
        if not operations:
            return []
        normalized_subject = self.expand_iri(subject)
        normalized_predicate = self.expand_iri(predicate)
        object_filter = self._query_repair_action_object_filter(
            action,
            action_arguments,
        )
        pending_iris: list[str] = []
        for row in pending_rows:
            if row["operation"] not in operations:
                continue
            if row["subject"] != normalized_subject:
                continue
            if row["predicate"] != normalized_predicate:
                continue
            if object_filter is not None:
                expected_object, expected_kind = object_filter
                if row["object"] != expected_object:
                    continue
                if row["object_kind"] != expected_kind:
                    continue
            revision_iri = row["revision_iri"]
            if revision_iri not in pending_iris:
                pending_iris.append(revision_iri)
        return pending_iris
    def _query_repair_action_object_filter(
        self,
        action: MappingABC[str, Any],
        action_arguments: MappingABC[str, Any],
    ) -> tuple[str, str] | None:
        object_value = action_arguments.get("object")
        if not isinstance(object_value, str):
            return None
        placeholder_fields = action.get("placeholder_fields")
        if isinstance(placeholder_fields, list) and "object" in placeholder_fields:
            return None
        if object_value.startswith("<") and object_value.endswith(">"):
            return None
        object_kind = action_arguments.get("object_kind", "literal")
        if object_kind in {"iri", "uri"}:
            return self.expand_iri(object_value), "uri"
        return object_value, "literal"
    def _query_context_repair_hinted_issues(
        self,
        issues: list[QueryPlanningIssue],
        *,
        dataset: DatasetDescription,
        decision: QueryTargetDecision,
        candidates: list[QueryTargetCandidate],
    ) -> list[QueryPlanningIssue]:
        selected_candidate: QueryTargetCandidate | None = None
        if (
            decision.candidate_index is not None
            and 0 <= decision.candidate_index < len(candidates)
        ):
            selected_candidate = candidates[decision.candidate_index]

        dataset_layout_repair_ready = (
            selected_candidate is not None
            and self._query_dataset_layout_status_repair_ready(
                dataset,
                selected_candidate,
                issues=issues,
            )
        )
        repair_partitions: list[PartitionDescription] = []
        repair_layouts: list[PhysicalLayoutDescription] = []
        if (
            selected_candidate is None
            or decision.status != "context_blocked"
            or decision.selected_candidate_direct_clean is not True
        ):
            if not dataset_layout_repair_ready:
                return issues
        else:
            blocker_iris = self._query_context_blocker_resource_iris(
                selected_candidate
            )
            partitions_by_iri = {
                partition.iri: partition for partition in dataset.partition_schemes
            }
            layouts_by_iri = {
                layout.iri: layout for layout in dataset.physical_layouts
            }
            repair_partitions = [
                partitions_by_iri[iri]
                for iri in blocker_iris
                if iri in partitions_by_iri
            ]
            candidate_repair_layouts = [
                layouts_by_iri[iri] for iri in blocker_iris if iri in layouts_by_iri
            ]
            repair_layouts = [
                layout
                for layout in candidate_repair_layouts
                if self._physical_layout_has_verified_matching_sibling(
                    layout,
                    dataset.physical_layouts,
                )
            ]
            if (
                not repair_partitions
                and not repair_layouts
                and not dataset_layout_repair_ready
            ):
                return issues

        partitions_by_iri = {
            partition.iri: partition for partition in dataset.partition_schemes
        }
        layouts_by_iri = {layout.iri: layout for layout in dataset.physical_layouts}
        if selected_candidate is None:
            return issues

        repair_partition_iris = {partition.iri for partition in repair_partitions}
        repair_layout_iris = {layout.iri for layout in repair_layouts}
        updated: list[QueryPlanningIssue] = []
        for issue in issues:
            resource_iri = issue.resource.iri if issue.resource is not None else None
            if (
                issue.code == "layout_needs_verification"
                and dataset_layout_repair_ready
                and resource_iri == dataset.iri
            ):
                details = copy.deepcopy(issue.details) if issue.details else {}
                details["repair_hint"] = (
                    self._query_dataset_layout_status_repair_hint(
                        dataset,
                        decision=decision,
                        selected_candidate=selected_candidate,
                    )
                )
                updated.append(
                    QueryPlanningIssue(
                        code=issue.code,
                        severity=issue.severity,
                        message=issue.message,
                        domain=issue.domain,
                        resource=issue.resource,
                        details=details,
                    )
                )
                continue
            if (
                issue.code == "layout_needs_verification"
                and resource_iri in repair_partition_iris
            ):
                partition = partitions_by_iri[resource_iri]
                details = copy.deepcopy(issue.details) if issue.details else {}
                details["repair_hint"] = self._query_partition_context_blocker_repair_hint(
                    dataset,
                    partition,
                    decision=decision,
                    selected_candidate=selected_candidate,
                )
                updated.append(
                    QueryPlanningIssue(
                        code=issue.code,
                        severity=issue.severity,
                        message=issue.message,
                        domain=issue.domain,
                        resource=issue.resource,
                        details=details,
                    )
                )
                continue
            if (
                issue.code == "layout_needs_verification"
                and resource_iri in repair_layout_iris
            ):
                layout = layouts_by_iri[resource_iri]
                details = copy.deepcopy(issue.details) if issue.details else {}
                details["repair_hint"] = self._query_physical_layout_context_blocker_repair_hint(
                    dataset,
                    layout,
                    decision=decision,
                    selected_candidate=selected_candidate,
                )
                updated.append(
                    QueryPlanningIssue(
                        code=issue.code,
                        severity=issue.severity,
                        message=issue.message,
                        domain=issue.domain,
                        resource=issue.resource,
                        details=details,
                    )
                )
                continue
            updated.append(issue)
        return updated
    def _query_dataset_layout_status_repair_ready(
        self,
        dataset: DatasetDescription,
        selected_candidate: QueryTargetCandidate,
        *,
        issues: list[QueryPlanningIssue],
    ) -> bool:
        if selected_candidate.source_resource.iri != dataset.iri:
            return False
        if self._layout_status_is_verified(dataset.layout_verification_status):
            return False
        if selected_candidate.storage_access is None:
            return False
        if not dataset.path_templates:
            return False
        storage_access = next(
            (
                access
                for access in dataset.storage_accesses
                if access.iri == selected_candidate.storage_access.iri
            ),
            None,
        )
        if storage_access is None or not self._layout_status_is_verified(
            storage_access.layout_verification_status
        ):
            return False
        if not any(
            self._layout_status_is_verified(layout.layout_verification_status)
            for layout in dataset.physical_layouts
        ):
            return False
        prerequisite_issue_codes = {
            "missing_storage_access",
            "missing_storage_protocol",
            "missing_storage_location",
            "missing_physical_layout",
            "missing_file_format",
            "ambiguous_physical_layout",
            "database_relation_template_source_mismatch",
        }
        for issue in issues:
            if issue.code in prerequisite_issue_codes:
                return False
            if issue.code != "layout_needs_verification":
                continue
            resource_iri = issue.resource.iri if issue.resource is not None else None
            if resource_iri not in {None, dataset.iri}:
                return False
        return True
    def _physical_layout_has_verified_matching_sibling(
        self,
        layout: PhysicalLayoutDescription,
        physical_layouts: list[PhysicalLayoutDescription],
    ) -> bool:
        layout_signature = self._physical_layout_signature(layout)
        return any(
            sibling.iri != layout.iri
            and self._layout_status_is_verified(sibling.layout_verification_status)
            and self._physical_layout_signature(sibling) == layout_signature
            for sibling in physical_layouts
        )
    @staticmethod
    def _physical_layout_signature(
        layout: PhysicalLayoutDescription,
    ) -> tuple[str | None, str | None]:
        return (
            layout.file_format.iri if layout.file_format is not None else None,
            (
                layout.compression_codec.iri
                if layout.compression_codec is not None
                else None
            ),
        )
    def _query_partition_context_blocker_repair_hint(
        self,
        dataset: DatasetDescription,
        partition: PartitionDescription,
        *,
        decision: QueryTargetDecision,
        selected_candidate: QueryTargetCandidate,
    ) -> dict[str, Any]:
        storage_access_iri = (
            selected_candidate.storage_access.iri
            if selected_candidate.storage_access is not None
            else None
        )
        return {
            "action_type": "remove_stale_partition_scheme_link",
            "requires_review": True,
            "target_dataset_iri": dataset.iri,
            "partition_scheme": {
                "iri": partition.iri,
                "label": partition.label,
                "path_template": partition.path_template,
            },
            "selected_candidate": {
                "candidate_index": decision.candidate_index,
                "candidate_path": selected_candidate.candidate_path,
                "candidate_path_status": selected_candidate.candidate_path_status,
                "template_source": selected_candidate.template_source,
                "source_resource_iri": selected_candidate.source_resource.iri,
                "storage_access_iri": storage_access_iri,
            },
            "actions": [
                {
                    "action_type": "remove_stale_partition_scheme_link",
                    "tool": "doxabase.stage_revision",
                    "reason": (
                        "Use after review confirms the selected direct-clean "
                        "query target supersedes this partition scheme for the "
                        "dataset."
                    ),
                    "required_extra_arguments": ["rationale"],
                    "rationale_template": (
                        "Reviewed stale partition-scheme link for "
                        f"{dataset.iri}; selected query target "
                        f"{selected_candidate.candidate_path!r} should be the "
                        "planning route."
                    ),
                    "args": {
                        "kind": "map_assertion",
                        "spec": {
                            "subject": dataset.iri,
                            "predicate": "rc:partitionedBy",
                            "object": partition.iri,
                            "object_kind": "iri",
                            "change_kind": "remove",
                            "graph": "map",
                            "validation_scope": "all",
                        },
                    },
                    "condition": (
                        "Only after review confirms this partition scheme is a "
                        "stale blocker for the selected direct-clean candidate, "
                        "not merely an unverified alternate route that should "
                        "remain linked."
                    ),
                }
            ],
        }
    def _query_dataset_layout_status_repair_hint(
        self,
        dataset: DatasetDescription,
        *,
        decision: QueryTargetDecision,
        selected_candidate: QueryTargetCandidate,
    ) -> dict[str, Any]:
        current_status_iri = (
            dataset.layout_verification_status.iri
            if dataset.layout_verification_status is not None
            else None
        )
        storage_access_iri = (
            selected_candidate.storage_access.iri
            if selected_candidate.storage_access is not None
            else None
        )
        verified_storage_access_iris = [
            access.iri
            for access in dataset.storage_accesses
            if self._layout_status_is_verified(access.layout_verification_status)
        ]
        verified_physical_layout_iris = [
            layout.iri
            for layout in dataset.physical_layouts
            if self._layout_status_is_verified(layout.layout_verification_status)
        ]
        actions: list[dict[str, Any]] = []
        for status_curie, action_label, evidence_label in (
            (
                "rc:VerifiedByListingLayout",
                "Stage dataset layout verified by listing",
                "a storage listing or equivalent metadata review",
            ),
            (
                "rc:VerifiedByQueryLayout",
                "Stage dataset layout verified by query",
                "a successful read/query against the selected route",
            ),
        ):
            status_iri = self.expand_iri(status_curie)
            actions.append(
                {
                    "action_type": "replace_dataset_layout_verification_status",
                    "tool": "doxabase.stage_revision",
                    "reason": (
                        "Use after review confirms the dataset-owned path "
                        f"template has been verified by {evidence_label}."
                    ),
                    "required_extra_arguments": ["rationale"],
                    "rationale_template": (
                        "Reviewed dataset layout verification for "
                        f"{dataset.iri}; selected query target "
                        f"{selected_candidate.candidate_path!r} is supported "
                        f"by {evidence_label}."
                    ),
                    "args": {
                        "kind": "map_assertion",
                        "spec": {
                            "subject": dataset.iri,
                            "predicate": "rc:layoutVerificationStatus",
                            "object": status_curie,
                            "object_kind": "iri",
                            "change_kind": "replace",
                            "graph": "map",
                            "review_note": (
                                "Generated from a dataset-level "
                                "layout_needs_verification query-planning repair "
                                "group after storage access and physical layout "
                                "were already verified."
                            ),
                            "review_recommendation": (
                                "Apply only after confirming the selected "
                                "dataset-owned path template matches the reviewed "
                                f"{status_iri} evidence."
                            ),
                            "validation_scope": "all",
                        },
                    },
                    "condition": (
                        "Choose this status only after reviewing the evidence "
                        "type. If the path was merely copied from a manifest or "
                        "inferred before storage/layout review, keep the "
                        "candidate status until listing or query evidence exists."
                    ),
                }
            )
        return {
            "action_type": "replace_dataset_layout_verification_status",
            "choice_mode": "choose_one",
            "requires_review": True,
            "target_dataset_iri": dataset.iri,
            "current_layout_verification_status_iri": current_status_iri,
            "selected_candidate": {
                "candidate_index": decision.candidate_index,
                "candidate_path": selected_candidate.candidate_path,
                "candidate_path_status": selected_candidate.candidate_path_status,
                "template_source": selected_candidate.template_source,
                "source_resource_iri": selected_candidate.source_resource.iri,
                "storage_access_iri": storage_access_iri,
            },
            "verified_storage_access_iris": verified_storage_access_iris,
            "verified_physical_layout_iris": verified_physical_layout_iris,
            "actions": actions,
        }
    def _query_physical_layout_context_blocker_repair_hint(
        self,
        dataset: DatasetDescription,
        layout: PhysicalLayoutDescription,
        *,
        decision: QueryTargetDecision,
        selected_candidate: QueryTargetCandidate,
    ) -> dict[str, Any]:
        storage_access_iri = (
            selected_candidate.storage_access.iri
            if selected_candidate.storage_access is not None
            else None
        )
        return {
            "action_type": "remove_stale_physical_layout_link",
            "requires_review": True,
            "target_dataset_iri": dataset.iri,
            "physical_layout": {
                "iri": layout.iri,
                "label": layout.label,
                "file_format_iri": (
                    layout.file_format.iri if layout.file_format is not None else None
                ),
                "compression_codec_iri": (
                    layout.compression_codec.iri
                    if layout.compression_codec is not None
                    else None
                ),
                "layout_verification_status_iri": (
                    layout.layout_verification_status.iri
                    if layout.layout_verification_status is not None
                    else None
                ),
            },
            "selected_candidate": {
                "candidate_index": decision.candidate_index,
                "candidate_path": selected_candidate.candidate_path,
                "candidate_path_status": selected_candidate.candidate_path_status,
                "template_source": selected_candidate.template_source,
                "source_resource_iri": selected_candidate.source_resource.iri,
                "storage_access_iri": storage_access_iri,
            },
            "actions": [
                {
                    "action_type": "remove_stale_physical_layout_link",
                    "tool": "doxabase.stage_revision",
                    "reason": (
                        "Use after review confirms the selected direct-clean "
                        "query target and verified sibling layout supersede "
                        "this unverified physical layout for the dataset."
                    ),
                    "required_extra_arguments": ["rationale"],
                    "rationale_template": (
                        "Reviewed stale physical-layout link for "
                        f"{dataset.iri}; selected query target "
                        f"{selected_candidate.candidate_path!r} and a verified "
                        "sibling layout should be the planning route."
                    ),
                    "args": {
                        "kind": "map_assertion",
                        "spec": {
                            "subject": dataset.iri,
                            "predicate": "rc:hasPhysicalLayout",
                            "object": layout.iri,
                            "object_kind": "iri",
                            "change_kind": "remove",
                            "graph": "map",
                            "validation_scope": "all",
                        },
                    },
                    "condition": (
                        "Only after review confirms this physical layout is a "
                        "stale blocker for the selected direct-clean candidate, "
                        "not an alternate valid layout that should remain linked "
                        "or be verified instead."
                    ),
                }
            ],
        }
    @staticmethod
    def _query_repair_action_group_summary(
        actions: list[Any],
    ) -> tuple[dict[str, int], int, int, int, list[str], list[dict[str, Any]]]:
        action_status_counts: dict[str, int] = {}
        pending_action_count = 0
        skippable_action_count = 0
        already_satisfied_action_count = 0
        pending_required_extra_arguments: list[str] = []
        pending_action_options: list[dict[str, Any]] = []

        for action_index, action in enumerate(actions):
            if not isinstance(action, MappingABC):
                status = "pending_review"
                skippable = False
                required_extra_arguments: list[Any] = []
                action_option = {
                    "action_index": action_index,
                    "action_type": None,
                    "tool": None,
                    "action_status": status,
                    "required_extra_arguments": [],
                    "placeholder_fields": [],
                    "reviewed_value_fields": [],
                }
            else:
                raw_status = action.get("action_status")
                status = str(raw_status) if raw_status else "pending_review"
                skippable = (
                    status == "already_satisfied"
                    and action.get("skip_when_already_satisfied") is True
                ) or (
                    status == "already_pending"
                    and action.get("skip_when_already_pending") is True
                )
                required_extra_arguments = action.get("required_extra_arguments")
                if not isinstance(required_extra_arguments, list):
                    required_extra_arguments = []
                placeholder_fields = action.get("placeholder_fields")
                if not isinstance(placeholder_fields, list):
                    placeholder_fields = []
                reviewed_value_fields = action.get("reviewed_value_fields")
                if not isinstance(reviewed_value_fields, list):
                    reviewed_value_fields = []
                action_option = {
                    "action_index": action_index,
                    "action_type": (
                        str(action["action_type"])
                        if action.get("action_type") is not None
                        else None
                    ),
                    "tool": (
                        str(action["tool"])
                        if action.get("tool") is not None
                        else None
                    ),
                    "action_status": status,
                    "required_extra_arguments": [
                        str(argument) for argument in required_extra_arguments
                    ],
                    "placeholder_fields": [
                        str(field) for field in placeholder_fields
                    ],
                    "reviewed_value_fields": [
                        str(field) for field in reviewed_value_fields
                    ],
                }
                for key in (
                    "pending_staged_repair_iris",
                    "already_pending_storage_access_iris",
                ):
                    values = action.get(key)
                    if isinstance(values, list):
                        action_option[key] = [str(value) for value in values]
                for key in (
                    "source_subject_iri",
                    "misplaced_template_subject_iri",
                    "misplaced_template_source",
                    "misplaced_template",
                ):
                    value = action.get(key)
                    if isinstance(value, str):
                        action_option[key] = value
                pending_candidate_count = action.get(
                    "already_pending_candidate_count"
                )
                if isinstance(pending_candidate_count, int):
                    action_option["already_pending_candidate_count"] = (
                        pending_candidate_count
                    )
                for key in ("reason", "condition", "review_rationale_guidance"):
                    value = action.get(key)
                    if isinstance(value, str):
                        action_option[key] = value

            action_status_counts[status] = action_status_counts.get(status, 0) + 1
            if status == "already_satisfied":
                already_satisfied_action_count += 1
            if skippable:
                skippable_action_count += 1
                continue

            pending_action_count += 1
            pending_action_options.append(action_option)
            for argument in required_extra_arguments:
                argument_name = str(argument)
                if argument_name not in pending_required_extra_arguments:
                    pending_required_extra_arguments.append(argument_name)

        return (
            action_status_counts,
            pending_action_count,
            skippable_action_count,
            already_satisfied_action_count,
            pending_required_extra_arguments,
            pending_action_options,
        )
    def _query_context_physical_layout_selection_actions(
        self,
        *,
        dataset_iri: str,
        graph: str | None,
        candidate_index: int,
        candidate: QueryTargetCandidate,
        columns: list[ColumnDescription],
        partition_schemes: list[PartitionDescription],
        allow_context_blocked_candidate: bool,
        pending_repair_groups_present: bool,
        route_intent_review_candidate_indexes: Iterable[int] = (),
        route_intent_caution: str | None = None,
    ) -> list[SuggestedNextAction]:
        issue = next(
            (
                reason
                for reason in candidate.direct_review_reasons
                if reason.code == "ambiguous_physical_layout"
                and reason.details is not None
            ),
            None,
        )
        if issue is None or issue.details is None:
            return []
        signatures = issue.details.get("layout_signatures")
        if not isinstance(signatures, list):
            return []
        actions: list[SuggestedNextAction] = []
        seen_layout_iris: set[str] = set()
        route_intent_peer_indexes = set(route_intent_review_candidate_indexes)
        unattended_caution = self._query_plan_action_caution(
            caution=(
                route_intent_caution if route_intent_peer_indexes else None
            ),
            pending_repair_groups_present=pending_repair_groups_present,
        )
        for signature in signatures:
            if not isinstance(signature, Mapping):
                continue
            layout_iris = signature.get("layout_iris")
            if not isinstance(layout_iris, list):
                continue
            file_format_iri = signature.get("file_format_iri")
            compression_codec_iri = signature.get("compression_codec_iri")
            signature_note_parts: list[str] = []
            if isinstance(file_format_iri, str) and file_format_iri:
                file_format_label = (
                    self._compact_iri(file_format_iri)
                    or self._local_name(file_format_iri)
                    or file_format_iri
                )
                signature_note_parts.append(f"file format {file_format_label}")
            if isinstance(compression_codec_iri, str) and compression_codec_iri:
                compression_label = (
                    self._compact_iri(compression_codec_iri)
                    or self._local_name(compression_codec_iri)
                    or compression_codec_iri
                )
                signature_note_parts.append(f"compression {compression_label}")
            if not self._query_layout_signature_compatible_with_candidate(
                candidate,
                file_format_iri if isinstance(file_format_iri, str) else None,
            ):
                continue
            if self._query_layout_signature_path_extension_mismatch(
                candidate,
                file_format_iri if isinstance(file_format_iri, str) else None,
            ):
                continue
            signature_note = (
                " with " + " and ".join(signature_note_parts)
                if signature_note_parts
                else ""
            )
            for layout_iri in layout_iris:
                if not isinstance(layout_iri, str) or not layout_iri:
                    continue
                if layout_iri in seen_layout_iris:
                    continue
                seen_layout_iris.add(layout_iri)
                arguments: dict[str, Any] = {
                    "iri": dataset_iri,
                    "plan_candidate": candidate.candidate_selector,
                    "physical_layout_iri": layout_iri,
                }
                if graph is not None and graph != "map":
                    arguments["graph"] = graph
                allowance_reason = ""
                if allow_context_blocked_candidate:
                    arguments["allow_context_blocked_candidate"] = True
                    allowance_reason = (
                        " Because this candidate's only direct blocker is "
                        "layout ambiguity and the remaining blockers are "
                        "candidate metadata on sibling routes, the action "
                        "includes allow_context_blocked_candidate=True to "
                        "draft the reviewed direct-clean route while keeping "
                        "context audit fields visible."
                    )
                reason = (
                    f"Candidate {candidate_index} is blocked by ambiguous "
                    "physical layout metadata. After reviewing that "
                    f"{layout_iri} is the intended layout"
                    f"{signature_note}, draft the query plan with "
                    "physical_layout_iri so scan.function is inferred "
                    "from an explicit layout choice."
                    f"{allowance_reason}"
                )
                if unattended_caution:
                    reason = f"{reason} {unattended_caution}"
                actions.append(
                    SuggestedNextAction(
                        tool="doxabase.describe_query_context",
                        args=arguments,
                        reason=reason,
                    )
                )
        return actions
    def _query_storage_access_repair_graph(
        self,
        *,
        dataset_iri: str,
        storage_access_iri: str,
        label: str | None,
        description: str | None,
        route_roles: list[str],
        storage_protocol: URIRef,
        access_mode: URIRef | None,
        location_kind: str | None,
        storage_root: str,
        endpoint_profile: str | None,
        bucket_name: str | None,
        key_prefix: str | None,
        region: str | None,
        path_style_access: bool | None,
        credential_reference: str | None,
        path_templates: list[str],
        layout_verification_status: URIRef | None,
        layout_verification_note: str | None,
    ) -> Graph:
        graph = Graph()
        self._bind_prefixes(graph)
        dataset = URIRef(dataset_iri)
        access = URIRef(storage_access_iri)
        graph.add((dataset, URIRef(self.expand_iri("rc:hasStorageAccess")), access))
        graph.add((access, RDF.type, URIRef(self.expand_iri("rc:StorageAccess"))))
        self._add_optional_literal(graph, access, str(RDFS.label), label)
        self._add_optional_literal(graph, access, str(RDFS.comment), description)
        for route_role in route_roles:
            graph.add(
                (
                    access,
                    URIRef(self.expand_iri("rc:routeRole")),
                    self._resource_ref("route_roles", route_role),
                )
            )
        graph.add(
            (
                access,
                URIRef(self.expand_iri("rc:storageProtocol")),
                storage_protocol,
            )
        )
        if access_mode is not None:
            graph.add((access, URIRef(self.expand_iri("rc:accessMode")), access_mode))
        for predicate, value in (
            ("rc:locationKind", location_kind),
            ("rc:storageRoot", storage_root),
            ("rc:endpointProfile", endpoint_profile),
            ("rc:bucketName", bucket_name),
            ("rc:keyPrefix", key_prefix),
            ("rc:region", region),
            ("rc:credentialReference", credential_reference),
        ):
            self._add_optional_literal(graph, access, predicate, value)
        if path_style_access is not None:
            graph.add(
                (
                    access,
                    URIRef(self.expand_iri("rc:pathStyleAccess")),
                    Literal(path_style_access, datatype=XSD.boolean),
                )
            )
        for path_template in path_templates:
            graph.add(
                (
                    access,
                    URIRef(self.expand_iri("rc:pathTemplate")),
                    Literal(path_template),
                )
            )
        if layout_verification_status is not None:
            graph.add(
                (
                    access,
                    URIRef(self.expand_iri("rc:layoutVerificationStatus")),
                    layout_verification_status,
                )
            )
        self._add_optional_literal(
            graph,
            access,
            "rc:layoutVerificationNote",
            layout_verification_note,
        )
        return graph
    def _query_physical_layout_repair_graph(
        self,
        *,
        dataset_iri: str,
        layout_iri: str,
        label: str | None,
        description: str | None,
        file_format: URIRef,
        compression_codec: URIRef | None,
        layout_verification_status: URIRef | None,
        layout_verification_note: str | None,
    ) -> Graph:
        graph = Graph()
        self._bind_prefixes(graph)
        dataset = URIRef(dataset_iri)
        layout = URIRef(layout_iri)
        graph.add((dataset, URIRef(self.expand_iri("rc:hasPhysicalLayout")), layout))
        graph.add((layout, RDF.type, URIRef(self.expand_iri("rc:PhysicalLayout"))))
        self._add_optional_literal(graph, layout, str(RDFS.label), label)
        self._add_optional_literal(graph, layout, str(RDFS.comment), description)
        graph.add((layout, URIRef(self.expand_iri("rc:fileFormat")), file_format))
        if compression_codec is not None:
            graph.add(
                (
                    layout,
                    URIRef(self.expand_iri("rc:compressionCodec")),
                    compression_codec,
                )
            )
        if layout_verification_status is not None:
            graph.add(
                (
                    layout,
                    URIRef(self.expand_iri("rc:layoutVerificationStatus")),
                    layout_verification_status,
                )
            )
        self._add_optional_literal(
            graph,
            layout,
            "rc:layoutVerificationNote",
            layout_verification_note,
        )
        return graph
    def _draft_query_plan_primary_repair_cue(
        self,
        issues: list[QueryPlanningIssue],
    ) -> dict[str, Any]:
        empty_cue: dict[str, Any] = {
            "primary_repair_issue_index": None,
            "primary_repair_issue_code": None,
            "primary_repair_group_action_type": None,
            "primary_repair_action_index": None,
            "primary_repair_action_type": None,
            "primary_repair_action_label": None,
            "primary_repair_tool": None,
            "primary_repair_required_extra_arguments": [],
        }
        for issue_index, issue in enumerate(issues):
            if issue.details is None:
                continue
            repair_hint = issue.details.get("repair_hint")
            if not isinstance(repair_hint, MappingABC):
                continue
            actions = repair_hint.get("actions")
            if not isinstance(actions, list) or not actions:
                continue
            (
                _action_status_counts,
                _pending_action_count,
                _skippable_action_count,
                _already_satisfied_action_count,
                _pending_required_extra_arguments,
                pending_action_options,
            ) = self._query_repair_action_group_summary(actions)
            if not pending_action_options:
                continue
            first_option = pending_action_options[0]
            group_action_type = repair_hint.get("action_type")
            action_index = first_option.get("action_index")
            action_type = first_option.get("action_type")
            action_label = (
                self._repair_action_type_label(str(action_type))
                if action_type is not None
                else None
            )
            return {
                "primary_repair_issue_index": issue_index,
                "primary_repair_issue_code": issue.code,
                "primary_repair_group_action_type": (
                    str(group_action_type)
                    if group_action_type is not None
                    else None
                ),
                "primary_repair_action_index": (
                    action_index if isinstance(action_index, int) else None
                ),
                "primary_repair_action_type": (
                    str(action_type) if action_type is not None else None
                ),
                "primary_repair_action_label": (
                    str(action_label) if action_label is not None else None
                ),
                "primary_repair_tool": self._optional_string(
                    first_option.get("tool")
                ),
                "primary_repair_required_extra_arguments": [
                    str(argument)
                    for argument in first_option.get(
                        "required_extra_arguments",
                        [],
                    )
                    if isinstance(argument, str)
                ],
            }
        return empty_cue
    @staticmethod
    def _repair_action_type_label(action_type: str) -> str:
        return action_type.replace("_", " ").capitalize()
    @staticmethod
    def _optional_string(value: Any) -> str | None:
        return str(value) if value is not None else None
    def _draft_query_plan_storage_access(
        self,
        context: QueryPlanningContext,
        selected_candidate: QueryTargetCandidate | None,
    ) -> StorageAccessDescription | None:
        if selected_candidate is None or selected_candidate.storage_access is None:
            return None
        storage_iri = selected_candidate.storage_access.iri
        for storage_access in context.storage_accesses:
            if storage_access.iri == storage_iri:
                return storage_access
        return None
    def _draft_query_plan_selected_physical_layout(
        self,
        context: QueryPlanningContext,
        *,
        physical_layout_iri: str | None,
    ) -> tuple[PhysicalLayoutDescription | None, str | None]:
        if physical_layout_iri is None:
            return None, None
        layout_iri = self._required_iri("physical_layout_iri", physical_layout_iri)
        for layout in context.physical_layouts:
            if layout.iri == layout_iri:
                return layout, layout_iri
        raise DoxaBaseError(
            "physical_layout_iri did not match any physical layout linked to "
            f"'{context.dataset.iri}': {layout_iri}"
        )
    def _query_physical_layout_storage_protocol_mismatch_issue(
        self,
        candidate: QueryTargetCandidate | None,
        layout: PhysicalLayoutDescription | None,
    ) -> QueryPlanningIssue | None:
        if candidate is None or layout is None or layout.file_format is None:
            return None
        expected_route_kind = self._query_candidate_layout_route_kind(candidate)
        layout_route_kind = self._query_file_format_layout_route_kind(
            layout.file_format.iri
        )
        if layout_route_kind is None or layout_route_kind == expected_route_kind:
            return None
        expected_formats = (
            ["rc:PostgreSQLTable", "rc:SQLiteTable", "rc:MySQLTable"]
            if expected_route_kind == "database"
            else ["rc:CSV", "rc:Parquet"]
        )
        storage_access_iri = (
            candidate.storage_access.iri
            if candidate.storage_access is not None
            else None
        )
        storage_protocol_iri = (
            candidate.storage_protocol.iri
            if candidate.storage_protocol is not None
            else None
        )
        return QueryPlanningIssue(
            code="physical_layout_storage_protocol_mismatch",
            severity="warning",
            message=(
                "Selected physical layout file format does not match the "
                "selected query target storage route. Choose a physical layout "
                "whose file/table format belongs to the selected storage access."
            ),
            resource=self._summary_from_description(layout),
            details={
                "candidate_storage_route_kind": expected_route_kind,
                "physical_layout_route_kind": layout_route_kind,
                "candidate_template": candidate.template,
                "candidate_template_source": candidate.template_source,
                "candidate_path": candidate.candidate_path,
                "relation_identifier": candidate.relation_identifier,
                "storage_access_iri": storage_access_iri,
                "storage_protocol_iri": storage_protocol_iri,
                "physical_layout_iri": layout.iri,
                "physical_layout_file_format_iri": layout.file_format.iri,
                "expected_file_format_examples": expected_formats,
            },
        )
    def _query_selected_physical_layout_path_extension_issue(
        self,
        candidate: QueryTargetCandidate | None,
        layout: PhysicalLayoutDescription | None,
    ) -> QueryPlanningIssue | None:
        if candidate is None or layout is None:
            return None
        return self._query_candidate_path_extension_physical_layout_issue(
            candidate_path=candidate.candidate_path,
            template=candidate.template,
            template_source=candidate.template_source,
            source_resource=candidate.source_resource,
            physical_layouts=[layout],
            selected_physical_layout=layout,
        )
    def _unique_physical_layout_for_query_plan(
        self,
        physical_layouts: list[PhysicalLayoutDescription],
    ) -> PhysicalLayoutDescription | None:
        if not physical_layouts:
            return None
        signatures = self._physical_layout_signatures(physical_layouts)
        if len(signatures) != 1:
            return None
        return physical_layouts[0]
    def _query_database_relation_template_repair_hint(
        self,
        *,
        template: str,
        template_source: str,
        source_resource: ResourceSummary,
        storage_access: StorageAccessDescription,
    ) -> dict[str, Any]:
        add_action = {
            "action_type": "add_reviewed_relation_template",
            "tool": "doxabase.stage_revision",
            "source_subject_iri": source_resource.iri,
            "misplaced_template_subject_iri": source_resource.iri,
            "misplaced_template_source": template_source,
            "misplaced_template": template,
            "required_extra_arguments": ["object", "rationale"],
            "rationale_template": (
                "Reviewed database relation identifier for "
                f"{storage_access.iri}."
            ),
            "arguments_template": {
                "kind": "map_assertion",
                "spec": {
                    "subject": storage_access.iri,
                    "predicate": "rc:pathTemplate",
                    "object": "<reviewed_database_relation_identifier>",
                    "object_kind": "literal",
                    "change_kind": "add",
                    "graph": "map",
                },
            },
            "placeholder_fields": ["object"],
            "reviewed_value_fields": ["object"],
            "condition": (
                "Replace the placeholder object with the reviewed "
                "database relation identifier before staging."
            ),
        }
        remove_action = {
            "action_type": "remove_misplaced_source_template",
            "tool": "doxabase.stage_revision",
            "source_subject_iri": source_resource.iri,
            "misplaced_template_subject_iri": source_resource.iri,
            "misplaced_template_source": template_source,
            "misplaced_template": template,
            "required_extra_arguments": ["rationale"],
            "rationale_template": (
                "Reviewed source template as misplaced database "
                "relation metadata."
            ),
            "args": {
                "kind": "map_assertion",
                "spec": {
                    "subject": source_resource.iri,
                    "predicate": "rc:pathTemplate",
                    "object": template,
                    "object_kind": "literal",
                    "change_kind": "remove",
                    "graph": "map",
                },
            },
            "condition": (
                "Only after review confirms the source template was "
                "misplaced relation metadata rather than a real "
                "file/object path."
            ),
        }
        storage_access_relation_templates = list(storage_access.path_templates)
        target_already_has_template = template in storage_access_relation_templates
        target_has_relation_template = bool(storage_access_relation_templates)
        if target_has_relation_template:
            if target_already_has_template:
                add_condition = (
                    "The storage access already carries this relation-like "
                    "template. Review the remaining misplaced source template "
                    "and run remove_misplaced_source_template instead of "
                    "adding a duplicate relation template."
                )
            else:
                add_condition = (
                    "The storage access already carries database relation "
                    "template(s). Inspect query target candidates; if one is "
                    "the reviewed relation, run remove_misplaced_source_template "
                    "instead of adding another relation template. If none is "
                    "correct, stage a separate reviewed add."
                )
            add_action = {
                **add_action,
                "action_status": "already_satisfied",
                "skip_when_already_satisfied": True,
                "existing_storage_access_relation_templates": (
                    storage_access_relation_templates
                ),
                "condition": add_condition,
            }
        actions = (
            [remove_action, add_action]
            if target_has_relation_template
            else [add_action, remove_action]
        )
        candidate_relation_identifier: dict[str, Any] = {
            "value": template,
            "requires_review": True,
            "already_on_storage_access": target_already_has_template,
            "review_note": (
                "Dataset and partition path templates are not database "
                "relation identifiers by default; replace this value with "
                "the reviewed schema/table/relation before staging the add."
            ),
        }
        if storage_access_relation_templates:
            candidate_relation_identifier[
                "storage_access_relation_templates"
            ] = storage_access_relation_templates
        return {
            "action_type": "move_database_relation_template_to_storage_access",
            "requires_review": True,
            "source_subject_iri": source_resource.iri,
            "misplaced_template_subject_iri": source_resource.iri,
            "misplaced_template_source": template_source,
            "misplaced_template": template,
            "source": {
                "subject_iri": source_resource.iri,
                "template_source": template_source,
                "predicate": "rc:pathTemplate",
                "template": template,
            },
            "target": {
                "storage_access_iri": storage_access.iri,
                "predicate": "rc:pathTemplate",
                "required_template_source": "storage_access",
            },
            "candidate_relation_identifier": candidate_relation_identifier,
            "actions": actions,
        }
    def _query_database_relation_template_missing_repair_hint(
        self,
        storage_access: StorageAccessDescription,
    ) -> dict[str, Any]:
        return {
            "action_type": "record_database_relation_template",
            "requires_review": True,
            "source": {
                "storage_access_iri": storage_access.iri,
                "storage_root": storage_access.storage_root,
                "location_kind": storage_access.location_kind,
            },
            "target": {
                "storage_access_iri": storage_access.iri,
                "predicate": "rc:pathTemplate",
                "required_template_source": "storage_access",
            },
            "candidate_relation_identifier": {
                "value": "<reviewed_database_relation_identifier>",
                "requires_review": True,
                "review_note": (
                    "Review the database schema/table/relation identifier "
                    "before staging; the storage root is only the connection "
                    "reference."
                ),
            },
            "actions": [
                {
                    "action_type": "add_reviewed_relation_template",
                    "tool": "doxabase.stage_revision",
                    "required_extra_arguments": ["object", "rationale"],
                    "rationale_template": (
                        "Reviewed database relation identifier for "
                        f"{storage_access.iri}."
                    ),
                    "arguments_template": {
                        "kind": "map_assertion",
                        "spec": {
                            "subject": storage_access.iri,
                            "predicate": "rc:pathTemplate",
                            "object": "<reviewed_database_relation_identifier>",
                            "object_kind": "literal",
                            "change_kind": "add",
                            "graph": "map",
                        },
                    },
                    "placeholder_fields": ["object"],
                    "reviewed_value_fields": ["object"],
                    "condition": (
                        "Replace the placeholder object with the reviewed "
                        "schema, table, or relation identifier before staging."
                    ),
                }
            ],
        }
    def _query_candidate_path_extension_physical_layout_issue(
        self,
        *,
        candidate_path: str | None,
        template: str,
        template_source: str,
        source_resource: ResourceSummary,
        physical_layouts: list[PhysicalLayoutDescription],
        selected_physical_layout: PhysicalLayoutDescription | None = None,
    ) -> QueryPlanningIssue | None:
        path_format = self._query_candidate_path_extension_format(candidate_path)
        if path_format is None:
            return None
        layout = selected_physical_layout or (
            self._unique_physical_layout_for_query_plan(physical_layouts)
        )
        if layout is None:
            return None
        layout_format = self._query_physical_layout_format_kind(layout)
        if layout_format is None or layout_format == path_format:
            return None
        layout_basis = (
            "selected physical layout"
            if selected_physical_layout is not None
            else "single linked physical layout"
        )
        layout_resource = self._summary_from_description(layout)
        if layout.file_format is not None:
            layout_label = (
                layout.file_format.label
                or self._compact_iri(layout.file_format.iri)
                or layout.file_format.iri
            )
        else:
            layout_label = layout_format
        source_label = source_resource.label or source_resource.iri
        return QueryPlanningIssue(
            code="physical_layout_path_extension_mismatch",
            severity="warning",
            message=(
                "Candidate path extension suggests "
                f"{path_format.upper()} data, but the {layout_basis} "
                f"layout records {layout_label} as the file format. Review "
                "the physical layout and path metadata before executable use."
            ),
            resource=layout_resource,
            details={
                "candidate_path": candidate_path,
                "path_extension_format": path_format,
                "template": template,
                "template_source": template_source,
                "template_source_resource_iri": source_resource.iri,
                "template_source_label": source_label,
                "physical_layout_iri": layout.iri,
                "physical_layout_file_format_iri": (
                    layout.file_format.iri
                    if layout.file_format is not None
                    else None
                ),
                "physical_layout_file_format_label": (
                    layout.file_format.label
                    if layout.file_format is not None
                    else None
                ),
                "physical_layout_format_kind": layout_format,
                "physical_layout_selection_basis": (
                    "caller_selected"
                    if selected_physical_layout is not None
                    else "single_linked_layout"
                ),
                "review_note": (
                    "This is a conservative extension/file-format guard for "
                    "known CSV and Parquet mismatches. Correct either the "
                    "path/template metadata or the physical layout file format "
                    "before using the candidate as an executable handoff."
                ),
            },
        )
    def _query_physical_layout_format_kind(
        self,
        layout: PhysicalLayoutDescription,
    ) -> str | None:
        if layout.file_format is None:
            return None
        values = [
            layout.file_format.iri,
            layout.file_format.label,
            self._compact_iri(layout.file_format.iri),
            self._local_name(layout.file_format.iri),
        ]
        text = " ".join(value for value in values if value).lower()
        if "parquet" in text:
            return "parquet"
        if "csv" in text:
            return "csv"
        return None
    def _storage_protocol_location_repair_hint(
        self,
        storage_access: StorageAccessDescription,
        *,
        mismatch_reasons: list[str],
        template: str | None = None,
        template_source_resource: ResourceSummary | None = None,
    ) -> dict[str, Any]:
        actions: list[dict[str, Any]] = [
            {
                "action_type": "set_reviewed_storage_protocol",
                "tool": "doxabase.stage_revision",
                "required_extra_arguments": ["rationale"],
                "rationale_template": (
                    "Reviewed protocol for storage access "
                    f"{storage_access.iri}."
                ),
                "arguments_template": {
                    "kind": "map_assertion",
                    "spec": {
                        "subject": storage_access.iri,
                        "predicate": "rc:storageProtocol",
                        "object": "<reviewed_rc_storage_protocol_iri>",
                        "object_kind": "iri",
                        "change_kind": "replace",
                        "graph": "map",
                    },
                },
                "placeholder_fields": ["object"],
                "reviewed_value_fields": ["object"],
                "condition": (
                    "Use when review shows the recorded storage protocol is the "
                    "wrong one for the true storage location."
                ),
            },
            {
                "action_type": "set_reviewed_storage_root",
                "tool": "doxabase.stage_revision",
                "required_extra_arguments": ["rationale"],
                "rationale_template": (
                    "Reviewed storage root or URL for storage access "
                    f"{storage_access.iri}."
                ),
                "arguments_template": {
                    "kind": "map_assertion",
                    "spec": {
                        "subject": storage_access.iri,
                        "predicate": "rc:storageRoot",
                        "object": "<reviewed_protocol_appropriate_root_url_or_connection>",
                        "object_kind": "literal",
                        "change_kind": "replace",
                        "graph": "map",
                    },
                },
                "placeholder_fields": ["object"],
                "reviewed_value_fields": ["object"],
                "condition": (
                    "Use when review shows the protocol is right but the root, "
                    "URL, or connection reference is malformed or in the wrong "
                    "scheme."
                ),
            },
        ]
        if self._is_s3_storage(storage_access.storage_protocol):
            actions.extend(
                [
                    {
                        "action_type": "set_reviewed_bucket_name",
                        "tool": "doxabase.stage_revision",
                        "required_extra_arguments": ["rationale"],
                        "rationale_template": (
                            "Reviewed bucket name for storage access "
                            f"{storage_access.iri}."
                        ),
                        "arguments_template": {
                            "kind": "map_assertion",
                            "spec": {
                                "subject": storage_access.iri,
                                "predicate": "rc:bucketName",
                                "object": "<reviewed_bucket_name>",
                                "object_kind": "literal",
                                "change_kind": "replace",
                                "graph": "map",
                            },
                        },
                        "placeholder_fields": ["object"],
                        "reviewed_value_fields": ["object"],
                        "condition": (
                            "Use for S3-compatible storage when review confirms "
                            "the bucket should be recorded separately from path "
                            "templates."
                        ),
                    },
                    {
                        "action_type": "set_reviewed_key_prefix",
                        "tool": "doxabase.stage_revision",
                        "required_extra_arguments": ["rationale"],
                        "rationale_template": (
                            "Reviewed key prefix for storage access "
                            f"{storage_access.iri}."
                        ),
                        "arguments_template": {
                            "kind": "map_assertion",
                            "spec": {
                                "subject": storage_access.iri,
                                "predicate": "rc:keyPrefix",
                                "object": "<reviewed_key_prefix>",
                                "object_kind": "literal",
                                "change_kind": "replace",
                                "graph": "map",
                            },
                        },
                        "placeholder_fields": ["object"],
                        "reviewed_value_fields": ["object"],
                        "condition": (
                            "Use for S3-compatible storage when review confirms "
                            "the prefix should be recorded separately from path "
                            "templates."
                        ),
                    },
                ]
            )
        if storage_access.bucket_name:
            actions.append(
                {
                    "action_type": "remove_conflicting_bucket_name",
                    "tool": "doxabase.stage_revision",
                    "required_extra_arguments": ["rationale"],
                    "rationale_template": (
                        "Reviewed bucket metadata as inappropriate for storage "
                        f"access {storage_access.iri}."
                    ),
                    "args": {
                        "kind": "map_assertion",
                        "spec": {
                            "subject": storage_access.iri,
                            "predicate": "rc:bucketName",
                            "object": storage_access.bucket_name,
                            "object_kind": "literal",
                            "change_kind": "remove",
                            "graph": "map",
                        },
                    },
                    "condition": (
                        "Only after review confirms bucket metadata is wrong for "
                        "this storage protocol or should be represented elsewhere."
                    ),
                }
            )
        if storage_access.key_prefix:
            actions.append(
                {
                    "action_type": "remove_conflicting_key_prefix",
                    "tool": "doxabase.stage_revision",
                    "required_extra_arguments": ["rationale"],
                    "rationale_template": (
                        "Reviewed key-prefix metadata as inappropriate for "
                        f"storage access {storage_access.iri}."
                    ),
                    "args": {
                        "kind": "map_assertion",
                        "spec": {
                            "subject": storage_access.iri,
                            "predicate": "rc:keyPrefix",
                            "object": storage_access.key_prefix,
                            "object_kind": "literal",
                            "change_kind": "remove",
                            "graph": "map",
                        },
                    },
                    "condition": (
                        "Only after review confirms key-prefix metadata is wrong "
                        "for this storage protocol or duplicates the template."
                    ),
                }
            )
        if template is not None and template_source_resource is not None:
            actions.extend(
                [
                    {
                        "action_type": "add_reviewed_path_template",
                        "tool": "doxabase.stage_revision",
                        "required_extra_arguments": ["rationale"],
                        "rationale_template": (
                            "Reviewed protocol-appropriate path template for "
                            f"{template_source_resource.iri}."
                        ),
                        "arguments_template": {
                            "kind": "map_assertion",
                            "spec": {
                                "subject": template_source_resource.iri,
                                "predicate": "rc:pathTemplate",
                                "object": "<reviewed_protocol_appropriate_path_template>",
                                "object_kind": "literal",
                                "change_kind": "add",
                                "graph": "map",
                            },
                        },
                        "placeholder_fields": ["object"],
                        "reviewed_value_fields": ["object"],
                        "condition": (
                            "Use when review confirms the template value should "
                            "be corrected while preserving the source resource."
                        ),
                    },
                    {
                        "action_type": "remove_conflicting_path_template",
                        "tool": "doxabase.stage_revision",
                        "required_extra_arguments": ["rationale"],
                        "rationale_template": (
                            "Reviewed path template as conflicting with storage "
                            f"access {storage_access.iri}."
                        ),
                        "args": {
                            "kind": "map_assertion",
                            "spec": {
                                "subject": template_source_resource.iri,
                                "predicate": "rc:pathTemplate",
                                "object": template,
                                "object_kind": "literal",
                                "change_kind": "remove",
                                "graph": "map",
                            },
                        },
                        "condition": (
                            "Only after review confirms this exact template is "
                            "malformed, duplicated, or belongs on a different "
                            "storage access."
                        ),
                    },
                ]
            )
        hint: dict[str, Any] = {
            "action_type": "repair_storage_protocol_location_mismatch",
            "requires_review": True,
            "storage_access": {
                "storage_access_iri": storage_access.iri,
                "storage_protocol_iri": (
                    storage_access.storage_protocol.iri
                    if storage_access.storage_protocol is not None
                    else None
                ),
                "storage_root": storage_access.storage_root,
                "bucket_name": storage_access.bucket_name,
                "key_prefix": storage_access.key_prefix,
            },
            "mismatch_reasons": mismatch_reasons,
            "actions": actions,
        }
        if template is not None and template_source_resource is not None:
            hint["source"] = {
                "subject_iri": template_source_resource.iri,
                "predicate": "rc:pathTemplate",
                "template": template,
            }
        return hint
    def _query_storage_access_location_kind_issue(
        self,
        storage_access: StorageAccessDescription,
    ) -> QueryPlanningIssue | None:
        if not storage_access.storage_root:
            return None
        if self._is_database_storage(storage_access.storage_protocol):
            return self._query_database_relation_template_missing_issue(
                storage_access
            )
        if storage_access.location_kind == "object":
            return None
        access_resource = self._summary_from_description(storage_access)
        if storage_access.location_kind is None:
            message = (
                "Storage root is the only candidate location, but location_kind "
                "is not recorded. Record location_kind='object' when the root "
                "names the dataset object/location exactly, or add a path "
                "template for directory, prefix, or connection roots."
            )
        else:
            message = (
                "Storage root is the only candidate location, but location_kind "
                f"is recorded as '{storage_access.location_kind}'. Add a path "
                "template before executable use, or record location_kind='object' "
                "when this root names the dataset object/location exactly."
            )
        return QueryPlanningIssue(
            code="storage_location_kind_needs_path_template",
            severity="warning",
            message=message,
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
                "allowed_template_sources": ["storage_access"],
                "repair_hint": (
                    self._query_storage_location_kind_repair_hint(storage_access)
                ),
            },
        )
    def _query_storage_location_kind_repair_hint(
        self,
        storage_access: StorageAccessDescription,
    ) -> dict[str, Any]:
        set_object_change_kind = (
            "add" if storage_access.location_kind is None else "replace"
        )
        return {
            "action_type": "record_file_object_path_template_or_exact_root",
            "choice_mode": "choose_one",
            "requires_review": True,
            "source": {
                "storage_access_iri": storage_access.iri,
                "storage_root": storage_access.storage_root,
                "location_kind": storage_access.location_kind,
            },
            "target": {
                "storage_access_iri": storage_access.iri,
                "predicate": "rc:pathTemplate",
                "required_template_source": "storage_access",
            },
            "candidate_path_template": {
                "value": "<reviewed_relative_path_template>",
                "requires_review": True,
                "review_note": (
                    "Review the path below the recorded storage root before "
                    "staging. Use this when the storage root is a directory, "
                    "prefix, or other broader container."
                ),
            },
            "actions": [
                {
                    "action_type": "add_reviewed_path_template",
                    "tool": "doxabase.stage_revision",
                    "required_extra_arguments": ["object", "rationale"],
                    "rationale_template": (
                        "Reviewed file/object path template for storage access "
                        f"{storage_access.iri}."
                    ),
                    "arguments_template": {
                        "kind": "map_assertion",
                        "spec": {
                            "subject": storage_access.iri,
                            "predicate": "rc:pathTemplate",
                            "object": "<reviewed_relative_path_template>",
                            "object_kind": "literal",
                            "change_kind": "add",
                            "graph": "map",
                        },
                    },
                    "placeholder_fields": ["object"],
                    "reviewed_value_fields": ["object"],
                    "condition": (
                        "Replace the placeholder object with the reviewed "
                        "dataset path template relative to the storage root."
                    ),
                },
                {
                    "action_type": "set_root_as_exact_object_location",
                    "tool": "doxabase.stage_revision",
                    "required_extra_arguments": ["rationale"],
                    "rationale_template": (
                        "Reviewed storage root as the exact dataset object or "
                        f"location for {storage_access.iri}."
                    ),
                    "args": {
                        "kind": "map_assertion",
                        "spec": {
                            "subject": storage_access.iri,
                            "predicate": "rc:locationKind",
                            "object": "object",
                            "object_kind": "literal",
                            "change_kind": set_object_change_kind,
                            "graph": "map",
                        },
                    },
                    "condition": (
                        "Use only when review shows the storage root itself "
                        "names the exact dataset file, object, or location and "
                        "no path template should be appended."
                    ),
                },
            ],
        }
    def _missing_physical_layout_details(
        self,
        dataset: DatasetDescription,
    ) -> dict[str, Any]:
        storage_protocol_iris = list(
            dict.fromkeys(
                access.storage_protocol.iri
                for access in dataset.storage_accesses
                if access.storage_protocol is not None
            )
        )
        database_storage_present = any(
            self._is_database_storage(access.storage_protocol)
            for access in dataset.storage_accesses
        )
        return {
            "dataset_iri": dataset.iri,
            "storage_protocol_iris": storage_protocol_iris,
            "database_storage_present": database_storage_present,
            "repair_hint": {
                "action_type": "record_or_stage_physical_layout",
                "choice_mode": "choose_one",
                "requires_review": True,
                "target_dataset_iri": dataset.iri,
                "storage_protocol_iris": storage_protocol_iris,
                "database_storage_present": database_storage_present,
                "file_format_guidance": {
                    "file_or_object_storage": (
                        "Use a reviewed rc:FileFormat such as rc:Parquet, "
                        "rc:CSV, or rc:JSONLines that matches the selected "
                        "file/object route."
                    ),
                    "rc:DatabaseStorage": (
                        "Use a database table layout such as rc:PostgreSQLTable, "
                        "rc:SQLiteTable, or rc:MySQLTable when the selected "
                        "route is a database relation handoff."
                    ),
                },
                "actions": [
                    {
                        "action_type": "stage_reviewed_physical_layout",
                        "tool": "doxabase.stage_revision",
                        "reason": (
                            "Use when review has identified the dataset's "
                            "physical layout, and the change should carry "
                            "staged-revision rationale before becoming map "
                            "state."
                        ),
                        "required_extra_arguments": [
                            "layout_iri",
                            "file_format",
                            "rationale",
                        ],
                        "arguments_template": {
                            "kind": "query_physical_layout_repair",
                            "spec": {
                                "dataset_iri": dataset.iri,
                                "layout_iri": "<reviewed physical layout IRI>",
                                "file_format": "<reviewed rc:FileFormat IRI>",
                                "rationale": (
                                    "<reviewed rationale for adding this layout>"
                                ),
                                "layout_verification_status": (
                                    "<reviewed rc:LayoutVerificationStatus IRI>"
                                ),
                                "layout_verification_note": (
                                    "<reviewed physical layout evidence note>"
                                ),
                                "validation_scope": "all",
                            },
                        },
                        "placeholder_fields": [
                            "layout_iri",
                            "file_format",
                            "rationale",
                            "layout_verification_status",
                            "layout_verification_note",
                        ],
                        "reviewed_value_fields": [
                            "layout_iri",
                            "file_format",
                            "rationale",
                            "layout_verification_status",
                            "layout_verification_note",
                        ],
                        "condition": (
                            "Replace placeholders with reviewed values before "
                            "staging. For database storage, prefer "
                            "rc:PostgreSQLTable, rc:SQLiteTable, or rc:MySQLTable "
                            "when that matches the relation engine."
                        ),
                        "review_rationale_guidance": (
                            "stage_revision kind='query_physical_layout_repair' "
                            "records a reviewable graph revision that adds the "
                            "physical layout resource and dataset link "
                            "together. Check and apply the staged row before "
                            "rerunning query planning."
                        ),
                    },
                    {
                        "action_type": "record_reviewed_physical_layout",
                        "tool": "doxabase.record_map_fact",
                        "reason": (
                            "Use when review has identified the dataset's file "
                            "format or database table layout."
                        ),
                        "required_extra_arguments": ["iri", "file_format"],
                        "arguments_template": {
                            "kind": "physical_layout",
                            "spec": {
                                "iri": "<reviewed physical layout IRI>",
                                "datasets": [dataset.iri],
                                "file_format": "<reviewed rc:FileFormat IRI>",
                                "layout_verification_status": (
                                    "<reviewed rc:LayoutVerificationStatus IRI>"
                                ),
                                "layout_verification_note": (
                                    "<reviewed physical layout evidence note>"
                                ),
                            },
                        },
                        "placeholder_fields": [
                            "file_format",
                            "layout_verification_status",
                            "layout_verification_note",
                        ],
                        "reviewed_value_fields": [
                            "file_format",
                            "layout_verification_status",
                            "layout_verification_note",
                        ],
                        "condition": (
                            "Replace placeholders with reviewed values before "
                            "recording. For database storage, prefer "
                            "rc:PostgreSQLTable, rc:SQLiteTable, or rc:MySQLTable "
                            "when that matches the relation engine."
                        ),
                        "review_rationale_guidance": (
                            "record_map_physical_layout writes current-best map "
                            "facts directly and does not record graph-revision "
                            "rationale. Preserve the reviewed rationale in the "
                            "calling workflow, or use a staged assertion helper "
                            "when durable review history is needed."
                        ),
                    }
                ],
            },
        }
    def _missing_storage_access_details(
        self,
        dataset: DatasetDescription,
        *,
        dataset_resource: ResourceSummary,
    ) -> dict[str, Any]:
        storage_access_count = self._count_type("rc:StorageAccess")
        (
            candidate_existing_storage_accesses,
            candidate_existing_storage_access_total,
        ) = self._missing_storage_existing_access_candidates(
            dataset,
            limit=8,
        )
        (
            database_relation_candidates,
            database_relation_candidate_total,
        ) = self._query_context_database_relation_candidates_from_evidence(
            dataset,
            limit=3,
        )
        (
            evidence_storage_route_candidates,
            evidence_storage_route_candidate_total,
        ) = self._query_context_evidence_storage_route_candidates_from_evidence(
            dataset,
            limit=6,
        )
        route_intent_preferred_roles = {
            self.expand_iri("rc:ProductionRoute"),
            self.expand_iri("rc:CurrentRoute"),
            self.expand_iri("rc:CanonicalRoute"),
        }
        route_intent_caution_roles = {
            self.expand_iri("rc:SampleRoute"),
            self.expand_iri("rc:ArchiveRoute"),
            self.expand_iri("rc:BackfillRoute"),
        }
        candidate_existing_storage_access_route_intent_preferred_indexes: list[int] = []
        candidate_existing_storage_access_route_intent_caution_indexes: list[int] = []
        for index, candidate in enumerate(candidate_existing_storage_accesses):
            role_iris = {
                str(role.get("iri"))
                for role in candidate.get("route_roles", [])
                if isinstance(role, MappingABC) and role.get("iri") is not None
            }
            if (
                role_iris & route_intent_preferred_roles
                and not candidate.get("pending_staged_repair_iris")
            ):
                candidate_existing_storage_access_route_intent_preferred_indexes.append(
                    index
                )
            if role_iris & route_intent_caution_roles:
                candidate_existing_storage_access_route_intent_caution_indexes.append(
                    index
                )
        optional_storage_fields = [
            "endpoint_profile",
            "bucket_name",
            "key_prefix",
            "region",
            "path_style_access",
            "credential_reference",
        ]
        actions: list[dict[str, Any]] = [
            {
                "action_type": "stage_reviewed_storage_access",
                "tool": "doxabase.stage_revision",
                "reason": (
                    "Use when review has identified the non-secret storage "
                    "protocol and location, and the change should carry "
                    "staged-revision rationale before becoming map state."
                ),
                "required_extra_arguments": [
                    "storage_access_iri",
                    "storage_protocol",
                    "storage_root",
                    "rationale",
                ],
                "arguments_template": {
                    "kind": "query_storage_access_repair",
                    "spec": {
                        "dataset_iri": dataset.iri,
                        "storage_access_iri": "<reviewed storage access IRI>",
                        "storage_protocol": "<reviewed rc:StorageProtocol IRI>",
                        "storage_root": (
                            "<reviewed root, URL, bucket URI, or connection>"
                        ),
                        "endpoint_profile": "<optional reviewed endpoint profile>",
                        "bucket_name": "<optional reviewed S3 bucket name>",
                        "key_prefix": "<optional reviewed S3 key prefix>",
                        "region": "<optional reviewed S3 region>",
                        "path_style_access": "<optional reviewed boolean>",
                        "credential_reference": (
                            "<optional non-secret credential reference>"
                        ),
                        "rationale": (
                            "<reviewed rationale for adding this storage route>"
                        ),
                        "location_kind": "<reviewed object|directory|prefix|connection>",
                        "path_templates": [
                            "<optional storage-owned path or relation template>"
                        ],
                        "layout_verification_status": (
                            "<reviewed rc:LayoutVerificationStatus IRI>"
                        ),
                        "layout_verification_note": (
                            "<reviewed storage access evidence note>"
                        ),
                        "validation_scope": "all",
                    },
                },
                "placeholder_fields": [
                    "storage_access_iri",
                    "storage_protocol",
                    "storage_root",
                    *optional_storage_fields,
                    "rationale",
                    "location_kind",
                    "path_templates",
                    "layout_verification_status",
                    "layout_verification_note",
                ],
                "reviewed_value_fields": [
                    "storage_access_iri",
                    "storage_protocol",
                    "storage_root",
                    *optional_storage_fields,
                    "rationale",
                    "location_kind",
                    "path_templates",
                    "layout_verification_status",
                    "layout_verification_note",
                ],
                "condition": (
                    "Replace placeholders with reviewed non-secret values before "
                    "staging. Include path_templates only when the storage access "
                    "itself owns the path or database relation template. Omit "
                    "them when the dataset or partition already carries the "
                    "reviewed path template; duplicating it can create equivalent "
                    "query target candidates. Database relation identifiers are "
                    "the important exception and should be storage-access-owned."
                ),
                "protocol_guidance": {
                    "file_or_object_storage": (
                        "Omit storage-owned path_templates when the dataset or "
                        "partition already owns the reviewed file/object template."
                    ),
                    "rc:S3CompatibleStorage": (
                        "Use optional bucket_name, key_prefix, region, "
                        "endpoint_profile, path_style_access, and "
                        "credential_reference only when they are reviewed "
                        "non-secret route metadata for the object store."
                    ),
                    "rc:DatabaseStorage": (
                        "Use storage-owned path_templates for reviewed database "
                        "relation identifiers. Then rerun describe_query_context "
                        "and follow database_relation_template_source_mismatch if "
                        "a dataset or partition still carries the same "
                        "relation-like template."
                    ),
                },
                "review_rationale_guidance": (
                    "stage_revision kind='query_storage_access_repair' records "
                    "a reviewable graph revision that adds the storage access "
                    "resource and dataset link together. Check and apply the "
                    "staged row before rerunning query planning."
                ),
            },
            {
                "action_type": "record_reviewed_storage_access",
                "tool": "doxabase.record_map_fact",
                "reason": (
                    "Use when review has identified the non-secret "
                    "storage protocol and location for this dataset."
                ),
                "required_extra_arguments": [
                    "iri",
                    "storage_protocol",
                    "storage_root",
                ],
                "arguments_template": {
                    "kind": "storage_access",
                    "spec": {
                        "iri": "<reviewed storage access IRI>",
                        "datasets": [dataset.iri],
                        "storage_protocol": "<reviewed rc:StorageProtocol IRI>",
                        "storage_root": (
                            "<reviewed root, URL, bucket URI, or connection>"
                        ),
                        "endpoint_profile": "<optional reviewed endpoint profile>",
                        "bucket_name": "<optional reviewed S3 bucket name>",
                        "key_prefix": "<optional reviewed S3 key prefix>",
                        "region": "<optional reviewed S3 region>",
                        "path_style_access": "<optional reviewed boolean>",
                        "credential_reference": (
                            "<optional non-secret credential reference>"
                        ),
                        "path_templates": [
                            "<optional storage-owned path or relation template>"
                        ],
                    },
                },
                "placeholder_fields": [*optional_storage_fields, "path_templates"],
                "reviewed_value_fields": [*optional_storage_fields, "path_templates"],
                "condition": (
                    "Include path_templates only when the storage access "
                    "itself owns the path or database relation template. "
                    "Omit this optional field when the dataset or "
                    "partition already carries the reviewed path "
                    "template; duplicating it can create equivalent "
                    "query target candidates. Database relation "
                    "identifiers are the important exception and should "
                    "be storage-access-owned. For database storage, "
                    "rerun describe_query_context after recording the "
                    "relation; if the same relation-like value remains "
                    "on the dataset or partition, follow the "
                    "database_relation_template_source_mismatch repair "
                    "group to remove or move the misplaced template."
                ),
                "protocol_guidance": {
                    "file_or_object_storage": (
                        "Omit storage-owned path_templates when the "
                        "dataset or partition already owns the reviewed "
                        "file/object template."
                    ),
                    "rc:S3CompatibleStorage": (
                        "Use optional bucket_name, key_prefix, region, "
                        "endpoint_profile, path_style_access, and "
                        "credential_reference only when they are reviewed "
                        "non-secret route metadata for the object store."
                    ),
                    "rc:DatabaseStorage": (
                        "Use storage-owned path_templates for reviewed "
                        "database relation identifiers. Then rerun "
                        "describe_query_context and follow "
                        "database_relation_template_source_mismatch if "
                        "a dataset or partition still carries the same "
                        "relation-like template."
                    ),
                },
                "review_rationale_guidance": (
                    "record_map_fact kind='storage_access' writes current-best "
                    "map facts directly and does not record graph-revision "
                    "rationale. Use stage_revision "
                    "kind='query_storage_access_repair' when durable review "
                    "history is needed for a new storage access and dataset "
                    "link."
                ),
            },
            {
                "action_type": "stage_existing_storage_access_link",
                "tool": "doxabase.stage_revision",
                "reason": (
                    "Use when a suitable storage access resource already "
                    "exists and the dataset should link to it after "
                    "review."
                ),
                "required_extra_arguments": [
                    "object",
                    "rationale",
                ],
                "arguments_template": {
                    "kind": "map_assertion",
                    "spec": {
                        "subject": dataset.iri,
                        "predicate": "rc:hasStorageAccess",
                        "object": "<reviewed existing storage access IRI>",
                        "object_kind": "iri",
                        "change_kind": "add",
                        "rationale": "<reviewed rationale>",
                        "review_note": (
                            "Generated from missing_storage_access query "
                            "planning guidance; apply only after confirming "
                            "the storage access is the intended non-secret "
                            "route for this dataset."
                        ),
                        "validation_scope": "all",
                    },
                },
                "placeholder_fields": ["object"],
                "reviewed_value_fields": ["object"],
            },
        ]
        pending_candidate_repair_iris = list(
            dict.fromkeys(
                staged_iri
                for candidate in candidate_existing_storage_accesses
                for staged_iri in candidate.get("pending_staged_repair_iris", [])
            )
        )
        pending_candidate_storage_access_iris = [
            str(candidate["storage_access_iri"])
            for candidate in candidate_existing_storage_accesses
            if candidate.get("pending_staged_repair_iris")
            and candidate.get("storage_access_iri") is not None
        ]
        if pending_candidate_repair_iris:
            link_action = actions[2]
            link_action["already_pending_candidate_count"] = len(
                pending_candidate_storage_access_iris
            )
            link_action["already_pending_storage_access_iris"] = (
                pending_candidate_storage_access_iris
            )
            link_action["pending_staged_repair_iris"] = pending_candidate_repair_iris
            link_action["condition"] = (
                "Do not stage another link for candidates whose "
                "candidate_status is already_pending; review the staged row "
                "first. Choose only a non-pending candidate after review."
            )
        all_visible_candidates_pending = (
            candidate_existing_storage_accesses
            and candidate_existing_storage_access_total
            == len(candidate_existing_storage_accesses)
            and all(
                candidate.get("pending_staged_repair_iris")
                for candidate in candidate_existing_storage_accesses
            )
        )
        if all_visible_candidates_pending:
            link_action = actions[2]
            link_action["action_status"] = "already_pending"
            link_action["skip_when_already_pending"] = True
            link_action["reason"] = (
                "Skip while current staged work already proposes linking this "
                "dataset to each visible reviewed existing storage access."
            )
            link_action["condition"] = (
                "Review the pending staged repair before staging another "
                "rc:hasStorageAccess link for the same dataset and storage "
                "access."
            )
        details: dict[str, Any] = {
            "dataset_iri": dataset.iri,
            "global_storage_access_count": storage_access_count,
            "repair_hint": {
                "action_type": "record_or_link_storage_access",
                "choice_mode": "choose_one",
                "target_dataset_iri": dataset.iri,
                "candidate_existing_storage_accesses": (
                    candidate_existing_storage_accesses
                ),
                "candidate_existing_storage_access_count": len(
                    candidate_existing_storage_accesses
                ),
                "candidate_existing_storage_access_total_count": (
                    candidate_existing_storage_access_total
                ),
                "candidate_existing_storage_accesses_truncated": (
                    candidate_existing_storage_access_total
                    > len(candidate_existing_storage_accesses)
                ),
                "candidate_existing_storage_access_route_intent_preferred_indexes": (
                    candidate_existing_storage_access_route_intent_preferred_indexes
                ),
                "first_candidate_existing_storage_access_route_intent_preferred_index": (
                    candidate_existing_storage_access_route_intent_preferred_indexes[0]
                    if candidate_existing_storage_access_route_intent_preferred_indexes
                    else None
                ),
                "candidate_existing_storage_access_route_intent_caution_indexes": (
                    candidate_existing_storage_access_route_intent_caution_indexes
                ),
                "candidate_existing_storage_access_route_intent_note": (
                    "Review route_roles before linking an existing storage access. "
                    "Indexes with CurrentRoute, ProductionRoute, or CanonicalRoute "
                    "are preferred for unattended current-data repair; indexes "
                    "with SampleRoute, ArchiveRoute, or BackfillRoute require "
                    "explicit route-intent review."
                    if candidate_existing_storage_accesses
                    else None
                ),
                "database_relation_candidates": database_relation_candidates,
                "database_relation_candidate_count": len(
                    database_relation_candidates
                ),
                "database_relation_candidate_total_count": (
                    database_relation_candidate_total
                ),
                "database_relation_candidates_truncated": (
                    database_relation_candidate_total
                    > len(database_relation_candidates)
                ),
                "evidence_storage_route_candidates": (
                    evidence_storage_route_candidates
                ),
                "evidence_storage_route_candidate_count": len(
                    evidence_storage_route_candidates
                ),
                "evidence_storage_route_candidate_total_count": (
                    evidence_storage_route_candidate_total
                ),
                "evidence_storage_route_candidates_truncated": (
                    evidence_storage_route_candidate_total
                    > len(evidence_storage_route_candidates)
                ),
                "actions": actions,
            },
        }
        if evidence_storage_route_candidates:
            details["repair_hint"]["evidence_storage_route_candidate_source"] = (
                "query_result_scanned_source_paths_and_handles"
            )
            details["repair_hint"]["evidence_storage_route_candidate_review_note"] = (
                "These candidates are parsed from query-result scanned source "
                "paths and handles and remain review-only. Use the candidate "
                "argument fields to fill reviewed storage-overlay or staged "
                "storage-repair calls; do not treat them as applied map facts."
            )
        if database_relation_candidates:
            details["repair_hint"]["database_relation_candidate_source"] = (
                "query_result_scanned_source_handles"
            )
            details["repair_hint"]["database_relation_candidate_review_note"] = (
                "These candidates are parsed from query-result scanned source "
                "handles and remain review-only. Use them to fill reviewed "
                "stage_revision query_storage_access_repair arguments; do not "
                "treat them as applied map facts."
            )
        if pending_candidate_repair_iris:
            details["repair_hint"]["already_pending_candidate_count"] = len(
                pending_candidate_storage_access_iris
            )
            details["repair_hint"]["already_pending_storage_access_iris"] = (
                pending_candidate_storage_access_iris
            )
            details["repair_hint"]["pending_staged_repair_iris"] = (
                pending_candidate_repair_iris
            )
        fixture_hint = self._known_fixture_missing_storage_access_hint(
            dataset_resource,
            storage_access_count=storage_access_count,
        )
        if fixture_hint is not None:
            details["fixture_staleness_hint"] = fixture_hint
        return details
    def _known_fixture_missing_storage_access_hint(
        self,
        dataset_resource: ResourceSummary,
        *,
        storage_access_count: int,
    ) -> dict[str, Any] | None:
        fixture_hint = self._known_fixture_tables_without_storage_access_hint(
            storage_access_count=storage_access_count
        )
        if fixture_hint is None:
            return None
        present_tables = fixture_hint["known_fixture_table_iris"]
        dataset_matches_known_fixture = any(
            dataset_resource.iri == table_iri for table_iri in present_tables
        )
        if storage_access_count == 0:
            message = (
                "Known AIS or Polymarket fixture tables are present but no "
                "rc:StorageAccess resources exist in the capsule. Treat this "
                "capsule as stale or intentionally reduced for query-planning "
                "trials; load current fixtures into a scratch capsule before "
                "drawing conclusions about query-target behavior."
            )
        else:
            message = (
                "Known AIS or Polymarket fixture tables are present without "
                "linked rc:StorageAccess resources, even though unrelated "
                "storage accesses exist elsewhere in the capsule. Treat those "
                "fixture tables as stale or intentionally reduced for "
                "query-planning trials; load current fixtures into a scratch "
                "capsule before drawing conclusions about query-target behavior."
            )
        return {
            **fixture_hint,
            "dataset_matches_known_fixture": dataset_matches_known_fixture,
            "message": message,
        }
    def _known_fixture_tables_without_storage_access_hint(
        self,
        *,
        storage_access_count: int,
    ) -> dict[str, Any] | None:
        map_graphs = self._expand_graphs(["map"])
        present_tables: list[str] = []
        fixture_names: list[str] = []
        for fixture_name, namespace, local_names in KNOWN_QUERY_FIXTURE_TABLE_GROUPS:
            table_iris = [
                f"{namespace}{local_name}"
                for local_name in local_names
                if self._subject_exists(f"{namespace}{local_name}", map_graphs)
                and not self._objects(
                    map_graphs,
                    f"{namespace}{local_name}",
                    "rc:hasStorageAccess",
                )
            ]
            if table_iris:
                fixture_names.append(fixture_name)
                present_tables.extend(table_iris)
        if not present_tables:
            return None
        return {
            "hint_type": "known_fixture_tables_without_storage_accesses",
            "fixture_names": fixture_names,
            "global_storage_access_count": storage_access_count,
            "known_fixture_table_iris": present_tables[:10],
        }
    def _ambiguous_physical_layout_issue(
        self,
        physical_layouts: list[PhysicalLayoutDescription],
        *,
        dataset_resource: ResourceSummary,
    ) -> QueryPlanningIssue | None:
        signatures = self._physical_layout_signatures(physical_layouts)
        if len(signatures) <= 1:
            return None
        signature_details = [
            {
                "file_format_iri": signature[0],
                "compression_codec_iri": signature[1],
                "layout_iris": [
                    layout.iri
                    for layout in layouts
                ],
            }
            for signature, layouts in signatures.items()
        ]
        return QueryPlanningIssue(
            code="ambiguous_physical_layout",
            severity="warning",
            message=(
                "Multiple linked physical layouts declare distinct file formats "
                "or compression codecs. Select or model the layout that belongs "
                "to the chosen query target before inferring a scan function."
            ),
            resource=dataset_resource,
            details={
                "layout_count": len(physical_layouts),
                "distinct_layout_signature_count": len(signatures),
                "layout_signatures": signature_details,
            },
        )
    @staticmethod
    def _physical_layout_signatures(
        physical_layouts: list[PhysicalLayoutDescription],
    ) -> dict[tuple[str | None, str | None], list[PhysicalLayoutDescription]]:
        signatures: dict[
            tuple[str | None, str | None],
            list[PhysicalLayoutDescription],
        ] = {}
        for layout in physical_layouts:
            signature = DoxaBase._physical_layout_signature(layout)
            signatures.setdefault(signature, []).append(layout)
        return signatures
    @staticmethod
    def _optional_repair_draft_limit_object(
        value: str | None,
        *,
        default: int | None,
    ) -> int | None:
        if value is None:
            return default
        normalized = value.strip().lower()
        if normalized in {"none", "null", "unbounded"}:
            return None
        try:
            parsed = int(normalized)
        except ValueError:
            return default
        return parsed if parsed >= 0 else default
    def _describe_physical_layout(
        self,
        layout_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> PhysicalLayoutDescription:
        file_format = self._first_object(data_graphs, layout_iri, "rc:fileFormat")
        compression_codec = self._first_object(
            data_graphs,
            layout_iri,
            "rc:compressionCodec",
        )
        return PhysicalLayoutDescription(
            iri=layout_iri,
            label=self._label_from_graphs(lookup_graphs, layout_iri),
            description=self._description_from_graphs(lookup_graphs, layout_iri),
            file_format=(
                self._resource_summary(lookup_graphs, file_format)
                if file_format is not None
                else None
            ),
            compression_codec=(
                self._resource_summary(lookup_graphs, compression_codec)
                if compression_codec is not None
                else None
            ),
            layout_verification_status=self._optional_resource_summary(
                lookup_graphs,
                self._first_object(
                    data_graphs,
                    layout_iri,
                    "rc:layoutVerificationStatus",
                ),
            ),
            layout_verification_note=self._first_object(
                data_graphs,
                layout_iri,
                "rc:layoutVerificationNote",
            ),
        )
    def _describe_storage_access(
        self,
        access_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> StorageAccessDescription:
        storage_protocol = self._first_object(data_graphs, access_iri, "rc:storageProtocol")
        access_mode = self._first_object(data_graphs, access_iri, "rc:accessMode")
        return StorageAccessDescription(
            iri=access_iri,
            label=self._label_from_graphs(lookup_graphs, access_iri),
            description=self._description_from_graphs(lookup_graphs, access_iri),
            route_roles=[
                self._resource_summary(lookup_graphs, route_role)
                for route_role in self._objects(
                    data_graphs,
                    access_iri,
                    "rc:routeRole",
                )
            ],
            storage_protocol=(
                self._resource_summary(lookup_graphs, storage_protocol)
                if storage_protocol is not None
                else None
            ),
            access_mode=(
                self._resource_summary(lookup_graphs, access_mode)
                if access_mode is not None
                else None
            ),
            location_kind=self._first_object(
                data_graphs,
                access_iri,
                "rc:locationKind",
            ),
            storage_root=self._first_object(data_graphs, access_iri, "rc:storageRoot"),
            endpoint_profile=self._first_object(
                data_graphs,
                access_iri,
                "rc:endpointProfile",
            ),
            bucket_name=self._first_object(data_graphs, access_iri, "rc:bucketName"),
            key_prefix=self._first_object(data_graphs, access_iri, "rc:keyPrefix"),
            region=self._first_object(data_graphs, access_iri, "rc:region"),
            path_style_access=self._bool_object(
                data_graphs,
                access_iri,
                "rc:pathStyleAccess",
            ),
            credential_reference=self._first_object(
                data_graphs,
                access_iri,
                "rc:credentialReference",
            ),
            path_templates=self._objects(data_graphs, access_iri, "rc:pathTemplate"),
            layout_verification_status=self._optional_resource_summary(
                lookup_graphs,
                self._first_object(
                    data_graphs,
                    access_iri,
                    "rc:layoutVerificationStatus",
                ),
            ),
            layout_verification_note=self._first_object(
                data_graphs,
                access_iri,
                "rc:layoutVerificationNote",
            ),
        )
